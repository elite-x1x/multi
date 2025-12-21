from app3.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app3.menus.util import print_panel, pause
from app3.config.imports import *
from app3.client.engsel import get_package
from app3.menus.package import settlement_bounty

def auto_redeem_bonus(is_enterprise: bool = False, pause_on_success: bool = False):
    """
    Bot loop: otomatis masuk ke menu 16 → A1, lalu redeem semua paket bonus dengan opsi B.
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

        # ambil detail paket
        package = get_package(api_key, tokens, action_param)
        if not package:
            print_panel("⚠️ Ups", f"Gagal ambil detail paket {code}")
            continue

        option = package.get("package_option", {})
        variant = package.get("package_detail_variant", {})
        price = option.get("price", 0)
        token_confirmation = package.get("token_confirmation", "")
        ts_to_sign = package.get("timestamp", "")
        option_name = option.get("name", "")
        variant_name = variant.get("name", "")

        # langsung eksekusi settlement_bounty (opsi B)
        settlement_bounty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=action_param,
            price=price,
            item_name=variant_name or option_name
        )

        #print_panel("✅ Mantap", f"Bonus {name} berhasil diambil 🎁")

        if pause_on_success:
            pause()
