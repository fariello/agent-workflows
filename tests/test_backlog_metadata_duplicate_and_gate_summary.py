"""Tests for IPD 7ohskw: Flag duplicated metadata bullet and non-blocked/unsafe Gate-Summary.

Outcome tests covering:
- backlog.metadata-bullet-repeated over six duplicate shapes, legacy Kind canonicalization,
  and indented sub-bullet boundary preservation.
- backlog.gate-summary-unexpected and backlog.gate-descriptive-unsafe across placement
  and length/control-character bounds (including exact 300 vs 301 char boundary).
- doctor.build_remediation routing ensuring the unsafe-value rule routes to a Gate-Summary
  remediation and does not get captured by the - Summary: arm.
- check_engine.RULE_REGISTRY membership for all three rules.
- Live tree regression floor via cli.main(['backlog', 'check', ...]).
- End-to-end producer case catching duplicated Blocks-Release lines.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as core
from agent_workflows import backlog
from agent_workflows import check_engine
from agent_workflows import cli
from agent_workflows import doctor
from agent_workflows import releases


def _make_item(
    id6: str = "abc123",
    status: str = "open",
    setid: str = "9rl7cm",
    priority: str = "low",
    work_kind: str = "chore",
    summary: str = "A valid summary line",
    extra_bullets: list[str] | None = None,
    body: str = "",
) -> str:
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {setid}",
        f"- Priority: {priority}",
        f"- Work-Kind: {work_kind}",
        f"- Summary: {summary}",
    ]
    if extra_bullets:
        lines.extend(extra_bullets)
    lines.extend(
        [
            "",
            "## Workflow history",
            f"- 2026-10-01 created (aw backlog): {summary}",
            "",
            body,
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


class BacklogMetadataDuplicateAndGateSummaryTests(unittest.TestCase):
    def test_duplicate_bullets_six_shapes(self) -> None:
        p_open = Path(".aw/records/backlog/open/abc123.md")

        # 1. Doubled - Status:
        text_status = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Status: done\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Work-Kind: chore\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts = backlog.validate_item(p_open, text_status)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Status", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        # 2. Doubled - Work-Kind:
        text_kind = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Work-Kind: chore\n"
            "- Work-Kind: bug\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts = backlog.validate_item(p_open, text_kind)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Work-Kind", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        # 3. One - Kind: plus one - Work-Kind:
        text_canon = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Kind: chore\n"
            "- Work-Kind: bug\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts = backlog.validate_item(p_open, text_canon)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Work-Kind", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        # 4. Doubled - Blocks-Release: agreeing and disagreeing
        text_br_agree = _make_item(
            extra_bullets=["- Blocks-Release: next", "- Blocks-Release: next"]
        )
        drifts = backlog.validate_item(p_open, text_br_agree)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Blocks-Release", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        text_br_disagree = _make_item(
            extra_bullets=["- Blocks-Release: next", "- Blocks-Release: 1.0.0"]
        )
        drifts = backlog.validate_item(p_open, text_br_disagree)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Blocks-Release", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        # 5. Doubled - Id:
        text_id = (
            "- Id: abc123\n"
            "- Id: def456\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Work-Kind: chore\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts = backlog.validate_item(p_open, text_id)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(repeated), 1)
        self.assertIn("Id", repeated[0].detail)
        self.assertIn("2", repeated[0].detail)

        # 6. Conformant item
        text_ok = _make_item()
        drifts = backlog.validate_item(p_open, text_ok)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(repeated, [])

    def test_legacy_kind_canonicalization_both_orders(self) -> None:
        p_open = Path(".aw/records/backlog/open/abc123.md")

        text_order1 = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Kind: chore\n"
            "- Work-Kind: bug\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts1 = backlog.validate_item(p_open, text_order1)
        rep1 = [d for d in drifts1 if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(rep1), 1)
        self.assertIn("Work-Kind", rep1[0].detail)
        self.assertIn("2", rep1[0].detail)

        text_order2 = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Work-Kind: bug\n"
            "- Kind: chore\n"
            "- Summary: Valid summary\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts2 = backlog.validate_item(p_open, text_order2)
        rep2 = [d for d in drifts2 if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(len(rep2), 1)
        self.assertIn("Work-Kind", rep2[0].detail)
        self.assertIn("2", rep2[0].detail)

    def test_sub_bullet_boundary_deliberate_non_finding(self) -> None:
        p_open = Path(".aw/records/backlog/open/abc123.md")
        text = (
            "- Id: abc123\n"
            "- Status: open\n"
            "- Set: 9rl7cm\n"
            "- Priority: low\n"
            "- Work-Kind: chore\n"
            "- Summary: A summary line\n"
            "  - indented sub bullet\n"
            "- Work-Kind: bug\n\n"
            "## Workflow history\n- 2026-10-01 created: note\n"
        )
        drifts = backlog.validate_item(p_open, text)
        repeated = [d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"]
        self.assertEqual(repeated, [])

    def test_gate_summary_rules(self) -> None:
        p_open = Path(".aw/records/backlog/open/abc123.md")
        p_done = Path(".aw/records/backlog/done/abc123.md")
        p_blocked = Path(".aw/records/backlog/blocked/abc123.md")

        # 1. done item with safe Gate-Summary
        text_done = _make_item(
            status="done", extra_bullets=["- Gate-Summary: waiting on a ruling"]
        )
        drifts = backlog.validate_item(p_done, text_done)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-summary-unexpected", rules)
        self.assertNotIn("backlog.gate-descriptive-unsafe", rules)
        self.assertNotIn("backlog.gate-unexpected", rules)

        # 2. open item with safe Gate-Summary
        text_open = _make_item(
            status="open", extra_bullets=["- Gate-Summary: waiting on a ruling"]
        )
        drifts = backlog.validate_item(p_open, text_open)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-summary-unexpected", rules)
        self.assertNotIn("backlog.gate-descriptive-unsafe", rules)
        self.assertNotIn("backlog.gate-unexpected", rules)

        # 3. blocked item with safe Gate-Summary
        text_blocked = _make_item(
            status="blocked",
            extra_bullets=[
                "- Gate-Kind: date",
                "- Gate-Ref: 2026-10-15",
                "- Gate-Summary: waiting on a ruling",
            ],
        )
        drifts = backlog.validate_item(p_blocked, text_blocked)
        rules = [d.rule for d in drifts]
        self.assertNotIn("backlog.gate-summary-unexpected", rules)
        self.assertNotIn("backlog.gate-descriptive-unsafe", rules)
        self.assertNotIn("backlog.gate-unexpected", rules)
        self.assertEqual(drifts, [])

        # 4. blocked item with ANSI escape in Gate-Summary
        text_ansi = _make_item(
            status="blocked",
            extra_bullets=[
                "- Gate-Kind: date",
                "- Gate-Ref: 2026-10-15",
                "- Gate-Summary: bad\x1b[31mred",
            ],
        )
        drifts = backlog.validate_item(p_blocked, text_ansi)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-descriptive-unsafe", rules)
        self.assertNotIn("backlog.gate-summary-unexpected", rules)

        # 5. blocked item at exactly 300 characters
        safe_300 = "x" * 300
        text_300 = _make_item(
            status="blocked",
            extra_bullets=[
                "- Gate-Kind: date",
                "- Gate-Ref: 2026-10-15",
                f"- Gate-Summary: {safe_300}",
            ],
        )
        drifts = backlog.validate_item(p_blocked, text_300)
        rules = [d.rule for d in drifts]
        self.assertNotIn("backlog.gate-descriptive-unsafe", rules)

        # 6. blocked item at 301 characters
        unsafe_301 = "x" * 301
        text_301 = _make_item(
            status="blocked",
            extra_bullets=[
                "- Gate-Kind: date",
                "- Gate-Ref: 2026-10-15",
                f"- Gate-Summary: {unsafe_301}",
            ],
        )
        drifts = backlog.validate_item(p_blocked, text_301)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-descriptive-unsafe", rules)

        # 7. blocked item with control character
        text_ctrl = _make_item(
            status="blocked",
            extra_bullets=[
                "- Gate-Kind: date",
                "- Gate-Ref: 2026-10-15",
                "- Gate-Summary: line\x00zero",
            ],
        )
        drifts = backlog.validate_item(p_blocked, text_ctrl)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-descriptive-unsafe", rules)

        # 8. done item with unsafe Gate-Summary (both findings reported)
        text_done_unsafe = _make_item(
            status="done",
            extra_bullets=["- Gate-Summary: bad\x1b[31mred"],
        )
        drifts = backlog.validate_item(p_done, text_done_unsafe)
        rules = [d.rule for d in drifts]
        self.assertIn("backlog.gate-summary-unexpected", rules)
        self.assertIn("backlog.gate-descriptive-unsafe", rules)

    def test_remediation_routing(self) -> None:
        # Chosen rule id: backlog.gate-descriptive-unsafe
        d_chosen = core.Drift(
            ".aw/records/backlog/blocked/abc123.md",
            "backlog.gate-descriptive-unsafe",
            "Gate-Summary not a single bounded control-char-free line",
        )
        rem_chosen = doctor.build_remediation(d_chosen, Path("."))
        self.assertIn("Gate-Summary", rem_chosen.title)
        self.assertNotIn("- Summary:", rem_chosen.summary_fix)

        # Rejected rule id: backlog.gate-summary-unsafe
        d_rejected = core.Drift(
            ".aw/records/backlog/blocked/abc123.md",
            "backlog.gate-summary-unsafe",
            "Gate-Summary not a single bounded control-char-free line",
        )
        rem_rejected = doctor.build_remediation(d_rejected, Path("."))
        self.assertEqual(
            rem_rejected.title, "Summary is not a single bounded control-char-free line"
        )
        self.assertIn("- Summary:", rem_rejected.summary_fix)

    def test_rule_registry_membership(self) -> None:
        self.assertIn("backlog.metadata-bullet-repeated", check_engine.RULE_REGISTRY)
        self.assertIn("backlog.gate-summary-unexpected", check_engine.RULE_REGISTRY)
        self.assertIn("backlog.gate-descriptive-unsafe", check_engine.RULE_REGISTRY)
        self.assertNotIn("backlog.gate-unexpected", check_engine.RULE_REGISTRY)

        for rule_id in (
            "backlog.metadata-bullet-repeated",
            "backlog.gate-summary-unexpected",
            "backlog.gate-descriptive-unsafe",
        ):
            spec = check_engine.rule_spec(rule_id)
            self.assertEqual(spec.severity, "error")
            self.assertEqual(spec.assurance, check_engine.ASSURANCE_REPOSITORY)
            self.assertEqual(spec.determinism, check_engine.DET_DETERMINISTIC)
            self.assertEqual(spec.invariant, "")

    def test_live_tree_regression_floor(self) -> None:
        text = _make_item()
        p = Path(".aw/records/backlog/open/abc123.md")
        self.assertEqual(backlog.validate_item(p, text), [])

        rc = cli.main(["backlog", "check", "--agent"])
        self.assertEqual(rc, 0)

    def test_e2e_producer_blocks_release_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            item_dir = root / ".aw" / "records" / "backlog" / "open"
            item_dir.mkdir(parents=True)
            item_path = item_dir / "20261001-9rl7cm-01-prod01-test-item.backlog.md"

            # 1. Direct two-line check
            seed_two = (
                "- Id: prod01\n"
                "- Status: open\n"
                "- Set: 9rl7cm\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: Test summary\n"
                "- Blocks-Release: next\n"
                "- Blocks-Release:\n\n"
                "## Workflow history\n- 2026-10-01 created: note\n"
            )
            item_path.write_text(seed_two, encoding="utf-8")
            drifts = backlog.validate_item(item_path, seed_two)
            rules = [d.rule for d in drifts]
            self.assertIn("backlog.metadata-bullet-repeated", rules)
            repeated_drift = [
                d for d in drifts if d.rule == "backlog.metadata-bullet-repeated"
            ][0]
            self.assertIn("Blocks-Release", repeated_drift.detail)
            self.assertIn("2", repeated_drift.detail)

            # 2. Producer simulation matching F-04:
            # Before releases.set_blocks_release_line was fixed, _BLOCKS_RELEASE_LINE_RE stripped \S+,
            # leaving empty-valued '- Blocks-Release:' lines in place when setting a new value.
            legacy_re = re.compile(r"(?m)^- Blocks-Release:[ \t]*\S+[ \t]*$\n?")
            seed_bare = (
                "- Id: prod01\n"
                "- Status: open\n"
                "- Set: 9rl7cm\n"
                "- Priority: low\n"
                "- Work-Kind: chore\n"
                "- Summary: Test summary\n"
                "- Blocks-Release:\n\n"
                "## Workflow history\n- 2026-10-01 created: note\n"
            )
            item_path.write_text(seed_bare, encoding="utf-8")
            with mock.patch.object(releases, "_BLOCKS_RELEASE_LINE_RE", legacy_re):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "prod01",
                        "--blocks-release",
                        "next",
                        "--no-commit",
                        "--dir",
                        str(root),
                    ]
                )
                self.assertEqual(rc, 0)

            written_content = item_path.read_text(encoding="utf-8")
            self.assertEqual(written_content.count("- Blocks-Release:"), 2)
            drifts_written = backlog.validate_item(item_path, written_content)
            rules_written = [d.rule for d in drifts_written]
            self.assertIn("backlog.metadata-bullet-repeated", rules_written)
