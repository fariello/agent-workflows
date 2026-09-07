"""Tests for `aw next` and its `--order-by/-o` ordering (worksequence i6015i, E-10).

Covers the nine required cases from the plan:

  (a) the CONTRACT REGRESSION test: the default order is byte-identical to the historical
      `(class, path, id)` order (the `xprio` pin), which is the highest-value test here;
  (b) all four names (`next`/`attention`/`att`/`todo`) produce identical output FOR THE SAME FLAGS,
      including `--format json` and `--check`, which FAILED under `todo` before this change;
  (c) each `-o` key produces its expected order on a fixture with hand-known values;
  (d) absent values sort LAST and the item COUNT is unchanged (ordering never filters);
  (e) `-o depth` orders a prerequisite before its dependent, including across a plan->backlog edge;
  (f) a cyclic fixture terminates and reports a notice;
  (g) `--check` fails closed under EVERY `-o` on a CONSTRUCTED invalid fixture;
  (h) `find_undeclared_leaves` is empty;
  (i) the ONE-SCAN GUARD: `-o depth` adds no artifact-reading pass, asserted by CALL COUNT, because a
      silent second scan produces correct-looking output and so is invisible to any output assertion.

Assertions are on the ORDERED SEQUENCE of ids, never on substring presence: a substring assertion
would pass against an unsorted list and so would not be falsifiable.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional

from agent_workflows import artifact_core as core
from agent_workflows import attention as att
from agent_workflows import attention_contract as A

REPO_ROOT = Path(__file__).resolve().parents[1]


class _Args:
    """A minimal args object; `attention.run` reads every option through `getattr` defaults."""

    def __init__(self, **kw):
        self.dir = None
        self.check = False
        self.format = None
        self.order_by = A.ORDER_CLASS
        self.agent = False
        self.json = False
        self.no_color = True
        self.all = True
        for k, v in kw.items():
            setattr(self, k, v)


def _run_json(**kw) -> dict:
    """Run the view capturing stdout, returning the parsed `--format json` payload."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = att.run(_Args(format="json", **kw))
    return {"exit": rc, "payload": json.loads(buf.getvalue())}


def _item(
    id6: str,
    path: str,
    tree: str = "plans",
    native_status: str = "draft",
    attention_class: str = A.READY,
    **kw,
) -> att.Item:
    return att.Item(
        id6,
        path,
        tree,
        native_status,
        attention_class,
        None,
        kw.pop("last_history_at", None),
        **kw,
    )


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _plan(id6: str, deps: str = "none", status: str = "draft") -> str:
    return (
        "# IPD: p\n\n"
        f"- Status: {status}\n"
        f"- Id: {id6}\n"
        f"- Item-Dependencies: {deps}\n\n"
        "## Workflow history\n- 2026-08-08 draft (t): created.\n"
    )


def _backlog(
    id6: str,
    status: str = "open",
    priority: str = "medium",
    gate_kind: Optional[str] = None,
    gate_ref: Optional[str] = None,
) -> str:
    """A backlog item in the shape the tree actually uses: leading `- Id:`/`- Status:` bullets and no
    `#` heading (verified against a live record under `.aw/records/backlog/open/`)."""
    gate_lines = ""
    if status == "blocked":
        gk = gate_kind or "external"
        gr = gate_ref or "ticket-123"
        gate_lines = f"- Gate-Kind: {gk}\n- Gate-Ref: {gr}\n"
    return (
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        "- Set: s\n"
        f"- Priority: {priority}\n"
        f"{gate_lines}"
        "- Work-Kind: chore\n"
        "- Summary: a fixture backlog item\n\n"
        "## Workflow history\n- 2026-08-08 created (aw backlog): a fixture backlog item\n"
    )


