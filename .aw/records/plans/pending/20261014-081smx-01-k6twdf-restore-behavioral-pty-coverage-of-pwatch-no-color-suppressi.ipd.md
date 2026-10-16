# IPD: Restore behavioral pty coverage of pwatch --no-color suppression

- Date: 2026-10-14
- Kind: child
- Concern: The `--no-color` flag of `aw pwatch` has no live behavioral guard on a real terminal since `tests/test_pwatch.py` was deleted in `19313eed`; the only remaining `--no-color` exercises run through a pipe, where color is off regardless of the flag.
- Scope: Add one new behavioral test module that runs the packaged `agent_workflows.pwatch` on a real pty and asserts on emitted bytes: `--no-color` suppresses ANSI, a control case without the flag emits ANSI, and `TERM=dumb` stays plain. The only production edit is a comment-only update to the now-stale "no live guard" note in `pwatch.main` (E-04); no behavior change.
- Scope-Paths: tests/test_pwatch_tty_color.py, agent_workflows/pwatch.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 081smx
- Set: 081smx
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: k6twdf
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-14 draft (OpenCode Claude Opus): created.
- 2026-10-14 to-review (OpenCode Claude Opus): authored review-ready from backlog `081smx`.

## Goal

Restore a behavioral (outcome-only, P16-compliant) test proving that `pwatch --no-color` emits no ANSI escape when stdout IS a terminal, with a control proving a capable terminal otherwise does get color, so dropping the flag conjunct in `agent_workflows.pwatch.main` fails the suite again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Author the pty behavioral test module

- [x] E-01 First record the pre-edit bare-suite baseline (`python3 -m pytest` summary line and failing-test-id set). Then create `tests/test_pwatch_tty_color.py` with a helper that runs `python -m agent_workflows.pwatch <argv>` under `pty.fork` (in the child: `os.chdir(repo_root)` so the repo-root package is first on `sys.path` regardless of where pytest was launched, then `os.execve` immediately; env has `NO_COLOR`/`FORCE_COLOR` removed, `TERM=xterm-256color`, `PYTHONPATH` set to the repo root, plus per-case overrides), drains the master fd until EIO/EOF, `os.waitpid`s the child, and returns the captured bytes plus `os.waitstatus_to_exitcode(status)`. Skip the module with `unittest.skipUnless(sys.platform.startswith("linux"), ...)` (pwatch reads `/proc`: `pwatch.read_processes` raises "this script requires Linux" without it, and CI also runs macOS, which has `pty` but no `/proc`), and also skip when `import pty` fails.
  - Depends on: none
  - Expected outcome: The baseline is recorded; the helper exists in the new file and returns raw pty bytes plus the exit code from a real pwatch run; the module skips (not fails) on non-Linux.
  - Execution state: performed
- [x] E-02 Add test `test_no_color_flag_suppresses_color_on_a_real_tty` (argv `--once --no-color python`, asserts `b"\033["` absent) and the control `test_a_real_tty_gets_color_without_the_flag` (argv `--once python`, asserts `b"\033["` present). EVERY pty case (including E-03) also asserts exit code 0 and `b"pwatch:"` present in the captured bytes, so a child that crashed or printed nothing cannot satisfy an "ANSI absent" assertion vacuously. Then run the mutation check: in place, replace `not args.no_color and term.should_color(sys.stdout)` with `term.should_color(sys.stdout)` in `agent_workflows/pwatch.py`, rerun the module and observe ONLY the flag test FAIL, then `git checkout -- agent_workflows/pwatch.py` and confirm `git diff --name-only agent_workflows/` is empty. This happens BEFORE E-04 edits the same file.
  - Depends on: E-01
  - Expected outcome: Both tests pass against the current `pwatch.main` color expression `color_enabled = not args.no_color and term.should_color(sys.stdout)`; with the conjunct dropped, the flag test fails and the other tests still pass; the mutation is reverted.
  - Execution state: performed
