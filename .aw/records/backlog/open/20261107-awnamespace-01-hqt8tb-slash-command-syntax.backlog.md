- Id: hqt8tb
- Status: open
- Set: awnamespace
- Priority: high
- Work-Kind: feature
- Summary: Choose the slash-command syntax: /aw-<verb>, /<verb>, or both, never /aw <verb>; research host collisions and completion first, then reverse the unreleased /aw dispatcher decision (2bodwq) before 1.3.0

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-09 note (aw backlog): proofread per the technical writing standard (spec ecmw83 R-08); meaning unchanged
- 2026-11-07 created (aw backlog): filed from maintainer note 2026-11-07: /aw <verb> is unwieldy and unused; ruling: /aw-<verb> or /<verb> or both, not /aw <verb>

## Problem

aw installs its workflows as slash commands in agent hosts (OpenCode, Claude Code, and others). Research Set `awnamespace` (reconciliation `2bodwq`, 2026-08-13) chose one dispatcher command, `/aw <verb> [args...]`, and planned to drop the per-verb commands by default. Commit `19f11bc48` (2026-08-19) implemented the dispatcher on `main`. No release contains it: `v1.2.0-recreated` and `v1.3.0-rc.1` predate that commit.

Maintainer finding (2026-11-07, from daily use): `/aw <verb>` is unwieldy, and he never uses it. Maintainer ruling: the public syntax will be `/aw-<verb>`, `/<verb>`, or both. It will NOT be `/aw <verb>`. Which of the three is not decided.

Current state on `main` (measured 2026-11-07):
- `.opencode/commands/` and `.claude/commands/` each install 28 commands: `aw.md` (the dispatcher) plus 27 bare `/<verb>` commands (`/advise`, `/askme`, ...).
- Each bare command carries a deprecation comment, for example `/advise` is deprecated; prefer `/aw advise`. The CHANGELOG already exempts `/askme` from that deprecation.
- No `/aw-<verb>` command is installed.

## What to decide

1. Public syntax: `/aw-<verb>`, `/<verb>`, or both. If both, which one is canonical, and whether the other is a permanent alias.
2. What happens to the `/aw` dispatcher: remove it, or keep it as an undocumented compatibility entry.
3. What happens to the deprecation comments on the 27 bare commands.
4. Which docs, installer code, managed AGENTS.md text, and tests change.

## Research needed before deciding

Market research with users is not available. Use evidence instead:
- Name collisions: for each supported host, list the built-in and common third-party slash commands, and count collisions with the 27 verb names (for example `/review`, `/init`, `/help`). `2bodwq` section 5 has per-host findings to re-check.
- Host constraints: whether each host allows `-` in command names, how it sorts and completes commands (does `/aw-` group the commands in the completion list?), and any length limit.
- Typing cost and discoverability: keystrokes per form, and whether typing `/aw-` then completing lists only aw commands.
- How comparable tools name their slash commands.
- Re-read the `2bodwq` reasons for rejecting flat commands and state, for each reason, whether it still holds.

Write the evidence as a research record (`aw research new --apply`) and ask the maintainer to choose through `/askme`.

## Done when

- The maintainer has chosen the syntax, and the choice is recorded in `DECISIONS.md` and in this item.
- Installer, commands, docs, and tests match the choice, with test output pasted.
- `2bodwq` gets a workflow note that points to the new decision (its adopted dispatcher decision is reversed).
- This lands before 1.3.0 ships, because `main` currently tells users to prefer `/aw <verb>`.
