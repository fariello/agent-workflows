# IPD: Triage and resolve the 24 dangling test citations attributable to neither suite-trim commit

- Date: 2026-10-11
- Kind: child
- Concern: Backlog `9vfxhn` reports 19 to 22 dangling `tests/test_*.py` path citations in the live tree that `tools/lost_guard_census.py` Axis A attributes to NEITHER trim commit (`19313eed`, `80db6750c`). Re-measured at authoring HEAD `8caebfd8d` the count is 24. Triage shows only ONE is a genuine stale pointer a reader is invited to follow; the other 23 are synthetic fixture literals inside tests, illustrative placeholder names in comments/docstrings, or an already-exempted past-tense historical mention. The census currently counts all 24 as defects because its declared `tmp_path` exclusion class is described in `EXCLUDED_CLASSES` but never implemented, and its placeholder set holds only `tests/test_x.py` and `tests/test_extra.py`.
- Scope: IN: (a) repoint the one genuine stale citation; (b) make the census honor its declared fixture/placeholder/historical exclusions through an explicit, keyed, reviewable exemption table, reported as a separate count so nothing is hidden; (c) a behavioral test of the exemption over a synthetic git repo; (d) document the new class in `tools/README.md`. OUT: the 75 paths attributable to `19313eed` (owned by backlog `iosmvn` and its sibling items); `CHANGELOG.md`/`DECISIONS.md` (already out of scope as append-only history); `.aw/records/` (immutable); restoring any deleted test.
- Scope-Paths: tools/lost_guard_census.py, tests/test_lost_guard_census.py, tests/test_lift_drift_scan.py, tools/README.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 9vfxhn
- Set: 9vfxhn
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: l4lc6p

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: l4lc6p verified (set 9vfxhn, attempt 1).
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Re-verified at HEAD ca5521479: E-01 command reproduces the 24-row table; census scans itself, so self-acknowledgement added.

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog `9vfxhn`; triaged all 24 NEITHER-attributed paths at HEAD `8caebfd8d`.

## Goal

Drive the census's "Attributable to NEITHER" Axis A count from 24 to 0 at execution HEAD by fixing the one real stale pointer and by recording every non-citation as an explicit keyed exemption with a reason, so the remaining count means "a real dangling citation" and any new one is visible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-measure and repoint the genuine stale citation

- [x] E-01 Re-measure the NEITHER set at execution HEAD with `python3 -c "from pathlib import Path; from collections import defaultdict; from tools.lost_guard_census import scan_axis_a; r=scan_axis_a(Path('.'),['80db6750c','19313eed']); d=defaultdict(set); [d[t].add(f) for f,t in r.hits if t in r.attr_neither]; [print(p,sorted(d[p])) for p in r.attr_neither]"` and record the list. Compare to the 24-row table in Findings; any path not in the table is dispositioned by the same rules (genuine -> repoint/remove; fixture/placeholder/historical -> exemption in E-03) and recorded.
  - Depends on: none
  - Expected outcome: the recorded list equals the Findings table, or each delta row carries a recorded disposition.
  - Execution state: performed

- [x] E-02 In `tests/test_lift_drift_scan.py` class `LiftDriftScanGuardTests` docstring, replace the stale pointer `tests/test_liftaudit_drift.py` (a file that has never existed in git history) with `tests/test_liftaudit_stop_halts_run.py`, the file executed plan `96xtmi` F-16 names as the behavioral replacement (`LiftauditStopHaltsRunTests::test_oc_run_queue_stop_now_force_level4`).
  - Depends on: E-01
  - Expected outcome: `grep -n "test_liftaudit_drift" tests/test_lift_drift_scan.py` prints nothing; the docstring names an existing file.
  - Execution state: performed

### Task group 2: Implement the declared exclusions in the census

