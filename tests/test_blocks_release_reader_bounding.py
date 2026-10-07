"""Outcome tests for bounding Blocks-Release readers and writers to the metadata region.

Covers IPD b92m14 (E-01 through E-08):
- Bounded reader selectors.read_front_matter_blocks_release
- Bidirectional display divergence resolved between aw set and aw attention
- Setter spellings (positional and flag) write byte-identical front matter
- Plans with body-only gate bullet excluded from releases.get_release_blockers
- releases.set_blocks_release_line bounds strip to metadata region, preserving body
- Fixture regression guard for get_release_blockers, sentinel count, check_blocks_release
- Removal with '-' strips only front-matter gate bullet, preserving body quotes
- ipd_lint board and check_engine release gate consistency bounded to metadata region

Tests behavioral outcomes and contracts only; no source inspection or AST (P16).
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import (
    attention,
    backlog,
    check_engine,
    ipd_lint,
    releases,
    selectors,
    status_set,
)


class TestBlocksReleaseReaderBounding(unittest.TestCase):
    """Behavioral outcome tests for metadata-bounded Blocks-Release readers/writers."""

    def test_read_front_matter_blocks_release_cases(self) -> None:
        """E-01 / V-01: read_front_matter_blocks_release on three distinct text shapes."""
        # Case 1: Declaring in bullet front matter
        text_fm = (
            "# Plan Title\n\n"
            "- Id: ppp111\n"
            "- Status: draft\n"
            "- Blocks-Release: next\n\n"
            "## Description\nBody here.\n"
        )
        self.assertEqual(selectors.read_front_matter_blocks_release(text_fm), "next")

        # Case 2: Only gate bullet sits below ## Workflow history
        text_body = (
            "# Plan Title\n\n"
            "- Id: ppp222\n"
            "- Status: draft\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created: - Blocks-Release: next\n"
        )
        self.assertIsNone(selectors.read_front_matter_blocks_release(text_body))

        # Case 3: YAML-fenced research doc with quoted bullet in body
        text_yaml = (
            "---\n"
            "id: rrr333\n"
            "status: active\n"
            "---\n\n"
            "# Research Document\n\n"
            "Here is a quote:\n"
            "- Blocks-Release: next\n"
        )
        self.assertIsNone(selectors.read_front_matter_blocks_release(text_yaml))

        # Anchored case from F-12: trailing content on gate line
        text_trailing = "- Blocks-Release: next                  - Set: demo\n"
        self.assertIsNone(selectors.read_front_matter_blocks_release(text_trailing))

    def test_bidirectional_display_divergence(self) -> None:
        """E-08(a) / V-02: aw set line and aw attention agree in body-quoted and real gate cases."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases.create_release(root, "2.0.0", "first release")

            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True)

            # Item 1: Body-quoted item
            item1 = bdir / "20261001-zzz999-01-zzz999-bug.backlog.md"
            item1.write_text(
                "- Id: zzz999\n"
                "- Status: open\n"
                "- Set: testset\n"
                "- Priority: low\n"
                "- Work-Kind: bug\n"
                "- Summary: Demo item\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created: note\n"
                "- Blocks-Release: next\n",
                encoding="utf-8",
            )

            # Item 2: Real front-matter gate item
            item2 = bdir / "20261001-www555-01-www555-bug.backlog.md"
            item2.write_text(
                "- Id: www555\n"
                "- Status: open\n"
                "- Blocks-Release: next\n"
                "- Set: testset\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Real gate item\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created: note\n",
                encoding="utf-8",
            )

            # 1. Format status transition line for Item 1 (body-quoted)
            inv = status_set.inventory_all_artifacts(root)
            rec1 = status_set.match_selector("zzz999", inv, root)[0]
            line1 = status_set._format_status_transition_line(
                rec1, rec1.path, "graduated", status_set.Term(), dry_run=True
            )
            self.assertNotIn("[blocking]", line1)
            self.assertTrue(line1.startswith("-    ") or line1.startswith("-  "))
            self.assertFalse(line1.startswith("- >"))

            # Check aw attention --format json for Item 1
            items, drift = attention.scan(root)
            json_str = attention.render_json(items, drift)
            payload = json.loads(json_str)
            item1_data = next(it for it in payload["items"] if it["id"] == "zzz999")
            self.assertIsNone(item1_data["blocks_release"])

            # 2. Format status transition line for Item 2 (real front-matter gate)
            rec2 = status_set.match_selector("www555", inv, root)[0]
            line2 = status_set._format_status_transition_line(
                rec2, rec2.path, "graduated", status_set.Term(), dry_run=True
            )
            self.assertIn("[blocking]", line2)
            self.assertIn(">", line2)

            # Check aw attention --format json for Item 2
            item2_data = next(it for it in payload["items"] if it["id"] == "www555")
            self.assertEqual(item2_data["blocks_release"], "next")

    def test_setter_spellings_byte_identical_with_body_quote(self) -> None:
        """E-08(b) / V-03: both setter spellings write byte-identical front matter."""

        def make_repo():
            td = tempfile.TemporaryDirectory()
            root = Path(td.name)
            releases.create_release(root, "2.0.0", "planned release")
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True)
            item = bdir / "20261001-bbb111-01-bbb111-bug.backlog.md"
            item.write_text(
                "- Id: bbb111\n"
                "- Status: open\n"
                "- Set: testset\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Fix bug\n\n"
                "## Workflow history\n"
                "- 2026-10-01 created (aw backlog): Fix bug\n"
                "- Blocks-Release: next\n",
                encoding="utf-8",
            )
            return td, root

        td1, root1 = make_repo()
        td2, root2 = make_repo()
        try:
            # Spelling 1: positional aw set blocked
            args1 = argparse.Namespace(
                gate_kind="decision", gate_ref="D100", dry_run=False, yes=True
            )
            ret1 = status_set.run_set_command(
                ["blocked", "bbb111"], repo_root=root1, args=args1
            )
            self.assertEqual(ret1, 0)

            # Spelling 2: flag aw backlog set --status blocked
            parser = argparse.ArgumentParser()
            parser.add_argument("--status", default=None)
            parser.add_argument("--gate-kind", default=None)
            parser.add_argument("--gate-ref", default=None)
            parser.add_argument("args", nargs="*")
            parser.add_argument("--dir", default=None)
            parser.add_argument("--message", default="")
            parser.add_argument("--allow-terminal-reopen", action="store_true")
            parser.add_argument("--blocks-release", default=None)
            parser.add_argument("--release-exempt-kind", default=None)
            parser.add_argument("--release-exempt-ref", default=None)
            parser.add_argument("--evidence", default=None)
            parser.add_argument("--graduated-to", default=None)
            parser.add_argument("--work-kind", default=None)
            parser.add_argument("--priority", default=None)
            parser.add_argument("--dry-run", action="store_true")
            parser.add_argument("--yes", "-y", action="store_true")
            parser.add_argument("--rewrite-citations", action="store_true")
            parser.add_argument("--gate-dir", default=None)
            parser.add_argument("--lane-carrier-ref", default=None)
            parser.add_argument("--lane-carrier-path", default=None)

            args2 = parser.parse_args(
                [
                    "--status",
                    "blocked",
                    "--gate-kind",
                    "decision",
                    "--gate-ref",
                    "D100",
                    "bbb111",
                ]
            )
            args2.dir = str(root2)
            args2.path = "bbb111"
            ret2 = backlog.run_set(args2)
            self.assertEqual(ret2, 0)

            # Read both relocated files
            file1 = list(
                (root1 / ".aw" / "records" / "backlog" / "blocked").glob("*.backlog.md")
            )[0]
            file2 = list(
                (root2 / ".aw" / "records" / "backlog" / "blocked").glob("*.backlog.md")
            )[0]

            def extract_front_matter(text: str) -> list[str]:
                fm = []
                for line in text.splitlines():
                    if not line.strip() or line.startswith("##"):
                        break
                    fm.append(line)
                return fm

            fm1 = extract_front_matter(file1.read_text(encoding="utf-8"))
            fm2 = extract_front_matter(file2.read_text(encoding="utf-8"))

            # Both must write byte-identical front matter including defaulted gate
            self.assertEqual(fm1, fm2)
            self.assertIn("- Blocks-Release: next", fm1)
        finally:
            td1.cleanup()
            td2.cleanup()

    def test_plan_with_body_only_bullet_absent_from_release_blockers(self) -> None:
        """E-08(c) / V-04: body-quoted plan absent from blockers; control plan present."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases.create_release(root, "2.0.0", "planned release")

            plan_dir = root / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True)

            # Plan with body-only bullet
            body_plan = plan_dir / "20261001-test-01-ppp444-body.ipd.md"
            body_plan.write_text(
                "# Title\n\n"
                "- Id: ppp444\n"
                "- Status: to-review\n"
                "- Set: testset\n\n"
                "## Workflow history\n"
                "- 2026-10-01: created\n"
                "- Blocks-Release: next\n",
                encoding="utf-8",
            )

            # Control plan with front-matter gate
            ctrl_plan = plan_dir / "20261001-test-02-qqq555-ctrl.ipd.md"
            ctrl_plan.write_text(
                "# Title\n\n"
                "- Id: qqq555\n"
                "- Status: to-review\n"
                "- Set: testset\n"
                "- Blocks-Release: next\n\n"
                "## Workflow history\n"
                "- 2026-10-01: created\n",
                encoding="utf-8",
            )

            blockers = releases.get_release_blockers(root, "next")
            blocker_ids = {b["id"] for b in blockers}

            self.assertNotIn("ppp444", blocker_ids)
            self.assertIn("qqq555", blocker_ids)

    def test_set_blocks_release_line_preserves_body(self) -> None:
        """E-08(d) / V-07: set_blocks_release_line preserves body line while setting front-matter."""
        text = (
            "- Id: bbb222\n"
            "- Status: open\n"
            "- Set: demo\n\n"
            "## Description\n"
            "Example quoted configuration:\n"
            "- Blocks-Release: next\n"
            "End of example.\n"
        )
        updated = releases.set_blocks_release_line(text, "next")
        # Line count: exactly 1 line added in front matter
        self.assertEqual(len(updated.splitlines()), len(text.splitlines()) + 1)
        self.assertEqual(updated.count("- Blocks-Release: next"), 2)

        # Idempotence: calling again yields identical text
        re_updated = releases.set_blocks_release_line(updated, "next")
        self.assertEqual(re_updated, updated)

        # Split at ## Description and verify body is byte-identical
        body_original = text.partition("## Description")[2]
        body_updated = updated.partition("## Description")[2]
        self.assertEqual(body_original, body_updated)

    def test_regression_guard_fixture_tree(self) -> None:
        """E-08(e) / V-05: fixture tree with gated and quoting records."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases.create_release(root, "2.0.0", "planned release")

            plan_dir = root / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True)

            # Legitimate gated plan
            gated_plan = plan_dir / "20261001-test-01-ggg111-gated.ipd.md"
            gated_plan.write_text(
                "# Gated Plan\n\n"
                "- Id: ggg111\n"
                "- Status: to-review\n"
                "- Set: testset\n"
                "- Blocks-Release: next\n\n"
                "## Workflow history\n"
                "- 2026-10-01: created\n",
                encoding="utf-8",
            )

            # Quoting plan quoting nonexistent release in body prose
            quoting_plan = plan_dir / "20261001-test-02-qqq222-quote.ipd.md"
            quoting_plan.write_text(
                "# Quoting Plan\n\n"
                "- Id: qqq222\n"
                "- Status: to-review\n"
                "- Set: testset\n\n"
                "## Workflow history\n"
                "- 2026-10-01: - Blocks-Release: nonexistent999\n",
                encoding="utf-8",
            )

            # get_release_blockers counts gated record and NOT quoting one
            blockers = releases.get_release_blockers(root, "next")
            self.assertEqual(len(blockers), 1)
            self.assertEqual(blockers[0]["id"], "ggg111")

            # count_blocks_release_sentinel counts only gated record
            sentinel_count = releases.count_blocks_release_sentinel(root)
            self.assertEqual(sentinel_count, 1)

            # check_blocks_release raises no dangling finding for quoting record
            findings = releases.check_blocks_release(root)
            self.assertEqual(findings, [])

    def test_set_blocks_release_line_remove_front_matter_only(self) -> None:
        """E-08(f) / V-07: set_blocks_release_line(text, '-') removes front-matter line only."""
        text = (
            "- Id: bbb333\n"
            "- Status: open\n"
            "- Blocks-Release: next\n"
            "- Set: demo\n\n"
            "## Description\n"
            "Body quote:\n"
            "- Blocks-Release: other_val\n"
        )
        removed = releases.set_blocks_release_line(text, "-")
        self.assertNotIn("- Blocks-Release: next", removed)
        self.assertIn("- Blocks-Release: other_val", removed)

        # Body remains byte-identical
        body_orig = text.partition("## Description")[2]
        body_rem = removed.partition("## Description")[2]
        self.assertEqual(body_orig, body_rem)

    def test_ipd_lint_board_bounding(self) -> None:
        """E-06 / V-06: ipd_lint board labels [blocking] only for front-matter gate."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan_dir = root / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True)

            p_body = plan_dir / "20261001-test-01-ppp111-body.ipd.md"
            p_body.write_text(
                "# Title\n\n"
                "- Id: ppp111\n"
                "- Status: to-review\n"
                "- Set: testset\n\n"
                "## Workflow history\n"
                "- 2026-10-01: - Blocks-Release: next\n",
                encoding="utf-8",
            )

            p_ctrl = plan_dir / "20261001-test-02-ppp222-ctrl.ipd.md"
            p_ctrl.write_text(
                "# Title\n\n"
                "- Id: ppp222\n"
                "- Status: to-review\n"
                "- Set: testset\n"
                "- Blocks-Release: next\n\n"
                "## Workflow history\n"
                "- 2026-10-01: created\n",
                encoding="utf-8",
            )

            args = argparse.Namespace(
                board=True,
                paths=[str(p_body), str(p_ctrl)],
                repo_root=root,
                dir=str(root),
                color=False,
                unfiltered=False,
            )

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                ipd_lint.run_lint(args)
            finally:
                sys.stdout = old_stdout

            output = buf.getvalue()
            # Find the row for each plan in the board output
            for line in output.splitlines():
                if "ppp111" in line:
                    self.assertNotIn("[blocking]", line)
                    self.assertFalse(line.startswith("- >"))
                elif "ppp222" in line:
                    self.assertIn("[blocking]", line)
                    self.assertIn(">", line)

    def test_check_release_gates_at_rest_bounding(self) -> None:
        """E-06 / V-06: at-rest arm of check_release_gate_consistency ignores body quote."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            releases.create_release(root, "2.0.0", "planned release")

            cfg_dir = root / ".aw" / "config"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"cutovers": {"release_gate_at_rest": "2026-10-01"}}),
                encoding="utf-8",
            )

            done_dir = root / ".aw" / "records" / "backlog" / "done"
            done_dir.mkdir(parents=True)

            # Done item with body-quoted gate only
            item_body = done_dir / "20261001-done01-01-done01-bug.backlog.md"
            item_body.write_text(
                "- Id: done01\n"
                "- Status: done\n"
                "- Set: testset\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Done item with body quote\n\n"
                "## Workflow history\n"
                "- 2026-10-01 done: note\n"
                "- Blocks-Release: next\n",
                encoding="utf-8",
            )

            # Done item with real front-matter gate and no handoff
            item_ctrl = done_dir / "20261001-done02-01-done02-bug.backlog.md"
            item_ctrl.write_text(
                "- Id: done02\n"
                "- Status: done\n"
                "- Blocks-Release: next\n"
                "- Set: testset\n"
                "- Priority: high\n"
                "- Work-Kind: bug\n"
                "- Summary: Done item with real gate\n\n"
                "## Workflow history\n"
                "- 2026-10-01 done: note\n",
                encoding="utf-8",
            )

            findings = check_engine.check_release_gate_consistency(root, at_rest=True)
            finding_locs = {f.location for f in findings}

            # item_body is NOT flagged because it carries no front-matter gate
            self.assertFalse(any("done01" in loc for loc in finding_locs))
            # item_ctrl IS flagged because it was closed without handoff/satisfaction
            self.assertTrue(any("done02" in loc for loc in finding_locs))
