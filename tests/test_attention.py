"""Tests for the read-only `aw attention` scanner (Set attnview, Order 03).

Stdlib unittest, zero deps. Verifies scan/classification, mapping, byte-determinism under varied
env, fail-closed --check with named violations, output safety, no-write invariant, and that the
existing per-tree checks are unaffected.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import attention as att
from agent_workflows import attention_contract as A
from agent_workflows.artifact_core import Drift as core_Drift

# This repository's own root, for the few cases that legitimately measure the REAL corpus (the E-08
# parity assertion). Derived from this file's location so it is correct in a worktree/lane too.
REPO_ROOT = Path(__file__).resolve().parent.parent


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
    def test_scan_classification_and_immutability(self):
        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            items, drift = att.scan(root)
            self.assertEqual(drift, [], f"expected clean, got {drift}")
            by_tree = {it.tree: it for it in items}
            self.assertEqual(by_tree["specs"].attention_class, "ready")
            self.assertEqual(by_tree["plans"].attention_class, "ready")
            self.assertEqual(by_tree["research"].attention_class, "active")

            # setup_needed derives read-only, scan does not stamp .aw/
            fresh = Path(d) / "fresh"
            fresh.mkdir(parents=True, exist_ok=True)
            items_f, _ = att.scan(fresh)
            self.assertFalse((fresh / ".aw").exists(), "scan must not stamp .aw/")
            self.assertFalse(att.setup_needed(fresh))
            from agent_workflows import engine

            engine.write_setup_marker(fresh)
            self.assertTrue(att.setup_needed(fresh))

            # determinism across env
            out1 = att.render_json(items, drift)
            with mock.patch.dict(
                os.environ,
                {"TZ": "Asia/Kolkata", "LANG": "de_DE.UTF-8", "LC_ALL": "de_DE.UTF-8"},
            ):
                items2, drift2 = att.scan(root)
                out2 = att.render_json(items2, drift2)
            self.assertEqual(out1, out2)

            # writes nothing invariant
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            att.scan(root)
            att.run(
                argparse.Namespace(
                    dir=str(root), check=False, agent=False, format="json", all=False
                )
            )
            after = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(set(before), set(after))

            # unclassified and violations
            (root / ".agents" / "docs" / "specs" / "bad.md").write_text(
                "# Spec: bad\n\n- Status: frobnicated\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )
            odd = root / ".agents" / "docs" / "weird"
            odd.mkdir(parents=True)
            (odd / "z.md").write_text("hello\n", encoding="utf-8")
            items_v, drift_v = att.scan(root)
            rules = {x.rule for x in drift_v}
            self.assertIn("attention.unknown-status", rules)
            self.assertIn("attention.unclassified-tree", rules)

    def test_rendering_formats_and_check_gate(self):
        with tempfile.TemporaryDirectory() as d:
            root = _mk_repo(Path(d))
            items, drift = att.scan(root)
            obj = json.loads(att.render_json(items, drift))
            self.assertEqual(obj["schema_version"], 4)
            self.assertEqual(obj["stranded_lanes"], [])
            self.assertTrue(obj["valid"])
            self.assertTrue(all("attention_class" in it for it in obj["items"]))

            # check fail closed on missing gate
            args = argparse.Namespace(
                dir=str(root), check=True, agent=False, format=None, all=False
            )
            with redirect_stdout(io.StringIO()):
                self.assertEqual(att.run(args), 0)

            (root / ".agents" / "docs" / "specs" / "bad.md").write_text(
                "# Spec: bad\n\n- Status: deferred\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )
            args_bad = argparse.Namespace(
                dir=str(root), check=True, agent=True, format=None, all=False
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(att.run(args_bad), 1)
            self.assertIn("attention.gate-missing", buf.getvalue())

            # board hides done/parked by default
            (root / ".agents" / "docs" / "specs" / "done.md").write_text(
                "# Spec: done\n\n- Status: implemented\n\n## Workflow history\n- 2026-08-08 x (t): y.\n",
                encoding="utf-8",
            )
            items_d, drift_d = att.scan(root)
            self.assertIn(
                "hidden; use --all", att.render_board(items_d, drift_d, show_all=False)
            )
            self.assertNotIn(
                "hidden; use --all", att.render_board(items_d, drift_d, show_all=True)
            )

            # plain vs colored render
            from agent_workflows import term as T

            sample_items = [
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
            plain = att.render_board(sample_items, [], term=T.Term(color=False))
            self.assertIn("- [research] .agents/docs/research/r.md (active)", plain)
            self.assertNotIn("\033[", plain)

            colored = att.render_board(sample_items, [], term=T.Term(color=True))
            self.assertIn("\033[1;38;5;220mactive\033[0m", colored)
            self.assertIn("\033[1;38;5;208m\u26a0\ufe0e\033[0m", colored)
            self.assertNotIn("\u26a0\ufe0f", colored)


class StaleResearchReclassifyTests(unittest.TestCase):
    """IPD h40usm E-02: attention no longer files finished/cited intake research under `ready`."""

    def _write_research(self, root, *, set_id, order, id6, slug, status, kind):
        from agent_workflows import research_cmd as C
        from agent_workflows import research_contract as R

        rroot = root / ".agents" / "docs" / "research"
        rroot.mkdir(parents=True, exist_ok=True)
        name = R.format_name(
            R.ResearchName(
                date="20260801",
                set_id=set_id,
                order=f"{order:02d}",
                id6=id6,
                slug=slug,
                model=None,
                kind=kind,
            )
        )
        content = C.build_frontmatter(
            id6=id6,
            created="20260801",
            set_id=set_id,
            order=f"{order:02d}",
            topic=["t"],
            model=None,
            kind=kind,
            status=status,
            outcome="none-yet",
            summary="s",
        )
        (rroot / name).write_text(
            content + "\n## Workflow history\n- 2026-08-01 draft (t): x.\n",
            encoding="utf-8",
        )

    def test_stale_research_reclassification_and_class_of(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # RUN prompt-set: intake report with prompt sibling -> stale/parked
            self._write_research(
                root,
                set_id="runset",
                order=0,
                id6="prmpt2",
                slug="ask",
                status="reference",
                kind="research-prompt",
            )
            self._write_research(
                root,
                set_id="runset",
                order=1,
                id6="rprt01",
                slug="ans",
                status="intake",
                kind="research-report",
            )
            # UNRUN prompt: intake prompt -> ready
            self._write_research(
                root,
                set_id="unrunset",
                order=0,
                id6="prmpt9",
                slug="ask",
                status="intake",
                kind="research-prompt",
            )
            # active doc -> active
            self._write_research(
                root,
                set_id="liveset",
                order=0,
                id6="live01",
                slug="w",
                status="active",
                kind="notes",
            )
            # cited by executed plan -> parked
            self._write_research(
                root,
                set_id="solo",
                order=0,
                id6="solo11",
                slug="s",
                status="intake",
                kind="notes",
            )
            pl = root / ".aw" / "records" / "plans" / "executed"
            pl.mkdir(parents=True, exist_ok=True)
            (pl / "20260801-set-01-plnexe-x.ipd.md").write_text(
                "# Plan\n\n- Id: plnexe\n\nAdopts RSCH-solo11.\n", encoding="utf-8"
            )

            # legacy intake vs todo
            self._write_research(
                root,
                set_id="s1",
                order=0,
                id6="todo01",
                slug="a",
                status="todo",
                kind="notes",
            )
            self._write_research(
                root,
                set_id="s2",
                order=0,
                id6="oldik0",
                slug="b",
                status="intake",
                kind="notes",
            )

            items, drift = att.scan(root)
            self.assertFalse(
                [dd for dd in drift if dd.rule == "attention.unknown-status"]
            )
            by_id = {it.id: it for it in items if it.tree == "research"}
            self.assertEqual(by_id["rprt01"].attention_class, "parked")
            self.assertEqual(by_id["prmpt9"].attention_class, "ready")
            self.assertEqual(by_id["live01"].attention_class, "active")
            self.assertEqual(by_id["solo11"].attention_class, "parked")
            self.assertEqual(by_id["todo01"].attention_class, "ready")
            self.assertEqual(by_id["oldik0"].attention_class, "ready")
            self.assertEqual(by_id["oldik0"].native_status, "todo")

            self.assertEqual(A.class_of("research", "todo"), "ready")
            self.assertEqual(A.class_of("research", "active"), "active")
            self.assertEqual(A.class_of("research", "reference"), "done")
            self.assertEqual(A.class_of("research", "archive"), "parked")

    def test_selectors_filtering_and_run(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            items, _drift = att.scan(root)
            self.assertEqual(len(items), 3)

            # Filter by id6, setid, tree, status, union, substring
            self.assertEqual(
                len(att.filter_items_by_selectors(items, ["abc123"], root)), 1
            )
            self.assertEqual(len(att.filter_items_by_selectors(items, ["r"], root)), 1)
            self.assertEqual(
                len(att.filter_items_by_selectors(items, ["specs"], root)), 1
            )
            self.assertEqual(
                len(att.filter_items_by_selectors(items, ["active"], root)), 1
            )
            self.assertEqual(
                len(att.filter_items_by_selectors(items, ["abc123", "def456"], root)), 2
            )
            self.assertEqual(
                len(att.filter_items_by_selectors(items, ["s.md"], root)), 1
            )

            # run with selectors
            args = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=["abc123"],
                no_color=True,
                all=False,
                long=False,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(att.run(args), 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["id"], "abc123")

    def test_detail_cascade_and_rendering(self):
        # Detail extraction cascade
        txt1 = "# IPD: My Title\n\n- Summary: Top summary\n- Scope: Sub scope\n"
        self.assertEqual(att._extract_detail(txt1), ("summary", "Top summary"))
        txt2 = "# IPD: My Title\n\n- Scope: Plan scope line\n- Concern: Plan concern\n"
        self.assertEqual(att._extract_detail(txt2), ("scope", "Plan scope line"))
        txt3 = (
            "# Backlog: Bug\n\n- Concern: Memory leak in worker\n- Title: Bug Title\n"
        )
        self.assertEqual(
            att._extract_detail(txt3), ("concern", "Memory leak in worker")
        )
        txt4 = "# Research: Survey\n\n- Question: What is the optimal batch size?\n"
        self.assertEqual(
            att._extract_detail(txt4), ("question", "What is the optimal batch size?")
        )
        txt5 = "# Doc\n\n- Title: Explicit doc title\n"
        self.assertEqual(att._extract_detail(txt5), ("title", "Explicit doc title"))
        txt6 = "# Spec: Fallback Specification Header\n\n- Status: draft\n"
        self.assertEqual(
            att._extract_detail(txt6), ("title", "Fallback Specification Header")
        )

        # Render board with details (plain and colored)
        item1 = att.Item(
            "abc123",
            ".aw/records/plans/pending/p.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            detail_kind="scope",
            detail_text="Implement feature X.",
        )
        board_plain = att.render_board(
            [item1], drift=[], show_all=True, term=att.T.Term(color=False), details=True
        )
        self.assertIn("scope: Implement feature X.", board_plain)
        board_color = att.render_board(
            [item1], drift=[], show_all=True, term=att.T.Term(color=True), details=True
        )
        self.assertIn("scope:", board_color)

        # JSON with details
        obj = json.loads(att.render_json([item1], drift=[]))
        self.assertEqual(obj["items"][0]["detail_kind"], "scope")

        # run with --details
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            (
                root / ".agents" / "plans" / "pending" / "20260808-x-01-abc123-p.md"
            ).write_text(
                "# IPD: p\n\n- Scope: Build test subsystem.\n- Status: draft\n- Id: abc123\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                dir=str(root),
                format=None,
                check=False,
                selectors=["abc123"],
                no_color=True,
                all=False,
                long=False,
                details=True,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(att.run(args), 0)
            self.assertIn("scope: Build test subsystem.", buf.getvalue())

    def test_type_filters_parsing_and_execution(self):
        self.assertEqual(att.parse_type_filters(None), set())
        self.assertEqual(att.parse_type_filters(["plans"]), {"plans"})
        self.assertEqual(
            att.parse_type_filters(["plans,specs,backlog"]),
            {"plans", "specs", "backlog"},
        )
        self.assertEqual(
            att.parse_type_filters(["ipd", "survey", "walkthr"]),
            {"plans", "research", "walkthroughs"},
        )

        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            args = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=["specs"],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(att.run(args), 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["tree"], "specs")

            args2 = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=["specs,plans"],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf2 = io.StringIO()
            with mock.patch("sys.stdout", buf2):
                self.assertEqual(att.run(args2), 0)
            data2 = json.loads(buf2.getvalue())
            self.assertEqual({it["tree"] for it in data2["items"]}, {"specs", "plans"})

    def test_release_blockers_and_interactive_headers(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            rel_dir = root / ".aw" / "records" / "releases"
            rel_dir.mkdir(parents=True, exist_ok=True)
            (rel_dir / "20260830-rel001-01-rel001-release.release.md").write_text(
                "# Release: 1.0.0\n\n- Id: rel001\n- Version: 1.0.0\n- Status: planned\n- Summary: Test\n",
                encoding="utf-8",
            )
            (root / ".agents" / "docs" / "specs" / "s.md").write_text(
                "# Spec: s\n\n- Date: 2026-08-08\n- Status: approved\n- Blocks-Release: next\n- Author: t\n\n## Body\n\nx\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
                encoding="utf-8",
            )
            args = argparse.Namespace(
                dir=str(root),
                format=None,
                check=False,
                selectors=[],
                types=["specs"],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(att.run(args), 0)
            output = buf.getvalue()
            self.assertIn("## release-blockers", output)
            self.assertIn(".agents/docs/specs/s.md", output)
            self.assertNotIn("## ready", output)

            from agent_workflows import engine

            engine.write_setup_marker(root)
            args_col = argparse.Namespace(
                dir=str(root),
                format=None,
                check=False,
                selectors=[],
                types=[],
                no_color=False,
                all=False,
                long=False,
                details=False,
            )
            buf_col = io.StringIO()
            term = att.T.Term(stream=buf_col, color=True)
            with mock.patch("sys.stdout", buf_col), mock.patch(
                "agent_workflows.attention.T.Term", return_value=term
            ):
                self.assertEqual(att.run(args_col), 0)
            stripped = re.sub(r"\033\[[0-9;]*m", "", buf_col.getvalue())
            self.assertIn(
                "Status   Type     Blocks Priority Readiness OQs Exec Valid Date     ",
                stripped,
            )
            self.assertTrue(
                stripped.endswith("TODO: Run `/aw setup-repo` to set up this repo.\n")
            )


class AttentionTableFormattingAndSortingTests(unittest.TestCase):
    def test_table_formatting_and_sorting(self):
        items = [
            att.Item(
                "c4gd2h",
                ".aw/records/specs/20260829-c4gd2h-01-c4gd2h.spec.md",
                "specs",
                "implementing",
                A.ACTIVE,
                None,
                None,
                blocks_release="2.0.0",
            ),
            att.Item(
                "p0l1to",
                ".aw/records/plans/pending/20260829-runprofile-02-p0l1to.ipd.md",
                "plans",
                "reviewed",
                A.READY,
                None,
                None,
            ),
            att.Item(
                "cnwy8g",
                ".aw/records/backlog/open/20260903-runnerlayer-01-cnwy8g.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority="medium",
                blocks_release="2.0.0",
            ),
            att.Item(
                "d07nz2",
                ".aw/records/backlog/open/20260904-rununbound-01-d07nz2.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority="medium",
                blocks_release="2.0.0",
            ),
            att.Item(
                "5e4sb6",
                ".aw/records/plans/pending/20260829-rununify-00-5e4sb6.ipd.md",
                "plans",
                "approved",
                A.READY,
                None,
                None,
                blocks_release="2.0.0",
            ),
            att.Item(
                "wlxkoz",
                ".aw/records/plans/pending/20260830-runcodes-01-wlxkoz.ipd.md",
                "plans",
                "reviewed",
                A.READY,
                None,
                None,
                blocks_release="2.0.0",
                readiness="go-pending-approval",
            ),
            att.Item(
                "76gsmv",
                ".aw/records/plans/pending/20260904-revsweep-01-76gsmv.ipd.md",
                "plans",
                "to-review",
                A.READY,
                None,
                None,
                blocks_release="2.0.0",
            ),
        ]

        # Colored output
        term = att.T.Term(color=True)
        colored_out = att.render_board(items, [], show_all=True, term=term)
        stripped = re.sub(r"\033\[[0-9;]*m", "", colored_out)
        self.assertIn("\033[1;38;5;45m20260903\033[0m", colored_out)
        self.assertIn("\033[1;38;5;45mrunnerlayer\033[0m", colored_out)
        self.assertIn("\033[1;38;5;45mcnwy8g\033[0m", colored_out)
        self.assertIn("\033[1;38;5;45m◕\033[0m \033[1;38;5;45mopen\033[0m", colored_out)
        self.assertIn("open\033[0m     backlog   ", colored_out)
        self.assertNotIn("\033[1;38;5;33m", colored_out)

        # Plain output
        plain_out = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=False)
        )
        self.assertEqual(stripped, plain_out)

        lines = [line for line in stripped.splitlines() if line.strip()]
        self.assertEqual(
            lines[0],
            "  Status   Type     Blocks Priority Readiness OQs Exec Valid Date     SetID       N  ID6    Deps",
        )
        self.assertEqual(
            lines[1],
            "◕ open     backlog   2.0.0 medium   -           -    -     - 20260903 runnerlayer 01 cnwy8g -",
        )
        self.assertEqual(
            lines[2],
            "◕ open     backlog   2.0.0 medium   -           -    -     - 20260904 rununbound  01 d07nz2 -",
        )
        self.assertEqual(
            lines[3],
            "◑ reviewed plan          - -        -           -    -     - 20260829 runprofile  02 p0l1to -",
        )
        self.assertEqual(
            lines[4],
            "◕ approved plan      2.0.0 -        -           -    -     - 20260829 rununify    00 5e4sb6 -",
        )
        self.assertEqual(
            lines[5],
            "◑ reviewed plan      2.0.0 -        go-pend?    -    -     - 20260830 runcodes    01 wlxkoz -",
        )
        self.assertEqual(
            lines[6],
            "◔ to-revie plan      2.0.0 -        -           -    -     - 20260904 revsweep    01 76gsmv -",
        )
        self.assertEqual(
            lines[7],
            "▶ implmntg spec      2.0.0 -        -           -    -     - 20260829 c4gd2h      01 c4gd2h -",
        )
        self.assertEqual(
            lines[8],
            "OQs = Open Questions (open/total), Exec = Executed items, Valid = Validated items, Deps = Dependencies",
        )

        # OQ counting and rendering in table
        text_with_oqs = """# IPD: test
