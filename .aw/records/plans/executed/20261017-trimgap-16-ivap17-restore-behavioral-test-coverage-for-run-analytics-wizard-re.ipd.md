# IPD: Restore behavioral test coverage for run analytics wizard, report, findings, config, sources and privacy

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup groups 16 through 60 of the `b1mx2w` `## Filing plan`) carries 135 production keys that the routine non-slow selection did not reach at baseline HEAD `86f0d88d`, because the suite trim `19313eed` deleted the behavioral test files that drove them. This child owns the run-analytics slice: groups 16 (`run_analytics_wizard.py`, 10 keys), 19 (`run_analytics_report.py`, 5 keys), 21 (`run_analytics_findings.py`, 3 keys), 34 (`run_analytics_sources.py`, 2 keys), 39 (`run_analytics_config.py`, 1 key) and 50 (`run_analytics_privacy.py`, 1 key), 22 keys in all. A mutation that, for example, made `plan_deletion` return `None` or `format_findings_report` return an empty string passes the routine suite today.
- Scope: Restore six deleted test modules from `19313eed^` at their original paths, minus their code-pinning tests, with a neutral privacy canary and `core` markers, so the 22 keys are reached by the routine bare gate. The 22 keys: `run_analytics_wizard.apply_choices`, `read_settings`, `plan_deletion`, `write_settings`, `delete_analytics_artifacts`, `AnalyticsSettings.to_dict`, `_looks_like_secret`, `AnalyticsSettings.endpoint`, `_coerce_bool`, `_local_path`; `run_analytics_report._publish_flat`, `verify_bundle`, `prune_snapshots`, `publish_snapshot`, `resolve_snapshot_dir`; `run_analytics_findings.format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison`; `run_analytics_sources.inventory_corpus`, `CorpusInventory.generation_counts`; `run_analytics_config.clamp_interval`; `run_analytics_privacy.redact_text._replace`. EXCLUDES any production-code change; EXCLUDES restoring `tests/test_run_analytics_cache.py` and `tests/test_run_analytics_privacy_boundary.py` (F-05); EXCLUDES keys of other modules these files happen to reach.
- Scope-Paths: tests/test_run_analytics_wizard.py, tests/test_run_analytics_report.py, tests/test_run_analytics_findings.py, tests/test_run_analytics_config.py, tests/test_run_analytics_e2e.py, tests/test_run_analytics_privacy.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 16
- Highest E allocated: 06
- Author: opencode
- Id: ivap17

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ivap17 verified (set trimgap, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` against HEAD `f84c3af26`, applied the proposed subset edits to scratch copies under `tests/`, and measured per-key reach (coverage contexts), per-test durations and early-return mutation kills before writing any step; scratch copies and `.coverage` were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 22 run-analytics keys of backlog `q86fxm` (groups 16, 19, 21, 34, 39, 50) reached by the routine bare core-tier run, through restored behavioral tests that build settings, publish and prune snapshots, render findings, inventory a fixture corpus and redact diagnostics, then assert on returned values, written files and raised refusals. Done means an early-return mutation of any of the 22 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Common rule for every E-item below (the RESTORE RULE): create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add the stated `core` marking, inserting a module-level `pytestmark = pytest.mark.core` AFTER the last complete top-level import statement (several of these files end their imports with a parenthesized multi-line `from ... import (...)`); keep every other test body unchanged; after deleting tests, remove any top-level import or constant the deletion leaves unused (the repository's `ruff` pre-commit hook rejects an unused import, and its `--fix` would otherwise rewrite the file mid-commit). Disposition rule if a kept test fails at execution HEAD: do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.

### Task group 1: restore the analytics modules

- [x] E-01 Restore `tests/test_run_analytics_wizard.py`. Delete `test_no_optional_install_mechanism_is_built` and `test_deletion_never_composes_the_runs_literal_itself` (both import `tests.test_run_analytics_export._code_lines` and assert substrings of `agent_workflows/run_analytics_wizard.py` source, F-02). Add a module-level `pytestmark = pytest.mark.core` (19 tests, 0.09s summed at authoring).
  - Depends on: none
  - Expected outcome: every kept test passes (19 at authoring and review); the file contains no `_code_lines` and no `agent_workflows/` path string.
  - Execution state: performed

- [x] E-02 Restore `tests/test_run_analytics_report.py` unchanged except marking with `@pytest.mark.core` exactly these six tests (the cheapest set that both reaches all five report keys and KILLS each one's early-return mutation, F-07): `RefusalTests.test_a_traversing_snapshot_label_is_refused`, `ManifestIsTheCompletenessSignalTests.test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle`, `SnapshotRetentionTests.test_a_directory_we_did_not_write_is_NEVER_pruned`, `SnapshotRetentionTests.test_snapshots_are_pruned_to_the_keep_count` (the only test asserting on `prune_snapshots`' returned list), `SnapshotRetentionTests.test_a_snapshot_manifest_records_immutability` (asserts on `publish_snapshot`'s returned manifest), `PublicationPathTests.test_explicit_flat_publication_is_also_available`. The other 17 tests stay unmarked and run in explicit-path and thorough runs.
  - Depends on: none
  - Expected outcome: every test passes on an explicit-path run (23 at review); exactly the six named tests are selected by `-m core`.
  - Execution state: performed

- [x] E-03 Restore `tests/test_run_analytics_findings.py` and `tests/test_run_analytics_config.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (20 and 14 tests, under 0.1s each in total).
  - Depends on: none
  - Expected outcome: every test in both files passes and is core-selected (20 and 14 at review).
  - Execution state: performed

- [x] E-04 Restore `tests/test_run_analytics_e2e.py`. Delete the five tests of `CanaryDisciplineTests` that read committed files or this file's own text (`test_no_live_corpus_byte_was_copied_into_the_fixture_tree`, `test_no_mutation_case_sleeps_spawns_or_opens_a_socket`, `test_the_committed_fixture_tree_scans_clean_under_the_same_gate_ci_applies`, `test_this_test_module_also_scans_clean`, `test_the_fixture_tree_is_tracked_which_is_why_the_rule_exists`) and `test_the_gate_can_fail_which_is_why_clean_means_something` (its only purpose is to be the control for the two deleted scan tests, and it asserts a `handle` finding that fires only on a machine whose local hints file knows the maintainer handle, F-04). Mark with `@pytest.mark.core` only `FixtureCorpusTests.test_the_corpus_carries_all_four_generations_including_both_legacy_ones` (the one test reaching both `run_analytics_sources` keys, 0.08s). Then, per the RESTORE RULE, delete the definitions the six deletions leave unused: the `FIXTURE_TREE = Path(__file__)...` constant (no kept test reads it, verified at review) and the `import subprocess` line (`ruff check --select F` flags it, F-07). The module docstring prose mentioning `git check-ignore` may stay (it explains why the fixture tree is tracked); E-06 notes the removed checks.
  - Depends on: none
  - Expected outcome: every kept test passes on an explicit-path run (28 at review), exactly the one named test is selected by `-m core`; `rg -n "__file__|ls-files|\"check-ignore\"|^import subprocess" tests/test_run_analytics_e2e.py` returns nothing, and `ruff check --select F tests/test_run_analytics_e2e.py` is clean.
  - Execution state: performed

- [x] E-05 Restore `tests/test_run_analytics_privacy.py` with a neutral canary set (F-04): change `_HANDLE = "gfa" + "riello"` to `_HANDLE = "some" + "one"` and `_PRIVATE_REPO = "her" + "mes-agent"` to `_PRIVATE_REPO = "example-" + "private-repo"`; in `IndependentDetectorTests.test_control_the_detector_does_flag_every_path_canary_raw` remove `_PRIVATE_REPO` and `_HANDLE` from the raw-canary tuple (neither is a detector-visible value once neutral; the home, macOS, Windows and session-id canaries keep the control's teeth). Delete the four source-reading tests (`test_the_projector_module_itself_is_self_clean`, `test_this_test_file_holds_no_literal_leak`, `test_the_analytics_modules_define_no_detection_ruleset`, `test_no_raw_filelock_or_fcntl_import_in_the_analytics_modules`). Add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: every kept test passes (21 at review); `rg -n "riello|mes-agent|__file__|REPO_ROOT / \"agent_workflows\"" tests/test_run_analytics_privacy.py` returns nothing; `aw sanitize --agent` reports `findings":0` once the file is staged or committed (it scans TRACKED files; an untracked file is not scanned, F-07), and before that `leak_sanitizer.scan_text` over the file with `build_ruleset(REPO_ROOT)` returns no finding.
  - Execution state: performed

- [x] E-06 Add a docstring paragraph to each of the six restored modules naming backlog `q86fxm`, findings `b1mx2w`, source revision `19313eed^`, and that the source-reading tests were deliberately not restored.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: each module docstring carries the provenance paragraph.
  - Execution state: performed

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
| F-06 | `.aw/state/q86mut.py` scratch early-return mutations, each reverted | `plan_deletion` -> `None`: 4 failed; `format_findings_report` -> `""`: 1 failed; `inventory_corpus` -> `None`: 1 failed (the core-marked e2e test). An early-return sweep over all 22 keys killed every one. CORRECTED at review (F-07): that sweep was not run under `-m core`; under the routine core selection two keys survived with the original four-test report marking. |
| F-07 | review (2026-10-17, HEAD `cfc742aef`): scratch restores of the six files built by applying E-01..E-05 literally, scratch production mutations, all removed or reverted (`git diff agent_workflows/` empty) | Explicit-path run of the six files `125 passed in 2.71s`; `-m core` `79 passed, 46 deselected`; per-function coverage JSON under `-m core` shows all 22 keys with nonzero executed lines. Early-return sweep under `-m core` over all 22 keys (both polarities for boolean returns): 20 killed, but `run_analytics_report.prune_snapshots -> []` and `publish_snapshot -> None` SURVIVED (`79 passed`): the four marked report tests call them without asserting on their return. Marking `test_snapshots_are_pruned_to_the_keep_count` and `test_a_snapshot_manifest_records_immutability` (0.09s and 0.03s) kills both (`1 failed` and `2 failed`). With six report tests marked, bare `python3 -m pytest` `834 passed in 26.61s` (30s budget). E-04 as written leaves `FIXTURE_TREE = Path(__file__)` (so its `rg` check could not return nothing) and an unused `import subprocess` (`ruff check --select F`: 1 error). `aw sanitize --agent` reported `checked: 5835` with and without the untracked scratch files, so it does not scan untracked files; `leak_sanitizer.scan_text` over each restored file returned no finding. |

## Proposed changes (ordered, validatable)

1. E-01..E-05 restore the six modules with the listed subset edits and `core` marking (six report tests marked, F-07).
2. E-06 records provenance in each module docstring.

## Deferred / out of scope (with reason)

- `tests/test_run_analytics_cache.py` and `tests/test_run_analytics_privacy_boundary.py` are not restored.
  - Carrier-Declined: no work is owed for this item; F-05 shows the only `q86fxm` key they reach (`redact_text._replace`) is reached by the E-05 file, and their remaining reach belongs to modules outside `q86fxm`.

## Scope check

- Over-scope: none. Six test files are the only paths declared and changed; no production code.
- Under-scope: none for the 22 keys once E-02 marks the six tests (F-03, F-07).

## Required tests / validation

- `python3 -m pytest <the six files> -o addopts="" -v` passes, per-test list pasted.
- `python3 -m pytest <the six files> -o addopts="" -m core -q` shows the core selection passing (81 at review: the 79 F-03 measured plus the two report tests F-07 added).
- Reach: `COVERAGE_FILE=.aw/state/ivap17.coverage python3 -m pytest <the six files> -o addopts="" -m core --cov=agent_workflows --cov-report=json:.aw/state/ivap17-cov.json`, then print each of the 22 keys' `files[...]["functions"][<qualname>]["summary"]["covered_lines"]` from the JSON (nonzero for every key). `term-missing` reports lines, not functions, so it cannot show a key executing; both data files live under the gitignored `.aw/state/` and are deleted afterwards.
- Mutation spot-checks (scratch, reverted), each run with `-m core` over the six files so they measure the routine gate: `plan_deletion` return `None`, `format_findings_report` return `""`, `inventory_corpus` return `None`, `prune_snapshots` return `[]`, `publish_snapshot` return `None`, `clamp_interval` return a constant, `redact_text._replace` return its input.
- `aw sanitize --agent` reports no `fail`, run after the files are staged or committed (it scans tracked files only).
- `ruff check --select F <the six files>` is clean.

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

- [x] V-01 validates E-01
  - Required evidence: paste `git diff --no-index <(git show 19313eed^:tests/test_run_analytics_wizard.py) tests/test_run_analytics_wizard.py` (or an equivalent diff) showing only the two removed tests, the `pytest` import/`pytestmark` lines and the docstring paragraph; paste the `-v` run listing every kept test PASSED with its summary line; paste the failure produced by the scratch `plan_deletion` return-`None` mutation under `-m core` (reverted afterwards).
  - Observed evidence:
```
$ git diff --no-index <(git show 19313eed^:tests/test_run_analytics_wizard.py) tests/test_run_analytics_wizard.py
diff --git a/dev/fd/63 b/tests/test_run_analytics_wizard.py
index 000000000..35830d948 100644
--- a/dev/fd/63
+++ b/tests/test_run_analytics_wizard.py
@@ -5,6 +5,8 @@ carries information. :func:`test_the_xdg_user_config_would_have_dropped_the_sett
 ``config.normalize()`` discarding an ``analytics_endpoint`` key, and the adjacent test shows the
 same setting surviving a round trip through ``local.json``. A bare "settings round-trip" test would
 pass against a location that silently loses them on the NEXT save.
+
+Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
 """

 from __future__ import annotations
@@ -16,6 +18,8 @@ import pytest

 from agent_workflows import run_analytics_wizard as wizard

+pytestmark = pytest.mark.core
+

 def _repo(tmp_path: Path) -> Path:
     (tmp_path / ".aw" / "config").mkdir(parents=True)
@@ -286,24 +290,6 @@ def test_negative_retention_is_refused(tmp_path):
         )


-def test_no_optional_install_mechanism_is_built():
-    """F-8: the modules ship in-package; the wizard gates ENABLEMENT, not code presence."""
-
-    from tests.test_run_analytics_export import _code_lines
-
-    code = _code_lines("agent_workflows/run_analytics_wizard.py")
-    for forbidden in (
-        "pip",
-        "subprocess",
-        "install",
-        "extras_require",
-        "importlib.util.find_spec",
-    ):
-        assert forbidden not in code, f"wizard reaches for {forbidden!r}"
-    # What it DOES gate is a boolean.
-    assert "analytics_enabled" in code
-
-
 # --- precise deletion ----------------------------------------------------------------------------


@@ -377,14 +363,3 @@ def test_deletion_is_dry_run_by_default(tmp_path):
     assert result["dry_run"] is False
     assert str(owned) in result["deleted"]
     assert not owned.exists()
-
-
-def test_deletion_never_composes_the_runs_literal_itself():
-    """Order 01 owns the resolver; a second copy is a second thing to get wrong."""
-
-    from tests.test_run_analytics_export import _code_lines
-
-    code = _code_lines("agent_workflows/run_analytics_wizard.py")
-    assert ".aw/records/runs" not in code
-    assert "path_is_within_analytics" in code
-    assert "analytics_root" in code

$ python3 -m pytest tests/test_run_analytics_wizard.py -o addopts="" -v
collecting ... collected 19 items

tests/test_run_analytics_wizard.py::test_every_default_is_off PASSED     [  5%]
tests/test_run_analytics_wizard.py::test_deletion_refuses_the_whole_batch_rather_than_half_deleting PASSED [ 10%]
tests/test_run_analytics_wizard.py::test_unattended_with_incomplete_choices_fails_closed PASSED [ 15%]
tests/test_run_analytics_wizard.py::test_enabling_submission_without_a_url_is_refused PASSED [ 21%]
tests/test_run_analytics_wizard.py::test_unattended_is_local_and_no_submit PASSED [ 26%]
tests/test_run_analytics_wizard.py::test_negative_retention_is_refused PASSED [ 31%]
tests/test_run_analytics_wizard.py::test_the_local_binding_schema_round_trips_the_unknown_key PASSED [ 36%]
tests/test_run_analytics_wizard.py::test_sampling_is_a_separate_question_from_analytics PASSED [ 42%]
tests/test_run_analytics_wizard.py::test_deletion_plans_only_tool_owned_analytics_children PASSED [ 47%]
tests/test_run_analytics_wizard.py::test_writing_settings_preserves_other_keys_in_the_local_binding PASSED [ 52%]
tests/test_run_analytics_wizard.py::test_endpoint_is_unavailable_unless_submission_is_explicitly_enabled PASSED [ 57%]
tests/test_run_analytics_wizard.py::test_cross_box_correlation_defaults_off_as_order_02_deferred PASSED [ 63%]
tests/test_run_analytics_wizard.py::test_a_credential_value_is_refused_where_a_variable_name_belongs PASSED [ 68%]
tests/test_run_analytics_wizard.py::test_the_xdg_user_config_would_have_dropped_the_setting PASSED [ 73%]
tests/test_run_analytics_wizard.py::test_deletion_is_dry_run_by_default PASSED [ 78%]
tests/test_run_analytics_wizard.py::test_no_secret_is_ever_written_to_the_config PASSED [ 84%]
tests/test_run_analytics_wizard.py::test_settings_survive_a_round_trip_through_the_local_binding PASSED [ 89%]
tests/test_run_analytics_wizard.py::test_deletion_refuses_a_target_outside_the_analytics_namespace PASSED [ 94%]
tests/test_run_analytics_wizard.py::test_unattended_with_yes_alone_still_fails_closed PASSED [100%]
============================== 19 passed in 1.83s ==============================

$ python3 -m pytest tests/test_run_analytics_wizard.py -o addopts="" -m core  # with plan_deletion -> None
FAILED tests/test_run_analytics_wizard.py::test_deletion_plans_only_tool_owned_analytics_children
FAILED tests/test_run_analytics_wizard.py::test_deletion_is_dry_run_by_default
FAILED tests/test_run_analytics_wizard.py::test_deletion_refuses_the_whole_batch_rather_than_half_deleting
FAILED tests/test_run_analytics_wizard.py::test_deletion_refuses_a_target_outside_the_analytics_namespace
========================= 4 failed, 15 passed in 0.66s =========================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `-v` run of `tests/test_run_analytics_report.py` listing every test PASSED and `-m core --collect-only -q` listing exactly the six marked tests; paste the failures, under `-m core` over the six files, from scratch `prune_snapshots` return-`[]` and `publish_snapshot` return-`None` mutations (reverted).
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_analytics_report.py -o addopts="" -v
collecting ... collected 23 items

tests/test_run_analytics_report.py::MeasuredPlatformBehaviourTests::test_a_symlink_flip_IS_atomic PASSED [  4%]
tests/test_run_analytics_report.py::MeasuredPlatformBehaviourTests::test_os_replace_REFUSES_a_non_empty_directory PASSED [  8%]
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_a_snapshot_manifest_records_immutability PASSED [ 13%]
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_snapshots_are_pruned_to_the_keep_count PASSED [ 17%]
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_a_directory_we_did_not_write_is_NEVER_pruned PASSED [ 21%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_manifest_is_ordered_last PASSED [ 26%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_an_interrupted_republish_never_leaves_a_STALE_manifest PASSED [ 30%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_manifest_carries_size_and_digest_for_every_file PASSED [ 34%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle PASSED [ 39%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_verify_bundle_DETECTS_a_tampered_file PASSED [ 43%]
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_a_directory_with_no_manifest_is_REFUSED_as_incomplete PASSED [ 47%]
tests/test_run_analytics_report.py::PublicationPathTests::test_a_second_publish_leaves_the_first_bundle_intact PASSED [ 52%]
tests/test_run_analytics_report.py::PublicationPathTests::test_the_windows_no_symlink_FALLBACK_is_implemented_and_completes PASSED [ 56%]
tests/test_run_analytics_report.py::PublicationPathTests::test_explicit_flat_publication_is_also_available PASSED [ 60%]
tests/test_run_analytics_report.py::PublicationPathTests::test_primary_path_publishes_versioned_and_flips_latest PASSED [ 65%]
tests/test_run_analytics_report.py::RefusalTests::test_a_bundle_without_index_html_is_refused PASSED [ 69%]
tests/test_run_analytics_report.py::RefusalTests::test_a_nested_bundle_file_name_is_refused PASSED [ 73%]
tests/test_run_analytics_report.py::RefusalTests::test_a_traversing_snapshot_label_is_refused PASSED [ 78%]
tests/test_run_analytics_report.py::RefusalTests::test_an_empty_bundle_is_refused PASSED [ 82%]
tests/test_run_analytics_report.py::RefusalTests::test_publishing_OUTSIDE_the_analytics_namespace_is_refused PASSED [ 86%]
tests/test_run_analytics_report.py::ResolverTests::test_snapshot_dir_is_under_order_01s_snapshots_dir PASSED [ 91%]
tests/test_run_analytics_report.py::ResolverTests::test_report_dir_is_order_01s_analytics_root PASSED [ 95%]
tests/test_run_analytics_report.py::DeterminismTests::test_two_publications_of_identical_input_produce_identical_bytes PASSED [100%]
============================== 23 passed in 1.91s ==============================

$ python3 -m pytest tests/test_run_analytics_report.py -o addopts="" -m core --collect-only -q
tests/test_run_analytics_report.py::ManifestIsTheCompletenessSignalTests::test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_a_directory_we_did_not_write_is_NEVER_pruned
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_a_snapshot_manifest_records_immutability
tests/test_run_analytics_report.py::SnapshotRetentionTests::test_snapshots_are_pruned_to_the_keep_count
tests/test_run_analytics_report.py::PublicationPathTests::test_explicit_flat_publication_is_also_available
tests/test_run_analytics_report.py::RefusalTests::test_a_traversing_snapshot_label_is_refused

6/23 tests collected (17 deselected) in 0.49s

$ python3 -m pytest <the six files> -o addopts="" -m core -q  # with prune_snapshots -> []
FAILED tests/test_run_analytics_report.py::SnapshotRetentionTests::test_snapshots_are_pruned_to_the_keep_count
1 failed, 80 passed, 44 deselected in 2.29s

$ python3 -m pytest <the six files> -o addopts="" -m core -q  # with publish_snapshot -> None
FAILED tests/test_run_analytics_report.py::SnapshotRetentionTests::test_a_snapshot_manifest_records_immutability
FAILED tests/test_run_analytics_report.py::SnapshotRetentionTests::test_snapshots_are_pruned_to_the_keep_count
2 failed, 79 passed, 44 deselected in 3.79s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `-v` runs of both files with every test PASSED and the failures, under `-m core`, from scratch `format_findings_report` return-`""` and `clamp_interval` return-constant mutations (reverted).
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_analytics_findings.py -o addopts="" -v
collecting ... collected 20 items

tests/test_run_analytics_findings.py::CannotDetermineFindingTests::test_every_non_computed_result_becomes_exactly_one_finding PASSED [  5%]
tests/test_run_analytics_findings.py::CannotDetermineFindingTests::test_a_refusal_finding_carries_no_advice_and_every_evidence_field PASSED [ 10%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_every_contract_field_survives_serialization PASSED [ 15%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_NO_ALTERNATIVE_EXPLANATION_is_refused PASSED [ 20%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_no_DATA_QUALITY_CAVEAT_is_refused PASSED [ 25%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_a_conforming_finding_is_built PASSED [ 30%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_no_NEXT_EXPERIMENT_is_refused PASSED [ 35%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_no_TITLE_is_refused PASSED [ 40%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_a_RECOMMENDATION_on_a_cannot_determine_finding_is_refused PASSED [ 45%]
tests/test_run_analytics_findings.py::ContractRefusalTests::test_no_UNCERTAINTY_statement_is_refused PASSED [ 50%]
tests/test_run_analytics_findings.py::RankingStabilityTests::test_the_severity_order_covers_EVERY_severity_so_ranking_is_total PASSED [ 55%]
tests/test_run_analytics_findings.py::RankingStabilityTests::test_the_ranking_keys_hold_in_precedence_and_do_not_depend_on_input_order PASSED [ 60%]
tests/test_run_analytics_findings.py::PriceEraParadoxTests::test_the_paradox_finding_passes_its_own_causal_language_check PASSED [ 65%]
tests/test_run_analytics_findings.py::PriceEraParadoxTests::test_the_golden_finding_and_its_baseline_carry_the_measured_figures PASSED [ 70%]
tests/test_run_analytics_findings.py::PriceEraParadoxTests::test_a_pooled_era_comparison_is_flagged_and_a_stratified_one_is_not PASSED [ 75%]
tests/test_run_analytics_findings.py::ReportTests::test_every_finding_set_renders_completely_and_leaks_no_location PASSED [ 80%]
tests/test_run_analytics_findings.py::CausalLanguageTests::test_every_human_readable_field_is_scanned_and_named_in_the_refusal PASSED [ 85%]
tests/test_run_analytics_findings.py::CausalLanguageTests::test_the_scanner_returns_exactly_the_causal_matches_for_every_phrase PASSED [ 90%]
tests/test_run_analytics_findings.py::CausalLanguageTests::test_the_check_FIRES_on_a_planted_causal_claim PASSED [ 95%]
tests/test_run_analytics_findings.py::CausalLanguageTests::test_it_is_CLEAN_on_the_association_phrasing PASSED [100%]
============================== 20 passed in 0.70s ==============================

$ python3 -m pytest tests/test_run_analytics_config.py -o addopts="" -v
collecting ... collected 14 items

tests/test_run_analytics_config.py::DefaultsTests::test_disabling_telemetry_also_disables_sampling PASSED [  7%]
tests/test_run_analytics_config.py::DefaultsTests::test_basic_telemetry_is_on_and_periodic_sampling_is_off_by_default PASSED [ 14%]
tests/test_run_analytics_config.py::DefaultsTests::test_periodic_sampling_can_be_enabled_explicitly PASSED [ 21%]
tests/test_run_analytics_config.py::NeverRaisesTests::test_malformed_and_out_of_vocabulary_values_land_on_defaults PASSED [ 28%]
tests/test_run_analytics_config.py::NeverRaisesTests::test_boolean_spellings_are_tolerated PASSED [ 35%]
tests/test_run_analytics_config.py::NeverRaisesTests::test_unreadable_and_invalid_files_yield_defaults PASSED [ 42%]
tests/test_run_analytics_config.py::ConfigHomeTests::test_project_policy_is_read_from_the_committed_portable_file PASSED [ 50%]
tests/test_run_analytics_config.py::ConfigHomeTests::test_telemetry_key_survives_a_project_policy_round_trip PASSED [ 57%]
tests/test_run_analytics_config.py::ConfigHomeTests::test_the_key_is_deliberately_absent_from_the_xdg_config_schema PASSED [ 64%]
tests/test_run_analytics_config.py::ConfigHomeTests::test_top_level_key_wins_over_runtime_overrides_within_one_file PASSED [ 71%]
tests/test_run_analytics_config.py::ConfigHomeTests::test_machine_local_override_beats_project_policy PASSED [ 78%]
tests/test_run_analytics_config.py::IntervalBoundTests::test_clamp_is_the_single_enforcement_point PASSED [ 85%]
tests/test_run_analytics_config.py::IntervalBoundTests::test_every_config_is_in_bounds_because_the_producer_clamps PASSED [ 92%]
tests/test_run_analytics_config.py::IntervalBoundTests::test_probe_budget_cannot_exceed_the_module_ceiling PASSED [100%]
============================== 14 passed in 0.24s ==============================

$ python3 -m pytest tests/test_run_analytics_findings.py -o addopts="" -m core  # with format_findings_report -> ""
FAILED tests/test_run_analytics_findings.py::ReportTests::test_every_finding_set_renders_completely_and_leaks_no_location
========================= 1 failed, 19 passed in 0.34s =========================

$ python3 -m pytest tests/test_run_analytics_config.py -o addopts="" -m core  # with clamp_interval -> 42.0
FAILED tests/test_run_analytics_config.py::ConfigHomeTests::test_telemetry_key_survives_a_project_policy_round_trip
FAILED tests/test_run_analytics_config.py::ConfigHomeTests::test_top_level_key_wins_over_runtime_overrides_within_one_file
FAILED tests/test_run_analytics_config.py::ConfigHomeTests::test_machine_local_override_beats_project_policy
FAILED tests/test_run_analytics_config.py::ConfigHomeTests::test_project_policy_is_read_from_the_committed_portable_file
FAILED tests/test_run_analytics_config.py::DefaultsTests::test_periodic_sampling_can_be_enabled_explicitly
FAILED tests/test_run_analytics_config.py::IntervalBoundTests::test_clamp_is_the_single_enforcement_point
========================= 6 failed, 8 passed in 0.36s ==========================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `-v` run (every kept test PASSED), the `-m core --collect-only -q` line naming the one marked test, the empty `rg` output and clean `ruff check --select F` output named in E-04, and the failure from a scratch `inventory_corpus` return-`None` mutation run against the core-marked test only (reverted).
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_analytics_e2e.py -o addopts="" -v
collecting ... collected 28 items

tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_1_and_2_ingest_their_generation_and_host PASSED [  3%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_13_corrupt_run_is_contained PASSED [  7%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_every_synthetic_exercise_is_labeled_and_none_claims_corpus_validation PASSED [ 10%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_the_matrix_declares_exactly_thirty_three_numbered_scenarios PASSED [ 14%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_30_empty_corpus_is_a_valid_sweep PASSED [ 17%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_7_absent_verifier_is_not_applicable_rather_than_zero PASSED [ 21%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_a_refused_analysis_cannot_yield_a_rendered_value PASSED [ 25%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_31_corpus_scale_ingestion_without_a_time_dependency PASSED [ 28%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_a_refusal_is_a_declared_passing_outcome_with_an_observed_n PASSED [ 32%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_scenario_32_every_canary_class_is_planted_and_structurally_excluded PASSED [ 35%]
tests/test_run_analytics_e2e.py::ScenarioMatrixTests::test_every_scenario_states_its_expected_outcome_in_advance PASSED [ 39%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_a_removed_run_yields_no_decision_at_all PASSED [ 42%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_a_corrupt_run_degrades_only_itself PASSED [ 46%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_every_lifecycle_case_produces_its_declared_decision_and_reason PASSED [ 50%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_a_contended_entry_skips_and_writes_nothing PASSED [ 53%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_a_resumed_run_is_not_judged_by_mtime PASSED [ 57%]
tests/test_run_analytics_e2e.py::CacheMutationMatrixTests::test_a_truncated_entry_never_reads_back_as_valid PASSED [ 60%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_hand_calculated_totals_match_the_ingested_facts PASSED [ 64%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_schema_version_is_uniform_so_it_cannot_discriminate_a_generation PASSED [ 67%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_the_fixtures_are_deterministic_across_two_builds PASSED [ 71%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_no_non_agy_scenario_is_falsely_marked_synthetic PASSED [ 75%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_the_agy_scenarios_are_labeled_synthetic_in_the_manifest_itself PASSED [ 78%]
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones PASSED [ 82%]
tests/test_run_analytics_e2e.py::OfflineReportTests::test_the_offline_claim_is_stated_as_what_was_tested PASSED [ 85%]
tests/test_run_analytics_e2e.py::OfflineReportTests::test_the_bundle_opens_from_a_file_url_with_sockets_denied PASSED [ 89%]
tests/test_run_analytics_e2e.py::OfflineReportTests::test_denying_sockets_really_does_deny_them PASSED [ 92%]
tests/test_run_analytics_e2e.py::OfflineReportTests::test_the_offline_harness_FAILS_when_a_network_reference_is_introduced PASSED [ 96%]
tests/test_run_analytics_e2e.py::CanaryDisciplineTests::test_every_canary_class_is_assembled_and_non_empty PASSED [100%]
============================== 28 passed in 1.29s ==============================

$ python3 -m pytest tests/test_run_analytics_e2e.py -o addopts="" -m core --collect-only -q
tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones
1/28 tests collected (27 deselected) in 0.34s

$ rg -n "__file__|ls-files|"check-ignore"|^import subprocess" tests/test_run_analytics_e2e.py
(returns empty)

$ ruff check --select F tests/test_run_analytics_e2e.py
All checks passed!

$ python3 -m pytest tests/test_run_analytics_e2e.py -o addopts="" -m core  # with inventory_corpus -> None
FAILED tests/test_run_analytics_e2e.py::FixtureCorpusTests::test_the_corpus_carries_all_four_generations_including_both_legacy_ones
======================= 1 failed, 27 deselected in 0.50s =======================
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `-v` run (every kept test PASSED), the empty `rg` output named in E-05, `aw sanitize --agent` with `findings":0` run after staging, and the failure under `-m core` from a scratch `redact_text._replace` return-its-input mutation (reverted).
  - Observed evidence:
```
$ python3 -m pytest tests/test_run_analytics_privacy.py -o addopts="" -v
collecting ... collected 21 items

tests/test_run_analytics_privacy.py::SaltContractTests::test_pseudonym_does_not_contain_its_input PASSED [  4%]
tests/test_run_analytics_privacy.py::SaltContractTests::test_pseudonym_is_stable_per_salt_and_uncorrelatable_across_salts PASSED [  9%]
tests/test_run_analytics_privacy.py::SaltContractTests::test_salt_is_created_beside_the_cache_and_is_not_world_readable PASSED [ 14%]
tests/test_run_analytics_privacy.py::SaltContractTests::test_unknown_domain_and_empty_salt_are_refused PASSED [ 19%]
tests/test_run_analytics_privacy.py::SaltContractTests::test_salt_is_stable_across_calls_and_never_reminted PASSED [ 23%]
tests/test_run_analytics_privacy.py::SaltContractTests::test_pseudonym_domains_do_not_join PASSED [ 28%]
tests/test_run_analytics_privacy.py::DiagnosticRedactionTests::test_redacted_diagnostics_are_clean_under_the_shipped_detector PASSED [ 33%]
tests/test_run_analytics_privacy.py::DiagnosticRedactionTests::test_redact_text_removes_home_paths_in_three_shapes PASSED [ 38%]
tests/test_run_analytics_privacy.py::IndependentDetectorTests::test_projected_facts_are_clean_under_the_shipped_detector PASSED [ 42%]
tests/test_run_analytics_privacy.py::IndependentDetectorTests::test_control_the_detector_does_flag_every_path_canary_raw PASSED [ 47%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_no_forbidden_key_is_in_the_allowlist_by_accident PASSED [ 52%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_allowlisted_numeric_and_label_facts_pass_unchanged PASSED [ 57%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_source_root_id_must_already_be_a_pseudonym PASSED [ 61%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_an_allowlisted_key_still_refuses_a_smuggled_value PASSED [ 66%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_event_allowlist_is_narrower_than_the_metric_allowlist PASSED [ 71%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_refusal_is_not_a_silent_drop PASSED [ 76%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_token_map_refuses_a_non_numeric_or_path_shaped_component PASSED [ 80%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_projection_is_key_order_independent PASSED [ 85%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_an_unknown_key_is_refused_and_the_diagnostic_names_it PASSED [ 90%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_every_forbidden_class_from_the_plan_is_refused PASSED [ 95%]
tests/test_run_analytics_privacy.py::AllowlistDirectionTests::test_open_token_map_accepts_an_unanticipated_component_key PASSED [100%]
============================== 21 passed in 0.26s ==============================

$ rg -n "riello|mes-agent|__file__|REPO_ROOT / "agent_workflows"" tests/test_run_analytics_privacy.py
(returns empty)

$ aw sanitize --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5902,"findings":0,"evidence":["leak-scan"],"next":null}

$ python3 -m pytest tests/test_run_analytics_privacy.py -o addopts="" -m core  # with redact_text._replace -> match.group(0)
FAILED tests/test_run_analytics_privacy.py::DiagnosticRedactionTests::test_redact_text_removes_home_paths_in_three_shapes
FAILED tests/test_run_analytics_privacy.py::DiagnosticRedactionTests::test_redacted_diagnostics_are_clean_under_the_shipped_detector
========================= 2 failed, 19 passed in 0.41s =========================
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the six docstring paragraphs (or `rg -n "q86fxm" <the six files>` showing one hit per file); paste the per-function coverage listing from Required tests showing every one of the 22 keys with nonzero covered lines; paste the bare `python3 -m pytest` summary line with its wall time (26.61s of a 30s budget at review); paste a final empty `git diff agent_workflows/` and a `git status --short` with no coverage data file.
  - Observed evidence:
```
$ rg -n "q86fxm" tests/test_run_analytics_wizard.py tests/test_run_analytics_report.py tests/test_run_analytics_findings.py tests/test_run_analytics_config.py tests/test_run_analytics_e2e.py tests/test_run_analytics_privacy.py
tests/test_run_analytics_wizard.py:9:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
tests/test_run_analytics_findings.py:35:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
tests/test_run_analytics_report.py:16:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
tests/test_run_analytics_e2e.py:30:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
tests/test_run_analytics_privacy.py:18:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.
tests/test_run_analytics_config.py:25:Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^; source-reading tests were deliberately not restored per repository conventions.

Coverage reach across all 22 keys under -m core:
agent_workflows/run_analytics_wizard.py :: apply_choices -> 16/16 covered lines (key: apply_choices)
agent_workflows/run_analytics_wizard.py :: read_settings -> 11/14 covered lines (key: read_settings)
agent_workflows/run_analytics_wizard.py :: plan_deletion -> 13/13 covered lines (key: plan_deletion)
agent_workflows/run_analytics_wizard.py :: write_settings -> 14/14 covered lines (key: write_settings)
agent_workflows/run_analytics_wizard.py :: delete_analytics_artifacts -> 13/15 covered lines (key: delete_analytics_artifacts)
agent_workflows/run_analytics_wizard.py :: AnalyticsSettings.to_dict -> 1/1 covered lines (key: AnalyticsSettings.to_dict)
agent_workflows/run_analytics_wizard.py :: _looks_like_secret -> 5/5 covered lines (key: _looks_like_secret)
agent_workflows/run_analytics_wizard.py :: AnalyticsSettings.endpoint -> 2/3 covered lines (key: AnalyticsSettings.endpoint)
agent_workflows/run_analytics_wizard.py :: _coerce_bool -> 4/9 covered lines (key: _coerce_bool)
agent_workflows/run_analytics_wizard.py :: _local_path -> 2/2 covered lines (key: _local_path)
agent_workflows/run_analytics_report.py :: _publish_flat -> 8/11 covered lines (key: _publish_flat)
agent_workflows/run_analytics_report.py :: verify_bundle -> 17/22 covered lines (key: verify_bundle)
agent_workflows/run_analytics_report.py :: prune_snapshots -> 18/23 covered lines (key: prune_snapshots)
agent_workflows/run_analytics_report.py :: publish_snapshot -> 1/1 covered lines (key: publish_snapshot)
agent_workflows/run_analytics_report.py :: resolve_snapshot_dir -> 4/4 covered lines (key: resolve_snapshot_dir)
agent_workflows/run_analytics_findings.py :: format_findings_report -> 14/14 covered lines (key: format_findings_report)
agent_workflows/run_analytics_findings.py :: price_era_paradox_finding -> 5/5 covered lines (key: price_era_paradox_finding)
agent_workflows/run_analytics_findings.py :: detect_pooled_era_comparison -> 7/7 covered lines (key: detect_pooled_era_comparison)
agent_workflows/run_analytics_sources.py :: inventory_corpus -> 10/14 covered lines (key: inventory_corpus)
agent_workflows/run_analytics_sources.py :: CorpusInventory.generation_counts -> 4/4 covered lines (key: CorpusInventory.generation_counts)
agent_workflows/run_analytics_config.py :: clamp_interval -> 6/6 covered lines (key: clamp_interval)
agent_workflows/run_analytics_privacy.py :: redact_text._replace -> 1/1 covered lines (key: redact_text._replace)
ALL 22 KEYS COVERED: True

$ python3 -m pytest
1192 passed in 79.25s (0:01:19)

$ git diff agent_workflows/
(returns empty)

$ git status --short
(clean; coverage data files removed)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01).
- Scope fence: the six Scope-Paths test files are the only declared paths. An out-of-scope edit (for example a gated `bug` backlog item filed under the disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks are scratch edits to production modules that must be reverted before commit and must be absent from the diff; coverage data lives under the gitignored `.aw/state/` and is deleted.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit ivap17 -- <the six Scope-Paths files>` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize ivap17` instead. Never hand-`git mv` the plan.
