"""
Enterprise Environment Synchronizer for Multi-Account Meta Integration.
Parses, normalizes, and auto-provisions multiple WhatsApp Business Lines
and Facebook Pages/Ad accounts configured via .env variables.
Supports 8+ developer accounts with dedicated secrets, verify tokens, and branch mappings.
"""

import os
import json
import logging
from typing import Dict, List, Set, Any, Optional
from django.conf import settings
from django.db import transaction

logger = logging.getLogger("crm")


def split_env_list(raw_val: Optional[str]) -> List[str]:
    """
    Splits a comma-, newline-, or semicolon-separated environment variable string into stripped tokens.
    """
    if not raw_val:
        return []
    clean_items = []
    # Replace newlines and semicolons with commas
    normalized = str(raw_val).replace("\n", ",").replace(";", ",")
    for part in normalized.split(","):
        p = part.strip()
        if p and p not in clean_items:
            clean_items.append(p)
    return clean_items


def get_candidate_webhook_secrets(provider: str = "all") -> Set[str]:
    """
    Aggregates all candidate Meta App Secrets from settings, environment variables,
    and active database records for multi-developer webhook HMAC validation.
    Splits any comma-, newline-, or semicolon-separated tokens into individual secrets.
    """
    secrets: Set[str] = set()

    # 1. Global settings and environment secrets
    if provider in ("all", "facebook"):
        fb_sec = getattr(settings, "FB_APP_SECRET", "") or os.getenv("FB_APP_SECRET", "")
        for s in split_env_list(fb_sec):
            secrets.add(s)
        raw_fb_secrets = getattr(settings, "FB_APP_SECRETS", "") or os.getenv("FB_APP_SECRETS", "")
        for s in split_env_list(raw_fb_secrets):
            secrets.add(s)

    if provider in ("all", "whatsapp"):
        wa_sec = getattr(settings, "WHATSAPP_APP_SECRET", "") or os.getenv("WHATSAPP_APP_SECRET", "")
        for s in split_env_list(wa_sec):
            secrets.add(s)
        raw_wa_secrets = getattr(settings, "WHATSAPP_APP_SECRETS", "") or os.getenv("WHATSAPP_APP_SECRETS", "")
        for s in split_env_list(raw_wa_secrets):
            secrets.add(s)

    # 2. Numbered environment variables (e.g. WHATSAPP_1_APP_SECRET, FB_PAGE_1_APP_SECRET)
    for k, v in os.environ.items():
        if not v or not v.strip():
            continue
        k_upper = k.upper()
        if provider in ("all", "whatsapp") and (k_upper.startswith("WHATSAPP_") and k_upper.endswith("_APP_SECRET")):
            for s in split_env_list(v):
                secrets.add(s)
        elif provider in ("all", "facebook") and (k_upper.startswith("FB_") and k_upper.endswith("_APP_SECRET")):
            for s in split_env_list(v):
                secrets.add(s)

    # 3. Database stored secrets on active WhatsApp Business Accounts & Facebook Accounts
    if provider in ("all", "whatsapp"):
        try:
            from chat.models import BusinessAccount
            db_wa_secrets = BusinessAccount.objects.filter(is_active=True).exclude(app_secret="").values_list("app_secret", flat=True)
            for s in db_wa_secrets:
                for item in split_env_list(s):
                    secrets.add(item)
        except Exception as exc:
            logger.debug("Could not query BusinessAccount app_secrets: %s", exc)

    if provider in ("all", "facebook"):
        try:
            from fb_leads.models import FacebookAccount
            db_fb_secrets = FacebookAccount.objects.exclude(app_secret="").values_list("app_secret", flat=True)
            for s in db_fb_secrets:
                for item in split_env_list(s):
                    secrets.add(item)
        except Exception as exc:
            logger.debug("Could not query FacebookAccount app_secrets: %s", exc)

    return secrets


