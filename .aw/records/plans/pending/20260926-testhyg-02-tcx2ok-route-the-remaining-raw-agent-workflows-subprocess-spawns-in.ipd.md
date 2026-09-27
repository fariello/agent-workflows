# IPD: Route the remaining raw agent_workflows subprocess spawns in six test files through support.run_cli

- Date: 2026-09-26
- Kind: child
- Concern: Six test files spawn `python -m agent_workflows...` without pinning `PYTHONPATH` to this checkout, so the child resolves `agent_workflows` from whatever is first on its path: the cwd, an inherited `PYTHONPATH`, or an editable install of another checkout. Under pytest the root `conftest.py` prepends the repo root to `PYTHONPATH` and masks this; under `python3 -m unittest`, which agents repeatedly use and which does NOT load `conftest.py`, nothing pins it. Measured at HEAD `61ef21d8` and RE-MEASURED in review at `bfdd8821` with a decoy `agent_workflows` package first on a cleaned `PYTHONPATH`: `python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` FAILS (the decoy answered), and `tests/test_comms_acks.py` run from the decoy's directory gives `5 failed, 15 passed`. TEN spawn sites (not four) use a bare `"python3"` instead of `sys.executable`, so they may run a different interpreter than the test. THE 19 SITES ARE NOT EQUALLY EXPOSED, and the plan is honest about which is which because it changes what the fix is FOR: 12 of them already pass `cwd=<repo root>`, and cwd precedes `PYTHONPATH` on `sys.path`, so a decoy on `PYTHONPATH` does NOT capture them today (measured); for those the pin is DEFENCE IN DEPTH against a future cwd change or a `-P`/`PYTHONSAFEPATH` child. The 2 in `test_completion` set `cwd` to a temp target repo and ARE live-exposed to `PYTHONPATH` (this is F-3's unittest failure), and the 5 in `test_comms_acks` pass no `cwd` at all and so inherit the test process's, which is what F-3's second reproduction exercises by running pytest FROM the decoy directory. Uniformity through one helper is still the right fix; the value claim is corrected, not withdrawn.
- Scope: IN: every unpinned `-m agent_workflows...` spawn in `tests/test_comms_acks.py` (5), `tests/test_completion.py` (2), `tests/test_concurrent_driver_guard.py` (2), `tests/test_project_context.py` (2), `tests/test_project_registry.py` (4), `tests/test_records_untracked_backend.py` (4) goes through `tests/support.py`; `support` gains the two small hooks needed (a module argument and a pinned-env helper); PLUS the ONE unpinned spawn review found in `tests/test_driver_attestation_gate.py` (`CliNoTokenFlagTests.test_finalize_help_has_no_token_flag` passes no `env` and no `cwd`, so F-5's "not defective" verdict is false for it), making 20 sites in seven files. OUT: the spawns in those two files that DO pin explicitly (19 of 20 in `test_oc_runipd.py` and 4 of 5 in `test_driver_attestation_gate.py`); a guard test; changing test assertions.
- Scope-Paths: tests/support.py, tests/test_comms_acks.py, tests/test_completion.py, tests/test_concurrent_driver_guard.py, tests/test_driver_attestation_gate.py, tests/test_project_context.py, tests/test_project_registry.py, tests/test_records_untracked_backend.py, CONTRIBUTING.md
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 17xkyp
- Set: testhyg
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: tcx2ok

## Workflow history
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-808. Reviewed in an isolated lane worktree at HEAD bfdd8821. The 19-site census, the 10 bare-`python3` sites, F-3's two decoy reproductions and F-4 all re-verified exactly. Three corrections: F-5's "not defective" claim is WRONG for one spawn (`test_driver_attestation_gate.CliNoTokenFlagTests.test_finalize_help_has_no_token_flag` passes NO env at all, and its `assertNotIn` assertions pass VACUOUSLY against a decoy); the 19 sites are NOT equally exposed (12 already have `cwd=REPO_ROOT`, which outranks `PYTHONPATH`, so they are defence-in-depth, while only `test_completion`'s 2 are live-exposed via `PYTHONPATH` and `test_comms_acks`'s 5 via cwd inheritance); and E-02's "drop kwargs `run_cli` already defaults" would silently turn two `check=True` spawns into non-raising ones. Also added an AST census that does not miss a variable-assigned argv, which my own first pass did.
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

- [ ] E-02 RE-MEASURE THE CENSUS AT HEAD with a scan that cannot miss a site. A naive `ast.walk` for a list/tuple LITERAL containing the adjacent constants `"-m"` and `"agent_workflows..."` MISSES a spawn whose argv was assigned to a variable first, which is exactly the shape `test_project_context.py` and `test_project_registry.py` use (`cmd = ["python3", "-m", ...]` then `subprocess.run(cmd, ...)`); review's own first pass missed all six of those and found them only after widening. So the scan must ALSO map argv-list assignments to their variable names and match a `subprocess.run`/`Popen`/`check_output`/`check_call` call whose first positional argument is one of those names. Record, per site, the file, line, call function, and whether `cwd=` and `env=` are present, because that triple is what determines exposure.
  - Depends on: E-01
  - Expected outcome: 20 sites across seven files: `test_comms_acks` 5, `test_completion` 2, `test_concurrent_driver_guard` 2 (one `run`, one `Popen`), `test_project_context` 2, `test_project_registry` 4, `test_records_untracked_backend` 4, `test_driver_attestation_gate` 1 (the no-env `CliNoTokenFlagTests` spawn). A literal-only scan reporting 13 or 19 means the widening was not applied.
  - Execution state: pending

- [ ] E-03 CONVERT THE SPAWNS. `subprocess.run([sys.executable|"python3", "-m", "agent_workflows", *args], cwd=..., env=..., capture_output=True, text=True)` becomes `support.run_cli(*args, cwd=..., env=...)`; `-m agent_workflows.comms_acks` spawns use `module="agent_workflows.comms_acks"`; the one `subprocess.Popen` in `test_concurrent_driver_guard.py` (the "genuinely CONTEND" test) keeps `Popen` but gets `env=support.pinned_env()` (it already uses `sys.executable`); the `test_driver_attestation_gate.CliNoTokenFlagTests` spawn goes through `run_cli` too. Every bare `"python3"` in these spawns disappears (`run_cli` uses `sys.executable`). Add `from tests import support` where missing. `test_comms_acks.py` is plain pytest functions with `tmp_path`; keep them as functions. Do not change any assertion, cwd or env content beyond the pin.
  PRESERVE AN EXPLICIT `check=True`; DO NOT "drop kwargs `run_cli` already defaults". `run_cli` uses `kwargs.setdefault("check", False)`, so an omitted `check` makes a previously RAISING spawn non-raising, silently converting a hard failure into an unasserted return code. Two sites in `tests/test_records_untracked_backend.py` (the `install --help` and `migrate-layout --help` pair) pass `check=True` today; both must keep it, and `run_cli` honors a passed-through `check=True` (verified in review: it raises `CalledProcessError` on a nonzero exit). Dropping `capture_output=True`/`text=True` IS safe, because `run_cli` defaults both to the same values.
  - Depends on: E-02
  - Expected outcome: the widened census reports 0 unpinned spawns across the seven files; the two `check=True` sites still pass `check=True`.
  - Execution state: pending

- [ ] E-04 Run each of the SEVEN files under BOTH runners from the repo root: `python3 -m pytest -o addopts="" tests/<file>` and `python3 -m unittest tests.<module>`. `test_comms_acks.py` has no `TestCase` classes (verified: 0, against 11 in `test_completion`, 8 in `test_concurrent_driver_guard`, 3 in `test_project_context`, 1 each in `test_project_registry` and `test_records_untracked_backend`, and 6 in `test_driver_attestation_gate`), so `unittest` collects 0 tests there; record that as expected (pytest is its only runner) rather than as a pass.
  - Depends on: E-03
  - Expected outcome: all pass under pytest; the six `TestCase` modules pass under unittest.
  - Execution state: pending

- [ ] E-05 Demonstrate the pin holds under unittest with a decoy. Create `/tmp/opencode/decoy/agent_workflows/{__init__.py,__main__.py}` where `__main__` prints `DECOY` and exits 0 (and a `comms_acks.py` that does the same). CLEAR ANY INHERITED `PYTHONPATH` FIRST, setting it to the decoy dir ALONE: review's first attempt appeared to show the defect NOT reproducing, purely because the ambient shell already carried a `PYTHONPATH` whose earlier entry answered before the decoy. A repro that leaves the ambient value in place proves nothing in either direction. Then run `PYTHONPATH=/tmp/opencode/decoy python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` and `(cd /tmp/opencode/decoy && PYTHONPATH=/tmp/opencode/decoy python3 -m pytest <repo>/tests/test_comms_acks.py -o addopts="" -p no:cacheprovider)` before and after E-03. ALSO demonstrate the `test_driver_attestation_gate` site, whose failure mode is DIFFERENT and worse: its three `assertNotIn("--driver-token", ...)` assertions pass VACUOUSLY against a decoy that prints `DECOY`, so unlike the other sites it goes GREEN while testing nothing. Show that before the fix the decoy answers that spawn (print the captured stdout, which is `DECOY` rather than a usage block) and after the fix it is the real help text. Note that the in-process import of the test module itself resolves the repo (the test process's `sys.path[0]` is the repo root under `-m unittest`), so only the subprocess is at risk; that is exactly what the decoy exercises.
  - Depends on: E-03
  - Expected outcome: before, the completion test FAILS, comms_acks shows `5 failed, 15 passed`, and the attestation-gate spawn's stdout is `DECOY` while its test still PASSES (the vacuous case); after, all pass with real output. If the before-state does not reproduce, check that `PYTHONPATH` was cleared before adding the decoy rather than concluding the defect is absent.
  - Execution state: pending

