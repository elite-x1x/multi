import io
import qrcode

from app2.config.imports import *
from app2.menus.util import clear_screen, pause, live_loading, simple_number

console = Console()


def generate_qr_ascii(data: str) -> str:
    """Generate ASCII representation of a QR code."""
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()


def show_info_menu():
    """Display donation and support information with QRIS code."""
    clear_screen()
    ensure_git()
    theme = get_theme()
    qris_url = (
        "00020101021126570011ID.DANA.WWW011893600915324993094502092499309450303UMI"
        "51440014ID.CO.QRIS.WWW0215ID10254398087220303UMI5204541153033605802ID5908BarbexID"
        "6004011361054646563047A81"
    )

    with live_loading("Menyiapkan QRIS...", theme):
        qr_code_ascii = generate_qr_ascii(qris_url)

    console.print(Panel(
        Align.center("Dukung Pengembangan myXL CLI", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
     ))
    simple_number()

    donate_info = Text()
    donate_info.append(
        "Butuh kode unlock untuk menambah akun lebih banyak? Hubungi Telegram (@barbex_id).\n\n",
        style=theme["text_body"]
    )
    donate_info.append(
        "Untuk mendukung pengembangan tool ini, Anda dapat memberikan donasi melalui metode berikut:\n\n",
        style=theme["text_body"]
    )
    donate_info.append("- Dana: 0831-1921-5545\n", style=theme["text_body"])
    donate_info.append("  A/N Joko S\n", style=theme["text_body"])
    donate_info.append("- QRIS tersedia di bawah.\n\n", style=theme["text_body"])
    donate_info.append("Terima kasih atas dukungan Anda.", style=theme["text_sub"])

    console.print(Panel(
        Align.left(donate_info),
        title=f"[{theme['text_title']}]Informasi Donasi[/]",
        border_style=theme["border_primary"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    console.print(Panel(
        Align.center(qr_code_ascii),
        title=f"[{theme['text_title']}]Scan QRIS[/]",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    pause()