def get_candidate_verify_tokens(provider: str = "all") -> Set[str]:
    """
    Aggregates all candidate Webhook Verify Tokens from settings, environment variables,
    and active database records for multi-developer webhook subscription handshakes.
    Splits any comma-, newline-, or semicolon-separated tokens into individual tokens.
    """
    tokens: Set[str] = set()

    # 1. Global settings and environment tokens
    if provider in ("all", "facebook"):
        fb_tok = getattr(settings, "FB_VERIFY_TOKEN", "") or os.getenv("FB_VERIFY_TOKEN", "")
        for t in split_env_list(fb_tok):
            tokens.add(t)
        raw_fb_tokens = getattr(settings, "FB_VERIFY_TOKENS", "") or os.getenv("FB_VERIFY_TOKENS", "")
        for t in split_env_list(raw_fb_tokens):
            tokens.add(t)

    if provider in ("all", "whatsapp"):
        wa_tok = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "") or os.getenv("WHATSAPP_VERIFY_TOKEN", "")
        for t in split_env_list(wa_tok):
            tokens.add(t)
        raw_wa_tokens = getattr(settings, "WHATSAPP_VERIFY_TOKENS", "") or os.getenv("WHATSAPP_VERIFY_TOKENS", "")
        for t in split_env_list(raw_wa_tokens):
            tokens.add(t)

    # 2. Numbered environment variables (e.g. WHATSAPP_1_VERIFY_TOKEN, FB_PAGE_1_VERIFY_TOKEN)
    for k, v in os.environ.items():
        if not v or not v.strip():
            continue
        k_upper = k.upper()
        if provider in ("all", "whatsapp") and (k_upper.startswith("WHATSAPP_") and k_upper.endswith("_VERIFY_TOKEN")):
            for t in split_env_list(v):
                tokens.add(t)
        elif provider in ("all", "facebook") and (k_upper.startswith("FB_") and k_upper.endswith("_VERIFY_TOKEN")):
            for t in split_env_list(v):
                tokens.add(t)

    # 3. Database stored verify tokens on active WhatsApp Business Accounts & Facebook Accounts
    if provider in ("all", "whatsapp"):
        try:
            from chat.models import BusinessAccount
            db_wa_tokens = BusinessAccount.objects.filter(is_active=True).exclude(verify_token="").values_list("verify_token", flat=True)
            for t in db_wa_tokens:
                for item in split_env_list(t):
                    tokens.add(item)
        except Exception as exc:
            logger.debug("Could not query BusinessAccount verify_tokens: %s", exc)

    if provider in ("all", "facebook"):
        try:
            from fb_leads.models import FacebookAccount
            db_fb_tokens = FacebookAccount.objects.exclude(verify_token="").values_list("verify_token", flat=True)
            for t in db_fb_tokens:
                for item in split_env_list(t):
                    tokens.add(item)
        except Exception as exc:
            logger.debug("Could not query FacebookAccount verify_tokens: %s", exc)

    return tokens


