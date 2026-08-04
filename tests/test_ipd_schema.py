"""Tests for the canonical IPD schema (Set ipd-structure, Order 01).

Table-driven, stdlib unittest, zero dependencies. Verifies the schema against the specification
.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md and against the LIVE
templates (for the heading orders).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from agent_workflows import ipd_schema as S
from tests.support import REPO_ROOT

CHILD_TEMPLATE = REPO_ROOT / ".agents" / "workflows" / "assess" / "templates" / "ipd.md"
ORCH_IPD = (
    REPO_ROOT
    / ".agents"
    / "plans"
    / "pending"
    / "20260802-1944-00-ipd-structure-orchestrator.md"
)


def _h2_sequence(path: Path):
    seq = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            seq.append(line[3:].strip())
    return seq


class HeadingOrderTests(unittest.TestCase):
    def test_child_order_matches_live_template(self):
        self.assertEqual(list(S.CHILD_H2_ORDER), _h2_sequence(CHILD_TEMPLATE))

    def test_child_order_includes_step0_and_bare_findings(self):
        self.assertIn("Project conventions discovered (Step 0)", S.CHILD_H2_ORDER)
        self.assertIn("Findings", S.CHILD_H2_ORDER)
        self.assertNotIn("Findings (drivers)", S.CHILD_H2_ORDER)

    def test_orchestrator_checklist_immediately_after_goal(self):
        self.assertTrue(S.execution_follows_goal(S.KIND_ORCHESTRATOR))
        self.assertTrue(S.execution_follows_goal(S.KIND_CHILD))

    def test_validation_immediately_before_gate(self):
        self.assertTrue(S.validation_precedes_gate(S.KIND_CHILD))
        self.assertTrue(S.validation_precedes_gate(S.KIND_ORCHESTRATOR))

    def test_orchestrator_order_matches_the_order00_file(self):
        # The Order-00 file exemplifies the corrected orchestrator order.
        self.assertEqual(list(S.ORCHESTRATOR_H2_ORDER), _h2_sequence(ORCH_IPD))


class MetadataTests(unittest.TestCase):
    BASE = {
        "Date": "2026-08-03",
        "Kind": "child",
        "Concern": "x",
        "Scope": "x",
        "Status": "to-review",
        "Author": "x",
        "Set": "s",
        "Order": "1",
    }

    def test_valid_child_metadata_passes(self):
        self.assertEqual(S.validate_metadata(dict(self.BASE), directory="pending"), [])

    def test_missing_required_field_flagged(self):
        f = dict(self.BASE)
        del f["Status"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Status" for e in errs))

    def test_auto_approved_is_recognized(self):
        self.assertIn("auto-approved", S.RECOGNIZED_STATUS)
        f = dict(self.BASE)
        f["Status"] = "auto-approved"
        errs = S.validate_metadata(f, directory="pending")
        # auto-approved must NOT require an Approval field.
        self.assertFalse(any(e.field == S.META_APPROVAL for e in errs))

    def test_approved_requires_approval_field(self):
        f = dict(self.BASE)
        f["Status"] = "approved"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == S.META_APPROVAL for e in errs))
        f["Approval"] = "approved by x 2026-08-03"
        self.assertFalse(
            any(
                e.field == S.META_APPROVAL
                for e in S.validate_metadata(f, directory="pending")
            )
        )

    def test_approval_forbidden_without_approved_status(self):
        f = dict(self.BASE)
        f["Approval"] = "approved by x"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == S.META_APPROVAL for e in errs))

    def test_orchestrator_order_must_be_zero(self):
        f = dict(self.BASE)
        f["Kind"] = "orchestrator"
        f["Order"] = "1"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Order" for e in errs))
        f["Order"] = "0"
        self.assertFalse(
            any(e.field == "Order" for e in S.validate_metadata(f, directory="pending"))
        )

    def test_child_order_must_be_ge_1(self):
        f = dict(self.BASE)
        f["Order"] = "0"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Order" for e in errs))

    def test_set_without_order_is_error(self):
        f = dict(self.BASE)
        del f["Order"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any("Set" in e.field for e in errs))

    def test_quarantine_trio_all_or_none(self):
        f = dict(self.BASE)
        f["Quarantine"] = "reason"
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Quarantine" for e in errs))

    def test_quarantine_forbidden_on_terminal(self):
        f = dict(self.BASE)
        f["Status"] = "executed"
        del f["Set"]
        del f["Order"]
        f["Quarantine"] = "r"
        f["Quarantine owner"] = "o"
        f["Quarantine follow-up"] = "f"
        errs = S.validate_metadata(f, directory="executed")
        self.assertTrue(any(e.field == "Quarantine" for e in errs))

    def test_duplicate_and_unknown_fields_from_parse(self):
        lines = [
            "- Date: 2026-08-03",
            "- Date: 2026-08-04",  # duplicate
            "- Bogus: x",  # unknown
        ]
        fields, errs = S.parse_metadata_block(lines)
        self.assertTrue(
            any(e.message == "duplicate field" and e.field == "Date" for e in errs)
        )
        self.assertTrue(
            any(e.message == "unknown field" and e.field == "Bogus" for e in errs)
        )

    def test_terminal_status_directory_mismatch(self):
        f = dict(self.BASE)
        f["Status"] = "executed"
        del f["Set"]
        del f["Order"]
        errs = S.validate_metadata(f, directory="pending")
        self.assertTrue(any(e.field == "Status" for e in errs))


class IdGrammarTests(unittest.TestCase):
    def test_id_matches_in_filename_and_prose(self):
        self.assertTrue(S.E_ID_RE.search("20260803-01-k7-slug.md path E-01 here"))
        self.assertTrue(S.E_ID_RE.search("see E-07 for details"))
        self.assertTrue(S.V_ID_RE.search("V-12 validates"))

    def test_rejects_malformed(self):
        self.assertIsNone(S.suffix_of("E-1"))  # too short
        self.assertIsNone(S.suffix_of("X-01"))  # wrong prefix
        self.assertEqual(S.suffix_of("E-01"), 1)
        self.assertEqual(S.suffix_of("V-12"), 12)

    def test_next_suffix_from_watermark_not_max_present(self):
        # Watermark 8, present max 5 (highest deleted) -> next is 9, NOT 6.
        self.assertEqual(S.next_suffix(8), 9)

    def test_watermark_below_present_id_is_error(self):
        self.assertIsNotNone(S.watermark_error(3, [1, 2, 5]))
        self.assertIsNone(S.watermark_error(5, [1, 2, 5]))
        self.assertIsNone(S.watermark_error(8, [1, 2, 5]))

    def test_watermark_required_once_e_exists(self):
        self.assertIsNotNone(S.watermark_error(None, [1]))
        self.assertIsNone(S.watermark_error(None, []))

    def test_depends_on_grammar(self):
        self.assertEqual(S.parse_depends_on("none"), ([], None))
        self.assertEqual(S.parse_depends_on(""), ([], None))
        ids, err = S.parse_depends_on("E-01, E-02")
        self.assertEqual(ids, ["E-01", "E-02"])
        self.assertIsNone(err)
        _, err2 = S.parse_depends_on("E-1, bogus")
        self.assertIsNotNone(err2)

    def test_dependency_self_missing_cycle(self):
        self.assertTrue(
            any("itself" in e for e in S.dependency_errors({"E-01": ["E-01"]}))
        )
        self.assertTrue(
            any("missing" in e for e in S.dependency_errors({"E-02": ["E-09"]}))
        )
        cyc = S.dependency_errors({"E-01": ["E-02"], "E-02": ["E-01"]})
        self.assertTrue(any("cycle" in e for e in cyc))
        self.assertEqual(S.dependency_errors({"E-01": [], "E-02": ["E-01"]}), [])

    def test_bijection(self):
        # Clean 1:1.
        self.assertEqual(
            S.bijection_errors(["E-01", "E-02"], {"V-01": "E-01", "V-02": "E-02"}), []
        )
        # Orphan V (no matching E).
        self.assertTrue(S.bijection_errors(["E-01"], {"V-01": "E-01", "V-02": "E-02"}))
        # E with no V.
        self.assertTrue(
            any(
                "no validation" in e
                for e in S.bijection_errors(["E-01", "E-02"], {"V-01": "E-01"})
            )
        )
        # Suffix mismatch (V-02 validates E-01).
        self.assertTrue(
            S.bijection_errors(["E-01", "E-02"], {"V-02": "E-01", "V-01": "E-02"})
        )


class ExecutionStateTests(unittest.TestCase):
    def test_legal_execution_rows(self):
        self.assertIsNone(S.execution_row_error("pending", False, False))
        self.assertIsNone(S.execution_row_error("performed", True, False))
        self.assertIsNone(S.execution_row_error("blocked", False, True))
        self.assertIsNone(S.execution_row_error("failed", False, True))

    def test_illegal_execution_rows(self):
        self.assertIsNotNone(
            S.execution_row_error("pending", True, False)
        )  # checked but pending
        self.assertIsNotNone(
            S.execution_row_error("performed", False, False)
        )  # unchecked but performed
        self.assertIsNotNone(S.execution_row_error("blocked", False, False))  # no note
        self.assertIsNotNone(S.execution_row_error("bogus", False, False))


class ValidationStateTests(unittest.TestCase):
    def test_legal_validation_rows(self):
        self.assertIsNone(S.validation_row_error("pending", False, False))
        self.assertIsNone(S.validation_row_error("pass", True, True))
        self.assertIsNone(S.validation_row_error("blocked", False, True))
        self.assertIsNone(S.validation_row_error("failed", False, True))

    def test_illegal_validation_rows(self):
        self.assertIsNotNone(S.validation_row_error("pass", False, True))  # not checked
        self.assertIsNotNone(S.validation_row_error("pass", True, False))  # no evidence
        self.assertIsNotNone(
            S.validation_row_error("pending", False, True)
        )  # evidence but pending
        self.assertIsNotNone(S.validation_row_error("bogus", False, False))

    def test_cross_state(self):
        self.assertIsNotNone(
            S.cross_state_error("pending", "pass")
        )  # pass needs performed
        self.assertIsNotNone(
            S.cross_state_error("blocked", "pass")
        )  # blocked can't pass
        self.assertIsNone(S.cross_state_error("performed", "pass"))
        self.assertIsNone(S.cross_state_error("pending", "pending"))


class CheckpointTests(unittest.TestCase):
    def test_checkpoints_set(self):
        self.assertEqual(
            S.CHECKPOINTS,
            (
                "author",
                "review-finalize",
                "pre-execution",
                "pre-transition",
                "post-transition",
            ),
        )

    def test_checkpoint_status_compat(self):
        self.assertTrue(S.checkpoint_allows_status("author", "to-review"))
        self.assertTrue(S.checkpoint_allows_status("pre-execution", "approved"))
        self.assertTrue(S.checkpoint_allows_status("pre-execution", "auto-approved"))
        self.assertFalse(S.checkpoint_allows_status("pre-execution", "to-review"))
        self.assertFalse(S.checkpoint_allows_status("pre-transition", "executed"))
        self.assertTrue(S.checkpoint_allows_status("post-transition", "executed"))
        self.assertFalse(S.checkpoint_allows_status("bogus", "approved"))


class SizeTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertFalse(S.size_warning(5, 18))
        self.assertTrue(S.size_warning(6, 1))
        self.assertTrue(S.size_warning(1, 19))
        self.assertEqual(S.SIZE_ASSESSMENTS, frozenset(("standard", "exception")))


class OpenQuestionTests(unittest.TestCase):
    def test_legal_and_illegal(self):
        self.assertIsNone(S.open_question_error("no", "open", False, False))
        self.assertIsNone(S.open_question_error("yes", "resolved", True, True))
        self.assertIsNone(S.open_question_error("no", "deferred", True, True))
        self.assertIsNotNone(
            S.open_question_error("yes", "deferred", True, True)
        )  # blocking can't defer
        self.assertIsNotNone(
            S.open_question_error("yes", "resolved", False, True)
        )  # resolved needs rationale
        self.assertIsNotNone(S.open_question_error("maybe", "open", False, False))


class QuarantineAndLegacyTests(unittest.TestCase):
    def test_dispositions(self):
        self.assertEqual(S.DISPOSITION_QUARANTINED, "quarantined")
        self.assertEqual(S.DISPOSITION_LEGACY, "legacy/not evaluated")
        # quarantined and legacy are NON-passing.
        self.assertNotIn(S.DISPOSITION_QUARANTINED, S.PASSING_DISPOSITIONS)
        self.assertNotIn(S.DISPOSITION_LEGACY, S.PASSING_DISPOSITIONS)
        self.assertIn(S.DISPOSITION_CONFORMING, S.PASSING_DISPOSITIONS)

    def test_is_quarantined(self):
        self.assertTrue(S.is_quarantined({"Quarantine": "r"}))
        self.assertFalse(S.is_quarantined({"Date": "x"}))


class NoDependencyTests(unittest.TestCase):
    def test_module_is_stdlib_only(self):
        # The module must not import third-party packages (zero runtime deps, D46).
        src = (REPO_ROOT / "agent_workflows" / "ipd_schema.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {"__future__", "re", "typing", "agent_workflows"},
                "unexpected import: " + line,
            )


if __name__ == "__main__":
    unittest.main()
