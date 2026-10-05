#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp[curl-cffi]", "gallery-dl", "faster-whisper", "av<19"]  # av 19 dropped an argument faster-whisper 1.2 passes
# ///
"""Download every post in <kb>/links.tsv to <kb>/raw/<id>/ with caption, transcript and contact sheets.

Resumable: whatever is already on disk is skipped.
Usage: uv run fetch.py <kb-folder> [filter] [--model turbo] [--device cpu]
                       [--cookies-from-browser BROWSER | --cookies FILE]
The filter is any part of a URL: one post or one maker.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path
from urllib.parse import urlparse

VIDEO = {".mp4", ".webm", ".mkv", ".mov"}
IMAGE = {".jpg", ".jpeg", ".png", ".webp"}
# A single post, never a profile or collection page (that would download everything on it).
POST = re.compile(r"https?://(?:vm|vt)\.tiktok\.com/\w+|/(?:reels?|p|tv|video|photo|t)/[\w-]+")


def item_id(url):
    return urlparse(url.strip()).path.rstrip("/").split("/")[-1]


def read_links(path, flt=""):
    """(collection, url) per post. A bare URL gets collection 'unsorted'; blank lines, # comments, repeated posts and non-post URLs are skipped."""
    rows, seen = [], set()
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():  # -sig: Notepad adds a BOM
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if not parts or parts[0].startswith("#"):
            continue
        coll, url = (parts[0], parts[1]) if len(parts) > 1 else ("unsorted", parts[0])
        if flt in url and POST.search(url) and item_id(url) not in seen:
            seen.add(item_id(url))
            rows.append((coll, url))
    return rows


def caption_from_meta(m):
    def name(v):
        return v.get("uniqueId") or v.get("username") if isinstance(v, dict) else v

    author = m.get("uploader") or m.get("username") or name(m.get("author")) or name(m.get("user")) or "?"
    text = m.get("description") or m.get("desc") or m.get("title") or ""
    return f"maker: {author}\n{text.strip()}\n"


def sheet_count(duration):
    # ponytail: 9 frames per sheet, max 3 sheets. More frames if on-screen text turns out unreadable.
    return min(3, max(1, math.ceil(duration / 54)))


def run(*cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")


def video(d):
    # stem check: yt-dlp leaves video.f<format>.mp4 / video.temp.mp4 behind when interrupted before merging
    return next((p for p in sorted(d.glob("video.*")) if p.suffix in VIDEO and p.stem == "video"), None)


def images(d):
    return sorted(p for p in (d / "img").glob("*") if p.suffix.lower() in IMAGE)


def fetched(d):
    """A video, or images from a gallery-dl run that finished (an interrupted carousel is retried)."""
    return bool(video(d)) or (d / "img" / ".done").exists()


def download(url, d, cookies):
    """Without cookies first; with the user's cookie option only when that fails."""
    for extra in ([], cookies) if cookies else ([],):
        if "/p/" not in url and "/photo/" not in url:  # carousels: yt-dlp with --no-playlist gets only the first slide
            run(sys.executable, "-m", "yt_dlp", *extra, "--no-playlist", "--write-info-json", "-o", d / "video.%(ext)s", url)
            if video(d):
                return
        # --range: a carousel has at most 20 slides; caps the damage if a URL is not a single post after all
        # -f: default names hold the whole caption and pass Windows' 260-character path limit
        r = run(sys.executable, "-m", "gallery_dl", *extra, "--range", "1-20", "-f", "{num:>02}.{extension}",
                "--write-metadata", "-D", d / "img", url)
        # gallery-dl also gets TikTok videos that yt-dlp misses: move the first one to the video slot.
        for clip in sorted((d / "img").glob("*.mp4")):
            meta = Path(f"{clip}.json")
            if meta.exists():
                meta.replace(d / "video.info.json")
            clip.replace(d / "video.mp4")
            break
        if video(d):
            return
        if r.returncode == 0 and images(d):
            (d / "img" / ".done").touch()
            return


def caption(d):
    meta = next(iter(sorted(d.glob("video.info.json")) + sorted((d / "img").glob("*.json"))), None)
    if meta:
        m = json.loads(meta.read_text(encoding="utf-8"))
        (d / "caption.txt").write_text(caption_from_meta(m), encoding="utf-8")


def has_audio(v):
    out = run("ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", v)
    return bool(out.stdout.strip())


@cache
def whisper(model, device):
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # noisy on Windows, harmless
    from faster_whisper import WhisperModel

    return WhisperModel(model, device=device, compute_type="auto")


def transcribe(v, model, device):
    if not has_audio(v):
        return "[no transcript: no audio stream]\n"
    try:
        segments, info = whisper(model, device).transcribe(str(v))
        return f"[language: {info.language}]\n{''.join(s.text for s in segments).strip()}\n"
    except Exception as e:  # one bad item must not stop the run
        return f"[no transcript: {type(e).__name__}: {e}]\n"


def sheets(v, d):
    out = run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v).stdout.strip()
    try:
        dur = float(out)
    except ValueError:
        return
    n = sheet_count(dur)
    run("ffmpeg", "-y", "-i", v, "-vf", f"fps={9 * n}/{dur},scale=480:-2,tile=3x3", "-q:v", "4", d / "sheet_%d.jpg")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("kb", type=Path, help="knowledge base folder containing links.tsv")
    p.add_argument("filter", nargs="?", default="", help="only URLs containing this text")
    p.add_argument("--model", default="turbo", help="faster-whisper model; 'small' is faster on a weak CPU")
    # cpu by default: with an NVIDIA driver but no cuDNN/cuBLAS, 'auto' crashes the process natively
    p.add_argument("--device", default="cpu", help="cpu (default) or cuda; cuda needs NVIDIA's cuBLAS and cuDNN")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--cookies-from-browser", metavar="BROWSER", help="e.g. firefox; on Windows Chrome cookies cannot be read")
    g.add_argument("--cookies", metavar="FILE", help="cookies.txt in Netscape format")
    a = p.parse_args(argv)

    links = a.kb / "links.tsv"
    if not links.exists():
        sys.exit(f"{links} not found. Collect links first (phase 2).")
    missing = [t for t in ("ffmpeg", "ffprobe") if not shutil.which(t)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}. Install ffmpeg: winget install Gyan.FFmpeg | brew install ffmpeg | sudo apt install ffmpeg")
    cookies = (["--cookies-from-browser", a.cookies_from_browser] if a.cookies_from_browser
               else ["--cookies", a.cookies] if a.cookies else [])
    sys.stdout.reconfigure(encoding="utf-8")
    ignore = a.kb / ".gitignore"
    if not ignore.exists():
        ignore.write_text("raw/\n", encoding="utf-8")

    rows = read_links(links, a.filter)
    for i, (coll, url) in enumerate(rows, 1):
        d = a.kb / "raw" / item_id(url)
        d.mkdir(parents=True, exist_ok=True)
        (d / "source.txt").write_text(f"{coll}\n{url}\n", encoding="utf-8")
        if not fetched(d):
            download(url, d, cookies)
        caption(d)
        v = video(d)
        if v and not (d / "transcript.txt").exists():
            (d / "transcript.txt").write_text(transcribe(v, a.model, a.device), encoding="utf-8")
        if v and not list(d.glob("sheet_*.jpg")):
            sheets(v, d)
        status = "video" if v else f"{len(images(d))} img" if fetched(d) else "FAILED"
        print(f"{i:>3}/{len(rows)} {coll:<12} {item_id(url):<22} {status}", flush=True)


if __name__ == "__main__":
    main()
