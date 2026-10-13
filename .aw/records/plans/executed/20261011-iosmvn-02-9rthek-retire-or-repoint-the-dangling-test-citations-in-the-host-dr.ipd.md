# IPD: Retire or repoint the dangling test citations in the host drivers and runner peripherals

- Date: 2026-10-11
- Kind: child
- Concern: The two host drivers and four runner-adjacent modules carry 19 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already record the deletion. Measured at authoring HEAD `8538be828` with the Set measurement command over `agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/ipd_lint.py agent_workflows/runner_shutdown.py agent_workflows/run_viewer.py agent_workflows/artifact_audit.py`: `UNRETIRED 19`.
- Scope: IN: comment and docstring prose at the 19 sites in Findings, in those six files. Each site is dispositioned REPOINT, RETIRE-PIN or RETIRE-UNGUARDED (definitions in Project conventions), preserving each comment's design reason. OUT: any executable change; restoring any test; the sites in these files owned by other plans (`3tov52`/`65d5zf` for `test_review_findings_cascade.py`/`test_runner_stop_triggers.py`/`test_orchestrator_probe_cache.py`, `046nys`/`dtelfb`, `yf1p8y` for `test_runner_backlog_close.py`), excluded by the measurement regex; the `__all__`/re-export rework (`fh8x8k`/`vzk1iw`); filing backlog for unguarded properties (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lint.py, agent_workflows/runner_shutdown.py, agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, .aw/records/plans/pending/20261011-iosmvn-02-9rthek-retire-or-repoint-the-dangling-test-citations-in-the-host-dr.ipd.md
- Item-Dependencies: none
- Status: executed
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
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 9rthek verified (set iosmvn, attempt 1).
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 19 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in the host drivers and runner peripherals truthful, so that each either names a live test that asserts the property or states the guard's deletion and whether anything still asserts it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [x] E-01 Re-measure at execution HEAD: run the Set measurement command over the six Scope-Paths source files and record the hit list, `UNRETIRED N`, and `git rev-parse --short HEAD`. Sibling plans `65d5zf`, `dtelfb` and `vzk1iw` edit some of these files; if any has landed, the excluded clusters are unaffected but line positions move, so match by enclosing symbol and cited path. Disposition any delta by the same rules.
  - Depends on: none
  - Expected outcome: recorded list equals Findings S-01..S-19, or each delta carries a disposition.
  - Execution state: performed

