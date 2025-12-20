import os, re, time, textwrap
from html.parser import HTMLParser

from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.padding import Padding
from rich import box

from app2.config.theme_config import get_theme, get_theme_style
import app2.menus.banner as banner

console = Console()

ascii_art = banner.load("https://d17e22l2uh4h4n.cloudfront.net/corpweb/pub-xlaxiata/2019-03/xl-logo.png", globals())



def clear_screenxx():
    """Clear screen and display banner with ASCII art."""
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        print("\n" * 100)

    if ascii_art:
        try:
            ascii_art.to_terminal(columns=55)
        except Exception:
            pass
    print_banner()


def clear_screenx():
    """Clear screen and display ASCII art banner only."""
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = r"""
            _____                    _____          
           /\    \                  /\    \         
          /::\____\                /::\    \        
         /::::|   |               /::::\    \       
        /:::::|   |              /::::::\    \      
       /::::::|   |             /:::/\:::\    \     
      /:::/|::|   |            /:::/__\:::\    \    
     /:::/ |::|   |           /::::\   \:::\    \   
    /:::/  |::|___|______    /::::::\   \:::\    \  
   /:::/   |::::::::\    \  /:::/\:::\   \:::\    \ 
  /:::/    |:::::::::\____\/:::/__\:::\   \:::\____\
  \::/    / ~~~~~/:::/    /\:::\   \:::\   \::/    /
   \/____/      /:::/    /  \:::\   \:::\   \/____/ 
               /:::/    /    \:::\   \:::\    \     
              /:::/    /      \:::\   \:::\____\    
             /:::/    /        \:::\   \::/    /    
            /:::/    /          \:::\   \/____/     
           /:::/    /            \:::\    \         
          /:::/    /              \:::\____\        
          \::/    /                \::/    /        
           \/____/                  \/____/ v8.10.0"""

    console.print(
        Padding(
            Align.center(ascii_art),
            (1, 0)
        ),
        style=get_theme_style("text_sub")
    )


def print_banner():
    """Print CLI banner with version information."""
    theme = get_theme()
    banner_text = Align.center(
        "[bold]myXL CLI v8.10.0 sunset[/]",
        vertical="middle"
    )
    console.print(Panel(
        banner_text,
        border_style=theme["border_primary"],
        style=theme["text_title"],
        padding=(1, 2),
        expand=True,
        box=box.DOUBLE
    ))


def mask_number(number: str) -> str:
    """Sensor 4 digit di tengah nomor dengan bintang."""
    num_str = str(number)
    if len(num_str) < 8:
        return num_str
    start = num_str[:4]
    end = num_str[-4:]
    return f"{start}{'*'*4}{end}"


def simple_number2():
    """Display active account number or information if none is active."""
    from app.service.auth import AuthInstance
    theme = get_theme()
    active_user = AuthInstance.get_active_user()

    if not active_user:
        text = f"[bold {theme['text_err']}]Tidak ada akun aktif.[/]"
    else:
        number = active_user.get("number", "-")
        text = f"[bold {theme['text_sub']}]Akun aktif: {number}[/]"

    console.print(Panel(
        Align.center(text),
        border_style=theme["border_primary"],
        padding=(0, 0),
        expand=True
    ))


def simple_number():
    """Tampilkan nomor akun aktif, atau info jika tidak ada."""
    from app.service.auth import AuthInstance
    theme = get_theme()
    active_user = AuthInstance.get_active_user()

    if not active_user:
        text = f"[bold {theme['text_err']}]Tidak ada akun aktif.[/]"
    else:
        number = active_user.get("number", "-")
        masked_number = mask_number(number)
        account_name = active_user.get("name", "")
        if account_name and account_name != "-":
            text = f"[bold {theme['text_title']}]Akun aktif: {masked_number} | {account_name}[/]"
        else:
            text = f"[bold {theme['text_title']}]Akun aktif: {masked_number}[/]"

    console.print(Panel(
        Align.center(text),
        border_style=theme["border_primary"],
        padding=(0, 0),
        expand=True
    ))


def clear_screen():
    """Clear screen and display ASCII art banner."""
    os.system('cls' if os.name == 'nt' else 'clear')
    ascii_art = r"""

__________             ___.                  
\______   \_____ ______\_ |__   ____ ___  ___    ▄   ▄
|    |  _/\__  \\_  __ \ __ \_/ __ \\  \/  / ▄█▄ █▀█▀█ ▄█▄
|    |   \ / __ \|  | \/ \_\ \  ___/ >    < ▀▀████▄█▄████▀▀
|______  /(____  /__|  |___  /\___  >__/\_ \     ▀█▀█▀
       \/      \/          \/     \/      \/"""

    version_text = f"[{get_theme_style('text_body')}]myXL CLI v8.10.0 sunset[/{get_theme_style('text_body')}]"
    
    content = f"{ascii_art}\n                  {version_text}"
    console.print(
        Padding(
            Align.center(content),
            (1, 0)
        ),
        style=get_theme_style("text_sub")
    )


