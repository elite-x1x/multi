import json
from datetime import datetime
from app2.client.store.segments import get_segments
from app2.menus.util import (
    clear_screen, pause, print_panel, simple_number, get_rupiah
)
from app.service.auth import AuthInstance
from app2.menus.package import show_package_details
from app2.config.imports import *

console = Console()


def show_store_segments_menu(is_enterprise: bool = False):
    """Menampilkan menu store segments yang tersedia."""
    theme = get_theme()
    in_store_segments_menu = True
    while in_store_segments_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        segments_res = get_segments(api_key, tokens, is_enterprise)
        if not segments_res:
            print_panel("Informasi", "Tidak ada store segments tersedia.")
            in_store_segments_menu = False
            continue
        
        segments = segments_res.get("data", {}).get("store_segments", [])
        clear_screen()
        ensure_git()
        
        console.print(Panel(
            Align.center("Store Segments", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()
        
        packages = {}
        for i, segment in enumerate(segments):
            name = segment.get("title", "N/A")
            banners = segment.get("banners", [])
            letter = chr(65 + i)  # Convert 0 -> A, 1 -> B, etc.
            
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("Kode", style=theme["text_key"], width=6)
            table.add_column("Family", style=theme["text_body"])
            table.add_column("Paket", style=theme["text_body"])
            table.add_column("Aktif", style=theme["text_date"])
            table.add_column("Harga", style=theme["text_money"], justify="right")
            
            if not banners:
                table.add_row("-", f"{name} (kosong)", "-", "-", "-")
            else:
                for j, banner in enumerate(banners):
                    title = banner.get("title", "N/A")
                    validity = banner.get("validity", "N/A")
                    family_name = banner.get("family_name", "N/A")
                    action_param = banner.get("action_param", "")
                    action_type = banner.get("action_type", "")
                    
                    # harga: original + discounted
                    original_price = banner.get("original_price", 0)
                    discounted_price = banner.get("discounted_price", 0)
                    if discounted_price and discounted_price > 0:
                        harga_str = f"{get_rupiah(original_price)} ➡ {get_rupiah(discounted_price)}"
                    else:
                        harga_str = get_rupiah(original_price)
                    
                    code = f"{letter}{j+1}"
                    packages[code.lower()] = {
                        "action_param": action_param,
                        "action_type": action_type
                    }
                    table.add_row(code, family_name, title, validity, harga_str)
            
            console.print(Panel(
                table,
                title=f"[{theme['text_title']}]Segment: {name}[/]",
                border_style=theme["border_info"],
                padding=(0, 0),
                expand=True
            ))
        
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))
        
        choice = console.input(f"[{theme['text_sub']}]Pilih banner (misal A1, B2):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            in_store_segments_menu = False
            continue
        
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            print_panel("Kesalahan", "Pilihan tidak valid.")
            pause()
            continue
        
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PDP":
            show_package_details(api_key, tokens, action_param, is_enterprise)
        else:
            print_panel("Informasi", f"Tidak ada aksi untuk tipe ini: {action_type}\nParam: {action_param}")
            pause()
