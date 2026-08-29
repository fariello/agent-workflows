# IPD: a terminal plan's leaked begin receipt must not drive the commit-scope gate

- Date: 2026-08-29
- Kind: child
- Concern: `check_scope_drift` treats ANY begin receipt on disk as an in-flight execution. Four receipts currently belong to plans already in `executed/`, so the shared commit-invariant aggregator reports 74 findings on this checkout, 24 of them from those terminal plans. The opt-in `precommit-scope-gate` hook delegates to that aggregator, so installing it today would refuse every commit by every session in this repo.
- Scope: Make `check_scope_drift` ignore a receipt that cannot describe an in-flight execution: one whose plan is in a TERMINAL lifecycle directory, and one whose frozen base is no longer reachable from HEAD. Adds the liveness predicate and its tests only. Does NOT change the ownership/attribution rule (backlog `077yqc`), does NOT install the hook, and does NOT touch the receipt-leak source in the runner.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_receipt_liveness.py
- Item-Dependencies: none
- Status: to-review
- Set: gatestale
- Order: 1
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: rygds7
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after measuring that the SHIPPED `precommit-scope-gate` hook cannot be safely enabled. Scope was deliberately NARROWED at authoring time: the companion contract-wording fix was dropped because plan `uyd3lw` is CURRENTLY EXECUTING with `agent_workflows/engine.py` and `AGENTS.md` in its declared Scope-Paths, and this plan must not touch another in-flight plan's files.

## Goal

Make the commit-scope gate believe only receipts that can still describe work in progress. A begin receipt is execution AUTHORITY for one in-flight plan; once that plan reaches a terminal directory the receipt is a leaked artifact, but the gate still reads it and compares the whole working tree against a dead frozen base. Fixing this is a precondition for ever enabling the hook, which is the mechanical half of the anti-clobbering protection.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: only trust a live receipt

- [ ] E-01 In `agent_workflows/check_engine.py`, add a small pure predicate (e.g. `_receipt_is_live(repo_root, plan_path, receipt)`) that returns False when the receipt cannot describe an in-flight execution, and use it in `check_scope_drift` immediately after the existing `if not receipt: continue` (check_engine.py:985-987). It must reject two cases: (1) TERMINAL PLAN, the plan file resides in a terminal lifecycle directory (`executed/`, `superseded/`, `not-executed/`), determined from the plan's own path rather than by re-parsing status text; (2) UNREACHABLE BASE, `base_head` is not an ancestor of HEAD, so the frozen baseline no longer describes this history. Keep the existing `unversioned`/empty-base skip. Do not change the comparison itself.
  - Depends on: none
  - Expected outcome: `check_commit_invariants` on this checkout drops from 74 findings to 50, with all 24 findings attributable to the four terminal plans (`8zgybk`, `qmt3yk`, `v58bvy`, `v7e88a`) gone and every in-flight plan's findings unchanged.
  - Execution state: pending

- [ ] E-02 Make the predicate fail SAFE rather than fail OPEN. If liveness cannot be determined (git unavailable, unreadable path, `merge-base` error), treat the receipt as NOT live and skip it, because a false refusal blocks a legitimate commit while a missed advisory is recoverable, and this gate is explicitly documented as best-effort local FEEDBACK rather than an authority boundary (`hooks/precommit_scope_gate.py` module docstring). Record the choice in a comment citing that docstring so the asymmetry is not later "corrected".
  - Depends on: E-01
  - Expected outcome: an induced git/OS error in the liveness check yields a skip, not a finding and not a traceback; the aggregator's per-rule exception isolation (check_engine.py:1056-1059) is not relied upon for this path.
  - Execution state: pending

### Task group 2: prove it, in both directions

- [ ] E-03 Add `tests/test_check_engine_receipt_liveness.py` covering, in a temp git repo: (a) a receipt whose plan is in `executed/` produces NO scope-drift finding even with an out-of-scope dirty path present; (b) a receipt whose plan is in `pending/` STILL produces the finding for the same dirty path, proving the rule was narrowed and not disabled; (c) a receipt whose `base_head` is not an ancestor of HEAD is skipped; (d) each terminal directory (`executed/`, `superseded/`, `not-executed/`) is rejected and `pending/`/`reusable/` are not; (e) a liveness-check error results in a skip (E-02). Each assertion must be shown to FAIL against the pre-fix predicate where applicable.
  - Depends on: E-01, E-02
  - Expected outcome: the module passes; case (a) FAILS against pre-fix code (that is the bug); case (b) FAILS if the receipt check is removed rather than narrowed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The gate is already built and is OPT-IN, not installed. `agent_workflows/hooks/precommit_scope_gate.py` delegates to the ONE shared aggregator `check_engine.check_commit_invariants` (check_engine.py:1029), which composes `check_status_untooled`, `check_release_gate_consistency`, and `check_scope_drift`. Verified `.pre-commit-config.yaml` contains no `precommit-scope-gate` entry. So this plan must NOT add a hook; the mechanical layer exists and merely cannot be trusted yet.
