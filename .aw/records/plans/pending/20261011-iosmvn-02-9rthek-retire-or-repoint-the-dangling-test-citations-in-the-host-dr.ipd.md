# IPD: Retire or repoint the dangling test citations in the host drivers and runner peripherals

- Date: 2026-10-11
- Kind: child
- Concern: The two host drivers and four runner-adjacent modules carry 19 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already record the deletion. Measured at authoring HEAD `8538be828` with the Set measurement command over `agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/ipd_lint.py agent_workflows/runner_shutdown.py agent_workflows/run_viewer.py agent_workflows/artifact_audit.py`: `UNRETIRED 19`.
- Scope: IN: comment and docstring prose at the 19 sites in Findings, in those six files. Each site is dispositioned REPOINT, RETIRE-PIN or RETIRE-UNGUARDED (definitions in Project conventions), preserving each comment's design reason. OUT: any executable change; restoring any test; the sites in these files owned by other plans (`3tov52`/`65d5zf` for `test_review_findings_cascade.py`/`test_runner_stop_triggers.py`/`test_orchestrator_probe_cache.py`, `046nys`/`dtelfb`, `yf1p8y` for `test_runner_backlog_close.py`), excluded by the measurement regex; the `__all__`/re-export rework (`fh8x8k`/`vzk1iw`); filing backlog for unguarded properties (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lint.py, agent_workflows/runner_shutdown.py, agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, .aw/records/plans/pending/20261011-iosmvn-02-9rthek-retire-or-repoint-the-dangling-test-citations-in-the-host-dr.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9rthek

## Workflow history
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 19 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in the host drivers and runner peripherals truthful, so that each either names a live test that asserts the property or states the guard's deletion and whether anything still asserts it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [ ] E-01 Re-measure at execution HEAD: run the Set measurement command over the six Scope-Paths source files and record the hit list, `UNRETIRED N`, and `git rev-parse --short HEAD`. Sibling plans `65d5zf`, `dtelfb` and `vzk1iw` edit some of these files; if any has landed, the excluded clusters are unaffected but line positions move, so match by enclosing symbol and cited path. Disposition any delta by the same rules.
  - Depends on: none
  - Expected outcome: recorded list equals Findings S-01..S-19, or each delta carries a disposition.
  - Execution state: pending

