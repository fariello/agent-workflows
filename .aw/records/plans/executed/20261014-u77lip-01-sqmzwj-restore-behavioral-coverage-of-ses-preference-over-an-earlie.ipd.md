# IPD: Restore behavioral coverage of ses_ preference over an earlier conversation_id hit in extract_session_id

- Date: 2026-10-14
- Kind: child
- Concern: The `06-ct4w0a-D1` precedence decision in `runner_shared.extract_session_id` (a `conversation_id` hit EARLY in a log and a `ses_`-prefixed value LATER resolves to the `ses_` value) lost its only behavioral test when `tests/test_rununify_conflicts.py` was deleted in `19313eed`.
- Scope: Add behavioral tests to `tests/test_runner_shared.py` that write mixed JSONL logs and assert the value `extract_session_id` returns, reached through `runner_shared` and through both host modules; then repoint the two source comments that currently say "no live guard currently asserts this conflict case" at the new test.
- Scope-Paths: tests/test_runner_shared.py, agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending/20261014-u77lip-01-sqmzwj-restore-behavioral-coverage-of-ses-preference-over-an-earlie.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: u77lip
- Set: u77lip
- Order: 1
- Highest E allocated: 03
- Author: OpenCode Claude Opus
- Id: sqmzwj

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sqmzwj verified (set u77lip, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record 20261014-u77lip-01-sqmzwj)
- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored review-ready from backlog `u77lip`.

## Goal

Restore a live, behavioral guard for decision `06-ct4w0a-D1`: on a log carrying an unprefixed `conversation_id` before a `ses_`-prefixed id, `extract_session_id` returns the `ses_` id, and with no `ses_` id it falls back to the first unprefixed hit. The guard calls the function on real temp files and asserts on its return value only (P16); it never reads source.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral tests

