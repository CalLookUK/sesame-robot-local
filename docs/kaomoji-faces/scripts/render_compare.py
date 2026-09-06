#!/usr/bin/env python3
"""Rasterize kaomoji test strings with Unifont vs a Noto stack, simulating
the actual 128x64 monochrome SSD1306 OLED output (1-bit threshold, no AA)."""

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

UNIFONT = "/usr/share/fonts/opentype/unifont/unifont.otf"
NOTO_SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
NOTO_CJK_JP = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
NOTO_SYM = "/usr/share/fonts/truetype/noto/NotoSansSymbols-Regular.ttf"
NOTO_SYM2 = "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf"

DISPLAY_W, DISPLAY_H = 128, 64

TEST_STRINGS = [
    ("ascii",      "(^_^)"),
    ("latin-ext",  "(¬_¬)"),
    ("katakana",   "ヽ(°〇°)ノ"),
    ("complex",    "(づ ̄ ³ ̄)づ"),
]

def cmap_has(font_path, char, font_index=0):
    try:
        tt = TTFont(font_path, fontNumber=font_index, lazy=True)
        cmap = tt.getBestCmap()
        return ord(char) in cmap
    except Exception:
        return False

def build_noto_fallback_chain():
    return [NOTO_SANS, NOTO_CJK_JP, NOTO_SYM, NOTO_SYM2]

def pick_font_for_char(char, chain, size, cache):
    for path in chain:
        key = (path, size)
        if cmap_has(path, char):
            if key not in cache:
                cache[key] = ImageFont.truetype(path, size)
            return cache[key], path
    key = (chain[0], size)
    if key not in cache:
        cache[key] = ImageFont.truetype(chain[0], size)
    return cache[key], chain[0] + " (MISSING GLYPH)"

def render_string_mixed(s, chain, size, cache):
    """Render each char with the first font in the chain that has the glyph,
    concatenated left-to-right, returned as an RGBA image sized to content."""
    imgs = []
    total_w = 0
    max_h = 0
    used_fonts = set()
    for ch in s:
        font, used_path = pick_font_for_char(ch, chain, size, cache)
        used_fonts.add(used_path)
        bbox = font.getbbox(ch)
        w = max(font.getlength(ch), 1)
        tmp = Image.new("L", (int(w) + 4, size * 2), 0)
        d = ImageDraw.Draw(tmp)
        d.text((2, size // 2), ch, font=font, fill=255, anchor="lm")
        imgs.append(tmp)
        total_w += tmp.width
        max_h = max(max_h, tmp.height)
    canvas = Image.new("L", (total_w, max_h), 0)
    x = 0
    for im in imgs:
        canvas.paste(im, (x, 0))
        x += im.width
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    return canvas, used_fonts

def render_string_single(s, font_path, size):
    font = ImageFont.truetype(font_path, size)
    bbox = font.getbbox(s)
    w = int(font.getlength(s)) + 4
    h = size * 2
    canvas = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(canvas)
    d.text((2, size // 2), s, font=font, fill=255, anchor="lm")
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
    return canvas

def to_oled_sim(glyph_img, threshold=110):
    """Fit glyph onto a 128x64 canvas, threshold to pure 1-bit (no AA),
    matching what actually gets pushed to the SSD1306 buffer."""
    canvas = Image.new("L", (DISPLAY_W, DISPLAY_H), 0)
    gw, gh = glyph_img.size
    scale = min((DISPLAY_W - 8) / gw, (DISPLAY_H - 8) / gh, 1.0)
    if scale < 1.0:
        glyph_img = glyph_img.resize((max(1, int(gw * scale)), max(1, int(gh * scale))), Image.LANCZOS)
        gw, gh = glyph_img.size
    bw = glyph_img.point(lambda p: 255 if p >= threshold else 0)
    x = (DISPLAY_W - gw) // 2
    y = (DISPLAY_H - gh) // 2
    canvas.paste(bw, (x, y))
    return canvas

def main():
    noto_chain = build_noto_fallback_chain()
    cache = {}
    size = 24  # target glyph pixel size before fitting to 64px-tall display

    rows = []
    for label, s in TEST_STRINGS:
        uni_glyph = render_string_single(s, UNIFONT, size)
        uni_oled = to_oled_sim(uni_glyph)

        noto_glyph, used = render_string_mixed(s, noto_chain, size, cache)
        noto_oled = to_oled_sim(noto_glyph)
        used_names = ", ".join(sorted(p.split("/")[-1] for p in used))

        rows.append((label, s, uni_oled, noto_oled, used_names))

    # Compose comparison sheet
    pad = 20
    label_w = 170
    col_w = DISPLAY_W * 3  # upscale each 128x64 sim 3x for visibility
    col_h = DISPLAY_H * 3
    row_h = col_h + 50
    sheet_w = label_w + col_w * 2 + pad * 3
    sheet_h = row_h * len(rows) + 80

    sheet = Image.new("RGB", (sheet_w, sheet_h), (30, 30, 30))
    d = ImageDraw.Draw(sheet)
    try:
        label_font = ImageFont.truetype(NOTO_SANS, 20)
        small_font = ImageFont.truetype(NOTO_SANS, 14)
    except Exception:
        label_font = ImageFont.load_default()
        small_font = label_font

    d.text((pad, 15), "Unifont", font=label_font, fill=(255, 255, 255))
    d.text((label_w + pad + col_w // 2 - 40, 15), "Unifont", font=label_font, fill=(255, 255, 255))
    d.text((label_w + pad * 2 + col_w + col_w // 2 - 90, 15), "Noto (Sans+CJK+Symbols)", font=label_font, fill=(255, 255, 255))

    y = 55
    for label, s, uni_oled, noto_oled, used_names in rows:
        d.text((pad, y + col_h // 2 - 10), f"{label}\n{s}", font=label_font, fill=(200, 200, 200))

        uni_up = uni_oled.resize((col_w, col_h), Image.NEAREST).convert("RGB")
        noto_up = noto_oled.resize((col_w, col_h), Image.NEAREST).convert("RGB")

        ux = label_w + pad
        sheet.paste(uni_up, (ux, y))
        nx = label_w + pad * 2 + col_w
        sheet.paste(noto_up, (nx, y))

        d.text((nx, y + col_h + 4), f"fonts used: {used_names}", font=small_font, fill=(150, 150, 150))

        y += row_h

    out_path = "/tmp/claude-0/-home-user-sesame-robot-local/7ccd3d44-7388-50a7-afa7-f8721113f68b/scratchpad/kaomoji_font_comparison.png"
    sheet.save(out_path)
    print("saved", out_path)

if __name__ == "__main__":
    main()
