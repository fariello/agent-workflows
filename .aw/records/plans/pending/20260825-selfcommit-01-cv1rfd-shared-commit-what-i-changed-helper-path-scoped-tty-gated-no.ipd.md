# IPD: Shared commit-what-I-changed helper: path-scoped, TTY-gated, no add -A, no push, per-verb default message

- Date: 2026-08-25
- Kind: child
- Concern: There is no shared helper to commit exactly the files a command changed. `ipd_lifecycle._git` (ipd_lifecycle.py:538) is a private path-scoped git subprocess wrapper used only by finalize; every other verb reimplements or omits committing. To let records-mutating verbs offer to commit their own changes safely, a single reusable helper is needed that enforces the repo contract (path-scoped, no `add -A`/`-a`, no push, no hook bypass) and is TTY-gated.
- Scope: Add `agent_workflows/git_commit_helper.py` exposing a function like `offer_commit(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None) -> CommitOutcome` that: (1) stages ONLY the explicit `paths` (repo-relative; the exact files the caller touched, including deletions/renames and the regenerated index) via `git add -- <paths>` (never `-A`/`-a`); (2) commits with `message`, never `--no-verify`, never `push`; (3) is INTERACTIVE-GATED - when `interactive` is a TTY and neither `--commit`/`assume_yes` nor `--no-commit` is set, PROMPT (reuse the cli.py:2616 yes/no helper pattern honoring isatty + assume_yes); non-interactive does NOTHING unless `assume_yes`/`--commit`; `--no-commit` short-circuits; (4) does NOT fold in unrelated staged/unstaged changes - if the index already has staged paths outside `paths`, either refuse or stage-scope defensively (decision recorded); (5) returns a structured outcome (committed sha / skipped / declined / refused-dirty) for the caller to report. Reuse `ipd_lifecycle._git` or factor a tiny shared `_git` runner so there is ONE subprocess wrapper. This child delivers ONLY the helper + its unit tests; adoption is child 02.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/ipd_lifecycle.py, tests/
- Status: draft
- Set: selfcommit
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: cv1rfd

## Workflow history

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add one reusable, path-scoped, TTY-gated "commit-what-I-changed" helper (`git_commit_helper.offer_commit`) that stages only an explicit file set, commits with a caller message, never uses `add -A`/`-a`/`--no-verify`/`push`, and never folds in unrelated dirty changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the helper

- [ ] E-01 Add `agent_workflows/git_commit_helper.py` with `offer_commit(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None) -> CommitOutcome`: stage ONLY `paths` via `git add -- <paths>`, commit with `message` (no `--no-verify`, no push), interactive-gated (prompt on TTY unless `assume_yes`/`no_commit`; non-interactive is a no-op unless `assume_yes`), refuse/scope defensively if the index has unrelated staged paths, return a structured outcome. Reuse or factor a single shared `_git` subprocess runner (from ipd_lifecycle.py:538).
  - Depends on: none
  - Expected outcome: importable helper with the documented signature and contract.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `ipd_lifecycle._git` (ipd_lifecycle.py:538) is the existing path-scoped git subprocess wrapper (staging/committing during finalize) - reuse it or factor one shared runner, don't add a third.
- `cli.py:2616` is the yes/no prompt helper honoring `isatty` + assume_yes and refusing to change things silently when non-interactive without `--yes` - mirror that gating.
- Repo contract (AGENTS.md): commit ONLY files you changed, path-scoped (`git commit -- <path>`), never `add -A`/bare/`-a`, never push, never hook-bypass.

## Findings

The only missing primitive is a reusable path-scoped committer with explicit path-set + TTY gating; the git plumbing and prompt patterns already exist and must be reused, not duplicated.

## Proposed changes (ordered, validatable)

1. `git_commit_helper.py`: `offer_commit` + `CommitOutcome` + shared `_git` reuse.
2. `tests/`: unit tests for path-scoping, TTY gating, `--commit`/`--no-commit`, no-fold-in of unrelated dirty files, no push, no `--no-verify`.

## Deferred / out of scope (with reason)

- Adopting the helper into the verbs: child 02.

## Scope check

- Over-scope: none (no verb is modified in this child).
- Under-scope: none (helper + unit tests is the complete deliverable).

## Required tests / validation

- Stages and commits exactly the given paths (a file outside `paths`, dirty in the tree, is NOT committed).
- Interactive prompt path (simulated TTY) commits on yes, skips on no; non-interactive is a no-op unless `assume_yes`; `no_commit` short-circuits.
- Never invokes `add -A`/`-a`, `push`, or `--no-verify` (assert on the git argv).
- Returns the correct structured outcome for each path.

## Spec / documentation sync

- N/A for the helper itself; verb-facing docs land in child 02.

## Open questions

### OQ-01: When the index already has unrelated staged changes, refuse or defensively scope?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Default to defensive scoping (stage/commit only `paths`, leave the rest), and if that is not cleanly possible, REFUSE with a message rather than risk folding in unrelated changes. Finalize in implementation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
