# IPD: Restore behavioral pty coverage of pwatch --no-color suppression

- Date: 2026-10-14
- Kind: child
- Concern: The `--no-color` flag of `aw pwatch` has no live behavioral guard on a real terminal since `tests/test_pwatch.py` was deleted in `19313eed`; the only remaining `--no-color` exercises run through a pipe, where color is off regardless of the flag.
- Scope: Add one new behavioral test module that runs the packaged `agent_workflows.pwatch` on a real pty and asserts on emitted bytes: `--no-color` suppresses ANSI, a control case without the flag emits ANSI, and `TERM=dumb` stays plain. No production code change.
- Scope-Paths: tests/test_pwatch_tty_color.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 081smx
- Set: 081smx
- Order: 1
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: k6twdf

## Workflow history

- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored review-ready from backlog `081smx`.

## Goal

Restore a behavioral (outcome-only, P16-compliant) test proving that `pwatch --no-color` emits no ANSI escape when stdout IS a terminal, with a control proving a capable terminal otherwise does get color, so dropping the flag conjunct in `agent_workflows.pwatch.main` fails the suite again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Author the pty behavioral test module

- [ ] E-01 Create `tests/test_pwatch_tty_color.py` with a helper that runs `python -m agent_workflows.pwatch <argv>` under `pty.fork` (child `os.execve`s immediately; env has `NO_COLOR`/`FORCE_COLOR` removed, `TERM=xterm-256color`, `PYTHONPATH` set to the repo root, plus per-case overrides), drains the master fd until EIO/EOF, waits for the child, and returns the captured bytes plus exit status. Skip the module (`unittest.skipUnless`) when `pty` is unavailable (non-POSIX).
  - Depends on: none
  - Expected outcome: The helper exists in the new file and returns raw pty bytes from a real pwatch run.
  - Execution state: pending
- [ ] E-02 Add test `test_no_color_flag_suppresses_color_on_a_real_tty` (argv `--once --no-color python`, asserts `b"\033["` absent and exit status 0) and the control `test_a_real_tty_gets_color_without_the_flag` (argv `--once python`, asserts `b"\033["` present).
  - Depends on: E-01
  - Expected outcome: Both tests pass against the current `pwatch.main` color expression `color_enabled = not args.no_color and term.should_color(sys.stdout)`.
  - Execution state: pending
- [ ] E-03 Add test `test_term_dumb_is_plain_on_a_real_tty` (argv `--once python`, env `TERM=dumb`, asserts `b"\033["` absent), covering the shared-decision behavior on the same pty path.
  - Depends on: E-01
  - Expected outcome: The test passes against current code.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must drive the code (here a subprocess on a pty) and assert on real output bytes and exit status; no `inspect`/`ast`/regex over source. The backlog item restates this ("only behavioral outcomes may be restored, never a source-reading pin").
- The suite runs bare as `python3 -m pytest` with `-n auto` from `pyproject.toml` `addopts`; `pty.fork` in an xdist worker emits a CPython `DeprecationWarning` about forking a multi-threaded process, which is safe because the child `execve`s immediately (recorded in the deleted `19313eed^:tests/test_pwatch.py` `ColorDecisionOnARealTtyTests._ansi_on_a_pty` docstring).
- Existing color tests (`tests/test_generic_color_depth.py`) use fake `isatty()` StringIO objects, which cannot exercise `pwatch.main`'s real `sys.stdout`; no live test uses `pty` against pwatch (`rg -l "pty.fork" tests` returns only `tests/test_git_commit_helper.py` and `tests/conformance_matrix.py`, neither for pwatch).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The flag guard lives in `agent_workflows.pwatch.main`: `color_enabled = not args.no_color and term.should_color(sys.stdout)`; its comment states no live guard asserts the pty behavior since `19313eed`. | `agent_workflows/pwatch.py` comment containing "deleted in `19313eed`; no live guard currently asserts" |
| F-02 | Plan `ev7t1w` site S-21 classified this as `RETIRE-UNGUARDED`: the deleted `ColorDecisionOnARealTtyTests.test_no_color_flag_still_suppresses_color_on_a_real_tty` was the only pty exercise. | `.aw/records/plans/*/20261011-iosmvn-03-ev7t1w-*.ipd.md` row S-21 |
| F-03 | A pipe cannot distinguish a working flag from a removed one, because `isatty()` is False either way; the deleted docstring records all 10 piped tests still passing with the conjunct dropped (measured 2026-09-19). | `19313eed^:tests/test_pwatch.py` class docstring |
| F-04 | `FORCE_COLOR` on a pipe is a separate property not named by backlog `081smx`; it is excluded here. | Backlog item text names only "--no-color suppression on a real TTY" |

