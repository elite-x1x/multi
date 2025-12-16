import json
import sys
import requests

from app3.config.imports import *
from app.type_dict import PaymentItem
from app3.menus.util import live_loading, clear_screen, pause, display_html, print_panel, get_rupiah, format_quota_byte, nav_range, simple_number
from app3.client.engsel import get_addons, send_api_request, unsubscribe
from app3.client.ciam import get_auth_code
from app3.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
from app3.client.purchase.qris import show_qris_payment
from app3.client.purchase.ewallet import show_multipayment
from app3.client.purchase.balance import settlement_balance
from app3.menus.purchase import purchase_n_times, purchase_n_times_by_option_code

console = Console()


def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order=-1):
    theme = get_theme()
    clear_screen()

    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print_panel("⚠️ Ups", "Gagal muat detail paket bro 🚨")
        pause()
        return "BACK"

    option = package.get("package_option", {})
    family = package.get("package_family", {})
    variant = package.get("package_detail_variant", {})

    price = option.get("price", 0)
    formatted_price = get_rupiah(price)
    validity = option.get("validity", "-")
    point = option.get("point", "-")
    plan_type = family.get("plan_type", "-")
    payment_for = family.get("payment_for", "") or "BUY_PACKAGE"

    token_confirmation = package.get("token_confirmation", "")
    ts_to_sign = package.get("timestamp", "")
    detail = display_html(option.get("tnc", ""))

    option_name = option.get("name", "")
    family_name = family.get("name", "")
    variant_name = variant.get("name", "")
    title = f"{family_name} - {variant_name} - {option_name}".strip()

    family_code = family.get("package_family_code", "")
    parent_code = package.get("package_addon", {}).get("parent_code", "") or "N/A"

    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]

    console.print(Panel(
        Align.center(f"📦 {family_name}", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))
    simple_number()
    ensure_git()

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["border_info"])
    info_table.add_column(justify="left")
    info_table.add_row("Nama", f": [bold {theme['text_body']}]{title}[/]")
    info_table.add_row("Harga", f": Rp [{theme['text_money']}]{formatted_price}[/]")
    info_table.add_row("Masa Aktif", f": [{theme['text_date']}]{validity}[/]")
    info_table.add_row("Point", f": [{theme['text_body']}]{point}[/]")
    info_table.add_row("Plan Type", f": [{theme['text_body']}]{plan_type}[/]")
    info_table.add_row("Payment For", f": [{theme['text_body']}]{payment_for}[/]")
    info_table.add_row("Family Code", f": [{theme['border_warning']}]{family_code}[/]")
    info_table.add_row("Parent Code", f": [{theme['text_sub']}]{parent_code}[/]")

    console.print(Panel(
        info_table,
        title=f"[{theme['text_title']}]📦 Detail Paket[/]",
        border_style=theme["border_info"],
        expand=True
    ))

    benefits = option.get("benefits", [])
    if benefits:
        benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        benefit_table.add_column("Nama", style=theme["text_body"])
        benefit_table.add_column("Jenis", style=theme["text_body"])
        benefit_table.add_column("Unli", style=theme["border_info"], justify="center")
        benefit_table.add_column("Total", style=theme["text_body"], justify="right")

        for b in benefits:
            dt = b["data_type"]
            total = b["total"]
            is_unli = b["is_unlimited"]

            if is_unli:
                total_str = {"VOICE": "menit", "TEXT": "SMS", "DATA": "kuota"}.get(dt, dt)
            else:
                if dt == "VOICE":
                    total_str = f"{total / 60:.0f} menit"
                elif dt == "TEXT":
                    total_str = f"{total} SMS"
                elif dt == "DATA":
                    if total >= 1_000_000_000:
                        total_str = f"{total / (1024 ** 3):.2f} GB"
                    elif total >= 1_000_000:
                        total_str = f"{total / (1024 ** 2):.2f} MB"
                    elif total >= 1_000:
                        total_str = f"{total / 1024:.2f} KB"
                    else:
                        total_str = f"{total} B"
                else:
                    total_str = f"{total} ({dt})"

            benefit_table.add_row(b["name"], dt, "YES" if is_unli else "-", total_str)

        console.print(Panel(
            benefit_table,
            title=f"[{theme['text_title']}]🎁 Benefit Paket[/]",
            border_style=theme["border_success"],
            padding=(0, 0),
            expand=True
        ))

    console.print(Panel(
        detail,
        title=f"[{theme['text_title']}]📜 Syarat & Ketentuan[/]",
        border_style=theme["border_warning"],
        expand=True
    ))

    nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    nav_table.add_column(justify="right", style=theme["text_key"], width=6)
    nav_table.add_column(style=theme["text_body"])
    nav_table.add_row("1", "💰 Beli pake Pulsa")
    nav_table.add_row("2", "💳 Bayar via E-Wallet")
    nav_table.add_row("3", "📱 QRIS")
    nav_table.add_row("4", "💰 Pulsa + Decoy")
    nav_table.add_row("5", "💰 Pulsa + Decoy V2")
    nav_table.add_row("6", "📱 QRIS + Decoy (+1K)")
    nav_table.add_row("7", "📱 QRIS + Decoy V2")
    nav_table.add_row("8", "💰 Pulsa N kali")
    if payment_for == "REDEEM_VOUCHER":
        nav_table.add_row("B", "🎁 Ambil bonus bro")
        nav_table.add_row("BA", "🎁 Kirim bonus ke temen")
        nav_table.add_row("L", "⭐ Beli pake Poin")
    if option_order != -1:
        nav_table.add_row("0", "🔖 Tambahin ke Bookmark")
    nav_table.add_row("00", f"[{theme['text_sub']}]Balik ke daftar paket ✌️[/]")

    console.print(Panel(
        nav_table,
        title=f"[{theme['text_title']}]🛒 Opsi Pembelian[/]",
        border_style=theme["border_primary"],
        expand=True
    ))

    choice = console.input(f"[{theme['text_sub']}]👉 Pilihan lo bro:[/{theme['text_sub']}] ").strip()

    if choice == "00":
        return "BACK"

    elif choice == "0" and option_order != -1:
        success = BookmarkInstance.add_bookmark(
            family_code=package.get("package_family", {}).get("package_family_code",""),
            family_name=package.get("package_family", {}).get("name",""),
            is_enterprise=is_enterprise,
            variant_name=variant_name,
            option_name=option_name,
            order=option_order,
        )
        if success:
            print_panel("✅ Mantap", "Paket udah masuk bookmark bro 🚀")
        else:
            print_panel("ℹ️ Santai", "Paket udah ada di bookmark bro 🙅")
        pause()
        return True

    elif choice == "1":
        settlement_balance(api_key, tokens, payment_items, payment_for, True)
        #print_panel("✅ Mantap", "Pembelian via pulsa sukses bro 🚀")
        pause()
        return True

    elif choice == "2":
        show_multipayment(api_key, tokens, payment_items, payment_for, True)
        #print_panel("✅ Mantap", "Pembayaran via e-wallet sukses bro 🚀")
        pause()
        return True

    elif choice == "3":
        show_qris_payment(api_key, tokens, payment_items, payment_for, True)
        #print_panel("✅ Mantap", "QRIS jalan lancar bro 🚀")
        pause()
        return True

    elif choice == "4":
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Ups", "Detail paket decoy nggak ketemu bro 🚨")
            pause()
            return "BACK"

        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

        overwrite_amount = price + decoy_package_detail["package_option"]["price"]
        res = settlement_balance(api_key, tokens, payment_items, payment_for, False, overwrite_amount=overwrite_amount)

        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Error ngaco bro")
            if "Bizz-err.Amount.Total" in error_msg:
                valid_amount = int(error_msg.split("=")[1].strip())
                print_panel("ℹ️ Santai", f"Total disesuaikan ke: {valid_amount}")
                res = settlement_balance(api_key, tokens, payment_items, payment_for, False, overwrite_amount=valid_amount)
                if res and res.get("status", "") == "SUCCESS":
                    print_panel("✅ Mantap", "Pembelian sukses bro 🚀")
        else:
            print_panel("✅ Mantap", "Pembelian sukses bro 🚀")
        pause()
        return True

    elif choice == "5":
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Ups", "Detail paket decoy nggak ketemu bro 🚨")
            pause()
            return "BACK"

        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

        overwrite_amount = price + decoy_package_detail["package_option"]["price"]
        res = settlement_balance(
            api_key, tokens, payment_items, "🤫", False,
            overwrite_amount=overwrite_amount, token_confirmation_idx=1
        )

        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Error ngaco bro")
            if "Bizz-err.Amount.Total" in error_msg:
                valid_amount = int(error_msg.split("=")[1].strip())
                print_panel("ℹ️ Santai", f"Total disesuaikan ke: {valid_amount}")
                res = settlement_balance(api_key, tokens, payment_items, "🤫", False, overwrite_amount=valid_amount, token_confirmation_idx=-1)
                if res and res.get("status", "") == "SUCCESS":
                    print_panel("✅ Mantap", "Pembelian sukses bro 🚀")
        else:
            print_panel("✅ Mantap", "Pembelian sukses bro 🚀")
        pause()
        return True

    elif choice == "6":
        decoy = DecoyInstance.get_decoy("qris")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Ups", "Detail paket decoy nggak ketemu bro 🚨")
            pause()
            return "BACK"

        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

        console.rule()
        console.print(f"Harga Paket Utama: Rp {price}")
        console.print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
        console.print("⚡ Silakan utak-atik amount bro (trial & error, 0 = ngaco)")
        console.rule()

        show_qris_payment(api_key, tokens, payment_items, "SHARE_PACKAGE", True, token_confirmation_idx=1)
        pause()
        return True

    elif choice == "7":
        decoy = DecoyInstance.get_decoy("qris0")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Ups", "Detail paket decoy nggak ketemu bro 🚨")
            pause()
            return "BACK"

        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=decoy_package_detail["package_option"]["name"],
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

        console.rule()
        console.print(f"Harga Paket Utama: Rp {price}")
        console.print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
        console.print("⚡ Silakan utak-atik amount bro (trial & error, 0 = ngaco)")
        console.rule()

        show_qris_payment(api_key, tokens, payment_items, "SHARE_PACKAGE", True, token_confirmation_idx=1)
        pause()
        return True

    elif choice == "8":
        use_decoy_for_n_times = console.input("Pake decoy paket bro? (y/n): ").strip().lower() == 'y'
        n_times_str = console.input("Mau beli berapa kali bro (cth: 3): ").strip()
        delay_seconds_str = console.input("Delay antar pembelian (detik, cth: 25): ").strip()
        if not delay_seconds_str.isdigit():
            delay_seconds_str = "0"

        try:
            n_times = int(n_times_str)
            if n_times < 1:
                raise ValueError("Minimal 1 bro.")
        except ValueError:
            print_panel("⚠️ Ups", "Input jumlah ngaco bro 🚨")
            pause()
            return "BACK"

        purchase_n_times_by_option_code(
            n_times,
            option_code=package_option_code,
            use_decoy=use_decoy_for_n_times,
            delay_seconds=int(delay_seconds_str),
            pause_on_success=False,
            token_confirmation_idx=1
        )
        #print_panel("✅ Mantap", f"Pembelian {n_times}x sukses bro 🚀")
        pause()
        return True

    elif choice.lower() == "b":
        settlement_bounty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=package_option_code,
            price=price,
            item_name=variant_name
        )
        #print_panel("✅ Mantap", "Bonus berhasil diambil bro 🎁")
        pause()
        return True

    elif choice.lower() == "ba":
        destination_msisdn = console.input("Masukin nomor tujuan bonus bro (62xxx): ").strip()
        bounty_allotment(
            api_key=api_key,
            tokens=tokens,
            ts_to_sign=ts_to_sign,
            destination_msisdn=destination_msisdn,
            item_name=option_name,
            item_code=package_option_code,
            token_confirmation=token_confirmation,
        )
        #print_panel("✅ Mantap", "Bonus berhasil dikirim bro 🎁")
        pause()
        return True

    elif choice.lower() == "l":
        settlement_loyalty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=package_option_code,
            price=price,
        )
        #print_panel("✅ Mantap", "Pembelian pake poin sukses bro ⭐")
        pause()
        return True

    else:
        print_panel("ℹ️ Santai", "Pembelian dibatalin bro 🙅")
        pause()
        return "BACK"


