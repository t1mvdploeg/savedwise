# Phase 1: Profile

Goal: `<kb>/profile.md`, confirmed by the user, so the synthesis can say which tip fits which project and what is already installed.

## Gather

1. Ask where their projects are: a folder, or "none".
2. For each subfolder of that folder (one level deeper when a subfolder only groups other projects), read:
   - the first ~40 lines of `README*`, `CLAUDE.md` and `AGENTS.md`;
   - the manifest for the stack: `package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `go.mod`, `composer.json` or `Gemfile`;
   - the last commit date: `git -C <dir> log -1 --format=%cs`.
   With more than ~15 projects, hand groups of folders to subagents that return table rows only.
3. Read `~/.claude/CLAUDE.md` and the memory files `~/.claude/projects/*/memory/*.md`. Keep only what describes the user's work, goals and preferences. Never copy secrets, tokens, client data or details about other people into the profile.
4. Installed: folder names in `~/.claude/skills/`, and the keys of `~/.claude/plugins/installed_plugins.json` (`<plugin>@<marketplace>`).
5. If this yields fewer than two projects or no clear focus, ask up to three short questions: what they work on, their main stack, what they want to get better at.

## Write `<kb>/profile.md`

```markdown
# Profile

Updated <YYYY-MM-DD>. Confirmed by the user.

## Focus
<2-4 sentences: what the user builds, for whom, what they want to learn.>

## Projects
| Project | Folder | What it is | Stack | Last activity |
| --- | --- | --- | --- | --- |
| <name> | <folder relative to the projects folder> | <one line> | <main tech> | <YYYY-MM-DD> |

## Installed
Skills: <comma-separated>
Plugins: <comma-separated>

## Preferences
- <only what changes advice, e.g. "prefers CLIs over MCP servers", "avoids paid tools">
```

List projects active in the last 30 days first.

## Confirm

Show the focus, the project names and the counts of skills and plugins. Ask what is wrong or missing. Do not start phase 2 before the user confirms. The user may edit the file later; phase 5 rereads it.
