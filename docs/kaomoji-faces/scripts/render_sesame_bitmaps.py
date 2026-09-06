#!/usr/bin/env python3
"""Decode every epd_bitmap_* PROGMEM array in firmware/face-bitmaps.h into
a real 128x64 1-bit image, and lay them all out as a labeled reference sheet."""

import re
from PIL import Image, ImageDraw, ImageFont

SRC = "/home/user/sesame-robot-local/firmware/face-bitmaps.h"
FONT = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

W, H = 128, 64
BYTES_PER_ROW = W // 8  # 16
FRAME_BYTES = BYTES_PER_ROW * H  # 1024

def parse_arrays(text):
    pattern = re.compile(
        r"const unsigned char epd_bitmap_([A-Za-z0-9_]+)\s*\[\]\s*PROGMEM\s*=\s*\{(.*?)\};",
        re.DOTALL,
    )
    out = {}
    for m in pattern.finditer(text):
        name = m.group(1)
        body = m.group(2)
        hex_bytes = re.findall(r"0x([0-9A-Fa-f]{2})", body)
        data = bytes(int(h, 16) for h in hex_bytes)
        out[name] = data
    return out

def bitmap_to_image(data):
    img = Image.new("1", (W, H), 0)
    px = img.load()
    n = min(len(data), FRAME_BYTES)
    for row in range(H):
        for col_byte in range(BYTES_PER_ROW):
            idx = row * BYTES_PER_ROW + col_byte
            if idx >= n:
                continue
            byte = data[idx]
            for bit in range(8):
                x = col_byte * 8 + bit
                on = (byte >> (7 - bit)) & 1
                if on:
                    px[x, row] = 1
    return img

def main():
    with open(SRC, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    arrays = parse_arrays(text)
    print(f"parsed {len(arrays)} bitmap arrays")

    names = sorted(arrays.keys())

    cols = 6
    cell_w, cell_h = W * 2 + 10, H * 2 + 40
    rows = (len(names) + cols - 1) // cols
    sheet_w = cols * cell_w + 20
    sheet_h = rows * cell_h + 60

    sheet = Image.new("RGB", (sheet_w, sheet_h), (25, 25, 28))
    d = ImageDraw.Draw(sheet)
    title_font = ImageFont.truetype(FONT, 22)
    label_font = ImageFont.truetype(FONT, 14)

    d.text((15, 15), "Sesame face-bitmaps.h reference (all 46 frames, real decode)", font=title_font, fill=(255, 255, 255))

    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x0 = 10 + c * cell_w
        y0 = 55 + r * cell_h

        data = arrays[name]
        if len(data) < FRAME_BYTES:
            note = f"({len(data)}B, short)"
        else:
            note = ""
        img = bitmap_to_image(data).convert("RGB")
        img_big = img.resize((W * 2, H * 2), Image.NEAREST)
        sheet.paste(img_big, (x0, y0))
        d.text((x0, y0 + H * 2 + 4), f"{name} {note}", font=label_font, fill=(220, 220, 220))

    out_path = "/tmp/claude-0/-home-user-sesame-robot-local/7ccd3d44-7388-50a7-afa7-f8721113f68b/scratchpad/sesame_faces_reference.png"
    sheet.save(out_path)
    print("saved", out_path)

if __name__ == "__main__":
    main()
