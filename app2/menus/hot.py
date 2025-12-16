import json
from datetime import datetime
from app2.config.imports import *
from app.type_dict import PaymentItem
from app2.client.engsel import get_package_details, get_family
from app2.menus.package import show_package_details
from app2.menus.util import (
    clear_screen, pause, print_panel, format_quota_byte,
    display_html, simple_number, get_rupiah, live_loading
)
from app2.client.purchase.ewallet import show_multipayment
from app2.client.purchase.qris import show_qris_payment
from app2.client.purchase.balance import settlement_balance
from app.util import merge_hot1, merge_hot2

console = Console()


def show_hot_menu():
    """Menampilkan menu Hot Promo (versi 1)."""
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        ensure_git()
        
        console.print(Panel(
            Align.center("Paket Hot Promo", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        with live_loading("Memuat data...", theme):
            hot_packages = merge_hot1("https://me.mashu.lol/pg-hot.json")

        if not hot_packages:
            try:
                with open("hot_data/hot.json", "r", encoding="utf-8") as f:
                    hot_packages = json.load(f)
            except Exception as e:
                print_panel("Kesalahan", f"Gagal memuat hot.json: {e}")
                pause()
                return

        if not hot_packages:
            print_panel("Informasi", "Tidak ada data HOT tersedia.")
            pause()
            return

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], width=4, justify="right")
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Variant", style=theme["text_body"])
        table.add_column("Option", style=theme["text_body"])
        table.add_column("Source", style=theme["text_sub"], justify="right")

        for idx, p in enumerate(hot_packages, start=1):
            table.add_row(
                str(idx),
                p["family_name"],
                p["variant_name"],
                p["option_name"],
                p.get("source", "local")
            )

        console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_hot_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm.get("is_enterprise", False)
            
            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_panel("Kesalahan", f"Gagal mengambil data family {family_code}.")
                pause()
                continue
            
            option_code = next(
                (opt["package_option_code"] for v in family_data["package_variants"]
                 if v["name"] == selected_bm["variant_name"]
                 for opt in v["package_options"]
                 if opt["order"] == selected_bm["order"]),
                None
            )
            
            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                print_panel("Kesalahan", "Option code tidak ditemukan.")
                pause()
        else:
            print_panel("Kesalahan", "Input tidak valid, silakan coba lagi.")
            pause()
            continue


def show_hot_menu2():
    """Menampilkan menu Hot Promo (versi 2) dengan detail dan opsi pembayaran."""
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_hot_menu2 = True
    while in_hot_menu2:
        clear_screen()
        ensure_git()
        main_package_detail = {}

        console.print(Panel(
            Align.center("Paket Hot Promo 2", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        with live_loading("Memuat data...", theme):
            hot_packages = merge_hot2("https://me.mashu.lol/pg-hot2.json")

        if not hot_packages:
            print_panel("Informasi", "Tidak ada data HOT2 tersedia.")
            pause()
            return None

        pkg_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        pkg_table.add_column("No", justify="right", style=theme["text_key"], width=4)
        pkg_table.add_column("Nama Paket", style=theme["text_body"])
        pkg_table.add_column("Harga", justify="right", style=theme["text_money"], width=16)
        pkg_table.add_column("Source", style=theme["text_sub"], justify="right")

        for idx, p in enumerate(hot_packages, start=1):
            formatted_price = get_rupiah(p["price"])
            pkg_table.add_row(str(idx), p["name"], formatted_price, p.get("source", "local"))

        console.print(Panel(pkg_table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        console.print(Panel(nav_table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_hot_menu2 = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print_panel("Informasi", "Paket tidak tersedia.")
                pause()
                continue

            payment_items = []
            for pkg_idx, package in enumerate(packages):
                detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )

                if pkg_idx == 0:
                    main_package_detail = detail

                if not detail:
                    print_panel("Kesalahan", f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None

                payment_items.append(PaymentItem(
                    item_code=detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=detail["package_option"]["price"],
                    item_name=detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=detail["token_confirmation"],
                ))

            clear_screen()
            ensure_git()
            console.print(Panel(
                Align.center(f"{selected_package['name']}", vertical="middle"),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            simple_number()

            info_text = Text()
            info_text.append(f"{selected_package['name']}\n", style="bold")
            info_text.append(f"Harga: Rp {get_rupiah(selected_package['price'])}\n", style=theme["text_money"])
            info_text.append("Detail:\n", style=theme["text_body"])
            for line in selected_package.get("detail", "").split("\n"):
                cleaned = line.strip()
                if cleaned:
                    info_text.append(f"- {cleaned}\n", style=theme["text_body"])

            console.print(Panel(
                info_text,
                title=f"[{theme['text_title']}]Detail Paket[/]",
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))

            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                method_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
                method_table.add_column(justify="right", style=theme["text_key"], width=6)
                method_table.add_column(style=theme["text_body"])
                method_table.add_row("1", "Balance")
                method_table.add_row("2", "E-Wallet")
                method_table.add_row("3", "QRIS")
                method_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")

                console.print(Panel(
                    method_table,
                    title=f"[{theme['text_title']}]Pilih Metode Pembelian[/]",
                    border_style=theme["border_primary"],
                    padding=(0, 1),
                    expand=True
                ))

                input_method = console.input(f"[{theme['text_sub']}]Pilih metode:[/{theme['text_sub']}] ").strip()

                if input_method == "1":
                    if overwrite_amount == -1:
                        last_price = payment_items[-1].item_price if hasattr(payment_items[-1], "item_price") else payment_items[-1]["item_price"]
                        warn_price_str = get_rupiah(last_price) if isinstance(last_price, (int, float)) else str(last_price)
                        console.print(f"[{theme['text_warn']}]Pastikan sisa balance kurang dari Rp{warn_price_str}[/]")

                        balance_answer = console.input(f"[{theme['text_sub']}]Lanjutkan pembelian? (y/n):[/{theme['text_sub']}] ").strip()
                        if balance_answer.lower() != "y":
                            print_panel("Informasi", "Pembelian dibatalkan.")
                            pause()
                            in_payment_menu = False
                            continue

                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    console.input(f"[{theme['text_sub']}]Pembelian selesai, tekan Enter...[/{theme['text_sub']}] ")
                    in_payment_menu = False

                elif input_method == "2":
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    console.input(f"[{theme['text_sub']}]Pembelian selesai, tekan Enter...[/{theme['text_sub']}] ")
                    in_payment_menu = False

                elif input_method == "3":
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    console.input(f"[{theme['text_sub']}]Pembelian selesai, tekan Enter...[/{theme['text_sub']}] ")
                    in_payment_menu = False

                elif input_method == "00":
                    in_payment_menu = False
                    continue

                else:
                    print_panel("Kesalahan", "Metode tidak valid.")
                    pause()
                    continue

        else:
            print_panel("Kesalahan", "Input tidak valid.")
            pause()
            continue
