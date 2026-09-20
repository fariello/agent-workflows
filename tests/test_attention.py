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
from contextlib import redirect_stderr, redirect_stdout
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
            # awdoctorfix Order 01 bumped to 2 (priority + blocks_release); then to 3 when items
            # gained readiness + oqs + rqs so the TTY columns are also machine-readable; then to 4 when
            # the payload gained the top-level `stranded_lanes` key (lanestrand-01 `pr5b0t`).
            self.assertEqual(obj["schema_version"], 4)
            self.assertEqual(obj["stranded_lanes"], [])
            self.assertTrue(obj["valid"])
            self.assertEqual(obj["violations"], [])
            self.assertTrue(all("attention_class" in it for it in obj["items"]))
            self.assertTrue(all("priority" in it for it in obj["items"]))
            self.assertTrue(all("blocks_release" in it for it in obj["items"]))
            self.assertTrue(all("readiness" in it for it in obj["items"]))
            self.assertTrue(all("oqs" in it for it in obj["items"]))
            self.assertTrue(all("rqs" in it for it in obj["items"]))

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
        # Status is 256-colored + bold, from the SHARED resolver.
        #
        # RECOMPUTED AGAINST SPEC `uonrjg` SECTION 5 (plan `f9t5hz` E-04). This read 39 ("active
        # azure") before the conversion, which was `attention.py`'s own index; the spec's `active`
        # stage is 220 bold, and research `active` maps to `active` (Section 6.4). The GLYPH carries
        # the identical escape, which is criterion A10 on this board.
        self.assertIn("\033[1;38;5;220mactive\033[0m", board)
        self.assertIn("\033[1;38;5;220m●\033[0m \033[1;38;5;220mactive\033[0m", board)
        # A blocked stage carries the TEXT-presentation `⚠︎` (U+26A0 U+FE0E), never the emoji form
        # (criterion A5), and `deferred` maps to `blocked` at 208 (Sections 5 and 6.2).
        self.assertIn("\033[1;38;5;208m\u26a0\ufe0e\033[0m", board)
        self.assertNotIn("\u26a0\ufe0f", board)
        # A10, the negative half: the artifact TYPE word carries no escape at all.
        self.assertIn("active\033[0m   research ", board)
        # Default colored board shows the compact identity stem (not the folded prefix / full path);
        # a non-clustered name like `r.md` falls back to `r`.
        self.assertNotIn(".agents/docs/research/r.md (active)", stripped)
        self.assertRegex(
            stripped, r"active\s+research\s+-\s+-\s+-\s+-\s+-\s+-\s+-\s+r\s+-\s+i1"
        )
        self.assertRegex(
            stripped,
            r"deferred\s+spec\s+-\s+-\s+-\s+-\s+-\s+-\s+-\s+s\s+-\s+i2\s+-\s+\[gate artifact: TODO.md\]",
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
            with (
                mock.patch("sys.stdout", buf),
                mock.patch("agent_workflows.attention.T.Term", return_value=term),
            ):
                rc = att.run(args)
            self.assertEqual(rc, 0)
            out = buf.getvalue()
            stripped = re.sub(r"\033\[[0-9;]*m", "", out)

            # Interactive output is a table with header
            self.assertIn(
                "Status   Type     Blocks Priority Readiness OQs Exec Valid Date     ",
                stripped,
            )
            self.assertIn("Deps", stripped)
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
        # Date, SetID, and ID6 receive the Status color.
        #
        # RECOMPUTED AGAINST SPEC `uonrjg` SECTION 5 (plan `f9t5hz` E-04). These read 40 before the
        # conversion, which was `attention.py`'s own index for `open`; the spec's `ready` stage is 45
        # bold, and `open` maps to `ready` (Section 6.3). The change of number here is the expected
        # human-snapshot churn Section 12 sanctions, not a regression.
        self.assertIn("\033[1;38;5;45m20260903\033[0m", colored_out)
        self.assertIn("\033[1;38;5;45mrunnerlayer\033[0m", colored_out)
        self.assertIn("\033[1;38;5;45mcnwy8g\033[0m", colored_out)
        # A10: the glyph, the id6 and the status word share ONE escape. `open` -> `ready` -> `◕`, 45
        # bold. Asserted on the raw escape, never on stripped text, or the assertion cannot fail.
        self.assertIn("\033[1;38;5;45m◕\033[0m \033[1;38;5;45mopen\033[0m", colored_out)
        # A10, the negative half: the artifact TYPE word carries NO escape (it emitted
        # `\033[1;38;5;33mbacklog\033[0m` before this conversion).
        self.assertIn("open\033[0m     backlog   ", colored_out)
        self.assertNotIn("\033[1;38;5;33m", colored_out)

        # Plain output
        plain_out = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=False)
        )
        self.assertEqual(stripped, plain_out)

        lines = [line for line in stripped.splitlines() if line.strip()]
        # THE COLUMN ORDER AND COUNT ARE UNCHANGED (Section 12): the lifecycle glyph is carried INSIDE
        # the existing Status column, ahead of the word, which is where Section 9.1 requires it ("glyph
        # MUST immediately precede either id6 or status"). Only that column's width grows, from 8 to
        # 10, so the header gains exactly two leading spaces and no column moves relative to another.
        self.assertEqual(
            lines[0],
            "  Status   Type     Blocks Priority Readiness OQs Exec Valid Date     SetID       N  ID6    Deps",
        )

        # Verify exact sorted lines. Each leading glyph is the spec Section 5 grapheme for the stage
        # the status maps to: `open`/`approved` -> ready `◕`, `reviewed` -> authority-queued `◑`,
        # `to-review` -> review-queued `◔`, `implementing` -> executing `▶`.
        # 1. Type: backlog (medium, 2.0.0)
        self.assertEqual(
            lines[1],
            "◕ open     backlog   2.0.0 medium   -           -    -     - 20260903 runnerlayer 01 cnwy8g -",
        )
        self.assertEqual(
            lines[2],
            "◕ open     backlog   2.0.0 medium   -           -    -     - 20260904 rununbound  01 d07nz2 -",
        )
        # 2. Type: plan (non-blocking first, then blocking)
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
            "◑ reviewed plan      2.0.0 -        go-pendin   -    -     - 20260830 runcodes    01 wlxkoz -",
        )
        self.assertEqual(
            lines[6],
            "◔ to-revie plan      2.0.0 -        -           -    -     - 20260904 revsweep    01 76gsmv -",
        )
        # 3. Type: spec
        self.assertEqual(
            lines[7],
            "▶ implemen spec      2.0.0 -        -           -    -     - 20260829 c4gd2h      01 c4gd2h -",
        )
        # 4. Legend
        self.assertEqual(
            lines[8],
            "OQs = Open Questions (open/total), Exec = Executed items, Valid = Validated items, Deps = Dependencies",
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
            "  Status   Type     Blocks Priority Readiness OQs Exec Valid Date     SetID N  ID6    Deps",
        )
        self.assertIn(
            "◔ to-revie plan          - -        -         2/3    -     - -        p     -  1      -",
            lines[1],
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
        self.assertEqual(lines[0].split()[-4], "c")
        self.assertEqual(lines[1].split()[-4], "b")
        self.assertEqual(lines[2].split()[-4], "d")
        self.assertEqual(lines[3].split()[-4], "a")

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
        self.assertEqual(lines[0].split()[-4], "a-item")
        self.assertEqual(lines[1].split()[-4], "m-item")
        self.assertEqual(lines[2].split()[-4], "z-item")

    def test_numbered_items_sort_by_n_before_id6(self):
        items = [
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
        out = att.render_table(items, [], show_all=True, term=att.T.Term(color=False))
        lines = [line for line in out.splitlines() if line.strip()][1:]
        # N column should sort 00, 01, 04, 06 despite priority differences
        self.assertEqual(lines[0].split()[-3], "00")
        self.assertEqual(lines[1].split()[-3], "01")
        self.assertEqual(lines[2].split()[-3], "04")
        self.assertEqual(lines[3].split()[-3], "06")
        self.assertEqual(lines[0].split()[-2], "8lfoum")
        self.assertEqual(lines[1].split()[-2], "d7qoxv")
        self.assertEqual(lines[2].split()[-2], "u23gbn")
        self.assertEqual(lines[3].split()[-2], "4xt6u4")


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

        # Tag/number normalization: 'v2.0.0' matches '2.0.0' and vice versa
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

        # 'next' matches any release blocker regardless of tag/number
        filters_next = att.parse_blocking_filters(["next"])
        self.assertTrue(att.matches_blocking(item_blk, filters_next))
        self.assertTrue(att.matches_blocking(item_blk_tag, filters_next))
        item_blk_next = att.Item(
            "4",
            "p4.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            blocks_release="next",
        )
        self.assertTrue(att.matches_blocking(item_blk_next, filters_next))
        item_blk_id6 = att.Item(
            "5",
            "p5.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
            blocks_release="f33nrj",
        )
        self.assertTrue(att.matches_blocking(item_blk_id6, filters_next))
        self.assertFalse(att.matches_blocking(item_nonblk, filters_next))

        item_dash = att.Item(
            "6", "p6.md", "plans", "approved", A.READY, None, None, blocks_release="-"
        )
        self.assertFalse(att.matches_blocking(item_dash, filters_next))

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
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            executed_dir.mkdir(parents=True)
            p3 = executed_dir / "20260901-test-03-cccccc-executed-with-oq.ipd.md"
            p3.write_text(
                "# IPD: executed with oq\n"
                "- Status: executed\n"
                "- Set: test\n"
                "- Order: 03\n"
                "- Id: cccccc\n\n"
                "## Open questions\n\n"
                "### OQ-01: Still open in old plan\n"
                "- Status: open\n",
                encoding="utf-8",
            )

            # Without --all: excludes archived (e.g. executed or superseded)
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

            # With --all: includes archived items with open questions
            args_all = argparse.Namespace(
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
                all=True,
                long=False,
                details=False,
            )
            buf_all = io.StringIO()
            with mock.patch("sys.stdout", buf_all):
                rc_all = att.run(args_all)
            self.assertEqual(rc_all, 0)
            data_all = json.loads(buf_all.getvalue())
            self.assertEqual(len(data_all["items"]), 2)
            ids = {it["id"] for it in data_all["items"]}
            self.assertEqual(ids, {"aaaaaa", "cccccc"})

    def test_research_blocks_release_frontmatter_vs_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            research_dir = root / ".aw" / "records" / "research"
            research_dir.mkdir(parents=True)

            # Research doc with blocks-release in frontmatter
            r1 = (
                "---\n"
                "id: res001\n"
                "status: todo\n"
                "blocks-release: next\n"
                "---\n\n"
                "# Real research blocker\n"
            )
            (research_dir / "20260901-test-01-res001-real.md").write_text(
                r1, encoding="utf-8"
            )

            # Research doc with quoted - Blocks-Release: in body (like 27rjro)
            r2 = (
                "---\n"
                "id: res002\n"
                "status: todo\n"
                "---\n\n"
                "# Prompt quoting an IPD\n\n"
                "```markdown\n"
                "- Blocks-Release: next\n"
                "```\n"
            )
            (research_dir / "20260901-test-02-res002-quote.md").write_text(
                r2, encoding="utf-8"
            )

            items, _drift = att.scan(root)
            item_map = {it.id: it for it in items}
            self.assertEqual(item_map["res001"].blocks_release, "next")
            self.assertIsNone(item_map["res002"].blocks_release)

            blockers = att.release_blockers(items, root)
            blocker_ids = {it.id for it in blockers}
            self.assertIn("res001", blocker_ids)
            self.assertNotIn("res002", blocker_ids)

            # Filtering by -b next matches res001 but not res002
            filters = att.parse_blocking_filters(["next"])
            self.assertTrue(att.matches_blocking(item_map["res001"], filters, root))
            self.assertFalse(att.matches_blocking(item_map["res002"], filters, root))


class ExecValidAndDepsColumnsTests(unittest.TestCase):
    """Pin checklist progress extraction and rendering for Exec, Valid, and Deps columns."""

    def test_extract_checklist_progress(self):
        # Empty / non-checklist
        self.assertEqual(att._extract_checklist_progress(""), (None, None))
        self.assertEqual(att._extract_checklist_progress("Just text"), (None, None))

        # Unchecked items
        text_unchecked = """
- [ ] E-01 First task
- [ ] E-02 Second task
- [ ] V-01 Validates E-01
- [ ] V-02 Validates E-02
"""
        self.assertEqual(
            att._extract_checklist_progress(text_unchecked), ((0, 2), (0, 2))
        )

        # Partially checked items with lower and upper case
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

        # Fully checked
        text_full = """
- [x] E-01 First task
- [X] E-02 Second task
- [x] V-01 Validates E-01
- [x] V-02 Validates E-02
"""
        self.assertEqual(att._extract_checklist_progress(text_full), ((2, 2), (2, 2)))

    def test_extract_dependency_id6s(self):
        # From item_dependencies
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

        # From gate with direct id6
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

        # From gate with path containing id6
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

        # From gate with non-id6 ref
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

        # No dependencies or gate
        it5 = att.Item("p2", "p2.ipd.md", "plans", "approved", A.READY, None, None)
        self.assertEqual(att._extract_dependency_id6s(it5), [])

    def test_render_table_colors_and_formatting(self):
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

        # Plain text rendering
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

        # Colored text rendering: check color codes
        colored = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=True), id_map=id_map
        )
        # 0/2 is styled in color 244
        self.assertIn("\033[38;5;244m0/2\033[0m", colored)
        # 1/2 is styled in bold yellow (color 214)
        self.assertIn("\033[1;38;5;214m1/2\033[0m", colored)
        # 2/2 is styled in bold green (color 40)
        self.assertIn("\033[1;38;5;40m2/2\033[0m", colored)
        # A DEPENDENCY id6 CARRIES ITS TARGET'S LIFECYCLE COLOR (spec Section 9.2's compact id6
        # reference), and every index here is RECOMPUTED against spec Section 5 (plan `f9t5hz` E-04).
        # THE HEADLINE PROPERTY THIS BLOCK NOW PROVES, which the old numbers could not: `executed` and
        # `approved` are DIFFERENT STAGES (done versus ready) and must therefore be DIFFERENT COLORS.
        # They both read 46 before the conversion, i.e. the board painted a merged plan and a
        # not-yet-run plan identically, which is exactly Section 1's "green currently means both ready
        # and complete in several views".
        # Executed dep 29wvmj -> done -> 46 bold (unchanged).
        self.assertIn("\033[1;38;5;46m29wvmj\033[0m", colored)
        # Approved dep 51vw4y -> ready -> 45 bold (was 46, indistinguishable from done).
        self.assertIn("\033[1;38;5;45m51vw4y\033[0m", colored)
        # To-review dep 6sb3yu -> review-queued -> 39, NOT bold (Section 5 bolds only ready, the
        # active family, waiting, blocked, failed and done).
        self.assertIn("\033[38;5;39m6sb3yu\033[0m", colored)
        # Backlog dep bk1111 -> `open` -> ready -> 45 bold, the SAME escape as the approved plan
        # above, because one stage is one presentation regardless of artifact type.
        self.assertIn("\033[1;38;5;45mbk1111\033[0m", colored)
        # Legend column names are bolded
        self.assertIn("\033[1mOQs\033[0m = Open Questions", colored)
        self.assertIn("\033[1mExec\033[0m = Executed items", colored)
        self.assertIn("\033[1mValid\033[0m = Validated items", colored)
        self.assertIn("\033[1mDeps\033[0m = Dependencies", colored)
        self.assertNotIn("(met", colored)

    def test_render_table_runs_mode_column_and_legend(self):
        it1 = att.Item(
            "111111",
            ".aw/records/plans/p1.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        it2 = att.Item(
            "222222",
            ".aw/records/plans/p2.ipd.md",
            "plans",
            "to-review",
            A.READY,
            None,
            None,
        )
        it3 = att.Item(
            "333333",
            ".aw/records/plans/p3.ipd.md",
            "plans",
            "draft",
            A.READY,
            None,
            None,
        )
        it4 = att.Item(
            "444444",
            ".aw/records/plans/p4.ipd.md",
            "plans",
            "draft",
            A.READY,
            None,
            None,
        )
        items = [it1, it2, it3, it4]
        run_map = {
            "111111": "running",
            "222222": "queued",
            "333333": "done",
        }

        # Default (runs_mode=False): Run column is absent
        plain_off = att.render_table(
            items, [], show_all=True, term=att.T.Term(color=False), runs_mode=False
        )
        header_off = plain_off.splitlines()[0]
        self.assertNotIn("Run", header_off)
        self.assertNotIn("Active runner state", plain_off)

        # Enabled (runs_mode=True): Run column is present immediately after Status
        plain_on = att.render_table(
            items,
            [],
            show_all=True,
            term=att.T.Term(color=False),
            runs_mode=True,
            run_map=run_map,
        )
        lines_on = plain_on.splitlines()
        header_on = lines_on[0]
        # The two leading spaces are the lifecycle GLYPH cell, which lives inside the Status column
        # ahead of the word (Section 9.1). The column ORDER is unchanged: Run still sits immediately
        # after Status.
        self.assertTrue(header_on.startswith("  Status   Run     Type"))
        self.assertIn("Run = Active runner state", plain_on)

        # Check values
        row1 = [ln for ln in lines_on if "111111" in ln][0]
        self.assertIn("approved running plan", row1)
        row2 = [ln for ln in lines_on if "222222" in ln][0]
        self.assertIn("to-revie queued  plan", row2)
        row3 = [ln for ln in lines_on if "333333" in ln][0]
        self.assertIn("draft    done    plan", row3)
        row4 = [ln for ln in lines_on if "444444" in ln][0]
        self.assertIn("draft    -       plan", row4)

        # Colored formatting
        colored = att.render_table(
            items,
            [],
            show_all=True,
            term=att.T.Term(color=True),
            runs_mode=True,
            run_map=run_map,
        )
        # running in cyan (51)
        self.assertIn("\033[1;38;5;51mrunning\033[0m", colored)
        # queued in yellow (220)
        self.assertIn("\033[38;5;220mqueued\033[0m", colored)
        # done in green (40)
        self.assertIn("\033[1;38;5;40mdone\033[0m", colored)
        # - in gray (244)
        self.assertIn("\033[38;5;244m-\033[0m", colored)
        # Legend bolded Run
        self.assertIn("\033[1mRun\033[0m = Active runner state", colored)

    def test_get_active_runs_map_logic(self):
        import tempfile
        from unittest.mock import patch

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
                json.dumps(
                    {
                        "queue": [
                            {"id6": "dead01", "status": "running"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            def mock_holder(r_dir):
                if "100" in str(r_dir):
                    return "live"
                return "none"

            with patch(
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
            # Dead run item should NOT be included
            self.assertNotIn("dead01", rmap)

    def test_cli_runs_argument(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args_default = parser.parse_args(["att"])
        self.assertFalse(getattr(args_default, "runs", False))

        args_runs = parser.parse_args(["att", "--runs"])
        self.assertTrue(getattr(args_runs, "runs", False))

    def test_cli_run_status_argument(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args_default = parser.parse_args(["att"])
        self.assertEqual(getattr(args_default, "run_status", None), [])

        args_one = parser.parse_args(["att", "--run-status", "running"])
        self.assertEqual(args_one.run_status, ["running"])

        args_alias = parser.parse_args(["att", "--runs-status", "done"])
        self.assertEqual(args_alias.run_status, ["done"])

        args_multi = parser.parse_args(
            ["att", "--run-status", "running,queued", "--runs-status", "blocked"]
        )
        self.assertEqual(args_multi.run_status, ["running,queued", "blocked"])

    def test_parse_run_status_filters_and_matches_run_status(self):
        filters = att.parse_run_status_filters(
            ["running,queued", "dependency-blocked", "failed_safely"]
        )
        self.assertIn("running", filters)
        self.assertIn("queued", filters)
        self.assertIn("dependency-blocked", filters)
        self.assertIn("blocked", filters)
        self.assertIn("failed-safely", filters)
        self.assertIn("failed_safely", filters)
        self.assertIn("failed", filters)

        run_map = {
            "run001": "running",
            "done01": "done",
            "blk001": "blocked",
        }
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

        # "any" matches any active run item, but not items without run
        self.assertTrue(att.matches_run_status(it_running, {"any"}, run_map))
        self.assertFalse(att.matches_run_status(it_none, {"any"}, run_map))

        # "-" or "none" matches items without active run
        self.assertTrue(att.matches_run_status(it_none, {"-"}, run_map))
        self.assertTrue(att.matches_run_status(it_none, {"none"}, run_map))
        self.assertFalse(att.matches_run_status(it_running, {"-"}, run_map))

    def test_run_status_filtering_in_att_run(self):
        it_run = att.Item(
            "run001", "p/run001.md", "plans", "draft", A.READY, None, None
        )
        it_que = att.Item(
            "que002", "p/que002.md", "plans", "draft", A.READY, None, None
        )
        it_other = att.Item(
            "oth003", "p/oth003.md", "plans", "draft", A.READY, None, None
        )

        run_map = {"run001": "running", "que002": "queued"}
        with (
            mock.patch.object(
                att, "scan", return_value=([it_run, it_que, it_other], [])
            ),
            mock.patch.object(att, "get_active_runs_map", return_value=run_map),
            # `dir=None` resolves to the REAL repository; stub the lane reader so a stranded lane in the
            # developer's own checkout cannot change this case's exit code (lanestrand-01 `pr5b0t`).
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

    def test_cli_id6_only_argument_and_mutual_exclusivity(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args_default = parser.parse_args(["att"])
        self.assertFalse(getattr(args_default, "id6_only", False))
        self.assertFalse(getattr(args_default, "paths", False))
        self.assertFalse(getattr(args_default, "filenames", False))
        self.assertFalse(getattr(args_default, "long", False))

        args_id = parser.parse_args(["att", "--id6-only"])
        self.assertTrue(args_id.id6_only)

        args_id_short = parser.parse_args(["att", "-id"])
        self.assertTrue(args_id_short.id6_only)

        args_paths = parser.parse_args(["att", "--paths"])
        self.assertTrue(args_paths.paths)

        args_files = parser.parse_args(["att", "--filenames"])
        self.assertTrue(args_files.filenames)

        # Mutually exclusive pairs:
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

    def test_cli_active_and_not_active_arguments_and_mutual_exclusivity(self):
        from agent_workflows import cli

        parser = cli._build_parser()
        args_active = parser.parse_args(["att", "--active"])
        self.assertTrue(args_active.active)
        self.assertFalse(args_active.not_active)

        for flag in ("-a", "-ac", "-act"):
            args = parser.parse_args(["att", flag])
            self.assertTrue(args.active)

        args_not_active = parser.parse_args(["att", "--not-active"])
        self.assertTrue(args_not_active.not_active)
        self.assertFalse(args_not_active.active)

        for flag in ("-na", "-nac", "-not"):
            args = parser.parse_args(["att", flag])
            self.assertTrue(args.not_active)

        args_arcive = parser.parse_args(["att", "--arcive-state", "running"])
        self.assertEqual(args_arcive.run_status, ["running"])
        self.assertEqual(args_arcive.arcive_state, ["running"])

        args_active_state = parser.parse_args(
            ["att", "--active-state", "running,queued"]
        )
        self.assertEqual(args_active_state.run_status, ["running,queued"])
        self.assertEqual(args_active_state.active_state, ["running,queued"])

        # Multiple --arcive-state flags
        args_multi = parser.parse_args(["att", "-as", "running", "-ars", "queued"])
        self.assertEqual(args_multi.run_status, ["running", "queued"])

        # Mutual exclusivity:
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

    def test_id6_only_output_in_att_run(self):
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

        # lanestrand-01 (`pr5b0t`): these `dir=None` cases resolve to the REAL repository, so the
        # lane reader is stubbed for the same reason `scan` is - the case is about item rendering, and
        # a real stranded lane in the developer's checkout would otherwise change its exit code.
        with mock.patch.object(
            att, "scan", return_value=([it1, it2, it_done], [])
        ), mock.patch.object(att, "stranded_lane_drift", return_value=[]):
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
            lines = [
                line.strip() for line in buf.getvalue().splitlines() if line.strip()
            ]
            self.assertEqual(lines, ["id0001", "id0002"])

            # With --all, it_done is also included
            buf_all = io.StringIO()
            with redirect_stdout(buf_all):
                args.all = True
                rc = att.run(args)
            self.assertEqual(rc, 0)
            lines_all = [
                line.strip() for line in buf_all.getvalue().splitlines() if line.strip()
            ]
            self.assertEqual(lines_all, ["id0001", "id0002", "id0003"])

    def test_paths_and_filenames_output_in_att_run(self):
        it1 = att.Item(
            "id0001",
            ".aw/records/plans/pending/20260901-test-01-id0001-slug.ipd.md",
            "plans",
            "approved",
            A.READY,
            None,
            None,
        )
        with mock.patch.object(
            att, "scan", return_value=([it1], [])
        ), mock.patch.object(att, "stranded_lane_drift", return_value=[]):
            # paths
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
                    id6_only=False,
                    paths=True,
                    filenames=False,
                    active=False,
                    not_active=False,
                )
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertEqual(
                buf.getvalue().strip(),
                ".aw/records/plans/pending/20260901-test-01-id0001-slug.ipd.md",
            )

            # filenames
            buf_f = io.StringIO()
            with redirect_stdout(buf_f):
                args.paths = False
                args.filenames = True
                rc = att.run(args)
            self.assertEqual(rc, 0)
            self.assertEqual(
                buf_f.getvalue().strip(),
                "20260901-test-01-id0001-slug.ipd.md",
            )

    def test_active_and_not_active_filtering_in_att_run(self):
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
            # `dir=None` resolves to the REAL repository; stub the lane reader so a stranded lane in the
            # developer's own checkout cannot change this case's exit code (lanestrand-01 `pr5b0t`).
            mock.patch.object(att, "stranded_lane_drift", return_value=[]),
        ):
            # Test --active: shows only it_run
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

            # Test --not-active: shows only it_idle
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

    def test_a_stranded_lane_is_reported_LOUDLY_in_the_human_board(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))
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
            # The remedy must be named: an alarm with no route trains its own dismissal.
            self.assertIn("Recover it", out)

    def test_neither_surface_contains_an_ABSOLUTE_path(self):
        """The load-bearing leak guard (F-15). `aw attention --json` is pasted by agents and read by CI."""
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))
            human = io.StringIO()
            with self._holder(False), mock.patch("sys.stdout", human):
                att.run(_lane_args(root))
            payload = io.StringIO()
            with self._holder(False), mock.patch("sys.stdout", payload):
                att.run(_lane_args(root, format="json"))
            for label, text in (
                ("human render", human.getvalue()),
                ("json payload", payload.getvalue()),
            ):
                with self.subTest(surface=label):
                    self.assertNotIn(self.ABSOLUTE_WORKTREE, text)
                    self.assertNotIn("/home/", text)
                    # The repository-relative rendering IS allowed and is what the ask wanted.
                    self.assertIn(".aw/worktrees/lane01", text)

    def test_check_exits_nonzero_with_a_stranded_lane_and_zero_without(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))
            buf = io.StringIO()
            with self._holder(False), redirect_stdout(buf):
                rc_stranded = att.run(_lane_args(root, check=True))
            self.assertEqual(rc_stranded, 1, buf.getvalue())
            self.assertIn("attention.lane-stranded", buf.getvalue())

        with tempfile.TemporaryDirectory() as td:
            # No run records at all: nothing stranded, and the gate must stay green.
            root = _mk_repo(Path(td))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc_clean = att.run(_lane_args(root, check=True))
            self.assertEqual(rc_clean, 0, buf.getvalue())
            self.assertIn("the view is valid", buf.getvalue())

    def test_a_MERGED_lane_does_not_fail_the_check(self):
        """The false positive that would destroy the alarm: every recovered lane reported forever."""
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td), merged=True)
            buf = io.StringIO()
            with self._holder(False), redirect_stdout(buf):
                rc = att.run(_lane_args(root, check=True))
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertNotIn("lane-stranded", buf.getvalue())

    def test_a_LIVE_runs_lane_does_not_fail_the_check(self):
        """A driver run in progress legitimately owns its lane; a check that reds during every normal
        run is a check that gets bypassed."""
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td), live=True)
            buf = io.StringIO()
            with self._holder(True), redirect_stdout(buf):
                rc = att.run(_lane_args(root, check=True))
            self.assertEqual(rc, 0, buf.getvalue())
            self.assertNotIn("lane-stranded", buf.getvalue())

    def test_the_json_and_agent_payloads_carry_the_same_fact(self):
        with tempfile.TemporaryDirectory() as td:
            root = self._fixture(Path(td))
            buf = io.StringIO()
            with self._holder(False), mock.patch("sys.stdout", buf):
                rc = att.run(_lane_args(root, format="json"))
            self.assertEqual(rc, 1)
            obj = json.loads(buf.getvalue())
            # The NEW field, and the pre-existing keys unchanged in name and order.
            self.assertEqual(
                list(obj.keys()),
                [
                    "schema_version",
                    "mapping_version",
                    "valid",
                    "items",
                    "violations",
                    "stranded_lanes",
                ],
            )
            self.assertEqual(obj["schema_version"], 4)
            self.assertEqual(obj["mapping_version"], 1)
            # `valid` and the exit code are ONE mechanism: both follow from the drift set.
            self.assertFalse(obj["valid"])
            self.assertEqual(len(obj["stranded_lanes"]), 1)
            self.assertEqual(obj["stranded_lanes"][0]["branch"], "aw/lane/lane01")
            self.assertEqual(obj["stranded_lanes"][0]["rule"], att.LANE_STRANDED_RULE)
            # The same fact is in `violations`, which is what makes the two unable to disagree.
            self.assertIn(
                att.LANE_STRANDED_RULE, [v["rule"] for v in obj["violations"]]
            )

            agent = io.StringIO()
            with self._holder(False), redirect_stdout(agent):
                rc_agent = att.run(_lane_args(root, agent=True))
            self.assertEqual(rc_agent, 1)
            self.assertIn("attention.lane-stranded", agent.getvalue())
            self.assertIn("aw/lane/lane01", agent.getvalue())

    def test_render_json_stranded_lanes_is_DERIVED_from_drift_not_recomputed(self):
        """The mechanism guarantee: `valid` cannot contradict `stranded_lanes` by construction."""
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

    def test_a_stranded_lane_maps_to_an_existing_class_and_an_unmapped_one_RAISES(self):
        from agent_workflows import runner_shared as rs

        self.assertEqual(A.class_of("lanes", rs.LANE_STRANDED), A.BLOCKED)
        self.assertEqual(A.class_of("lanes", rs.LANE_UNKNOWN), A.BLOCKED)
        self.assertEqual(A.class_of("lanes", rs.LANE_LIVE), A.ACTIVE)
        self.assertEqual(A.class_of("lanes", rs.LANE_LANDED), A.DONE)
        self.assertEqual(A.class_of("lanes", rs.LANE_EMPTY_OF_WORK), A.DONE)
        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("lanes", "FROBNICATED")

    def test_the_lanes_fragment_is_TOTAL_over_the_predicates_states(self):
        from agent_workflows import runner_shared as rs

        self.assertEqual(set(A.CLASS_MAPS["lanes"].keys()), set(rs.LANE_REPORT_STATES))

    def test_scan_roots_are_unchanged_so_no_filesystem_walk_decides_this(self):
        from agent_workflows import artifact_core

        joined = " ".join(str(r) for r in artifact_core.SCAN_ROOTS)
        self.assertNotIn("worktrees", joined)
        self.assertNotIn("records/runs", joined)

    def test_stranded_lane_terminal_pruning(self):
        """Cleanly terminal runs with no preserved worktrees bypass live inspect_lane git calls."""
        from agent_workflows import runner_shared as rs
        from agent_workflows import worktree_lease

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

        with (
            tempfile.TemporaryDirectory() as td,
            mock.patch.object(worktree_lease, "inspect_lane") as mock_inspect,
        ):
            repo = Path(td)
            # With memoized empty caches, cleanly terminal runs are pruned
            with worktree_lease.memoize_worktrees(repo):
                records = rs.stranded_lane_records(repo, [state], attention_only=True)
                self.assertEqual(records, [])
                self.assertEqual(mock_inspect.call_count, 0)

    def test_count_question_stats(self):
        """Test count_question_stats boundary slicing and count accuracy."""
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

        # Empty or questionless document
        self.assertEqual(att.count_question_stats(""), (0, 0))
        self.assertEqual(
            att.count_question_stats("# Just a doc\nNo questions here"), (0, 0)
        )


