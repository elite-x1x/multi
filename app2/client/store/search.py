import json
from app2.client.engsel import send_api_request
from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme


def get_family_list(api_key: str, tokens: dict,
                    subs_type: str = "PREPAID",
                    is_enterprise: bool = False) -> dict | None:
    path = "api/v8/xl-stores/options/search/family-list"
    payload = {"is_enterprise": is_enterprise, "subs_type": subs_type, "lang": "en"}

    with live_loading("Mengambil data family list...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil data family list.")
        return None

    print_panel("Berhasil", "Data family list berhasil diambil.")
    return res


def get_store_packages(api_key: str, tokens: dict,
                       subs_type: str = "PREPAID",
                       is_enterprise: bool = False) -> dict | None:
    path = "api/v9/xl-stores/options/search"
    payload = {
        "is_enterprise": is_enterprise,
        "filters": [
            {"unit": "THOUSAND", "id": "FIL_SEL_P", "type": "PRICE", "items": []},
            {"unit": "GB", "id": "FIL_SEL_MQ", "type": "DATA_TYPE", "items": []},
            {"unit": "PACKAGE_NAME", "id": "FIL_PKG_N", "type": "PACKAGE_NAME",
             "items": [{"id": "", "label": ""}]},
            {"unit": "DAY", "id": "FIL_SEL_V", "type": "VALIDITY", "items": []},
        ],
        "substype": subs_type,
        "text_search": "",
        "lang": "en",
    }

    with live_loading("Mengambil data store packages...", get_theme()):
        res = send_api_request(api_key, path, payload, tokens["id_token"], "POST")

    if not res or res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil data store packages.")
        return None

    print_panel("Berhasil", "Data store packages berhasil diambil.")
    return res
