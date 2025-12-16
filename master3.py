from dotenv import load_dotenv
load_dotenv()

import sys, json, random
from datetime import datetime
from app3.config.imports import *
from app3.menus.util import clear_screenx
from app3.menus.sharing import show_balance_allotment_menu


def show_main_menu(profile: dict, display_quota: str, segments: dict):
    clear_screenx()
    theme = get_theme()

    expired_at_ts = profile.get("balance_expired_at")
    expired_at_dt = datetime.fromtimestamp(expired_at_ts).strftime("%Y-%m-%d %H:%M:%S") if expired_at_ts else "-"
    pulsa_str = get_rupiah(profile.get("balance", 0))

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=get_theme_style("border_info"))
    info_table.add_column(justify="left", style=get_theme_style("text_body"))

    info_table.add_row(" Nomor", f": 📞 [bold {theme['text_body']}]{profile['number']}[/]")
    info_table.add_row(" Type", f": 🧾 [{theme['text_body']}]{profile['subscription_type']} ({profile['subscriber_id']})[/]")
    info_table.add_row(" Pulsa", f": 💰 Rp [{theme['text_money']}]{pulsa_str}[/]")
    info_table.add_row(" Kuota", f": 📊 [{theme['text_date']}]{display_quota}[/]")
    info_table.add_row(" Tiering", f": 🏅 [{theme['text_date']}]{profile['point_info']}[/]")
    info_table.add_row(" Masa Aktif", f": ⏳ [{theme['text_date']}]{expired_at_dt}[/]")

    console.print(
        Panel(
            info_table,
            title=f"[{get_theme_style('text_title')}][ Informasi Akun ][/]",
            title_align="center",
            border_style=get_theme_style("border_info"),
            padding=(1, 2),
            expand=True,
        )
    )

    special_packages = segments.get("special_packages", [])
    if special_packages:
        best = random.choice(special_packages)
        name = best.get("name", "-")
        diskon_percent = best.get("diskon_percent", 0)
        diskon_price = best.get("diskon_price", 0)
        original_price = best.get("original_price", 0)
        emoji_diskon = "💸" if diskon_percent >= 50 else ""
        emoji_kuota = "🔥" if best.get("kuota_gb", 0) >= 100 else ""

        special_text = (
            f"[bold {theme['text_title']}]🔥🔥🔥 Paket Special Buat Lo! 🔥🔥🔥[/{theme['text_title']}]\n\n"
            f"[{theme['text_body']}]{emoji_kuota} {name}[/{theme['text_body']}]\n"
            f"Diskon {diskon_percent}% {emoji_diskon} "
            f"Rp[{theme['text_err']}][strike]{get_rupiah(original_price)}[/strike][/{theme['text_err']}] ➡️ "
            f"Rp[{theme['text_money']}]{get_rupiah(diskon_price)}[/{theme['text_money']}]"
        )

        console.print(
            Panel(
                Align.center(special_text),
                border_style=theme["border_warning"],
                padding=(0, 2),
                width=console.size.width,
            )
        )
        console.print(Align.center(f"[{theme['text_sub']}]Pilih [Y] buat lihat semua paket special[/{theme['text_sub']}]"))

    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=get_theme_style("text_key"), width=6)
    menu_table.add_column("Aksi", style=get_theme_style("text_body"))

    menu_table.add_row("1", "🔐 Login / Ganti akun")
    menu_table.add_row("2", "📑 Lihat paket aktif")
    menu_table.add_row("3", "📜 Riwayat Transaksi")
    menu_table.add_row("4", "🔥 Beli paket Hot promo")
    menu_table.add_row("5", "🔥 Beli paket Hot promo-2")
    menu_table.add_row("6", "💴 Beli paket via Option Code")
    menu_table.add_row("7", "💵 Beli paket via Family Code")
    menu_table.add_row("8", "🔁 Borong semua paket di Family Code")
    menu_table.add_row("9", "🔂 Auto Loop target Paket by Family")
    menu_table.add_row("", "")
    menu_table.add_row("[D]", "🎭 Bikin bundle paket ala decoy")
    menu_table.add_row("[F]", "💾 Save/Kelola Family Code lo")
    menu_table.add_row("[B]", "📌 Bookmark paket favorit")
    menu_table.add_row("[C]", f"[{theme['text_body']}]🧹 Bersihin cache akun[/]")
    menu_table.add_row("[M]", f"[{theme['text_body']}]☕ Lanjut ke menu berikutnya...[/]")
    menu_table.add_row("", "")
    menu_table.add_row("66", f"[{theme['border_warning']}]📢 Info kode unlock akun[/]")
    menu_table.add_row("69", f"[{theme['text_sub']}]🎨 Ganti tema CLI biar kece[/]")
    menu_table.add_row("99", f"[{theme['text_err']}]⛔ Cabut / Tutup aplikasi[/]")

    console.print(
        Panel(
            menu_table,
            title=f"[{get_theme_style('text_title')}]✨ Menu Utama ✨[/]",
            title_align="center",
            border_style=get_theme_style("border_primary"),
            padding=(0, 1),
            expand=True,
        )
    )


