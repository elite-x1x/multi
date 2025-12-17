import requests, time
from random import randint

from app3.config.imports import *
from app3.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app3.menus.util import (
    clear_screen,
    pause,
    print_panel,
    get_rupiah,
    display_html,
    simple_number,
    delay_inline,
    format_quota_byte
)

from app3.client.purchase.redeem import settlement_bounty


console = Console()

bonus_bookmarks = [
    {
        "family_name": "Bonus Bebas Puas",
        "family_code": "7e5eb288-58a0-44d0-8002-b66bad210f21",
        "variant_name": "Bonus Bebas Puas",
        "option_name": "Kuota Youtube & Tiktok 3.13GB",
        "order": 200
    },
    {
        "family_name": "Bonus Bebas Puas",
        "family_code": "7e5eb288-58a0-44d0-8002-b66bad210f21",
        "variant_name": "Bonus Bebas Puas",
        "option_name": "Kuota Utama 1.25GB",
        "order": 201
    },
    {
        "family_name": "Bonus Bebas Puas",
        "family_code": "7e5eb288-58a0-44d0-8002-b66bad210f21",
        "variant_name": "Bonus Bebas Puas",
        "option_name": "Kuota Malam 3.75GB",
        "order": 199
    }
]

def redeem_looping(loop_count: int, pause_on_success=True):
    theme = get_theme()
    api_key = AuthInstance.api_key

    for i in range(loop_count):
        tokens = AuthInstance.get_active_tokens() or {}

        if i > 0:
            clear_cache()

        console.rule()
        console.print(f"[{theme['text_title']}]🔁 Redeem Looping ke-{i+1}/{loop_count}[/]")

        successful = []
        failed = []

        for bm in bonus_bookmarks:
            family_code = bm["family_code"]
            order = bm["order"]
            option_name = bm["option_name"]

            console.print(f"🎯 Claim bonus: {bm['variant_name']} - {option_name}")

            try:
                family_data = get_family(api_key, tokens, family_code)
                if not family_data:
                    failed.append(option_name)
                    print_panel("❌ Gagal", f"Ga bisa ambil data family buat {option_name} 😅")
                    continue

                target_variant = next(
                    (v for v in family_data["package_variants"] if v["name"] == bm["variant_name"]),
                    None
                )
                if not target_variant:
                    failed.append(option_name)
                    print_panel("⚠️ Error", f"Variant ga ketemu buat {option_name} 🤔")
                    continue

                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    target_variant["package_variant_code"],
                    order,
                    None,
                    None,
                )

                if not target_package_detail or "package_option" not in target_package_detail:
                    failed.append(option_name)
                    print_panel("⚠️ Error", f"Detail paket ga ada buat {option_name} 📦")
                    continue

                res = settlement_bounty(
                    api_key=api_key,
                    tokens=tokens,
                    token_confirmation=target_package_detail.get("token_confirmation", ""),
                    ts_to_sign=target_package_detail.get("timestamp", ""),
                    payment_target=target_package_detail["package_option"]["package_option_code"],
                    price=target_package_detail["package_option"]["price"],
                    item_name=target_package_detail["package_option"]["name"],
                )

                if res and res.get("status", "") == "SUCCESS":
                    successful.append(option_name)
                    print_panel("✅ Mantap", f"Redeem sukses: {option_name} 🎉")
                    if pause_on_success:
                        pause()
                else:
                    msg = res.get("message", "Ga jelas alasannya") if isinstance(res, dict) else "Error"
                    failed.append(option_name)
                    print_panel("❌ Gagal", f"Redeem gagal: {msg} 💥")

            except Exception as e:
                failed.append(option_name)
                print_panel("💥 Error", f"Redeem {option_name} kena masalah: {e}")

        console.rule()
        summary_text = f"📊 Selesai looping {i+1}/{loop_count}\n" \
                       f"✅ Berhasil: {len(successful)}\n" \
                       f"❌ Gagal: {len(failed)}"
        console.print(Panel(summary_text, border_style=theme["border_info"]))
        if successful:
            console.print("🎉 Daftar sukses:")
            for s in successful:
                console.print(f"   - {s}")
        if failed:
            console.print("💔 Daftar gagal:")
            for f in failed:
                console.print(f"   - {f}")

        if i < loop_count - 1:
            console.print(f"[{theme['text_sub']}]☕ Tunggu 11 menit sebelum looping berikutnya...[/]")
            delay_inline(660)


