# Phase 5: Synthesis

Goal: one `domains/N-<slug>.md` per topic, an `OVERVIEW.md` and, when notes have a `## Design` section, a `STYLE.md`, tied to the user's profile. Reread `profile.md` first.

## 1. Domains

- Read every note. With more than ~40 notes, have subagents return one line per note: `id | maker | title | tools | one-line verdict`.
- Choose 4 to 10 domains from the content, ordered by relevance to the profile. A final "Other" domain is fine.
- Every post goes in exactly one domain. When adding posts to an existing knowledge base, put them in the existing domains; add a domain only when at least three new posts fit none.

## 2. Judging overlap

When posts cover the same thing, the better one:

1. is concrete enough to follow (name, repo or command visible);
2. does not hide the substance behind "comment X for the link";
3. points to something that exists and is maintained. If `gh` is available, check repos with `gh api repos/<owner>/<repo> --jq '"\(.stargazers_count) \(.pushed_at) \(.archived)"'`; otherwise write "not checked";
4. fits the profile.

The tools are not installed or tested. "Winner" means best source. Say what was not checked, such as terms of service.

## 3. Domain file

```markdown
# <Domain name>

[← Overview](../OVERVIEW.md)

✅ already installed · 🆕 new and worth it · ⚠️ caution · ⏭️ skip

<One sentence: what this domain covers and how many posts it has.>

## <Sub-topic>

| Post | What | Verdict |
| --- | --- | --- |
| [<maker>: <short title>](../items/<id>.md) | <one line> | <marker> <one line> |

**Fits your projects**
- <project from profile.md>: <tip>, because <reason>.

## Advice

- <3-6 bullets in order of value, with the exact commands or repo paths>
```

✅ comes only from the Installed list in `profile.md`. Leave out "Fits your projects" when nothing fits; do not force a match.

## 4. OVERVIEW.md

```markdown
# Overview: saved posts

<N> posts from <collections>. Processed <YYYY-MM-DD>.

**How "better" was decided.** <the four criteria above, one line each>

**What was not done.** The tools were not installed or tested. "Winner" means best source, not proven best tool.

✅ already installed · 🆕 new and worth it · ⚠️ caution · ⏭️ skip

## Do these first

| # | What | Why for you | Project | Source |
| --- | --- | --- | --- | --- |
| 1 | <action with command or repo> | <reason tied to the profile> | <project or —> | [<maker>](items/<id>.md) |

## Domains

| # | Domain | Posts | Core |
| --- | --- | --- | --- |
| 1 | [<name>](domains/1-<slug>.md) | <n> | <the winners in a few words> |

## Skill ideas

Skills worth building from these posts. Not built; ask and I will build one.

| Skill | What it would do | Based on | Serves |
| --- | --- | --- | --- |
| <name> | <one or two lines> | [<maker>](items/<id>.md), … | <project or workflow> |

## What stood out

- <3-5 patterns: bait, duplicates, how much the user already has, what was missing>

**Style.** <one line on the recurring look> See [STYLE.md](STYLE.md).
```

- "Do these first": 5 to 10 rows, ranked by value for this user.
- Skill ideas: 2 to 5, each backed by at least two posts, or one post plus a pattern visible in the profile. Skip anything already in the Installed list.
- Domain files link with `../items/<id>.md`, the overview with `items/<id>.md`. A domain's content lives only in its file, not repeated in the overview.

- Leave out the **Style** line when there is no `STYLE.md`.

## 5. STYLE.md

Only when at least one note has a `## Design` section (`grep -l "^## Design" <kb>/items/*.md`). Read those sections, not the whole notes.

```markdown
# Style: the designs you saved

[← Overview](OVERVIEW.md)

<N> posts show a website, app or interface.

## Recurring style

- **Colours:** <what keeps coming back, with hex codes when notes have them> (<n> posts)
- **Type:** <…>
- **Layout:** <…>
- **Effects:** <…>

## Libraries that keep showing up

| Library | Posts | How sure |
| --- | --- | --- |
| <name> | [<maker>](items/<id>.md), … | on screen in <n>, guessed in <m> |

## Best examples

| Post | Why |
| --- | --- |
| [<maker>: <short title>](items/<id>.md) | <what to take from it> |
```

- Only patterns seen in at least two posts go under "Recurring style"; give the count.
- Libraries: most posts first. A library only ever guessed from the look gets "guessed only"; never present a guess as fact.
- Best examples: 3 to 8 posts, chosen for how clearly the design shows and how much can be reused, not for the claims in the post.

## 6. Check and finish

Run `uv run <skill>/scripts/check.py <kb>` until it prints `ok`. Posts it lists as "not fetched" could not be downloaded; they need no note and do not belong in a domain. Then tell the user where `OVERVIEW.md` (and `STYLE.md`) is, the top three actions, which posts failed, and offer to build one of the skill ideas.