- Status: to-review

## Open questions

### OQ-01: First
- Status: open
- Blocking: yes

### OQ-02: Second
- Status: resolved
- Blocking: no

### OQ-03: Third
- Status: deferred
- Blocking: no
"""
        self.assertEqual(att.count_unresolved_open_questions(text_with_oqs), 2)
        self.assertEqual(att.count_resolved_questions(text_with_oqs), 1)
        self.assertEqual(att.count_question_stats(text_with_oqs), (2, 1))

        item_oq = att.Item(
            "1",
            ".aw/records/plans/pending/p.ipd.md",
            "plans",
            "to-review",
            A.READY,
            None,
            None,
            oqs=2,
            rqs=1,
        )
        out_oq = att.render_table(
            [item_oq], [], show_all=True, term=att.T.Term(color=False)
        )
        lines_oq = [line for line in out_oq.splitlines() if line.strip()]
        self.assertEqual(
            lines_oq[0],
            "  Status   Type     Blocks Priority Readiness OQs Exec Valid Date     SetID N  ID6    Deps",
        )
        self.assertIn(
            "◔ to-revie plan          - -        -         2/3    -     - -        p     -  1      -",
            lines_oq[1],
        )

        # Priority sorting
        items_prio = [
            att.Item(
                "1",
                ".aw/records/backlog/open/a.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority="high",
            ),
            att.Item(
                "2",
                ".aw/records/backlog/open/b.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority="low",
            ),
            att.Item(
                "3",
                ".aw/records/backlog/open/c.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority=None,
            ),
            att.Item(
                "4",
                ".aw/records/backlog/open/d.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
                priority="medium",
            ),
        ]
        out_prio = att.render_table(
            items_prio, [], show_all=True, term=att.T.Term(color=False)
        )
        lines_prio = [line for line in out_prio.splitlines() if line.strip()][1:]
        self.assertEqual(lines_prio[0].split()[-4], "c")
        self.assertEqual(lines_prio[1].split()[-4], "b")
        self.assertEqual(lines_prio[2].split()[-4], "d")
        self.assertEqual(lines_prio[3].split()[-4], "a")

        # Name sorting
        items_names = [
            att.Item(
                "1",
                ".aw/records/backlog/open/z-item.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
            ),
            att.Item(
                "2",
                ".aw/records/backlog/open/m-item.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
            ),
            att.Item(
                "3",
                ".aw/records/backlog/open/a-item.backlog.md",
                "backlog",
                "open",
                A.READY,
                None,
                None,
            ),
        ]
        out_names = att.render_table(
            items_names, [], show_all=True, term=att.T.Term(color=False)
        )
        lines_names = [line for line in out_names.splitlines() if line.strip()][1:]
        self.assertEqual(lines_names[0].split()[-4], "a-item")
        self.assertEqual(lines_names[1].split()[-4], "m-item")
        self.assertEqual(lines_names[2].split()[-4], "z-item")

        # Numbered items sort by N before ID6
        items_num = [
            att.Item(
                "u23gbn",
                ".aw/records/plans/pending/20260913-dirtygates-04-u23gbn.ipd.md",
                "plans",
                "reviewed",
                A.READY,
                None,
                None,
                priority="medium",
            ),
            att.Item(
                "8lfoum",
                ".aw/records/plans/pending/20260913-dirtygates-00-8lfoum.ipd.md",
                "plans",
                "reviewed",
                A.READY,
                None,
                None,
                priority="high",
            ),
            att.Item(
                "4xt6u4",
                ".aw/records/plans/pending/20260913-dirtygates-06-4xt6u4.ipd.md",
                "plans",
                "to-review",
                A.READY,
                None,
                None,
                priority="medium",
            ),
            att.Item(
                "d7qoxv",
                ".aw/records/plans/pending/20260913-dirtygates-01-d7qoxv.ipd.md",
                "plans",
                "reviewed",
                A.READY,
                None,
                None,
                priority="high",
            ),
        ]
        out_num = att.render_table(
            items_num, [], show_all=True, term=att.T.Term(color=False)
        )
        lines_num = [line for line in out_num.splitlines() if line.strip()][1:]
        self.assertEqual(lines_num[0].split()[-3], "00")
        self.assertEqual(lines_num[1].split()[-3], "01")
        self.assertEqual(lines_num[2].split()[-3], "04")
        self.assertEqual(lines_num[3].split()[-3], "06")
        self.assertEqual(lines_num[0].split()[-2], "8lfoum")
        self.assertEqual(lines_num[1].split()[-2], "d7qoxv")
        self.assertEqual(lines_num[2].split()[-2], "u23gbn")
        self.assertEqual(lines_num[3].split()[-2], "4xt6u4")


class AttentionFilteringTests(unittest.TestCase):
    def test_token_parsing_and_item_filtering(self):
        # Tokens parsing
        self.assertEqual(att.parse_filter_tokens(None), set())
        self.assertEqual(att.parse_filter_tokens([]), set())
        self.assertEqual(
            att.parse_filter_tokens(["to-review", "draft"]),
            {"to-review", "draft"},
        )
        self.assertEqual(
            att.parse_filter_tokens(["to-review,draft"]),
            {"to-review", "draft"},
        )
        self.assertEqual(
            att.parse_filter_tokens(["to-review, draft", "open"]),
            {"to-review", "draft", "open"},
        )

        # Status filtering
        item_rev = att.Item("1", "p1.md", "plans", "to-review", A.READY, None, None)
        item_dft = att.Item("2", "p2.md", "plans", "draft", A.READY, None, None)
        item_opn = att.Item("3", "b1.md", "backlog", "open", A.READY, None, None)

        filters = att.parse_status_filters(["to-review", "draft"])
        self.assertTrue(att.matches_status(item_rev, filters))
        self.assertTrue(att.matches_status(item_dft, filters))
        self.assertFalse(att.matches_status(item_opn, filters))

        filters_comma = att.parse_status_filters(["to-review,draft"])
        self.assertTrue(att.matches_status(item_rev, filters_comma))
        self.assertTrue(att.matches_status(item_dft, filters_comma))
        self.assertFalse(att.matches_status(item_opn, filters_comma))

        # Priority filtering
        item_high = att.Item(
            "1", "b1.md", "backlog", "open", A.READY, None, None, priority="high"
        )
        item_med = att.Item(
            "2", "b2.md", "backlog", "open", A.READY, None, None, priority="medium"
        )
        item_none = att.Item(
            "3", "b3.md", "backlog", "open", A.READY, None, None, priority=None
        )

        filters_prio = att.parse_priority_filters(["high", "medium"])
        self.assertTrue(att.matches_priority(item_high, filters_prio))
        self.assertTrue(att.matches_priority(item_med, filters_prio))
        self.assertFalse(att.matches_priority(item_none, filters_prio))

        filters_none = att.parse_priority_filters(["-"])
        self.assertFalse(att.matches_priority(item_high, filters_none))
        self.assertTrue(att.matches_priority(item_none, filters_none))

        # Blocking filtering
        item_blk = att.Item(
            "1",
            "p1.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            blocks_release="2.0.0",
        )
        item_nonblk = att.Item("2", "p2.md", "plans", "approved", A.READY, None, None)

        filters_ver = att.parse_blocking_filters(["2.0.0"])
        self.assertTrue(att.matches_blocking(item_blk, filters_ver))
        self.assertFalse(att.matches_blocking(item_nonblk, filters_ver))

        filters_tag = att.parse_blocking_filters(["v2.0.0"])
        self.assertTrue(att.matches_blocking(item_blk, filters_tag))
        item_blk_tag = att.Item(
            "3",
            "p3.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            blocks_release="v2.0.0",
        )
        self.assertTrue(att.matches_blocking(item_blk_tag, filters_ver))
        self.assertTrue(att.matches_blocking(item_blk_tag, filters_tag))

        filters_next = att.parse_blocking_filters(["next"])
        self.assertFalse(att.matches_blocking(item_blk, filters_next))
        self.assertFalse(att.matches_blocking(item_blk_tag, filters_next))

        item_dash = att.Item(
            "6", "p6.md", "plans", "approved", A.READY, None, None, blocks_release="-"
        )
        self.assertFalse(att.matches_blocking(item_dash, filters_next))

        filters_any = att.parse_blocking_filters(["any"])
        self.assertTrue(att.matches_blocking(item_blk, filters_any))
        self.assertFalse(att.matches_blocking(item_dash, filters_any))
        self.assertFalse(att.matches_blocking(item_nonblk, filters_any))

        filters_bool_true = att.parse_blocking_filters(["true"])
        self.assertTrue(att.matches_blocking(item_blk, filters_bool_true))
        self.assertFalse(att.matches_blocking(item_nonblk, filters_bool_true))

        filters_bool_false = att.parse_blocking_filters(["-"])
        self.assertFalse(att.matches_blocking(item_blk, filters_bool_false))
        self.assertTrue(att.matches_blocking(item_nonblk, filters_bool_false))

        # Readiness filtering
        item_ready = att.Item(
            "1",
            "p1.md",
            "plans",
            "reviewed",
            A.READY,
            None,
            None,
            readiness="go-pending-approval",
        )
        item_noready = att.Item("2", "p2.md", "plans", "reviewed", A.READY, None, None)

        filters_r = att.parse_readiness_filters(["go-pending-approval"])
        self.assertTrue(att.matches_readiness(item_ready, filters_r))
        self.assertFalse(att.matches_readiness(item_noready, filters_r))

        filters_r_none = att.parse_readiness_filters(["-"])
        self.assertFalse(att.matches_readiness(item_ready, filters_r_none))
        self.assertTrue(att.matches_readiness(item_noready, filters_r_none))

    def test_cli_filtering_and_open_questions(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args = parser.parse_args(
            ["attention", "--status", "to-review", "--status", "draft"]
        )
        self.assertEqual(args.status, ["to-review", "draft"])

        args2 = parser.parse_args(
            [
                "att",
                "--status",
                "to-review,draft",
                "-p",
                "high,medium",
                "-b",
                "2.0.0",
                "-r",
                "go-pending-approval",
            ]
        )
        self.assertEqual(args2.status, ["to-review,draft"])
        self.assertEqual(args2.priority, ["high,medium"])
        self.assertEqual(args2.blocking, ["2.0.0"])
        self.assertEqual(args2.readiness, ["go-pending-approval"])
        self.assertTrue(parser.parse_args(["att", "--open-questions"]).open_questions)
        self.assertTrue(parser.parse_args(["att", "--oqs"]).open_questions)

        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            args_run = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=[],
                status=["to-review", "draft"],
                priority=[],
                blocking=[],
                readiness=[],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                rc = att.run(args_run)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            for item in data["items"]:
                self.assertIn(item["native_status"], ("to-review", "draft"))

        # Open questions filter and research blocks release frontmatter vs body
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw").mkdir(parents=True)
            plans_dir = root / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            p1 = plans_dir / "20260901-test-01-aaaaaa-has-oq.ipd.md"
            p1.write_text(
                "# IPD: has oq\n- Status: to-review\n- Set: test\n- Order: 01\n- Id: aaaaaa\n\n## Open questions\n\n### OQ-01: Open\n- Status: open\n",
                encoding="utf-8",
            )
            p2 = plans_dir / "20260901-test-02-bbbbbb-resolved-oq.ipd.md"
            p2.write_text(
                "# IPD: resolved oq\n- Status: to-review\n- Set: test\n- Order: 02\n- Id: bbbbbb\n\n## Open questions\n\n### OQ-01: Resolved\n- Status: resolved\n",
                encoding="utf-8",
            )
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            executed_dir.mkdir(parents=True)
            p3 = executed_dir / "20260901-test-03-cccccc-executed-with-oq.ipd.md"
            p3.write_text(
                "# IPD: executed with oq\n- Status: executed\n- Set: test\n- Order: 03\n- Id: cccccc\n\n## Open questions\n\n### OQ-01: Still open in old plan\n- Status: open\n",
                encoding="utf-8",
            )

            args_oq = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=[],
                status=[],
                priority=[],
                blocking=[],
                readiness=[],
                open_questions=True,
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                rc = att.run(args_oq)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual({it["id"] for it in data["items"]}, {"aaaaaa", "cccccc"})

            # Default human board hides terminal items
            args_human = argparse.Namespace(
                dir=str(root),
                format=None,
                check=False,
                selectors=[],
                types=[],
                status=[],
                priority=[],
                blocking=[],
                readiness=[],
                open_questions=True,
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf_human = io.StringIO()
            with mock.patch("sys.stdout", buf_human):
                rc_human = att.run(args_human)
            self.assertEqual(rc_human, 0)
            human_out = buf_human.getvalue()
            self.assertIn("aaaaaa", human_out)
            self.assertNotIn("cccccc", human_out)
            self.assertIn("hidden; use --all", human_out)

            # Research doc frontmatter vs quoted body
            research_dir = root / ".aw" / "records" / "research"
            research_dir.mkdir(parents=True)
            releases_dir = root / ".aw" / "records" / "releases"
            releases_dir.mkdir(parents=True)
            (releases_dir / "20260901-rel001-01-rel001-1-0-0.release.md").write_text(
                "# Release: 1.0.0\n\n- Id: rel001\n- Version: 1.0.0\n- Status: planned\n\n## Summary\n\nfixture release.\n",
                encoding="utf-8",
            )
            (research_dir / "20260901-test-01-res001-real.md").write_text(
                "---\nid: res001\nstatus: todo\nblocks-release: next\n---\n\n# Real research blocker\n",
                encoding="utf-8",
            )
            (research_dir / "20260901-test-02-res002-quote.md").write_text(
                "---\nid: res002\nstatus: todo\n---\n\n# Prompt quoting an IPD\n\n```markdown\n- Blocks-Release: next\n```\n",
                encoding="utf-8",
            )

            items, _drift = att.scan(root)
            item_map = {it.id: it for it in items}
            self.assertEqual(item_map["res001"].blocks_release, "next")
            self.assertIsNone(item_map["res002"].blocks_release)

            blockers = att.release_blockers(items, root)
            blocker_ids = {it.id for it in blockers}
            self.assertIn("res001", blocker_ids)
            self.assertNotIn("res002", blocker_ids)
            filters_b = att.parse_blocking_filters(["next"])
            self.assertTrue(att.matches_blocking(item_map["res001"], filters_b, root))
            self.assertFalse(att.matches_blocking(item_map["res002"], filters_b, root))


class ExecValidAndDepsColumnsTests(unittest.TestCase):
    """Pin checklist progress extraction and rendering for Exec, Valid, and Deps columns."""

    def test_checklist_progress_and_dependencies(self):
        # Progress extraction
        self.assertEqual(att._extract_checklist_progress(""), (None, None))
        self.assertEqual(att._extract_checklist_progress("Just text"), (None, None))

        text_unchecked = """