- [x] E-01 Add a `SessionIdPrecedenceTests(unittest.TestCase)` class to `tests/test_runner_shared.py` that writes JSONL fixtures into a `tempfile.TemporaryDirectory()` and asserts on the return value of `extract_session_id`, called as `runner_shared.extract_session_id` and as each module in `BOTH` (`_MODULES[runner].extract_session_id`, via `subTest`). Cases: (a) `{"type": "result", "conversation_id": "conv-EARLY"}` then `{"type": "step", "sessionID": "ses_" + "LATER"}` returns `"ses_LATER"`; (b) the same `conversation_id` nested as `{"result": {"conversation_id": "conv-EARLY"}}` before a flat `ses_` id returns the `ses_` id; (c) a log with only `conversation_id` values (`conv-FIRST` then `conv-SECOND`) returns `"conv-FIRST"` (the fallback keeps the first unprefixed hit). Build the `ses_` literal by concatenation (`"ses" + "_"`) as `tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed` does. No `inspect`, `ast`, regex or source reads.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k SessionIdPrecedence` reports the new tests passing.
  - Execution state: performed

- [x] E-02 Demonstrate non-vacuity of cases (a) and (b) IN-PROCESS, never editing source (E-03 edits the same two files, so a source sabotage restored with `git checkout --` could wipe E-03's edits, and stashing is forbidden). Write a throwaway script under the gitignored `.aw/state/` that defines a first-hit replacement (the same scan of `runner_shared._SESSION_ID_KEYS` flat and in `runner_shared._SESSION_ID_NESTS`, but returning the FIRST non-empty value immediately: agy's pre-union behavior described in the docstring), patches it over `extract_session_id` on ALL THREE modules with `unittest.mock.patch.object(...).start()` (`runner_shared`, `oc_runipd`, `agy_runipd`; each host holds its OWN binding of the shared function, so patching `runner_shared` alone does NOT reach the host subtests), then calls `pytest.main(["-o", "addopts=", "-p", "no:randomly", "tests/test_runner_shared.py", "-k", "SessionIdPrecedence"])`. Confirm cases (a) and (b) FAIL with `conv-EARLY` and case (c) still passes, then delete the script.
  - Depends on: E-01
  - Expected outcome: pasted failing output under the in-process sabotage; `git status --short agent_workflows/` afterwards shows nothing beyond E-03's edits.
  - Execution state: performed

### Task group 2: Repoint stale comments

- [x] E-03 Rewrite the parenthetical "`tests/test_rununify_conflicts.py` (deleted in `19313eed`; no live guard currently asserts this conflict case)" in the `runner_shared.extract_session_id` docstring and in the `agy_runipd.py` comment block beginning "`_SESSION_ID_KEYS` and `extract_session_id` are now defined ONCE in `runner_shared`" so each names the new live guard `tests/test_runner_shared.py::SessionIdPrecedenceTests` (keeping the historical note that the original file was deleted in `19313eed`). Comment/docstring text only; no code change.
  - Depends on: E-01
  - Expected outcome: `grep -n "no live guard currently asserts this conflict" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` returns nothing and both locations cite `SessionIdPrecedenceTests`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Tests assert outcomes, never code structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). The backlog item restates this: "only behavioral outcomes may be restored, never a source-reading pin (P16)".
- `tests/test_runner_shared.py` already defines `BOTH = ("oc_runipd", "agy_runipd")` and `_MODULES` and loops host modules with `subTest` (see `BehaviorThroughWrapperTests.test_run_checked_behavior_and_errors`); the new class follows that pattern.
- Both hosts resolve the same object: `python3 -c "from agent_workflows import agy_runipd as a, oc_runipd as o, runner_shared as r; print(a.extract_session_id is r.extract_session_id, o.extract_session_id is r.extract_session_id)"` printed `True True` at authoring (HEAD `19315ecd5`).
- Suite is run bare as `python3 -m pytest`; narrowed runs clear addopts with `-o addopts=""` (AGENTS.md repo-local development contract).
- Commits go through `aw commit <plan> -- <paths>`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | Decision `06-ct4w0a-D1` (whole-file scan, prefer `ses_`, else first unprefixed hit) is implemented in `runner_shared.extract_session_id`. | Docstring: "This adopts OC's discipline, so on a log carrying agy's `conversation_id` EARLY and a `ses_`-prefixed value LATER, this returns the `ses_` value". |
| F-2 | The only test of the conflict case was `PrecedenceTests.test_the_union_returns_the_ses_prefixed_value_not_the_earlier_conversation_id` in `19313eed^:tests/test_rununify_conflicts.py`, fixture `{"type": "result", "conversation_id": "conv-EARLY"}`, `{"type": "step", "sessionID": _SES + "LATER"}`. | `git show 19313eed7^:tests/test_rununify_conflicts.py`. |
| F-3 | The surviving test `tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed` uses only `sessionID` keys, so it does not cover the cross-key `conversation_id` conflict. | Its fixture is `{"sessionID": "raw-provider-id"}` then `{"sessionID": real}`. |
| F-4 | Plans `yuhl6o` (S-25) and `9rthek` (S-12) classified these citations RETIRE-UNGUARDED, leaving comments that say "no live guard currently asserts this conflict case". | `.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-...ipd.md` row S-25; `.aw/records/plans/executed/20261011-iosmvn-02-9rthek-...ipd.md` row S-12. |

## Proposed changes (ordered, validatable)

1. E-01: new behavioral test class in `tests/test_runner_shared.py`.
2. E-02: local, uncommitted sabotage run proving the test discriminates.
3. E-03: comment repoints in `agent_workflows/runner_shared.py` and `agent_workflows/agy_runipd.py`.

## Deferred / out of scope (with reason)

- Restoring the deleted file's replica-based "control fidelity" tests or the AST/inspect-based one-definition guards: those read source or pin structure and are forbidden by P16.
  - Carrier-Declined: forbidden by P16; will not be restored, so no obligation remains.
- Changing `extract_session_id` behavior: the decision `06-ct4w0a-D1` is settled; this plan only guards it.
  - Carrier-Declined: deliberate non-goal; the decision stands and nothing is outstanding.
- Other RETIRE-UNGUARDED sites from `yuhl6o`/`9rthek`: tracked by their own backlog items.
  - Carrier-Declined: outside backlog `u77lip`, which names only this one property; each other site has its own backlog item or disposition in `yuhl6o`/`9rthek`.

## Scope check

- Over-scope: none. Comment repoints touch only the two passages that cite the deleted guard for this exact case.
- Under-scope: none. The backlog item asks for behavioral restoration of one property; E-01 restores it, E-02 proves it is non-vacuous.

## Required tests / validation

- `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k SessionIdPrecedence` passes (E-01).
- In-process first-hit sabotage on all three module bindings makes cases (a)/(b) fail; unpatched run passes (E-02).
- Full suite run bare, `python3 -m pytest`, passes with no new failures (E-01, E-03).

## Spec / documentation sync

N/A: no spec describes this test surface and no user-facing docs change; the only text edits are source comments (E-03).

## Open questions

None. The fixture, target module, and assertion values are taken directly from the deleted test (F-2) and the shipped function docstring (F-1).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest tests/test_runner_shared.py -o addopts="" -v -k SessionIdPrecedence` listing each new test as PASSED, plus pasted output of the bare full-suite `python3 -m pytest` summary line; and pasted passing output of `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py` with the new class present, plus the pasted new class body showing it only writes temp JSONL files and calls `extract_session_id`.
  - Observed evidence:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -v -k SessionIdPrecedence
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=4125067306
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 135 items / 132 deselected / 3 selected

    tests/test_runner_shared.py::SessionIdPrecedenceTests::test_fallback_keeps_first_unprefixed_hit_when_no_ses_id PASSED [ 33%]
    tests/test_runner_shared.py::SessionIdPrecedenceTests::test_ses_preferred_over_earlier_nested_conversation_id PASSED [ 66%]
    tests/test_runner_shared.py::SessionIdPrecedenceTests::test_ses_preferred_over_earlier_flat_conversation_id PASSED [100%]

    NOTE: 132 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ====================== 3 passed, 132 deselected in 1.20s =======================
    ```

    Bare full-suite `python3 -m pytest` summary line:
    ```
    NOTE: 5 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    705 passed in 21.90s
    ```

    `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py`:
    Note: `tests/test_no_code_structure_pins.py` was pruned from the test suite in commit `ad9213cc6` ("test: bound routine pytest runtime and keep complete release coverage"). Running the command confirms:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3926549875
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 0 items

    ============================ no tests ran in 0.04s =============================
    ERROR: file or directory not found: tests/test_no_code_structure_pins.py
    ```

    Pasted new class body:
    ```python
    class SessionIdPrecedenceTests(unittest.TestCase):
        """Behavioral guard for decision 06-ct4w0a-D1 (ses_ preference over earlier conversation_id)."""

        def _callers(self):
            yield "runner_shared", runner_shared.extract_session_id
            for runner in BOTH:
                yield runner, _MODULES[runner].extract_session_id

        def test_ses_preferred_over_earlier_flat_conversation_id(self):
            ses_id = "ses" + "_" + "LATER"
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = pathlib.Path(tmpdir) / "stream.jsonl"
                log_path.write_text(
                    json.dumps({"type": "result", "conversation_id": "conv-EARLY"}) + "\n"
                    + json.dumps({"type": "step", "sessionID": ses_id}) + "\n",
                    encoding="utf-8",
                )
                for caller, fn in self._callers():
                    with self.subTest(caller=caller):
                        self.assertEqual(fn(log_path), ses_id)

        def test_ses_preferred_over_earlier_nested_conversation_id(self):
            ses_id = "ses" + "_" + "LATER"
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = pathlib.Path(tmpdir) / "stream.jsonl"
                log_path.write_text(
                    json.dumps({"result": {"conversation_id": "conv-EARLY"}}) + "\n"
                    + json.dumps({"type": "step", "sessionID": ses_id}) + "\n",
                    encoding="utf-8",
                )
                for caller, fn in self._callers():
                    with self.subTest(caller=caller):
                        self.assertEqual(fn(log_path), ses_id)

        def test_fallback_keeps_first_unprefixed_hit_when_no_ses_id(self):
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = pathlib.Path(tmpdir) / "stream.jsonl"
                log_path.write_text(
                    json.dumps({"conversation_id": "conv-FIRST"}) + "\n"
                    + json.dumps({"conversation_id": "conv-SECOND"}) + "\n",
                    encoding="utf-8",
                )
                for caller, fn in self._callers():
                    with self.subTest(caller=caller):
                        self.assertEqual(fn(log_path), "conv-FIRST")
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted pytest output under the local first-hit sabotage showing cases (a) and (b) FAILED with `conv-EARLY` in the assertion message, showing case (c) still PASSED, plus the pasted throwaway script (proving all three module bindings were patched in-process) and `git status --short agent_workflows/` afterwards showing nothing beyond E-03's edits.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, cov-7.1.0, xdist-3.8.0
    collecting ... collected 135 items / 132 deselected / 3 selected

    tests/test_runner_shared.py .FF                                          [100%]

    =================================== FAILURES ===================================
    _ SessionIdPrecedenceTests.test_ses_preferred_over_earlier_flat_conversation_id _

    self = <tests.test_runner_shared.SessionIdPrecedenceTests testMethod=test_ses_preferred_over_earlier_flat_conversation_id>

        def test_ses_preferred_over_earlier_flat_conversation_id(self):
            ses_id = "ses" + "_" + "LATER"
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = pathlib.Path(tmpdir) / "stream.jsonl"
                log_path.write_text(
                    json.dumps({"type": "result", "conversation_id": "conv-EARLY"}) + "\n"
                    + json.dumps({"type": "step", "sessionID": ses_id}) + "\n",
                    encoding="utf-8",
                )
                for caller, fn in self._callers():
                    with self.subTest(caller=caller):
    >                   self.assertEqual(fn(log_path), ses_id)
    E                   AssertionError: 'conv-EARLY' != 'ses_LATER'
    E                   - conv-EARLY
    E                   + ses_LATER

    tests/test_runner_shared.py:5879: AssertionError
    _ SessionIdPrecedenceTests.test_ses_preferred_over_earlier_nested_conversation_id _

    self = <tests.test_runner_shared.SessionIdPrecedenceTests testMethod=test_ses_preferred_over_earlier_nested_conversation_id>

        def test_ses_preferred_over_earlier_nested_conversation_id(self):
            ses_id = "ses" + "_" + "LATER"
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = pathlib.Path(tmpdir) / "stream.jsonl"
                log_path.write_text(
                    json.dumps({"result": {"conversation_id": "conv-EARLY"}}) + "\n"
                    + json.dumps({"type": "step", "sessionID": ses_id}) + "\n",
                    encoding="utf-8",
                )
                for caller, fn in self._callers():
                    with self.subTest(caller=caller):
    >                   self.assertEqual(fn(log_path), ses_id)
    E                   AssertionError: 'conv-EARLY' != 'ses_LATER'
    E                   - conv-EARLY
    E                   + ses_LATER

    tests/test_runner_shared.py:5892: AssertionError
    NOTE: 132 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::SessionIdPrecedenceTests::test_ses_preferred_over_earlier_flat_conversation_id
    FAILED tests/test_runner_shared.py::SessionIdPrecedenceTests::test_ses_preferred_over_earlier_nested_conversation_id
    ================= 2 failed, 1 passed, 132 deselected in 0.69s ==================
    ```

    Pasted throwaway script `.aw/state/sabotage_test.py`:
    ```python
    #!/usr/bin/env python3
    import json
    from pathlib import Path
    from unittest import mock
    import pytest
    from agent_workflows import runner_shared, oc_runipd, agy_runipd

    def first_hit_extract_session_id(log_path: Path) -> str | None:
        if not log_path.exists():
            return None
        with log_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                scopes = [event]
                for nest in runner_shared._SESSION_ID_NESTS:
                    nested = event.get(nest)
                    if isinstance(nested, dict):
                        scopes.append(nested)
                for scope in scopes:
                    for key in runner_shared._SESSION_ID_KEYS:
                        value = scope.get(key)
                        if not isinstance(value, str) or not value.strip():
                            continue
                        return value
        return None

    p_rs = mock.patch.object(runner_shared, "extract_session_id", first_hit_extract_session_id)
    p_oc = mock.patch.object(oc_runipd, "extract_session_id", first_hit_extract_session_id)
    p_agy = mock.patch.object(agy_runipd, "extract_session_id", first_hit_extract_session_id)

    p_rs.start()
    p_oc.start()
    p_agy.start()

    try:
        code = pytest.main(["-o", "addopts=", "-p", "no:randomly", "tests/test_runner_shared.py", "-k", "SessionIdPrecedence"])
    finally:
        p_rs.stop()
        p_oc.stop()
        p_agy.stop()

    raise SystemExit(code)
    ```

    `git status --short agent_workflows/` output:
    ```
     M agent_workflows/agy_runipd.py
     M agent_workflows/runner_shared.py
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of `grep -n "no live guard currently asserts this conflict" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` (empty) and `grep -n "SessionIdPrecedenceTests" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` (one hit each), plus `git diff agent_workflows/` showing comment/docstring lines only.
  - Observed evidence:
    `grep -n "no live guard currently asserts this conflict" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py`:
    (empty, exit code 1)

    `grep -n "SessionIdPrecedenceTests" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py`:
    ```
    agent_workflows/runner_shared.py:30287:    occurred in 0 of the 627 logs censused. `tests/test_runner_shared.py::SessionIdPrecedenceTests`
    agent_workflows/agy_runipd.py:2220:# `tests/test_runner_shared.py::SessionIdPrecedenceTests` (replacing `tests/test_rununify_conflicts.py`,
    ```

    `git diff agent_workflows/`:
    ```diff
    diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
    index cff120475..f1d621e2b 100755
    --- a/agent_workflows/agy_runipd.py
    +++ b/agent_workflows/agy_runipd.py
    @@ -2217,8 +2217,8 @@ def save_state(run_dir: Path, state: dict[str, Any]) -> None:
     # returned the FIRST non-empty hit, and the shared reader adopts oc's whole-file scan with a
     # `ses_`-prefix preference, so a log carrying a `conversation_id` EARLY and a `ses_` value LATER now
     # resolves to the `ses_` value. That is decision `06-ct4w0a-D1`, it occurred in 0 of 627 real logs, and
    -# `tests/test_rununify_conflicts.py` (deleted in `19313eed`; no live guard currently asserts this conflict
    -# case) pinned it. The dead `fallback` local this body carried (initialized to None, returned at the
    +# `tests/test_runner_shared.py::SessionIdPrecedenceTests` (replacing `tests/test_rununify_conflicts.py`,
    +# deleted in `19313eed`) pins it. The dead `fallback` local this body carried (initialized to None, returned at the
     # end, unreachable because every assigning branch returned first) is gone.


    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 25dc01548..19c01760f 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -30284,9 +30284,9 @@ def extract_session_id(log_path: Path) -> str | None:
         whereas nothing anywhere pinned agy's ordering; the standing maintainer ruling prefers oc absent a
         significant behavioral difference; and the affected shape needs an unprefixed id EARLY plus a
         `ses_` id LATER in the SAME log, which is an OpenCode id appearing in an Antigravity log and
    -    occurred in 0 of the 627 logs censused. `tests/test_rununify_conflicts.py` (deleted in `19313eed`;
    -    no live guard currently asserts this conflict case) pinned this answer so a future change to it is
    -    a visible edit rather than a silent drift.
    +    occurred in 0 of the 627 logs censused. `tests/test_runner_shared.py::SessionIdPrecedenceTests`
    +    (replacing `tests/test_rununify_conflicts.py`, deleted in `19313eed`) pins this answer so a
    +    future change to it is a visible edit rather than a silent drift.

         A NOTE ON WHAT WAS DELETED: agy's body carried a dead `fallback` local, initialized to `None` and
         returned at the end while every branch that could assign it returned immediately instead. It could
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved sqmzwj --by-human`); no open questions remain. Begin with `aw ipd begin sqmzwj`, then perform E-01..E-03 in dependency order.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or `runner_shared.extract_session_id` no longer containing the `ses_` preference with the `fallback` discipline cited in F-1.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The E-02 sabotage is in-process only, is never written to source, and its script is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit sqmzwj -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize sqmzwj`. Never hand-roll a `git mv`.
