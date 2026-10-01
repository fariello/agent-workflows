"""Tests for V-item evidence durability and parity rules (IPD vtup6x, set nos070).

Exemption from source-text-pin prohibition:
This test is explicitly outside the source-text-pin prohibition, verified at review
(PR-004) rather than assumed, because plan 96xtmi (srcguard-01) deleted text-pinning
tests under the maintainer's 2026-09-26 ruling and that plan's scope excluded "tests that
read NON-production files (specs, workflow bodies, READMEs, the test module's own file)
unless the census flags them as reading agent_workflows/*". A workflow body is a WORKFLOW
BODY, the artifact under change, and this test reads no agent_workflows/* source, so it
sits inside GUIDING_PRINCIPLES P16's stated narrow exception ("Content verification is
permissible only where the text or file itself is the artifact under test") and outside its
"No production source inspection" prohibition (whose enumerated targets are all
agent_workflows/*.py). Follows the precedent of tests/test_plan_review_feasibility_rule.py.
"""

from __future__ import annotations

from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".aw" / "system" / "workflows"
PLAN_REVIEW_FILE = WORKFLOWS_DIR / "plan-review" / "plan-review.md"
REVIEW_RUBRIC_FILE = WORKFLOWS_DIR / "plan-review-long" / "review-rubric.md"

PLAN_REVIEW_REL = ".aw/system/workflows/plan-review/plan-review.md"
REVIEW_RUBRIC_REL = ".aw/system/workflows/plan-review-long/review-rubric.md"

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

        start_heading = "### G. Plan executability"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx,
            -1,
            f"Missing heading '{start_heading}' in {PLAN_REVIEW_REL}",
        )

        section_g = content[start_idx:]

        # Locate the re-derivation convention bullet
        bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
        bullet_idx = section_g.find(bullet_prefix)
        self.assertNotEqual(
            bullet_idx,
            -1,
            f"Missing bullet '{bullet_prefix}' in {PLAN_REVIEW_REL}",
        )

        # Slice the bullet text up to the next bullet item
        next_bullet_idx = section_g.find("\n- **", bullet_idx + len(bullet_prefix))
        bullet_text = (
            section_g[bullet_idx:next_bullet_idx]
            if next_bullet_idx != -1
            else section_g[bullet_idx:]
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

        start_heading = "## A. Plan completeness"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx,
            -1,
            f"Missing heading '{start_heading}' in {REVIEW_RUBRIC_REL}",
        )

        section_a = content[start_idx:]

        # Locate the pointer bullet
        bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
        bullet_idx = section_a.find(bullet_prefix)
        self.assertNotEqual(
            bullet_idx,
            -1,
            f"Missing pointer bullet '{bullet_prefix}' in {REVIEW_RUBRIC_REL}",
        )

        next_bullet_idx = section_a.find("\n- **", bullet_idx + len(bullet_prefix))
        bullet_text = (
            section_a[bullet_idx:next_bullet_idx]
            if next_bullet_idx != -1
            else section_a[bullet_idx:]
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
