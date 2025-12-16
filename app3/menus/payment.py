from datetime import datetime, timedelta

from app3.client.engsel import get_transaction_history
from app3.config.imports import *
from app3.menus.util import clear_screen, pause, print_panel, simple_number

console = Console()


def show_transaction_history(api_key, tokens):
    theme = get_theme()
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        ensure_git()
        console.print(Panel(
            Align.center("📄 Riwayat Transaksi 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            print_panel("⚠️ Ups", f"Gagal ngambil riwayat transaksi bro: {e} 🤯")
            history = []

        if not history:
            print_panel("ℹ️ Santuy", "Sepi cuy, belum ada riwayat transaksi 😴")
        else:
            for idx, transaction in enumerate(history, start=1):
                ts = transaction.get("timestamp", 0)
                dt = datetime.fromtimestamp(ts) - timedelta(hours=7)
                formatted_time = dt.strftime("%d %B %Y | %H:%M WIB")

                t = Table(box=MINIMAL_DOUBLE_HEAD, expand=True, padding=(0, 0))
                t.add_column("Label", justify="left", style=theme["text_body"], width=18)
                t.add_column("Detail", justify="right", style=theme["text_body"])
                t.add_row("📝 Judul", transaction.get("title", "-"))
                t.add_row("💸 Harga", f"Rp {transaction.get('price', '-')}")
                t.add_row("📅 Tanggal", formatted_time)
                t.add_row("💳 Metode", transaction.get("payment_method_label", "-"))
                t.add_row("📦 Status Transaksi", transaction.get("status", "-"))
                t.add_row("✅ Status Pembayaran", transaction.get("payment_status", "-"))

                console.print(Panel(t, title=f"🧾 Transaksi #{idx}", border_style=theme["border_info"], expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(justify="left", style=theme["text_body"])
        nav_table.add_row("0", "Refresh 🔄 ")
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut balik ke Menu Utama 🏠[/]")

        console.print(Panel(nav_table, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan lo bro:[/{theme['text_sub']}] ").strip()
        if choice == "0":
            continue
        elif choice == "00":
            return
        else:
            print_panel("⚠️ Ups", "Opsi lo ngaco bro, coba lagi 🚨")
            pause()
