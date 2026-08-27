# IPD: Shared commit-what-I-changed helper: path-scoped, TTY-gated, no add -A, no push, per-verb default message

- Date: 2026-08-25
- Kind: child
- Concern: There is no shared helper to commit exactly the files a command changed. `ipd_lifecycle._git` (ipd_lifecycle.py:557) is a private path-scoped git subprocess wrapper used only by finalize; every other verb reimplements or omits committing. To let records-mutating verbs offer to commit their own changes safely, a single reusable helper is needed that enforces the repo contract (path-scoped, no `add -A`/`-a`, no push, no hook bypass) and is TTY-gated.
- Scope: Add `agent_workflows/git_commit_helper.py` exposing a function like `offer_commit(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None, on_unrelated_staged="scope") -> CommitOutcome` that: (1) stages ONLY the explicit `paths` (repo-relative; the exact files the caller touched, including deletions/renames and the regenerated index) via `git add -- <paths>` (never `-A`/`-a`); (2) commits with `message`, never `--no-verify`, never `push`; (3) is INTERACTIVE-GATED - when `interactive` is a TTY and neither `assume_yes` (the `--commit` flag) nor `no_commit` is set, PROMPT using the SAME prompt UX as the existing `_confirm` helper (cli.py:2689, which honors `isatty`); `no_commit` short-circuits to a no-op. CRITICAL DIVERGENCE FROM `_confirm`: unlike `_confirm` (cli.py:2694, which auto-YES on non-interactive stdin), this helper's non-interactive default is a NO-OP (skipped, not committed) unless `assume_yes` (`--commit`) is explicitly passed - this is orchestrator constraint 2 and is the opposite of `_confirm`'s non-TTY behavior, so do NOT blindly reuse `_confirm` for the gate decision; reuse only its TTY prompt rendering. (4) does NOT fold in unrelated staged/unstaged changes - `on_unrelated_staged` selects the policy when the index already holds staged paths OUTSIDE `paths`: `"scope"` (default; stage/commit only `paths`, leave the rest untouched) or `"refuse"` (return `refused-dirty` without committing). Both consumers are served: selfcommit verbs pass `"scope"`; the agentadhere `aw commit` primitive (child 8dto0g E-03) passes `"refuse"`. (5) returns a structured outcome (committed sha / skipped / declined / refused-dirty) for the caller to report. Reuse `ipd_lifecycle._git` (ipd_lifecycle.py:557) or factor a tiny shared `_git` runner so there is ONE subprocess wrapper. This child delivers ONLY the helper + its unit tests; adoption is child 02.
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/ipd_lifecycle.py, tests/
- Status: reviewed
- Set: selfcommit
- Order: 1
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: cv1rfd

## Workflow history
- 2026-08-27 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED (PR-001..PR-010); corrected architecture (type-parameterized group/rename dispatch, shared status_set engine, specs dual path), fixed the cli.py prompt-helper citation and non-TTY gating divergence, parameterized on_unrelated_staged, split the multi-concern E-item, authored falsifiable V-evidence, filled execution-contract gates. GO - PENDING HUMAN APPROVAL.

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add one reusable, path-scoped, TTY-gated "commit-what-I-changed" helper (`git_commit_helper.offer_commit`) that stages only an explicit file set, commits with a caller message, never uses `add -A`/`-a`/`--no-verify`/`push`, and never folds in unrelated dirty changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the helper

- [ ] E-01 Add `agent_workflows/git_commit_helper.py` with `offer_commit(repo_root, paths, *, message, assume_yes=False, no_commit=False, interactive=None, on_unrelated_staged="scope") -> CommitOutcome`: stage ONLY `paths` via `git add -- <paths>`, commit with `message` (no `--no-verify`, no push), interactive-gated (prompt on TTY unless `assume_yes`/`no_commit`; non-interactive is a NO-OP unless `assume_yes` - the OPPOSITE of `_confirm`'s non-TTY auto-yes, so reuse only `_confirm`'s TTY prompt rendering, not its gate decision), honor `on_unrelated_staged` (`"scope"` default vs `"refuse"`) when the index holds unrelated staged paths, return a structured outcome. Reuse or factor a single shared `_git` subprocess runner (from ipd_lifecycle.py:557).
  - Depends on: none
  - Expected outcome: importable helper with the documented signature and contract.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `ipd_lifecycle._git` (ipd_lifecycle.py:557) is the existing path-scoped git subprocess wrapper (staging/committing during finalize) - reuse it or factor one shared runner, don't add a third.
