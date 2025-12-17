import json
import uuid
import time
import requests
from datetime import datetime, timezone

from app2.client.engsel import BASE_API_URL, UA, intercept_page, send_api_request
from app2.client.encrypt import API_KEY, decrypt_xdata, encryptsign_xdata, java_like_timestamp, get_x_signature_payment
from app.type_dict import PaymentItem
from app2.menus.util import live_loading, print_error, print_success, print_warning, print_panel
from app2.config.theme_config import get_theme


def settlement_multipayment(
    api_key: str,
    tokens: dict,
    items: list[PaymentItem],
    wallet_number: str,
    payment_method: str,
    payment_for: str,
    ask_overwrite: bool,
    overwrite_amount: int = -1,
    token_confirmation_idx: int = 0,
    amount_idx: int = -1,
):
    if overwrite_amount == -1 and not ask_overwrite:
        print_error("Kesalahan", "Harus ada overwrite_amount atau flag ask_overwrite.")
        return None

    token_confirmation = items[token_confirmation_idx]["token_confirmation"]
    payment_targets = ";".join([item["item_code"] for item in items])

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
    path = "payments/api/v8/settlement-multipayment/ewallet"
    settlement_payload = {
        "akrab": {"akrab_members": [], "akrab_parent_alias": "", "members": []},
        "can_trigger_rating": False,
        "total_discount": 0,
        "coupon": "",
        "payment_for": payment_for,
        "topup_number": "",
        "is_enterprise": False,
        "autobuy": {
            "is_using_autobuy": False,
            "activated_autobuy_code": "",
            "autobuy_threshold_setting": {"label": "", "type": "", "value": 0},
        },
        "cc_payment_type": "",
        "access_token": tokens["access_token"],
        "is_myxl_wallet": False,
        "wallet_number": wallet_number,
        "additional_data": {},
        "total_amount": amount_int,
        "total_fee": 0,
        "is_use_point": False,
        "lang": "en",
        "items": items,
        "verification_token": token_payment,
        "payment_method": payment_method,
        "timestamp": int(time.time()),
    }

    encrypted_payload = encryptsign_xdata(api_key, "POST", path, tokens["id_token"], settlement_payload)
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
        payment_method,
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
    with live_loading("Mengirim settlement request...", get_theme()):
        resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)

    try:
        decrypted_body = decrypt_xdata(api_key, json.loads(resp.text))
        if decrypted_body.get("status") != "SUCCESS":
            print_panel("Kesalahan", "Settlement gagal.")
            print_panel("Response", json.dumps(decrypted_body, indent=2))
        else:
            print_panel("Berhasil", "Multipayment berhasil.")
            print_panel("Settlement Result", json.dumps(decrypted_body, indent=2))
        return decrypted_body
    except Exception as e:
        print_panel("Kesalahan", f"Error decrypt: {e}")
        print_panel("Raw Response", resp.text)
        return resp.text


def show_multipayment(api_key: str, tokens: dict, items: list[PaymentItem],
                      payment_for: str, ask_overwrite: bool,
                      overwrite_amount: int = -1,
                      token_confirmation_idx: int = 0,
                      amount_idx: int = -1):
    choosing_payment_method = True
    while choosing_payment_method:
        payment_method = ""
        wallet_number = ""
        print_panel("Pilihan Multipayment", "1. DANA\n2. ShopeePay\n3. GoPay\n4. OVO")
        choice = input("Pilih metode pembayaran: ")
        if choice == "1":
            payment_method = "DANA"
            wallet_number = input("Masukkan nomor DANA (contoh: 08123456789): ")
            if not wallet_number.startswith("08") or not wallet_number.isdigit() or len(wallet_number) < 10 or len(wallet_number) > 13:
                print_panel("Kesalahan", "Nomor DANA tidak valid.")
                continue
            choosing_payment_method = False
        elif choice == "2":
            payment_method = "SHOPEEPAY"
            choosing_payment_method = False
        elif choice == "3":
            payment_method = "GOPAY"
            choosing_payment_method = False
        elif choice == "4":
            payment_method = "OVO"
            wallet_number = input("Masukkan nomor OVO (contoh: 08123456789): ")
            if not wallet_number.startswith("08") or not wallet_number.isdigit() or len(wallet_number) < 10 or len(wallet_number) > 13:
                print_panel("Kesalahan", "Nomor OVO tidak valid.")
                continue
            choosing_payment_method = False
        else:
            print_panel("Kesalahan", "Pilihan tidak valid.")
            continue

    settlement_response = settlement_multipayment(
        api_key,
        tokens,
        items,
        wallet_number,
        payment_method,
        payment_for,
        ask_overwrite,
        overwrite_amount,
        token_confirmation_idx,
        amount_idx,
    )

    if not settlement_response or settlement_response.get("status") != "SUCCESS":
        return

    if payment_method != "OVO":
        deeplink = settlement_response["data"].get("deeplink", "")
        if deeplink:
            print_panel("Payment Link", f"Selesaikan pembayaran melalui link berikut:\n{deeplink}")
    else:
        print_panel("Berhasil", "Buka aplikasi OVO untuk menyelesaikan pembayaran.")
    return
