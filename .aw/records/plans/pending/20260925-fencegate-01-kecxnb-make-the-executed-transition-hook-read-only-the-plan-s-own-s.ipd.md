# IPD: Make the executed-transition hook read only the plan's own Status line

- Date: 2026-09-25
- Kind: child
- Concern: The pre-commit hook `agent_workflows/hooks/executed_transition_gate.py` decides a plan gained `executed` by `_has_executed_status`, which matches ANY line equal to `- Status: executed`, including one quoted inside a code fence. The refusal is REAL but narrower than "a plan that quotes the line": the hook reads ONLY `.aw/records/plans/**/*.ipd.md` (`_is_plan_path`), and detection is a HEAD-versus-staged DELTA, so the trigger is specifically a commit that ADDS such a quote to a PLAN whose own status is not executed. Measured end to end: that commit is refused with `gained '- Status: executed'` and told to run `aw ipd finalize`, which is nonsense for a plan that is not transitioning. A lifecycle doc or a review record quoting the line cannot trip it at all (they are not plan paths), and an ordinary edit to a plan that already contained the quote cannot either (no delta).
- Scope: IN: `_has_executed_status` reads only the metadata region's FIRST `- Status:`; tests. OUT: the rest of the hook's logic; the sibling `check_engine._status_meta` residual case found at review (carried).
- Scope-Paths: agent_workflows/hooks/executed_transition_gate.py, tests/test_executed_transition_gate.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: fencegate
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: kecxnb
- From-Backlog: 4vhe5o
- Blocks-Release: next

## Workflow history
- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; 6 findings PR-901..PR-906 all FIXED, 4 decisions D-1..D-4 recorded; review record written; reproduced the false refusal end to end and narrowed the trigger (F-3), found the first-bullet requirement (F-4), proved the fix regresses nothing by running the hook's deleted suite against it (6 passed), and filed items ove09p and pyk78c; aw ipd lint --phase review-finalize conforming
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4vhe5o. Reproduced at HEAD: `_has_executed_status` on a plan whose own Status is `approved` but which quotes `- Status: executed` in a fence returns True.

## Goal

The hook refuses a real raw `executed` transition and never refuses a plan for quoting one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: fix and test

- [ ] E-01 Change `_has_executed_status` to read the status from the record's metadata region via `selectors.metadata_region(text)` (the toolkit's ONE metadata boundary), matching the FIRST `- Status:` bullet there, case-insensitively, against `executed` or its `done` alias.
  - TAKE THE FIRST BULLET, NOT ANY MATCH IN THE REGION, and this is load-bearing rather than stylistic. `metadata_region` returns "everything before the first `##` heading", and for a record with NO `##` heading at all it returns the WHOLE input by design (its docstring records that this is correct for 25 of 1614 tracked records). So an any-match-in-region implementation still returns True for a headingless plan that quotes the line: measured at review, `('(e) headingless approved + fenced')` is False under first-match and True under any-match. No such plan exists in the tree today (measured: 0 of 776 plans lack a `##` heading), so this is a latent case, not a live one; implement it correctly anyway because the hook also reads STAGED blobs of arbitrary content.
  - Verified at review that the change is BEHAVIOR-COMPATIBLE with the hook's deleted test suite: monkeypatching this exact implementation in and running the six recovered tests from `19313eed^` gave `6 passed`, so no existing gate behavior regresses.
  - Depends on: none
  - Expected outcome: a fenced or body-level `- Status: executed` no longer counts; the metadata one still does.
  - Execution state: pending

- [ ] E-02 Add `tests/test_executed_transition_gate.py` with those two cases plus (c) a `done` alias in metadata -> True and (d) an OQ block's own `- Status: open` below the metadata with metadata `executed` -> True. All four verified at review against the proposed implementation: (a) False, (b) True, (c) True, (d) True.
  - THE FILE NAME IS NOT FREE: a 1267-line `tests/test_executed_transition_gate.py` was DELETED by the suite trim `19313eed`, and this item recreates that exact path with four unit cases. Recovered and run at review: its six tests still PASS against today's hook (`6 passed in 3.65s`). So creating the file is correct, but state plainly in its module docstring that it is a NEW narrow file and not the restored suite, so a later reader does not mistake four cases for the coverage that was lost. ADD at least one END-TO-END case beside the four unit cases, because the four exercise `_has_executed_status` in isolation while the defect a human experiences is a refused commit: stage a commit that ADDS the fenced quote to a non-executed plan in a temp repo and assert `check()` returns `(0, [])`. Measured at review, that same commit today returns exit 1 with the `gained '- Status: executed'` refusal.
  - Depends on: E-01
  - Expected outcome: five cases pass; (a) and the end-to-end case fail against the pre-change function.
  - Execution state: pending