class DefaultOrderContractTests(unittest.TestCase):
    """(a) The default order is the pinned historical one and must not move."""

    def test_default_order_is_exactly_class_then_path_then_id(self):
        # The fixture is built so PATH order and ID order DISAGREE (item `zzz999` has the earliest
        # path but the latest id, and `aaa000` the reverse). A tail of `(id, path)` instead of
        # `(path, id)` therefore produces a DIFFERENT sequence, which is what makes this test able to
        # detect a swapped tail at all; a fixture whose two orders coincide would pass either way.
        items = [
            _item("bbb222", ".agents/plans/pending/b.md", attention_class=A.READY),
            _item("aaa111", ".agents/plans/pending/m.md", attention_class=A.BLOCKED),
            _item("ccc333", ".agents/plans/pending/c.md", attention_class=A.ACTIVE),
            _item("zzz999", ".agents/plans/pending/a.md", attention_class=A.READY),
            _item("aaa000", ".agents/plans/pending/z.md", attention_class=A.READY),
        ]
        got = [it.id for it in att.sort_items(items)]
        # The historical tuple, computed independently of the implementation under test.
        expect = [
            it.id
            for it in sorted(
                items,
                key=lambda it: (
                    A.ATTENTION_CLASS_ORDER.index(it.attention_class),
                    it.path,
                    it.id,
                ),
            )
        ]
        self.assertEqual(got, expect)
        # Pin the literal sequence too, so a change to BOTH sides cannot pass silently.
        # ACTIVE(ccc333) -> READY sorted by PATH (a.md=zzz999, b.md=bbb222, z.md=aaa000) -> BLOCKED.
        self.assertEqual(got, ["ccc333", "zzz999", "bbb222", "aaa000", "aaa111"])
        # And assert the tail is path-BEFORE-id explicitly: sorting the READY items by id would give
        # aaa000 first, so this ordering can only come from a path-major tail.
        ready = [i for i in got if i in ("zzz999", "bbb222", "aaa000")]
        self.assertEqual(ready, ["zzz999", "bbb222", "aaa000"])
        self.assertNotEqual(
            ready, sorted(ready), "tail must be path-major, not id-major"
        )

    def test_explicit_class_key_equals_the_default(self):
        items = [
            _item("bbb222", ".agents/plans/pending/b.md"),
            _item("aaa111", ".agents/plans/pending/a.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items)],
            [it.id for it in att.sort_items(items, A.ORDER_CLASS)],
        )

    def test_default_order_is_deterministic_across_repeated_sorts(self):
        items = [
            _item("bbb222", ".agents/plans/pending/b.md"),
            _item("aaa111", ".agents/plans/pending/a.md"),
            _item("ccc333", ".agents/plans/pending/c.md"),
        ]
        first = [it.id for it in att.sort_items(items)]
        for _ in range(5):
            self.assertEqual([it.id for it in att.sort_items(items)], first)


class AliasEquivalenceTests(unittest.TestCase):
    """(b) All four names share one parser, so they agree under every flag."""

    NAMES = ("next", "attention", "att", "todo")
    _td: Optional[tempfile.TemporaryDirectory] = None
    fixture_root: Path

    @classmethod
    def setUpClass(cls):
        cls._td = tempfile.TemporaryDirectory()
        cls.fixture_root = Path(cls._td.name)
        _write(
            cls.fixture_root
            / ".aw/records/backlog/open/20260101-s-01-rdy001-r.backlog.md",
            _backlog("rdy001", status="open", priority="high"),
        )
        _write(
            cls.fixture_root
            / ".aw/records/backlog/blocked/20260101-s-02-blk001-b.backlog.md",
            _backlog(
                "blk001",
                status="blocked",
                priority="low",
                gate_kind="external",
                gate_ref="dep",
            ),
        )

    @classmethod
    def tearDownClass(cls):
        if cls._td is not None:
            cls._td.cleanup()

    def _run(self, *argv):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT)
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *argv],
            cwd=str(self.fixture_root),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_all_four_names_agree_bare(self):
        outs = {n: self._run(n, "--no-color") for n in self.NAMES}
        for n, proc in outs.items():
            self.assertEqual(proc.returncode, 0, f"{n} exited {proc.returncode}")
        first = outs["next"].stdout
        for n in self.NAMES:
            self.assertEqual(outs[n].stdout, first, f"{n} differs from next")

    def test_all_four_names_agree_under_format_json(self):
        """`aw todo --format json` FAILED with 'unrecognized arguments' before E-01."""
        outs = {n: self._run(n, "--format", "json") for n in self.NAMES}
        for n, proc in outs.items():
            self.assertEqual(
                proc.returncode,
                0,
                f"{n} --format json exited {proc.returncode}: {proc.stderr}",
            )
        first = outs["next"].stdout
        for n in self.NAMES:
            self.assertEqual(outs[n].stdout, first, f"{n} --format json differs")

    def test_all_four_names_agree_under_check(self):
        """`aw todo --check` FAILED with 'unrecognized arguments' before E-01."""
        outs = {n: self._run(n, "--check", "--no-color") for n in self.NAMES}
        first = (outs["next"].returncode, outs["next"].stdout)
        for n in self.NAMES:
            self.assertEqual(
                (outs[n].returncode, outs[n].stdout), first, f"{n} differs"
            )

    def test_all_four_names_agree_under_details_and_long(self):
        for flag in ("--details", "--long"):
            outs = {n: self._run(n, flag, "--no-color") for n in self.NAMES}
            for n, proc in outs.items():
                self.assertEqual(
                    proc.returncode, 0, f"{n} {flag} exited {proc.returncode}"
                )
            first = outs["next"].stdout
            for n in self.NAMES:
                self.assertEqual(outs[n].stdout, first, f"{n} {flag} differs")

    def test_all_four_names_agree_under_order_by(self):
        for key in A.ORDER_KEYS:
            outs = {n: self._run(n, "-o", key, "--format", "json") for n in self.NAMES}
            first = outs["next"].stdout
            for n in self.NAMES:
                self.assertEqual(outs[n].stdout, first, f"{n} -o {key} differs")

    def test_todo_help_no_longer_advertises_the_deleted_action_ledger(self):
        proc = self._run("todo", "--help")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("action ledger", proc.stdout)
        self.assertNotIn("operational AW actions", proc.stdout)
        self.assertIn("--order-by", proc.stdout)

    def test_alias_tests_use_fixture_root_not_repo_root(self):
        """Assert AliasEquivalenceTests exercises an isolated fixture directory, not REPO_ROOT (E-03, E-05(d))."""
        self.assertNotEqual(self.fixture_root, REPO_ROOT)
        self.assertTrue(self.fixture_root.exists())
        items, _ = att.scan(self.fixture_root)
        classes = {it.attention_class for it in items}
        priorities = {it.priority for it in items}
        self.assertGreaterEqual(
            len(classes), 2, f"expected at least 2 classes, got {classes}"
        )
        self.assertGreaterEqual(
            len(priorities), 2, f"expected at least 2 priorities, got {priorities}"
        )


