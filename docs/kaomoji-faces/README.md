# Kaomoji Faces - Research Handoff

Summary of an exploratory session on replacing/augmenting Sesame's bitmap
faces with text-based kaomoji. Written up so work can continue in
VS Code / Claude Code from a clean context. Reference images and the
scripts that generated them are in this folder.

## The idea

Replace the OLED bitmap-animation face system with kaomoji (text faces
like `(^_^)`, `ヽ(°〇°)ノ`) rendered live from a font, instead of hand-drawn
PROGMEM bitmaps. Motivation: cheaper to add new expressions (edit a
string vs. draw+convert a bitmap), much smaller flash footprint per
face, and it opens the door to fully custom user-typed faces over the
existing face-only API.

**Key validating observation**: the existing bitmap faces already lean
kaomoji in style - hand-drawn `w`-mouths, dot/circle eyes, `ﾟ` marks
(see `images/sesame_faces_reference.png`, decoded directly from the
real PROGMEM byte data in `firmware/face-bitmaps.h` - all 46 arrays).
Several of those 46 are near-duplicate frames (blink states, talk-open
mouth variants of the same base expression), so the real number of
distinct expressions to design kaomoji for is smaller than 46.

## Current firmware architecture (as of this session)

- `firmware/face-bitmaps.h`: `FACE_LIST` X-macro generates a
  `FaceEntry` table (name -> frame array pointer + frame count) from
  raw 1-bit PROGMEM bitmaps, 1024 bytes each (128x64 / 8).
- `firmware/sesame-firmware-main.ino`: `setFace(name)` looks up the
  table (falls back to `"default"`), `updateAnimatedFace()` steps
  frames on a timer per-face FPS (`faceFpsEntries[]`), with
  loop/once/boomerang modes (`FaceAnimMode`).
- Display today: `Adafruit_SSD1306`, 128x64, monochrome, I2C
  (`sesame-firmware-main.ino:8,25-47`). Same code path across every
  board variant (S2 Mini, Distro V1/V2/V3) - only I2C pins differ per
  board.
- API: `POST /api/command` supports a face-only update
  (`{"face":"happy"}`), separate from movement commands - this is the
  hook the Companion App / voice integration already uses, and it
  should stay stable across this migration.

## Font research findings

Two target displays, two different answers - not one global font choice.

### Mono 128x64 SSD1306 (existing boards)

- Compared **GNU Unifont** vs a **Noto Sans stack** rasterized and
  thresholded to real 1-bit output. See
  `images/kaomoji_font_comparison.png`.
- At this resolution, once thresholded to 1-bit, the two are visually
  near-identical. Noto is marginally smoother in a few spots but not a
  meaningful win.
- Unifont covers everything (katakana, box drawing, Latin extended,
  general symbols) from **one font file**. Noto needed a multi-font
  fallback chain even for simple strings (`NotoSans-Regular` +
  `NotoSansCJK-Regular.ttc` for katakana).
- **Recommendation: Unifont for the mono board.** Simpler (one file,
  no fallback chain), same legibility once thresholded, keeps the
  existing `Adafruit_GFX`/`GFXfont` pipeline unchanged.

### Colour 96x64 panel (new ESP32-S3 board variant) - confirmed SSD1331

- Same test strings re-rendered **without** the 1-bit threshold (AA
  preserved) plus a colour tint, simulating an RGB565-capable panel.
  See `images/kaomoji_color_comparison.png`.
- Here Noto's vector curves clearly win - Unifont's "o"/"〇"/♥ glyphs
  are blocky/octagonal (they're literally traced from an 8x16 pixel
  grid, so AA can't add curvature that was never there). Noto's
  circles and hearts are genuinely smooth.
- Expanded coverage test with the user's requested set (`ಠ_ಠ`,
  `(・ω・)`, `（≧∇≦）`) plus a few classic extras (shrug, table-flip,
  sunglasses) - see `images/kaomoji_noto_showcase.png`. All resolved,
  but it took **six separate Noto font files**: `NotoSans`,
  `NotoSansCJK-JP`, `NotoSansSymbols`, `NotoSansSymbols2`,
  `NotoSansKannada`, `NotoSansMath` (the last just for the `⌐` in the
  sunglasses face).
- **Takeaway**: going broad with Noto works, but each "exotic" glyph
  risks pulling in another font subfamily. Before finalizing, audit
  the actual shortlist of kaomoji you intend to ship and see how many
  font sources it really needs - aim to consolidate to 2-3, not
  accumulate one per exotic character.

### Cross-cutting bug, independent of font choice

Kaomoji using **combining diacritics** (e.g. the macron `` ̄ `` in
`(づ ̄ ³ ̄)づ`) render broken in both fonts under simple sequential glyph
rendering - the mark shows as a floating dash next to the character
instead of composed above it. This isn't a font-rasterization artifact:
`Adafruit_GFX`'s `drawChar()`/`print()` draws each codepoint
independently and advances the cursor, with **no mark-positioning
logic**, so this will reproduce on real hardware regardless of font.
**Curate the kaomoji set to precomposed/spacing characters only** -
plenty of good ones exist (`¬_¬`, `°_°`, `ヽ(°〇°)ノ`, `ಠ_ಠ`, `(・ω・)`,
`（≧∇≦）` all render clean).

