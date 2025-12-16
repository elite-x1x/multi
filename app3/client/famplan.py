import json
from app3.client.engsel import send_api_request
from app3.menus.util import format_quota_byte, live_loading, print_panel
from app3.config.theme_config import get_theme

def get_family_data(
    api_key: str,
    tokens: dict,
) -> dict:
    path = "sharings/api/v8/family-plan/member-info"

    raw_payload = {
        "group_id": 0,
        "is_enterprise": False,
        "lang": "en"
    }

    with live_loading("👨‍👩‍👧 Lagi ngumpulin data family bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    return res

def validate_msisdn(
    api_key: str,
    tokens: dict,
    msisdn: str,
) -> dict:
    # path = "api/v8/auth/validate-msisdn"
    path = "api/v8/auth/check-dukcapil"

    raw_payload = {
        "with_bizon": True,
        "with_family_plan": True,
        "is_enterprise": False,
        "with_optimus": True,
        "lang": "en",
        "msisdn": msisdn,
        "with_regist_status": True,
        "with_enterprise": True
    }

    with live_loading(f"🔍 Lagi ngecek nomor {msisdn} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    return res

def change_member(
    api_key: str,
    tokens: dict,
    parent_alias: str,
    alias: str,
    slot_id: int,
    family_member_id: str,
    new_msisdn: str,
) -> dict:
    path = "sharings/api/v8/family-plan/change-member"

    raw_payload = {
        "parent_alias": parent_alias,
        "is_enterprise": False,
        "slot_id": slot_id,
        "alias": alias,
        "lang": "en",
        "msisdn": new_msisdn,
        "family_member_id": family_member_id
    }
    
    with live_loading(f"🔄 Lagi assign slot {slot_id} ke {new_msisdn} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    return res

def remove_member(
    api_key: str,
    tokens: dict,
    family_member_id: str,
) -> dict:
    path = "sharings/api/v8/family-plan/remove-member"

    raw_payload = {
        "is_enterprise": False,
        "family_member_id": family_member_id,
        "lang": "en"
    }

    with live_loading(f"🗑️ Lagi nendang member {family_member_id} keluar bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    return res

def set_quota_limit(
    api_key: str,
    tokens: dict,
    original_allocation: int,
    new_allocation: int,
    family_member_id: str,
) -> dict:
    path = "sharings/api/v8/family-plan/allocate-quota"

    raw_payload = {
        "is_enterprise": False,
        "member_allocations": [{
            "new_text_allocation": 0,
            "original_text_allocation": 0,
            "original_voice_allocation": 0,
            "original_allocation": original_allocation,
            "new_voice_allocation": 0,
            "message": "",
            "new_allocation": new_allocation,
            "family_member_id": family_member_id,
            "status": ""
        }],
        "lang": "en"
    }
    
    formatted_new_allocation = format_quota_byte(new_allocation)

    with live_loading(f"📊 Lagi ngatur limit kuota buat {family_member_id} ke {formatted_new_allocation} bro...", get_theme()):
        res = send_api_request(api_key, path, raw_payload, tokens["id_token"], "POST")

    return res
