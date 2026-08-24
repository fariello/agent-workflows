"""Tests for agent_workflows.check_engine (awcheck Order 01): the unified check engine core."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce


class CheckEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        # a well-named plan and a badly-named one
        (self.plans / "20260101-demo-01-aaa111-ok.ipd.md").write_text(
            "# IPD: ok\n\n- Id: aaa111\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        (self.plans / "not-a-grammar.md").write_text(
            "# IPD: bad\n\n- Id: bbb222\n- Status: draft\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        # a malformed spec (missing Status)
        specs = self.root / ".aw" / "records" / "specs"
        specs.mkdir(parents=True)
        (specs / "20260101-1200-01-x.spec.md").write_text(
            "# Spec: x\n\n- Author: t\n\n## Body\n\nno status here\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_check_names_flags_bad_name(self) -> None:
        drift = ce.check_names(self.root, "plans")
        rules = [d.rule for d in drift]
        self.assertIn("check.name-nonconformant", rules)
        # only the bad file
        self.assertTrue(all("not-a-grammar.md" in d.location for d in drift))

    def test_check_content_surfaces_malformed_spec(self) -> None:
        drift = ce.check_content(self.root, "specs")
        self.assertTrue(len(drift) >= 1)

    def test_no_content_validator_returns_empty(self) -> None:
        self.assertEqual(ce.check_content(self.root, "prompts"), [])

    def test_check_type_names_only(self) -> None:
        drift = ce.check_type(self.root, "plans", names_only=True)
        self.assertTrue(all(d.rule == "check.name-nonconformant" for d in drift))

    def test_check_types_all_runs(self) -> None:
        drift = ce.check_types(self.root, ["all"])
        self.assertIsInstance(drift, list)

    def test_unsupported_single_type(self) -> None:
        drift = ce.check_type(self.root, "bogus")
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0].rule, "check.type-unsupported")

    def test_check_refs_seam_empty(self) -> None:
        self.assertEqual(ce.check_refs(self.root, "plans"), [])


class CollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.specs = self.root / ".aw" / "records" / "specs"
        self.specs.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _plan(self, name, id6, setid="demo", desc=None):
        setline = f"{setid} ({desc})" if desc else setid
        (self.plans / name).write_text(
            f"# IPD\n\n- Id: {id6}\n- Status: approved\n- Set: {setline}\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )

    def _spec(self, name, id6, setid="demo", desc=None):
        setline = f"{setid} ({desc})" if desc else setid
        (self.specs / name).write_text(
            f"# Spec\n\n- Id: {id6}\n- Status: draft\n- Set: {setline}\n\n## Body\n\nx\n",
            encoding="utf-8",
        )

    def test_id6_collision(self) -> None:
        self._plan("20260101-demo-01-dup111-a.ipd.md", "dup111")
        self._spec("20260101-demo-01-dup111-b.spec.md", "dup111")
        drift = ce.check_collisions(self.root)
        self.assertEqual(len([d for d in drift if d.rule == "check.id6-collision"]), 1)

    def test_no_collision_clean(self) -> None:
        self._plan("20260101-demo-01-aaa111-a.ipd.md", "aaa111", desc="Demo")
        self._spec("20260101-demo-01-bbb222-b.spec.md", "bbb222", setid="other")
        drift = ce.check_collisions(self.root)
        self.assertEqual([d for d in drift if d.rule.startswith("check.")], [])

    def test_setid_collision(self) -> None:
        self._plan(
            "20260101-demo-01-aaa111-a.ipd.md", "aaa111", setid="demo", desc="Alpha"
        )
        self._plan(
            "20260101-demo-02-bbb222-b.ipd.md", "bbb222", setid="demo", desc="Beta"
        )
        drift = ce.check_collisions(self.root)
        self.assertTrue(any(d.rule == "check.setid-collision" for d in drift))

    def test_all_runs_collisions_once(self) -> None:
        self._plan("20260101-demo-01-dup111-a.ipd.md", "dup111")
        self._spec("20260101-demo-01-dup111-b.spec.md", "dup111")
        drift = ce.check_types(self.root, ["all"])
        self.assertEqual(len([d for d in drift if d.rule == "check.id6-collision"]), 1)


class IdentitySlotTests(unittest.TestCase):
    """Filename identity-slot id6 invariant (DECISIONS.md D140), IPD 9a655p E-01/V-01."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.walk = self.root / ".aw" / "records" / "walkthroughs"
        self.walk.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _slots(self, drift):
        return [d for d in drift if d.rule == "check.id6-identity-slot"]

    def test_rule_a_declared_id_differs_from_slot(self) -> None:
        # A file that DECLARES an Id different from its filename slot id6 is flagged (rule a).
        (self.plans / "20260101-demo-01-slotaa-a.ipd.md").write_text(
            "# IPD\n\n- Id: fmbbb1\n- Status: draft\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        flagged = self._slots(ce.check_collisions(self.root))
        self.assertEqual(len(flagged), 1, flagged)
        self.assertIn("slotaa", flagged[0].detail)
        self.assertIn("fmbbb1", flagged[0].detail)

    def test_rule_b_reuse_of_another_files_identity(self) -> None:
        # The p7dqwz case: a walkthrough with NO declared Id whose slot id6 is a PLAN's identity.
        (self.plans / "20260101-demo-01-abc123-plan.ipd.md").write_text(
            "# IPD\n\n- Id: abc123\n- Status: draft\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        (self.walk / "20260101-demo-01-abc123-execution.walkthrough.md").write_text(
            "# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n",
            encoding="utf-8",
        )
        flagged = self._slots(ce.check_collisions(self.root))
        self.assertEqual(len(flagged), 1, flagged)
        # Names BOTH the offending walkthrough and the plan that owns abc123.
        self.assertIn("execution.walkthrough.md", flagged[0].location)
        self.assertIn("abc123", flagged[0].detail)
        self.assertIn("plan.ipd.md", flagged[0].detail)

    def test_conformant_declared_matching_slot_is_clean(self) -> None:
        # A file whose declared Id EQUALS its slot id6 is fine (no flag).
        (self.plans / "20260101-demo-01-abc123-ok.ipd.md").write_text(
            "# IPD\n\n- Id: abc123\n- Status: draft\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        (self.walk / "20260101-demo-01-def456-own.walkthrough.md").write_text(
            "# Walkthrough\n\n- Date: 20260101\n- Id: def456\n\n## Summary\n\nx\n",
            encoding="utf-8",
        )
        self.assertEqual(self._slots(ce.check_collisions(self.root)), [])

    def test_legacy_hhmm_slug_word_not_flagged(self) -> None:
        # Legacy YYYYMMDD-HHMM-NN-<slug> names (no id6 slot; the 4-digit HHMM matches the setid
        # segment and the slug's first word matches [0-9a-z]{6}) must NOT be mass-flagged.
        (self.plans / "20260101-1357-01-assess-bugs.ipd.md").write_text(
            "# IPD\n\n- Id: wvlk84\n- Status: draft\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        (
            self.walk / "20260101-1033-01-assess-bugs-and-tests.walkthrough.md"
        ).write_text(
            "# Walkthrough\n\n- Date: 20260101\n\n## Summary\n\nx\n",
            encoding="utf-8",
        )
        self.assertEqual(self._slots(ce.check_collisions(self.root)), [])

    def test_all_clean_tree_no_slot_findings(self) -> None:
        (self.plans / "20260101-demo-01-abc123-a.ipd.md").write_text(
            "# IPD\n\n- Id: abc123\n- Status: draft\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        drift = ce.check_types(self.root, ["all"])
        self.assertEqual(self._slots(drift), [])


class LegacyNamesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_legacy_flag_allows_legacy_name(self) -> None:
        # hyphenated-date legacy form: fails is_conformant but parse_name recognizes it.
        (self.plans / "2026-01-01-old-hyphenated.md").write_text(
            "# IPD\n\n- Id: aaa111\n- Status: draft\n\n## Goal\n\nx\n", encoding="utf-8"
        )
        flagged = [
            d
            for d in ce.check_names(self.root, "plans")
            if d.rule == "check.name-nonconformant"
        ]
        self.assertEqual(len(flagged), 1)  # flagged WITHOUT legacy
        self.assertEqual(
            ce.check_names(self.root, "plans", legacy=True), []
        )  # allowed WITH legacy

    def test_current_name_ok(self) -> None:
        (self.plans / "20260101-demo-01-aaa111-ok.ipd.md").write_text(
            "# IPD\n\n- Id: aaa111\n- Status: draft\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        self.assertEqual(ce.check_names(self.root, "plans"), [])


if __name__ == "__main__":
    unittest.main()
