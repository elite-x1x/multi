import os
import json
import uuid
import requests
from datetime import datetime, timezone

from app3.menus.util import live_loading
from app3.config.theme_config import get_theme
from app3.client.encrypt import (
    encryptsign_xdata,
    java_like_timestamp,
    decrypt_xdata,
    API_KEY,
)

BASE_API_URL = os.getenv("BASE_API_URL")
if not BASE_API_URL:
    raise ValueError("BASE_API_URL environment variable tidak diset")
UA = os.getenv("UA")


def send_api_request(api_key: str, path: str, payload_dict: dict, id_token: str, method: str = "POST"):
    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method=method,
        path=path,
        id_token=id_token,
        payload=payload_dict,
    )

    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    now = datetime.now(timezone.utc).astimezone()
    sig_time_sec = xtime // 1000

    body = encrypted_payload["encrypted_body"]
    x_sig = encrypted_payload["x_signature"]

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {id_token}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(now),
        "x-version-app": "8.10.0",
    }

    url = f"{BASE_API_URL}/{path}"
    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        return decrypt_xdata(api_key, json.loads(resp.text))
    except Exception as e:
        return {"error": f"Gagal decrypt response: {e}", "raw": resp.text}


def _with_loading(message: str, func, use_loading: bool, theme, *args, **kwargs):
    if use_loading:
        with live_loading(message, theme):
            return func(*args, **kwargs)
    return func(*args, **kwargs)


# ============================
# API Wrapper Functions
# ============================

