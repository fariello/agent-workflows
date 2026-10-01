"""Tests for refusal record path redaction at the writer (IPD 7sc8fk).

Validates:
- E-04: Writer-side redaction across all five reader surfaces (Diagnostics block,
  format_refusal_summary, render_step_details, rec["refusal"], rec["issue_reasons"]).
- E-05: Non-mangling of slash commands (/spec-review, /plan-review, /exec-set, /whatnext)
  and idempotence under re-application.
"""

from __future__ import annotations

import unittest
from agent_workflows import render_stream as rs
from agent_workflows import run_viewer as rv
from agent_workflows.artifact_audit import ArtifactAudit
from agent_workflows.term import Term


SYNTHETIC_HOME = "/home/user/VC/agent-workflows"
SYNTHETIC_WORKTREE = f"{SYNTHETIC_HOME}/.aw/worktrees/abc123"
SYNTHETIC_REASON = (
    f"suite FAILED with exit 1 in {SYNTHETIC_HOME} (no summary line parsed)"
)
SYNTHETIC_REMEDY = f"inspect the lane at {SYNTHETIC_WORKTREE} then retry"


def _make_refused_item(
    reason: str = SYNTHETIC_REASON,
    remedy: str = SYNTHETIC_REMEDY,
    code: str = "merge-refused",
) -> dict:
    item = {
        "id6": "abc123",
        "action": "execute",
        "status": "refused",
        "setid": "testset",
        "position": 1,
    }
    rs.record_refusal(item, code=code, reason=reason, remedy=remedy)
    return item


def _make_step_and_audit(item: dict) -> tuple[rv.StepSummary, ArtifactAudit]:
    step = rv.StepSummary(
        position=item.get("position", 1),
        id6=item.get("id6", "abc123"),
        setid=item.get("setid", "testset"),
        action=item.get("action", "execute"),
        status=item.get("status", "refused"),
        configured_file="",
        stem=item.get("id6", "abc123"),
        refusal=item.get("refusal"),
    )
    audit = ArtifactAudit(
        id6=item.get("id6", "abc123"),
        stem=item.get("id6", "abc123"),
        run_status="refused",
        missing_entirely=False,
        location_mismatch=False,
        status_mismatch=False,
    )
    return step, audit


class RefusalRecordRedactionTests(unittest.TestCase):
    """Pin that record_refusal redacts absolute paths across all five reader surfaces."""

    def test_surface_1_render_run_summary_table_diagnostics(self) -> None:
        """Surface 1: render_run_summary_table Diagnostics block does not leak absolute path."""
        item = _make_refused_item()
        state = {"queue": [item], "run_id": "run_test_redact"}
        rendered = rs.render_run_summary_table(state)

        self.assertNotIn(SYNTHETIC_HOME, rendered)
        self.assertIn("refused (suite FAILED with exit 1 in <path>", rendered)
        self.assertIn(
            "remedy: inspect the lane at .aw/worktrees/abc123 then retry", rendered
        )

    def test_surface_2_run_viewer_format_refusal_summary(self) -> None:
        """Surface 2: format_refusal_summary does not leak absolute path."""
        item = _make_refused_item()
        step, _ = _make_step_and_audit(item)
        summary = rv.format_refusal_summary([step], Term(False))

        self.assertNotIn(SYNTHETIC_HOME, summary)
        self.assertIn("<path>", summary)
        self.assertIn(".aw/worktrees/abc123", summary)

    def test_surface_3_run_viewer_render_step_details(self) -> None:
        """Surface 3: render_step_details does not leak absolute path."""
        item = _make_refused_item()
        step, _ = _make_step_and_audit(item)
        details = rv.render_step_details([step], Term(False))
        joined = "\n".join(details)

        self.assertNotIn(SYNTHETIC_HOME, joined)
        self.assertIn("<path>", joined)
        self.assertIn(".aw/worktrees/abc123", joined)

    def test_surface_4_json_record_refusal_dict(self) -> None:
        """Surface 4: JSON record's rec['refusal'] does not leak absolute path."""
        item = _make_refused_item()
        step, _ = _make_step_and_audit(item)
        rf = rv.step_refusal(step)
        self.assertIsNotNone(rf)
        rec_refusal = rf.to_dict()

        self.assertNotIn(SYNTHETIC_HOME, rec_refusal["reason"])
        self.assertNotIn(SYNTHETIC_HOME, rec_refusal["remedy"])
        self.assertIn("<path>", rec_refusal["reason"])
        self.assertIn(".aw/worktrees/abc123", rec_refusal["remedy"])

    def test_surface_5_step_issue_reasons_in_rec_issue_reasons(self) -> None:
        """Surface 5: step_issue_reasons (feeding rec['issue_reasons']) does not leak absolute path."""
        item = _make_refused_item()
        step, audit = _make_step_and_audit(item)
        reasons = rv.step_issue_reasons(audit, step)

        self.assertTrue(len(reasons) > 0)
        self.assertNotIn(SYNTHETIC_HOME, reasons[0])
        self.assertIn("<path>", reasons[0])


class SlashCommandAndIdempotenceTests(unittest.TestCase):
    """Pin slash command preservation and redaction idempotence (E-05)."""

    def test_slash_command_remedies_survive_record_refusal(self) -> None:
        """Remedies naming slash commands survive record_refusal unchanged."""
        slash_commands = [
            "/spec-review .aw/records/specs/to-review/20260930-foo.spec.md",
            "/plan-review .aw/records/plans/pending/20260930-bar.ipd.md",
            "/exec-set refusalleak",
            "/whatnext",
        ]
        for cmd in slash_commands:
            item = {}
            rf = rs.record_refusal(
                item,
                code="review-refused",
                reason="review required",
                remedy=cmd,
            )
            self.assertEqual(cmd, rf.remedy)
            self.assertEqual(cmd, item["refusal"]["remedy"])

    def test_record_refusal_is_idempotent(self) -> None:
        """Applying redaction to already-redacted text is idempotent."""
        item = _make_refused_item()
        rf1 = item["refusal"]
        # Apply record_refusal again with the already-redacted text
        item2 = {}
        rf2 = rs.record_refusal(
            item2,
            code=rf1["code"],
            reason=rf1["reason"],
            remedy=rf1["remedy"],
        )
        self.assertEqual(rf1["reason"], rf2.reason)
        self.assertEqual(rf1["remedy"], rf2.remedy)
        self.assertEqual(rf1, item2["refusal"])


if __name__ == "__main__":
    unittest.main()
