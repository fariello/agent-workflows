# IPD: Restore behavioral test coverage for run analytics wizard, report, findings, config, sources and privacy

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup groups 16 through 60 of the `b1mx2w` `## Filing plan`) carries 135 production keys that the routine non-slow selection did not reach at baseline HEAD `86f0d88d`, because the suite trim `19313eed` deleted the behavioral test files that drove them. This child owns the run-analytics slice: groups 16 (`run_analytics_wizard.py`, 10 keys), 19 (`run_analytics_report.py`, 5 keys), 21 (`run_analytics_findings.py`, 3 keys), 34 (`run_analytics_sources.py`, 2 keys), 39 (`run_analytics_config.py`, 1 key) and 50 (`run_analytics_privacy.py`, 1 key), 22 keys in all. A mutation that, for example, made `plan_deletion` return `None` or `format_findings_report` return an empty string passes the routine suite today.
- Scope: Restore six deleted test modules from `19313eed^` at their original paths, minus their code-pinning tests, with a neutral privacy canary and `core` markers, so the 22 keys are reached by the routine bare gate. The 22 keys: `run_analytics_wizard.apply_choices`, `read_settings`, `plan_deletion`, `write_settings`, `delete_analytics_artifacts`, `AnalyticsSettings.to_dict`, `_looks_like_secret`, `AnalyticsSettings.endpoint`, `_coerce_bool`, `_local_path`; `run_analytics_report._publish_flat`, `verify_bundle`, `prune_snapshots`, `publish_snapshot`, `resolve_snapshot_dir`; `run_analytics_findings.format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison`; `run_analytics_sources.inventory_corpus`, `CorpusInventory.generation_counts`; `run_analytics_config.clamp_interval`; `run_analytics_privacy.redact_text._replace`. EXCLUDES any production-code change; EXCLUDES restoring `tests/test_run_analytics_cache.py` and `tests/test_run_analytics_privacy_boundary.py` (F-05); EXCLUDES keys of other modules these files happen to reach.
- Scope-Paths: tests/test_run_analytics_wizard.py, tests/test_run_analytics_report.py, tests/test_run_analytics_findings.py, tests/test_run_analytics_config.py, tests/test_run_analytics_e2e.py, tests/test_run_analytics_privacy.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 16
- Highest E allocated: 06
- Author: opencode
- Id: ivap17

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` against HEAD `f84c3af26`, applied the proposed subset edits to scratch copies under `tests/`, and measured per-key reach (coverage contexts), per-test durations and early-return mutation kills before writing any step; scratch copies and `.coverage` were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 22 run-analytics keys of backlog `q86fxm` (groups 16, 19, 21, 34, 39, 50) reached by the routine bare core-tier run, through restored behavioral tests that build settings, publish and prune snapshots, render findings, inventory a fixture corpus and redact diagnostics, then assert on returned values, written files and raised refusals. Done means an early-return mutation of any of the 22 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Common rule for every E-item below (the RESTORE RULE): create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add the stated `core` marking; keep every other test body unchanged. If any kept test fails at execution HEAD, STOP on that test: record it in Findings, decide from `git log -S` on the asserted value whether HEAD changed the behavior on purpose (cite the commit) and update only that expectation, or, for a regression, file a `bug` backlog item with `--blocks-release next` instead of editing the test.

### Task group 1: restore the analytics modules

- [ ] E-01 Restore `tests/test_run_analytics_wizard.py`. Delete `test_no_optional_install_mechanism_is_built` and `test_deletion_never_composes_the_runs_literal_itself` (both import `tests.test_run_analytics_export._code_lines` and assert substrings of `agent_workflows/run_analytics_wizard.py` source, F-02). Add a module-level `pytestmark = pytest.mark.core` (19 tests, 0.09s summed at authoring).
  - Depends on: none
  - Expected outcome: 19 tests pass; the file contains no `_code_lines` and no `agent_workflows/` path string.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_run_analytics_report.py` unchanged except marking with `@pytest.mark.core` exactly these four tests (the cheapest set reaching all five report keys, F-03): `RefusalTests.test_a_traversing_snapshot_label_is_refused`, `ManifestIsTheCompletenessSignalTests.test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle`, `SnapshotRetentionTests.test_a_directory_we_did_not_write_is_NEVER_pruned`, `PublicationPathTests.test_explicit_flat_publication_is_also_available`. The other 19 tests stay unmarked and run in explicit-path and thorough runs.
  - Depends on: none
  - Expected outcome: 23 tests pass on an explicit-path run; exactly 4 are selected by `-m core`.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_run_analytics_findings.py` and `tests/test_run_analytics_config.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (20 and 14 tests, under 0.1s each in total).
  - Depends on: none
  - Expected outcome: 34 tests pass, all core-selected.
  - Execution state: pending