- [ ] E-03 Run the bare suite.
  - Depends on: E-02
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.metadata_region` is documented as the ONE boundary every identity/status reader is bounded to; reusing it keeps this hook consistent with every other status reader. Its own docstring states the purpose exactly: "a document that merely QUOTES a metadata block ... cannot be read as ASSERTING the quoted values."
- `metadata_region` returns the WHOLE input when a record presents no `##` heading (deliberate, documented, and correct for 25 of 1614 tracked records), so a caller must still take the FIRST `- Status:` bullet rather than scanning the region for any match.
- The hook is a LOCAL best-effort prevention, not the authority: its own refusal text says `--no-verify` bypasses it and names `aw check`/`aw doctor` as the backstop. That bounds the severity of the false refusal (an operator is not permanently stuck) and is why this is MED rather than HIGH.

## Findings

All measured at HEAD `3243791b` unless stated (the plan cited `0c2e7970`, an ancestor; both were checked and the measurements agree). F-3 through F-5 were added at review.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `executed_transition_gate._has_executed_status` | Matches any matching line anywhere in the file. | driven: metadata `approved` plus a fenced `- Status: executed` -> `True` |
| F-2 | INFO | sibling detector | The untooled-status detector (`check_engine._status_meta`) already takes the first match, so it does not share this defect for a plan with front-matter Status. | read `_STATUS_META_RE` use |
| F-3 | MED | the Concern as authored | THE TRIGGER IS NARROWER THAN THE CONCERN CLAIMS, AND THE NARROWING MATTERS BECAUSE IT DECIDES THE TEST. The hook reads only plan paths (`_is_plan_path`: `.aw/records/plans/**` + `.ipd.md`), so a lifecycle DOC or a REVIEW record quoting the line cannot trip it; and detection is a HEAD-versus-staged delta, so an ordinary edit to a plan that ALREADY contained the quote cannot either. The live trigger is exactly a commit that ADDS the quote to a plan whose own status is not executed. | `_is_plan_path` on the lifecycle doc and a `.review.md` -> `False`; staging an ordinary edit to a plan already containing the quote -> `check()` returns `(0, [])`; staging the commit that ADDS the quote -> exit 1, `gained '- Status: executed'` |
| F-4 | MED | E-01 as authored (implementation detail) | AN ANY-MATCH-IN-REGION IMPLEMENTATION IS STILL WRONG for a record with no `##` heading, because `metadata_region` then returns the whole input by design. Taking the FIRST bullet is what makes the fix complete. Latent rather than live: 0 of 776 tracked plans lack a `##` heading. | driven: headingless plan, metadata `approved` + fenced `executed` -> first-match `False`, any-match `True`; `metadata_region` docstring on header exhaustion |
| F-5 | LOW | `tests/test_executed_transition_gate.py` (the path E-02 creates) | THE PATH E-02 CREATES WAS A 1267-LINE SUITE DELETED BY `19313eed`, and its six tests STILL PASS against today's hook. This plan legitimately adds four narrow unit cases there rather than restoring that suite, but the file must say so, or four cases read as the coverage of a hook whose end-to-end, merge-stage and hook-registration tests are gone. | `git show 19313eed^:tests/test_executed_transition_gate.py` -> 1267 lines, 6 tests; recovered and run at review -> `6 passed in 3.65s`; the same six re-run with the PROPOSED fix monkeypatched in -> `6 passed`, so the fix regresses nothing |

## Proposed changes (ordered, validatable)

1. E-01: bound the status read to the metadata region's first `- Status:` bullet.
2. E-02: behavior tests, including one end-to-end refusal case.
3. E-03: bare suite.

## Deferred / out of scope (with reason)

- RESTORING the 1267-line `tests/test_executed_transition_gate.py` deleted by `19313eed` (F-5), whose six tests cover the hook's end-to-end refusal, merge-stage behavior and pre-commit registration and still pass today. This plan adds four unit cases plus one end-to-end case at that path; the broader suite is a separate restoration decision.
  - Carrier: ove09p
- The sibling `check_engine._status_meta` residual case: it reads the first `- Status:` anywhere in the file rather than within the metadata region, so a plan with NO front-matter Status that quotes an executed line still reads as `executed` there. F-2 correctly scoped its own claim to a plan WITH front-matter Status; this is the remaining half. Out of scope (a different module and a different consumer, `check.status-untooled`), and note the fix in E-01 makes the HOOK strictly stricter than its sibling.
  - Carrier: pyk78c

## Scope check

