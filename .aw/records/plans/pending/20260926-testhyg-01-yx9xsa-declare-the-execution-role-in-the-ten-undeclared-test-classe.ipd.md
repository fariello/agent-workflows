# IPD: Declare the execution role in the ten undeclared test classes of test_ipd_lifecycle_cli.py

- Date: 2026-09-26
- Kind: child
- Concern: `tests/test_ipd_lifecycle_cli.py` has 11 `TestCase` classes and only `BeginCliTests` declares its execution role (`support.declare_execution_role(self)` first in `setUp`). The other ten inherit the ambient `AW_EXECUTION_ROLE`. The root `conftest.py` pops that variable at import, which masks the defect in a normal run, but any process that re-asserts `AW_EXECUTION_ROLE=worker` after conftest (a runner lane turn whose environment is re-applied, a plugin, an in-test leak) turns lifecycle tests red with `AW-LIFECYCLE-ROLE-001`. Measured at HEAD `61ef21d8` with a throwaway plugin re-asserting the marker in `pytest_runtest_setup`: `22 failed, 15 passed`. The conftest comment explaining this cites a deleted test file and a stale count.
- Scope: IN: declare the role first in `setUp` of the ten undeclared classes (adding a `setUp` to the one that has none); correct the stale `conftest.py` comment. OUT: a permanent guard test (maintainer declined structural guards); other test files.
- Scope-Paths: tests/test_ipd_lifecycle_cli.py, conftest.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: owi0no
- Blocks-Release: next
- Set: testhyg
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: yx9xsa

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog owi0no: declare the execution role in the ten undeclared classes of test_ipd_lifecycle_cli.py; re-measured 22 failures under a re-asserted worker marker at HEAD 61ef21d8.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every test in `tests/test_ipd_lifecycle_cli.py` measures the same behavior whether or not the ambient process carries `AW_EXECUTION_ROLE=worker`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declare, correct, verify

- [ ] E-01 In `tests/test_ipd_lifecycle_cli.py`, make `support.declare_execution_role(self)` the FIRST statement of `setUp` in each of: `BeginHappyPathTests`, `BeginFailClosedTests`, `FinalizeTests`, `ReconciliationTests`, `AdditiveScopeWideningTests`, `RollbackFailureSemanticsTests`, `TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout`, `DelegationAndBypassRemovalTests`, `ParenthesizedActorIsRefusedBeforeAnyWrite`. `ScaffoldStopsWritingTheShapeItsOwnSetterRefuses` has no `setUp`; add `def setUp(self) -> None: support.declare_execution_role(self)`. `support` is already imported (`from tests import support`). A class that defines `setUp` in a subclass must still reach the declaration (none do today; confirm with `grep -n "super().setUp\|class .*(.*Tests)" tests/test_ipd_lifecycle_cli.py`). No other change to any test body.
  - Depends on: none
  - Expected outcome: all 11 classes declare the coordinator role.
  - Execution state: pending

- [ ] E-02 Rewrite the `HONEST LIMITS` and `CROSS-REFERENCE` paragraphs of the `conftest.py` comment block above `os.environ.pop("AW_EXECUTION_ROLE", None)`: remove both references to `tests/test_role_declaration_guard.py` (deleted; `git ls-files tests/test_role_declaration_guard.py` is empty) and the claim that 42 tests in `tests/test_ipd_lifecycle_cli.py` still inherit the ambient role; state instead that tests which drive lifecycle wrappers declare their role with `support.declare_execution_role`, and that re-asserting the marker with a throwaway `pytest_runtest_setup` plugin is how to check a file (as plan yx9xsa did). Keep the paragraph about `test_driver_own_process_is_not_worker_role` minus its dead cross-reference. Also remove the parenthetical "re-measured at IPD `8i0xa7`: 42 tests ... see backlog `owi0no`" in the WHAT WENT WRONG paragraph, or reword it to say the gap was closed by plan yx9xsa.
  - Depends on: E-01
  - Expected outcome: the comment cites no deleted file and no stale count.
  - Execution state: pending