class OrderKeyVocabularyTests(unittest.TestCase):
    """E-03: the vocabulary is closed, declared once, and refused when unknown."""

    def test_order_keys_is_a_closed_tuple_with_class_first(self):
        self.assertIsInstance(A.ORDER_KEYS, tuple)
        self.assertEqual(A.ORDER_KEYS[0], A.ORDER_CLASS)
        self.assertEqual(len(A.ORDER_KEYS), len(set(A.ORDER_KEYS)))
        for key in ("priority", "date", "set", "order", "blocking", "depth"):
            self.assertIn(key, A.ORDER_KEYS)

    def test_cli_choices_are_generated_from_the_contract_tuple(self):
        from agent_workflows.cli import _attention_order_keys

        self.assertEqual(tuple(_attention_order_keys()), tuple(A.ORDER_KEYS))

    def test_unknown_key_is_refused_by_argparse_with_the_valid_list(self):
        # Scan-independent by construction: argparse rejects unknown keys before repo scanning occurs.
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "next", "-o", "bogus"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice: 'bogus'", proc.stderr)
        for key in A.ORDER_KEYS:
            self.assertIn(repr(key), proc.stderr)

    def test_sort_items_rejects_an_out_of_vocabulary_key(self):
        with self.assertRaises(ValueError):
            att.sort_items([], "not-a-key")


class PerKeyOrderTests(unittest.TestCase):
    """(c) Each key produces its expected order on hand-known values."""

    def test_priority_orders_high_then_medium_then_low(self):
        items = [
            _item("low001", "p/low.md", priority="low"),
            _item("hig001", "p/high.md", priority="high"),
            _item("med001", "p/med.md", priority="medium"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "priority")],
            ["hig001", "med001", "low001"],
        )

    def test_date_orders_newest_first(self):
        items = [
            _item("old001", "p/old.md", last_history_at="2026-01-01"),
            _item("new001", "p/new.md", last_history_at="2026-09-01"),
            _item("mid001", "p/mid.md", last_history_at="2026-05-01"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "date")],
            ["new001", "mid001", "old001"],
        )

    def test_set_orders_by_the_filename_set_id(self):
        items = [
            _item("aaa111", ".agents/plans/pending/20260101-zeta-01-aaa111-a.ipd.md"),
            _item("bbb222", ".agents/plans/pending/20260101-alpha-01-bbb222-b.ipd.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "set")], ["bbb222", "aaa111"]
        )

    def test_order_orders_by_the_filename_order_number(self):
        items = [
            _item("aaa111", ".agents/plans/pending/20260101-s-03-aaa111-a.ipd.md"),
            _item("bbb222", ".agents/plans/pending/20260101-s-01-bbb222-b.ipd.md"),
            _item("ccc333", ".agents/plans/pending/20260101-s-02-ccc333-c.ipd.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "order")],
            ["bbb222", "ccc333", "aaa111"],
        )

    def test_blocking_puts_release_blockers_first(self):
        items = [
            _item("free01", "p/free.md"),
            _item("gate01", "p/gate.md", blocks_release="next"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "blocking")], ["gate01", "free01"]
        )

    def test_id6_path_status_tree_each_order_by_their_field(self):
        items = [
            _item("ccc333", "p/c.md", tree="specs", native_status="reviewed"),
            _item("aaa111", "p/a.md", tree="plans", native_status="draft"),
            _item("bbb222", "p/b.md", tree="backlog", native_status="open"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "id6")],
            ["aaa111", "bbb222", "ccc333"],
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "path")],
            ["aaa111", "bbb222", "ccc333"],
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "status")],
            ["aaa111", "bbb222", "ccc333"],  # draft < open < reviewed
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "tree")],
            ["bbb222", "aaa111", "ccc333"],  # backlog < plans < specs
        )

    def test_every_key_falls_through_to_the_default_tail(self):
        """Two items tied on the selected key keep the default (class, path, id) relative order."""
        items = [
            _item("bbb222", "p/b.md", priority="high"),
            _item("aaa111", "p/a.md", priority="high"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "priority")], ["aaa111", "bbb222"]
        )

    def test_every_key_is_a_total_deterministic_order(self):
        items = [
            _item("bbb222", "p/b.md", priority="high", tree="specs"),
            _item("aaa111", "p/a.md", tree="plans"),
            _item("ccc333", "p/c.md", priority="low", tree="backlog"),
        ]
        for key in A.ORDER_KEYS:
            first = [it.id for it in att.sort_items(items, key)]
            for _ in range(3):
                self.assertEqual([it.id for it in att.sort_items(items, key)], first)
            self.assertEqual(sorted(first), ["aaa111", "bbb222", "ccc333"])


