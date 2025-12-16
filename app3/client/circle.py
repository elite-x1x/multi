import json
from app3.client.engsel import send_api_request
from app3.client.encrypt import encrypt_circle_msisdn
from app3.menus.util import live_loading, print_panel
from app3.config.theme_config import get_theme


def get_group_data(api_key: str, tokens: dict) -> dict | None:
    path = "family-hub/api/v8/groups/status"
    raw_payload = {"is_enterprise": False, "lang": "en"}
    with live_loading("👥 Lagi ngumpulin detail Circle bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    if not res or res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", "Gagal ambil detail Circle 🚨")
        return None
    #print_panel("✅ Mantap", "Detail Circle berhasil diambil 🚀")
    return res


def get_group_members(api_key: str, tokens: dict, group_id: str) -> dict | None:
    path = "family-hub/api/v8/members/info"
    raw_payload = {"group_id": group_id, "is_enterprise": False, "lang": "en"}
    with live_loading(f"👥 Lagi ngumpulin member buat group {group_id} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def validate_circle_member(api_key: str, tokens: dict, msisdn: str) -> dict | None:
    path = "family-hub/api/v8/members/validate"
    encrypted_msisdn = encrypt_circle_msisdn(api_key, msisdn)
    raw_payload = {"msisdn": encrypted_msisdn, "is_enterprise": False, "lang": "en"}
    with live_loading(f"🔍 Lagi ngecek member {msisdn} bro...", get_theme()):
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
    with live_loading(f"📩 Lagi ngundang {msisdn} ke Circle bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("⚠️ Ups", "Gagal ngundang member ke Circle 🚨")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    colored_status = f"✅ {status}" if status == "SUCCESS" else f"⚠️ {status}"
    print_panel("📩 Invite Status", f"Status: {colored_status}\nPesan: {message}")

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
    with live_loading(f"🗑️ Lagi nendang member {member_id} keluar bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("⚠️ Ups", "Gagal hapus member dari Circle 🚨")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    colored_status = f"✅ {status}" if status == "SUCCESS" else f"⚠️ {status}"
    print_panel("🗑️ Remove Status", f"Status: {colored_status}\nPesan: {message}")

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
    with live_loading(f"✅ Lagi nerima undangan Circle {group_id} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("⚠️ Ups", "Gagal nerima undangan Circle 🚨")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    colored_status = f"✅ {status}" if status == "SUCCESS" else f"⚠️ {status}"
    print_panel("✅ Accept Invitation Status", f"Status: {colored_status}\nPesan: {message}")

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
    with live_loading(f"➕ Lagi bikin Circle baru dengan member {member_msisdn} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    if not res:
        print_panel("⚠️ Ups", "Gagal bikin Circle 🚨")
        return None

    status = res.get("status", "UNKNOWN")
    message = res.get("message", "")
    colored_status = f"✅ {status}" if status == "SUCCESS" else f"⚠️ {status}"
    print_panel("➕ Create Circle Status", f"Status: {colored_status}\nPesan: {message}")

    return {"status": status, "message": message, "data": res}


def spending_tracker(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict | None:
    path = "gamification/api/v8/family-hub/spending-tracker"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("💸 Lagi ngumpulin data spending tracker bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res


def get_bonus_data(api_key: str, tokens: dict, parent_subs_id: str, family_id: str) -> dict | None:
    path = "gamification/api/v8/family-hub/bonus/list"
    raw_payload = {"is_enterprise": False, "parent_subs_id": parent_subs_id, "family_id": family_id, "lang": "en"}
    with live_loading("🎁 Lagi ngumpulin data bonus bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")
    return res
