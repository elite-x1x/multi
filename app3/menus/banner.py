import os
import hashlib
import urllib.parse
import urllib.request
from pathlib import Path
from ascii_magic import AsciiArt
from PIL import Image   # pip install pillow

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ALLOWED_DOMAINS = {"d17e22l2uh4h4n.cloudfront.net"}

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

def calculate_idat_hash(data: bytes) -> bytes:
    """Hitung SHA-256 hash dari semua chunk IDAT dalam file PNG."""
    sha256 = hashlib.sha256()
    for chunk_type, chunk_data in parse_png_chunks(data):
        if chunk_type == b"IDAT":
            sha256.update(chunk_data)
    return sha256.digest()

def derive_key(seed: bytes, length: int) -> bytes:
    """Derive key dengan SHA-256 berbasis seed untuk panjang tertentu."""
    result, counter = bytearray(), 0
    while len(result) < length:
        result += hashlib.sha256(seed + counter.to_bytes(8, "big")).digest()
        counter += 1
    return bytes(result[:length])

def xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR dua byte array."""
    return bytes(d ^ k for d, k in zip(data, key))

def validate_url(url: str):
    """Validasi URL agar hanya menggunakan skema http/https dan domain yang diizinkan."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Skema URL tidak didukung. Gunakan http atau https.")
    host = parsed.hostname or ""
    if host not in ALLOWED_DOMAINS:
        raise ValueError(f"Domain tidak diizinkan: {host}")

def load(url: str, context: dict):
    """Load ASCII art dari URL yang valid dan ekstrak banner text jika tersedia."""
    try:
        validate_url(url)
        ascii_art = AsciiArt.from_url(url)
        with urllib.request.urlopen(url, timeout=5) as response:
            content = response.read()
        if not content.startswith(PNG_SIGNATURE):
            return None
    except Exception as e:
        print(f"Error load: {e}")
        return None

    banner_text = None
    for chunk_type, chunk_data in parse_png_chunks(content):
        if chunk_type in {b"tEXt", b"iTXt"} and chunk_data.startswith(b"banner\x00"):
            banner_text = chunk_data.split(b"\x00", 1)[1].decode("utf-8", "ignore").strip()
            break

    if banner_text:
        context["__banner__"] = banner_text

    return ascii_art

def load_local(path: str, context: dict):
    """Load ASCII art dari file PNG lokal dan ekstrak banner text jika ada."""
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File tidak ditemukan: {path}")
        # buka gambar dengan Pillow
        img = Image.open(path)
        ascii_art = AsciiArt.from_image(img)
        # baca raw bytes untuk parse chunk
        with open(path, "rb") as f:
            content = f.read()
        if not content.startswith(PNG_SIGNATURE):
            return None
    except Exception as e:
        print(f"Error load_local: {e}")
        return None

    banner_text = None
    for chunk_type, chunk_data in parse_png_chunks(content):
        if chunk_type in {b"tEXt", b"iTXt"} and chunk_data.startswith(b"banner\x00"):
            banner_text = chunk_data.split(b"\x00", 1)[1].decode("utf-8", "ignore").strip()
            break

    if banner_text:
        context["__banner__"] = banner_text

    return ascii_art
