import os

from app3.config.imports import *
from app3.menus.util import clear_screen, pause, print_panel, print_error
from app3.menus.package import show_package_details
from app3.menus.util import get_rupiah

console = Console()


def fetch_special_for_you(api_key: str, id_token: str, access_token: str, balance: int = 0) -> list:
    try:
        seg_data = dash_segments(api_key, id_token, access_token, balance)
        if not seg_data:
            return []

        packages = seg_data.get("special_packages", [])
        special_packages = []

        for pkg in packages:
            try:
                name = pkg.get("name", "Unknown Package")
                kode_paket = pkg.get("kode_paket", "-")

                if not kode_paket or kode_paket == "-":
                    continue

                original_price = int(pkg.get("original_price", 0))
                diskon_price = int(pkg.get("diskon_price", original_price))

                diskon_percent = 0
                if original_price > 0 and diskon_price < original_price:
                    diskon_percent = int(round((original_price - diskon_price) / original_price * 100))

                special_packages.append({
                    "name": name,
                    "kode_paket": kode_paket,
                    "original_price": original_price,
                    "diskon_price": diskon_price,
                    "diskon_percent": diskon_percent,
                    "kuota_gb": pkg.get("kuota_gb", 0),
                })
            except Exception as e:
                print_panel("⚠️ Ups", f"Gagal parse paket bro: {e} 🤯")
                continue

        special_packages.sort(key=lambda x: x["diskon_percent"], reverse=True)
        return special_packages

    except Exception as e:
        print_panel("⚠️ Ups", f"Gagal ngambil data SFY bro: {e} 🤯")
        return []


def show_special_for_you_menu(tokens: dict):
    theme = get_theme()

    api_key = AuthInstance.api_key
    id_token = tokens.get("id_token", "")
    access_token = tokens.get("access_token", "")
    balance = 0

    special_packages = fetch_special_for_you(api_key, id_token, access_token, balance)

    while True:
        clear_screen()
        ensure_git()

        if not special_packages:
            print_panel("ℹ️ Santuy", "Sepi cuy, nggak ada paket spesial 😴")
            pause()
            return

        info_text = Align.center(
            f"[{theme['text_body']}]🔥 Paket Special For You 🤙🔥[/{theme['text_body']}]"
        )
        console.print(Panel(
            info_text,
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Diskon", justify="right", style=theme["text_money"])
        table.add_column("Normal", justify="right", style=theme["text_err"])
        table.add_column("Harga", justify="right", style=theme["text_money"])

        for idx, pkg in enumerate(special_packages, 1):
            emoji_diskon = "💸" if pkg.get("diskon_percent", 0) >= 50 else ""
            emoji_kuota = "🔥" if pkg.get("kuota_gb", 0) >= 100 else ""

            original_price = get_rupiah(pkg.get("original_price", 0))
            diskon_price = get_rupiah(pkg.get("diskon_price", 0))

            table.add_row(
                str(idx),
                f"{emoji_kuota} {pkg.get('name', '-')}",
                f"{pkg.get('diskon_percent', 0)}% {emoji_diskon}",
                f"[{theme['text_err']}][strike]{original_price}[/strike][/{theme['text_err']}]",
                f"[{theme['text_money']}]{diskon_price}[/{theme['text_money']}]"
            )

        console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu sebelumnya 🏠[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_title']}]Pilih paket (nomor) bro 👉:[/{theme['text_title']}] ").strip()

        if choice == "00":
            return "BACK"

        if not choice.isdigit():
            print_panel("⚠️ Ups", "Input lo ngaco bro, masukin angka 🚨")
            pause()
            continue

        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(special_packages):
            selected_pkg = special_packages[choice_idx]
            api_key = AuthInstance.api_key
            result = show_package_details(api_key, tokens, selected_pkg["kode_paket"], is_enterprise=False)

            if result == "MAIN":
                return "MAIN"
        else:
            print_panel("⚠️ Ups", "Nomor paket nggak valid bro 🚨")
            pause()
