import json
from app3.client.engsel import send_api_request
from app3.menus.util import live_loading, print_panel
from app3.config.theme_config import get_theme


def get_segments(api_key: str, tokens: dict, is_enterprise: bool = False) -> dict | None:
    path = "api/v8/configs/store/segments"
    payload = {"is_enterprise": is_enterprise, "lang": "en"}

    with live_loading("📊 Lagi ngumpulin store segments bro...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", "Gagal ambil store segments bro 🚨")
        return None

    print_panel("✅ Mantap", "Store segments berhasil diambil 🚀")
    return res