### Task group 3: doc and suite

- [ ] E-06 Add ONE sentence to `CONTRIBUTING.md`'s `make test-serial` paragraph, recording that `unittest` does not load `conftest.py` and so loses its role scrub and `PYTHONPATH` pin, that the serial runner is for the isolation-debugging purpose already stated there, and that tests spawn the CLI only through `tests/support.run_cli`. Then run the bare suite.
  - Depends on: E-04, E-05
  - Expected outcome: one added sentence, carrying no em or en dashes (`CONTRIBUTING.md` is user-facing prose) and NOT claiming unittest loses the home sandbox, which `tests/__init__.py` still provides. `AGENTS.md`'s managed "HOW TO RUN THE SUITE" paragraph stays untouched: it already directs a bare `python3 -m pytest` and is generated from `agent_workflows/engine.py`, which is outside the fence (confirmed: the phrase occurs once in `engine.py` and once in the generated `AGENTS.md`). Bare suite green against the review-measured baseline `2598 passed, 2 skipped`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/support.run_cli` is the sanctioned spawn helper (IPD `lhjsu0`, bug `ccbe60`): pins `PYTHONPATH` to `REPO_ROOT` and uses `sys.executable`. It sets its kwargs with `setdefault`, so a caller's explicit `capture_output`/`text`/`check` is HONORED and an OMITTED `check` silently becomes `False` (the `check=True` hazard E-03 names).
