#!/usr/bin/env python3
"""Noto-only render pass for the requested kaomoji + a few extras, on the
96x64 colour display simulation (AA, no threshold)."""

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

NOTO_SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
NOTO_CJK_JP = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
NOTO_SYM = "/usr/share/fonts/truetype/noto/NotoSansSymbols-Regular.ttf"
NOTO_SYM2 = "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf"
NOTO_KANNADA = "/usr/share/fonts/truetype/noto/NotoSansKannada-Regular.ttf"
NOTO_MATH = "/usr/share/fonts/truetype/noto/NotoSansMath-Regular.ttf"

NOTO_CHAIN = [NOTO_SANS, NOTO_CJK_JP, NOTO_SYM, NOTO_SYM2, NOTO_KANNADA, NOTO_MATH]

DISPLAY_W, DISPLAY_H = 96, 64

TEST_STRINGS = [
    ("disapproval", "ಠ_ಠ",        (255, 120, 120)),
    ("content",     "(・ω・)",     (120, 220, 160)),
    ("overjoyed",   "（≧∇≦）",     (255, 210, 80)),
    ("shrug",       "¯\\_(ツ)_/¯", (200, 200, 255)),
    ("tableflip",   "(╯°□°）╯",    (255, 140, 60)),
    ("sunglasses",  "(⌐■_■)",      (150, 255, 150)),
]

def cmap_has(font_path, char, font_index=0):
    try:
        tt = TTFont(font_path, fontNumber=font_index, lazy=True)
        return ord(char) in tt.getBestCmap()
    except Exception:
        return False

def pick_font(char, size, cache, missing):
    for path in NOTO_CHAIN:
        if cmap_has(path, char):
            key = (path, size)
            if key not in cache:
                cache[key] = ImageFont.truetype(path, size)
            return cache[key]
    missing.add(char)
    key = (NOTO_CHAIN[0], size)
    if key not in cache:
        cache[key] = ImageFont.truetype(NOTO_CHAIN[0], size)
    return cache[key]

def render_mixed_alpha(s, size, cache, missing):
    imgs = []
    for ch in s:
        font = pick_font(ch, size, cache, missing)
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

def to_color_oled_sim(alpha_glyph, color):
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
    missing = set()
    size = 22

    rows = []
    for label, s, color in TEST_STRINGS:
        alpha = render_mixed_alpha(s, size, cache, missing)
        img = to_color_oled_sim(alpha, color)
        rows.append((label, s, img))

    pad = 20
    label_w = 260
    upscale = 6
    col_w = DISPLAY_W * upscale
    col_h = DISPLAY_H * upscale
    row_h = col_h + 20
    sheet_w = label_w + col_w + pad * 2
    sheet_h = row_h * len(rows) + 60

    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 22))
    d = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(NOTO_CJK_JP, 22)
    small_font = ImageFont.truetype(NOTO_CJK_JP, 16)

    d.text((pad, 15), "Noto stack, real 96x64 colour panel simulation", font=label_font, fill=(255, 255, 255))

    y = 50
    for label, s, img in rows:
        d.text((pad, y + col_h // 2 - 24), label, font=label_font, fill=(230, 230, 230))
        d.text((pad, y + col_h // 2 + 4), s, font=small_font, fill=(150, 150, 150))
        up = img.resize((col_w, col_h), Image.NEAREST)
        sheet.paste(up, (label_w + pad, y))
        y += row_h

    out_path = "/tmp/claude-0/-home-user-sesame-robot-local/7ccd3d44-7388-50a7-afa7-f8721113f68b/scratchpad/kaomoji_noto_showcase.png"
    sheet.save(out_path)
    print("saved", out_path)
    print("missing glyphs:", missing)

if __name__ == "__main__":
    main()
