import json
import uuid
import base64
import qrcode
import time
import requests
from datetime import datetime, timezone

from app2.client.engsel import BASE_API_URL, UA, intercept_page, send_api_request
from app2.client.encrypt import API_KEY, decrypt_xdata, encryptsign_xdata, java_like_timestamp, get_x_signature_payment
from app.type_dict import PaymentItem
from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme


def settlement_qris(api_key: str, tokens: dict, items: list[PaymentItem],
                    payment_for: str, ask_overwrite: bool,
                    overwrite_amount: int = -1,
                    token_confirmation_idx: int = 0,
                    amount_idx: int = -1,
                    topup_number: str = "",
                    stage_token: str = "") -> str | None:
    if overwrite_amount == -1 and not ask_overwrite:
        print_panel("Kesalahan", "Harus ada overwrite_amount atau flag ask_overwrite.")
        return None

    token_confirmation = items[token_confirmation_idx]["token_confirmation"]
    payment_targets = ";".join([item["item_code"] for item in items])

    # Tentukan amount
    if overwrite_amount != -1:
        amount_int = overwrite_amount
    elif amount_idx == -1:
        amount_int = items[amount_idx]["item_price"]

    if ask_overwrite:
        print_panel("Amount", f"Total {amount_int}. Masukkan nominal baru jika ingin overwrite.")
        amount_str = input("Tekan enter untuk menggunakan nominal default: ")
        if amount_str:
            try:
                amount_int = int(amount_str)
            except ValueError:
                print_panel("Kesalahan", "Input overwrite tidak valid, menggunakan harga asli.")

    intercept_page(api_key, tokens, items[0]["item_code"], False)

    # Ambil payment methods
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": items[token_confirmation_idx]["item_code"],
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation,
    }

    with live_loading("Mengambil metode pembayaran...", get_theme()):
        payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")

    if payment_res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil metode pembayaran.")
        print_panel("Response", json.dumps(payment_res, indent=2))
        return None

    token_payment = payment_res["data"]["token_payment"]
    ts_to_sign = payment_res["data"]["timestamp"]

    # Settlement request
    path = "payments/api/v8/settlement-multipayment/qris"
    settlement_payload = {
        "akrab": {"akrab_members": [], "akrab_parent_alias": "", "members": []},
        "can_trigger_rating": False,
        "total_discount": 0,
        "coupon": "",
        "payment_for": payment_for,
        "topup_number": topup_number,
        "stage_token": stage_token,
        "is_enterprise": False,
        "autobuy": {
            "is_using_autobuy": False,
            "activated_autobuy_code": "",
            "autobuy_threshold_setting": {"label": "", "type": "", "value": 0},
        },
        "access_token": tokens["access_token"],
        "is_myxl_wallet": False,
        "additional_data": {
            "original_price": items[0]["item_price"],
            "is_spend_limit_temporary": False,
            "migration_type": "",
            "spend_limit_amount": 0,
            "is_spend_limit": False,
            "tax": 0,
            "benefit_type": "",
            "quota_bonus": 0,
            "cashtag": "",
            "is_family_plan": False,
            "combo_details": [],
            "is_switch_plan": False,
            "discount_recurring": 0,
            "has_bonus": False,
            "discount_promo": 0,
        },
        "total_amount": amount_int,
        "total_fee": 0,
        "is_use_point": False,
        "lang": "en",
        "items": items,
        "verification_token": token_payment,
        "payment_method": "QRIS",
        "timestamp": int(time.time()),
    }

    encrypted_payload = encryptsign_xdata(api_key, "POST", path, tokens["id_token"], settlement_payload)
    xtime = int(encrypted_payload["encrypted_body"]["xtime"])
    sig_time_sec = xtime // 1000
    x_requested_at = datetime.fromtimestamp(sig_time_sec, tz=timezone.utc).astimezone()
    settlement_payload["timestamp"] = ts_to_sign

    body = encrypted_payload["encrypted_body"]
    x_sig = get_x_signature_payment(api_key, tokens["access_token"], ts_to_sign,
                                    payment_targets, token_payment, "QRIS", payment_for, path)

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
    with live_loading("Mengirim settlement request...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        if decrypted_body.get("status") != "SUCCESS":
            print_panel("Kesalahan", "Settlement QRIS gagal.")
            print_panel("Response", json.dumps(decrypted_body, indent=2))
            return None
        transaction_id = decrypted_body["data"]["transaction_code"]
        print_panel("Berhasil", "Transaksi QRIS berhasil dibuat.")
        return transaction_id
    except Exception as e:
        print_panel("Kesalahan", f"Error decrypt: {e}")
        print_panel("Raw Response", resp.text)
        return None


def get_qris_code(api_key: str, tokens: dict, transaction_id: str) -> str | None:
    path = "payments/api/v8/pending-detail"
    payload = {"transaction_id": transaction_id, "is_enterprise": False, "lang": "en", "status": ""}

    with live_loading("Mengambil QRIS code...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil QRIS code.")
        print_panel("Response", json.dumps(res, indent=2))
        return None

    print_panel("Berhasil", "QRIS code berhasil diambil.")
    return res["data"]["qr_code"]


def show_qris_payment(api_key: str, tokens: dict, items: list[PaymentItem],
                      payment_for: str, ask_overwrite: bool,
                      overwrite_amount: int = -1,
                      token_confirmation_idx: int = 0,
                      amount_idx: int = -1,
                      topup_number: str = "",
                      stage_token: str = "") -> str | None:
    transaction_id = settlement_qris(api_key, tokens, items, payment_for,
                                     ask_overwrite, overwrite_amount,
                                     token_confirmation_idx, amount_idx,
                                     topup_number, stage_token)

    if not transaction_id:
        print_panel("Kesalahan", "Gagal membuat transaksi QRIS.")
        return None

    qris_code = get_qris_code(api_key, tokens, transaction_id)
    if not qris_code:
        print_panel("Kesalahan", "Gagal mengambil QRIS code.")
        return None

    print_panel("QRIS Data", qris_code)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=1, border=1)
    qr.add_data(qris_code)
    qr.make(fit=True)
    qr.print_ascii(invert=True)

    qris_b64 = base64.urlsafe_b64encode(qris_code.encode()).decode()
    qris_url = f"https://ki-ar-kod.netlify.app/?data={qris_b64}"

    print_panel("QRIS Link", f"Atau buka tautan berikut untuk melihat QRIS:\n{qris_url}")
    return qris_b64