class LaneRemedyHintTests(unittest.TestCase):
    """E-06: the remedy must name a verb that EXISTS, and the probe must be observable when it rots.

    THE DEFECT WAS UNOBSERVABILITY, NOT THE WRONG STRING. The old probe was a bare
    `hasattr(oc_runipd, "cmd_integrate")` against a name NOTHING ELSE in the repository referenced, so
    when `rl67b0` shipped the verb as `handle_integrate_command` the conditional silently froze in its
    pre-`rl67b0` state and kept telling operators "no `aw integrate` verb exists yet". Nothing failed.
    """

    def test_the_hint_names_the_integrate_verb_that_really_exists(self):
        hint = att.lane_remedy_hint()
        self.assertIn("aw oc integrate", hint)
        self.assertNotIn("no `aw integrate` verb exists yet", hint)

    def test_the_hint_names_the_CONCRETE_command_when_given_an_id6(self):
        self.assertIn("aw oc integrate abc123", att.lane_remedy_hint("abc123"))
        # The no-argument call must keep working: it is part of the function's contract.
        self.assertIn("<id6>", att.lane_remedy_hint())

    def test_the_PROBED_SYMBOL_really_exists_on_BOTH_hosts(self):
        """THE PIN. If the probed name disappears or is renamed again, THIS fails loudly.

        Both hosts are asserted because the hint claims a route that must not be host-specific fiction.
        """
        from agent_workflows import agy_runipd, oc_runipd

        self.assertTrue(
            hasattr(oc_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL),
            "oc_runipd lost {0}; lane_remedy_hint would silently fall back to the manual "
            "hint again".format(att.LANE_INTEGRATE_PROBE_SYMBOL),
        )
        self.assertTrue(
            hasattr(agy_runipd, att.LANE_INTEGRATE_PROBE_SYMBOL),
            "agy_runipd lost {0}".format(att.LANE_INTEGRATE_PROBE_SYMBOL),
        )

    def test_it_DEGRADES_to_the_manual_hint_when_the_verb_is_genuinely_absent(self):
        """The rule the function keeps: do not print a verb that does not exist.

        Probing for a name that is really absent is what proves the conditional is LIVE rather than
        effectively constant, which is precisely what the old `cmd_integrate` probe had become.
        """
        with mock.patch.object(att, "LANE_INTEGRATE_PROBE_SYMBOL", "no_such_symbol"):
            hint = att.lane_remedy_hint()
        self.assertIn("no `aw integrate` verb exists yet", hint)
        self.assertNotIn("aw oc integrate", hint)

    def test_the_stranded_row_carries_the_concrete_remedy(self):
        with tempfile.TemporaryDirectory() as td:
            root = StrandedLaneViewTests()._fixture(Path(td))
            with mock.patch(
                "agent_workflows.run_viewer.driver_holder_state", return_value="none"
            ):
                drift = att.stranded_lane_drift(root)
            self.assertEqual(len(drift), 1)
            self.assertIn("aw oc integrate lane01", drift[0].detail)


