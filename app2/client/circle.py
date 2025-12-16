import json
from app2.client.engsel import send_api_request
from app2.client.encrypt import encrypt_circle_msisdn
from app2.menus.util import live_loading, print_panel
from app2.config.theme_config import get_theme


def get_group_data(api_key: str, tokens: dict) -> dict | None:
    path = "family-hub/api/v8/groups/status"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    with live_loading("Mengambil detail Circle...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if not res or res.get("status") != "SUCCESS":
        print_panel("Kesalahan", "Gagal mengambil detail Circle.")
        return None
    return res


def get_group_members(api_key: str, tokens: dict, group_id: str) -> dict | None:
    path = "family-hub/api/v8/members/info"
    raw_payload = {"group_id": group_id, "is_enterprise": False, "lang": "en"}
    with live_loading(f"Mengambil member untuk group {group_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def validate_circle_member(api_key: str, tokens: dict, msisdn: str) -> dict | None:
    path = "family-hub/api/v8/members/validate"
    encrypted_msisdn = encrypt_circle_msisdn(api_key, msisdn)
    raw_payload = {"msisdn": encrypted_msisdn, "is_enterprise": False, "lang": "en"}
    with live_loading(f"Memvalidasi member {msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def invite_circle_member(api_key: str, tokens: dict, msisdn: str, name: str,
                         group_id: str, member_id_parent: str) -> dict | None:
    path = "family-hub/api/v8/members/invite"
    encrypted_msisdn = encrypt_circle_msisdn(api_key, msisdn)
    raw_payload = {
        "access_token": tokens["access_token"],
        "group_id": group_id,
        "is_enterprise": False,
        "members": [{"msisdn": encrypted_msisdn, "name": name}],
        "lang": "en",
        "member_id_parent": member_id_parent,
    }
    with live_loading(f"Mengundang {msisdn} ke Circle...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("Kesalahan", "Gagal mengundang member ke Circle.")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    print_panel("Status Undangan", f"Status: {status}\nPesan: {message}")

    return {"status": status, "message": message, "data": res}


def remove_circle_member(api_key: str, tokens: dict, member_id: str,
                         group_id: str, member_id_parent: str,
                         is_last_member: bool = False) -> dict | None:
    path = "family-hub/api/v8/members/remove"
    raw_payload = {
        "member_id": member_id,
        "group_id": group_id,
        "is_enterprise": False,
        "is_last_member": is_last_member,
        "lang": "en",
        "member_id_parent": member_id_parent,
    }
    with live_loading(f"Menghapus member {member_id} dari Circle...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("Kesalahan", "Gagal menghapus member dari Circle.")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    print_panel("Status Penghapusan", f"Status: {status}\nPesan: {message}")

    return {"status": status, "message": message, "data": res}


def accept_circle_invitation(api_key: str, tokens: dict, group_id: str, member_id: str) -> dict | None:
    path = "family-hub/api/v8/groups/accept-invitation"
    raw_payload = {
        "access_token": tokens["access_token"],
        "group_id": group_id,
        "member_id": member_id,
        "is_enterprise": False,
        "lang": "en",
    }
    with live_loading(f"Menerima undangan Circle {group_id}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("Kesalahan", "Gagal menerima undangan Circle.")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    print_panel("Status Penerimaan Undangan", f"Status: {status}\nPesan: {message}")

    return {"status": status, "message": message, "data": res}


def create_circle(api_key: str, tokens: dict, parent_name: str,
                  group_name: str, member_msisdn: str, member_name: str) -> dict | None:
    path = "family-hub/api/v8/groups/create"
    raw_payload = {
        "access_token": tokens["access_token"],
        "parent_name": parent_name,
        "group_name": group_name,
        "is_enterprise": False,
        "members": [{"msisdn": encrypt_circle_msisdn(api_key, member_msisdn), "name": member_name}],
        "lang": "en",
    }
    with live_loading(f"Membuat Circle baru dengan member {member_msisdn}...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("Kesalahan", "Gagal membuat Circle.")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    print_panel("Status Pembuatan Circle", f"Status: {status}\nPesan: {message}")

    return {"status": status, "message": message, "data": res}


def spending_tracker(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict | None:
    path = "gamification/api/v8/family-hub/spending-tracker"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("Mengambil data spending tracker...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def get_bonus_data(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict | None:
    path = "gamification/api/v8/family-hub/bonus/list"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("Mengambil data bonus...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res