- Over-scope: none. E-02 gained one end-to-end case, which is not new scope: it validates the same one-function change at the level a human actually experiences it (a refused commit).
- Under-scope: none for the declared concern. Two adjacent gaps found at review (the deleted suite, the sibling detector's residual case) are carried rather than absorbed, since each is a separate module or a separate decision.

## Required tests / validation

- `python3 -m pytest tests/test_executed_transition_gate.py -o addopts="" -q` plus the V-02 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: the ipd-lifecycle spec already says a plan's status is its metadata `- Status:`; this makes the hook read that line and nothing else.

## Open questions

### OQ-01: Use `ipd_lint._structural_lines` (fence-aware) or `selectors.metadata_region`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `selectors.metadata_region`, resolved from the code: it is documented as the single boundary for identity/status readers, and a status is a metadata field, so a fence-aware whole-file scan would still wrongly count a body-level status line. Re-verified at review, which also surfaced the one caveat the answer needs: `metadata_region` returns the WHOLE input for a record with no `##` heading, so the caller must take the FIRST `- Status:` bullet (F-4). With that, `metadata_region` also handles a case `ipd_lint._structural_lines` would not (a plan with no front-matter Status that quotes the line), and is what makes the fixed hook stricter than its `check_engine._status_meta` sibling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c` driving `_has_executed_status` on (a) metadata `approved` + fenced `executed` -> False and (b) metadata `executed` -> True.
  - ALSO REQUIRED: paste the HEADINGLESS case (a plan text with no `##` at all, metadata `approved`, quoting `- Status: executed`) returning False, which is what proves the implementation took the FIRST bullet rather than scanning the region (F-4). An any-match implementation passes (a) and (b) and FAILS this one.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test run passing; revert E-01 IN THE WORKTREE and paste case (a) FAILING; restore. Name the observed failure mode in the reverted run, which must be the fenced-quote assertion rather than an import or fixture error.
  - ALSO REQUIRED: paste the END-TO-END case's output, showing `check()` returning `(0, [])` for a staged commit that ADDS the fenced quote to a non-executed plan, and paste the same scenario against the reverted code showing exit 1 with `gained '- Status: executed'` (measured at review, that is exactly what it returns today). Confirm the new test file's docstring says it is a NEW narrow file, not the restored `19313eed` suite (F-5).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. A change to ONE function in a pre-commit GATE, making it stop refusing a commit it should allow. The direction is important: this makes the hook STRICTLY MORE PERMISSIVE in exactly one situation (a plan that merely quotes the executed line), and it does NOT loosen the real gate, because a genuine metadata `- Status: executed` still returns True (verified on cases (b), (c) and (d)). Review confirmed the change regresses nothing by running the hook's own deleted test suite against it (`6 passed`). Two things approval does NOT cover, each carried as its own item: the 1267-line test suite for this hook that `19313eed` deleted (`ove09p`), and the sibling `check_engine._status_meta` reading statuses outside the metadata region (`pyk78c`).

SEVERITY IS HONESTLY MED, NOT HIGH, and the reason belongs in front of the approver: this hook is a LOCAL best-effort prevention whose own refusal text says `--no-verify` bypasses it and names `aw check`/`aw doctor` as the backstop. So the false refusal wastes an operator's time and pushes them toward `--no-verify` (the real harm, since that habit disables the gate for genuine transitions too); it does not permanently block anyone.

Scope fence (a DECLARATION for reconciliation, not a stop directive): within `agent_workflows/hooks/executed_transition_gate.py` only `_has_executed_status`; no change to `_staged_plan_executed_transitions`, `_finalize_evidence_ok`, `_is_plan_path`, the merge-aware paths, or `main`. `tests/test_executed_transition_gate.py` is NEW at a path a deleted suite occupied. The module constants `_STATUS_EXECUTED_LINE` / `_STATUS_DONE_LINE` become unused if the new implementation does not consult them; either keep them in use or remove them, and say which at finalize rather than leaving a dead constant. `agent_workflows/check_engine.py` and `agent_workflows/selectors.py` are expected to need NO edit (the fix CONSUMES `selectors.metadata_region` unchanged). An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do not add `-n0`, a second `-q`, or `-p no:randomly`. Two claims here are specifically easy to fake and must not be: V-01's HEADINGLESS case, which is the only one distinguishing a correct first-bullet implementation from a plausible any-match one, and V-02's end-to-end pair, since four passing unit assertions prove nothing about whether the COMMIT is still refused.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if any case among (b), (c) or (d) returns False after the change, stop and report, because loosening the real gate is strictly worse than the false refusal this plan fixes; if importing `selectors` into the hook introduces a circular import or measurably slows the pre-commit path, stop and report rather than inlining a second copy of the metadata-boundary rule, since a duplicated boundary is the drift `selectors.metadata_region` exists to prevent.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition to `executed/` is performed with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane, and the executor otherwise performs it. Then set backlog item `4vhe5o` `done` with `--evidence` citing the executed plan. It carries `- Blocks-Release: next`, which this plan inherits, so the gate is preserved by that handoff and no separate de-gating is required; items `ove09p` and `pyk78c` stay open and carry their own state.