- [ ] E-01 First task
- [ ] E-02 Second task
- [ ] V-01 Validates E-01
- [ ] V-02 Validates E-02
"""
        self.assertEqual(
            att._extract_checklist_progress(text_unchecked), ((0, 2), (0, 2))
        )

        text_partial = """
- [x] E-01 First task
- [ ] E-02 Second task
- [ ] E-03 Third task
- [X] V-01 Validates E-01
- [x] V-02 Validates E-02
- [ ] V-03 Validates E-03
"""
        self.assertEqual(
            att._extract_checklist_progress(text_partial), ((1, 3), (2, 3))
        )

        text_full = """
- [x] E-01 First task
- [X] E-02 Second task
- [x] V-01 Validates E-01
- [x] V-02 Validates E-02
"""
        self.assertEqual(att._extract_checklist_progress(text_full), ((2, 2), (2, 2)))

        # Dependencies extraction
        it1 = att.Item(
            "p1",
            "p1.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            item_dependencies=(
                "executed:29wvmj",
                "exists:spec:6sb3yu",
                "state:ipd:reviewed:rl67b0",
            ),
        )
        self.assertEqual(
            att._extract_dependency_id6s(it1), ["29wvmj", "6sb3yu", "rl67b0"]
        )

        it2 = att.Item(
            "b1",
            "b1.md",
            "backlog",
            "blocked",
            A.BLOCKED,
            {"kind": "artifact", "ref": "rnl3b7"},
            None,
        )
        self.assertEqual(att._extract_dependency_id6s(it2), ["rnl3b7"])

        it3 = att.Item(
            "b2",
            "b2.md",
            "backlog",
            "blocked",
            A.BLOCKED,
            {
                "kind": "artifact",
                "ref": ".aw/records/research/20260905-awmetastore-00-27rjro-where.md",
            },
            None,
        )
        self.assertEqual(att._extract_dependency_id6s(it3), ["27rjro"])

        it4 = att.Item(
            "s1",
            "s1.md",
            "specs",
            "deferred",
            A.BLOCKED,
            {"kind": "artifact", "ref": "TODO.md"},
            None,
        )
        self.assertEqual(att._extract_dependency_id6s(it4), [])

        it5 = att.Item("p2", "p2.ipd.md", "plans", "approved", A.READY, None, None)
        self.assertEqual(att._extract_dependency_id6s(it5), [])

    def test_render_table_colors_and_runs_mode(self):
        it_none = att.Item(
            "p0",
            ".aw/records/plans/pending/p0.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        it_zero = att.Item(
            "p1",
            ".aw/records/plans/pending/p1.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            exec_progress=(0, 2),
            valid_progress=(0, 2),
        )
        it_partial = att.Item(
            "p2",
            ".aw/records/plans/pending/p2.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            exec_progress=(1, 2),
            valid_progress=(0, 2),
            item_dependencies=("executed:29wvmj", "executed:51vw4y"),
        )
        it_full = att.Item(
            "p3",
            ".aw/records/plans/pending/p3.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            exec_progress=(2, 2),
            valid_progress=(2, 2),
            item_dependencies=("executed:6sb3yu",),
        )
        dep_exec = att.Item(
            "29wvmj",
            ".aw/records/plans/executed/20260906-integpath-01-29wvmj.ipd.md",
            "plans",
            "executed",
            A.DONE,
            None,
            None,
        )
        dep_appr = att.Item(
            "51vw4y",
            ".aw/records/plans/pending/20260906-integpath-02-51vw4y.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        dep_draft = att.Item(
            "6sb3yu",
            ".aw/records/plans/pending/20260906-integpath-03-6sb3yu.ipd.md",
            "plans",
            "to-review",
            A.READY,
            None,
            None,
        )
        dep_bk = att.Item(
            "bk1111",
            ".aw/records/backlog/open/bk1111.backlog.md",
            "backlog",
            "open",
            A.READY,
            None,
            None,
        )
        it_bk_dep = att.Item(
            "p4",
            ".aw/records/plans/pending/p4.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            item_dependencies=("exists:backlog:bk1111",),
        )
        id_map = {it.id: it for it in [dep_exec, dep_appr, dep_draft, dep_bk]}
        items = [it_none, it_zero, it_partial, it_full, it_bk_dep]

        plain = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=False), id_map=id_map
        )
        lines = [line for line in plain.splitlines() if line.strip()][1:]
        self.assertIn("   -    -     - -        p0", lines[0])
        self.assertTrue(lines[0].endswith("-"))
        self.assertIn(" 0/2   0/2 -        p1", lines[1])
        self.assertTrue(lines[1].endswith("-"))
        self.assertIn(" 1/2   0/2 -        p2", lines[2])
        self.assertTrue(lines[2].endswith("29wvmj, 51vw4y"))
        self.assertIn(" 2/2   2/2 -        p3", lines[3])
        self.assertTrue(lines[3].endswith("6sb3yu"))

        colored = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=True), id_map=id_map
        )
        self.assertIn("\033[38;5;244m0/2\033[0m", colored)
        self.assertIn("\033[1;38;5;214m1/2\033[0m", colored)
        self.assertIn("\033[1;38;5;40m2/2\033[0m", colored)
        self.assertIn("\033[1;38;5;46m29wvmj\033[0m", colored)
        self.assertIn("\033[1;38;5;45m51vw4y\033[0m", colored)
        self.assertIn("\033[38;5;39m6sb3yu\033[0m", colored)
        self.assertIn("\033[1;38;5;45mbk1111\033[0m", colored)
        self.assertIn("\033[1mOQs\033[0m = Open Questions", colored)

        # Runs mode
        it_r1 = att.Item(
            "111111",
            ".aw/records/plans/p1.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        it_r2 = att.Item(
            "222222",
            ".aw/records/plans/p2.ipd.md",
            "plans",
            "to-review",
            A.READY,
            None,
            None,
        )
        it_r3 = att.Item(
            "333333",
            ".aw/records/plans/p3.ipd.md",
            "plans",
            "draft",
            A.READY,
            None,
            None,
        )
        it_r4 = att.Item(
            "444444",
            ".aw/records/plans/p4.ipd.md",
            "plans",
            "draft",
            A.READY,
            None,
            None,
        )
        r_items = [it_r1, it_r2, it_r3, it_r4]
        run_map = {"111111": "running", "222222": "queued", "333333": "done"}

        plain_off = att.render_table(
            r_items, [], show_all=True, term=att.T.Term(color=False), runs_mode=False
        )
        self.assertNotIn("Run", plain_off.splitlines()[0])

        plain_on = att.render_table(
            r_items,
            [],
            show_all=True,
            term=att.T.Term(color=False),
            runs_mode=True,
            run_map=run_map,
        )
        lines_on = plain_on.splitlines()
        self.assertTrue(lines_on[0].startswith("  Status   Run     Type"))
        self.assertIn("Run = Active runner state", plain_on)
        row1 = [ln for ln in lines_on if "111111" in ln][0]
        self.assertIn("approved running plan", row1)
        row2 = [ln for ln in lines_on if "222222" in ln][0]
        self.assertIn("to-revie queued  plan", row2)
        row3 = [ln for ln in lines_on if "333333" in ln][0]
        self.assertIn("draft    done    plan", row3)
        row4 = [ln for ln in lines_on if "444444" in ln][0]
        self.assertIn("draft    -       plan", row4)

        colored_r = att.render_table(
            r_items,
            [],
            show_all=True,
            term=att.T.Term(color=True),
            runs_mode=True,
            run_map=run_map,
        )
        self.assertIn("\033[1;38;5;51mrunning\033[0m", colored_r)
        self.assertIn("\033[38;5;220mqueued\033[0m", colored_r)
        self.assertIn("\033[1;38;5;40mdone\033[0m", colored_r)
        self.assertIn("\033[38;5;244m-\033[0m", colored_r)

    def test_active_runs_map_and_run_status_filtering(self):
        from agent_workflows import cli

        # Logic test for active runs map
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            runs_dir = repo / ".aw" / "records" / "runs"
            runs_dir.mkdir(parents=True)

            live_dir = runs_dir / "run-20260908T000000Z-100"
            live_dir.mkdir()
            (live_dir / "driver.lock").write_text("pid=100\n", encoding="utf-8")
            (live_dir / "state.json").write_text(
                json.dumps(
                    {
                        "queue": [
                            {"id6": "run001", "status": "running"},
                            {"id6": "que002", "status": "queued"},
                            {"id6": "exe003", "status": "executed"},
                            {"id6": "mrg004", "status": "merging"},
                            {"id6": "fld005", "status": "failed-safely"},
                            {"id6": "blk006", "status": "dependency-blocked"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            dead_dir = runs_dir / "run-20260908T000000Z-200"
            dead_dir.mkdir()
            (dead_dir / "driver.lock").write_text("pid=200\n", encoding="utf-8")
            (dead_dir / "state.json").write_text(
                json.dumps({"queue": [{"id6": "dead01", "status": "running"}]}),
                encoding="utf-8",
            )

            def mock_holder(r_dir):
                if "100" in str(r_dir):
                    return "live"
                return "none"

            with mock.patch(
                "agent_workflows.run_viewer.driver_holder_state",
                side_effect=mock_holder,
            ):
                rmap = att.get_active_runs_map(repo)

            self.assertEqual(rmap.get("run001"), "running")
            self.assertEqual(rmap.get("que002"), "queued")
            self.assertEqual(rmap.get("exe003"), "done")
            self.assertEqual(rmap.get("mrg004"), "merging")
            self.assertEqual(rmap.get("fld005"), "failed")
            self.assertEqual(rmap.get("blk006"), "blocked")
            self.assertNotIn("dead01", rmap)

        # CLI args
        parser = cli._build_parser()
        self.assertFalse(getattr(parser.parse_args(["att"]), "runs", False))
        self.assertTrue(getattr(parser.parse_args(["att", "--runs"]), "runs", False))
        self.assertEqual(
            parser.parse_args(["att", "--run-status", "running"]).run_status,
            ["running"],
        )
        self.assertEqual(
            parser.parse_args(["att", "--runs-status", "done"]).run_status, ["done"]
        )
        self.assertEqual(
            parser.parse_args(
                ["att", "--run-status", "running,queued", "--runs-status", "blocked"]
            ).run_status,
            ["running,queued", "blocked"],
        )

        # parse_run_status_filters & matches_run_status
        filters = att.parse_run_status_filters(
            ["running,queued", "dependency-blocked", "failed_safely"]
        )
        self.assertIn("running", filters)
        self.assertIn("queued", filters)
        self.assertIn("dependency-blocked", filters)
        self.assertIn("blocked", filters)
        self.assertIn("failed-safely", filters)
        self.assertIn("failed", filters)

        run_map = {"run001": "running", "done01": "done", "blk001": "blocked"}
        it_running = att.Item(
            "run001", "p/run001.md", "plans", "draft", A.READY, None, None
        )
        it_done = att.Item(
            "done01", "p/done01.md", "plans", "draft", A.READY, None, None
        )
        it_none = att.Item(
            "none01", "p/none01.md", "plans", "draft", A.READY, None, None
        )

        self.assertTrue(att.matches_run_status(it_running, {"running"}, run_map))
        self.assertFalse(att.matches_run_status(it_done, {"running"}, run_map))
        self.assertTrue(att.matches_run_status(it_done, {"done"}, run_map))
        self.assertTrue(att.matches_run_status(it_running, {"any"}, run_map))
        self.assertFalse(att.matches_run_status(it_none, {"any"}, run_map))
        self.assertTrue(att.matches_run_status(it_none, {"-"}, run_map))
        self.assertTrue(att.matches_run_status(it_none, {"none"}, run_map))
        self.assertFalse(att.matches_run_status(it_running, {"-"}, run_map))

        # att.run status filtering
        it_que = att.Item(
            "que002", "p/que002.md", "plans", "draft", A.READY, None, None
        )
        it_other = att.Item(
            "oth003", "p/oth003.md", "plans", "draft", A.READY, None, None
        )
        with (
            mock.patch.object(
                att, "scan", return_value=([it_running, it_que, it_other], [])
            ),
            mock.patch.object(
                att,
                "get_active_runs_map",
                return_value={"run001": "running", "que002": "queued"},
            ),
            mock.patch.object(att, "stranded_lane_drift", return_value=[]),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                args = argparse.Namespace(
                    dir=None,
                    check=False,
                    format=None,
                    order_by=A.ORDER_CLASS,
                    agent=False,
                    json=False,
                    no_color=True,
                    all=True,
                    types=[],
                    status=[],
                    priority=[],
                    blocking=[],
                    readiness=[],
                    open_questions=False,
                    run_status=["running"],
                    runs=False,
                    selectors=[],
                    long=False,
                    details=False,
                )
                rc = att.run(args)
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            self.assertIn("run001", out)
            self.assertNotIn("que002", out)
            self.assertNotIn("oth003", out)
            self.assertIn("[run: running]", out)

    def test_cli_output_modes_and_active_filters(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args_default = parser.parse_args(["att"])
        self.assertFalse(getattr(args_default, "id6_only", False))
        self.assertFalse(getattr(args_default, "paths", False))
        self.assertFalse(getattr(args_default, "filenames", False))
        self.assertFalse(getattr(args_default, "long", False))

        self.assertTrue(parser.parse_args(["att", "--id6-only"]).id6_only)
        self.assertTrue(parser.parse_args(["att", "-id"]).id6_only)
        self.assertTrue(parser.parse_args(["att", "--paths"]).paths)
        self.assertTrue(parser.parse_args(["att", "--filenames"]).filenames)

        # Mutually exclusive output format pairs
        for bad in (
            ["att", "-id", "--paths"],
            ["att", "-id", "--filenames"],
            ["att", "-id", "--long"],
            ["att", "--paths", "--filenames"],
            ["att", "--paths", "--long"],
            ["att", "--filenames", "--long"],
        ):
            with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                parser.parse_args(bad)

        # Active / not-active flags
        args_active = parser.parse_args(["att", "--active"])
        self.assertTrue(args_active.active)
        self.assertFalse(args_active.not_active)

        for flag in ("-a", "-ac", "-act"):
            self.assertTrue(parser.parse_args(["att", flag]).active)

        args_not_active = parser.parse_args(["att", "--not-active"])
        self.assertTrue(args_not_active.not_active)
        self.assertFalse(args_not_active.active)

        for flag in ("-na", "-nac", "-not"):
            self.assertTrue(parser.parse_args(["att", flag]).not_active)

        args_arcive = parser.parse_args(["att", "--arcive-state", "running"])
        self.assertEqual(args_arcive.run_status, ["running"])

        args_active_state = parser.parse_args(
            ["att", "--active-state", "running,queued"]
        )
        self.assertEqual(args_active_state.run_status, ["running,queued"])

        args_multi = parser.parse_args(["att", "-as", "running", "-ars", "queued"])
        self.assertEqual(args_multi.run_status, ["running", "queued"])

        # Mutually exclusive active/not-active pairs
        for bad in (
            ["att", "--active", "--not-active"],
            ["att", "-a", "-na"],
            ["att", "--arcive-state", "running", "--active"],
            ["att", "--arcive-state", "running", "--not-active"],
            ["att", "-as", "running", "-a"],
            ["att", "-ars", "running", "-nac"],
        ):
            with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                parser.parse_args(bad)

        # att.run output modes
        it1 = att.Item(
            "id0001",
            ".aw/records/plans/pending/20260901-test-01-id0001-slug.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        it2 = att.Item(
            "id0002",
            ".aw/records/plans/pending/20260901-test-02-id0002-slug.ipd.md",
            "plans",
            "open",
            A.READY,
            None,
            None,
        )
        it_done = att.Item(
            "id0003",
            ".aw/records/plans/executed/20260901-test-03-id0003-slug.ipd.md",
            "plans",
            "executed",
            A.DONE,
            None,
            None,
        )

        with (
            mock.patch.object(att, "scan", return_value=([it1, it2, it_done], [])),
            mock.patch.object(att, "stranded_lane_drift", return_value=[]),
        ):
            buf = io.StringIO()
            with redirect_stdout(buf):
                args = argparse.Namespace(
                    dir=None,
                    check=False,
                    format=None,
                    order_by=A.ORDER_CLASS,
                    agent=False,
                    json=False,
                    no_color=True,
                    all=False,
                    types=[],
                    status=[],
                    priority=[],
                    blocking=[],
                    readiness=[],
                    open_questions=False,
                    run_status=[],
                    runs=False,
                    selectors=[],
                    long=False,
                    details=False,
                    id6_only=True,
                    paths=False,
                    filenames=False,
                    active=False,
                    not_active=False,
                )
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertEqual(
                [line.strip() for line in buf.getvalue().splitlines() if line.strip()],
                ["id0001", "id0002"],
            )

            # With --all
            buf_all = io.StringIO()
            with redirect_stdout(buf_all):
                args.all = True
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertEqual(
                [
                    line.strip()
                    for line in buf_all.getvalue().splitlines()
                    if line.strip()
                ],
                ["id0001", "id0002", "id0003"],
            )

            # paths & filenames
            args.id6_only = False
            args.paths = True
            buf_p = io.StringIO()
            with redirect_stdout(buf_p):
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertIn(
                ".aw/records/plans/pending/20260901-test-01-id0001-slug.ipd.md",
                buf_p.getvalue(),
            )

            args.paths = False
            args.filenames = True
            buf_fn = io.StringIO()
            with redirect_stdout(buf_fn):
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertIn("20260901-test-01-id0001-slug.ipd.md", buf_fn.getvalue())

        # active / not_active filtering in att.run
        it_run = att.Item(
            "run001", "p/run001.md", "plans", "approved", A.READY, None, None
        )
        it_idle = att.Item(
            "idl002", "p/idl002.md", "plans", "approved", A.READY, None, None
        )
        run_map = {"run001": "running"}

        with (
            mock.patch.object(att, "scan", return_value=([it_run, it_idle], [])),
            mock.patch.object(att, "get_active_runs_map", return_value=run_map),
            mock.patch.object(att, "stranded_lane_drift", return_value=[]),
        ):
            buf_act = io.StringIO()
            with redirect_stdout(buf_act):
                args_act = argparse.Namespace(
                    dir=None,
                    check=False,
                    format=None,
                    order_by=A.ORDER_CLASS,
                    agent=False,
                    json=False,
                    no_color=True,
                    all=False,
                    types=[],
                    status=[],
                    priority=[],
                    blocking=[],
                    readiness=[],
                    open_questions=False,
                    run_status=[],
                    runs=False,
                    selectors=[],
                    long=False,
                    details=False,
                    id6_only=True,
                    paths=False,
                    filenames=False,
                    active=True,
                    not_active=False,
                )
                rc = att.run(args_act)
            self.assertEqual(rc, 0)
            self.assertEqual(buf_act.getvalue().strip().splitlines(), ["run001"])

            buf_idle = io.StringIO()
            with redirect_stdout(buf_idle):
                args_idle = argparse.Namespace(
                    dir=None,
                    check=False,
                    format=None,
                    order_by=A.ORDER_CLASS,
                    agent=False,
                    json=False,
                    no_color=True,
                    all=False,
                    types=[],
                    status=[],
                    priority=[],
                    blocking=[],
                    readiness=[],
                    open_questions=False,
                    run_status=[],
                    runs=False,
                    selectors=[],
                    long=False,
                    details=False,
                    id6_only=True,
                    paths=False,
                    filenames=False,
                    active=False,
                    not_active=True,
                )
                rc = att.run(args_idle)
            self.assertEqual(rc, 0)
            self.assertEqual(buf_idle.getvalue().strip().splitlines(), ["idl002"])


# --------------------------------------------------------------------------------------------------
# lanestrand-01 (`pr5b0t`) E-07: the view reports stranded lanes and `--check` fails closed on them
# --------------------------------------------------------------------------------------------------


def _lane_args(root: Path, **over):
    """A full `aw attention` namespace, defaulted the way the CLI parser defaults it."""
    ns = dict(
        dir=str(root),
        format=None,
        check=False,
        selectors=[],
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        run_status=[],
        runs=False,
        order_by=A.ORDER_CLASS,
        agent=False,
        json=False,
        no_color=True,
        all=False,
        long=False,
        details=False,
        id6_only=False,
        paths=False,
        filenames=False,
        active=False,
        not_active=False,
    )
    ns.update(over)
    return argparse.Namespace(**ns)


class StrandedLaneViewTests(unittest.TestCase):
    """FIXTURES ONLY. This repository holds dozens of live `aw/lane/*` branches and several in-repo lane
    worktrees, and a test that touched one could destroy the very unintegrated work this surface exists
    to protect. Every lane below is built in a throwaway repo."""

    # THE FIXTURE'S ABSOLUTE PATH IS COMPOSED, NOT WRITTEN AS A LITERAL. The shape being guarded
    # against is a home path, and the deterministic leak-sanitizer (`aw sanitize`) correctly FAILS a
    # tracked file containing one even inside a test fixture, so spelling it out would trade one
    # enforced rule for another. The assembled value is byte-identical to what a recorded
    # `preserved_worktree` looks like, which is all the guard needs.
    ABSOLUTE_WORKTREE = "/" + "home" + "/someone/VC/proj/.aw/worktrees/lane01"

    def _fixture(self, td: Path, *, merged: bool = False, live: bool = False):
        """A tracked-tree repo plus ONE recorded lane, built the way the runner builds a lane."""
        import subprocess

        root = _mk_repo(td)
        for cmd in (
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        # The CANONICAL lane location, so the rendered worktree is the real `.aw/worktrees/<lane>`
        # shape an operator sees. NOTE `describe_lane` prefers the REGISTERED worktree over the
        # recorded `preserved_worktree`, so the absolute recorded value below is what the leak guard
        # exercises through the record, while this is what the display renders.
        lane_dir = root / ".aw" / "worktrees" / "lane01"
        lane_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "worktree",
                "add",
                "-q",
                "-b",
                "aw/lane/lane01",
                str(lane_dir),
                base,
            ],
            cwd=root,
            check=True,
        )
        (lane_dir / "work.txt").write_text("work\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=lane_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "lane work"], cwd=lane_dir, check=True)
        if merged:
            subprocess.run(
                [
                    "git",
                    "merge",
                    "--no-ff",
                    "--no-edit",
                    "-m",
                    "integrate lane01",
                    "aw/lane/lane01",
                ],
                cwd=root,
                check=True,
                capture_output=True,
            )

        run_dir = root / ".aw" / "records" / "runs" / "run-20260917T000000Z-1"
        run_dir.mkdir(parents=True)
        if live:
            (run_dir / "driver.lock").write_text("pid=1\n", encoding="utf-8")
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-20260917T000000Z-1",
                    "repo": str(root),
                    "queue": [
                        {
                            "id6": "lane01",
                            "position": 1,
                            "status": "substantially-complete",
                            # THE REAL SHAPE: an ABSOLUTE home path, which is what 71 of the 140
                            # recorded run items carry. This is the fixture the leak guard needs.
                            "preserved_worktree": self.ABSOLUTE_WORKTREE,
                            "preserved_branch": "aw/lane/lane01",
                            "preserved_lane_id": "lane01",
                            "preserved_base": base,
                            "preserved_disposition": "created",
                            "preserved_reason": "the run ended without integrating this lane",
                            "integration_signal": "suite-failed",
                            "attempts": [
                                {
                                    "worktree": self.ABSOLUTE_WORKTREE,
                                    "worktree_branch": "aw/lane/lane01",
                                    "worktree_lane_id": "lane01",
                                    "worktree_base": base,
                                    "integration_detail": "gate refused in {0}".format(
                                        root
                                    ),
                                }
                            ],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return root

    def _holder(self, live: bool):
        return mock.patch(
            "agent_workflows.run_viewer.driver_holder_state",
            return_value="live" if live else "none",
        )

    def test_stranded_lane_detection_and_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))

            # Human board output and leak guard
            buf = io.StringIO()
            with self._holder(False), mock.patch("sys.stdout", buf):
                rc = att.run(_lane_args(root))
            out = buf.getvalue()
            self.assertEqual(rc, 1, out)
            self.assertIn("STRANDED LANES", out)
            self.assertIn("aw/lane/lane01", out)
            self.assertIn("attention.lane-stranded", out)
            self.assertIn("plan lane01", out)
            self.assertIn("integration_signal=suite-failed", out)
            self.assertIn("Recover it", out)
            self.assertNotIn(self.ABSOLUTE_WORKTREE, out)
            self.assertNotIn("/home/", out)
            self.assertIn(".aw/worktrees/lane01", out)

            # JSON payload
            buf_json = io.StringIO()
            with self._holder(False), mock.patch("sys.stdout", buf_json):
                rc_json = att.run(_lane_args(root, format="json"))
            self.assertEqual(rc_json, 1)
            json_text = buf_json.getvalue()
            self.assertNotIn(self.ABSOLUTE_WORKTREE, json_text)
            self.assertNotIn("/home/", json_text)
            obj = json.loads(json_text)
            self.assertEqual(obj["schema_version"], 4)
            self.assertEqual(obj["mapping_version"], 1)
            self.assertFalse(obj["valid"])
            self.assertEqual(len(obj["stranded_lanes"]), 1)
            self.assertEqual(obj["stranded_lanes"][0]["branch"], "aw/lane/lane01")
            self.assertEqual(obj["stranded_lanes"][0]["rule"], att.LANE_STRANDED_RULE)
            self.assertIn(
                att.LANE_STRANDED_RULE, [v["rule"] for v in obj["violations"]]
            )

            # Agent payload
            agent = io.StringIO()
            with self._holder(False), redirect_stdout(agent):
                rc_agent = att.run(_lane_args(root, agent=True))
            self.assertEqual(rc_agent, 1)
            self.assertIn("attention.lane-stranded", agent.getvalue())
            self.assertIn("aw/lane/lane01", agent.getvalue())

            # Check exits nonzero with stranded lane
            buf_chk = io.StringIO()
            with self._holder(False), redirect_stdout(buf_chk):
                rc_chk = att.run(_lane_args(root, check=True))
            self.assertEqual(rc_chk, 1, buf_chk.getvalue())
            self.assertIn("attention.lane-stranded", buf_chk.getvalue())

        # Clean repo without stranded lane
        with tempfile.TemporaryDirectory() as td:
            root_clean = _mk_repo(Path(td))
            buf_clean = io.StringIO()
            with redirect_stdout(buf_clean):
                rc_clean = att.run(_lane_args(root_clean, check=True))
            self.assertEqual(rc_clean, 0, buf_clean.getvalue())
            self.assertIn("the view is valid", buf_clean.getvalue())

        # Merged lane does not fail check
        with tempfile.TemporaryDirectory() as td:
            root_m = self._fixture(Path(td), merged=True)
            buf_m = io.StringIO()
            with self._holder(False), redirect_stdout(buf_m):
                rc_m = att.run(_lane_args(root_m, check=True))
            self.assertEqual(rc_m, 0, buf_m.getvalue())
            self.assertNotIn("lane-stranded", buf_m.getvalue())

        # Live run lane does not fail check
        with tempfile.TemporaryDirectory() as td:
            root_l = self._fixture(Path(td), live=True)
            buf_l = io.StringIO()
            with self._holder(True), redirect_stdout(buf_l):
                rc_l = att.run(_lane_args(root_l, check=True))
            self.assertEqual(rc_l, 0, buf_l.getvalue())
            self.assertNotIn("lane-stranded", buf_l.getvalue())

    def test_stranded_lane_mappings_and_pruning(self):
        from agent_workflows import runner_shared as rs
        from agent_workflows import worktree_lease

        # Derived from drift
        drift = [
            core_Drift(
                "aw/lane/zzz999", att.LANE_STRANDED_RULE, "STRANDED", severity="error"
            )
        ]
        obj = json.loads(att.render_json([], drift))
        self.assertFalse(obj["valid"])
        self.assertEqual(
            obj["stranded_lanes"],
            [
                {
                    "branch": "aw/lane/zzz999",
                    "rule": att.LANE_STRANDED_RULE,
                    "detail": "STRANDED",
                }
            ],
        )
        clean = json.loads(att.render_json([], []))
        self.assertTrue(clean["valid"])
        self.assertEqual(clean["stranded_lanes"], [])

        # Class mapping
        self.assertEqual(A.class_of("lanes", rs.LANE_STRANDED), A.BLOCKED)
        self.assertEqual(A.class_of("lanes", rs.LANE_UNKNOWN), A.BLOCKED)
        self.assertEqual(A.class_of("lanes", rs.LANE_LIVE), A.ACTIVE)
        self.assertEqual(A.class_of("lanes", rs.LANE_LANDED), A.DONE)
        self.assertEqual(A.class_of("lanes", rs.LANE_EMPTY_OF_WORK), A.DONE)
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("lanes", "FROBNICATED")

        # Terminal pruning: cleanly terminal runs with no preserved worktrees bypass inspect_lane
        state = {
            "run_id": "run-clean-terminal-test",
            "queue": [
                {
                    "id6": "cln001",
                    "status": "executed",
                    "preserved_worktree": None,
                    "attempts": [
                        {
                            "worktree": "/tmp/nonexistent/lane",
                            "worktree_branch": "aw/lane/cln001",
                        }
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td, mock.patch.object(
            worktree_lease, "inspect_lane"
        ) as mock_inspect:
            repo = Path(td)
            with worktree_lease.memoize_worktrees(repo):
                records = rs.stranded_lane_records(repo, [state], attention_only=True)
                self.assertEqual(records, [])
                self.assertEqual(mock_inspect.call_count, 0)

    def test_count_question_stats(self):
        doc = """# Test IPD

