"""Tests for aw ipd scaffold + non-destructive sync (Set ipd-structure, Order 03).

Covers scaffold args/defaults/metadata + dry-run/apply/overwrite + atomic write; sync placeholder
recognition, monotonic watermark assignment, gap stability, no-reuse-after-deletion, matching V
skeletons, content preservation, and refusal after execution/approval. Stdlib unittest.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S
from tests.support import REPO_ROOT


def _ns(**kw) -> argparse.Namespace:
    base = dict(
        kind=None,
        title=None,
        path=None,
        set=None,
        order=None,
        author=None,
        apply=False,
        overwrite=False,
    )
    base.update(kw)
    return argparse.Namespace(**base)


def _run(fn, ns) -> tuple:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(ns)
    return rc, buf.getvalue()


class ScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_dry_run_writes_nothing(self):
        target = self.tmp / "a.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
            ),
        )
        self.assertEqual(rc, 0)
        self.assertFalse(target.exists())
        self.assertIn("would write", out)

    def test_apply_writes_conforming_child(self):
        target = self.tmp / "b.md"
        rc, _ = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 0)
        self.assertTrue(target.exists())
        res = L.lint_text(target.read_text(), checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_apply_writes_conforming_orchestrator(self):
        target = self.tmp / "orch.md"
        rc, _ = _run(
            A.run_scaffold,
            _ns(
                kind="orchestrator",
                title="o (Set x, Order 0)",
                path=str(target),
                set="x",
                order=0,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 0)
        res = L.lint_text(target.read_text(), checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_scaffold_emits_unique_valid_id(self):
        # plans-adopter Order 02: scaffold emits a valid, collision-checked `- Id:`.
        import re as _re

        def _scaffold(name):
            target = self.tmp / name
            _run(
                A.run_scaffold,
                _ns(
                    kind="child",
                    title="t (Set x, Order 1)",
                    path=str(target),
                    set="x",
                    order=1,
                    author="tester",
                    apply=True,
                ),
            )
            m = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", target.read_text())
            return m.group(1) if m else None

        id_a = _scaffold("ida.md")
        id_b = _scaffold("idb.md")
        self.assertIsNotNone(id_a)
        self.assertIsNotNone(id_b)
        self.assertNotEqual(id_a, id_b)

    def test_overwrite_refused_without_flag(self):
        target = self.tmp / "c.md"
        target.write_text("existing\n")
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 1)
        self.assertIn("refusing to overwrite", out)
        self.assertEqual(target.read_text(), "existing\n")

    def test_orchestrator_order_must_be_zero(self):
        target = self.tmp / "d.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(
                kind="orchestrator",
                title="t (Set x, Order 1)",
                path=str(target),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )
        self.assertEqual(rc, 2)

    def test_set_without_order_rejected(self):
        target = self.tmp / "e.md"
        rc, out = _run(
            A.run_scaffold,
            _ns(kind="child", title="t", path=str(target), set="x", author="tester"),
        )
        self.assertEqual(rc, 2)

    def test_author_required(self):
        target = self.tmp / "f.md"
        old = os.environ.pop("AW_IPD_AUTHOR", None)
        try:
            rc, out = _run(
                A.run_scaffold,
                _ns(
                    kind="child",
                    title="t (Set x, Order 1)",
                    path=str(target),
                    set="x",
                    order=1,
                ),
            )
            self.assertEqual(rc, 2)
        finally:
            if old is not None:
                os.environ["AW_IPD_AUTHOR"] = old


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "plan.md"
        _run(
            A.run_scaffold,
            _ns(
                kind="child",
                title="t (Set x, Order 1)",
                path=str(self.path),
                set="x",
                order=1,
                author="tester",
                apply=True,
            ),
        )

    def _add_unassigned(self, n=1):
        t = self.path.read_text()
        marker = "  - Execution state: pending\n"
        idx = t.index(marker) + len(marker)
        block = ""
        for _ in range(n):
            block += (
                "- [ ] {0} TODO action.\n  - Depends on: none\n"
                "  - Expected outcome: TODO.\n  - Execution state: pending\n".format(
                    A.UNASSIGNED_MARKER
                )
            )
        self.path.write_text(t[:idx] + block + t[idx:])

    def test_sync_assigns_from_watermark_and_advances(self):
        self._add_unassigned(2)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        t = self.path.read_text()
        # scaffold shipped E-01 (watermark 01); two new leaves -> E-02, E-03; watermark -> 03.
        self.assertIn("- [ ] E-02", t)
        self.assertIn("- [ ] E-03", t)
        self.assertIn("- Highest E allocated: 03", t)
        self.assertIn("- [ ] V-02 validates E-02", t)
        self.assertIn("- [ ] V-03 validates E-03", t)
        res = L.lint_text(t, checkpoint="author", directory="pending")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_sync_backfills_missing_id_and_leaves_present_id(self):
        # plans-adopter Order 02: sync backfills a missing `- Id:`, leaves an existing one.
        import re as _re

        t = self.path.read_text()
        m0 = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", t)
        self.assertIsNotNone(m0)  # scaffold already emitted one
        # Strip the Id to simulate a legacy plan lacking it.
        t_noid = _re.sub(r"(?m)^- Id: [0-9a-z]{6}\n", "", t)
        self.path.write_text(t_noid)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        t_after = self.path.read_text()
        m1 = _re.search(r"(?m)^- Id: ([0-9a-z]{6})$", t_after)
        self.assertIsNotNone(m1)  # backfilled
        # Running sync again does not add a second Id or change the existing one.
        existing = m1.group(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        ids = _re.findall(r"(?m)^- Id: ([0-9a-z]{6})$", self.path.read_text())
        self.assertEqual(ids, [existing])

    def test_dry_run_writes_nothing(self):
        self._add_unassigned(1)
        before = self.path.read_text()
        rc, out = _run(A.run_sync, _ns(path=str(self.path)))
        self.assertEqual(rc, 0)
        self.assertEqual(self.path.read_text(), before)
        self.assertIn("would assign", out)

    def test_no_reuse_after_deleting_highest(self):
        # Assign up to E-03 (watermark 03), then delete the highest E and its V, then add one.
        self._add_unassigned(2)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        t = self.path.read_text()
        # remove E-03 leaf + V-03 row (pre-approval deletion of the highest).
        t = re.sub(r"- \[ \] E-03 .*?\n(?:  - .*\n)+", "", t)
        t = re.sub(r"- \[ \] V-03 validates E-03\n(?:  - .*\n)+", "", t)
        self.path.write_text(t)
        self.assertIn(
            "- Highest E allocated: 03", self.path.read_text()
        )  # watermark not decreased
        # Add a new leaf and sync: it must get E-04 (above watermark), NOT reuse E-03.
        self._add_unassigned(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        t = self.path.read_text()
        self.assertIn("- [ ] E-04", t)
        self.assertNotIn("- [ ] E-03", t)
        self.assertIn("- Highest E allocated: 04", t)

    def test_refuses_after_execution_begun(self):
        # Add an unassigned leaf FIRST, then mark the scaffolded E-01 performed -> execution has
        # begun -> sync must refuse (do not consume the pending marker before adding the leaf).
        self._add_unassigned(1)
        t = (
            self.path.read_text()
            .replace("- [ ] E-01", "- [x] E-01")
            .replace(
                "  - Execution state: pending", "  - Execution state: performed", 1
            )
        )
        self.path.write_text(t)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertIn("execution has begun", out)

    def test_refuses_when_approved(self):
        t = (
            self.path.read_text()
            .replace("- Status: draft", "- Status: approved")
            .replace(
                "- Author: tester",
                "- Approval: approved by x 2026-08-03\n- Author: tester",
            )
        )
        self.path.write_text(t)
        self._add_unassigned(1)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertIn("Status is 'approved'", out)

    def test_preserves_existing_content(self):
        # Author real evidence text into V-01, then sync a new leaf; the evidence must survive.
        t = self.path.read_text().replace(
            "  - Required evidence: TODO falsifiable evidence.",
            "  - Required evidence: the artifact exists at PATH-X.",
            1,
        )
        self.path.write_text(t)
        self._add_unassigned(1)
        _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertIn("the artifact exists at PATH-X.", self.path.read_text())

    def test_missing_watermark_refused(self):
        t = self.path.read_text().replace("- Highest E allocated: 01\n", "")
        self.path.write_text(t)
        self._add_unassigned(1)
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 1)
        self.assertIn("Highest E allocated", out)

    def test_no_unassigned_is_noop(self):
        rc, out = _run(A.run_sync, _ns(path=str(self.path), apply=True))
        self.assertEqual(rc, 0)
        self.assertIn("nothing to sync", out)


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_write_leaves_no_temp(self):
        tmp = Path(tempfile.mkdtemp())
        target = tmp / "x.md"
        A._atomic_write(target, "hello\n")
        self.assertEqual(target.read_text(), "hello\n")
        leftovers = [p for p in tmp.iterdir() if p.name.startswith(".ipd-tmp-")]
        self.assertEqual(leftovers, [])


class NoDependencyTests(unittest.TestCase):
    def test_authoring_module_is_stdlib_only(self):
        src = (REPO_ROOT / "agent_workflows" / "ipd_authoring.py").read_text(
            encoding="utf-8"
        )
        for line in src.splitlines():
            m = re.match(r"^(?:from|import)\s+([a-zA-Z0-9_.]+)", line.strip())
            if not m:
                continue
            top = m.group(1).split(".")[0]
            self.assertIn(
                top,
                {
                    "__future__",
                    "argparse",
                    "os",
                    "re",
                    "tempfile",
                    "datetime",
                    "pathlib",
                    "typing",
                    "agent_workflows",
                },
                "unexpected import: " + line,
            )


if __name__ == "__main__":
    unittest.main()
