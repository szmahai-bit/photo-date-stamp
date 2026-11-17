#!/usr/bin/env python3
"""Generate assets/icon.ico (calendar / date themed) with pure Pillow.

No external assets required. Run automatically by build.bat and the CI
workflow before PyInstaller packages the app. Keeping the icon generated from
source avoids committing a binary blob and keeps the repository reproducible.
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]
ORANGE = (0xFF, 0x5C, 0x1C)
DARK = (0x2A, 0x20, 0x18)
WHITE = (0xFF, 0xF3, 0xE8)

HERE = Path(__file__).resolve().parent
OUT = HERE / "assets" / "icon.ico"


def draw_base(S: int) -> Image.Image:
    """Draw one high-res master tile at size S, then downscale per ICO size."""
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
    OUT.parent.mkdir(parents=True, exist_ok=True)
    master = draw_base(max(SIZES))
    master.save(OUT, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"icon written: {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
