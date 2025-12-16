from datetime import datetime, timedelta
from app.client.engsel import get_transaction_history
from app.menus.util import clear_screen, pause

WIDTH = 55


def show_transaction_history(api_key, tokens):
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        print("=" * WIDTH)
        print("📜 Riwayat Transaksi".center(WIDTH))
        print("=" * WIDTH)

        history = []
        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            print(f"💥 Gagal ambil riwayat transaksi bro: {e}")
            history = []

        if not history:
            print("❌ Belum ada riwayat transaksi bro.")
            #pause()
        else:
            for idx, transaction in enumerate(history, start=1):
                transaction_timestamp = transaction.get("timestamp", 0)
                try:
                    dt = datetime.utcfromtimestamp(transaction_timestamp) + timedelta(hours=7)
                    formatted_time = dt.strftime("%d %B %Y | %H:%M WIB")
                except Exception:
                    formatted_time = "-"

                price_val = transaction.get("price", 0)
                try:
                    formatted_price = f"Rp{int(price_val):,}".replace(",", ".")
                except Exception:
                    formatted_price = str(price_val)

                print(f"[{idx}.] {transaction.get('title','-')} - {formatted_price}")
                print(f"  📅 Tanggal: {formatted_time}")
                print(f"  💳 Metode Pembayaran: {transaction.get('payment_method_label','-')}")
                print(f"  📦 Status Transaksi: {transaction.get('status','-')}")
                print(f"  💰 Status Pembayaran: {transaction.get('payment_status','-')}")
                print("-" * WIDTH)

        print(" [0.] Refresh 🔄")
        print("[00.] Balik ke Menu Utama")
        print("-" * WIDTH)
        choice = input("Pilih opsi: ").strip()

        if choice == "0":
            print("🔄 Refreshing transaksi bro...")
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            print("⚠️ Opsi nggak valid bro. Coba lagi ✌️")
            pause()
