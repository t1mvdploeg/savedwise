# Phase 4: Notes

Goal: `<kb>/items/<id>.md` for every post that was fetched, in a fixed format that phase 5 and `check.py` rely on.

## Batches

Images fill the context fast, so subagents write the notes: batches of about 8 posts (4 for videos over three minutes), at most 4 subagents at a time, on a fast model when one is offered. Each gets the prompt below with its ids and writes the files itself. Afterwards check that every file exists and starts with `---`; rerun a batch for the ones that do not.

Posts whose fetch status was `FAILED` get no note. List them for the user at the end of the run.

## Subagent prompt

Replace `{kb}` and `{ids}`:

```text
Write a note for each of these saved social media posts: {ids}

For each id, read everything in {kb}/raw/<id>/:
- source.txt (line 1 collection, line 2 URL) and caption.txt (line 1 is the maker)
- transcript.txt for videos (line 1 is the detected language)
- every sheet_N.jpg (3x3 frames in time order) or every image in img/
Look at every image: names, repo paths, URLs and commands are often only on screen.

Write {kb}/items/<id>.md in English, exactly in this format:

---
id: <id>
url: <url>
collection: <collection>
maker: <maker>
type: video | photo
tags: <3-6 lowercase tags, comma-separated>
---
# <one-line title saying what the post delivers>

## What is explained
- The substance: concrete steps, numbers, examples, and what is shown on screen.
- If the substance is withheld ("comment X for the link"), say so.

## Tools, repos and links mentioned
- <name>: what it is (certain, on screen | heard, spelling uncertain). The exact repo path or URL when visible.
- "None" when there are none.

## Design
Only when the post shows a website, app or interface; leave the whole section out otherwise.
- Colours: the palette, with hex codes when visible, and light or dark.
- Type: typefaces (named when visible, otherwise described: geometric sans, serif, mono), sizes and weights that stand out.
- Layout: the structure (hero, grid, bento, sidebar, cards) and spacing.
- Effects: animation, scroll effects, gradients, glass, 3D, cursor effects.
- Libraries: <name> (on screen | guessed from the look), one line each. "None visible" when nothing can be named.

## Core claim
One sentence: what the maker wants you to believe or do.

## Usefulness
2-4 sentences: how concrete and actionable it is, what is missing, whether it is promotion (disclosed or not), and any doubt about its claims.

Rules:
- On-screen text wins over the transcript for names, repo paths, URLs and commands. A name that is only heard gets "(heard, spelling uncertain)".
- Whisper invents text over music or silence ("Thank you.", repeated phrases). If the transcript does not match the frames, ignore it and base the note on frames and caption.
- A transcript starting with "[no transcript" means there was no usable speech; use frames and caption.
- A library is "on screen" only when its name, import, package or site is visible; anything else is "guessed from the look".
- Do not judge the post against anyone's projects; that happens later.
- Do not install, run or visit anything.

Reply with one line per id: "<id> ok" or "<id> problem: <what>".
```
