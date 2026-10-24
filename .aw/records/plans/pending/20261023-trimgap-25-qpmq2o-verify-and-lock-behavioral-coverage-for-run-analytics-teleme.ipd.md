# IPD: Verify and lock behavioral coverage for run_analytics_telemetry validator and pseudonym keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `gmfupc` (Set `trimgap`, group 5 of the `wo21z5` `## Filing plan`) carries four production keys of `agent_workflows/run_analytics_telemetry.py` that the `wo21z5` budget probe classified `unguarded` under operator `return-none`: `_validate_label_list`, `_validate_tool_versions`, `node_pseudonym` and `_validate_number_map`. The probe ran at baseline HEAD `f3afece9`, where the surviving selection did not kill those mutants and only the deleted control file `tests/test_run_analytics_telemetry.py` did. That control file was restored by executed plan `8bhcd3` (commit `cbf70e39a`, 2026-10-17 19:34, NOT an ancestor of `f3afece9`), so the probe's verdict predates the restore. Re-probing at authoring HEAD `cfdb15970` (F-02) shows all four mutants are now KILLED under the routine `-m core` selection. The residual risk this plan closes is that the verdict is unrecorded: the backlog item still reads as an open gap.
- Scope: Re-run the four `wo21z5` `return-none` mutation probes against `tests/test_run_analytics_telemetry.py` under the routine `core` selection at execution HEAD, and record the verdicts in this plan. ONLY IF a probe SURVIVES at execution HEAD, add one behavioral test to `tests/test_run_analytics_telemetry.py` that calls the surviving function and asserts on its returned value or raised error. EXCLUDES any production-code change; EXCLUDES other `run_analytics_telemetry.py` keys (owned by executed `8bhcd3` or other `trimgap` items); EXCLUDES other test files.
- Scope-Paths: tests/test_run_analytics_telemetry.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: gmfupc
- Set: trimgap
- Order: 25
- Highest E allocated: 03
- Author: opencode
- Id: qpmq2o
- Approval: 2026-10-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (commit-before-reprobe, head/baseline_failing/newly_failing evidence and base sha, satisfiable budget bar, execution contract, target classes); four probes re-run killed at f1dbef8a7 (F-04)

- 2026-10-23 to-review (opencode): authored from backlog `gmfupc`. Confirmed `8bhcd3` restored the control file after the `wo21z5` baseline (`git merge-base --is-ancestor cbf70e39a f3afece925` false), then re-ran `tools/mutation_probe.py` for all four keys at HEAD `cfdb15970`; every mutant was killed (F-02). The plan is therefore verification-first with a conditional restore step, following sibling `92tzo6`.
- 2026-10-23 draft (opencode): created.

## Goal

Prove, with recorded mutation-probe output at execution HEAD, that a `return-none` mutation of each of the four `gmfupc` keys turns a routine core-tier test red, and add a behavioral test only for any key where that is not true. Done means all four keys have a pasted `verdict: killed` under `-m core`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-probe at execution HEAD

- [x] E-01 Run `python3 tools/mutation_probe.py --op return-none agent_workflows/run_analytics_telemetry.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` for each key in (`_validate_label_list`, `_validate_tool_versions`, `node_pseudonym`, `_validate_number_map`). `tools/mutation_probe.py` mutates inside its own isolated worktree (`git worktree add --detach <dir> HEAD`), so the checkout's production code is never modified; it probes committed `HEAD` only. Before the first probe, record `git rev-parse HEAD` as `<base>`. Record each `head:`, `verdict:`, `baseline_failing:`, `mutant_failing:` and `newly_failing` list in Findings. A probe with `baseline_failing` above 0 or a `verdict:` other than `killed`/`survived` (for example `error` or `invalid`) is not a result: record it, fix the cause if it is in scope, and re-run.
  - Depends on: none
  - Expected outcome: four probe outputs recorded; at authoring all four were `verdict: killed` (F-02).
  - Execution state: performed

### Task group 2: conditional restore

- [x] E-02 For every key E-01 reports `survived`, add one test to `tests/test_run_analytics_telemetry.py` in the class that already covers that function (`NodeIdentityTests` for `node_pseudonym`, called directly; `EventSchemaTests` for the private `_validate_*` validators, reached through `run_analytics_telemetry.validate_event`) and assert on the returned value or the raised validation error; mine the body from `git show 19313eed^:tests/test_run_analytics_telemetry.py` where an equivalent test exists. Commit the test file through `aw commit qpmq2o -- tests/test_run_analytics_telemetry.py` BEFORE re-running the E-01 probe for that key, because the probe sees only committed `HEAD`; then re-run it. If E-01 reported `killed` for all four keys, make NO file change and record "no survivor; no edit" in Findings.
  - Depends on: E-01
  - Expected outcome: either no diff to `tests/test_run_analytics_telemetry.py`, or a diff adding only tests, after which the re-probe of each previously surviving key (with `head:` at or after that commit) reports `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` list naming the added test.
  - Execution state: performed