- [ ] E-04 Restore `tests/test_run_analytics_e2e.py`. Delete the five tests of `CanaryDisciplineTests` that read committed files or this file's own text (`test_no_live_corpus_byte_was_copied_into_the_fixture_tree`, `test_no_mutation_case_sleeps_spawns_or_opens_a_socket`, `test_the_committed_fixture_tree_scans_clean_under_the_same_gate_ci_applies`, `test_this_test_module_also_scans_clean`, `test_the_fixture_tree_is_tracked_which_is_why_the_rule_exists`) and `test_the_gate_can_fail_which_is_why_clean_means_something` (its only purpose is to be the control for the two deleted scan tests, and it asserts a `handle` finding that fires only on a machine whose local hints file knows the maintainer handle, F-04). Mark with `@pytest.mark.core` only `FixtureCorpusTests.test_the_corpus_carries_all_four_generations_including_both_legacy_ones` (the one test reaching both `run_analytics_sources` keys, 0.08s).
  - Depends on: none
  - Expected outcome: 28 tests pass on an explicit-path run, 1 selected by `-m core`; `rg -n "__file__|git\", \"ls-files|check-ignore" tests/test_run_analytics_e2e.py` returns nothing.
  - Execution state: pending

- [ ] E-05 Restore `tests/test_run_analytics_privacy.py` with a neutral canary set (F-04): change `_HANDLE = "gfa" + "riello"` to `_HANDLE = "some" + "one"` and `_PRIVATE_REPO = "her" + "mes-agent"` to `_PRIVATE_REPO = "example-" + "private-repo"`; in `IndependentDetectorTests.test_control_the_detector_does_flag_every_path_canary_raw` remove `_PRIVATE_REPO` and `_HANDLE` from the raw-canary tuple (neither is a detector-visible value once neutral; the home, macOS, Windows and session-id canaries keep the control's teeth). Delete the four source-reading tests (`test_the_projector_module_itself_is_self_clean`, `test_this_test_file_holds_no_literal_leak`, `test_the_analytics_modules_define_no_detection_ruleset`, `test_no_raw_filelock_or_fcntl_import_in_the_analytics_modules`). Add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: 21 tests pass; `rg -n "riello|mes-agent|__file__|REPO_ROOT / \"agent_workflows\"" tests/test_run_analytics_privacy.py` returns nothing; `aw sanitize --agent` reports `findings":0`.
  - Execution state: pending

- [ ] E-06 Add a docstring paragraph to each of the six restored modules naming backlog `q86fxm`, findings `b1mx2w`, source revision `19313eed^`, and that the source-reading tests were deliberately not restored.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: each module docstring carries the provenance paragraph.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16): this is why the source-reading, file-self-scan and `__doc__` tests are dropped. The privacy property those self-scans guarded (no sensitive literal committed) is enforced by `aw sanitize --agent` in V-05.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget enforced on hosts with 12 or more CPUs. Expensive files are therefore marked per test, choosing the cheapest tests that still reach every key; cheap files are marked per module.
- Sibling precedent in the same Set: `8bhcd3` (telemetry) and `438gkf` (export) restore one core-marked module plus residual tests and validate with `-v` output, coverage output and reverted mutation spot-checks.
- Leak-sanitizer awareness (`AGENTS.md`): a committed test must not carry maintainer-identifying data even fragment-assembled, hence the neutral canaries.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows for the six modules (verdict `unguarded-unreached`); `hpjj44` `## Derived properties` reaching-file column | The 22 keys map to deleted files `tests/test_run_analytics_wizard.py`, `tests/test_run_analytics_report.py`, `tests/test_run_analytics_findings.py`, `tests/test_run_analytics_config.py`, `tests/test_run_analytics_e2e.py` and (for `redact_text._replace`) `tests/test_run_analytics_privacy.py`/`_cache.py`/`_privacy_boundary.py`. |
| F-02 | `python3 tools/deleted_test_replay.py 19313eed <files> --format json` at HEAD `f84c3af26` | Verbatim replays: wizard `fail` (19 passed, 2 failed: `ModuleNotFoundError: No module named 'tests.test_run_analytics_export'` in the two `_code_lines` source-reading tests); report 23 passed; findings 20 passed; config 14 passed; e2e 34 passed; privacy 25 passed. |
| F-03 | Scratch restore with E-01..E-05 edits, `pytest -o addopts="" -n 6 -m "not slow and not livecorpus" --cov=agent_workflows --cov-context=test`, keys mapped to function bodies | Every one of the 22 keys has executed lines, and each is reached by a core-marked test after the E-02/E-04 marking. Summed core CPU time for this child's six files: 0.50s (79 tests). |
| F-04 | `leak_sanitizer.scan_text` with `build_ruleset(REPO_ROOT)` at HEAD | The deleted privacy file's `_HANDLE` is the maintainer handle in fragments and `_PRIVATE_REPO` is a private repository name that scans `private-repo` `fail`; restoring either re-commits identifying data. Neutral `"some" + "one"` scans clean, so it cannot be a raw-detector control; the four path/session canaries still scan `fail` and keep the control meaningful. With the edits, the file passes 21 tests and `aw sanitize --agent` reported `"outcome":"clean" ... "findings":0`. The e2e `handle` control fires only via the local hints file, so it is machine-dependent. |
| F-05 | Coverage contexts of F-03 | `redact_text._replace` is reached by `tests/test_run_analytics_privacy.py` alone after E-05 (`DiagnosticRedactionTests.test_redact_text_removes_home_paths_in_three_shapes`), so `_cache.py` (1145 lines, 25 source-reading hits) and `_privacy_boundary.py` add no key reach for this item. |
| F-06 | `.aw/state/q86mut.py` scratch early-return mutations, each reverted | `plan_deletion` -> `None`: 4 failed; `format_findings_report` -> `""`: 1 failed; `inventory_corpus` -> `None`: 1 failed (the core-marked e2e test). An early-return sweep over all 22 keys killed every one. |

