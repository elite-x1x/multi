import os
import json
import time

# File cache lokal (hidden file)
CACHE_FILE = ".cache.json"

# Cache in-memory
_memory_cache = {}

# Limit jumlah key di file cache (default 50)
MAX_KEYS = 500  # bisa disesuaikan


def _load_file_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_file_cache(cache: dict):
    try:
        # Batasi jumlah key agar file tidak membesar
        if len(cache) > MAX_KEYS:
            oldest = min(cache.items(), key=lambda x: x[1]["time"])[0]
            del cache[oldest]
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            # indent=2 membuat JSON rapi, tiap level masuk 2 spasi
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _make_key(account_id: str, key: str) -> str:
    """Gabungkan account_id dengan key agar cache per akun."""
    return f"{account_id}_{key}"

def get_cache(account_id: str, key: str, ttl: int = 60, use_file: bool = False, default=None):
    """
    Ambil data dari cache per akun.
    - account_id: identifier akun (misalnya nomor/subscriber_id)
    - key: nama data (balance, quota, segments)
    - ttl: waktu hidup cache (detik)
    - use_file: True untuk cache file, False untuk cache memory
    - default: nilai default jika cache kosong/kadaluarsa
    """
    now = time.monotonic()
    full_key = _make_key(account_id, key)

    if use_file:
        cache = _load_file_cache()
        if full_key in cache:
            if now - cache[full_key]["time"] < ttl:
                return cache[full_key]["value"]
    else:
        data = _memory_cache.get(full_key)
        if data and (now - data["time"] < ttl):
            return data["value"]
    return default

def set_cache(account_id: str, key: str, value, use_file: bool = False):
    """
    Simpan data ke cache per akun.
    """
    now = time.monotonic()
    full_key = _make_key(account_id, key)

    if use_file:
        cache = _load_file_cache()
        cache[full_key] = {"value": value, "time": now}
        _save_file_cache(cache)
    else:
        _memory_cache[full_key] = {"value": value, "time": now}

def clear_cache(account_id: str = None):
    """
    Bersihkan cache.
    - Jika account_id diberikan, hanya cache untuk akun itu yang dihapus.
    - Jika tidak, semua cache dihapus.
    """
    global _memory_cache
    if account_id:
        # Hapus cache memory per akun
        _memory_cache = {k: v for k, v in _memory_cache.items() if not k.startswith(f"{account_id}_")}
        # Hapus cache file per akun
        cache = _load_file_cache()
        cache = {k: v for k, v in cache.items() if not k.startswith(f"{account_id}_")}
        _save_file_cache(cache)
    else:
        # Hapus semua cache
        _memory_cache = {}
        if os.path.exists(CACHE_FILE):
            try:
                os.remove(CACHE_FILE)
            except Exception:
                pass