def get_profile(api_key: str, access_token: str, id_token: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/profile"
    payload = {
        "access_token": access_token,
        "app_version": "8.10.0",
        "is_enterprise": False,
        "lang": "en",
    }
    return _with_loading("📡 Mengambil profil...", send_api_request, use_loading, get_theme(),
                         api_key, path, payload, id_token, "POST").get("data")


def get_balance(api_key: str, id_token: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/packages/balance-and-credit"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("💰 Mengambil saldo...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, id_token, "POST")
    return res.get("data", {}).get("balance")


def get_family(api_key: str, tokens: dict, family_code: str,
               is_enterprise: bool | None = None,
               migration_type: str | None = None,
               use_loading: bool = True) -> dict | None:
    theme = get_theme()
    is_enterprise_list = [False, True] if is_enterprise is None else [is_enterprise]
    migration_type_list = ["NONE", "PRE_TO_PRIOH", "PRIOH_TO_PRIO", "PRIO_TO_PRIOH"] if migration_type is None else [migration_type]
    path = "api/v8/xl-stores/options/list"
    id_token = tokens.get("id_token")

    def _fetch_family():
        for mt in migration_type_list:
            for ie in is_enterprise_list:
                payload = {
                    "is_show_tagging_tab": True,
                    "is_dedicated_event": True,
                    "is_transaction_routine": False,
                    "migration_type": mt,
                    "package_family_code": family_code,
                    "is_autobuy": False,
                    "is_enterprise": ie,
                    "is_pdlp": True,
                    "referral_code": "",
                    "is_migration": False,
                    "lang": "en",
                }
                res = send_api_request(api_key, path, payload, id_token, "POST")
                if res.get("status") == "SUCCESS":
                    family_name = res["data"]["package_family"].get("name", "")
                    if family_name:
                        return res["data"]
        return None

    return _with_loading(f"📦 Mengambil family paket {family_code}...", _fetch_family, use_loading, theme)


def get_families(api_key: str, tokens: dict, package_category_code: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/xl-stores/families"
    payload = {
        "migration_type": "",
        "is_enterprise": False,
        "is_shareable": False,
        "package_category_code": package_category_code,
        "with_icon_url": True,
        "is_migration": False,
        "lang": "en",
    }
    res = _with_loading(f"📂 Mengambil families kategori {package_category_code}...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res.get("data") if res.get("status") == "SUCCESS" else None


def get_package(api_key: str, tokens: dict,
                package_option_code: str,
                package_family_code: str = "",
                package_variant_code: str = "",
                use_loading: bool = True) -> dict | None:
    path = "api/v8/xl-stores/options/detail"
    payload = {
        "is_transaction_routine": False,
        "migration_type": "NONE",
        "package_family_code": package_family_code,
        "family_role_hub": "",
        "is_autobuy": False,
        "is_enterprise": False,
        "is_shareable": False,
        "is_migration": False,
        "lang": "id",
        "package_option_code": package_option_code,
        "is_upsell_pdp": False,
        "package_variant_code": package_variant_code,
    }
    res = _with_loading("📦 Mengambil detail paket...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res.get("data")


def get_package_details(api_key: str, tokens: dict,
                        family_code: str, variant_code: str, option_order: int,
                        is_enterprise: bool | None = None,
                        migration_type: str | None = None,
                        use_loading: bool = True) -> dict | None:
    family_data = get_family(api_key, tokens, family_code, is_enterprise, migration_type, use_loading)
    if not family_data:
        return None

    option_code = None
    for variant in family_data.get("package_variants", []):
        if variant.get("package_variant_code") == variant_code:
            for option in variant.get("package_options", []):
                if option.get("order") == option_order:
                    option_code = option.get("package_option_code")
                    break
    if not option_code:
        return None

    return get_package(api_key, tokens, option_code, use_loading=use_loading)


def get_addons(api_key: str, tokens: dict, package_option_code: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/xl-stores/options/addons-pinky-box"
    payload = {"is_enterprise": False, "lang": "en", "package_option_code": package_option_code}
    res = _with_loading(f"🧩 Mengambil addons...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res.get("data")


def intercept_page(api_key: str, tokens: dict, option_code: str, is_enterprise: bool = False, use_loading: bool = True) -> dict | None:
    path = "misc/api/v8/utility/intercept-page"
    payload = {"is_enterprise": is_enterprise, "lang": "en", "package_option_code": option_code}
    return _with_loading(f"🛡️ Mengambil intercept...", send_api_request, use_loading, get_theme(),
                         api_key, path, payload, tokens["id_token"], "POST")


def login_info(api_key: str, tokens: dict, is_enterprise: bool = False, use_loading: bool = True) -> dict | None:
    path = "api/v8/auth/login"
    payload = {
        "access_token": tokens["access_token"],
        "is_enterprise": is_enterprise,
        "lang": "en",
    }
    res = _with_loading("🔑 Mengambil info login...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res.get("data")


def get_notifications(api_key: str, tokens: dict, use_loading: bool = True) -> dict | None:
    path = "api/v8/notification-non-grouping"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("🔔 Mengambil notifikasi...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res if res.get("status") == "SUCCESS" else None


def get_notification_detail(api_key: str, tokens: dict, notification_id: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/notification/detail"
    payload = {"is_enterprise": False, "lang": "en", "notification_id": notification_id}
    res = _with_loading(f"🔔 Mengambil detail notifikasi {notification_id}...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res if res.get("status") == "SUCCESS" else None


def get_pending_transaction(api_key: str, tokens: dict, use_loading: bool = True) -> dict | None:
    path = "api/v8/profile"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("⏳ Mengambil transaksi pending...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    data = res.get("data", {})
    return data if res.get("status") == "SUCCESS" and "pending_payment" in data else None


def get_transaction_history(api_key: str, tokens: dict, use_loading: bool = True) -> dict | None:
    path = "payments/api/v8/transaction-history"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("📜 Mengambil riwayat transaksi...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    data = res.get("data", {})
    return data if res.get("status") == "SUCCESS" and "list" in data else None


def get_tiering_info(api_key: str, tokens: dict, use_loading: bool = True) -> dict:
    path = "gamification/api/v8/loyalties/tiering/info"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("🏆 Mengambil info tiering...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return res.get("data", {}) if res and res.get("status") == "SUCCESS" else {}


def unsubscribe(api_key: str, tokens: dict,
                quota_code: str, product_domain: str, product_subscription_type: str,
                use_loading: bool = True) -> bool:
    path = "api/v8/packages/unsubscribe"
    payload = {
        "product_subscription_type": product_subscription_type,
        "quota_code": quota_code,
        "product_domain": product_domain,
        "is_enterprise": False,
        "unsubscribe_reason_code": "",
        "lang": "en",
        "family_member_id": "",
    }
    res = _with_loading(f"🚫 Unsubscribe kuota {quota_code}...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, tokens["id_token"], "POST")
    return bool(res and res.get("code") == "000")


def dashboard_segments(api_key: str, tokens: dict, use_loading: bool = True) -> dict:
    path = "dashboard/api/v8/segments"
    payload = {"access_token": tokens["access_token"]}
    return _with_loading("📊 Mengambil segmen dashboard...", send_api_request, use_loading, get_theme(),
                         api_key, path, payload, tokens["id_token"], "POST")


def dash_segments(api_key: str, id_token: str, access_token: str, balance: int = 0, use_loading: bool = True) -> dict | None:
    path = "dashboard/api/v8/segments"
    payload = {
        "access_token": access_token,
        "app_version": "8.10.0",
        "current_balance": balance,
        "family_plan_role": "NO_ROLE",
        "is_enterprise": False,
        "lang": "id",
        "manufacturer_name": "samsung",
        "model_name": "SM-N935F",
    }
    res = _with_loading("📊 Mengambil data segmen pengguna...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, id_token, "POST")
    if not (isinstance(res, dict) and "data" in res):
        return None

    data = res["data"]
    loyalty_data = data.get("loyalty", {}).get("data", {})
    loyalty_info = {
        "current_point": loyalty_data.get("current_point", 0),
        "tier_name": loyalty_data.get("detail_tier", {}).get("name", ""),
    }
    notifications = data.get("notification", {}).get("data", [])
    sfy_data = data.get("special_for_you", {}).get("data", {})
    sfy_banners = sfy_data.get("banners", [])
    special_packages = []

    for pkg in sfy_banners:
        try:
            if not pkg.get("action_param"):
                continue
            kuota_total = sum(
                int(benefit.get("total", 0))
                for benefit in pkg.get("benefits", [])
                if benefit.get("data_type") == "DATA"
            )
            kuota_gb = kuota_total / (1024 ** 3)
            original_price = int(pkg.get("original_price", 0))
            discounted_price = int(pkg.get("discounted_price", original_price))
            diskon_percent = int(round((original_price - discounted_price) / original_price * 100)) if original_price else 0

            special_packages.append({
                "name": f"{pkg.get('family_name', '')} ({pkg.get('title', '')}) {pkg.get('validity', '')}",
                "kode_paket": pkg.get("action_param", ""),
                "original_price": original_price,
                "diskon_price": discounted_price,
                "diskon_percent": diskon_percent,
                "kuota_gb": kuota_gb,
            })
        except Exception:
            continue

    return {
        "loyalty": loyalty_info,
        "notification": notifications,
        "special_packages": special_packages,
    }


def get_quota(api_key: str, id_token: str, use_loading: bool = True) -> dict | None:
    path = "api/v8/packages/quota-summary"
    payload = {"is_enterprise": False, "lang": "en"}
    res = _with_loading("📶 Mengambil ringkasan kuota...", send_api_request, use_loading, get_theme(),
                        api_key, path, payload, id_token, "POST")
    quota = res.get("data", {}).get("quota", {}).get("data")
    if quota:
        return {
            "remaining": quota.get("remaining", 0),
            "total": quota.get("total", 0),
            "has_unlimited": quota.get("has_unlimited", False),
        }
    return None
