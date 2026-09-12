# IPD: Fix aw doctor's environment probe: it reads three nonexistent paths and reports a healthy repo as not installed

- Date: 2026-09-12
- Kind: child
- Concern: `aw doctor`'s environment probe resolves the installed VERSION, the preset, and the records backend from paths that do not exist in either supported layout, so it reports a correctly installed repo as `not installed` and emits a false `doctor.version-not-installed` finding.
- Scope: Repoint `doctor.probe_environment`'s three misresolved reads at the canonical locations, delegating version resolution to the single existing authority (`engine.read_installed_version`) instead of a second divergent path list; add regression tests that fail on the current code.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: none
- Status: to-review
- Set: doctorprobe
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: h90ij1
- From-Backlog: hdhzr2
- Blocks-Release: f33nrj

## Workflow history

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

- [ ] E-02 In the same function, fix the project-config read (doctor.py:341-343): the probe reads `repo_root/".aw"/"config.json"` then `repo_root/".agents"/"config.json"`. The canonical project config is `.aw/config/project.json` (config.py:1056 and config.py:1115 both resolve `Path(repo_root)/".aw"/"config"/"project.json"`), and `preset` is a key there. Keep the legacy `.agents/config.json` fallback for an un-migrated repo, and keep reading `records_backend` from `.aw/config/config.json` where it actually lives.
  - Depends on: E-01
  - Expected outcome: on this repo, `probe_environment(".").preset == "private-target"` (the value in `.aw/config/project.json`) and `.backend == "repository"` (the value in `.aw/config/config.json`), instead of the current `None` for both.
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

## Proposed changes (ordered, validatable)

1. Delegate the VERSION read to `engine.read_installed_version` (E-01), removing the divergent path list rather than extending it. Extending it would leave two authorities that can drift again.
2. Repoint the project-config read at `.aw/config/project.json`, retaining the legacy fallback (E-02).
3. Add a test binding doctor's reading to engine's (E-03).
4. Add a test asserting no false `version-not-installed` finding on a healthy fixture (E-04).

## Deferred / out of scope (with reason)

- The `.agents/VERSION` and `.agents/config.json` fallbacks are RETAINED, not deleted. They are harmless (they simply never match) and removing them is a separate legacy-cleanup decision.
- `doctor._version_drift` (doctor.py:683) is a separate legacy helper and is not in scope; this plan changes `probe_environment` only.
- The stale-VERSION-stamping defect (backlog `ygtykn`) is a different bug in the installer, not in doctor, and is planned separately. Fixing doctor's READ does not change what the installer WRITES.

## Scope check

- Over-scope: none. Two reads in one function, plus two tests.
- Under-scope: this plan does not audit the remaining reads in `probe_environment` beyond the three proven wrong. E-02's expected outcome pins the two config fields, so a further divergent read would surface as a test failure rather than silently persisting.

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

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`Status: approved`) before any code change. The executor must: commit only the files listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <path>`), never `git add -A` and never push; paste ACTUAL runner output for every `V-*` item rather than asserting success; and confirm each new test was RED before the fix. Post-gate lifecycle: once every `V-*` carries observed evidence and `aw ipd lint --phase pre-transition` reports conforming, move this plan to `.aw/records/plans/executed/` via `aw ipd finalize` (never a raw `git mv` plus commit, which the pre-commit gate refuses). Backlog item `hdhzr2` closes only after this plan is executed; it carries `Blocks-Release: f33nrj`, which this plan inherits.