def parse_whatsapp_env_accounts() -> List[Dict[str, Any]]:
    """
    Extracts all WhatsApp accounts defined in .env, supporting:
    1. JSON block: WHATSAPP_ACCOUNTS_JSON
    2. Numbered indexing: WHATSAPP_1_*, WHATSAPP_2_*, ... up to WHATSAPP_50_*
    3. Legacy single account fallback: WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN
    """
    accounts: List[Dict[str, Any]] = []
    seen_phone_ids: Set[str] = set()

    # 1. Check for JSON array specification
    json_spec = os.getenv("WHATSAPP_ACCOUNTS_JSON", "").strip()
    if json_spec:
        try:
            parsed = json.loads(json_spec)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and item.get("phone_number_id") or item.get("phone_id"):
                        phone_id = str(item.get("phone_number_id") or item.get("phone_id")).strip()
                        if phone_id not in seen_phone_ids:
                            accounts.append({
                                "name": item.get("name") or f"WhatsApp Line ({phone_id})",
                                "phone_number": item.get("phone") or item.get("phone_number") or "",
                                "phone_number_id": phone_id,
                                "business_account_id": str(item.get("business_account_id") or item.get("waba_id") or "").strip(),
                                "access_token": item.get("access_token") or item.get("token") or "",
                                "app_secret": item.get("app_secret") or "",
                                "verify_token": item.get("verify_token") or "",
                                "branch": item.get("branch") or "",
                                "automation_enabled": item.get("automation_enabled", True),
                                "is_default": bool(item.get("is_default", False)),
                            })
                            seen_phone_ids.add(phone_id)
        except Exception as exc:
            logger.warning("Failed parsing WHATSAPP_ACCOUNTS_JSON: %s", exc)

    # 2. Check numbered indexing: WHATSAPP_1_*, WHATSAPP_2_*, up to 50
    for idx in range(1, 51):
        prefix = f"WHATSAPP_{idx}_"
        phone_id = (
            os.getenv(f"{prefix}PHONE_ID")
            or os.getenv(f"{prefix}PHONE_NUMBER_ID")
            or ""
        ).strip()

        if not phone_id or phone_id in seen_phone_ids:
            continue

        name = (os.getenv(f"{prefix}NAME") or f"WhatsApp Line {idx}").strip()
        phone = (os.getenv(f"{prefix}PHONE") or os.getenv(f"{prefix}PHONE_NUMBER") or "").strip()
        waba_id = (os.getenv(f"{prefix}WABA_ID") or os.getenv(f"{prefix}BUSINESS_ACCOUNT_ID") or "").strip()
        token = (os.getenv(f"{prefix}ACCESS_TOKEN") or os.getenv(f"{prefix}TOKEN") or "").strip()
        app_sec = os.getenv(f"{prefix}APP_SECRET", "").strip()
        ver_tok = os.getenv(f"{prefix}VERIFY_TOKEN", "").strip()
        branch_name = os.getenv(f"{prefix}BRANCH", "").strip()
        auto_en_raw = os.getenv(f"{prefix}AUTOMATION_ENABLED", "true").lower()
        auto_enabled = auto_en_raw in ("true", "1", "yes")
        is_def_raw = os.getenv(f"{prefix}IS_DEFAULT", "false").lower()
        is_default = (idx == 1 and not seen_phone_ids) or is_def_raw in ("true", "1", "yes")

        accounts.append({
            "name": name,
            "phone_number": phone,
            "phone_number_id": phone_id,
            "business_account_id": waba_id,
            "access_token": token,
            "app_secret": app_sec,
            "verify_token": ver_tok,
            "branch": branch_name,
            "automation_enabled": auto_enabled,
            "is_default": is_default,
        })
        seen_phone_ids.add(phone_id)

    # 3. Fallback to default single account in .env if not already loaded
    default_phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if default_phone_id and default_phone_id not in seen_phone_ids:
        accounts.append({
            "name": "Default WhatsApp Line",
            "phone_number": os.getenv("WHATSAPP_PHONE_NUMBER", "+91 84382 39448"),
            "phone_number_id": default_phone_id,
            "business_account_id": getattr(settings, "WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip(),
            "access_token": getattr(settings, "WHATSAPP_ACCESS_TOKEN", "").strip(),
            "app_secret": getattr(settings, "WHATSAPP_APP_SECRET", "").strip(),
            "verify_token": getattr(settings, "WHATSAPP_VERIFY_TOKEN", "").strip(),
            "branch": getattr(settings, "WHATSAPP_DEFAULT_BRANCH", "").strip(),
            "automation_enabled": True,
            "is_default": not seen_phone_ids,
        })
        seen_phone_ids.add(default_phone_id)

    return accounts


def parse_facebook_env_pages() -> List[Dict[str, Any]]:
    """
    Extracts all Facebook Pages/Accounts defined in .env, supporting:
    1. JSON block: FB_PAGES_JSON
    2. Numbered indexing: FB_PAGE_1_*, FB_PAGE_2_*, ... up to FB_PAGE_50_*
    3. Legacy single page fallback: FB_PAGE_ID, FB_PAGE_TOKEN
    """
    pages: List[Dict[str, Any]] = []
    seen_page_ids: Set[str] = set()

    # 1. Check for JSON array specification
    json_spec = os.getenv("FB_PAGES_JSON", "").strip()
    if json_spec:
        try:
            parsed = json.loads(json_spec)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and item.get("page_id"):
                        page_id = str(item.get("page_id")).strip()
                        if page_id not in seen_page_ids:
                            pages.append({
                                "account_name": item.get("account_name") or f"Meta Dev Account ({page_id})",
                                "page_name": item.get("page_name") or item.get("name") or f"Facebook Page ({page_id})",
                                "page_id": page_id,
                                "page_access_token": item.get("page_access_token") or item.get("token") or "",
                                "app_id": str(item.get("app_id") or "").strip(),
                                "app_secret": item.get("app_secret") or "",
                                "verify_token": item.get("verify_token") or "",
                                "branch": item.get("branch") or "",
                                "auto_sync_enabled": item.get("auto_sync_enabled", True),
                                "sync_interval_minutes": int(item.get("sync_interval_minutes") or 3),
                            })
                            seen_page_ids.add(page_id)
        except Exception as exc:
            logger.warning("Failed parsing FB_PAGES_JSON: %s", exc)

    # 2. Check numbered indexing: FB_PAGE_1_*, FB_PAGE_2_*, up to 50
    for idx in range(1, 51):
        prefix = f"FB_PAGE_{idx}_"
        page_id = os.getenv(f"{prefix}PAGE_ID", "").strip()
        if not page_id or page_id in seen_page_ids:
            continue

        acc_name = (os.getenv(f"{prefix}ACCOUNT_NAME") or f"Meta Developer Account {idx}").strip()
        page_name = (os.getenv(f"{prefix}NAME") or os.getenv(f"{prefix}PAGE_NAME") or f"Facebook Page {idx}").strip()
        token = (os.getenv(f"{prefix}TOKEN") or os.getenv(f"{prefix}PAGE_ACCESS_TOKEN") or "").strip()
        app_id = os.getenv(f"{prefix}APP_ID", "").strip()
        app_sec = os.getenv(f"{prefix}APP_SECRET", "").strip()
        ver_tok = os.getenv(f"{prefix}VERIFY_TOKEN", "").strip()
        branch_name = os.getenv(f"{prefix}BRANCH", "").strip()
        auto_en_raw = os.getenv(f"{prefix}AUTO_SYNC_ENABLED", "true").lower()
        auto_sync = auto_en_raw in ("true", "1", "yes")

        try:
            interval = int(os.getenv(f"{prefix}SYNC_INTERVAL_MINUTES", "3"))
        except ValueError:
            interval = 3

        pages.append({
            "account_name": acc_name,
            "page_name": page_name,
            "page_id": page_id,
            "page_access_token": token,
            "app_id": app_id,
            "app_secret": app_sec,
            "verify_token": ver_tok,
            "branch": branch_name,
            "auto_sync_enabled": auto_sync,
            "sync_interval_minutes": interval,
        })
        seen_page_ids.add(page_id)

    # 3. Fallback to default single page in .env if not already loaded
    default_page_id = getattr(settings, "FB_PAGE_ID", "").strip()
    if default_page_id and default_page_id not in seen_page_ids:
        pages.append({
            "account_name": "Default Facebook Connection",
            "page_name": os.getenv("FB_PAGE_NAME", "Default Facebook Page"),
            "page_id": default_page_id,
            "page_access_token": getattr(settings, "FB_PAGE_TOKEN", "").strip(),
            "app_id": os.getenv("FB_APP_ID", "").strip(),
            "app_secret": getattr(settings, "FB_APP_SECRET", "").strip(),
            "verify_token": getattr(settings, "FB_VERIFY_TOKEN", "").strip(),
            "branch": getattr(settings, "FB_DEFAULT_BRANCH", "").strip(),
            "auto_sync_enabled": True,
            "sync_interval_minutes": 3,
        })
        seen_page_ids.add(default_page_id)

    return pages


def resolve_branch_by_name(branch_name: str) -> Optional[Any]:
    """
    Resolves a Branch foreign key by name or alias, supporting hyphens, dots, and partial matches.
    """
    if not branch_name:
        return None
    try:
        from branches.models import Branch
        b_clean = branch_name.strip()
        # 1. Direct exact or substring match
        branch = Branch.objects.filter(name__iexact=b_clean).first()
        if branch:
            return branch
        # 2. Hyphen / space / dot variations (e.g. T-Nagar vs T. Nagar vs T Nagar)
        alt_space = b_clean.replace("-", " ")
        alt_dot = b_clean.replace("-", ". ")
        alt_clean = b_clean.replace(".", "").replace("-", " ")
        branch = (
            Branch.objects.filter(name__iexact=alt_space).first()
            or Branch.objects.filter(name__iexact=alt_dot).first()
            or Branch.objects.filter(name__iexact=alt_clean).first()
            or Branch.objects.filter(name__icontains=b_clean).first()
            or Branch.objects.filter(name__icontains=alt_space).first()
        )
        if branch:
            return branch
        # 3. Alphanumeric canonical match
        alpha_input = "".join(c.lower() for c in b_clean if c.isalnum())
        for candidate in Branch.objects.all():
            alpha_cand = "".join(c.lower() for c in candidate.name if c.isalnum())
            if alpha_input and (alpha_input == alpha_cand or alpha_input in alpha_cand or alpha_cand in alpha_input):
                return candidate
        return None
    except Exception as exc:
        logger.debug("Could not resolve branch %s: %s", branch_name, exc)
        return None


def sync_all_env_meta_accounts(stdout=None) -> Dict[str, int]:
    """
    Synchronizes all WhatsApp Business Lines and Facebook Pages configured in .env
    into their respective CRM database models without destroying existing relations or leads.
    """
    stats = {
        "whatsapp_created": 0,
        "whatsapp_updated": 0,
        "facebook_created": 0,
        "facebook_updated": 0,
    }

    # 1. Sync WhatsApp accounts
    wa_configs = parse_whatsapp_env_accounts()
    if wa_configs:
        from chat.models import BusinessAccount
        with transaction.atomic():
            for cfg in wa_configs:
                phone_id = cfg["phone_number_id"]
                branch = resolve_branch_by_name(cfg.get("branch", ""))
                ba = BusinessAccount.objects.filter(phone_number_id=phone_id).first()

                if ba:
                    update_fields = []
                    if cfg["name"] and ba.name != cfg["name"]:
                        ba.name = cfg["name"]
                        update_fields.append("name")
                    if cfg["phone_number"] and ba.phone_number != cfg["phone_number"]:
                        ba.phone_number = cfg["phone_number"]
                        update_fields.append("phone_number")
                    if cfg["business_account_id"] and ba.business_account_id != cfg["business_account_id"]:
                        ba.business_account_id = cfg["business_account_id"]
                        update_fields.append("business_account_id")
                    if cfg["access_token"] and ba.access_token != cfg["access_token"]:
                        ba.access_token = cfg["access_token"]
                        update_fields.append("access_token")
                    if cfg["app_secret"] and ba.app_secret != cfg["app_secret"]:
                        ba.app_secret = cfg["app_secret"]
                        update_fields.append("app_secret")
                    if cfg["verify_token"] and ba.verify_token != cfg["verify_token"]:
                        ba.verify_token = cfg["verify_token"]
                        update_fields.append("verify_token")
                    if branch and ba.crm_branch != branch:
                        ba.crm_branch = branch
                        update_fields.append("crm_branch")
                    if ba.automation_enabled != cfg["automation_enabled"]:
                        ba.automation_enabled = cfg["automation_enabled"]
                        update_fields.append("automation_enabled")
                    if not ba.is_active:
                        ba.is_active = True
                        update_fields.append("is_active")
                    if cfg.get("is_default") and not ba.is_default:
                        BusinessAccount.objects.exclude(pk=ba.pk).update(is_default=False)
                        ba.is_default = True
                        update_fields.append("is_default")

                    if update_fields:
                        ba.save(update_fields=update_fields)
                        stats["whatsapp_updated"] += 1
                else:
                    BusinessAccount.objects.create(
                        name=cfg["name"],
                        phone_number=cfg["phone_number"] or phone_id,
                        phone_number_id=phone_id,
                        business_account_id=cfg["business_account_id"],
                        access_token=cfg["access_token"],
                        app_secret=cfg["app_secret"],
                        verify_token=cfg["verify_token"],
                        crm_branch=branch,
                        automation_enabled=cfg["automation_enabled"],
                        is_default=cfg["is_default"],
                        is_active=True
                    )
                    stats["whatsapp_created"] += 1

    # 2. Sync Facebook pages
    fb_configs = parse_facebook_env_pages()
    if fb_configs:
        from fb_leads.models import FacebookAccount, FacebookPage
        with transaction.atomic():
            for cfg in fb_configs:
                page_id = cfg["page_id"]
                branch = resolve_branch_by_name(cfg.get("branch", ""))

                # Ensure parent FacebookAccount connection exists
                fb_account, _ = FacebookAccount.objects.get_or_create(
                    account_name=cfg["account_name"],
                    defaults={
                        "access_token": cfg["page_access_token"] or "env_managed_token",
                        "app_id": cfg.get("app_id", ""),
                        "app_secret": cfg.get("app_secret", ""),
                        "verify_token": cfg.get("verify_token", ""),
                        "status": "CONNECTED",
                    }
                )

                page = FacebookPage.objects.filter(page_id=page_id).first()
                if page:
                    update_fields = []
                    if cfg["page_name"] and page.page_name != cfg["page_name"]:
                        page.page_name = cfg["page_name"]
                        update_fields.append("page_name")
                    if cfg["page_access_token"] and page.page_access_token != cfg["page_access_token"]:
                        page.page_access_token = cfg["page_access_token"]
                        update_fields.append("page_access_token")
                    if branch and page.branch != branch:
                        page.branch = branch
                        update_fields.append("branch")
                    if page.auto_sync_enabled != cfg["auto_sync_enabled"]:
                        page.auto_sync_enabled = cfg["auto_sync_enabled"]
                        update_fields.append("auto_sync_enabled")
                    if page.sync_interval_minutes != cfg["sync_interval_minutes"]:
                        page.sync_interval_minutes = cfg["sync_interval_minutes"]
                        update_fields.append("sync_interval_minutes")
                    if page.status != "CONNECTED":
                        page.status = "CONNECTED"
                        update_fields.append("status")

                    if update_fields:
                        page.save(update_fields=update_fields)
                        stats["facebook_updated"] += 1
                else:
                    FacebookPage.objects.create(
                        account=fb_account,
                        page_id=page_id,
                        page_name=cfg["page_name"],
                        page_access_token=cfg["page_access_token"],
                        branch=branch,
                        auto_sync_enabled=cfg["auto_sync_enabled"],
                        sync_interval_minutes=cfg["sync_interval_minutes"],
                        status="CONNECTED",
                        webhook_subscribed=True
                    )
                    stats["facebook_created"] += 1

    if stdout:
        stdout.write(f"Meta accounts synced from .env: {stats}\n")

    return stats