- The defect is a missing liveness test, not a missing feature. `check_scope_drift` (check_engine.py:960) skips only when there is no receipt at all or the base is empty/`unversioned` (check_engine.py:985-991). It never asks whether the plan is still in flight.
- Measured on this checkout: 8 receipts under `.aw/state/ipd-lifecycle/`, of which FOUR (`8zgybk`, `qmt3yk`, `v58bvy`, `v7e88a`) belong to plans already in `executed/`. `check_commit_invariants(".")` returns 74 findings; 24 come from those four terminal plans and 50 from in-flight ones. Every receipt's `base_head` is currently an ancestor of HEAD, so the terminal-plan case is the one with live evidence and the unreachable-base case is defensive.
- The leak has a known source, and it is NOT in scope here. `finalize` DOES consume the receipt, but only on the clean-complete path (`receipt_path_for(...).unlink()`, ipd_lifecycle.py:1647-1651). Under worktree isolation the runner COPIES the receipt into the lane (`sync_receipt_into_worktree`, oc_runipd.py:488-494, called at :2216), so an in-lane finalize consumes the LANE's copy and the main-tree original is left behind. `8zgybk` was finalized exactly that way (`f5f733f`), which explains its leaked receipt. Fixing the leak is a runner change in files owned by in-flight plans, so this plan hardens the CONSUMER instead, which is correct regardless: the gate must not trust a stale receipt even if leaks are later eliminated.
- Terminal-vs-active is already encoded in the DIRECTORY, per the repository's filesystem-encoded-state principle: `pending/` and `reusable/` are non-terminal; `executed/`, `superseded/`, and `not-executed/` are terminal. Deriving liveness from the path is therefore consistent with how the rest of the toolkit reads disposition, and avoids re-parsing status text that may legitimately lag.
- The hook's own docstring states the honest limit: "git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. This is OPT-IN best-effort FEEDBACK, not an authority boundary; the authoritative boundary is phase-5 CI running the same engine." That is the basis for E-02's fail-safe direction.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `check_engine.py:985-991` | `check_scope_drift` accepts any receipt with a non-empty base as an in-flight execution. No check that the plan is still active. | source |
| F2 | HIGH | this checkout | 4 of 8 receipts belong to plans in `executed/`; the aggregator reports 74 findings, 24 of them from those terminal plans. | measured via `check_commit_invariants(Path('.'))` and per-receipt directory resolution |
| F3 | HIGH | `hooks/precommit_scope_gate.py` + F2 | Because the hook delegates to that aggregator and fails closed on any finding, installing it today would refuse EVERY commit in this repo, including the four live runners'. The mechanical anti-clobbering protection is therefore unusable. | hook `check()` returns exit 1 whenever drift is non-empty |
| F4 | MED | `oc_runipd.py:488-494`, `:2216` vs `ipd_lifecycle.py:1647-1651` | The leak source: `finalize` unlinks the receipt it can see, but a lane-side finalize sees only the COPY synced into the worktree, so the main-tree receipt survives. `8zgybk` (`f5f733f`) is an instance. | source + the leaked receipt for a plan in `executed/` |
| F5 | MED | `check_engine.py:1041-1043` | The rule reuses `_paths_changed_by_this_execution`, the same helper backlog `077yqc` reports has NO ownership filter. So a stale receipt does not merely produce noise: it attributes ANOTHER agent's uncommitted work to a finished plan. Narrowing liveness reduces the blast radius; it does not fix attribution. | `077yqc`; helper at ipd_lifecycle.py:791-814 |

## Proposed changes (ordered, validatable)

1. Add the liveness predicate and apply it in `check_scope_drift` (E-01).
2. Make it fail safe, with the rationale cited in a comment (E-02).
3. Prove the rule was narrowed rather than disabled, in both directions (E-03).

## Deferred / out of scope (with reason)

- The CONTRACT wording fix (naming the shared-index race in the installed agent contract). Its files are `agent_workflows/engine.py` and `AGENTS.md`, which are the declared Scope-Paths of plan `uyd3lw`, CURRENTLY EXECUTING in a live runner. Editing them would collide with an in-flight plan, so this is deferred to its own plan once `uyd3lw` completes. This is the single most important scoping decision in this plan.
- Ownership-aware attribution (backlog `077yqc`, open, release-blocking). Distinct defect: `077yqc` is about WHOSE changes a rule may attribute; this plan is about WHETHER a receipt is still live. Both are needed before the hook is safe to enable; they are independent and separately verifiable.
- Fixing the receipt LEAK in the runner (F4). Its files (`oc_runipd.py`, `ipd_lifecycle.py`) are in the declared Scope-Paths of in-flight plans `y0gg8o`/`af7i6p`/`z2isfg`. Also, hardening the consumer is the more durable fix: the gate must tolerate a stale receipt regardless of how carefully leaks are prevented.
- INSTALLING the `precommit-scope-gate` hook. Explicitly not done here. With `077yqc` unfixed the gate would still misattribute concurrent work, so enabling it now would trade one clobbering failure for another. Installation belongs to a later plan that can demonstrate a clean run on a busy shared checkout.
- Any change to `check_status_untooled` or `check_release_gate_consistency`, the aggregator's other two rules. Neither is receipt-driven and neither contributed to the measured findings.

