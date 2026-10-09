"""Tests for V-item evidence durability and parity rules (IPD vtup6x, set nos070; IPD 5q9a6a, set ezv744).

Exemption from source-text-pin prohibition:
This module reads WORKFLOW BODIES and a SPEC, the artifacts under change, and no
agent_workflows/* source, so it sits inside GUIDING_PRINCIPLES P16's stated narrow
exception ("Content verification is permissible only where the text or file itself is
the artifact under test") and outside its "No production source inspection" prohibition
(whose enumerated targets are all agent_workflows/*.py). Follows the precedent of
tests/test_plan_review_feasibility_rule.py.

This module owns the Section 5.4 surface in the spec ipd-structure-and-linting (established
by vtup6x alongside the durability amendment). Sibling module
tests/test_v_item_demonstration_reachability.py owns the rule's presence across the two
workflow review bodies. Pinning by surface keeps one test module per file-under-contract.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from tests import support

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".aw" / "system" / "workflows"
PLAN_REVIEW_FILE = WORKFLOWS_DIR / "plan-review" / "plan-review.md"
REVIEW_RUBRIC_FILE = WORKFLOWS_DIR / "plan-review-long" / "review-rubric.md"
SPEC_FILE = (
    REPO_ROOT
    / ".aw"
    / "records"
    / "specs"
    / "implemented"
    / "20260802-1904-01-ipd-structure-and-linting.spec.md"
)

PLAN_REVIEW_REL = ".aw/system/workflows/plan-review/plan-review.md"
REVIEW_RUBRIC_REL = ".aw/system/workflows/plan-review-long/review-rubric.md"
SPEC_REL = (
    ".aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md"
)

# Semantic anchors for spec Section 5.4 reachability rule:
SPEC_SECTION_5_4_REACHABILITY_ANCHORS = [
    "runtime-demonstration reachability",
    "name the code path",
    "UNDER-SCOPE",
    "convention enforced during review, not by tooling",
]
LINTER_BOUNDARY_SENTENCE = (
    "The linter checks presence and state consistency. It MUST NOT claim that"
    " evidence is authentic, relevant, or sufficient."
)

# Semantic anchors for the single-file presence-and-narrowing rule:
SINGLE_FILE_ANCHORS = [
    "Live-artifact success criteria vs. stable code facts (re-derivation convention):",
    "ARTIFACTS OF TEST ORGANIZATION",
    "neither may serve as a V-item's bar",
    "behaviour pinned plus the mechanism that pins it",
    "re-derivation at execution time",
    "schema keys, enum members",
    "orchestrator counting its own declared children",
    "Review is the only enforcement surface",
]

# Pointer anchors for the long-form parity rule:
LONG_FORM_POINTER_ANCHORS = [
    "Live-artifact success criteria vs. stable code facts (re-derivation convention):",
    "behaviour pinned plus the mechanism that pins it",
    "collected test count is never the bar",
    "../plan-review/plan-review.md",
    "per the parity note in `plan-review-long.md`",
]


class TestVItemEvidenceDurability(unittest.TestCase):
    def test_single_file_plan_review_evidence_durability(self) -> None:
        """Assert single-file plan-review.md narrows the exemption and requires behaviour plus mechanism."""
        content = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
        section_g = support.section(content, "### G. Plan executability", "## ")

        # Locate the re-derivation convention bullet
        bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
        bullet_text = support.section(
            section_g, bullet_prefix, "\n- **", anchored=False
        )

        # 1. Assert semantic anchors are present
        for anchor in SINGLE_FILE_ANCHORS:
            self.assertIn(
                anchor,
                bullet_text,
                f"Anchor '{anchor}' not found in re-derivation bullet of {PLAN_REVIEW_REL}",
            )

        # 2. Assert narrowing: test assertions is no longer exempt
        self.assertNotIn(
            "test assertions",
            bullet_text,
            f"'test assertions' must not appear in re-derivation bullet of {PLAN_REVIEW_REL}",
        )

        # 3. Assert narrowing: a collected test count is not exempt
        self.assertNotIn(
            "collected test count is exempt",
            bullet_text.lower(),
            f"Exemption re-widened in {PLAN_REVIEW_REL}: a collected test count must not be exempt",
        )
        self.assertNotIn(
            "collected test count are exempt",
            bullet_text.lower(),
            f"Exemption re-widened in {PLAN_REVIEW_REL}: collected test counts must not be exempt",
        )

    def test_long_form_plan_review_evidence_durability_parity(self) -> None:
        """Assert review-rubric.md carries the parity pointer without duplicating the paragraph."""
        content = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
        section_a = support.section(content, "## A. Plan completeness", "## ")

        # Locate the pointer bullet
        bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
        bullet_text = support.section(
            section_a, bullet_prefix, "\n- **", anchored=False
        )

        # Assert pointer trio and summary anchors are present in the long-form bullet
        for anchor in LONG_FORM_POINTER_ANCHORS:
            self.assertIn(
                anchor,
                bullet_text,
                f"Anchor '{anchor}' not found in pointer bullet of {REVIEW_RUBRIC_REL}",
            )

        # Confirm the long-form does NOT duplicate the full paragraph (remains a pointer)
        self.assertNotIn(
            "Criteria counting **stable code facts**",
            bullet_text,
            f"{REVIEW_RUBRIC_REL} must not duplicate the full normative paragraph from plan-review.md",
        )

    def test_spec_section_5_4_evidence_reachability(self) -> None:
        """Assert spec Section 5.4 carries reachability rule and preserves linter boundary.

        This test lives in this module rather than tests/test_v_item_demonstration_reachability.py
        because that module owns the rule's presence across the two workflow review bodies,
        while this module owns the Section 5.4 spec surface (established by vtup6x).
        Pinning by surface keeps one test module per file-under-contract.
        """
        content = SPEC_FILE.read_text(encoding="utf-8")

        start_heading = "### 5.4 Evidence requirements"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx,
            -1,
            f"Missing heading '{start_heading}' in {SPEC_REL}",
        )

        end_heading = "### 5.5 "
        end_idx = content.find(end_heading, start_idx + len(start_heading))
        self.assertNotEqual(
            end_idx,
            -1,
            f"Missing heading '{end_heading}' in {SPEC_REL}",
        )

        section_5_4 = content[start_idx:end_idx]

        for anchor in SPEC_SECTION_5_4_REACHABILITY_ANCHORS:
            self.assertIn(
                anchor,
                section_5_4,
                f"Anchor '{anchor}' not found in Section 5.4 of {SPEC_REL}",
            )

        self.assertIn(
            LINTER_BOUNDARY_SENTENCE,
            section_5_4,
            f"Linter boundary sentence not found in Section 5.4 of {SPEC_REL}",
        )