- [x] E-03 In `tools/lost_guard_census.py`: (i) extend `EXCLUDED_PLACEHOLDER_PATHS` with the generic illustrative names `tests/test_foo.py`, `tests/test_secret.py`, `tests/test_demo.py` and update the `placeholders` text in `EXCLUDED_CLASSES` to list them; (ii) add a module constant `ACKNOWLEDGED_NON_CITATIONS: dict[tuple[str, str], str]` keyed `(carrying_file, cited_path) -> reason`, populated with every Findings row dispositioned FIXTURE or HISTORICAL, with a reason string per key; (iii) in `scan_axis_a`, skip a hit whose `(rel_path, target)` key is in that table, collecting it into a new `AxisAResult` field `acknowledged_hits: list[tuple[str, str]]` instead of `hits`/`cited_paths`; (iv) in `print_axis_a`, print `Acknowledged non-citations (keyed exemptions): N hits` under CENSUS RESULTS, and add an `acknowledged` entry to `EXCLUDED_CLASSES` so `print_scan_definition` declares it. (v) SELF-CITATION: `tools/lost_guard_census.py` is itself inside the scan roots (`scan_target_files` returns it, measured at review), so every cited-path string written into `ACKNOWLEDGED_NON_CITATIONS` would become a NEW NEITHER hit carried by the census module itself and the goal of 0 would be unreachable. So `scan_axis_a` must also route a hit into `acknowledged_hits` when its carrying file is the census module's own repo-relative path AND its target is a cited path of some table key (the table acknowledging its own entries); do NOT exclude the census module from the scan wholesale, which would hide any genuine citation in it. (vi) Print, beside the acknowledged line, the number of table keys that matched no hit (`Unused acknowledgements: M keys`), so an acknowledgement that has gone stale is visible rather than silently dead. Keep the `[review measured ...]` labels unchanged.
  - Depends on: E-01
  - Expected outcome: `python3 tools/lost_guard_census.py --axis a` prints `Attributable to NEITHER:   0 paths` (after E-04 and E-05 have also landed, since both add text to scanned files), a nonzero acknowledged-hits line and `Unused acknowledgements: 0 keys`; the `19313eed` count is unchanged from the E-01 measurement.
  - Execution state: performed

- [x] E-04 Add a behavioral test to `tests/test_lost_guard_census.py` class `LostGuardCensusSyntheticRepoTests`: in the synthetic repo, write a carrier at a carrying-file path that is a key of `ACKNOWLEDGED_NON_CITATIONS` (e.g. `tests/test_verifier_evidence.py` citing `tests/test_two.py`), a carrier citing `tests/test_foo.py`, and keep the existing `tests/test_unrelated_missing.py` citation in `agent_workflows/worker.py`; assert via `scan_axis_a` that the keyed path is absent from `dangling_paths`/`attr_neither` and present in `acknowledged_hits`, the placeholder is absent from `cited_paths`, and `tests/test_unrelated_missing.py` is STILL in `attr_neither` (the exemption is keyed, not global). Also assert the CLI `--axis a` output contains the acknowledged line (run as a subprocess with `cwd=repo`, the pattern `test_cli_summary_output_and_rules` uses). LITERAL HYGIENE: this test file is itself scanned, so every `tests/test_*.py` literal it newly introduces must be either a member of `EXCLUDED_PLACEHOLDER_PATHS`, an existing `(tests/test_lost_guard_census.py, <path>)` key, or a new key added to the table in the same change; re-run E-03's command after this item to confirm NEITHER stays 0.
  - Depends on: E-03
  - Expected outcome: the new test passes; an in-process `mock.patch.object(lost_guard_census, "ACKNOWLEDGED_NON_CITATIONS", {})` (or equivalent rebinding from a gitignored `tmp/` scratch script) makes it fail, without editing the source file.
  - Execution state: performed

