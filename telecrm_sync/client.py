import logging
import random
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SharedRateLimiter:
    """
    Thread-safe, process-wide shared rate limiter across all TeleCRM workers.
    Caps total request rate (default 4.0 req/sec = 14,400 req/hour) so all
    worker threads and clients share one budget under TeleCRM's 18,000 req/hr limit.
    """

    def __init__(self, rate_per_sec: float = 4.0):
        self.rate_per_sec = max(0.1, float(rate_per_sec))
        self._min_interval = 1.0 / self.rate_per_sec
        self._lock = threading.Lock()
        self._next_allowed_at = 0.0
        self._backoff_until = 0.0
        self._started_at = time.monotonic()
        self._total_requests = 0
        self._rate_limit_429_count = 0

    def acquire(self) -> None:
        """Reserve the next shared slot and sleep outside the lock if needed."""
        with self._lock:
            now = time.monotonic()
            slot = max(now, self._next_allowed_at, self._backoff_until)
            self._next_allowed_at = slot + self._min_interval
            self._total_requests += 1
        delay = slot - now
        if delay > 0:
            time.sleep(delay)

    def penalize(self, wait_sec: float) -> int:
        """Push back the shared schedule for ALL workers when HTTP 429 occurs."""
        with self._lock:
            self._rate_limit_429_count += 1
            until = time.monotonic() + max(0.0, float(wait_sec))
            if until > self._backoff_until:
                self._backoff_until = until
            if until > self._next_allowed_at:
                self._next_allowed_at = until
            return self._rate_limit_429_count

    def reset_stats(self) -> None:
        """Reset request counters and start timestamp for a new run."""
        with self._lock:
            now = time.monotonic()
            self._started_at = now
            self._total_requests = 0
            self._rate_limit_429_count = 0
            self._backoff_until = 0.0
            self._next_allowed_at = 0.0

    def get_stats(self) -> Dict[str, Any]:
        """Return current throughput (req/sec, req/hr) and 429 hit count."""
        with self._lock:
            elapsed = max(0.001, time.monotonic() - self._started_at)
            reqs = self._total_requests
            hits_429 = self._rate_limit_429_count
        rps = reqs / elapsed
        rph = rps * 3600.0
        return {
            "total_requests": reqs,
            "rate_limit_429_count": hits_429,
            "elapsed_sec": elapsed,
            "requests_per_sec": rps,
            "requests_per_hour": rph,
            "cap_rps": self.rate_per_sec,
        }


_SHARED_RATE_LIMITER_LOCK = threading.Lock()
_SHARED_RATE_LIMITER: Optional[SharedRateLimiter] = None


