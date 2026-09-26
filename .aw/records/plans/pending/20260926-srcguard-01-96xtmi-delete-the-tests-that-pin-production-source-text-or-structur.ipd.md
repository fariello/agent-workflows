# IPD: Delete the tests that pin production source text or structure, keeping a behavioral test where real behavior is at stake

- Date: 2026-09-26
- Kind: child
- Concern: THE SUITE STILL CARRIES TESTS THAT READ PRODUCTION SOURCE AND ASSERT ON ITS TEXT OR SHAPE, which the maintainer ruled out on 2026-09-26 ("I DO NOT want any tests that try to prevent text or code from changing"). Such a test is wrong in both directions, as backlog `xelvyi` measured: it goes RED on a correct tree when a docstring or comment mentions the pinned literal (the `blocking=True` guard in `tests/test_platform_lock.py`), and it stays GREEN on a broken tree whenever the literal survives in prose. Re-measured at HEAD `61ef21d8`: at least three current pins pass on DOCSTRINGS ALONE, proven by splitting each function's docstring from its code: `tests/test_check_engine_release_gate.py::...test_check_commit_invariants_composition_intact` asserts `check_status_untooled`, `check_release_gate_consistency`, `check_scope_drift` appear in `inspect.getsource(check_engine.check_commit_invariants)`, and all three appear in that function's docstring; `tests/test_orchestrator_shape_composed.py::...test_both_consumers_reach_shared_conformance_rule` asserts `orchestrator_row_conformance` in `inspect.getsource(runner_shared.enforce_orchestrator_shape_gate)`, which its docstring contains; and `tests/test_spec_edit_ack_gate.py::...test_gate_is_wired_once_before_announcement` counts `enforce_spec_edit_ack_gate(` in `inspect.getsource(runner_shared.initialize_run_core)` (code-only today, but a single docstring mention would break the `== 1`). A reproducible AST census script finds 34 test functions across 19 files reading `agent_workflows/*` source (listed in Findings).
- Scope: IN: (a) a committed-free, reproducible census (E-01; the script lives under `/tmp/`, not in the repo, and is pasted in V-01); (b) for every hit, one recorded disposition: DELETE (pure source/structure pin), REPLACE (behavior is at stake: a new test calls the code and checks its effect), or KEEP-NOT-A-PIN (the subject is not production code shape; each justified); (c) performing those deletions and replacements; (d) re-running the census to show zero unresolved hits. OUT: the `tests/test_runner_shared.py` move-fingerprint prose, `INJECTED`, `SUPERSEDED_SINCE_MOVE` and `tests/fixtures/runner_shared_premove_fingerprints.json` (EXEMPT, see Deferred); any production code change; tests that read NON-production files (specs, workflow bodies, READMEs, the test module's own file) unless the census flags them as reading `agent_workflows/*`.
- Scope-Paths: tests/test_check_engine_release_gate.py, tests/test_finalize_sendback.py, tests/test_hostdedup_third_host.py, tests/test_ipd_authoring.py, tests/test_ipd_lint.py, tests/test_ipd_schema.py, tests/test_leak_sanitizer.py, tests/test_lifecycle_dirs.py, tests/test_lift_drift_scan.py, tests/test_local_leaks.py, tests/test_oc_runipd.py, tests/test_orchestrator_shape_composed.py, tests/test_orchestrator_shape_gate.py, tests/test_platform_lock.py, tests/test_project_context.py, tests/test_review_record_classifier.py, tests/test_runner_finalize_message.py, tests/test_spec_edit_ack_gate.py, tests/test_terminal_status_vocabulary.py, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: xelvyi
- Set: srcguard
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 96xtmi

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog xelvyi on the maintainer's 2026-09-26 ruling (no tests that prevent text or code from changing; item reclassified chore, no release gate). Census re-derived at HEAD 61ef21d8 with an AST script: 34 hits in 19 files; docstring-only passes proven for three pins.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Remove every test that asserts on the text or structure of production source, replacing it with a behavioral test only where a real behavior would otherwise lose coverage, so the suite stops failing on correct refactors and stops passing on prose.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: census

- [ ] E-01 RE-DERIVE THE CENSUS with a reproducible script written to `/tmp/srcguard/census.py` (NOT committed). It walks `tests/test_*.py` with `ast`, and for every function (including methods and module helpers) reports a hit when the function (i) calls `inspect.getsource`/`getsourcelines`, or (ii) calls `read_text`/`read_bytes`/`open`/`glob`/`rglob`/`walk`/`ast.parse` or runs an `rg` subprocess AND its source mentions a path into the REAL package (`/ "agent_workflows"`, `"agent_workflows/..py"`, or `package_dir()`) anchored at the real checkout (`REPO_ROOT`, `__file__`, `parent.parent`, `package_dir(`), or (iii) tests existence of a named `*.py` under `Path(<module>.__file__).parent`. A subprocess `python -m agent_workflows ...` is behavior and is NOT a hit; a temp fixture root containing an `agent_workflows/` dir is NOT a hit. Paste the script and its full output (`path::Class.func<TAB>signals<TAB>line N`) and the hit count. Then separately run `rg -n "inspect\.getsource|ast\.parse\(|agent_workflows\" */|/ *\"agent_workflows\"" tests --glob '!tests/fixtures/**'` and reconcile: every rg line either maps to a census hit or is explained (a comment, a docstring, a temp-fixture path, a `-m agent_workflows` subprocess).
  - Depends on: none
  - Expected outcome: 34 hits in 19 files (the Findings table), or a reconciled delta if the tree moved.
  - Execution state: pending

- [ ] E-02 RECORD A DISPOSITION FOR EVERY HIT in this plan's Findings table (column "Disposition"), updating the authored table where E-01's census or a closer read differs, and add a row for any new hit. Rules: DELETE when the assertion is about text/shape and a behavioral test of the same behavior already exists (name it) or no user-visible behavior is at stake; REPLACE when a behavior is at stake and no existing test covers it (name the behavioral test to write); KEEP-NOT-A-PIN only when the test's subject is repository CONTENT or a property that cannot be observed by calling code (each needs a one-line justification). No disposition may be "convert to an AST check": an AST structure pin is still a structure pin under the ruling.
  - Depends on: E-01
  - Expected outcome: every census hit has exactly one disposition with a named existing test (DELETE), a named new test (REPLACE), or a justification (KEEP-NOT-A-PIN).
  - Execution state: pending

### Task group 2: replace, then delete

- [ ] E-03 WRITE THE REPLACEMENT BEHAVIORAL TESTS the table names, each placed in the same file as the pin it replaces, BEFORE deleting that pin: (R1) `check_engine.check_commit_invariants` on fixtures: a temp repo that triggers each composed rule (a staged hand-edited plan status change for `check.status-untooled`; a staged done+blocking backlog item without a preserved gate for `check.blocking-item-closed-without-gate`; for `check.scope-drift`, a live begin receipt with an out-of-scope lane change, or, if that fixture is impractical, patch the single rule function on the module with a stub returning a sentinel Drift and assert it reaches the aggregate) and asserts each finding's `rule` appears in the aggregate, plus a fixture that would trigger `check.live-bug-ungated` asserting it does NOT appear (the composition excludes it); (R2) a stdlib-only IMPORT test for `ipd_schema`, `ipd_lint`, `ipd_authoring`: in a child interpreter install a `sys.meta_path` finder that raises `ImportError` for any top-level module not in `sys.stdlib_module_names` and not `agent_workflows`, import the module, assert success (measured at authoring: all three import cleanly under that finder; `platform_lock` does NOT, because it imports `filelock`, the one declared runtime dependency); guard with `skipUnless(hasattr(sys, "stdlib_module_names"))` since `requires-python = ">=3.9"` and that attribute is 3.10+; (R3) for `tests/test_oc_runipd.py::HostIntegrateVerbTests::test_the_alias_names_the_subcommand_so_the_shim_cannot_rewrite_it`, keep its behavioral half and replace the regex-over-source half with a call proving the driver does not rewrite `integrate`: drive `oc_runipd.main(["integrate", "<id6>", ...])` (or the smallest seam of `main` that applies the implicit-start shim) with the integrate handler patched to a sentinel and assert the sentinel ran and no run started. Every other REPLACE row names its test in the same concrete way.
  - Depends on: E-02
  - Expected outcome: each replacement passes on the current tree; for each, a deliberate one-line breakage of the behavior it guards (reverted afterwards) makes it FAIL.
  - Execution state: pending

- [ ] E-04 DELETE THE PINS marked DELETE or REPLACE (the latter only after its E-03 test is green), removing each test function whole. Where a test mixes a behavioral half with a source-reading half (for example `test_both_consumers_reach_shared_conformance_rule`, whose first half calls `lint.check_orchestrator_rows`), keep the behavioral half and delete only the source-reading statements, renaming the test if its name then misdescribes it. Remove imports (`inspect`, `ast`, `re`) and module helpers (`tests/test_lifecycle_dirs.py::_find_literal_drift_sites` and its caller) left unused. Update any module or class docstring in the touched files that claims the deleted pin still guards something, so no surviving prose asserts a guard that no longer exists.
  - Depends on: E-03
  - Expected outcome: every DELETE/REPLACE hit is gone; `python3 -m pyflakes` (or `python3 -m py_compile` if pyflakes is absent) over the touched files reports no unused-import or undefined-name error introduced by the deletions.
  - Execution state: pending

- [ ] E-05 CORRECT THE xelvyi-ERA PLATFORM-LOCK GUARD's status explicitly: `tests/test_platform_lock.py::SingleOwnerTests` holds three source readers (`test_no_module_carries_a_top_level_fcntl_import`, `test_only_platform_lock_touches_the_primitive`, `test_platform_lock_has_no_posix_only_import_of_its_own`); the `blocking=True` AST guard the backlog item describes is no longer present at HEAD (`rg -n "def test_no_blocking_mode" tests/test_platform_lock.py` -> no hit). Confirm that the behavior the three protect is already pinned behaviorally by `FcntlAbsentTests` (or the class holding `test_all_affected_modules_import_without_fcntl`, `test_the_lock_still_excludes_without_fcntl`, `test_the_probe_reports_undetermined_without_the_posix_primitive`, which import every affected module with `fcntl` blocked in a child interpreter) and record that as the named existing test for their DELETE disposition; paste those three tests passing.
  - Depends on: E-02
  - Expected outcome: the three `SingleOwnerTests` source readers are dispositioned DELETE with the fcntl-blocked import tests as their behavioral coverage, and those tests pass.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-06 RE-RUN THE CENSUS after the change and paste it. The only remaining hits must be the KEEP-NOT-A-PIN rows, each already justified in the table.
  - Depends on: E-04, E-05
  - Expected outcome: the post-change census lists exactly the KEEP-NOT-A-PIN rows (expected: the two leak self-clean tests), and nothing else.
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

Summary: 34 census hits in 19 files (the census's 34 rows are F-01..F-34; F-14 counts its helper). Proposed: 24 DELETE (whole or source half), 8 REPLACE, 2 KEEP-NOT-A-PIN, plus F-35 EXEMPT and not a hit.

## Proposed changes (ordered, validatable)

1. E-01 re-derives the census reproducibly; E-02 confirms a disposition per hit.
2. E-03 writes the behavioral replacements first; E-04 deletes the pins; E-05 settles the platform-lock guard.
3. E-06 re-runs the census; E-07 runs the bare suite and records the net count.

## Deferred / out of scope (with reason)

- The `tests/test_runner_shared.py` move-verification mechanism (`INJECTED`, `SUPERSEDED_SINCE_MOVE`, the module docstring's "FINGERPRINT EQUALITY" description) and `tests/fixtures/runner_shared_premove_fingerprints.json`.
  - Carrier-Declined: removing the move fingerprint mechanism changes pending plans' validation; needs its own ruling. Measured at authoring: nothing reads the fixture at HEAD and pending plan `0i4fkt` (E-05) already corrects the prose that calls it a live pin, so leaving it here costs nothing and avoids colliding with that plan.
- Tests reading non-production files (workflow bodies, specs, the test's own module, e.g. `tests/test_artifact_adopt.py::test_this_module_never_references_the_repository_inbox_path`).
  - Carrier-Declined: outside the census's definition (production source under `agent_workflows/`); whether prose-content tests fall under the ruling is a separate judgement the maintainer has not been asked.

## Scope check

- Over-scope: none.
- Under-scope: `tests/test_runner_shared.py` is declared only because E-04 may need to touch a docstring there if a deleted test is cited by it; if untouched, `--scope-ack` it at finalize.
- Scope-Paths justification: every file holding a census hit, plus `tests/test_runner_shared.py` as above. No production file is declared, and none should change.

## Required tests / validation

- The census before (E-01) and after (E-06), pasted.
- Each REPLACE test passing on the tree and FAILING against a deliberate, reverted breakage of the behavior it guards (E-03).
- Bare `python3 -m pytest` before and after, plus the collected-count delta (E-07).

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
  - Required evidence: paste the census script, its full output with the hit count and HEAD hash, and the `rg` reconciliation (each rg line mapped or explained).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the final Findings table with a disposition on every row, and a diff against the authored table if any row changed.
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
  - Required evidence: paste the post-change census output; every remaining row must be a KEEP-NOT-A-PIN row from the table.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the bare `python3 -m pytest` summary BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), and the collected-count before and after with the arithmetic against the table.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Deleting about two dozen tests that read production source and assert on its text or shape, per your 2026-09-26 ruling, and writing about eight behavioral tests where a real behavior would otherwise lose coverage (the pre-commit gate's composition, stdlib-only importability, the `integrate` verb not launching a run, the retry route for `failed-safely`, and the finalize retry allowlist). Two leak self-clean tests are kept because they check repository content, not code shape. The `runner_shared` move-fingerprint mechanism is left alone and flagged for a separate ruling. No production code changes. This graduates backlog `xelvyi`, which carries no release gate.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the test files in `- Scope-Paths:` only. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-03 must show each replacement FAILING against a deliberate breakage. No new test may read production source.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `xelvyi` `done` with `--evidence` citing the executed plan.
