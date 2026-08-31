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
        # awdoctorfix Order 02: the default colored board shows the compact identity stem (not the
        # folded prefix / full path); a non-clustered name like `r.md` falls back to `r`. A None
        # last_history_at yields a '?' age marker.
        self.assertNotIn(".agents/docs/research/r.md (active)", stripped)
        self.assertRegex(stripped, r"- \??\s*active\s+research\s+r")
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


if __name__ == "__main__":
    unittest.main()
