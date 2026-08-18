"""Parity tests for the IPD templates (Set ipd-structure, Order 04).

The child and orchestrator templates are the single-source-of-truth `build_skeleton` output, so they
cannot drift from the schema. These tests assert byte-parity with the generator AND that each
template lints `conforming` at the author checkpoint, and that the templates + ipd-spec are free of
the retired "near the top/end" placement language and the F-08 transition-as-checklist-item defect.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from tests.support import SOURCE_WORKFLOWS, SOURCE_DOCS

TEMPLATES = SOURCE_WORKFLOWS / "assess" / "templates"
CHILD = TEMPLATES / "ipd.md"
ORCH = TEMPLATES / "orchestrator-ipd.md"
IPD_SPEC = SOURCE_DOCS / "specs" / "20260726-1340-01-ipd-spec.spec.md"

CHILD_TITLE = "<short title of the change>"
ORCH_TITLE = "<short title of the coordinated change>"
AUTHOR = "<agent/model>"
WHEN = "<YYYY-MM-DD>"
# A fixed, valid id6 placeholder so the templates are deterministic AND lint conforming; a real
# scaffold generates a fresh id per plan (plans-adopter Order 02).
TEMPLATE_ID = "tmp1d6"


class TemplateParityTests(unittest.TestCase):
    def test_child_template_matches_generator(self):
        expected = A.build_skeleton(
            kind="child",
            title=CHILD_TITLE,
            author=AUTHOR,
            when=WHEN,
            set_name=None,
            order=None,
            plan_id=TEMPLATE_ID,
        )
        self.assertEqual(
            CHILD.read_text(encoding="utf-8"),
            expected,
            "child template drifted from build_skeleton; regenerate it",
        )

    def test_orchestrator_template_matches_generator(self):
        expected = A.build_skeleton(
            kind="orchestrator",
            title=ORCH_TITLE,
            author=AUTHOR,
            when=WHEN,
            set_name="<set-id>",
            order=0,
            plan_id=TEMPLATE_ID,
        )
        self.assertEqual(
            ORCH.read_text(encoding="utf-8"),
            expected,
            "orchestrator template drifted from build_skeleton; regenerate it",
        )


class TemplateLintTests(unittest.TestCase):
    def test_child_template_conforms_at_author(self):
        res = L.lint_text(
            CHILD.read_text(encoding="utf-8"), checkpoint="author", directory="pending"
        )
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_orchestrator_template_conforms_at_author(self):
        res = L.lint_text(
            ORCH.read_text(encoding="utf-8"), checkpoint="author", directory="pending"
        )
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )


class TemplateStructureTests(unittest.TestCase):
    def _h2(self, path: Path):
        return [
            line[3:].strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")
        ]

    def test_child_h2_matches_schema_order(self):
        self.assertEqual(self._h2(CHILD), list(S.CHILD_H2_ORDER))

    def test_orchestrator_h2_matches_schema_order(self):
        self.assertEqual(self._h2(ORCH), list(S.ORCHESTRATOR_H2_ORDER))

    def test_execution_immediately_after_goal_in_both(self):
        for path in (CHILD, ORCH):
            h2 = self._h2(path)
            self.assertEqual(h2[h2.index(S.H_GOAL) + 1], S.H_EXECUTION)

    def test_no_transition_as_checklist_item(self):
        # F-08: the exec checklist must not contain a lifecycle transition item ("git mv ... plan").
        for path in (CHILD, ORCH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("git mv this plan", text)
            self.assertNotIn("Set terminal `Status:` and `git mv`", text)


class SpecCleanlinessTests(unittest.TestCase):
    def test_ipd_spec_has_no_relational_placement_language(self):
        text = IPD_SPEC.read_text(encoding="utf-8")
        # The only allowed occurrence is the explicit negation stating placement is exact.
        for bad in ("placed near the BEGINNING", "placed near the END"):
            self.assertNotIn(bad, text)

    def test_ipd_spec_points_at_schema(self):
        text = IPD_SPEC.read_text(encoding="utf-8")
        self.assertIn("agent_workflows/ipd_schema.py", text)


if __name__ == "__main__":
    unittest.main()
