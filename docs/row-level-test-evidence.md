# Row-Level Test Evidence

This document defines how an executing agent obtains truthful row-level test verdicts to satisfy an IPD validation item (V-item) when an individual named test has been refactored into a parameterized table row.

## Purpose

When individual test methods are consolidated into a parameterized table over `self.subTest(...)`, a V-item citing an older test name cannot run a single dedicated test method. Under the substitution rule established in plan `vtup6x` (`nos070-01`), the executor runs the containing table test and provides evidence for the specific table row corresponding to the requirement.

## Repeatable Command

To execute a test and obtain per-row verdicts alongside the enclosing test verdict, run:

```sh
python3 -c "import agent_workflows.subtest_rows as r; r.run('tests.test_executed_transition_gate_e2e.MergeAwareInTreeEvidenceTests.test_merge_state_never_becomes_a_blanket_exemption')"
```

Pytest-style paths with `::` delimiters are also accepted:

```sh
python3 -c "import agent_workflows.subtest_rows as r; r.run('tests/test_executed_transition_gate_e2e.py::MergeAwareInTreeEvidenceTests::test_merge_state_never_becomes_a_blanket_exemption')"
```

The helper sets strict mode (`AW_ROW_STRICT=1`) during the test run, restores the environment afterwards, and prints the per-row PASS/FAIL verdicts plus the overall enclosing test verdict.

## The Two-Idiom Hazard and Runner Behavior

In Python `unittest`, subtest outcomes are recorded via `addSubTest(test, subtest, outcome)`. When `outcome` is `None`, the subtest is marked PASS; when an exception is passed, it is marked FAIL. This repository runs tests under `pytest` without `pytest-subtests`, so `pytest` does not surface subtests as independent collected node IDs; passing subtests produce no output during ordinary suite runs, and only unhandled failures reach the test report.

This creates a serious hazard in append-only table tests:

If a test block appends failing cases to a `wrong` list inside `with self.subTest(case=case):` and defers all assertions to a single trailing `self.assertEqual(wrong, [])` after the loop, no exception is ever raised inside the subtest context. Consequently, `addSubTest` records every row as PASS, even for rows that failed. An executor running an `addSubTest`-based harness over an append-only test will receive all-PASS verdicts for a failing test.

## Trustworthy Row Verdicts

A row-level verdict is only trustworthy when the test fails inside the `with self.subTest(...)` context.

In this repository, table tests support opt-in strict mode:
1. Default mode (`AW_ROW_STRICT` unset or not `"1"`): Ordinary suite runs (`python3 -m pytest`) execute byte-identically to standard runs, preserving full aggregate diagnostic messages and the complete list of wrong rows without aborting on the first failure.
2. Strict mode (`AW_ROW_STRICT=1`): When enabled by `agent_workflows.subtest_rows`, failing rows call `self.fail(...)` inside the `subTest` context in addition to appending to `wrong`. This ensures `addSubTest` accurately records FAIL for defective rows while continuing the sweep for subsequent rows.

The `agent_workflows.subtest_rows` helper enforces two honesty checks:
- It reports the enclosing test's pass/fail status directly beside the row verdicts.
- If the enclosing test fails while zero subtest rows failed (the signature of the append-only hazard or a failure in `setUp` or aggregate assertion), the helper prints an explicit warning.
