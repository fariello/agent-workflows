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
from concurrent.futures import ThreadPoolExecutor
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
        """Kept separate and NOT tabulated: this is the contract-regression pin, and it asserts four
        structurally different things about ONE fixture (a sequence recomputed independently of the
        implementation, a literal sequence, the READY subsequence, and that that subsequence is NOT
        id-sorted). A row of (key, expected sequence) cannot carry the last two.
        """
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
        """Kept separate: compares two CALLS to each other rather than either to an expected
        sequence, so it has no expected-value column to tabulate."""
        items = [
            _item("bbb222", ".agents/plans/pending/b.md"),
            _item("aaa111", ".agents/plans/pending/a.md"),
        ]
        self.assertEqual(
            [it.id for it in att.sort_items(items)],
            [it.id for it in att.sort_items(items, A.ORDER_CLASS)],
        )

    def test_default_order_is_deterministic_across_repeated_sorts(self):
        """Kept separate: asserts REPEATABILITY across five calls, not a specific sequence."""
        items = [
            _item("bbb222", ".agents/plans/pending/b.md"),
            _item("aaa111", ".agents/plans/pending/a.md"),
            _item("ccc333", ".agents/plans/pending/c.md"),
        ]
        first = [it.id for it in att.sort_items(items)]
        for _ in range(5):
            self.assertEqual([it.id for it in att.sort_items(items)], first)


class AliasEquivalenceTests(unittest.TestCase):
    """(b) All four names share one parser, so they agree under every flag.

    ONE table replaces five tests of identical shape: run the four names with the SAME argv, then
    assert every name's stdout (and exit code) equals `next`'s. The only thing that differed was the
    flag set.

    The table is better than the five because the four names are meant to be ONE command behind one
    parser, and the historical defect was exactly a flag reaching some names and not others (`aw todo
    --format json` and `aw todo --check` both died with 'unrecognized arguments' before E-01). That
    kind of regression is a flag-shaped hole, not a name-shaped one: it breaks several flag rows for
    the same name at once. Five tests report five red lines; this reports one failure naming every
    (flag set, name) pair that diverged, so the shape of the hole is visible.

    The exit code is compared alongside stdout for EVERY row, not just the `--check` row. The old
    file checked `returncode == 0` for the bare/json/details rows but compared exit codes only under
    `--check`; comparing both everywhere is strictly stronger and costs nothing, since a name that
    exits differently while printing the same text is still a divergence.
    """

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

    def _run_all(self, *argv):
        """Run the read-only alias probes concurrently against the same fixture."""
        with ThreadPoolExecutor(max_workers=len(self.NAMES)) as pool:
            futures = {name: pool.submit(self._run, name, *argv) for name in self.NAMES}
            return {name: futures[name].result() for name in self.NAMES}

    #: (argv, expected exit code or None for "only agreement matters", why this row exists)
    FLAG_SETS = (
        (
            ("--no-color",),
            0,
            "the bare view: the baseline all the other rows extend",
        ),
        (
            ("--format", "json"),
            0,
            "`aw todo --format json` FAILED with 'unrecognized arguments' before E-01, which is the "
            "defect this whole class exists for",
        ),
        (
            ("--check", "--no-color"),
            None,
            "`aw todo --check` FAILED the same way before E-01. Its exit code is NOT pinned to 0: "
            "`--check` is fail-closed and its code depends on the live tree, so the contract here is "
            "that all four names AGREE, whatever the code is",
        ),
        (
            ("--details", "--no-color"),
            0,
            "a display flag must reach every name too, not only the machine-readable ones",
        ),
        (
            ("--long", "--no-color"),
            0,
            "the second display flag, which was a separate parser argument from --details",
        ),
    ) + tuple(
        (
            ("-o", key, "--format", "json"),
            0,
            f"every `-o` key must be accepted by every name; {key!r} is one member of the closed "
            "ORDER_KEYS vocabulary, and a name missing the option fails all of them at once",
        )
        for key in A.ORDER_KEYS
    )

    def test_all_four_names_agree_under_every_flag_set(self):
        wrong = []
        for argv, expected_rc, why in self.FLAG_SETS:
            shown = " ".join(argv)
            outs = self._run_all(*argv)
            baseline = outs["next"]
            if expected_rc is not None and baseline.returncode != expected_rc:
                wrong.append(
                    f"  `aw next {shown}` exited {baseline.returncode}, expected {expected_rc}\n"
                    f"    stderr: {baseline.stderr.strip()[:400]}\n"
                    f"    this row exists because: {why}"
                )
            for name in self.NAMES:
                proc = outs[name]
                if (proc.returncode, proc.stdout) != (
                    baseline.returncode,
                    baseline.stdout,
                ):
                    wrong.append(
                        f"  `aw {name} {shown}` diverged from `aw next {shown}`\n"
                        f"    next: exit {baseline.returncode}, {len(baseline.stdout)} bytes of stdout\n"
                        f"    {name}: exit {proc.returncode}, {len(proc.stdout)} bytes of stdout\n"
                        f"    {name} stderr: {proc.stderr.strip()[:400]}\n"
                        f"    this row exists because: {why}"
                    )
        self.assertEqual(
            wrong,
            [],
            f"the four names disagreed on {len(wrong)} of {len(self.FLAG_SETS)} flag sets. All four "
            "are meant to be ONE command behind ONE parser, so the historical failure is a flag "
            "reaching some names and not others ('unrecognized arguments'), which breaks every row "
            "carrying that flag at once. FIX: if ONE name failed across many rows, it has its own "
            "parser again (check that the aliases are registered as choices sharing `next`'s "
            "subparser object, which DeclarationTests asserts structurally); if EVERY name failed on "
            "one row, that flag itself is broken for the whole command.\n"
            + "\n".join(wrong),
        )

    def test_todo_help_no_longer_advertises_the_deleted_action_ledger(self):
        """Kept separate: asserts HELP TEXT content for one name, and its assertions are substring
        presence/absence rather than cross-name agreement."""
        proc = self._run("todo", "--help")
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("action ledger", proc.stdout)
        self.assertNotIn("operational AW actions", proc.stdout)
        self.assertIn("--order-by", proc.stdout)

    def test_alias_tests_use_fixture_root_not_repo_root(self):
        """Assert AliasEquivalenceTests exercises an isolated fixture directory, not REPO_ROOT (E-03, E-05(d)).

        Kept separate: this is the PRECONDITION for the agreement table above rather than another row
        of it. If the fixture were REPO_ROOT, or held too few distinct classes and priorities, the
        four names could agree trivially on an empty or uniform view.
        """
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
        """Kept separate: asserts the vocabulary's TYPE, uniqueness, and first element, which are
        properties of the tuple as a whole rather than per-key rows."""
        self.assertIsInstance(A.ORDER_KEYS, tuple)
        self.assertEqual(A.ORDER_KEYS[0], A.ORDER_CLASS)
        self.assertEqual(len(A.ORDER_KEYS), len(set(A.ORDER_KEYS)))
        for key in ("priority", "date", "set", "order", "blocking", "depth"):
            self.assertIn(key, A.ORDER_KEYS)

    def test_cli_choices_are_generated_from_the_contract_tuple(self):
        """Kept separate: a single equality between two vocabularies, not a per-key table."""
        from agent_workflows.cli import _attention_order_keys

        self.assertEqual(tuple(_attention_order_keys()), tuple(A.ORDER_KEYS))

    def test_unknown_key_is_refused_by_argparse_with_the_valid_list(self):
        """Kept separate: spawns the CLI and asserts on STDERR and exit 2, materially different setup
        from an in-process sort."""
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
        """Kept separate: assertRaises."""
        with self.assertRaises(ValueError):
            att.sort_items([], "not-a-key")