- The root `conftest.py` pins `PYTHONPATH` only under pytest; `tests/__init__.py` provides a home sandbox for unittest but no path pin.
- CWD OUTRANKS `PYTHONPATH` on `sys.path`, which is why the 19 authored sites are not equally exposed. Measured in review with a decoy on a cleaned `PYTHONPATH`: a child with `cwd=<repo root>` imports the REPO's package (12 sites), while a child whose cwd is a temp dir with no `agent_workflows/` imports the DECOY (the 2 `test_completion` sites), and a child with no `cwd=` inherits the test process's. A pin is still correct for all of them, but only some are live defects.
- A DECOY REPRODUCTION MUST CLEAR THE AMBIENT `PYTHONPATH` FIRST. Review's first attempt showed the defect apparently NOT reproducing, solely because the invoking shell already exported a `PYTHONPATH` whose earlier entry answered ahead of the decoy. Set `PYTHONPATH` to the decoy directory alone.
- `AGENTS.md` HOW TO RUN THE SUITE already tells agents to run pytest bare; CONTRIBUTING.md names `make test` as canonical and `make test-serial` as a debugging fallback.
- Maintainer rule: no guard tests; tests assert outcomes. This plan adds no test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1..F-5 authored at HEAD `61ef21d8` and re-verified in review at `bfdd8821`. F-6..F-8 found in review at `bfdd8821`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | six files | Unpinned spawns: test_comms_acks 5 (all `agent_workflows.comms_acks`), test_completion 2, test_concurrent_driver_guard 2 (one `run`, one `Popen`), test_project_context 2, test_project_registry 4, test_records_untracked_backend 4. None uses `run_cli`. CONFIRMED exactly, all 19, by an independent widened scan. | per-site scan output with file, line, call function, and the presence of `cwd=`/`env=` |
| F-2 | MED | test_project_context, test_project_registry, test_records_untracked_backend | Bare `"python3"` in all 10 of their spawns, not only the two the brief named in test_records_untracked_backend. CONFIRMED: exactly 10, and exactly those three files repo-wide. | `grep -c '"python3"'`: test_project_context 2, test_project_registry 4, test_records_untracked_backend 4; the other three in-scope files 0 each; `grep -rln` over `tests/*.py` names only those three |
| F-3 | MED | unittest runs | The defect is real, not theoretical: a decoy on `PYTHONPATH` answers the spawn. BOTH halves reproduced verbatim in review. | `PYTHONPATH=<decoy> python3 -m unittest tests.test_completion.CompletionInstallSubprocessTests` -> `Ran 1 test`, `FAILED (failures=1)`; `tests/test_comms_acks.py` under pytest from the decoy cwd -> `5 failed, 15 passed in 0.56s` |
| F-4 | INFO | `support.run_cli` | Cannot spawn a submodule (`-m agent_workflows.comms_acks`) or feed a `Popen`; E-01 adds both hooks. `comms_acks` is not reachable via the `aw` CLI (`aw comms` is an invalid choice). CONFIRMED, including V-01's assertion target. | `run_cli` builds `[sys.executable, "-m", "agent_workflows", *cli_args]`; `aw comms` -> `invalid choice: 'comms'`; `python3 -m agent_workflows.comms_acks --help` exits 0 and its stdout contains `subcommand` |
| F-5 | MED | test_driver_attestation_gate.py, test_oc_runipd.py | **CORRECTED IN REVIEW: THE "NOT DEFECTIVE" VERDICT IS WRONG FOR ONE SPAWN.** `test_oc_runipd.py` is clean (all 20 of its `agent_workflows` spawns pass an `env`, 12 via `_DRIVER_ENV` and the rest via a local pinned `env`). But `test_driver_attestation_gate.py` has FIVE such spawns and only FOUR use `self._env()`; `CliNoTokenFlagTests.test_finalize_help_has_no_token_flag` passes NO `env` and NO `cwd` at all. It is now IN scope (see F-6 for why it is the worst of the set). | per-call AST audit of both files printing the `env=` argument: `test_oc_runipd` 20/20 present; `test_driver_attestation_gate` lines with `self._env(...)` x4 and one call with `env=False` (absent) |
| F-6 | MED | `test_driver_attestation_gate.CliNoTokenFlagTests` | **THIS SITE FAILS SILENTLY GREEN, WHICH IS WORSE THAN THE OTHER 19.** Its three assertions are `assertNotIn("--driver-token"/"--driver-attest"/"--attestation", proc.stdout)`, so a decoy whose stdout is `DECOY` satisfies ALL THREE. Every other site asserts something POSITIVE and therefore fails loudly when hijacked; this one passes while testing nothing, so no runner would ever report it. | driven with a decoy first on a cleaned `PYTHONPATH`: the spawn returns rc 0 with stdout `DECOY`, and `"--driver-token" not in stdout` is `True`, i.e. all three assertions hold vacuously |
| F-7 | MED | E-02's conversion rule | **"DROP KWARGS `run_cli` ALREADY DEFAULTS" WOULD CHANGE BEHAVIOR AT TWO SITES.** `run_cli` uses `kwargs.setdefault("check", False)`, so omitting a previously explicit `check=True` converts a raising spawn into a silently non-raising one. `capture_output`/`text` are genuinely safe to drop (same defaults). | `tests/test_records_untracked_backend.py` `install --help` and `migrate-layout --help` both pass `check=True`; driven: `run_cli("no-such-verb", check=True)` raises `CalledProcessError` while `run_cli("no-such-verb")` returns rc 2 with no raise |
| F-8 | INFO | exposure is not uniform | 12 of the 19 authored sites pass `cwd=<repo root>`, and cwd precedes `PYTHONPATH` on `sys.path`, so a `PYTHONPATH` decoy does NOT capture them today; the pin there is defence in depth. The live-exposed ones are `test_completion`'s 2 (cwd is a temp target repo) and `test_comms_acks`' 5 (no `cwd`, so the test process's is inherited, which is what F-3's second repro exercises). This does not change the fix, only the claim made for it. | with a decoy on a cleaned `PYTHONPATH`: `cwd=<repo root>` -> repo's `__init__.py`; `cwd=/tmp/...` -> decoy's; `cwd=<decoy dir>` -> decoy's |