## The bigger architectural decision: real AA needs a render-pipeline swap

Colour alone does not get you anti-aliasing. `Adafruit_GFX`/`GFXfont`
draws hard 1-bit glyph bitmaps regardless of the panel's colour depth.
To get genuine AA text on the SSD1331 you need to replace the
rendering layer for that board variant:

1. **Panel driver**: SSD1331 is SPI (not I2C like every current
   board) - needs its own wiring (MOSI/SCK/CS/DC/RST) on the ESP32-S3.
   `Arduino_GFX` (moononournation) is the recommended low-level driver
   - it has documented LVGL bindings for SSD1331.
2. **Add LVGL** as a dependency, `lv_conf.h` tuned for the S3. Memory
   is a non-issue: a 96x64 RGB565 framebuffer is 12KB, ~24KB
   double-buffered - trivial on this MCU, no PSRAM required.
3. **Re-run font conversion in LVGL's format**, not Adafruit's
   `fontconvert` - same curated Noto glyph subset, but through LVGL's
   font converter, targeting 4bpp (the usual legibility/flash-size
   sweet spot). This is what actually delivers the AA - LVGL's font
   format supports real multi-bit alpha, `GFXfont` doesn't.
4. **Replace face-rendering call sites**: `updateFaceBitmap()` /
   `display.drawBitmap()` (`sesame-firmware-main.ino:608-610, 835`)
   become an LVGL label update. `setFace()`'s public contract stays
   the same - `/api/command {"face":"happy"}` keeps working, it just
   resolves to a kaomoji string + colour instead of a bitmap-frame
   array.
5. **Integrate LVGL's tick/`lv_timer_handler()`** into the existing
   non-blocking loop alongside `pressingCheck()`,
   `server.handleClient()`, `dnsServer.processNextRequest()`. Should be
   fine at this screen size/refresh rate, but verify no added input
   latency.
6. **Compile-time branch per board variant**: mono boards (S2 Mini,
   Distro V1/V2/V3-mono) keep the existing `Adafruit_SSD1306` + Unifont
   bitmap path untouched; only the new colour ESP32-S3 variant gets
   the LVGL path. Same pattern as the existing per-board pin `#define`
   blocks.

## Open items / next steps

- [ ] Confirm exact SSD1331 module wiring (which GPIOs on the S3 for
      MOSI/SCK/CS/DC/RST) - needs the physical board in hand.
- [ ] Finalize the kaomoji shortlist (consolidate near-duplicate
      expressions per the reference sheet), then re-run the glyph
      coverage check (`scripts/render_compare_noto2.py` has the
      pattern - `cmap_has()` + a font-chain list) to pin down the
      minimal Noto font set needed.
- [ ] Decide the mono-path font subset (Unifont, single file) and
      generate the `GFXfont` subset via Adafruit's `fontconvert`.
- [ ] Stand up the LVGL + `Arduino_GFX` SSD1331 driver, verify the
      flush callback, confirm no regression to the non-blocking
      control loop.
- [ ] Generate the LVGL font from the finalized Noto subset (4bpp).
- [ ] Wire `setFace()` to the new render path for the colour board
      variant behind a compile-time flag; keep the API contract
      unchanged.
- [ ] Hardware bring-up and visual verification on the real SSD1331 -
      this can't be validated remotely.

## Files in this folder

- `images/kaomoji_font_comparison.png` - Unifont vs Noto, mono 1-bit,
  128x64 simulation.
- `images/kaomoji_color_comparison.png` - Unifont vs Noto, AA + colour,
  96x64 simulation.
- `images/kaomoji_noto_showcase.png` - expanded Noto glyph-coverage
  test (`ಠ_ಠ`, `(・ω・)`, `（≧∇≦）`, shrug, table-flip, sunglasses).
- `images/sesame_faces_reference.png` - all 46 existing
  `face-bitmaps.h` arrays, decoded directly from PROGMEM bytes.
- `scripts/render_compare.py` - mono 1-bit Unifont-vs-Noto renderer.
- `scripts/render_compare_color.py` - colour/AA Unifont-vs-Noto
  renderer.
- `scripts/render_compare_noto2.py` - Noto-only glyph-coverage
  showcase renderer, includes the `cmap_has()`/font-chain pattern
  for auditing coverage against a candidate kaomoji list.
- `scripts/render_sesame_bitmaps.py` - parses and decodes every
  `epd_bitmap_*` PROGMEM array in `face-bitmaps.h` into real images.

All scripts need `Pillow` and `fonttools` (`pip install Pillow
fonttools`), plus the relevant font files on the system
(`fonts-noto-core`, `fonts-noto-cjk`, `fonts-noto-extra` via apt, and
`unifont` which is commonly preinstalled on Debian/Ubuntu-based
systems, otherwise `apt install fonts-noto fonts-noto-cjk` and grab
`unifont.otf` from the GNU Unifont project).
