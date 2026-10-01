"""Tests for the plan-review feasibility rule (IPD 7nghg8, set oqproof).

Exemption from source-text-pin prohibition:
This test is explicitly outside the source-text-pin prohibition, verified at review
(PR-004) rather than assumed, because the concurrent plan 96xtmi (srcguard-01) is
deleting text-pinning tests under the maintainer's 2026-09-26 ruling and a new one
would be born condemned. That plan's own Scope excludes "tests that read
NON-production files (specs, workflow bodies, READMEs, the test module's own file)
unless the census flags them as reading agent_workflows/*". A workflow body is a
WORKFLOW BODY, the artifact under change, and this test reads no agent_workflows/*
source, so it is out of scope for that deletion.
"""

from __future__ import annotations

from pathlib import Path
import unittest

# Distinctive anchor phrases for each of the five points in the feasibility rule:
# 1. Choosing a mechanism defines a HOW question.
# 2. Demonstration required for resolution.
# 3. Blocking question fallback causes lint error with IPD-Q501.
# 4. "Confirm empirically" clause is by definition undemonstrated.
# 5. False Owner: maintainer passes mechanical checks unenforced.
ANCHOR_PHRASES = [
    "chooses a mechanism rather than a fact or a scope",
    "cites a demonstration that the mechanism produces the required outcome",
    "IPD-Q501: OQ-01: BLOCKING question is still 'open'",
    "confirm empirically / if no form works, stop",
    "false `Owner: maintainer` passes every mechanical check",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".aw" / "system" / "workflows"
PLAN_REVIEW_FILE = WORKFLOWS_DIR / "plan-review" / "plan-review.md"
PLAN_REVIEW_LONG_FILE = (
    WORKFLOWS_DIR / "plan-review-long" / "03-resolve-and-finalize.md"
)
SPEC_REVIEW_FILE = WORKFLOWS_DIR / "spec-review" / "spec-review.md"
REVIEW_RUBRIC_FILE = WORKFLOWS_DIR / "plan-review-long" / "review-rubric.md"

# Anchor phrases for the canonical no-error-added proof shape (IPD k6t24p, set findtier):
# 1. Gate-consequence measurement function
# 2. Rule spec severity assertion symbol
# 3. Naming the exit-0 demand unsatisfiable
NO_ERROR_ADDED_ANCHOR_PHRASES = [
    "drift_exit_code",
    "check_engine.rule_spec",
    "unsatisfiable",
]


class TestPlanReviewFeasibilityRule(unittest.TestCase):
    def test_single_file_plan_review_feasibility_rule(self) -> None:
        """Assert single-file plan-review.md carries the 5-point feasibility rule in 3.1."""
        content = PLAN_REVIEW_FILE.read_text(encoding="utf-8")

        # Locate section 3.1 by heading boundaries
        start_heading = "### 3.1 "
        next_heading = "### 3.2 "
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx, -1, f"Missing heading '{start_heading}' in {PLAN_REVIEW_FILE}"
        )
        end_idx = content.find(next_heading, start_idx)
        self.assertNotEqual(
            end_idx, -1, f"Missing heading '{next_heading}' after '{start_heading}'"
        )

        section_31 = content[start_idx:end_idx]

        # Assert the subsection heading exists inside section 3.1
        subheading = "#### Resolving HOW questions: demonstrate, do not describe"
        self.assertIn(
            subheading,
            section_31,
            f"Subsection heading '{subheading}' not found inside section 3.1 of {PLAN_REVIEW_FILE}",
        )

        # Assert each of the five points is present via its anchor phrase
        for phrase in ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                section_31,
                f"Anchor phrase '{phrase}' not found in section 3.1 of {PLAN_REVIEW_FILE}",
            )

    def test_long_form_plan_review_feasibility_rule(self) -> None:
        """Assert long-form 03-resolve-and-finalize.md carries all five points plus parity pointer."""
        content = PLAN_REVIEW_LONG_FILE.read_text(encoding="utf-8")

        # Locate section 1 by heading boundaries
        start_heading = "## 1. Resolve open questions"
        start_idx = content.find(start_heading)
        self.assertNotEqual(
            start_idx,
            -1,
            f"Missing heading '{start_heading}' in {PLAN_REVIEW_LONG_FILE}",
        )

        # The section runs to the next ## heading (or end of file)
        next_heading = "\n## "
        end_idx = content.find(next_heading, start_idx + len(start_heading))
        section_1 = content[start_idx:end_idx] if end_idx != -1 else content[start_idx:]

        # Assert subsection heading exists in section 1
        subheading = "### Resolving HOW questions: demonstrate, do not describe"
        self.assertIn(
            subheading,
            section_1,
            f"Subsection heading '{subheading}' not found in section 1 of {PLAN_REVIEW_LONG_FILE}",
        )

        # Assert every one of the five points is present in full
        for phrase in ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                section_1,
                f"Anchor phrase '{phrase}' not found in section 1 of {PLAN_REVIEW_LONG_FILE}",
            )

        # Assert parity pointer naming the single-file form
        self.assertIn(
            "../plan-review/plan-review.md",
            section_1,
            f"Parity pointer to '../plan-review/plan-review.md' not found in {PLAN_REVIEW_LONG_FILE}",
        )
        self.assertIn(
            "per the parity note in `plan-review-long.md`",
            section_1,
            f"Parity note reference not found in {PLAN_REVIEW_LONG_FILE}",
        )

    def test_spec_review_feasibility_rule_reference(self) -> None:
        """Assert spec-review.md references plan-review's rule without copying the five points."""
        content = SPEC_REVIEW_FILE.read_text(encoding="utf-8")

        # Must reference plan-review.md and the subsection heading
        self.assertIn(
            "../plan-review/plan-review.md",
            content,
            f"Reference to '../plan-review/plan-review.md' not found in {SPEC_REVIEW_FILE}",
        )
        self.assertIn(
            "Resolving HOW questions: demonstrate, do not describe",
            content,
            f"Reference to subsection not found in {SPEC_REVIEW_FILE}",
        )

        # Must NOT duplicate the five points (at most one anchor phrase allowed)
        found_phrases = [p for p in ANCHOR_PHRASES if p in content]
        self.assertLessEqual(
            len(found_phrases),
            1,
            f"spec-review.md duplicates the feasibility rule ({len(found_phrases)} phrases found: "
            f"{found_phrases}). It must reference the rule, not copy it.",
        )

    def test_no_error_added_proof_shape_in_rubrics(self) -> None:
        """Assert both single-file and long-form rubrics carry the canonical no-error-added proof shape.

        Exemption from source-text-pin prohibition (GUIDING_PRINCIPLES P16):
        This test is explicitly within P16's narrow exception ('only where the text or file
        itself is the artifact under test') because the workflow bodies (plan-review.md and
        review-rubric.md) are the exact artifacts under change by IPD k6t24p. The test reads
        no code under agent_workflows/*.
        """
        # 1. Single-file rubric: check section G (Plan executability)
        single_content = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
        single_start = single_content.find("### G. Plan executability")
        self.assertNotEqual(
            single_start,
            -1,
            f"Missing heading '### G. Plan executability' in {PLAN_REVIEW_FILE}",
        )
        single_section = single_content[single_start:]
        for phrase in NO_ERROR_ADDED_ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                single_section,
                f"Anchor phrase '{phrase}' not found in section G of {PLAN_REVIEW_FILE}",
            )

        # 2. Long-form rubric: check section A (Plan completeness)
        long_content = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
        long_start = long_content.find("## A. Plan completeness")
        self.assertNotEqual(
            long_start,
            -1,
            f"Missing heading '## A. Plan completeness' in {REVIEW_RUBRIC_FILE}",
        )
        long_section = long_content[long_start:]
        for phrase in NO_ERROR_ADDED_ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                long_section,
                f"Anchor phrase '{phrase}' not found in section A of {REVIEW_RUBRIC_FILE}",
            )
