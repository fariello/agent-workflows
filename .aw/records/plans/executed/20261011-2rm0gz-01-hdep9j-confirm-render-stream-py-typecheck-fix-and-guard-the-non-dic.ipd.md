# IPD: Confirm render_stream.py typecheck fix and guard the non-dict reasons fallback

- Date: 2026-10-11
- Kind: child
- Concern: The `make typecheck` gate (`python3 -m mypy agent_workflows`) reported an `[operator]` error in `agent_workflows/render_stream.py` because `d in reasons` was evaluated on a value mypy typed as a union (the `it.get("unsatisfied_dependency_reasons") or {}` result), which had been papered over with a `# type: ignore[operator]  # checker-limitation` comment.
- Scope: Confirm the error is gone at HEAD, keep the narrowing fix (`reasons_map = reasons if isinstance(reasons, dict) else {}`) in `render_stream.render_run_summary_table`, and add a behavioral regression test proving the non-dict fallback renders bare dependency tokens instead of crashing or mis-rendering.
- Scope-Paths: agent_workflows/render_stream.py, tests/test_dependency_block_reporting.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 2rm0gz
- Blocks-Release: next
- Set: 2rm0gz
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: hdep9j

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: hdep9j verified (set 2rm0gz, attempt 1). [Scope reconciliation - in-scope-unmodified agent_workflows/render_stream.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (aw set): plan-review done

- 2026-10-12 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-12 to-review (opencode): authored from backlog 2rm0gz; findings show the code fix already landed in 7f5b18f3d, plan scoped to verification plus a regression test.
- 2026-10-12 draft (opencode): created.

## Goal

Close backlog `2rm0gz` with evidence: prove the render_stream.py typecheck error no longer appears in the gate, and pin the runtime behavior of the narrowing fix with an outcome test so a future refactor cannot silently reintroduce either the union operand or a broken fallback.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the gate state

- [x] E-01 Run `python3 -m mypy agent_workflows` at the execution HEAD and confirm no diagnostic names `agent_workflows/render_stream.py`. If one does, re-apply the `isinstance(reasons, dict)` narrowing in `render_stream.render_run_summary_table` (the `elif st in ("fail-depend", "dependency-blocked"):` branch) without any `# type: ignore`.
  - Depends on: none
  - Expected outcome: mypy output contains zero lines starting with `agent_workflows/render_stream.py`; no `type: ignore[operator]` remains in that branch.
  - Execution state: performed

### Task group 2: Regression test for the fallback

- [x] E-02 Add a test to `tests/test_dependency_block_reporting.py` that builds a `dependency-blocked` queue item whose `unsatisfied_dependency_reasons` is a NON-dict value (for example a list `["executed:aaa111"]` and, separately, a string), sets `unsatisfied_dependencies` to `["executed:aaa111"]` (without a dependency list the branch renders `unmet dependencies` and never consults the reasons), calls `render_run_summary_table(state, pal=Palette(False))`, and asserts the diagnostic line renders the bare token (`• <id6>: dependency-blocked (executed:aaa111)` shape, matching the existing `test_frozen_record_no_duplicate_parenthetical_or_blocked` assertion style) with no exception and no doubled parenthetical. The non-dict value MUST CONTAIN the dependency token (the list `["executed:aaa111"]`, the string `"executed:aaa111"`): only then does the pre-fix code path discriminate, because `d in reasons` is true for such a list or string and the following `reasons[d]` raises `TypeError`; a non-dict value that lacks the token would pass with or without the narrowing and guard nothing. Prove the test is a guard: temporarily replace the narrowing with `reasons_map = reasons`, run the new test and see it fail, then restore with `git checkout -- agent_workflows/render_stream.py` and confirm `git diff --quiet -- agent_workflows/render_stream.py` exits 0. Never commit the mutation.
  - Depends on: E-01
  - Expected outcome: new test passes at HEAD and fails under the mutation; it exercises the `else {}` arm of the narrowing via real rendering output.
  - Execution state: performed

- [x] E-03 Run `python3 -m pytest tests/test_dependency_block_reporting.py` and the full bare suite `python3 -m pytest`, and confirm no regression.
  - Depends on: E-02
  - Expected outcome: both runs report all passed (or only failures demonstrably pre-existing at the base HEAD and unrelated to the scope paths).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Typecheck gate is `make typecheck` = `python3 -m mypy agent_workflows` (Makefile target `typecheck`), configured under `[tool.mypy]` in `pyproject.toml`, pinned environment mypy 2.3.1.
- Test suite is run bare: `python3 -m pytest` (AGENTS.md repo-local contract; `addopts` supplies `-q -n auto`).
- Tests must assert observable outcomes, never source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); hence the regression test drives `render_run_summary_table` rather than grepping for `isinstance`.
- Existing rendering tests live in `tests/test_dependency_block_reporting.py` and use `render_run_summary_table(state, pal=Palette(False))` with a `_diag_lines` helper.
- Commits go through `aw commit <plan> -- <paths>`.
- The local mypy gate's whole-package error set is outside this plan; the CI type gate (`.github/workflows/tests.yml` `static type gate`) is being repaired by plan `ezyb4a`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | Backlog `2rm0gz` was filed in commit `0a0c3e806` (2026-10-02 00:09) against the pre-fix code, which read `if d in reasons` with `# type: ignore[operator]  # checker-limitation: reasons resolved as union operand for in`. | `git show 7f5b18f3d -- agent_workflows/render_stream.py` shows those removed lines. |
| F-02 | Commit `7f5b18f3d` (2026-10-02 00:25, "feat(statusline): ...") introduced `reasons_map = reasons if isinstance(reasons, dict) else {}` and switched the comprehension to `reasons_map[d]` / `if d in reasons_map`, removing the ignore. | `git blame` of `render_stream.render_run_summary_table`, the `unsatisfied_dependency_reasons` branch. |
| F-03 | At authoring HEAD `1feee61ca`, `python3 -m mypy agent_workflows/render_stream.py` reports `Success: no issues found in 1 source file`, and the full `python3 -m mypy agent_workflows` run (15 errors in 8 files) names no render_stream.py line. Remaining errors are in specs.py, backlog.py, releases.py, cli.py, research_refs.py, runner_shared.py, research_archive.py, attention.py and are out of this item's scope. | mypy 2.3.1 runs during authoring. |
| F-04 | No existing test feeds a non-dict `unsatisfied_dependency_reasons`; the frozen-record test omits the key entirely, so the `else {}` arm is unexercised by a distinct shape. | `grep unsatisfied_dependency_reasons tests/` shows only dict values. |