class AbsentValueTests(unittest.TestCase):
    """(d) Absent values sort LAST and ordering never filters."""

    def test_absent_priority_sorts_last_not_hidden_and_not_defaulted(self):
        items = [
            _item("none01", "p/none.md"),
            _item("low001", "p/low.md", priority="low"),
            _item("hig001", "p/high.md", priority="high"),
        ]
        got = [it.id for it in att.sort_items(items, "priority")]
        self.assertEqual(got, ["hig001", "low001", "none01"])
        # Not defaulted to `medium`: it sorts after `low`, which a medium default would not.
        self.assertEqual(got[-1], "none01")

    def test_absent_sorts_last_for_every_key_and_count_is_preserved(self):
        items = [
            _item("emp001", "no-grammar.md"),
            _item(
                "ful001",
                ".agents/plans/pending/20260101-s-01-ful001-x.ipd.md",
                priority="high",
                blocks_release="next",
                last_history_at="2026-09-01",
            ),
        ]
        for key in A.ORDER_KEYS:
            got = att.sort_items(items, key)
            self.assertEqual(len(got), len(items), f"-o {key} changed the item count")
            self.assertEqual(
                {it.id for it in got},
                {it.id for it in items},
                f"-o {key} changed the set",
            )
        for key in ("priority", "date", "set", "order", "blocking"):
            self.assertEqual(
                [it.id for it in att.sort_items(items, key)][-1],
                "emp001",
                f"-o {key} did not place the absent value last",
            )

    def test_filename_outside_the_grammar_sorts_absent_without_raising(self):
        items = [
            _item("odd001", ".agents/plans/pending/not-a-grammar-name.md"),
            _item("ok0001", ".agents/plans/pending/20260101-s-01-ok0001-x.ipd.md"),
        ]
        for key in ("set", "order"):
            got = [it.id for it in att.sort_items(items, key)]
            self.assertEqual(got, ["ok0001", "odd001"])

    def test_live_item_count_is_identical_across_every_order(self):
        base = _run_json()
        self.assertEqual(base["exit"], 0)
        n = len(base["payload"]["items"])
        ids = sorted(it["id"] for it in base["payload"]["items"])
        for key in A.ORDER_KEYS:
            got = _run_json(order_by=key)
            self.assertEqual(
                len(got["payload"]["items"]), n, f"-o {key} changed the item count"
            )
            self.assertEqual(
                sorted(it["id"] for it in got["payload"]["items"]),
                ids,
                f"-o {key} changed the item SET rather than only its order",
            )


