# app/menus/famplan.py

from datetime import datetime
import json
from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.famplan import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn

WIDTH = 55


def print_header(title: str):
    print("=" * WIDTH)
    print(title.center(WIDTH))
    print("=" * WIDTH)


def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        res = get_family_data(api_key, tokens)
        if not res.get("data"):
            print("⚠️ Gagal ambil data Family Plan bro.")
            pause()
            return

        family_detail = res["data"]
        plan_type = family_detail["member_info"]["plan_type"]

        if plan_type == "":
            print("⚠️ Kamu bukan organizer Family Plan bro.")
            pause()
            return

        parent_msisdn = family_detail["member_info"]["parent_msisdn"]
        members = family_detail["member_info"]["members"]
        empty_slots = [slot for slot in members if slot.get("msisdn") == ""]

        total_quota_byte = family_detail["member_info"].get("total_quota", 0)
        remaining_quota_byte = family_detail["member_info"].get("remaining_quota", 0)

        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)

        end_date_ts = family_detail["member_info"].get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d")

        clear_screen()
        print_header("👨‍👩‍👧‍👦 Family Plan Info")
        print(f"Plan: {plan_type} | Parent: {parent_msisdn}".center(WIDTH))
        print(f"Shared Quota: {remaining_quota_human} / {total_quota_human} | Exp: {end_date}".center(WIDTH))
        print("-" * WIDTH)

        print(f"Members: {len(members) - len(empty_slots)}/{len(members)}")
        for idx, member in enumerate(members, start=1):
            print("-" * WIDTH)
            msisdn = member.get("msisdn", "")
            formatted_msisdn = msisdn if msisdn else "<Empty Slot>"
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")

            quota_allocated_byte = member.get("usage", {}).get("quota_allocated", 0)
            quota_used_byte = member.get("usage", {}).get("quota_used", 0)
            formated_quota_allocated = format_quota_byte(quota_allocated_byte)
            formated_quota_used = format_quota_byte(quota_used_byte)

            add_chances = member.get("add_chances", 0)
            total_add_chances = member.get("total_add_chances", 0)

            end_date_ts = member.get("usage", {}).get("quota_expired_at", 0)
            end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d") if end_date_ts else "N/A"

            print(f"{idx}. {formatted_msisdn} ({alias}) | {member_type} | Add Chances: {add_chances}/{total_add_chances}")
            print(f"   Usage: {formated_quota_used} / {formated_quota_allocated} | Exp: {end_date}")

        print("-" * WIDTH)
        print("Options:")
        print("1. Change Member 👤")
        print("limit <Slot Number> <Quota MB> ➡️ Set Quota limit untuk member")
        print("del <Slot Number> ➡️ Hapus member dari slot")
        print("00. Balik ke menu utama")
        print("-" * WIDTH)

        choice = input("Pilih opsi: ").strip()

        if choice == "1":
            slot_idx = input("Masukin nomor slot: ").strip()
            target_msisdn = input("Masukin nomor HP member baru (62xxxx): ").strip()
            parent_alias = input("Masukin alias kamu: ").strip()
            child_alias = input("Masukin alias member baru: ").strip()

            try:
                slot_idx_int = int(slot_idx)
                if not (1 <= slot_idx_int <= len(members)):
                    print("⚠️ Nomor slot nggak valid bro.")
                    pause()
                    continue

                if members[slot_idx_int - 1].get("msisdn"):
                    print("🚫 Slot ini udah kepake bro.")
                    pause()
                    continue

                family_member_id = members[slot_idx_int - 1]["family_member_id"]
                slot_id = members[slot_idx_int - 1]["slot_id"]

                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                if validation_res.get("status", "").lower() != "success":
                    print(f"⚠️ Validasi MSISDN gagal: {json.dumps(validation_res, indent=2)}")
                    pause()
                    continue
                print("✅ MSISDN valid bro.")

                if validation_res["data"].get("family_plan_role", "") != "NO_ROLE":
                    print(f"🚫 {target_msisdn} udah join Family Plan lain bro.")
                    pause()
                    continue

                confirm = input(f"Yakin mau assign {target_msisdn} ke slot {slot_idx_int}? (y/n): ").strip().lower()
                if confirm != "y":
                    print("↩️ Operasi dibatalin bro.")
                    pause()
                    continue

                change_member_res = change_member(api_key, tokens, parent_alias, child_alias, slot_id, family_member_id, target_msisdn)
                if change_member_res.get("status") == "SUCCESS":
                    print("✅ Member berhasil diganti bro.")
                else:
                    print(f"💥 Gagal ganti member: {change_member_res.get('message', 'Unknown error')}")
                print(json.dumps(change_member_res, indent=4))
            except ValueError:
                print("⚠️ Input slot nggak valid bro.")
            pause()

        elif choice.startswith("del "):
            try:
                _, slot_num = choice.split(" ", 1)
                slot_idx_int = int(slot_num)
                if not (1 <= slot_idx_int <= len(members)):
                    print("⚠️ Nomor slot nggak valid bro.")
                    pause()
                    continue

                member = members[slot_idx_int - 1]
                if not member.get("msisdn"):
                    print("⚠️ Slot ini udah kosong bro.")
                    pause()
                    continue

                confirm = input(f"Yakin mau hapus member {member.get('msisdn')} dari slot {slot_idx_int}? (y/n): ").strip().lower()
                if confirm != "y":
                    print("↩️ Penghapusan dibatalin bro.")
                    pause()
                    continue

                res = remove_member(api_key, tokens, member["family_member_id"])
                if res.get("status") == "SUCCESS":
                    print("🗑️ Member berhasil dihapus bro.")
                else:
                    print(f"💥 Gagal hapus member: {res.get('message', 'Unknown error')}")
                print(json.dumps(res, indent=4))
            except ValueError:
                print("⚠️ Input slot nggak valid bro.")
            pause()

        elif choice.startswith("limit "):
            try:
                _, slot_num, new_quota_mb = choice.split(" ", 2)
                slot_idx_int = int(slot_num)
                new_quota_mb_int = int(new_quota_mb)

                if not (1 <= slot_idx_int <= len(members)):
                    print("⚠️ Nomor slot nggak valid bro.")
                    pause()
                    continue

                member = members[slot_idx_int - 1]
                if not member.get("msisdn"):
                    print("🚫 Slot kosong bro, nggak bisa set quota.")
                    pause()
                    continue

                family_member_id = member["family_member_id"]
                original_alloc = member.get("usage", {}).get("quota_allocated", 0)
                new_alloc = new_quota_mb_int * 1024 * 1024

                res = set_quota_limit(api_key, tokens, original_alloc, new_alloc, family_member_id)
                if res.get("status") == "SUCCESS":
                    print("✅ Quota limit berhasil di-set bro.")
                else:
                    print(f"💥 Gagal set quota: {res.get('message', 'Unknown error')}")
                print(json.dumps(res, indent=4))
            except ValueError:
                print("⚠️ Input slot/quota nggak valid bro.")
            pause()

        elif choice == "00":
            in_family_menu = False
            return
