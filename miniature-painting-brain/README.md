# Miniature Painting Brain

A plain-markdown second brain for miniature painting, driven by Claude Code. Built
from the Second Brain starter kit, adapted for tutorials and recipes.

## Use

1. Open Claude Code in this folder (`miniature-painting-brain/`) so `CLAUDE.md` and
   `.claude/skills/` are picked up.
2. Drop PDFs into `Sources/Inbox/`.
3. Say **"ingest the PDFs"** (`/ingest-pdf`). Each PDF becomes:
   - page-tagged text in `Sources/Text/` (full-text searchable),
   - a source note in `Library/Sources/`,
   - technique, recipe and paint notes with page citations.
4. Ask things: **"how did I say to paint red armour?"** (`/ask`).
5. Log your own results: **"capture: painted 10 intercessors with ..."** (`/capture`).
6. Keep it tidy: `/link`, or `python3 tools/check_vault.py`.

## Layout

```
CLAUDE.md          conventions Claude reads first
*.md hubs          Painting Hub is the entry point
Sources/Inbox/     drop new PDFs here
Sources/PDFs/      originals after ingest (never modified)
Sources/Text/      generated page-tagged text
Library/           Sources, Techniques, Recipes, Paints, Projects
Inbox/             unprocessed fragments
_Archive/          superseded notes (never deleted)
tools/             extract_pdf.py, check_vault.py
```

Requires `pdftotext` (poppler-utils) and Python 3. Image-heavy or scanned PDFs are
read visually page by page, so expect those to take longer.
