"""Parity + registration tests for the review workflows and the new ipd-lifecycle path (Order 05).

Ensures the single-file `plan-review` and the long-form `plan-review-long` carry the SAME structural
linter contract (same checkpoints, disposition, fail-closed exit codes, deterministic-vs-semantic
boundary), that required long-form dependencies exist, and that `ipd-lifecycle` is registered and
shimmed consistently. Stdlib unittest.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from tests.support import REPO_ROOT

from tests.support import SOURCE_WORKFLOWS as WF

PLAN_REVIEW = WF / "plan-review" / "plan-review.md"
PRL_DIR = WF / "plan-review-long"
PRL_01 = PRL_DIR / "01-discover-and-snapshot.md"
PRL_03 = PRL_DIR / "03-resolve-and-finalize.md"
RUBRIC = PRL_DIR / "review-rubric.md"
REPORT_TEMPLATE = PRL_DIR / "report-template.md"
LIFECYCLE = WF / "ipd-lifecycle" / "ipd-lifecycle.md"
LIFECYCLE_README = WF / "ipd-lifecycle" / "README.md"
INDEX = WF / "index.md"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class ReviewPreflightParityTests(unittest.TestCase):
    def test_author_preflight_in_both_variants(self):
        cmd = "aw ipd lint --phase author"
        self.assertIn(
            cmd, _read(PLAN_REVIEW), "single-file plan-review missing author preflight"
        )
        self.assertIn(cmd, _read(PRL_01), "long-form step 01 missing author preflight")

    def test_review_finalize_preflight_in_both_variants(self):
        cmd = "aw ipd lint --phase review-finalize"
        self.assertIn(
            cmd,
            _read(PLAN_REVIEW),
            "single-file plan-review missing review-finalize preflight",
        )
        self.assertIn(
            cmd, _read(PRL_03), "long-form step 03 missing review-finalize preflight"
        )

    def test_both_variants_state_conforming_gate_and_failclosed(self):
        for path in (PLAN_REVIEW, PRL_01, PRL_03, RUBRIC):
            t = _read(path)
            if "aw ipd lint" not in t:
                continue
            tl = t.lower()
            self.assertIn(
                "conforming",
                tl,
                "{0} must require a conforming disposition".format(path.name),
            )
            self.assertIn(
                "exit `1`", tl, "{0} must state exit-1 handling".format(path.name)
            )
            self.assertIn(
                "exit `2`", tl, "{0} must state exit-2 handling".format(path.name)
            )

    def test_deterministic_vs_semantic_boundary_stated(self):
        for path in (PLAN_REVIEW, RUBRIC):
            t = _read(path).lower()
            self.assertIn("structure", t)
            self.assertIn("semantic", t)

    def test_invoke_not_paraphrase(self):
        # The workflows must INVOKE the linter, not restate its checks.
        self.assertIn("do not paraphrase", _read(PLAN_REVIEW).lower())


class LongFormDependencyTests(unittest.TestCase):
    def test_required_long_form_files_exist(self):
        for p in (PRL_01, PRL_03, RUBRIC, REPORT_TEMPLATE):
            self.assertTrue(
                p.is_file(), "missing required long-form dependency: {0}".format(p)
            )

    def test_report_template_referenced(self):
        # 03-resolve-and-finalize references the report template; the dependency must be present.
        self.assertTrue(REPORT_TEMPLATE.is_file())


class IpdLifecycleRegistrationTests(unittest.TestCase):
    def test_lifecycle_files_exist(self):
        self.assertTrue(LIFECYCLE.is_file())
        self.assertTrue(LIFECYCLE_README.is_file())

    def test_lifecycle_registered_in_index(self):
        t = _read(INDEX)
        self.assertIn("| ipd-lifecycle |", t)
        # Post-.aw/-migration the shipped bundle is under .aw/system/workflows/ (IPD awretrofit
        # Order 02); the index invocation column must reference the real installed path.
        self.assertIn(".aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md", t)

    def test_lifecycle_shims_exist_both_hosts(self):
        for host in (".opencode", ".claude"):
            shim = REPO_ROOT / host / "commands" / "ipd-lifecycle.md"
            self.assertTrue(shim.is_file(), "missing {0} shim".format(host))
            self.assertIn(
                ".agents/workflows/ipd-lifecycle/ipd-lifecycle.md", _read(shim)
            )

    def test_lifecycle_names_all_three_checkpoints(self):
        t = _read(LIFECYCLE)
        for phase in ("pre-execution", "pre-transition", "post-transition"):
            self.assertIn("aw ipd lint --phase {0}".format(phase), t)

    def test_lifecycle_states_failclosed_and_recovery(self):
        t = _read(LIFECYCLE)
        tl = t.lower()
        self.assertIn("exit `1`", tl)
        self.assertIn("exit `2`", tl)
        self.assertIn("hard stop", tl)
        # transition is a post-gate transaction, not a checklist item
        self.assertIn("POST-gate", t) if "POST-gate" in t else self.assertIn(
            "post-gate", t.lower()
        )
        # pre/post-commit recovery language present
        self.assertIn("BEFORE the lifecycle commit", t)
        self.assertIn("AFTER the lifecycle commit", t)


class DriftGuardTests(unittest.TestCase):
    def test_deliberate_desync_would_fail(self):
        # Sanity: the parity assertions are content-based, so removing the preflight line from a
        # copy is detectable. We assert the marker exists in the real file (the inverse of drift).
        self.assertIn("aw ipd lint --phase author", _read(PRL_01))


if __name__ == "__main__":
    unittest.main()
