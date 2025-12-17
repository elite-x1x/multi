import os
import json
import uuid
import requests
from datetime import datetime, timezone

from app2.client.engsel import BASE_API_URL, UA
from app2.client.encrypt import (
    API_KEY,
    build_encrypted_field,
    decrypt_xdata,
    encryptsign_xdata,
    get_x_signature_loyalty,
    java_like_timestamp,
    get_x_signature_bounty,
    get_x_signature_bounty_allotment,
)
from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme

BASE_API_URL = os.getenv("BASE_API_URL")
AX_FP = os.getenv("AX_FP")
UA = os.getenv("UA")


def settlement_bounty(api_key: str, tokens: dict,
                      token_confirmation: str, ts_to_sign: int,
                      payment_target: str, price: int,
                      item_name: str = "") -> dict | None:
    path = "api/v8/personalization/bounties-exchange"
    settlement_payload = {
        "total_discount": 0,
        "is_enterprise": False,
        "payment_method": "BALANCE",
        "timestamp": ts_to_sign,
        "payment_for": "REDEEM_VOUCHER",
        "token_confirmation": token_confirmation,
        "access_token": tokens["access_token"],
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "items": [{
            "item_code": payment_target,
            "item_price": price,
            "item_name": item_name,
            "tax": 0
        }]
    }

    encrypted_payload = encryptsign_xdata(api_key, "POST", path, tokens["id_token"], settlement_payload)
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    body = encrypted_payload["encrypted_body"]

    x_sig = get_x_signature_bounty(api_key, tokens["access_token"], ts_to_sign,
                                   payment_target, token_confirmation)

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.10.0",
    }

    url = f"{BASE_API_URL}/{path}"
    with live_loading("Mengirim bounty request...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        status = decrypted_body.get("status", "UNKNOWN")
        message = decrypted_body.get("message", "")

        print_panel("Bounty Status", f"Status: {status}\nPesan: {message}")
        return {"status": status, "message": message, "data": decrypted_body}
    except Exception as e:
        print_panel("Bounty Status", f"Kesalahan\nPesan: Error decrypt: {e}")
        return {"status": "ERROR", "message": f"Decrypt error: {e}", "data": None}


def settlement_loyalty(api_key: str, tokens: dict,
                       token_confirmation: str, ts_to_sign: int,
                       payment_target: str, price: int) -> dict | None:
    path = "gamification/api/v8/loyalties/tiering/exchange"
    settlement_payload = {
        "item_code": payment_target,
        "points": price,
        "timestamp": ts_to_sign,
        "token_confirmation": token_confirmation,
        "is_enterprise": False,
        "lang": "en",
    }

    encrypted_payload = encryptsign_xdata(api_key, "POST", path, tokens["id_token"], settlement_payload)
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    body = encrypted_payload["encrypted_body"]

    x_sig = get_x_signature_loyalty(api_key, ts_to_sign, payment_target, token_confirmation, path)

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.10.0",
    }

    url = f"{BASE_API_URL}/{path}"
    with live_loading("Mengirim loyalty request...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        status = decrypted_body.get("status", "UNKNOWN")
        message = decrypted_body.get("message", "")

        print_panel("Loyalty Status", f"Status: {status}\nPesan: {message}")
        return {"status": status, "message": message, "data": decrypted_body}
    except Exception as e:
        print_panel("Loyalty Status", f"Kesalahan\nPesan: Error decrypt: {e}")
        return {"status": "ERROR", "message": f"Decrypt error: {e}", "data": None}


def bounty_allotment(api_key: str, tokens: dict,
                     ts_to_sign: int, destination_msisdn: str,
                     item_name: str, item_code: str,
                     token_confirmation: str) -> dict | None:
    path = "gamification/api/v8/loyalties/tiering/bounties-allotment"
    settlement_payload = {
        "destination_msisdn": destination_msisdn,
        "item_code": item_code,
        "item_name": item_name,
        "timestamp": int(datetime.now().timestamp()),
        "token_confirmation": token_confirmation,
        "is_enterprise": False,
        "lang": "en",
    }

    encrypted_payload = encryptsign_xdata(api_key, "POST", path, tokens["id_token"], settlement_payload)
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    body = encrypted_payload["encrypted_body"]

    x_sig = get_x_signature_bounty_allotment(api_key, ts_to_sign, item_code,
                                             token_confirmation, destination_msisdn, path)

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.10.0",
    }

    url = f"{BASE_API_URL}/{path}"
    with live_loading("Mengirim bounty allotment...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        status = decrypted_body.get("status", "UNKNOWN")
        message = decrypted_body.get("message", "")

        print_panel("Bounty Allotment Status", f"Status: {status}\nPesan: {message}")
        return {"status": status, "message": message, "data": decrypted_body}
    except Exception as e:
        print_panel("Bounty Allotment Status", f"Kesalahan\nPesan: Error decrypt: {e}")
        return {"status": "ERROR", "message": f"Decrypt error: {e}", "data": None}
