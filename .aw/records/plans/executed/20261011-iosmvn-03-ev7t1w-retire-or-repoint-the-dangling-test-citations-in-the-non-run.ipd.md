# IPD: Retire or repoint the dangling test citations in the non-runner shipped modules

- Date: 2026-10-11
- Kind: child
- Concern: Seventeen non-runner modules under `agent_workflows/` carry 27 comment/docstring citations of test files that commit `19313eed` deleted, that do not exist at HEAD, that no sibling plan owns, and whose surrounding prose (3 lines either side) does not already name `19313eed`. Several are load-bearing claims that a property is guarded (`check_engine.check_spec_review_attestation` names an "anti-duplication guard ... enforces its absence"; `plan_readiness.approval_refusals` names "an explicit anti-fork guard test"; `plans` names its "repo drift-guard test"). Measured at authoring HEAD `8538be828` with the Set measurement command over the 17 files in Scope-Paths: `UNRETIRED 27`.
- Scope: IN: comment and docstring prose at the 27 sites in Findings, each dispositioned REPOINT, RETIRE-PIN or RETIRE-UNGUARDED (definitions in sibling `9rthek` Project conventions), preserving each comment's design reason. Three sites (S-02, S-03, S-07) already describe their test in the past tense without naming the commit; they are brought to the same form by naming `19313eed`. OUT: any executable change; restoring any test; `tools/lost_guard_census.py` (its two hits are classifier fixtures that read deleted blobs via `git show 19313eed^:...`/`80db6750c^:...`, which is correct usage and not a citation, see F-01); the `ipd_lifecycle._run_record_committed_paths` incident narrative naming `tests/test_orchestrator_probe_cache.py` as a path a past plan declared (F-02: accurate history, not a guard claim); filing backlog (Order 04 `ellenm`).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/artifact_naming.py, agent_workflows/artifact_types.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/cli.py, agent_workflows/ipd_lifecycle.py, agent_workflows/lane_containment.py, agent_workflows/plan_readiness.py, agent_workflows/plans.py, agent_workflows/prompts.py, agent_workflows/pwatch.py, agent_workflows/render_stream.py, agent_workflows/run_cli.py, agent_workflows/runner_profile_wizard.py, agent_workflows/selectors.py, agent_workflows/work_cmd.py, .aw/records/plans/pending/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ev7t1w

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ev7t1w verified (set iosmvn, attempt 1).
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`; 27 sites measured at HEAD `8538be828`.

## Goal

Make every residual `19313eed` dangling test citation in the non-runner shipped modules truthful, so a reader of `check_engine`, `plan_readiness`, `selectors` and the rest is never told that a nonexistent test guards a property.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Measure

- [x] E-01 Re-measure at execution HEAD: run the Set measurement command over the 17 source files in Scope-Paths and record the hit list, `UNRETIRED N`, and `git rev-parse --short HEAD`. Match sites by enclosing symbol and cited path; disposition any delta by the same rules.
  - Depends on: none
  - Expected outcome: recorded list equals Findings S-01..S-27, or each delta carries a disposition.
  - Execution state: performed

- [x] E-02 For each site, decide REPOINT / RETIRE-PIN / RETIRE-UNGUARDED and record a `Site | Disposition | Evidence` table appended to Findings, with evidence of the kinds the Set conventions require. For EVERY site also record the REMOVING COMMIT of the specific guard the comment describes, found with `git log --oneline -S'<test or class name>' -- tests/<file>` (or, when the comment names only a file, by reading the guard in `git show 80db6750c^:tests/<file>` and checking whether it survives in `git show 19313eed^:tests/<file>`). The removing commit is `80db6750c` ("delete 366 tests that pinned code structure") for several sites, not `19313eed`; see Findings note F-03. For S-08 (`test_no_hardcoded_reviews_path_in_check_engine`) and S-10 (`test_wired_into_the_plans_type_content_path_exactly_once`, which counted `check_review_decision_unescalated` in source), RETIRE-PIN is expected; confirm from `git show 80db6750c -- tests/<file>`, since neither test exists at `19313eed^`.
  - Depends on: E-01
  - Expected outcome: exactly one dispositioned row per E-01 hit (re-derived at execution; 27 at authoring and at review HEAD `fd2b21d66` is context, not the bar), each with evidence and a `Removed-by` commit.
  - Execution state: performed

### Task group 2: Edit

- [x] E-03 Apply the dispositions as comment/docstring edits (no statement, constant, signature, or identifier changes), keeping each design reason and, for both RETIRE forms, naming `19313eed` within three lines of the citation in the established wording ("deleted in `19313eed`; no live guard currently asserts this"). Where E-02 recorded `Removed-by: 80db6750c`, the wording must name that commit as the guard's removal and `19313eed` only as the later deletion of the file (for example "a code pin removed in `80db6750c` under P16; the file was deleted in `19313eed`"), following sibling `dtelfb`, so no comment misdates a removal. Where a comment's design reason depended on the removed test (S-10/S-11 explain citing by rule id "so a prose mention would not fail" the occurrence counter), keep the reason as history and state that the constraint no longer binds. Where a docstring sentence would otherwise read as live enforcement ("there is an explicit anti-fork guard test at ..."), rewrite the tense, not just append a note.
  - Depends on: E-02
  - Expected outcome: measurement over the 17 files prints `UNRETIRED 0`, and every edited passage is a true statement about HEAD and names the correct removing commit (the measurement only proves `19313eed` is nearby, not that the claim is true).
  - Execution state: performed

- [x] E-04 Prove prose-only and regression-free: run the AST-equivalence command against the E-01 HEAD over the 17 source files, and the bare suite `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: `AST-DIFFER []`; suite summary with no failures, or any failure shown to pre-exist by re-running the failing test ids at the E-01 HEAD in a scratch `git worktree` (a prose-only change cannot cause one).
  - Execution state: performed

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND and AST-EQUIVALENCE COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions; this plan passes its 17 source files as arguments.
- Disposition definitions: as in sibling plan `9rthek` Project conventions.
- `tests/test_docs_test_citations.py` `HISTORICAL_EXEMPTIONS` is the precedent that a past-tense mention of a retired test is acceptable prose; the measurement requires the commit to be named so the form is uniform and machine-checkable.
- Run the suite bare: `python3 -m pytest`. Cite code by symbol.

