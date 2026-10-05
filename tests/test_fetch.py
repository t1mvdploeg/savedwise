import json

import pytest

import fetch


@pytest.mark.parametrize("url, expected", [
    ("https://www.instagram.com/reel/Abc123xyz/", "Abc123xyz"),
    ("https://www.instagram.com/reel/Abc123xyz/?igsh=MWx0ZnR3", "Abc123xyz"),
    ("https://www.tiktok.com/@maker/video/7000000000000000001?is_from_webapp=1", "7000000000000000001"),
    ("  https://www.instagram.com/p/Def456uvw  ", "Def456uvw"),
])
def test_item_id(url, expected):
    assert fetch.item_id(url) == expected


def test_read_links_skips_blanks_comments_and_repeats(tmp_path):
    f = tmp_path / "links.tsv"
    f.write_text(
        "# saved posts\n"
        "\n"
        "ai\thttps://www.instagram.com/reel/Abc123xyz/\n"
        "ai\thttps://www.instagram.com/reel/Abc123xyz/?igsh=x\n"
        "https://www.tiktok.com/@a/video/7000000000000000001\n",
        encoding="utf-8",
    )
    assert fetch.read_links(f) == [
        ("ai", "https://www.instagram.com/reel/Abc123xyz/"),
        ("unsorted", "https://www.tiktok.com/@a/video/7000000000000000001"),
    ]


def test_read_links_filter(tmp_path):
    f = tmp_path / "links.tsv"
    f.write_text("ai\thttps://www.instagram.com/reel/Abc123xyz/\ndev\thttps://www.tiktok.com/@a/video/7000000000000000001\n", encoding="utf-8")
    assert fetch.read_links(f, "tiktok") == [("dev", "https://www.tiktok.com/@a/video/7000000000000000001")]


def test_read_links_ignores_bom(tmp_path):
    f = tmp_path / "links.tsv"
    f.write_text("ai\thttps://www.instagram.com/reel/Abc123xyz/\n", encoding="utf-8-sig")
    assert fetch.read_links(f) == [("ai", "https://www.instagram.com/reel/Abc123xyz/")]


@pytest.mark.parametrize("meta, expected", [
    ({"uploader": "ytdlp_maker", "description": "  Five tools \n"}, "maker: ytdlp_maker\nFive tools\n"),
    ({"username": "ig_maker", "description": "carousel"}, "maker: ig_maker\ncarousel\n"),
    ({"author": {"uniqueId": "tt_maker"}, "desc": "tiktok"}, "maker: tt_maker\ntiktok\n"),
    ({"user": {"username": "u_maker"}, "title": "t"}, "maker: u_maker\nt\n"),
    ({"author": "plain_name", "title": "t"}, "maker: plain_name\nt\n"),
    ({}, "maker: ?\n\n"),
])
def test_caption_from_meta(meta, expected):
    assert fetch.caption_from_meta(meta) == expected


@pytest.mark.parametrize("duration, sheets", [(10, 1), (54, 1), (55, 2), (108, 2), (109, 3), (3600, 3)])
def test_sheet_count(duration, sheets):
    assert fetch.sheet_count(duration) == sheets


def test_video_ignores_partial_and_metadata(tmp_path):
    (tmp_path / "video.mp4.part").write_bytes(b"x")
    (tmp_path / "video.info.json").write_text("{}", encoding="utf-8")
    assert fetch.video(tmp_path) is None
    (tmp_path / "video.mp4").write_bytes(b"x")
    assert fetch.video(tmp_path) == tmp_path / "video.mp4"


