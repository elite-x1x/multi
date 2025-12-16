import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request, unsubscribe
from app.client.ciam import get_auth_code
from app.service.bookmark import BookmarkInstance
from app.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte
from app.service.decoy import DecoyInstance

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order=-1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")

    clear_screen()
    print("=" * 55)
    print("📦 Detail Paket".center(55))
    print("=" * 55)

    package = get_package(api_key, tokens, package_option_code)
    if not package:
        print("💥 Gagal load detail paket bro.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name", "")
    family_name = package.get("package_family", {}).get("name", "")
    variant_name = package.get("package_detail_variant", {}).get("name", "")
    title = f"{family_name} - {variant_name} - {option_name}".strip()

    family_code = package.get("package_family", {}).get("package_family_code", "")
    parent_code = package.get("package_addon", {}).get("parent_code", "") or "N/A"

    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"] or "BUY_PACKAGE"

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

    print("-" * 55)
    print(f"Nama: {title}")
    print(f"Harga: Rp {price}")
    print(f"Payment For: {payment_for}")
    print(f"Masa Aktif: {validity}")
    print(f"Point: {package['package_option']['point']}")
    print(f"Plan Type: {package['package_family']['plan_type']}")
    print("-" * 55)
    print(f"Family Code: {family_code}")
    print(f"Parent Code: {parent_code}")
    print("-" * 55)

    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        print("✨ Benefits:")
        for benefit in benefits:
            print("-" * 55)
            print(f" Name: {benefit['name']}")
            print(f"  Item id: {benefit['item_id']}")
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']/60} menit")
            elif data_type == "TEXT" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']} SMS")
            elif data_type == "DATA" and benefit['total'] > 0:
                quota = int(benefit['total'])
                print(f"  Kuota: {format_quota_byte(quota)}")
            else:
                print(f"  Total: {benefit['total']} ({data_type})")

            if benefit.get("is_unlimited"):
                print("  Unlimited: Yes")

    print("-" * 55)
    addons = get_addons(api_key, tokens, package_option_code)
    print(f"Addons:\n{json.dumps(addons, indent=2)}")
    print("-" * 55)
    print(f"SnK MyXL:\n{detail}")
    print("=" * 55)

    in_package_detail_menu = True
    while in_package_detail_menu:
        print("Options:")
        print(" [1.] Beli dengan Pulsa 💰")
        print(" [2.] Beli dengan E-Wallet 📱")
        print(" [3.] Bayar dengan QRIS 🔳")
        print(" [4.] Pulsa + Decoy 🤫")
        print(" [5.] Pulsa + Decoy V2 🤫")
        print(" [6.] QRIS + Decoy (+1K)")
        print(" [7.] QRIS + Decoy V2")
        print(" [8.] Pulsa N kali 🔄")

        if payment_for == "REDEEM_VOUCHER":
            print(" [B.] Ambil sebagai bonus 🎁")
            print("[BA.] Kirim bonus 🎁")
            print(" [L.] Beli dengan Poin ⭐")

        if option_order != -1:
            print(" [0.] Tambah ke Bookmark 📌")
        print("[00.] Balik ke daftar paket")
        print("=" * 55)

        choice = input("Pilihan: ").strip()
        if choice == "00":
            return False
        elif choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print("✅ Paket ditambah ke bookmark bro.")
            else:
                print("⚠️ Paket udah ada di bookmark bro.")
            pause()
            continue

        elif choice == '1':
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True
            )
            if res and res.get("status", "") == "SUCCESS":
                print("✅ Silahkan cek hasil pembelian di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembelian pulsa gagal bro: {error_msg}")
            pause()
            return True
        
        elif choice == '2':
            res = show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            if res and res.get("status", "") == "SUCCESS":
                print("✅ Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembayaran via E-Wallet gagal bro: {error_msg}")
            pause()
            return True
        
        elif choice == '3':
            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            if res and res.get("status", "") == "SUCCESS":
                print("✅ Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembayaran via QRIS gagal bro: {error_msg}")
            pause()
            return True

        elif choice == '4':
            # Balance with Decoy 🤫
            decoy = DecoyInstance.get_decoy("balance")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])

            if not decoy_package_detail:
                print("💥 Gagal load detail paket decoy bro.")
                pause()
                return False

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
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )

            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())

                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("✅ Pembelian berhasil bro.")
                    else:
                        error_msg = res.get("message", "Unknown error") if res else "No response"
                        print(f"⚠️ Pembelian pulsa + decoy gagal bro: {error_msg}")
                else:
                    print(f"⚠️ Pembelian pulsa + decoy gagal bro: {error_msg}")
            else:
                print("✅ Pembelian berhasil bro.")
            pause()
            return True

        elif choice == '5':
            # Balance with Decoy v2 🤫 (pakai token confirmation decoy)
            decoy = DecoyInstance.get_decoy("balance")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])

            if not decoy_package_detail:
                print("💥 Gagal load detail paket decoy bro.")
                pause()
                return False

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
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )

            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())

                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("✅ Pembelian berhasil bro.")
                    else:
                        error_msg = res.get("message", "Unknown error") if res else "No response"
                        print(f"⚠️ Pembelian pulsa + decoy v2 gagal bro: {error_msg}")
                else:
                    print(f"⚠️ Pembelian pulsa + decoy v2 gagal bro: {error_msg}")
            else:
                print("✅ Pembelian berhasil bro.")
            pause()
            return True

        elif choice == '6':
            # QRIS decoy + Rpx 🔳🤫
            decoy = DecoyInstance.get_decoy("qris")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])

            if not decoy_package_detail:
                print("💥 Gagal load detail paket decoy bro.")
                pause()
                return False

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

            print("-" * 55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("⚠️ Silakan sesuaikan amount (trial & error, 0 = malformed)")
            print("-" * 55)

            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )

            if res and res.get("status", "") == "SUCCESS":
                print("✅ Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembayaran QRIS + Decoy (+1K) gagal bro: {error_msg}")
            pause()
            return True

        elif choice == '7':
            # QRIS decoy + Rp0 🔳🤫
            decoy = DecoyInstance.get_decoy("qris0")
            decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])

            if not decoy_package_detail:
                print("💥 Gagal load detail paket decoy bro.")
                pause()
                return False

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

            print("-" * 55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("⚠️ Silakan sesuaikan amount (trial & error, 0 = malformed)")
            print("-" * 55)

            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )

            if res and res.get("status", "") == "SUCCESS":
                print("✅ Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembayaran QRIS + Decoy V2 gagal bro: {error_msg}")
            pause()
            return True

        elif choice == '8':
            # Pulsa N kali 🔄
            use_decoy_for_n_times = input("Mau pake decoy package? (y/n): ").strip().lower() == 'y'
            n_times_str = input("Masukin jumlah pembelian (contoh 3): ").strip()
            delay_seconds_str = input("Masukin jeda antar pembelian (detik, contoh 25): ").strip()

            if not delay_seconds_str.isdigit():
                delay_seconds_str = "0"

            try:
                n_times = int(n_times_str)
                if n_times < 1:
                    raise ValueError("Jumlah minimal 1 bro.")
            except ValueError:
                print("⚠️ Input jumlah nggak valid bro. Masukin angka yang bener ✌️")
                pause()
                continue

            res = purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_seconds_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )

            if res and res.get("status", "") == "SUCCESS":
                print(f"✅ Pembelian pulsa {n_times} kali berhasil bro.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembelian pulsa {n_times} kali gagal bro: {error_msg}")
            pause()
            return True

        elif choice == '9':
            # Debug Share Package 🐞
            pin = input("Masukin PIN (6 digit): ").strip()
            if len(pin) != 6:
                print("⚠️ PIN terlalu pendek bro.")
                pause()
                continue

            auth_code = get_auth_code(tokens, pin, active_user["number"])
            if not auth_code:
                print("💥 Gagal dapetin auth_code bro.")
                pause()
                continue

            target_msisdn = input("Masukin nomor tujuan (62xxxx): ").strip()
            url = "https://me.mashu.lol/pg-decoy-edu.json"

            try:
                response = requests.get(url, timeout=30)
            except Exception as e:
                print(f"💥 Error ambil data decoy: {e}")
                pause()
                return None

            if response.status_code != 200:
                print("⚠️ Gagal ambil data decoy package bro.")
                pause()
                return None

            decoy_data = response.json()
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                topup_number=target_msisdn,
                stage_token=auth_code,
            )

            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())

                    print(f"⚠️ Adjusted total amount ke: {valid_amount}")
                    res = show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        "SHARE_PACKAGE",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=0,
                        topup_number=target_msisdn,
                        stage_token=auth_code,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("✅ Purchase berhasil bro.")
                    else:
                        error_msg = res.get("message", "Unknown error") if res else "No response"
                        print(f"⚠️ Purchase gagal bro: {error_msg}")
                else:
                    print(f"⚠️ Purchase gagal bro: {error_msg}")
            else:
                print("✅ Purchase berhasil bro.")

            # ⚠️ Jangan pop payment_items kalau nggak ada append di atas
            pause()
            return True
       
        elif choice.lower() == 'b':
            # Ambil sebagai bonus 🎁
            res = settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            if res and res.get("status", "") == "SUCCESS":
                print("✅ Bonus berhasil diambil bro. Silakan cek di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Bonus gagal diambil bro: {error_msg}")
            pause()
            return True

        elif choice.lower() == 'ba':
            # Kirim bonus 🎁➡️📱
            destination_msisdn = input("Masukin nomor tujuan bonus (62xxxx): ").strip()
            res = bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            if res and res.get("status", "") == "SUCCESS":
                print(f"✅ Bonus berhasil dikirim ke {destination_msisdn} bro.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Bonus gagal dikirim bro: {error_msg}")
            pause()
            return True

        elif choice.lower() == 'l':
            # Beli dengan Poin ⭐
            res = settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            if res and res.get("status", "") == "SUCCESS":
                print("✅ Pembelian dengan poin berhasil bro. Silakan cek di aplikasi MyXL.")
            else:
                error_msg = res.get("message", "Unknown error") if res else "No response"
                print(f"⚠️ Pembelian dengan poin gagal bro: {error_msg}")
            pause()
            return True

        else:
            print("Purchase cancelled.")
            return False
    pause()
    sys.exit(0)