## Proposed changes (ordered, validatable)

1. E-01: `pinned_env` and `module=` in support.
2. E-02: the widened census (20 sites, seven files).
3. E-03: migrate them, preserving `check=True` where present.
4. E-04, E-05: both runners; decoy demonstration including the vacuous-green site.
5. E-06: one CONTRIBUTING sentence; bare suite.

## Deferred / out of scope (with reason)

- Converting the ALREADY-PINNED spawns in `test_oc_runipd.py` (all 20) and the four pinned ones in `test_driver_attestation_gate.py` to `run_cli` for uniformity: they are correct today; churn without an outcome change. NOTE the fifth spawn in `test_driver_attestation_gate.py` is NOT covered by this declination: it pins nothing and is now in scope (F-5, F-6).
  - Carrier-Declined: no defect in the pinned spawns; uniformity alone does not justify the edit.
- A guard test that fails on any new unpinned spawn: maintainer declined structural guards (2026-09-26).
  - Carrier-Declined: maintainer decision 2026-09-26.

## Scope check

- Over-scope: `tests/support.py` and `CONTRIBUTING.md` are beyond the six files; both are required (F-4; maintainer asked to consider the doc).
- Under-scope (FOUND IN REVIEW, now fixed): `tests/test_driver_attestation_gate.py` was excluded on a false premise. F-5 asserted the file pins explicitly; four of its five `agent_workflows` spawns do, and the fifth (`CliNoTokenFlagTests.test_finalize_help_has_no_token_flag`) passes no `env` and no `cwd`. It is the WORST member of the set, because its three `assertNotIn` assertions pass vacuously against a hijacked child (F-6), so it is now declared and converted in E-03.
- `tests/test_oc_runipd.py` stays out and was VERIFIED rather than assumed: all 20 of its `agent_workflows` spawns pass an `env` (12 `_DRIVER_ENV`, 8 a local pinned `env`).
- `conftest.py` and `tests/__init__.py` are NOT declared and must not be edited: the fix is at the spawn sites, and changing the pytest-only pin or the unittest home sandbox would alter every test's environment for a defect that belongs to 20 call sites. Sibling plan `yx9xsa` (testhyg Order 01) declares `conftest.py`; leave it to that plan.
- `agent_workflows/engine.py` is NOT declared, so the managed `AGENTS.md` paragraph is not touched (E-06 says so and the reason was verified: the phrase lives once in `engine.py` and once in the generated `AGENTS.md`).

