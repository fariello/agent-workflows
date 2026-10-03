"""runanalytics Order 10 (`9xycbh`) E-09 / Set spvm3v (bmxgt7) E-01, E-02:
Coupling guards between docs/run-analytics.md and agent_workflows.run_analytics_export.

Asserts:
1. docs/run-analytics.md exists and is linked from docs/README.md.
2. Every detector blind spot and covered class from agent_workflows.run_analytics_export
   is named in docs/run-analytics.md.
3. No document under docs/ claims an artifact passes or is clean by the sanitizer.
4. docs/run-analytics.md states the no-anonymity and no-causation limits.
5. docs/run-analytics.md distinguishes measured, derived, and missing provenance tokens.
6. docs/run-analytics.md covers each required audience section.
7. Set-equality arm (E-02): the harvested covered and blind-spot bullet sections in
   docs/run-analytics.md match DETECTOR_COVERED_CLASSES and DETECTOR_BLIND_SPOTS as sets,
   preventing silent drift when a class moves between lists.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from agent_workflows.run_analytics_export import (
    DETECTOR_BLIND_SPOTS,
    DETECTOR_COVERED_CLASSES,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


def _harvest_bullet_classes_after_anchor(text: str, anchor: str) -> set[str]:
    """Harvest the first contiguous bullet block after anchor as a set of class names.

    Anchors on a count-free prose string. Stops at the first non-bullet, non-blank line.
    Fails loudly if the anchor is absent or if no bullets are found, preventing silent no-ops.
    """
    if anchor not in text:
        raise AssertionError(
            f"Anchor prose {anchor!r} not found in documentation. "
            "The document's structure may have changed and this arm needs re-anchoring."
        )
    after = text.split(anchor, 1)[1]
    pattern = re.compile(r"^- `([a-z-]+)`")
    harvested = set()
    in_bullets = False
    for raw_line in after.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            in_bullets = True
            harvested.add(m.group(1))
        elif in_bullets:
            break
    if not harvested:
        raise AssertionError(
            f"No bullets matching '^- `([a-z-]+)`' found after anchor {anchor!r}. "
            "The document's structure may have changed and this arm needs re-anchoring."
        )
    return harvested


class RunAnalyticsPrivacyDocTests(unittest.TestCase):
    """runanalytics Order 10 (`9xycbh`) E-09 / Set spvm3v (bmxgt7) E-01, E-02:
    The privacy prose stays COUPLED to the code.

    Documentation about a detector's coverage rots the moment the ruleset changes, and a stale
    blind-spot list is worse than none: it would tell a reader a class is unchecked when it is, or
    (far worse) let a newly blind class go unnamed. So the list is asserted against the shipped
    enumeration rather than being trusted, which makes a future ruleset change fail HERE, with a
    message naming the document to update.
    """

    ANALYTICS_DOC = DOCS_DIR / "run-analytics.md"

    def setUp(self):
        self.maxDiff = None
        self.text = self.ANALYTICS_DOC.read_text(encoding="utf-8")

    def test_the_analytics_doc_exists_and_is_linked_from_the_index(self):
        self.assertTrue(self.ANALYTICS_DOC.is_file())
        index = (DOCS_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("run-analytics.md", index, "the doc is not linked from the index")

    def test_every_detector_blind_spot_is_NAMED_in_the_documentation(self):
        missing = [name for name in DETECTOR_BLIND_SPOTS if name not in self.text]
        self.assertEqual(
            missing,
            [],
            f"docs/run-analytics.md does not name these detector blind spots: {missing}. "
            f"A reader would take the list as complete.",
        )
        for covered in DETECTOR_COVERED_CLASSES:
            self.assertIn(covered, self.text, f"{covered} is not named as covered")

    def test_no_document_claims_an_artifact_PASSES_the_sanitizer(self):
        """The forbidden claim, because it converts corroboration into a guarantee."""

        for path in sorted(DOCS_DIR.rglob("*.md")):
            body = path.read_text(encoding="utf-8").lower()
            for forbidden in (
                "passes the sanitizer",
                "passed the sanitizer",
                "sanitizer-clean",
                "verified clean by the sanitizer",
            ):
                with self.subTest(doc=path.name, claim=forbidden):
                    self.assertNotIn(forbidden, body)

    def test_the_documentation_states_the_no_anonymity_and_no_causation_limits(self):
        lowered = self.text.lower()
        self.assertIn("no tier is anonymous", lowered)
        self.assertIn("minimization is not anonymity", lowered)
        self.assertIn("causation", lowered)
        self.assertIn("pseudonymous, never anonymous", lowered)

    def test_the_documentation_distinguishes_measured_derived_and_missing(self):
        for token in (
            "recorded",
            "measured",
            "derived",
            "missing",
            "unavailable",
            "not-applicable",
        ):
            with self.subTest(provenance=token):
                self.assertIn(token, self.text)

    def test_the_documentation_covers_every_audience_this_plan_owes(self):
        """The per-audience coverage map, asserted rather than promised."""

        for heading in (
            "## Quick start (operator)",
            "## The agent surface",
            "## The privacy boundary",
            "## Troubleshooting",
            "## Compatibility",
            "## The cache, and when it rebuilds",
            "## Telemetry",
        ):
            with self.subTest(section=heading):
                self.assertIn(heading, self.text)

    def test_detector_covered_and_blind_spot_lists_match_code_as_sets(self):
        """E-02: set-equality coupling between docs/run-analytics.md list sections and code.

        Harvests the covered list following 'at fail severity:' and the blind-spot list
        following 'does NOT look for the other', asserting each matches the corresponding
        code tuple as a set. Closes the blind spot where a class moving from blind to covered
        would satisfy substring presence while leaving the documentation lists stale.
        """
        covered_in_doc = _harvest_bullet_classes_after_anchor(
            self.text, "at fail severity:"
        )
        blind_in_doc = _harvest_bullet_classes_after_anchor(
            self.text, "does NOT look for the other"
        )

        expected_covered = set(DETECTOR_COVERED_CLASSES)
        expected_blind = set(DETECTOR_BLIND_SPOTS)

        if covered_in_doc != expected_covered:
            in_doc_not_code = covered_in_doc - expected_covered
            in_code_not_doc = expected_covered - covered_in_doc
            self.fail(
                "Covered classes list mismatch between docs/run-analytics.md and DETECTOR_COVERED_CLASSES:\n"
                f"  In doc but not in code: {sorted(in_doc_not_code)}\n"
                f"  In code but not in doc: {sorted(in_code_not_doc)}"
            )

        if blind_in_doc != expected_blind:
            in_doc_not_code = blind_in_doc - expected_blind
            in_code_not_doc = expected_blind - blind_in_doc
            self.fail(
                "Blind spots list mismatch between docs/run-analytics.md and DETECTOR_BLIND_SPOTS:\n"
                f"  In doc but not in code: {sorted(in_doc_not_code)}\n"
                f"  In code but not in doc: {sorted(in_code_not_doc)}"
            )


if __name__ == "__main__":
    unittest.main()
