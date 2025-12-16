import json
from app2.client.engsel import send_api_request
from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme


def get_segments(api_key: str, tokens: dict, is_enterprise: bool = False) -> dict | None:
    path = "api/v8/configs/store/segments"
    payload = {"is_enterprise": is_enterprise, "lang": "en"}

    with live_loading("Mengambil data store segments...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil data store segments.")
        return None

    print_panel("Berhasil", "Data store segments berhasil diambil.")
    return res
