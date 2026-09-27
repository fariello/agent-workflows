# IPD: Treat a Windows NUL stdin as non-interactive at the human-attestation and commit-prompt gates

- Date: 2026-09-26
- Kind: child
- Concern: On Windows a stdin redirected from NUL reports isatty() True (NUL is a character device), so specs.run_set and status_set grant --by-human attestation and git_commit_helper prints a commit prompt for a non-interactive run.
- Scope: IN: one helper term.stdin_is_interactive (isatty plus win32 GetConsoleMode); engine.is_interactive_session delegates to it; the three security-relevant sites (specs.run_set floor, status_set spec floor, git_commit_helper._is_interactive) use it; outcome tests; one CHANGELOG line. OUT: the ~20 prompt-only cli.py sites and other prompt-only sites.
- Scope-Paths: agent_workflows/term.py, agent_workflows/engine.py, agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/git_commit_helper.py, tests/test_stdin_interactive.py, tests/test_specs_verbs.py, tests/test_status_set.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: ddo56m
- Blocks-Release: next
- Set: wintty
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: k4vi7z
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-006 all FIXED. Re-derived every cited construct at HEAD 48e8c097 and drove the real commands: a pty-stdin plus piped-stdout run of 'aw specs set --status approved' already fabricates a --by-human provenance line (F-10); git_commit_helper blocks on input() in that same shape ON LINUX (F-8, now carried by E-09); V-02's prescribed command deselected all 120 tests in a module the bare suite skips entirely (F-9). Split E-06 into E-06/E-10/E-11, added E-09, rewrote all eight V-items, and resolved OQ-02 so an unpushable Windows CI job no longer strands a completed plan. Findings in .aw/records/reviews/20260926-wintty-01-k4vi7z-treat-a-windows-nul-stdin-as-non-interactive-at-the-human-at.review.md
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ddo56m: require a real console (GetConsoleMode) on win32 at the three stdin gates that grant human attestation or print a commit prompt.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

On Windows a stdin redirected from `NUL` reports `isatty()` True because `NUL` is a character device. Add one helper that also requires a real console (`kernel32.GetConsoleMode` succeeds) on win32, and use it at the three sites where a false "interactive" verdict grants human attestation or prints a commit prompt: `specs.run_set`, `status_set` (spec `by_human` floor), and `git_commit_helper._is_interactive`. `engine.is_interactive_session` delegates to the same helper.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The helper

- [ ] E-01 Add `term.stdin_is_interactive(stream=None) -> bool` to `agent_workflows/term.py`: `stream` defaults to `sys.stdin`; return False if it is None or lacks `isatty`, or if `isatty()` raises (`ValueError`/`OSError`/`AttributeError`) or returns False. Then, only when `sys.platform == "win32"`, import `ctypes` inside the branch, call `ctypes.windll.kernel32.GetStdHandle(-10)` and `GetConsoleMode(handle, ctypes.byref(ctypes.c_ulong()))`, and return False if it returns 0 or anything raises. Otherwise return True. The platform guard means `ctypes.windll` is never touched on POSIX. `term.py` is a stdlib-only leaf whose sole internal import is `lifecycle_style` (verified at review), so `git_commit_helper` (which documents that it MUST NOT import `cli`) may import it without inverting any dependency.
  - Depends on: none
  - Expected outcome: POSIX behavior equals `bool(sys.stdin.isatty())` with exceptions mapped to False; win32 additionally requires a console.
  - DOCSTRING MUST STATE THREE THINGS, because each is a trap a future reader would otherwise re-discover. (1) WHY the win32 branch exists (`NUL` is a character device, so `isatty()` is True on a redirected stdin). (2) That the win32 probe reads the PROCESS's real `STD_INPUT_HANDLE`, so a caller passing a non-default `stream` gets the `isatty` half only on POSIX and BOTH halves on win32; that asymmetry is deliberate and is why the parameter exists for testing rather than for probing an arbitrary stream. (3) THE HONEST LIMIT, in its own sentence: this answers "is stdin a real console?" and NOT "can a human answer a prompt?". The repository already has three sites that deliberately require MORE (`ipd_lifecycle.run_finalize`'s ttywedge fence, `runner_stop.interrupt_menu_is_safe`, `artifact_adopt.leak_gate_is_interactive`), all requiring the OUTPUT stream to be a TTY too and honoring `AW_NONINTERACTIVE`/`CI`; say so and name `artifact_adopt.leak_gate_is_interactive` as the predicate to use when a caller is about to BLOCK on input. Without this note the new helper reads like the canonical interactivity predicate and invites a future caller to weaken one of those fences to it.
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

