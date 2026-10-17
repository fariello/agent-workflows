# IPD: Restore behavioral test coverage for run analytics wizard, report, findings, config, sources and privacy

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup groups 16 through 60 of the `b1mx2w` `## Filing plan`) carries 135 production keys that the routine non-slow selection did not reach at baseline HEAD `86f0d88d`, because the suite trim `19313eed` deleted the behavioral test files that drove them. This child owns the run-analytics slice: groups 16 (`run_analytics_wizard.py`, 10 keys), 19 (`run_analytics_report.py`, 5 keys), 21 (`run_analytics_findings.py`, 3 keys), 34 (`run_analytics_sources.py`, 2 keys), 39 (`run_analytics_config.py`, 1 key) and 50 (`run_analytics_privacy.py`, 1 key), 22 keys in all. A mutation that, for example, made `plan_deletion` return `None` or `format_findings_report` return an empty string passes the routine suite today.
- Scope: Restore six deleted test modules from `19313eed^` at their original paths, minus their code-pinning tests, with a neutral privacy canary and `core` markers, so the 22 keys are reached by the routine bare gate. The 22 keys: `run_analytics_wizard.apply_choices`, `read_settings`, `plan_deletion`, `write_settings`, `delete_analytics_artifacts`, `AnalyticsSettings.to_dict`, `_looks_like_secret`, `AnalyticsSettings.endpoint`, `_coerce_bool`, `_local_path`; `run_analytics_report._publish_flat`, `verify_bundle`, `prune_snapshots`, `publish_snapshot`, `resolve_snapshot_dir`; `run_analytics_findings.format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison`; `run_analytics_sources.inventory_corpus`, `CorpusInventory.generation_counts`; `run_analytics_config.clamp_interval`; `run_analytics_privacy.redact_text._replace`. EXCLUDES any production-code change; EXCLUDES restoring `tests/test_run_analytics_cache.py` and `tests/test_run_analytics_privacy_boundary.py` (F-05); EXCLUDES keys of other modules these files happen to reach.
- Scope-Paths: tests/test_run_analytics_wizard.py, tests/test_run_analytics_report.py, tests/test_run_analytics_findings.py, tests/test_run_analytics_config.py, tests/test_run_analytics_e2e.py, tests/test_run_analytics_privacy.py
- Item-Dependencies: none
- Status: reviewed
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
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` against HEAD `f84c3af26`, applied the proposed subset edits to scratch copies under `tests/`, and measured per-key reach (coverage contexts), per-test durations and early-return mutation kills before writing any step; scratch copies and `.coverage` were removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make all 22 run-analytics keys of backlog `q86fxm` (groups 16, 19, 21, 34, 39, 50) reached by the routine bare core-tier run, through restored behavioral tests that build settings, publish and prune snapshots, render findings, inventory a fixture corpus and redact diagnostics, then assert on returned values, written files and raised refusals. Done means an early-return mutation of any of the 22 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Common rule for every E-item below (the RESTORE RULE): create the file from `git show 19313eed^:<path>`; make only the listed edits; add `import pytest` if absent; add the stated `core` marking, inserting a module-level `pytestmark = pytest.mark.core` AFTER the last complete top-level import statement (several of these files end their imports with a parenthesized multi-line `from ... import (...)`); keep every other test body unchanged; after deleting tests, remove any top-level import or constant the deletion leaves unused (the repository's `ruff` pre-commit hook rejects an unused import, and its `--fix` would otherwise rewrite the file mid-commit). Disposition rule if a kept test fails at execution HEAD: do not mark the item performed until it is dispositioned. Record the failure in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.

### Task group 1: restore the analytics modules

- [ ] E-01 Restore `tests/test_run_analytics_wizard.py`. Delete `test_no_optional_install_mechanism_is_built` and `test_deletion_never_composes_the_runs_literal_itself` (both import `tests.test_run_analytics_export._code_lines` and assert substrings of `agent_workflows/run_analytics_wizard.py` source, F-02). Add a module-level `pytestmark = pytest.mark.core` (19 tests, 0.09s summed at authoring).
  - Depends on: none
  - Expected outcome: every kept test passes (19 at authoring and review); the file contains no `_code_lines` and no `agent_workflows/` path string.
  - Execution state: pending

- [ ] E-02 Restore `tests/test_run_analytics_report.py` unchanged except marking with `@pytest.mark.core` exactly these six tests (the cheapest set that both reaches all five report keys and KILLS each one's early-return mutation, F-07): `RefusalTests.test_a_traversing_snapshot_label_is_refused`, `ManifestIsTheCompletenessSignalTests.test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle`, `SnapshotRetentionTests.test_a_directory_we_did_not_write_is_NEVER_pruned`, `SnapshotRetentionTests.test_snapshots_are_pruned_to_the_keep_count` (the only test asserting on `prune_snapshots`' returned list), `SnapshotRetentionTests.test_a_snapshot_manifest_records_immutability` (asserts on `publish_snapshot`'s returned manifest), `PublicationPathTests.test_explicit_flat_publication_is_also_available`. The other 17 tests stay unmarked and run in explicit-path and thorough runs.
  - Depends on: none
  - Expected outcome: every test passes on an explicit-path run (23 at review); exactly the six named tests are selected by `-m core`.
  - Execution state: pending

- [ ] E-03 Restore `tests/test_run_analytics_findings.py` and `tests/test_run_analytics_config.py` unchanged except a module-level `pytestmark = pytest.mark.core` in each (20 and 14 tests, under 0.1s each in total).
  - Depends on: none
  - Expected outcome: every test in both files passes and is core-selected (20 and 14 at review).
  - Execution state: pending

- [ ] E-04 Restore `tests/test_run_analytics_e2e.py`. Delete the five tests of `CanaryDisciplineTests` that read committed files or this file's own text (`test_no_live_corpus_byte_was_copied_into_the_fixture_tree`, `test_no_mutation_case_sleeps_spawns_or_opens_a_socket`, `test_the_committed_fixture_tree_scans_clean_under_the_same_gate_ci_applies`, `test_this_test_module_also_scans_clean`, `test_the_fixture_tree_is_tracked_which_is_why_the_rule_exists`) and `test_the_gate_can_fail_which_is_why_clean_means_something` (its only purpose is to be the control for the two deleted scan tests, and it asserts a `handle` finding that fires only on a machine whose local hints file knows the maintainer handle, F-04). Mark with `@pytest.mark.core` only `FixtureCorpusTests.test_the_corpus_carries_all_four_generations_including_both_legacy_ones` (the one test reaching both `run_analytics_sources` keys, 0.08s). Then, per the RESTORE RULE, delete the definitions the six deletions leave unused: the `FIXTURE_TREE = Path(__file__)...` constant (no kept test reads it, verified at review) and the `import subprocess` line (`ruff check --select F` flags it, F-07). The module docstring prose mentioning `git check-ignore` may stay (it explains why the fixture tree is tracked); E-06 notes the removed checks.
  - Depends on: none
  - Expected outcome: every kept test passes on an explicit-path run (28 at review), exactly the one named test is selected by `-m core`; `rg -n "__file__|ls-files|\"check-ignore\"|^import subprocess" tests/test_run_analytics_e2e.py` returns nothing, and `ruff check --select F tests/test_run_analytics_e2e.py` is clean.
  - Execution state: pending

- [ ] E-05 Restore `tests/test_run_analytics_privacy.py` with a neutral canary set (F-04): change `_HANDLE = "gfa" + "riello"` to `_HANDLE = "some" + "one"` and `_PRIVATE_REPO = "her" + "mes-agent"` to `_PRIVATE_REPO = "example-" + "private-repo"`; in `IndependentDetectorTests.test_control_the_detector_does_flag_every_path_canary_raw` remove `_PRIVATE_REPO` and `_HANDLE` from the raw-canary tuple (neither is a detector-visible value once neutral; the home, macOS, Windows and session-id canaries keep the control's teeth). Delete the four source-reading tests (`test_the_projector_module_itself_is_self_clean`, `test_this_test_file_holds_no_literal_leak`, `test_the_analytics_modules_define_no_detection_ruleset`, `test_no_raw_filelock_or_fcntl_import_in_the_analytics_modules`). Add a module-level `pytestmark = pytest.mark.core`.
  - Depends on: none
  - Expected outcome: every kept test passes (21 at review); `rg -n "riello|mes-agent|__file__|REPO_ROOT / \"agent_workflows\"" tests/test_run_analytics_privacy.py` returns nothing; `aw sanitize --agent` reports `findings":0` once the file is staged or committed (it scans TRACKED files; an untracked file is not scanned, F-07), and before that `leak_sanitizer.scan_text` over the file with `build_ruleset(REPO_ROOT)` returns no finding.
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

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --no-index <(git show 19313eed^:tests/test_run_analytics_wizard.py) tests/test_run_analytics_wizard.py` (or an equivalent diff) showing only the two removed tests, the `pytest` import/`pytestmark` lines and the docstring paragraph; paste the `-v` run listing every kept test PASSED with its summary line; paste the failure produced by the scratch `plan_deletion` return-`None` mutation under `-m core` (reverted afterwards).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` run of `tests/test_run_analytics_report.py` listing every test PASSED and `-m core --collect-only -q` listing exactly the six marked tests; paste the failures, under `-m core` over the six files, from scratch `prune_snapshots` return-`[]` and `publish_snapshot` return-`None` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `-v` runs of both files with every test PASSED and the failures, under `-m core`, from scratch `format_findings_report` return-`""` and `clamp_interval` return-constant mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` run (every kept test PASSED), the `-m core --collect-only -q` line naming the one marked test, the empty `rg` output and clean `ruff check --select F` output named in E-04, and the failure from a scratch `inventory_corpus` return-`None` mutation run against the core-marked test only (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `-v` run (every kept test PASSED), the empty `rg` output named in E-05, `aw sanitize --agent` with `findings":0` run after staging, and the failure under `-m core` from a scratch `redact_text._replace` return-its-input mutation (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the six docstring paragraphs (or `rg -n "q86fxm" <the six files>` showing one hit per file); paste the per-function coverage listing from Required tests showing every one of the 22 keys with nonzero covered lines; paste the bare `python3 -m pytest` summary line with its wall time (26.61s of a 30s budget at review); paste a final empty `git diff agent_workflows/` and a `git status --short` with no coverage data file.
  - Observed evidence:
  - Result: pending

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
