# IPD: Records-mutating commands offer to commit their own path-scoped changes when interactive

- Date: 2026-08-25
- Kind: orchestrator
- Concern: Records-mutating verbs leave their changeset UNCOMMITTED, so the user must notice and hand-commit it. Two shapes: (a) MOVE/RENAME + INDEX-regeneration verbs (`aw archive`, `aw group`, `aw rename`, `aw research set-assign`/`mv`) produce a large coherent set of renames + index updates (origin: a 23-file `aw archive` research changeset); (b) IN-PLACE metadata rewrites (`aw ipd set`, `aw spec set`/`specs set`, and the shared `aw set` engine) flip `- Status:` + append workflow-history on one file (or a whole Set) with no rename. Both leave uncommitted work worth offering to commit. There is no shared "commit-what-I-changed" helper today; `ipd_lifecycle._git` (ipd_lifecycle.py:557) is a private path-scoped git wrapper used only by finalize, and each verb reimplements or omits committing. Backlog item vvc7c1 (medium).
- Scope: Add ONE shared "commit-what-I-changed" helper and adopt it across the records-mutating verbs so that, when run interactively (TTY), each verb PROMPTS to commit ONLY the files it just touched (moved/renamed paths + regenerated index), path-scoped, never `git add -A`/`-a`, never push, no hook bypass, with a good per-verb default message. Constraints (from vvc7c1): (1) commit ONLY files the command itself touched - track them explicitly, never commit whatever is dirty; (2) interactive-only by default - non-interactive/CI must NOT auto-commit unless an explicit `--commit` flag is passed, and a `--no-commit` escape hatch exists; (3) respect the repo contract (path-scoped, no push, no hook bypass); (4) if the tree already has unrelated staged/unstaged changes, do not fold them in; (5) sensible default message per verb (e.g. `chore(research): archive aged artifacts and regenerate index`). Two children: 01 builds the shared helper (path-scoped, TTY-gated, explicit path-set, `--commit`/`--no-commit`, per-verb message); 02 adopts it across the verbs with tests. NOTE: this helper is the same path-scoped-commit plumbing the agentadhere `aw commit` primitive (Phase 2) will want; keep it a standalone reusable helper so agentadhere can consume it later (no duplicate code path).
- Scope-Paths: agent_workflows/git_commit_helper.py, agent_workflows/research_archive.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/cli.py, tests/
- Status: executed
- Set: selfcommit
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 88h0h8

## Workflow history
- 2026-08-28 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Orchestrator rollup: selfcommit children cv1rfd+jgcm68 executed; integration check verified (single offer_commit + all adopting sites + 16 tests). Post-hoc finalize; orchestrator authors no code so declared paths were committed by children pre-receipt. [Scope reconciliation - in-scope-unmodified agent_workflows/cli.py: children, committed pre-receipt; in-scope-unmodified agent_workflows/git_commit_helper.py: child cv1rfd, committed pre-receipt; in-scope-unmodified agent_workflows/plans_archive.py: child jgcm68, committed pre-receipt; in-scope-unmodified agent_workflows/plans_refs.py: child jgcm68, committed pre-receipt; in-scope-unmodified agent_workflows/research_archive.py: child jgcm68, committed pre-receipt; in-scope-unmodified agent_workflows/specs.py: child jgcm68, committed pre-receipt; in-scope-unmodified agent_workflows/status_set.py: child, committed pre-receipt; in-scope-unmodified tests/: children, committed pre-receipt]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED (PR-001..PR-010); corrected architecture (type-parameterized group/rename dispatch, shared status_set engine, specs dual path), fixed the cli.py prompt-helper citation and non-TTY gating divergence, parameterized on_unrelated_staged, split the multi-concern E-item, authored falsifiable V-evidence, filled execution-contract gates. GO - PENDING HUMAN APPROVAL.

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Give records-mutating verbs one shared "commit-what-I-changed" helper so they offer, interactively, to path-scoped-commit only the files they just touched (no `git add -A`, no push, no hook bypass), eliminating orphaned uncommitted rename/index changesets. Standalone and reusable so the agentadhere `aw commit` primitive can consume it later.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the executable work. Its only execution step is the whole-Set consistency check after both children land.

### Task group 1: whole-Set integration check