def purchase_loop(
    family_code: str,
    order: int,
    use_decoy: bool,
    delay: int,
    pause_on_success: bool = False,
):
    theme = get_theme()
    ensure_git()
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Peringatan", f"❌ Gagal ambil data family buat kode: {family_code} 😅")
        pause()
        return False

    target_variant = None
    target_option = None
    for variant in family_data["package_variants"]:
        for option in variant["package_options"]:
            if option["order"] == order:
                target_variant = variant
                target_option = option
                break
        if target_option:
            break

    if not target_option or not target_variant:
        print_panel("⚠️ Peringatan", f"Option order {order} ga ketemu di family {family_code} 🤔")
        pause()
        return False

    option_name = target_option["name"]
    option_price = target_option["price"]
    variant_code = target_variant["package_variant_code"]

    console.rule()
    console.print(f"[{theme['text_title']}]🛒 Proses pembelian: {target_variant['name']} - {order}. {option_name} - Rp{option_price}[/]")

    decoy_package_detail = None
    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
            pause()
            return False

    try:
        target_package_detail = get_package_details(
            api_key,
            tokens,
            family_code,
            variant_code,
            order,
            None,
            None,
        )
    except Exception as e:
        print_panel("💥 Kesalahan", f"Error pas ambil detail paket: {e}")
        delay_inline(delay)
        return True

    payment_items = [
        PaymentItem(
            item_code=target_package_detail["package_option"]["package_option_code"],
            product_type="",
            item_price=target_package_detail["package_option"]["price"],
            item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
            tax=0,
            token_confirmation=target_package_detail["token_confirmation"],
        )
    ]

    if use_decoy and decoy_package_detail:
        payment_items.append(
            PaymentItem(
                item_code=decoy_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {decoy_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=decoy_package_detail["token_confirmation"],
            )
        )

    overwrite_amount = target_package_detail["package_option"]["price"]
    if use_decoy and decoy_package_detail:
        overwrite_amount += decoy_package_detail["package_option"]["price"]

    try:
        res = settlement_balance(
            api_key,
            tokens,
            payment_items,
            "BUY_PACKAGE",
            False,
            overwrite_amount,
        )

        if res and res.get("status", "") != "SUCCESS":
            error_msg = res.get("message", "Unknown error")
            if "Bizz-err.Amount.Total" in error_msg:
                error_msg_arr = error_msg.split("=")
                valid_amount = int(error_msg_arr[1].strip())
                print_panel("ℹ️ Info", f"💡 Total amount disesuaikan jadi: {valid_amount}")
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "BUY_PACKAGE",
                    False,
                    valid_amount,
                )

        if res and res.get("status", "") == "SUCCESS":
            print_panel("✅ Sukses", f"Pembelian berhasil 🎉: {option_name}")
            if pause_on_success:
                choice = console.input("👉 Lanjut lagi bro? (y/n): ").strip().lower()
                if choice == 'n':
                    return False

    except Exception as e:
        print_panel("💥 Kesalahan", f"Error pas bikin order: {e}")

    if delay > 0:
        delay_inline(delay)

    return True


