"""Outcome tests for `selectors.scan_once()`, the read-only scan scope.

Inside the scope `selectors.resolve` reuses one walk and one header read per record type instead
of re-reading every record per call (measured 2026-11-11: `aw partition` spent 530 of 539 s doing
that). These tests check what callers observe: the same answers as an unscoped resolve, file reads
counted through the real `open` builtin, and a fresh scan after the scope closes.
"""

from __future__ import annotations

import builtins
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import selectors


def _plan(pend: Path, order: int, id6: str, status: str = "to-review") -> Path:
    p = pend / f"20260101-demo-{order:02d}-{id6}-plan-{order}.ipd.md"
    p.write_text(
        f"# Plan {order}\n\n- Id: {id6}\n- Status: {status}\n- Set: demo\n\n## Goal\nx\n",
        encoding="utf-8",
    )
    return p


class ScanOnceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="aw_scan_once_")
        self.repo = Path(self.tmp.name).resolve()
        self.pend = self.repo / ".aw" / "records" / "plans" / "pending"
        self.pend.mkdir(parents=True)
        self.ids = [f"sc{i:04d}" for i in range(20)]
        self.paths = {i: _plan(self.pend, n + 1, i) for n, i in enumerate(self.ids)}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _resolve_all(self) -> dict:
        out = {}
        for i in self.ids:
            res = selectors.resolve(self.repo, "plans", i)
            out[i] = (res.kind, [str(p) for p in res.paths])
        return out

    def _count_record_opens(self, fn) -> int:
        real_open = builtins.open
        count = 0

        def counting_open(file, *a, **kw):
            nonlocal count
            if str(file).endswith(".ipd.md"):
                count += 1
            return real_open(file, *a, **kw)

        with mock.patch("builtins.open", counting_open), mock.patch(
            "pathlib.Path.open",
            lambda self, *a, **kw: counting_open(str(self), *a, **kw),
        ):
            fn()
        return count

    def test_scoped_answers_match_unscoped(self) -> None:
        unscoped = self._resolve_all()
        with selectors.scan_once():
            scoped = self._resolve_all()
        self.assertEqual(scoped, unscoped)
        for i in self.ids:
            self.assertEqual(scoped[i][0], selectors.MATCH_ID6)
            self.assertEqual(scoped[i][1], [str(self.paths[i])])

    def test_scope_reads_each_record_once(self) -> None:
        unscoped_reads = self._count_record_opens(self._resolve_all)

        def scoped():
            with selectors.scan_once():
                self._resolve_all()

        scoped_reads = self._count_record_opens(scoped)
        # Unscoped: every lookup reads every record (20 x 20). Scoped: one read per record.
        self.assertGreaterEqual(unscoped_reads, len(self.ids) * len(self.ids))
        self.assertLessEqual(scoped_reads, len(self.ids))

    def test_other_selector_kinds_still_resolve_in_scope(self) -> None:
        with selectors.scan_once():
            by_set = selectors.resolve(self.repo, "plans", "demo")
            by_status = selectors.resolve(self.repo, "plans", "to-review")
            missing = selectors.resolve(self.repo, "plans", "zz9999")
        self.assertEqual(by_set.kind, selectors.MATCH_SETID)
        self.assertEqual(len(by_set.paths), len(self.ids))
        self.assertEqual(by_status.kind, selectors.MATCH_STATUS)
        self.assertEqual(missing.paths, [])

    def test_new_record_visible_after_scope_closes(self) -> None:
        with selectors.scan_once():
            self.assertEqual(selectors.resolve(self.repo, "plans", "sc9999").paths, [])
            new = _plan(self.pend, 99, "sc9999")
        self.assertEqual(
            [str(p) for p in selectors.resolve(self.repo, "plans", "sc9999").paths],
            [str(new)],
        )

    def test_nested_scopes_share_and_close_once(self) -> None:
        with selectors.scan_once():
            with selectors.scan_once():
                selectors.resolve(self.repo, "plans", self.ids[0])
            # Inner exit must not close the outer scope: a record added now stays unseen.
            _plan(self.pend, 98, "sc9998")
            self.assertEqual(selectors.resolve(self.repo, "plans", "sc9998").paths, [])
        self.assertEqual(len(selectors.resolve(self.repo, "plans", "sc9998").paths), 1)


if __name__ == "__main__":
    unittest.main()
