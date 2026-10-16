"""Restored behavioral outcome coverage for selector precedence.

This module guards the frozen selector precedence in ``agent_workflows.selectors``:
specifically that ``setid`` and ``status`` rules outrank filename ``stem`` and
``substring`` rules when resolving query tokens against record collections.

When a query token is simultaneously a declared metadata field (such as a Set id
or Status) and a fragment of a record's filename, the earlier metadata rule in the
precedence order must win.

This restores behavioral coverage for the gap classified as site S-26 in plan
``ev7t1w`` (RETIRE-UNGUARDED), following the removal of
``tests/test_selector_zero_open.py`` in commit ``19313eed``.

In compliance with GUIDING_PRINCIPLES P16 and AGENTS.md ("TEST OUTCOMES, NOT CODE
STRUCTURE"), these tests call ``selectors.resolve`` against fixture records in
temporary repositories and assert strictly on the returned ``Resolution.kind`` and
``Resolution.paths``. They contain no inspection of AST, source text, line counts,
or internal precedence data structures.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import selectors


class SelectorPrecedenceOutcomesTests(unittest.TestCase):
    """Behavioral outcome tests for selector precedence rules."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory(prefix="aw_test_precedence_")
        self.repo_root = Path(self.tmpdir.name).resolve()
        self.pend = self.repo_root / ".aw" / "records" / "plans" / "pending"
        self.pend.mkdir(parents=True, exist_ok=True)

        # Several plans declaring `- Set: demo`
        self.demo_plan_1 = self.pend / "20260101-demo-01-aa0001-first-demo-plan.ipd.md"
        self.demo_plan_1.write_text(
            "# Plan 1\n\n- Id: aa0001\n- Status: draft\n- Set: demo\n\n## Goal\nDemo 1\n",
            encoding="utf-8",
        )
        self.demo_plan_2 = self.pend / "20260101-demo-02-aa0002-second-demo-plan.ipd.md"
        self.demo_plan_2.write_text(
            "# Plan 2\n\n- Id: aa0002\n- Status: draft\n- Set: demo\n\n## Goal\nDemo 2\n",
            encoding="utf-8",
        )
        self.demo_plan_3 = self.pend / "20260101-demo-03-aa0003-third-demo-plan.ipd.md"
        self.demo_plan_3.write_text(
            "# Plan 3\n\n- Id: aa0003\n- Status: approved\n- Set: demo\n\n## Goal\nDemo 3\n",
            encoding="utf-8",
        )
        self.demo_plans = [self.demo_plan_1, self.demo_plan_2, self.demo_plan_3]

        # Colliding plan declaring `- Set: other` whose FILENAME contains `demo`
        self.setid_collide_plan = (
            self.pend / "20260101-other-01-dd0001-demo-colliding-plan.ipd.md"
        )
        self.setid_collide_plan.write_text(
            "# Set Collision Plan\n\n- Id: dd0001\n- Status: draft\n- Set: other\n\n## Goal\nCollide setid\n",
            encoding="utf-8",
        )

        # Colliding plan declaring `- Set: other` and `- Status: draft` whose FILENAME contains `approved`
        self.status_collide_plan = (
            self.pend / "20260101-other-02-dd0002-approved-naming-check.ipd.md"
        )
        self.status_collide_plan.write_text(
            "# Status Collision Plan\n\n- Id: dd0002\n- Status: draft\n- Set: other\n\n## Goal\nCollide status\n",
            encoding="utf-8",
        )

        # Non-colliding plan with a distinct substring token not present in any front matter
        self.fallthrough_plan = (
            self.pend / "20260101-other-03-dd0003-unique-substring-fallback.ipd.md"
        )
        self.fallthrough_plan.write_text(
            "# Fallthrough Plan\n\n- Id: dd0003\n- Status: draft\n- Set: other\n\n## Goal\nFallthrough substring\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_setid_outranks_filename_substring_on_collision(self) -> None:
        """A token matching both Set ID and filename substring resolves as MATCH_SETID."""
        got = selectors.resolve(self.repo_root, "plans", "demo")
        self.assertEqual(got.kind, selectors.MATCH_SETID)
        resolved_paths = [p.resolve() for p in got.paths]
        for plan_path in self.demo_plans:
            self.assertIn(plan_path.resolve(), resolved_paths)
        self.assertNotIn(self.setid_collide_plan.resolve(), resolved_paths)
        self.assertEqual(len(resolved_paths), len(self.demo_plans))

    def test_status_outranks_filename_substring_on_collision(self) -> None:
        """A token matching both Status and filename substring resolves as MATCH_STATUS."""
        got = selectors.resolve(self.repo_root, "plans", "approved")
        self.assertEqual(got.kind, selectors.MATCH_STATUS)
        resolved_paths = [p.resolve() for p in got.paths]
        self.assertIn(self.demo_plan_3.resolve(), resolved_paths)
        self.assertNotIn(self.status_collide_plan.resolve(), resolved_paths)

    def test_filename_substring_resolves_when_earlier_rules_do_not_match(self) -> None:
        """A token matching only filename substring resolves as MATCH_SUBSTRING to that file."""
        got = selectors.resolve(self.repo_root, "plans", "unique-substring-fallback")
        self.assertEqual(got.kind, selectors.MATCH_SUBSTRING)
        self.assertEqual(
            [p.resolve() for p in got.paths], [self.fallthrough_plan.resolve()]
        )


if __name__ == "__main__":
    unittest.main()
