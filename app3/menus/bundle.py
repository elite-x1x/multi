from app3.config.imports import *
from app3.client.purchase.balance import settlement_balance
from app3.client.purchase.qris import show_qris_payment
from app3.client.purchase.ewallet import show_multipayment
from app3.menus.util import clear_screen, pause, print_panel, get_rupiah, simple_number
from app3.menus.package import get_packages_by_family
from app3.menus.family_grup import show_family_grup_menu
from app3.menus.bookmark import show_bookmark_menu
from app.type_dict import PaymentItem

console = Console()


def show_bundle_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    cart_items = []
    display_cart = []
    total_price = 0

    while True:
        clear_screen()
        ensure_git()
        console.print(Panel(
            Align.center("🛒 Keranjang Paket 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        if cart_items:
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("No", justify="right", style=theme["text_key"], width=4)
            table.add_column("Nama Paket", style=theme["text_body"])
            table.add_column("Harga", style=theme["text_money"], justify="right")

            for i, item in enumerate(display_cart, start=1):
                table.add_row(str(i), item["name"], get_rupiah(item["price"]))

            console.print(Panel(table, border_style=theme["border_info"], padding=(0, 1), expand=True))
            console.print(f"[{theme['text_body']}]Total Harga: Rp {get_rupiah(total_price)}[/]")
        else:
            print_panel("ℹ️ Santuy", "Keranjang lo masih kosong bro 😴")

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("1", "Tambah dari Bookmark 📌")
        nav.add_row("2", "Tambah dari Family Code Tersimpan 👨‍👩‍👧‍👦")
        nav.add_row("3", "Tambah dari Family Code Manual ✍️")
        if cart_items:
            nav.add_row("4", f"[{theme['text_err']}]🗑️ Hapus Item dari Keranjang[/]")
            nav.add_row("5", f"[{theme['text_warn']}]💳 Gaskeun ke Pembayaran[/]")
        nav.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")

        console.print(Panel(nav, border_style=theme["border_primary"], padding=(0, 0), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilihan lo bro:[/{theme['text_sub']}] ").strip()

        def add_to_cart(detail, name):
            nonlocal total_price
            option = detail["package_option"]
            cart_items.append(PaymentItem(
                item_code=option["package_option_code"],
                product_type="", item_price=option["price"],
                item_name=option["name"], tax=0,
                token_confirmation=detail["token_confirmation"]
            ))
            display_cart.append({"name": name, "price": option["price"]})
            total_price += option["price"]
            print_panel("✅ Mantap", f"Paket '{name}' udah masuk keranjang bro 🚀")
            pause()

        if choice == "1":
            result = show_bookmark_menu(return_package_detail=True)
            if isinstance(result, tuple):
                detail, name = result
                if detail:
                    add_to_cart(detail, name)

        elif choice == "2":
            result = show_family_grup_menu(return_package_detail=True)
            if result == "MAIN":
                break
            elif isinstance(result, tuple):
                detail, name = result
                if detail:
                    add_to_cart(detail, name)

        elif choice == "3":
            fc = console.input(f"[{theme['text_sub']}]Masukin Family Code bro:[/{theme['text_sub']}] ").strip()
            result = get_packages_by_family(fc, return_package_detail=True)
            if result == "MAIN":
                break
            elif isinstance(result, tuple):
                detail, name = result
                if detail:
                    add_to_cart(detail, name)

        elif choice == "4" and cart_items:
            idx = console.input(f"[{theme['text_sub']}]Nomor item yang mau dihapus:[/{theme['text_sub']}] ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(cart_items):
                i = int(idx) - 1
                removed = display_cart.pop(i)
                cart_items.pop(i)
                total_price -= removed["price"]
                print_panel("🗑️ Dihapus", f"Item '{removed['name']}' udah gue hapus bro ✌️")
                pause()
            else:
                print_panel("⚠️ Ups", "Nomor item nggak valid bro 🤯")
                pause()

        elif choice == "5" and cart_items:
            clear_screen()
            info_text = Text()
            info_text.append("💳 Detail Pembayaran:\n", style=theme["text_body"])
            for i, item in enumerate(display_cart, start=1):
                info_text.append(f"{i}. {item['name']} - Rp {get_rupiah(item['price'])}\n", style=theme["text_body"])
            info_text.append(f"\nTotal: Rp {get_rupiah(total_price)}", style=theme["text_money"])

            console.print(Panel(
                info_text,
                title=f"[{theme['text_title']}]Informasi Pembayaran 🤙[/]",
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))
            simple_number()

            while True:
                method_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
                method_table.add_column(justify="right", style=theme["text_key"], width=6)
                method_table.add_column(style=theme["text_body"])
                method_table.add_row("1", "💰 Balance")
                method_table.add_row("2", "💳 E-Wallet")
                method_table.add_row("3", "📱 QRIS")
                method_table.add_row("00", f"[{theme['text_sub']}]Balik ke menu sebelumnya[/]")

                console.print(Panel(
                    method_table,
                    title=f"[{theme['text_title']}]🔥 Pilih Metode Pembayaran[/]",
                    border_style=theme["border_primary"],
                    padding=(0, 1),
                    expand=True
                ))

                method = console.input(f"[{theme['text_sub']}]Mau pake metode apa bro:[/{theme['text_sub']}] ").strip()

                if method == "00":
                    break

                confirm = console.input(f"[{theme['text_sub']}]Gaskeun pake metode ini? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Santuy", "Pembayaran dibatalin bro ✌️")
                    pause()
                    continue

                if method == "1":
                    settlement_balance(api_key, tokens, cart_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]✅ Pembayaran kelar bro, tekan Enter...[/{theme['text_sub']}]")
                    break
                elif method == "2":
                    show_multipayment(api_key, tokens, cart_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]✅ Pembayaran kelar bro, tekan Enter...[/{theme['text_sub']}]")
                    break
                elif method == "3":
                    show_qris_payment(api_key, tokens, cart_items, "BUY_PACKAGE", True)
                    console.input(f"[{theme['text_sub']}]✅ Pembayaran kelar bro, tekan Enter...[/{theme['text_sub']}]")
                    break
                else:
                    print_panel("⚠️ Ups", "Metode nggak valid bro 🤯")
                    pause()

        elif choice == "00":
            break

        else:
            print_panel("⚠️ Ups", "Pilihan lo ngaco bro 🚨")
            pause()