- [x] E-02 For each site, decide REPOINT / RETIRE-PIN / RETIRE-UNGUARDED and record a `Site | Disposition | Evidence` table appended to Findings, with evidence of the same kinds as the Set conventions require (live `rg -n` hit in `tests/` for REPOINT; the deleted test's form via `git show 19313eed^:<path>` for RETIRE-PIN; an empty `rg` over `tests/` for RETIRE-UNGUARDED).
  - Depends on: E-01
  - Expected outcome: exactly one dispositioned row per E-01 hit (re-derived at execution; 19 at authoring and at review HEAD `3e328494b` is context, not the bar), each with evidence. S-14 is recorded RETIRE-UNGUARDED unless E-02 finds a live test asserting `agy_runipd.build_parser()` defaults `dangerously_skip_permissions` to True (review found none; see Findings note).
  - Execution state: performed

### Task group 2: Edit

- [x] E-03 Apply the dispositions as comment/docstring edits (no statement, constant, signature, or identifier changes), keeping each design reason and, for both RETIRE forms, placing `19313eed` within three lines of the citation using the existing `oc_runipd.py` wording ("deleted in `19313eed`; no live guard currently asserts this"). Where an `oc_runipd`/`agy_runipd` twin comment exists (S-02/S-03 vs S-09/S-10/S-13), edit both identically so the drivers do not contradict each other. At S-18 also correct the same sentence's claim that `tests/test_artifact_audit.py` asserts object identity (see Findings note on S-18). Keep S-14's "Do NOT harden" instruction and its R4.1c reason; only the enforcement claim changes.
  - Depends on: E-02
  - Expected outcome: measurement over the six files prints `UNRETIRED 0`, and every edited passage reads as a true statement about HEAD (the measurement only proves `19313eed` is nearby, not that the claim is true).
  - Execution state: performed

- [x] E-04 Prove prose-only and regression-free: run the AST-equivalence command against the E-01 HEAD over the six source files, and the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures, or any failure shown to pre-exist by re-running the failing test ids at the E-01 HEAD in a scratch `git worktree` (a prose-only change cannot cause one).
  - Execution state: performed

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

### E-02 Disposition Table

| Site | File | Enclosing symbol | Cited path | Disposition | Evidence |
|---|---|---|---|---|---|
| S-01 | `oc_runipd.py` | module (format_run_order_announcement re-export) | `tests/test_run_order_announcement.py` | RETIRE-PIN | Deleted test `AnnouncementFormatterTests.test_both_drivers_bind_the_same_formatter_object` in `19313eed^:tests/test_run_order_announcement.py` (`assertIs(mod.format_run_order_announcement, render_stream.format_run_order_announcement)`); deleted in `19313eed`; `rg -n "format_run_order_announcement" tests/` returns empty (only fixture) |
| S-02 | `oc_runipd.py` | module (edge_satisfied re-export) | `tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` | RETIRE-PIN | Deleted test `CrossDriverSymmetryTests` in `19313eed^:tests/test_runner_item_dependencies.py` pinned driver attributes by object identity (`_SHARED_NAMES` / `CrossDriverSymmetryTests`); deleted in `19313eed`; no live guard asserts `oc_runipd.classify_drain_block is agy_runipd.classify_drain_block` |
| S-03 | `oc_runipd.py` | module (dependency regex note) | `tests/test_runner_item_dependencies.py` | RETIRE-PIN | Deleted test `AntiDivergenceGuardTests._DRIVER_SOURCES` in `19313eed^:tests/test_runner_item_dependencies.py` read driver source files looking for `_DEPS_RE` and `def _read_deps`; deleted in `19313eed`; no live guard asserts this source regex |
| S-04 | `oc_runipd.py` | `finalize_orchestrator` | `tests/test_lane_tool_identity.py` | RETIRE-PIN | Deleted test `test_no_unpinned_module_launch_sites_remain` / `test_every_site_is_classified_and_none_unknown` in `19313eed^:tests/test_lane_tool_identity.py` read source AST (`_classify_sites`); bare line range `:585-609` removed; deleted in `19313eed`; `rg -n "test_lane_tool_identity" tests/` returns empty |
| S-05 | `oc_runipd.py` | `terminate_process` | `tests/test_runner_shutdown.py` | RETIRE-PIN | Deleted test `test_tuning_driver_constants_passes_through_to_reaper` in `19313eed^:tests/test_runner_shutdown.py` spied on `rs.terminate_process` to check `oc._SIGINT_GRACE_SECONDS` passthrough; deleted in `19313eed`; no live guard checks passthrough of module constants |
| S-06 | `oc_runipd.py` | `run_queue` | `tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned` | RETIRE-PIN | Deleted test `TheSignalReportRefreshSitesArePinned` in `19313eed^:tests/test_rununify_run_queue.py` pinned call site count in source AST; deleted in `19313eed`; no live test pins this count |
| S-07 | `oc_runipd.py` | `main` | `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` | RETIRE-UNGUARDED | Deleted test `RunnerMainOutputOnInterruptTests` in `19313eed^:tests/test_interrupt_menu.py` tested stderr message byte-identical string; deleted in `19313eed`; `rg -n "Interrupted; durable run state was preserved" tests/` returns empty |
| S-08 | `agy_runipd.py` | module (render_stream re-exports) | `tests/test_refusal_surfacing.py` | RETIRE-PIN | Deleted test `TestOneDefinitionAcrossHosts.test_both_hosts_bind_the_same_object` in `19313eed^:tests/test_refusal_surfacing.py` asserted object identity across hosts; deleted in `19313eed`; no live guard asserts object identity |
| S-09 | `agy_runipd.py` | module (decide_orchestrator_dispatch note) | `tests/test_runner_item_dependencies.py` | RETIRE-PIN | Deleted test `CrossDriverSymmetryTests` / `_SHARED_NAMES` in `19313eed^:tests/test_runner_item_dependencies.py` pinned presence and object identity; deleted in `19313eed`; no live guard asserts this name |
| S-10 | `agy_runipd.py` | module (dependency regex note) | `tests/test_runner_item_dependencies.py` | RETIRE-PIN | Twin of S-03; deleted test `AntiDivergenceGuardTests._DRIVER_SOURCES` read driver source looking for `_DEPS_RE`; deleted in `19313eed`; no live guard asserts this source regex |
| S-11 | `agy_runipd.py` | module (record fallback note) | `tests/test_rununify_record.py` | RETIRE-UNGUARDED | Deleted test `test_legacy_manifest_fallback_infers_orchestrator_kind_from_plan_file` in `19313eed^:tests/test_rununify_record.py` tested behavioral fallback for legacy manifests missing `kind`; deleted in `19313eed`; `rg -n "plan_kind_from_file" tests/` and `rg -n "resolve_manifest_kind" tests/` return empty |
| S-12 | `agy_runipd.py` | module (session-id note) | `tests/test_rununify_conflicts.py` | RETIRE-UNGUARDED | Deleted test `test_pre_union_agy_picked_first_hit_now_prefers_ses` in `19313eed^:tests/test_rununify_conflicts.py` tested resolution of `conversation_id` vs `ses_`; deleted in `19313eed`; general `ses_` preference asserted in `tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed` but no live guard tests the specific `06-ct4w0a-D1` conflict case |
| S-13 | `agy_runipd.py` | module (satisfaction semantics) | `tests/test_runner_item_dependencies.py::test_the_implementation_is_shared_not_copied` | RETIRE-PIN | Deleted test `test_the_implementation_is_shared_not_copied` in `19313eed^:tests/test_runner_item_dependencies.py` pinned object identity via `_SHARED_NAMES`; deleted in `19313eed`; no live guard asserts object identity |
| S-14 | `agy_runipd.py` | `run_agy_turn` | `tests/test_lane_permission_posture.py` | RETIRE-UNGUARDED | Deleted test `TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` in `19313eed^:tests/test_lane_permission_posture.py` tested parser default for `--dangerously-skip-permissions`; deleted in `19313eed`; `rg -n dangerously_skip_permissions tests/` returns empty; no live guard asserts this default |
| S-15 | `agy_runipd.py` | `build_parser` | `tests/test_rununify_build_parser.py` | RETIRE-PIN | Deleted test `test_both_hosts_register_the_same_seven_subparsers` in `19313eed^:tests/test_rununify_build_parser.py` pinned parser subparser registration list; deleted in `19313eed`; no live test asserts `agy_runipd` registers `audit` subparser |
| S-16 | `ipd_lint.py` | module (driver-ignorance note) | `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` | RETIRE-PIN | Deleted test `AntiDivergenceGuardTests` in `19313eed^:tests/test_runner_item_dependencies.py` read module text looking for driver names (`assertNotIn(runner_only, text)`); deleted in `19313eed`; no live guard checks this source invariant |
| S-17 | `runner_shutdown.py` | module (`KNOWN_ITEM_STATUSES`) | `tests/test_runner_shutdown.py` | RETIRE-PIN | Deleted test `test_ledger_status_vocabulary_covers_both_drivers` in `19313eed^:tests/test_runner_shutdown.py` pinned set difference of module constants; deleted in `19313eed`; no live guard checks this set relationship |
| S-18 | `run_viewer.py` | module (artifact_audit re-exports) | `tests/test_runner_refork_guard.py` | RETIRE-PIN | Deleted test `tests/test_runner_refork_guard.py` and deleted test `OneImplementationTests.test_run_viewer_audit_type_is_the_shared_module_object` in `tests/test_artifact_audit.py` pinned object identity (`assertIs(run_viewer.StepArtifactAudit, artifact_audit.ArtifactAudit)`); deleted in `19313eed`; `rg -n "StepArtifactAudit" tests/` shows no live object-identity test in `tests/` |
| S-19 | `artifact_audit.py` | module docstring | `tests/test_runner_refork_guard.py` | RETIRE-PIN | Deleted test `tests/test_runner_refork_guard.py` pinned 28 (runner, symbol) pairs via AST inspection and object identity; deleted in `19313eed`; no live guard asserts this table |

Explicit S-14 finding: S-14 is recorded RETIRE-UNGUARDED because the deleted guard was behavioral (`TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` in `git show 19313eed^:tests/test_lane_permission_posture.py`), and `rg -n dangerously_skip_permissions tests/` returned empty (exit code 1), so no live test asserts that `agy_runipd.build_parser()` defaults `dangerously_skip_permissions` to True.

## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table. 3. E-03 prose edits, twin comments in lockstep. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog for RETIRE-UNGUARDED properties.
  - Carrier: ellenm
- The `test_review_findings_cascade.py`, `test_runner_stop_triggers.py`, `test_orchestrator_probe_cache.py` sites in these files.
  - Carrier: 3tov52
  - Carrier-Evidence: .aw/records/backlog/done/20261001-3tov52-01-3tov52-retire-or-update-dangling-test-symbol-citations-fo.backlog.md
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

- [x] V-01 validates E-01
  - Required evidence: pasted measurement output with `UNRETIRED N` and HEAD sha, deltas listed.
  - Observed evidence:
    Measurement output at execution HEAD 7f8bfa478:
    ```
    agent_workflows/oc_runipd.py 134 tests/test_run_order_announcement.py
    agent_workflows/oc_runipd.py 272 tests/test_runner_item_dependencies.py
    agent_workflows/oc_runipd.py 937 tests/test_runner_item_dependencies.py
    agent_workflows/oc_runipd.py 1144 tests/test_lane_tool_identity.py
    agent_workflows/oc_runipd.py 2334 tests/test_runner_shutdown.py
    agent_workflows/oc_runipd.py 3921 tests/test_rununify_run_queue.py
    agent_workflows/oc_runipd.py 5610 tests/test_interrupt_menu.py
    agent_workflows/agy_runipd.py 96 tests/test_refusal_surfacing.py
    agent_workflows/agy_runipd.py 583 tests/test_runner_item_dependencies.py
    agent_workflows/agy_runipd.py 843 tests/test_runner_item_dependencies.py
    agent_workflows/agy_runipd.py 1940 tests/test_rununify_record.py
    agent_workflows/agy_runipd.py 2202 tests/test_rununify_conflicts.py
    agent_workflows/agy_runipd.py 2212 tests/test_runner_item_dependencies.py
    agent_workflows/agy_runipd.py 2505 tests/test_lane_permission_posture.py
    agent_workflows/agy_runipd.py 4067 tests/test_rununify_build_parser.py
    agent_workflows/ipd_lint.py 1267 tests/test_runner_item_dependencies.py
    agent_workflows/runner_shutdown.py 63 tests/test_runner_shutdown.py
    agent_workflows/run_viewer.py 542 tests/test_runner_refork_guard.py
    agent_workflows/artifact_audit.py 10 tests/test_runner_refork_guard.py
    UNRETIRED 19
    ```
    Deltas: exactly matches authoring and review Findings S-01..S-19 (0 deltas).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the appended disposition table, one row per site, with pasted evidence for every REPOINT and RETIRE-UNGUARDED row, and an explicit S-14 finding.
  - Observed evidence:
    Appended E-02 Disposition Table in Findings contains 19 rows matching S-01..S-19 with evidence for all rows and an explicit S-14 finding:
    S-07: `rg -n "Interrupted; durable run state was preserved" tests/` exited 1 (empty).
    S-11: `rg -n "plan_kind_from_file" tests/` exited 1 (empty); `rg -n "resolve_manifest_kind" tests/` exited 1 (empty).
    S-12: `tests/test_rununify_conflicts.py` deleted in `19313eed`; `tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed` asserts general `ses_` preference but no live test asserts `06-ct4w0a-D1` `conversation_id` conflict.
    S-14: `rg -n dangerously_skip_permissions tests/` exited 1 (empty); `TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser` in `git show 19313eed^:tests/test_lane_permission_posture.py` deleted in `19313eed`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted post-edit measurement ending `UNRETIRED 0`, `git diff --stat` over the six files, and each edited passage quoted after the edit (including the S-18 `test_artifact_audit.py` sentence and both halves of every twin pair).
  - Observed evidence:
    Post-edit measurement across the six files:
    ```
    UNRETIRED 0
    ```
    `git diff --stat`:
    ```
     agent_workflows/agy_runipd.py      | 36 ++++++++++++++++-----------------
     agent_workflows/artifact_audit.py  |  5 +++--
     agent_workflows/ipd_lint.py        |  5 +++--
     agent_workflows/oc_runipd.py       | 41 ++++++++++++++++++++------------------
     agent_workflows/run_viewer.py      |  4 ++--
     agent_workflows/runner_shutdown.py |  4 ++--
     6 files changed, 50 insertions(+), 45 deletions(-)
    ```
    Quoted edited passages:
    - S-01 (`oc_runipd.py:130-140`):
      `# it on the batch's first commit (`tests/test_run_order_announcement.py` was deleted in `19313eed`;`
      `# no live guard currently asserts this property). The redundant alias is what marks the import`
    - S-02 (`oc_runipd.py:268-275`):
      `# (`tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests` was deleted in `19313eed`; no live`
      `# guard currently asserts this) required each driver to CARRY the attribute and asserted it was the`
    - S-03 (`oc_runipd.py:929-937`):
      `# Re-adding a dependency regex here was guarded by`
      `# `tests/test_runner_item_dependencies.py` (deleted in `19313eed`; no live guard currently asserts this).`
    - S-04 (`oc_runipd.py:1140-1147`):
      `documented `oc`-only module-launch site that `tests/test_lane_tool_identity.py` (deleted in`
      ``19313eed`; no live guard currently asserts this) asserted as an expected asymmetry against`
      ``agy`, so deleting it would quietly erase a discussed design point, while leaving the old string`
      `would leave a call site the guard refuses as a trap for whoever next wires it up. Do NOT add`
      `an `agy` twin; the deleted test forbade it.`
    - S-05 (`oc_runipd.py:2330-2335`):
      `inert (`tests/test_runner_shutdown.py` was deleted in `19313eed`; no live guard currently asserts`
      `this passthrough tuning).`
    - S-06 (`oc_runipd.py:3917-3923`):
      `# `register_signal_report` site to a function whose five sites were pinned as a measured invariant`
      `# (`tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned` was deleted in`
      `# `19313eed`; no live guard currently asserts this). The loop below reloads on its own first`
    - S-07 (`oc_runipd.py:5608-5613`):
      `# which is what `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` asserted`
      `# (deleted in `19313eed`; no live guard currently asserts this).`
    - S-08 (`agy_runipd.py:93-97`):
      `# oc-to-agy coupling that backlog `cnwy8g` tracks. Same object in both hosts (`tests/test_refusal_surfacing.py``
      `# was deleted in `19313eed`; no live guard currently asserts this object-identity property).`
    - S-09 (`agy_runipd.py:580-585`):
      `# `tests/test_runner_item_dependencies.py`'s `_SHARED_NAMES` pinned this name (deleted`
      `# in `19313eed`; no live guard currently asserts this), so the copy cannot come back silently.`
    - S-10 (`agy_runipd.py:838-844` - twin of S-03):
      `# Re-adding a dependency regex here was guarded by`
      `# `tests/test_runner_item_dependencies.py` (deleted in `19313eed`; no live guard currently asserts this).`
    - S-11 (`agy_runipd.py:1936-1941`):
      `# `tests/test_rununify_record.py` was deleted in `19313eed`; no live guard currently asserts this fallback.`
    - S-12 (`agy_runipd.py:2199-2204`):
      `# `tests/test_rununify_conflicts.py` (deleted in `19313eed`; no live guard currently asserts this conflict`
      `# case) pinned it. The dead `fallback` local this body carried (initialized to None, returned at the`
    - S-13 (`agy_runipd.py:2210-2215`):
      `# satisfaction semantics exist exactly ONCE (`tests/test_runner_item_dependencies.py::test_the_implementation_is_shared_not_copied`,`
      `# whose `_SHARED_NAMES` list named both, was deleted in `19313eed`; no live guard currently asserts this).`
    - S-14 (`agy_runipd.py:2502-2508`):
      `# it out of scope. Do NOT "harden" it: `tests/test_lane_permission_posture.py` was deleted in`
      `# `19313eed`; no live guard currently asserts this default, but running without it remains`
      `# unsupported by design.`
    - S-15 (`agy_runipd.py:4063-4069`):
      `# helper so the two hosts keep registering the same subparser set (`tests/test_rununify_build_parser.py``
      `# was deleted in `19313eed`; no live guard currently asserts this), and so `aw agy run audit --help``
    - S-16 (`ipd_lint.py:1266-1270`):
      `# (`tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` was deleted in `19313eed`; no live`
      `# guard currently asserts this) required the shared rule modules to stay ignorant of the runner, and it`
    - S-17 (`runner_shutdown.py:61-65`):
      `# `tests/test_runner_shutdown.py` was deleted in `19313eed`; no live guard currently asserts this`
      `# set covers both drivers' `TERMINAL_STATES`.`
    - S-18 (`run_viewer.py:537-543`):
      `# owner's (`tests/test_runner_refork_guard.py` and the object-identity test in `tests/test_artifact_audit.py``
      `# were deleted in `19313eed`; no live guard currently asserts this object identity).`
    - S-19 (`artifact_audit.py:7-13`):
      `precedent for the failure this prevents is `render_stream` plus `tests/test_runner_refork_guard.py``
      `(deleted in `19313eed`; no live guard currently asserts this), which pinned 28 (runner, symbol) pairs`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` with the `<rev>` used, and the bare `python3 -m pytest` summary line (stated run with no added flags); for any failure, the pasted pre-existence re-run at E-01 HEAD.
  - Observed evidence:
    AST-equivalence command against E-01 HEAD `7f8bfa478`:
    ```
    AST-DIFFER []
    ```
    Bare `python3 -m pytest` run summary (run with no added flags):
    ```
    8237 passed, 4 skipped, 18 xfailed, 3 warnings in 1179.36s (0:19:39)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths through `aw commit 9rthek -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, AST check, and suite claim; never claim a result you did not run. Sibling plans `65d5zf`, `dtelfb` and `vzk1iw` edit other passages of these files; if a site here was concurrently changed in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