def test_caption_keeps_emoji(tmp_path):
    meta = {"uploader": "maker", "description": "Ship it 🚀 — café"}
    (tmp_path / "video.info.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    fetch.caption(tmp_path)
    assert (tmp_path / "caption.txt").read_text(encoding="utf-8") == "maker: maker\nShip it 🚀 — café\n"


def test_caption_from_gallery_dl_metadata(tmp_path):
    (tmp_path / "img").mkdir()
    (tmp_path / "img" / "1.jpg.json").write_text(json.dumps({"username": "ig", "description": "slides"}), encoding="utf-8")
    fetch.caption(tmp_path)
    assert (tmp_path / "caption.txt").read_text(encoding="utf-8") == "maker: ig\nslides\n"


def test_transcribe_without_audio_skips_whisper(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "has_audio", lambda v: False)
    monkeypatch.setattr(fetch, "whisper", lambda *a: pytest.fail("whisper must not load"))
    assert fetch.transcribe(tmp_path / "video.mp4", "turbo", "auto") == "[no transcript: no audio stream]\n"


def test_transcribe_failure_does_not_raise(tmp_path, monkeypatch):
    class Broken:
        def transcribe(self, path):
            raise RuntimeError("CUDA not available")

    monkeypatch.setattr(fetch, "has_audio", lambda v: True)
    monkeypatch.setattr(fetch, "whisper", lambda *a: Broken())
    assert fetch.transcribe(tmp_path / "video.mp4", "turbo", "auto") == "[no transcript: RuntimeError: CUDA not available]\n"


def test_transcribe_joins_segments(tmp_path, monkeypatch):
    class Seg:
        def __init__(self, text):
            self.text = text

    class Info:
        language = "en"

    class Model:
        def transcribe(self, path):
            return iter([Seg(" Hello"), Seg(" world. ")]), Info()

    monkeypatch.setattr(fetch, "has_audio", lambda v: True)
    monkeypatch.setattr(fetch, "whisper", lambda *a: Model())
    assert fetch.transcribe(tmp_path / "video.mp4", "turbo", "auto") == "[language: en]\nHello world.\n"


def test_main_without_links(tmp_path):
    with pytest.raises(SystemExit) as e:
        fetch.main([str(tmp_path)])
    assert "links.tsv" in str(e.value) and "phase 2" in str(e.value)


def test_read_links_keeps_only_post_urls(tmp_path):
    f = tmp_path / "links.tsv"
    f.write_text(
        "ai\thttps://www.instagram.com/someone/\n"
        "ai\thttps://www.instagram.com/\n"
        "ai\thttps://vm.tiktok.com/ZMabc123/\n"
        "ai\thttps://www.instagram.com/reel/Abc123xyz/\n",
        encoding="utf-8",
    )
    assert [u for _, u in fetch.read_links(f)] == ["https://vm.tiktok.com/ZMabc123/", "https://www.instagram.com/reel/Abc123xyz/"]


def test_video_ignores_unmerged_streams(tmp_path):
    (tmp_path / "video.fdash-123v.mp4").write_bytes(b"x")
    (tmp_path / "video.temp.mp4").write_bytes(b"x")
    assert fetch.video(tmp_path) is None


class Result:
    def __init__(self, returncode):
        self.returncode = returncode
        self.stdout = ""


def fake_gallery_dl(d, returncode, calls):
    def run(*cmd):
        calls.append([str(c) for c in cmd])
        (d / "img").mkdir(exist_ok=True)
        (d / "img" / "1.jpg").write_bytes(b"x")
        return Result(returncode)
    return run


def test_finished_carousel_is_fetched(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(fetch, "run", fake_gallery_dl(tmp_path, 0, calls))
    fetch.download("https://www.instagram.com/p/Abc123xyz/", tmp_path, [])
    assert fetch.fetched(tmp_path)
    assert "--range" in calls[0]


def test_gallery_dl_uses_short_filenames(tmp_path, monkeypatch):
    # Default names hold the whole caption; on Windows that passes the 260-character path limit.
    calls = []
    monkeypatch.setattr(fetch, "run", fake_gallery_dl(tmp_path, 0, calls))
    fetch.download("https://www.tiktok.com/@a/photo/7000000000000000001", tmp_path, [])
    assert calls[0][calls[0].index("-f") + 1] == "{num:>02}.{extension}"


def test_interrupted_carousel_is_not_fetched(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "run", fake_gallery_dl(tmp_path, 1, []))
    fetch.download("https://www.instagram.com/p/Abc123xyz/", tmp_path, [])
    assert fetch.images(tmp_path) and not fetch.fetched(tmp_path)
