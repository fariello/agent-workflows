# IPD: Fix aw doctor's environment probe: it reads three nonexistent paths and reports a healthy repo as not installed

- Date: 2026-09-12
- Kind: child
- Concern: `aw doctor`'s environment probe resolves the installed VERSION, the preset, and the records backend from paths that do not exist in either supported layout, so it reports a correctly installed repo as `not installed` and emits a false `doctor.version-not-installed` finding.
- Scope: Repoint `doctor.probe_environment`'s three misresolved reads at the canonical locations, delegating version resolution to the single existing authority (`engine.read_installed_version`) instead of a second divergent path list; add regression tests that fail on the current code.
- Scope-Paths: agent_workflows/doctor.py, agent_workflows/cli.py, agent_workflows/project_context.py, tests/test_doctor.py, tests/test_cli.py, tests/test_renderer_boundary.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: doctorprobe
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: h90ij1
- From-Backlog: hdhzr2
- Blocks-Release: f33nrj

## Workflow history
- 2026-09-22 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: h90ij1 verified (set doctorprobe, attempt 1). [Scope reconciliation - widened-scope agent_workflows/project_context.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run); widened-scope tests/test_renderer_boundary.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run); in-scope-unmodified tests/test_cli.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-09-12 to-review (opencode): authored from backlog item hdhzr2; graduated with measured evidence and repo-cited root cause.
- 2026-09-12 draft (opencode): created.

## Goal

Make `aw doctor` report the framework state a repo actually has. Today the one command a user runs to check install health misreports a healthy install as `not installed`, and also blanks the preset and records backend, because three reads in `probe_environment` point at paths that no layout ever creates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Repoint the misresolved reads

- [x] E-01 In `agent_workflows/doctor.py`, replace the hand-rolled VERSION probe (currently `repo_root/".aw"/"VERSION"` falling back to `repo_root/".agents"/"VERSION"`, doctor.py:355-357) with a call to `engine.read_installed_version(repo_root)`, which already probes the three real locations in priority order (engine.py:5705-5719). Do not duplicate the path list; `doctor.py` already imports `engine` (it calls `engine.resolve_source_root` at doctor.py:366).
  - Depends on: none
  - Expected outcome: `probe_environment(repo).installed_version` returns the same value `engine.read_installed_version(repo)` returns, for a repo whose VERSION sits at any of `.aw/system/VERSION`, `.aw/system/workflows/VERSION`, or `.agents/workflows/VERSION`.
  - Execution state: performed

- [x] E-02 Add ONE shared project-config reader (a small module-level helper, placed where both `doctor.py` and `cli.py` can import it without a cycle) that resolves the repo's `preset` and `records_backend`, and repoint `doctor.probe_environment` at it. The current probe reads `repo_root/".aw"/"config.json"` then `repo_root/".agents"/"config.json"` (doctor.py:341-343); NEITHER exists in the `.aw` layout. The canonical project config is `.aw/config/project.json` (config.py:1056 and config.py:1115 both resolve `Path(repo_root)/".aw"/"config"/"project.json"`). Note BOTH keys are present there, and `records_backend` ALSO appears in `.aw/config/config.json`; the helper must therefore define and document an explicit precedence rather than reading whichever file it happens to find (see OQ-02). Keep the legacy `.agents/config.json` fallback for an un-migrated repo.
  - Depends on: E-01
  - Expected outcome: on this repo, `probe_environment(".").preset == "private-target"` and `.backend == "repository"`, instead of the current `None` for both, with the precedence documented in the helper's docstring.
  - Execution state: performed

- [x] E-05 Repoint `cli._collect_repo_status_details` (cli.py:6219-6226) at the SAME shared helper from E-02. It contains the identical defect, reading `repo/(".aw" if has_aw else ".agents")/"config.json"`, a file that does not exist in the `.aw` layout, so `aw status` reports `preset=None`/`backend=None` for every correctly installed repo. Measured on this repo: `_collect_repo_status_details(Path("."), "1.3.0")` returns `preset: None`, `backend: None` while `installed: 1.2.1`. Fixing doctor alone would leave the same wrong answer reachable from a second command, which is exactly the duplicate-authority pattern E-01 exists to eliminate.
  - Depends on: E-02
  - Expected outcome: `_collect_repo_status_details` returns `preset="private-target"` and `backend="repository"` for this repo, sourced from the same helper doctor uses, so the two commands cannot diverge.
  - Execution state: performed