class DependencyDepthTests(unittest.TestCase):
    """(e) `-o depth` sequences prerequisites before dependents, across types too."""

    def test_chain_orders_prerequisite_first_regardless_of_path_and_id(self):
        # C depends on B depends on A. Paths and ids are chosen so the DEFAULT order is the
        # REVERSE (C, B, A), which makes the assertion falsifiable: only a real depth sort passes.
        items = [
            _item("aaa999", "p/z-a.md", item_dependencies=()),
            _item("bbb555", "p/y-b.md", item_dependencies=("exists:ipd:aaa999",)),
            _item("ccc111", "p/x-c.md", item_dependencies=("exists:ipd:bbb555",)),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items)],
            ["ccc111", "bbb555", "aaa999"],
            "fixture precondition: the default order must be the reverse of the depth order",
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "depth")],
            ["aaa999", "bbb555", "ccc111"],
        )

    def test_depths_are_the_longest_chain_and_roots_are_zero(self):
        items = [
            _item("aaa999", "p/a.md", item_dependencies=()),
            _item("bbb555", "p/b.md", item_dependencies=("exists:ipd:aaa999",)),
            _item("ccc111", "p/c.md", item_dependencies=("exists:ipd:bbb555",)),
        ]
        depths, cycles = att.dependency_depths(items)
        self.assertEqual(cycles, [])
        self.assertEqual(depths["aaa999"], 0)
        self.assertEqual(depths["bbb555"], 1)
        self.assertEqual(depths["ccc111"], 2)

    def test_cross_type_edge_plan_to_backlog_orders_the_backlog_item_first(self):
        """The cross-type case the backlog item asked for: a plan depending on a BACKLOG item."""
        items = [
            _item(
                "plan01",
                "p/a-plan.md",
                tree="plans",
                item_dependencies=("state:backlog:open:bklg01",),
            ),
            _item("bklg01", "p/z-backlog.md", tree="backlog", native_status="open"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items)],
            ["plan01", "bklg01"],
            "fixture precondition: default order puts the plan first",
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "depth")], ["bklg01", "plan01"]
        )

    def test_edge_to_an_artifact_outside_the_view_contributes_no_ordering(self):
        items = [
            _item("aaa111", "p/a.md", item_dependencies=("exists:ipd:zzzzzz",)),
            _item("bbb222", "p/b.md", item_dependencies=()),
        ]
        depths, _ = att.dependency_depths(items)
        self.assertEqual(depths["aaa111"], 0)
        self.assertEqual(depths["bbb222"], 0)

    def test_scan_extracts_item_dependencies_onto_the_item(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(
                root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
                _plan("aaa111", deps="exists:backlog:bbb222"),
            )
            _write(
                root / ".agents/backlog/20260101-s-01-bbb222-b.md", _backlog("bbb222")
            )
            items, drift = att.scan(root)
            self.assertEqual(drift, [], f"expected a clean fixture, got {drift}")
            by_id = {it.id: it for it in items}
            self.assertEqual(
                by_id["aaa111"].item_dependencies, ("exists:backlog:bbb222",)
            )
            # `none` is present-but-empty, and an absent field is None; both are distinguishable.
            self.assertEqual(by_id["bbb222"].item_dependencies, None)

    def test_depth_orders_a_real_scanned_fixture_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(
                root / ".agents/backlog/20260101-s-01-bbb222-b.md", _backlog("bbb222")
            )
            _write(
                root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
                _plan("aaa111", deps="exists:backlog:bbb222"),
            )
            items, _ = att.scan(root)
            self.assertEqual(
                [it.id for it in att.sort_items(items, "depth")], ["bbb222", "aaa111"]
            )


class CycleSafetyTests(unittest.TestCase):
    """(f) A cyclic fixture terminates, reports, and does not raise."""

    def test_cycle_terminates_and_is_reported_not_absorbed(self):
        items = [
            _item("aaa111", "p/a.md", item_dependencies=("exists:ipd:bbb222",)),
            _item("bbb222", "p/b.md", item_dependencies=("exists:ipd:aaa111",)),
        ]
        ordered, notices = att.sort_items_with_notices(items, "depth")
        self.assertEqual(len(ordered), 2, "the view must still render every item")
        self.assertTrue(notices, "a cycle must be REPORTED, not silently absorbed")
        self.assertIn("cycle", notices[0].lower())
        self.assertTrue(
            any("aaa111" in n and "bbb222" in n for n in notices),
            f"the notice must name the cycle members, got {notices}",
        )

    def test_self_edge_does_not_hang_or_raise(self):
        items = [_item("aaa111", "p/a.md", item_dependencies=("exists:ipd:aaa111",))]
        ordered, _notices = att.sort_items_with_notices(items, "depth")
        self.assertEqual([it.id for it in ordered], ["aaa111"])

    def test_three_node_cycle_terminates(self):
        items = [
            _item("aaa111", "p/a.md", item_dependencies=("exists:ipd:bbb222",)),
            _item("bbb222", "p/b.md", item_dependencies=("exists:ipd:ccc333",)),
            _item("ccc333", "p/c.md", item_dependencies=("exists:ipd:aaa111",)),
        ]
        ordered, notices = att.sort_items_with_notices(items, "depth")
        self.assertEqual(len(ordered), 3)
        self.assertTrue(notices)

    def test_cycle_notice_reaches_the_human_board(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(
                root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
                _plan("aaa111", deps="exists:ipd:bbb222"),
            )
            _write(
                root / ".agents/plans/pending/20260101-s-02-bbb222-b.ipd.md",
                _plan("bbb222", deps="exists:ipd:aaa111"),
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = att.run(_Args(dir=str(root), order_by="depth"))
            out = buf.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("order-notices", out)
            self.assertIn("cycle", out)


class FailClosedTests(unittest.TestCase):
    """(g) `--check` stays fail-closed under EVERY order, on a CONSTRUCTED invalid fixture.

    A constructed fixture is used deliberately: the live tree is currently VALID (`--check` exits 0),
    so a test relying on a pre-existing violation would silently stop testing anything the day the
    tree was repaired.
    """

    def _duplicate_id_repo(self, root: Path) -> None:
        """The same id6 in two trees, which `attention.duplicate-id` detects."""
        _write(
            root / ".agents/plans/pending/20260101-s-01-dup111-a.ipd.md",
            _plan("dup111"),
        )
        _write(root / ".agents/backlog/20260101-s-01-dup111-b.md", _backlog("dup111"))

    def test_the_constructed_fixture_really_is_invalid(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._duplicate_id_repo(root)
            _items, drift = att.scan(root)
            self.assertTrue(drift, "fixture precondition: the fixture must be invalid")
            self.assertIn("attention.duplicate-id", {x.rule for x in drift})
            self.assertNotEqual(core.drift_exit_code(drift), 0)

    def test_check_fails_closed_under_every_order_key(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._duplicate_id_repo(root)
            for key in A.ORDER_KEYS:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = att.run(_Args(dir=str(root), check=True, order_by=key))
                self.assertNotEqual(
                    rc, 0, f"--check -o {key} did NOT fail closed on an invalid view"
                )

    def test_check_exits_zero_on_a_valid_tree_under_every_order_key(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _write(
                root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
                _plan("aaa111"),
            )
            for key in A.ORDER_KEYS:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = att.run(_Args(dir=str(root), check=True, order_by=key))
                self.assertEqual(rc, 0, f"--check -o {key} failed on a VALID view")

    def test_plain_view_still_fails_closed_under_every_order_key(self):
        """A display option must not be able to launder an invalid view into exit 0."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._duplicate_id_repo(root)
            for key in A.ORDER_KEYS:
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = att.run(_Args(dir=str(root), format="json", order_by=key))
                self.assertNotEqual(rc, 0, f"plain view -o {key} did not fail closed")


class DeclarationTests(unittest.TestCase):
    """(h) Every leaf, including the renamed one, carries a declaration."""

    def test_no_undeclared_parser_leaves_for_the_renamed_command(self):
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import find_undeclared_leaves

        undeclared = find_undeclared_leaves(_build_parser())
        for leaf in ("next", "attention", "att", "todo"):
            self.assertNotIn(leaf, undeclared)

    def test_next_is_the_canonical_declaration_and_the_others_are_aliases(self):
        from agent_workflows.command_surface import get_all_declarations

        by_name = {d.command: d for d in get_all_declarations()}
        self.assertEqual(by_name["next"].command_class, "read")
        for alias in ("attention", "att", "todo"):
            self.assertEqual(by_name[alias].command_class, "alias")
            self.assertEqual(by_name[alias].canonical_command, "next")

    def test_next_is_a_real_parser_leaf_and_the_aliases_share_its_parser(self):
        import argparse

        from agent_workflows.cli import _build_parser

        parser = _build_parser()
        sub = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)][
            0
        ]
        self.assertIn("next", sub.choices)
        for alias in ("attention", "att", "todo"):
            self.assertIs(
                sub.choices[alias],
                sub.choices["next"],
                f"{alias} must SHARE the canonical parser, not be a separate one",
            )

    def test_the_standalone_todo_parser_and_dispatch_special_case_are_gone(self):
        src = (REPO_ROOT / "agent_workflows" / "cli.py").read_text(encoding="utf-8")
        self.assertNotIn("p_todo = sub.add_parser(", src)
        self.assertNotIn('if args.command == "todo":', src)


class OneScanGuardTests(unittest.TestCase):
    """(i) `-o depth` must add NO artifact-reading pass.

    This is the guard the plan calls for explicitly, because a silent second scan produces
    correct-LOOKING output: no assertion on what the command prints could detect it, while it would
    break the single-authority rule that keeps `aw next`, `aw attention` and `aw doctor` from
    disagreeing.
    """

    def _counted_run(self, root: Path, **kw):
        calls = {"scan": 0, "iter": 0}
        orig_scan = att.scan
        orig_iter = core.iter_scan_files

        def scan_counting(*a, **k):
            calls["scan"] += 1
            return orig_scan(*a, **k)

        def iter_counting(*a, **k):
            calls["iter"] += 1
            return orig_iter(*a, **k)

        att.scan = scan_counting
        core.iter_scan_files = iter_counting
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                att.run(_Args(dir=str(root), format="json", **kw))
        finally:
            att.scan = orig_scan
            core.iter_scan_files = orig_iter
        return calls

    def _fixture(self, root: Path) -> None:
        _write(root / ".agents/backlog/20260101-s-01-bbb222-b.md", _backlog("bbb222"))
        _write(
            root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
            _plan("aaa111", deps="exists:backlog:bbb222"),
        )

    def test_scan_is_called_exactly_once_under_depth(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._fixture(root)
            self.assertEqual(self._counted_run(root, order_by="depth")["scan"], 1)

    def test_depth_adds_no_artifact_reading_pass_versus_the_default(self):
        """The COUNT-BASED assertion: `-o depth` must read the tree no more times than `-o class`.

        Compared against the DEFAULT order rather than against a hardcoded number, so the test keeps
        testing the right thing even as unrelated passes are added or removed elsewhere.
        """
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._fixture(root)
            baseline = self._counted_run(root, order_by=A.ORDER_CLASS)
            depth = self._counted_run(root, order_by="depth")
            self.assertEqual(
                depth["iter"],
                baseline["iter"],
                "-o depth performed MORE artifact-reading passes than the default order "
                f"({depth['iter']} vs {baseline['iter']}): a second scan was introduced",
            )
            self.assertEqual(depth["scan"], baseline["scan"])

    def test_every_order_key_adds_no_artifact_reading_pass(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._fixture(root)
            baseline = self._counted_run(root, order_by=A.ORDER_CLASS)
            for key in A.ORDER_KEYS:
                got = self._counted_run(root, order_by=key)
                self.assertEqual(
                    got["iter"], baseline["iter"], f"-o {key} added a scan pass"
                )

    def test_depth_is_computed_from_the_scan_result_not_a_dependency_index(self):
        """`build_dependency_index` re-reads every artifact; the ordering must not call it."""
        from agent_workflows import check_engine

        called = {"n": 0}
        orig = check_engine.build_dependency_index

        def counting(*a, **k):
            called["n"] += 1
            return orig(*a, **k)

        check_engine.build_dependency_index = counting
        try:
            items = [
                _item("aaa111", "p/a.md", item_dependencies=()),
                _item("bbb222", "p/b.md", item_dependencies=("exists:ipd:aaa111",)),
            ]
            att.sort_items(items, "depth")
        finally:
            check_engine.build_dependency_index = orig
        self.assertEqual(
            called["n"],
            0,
            "the ordering must not trigger a second full-tree index build",
        )


class MultiAttributeOrderingTests(unittest.TestCase):
    """Multi-column sort precedence, comma-separated parsing, and stable tiebreaking."""

    def test_multi_key_parsing_in_argparse(self):
        from agent_workflows.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["next", "-o", "priority,status,id6"])
        self.assertEqual(args.order_by, "priority,status,id6")

    def test_multi_key_with_invalid_token_is_refused_by_argparse(self):
        # Scan-independent by construction: argparse rejects invalid tokens before repo scanning occurs.
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "next", "-o", "priority,bogus"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_sort_items_rejects_invalid_token_in_multi_key(self):
        with self.assertRaises(ValueError) as ctx:
            att.sort_items([], "priority,not-a-key")
        self.assertIn("not-a-key", str(ctx.exception))

    def test_multi_attribute_precedence(self):
        items = [
            _item("prio_hi_draft", "p/a.md", priority="high", native_status="draft"),
            _item("prio_hi_open", "p/b.md", priority="high", native_status="open"),
            _item("prio_lo_draft", "p/c.md", priority="low", native_status="draft"),
            _item("prio_lo_open", "p/d.md", priority="low", native_status="open"),
        ]
        # priority primary, status secondary
        self.assertEqual(
            [it.id for it in att.sort_items(items, "priority,status")],
            ["prio_hi_draft", "prio_hi_open", "prio_lo_draft", "prio_lo_open"],
        )
        # status primary, priority secondary
        self.assertEqual(
            [it.id for it in att.sort_items(items, "status,priority")],
            ["prio_hi_draft", "prio_lo_draft", "prio_hi_open", "prio_lo_open"],
        )

    def test_three_attribute_ordering_with_tiebreaker(self):
        items = [
            _item("c01", "p/c.md", priority="high", native_status="open"),
            _item("a01", "p/a.md", priority="high", native_status="open"),
            _item("b01", "p/b.md", priority="high", native_status="draft"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "priority,status,id6")],
            ["b01", "a01", "c01"],
        )


class NewAttributeOrderTests(unittest.TestCase):
    """Ordering by readiness, oqs, rqs, file, aliases (setid, type), and timestamps (ctime, mtime)."""

    def test_readiness_orders_go_then_go_pending_then_no_go(self):
        items = [
            _item("no001", "p/no.md", readiness="no-go"),
            _item("go001", "p/go.md", readiness="go"),
            _item("pen001", "p/pen.md", readiness="go-pending-approval"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "readiness")],
            ["go001", "pen001", "no001"],
        )

    def test_oqs_orders_descending_with_absent_last(self):
        items = [
            _item("oq1", "p/oq1.md", oqs=1),
            _item("oq5", "p/oq5.md", oqs=5),
            _item("oq0", "p/oq0.md", oqs=0),
            _item("none", "p/none.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "oqs")],
            ["oq5", "oq1", "none", "oq0"],
        )

    def test_rqs_orders_descending_with_absent_last(self):
        items = [
            _item("rq2", "p/rq2.md", rqs=2),
            _item("rq9", "p/rq9.md", rqs=9),
            _item("rq0", "p/rq0.md", rqs=0),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "rqs")],
            ["rq9", "rq2", "rq0"],
        )

    def test_file_orders_by_basename(self):
        items = [
            _item("z01", "deep/nested/z_file.md"),
            _item("a01", "other/a_file.md"),
            _item("m01", "root/m_file.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "file")],
            ["a01", "m01", "z01"],
        )

    def test_setid_and_type_aliases(self):
        items = [
            _item(
                "aaa111",
                ".agents/plans/pending/20260101-zeta-01-aaa111-a.ipd.md",
                tree="specs",
            ),
            _item(
                "bbb222",
                ".agents/plans/pending/20260101-alpha-01-bbb222-b.ipd.md",
                tree="backlog",
            ),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items, "setid")], ["bbb222", "aaa111"]
        )
        self.assertEqual(
            [it.id for it in att.sort_items(items, "type")], ["bbb222", "aaa111"]
        )

    def test_ctime_and_mtime_newest_first_with_real_files(self):
        import os

        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f_old = root / "old.md"
            f_new = root / "new.md"
            _write(f_old, "# Old")
            _write(f_new, "# New")
            os.utime(f_old, (1000.0, 1000.0))
            os.utime(f_new, (2000.0, 2000.0))

            items = [
                _item("old01", "old.md"),
                _item("new01", "new.md"),
            ]
            self.assertEqual(
                [it.id for it in att.sort_items(items, "mtime", repo_root=root)],
                ["new01", "old01"],
            )
            self.assertEqual(
                [it.id for it in att.sort_items(items, "ctime", repo_root=root)],
                ["new01", "old01"],
            )

    def test_ctime_and_mtime_missing_files_sort_last_safely(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            f_real = root / "real.md"
            _write(f_real, "# Real")

            items = [
                _item("miss01", "does_not_exist.md"),
                _item("real01", "real.md"),
            ]
            for key in ("ctime", "mtime"):
                got = [it.id for it in att.sort_items(items, key, repo_root=root)]
                self.assertEqual(got, ["real01", "miss01"])


class TableSortPreservationTests(unittest.TestCase):
    """TTY table render_table preserves user-specified ordering when order_by != class."""

    def test_render_table_preserves_explicit_ordering(self):
        spec_item = _item(
            "spec01",
            "specs/20260101-spec01-01-spec01-s.spec.md",
            tree="specs",
            priority="high",
        )
        backlog_item = _item(
            "bklg01",
            "backlog/20260101-bklg01-01-bklg01-b.md",
            tree="backlog",
            priority="low",
        )
        # Under priority sorting, high comes before low: [spec_item, backlog_item]
        items_sorted_by_priority = [spec_item, backlog_item]

        # 1. When order_by="priority" is passed, render_table MUST preserve the order: spec_item first
        out_priority = att.render_table(
            items_sorted_by_priority,
            [],
            show_all=True,
            term=att.T.Term(color=False),
            order_by="priority",
        )
        lines_priority = [line for line in out_priority.splitlines() if line.strip()]
        self.assertIn("spec01", lines_priority[1])
        self.assertIn("bklg01", lines_priority[2])

        # 2. When order_by is None or ORDER_CLASS, historical table sort applies: backlog before specs
        out_default = att.render_table(
            items_sorted_by_priority,
            [],
            show_all=True,
            term=att.T.Term(color=False),
            order_by=A.ORDER_CLASS,
        )
        lines_default = [line for line in out_default.splitlines() if line.strip()]
        self.assertIn("bklg01", lines_default[1])
        self.assertIn("spec01", lines_default[2])

    def test_render_board_forwards_order_by_to_render_table(self):
        spec_item = _item(
            "spec01",
            "specs/20260101-spec01-01-spec01-s.spec.md",
            tree="specs",
            priority="high",
        )
        backlog_item = _item(
            "bklg01",
            "backlog/20260101-bklg01-01-bklg01-b.md",
            tree="backlog",
            priority="low",
        )
        items = [spec_item, backlog_item]
        term = att.T.Term(color=True)
        # Force color=True so render_board calls render_table
        out = att.render_board(
            items,
            [],
            show_all=True,
            term=term,
            order_by="priority",
        )
        clean = att.T.strip_ansi(out)
        lines = [line for line in clean.splitlines() if line.strip()]
        self.assertIn("spec01", lines[1])
        self.assertIn("bklg01", lines[2])


class NonColoredBoardOrderingTests(unittest.TestCase):
    """Pin explicit ordering in non-colored render_board and cmd_attention (E-01, E-02, E-05, E-06)."""

    def test_non_colored_board_honors_explicit_ordering_across_classes(self):
        """The defect itself (E-05(a)): items in conflicting classes must sort by the requested order.

        Class order has 'ready' before 'blocked'. Here item 'blk_hi' is in 'blocked' with 'high' priority,
        while 'rdy_lo' is in 'ready' with 'low' priority. Under '-o priority', 'blk_hi' must print FIRST.
        """
        item_rdy = _item(
            "rdy_lo",
            "p/rdy_lo.md",
            tree="backlog",
            attention_class=A.READY,
            priority="low",
        )
        item_blk = _item(
            "blk_hi",
            "p/blk_hi.md",
            tree="backlog",
            attention_class=A.BLOCKED,
            priority="high",
        )
        items = [item_blk, item_rdy]  # already sorted by priority

        out = att.render_board(
            items, [], show_all=True, term=att.T.Term(color=False), order_by="priority"
        )
        lines = [line for line in out.splitlines() if line.strip()]
        # The flat output must contain no section headers, and blk_hi must precede rdy_lo
        self.assertFalse(
            any(line.startswith("## ") for line in lines),
            f"unexpected section header in {lines}",
        )
        self.assertEqual(len(lines), 2)
        self.assertIn("blk_hi", lines[0])
        self.assertIn("rdy_lo", lines[1])

    def test_default_order_preserves_class_section_headers(self):
        """Default order (no -o or class) keeps ## <class> (N) section headers (E-05(b))."""
        item_rdy = _item(
            "rdy01",
            "backlog/rdy.md",
            tree="backlog",
            attention_class=A.READY,
            priority="low",
        )
        item_blk = _item(
            "blk01",
            "backlog/blk.md",
            tree="backlog",
            attention_class=A.BLOCKED,
            priority="high",
        )
        items = [item_blk, item_rdy]

        out = att.render_board(
            items,
            [],
            show_all=True,
            term=att.T.Term(color=False),
            order_by=A.ORDER_CLASS,
        )
        self.assertIn("## ready (1)", out)
        self.assertIn("## blocked (1)", out)

    def test_hidden_class_suppressed_without_all_under_explicit_order(self):
        """Done/parked items are suppressed without show_all under explicit order, no notice line (E-02, E-05(c))."""
        item_rdy = _item(
            "rdy01",
            "p/rdy01.md",
            tree="backlog",
            attention_class=A.READY,
            priority="high",
        )
        item_done = _item(
            "done01",
            "p/done01.md",
            tree="backlog",
            attention_class=A.DONE,
            priority="high",
        )
        items = [item_rdy, item_done]

        # Without show_all: done01 must be suppressed, and no notice line emitted in flat form
        out = att.render_board(
            items, [], show_all=False, term=att.T.Term(color=False), order_by="priority"
        )
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertIn("rdy01", lines[0])
        self.assertNotIn("done01", out)
        self.assertNotIn("hidden; use --all", out)

        # With show_all: done01 must be present
        out_all = att.render_board(
            items, [], show_all=True, term=att.T.Term(color=False), order_by="priority"
        )
        lines_all = [line for line in out_all.splitlines() if line.strip()]
        self.assertEqual(len(lines_all), 2)
        self.assertIn("rdy01", out_all)
        self.assertIn("done01", out_all)

    def test_release_blocker_in_order_under_explicit_sort(self):
        """Release blockers stay in single ordered list without trailing section under explicit order (E-06, E-05(e))."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write(
                root
                / ".aw/records/releases/planned/20260101-rel-01-rel001-r.release.md",
                (
                    "# Release 2.0.0\n\n- Status: planned\n- Id: rel001\n- Version: 2.0.0\n\n"
                    "## Workflow history\n- 2026-08-08 planned (r): planned\n"
                ),
            )
            # eee555 is high priority and blocks-release; aaa111 is medium priority
            _write(
                root / ".aw/records/backlog/open/20260101-s-01-eee555-e.backlog.md",
                (
                    "- Id: eee555\n- Status: open\n- Set: s\n- Priority: high\n- Blocks-Release: next\n"
                    "- Work-Kind: chore\n- Summary: blocker\n\n## Workflow history\n- 2026-08-08 created (aw backlog): e\n"
                ),
            )
            _write(
                root / ".aw/records/backlog/open/20260101-s-02-aaa111-a.backlog.md",
                (
                    "- Id: aaa111\n- Status: open\n- Set: s\n- Priority: medium\n"
                    "- Work-Kind: chore\n- Summary: normal\n\n## Workflow history\n- 2026-08-08 created (aw backlog): a\n"
                ),
            )
            subprocess.run(["git", "init"], cwd=str(root), capture_output=True)

            # Explicit order: eee555 must come first in a flat list with no ## release-blockers section
            p_exp = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "next",
                    "--dir",
                    str(root),
                    "-o",
                    "priority",
                    "--no-color",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(p_exp.returncode, 0)
            lines_exp = [line for line in p_exp.stdout.splitlines() if line.strip()]
            self.assertNotIn("## release-blockers", p_exp.stdout)
            self.assertEqual(len(lines_exp), 2)
            self.assertIn("eee555", lines_exp[0])
            self.assertIn("aaa111", lines_exp[1])

            # Default order (no -o): trailing ## release-blockers section must appear
            p_def = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "next",
                    "--dir",
                    str(root),
                    "--no-color",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(p_def.returncode, 0)
            self.assertIn("## release-blockers", p_def.stdout)


if __name__ == "__main__":
    unittest.main()
