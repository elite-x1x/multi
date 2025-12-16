from app3.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app3.menus.util import clear_screen, pause, print_panel, simple_number
from app3.menus.package import show_package_details, get_packages_by_family
from app3.config.imports import *
from datetime import datetime

console = Console()


def show_redeemables_menu(is_enterprise: bool = False):
    theme = get_theme()
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
        if not redeemables_res:
            print_panel("ℹ️ Info", "Sepi cuy, nggak ada redeemables masuk 😴")
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        clear_screen()
        ensure_git()
        
        console.print(Panel(
            Align.center("🎁 Redeemables 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1,2),
            expand=True
        ))
        simple_number()
        
        packages = {}
        for i, category in enumerate(categories):
            category_name = category.get("category_name", "N/A")
            category_code = category.get("category_code", "N/A")
            redeemables = category.get("redeemables", [])
            
            letter = chr(65 + i)
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("Kode", style=theme["text_key"], width=6)
            table.add_column("Nama Barang", style=theme["text_body"])
            table.add_column("Berlaku", style=theme["text_date"])
            table.add_column("Tipe", style=theme["text_body"])
            
            if not redeemables:
                table.add_row("-", f"{category_name} (kosong bro)", "-", "-")
            else:
                for j, redeemable in enumerate(redeemables):
                    name = redeemable.get("name", "N/A")
                    valid_until = redeemable.get("valid_until", 0)
                    valid_until_date = datetime.fromtimestamp(valid_until).strftime("%Y-%m-%d")
                    action_param = redeemable.get("action_param", "")
                    action_type = redeemable.get("action_type", "")
                    
                    code = f"{letter}{j+1}"
                    packages[code.lower()] = {
                        "action_param": action_param,
                        "action_type": action_type
                    }
                    table.add_row(code, name, valid_until_date, action_type)
            
            console.print(Panel(
                table,
                title=f"[{theme['text_title']}]📂 Kategori: {category_name}[/] (Kode: {category_code})",
                border_style=theme["border_info"],
                padding=(0, 0),
                expand=True
            ))
        
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))
        
        choice = console.input(f"[{theme['text_sub']}]Pilih redeemable (misal A1, B2): 👉 [/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_redeemables_menu = False
            continue
        
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            print_panel("❌ Ups", "Pilihan lo ngaco bro 🤯")
            pause()
            continue
        
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "")
        elif action_type == "PDP":
            show_package_details(api_key, tokens, action_param, is_enterprise)
        else:
            print_panel("ℹ️ Info", f"Belum ada aksi buat tipe ini bro: {action_type}\nParam: {action_param}")
            pause()
