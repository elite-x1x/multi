from dotenv import load_dotenv

load_dotenv()

import sys
import time
import select
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests
import json

from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance, send_api_request, get_package_details
from app.client.purchase.balance import settlement_balance
from app.service.auth import AuthInstance
from app.menus.account import show_account_menu

# --- Helper functions copied from app/menus/bot.py ---

def _ping_ok() -> bool:
    """
    Cek koneksi internet sederhana.
    """
    urls = [
        "https://www.google.com/generate_204",
        "https://me.mashu.lol/pg-hot2.json",
    ]
    for u in urls:
        try:
            r = requests.get(u, timeout=4)
            if r.status_code in (200, 204):
                return True
        except Exception:
            continue
    return False

def _user_typed_exit() -> bool:
    """
    Non-blocking: cek apakah user mengetik '99' + Enter.
    """
    try:
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            s = sys.stdin.readline().strip()
            return s == "99"
    except Exception:
        return False
    return False

def _await_connection(step_seconds: int = 3) -> bool:
    """
    Tunggu sampai koneksi kembali normal.
    Mengembalikan False jika user mengetik '99' untuk keluar saat menunggu.
    """
    print("\n[!] Koneksi internet terputus. Menunggu koneksi kembali... (ketik 99 lalu Enter untuk keluar)")
    while not _ping_ok():
        for s in range(step_seconds, 0, -1):
            if _user_typed_exit():
                return False
            print(f" Menunggu koneksi : {s} detik", end="\r")
            time.sleep(1)
        print(" " * 60, end="\r")  # bersihkan baris
    return True

def _refresh_tokens(strict: bool = False) -> Optional[dict]:
    """
    Selalu panggil untuk mengambil/refresh token terbaru dari AuthInstance.
    """
    try:
        tokens = AuthInstance.get_active_tokens()
    except Exception:
        tokens = None
    if not tokens and strict:
        print("[!] Sesi login tidak tersedia / habis. Silakan login ulang.")
        pause()
        return None
    return tokens or {}

def _format_bytes_to_human(val: int) -> (float, str):
    try:
        v = float(val)
    except Exception:
        return (0.0, "B")
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while v >= 1024.0 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    return (v, units[i])

def _fmt_quota(remaining: int, total: int) -> str:
    rv, ru = _format_bytes_to_human(remaining)
    tv, tu = _format_bytes_to_human(total)
    if ru == tu:
        return f"{rv:.2f} {ru} / {tv:.2f} {tu}"
    if ru in ("MB", "GB") and tu in ("MB", "GB"):
        r_in_gb = remaining / (1024 ** 3)
        t_in_gb = total / (1024 ** 3)
        return f"{r_in_gb:.2f} GB / {t_in_gb:.2f} GB"
    return f"{rv:.2f} {ru} / {tv:.2f} {tu}"

def _fetch_quota_details() -> Optional[List[Dict[str, Any]]]:
    api_key = AuthInstance.api_key
    tokens = _refresh_tokens(strict=True)
    if not tokens:
        return None
    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }
    try:
        res = send_api_request(api_key, path, payload, id_token, "POST")
    except Exception as e:
        print(f"Gagal mengambil data paket saya: {e}")
        return None
    if not isinstance(res, dict) or res.get("status") != "SUCCESS":
        print("Gagal mengambil data paket saya (quota-details).")
        return None
    return res["data"].get("quotas", [])

def _extract_main_benefit(quota_item: Dict[str, Any]) -> (int, int, str):
    benefits = quota_item.get("benefits") or quota_item.get("quota_benefits") or []
    def score(b: Dict[str, Any]) -> int:
        name = (b.get("name") or "").lower()
        dtype = (b.get("data_type") or b.get("dataType") or "").upper()
        cat = (b.get("category") or "").upper()
        s = 0
        if "utama" in name or "main" in name or "regular" in name:
            s += 3
        if dtype == "DATA":
            s += 2
        if "DATA_MAIN" in cat or "MAIN" in cat:
            s += 2
        try:
            s += int(b.get("total", 0)) // (1024 ** 2)
        except Exception:
            pass
        return s
    if benefits:
        sel = max(benefits, key=score)
        remaining = int(sel.get("remaining") or 0)
        total = int(sel.get("total") or 0)
        bname = sel.get("name") or "Kuota Utama"
        return remaining, total, bname
    remaining = int(quota_item.get("remaining") or 0)
    total = int(quota_item.get("total") or 0)
    return remaining, total, "Kuota"

