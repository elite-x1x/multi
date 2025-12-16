import base64
import os
import json
import uuid
import requests
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme
from app2.client.encrypt import (
    java_like_timestamp,
    ts_gmt7_without_colon,
    ax_api_signature,
    load_ax_fp,
    ax_device_id
)

BASE_CIAM_URL = os.getenv("BASE_CIAM_URL")
if not BASE_CIAM_URL:
    raise ValueError("BASE_CIAM_URL environment variable not set")

BASIC_AUTH = os.getenv("BASIC_AUTH")
AX_DEVICE_ID = ax_device_id()
AX_FP = load_ax_fp()
UA = os.getenv("UA")


def validate_contact(contact: str) -> bool:
    return contact.startswith("628") and len(contact) <= 14


def get_otp(contact: str) -> str | None:
    if not validate_contact(contact):
        print_panel("Kesalahan", "Nomor tidak valid.")
        return None

    url = BASE_CIAM_URL + "/realms/xl-ciam/auth/otp"
    querystring = {"contact": contact, "contactType": "SMS", "alternateContact": "false"}
    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = java_like_timestamp(now)
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Basic {BASIC_AUTH}",
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Fingerprint": AX_FP,
        "Ax-Request-At": ax_request_at,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": ax_request_id,
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/json",
        "Host": BASE_CIAM_URL.replace("https://", ""),
        "User-Agent": UA,
    }

    with live_loading(f"Meminta OTP untuk {contact}...", get_theme()):
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            json_body = response.json()
            if "subscriber_id" not in json_body:
                print_panel("Kesalahan", "OTP gagal diambil.")
                return None
            print_panel("Berhasil", f"OTP berhasil dikirim ke {contact}.")
            return json_body["subscriber_id"]
        except Exception:
            print_panel("Kesalahan", "Terjadi error saat request OTP.")
            return None


def extend_session(subscriber_id: str) -> str | None:
    b64_subscriber_id = base64.b64encode(subscriber_id.encode()).decode()
    url = f"{BASE_CIAM_URL}/realms/xl-ciam/auth/extend-session"
    querystring = {"contact": b64_subscriber_id, "contactType": "DEVICEID"}
    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = java_like_timestamp(now)
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Basic {BASIC_AUTH}",
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Fingerprint": AX_FP,
        "Ax-Request-At": ax_request_at,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": ax_request_id,
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/json",
        "Host": BASE_CIAM_URL.replace("https://", ""),
        "User-Agent": UA,
    }

    with live_loading("Memperpanjang session...", get_theme()):
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            if response.status_code != 200:
                print_panel("Kesalahan", "Extend session gagal.")
                return None
            data = response.json()
            print_panel("Berhasil", "Session berhasil diperpanjang.")
            return data.get("data", {}).get("exchange_code")
        except Exception:
            print_panel("Kesalahan", "Terjadi error saat extend session.")
            return None


def submit_otp(api_key: str, contact_type: str, contact: str, code: str) -> dict | None:
    if contact_type == "SMS":
        if not validate_contact(contact):
            print_panel("Kesalahan", "Nomor tidak valid.")
            return None
        if not code or len(code) != 6:
            print_panel("Kesalahan", "Kode OTP tidak valid.")
            return None
        final_contact = contact
        final_code = code
    elif contact_type == "DEVICEID":
        final_contact = base64.b64encode(contact.encode()).decode()
        final_code = code
    else:
        print_panel("Kesalahan", "Contact type tidak valid.")
        return None

    url = BASE_CIAM_URL + "/realms/xl-ciam/protocol/openid-connect/token"
    now_gmt7 = datetime.now(timezone(timedelta(hours=7)))
    ts_for_sign = ts_gmt7_without_colon(now_gmt7)
    ts_header = ts_gmt7_without_colon(now_gmt7 - timedelta(minutes=5))
    signature = ax_api_signature(api_key, ts_for_sign, final_contact, code, contact_type)

    payload = f"contactType={contact_type}&code={final_code}&grant_type=password&contact={final_contact}&scope=openid"
    headers = {
        "Authorization": f"Basic {BASIC_AUTH}",
        "Ax-Api-Signature": signature,
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Fingerprint": AX_FP,
        "Ax-Request-At": ts_header,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Request-Id": str(uuid.uuid4()),
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": UA,
    }

    with live_loading("Submit OTP...", get_theme()):
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=30)
            json_body = response.json()
            if "error" in json_body:
                print_panel("Kesalahan", "OTP ditolak.")
                return None
            print_panel("Berhasil", "OTP berhasil divalidasi.")
            return json_body
        except requests.RequestException:
            print_panel("Kesalahan", "Terjadi error saat submit OTP.")
            return None


