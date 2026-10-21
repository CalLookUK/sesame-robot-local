#!/usr/bin/env python3
"""Lint the vault: frontmatter, unresolved [[wikilinks]], orphans, hub coverage."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"_Archive", "tools", ".claude", ".git"}
LINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
HUBS = {
    "source": "Sources Hub", "technique": "Techniques Hub", "recipe": "Recipes Hub",
    "paint": "Paints Hub", "project": "Projects Hub",
}


def notes():
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP or rel.name == "CLAUDE.md":
            continue
        yield p


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        if k and not k.startswith(" "):
            fm[k.strip()] = v.split("#")[0].strip()
    return fm


def main():
    data = {p.stem: p.read_text(encoding="utf-8") for p in notes()}
    problems, inbound = [], {n: 0 for n in data}
    for name, text in data.items():
        fm = frontmatter(text)
        if fm is None:
            problems.append(f"{name}: missing frontmatter")
        else:
            for k in ("title", "type"):
                if not fm.get(k):
                    problems.append(f"{name}: missing '{k}'")
        for target in {t.strip() for t in LINK.findall(text)}:
            if target in data:
                if target != name:
                    inbound[target] += 1
            else:
                problems.append(f"{name}: unresolved link [[{target}]]")
        hub = HUBS.get((fm or {}).get("type", ""))
        if hub and hub in data and f"[[{name}]]" not in data[hub]:
            problems.append(f"{name}: not listed in [[{hub}]]")
    for name, n in inbound.items():
        if n == 0 and name != "Painting Hub":
            problems.append(f"{name}: orphan (no inbound links)")
    print(f"{len(data)} notes checked")
    for p in problems:
        print("  -", p)
    print("clean" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