def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    theme = get_theme()
    ensure_git()
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warn']}]💰 Pastikan sisa saldo KURANG DARI Rp{balance_threshold}[/]")
        balance_answer = console.input("👉 Gas lanjut pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan 🙅‍♂️")
            pause()
            return None

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Peringatan", f"❌ Gagal ambil data family buat kode: {family_code}")
        pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    
    console.rule()
    successful_purchases = []
    packages_count = sum(len(v["package_options"]) for v in variants)
    
    purchase_count = 0
    start_buying = start_from_option <= 1

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            option_order = option["order"]
            if not start_buying and option_order == start_from_option:
                start_buying = True
            if not start_buying:
                console.print(f"[{theme['text_sub']}]⏭️ Lewati option {option_order}. {option['name']}[/]")
                continue
            
            option_name = option["name"]
            option_price = option["price"]
            
            purchase_count += 1
            console.print(f"[{theme['text_title']}]🛒 Proses pembelian {purchase_count}/{packages_count}[/]")
            console.print(f"👉 Lanjut beli: {variant_name} - {option_order}. {option_name} - Rp{option_price}")
            
            payment_items = []
            
            try:
                if use_decoy:                
                    decoy = DecoyInstance.get_decoy("balance")
                    decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                    if not decoy_package_detail:
                        print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
                        pause()
                        return False
                
                target_package_detail = get_package_details(
                    api_key,
                    tokens,
                    family_code,
                    variant["package_variant_code"],
                    option["order"],
                    None,
                    None,
                )
            except Exception as e:
                print_panel("💥 Kesalahan", f"Error ambil detail paket: {e}")
                console.print(f"❌ Gagal ambil detail buat {variant_name} - {option_name}, skip dulu bro.")
                continue

            payment_items.append(
                PaymentItem(
                    item_code=target_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_package_detail["package_option"]["price"],
                    item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=target_package_detail["token_confirmation"],
                )
            )

            if use_decoy:
                payment_items.append(
                    PaymentItem(
                        item_code=decoy_package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=decoy_package_detail["package_option"]["price"],
                        item_name=f"{randint(1000, 9999)} {decoy_package_detail['package_option']['name']}",
                        tax=0,
                        token_confirmation=decoy_package_detail["token_confirmation"],
                    )
                )
            
            overwrite_amount = target_package_detail["package_option"]["price"]
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_package_detail["package_option"]["price"]
                
            error_msg = ""

            try:
                res = settlement_balance(
                    api_key,
                    tokens,
                    payment_items,
                    "🤑",
                    False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )
                
                if res and res.get("status", "") != "SUCCESS":
                    error_msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in error_msg:
                        error_msg_arr = error_msg.split("=")
                        valid_amount = int(error_msg_arr[1].strip())
                        print_panel("ℹ️ Info", f"💡 Total amount disesuaikan jadi: {valid_amount}")
                        res = settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            "SHARE_PACKAGE",
                            False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=-1
                        )
                        if res and res.get("status", "") == "SUCCESS":
                            error_msg = ""
                            successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - Rp{option_price}")
                            print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                            if pause_on_success:
                                pause()
                        else:
                            error_msg = res.get("message", "")
                else:
                    successful_purchases.append(f"{variant_name}|{option_order}. {option_name} - Rp{option_price}")
                    print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                    if pause_on_success:
                        pause()

            except Exception as e:
                print_panel("💥 Kesalahan", f"Error bikin order: {e}")
            
            console.rule()
            should_delay = error_msg == "" or "Failed call ipaas purchase" in error_msg
            if delay_seconds > 0 and should_delay:
                delay_inline(delay_seconds)

    console.print(f"[{theme['text_title']}]👨‍👩‍👧 Family: {family_name}[/]")
    console.print(f"📊 Total sukses: {len(successful_purchases)}")
    if successful_purchases:
        console.rule()
        console.print("🎉 Daftar pembelian sukses:")
        for purchase in successful_purchases:
            console.print(f"   - {purchase}")
    console.rule()
    pause()


def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    theme = get_theme()
    ensure_git()
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warn']}]💰 Pastikan saldo KURANG DARI Rp{balance_threshold}[/]")
        balance_answer = console.input("👉 Gas lanjut pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan 🙅‍♂️")
            pause()
            return None

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Peringatan", f"❌ Gagal ambil data family buat kode: {family_code}")
        pause()
        return None
    
    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = next((v for v in variants if v["package_variant_code"] == variant_code), None)
    if not target_variant:
        print_panel("⚠️ Peringatan", f"Variant code {variant_code} ga ketemu di family {family_name} 🤔")
        pause()
        return None
    
    target_option = next((o for o in target_variant["package_options"] if o["order"] == option_order), None)
    if not target_option:
        print_panel("⚠️ Peringatan", f"Option order {option_order} ga ada di variant {target_variant['name']} 😅")
        pause()
        return None
    
    option_name = target_option["name"]
    option_price = target_option["price"]
    console.rule()
    successful_purchases = []
    
    for i in range(n):
        console.print(f"[{theme['text_title']}]🛒 Proses pembelian {i + 1}/{n}[/]")
        console.print(f"👉 Lanjut beli: {target_variant['name']} - {option_order}. {option_name} - Rp{option_price}")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
                    pause()
                    return False
            
            target_package_detail = get_package_details(
                api_key,
                tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None,
                None,
            )
        except Exception as e:
            print_panel("💥 Kesalahan", f"Error ambil detail paket: {e}")
            console.print(f"❌ Gagal ambil detail buat {target_variant['name']} - {option_name}, skip dulu bro.")
            continue

        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )

        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=f"{randint(1000, 9999)} {decoy_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    print_panel("ℹ️ Info", f"💡 Total amount disesuaikan jadi: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                        print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                        if pause_on_success:
                            pause()
            else:
                successful_purchases.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{option_price}")
                print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                if pause_on_success:
                    pause()
        except Exception as e:
            print_panel("💥 Kesalahan", f"Error bikin order: {e}")
        
        console.rule()

        if delay_seconds > 0 and i < n - 1:
            delay_inline(delay_seconds)

    console.print(f"[{theme['text_title']}]📊 Total sukses {len(successful_purchases)}/{n}[/]")
    console.print(f"👨‍👩‍👧 Family: {family_name}\n📦 Variant: {target_variant['name']}\n🎯 Option: {option_order}. {option_name} - Rp{option_price}")
    if successful_purchases:
        console.rule()
        console.print("🎉 Daftar pembelian sukses:")
        for idx, purchase in enumerate(successful_purchases, start=1):
            console.print(f"{idx}. {purchase}")
    console.rule()
    pause()
    return True