- [ ] E-05 In `git_commit_helper._is_interactive`, keep the explicit-override branch and replace the `try: return bool(sys.stdin.isatty()) except ...` fallback with `return _term.stdin_is_interactive()` (function-local `from agent_workflows import term as _term`, keeping this module's leaf discipline visible at the call site; the helper already maps the exceptions). Update the docstring's "falls back to `sys.stdin.isatty()`" to name the helper, and KEEP the existing `cli._confirm` cross-reference accurate: `cli._confirm` still reads bare `sys.stdin.isatty()` (`cli.py:6393`), so the two signals now DIFFER on win32; state that rather than leaving a claim of equivalence that this edit falsifies.
  - Depends on: E-01
  - Expected outcome: no commit prompt is printed (and nothing blocks on `input()`) on a Windows `NUL` stdin.
  - Execution state: pending

- [ ] E-09 Record the LARGER, CROSS-PLATFORM hole this change does NOT close, so it is not lost. `git_commit_helper._is_interactive` keys on stdin ALONE, and the seven in-repo `offer_commit` callers pass `interactive=` at only ONE of them (`runner_shared.py:30054`, `interactive=False`); the other six leave it `None` and so reach this probe. Measured at review ON LINUX, not Windows: with stdin on a real pty and stdout on a PIPE (the exact driver shape `ipd_lifecycle`'s ttywedge note records as a 1h49m wedge), `offer_commit(repo, ["mine.txt"], message="probe")` printed `Commit these path-scoped changes? [Y/n]` INTO THE PIPE and blocked on `input()` until a 20s timeout killed it. This plan's helper does not change that: the fence those three other sites use additionally requires the OUTPUT stream to be a TTY and honors `AW_NONINTERACTIVE`/`CI`. File ONE `aw backlog new` item, `--work-kind bug --priority medium --blocks-release next` (a user-perceptible hang is a live bug, so the repository's gating rule applies), summarizing: `git_commit_helper._is_interactive` trusts stdin alone, so a driver-spawned `aw` verb with stdin inherited and stdout piped prints a commit prompt into the pipe and blocks; adopt `artifact_adopt.leak_gate_is_interactive` (or the equivalent both-streams-plus-`AW_NONINTERACTIVE` fence). Paste the measured reproduction into the item body, and record the new item's id6 in this plan's Findings table as F-8. Do NOT fix it here: that is a cross-platform behavior change at six call sites and is outside this plan's maintainer-approved narrow scope.
  - Depends on: none
  - Expected outcome: one new `open` backlog item exists, carrying `- Work-Kind: bug` and `- Blocks-Release: next`, and its id6 is written into F-8.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-06 Add `tests/test_stdin_interactive.py` with the THREE HELPER-LEVEL tests. Each test installs its OWN fake stdin (a tiny class with `isatty()` returning True, via `mock.patch.object(sys, "stdin", _Fake())`) so the `tests/__init__.py` win32 `_NotATty` wrapper (which forces `isatty()` False in the suite and so MASKS this bug) cannot decide the outcome. Do NOT add `pytestmark = pytest.mark.slow` (see F-9). Tests: (a) with `sys.platform` patched to `"win32"` and a fake `ctypes.windll` (`mock.patch.object(ctypes, "windll", <SimpleNamespace(kernel32=SimpleNamespace(GetStdHandle=lambda n: 1, GetConsoleMode=lambda h, m: 0))>, create=True)`), `term.stdin_is_interactive()` is False; (b) the same with `GetConsoleMode -> 1` is True; (c) POSIX: `sys.platform` patched to `"linux"`, fake stdin `isatty()` True, and `ctypes.windll` NOT patched, `stdin_is_interactive()` is True (`hasattr(ctypes, "windll")` is False on Linux, so this also proves the POSIX path never touches it). All three patch shapes were EXECUTED at review against a scratch copy of the proposed helper body and produced False / True / True respectively, so the mechanism is proven, not assumed.
  - Depends on: E-01
  - Expected outcome: three tests passing on Linux, macOS and Windows.
  - Execution state: pending

- [ ] E-10 Add the TWO SITE-LEVEL outcome tests to the same file, which are what prove the security fix rather than the helper's arithmetic. (d) Under (a)'s conditions, `specs.run_set` on a `reviewed` spec with `--status approved` and no `--by-human` returns 1, stderr contains `human-only transition`, and the spec file is BYTE-IDENTICAL afterwards. Build the namespace the way `tests/test_specs_verbs.py::_args` already does rather than inventing a second shape, and note that `mock.patch("sys.stdin")` as used there yields a `MagicMock` whose `isatty()` is configurable; this test needs `sys.platform` patched too, so patch stdin with an explicit fake rather than a bare `MagicMock`. (e) Under (a)'s conditions, `git_commit_helper.offer_commit(repo, [path], message=..., interactive=None)` with `builtins.input` patched to RAISE returns `git_commit_helper.STATUS_SKIPPED` and never calls `input`; the `input`-raises patch is the load-bearing half, since a test asserting only the status would still pass if the prompt were printed. Reuse `tests/support.init_repo` for the fixture, as `tests/test_git_commit_helper.py` does.
  - Depends on: E-03, E-05
  - Expected outcome: two tests passing; (d) and (e) both FAIL on the base commit (verified in V-10).
  - Execution state: pending

- [ ] E-11 Adjust the TWO EXISTING tests that patch `isatty` to True and expect the interactive branch, rather than leaving them to break on Windows CI. `tests/test_specs_verbs.py::test_approved_requires_human_and_is_refused_non_tty` (its third block, "Interactive TTY approval succeeds directly", `tests/test_specs_verbs.py` ~:191) and `tests/test_status_set.py::test_spec_approved_interactive_confirmation` (~:666) both force `isatty()` True and assert the approval SUCCEEDS. After E-03/E-04 those tests reach the real `GetConsoleMode` on the `windows-latest` job, where a CI runner has no console, so each would begin FAILING there. Patch the PREDICATE instead of the stream in those two places (`mock.patch("agent_workflows.term.stdin_is_interactive", return_value=True)`, added alongside the existing `isatty` patch so POSIX behavior is unchanged), keeping each test's existing assertions intact. Doing this as its own item makes the change visible in review rather than arriving as an unplanned Windows-CI hotfix; F-6 previously deferred it to E-08, which would have discovered it only after the maintainer pushed.
  - Depends on: E-03, E-04
  - Expected outcome: both tests still pass on Linux and no longer depend on a real console on win32.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-07 Add one `- Fixed:` line to `## 2.0.0 (pending)` in `CHANGELOG.md`: on Windows, running `aw` with input redirected from `NUL` was treated as an interactive session, so `aw specs set ... --status approved` could record a human approval that nobody gave (writing an attributed `--by-human` provenance line into the spec's history), and a commit prompt could be printed; a real console is now required. State the CONSEQUENCE, not just the mechanism, because `approved` is the state that licenses execution; F-10 has the measured wording to draw on. No em or en dashes.
  - Depends on: E-03
  - Expected outcome: one line, no dashes.
  - Execution state: pending

- [ ] E-08 Run the bare suite `python3 -m pytest` and `aw sanitize --agent` locally. ALSO run the SLOW set for the one module the engine delegation touches (`python3 -m pytest tests/test_installer.py -o addopts="" -q`), because `tests/test_installer.py:59` is `pytestmark = pytest.mark.slow` and so is EXCLUDED from the bare run by `pyproject.toml`'s `addopts` `-m 'not slow'`: it is the only module exercising `engine.is_interactive_session`, and a bare run therefore proves nothing about E-02. Then report the Windows CI position honestly: the `unittest (windows-latest, ...)` job of `.github/workflows/tests.yml` is the REAL verification of the win32 branch (the local tests fake `ctypes.windll`, which proves the logic but not the actual Win32 call), it requires a push, and the executor never pushes. FINALIZATION IS NOT BLOCKED ON IT: state in the report that Windows CI is outstanding and record it on V-08, rather than holding a completed plan in `pending/` for an act the executor is forbidden to perform (see OQ-02).
  - Depends on: E-06, E-10, E-11, E-07
  - Expected outcome: 0 failed in the bare suite; `tests/test_installer.py` passes with the slow marker cleared; `aw sanitize --agent` exit 0; the Windows CI position stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `engine.is_interactive_session` (~:1940-1958) already contains the correct win32 probe (`GetStdHandle(-10)`, `GetConsoleMode`), but takes an `InstallPlan` and also short-circuits on `plan.yes` and `CI`, so it cannot be called from the setters as is.
- `tests/__init__.py` (~:70-92) reopens stdin on `os.devnull` and, on win32, wraps it in a `_NotATty` `TextIOWrapper` subclass. That wrapper is why the suite passes on Windows today while the product code is wrong: tests never see the real `NUL` `isatty()` True.
- Existing tests patch `sys.stdin.isatty` (`tests/test_specs_verbs.py::test_approved_requires_human_and_is_refused_non_tty` ~:191, `tests/test_status_set.py::test_spec_approved_interactive_confirmation` ~:666). On POSIX the helper reads the same `isatty`, so they still pass; on win32 CI they would reach the real `GetConsoleMode` and fail. E-11 adjusts them IN THIS PLAN rather than leaving it to a post-push discovery.
- Tests: outcome only (maintainer standing rule). No test greps for call sites or pins the helper's source.
- `term.py` is stdlib-only apart from `from . import lifecycle_style`, which is itself stdlib-only (verified at review). That is what makes it a legal import target for `git_commit_helper`, whose module docstring forbids importing `cli`.
- A BARE `python3 -m pytest` DOES NOT RUN `tests/test_installer.py` (`pytestmark = pytest.mark.slow` at `tests/test_installer.py:59`; `pyproject.toml` `addopts` carries `-m 'not slow'`). Any validation of E-02 must clear the marker explicitly. See F-9.
- Commit via `aw commit k4vi7z -- <paths>`; never push. Line numbers at HEAD `92679444`, approximate; re-verified at review against HEAD `48e8c097`, where every cited construct still resolves.

## Findings

| # | Location (HEAD 92679444) | Finding |
| --- | --- | --- |
| F-1 | `specs.run_set` authority floor (~:637-645) | Confirmed: `is_interactive = (hasattr(sys.stdin, "isatty") and sys.stdin.isatty() and not agent/as_agent/json)` then `setattr(args, "by_human", True)`. |
| F-2 | `status_set` spec floor (~:648-655) | Confirmed, same expression. |
| F-3 | `git_commit_helper._is_interactive` (~:302-315) | Confirmed: `bool(sys.stdin.isatty())` fallback. |
| F-4 | `engine.is_interactive_session` (~:1940-1958) | Confirmed; the probe to reuse. |
| F-5 | `tests/__init__.py` (~:78-89) | Confirmed: the `_NotATty` wrapper masks the bug in the suite. E-06 installs its own fake stdin per test so the wrapper is irrelevant to the outcome. |
| F-6 | `tests/test_specs_verbs.py::test_approved_requires_human_and_is_refused_non_tty`, its block commented `# Interactive TTY approval succeeds directly` (~:191); `tests/test_status_set.py::test_spec_approved_interactive_confirmation` (~:666) | Both force `isatty()` True and assert the approval SUCCEEDS, so after E-03/E-04 they reach the real `GetConsoleMode` on `windows-latest` and would begin failing there. REVISED AT REVIEW: this is now owned by E-11 and both test files are DECLARED in `- Scope-Paths:`, so it is a planned edit reconciled at finalize rather than a contingency discovered after the maintainer pushes. |
| F-7 | `grep -c "stdin.isatty" agent_workflows/cli.py` = 22 at HEAD `48e8c097` (21 at the authoring HEAD `92679444`) | Confirmed ~20 prompt-only sites in `cli.py` are out of scope (maintainer-approved narrow scope). The count DRIFTED by one between authoring and review, which is why it is recorded as context and no `Expected outcome` asserts on it. |
| F-8 | `git_commit_helper._is_interactive` (`agent_workflows/git_commit_helper.py:302-315`); `offer_commit` callers at `cli.py:6448`, `plans_archive.py:295`, `research_archive.py:554`, `specs.py:888`, `status_set.py:1565`, `work_cmd.py:684` (all `interactive=None`) and `runner_shared.py:30054` (`interactive=False`) | FOUND AT REVIEW, CROSS-PLATFORM AND NOT CLOSED BY THIS PLAN. Measured ON LINUX with stdin on a real pty and stdout on a PIPE: `offer_commit(repo, ["mine.txt"], message="probe")` printed `Commit these path-scoped changes? [Y/n] ` into the pipe and BLOCKED on `input()` until a 20s timeout. That is the same predicate error `ipd_lifecycle.run_finalize`'s ttywedge note records as a measured 1h49m wedge, and three sites already use the stronger fence (`artifact_adopt.leak_gate_is_interactive`, `runner_stop.interrupt_menu_is_safe`, `ipd_lifecycle.run_finalize`). E-09 files a backlog carrier; record its id6 here: `<id6 pending E-09>`. |
| F-9 | `tests/test_installer.py:59` `pytestmark = pytest.mark.slow`; `pyproject.toml` `addopts` `-m 'not slow'` | FOUND AT REVIEW: V-02 as originally written (`pytest tests/test_installer.py -o addopts="" -q -k interactive`) is VACUOUS TWICE OVER. Measured: `-k interactive` deselects all 120 tests and exits 0 having run NOTHING, and even without `-k` the module is slow-marked and so never runs in the bare suite E-08 uses as its gate. `tests/test_installer.py` is the ONLY module exercising `engine.is_interactive_session` (it patches it at `tests/test_installer.py:1432`), so this was the only coverage E-02 had. V-02 and E-08 are corrected. |
| F-10 | `attention_contract.TRANSITION_AUTHORITY["->approved"]` = `{"who": "human", "by_human": True, "human_token": True, ...}`; spec `20260815-0151-01-honest-human-approval-attestation` (`Status: implemented`) G1 | THE SEVERITY OF THE `specs`/`status_set` HALF, verified at review by driving the real command. With stdin on a pty and stdout PIPED (the driver shape, no human present), `python3 -m agent_workflows specs set --status approved <reviewed spec> --message "driver-spawned, no human involved"` exited 0 and wrote `- 2026-09-26 approved (aw specs, --by-human): driver-spawned, no human involved`. So the auto-attestation fabricates a `--by-human` provenance line the spec's own G2 shape ("SUCCEEDS iff the explicit flag is passed") does not contemplate, and `approved` is the state that LICENSES EXECUTION. On POSIX a pipe is not a tty so this needs an inherited terminal; on win32 a bare `< NUL` suffices, which is this plan's subject. Recorded to show the fix is worth its narrow scope, and carried into the CHANGELOG wording (E-07). |

## Proposed changes (ordered, validatable)

1. E-01 helper; E-02 engine delegates.
2. E-03 to E-05 replace the three security-relevant checks; E-09 records the cross-platform hole that stays open.
3. E-06/E-10/E-11 tests; E-07 CHANGELOG; E-08 verify locally and state the Windows CI position.

## Deferred / out of scope (with reason)

- The ~20 prompt-only `sys.stdin.isatty()` sites in `cli.py` (and similar prompt-only sites in `oc_runipd`, `agy_runipd`, `install_wizard`).
  - Carrier-Declined: maintainer-approved narrow scope for this plan; those sites only choose whether to show a prompt, and a prompt on a Windows `NUL` stdin reads EOF and falls back to the non-interactive answer, so they grant no authority. Spot-checked at review: `cli._confirm` (`cli.py:6393-6403`) guards `input()` with `except EOFError: return False`, `cli.main` carries a top-level `except EOFError` returning 130 (`cli.py:14860-14862`), and of the twelve `input()` call sites in `cli.py` nine carry a local EOF guard; the three that do not (`cli.py:7397` is a docstring, `cli.py:7679` is guarded by `except (EOFError, KeyboardInterrupt)` four lines later, `cli.py:8868` carries an inline comment deferring to `main()`) are covered by the top-level handler. So an EOF at a prompt-only site produces a declined answer or exit 130, not a hang. Revisit only if a prompt-only site is shown to block or to write into machine output.
- The cross-platform `git_commit_helper` prompt hazard measured at review (F-8): `_is_interactive` keys on stdin ALONE, so a driver-spawned verb with stdin inherited and stdout piped prints a prompt into the pipe and blocks.
  - Carrier-Declined: NOT declined as unowned; the carrier is MINTED BY THIS PLAN and cannot be named here. `- Carrier:` requires a bare 6-char id6 resolving to an existing open backlog item, and `aw check`'s `check.ipd-uncarried-obligation` rejects prose in that field (verified at review by driving `check_engine.evaluate_durable_carrier`, which reported `expected a bare 6-char id6`). E-09 files the item with `aw backlog new --work-kind bug --priority medium --blocks-release next --apply`, so the id6 does not exist until execution; V-09 requires the item's path and front matter as evidence, and E-09 requires the minted id6 to be written into the F-8 row. Deferred rather than fixed here because the fix changes behavior at six call sites on all platforms, which is outside this plan's maintainer-approved scope and would make a Windows-only bugfix a cross-platform interactivity change. If a future reader finds F-8 still reading `<id6 pending E-09>` on an executed plan, E-09 was not performed and that IS the defect to chase.

## Scope check

- Over-scope: none. E-09 writes a backlog item rather than code, which is the repository's own carrier mechanism for an obligation a plan must not silently drop, not a scope expansion.
- Under-scope (CLOSED at review): the two existing interactive tests are now owned by E-11 and both files are declared in `- Scope-Paths:`.
- Declared-but-possibly-unmodified: `tests/test_specs_verbs.py` and `tests/test_status_set.py` are declared for E-11. If E-11 turns out to need only one of them, `--scope-ack` the other at finalize.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_stdin_interactive.py` asserts observable outcomes (the helper's verdict, a refused approval with the file unchanged, no prompt issued) under a patched platform and a faked Win32 API. Five tests, split E-06 (three helper-level) / E-10 (two site-level), plus E-11's adjustment of two existing tests.

RUN THE SUITE BARE (`python3 -m pytest`), and separately run `python3 -m pytest tests/test_installer.py -o addopts="" -q`: the bare run EXCLUDES that module (`pytestmark = pytest.mark.slow`, `tests/test_installer.py:59`) and it is the only coverage of `engine.is_interactive_session`, so E-02 is otherwise untested. Do NOT add a slow marker to the new test file.

The Windows CI job (`windows-latest` in the `tests.yml` matrix) is the real verification of the win32 branch, since the local tests fake `ctypes.windll`. It needs a push, which the executor is forbidden to perform, so it is reported as outstanding and does not block finalization (OQ-02).

## Spec / documentation sync

No `.spec.md` is amended, and the reasoning was re-checked at review. The governing spec is `20260815-0151-01-honest-human-approval-attestation` (`Status: implemented`), whose G1 requires that `--by-human` be "honored regardless of TTY" and that the `isatty()` REQUIREMENT be removed from the human-only path; its G2 shape is "the action SUCCEEDS iff the explicit flag is passed and is REFUSED with a clear message otherwise". This plan touches neither: `--by-human` keeps working with no TTY, and the refusal message is unchanged. What it narrows is the SEPARATE auto-attestation branch added later by commit `cf7dceea` (2026-09-04, "auto-attest human approval on interactive TTY without prompt"), which the spec does not describe at all; making that branch require a real console on Windows brings it in line with what it already means on POSIX. `CHANGELOG.md` gains one line (E-07).

## Open questions

### OQ-01: Narrow fix (three sites) or replace every stdin.isatty() in the package?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Narrow fix, maintainer-approved in the authoring brief. Only the three sites grant authority or can print into machine output; the rest are prompt-only, and their EOF behavior was spot-checked at review (see Deferred). The genuinely serious remaining gap is F-8, which is cross-platform rather than a `stdin.isatty()` spelling issue, and E-09 carries it.

### OQ-02: Does an unrun Windows CI job hold this plan in `pending/`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. Resolved at review from the repository's own execution contract, which states plainly that the executor "never pushes" and, in the managed-lane case, that the runner owns the terminal transition. As originally written, V-08 required either the Windows CI job result OR a statement that the branch is unpushed, and in the second case said "this V-item stays `pending` and the plan is not finalized". That makes finalization conditional on an act the executor is FORBIDDEN to perform, so a fully completed plan would sit in `pending/` indefinitely waiting for the maintainer, which is the stranding shape the corrected element-5 contract exists to prevent. V-08 is rewritten to require the local evidence and an explicit, honest statement of the Windows CI position, recorded as a KNOWN HOLE rather than as a blocker. The hole is real and is stated as such: the win32 branch's ACTUAL `GetConsoleMode` call is proven only by that job.

- Carrier-Declined: nothing is left outstanding by this resolution. The Windows CI verification is not lost, it is RECORDED on V-08 and in the plan's report; the maintainer's ordinary push runs the job, and a failure there is a normal CI failure with a normal fix, not an obligation this plan must pre-register.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import sys; from agent_workflows import term; print(term.stdin_is_interactive())" < /dev/null` printing `False`, and `script -q -c 'python3 -c "from agent_workflows import term; print(term.stdin_is_interactive())"' /dev/null` printing `True` (the `script` form was EXECUTED at review and does produce a real tty here; if the sandbox refuses it, substitute an in-process `pty.openpty()` fixture and say which was used). Also paste the helper's docstring, which must visibly carry the three required statements from E-01 including the honest limit naming `artifact_adopt.leak_gate_is_interactive`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/engine.py` showing `is_interactive_session` delegating while KEEPING its `plan.yes` and `CI` short-circuits, and paste `python3 -m pytest tests/test_installer.py -o addopts="" -q` showing its full pass line. DO NOT use `-k interactive`: measured at review, it deselects all 120 tests and exits 0 having run NOTHING, and the module is additionally `slow`-marked so it is absent from the bare suite (F-9). The test that actually covers this function is `tests/test_installer.py::OverwritePromptTests::test_every_prompt_answer_has_the_right_effect_and_exit_code`; name it in the pasted output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the output of test (d) from E-10 (node id and PASSED) and `git diff agent_workflows/specs.py` limited to the authority floor, showing the `--agent`/`--as-agent`/`--json` exclusions retained.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a scratch-repo run of `python3 -m agent_workflows specs set approved <id6> --yes < /dev/null; echo rc=$?` on a `reviewed` spec showing a non-zero exit and a refusal naming `--by-human`, plus proof the file is unchanged. This is the POSIX REGRESSION GUARD and it must be non-vacuous: the same command was EXECUTED at review against unmodified code and ALREADY exits 1 with `aw specs set: reviewed -> approved is a human-only transition; pass --by-human ...`, so a passing run proves only that POSIX behavior did not change. State that explicitly beside the paste rather than presenting it as evidence of the fix. Also paste `git diff agent_workflows/status_set.py` limited to the floor.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the output of test (e) from E-10 (PASSED) and `python3 -m pytest tests/test_git_commit_helper.py -o addopts="" -q` all passing. `tests/test_git_commit_helper.py::test_non_interactive_commit_modes` installs its own `_FakeStdin` returning `isatty() -> False` and asserts `STATUS_SKIPPED`, so it must keep passing unchanged; say so.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the new backlog item's path and its front matter showing `- Status: open`, `- Work-Kind: bug` and `- Blocks-Release: next`, paste `aw check release-gates --agent` (or `aw check` scoped to backlog) showing the item raises no new finding, and paste the F-8 row of this plan showing the id6 written in place of `<id6 pending E-09>`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_stdin_interactive.py -o addopts="" -v` showing all five tests (E-06's three plus E-10's two) PASSED with their node ids, and confirm the file carries NO `pytest.mark.slow`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: THE BASE-COMMIT RED RUN, which is what makes the two site-level tests non-vacuous. In a throwaway detached worktree (`git worktree add --detach <gitignored path> <base-sha>`; `.gitignore:73` ignores `.aw/worktrees/` and `.gitignore:42` ignores `tmp/`, so either is safe), copy in ONLY `tests/test_stdin_interactive.py` and run it. Paste the result showing tests (d) and (e) FAIL or ERROR there. An ERROR from the absent `term.stdin_is_interactive` is acceptable for (a)/(b)/(c) but NOT for (d)/(e): those two must fail on the OUTCOME (an approval granted, or a prompt issued), so if they merely error on the missing import, restructure them to call the product path and re-run. Then paste the worktree teardown (`git worktree remove`). Do NOT revert the fix in place, and do NOT use `git stash`: this is a shared checkout and a stash would move a co-worker's uncommitted changes.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest tests/test_specs_verbs.py tests/test_status_set.py -o addopts="" -q` all passing, and `git diff` for both files showing the predicate patch ADDED alongside the existing `isatty` patch with every original assertion intact (no assertion deleted or weakened).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md` showing one added `- Fixed:` line under `## 2.0.0 (pending)` and `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing. NOTE the exit code: `grep` exits 1 on no match, so `echo rc=$?` will show `rc=1` and that is the PASSING case; the pattern and this behavior were both verified at review.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed; paste `python3 -m pytest tests/test_installer.py -o addopts="" -q` passing (the slow-marked module the bare run skips); paste `aw sanitize --agent` with its exit code. Then state the Windows CI position EXPLICITLY in one of two forms, and do not invent a third: either the job result (`gh run view <id> --json jobs` excerpt showing `unittest (windows-latest, ...)` `conclusion: success`), or a plain statement that the branch is unpushed so the job has not run, naming the win32 `GetConsoleMode` call as the KNOWN HOLE this leaves. The second form is a legitimate pass for this V-item (OQ-02): it does NOT block finalization, and it must not be dressed up as a green result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one helper and its three authority-granting callers; the engine delegation removes the only existing copy of the probe. Assessed against the right-sizing diagnostics at review: each E-item names one deliverable in one region, and E-06 was split into E-06 (helper-level), E-10 (site-level, the tests that prove the fix) and E-11 (the two existing tests that would otherwise break on Windows CI) because the original single item bundled three independent test-surfaces requiring three separate V-items.

This plan is `reviewed` and needs explicit human approval before execution. `reviewed` records that the review happened; it is not approval, and `- Readiness: go-pending-approval` means exactly that.

WHAT A HUMAN IS APPROVING: a Windows-only behavior change at three gates (a redirected `NUL` stdin is no longer treated as a human), one new helper in `term.py`, five new outcome tests, a predicate-patch adjustment to two existing tests so they keep passing on the `windows-latest` CI job, one new backlog item recording a cross-platform prompt hang this plan deliberately does NOT fix (F-8), and one CHANGELOG line. The Windows CI job is the only real proof of the win32 `GetConsoleMode` call and needs a push the executor may not perform; it is reported as a known hole and does NOT block finalization (OQ-02).

WHAT THIS DOES NOT FIX, stated plainly because a reader could reasonably assume otherwise. It does not make `git_commit_helper` safe to prompt from: that predicate keys on stdin ALONE, and with stdin inherited and stdout piped it still prints a prompt into the pipe and blocks on `input()` (measured on LINUX at review, F-8). E-09 files that as a release-gating bug. It also does not touch the ~20 prompt-only `cli.py` sites, whose EOF handling was spot-checked instead (Deferred).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`; within `engine.py` only `is_interactive_session`, within `specs.py` only the `run_set` authority floor, within `status_set.py` only the spec `by_human` floor, within `git_commit_helper.py` only `_is_interactive`, within `tests/test_specs_verbs.py` and `tests/test_status_set.py` only the two cases named in E-11. E-09 also writes ONE new file under `.aw/records/backlog/open/`, which `aw backlog new --apply` names; that path cannot be predeclared here because the id6 is minted at execution, so `--scope-reason` it at finalize. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). Genuine stop condition: a co-worker's concurrent edit to one of these functions that cannot be safely combined.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run, and never claim Windows CI passed without the job result. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`.

Commit ONLY the paths in `- Scope-Paths:` (plus E-09's minted backlog file) through `aw commit k4vi7z -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, the terminal transition is performed with `aw ipd finalize k4vi7z --actor <agent/model> --message <summary> --apply`. OWNERSHIP IS CONDITIONAL: in a managed lane the RUNNER owns that transition and the executor must not run it; in an unmanaged or hand-driven run the executor runs it. Never hand-roll the move with `git mv` plus a `Status:` edit.

This plan inherits `- Blocks-Release: next` from `ddo56m`; after execution set `ddo56m` `done` with `--evidence` citing the executed plan. Note that E-09's new item carries its OWN `- Blocks-Release: next`, so closing `ddo56m` does not release the gate on the F-8 work: that is deliberate, since F-8 is a separate live bug and not part of `ddo56m`'s subject.
