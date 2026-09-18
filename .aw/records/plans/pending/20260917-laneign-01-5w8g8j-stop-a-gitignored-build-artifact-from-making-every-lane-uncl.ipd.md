# IPD: Stop gitignored files from blocking lane teardown

- Date: 2026-09-17
- Kind: child
- Concern: A lane that finished cleanly is preserved forever because it contains gitignored files such as bytecode caches (`__pycache__/*.pyc`), toolchain dependencies (`.opencode/node_modules/`), and test caches (`.pytest_cache/`). Under the former spec `7ckptx` R5.5, any unknown ignored file made `LaneInventory.classified` false, refusing teardown. Measured in this checkout: 38 undisposed lane worktrees accumulated because 100 percent of clean test runs failed teardown due to routine gitignored files.
- Scope: Update `LaneInventory` in `agent_workflows/lane_containment.py` so gitignored files do not block classification, implementing amended spec `7ckptx` R5.5 (committed at `e94a7c4e`). Teardown continues to refuse on uncommitted tracked modifications (dirty tracked files), uncommitted untracked source files (unknown untracked files), and uncollected submissions under `.aw/state/lane-submissions/`. Update `tests/test_lane_retention.py` to match the amended contract.
- Scope-Paths: agent_workflows/lane_containment.py, tests/test_lane_retention.py, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: laneign
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 5w8g8j

## Workflow history

- 2026-09-18 reviewed (aw set): plan-review round 2 complete: APPROVE WITH REVISIONS APPLIED. Spec 7ckptx R5.5 amended in commit e94a7c4e per maintainer ruling: gitignored files are disposable upon lane destruction and do not block teardown. PR-001 and PR-002 marked FIXED. OQ-02 and OQ-03 resolved. Plan simplified to 3 E/V items. Readiness go-pending-approval.
- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 11 findings, 9 FIXED, PR-001 (fix covers 12 percent of the real population) and PR-002 (narrows an approved spec MUST) left OPEN at BLOCKER and escalated as blocking OQ-02/OQ-03; readiness no-go
- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-011; readiness `no-go` on TWO blocking findings. Reviewed at HEAD `5a7d81d1`; `aw ipd lint --phase author` conforming before revision.
- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored after the maintainer asked what the "4,176-file lane-retention noise" from their overnight run actually was.

## Goal

Allow clean lanes to be torn down without accumulating stranded worktrees. Gitignored files (such as Python bytecode caches `__pycache__/*.pyc`, tool dependencies `.opencode/node_modules/`, and test runner caches `.pytest_cache/`) are disposable when an isolated worktree is destroyed, aligning lane containment with standard Git semantics and the amended spec `7ckptx` R5.5.

Teardown continues to refuse whenever a lane holds uncommitted work:
1. Dirty tracked files (uncommitted edits to tracked files).
2. Unknown untracked files (new uncommitted files not in `.gitignore`).
3. Uncollected task submissions under `.aw/state/lane-submissions/`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: implement the amended R5.5 retention rule

- [ ] E-01 UPDATE `LaneInventory` IN `agent_workflows/lane_containment.py` so gitignored files do not prevent classification. `LaneInventory.classified` returns True when `readable and not dirty_tracked and not unknown_untracked and not uncollected_submission`. `unknown_ignored` remains tracked in the inventory record for diagnostics and telemetry (`as_dict()`), but does not block teardown.
  - Depends on: none
  - Expected outcome: `LaneInventory.classified` returns True for an inventory whose only unexpected files are gitignored (`unknown_ignored`), and returns False when dirty tracked files, unknown untracked files, or uncollected submissions are present.
  - Execution state: pending

- [ ] E-02 UPDATE `tests/test_lane_retention.py` to verify the amended R5.5 and A15 behavior. Update tests so that an unknown untracked file still refuses teardown, a dirty tracked file still refuses teardown, and an uncollected submission still refuses teardown, while a lane holding only gitignored files is classified as clean and torn down.
  - Depends on: E-01
  - Expected outcome: all lane retention tests pass against the amended contract with both drivers tested.
  - Execution state: pending

- [ ] E-03 VALIDATE THAT CLEAN LANES ARE CLASSIFIABLE AND TEARDOWN SUCCEEDS. Run `inventory_lane` against a real lane holding bytecode and `.opencode/node_modules/` and verify that `classified` is True. Run the test suite and verify no new failures.
  - Depends on: E-02
  - Expected outcome: real lane inventory reports `classified=True`; bare test suite passes with no new failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- FAIL TOWARD PRESERVATION IS THE SPEC'S RULE for uncommitted work. `LaneInventory` preserves whenever dirty tracked files, unknown untracked files, or uncollected submissions remain.