class SharedLifecycleResolverTests(unittest.TestCase):
    """The board renders lifecycle state through the SHARED resolver (spec `uonrjg` R10.3).

    Added by plan `f9t5hz`. These assert the PROPERTIES of the conversion rather than a snapshot, so
    they survive a future palette amendment in the spec while still failing if this module reacquires
    a lifecycle table of its own or breaks criterion A10.
    """

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

    def test_no_local_lifecycle_palette_remains(self):
        """Criterion A17 / R10.3: the local `_STATUS_COLOR_256` table is GONE, not merely unused.

        `_CLASS_COLOR_256` deliberately SURVIVES: its keys are the five cross-tree attention CLASS
        constants, which spec Section 3 lists as an explicit NON-GOAL, and it colors only the
        section headers of the non-columnar board.
        """

        self.assertFalse(hasattr(att, "_STATUS_COLOR_256"))
        self.assertEqual(
            set(att._CLASS_COLOR_256),
            {A.ACTIVE, A.READY, A.BLOCKED, A.DONE, A.PARKED},
        )

    def test_a10_glyph_id6_and_status_share_one_escape_and_type_has_none(self):
        """Criterion A10, asserted on RAW escapes, in both directions.

        The positive half (glyph, id6 and status word carry the SAME code) and the negative half (the
        artifact TYPE carries NONE) are both required, and the negative half is the one that
        regressed silently before this conversion: the type word was painted 33 bold.
        """

        item = self._item("plans", "approved", ".aw/records/plans/pending/p.ipd.md")
        row = self._row(item)
        resolved = self._LS.resolve(self._LS.FAMILY_PLANS, "approved")
        code = resolved.style.color
        prefix = f"\033[1;38;5;{code}m"
        glyph = self._LS.style_for(resolved.stage).unicode
        self.assertIn(f"{prefix}{glyph}\033[0m", row)
        self.assertIn(f"{prefix}approved\033[0m", row)
        self.assertIn(f"{prefix}aaa111\033[0m", row)
        # The type word is present and PLAIN. Asserted as an adjacency so a bare `assertNotIn` on the
        # escape cannot pass merely because the column vanished.
        self.assertIn("approved\033[0m plan ", row)
        self.assertNotIn(f"\033[1;38;5;{att._TREE_COLOR_256}mplan", row)

    def test_the_three_statuses_that_used_to_borrow_a_class_color(self):
        """The wrong-color defect this child closes, per spec Section 6.

        These three pass `attention_contract.class_of` yet were ABSENT from the old local table, so
        each fell through to the attention CLASS palette (or gray) instead of its own stage. They are
        the only reachable fallthroughs: `class_of` is total and RAISES for anything unmapped, so an
        unrecognized status never reaches a render site at all.
        """

        expected = {
            ("plans", "auto-approved"): self._LS.READY,
            ("backlog", "graduated"): self._LS.ACTIVE,
            ("research", "archive"): self._LS.PARKED,
        }
        for (tree, status), stage in expected.items():
            with self.subTest(tree=tree, status=status):
                resolved = self._LS.resolve(att._LIFECYCLE_FAMILY_BY_TREE[tree], status)
                self.assertEqual(resolved.stage, stage)
                item = self._item(tree, status, f".aw/records/{tree}/x.md")
                row = self._row(item)
                style = resolved.style
                bold = "1;" if style.bold else ""
                self.assertIn(
                    f"\033[{bold}38;5;{style.color}m{style.unicode}\033[0m", row
                )

    def test_class_of_raises_rather_than_reaching_a_render_site(self):
        """Why criterion A20's `?`-row is unreachable HERE, pinned so nobody tests for one.

        The resolver owes A20 and views that can receive an unmapped value owe its rendering. This
        board cannot: an unmapped status becomes an `attention.unknown-status` violation upstream.
        """

        with self.assertRaises(A.UnknownNativeStatus):
            A.class_of("plans", "bogus-status")

    def test_the_glyph_column_pads_by_rendered_width_not_codepoints(self):
        """Section 9.4: a variation-selector-bearing glyph occupies the same COLUMNS as a plain one.

        `⚠︎` is U+26A0 U+FE0E, i.e. 2 code points and 1 rendered column, so a `len()`-based pad would
        leave its cell one column short of every other row's. Measured here on real rendered rows.
        """

        blocked = self._item(
            "specs", "deferred", ".aw/records/specs/s.spec.md", id6="bbb222"
        )
        ready = self._item(
            "plans", "approved", ".aw/records/plans/pending/p.ipd.md", id6="ccc333"
        )
        blocked_glyph = self._LS.style_for(self._LS.BLOCKED).unicode
        ready_glyph = self._LS.style_for(self._LS.READY).unicode
        # The premise: one is a 2-codepoint grapheme, the other is not.
        self.assertEqual(len(blocked_glyph), 2)
        self.assertEqual(self._T.visible_width(blocked_glyph), 1)
        self.assertEqual(len(ready_glyph), 1)
        # The consequence: the status WORD starts at the same rendered column in both rows.
        # `render_table` directly, because the UNCOLORED `render_board` deliberately emits the stable
        # machine `- [tree] path (status)` form instead of the columnar table.
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
        # And the VS is intact in the rendered cell, not severed (criterion A15 / A5).
        self.assertIn(blocked_glyph, rows["deferred"])
        self.assertNotIn("\u26a0\ufe0f", plain)

    def test_machine_output_carries_no_ansi(self):
        """Criterion A14 as a characterization test: `--agent`/`--json` were already ANSI-free.

        Pinned so this conversion cannot leak an escape into machine output. The plain human board is
        included because it is the form an agent greps (`- [tree] path (status)`).
        """

        item = self._item("plans", "approved", ".aw/records/plans/pending/p.ipd.md")
        payload = att.render_json([item], [])
        self.assertNotIn("\033", payload)
        plain = att.render_board(
            [item], [], show_all=True, term=self._T.Term(color=False)
        )
        self.assertNotIn("\033", plain)
        self.assertIn("- [plans] .aw/records/plans/pending/p.ipd.md (approved)", plain)


def core_Drift(*args, **kw):
    from agent_workflows import artifact_core

    return artifact_core.Drift(*args, **kw)


if __name__ == "__main__":
    unittest.main()