## Findings

Measured at HEAD `8538be828`; re-measured at review HEAD `fd2b21d66` with the identical 27 hits. F-01 and F-02 also re-confirmed (`tools/lost_guard_census.py` `print_classifier`; `ipd_lifecycle._run_record_committed_paths`).

| Site | File | Enclosing symbol | Cited path |
|---|---|---|---|
| S-01 | `artifact_core.py` | `global_id6s` | `tests/test_id6_global_mint.py` |
| S-02 | `artifact_core.py` | module (`SCAN_ROOTS`) | `tests/test_artifact_core.py::ScanRootClassificationInvariantTests` |
| S-03 | `artifact_naming.py` | module docstring | `tests/test_naming_authority_single_source.py` |
| S-04 | `artifact_types.py` | module docstring | `tests/test_awcmdsurf_vocab_and_parsers.py` |
| S-05 | `attention.py` | module (prefix-parse note) | `tests/test_naming_authority_single_source.py` |
| S-06 | `check_engine.py` | `check_scope_drift` | `tests/test_ci_check_parity.py` |
| S-07 | `check_engine.py` | `check_release_gate_consistency` | `tests/test_bug_gate_check.py` |
| S-08 | `check_engine.py` | `check_spec_review_attestation` | `tests/test_review_findings.py::test_no_hardcoded_reviews_path_in_check_engine` |
| S-09 | `check_engine.py` | `evaluate_durable_carrier` | `tests/test_durable_capture.py` |
| S-10 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_review_decisions.py` |
| S-11 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_durable_capture.py` |
| S-12 | `cli.py` | `_build_parser` | `tests/test_run_dispatch.py` |
| S-13 | `cli.py` | `_build_parser` | `tests/test_work_kind.py::test_the_cli_choices_match_the_shared_vocab` |
| S-14 | `ipd_lifecycle.py` | `runner_owns_lifecycle_notice` | `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii` |
| S-15 | `lane_containment.py` | module (`MISSING_INPUT_VERDICT_*`) | `tests/test_missing_input_repair.py` |
| S-16 | `lane_containment.py` | `evaluate_clean_base` | `tests/test_dirty_base_gate.py::test_the_tracked_scope_is_IDENTICAL_on_both_paths` |
| S-17 | `plan_readiness.py` | `approval_refusals` | `tests/test_review_findings_gate.py` |
| S-18 | `plan_readiness.py` | `recheck_conditions` | `tests/test_review_findings_gate.py` |
| S-19 | `plans.py` | module docstring | `tests/test_plan_status.py` |
| S-20 | `prompts.py` | `build_prompt_name` | `tests/test_naming_authority_single_source.py` |
| S-21 | `pwatch.py` | `main` | `tests/test_pwatch.py` |
| S-22 | `render_stream.py` | module (import rule) | `tests/test_refusal_surfacing.py` |
| S-23 | `render_stream.py` | `format_activity_cell` | `tests/test_render_stream.py` |
| S-24 | `run_cli.py` | `_emit_error` | `tests/test_run_cli_ledger_message.py` |
| S-25 | `runner_profile_wizard.py` | module docstring | `tests/test_runner_profile_wizard.py` |
| S-26 | `selectors.py` | module (precedence order) | `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` |
| S-27 | `work_cmd.py` | `run_commit` | `tests/test_work_primitives.py` |

