# IPD: Treat a Windows NUL stdin as non-interactive at the human-attestation and commit-prompt gates

- Date: 2026-09-26
- Kind: child
- Concern: On Windows a stdin redirected from NUL reports isatty() True (NUL is a character device), so specs.run_set and status_set grant --by-human attestation and git_commit_helper prints a commit prompt for a non-interactive run.
- Scope: IN: one helper term.stdin_is_interactive (isatty plus win32 GetConsoleMode); engine.is_interactive_session delegates to it; the three security-relevant sites (specs.run_set floor, status_set spec floor, git_commit_helper._is_interactive) use it; outcome tests; one CHANGELOG line. OUT: the ~20 prompt-only cli.py sites and other prompt-only sites.
- Scope-Paths: agent_workflows/term.py, agent_workflows/engine.py, agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/git_commit_helper.py, tests/test_stdin_interactive.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: ddo56m
- Blocks-Release: next
- Set: wintty
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: k4vi7z

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ddo56m: require a real console (GetConsoleMode) on win32 at the three stdin gates that grant human attestation or print a commit prompt.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

On Windows a stdin redirected from `NUL` reports `isatty()` True because `NUL` is a character device. Add one helper that also requires a real console (`kernel32.GetConsoleMode` succeeds) on win32, and use it at the three sites where a false "interactive" verdict grants human attestation or prints a commit prompt: `specs.run_set`, `status_set` (spec `by_human` floor), and `git_commit_helper._is_interactive`. `engine.is_interactive_session` delegates to the same helper.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The helper

- [ ] E-01 Add `term.stdin_is_interactive(stream=None) -> bool` to `agent_workflows/term.py`: `stream` defaults to `sys.stdin`; return False if it is None or lacks `isatty`, or if `isatty()` raises (`ValueError`/`OSError`/`AttributeError`) or returns False. Then, only when `sys.platform == "win32"`, import `ctypes` inside the branch, call `ctypes.windll.kernel32.GetStdHandle(-10)` and `GetConsoleMode(handle, ctypes.byref(ctypes.c_ulong()))`, and return False if it returns 0 or anything raises. Otherwise return True. The platform guard means `ctypes.windll` is never touched on POSIX. Docstring states WHY (NUL is a character device) and that the probe checks the process's real STD_INPUT_HANDLE, so a caller passing a non-default `stream` gets the isatty half only on POSIX and both halves on win32.
  - Depends on: none
  - Expected outcome: POSIX behavior equals `bool(sys.stdin.isatty())` with exceptions mapped to False; win32 additionally requires a console.
  - Execution state: pending

- [ ] E-02 Make `engine.is_interactive_session` keep its `plan.yes` and `CI` checks and replace its inline `sys.stdin.isatty()` plus `GetConsoleMode` block with `return term.stdin_is_interactive()` (import from `.term`, which `engine` already imports `Term` from).
  - Depends on: E-01
  - Expected outcome: one implementation of the console probe; `engine.is_interactive_session` behavior unchanged on every platform.
  - Execution state: pending

### Task group 2: The three security-relevant sites