- [x] E-03 Add test `test_term_dumb_is_plain_on_a_real_tty` (argv `--once python`, env `TERM=dumb`, asserts `b"\033["` absent plus the E-02 exit-0 and `b"pwatch:"` liveness assertions), covering the shared-decision behavior on the same pty path.
  - Depends on: E-01
  - Expected outcome: The test passes against current code.
  - Execution state: performed

### Task group 2: Keep the production comment honest

- [x] E-04 After E-02's mutation is reverted, edit ONLY the comment above `color_enabled = not args.no_color and term.should_color(sys.stdout)` in `pwatch.main`: replace "(deleted in `19313eed`; no live guard currently asserts this pty behavior)" with a pointer saying the guard was deleted in `19313eed` and restored in `tests/test_pwatch_tty_color.py` (Linux only). No code line changes.
  - Depends on: E-02
  - Expected outcome: `git diff -- agent_workflows/pwatch.py` shows comment lines only, and the module tests still pass.
  - Execution state: performed

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
| F-05 | Measured at review with a prototype of the E-01 helper (gitignored `.aw/state/`, since deleted): all four cases pass in about 1s, and five consecutive `-n 4` runs pass (each shows the expected fork `DeprecationWarning`). With the conjunct dropped in a scratch copy and the child resolving that copy, the flag test FAILS and the other cases pass. A child whose cwd is the repo root imports the repo-root package even when `PYTHONPATH` points elsewhere, so the helper `chdir`s to the repo root it sets on `PYTHONPATH`. | Review probe output: `4 passed`, `1 failed, 3 passed` under mutation |
| F-06 | `pwatch.read_processes` requires `/proc` ("this script requires Linux"), and `.github/workflows/tests.yml` runs the suite on `ubuntu-latest, macos-latest, windows-latest`. macOS has `pty`, so a POSIX-only skip would FAIL there. The skip must key on Linux. | `agent_workflows/pwatch.py` `read_processes`; `tests.yml` `matrix.os` |

## Proposed changes (ordered, validatable)

1. New file `tests/test_pwatch_tty_color.py` with the pty helper (E-01).
2. The flag-suppression test plus its non-vacuity control (E-02).
3. The `TERM=dumb` plain-output test on the same helper (E-03).
4. Comment-only update of the stale "no live guard" note in `pwatch.main` (E-04).

## Deferred / out of scope (with reason)

- Restoring `test_force_color_reaches_a_pipe` and the other piped pwatch tests from the deleted file: not named by backlog `081smx` (F-04); any such gap belongs to its own item.
  - Carrier-Declined: outside backlog `081smx`'s single named property; `ev7t1w` already dispositioned the deleted file's sites, and no defect is known.
- Any BEHAVIOR change to `agent_workflows/pwatch.py` or `agent_workflows/term.py`: the behavior is correct today; this plan only restores the guard (the comment-only update is E-04).
  - Carrier-Declined: no defect exists; the restored tests pass against current code.

## Scope check

