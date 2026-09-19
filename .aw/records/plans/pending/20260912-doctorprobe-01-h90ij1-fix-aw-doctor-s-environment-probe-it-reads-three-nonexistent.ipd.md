# IPD: Fix aw doctor's environment probe: it reads three nonexistent paths and reports a healthy repo as not installed

- Date: 2026-09-12
- Kind: child
- Concern: `aw doctor`'s environment probe resolves the installed VERSION, the preset, and the records backend from paths that do not exist in either supported layout, so it reports a correctly installed repo as `not installed` and emits a false `doctor.version-not-installed` finding.
- Scope: Repoint `doctor.probe_environment`'s three misresolved reads at the canonical locations, delegating version resolution to the single existing authority (`engine.read_installed_version`) instead of a second divergent path list; add regression tests that fail on the current code.
- Scope-Paths: agent_workflows/doctor.py, agent_workflows/cli.py, tests/test_doctor.py, tests/test_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: doctorprobe
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: h90ij1
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved
- From-Backlog: hdhzr2
- Blocks-Release: f33nrj

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-09-12 to-review (opencode): authored from backlog item hdhzr2; graduated with measured evidence and repo-cited root cause.
- 2026-09-12 draft (opencode): created.

## Goal

Make `aw doctor` report the framework state a repo actually has. Today the one command a user runs to check install health misreports a healthy install as `not installed`, and also blanks the preset and records backend, because three reads in `probe_environment` point at paths that no layout ever creates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Repoint the misresolved reads

- [ ] E-01 In `agent_workflows/doctor.py`, replace the hand-rolled VERSION probe (currently `repo_root/".aw"/"VERSION"` falling back to `repo_root/".agents"/"VERSION"`, doctor.py:355-357) with a call to `engine.read_installed_version(repo_root)`, which already probes the three real locations in priority order (engine.py:5705-5719). Do not duplicate the path list; `doctor.py` already imports `engine` (it calls `engine.resolve_source_root` at doctor.py:366).
  - Depends on: none
  - Expected outcome: `probe_environment(repo).installed_version` returns the same value `engine.read_installed_version(repo)` returns, for a repo whose VERSION sits at any of `.aw/system/VERSION`, `.aw/system/workflows/VERSION`, or `.agents/workflows/VERSION`.
  - Execution state: pending

- [ ] E-02 Add ONE shared project-config reader (a small module-level helper, placed where both `doctor.py` and `cli.py` can import it without a cycle) that resolves the repo's `preset` and `records_backend`, and repoint `doctor.probe_environment` at it. The current probe reads `repo_root/".aw"/"config.json"` then `repo_root/".agents"/"config.json"` (doctor.py:341-343); NEITHER exists in the `.aw` layout. The canonical project config is `.aw/config/project.json` (config.py:1056 and config.py:1115 both resolve `Path(repo_root)/".aw"/"config"/"project.json"`). Note BOTH keys are present there, and `records_backend` ALSO appears in `.aw/config/config.json`; the helper must therefore define and document an explicit precedence rather than reading whichever file it happens to find (see OQ-02). Keep the legacy `.agents/config.json` fallback for an un-migrated repo.
  - Depends on: E-01
  - Expected outcome: on this repo, `probe_environment(".").preset == "private-target"` and `.backend == "repository"`, instead of the current `None` for both, with the precedence documented in the helper's docstring.
  - Execution state: pending

- [ ] E-05 Repoint `cli._collect_repo_status_details` (cli.py:6219-6226) at the SAME shared helper from E-02. It contains the identical defect, reading `repo/(".aw" if has_aw else ".agents")/"config.json"`, a file that does not exist in the `.aw` layout, so `aw status` reports `preset=None`/`backend=None` for every correctly installed repo. Measured on this repo: `_collect_repo_status_details(Path("."), "1.3.0")` returns `preset: None`, `backend: None` while `installed: 1.2.1`. Fixing doctor alone would leave the same wrong answer reachable from a second command, which is exactly the duplicate-authority pattern E-01 exists to eliminate.
  - Depends on: E-02
  - Expected outcome: `_collect_repo_status_details` returns `preset="private-target"` and `backend="repository"` for this repo, sourced from the same helper doctor uses, so the two commands cannot diverge.
  - Execution state: pending

### Task group 2: Regression tests

- [ ] E-03 Add a test to `tests/test_doctor.py` asserting `probe_environment` agrees with `engine.read_installed_version` on a fixture repo that has ONLY `.aw/system/VERSION`. This test must fail against the pre-fix code; confirm that before fixing.
  - Depends on: E-01
  - Expected outcome: a named test that fails on the current implementation and passes after E-01.
  - Execution state: pending

- [ ] E-04 Add a test asserting that a correctly installed non-source fixture repo produces NO `doctor.version-not-installed` drift entry. This is the user-visible symptom and is a distinct surface from E-03: E-03 covers the read, E-04 covers the finding the read drives (doctor.py:371-382).
  - Depends on: E-01, E-02
  - Expected outcome: a named test that fails on the current implementation and passes after the fix.
  - Execution state: pending

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
- Status: open
- Owner: opencode (settle during E-02 from the writer side)
- Resolution or deferral rationale: Both files carry the key (F-08), so the helper must not read whichever it finds first. Settle it by identifying which file the INSTALLER writes as authoritative (`install_wizard` persists project policy; `config.py:1056`/`:1115` resolve `project.json`) and document that precedence in the helper docstring. Not blocking because both files currently hold the SAME value (`repository`) on every repo measured, so the observable output is identical either way today; the risk is future drift, which the documented precedence removes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the output of a command that prints BOTH `engine.read_installed_version(repo)` and `doctor.probe_environment(repo).installed_version` for a fixture whose VERSION is at `.aw/system/VERSION`, showing the two values EQUAL and non-None. Also paste the same two values for a fixture with VERSION at `.agents/workflows/VERSION`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste output showing `probe_environment(".").preset == "private-target"` and `.backend == "repository"` on this repo, alongside the corresponding values read directly from `.aw/config/project.json` and `.aw/config/config.json`, demonstrating agreement. The pre-fix values were both `None`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the RED run (the new test failing against pre-fix code, with the assertion message) and then the GREEN run after the fix, including the `N passed` summary line from `python3 -m pytest tests/test_doctor.py -o addopts=""`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the RED then GREEN runs for the no-false-finding test, plus the drift list for a healthy non-source fixture showing no `doctor.version-not-installed` entry. Additionally paste a full `python3 -m pytest` summary line and confirm the failure set matches the four-failure pre-existing baseline named in Required tests, with no new entries.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `_collect_repo_status_details(Path("."), <packaged>)`'s `preset`/`backend` values post-fix (pre-fix both were `None`), AND paste the same two values from `probe_environment(".")`, demonstrating the two commands now agree because they share one reader. Also paste the human-visible `aw status` output showing the preset, since that is the surface a user sees.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item rather than asserting success; and confirm each new test was RED before the fix. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` (never a raw `git mv` plus commit, which the pre-commit gate refuses). Backlog item `hdhzr2` closes only after this plan is executed; it carries `Blocks-Release: f33nrj`, which this plan inherits.
