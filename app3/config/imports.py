# Standard library
import os
import re
import textwrap
from html.parser import HTMLParser

# Third-party (Rich)
from rich import box
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD
from rich.console import Console, Group
from rich.panel import Panel
from rich.padding import Padding
from rich.table import Table
from rich.text import Text

# Internal app - config
from app.config.cache import clear_cache, get_cache, set_cache
from app3.config.theme_config import get_theme, get_theme_style, get_all_presets, set_theme

# Internal app - client
from app3.client.engsel import (
    dash_segments,
    get_balance,
    get_family,
    get_package,
    get_package_details,
    get_quota,
    get_tiering_info,
)
from app3.client.famplan import validate_msisdn
from app3.client.registration import dukcapil

# Internal app - service
from app.service.auth import AuthInstance
from app.service.bookmark import BookmarkInstance
from app.service.decoy import DecoyInstance
from app.service.git import check_for_updates, ensure_git
from app.service.sentry import enter_sentry_mode

# Internal app - menus
from app3.menus.account import show_account_menu
from app3.menus.bookmark import show_bookmark_menu
from app3.menus.bundle import show_bundle_menu
from app3.menus.circle import show_circle_info
from app3.menus.family_grup import show_family_grup_menu
from app3.menus.famplan import show_family_info
from app3.menus.hot import show_hot_menu, show_hot_menu2
from app3.menus.info import show_info_menu
from app3.menus.notification import show_notification_menu
from app3.menus.package import (
    fetch_my_packages,
    get_packages_by_family,
    show_package_details,
)
from app3.menus.payment import show_transaction_history
from app3.menus.purchase import purchase_by_family, purchase_loop
from app3.menus.sfy import show_special_for_you_menu
from app3.menus.store.redemables import show_redeemables_menu
from app3.menus.store.search import show_family_list_menu, show_store_packages_menu
from app3.menus.store.segments import show_store_segments_menu
from app3.menus.theme import show_theme_menu
from app3.menus.util import (
    clear_screen,
    display_html,
    format_quota_byte,
    get_rupiah,
    live_loading,
    nav_range,
    pause,
    print_error,
    print_panel,
    print_success,
    print_warning,
    simple_number,
)

# Internal app - types
from app.type_dict import PaymentItem


# Inisialisasi console global
console = Console()

# __all__ untuk kontrol import *
__all__ = [
    # Rich
    "Align",
    "Group",
    "MINIMAL_DOUBLE_HEAD",
    "Padding",
    "Panel",
    "Table",
    "Text",
    "box",
    "console",

    # Config
    "get_theme",
    "get_theme_style",
    "get_cache",
    "set_cache",
    "clear_cache",
    "get_all_presets",
    "set_theme",

    # Client
    "dash_segments",
    "get_balance",
    "get_family",
    "get_package",
    "get_package_details",
    "get_quota",
    "get_tiering_info",
    "validate_msisdn",
    "dukcapil",

    # Service
    "AuthInstance",
    "BookmarkInstance",
    "DecoyInstance",
    "check_for_updates",
    "ensure_git",
    "enter_sentry_mode",

    # Menus
    "show_account_menu",
    "show_bookmark_menu",
    "show_bundle_menu",
    "show_circle_info",
    "show_family_grup_menu",
    "show_family_info",
    "show_hot_menu",
    "show_hot_menu2",
    "show_info_menu",
    "show_notification_menu",
    "fetch_my_packages",
    "get_packages_by_family",
    "show_package_details",
    "show_transaction_history",
    "purchase_by_family",
    "purchase_loop",
    "show_special_for_you_menu",
    "show_redeemables_menu",
    "show_family_list_menu",
    "show_store_packages_menu",
    "show_store_segments_menu",
    "show_theme_menu",

    # Util
    "clear_screen",
    "pause",
    "print_panel",
    "print_error",
    "print_warning",
    "print_success",
    "get_rupiah",
    "display_html",
    "simple_number",
    "format_quota_byte",
    "live_loading",
    "nav_range",

    # Types
    "PaymentItem",
]
