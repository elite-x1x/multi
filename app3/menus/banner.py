import os
import urllib.parse
import urllib.request
from pathlib import Path
from ascii_magic import AsciiArt
from PIL import Image   # pastikan Pillow terinstall: pip install pillow

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

def parse_png_chunks(data: bytes):
    """Parse PNG chunks dari raw byte data."""
    assert data.startswith(PNG_SIGNATURE), "Data bukan file PNG yang valid."
    offset, length = 8, len(data)
    while offset + 12 <= length:
        chunk_size = int.from_bytes(data[offset:offset + 4], "big")
        chunk_type = data[offset + 4:offset + 8]
        chunk_data = data[offset + 8:offset + 8 + chunk_size]
        yield chunk_type, chunk_data
        offset += 12 + chunk_size

def load_any(source: str, context: dict):
    """
    Bisa load ASCII art dari URL (http/https) atau file lokal (path).
    Juga ekstrak banner text dari chunk PNG jika ada.
    """
    content = None
    ascii_art = None

    try:
        parsed = urllib.parse.urlparse(source)
        if parsed.scheme in {"http", "https"}:
            # --- Mode URL ---
            ascii_art = AsciiArt.from_url(source)
            with urllib.request.urlopen(source, timeout=5) as response:
                content = response.read()
        else:
            # --- Mode file lokal ---
            if not os.path.exists(source):
                raise FileNotFoundError(f"File tidak ditemukan: {source}")
            # baca raw bytes untuk parse chunk
            with open(source, "rb") as f:
                content = f.read()
            # buka image dengan Pillow untuk ASCII
            img = Image.open(source)
            ascii_art = AsciiArt.from_image(img)

        # validasi signature PNG
        if not content.startswith(PNG_SIGNATURE):
            return None

    except Exception as e:
        print(f"Error load_any: {e}")
        return None

    # Ekstrak banner text dari chunk PNG
    banner_text = None
    for chunk_type, chunk_data in parse_png_chunks(content):
        if chunk_type in {b"tEXt", b"iTXt"} and chunk_data.startswith(b"banner\x00"):
            banner_text = chunk_data.split(b"\x00", 1)[1].decode("utf-8", "ignore").strip()
            break

    if banner_text:
        context["__banner__"] = banner_text

    return ascii_art