def purchase_n_times_by_option_code(
    n: int,
    option_code: str,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    theme = get_theme()
    ensure_git()
    active_user = AuthInstance.get_active_user()
    subscription_type = active_user.get("subscription_type", "")
    
    api_key = AuthInstance.api_key
    tokens: dict = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        decoy = DecoyInstance.get_decoy("balance")
        decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
        if not decoy_package_detail:
            print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
            pause()
            return False
        
        balance_threshold = decoy_package_detail["package_option"]["price"]
        console.print(f"[{theme['text_warn']}]💰 Pastikan saldo KURANG DARI Rp{balance_threshold}[/]")
        balance_answer = console.input("👉 Gas lanjut pembelian? (y/n): ").strip().lower()
        if balance_answer != "y":
            print_panel("ℹ️ Info", "Pembelian dibatalkan 🙅‍♂️")
            pause()
            return None
    
    console.rule()
    successful_purchases = []
    
    for i in range(n):
        console.print(f"[{theme['text_title']}]🛒 Proses pembelian {i + 1}/{n}[/]")
        
        api_key = AuthInstance.api_key
        tokens: dict = AuthInstance.get_active_tokens() or {}
        payment_items = []
        
        try:
            if use_decoy:
                decoy = DecoyInstance.get_decoy("balance")
                decoy_package_detail = get_package(api_key, tokens, decoy["option_code"])
                if not decoy_package_detail:
                    print_panel("⚠️ Peringatan", "❌ Gagal load detail paket decoy 😅")
                    pause()
                    return False
            
            target_package_detail = get_package(api_key, tokens, option_code)
        except Exception as e:
            print_panel("💥 Kesalahan", f"Error ambil detail paket: {e}")
            continue

        payment_items.append(
            PaymentItem(
                item_code=target_package_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_package_detail["package_option"]["price"],
                item_name=f"{randint(1000, 9999)} {target_package_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_package_detail["token_confirmation"],
            )
        )

        if use_decoy:
            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=f"{randint(1000, 9999)} {decoy_package_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
        
        overwrite_amount = target_package_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_package_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    print_panel("ℹ️ Info", f"💡 Total amount disesuaikan jadi: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=token_confirmation_idx
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        successful_purchases.append(f"Purchase {i + 1}")
                        print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                        if pause_on_success:
                            pause()
            else:
                successful_purchases.append(f"Purchase {i + 1}")
                print_panel("✅ Sukses", "Pembelian berhasil 🎉")
                if pause_on_success:
                    pause()
        except Exception as e:
            print_panel("💥 Kesalahan", f"Error bikin order: {e}")
        
        console.rule()

        if delay_seconds > 0 and i < n - 1:
            delay_inline(delay_seconds)

    console.print(f"[{theme['text_title']}]📊 Total sukses {len(successful_purchases)}/{n}[/]")
    if successful_purchases:
        console.rule()
        console.print("🎉 Daftar pembelian sukses:")
        for idx, purchase in enumerate(successful_purchases, start=1):
            console.print(f"{idx}. {purchase}")
    console.rule()
    return True