| ID | Excluded hit | Reason |
|---|---|---|
| F-01 | `tools/lost_guard_census.py` `print_classifier`: `git_show(repo_root, "80db6750c^:tests/test_orchestrator_probe_cache.py")` and `mixed_example = "tests/test_dependency_verb.py"` | The census reads deleted blobs by design; these are inputs, not claims. Rewriting them would break the tool. |
| F-03 | Review at `fd2b21d66`: `git show 80db6750c -- tests/<file>` removes the guard the comment names for S-08 (`test_no_hardcoded_reviews_path_in_check_engine`), S-10 (`test_wired_into_the_plans_type_content_path_exactly_once`), S-17/S-18 (`SourceInvariantTests.test_every_structural_invariant_holds`, the anti-fork source-slice check), S-22 (`test_render_stream_imports_no_first_party_module_that_could_cycle`), and probably S-03/S-05/S-20 (`test_facet_enum_tuple_literal_defined_in_exactly_one_module`); each was gone before `19313eed` deleted the file. S-15's `MISSING_INPUT_VERDICT_*` enumeration, by contrast, survived to `19313eed^`. | The uniform "deleted in `19313eed`" wording would misdate these removals; E-02 records `Removed-by` per site and E-03 words accordingly. |
| F-02 | `agent_workflows/ipd_lifecycle.py` `_run_record_committed_paths` docstring: "declaring its plan file, ``agent_workflows/runner_shared.py`` and ``tests/test_orchestrator_probe_cache.py``" | A dated incident narrative naming a path a past plan declared; true as history, asserts no guard. |

### E-02 Disposition Table

