# IPD: Route the remaining raw agent_workflows subprocess spawns in six test files through support.run_cli

- Date: 2026-09-26
- Kind: child
- Concern: Six test files spawn `python -m agent_workflows...` without pinning `PYTHONPATH` to this checkout, so the child resolves `agent_workflows` from whatever is first on its path: the cwd, an inherited `PYTHONPATH`, or an editable install of another checkout. Under pytest the root `conftest.py` prepends the repo root to `PYTHONPATH` and masks this; under `python3 -m unittest`, which agents repeatedly use and which does NOT load `conftest.py`, nothing pins it. Measured at HEAD `61ef21d8` with a decoy `agent_workflows` package first on `PYTHONPATH`: `python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` FAILS (the decoy answered), and `tests/test_comms_acks.py` run from the decoy's directory gives `5 failed, 15 passed`. Four spawn sites also use a bare `"python3"` instead of `sys.executable`, so they may run a different interpreter than the test.
- Scope: IN: every unpinned `-m agent_workflows...` spawn in `tests/test_comms_acks.py` (5), `tests/test_completion.py` (2), `tests/test_concurrent_driver_guard.py` (2), `tests/test_project_context.py` (2), `tests/test_project_registry.py` (4), `tests/test_records_untracked_backend.py` (4) goes through `tests/support.py`; `support` gains the two small hooks needed (a module argument and a pinned-env helper). OUT: files that already pin explicitly (`tests/test_driver_attestation_gate.py`, `tests/test_oc_runipd.py`); a guard test; changing test assertions.
- Scope-Paths: tests/support.py, tests/test_comms_acks.py, tests/test_completion.py, tests/test_concurrent_driver_guard.py, tests/test_project_context.py, tests/test_project_registry.py, tests/test_records_untracked_backend.py, CONTRIBUTING.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 17xkyp
- Set: testhyg
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: tcx2ok

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 17xkyp: route 19 unpinned agent_workflows spawns in six test files through support.run_cli; decoy reproduction fails today under unittest.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every CLI subprocess these six files spawn imports THIS checkout's `agent_workflows` with the test's own interpreter, whether the file is run under pytest or under `python3 -m unittest`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: support hooks

- [ ] E-01 In `tests/support.py`, factor the env merge out of `run_cli` into `pinned_env(env: dict | None = None) -> dict` (copy of `os.environ` or `env`, with `REPO_ROOT` prepended to `PYTHONPATH` if absent) and make `run_cli` call it; add a keyword-only `module: str = "agent_workflows"` to `run_cli` so `-m agent_workflows.comms_acks` can be spawned (`[sys.executable, "-m", module, *cli_args]`). Default behavior of every existing `run_cli` caller is unchanged.
  - Depends on: none
  - Expected outcome: `support.run_cli("--version")` behaves as before; `support.run_cli("--help", module="agent_workflows.comms_acks")` runs the submodule pinned.
  - Execution state: pending

### Task group 2: migrate the six files

- [ ] E-02 Re-measure at HEAD first (an `ast.walk` scan over `tests/*.py` listing each list/tuple literal containing the adjacent constants `"-m"`, `"agent_workflows..."`, or `grep -n '"agent_workflows' tests/<file>`), then convert each spawn: `subprocess.run([sys.executable|"python3", "-m", "agent_workflows", *args], cwd=..., env=..., capture_output=True, text=True)` becomes `support.run_cli(*args, cwd=..., env=...)` (drop kwargs `run_cli` already defaults); `-m agent_workflows.comms_acks` spawns use `module="agent_workflows.comms_acks"`; the one `subprocess.Popen` in `test_concurrent_driver_guard.py` (the "genuinely CONTEND" test) keeps `Popen` but gets `[sys.executable, ...]` and `env=support.pinned_env()`. Every bare `"python3"` in these spawns disappears (run_cli uses `sys.executable`). Add `from tests import support` where missing. `test_comms_acks.py` is plain pytest functions with `tmp_path`; keep them as functions. Do not change any assertion, cwd or env content beyond the pin.
  - Depends on: E-01
  - Expected outcome: the AST scan reports 0 unpinned spawns in the six files.
  - Execution state: pending

- [ ] E-03 Run each of the six files under BOTH runners from the repo root: `python3 -m pytest -o addopts="" tests/<file>` and `python3 -m unittest tests.<module>`. `test_comms_acks.py` has no `TestCase` classes, so `unittest` collects 0 tests there; record that as expected (pytest is its only runner) rather than as a pass.
  - Depends on: E-02
  - Expected outcome: all pass under pytest; the five `TestCase` modules pass under unittest.
  - Execution state: pending

