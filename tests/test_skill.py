import re
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "skills" / "scrollback"


def frontmatter(text):
    head = text.split("---")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines())


def test_frontmatter():
    fm = frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
    assert fm["name"] == "scrollback"
    assert 100 < len(fm["description"]) <= 1024


def test_every_referenced_file_exists():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    refs = set(re.findall(r"(?:references|scripts)/[\w.-]+\.(?:md|py)", text))
    assert len(refs) == 6
    assert [r for r in refs if not (SKILL / r).exists()] == []


def test_note_sections_match_everywhere():
    sections = ["## What is explained", "## Tools, repos and links mentioned", "## Design", "## Core claim", "## Usefulness"]
    notes = (SKILL / "references" / "notes.md").read_text(encoding="utf-8")
    assert all(s in notes for s in sections)