def show_main_menu2(active_user: dict, profile: dict):
    theme = get_theme()

    if not active_user or "tokens" not in active_user:
        print_panel("⚠️ Ups", "User belum aktif bro, login dulu 🚨")
        pause()
        return

    while True:
        clear_screenx()

        console.print(Panel(
            Align.center("☕ Halaman Menu-2", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        menu_table.add_column("Kode", justify="right", style=theme["text_key"], width=6)
        menu_table.add_column("Aksi", style=theme["text_body"])

        menu_table.add_row("1", "🔐 Login / Ganti akun")
        menu_table.add_row("11", "🤝 Akrab Squad Organizer")
        menu_table.add_row("12", "👥 Circle Nongkrong")
        menu_table.add_row("13", "🏬 Segmen Store (lapak)")
        menu_table.add_row("14", "📂 Family List Paket")
        menu_table.add_row("15", "📦 Paket Store")
        menu_table.add_row("16", "🎁 Redeem Reward/Bonus")
        menu_table.add_row("", "")
        menu_table.add_row("[TF]", "💸 Transfer Pulsa")
        menu_table.add_row("[N]", "🔔 Cek Notifikasi")
        menu_table.add_row("[R]", "📝 Registrasi MSISDN")
        menu_table.add_row("[V]", "✅ Validasi Nomor (MSISDN)")
        menu_table.add_row("", "")
        menu_table.add_row("00", f"[{theme['text_sub']}]🏠 Balik ke menu utama[/]")
        menu_table.add_row("99", f"[{theme['text_err']}]⛔ Cabut / Tutup aplikasi[/]")

        console.print(Panel(
            menu_table,
            title=f"[{theme['text_title']}]🧾 Menu-2[/]",
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]👉 Pilih menu bro:[/{theme['text_sub']}] ").strip()
        if choice == "1":
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
                #print_panel("✅ Mantap", f"Akun aktif diganti ke {selected_user_number}")
            else:
                print_panel("⚠️ Ups", "Nggak ada user terpilih bro 🚨")
            continue
        elif choice == "11":
            show_family_info(AuthInstance.api_key, active_user["tokens"])
        elif choice == "12":
            show_circle_info(AuthInstance.api_key, active_user["tokens"])
        elif choice == "13":
            is_enterprise = console.input(f"[{theme['text_sub']}]🏬 Enterprise store? (y/n):[/{theme['text_sub']}] ").lower() == "y"
            show_store_segments_menu(is_enterprise)
        elif choice == "14":
            is_enterprise = console.input(f"[{theme['text_sub']}]📂 Enterprise? (y/n):[/{theme['text_sub']}] ").lower() == "y"
            show_family_list_menu(profile["subscription_type"], is_enterprise)
        elif choice == "15":
            is_enterprise = console.input(f"[{theme['text_sub']}]📦 Enterprise? (y/n):[/{theme['text_sub']}] ").lower() == "y"
            show_store_packages_menu(profile["subscription_type"], is_enterprise)
        elif choice == "16":
            is_enterprise = console.input(f"[{theme['text_sub']}]🎁 Enterprise? (y/n):[/{theme['text_sub']}] ").lower() == "y"
            show_redeemables_menu(is_enterprise)
        elif choice.lower() == "tf":
            show_balance_allotment_menu()
        elif choice.lower() == "n":
            show_notification_menu()
        elif choice.lower() == "r":
            msisdn = console.input(f"[{theme['text_sub']}]📝 Masukin msisdn (628xxxx):[/{theme['text_sub']}] ")
            nik = console.input("Masukin NIK: ")
            kk = console.input("Masukin KK: ")
            res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
            print_panel("📑 Hasil Registrasi", json.dumps(res, indent=2))
            pause()
        elif choice.lower() == "v":
            msisdn = console.input(f"[{theme['text_sub']}]✅ Masukin msisdn buat validasi (628xxxx):[/{theme['text_sub']}] ")
            res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
            print_panel("📑 Hasil Validasi", json.dumps(res, indent=2))
            pause()
        elif choice == "00":
            with live_loading("🔄 Balik ke menu utama...", theme):
                pass
            return
        elif choice == "99":
            print_panel("👋 Sampai jumpa bro!", "Aplikasi ditutup dengan aman.")
            sys.exit(0)
        else:
            print_panel("⚠️ Ups", "Pilihan nggak valid bro 🚨")
            pause()


def main():
    ensure_git()
    while True:
        theme = get_theme()
        active_user = AuthInstance.get_active_user()
        if active_user is not None:
            account_id = active_user["number"]

            # Balance cache per akun (TTL 90 detik)
            balance = get_cache(account_id, "balance", ttl=90)
            if not balance:
                balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
                set_cache(account_id, "balance", balance)

            # Quota cache per akun (TTL 60 detik)
            quota = get_cache(account_id, "quota", ttl=70)
            if not quota:
                quota = get_quota(AuthInstance.api_key, active_user["tokens"]["id_token"]) or {}
                set_cache(account_id, "quota", quota)

            # Segments cache per akun (TTL 300 detik, file-based)
            segments = get_cache(account_id, "segments", ttl=290, use_file=True)
            if not segments:
                segments = dash_segments(
                    AuthInstance.api_key,
                    active_user["tokens"]["id_token"],
                    active_user["tokens"]["access_token"]
                ) or {}
                set_cache(account_id, "segments", segments, use_file=True)

            remaining = quota.get("remaining", 0)
            total = quota.get("total", 0)
            has_unlimited = quota.get("has_unlimited", False)
            if total > 0 or has_unlimited:
                display_quota = f"{remaining/1e9:.2f} / {total/1e9:.2f} GB" + (" (Unlimited)" if has_unlimited else "")
            else:
                display_quota = "-"

            point_info = "Points: N/A | Tier: N/A"
            if active_user["subscription_type"] == "PREPAID":
                # Tiering cache per akun (TTL 240 detik)
                tiering_data = get_cache(account_id, "tiering", ttl=250)
                if not tiering_data:
                    tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                    set_cache(account_id, "tiering", tiering_data)
                point_info = f"Points: {tiering_data.get('current_point',0)} | Tier: {tiering_data.get('tier',0)}"

            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance.get("remaining"),
                "balance_expired_at": balance.get("expired_at"),
                "point_info": point_info,
            }

            show_main_menu(profile, display_quota, segments)

            choice = console.input(f"[{theme['text_sub']}]👉 Pilih menu bro:[/{theme['text_sub']}] ").strip()

            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                    #print_panel("✅ Mantap", f"Akun aktif diganti ke {selected_user_number}")
                else:
                    print_panel("⚠️ Ups", "Nggak ada user terpilih bro 🚨")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "4":
                show_hot_menu()
            elif choice == "5":
                show_hot_menu2()
            elif choice == "6":
                option_code = console.input(f"[{theme['text_sub']}]🔎 Masukin option code bro:[/{theme['text_sub']}] ")
                if option_code == "99":
                    continue
                show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)
            elif choice == "7":
                family_code = console.input(f"[{theme['text_sub']}]🔎 Masukin family code bro:[/{theme['text_sub']}] ")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "8":
                family_code = console.input(f"[{theme['text_sub']}]🔎 Masukin family code bro:[/{theme['text_sub']}] ")
                if family_code == "99":
                    continue
                start_from_option = console.input(f"[{theme['text_sub']}]Mulai dari option number (default 1):[/{theme['text_sub']}] ")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1
                use_decoy = console.input(f"[{theme['text_sub']}]Gunakan decoy package? (y/n):[/{theme['text_sub']}] ").lower() == "y"
                pause_on_success = console.input(f"[{theme['text_sub']}]Pause tiap sukses? (y/n):[/{theme['text_sub']}] ").lower() == "y"
                delay_seconds = console.input(f"[{theme['text_sub']}]Delay antar pembelian (0 = tanpa delay):[/{theme['text_sub']}] ")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)
            elif choice == "9":
                family_code = console.input(f"[{theme['text_sub']}]Masukin family code bro:[/{theme['text_sub']}] ")
                try:
                    order = int(console.input(f"[{theme['text_sub']}]Masukin order number (default 1):[/{theme['text_sub']}] ") or 1)
                except ValueError:
                    order = 1
                try:
                    delay = int(console.input(f"[{theme['text_sub']}]Masukin delay (detik) (default 0):[/{theme['text_sub']}] ") or 0)
                except ValueError:
                    delay = 0
                pause_on_success = console.input(f"[{theme['text_sub']}]Aktifin mode pause? (y/n):[/{theme['text_sub']}] ").lower() == 'y'
                while True:
                    should_continue = purchase_loop(
                        family_code=family_code,
                        order=order,
                        use_decoy=True,
                        delay=delay,
                        pause_on_success=pause_on_success
                    )
                    if not should_continue:
                        break
                continue
            elif choice.lower() == "d":
                show_bundle_menu()
            elif choice.lower() == "f":
                show_family_grup_menu()
            elif choice.lower() == "b":
                show_bookmark_menu()
            elif choice.lower() == "m":
                show_main_menu2(active_user, profile)
            elif choice.lower() == "c":
                clear_cache(account_id)
                print_panel("✅ Mantap", f"Cache akun {account_id} udah dibersihin 🚀")
                pause()
            elif choice == "66":
                show_info_menu()
            elif choice == "69":
                show_theme_menu()
            elif choice == "99":
                print_panel("👋 Sampai jumpa bro!", "Aplikasi ditutup dengan aman.")
                sys.exit(0)
            elif choice.lower() == "y":
                show_special_for_you_menu(active_user["tokens"])
            elif choice.lower() == "s":
                enter_sentry_mode()
            else:
                print_panel("⚠️ Ups", "Pilihan nggak valid bro 🚨")
                pause()
        else:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
                #print_panel("✅ Mantap", f"Akun aktif diganti ke {selected_user_number}")
            else:
                print_panel("⚠️ Ups", "Nggak ada user terpilih bro 🚨")

if __name__ == "__main__":
    try:
        with live_loading("🔄 Checking for updates...", get_theme()):
            need_update = check_for_updates()
        # Jika ingin paksa update, aktifkan blok ini:
        # if need_update:
        #     print_warning("⬆️", "Versi baru tersedia, silakan update sebelum melanjutkan.")
        #     pause()
        #     sys.exit(0)
        main()
    except KeyboardInterrupt:
        print_error("👋 Keluar", "Aplikasi dihentikan oleh pengguna.")
