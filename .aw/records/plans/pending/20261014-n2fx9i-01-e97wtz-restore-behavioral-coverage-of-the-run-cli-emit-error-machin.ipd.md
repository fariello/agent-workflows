# IPD: Restore behavioral coverage of the run_cli._emit_error machine JSON payload key set

- Date: 2026-10-14
- Kind: child
- Concern: `run_cli._emit_error` emits, in `--agent`/`--json` mode, a bare machine payload whose key set (`ok`/`error`/`exit_code`, EXTENDED by `extra` and never replaced) is a consumed contract per its own docstring; the test that pinned that key set EXACTLY for the unknown-target refusal (`test_machine_payload_carries_the_same_text_with_unchanged_keys` in `tests/test_run_cli_ledger_message.py`) was deleted in `19313eed`, so a rename or an unconditional extra key on the bare (no-`extra`) path of most `_emit_error` sites would now go undetected outside the single `runs resume --agent` row in `tests/test_run_recovery_cli.py`.
- Scope: Add one new behavioral test module that drives `cli.main` in-process across several `aw run`/`aw runs` leaves and both machine renderers, reaching `_emit_error` through three distinct emit paths (unknown target via `_emit_ledger_not_found`, explicit absent path, and empty ledger via the engine builder), asserting on the returned exit code and on the parsed payload's exact key set and values; then update the stale "deleted in `19313eed`; no live guard currently asserts this" remark in the `_emit_error` docstring to name the new module.
- Scope-Paths: tests/test_run_cli_error_payload_keys.py, agent_workflows/run_cli.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: n2fx9i
- Set: n2fx9i
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: e97wtz
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (/plan-review opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004

- 2026-10-15 draft (opencode): created.
- 2026-10-15 to-review (opencode): authored from backlog n2fx9i; review-ready.

## Goal

Restore, as behavioral tests only (P16), coverage that every machine-mode error emitted through `run_cli._emit_error` without `extra` carries exactly the keys `{"ok", "error", "exit_code"}`, with `ok is False` and `exit_code` equal to the process's returned code, in both `--agent` and `--json` renderers. Lost with `tests/test_run_cli_ledger_message.py` (`ev7t1w` site S-24, disposition RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: unknown-target payload key set

- [x] E-01 Create `tests/test_run_cli_error_payload_keys.py` with a `unittest.TestCase` whose `setUp` calls `support.declare_execution_role(self)` and creates a `tempfile.TemporaryDirectory` (cleaned in `tearDown`), a helper `_cli(*argv)` returning `(cli.main(list(argv)), stdout)` with stdout captured by `unittest.mock.patch("sys.stdout", new_callable=io.StringIO)` (no subprocess pipeline, so the code read is the command's own), and a helper `_payload(out, renderer)` that parses the whole text for `--json` and the last non-empty line for `--agent`. Add `test_unknown_target_payload_has_exactly_the_three_keys`: for each leaf in (`runs verify-ledger`, `runs show`, `runs status`, `run cancel`, `run start`) and each renderer in (`--agent`, `--json`), as `subTest`, invoke `<leaf> totalgibberish --dir <tmp> <renderer>` and assert `rc == run_cli.EXIT_INVALID_INVOCATION`, `set(payload) == {"ok", "error", "exit_code"}`, `payload["ok"] is False`, `payload["exit_code"] == rc`, `payload["error"]` is a non-empty `str` that does NOT start with `"error: "` (the prefix belongs to the human stream per `_emit_ledger_not_found` F-17), and contains `"ledger.jsonl"`. Accumulate per-row problems into one list and assert it is empty, so a drift between inline-routed and `_resolve_or_error`-routed leaves shows as one failure naming every affected leaf.
  - Depends on: none
  - Expected outcome: the module exists and the test passes against current code.
  - Execution state: performed

### Task group 2: other bare emit paths

- [x] E-02 In the same module add `test_explicit_absent_path_payload_has_exactly_the_three_keys` (`runs verify-ledger <tmp>/nowhere/ledger.jsonl --agent`: rc 2, exact key set, `error` contains `"not found"` and does NOT contain `"no driver run writes one"`) and `test_empty_ledger_payload_has_exactly_the_three_keys` (create an empty `<tmp>/ledger.jsonl` and pass that path as the positional target, i.e. `<leaf> <tmp>/ledger.jsonl --agent`; for each leaf in (`runs next`, `runs status`, `runs resume`, `run cancel`), as `subTest`: rc 2, exact key set, `payload["error"] == "ledger is empty"`, `payload["exit_code"] == rc`). Add `test_human_stream_is_not_json` (`runs status totalgibberish --dir <tmp>` with no renderer flag: rc 2, stdout starts with `"error: "`, and `json.loads` of the stdout raises `ValueError`), proving the key-set contract is renderer-gated rather than leaking into human output.
  - Depends on: E-01
  - Expected outcome: the three tests pass against current code.
  - Execution state: performed

### Task group 3: stale remark

- [x] E-03 In `agent_workflows/run_cli.py`, edit the `_emit_error` docstring sentence "`tests/test_run_cli_ledger_message.py` (deleted in `19313eed`; no live guard currently asserts this) formerly pinned the unknown-target payload's key set exactly" so it states that `tests/test_run_cli_error_payload_keys.py` asserts the bare payload's key set exactly across leaves and both machine renderers. Docstring-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the docstring names the live module and no longer claims the property is unguarded.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): drive `cli.main` and assert exit codes and parsed payloads; never read `run_cli.py` source via `inspect`/`ast`/regex.
- The deleted module's `_CliCase._exit_code_unpiped` read `cli.main`'s return directly and captured stdout by patching `sys.stdout`, deliberately avoiding a pipeline (backlog `zrzfkw` measurement error); `tests/test_run_recovery_cli.py` `TestLedgerResolutionAndWrongFormatVerdict._cli` uses the same idiom. The new module follows it.
- Suite runs bare as `python3 -m pytest` (`-n auto`); tests must be xdist-safe (per-test temp dirs) and call `support.declare_execution_role(self)` (`tests/support.py` `declare_execution_role`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-24: `run_cli.py` / `_emit_error` / `tests/test_run_cli_ledger_message.py` / `19313eed` / RETIRE-UNGUARDED; "asserted json key set equality `{"ok", "error", "exit_code"}`".
- `19313eed7^:tests/test_run_cli_ledger_message.py` `TestAbsentLedgerRefusalIsTruthful.test_machine_payload_carries_the_same_text_with_unchanged_keys` drove `runs verify-ledger run-abcdef1234 --dir <tmp> --agent` and asserted `set(payload) == {"ok", "error", "exit_code"}`, `ok is False`, and `exit_code == EXIT_INVALID_INVOCATION`. It is the model for E-01. Its clause/wording assertions are out of scope here (see Deferred).
- `run_cli._emit_error` builds `{"ok": False, "error": message, "exit_code": exit_code}` and calls `payload.update(extra)` only when `extra` is truthy; human mode prints `error: {message}`.
- `run_cli._emit_ledger_not_found` passes `extra` only when the target classifies as `TARGET_DRIVER_RUN`; for an unknown target `extra` is `None`, so the bare shape is emitted.
- Measured in this worktree (2026-10-15): `runs verify-ledger run-abcdef1234 --dir <tmp> --agent` printed `{"error":"ledger file not found for target 'run-abcdef1234': ...","exit_code":2,"ok":false}` with rc=2; `runs status`/`runs next`/`runs resume`/`run cancel` on an empty `ledger.jsonl` with `--agent` each printed `{"error":"ledger is empty","exit_code":2,"ok":false}` with rc=2; `run start`/`run record`/`run finalize`/`runs evidence`/`runs show` on `totalgibberish` printed the bare three-key shape at rc=2 under `--agent` and returned 2 under `--json`.
- Surviving coverage: `tests/test_run_recovery_cli.py` `test_an_unknown_target_keeps_the_bare_machine_shape` asserts the exact key set for `runs resume --agent` only; `test_both_machine_renderers_carry_the_suggestion_as_data` asserts only a SUBSET (`assertLessEqual`) on the driver-run path. No live test asserts the exact key set across leaves, under `--json`, or on the empty-ledger path.

## Proposed changes (ordered, validatable)

1. E-01: new module; unknown-target bare payload key set across five leaves and both machine renderers.
2. E-02: explicit-absent-path and empty-ledger bare payloads, plus human-stream non-JSON check.
3. E-03: docstring-only update in `run_cli._emit_error`.

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted module (three-clause wording table, no-run-health prohibition, explicit-path bare sentence beyond the key set, present-ledger happy path): not part of backlog `n2fx9i`, which names only the machine JSON payload key set.
  - Carrier-Declined: outside this backlog item's named property; the wording clauses are largely re-covered by `tests/test_run_recovery_cli.py` signpost tests and no defect is known.
- The `extra`-extended driver-run payload: already covered by `tests/test_run_recovery_cli.py` `test_both_machine_renderers_carry_the_suggestion_as_data`.
  - Carrier-Declined: live coverage exists.
- Converting these payloads to `aw.agent/v1` records: a different contract explicitly declined in the `_emit_error` docstring (F-16).
  - Carrier-Declined: deliberate non-goal, not an outstanding obligation.
- Any behavior change to `run_cli`: this is coverage restoration.
  - Carrier-Declined: deliberate non-goal.

## Scope check

- Over-scope: none. The only production edit is a docstring sentence that would otherwise remain false.
- Under-scope: none. The named property (bare machine payload key set) is covered on three emit paths, many leaves, and both machine renderers.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_run_cli_error_payload_keys.py` passes (V-01, V-02).
- Mutation check: temporarily add `"detail": None` to the bare payload dict in `_emit_error`, confirm the E-01 and E-02 key-set tests FAIL, then revert (V-01).
- Mutation check: temporarily make `_emit_error` set `"exit_code": 0` in the payload, confirm `test_empty_ledger_payload_has_exactly_the_three_keys` FAILS, then revert (V-02).
- Full bare suite `python3 -m pytest` with no new failures (V-03).

## Spec / documentation sync

N/A: `docs/cli-output-contract.md` already describes `_emit_error` payloads as bare JSON dictionaries outside the `aw.agent/v1` envelope, and nothing here changes that; the only text change is the `_emit_error` docstring in E-03.

## Open questions

### OQ-01: New module or re-create `tests/test_run_cli_ledger_message.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: a new purpose-named module `tests/test_run_cli_error_payload_keys.py`. Re-creating the deleted name would imply its wording-clause tests are restored too, which this item does not do; sibling restoration plan `4xqhsq` (backlog `heknx6`) likewise uses a purpose-named module.

## Validation and cross-check (verify before reporting done)

Test function names below are non-binding POINTERS, not the bar: the bar is the behavior each item names (exact bare key set, `ok is False`, `exit_code == rc`, renderer gating) plus the mutation run proving the test detects its violation; a renamed test that pins the same behavior satisfies the item. Re-derive at execution time.

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_run_cli_error_payload_keys.py` showing `test_unknown_target_payload_has_exactly_the_three_keys` PASSED; pasted output of the temporary `"detail": None` mutation run showing that test FAILED, followed by `git diff --stat agent_workflows/run_cli.py` after revert proving only the E-03 docstring change remains; plus `grep -nE "^\s*(import|from) (inspect|ast)\b|\.read_text\(|getsource" tests/test_run_cli_error_payload_keys.py` returning no match (P16: the module reads no production source).
  - Observed evidence:
    pytest -o addopts="" -v tests/test_run_cli_error_payload_keys.py:
    ```
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys PASSED [ 25%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys PASSED [ 50%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_human_stream_is_not_json PASSED [ 75%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys PASSED [100%]

    ============================== 4 passed in 1.99s ===============================
    ```
    Mutation run with "detail": None added to _emit_error payload:
    ```
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_human_stream_is_not_json PASSED [ 25%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys FAILED [ 50%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys FAILED [ 75%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys FAILED [100%]

    =================================== FAILURES ===================================
    _ TestRunCliErrorPayloadKeys.test_unknown_target_payload_has_exactly_the_three_keys _
    ...
    >                   self.assertEqual(set(payload), {"ok", "error", "exit_code"})
    E                   AssertionError: Items in the first set but not the second:
    E                   'detail'

    tests/test_run_cli_error_payload_keys.py:89: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys
    ========================= 3 failed, 1 passed in 0.66s ==========================
    ```
    git diff --stat agent_workflows/run_cli.py after revert:
    ```
     agent_workflows/run_cli.py | 6 +++---
     1 file changed, 3 insertions(+), 3 deletions(-)
    ```
    grep -nE "^\s*(import|from) (inspect|ast)\b|\.read_text\(|getsource" tests/test_run_cli_error_payload_keys.py:
    (empty, exit code 1)
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `-v` pytest output showing `test_explicit_absent_path_payload_has_exactly_the_three_keys`, `test_empty_ledger_payload_has_exactly_the_three_keys` and `test_human_stream_is_not_json` PASSED; pasted output of the temporary `"exit_code": 0` mutation showing `test_empty_ledger_payload_has_exactly_the_three_keys` FAILED, then reverted.
  - Observed evidence:
    pytest -o addopts="" -v tests/test_run_cli_error_payload_keys.py:
    ```
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys PASSED [ 25%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys PASSED [ 50%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_human_stream_is_not_json PASSED [ 75%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys PASSED [100%]
    ```
    Mutation run with "exit_code": 0 in _emit_error payload:
    ```
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_human_stream_is_not_json PASSED [ 25%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys FAILED [ 50%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys FAILED [ 75%]
    tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys FAILED [100%]

    =================================== FAILURES ===================================
    _ TestRunCliErrorPayloadKeys.test_empty_ledger_payload_has_exactly_the_three_keys _

    self = <tests.test_run_cli_error_payload_keys.TestRunCliErrorPayloadKeys testMethod=test_empty_ledger_payload_has_exactly_the_three_keys>
    ...
    >               self.assertEqual(payload["exit_code"], rc)
    E               AssertionError: 0 != 2

    tests/test_run_cli_error_payload_keys.py:125: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_unknown_target_payload_has_exactly_the_three_keys
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_empty_ledger_payload_has_exactly_the_three_keys
    FAILED tests/test_run_cli_error_payload_keys.py::TestRunCliErrorPayloadKeys::test_explicit_absent_path_payload_has_exactly_the_three_keys
    ========================= 3 failed, 1 passed in 0.67s ==========================
    ```
    Reverted and confirmed clean.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/run_cli.py` showing only docstring lines changed and naming `tests/test_run_cli_error_payload_keys.py`; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
    git diff agent_workflows/run_cli.py:
    ```diff
    diff --git a/agent_workflows/run_cli.py b/agent_workflows/run_cli.py
    index c70ba2f04..4eb6635b5 100644
    --- a/agent_workflows/run_cli.py
    +++ b/agent_workflows/run_cli.py
    @@ -860,9 +860,9 @@ def _emit_error(
         against one; `run_cli` imports `agent_schema` zero times. Converting them is a real gap on a
         different contract, across every `_emit_machine`/`_emit_error` site, and doing it here would
         silently change what every existing `aw run`/`aw runs --agent` consumer parses. So `extra`
    -    EXTENDS the shape that exists, and `tests/test_run_cli_ledger_message.py` (deleted in
    -    `19313eed`; no live guard currently asserts this) formerly pinned the unknown-target payload's key
    -    set exactly, which is what kept this from drifting into a rewrite.
    +    EXTENDS the shape that exists, and `tests/test_run_cli_error_payload_keys.py` asserts the bare
    +    payload's key set exactly across leaves and both machine renderers, which is what keeps this from
    +    drifting into a rewrite.
         """
         if _machine(args):
             payload: Dict[str, Any] = {
    ```
    Bare `python3 -m pytest` summary line:
    ```
    702 passed in 23.04s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Open questions: OQ-01 is resolved; none remain. Start a hand execution with `aw ipd begin e97wtz`.

- Scope fence: `- Scope-Paths:` is a DECLARATION reconciled at finalize. The only production edit is the E-03 docstring sentence; an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`, not treated as a reason to stop. The V-01/V-02 mutations are TEMPORARY in-tree edits to `agent_workflows/run_cli.py` that MUST be reverted before any commit; never commit a mutation.
- Honesty rule (hard MUST): every `V-*` `Observed evidence` block pastes the ACTUAL runner output; a claimed pass without pasted output does not satisfy the item. Do not weaken an assertion to make a test pass.
- Commit: only through `aw commit e97wtz -- tests/test_run_cli_error_payload_keys.py agent_workflows/run_cli.py <this plan path>` (never `git add -A`, `-a`, or `--no-verify`); verify the staged set with `git diff --cached --name-only` first; never push.
- Lifecycle transition (mandatory; owner conditional): when dispatched by `aw oc run` / `aw agy run`, the runner performs the finalize (path-scoped commit and move to `executed/`) after its merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize`; in a hand execution the executor runs `aw ipd finalize e97wtz`. Never hand-`git mv` the plan into `executed/` or hand-edit `- Status:`. The transition happens only after `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry pasted observed evidence with `Result: pass`.
- Release gate: backlog `n2fx9i` is `Work-Kind: chore` and carries no `- Blocks-Release:`, so none is inherited and none may be invented; it reaches `done` through the `- From-Backlog: n2fx9i` handoff, so do not close it by hand.
