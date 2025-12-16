import json

from app3.config.imports import *
from app.service.auth import AuthInstance
from app3.menus.util import pause, clear_screen, print_panel, live_loading, get_rupiah
from app3.client.engsel import get_balance
from app3.client.sharing import balance_allotment
from app3.client.ciam import get_auth_code
from rich.console import Console

console = Console()

def show_balance_allotment_menu():
    theme = get_theme()
    active_user = AuthInstance.get_active_user()
    clear_screen()
    simple_number()
    ensure_git()

    #with live_loading("🔄 Lagi cek saldo bro...", theme):
    balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])

    if not balance:
        print_panel("⚠️ Ups", "Gagal ambil saldo bro 🚨")
        pause()
        return "BACK"

    balance_remaining = balance.get("remaining", 0)
    console.print(Panel(
        Align.center(f"💰 Balance Sharing | Rp {get_rupiah(balance_remaining)}", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))
    console.print(Panel(
        Align.center("Pastikan PIN transaksi udah di-set di MyXL bro 🔑", vertical="middle"),
        border_style=theme["border_warning"],
        expand=True
    ))

    pin = console.input(f"[{theme['text_sub']}]👉 Masukin PIN 6 digit:[/{theme['text_sub']}] ").strip()
    if len(pin) != 6 or not pin.isdigit():
        print_panel("⚠️ Ups", "Format PIN ngaco bro 🚨")
        pause()
        return "BACK"

    stage_token = get_auth_code(
        active_user["tokens"],
        pin,
        active_user["number"]
    )
    if stage_token is None:
        print_panel("⚠️ Ups", "Stage token gagal diambil bro 🚨")
        pause()
        return "BACK"

    receiver_msisdn = console.input(f"[{theme['text_sub']}]👉 Masukin nomor penerima (628xxx):[/{theme['text_sub']}] ").strip()
    amount_str = console.input(f"[{theme['text_sub']}]👉 Masukin nominal (cth: 5000):[/{theme['text_sub']}] ").strip()

    try:
        amount = int(amount_str)
    except ValueError:
        print_panel("⚠️ Ups", "Nominal ngaco bro 🚨")
        pause()
        return "BACK"

    with live_loading("🔄 Lagi kirim saldo bro...", theme):
        res = balance_allotment(
            AuthInstance.api_key,
            active_user["tokens"],
            stage_token,
            receiver_msisdn,
            amount,
        )

    if res is None:
        print_panel("⚠️ Ups", "Balance allotment gagal bro 🚨")
        pause()
        return "BACK"

    console.print(Panel(
        json.dumps(res, indent=2),
        title=f"[{theme['text_title']}]📜 Hasil Transaksi[/]",
        border_style=theme["border_success"],
        expand=True
    ))
    pause()
    return res