- [x] E-05 Document the acknowledged-exemption class and the extended placeholder set in the `lost_guard_census.py` section of `tools/README.md` (what qualifies: fixture literals inside tests, illustrative placeholders, past-tense historical mentions already exempted by `tests/test_docs_test_citations.py`; what does not: any present-tense pointer a reader is invited to follow), and the rule that a NEW acknowledgement is a reviewed table edit with a reason, never a pattern. Name example placeholders only from `EXCLUDED_PLACEHOLDER_PATHS` (the README is scanned too). `tools/README.md` is user-facing prose: no em or en dashes.
  - Depends on: E-03
  - Expected outcome: README section names the class and the rule.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The scanner is `tools/lost_guard_census.py` (`scan_axis_a`, `AxisAResult`, `EXCLUDED_PLACEHOLDER_PATHS`, `EXCLUDED_CLASSES`, `print_axis_a`); its tests in `tests/test_lost_guard_census.py` build a throwaway git repo (`_setup_repo`) and must not reference the live tree or real trim shas.
- Precedent for keyed `(document, citation) -> rationale` exemptions: `tests/test_docs_test_citations.py` `HISTORICAL_EXEMPTIONS`, with the present-tense vs past-tense rule in its module docstring.
- Tests must exercise behavior and never read production source (GUIDING_PRINCIPLES P16).
- The scan roots include `tools/` and `tests/` (`SCAN_ROOTS`), so the census module, its test file and `tools/README.md` are all scanned; any path literal this plan writes into them is itself a candidate citation (E-03 (v), E-04, E-05).
- Sibling plan `1ub8ex` (`uncitedaudit-01`, reviewed) declares the same `tools/lost_guard_census.py`, `tests/test_lost_guard_census.py`, `tools/README.md` and adds an `--uncited` section that consumes `scan_axis_a(...).cited_paths`. This plan moves acknowledged hits OUT of `cited_paths`, which changes `compute_reach_partition`'s cited/uncited split only for acknowledged non-citations (none of which names a trim-deleted file, since all are NEITHER-attributed), so the two compose; the sites are otherwise disjoint and each runner item gets an isolated worktree, so no `- Item-Dependencies:` edge is needed. Uncitedaudit 02-04 and `ww744p` touch only `tools/README.md`, in other sections.
- Run the suite bare: `python3 -m pytest`; narrowed runs use `-o addopts=""`.
- Cite code by symbol, never by bare line number.

## Findings

Measured at HEAD `8caebfd8d` (24 NEITHER paths; `git log --all -- <path>` shows only two ever existed). Disposition key: GENUINE = stale present-tense pointer; FIXTURE = synthetic literal in a test's own data; PLACEHOLDER = generic illustrative name; HISTORICAL = past-tense mention already exempted.

| ID | Cited path | Carrying file(s) | Ever existed | Disposition |
|---|---|---|---|---|
| F-01 | tests/test_liftaudit_drift.py | tests/test_lift_drift_scan.py (class docstring) | no | GENUINE: repoint to tests/test_liftaudit_stop_halts_run.py (E-02) |
| F-02 | tests/test_wtiso_characterization.py | docs/wtiso-state-taxonomy.md, tests/test_docs_test_citations.py | yes, deleted d4dd6b880 | HISTORICAL: already in `HISTORICAL_EXEMPTIONS`; keyed exemption (E-03) |
| F-03 | tests/test_rununify_initialize_run_characterization.py | tests/test_finalize_sendback.py (`REDUCTION_REFUSAL_SINGULAR` fixture string) | yes, deleted 7ebc29645 | FIXTURE (E-03) |
| F-04 | tests/test_1.py, tests/test_2.py | tests/test_finalize_sendback.py | no | FIXTURE (E-03) |
| F-05 | tests/test_a.py | tests/test_scope_match.py | no | FIXTURE (E-03) |
| F-06 | tests/test_deleted_a.py, tests/test_deleted_b.py, tests/test_mixed.py, tests/test_modified_c.py, tests/test_unrelated_missing.py | tests/test_lost_guard_census.py (`_setup_repo`) | no | FIXTURE (E-03) |
| F-07 | tests/test_deleted_suite.py, tests/test_e2e_nonexistent.py, tests/test_missing_file.py, tests/test_real_file.py | tests/test_check_engine_test_citation.py | no | FIXTURE (E-03) |
| F-08 | tests/test_new.py | tests/test_scope_path_target_stale.py | no | FIXTURE (E-03) |
| F-09 | tests/test_release_gate.py | tests/test_verifier_corroboration.py (`claimed_command`) | no | FIXTURE (E-03) |
| F-10 | tests/test_spec.py | tests/test_agy_runipd_cli.py (mock `TargetFile`) | no | FIXTURE (E-03) |
| F-11 | tests/test_two.py, tests/test_three.py, tests/test_verify.py | tests/test_verifier_evidence.py | no | FIXTURE (E-03) |
| F-12 | tests/test_foo.py | agent_workflows/ipd_authoring.py (Scope-Paths example comment) and 8 test files | no | PLACEHOLDER (E-03) |
| F-13 | tests/test_secret.py | agent_workflows/ipd_lifecycle.py (`scope_entry_is_literal_file` docstring example) | no | PLACEHOLDER (E-03) |
| F-14 | tests/test_demo.py | tests/support.py and 7 test files | no | PLACEHOLDER (E-03) |

