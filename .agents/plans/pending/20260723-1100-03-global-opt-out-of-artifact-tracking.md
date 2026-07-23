# IPD (DRAFT STUB): global opt-out of git-tracking for artifact classes (IPDs, prompts, research)

- Date: 2026-07-23
- Concern: let a user choose that agent-workflows artifact classes (plans/IPDs, prompts, research, docs) are NOT git-tracked, without breaking the lifecycle and workflows that assume tracking
- Scope (intended): an install-time / config option to make some or all artifact classes untracked, and the workflow/instruction changes needed so the lifecycle still functions. Large, lifecycle-wide. Details TBD.
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

> DRAFT STUB - PRELIMINARY. Captures INTENT and OBJECTIVES only. NOT ready for /plan-review or
> execution. This one is LARGE and TOUCHES MANY WORKFLOWS; it DEFINITELY NEEDS MORE DISCUSSION
> AND DESIGN before being fleshed out. Do not execute.

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): spun out of the install-manifest discussion as the largest, most invasive piece. Preliminary; needs design discussion.

## Intent and objectives

Some users will not want agent-workflows to git-track their IPDs, prompts, research, or other artifacts (sensitivity, noise, policy). The objective is to let them OPT OUT of tracking some or all artifact classes, while the plan lifecycle and the workflows that produce/move those artifacts continue to work honestly.

This is invasive because the current design ASSUMES tracked artifacts in many places:

- The plan lifecycle (`.agents/plans/`) moves IPDs through directories via `git mv` and records provenance in git history; "committed deliverable" is the default for plans, run records, prompts (tracked lanes), etc.
- Comms already has a tracked/`shared` vs gitignored/`local` split; prompts have a `local/` lane; those are precedents for a per-class tracked/untracked distinction.
- Many workflow runbooks instruct "commit (never push)" for the artifacts they produce (assess/incident/migrate/spec/plan-review/etc.).

## Objectives / must-haves (intent, not implementation)

- A clear, consented choice (probably at install / in config) of which artifact classes are tracked vs untracked - not silent.
- When a class is untracked, the workflows that produce/move it must adapt: no `git mv` through tracked buckets, no "commit this" instruction for untracked classes, and the lifecycle still expresses status/disposition somehow (directory moves still work on untracked files; only the git-tracking changes).
- Honest instruction sets: the guidance must reflect the chosen mode so agents do not try to commit untracked artifacts (or fight the user's choice, the exact failure the untracked-convention IPD addresses at the single-file level).
- Coexist with: the untracked-file convention IPD (single-file escape hatch), the comms/prompts `local/` lanes, and the install-manifest/ownership model.

## Known open questions / needs discussion (NON-EXHAUSTIVE)

- Granularity: all-or-nothing, or per-class (plans / prompts / research / docs / comms) toggles? Likely per-class.
- Where the choice is stored and how it is discovered by every workflow (config? manifest? a managed directive?).
- How the plan lifecycle works untracked: directory moves still function, but "git history as the provenance/audit trail" is lost - do we need an alternative record?
- How every producing workflow's "commit (never push)" instruction becomes conditional on the class's tracking mode without bloating each runbook (single-source guidance, P8).
- Migration for existing repos that flip a class from tracked to untracked (git rm --cached, gitignore) - and the already-tracked caveat.
- Whether this is even desirable vs pointing users at the untracked-file convention + `local/` lanes for the sensitive subset (i.e. is a global mode worth its complexity?).

## Dependencies

- Builds on / coordinates with: the untracked-file convention IPD (single-file safety), the comms/prompts `local/` precedents, and the install-manifest/ownership model. Should be sequenced LAST among this cluster; needs its own design discussion before fleshing out.

## Approval and execution gate

DRAFT STUB. Requires a dedicated design discussion, then a full IPD (findings, ordered validatable steps across the affected workflows, tests, docs sync, resolved open questions) and /plan-review + explicit human approval before any execution. Standard execution contract applies when fleshed out.
