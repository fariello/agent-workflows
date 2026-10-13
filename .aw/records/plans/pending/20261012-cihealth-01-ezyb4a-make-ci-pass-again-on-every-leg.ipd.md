# IPD: Make CI pass again on every leg

- Date: 2026-10-12
- Kind: child
- Concern: Every `tests.yml` run since 2026-09-27 has failed. In the last completed run (`38168033704`, commit `3468cabbd`, 2026-10-11) four separate causes fail the jobs: (1) every Python 3.9 leg fails at `pip install -e ".[test]"`, because the `test` extra pins `filelock>=4` and filelock 4.x requires Python >=3.10 (`ResolutionImpossible`), while `requires-python = ">=3.9"`; (2) the unit-test legs that do install report 20 failed and 2 errors, among them tests using 3.11+ only APIs (`typing.Self` in `tests/test_egress_policy.py`, `contextlib.chdir` in `tests/test_run_dir_outcomes_parent_is_guaranteed.py`), tests that need the `agy` binary on PATH, a sandbox probe that needs user namespaces, and tests sensitive to an interactive terminal; (3) the static type gate reports 15 mypy errors in 8 files; (4) the `attention + specs contract check` job fails on `aw check plans --agent` with 15 findings, i.e. committed plan records that do not conform.
- Scope: Make every job in `tests.yml` pass on main, on every OS and Python leg it declares, without removing a leg and without weakening a gate. Fix the code, the tests and the records; do not skip tests, lower a gate's severity, or loosen the type gate to get there. If one leg's failure needs a maintainer decision (for example dropping Python 3.9 support), stop that item and ask, because that changes the published support contract.
- Scope-Paths: pyproject.toml, tests, agent_workflows, .aw/records/plans, .aw/records/backlog, .github/workflows/tests.yml
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 1
- Highest E allocated: 06
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: ezyb4a

## Workflow history
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix; failures measured from run 38168033704 job logs.
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A push to main produces a green `tests.yml` run, on every declared leg, with every gate still as strict as it is today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure

- [ ] E-01 RE-MEASURE the failures at execution HEAD. Failures drift, so the review-time list in Findings is context, not the bar. Fetch the latest completed `tests.yml` run (`gh run list --workflow tests.yml`, then `gh run view <id> --json jobs` and `gh api repos/<owner>/<repo>/actions/jobs/<job>/logs`) and record, per failing job: the job name, the failing step, and each failing test id or error line. Also run, locally: the bare suite (`python3 -m pytest`), the type gate exactly as `tests.yml` runs it, and `python -m agent_workflows check plans --agent`. Paste a table grouping every failure under one of: install, Python-version API, missing external binary, environment-dependent (sandbox, terminal), real defect, type error, record conformance.
  - Depends on: none
  - Expected outcome: a pasted, grouped failure table naming the run id and HEAD.
  - Execution state: pending

### Task group 2: fix by group

- [ ] E-02 Fix the 3.9 install. The `test` extra and the `dev` group pin `filelock>=4`, which needs Python >=3.10. Use an environment marker so 3.9 resolves a 3.x filelock and 3.10+ keeps the >=4 floor (for example `"filelock>=4; python_version >= '3.10'"` plus `"filelock>=3; python_version < '3.10'"`), and keep the shipped runtime dependency `filelock>=3` unchanged. If the type gate's baseline depends on filelock 4 (see the `pyproject.toml` E-07 comment), confirm the type gate job installs on 3.10+ only and still passes. Prove it with `pip install -e ".[test]"` resolving under a 3.9 interpreter (or `pip install --dry-run --python-version 3.9 --only-binary=:all:` against the extra), and paste the output.
  - Depends on: E-01
  - Expected outcome: `pip install -e ".[test]"` resolves on 3.9 and on 3.10+.
  - Execution state: pending

- [ ] E-03 Fix the Python-version API failures. Replace 3.11+ only APIs in tests and code with forms available on 3.9 (for example `typing_extensions.Self` or a quoted annotation instead of `typing.Self`; an explicit `os.chdir` with `try`/`finally` instead of `contextlib.chdir`), and fix any other version-specific failure E-01 found. Do not mark a test skipped by version unless the behavior under test genuinely does not exist on that version, and say why where you do.
  - Depends on: E-01
  - Expected outcome: no collection error or `AttributeError`/`ImportError` from a missing API on any leg.
  - Execution state: pending

- [ ] E-04 Fix the environment-dependent failures. A test that needs the `agy` binary, user namespaces, or an interactive terminal must not depend on the CI machine having them: give it the fake binary or seam the neighbouring tests already use (for example the scripted host), or detect the missing capability and skip with the reason, choosing per test and recording which and why. Fix every real defect E-01 found (for example `lanes list` emitting empty stdout under `--agent`, the completion-offer tests) in the code, not in the test.
  - Depends on: E-01
  - Expected outcome: every unit-test leg passes, with each skip carrying a stated reason.
  - Execution state: pending