## Scope check

- Over-scope: none. `check_engine.py` carries F1/F2/F5; the test module is new and required by E-03. No other file is touched, which is deliberate given four concurrent runners.
- Under-scope: the contract fix, `077yqc`, the runner-side leak, and hook installation are each named under Deferred with the reason and, where relevant, the in-flight plan that owns the files.

## Required tests / validation

- The new `tests/test_check_engine_receipt_liveness.py` must pass, with case (a) shown to FAIL pre-fix and case (b) shown to fail under a naive removal of the receipt check. Both directions are mandatory: a change that merely stops reporting has deleted a safety property rather than corrected it.
- `tests/test_phase4_hooks.py` and `tests/test_event_derived_lifecycle.py` are the existing consumers of `check_scope_drift`/`check_commit_invariants` and must pass UNCHANGED.
- `python3 -m pytest -n auto` (the repo's configured invocation; `-n auto` is already in `addopts`) and `python3 -m pytest -m "" -n auto` for the full suite. RECORDED BASELINE at authoring: fast subset `2871 passed, 3 skipped, 4 xfailed`; full `4 failed, 3198 passed, 3 skipped, 4 xfailed`. KNOWN-UNRELATED failures that must NOT be claimed as caused or fixed: `test_command_surface_declarations`, `test_cli_conformance_matrix` (x2), `test_cli` subparser descriptions (undeclared CLI parser leaves from concurrent `run_cli` work), plus `tests/test_run_viewer.py::test_run_viewer_cli_issues_flag`, which reads the LIVE run tree via `discover_run_dirs(Path("."))` and is state-dependent while runners are active.
- A measured before/after on this checkout: `check_commit_invariants(Path("."))` count drops from 74 to 50, and the four terminal plans contribute zero findings. Because concurrent sessions change the tree, the executor must record both numbers from the SAME session and state the tree state, rather than comparing against this document's numbers.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec change. Spec `25kzda` section 5.2 treats scope discipline as a safety property and section 6.1 requires honest limits; this plan makes an existing local gate's precondition true rather than altering specified behavior.
- No user-facing docs describe `check_scope_drift`, so no doc updates. The rule's docstring must be updated to state that only a LIVE receipt is considered, so the next reader does not restore the old behavior.

## Open questions

### OQ-01: Should liveness be derived from the plan's directory or from its `Status:` field?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: DIRECTORY. The repository encodes disposition in the path by design (filesystem-encoded-state), the lifecycle setters move files as the authoritative act, and `aw runs -L` already reports directory-vs-status discrepancies as a real and observed condition, so status text can lag the move. Using the directory also avoids re-parsing and cannot disagree with where `finalize` actually put the file. The predicate should additionally tolerate a plan file that cannot be located at all by treating the receipt as not live, which E-02's fail-safe rule already covers.

### OQ-02: Should a stale receipt be reported as its own advisory rather than silently skipped?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Lean YES eventually, but NOT in this plan. A leaked receipt is a real anomaly worth surfacing (it is evidence of F4's interrupted-finalize path), and silently ignoring it hides the leak. But emitting a new finding class from a commit-scoped gate would make the hook noisy on a repo that already has four leaked receipts, defeating this plan's purpose. The clean home is a separate `aw doctor`-style check or an `aw check` advisory outside the commit gate. Recorded so the silence is a deliberate choice rather than an oversight.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's source and the `check_scope_drift` call site. Paste a before/after `check_commit_invariants(Path("."))` count from the SAME session with the tree state noted, showing the four terminal plans (`8zgybk`, `qmt3yk`, `v58bvy`, `v7e88a`) contributing zero findings afterward and the in-flight plans' findings unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the induced-error case showing a SKIP rather than a finding or a traceback, and paste the comment citing the hook docstring's best-effort-feedback limit as the basis for failing safe.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the new module passing with all five cases. Then paste FALSIFIABILITY in both directions: case (a) FAILS against the pre-fix predicate, and case (b) FAILS when the receipt check is removed instead of narrowed. Paste `tests/test_phase4_hooks.py` and `tests/test_event_derived_lifecycle.py` passing unchanged, plus the fast and full suite results against the recorded baseline with the known-unrelated failures named and not claimed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the two files in Scope-Paths, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`/bare/`-a`, and never push.

SHARED-CHECKOUT WARNING, unusually acute for this plan: FOUR runners are executing concurrently at authoring time, including plans that declare `agent_workflows/engine.py`, `AGENTS.md`, `oc_runipd.py`, `agy_runipd.py`, and `ipd_lifecycle.py`. This plan touches NONE of those, deliberately. Before every commit AND every retry, run `git diff --cached --name-only` and unstage anything not in this plan's Scope-Paths: the git index is SHARED mutable state, so a co-worker's `git add` can land between your check and your commit, which was observed this session. A verification result older than the commit attempt is worthless; re-verify immediately before each attempt.

Do not "fix" the leaked receipts on disk as a convenience. They are the evidence F2/F4 rest on, they belong to other plans' executions, and deleting them would both destroy the before/after measurement V-01 requires and modify state this plan does not own.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
