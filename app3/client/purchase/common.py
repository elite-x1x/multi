import json
import os
from app3.client.engsel import send_api_request
from app3.menus.util import live_loading, print_panel
from app3.config.theme_config import get_theme

BASE_API_URL = os.getenv("BASE_API_URL")
AX_FP = os.getenv("AX_FP")
UA = os.getenv("UA")


def get_payment_methods(api_key: str, tokens: dict,
                        token_confirmation: str,
                        payment_target: str) -> dict | None:
    payment_path = "payments/api/v8/payment-methods-option"
    payment_payload = {
        "payment_type": "PURCHASE",
        "is_enterprise": False,
        "payment_target": payment_target,
        "lang": "en",
        "is_referral": False,
        "token_confirmation": token_confirmation,
    }

    with live_loading("💳 Lagi ngumpulin payment methods bro...", get_theme()):
        payment_res = send_api_request(api_key, payment_path, payment_payload, tokens["id_token"], "POST")

    if not payment_res or payment_res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", "Gagal ambil payment methods bro 🚨")
        return None

    print_panel("✅ Mantap", "Payment methods berhasil diambil 🚀")
    return payment_res.get("data")
