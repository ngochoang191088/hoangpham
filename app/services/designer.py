"""Thiết kế bộ ảnh quảng cáo từ ảnh gốc Shopee (Pillow).

- Chỉnh ảnh gốc: xoay đúng chiều, cân bằng sáng/tương phản, tăng độ nét, phóng to ảnh nhỏ.
- Dựng 3-5 ảnh theo bố cục: ảnh bìa (tiêu đề + giá), ảnh điểm nổi bật, ảnh kêu gọi mua.
- Nhiều "theme" màu và bố cục; mỗi phiên bản (variant) khác nhau để các page không đăng ảnh giống hệt.
Kích thước: 1080x1350 (4:5, hiển thị lớn nhất trên bảng tin Facebook) và 1080x1920 (9:16, dùng cho video).
"""
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

FONT_DIR = Path(__file__).resolve().parent.parent / "static" / "fonts"
FONT_BOLD = FONT_DIR / "BeVietnamPro-ExtraBold.ttf"
FONT_MEDIUM = FONT_DIR / "BeVietnamPro-Medium.ttf"

FEED = (1080, 1350)
STORY = (1080, 1920)

THEMES = [
    {"name": "Cam Shopee", "top": "#FFF4EE", "bottom": "#FFD9C9", "accent": "#EE4D2D", "text": "#2A1A14",
     "muted": "#7A5A4E", "on_accent": "#FFFFFF"},
    {"name": "Xanh mint", "top": "#F0FBF6", "bottom": "#CDEFE0", "accent": "#0E9F6E", "text": "#0F2A20",
     "muted": "#4F6B60", "on_accent": "#FFFFFF"},
    {"name": "Đêm sang trọng", "top": "#222B4A", "bottom": "#0E1426", "accent": "#FFC53D", "text": "#FFFFFF",
     "muted": "#B9C0D8", "on_accent": "#1B1B1B"},
    {"name": "Hồng pastel", "top": "#FFF2F6", "bottom": "#FFD6E4", "accent": "#E0457B", "text": "#3A1422",
     "muted": "#7D4C5E", "on_accent": "#FFFFFF"},
    {"name": "Tối giản", "top": "#FFFFFF", "bottom": "#EEF0F3", "accent": "#141414", "text": "#141414",
     "muted": "#5E636B", "on_accent": "#FFFFFF"},
    {"name": "Xanh biển", "top": "#EEF5FF", "bottom": "#CFE0FF", "accent": "#2563EB", "text": "#0F1B33",
     "muted": "#4A5B7A", "on_accent": "#FFFFFF"},
]


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_MEDIUM), size)


def enhance(path: str) -> Image.Image:
    """Chỉnh ảnh gốc cho đẹp hơn mà không làm sai màu sản phẩm."""
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    if max(im.size) < 1000:                                  # ảnh nhỏ: phóng to cho nét khi in lên khung lớn
        scale = 1000 / max(im.size)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=0.5, preserve_tone=True)
    im = ImageEnhance.Color(im).enhance(1.07)
    im = ImageEnhance.Contrast(im).enhance(1.03)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=3))


def _gradient(size, top, bottom) -> Image.Image:
    """Nền chuyển màu dọc."""
    col = Image.new("RGB", (1, 2))
    col.putpixel((0, 0), ImageColor.getrgb(top))
    col.putpixel((0, 1), ImageColor.getrgb(bottom))
    return col.resize(size, Image.BILINEAR)


