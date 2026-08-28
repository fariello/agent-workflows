"""Tests for ipddeps Order g69y23: the Item-Dependencies field, grammar/parser, write primitive,
`aw ipd dependencies set` setter, and scaffold emission.

Covers the child's V-items:

* V-01 - schema recognition (lint-clean, no IPD-M103) + `parse_item_dependencies` accept/reject matrix.
* V-02 - `set_item_dependencies_line` inserts IMMEDIATELY AFTER `- Scope-Paths:` (NOT after `- Status:`),
  overwrites in place, and clears; other metadata byte-identical.
* V-03 - `aw ipd dependencies set` writes canonical edges, persists on a same-status no-op transition,
  clears with `none`, and rejects a malformed token non-zero writing nothing.
* V-04 - `aw ipd scaffold` emits `- Item-Dependencies: unresolved` positioned after `- Scope-Paths:`.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli, ipd_schema, releases


# --------------------------------------------------------------------------------------
# V-01: schema recognition + parser accept/reject matrix
# --------------------------------------------------------------------------------------


class ItemDependenciesSchemaAndParserTests(unittest.TestCase):
    def test_field_recognized_but_not_required(self) -> None:
        self.assertIn(ipd_schema.META_ITEM_DEPENDENCIES, ipd_schema.META_RECOGNIZED)
        self.assertNotIn(ipd_schema.META_ITEM_DEPENDENCIES, ipd_schema.META_REQUIRED)

    def test_parser_accepts_every_valid_form(self) -> None:
        cases = {
            "none": ([], True),
            "unresolved": ([], False),
            "executed:aaaaaa": (["executed:aaaaaa"], True),
            "exists:spec:bbbbbb": (["exists:spec:bbbbbb"], True),
            "state:backlog:done:cccccc": (["state:backlog:done:cccccc"], True),
            "exists:ipd:dddddd": (["exists:ipd:dddddd"], True),
            "state:ipd:approved:eeeeee": (["state:ipd:approved:eeeeee"], True),
        }
        for value, (expected_canon, expected_ready) in cases.items():
            edges, ready, err = ipd_schema.parse_item_dependencies(value)
            self.assertIsNone(err, f"{value!r} should parse: {err}")
            self.assertEqual(ready, expected_ready, f"ready mismatch for {value!r}")
            self.assertEqual(
                [e.canonical() for e in edges], expected_canon, f"edges for {value!r}"
            )

    def test_parser_canonical_ordering_multi_edge(self) -> None:
        # Input out of canonical order; parser must sort executed < exists < state, then type.
        value = "state:backlog:done:cccccc, exists:spec:bbbbbb, executed:aaaaaa"
        edges, ready, err = ipd_schema.parse_item_dependencies(value)
        self.assertIsNone(err)
        self.assertTrue(ready)
        self.assertEqual(
            [e.canonical() for e in edges],
            ["executed:aaaaaa", "exists:spec:bbbbbb", "state:backlog:done:cccccc"],
        )
        canon, cerr = ipd_schema.canonical_item_dependencies(value)
        self.assertIsNone(cerr)
        self.assertEqual(
            canon,
            "executed:aaaaaa, exists:spec:bbbbbb, state:backlog:done:cccccc",
        )

    def test_parser_rejects_each_malformed_form(self) -> None:
        rejects = [
            "executed:aaaaaa, executed:aaaaaa",  # duplicate
            "none, executed:aaaaaa",  # none mixed
            "unresolved, executed:aaaaaa",  # unresolved mixed
            "exists:bogus:aaaaaa",  # bad target type
            "state:backlog:reviewed:cccccc",  # bad status for type
            "E-01",  # an intra-plan E-id
            "state:ipd:executed:aaaaaa",  # illegal; must use executed:
            "executed:BADID",  # not a 6-char id6
            "executed:toolongid",  # not a 6-char id6
        ]
        for value in rejects:
            edges, _ready, err = ipd_schema.parse_item_dependencies(value)
            self.assertIsNotNone(err, f"{value!r} should be rejected")
            self.assertEqual(edges, [], f"{value!r} rejected -> no edges")

    def test_state_ipd_executed_redirect_message(self) -> None:
        _e, _r, err = ipd_schema.parse_item_dependencies("state:ipd:executed:aaaaaa")
        self.assertIsNotNone(err)
        self.assertIn("executed:", err or "")


class ItemDependenciesLintCleanTests(unittest.TestCase):
    """V-01(a): an IPD carrying a valid Item-Dependencies lints CONFORMING (no IPD-M103)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        from tests.support import CONFORMING_ORCHESTRATOR

        self.plan = self.plans / "20260803-fixture-00-fix000-sample-fixture.ipd.md"
        base = CONFORMING_ORCHESTRATOR.read_text(encoding="utf-8")
        self.plan.write_text(
            releases.set_item_dependencies_line(
                base, "executed:aaaaaa, exists:spec:bbbbbb, state:backlog:done:cccccc"
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_lints_clean_with_item_dependencies(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["ipd", "lint", "--agent", str(self.plan)])
        out = buf.getvalue()
        self.assertEqual(rc, 0, f"plan with Item-Dependencies must lint clean: {out}")
        self.assertNotIn("IPD-M103", out)
        self.assertIn(
            "- Item-Dependencies: executed:aaaaaa",
            self.plan.read_text(encoding="utf-8"),
        )


# --------------------------------------------------------------------------------------
# V-02: write primitive anchors after Scope-Paths
# --------------------------------------------------------------------------------------


class ItemDependenciesWritePrimitiveTests(unittest.TestCase):
    def _block(self) -> str:
        return (
            "# IPD\n\n- Date: 2026-08-27\n- Kind: child\n"
            "- Scope-Paths: a.py, tests/\n- Status: draft\n- Set: x\n- Order: 1\n- Id: aaaaaa\n"
        )

    def test_insert_immediately_after_scope_paths(self) -> None:
        out = releases.set_item_dependencies_line(self._block(), "executed:bbbbbb")
        lines = out.splitlines()
        sp = next(i for i, ln in enumerate(lines) if ln.startswith("- Scope-Paths:"))
        self.assertEqual(
            lines[sp + 1],
            "- Item-Dependencies: executed:bbbbbb",
            "field must sit immediately after Scope-Paths (spec 2.7), NOT after Status",
        )
        # It must NOT be placed right after Status (the blind-clone bug).
        st = next(i for i, ln in enumerate(lines) if ln.startswith("- Status:"))
        self.assertNotEqual(lines[st + 1], "- Item-Dependencies: executed:bbbbbb")

    def test_overwrite_in_place_single_line(self) -> None:
        one = releases.set_item_dependencies_line(self._block(), "executed:bbbbbb")
        two = releases.set_item_dependencies_line(one, "exists:spec:cccccc")
        self.assertEqual(two.count("- Item-Dependencies:"), 1)
        self.assertIn("- Item-Dependencies: exists:spec:cccccc", two)

    def test_clear_removes_and_leaves_other_metadata_intact(self) -> None:
        block = self._block()
        one = releases.set_item_dependencies_line(block, "executed:bbbbbb")
        cleared = releases.set_item_dependencies_line(one, "-")
        self.assertNotIn("Item-Dependencies", cleared)
        # every original metadata line survives byte-identically
        for ln in block.splitlines():
            self.assertIn(ln, cleared.splitlines())
        # None also clears
        self.assertNotIn(
            "Item-Dependencies", releases.set_item_dependencies_line(one, None)
        )


# --------------------------------------------------------------------------------------
# V-03: aw ipd dependencies set end-to-end
# --------------------------------------------------------------------------------------


class IpdDependenciesSetE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        from tests.support import CONFORMING_ORCHESTRATOR

        self.plan = self.plans / "20260803-fixture-00-fix000-sample-fixture.ipd.md"
        self.plan.write_text(
            CONFORMING_ORCHESTRATOR.read_text(encoding="utf-8"), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _text(self) -> str:
        return self.plan.read_text(encoding="utf-8")

    def test_set_canonical_noop_persist_and_clear(self) -> None:
        # write edges out-of-order; expect canonical order persisted (this is a same-status no-op).
        rc = cli.main(
            [
                "ipd",
                "dependencies",
                "set",
                "fix000",
                "exists:spec:bbbbbb",
                "executed:aaaaaa",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn(
            "- Item-Dependencies: executed:aaaaaa, exists:spec:bbbbbb", self._text()
        )
        # plan still lints clean.
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc_lint = cli.main(["ipd", "lint", "--agent", str(self.plan)])
        self.assertEqual(rc_lint, 0, buf.getvalue())
        self.assertNotIn("IPD-M103", buf.getvalue())
        # clear with 'none'
        rc2 = cli.main(
            [
                "ipd",
                "dependencies",
                "set",
                "fix000",
                "none",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertIn("- Item-Dependencies: none", self._text())

    def test_malformed_token_rejected_nonzero_writes_nothing(self) -> None:
        before = self._text()
        rc = cli.main(
            [
                "ipd",
                "dependencies",
                "set",
                "fix000",
                "state:ipd:executed:aaaaaa",  # illegal
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertNotEqual(rc, 0, "malformed token must be rejected non-zero")
        self.assertEqual(before, self._text(), "nothing must be written on rejection")


# --------------------------------------------------------------------------------------
# V-04: scaffold emits unresolved after Scope-Paths
# --------------------------------------------------------------------------------------


class ScaffoldEmitsUnresolvedTests(unittest.TestCase):
    def test_scaffold_cli_emits_unresolved_after_scope_paths(self) -> None:
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(
                [
                    "ipd",
                    "scaffold",
                    "--kind",
                    "child",
                    "--title",
                    "Demo Plan",
                    "--set",
                    "demoset",
                    "--order",
                    "1",
                    "--author",
                    "test",
                ]
            )
        # Scaffold is dry-run by default: the body is printed to stdout.
        text = buf.getvalue()
        self.assertIn("- Item-Dependencies: unresolved", text)
        self.assertNotIn("- Item-Dependencies: none", text)
        # position: immediately after Scope-Paths
        lines = text.splitlines()
        sp = [i for i, ln in enumerate(lines) if ln.startswith("- Scope-Paths:")]
        if sp:
            self.assertEqual(
                lines[sp[0] + 1],
                "- Item-Dependencies: unresolved",
                "scaffold must place Item-Dependencies immediately after Scope-Paths",
            )
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
