"""Repo-level guards: the manifests agree, and nothing private is in the repo."""
import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".venv", "__pycache__", ".pytest_cache", ".superpowers"}
LEAKS = [
    re.compile(r"[A-Za-z]:\\Users\\", re.I),
    re.compile(r"/(?:Users|home)/[\w.-]+/"),
    re.compile(r"[\w.+-]+@(?!users\.noreply\.github\.com|example\.com)[\w-]+\.[a-z]{2,}", re.I),
]


def repo_texts():
    me = Path(__file__).resolve()
    for p in ROOT.rglob("*"):
        if p.is_file() and not SKIP & set(p.relative_to(ROOT).parts) and p != me:
            yield p, p.read_text(encoding="utf-8", errors="ignore")


def test_manifests_agree():
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "scrollback"
    assert [(p["name"], p["source"]) for p in market["plugins"]] == [("scrollback", "./")]


def test_no_home_paths_or_emails():
    found = [f"{p.relative_to(ROOT)}: {m.group(0)}" for p, text in repo_texts() for rx in LEAKS for m in rx.finditer(text)]
    assert found == []


def test_no_private_terms():
    path = os.environ.get("SCROLLBACK_PRIVATE_TERMS")
    if not path:
        pytest.skip("set SCROLLBACK_PRIVATE_TERMS to a file with one private term per line")
    terms = [t.strip().lower() for t in Path(path).read_text(encoding="utf-8").splitlines() if t.strip()]
    found = [f"{p.relative_to(ROOT)}: {t}" for p, text in repo_texts() for t in terms if t in text.lower()]
    assert found == []
