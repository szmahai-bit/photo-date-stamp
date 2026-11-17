#!/usr/bin/env python3
"""Generate app icons (calendar / date themed) with pure Pillow.

No external assets required. Generates:
  - assets/icon.ico        Windows EXE icon
  - assets/icon.iconset/   macOS PNG set, converted to .icns by iconutil in build_mac.sh

Keeping icons generated from source avoids committing binary blobs and keeps
the repository reproducible.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
# macOS iconset: each logical size has a 1x and a 2x (retina) PNG.
ICONSET_SPECS = [
    ("icon_16x16.png", 16), ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32), ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128), ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256), ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512), ("icon_512x512@2x.png", 1024),
]
ORANGE = (0xFF, 0x5C, 0x1C)
DARK = (0x2A, 0x20, 0x18)
WHITE = (0xFF, 0xF3, 0xE8)

HERE = Path(__file__).resolve().parent
ICO_OUT = HERE / "assets" / "icon.ico"
ICONSET_OUT = HERE / "assets" / "icon.iconset"


def draw_base(S: int) -> Image.Image:
    """Draw one high-res master tile at size S, then downscale per icon size."""
    scale = 4
    N = S * scale
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    m = round(N * 0.10)
    # Rounded orange body
    d.rounded_rectangle([m, m, N - m, N - m], radius=round(N * 0.16), fill=ORANGE)
    # Top binding bar (darker)
    bar_h = round(N * 0.17)
    d.rounded_rectangle([m, m, N - m, m + bar_h], radius=round(N * 0.16), fill=DARK)
    d.rectangle([m, m + bar_h // 2, N - m, m + bar_h], fill=DARK)
    # Two binder rings
    ring_w = round(N * 0.05)
    ring_h = round(N * 0.09)
    for cx in (N * 0.33, N * 0.67):
        d.rounded_rectangle(
            [cx - ring_w / 2, m - ring_h * 0.55, cx + ring_w / 2, m + ring_h * 0.55],
            radius=ring_w / 2, fill=WHITE,
        )
    # Seven-segment-ish "date" dots in the body
    dot = round(N * 0.045)
    gap = round(N * 0.085)
    cy = round(N * 0.60)
    for i in range(3):
        cx = N * 0.30 + i * gap
        d.rounded_rectangle([cx - dot, cy - dot, cx + dot, cy + dot], radius=dot / 2, fill=WHITE)
    return img.resize((S, S), Image.LANCZOS)


def main() -> None:
    ICO_OUT.parent.mkdir(parents=True, exist_ok=True)
    master = draw_base(max(max(ICO_SIZES), 1024))
    # Windows ICO
    master.save(ICO_OUT, format="ICO", sizes=[(s, s) for s in ICO_SIZES])
    print(f"icon written: {ICO_OUT} ({ICO_OUT.stat().st_size} bytes)")
    # macOS iconset PNGs (iconutil converts these to .icns at build time)
    ICONSET_OUT.mkdir(parents=True, exist_ok=True)
    for name, size in ICONSET_SPECS:
        draw_base(size).save(ICONSET_OUT / name, format="PNG")
    print(f"iconset written: {ICONSET_OUT} ({len(ICONSET_SPECS)} PNGs)")


if __name__ == "__main__":
    main()