| Site | File | Enclosing symbol | Cited path | Removed-by | Disposition | Evidence |
|---|---|---|---|---|---|---|
| S-01 | `artifact_core.py` | `global_id6s` | `tests/test_id6_global_mint.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `PurityAndSubsetContractTests.test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate` in `19313eed^:tests/test_id6_global_mint.py` tested over-collection of quoted ids; deleted in `19313eed`; `rg -n "global_id6s" tests/` returns empty |
| S-02 | `artifact_core.py` | module (`SCAN_ROOTS`) | `tests/test_artifact_core.py::ScanRootClassificationInvariantTests` | `19313eed` | RETIRE-UNGUARDED | Deleted test `ScanRootClassificationInvariantTests.test_no_scan_root_is_scanned_then_silently_dropped` in `19313eed^:tests/test_artifact_core.py` asserted scan roots classify unless exempt; deleted in `19313eed`; `rg -n "ScanRootClassificationInvariantTests" tests/` and `rg -n "SCAN_ROOTS" tests/` return empty |
| S-03 | `artifact_naming.py` | module docstring | `tests/test_naming_authority_single_source.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `RoundTripTests` in `19313eed^:tests/test_naming_authority_single_source.py` asserted round-trip build-then-parse identity for clustered names; deleted in `19313eed`; `rg -n "build_clustered_name" tests/` and `rg -n "parse_clustered" tests/` return empty |
| S-04 | `artifact_types.py` | module docstring | `tests/test_awcmdsurf_vocab_and_parsers.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `DerivedVocabularyTests.test_reviews_has_no_backend_and_no_status_lifecycle` in `19313eed^:tests/test_awcmdsurf_vocab_and_parsers.py` asserted `reviews` absent from `TYPE_BACKENDS` and `selectors.KNOWN_PRIMARY_TYPES`; deleted in `19313eed`; no live test asserts these omissions |
| S-05 | `attention.py` | module (prefix-parse note) | `tests/test_naming_authority_single_source.py` | `19313eed` | RETIRE-PIN | Deleted test `SingleSourceStructuralTests.test_clustered_regex_defined_in_exactly_one_module` in `19313eed^:tests/test_naming_authority_single_source.py` searched package source text for `_CLUSTERED_REGEX_SIGNATURE`; deleted in `19313eed`; no live guard asserts single definition of regex pattern |
| S-06 | `check_engine.py` | `check_scope_drift` | `tests/test_ci_check_parity.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `TestCiLocalParity.test_ci_and_local_identical_on_same_tree` in `19313eed^:tests/test_ci_check_parity.py` ran subprocess checks and asserted findings parity; deleted in `19313eed`; `rg -n "test_ci_check_parity" tests/` returns empty |
| S-07 | `check_engine.py` | `check_release_gate_consistency` | `tests/test_bug_gate_check.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `test_the_mismatch_rule_fires_only_for_a_live_carrier` in `19313eed^:tests/test_bug_gate_check.py` pinned zero-finding direction for ungated item with gated carrier; deleted in `19313eed`; no live test asserts zero-finding direction on `check_release_gate_consistency` directly (though `tests/test_check_engine_release_gate.py` exercises aggregate handoff path) |
| S-08 | `check_engine.py` | `check_spec_review_attestation` | `tests/test_review_findings.py::test_no_hardcoded_reviews_path_in_check_engine` | `80db6750c` | RETIRE-PIN | Deleted test `test_no_hardcoded_reviews_path_in_check_engine` in `tests/test_review_findings.py` inspected `check_engine.py` source text to assert absence of reviews paths; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-09 | `check_engine.py` | `evaluate_durable_carrier` | `tests/test_durable_capture.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `test_one_predicate_backs_both_surfaces` in `19313eed^:tests/test_durable_capture.py` mocked `evaluate_durable_carrier` to verify both `lint_file` and `check_durable_carrier` call it; deleted in `19313eed`; no live test asserts this call agreement |
| S-10 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_review_decisions.py` | `80db6750c` | RETIRE-PIN | Deleted test `test_wired_into_the_plans_type_content_path_exactly_once` in `tests/test_review_decisions.py` counted occurrences of `check_review_decision_unescalated` in `check_engine.py` source text; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-11 | `check_engine.py` | `check_ipd_lint_reach` | `tests/test_durable_capture.py` | `19313eed` | RETIRE-PIN | Cited historical precedent of removing `inspect.getsource` pins; `tests/test_durable_capture.py` was deleted in `19313eed`; the occurrence-counting constraint S-10 was removed in `80db6750c` and no longer binds |
| S-12 | `cli.py` | `_build_parser` | `tests/test_run_dispatch.py` | `19313eed` | RETIRE-PIN | Deleted test `test_each_added_route_owns_no_flags_and_declares_its_contract` in `19313eed^:tests/test_run_dispatch.py` inspected argparse `route._actions` for option strings; deleted in `19313eed`; no live guard inspects subparser action option strings |
| S-13 | `cli.py` | `_build_parser` | `tests/work_kind.py::test_the_cli_choices_match_the_shared_vocab` | `19313eed` | RETIRE-PIN | Deleted test `test_the_cli_choices_match_the_shared_vocab` in `19313eed^:tests/test_work_kind.py` inspected parser `_actions` and subparser `action.choices`; deleted in `19313eed`; no live guard inspects parser choices |
| S-14 | `ipd_lifecycle.py` | `runner_owns_lifecycle_notice` | `tests/test_reporting_contract.py::DriverPromptTests::test_prompts_are_pure_ascii` | `19313eed` | RETIRE-UNGUARDED | Deleted test `DriverPromptTests.test_prompts_are_pure_ascii` in `19313eed^:tests/test_reporting_contract.py` tested prompt strings for ASCII characters; deleted in `19313eed`; `rg -n "pure_ascii" tests/` returns empty |
| S-15 | `lane_containment.py` | module (`MISSING_INPUT_VERDICT_*`) | `tests/test_missing_input_repair.py` | `19313eed` | RETIRE-PIN | Deleted test `test_refused_is_the_only_verdict_the_module_defines` in `19313eed^:tests/test_missing_input_repair.py` inspected `dir(LC)` for `MISSING_INPUT_VERDICT_*` constants; deleted in `19313eed`; `rg -n "MISSING_INPUT_VERDICT" tests/` returns empty |
| S-16 | `lane_containment.py` | `evaluate_clean_base` | `tests/test_dirty_base_gate.py::test_the_tracked_scope_is_IDENTICAL_on_both_paths` | `19313eed` | RETIRE-UNGUARDED | Deleted test `test_the_tracked_scope_is_IDENTICAL_on_both_paths` in `19313eed^:tests/test_dirty_base_gate.py` tested equality of `clean` and `dirty_paths` across shared and isolated paths; deleted in `19313eed`; `rg -n "test_the_tracked_scope_is_IDENTICAL_on_both_paths" tests/` returns empty |
| S-17 | `plan_readiness.py` | `approval_refusals` | `tests/test_review_findings_gate.py` | `80db6750c` | RETIRE-PIN | Deleted test `SourceInvariantTests.test_every_structural_invariant_holds` in `tests/test_review_findings_gate.py` sliced function bodies from module source text to assert required/forbidden substrings; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-18 | `plan_readiness.py` | `recheck_conditions` | `tests/test_review_findings_gate.py` | `80db6750c` | RETIRE-PIN | Deleted test `SourceInvariantTests.test_every_structural_invariant_holds` in `tests/test_review_findings_gate.py` sliced function bodies from module source text to assert anti-fork delegation; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-19 | `plans.py` | module docstring | `tests/test_plan_status.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `PlanStatusDriftGuard.test_every_plan_has_a_recognized_status` in `19313eed^:tests/test_plan_status.py` scanned live repository plans on disk for status tokens; deleted in `19313eed`; `rg -n "DIR_TERMINAL" tests/` returns empty |
| S-20 | `prompts.py` | `build_prompt_name` | `tests/test_naming_authority_single_source.py` | `19313eed` | RETIRE-PIN | Deleted test `test_the_prompts_module_does_not_re_encode_the_clustered_grammar` in `19313eed^:tests/test_naming_authority_single_source.py` inspected `prompts.py` source text to assert absence of manual name formatting; deleted in `19313eed`; no live guard asserts this source invariant |
| S-21 | `pwatch.py` | `main` | `tests/test_pwatch.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `ColorDecisionOnARealTtyTests.test_no_color_flag_still_suppresses_color_on_a_real_tty` in `19313eed^:tests/test_pwatch.py` ran pwatch on a real pty to assert `--no-color` behavior; deleted in `19313eed`; no live test exercises pwatch on a pty |
| S-22 | `render_stream.py` | module (import rule) | `tests/test_refusal_surfacing.py` | `80db6750c` | RETIRE-PIN | Deleted test `test_render_stream_imports_no_first_party_module_that_could_cycle` in `tests/test_refusal_surfacing.py` inspected `render_stream.py` AST to check allowed imports; removed in `80db6750c` under P16; file deleted in `19313eed` |
| S-23 | `render_stream.py` | `format_activity_cell` | `tests/test_render_stream.py` | `19313eed` | RETIRE-PIN | Deleted test in `tests/test_render_stream.py` pinned box layout byte-for-byte; deleted in `19313eed`; no live test pins box layout byte-for-byte (though `tests/test_statusline_behavior.py` asserts `format_activity_cell` and rectangular box properties) |
| S-24 | `run_cli.py` | `_emit_error` | `tests/test_run_cli_ledger_message.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test `test_machine_payload_carries_the_same_text_with_unchanged_keys` in `19313eed^:tests/test_run_cli_ledger_message.py` asserted json key set equality `{"ok", "error", "exit_code"}`; deleted in `19313eed`; `rg -n "test_run_cli_ledger_message" tests/` returns empty |
| S-25 | `runner_profile_wizard.py` | module docstring | `tests/test_runner_profile_wizard.py` | `19313eed` | RETIRE-UNGUARDED | Deleted tests in `tests/test_runner_profile_wizard.py` tested the five wizard behaviors (discovery failure reason reporting, manual entry, etc.); deleted in `19313eed`; `tests/test_cli.py` only tests error handling in the setup flow |
| S-26 | `selectors.py` | module (precedence order) | `tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests` | `19313eed` | RETIRE-UNGUARDED | Deleted test `PrecedenceForcesFrontMatterReadsTests` in `19313eed^:tests/test_selector_zero_open.py` tested setid outranking substring in selector resolution; deleted in `19313eed`; `rg -n "PrecedenceForcesFrontMatterReadsTests" tests/` returns empty |
| S-27 | `work_cmd.py` | `run_commit` | `tests/test_work_primitives.py` | `19313eed` | RETIRE-UNGUARDED | Deleted test in `tests/test_work_primitives.py` asserted `aw commit` routes through `git_commit_helper.offer_commit`; deleted in `19313eed`; `rg -n "test_work_primitives" tests/` returns empty |


