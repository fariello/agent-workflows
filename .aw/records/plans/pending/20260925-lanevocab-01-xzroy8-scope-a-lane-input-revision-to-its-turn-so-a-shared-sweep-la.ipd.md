# IPD: Scope a lane input revision to its turn so a shared sweep lane attaches the right plan

- Date: 2026-09-25
- Kind: child
- Concern: Spec `7ckptx` R5.1a (iii) treats a lane's manifest revisions as ONE owner's input history ("any legitimate change to the input set is a NEW MANIFEST REVISION"), and the code inherits that assumption: `lane_containment.localize_attachment` defaults to `revision=None`, which `read_lane_input_manifest` resolves to `latest_lane_input_revision` (the highest `rev-<N>` directory on disk). The review sweep lane breaks the assumption: `runner_shared.execute_item_core` materializes each review at `revision=int(item["position"])`, but the queue dispatches by `queue_sort_key` (dependency depth first), not by position, so a review dispatched after a higher-positioned one gets the OTHER plan attached. `oc_runipd.run_opencode` calls `localize_attachment` for the plan with no `revision`. The backlog item called this wording-only; it is not: it is shipped misbehavior, measured in recorded runs.
- Scope: IN: (a) `oc_runipd.run_opencode` passes the current attempt's `lane_input_revision` to both `localize_attachment` calls; (b) the `localize_attachment` docstring states that `revision=None` means "latest" and is only correct for a single-owner lane; (c) spec `7ckptx` R5.1a (iii) and acceptance A12b state that a revision is scoped to the (lane, turn) pair, that a shared lane holds one revision per turn, and that a consumer MUST address a turn's own revision rather than the latest; (d) a regression test. OUT: renaming or re-keying `rev-<N>` directories; the agy host (it has no `--file` surface and names the lane plan path in the prompt, which `resolve_plan_path(lane_root, ...)` already resolves per turn); the execute lane (single owner, always rev-1).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/lane_containment.py, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, tests/test_lane_input_revision_scope.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: i4y84y
- Blocks-Release: next
- Set: lanevocab
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xzroy8

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog i4y84y; re-measured the sweep lane's revision use across all 22 recorded runs with sweep reviews and found 4 review attempts whose `--file` attachment named a different plan's `rev-<N>` copy.

## Goal

Every isolated turn attaches the plan copy from ITS OWN manifest revision, and the containment spec says a revision belongs to a (lane, turn) pair, so the sweep lane's one-revision-per-review layout is both correct and described.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect

- [ ] E-01 Re-measure the misattachment from recorded runs. For every `.aw/records/runs/*/state.json`, for each queue item attempt with `review_sweep_lane: true`, compare `lane_input_revision` against the `rev-<N>` segment of the path following each `--file` in the attempt's `argv`. Print every mismatch as `run id6 rev=<own> attached=<rev-dir>/<plan-prefix>`.
  - Depends on: none
  - Expected outcome: at least the 4 mismatches measured at authoring (run `run-20260917T231229Z-2701568`: `nmlx47` rev 5, `xdvglg` rev 6, `ut0vzr` rev 10, each attached `rev-12/...-zx9dkq-...`; run `run-20260919T133719Z-1618106`: `udgilu` rev 2 attached `rev-3/...-13xo5k-...`). If there are none, stop and report: the defect has moved.
  - Execution state: pending

- [ ] E-02 Add `tests/test_lane_input_revision_scope.py`. Build a temp lane, call `lane_containment.materialize_lane_inputs` for plan B at `revision=5` then plan A at `revision=3` (the out-of-position dispatch order). Drive the REAL `oc_runipd.run_opencode` with `work_dir=<lane>`, `item={"position": 3, "id6": "revaaa", "setid": "s1", "action": "review", "attempts": [{"lane_input_revision": 3}]}`, capturing argv through a patched `driver.subprocess.Popen` exactly as `LaunchProfileFrozenTurnArgvTests._argv_for` in `tests/test_oc_runipd.py` does. Assert the path after the plan `--file` is under `rev-3/` and its bytes are plan A's. Add a second case: an execute item whose attempt has `lane_input_revision: 1` and a lane holding only rev-1 still attaches rev-1 (no behavior change for single-owner lanes).
  - Depends on: E-01
  - Expected outcome: the review case FAILS at HEAD (attachment under `rev-5/`, plan B); the execute case passes.
  - Execution state: pending

### Task group 2: fix the consumer and the contract

- [ ] E-03 In `oc_runipd.run_opencode`, read `turn_revision = ((item.get("attempts") or [{}])[-1]).get("lane_input_revision")` next to `lane_root_for_attachments`, and pass `revision=turn_revision` to both `lane_containment.localize_attachment(` calls (runbook and plan). Extend the comment block above `lane_root_for_attachments` with one paragraph naming this plan and the measured mismatch. `None` (a non-isolated turn, or an attempt without materialization) keeps today's latest-revision behavior.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_lane_input_revision_scope.py` passes.
  - Execution state: pending

- [ ] E-04 In `lane_containment.localize_attachment`'s docstring, add a paragraph: `revision=None` reads the LATEST revision, which is the turn's own only in a single-owner lane; a shared lane (the review sweep) holds one revision per turn, so its caller MUST pass the turn's recorded `lane_input_revision`. Add the same one-line caveat to `read_lane_input_manifest`'s docstring. No code change in this module.
  - Depends on: E-03
  - Expected outcome: `git diff -- agent_workflows/lane_containment.py` shows docstring-only changes.
  - Execution state: pending