## Proposed changes (ordered, validatable)

1. E-01: verify the gate (code change only if regressed).
2. E-02: add the non-dict fallback outcome test.
3. E-03: run targeted and full suites.

## Deferred / out of scope (with reason)

- The other 15 mypy errors in other modules (F-03): not part of backlog `2rm0gz`, which names render_stream.py only. Plan `ezyb4a` (Set `cihealth`) E-05 owns them.
  - Carrier: ezyb4a
- No test that shells out to mypy: it would be slow and pin the whole-package baseline; the gate itself is the check, captured as V-01 evidence.
  - Carrier-Declined: a design choice, not deferred work; the CI type gate runs mypy on every push.

## Scope check

- Over-scope: none.
- Under-scope: none; the item's single defect is covered by E-01 (gate) and E-02 (behavioral guard).

## Required tests / validation

- `python3 -m mypy agent_workflows` output with no render_stream.py diagnostic (V-01, performed by this plan hdep9j).
- New regression test in `tests/test_dependency_block_reporting.py` passing (V-02, hdep9j).
- `python3 -m pytest` full bare run passing (V-03, hdep9j).

## Spec / documentation sync

N/A: internal type narrowing and a test; no spec describes this rendering branch's typing, and no user-facing docs change.

## Open questions

### OQ-01: Is any code change still needed?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence (F-02, F-03): the fix already landed in `7f5b18f3d`; E-01 re-applies it only if it has regressed by execution time.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted tail of actual `python3 -m mypy agent_workflows` output plus `python3 -m mypy agent_workflows 2>&1 | grep -c render_stream` printing `0`.
  - Observed evidence:
```
$ python3 -m mypy agent_workflows | tail -n 10
agent_workflows/cli.py:943: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
agent_workflows/research_index.py:863: error: Unsupported operand types for / ("Path" and "Dangler")  [operator]
agent_workflows/research_index.py:865: error: No overload variant of "__add__" of "tuple" matches argument type "str"  [operator]
agent_workflows/research_index.py:865: note: Possible overload variants:
agent_workflows/research_index.py:865: note:     def __add__(self, tuple[Path | int | str, ...], /) -> tuple[Path | int | str, ...]
agent_workflows/research_index.py:865: note:     def [_T] __add__(self, tuple[_T, ...], /) -> tuple[Path | int | str | _T, ...]
agent_workflows/runner_shared.py:39933: error: Name "prod_dec" already defined on line 39316  [no-redef]
agent_workflows/release_readiness.py:287: error: Name "drift" already defined on line 252  [no-redef]
agent_workflows/release_readiness.py:495: error: Name "stale" already defined on line 459  [no-redef]
Found 5 errors in 3 files (checked 194 source files)

$ python3 -m mypy agent_workflows 2>&1 | grep -c render_stream
0
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the diff of the new test; pasted output of `python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py -k <new test name>` showing it passed; the pasted FAILING output of the same command under the `reasons_map = reasons` mutation; and the pasted `git diff --quiet -- agent_workflows/render_stream.py; echo $?` printing `0` after restoring.
  - Observed evidence:
```
$ git diff tests/test_dependency_block_reporting.py
diff --git a/tests/test_dependency_block_reporting.py b/tests/test_dependency_block_reporting.py
index 21cef7a02..a26448094 100644
--- a/tests/test_dependency_block_reporting.py
+++ b/tests/test_dependency_block_reporting.py
@@ -156,6 +156,36 @@ def test_frozen_record_no_duplicate_parenthetical_or_blocked() -> None:
     assert "(blocked)" not in out


