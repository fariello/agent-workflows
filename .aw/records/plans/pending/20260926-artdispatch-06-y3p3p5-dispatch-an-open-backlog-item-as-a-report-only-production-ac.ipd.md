# IPD: Dispatch an open backlog item as a report-only production action verified by the BACKLOG codes

- Date: 2026-09-26
- Kind: child
- Concern: THE BACKLOG HALF OF PRODUCTION IS UNBUILT (spec `z7nbn1` section 3, OQ-05, acceptance 5.5c). `run_selection_policy._BACKLOG_ACTIONS` maps `open -> plan`, and after plans `8l8dgb` and `aeq7f8` a queue can carry a backlog item and the runner can run a production turn, but no dispatcher exists for `backlog`/`plan`, and the five verification codes of approved spec `25kzda` 4.9 (`BACKLOG-GRADUATE-COUNT`, `BACKLOG-GRADUATE-IPD`, `BACKLOG-GATE-HANDOFF`, `BACKLOG-GRADUATE-LEGITIMACY`, `BACKLOG-CROSS-TREE`) re-measured at HEAD `310ea53e` grep to ZERO under `agent_workflows/`. `25kzda` 3.4's `open` row defines the action: author the artifacts the item needs (one or more conformant IPDs, each carrying `From-Backlog` and inheriting `Blocks-Release`), set the item `graduated` using the handoff receipt, verify, and report the IPDs as next actions; setting it `graduated` before a conformant handoff exists, or setting it `done`, is forbidden. The shared gate predicate `check_engine.evaluate_blocking_close` already treats `graduated` as legitimate for a release-gated item ("graduated preserves gate ... `done` still requires handoff, evidence, or explicit de-gating"), and `check_engine.check_release_gates` already implements the cross-tree findings (`check.from-backlog-gate-mismatch`, `check.from-backlog-dangling`, `check.orphaned-live-blocker`) `BACKLOG-CROSS-TREE` must consult.
- Scope: IN: (a) the backlog production dispatcher, reusing plan `aeq7f8`'s production turn, commit, report-only `generated_next_actions` and quarantine machinery, with a backlog-specific prompt (house "Acting on a backlog item" rules: review-ready `to-review` plans, `aw ipd scaffold --from-backlog <id6>` which inherits Priority/Work-Kind/Blocks-Release, `aw ipd lint` conforming; "do NOT change the item's `- Status:`; the runner sets `graduated`"); (b) the five `BACKLOG-*` verifiers in `agent_workflows/production_checks.py` beside the `SPEC-PLAN-*` ones, implementing `25kzda` 4.9's pass criteria, message templates and Action columns; (c) on success, the runner sets the item `open -> graduated` through the GATED setter spelling `aw backlog set <path> --status graduated --message ...` (the spelling that runs `evaluate_blocking_close`; `runner_shared.close_backlog_item`'s docstring records why the positional spelling is unsafe) AFTER the handoff commit, citing the produced plans (`--graduated-to` when the produced plans share a Set), then re-runs `BACKLOG-CROSS-TREE`; on any failure, the item is left `open`; the item is never set `done`; (d) spec 5.5c's refusal matrix tested. OUT: authoring a SPEC from a backlog item (25kzda 3.4 permits "any spec it requires"; spec `z7nbn1` 5.5c tests plans only, and a spec-producing graduation needs the human-approval attestation a runner cannot supply; recorded as OQ-01); the existing post-execution `process_backlog_close` (`done` on executed carriers), which is unchanged.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_backlog_production.py
- Item-Dependencies: executed:aeq7f8
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 6
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: y3p3p5

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 06 of Set artdispatch). The five BACKLOG-* codes re-measured at HEAD 310ea53e (zero enforcement); evaluate_blocking_close's graduated branch and check_release_gates' cross-tree rules confirmed as the authorities to consume; backlog corpus measured (166 open, 620 total).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running an open backlog item produces review-ready plans that link back to it and carry its release gate, moves the item to `graduated` (never `done`) through the gated setter only after a verified handoff, and leaves the item `open` whenever any of the five backlog handoff checks fails.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 RE-MEASURE at the executing HEAD: `grep -rn "BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` (expect only plan `aeq7f8`'s module scaffolding, no enforcement); paste `25kzda` 4.9's five rows' pass criteria and Action cells verbatim into Findings; confirm the gated `aw backlog set <path> --status graduated` path runs `check_engine.evaluate_blocking_close` and returns ok for a release-gated item (scratch item, paste output); confirm the positional `aw backlog set graduated <id6>` spelling does NOT (paste); confirm which `check_release_gates` rule ids fire for a dropped gate, a dangling `From-Backlog`, and an orphaned live blocker on a scratch tree; read plan `aeq7f8`'s executed production turn and name the extension points this plan uses.
  - Depends on: none
  - Expected outcome: the five rows pasted; both setter spellings' behavior pasted; the three cross-tree rule ids confirmed; extension points named.
  - Execution state: pending

### Task group 2: the verifiers

- [ ] E-02 ADD THE FIVE VERIFIERS to `agent_workflows/production_checks.py`, each returning templated findings from `25kzda` 4.9: `backlog_graduate_count(repo, item_id6, baseline_plan_ids)` (at least one new ACTIVE plan and every new plan claiming this item links `From-Backlog: <id6>`); `backlog_graduate_ipd(repo, item_id6, produced_paths)` (every produced plan canonical, `to-review`, in `pending/`, resolved `Item-Dependencies`, `review-finalize` lint conforming; share `aeq7f8`'s conformance helper rather than copying it); `backlog_gate_handoff(repo, item_id6, produced_paths)` (if the item carries `Blocks-Release: R`, every produced plan carries a gate `check_engine._same_release` equates with R, checked BEFORE the transition; all references resolve); `backlog_graduate_legitimacy(repo, item_id6, handoff_commit)` (the item changed `open -> graduated` through the setter only after the handoff commit: its history carries the setter record naming the produced plans, the item file's `graduated` move is in a commit whose parent chain includes the handoff commit, and its status is not `done`); `backlog_cross_tree(repo, item_id6)` (no `check_release_gates` finding located at the item or any produced plan).
  - Depends on: E-01
  - Expected outcome: each returns `[]` for a legitimate handoff and the templated finding for each violation.
  - Execution state: pending

### Task group 3: the dispatcher

- [ ] E-03 ADD THE BACKLOG PRODUCTION TURN AND HANDOFF. Route a `backlog`/`plan` entry to the production turn plan `aeq7f8` built, with the backlog prompt (Scope bullet (a)); capture the baseline; after the turn, commit the new plans path-scoped (the handoff commit); run COUNT, IPD and GATE-HANDOFF. Any finding: item `fail-gate` with every finding recorded via `render_stream.record_refusal`, item left `open`, produced files quarantined on the lane and not integrated. No finding: run the gated setter `aw backlog set <item path> --status graduated --message "graduated by run <run-id>: <plan id6s>"` (plus `--graduated-to <setid>` when every produced plan shares one Set) through `pinned_module_argv`, in the tree holding the handoff commit, commit that transition path-scoped, then run LEGITIMACY and CROSS-TREE against the result. A finding THERE: restore the item to `open` through the setter (`aw backlog set <path> --status open --message "handoff incomplete: <code>"`, the recovery `25kzda` 4.9 names), commit, and fail the item. Success: record `generated_next_actions` on the item, end it `executed`. The runner NEVER sets `done`; the existing `process_backlog_close` must not fire for a production item (it keys on a plan's `from_backlog` after execution; confirm by test that a `backlog`-typed entry never reaches it).
  - Depends on: E-02
  - Expected outcome: a legitimate handoff ends `executed` with the item under `graduated/`; each failure leaves the item `open`.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-04 ADD `tests/test_backlog_production.py` (behavioral only; temp git repos; `AW_HOME` isolated; fake agent via patched host spawn). Spec 5.5c on BOTH hosts: (1) success: one conformant plan carrying `From-Backlog` and the item's `Blocks-Release: next`; item `graduated` via the setter (history shows it), never `done`; plan listed in `generated_next_actions`; queue id set before equals after, and resume spawns nothing; (2) `BACKLOG-GRADUATE-COUNT`: no plan written; (3) `BACKLOG-GRADUATE-IPD`: a plan with `- Status: draft` or unresolved `Item-Dependencies`; (4) `BACKLOG-GATE-HANDOFF`: a release-gated item whose plan omits the gate; (5) `BACKLOG-GRADUATE-LEGITIMACY`: the fake agent itself sets the item `done` (and, separately, sets it `graduated` before any plan exists, so the transition precedes the handoff commit); (6) `BACKLOG-CROSS-TREE`: a produced plan with a dangling `From-Spec` or a mismatched gate that only the cross-tree checker sees; in EACH of (2)-(6) the item ends `open` (for (5), restored to `open` through the setter) and the item fails naming the code.
  - Depends on: E-03
  - Expected outcome: all pass on both hosts; every case FAILS against the pre-change code.
  - Execution state: pending

- [ ] E-05 UNIT-TEST THE FIVE VERIFIERS DIRECTLY against hand-built trees, one pass and one fail fixture per pass-criterion clause.
  - Depends on: E-04
  - Expected outcome: each clause has a passing and a failing fixture.
  - Execution state: pending

- [ ] E-06 RUN the bare suite before and after, and `aw check release-gates` on a scratch repo after a successful graduation to show no finding.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty; the scratch release-gates check is clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `graduated` means the design is handed off; `done` means the code is written and validated (AGENTS.md "Acting on a backlog item"; `backlog.py` bklgrad comment). A release-gated item may be `graduated` freely and may reach `done` only by handoff, evidence, or de-gating (`evaluate_blocking_close`).
- The GATED backlog setter spelling is `aw backlog set <path> --status <s>`, which dispatches to `backlog.run_set` and runs the shared predicate; the positional spelling dispatches to `status_set.run_set_command` and does not (`close_backlog_item` docstring, verified live there).
- `aw ipd scaffold --from-backlog <id6>` inherits Priority, Work-Kind and Blocks-Release (its `--help`), so a well-behaved turn carries the gate by construction; `BACKLOG-GATE-HANDOFF` verifies rather than assumes it.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | verification | The five `BACKLOG-*` codes have zero enforcement. | `grep -rn "BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` -> no hits |
| F-2 | INFO | `check_engine.evaluate_blocking_close` | `graduated` is explicitly legitimate for a gated item and drops nothing. | branch `if target_status == "graduated" and blocks_release: return CloseVerdict(True, "ok", ...)` |
| F-3 | INFO | `check_engine.check_release_gates` | Cross-tree gate rules already exist. | rule ids `check.from-backlog-gate-mismatch`, `check.from-backlog-dangling`, `check.orphaned-live-blocker`, `check.blocking-item-closed-without-gate` in `check_engine`'s rule table |
| F-4 | INFO | corpus | 620 backlog items: 166 open, 122 graduated, 315 done, 15 parked, 2 blocked. | `backlog._iter_items` + status read |

## Proposed changes (ordered, validatable)

1. E-01 re-measures and names the extension points.
2. E-02 adds the five verifiers.
3. E-03 adds the backlog production turn, gated transition and rollback.
4. E-04 adds run-level tests for spec 5.5c's matrix.
5. E-05 adds verifier unit tests.
6. E-06 runs the suite and a scratch release-gates check.

## Deferred / out of scope (with reason)

- Producing a SPEC (rather than plans) from a backlog item.
  - Carrier-Declined: spec `z7nbn1` 5.5c specifies plan production only, and a spec that graduates work must be human-approved (`aw specs set approved --by-human`), which an unattended production turn cannot attest; OQ-01 records it.
- Changing `process_backlog_close` (closing `done` after carriers execute).
  - Carrier-Declined: unchanged by spec `z7nbn1`; E-03 only proves a production item never reaches it.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/backlog.py`, `check_engine.py` are called, not changed.
- Scope-Paths justification: `production_checks.py` gains the five verifiers beside `aeq7f8`'s; `runner_shared.py` holds the backlog dispatch, transition and rollback; host modules hold any host-specific prompt spelling; the new test file holds E-04/E-05.

## Required tests / validation

- `tests/test_backlog_production.py` (new): the success path and all five refusal codes of spec 5.5c on both hosts, each leaving the item `open`; report-only and resume checks; verifier unit cases; shown failing before the change.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` section 3 (backlog half), OQ-05 and acceptance 5.5c as written, and `25kzda` 3.4's `open` row and 4.9's five rows with their existing text.
- No user-facing docs.

## Open questions

### OQ-01: May the backlog production turn author a spec instead of plans?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NOT in this plan, from repository evidence. `25kzda` 3.4 allows "any spec it requires (created and approved under the authority of this request)", but spec `z7nbn1` 5.5c's acceptance criterion names plans only, and approval of a spec is a human-only transition (`attention_contract.TRANSITION_AUTHORITY["->approved"]` requires `by_human`); an unattended turn asserting it would forge the attestation the AGENTS.md "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD" rule forbids. The prompt tells the agent to write plans; a turn that writes a spec instead fails `BACKLOG-GRADUATE-COUNT`.

### OQ-02: Scope of the backlog production ruling

- Blocking: no
- Status: resolved
- Owner: maintainer (ruled 2026-09-26)
- Resolution or deferral rationale: RULED by the maintainer 2026-09-26 at spec review (spec `z7nbn1` OQ-05): the backlog production action and ALL FIVE `BACKLOG-*` verification codes of `25kzda` 4.9 are in scope, covered by acceptance criterion 5.5c. This plan implements exactly that set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the grep, the five 25kzda 4.9 rows verbatim, both setter spellings' outputs on a scratch gated item, the three cross-tree rule ids observed, and the named extension points.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the five signatures and one `python3 -c` run per verifier on a hand-built tree showing `[]` and a templated finding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a success run's item record and the backlog item's new location and history line; a GATE-HANDOFF failure run's item record with the item still under `open/`; and a LEGITIMACY failure run showing the setter restore to `open` in `git log --oneline` for the item path.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_backlog_production.py -q` passing with count, and with E-03 reverted the run-level cases FAILING; passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the verifier unit case names and pass output, one pass and one fail fixture per clause.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty), and the scratch `aw check release-gates` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Running an open backlog item now GRADUATES it: one agent turn writes review-ready plans linked to the item and carrying its release gate, the runner verifies the handoff with the five `25kzda` 4.9 checks, then moves the item to `graduated` (never `done`) through the gated setter and lists the plans as next actions without running them. Any failed check leaves the item `open` (restoring it through the setter if the failure is found after the transition) and quarantines the produced files on the lane. Order 06 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `aeq7f8`, whose production machinery it reuses.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
