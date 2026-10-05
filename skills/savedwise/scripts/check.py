#!/usr/bin/env python3
"""Check a Savedwise knowledge base: every post has a note and sits in exactly one domain file, and every link to items/ resolves.

Posts that fetch.py tried but could not download (deleted, private, login refused) need no note; they are listed, not counted as problems.
Usage: python check.py <kb-folder>   (exit code 1 when there are problems)
"""
import re
import sys
from pathlib import Path

from fetch import fetched, item_id, read_links

LINK = re.compile(r"\]\(([^)\s#]*items/[^)\s#]+\.md)")


def not_fetched(kb):
    kb = Path(kb)
    ids = [item_id(url) for _, url in read_links(kb / "links.tsv")]
    return [i for i in ids if (kb / "raw" / i).is_dir() and not fetched(kb / "raw" / i)]


def problems(kb):
    kb = Path(kb)
    skip = set(not_fetched(kb))
    domains = sorted((kb / "domains").glob("*.md"))
    texts = {f: f.read_text(encoding="utf-8") for f in [kb / "OVERVIEW.md", *domains] if f.exists()}
    out = [] if (kb / "OVERVIEW.md").exists() else ["OVERVIEW.md is missing"]
    for _, url in read_links(kb / "links.tsv"):
        i = item_id(url)
        if i in skip:
            continue
        if not (kb / "items" / f"{i}.md").exists():
            out.append(f"{i}: no note in items/")
        n = sum(f"items/{i}.md" in texts[d] for d in domains)
        if n != 1:
            out.append(f"{i}: in {n} domain files, expected 1")
    for f, text in texts.items():
        for target in LINK.findall(text):
            if not (f.parent / target).exists():
                out.append(f"{f.name}: broken link {target}")
    return out


if __name__ == "__main__":
    found = problems(sys.argv[1])
    print("\n".join(found) or "ok")
    skipped = not_fetched(sys.argv[1])
    if skipped:
        print(f"not fetched, no note needed: {', '.join(skipped)}")
    sys.exit(1 if found else 0)
