"""Subtest row-level test verdict runner and honesty reporter.

Exposes an importable helper that runs one or more named test methods and
prints plus returns per-row subTest verdicts alongside the enclosing test's
own verdict.

Owns enabling AW_ROW_STRICT=1 during execution and restoring it afterwards.
Guarantees three honesty requirements:
1. Reports enclosing test pass/fail beside row verdicts.
2. Explicitly warns if enclosing test failed with zero failing rows (append-only hazard or failure outside loop).
3. Strictly scoped: does not interfere with normal pytest runs.
"""

from __future__ import annotations

import io
import os
import sys
import unittest
from typing import Any


class SubTestRowResult(unittest.TextTestResult):
    """Test result class recording addSubTest outcomes and test-level failures."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.subtest_records: dict[str, list[dict[str, Any]]] = {}
        self.enclosing_failures: set[str] = set()
        self.current_test_id: str | None = None

    def startTest(self, test: unittest.TestCase) -> None:
        super().startTest(test)
        self.current_test_id = test.id()
        if self.current_test_id not in self.subtest_records:
            self.subtest_records[self.current_test_id] = []

    def addSubTest(
        self,
        test: unittest.TestCase,
        subtest: unittest.TestCase,
        outcome: Any,
    ) -> None:
        super().addSubTest(test, subtest, outcome)
        test_id = test.id()
        if test_id not in self.subtest_records:
            self.subtest_records[test_id] = []
        status = "FAIL" if outcome is not None else "PASS"
        params = (
            dict(subtest.params)
            if hasattr(subtest, "params") and subtest.params
            else {}
        )
        desc = (
            subtest._subDescription()
            if hasattr(subtest, "_subDescription")
            else str(params)
        )
        self.subtest_records[test_id].append(
            {
                "params": params,
                "description": desc,
                "status": status,
            }
        )

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        super().addFailure(test, err)
        if not isinstance(test, getattr(unittest.case, "_SubTest", ())):
            self.enclosing_failures.add(test.id())

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        super().addError(test, err)
        if not isinstance(test, getattr(unittest.case, "_SubTest", ())):
            self.enclosing_failures.add(test.id())


def normalize_test_name(name: str) -> str:
    """Normalize pytest-style paths (e.g. path/to/test.py::Class::method) to dotted python path."""
    if "::" in name:
        name = name.replace(".py", "").replace("/", ".").replace("::", ".")
    elif name.endswith(".py"):
        name = name[:-3].replace("/", ".")
    return name


def run_tests(*test_names: str, stream: Any = None) -> list[dict[str, Any]]:
    """Run one or more named test methods and print plus return row-level verdicts.

    Enforces strict mode (AW_ROW_STRICT=1) during test execution, restoring prior
    environment state on exit.
    """
    if stream is None:
        stream = sys.stdout

    # Flatten if a list/tuple was passed as the first argument
    if len(test_names) == 1 and isinstance(test_names[0], (list, tuple)):
        test_names = tuple(test_names[0])

    if not test_names:
        print("[subtest-rows] No test names specified.", file=stream)
        return []

    orig_strict = os.environ.get("AW_ROW_STRICT")
    os.environ["AW_ROW_STRICT"] = "1"
    print("[subtest-rows] strict mode: active (AW_ROW_STRICT=1)", file=stream)

    try:
        normalized_names = [normalize_test_name(n) for n in test_names]
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for name in normalized_names:
            suite.addTests(loader.loadTestsFromName(name))

        all_tests = _flatten_suite(suite)
        null_stream = io.StringIO()
        result = SubTestRowResult(stream=null_stream, descriptions=True, verbosity=0)
        suite.run(result)

        outcomes: list[dict[str, Any]] = []
        for test in all_tests:
            test_id = test.id()
            rows = result.subtest_records.get(test_id, [])
            has_subtest_fail = any(r["status"] == "FAIL" for r in rows)
            has_enclosing_fail = test_id in result.enclosing_failures
            test_failed = has_subtest_fail or has_enclosing_fail

            verdict = "FAILED" if test_failed else "PASSED"
            failed_without_subtest = test_failed and not has_subtest_fail

            print(f"{test_id}:", file=stream)
            for r in rows:
                print(f"  subtest {r['description']}: {r['status']}", file=stream)

            pass_count = sum(1 for r in rows if r["status"] == "PASS")
            fail_count = sum(1 for r in rows if r["status"] == "FAIL")
            print(
                f"enclosing test: {verdict} ({len(rows)} subtests: {pass_count} passed, {fail_count} failed)",
                file=stream,
            )

            if failed_without_subtest:
                print(
                    "WARNING: enclosing test FAILED but no subtest row was recorded as failing "
                    "(failure occurred outside subtest context or test uses append-only pattern without in-context failure)",
                    file=stream,
                )

            outcomes.append(
                {
                    "test": test_id,
                    "enclosing_verdict": verdict,
                    "subtests": rows,
                    "failed_without_failing_subtest": failed_without_subtest,
                }
            )

        return outcomes
    finally:
        if orig_strict is None:
            os.environ.pop("AW_ROW_STRICT", None)
        else:
            os.environ["AW_ROW_STRICT"] = orig_strict


def _flatten_suite(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    cases = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            cases.extend(_flatten_suite(item))
        elif isinstance(item, unittest.TestCase):
            cases.append(item)
    return cases


# Alias for concise invocation
run = run_tests

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_tests(*sys.argv[1:])
    else:
        print(
            "Usage: python3 -m agent_workflows.subtest_rows <test_name>...",
            file=sys.stderr,
        )
        sys.exit(1)
