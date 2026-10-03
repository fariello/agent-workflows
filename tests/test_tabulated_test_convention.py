"""Tests for the tabulated test convention documentation (IPD prj0vm, set 7fzqop).

Exemption from source-text-pin prohibition:
This test is explicitly outside the source-text-pin prohibition per GUIDING_PRINCIPLES
P16's narrow exception ('Content verification is permissible only where the text or file
itself is the artifact under test') because GUIDING_PRINCIPLES.md and CONTRIBUTING.md
are the exact non-production documentation artifacts under change. This test reads no
source code under agent_workflows/*.

Hard constraint on file inspection:
This test reads files strictly via Path.read_text() and calls NO inspect or ast forms
(no source-inspection or AST-parsing call forms). This ensures compatibility with the
codebase's structural pin guards (such as 76ic0k).
"""

from __future__ import annotations

from pathlib import Path
import unittest

# Distinctive anchor phrases for each of the four load-bearing rules:
# 1. The canonical row shape citation from test_ipd_lint.py RULES comment.
# 2. The mandatory why column rendering in failure messages.
# 3. The when-NOT-to-tabulate list (sequence or rollback order).
# 4. The runner-dependent row verdict rule (default pytest without pytest-subtests).
ANCHOR_PHRASES = [
    "(case, the plan text, codes that MUST all be reported",
    "this row exists because: <why>",
    "The property is sequence or rollback order",
    "In default pytest runs (where `pytest-subtests` is not installed)",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDING_PRINCIPLES_FILE = REPO_ROOT / "GUIDING_PRINCIPLES.md"
CONTRIBUTING_FILE = REPO_ROOT / "CONTRIBUTING.md"


class TestTabulatedTestConvention(unittest.TestCase):
    def test_guiding_principles_p16_carries_tabulated_convention_subsection(
        self,
    ) -> None:
        """Assert GUIDING_PRINCIPLES.md carries the tabulated test convention within P16."""
        content = GUIDING_PRINCIPLES_FILE.read_text(encoding="utf-8")

        # Locate section 16 by heading boundary
        p16_heading = "## 16. Test outcomes and behavior, never code structure or text"
        p16_idx = content.find(p16_heading)
        self.assertNotEqual(
            p16_idx,
            -1,
            f"Missing heading '{p16_heading}' in {GUIDING_PRINCIPLES_FILE.name}",
        )

        # Bounding rule: P16 is the last principle in GUIDING_PRINCIPLES.md and ends at EOF.
        # Tolerate the absence of a following '## ' heading.
        next_heading = "\n## "
        end_idx = content.find(next_heading, p16_idx + len(p16_heading))
        section_16 = content[p16_idx:end_idx] if end_idx != -1 else content[p16_idx:]

        # Locate the subsection heading
        subheading = "### Tabulated and table-driven tests (accumulate versus subTest):"
        subheading_idx = section_16.find(subheading)
        self.assertNotEqual(
            subheading_idx,
            -1,
            f"Subsection heading '{subheading}' not found inside P16 of {GUIDING_PRINCIPLES_FILE.name}",
        )

        subsection_content = section_16[subheading_idx:]

        # Assert every anchor phrase is present in the subsection
        for phrase in ANCHOR_PHRASES:
            self.assertIn(
                phrase,
                subsection_content,
                f"Anchor phrase '{phrase}' not found in P16 subsection of {GUIDING_PRINCIPLES_FILE.name}",
            )

    def test_contributing_carries_pointer_to_p16_subsection(self) -> None:
        """Assert CONTRIBUTING.md points at the P16 subsection without restating the shape."""
        content = CONTRIBUTING_FILE.read_text(encoding="utf-8")

        # Locate ## Authoring conventions
        heading = "## Authoring conventions"
        heading_idx = content.find(heading)
        self.assertNotEqual(
            heading_idx,
            -1,
            f"Missing heading '{heading}' in {CONTRIBUTING_FILE.name}",
        )

        next_heading = "\n## "
        end_idx = content.find(next_heading, heading_idx + len(heading))
        section = (
            content[heading_idx:end_idx] if end_idx != -1 else content[heading_idx:]
        )

        # Assert pointer exists and points to the P16 subsection title
        pointer_title = "Tabulated and table-driven tests (accumulate versus subTest)"
        self.assertIn(
            pointer_title,
            section,
            f"Pointer to '{pointer_title}' not found in '## Authoring conventions' of {CONTRIBUTING_FILE.name}",
        )