- [ ] E-05 Fix the type errors and the record findings. Resolve each mypy error the type gate reports (15 at review: `Unsupported left operand type for + ("None")` in `specs.py`, `backlog.py`, `releases.py`, `cli.py`, `research_refs.py`, `research_archive.py`, `attention.py`, and two `Incompatible return value type ... ScopeReconciliation` in `runner_shared.py`) in the code, without adding `type: ignore` unless a line genuinely cannot be typed, and say why where you do. Resolve each `aw check plans` finding (15 at review, across `check.lifecycle-transition-unvalidated`, `check.ipd-carrier-ungated`, `check.ipd-uncarried-obligation` and others) by fixing the record through the shipped tooling (`aw ipd set`, `aw ipd sync`, adding a `Carrier`), never by editing a plan already in `executed/` beyond a dated `## Workflow history` note.
  - Depends on: E-01
  - Expected outcome: the type gate and `aw check plans --agent` both exit 0 locally, as CI runs them.
  - Execution state: pending

### Task group 3: prove on CI

- [ ] E-06 Prove it on CI. Run the bare suite locally and paste the summary line. After integration to main, wait for the `tests.yml` run on that commit (`gh run watch <id>` or poll `gh run list`) and paste every job's conclusion. If any job still fails, fix it under the group it belongs to and repeat; do not report this plan done on a red run.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: a `tests.yml` run on main with every job `success`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- `requires-python = ">=3.9"` is a published support contract; changing it is a maintainer decision.
- Commit through `aw commit <plan> -- <paths>`; never push. The runner integrates; CI runs on the push to main.
- Cite code by SYMBOL.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | CI red since 2026-09-27; 1,623 first-parent main commits since the last green run. | `gh run list --workflow tests.yml`: last `success` 2026-09-27 at `f69ad318a`; `git log --first-parent f69ad318a..main` = 1623 (2026-10-12). |
| F-02 | Every 3.9 leg fails at install. | Job `unittest (windows-latest, py3.9)` log: "agent-workflows[test] ... depends on filelock>=4" with "ResolutionImpossible"; filelock 4.0.0 `requires_python >=3.10` (PyPI JSON). |
| F-03 | 3.10 leg: 20 failed, 2 errors, 7146 passed. | Job `unittest (ubuntu-latest, py3.10)`: `ImportError: cannot import name 'Self' from 'typing'`; `AttributeError: module 'contextlib' has no attribute 'chdir'`; `Cannot find 'agy' on PATH`; `unshare: write failed /proc/self/uid_map: Operation not permitted`; `Leaf 'lanes list' emitted EMPTY stdout under --agent`; completion and interactivity assertions. |
| F-04 | Type gate: 15 errors in 8 files. | Job `static type gate (fail-closed)`: "Found 15 errors in 8 files (checked 193 source files)". |
| F-05 | Records job fails on `aw check plans`. | Job `attention + specs contract check (fail-closed)`: `check plans --agent` -> `"findings":15`, exit 1. |

## Proposed changes (ordered, validatable)

1. Re-measure (E-01).
2. Install, version APIs, environment, types and records, one group per item (E-02..E-05).
3. Prove on CI (E-06).

## Deferred / out of scope (with reason)

- Dropping a Python version or OS leg: a support-contract change, not a fix.
  - Carrier-Declined: if E-02 or E-03 finds a leg that cannot be fixed, the executor asks the maintainer, per the Scope.

## Scope check

- Over-scope: none.
- Under-scope: none known. Scope-Paths is broad on purpose (`tests`, `agent_workflows`) because E-01 decides which files fail; each changed path is justified at finalize.

## Required tests / validation

- The bare suite locally.
- The type gate and `aw check plans --agent` locally, as CI runs them.
- A green `tests.yml` run on main (E-06).

## Spec / documentation sync

N/A: fixes CI to match existing contracts (`requires-python`, the gates in `tests.yml`); no spec or user-facing behavior changes. If E-02 changes the dependency declaration, add a CHANGELOG line (no em or en dashes).

## Open questions

### OQ-01: May a leg be dropped if it cannot be fixed?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No, not by the executor. Dropping a leg changes the published support contract; the executor stops that item and asks. Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted grouped failure table with the run id and HEAD.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted resolver output for the test extra on 3.9 and on 3.10+, and the `pyproject.toml` diff.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the diff, and the previously failing test ids passing under a 3.9 or 3.10 interpreter (pasted), or the CI job log after E-06.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the diff; each previously failing test id with its new outcome and, for any skip, the pasted skip reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the type gate's pasted "Success" line and `aw check plans --agent` with `"findings":0` and exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the bare-suite summary line and the pasted job list of the main `tests.yml` run, every job `success`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit ezyb4a -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize ezyb4a` only after `aw ipd lint --phase pre-transition` conforms. E-06 needs the commit to reach main; when executed by a runner, it may be completed in the run that follows integration.