- GITIGNORED FILES ARE DISPOSABLE. Under amended spec `7ckptx` R5.5, files matching `.gitignore` are disposable upon lane destruction and do not block teardown.
- THE MESSAGE CAP IS DELIBERATE. `RETENTION_REASON_PATH_LIMIT = 10` caps the reason sentence length while the full list survives in `as_dict()`.
- TWO DRIVERS SHARE THE SAME INVENTORY. `oc_runipd` and `agy_runipd` share the same `lane_containment` functions; tests must parameterize over both.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `LaneInventory.classified` (`lane_containment.py:2889`) | One gitignored bytecode or tool file previously prevented teardown forever because `unknown` included `unknown_ignored`. | `LaneInventory.classified` definition; 38 accumulated worktrees. |
| F2 | HIGH | `.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` | Spec `7ckptx` R5.5 and A15 amended by maintainer ruling on 2026-09-18 (commit `e94a7c4e`) to remove the teardown refusal on gitignored files. | Spec commit `e94a7c4e`. |
| F3 | MEDIUM | `tests/test_lane_retention.py` | Existing tests assert `unknown_ignored` blocks `classified`; these must be updated to match amended criterion A15. | `tests/test_lane_retention.py:198-210`. |

## Proposed changes (ordered, validatable)

1. Update `LaneInventory` in `lane_containment.py` so gitignored files do not block classification (E-01).
2. Update `tests/test_lane_retention.py` to assert the amended R5.5 and A15 behavior (E-02).
3. Validate real-lane classification and test suite status (E-03).

## Deferred / out of scope (with reason)

- TEARING DOWN EXISTING STRANDED WORKTREES. Defer to a separate maintenance step after the fix lands.
- THE DIRTY-TRACKED AND UNKNOWN-UNTRACKED RULES. Untouched. An untracked source file or uncommitted tracked change remains strictly protected.
- THE PRESERVE-ON-UNREADABLE RULE. Untouched. An inventory failure continues to refuse teardown.

## Scope check

- Over-scope: none. Changes confined to `lane_containment.py`, `tests/test_lane_retention.py`, and the already-committed spec `7ckptx`.
- Under-scope: none. The change directly eliminates the 100% teardown refusal rate for clean runs.

## Required tests / validation

1. `python3 -m pytest` showing no new failures against baseline.
2. A lane holding only gitignored files: shown classifiable and torn down after the change.
3. An injected regression: a lane holding an unknown untracked file or dirty tracked file: shown still preserved with the path named.
4. An uncollected submission: shown still preserved.
5. Real lane check: `inventory_lane` on a real lane returns `classified=True`.
6. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

SPEC `7ckptx` GOVERNS THIS BEHAVIOR (R5.5 retention, R5.6 reason codes, A15 acceptance criterion). Spec amended in place and committed at `e94a7c4e` on 2026-09-18 per maintainer ruling.

R5.5 now reads:
"Teardown MUST be refused while a lane holds content the driver cannot classify: a dirty tracked file, an unknown untracked file, or an unimported submission. Gitignored files (including interpreter bytecode caches, toolchain dependencies, and build or test residues) are disposable upon lane destruction and do not block teardown."

A15 now reads:
"A lane holding an unknown untracked file, a dirty tracked file, or an uncollected submission is not torn down and an event records the reason; gitignored files do not block teardown; a fully classified clean lane is torn down. (R5.5, R5.6)"

## Open questions

### OQ-01: Should the discardable-ignored allowlist be shape-based, or should a lane declare its own expected artifacts?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer ruling: neither an allowlist nor artifact declarations are needed. Gitignored files are disposable by default at lane destruction per amended spec `7ckptx` R5.5.

### OQ-02: Is an agent tool's installed dependency tree (`.opencode/node_modules/**`) discardable?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer ruling: All gitignored files, including toolchain dependencies like `.opencode/node_modules/**` and interpreter bytecode, are disposable upon lane destruction.

### OQ-03: R5.5 must be amended. Approve the narrowing of an approved spec's MUST?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED 2026-09-18 by maintainer decision: Spec `7ckptx` R5.5 and A15 amended in place and committed at `e94a7c4e`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted code of `LaneInventory.classified` and `LaneInventory.unknown` showing that `unknown_ignored` does not block classification. Proof that an inventory holding only gitignored files yields `classified=True`, while dirty tracked, unknown untracked, or uncollected submissions yield `classified=False`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted test results from `tests/test_lane_retention.py` showing all tests passing against the amended contract, including both drivers.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of `inventory_lane` on a real lane worktree holding bytecode and `.opencode/node_modules/` showing `classified=True`. Pasted `python3 -m pytest` summary showing no new failures against baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: single focused change to align lane retention with amended spec `7ckptx` R5.5.

EXECUTION CONTRACT. All open questions are resolved. SCOPE FENCE: `agent_workflows/lane_containment.py`, `tests/test_lane_retention.py`, `.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`. Commit path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run `git diff --cached --name-only` and unstage anything not yours. After the gate, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
