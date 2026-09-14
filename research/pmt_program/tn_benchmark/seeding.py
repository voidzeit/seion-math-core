"""Deterministic seeds independent of PYTHONHASHSEED."""
import zlib


def stable_seed(*parts) -> int:
    return zlib.crc32(repr(parts).encode("utf-8")) & 0xFFFFFFFF