def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("⚠️ Nggak ada token aktif bro. Login dulu.")
        pause()
        return None

    packages = []

    data = get_family(
        api_key,
        tokens,
        family_code,
        is_enterprise,
        migration_type
    )

    if not data:
        print("💥 Gagal load data family bro.")
        pause()
        return None

    price_currency = "Rp"
    rc_bonus_type = data["package_family"].get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"

    in_package_menu = True
    while in_package_menu:
        clear_screen()
        print("=" * 55)
        print(f"👨‍👩‍👧 Family Name: {data['package_family']['name']}")
        print(f"🔑 Family Code: {family_code}")
        print(f"📦 Family Type: {data['package_family']['package_family_type']}")
        print(f"📊 Variant Count: {len(data['package_variants'])}")
        print("=" * 55)
        print("✨ Paket Tersedia ✨")
        print("=" * 55)

        package_variants = data["package_variants"]

        option_number = 1
        variant_number = 1

        for variant in package_variants:
            variant_name = variant["name"]
            variant_code = variant["package_variant_code"]
            print(f" Variant {variant_number}: {variant_name}")
            print(f" Code: {variant_code}")
            for option in variant["package_options"]:
                option_name = option["name"]

                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })

                print(f"  [{option_number}.] {option_name} - {price_currency} {option['price']}")
                option_number += 1

            if variant_number < len(package_variants):
                print("-" * 55)
            variant_number += 1
        print("=" * 55)

        print("[00.] Balik ke menu utama")
        print("=" * 55)
        pkg_choice = input("Pilih paket (nomor): ").strip()

        if pkg_choice == "00":
            in_package_menu = False
            return None

        if not pkg_choice.isdigit():
            print("⚠️ Input nggak valid bro. Masukin nomor paket yang bener ✌️")
            pause()
            continue

        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)

        if not selected_pkg:
            print("❌ Paket nggak ketemu bro. Masukin nomor yang bener.")
            pause()
            continue

        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )

    return packages