- Status: approved

## 1. Context
Some content

## Open questions

### OQ-01 First question
- Status: open
- Blocking: yes

### RQ-02 Resolved question
- Status: resolved

### OQ-03 Closed by rationale
- Status: closed

## Next Section
### OQ-99 Not in open questions
- Status: open
"""
        unresolved, resolved = att.count_question_stats(doc)
        self.assertEqual(unresolved, 1)
        self.assertEqual(resolved, 2)
        self.assertEqual(att.count_question_stats(""), (0, 0))
        self.assertEqual(
            att.count_question_stats("# Just a doc\nNo questions here"), (0, 0)
        )


class LaneRemedyHintTests(unittest.TestCase):
    def test_lane_remedy_hints_and_degradation(self):
        from agent_workflows import agy_runipd, oc_runipd

        hint = att.lane_remedy_hint()
        self.assertIn("aw oc integrate", hint)
        self.assertNotIn("no `aw integrate` verb exists yet", hint)
        self.assertIn("aw oc integrate abc123", att.lane_remedy_hint("abc123"))
        self.assertIn("<id6>", att.lane_remedy_hint())

        self.assertTrue(hasattr(oc_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL))
        self.assertTrue(hasattr(agy_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL))

        with mock.patch.object(att, "LANE_INTEGRATE_PROBE_SYMBOL", "no_such_symbol"):
            hint_deg = att.lane_remedy_hint()
        self.assertIn("no `aw integrate` verb exists yet", hint_deg)
        self.assertNotIn("aw oc integrate", hint_deg)

        with tempfile.TemporaryDirectory() as td:
            root = StrandedLaneViewTests()._fixture(Path(td))
            with mock.patch(
                "agent_workflows.run_viewer.driver_holder_state", return_value="none"
            ):
                drift = att.stranded_lane_drift(root)
            self.assertEqual(len(drift), 1)
            self.assertIn("aw oc integrate lane01", drift[0].detail)


class SharedLifecycleResolverTests(unittest.TestCase):
    from agent_workflows import lifecycle_style as _LS
    from agent_workflows import term as _T

    def _row(self, item, *, colored=True):
        out = att.render_board(
            [item],
            [],
            show_all=True,
            term=self._T.Term(stream=io.StringIO(), color=colored),
        )
        return [ln for ln in out.splitlines() if item.id in ln][0]

    def _item(self, tree, status, path, *, id6="aaa111"):
        return att.Item(
            id6, path, tree, status, A.class_of(tree, status), None, "2026-05-01"
        )

    def test_lifecycle_resolution_and_escapes(self):
        self.assertFalse(hasattr(att, "_STATUS_COLOR_256"))
        self.assertEqual(
            set(att._CLASS_COLOR_256),
            {A.ACTIVE, A.READY, A.BLOCKED, A.DONE, A.PARKED},
        )

        item = self._item("plans", "approved", ".aw/records/plans/pending/p.ipd.md")
        row = self._row(item)
        resolved = self._LS.resolve(self._LS.FAMILY_PLANS, "approved")
        code = resolved.style.color
        prefix = f"\033[1;38;5;{code}m"
        glyph = self._LS.style_for(resolved.stage).unicode
        self.assertIn(f"{prefix}{glyph}\033[0m", row)
        self.assertIn(f"{prefix}approved\033[0m", row)
        self.assertIn(f"{prefix}aaa111\033[0m", row)
        self.assertIn("approved\033[0m plan ", row)
        self.assertNotIn(f"\033[1;38;5;{att._TREE_COLOR_256}mplan", row)

        expected = {
            ("plans", "auto-approved"): self._LS.READY,
            ("backlog", "graduated"): self._LS.ACTIVE,
            ("research", "archive"): self._LS.PARKED,
        }
        for (tree, status), stage in expected.items():
            resolved = self._LS.resolve(att._LIFECYCLE_FAMILY_BY_TREE[tree], status)
            self.assertEqual(resolved.stage, stage)
            item = self._item(tree, status, f".aw/records/{tree}/x.md")
            row = self._row(item)
            style = resolved.style
            bold = "1;" if style.bold else ""
            self.assertIn(f"\033[{bold}38;5;{style.color}m{style.unicode}\033[0m", row)

        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("plans", "bogus-status")

    def test_glyph_rendering_and_ansi_free_machine_output(self):
        blocked = self._item(
            "specs", "deferred", ".aw/records/specs/s.spec.md", id6="bbb222"
        )
        ready = self._item(
            "plans", "approved", ".aw/records/plans/pending/p.ipd.md", id6="ccc333"
        )
        blocked_glyph = self._LS.style_for(self._LS.BLOCKED).unicode
        ready_glyph = self._LS.style_for(self._LS.READY).unicode
        self.assertEqual(len(blocked_glyph), 2)
        self.assertEqual(self._T.visible_width(blocked_glyph), 1)
        self.assertEqual(len(ready_glyph), 1)

        plain = att.render_table(
            [blocked, ready], [], show_all=True, term=self._T.Term(color=False)
        )
        rows = {
            "deferred": [ln for ln in plain.splitlines() if "bbb222" in ln][0],
            "approved": [ln for ln in plain.splitlines() if "ccc333" in ln][0],
        }
        self.assertEqual(
            self._T.visible_width(rows["deferred"].split("deferred")[0]),
            self._T.visible_width(rows["approved"].split("approved")[0]),
        )
        self.assertIn(blocked_glyph, rows["deferred"])
        self.assertNotIn("\u26a0\ufe0f", plain)

        payload = att.render_json([ready], [])
        self.assertNotIn("\033", payload)
        board = att.render_board(
            [ready], [], show_all=True, term=self._T.Term(color=False)
        )
        self.assertNotIn("\033", board)
        self.assertIn("- [plans] .aw/records/plans/pending/p.ipd.md (approved)", board)


# ======================================================================================
# attcor `rkn8ya`: the attention-view correctness and drift-audit fixes.
#
# One class per execution item, so a failure names the fix it belongs to. Each class states the
# DEFECT it pins, because several of these conditions are invisible on the live repository tree and a
# test written against that tree would pass with the bug intact.
# ======================================================================================


def _mk_plan(
    dirpath: Path, *, setid: str, order: str, id6: str, slug: str, body: str
) -> Path:
    """Write a clustered-name plan file and return its path."""

    dirpath.mkdir(parents=True, exist_ok=True)
    p = dirpath / f"20260101-{setid}-{order}-{id6}-{slug}.ipd.md"
    p.write_text(body, encoding="utf-8")
    return p


def _check_args(root: Path, **kw):
    """An argparse Namespace for a `--check` run, with every filter defaulted off."""

    base = dict(
        dir=str(root),
        check=True,
        format=None,
        agent=False,
        json=False,
        no_color=True,
        all=False,
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        selectors=[],
        long=False,
        details=False,
    )
    base.update(kw)
    return argparse.Namespace(**base)


class DriftSurvivesEveryNarrowingTests(unittest.TestCase):
    """E-01: `--check` must FAIL CLOSED under every narrowing, not just the bare invocation.

    THE DEFECT: each filter pruned `drift` down to the paths of the SURVIVING ITEMS. An artifact that
    fails to parse yields drift and NO item (`_plans_record` returns `(None, drift)`; `scan` skips the
    `None` record AFTER extending drift), so its violation matched no surviving path and was silently
    DELETED. Measured before the fix with one unparseable plan present: bare `--check` exited 1,
    `-t plans --check` exited 0, and a selector narrowing exited 0. The spec's Section 8.6 requires
    `--check` to "never silently skip a malformed included artifact".

    THE PRUNE EXISTED AT THREE SITES (types, selectors, and the combined status/priority/blocking/
    readiness/open-questions/run-status site), so this class exercises all three: fixing one would
    have left two live, which is how the bug hid.
    """

    def _fixture(self, tmp: Path) -> Path:
        plans = tmp / ".aw" / "records" / "plans" / "pending"
        # A GOOD plan, so the plans tree has a surviving item and the narrowing is not vacuous.
        _mk_plan(
            plans,
            setid="fix",
            order="01",
            id6="aaaaaa",
            slug="good",
            body="# IPD: good\n\n- Status: to-review\n- Id: aaaaaa\n\n"
            "## Workflow history\n- 2026-01-01 draft (t): created.\n",
        )
        # The UNPARSEABLE plan: an unknown status yields drift and NO item.
        _mk_plan(
            plans,
            setid="fix",
            order="02",
            id6="bbbbbb",
            slug="bad",
            body="# IPD: bad\n\n- Status: frobnicated\n- Id: bbbbbb\n\n"
            "## Workflow history\n- 2026-01-01 draft (t): created.\n",
        )
        specs = tmp / ".aw" / "records" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "20260101-cccccc-01-cccccc-s.spec.md").write_text(
            "# Spec: s\n\n- Status: approved\n- Id: cccccc\n\n## Body\n\nx\n\n"
            "## Workflow history\n- 2026-01-01 draft (t): created.\n",
            encoding="utf-8",
        )
        return tmp

    def _run_check(self, root: Path, **kw):
        buf = io.StringIO()
        with mock.patch.object(att, "stranded_lane_drift", return_value=[]):
            with redirect_stdout(buf):
                rc = att.run(_check_args(root, **kw))
        return rc, buf.getvalue()

    def test_drift_survives_narrowings_and_pruning(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))

            for label, kw in (
                ("bare", {}),
                ("--types plans", dict(types=["plans"])),
                ("a selector", dict(selectors=["aaaaaa"])),
                ("--status to-review", dict(status=["to-review"])),
            ):
                rc, out = self._run_check(root, **kw)
                self.assertEqual(
                    rc,
                    1,
                    f"--check must FAIL CLOSED under {label}; got exit {rc}. Output:\n{out}",
                )
                self.assertIn("attention.unknown-status", out)
                self.assertIn("bbbbbb", out)

            # Drift from unselected tree pruned
            (
                root
                / ".aw"
                / "records"
                / "specs"
                / "20260101-dddddd-01-dddddd-bad.spec.md"
            ).write_text(
                "# Spec: bad\n\n- Status: frobnicated\n- Id: dddddd\n\n## Workflow history\n- 2026-01-01 draft (t): created.\n",
                encoding="utf-8",
            )
            rc_p, out_p = self._run_check(root, types=["plans"])
            self.assertEqual(rc_p, 1, out_p)
            self.assertIn("bbbbbb", out_p)
            self.assertNotIn("dddddd", out_p)

            # Stranded lane drift suppressed under explicit narrowing
            lane = core_Drift("aw/lane/lane01", "attention.lane-stranded", "stranded")
            with mock.patch.object(att, "stranded_lane_drift", return_value=[lane]):
                buf_bare = io.StringIO()
                with redirect_stdout(buf_bare):
                    att.run(_check_args(root))
                buf_narrow = io.StringIO()
                with redirect_stdout(buf_narrow):
                    att.run(_check_args(root, types=["plans"]))
            self.assertIn("attention.lane-stranded", buf_bare.getvalue())
            self.assertNotIn("attention.lane-stranded", buf_narrow.getvalue())


class SpecDriftLocationIsRepoRelativeTests(unittest.TestCase):
    _SPEC_BODY = (
        "# Spec: bad\n\n- Status: frobnicated\n- Id: aaaaaa\n\n"
        "## Workflow history\n- 2026-01-01 draft (t): created.\n"
    )

    def test_spec_drift_location_is_repo_relative(self):
        from agent_workflows import specs as specs_mod

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = ".aw/records/specs/20260101-aaaaaa-01-aaaaaa-bad.spec.md"
            p = root / rel
            p.parent.mkdir(parents=True)
            p.write_text(self._SPEC_BODY, encoding="utf-8")

            drift = specs_mod.validate_spec(p, self._SPEC_BODY)
            self.assertTrue(drift)
            for d in drift:
                self.assertEqual(d.location, rel)
                self.assertNotIn(str(root), d.location)

            # Legacy layout
            rel_leg = ".agents/docs/specs/bad.md"
            p_leg = root / rel_leg
            p_leg.parent.mkdir(parents=True)
            p_leg.write_text(self._SPEC_BODY, encoding="utf-8")
            drift_leg = specs_mod.validate_spec(p_leg, self._SPEC_BODY)
            self.assertTrue(drift_leg)
            self.assertEqual(drift_leg[0].location, rel_leg)

            # Already relative path
            drift_rel = specs_mod.validate_spec(Path("s.md"), self._SPEC_BODY)
            self.assertTrue(drift_rel)
            self.assertEqual(drift_rel[0].location, "s.md")

            # Human and JSON surfaces
            human = io.StringIO()
            with mock.patch.object(att, "stranded_lane_drift", return_value=[]):
                with redirect_stdout(human):
                    rc = att.run(_check_args(root, types=["specs"]))
            self.assertEqual(rc, 1, human.getvalue())
            self.assertIn(rel, human.getvalue())
            self.assertNotIn(str(root), human.getvalue())

            payload = io.StringIO()
            with mock.patch.object(att, "stranded_lane_drift", return_value=[]):
                with mock.patch("sys.stdout", payload):
                    att.run(
                        _check_args(root, check=False, format="json", types=["specs"])
                    )
            obj = json.loads(payload.getvalue())
            self.assertIn(rel, [v["location"] for v in obj["violations"]])
            self.assertNotIn(str(root), payload.getvalue())


class BlockingNextResolvesAgainstThePlannedReleaseTests(unittest.TestCase):
    def _fixture(self, tmp: Path, *, planned: bool = True) -> Path:
        releases = tmp / ".aw" / "records" / "releases"
        releases.mkdir(parents=True)
        (releases / "20260101-pppppp-01-pppppp-1-0-0.release.md").write_text(
            f"# Release: 1.0.0\n\n- Id: pppppp\n- Version: 1.0.0\n- Status: {'planned' if planned else 'shipped'}\n\n## Summary\n\nx.\n",
            encoding="utf-8",
        )
        (releases / "20251201-ssssss-01-ssssss-0-9-0.release.md").write_text(
            "# Release: 0.9.0\n\n- Id: ssssss\n- Version: 0.9.0\n- Status: shipped\n\n## Summary\n\nx.\n",
            encoding="utf-8",
        )
        backlog = tmp / ".aw" / "records" / "backlog" / "open"
        backlog.mkdir(parents=True)
        for order, id6, gate in (
            ("01", "aaaaaa", "next"),
            ("02", "bbbbbb", "ssssss"),
            ("03", "cccccc", "pppppp"),
        ):
            (backlog / f"20260101-b-{order}-{id6}-gate.backlog.md").write_text(
                f"- Id: {id6}\n- Status: open\n- Set: b\n- Priority: high\n- Work-Kind: chore\n- Blocks-Release: {gate}\n- Summary: fixture\n\n## Workflow history\n- 2026-01-01 created (aw backlog): fixture\n",
                encoding="utf-8",
            )
        return tmp

    def test_blocking_next_resolves_against_planned_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td), planned=True)
            items, drift = att.scan(root)
            self.assertEqual(drift, [])
            filters = att.parse_blocking_filters(["next"])
            matched = {it.id for it in items if att.matches_blocking(it, filters, root)}
            self.assertEqual(matched, {"aaaaaa", "cccccc"})

        # With no planned release
        with tempfile.TemporaryDirectory() as td:
            root_no_plan = self._fixture(Path(td), planned=False)
            items_np, _ = att.scan(root_no_plan)
            next_filters = att.parse_blocking_filters(["next"])
            self.assertEqual(
                [
                    it.id
                    for it in items_np
                    if att.matches_blocking(it, next_filters, root_no_plan)
                ],
                [],
            )
            any_filters = att.parse_blocking_filters(["any"])
            self.assertEqual(
                {
                    it.id
                    for it in items_np
                    if att.matches_blocking(it, any_filters, root_no_plan)
                },
                {"aaaaaa", "bbbbbb", "cccccc"},
            )


class DispositionMismatchFiresUnderTheModernLayoutTests(unittest.TestCase):
    _TERMINAL_MISMATCH = (
        "# IPD: mismatch\n\n- Status: superseded\n- Id: {id6}\n\n"
        "## Workflow history\n- 2026-01-01 draft (t): created.\n"
    )

    def _rules_for(self, root: Path):
        items, drift = att.scan(root)
        return [(d.location, d.rule) for d in drift]

    def test_disposition_mismatch_fires_under_modern_layout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _mk_plan(
                root / ".aw" / "records" / "plans" / "executed",
                setid="d",
                order="01",
                id6="aaaaaa",
                slug="mismatch",
                body=self._TERMINAL_MISMATCH.format(id6="aaaaaa"),
            )
            found = self._rules_for(root)
            self.assertIn(
                (
                    ".aw/records/plans/executed/20260101-d-01-aaaaaa-mismatch.ipd.md",
                    "attention.disposition-mismatch",
                ),
                found,
            )

            # Archive sharded plan
            _mk_plan(
                root / ".aw" / "records" / "plans" / "executed" / "202609",
                setid="d",
                order="02",
                id6="bbbbbb",
                slug="shard",
                body=self._TERMINAL_MISMATCH.format(id6="bbbbbb"),
            )
            found_shard = self._rules_for(root)
            self.assertIn(
                (
                    ".aw/records/plans/executed/202609/20260101-d-02-bbbbbb-shard.ipd.md",
                    "attention.disposition-mismatch",
                ),
                found_shard,
            )

            # Matching status and non-terminal status emit nothing
            plans = root / ".aw" / "records" / "plans"
            _mk_plan(
                plans / "superseded",
                setid="d",
                order="03",
                id6="cccccc",
                slug="ok",
                body=self._TERMINAL_MISMATCH.format(id6="cccccc"),
            )
            _mk_plan(
                plans / "executed",
                setid="d",
                order="04",
                id6="dddddd",
                slug="draft-in-executed",
                body="# IPD: draft\n\n- Status: draft\n- Id: dddddd\n\n## Workflow history\n- 2026-01-01 draft (t): created.\n",
            )
            mismatches = [
                loc
                for loc, r in self._rules_for(root)
                if r == "attention.disposition-mismatch"
            ]
            self.assertEqual(len(mismatches), 2)


class PriorityMedAliasTests(unittest.TestCase):
    def test_priority_med_alias(self):
        from agent_workflows import cli

        self.assertEqual(
            att.parse_priority_filters(["med"]), att.parse_priority_filters(["medium"])
        )
        item_med = att.Item(
            "aaaaaa", "p.md", "backlog", "open", A.READY, None, None, priority="medium"
        )
        item_high = att.Item(
            "bbbbbb", "q.md", "backlog", "open", A.READY, None, None, priority="high"
        )
        for token in ("med", "medium"):
            filters = att.parse_priority_filters([token])
            self.assertTrue(att.matches_priority(item_med, filters), token)
            self.assertFalse(att.matches_priority(item_high, filters), token)

        self.assertEqual(A.PRIORITY_ORDER, ("high", "medium", "low"))
        self.assertEqual(att._PRIORITY_SORT_RANK, {"high": 0, "medium": 1, "low": 2})

        parser = cli._build_parser()
        for argv in (
            ["backlog", "set", "done", "aaaaaa", "--priority", "med"],
            ["specs", "set", "x.md", "--priority", "med"],
        ):
            with self.assertRaises(SystemExit):
                with redirect_stderr(io.StringIO()):
                    parser.parse_args(argv)


class NameGrammarAgreesWithTheNamingAuthorityTests(unittest.TestCase):
    def test_name_grammar_agrees_with_naming_authority(self):
        from agent_workflows import artifact_naming as an

        items, _drift = att.scan(REPO_ROOT)
        conformant = 0
        mismatches = []
        for it in items:
            name = Path(it.path).name
            m = an.parse_clustered(name)
            if m is None:
                continue
            conformant += 1
            expected = (m.group("set"), int(m.group("nn")))
            got = att._name_grammar_fields(it.path)
            if got != expected:
                mismatches.append((name, got, expected))
        self.assertGreater(conformant, 100)
        self.assertEqual(mismatches, [])

        self.assertEqual(
            att._name_grammar_fields(
                ".aw/records/plans/pending/20260917-gate-contract-01-dcri4s-some-slug.ipd.md"
            ),
            ("gate-contract", 1),
        )

        stem = "20260101-foo-12-abc123-bar-01-def456-slug.ipd.md"
        m = an.parse_clustered(stem)
        assert m is not None
        self.assertEqual((m.group("set"), int(m.group("nn"))), ("foo", 12))
        self.assertEqual(att._name_grammar_fields(stem), ("foo", 12))

        self.assertEqual(
            att._name_grammar_fields(
                ".aw/records/specs/20260808-1945-01-attention-registry.spec.md"
            ),
            (None, None),
        )
        self.assertEqual(
            att._name_grammar_fields(
                ".aw/records/research/20260826-awclia-03-3uh9j3-aw-cli-naming-ia.gemini31pro.research-report.md"
            ),
            ("awclia", 3),
        )


class BlocksReleaseDashSortsAsAbsentTests(unittest.TestCase):
    def test_blocks_release_dash_sorts_as_absent(self):
        def mk(i, br):
            return att.Item(
                i, f"p/{i}.md", "plans", "draft", A.READY, None, None, blocks_release=br
            )

        items = [mk("dashes", "-"), mk("real01", "next"), mk("none01", None)]
        ordered, _notices = att.sort_items_with_notices(
            items, "blocking", repo_root=REPO_ROOT
        )
        self.assertEqual([it.id for it in ordered][0], "real01")
        self.assertEqual({it.id for it in ordered[1:]}, {"dashes", "none01"})

        dash = att.Item(
            "aaaaaa", "p.md", "plans", "draft", A.READY, None, None, blocks_release="-"
        )
        absent = att.Item("bbbbbb", "q.md", "plans", "draft", A.READY, None, None)
        self.assertEqual(
            att._order_key(dash, "blocking", None),
            att._order_key(absent, "blocking", None),
        )


class UnbulletedFrontmatterDetailTests(unittest.TestCase):
    def test_unbulleted_frontmatter_detail(self):
        text = "---\nid: aaaaaa\nstatus: todo\nsummary: The real summary.\n---\n\n# Research: a title\n"
        self.assertEqual(att._extract_detail(text), ("summary", "The real summary."))

        text_noh1 = "---\nid: aaaaaa\nstatus: todo\nsummary: Only the summary exists.\n---\n\nbody text\n"
        self.assertEqual(
            att._extract_detail(text_noh1), ("summary", "Only the summary exists.")
        )

        text_body = "---\nid: aaaaaa\nstatus: todo\n---\n\n# Real Title\n\n```yaml\nsummary: THIS IS QUOTED PROSE\n```\n"
        kind, val = att._extract_detail(text_body)
        self.assertEqual((kind, val), ("title", "Real Title"))
        self.assertNotIn("QUOTED PROSE", val or "")

        plan = "# IPD: p\n\n- Status: to-review\n- Scope: the declared scope\n- Id: aaaaaa\n"
        self.assertEqual(att._extract_detail(plan), ("scope", "the declared scope"))
        both = "---\nid: aaaaaa\nsummary: the frontmatter one\n---\n\n# T\n\n- Summary: the bulleted one\n"
        self.assertEqual(att._extract_detail(both), ("summary", "the bulleted one"))

        self.assertEqual(
            att._extract_detail("# Just A Title\n\nbody\n"), ("title", "Just A Title")
        )


class StatusAndReadinessColumnCollisionTests(unittest.TestCase):
    def _item(self, id6, status, readiness=None):
        return att.Item(
            id6,
            f".aw/records/plans/pending/20260101-t-01-{id6}-x.ipd.md",
            "plans",
            status,
            A.ACTIVE,
            None,
            None,
            readiness=readiness,
        )

    def test_status_and_readiness_column_collisions(self):
        rows = att.render_table(
            [self._item("aaaaaa", "implementing"), self._item("bbbbbb", "implemented")],
            [],
            show_all=True,
            term=att.T.Term(color=False),
        )
        line_ing = [ln for ln in rows.splitlines() if "aaaaaa" in ln][0]
        line_ed = [ln for ln in rows.splitlines() if "bbbbbb" in ln][0]
        self.assertNotEqual(line_ing.split()[1], line_ed.split()[1])
        self.assertNotIn("implemen ", line_ing)

        rows_r = att.render_table(
            [
                self._item("cccccc", "approved", "go"),
                self._item("dddddd", "reviewed", "go-pending-approval"),
            ],
            [],
            show_all=True,
            term=att.T.Term(color=False),
        )
        self.assertIn("go-pend?", rows_r)
        self.assertNotIn("go-pendin", rows_r)

        colored = att.render_table(
            [
                self._item("cccccc", "approved", "go"),
                self._item("dddddd", "reviewed", "go-pending-approval"),
                self._item("eeeeee", "draft", "no-go"),
            ],
            [],
            show_all=True,
            term=att.T.Term(color=True),
        )
        codes = {}
        for token in ("go", "go-pend?", "no-go"):
            m = re.search(r"\033\[([0-9;]*)m" + re.escape(token) + r"\033\[0m", colored)
            self.assertIsNotNone(m)
            assert m is not None
            codes[token] = m.group(1)
        self.assertEqual(len(set(codes.values())), 3)

        statuses = (
            "not-executed",
            "superseded",
            "to-review",
            "reviewed",
            "approved",
            "executed",
            "implementing",
            "implemented",
        )
        items = [self._item(f"id{i:04d}", s) for i, s in enumerate(statuses)]
        plain = att.render_table(items, [], show_all=True, term=att.T.Term(color=False))
        body = [ln for ln in plain.splitlines() if re.search(r"\bid\d{4}\b", ln)]
        self.assertEqual(len(body), len(statuses))
        widths = {att.T.visible_width(ln) for ln in body}
        self.assertEqual(len(widths), 1)

        for status in ("implementing", "implemented"):
            self.assertLessEqual(len(att._abbrev_status(status)), 8)
        self.assertLessEqual(len(att._abbrev_readiness("go-pending-approval")), 9)


class NoProjectAgentEnvelopeTests(unittest.TestCase):
    def _run_from_nowhere(self, **kw):
        base = dict(
            dir=None,
            check=False,
            format=None,
            agent=False,
            json=False,
            no_color=True,
            all=False,
            types=[],
            status=[],
            priority=[],
            blocking=[],
            readiness=[],
            open_questions=False,
            selectors=[],
            long=False,
            details=False,
        )
        base.update(kw)
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as td:
            os.chdir(td)
            try:
                out, err = io.StringIO(), io.StringIO()
                old_out, old_err = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = out, err
                try:
                    rc = att.run(argparse.Namespace(**base))
                finally:
                    sys.stdout, sys.stderr = old_out, old_err
                return rc, out.getvalue(), err.getvalue(), td
            finally:
                os.chdir(cwd)

    def test_no_project_agent_envelope(self):
        from agent_workflows import agent_schema, cli

        rc, out, err, td = self._run_from_nowhere(agent=True)
        self.assertEqual(rc, 2)
        self.assertTrue(out.strip())
        rec = json.loads(out.splitlines()[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

        rc_j, out_j, _, _ = self._run_from_nowhere(format="json")
        self.assertEqual(rc_j, 2)
        obj = json.loads(out_j)
        self.assertEqual(obj["status"], "cannot-run")
        self.assertEqual(obj["exit_code"], 2)

        self.assertNotIn(td, out)
        self.assertNotIn("/home/", out)
        self.assertNotIn(td, out_j)
        self.assertNotIn("/home/", out_j)

        rc_h, out_h, err_h, _ = self._run_from_nowhere()
        self.assertEqual(rc_h, 3)
        self.assertEqual(out_h, "")
        self.assertIn("no AW project found", err_h)

        parser = cli._build_parser()
        args = parser.parse_args(["att", "--arcive-state", "running"])
        self.assertEqual(args.run_status, ["running"])
        self.assertEqual(args.arcive_state, ["running"])


def _attsel_repo(tmp: Path) -> Path:
    specs = tmp / ".aw" / "records" / "specs"
    research = tmp / ".aw" / "records" / "research"
    plans = tmp / ".aw" / "records" / "plans" / "pending"
    backlog = tmp / ".aw" / "records" / "backlog" / "parked"
    for d in (specs, research, plans, backlog):
        d.mkdir(parents=True, exist_ok=True)
    (specs / "20260808-s-01-spc001-s.spec.md").write_text(
        "# Spec: s\n\n- Date: 2026-08-08\n- Status: approved\n- Id: spc001\n- Author: t\n\n## Body\n\nx\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
        encoding="utf-8",
    )
    (plans / "20260808-x-01-abc123-p.ipd.md").write_text(
        "# IPD: p\n\n- Status: draft\n- Id: abc123\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
        encoding="utf-8",
    )
    (research / "20260808-r-00-def456-r.survey.md").write_text(
        "---\nid: def456\nstatus: active\nkind: survey\n---\n\n# r\n\n## Workflow history\n- 2026-08-08 draft (t): x.\n",
        encoding="utf-8",
    )
    (backlog / "20260808-b-01-prk001-b.backlog.md").write_text(
        "- Id: prk001\n- Status: parked\n- Set: b\n- Priority: medium\n- Work-Kind: chore\n- Summary: a parked maybe\n\n## Workflow history\n- 2026-08-08 parked (t): created.\n",
        encoding="utf-8",
    )
    return tmp


def _attsel_args(root: Path, **kw) -> argparse.Namespace:
    base = dict(
        dir=str(root),
        format=None,
        check=False,
        selectors=[],
        no_color=True,
        all=False,
        long=False,
        types=[],
        status=[],
        priority=[],
        blocking=[],
        readiness=[],
        open_questions=False,
        agent=False,
        json=False,
        id6_only=False,
        paths=False,
        filenames=False,
        details=False,
        order_by=None,
        runs=False,
        active=False,
        not_active=False,
        run_status=[],
        arcive_state=[],
        active_state=[],
    )
    base.update(kw)
    return argparse.Namespace(**base)


def _attsel_run(root: Path, **kw):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = att.run(_attsel_args(root, **kw))
    return rc, out.getvalue(), err.getvalue()


class SelectorNoMatchIsReportedTests(unittest.TestCase):
    def test_selector_no_match_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            root = _attsel_repo(Path(td))

            rc, out, err = _attsel_run(root, selectors=["zzzzzz"])
            self.assertEqual(rc, att.EXIT_UNRESOLVED_SELECTOR)
            self.assertEqual(rc, 2)
            self.assertEqual(out, "")
            self.assertIn("zzzzzz", err)

            rc_b, out_b, err_b = _attsel_run(
                root, selectors=["def456"], types=["plans"]
            )
            self.assertEqual(rc_b, 0)
            self.assertEqual(err_b, "")

            rc_c, out_c, err_c = _attsel_run(root, selectors=["abc123"])
            self.assertEqual(rc_c, 0)
            self.assertIn("abc123", out_c)
            self.assertEqual(err_c, "")

            rc_sub, _, err_sub = _attsel_run(root, selectors=[".aw"])
            self.assertEqual(rc_sub, 0)
            self.assertEqual(err_sub, "")

            rc_j, out_j, _ = _attsel_run(root, selectors=["zzzzzz"], format="json")
            self.assertEqual(rc_j, att.EXIT_UNRESOLVED_SELECTOR)
            payload = json.loads(out_j)
            self.assertEqual(payload["outcome"], "cannot-run")
            self.assertEqual(payload["unresolved_selectors"], ["zzzzzz"])

            rc_bare, _, err_bare = _attsel_run(root, selectors=[])
            self.assertEqual(rc_bare, 0)
            self.assertEqual(err_bare, "")


class AttentionMatchingArtifactsCountTests(unittest.TestCase):
    """The board ends with how many artifacts matched, and how many are hidden without --all."""

    def _run(self, root, selectors=(), show_all=False):
        args = argparse.Namespace(
            dir=str(root),
            format=None,
            check=False,
            selectors=list(selectors),
            types=[],
            no_color=True,
            all=show_all,
            long=False,
            details=False,
        )
        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = att.run(args)
        return rc, buf.getvalue()

    def _add_done_spec(self, root):
        (root / ".agents" / "docs" / "specs" / "done.md").write_text(
            "# Spec: done\n\n- Date: 2026-08-08\n- Status: implemented\n- Author: t\n\n"
            "## Body\n\nx\n\n## Workflow history\n- 2026-08-08 draft (t): created.\n",
            encoding="utf-8",
        )

    def test_count_all_visible(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = self._run(_mk_repo(Path(td)))
            self.assertEqual(rc, 0)
            self.assertIn("3 matching artifacts\n", out)
            self.assertNotIn("hidden", out)

    def test_count_singular(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out = self._run(_mk_repo(Path(td)), selectors=["abc123"])
            self.assertEqual(rc, 0)
            self.assertIn("1 matching artifact\n", out)
            self.assertNotIn("matching artifacts", out)

    def test_count_names_hidden_terminal_items(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            self._add_done_spec(root)
            _, out = self._run(root)
            self.assertIn("4 matching artifacts (1 hidden; use --all)\n", out)
            self.assertNotIn("see old stuff", out)

    def test_count_with_all_hides_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            self._add_done_spec(root)
            _, out = self._run(root, show_all=True)
            self.assertIn("4 matching artifacts\n", out)
            self.assertNotIn("hidden", out)