- [ ] E-05 Amend spec `7ckptx`: in R5.1a append to part (iii) "A revision is scoped to the (lane, turn) pair. A lane shared by several turns (the review sweep lane) therefore holds one revision per turn, numbered by the turn's queue position, and consecutive revision numbers need not belong to the same turn. Any consumer that reads a manifest on a turn's behalf MUST address that turn's own recorded revision, never the latest on disk." In A12b append "and, for a shared lane, that each turn's attachment resolves to its own revision when turns are dispatched out of position order."
  - Depends on: E-04
  - Expected outcome: `grep -n "(lane, turn) pair" <spec>` returns the R5.1a line; A12b names the shared-lane case.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 Run the directly affected modules: `python3 -m pytest tests/test_lane_input_revision_scope.py tests/test_oc_runipd.py tests/test_defect_report.py`.
  - Depends on: E-05
  - Expected outcome: 0 failed.
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `lane_containment.materialize_lane_inputs` takes `revision: int = 1` and writes `<lane>/.aw/state/lane-inputs/rev-<N>/`; `latest_lane_input_revision` derives "latest" from directory names only.
- The sweep path in `runner_shared.execute_item_core` (`if work_dir and is_review:`) calls `materialize_lane_inputs(..., revision=int(item["position"]))` and records `attempt["lane_input_revision"]`; the attempt dict is appended to `item["attempts"]` before materialization mutates it, so `item["attempts"][-1]` is the live attempt when `run_opencode` runs.
- Dispatch order is `queue_sort_key` (dependency depth, then position), so position order is NOT dispatch order whenever a lower-positioned review declares an in-queue dependency.
- `lane_containment.lane_input_paths` already iterates `range(1, latest + 1)` and skips missing revisions, so teardown accounting is correct for sparse, out-of-order revisions and needs no change.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.run_opencode` plan `--file` | A sweep review attaches the latest revision's plan, which is another review's plan when dispatch is out of position order. The reviewing agent receives the wrong plan as its attachment. | Recorded argv: `udgilu rev 2 attached: ['rev-3/plan-20260919-stopcrash-01-13xo5k-record']`; three more in run `run-20260917T231229Z-2701568`, all attaching `rev-12/...zx9dkq...` |
| F-2 | MED | spec `7ckptx` R5.1a (iii) | The spec describes revisions as one owner's input history and says nothing about which revision a consumer reads; the shipped sweep lane violates the unstated assumption. | R5.1a text; `revision=int(item["position"])` in `execute_item_core` |
| F-3 | INFO | backlog `i4y84y` | Its claim "nothing behaves incorrectly" was true of the manifest bookkeeping and false of the attachment consumer. The item stays `Work-Kind: chore` as filed; see OQ-01. | F-1 |
| F-4 | INFO | agy host | Not affected: no `--file` surface; the prompt names `resolve_plan_path(lane_root, ...)`, the lane's tracked copy, resolved per turn. | `oc_runipd` comment "the agy twin has no `--file` surface at all" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the mismatch from run records.
2. E-02 adds a failing regression test.
3. E-03 passes the turn's revision at the one consumer.
4. E-04 documents the `None` default's single-owner limit.
5. E-05 amends R5.1a and A12b.
6. E-06 and E-07 run the affected modules and the bare suite.

## Deferred / out of scope (with reason)

- Replacing the position-keyed revision integer with an explicit per-turn key (the backlog's second suggested shape). The (lane, turn) scoping plus a consumer that addresses its own revision removes the ambiguity without a layout change that every teardown and accounting path would have to follow.
  - Carrier-Declined: the wording plus consumer fix closes the defect; a re-key is churn with no measured need.

## Scope check

- Over-scope: none.
- Under-scope: none; the only product caller of `localize_attachment` is `oc_runipd.run_opencode` (grep of `localize_attachment` across `agent_workflows`).

## Required tests / validation

New `tests/test_lane_input_revision_scope.py` (failing before E-03), the affected modules, then the bare suite.

## Spec / documentation sync

AMENDS spec `7ckptx` (listed in Scope-Paths): R5.1a (iii) and A12b. Why: the spec is the contract the sweep lane is reviewed against, and it currently does not say which revision a turn owns, which is exactly the gap F-1 fell through. No user-facing docs describe lane revisions.

## Open questions

### OQ-01: Should backlog `i4y84y` be reclassified from `chore` to `bug`?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: F-1 is user-visible misbehavior (a review agent is handed another plan), which the repository's policy would classify as `bug`, and a live `bug` must carry `- Blocks-Release:`. This plan keeps the filed `chore`/`low` because the graduating author may not change the item's classification. Default: proceed as filed; the maintainer may reclassify and add `- Blocks-Release: next` to both the item and this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of the E-01 probe listing each mismatch line, including `udgilu rev=2 attached=rev-3/...13xo5k...`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_lane_input_revision_scope.py` run BEFORE E-03, pasted, showing the review case FAILING with the attached path under `rev-5/` and the execute case passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the same command after E-03, pasted, showing all passed; `git diff -- agent_workflows/oc_runipd.py` showing `revision=turn_revision` on both `localize_attachment(` calls.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff --stat -- agent_workflows/lane_containment.py` plus the diff hunk showing only docstring lines changed, naming "single-owner" and `lane_input_revision`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `grep -n "(lane, turn) pair\|out of position order" .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` returning the R5.1a and A12b lines.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted summary line of `python3 -m pytest tests/test_lane_input_revision_scope.py tests/test_oc_runipd.py tests/test_defect_report.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted final summary line of the bare `python3 -m pytest`, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution. It declares a spec edit (spec `7ckptx`), which the runners announce before the run. The executor commits only the Scope-Paths via `aw commit xzroy8 -- <paths>`, never `git add -A`, never pushes, pastes actual runner output for every V item, and moves the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms.
