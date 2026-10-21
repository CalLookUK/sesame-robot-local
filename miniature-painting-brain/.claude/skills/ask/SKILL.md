---
name: ask
description: Answer a miniature painting question from the vault - recipes, techniques, paints, how a source does something - with citations. Use for "how do I paint...", "what recipe do I have for...", "which paints do I need for...", "what does <source> say about...".
---

# Ask

Answer from the vault, not from general knowledge, and say which is which.

## Steps

1. **Search the notes first.** `grep -ril` and `Glob` across `Library/`, matching on
   the subject, colour, technique and likely synonyms (e.g. "NMM" / "non-metallic
   metal", "OSL" / "object source lighting", "wet blend" / "blending").
2. **Read the best matches**, including `## My notes` sections - my experience
   outranks a source's claim where they differ; show both.
3. **Fall back to the full text** if notes don't cover it:
   `grep -n -i -C3 "<term>" Sources/Text/*.txt`. Read the surrounding pages. If the
   answer is only in the text, offer to add it to the vault.
4. **Answer** concisely: the steps or paints requested, with citations
   (`[[Source]] p.N`). Where sources disagree, list each approach and its source.
5. **Be explicit about gaps.** If the vault has nothing, say so, then give general
   knowledge clearly labelled as not from my library.

## Don't

- Don't present general knowledge as if a source said it.
- Don't invent paint equivalents; use only those the vault records.
- Don't write or edit notes - this skill is read-only. Offer `/capture` or
  `/ingest-pdf` for follow-ups.
