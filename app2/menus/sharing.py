import json

from app2.config.imports import *
from app.service.auth import AuthInstance
from app2.menus.util import pause, clear_screen, print_panel, live_loading, get_rupiah
from app2.client.engsel import get_balance
from app2.client.sharing import balance_allotment
from app2.client.ciam import get_auth_code
from rich.console import Console

console = Console()


def show_balance_allotment_menu():
    """Menu untuk melakukan pembagian saldo (balance sharing)."""
    theme = get_theme()
    active_user = AuthInstance.get_active_user()
    clear_screen()
    simple_number()
    ensure_git()

    balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])

    if not balance:
        print_panel("Kesalahan", "Gagal mengambil saldo.")
        pause()
        return "BACK"

    balance_remaining = balance.get("remaining", 0)
    console.print(Panel(
        Align.center(f"Balance Sharing | Rp {get_rupiah(balance_remaining)}", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))
    console.print(Panel(
        Align.center("Pastikan PIN transaksi sudah diatur di aplikasi MyXL.", vertical="middle"),
        border_style=theme["border_warning"],
        expand=True
    ))

    pin = console.input(f"[{theme['text_sub']}]Masukkan PIN 6 digit:[/{theme['text_sub']}] ").strip()
    if len(pin) != 6 or not pin.isdigit():
        print_panel("Kesalahan", "Format PIN tidak valid.")
        pause()
        return "BACK"

    stage_token = get_auth_code(
        active_user["tokens"],
        pin,
        active_user["number"]
    )
    if stage_token is None:
        print_panel("Kesalahan", "Stage token gagal diambil.")
        pause()
        return "BACK"

    receiver_msisdn = console.input(f"[{theme['text_sub']}]Masukkan nomor penerima (628xxx):[/{theme['text_sub']}] ").strip()
    amount_str = console.input(f"[{theme['text_sub']}]Masukkan nominal (contoh: 5000):[/{theme['text_sub']}] ").strip()

    try:
        amount = int(amount_str)
    except ValueError:
        print_panel("Kesalahan", "Nominal tidak valid.")
        pause()
        return "BACK"

    with live_loading("Mengirim saldo...", theme):
        res = balance_allotment(
            AuthInstance.api_key,
            active_user["tokens"],
            stage_token,
            receiver_msisdn,
            amount,
        )

    if res is None:
        print_panel("Kesalahan", "Balance allotment gagal.")
        pause()
        return "BACK"

    console.print(Panel(
        json.dumps(res, indent=2),
        title=f"[{theme['text_title']}]Hasil Transaksi[/]",
        border_style=theme["border_success"],
        expand=True
    ))
    pause()
    return res
