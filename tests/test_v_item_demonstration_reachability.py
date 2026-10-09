"""Tests for the V-item demonstration reachability rule (IPD 9aprci, set vreach; IPD ua133b, set l07ohc).

Exemption from source-text-pin prohibition (GUIDING_PRINCIPLES P16):
The two review-surface tests (test_single_file_plan_review_reachability_rule and
test_long_form_review_rubric_reachability_rule_parity) read WORKFLOW BODY markdown and
no agent_workflows/*.py, so they sit inside GUIDING_PRINCIPLES P16's stated narrow
exception ('Content verification is permissible only where the text or file itself is
the artifact under test') and outside its 'No production source inspection' prohibition,
whose enumerated targets are all production code. This follows the precedent of
tests/test_plan_review_feasibility_rule.py.

The scaffolded intro test (test_scaffolded_validation_intro_carries_reachability_rule)
reads no files: it drives ipd_authoring.build_skeleton behaviorally and asserts on the
returned document, which is an observable outcome requiring no P16 exemption.

Non-applicability of pending plan 76ic0k guard:
The pending author-time guard in plan 76ic0k does NOT flag this module: the guard
flags six attribute-call forms (inspect.getsource, inspect.getsourcelines,
inspect.getsourcefile, ast.parse, ast.walk, ast.unparse) and deliberately does NOT
flag read_text(), and its scope is a production-source read, which this module does
not perform.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_schema as S
from tests import support

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".aw" / "system" / "workflows"
PLAN_REVIEW_FILE = WORKFLOWS_DIR / "plan-review" / "plan-review.md"
REVIEW_RUBRIC_FILE = WORKFLOWS_DIR / "plan-review-long" / "review-rubric.md"

# Distinctive semantic anchors covering the three load-bearing elements of the reachability rule:
# 1. The runtime-demonstration scope:
#    "Runtime-demonstration reachability"
# 2. The reviewer's obligation to name the producing code path or sibling E-item:
#    "name the code path"
# 3. The under-scope disposition when neither exists:
#    "UNDER-SCOPE"
REACHABILITY_ANCHOR_PHRASES = [
    "Runtime-demonstration reachability",
    "name the code path",
    "UNDER-SCOPE",
]


class TestVItemDemonstrationReachability(unittest.TestCase):
    def test_single_file_plan_review_reachability_rule(self) -> None:
        """Assert single-file plan-review.md carries the reachability rule in rubric G."""
        content = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
        section_g = support.section(content, "### G. Plan executability", "## ")

        for phrase in REACHABILITY_ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                section_g,
                f"Anchor phrase '{phrase}' not found in section G of {PLAN_REVIEW_FILE}",
            )

    def test_long_form_review_rubric_reachability_rule_parity(self) -> None:
        """Assert long-form review-rubric.md carries the reachability rule in section A.

        Notice: the two rubric surfaces do NOT share section letters. plan-review.md
        carries Plan executability in '### G.', whereas in review-rubric.md '## G.' is
        'UX and accessibility' and its plan-executability content lives in
        '## A. Plan completeness'. Slicing on '## G.' would erroneously assert against
        accessibility text; we specifically slice on '## A. Plan completeness'.
        """
        content = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
        section_a = support.section(content, "## A. Plan completeness", "## ")

        for phrase in REACHABILITY_ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                section_a,
                f"Anchor phrase '{phrase}' not found in section A of {REVIEW_RUBRIC_FILE}",
            )

    def test_scaffolded_validation_intro_carries_reachability_rule(self) -> None:
        """Assert the scaffolded validation intro of both kinds carries the reachability rule."""
        for kind, heading in (
            ("child", S.H_VALIDATION_CHILD),
            ("orchestrator", S.H_VALIDATION_ORCH),
        ):
            text = A.build_skeleton(
                kind=kind,
                title=f"Reachability Scaffold Test {kind}",
                author="tester",
                when="2026-10-01",
                set_name="reachprobe",
                order=1 if kind == "child" else 0,
                plan_id="rch123",
            )
            lines = text.splitlines()
            valid_intro = None
            for i, line in enumerate(lines):
                if line.startswith("## ") and line[3:].strip() == heading:
                    for candidate in lines[i + 1 : i + 5]:
                        if candidate.startswith("Validation-state rule:"):
                            valid_intro = candidate
                            break
                    break

            self.assertIsNotNone(
                valid_intro,
                f"missing validation intro in {kind} scaffold",
            )
            for phrase in REACHABILITY_ANCHOR_PHRASES:
                self.assertIn(
                    phrase,
                    valid_intro,
                    f"Anchor phrase '{phrase}' not found in validation intro of {kind} scaffold",
                )


if __name__ == "__main__":
    unittest.main()
