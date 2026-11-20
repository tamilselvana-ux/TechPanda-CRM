import logging
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TeleCRMError(Exception):
    """Base exception for all TeleCRM integration errors."""
    pass


class TeleCRMAuthError(TeleCRMError):
    """Non-retryable authentication or authorization error (HTTP 401 / 403)."""
    pass


class TeleCRMRateLimitError(TeleCRMError):
    """Rate limit exceeded error (HTTP 429)."""
    pass


class TeleCRMServerError(TeleCRMError):
    """Server-side error returned by TeleCRM (HTTP 5xx)."""
    pass


class TeleCRMClient:
    """
    High-reliability, retry-resilient HTTP client for the TeleCRM Sync API v2.
    Adheres strictly to zero-dependency principles using requests.Session,
    exponential backoff with jitter, and non-retryable authentication gates.
    """
    DEFAULT_BASE_URL = "https://next.telecrm.in/autoupdate/v2/enterprise"
    DEFAULT_TIMEOUT = 60
    MAX_RETRIES = 8
    INITIAL_BACKOFF_SEC = 2.0
    MAX_BACKOFF_SEC = 60.0

    def __init__(
        self,
        token: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        session: Optional[requests.Session] = None
    ):
        self.token = (token or getattr(settings, 'TELECRM_TOKEN', '') or '').strip()
        self.enterprise_id = (enterprise_id or getattr(settings, 'TELECRM_ENTERPRISE_ID', '681848fb55c90e360f77494c') or '').strip()
        self.base_url = f"{self.DEFAULT_BASE_URL}/{self.enterprise_id}"
        self.session = session or requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        attempt: int = 1
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = self._get_headers()

        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT
            )
        except (requests.Timeout, requests.ConnectionError) as req_err:
            if attempt < self.MAX_RETRIES:
                sleep_sec = min(self.MAX_BACKOFF_SEC, self.INITIAL_BACKOFF_SEC * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 1.0)
                wait_time = sleep_sec + jitter
                logger.warning(
                    "Network error connecting to TeleCRM %s %s (attempt %d/%d): %s. Retrying in %.2fs",
                    method, path, attempt, self.MAX_RETRIES, req_err, wait_time
                )
                time.sleep(wait_time)
                return self._request(method, path, params, json_data, attempt + 1)
            raise TeleCRMError(f"Network error after {self.MAX_RETRIES} attempts: {req_err}") from req_err

        status = response.status_code

        # 401 / 403: Stop immediately, do not retry
        if status in (401, 403):
            err_msg = f"TeleCRM authentication failed (HTTP {status}): {response.text}"
            logger.error(err_msg)
            raise TeleCRMAuthError(err_msg)

        # 429 Rate Limit or 5xx Server Error: Retry with exponential backoff
        if status == 429 or status >= 500:
            if attempt < self.MAX_RETRIES:
                sleep_sec = min(self.MAX_BACKOFF_SEC, self.INITIAL_BACKOFF_SEC * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 1.0)
                wait_time = sleep_sec + jitter
                logger.warning(
                    "TeleCRM returned HTTP %d on %s %s (attempt %d/%d). Retrying in %.2fs",
                    status, method, path, attempt, self.MAX_RETRIES, wait_time
                )
                time.sleep(wait_time)
                return self._request(method, path, params, json_data, attempt + 1)

            if status == 429:
                raise TeleCRMRateLimitError(f"TeleCRM rate limit exceeded (HTTP 429): {response.text}")
            raise TeleCRMServerError(f"TeleCRM server error (HTTP {status}): {response.text}")

        # Other 4xx client errors: Raise TeleCRMError
        if 400 <= status < 500:
            raise TeleCRMError(f"TeleCRM request rejected (HTTP {status}): {response.text}")

        # Successful response: Parse JSON or return empty structure
        if response.text.strip():
            try:
                return response.json()
            except ValueError as json_err:
                raise TeleCRMError(f"Invalid JSON returned by TeleCRM: {response.text[:200]}") from json_err
        return {}

    def count_leads(self) -> int:
        """
        Retrieves total count of leads in TeleCRM enterprise.
        POST /lead/search?onlyCount=true body {}
        """
        data = self._request("POST", "/lead/search", params={"onlyCount": "true"}, json_data={})
        if isinstance(data, dict):
            return int(data.get("total_count", 0))
        return 0

    def list_leads(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Lists leads sorted newest-first by creation.
        POST /lead/search?skip=<skip>&limit=<limit> body {}
        """
        limit = max(1, min(100, limit))
        data = self._request("POST", "/lead/search", params={"skip": skip, "limit": limit}, json_data={})
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data") or data.get("leads") or []
        return []

    def list_leads_active_between(
        self,
        start_dt: datetime,
        end_dt: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Lists leads that had actions performed within the given time window.
        POST /lead/search body {"actions": {"performed_at": {"from": <ms>, "to": <ms>}}}
        Returns (leads_list, total_count).
        """
        limit = max(1, min(100, limit))
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)

        payload = {
            "actions": {
                "performed_at": {
                    "from": start_ms,
                    "to": end_ms
                }
            }
        }
        data = self._request(
            "POST",
            "/lead/search",
            params={"skip": skip, "limit": limit},
            json_data=payload
        )

        leads = []
        total_count = 0
        if isinstance(data, list):
            leads = data
            total_count = len(data)
        elif isinstance(data, dict):
            leads = data.get("data") or data.get("leads") or []
            total_count = int(data.get("total_count", len(leads)))

        return leads, total_count

    def get_lead_actions(
        self,
        lead_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Retrieves paginated timeline actions/history for a specific lead.
        POST /lead/{leadId}/action/search?skip=<skip>&limit=<limit> body {}
        Returns (actions_list, total_count).
        """
        limit = max(1, min(100, limit))
        data = self._request(
            "POST",
            f"/lead/{lead_id}/action/search",
            params={"skip": skip, "limit": limit},
            json_data={}
        )

        actions = []
        total_count = 0
        if isinstance(data, list):
            actions = data
            total_count = len(data)
        elif isinstance(data, dict):
            actions = data.get("data") or data.get("actions") or []
            total_count = int(data.get("total_count", len(actions)))

        return actions, total_count

    def get_team_members(self) -> List[Dict[str, Any]]:
        """
        Retrieves enterprise team members to map TeleCRM internal UIDs to email addresses.
        GET /team-members or /team-members/list
        """
        try:
            data = self._request("GET", "/team-members")
        except TeleCRMError:
            data = self._request("GET", "/team-members/list")

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data") or data.get("team_members") or []
        return []

    def get_lead_stage_pipeline(self) -> Dict[str, Any]:
        """
        Retrieves enterprise lead stage pipeline and active status definitions.
        GET /lead-stage-pipeline
        """
        data = self._request("GET", "/lead-stage-pipeline")
        if isinstance(data, dict):
            return data
        return {"statuses": []}
