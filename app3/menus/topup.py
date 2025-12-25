# app3/menus/topup.py

import sys
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

from app3.config.imports import *
from app3.config.theme_config import get_theme
from app3.menus.util import clear_screen, pause, print_panel, simple_number, live_loading
from app3.client.engsel import get_family, get_topups

console = Console()


def show_topup_menu():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_topup_menu = True
    while in_topup_menu:
        clear_screen()
        ensure_git()

        console.print(Panel(
            Align.center("💳 Menu Topup 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        # ambil semua family code dari akun aktif
        family_codes = []
        profile = AuthInstance.get_active_user()
        if not profile:
            print_panel("⚠️ Ups", "User belum aktif bro 🚨")
            pause()
            return

        # misalnya ambil dari subscription_type
        subscription_type = profile.get("subscription_type", "")
        if subscription_type:
            family_codes.append(subscription_type)

        all_topups = []
        with live_loading("Memuat data topup... 🤙", theme):
            for fam_code in family_codes:
                family_data = get_family(api_key, tokens, fam_code)
                if not family_data:
                    continue
                for variant in family_data.get("package_variants", []):
                    for option in variant.get("package_options", []):
                        code = option.get("package_option_code")
                        if not code:
                            continue
                        data = get_topups(api_key, tokens, code, use_loading=False)
                        if data and "list" in data:
                            all_topups.extend(data["list"])

        if not all_topups:
            print_panel("⚠️ Ups", "Nggak ada data topup bro 🚨")
            pause()
            return

        # tampilkan tabel topup
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], width=4, justify="right")
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", justify="right", style=theme["text_money"], width=16)
        table.add_column("Masa Aktif", style=theme["text_body"])
        table.add_column("Kode", style=theme["text_sub"], justify="right")

        for idx, item in enumerate(all_topups, start=1):
            table.add_row(
                str(idx),
                item.get("name", ""),
                str(item.get("price", 0)),
                item.get("validity", ""),
                item.get("package_option_code", "")
            )

        console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        # navigasi balik
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket bro 👉:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_topup_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(all_topups):
            selected = all_topups[int(choice) - 1]
            print_panel("ℹ️ Info Paket",
                        f"Nama: {selected.get('name')}\n"
                        f"Harga: {selected.get('price')}\n"
                        f"Masa Aktif: {selected.get('validity')}\n"
                        f"Kode: {selected.get('package_option_code')}")
            pause()
        else:
            print_panel("⚠️ Ups", "Input lo ngaco bro 🚨")
            pause()
            continue
