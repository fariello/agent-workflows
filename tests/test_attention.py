"""Tests for the read-only `aw attention` scanner (Set attnview, Order 03).

Stdlib unittest, zero deps. Verifies scan/classification, mapping, byte-determinism under varied
env, fail-closed --check with named violations, output safety, no-write invariant, and that the
existing per-tree checks are unaffected.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import attention as att
from agent_workflows import attention_contract as A


def _mk_repo(tmp: Path):
    """Build a tiny tracked-tree repo: one clean spec, one plan, one research doc."""

    specs = tmp / ".agents" / "docs" / "specs"
    research = tmp / ".agents" / "docs" / "research"
    plans = tmp / ".agents" / "plans" / "pending"
    for d in (specs, research, plans):
        d.mkdir(parents=True, exist_ok=True)
    (specs / "s.md").write_text(
        "# Spec: s\n\n- Date: 2026-08-08\n- Status: approved\n- Author: t\n\n## Body\n\nx\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
        encoding="utf-8",
    )
    (plans / "20260808-x-01-abc123-p.md").write_text(
        "# IPD: p\n\n- Status: draft\n- Id: abc123\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
        encoding="utf-8",
    )
    (research / "20260808-r-00-def456-r.survey.md").write_text(
        "---\nid: def456\nstatus: active\nkind: survey\n---\n\n# r\n\n## Workflow history\n- 2026-08-08 draft (t): x.\n",
        encoding="utf-8",
    )
    return tmp


class ScanTests(unittest.TestCase):
    def test_classifies_and_maps(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            items, drift = att.scan(root)
            self.assertEqual(drift, [], f"expected clean, got {drift}")
            by_tree = {it.tree: it for it in items}
            self.assertEqual(
                by_tree["specs"].attention_class, "ready"
            )  # approved -> ready
            self.assertEqual(
                by_tree["plans"].attention_class, "ready"
            )  # draft -> ready
            self.assertEqual(
                by_tree["research"].attention_class, "active"
            )  # active -> active (live source)

    def test_scans_external_aw_actions(self):
        import tempfile
        from agent_workflows.actions import ActionManager

        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "myrepo"
            root.mkdir(parents=True, exist_ok=True)
            _mk_repo(root)

            mgr = ActionManager(target_repo=str(root))
            mgr.create_action("setup-repo", 1, "Setup Repo", "Desc")

            items, drift = att.scan(root)
            self.assertEqual(drift, [])
            action_items = [it for it in items if it.tree == "actions"]
            self.assertEqual(len(action_items), 1)
            self.assertEqual(action_items[0].id, "setup-repo")
            self.assertEqual(
                action_items[0].path, "aw-state/actions/open/setup-repo-v1.md"
            )
            self.assertEqual(action_items[0].attention_class, "ready")

    def test_unclassified_and_violations(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            # an unknown-status spec
            (root / ".agents" / "docs" / "specs" / "bad.md").write_text(
                "# Spec: bad\n\n- Status: frobnicated\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )
            # a file under a scanned root (.agents/docs) but no inventoried tree
            odd = root / ".agents" / "docs" / "weird"
            odd.mkdir(parents=True)
            (odd / "z.md").write_text("hello\n", encoding="utf-8")
            items, drift = att.scan(root)
            rules = {x.rule for x in drift}
            self.assertIn("attention.unknown-status", rules)
            self.assertIn("attention.unclassified-tree", rules)

    def test_determinism_across_env(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            items1, drift1 = att.scan(root)
            out1 = att.render_json(items1, drift1)
            with mock.patch.dict(
                os.environ,
                {"TZ": "Asia/Kolkata", "LANG": "de_DE.UTF-8", "LC_ALL": "de_DE.UTF-8"},
            ):
                items2, drift2 = att.scan(root)
                out2 = att.render_json(items2, drift2)
            self.assertEqual(out1, out2)
            self.assertTrue(out1.endswith("\n"))

    def test_json_shape_and_validity(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            items, drift = att.scan(root)
            obj = json.loads(att.render_json(items, drift))
            # awdoctorfix Order 01: schema bumped to 2 (items gained priority + blocks_release).
            self.assertEqual(obj["schema_version"], 2)
            self.assertTrue(obj["valid"])
            self.assertEqual(obj["violations"], [])
            self.assertTrue(all("attention_class" in it for it in obj["items"]))
            self.assertTrue(all("priority" in it for it in obj["items"]))
            self.assertTrue(all("blocks_release" in it for it in obj["items"]))

    def test_check_fail_closed(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            args = argparse.Namespace(
                dir=str(root), check=True, agent=False, format=None, all=False
            )
            with redirect_stdout(io.StringIO()):
                rc = att.run(args)
            self.assertEqual(rc, 0)
            (root / ".agents" / "docs" / "specs" / "bad.md").write_text(
                "# Spec: bad\n\n- Status: deferred\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )  # deferred without a gate
            args = argparse.Namespace(
                dir=str(root), check=True, agent=True, format=None, all=False
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = att.run(args)
            self.assertEqual(rc, 1)
            self.assertIn("attention.gate-missing", buf.getvalue())

    def test_board_hides_done_parked_by_default(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            (root / ".agents" / "docs" / "specs" / "done.md").write_text(
                "# Spec: done\n\n- Status: implemented\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )
            items, drift = att.scan(root)
            board = att.render_board(items, drift, show_all=False)
            self.assertIn("hidden; use --all", board)
            board_all = att.render_board(items, drift, show_all=True)
            self.assertNotIn("hidden; use --all", board_all)

    def test_plain_render_keeps_machine_readable_tree_bracket(self):
        # Non-TTY / no-color view: the stable "- [tree] path (status){gate}" form agents parse.
        from agent_workflows import term as T

        items = [
            att.Item(
                "i1",
                ".agents/docs/research/r.md",
                "research",
                "active",
                A.ACTIVE,
                None,
                None,
            ),
            att.Item(
                "i2",
                ".agents/docs/specs/s.md",
                "specs",
                "deferred",
                A.BLOCKED,
                {"kind": "artifact", "ref": "TODO.md"},
                None,
            ),
        ]
        board = att.render_board(items, [], term=T.Term(color=False))
        self.assertIn("- [research] .agents/docs/research/r.md (active)", board)
        self.assertIn(
            "- [specs] .agents/docs/specs/s.md (deferred)  [gate artifact: TODO.md]",
            board,
        )
        self.assertNotIn("\033[", board)  # no ANSI when color off

    def test_colored_render_drops_bracket_colors_and_folds_gate(self):
        from agent_workflows import term as T

        items = [
            att.Item(
                "i1",
                ".agents/docs/research/r.md",
                "research",
                "active",
                A.ACTIVE,
                None,
                None,
            ),
            att.Item(
                "i2",
                ".agents/docs/specs/s.md",
                "specs",
                "deferred",
                A.BLOCKED,
                {"kind": "artifact", "ref": "TODO.md"},
                None,
            ),
        ]
        board = att.render_board(items, [], term=T.Term(color=True))
        stripped = re.sub(r"\033\[[0-9;]*m", "", board)
        # No machine bracket and no trailing tree tag in the human view.
        self.assertNotIn("[research]", board)
        # Status is 256-colored + bold.
        self.assertIn("\033[1;38;5;39mactive\033[0m", board)  # active azure
        # awdoctorfix Order 02: the default colored board shows the compact identity stem (not the
        # folded prefix / full path); a non-clustered name like `r.md` falls back to `r`. A None
        # last_history_at yields a '?' age marker.
        self.assertNotIn(".agents/docs/research/r.md (active)", stripped)
        self.assertRegex(stripped, r"- \??\s*active\s+r")
        # Blocked gate folds into the section header, not each line.
        self.assertIn("## blocked (1) in TODO.md", board)
        self.assertNotIn("[gate artifact: TODO.md]", board)
        # No trailing " tree" tag after the status.
        self.assertNotIn("(active) research", stripped)

    def test_writes_nothing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            att.scan(root)
            att.run(
                argparse.Namespace(
                    dir=str(root), check=False, agent=False, format="json", all=False
                )
            )
            after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(set(before), set(after), "no files created/removed")
            for p, b in before.items():
                self.assertEqual(after[p], b, f"{p} changed")


if __name__ == "__main__":
    unittest.main()
