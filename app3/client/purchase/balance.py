import json
import time
import uuid
import requests
from datetime import timezone, datetime

from app3.client.encrypt import (
    API_KEY,
    build_encrypted_field,
    decrypt_xdata,
    encryptsign_xdata,
    get_x_signature_payment,
    java_like_timestamp,
)
from app3.client.engsel import BASE_API_URL, UA, intercept_page, send_api_request
from app.type_dict import PaymentItem
from app3.menus.util import live_loading, print_error, print_success, print_panel
from app3.config.theme_config import get_theme


def settlement_balance(
    api_key: str,
    tokens: dict,
    items: list[PaymentItem],
    payment_for: str,
    ask_overwrite: bool,
    overwrite_amount: int = -1,
    token_confirmation_idx: int = 0,
    amount_idx: int = -1,
    topup_number: str = "",
    stage_token: str = "",
):
    # Sanity check
    if overwrite_amount == -1 and not ask_overwrite:
        print_error("⚠️ Ups", "Harus ada overwrite_amount atau flag ask_overwrite bro 🚨")
        return None

    token_confirmation = items[token_confirmation_idx]["token_confirmation"]
    payment_targets = ";".join([item["item_code"] for item in items])

    # Determine amount to use
    if overwrite_amount != -1:
        amount_int = overwrite_amount
    elif amount_idx == -1:
        amount_int = items[amount_idx]["item_price"]

    # If Overwrite
    if ask_overwrite:
        print_panel("💰 Amount", f"Total {amount_int}. Masukin nominal baru kalo mau overwrite bro ✌️")
        amount_str = input("Press enter to ignore & use default amount: ")
        if amount_str != "":
            try:
                amount_int = int(amount_str)
            except ValueError:
                print_warning("⚠️ Ups", "Input overwrite ngaco, pake harga asli aja 🚨")

    intercept_page(api_key, tokens, items[0]["item_code"], False)

    # Get payment methods
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": items[token_confirmation_idx]["item_code"],
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation,
    }

    with live_loading("💳 Getting payment methods...", get_theme()):
        payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")

    if payment_res.get("status") != "SUCCESS":
        print_error("⚠️ Ups", "Gagal ambil payment methods bro 🚨")
        print_panel("📑 Response", json.dumps(payment_res, indent=2))
        return payment_res

    token_payment = payment_res["data"]["token_payment"]
    ts_to_sign = payment_res["data"]["timestamp"]

    # Settlement request
    path = "payments/api/v8/settlement-multipayment"
    settlement_payload = {
        "total_discount": 0,
        "is_enterprise": False,
        "payment_token": "",
        "token_payment": token_payment,
        "activated_autobuy_code": "",
        "cc_payment_type": "",
        "is_myxl_wallet": False,
        "pin": "",
        "ewallet_promo_id": "",
        "members": [],
        "total_fee": 0,
        "fingerprint": "",
        "autobuy_threshold_setting": {"label": "", "type": "", "value": 0},
        "is_use_point": False,
        "lang": "en",
        "payment_method": "BALANCE",
        "timestamp": int(time.time()),
        "points_gained": 0,
        "can_trigger_rating": False,
        "akrab_members": [],
        "akrab_parent_alias": "",
        "referral_unique_code": "",
        "coupon": "",
        "payment_for": payment_for,
        "with_upsell": False,
        "topup_number": topup_number,
        "stage_token": stage_token,
        "authentication_id": "",
        "encrypted_payment_token": build_encrypted_field(urlsafe_b64=True),
        "token": "",
        "token_confirmation": "",
        "access_token": tokens["access_token"],
        "wallet_number": "",
        "encrypted_authentication_id": build_encrypted_field(urlsafe_b64=True),
        "additional_data": {
            "original_price": items[-1]["item_price"],
            "is_spend_limit_temporary": False,
            "migration_type": "",
            "akrab_m2m_group_id": "false",
            "spend_limit_amount": 0,
            "is_spend_limit": False,
            "mission_id": "",
            "tax": 0,
            "quota_bonus": 0,
            "cashtag": "",
            "is_family_plan": False,
            "combo_details": [],
            "is_switch_plan": False,
            "discount_recurring": 0,
            "is_akrab_m2m": False,
            "balance_type": "PREPAID_BALANCE",
            "has_bonus": False,
            "discount_promo": 0,
        },
        "total_amount": amount_int,
        "is_using_autobuy": False,
        "items": items,
    }

    encrypted_payload = encryptsign_xdata(
        api_key=api_key,
        method="POST",
        path=path,
        id_token=tokens["id_token"],
        payload=settlement_payload,
    )

    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    settlement_payload["timestamp"] = ts_to_sign

    body = encrypted_payload["encrypted_body"]
    x_sig = get_x_signature_payment(
        api_key,
        tokens["access_token"],
        ts_to_sign,
        payment_targets,
        token_payment,
        "BALANCE",
        payment_for,
        path,
    )

    headers = {
        "host": BASE_API_URL.replace("https://", ""),
        "content-type": "application/json; charset=utf-8",
        "user-agent": UA,
        "x-api-key": API_KEY,
        "authorization": f"Bearer {tokens['id_token']}",
        "x-hv": "v3",
        "x-signature-time": str(sig_time_sec),
        "x-signature": x_sig,
        "x-request-id": str(uuid.uuid4()),
        "x-request-at": java_like_timestamp(x_requested_at),
        "x-version-app": "8.10.0",
    }

    url = f"{BASE_API_URL}/{path}"
    with live_loading("📤 Lagi kirim settlement request bro...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        if decrypted_body.get("status") != "SUCCESS":
            print_error("⚠️ Ups", "Settlement gagal bro 🚨")
            print_panel("📑 Response", json.dumps(decrypted_body, indent=2))
            return decrypted_body

        print_success("✅ Mantap", "Pembelian sukses bro 🚀")
        print_panel("🧾 Purchase Result", json.dumps(decrypted_body, indent=2))
        return decrypted_body
    except Exception as e:
        print_error("⚠️ Ups", f"Error decrypt: {e} 🤯")
        print_panel("📑 Raw Response", resp.text)
        return resp.text
