# IPD (DRAFT STUB): untracked-file safety convention + install-time tracking warning

- Date: 2026-07-23
- Concern: data-exposure safety - give agents and users a self-evident way to keep sensitive files out of git, and warn users that agent-workflows git-tracks IPDs/prompts/research
- Scope (intended): a gitignore convention (`*.untracked.*` files and `*untracked*/` directories) the installer adds with an explanatory comment, plus an install-time warning about what gets tracked. Details TBD.
- Status: draft
- Set: install-safety-and-ownership
- Order: 2
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> DRAFT STUB - PRELIMINARY. This IPD captures INTENT and OBJECTIVES only. It is NOT ready for
> /plan-review or execution. The "how" is deliberately unspecified and LIKELY NEEDS MORE
> DISCUSSION AND CLARITY before it is fleshed out. Do not execute.

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): captured from a maintainer request during the install-manifest discussion, spun out as its own prioritized safety IPD. Preliminary; to be fleshed out later.

## Intent and objectives

The maintainer has repeatedly hit a failure mode: sensitive IPDs/notes that should have stayed untracked got committed because directives (or an agent) overrode the intent to keep them local. This IPD's objective is a simple, agent-obvious, hard-to-get-wrong escape hatch:

- On install, add to the repo's `.gitignore` (in the agent-workflows-managed way, identifiable and removable) patterns that exclude any file named `*.untracked.*` and any directory named `*untracked*/`, with a clear comment stating that agents and users can safely use this naming as a deliberate "do not track/commit this" mechanism.
- Make the instruction sets / agent guidance AWARE of this convention so an agent, when it needs to write something sensitive or provisional, can name it accordingly and trust it will not be committed.
- Separately (but related): WARN the user at install time that agent-workflows git-tracks IPDs, prompts, research, and similar artifacts by default; that this is extremely useful (durable, travels, auditable) but means they and especially their agents should be cautious about what goes into those files; and point them at the untracked convention (and the comms `local/` and prompts `local/` lanes) as the safety valves.

## Objectives / must-haves (intent, not implementation)

- A naming convention that is obvious and needs no lookup: seeing `foo.untracked.md` or `scratch-untracked/` should tell any agent "this is not tracked."
- The gitignore entries are added in an identifiable, agent-workflows-managed, removable way (consistent with the managed-sections/ownership model, IPD A).
- Agent guidance explicitly authorizes and explains the convention so agents use it for sensitive/provisional content instead of committing it.
- An honest, plain-language install-time warning about default tracking of IPDs/prompts/research, with the safety valves named.

## Known open questions / needs discussion (NON-EXHAUSTIVE)

- The already-tracked-file CAVEAT: a `.gitignore` pattern only stops FUTURE tracking; a file already committed stays tracked even if renamed to match, absent `git rm --cached`. How (and whether) to detect/warn about that.
- Exact patterns and case sensitivity (`*.untracked.*`, `*untracked*/`, upper/lower, nested).
- Whether the warning is interactive (consent to proceed) or informational, and how it fits the per-directive consent model (IPD A / interactive-questions rule P12).
- Interaction with the existing comms `local/` (gitignored) and prompts `local/` lanes - is this convention additive, or should those be unified/cross-referenced?
- Where the agent-facing explanation of the convention lives (AGENTS.md managed section? a directive file? both?) and how it is delivered token-efficiently (ties to IPD A markers/manifest).
- Whether a leak-sanitizer or install check should flag sensitive-looking tracked files.

## Dependencies

- Best built ON the managed-sections/ownership model (IPD A) so the gitignore additions are identifiable/removable and any AGENTS.md guidance is a consented section. Could ship a minimal version independently, but coordinate to avoid two gitignore-management paths.

## Reference implementation (maintainer-provided; adopt as the proposed content)

The maintainer field-tested this exact block in another repo's `.gitignore`. Adopt it as the canonical content for the managed `.gitignore` section (note the markers are `#`-commented because `.gitignore` has no HTML-comment syntax; see the two-marker-syntax note below). Patterns: `*.untracked.*`, `*.untracked`, `**/*untracked*/` (this supersedes the earlier stub's narrower `*.untracked.*` + `*untracked*/`; it also catches an extensionless `scratch.untracked` and an `untracked`-containing dir nested anywhere).

```
# <!-- aw:block -->
# --- Deliberately-untracked local artifacts (DO NOT REMOVE these patterns) ---
#
# Purpose: provide a RELIABLE way to keep a file or directory OUT of git even when it
# lives inside a directory that agent directives would otherwise tell an agent to commit
# (e.g. AGENTS.md / the .agents/plans lifecycle rules say IPDs live under .agents/plans/
# and should be committed and moved pending -> executed). Some work is sensitive enough that
# it must NOT be tracked or pushed (incident/remediation notes, scratch audits, local-only
# working docs), yet it is convenient to keep it next to the related tracked files.
#
# Naming a file or directory with the "untracked" marker below makes git ignore it, so a
# blanket `git add .`, `git add -A`, the pre-commit hooks, and the sanitizer never stage it.
# This is a PASSIVE guard that works WITH the tooling: it does not rely on any agent
# remembering a special rule or resisting a lifecycle directive.
#
# How to use:
#   - A single file:      my-notes.untracked.md   audit.untracked.json   scratch.untracked
#   - A whole directory:  put files under any dir whose name contains "untracked",
#                         e.g. .agents/plans/pending/untracked/  or  foo.untracked/
#
# IMPORTANT LIMITS (so this is not over-trusted):
#   - This only affects files that are NOT already tracked. Gitignoring a pattern does NOT
#     untrack an already-committed file, and it does NOT remove a name from history. Name
#     the file with the marker BEFORE it is ever `git add`ed.
#   - `.gitignore` is advisory: `git add -f` bypasses it. "Untracked by default" is the goal,
#     not an enforcement boundary.
#
# DO NOT delete or narrow these patterns to "clean up" the ignore file: they are a
# deliberate safety mechanism, and removing them can cause sensitive local files to become
# trackable (and then accidentally committed) by a later `git add`.
*.untracked.*
*.untracked
**/*untracked*/
# <!-- /aw:block -->
```

## Two-marker-syntax note (for the parser, ties to IPD 02)

The managed-block markers must be rendered in the target file's OWN comment syntax: bare `<!-- aw:... -->` in Markdown, and `#`-prefixed `# <!-- aw:... -->` in `#`-comment config files (`.gitignore`, YAML, TOML). The IPD-02 managed-block parser/writer must therefore treat "the aw marker" as one logical construct with a per-file-syntax rendering, not assume HTML comments everywhere. This block is the first `#`-comment instance.

## General policy this establishes (coordinate with IPD 02)

Per the maintainer: EVERY agent-workflows-managed block we add to a shared config file (`.gitignore` and others) should carry (a) the `aw:block` markers in that file's comment syntax so it is identifiable and removable, and (b) a short "DO NOT REMOVE, this is deliberate" rationale. IPD 02 (managed-sections model) should establish this as the general rule; this IPD is the first concrete application.

## Approval and execution gate

DRAFT STUB. Must be fleshed out into a full IPD (findings, ordered validatable steps, tests, docs sync, resolved open questions) and pass /plan-review + explicit human approval before any execution. Standard execution contract will apply when fleshed out: path-scoped commits, never push, paste real test output, no em/en dashes, STOP-and-report on scope growth.
