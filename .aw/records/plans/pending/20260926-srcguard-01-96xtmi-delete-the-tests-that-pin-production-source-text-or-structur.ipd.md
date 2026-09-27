# IPD: Delete the tests that pin production source text or structure, keeping a behavioral test where real behavior is at stake

- Date: 2026-09-26
- Kind: child
- Concern: THE SUITE STILL CARRIES TESTS THAT READ PRODUCTION SOURCE AND ASSERT ON ITS TEXT OR SHAPE, which the maintainer ruled out on 2026-09-26 ("I DO NOT want any tests that try to prevent text or code from changing"). Such a test is wrong in both directions, as backlog `xelvyi` measured: it goes RED on a correct tree when a docstring or comment mentions the pinned literal (the `blocking=True` guard in `tests/test_platform_lock.py`), and it stays GREEN on a broken tree whenever the literal survives in prose. Re-measured at HEAD `61ef21d8`: at least three current pins pass on DOCSTRINGS ALONE, proven by splitting each function's docstring from its code: `tests/test_check_engine_release_gate.py::...test_check_commit_invariants_composition_intact` asserts `check_status_untooled`, `check_release_gate_consistency`, `check_scope_drift` appear in `inspect.getsource(check_engine.check_commit_invariants)`, and all three appear in that function's docstring; `tests/test_orchestrator_shape_composed.py::...test_both_consumers_reach_shared_conformance_rule` asserts `orchestrator_row_conformance` in `inspect.getsource(runner_shared.enforce_orchestrator_shape_gate)`, which its docstring contains; and `tests/test_spec_edit_ack_gate.py::...test_gate_is_wired_once_before_announcement` counts `enforce_spec_edit_ack_gate(` in `inspect.getsource(runner_shared.initialize_run_core)` (code-only today, but a single docstring mention would break the `== 1`). A reproducible AST census script finds 34 test functions across 19 files reading `agent_workflows/*` source (listed in Findings). THE AUTHORED CENSUS WAS INCOMPLETE BY THREE (found in review, F-36/F-37/F-38): an independent sweep found `tests/test_isolation_per_action.py::LaunchSiteWiringStructuralTests::test_execute_item_core_does_not_read_isolate_worktree_directly` (an `inspect.getsource` count pin, in a class literally named `...StructuralTests`), `tests/test_lane_input_manifest.py::...::test_revise_lane_inputs_has_no_production_caller` (an `ast.walk` over every package module asserting a call site list is empty), and `tests/test_aw_upgrade_test.py::...::test_default_sandbox_root_is_computed_not_hardcoded` (`assertNotIn("DEFAULT_SANDBOX_ROOT = Path(", source)` over `upgrade_rehearsal.py`). All three are live and passing, all three are exactly the class of pin the ruling names, and all three sat OUTSIDE the declared `Scope-Paths`, so the authored E-06 would have reported a clean post-change census while they survived. The census DEFINITION is therefore the deliverable to fix, not just the row list.
- Scope: IN: (a) a committed-free, reproducible census (E-01; the script lives under `/tmp/`, not in the repo, and is pasted in V-01); (b) for every hit, one recorded disposition: DELETE (pure source/structure pin), REPLACE (behavior is at stake: a new test calls the code and checks its effect), or KEEP-NOT-A-PIN (the subject is not production code shape; each justified); (c) performing those deletions and replacements; (d) re-running the census to show zero unresolved hits. OUT: the `tests/test_runner_shared.py` move-fingerprint prose, `INJECTED`, `SUPERSEDED_SINCE_MOVE` and `tests/fixtures/runner_shared_premove_fingerprints.json` (EXEMPT, see Deferred); any production code change; tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`.
- Scope-Paths: tests/test_check_engine_release_gate.py, tests/test_finalize_sendback.py, tests/test_hostdedup_third_host.py, tests/test_ipd_authoring.py, tests/test_ipd_lint.py, tests/test_ipd_schema.py, tests/test_leak_sanitizer.py, tests/test_lifecycle_dirs.py, tests/test_lift_drift_scan.py, tests/test_local_leaks.py, tests/test_oc_runipd.py, tests/test_orchestrator_shape_composed.py, tests/test_orchestrator_shape_gate.py, tests/test_platform_lock.py, tests/test_project_context.py, tests/test_review_record_classifier.py, tests/test_runner_finalize_message.py, tests/test_spec_edit_ack_gate.py, tests/test_terminal_status_vocabulary.py, tests/test_runner_shared.py, tests/test_isolation_per_action.py, tests/test_lane_input_manifest.py, tests/test_aw_upgrade_test.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: xelvyi
- Set: srcguard
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 96xtmi

## Workflow history
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401..PR-408 all FIXED. Census was incomplete by three live pins that were also outside the fence, so E-06 would have reported success with all three alive; every 'already covered by X' now requires per-row sabotage per this repo's own precedent.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xelvyi on the maintainer's 2026-09-26 ruling (no tests that prevent text or code from changing; item reclassified chore, no release gate). Census re-derived at HEAD 61ef21d8 with an AST script: 34 hits in 19 files; docstring-only passes proven for three pins.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Remove every test that asserts on the text or structure of production source, replacing it with a behavioral test only where a real behavior would otherwise lose coverage, so the suite stops failing on correct refactors and stops passing on prose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: census

- [ ] E-01 RE-DERIVE THE CENSUS with a reproducible script written to `/tmp/srcguard/census.py` (NOT committed). It walks `tests/test_*.py` with `ast`, and for every function (including methods and module helpers) reports a hit when the function (i) calls `inspect.getsource`/`getsourcelines`, or (ii) calls `read_text`/`read_bytes`/`open`/`glob`/`rglob`/`walk`/`ast.parse` or runs an `rg` subprocess AND its source mentions a path into the REAL package (`/ "agent_workflows"`, `"agent_workflows/..py"`, or `package_dir()`) anchored at the real checkout (`REPO_ROOT`, `__file__`, `parent.parent`, `package_dir(`), or (iii) tests existence of a named `*.py` under `Path(<module>.__file__).parent`. A subprocess `python -m agent_workflows ...` is behavior and is NOT a hit; a temp fixture root containing an `agent_workflows/` dir is NOT a hit. Paste the script and its full output (`path::Class.func<TAB>signals<TAB>line N`) and the hit count. Then separately run `rg -n "inspect\.getsource|ast\.parse\(|agent_workflows\" */|/ *\"agent_workflows\"" tests --glob '!tests/fixtures/**'` and reconcile: every rg line either maps to a census hit or is explained (a comment, a docstring, a temp-fixture path, a `-m agent_workflows` subprocess).
  - THE AUTHORED PREDICATE MISSED THREE LIVE PINS AND MUST BE WIDENED (F-36/F-37/F-38, measured in review). Add these signals, each named because a real miss traces to it: (i) `Path(<module>.__file__).parent` used as a PACKAGE ROOT to walk (`rglob("*.py")` + `ast.parse`), not only as an existence test, which is how `tests/test_lane_input_manifest.py::test_revise_lane_inputs_has_no_production_caller` escaped; (ii) `REPO_ROOT / "agent_workflows" / "<file>.py"` with `.read_text()` followed by an `assertIn`/`assertNotIn`, which is how `tests/test_aw_upgrade_test.py::test_default_sandbox_root_is_computed_not_hardcoded` escaped; (iii) any `inspect.getsource` hit ANYWHERE in `tests/`, reported unconditionally with no path-anchoring requirement, since `getsource` on an imported production symbol is a pin by construction and the anchoring heuristic is what let `tests/test_isolation_per_action.py::test_execute_item_core_does_not_read_isolate_worktree_directly` slip. CROSS-CHECK THE WIDENED CENSUS AGAINST A SECOND, CRUDER SWEEP and reconcile every difference: `rg -n "inspect\.getsource|getsourcelines" tests --glob '!tests/fixtures/**'` must have every line either in the census or explained. A census that finds exactly the authored 34 is now a FAILED E-01, because three more are known to exist.
  - Depends on: none
  - Expected outcome: at least 37 hits (the authored 34 plus the three review findings) across at least 22 files, or a reconciled delta if the tree moved. Report what the script finds; the integers here are live counts, not the bar. If the widened predicate finds fewer than 37, the predicate is wrong and must be fixed before proceeding, since all three extra pins were verified passing in review.
  - Execution state: pending

- [ ] E-02 RECORD A DISPOSITION FOR EVERY HIT in this plan's Findings table (column "Disposition"), updating the authored table where E-01's census or a closer read differs, and add a row for any new hit. Rules: DELETE when the assertion is about text/shape and a behavioral test of the same behavior already exists (name it) or no user-visible behavior is at stake; REPLACE when a behavior is at stake and no existing test covers it (name the behavioral test to write); KEEP-NOT-A-PIN only when the test's subject is repository CONTENT or a property that cannot be observed by calling code (each needs a one-line justification). No disposition may be "convert to an AST check": an AST structure pin is still a structure pin under the ruling.
  - A NAMED EXISTING TEST IS A CLAIM, AND THIS REPOSITORY ALREADY RULED THAT SUCH CLAIMS GET SABOTAGE-PROVEN (added in review, F-39). `tests/test_lane_input_manifest.py`'s own module docstring records the precedent: a prior review (PR-801/F-5) proposed four deletions, then REINSTATED all four "after per-branch sabotage proved each is the sole guard catching its defect", and separately justified a deletion by showing that "sabotaging `SEALED_FILE_MODE` from `0o444` to `0o644` fails the kept test, confirming coverage survives". Apply that standard here, because the whole risk of this plan is deleting a guard whose named substitute does not actually catch the defect. For EVERY DELETE row whose basis names an existing behavioral test, BREAK the behavior that row claims is covered (one line, reverted immediately) and confirm the NAMED test goes red. Where the named test does NOT go red, the row is not a DELETE: promote it to REPLACE and write the test. This is cheap because the break is one line per row and it is the only thing separating "coverage survives" from "coverage was asserted". Rows whose basis is structural-with-no-behavior (for example F-23's line-count pin, F-21's regex-compile count) need no sabotage: state that there is no behavior to break, which is itself the justification for deleting them.
  - Depends on: E-01
  - Expected outcome: every census hit has exactly one disposition with a named existing test (DELETE, plus its sabotage result), a named new test (REPLACE), or a justification (KEEP-NOT-A-PIN). Any named test that fails to go red under sabotage is recorded and its row promoted to REPLACE.
  - Execution state: pending

### Task group 2: replace, then delete

- [ ] E-03 WRITE THE REPLACEMENT BEHAVIORAL TESTS the table names, each placed in the same file as the pin it replaces, BEFORE deleting that pin: (R1) `check_engine.check_commit_invariants` on fixtures: a temp repo that triggers each composed rule (a staged hand-edited plan status change for `check.status-untooled`; a staged done+blocking backlog item without a preserved gate for `check.blocking-item-closed-without-gate`; for `check.scope-drift`, a live begin receipt with an out-of-scope lane change, or, if that fixture is impractical, patch the single rule function on the module with a stub returning a sentinel Drift and assert it reaches the aggregate) and asserts each finding's `rule` appears in the aggregate, plus a fixture that would trigger `check.live-bug-ungated` asserting it does NOT appear (the composition excludes it); (R2) a stdlib-only IMPORT test for `ipd_schema`, `ipd_lint`, `ipd_authoring`: in a child interpreter install a `sys.meta_path` finder that raises `ImportError` for any top-level module not in `sys.stdlib_module_names` and not `agent_workflows`, import the module, assert success (measured at authoring: all three import cleanly under that finder; `platform_lock` does NOT, because it imports `filelock`, the one declared runtime dependency); guard with `skipUnless(hasattr(sys, "stdlib_module_names"))` since `requires-python = ">=3.9"` and that attribute is 3.10+; (R3) for `tests/test_oc_runipd.py::HostIntegrateVerbTests::test_the_alias_names_the_subcommand_so_the_shim_cannot_rewrite_it`, keep its behavioral half and replace the regex-over-source half with a call proving the driver does not rewrite `integrate`: drive `oc_runipd.main(["integrate", "<id6>", ...])` (or the smallest seam of `main` that applies the implicit-start shim) with the integrate handler patched to a sentinel and assert the sentinel ran and no run started. Every other REPLACE row names its test in the same concrete way.
  - Depends on: E-02
  - Expected outcome: each replacement passes on the current tree; for each, a deliberate one-line breakage of the behavior it guards (reverted afterwards) makes it FAIL.
  - Execution state: pending

- [ ] E-04 DELETE THE PINS marked DELETE or REPLACE (the latter only after its E-03 test is green), removing each test function whole. Where a test mixes a behavioral half with a source-reading half (for example `test_both_consumers_reach_shared_conformance_rule`, whose first half calls `lint.check_orchestrator_rows`), keep the behavioral half and delete only the source-reading statements, renaming the test if its name then misdescribes it. Remove imports (`inspect`, `ast`, `re`) and module helpers (`tests/test_lifecycle_dirs.py::_find_literal_drift_sites` and its caller) left unused. Update any module or class docstring in the touched files that claims the deleted pin still guards something, so no surviving prose asserts a guard that no longer exists.
  - THE THREE REVIEW-FOUND ROWS HAVE PARTICULAR SHAPES, so handle each as its row says rather than uniformly: F-36 deletes whole (the class `LaunchSiteWiringStructuralTests` then holds nothing, so remove the class too and its `inspect` import if now unused); F-38 deletes ONLY the `assertNotIn` over source plus the `read_text` that feeds it, KEEPING the `default_sandbox_root()` call and its two assertions, and renames the test if `_is_computed_not_hardcoded` then misdescribes it; F-37 deletes the AST scan AND adds the prose its row requires to the module docstring (spec `7ckptx` R3.4's "MUST state that it has no consumer"), because that is the obligation the deleted test was discharging and dropping it silently would leave the spec requirement unmet. Also correct `tests/test_lane_input_manifest.py`'s module docstring, which currently describes that test as the "outcome test ... verifying zero production call sites", a description that becomes false.
  - Depends on: E-03
  - Expected outcome: every DELETE/REPLACE hit is gone; F-37's prose obligation is written; `python3 -m pyflakes` (or `python3 -m py_compile` if pyflakes is absent) over the touched files reports no unused-import or undefined-name error introduced by the deletions.
  - Execution state: pending

- [ ] E-05 CORRECT THE xelvyi-ERA PLATFORM-LOCK GUARD's status explicitly: `tests/test_platform_lock.py::SingleOwnerTests` holds three source readers (`test_no_module_carries_a_top_level_fcntl_import`, `test_only_platform_lock_touches_the_primitive`, `test_platform_lock_has_no_posix_only_import_of_its_own`); the `blocking=True` AST guard the backlog item describes is no longer present at HEAD (`rg -n "def test_no_blocking_mode" tests/test_platform_lock.py` -> no hit). Confirm that the behavior the three protect is already pinned behaviorally by `FcntlAbsentTests` (or the class holding `test_all_affected_modules_import_without_fcntl`, `test_the_lock_still_excludes_without_fcntl`, `test_the_probe_reports_undetermined_without_the_posix_primitive`, which import every affected module with `fcntl` blocked in a child interpreter) and record that as the named existing test for their DELETE disposition; paste those three tests passing.
  - Depends on: E-02
  - Expected outcome: the three `SingleOwnerTests` source readers are dispositioned DELETE with the fcntl-blocked import tests as their behavioral coverage, and those tests pass.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 RE-RUN THE CENSUS after the change and paste it. The only remaining hits must be the KEEP-NOT-A-PIN rows, each already justified in the table.
  - RUN THE WIDENED PREDICATE FROM E-01, not the authored one. A post-change census run with the authored predicate proves nothing about F-36/F-37/F-38, which it could not see in the first place; that is precisely how the authored plan would have reported success with three pins alive. Additionally paste the crude cross-check (`rg -n "inspect\.getsource|getsourcelines" tests --glob '!tests/fixtures/**'`) and account for every surviving line.
  - Depends on: E-04, E-05
  - Expected outcome: the post-change census lists exactly the KEEP-NOT-A-PIN rows (expected: the two leak self-clean tests), and nothing else; the `rg` cross-check shows no surviving `inspect.getsource` in `tests/` except any line explained in the table.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE `python3 -m pytest` before and after and compare. Also record the collected-test count before and after (`python3 -m pytest --collect-only -q -o addopts="" -m "not slow" | tail -1`), so the net deletion is visible.
  - Depends on: E-06
  - Expected outcome: the after-minus-before failing node set is empty; the collected count drops by (DELETE rows) minus (new REPLACE tests), matching the table.
  - Execution state: pending

## Project conventions discovered (Step 0)

- MAINTAINER RULING 2026-09-26 (recorded on backlog `xelvyi`): no tests that pin source text or code structure; keep or add a behavioral test only where real behavior is at stake. The item was reclassified `chore` with its release gate removed, which this plan inherits (no `- Blocks-Release:`).
- Precedent for the deletion: `tests/test_run_flag_surface.py`'s module docstring recorded deleting sixteen source-text pins for this reason (that file has since been removed in the `19313eed` trim), and commit `94b00d37` recorded a shipped guard passing solely because its literal appeared in a comment.
- The behavioral tool for "only stdlib" already exists in the repo's own style: `tests/test_platform_lock.py` runs a child interpreter with an import blocked (`_BLOCK_FCNTL`, `_run_child`), which is the model for R2.
- Other pending plans already state the outcome-only rule (e.g. plan `tb6wh7`: "no test pins the paragraph's wording, a fingerprint, or 'code unchanged'"), so this plan does not change the rule, only the legacy tests that predate it.
- THE STANDARD FOR DELETING A TEST IS ALREADY SET IN THIS REPOSITORY, and it is sabotage, not assertion (added in review). `tests/test_lane_input_manifest.py`'s module docstring records that a prior review proposed four deletions and then REINSTATED all four "after per-branch sabotage proved each is the sole guard catching its defect", and justified a different deletion by showing that sabotaging `SEALED_FILE_MODE` from `0o444` to `0o644` reddens the kept test. So "covered by X" must be demonstrated per row, which is what E-02 now requires.
- BOTH CITED COMMITS AND THE DELETED FILE WERE CONFIRMED in review: `94b00d37` is "test: drop source-text pins redundant with behavioral coverage", `19313eed` is "test: trim test suite from 9,136 to under 2,000 tests", and `tests/test_run_flag_surface.py` is indeed absent at HEAD.
- Suites run BARE as `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Census at HEAD `61ef21d8` (script in E-01; `Class.` prefixes omitted where the file has one class of hits). Disposition is the author's proposal, which E-02 confirms or corrects.

| Id | Test (file::function) | Reads | Disposition | Basis |
| --- | --- | --- | --- | --- |
| F-01 | `test_check_engine_release_gate.py::test_check_commit_invariants_composition_intact` | `getsource(check_engine.check_commit_invariants)` | REPLACE (R1) | Passes on the docstring alone (all three names are in it); the composition is real behavior of the pre-commit gate. |
| F-02 | `test_finalize_sendback.py::test_substantially_complete_was_not_removed_from_the_outcome_tuple` | `getsource(render_stream.render_run_summary_table)` | DELETE | Pins a tuple literal; the rendered outcome is covered behaviorally by the sibling `test_the_refusal_is_visible_on_the_summary_itself`, which renders a real state. |
| F-03 | `test_finalize_sendback.py::test_the_summary_text_is_the_one_finalize_precheck_ACTUALLY_EMITS` | `getsource(ipd_lifecycle.finalize_precheck)` | REPLACE | Behavior at stake (the retry allowlist must match what finalize emits): drive `finalize_precheck` on a stale-receipt fixture and assert `runner_shared.finalize_refusal_is_retryable(<its message>)` is True. If `TheRetryTriggerIsAPositiveAllowlist` already has such a test, DELETE instead and name it. |
| F-04 | `test_finalize_sendback.py::test_the_decision_lives_in_the_refusal_arm_and_not_a_later_sweep` | `getsource(runner_shared.execute_item_core)` count | DELETE | Structural count; `TheRefusalArmPerformsTheSendBack._run`-based tests drive the arm and observe state. |
| F-05 | `test_finalize_sendback.py::test_both_hosts_execute_through_the_SAME_refusal_arm` | `getsource(<driver module>)` | DELETE | Structural; `test_the_send_back_symbols_are_reachable_from_both_hosts` asserts identity of the shared performers (`assertIs`), which is observable behavior. |
| F-06 | `test_finalize_sendback.py::test_the_exhausted_status_keeps_the_manual_recovery_route` | `getsource(oc_driver.run_queue)` | REPLACE | Behavior at stake: a `failed-safely` item is requeued by `--retry-incomplete` (the status set in `run_queue`'s `if retry_incomplete:` branch). Drive `run_queue` (or its smallest seam) with `retry_incomplete=True` on a state holding one `failed-safely` item and a stub executor, and assert it was re-dispatched. |
| F-07 | `test_finalize_sendback.py::test_the_in_run_status_shortcut_is_STILL_GONE` | `getsource(oc_driver.edge_satisfied)` | DELETE | Structural; the behavior is pinned by the preceding test in the same class (`dependency_status` on a `substantially-complete` dep returns `unsatisfied == ["executed:yaxr4i"]`). |
| F-08 | `test_hostdedup_third_host.py::test_third_host_needs_no_runner_module` | existence of `scripted_runipd.py` in the package dir | DELETE (the two existence asserts only) | A file-absence pin; the test's `HostLabels` assertions are behavioral and stay. |
| F-09 | `test_ipd_authoring.py::test_authoring_module_is_stdlib_only` | import regex over `ipd_authoring.py` | REPLACE (R2) | Behavior (importable with no third-party packages) is observable by importing under a blocking finder. |
| F-10 | `test_ipd_authoring.py::test_it_holds_no_duplicate_write_body` | substrings in `ipd_authoring.py` | DELETE (source half) | Its second half writes a file and checks trailing whitespace and EOF, which is behavioral and stays. |
| F-11 | `test_ipd_lint.py::test_lint_module_is_stdlib_only` | import regex | REPLACE (R2) | As F-09. |
| F-12 | `test_ipd_schema.py::test_module_is_stdlib_only` | import regex | REPLACE (R2) | As F-09. |
| F-13 | `test_leak_sanitizer.py::test_engine_source_is_self_clean` | scans `leak_sanitizer.py` with the sanitizer | KEEP-NOT-A-PIN | Subject is repository CONTENT (does the shipped file contain a leak?), checked by running the sanitizer; it does not constrain how the code is written. |
| F-14 | `test_lifecycle_dirs.py::_find_literal_drift_sites` (+ its caller `test_no_literal_lifecycle_subdir_drift`) | AST of every package module | DELETE | Structure pin ("derive from lifecycle_dirs instead"); the class's `ConsumerAgreementTests` and `tests/test_record_placement.py` pin the consumer agreement behaviorally (its own docstring says so). |
| F-15 | `test_lift_drift_scan.py::test_resolved_signature_arity_violations_match_allowlist` | AST of `runner_shared.py` via `tools/lift_drift_scan` | DELETE | A static-arity structure scan; a missing argument surfaces as a `TypeError` in the behavioral runner tests that call these paths. |
| F-16 | `test_lift_drift_scan.py::test_execute_item_core_spawn_path_stop_handlers_raise` | AST of `runner_shared.py` | DELETE | Behavior is pinned by `tests/test_liftaudit_stop_halts_run.py` (`test_oc_run_queue_stop_now_force_level4`, `test_agy_run_queue_stop_now_force_level4` and the checkpoint twins drive the queue and observe the halt). |
| F-17 | `test_local_leaks.py::test_module_source_is_self_clean` | scans `local_leaks.py` | KEEP-NOT-A-PIN | As F-13. |
| F-18 | `test_oc_runipd.py::test_no_caller_compares_a_bucket_to_a_non_terminal_member` | regex over both drivers | DELETE | Structure pin; readiness-by-status behavior is covered by the `PlanBucketRecognitionTests` siblings that call `plan_bucket`. |
| F-19 | `test_oc_runipd.py::test_the_alias_names_the_subcommand_so_the_shim_cannot_rewrite_it` | regex over `oc_runipd.py` `subcommands = {` | REPLACE (R3), keep behavioral half | The behavior (bare `integrate` is not rewritten into `start`) is real and user-visible (it would LAUNCH A RUN). |
| F-20 | `test_orchestrator_shape_composed.py::test_both_consumers_reach_shared_conformance_rule` | `getsource(enforce_orchestrator_shape_gate)` | DELETE (source half) | Passes on the docstring alone; the run-side refusal is pinned behaviorally by `tests/test_orchestrator_shape_gate.py::...test_non_conforming_run_leaves_no_run_dir_no_session_no_worktree` (`IPD-S407` raised on both hosts). The lint-side half stays. |
| F-21 | `test_orchestrator_shape_composed.py::test_no_second_row_pattern_in_agent_workflows` | AST of every package module | DELETE | Structure pin (count of regex compiles). |
| F-22 | `test_orchestrator_shape_composed.py::test_account_for_known_good_scanners_and_status_lists` | `getsource(orchestrator_row_conformance)` | DELETE (source half) | Structural; the `hasattr` asserts may stay or go with it (they are not behavior either; delete the whole test unless E-02 finds a behavioral assertion in it). |
| F-23 | `test_orchestrator_shape_composed.py::test_probe_seven_functions_exist_and_sum_to_476_lines_ast` | AST line spans of `runner_shared.py` | DELETE | A line-count pin; the purest form of "prevent code from changing". |
| F-24 | `test_orchestrator_shape_gate.py::test_oc_to_agy_import_count_did_not_increase` | AST of `agy_runipd.py` | DELETE | Import-count structure pin. |
| F-25 | `test_orchestrator_shape_gate.py::test_queued_orchestrator_targets_is_reused` | AST of `runner_shared.py` | DELETE | Structure pin. |
| F-26 | `test_orchestrator_shape_gate.py::test_siting_comment_names_both_invariants` | comment text in `runner_shared.py` | DELETE (source half) | Pins a COMMENT; its behavioral half (`DriverError` with `IPD-S407` on `--prepare-only`) stays. |
| F-27 | `test_platform_lock.py::test_no_module_carries_a_top_level_fcntl_import` | text of every package module | DELETE | E-05: the fcntl-blocked child-interpreter import tests pin the behavior. |
| F-28 | `test_platform_lock.py::test_only_platform_lock_touches_the_primitive` | text of every package module | DELETE | As F-27; single ownership is design, not observable behavior. |
| F-29 | `test_platform_lock.py::test_platform_lock_has_no_posix_only_import_of_its_own` | text of `platform_lock.py` | DELETE | As F-27 (`test_the_lock_still_excludes_without_fcntl` exercises exactly this). |
| F-30 | `test_project_context.py::test_duplicate_enum_literals_audit` | `rg` over the package | DELETE | Structure pin on where literals are written. |
| F-31 | `test_review_record_classifier.py::test_exactly_one_history_record_parts_parser_in_plan_readiness` | AST of `plan_readiness.py` | DELETE | "Exactly one parser" is structure; the classifier's behavior is pinned by the file's other tests. |
| F-32 | `test_runner_finalize_message.py::test_notice_prefix_matches_checkout_pin_source` | `getsource(checkout_pin.check_and_reexec)` | REPLACE | Behavior at stake: a real checkout-pin notice must be recognized. Produce the notice by calling `checkout_pin.check_and_reexec` in the mismatch shape (patched to capture stderr instead of re-exec), prepend it to a refusal, and assert `runner_shared.finalize_refusal_is_retryable(runner_shared.nested_aw_message(...))` still holds, extending the sibling test that already uses a hand-written `NOTICE`. |
| F-33 | `test_spec_edit_ack_gate.py::test_gate_is_wired_once_before_announcement` | `getsource(runner_shared.initialize_run_core)` count/order | DELETE | Structural; the refusal-before-work behavior is pinned by `test_unattended_without_flag_REFUSES_and_records_it` and siblings. If E-02 finds none asserts the ORDER (refusal before `announce_run_order_fn` is called), REPLACE with a test passing a recording `announce_run_order_fn` and asserting it was not called on refusal. |
| F-34 | `test_terminal_status_vocabulary.py::test_exhaustiveness_scan_over_agent_workflows` | AST string constants of every package module | DELETE | Structure pin on where tokens are written; also delete its self-test `test_exhaustiveness_guard_non_vacuous`, which exists only to prove the scanner works. |
| F-35 | `test_runner_shared.py` move-fingerprint prose, `INJECTED`, `SUPERSEDED_SINCE_MOVE`, `tests/fixtures/runner_shared_premove_fingerprints.json` | (not a census hit) | EXEMPT | See Deferred. Measured: no test reads the fixture at HEAD (the strict fingerprint test was removed in `19313eed`); what remains is a table and prose. |
| F-36 | `test_isolation_per_action.py::LaunchSiteWiringStructuralTests::test_execute_item_core_does_not_read_isolate_worktree_directly` | `getsource(runner_shared.execute_item_core).count('get("isolate_worktree"')` | DELETE | MISSED BY THE AUTHORED CENSUS (review). A pure `getsource` count pin asserting a call form is absent, in a class named `LaunchSiteWiringStructuralTests` whose docstring says "Test structural wiring". The BEHAVIOR (policy resolution per action) is covered by 12 sibling tests in the same file that call `isolation_for_action`/`resolve_isolation` and observe results, including the per-action object shape, the malformed-value fallback and the CLI-versus-policy precedence. Verified live and passing at review. |
| F-37 | `test_lane_input_manifest.py::RevisionMechanismTests::test_revise_lane_inputs_has_no_production_caller` | `ast.walk` over every module under `Path(lane_containment.__file__).parent` asserting the call-site list is empty | DELETE, WITH A PROSE OBLIGATION (see basis) | MISSED BY THE AUTHORED CENSUS (review), and the SUBTLEST ROW IN THE TABLE, so do not delete it mechanically. It is an AST structure pin over the whole package, which the ruling covers. But two things make it special. FIRST, it is the ONLY guard for spec `7ckptx` R3.4 and it was itself introduced BY A PRIOR REVIEW (PR-802) as the "outcome test" replacing a docstring pin, so deleting it reverses an earlier reviewer's remedy and that must be visible, not silent. SECOND, and what resolves it: R3.4 is WITHDRAWN, and its text says the mechanism "may still be built ... but nothing in this spec now requires a caller for it; a plan that implements it MUST state that it has no consumer rather than implying one". That obligation is DOCUMENTARY, not behavioral: there is no behavior to observe, because the requirement is the ABSENCE of a caller. So the honest disposition is DELETE the AST scan and satisfy R3.4 in PROSE, in the test module's docstring, recording that the mechanism has no production consumer and that the former scan was removed under the 2026-09-26 ruling. Do NOT write a replacement behavioral test: there is none to write, and a `hasattr` or import-only test would be theatre. |
| F-38 | `test_aw_upgrade_test.py::test_default_sandbox_root_is_computed_not_hardcoded` | `assertNotIn("DEFAULT_SANDBOX_ROOT = Path(", (REPO_ROOT / "agent_workflows" / "upgrade_rehearsal.py").read_text())` | DELETE (the source-reading assert only) | MISSED BY THE AUTHORED CENSUS (review). The `assertNotIn` over production source is a literal text pin of exactly the failing kind (reword the assignment and it passes; mention the literal in a comment and it fails). The REST of the same test is behavioral and STAYS: it calls `uat.default_sandbox_root()` and asserts the computed path's `name` and `parent.name`, which is the real property. The sibling `test_sandbox_root_env_override_is_honored` covers the override. Rename the test if "not_hardcoded" then misdescribes what it checks. |

| F-39 | plan checklist as authored (E-02 dispositions) | A DELETE row's "the behavior is already covered by X" was a CLAIM, not a measurement, on ~24 rows. | This repository already settled the standard: `tests/test_lane_input_manifest.py`'s module docstring records a prior review REINSTATING four proposed deletions "after per-branch sabotage proved each is the sole guard catching its defect", and justifying another by showing a `SEALED_FILE_MODE` sabotage reddens the kept test. E-02 now requires the same per-row sabotage before a DELETE stands. |
| F-40 | F-06's premise (`failed-safely` requeue) | The REPLACE target names a status token and a `run_queue` branch; I could not confirm from reading alone that `retry_incomplete` requeues `failed-safely` specifically rather than a broader terminal set, so the replacement's assertion may need to be shaped differently than the row implies. | Recorded as a risk for the executor to resolve at E-03 by driving the branch, not as a defect in the plan: the behavior named is real and the test is the right idea. V-03 already demands a sabotage per replacement, which will surface a mis-shaped assertion. |

Summary AS AUTHORED: 34 census hits in 19 files (F-01..F-34; F-14 counts its helper), proposed 24 DELETE (whole or source half), 8 REPLACE, 2 KEEP-NOT-A-PIN, plus F-35 EXEMPT and not a hit.

CORRECTED IN REVIEW: at least 37 hits in at least 22 files. F-36, F-37 and F-38 are live, passing pins the authored census did not see, each in a file the authored `- Scope-Paths:` did not declare, so the authored E-06 would have reported a clean census with all three still in the tree. Revised proposal: 27 DELETE (whole or partial), 8 REPLACE, 2 KEEP-NOT-A-PIN, F-35 EXEMPT, and one DELETE carrying a prose obligation in place of a replacement test (F-37). Treat 37/22 as a FLOOR that E-01 re-derives, not a target: the three were found by a differently-shaped sweep, so a fourth may exist and the widened predicate is what must find it.

## Proposed changes (ordered, validatable)

1. E-01 re-derives the census with the WIDENED predicate (it must surface F-36/F-37/F-38); E-02 confirms a disposition per hit AND sabotage-proves every DELETE row's named substitute.
2. E-03 writes the behavioral replacements first; E-04 deletes the pins (F-37 also gains its prose obligation); E-05 settles the platform-lock guard.
3. E-06 re-runs the WIDENED census plus the `rg` cross-check; E-07 runs the bare suite and records the net count, reported as a no-regression check rather than as coverage evidence.

## Deferred / out of scope (with reason)

- The `tests/test_runner_shared.py` move-verification mechanism (`INJECTED`, `SUPERSEDED_SINCE_MOVE`, the module docstring's "FINGERPRINT EQUALITY" description) and `tests/fixtures/runner_shared_premove_fingerprints.json`.
  - Carrier-Declined: removing the move fingerprint mechanism changes pending plans' validation; needs its own ruling. Measured at authoring: nothing reads the fixture at HEAD and pending plan `0i4fkt` (E-05) already corrects the prose that calls it a live pin, so leaving it here costs nothing and avoids colliding with that plan.
- Tests reading non-production files (workflow bodies, specs, the test's own module, e.g. `tests/test_artifact_adopt.py::test_this_module_never_references_the_repository_inbox_path`).
  - Carrier-Declined: outside the census's definition (production source under `agent_workflows/`); whether prose-content tests fall under the ruling is a separate judgement the maintainer has not been asked.

## Scope check

- Over-scope: none.
- Under-scope: CLOSED BY REVIEW on the count that matters. Three live pins sat outside the declared fence (F-36 `tests/test_isolation_per_action.py`, F-37 `tests/test_lane_input_manifest.py`, F-38 `tests/test_aw_upgrade_test.py`); all three are now declared. `tests/test_runner_shared.py` remains declared only because E-04 may need to touch a docstring there if a deleted test is cited by it; if untouched, `--scope-ack` it at finalize. The same applies to any declared file whose hits all turn out to be KEEP.
- Scope-Paths justification: every file holding a census hit, plus `tests/test_runner_shared.py` as above. No production file is declared, and none should change.
- THE FENCE IS A CONSEQUENCE OF THE CENSUS, WHICH IS THE REAL RISK HERE (F-36..F-38). `- Scope-Paths:` was derived from the census, so a census miss silently becomes a fence hole, and a fence hole makes the final proof (E-06) report success over a surviving pin. If the widened E-01 finds a hit in a file not listed above, ADD the file: that is the sanctioned out-of-fence edit for this plan, and it should be justified at finalize with `--scope-reason` rather than skipped to stay inside the declaration.
- WHAT THIS PLAN CANNOT BREAK, stated to size the risk honestly: it touches no production file, so no shipped behavior changes and the worst outcome is LOST COVERAGE, not a regression. That is why the defenses are all about proving coverage survives (E-02's sabotage, E-03's break-and-revert, E-07's failing-node comparison) rather than about protecting runtime behavior.

## Required tests / validation

- The census before (E-01, WIDENED per F-36..F-38) and after (E-06, run with the SAME widened predicate), pasted, plus the crude `rg` cross-check each time.
- For each DELETE row naming an existing test: the sabotage result showing that named test goes RED (E-02, F-39). A row whose named test stays green is promoted to REPLACE.
- Each REPLACE test passing on the tree and FAILING against a deliberate, reverted breakage of the behavior it guards (E-03).
- Bare `python3 -m pytest` before and after, plus the collected-count delta (E-07).
- WHAT VERIFICATION CAN AND CANNOT PROVE HERE. A green suite after deleting tests is nearly meaningless on its own: deleting a test always makes the suite pass. The load-bearing evidence is therefore the SABOTAGE pairs (a named substitute goes red without its deleted sibling) and the widened census, not the suite run. State that when reporting, and do not offer "the suite is green" as evidence that coverage survived.

## Spec / documentation sync

- N/A for specs: no spec requires any of these pins; the ruling is a test-policy decision. No `.spec.md` is in `- Scope-Paths:`.
- Docstrings in touched test files that claim a deleted pin still guards something are corrected in E-04.

## Open questions

### OQ-01: Should source-reading guards be converted to AST checks instead of deleted?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No. MAINTAINER RULING, 2026-09-26 (recorded on backlog `xelvyi`): "I DO NOT want any tests that try to prevent text or code from changing." The item now means DELETE the source-reading tests (text or AST structure pins) and keep or add a BEHAVIORAL test only where real behavior is at stake. This supersedes the item's original remedy (a), "convert to AST".

### OQ-02: Are the two leak self-clean tests pins?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No. They run the shipped sanitizer over the shipped file and fail only if the file CONTAINS a leak, which is a property of repository content that a user of the published package would observe; they do not fail when the code is restructured. Kept as KEEP-NOT-A-PIN with that justification in F-13/F-17.

### OQ-03: Does deleting the platform-lock single-owner guards drop coverage of the backlog item's original incident?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: No. The `blocking=True` guard the item describes is not present at HEAD (`rg -n "def test_no_blocking_mode" tests/test_platform_lock.py` -> no hit); the remaining three single-owner readers protect "the package imports and locks without fcntl", which the fcntl-blocked child-interpreter tests in the same file already exercise (E-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the census script, its full output with the hit count and HEAD hash, and the `rg` reconciliation (each rg line mapped or explained). The script MUST be the WIDENED predicate (F-36..F-38's three signals) and its output MUST include `tests/test_isolation_per_action.py::test_execute_item_core_does_not_read_isolate_worktree_directly`, `tests/test_lane_input_manifest.py::test_revise_lane_inputs_has_no_production_caller` and `tests/test_aw_upgrade_test.py::test_default_sandbox_root_is_computed_not_hardcoded`, all three verified live and passing in review. A census output missing any of the three is a FAILED V-01 regardless of its total.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the final Findings table with a disposition on every row, and a diff against the authored table if any row changed. FOR EVERY DELETE ROW NAMING AN EXISTING TEST, paste the sabotage pair: the one-line break applied, the NAMED test failing, the break reverted (F-39). List explicitly any row whose named test did NOT go red and show it promoted to REPLACE. For a structural row with no behavior to break, say so in one line instead.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for EACH replacement test, paste it passing, then the one-line breakage applied and the test FAILING, then the breakage reverted and the test passing again.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff --stat` over the Scope-Paths, the list of deleted test node IDs, and the pyflakes (or py_compile) output over touched files.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `rg` for the absent `blocking=True` guard, and the three fcntl-blocked tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the post-change census output FROM THE WIDENED PREDICATE (the same script as V-01, not the authored one) plus the `rg -n "inspect\.getsource|getsourcelines" tests --glob '!tests/fixtures/**'` cross-check; every remaining census row and every surviving `rg` line must be a KEEP-NOT-A-PIN row or an explained line from the table. Re-running the NARROW predicate here would prove nothing about the three pins it could not see, which is exactly the hole this review closed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the collected-count before and after with the arithmetic against the table. STATE PLAINLY that the green suite is NOT the coverage evidence (deleting tests always makes a suite pass) and point at V-02's sabotage pairs and V-03's breakages as the evidence that coverage survived.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Deleting about TWENTY-SEVEN tests (24 authored plus 3 found in review) that read production source and assert on its text or shape, per your 2026-09-26 ruling, and writing about eight behavioral tests where a real behavior would otherwise lose coverage (the pre-commit gate's composition, stdlib-only importability, the `integrate` verb not launching a run, the retry route for `failed-safely`, and the finalize retry allowlist). Two leak self-clean tests are kept because they check repository content, not code shape. The `runner_shared` move-fingerprint mechanism is left alone and flagged for a separate ruling. No production code changes, so nothing shipped can regress; the only thing at risk is COVERAGE. This graduates backlog `xelvyi`, which carries no release gate.

THE REVIEW CHANGED TWO THINGS WORTH YOUR ATTENTION. FIRST, the census was incomplete: three live, passing pins sat outside it AND outside the declared fence (an `inspect.getsource` count in `test_isolation_per_action.py`, an `ast.walk` over the whole package in `test_lane_input_manifest.py`, and an `assertNotIn` over `upgrade_rehearsal.py` in `test_aw_upgrade_test.py`), so the plan's own final proof would have reported a clean sweep with all three alive. The census PREDICATE is widened and those files are now declared. SECOND, every "this is already covered by test X" was a claim rather than a measurement across roughly two dozen rows; the plan now requires the same per-row sabotage this repository already used when a prior review REINSTATED four proposed deletions after proving each was the sole guard of its defect. Both changes make the plan slower and are the difference between deleting tests safely and deleting them hopefully.

ONE ROW IS A JUDGEMENT YOU MAY WANT TO OVERRULE (F-37). `test_revise_lane_inputs_has_no_production_caller` is an AST structure pin, so the ruling covers it, but it is the sole guard for spec `7ckptx` R3.4 and it was itself written by an earlier review as the "outcome test" remedy for a docstring pin. I resolved it DELETE-plus-prose on the spec's own words: R3.4 is WITHDRAWN and says a plan implementing the mechanism "MUST state that it has no consumer rather than implying one", which is a documentary obligation with no behavior to observe. If you would rather keep a mechanical guard for a withdrawn requirement, say so; the alternative is keeping one AST pin as a deliberate exception.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the test files in `- Scope-Paths:` only. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03 must show each replacement FAILING against a deliberate breakage, and V-02 must show each DELETE row's NAMED substitute failing under sabotage. No new test may read production source.

A GREEN SUITE IS NOT EVIDENCE ON THIS PLAN, and the honesty rule bites hardest here: deleting a test always makes the suite pass, so "the suite is green after the deletions" proves only that nothing else broke. The evidence that coverage SURVIVED is the sabotage pairs. Do not report the suite result as if it settled the question.

GENUINE STOP CONDITION: if the widened census finds fewer than the three review-verified pins (F-36, F-37, F-38), the predicate is wrong; fix it before deleting anything, because a census that cannot see a pin cannot prove it was removed.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `xelvyi` `done` with `--evidence` citing the executed plan.
