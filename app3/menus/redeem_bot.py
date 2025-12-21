from app3.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app3.menus.package import show_package_details, get_packages_by_family
from app3.menus.util import print_panel, pause
from app3.config.imports import *

def auto_redeem_bonus(is_enterprise: bool = False, pause_on_success: bool = False):
    """
    Bot loop: otomatis masuk ke menu 16 → A1, lalu redeem semua paket dengan pembayaran B (bonus).
    """
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    redeemables_res = get_redeemables(api_key, tokens, is_enterprise)
    if not redeemables_res:
        print_panel("ℹ️ Info", "Nggak ada redeemables bro 😴")
        return

    categories = redeemables_res.get("data", {}).get("categories", [])
    if not categories:
        print_panel("ℹ️ Info", "Kategori kosong 🚨")
        return

    # ambil kategori pertama (A)
    category = categories[0]
    redeemables = category.get("redeemables", [])
    if not redeemables:
        print_panel("ℹ️ Info", "Kategori A1 kosong 🚨")
        return

    for idx, redeemable in enumerate(redeemables, start=1):
        code = f"A{idx}"
        name = redeemable.get("name", "N/A")
        action_param = redeemable.get("action_param", "")
        action_type = redeemable.get("action_type", "")

        print_panel("➡️ Redeem", f"{code} - {name} (pakai bonus B)")

        # langsung paksa opsi B
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "B")
        elif action_type == "PDP":
            # show_package_details biasanya minta input, kita override ke B
            show_package_details(api_key, tokens, action_param, is_enterprise)
            # langsung trigger settlement_bounty di dalam show_package_details
            # bisa juga bikin wrapper khusus kalau mau full silent
        else:
            print_panel("ℹ️ Info", f"Tipe belum didukung: {action_type}")

        if pause_on_success:
            pause()
