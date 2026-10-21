# Miniature Painting Brain

A second brain for miniature painting: tutorials, paint recipes, techniques and my
own project notes. Plain markdown on disk - no database, no MCP server. Read, grep
and edit the files directly. Obsidian works as an optional viewer (open this folder
as a vault) but is not required.

**Vault root:** `miniature-painting-brain/` (this folder)

## How it works

1. PDFs are dropped in `Sources/Inbox/`.
2. `/ingest-pdf` extracts the text (page-tagged) into `Sources/Text/`, moves the PDF
   to `Sources/PDFs/`, and writes a **source note** plus **technique / recipe / paint
   notes** in `Library/`, each citing the PDF and page.
3. `/ask` answers questions from the notes first, then falls back to the full text.
4. `/capture` logs my own experiments, results and quick thoughts.
5. `/link` keeps the graph connected and the hubs current.

## Ground rules

1. **Cite everything.** Every fact lifted from a PDF carries its source and page,
   e.g. `([[Source Title]] p.12)`. If I can't point to a page, say so.
2. **Never invent paint data.** Paint names, brands, mixing ratios and step order come
   from the source. If a recipe says "a dark red" without naming a paint, record it
   as written - don't guess a product. Paint equivalents between brands are only
   recorded when a source states them, otherwise marked `(unverified)`.
3. **Separate source from opinion.** Source-derived content lives in `Library/`
   notes. My own results and preferences go in `## My notes` sections or `Projects/`
   so they never get mistaken for what the author said.
4. **Never delete.** Superseded or duplicate notes move to `_Archive/`. Original PDFs
   are never modified or removed.
5. **Don't paraphrase away detail.** Recipes keep exact step order, paint names and
   ratios. Summaries go in the source note, not instead of the steps.
6. **Copyright.** PDFs are for my personal reference. Notes may summarise and quote
   short passages; don't reproduce whole tutorials verbatim in notes.
7. **Extracted text is read-only.** `Sources/Text/` is generated - re-run the
   extractor rather than hand-editing.
8. **Rename in reviewable batches** and repair `[[wikilinks]]` afterwards
   (`python3 tools/check_vault.py`).

## Frontmatter schema

```yaml
---
title: Non-Metallic Metal Gold
type: technique          # see note types
created: 2026-10-21
updated: 2026-10-21      # optional
tags: [nmm, highlights, gold]
sources: ["[[Source Note Title]]"]   # technique/recipe/paint notes: where it came from
status: active           # active | to-try | tried | archive
---
```

`title` and `type` are required. Omit optional keys rather than leaving them empty.

## Note types

| `type` | What goes here | Folder |
|---|---|---|
| `source` | One per PDF: metadata, summary, contents with page refs | `Library/Sources/` |
| `technique` | A reusable method (glazing, wet blending, NMM, OSL, zenithal...) | `Library/Techniques/` |
| `recipe` | A specific colour scheme / step-by-step for a subject (skin, red armour, gold) | `Library/Recipes/` |
| `paint` | A paint, range or brand, plus equivalents and notes | `Library/Paints/` |
| `project` | My own models: what I painted, recipe used, result, lessons | `Library/Projects/` |
| `fleeting` | Unprocessed fragments | `Inbox/` |
| `hub` | Maps of content in the vault root | root |

Hubs (maps of content) live in the vault root: `Painting Hub.md`, `Techniques Hub.md`,
`Recipes Hub.md`, `Paints Hub.md`, `Sources Hub.md`, `Projects Hub.md`.

## Note templates

**Source note** (`Library/Sources/<Title>.md`)
- Frontmatter: `type: source`, plus `author`, `publisher`, `year`, `pdf: Sources/PDFs/<file>.pdf`, `text: Sources/Text/<file>.txt`, `pages`, `ingested`
- Sections: `## Summary` (3-6 bullets), `## Contents` (page-referenced list of what's covered, each linked to the technique/recipe notes), `## Extraction notes` (scanned? diagrams? things I couldn't read)

**Technique note**
- Sections: `## What it is`, `## When to use`, `## Steps`, `## Tips and pitfalls`, `## Paints/tools`, `## My notes`
- Cite page for each section drawn from a source. If several sources cover the technique, keep one note and list each source's variation under its own heading.

**Recipe note**
- Sections: `## Subject` (model/area), `## Paints`, `## Steps` (numbered, exact order, dilution/ratios as written), `## Result`, `## My notes`
- Frontmatter extras: `subject`, `colours` (e.g. `[red, gold]`), `difficulty` if stated.

**Paint note**
- Frontmatter extras: `brand`, `range`, `paint_type` (base, layer, shade, contrast, metallic, ink...).
- Sections: `## Used in` (links to recipes), `## Equivalents` (only if sourced), `## My notes`

## Naming

- Descriptive Title Case, no numbering: `Wet Blending Skin Tones.md`
- Source notes use the document title: `Painting Warhammer Eldar.md`
- Paint notes: `Brand Paint Name.md`, e.g. `Citadel Mephiston Red.md`
- Never leave `Untitled N`.

## Linking

- Every note links to at least one hub and to its source.
- Recipes link the techniques they use and the paints they list; paint notes link back.
- End each note with `Part of [[X Hub]].`
- Never link `_Archive/` notes.
- Tags are for cross-cutting themes (`nmm`, `osl`, `skin`, `armour`, `beginner`), not for what `type` already says.

## Style

Terse bullets. Exact paint names. Steps numbered. No filler.