- [ ] E-04 Demonstrate the pin holds under unittest with a decoy. Create `/tmp/opencode/decoy/agent_workflows/{__init__.py,__main__.py}` where `__main__` prints `DECOY` and exits 0 (and a `comms_acks.py` that does the same). Run `PYTHONPATH=/tmp/opencode/decoy python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` and `(cd /tmp/opencode/decoy && PYTHONPATH=/tmp/opencode/decoy python3 -m pytest <repo>/tests/test_comms_acks.py -o addopts="" -p no:cacheprovider)` before and after E-02. Note that the in-process import of the test module itself resolves the repo (the test process's `sys.path[0]` is the repo root under `-m unittest`), so only the subprocess is at risk; that is exactly what the decoy exercises.
  - Depends on: E-02
  - Expected outcome: before, the completion test FAILS and comms_acks shows `5 failed`; after, both pass.
  - Execution state: pending

### Task group 3: doc and suite

- [ ] E-05 Documentation: `AGENTS.md`'s managed "HOW TO RUN THE SUITE" paragraph already says to run `python3 -m pytest` bare, and it is generated from `agent_workflows/engine.py` (so it is not edited here). `CONTRIBUTING.md` presents `make test-serial` (`python3 -m unittest discover`) as a legitimate fallback, which it is. Add ONE sentence to that `CONTRIBUTING.md` paragraph: `unittest` does not load `conftest.py`, so its role scrub, home sandbox and `PYTHONPATH` pin do not apply; use it only for the stated isolation-debugging purpose, and spawn the CLI in tests only through `tests/support.run_cli`. Then run the bare suite.
  - Depends on: E-03, E-04
  - Expected outcome: one added sentence; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/support.run_cli` is the sanctioned spawn helper (IPD `lhjsu0`, bug `ccbe60`): pins `PYTHONPATH` to `REPO_ROOT` and uses `sys.executable`.
- The root `conftest.py` pins `PYTHONPATH` only under pytest; `tests/__init__.py` provides a home sandbox for unittest but no path pin.
- `AGENTS.md` HOW TO RUN THE SUITE already tells agents to run pytest bare; CONTRIBUTING.md names `make test` as canonical and `make test-serial` as a debugging fallback.
- Maintainer rule: no guard tests; tests assert outcomes. This plan adds no test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8` with an AST scan for `["-m", "agent_workflows..."]` lists in `tests/*.py`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | six files | Unpinned spawns: test_comms_acks 5 (all `agent_workflows.comms_acks`), test_completion 2, test_concurrent_driver_guard 2 (one `run`, one `Popen`), test_project_context 2, test_project_registry 4, test_records_untracked_backend 4. None uses `run_cli`. Matches the brief. | scan output per file |
| F-2 | MED | test_project_context, test_project_registry, test_records_untracked_backend | Bare `"python3"` in all 10 of their spawns, not only the two the brief named in test_records_untracked_backend. | `grep -n 'python3"'`: test_project_context 2, test_project_registry 4, test_records_untracked_backend 4 |
| F-3 | MED | unittest runs | The defect is real, not theoretical: a decoy on `PYTHONPATH` answers the spawn. | `PYTHONPATH=<decoy> python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` -> `FAILED (failures=1)`, `AssertionError: False is not true`; comms_acks from decoy cwd -> `5 failed, 15 passed` |
| F-4 | INFO | `support.run_cli` | Cannot spawn a submodule (`-m agent_workflows.comms_acks`) or feed a `Popen`; E-01 adds both hooks. `comms_acks` is not reachable via the `aw` CLI (`aw comms` is an invalid choice). | `run_cli` builds `[sys.executable, "-m", "agent_workflows", *cli_args]` |
| F-5 | INFO | test_driver_attestation_gate.py, test_oc_runipd.py | Also spawn raw, but pin `PYTHONPATH` explicitly (`_env()` / `_DRIVER_ENV`) and use `sys.executable`; not defective, out of scope. | `env["PYTHONPATH"] = str(support.REPO_ROOT)`; `_DRIVER_ENV = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}` |

## Proposed changes (ordered, validatable)

1. E-01: `pinned_env` and `module=` in support.
2. E-02: migrate 19 spawns.
3. E-03, E-04: both runners; decoy demonstration.
4. E-05: one CONTRIBUTING sentence; bare suite.

## Deferred / out of scope (with reason)

- Converting the two explicitly pinned files (F-5) to `run_cli` for uniformity: they are correct today; churn without an outcome change.
  - Carrier-Declined: no defect; uniformity alone does not justify the edit.
- A guard test that fails on any new unpinned spawn: maintainer declined structural guards (2026-09-26).
  - Carrier-Declined: maintainer decision 2026-09-26.

## Scope check

- Over-scope: `tests/support.py` and `CONTRIBUTING.md` are beyond the six files; both are required (F-4; maintainer asked to consider the doc).
- Under-scope: none.

## Required tests / validation

- Each file under `python3 -m pytest -o addopts=""` and `python3 -m unittest`; the decoy demonstration; bare suite. No new test (outcome rule; no guard tests).

## Spec / documentation sync

`CONTRIBUTING.md` gains one sentence (E-05); it is user-facing, so write it with no em or en dashes. No `.spec.md` is touched. `AGENTS.md` is generated from `engine.py` and already directs pytest; not edited.

## Open questions

### OQ-01: Tell agents never to use unittest?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No blanket ban. `AGENTS.md` already directs `python3 -m pytest` bare (managed HOW TO RUN THE SUITE paragraph), and CONTRIBUTING's `make test-serial` is a real debugging tool. The fix makes unittest runs correct for these files; E-05 adds one sentence naming what unittest skips.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `tests/support.py` diff; paste `python3 -c 'from tests import support; r=support.run_cli("--help", module="agent_workflows.comms_acks"); print(r.returncode, "subcommand" in r.stdout); print(support.pinned_env({})["PYTHONPATH"])'` showing `0 True` and the repo root.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the AST scan (or grep) output BEFORE (19 sites) and AFTER (0 unpinned sites in the six files; the Popen site shows `env=support.pinned_env()`); paste `grep -n '"python3"' ` over the six files returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, per file, the summary line of `python3 -m pytest -o addopts="" tests/<file>` and of `python3 -m unittest tests.<module>` (12 runs; `test_comms_acks` under unittest shows `Ran 0 tests`, stated as expected).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the decoy file contents and the two decoy runs BEFORE (completion `FAILED`, comms_acks `5 failed`) and AFTER (both pass).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the CONTRIBUTING.md diff; paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Test-harness changes only: 19 spawn sites in six test files routed through `tests/support.py`, which gains a `pinned_env` helper and a `module=` argument; one sentence in CONTRIBUTING.md. No production code, no assertion changes.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); nothing under `/tmp` is committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `17xkyp` `done` with `--evidence` citing the executed plan.
