import check

IDS = ("AAA111", "BBB222")


def make_kb(tmp, domains, notes=IDS, overview="# Overview\n", failed=()):
    (tmp / "links.tsv").write_text("".join(f"ai\thttps://www.instagram.com/reel/{i}/\n" for i in IDS), encoding="utf-8")
    for i in IDS:
        (tmp / "raw" / i).mkdir(parents=True)
        (tmp / "raw" / i / "source.txt").write_text("ai\n", encoding="utf-8")
        if i not in failed:
            (tmp / "raw" / i / "video.mp4").write_bytes(b"x")
    (tmp / "items").mkdir()
    for i in notes:
        (tmp / "items" / f"{i}.md").write_text("---\n", encoding="utf-8")
    (tmp / "domains").mkdir()
    for name, body in domains.items():
        (tmp / "domains" / name).write_text(body, encoding="utf-8")
    if overview is not None:
        (tmp / "OVERVIEW.md").write_text(overview, encoding="utf-8")
    return tmp


GOOD = {"1-a.md": "[x](../items/AAA111.md)\n", "2-b.md": "[y](../items/BBB222.md)\n"}


def test_valid_kb(tmp_path):
    assert check.problems(make_kb(tmp_path, GOOD, overview="[x](items/AAA111.md)\n")) == []


def test_missing_note(tmp_path):
    assert check.problems(make_kb(tmp_path, GOOD, notes=("AAA111",))) == ["BBB222: no note in items/", "2-b.md: broken link ../items/BBB222.md"]


def test_post_in_two_domains_and_in_none(tmp_path):
    kb = make_kb(tmp_path, {"1-a.md": "[x](../items/AAA111.md)\n", "2-b.md": "[x](../items/AAA111.md)\n"})
    assert check.problems(kb) == ["AAA111: in 2 domain files, expected 1", "BBB222: in 0 domain files, expected 1"]


def test_broken_link_in_overview(tmp_path):
    assert check.problems(make_kb(tmp_path, GOOD, overview="[z](items/ZZZ999.md)\n")) == ["OVERVIEW.md: broken link items/ZZZ999.md"]


def test_missing_overview(tmp_path):
    assert check.problems(make_kb(tmp_path, GOOD, overview=None)) == ["OVERVIEW.md is missing"]


def test_failed_download_needs_no_note(tmp_path):
    kb = make_kb(tmp_path, {"1-a.md": "[x](../items/AAA111.md)\n"}, notes=("AAA111",), failed=("BBB222",))
    assert check.problems(kb) == []
    assert check.not_fetched(kb) == ["BBB222"]


def test_post_without_raw_folder_still_needs_a_note(tmp_path):
    kb = make_kb(tmp_path, GOOD, notes=("AAA111",))
    for f in (kb / "raw" / "BBB222").iterdir():
        f.unlink()
    (kb / "raw" / "BBB222").rmdir()
    assert "BBB222: no note in items/" in check.problems(kb)


def test_design_note_needs_style_file(tmp_path):
    kb = make_kb(tmp_path, GOOD)
    (kb / "items" / "AAA111.md").write_text("---\n## Design\n- Colours: black\n", encoding="utf-8")
    assert check.problems(kb) == ["STYLE.md is missing (1 notes have a Design section)"]
    (kb / "STYLE.md").write_text("[x](items/AAA111.md)\n", encoding="utf-8")
    assert check.problems(kb) == []


def test_broken_link_in_style_file(tmp_path):
    kb = make_kb(tmp_path, GOOD)
    (kb / "STYLE.md").write_text("[z](items/ZZZ999.md)\n", encoding="utf-8")
    assert check.problems(kb) == ["STYLE.md: broken link items/ZZZ999.md"]