def _rounded(im: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *im.size), radius, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def _paste_card(canvas: Image.Image, photo: Image.Image, box: tuple, radius: int = 40) -> None:
    """Ảnh sản phẩm trên thẻ trắng bo góc, có bóng đổ."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    card = Image.new("RGB", (w, h), "white")
    fitted = ImageOps.contain(photo, (w - 24, h - 24), Image.LANCZOS)
    card.paste(fitted, ((w - fitted.width) // 2, (h - fitted.height) // 2))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x0 + 6, y0 + 18, x1 + 6, y1 + 18), radius, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(_rounded(card, radius), (x0, y0))


def _wrap(draw, text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textlength(test, font=fnt) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    return lines + ([cur] if cur else [])


def _fit_text(draw, text: str, max_w: int, max_lines: int, size: int, min_size: int = 30, bold=True):
    """Chữ to nhất vừa khung (tối đa max_lines dòng)."""
    while size > min_size:
        fnt = font(size, bold)
        lines = _wrap(draw, text, fnt, max_w)
        if len(lines) <= max_lines and all(draw.textlength(ln, font=fnt) <= max_w for ln in lines):
            return fnt, lines
        size -= 2
    fnt = font(min_size, bold)
    lines = _wrap(draw, text, fnt, max_w)[:max_lines]
    return fnt, lines


def _draw_lines(draw, lines, fnt, x, y, fill, align="left", max_w=0, spacing=1.18) -> int:
    lh = int(fnt.size * spacing)
    for line in lines:
        lx = x if align == "left" else x + (max_w - draw.textlength(line, font=fnt)) / 2
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += lh
    return y


def _pill(draw, xy, text, fnt, bg, fg, pad=(28, 14), anchor_right=False) -> tuple:
    x, y = xy
    w = draw.textlength(text, font=fnt) + pad[0] * 2
    h = fnt.size + pad[1] * 2
    if anchor_right:
        x -= w
    draw.rounded_rectangle((x, y, x + w, y + h), h // 2, fill=bg)
    draw.text((x + pad[0], y + pad[1] - fnt.size * 0.12), text, font=fnt, fill=fg)
    return (x, y, x + w, y + h)


def _check(draw, cx, cy, r, bg, fg) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=bg)
    draw.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.48, cy - r * 0.36)],
              fill=fg, width=max(3, r // 4), joint="curve")


def _price(product: dict) -> str:
    p = product.get("price") or 0
    return f"{int(p):,}đ".replace(",", ".") if p else ""


def render_slide(photo: Image.Image, kind: str, brief: dict, product: dict, theme: dict,
                 size=FEED, index: int = 0, total: int = 1, point: str = "", mirror: bool = False) -> Image.Image:
    """Dựng 1 ảnh. kind: cover | feature | cta."""
    W, H = size
    tall = H / W > 1.5                                       # khung 9:16 cho video
    pad = 100 if tall else 72                               # video phóng to 6%: chừa lề để chữ không bị cắt
    canvas = _gradient(size, theme["top"], theme["bottom"]).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    # vòng tròn trang trí nhẹ
    deco = Image.new("RGBA", size, (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    cx = W - 120 if not mirror else 120
    dd.ellipse((cx - 330, -260, cx + 330, 400), fill=(*ImageColor.getrgb(theme["accent"]), 28))
    dd.ellipse((W - cx - 260, H - 300, W - cx + 260, H + 220), fill=(*ImageColor.getrgb(theme["accent"]), 20))
    canvas.alpha_composite(deco)
    draw = ImageDraw.Draw(canvas)
    text_w = W - pad * 2
    price = _price(product)

    if kind == "cover":
        y = pad + (60 if tall else 0)
        if brief.get("badge"):
            _pill(draw, (pad, y), brief["badge"].upper(), font(30), theme["accent"], theme["on_accent"])
            y += 84
        fnt, lines = _fit_text(draw, brief["headline"], text_w, 3 if tall else 2, 84 if tall else 72)
        y = _draw_lines(draw, lines, fnt, pad, y, theme["text"])
        if brief.get("subheadline"):
            sf, sl = _fit_text(draw, brief["subheadline"], text_w, 1, 38, 28, bold=False)
            y = _draw_lines(draw, sl, sf, pad, y + 6, theme["muted"])
        bottom_space = 190 if price else 90
        box = (pad, y + 30, W - pad, H - pad - bottom_space - (160 if tall else 0))
        _paste_card(canvas, photo, box)
        draw = ImageDraw.Draw(canvas)
        if price:
            pf = font(56)
            yb = box[3] + 50
            _pill(draw, (W - pad if mirror else pad, yb), f"Chỉ từ {price}", pf, theme["accent"],
                  theme["on_accent"], pad=(36, 20), anchor_right=mirror)
    elif kind == "feature":
        top = pad + (160 if tall else 0)
        card_h = int(H * (0.56 if tall else 0.6))
        box = (pad, top, W - pad, top + card_h)
        _paste_card(canvas, photo, box)
        draw = ImageDraw.Draw(canvas)
        y = box[3] + 56
        num_f = font(64)
        draw.text((pad, y - 8), f"{index:02d}", font=num_f, fill=theme["accent"])
        nx = pad + draw.textlength(f"{index:02d}", font=num_f) + 28
        pf, pl = _fit_text(draw, point or brief["headline"], W - pad - nx, 3, 60, 34)
        _draw_lines(draw, pl, pf, nx, y, theme["text"])
        hf, hl = _fit_text(draw, brief["headline"], text_w, 1, 30, 22, bold=False)
        _draw_lines(draw, hl, hf, pad, H - pad - 40 - (120 if tall else 0), theme["muted"])
    else:  # cta
        top = pad + (100 if tall else 0)
        card_h = int(H * (0.4 if tall else 0.38))
        cw = int(W * 0.62)
        x0 = pad if not mirror else W - pad - cw
        _paste_card(canvas, photo, (x0, top, x0 + cw, top + card_h))
        draw = ImageDraw.Draw(canvas)
        if price:
            side_x = x0 + cw + 30 if not mirror else pad
            side_w = W - pad - side_x if not mirror else x0 - 30 - pad
            lf = font(30, bold=False)
            draw.text((side_x, top + 40), "Giá chỉ từ", font=lf, fill=theme["muted"])
            pf, pl = _fit_text(draw, price, side_w, 1, 58, 26)
            _draw_lines(draw, pl, pf, side_x, top + 84, theme["accent"])
        y = top + card_h + 60
        tf, tl = _fit_text(draw, brief["headline"], text_w, 2, 54, 34)
        y = _draw_lines(draw, tl, tf, pad, y, theme["text"]) + 18
        pf = font(40, bold=False)
        for p in brief["points"][:4]:
            _check(draw, pad + 24, y + 26, 24, theme["accent"], theme["on_accent"])
            lines = _wrap(draw, p, pf, text_w - 80)[:2]
            y = _draw_lines(draw, lines, pf, pad + 72, y, theme["text"]) + 14
        bf = font(44)
        bh = 44 + 56
        by = min(H - pad - bh - (120 if tall else 0), y + 30)
        draw.rounded_rectangle((pad, by, W - pad, by + bh), bh // 2, fill=theme["accent"])
        cta = brief["cta"]
        cf, cl = _fit_text(draw, cta, text_w - 80, 1, 44, 26)
        draw.text(((W - draw.textlength(cl[0], font=cf)) / 2, by + (bh - cf.size) / 2 - cf.size * 0.12),
                  cl[0], font=cf, fill=theme["on_accent"])

    # chấm chỉ số trang
    if total > 1 and not tall:
        r, gap = 7, 26
        sx = (W - (total - 1) * gap) / 2
        for i in range(total):
            c = theme["accent"] if i == index else theme["muted"]
            draw.ellipse((sx + i * gap - r, H - 36 - r, sx + i * gap + r, H - 36 + r), fill=c)
    return canvas.convert("RGB")


def plan_slides(brief: dict, n_photos: int, want: int = 5) -> list[tuple[str, int, str]]:
    """(kind, chỉ số ảnh gốc, điểm nổi bật) cho 3-5 ảnh."""
    order = brief["image_order"] or list(range(n_photos))
    points = brief["points"] or [brief["headline"]]
    n = max(3, min(want, len(points) + 2, 5))
    slides = [("cover", order[0], "")]
    for i in range(n - 2):
        slides.append(("feature", order[(i + 1) % len(order)], points[i % len(points)]))
    slides.append(("cta", order[(n - 1) % len(order)] if len(order) > 1 else order[0], ""))
    return slides


def render_set(photos: list[Image.Image], brief: dict, product: dict, variant: int, size=FEED,
               theme_index: int | None = None) -> list[Image.Image]:
    """Bộ 3-5 ảnh cho 1 phiên bản. Phiên bản khác nhau: màu, bố cục trái/phải, thứ tự ảnh."""
    theme = THEMES[(theme_index if theme_index is not None else variant) % len(THEMES)]
    mirror = variant % 2 == 1
    order = brief["image_order"]
    if variant and len(order) > 1:                          # đổi ảnh bìa giữa các phiên bản
        k = variant % len(order)
        brief = {**brief, "image_order": order[k:] + order[:k]}
    slides = plan_slides(brief, len(photos))
    return [render_slide(photos[src], kind, brief, product, theme, size, idx, len(slides), point, mirror)
            for idx, (kind, src, point) in enumerate(slides)]