The census's own `EXCLUDED_CLASSES["tmp_path"]` claims fixture paths are excluded, but `scan_axis_a` filters only `EXCLUDED_PLACEHOLDER_PATHS`; that gap is why F-03..F-11 count.

## Proposed changes (ordered, validatable)

1. E-01: re-measure; disposition any delta.
2. E-02: repoint F-01.
3. E-03: placeholders + keyed exemption table + separate acknowledged count.
4. E-04: synthetic-repo behavioral test of the exemption.
5. E-05: README documentation.

## Deferred / out of scope (with reason)

- The 75 `19313eed`-attributed paths: owned by backlog `iosmvn` and its dedicated sibling items; mixing them here would duplicate that work.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- `CHANGELOG.md`/`DECISIONS.md` history hits: append-only records, already reported separately by the census.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Restoring any deleted suite: none of the 24 paths names lost behavioral coverage (F-01's behavior is pinned by `tests/test_liftaudit_stop_halts_run.py` per `96xtmi`).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none; fixture strings in tests are NOT rewritten (they are correct test data), only acknowledged.
- Under-scope: none; every one of the 24 rows has a disposition and an E-item.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_lost_guard_census.py tests/test_lift_drift_scan.py tests/test_docs_test_citations.py -v` (E-02, E-04).
- `python3 tools/lost_guard_census.py --axis a` showing NEITHER 0 (E-03).
- Bare suite `python3 -m pytest` before E-02 (baseline) and after E-05 (regression), same failing-test set by name.

## Spec / documentation sync

`tools/README.md` updated (E-05). No spec governs `tools/lost_guard_census.py`; no `.spec.md` is touched.

## Open questions

### OQ-01: Should fixture literals be rewritten to an excluded placeholder instead of acknowledged?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Rewriting test data in ~10 unrelated test modules widens scope and risks behavior changes in those tests; the keyed-exemption precedent (`tests/test_docs_test_citations.py` `HISTORICAL_EXEMPTIONS`) is established and keeps each acknowledgement reviewable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted E-01 command output listing the NEITHER paths with carriers, and a recorded disposition for any row not in Findings.
  - Observed evidence:
```
tests/test_1.py ['tests/test_finalize_sendback.py']
tests/test_2.py ['tests/test_finalize_sendback.py']
tests/test_a.py ['tests/test_scope_match.py']
tests/test_always_fails_extra.py ['tests/test_mutation_probe.py']
tests/test_cited.py ['tests/test_lost_guard_census.py']
tests/test_deleted_a.py ['tests/test_lost_guard_census.py']
tests/test_deleted_b.py ['tests/test_lost_guard_census.py']
tests/test_deleted_suite.py ['tests/test_check_engine_test_citation.py']
tests/test_demo.py ['tests/support.py', 'tests/test_capture_command_contract.py', 'tests/test_finalize_empty_declared_scope.py', 'tests/test_finalize_trailer_attribution.py', 'tests/test_finidem_reusable_not_finalized.py', 'tests/test_ipd_lifecycle_cli.py', 'tests/test_lifecycle_holder_gate.py', 'tests/test_lifecycle_lane_nudge.py']
tests/test_e2e_nonexistent.py ['tests/test_check_engine_test_citation.py']
tests/test_flaky.py ['tests/test_mutation_probe.py']
tests/test_foo.py ['agent_workflows/ipd_authoring.py', 'tests/test_hook_and_suite_fix_it.py', 'tests/test_ipd_lint.py', 'tests/test_ipd_schema.py', 'tests/test_plan_priority_required.py', 'tests/test_resolve_plan_path_typed.py', 'tests/test_runner_stop_interactive.py', 'tests/test_runners_monitor.py', 'tests/test_scope_path_target_stale.py', 'tests/test_spec_edit_ack_gate.py']
tests/test_gone.py ['tests/test_lost_guard_census.py']
tests/test_liftaudit_drift.py ['tests/test_lift_drift_scan.py']
tests/test_m.py ['tests/test_mutation_probe.py', 'tools/README.md']
tests/test_missing_file.py ['tests/test_check_engine_test_citation.py']
tests/test_mixed.py ['tests/test_lost_guard_census.py']
tests/test_modified_c.py ['tests/test_lost_guard_census.py']
tests/test_new.py ['tests/test_scope_path_target_stale.py']
tests/test_now_collected.py ['tests/test_uncollected_test_modules.py']
tests/test_other.py ['tests/test_mutation_probe.py']
tests/test_present.py ['tests/test_lost_guard_census.py']
tests/test_real_file.py ['tests/test_check_engine_test_citation.py']
tests/test_recreated.py ['tests/test_lost_guard_census.py']
tests/test_regular.py ['tests/test_uncollected_test_modules.py']
tests/test_release_gate.py ['tests/test_verifier_corroboration.py']
tests/test_rununify_initialize_run_characterization.py ['tests/test_finalize_sendback.py']
tests/test_secret.py ['agent_workflows/ipd_lifecycle.py']
tests/test_sleep.py ['tests/test_mutation_probe.py']
tests/test_spec.py ['tests/test_agy_runipd_cli.py']
tests/test_three.py ['tests/test_verifier_evidence.py']
tests/test_two.py ['tests/test_verifier_evidence.py']
tests/test_unrelated_missing.py ['tests/test_lost_guard_census.py']
tests/test_unused.py ['tests/test_mutation_probe.py']
tests/test_verify.py ['tests/test_verifier_evidence.py']
tests/test_wtiso_characterization.py ['docs/wtiso-state-taxonomy.md', 'tests/test_docs_test_citations.py']
```
Recorded disposition for 12 delta rows not in authoring HEAD Findings table:
- `tests/test_always_fails_extra.py` (`tests/test_mutation_probe.py`): FIXTURE (synthetic test repo fixture in mutation probe tests)
- `tests/test_cited.py` (`tests/test_lost_guard_census.py`): FIXTURE (synthetic test repo fixture in uncited inventory tests)
- `tests/test_flaky.py` (`tests/test_mutation_probe.py`): FIXTURE (synthetic test repo fixture in mutation probe tests)
- `tests/test_gone.py` (`tests/test_lost_guard_census.py`): FIXTURE (synthetic test repo fixture in uncited inventory tests)
- `tests/test_m.py` (`tests/test_mutation_probe.py`, `tools/README.md`): FIXTURE / PLACEHOLDER (synthetic test repo fixture and CLI documentation example)
- `tests/test_now_collected.py` (`tests/test_uncollected_test_modules.py`): FIXTURE (synthetic test candidate fixture)
- `tests/test_other.py` (`tests/test_mutation_probe.py`): FIXTURE (synthetic test repo fixture in mutation probe tests)
- `tests/test_present.py` (`tests/test_lost_guard_census.py`): FIXTURE (synthetic test repo fixture in uncited inventory tests)
- `tests/test_recreated.py` (`tests/test_lost_guard_census.py`): FIXTURE (synthetic test repo fixture in uncited inventory tests)
- `tests/test_regular.py` (`tests/test_uncollected_test_modules.py`): FIXTURE (synthetic test candidate fixture)
- `tests/test_sleep.py` (`tests/test_mutation_probe.py`): FIXTURE (synthetic test repo fixture in mutation probe tests)
- `tests/test_unused.py` (`tests/test_mutation_probe.py`): FIXTURE (synthetic test repo fixture in mutation probe tests)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff tests/test_lift_drift_scan.py` showing the repoint, empty output of `grep -n test_liftaudit_drift tests/test_lift_drift_scan.py`, and `ls tests/test_liftaudit_stop_halts_run.py` succeeding.
  - Observed evidence:
```diff
diff --git a/tests/test_lift_drift_scan.py b/tests/test_lift_drift_scan.py
index a3b4da9cd..ec7ddb4e2 100644
--- a/tests/test_lift_drift_scan.py
+++ b/tests/test_lift_drift_scan.py
@@ -7,7 +7,7 @@ class LiftDriftScanGuardTests(unittest.TestCase):
     """Retired under IPD 96xtmi (source-guard cleanup).

     The AST drift scans pinning runner_shared.py source were deleted in favor of
-    behavioral tests in tests/test_liftaudit_drift.py and type checking.
+    behavioral tests in tests/test_liftaudit_stop_halts_run.py and type checking.
     """

     pass
```
Command `grep -n "test_liftaudit_drift" tests/test_lift_drift_scan.py` output: (empty, exit 1).
Command `ls tests/test_liftaudit_stop_halts_run.py` output:
`tests/test_liftaudit_stop_halts_run.py`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `python3 tools/lost_guard_census.py --axis a` output (produced by `print_axis_a`), run AFTER E-04 and E-05, showing `Attributable to NEITHER:   0 paths`, the acknowledged-hits line, `Unused acknowledgements: 0 keys`, the `acknowledged` class in the scan definition, and a `19313eed` count equal to the E-01 measurement; plus the pasted E-01 command re-run printing no NEITHER path (in particular none carried by `tools/lost_guard_census.py`, `tests/test_lost_guard_census.py` or `tools/README.md`).
  - Observed evidence:
```
==============================================================================
AXIS A: DANGLING TEST FILE PATH CITATIONS
==============================================================================
DECLARED SCAN DEFINITION:
  Roots:             README.md, CONTRIBUTING.md, RELEASING.md, GUIDING_PRINCIPLES.md, AGENTS.md, agent_workflows, tests, docs, tools, .github
  Allowed ext:       .py, .md, .rst, .txt, .yaml, .yml, .sh, .toml, .json
  Hit counting rule: raw hits
  Exclusions:
    - records: .aw/records/ (immutable terminal records whose citations reflect author-time state)
    - placeholders: tests/test_x.py, tests/test_extra.py, tests/test_foo.py, tests/test_secret.py, and tests/test_demo.py (illustrative docstring/comment examples)
    - tmp_path: temporary directory fixture paths constructed under tmp_path
    - acknowledged: acknowledged non-citations (keyed carrier-target exemptions with recorded rationale)
    - append_only_history: CHANGELOG.md and DECISIONS.md (append-only dated history records; reported separately out of scope)

CENSUS RESULTS:
  Distinct cited test paths:    185
  Distinct dangling test paths: 76
  Total dangling path hits:     482
  Carrying files:               117
  Acknowledged non-citations (keyed exemptions): 125 hits [Unused acknowledgements: 0 keys]

TRIM ATTRIBUTION:
  Attributable to 19313eed: 76 paths [review measured 82 at aa5398132]
  Attributable to 80db6750c: 0 paths (STRUCTURAL ZERO: commit deleted 0 files)
  Attributable to NEITHER:   0 paths [review measured 22 at aa5398132]

EXCLUDED OUT-OF-SCOPE HISTORY FILES (CHANGELOG.md, DECISIONS.md):
  Total history hits:             83 hits
  Distinct dangling history paths: 18 paths
  [Note: Both files are append-only dated history whose citations were valid when written.]
```
Re-running E-01 command:
`python3 -c "from pathlib import Path; from collections import defaultdict; from tools.lost_guard_census import scan_axis_a; r=scan_axis_a(Path('.'),['80db6750c','19313eed']); d=defaultdict(set); [d[t].add(f) for f,t in r.hits if t in r.attr_neither]; [print(p,sorted(d[p])) for p in r.attr_neither]"`
Output: (empty, 0 paths output).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_lost_guard_census.py tests/test_docs_test_citations.py -v` output with the new test PASSED, plus pasted failing output of the new test with `ACKNOWLEDGED_NON_CITATIONS` rebound to `{}` in-process (no source edit; any scratch script under gitignored `tmp/` and deleted, shown by `git status --short`).
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
cachedir: .pytest_cache
Using --randomly-seed=880350387
rootdir: <repo>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 7 items                                                             collected 8 items

tests/test_docs_test_citations.py::test_published_docs_test_citations_exist PASSED [ 12%]
tests/test_lost_guard_census.py::LostGuardCensusBehavioralTests::test_classifier_bidirectional_and_mixed PASSED [ 25%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_mixed_candidate_annotation_contract PASSED [ 37%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_cli_summary_output_and_rules PASSED [ 50%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_uncited_inventory_and_cli PASSED [ 62%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_acknowledged_non_citations_and_placeholders PASSED [ 75%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_synthetic_axes_attribution PASSED [ 87%]
tests/test_lost_guard_census.py::LostGuardCensusSyntheticRepoTests::test_synthetic_census_computation PASSED [100%]

============================== 8 passed in 2.93s ===============================
```
Failure output with `ACKNOWLEDGED_NON_CITATIONS` rebound to `{}` in-process:
```
test_acknowledged_non_citations_and_placeholders (tests.test_lost_guard_census.LostGuardCensusSyntheticRepoTests.test_acknowledged_non_citations_and_placeholders)
Assert keyed acknowledged non-citations and placeholders behave correctly. ... [main (root-commit) 4b416e4] initial before tree
 6 files changed, 17 insertions(+)
 create mode 100644 README.md
 create mode 100644 agent_workflows/worker.py
 create mode 100644 tests/test_deleted_a.py
 create mode 100644 tests/test_deleted_b.py
 create mode 100644 tests/test_mixed.py
 create mode 100644 tests/test_modified_c.py
[main 8115b12] trim commit
 4 files changed, 12 deletions(-)
 delete mode 100644 tests/test_deleted_a.py
 delete mode 100644 tests/test_deleted_b.py
 delete mode 100644 tests/test_mixed.py
FAIL

======================================================================
FAIL: test_acknowledged_non_citations_and_placeholders (tests.test_lost_guard_census.LostGuardCensusSyntheticRepoTests.test_acknowledged_non_citations_and_placeholders)
Assert keyed acknowledged non-citations and placeholders behave correctly.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "tests/test_lost_guard_census.py", line 253, in test_acknowledged_non_citations_and_placeholders
    self.assertIn(
    ~~~~~~~~~~~~~^
        ("tests/test_verifier_evidence.py", "tests/test_two.py"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        axis_a.acknowledged_hits,
        ^^^^^^^^^^^^^^^^^^^^^^^^^
        "Keyed non-citation must be recorded in acknowledged_hits",
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: ('tests/test_verifier_evidence.py', 'tests/test_two.py') not found in [] : Keyed non-citation must be recorded in acknowledged_hits

----------------------------------------------------------------------
Ran 1 test in 0.073s

FAILED (failures=1)
```
No git edits were made during failure demo (`git status --short` shows no untracked files).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff tools/README.md` showing the acknowledged class and extended placeholder set, and the bare-suite `python3 -m pytest` summary lines from a baseline taken on the tree as found before E-02 and after E-05, with the failing-test set identical by name (do not fix, skip or deselect other parties' failures) and the passed count not lower.
  - Observed evidence:
~~~diff
diff --git a/tools/README.md b/tools/README.md
index d926715f3..02e9cf38f 100644
--- a/tools/README.md
+++ b/tools/README.md
@@ -281,6 +281,24 @@ The tool provides an audit that distinguishes between deliberate code-pin test r

 The tool provides an audit that distinguishes between deliberate code-pin test retirements (tests pinning AST or internal implementation details, which must never be restored per GUIDING_PRINCIPLES P16) and genuine behavioral coverage gaps. It measures test removals across both deleted and modified files using multiset difference, computes reach bounds, and cross-references live backlog items to deduplicate known issues.

+### Exclusions and Acknowledged Non-Citations
+
+Axis A scans repository files for test path citations and flags dangling references. To prevent false positives while keeping the audit strict, the scanner defines two non-defect categories:
+
+1. **Placeholders:** Generic illustrative paths used in docstrings, schema examples, and comments. The recognized placeholder set comprises `tests/test_x.py`, `tests/test_extra.py`, `tests/test_foo.py`, `tests/test_secret.py`, and `tests/test_demo.py`.
+2. **Acknowledged non-citations (keyed exemptions):** Explicit, reviewed table entries in `ACKNOWLEDGED_NON_CITATIONS` keyed by `(carrying_file, cited_path)` mapping to an explanatory rationale.
+
+What qualifies for an acknowledgement:
+- Synthetic fixture literals inside test data or mock objects that construct non-existent test paths to test harness behavior.
+- Illustrative placeholders in tool or library documentation.
+- Deliberate past-tense historical mentions where surrounding prose already explains that the suite was retired or deleted (and which are already exempted by `tests/test_docs_test_citations.py`).
+
+What does NOT qualify:
+- Any present-tense pointer a reader or maintainer is invited to follow or run.
+
+Rule for new exemptions:
+A new acknowledgement must always be an explicit, reviewed table entry with a specific carrying file, target path, and reason. Blanket file-level exclusions or regex pattern exemptions are strictly prohibited to ensure every exemption remains auditable and visible.
+
 ### Usage

 ```bash
~~~
Bare-suite `python3 -m pytest` before E-02:
`8023 passed, 4 skipped, 18 xfailed, 3 warnings in 908.45s (0:15:08)`
Bare-suite `python3 -m pytest` after E-05:
`8024 passed, 4 skipped, 18 xfailed, 3 warnings in 440.97s (0:07:20)`
Failing-test set identical by name: 0 failed in baseline, 0 failed in regression. Passed count increased by 1 (8024 >= 8023).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: OQ-01 is resolved; none remain. `- Scope-Paths:` is a DECLARATION reconciled at finalize: an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, not a reason to stop. HONESTY RULE: every `V-*` item MUST paste the ACTUAL command or runner output; a claimed pass with no output does not satisfy it. Start with `aw ipd begin`. Commit only through `aw commit l4lc6p -- <paths>` limited to the declared Scope-Paths plus this plan's lifecycle files (never `git add -A`, `-a`, or `--no-verify`), verify the staged set with `git diff --cached --name-only` first, and never push. The terminal transition is MANDATORY and its owner is conditional: under `aw oc run` / `aw agy run` the runner performs the finalize after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; executed by hand, the executor runs `aw ipd finalize`. Never hand-roll the move or `git mv` this plan into `executed/`; it happens only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with pasted evidence. Backlog `9vfxhn` carries no `- Blocks-Release:` gate, so none is inherited; it closes through the handoff route, not by hand.
