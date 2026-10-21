---
name: link
description: Find and add [[wikilinks]] between related notes, repair broken links, and keep the hub notes complete. Use for "link up my notes", "update the hubs", "check the vault", "why is a note orphaned?".
---

# Link

Links are the retrieval surface. Precision over coverage.

## Steps

1. **Run the checker:** `python3 tools/check_vault.py` - lists unresolved links,
   orphans (no inbound links), notes missing from their hub, and frontmatter problems.
2. **Find real connections:**
   - Recipes <-> the techniques they use <-> the paints they list
   - Notes citing the same source <-> that source note
   - Techniques that build on each other (e.g. glazing -> OSL)
   Only link where the notes genuinely relate; shared common words are not a reason.
3. **Propose before applying** if more than ~10 links; otherwise apply and report.
4. **Hubs:** each hub is an index - one line per link, grouped by theme (faction/colour
   for recipes, brand for paints, skill area for techniques). Add anything missing.
5. **Re-run the checker** and confirm it's clean.

## Don't

- Don't link `_Archive/` notes.
- Don't rewrite bodies beyond inserting `[[ ]]` brackets around existing mentions.