- [ ] E-03 Verify with a throwaway plugin OUTSIDE the repo and run the bare suite. Create `/tmp/opencode/roleplug/reassert_worker.py` containing a `@pytest.hookimpl(trylast=True) def pytest_runtest_setup(item): os.environ["AW_EXECUTION_ROLE"] = "worker"` (trylast so it runs after conftest's import-time pop and before each test body; `setUp` then runs inside the test call and the declaration overrides it). Run `PYTHONPATH=/tmp/opencode/roleplug python3 -m pytest tests/test_ipd_lifecycle_cli.py -p reassert_worker -o addopts="-q -n auto"` before and after E-01. Then run the bare suite. Do not commit the plugin.
  - Depends on: E-01, E-02
  - Expected outcome: before `22 failed, 15 passed`; after `0 failed` (37 passed); bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `support.declare_execution_role(case, role=None)` enters the declaration immediately and unwinds via `addCleanup`, so it cannot leak into the next test on the same xdist worker (its docstring).
- Maintainer rule: no permanent structural guard tests; tests assert outcomes only. This plan adds no test; it corrects fixtures, and the verification is a one-off probe.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `tests/test_ipd_lifecycle_cli.py` | 10 of 11 classes do not declare their role; under a re-asserted worker marker 22 tests fail: FinalizeTests 5, RollbackFailureSemanticsTests 4, TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout 4, ReconciliationTests 3, AdditiveScopeWideningTests 3, DelegationAndBypassRemovalTests 2, ParenthesizedActorIsRefusedBeforeAnyWrite 1. | `PYTHONPATH=/tmp/opencode/roleplug python3 -m pytest tests/test_ipd_lifecycle_cli.py -p reassert_worker -o addopts="-q -n auto"` -> `22 failed, 15 passed in 6.49s` |
| F-2 | INFO | BeginHappyPathTests, BeginFailClosedTests, ScaffoldStops... | These three pass under the probe today but are declared anyway so the file has one rule and a future edit cannot silently start inheriting. | same run: no failures in those classes |
| F-3 | LOW | `conftest.py` comment | Cites the deleted `tests/test_role_declaration_guard.py` twice and a count of 42. | `git ls-files tests/test_role_declaration_guard.py` -> empty |
| F-4 | INFO | backlog owi0no body | Says 42 tests fail; measured 22 at HEAD. The brief's 22 is correct. | F-1 |

## Proposed changes (ordered, validatable)

1. E-01: declare the role in ten classes.
2. E-02: correct the conftest comment.
3. E-03: probe before/after and bare suite.

## Deferred / out of scope (with reason)

- A permanent guard test asserting every lifecycle test class declares its role: the maintainer declined structural guards (2026-09-26); the probe in E-03 is the one-off check.
  - Carrier-Declined: maintainer decision 2026-09-26, no structural guard tests.

## Scope check

- Over-scope: none. F-2's three classes are included because the brief and the item scope all ten undeclared classes.
- Under-scope: none.

## Required tests / validation

- The E-03 probe before and after, and the bare suite. No new test is added (fixture correction only; outcome rule respected).

## Spec / documentation sync

N/A: test fixtures and a code comment only.

## Open questions

### OQ-01: Should the plugin use `pytest_runtest_setup` or `pytest_configure`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `pytest_runtest_setup` with `trylast=True`, measured: it reproduces exactly the 22 failures, and it re-asserts before every test, which is the strongest ambient condition the declaration must survive. `pytest_configure` sets it once and a test's cleanup could clear it for later tests on the worker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `grep -c "support.declare_execution_role(self)" tests/test_ipd_lifecycle_cli.py` showing 11 and `grep -c "^class .*TestCase" tests/test_ipd_lifecycle_cli.py` showing 11.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the conftest diff; paste `grep -n "test_role_declaration_guard\|42 tests" conftest.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the plugin file content; paste the probe's summary line BEFORE E-01 (expected `22 failed`) and AFTER (expected `0 failed`, i.e. `37 passed`); paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Eleven one-line fixture declarations in one test file and a corrected comment in `conftest.py`. No production code changes; no new test.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); the probe plugin under `/tmp` is not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `owi0no` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
