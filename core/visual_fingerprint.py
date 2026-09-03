"""Deterministic visual-review fingerprint over Playwright PNG screenshots.

The proof bundle still carries exact SHA-256 hashes for every PNG. This module
adds a second identity used only for subjective visual approval: a bounded
raster-equivalence fingerprint that deliberately ignores isolated ±1 channel
rasterisation noise while remaining sensitive to meaningful rendered changes.

No third-party imaging dependency is used. The decoder supports the 8-bit,
non-interlaced RGB/RGBA PNGs emitted by Playwright/Chromium.
"""
from __future__ import annotations

import hashlib
import pathlib
import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REVIEW_FINGERPRINT_ALGO = "png-blockmean4-v1"
BLOCK_SIZE = 4


class VisualFingerprintError(ValueError):
    """Raised when a screenshot cannot be fingerprinted deterministically."""


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _decode_png(path: pathlib.Path) -> tuple[int, int, int, list[bytes]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise VisualFingerprintError(f"not a PNG: {path}")

    pos = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    compression = filter_method = None
    idat: list[bytes] = []

    while pos < len(data):
        if pos + 12 > len(data):
            raise VisualFingerprintError(f"truncated PNG chunk: {path}")
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        start = pos + 8
        end = start + length
        if end + 4 > len(data):
            raise VisualFingerprintError(f"truncated PNG payload: {path}")
        payload = data[start:end]
        expected_crc = struct.unpack(">I", data[end : end + 4])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise VisualFingerprintError(f"PNG CRC mismatch in {path}")
        pos = end + 4

        if chunk_type == b"IHDR":
            if length != 13:
                raise VisualFingerprintError(f"invalid IHDR in {path}")
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == b"IDAT":
            idat.append(payload)
        elif chunk_type == b"IEND":
            break

    if None in (width, height, bit_depth, color_type, compression, filter_method, interlace):
        raise VisualFingerprintError(f"PNG header missing in {path}")
    if bit_depth != 8 or color_type not in (2, 6):
        raise VisualFingerprintError(
            f"unsupported PNG format in {path}: bit_depth={bit_depth} color_type={color_type}"
        )
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise VisualFingerprintError(
            f"unsupported PNG encoding in {path}: compression={compression} "
            f"filter={filter_method} interlace={interlace}"
        )
    if not idat:
        raise VisualFingerprintError(f"PNG has no IDAT in {path}")

    channels = 3 if color_type == 2 else 4
    stride = width * channels
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as exc:
        raise VisualFingerprintError(f"PNG inflate failed in {path}: {exc}") from exc
    expected_size = height * (stride + 1)
    if len(raw) != expected_size:
        raise VisualFingerprintError(
            f"unexpected PNG scanline size in {path}: {len(raw)} != {expected_size}"
        )

    rows: list[bytes] = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        scanline = raw[offset : offset + stride]
        offset += stride
        reconstructed = bytearray(stride)

        for i, value in enumerate(scanline):
            left = reconstructed[i - channels] if i >= channels else 0
            up = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = (value + left) & 0xFF
            elif filter_type == 2:
                decoded = (value + up) & 0xFF
            elif filter_type == 3:
                decoded = (value + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                decoded = (value + _paeth(left, up, upper_left)) & 0xFF
            else:
                raise VisualFingerprintError(
                    f"unsupported PNG filter {filter_type} in {path}"
                )
            reconstructed[i] = decoded

        rows.append(bytes(reconstructed))
        previous = reconstructed

    return width, height, channels, rows


def screenshot_review_fingerprint(path: pathlib.Path, block_size: int = BLOCK_SIZE) -> str:
    """Return a content fingerprint over 4x4 channel means.

    Exact PNG integrity is verified separately by the proof bundle. Here each
    source-aligned block is reduced to floor(mean(channel)). An isolated ±1
    antialiasing fluctuation therefore cannot normally invalidate an approval,
    while a coherent rendered change affects one or more block means.
    """
    if block_size <= 0:
        raise VisualFingerprintError("block_size must be positive")

    width, height, channels, rows = _decode_png(path)
    payload = bytearray()
    payload.extend(REVIEW_FINGERPRINT_ALGO.encode("ascii"))
    payload.append(0)
    payload.extend(struct.pack(">IIHH", width, height, channels, block_size))

    for y0 in range(0, height, block_size):
        block_height = min(block_size, height - y0)
        for x0 in range(0, width, block_size):
            block_width = min(block_size, width - x0)
            count = block_width * block_height
            sums = [0] * channels
            for y in range(y0, y0 + block_height):
                row = rows[y]
                for x in range(x0, x0 + block_width):
                    base = x * channels
                    for channel in range(channels):
                        sums[channel] += row[base + channel]
            payload.extend(bytes(total // count for total in sums))

    return hashlib.sha256(payload).hexdigest()[:16]


def review_fingerprint_manifest(paths: dict[str, pathlib.Path]) -> dict[str, str]:
    """Fingerprint an exact named screenshot matrix in stable name order."""
    return {
        name: screenshot_review_fingerprint(paths[name])
        for name in sorted(paths)
    }
