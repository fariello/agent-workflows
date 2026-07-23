# IPD (DRAFT STUB): conservative `aw uninstall` that consumes the install manifest

- Date: 2026-07-23
- Concern: safe, complete, reversible removal of agent-workflows from a repo without destroying user content
- Scope (intended): an `aw uninstall` that removes what the installer owns (per the manifest), strips only managed blocks from shared files, preserves user/workflow content by default, and offers a clearly-warned deeper `.agents/` cleanup. Details TBD.
- Status: draft
- Set: install-safety-and-ownership
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> DRAFT STUB - PRELIMINARY. Captures INTENT and OBJECTIVES only. NOT ready for /plan-review or
> execution. The "how" is deliberately unspecified and LIKELY NEEDS MORE DISCUSSION AND CLARITY.
> Do not execute.

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's original "Item 3", now scoped to build on the install-manifest/ownership model (IPD A). Preliminary; to be fleshed out after A.

## Intent and objectives

Today `aw uninstall` (`_run_uninstall` / `uninstall_repo`, engine) removes only three hard-coded namespaces (the workflow tree, generated shim `*.md`, the monolithic AGENTS pointer block) and leaves the setup artifacts (`.agents/plans|docs|prompts|comms`, `.gitleaksignore`, CI, gitignore entries) behind. There is no durable manifest it consults. The objective is a CONSERVATIVE, manifest-driven uninstall that removes everything agent-workflows provably installed while never destroying user or workflow-output content, and that OFFERS (never assumes) a deeper cleanup.

Behavior intended (per the write-safety research, `.agents/docs/research/20260722-2241-...`):

- Remove only files whose current hash still matches the last-installed hash in the manifest (IPD A). A user-modified generated file is REPORTED and left, not deleted.
- Strip only the agent-workflows-managed BLOCKS/sections from shared files (AGENTS.md, CLAUDE.md, GEMINI.md); delete the containing file only if it becomes empty AND the manifest proves the installer created it.
- PRESERVE by default: `.agents/plans/`, `.agents/docs/`, `.agents/comms/`, `workflow-artifacts/`, and anything not in the manifest. Never `rm -rf` a host directory (`.opencode/`, `.claude/`, `.github/`, `.agents/`, etc.).
- OFFER a deeper `.agents/` cleanup as an explicit, warned, interactive choice (the maintainer's original ask): options along the lines of "remove only agent-workflows-created files/dirs" vs "remove more", with a show-and-confirm and a loud warning that this may permanently delete files.
- Before any deeper cleanup, COUNT and report the untracked-or-ignored NON-agent-workflows files under `.agents/` so the user is warned about collateral before deletion.
- Handle the LEGACY monolithic block format on uninstall (recognize and remove it) but do not re-emit it.
- Stage changes, never commit/push (existing behavior).

## Objectives / must-haves (intent, not implementation)

- Manifest-driven: uninstall consults IPD A's manifest for ownership + hashes; no hard-coded namespace list as the source of truth.
- Never destroys user-authored content or workflow outputs by default; drift is reported, not clobbered.
- The deeper-cleanup prompt is self-contained (P12), warned, show-and-confirm, with a non-agent-workflows file count.
- Recognizes and removes the legacy format; does not keep it.

## Known open questions / needs discussion (NON-EXHAUSTIVE)

- Exact option set and wording for the deeper `.agents/` cleanup (all vs aw-created; how "aw-created" is proven when the manifest predates some files).
- How to count/classify "non-aw untracked or ignored" files reliably and cheaply (git plumbing vs walk); performance on large repos.
- What to do about setup artifacts that the user has since edited or filled (e.g. `.agents/plans/` full of the user's own IPDs) - preserve always, presumably, but confirm.
- Interaction with `--undo` (rollback of last install) vs uninstall (remove everything) - keep both? unify?
- Whether uninstall should also offer to remove the manifest itself and the gitignore entries.
- Dry-run and reporting format.

## Dependencies

- REQUIRES the install manifest + ownership/managed-sections model (IPD A). Should be authored/fleshed out after A is settled, since it is A's primary consumer. Also intersects the untracked-convention IPD (counting/handling untracked files).

## Approval and execution gate

DRAFT STUB. Must be fleshed out (findings, ordered validatable steps, tests incl. the write-safety golden invariants, docs sync, resolved open questions) and pass /plan-review + explicit human approval before execution. Standard execution contract applies when fleshed out.