## Proposed changes (ordered, validatable)

1. New file `tests/test_pwatch_tty_color.py` with the pty helper (E-01).
2. The flag-suppression test plus its non-vacuity control (E-02).
3. The `TERM=dumb` plain-output test on the same helper (E-03).

## Deferred / out of scope (with reason)

- Restoring `test_force_color_reaches_a_pipe` and the other piped pwatch tests from the deleted file: not named by backlog `081smx` (F-04); any such gap belongs to its own item.
- Any change to `agent_workflows/pwatch.py` or `agent_workflows/term.py`: the behavior is correct today; this plan only restores the guard. The stale comment in `pwatch.main` that says "no live guard currently asserts this pty behavior" is left alone because the file is outside Scope-Paths; a reviewer may choose to add it.

## Scope check

- Over-scope: none.
- Under-scope: none; the falsifiability of the restored guard is demonstrated in V-02 by a temporary local mutation that is reverted and never committed.

## Required tests / validation

- `python3 -m pytest tests/test_pwatch_tty_color.py` passes (all three tests).
- Mutation check: temporarily change `not args.no_color and term.should_color(sys.stdout)` to `term.should_color(sys.stdout)` in a scratch edit, rerun the new module, observe `test_no_color_flag_suppresses_color_on_a_real_tty` FAIL, then `git checkout -- agent_workflows/pwatch.py` and confirm `git diff --name-only` shows no production change.
- Full suite `python3 -m pytest` passes bare.
- The new file contains no `inspect`, `ast`, or source-reading of production modules (P16).

## Spec / documentation sync

N/A: no behavior or contract changes; this plan adds a test only, and no spec describes pwatch's test coverage.

## Open questions

### OQ-01: Should the stale "no live guard" comment in `pwatch.main` be updated?

- Blocking: no
- Status: deferred
- Owner: maintainer (trigger: next edit of agent_workflows/pwatch.py)
- Resolution or deferral rationale: Deferred. Editing `agent_workflows/pwatch.py` would widen scope beyond the test-only change the backlog item asks for; the comment is accurate history ("deleted in `19313eed`") and a follow-up can point it at the new test.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `git diff --name-only` (or `git show --stat`) of the execution commit showing only `tests/test_pwatch_tty_color.py`, plus pasted `rg -n "pty.fork|os.execve|skipUnless" tests/test_pwatch_tty_color.py` output showing the helper uses a real pty and execs immediately, and `rg -n "inspect|import ast|read_text" tests/test_pwatch_tty_color.py` returning no hits.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted actual output of `python3 -m pytest tests/test_pwatch_tty_color.py -o addopts="" -v` showing both E-02 tests PASSED; AND pasted output of the same command with the flag conjunct temporarily removed from `pwatch.main` showing `test_no_color_flag_suppresses_color_on_a_real_tty` FAILED, followed by pasted `git diff --name-only agent_workflows/` returning empty after reverting. The observation is produced by the tests E-02 creates.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted actual pytest output showing `test_term_dumb_is_plain_on_a_real_tty` PASSED, and pasted bare `python3 -m pytest` summary line (`N passed`) with no failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- tests/test_pwatch_tty_color.py`; never commit the temporary mutation of `agent_workflows/pwatch.py` used in V-02, and never push. Move to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