def get_shared_rate_limiter() -> SharedRateLimiter:
    """Return the process-wide SharedRateLimiter instance (capped at 4 req/sec by default)."""
    global _SHARED_RATE_LIMITER
    if _SHARED_RATE_LIMITER is None:
        with _SHARED_RATE_LIMITER_LOCK:
            if _SHARED_RATE_LIMITER is None:
                rps = float(getattr(settings, "TELECRM_RATE_LIMIT_RPS", 4.0) or 4.0)
                _SHARED_RATE_LIMITER = SharedRateLimiter(rate_per_sec=min(4.0, rps))
    return _SHARED_RATE_LIMITER


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
    MAX_RETRIES = 12
    INITIAL_BACKOFF_SEC = 2.0
    MAX_BACKOFF_SEC = 120.0

    def __init__(
        self,
        token: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        session: Optional[requests.Session] = None,
        rate_limiter: Optional[SharedRateLimiter] = None,
    ):
        self.token = (
            token or
            getattr(settings, 'TELECRM_SYNC_TOKEN', '') or
            getattr(settings, 'TELECRM_TOKEN', '') or
            ''
        ).strip()
        self.enterprise_id = (enterprise_id or getattr(settings, 'TELECRM_ENTERPRISE_ID', '681848fb55c90e360f77494c') or '').strip()
        self.base_url = f"{self.DEFAULT_BASE_URL}/{self.enterprise_id}"
        self.session = session or requests.Session()
        self.rate_limiter = rate_limiter or get_shared_rate_limiter()

    @staticmethod
    def extract_lead_id(obj: Any) -> str:
        """
        Parses lead id from lead_id, leadid, or id field variations across TeleCRM endpoints.
        """
        if not isinstance(obj, dict):
            return ""
        return str(
            obj.get("lead_id") or
            obj.get("leadid") or
            obj.get("id") or
            ""
        ).strip()

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
        if not self.token:
            raise TeleCRMAuthError("TELECRM_SYNC_TOKEN is missing.")
        url = f"{self.base_url}{path}"
        headers = self._get_headers()

        self.rate_limiter.acquire()

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

        # 429 Rate Limit: Exponential backoff, shared worker pause, and explicit logging
        if status == 429:
            sleep_sec = min(self.MAX_BACKOFF_SEC, self.INITIAL_BACKOFF_SEC * (2 ** (attempt - 1)))
            jitter = random.uniform(0, 1.0)
            wait_time = sleep_sec + jitter
            retry_after_raw = (getattr(response, "headers", None) or {}).get("Retry-After")
            if retry_after_raw:
                try:
                    wait_time = max(wait_time, min(self.MAX_BACKOFF_SEC, float(retry_after_raw)))
                except (TypeError, ValueError):
                    pass
            total_429s = self.rate_limiter.penalize(wait_time)
            logger.warning(
                "TeleCRM HTTP 429 rate limit hit on %s %s (attempt %d/%d, total_429s=%d). Exponential backoff %.2fs across all workers.",
                method, path, attempt, self.MAX_RETRIES, total_429s, wait_time
            )
            if attempt < self.MAX_RETRIES:
                time.sleep(wait_time)
                return self._request(method, path, params, json_data, attempt + 1)
            raise TeleCRMRateLimitError(f"TeleCRM rate limit exceeded (HTTP 429): {response.text}")

        # 5xx Server Error: Retry with exponential backoff
        if status >= 500:
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
        Supports totalCount, total_count, count, and total JSON keys.
        """
        data = self._request("POST", "/lead/search", params={"onlyCount": "true"}, json_data={})
        if isinstance(data, dict):
            val = (
                data.get("totalCount") or
                data.get("total_count") or
                data.get("count") or
                data.get("total") or
                0
            )
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0
        elif isinstance(data, (int, float)):
            return int(data)
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

    def get_metadata(self) -> Dict[str, Any]:
        """
        Retrieves enterprise metadata: enterprise info, name, id, creation timestamp.
        GET /metadata
        """
        data = self._request("GET", "/metadata")
        return data if isinstance(data, dict) else {}

    def get_custom_fields(self, detail: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves enterprise custom field definitions.
        GET /custom-fields?detail=true
        """
        params = {"detail": "true"} if detail else {}
        data = self._request("GET", "/custom-fields", params=params)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data") or []
        return []

    def get_custom_actions(self, detail: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieves enterprise custom action definitions.
        GET /custom-actions?detail=true
        """
        params = {"detail": "true"} if detail else {}
        data = self._request("GET", "/custom-actions", params=params)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data") or []
        return []

    def get_team_members(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieves all enterprise team members by paginating /team-members with limit=10.
        Paginates until total_count is reached or page returns fewer than limit rows.
        """
        all_members = []
        skip = 0
        limit = 10

        while True:
            params = {"skip": skip, "limit": limit}
            if include_deleted:
                params["includeDeleted"] = "true"

            try:
                data = self._request("GET", "/team-members", params=params)
            except TeleCRMError:
                data = self._request("GET", "/team-members/list", params=params)

            page = []
            total = 0
            if isinstance(data, list):
                page = data
                total = len(data)
            elif isinstance(data, dict):
                page = data.get("data") or data.get("team_members") or []
                total = data.get("total_count", 0)

            if not page:
                break

            all_members.extend(page)
            skip += len(page)

            if total and skip >= total:
                break
            if len(page) < limit:
                break

        return all_members

    def get_lead_stage_pipeline(self) -> Dict[str, Any]:
        """
        Retrieves enterprise lead stage pipeline and active status definitions.
        GET /lead-stage-pipeline
        """
        data = self._request("GET", "/lead-stage-pipeline")
        if isinstance(data, dict):
            return data
        return {"statuses": []}

    def get_file_download_url(self, lead_id: str, file_path: str) -> Dict[str, Any]:
        """
        Mints a short-lived download URL for a file or recording attached to a lead.
        GET /lead/{leadId}/file/download-url?path=<file_path>
        """
        data = self._request(
            "GET",
            f"/lead/{lead_id}/file/download-url",
            params={"path": file_path},
        )
        return data if isinstance(data, dict) else {}
