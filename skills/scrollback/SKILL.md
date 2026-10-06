---
name: scrollback
description: Turns saved Instagram and TikTok posts (reels, videos, carousels, photo posts) into a personal knowledge base - one note per post, topic domains, an overview of what is worth doing, which of the user's own projects each tip fits, and skills worth building. Use when the user wants to process, summarise or learn from their saved, bookmarked or favorited social media posts, add newly saved posts, or update an existing Scrollback knowledge base.
---

# Scrollback

Turn a pile of saved posts into a knowledge base the user will actually use. Every post is downloaded, transcribed and read frame by frame, summarised into a note, and grouped into domains with a verdict per post and advice tied to the user's own projects. Everything stays on the user's machine.

## Requirements

- ffmpeg and ffprobe on PATH (`ffmpeg -version`). Install with `winget install Gyan.FFmpeg`, `brew install ffmpeg` or `sudo apt install ffmpeg`.
- uv (`uv --version`), see https://docs.astral.sh/uv/getting-started/installation/. Without uv: Python 3.10+ and `python -m pip install "yt-dlp[curl-cffi]" gallery-dl faster-whisper "av<19"`, then run the scripts with `python` instead of `uv run`.
- Claude in Chrome, only for collecting links by scrolling. Pasted links work without it.

Check these before phase 3 and tell the user what is missing. Never install anything without asking.

## The knowledge base

The knowledge base lives in one fixed folder, so every run adds to the same one. `~/.scrollback` holds its absolute path on one line.

- `~/.scrollback` exists: use that folder. Do not ask again.
- It does not exist: ask where the knowledge base should live (suggest `~/scrollback-kb`), create the folder and write its absolute path to `~/.scrollback`.
- The user wants it elsewhere: move the folder only if they ask, then update `~/.scrollback`.

Below, `<kb>` is that folder and `<skill>` is this skill's base directory.

```
<kb>/
  profile.md        who the user is, their projects, what they have installed
  links.tsv         <collection><TAB><url>, one post per line
  raw/<id>/         downloads, caption, transcript, contact sheets
  items/<id>.md     one note per post, with a Design section when it shows a site, app or interface
  domains/N-<slug>.md
  OVERVIEW.md
  STYLE.md          recurring style and libraries across the Design sections
```

The id of a post is the last path segment of its URL.

## Where to start

Check the knowledge base and start at the first row that is true:

| State | Phase |
| --- | --- |
| `profile.md` missing | 1. Profile |
| `links.tsv` missing or empty, or the user brings new links | 2. Links |
| a post in `links.tsv` has no `raw/<id>/` folder | 3. Fetch |
| a fetched post (status `video` or `<n> img`) has no `items/<id>.md` | 4. Notes |
| `OVERVIEW.md` missing, older than the newest note, or `check.py` fails | 5. Synthesis |
| none of the above | Done: say so and offer to add links |

Tell the user which phase you start at and why. Read the phase's reference file before starting it. Between phases, give a one-line status (counts, failures) and continue unless something needs the user's decision.

## Phases

1. **Profile.** Learn the user's projects, stack and installed skills; write `profile.md`; get it confirmed. Read `references/profile.md`.
2. **Links.** Collect post URLs from a saved collection via Claude in Chrome, or take pasted links. Read `references/links.md`.
3. **Fetch.** Run `uv run <skill>/scripts/fetch.py <kb>`. See below.
4. **Notes.** One note per post, written by subagents in batches. Read `references/notes.md`.
5. **Synthesis.** Domains, overview, project fit, skill ideas, `STYLE.md`; finish with `uv run <skill>/scripts/check.py <kb>`. Read `references/synthesis.md`.

### Phase 3: fetch

`uv run <skill>/scripts/fetch.py <kb> [filter]` downloads every post in `links.tsv` to `raw/<id>/` and prints one line per post: `video`, `<n> img` or `FAILED`. It skips whatever is already on disk, so rerunning is safe. The first run downloads the whisper model (about 1.5 GB for `turbo`).

- Run it in the background for more than ~10 posts and report progress.
- Transcription runs on the CPU. Too slow: rerun with `--model small`. With an NVIDIA GPU, `--device cuda` is much faster; if fetch then stops or transcripts mention cudnn, cublas or CUDA, the CUDA libraries are missing: delete those `transcript.txt` files and go back to the default.
- `fetch.py` skips links that are not a single post (a profile or collection page would download everything on it).
- `FAILED` posts usually need a login (Instagram carousels always do). Ask the user before using cookies, then rerun with `--cookies-from-browser firefox` (or their browser) or `--cookies cookies.txt`. On Windows Chrome's cookies cannot be read; suggest Firefox or a `cookies.txt` export.
- Redo one post: delete what should be redone in `raw/<id>/` (`video.*`, `transcript.txt`, `sheet_*.jpg`) and run `fetch.py <kb> <id>`.

## Rules

- Write everything in English unless the user asks for another language.
- Never share, upload or commit `raw/` or cookie files: they hold other people's content and the user's login. `fetch.py` writes a `.gitignore` for `raw/`.
- Never type a password; the user logs in themselves.
- Do not install, run or test the tools mentioned in posts. "Winner" means best source, not proven best tool.
- On-screen text beats the transcript for names, repo paths, URLs and commands.