### Task group 2: Regression tests

- [x] E-03 Add a test to `tests/test_doctor.py` asserting `probe_environment` agrees with `engine.read_installed_version` on a fixture repo that has ONLY `.aw/system/VERSION`. This test must fail against the pre-fix code; confirm that before fixing.
  - Depends on: E-01
  - Expected outcome: a named test that fails on the current implementation and passes after E-01.
  - Execution state: performed

- [x] E-04 Add a test asserting that a correctly installed non-source fixture repo produces NO `doctor.version-not-installed` drift entry. This is the user-visible symptom and is a distinct surface from E-03: E-03 covers the read, E-04 covers the finding the read drives (doctor.py:371-382).
  - Depends on: E-01, E-02
  - Expected outcome: a named test that fails on the current implementation and passes after the fix.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Version resolution has ONE authority: `engine.read_installed_version` (engine.py:5705), whose probe order is `.aw/system/VERSION`, `.aw/system/workflows/VERSION`, `.agents/workflows/VERSION`. `cli.py`, `versioning.status`, and `check_engine.check_system_layout` all consume it. `doctor.py` is the sole divergent reader, which is why only doctor is wrong.
- The suite is `unittest`-style with `tests/support.py` helpers (`init_repo` at support.py:92). `tests/test_doctor.py` exists (179 lines) and is the right home.
- Most installer/doctor tests carry `pytestmark = pytest.mark.slow` and are DESELECTED by a bare `python3 -m pytest` (addopts includes `-m 'not slow'`). Validation must therefore run the file explicitly or via `make test-all`, or the run will silently report success having executed nothing.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The VERSION probe reads two paths that no layout creates. | doctor.py:355-357 reads `.aw/VERSION` then `.agents/VERSION`. The real locations are `.aw/system/VERSION`, `.aw/system/workflows/VERSION`, `.agents/workflows/VERSION` (engine.py:5708-5712). |
| F-02 | Measured on this repo: doctor disagrees with engine on a repo that IS installed. | `engine.read_installed_version` returns `1.2.1`; `doctor.probe_environment(".").installed_version` returns `None`. |
| F-03 | The defect is MASKED in this repo, which is why no test caught it. | doctor.py:371 gates the drift on `not res.is_source_repo`, so the framework's own checkout never emits the finding. A real target repo does. |
| F-04 | Measured on a real target: a correctly migrated repo is reported as not installed. | On an upgrade-rehearsal sandbox built from a real 1.2.1 repo, with `.aw/system/VERSION` present: `Version: not installed (packaged: 1.3.0rc2.dev2553+g87759153) [not-installed]`. |
| F-05 | The same block misreads the project config, blanking two more fields. | doctor.py:341-343 reads `.aw/config.json`, which does not exist; the canonical path is `.aw/config/project.json` (config.py:1056, config.py:1115). Measured: `doctor preset: None` / `doctor backend: None` while `.aw/config/project.json` contains `"preset": "private-target"`. |
| F-06 | `--check-pypi` is unaffected and must not be changed. | doctor.py:387-395 deliberately compares against `packaged_version` (the RUNNING package), not the per-repo marker, with a comment stating why. Only the installed-marker reads are wrong. |
| F-07 | The SAME wrong config read exists in a SECOND consumer, so this is not a doctor-only defect (found in review, PR-001). | `cli._collect_repo_status_details` reads `repo/(".aw" if has_aw else ".agents")/"config.json"` (cli.py:6219-6226), which does not exist in the `.aw` layout. Measured: it returns `preset: None`, `backend: None` for this correctly installed repo. It feeds `aw status` (called at cli.py:6367). |
| F-08 | `records_backend` is present in BOTH candidate config files, so a naive repoint could silently pick the wrong one (found in review, PR-004). | `.aw/config/config.json` contains `{"records_backend": "repository"}`; `.aw/config/project.json` contains a `records_backend` key too, alongside `preset`. Precedence must be explicit, not incidental. |

