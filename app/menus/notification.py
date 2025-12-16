from datetime import datetime, timedelta
from app.menus.util import clear_screen, pause
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance

WIDTH = 55


def format_timestamp(ts):
    if ts is None or ts == "":
        return "-"
    try:
        if isinstance(ts, (int, float)):
            dt = datetime.utcfromtimestamp(ts) + timedelta(hours=7)
            return dt.strftime("%d %B %Y | %H:%M WIB")
        elif isinstance(ts, str) and ts.isdigit():
            dt = datetime.utcfromtimestamp(int(ts)) + timedelta(hours=7)
            return dt.strftime("%d %B %Y | %H:%M WIB")
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) + timedelta(hours=7)
            return dt.strftime("%d %B %Y | %H:%M WIB")
    except Exception:
        return "-"
    return "-"


def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        print("🔍 Lagi ambil notifikasi bro...")

        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()

        notifications_res = dashboard_segments(api_key, tokens)
        if not notifications_res:
            print("❌ Nggak ada notifikasi bro.")
            pause()
            return

        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            print("⚠️ Belum ada notifikasi bro.")
            pause()
            return

        print("=" * WIDTH)
        print("🔔 Daftar Notifikasi".center(WIDTH))
        print("=" * WIDTH)
        unread_count = 0
        for idx, notification in enumerate(notifications):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "-")
            formatted_time = format_timestamp(notification.get("timestamp"))

            status = "✅ READ" if is_read else "🔔 UNREAD"
            if not is_read:
                unread_count += 1

            print(f"[{idx + 1}.] Status: {status}")
            print(f" 📅 Waktu: {formatted_time}")
            print(f" 📝 Pesan: {full_message}")
            print("-" * WIDTH)

        print(f"📊 Total: {len(notifications)} | Unread: {unread_count}")
        print("=" * WIDTH)
        print(" [0.] Refresh 🔄")
        print(" [1.] Tandai semua Unread jadi Read ✅")
        print("[00.] Balik ke Menu Utama")
        print("=" * WIDTH)

        choice = input("Pilih opsi: ").strip()
        if choice == "0":
            print("🔄 Refreshing notifikasi bro...")
            continue
        elif choice == "1":
            for notification in notifications:
                if notification.get("is_read", False):
                    continue
                notification_id = notification.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notification_id)
                if detail:
                    print(f"✅ Notifikasi {notification_id} ditandai sebagai READ bro.")
            pause()
        elif choice == "00":
            in_notification_menu = False
        else:
            print("⚠️ Input nggak valid bro. Coba lagi ✌️")
            pause()