def get_new_token(api_key: str, refresh_token: str, subscriber_id: str) -> dict | None:
    url = BASE_CIAM_URL + "/realms/xl-ciam/protocol/openid-connect/token"
    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0700"
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Host": BASE_CIAM_URL.replace("https://", ""),
        "ax-request-at": ax_request_at,
        "ax-device-id": AX_DEVICE_ID,
        "ax-request-id": ax_request_id,
        "ax-request-device": "samsung",
        "ax-request-device-model": "SM-N935F",
        "ax-fingerprint": AX_FP,
        "authorization": f"Basic {BASIC_AUTH}",
        "user-agent": UA,
        "ax-substype": "PREPAID",
        "content-type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}

    #with live_loading("Refresh token...", get_theme()):
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=30)
    except requests.RequestException:
        print_panel("Kesalahan", "Terjadi error saat refresh token.")
        return None

    if resp.status_code == 400:
        try:
            err_json = resp.json()
        except ValueError:
            return None
        if err_json.get("error_description") != "Session not active":
            return None
        if not subscriber_id:
            return None
        exchange_code = extend_session(subscriber_id)
        if not exchange_code:
            print_panel("Kesalahan", "Extend session gagal.")
            return None
        print_panel("Informasi", "Session expired, silakan submit OTP kembali.")
        return submit_otp(api_key, "DEVICEID", subscriber_id, exchange_code)

    try:
        resp.raise_for_status()
    except requests.HTTPError:
        print_panel("Kesalahan", "HTTP error saat refresh token.")
        return None

    try:
        body = resp.json()
    except ValueError:
        print_panel("Kesalahan", "Response token tidak valid.")
        return None

    if "id_token" not in body or "error" in body:
        print_panel("Kesalahan", "Token baru gagal diambil.")
        return None

    # print_panel("Berhasil", "Token baru berhasil diambil.")
    return body


def get_auth_code(tokens: dict, pin: str, msisdn: str) -> str | None:
    url = BASE_CIAM_URL + "/ciam/auth/authorization-token/generate"

    parsed = urlparse(BASE_CIAM_URL)
    host_header = parsed.netloc or BASE_CIAM_URL.replace("https://", "")

    now = datetime.now(timezone(timedelta(hours=7)))
    ax_request_at = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0700"
    ax_request_id = str(uuid.uuid4())

    headers = {
        "Host": host_header,
        "Ax-Request-At": ax_request_at,
        "Ax-Device-Id": AX_DEVICE_ID,
        "Ax-Request-Id": ax_request_id,
        "Ax-Request-Device": "samsung",
        "Ax-Request-Device-Model": "SM-N935F",
        "Ax-Fingerprint": AX_FP,
        "Authorization": f"Bearer {tokens['access_token']}",
        "User-Agent": UA,
        "Ax-Substype": "PREPAID",
        "Content-Type": "application/json",
    }

    pin_b64 = base64.b64encode(pin.encode("utf-8")).decode("utf-8")
    body = {
        "pin": pin_b64,
        "transaction_type": "SHARE_BALANCE",
        "receiver_msisdn": msisdn,
    }

    with live_loading(f"Meminta authorization code untuk {msisdn}...", get_theme()):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=30)
        except requests.RequestException:
            print_panel("Kesalahan", "Terjadi error saat request authorization code.")
            return None

    if resp.status_code != 200:
        print_panel("Kesalahan", "Authorization code gagal diambil.")
        return None

    try:
        data = resp.json()
    except ValueError:
        print_panel("Kesalahan", "Response authorization code tidak valid.")
        return None

    if not isinstance(data, dict):
        print_panel("Kesalahan", "Format data authorization code tidak valid.")
        return None

    status = data.get("status", "")
    message = data.get("message", "")

    if status == "Success":
        # print_panel("Berhasil", f"Authorization code berhasil diambil.\nPesan: {message}")
        pass
    else:
        print_panel("Kesalahan", f"Authorization code gagal.\nPesan: {message}")
        return None

    authorization_code = data.get("data", {}).get("authorization_code")
    if not authorization_code:
        print_panel("Kesalahan", "Authorization code kosong.")
        return None

    return authorization_code