- `_confirm(term, prompt, assume_yes)` (cli.py:2689) is the repo's yes/no prompt helper. It honors `isatty` and `assume_yes`. IMPORTANT: `_confirm` AUTO-ANSWERS YES when stdin is non-interactive (cli.py:2694) - reuse only its TTY prompt RENDERING for the interactive branch; the gate DECISION must NOT auto-yes on non-TTY (orchestrator constraint 2: non-interactive is a no-op unless `--commit`/`assume_yes`). Contrast `_prompt_yes_no` (cli.py:2707), which never auto-answers; neither matches the required "no-op on non-TTY unless assume_yes" semantics exactly, so the helper implements that gate itself.
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

- Stages and commits exactly the given paths (a file outside `paths`, dirty in the tree, is NOT committed); assert the committed tree contains only `paths` and the unrelated dirty file remains uncommitted.
- Interactive prompt path (simulated TTY, e.g. monkeypatched `isatty`/input) commits on yes, skips (`declined`) on no; non-interactive (non-TTY) WITHOUT `assume_yes` is a NO-OP returning `skipped` (explicitly assert it does NOT auto-commit, guarding against the `_confirm` non-TTY auto-yes divergence); non-interactive WITH `assume_yes` commits; `no_commit=True` short-circuits to `skipped` regardless of TTY.
- `on_unrelated_staged`: with a pre-staged unrelated path, `"scope"` commits only `paths` and leaves the unrelated staged path staged-but-uncommitted; `"refuse"` returns `refused-dirty` and commits nothing.
- Never invokes `git add -A`/`-a`, `git push`, or `--no-verify` (assert on the captured git argv across every branch).
- Returns the correct structured `CommitOutcome` (committed sha / skipped / declined / refused-dirty) for each branch.

## Spec / documentation sync

- N/A for the helper itself; verb-facing docs land in child 02.
- Import-direction note: `git_commit_helper` is a low-level leaf module and MUST NOT import `cli.py` (that would invert the dependency and risk a cycle). Reuse the `_confirm` prompt UX by REIMPLEMENTING an equivalent tiny yes/no render inside the helper (or factoring a shared prompt primitive into a leaf module), not by importing from `cli`. This is why `cli.py` is deliberately absent from this child's `Scope-Paths`.

## Open questions

### OQ-01: When the index already has unrelated staged changes, refuse or defensively scope?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED (plan-review PR-005): support BOTH policies via an `on_unrelated_staged` parameter rather than picking one, because the two known consumers need different behavior. `"scope"` (the default, used by the selfcommit records-mutating verbs in child 02) stages/commits ONLY `paths` and leaves any unrelated staged path untouched. `"refuse"` (used by the agentadhere `aw commit` primitive, child 8dto0g E-03, which must reject any out-of-scope staged change) returns a `refused-dirty` outcome without committing. In both modes the helper NEVER stages a path outside `paths`; the only difference is whether pre-existing unrelated staged content aborts the commit or is left alone. This keeps one shared helper serving both Sets (no forked commit path).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The new `tests/` module for `git_commit_helper.offer_commit` passes, and its captured pytest output shows assertions for: (a) only `paths` committed while an unrelated dirty file stays uncommitted; (b) the non-TTY-without-`assume_yes` NO-OP branch (returns `skipped`, no commit created) AND the `assume_yes` commit branch AND the `no_commit` short-circuit AND interactive yes/no branches; (c) both `on_unrelated_staged="scope"` and `"refuse"` behaviors; (d) a captured-git-argv assertion proving no `add -A`/`-a`, no `push`, no `--no-verify` on any branch. Paste the actual `run_checks.py` (or pytest) command and its output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: touch ONLY the declared `Scope-Paths` (`agent_workflows/git_commit_helper.py`, `agent_workflows/ipd_lifecycle.py`, `tests/`) plus this plan's own file. Scope fence: this child builds the shared helper and its unit tests ONLY; it MUST NOT modify any records-mutating verb (that is child 02) and MUST NOT introduce a second git subprocess wrapper (reuse/factor the single `ipd_lifecycle._git`). Open questions: OQ-01 is resolved (parameterized `on_unrelated_staged`); no blocking question remains. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output (the `run_checks.py`/pytest command and its result); never claim success not run. Commit only files this plan changes, path-scoped (`git commit -- <path>`); never `git add -A`/`-a`; never push; never `--no-verify`. On completion perform the terminal transition via `aw ipd begin <plan> --actor <agent/model>` then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`; do NOT hand-edit the terminal transition or move the file by hand. This plan awaits `/plan-review` and explicit human approval (`Status: approved`) before it may be executed.
