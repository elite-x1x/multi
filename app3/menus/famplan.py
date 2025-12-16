from datetime import datetime
import json
from app3.config.imports import *
from app3.menus.util import pause, clear_screen, format_quota_byte, print_panel, simple_number, nav_range
from app3.client.famplan import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn

console = Console()


def show_family_info(api_key: str, tokens: dict):
    theme = get_theme()
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        res = get_family_data(api_key, tokens)
        if not res.get("data"):
            print_panel("⚠️ Ups", "Gagal ngambil data family bro 🤯")
            pause()
            return
        
        family_detail = res["data"]
        plan_type = family_detail["member_info"]["plan_type"]
        if plan_type == "":
            print_panel("ℹ️ Santuy", "Lo bukan organizer family plan bro 😴")
            pause()
            return
        
        parent_msisdn = family_detail["member_info"]["parent_msisdn"]
        members = family_detail["member_info"]["members"]
        empty_slots = [slot for slot in members if slot.get("msisdn") == ""]
        
        total_quota_human = format_quota_byte(family_detail["member_info"].get("total_quota", 0))
        remaining_quota_human = format_quota_byte(family_detail["member_info"].get("remaining_quota", 0))
        end_date_ts = family_detail["member_info"].get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d")

        console.print(Panel(
            Align.center(
                f"👨‍👩‍👧‍👦 Family Plan: {plan_type}\n"
                f"📱 Parent: {parent_msisdn}\n"
                f"📶 Quota: {remaining_quota_human}/{total_quota_human} | Exp: {end_date}",
                vertical="middle"
            ),
            border_style=theme["border_info"],
            padding=(1,2),
            expand=True
        ))
        simple_number()
        ensure_git()

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("MSISDN", style=theme["text_body"])
        table.add_column("Alias", style=theme["text_body"])
        table.add_column("Type", style=theme["text_body"])
        table.add_column("Quota", style=theme["text_money"], justify="right")
        table.add_column("Add Chances", style=theme["text_body"], justify="center")
        
        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "")
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")
            quota_used = format_quota_byte(member.get("usage", {}).get("quota_used", 0))
            quota_alloc = format_quota_byte(member.get("usage", {}).get("quota_allocated", 0))
            add_chances = f"{member.get('add_chances',0)}/{member.get('total_add_chances',0)}"
            table.add_row(str(idx), msisdn or "<Slot Kosong>", alias, member_type, f"{quota_used}/{quota_alloc}", add_chances)
        
        console.print(Panel(table, title=f"[{theme['text_title']}]👥 Member Family[/]", border_style=theme["border_info"], expand=True))

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("1", "Ganti Member 🔄 ")
        nav.add_row("limit <No> <MB>", "Set Limit Kuota 📊 ")
        nav.add_row("del <No>", "Hapus Member 🗑️ ")
        nav.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan lo bro:[/{theme['text_sub']}] ").strip()

        if choice == "1":
            slot_idx = console.input("Nomor slot: ").strip()
            target_msisdn = console.input("Nomor baru (62...): ").strip()
            parent_alias = console.input("Alias parent: ").strip()
            child_alias = console.input("Alias member baru: ").strip()
            try:
                slot_idx_int = int(slot_idx)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_panel("⚠️ Ups", "Nomor slot nggak valid bro 🚨")
                    pause()
                    continue
                if members[slot_idx_int - 1].get("msisdn") != "":
                    print_panel("⚠️ Ups", "Slot udah terisi bro 🤯")
                    pause()
                    continue
                validation_res = validate_msisdn(api_key, tokens, target_msisdn)
                if validation_res.get("status","").lower() != "success":
                    print_panel("⚠️ Ups", f"Validasi gagal bro: {json.dumps(validation_res, indent=2)}")
                    pause()
                    continue
                if validation_res["data"].get("family_plan_role","") != "NO_ROLE":
                    print_panel("⚠️ Ups", f"{target_msisdn} udah join family lain bro 🚨")
                    pause()
                    continue
                is_continue = console.input(f"Assign {target_msisdn} ke slot {slot_idx_int}? (y/n): ").strip().lower()
                if is_continue != "y":
                    print_panel("ℹ️ Santuy", "Dibatalkan bro ✌️")
                    pause()
                    continue
                res_change = change_member(api_key, tokens, parent_alias, child_alias,
                                           members[slot_idx_int-1]["slot_id"],
                                           members[slot_idx_int-1]["family_member_id"],
                                           target_msisdn)
                if res_change.get("status") == "SUCCESS":
                    print_panel("✅ Mantap", "Member berhasil diganti bro 🚀")
                else:
                    print_panel("⚠️ Ups", res_change.get("message","Error bro 🤯"))
                console.print(json.dumps(res_change, indent=4))
            except ValueError:
                print_panel("⚠️ Ups", "Input slot ngaco bro 🚨")
            pause()

        elif choice.startswith("del "):
            _, slot_num = choice.split(" ",1)
            try:
                slot_idx_int = int(slot_num)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_panel("⚠️ Ups", "Nomor slot nggak valid bro 🚨")
                    pause()
                    continue
                member = members[slot_idx_int-1]
                if member.get("msisdn") == "":
                    print_panel("ℹ️ Santuy", "Slot kosong bro 😴")
                    pause()
                    continue
                is_continue = console.input(f"Hapus {member.get('msisdn')} dari slot {slot_idx_int}? (y/n): ").strip().lower()
                if is_continue != "y":
                    print_panel("ℹ️ Santuy", "Penghapusan dibatalin bro ✌️")
                    pause()
                    continue
                res_del = remove_member(api_key, tokens, member["family_member_id"])
                if res_del.get("status") == "SUCCESS":
                    print_panel("✅ Mantap", "Member berhasil dihapus bro 🚀")
                else:
                    print_panel("⚠️ Ups", res_del.get("message","Error bro 🤯"))
                console.print(json.dumps(res_del, indent=4))
            except ValueError:
                print_panel("⚠️ Ups", "Input slot ngaco bro 🚨")
            pause()

        elif choice.startswith("limit "):
            try:
                _, slot_num, new_quota_mb = choice.split(" ",2)
                slot_idx_int = int(slot_num)
                new_quota_mb_int = int(new_quota_mb)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    print_panel("⚠️ Ups", "Nomor slot nggak valid bro 🚨")
                    pause()
                    continue
                member = members[slot_idx_int-1]
                if member.get("msisdn") == "":
                    print_panel("⚠️ Ups", "Slot kosong bro 😴")
                    pause()
                    continue
                new_allocation_byte = new_quota_mb_int * 1024 * 1024
                res_limit = set_quota_limit(api_key, tokens,
                                            member.get("usage",{}).get("quota_allocated",0),
                                            new_allocation_byte,
                                            member["family_member_id"])
                if res_limit.get("status") == "SUCCESS":
                    print_panel("✅ Mantap", "Limit kuota berhasil diatur bro 🚀")
                else:
                    print_panel("⚠️ Ups", res_limit.get("message","Error bro 🤯"))
                console.print(json.dumps(res_limit, indent=4))
            except ValueError:
                print_panel("⚠️ Ups", "Input quota ngaco bro 🚨")
            pause()
        
        elif choice == "00":
            in_family_menu = False
            return

        else:
            print_panel("ℹ️ Santuy", "Perintah lo nggak dikenali bro 🤨")
            pause()