class PerKeyOrderTests(unittest.TestCase):
    """(c) Each key produces its expected order on hand-known values.

    ONE table replaces seven tests of one shape: build a small item list whose field values are
    hand-known, call `att.sort_items(items, key)`, assert the resulting ID SEQUENCE. Nothing but the
    row differed, so the old file asserted the same three lines seven times.

    The table is better than the seven for the reason that governs ordering code generally.
    `A.ORDER_KEYS` is a CLOSED SET dispatched through one sort-key builder, so the realistic failure
    is not one key breaking alone: it is a change to that builder (a reversed direction, a lost
    tiebreak tail, a rank table renumbered) that moves SEVERAL keys at once. Seven tests report that
    as seven unrelated red lines; this table reports one failure listing every key whose sequence
    moved, with expected vs actual, and the pattern across those keys is what identifies which part
    of the builder is wrong.

    Two rows deliberately share one fixture with different keys (`id6`/`path`/`status`/`tree` over
    the same three items): that is how the old test was written, and keeping it lets a reader see
    that only `tree` reorders them, which is the whole point of having four separate keys.
    """

    #: A three-item fixture used by several rows, so the reader can see which keys reorder it.
    _FIELDS = (
        _item("ccc333", "p/c.md", tree="specs", native_status="reviewed"),
        _item("aaa111", "p/a.md", tree="plans", native_status="draft"),
        _item("bbb222", "p/b.md", tree="backlog", native_status="open"),
    )

    #: (order key, items, expected id sequence, why this row exists)
    CASES = (
        (
            "priority",
            (
                _item("low001", "p/low.md", priority="low"),
                _item("hig001", "p/high.md", priority="high"),
                _item("med001", "p/med.md", priority="medium"),
            ),
            ["hig001", "med001", "low001"],
            "priority is RANKED, not alphabetical: high before medium before low (alphabetical "
            "would give high, low, medium)",
        ),
        (
            "date",
            (
                _item("old001", "p/old.md", last_history_at="2026-01-01"),
                _item("new001", "p/new.md", last_history_at="2026-09-01"),
                _item("mid001", "p/mid.md", last_history_at="2026-05-01"),
            ),
            ["new001", "mid001", "old001"],
            "date is DESCENDING (newest first), which is the opposite of the natural string order",
        ),
        (
            "set",
            (
                _item(
                    "aaa111", ".agents/plans/pending/20260101-zeta-01-aaa111-a.ipd.md"
                ),
                _item(
                    "bbb222", ".agents/plans/pending/20260101-alpha-01-bbb222-b.ipd.md"
                ),
            ),
            ["bbb222", "aaa111"],
            "the set id is parsed out of the FILENAME grammar, not read from a field; alpha before "
            "zeta proves the parse happened",
        ),
        (
            "order",
            (
                _item("aaa111", ".agents/plans/pending/20260101-s-03-aaa111-a.ipd.md"),
                _item("bbb222", ".agents/plans/pending/20260101-s-01-bbb222-b.ipd.md"),
                _item("ccc333", ".agents/plans/pending/20260101-s-02-ccc333-c.ipd.md"),
            ),
            ["bbb222", "ccc333", "aaa111"],
            "the NN Order number is parsed out of the filename too, and 01/02/03 must sequence a Set "
            "the way a runner would execute it",
        ),
        (
            "blocking",
            (
                _item("free01", "p/free.md"),
                _item("gate01", "p/gate.md", blocks_release="next"),
            ),
            ["gate01", "free01"],
            "a release blocker must come FIRST; this row is also the reverse of the default id/path "
            "order, so it cannot pass by accident",
        ),
        (
            "id6",
            _FIELDS,
            ["aaa111", "bbb222", "ccc333"],
            "id6 sorts by the stable handle",
        ),
        (
            "path",
            _FIELDS,
            ["aaa111", "bbb222", "ccc333"],
            "path sorts by the full path; same result as id6 on this fixture BY CONSTRUCTION, which "
            "is what makes the `tree` row below meaningful",
        ),
        (
            "status",
            _FIELDS,
            ["aaa111", "bbb222", "ccc333"],
            "status sorts the NATIVE status string: draft < open < reviewed",
        ),
        (
            "tree",
            _FIELDS,
            ["bbb222", "aaa111", "ccc333"],
            "tree sorts by artifact tree (backlog < plans < specs), which REORDERS the same three "
            "items the previous rows left alone, proving the key is actually consulted",
        ),
        (
            "priority",
            (
                _item("bbb222", "p/b.md", priority="high"),
                _item("aaa111", "p/a.md", priority="high"),
            ),
            ["aaa111", "bbb222"],
            "TIE FALL-THROUGH: two items equal on the selected key must keep the default "
            "(class, path, id) relative order rather than input order",
        ),
    )

    def test_every_order_key_produces_its_expected_sequence(self):
        wrong = []
        for key, items, expected, why in self.CASES:
            got = [it.id for it in att.sort_items(list(items), key)]
            if got != expected:
                wrong.append(
                    f"  -o {key} over {[it.id for it in items]}\n"
                    f"    expected {expected}\n"
                    f"    got      {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"attention.sort_items produced the wrong sequence for {len(wrong)} of "
            f"{len(self.CASES)} key/fixture rows. Every key is dispatched through ONE sort-key "
            "builder, so several rows failing together usually means that builder changed (a "
            "reversed direction, a dropped default tail, a renumbered rank table) rather than "
            "several keys breaking independently. FIX: read the key builder in attention.sort_items "
            "and compare the FAILING keys' branches against the passing ones.\n"
            + "\n".join(wrong),
        )

    def test_every_key_is_a_total_deterministic_order(self):
        """Kept separate: asserts REPEATABILITY and membership across every key in the live
        vocabulary, not any one key's expected sequence, so it has no expected-value column."""
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
        """Kept separate from PerKeyOrderTests' table: its subject is the ABSENT value, and it
        additionally asserts the item was neither hidden nor defaulted to `medium`."""
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
        """Kept separate: already a loop over the LIVE key vocabulary asserting count/set preservation
        plus a last-position rule for a subset of keys, so there is no fixed row set to tabulate."""
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
        """Kept separate: the subject is a non-conforming FILENAME (the parse must degrade, not
        raise), which is a different failure mode from a missing field."""
        items = [
            _item("odd001", ".agents/plans/pending/not-a-grammar-name.md"),
            _item("ok0001", ".agents/plans/pending/20260101-s-01-ok0001-x.ipd.md"),
        ]
        for key in ("set", "order"):
            got = [it.id for it in att.sort_items(items, key)]
            self.assertEqual(got, ["ok0001", "odd001"])

    def test_item_count_is_identical_across_every_order(self):
        """Every ordering runs against a realistic, isolated record tree. Kept separate: it runs the
        whole COMMAND per key and asserts membership rather than sequence.

        The invariant is that ordering changes sequence only, never membership. A
        temporary tree keeps that contract deterministic and avoids rescanning this
        repository's growing records once for every ordering key.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            _write(
                root / ".aw/records/backlog/open/20260101-s-01-bak001-a.backlog.md",
                _backlog("bak001", priority="high"),
            )
            _write(
                root / ".aw/records/backlog/blocked/20260101-s-02-bak002-b.backlog.md",
                _backlog("bak002", status="blocked", priority="low"),
            )
            _write(
                root / ".aw/records/plans/pending/20260101-s-03-pln001-p.ipd.md",
                _plan("pln001"),
            )
            base = _run_json(dir=str(root))
            self.assertEqual(base["exit"], 0)
            n = len(base["payload"]["items"])
            ids = sorted(it["id"] for it in base["payload"]["items"])
            self.assertEqual(n, 3)
            for key in A.ORDER_KEYS:
                got = _run_json(dir=str(root), order_by=key)
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

    #: (case, items, expected default order, expected depth order, why this row exists)
    ORDERS = (
        (
            "a three-node chain (C needs B needs A)",
            (
                _item("aaa999", "p/z-a.md", item_dependencies=()),
                _item("bbb555", "p/y-b.md", item_dependencies=("exists:ipd:aaa999",)),
                _item("ccc111", "p/x-c.md", item_dependencies=("exists:ipd:bbb555",)),
            ),
            ["ccc111", "bbb555", "aaa999"],
            ["aaa999", "bbb555", "ccc111"],
            "paths and ids are chosen so the DEFAULT order is the exact REVERSE of the depth order, "
            "which is what makes the assertion falsifiable: only a real depth sort passes",
        ),
        (
            "a cross-type edge (a plan depending on a BACKLOG item)",
            (
                _item(
                    "plan01",
                    "p/a-plan.md",
                    tree="plans",
                    item_dependencies=("state:backlog:open:bklg01",),
                ),
                _item("bklg01", "p/z-backlog.md", tree="backlog", native_status="open"),
            ),
            ["plan01", "bklg01"],
            ["bklg01", "plan01"],
            "the cross-type case the backlog item asked for: depth must follow an edge that crosses "
            "artifact TYPES, not only plan-to-plan edges, and here too the default order is the "
            "reverse, so the row cannot pass by accident",
        ),
    )

    def test_depth_puts_prerequisites_first_and_reverses_the_default_order(self):
        """Both depth-ordering fixtures, with their DEFAULT-order preconditions as a column.

        These were two tests with the same four lines: assert the default order, then assert the depth
        order. The precondition stays a column rather than being dropped, because it is what makes
        each row falsifiable - if the default order stopped being the reverse, the depth assertion
        would pass against a sort that ignores depth entirely. The message distinguishes the two, so a
        precondition failure is not mistaken for a depth failure.
        """
        wrong = []
        for case, items, default_order, depth_order, why in self.ORDERS:
            got_default = [it.id for it in att.sort_items(list(items))]
            if got_default != default_order:
                wrong.append(
                    f"  {case}: FIXTURE PRECONDITION broken. The default order must be "
                    f"{default_order} (the reverse of the depth order), got {got_default}. While "
                    "this is false the depth assertion below is not falsifiable\n"
                    f"    this row exists because: {why}"
                )
            got_depth = [it.id for it in att.sort_items(list(items), "depth")]
            if got_depth != depth_order:
                wrong.append(
                    f"  {case}: -o depth\n    expected {depth_order}\n    got      {got_depth}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"`-o depth` sequenced {len(wrong)} of {len(self.ORDERS)} fixtures wrongly. Both rows run "
            "through one depth computation, so failing together usually means that computation "
            "changed rather than the cross-type edge specifically. FIX: check the depth NUMBERS first "
            "(the dependency_depths table below pins them); if the numbers are right, the defect is "
            "in how the depth key is applied. A PRECONDITION line means the DEFAULT order moved, "
            "which is DefaultOrderContractTests' subject rather than this test's.\n"
            + "\n".join(wrong),
        )

    #: (case, items, expected {id: depth}, why this row exists)
    DEPTHS = (
        (
            "a three-node chain",
            (
                _item("aaa999", "p/a.md", item_dependencies=()),
                _item("bbb555", "p/b.md", item_dependencies=("exists:ipd:aaa999",)),
                _item("ccc111", "p/c.md", item_dependencies=("exists:ipd:bbb555",)),
            ),
            {"aaa999": 0, "bbb555": 1, "ccc111": 2},
            "depth is the LONGEST chain to a root, and a root is 0; these are the numbers the "
            "ordering rows above consume, so a wrong depth here explains a wrong sequence there",
        ),
        (
            "an edge pointing outside the view",
            (
                _item("aaa111", "p/a.md", item_dependencies=("exists:ipd:zzzzzz",)),
                _item("bbb222", "p/b.md", item_dependencies=()),
            ),
            {"aaa111": 0, "bbb222": 0},
            "a dependency on an artifact NOT in the view contributes NO depth: the alternative "
            "(counting it as 1) would silently demote every item whose prerequisite is filtered out "
            "of the board, which is most of them",
        ),
    )

    def test_dependency_depths_are_the_longest_chain_with_roots_at_zero(self):
        """The DEPTH NUMBERS themselves, tabulated apart from the resulting order.

        These two rows were two tests calling `dependency_depths` and asserting individual dict
        entries. They belong in one table because they are the same function over the same shape of
        input, and because a depth defect is systemic: the propagation rule is shared, so an
        off-by-one or a mishandled external edge moves several entries at once. The failure message
        prints the WHOLE expected and actual maps, which the old per-entry asserts could not.
        """
        wrong = []
        for case, items, expected, why in self.DEPTHS:
            depths, cycles = att.dependency_depths(list(items))
            got = {id6: depths.get(id6) for id6 in expected}
            if got != expected:
                wrong.append(
                    f"  {case}\n    expected depths {expected}\n    got depths      {got}\n"
                    f"    this row exists because: {why}"
                )
            if cycles:
                wrong.append(
                    f"  {case}: this acyclic fixture must report NO cycles, got {cycles}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"attention.dependency_depths computed the wrong depths for {len(wrong)} of "
            f"{len(self.DEPTHS)} fixtures. One propagation rule produces every number, so both rows "
            "failing together usually means that rule changed (an off-by-one on roots, or counting "
            "edges that leave the view) rather than two independent bugs. FIX: these depths are what "
            "`-o depth` sorts on, so fix them before investigating any depth ORDERING failure "
            "above.\n" + "\n".join(wrong),
        )

    def test_scan_extracts_item_dependencies_onto_the_item(self):
        """Kept separate: exercises `att.scan` over on-disk fixtures and asserts the parsed FIELD
        (including the `none` vs absent distinction), not an order."""
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
        """Kept separate: the END-TO-END path (write files, scan, sort), which no in-memory row
        exercises."""
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
    """(f) A cyclic fixture terminates, reports, and does not raise.

    ONE table replaces three tests that each built a cyclic item list, called
    `sort_items_with_notices(items, "depth")`, and asserted that every item still came back. The
    table is better because the three differed only in cycle TOPOLOGY (2-node, 3-node, self-edge),
    and a depth implementation either handles cycles or it does not: a missing visited-set breaks
    every topology at once, and (worse) a regression here can HANG rather than fail, so the useful
    report is which topologies got through and which did not.

    The three rows do NOT all demand the same reporting, and that difference is a COLUMN rather than
    a separate test. The `notice` column is tri-state: `"named-members"` requires a cycle notice
    naming every participant, `"required"` requires a cycle notice at all, and `"not-asserted"`
    requires only that the call return every item. The self-edge is `"not-asserted"` because that is
    exactly what the old self-edge test claimed (a self-edge currently produces NO notice; `aw check`
    is what reports it), and pinning a notice there would assert behavior no prior test asserted.
    """

    #: (case, item_dependencies by id, notice requirement, why this row exists)
    CYCLES = (
        (
            "a two-node cycle",
            {"aaa111": ("exists:ipd:bbb222",), "bbb222": ("exists:ipd:aaa111",)},
            "named-members",
            "the minimal real cycle: it must be REPORTED with its members named, not silently "
            "absorbed, because a human has to know WHICH plans to break the edge between",
        ),
        (
            "a three-node cycle",
            {
                "aaa111": ("exists:ipd:bbb222",),
                "bbb222": ("exists:ipd:ccc333",),
                "ccc333": ("exists:ipd:aaa111",),
            },
            "required",
            "a longer cycle must terminate too: a naive depth walk that survives the 2-node case by "
            "accident (say, by only checking the immediate parent) recurses forever here",
        ),
        (
            "a self-edge",
            {"aaa111": ("exists:ipd:aaa111",)},
            "not-asserted",
            "the degenerate case, kept as a row because it is the one an `is my dep me?` guard misses "
            "while both real cycles above pass. It must not HANG or RAISE and must still return its "
            "item; reporting is deliberately not asserted, matching the old test, because a self-edge "
            "emits no order-notice today and `aw check` is what flags it",
        ),
    )

    def test_every_cycle_topology_terminates_and_is_reported(self):
        wrong = []
        for case, deps, notice_rule, why in self.CYCLES:
            items = [
                _item(id6, f"p/{id6}.md", item_dependencies=edges)
                for id6, edges in deps.items()
            ]
            try:
                ordered, notices = att.sort_items_with_notices(items, "depth")
            except Exception as exc:
                wrong.append(
                    f"  {case} RAISED {type(exc).__name__}: {exc}\n"
                    f"    this row exists because: {why}"
                )
                continue
            if len(ordered) != len(items):
                wrong.append(
                    f"  {case}: the view must still render every item, got "
                    f"{[it.id for it in ordered]} from {sorted(deps)}\n"
                    f"    this row exists because: {why}"
                )
            if notice_rule == "not-asserted":
                continue
            if not notices:
                wrong.append(
                    f"  {case}: a cycle must be REPORTED, not silently absorbed; got no notices\n"
                    f"    this row exists because: {why}"
                )
            elif "cycle" not in notices[0].lower():
                wrong.append(
                    f"  {case}: the first notice must say 'cycle', got {notices[0]!r}\n"
                    f"    this row exists because: {why}"
                )
            elif notice_rule == "named-members" and not any(
                all(id6 in n for id6 in deps) for n in notices
            ):
                wrong.append(
                    f"  {case}: a notice must name every cycle member {sorted(deps)}, got "
                    f"{notices}\n    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"attention's depth ordering mishandled {len(wrong)} of {len(self.CYCLES)} cycle "
            "topologies. One visited-set guard covers all of them, so several rows failing together "
            "means that guard is missing or was narrowed rather than several independent bugs. NOTE: "
            "a regression here can HANG instead of failing, so reaching this message at all means "
            "the walk terminated and only the REPORTING is wrong. FIX: read the cycle detection in "
            "`dependency_depths` and check it records participants before returning.\n"
            + "\n".join(wrong),
        )

    def test_cycle_notice_reaches_the_human_board(self):
        """Kept separate: an END-TO-END assertion through `att.run` on a scanned on-disk fixture,
        proving the notice survives into rendered output rather than only into the returned list."""
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

    def _valid_repo(self, root: Path) -> None:
        """A single clean plan: the tree `--check` must NOT reject."""
        _write(
            root / ".agents/plans/pending/20260101-s-01-aaa111-a.ipd.md",
            _plan("aaa111"),
        )

    #: (fixture builder, extra run args, must exit nonzero?, why this row exists)
    VIEWS = (
        (
            _duplicate_id_repo,
            {"check": True},
            True,
            "`--check` on an INVALID view must fail closed under every order key; this is the "
            "primary contract (g)",
        ),
        (
            _duplicate_id_repo,
            {"format": "json"},
            True,
            "the PLAIN view must fail closed too: a display option must not be able to launder an "
            "invalid view into exit 0",
        ),
        (
            _valid_repo,
            {"check": True},
            False,
            "THE POSITIVE ROW: `--check` on a VALID tree must exit 0 under every key. While this row "
            "is broken both negative rows above are VACUOUS, because a view that failed "
            "unconditionally would satisfy them for every key",
        ),
    )

    def test_every_view_and_order_key_combination_reaches_its_expected_exit(self):
        wrong = []
        rows = 0
        for build, run_kw, want_nonzero, why in self.VIEWS:
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                build(self, root)
                for key in A.ORDER_KEYS:
                    rows += 1
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        rc = att.run(_Args(dir=str(root), order_by=key, **run_kw))
                    bad = (rc == 0) if want_nonzero else (rc != 0)
                    if bad:
                        flags = " ".join(
                            f"{k}={v!r}" for k, v in sorted(run_kw.items())
                        )
                        wrong.append(
                            f"  {build.__name__} + {flags} -o {key}: expected exit "
                            f"{'nonzero' if want_nonzero else '0'}, got {rc}\n"
                            f"    this row exists because: {why}"
                        )
        self.assertEqual(
            wrong,
            [],
            f"attention.run reached the wrong exit code for {len(wrong)} of {rows} "
            "(view, order key) combinations. Ordering is applied AFTER validity is decided, so "
            "every key should reach the same exit code for a given view; a whole view's worth of "
            "rows failing together means the exit decision itself moved, while a single key failing "
            "across views means that key's branch raises or swallows the drift. FIX: check that the "
            "drift exit code is computed from the scan result and not from the rendered output. If "
            "only the VALID rows failed, `--check` has become unconditional and the invalid rows "
            "above prove nothing.\n" + "\n".join(wrong),
        )

    def test_the_constructed_fixture_really_is_invalid(self):
        """Kept separate: a fixture PRECONDITION asserting the drift rule by name and the scan-level
        exit code, not the command's exit. Without it the fail-closed rows could pass against a
        fixture that stopped being invalid."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._duplicate_id_repo(root)
            _items, drift = att.scan(root)
            self.assertTrue(drift, "fixture precondition: the fixture must be invalid")
            self.assertIn("attention.duplicate-id", {x.rule for x in drift})
            self.assertNotEqual(core.drift_exit_code(drift), 0)


