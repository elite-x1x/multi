from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family

WIDTH = 55


def print_header(title: str):
    print("-" * WIDTH)
    print(title.center(WIDTH))
    print("-" * WIDTH)


def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        print_header("Bookmark Paket")
        bookmarks = BookmarkInstance.get_bookmarks()

        if not bookmarks or len(bookmarks) == 0:
            print("Belum ada bookmark tersimpan.")
            pause()
            return None

        for idx, bm in enumerate(bookmarks):
            print(f" {idx + 1}. {bm['family_name']} - {bm['variant_name']} - {bm['option_name']}")

        print("-" * WIDTH)
        print("Perintah:")
        print(" [00] Kembali ke menu utama")
        print(" [000] Hapus bookmark tertentu")
        print("-" * WIDTH)

        choice = input("Pilih bookmark (nomor): ").strip()

        if choice == "00":
            in_bookmark_menu = False
            return None

        elif choice == "000":
            del_choice = input("Masukkan nomor bookmark yang ingin dihapus: ").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
                print(f"Bookmark {del_bm['option_name']} berhasil dihapus.")
                pause()
            else:
                print("Input tidak valid. Silakan coba lagi.")
                pause()
            continue

        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]

            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print("Gagal mengambil data paket.")
                pause()
                continue

            package_variants = family_data.get("package_variants", [])
            option_code = None

            for variant in package_variants:
                if variant.get("name") == selected_bm["variant_name"]:
                    for option in variant.get("package_options", []):
                        if option.get("order") == selected_bm["order"]:
                            option_code = option.get("package_option_code")
                            break

            if option_code:
                print(f"Option code: {option_code}")
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                print("Option code tidak ditemukan.")
                pause()

        else:
            print("Input tidak valid. Silakan coba lagi.")
            pause()
            continue