def pause():
    """Pause execution until user presses Enter."""
    theme = get_theme()
    console.print(f"\n[bold {theme['text_sub']}]Tekan Enter untuk melanjutkan[/]")
    input()


class HTMLToText(HTMLParser):
    """Convert HTML content to plain text with optional bullet points."""
    def __init__(self, width=80, bullet="•"):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False
        self.bullet = bullet

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"{self.bullet} {text}")
            else:
                self.result.append(text)

    def get_text(self):
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))


def display_html(html_text, width=80):
    """Render HTML text into formatted plain text."""
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()


def format_quota_byte(quota_byte: int) -> str:
    """Format quota bytes into human-readable string (GB, MB, KB, B)."""
    GB = 1024**3
    MB = 1024**2
    KB = 1024
    if quota_byte >= GB:
        return f"{quota_byte / GB:.2f} GB"
    elif quota_byte >= MB:
        return f"{quota_byte / MB:.2f} MB"
    elif quota_byte >= KB:
        return f"{quota_byte / KB:.2f} KB"
    return f"{quota_byte} B"


def get_rupiah(value) -> str:
    """Format integer or string into Indonesian Rupiah currency format."""
    value_str = str(value).strip()
    value_str = re.sub(r"^Rp\s?", "", value_str)
    match = re.match(r"([\d,]+)(.*)", value_str)
    if not match:
        return value_str
    raw_number = match.group(1).replace(",", "")
    suffix = match.group(2).strip()
    try:
        number = int(raw_number)
    except ValueError:
        return value_str
    formatted_number = f"{number:,}".replace(",", ".")
    formatted = f"{formatted_number},-"
    return f"{formatted} {suffix}" if suffix else formatted


def nav_range(label: str, count: int) -> str:
    """Return formatted navigation range string."""
    if count <= 0:
        return f"{label} (tidak tersedia)"
    if count == 1:
        return f"{label} (1)"
    return f"{label} (1–{count})"


def live_loading(text: str, theme: dict):
    """Display live loading spinner with text."""
    return console.status(f"[{theme['text_body']}]{text}[/{theme['text_body']}]", spinner="dots")


def delay_inline(seconds: int):
    """Tampilkan countdown delay."""
    theme = get_theme()
    with Live(refresh_per_second=4) as live:
        for i in range(seconds, 0, -1):
            panel = Panel(
                f"{i} detik tersisa...",
                title="Menunggu",
                border_style=theme["border_info"]
            )
            live.update(panel)
            time.sleep(1)
        panel = Panel(
            "Delay selesai.",
            title="Selesai",
            border_style=theme["border_success"]
        )
        live.update(panel)
        time.sleep(0.5)


def print_panel(title, content, border_style=None):
    """Print a panel with title and content."""
    style = border_style or get_theme_style("border_info")
    console.print(Panel(content, title=title, title_align="left", border_style=style))


def print_success(title, content):
    """Print success message panel."""
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_success")))


def print_error(title, content):
    """Print error message panel."""
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_error")))


def print_warning(title, content):
    """Print warning message panel."""
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_warning")))


def print_title(text):
    """Print title panel with centered text."""
    console.print(
        Panel(
            Align.center(f"[bold {get_theme_style('text_title')}]{text}[/{get_theme_style('text_title')}]"),
            border_style=get_theme_style("border_primary"),
            padding=(0, 1),
            expand=True,
        )
    )


def print_key_value(label, value):
    """Print key-value pair with consistent styling."""
    console.print(f"[{get_theme_style('text_key')}]{label}:[/] [{get_theme_style('text_value')}]{value}[/{get_theme_style('text_value')}] ✔")


def print_info(label, value):
    """Print informational key-value pair."""
    console.print(f"[{get_theme_style('text_sub')}]{label}:[/{get_theme_style('text_sub')}] [{get_theme_style('text_body')}]{value}[/{get_theme_style('text_body')}]")


def print_menu(title, options, highlight=None):
    """Print menu options in a table format."""
    table = Table(title=title, box=box.SIMPLE, show_header=False)
    for key, label in options.items():
        style = get_theme_style("text_value")
        if highlight and key == highlight:
            style = get_theme_style("text_title")
        table.add_row(
            f"[{get_theme_style('text_key')}]{key}[/{get_theme_style('text_key')}]",
            f"[{style}]{label}[/{style}]",
        )
    console.print(table)
