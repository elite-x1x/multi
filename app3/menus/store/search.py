from app3.client.store.search import get_family_list, get_store_packages
from app3.menus.package import get_packages_by_family, show_package_details
from app3.menus.util import clear_screen, pause, print_panel, simple_number, get_rupiah, live_loading
from app.service.auth import AuthInstance
from app3.config.imports import *

console = Console()


def show_family_list_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    theme = get_theme()
    in_family_list_menu = True
    while in_family_list_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        family_list_res = get_family_list(api_key, tokens, subs_type, is_enterprise)
        if not family_list_res:
            print_panel("ℹ️ Info", "Sepi cuy, nggak ada family list 😴")
            in_family_list_menu = False
            continue
        
        family_list = family_list_res.get("data", {}).get("results", [])
        clear_screen()
        ensure_git()
        
        console.print(Panel(
            Align.center("👨‍👩‍👧‍👦 Family List 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1,2),
            expand=True
        ))
        simple_number()
        
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Nama Family", style=theme["text_body"])
        table.add_column("Kode", style=theme["border_warning"])
        
        for i, family in enumerate(family_list, start=1):
            table.add_row(str(i), family.get("label","N/A"), family.get("id","N/A"))
        
        console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))
        
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))
        
        choice = console.input(f"[{theme['text_sub']}]Pilih family (nomor): 👉 [/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_family_list_menu = False
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(family_list):
            selected_family = family_list[int(choice)-1]
            family_code = selected_family.get("id","")
            family_name = selected_family.get("label","N/A")
            console.print(Panel(f"🔍 Lagi nyari paket buat family: {family_name} 🚀", border_style=theme["border_info"]))
            get_packages_by_family(family_code)
        else:
            print_panel("❌ Ups", "Pilihan lo ngaco bro 🤯")
            pause()


def show_store_packages_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    theme = get_theme()
    in_store_packages_menu = True
    while in_store_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        store_packages_res = get_store_packages(api_key, tokens, subs_type, is_enterprise)
        if not store_packages_res:
            print_panel("ℹ️ Info", "Sepi cuy, nggak ada paket di store 😴")
            in_store_packages_menu = False
            continue
        
        store_packages = store_packages_res.get("data", {}).get("results_price_only", [])
        clear_screen()
        ensure_git()
        
        console.print(Panel(
            Align.center("🛒 Store Packages 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1,2),
            expand=True
        ))
        simple_number()

        with live_loading("🔄 Lagi nyusun tabel paket bro...", theme):
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("No", justify="right", style=theme["text_key"], width=4)
            table.add_column("Paket", style=theme["text_body"])
            table.add_column("Family", style=theme["text_body"])
            table.add_column("Aktif", style=theme["text_date"])
            table.add_column("Harga", style=theme["text_money"], justify="right")
            
            packages = {}
            for i, package in enumerate(store_packages, start=1):
                title = package.get("title","N/A")
                original_price = package.get("original_price",0)
                discounted_price = package.get("discounted_price",0)
                validity = package.get("validity","N/A")
                family_name = package.get("family_name","N/A")
                action_type = package.get("action_type","")
                action_param = package.get("action_param","")
                
                packages[str(i)] = {"action_type": action_type, "action_param": action_param}
                
                if discounted_price and discounted_price > 0:
                    harga_str = f"{get_rupiah(original_price)} ➡️ {get_rupiah(discounted_price)}"
                else:
                    harga_str = get_rupiah(original_price)
                
                table.add_row(str(i), title, family_name, validity, harga_str)
        
        console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))
        
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))
        
        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor): 👉 [/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_store_packages_menu = False
            continue
        elif choice in packages:
            selected = packages[choice]
            if selected["action_type"] == "PDP":
                show_package_details(api_key, tokens, selected["action_param"], is_enterprise)
            else:
                print_panel("ℹ️ Info", f"Belum ada aksi buat tipe ini bro: {selected['action_type']}\nParam: {selected['action_param']}")
                pause()
        else:
            print_panel("❌ Ups", "Pilihan lo ngaco bro 🤯")
            pause()