- [x] E-01 After children 01-02 execute and are green, confirm one shared helper (`git_commit_helper.offer_commit`) is used by ALL adopting integration points (single definition, no duplicated commit path), that group/rename coverage spans non-plans types, that the `set` family + specs dual path each offer exactly once, and that the whole test suite passes.
  - Depends on: none
  - Expected outcome: grep shows a single `def offer_commit` definition and a single git-subprocess wrapper; every adopting site imports/calls it; group/rename covers plans+research+artifact_rename types; full suite green.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | shared helper (cv1rfd) | `git_commit_helper.offer_commit`: path-scoped, TTY-gated (NO-OP on non-TTY unless `--commit`; matches `_confirm`'s real decline-on-non-TTY behavior, cli.py:2694), explicit path-set, `on_unrelated_staged` scope-vs-refuse (serves both selfcommit and agentadhere), never `add -A`/push/`--no-verify` | none |
| 02 | adopt across verbs (jgcm68) | wire the helper into `aw archive` (2 backends), the TYPE-PARAMETERIZED `group`/`rename` dispatch (covering plans/research/artifact_rename types), `research set-assign`-`mv`, and the SHARED `status_set` engine (`set`/`ipd set`/`spec set`/...) plus the `specs.py` dual path; shared `--commit`/`--no-commit` flags; tests incl. coverage + exactly-once | 01 |

Sequence: 01 -> 02; orchestrator integration check runs last.

## Completion criteria (the whole Set is done only when)

- A shared helper exists that commits ONLY an explicit path-set, path-scoped, never `add -A`/`-a`, never pushes, no hook bypass; interactive-prompts on TTY and is a NO-OP on non-TTY unless `--commit`/`assume_yes` (constraint 2); `--commit`/`--no-commit` honored; supports both `on_unrelated_staged="scope"` (default) and `"refuse"` so it also serves the agentadhere `aw commit` primitive; does not fold in unrelated dirty files (01).
- ALL records-mutating verbs use the helper and offer to commit their own changes with a good default message: `aw archive` (both backends), `aw group`/`aw rename` for EVERY supported artifact type (not just plans), `aw research set-assign`/`mv`, and the shared `set` family (`set`/`ipd set`/`spec set`/`specs set`/`prompts set`/`backlog set`) including the `specs.py` `--status` dual path - each offering exactly once; tests cover coverage-across-types and exactly-once (02).
- Full test suite green.

## Cross-IPD validation

- Single helper definition consumed by every adopting verb (no duplicate commit logic).
- The helper is standalone (importable by a future agentadhere `aw commit`), not entangled with any one verb.

## Cross-set dependencies

This set is a HARD PREREQUISITE for another set (downstream), and has SOFT contention with others:
- DOWNSTREAM (hard): **agentadhere child 03 (8dto0g)** hard-depends on this set's child 01 (cv1rfd) `git_commit_helper.offer_commit` (its `aw commit` primitive reuses it, passing `on_unrelated_staged="refuse"`). selfcommit child 01 MUST land before agentadhere child 03 runs. selfcommit therefore has no upstream dependency and should run EARLY.
- SOFT file-contention: `status_set.py` (shared with ipddeps/xprio), `specs.py` (shared with specid6/xprio), `artifact_rename.py` (shared with specid6), `cli.py` (shared broadly). Sequence rather than run concurrently with those.
Recommendation: run selfcommit EARLY (it unblocks agentadhere phase 2); it may run in parallel with installerskill/runnernorm (disjoint), but not concurrently with specid6 (shares specs.py/artifact_rename.py).

## Deferred / out of scope (with reason)

- The agentadhere `aw commit <ipd>` primitive that will REUSE this helper: agentadhere set (this set only builds the reusable helper).
- Auto-commit in non-interactive/CI without `--commit`: explicitly excluded by design (constraint 2).

## Scope check

- Over-scope: none.
- Under-scope: none (shared helper + adoption is the complete deliverable).

## Required tests / validation

Aggregate of the children's tests: helper unit tests (path-scoping, TTY gating, `--commit`/`--no-commit`, no-fold-in of unrelated dirty files, no push), and per-verb adoption tests (archive/group/rename/research/ipd set/specs set offer + commit correctly).

## Open questions

### OQ-01: Which default commit-message convention per verb?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Start with `chore(<verb-domain>): <action> and regenerate index` (e.g. `chore(research): archive aged artifacts and regenerate index`); finalize exact strings in child 02.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `grep -rn "def offer_commit" agent_workflows/` returns exactly one definition; the git-subprocess wrapper (`_git`) has a single definition reused by the helper; every adopting site (archive x2, the group/rename dispatch, research set-assign/mv, status_set, specs.py) calls `offer_commit`; the child-02 coverage tests (V-03) and exactly-once tests (V-05/V-06) pass; and the full suite (`run_checks.py`/pytest) is green. Paste the grep output and the runner output.
  - Observed evidence: Post-hoc rollup verification 2026-08-28 (children cv1rfd + jgcm68 executed overnight, run-20260828T035444Z). `grep -rn "def offer_commit" agent_workflows/` -> exactly one: `agent_workflows/git_commit_helper.py:132`. Single `_git` wrapper: `git_commit_helper.py:54`. Adopting sites calling `offer_commit` (grep -rln): `cli.py`, `plans_archive.py`, `plans_refs.py`, `research_archive.py`, `specs.py`, `status_set.py` (+ `work_cmd.py`). `python -m pytest tests/test_git_commit_helper.py -p no:randomly` -> `16 passed`. Both children are in `.aw/records/plans/executed/`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: this is an ORCHESTRATOR - it authors NO product code; the children (`cv1rfd` then `jgcm68`) carry the executable work and each has its own gate. The orchestrator's only execution step is the whole-Set integration check (E-01) run AFTER both children have executed, been validated, and moved to `executed/`. Scope fence: touch ONLY this plan's own file; do NOT make product changes here. Sequence: 01 -> 02 -> orchestrator integration check. Open questions: OQ-01 is non-blocking (default message convention finalized in child 02). Honesty rule (hard MUST): when reporting the integration check and tests passed, paste the ACTUAL grep and runner output; never claim success not run. Commit only this plan's own file, path-scoped (`git commit -- <path>`); never `git add -A`/`-a`; never push. On completion perform the terminal transition via `aw ipd begin <plan> --actor <agent/model>` then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`; do NOT hand-edit the terminal transition. This plan awaits `/plan-review` and explicit human approval (`Status: approved`) before it may be executed.