## Required tests / validation

- Each of the SEVEN files under `python3 -m pytest -o addopts=""` and `python3 -m unittest` (14 runs); the decoy demonstration; bare suite. No new test (outcome rule; no guard tests).
- THE SUITE IS THE WEAKEST EVIDENCE HERE, AND THE PLAN SHOULD NOT LEAN ON IT. The defect is invisible under pytest, because `conftest.py` already pins `PYTHONPATH`; one affected site (F-6) passes even when its child is fully hijacked, so no runner reports it; and dropping a `check=True` (F-7) is invisible until something exits nonzero. The load-bearing evidence is V-05's decoy before/after pair (including the vacuous-green site) and V-03's proof that both `check=True` spawns kept it.

## Spec / documentation sync

`CONTRIBUTING.md` gains one sentence (E-06); it is user-facing, so write it with no em or en dashes. No `.spec.md` is touched. `AGENTS.md` is generated from `engine.py` and already directs pytest; not edited.

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
  - Required evidence: paste the WIDENED census output BEFORE any conversion, showing 20 sites across seven files with the per-site `cwd=`/`env=` triple, and confirm it includes the six variable-assigned argv sites in `test_project_context`/`test_project_registry` and the `test_driver_attestation_gate` no-env site. A census reporting 13 (literal-only, missing the variable-assigned ones) or 19 (missing the attestation-gate site) is a FAILED E-02, not a smaller number to accept.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the census AFTER (0 unpinned sites across the seven files; the `Popen` site shows `env=support.pinned_env()`); paste `grep -n '"python3"'` over the seven files returning nothing; and paste the two `check=True` sites' post-conversion source showing `check=True` STILL PRESENT (F-7). Dropping either is a failed validation even if the suite stays green, because the suite cannot see the difference until something exits nonzero.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste, per file, the summary line of `python3 -m pytest -o addopts="" tests/<file>` and of `python3 -m unittest tests.<module>` (14 runs across seven files; `test_comms_acks` under unittest shows `Ran 0 tests`, stated as expected rather than as a pass).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the decoy file contents, the command showing `PYTHONPATH` was set to the decoy dir ALONE (not appended to an ambient value), and the decoy runs BEFORE (completion `FAILED (failures=1)`, comms_acks `5 failed, 15 passed`, and the attestation-gate spawn's captured stdout equal to `DECOY` while its test still PASSES) and AFTER (all pass, and that spawn's stdout is the real `ipd finalize --help` usage block). The attestation-gate before/after pair is the load-bearing half: it is the only site whose hijack is invisible to a test runner.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the CONTRIBUTING.md diff (one sentence, no em or en dashes, and not claiming unittest loses the home sandbox, which `tests/__init__.py` still provides); paste the final summary line of a BARE `python3 -m pytest` showing 0 failed, compared against the review-measured baseline `2598 passed, 2 skipped`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Test-harness changes only: 20 spawn sites in SEVEN test files routed through `tests/support.py`, which gains a `pinned_env` helper and a `module=` argument; one sentence in CONTRIBUTING.md. No production code, no assertion changes.

WHAT REVIEW CHANGED. Three corrections, each measured. (1) The seventh file: `tests/test_driver_attestation_gate.py` was excluded because F-5 said it pins explicitly; four of its five spawns do, and the fifth pins nothing. It is the WORST member of the whole set, because its three `assertNotIn` assertions pass VACUOUSLY when the child is hijacked, so that site goes green while testing nothing and no runner would ever report it. (2) E-03's "drop kwargs `run_cli` already defaults" would have converted two `check=True` spawns into silently non-raising ones, since `run_cli` defaults `check` to `False`. (3) The 19 authored sites are NOT equally exposed: 12 already pass `cwd=<repo root>`, which outranks `PYTHONPATH`, so for them the pin is defence in depth rather than a live fix; only `test_completion`'s 2 and `test_comms_acks`' 5 are live-exposed. The fix is unchanged and still right; the claim made for it is now accurate. Review also added a census that cannot miss a variable-assigned argv, having first missed six sites that way.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. A GREEN SUITE IS WEAK EVIDENCE ON THIS PLAN: the defect it fixes is invisible under pytest (whose `conftest.py` already pins `PYTHONPATH`), one affected site passes even when fully hijacked (F-6), and dropping a `check=True` (F-7) changes nothing a green run can see. V-05's decoy before/after pair and V-03's `check=True` proof are the load-bearing evidence.

GENUINE STOP CONDITIONS: (1) if E-05's before-state does not reproduce, verify `PYTHONPATH` was set to the decoy directory ALONE before concluding the defect is absent; an ambient `PYTHONPATH` masked it once in review. (2) If the fix appears to require editing `conftest.py` or `tests/__init__.py`, stop and report: that would change every test's environment, and sibling plan `yx9xsa` owns `conftest.py`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); nothing under `/tmp` is committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `17xkyp` `done` with `--evidence` citing the executed plan.
