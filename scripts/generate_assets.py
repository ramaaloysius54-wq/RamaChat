import struct
import zlib
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

def create_solid_png(path: Path, width: int, height: int, rgb: tuple[int, int, int]) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    raw_row = b"\x00" + bytes(rgb) * width
    raw_data = raw_row * height
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_data, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)

def generate_all_assets() -> None:
    create_solid_png(ASSETS_DIR / "icon.png", 256, 256, (40, 120, 240))
    create_solid_png(ASSETS_DIR / "logo.png", 256, 256, (40, 120, 240))
    create_solid_png(ASSETS_DIR / "splash.png", 360, 640, (247, 249, 252))
    print("[OK] assets/icon.png, logo.png, splash.png berhasil dibuat.")

if __name__ == "__main__":
    generate_all_assets()