## Proposed changes (ordered, validatable)

1. E-01..E-05 restore the six modules with the listed subset edits and `core` marking.
2. E-06 records provenance in each module docstring.

## Deferred / out of scope (with reason)

- `tests/test_run_analytics_cache.py` and `tests/test_run_analytics_privacy_boundary.py` are not restored.
  - Carrier-Declined: no work is owed for this item; F-05 shows the only `q86fxm` key they reach (`redact_text._replace`) is reached by the E-05 file, and their remaining reach belongs to modules outside `q86fxm`.

## Scope check

- Over-scope: none. Six test files are the only paths declared and changed; no production code.
- Under-scope: none for the 22 keys (F-03, F-06).

## Required tests / validation

- `python3 -m pytest <the six files> -o addopts="" -v` passes, per-test list pasted.
- `python3 -m pytest <the six files> -o addopts="" -m core -q` shows 79 selected and passing.
- Reach: `python3 -m pytest <the six files> -o addopts="" -m core --cov=agent_workflows.run_analytics_wizard --cov=agent_workflows.run_analytics_report --cov=agent_workflows.run_analytics_findings --cov=agent_workflows.run_analytics_sources --cov=agent_workflows.run_analytics_config --cov=agent_workflows.run_analytics_privacy --cov-report=term-missing` with each of the 22 keys shown executing.
- Mutation spot-checks (scratch, reverted): `plan_deletion` return `None`, `format_findings_report` return `""`, `inventory_corpus` return `None`, `prune_snapshots` return `[]`, `clamp_interval` return a constant, `redact_text._replace` return its input.
- `aw sanitize --agent` reports no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the deleted analytics files verbatim, or behavioral subsets?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: behavioral subsets. Verbatim restores bring back source-reading and self-scan tests the repository test contract forbids (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE") and maintainer-identifying canaries (F-04); every remaining test passes unchanged at HEAD (F-02).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --no-index <(git show 19313eed^:tests/test_run_analytics_wizard.py) tests/test_run_analytics_wizard.py` (or an equivalent diff) showing only the two removed tests, the `pytest` import/`pytestmark` lines and the docstring paragraph; paste the `-v` run listing 19 PASSED; paste the failure produced by the scratch `plan_deletion` return-`None` mutation (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` run of `tests/test_run_analytics_report.py` listing 23 PASSED and `-m core --collect-only -q` listing exactly the four marked tests; paste the failure from a scratch `prune_snapshots` return-`[]` mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `-v` runs of both files (20 and 14 PASSED) and the failures from scratch `format_findings_report` return-`""` and `clamp_interval` return-constant mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` run (28 PASSED), the `-m core --collect-only -q` line naming the one marked test, the empty `rg` output named in E-04, and the failure from a scratch `inventory_corpus` return-`None` mutation run against the core-marked test only (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` run (21 PASSED), the empty `rg` output named in E-05, `aw sanitize --agent` with `findings":0`, and the failure from a scratch `redact_text._replace` return-its-input mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the six docstring paragraphs (or `rg -n "q86fxm" <the six files>` showing one hit per file); paste the `--cov-report=term-missing` output from Required tests showing every one of the 22 keys executing; paste the bare `python3 -m pytest` summary line; paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the six Scope-Paths files through `aw commit ivap17 -- <paths>`; never push. Mutation spot-checks are scratch edits to production modules that must be reverted before commit and must not appear in the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