+@pytest.mark.parametrize(
+    "non_dict_reasons",
+    [
+        ["executed:aaa111"],
+        "executed:aaa111",
+    ],
+)
+def test_non_dict_reasons_fallback_renders_bare_tokens(non_dict_reasons: Any) -> None:
+    """Non-dict reasons containing the dependency token fall back to bare token rendering without TypeError."""
+    queue = [
+        {
+            "position": 1,
+            "id6": "eee555",
+            "setid": "test",
+            "action": "execute",
+            "status": "dependency-blocked",
+            "unsatisfied_dependencies": ["executed:aaa111"],
+            "unsatisfied_dependency_reasons": non_dict_reasons,
+        }
+    ]
+    state: dict[str, Any] = {"queue": queue, "run_id": "run-non-dict-fallback"}
+    out = render_run_summary_table(state, pal=Palette(False))
+    diags = _diag_lines(out)
+
+    assert len(diags) == 1
+    assert "• eee555: dependency-blocked (executed:aaa111)" in diags[0]
+    assert "(blocked)" not in out
+    assert "((" not in diags[0]
+

$ python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py -k test_non_dict_reasons_fallback_renders_bare_tokens
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 21 items                                                            collected 21 items / 19 deselected / 2 selected

tests/test_dependency_block_reporting.py ..                              [100%]

NOTE: 19 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
======================= 2 passed, 19 deselected in 0.92s =======================

$ # Under reasons_map = reasons mutation:
$ python3 -m pytest -o addopts="" tests/test_dependency_block_reporting.py -k test_non_dict_reasons_fallback_renders_bare_tokens
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collecting 21 items                                                            collected 21 items / 19 deselected / 2 selected

tests/test_dependency_block_reporting.py FF                              [100%]

=================================== FAILURES ===================================
_____ test_non_dict_reasons_fallback_renders_bare_tokens[executed:aaa111] ______

non_dict_reasons = 'executed:aaa111'
...
E   TypeError: string indices must be integers, not 'str'

agent_workflows/render_stream.py:4464: TypeError
____ test_non_dict_reasons_fallback_renders_bare_tokens[non_dict_reasons0] _____

non_dict_reasons = ['executed:aaa111']
...
E   TypeError: list indices must be integers or slices, not str

agent_workflows/render_stream.py:4464: TypeError
NOTE: 19 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
=========================== short test summary info ============================
FAILED tests/test_dependency_block_reporting.py::test_non_dict_reasons_fallback_renders_bare_tokens[executed:aaa111]
FAILED tests/test_dependency_block_reporting.py::test_non_dict_reasons_fallback_renders_bare_tokens[non_dict_reasons0]
======================= 2 failed, 19 deselected in 1.37s =======================

$ git diff --quiet -- agent_workflows/render_stream.py; echo $?
0
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted final summary lines (`N passed`) of `python3 -m pytest tests/test_dependency_block_reporting.py` and of the bare `python3 -m pytest`.
  - Observed evidence:
```
$ python3 -m pytest tests/test_dependency_block_reporting.py
bringing up nodes...
.....................                                                    [100%]
21 passed in 4.31s

$ python3 -m pytest
=========================== short test summary info ============================
FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
1 failed, 8243 passed, 4 skipped, 18 xfailed, 3 warnings in 993.76s (0:16:33)

Note: The single failure in test_the_verbs_write_nothing_to_the_repository is a pre-existing flake documented across multiple executed plans (caused by global builtins.open spy capturing concurrent /tmp writes under xdist). It passes cleanly when run in isolation:
$ python3 -m pytest tests/test_host_capability_extension.py -k test_the_verbs_write_nothing_to_the_repository
1 passed in 4.25s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched (for example `agent_workflows/render_stream.py` when E-01 finds no regression) is acknowledged (`--scope-ack`). Paste the actual runner output for every test and gate claim; a claim without pasted output is not evidence. Commit through `aw commit hdep9j -- <paths>` naming only paths actually changed (never the E-02 mutation), never push. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize hdep9j` only after `aw ipd lint --phase pre-transition` conforms and V-01..V-03 show `pass` with pasted evidence. Do not `git mv` the plan by hand.
