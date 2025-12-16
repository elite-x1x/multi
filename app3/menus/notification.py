from app3.config.imports import *
from app3.menus.util import clear_screen, pause, print_panel, simple_number, live_loading
from app3.client.engsel import get_notification_detail, dashboard_segments

console = Console()


def show_notification_menu():
    theme = get_theme()
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        ensure_git()
        console.print(Panel(
            Align.center("📢 Notifikasi 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()

        notifications_res = dashboard_segments(api_key, tokens)

        if not notifications_res:
            print_panel("ℹ️ Info", "Waduh, sepi banget bro... nggak ada notif masuk 😴")
            pause()
            return

        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            print_panel("ℹ️ Info", "Kosong cuy, notif lo lagi liburan 🌴")
            pause()
            return

        jumlah_belum_dibaca = 0
        for idx, notification in enumerate(notifications, start=1):
            sudah_dibaca = notification.get("is_read", False)
            pesan_lengkap = notification.get("full_message", "")
            pesan_singkat = notification.get("brief_message", "")
            waktu = notification.get("timestamp", "")

            status = "Udah Dibaca 😎" if sudah_dibaca else "Belum Dibaca 🚨"
            if not sudah_dibaca:
                jumlah_belum_dibaca += 1

            notif_text = Text()
            notif_text.append(f"🔔 Notif {idx}\n", style="bold")
            notif_text.append("Status: ", style=theme["border_info"])
            notif_text.append(f"{status}\n", style=theme["text_err"] if status.startswith("Belum") else theme["text_ok"])
            notif_text.append("Pesan Singkat: ", style=theme["border_info"])
            notif_text.append(f"{pesan_singkat}\n", style=theme["text_body"])
            notif_text.append("Waktu: ", style=theme["border_info"])
            notif_text.append(f"{waktu}\n", style=theme["border_warning"])
            notif_text.append("Pesan Lengkap:\n", style=theme["border_info"])
            notif_text.append(f"{pesan_lengkap}\n", style=theme["text_body"])

            console.print(Panel(
                notif_text,
                border_style=theme["border_info"],
                padding=(0, 1),
                expand=True
            ))

        console.print(
            f"[{theme['text_title']}]Total: {len(notifications)}[/] | "
            f"[{theme['text_err']}]Belum Dibaca: {jumlah_belum_dibaca}[/]"
        )

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "Gas! Tandai Semua Notif 🚀")
        nav_table.add_row("2", "Tandai Satu Notif Aja 🎯")
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut Balik ke Menu Utama 🏠[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        pilihan = console.input(f"[{theme['text_sub']}]Mau pilih yang mana bro? 👉 [/{theme['text_sub']}] ").strip()
        if pilihan == "1":
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print_panel("✅ Mantap", f"Notif ID {notification_id} udah gue tandain dibaca bro 🤟")
            pause()

        elif pilihan == "2":
            nomor = console.input(f"[{theme['text_sub']}]Masukin nomor notif cuy:[/{theme['text_sub']}] ").strip()
            if not nomor.isdigit():
                print_panel("❌ Ups", "Nomor nggak valid bro, jangan ngaco 🤪")
                pause()
                continue
            nomor = int(nomor)
            selected = next((n for i, n in enumerate(notifications, start=1) if i == nomor), None)
            if not selected:
                print_panel("❌ Ups", "Nomor notif nggak ketemu, jangan halu 🫠")
                pause()
                continue
            if selected.get("is_read", False):
                print_panel("ℹ️ Info", "Notif ini udah dibaca sebelumnya, santuy aja 😌")
                pause()
                continue
            notification_id = selected.get("notification_id")
            detail = get_notification_detail(api_key, tokens, notification_id)
            if detail:
                print_panel("✅ Mantap", f"Notif ID {notification_id} udah gue tandain dibaca bro 🤟")
            pause()

        elif pilihan == "00":
            in_notification_menu = False

        else:
            print_panel("⚠️ Bro", "Pilihan lo ngaco, coba lagi deh 🤯")
            pause()
