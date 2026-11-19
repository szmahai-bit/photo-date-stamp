"""日期戳渲染核心 —— 独立模块，不依赖 alcedo skill 或任何外部工具。

只依赖 Pillow。对外提供:
  - read_exif_datetime(path)  读取拍摄时间
  - render_stamp(...)         渲染日期戳图层
  - apply_stamp(...)          把日期戳叠加到图片并返回结果
  - process_file(...)         单文件端到端处理并保存

渲染风格与 date_stamp.py 完全一致：Pentax 橙红七段数码管、柔光、段亮度不均、
screen(滤色)叠加，使暗处发光、亮处冲淡，模拟胶片背面曝光。
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".png", ".bmp", ".webp"}

PENTAX_ORANGE = (0xFF, 0x5C, 0x1C)

# 年月日各组之间的最小可见间隙，单位为数字宽度 digit_w。
# "26 01 08" 这类组合里，组间空白至少要有 GROUP_GAP_RATIO 个数字那么宽，避免挤在一起。
GROUP_GAP_RATIO = 1.5

# 位置比例，来自真实 Pentax 样片测量。ratio 描述"墨迹到边缘"的距离。
LAYOUTS = {
    "landscape": {"rotate": 0, "right": 0.10, "edge": 0.089, "edge_side": "bottom"},
    "portrait": {"rotate": 90, "right": 0.10, "edge": 0.133, "edge_side": "top"},
}

SEGMENTS = {
    "0": set("abcdef"), "1": set("bc"), "2": set("abged"), "3": set("abgcd"),
    "4": set("fgbc"), "5": set("afgcd"), "6": set("afgecd"), "7": set("abc"),
    "8": set("abcdefg"), "9": set("abfgcd"), "'": set("i"), ".": set("h"),
    ":": set("jk"), "-": set("g"), "/": set("fc"),
}
ALL_SEGMENTS = set("abcdefg")


def read_exif_datetime(path: str | Path) -> Optional[dt.datetime]:
    """读取图片的 EXIF 拍摄时间 (DateTimeOriginal -> DateTimeDigitized -> DateTime)。"""
    try:
        with Image.open(path) as im:
            exif = im.getexif()
    except Exception:
        return None
    if not exif:
        return None
    sources = []
    try:
        sources.append(exif.get_ifd(0x8769))
    except Exception:
        pass
    sources.append(exif)
    tags = (0x9003, 0x9004, 0x0132)
    for src in sources:
        if not src:
            continue
        for tag in tags:
            value = src.get(tag)
            if not value:
                continue
            text = str(value).strip().strip("\x00")
            for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S",
                            "%Y:%m:%d", "%Y-%m-%d"):
                try:
                    return dt.datetime.strptime(text, pattern)
                except ValueError:
                    continue
    return None


def _chamfer_rect(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def _glyph_polygons(w, h, t):
    mid = (h - t) / 2
    return {
        "a": _chamfer_rect(t, 0, w - t, t, t / 2),
        "g": _chamfer_rect(t, mid, w - t, mid + t, t / 2),
        "d": _chamfer_rect(t, h - t, w - t, h, t / 2),
        "f": _chamfer_rect(0, t, t, mid, t / 2),
        "b": _chamfer_rect(w - t, t, w, mid, t / 2),
        "e": _chamfer_rect(0, mid + t, t, h - t, t / 2),
        "c": _chamfer_rect(w - t, mid + t, w, h - t, t / 2),
        "i": _chamfer_rect(w * 0.30, h * 0.05, w * 0.48, h * 0.32, t / 3),
        "h": _chamfer_rect(w * 0.34, h - t * 1.7, w * 0.66, h - t * 0.7, t / 3),
        "j": _chamfer_rect(w * 0.38, h * 0.18, w * 0.62, h * 0.40, t / 3),
        "k": _chamfer_rect(w * 0.38, h * 0.60, w * 0.62, h * 0.82, t / 3),
    }


def _advance(char, digit_w, gap, t):
    if char == " ":
        # 组间空白 = 前一个数字的右间距(gap) + 空格的推进量。
        # 要求该空白 >= GROUP_GAP_RATIO * digit_w，故空格至少推进这么多；
        # 也保留旧值做下限，避免其它比例组合下反而变小。
        return max(digit_w * 0.62, GROUP_GAP_RATIO * digit_w - gap)
    if char in ".:'":
        return digit_w * 0.55 + gap
    if char == "-":
        return digit_w * 0.75 + gap
    return digit_w + gap


def _segment_gain(char, name):
    seed = (ord(char) * 31 + ord(name) * 17 + len(name)) % 13
    return 0.84 + seed * 0.012


def render_stamp(text: str, digit_h: int, color: tuple[int, int, int] = PENTAX_ORANGE,
                 glow: bool = True, ghost: bool = True) -> "Image.Image":
    """把日期文本渲染为 RGB '光量' 图层：黑=无光，彩色=发光。供 screen 叠加。"""
    t = max(2, round(digit_h * 0.13))
    digit_w = round(digit_h * 0.58)
    gap = round(digit_h * 0.22)
    pad = max(4, round(digit_h * 0.30))
    width = int(sum(_advance(c, digit_w, gap, t) for c in text) + pad * 2)
    height = digit_h + pad * 2
    mask = Image.new("L", (max(width, 1), height), 0)
    draw = ImageDraw.Draw(mask)
    polys = _glyph_polygons(digit_w, digit_h, t)
    x = pad
    for char in text:
        if char == " ":
            x += _advance(char, digit_w, gap, t)
            continue
        segments = SEGMENTS.get(char)
        if segments is None:
            x += _advance(char, digit_w, gap, t)
            continue
        if ghost:
            for name in ALL_SEGMENTS:
                draw.polygon([(px + x, py + pad) for px, py in polys[name]], fill=18)
        for name in segments:
            draw.polygon([(px + x, py + pad) for px, py in polys[name]],
                         fill=round(255 * _segment_gain(char, name)))
        x += _advance(char, digit_w, gap, t)

    soft = max(1.0, digit_h * 0.022)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=soft))
    if glow:
        halo = mask.filter(ImageFilter.GaussianBlur(radius=max(2.0, digit_h * 0.11)))
        halo = halo.point(lambda v: int(v * 0.55))
        mask = ImageChops.lighter(mask, halo)

    r = mask.point(lambda v: v * color[0] // 255)
    g = mask.point(lambda v: v * color[1] // 255)
    b = mask.point(lambda v: v * color[2] // 255)
    return Image.merge("RGB", (r, g, b))


def compute_layout(image_size: tuple[int, int], stamp: "Image.Image",
                   orientation: str = "auto", right_ratio: float = 0.10,
                   edge_ratio: float | None = None, digit_h: int = 0) -> tuple[int, int]:
    """根据图片尺寸和布局策略算出日期戳左上角坐标。"""
    W, H = image_size
    if orientation == "auto":
        orientation = "portrait" if H > W else "landscape"
    layout = LAYOUTS[orientation]
    er = edge_ratio if edge_ratio is not None else layout["edge"]
    pad = max(4, round(digit_h * 0.30))
    margin_x = round(W * right_ratio) - pad
    margin_y = round(H * er) - pad
    if layout["edge_side"] == "top":
        return (W - stamp.width - margin_x, margin_y)
    return (W - stamp.width - margin_x, H - stamp.height - margin_y)


def apply_stamp(image: "Image.Image", text: str, *, size_ratio: float = 0.032,
                size: int | None = None, color: tuple[int, int, int] = PENTAX_ORANGE,
                glow: bool = True, ghost: bool = True, orientation: str = "auto",
                right_ratio: float = 0.10, edge_ratio: float | None = None,
                rotate: int | None = None,
                pos: tuple[int, int] | None = None) -> "Image.Image":
    """把日期戳叠加到图片，返回结果图（RGB）。rotate 可强制旋转角度覆盖布局默认。"""
    if image.mode != "RGB":
        image = image.convert("RGB")
    short_edge = min(image.size)
    digit_h = size if size else max(18, round(short_edge * size_ratio))
    stamp = render_stamp(text, digit_h, color, glow, ghost)

    if rotate is None:
        lay = LAYOUTS["portrait" if image.height > image.width else "landscape"]
        rotate = lay["rotate"]
    if rotate:
        stamp = stamp.rotate(rotate, expand=True)

    if pos is None:
        pos = compute_layout(image.size, stamp, orientation, right_ratio, edge_ratio, digit_h)
    light = Image.new("RGB", image.size, (0, 0, 0))
    light.paste(stamp, pos)
    return ImageChops.screen(image, light)


def process_file(src: str | Path, dst: str | Path, *, captured: dt.datetime | str | None = None,
                 date_format: str = "'%y %m %d", size_ratio: float = 0.032,
                 size: int | None = None, color: tuple[int, int, int] = PENTAX_ORANGE,
                 glow: bool = True, ghost: bool = True, orientation: str = "auto",
                 right_ratio: float = 0.10, edge_ratio: float | None = None,
                 quality: int = 95) -> tuple[bool, str]:
    """单文件端到端：读图 -> 取日期 -> 盖章 -> 保存(保留 EXIF/ICC)。返回 (成功, 说明)。"""
    src = Path(src)
    dst = Path(dst)
    try:
        with Image.open(src) as opened:
            image = ImageOps.exif_transpose(opened)
            image.load()
            exif = opened.getexif()
            icc = opened.info.get("icc_profile")
            fmt = opened.format
            # exif_transpose has already physically rotated the pixels to their
            # display orientation. The source EXIF still carries the Orientation
            # tag (e.g. 6/8 for a portrait shot); writing it back makes viewers
            # rotate the image a SECOND time and turn portrait photos landscape.
            # Strip the orientation tag while keeping all other EXIF/ICC data.
            if 0x0112 in exif:
                del exif[0x0112]
    except Exception as error:
        return False, f"无法打开: {error}"

    if captured is None:
        captured = read_exif_datetime(src)
    elif isinstance(captured, str):
        try:
            captured = dt.datetime.strptime(captured, "%Y-%m-%d")
        except ValueError:
            return False, "手动日期格式应为 YYYY-MM-DD"
    if captured is None:
        return False, "图片没有 EXIF 拍摄时间（请在界面里手动指定日期）"

    text = captured.strftime(date_format)
    result = apply_stamp(image, text, size_ratio=size_ratio, size=size, color=color,
                         glow=glow, ghost=ghost, orientation=orientation,
                         right_ratio=right_ratio, edge_ratio=edge_ratio)

    dst.parent.mkdir(parents=True, exist_ok=True)
    save_kwargs: dict = {"quality": quality, "subsampling": 0}
    if exif:
        save_kwargs["exif"] = exif.tobytes()
    if icc:
        save_kwargs["icc_profile"] = icc
    ext = dst.suffix.lower()
    out = result.convert("RGB")
    try:
        if ext in (".tif", ".tiff"):
            save_kwargs.pop("quality", None); save_kwargs.pop("subsampling", None)
            out.save(dst, "TIFF", **save_kwargs)
        elif ext == ".png":
            save_kwargs.pop("quality", None); save_kwargs.pop("subsampling", None)
            out.save(dst, "PNG", **save_kwargs)
        else:
            if dst.suffix.lower() not in (".jpg", ".jpeg", ".jpe"):
                dst = dst.with_suffix(".jpg")
            out.save(dst, "JPEG", **save_kwargs)
    except Exception as error:
        return False, f"保存失败: {error}"
    return True, text