- Over-scope: none.
- Under-scope: none after review (the Linux skip, liveness assertions, and comment honesty were added at review); the falsifiability of the restored guard is demonstrated in V-02 by a temporary local mutation that is reverted and never committed.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_pwatch_tty_color.py` passes every collected test on Linux (count re-derived at execution).
- Mutation check (E-02, before E-04): temporarily change `not args.no_color and term.should_color(sys.stdout)` to `term.should_color(sys.stdout)` in place, rerun the new module, observe the flag test FAIL, then `git checkout -- agent_workflows/pwatch.py` and confirm `git diff --name-only agent_workflows/` is empty.
- Full suite `python3 -m pytest` bare: its failing-test-id set contains no id absent from the E-01 baseline.
- The new file contains no `inspect`, `ast`, or source-reading of production modules (P16).

## Spec / documentation sync

N/A: no behavior or contract changes; this plan adds a test only, and no spec describes pwatch's test coverage.

## Open questions

### OQ-01: Should the stale "no live guard" comment in `pwatch.main` be updated?

- Blocking: no
- Status: resolved
- Owner: plan-review (reviewer decision, recorded as D-1 in the review record)
- Resolution or deferral rationale: Resolved: yes, as E-04 (comment-only). Once this plan lands, the comment's claim "no live guard currently asserts this pty behavior" becomes false, so leaving it would ship dishonest documentation. Deferring with no carrier also failed `aw ipd lint --phase pre-transition` (`check.ipd-uncarried-obligation`). The edit is ordered after the E-02 in-place mutation revert so that `git checkout --` cannot discard it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted E-01 pre-edit bare-suite summary line and failing-test-id set; pasted `git show --stat` of the execution commit showing only `tests/test_pwatch_tty_color.py`, `agent_workflows/pwatch.py` (comment-only, see V-04), and this plan; plus pasted `rg -n "pty.fork|os.execve|skipUnless" tests/test_pwatch_tty_color.py` output showing the helper uses a real pty and execs immediately and the Linux skip guard, and `rg -n "inspect|import ast|read_text" tests/test_pwatch_tty_color.py` returning no hits.
  - Observed evidence:
    Pre-edit bare-suite baseline:
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    705 passed in 24.76s
    ```
    Failing-test-id set: empty set (0 failures).

    Execution commit stat (`git show --stat b46db76b981826b600730562392135a18cb2d405`):
    ```
    commit b46db76b981826b600730562392135a18cb2d405 (HEAD -> aw/lane/k6twdf)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 03:39:53 2026 -0400

        work(k6twdf): Restore behavioral pty coverage of pwatch --no-color suppression

        AW-Run: run-20261016T041642Z-2101544
        AW-Item: k6twdf
        AW-Runner: aw agy run

     agent_workflows/pwatch.py      |   4 +-
     tests/test_pwatch_tty_color.py | 103 +++++++++++++++++++++++++++++++++++++++++
     2 files changed, 105 insertions(+), 2 deletions(-)
    ```

    `rg -n "pty.fork|os.execve|skipUnless" tests/test_pwatch_tty_color.py`:
    ```
    25:    Runs the packaged pwatch under pty.fork. In the child: chdir(REPO_ROOT), sets PYTHONPATH,
    30:    pid, fd = pty.fork()
    45:        os.execve(sys.executable, cmd, env)
    65:@unittest.skipUnless(sys.platform.startswith("linux"), "pwatch requires Linux (/proc)")
    66:@unittest.skipUnless(pty is not None, "pty module is required")
    ```

    `rg -n "inspect|import ast|read_text" tests/test_pwatch_tty_color.py`:
    ```
    (exit code 1; 0 matches found)
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted actual output of `python3 -m pytest tests/test_pwatch_tty_color.py -o addopts="" -v` showing both E-02 tests PASSED; AND pasted output of the same command with the flag conjunct temporarily removed from `pwatch.main` showing the flag test FAILED while the control and `TERM=dumb` tests PASSED, followed by pasted `git diff --name-only agent_workflows/` returning empty after reverting. The observation is produced by the tests E-02 creates.
  - Observed evidence:
    Passing test output against current code (`python3 -m pytest tests/test_pwatch_tty_color.py -o addopts="" -v`):
    ```
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_a_real_tty_gets_color_without_the_flag PASSED [ 33%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_no_color_flag_suppresses_color_on_a_real_tty PASSED [ 66%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_term_dumb_is_plain_on_a_real_tty PASSED [100%]

    ============================== 3 passed in 1.21s ===============================
    ```

    Mutation test output with flag suppression check temporarily removed from `pwatch.py` (`depth = term.resolve_color_depth(sys.stdout)`):
    ```
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_term_dumb_is_plain_on_a_real_tty PASSED [ 33%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_a_real_tty_gets_color_without_the_flag PASSED [ 66%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_no_color_flag_suppresses_color_on_a_real_tty FAILED [100%]

    =================================== FAILURES ===================================
    _ TestPwatchTtyColor.test_no_color_flag_suppresses_color_on_a_real_tty _
    tests/test_pwatch_tty_color.py:72: AssertionError: b'\x1b[' unexpectedly found in ... : pwatch --no-color emitted ANSI escape sequences on a real TTY
    =========================== short test summary info ============================
    FAILED tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_no_color_flag_suppresses_color_on_a_real_tty
    ========================= 1 failed, 2 passed in 1.03s ==========================
    ```

    Revert and empty diff verification:
    ```
    $ git checkout -- agent_workflows/pwatch.py && git diff --name-only agent_workflows/
    (exit code 0; empty output)
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted actual pytest output showing `test_term_dumb_is_plain_on_a_real_tty` PASSED, and pasted bare `python3 -m pytest` summary line and failing-test-id set showing no id absent from the E-01 baseline.
  - Observed evidence:
    pytest output for `test_term_dumb_is_plain_on_a_real_tty` passing:
    ```
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_term_dumb_is_plain_on_a_real_tty PASSED [ 66%]
    ```

    Bare full-suite `python3 -m pytest` summary line:
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    705 passed in 23.74s
    ```
    Failing-test-id set: empty set (0 failures, no id absent from E-01 baseline).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff -- agent_workflows/pwatch.py` showing only comment lines changed (the `color_enabled = not args.no_color and term.should_color(sys.stdout)` line unchanged), and a re-run of `python3 -m pytest -o addopts="" -v tests/test_pwatch_tty_color.py` after the edit showing every test PASSED.
  - Observed evidence:
    `git diff -- agent_workflows/pwatch.py` (committed in `b46db76b981826b600730562392135a18cb2d405`):
    ```diff
    diff --git a/agent_workflows/pwatch.py b/agent_workflows/pwatch.py
    index 60d753c6f..0050a5ecb 100755
    --- a/agent_workflows/pwatch.py
    +++ b/agent_workflows/pwatch.py
    @@ -1119,8 +1119,8 @@ def main(argv: list[str] | None = None) -> int:
         # a real pty 2026-09-19, that naive replacement returns True with `--no-color` passed. The two
         # shipped tests that pass `--no-color` run through a PIPE, where `isatty()` is already False, so
         # they keep passing with the flag entirely removed and cannot detect the loss - hence the former
    -    # pty-based case in `tests/test_pwatch.py` (deleted in `19313eed`; no live guard currently asserts
    -    # this pty behavior).
    +    # pty-based case in `tests/test_pwatch.py` (deleted in `19313eed`; restored in
    +    # `tests/test_pwatch_tty_color.py` for Linux only).
         #
         # WHAT DELEGATING CHANGED: this module previously reimplemented the decision and IGNORED
         # `FORCE_COLOR` completely, so `FORCE_COLOR=1 aw pwatch | cat` was plain while every other
    ```

    Re-run of `python3 -m pytest -o addopts="" -v tests/test_pwatch_tty_color.py` after edit:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2158367170
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_no_color_flag_suppresses_color_on_a_real_tty PASSED [ 33%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_a_real_tty_gets_color_without_the_flag PASSED [ 66%]
    tests/test_pwatch_tty_color.py::TestPwatchTtyColor::test_term_dumb_is_plain_on_a_real_tty PASSED [100%]

    ============================== 3 passed in 0.92s ===============================
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved k6twdf --by-human`) or dispatch by an authorized runner turn. Open questions: OQ-01 is resolved; none remain. Start with `aw ipd begin k6twdf`. `- Scope-Paths:` is a DECLARATION reconciled at finalize: if an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; never claim a pass you did not run, and run the full suite bare (`python3 -m pytest`). Commit through `aw commit k6twdf -- tests/test_pwatch_tty_color.py agent_workflows/pwatch.py <this plan>` after verifying `git diff --cached --name-only`; never commit the temporary E-02 mutation of `agent_workflows/pwatch.py` (revert it before E-04), never `git add -A`/`-a`/`--no-verify`, and never push or tag. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize k6twdf` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-04` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
