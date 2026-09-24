"""The single-file and long-form `plan-review` variants must stay in PARITY.

WHY THIS FILE STILL EXISTS WHEN OTHER PROSE-PINNING FILES WERE DELETED. The property here is not
"this sentence is present"; it is "these TWO documents agree". A reviewer reaches the same gate
through either variant, so an instruction added to one and not the other silently gives long-form
reviewers a weaker review than single-file ones. No amount of reading one file detects that; only
the comparison does. Git records prose edits, but it does not tell you the two copies diverged.

WHAT CHANGED. The needle lists were cut down to what is LOAD-BEARING, meaning a token something
other than a human consumes: a literal `aw ipd lint` invocation, an `aw check` rule id, a front
matter field spelling, a fixed vocabulary, a table header. Those are quoted verbatim in the
workflow because the reviewer must type or emit them exactly. Descriptive wording ("must mention
conceptual density", "must recommend splitting") was dropped: it is rewritten legitimately and
often, and pinning it produced failures that told the author nothing except that they edited prose.

The old shape also spent one test per phrase, so a single dropped instruction produced a wall of
red naming the same root cause. Each test below reports EVERY divergence it finds at once.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support import SOURCE_WORKFLOWS as WF

PLAN_REVIEW = WF / "plan-review" / "plan-review.md"
PRL_DIR = WF / "plan-review-long"
PRL_01 = PRL_DIR / "01-discover-and-snapshot.md"
PRL_02 = PRL_DIR / "02-review-and-revise.md"
PRL_03 = PRL_DIR / "03-resolve-and-finalize.md"
RUBRIC = PRL_DIR / "review-rubric.md"
REPORT_TEMPLATE = PRL_DIR / "report-template.md"
ORCHESTRATOR = PRL_DIR / "plan-review-long.md"
LIFECYCLE = WF / "ipd-lifecycle" / "ipd-lifecycle.md"
INDEX = WF / "index.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class WorkflowFilesTests(unittest.TestCase):
    def test_every_file_the_review_workflows_depend_on_exists(self):
        """One test for every required file: a missing dependency breaks the workflow identically.

        Reported together because the fix is the same (restore or re-point the file) and because a
        reviewer discovering them one at a time re-runs the suite once per missing file.
        """
        required = (
            PLAN_REVIEW,
            PRL_01,
            PRL_02,
            PRL_03,
            RUBRIC,
            REPORT_TEMPLATE,
            ORCHESTRATOR,
            LIFECYCLE,
            INDEX,
        )
        missing = [str(p) for p in required if not p.is_file()]
        self.assertEqual(
            missing,
            [],
            "the review workflows reference files that do not exist, so an agent following them "
            "hits a dead path:\n  " + "\n  ".join(missing),
        )


class VariantParityTests(unittest.TestCase):
    """Each entry: a load-bearing token, and the files that MUST all carry it.

    A token qualifies only if something non-human consumes it verbatim: a command an agent runs, a
    rule id `aw check` emits, a front matter field a parser reads, or a closed vocabulary a record
    is validated against. Prose describing a judgement is deliberately NOT here.
    """

    #: (token, why it is load-bearing, files that must each contain it)
    PARITY: tuple[tuple[str, str, tuple[Path, ...]], ...] = (
        (
            "aw ipd lint --phase author",
            "the authoring preflight an agent runs verbatim",
            (PLAN_REVIEW, PRL_01),
        ),
        (
            "aw ipd lint --phase review-finalize",
            "the finalize gate an agent runs verbatim",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            ".aw/records/reviews/",
            "the directory the typed review record is written to",
            (PLAN_REVIEW, PRL_02),
        ),
        (
            ".review.md",
            "the artifact facet the review record must use",
            (PLAN_REVIEW, PRL_02),
        ),
        (
            "- Blocking: yes",
            "the exact front matter field an escalation must carry to be detected",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            "check.review-finding-unescalated",
            "the `aw check` rule id that enforces the escalation",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            "check.review-decision-unescalated",
            "the `aw check` rule id that enforces decision escalation",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            "aw reviews decisions",
            "the command that reads the recorded decisions",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            "### Decisions",
            "the heading the decisions reader parses",
            (PLAN_REVIEW, PRL_03),
        ),
        (
            "`BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`",
            "the closed severity vocabulary a review record is validated against",
            (PLAN_REVIEW, PRL_02),
        ),
        (
            "`FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`",
            "the closed decision vocabulary a review record is validated against",
            (PLAN_REVIEW, PRL_02),
        ),
        (
            "IPD-S407",
            "the rule code for orchestrator checklist row conformance",
            (PLAN_REVIEW, PRL_02, PRL_03),
        ),
    )

    def test_both_variants_carry_every_load_bearing_token(self):
        divergences = []
        for token, why, paths in self.PARITY:
            absent = [p.name for p in paths if token not in _read(p)]
            if absent:
                present = [p.name for p in paths if token not in absent]
                divergences.append(
                    f"  {token!r}\n"
                    f"    load-bearing because: {why}\n"
                    f"    MISSING FROM: {absent}\n"
                    f"    present in:   {present or ['nothing - it is gone from every variant']}"
                )
        self.assertEqual(
            divergences,
            [],
            "the two plan-review variants have DIVERGED. A reviewer reaches the same gate through "
            "either one, so an instruction present in only one variant means whoever used the other "
            "variant was never told. Each token below is consumed verbatim by a command, a parser, "
            "or a validator, so a paraphrase does not substitute for it.\n"
            + "\n".join(divergences)
            + f"\n  FIX: add the token to the file(s) listed as MISSING FROM, under "
            f"{PRL_DIR} or {PLAN_REVIEW.parent}. If a token is gone from EVERY variant it was "
            "deleted wholesale; restore it or remove this row deliberately with a reason.",
        )

    def test_the_lint_checkpoints_are_named_in_the_lifecycle_workflow(self):
        """The three gates must be invocable as written; a renamed phase silently stops gating."""
        body = _read(LIFECYCLE)
        missing = [
            phase
            for phase in ("pre-execution", "pre-transition", "post-transition")
            if f"aw ipd lint --phase {phase}" not in body
        ]
        self.assertEqual(
            missing,
            [],
            f"ipd-lifecycle.md must name each lint checkpoint as a runnable command; {missing} "
            "are absent, so an agent following the workflow never runs that gate",
        )


class OrchestratorIsNotAStepFileTests(unittest.TestCase):
    """`plan-review-long.md` is a step INDEX; instructions put there reach nobody.

    This guards a mistake that has been made twice: editing the orchestrator instead of the step
    file. A naive parity check passes (the token IS in the long variant's directory) while long-form
    reviewers receive no instruction, because they read the step files.
    """

    def test_reviewer_instructions_live_in_step_files_not_the_orchestrator(self):
        body = _read(ORCHESTRATOR)
        misplaced = [
            token
            for token in (
                "A question you resolve yourself is not GONE",
                "check.review-decision-unescalated",
            )
            if token in body
        ]
        self.assertEqual(
            misplaced,
            [],
            f"{ORCHESTRATOR.name} only LISTS the steps; a reviewer never acts on it. The "
            f"instruction(s) {misplaced} belong in 03-resolve-and-finalize.md, the step file the "
            "reviewer actually follows. Left here, long-form reviewers get nothing while a "
            "directory-level parity check looks green.",
        )


class LifecycleRegistrationTests(unittest.TestCase):
    def test_ipd_lifecycle_is_registered_and_shimmed_at_its_real_path(self):
        """A shim pointing at a moved bundle is a broken slash command, which IS functional."""
        bundle = ".aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md"
        problems = []
        index = _read(INDEX)
        if "| ipd-lifecycle |" not in index:
            problems.append(
                "  the workflow index has no ipd-lifecycle row, so it is undiscoverable"
            )
        if bundle not in index:
            problems.append(f"  the index does not point at {bundle}")
        for host in (".opencode", ".claude"):
            shim = WF.parents[2] / host / "commands" / "ipd-lifecycle.md"
            if not shim.is_file():
                problems.append(f"  missing {host} shim: {shim}")
            elif bundle not in _read(shim):
                problems.append(
                    f"  {host} shim does not point at {bundle} (stale path)"
                )
        self.assertEqual(
            problems,
            [],
            "the ipd-lifecycle workflow is not reachable as installed:\n"
            + "\n".join(problems),
        )


if __name__ == "__main__":
    unittest.main()
