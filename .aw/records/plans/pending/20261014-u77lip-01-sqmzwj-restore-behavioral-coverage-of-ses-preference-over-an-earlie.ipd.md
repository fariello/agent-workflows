# IPD: Restore behavioral coverage of ses_ preference over an earlier conversation_id hit in extract_session_id

- Date: 2026-10-14
- Kind: child
- Concern: The `06-ct4w0a-D1` precedence decision in `runner_shared.extract_session_id` (a `conversation_id` hit EARLY in a log and a `ses_`-prefixed value LATER resolves to the `ses_` value) lost its only behavioral test when `tests/test_rununify_conflicts.py` was deleted in `19313eed`.
- Scope: Add behavioral tests to `tests/test_runner_shared.py` that write mixed JSONL logs and assert the value `extract_session_id` returns, reached through `runner_shared` and through both host modules; then repoint the two source comments that currently say "no live guard currently asserts this conflict case" at the new test.
- Scope-Paths: tests/test_runner_shared.py, agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending/20261014-u77lip-01-sqmzwj-restore-behavioral-coverage-of-ses-preference-over-an-earlie.ipd.md
- Item-Dependencies: none
- Status: reviewed
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
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record 20261014-u77lip-01-sqmzwj)
- 2026-10-15 draft (OpenCode Claude Opus): created.
- 2026-10-15 to-review (OpenCode Claude Opus): authored review-ready from backlog `u77lip`.

## Goal

Restore a live, behavioral guard for decision `06-ct4w0a-D1`: on a log carrying an unprefixed `conversation_id` before a `ses_`-prefixed id, `extract_session_id` returns the `ses_` id, and with no `ses_` id it falls back to the first unprefixed hit. The guard calls the function on real temp files and asserts on its return value only (P16); it never reads source.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Behavioral tests

- [ ] E-01 Add a `SessionIdPrecedenceTests(unittest.TestCase)` class to `tests/test_runner_shared.py` that writes JSONL fixtures into a `tempfile.TemporaryDirectory()` and asserts on the return value of `extract_session_id`, called as `runner_shared.extract_session_id` and as each module in `BOTH` (`_MODULES[runner].extract_session_id`, via `subTest`). Cases: (a) `{"type": "result", "conversation_id": "conv-EARLY"}` then `{"type": "step", "sessionID": "ses_" + "LATER"}` returns `"ses_LATER"`; (b) the same `conversation_id` nested as `{"result": {"conversation_id": "conv-EARLY"}}` before a flat `ses_` id returns the `ses_` id; (c) a log with only `conversation_id` values (`conv-FIRST` then `conv-SECOND`) returns `"conv-FIRST"` (the fallback keeps the first unprefixed hit). Build the `ses_` literal by concatenation (`"ses" + "_"`) as `tests/test_oc_runipd.py::test_extract_session_id_prefers_ses_prefixed_over_nonprefixed` does. No `inspect`, `ast`, regex or source reads.
  - Depends on: none
  - Expected outcome: `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k SessionIdPrecedence` reports the new tests passing.
  - Execution state: pending

- [ ] E-02 Demonstrate non-vacuity of cases (a) and (b) IN-PROCESS, never editing source (E-03 edits the same two files, so a source sabotage restored with `git checkout --` could wipe E-03's edits, and stashing is forbidden). Write a throwaway script under the gitignored `.aw/state/` that defines a first-hit replacement (the same scan of `runner_shared._SESSION_ID_KEYS` flat and in `runner_shared._SESSION_ID_NESTS`, but returning the FIRST non-empty value immediately: agy's pre-union behavior described in the docstring), patches it over `extract_session_id` on ALL THREE modules with `unittest.mock.patch.object(...).start()` (`runner_shared`, `oc_runipd`, `agy_runipd`; each host holds its OWN binding of the shared function, so patching `runner_shared` alone does NOT reach the host subtests), then calls `pytest.main(["-o", "addopts=", "-p", "no:randomly", "tests/test_runner_shared.py", "-k", "SessionIdPrecedence"])`. Confirm cases (a) and (b) FAIL with `conv-EARLY` and case (c) still passes, then delete the script.
  - Depends on: E-01
  - Expected outcome: pasted failing output under the in-process sabotage; `git status --short agent_workflows/` afterwards shows nothing beyond E-03's edits.
  - Execution state: pending

### Task group 2: Repoint stale comments

- [ ] E-03 Rewrite the parenthetical "`tests/test_rununify_conflicts.py` (deleted in `19313eed`; no live guard currently asserts this conflict case)" in the `runner_shared.extract_session_id` docstring and in the `agy_runipd.py` comment block beginning "`_SESSION_ID_KEYS` and `extract_session_id` are now defined ONCE in `runner_shared`" so each names the new live guard `tests/test_runner_shared.py::SessionIdPrecedenceTests` (keeping the historical note that the original file was deleted in `19313eed`). Comment/docstring text only; no code change.
  - Depends on: E-01
  - Expected outcome: `grep -n "no live guard currently asserts this conflict" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` returns nothing and both locations cite `SessionIdPrecedenceTests`.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest tests/test_runner_shared.py -o addopts="" -v -k SessionIdPrecedence` listing each new test as PASSED, plus pasted output of the bare full-suite `python3 -m pytest` summary line; and pasted passing output of `python3 -m pytest -o addopts="" tests/test_no_code_structure_pins.py` with the new class present, plus the pasted new class body showing it only writes temp JSONL files and calls `extract_session_id`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output under the local first-hit sabotage showing cases (a) and (b) FAILED with `conv-EARLY` in the assertion message, showing case (c) still PASSED, plus the pasted throwaway script (proving all three module bindings were patched in-process) and `git status --short agent_workflows/` afterwards showing nothing beyond E-03's edits.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of `grep -n "no live guard currently asserts this conflict" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` (empty) and `grep -n "SessionIdPrecedenceTests" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` (one hit each), plus `git diff agent_workflows/` showing comment/docstring lines only.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved sqmzwj --by-human`); no open questions remain. Begin with `aw ipd begin sqmzwj`, then perform E-01..E-03 in dependency order.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to a scoped file that cannot be safely combined, or `runner_shared.extract_session_id` no longer containing the `ses_` preference with the `fallback` discipline cited in F-1.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The E-02 sabotage is in-process only, is never written to source, and its script is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit sqmzwj -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the RUNNER owns finalize, so do not run it yourself; when executing by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize sqmzwj`. Never hand-roll a `git mv`.
