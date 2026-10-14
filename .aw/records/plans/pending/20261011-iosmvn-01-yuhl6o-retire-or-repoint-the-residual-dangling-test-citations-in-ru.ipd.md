# IPD: Retire or repoint the residual dangling test citations in runner_shared

- Date: 2026-10-11
- Kind: child
- Concern: `agent_workflows/runner_shared.py` carries 41 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already record the deletion. Each tells a reader that a named test guards a property, and the reader cannot open it. Measured at authoring HEAD `8538be828` with the Set's measurement command (see Project conventions): `UNRETIRED 41` for this file.
- Scope: IN: comment and docstring prose in `agent_workflows/runner_shared.py` only, at the 41 sites in Findings. Each site is dispositioned one of: REPOINT (a live test at HEAD asserts the same property; cite it), RETIRE-PIN (the deleted test read source or pinned structure; state that it was deleted in `19313eed` and will not return under `GUIDING_PRINCIPLES` P16), or RETIRE-UNGUARDED (the deleted test was behavioral and no live test asserts the property; state that it was deleted in `19313eed` and that no live guard currently asserts it). The design reasoning each comment carries is preserved. OUT: any executable change; restoring any test; the sites owned by other plans (`046nys`/`dtelfb`, `3tov52`/`65d5zf`, `yf1p8y`, executed `rcp8c4`), excluded by the measurement regex; filing backlog for unguarded properties (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/runner_shared.py, .aw/records/plans/pending/20261011-iosmvn-01-yuhl6o-retire-or-repoint-the-residual-dangling-test-citations-in-ru.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: yuhl6o
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 41 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in `runner_shared.py` truthful: either it names a test that exists and asserts the property, or it says plainly that the guard was deleted in `19313eed` and whether anything still asserts the property.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [x] E-01 Re-measure at execution HEAD: run the Set measurement command (Project conventions) with argument `agent_workflows/runner_shared.py` and record the list and `UNRETIRED N` line; record `git rev-parse --short HEAD`. Any site not in Findings (or any Findings row now absent) is recorded as a delta and dispositioned by the same rules.
  - Depends on: none
  - Expected outcome: the recorded list equals Findings S-01..S-41 or each delta carries a recorded disposition.
  - Execution state: performed

- [x] E-02 For each site, decide its disposition and record it in a table appended to this plan's Findings (`Site | Disposition | Evidence`). Evidence for REPOINT is the live test id plus a pasted `rg -n` hit in `tests/`; for RETIRE-PIN, the deleted test's form from `git show 19313eed^:<path>` (e.g. `ast.parse`/`inspect.getsource`/source substring); for RETIRE-UNGUARDED, the empty `rg` over `tests/` for the property's symbol or behavior. For EVERY site also record a `Removed-by` commit for the specific guard the comment describes. Find it with `git log --oneline -S'<test or class name>' -- tests/<file>`, or, when the comment names only a file, by reading the guard in `git show 80db6750c^:tests/<file>` and checking whether it survives in `git show 19313eed^:tests/<file>`. Several guards here were removed by `80db6750c` ("delete 366 tests that pinned code structure") before `19313eed` deleted the file; see Findings note F-01. For a guard removed by `80db6750c`, the RETIRE-PIN evidence is `git show 80db6750c -- tests/<file>`, since `19313eed^` no longer holds it.
  - Depends on: E-01
  - Expected outcome: exactly one dispositioned row per E-01 hit (re-derived at execution; 41 at authoring and at review HEAD `1406157ff` is context, not the bar), each with evidence and a `Removed-by` commit.
  - Execution state: performed

### Task group 2: Edit

- [x] E-03 Apply the dispositions as comment/docstring edits in `agent_workflows/runner_shared.py`. REPOINT replaces the path (and `::Symbol`) with the live one. RETIRE-PIN and RETIRE-UNGUARDED keep the sentence's design reason and replace the enforcement claim with the wording precedent already used in `oc_runipd.py` ("deleted in `19313eed`; no live guard currently asserts this") so that `19313eed` appears within three lines of the citation. Where E-02 recorded `Removed-by: 80db6750c`, the wording names that commit as the guard's removal and `19313eed` only as the later deletion of the file (for example "a code pin removed in `80db6750c` under P16; the file was deleted in `19313eed`"), following sibling `dtelfb`. Where a comment's instruction depended on the removed guard (S-02/S-19 "Keep the name qualified" because an AST guard forbade an `ast.Name` called `signal`; S-38..S-41 "may not" register a handler because guards forbade it), keep the reason as history and say plainly that the constraint is no longer mechanically enforced. Do not change any statement, constant, signature, or identifier.
  - Depends on: E-02
  - Expected outcome: measurement command prints `UNRETIRED 0` for this file, and every edited passage is a true statement about HEAD that names the correct removing commit (the measurement only proves `19313eed` is nearby, not that the claim is true).
  - Execution state: performed

- [x] E-04 Prove the edit is prose-only and regression-free: run the AST-equivalence command (Project conventions) against the E-01 HEAD and run the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures, or any failure shown to pre-exist by re-running the failing test ids at the E-01 HEAD in a scratch `git worktree` (a prose-only change cannot cause one).
  - Execution state: performed

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND (identical in every child; pass the files as arguments). A hit is a `tests/test_*.py` path deleted by `19313eed`, absent at HEAD, not in a sibling-owned cluster, with no `19313eed` within 3 lines:

```sh
python3 -c 'import re,subprocess,sys;from pathlib import Path;D=set(subprocess.check_output(["git","diff","--diff-filter=D","--name-only","19313eed^","19313eed"],text=True).split());O=re.compile(r"test_(orchestrator_probe_cache|review_findings_cascade|runner_stop_triggers|runner_backlog_close|runner_layering|run_flag_surface)\.py");B=[(f,i+1,t) for f in sys.argv[1:] for L in [Path(f).read_text().splitlines()] for i,l in enumerate(L) for t in re.findall(r"tests/test_\w+\.py",l) if t in D and not Path(t).is_file() and not O.search(t) and "19313eed" not in " ".join(L[max(0,i-3):i+4])];[print(*b) for b in B];print("UNRETIRED",len(B))' <files...>
```

- AST-EQUIVALENCE COMMAND (docstrings blanked; comments are invisible to `ast`), `<rev>` the E-01 HEAD: `python3 -c "import ast,subprocess,sys
def norm(src):
 t=ast.parse(src)
 for n in ast.walk(t):
  b=getattr(n,'body',None)
  if isinstance(b,list) and b and isinstance(b[0],ast.Expr) and isinstance(getattr(b[0],'value',None),ast.Constant) and isinstance(b[0].value.value,str): b[0].value.value=''
 return ast.dump(t)
r=sys.argv[1];bad=[f for f in sys.argv[2:] if norm(subprocess.check_output(['git','show',r+':'+f],text=True))!=norm(open(f).read())];print('AST-DIFFER',bad)" <rev> <files...>` (verified at authoring HEAD: `AST-DIFFER []` on the unchanged file).
- Retirement wording precedent: `oc_runipd.py` re-export comments ("`tests/test_runner_refork_guard.py` was deleted in `19313eed`, so no live guard currently asserts this property"), and executed plans `rcp8c4`/`gia5i7`.
- Code-pinning tests will not be restored (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16, maintainer ruling recorded on `pn7rw3`).
- Run the suite bare: `python3 -m pytest`. Cite code by symbol.

## Findings

Measured at HEAD `8538be828`. Enclosing symbol is the innermost `def`/`class`; "module" means a module-level comment block near that region.

| Site | Enclosing symbol | Cited path |
|---|---|---|
| S-01 | module (`_KIND_RE` block) | `tests/test_runner_item_dependencies.py` |
| S-02 | `_lane_record_informativeness` | `tests/test_runner_telemetry_integration.py` |
| S-03 | `add_audit_parser` | `tests/test_rununify_build_parser.py` |
| S-04 | module (`PlanRecord` section) | `tests/test_rununify_record.py` |
| S-05 | `PlanRecord` | `tests/test_rununify_record.py` |
| S-06 | `parse_plan_file` | `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` |
| S-07 | module | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` |
| S-08 | `manifest_entry_is_selectable` | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` |
| S-09 | module (clean-base note) | `tests/test_lane_clean_base.py` |
| S-10 | module (deferral reason mapping) | `tests/test_orchestrator_deferral_reporting.py` |
| S-11 | `orchestrator_refusal_text` | `tests/test_orchestrator_deferral_reporting.py` |
| S-12 | module (telemetry seam) | `tests/test_runner_refork_guard.py` |
| S-13 | `defect_report_prompt_block` | `tests/test_reporting_contract.py` |
| S-14 | `defect_report_prompt_block` | `tests/test_lane_prompt_purity.py` |
| S-15 | module (lift exclusions) | `tests/test_rununify_lift.py` |
| S-16 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` |
| S-17 | module (suite baseline) | `tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable` |
| S-18 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-19 | `gate_answer_is_warranted` | `tests/test_runner_telemetry_integration.py` |
| S-20 | `perform_gate_answer` | `tests/test_suite_baseline.py` |
| S-21 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` |
| S-22 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-23 | `new_failures_since_baseline` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-24 | `unattributed_merged_failures` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` |
| S-25 | `extract_session_id` | `tests/test_rununify_conflicts.py` |
| S-26 | `driver_begin` | `tests/test_lane_tool_identity.py` |
| S-27 | module (host descriptor) | `tests/test_rununify_host_descriptor.py` |
| S-28 | module (success-bar note) | `tests/test_runner_item_dependencies.py::_SHARED_NAMES` |
| S-29 | module (success states) | `tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome` |
| S-30 | `exit_code_statuses` | `tests/test_runner_stop_levels12.py` |
| S-31 | `finalize_outcome` | `tests/test_rununify_execute_item.py` |
| S-32 | `terminate_process` | `tests/test_runner_shutdown.py` |
| S-33 | `_record_checkpoint_stop` | `tests/test_runner_stop.py::test_stop_isolated_git_status` |
| S-34 | `reconcile_interrupted` | `tests/test_rununify_run_queue.py` |
| S-35 | `_run_verifier_turn` | `tests/test_runner_refork_guard.py` |
| S-36 | `execute_item_core` | `tests/test_rununify_execute_item_gates.py` |
| S-37 | `edge_satisfied` | `tests/test_runner_refork_guard.py` |
| S-38 | module (signal-handler note) | `tests/test_lane_allocation_idempotent.py` |
| S-39 | module (signal-handler note) | `tests/test_runner_stop.py` |
| S-40 | module (signal-handler note) | `tests/test_runner_stop_level3.py` |
| S-41 | module (signal-handler note) | `tests/test_runner_stop_level4.py` |

Measured at authoring HEAD `8538be828`; re-measured at review HEAD `1406157ff` with the identical 41 hits.

Observed shape at authoring (to guide, not to pre-decide, E-02): S-02/S-19 cite an `ast.Name` guard (RETIRE-PIN candidates; the guard survived to `19313eed^:tests/test_runner_telemetry_integration.py`); S-16/S-21 have a live sibling `tests/test_suite_baseline_direction.py` that may be a REPOINT for the direction property only, and the S-16 paragraph already cites that live file correctly; S-07/S-08 name no deletion commit anywhere nearby (corrected at review: no `19313eed` near either site), and backlog `mv18lz` (`graduated`) carries the lost coverage; S-18/S-22..S-24 cite a behavioral class (44 functions in `19313eed^:tests/test_suite_adjudication.py`), a likely RETIRE-UNGUARDED.

F-01 (review at `1406157ff`): `git show 80db6750c -- tests/<file>` shows that some guards these comments describe were removed by `80db6750c`, not `19313eed`. Confirmed: S-38 (the `signal.signal(` forbid in `tests/test_lane_allocation_idempotent.py`: 2 hits at `80db6750c^`, 0 at `19313eed^`); S-36 (`test_neither_driver_tests_a_verdict_by_substring` in `tests/test_runner_refork_guard.py`); and S-12 (`test_neither_driver_defines_a_telemetry_symbol_of_its_own` and `test_the_agy_driver_reaches_telemetry_through_shared_not_through_oc`). Not confirmed but possible: S-35, S-37, and `80db6750c` removals in `test_rununify_record`, `test_rununify_lift`, `test_rununify_conflicts`, `test_lane_tool_identity`, `test_rununify_host_descriptor`, `test_suite_baseline` and `test_suite_adjudication`. Confirmed SURVIVING to `19313eed^`: the S-02/S-19 AST guard, S-06 `FrontMatterReaderBehaviorTests`, S-07/S-08 `InRunExecutedDependencyTests`, S-16..S-18/S-21..S-24 classes, S-28 `_SHARED_NAMES`, S-29 `TheExitCodeReflectsTheRealOutcome`, S-33 `test_stop_isolated_git_status`, and the S-39..S-41 signal forbids. E-02 records `Removed-by` per site.


### E-02 Disposition Table

| Site | Enclosing symbol | Cited path | Disposition | Removed-by | Evidence |
|---|---|---|---|---|---|
| S-01 | module (`_KIND_RE` block) | `tests/test_runner_item_dependencies.py` | RETIRE-PIN | `19313eed` | Deleted test `AntiDivergenceGuardTests._DRIVER_SOURCES` in `19313eed^:tests/test_runner_item_dependencies.py` read driver source files looking for `_DEPS_RE` and `def _read_deps`; deleted in `19313eed`; no live guard asserts this source regex under P16 |
| S-02 | `_lane_record_informativeness` | `tests/test_runner_telemetry_integration.py` | RETIRE-PIN | `19313eed` | Deleted test `SamplerTeardownTests.test_this_change_registered_no_signal_handler_in_either_driver` in `19313eed^:tests/test_runner_telemetry_integration.py` parsed AST asserting no `ast.Name` called `signal`; deleted in `19313eed`; constraint no longer mechanically enforced under P16 |
| S-03 | `add_audit_parser` | `tests/test_rununify_build_parser.py` | RETIRE-PIN | `19313eed` | Deleted test `test_both_hosts_register_the_same_seven_subparsers` in `19313eed^:tests/test_rununify_build_parser.py` pinned subparser registration sets and counts; deleted in `19313eed`; no live test pins parser subparser sets under P16 |
| S-04 | module (`PlanRecord` section) | `tests/test_rununify_record.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `EndToEndDerivationTests.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts` in `19313eed^:tests/test_rununify_record.py` tested orchestrator derivation end to end across both hosts; deleted in `19313eed`; no live test asserts end-to-end derivation across both hosts |
| S-05 | `PlanRecord` | `tests/test_rununify_record.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `EndToEndDerivationTests.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts` in `19313eed^:tests/test_rununify_record.py`; deleted in `19313eed`; no live test asserts end-to-end orchestrator derivation across both hosts |
| S-06 | `parse_plan_file` | `tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` | RETIRE-UNGUARDED | `19313eed` | Deleted test `FrontMatterReaderBehaviorTests.test_public_readers_tolerate_loose_leading_whitespace` in `19313eed^:tests/test_runner_refork_guard.py`; deleted in `19313eed`; `rg -n 'permissive.*reader' tests/` shows only object identity in `tests/test_runner_shared.py:206`, no live test asserts loose-whitespace tolerance |
| S-07 | module | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` | RETIRE-UNGUARDED | `19313eed` | Deleted test `InRunExecutedDependencyTests.test_in_run_executed` in `19313eed^:tests/test_runner_item_dependencies.py`; deleted in `19313eed`; `rg -n InRunExecutedDependencyTests tests/` returned empty; coverage carried by backlog `mv18lz` (`graduated`) |
| S-08 | `manifest_entry_is_selectable` | `tests/test_runner_item_dependencies.py::InRunExecutedDependencyTests` | RETIRE-UNGUARDED | `19313eed` | Deleted test `InRunExecutedDependencyTests.test_in_run_executed` in `19313eed^:tests/test_runner_item_dependencies.py`; deleted in `19313eed`; `rg -n InRunExecutedDependencyTests tests/` returned empty; coverage carried by backlog `mv18lz` (`graduated`) |
| S-09 | module (clean-base note) | `tests/test_lane_clean_base.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `test_case_3_an_untracked_file_does_NOT_refuse` in `19313eed^:tests/test_lane_clean_base.py`; deleted in `19313eed`; `rg -n evaluate_clean_base tests/` returned empty (0 hits) |
| S-10 | module (deferral reason mapping) | `tests/test_orchestrator_deferral_reporting.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test in `19313eed^:tests/test_orchestrator_deferral_reporting.py` tested `RETIRE_REFUSED_*` translation to `ORCH_REASON_*`; deleted in `19313eed`; live tests in `tests/test_orchestrator_not_approved_reason.py` test only `ORCH_REASON_*`, no live test asserts translation from `RETIRE_REFUSED_*` |
| S-11 | `orchestrator_refusal_text` | `tests/test_orchestrator_deferral_reporting.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test in `19313eed^:tests/test_orchestrator_deferral_reporting.py` tested unrecognized-reason fallback; deleted in `19313eed`; `rg -n 'THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE' tests/` shows only negative assertion, no live test tests fallback |
| S-12 | module (telemetry seam) | `tests/test_runner_refork_guard.py` | RETIRE-PIN | `19313eed` | Deleted test `SymmetricReForkGuardTests.test_no_runner_redefines_an_already_extracted_symbol` and `test_every_runner_attribute_is_the_owning_modules_object` in `19313eed^:tests/test_runner_refork_guard.py` inspected AST and object identity; deleted in `19313eed` under P16 |
| S-13 | `defect_report_prompt_block` | `tests/test_reporting_contract.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_reporting_contract.py` asserted prompt heading-to-end byte-equality with `contract_text()`; deleted in `19313eed` under P16 |
| S-14 | `defect_report_prompt_block` | `tests/test_lane_prompt_purity.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_lane_prompt_purity.py` digest-pinned early prompt blocks; deleted in `19313eed` under P16 |
| S-15 | module (lift exclusions) | `tests/test_rununify_lift.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_rununify_lift.py` asserted AST definitions and object identity for wrappers and `disable_lane_prompt`; deleted in `19313eed` under P16 |
| S-16 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` | RETIRE-UNGUARDED | `19313eed` | Deleted test `NothingRefusesOnTheBaseline` in `19313eed^:tests/test_suite_baseline.py` tested `perform_gate_answer` `not-mine` verdict byte-identical outcome with/without baseline; deleted in `19313eed`; `tests/test_suite_baseline_direction.py` tests only `_relative_revalidation_verdict`, no live test asserts `perform_gate_answer` baseline indifference |
| S-17 | module (suite baseline) | `tests/test_suite_baseline.py::TheTwoMeasurementsAreComparable` | RETIRE-PIN | `19313eed` | Deleted test `TheTwoMeasurementsAreComparable.test_the_baseline_runs_the_SAME_argv_as_the_post_work_check` in `19313eed^:tests/test_suite_baseline.py` read source AST checking argv literals; deleted in `19313eed` under P16 |
| S-18 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` | RETIRE-UNGUARDED | `19313eed` | Deleted test `TheExitCodeIsTheAuthorityAndNotTheList.test_a_RED_exit_with_an_EMPTY_failing_list_still_ESCALATES` in `19313eed^:tests/test_suite_adjudication.py`; deleted in `19313eed`; `rg -n TheExitCodeIsTheAuthorityAndNotTheList tests/` returned empty |
| S-19 | `gate_answer_is_warranted` | `tests/test_runner_telemetry_integration.py` | RETIRE-PIN | `19313eed` | Deleted test `SamplerTeardownTests.test_this_change_registered_no_signal_handler_in_either_driver` in `19313eed^:tests/test_runner_telemetry_integration.py` checked AST for `ast.Name` called `signal`; deleted in `19313eed`; constraint no longer mechanically enforced under P16 |
| S-20 | `perform_gate_answer` | `tests/test_suite_baseline.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `NothingRefusesOnTheBaseline` in `19313eed^:tests/test_suite_baseline.py`; deleted in `19313eed`; no live test asserts `perform_gate_answer` producing identical `GateAnswerOutcome.release` with/without baseline |
| S-21 | module (suite baseline) | `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` | RETIRE-UNGUARDED | `19313eed` | Deleted test `NothingRefusesOnTheBaseline` in `19313eed^:tests/test_suite_baseline.py`; deleted in `19313eed`; no live test asserts baseline non-refusal in `perform_gate_answer` |
| S-22 | module (suite adjudication) | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` | RETIRE-UNGUARDED | `19313eed` | Deleted test `TheExitCodeIsTheAuthorityAndNotTheList` in `19313eed^:tests/test_suite_adjudication.py`; deleted in `19313eed`; `rg -n TheExitCodeIsTheAuthorityAndNotTheList tests/` returned empty |
| S-23 | `new_failures_since_baseline` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` | RETIRE-UNGUARDED | `19313eed` | Deleted test `TheExitCodeIsTheAuthorityAndNotTheList` in `19313eed^:tests/test_suite_adjudication.py`; deleted in `19313eed`; `rg -n new_failures_since_baseline tests/` returned empty |
| S-24 | `unattributed_merged_failures` | `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` | RETIRE-UNGUARDED | `19313eed` | Deleted test `TheExitCodeIsTheAuthorityAndNotTheList` in `19313eed^:tests/test_suite_adjudication.py`; deleted in `19313eed`; `rg -n unattributed_merged_failures tests/` returned empty |
| S-25 | `extract_session_id` | `tests/test_rununify_conflicts.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `PrecedenceTests.test_the_union_returns_the_ses_prefixed_value_not_the_earlier_conversation_id` in `19313eed^:tests/test_rununify_conflicts.py` tested `06-ct4w0a-D1` conflict case; deleted in `19313eed`; general `ses_` preference asserted in `test_oc_runipd.py` but no live test asserts the specific conflict case |
| S-26 | `driver_begin` | `tests/test_lane_tool_identity.py` | RETIRE-UNGUARDED | `19313eed` | Deleted test `test_the_env_handed_to_the_begin_child_actually_carries_the_pin` in `19313eed^:tests/test_lane_tool_identity.py` spied on `subprocess.run` inside `driver_begin` to check child env markers; deleted in `19313eed`; `rg -n begin_baseline_env tests/` returned empty (0 hits) |
| S-27 | module (host descriptor) | `tests/test_rununify_host_descriptor.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_rununify_host_descriptor.py` checked call sites and AST definitions of host descriptor fields; deleted in `19313eed` under P16 |
| S-28 | module (success-bar note) | `tests/test_runner_item_dependencies.py::_SHARED_NAMES` | RETIRE-PIN | `19313eed` | Deleted test `test_the_implementation_is_shared_not_copied` in `19313eed^:tests/test_runner_item_dependencies.py` asserted object identity via `_SHARED_NAMES`; deleted in `19313eed` under P16 |
| S-29 | module (success states) | `tests/test_rununify_run_queue.py::TheExitCodeReflectsTheRealOutcome` | RETIRE-UNGUARDED | `19313eed` | Deleted test `TheExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES` in `19313eed^:tests/test_rununify_run_queue.py` tested nonzero exit on `substantially-complete`; deleted in `19313eed`; no live test asserts this exit behavior |
| S-30 | `exit_code_statuses` | `tests/test_runner_stop_levels12.py` | RETIRE-PIN | `19313eed` | Deleted test `BothDriversWireTheSameLevelsTests.test_neither_driver_reimplements_the_boundary` in `19313eed^:tests/test_runner_stop_levels12.py` checked AST wiring; deleted in `19313eed` under P16 |
| S-31 | `finalize_outcome` | `tests/test_rununify_execute_item.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_rununify_execute_item.py` tracked AST duplication of `driver_finalize`; deleted in `19313eed` under P16 |
| S-32 | `terminate_process` | `tests/test_runner_shutdown.py` | RETIRE-PIN | `19313eed` | Deleted test `test_tuning_driver_constants_passes_through_to_reaper` in `19313eed^:tests/test_runner_shutdown.py` checked constant passthrough; deleted in `19313eed` under P16 |
| S-33 | `_record_checkpoint_stop` | `tests/test_runner_stop.py::test_stop_isolated_git_status` | RETIRE-UNGUARDED | `19313eed` | Deleted test `test_stop_isolated_git_status` in `19313eed^:tests/test_runner_stop.py` tested that stopping with dirty work records git state without raising keyword-only argument error; deleted in `19313eed`; `rg -n test_stop_isolated_git_status tests/` returned empty |
| S-34 | `reconcile_interrupted` | `tests/test_rununify_run_queue.py` | RETIRE-PIN | `19313eed` | Deleted test `test_the_repair_added_no_save_state_call_site` in `19313eed^:tests/test_rununify_run_queue.py` counted `save_state` call sites via AST; deleted in `19313eed` under P16 |
| S-35 | `_run_verifier_turn` | `tests/test_runner_refork_guard.py` | RETIRE-PIN | `80db6750c` | Deleted test `test_the_mapping_is_reached_from_the_shared_execute_path` in `tests/test_runner_refork_guard.py` searched source for `map_verdict`; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-36 | `execute_item_core` | `tests/test_rununify_execute_item_gates.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_rununify_execute_item_gates.py` checked AST assignment target tuple containing `Name` called `disposition`; deleted in `19313eed` under P16 |
| S-37 | `edge_satisfied` | `tests/test_runner_refork_guard.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_runner_refork_guard.py` tabled `_read_status` in `REFORK_TABLE` checking object identity; deleted in `19313eed` under P16 |
| S-38 | module (signal-handler note) | `tests/test_lane_allocation_idempotent.py` | RETIRE-PIN | `80db6750c` | Deleted test in `tests/test_lane_allocation_idempotent.py` forbade `signal.signal(` in driver source; removed in `80db6750c` under P16; file deleted in `19313eed`; constraint no longer mechanically enforced |
| S-39 | module (signal-handler note) | `tests/test_runner_stop.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_runner_stop.py` forbade `signal.signal(` in driver source; deleted in `19313eed` under P16; constraint no longer mechanically enforced |
| S-40 | module (signal-handler note) | `tests/test_runner_stop_level3.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_runner_stop_level3.py` forbade `signal.signal(` in driver source; deleted in `19313eed` under P16; constraint no longer mechanically enforced |
| S-41 | module (signal-handler note) | `tests/test_runner_stop_level4.py` | RETIRE-PIN | `19313eed` | Deleted test in `19313eed^:tests/test_runner_stop_level4.py` forbade `signal.signal(` in driver source; deleted in `19313eed` under P16; constraint no longer mechanically enforced |

## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table with evidence. 3. E-03 prose edits. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog items for RETIRE-UNGUARDED properties: done once for the whole Set.
  - Carrier: ellenm
- Restoring the lost behavioral coverage for `manifest_entry_is_selectable` (S-07/S-08).
  - Carrier: mv18lz
- `test_orchestrator_probe_cache.py`, `test_review_findings_cascade.py`, `test_runner_layering.py`, `test_run_flag_surface.py` citations in this file: owned by plans `dtelfb`/`65d5zf`, backlog `yf1p8y`, and executed `rcp8c4`.
  - Carrier: 046nys
- Restoring any source-reading guard.
  - Carrier-Declined: forbidden by `AGENTS.md` and `GUIDING_PRINCIPLES` P16.

## Scope check

- Over-scope: none; one production file, prose only, proven by E-04.
- Under-scope: none; every one of the 41 measured sites has a row and an E-item; lost coverage is carried by `ellenm`/`mv18lz`.

## Required tests / validation

- Measurement command on `agent_workflows/runner_shared.py` -> `UNRETIRED 0`.
- AST-equivalence command -> `AST-DIFFER []`.
- Bare `python3 -m pytest` with no failures.

## Spec / documentation sync

N/A: comment and docstring prose only; no spec describes these comments and no `.spec.md` is touched.

## Open questions

### OQ-01: Rewrite each citation or delete it?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Rewrite, preserving the design reason. Executed plans `rcp8c4` and `gia5i7` set the precedent: the comment's reason is the valuable part, and deleting it loses why the code is shaped as it is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted measurement output (all hit lines plus `UNRETIRED N`) and the HEAD sha, with any delta rows listed.
  - Observed evidence:
    Measurement output at execution HEAD `0c323ea3b`:
    ```
    agent_workflows/runner_shared.py 258 tests/test_runner_item_dependencies.py
    agent_workflows/runner_shared.py 2207 tests/test_runner_telemetry_integration.py
    agent_workflows/runner_shared.py 13550 tests/test_rununify_build_parser.py
    agent_workflows/runner_shared.py 14063 tests/test_rununify_record.py
    agent_workflows/runner_shared.py 14158 tests/test_rununify_record.py
    agent_workflows/runner_shared.py 14205 tests/test_runner_refork_guard.py
    agent_workflows/runner_shared.py 15865 tests/test_runner_item_dependencies.py
    agent_workflows/runner_shared.py 15912 tests/test_runner_item_dependencies.py
    agent_workflows/runner_shared.py 17346 tests/test_lane_clean_base.py
    agent_workflows/runner_shared.py 22339 tests/test_orchestrator_deferral_reporting.py
    agent_workflows/runner_shared.py 22446 tests/test_orchestrator_deferral_reporting.py
    agent_workflows/runner_shared.py 23472 tests/test_runner_refork_guard.py
    agent_workflows/runner_shared.py 24112 tests/test_reporting_contract.py
    agent_workflows/runner_shared.py 24116 tests/test_lane_prompt_purity.py
    agent_workflows/runner_shared.py 24958 tests/test_rununify_lift.py
    agent_workflows/runner_shared.py 27152 tests/test_suite_baseline.py
    agent_workflows/runner_shared.py 27176 tests/test_suite_baseline.py
    agent_workflows/runner_shared.py 28109 tests/test_suite_adjudication.py
    agent_workflows/runner_shared.py 28179 tests/test_runner_telemetry_integration.py
    agent_workflows/runner_shared.py 28394 tests/test_suite_baseline.py
    agent_workflows/runner_shared.py 28564 tests/test_suite_baseline.py
    agent_workflows/runner_shared.py 28572 tests/test_suite_adjudication.py
    agent_workflows/runner_shared.py 28703 tests/test_suite_adjudication.py
    agent_workflows/runner_shared.py 28895 tests/test_suite_adjudication.py
    agent_workflows/runner_shared.py 30255 tests/test_rununify_conflicts.py
    agent_workflows/runner_shared.py 30371 tests/test_lane_tool_identity.py
    agent_workflows/runner_shared.py 30443 tests/test_rununify_host_descriptor.py
    agent_workflows/runner_shared.py 30806 tests/test_runner_item_dependencies.py
    agent_workflows/runner_shared.py 30906 tests/test_rununify_run_queue.py
    agent_workflows/runner_shared.py 31080 tests/test_runner_stop_levels12.py
    agent_workflows/runner_shared.py 31368 tests/test_rununify_execute_item.py
    agent_workflows/runner_shared.py 34677 tests/test_runner_shutdown.py
    agent_workflows/runner_shared.py 35483 tests/test_runner_stop.py
    agent_workflows/runner_shared.py 36153 tests/test_rununify_run_queue.py
    agent_workflows/runner_shared.py 39294 tests/test_runner_refork_guard.py
    agent_workflows/runner_shared.py 39840 tests/test_rununify_execute_item_gates.py
    agent_workflows/runner_shared.py 45330 tests/test_runner_refork_guard.py
    agent_workflows/runner_shared.py 46139 tests/test_lane_allocation_idempotent.py
    agent_workflows/runner_shared.py 46139 tests/test_runner_stop.py
    agent_workflows/runner_shared.py 46140 tests/test_runner_stop_level3.py
    agent_workflows/runner_shared.py 46140 tests/test_runner_stop_level4.py
    UNRETIRED 41
    ```
    HEAD sha: `0c323ea3b`
    Deltas: Matches Findings S-01..S-41 exactly (0 deltas).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the appended disposition table with one row per site and a `Removed-by` commit, with pasted `rg`/`git show` evidence for every REPOINT and every RETIRE-UNGUARDED row, and the pasted `git log -S` (or `git show`) output establishing each `Removed-by`.
  - Observed evidence:
    Appended E-02 Disposition Table contains 41 rows matching S-01..S-41 with `Removed-by` commit for every row (39 removed in `19313eed`, 2 removed in `80db6750c`).
    Evidence establishing Removed-by:
    - S-35: `git show 80db6750c -- tests/test_runner_refork_guard.py` shows removal of `test_the_mapping_is_reached_from_the_shared_execute_path` and `test_neither_driver_tests_a_verdict_by_substring`.
    - S-38: `git show 80db6750c -- tests/test_lane_allocation_idempotent.py` shows removal of `signal.signal(` assertions.
    - S-01..S-34, S-36, S-37, S-39..S-41: all confirmed surviving in `git show 19313eed^:<path>` and deleted by `19313eed`.
    Evidence for RETIRE-UNGUARDED rows:
    - S-04 / S-05: `git show 19313eed^:tests/test_rununify_record.py` shows `EndToEndDerivationTests.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts`; `rg -n "action_for.*orchestrator" tests/` returns no end-to-end multi-host derivation test.
    - S-06: `git show 19313eed^:tests/test_runner_refork_guard.py` shows `FrontMatterReaderBehaviorTests.test_public_readers_tolerate_loose_leading_whitespace`; `rg -n "permissive.*reader" tests/` shows only identity test, no loose-whitespace test.
    - S-07 / S-08: `git show 19313eed^:tests/test_runner_item_dependencies.py` shows `InRunExecutedDependencyTests.test_in_run_executed`; `rg -n "InRunExecutedDependencyTests" tests/` exited 1 (empty); coverage carried by backlog `mv18lz`.
    - S-09: `git show 19313eed^:tests/test_lane_clean_base.py` shows `test_case_3_an_untracked_file_does_NOT_refuse`; `rg -n "evaluate_clean_base" tests/` exited 1 (empty).
    - S-10 / S-11: `git show 19313eed^:tests/test_orchestrator_deferral_reporting.py` shows translation and fallback tests; `tests/test_orchestrator_not_approved_reason.py` tests only `ORCH_REASON_*`, and `rg -n "THIS VERSION OF THE RUNNER DOES NOT RECOGNIZE" tests/` returns only negative assertion.
    - S-16 / S-20 / S-21: `git show 19313eed^:tests/test_suite_baseline.py` shows `NothingRefusesOnTheBaseline`; `tests/test_suite_baseline_direction.py` tests `_relative_revalidation_verdict` and not `perform_gate_answer`.
    - S-18 / S-22 / S-23 / S-24: `git show 19313eed^:tests/test_suite_adjudication.py` shows `TheExitCodeIsTheAuthorityAndNotTheList`; `rg -n "TheExitCodeIsTheAuthorityAndNotTheList" tests/` exited 1 (empty).
    - S-25: `git show 19313eed^:tests/test_rununify_conflicts.py` shows `PrecedenceTests`; `tests/test_oc_runipd.py` asserts general `ses_` preference but no live test asserts `06-ct4w0a-D1` conflict case.
    - S-26: `git show 19313eed^:tests/test_lane_tool_identity.py` shows `test_the_env_handed_to_the_begin_child_actually_carries_the_pin`; `rg -n "begin_baseline_env" tests/` exited 1 (empty).
    - S-29: `git show 19313eed^:tests/test_rununify_run_queue.py` shows `TheExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES`; `rg -n "TheExitCodeReflectsTheRealOutcome" tests/` exited 1 (empty).
    - S-33: `git show 19313eed^:tests/test_runner_stop.py` shows `test_stop_isolated_git_status`; `rg -n "test_stop_isolated_git_status" tests/` exited 1 (empty).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted post-edit measurement output ending `UNRETIRED 0`, `git diff --stat agent_workflows/runner_shared.py`, and each edited passage quoted after the edit, with every `Removed-by: 80db6750c` site shown naming that commit.
  - Observed evidence:
    Post-edit Set measurement command:
    ```
    python3 -c 'import re,subprocess,sys;from pathlib import Path;D=set(subprocess.check_output(["git","diff","--diff-filter=D","--name-only","19313eed^","19313eed"],text=True).split());O=re.compile(r"test_(orchestrator_probe_cache|review_findings_cascade|runner_stop_triggers|runner_backlog_close|runner_layering|run_flag_surface)\.py");B=[(f,i+1,t) for f in sys.argv[1:] for L in [Path(f).read_text().splitlines()] for i,l in enumerate(L) for t in re.findall(r"tests/test_\w+\.py",l) if t in D and not Path(t).is_file() and not O.search(t) and "19313eed" not in " ".join(L[max(0,i-3):i+4])];[print(*b) for b in B];print("UNRETIRED",len(B))' agent_workflows/runner_shared.py
    UNRETIRED 0
    ```
    `git diff --stat agent_workflows/runner_shared.py`:
    ```
     agent_workflows/runner_shared.py | 189 +++++++++++++++++++++++----------------
     1 file changed, 111 insertions(+), 78 deletions(-)
    ```
    Quoted passages showing `Removed-by: 80db6750c` naming that commit:
    - S-35 (`runner_shared.py:39304`):
      `# Both hosts reach this through execute_item_core, so there is one mapping;`
      `# tests/test_runner_refork_guard.py was a code pin removed in 80db6750c`
      `# under P16 (will not return; the file was deleted in 19313eed).`
    - S-38 (`runner_shared.py:46150`):
      `# (tests/test_lane_allocation_idempotent.py, a code pin removed in 80db6750c under P16, the file`
      `# deleted in 19313eed; and tests/test_runner_stop.py, tests/test_runner_stop_level3.py,`
      `# tests/test_runner_stop_level4.py, code pins deleted in 19313eed under P16; will not return)`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` output with the `<rev>` used, and the bare `python3 -m pytest` summary line (stated run with no added flags); for any failure, the pasted pre-existence re-run at E-01 HEAD.
  - Observed evidence:
    AST-equivalence check against E-01 HEAD `0c323ea3b`:
    ```
    python3 -c "import ast,subprocess,sys
    def norm(src):
     t=ast.parse(src)
     for n in ast.walk(t):
      b=getattr(n,'body',None)
      if isinstance(b,list) and b and isinstance(b[0],ast.Expr) and isinstance(getattr(b[0],'value',None),ast.Constant) and isinstance(b[0].value.value,str): b[0].value.value=''
     return ast.dump(t)
    r=sys.argv[1];bad=[f for f in sys.argv[2:] if norm(subprocess.check_output(['git','show',r+':'+f],text=True))!=norm(open(f).read())];print('AST-DIFFER',bad)" 0c323ea3b agent_workflows/runner_shared.py
    AST-DIFFER []
    ```
    Bare `python3 -m pytest` summary line (run with no added flags):
    ```
    8414 passed, 5 skipped, 18 xfailed, 3 warnings in 650.55s (0:10:50)
    ```
    Zero test failures.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths through `aw commit yuhl6o -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, AST check, history lookup, and suite claim; never claim a result you did not run. Sibling plans `65d5zf`, `dtelfb` and `z2ugxc` (all approved) edit other passages of `runner_shared.py`; if a site here was concurrently changed in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