- [ ] E-03 In `specs.run_set`, replace `hasattr(sys.stdin, "isatty") and sys.stdin.isatty()` inside the `is_interactive = (...)` expression of the authority floor with `_term.stdin_is_interactive()` (function-local import, matching the module's existing `from agent_workflows import term as _term` usage in `run_check`). The `--agent`/`--as-agent`/`--json` exclusions stay.
  - Depends on: E-01
  - Expected outcome: a `NUL` stdin on Windows no longer grants `by_human`; POSIX unchanged.
  - Execution state: pending

- [ ] E-04 In `status_set` (the spec `by_human` floor inside the transition validator, `is_interactive = (` with `hasattr(sys.stdin, "isatty") and sys.stdin.isatty()`), make the same replacement.
  - Depends on: E-01
  - Expected outcome: the positional spelling `aw specs set approved <id6>` behaves as E-03 does.
  - Execution state: pending

- [ ] E-05 In `git_commit_helper._is_interactive`, keep the explicit-override branch and replace the `try: return bool(sys.stdin.isatty()) except ...` fallback with `return stdin_is_interactive()` (the helper already maps the exceptions). Update the docstring's "falls back to `sys.stdin.isatty()`" to name the helper.
  - Depends on: E-01
  - Expected outcome: no commit prompt is printed (and nothing blocks on `input()`) on a Windows `NUL` stdin.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-06 Add `tests/test_stdin_interactive.py`. Each test installs its OWN fake stdin (`mock.patch("sys.stdin", _Fake(isatty=True))`) so the `tests/__init__.py` win32 `_NotATty` wrapper (which forces `isatty()` False in the suite and so MASKS this bug) cannot decide the outcome. Tests: (a) with `sys.platform` patched to `"win32"` and a fake `ctypes.windll` (patched via `mock.patch.object(ctypes, "windll", <fake with kernel32.GetStdHandle -> 1, GetConsoleMode -> 0>, create=True)`), `term.stdin_is_interactive()` is False; (b) same with `GetConsoleMode -> 1` is True; (c) under the (a) conditions, `specs.run_set` for a `reviewed` spec with `--status approved`, no `--by-human`, returns 1, stderr contains `human-only transition`, and the file is byte-identical; (d) under the (a) conditions, `git_commit_helper.offer_commit(..., interactive=None)` does not call `input` (patch `builtins.input` to raise) and returns an outcome whose status is `skipped` (`git_commit_helper.STATUS_SKIPPED`); (e) POSIX: `sys.platform` patched to `"linux"`, fake stdin `isatty()` True, `windll` not present, `stdin_is_interactive()` is True and never touches `ctypes.windll`.
  - Depends on: E-03, E-05
  - Expected outcome: five tests passing on Linux, macOS and Windows; (c) fails on the base commit.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-07 Add one `- Fixed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`: on Windows, running `aw` with input redirected from `NUL` was treated as an interactive session, so `aw specs set ... --status approved` could record a human approval without `--by-human`, and a commit prompt could be printed; a real console is now required. No em or en dashes.
  - Depends on: E-03
  - Expected outcome: one line, no dashes.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest` and `aw sanitize --agent` locally, then confirm the `unittest (windows-latest, ...)` job of `.github/workflows/tests.yml` passes on the pushed branch (the maintainer pushes; the executor does not). The Windows CI job is the REAL verification of the win32 branch: the local tests fake `ctypes.windll`, which proves the logic but not the actual Win32 call.
  - Depends on: E-06, E-07
  - Expected outcome: 0 failed locally; Windows CI green, or the plan's report states it is awaiting the maintainer's push.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `engine.is_interactive_session` (~:1940-1958) already contains the correct win32 probe (`GetStdHandle(-10)`, `GetConsoleMode`), but takes an `InstallPlan` and also short-circuits on `plan.yes` and `CI`, so it cannot be called from the setters as is.
- `tests/__init__.py` (~:70-92) reopens stdin on `os.devnull` and, on win32, wraps it in a `_NotATty` `TextIOWrapper` subclass. That wrapper is why the suite passes on Windows today while the product code is wrong: tests never see the real `NUL` `isatty()` True.
- Existing tests patch `sys.stdin.isatty` (e.g. `tests/test_specs_verbs.py` interactive-approval case, `tests/test_status_set.py` `test_spec_approved_interactive_confirmation`). On POSIX the helper reads the same `isatty`, so they still pass; on win32 CI they would now also need a console. Those tests must be checked on Windows CI (E-08).
- Tests: outcome only (maintainer standing rule). No test greps for call sites or pins the helper's source.
- Commit via `aw commit k4vi7z -- <paths>`; never push. Line numbers at HEAD `92679444`, approximate.

## Findings

| # | Location (HEAD 92679444) | Finding |
| --- | --- | --- |
| F-1 | `specs.run_set` authority floor (~:637-645) | Confirmed: `is_interactive = (hasattr(sys.stdin, "isatty") and sys.stdin.isatty() and not agent/as_agent/json)` then `setattr(args, "by_human", True)`. |
| F-2 | `status_set` spec floor (~:648-655) | Confirmed, same expression. |
| F-3 | `git_commit_helper._is_interactive` (~:302-315) | Confirmed: `bool(sys.stdin.isatty())` fallback. |
| F-4 | `engine.is_interactive_session` (~:1940-1958) | Confirmed; the probe to reuse. |
| F-5 | `tests/__init__.py` (~:78-89) | Confirmed: the `_NotATty` wrapper masks the bug in the suite. E-06 installs its own fake stdin per test so the wrapper is irrelevant to the outcome. |
| F-6 | an existing test that patches `sys.stdin.isatty` to True and expects approval (`tests/test_specs_verbs.py` "Interactive TTY approval succeeds directly", `tests/test_status_set.py::test_spec_approved_interactive_confirmation`) | RISK NOT IN THE BRIEF: on the Windows CI job these now reach the real `GetConsoleMode`, which fails on a CI runner, so they would start failing there. E-06 does not change them; E-08 must check Windows CI and, if they fail, patch `term.stdin_is_interactive` to True in those two tests (in scope as a test-only adjustment; list them via `--scope-reason` at finalize). |
| F-7 | `grep -c "stdin.isatty" agent_workflows/cli.py` = 21 | Confirmed ~20 prompt-only sites in `cli.py` are out of scope (maintainer-approved narrow scope). |

## Proposed changes (ordered, validatable)

1. E-01 helper; E-02 engine delegates.
2. E-03 to E-05 replace the three security-relevant checks.
3. E-06 outcome tests; E-07 CHANGELOG; E-08 verify locally and on Windows CI.

## Deferred / out of scope (with reason)

- The ~20 prompt-only `sys.stdin.isatty()` sites in `cli.py` (and similar prompt-only sites in `oc_runipd`, `agy_runipd`, `install_wizard`).
  - Carrier-Declined: maintainer-approved narrow scope for this plan; those sites only choose whether to show a prompt, and a prompt on a Windows `NUL` stdin reads EOF and falls back to the non-interactive answer, so they grant no authority. Revisit only if a prompt-only site is shown to block or to write into machine output.

## Scope check

- Over-scope: none.
- Under-scope: the two existing interactive tests may need a Windows-only adjustment (F-6); declared there, not pre-emptively edited.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_stdin_interactive.py` asserts observable outcomes (the helper's verdict, a refused approval with the file unchanged, no prompt issued) under a patched platform and a faked Win32 API. Few tests (five). Run the suite BARE: `python3 -m pytest`. The Windows CI job (`windows-latest` in the `tests.yml` matrix) is the real verification of the win32 branch, since the local tests fake `ctypes.windll`.

## Spec / documentation sync

No `.spec.md` is amended: the human-attestation contract (`--by-human`, or an interactive session) is unchanged; this plan makes "interactive" mean a real console on Windows as it already does on POSIX. `CHANGELOG.md` gains one line (E-07).

## Open questions

### OQ-01: Narrow fix (three sites) or replace every stdin.isatty() in the package?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Narrow fix, maintainer-approved in the authoring brief. Only the three sites grant authority or can print into machine output; the rest are prompt-only (Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import sys; from agent_workflows import term; print(term.stdin_is_interactive())" < /dev/null` printing `False`, and the same run under `script -q -c ... /dev/null` (or any real TTY) printing `True`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/engine.py` showing `is_interactive_session` delegating, and `python3 -m pytest tests/test_installer.py -o addopts="" -q -k interactive` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the output of test (c) from E-06 (node id and PASSED) and `git diff agent_workflows/specs.py` limited to the authority floor.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a scratch-repo run of `python3 -m agent_workflows specs set approved <id6> --yes < /dev/null; echo rc=$?` on a `reviewed` spec showing a non-zero exit and a refusal naming `--by-human` (POSIX regression guard), plus `git diff agent_workflows/status_set.py` limited to the floor.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the output of test (d) from E-06 (PASSED) and `python3 -m pytest tests/test_git_commit_helper.py -o addopts="" -q` all passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_stdin_interactive.py -o addopts="" -v` showing 5 passed, and the same file run against the base commit (in `git worktree add /tmp/opencode/base <base-sha>`, with the helper absent) showing test (c) FAIL (or erroring on the missing helper for (a)/(b)/(e), which is expected).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md` showing one added `- Fixed:` line and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed, `aw sanitize --agent` exit 0, and EITHER the Windows CI job result (`gh run view <id> --json jobs` excerpt showing `unittest (windows-latest, ...)` `conclusion: success`) OR an explicit statement that Windows CI has not yet run because the branch is unpushed, in which case this V-item stays `pending` and the plan is not finalized.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one helper and its three authority-granting callers; the engine delegation removes the only existing copy of the probe.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a Windows-only behavior change at three gates (a redirected `NUL` stdin is no longer a human), one new helper in `term.py`, five outcome tests, one CHANGELOG line. Finalization requires the Windows CI job, which needs the maintainer to push (the executor never pushes).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `engine.py` only `is_interactive_session`, within `specs.py` only the `run_set` authority floor, within `status_set.py` only the spec `by_human` floor, within `git_commit_helper.py` only `_is_interactive`. Do not expand scope casually; if the work genuinely requires a file outside the fence (for example the two existing interactive tests in F-6), make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to one of these functions that cannot be safely combined.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run, and never claim Windows CI passed without the job result. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit k4vi7z -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize k4vi7z --actor <agent/model> --message <summary> --apply` (the runner owns it in a lane). This plan inherits `- Blocks-Release: next` from `ddo56m`; after execution set `ddo56m` `done` with `--evidence` citing the executed plan.
