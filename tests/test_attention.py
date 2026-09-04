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
import tempfile
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

    def test_scan_does_not_stamp_aw_and_setup_needed_derives(self):
        """setupmarker Order 01: the action-ledger scan was removed (it caused write-on-read). A scan
        must NOT create .aw/, and setup_needed derives read-only from the .aw/setup-repo-needed.md
        marker."""
        import tempfile
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as d:
            fresh = Path(d) / "fresh"
            fresh.mkdir(parents=True, exist_ok=True)
            items, drift = att.scan(fresh)
            self.assertFalse(
                (fresh / ".aw").exists(), "scan must not stamp .aw/ (write-on-read)"
            )
            self.assertFalse(att.setup_needed(fresh))
            engine.write_setup_marker(fresh)
            self.assertTrue(att.setup_needed(fresh))
            self.assertFalse(any(it.tree == "actions" for it in items))

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
        # Default colored board shows the compact identity stem (not the folded prefix / full path);
        # a non-clustered name like `r.md` falls back to `r`.
        self.assertNotIn(".agents/docs/research/r.md (active)", stripped)
        self.assertRegex(stripped, r"active\s+research\s+-\s+-\s+-\s+0\s+0\s+r")
        self.assertRegex(
            stripped,
            r"deferred\s+spec\s+-\s+-\s+-\s+0\s+0\s+s\s+\[gate artifact: TODO.md\]",
        )
        self.assertNotIn("## blocked", stripped)
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

    def test_run_set_intake_not_ready_unrun_stays_ready_active_untouched(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # RUN prompt-set: an intake report whose set has a prompt + report sibling -> stale.
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
            # UNRUN prompt: bare NN=00 intake prompt -> stays actionable/ready.
            self._write_research(
                root,
                set_id="unrunset",
                order=0,
                id6="prmpt9",
                slug="ask",
                status="intake",
                kind="research-prompt",
            )
            # active doc -> keeps ACTIVE.
            self._write_research(
                root,
                set_id="liveset",
                order=0,
                id6="live01",
                slug="w",
                status="active",
                kind="notes",
            )
            items, drift = att.scan(root)
            cls = {it.id: it.attention_class for it in items if it.tree == "research"}
            self.assertEqual(
                cls.get("rprt01"), "parked", "stale RUN-set intake must not be ready"
            )
            self.assertEqual(
                cls.get("prmpt9"), "ready", "genuinely-unrun intake prompt stays ready"
            )
            self.assertEqual(cls.get("live01"), "active", "active doc keeps ACTIVE")

    def test_todo_and_legacy_intake_classify_identically(self):
        # rstodo p3o9je load-bearing compat: a `todo` doc and a legacy `intake` doc both classify
        # READY and both surface with native_status normalized to canonical `todo` (so color +
        # stale-reclass behave identically). Falsifiable: a legacy `intake` raising unknown-status or
        # classifying differently fails.
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
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
                [dd for dd in drift if dd.rule == "attention.unknown-status"],
                f"legacy intake must not raise unknown-status: {drift}",
            )
            by_id = {it.id: it for it in items if it.tree == "research"}
            self.assertEqual(by_id["todo01"].attention_class, "ready")
            self.assertEqual(by_id["oldik0"].attention_class, "ready")
            # native_status normalized to canonical `todo` for BOTH (so color/reclass are identical)
            self.assertEqual(by_id["todo01"].native_status, "todo")
            self.assertEqual(by_id["oldik0"].native_status, "todo")

    def test_cited_by_executed_intake_not_ready(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            # A standalone intake doc cited by an EXECUTED plan -> stale -> parked.
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
            items, _drift = att.scan(root)
            cls = {it.id: it.attention_class for it in items if it.tree == "research"}
            self.assertEqual(cls.get("solo11"), "parked")

    def test_class_of_unchanged_and_total(self):
        # E-02 must NOT modify class_of; it stays status-only and total over the four statuses.
        # rstodo p3o9je: the hot state canonical token is now `todo` (renamed from `intake`); a legacy
        # `intake` is normalized to `todo` at the SCANNER, not in the pure/total class_of, so class_of
        # keys on the canonical `todo`.
        self.assertEqual(A.class_of("research", "todo"), "ready")
        self.assertEqual(A.class_of("research", "active"), "active")
        self.assertEqual(A.class_of("research", "reference"), "done")
        self.assertEqual(A.class_of("research", "archive"), "parked")

    def test_filter_items_by_selectors(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            items, _drift = att.scan(root)
            self.assertEqual(len(items), 3)

            # Filter by id6
            f1 = att.filter_items_by_selectors(items, ["abc123"], root)
            self.assertEqual(len(f1), 1)
            self.assertEqual(f1[0].id, "abc123")

            # Filter by setid
            f2 = att.filter_items_by_selectors(items, ["r"], root)
            self.assertEqual(len(f2), 1)
            self.assertEqual(f2[0].id, "def456")

            # Filter by tree
            f3 = att.filter_items_by_selectors(items, ["specs"], root)
            self.assertEqual(len(f3), 1)

            # Filter by attention class / status
            f4 = att.filter_items_by_selectors(items, ["active"], root)
            self.assertEqual(len(f4), 1)
            self.assertEqual(f4[0].id, "def456")

            # Multiple selectors OR-union
            f5 = att.filter_items_by_selectors(items, ["abc123", "def456"], root)
            self.assertEqual(len(f5), 2)
            self.assertEqual({it.id for it in f5}, {"abc123", "def456"})

            # Substring match
            f6 = att.filter_items_by_selectors(items, ["s.md"], root)
            self.assertEqual(len(f6), 1)

    def test_run_with_selectors(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))

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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["id"], "abc123")

    def test_extract_detail_cascade(self):
        # 1. Summary takes top priority
        txt1 = "# IPD: My Title\n\n- Summary: Top summary\n- Scope: Sub scope\n"
        self.assertEqual(att._extract_detail(txt1), ("summary", "Top summary"))

        # 2. Scope if no Summary
        txt2 = "# IPD: My Title\n\n- Scope: Plan scope line\n- Concern: Plan concern\n"
        self.assertEqual(att._extract_detail(txt2), ("scope", "Plan scope line"))

        # 3. Concern if no Scope/Summary
        txt3 = (
            "# Backlog: Bug\n\n- Concern: Memory leak in worker\n- Title: Bug Title\n"
        )
        self.assertEqual(
            att._extract_detail(txt3), ("concern", "Memory leak in worker")
        )

        # 4. Question for research
        txt4 = "# Research: Survey\n\n- Question: What is the optimal batch size?\n"
        self.assertEqual(
            att._extract_detail(txt4),
            ("question", "What is the optimal batch size?"),
        )

        # 5. Title frontmatter
        txt5 = "# Doc\n\n- Title: Explicit doc title\n"
        self.assertEqual(att._extract_detail(txt5), ("title", "Explicit doc title"))

        # 6. H1 header fallback
        txt6 = "# Spec: Fallback Specification Header\n\n- Status: draft\n"
        self.assertEqual(
            att._extract_detail(txt6),
            ("title", "Fallback Specification Header"),
        )

    def test_render_board_with_details(self):
        item1 = att.Item(
            id="abc123",
            path=".aw/records/plans/pending/20260808-p.ipd.md",
            tree="plans",
            native_status="approved",
            attention_class="ready",
            gate=None,
            last_history_at=None,
            detail_kind="scope",
            detail_text="Implement feature X and update CLI.",
        )
        item2 = att.Item(
            id="def456",
            path=".aw/records/specs/s.spec.md",
            tree="specs",
            native_status="approved",
            attention_class="ready",
            gate=None,
            last_history_at=None,
            detail_kind="summary",
            detail_text="Specification for feature X.",
        )
        items = [item1, item2]

        # Plain uncolored board
        term_plain = att.T.Term(color=False)
        board_plain = att.render_board(
            items, drift=[], show_all=True, term=term_plain, details=True
        )
        self.assertIn("      scope: Implement feature X and update CLI.", board_plain)
        self.assertIn("      summary: Specification for feature X.", board_plain)

        # Colored board
        term_color = att.T.Term(color=True)
        board_color = att.render_board(
            items, drift=[], show_all=True, term=term_color, details=True
        )
        self.assertIn("scope:", board_color)
        self.assertIn("Implement feature X and update CLI.", board_color)
        self.assertIn("summary:", board_color)
        self.assertIn("Specification for feature X.", board_color)

    def test_render_json_with_details(self):
        item = att.Item(
            id="abc123",
            path=".aw/records/plans/pending/20260808-p.ipd.md",
            tree="plans",
            native_status="approved",
            attention_class="ready",
            gate=None,
            last_history_at=None,
            detail_kind="scope",
            detail_text="Implement feature X.",
        )
        out = att.render_json([item], drift=[])
        data = json.loads(out)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["detail_kind"], "scope")
        self.assertEqual(data["items"][0]["detail_text"], "Implement feature X.")

    def test_run_with_details_flag(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            # Write a plan with an explicit Scope
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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            output = buf.getvalue()
            self.assertIn("scope: Build test subsystem.", output)

    def test_parse_type_filters(self):
        # Empty/None
        self.assertEqual(att.parse_type_filters(None), set())
        self.assertEqual(att.parse_type_filters([]), set())

        # Single type
        self.assertEqual(att.parse_type_filters(["plans"]), {"plans"})
        self.assertEqual(att.parse_type_filters(["plan"]), {"plans"})
        self.assertEqual(att.parse_type_filters(["ipd"]), {"plans"})

        # Comma-separated
        self.assertEqual(
            att.parse_type_filters(["plans,specs,backlog"]),
            {"plans", "specs", "backlog"},
        )
        self.assertEqual(
            att.parse_type_filters(["plan,spec,bk"]),
            {"plans", "specs", "backlog"},
        )

        # Repeated arguments
        self.assertEqual(
            att.parse_type_filters(["plans", "specs"]),
            {"plans", "specs"},
        )
        self.assertEqual(
            att.parse_type_filters(["ipd", "survey", "walkthr"]),
            {"plans", "research", "walkthroughs"},
        )

    def test_run_with_type_filter(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))

            # Filter single type
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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["tree"], "specs")

            # Filter multiple types via comma-separated
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
                rc = att.run(args2)
            self.assertEqual(rc, 0)
            data2 = json.loads(buf2.getvalue())
            self.assertEqual(len(data2["items"]), 2)
            self.assertEqual({it["tree"] for it in data2["items"]}, {"specs", "plans"})

            # Filter multiple types via repeated flags with aliases
            args3 = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=["ipd", "spec"],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf3 = io.StringIO()
            with mock.patch("sys.stdout", buf3):
                rc = att.run(args3)
            self.assertEqual(rc, 0)
            data3 = json.loads(buf3.getvalue())
            self.assertEqual(len(data3["items"]), 2)
            self.assertEqual({it["tree"] for it in data3["items"]}, {"specs", "plans"})

    def test_run_deduplicates_release_blockers(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            # Write a planned release
            rel_dir = root / ".aw" / "records" / "releases"
            rel_dir.mkdir(parents=True, exist_ok=True)
            (rel_dir / "20260830-rel001-01-rel001-release.release.md").write_text(
                "# Release: 1.0.0\n\n- Id: rel001\n- Version: 1.0.0\n- Status: planned\n- Summary: Test\n",
                encoding="utf-8",
            )
            # Add - Blocks-Release: next to the spec
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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            output = buf.getvalue()

            # Spec should appear in release-blockers section, but NOT in ## ready section!
            self.assertIn("## release-blockers", output)
            self.assertIn(".agents/docs/specs/s.md", output)
            self.assertNotIn("## ready", output)

    def test_footer_placement_and_interactive_headers(self):
        from agent_workflows import engine

        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            engine.write_setup_marker(root)

            # Test colored output
            args = argparse.Namespace(
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
            buf = io.StringIO()
            term = att.T.Term(stream=buf, color=True)
            with mock.patch("sys.stdout", buf), mock.patch(
                "agent_workflows.attention.T.Term", return_value=term
            ):
                rc = att.run(args)
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            stripped = re.sub(r"\033\[[0-9;]*m", "", out)

            # Interactive output is a table with header
            self.assertIn(
                "Status    Type    Blocking Priority Readiness  OQs  RQs  Artifact Set / ID",
                stripped,
            )
            self.assertNotIn("## active", stripped)
            self.assertNotIn("## ready", stripped)

            # Note must be at the very bottom
            self.assertTrue(
                stripped.endswith("TODO: Run `/aw setup-repo` to set up this repo.\n")
            )


class AttentionTableFormattingAndSortingTests(unittest.TestCase):
    def test_exact_user_columns_and_formatting(self):
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

        # Plain output
        plain_out = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=False)
        )
        self.assertEqual(stripped, plain_out)

        lines = [line for line in stripped.splitlines() if line.strip()]
        self.assertEqual(
            lines[0],
            "Status    Type    Blocking Priority Readiness  OQs  RQs  Artifact Set / ID",
        )

        # Verify exact sorted lines:
        # 1. Type: backlog (medium, 2.0.0)
        self.assertEqual(
            lines[1],
            "open      backlog    2.0.0 medium   -            0    0  20260903-runnerlayer-01-cnwy8g",
        )
        self.assertEqual(
            lines[2],
            "open      backlog    2.0.0 medium   -            0    0  20260904-rununbound-01-d07nz2",
        )
        # 2. Type: plan (non-blocking first, then blocking)
        self.assertEqual(
            lines[3],
            "reviewed  plan           - -        -            0    0  20260829-runprofile-02-p0l1to",
        )
        self.assertEqual(
            lines[4],
            "approved  plan       2.0.0 -        -            0    0  20260829-rununify-00-5e4sb6",
        )
        self.assertEqual(
            lines[5],
            "reviewed  plan       2.0.0 -        go-pendin    0    0  20260830-runcodes-01-wlxkoz",
        )
        self.assertEqual(
            lines[6],
            "to-revie  plan       2.0.0 -        -            0    0  20260904-revsweep-01-76gsmv",
        )
        # 3. Type: spec
        self.assertEqual(
            lines[7],
            "implemen  spec       2.0.0 -        -            0    0  20260829-c4gd2h-01-c4gd2h",
        )

    def test_oq_count_in_table_and_parser(self):
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

        item = att.Item(
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
        out = att.render_table([item], [], show_all=True, term=att.T.Term(color=False))
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(
            lines[0],
            "Status    Type    Blocking Priority Readiness  OQs  RQs  Artifact Set / ID",
        )
        self.assertIn(
            "to-revie  plan           - -        -            2    1  p", lines[1]
        )

    def test_priority_sorting(self):
        items = [
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
        out = att.render_table(items, [], show_all=True, term=att.T.Term(color=False))
        lines = [line for line in out.splitlines() if line.strip()][1:]
        # None first, then low, med, high
        self.assertTrue(lines[0].endswith("c"))
        self.assertTrue(lines[1].endswith("b"))
        self.assertTrue(lines[2].endswith("d"))
        self.assertTrue(lines[3].endswith("a"))

    def test_name_sorting(self):
        items = [
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
        out = att.render_table(items, [], show_all=True, term=att.T.Term(color=False))
        lines = [line for line in out.splitlines() if line.strip()][1:]
        self.assertTrue(lines[0].endswith("a-item"))
        self.assertTrue(lines[1].endswith("m-item"))
        self.assertTrue(lines[2].endswith("z-item"))


class AttentionFilteringTests(unittest.TestCase):
    def test_parse_filter_tokens(self):
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

    def test_status_filtering(self):
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

    def test_priority_filtering(self):
        item_high = att.Item(
            "1", "b1.md", "backlog", "open", A.READY, None, None, priority="high"
        )
        item_med = att.Item(
            "2", "b2.md", "backlog", "open", A.READY, None, None, priority="medium"
        )
        item_none = att.Item(
            "3", "b3.md", "backlog", "open", A.READY, None, None, priority=None
        )

        filters = att.parse_priority_filters(["high", "medium"])
        self.assertTrue(att.matches_priority(item_high, filters))
        self.assertTrue(att.matches_priority(item_med, filters))
        self.assertFalse(att.matches_priority(item_none, filters))

        filters_none = att.parse_priority_filters(["-"])
        self.assertFalse(att.matches_priority(item_high, filters_none))
        self.assertTrue(att.matches_priority(item_none, filters_none))

    def test_blocking_filtering(self):
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

        filters_bool_true = att.parse_blocking_filters(["true"])
        self.assertTrue(att.matches_blocking(item_blk, filters_bool_true))
        self.assertFalse(att.matches_blocking(item_nonblk, filters_bool_true))

        filters_bool_false = att.parse_blocking_filters(["-"])
        self.assertFalse(att.matches_blocking(item_blk, filters_bool_false))
        self.assertTrue(att.matches_blocking(item_nonblk, filters_bool_false))

    def test_readiness_filtering(self):
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

        filters = att.parse_readiness_filters(["go-pending-approval"])
        self.assertTrue(att.matches_readiness(item_ready, filters))
        self.assertFalse(att.matches_readiness(item_noready, filters))

        filters_none = att.parse_readiness_filters(["-"])
        self.assertFalse(att.matches_readiness(item_ready, filters_none))
        self.assertTrue(att.matches_readiness(item_noready, filters_none))

    def test_run_with_status_and_priority_filters(self):
        with tempfile.TemporaryDirectory() as td:
            root = _mk_repo(Path(td))
            # Test --status with multiple values and comma-separated
            args = argparse.Namespace(
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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            for item in data["items"]:
                self.assertIn(item["native_status"], ("to-review", "draft"))

            # Test --status comma-separated: --status to-review,draft
            args2 = argparse.Namespace(
                dir=str(root),
                format="json",
                check=False,
                selectors=[],
                types=[],
                status=["to-review,draft"],
                priority=[],
                blocking=[],
                readiness=[],
                no_color=True,
                all=False,
                long=False,
                details=False,
            )
            buf2 = io.StringIO()
            with mock.patch("sys.stdout", buf2):
                rc2 = att.run(args2)
            self.assertEqual(rc2, 0)
            data2 = json.loads(buf2.getvalue())
            self.assertEqual(len(data["items"]), len(data2["items"]))

    def test_cli_parsing_filters(self):
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

        args3 = parser.parse_args(["att", "--open-questions"])
        self.assertTrue(args3.open_questions)
        args4 = parser.parse_args(["att", "--oqs"])
        self.assertTrue(args4.open_questions)

    def test_open_questions_filter(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw").mkdir(parents=True)
            plans_dir = root / ".aw" / "records" / "plans" / "pending"
            plans_dir.mkdir(parents=True)

            p1 = plans_dir / "20260901-test-01-aaaaaa-has-oq.ipd.md"
            p1.write_text(
                "# IPD: has oq\n"
                "- Status: to-review\n"
                "- Set: test\n"
                "- Order: 01\n"
                "- Id: aaaaaa\n\n"
                "## Open questions\n\n"
                "### OQ-01: Open\n"
                "- Status: open\n",
                encoding="utf-8",
            )
            p2 = plans_dir / "20260901-test-02-bbbbbb-resolved-oq.ipd.md"
            p2.write_text(
                "# IPD: resolved oq\n"
                "- Status: to-review\n"
                "- Set: test\n"
                "- Order: 02\n"
                "- Id: bbbbbb\n\n"
                "## Open questions\n\n"
                "### OQ-01: Resolved\n"
                "- Status: resolved\n",
                encoding="utf-8",
            )

            args = argparse.Namespace(
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
                rc = att.run(args)
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["items"][0]["id"], "aaaaaa")


if __name__ == "__main__":
    unittest.main()
