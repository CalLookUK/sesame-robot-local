#!/usr/bin/env python3
"""Extract a PDF to page-tagged text in Sources/Text/ using pdftotext.

Usage: python3 tools/extract_pdf.py path/to/file.pdf [--force]
Writes Sources/Text/<slug>.txt with '=== page N ===' markers and reports pages
with little or no text (likely images/scans that need a visual read).
"""
import re
import subprocess
import sys
from pathlib import Path

LOW_TEXT_CHARS = 150
ROOT = Path(__file__).resolve().parent.parent


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "document"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    pdf = Path(args[0])
    if not pdf.is_file():
        sys.exit(f"not found: {pdf}")
    out = ROOT / "Sources" / "Text" / f"{slugify(pdf.stem)}.txt"
    if out.exists() and not force:
        sys.exit(f"{out} exists (use --force to overwrite)")
    try:
        raw = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=True, capture_output=True, text=True, errors="replace",
        ).stdout
    except FileNotFoundError:
        sys.exit("pdftotext not installed (apt install poppler-utils)")
    except subprocess.CalledProcessError as e:
        sys.exit(f"pdftotext failed: {e.stderr.strip()}")

    pages = raw.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    parts, low = [], []
    for i, text in enumerate(pages, 1):
        parts.append(f"=== page {i} ===\n{text.strip()}\n")
        if len(text.strip()) < LOW_TEXT_CHARS:
            low.append(i)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")

    total = sum(len(p.strip()) for p in pages)
    print(f"text:  {out.relative_to(ROOT)}")
    print(f"pages: {len(pages)}   chars: {total}")
    if low:
        print(f"low-text pages ({len(low)}): {', '.join(map(str, low))}")
        print("  -> read these visually (Read tool with pages=...)")
        if len(low) == len(pages):
            print("  -> no extractable text: scanned/image-only PDF")


if __name__ == "__main__":
    main()
