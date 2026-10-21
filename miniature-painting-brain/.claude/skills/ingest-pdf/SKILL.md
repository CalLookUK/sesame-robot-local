---
name: ingest-pdf
description: Read PDFs dropped in Sources/Inbox/, extract and index their content into the vault as a source note plus technique, recipe and paint notes with page citations. Use for "ingest these PDFs", "process the inbox", "add this tutorial", or whenever new PDFs appear in Sources/Inbox/.
---

# Ingest PDF

Turn each PDF into searchable text and structured, cited notes. Process **one PDF at a
time, fully**, then report. If several are queued, do them sequentially and give one
summary table at the end.

## Steps

1. **Read `CLAUDE.md`** for schema, templates, ground rules and naming.

2. **Find the queue.** `ls Sources/Inbox/*.pdf`. If a PDF with the same name already
   exists in `Sources/PDFs/`, stop and ask - don't overwrite.

3. **Extract.** Run:
   ```bash
   python3 tools/extract_pdf.py "Sources/Inbox/<file>.pdf"
   ```
   It writes page-tagged text to `Sources/Text/<slug>.txt` (`=== page N ===` markers)
   and prints page count, characters per page and a warning for pages with little or
   no text.

4. **Handle weak extraction.** Tutorials are often image-heavy.
   - Pages flagged as low-text: open them as images with the Read tool
     (`pages: "N-M"`, max 20 per call) and read the content visually - paint lists,
     step photos with captions, swatch charts.
   - Fully scanned PDF: do the visual read for the whole document in chunks, and
     write what you read to a short `## Visual read` appendix in the source note, not
     into `Sources/Text/` (which is generated).
   - Note what couldn't be read in the source note's `## Extraction notes`.

5. **Read the document.** Read the full extracted text (in chunks if long) before
   writing anything. Identify: title, author/publisher/year, every distinct technique,
   recipe and named paint.

6. **Write the source note** in `Library/Sources/` per the template. The `## Contents`
   list maps each topic to page numbers and links to the notes created next.

7. **Create or update notes.**
   - For each technique/recipe/paint, first `Glob`/`grep` `Library/` for an existing
     note. **Update it** (add a section citing this source) rather than creating a
     near-duplicate. Flag possible duplicates; don't merge silently.
   - New technique/recipe notes follow the templates. Keep exact step order, paint
     names, ratios and dilutions. Cite page numbers.
   - Paint notes: only create for paints that are named in the source. Add the recipe
     to `## Used in`.
   - Anything the source says that doesn't fit a note (general advice, workflow, tool
     recommendations) goes in the source note's summary.

8. **Link.** Add every new note to its hub (`Techniques Hub`, `Recipes Hub`,
   `Paints Hub`, `Sources Hub`). Ensure notes link to each other and the source.

9. **File the PDF.** Move it: `mv "Sources/Inbox/<file>.pdf" Sources/PDFs/`. Set `pdf:`
   in the source note to the new path.

10. **Verify.** `python3 tools/check_vault.py` - fix any unresolved links or missing
    frontmatter it reports.

11. **Report** one block: source note path, page count, notes created vs updated,
    anything unreadable or ambiguous, possible duplicates.

## Don't

- Don't guess paint names or substitute products for ones the source doesn't name.
- Don't summarise away steps - summaries live in the source note, steps stay exact.
- Don't copy long passages verbatim; short quotes only.
- Don't edit `Sources/Text/` by hand, and never modify or delete the original PDF.
- Don't start the next PDF before the current one is verified and filed.