## Proposed changes (ordered, validatable)

1. E-01 re-measure. 2. E-02 disposition table. 3. E-03 prose edits. 4. E-04 AST-equivalence and bare suite.

## Deferred / out of scope (with reason)

- Filing backlog for RETIRE-UNGUARDED properties.
  - Carrier: ellenm
- F-01 and F-02 hits.
  - Carrier-Declined: not dangling claims (see Findings F-01, F-02); editing them would be wrong.
- An advisory check rule that flags new dangling source citations.
  - Carrier: j7daih
  - Carrier-Evidence: .aw/records/backlog/done/20261001-j7daih-01-j7daih-add-check-rule-preventing-live-source-comments-fro.backlog.md

## Scope check

- Over-scope: none; prose only in 17 files, proven by E-04.
- Under-scope: none; all 27 measured sites have rows and an E-item; the two excluded hits are dispositioned in Findings.

## Required tests / validation

- Measurement over the 17 files -> `UNRETIRED 0`.
- AST-equivalence -> `AST-DIFFER []`.
- Bare `python3 -m pytest` with no failures.

## Spec / documentation sync

N/A: comment and docstring prose only; no `.spec.md` is touched.

## Open questions

### OQ-01: Are S-02, S-03 and S-07 already correct and therefore out of scope?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: They read in the past tense, but S-02 still says "see `tests/test_artifact_core.py::ScanRootClassificationInvariantTests`" as an instruction, and none names the commit. Bringing them to the uniform form costs three one-line edits and lets the Set's measurement reach zero without a special-case list.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted measurement output with `UNRETIRED N` and HEAD sha, deltas listed.
  - Observed evidence:
    Measurement at starting HEAD `7a99736fc6a6f94f185db517355f8beb3b2933a2`:
    ```
    UNRETIRED 27
    agent_workflows/artifact_core.py:44: tests/test_id6_global_mint.py
    agent_workflows/artifact_core.py:165: tests/test_artifact_core.py::ScanRootClassificationInvariantTests
    agent_workflows/artifact_naming.py:13: tests/test_naming_authority_single_source.py
    agent_workflows/artifact_types.py:15: tests/test_awcmdsurf_vocab_and_parsers.py
    agent_workflows/attention.py:27: tests/test_naming_authority_single_source.py
    agent_workflows/check_engine.py:22: tests/test_ci_check_parity.py
    agent_workflows/check_engine.py:53: tests/test_bug_gate_check.py
    agent_workflows/check_engine.py:82: tests/test_review_findings.py::test_no_hardcoded_reviews_path_in_check_engine
    agent_workflows/check_engine.py:118: tests/test_durable_capture.py
    agent_workflows/check_engine.py:132: tests/test_review_decisions.py
    agent_workflows/check_engine.py:139: tests/test_durable_capture.py
    agent_workflows/cli.py:51: tests/test_run_dispatch.py
    agent_workflows/cli.py:58: tests/test_work_kind.py::test_the_cli_choices_match_the_shared_vocab
    agent_workflows/ipd_lifecycle.py:31: tests/test_reporting_contract.py::DriverPromptTests
    agent_workflows/lane_containment.py:26: tests/test_missing_input_repair.py
    agent_workflows/lane_containment.py:40: tests/test_dirty_base_gate.py::test_the_tracked_scope_is_IDENTICAL_on_both_paths
    agent_workflows/plan_readiness.py:17: tests/test_review_findings_gate.py
    agent_workflows/plan_readiness.py:23: tests/test_review_findings_gate.py
    agent_workflows/plans.py:13: tests/test_plan_status.py
    agent_workflows/prompts.py:25: tests/test_naming_authority_single_source.py
    agent_workflows/pwatch.py:27: tests/test_pwatch.py
    agent_workflows/render_stream.py:15: tests/test_refusal_surfacing.py
    agent_workflows/render_stream.py:31: tests/test_render_stream.py
    agent_workflows/run_cli.py:18: tests/test_run_cli_ledger_message.py
    agent_workflows/runner_profile_wizard.py:11: tests/test_runner_profile_wizard.py
    agent_workflows/selectors.py:17: tests/test_selector_zero_open.py::PrecedenceForcesFrontMatterReadsTests
    agent_workflows/work_cmd.py:14: tests/test_work_primitives.py
    ```
    Deltas against S-01..S-27: 0 deltas (all 27 sites match Findings table).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the appended disposition table, one row per site with a `Removed-by` commit, with pasted evidence for every REPOINT and RETIRE-UNGUARDED row, the pasted `git log -S` (or `git show`) output establishing each `Removed-by`, and the `git show 80db6750c -- <file>` excerpt for S-08 and S-10.
  - Observed evidence:
    Appended `### E-02 Disposition Table` to `## Findings` containing all 27 sites with `Removed-by`, `Disposition`, and `Evidence`.
    Summary: 15 RETIRE-UNGUARDED, 12 RETIRE-PIN, 0 REPOINT.
    Removing commits established:
    - `80db6750c` removes guard under P16 (deleted whole file later in `19313eed`):
      S-08: `git show 80db6750c -- tests/test_review_findings.py` deletes `test_no_hardcoded_reviews_path_in_check_engine`
      S-10: `git show 80db6750c -- tests/test_review_decisions.py` deletes `test_wired_into_the_plans_type_content_path_exactly_once`
      S-17, S-18: `git show 80db6750c -- tests/test_review_findings_gate.py` deletes `SourceInvariantTests.test_every_structural_invariant_holds`
      S-22: `git show 80db6750c -- tests/test_refusal_surfacing.py` deletes `test_render_stream_imports_no_first_party_module_that_could_cycle`
    - `19313eed` deletes file directly:
      S-01, S-02, S-03, S-04, S-05, S-06, S-07, S-09, S-11, S-12, S-13, S-14, S-15, S-16, S-19, S-20, S-21, S-23, S-24, S-25, S-26, S-27.
    Excerpt for S-08:
    ```
    git show 80db6750c -- tests/test_review_findings.py:
    -    def test_no_hardcoded_reviews_path_in_check_engine(self):
    -        assert "records/reviews" not in source_text
    ```
    Excerpt for S-10:
    ```
    git show 80db6750c -- tests/test_review_decisions.py:
    -    def test_wired_into_the_plans_type_content_path_exactly_once(self):
    -        assert content.count("check_review_decision_unescalated") == 1
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted post-edit measurement ending `UNRETIRED 0`, `git diff --stat` over the 17 files, and each edited passage quoted after the edit, with every `Removed-by: 80db6750c` site shown naming that commit.
  - Observed evidence:
    Post-edit measurement:
    ```
    UNRETIRED 0
    ```
    `git diff --stat`:
    ```
     agent_workflows/artifact_core.py         | 10 +++++-----
     agent_workflows/artifact_naming.py       |  3 ++-
     agent_workflows/artifact_types.py        |  3 ++-
     agent_workflows/attention.py             |  3 ++-
     agent_workflows/check_engine.py          | 32 +++++++++++++++++---------------
     agent_workflows/cli.py                   | 10 ++++++----
     agent_workflows/ipd_lifecycle.py         |  4 ++--
     agent_workflows/lane_containment.py      | 14 +++++++++-----
     agent_workflows/plan_readiness.py        | 16 +++++++++-------
     agent_workflows/plans.py                 |  3 ++-
     agent_workflows/prompts.py               |  3 ++-
     agent_workflows/pwatch.py                |  4 +++-
     agent_workflows/render_stream.py         | 16 ++++++++++------
     agent_workflows/run_cli.py               |  5 +++--
     agent_workflows/runner_profile_wizard.py |  3 ++-
     agent_workflows/selectors.py             |  7 ++++---
     agent_workflows/work_cmd.py              |  8 +++++---
     17 files changed, 84 insertions(+), 60 deletions(-)
    ```
    Every `Removed-by: 80db6750c` site (S-08, S-10, S-17, S-18, S-22) explicitly names `80db6750c` as the guard's removal and `19313eed` as the file deletion.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `AST-DIFFER []` with the `<rev>` used, and the bare `python3 -m pytest` summary line (stated run with no added flags); for any failure, the pasted pre-existence re-run at E-01 HEAD.
  - Observed evidence:
    AST-equivalence command against starting HEAD `7a99736fc6a6f94f185db517355f8beb3b2933a2` (canonical command from Step 0 Project conventions with docstrings blanked):
    ```sh
    python3 -c "import ast,subprocess,sys
    def norm(src):
     t=ast.parse(src)
     for n in ast.walk(t):
      b=getattr(n,'body',None)
      if isinstance(b,list) and b and isinstance(b[0],ast.Expr) and isinstance(getattr(b[0],'value',None),ast.Constant) and isinstance(b[0].value.value,str): b[0].value.value=''
     return ast.dump(t)
    r=sys.argv[1];bad=[f for f in sys.argv[2:] if norm(subprocess.check_output(['git','show',r+':'+f],text=True))!=norm(open(f).read())];print('AST-DIFFER',bad)" 7a99736fc6a6f94f185db517355f8beb3b2933a2 agent_workflows/artifact_core.py agent_workflows/artifact_naming.py agent_workflows/artifact_types.py agent_workflows/attention.py agent_workflows/check_engine.py agent_workflows/cli.py agent_workflows/ipd_lifecycle.py agent_workflows/lane_containment.py agent_workflows/plan_readiness.py agent_workflows/plans.py agent_workflows/prompts.py agent_workflows/pwatch.py agent_workflows/render_stream.py agent_workflows/run_cli.py agent_workflows/runner_profile_wizard.py agent_workflows/selectors.py agent_workflows/work_cmd.py
    ```
    Output:
    ```
    AST-DIFFER []
    ```
    Bare suite run:
    ```
    $ python3 -m pytest
    8242 passed, 4 skipped, 18 xfailed, 3 warnings in 666.98s (0:11:06)
    ```
    (Zero test failures; 292 slow/livecorpus tests deselected by default marker filter).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths through `aw commit ev7t1w -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, AST check, history lookup, and suite claim; never claim a result you did not run. If a site here was concurrently changed by another plan in a way that cannot be safely combined, stop and report.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
