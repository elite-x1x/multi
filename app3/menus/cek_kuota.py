import requests
from app3.menus.util import print_panel, pause
from app3.config.imports import *


def cek_kuota(msisdn: str) -> str:
    """
    Mengecek kuota berdasarkan nomor XL (msisdn).
    Return string hasil mentah dari API.
    """
    api_url = f"https://apigw.kmsp-store.com/sidompul/v4/cek_kuota?msisdn={msisdn}&isJSON=true"
    headers = {
        'Authorization': 'Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw',
        'X-API-Key': '4352ff7d-f4e6-48c6-89dd-21c811621b1c',
        'X-App-Version': '3.0.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.get(api_url, headers=headers)
        print_panel("Informasi", f"Request URL: {api_url}")
        print_panel("Informasi", f"Response Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                hasil = data.get("data", {}).get("hasil", "")
                return hasil
            except ValueError:
                print_panel("Kesalahan", "Tidak dapat memproses respons JSON.")
                return "Error: Tidak dapat memproses respons JSON"
        else:
            print_panel("Kesalahan", f"Tidak dapat mengakses API. Status Code: {response.status_code}")
            return f"Error: Tidak dapat mengakses API, Status Code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        print_panel("Kesalahan", f"Terjadi error koneksi: {e}")
        return "Terjadi kesalahan. Silakan coba lagi!"

def format_result(result: str) -> str:
    """
    Memformat hasil kuota agar lebih mudah dibaca di CLI.
    """
    formatted = result.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    formatted = formatted.replace("📃 RESULT :", "📃 RESULT:")
    formatted = formatted.replace("🧧 Name :", "\n🧧 Name:")
    formatted = formatted.replace("🍂 Expired Date :", "\n🍂 Expired Date:")
    formatted = formatted.replace("🎨 Benefit :", "\n🎨 Benefit:")
    formatted = formatted.replace("🎁 Kuota :", "\n🎁 Kuota:")
    formatted = formatted.replace("🌲 Sisa Kuota :", "\n🌲 Sisa Kuota:")
    return formatted
