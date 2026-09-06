#!/usr/bin/env python3
"""Rasterize kaomoji with Unifont vs Noto for a 96x64 COLOR display,
keeping anti-aliasing (no 1-bit threshold) and adding a colour tint,
simulating something like an SSD1331-class RGB OLED/TFT."""

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

UNIFONT = "/usr/share/fonts/opentype/unifont/unifont.otf"
NOTO_SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
NOTO_CJK_JP = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
NOTO_SYM = "/usr/share/fonts/truetype/noto/NotoSansSymbols-Regular.ttf"
NOTO_SYM2 = "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf"

DISPLAY_W, DISPLAY_H = 96, 64

TEST_STRINGS = [
    ("ascii",     "(^_^)",        (255, 255, 255)),
    ("happy",     "(^o^)",        (255, 200, 60)),
    ("katakana",  "ヽ(°〇°)ノ",    (80, 220, 255)),
    ("love",      "(♥‿♥)",        (255, 90, 140)),
]

def cmap_has(font_path, char, font_index=0):
    try:
        tt = TTFont(font_path, fontNumber=font_index, lazy=True)
        return ord(char) in tt.getBestCmap()
    except Exception:
        return False

NOTO_CHAIN = [NOTO_SANS, NOTO_CJK_JP, NOTO_SYM, NOTO_SYM2]

def pick_font(char, chain, size, cache):
    for path in chain:
        if cmap_has(char=char, font_path=path):
            key = (path, size)
            if key not in cache:
                cache[key] = ImageFont.truetype(path, size)
            return cache[key]
    key = (chain[0], size)
    if key not in cache:
        cache[key] = ImageFont.truetype(chain[0], size)
    return cache[key]

def render_mixed_alpha(s, chain, size, cache):
    imgs = []
    for ch in s:
        font = pick_font(ch, chain, size, cache)
        w = max(int(font.getlength(ch)), 1)
        tmp = Image.new("L", (w + 4, size * 2), 0)
        d = ImageDraw.Draw(tmp)
        d.text((2, size // 2), ch, font=font, fill=255, anchor="lm")
        imgs.append(tmp)
    total_w = sum(im.width for im in imgs)
    max_h = max(im.height for im in imgs)
    canvas = Image.new("L", (total_w, max_h), 0)
    x = 0
    for im in imgs:
        canvas.paste(im, (x, 0))
        x += im.width
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas

def render_single_alpha(s, font_path, size):
    font = ImageFont.truetype(font_path, size)
    w = int(font.getlength(s)) + 4
    canvas = Image.new("L", (w, size * 2), 0)
    d = ImageDraw.Draw(canvas)
    d.text((2, size // 2), s, font=font, fill=255, anchor="lm")
    bbox = canvas.getbbox()
    return canvas.crop(bbox) if bbox else canvas

def to_color_oled_sim(alpha_glyph, color):
    """Fit onto 96x64, keep antialiasing (alpha as brightness), tint colour."""
    canvas = Image.new("RGB", (DISPLAY_W, DISPLAY_H), (0, 0, 0))
    gw, gh = alpha_glyph.size
    scale = min((DISPLAY_W - 6) / gw, (DISPLAY_H - 6) / gh, 1.0)
    if scale < 1.0:
        alpha_glyph = alpha_glyph.resize(
            (max(1, int(gw * scale)), max(1, int(gh * scale))), Image.LANCZOS
        )
        gw, gh = alpha_glyph.size
    tint = Image.new("RGB", (gw, gh), color)
    x = (DISPLAY_W - gw) // 2
    y = (DISPLAY_H - gh) // 2
    canvas.paste(tint, (x, y), alpha_glyph)
    return canvas

def main():
    cache = {}
    size = 26

    rows = []
    for label, s, color in TEST_STRINGS:
        uni_alpha = render_single_alpha(s, UNIFONT, size)
        uni_img = to_color_oled_sim(uni_alpha, color)

        noto_alpha = render_mixed_alpha(s, NOTO_CHAIN, size, cache)
        noto_img = to_color_oled_sim(noto_alpha, color)

        rows.append((label, s, uni_img, noto_img))

    pad = 20
    label_w = 150
    upscale = 5
    col_w = DISPLAY_W * upscale
    col_h = DISPLAY_H * upscale
    row_h = col_h + 30
    sheet_w = label_w + col_w * 2 + pad * 3
    sheet_h = row_h * len(rows) + 70

    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 22))
    d = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(NOTO_SANS, 20)

    d.text((label_w + pad + col_w // 2 - 40, 15), "Unifont (AA, colour)", font=label_font, fill=(255, 255, 255))
    d.text((label_w + pad * 2 + col_w + col_w // 2 - 100, 15), "Noto (AA, colour)", font=label_font, fill=(255, 255, 255))

    y = 55
    for label, s, uni_img, noto_img in rows:
        d.text((pad, y + col_h // 2 - 10), f"{label}", font=label_font, fill=(200, 200, 200))
        uni_up = uni_img.resize((col_w, col_h), Image.NEAREST)
        noto_up = noto_img.resize((col_w, col_h), Image.NEAREST)
        sheet.paste(uni_up, (label_w + pad, y))
        sheet.paste(noto_up, (label_w + pad * 2 + col_w, y))
        y += row_h

    out_path = "/tmp/claude-0/-home-user-sesame-robot-local/7ccd3d44-7388-50a7-afa7-f8721113f68b/scratchpad/kaomoji_color_comparison.png"
    sheet.save(out_path)
    print("saved", out_path)

if __name__ == "__main__":
    main()