class DeclarationTests(unittest.TestCase):
    """(h) Every leaf, including the renamed one, carries a declaration."""

    def test_no_undeclared_parser_leaves_for_the_renamed_command(self):
        """Kept separate: a different subject (the command-surface declaration sweep)."""
        from agent_workflows.cli import _build_parser
        from agent_workflows.command_surface import find_undeclared_leaves

        undeclared = find_undeclared_leaves(_build_parser())
        for leaf in ("next", "attention", "att", "todo"):
            self.assertNotIn(leaf, undeclared)

    def test_next_is_the_canonical_declaration_and_the_others_are_aliases(self):
        """Kept separate: asserts DECLARATION metadata (command_class, canonical_command), not
        behavior, so it cannot share a row shape with the alias-agreement table above."""
        from agent_workflows.command_surface import get_all_declarations

        by_name = {d.command: d for d in get_all_declarations()}
        self.assertEqual(by_name["next"].command_class, "read")
        for alias in ("attention", "att", "todo"):
            self.assertEqual(by_name[alias].command_class, "alias")
            self.assertEqual(by_name[alias].canonical_command, "next")

    def test_next_is_a_real_parser_leaf_and_the_aliases_share_its_parser(self):
        """Kept separate: asserts parser OBJECT IDENTITY (`assertIs`), which is the structural reason
        the alias-agreement table passes; behavior agreement and shared identity are distinct
        claims."""
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
        """Kept separate: greps the SOURCE for deleted constructs, not runtime behavior."""
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

    def test_no_order_key_adds_an_artifact_reading_pass(self):
        """Every key reads the tree exactly as many times as the DEFAULT order does.

        ONE table over `A.ORDER_KEYS` replaces three tests that all ran the same counted fixture: an
        absolute `scan == 1` check for `depth`, a relative `depth vs class` comparison, and a loop
        over every key. Merging them is right here because the counts are one measurement per key and
        the assertions are three views of it; the row set is the closed key vocabulary, and the
        realistic regression (an ordering path that resolves data by re-reading artifacts) shows up on
        whichever keys touch that path, so seeing WHICH keys gained a pass is the diagnosis.

        Both the ABSOLUTE and the RELATIVE assertion are preserved as separate columns. The relative
        one (against `-o class`) keeps the test meaningful as unrelated passes are added or removed
        elsewhere; the absolute one (`scan == 1`) is what catches the case where the baseline ITSELF
        regressed to two scans, which a purely relative comparison would rate as clean.
        """
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._fixture(root)
            baseline = self._counted_run(root, order_by=A.ORDER_CLASS)
            wrong = []
            if baseline["scan"] != 1:
                wrong.append(
                    f"  BASELINE: -o {A.ORDER_CLASS} called att.scan {baseline['scan']} times, "
                    "expected exactly 1. Every row below is measured against this baseline, so "
                    "while it is wrong a matching count proves nothing"
                )
            for key in A.ORDER_KEYS:
                got = self._counted_run(root, order_by=key)
                if got["scan"] != 1:
                    wrong.append(
                        f"  -o {key} called att.scan {got['scan']} times, expected exactly 1\n"
                        "    this row exists because: the view has ONE scan authority; a second "
                        "scan makes `aw next` able to disagree with `aw doctor`"
                    )
                if got["iter"] != baseline["iter"]:
                    wrong.append(
                        f"  -o {key} made {got['iter']} artifact-reading passes vs the default "
                        f"order's {baseline['iter']}\n"
                        "    this row exists because: ordering must sort data already in hand; "
                        "re-reading the tree produces correct-LOOKING output, so no assertion on "
                        "what the command PRINTS could detect it"
                    )
        self.assertEqual(
            wrong,
            [],
            f"{len(wrong)} of {len(A.ORDER_KEYS)} order keys changed how many times the tree is "
            "read. Every key sorts the SAME scan result, so several keys failing together usually "
            "means a shared resolution helper started re-reading artifacts rather than that each key "
            "regressed separately. FIX: the failing keys' value extractors must read fields off the "
            "Item objects, not off disk. If only the BASELINE line failed, the default path itself "
            "gained a scan and every relative comparison here is vacuous.\n"
            + "\n".join(wrong),
        )

    def test_depth_is_computed_from_the_scan_result_not_a_dependency_index(self):
        """`build_dependency_index` re-reads every artifact; the ordering must not call it.

        Kept separate: it counts a DIFFERENT function on a different seam (an in-process
        `sort_items` call, with no command run and no fixture on disk).
        """
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
        """Kept separate: asserts the PARSED argv value, not a sort result."""
        from agent_workflows.cli import _build_parser

        parser = _build_parser()
        args = parser.parse_args(["next", "-o", "priority,status,id6"])
        self.assertEqual(args.order_by, "priority,status,id6")

    def test_multi_key_with_invalid_token_is_refused_by_argparse(self):
        """Kept separate: spawns the CLI and asserts exit 2 plus stderr text."""
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
        """Kept separate: assertRaises, and it also asserts the message names the bad token."""
        with self.assertRaises(ValueError) as ctx:
            att.sort_items([], "priority,not-a-key")
        self.assertIn("not-a-key", str(ctx.exception))

    #: A four-item fixture spanning both values of two keys, so swapping precedence REORDERS it.
    _GRID = (
        _item("prio_hi_draft", "p/a.md", priority="high", native_status="draft"),
        _item("prio_hi_open", "p/b.md", priority="high", native_status="open"),
        _item("prio_lo_draft", "p/c.md", priority="low", native_status="draft"),
        _item("prio_lo_open", "p/d.md", priority="low", native_status="open"),
    )

    #: (order spec, items, expected id sequence, why this row exists)
    CASES = (
        (
            "priority,status",
            _GRID,
            ["prio_hi_draft", "prio_hi_open", "prio_lo_draft", "prio_lo_open"],
            "priority PRIMARY: both high items come before both low ones, and status only orders "
            "within each priority group",
        ),
        (
            "status,priority",
            _GRID,
            ["prio_hi_draft", "prio_lo_draft", "prio_hi_open", "prio_lo_open"],
            "the SAME two keys with the precedence SWAPPED must produce a DIFFERENT sequence over the "
            "same items; this row is what proves the order of the comma-separated tokens is honored "
            "rather than the keys being merged into one comparison",
        ),
        (
            "priority,status,id6",
            (
                _item("c01", "p/c.md", priority="high", native_status="open"),
                _item("a01", "p/a.md", priority="high", native_status="open"),
                _item("b01", "p/b.md", priority="high", native_status="draft"),
            ),
            ["b01", "a01", "c01"],
            "THREE keys deep, where the first is tied across every item and the third does the real "
            "work: it proves precedence keeps descending past the second token instead of falling "
            "back to the default tail",
        ),
    )

    def test_multi_key_precedence_is_honored_left_to_right(self):
        """The precedence table: two keys either way round, plus a three-deep spec.

        These were two tests holding three `assertEqual`s of identical shape. Tabulating them matters
        more than the line saving: the rows are only meaningful RELATIVE to each other (the
        `priority,status` and `status,priority` rows share one fixture and must disagree), and a
        precedence bug - tokens applied in the wrong order, or the tail swallowing later tokens -
        breaks several rows at once. The message names which spec produced which sequence, so the
        comparison a reader needs is in front of them.
        """
        wrong = []
        for spec, items, expected, why in self.CASES:
            got = [it.id for it in att.sort_items(list(items), spec)]
            if got != expected:
                wrong.append(
                    f"  -o {spec}\n    expected {expected}\n    got      {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"attention.sort_items applied multi-key precedence wrongly for {len(wrong)} of "
            f"{len(self.CASES)} specs. All three run through one comma-splitting key builder, so "
            "several rows failing together usually means precedence itself broke (tokens applied "
            "right-to-left, or only the first token honored) rather than one spec misbehaving. FIX: "
            "if the two two-key rows produced the SAME sequence as each other, the tokens are being "
            "merged instead of ranked; if only the three-key row failed, the chain stops after the "
            "second token.\n" + "\n".join(wrong),
        )


