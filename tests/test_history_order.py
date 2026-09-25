"""Tests for workflow history ordering and lifecycle transition validation (IPD 63h054).

Covers:
1. DerivationIsUnchangedTests: Whole-tree anti-regression guard verifying derive_plan_status
   output matches tests/fixtures/derive_plan_status_baseline.json.
2. HistoryOrderFixtureTests: Fixtures (a)-(e) validating newest-first, oldest-first, mixed,
   cross-day backward, and single-date tie history orders through both
   _plan_status_event_groups (when available) and check_lifecycle_transitions.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from agent_workflows import check_engine as ce
from agent_workflows import ipd_lifecycle as il


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _fixture_plan_text(id6: str, history_text: str, status: str = "approved") -> str:
    approval = (
        "- Approval: 2026-09-03, recorded via aw ipd set\n"
        if status == "approved"
        else ""
    )
    return (
        f"# IPD: Fixture {id6}\n\n"
        "- Date: 2026-09-01\n"
        "- Kind: child\n"
        "- Concern: history order fixture\n"
        "- Scope: history order fixture\n"
        "- Scope-Paths: agent_workflows/ipd_lifecycle.py\n"
        "- Item-Dependencies: none\n"
        f"- Status: {status}\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Highest E allocated: 01\n"
        "- Priority: medium\n"
        "- Work-Kind: chore\n"
        "- Author: fixture\n"
        f"- Id: {id6}\n"
        f"{approval}"
        "\n## Workflow history\n"
        f"{history_text}\n"
        "\n## Goal\n\nFixture goal.\n"
        "\n## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 execute.\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n"
        "\n## Project conventions discovered (Step 0)\n\n- none\n"
        "\n## Findings\n\n- none\n"
        "\n## Proposed changes (ordered, validatable)\n\n- none\n"
        "\n## Deferred / out of scope (with reason)\n\n- none\n"
        "\n## Scope check\n\n- none\n"
        "\n## Required tests / validation\n\n- none\n"
        "\n## Spec / documentation sync\n\n- none\n"
        "\n## Open questions\n\n- none\n"
        "\n## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: none\n"
        "  - Observed evidence: none\n"
        "  - Result: pending\n"
        "\n## Approval and execution gate\n\n- none\n"
    )


class DerivationIsUnchangedTests(unittest.TestCase):
    """Anti-regression guard for derive_plan_status across the whole tree."""

    def test_whole_tree_derivation_is_unchanged(self):
        root = _repo_root()
        baseline_file = root / "tests" / "fixtures" / "derive_plan_status_baseline.json"
        self.assertTrue(
            baseline_file.is_file(), f"Missing baseline fixture: {baseline_file}"
        )

        with open(baseline_file, "r", encoding="utf-8") as f:
            baseline = json.load(f)

        # TERMINAL DIRECTORIES ONLY. This guards the derive_plan_status ALGORITHM, so it must compare
        # against plans whose content is frozen. A `pending/` plan legitimately changes status
        # (reviewed -> approved) with no code change at all, which made this test fail on every
        # routine approval (measured 2026-09-25: five pending plans approved after the baseline was
        # captured). Terminal plans are frozen by contract (no commits to an executed plan).
        plan_paths = [
            p.relative_to(root).as_posix()
            for bucket in ("executed", "superseded", "not-executed")
            for p in sorted(root.glob(f".aw/records/plans/{bucket}/**/*.ipd.md"))
        ]
        intersection = sorted(set(plan_paths) & set(baseline.keys()))

        print(f"Compared {len(intersection)} paths")
        self.assertGreaterEqual(
            len(intersection),
            700,
            f"Compared {len(intersection)} paths; expected at least 700 paths in common",
        )

        mismatches = []
        for rel_path in intersection:
            abs_path = root / rel_path
            text = abs_path.read_text(encoding="utf-8")
            derived = il.derive_plan_status(text)
            expected = baseline[rel_path]
            if derived != expected:
                mismatches.append(f"{rel_path}: expected {expected!r}, got {derived!r}")

        self.assertEqual(
            mismatches,
            [],
            f"derive_plan_status changed on {len(mismatches)} plans:\n"
            + "\n".join(mismatches[:20]),
        )


class HistoryOrderFixtureTests(unittest.TestCase):
    """Five fixture tests (a)-(e) for lifecycle transition checking and history grouping."""

    def _run_check_on_plan(self, filename: str, content: str):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmproot = Path(tmpdir)
            pending_dir = tmproot / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            plan_file = pending_dir / filename
            plan_file.write_text(content, encoding="utf-8")
            return ce.check_lifecycle_transitions(tmproot, include_untracked=True)

    def test_fixture_a_newest_first(self):
        """(a) NEWEST-FIRST -> oldest-first draft, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-03 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-01 draft (agent): ok"
        )
        content = _fixture_plan_text("fix01a", history, status="approved")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01a-01-fix01a-newest-first.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_b_oldest_first(self):
        """(b) OLDEST-FIRST -> oldest-first draft, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-01 draft (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "- 2026-09-03 approved (agent): ok"
        )
        content = _fixture_plan_text("fix01b", history, status="approved")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01b-01-fix01b-oldest-first.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_c_mixed_blocks(self):
        """(c) MIXED -> draft, to-review, reviewed, approved (0 findings)."""
        history = (
            "- 2026-09-03 approved (agent): ok\n"
            "- 2026-09-02 reviewed (agent): ok\n"
            "\n"
            "- 2026-08-30 draft (agent): ok\n"
            "- 2026-09-01 to-review (agent): ok"
        )
        content = _fixture_plan_text("fix01c", history, status="approved")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-08-30", [("draft", "agent")], True),
                    ("2026-09-01", [("to-review", "agent")], True),
                    ("2026-09-02", [("reviewed", "agent")], True),
                    ("2026-09-03", [("approved", "agent")], True),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01c-01-fix01c-mixed.ipd.md", content
        )
        self.assertEqual(drift, [])

    def test_fixture_d_negative_cross_day_backwards(self):
        """(d) Cross-day approved then draft -> exactly 1 finding naming 'approved' -> 'draft'."""
        history = (
            "- 2026-09-01 draft (agent): ok\n"
            "- 2026-09-02 approved (agent): ok\n"
            "- 2026-09-03 draft (agent): ok"
        )
        content = _fixture_plan_text("fix01d", history, status="draft")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent")], True),
                    ("2026-09-02", [("approved", "agent")], True),
                    ("2026-09-03", [("draft", "agent")], True),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01d-01-fix01d-cross-day.ipd.md", content
        )
        self.assertEqual(len(drift), 1)
        self.assertIn("'approved' -> 'draft'", drift[0].detail)

    def test_fixture_e_discriminating_single_date_tie(self):
        """(e) Single-date draft above approved in one block -> 0 findings (unordered)."""
        history = "- 2026-09-01 draft (agent): ok\n" "- 2026-09-01 approved (agent): ok"
        content = _fixture_plan_text("fix01e", history, status="approved")

        if hasattr(il, "_plan_status_event_groups"):
            groups = il._plan_status_event_groups(content)
            self.assertEqual(
                groups,
                [
                    ("2026-09-01", [("draft", "agent"), ("approved", "agent")], False),
                ],
            )

        drift = self._run_check_on_plan(
            "20260901-fix01e-01-fix01e-single-date.ipd.md", content
        )
        self.assertEqual(drift, [])


if __name__ == "__main__":
    unittest.main()
