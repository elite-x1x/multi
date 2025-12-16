import io
import qrcode

from app3.config.imports import *
from app3.menus.util import clear_screen, pause, live_loading, simple_number

console = Console()


def generate_qr_ascii(data: str) -> str:
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()


def show_info_menu():
    clear_screen()
    ensure_git()
    theme = get_theme()
    qris_url = (
        "00020101021126570011ID.DANA.WWW011893600915324993094502092499309450303UMI"
        "51440014ID.CO.QRIS.WWW0215ID10254398087220303UMI5204541153033605802ID5908BarbexID"
        "6004011361054646563047A81"
    )

    with live_loading("🔄 Lagi siapin QRIS bro...", theme):
        qr_code_ascii = generate_qr_ascii(qris_url)

    console.print(Panel(
        Align.center("🔥 Dukung Pengembangan myXL CLI 🤙", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
     ))
    simple_number()

    donate_info = Text()
    donate_info.append(
        "Butuh Kode Unlock buat nambah akun lebih banyak? Gas chat gue di Telegram (@barbex_id), tebus seikhlasnya aja bro 😁\n\n",
        style=theme["text_body"]
    )
    donate_info.append(
        "Kalau mau support pengembangan tool ini, bisa donasi pake metode di bawah:\n\n",
        style=theme["text_body"]
    )
    donate_info.append("- 💸 Dana: 0831-1921-5545\n", style=theme["text_body"])
    donate_info.append("  A/N Joko S\n", style=theme["text_body"])
    donate_info.append("- 📱 QRIS juga tersedia di bawah bro\n\n", style=theme["text_body"])
    donate_info.append("🙏 Makasih banyak atas dukungan lo cuy! 🚀", style=theme["text_sub"])

    console.print(Panel(
        Align.left(donate_info),
        title=f"[{theme['text_title']}]💰 Donasi Seikhlasnya Bro[/]",
        border_style=theme["border_primary"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    console.print(Panel(
        Align.center(qr_code_ascii),
        title=f"[{theme['text_title']}]📱 Scan QRIS Tongkrongan[/]",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    pause()
