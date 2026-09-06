# Continuation Prompt

Paste this into Claude Code in VS Code, after checking out (or pulling)
the `claude/sesame-bot-faces-idea-9o9ftw` branch.

---

Read docs/kaomoji-faces/README.md in full - it's a handoff doc from a prior
research session on replacing Sesame's bitmap OLED faces with kaomoji text
faces. It covers: the current face-bitmaps.h/setFace() architecture, why
Unifont is the right font for the existing mono 128x64 SSD1306 boards, why
Noto is the right font for the new colour 96x64 SSD1331 board on ESP32-S3
(and why that requires swapping the render pipeline to LVGL + Arduino_GFX,
since Adafruit_GFX can't anti-alias even on colour panels), and the
combining-diacritics bug to avoid when picking kaomoji strings. Reference
images are in docs/kaomoji-faces/images/, and the Python scripts used to
generate them (including a glyph-coverage checker) are in
docs/kaomoji-faces/scripts/.

Start on the "Open items / next steps" checklist at the bottom of that
README, in order:

1. Help me finalize a consolidated kaomoji shortlist (the existing
   face-bitmaps.h has 46 arrays but many are near-duplicate frames of the
   same expression - use images/sesame_faces_reference.png to figure out
   the real distinct-expression count).
2. Run the glyph-coverage check (pattern is in scripts/render_compare_noto2.py)
   against that shortlist to pin down the minimal Noto font set needed for
   the SSD1331 path, and the minimal Unifont subset for the SSD1306 path.
3. Then help me scope the actual firmware changes: the Unifont GFXfont
   subset for the mono boards, and the LVGL + Arduino_GFX SSD1331
   integration for the new colour board, per the architecture plan in the
   README - without breaking the existing /api/command face-only contract.

I have the physical SSD1331 hardware in hand now, so once we've got code
you can tell me what to flash and test.
