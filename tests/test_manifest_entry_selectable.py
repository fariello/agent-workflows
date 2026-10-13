"""Behavioral regression tests for manifest_entry_is_selectable.

Covers:
- Predicate table: preserves executed and status-less entries while refusing
  retired plans (by status or directory disagreement).
- End-to-end queue selection: both hosts (oc and agy) retain executed entries
  and keep dependents queued while dropping superseded entries from the queue.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.test_typed_queue_entries import (
    _build_queue_for_selector,
    _make_test_repo,
    _write_plan,
)

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))

TABLE_CASES: tuple[tuple[str, Mapping[str, Any] | None, bool], ...] = (
    (
        "executed status in executed directory",
        {"status": "executed", "file": ".aw/records/plans/executed/x.ipd.md"},
        True,
    ),
    (
        "status-less entry",
        {"file": "x.ipd.md"},
        True,
    ),
    (
        "approved status in pending directory",
        {"status": "approved", "file": ".aw/records/plans/pending/x.ipd.md"},
        True,
    ),
    (
        "superseded status without file",
        {"status": "superseded"},
        False,
    ),
    (
        "not-executed status without file",
        {"status": "not-executed"},
        False,
    ),
    (
        "approved status in superseded directory (directory disagreement)",
        {"status": "approved", "file": ".aw/records/plans/superseded/x.ipd.md"},
        False,
    ),
    (
        "approved status in not-executed directory (directory disagreement)",
        {"status": "approved", "file": ".aw/records/plans/not-executed/x.ipd.md"},
        False,
    ),
    (
        "uppercase and whitespace superseded status",
        {"status": " Superseded "},
        False,
    ),
    (
        "None entry",
        None,
        False,
    ),
    (
        "empty entry dict",
        {},
        False,
    ),
)


class TestManifestEntrySelectable(unittest.TestCase):
    """Behavioral tests for runner_shared.manifest_entry_is_selectable."""

    def test_manifest_entry_is_selectable_table(self):
        """Predicate table: executed and status-less admitted, retired refused."""
        for desc, entry, expected in TABLE_CASES:
            with self.subTest(case=desc, entry=entry):
                actual = runner_shared.manifest_entry_is_selectable(entry)
                self.assertEqual(
                    actual,
                    expected,
                    f"case {desc!r} for entry {entry!r} expected {expected} but got {actual}",
                )

    def test_end_to_end_queue_selection_preserves_executed_plans(self):
        """End-to-end queue selection on both hosts preserves executed, drops superseded."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            (repo / ".gitignore").write_text(".aw/records/runs/\n", encoding="utf-8")
            _write_plan(
                repo,
                id6="aaaaaa",
                setid="demo",
                order=1,
                status="executed",
                slug="first",
            )
            _write_plan(
                repo,
                id6="bbbbbb",
                setid="demo",
                order=2,
                status="approved",
                slug="second",
                dependencies=["executed:aaaaaa"],
            )
            _write_plan(
                repo,
                id6="cccccc",
                setid="demo",
                order=3,
                status="superseded",
                slug="third",
            )

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)

            for driver_name, mod in _DRIVERS:
                with self.subTest(driver=driver_name):
                    data = _build_queue_for_selector(mod, repo, "demo")
                    queue = data.get("queue", [])
                    queue_by_id = {item["id6"]: item["status"] for item in queue}

                    # Executed plan is present with status == "executed"
                    self.assertEqual(
                        queue_by_id["aaaaaa"],
                        "executed",
                        f"{driver_name} must retain executed status for executed plan",
                    )

                    # Dependent plan is queued
                    self.assertEqual(
                        queue_by_id["bbbbbb"],
                        "queued",
                        f"{driver_name} dependent plan must stay queued",
                    )

                    # Dependent plan is absent from cascade_dependency_blocked(state)
                    blocked = runner_shared.cascade_dependency_blocked(data)
                    blocked_ids = [
                        b["id6"] if isinstance(b, dict) else b for b in blocked
                    ]
                    self.assertNotIn(
                        "bbbbbb",
                        blocked_ids,
                        f"{driver_name} dependent plan must not be marked dependency-blocked",
                    )

                    # Superseded plan is absent
                    self.assertNotIn(
                        "cccccc",
                        queue_by_id,
                        "'cccccc' unexpectedly found",
                    )


if __name__ == "__main__":
    unittest.main()
