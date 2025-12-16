from datetime import datetime
import json
from app3.config.imports import *
from app3.menus.package import get_packages_by_family, show_package_details
from app3.menus.util import pause, clear_screen, format_quota_byte, live_loading, get_rupiah ,print_panel
from app3.client.circle import (
    get_group_data,
    get_group_members,
    create_circle,
    validate_circle_member,
    invite_circle_member,
    remove_circle_member,
    accept_circle_invitation,
    spending_tracker,
    get_bonus_data,
)
from app3.client.encrypt import decrypt_circle_msisdn

console = Console()


def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    ensure_git()
    theme = get_theme()

    console.print(Panel(
        Align.center("🔥 Bikin Circle Baru Bro 🤙", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))

    parent_name = console.input(f"[{theme['text_sub']}]Masukin nama lo (Parent):[/{theme['text_sub']}] ").strip()
    group_name = console.input(f"[{theme['text_sub']}]Kasih nama Circle lo cuy:[/{theme['text_sub']}] ").strip()
    member_msisdn = console.input(f"[{theme['text_sub']}]Nomor member pertama (contoh 628123...):[/{theme['text_sub']}] ").strip()
    member_name = console.input(f"[{theme['text_sub']}]Nama member pertama bro:[/{theme['text_sub']}] ").strip()

    with live_loading("🔄 Lagi bikin Circle bro...", theme):
        create_res = create_circle(api_key, tokens, parent_name, group_name, member_msisdn, member_name)

    res_text = Text()
    res_text.append("Respon Server:\n", style="bold")
    res_text.append(json.dumps(create_res, indent=2), style=theme["text_body"])
    console.print(Panel(res_text, border_style=theme["border_primary"], expand=True))
    pause()


def show_bonus_list(api_key: str, tokens: dict, parent_subs_id: str, family_id: str):
    theme = get_theme()
    in_circle_bonus_menu = True

    while in_circle_bonus_menu:
        clear_screen()
        ensure_git()

        bonus_data = get_bonus_data(api_key, tokens, parent_subs_id, family_id)

        if bonus_data.get("status") != "SUCCESS":
            print_panel("⚠️ Ups", "Gagal ngambil data bonus bro 🤯")
            pause()
            return

        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        if not bonus_list:
            print_panel("ℹ️ Santuy", "Sepi cuy, nggak ada bonus 😴")
            pause()
            return

        console.print(Panel(
            Align.center("🎁 Bonus Circle 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 1),
            expand=True
        ))

        for idx, bonus in enumerate(bonus_list, start=1):
            bonus_name = bonus.get("name", "N/A")
            bonus_type = bonus.get("bonus_type", "N/A")
            action_type = bonus.get("action_type", "N/A")
            action_param = bonus.get("action_param", "N/A")
            if isinstance(action_param, (int, float)):
                action_param = get_rupiah(action_param)

            bonus_text = Text()
            bonus_text.append(f"{idx}. {bonus_name}\n", style="bold")
            bonus_text.append(f"Tipe: {bonus_type}\n", style=theme["text_body"])
            bonus_text.append(f"Aksi: {action_type}\n", style=theme["text_body"])
            bonus_text.append(f"Param: {action_param}\n", style=theme["text_sub"])

            console.print(Panel(bonus_text, border_style=theme["border_primary"], expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali[/]")
        console.print(Panel(nav_table, border_style=theme["border_info"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih bonus bro:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_circle_bonus_menu = False
        else:
            if not choice.isdigit():
                print_panel("⚠️ Ups", "Nomor bonus nggak valid bro 🚨")
                pause()
                continue

            bonus_number = int(choice)
            if bonus_number < 1 or bonus_number > len(bonus_list):
                print_panel("⚠️ Ups", "Nomor bonus nggak valid bro 🤯")
                pause()
                continue

            selected_bonus = bonus_list[bonus_number - 1]
            action_type = selected_bonus.get("action_type", "N/A")
            action_param = selected_bonus.get("action_param", "N/A")

            if action_type == "PLP":
                get_packages_by_family(action_param)
                pause()
            elif action_type == "PDP":
                show_package_details(api_key, tokens, action_param, False)
                pause()
            else:
                detail_text = Text()
                detail_text.append("⚠️ Belum ada aksi buat tipe ini bro\n", style="bold")
                detail_text.append(f"Aksi: {action_type}\nParam: {action_param}", style=theme["text_body"])
                console.print(Panel(detail_text, border_style=theme["border_info"], expand=True))
                pause()


def show_circle_info(api_key: str, tokens: dict):
    theme = get_theme()
    in_circle_menu = True
    user: dict = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "")

    while in_circle_menu:
        clear_screen()
        ensure_git()

        group_res = get_group_data(api_key, tokens)

        if group_res.get("status") != "SUCCESS":
            print_panel("⚠️ Ups", "Gagal ngambil data Circle bro 🤯")
            pause()
            return "BACK"

        group_data = group_res.get("data", {})
        group_id = group_data.get("group_id", "")

        if group_id == "":
            console.print(Panel(
                Align.center("🚫 Lo belum join Circle manapun bro 😴", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            create_new = console.input(f"[{theme['text_sub']}]Gas bikin Circle baru? (y/n):[/{theme['text_sub']}] ").strip().lower()
            if create_new == "y":
                show_circle_creation(api_key, tokens)
                continue
            else:
                pause()
                return "BACK"

        if group_data.get("group_status") == "BLOCKED":
            print_panel("⚠️ Info", "Circle ini lagi ke-block cuy 🚨")
            pause()
            return "BACK"

        group_name = group_data.get("group_name", "N/A")
        owner_name = group_data.get("owner_name", "N/A")

        members_res = get_group_members(api_key, tokens, group_id)

        if members_res.get("status") != "SUCCESS":
            print_panel("⚠️ Ups", "Gagal ngambil data member Circle bro 🤯")
            pause()
            return "BACK"

        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if not members:
            print_panel("ℹ️ Santuy", "Sepi cuy, nggak ada member 😴")
            pause()
            return "BACK"

        parent_member_id = ""
        parent_subs_id = ""
        parrent_msisdn = ""
        for member in members:
            if member.get("member_role") == "PARENT":
                parent_member_id = member.get("member_id", "")
                parent_subs_id = member.get("subscriber_number", "")
                parrent_msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))

        package = members_data.get("package", {})
        package_name = package.get("name", "N/A")
        benefit = package.get("benefit", {})
        allocation_byte = benefit.get("allocation", 0)
        remaining_byte = benefit.get("remaining", 0)

        formatted_allocation = format_quota_byte(allocation_byte)
        formatted_remaining = format_quota_byte(remaining_byte)

        spending_res = spending_tracker(api_key, tokens, parent_subs_id, group_id)

        if spending_res.get("status") != "SUCCESS":
            print_panel("⚠️ Ups", "Gagal ngambil data spending bro 🤯")
            pause()
            return "BACK"

        spending_data = spending_res.get("data", {})
        spend = spending_data.get("spend", 0)
        target = spending_data.get("target", 0)

        header_text = Text()
        header_text.append(f"🔥 Circle: {group_name}\n", style="bold")
        header_text.append(f"👑 Owner: {owner_name} {parrent_msisdn}\n", style=theme["text_body"])
        header_text.append(f"📦 Paket: {package_name} | {formatted_remaining} / {formatted_allocation}\n", style=theme["text_body"])
        header_text.append(f"💸 Spending: {get_rupiah(spend)} / {get_rupiah(target)}\n", style=theme["text_money"])

        console.print(Panel(header_text, border_style=theme["border_primary"], expand=True))

        for idx, m in enumerate(members, start=1):
            msisdn = decrypt_circle_msisdn(api_key, m.get("msisdn", "")) or "<No Number>"
            me_mark = " (Lo)" if str(msisdn) == str(my_msisdn) else ""
            role = "Parent" if m.get("member_role") == "PARENT" else "Member"
            joined_str = datetime.fromtimestamp(m.get("join_date", 0)).strftime('%Y-%m-%d') if m.get("join_date") else "N/A"
            alloc = format_quota_byte(m.get("allocation", 0))
            used = format_quota_byte(max(m.get("allocation", 0) - m.get("remaining", 0), 0))
            usage_str = f"{used} / {alloc}"

            member_text = Text()
            member_text.append(f"{idx}. {m.get('member_name','N/A')} {me_mark}\n", style="bold")
            member_text.append(f"📱 Nomor: {msisdn}\n", style=theme["border_warning"])
            member_text.append(f"🎭 Role: {role}\n", style=theme["text_body"])
            member_text.append(f"📅 Join: {joined_str}\n", style=theme["border_info"])
            member_text.append(f"🎲 Slot: {m.get('slot_type','N/A')}\n", style=theme["text_body"])
            member_text.append(f"⚡ Status: {m.get('status','N/A')}\n", style=theme["text_sub"])
            member_text.append(f"📊 Usage: {usage_str}\n", style=theme["text_body"])

            console.print(Panel(member_text, border_style=theme["border_info"], expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "Invite Member ke Circle ➕ ")
        nav_table.add_row("del <num>", f"[{theme['text_err']}]Hapus Member 🗑️ [/]")
        nav_table.add_row("acc <num>", "Terima Undangan ✅ ")
        nav_table.add_row("2", "Lihat Bonus Circle 🎁 ")
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")

        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan lo bro:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"

        elif choice == "1":
            msisdn_to_invite = console.input(f"[{theme['text_sub']}]Nomor member yang mau di-invite:[/{theme['text_sub']}] ").strip()
            validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if validate_res.get("status") == "SUCCESS":
                if validate_res.get("data", {}).get("response_code", "") != "200-2001":
                    print_panel("⚠️ Ups", f"Nggak bisa invite {msisdn_to_invite}: {validate_res.get('data', {}).get('message', 'Error bro')}")
                    pause()
                    continue
            member_name = console.input(f"[{theme['text_sub']}]Nama membernya bro:[/{theme['text_sub']}] ").strip()
            with live_loading("🔄 Lagi kirim undangan...", theme):
                invite_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)
            if invite_res.get("status") == "SUCCESS" and invite_res.get("data", {}).get("response_code") == "200-00":
                print_panel("✅ Mantap", f"Undangan udah dikirim ke {msisdn_to_invite} 🚀")
            else:
                print_panel("⚠️ Ups", f"Gagal invite {msisdn_to_invite} 🤯")
            pause()

        elif choice.startswith("del "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    print_panel("⚠️ Ups", "Nomor member nggak valid bro 🚨")
                    pause()
                    continue
                member_to_remove = members[member_number - 1]
                if member_to_remove.get("member_role") == "PARENT":
                    print_panel("⚠️ Info", "Parent nggak bisa dihapus bro 🚨")
                    pause()
                    continue
                is_last_member = len(members) == 2
                if is_last_member:
                    print_panel("⚠️ Info", "Nggak bisa hapus member terakhir bro 🤯")
                    pause()
                    continue
                msisdn_to_remove = decrypt_circle_msisdn(api_key, member_to_remove.get("msisdn", ""))
                confirm = console.input(f"[{theme['text_sub']}]Yakin mau hapus {msisdn_to_remove}? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Santuy", "Penghapusan dibatalin bro ✌️")
                    pause()
                    continue
                with live_loading("🔄 Lagi hapus member...", theme):
                    remove_res = remove_circle_member(api_key, tokens, member_to_remove.get("member_id", ""), group_id, parent_member_id, is_last_member)
                if remove_res.get("status") == "SUCCESS":
                    res_text = Text()
                    res_text.append(f"🗑️ Member {msisdn_to_remove} udah gue hapus bro ✌️\n", style="bold")
                    res_text.append(json.dumps(remove_res, indent=2), style=theme["text_body"])
                    console.print(Panel(res_text, border_style=theme["border_info"], expand=True))
                else:
                    print_panel("⚠️ Ups", f"Gagal hapus member: {remove_res}")
            except ValueError:
                print_panel("⚠️ Ups", "Format input buat hapus member ngaco bro 🚨")
            pause()

        elif choice.startswith("acc "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    print_panel("⚠️ Ups", "Nomor member nggak valid bro 🚨")
                    pause()
                    continue
                member_to_accept = members[member_number - 1]
                if member_to_accept.get("status") != "INVITED":
                    print_panel("⚠️ Info", "Member ini nggak dalam status undangan bro 🤨")
                    pause()
                    continue
                msisdn_to_accept = decrypt_circle_msisdn(api_key, member_to_accept.get("msisdn", ""))
                confirm = console.input(f"[{theme['text_sub']}]Terima undangan buat {msisdn_to_accept}? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Santuy", "Undangan nggak jadi diterima bro ✌️")
                    pause()
                    continue
                with live_loading("🔄 Lagi terima undangan...", theme):
                    accept_res = accept_circle_invitation(api_key, tokens, group_id, member_to_accept.get("member_id", ""))
                if accept_res.get("status") == "SUCCESS":
                    res_text = Text()
                    res_text.append(f"✅ Undangan buat {msisdn_to_accept} udah diterima bro 🚀\n", style="bold")
                    res_text.append(json.dumps(accept_res, indent=2), style=theme["text_body"])
                    console.print(Panel(res_text, border_style=theme["border_info"], expand=True))
                else:
                    print_panel("⚠️ Ups", f"Gagal terima undangan: {accept_res}")
            except ValueError:
                print_panel("⚠️ Ups", "Format input buat terima undangan ngaco bro 🚨")
            pause()

        elif choice == "2":
            show_bonus_list(api_key, tokens, parent_subs_id, group_id)

