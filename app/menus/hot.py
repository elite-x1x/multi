import requests

from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, format_quota_byte, pause, display_html
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.util import merge_hot1, merge_hot2

WIDTH = 55


def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_hot_menu = True
    while in_hot_menu:
        clear_screen()
        print("=" * WIDTH)
        print("🔥 Paket HOT 🔥".center(WIDTH))
        print("=" * WIDTH)

        hot1_packages = merge_hot1("https://me.mashu.lol/pg-hot.json")

        if not hot1_packages:
            print("⚠️ Nggak ada data HOT1 bro.")
            pause()
            return None

        for idx, p in enumerate(hot1_packages, 1):
            print(f"[{idx}.] {p['family_name']} - {p['variant_name']} - {p['option_name']}")
            print(f"     (source: {p['source']})")
            print("-" * WIDTH)

        print("[00.] Balik ke menu utama")
        print("-" * WIDTH)
        choice = input("Pilih paket (nomor): ").strip()

        if choice == "00":
            in_hot_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot1_packages):
            selected_bm = hot1_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]

            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print("💥 Gagal ambil data family bro.")
                pause()
                continue

            option_code = None
            for variant in family_data.get("package_variants", []):
                if variant["name"] == selected_bm["variant_name"]:
                    for option in variant.get("package_options", []):
                        if option["order"] == selected_bm["order"]:
                            option_code = option.get("package_option_code")
                            break

            if option_code:
                print(f"🎯 Option code: {option_code}")
                show_package_details(api_key, tokens, option_code, is_enterprise)
        else:
            print("⚠️ Input nggak valid bro. Coba lagi ✌️")
            pause()
            continue


def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_hot_menu2 = True
    while in_hot_menu2:
        clear_screen()
        main_package_detail = {}
        print("=" * WIDTH)
        print("🔥 Paket HOT 2 🔥".center(WIDTH))
        print("=" * WIDTH)

        hot2_packages = merge_hot2("https://me.mashu.lol/pg-hot2.json")

        if not hot2_packages:
            print("⚠️ Nggak ada data HOT2 bro.")
            pause()
            return None

        for idx, p in enumerate(hot2_packages, 1):
            print(f"[{idx}.] {p['name']} - {p['price']}")
            print(f"     (source: {p['source']})")
            print("-" * WIDTH)

        print("[00.] Balik ke menu utama")
        print("-" * WIDTH)
        choice = input("Pilih paket (nomor): ").strip()

        if choice == "00":
            in_hot_menu2 = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot2_packages):
            selected_package = hot2_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if not packages:
                print("⚠️ Paket nggak tersedia bro.")
                pause()
                continue

            payment_items = []
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )

                if package == packages[0]:
                    main_package_detail = package_detail

                if not package_detail:
                    print(f"💥 Gagal ambil detail paket {package['family_code']} bro.")
                    return None

                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )

            clear_screen()
            print("=" * WIDTH)
            print(f"Nama: {selected_package['name']}")
            print(f"Harga: {selected_package['price']}")
            print(f"Detail: {selected_package['detail']}")
            print("=" * WIDTH)
            print("Main Package Details:".center(WIDTH))
            print("-" * WIDTH)

            price = main_package_detail["package_option"]["price"]
            detail = display_html(main_package_detail["package_option"]["tnc"])
            validity = main_package_detail["package_option"]["validity"]

            option_name = main_package_detail.get("package_option", {}).get("name", "")
            family_name = main_package_detail.get("package_family", {}).get("name", "")
            variant_name = main_package_detail.get("package_detail_variant", {}).get("name", "")

            title = f"{family_name} - {variant_name} - {option_name}".strip()

            family_code = main_package_detail.get("package_family", {}).get("package_family_code", "")
            parent_code = main_package_detail.get("package_addon", {}).get("parent_code", "") or "N/A"

            payment_for = main_package_detail["package_family"]["payment_for"]

            print(f"Nama: {title}")
            print(f"Harga: Rp {price}")
            print(f"Payment For: {payment_for}")
            print(f"Masa Aktif: {validity}")
            print(f"Point: {main_package_detail['package_option']['point']}")
            print(f"Plan Type: {main_package_detail['package_family']['plan_type']}")
            print("-" * WIDTH)
            print(f"Family Code: {family_code}")
            print(f"Parent Code: {parent_code}")
            print("-" * WIDTH)

            benefits = main_package_detail["package_option"]["benefits"]
            if benefits and isinstance(benefits, list):
                print("Benefits:")
                for benefit in benefits:
                    print("-" * WIDTH)
                    print(f" Name: {benefit['name']}")
                    print(f"  Item id: {benefit['item_id']}")
                    data_type = benefit['data_type']
                    if data_type == "VOICE" and benefit['total'] > 0:
                        print(f"  Total: {benefit['total']/60} menit")
                    elif data_type == "TEXT" and benefit['total'] > 0:
                        print(f"  Total: {benefit['total']} SMS")
                    elif data_type == "DATA" and benefit['total'] > 0:
                        quota_formatted = format_quota_byte(int(benefit['total']))
                        print(f"  Total: {quota_formatted} ({data_type})")
                    else:
                        print(f"  Total: {benefit['total']} ({data_type})")

                    if benefit.get("is_unlimited"):
                        print("  Unlimited: Yes")

            print("-" * WIDTH)
            print(f"SnK MyXL:\n{detail}")
            print("=" * WIDTH)

            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                print("Pilih Metode Pembelian:")
                print(" [1.] Balance 💰")
                print(" [2.] E-Wallet 📱")
                print(" [3.] QRIS 🔳")
                print("[00.] Balik ke menu sebelumnya")
                print("=" * WIDTH)

                input_method = input("Pilih metode (nomor): ").strip()
                if input_method == "1":
                    if overwrite_amount == -1:
                        print(f"⚠️ Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']}!!!")
                        balance_answer = input("Yakin lanjut pembelian? (y/n): ").strip().lower()
                        if balance_answer != "y":
                            print("↩️ Pembelian dibatalin bro.")
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
                    pause()
                    in_payment_menu = False
                    in_hot_menu2 = False

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
                    pause()
                    in_payment_menu = False
                    in_hot_menu2 = False

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
                    pause()
                    in_payment_menu = False
                    in_hot_menu2 = False

                elif input_method == "00":
                    in_payment_menu = False
                    continue

                else:
                    print("⚠️ Metode nggak valid bro. Coba lagi ✌️")
                    pause()
                    continue
        else:
            print("⚠️ Input nggak valid bro. Coba lagi ✌️")
            pause()
            continue