class NewAttributeOrderTests(unittest.TestCase):
    """Ordering by readiness, oqs, rqs, file, aliases (setid, type), run state, and timestamps.

    ONE table replaces six tests with the identical body shape (hand-known items -> `sort_items` ->
    assert the id sequence) covering the keys added after the original `-o` vocabulary. Merging them
    is worth more here than anywhere else in this file, because these keys are precisely the ones
    with NON-OBVIOUS directions and rank tables: `oqs`/`rqs` sort DESCENDING with absent AFTER zero,
    `readiness` and `runs` have hand-written rank orders, and `setid`/`type` are ALIASES of `set` and
    `tree`. All of that lives in one sort-key builder, so a renumbering or a lost `reverse` moves
    several of these keys at once, and the table reports them together rather than as six unrelated
    red lines.

    The alias rows are in the SAME table as the keys they alias on purpose: an alias that silently
    stopped forwarding would still produce SOME order, and the only way to see it is to compare the
    alias row against its canonical row in one place.
    """

    #: (order key, items, extra sort_items kwargs, expected id sequence, why this row exists)
    CASES = (
        (
            "readiness",
            (
                _item("no001", "p/no.md", readiness="no-go"),
                _item("go001", "p/go.md", readiness="go"),
                _item("pen001", "p/pen.md", readiness="go-pending-approval"),
            ),
            {},
            ["go001", "pen001", "no001"],
            "readiness is a hand-written RANK (go, then go-pending-approval, then no-go), and "
            "alphabetically 'go' < 'go-pending-approval' < 'no-go' coincides, so this row's value is "
            "pinning the rank at all rather than distinguishing it from string order",
        ),
        (
            "oqs",
            (
                _item("oq1", "p/oq1.md", oqs=1),
                _item("oq5", "p/oq5.md", oqs=5),
                _item("oq0", "p/oq0.md", oqs=0),
                _item("none", "p/none.md"),
            ),
            {},
            ["oq5", "oq1", "none", "oq0"],
            "open questions sort DESCENDING (most questions first), and the absent value sorts after "
            "every POSITIVE count but before an explicit ZERO: an item with no oqs field is not the "
            "same as one known to have none outstanding",
        ),
        (
            "rqs",
            (
                _item("rq2", "p/rq2.md", rqs=2),
                _item("rq9", "p/rq9.md", rqs=9),
                _item("rq0", "p/rq0.md", rqs=0),
            ),
            {},
            ["rq9", "rq2", "rq0"],
            "resolved questions sort DESCENDING by the same rule as oqs, which is what makes the two "
            "keys' shared implementation safe to change only in one place",
        ),
        (
            "file",
            (
                _item("z01", "deep/nested/z_file.md"),
                _item("a01", "other/a_file.md"),
                _item("m01", "root/m_file.md"),
            ),
            {},
            ["a01", "m01", "z01"],
            "`file` sorts by BASENAME, not by full path: the directories here (deep/, other/, root/) "
            "sort in the opposite order, so a path-based implementation fails this row",
        ),
        (
            "setid",
            (
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
            ),
            {},
            ["bbb222", "aaa111"],
            "`setid` is an ALIAS of `set`; the fixture's trees and set ids happen to agree, which is "
            "why the `type` row below uses the same items",
        ),
        (
            "type",
            (
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
            ),
            {},
            ["bbb222", "aaa111"],
            "`type` is an ALIAS of `tree` (backlog < specs); an alias that stopped forwarding would "
            "still emit some order, so it is pinned beside its canonical key",
        ),
        (
            "runs",
            (
                _item("fail01", "p/fail.md"),
                _item("run001", "p/run.md"),
                _item("none01", "p/none.md"),
                _item("done01", "p/done.md"),
                _item("que001", "p/que.md"),
                _item("merg01", "p/merg.md"),
                _item("blk001", "p/blk.md"),
            ),
            {
                "run_map": {
                    "run001": "running",
                    "merg01": "merging",
                    "que001": "queued",
                    "done01": "done",
                    "blk001": "blocked",
                    "fail01": "failed",
                }
            },
            ["run001", "merg01", "que001", "done01", "blk001", "fail01", "none01"],
            "the run-state RANK is fully hand-written (running, merging, queued, done, blocked, "
            "failed) and matches no alphabetical order at all, so this is the row a renumbering "
            "breaks first; an item with NO run state sorts last",
        ),
        (
            "run",
            (
                _item("fail01", "p/fail.md"),
                _item("run001", "p/run.md"),
                _item("none01", "p/none.md"),
                _item("done01", "p/done.md"),
                _item("que001", "p/que.md"),
                _item("merg01", "p/merg.md"),
                _item("blk001", "p/blk.md"),
            ),
            {
                "run_map": {
                    "run001": "running",
                    "merg01": "merging",
                    "que001": "queued",
                    "done01": "done",
                    "blk001": "blocked",
                    "fail01": "failed",
                }
            },
            ["run001", "merg01", "que001", "done01", "blk001", "fail01", "none01"],
            "`run` is an ALIAS of `runs` and must produce the IDENTICAL sequence, which is only "
            "checkable against the canonical row above",
        ),
        (
            "runs,priority",
            (
                _item("r_low", "p/r_low.md", priority="low"),
                _item("r_high", "p/r_high.md", priority="high"),
                _item("q_med", "p/q_med.md", priority="medium"),
                _item("q_high", "p/q_high.md", priority="high"),
            ),
            {
                "run_map": {
                    "r_low": "running",
                    "r_high": "running",
                    "q_med": "queued",
                    "q_high": "queued",
                }
            },
            ["r_high", "r_low", "q_high", "q_med"],
            "run state is PRIMARY and priority only breaks ties within it: `r_low` outranks `q_high` "
            "despite the lower priority, which is what proves the precedence rather than a merge of "
            "the two ranks",
        ),
    )

    def test_every_added_order_key_produces_its_expected_sequence(self):
        wrong = []
        for key, items, kwargs, expected, why in self.CASES:
            got = [it.id for it in att.sort_items(list(items), key, **kwargs)]
            if got != expected:
                wrong.append(
                    f"  -o {key}\n"
                    f"    expected {expected}\n"
                    f"    got      {got}\n"
                    f"    this row exists because: {why}"
                )
        self.assertEqual(
            wrong,
            [],
            f"attention.sort_items produced the wrong sequence for {len(wrong)} of "
            f"{len(self.CASES)} added keys. These keys carry the NON-OBVIOUS parts of the ordering "
            "(descending numeric keys, hand-written readiness and run-state ranks, and the "
            "setid/type/run aliases), all built in one place, so several rows failing together "
            "usually means a rank table was renumbered or a `reverse` was dropped rather than "
            "several keys breaking independently. FIX: if an ALIAS row failed while its canonical "
            "row passed, the alias stopped forwarding; if both failed, the shared key builder "
            "changed.\n" + "\n".join(wrong),
        )

    def test_ctime_and_mtime_newest_first_with_real_files(self):
        """Kept separate: needs materially different setup (real files on disk, stamped with
        `os.utime`, plus a `repo_root` to resolve them against) that no in-memory row can supply."""
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
        """Kept separate: asserts RENDERED LINE POSITIONS from `render_table` under two different
        `order_by` values, which is a structurally different assertion from a sorted id sequence."""
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
        """Kept separate: needs the distinct color=True setup that makes `render_board` delegate to
        `render_table`, and asserts on ANSI-stripped output."""
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
            # durablecapture-02 (`m867ox`): the `releases` tree is TRACKED and now actually SCANNED,
            # so the release record written above is itself a legitimate board row. Assert the
            # RELATIONSHIP the test exists to prove (the blocking backlog item sorts ahead of the
            # non-blocking one in one flat list) plus the release record's PRESENCE with its tree tag,
            # rather than a total line count, so the record vanishing again would fail this test.
            backlog_lines = [line for line in lines_exp if "[backlog]" in line]
            release_lines = [line for line in lines_exp if "[releases]" in line]
            self.assertEqual(len(backlog_lines), 2)
            self.assertIn("eee555", backlog_lines[0])
            self.assertIn("aaa111", backlog_lines[1])
            self.assertEqual(len(release_lines), 1)
            self.assertIn("rel001", release_lines[0])
            self.assertIn("(planned)", release_lines[0])
            self.assertEqual(len(lines_exp), len(backlog_lines) + len(release_lines))

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