- [ ] E-02 For each site, decide REPOINT / RETIRE-PIN / RETIRE-UNGUARDED and record a `Site | Disposition | Evidence` table appended to Findings, with evidence of the same kinds as the Set conventions require (live `rg -n` hit in `tests/` for REPOINT; the deleted test's form via `git show 19313eed^:<path>` for RETIRE-PIN; an empty `rg` over `tests/` for RETIRE-UNGUARDED).
  - Depends on: E-01
  - Expected outcome: exactly one dispositioned row per E-01 hit (re-derived at execution; 19 at authoring and at review HEAD `3e328494b` is context, not the bar), each with evidence. S-14 is recorded RETIRE-UNGUARDED unless E-02 finds a live test asserting `agy_runipd.build_parser()` defaults `dangerously_skip_permissions` to True (review found none; see Findings note).
  - Execution state: pending

### Task group 2: Edit

- [ ] E-03 Apply the dispositions as comment/docstring edits (no statement, constant, signature, or identifier changes), keeping each design reason and, for both RETIRE forms, placing `19313eed` within three lines of the citation using the existing `oc_runipd.py` wording ("deleted in `19313eed`; no live guard currently asserts this"). Where an `oc_runipd`/`agy_runipd` twin comment exists (S-02/S-03 vs S-09/S-10/S-13), edit both identically so the drivers do not contradict each other. At S-18 also correct the same sentence's claim that `tests/test_artifact_audit.py` asserts object identity (see Findings note on S-18). Keep S-14's "Do NOT harden" instruction and its R4.1c reason; only the enforcement claim changes.
  - Depends on: E-02
  - Expected outcome: measurement over the six files prints `UNRETIRED 0`, and every edited passage reads as a true statement about HEAD (the measurement only proves `19313eed` is nearby, not that the claim is true).
  - Execution state: pending

- [ ] E-04 Prove prose-only and regression-free: run the AST-equivalence command against the E-01 HEAD over the six source files, and the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures, or any failure shown to pre-exist by re-running the failing test ids at the E-01 HEAD in a scratch `git worktree` (a prose-only change cannot cause one).
  - Execution state: pending

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND and AST-EQUIVALENCE COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions; this plan passes its six source files as arguments.
- Dispositions: REPOINT (a live test at HEAD asserts the same property; cite it), RETIRE-PIN (deleted test read source or pinned structure; state the deletion and that it will not return under `GUIDING_PRINCIPLES` P16), RETIRE-UNGUARDED (deleted test was behavioral and no live test asserts the property; state the deletion and that no live guard asserts it).
- `oc_runipd.py` and `agy_runipd.py` already use the retirement wording at 13 sites (the `already-retired` partition of the measurement); match it.
- `tests/test_runner_delegation_and_host_independence.py` and `tests/test_cross_tree_session_refusal.py` are the established outcome-based replacements for some driver-symmetry guards; check them first for REPOINT.
- Run the suite bare: `python3 -m pytest`. Cite code by symbol.

## Findings

Measured at HEAD `8538be828`; re-measured at review HEAD `3e328494b` with the identical 19 hits (same files, symbols, and cited paths).

| Site | File | Enclosing symbol | Cited path |
|---|---|---|---|
| S-01 | `oc_runipd.py` | module (format_run_order_announcement re-export) | `tests/test_run_order_announcement.py` |
| S-02 | `oc_runipd.py` | module (edge_satisfied re-export) | `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` |
| S-03 | `oc_runipd.py` | module (dependency regex note) | `tests/test_runner_item_dependencies.py` |
| S-04 | `oc_runipd.py` | `finalize_orchestrator` | `tests/test_lane_tool_identity.py` |
| S-05 | `oc_runipd.py` | `terminate_process` | `tests/test_runner_shutdown.py` |
| S-06 | `oc_runipd.py` | `run_queue` | `tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned` |
| S-07 | `oc_runipd.py` | `main` | `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` |
| S-08 | `agy_runipd.py` | module (render_stream re-exports) | `tests/test_refusal_surfacing.py` |
| S-09 | `agy_runipd.py` | module (decide_orchestrator_dispatch note) | `tests/test_runner_item_dependencies.py` |
| S-10 | `agy_runipd.py` | module (dependency regex note) | `tests/test_runner_item_dependencies.py` |
| S-11 | `agy_runipd.py` | module (record fallback note) | `tests/test_rununify_record.py` |
| S-12 | `agy_runipd.py` | module (session-id note) | `tests/test_rununify_conflicts.py` |
| S-13 | `agy_runipd.py` | module (satisfaction semantics) | `tests/test_runner_item_dependencies.py::test_the_implementation_is_shared_not_copied` |
| S-14 | `agy_runipd.py` | `run_agy_turn` | `tests/test_lane_permission_posture.py` |
| S-15 | `agy_runipd.py` | `build_parser` | `tests/test_rununify_build_parser.py` |
| S-16 | `ipd_lint.py` | module (driver-ignorance note) | `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` |
| S-17 | `runner_shutdown.py` | module (`KNOWN_ITEM_STATUSES`) | `tests/test_runner_shutdown.py` |
| S-18 | `run_viewer.py` | module (artifact_audit re-exports) | `tests/test_runner_refork_guard.py` |
| S-19 | `artifact_audit.py` | module docstring | `tests/test_runner_refork_guard.py` |

Note on S-04: the comment cites a bare line range (585 to 609) into the deleted `tests/test_lane_tool_identity.py`; whatever the disposition, the line range is removed.
Note on S-18 (found at review): the same sentence also says the names are "asserted by object identity in `tests/test_artifact_audit.py`". That file is live, so the measurement does not flag it, but the identity test it meant (`test_run_viewer_audit_type_is_the_shared_module_object`, `assertIs(run_viewer.StepArtifactAudit, artifact_audit.ArtifactAudit)`) was removed from it by `19313eed` (`git show 19313eed7 -- tests/test_artifact_audit.py`), and the live file never imports `run_viewer`. E-02/E-03 disposition that claim together with S-18.
Note on S-14: the comment says the test "PINS the default and will fail if it is flipped"; that is a load-bearing safety claim (a guard against hardening an agy permission default), so E-02 must check whether any live test asserts that default before retiring it, and if none does it is a RETIRE-UNGUARDED row for `ellenm` to file. Review at `3e328494b`: the deleted guard was behavioral (`TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` in `git show 19313eed^:tests/test_lane_permission_posture.py`), and `rg -n dangerously_skip_permissions tests/` returns nothing, so no live test asserts the default.

## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table. 3. E-03 prose edits, twin comments in lockstep. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog for RETIRE-UNGUARDED properties.
  - Carrier: ellenm
- The `test_review_findings_cascade.py`, `test_runner_stop_triggers.py`, `test_orchestrator_probe_cache.py` sites in these files.
  - Carrier: 3tov52
- The `test_runner_backlog_close.py` / `test_runner_layering.py` residual coverage and sites.
  - Carrier: yf1p8y
- The `agy_runipd` re-export mechanism (`__all__`, `noqa`).
  - Carrier: fh8x8k
- Restoring any source-reading guard.
  - Carrier-Declined: forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16.

## Scope check

- Over-scope: none; prose only in six files, proven by E-04.
- Under-scope: none; all 19 measured sites have rows and an E-item.

## Required tests / validation

- Measurement over the six files -> `UNRETIRED 0`.
- AST-equivalence -> `AST-DIFFER []`.
- Bare `python3 -m pytest` with no failures.

## Spec / documentation sync

N/A: comment and docstring prose only; no `.spec.md` is touched.

## Open questions

### OQ-01: Should twin driver comments be edited even if only one site is in the measurement?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, when the twin is in this plan's Scope-Paths and carries the same claim; the precedent is plan `65d5zf` F-05, which edited the `oc_runipd` twin so the drivers do not contradict each other.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted measurement output with `UNRETIRED N` and HEAD sha, deltas listed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the appended disposition table, one row per site, with pasted evidence for every REPOINT and RETIRE-UNGUARDED row, and an explicit S-14 finding.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted post-edit measurement ending `UNRETIRED 0`, `git diff --stat` over the six files, and each edited passage quoted after the edit (including the S-18 `test_artifact_audit.py` sentence and both halves of every twin pair).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` with the `<rev>` used, and the bare `python3 -m pytest` summary line (stated run with no added flags); for any failure, the pasted pre-existence re-run at E-01 HEAD.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths through `aw commit 9rthek -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, AST check, and suite claim; never claim a result you did not run. Sibling plans `65d5zf`, `dtelfb` and `vzk1iw` edit other passages of these files; if a site here was concurrently changed in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