## Proposed changes (ordered, validatable)

1. Delegate the VERSION read to `engine.read_installed_version` (E-01), removing the divergent path list rather than extending it. Extending it would leave two authorities that can drift again.
2. Introduce ONE shared project-config reader with documented precedence and repoint doctor at it (E-02).
3. Repoint the second consumer, `cli._collect_repo_status_details`, at that same helper (E-05), so `aw doctor` and `aw status` cannot give different answers.
4. Add a test binding doctor's reading to engine's (E-03).
5. Add a test asserting no false `version-not-installed` finding on a healthy fixture (E-04).

## Deferred / out of scope (with reason)

- The `.agents/VERSION` and `.agents/config.json` fallbacks are RETAINED, not deleted. They are harmless (they simply never match) and removing them is a separate legacy-cleanup decision.
- `doctor._version_drift` (doctor.py:683) is a separate legacy helper and is not in scope; this plan changes `probe_environment` only.
- The stale-VERSION-stamping defect (backlog `ygtykn`) is a different bug in the installer, not in doctor, and is planned separately. Fixing doctor's READ does not change what the installer WRITES.

## Scope check

- Over-scope: none. The plan now touches two functions (one per affected consumer) plus a small shared helper and tests. `cli.py` was ADDED to `Scope-Paths` during review because the same defect is reachable there (F-07); fixing only doctor would have left a user-visible wrong answer in `aw status`.
- Under-scope: this plan does not audit every other read in `probe_environment` beyond those proven wrong, and does not sweep the repo for further copies of the config-read pattern beyond the two now fixed. The shared helper introduced by E-02 is what prevents a THIRD copy from being written; a future divergent reader remains possible but would now be a deliberate act rather than the path of least resistance.
- SCOPE ADDITIONS MADE DURING EXECUTION (2026-09-22), declared here because they were unavoidable consequences of the fix rather than opportunistic work:
  - `agent_workflows/project_context.py` - the home chosen for E-02's ONE shared reader. E-02 required a helper "placed where both `doctor.py` and `cli.py` can import it without a cycle" but named no file, so a third path was always going to be touched. `project_context.py` is the correct home on the criterion E-02 itself set: it already OWNS project-config resolution (it is the module that reads `.aw/config/project.json` as Level 3 PROJECT_DURABLE_CONFIG) and it imports only `project_schema`/`layout`, so neither `doctor` nor `cli` can form a cycle through it. Verified by import: `import agent_workflows.project_context; import agent_workflows.cli` and `import agent_workflows.doctor` both succeed.
  - `tests/test_renderer_boundary.py` - a PRE-EXISTING fixture defect the fix exposed, not new work. Its `DoctorRendererBoundaryTests.setUp` seeded the install marker at `.aw/VERSION`, the same fictional path the bug read, so the fixture only ever looked "installed" BECAUSE the probe was wrong. With the probe corrected the fixture became an uninstalled repo and its two tests failed on a false `doctor.version-not-installed`. Leaving it would mean shipping a red suite; changing the assertions instead would mean weakening a test to accommodate a fixture bug. The marker was therefore moved to `.aw/system/VERSION` (where an install really writes it), with `engine.emit_layout_artifacts` called so the now-genuinely-installed fixture also carries the emitted layout document that `check_engine.check_system_layout` correctly requires of an installed workspace. The identical defect in `tests/test_doctor.py` is fixed the same way, and that file WAS in scope.

## Required tests / validation

- `python3 -m pytest tests/test_doctor.py -o addopts=""` must pass, including the two new tests. Bare `python3 -m pytest` is insufficient here because the file may be marked slow and deselected; the explicit path plus cleared addopts is required for the counts to be meaningful.
- Both new tests must be confirmed RED before the fix and GREEN after. A test that passes before the fix proves nothing.
- Full suite: `python3 -m pytest` must show no NEW failures against the pre-existing baseline. Four failures are already present on untouched HEAD (three `oc profile` undeclared-leaf failures in `tests/test_command_surface_declarations.py` and `tests/test_cli_conformance_matrix.py`, plus `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory`), verified on a pristine worktree of HEAD; they are unrelated to this plan and must not be counted as regressions or fixed here.

