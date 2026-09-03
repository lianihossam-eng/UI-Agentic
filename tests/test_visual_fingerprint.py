import hashlib
import pathlib
import struct
import tempfile
import unittest
import zlib

from core.visual_fingerprint import (
    REVIEW_FINGERPRINT_ALGO,
    VisualFingerprintError,
    screenshot_review_fingerprint,
)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def write_rgb_png(path: pathlib.Path, width: int, height: int, pixels: list[list[tuple[int, int, int]]]) -> None:
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(data)


class VisualFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def image(self, value: int = 100) -> list[list[tuple[int, int, int]]]:
        return [[(value, value, value) for _ in range(8)] for _ in range(8)]

    def test_algorithm_identifier_is_versioned(self):
        self.assertEqual(REVIEW_FINGERPRINT_ALGO, "png-spatialmoments4-v2")

    def test_isolated_one_level_raster_noise_does_not_invalidate_review(self):
        base = self.root / "base.png"
        noisy = self.root / "noisy.png"
        base_pixels = self.image()
        noisy_pixels = self.image()
        noisy_pixels[1][1] = (101, 100, 100)
        write_rgb_png(base, 8, 8, base_pixels)
        write_rgb_png(noisy, 8, 8, noisy_pixels)

        self.assertNotEqual(hashlib.sha256(base.read_bytes()).digest(), hashlib.sha256(noisy.read_bytes()).digest())
        self.assertEqual(
            screenshot_review_fingerprint(base),
            screenshot_review_fingerprint(noisy),
        )

    def test_coherent_rendered_change_changes_review_fingerprint(self):
        base = self.root / "base.png"
        changed = self.root / "changed.png"
        base_pixels = self.image()
        changed_pixels = self.image()
        for y in range(4):
            for x in range(4):
                changed_pixels[y][x] = (132, 100, 100)
        write_rgb_png(base, 8, 8, base_pixels)
        write_rgb_png(changed, 8, 8, changed_pixels)

        self.assertNotEqual(
            screenshot_review_fingerprint(base),
            screenshot_review_fingerprint(changed),
        )

    def test_same_mean_spatial_rearrangement_changes_review_fingerprint(self):
        horizontal = self.root / "horizontal.png"
        vertical = self.root / "vertical.png"
        horizontal_pixels = self.image()
        vertical_pixels = self.image()

        for y in range(4):
            for x in range(4):
                horizontal_pixels[y][x] = (80 if x < 2 else 120, 100, 100)
                vertical_pixels[y][x] = (80 if y < 2 else 120, 100, 100)

        write_rgb_png(horizontal, 8, 8, horizontal_pixels)
        write_rgb_png(vertical, 8, 8, vertical_pixels)

        # Both 4x4 red blocks have exactly the same arithmetic mean (100), but
        # their spatial arrangement differs. v1 block means collided here.
        self.assertNotEqual(
            screenshot_review_fingerprint(horizontal),
            screenshot_review_fingerprint(vertical),
        )

    def test_corrupt_png_is_fail_closed(self):
        path = self.root / "corrupt.png"
        pixels = self.image()
        write_rgb_png(path, 8, 8, pixels)
        data = bytearray(path.read_bytes())
        data[-5] ^= 0x01
        path.write_bytes(data)
        with self.assertRaises(VisualFingerprintError):
            screenshot_review_fingerprint(path)


if __name__ == "__main__":
    unittest.main()
