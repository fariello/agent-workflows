"""Tests for the V-item demonstration reachability rule (IPD 9aprci, set vreach).

Exemption from source-text-pin prohibition (GUIDING_PRINCIPLES P16):
This module reads WORKFLOW BODY markdown and no agent_workflows/*.py, so it sits
inside GUIDING_PRINCIPLES P16's stated narrow exception ('Content verification is
permissible only where the text or file itself is the artifact under test') and
outside its 'No production source inspection' prohibition, whose enumerated targets
are all production code. This follows the precedent of
tests/test_plan_review_feasibility_rule.py, whose docstring records the same
exemption for the same pair of files.

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

        start_heading = "### G. Plan executability"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx, -1, f"Missing heading '{start_heading}' in {PLAN_REVIEW_FILE}"
        )

        next_heading = "\n## "
        end_idx = content.find(next_heading, start_idx)
        section_g = content[start_idx:end_idx] if end_idx != -1 else content[start_idx:]

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

        start_heading = "## A. Plan completeness"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx, -1, f"Missing heading '{start_heading}' in {REVIEW_RUBRIC_FILE}"
        )

        next_heading = "\n## "
        end_idx = content.find(next_heading, start_idx + len(start_heading))
        section_a = content[start_idx:end_idx] if end_idx != -1 else content[start_idx:]

        for phrase in REACHABILITY_ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                section_a,
                f"Anchor phrase '{phrase}' not found in section A of {REVIEW_RUBRIC_FILE}",
            )


if __name__ == "__main__":
    unittest.main()