def _build_hot2_num2_payment_items() -> Optional[dict]:
    """
    Ambil paket Hot-2 nomor 2 (index 1).
    """
    api_key = AuthInstance.api_key
    tokens = _refresh_tokens(strict=True)
    if not tokens:
        return None
    url = "https://me.mashu.lol/pg-hot2.json"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        hot_packages = resp.json()
    except Exception as e:
        print(f"Gagal mengambil data hot 2: {e}")
        return None
    if not isinstance(hot_packages, list) or len(hot_packages) < 2:
        print("Data hot 2 tidak valid atau tidak ada paket index 2.")
        return None
    selected_package = hot_packages[1]  # nomor 2
    payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
    packages = selected_package.get("packages", [])
    if not packages:
        print("Paket di hot 2 nomor 2 tidak memiliki items.")
        return None

    def _extract_item(pd: dict) -> dict:
        opt = pd.get("package_option") or {}
        item_code = opt.get("code") or opt.get("package_option_code") or pd.get("package_option_code") or pd.get("option_code") or ""
        item_name = opt.get("name") or pd.get("name") or "Unknown"
        item_price = opt.get("price") or pd.get("price") or 0
        token_confirmation = pd.get("token_confirmation") or opt.get("token_confirmation") or ""
        return dict(
            item_code=item_code,
            product_type="",
            item_price=item_price,
            item_name=item_name,
            tax=0,
            token_confirmation=token_confirmation,
        )

    items: List[dict] = []
    for package in packages:
        tokens = _refresh_tokens(strict=True)
        if not tokens:
            return None
        package_detail = get_package_details(
            api_key,
            tokens,
            package.get("family_code"),
            package.get("variant_code"),
            package.get("order"),
            package.get("is_enterprise"),
        )
        if not package_detail:
            print(f"Gagal mengambil detail paket untuk {package.get('family_code')}.")
            return None
        items.append(_extract_item(package_detail))

    return {
        "items": items,
        "payment_for": payment_for,
    }

# --- Main Automated Bot Logic ---

def run_automated_bot():
    """
    Main function for the automated bot.
    """
    # 1. Select Account
    selected_user_number = show_account_menu()
    if selected_user_number:
        AuthInstance.set_active_user(selected_user_number)
        print(f"Pengguna {selected_user_number} dipilih.")
    else:
        print("Tidak ada pengguna yang dipilih atau gagal memuat pengguna. Keluar.")
        return

    print("Memulai bot pembayaran otomatis...")
    time.sleep(2)

    # 3. Start the timer loop
    seconds = 1
    while True:
        if not _ping_ok():
            if not _await_connection(3):
                return
        
        tokens = _refresh_tokens(strict=True)
        if not tokens:
            return

        clear_screen()
        print("=======================================================")
        print(" BOT PEMBAYARAN OTOMATIS ")
        print("=======================================================")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Waktu: {now}")
        print("Status: Aktif, menunggu timer untuk melakukan pembayaran.")
        print("-------------------------------------------------------")

        print("\nKetik '99' dan tekan Enter untuk keluar.")
        for s in range(seconds, 0, -1):
            if _user_typed_exit():
                print("\nKeluar dari bot...")
                return
            print(f" Pembelian dalam {s} detik...", end="\r")
            time.sleep(1)
        print("\nMelakukan pembayaran...")

        # 4. Perform payment
        tokens = _refresh_tokens(strict=True) # Refresh again just before payment
        if not tokens:
            return

        try:
            cfg = _build_hot2_num2_payment_items()
            if cfg and cfg.get("items"):
                print("Membeli paket...")
                settlement_balance(
                    AuthInstance.api_key,
                    tokens,
                    cfg["items"],
                    cfg.get("payment_for", "BUY_PACKAGE"),
                    False,
                    ""
                )
                print("Pembelian selesai. Menunggu siklus berikutnya...")
            else:
                print("Gagal menyiapkan item pembayaran. Melewatkan siklus ini.")
        except Exception as e:
            print(f"Terjadi error saat persiapan atau pembayaran: {e}")
            print("Bot akan melanjutkan ke siklus berikutnya.")
        
        time.sleep(2) # Brief pause after payment


if __name__ == "__main__":
    try:
        run_automated_bot()
    except KeyboardInterrupt:
        print("\nExiting the application.")
    except Exception as e:
        print(f"An error occurred: {e}")