## Spec / documentation sync

N/A: no spec governs doctor's internal path resolution, and this plan changes no public contract or flag. The fix makes the command's OUTPUT correct; the output format is unchanged. No `.spec.md` file is touched, hence none is declared in `Scope-Paths`.

## Open questions

### OQ-01: Should the legacy `.agents/VERSION` and `.agents/config.json` fallbacks be dropped?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: Keep them. They cost one `is_file()` each and never match, so they are harmless; deleting them is a legacy-support decision that belongs with the wider `.agents/` deprecation, not with a correctness fix. Resolved from repository evidence: the codebase consistently retains legacy fallbacks alongside canonical paths (`engine.read_installed_version` itself still probes `.agents/workflows/VERSION`).

### OQ-02: Which file wins for `records_backend`, `.aw/config/config.json` or `.aw/config/project.json`?

- Blocking: no
- Status: resolved
- Owner: opencode (settled during E-02 from the writer side, as directed)
- Resolution or deferral rationale: RESOLVED AS `.aw/config/project.json` WINS, with `.aw/config/config.json` consulted per-key as a LEGACY fallback and `.agents/config.json` last. Settled from the writer side exactly as this OQ directed, on three independent pieces of repository evidence. (1) `install_wizard.resolve_existing_policy` (install_wizard.py:458-461) names `project.json` as `proj_json` and `config.json` as `legacy_json`, so the INSTALLER itself classifies the latter as legacy. (2) `project_context.resolve_project_context` (project_context.py:571-593) reads `project.json` as Level 3 PROJECT_DURABLE_CONFIG and reaches `legacy_config_file` only in an `elif`, i.e. never when `project.json` exists. (3) `project_schema.migrate_legacy_config` (project_schema.py:665) exists specifically to MIGRATE a `config.json` FORWARD into the project/local split, which is only coherent if `project.json` is the destination and therefore the authority. Per-key rather than first-file-wins so a legacy file can still supply a field the canonical file omits without ever overriding it. The precedence is documented in the helper's docstring (`project_context.read_project_identity`). As predicted, this is observationally inert today (both files hold `repository` on this repo, verified in V-02), so the change is purely about removing future drift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the output of a command that prints BOTH `engine.read_installed_version(repo)` and `doctor.probe_environment(repo).installed_version` for a fixture whose VERSION is at `.aw/system/VERSION`, showing the two values EQUAL and non-None. Also paste the same two values for a fixture with VERSION at `.agents/workflows/VERSION`.
  - Observed evidence: both required fixtures paste below, plus the third probe location as a bonus. Note the pre-fix value of the doctor read was `None` in EVERY one of these cases, since none of the three real locations was among the two paths it probed.

    ```
    === V-01a: VERSION at .aw/system/VERSION ===
    engine.read_installed_version   : '1.2.1'
    doctor.probe_environment(...)   : '1.2.1'
    EQUAL and non-None              : True

    === V-01b: VERSION at .agents/workflows/VERSION ===
    engine.read_installed_version   : '1.1.0'
    doctor.probe_environment(...)   : '1.1.0'
    EQUAL and non-None              : True

    === V-01c: also the third location, .aw/system/workflows/VERSION ===
    engine: '1.0.9'  doctor: '1.0.9'
    ```

    And on THIS repo (F-02's exact measurement, now agreeing where it previously disagreed `1.2.1` vs `None`):

    ```
    engine.read_installed_version: 1.2.1
    doctor.installed_version: 1.2.1
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste output showing `probe_environment(".").preset == "private-target"` and `.backend == "repository"` on this repo, alongside the corresponding values read directly from `.aw/config/project.json` and `.aw/config/config.json`, demonstrating agreement. The pre-fix values were both `None`.
  - Observed evidence: the probe now agrees with both config files. This also supplies the measurement OQ-02's resolution relies on, namely that the two candidate files currently hold the SAME `records_backend`, so the documented precedence is observationally inert today and guards only against future drift.

    ```
    === V-02: preset/backend on THIS repo (pre-fix both were None) ===
    probe_environment('.').preset  : 'private-target'
    probe_environment('.').backend : 'repository'
    .aw/config/project.json preset          : 'private-target'
    .aw/config/project.json records_backend : 'repository'
    .aw/config/config.json  records_backend : 'repository'
    AGREEMENT preset : True
    AGREEMENT backend: True
    ```

    Pre-fix, for contrast (measured on this repo before the change):

    ```
    doctor.preset: None
    doctor.backend: None
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the RED run (the new test failing against pre-fix code, with the assertion message) and then the GREEN run after the fix, including the `N passed` summary line from `python3 -m pytest tests/test_doctor.py -o addopts=""`.
  - Observed evidence: RED was established by reverting ONLY the three source files to HEAD while keeping the new tests, which is the honest way to prove the tests bind to the fix rather than to their own fixtures.

    RED (`python3 -m pytest tests/test_doctor.py -o addopts="" -p no:randomly`, source at HEAD):

    ```
    E       AssertionError: None != '1.1.0'
    E       AssertionError: None != 'private-target'
    E       AssertionError: None != 'public-target-private-companion'
    =========================== short test summary info ============================
    FAILED tests/test_doctor.py::DoctorTests::test_clean_repo_no_findings - Asser...
    FAILED tests/test_doctor.py::DoctorTests::test_run_no_findings_exit0 - Assert...
    FAILED tests/test_doctor.py::DoctorTests::test_untracked_dir_excluded_by_default
    FAILED tests/test_doctor.py::DoctorEnvironmentProbeReadsCanonicalPathsTests::test_healthy_installed_target_emits_no_version_not_installed_finding
    FAILED tests/test_doctor.py::DoctorEnvironmentProbeReadsCanonicalPathsTests::test_probe_agrees_with_engine_on_aw_system_version
    FAILED tests/test_doctor.py::DoctorEnvironmentProbeReadsCanonicalPathsTests::test_probe_agrees_with_engine_on_legacy_workflows_version
    FAILED tests/test_doctor.py::DoctorEnvironmentProbeReadsCanonicalPathsTests::test_probe_reads_preset_and_backend_from_canonical_project_config
    FAILED tests/test_doctor.py::DoctorEnvironmentProbeReadsCanonicalPathsTests::test_status_and_doctor_report_the_same_preset_and_backend
    ========================= 8 failed, 7 passed in 4.89s ==========================
    ```

    All FIVE new tests are in that RED set. The three `DoctorTests` failures in it are the PRE-EXISTING fixture defect described under V-04 (the fixture wrote the fictional `.aw/VERSION`), surfaced because the tests were correct and the source was not yet.

    GREEN (same command, fix applied):

    ```
    collected 15 items

    tests/test_doctor.py ...............                                     [100%]

    ============================== 15 passed in 5.51s ==============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the RED then GREEN runs for the no-false-finding test, plus the drift list for a healthy non-source fixture showing no `doctor.version-not-installed` entry. Additionally paste a full `python3 -m pytest` summary line and confirm the failure set matches the four-failure pre-existing baseline named in Required tests, with no new entries.
  - Observed evidence: RED for `test_healthy_installed_target_emits_no_version_not_installed_finding` is in the V-03 RED summary above; GREEN is in the 15-passed run. The drift list for a healthy NON-SOURCE fixture:

    ```
    === V-04: drift list for a HEALTHY NON-SOURCE fixture (the F-04 symptom) ===
    is_source_repo     : False
    installed_version  : 1.3.0rc2.dev3442+g301a1d8f.d20260922
    version_status     : dev
    drift rules        : ['check.system-layout-missing']
    HAS version-not-installed: False
    ```

    F-04's exact scenario rehearsed (a real 1.2.1 target), showing the false `not installed` replaced by the TRUE `stale`:

    ```
    F-04 rehearsal (a real 1.2.1 target):
      installed_version: 1.2.1 (was: None -> 'not installed')
      version_status   : stale
      preset / backend : private-target / repository (was: None / None)
      version drift    : ['doctor.version-stale']
    ```

    FULL SUITE (`python3 -m pytest`, bare as the contract requires):

    ```
    FAILED tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    2 failed, 8046 passed, 3 skipped, 2 xfailed, 3 warnings in 174.85s (0:02:54)
    ```

    The PRE-CHANGE baseline on this same worktree, measured before any edit, was the SAME two failures (`2 failed, 8041 passed`); the count rose by exactly the 5 tests this plan adds. NO NEW FAILURES. Neither failing test references `doctor`, `project_context`, `probe_environment` or `_collect_repo_status_details` (verified by grep), and both concern `oc_runipd`/turn-bounds code this plan does not touch.

    CORRECTION TO THIS PLAN'S PREDICTED BASELINE, recorded rather than quietly ignored. The plan named a FOUR-failure baseline (three `oc profile` undeclared-leaf failures plus one installer uninstall test). Those four are real but are all `slow`-marked and therefore DESELECTED by a bare `python3 -m pytest`, so they cannot appear in the run above; the plan's own "Project conventions" note anticipates exactly this deselection. Run explicitly, they still fail, and they fail IDENTICALLY at pristine HEAD with my changes stashed:

    ```
    --- at pristine HEAD ---
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
    FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
    4 failed, 22 passed in 264.31s (0:04:24)
    ```

    with my changes applied, the same four and no others:

    ```
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves
    FAILED tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_every_declared_leaf_gets_a_full_scenario_row_set
    FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
    FAILED tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves
    4 failed, 22 passed in 318.90s (0:05:18)
    ```

    So the full pre-existing failure set is SIX across both selections (2 fast + 4 slow), unchanged by this plan in both directions.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `_collect_repo_status_details(Path("."), <packaged>)`'s `preset`/`backend` values post-fix (pre-fix both were `None`), AND paste the same two values from `probe_environment(".")`, demonstrating the two commands now agree because they share one reader. Also paste the human-visible `aw status` output showing the preset, since that is the surface a user sees.
  - Observed evidence: the two consumers now agree because they share one reader, and the preset is visible to a human for the first time.

    ```
    === V-05: aw status and aw doctor agree (both were None pre-fix) ===
    _collect_repo_status_details preset : 'private-target'
    _collect_repo_status_details backend: 'repository'
    probe_environment preset            : 'private-target'
    probe_environment backend           : 'repository'
    THEY AGREE: True
    ```

    The pre-fix measurement of the same call, reproducing F-07 exactly (`installed` was already correct because that line already delegated to `engine.read_installed_version`; only the config read was wrong):

    ```
    {'installed': '1.2.1', 'preset': None, 'backend': None, 'layout': '.aw', 'state': 'source-root'}
    ```

    HUMAN-VISIBLE SURFACE (`python3 -m agent_workflows status`, i.e. this lane's code rather than the installed `aw`). Post-fix:

    ```
    - <repo>/.aw/worktrees/h90ij1 [source root] v1.3.0rc2.dev3442+g301a1d8f.d20260922 (source checkout)
      Layout:    .aw (preset: private-target, backend: repository)
    ```

    Pre-fix, same command and same repo, with `cli.py` stashed. The ENTIRE parenthetical was absent, because cli.py:7339 gates it on `rd["preset"] or rd["backend"]` and both were `None`, so the user was not merely shown a wrong preset, they were shown NO preset at all:

    ```
    - <repo>/.aw/worktrees/h90ij1 [source root] v1.3.0rc2.dev3442+g301a1d8f.d20260922 (source checkout)
      Layout:    .aw
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item rather than asserting success; and confirm each new test was RED before the fix. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` (never a raw `git mv` plus commit, which the pre-commit gate refuses). Backlog item `hdhzr2` closes only after this plan is executed; it carries `Blocks-Release: f33nrj`, which this plan inherits.