def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    return_package_detail: bool = False
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    if not tokens:
        print_panel("⚠️ Ups", "Token user aktif nggak ketemu bro 🚨")
        return "BACK"

    data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    if not data:
        print_panel("⚠️ Ups", "Gagal muat data paket family bro 🚨")
        return "BACK"

    price_currency = "Rp"
    if data["package_family"].get("rc_bonus_type") == "MYREWARDS":
        price_currency = "Poin"

    packages = []
    for variant in data["package_variants"]:
        for option in variant["package_options"]:
            packages.append({
                "number": len(packages) + 1,
                "variant_name": variant["name"],
                "option_name": option["name"],
                "price": option["price"],
                "code": option["package_option_code"],
                "option_order": option["order"]
            })

    while True:
        clear_screen()
        ensure_git()
        console.print(Panel(
            Align.center(f"📦 {data['package_family']['name']}", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        info_text = Text()
        info_text.append("Nama Family: ", style=theme["border_info"])
        info_text.append(f"{data['package_family']['name']}\n", style=theme["text_value"])
        info_text.append("Kode Family: ", style=theme["border_info"])
        info_text.append(f"{family_code}\n", style=theme["border_warning"])
        info_text.append("Tipe Paket: ", style=theme["border_info"])
        info_text.append(f"{data['package_family']['package_family_type']}\n", style=theme["text_value"])
        info_text.append("Jumlah Varian: ", style=theme["border_info"])
        info_text.append(f"{len(data['package_variants'])}\n", style=theme["text_value"])

        console.print(Panel(
            info_text,
            border_style=theme["border_info"],
            padding=(0, 2),
            expand=True
        ))

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Varian", style=theme["text_body"])
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_money"], justify="right")

        for pkg in packages:
            harga_str = get_rupiah(pkg["price"]) if price_currency == "Rp" else f"{pkg['price']} Poin"
            table.add_row(
                str(pkg["number"]),
                pkg["variant_name"],
                pkg["option_name"],
                harga_str
            )

        console.print(Panel(
            table,
            border_style=theme["border_info"],
            padding=(0, 0),
            expand=True
        ))

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Balik ke menu sebelumnya ✌️[/]")

        console.print(Panel(
            nav,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_title']}]👉 Pilih (nomor) paket bro:[/{theme['text_title']}] ").strip()
        if choice == "00":
            return "BACK"
        if not choice.isdigit():
            print_panel("⚠️ Ups", "Input ngaco bro, masukin nomor paket 🚨")
            pause()
            continue

        selected = next((p for p in packages if p["number"] == int(choice)), None)
        if not selected:
            print_panel("⚠️ Ups", "Nomor paket nggak ketemu bro 🚨")
            pause()
            continue

        if return_package_detail:
            variant_code = next((v["package_variant_code"] for v in data["package_variants"] if v["name"] == selected["variant_name"]), None)
            detail = get_package_details(
                api_key, tokens,
                family_code,
                variant_code,
                selected["option_order"],
                is_enterprise
            )
            if detail:
                display_name = f"{data['package_family']['name']} - {selected['variant_name']} - {selected['option_name']}"
                return detail, display_name
            else:
                print_panel("⚠️ Ups", "Gagal ngambil detail paket bro 🚨")
                pause()
                continue
        else:
            result = show_package_details(
                api_key,
                tokens,
                selected["code"],
                is_enterprise,
                option_order=selected["option_order"]
            )
            if result == "MAIN":
                return "MAIN"
            elif result == "BACK":
                continue
            elif result is True:
                continue


def fetch_my_packages():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print_panel("⚠️ Ups", "Token user aktif nggak ketemu bro 🚨")
        pause()
        return "BACK"

    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    with live_loading("🔄 Lagi ngambil paket aktif bro...", theme):
        res = send_api_request(api_key, path, payload, id_token, "POST")

    if res.get("status") != "SUCCESS":
        print_panel("⚠️ Ups", "Gagal ngambil paket aktif bro 🚨")
        pause()
        return "BACK"

    quotas = res["data"]["quotas"]
    if not quotas:
        print_panel("ℹ️ Info", "Nggak ada paket aktif ketemu bro 🙅")
        pause()
        return "BACK"

    while True:
        clear_screen()
        ensure_git()
        console.print(Panel(
            Align.center("📦 Paket Aktif Gue", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        my_packages = []
        for num, quota in enumerate(quotas, start=1):
            quota_code = quota["quota_code"]
            group_code = quota["group_code"]
            quota_name = quota["name"]
            family_code = "N/A"

            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")

            benefits = quota.get("benefits", [])
            benefit_table = None
            if benefits:
                benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
                benefit_table.add_column("Nama", style=theme["text_body"])
                benefit_table.add_column("Jenis", style=theme["text_body"])
                benefit_table.add_column("Kuota", style=theme["text_body"], justify="right")

                for b in benefits:
                    name = b.get("name", "")
                    dt = b.get("data_type", "N/A")
                    r = b.get("remaining", 0)
                    t = b.get("total", 0)

                    if dt == "DATA":
                        r_str = format_quota_byte(r)
                        t_str = format_quota_byte(t)
                    elif dt == "VOICE":
                        r_str = f"{r / 60:.2f} menit"
                        t_str = f"{t / 60:.2f} menit"
                    elif dt == "TEXT":
                        r_str = f"{r} SMS"
                        t_str = f"{t} SMS"
                    else:
                        r_str = str(r)
                        t_str = str(t)

                    benefit_table.add_row(name, dt, f"{r_str} / {t_str}")

            package_details = get_package(api_key, tokens, quota_code)
            if package_details:
                family_code = package_details["package_family"]["package_family_code"]

            package_text = Text()
            package_text.append(f"📦 Paket {num}\n", style="bold")
            package_text.append("Nama: ", style=theme["border_info"])
            package_text.append(f"{quota_name}\n", style=theme["text_sub"])
            package_text.append("Quota Code: ", style=theme["border_info"])
            package_text.append(f"{quota_code}\n", style=theme["text_body"])
            package_text.append("Family Code: ", style=theme["border_info"])
            package_text.append(f"{family_code}\n", style=theme["border_warning"])
            package_text.append("Group Code: ", style=theme["border_info"])
            package_text.append(f"{group_code}\n", style=theme["text_body"])

            panel_content = [package_text]
            if benefit_table:
                panel_content.append(benefit_table)

            console.print(Panel(
                Group(*panel_content),
                border_style=theme["border_info"],
                padding=(0, 1),
                expand=True
            ))

            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Balik ke menu utama[/]")
        nav_table.add_row(nav_range("", len(my_packages)), "Lihat detail paket 👀 ")
        nav_table.add_row(nav_range("del", len(my_packages)), f"[{theme['text_err']}]Hapus paket 🗑️ [/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]👉 Pilihan lo bro:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"

        if choice.isdigit():
            nomor = int(choice)
            selected = next((p for p in my_packages if p["number"] == nomor), None)
            if not selected:
                print_panel("⚠️ Ups", "Nomor paket nggak ketemu bro 🚨")
                pause()
                continue
            show_package_details(api_key, tokens, selected["quota_code"], False)
            continue

        elif choice.startswith("del "):
            parts = choice.split(" ")
            if len(parts) != 2 or not parts[1].isdigit():
                print_panel("⚠️ Ups", "Format hapus paket ngaco bro 🚨")
                pause()
                continue

            nomor = int(parts[1])
            selected = next((p for p in my_packages if p["number"] == nomor), None)
            if not selected:
                print_panel("⚠️ Ups", "Nomor paket nggak ketemu bro 🚨")
                pause()
                continue

            confirm = console.input(f"[{theme['text_sub']}]Yakin mau unsubscribe paket {nomor} - {selected['name']}? (y/n):[/{theme['text_sub']}] ").strip().lower()
            if confirm == "y":
                with live_loading("🔄 Lagi hapus paket bro...", theme):
                    success = unsubscribe(
                        api_key,
                        tokens,
                        selected["quota_code"],
                        selected["product_subscription_type"],
                        selected["product_domain"]
                    )
                print_panel("✅ Mantap" if success else "⚠️ Ups", "Unsubscribe sukses bro 🚀" if success else "Gagal unsubscribe bro 🚨")
            else:
                print_panel("❎ Info", "Unsubscribe dibatalin bro 🙅")
            pause()