- [x] E-03 Run the routine bare gate `python3 -m pytest` and confirm it passes with `tests/test_run_analytics_telemetry.py` in the core selection. The conftest budget check (`conftest.pytest_sessionfinish`) sets exit 1 on a wall-time overrun only when enforced and otherwise prints a warning; the core tier already exceeds 30s on this host before this plan (sibling `f6el0l` review measured 34.68s at `16d8abbb8`). So paste any `CORE TIER BUDGET EXCEEDED` block verbatim and do not count it against this item unless E-02 added a test that is among the block's listed slowest tests.
  - Depends on: E-02
  - Expected outcome: the bare run exits 0 and its summary line shows `passed` with no `failed` or `error`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): any test E-02 adds calls the function and asserts on outputs or raised errors; no source reading.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items. `tests/test_run_analytics_telemetry.py` carries a module-level `pytestmark = pytest.mark.core`, so every test in it is in the routine gate, and a new test added there inherits the marking.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, selection after `--`) is the same tool `wo21z5` used, so the re-probe is directly comparable to the original verdict.
- Sibling precedent: pending `92tzo6` (backlog `6ntz8v`) applies the same verify-first shape to `run_analytics_findings.py`; executed `8bhcd3` restored `tests/test_run_analytics_telemetry.py` from `19313eed^`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Budget probe results` rows for the four keys (`files`, survivor `survived`, control `killed`, `unguarded`) and the probe `head: f3afece925...`; `git log -1 cbf70e39a` (2026-10-17 19:34, `work(8bhcd3): Restore behavioral test coverage for run_analytics_telemetry`); `git merge-base --is-ancestor cbf70e39a f3afece925` returns false | The probe's surviving selection excluded the control file because it did not exist at `f3afece9`; `8bhcd3` restored it afterwards. The `unguarded` verdict describes a tree that no longer exists. |
| F-02 | `tools/mutation_probe.py --op return-none` at HEAD `cfdb15970`, selection `-o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` | `_validate_label_list`: `verdict: killed`, `mutant_failing: 2`. `_validate_tool_versions`: `killed`, `mutant_failing: 1`. `node_pseudonym`: `killed`, `mutant_failing: 7`. `_validate_number_map`: `killed`, `mutant_failing: 4`. |
| F-04 | review re-probe at HEAD `f1dbef8a7`, same four keys and selection `-o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` | All four `verdict: killed`, `baseline_failing: 0`, about 10s each: `_validate_label_list` 2 (`AcceleratorProbeTests::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path`, `EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field`); `_validate_tool_versions` 1 (`EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field`); `node_pseudonym` 7 (all `NodeIdentityTests`); `_validate_number_map` 4 (`DegradedSystemTests`, two `EventSchemaTests`, `PrivacyCorpusTests`). F-02 reproduces. |
| F-03 | Same as F-02 | `_validate_tool_versions` is killed by exactly one test, so it is the thinnest of the four; E-02 is the remedy only if that single test is lost before execution. |
| F-05 | execution re-probe at HEAD `d72505590fc73408e9bee8e86101e191e0016b59`, selection `-o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py` | All four `verdict: killed`, `baseline_failing: 0`: `_validate_label_list` 2 (`AcceleratorProbeTests::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path`, `EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field`); `_validate_tool_versions` 1 (`EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field`); `node_pseudonym` 7 (all `NodeIdentityTests`); `_validate_number_map` 4 (`DegradedSystemTests`, two `EventSchemaTests`, `PrivacyCorpusTests`). F-04 reproduces at execution HEAD. No survivor; no edit. |

## Proposed changes (ordered, validatable)

1. E-01 re-probes all four keys at execution HEAD under `-m core`.
2. E-02 adds a behavioral test only for a surviving key; otherwise no file change.
3. E-03 confirms the bare core gate passes.

## Deferred / out of scope (with reason)

- Adding redundant tests for `_validate_tool_versions` beyond the single killing test.
  - Carrier-Declined: no work is owed; one killing test meets the item's remedy ("restore behavioral coverage") and the repository's trim direction disfavors redundant tests.

## Scope check

- Over-scope: none. Only `tests/test_run_analytics_telemetry.py` is declared, and it changes only if a probe survives.
- Under-scope: none. All four backlog keys are probed by E-01 and remedied by E-02 when needed.

## Required tests / validation

- The four `tools/mutation_probe.py` runs of E-01 (and any E-02 re-probes), full `head`/`target`/`operator`/`selection`/`verdict`/`baseline_failing`/`mutant_failing`/`newly_failing` output pasted.
- `python3 -m pytest -o addopts="" -v tests/test_run_analytics_telemetry.py` passes, per-test list pasted (required only when E-02 edits the file).
- Bare `python3 -m pytest` summary line and exit status pasted.
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty (no production change committed or left in the tree).

## Spec / documentation sync

N/A: tests only (at most); no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests from `19313eed^` even though the keys are already guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. `8bhcd3` already restored `tests/test_run_analytics_telemetry.py` from `19313eed^` (F-01) and the re-probe kills every mutant (F-02); restoring again would duplicate tests. E-02 keeps a conditional remedy in case the tree changes before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the full output of all four `tools/mutation_probe.py` runs (produced by `tools/mutation_probe.py` itself, E-01), each showing `head:`, `selection:` containing `-m core tests/test_run_analytics_telemetry.py`, `baseline_failing: 0`, its `verdict:` line and its `newly_failing` list; paste `<base>` and `git diff --stat <base>..HEAD -- agent_workflows/` plus `git diff --stat -- agent_workflows/`, both showing no change.
  - Observed evidence:
    `<base>` sha:
    `d72505590fc73408e9bee8e86101e191e0016b59`

    `git diff --stat d72505590fc73408e9bee8e86101e191e0016b59..HEAD -- agent_workflows/`:
    (empty; no production files changed)

    `git diff --stat -- agent_workflows/`:
    (empty; no uncommitted production changes)

    Probe 1:
    ```text
    head: d72505590fc73408e9bee8e86101e191e0016b59
    target: agent_workflows/run_analytics_telemetry.py::_validate_label_list
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 2
    newly_failing (2 total):
      tests.test_run_analytics_telemetry.AcceleratorProbeTests::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path
      tests.test_run_analytics_telemetry.EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field
    wall_s: 16.91
    ```

    Probe 2:
    ```text
    head: d72505590fc73408e9bee8e86101e191e0016b59
    target: agent_workflows/run_analytics_telemetry.py::_validate_tool_versions
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 1
    newly_failing (1 total):
      tests.test_run_analytics_telemetry.EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field
    wall_s: 10.68
    ```

    Probe 3:
    ```text
    head: d72505590fc73408e9bee8e86101e191e0016b59
    target: agent_workflows/run_analytics_telemetry.py::node_pseudonym
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 7
    newly_failing (7 total):
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_a_different_node_yields_a_different_pseudonym
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_a_missing_salt_is_refused_rather_than_defaulted
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_identity_assembly_never_raises_even_with_every_source_broken
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_neither_the_raw_hostname_nor_the_hash_input_appears_in_the_pseudonym
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_rotating_the_salt_invalidates_correlation_by_design
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_the_raw_hostname_is_absent_from_the_produced_jsonl
      tests.test_run_analytics_telemetry.NodeIdentityTests::test_the_same_node_yields_a_stable_pseudonym
    wall_s: 11.17
    ```

    Probe 4:
    ```text
    head: d72505590fc73408e9bee8e86101e191e0016b59
    target: agent_workflows/run_analytics_telemetry.py::_validate_number_map
    operator: return-none
    selection: -o addopts= -q -p no:randomly -m core tests/test_run_analytics_telemetry.py
    verdict: killed
    baseline_failing: 0
    mutant_failing: 4
    newly_failing (4 total):
      tests.test_run_analytics_telemetry.DegradedSystemTests::test_impossible_values_are_refused_rather_than_persisted
      tests.test_run_analytics_telemetry.EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field
      tests.test_run_analytics_telemetry.EventSchemaTests::test_nested_observation_objects_have_their_own_allowlists
      tests.test_run_analytics_telemetry.PrivacyCorpusTests::test_no_forbidden_shaped_value_can_be_persisted
    wall_s: 12.85
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: either paste `git diff --stat tests/test_run_analytics_telemetry.py` showing no change together with the Findings line "no survivor; no edit", or paste the diff adding only test functions, the `aw commit` output for it, and the re-probe output with a `head:` at or after that commit showing `baseline_failing: 0` and `verdict: killed` for each previously surviving key, with a `newly_failing` list naming the added test, and `python3 -m pytest -o addopts="" -v tests/test_run_analytics_telemetry.py` with every test PASSED.
  - Observed evidence:
    `git diff --stat tests/test_run_analytics_telemetry.py`:
    (empty; no change to test file)

    Findings line:
    "no survivor; no edit" (recorded in Findings row F-05)

    `python3 -m pytest -o addopts="" -v tests/test_run_analytics_telemetry.py`:
    ```text
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=3650471417
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 67 items

    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_denied_probe_degrades_to_a_structured_reason_rather_than_raising PASSED [  1%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_timing_out_command_is_reported_not_raised PASSED [  2%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_every_command_probe_is_bounded_by_a_timeout_and_an_output_cap PASSED [  4%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_composed_resources_record_every_failure_as_a_label PASSED [  5%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_real_adapter_probes_this_machine_without_raising PASSED [  7%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_absent_procfs_yields_unavailable_not_an_exception PASSED [  8%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_malformed_procfs_yields_parse_error_with_a_byte_count_only PASSED [ 10%]
    tests/test_run_analytics_telemetry.py::ProbeAdapterTests::test_a_missing_executable_is_reported_not_raised PASSED [ 11%]
    tests/test_run_analytics_telemetry.py::NoRealIOTests::test_a_fake_adapter_run_performs_no_subprocess_no_sleep_and_no_network PASSED [ 13%]
    tests/test_run_analytics_telemetry.py::PrivacyCorpusTests::test_no_forbidden_shaped_value_can_be_persisted PASSED [ 14%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_validate_accelerators_refuses_non_list PASSED [ 16%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_real_loop_runs_and_stops PASSED [ 17%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sample_returns_none_before_start_and_after_close PASSED [ 19%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_run_skip_branch_deterministic PASSED [ 20%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_as_int_invalid_or_none_and_whitespace PASSED [ 22%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_sampler_tick_failure_terminates_thread PASSED [ 23%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_parse_accelerator_csv_blank_line_skip_and_empty PASSED [ 25%]
    tests/test_run_analytics_telemetry.py::ResidualKeyBranchTests::test_build_event_omits_none_fields PASSED [ 26%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_a_missing_salt_is_refused_rather_than_defaulted PASSED [ 28%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_raw_hostname_is_absent_from_the_produced_jsonl PASSED [ 29%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_neither_the_raw_hostname_nor_the_hash_input_appears_in_the_pseudonym PASSED [ 31%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_a_different_node_yields_a_different_pseudonym PASSED [ 32%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_rotating_the_salt_invalidates_correlation_by_design PASSED [ 34%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_same_node_yields_a_stable_pseudonym PASSED [ 35%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_sanitizer_scan_of_the_produced_telemetry_is_clean_with_a_control PASSED [ 37%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_identity_assembly_never_raises_even_with_every_source_broken PASSED [ 38%]
    tests/test_run_analytics_telemetry.py::NodeIdentityTests::test_the_sanitizer_does_not_fail_on_a_hostname_which_is_why_the_direct_check_leads PASSED [ 40%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_persisting_raw_output_would_break_this_suite PASSED [ 41%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_timeout_yields_the_timeout_code PASSED [ 43%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_malformed_output_yields_parse_error_carrying_only_a_byte_length PASSED [ 44%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_absent_tool_yields_unavailable PASSED [ 46%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_no_raw_tool_output_reaches_the_jsonl_on_any_failure_path PASSED [ 47%]
    tests/test_run_analytics_telemetry.py::AcceleratorProbeTests::test_a_well_formed_reading_parses_to_numeric_and_categorical_fields PASSED [ 49%]
    tests/test_run_analytics_telemetry.py::OverheadTests::test_per_event_cost_against_the_real_append_jsonl_is_bounded PASSED [ 50%]
    tests/test_run_analytics_telemetry.py::OverheadTests::test_sampling_cadence_cannot_exceed_the_configured_rate PASSED [ 52%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_nested_observation_objects_have_their_own_allowlists PASSED [ 53%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_free_text_is_refused_in_every_string_carrying_field PASSED [ 55%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_unknown_schema_version_is_refused_before_key_checks PASSED [ 56%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_each_event_kind_round_trips PASSED [ 58%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_full_event_with_every_payload_round_trips PASSED [ 59%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_negative_and_non_finite_numbers_are_refused PASSED [ 61%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_out_of_vocabulary_event_kind_is_refused PASSED [ 62%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_unknown_key_is_refused_and_not_silently_dropped PASSED [ 64%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_a_raw_host_identity_cannot_ride_in_through_node_id PASSED [ 65%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_build_event_validates_at_construction PASSED [ 67%]
    tests/test_run_analytics_telemetry.py::EventSchemaTests::test_missing_required_field_is_refused PASSED [ 68%]
    tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_impossible_values_are_refused_rather_than_persisted PASSED [ 70%]
    tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_each_degraded_case_completes_with_a_structured_warning PASSED [ 71%]
    tests/test_run_analytics_telemetry.py::DegradedSystemTests::test_negative_and_absurd_resource_values_do_not_break_the_stream PASSED [ 73%]
    tests/test_run_analytics_telemetry.py::SchemaMutationTests::test_dropping_instead_of_refusing_breaks_the_boundary PASSED [ 74%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_disabled_config_emits_nothing_at_all PASSED [ 76%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_an_adapter_that_raises_is_isolated_to_a_warning PASSED [ 77%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_an_unwritable_stream_records_a_warning_and_never_ends_the_run PASSED [ 79%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_allowlisted_context_fields_are_carried_and_others_are_not PASSED [ 80%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_second_close_is_a_no_op_and_emits_no_second_end PASSED [ 82%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_one_execution_yields_exactly_one_start_and_one_end PASSED [ 83%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_wall_clock_stepping_backwards_cannot_produce_a_negative_duration PASSED [ 85%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_a_second_start_emits_nothing PASSED [ 86%]
    tests/test_run_analytics_telemetry.py::CollectorLifecycleTests::test_durations_derive_from_a_monotonic_clock_and_are_never_negative PASSED [ 88%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_a_probe_slower_than_the_interval_skips_rather_than_accumulating PASSED [ 89%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_after_exit PASSED [ 91%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_an_overlapping_tick_is_skipped_and_counted_never_queued PASSED [ 92%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_the_check_interval_is_clamped_against_the_interval PASSED [ 94%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_by_a_signal_assisted_teardown PASSED [ 95%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_the_thread_is_stopped_after_an_exception_inside_the_block PASSED [ 97%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_sampling_does_not_run_when_it_is_not_enabled PASSED [ 98%]
    tests/test_run_analytics_telemetry.py::SamplerTests::test_stop_is_idempotent_and_safe_before_start PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 67 passed in 1.98s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `passed` and no `failed` or `error`, its exit status, and any `CORE TIER BUDGET EXCEEDED` block verbatim (including any "not enforced" reason).
  - Observed evidence:
    Exit status: 0
    Summary line:
    `1746 passed, 11 warnings in 84.02s (0:01:24)`

    Budget block:
    ```text
    WARNING:
    ================================ CORE TIER BUDGET EXCEEDED ================================
    Core tier wall time: 84.02s exceeded budget of 30.00s.
    Host 1-minute load average: 15.80 on 12 CPUs
    Core tier budget not enforced: host oversubscribed (1-minute load average above the CPU count)
    Top 10 slowest core tests:
       1.   8.93s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_json_is_valid
       2.   7.60s  tests/test_json_and_exitcodes.py::JsonAndExitCodesTests::test_status_human_unchanged
       3.   7.44s  tests/test_runner_shared.py::VerificationPolarityTests::test_verification_polarity_matrix_and_agreement
       4.   5.68s  tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       5.   5.38s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tiers_1_through_4_precedence
       6.   4.61s  tests/test_ipd_schema.py::DensityHeuristicTests::test_executed_conforming_corpus_low_overfire_rate
       7.   4.39s  tests/test_notify_cli.py::test_listen_lifecycle_and_answering
       8.   4.25s  tests/test_runner_shared.py::VerificationChainFrozenStateTests::test_verification_tristate_and_provenance_recording
       9.   3.63s  tests/test_local_leaks.py::ThisRepoTests::test_this_repo_working_tree_is_clean
      10.   3.18s  tests/test_status_set.py::TestScopePathCitationRewriteSetter::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan
    ===========================================================================================
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit qpmq2o -- tests/test_run_analytics_telemetry.py` (only if E-02 changed it; plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL probe and runner output into each `V-*`; never claim a mutant was killed or a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which is the expected case here when E-02 makes no edit). No production file under `agent_workflows/` may change. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize qpmq2o` itself.
