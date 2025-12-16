from dotenv import load_dotenv

from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance, get_tiering_info
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.menus.sharing import show_balance_allotment_menu
from app.client.registration import dukcapil

WIDTH = 55


def safe_expired_date(ts):
    try:
        if ts:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        pass
    return "-"


def show_main_menu(profile):
    clear_screen()
    print("=" * WIDTH)
    expired_at_dt = safe_expired_date(profile.get("balance_expired_at"))
    print(f"Nomor: {profile.get('number')} | Type: {profile.get('subscription_type')}".center(WIDTH))
    print(f"Pulsa: Rp {profile.get('balance_remaining')} | Aktif sampai: {expired_at_dt}".center(WIDTH))
    print(f"{profile.get('point_info')}".center(WIDTH))
    print("=" * WIDTH)
    print("Menu:")
    print(" [1.] Login/Ganti akun 👤")
    print(" [2.] Lihat Paket Saya 📦")
    print(" [3.] Beli Paket 🔥 HOT 🔥")
    print(" [4.] Beli Paket 🔥 HOT-2 🔥")
    print(" [5.] Beli Paket Berdasarkan Option Code")
    print(" [6.] Beli Paket Berdasarkan Family Code")
    print(" [7.] Beli Semua Paket di Family Code (loop)")
    print(" [8.] Riwayat Transaksi 🧾")
    print(" [9.] Family Plan/Akrab Organizer 👨‍👩‍👧‍👦")
    print("[10.] Circle 🔄")
    print("[11.] Store Segments 🏬")
    print("[12.] Store Family List 📑")
    print("[13.] Store Packages 📦")
    print("[14.] Redeemables 🎁")
    print("[BA.] Balance Allotment (Transfer Pulsa) 💸")
    print(" [R.] Register 📝")
    print(" [N.] Notifikasi 🔔")
    print(" [V.] Validate msisdn ✅")
    #print(" [S.] Sentry Mode 🛡️")
    print("[00.] Bookmark Paket ⭐")
    print("[99.] Tutup aplikasi ❌")
    print("-------------------------------------------------------")


def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"]) or {}
            balance_remaining = balance.get("remaining", 0)
            balance_expired_at = balance.get("expired_at")

            point_info = "Points: N/A | Tier: N/A"
            if active_user.get("subscription_type") == "PREPAID":
                try:
                    tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"]) or {}
                    tier = tiering_data.get("tier", 0)
                    current_point = tiering_data.get("current_point", 0)
                    point_info = f"Points: {current_point} | Tier: {tier}"
                except Exception as e:
                    print(f"⚠️ Bro, gagal ambil info tiering: {e}")

            profile = {
                "number": active_user.get("number"),
                "subscriber_id": active_user.get("subscriber_id"),
                "subscription_type": active_user.get("subscription_type"),
                "balance_remaining": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = input("Pilih menu: ").strip()
            if choice.lower() == "t":
                pause("☕ Santai dulu bro, tekan Enter biar lanjut 🚀...")
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("⚠️ Nggak ada user yang dipilih bro.")
                continue
            elif choice == "2":
                fetch_my_packages()
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = input("Masukin option code (atau '99' buat batal): ").strip()
                if option_code == "99":
                    continue
                show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)
            elif choice == "6":
                family_code = input("Masukin family code (atau '99' buat batal): ").strip()
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "7":
                family_code = input("Masukin family code (atau '99' buat batal): ").strip()
                if family_code == "99":
                    continue
                try:
                    start_from_option = int(input("Mulai dari option nomor (default 1): ") or "1")
                except ValueError:
                    start_from_option = 1
                use_decoy = input("Pake decoy package? (y/n): ").lower() == 'y'
                pause_on_success = input("Pause tiap sukses beli? (y/n): ").lower() == 'y'
                try:
                    delay_seconds = int(input("Delay detik antar pembelian (0 = no delay): ") or "0")
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                is_enterprise = input("Enterprise store? (y/n): ").lower() == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                is_enterprise = input("Enterprise? (y/n): ").lower() == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "13":
                is_enterprise = input("Enterprise? (y/n): ").lower() == 'y'
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "14":
                is_enterprise = input("Enterprise? (y/n): ").lower() == 'y'
                show_redeemables_menu(is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                print("👋 Bye bye bro, aplikasi ditutup.")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = input("Masukin msisdn (628xxxx): ").strip()
                nik = input("Masukin NIK: ").strip()
                kk = input("Masukin KK: ").strip()
                try:
                    res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
                    print(json.dumps(res, indent=2))
                except Exception as e:
                    print(f"⚠️ Bro, gagal register: {e}")
                pause()
            elif choice.lower() == "ba":
                show_balance_allotment_menu()
            elif choice.lower() == "v":
                msisdn = input("Masukin msisdn buat validasi (628xxxx): ").strip()
                res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
                print(json.dumps(res, indent=2))
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice.lower() == "s":
                enter_sentry_mode()
            else:
                print("⚠️ Pilihan nggak valid bro, coba lagi ✌️")
                pause()
        else:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("⚠️ Belum login bro, nggak ada user aktif.")


if __name__ == "__main__":
    try:
        print("🔍 Lagi ngecek update dulu bro...")
        need_update = check_for_updates()
        if need_update:
            pause("⚠️ Ada update bro, cek dulu sebelum lanjut...")

        main()
    except KeyboardInterrupt:
        print("\n👋 Bye bye bro, aplikasi ditutup. Sampai jumpa lagi 🚀")
    except Exception as e:
        print(f"💥 Ups bro, ada error yang nggak kepikiran: {e}")
        pause("🚧 Tekan Enter biar lanjut, atau close aja bro...")
