from app2.client.engsel import get_family
from app2.menus.package import get_packages_by_family
from app2.menus.util import clear_screen, pause, print_panel, simple_number
from app.service.auth import AuthInstance
from app2.config.imports import *
from rich.console import Console

import re, os, json, time

console = Console()
FAMILY_FILE = "families.json"
FAMILY_INPUT_TXT = "families-input.txt"
DELAY_SECONDS = 1  # ubah ke 0 kalau mau tanpa jeda

def save_families(families):
    with open(FAMILY_FILE, "w", encoding="utf-8") as f:
        json.dump(families, f, indent=2)

def load_families():
    if os.path.exists(FAMILY_FILE):
        with open(FAMILY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_family_input_txt():
    if os.path.exists(FAMILY_INPUT_TXT):
        with open(FAMILY_INPUT_TXT, "r", encoding="utf-8") as f:
            return f.readlines()
    return []

def _fetch_family(api_key, tokens, code, subs_type: str):
    data = get_family(api_key, tokens, code, False, subs_type)
    if data and "package_family" in data and data["package_family"].get("name"):
        return {
            "family_name": data["package_family"].get("name", "N/A"),
            "family_code": code,
            "is_enterprise": False,
        }

    data2 = get_family(api_key, tokens, code, True, subs_type)
    if data2 and "package_family" in data2 and data2["package_family"].get("name"):
        return {
            "family_name": data2["package_family"].get("name", "N/A"),
            "family_code": code,
            "is_enterprise": True,
        }

    return None

def process_family_input_txt(subs_type: str = "PREPAID"):
    raw_lines = load_family_input_txt()
    if not raw_lines:
        print_panel("Kesalahan", "File families-input.txt tidak ditemukan atau kosong.")
        pause()
        return []

    uuid_pattern = re.compile(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )

    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    old_families = load_families()
    families = {f["family_code"]: f for f in old_families}
    processed_codes = set(families.keys())

    pending = []
    for line in raw_lines:
        matches = uuid_pattern.findall(line)
        for code in matches:
            code = code.lower()
            if code in processed_codes:
                continue
            pending.append(code)

    total = len(pending)
    for idx, code in enumerate(pending, start=1):
        console.print(f"[cyan]Memproses {idx}/{total}: {code}[/cyan]")
        try:
            result = _fetch_family(api_key, tokens, code, subs_type)
            if result:
                families[code] = result
                processed_codes.add(code)
            else:
                console.print(f"[yellow]Family {code} tidak ditemukan (non-enterprise & enterprise), dilewati.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error memproses {code}: {e}[/red]")
        time.sleep(DELAY_SECONDS)

    final_data = [
        fam for fam in families.values()
        if fam.get("family_name") and not str(fam.get("family_name")).startswith("Error")
    ]

    final_data.sort(key=lambda x: x["family_name"].lower())

    save_families(final_data)
    return final_data

def show_family_table(families, theme):
    families = sorted(families, key=lambda f: f["family_name"].lower())

    table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("No", justify="right", style=theme["text_key"], width=4)
    table.add_column("Nama Family", style=theme["text_body"])
    table.add_column("Kode", style=theme["border_warning"])
    table.add_column("Enterprise", style=theme["text_sub"], width=10)

    for i, fam in enumerate(families, start=1):
        ent = "Ya" if fam.get("is_enterprise") else "Tidak"
        table.add_row(str(i), fam["family_name"], fam["family_code"], ent)
    console.print(Panel(table, border_style=theme["border_info"], padding=(0, 0), expand=True))

def show_family_input_menu(subs_type: str = "PREPAID"):
    theme = get_theme()
    in_menu = True
    while in_menu:
        clear_screen()
        console.print(Panel(
            Align.center("Tools Family Code", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        families = load_families()
        if families:
            show_family_table(families, theme)
        else:
            print_panel("Informasi", "Belum ada data family. Tekan L untuk load dari TXT.")

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("", "Pilih nomor family untuk buka paket")
        nav.add_row("L", "Load families-input.txt → merge + scan otomatis")
        nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        console.print(Panel(nav, border_style=theme["border_primary"], expand=True))

        choice = console.input(f"[{theme['text_sub']}]Input pilihan:[/{theme['text_sub']}] ").strip()
        if choice.isdigit() and families and 1 <= int(choice) <= len(families):
            selected = families[int(choice)-1]
            console.print(Panel(f"Mencari paket untuk family: {selected['family_name']}", border_style=theme["border_info"]))
            get_packages_by_family(selected["family_code"], is_enterprise=selected["is_enterprise"])
        elif choice.upper() == "L":
            process_family_input_txt(subs_type)
        elif choice == "00":
            in_menu = False
        else:
            print_panel("Kesalahan", "Input tidak valid.")
            pause()
