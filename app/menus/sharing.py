import json

from app.service.auth import AuthInstance
from app.menus.util import pause, clear_screen
from app.client.engsel import get_balance
from app.client.sharing import balance_allotment
from app.client.ciam import get_auth_code

WIDTH = 55


def show_balance_allotment_menu():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        print("⚠️ Belum login bro, nggak bisa transfer pulsa.")
        pause()
        return

    balance = get_balance(AuthInstance.api_key, active_user["tokens"].get("id_token")) or {}
    clear_screen()
    balance_remaining = balance.get("remaining", 0)

    print("=" * WIDTH)
    print(f"💸 BALANCE SHARING | Rp {balance_remaining}".center(WIDTH))
    print("-" * WIDTH)
    print("Pastikan PIN transaksi udah di-set di MyXL 🔐".center(WIDTH))
    print("=" * WIDTH)

    pin = input("Masukin PIN 6 digit: ").strip()
    if len(pin) != 6 or not pin.isdigit():
        print("❌ Format PIN salah bro, batalin dulu.")
        pause()
        return

    try:
        stage_token = get_auth_code(
            active_user["tokens"],
            pin,
            active_user["number"]
        )
    except Exception as e:
        print(f"💥 Gagal ambil stage token bro: {e}")
        pause()
        return

    if not stage_token:
        print("❌ Stage token nggak valid bro, batalin transfer.")
        pause()
        return

    receiver_msisdn = input("Masukin nomor penerima (628xxxx): ").strip()
    amount_str = input("Masukin nominal pulsa (contoh 5000): ").strip()

    try:
        amount = int(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        print("❌ Nominal nggak valid bro, batalin transfer.")
        pause()
        return

    try:
        res = balance_allotment(
            AuthInstance.api_key,
            active_user["tokens"],
            stage_token,
            receiver_msisdn,
            amount,
        )
    except Exception as e:
        print(f"💥 Gagal allotment bro: {e}")
        pause()
        return

    if not res:
        print("❌ Transfer pulsa gagal bro.")
        pause()
        return

    print("✅ Transfer berhasil bro, detail response:")
    print(json.dumps(res, indent=2))
    pause()
    return res
