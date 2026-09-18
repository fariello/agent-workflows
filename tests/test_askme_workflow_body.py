"""The `askme` workflow's pre-flight self-check list must have EXACTLY ONE home.

WHAT THIS FILE USED TO BE, AND WHY IT SHRANK. It was 29 tests that each asserted one verbatim
English sentence still appeared in `askme.md`, with a docstring conceding they proved "NOTHING
about whether the rules work". That is a change-detector over prose: a git repository already
records when prose changes and who changed it, and a reworded rule is a normal, desirable edit
rather than a regression. Pinning the wording made every legitimate reword a test failure while
still catching no defect, so the wording pins were deleted deliberately (not lost).

WHAT SURVIVES, because it is a STRUCTURAL property that prose-reading alone cannot give you:
the relocated pre-flight list must live in ONE place. Asserting merely "it is present somewhere"
passes in the DUPLICATED state, and duplication is the actual failure mode here (P8): two copies
drift, and an agent then obeys whichever it happened to read. So the single test below asserts
presence in the kernel AND absence from `GUIDING_PRINCIPLES.md` together, since neither half is
meaningful alone.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.support import REPO_ROOT
from tests.support import SOURCE_WORKFLOWS as WF

ASKME = WF / "askme" / "askme.md"
PRINCIPLES = REPO_ROOT / "GUIDING_PRINCIPLES.md"

# The four questions of the pre-flight self-check list that was relocated out of P12.
PREFLIGHT_QUESTIONS = (
    "Can the user answer without reopening other material?",
    "Is every included fact necessary?",
    "Is the reason for asking clear?",
    "Have I avoided repeating the tool's choices?",
)


def _read(p: Path) -> str:
    """Read a file with runs of whitespace collapsed, so a re-wrap is not a failure."""
    return re.sub(r"\s+", " ", p.read_text(encoding="utf-8"))


class PreflightListHasExactlyOneHomeTests(unittest.TestCase):
    def test_the_preflight_list_lives_in_the_kernel_and_nowhere_else(self):
        """Presence AND non-duplication in one test, because each half alone is misleading.

        A test asserting only presence passes while two divergent copies exist; a test asserting
        only absence passes when the list has been dropped entirely. Reporting both together also
        tells whoever broke it WHICH of the two states the tree is in, which is the information
        needed to fix it.
        """
        kernel, principles = _read(ASKME), _read(PRINCIPLES)
        problems = []
        for q in PREFLIGHT_QUESTIONS:
            in_kernel, in_principles = q in kernel, q in principles
            if not in_kernel and not in_principles:
                problems.append(f"  DROPPED ENTIRELY: {q!r} is in neither file")
            elif not in_kernel:
                problems.append(f"  WRONG HOME: {q!r} is only in GUIDING_PRINCIPLES.md")
            elif in_principles:
                problems.append(
                    f"  DUPLICATED: {q!r} is in BOTH files and the copies can drift"
                )
        self.assertEqual(
            problems,
            [],
            "the pre-flight self-check list must live in exactly one home, the askme memory "
            "kernel, with GUIDING_PRINCIPLES.md P12 POINTING at it rather than restating it "
            "(P8, single source of truth).\n"
            + "\n".join(problems)
            + f"\n  kernel: {ASKME}\n  principles: {PRINCIPLES}",
        )

    def test_principles_still_points_at_the_kernel(self):
        """If P12 stops pointing anywhere, the list is unreachable from where readers start."""
        principles = _read(PRINCIPLES)
        self.assertIn(
            "askme",
            principles,
            "GUIDING_PRINCIPLES.md P12 must still name the askme workflow, otherwise a reader "
            "of P12 has no route to the relocated pre-flight list",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