def fetch_my_packages():
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            print("⚠️ Nggak ada token aktif bro. Login dulu.")
            pause()
            return None

        id_token = tokens.get("id_token")
        path = "api/v8/packages/quota-details"
        payload = {
            "is_enterprise": False,
            "lang": "en",
            "family_member_id": ""
        }

        print("🔍 Lagi ambil paket kamu bro...")
        res = send_api_request(api_key, path, payload, id_token, "POST")
        if res.get("status") != "SUCCESS":
            print("💥 Gagal ambil paket bro.")
            print("Response:", res)
            pause()
            return None

        quotas = res["data"]["quotas"]

        clear_screen()
        print("=" * 55)
        print("📦 My Packages".center(55))
        print("=" * 55)

        my_packages = []
        num = 1
        for quota in quotas:
            quota_code = quota["quota_code"]
            group_code = quota["group_code"]
            group_name = quota["group_name"]
            quota_name = quota["name"]
            family_code = "N/A"

            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")

            benefit_infos = []
            for benefit in quota.get("benefits", []):
                benefit_id = benefit.get("id", "")
                name = benefit.get("name", "")
                data_type = benefit.get("data_type", "N/A")
                benefit_info = "  -----------------------------------------------------\n"
                benefit_info += f"  ID    : {benefit_id}\n"
                benefit_info += f"  Name  : {name}\n"
                benefit_info += f"  Type  : {data_type}\n"

                remaining = benefit.get("remaining", 0)
                total = benefit.get("total", 0)

                if data_type == "DATA":
                    remaining_str = format_quota_byte(remaining)
                    total_str = format_quota_byte(total)
                    benefit_info += f"  Kuota : {remaining_str} / {total_str}"
                elif data_type == "VOICE":
                    benefit_info += f"  Kuota : {remaining/60:.2f} / {total/60:.2f} menit"
                elif data_type == "TEXT":
                    benefit_info += f"  Kuota : {remaining} / {total} SMS"
                else:
                    benefit_info += f"  Kuota : {remaining} / {total}"

                benefit_infos.append(benefit_info)

            print(f"🔎 Fetching package no. {num} details...")
            package_details = get_package(api_key, tokens, quota_code)
            if package_details:
                family_code = package_details["package_family"]["package_family_code"]

            print("=" * 55)
            print(f"📦 Package {num}")
            print(f"Name: {quota_name}")
            print("Benefits:")
            if benefit_infos:
                for bi in benefit_infos:
                    print(bi)
                print("  -----------------------------------------------------")
            print(f"Group Name: {group_name}")
            print(f"Quota Code: {quota_code}")
            print(f"Family Code: {family_code}")
            print(f"Group Code: {group_code}")
            print("=" * 55)

            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })
            num += 1

        print("👉 Input nomor paket buat liat detail.")
        print("👉 Input del <nomor paket> buat unsubscribe.")
        print("👉 Input 00 buat balik ke menu utama.")
        print("=" * 55)
        choice = input("Pilihan: ").strip()

        if choice == "00":
            in_my_packages_menu = False

        elif choice.isdigit() and 1 <= int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                print("❌ Paket nggak ketemu bro. Masukin nomor yang bener.")
                pause()
                continue
            _ = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)

        elif choice.startswith("del "):
            del_parts = choice.split(" ")
            if len(del_parts) != 2 or not del_parts[1].isdigit():
                print("⚠️ Format input delete nggak valid bro.")
                pause()
                continue

            del_number = int(del_parts[1])
            del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_number), None)
            if not del_pkg:
                print("❌ Paket buat dihapus nggak ketemu bro.")
                pause()
                continue

            confirm = input(f"Yakin mau unsubscribe dari paket {del_number}. {del_pkg['name']}? (y/n): ").strip().lower()
            if confirm == 'y':
                print(f"🔄 Unsubscribing dari paket {del_pkg['name']}...")
                success = unsubscribe(
                    api_key,
                    tokens,
                    del_pkg["quota_code"],
                    del_pkg["product_subscription_type"],
                    del_pkg["product_domain"]
                )
                if success:
                    print("✅ Berhasil unsubscribe bro.")
                else:
                    print("💥 Gagal unsubscribe bro.")
            else:
                print("↩️ Unsubscribe dibatalin bro.")
            pause()

