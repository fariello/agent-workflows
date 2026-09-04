"""Tests for bklggrad Order 02 (orb9zb): the shared close-legitimacy predicate + setter gate +
`aw check` consistency rules + WARN transitions + the generalized evidence resolver.

Covers:
- V-02 evaluate_blocking_close: fail-closed on a bare blocking `-> done`; legitimate for HANDOFF,
  SATISFIED, DE-GATED; warn (not error) for blocking `-> parked` and priority-demote-of-blocker.
- V-03 the shared evidence resolver accepts a real in-tree artifact, rejects nonexistent/unsafe;
  specs `implementing -> implemented` behavior unchanged.
- V-04 `aw backlog set done` on a blocking item fails with the three-fix teaching error and
  succeeds via each of the three paths (HANDOFF plan, --evidence, same-call --blocks-release -).
- V-05 `aw check` fires blocking-item-closed-without-gate and from-backlog-gate-mismatch on
  fixtures and is clean otherwise.
- V-06 blocking `-> parked` and priority-demote-of-a-blocker succeed (exit 0) with a warning.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch
from pathlib import Path

from agent_workflows import backlog as B
from agent_workflows import check_engine as CE


def _args(**kw):
    ns = argparse.Namespace()
    for k, v in kw.items():
        setattr(ns, k, v)
    return ns


def _write_item(
    repo: Path,
    id6: str,
    *,
    status="open",
    priority="high",
    blocks_release: "str | None" = "next",
    setid="demo",
) -> Path:
    d = repo / ".aw" / "records" / "backlog" / status
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        f"- Set: {setid}",
        f"- Priority: {priority}",
        "- Kind: chore",
        "- Summary: x",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", "- 2026-01-01 created (t): x", ""]
    p = d / f"20260101-{setid}-01-{id6}-x.backlog.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def _write_plan(
    repo: Path,
    id6: str,
    *,
    from_backlog=None,
    blocks_release=None,
    status="approved",
    setid="demo",
    order="01",
) -> Path:
    d = repo / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# IPD: {id6}",
        "",
        "- Date: 2026-08-25",
        "- Kind: child",
        f"- Status: {status}",
        f"- Set: {setid}",
        f"- Order: {int(order)}",
        f"- Id: {id6}",
    ]
    if from_backlog:
        lines.append(f"- From-Backlog: {from_backlog}")
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += [
        "",
        "## Workflow history",
        "- 2026-08-25 draft (t): x.",
        "",
        "## Goal",
        "x",
    ]
    p = d / f"20260825-{setid}-{order}-{id6}-x.ipd.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


class PredicateTests(unittest.TestCase):
    """V-02: evaluate_blocking_close fail-closed + three legitimacy paths + two warns."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_bare_blocking_done_fails_closed(self):
        p = _write_item(self.root, "aaa111")
        v = CE.evaluate_blocking_close(self.root, p, "done")
        self.assertFalse(v.legitimate)
        self.assertEqual(v.severity, "error")
        self.assertEqual(len(v.fixes), 3)

    def test_handoff_path_legitimate(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        v = CE.evaluate_blocking_close(self.root, p, "done")
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "HANDOFF")

    def test_handoff_mismatched_release_not_legitimate(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="r9z9z9")
        v = CE.evaluate_blocking_close(self.root, p, "done")
        self.assertFalse(v.legitimate)  # gate release differs -> not a valid handoff

    def test_satisfied_path_legitimate(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        # a real in-tree records artifact
        art = self.root / ".aw" / "records" / "walkthroughs" / "w.md"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("done\n", encoding="utf-8")
        rel = ".aw/records/walkthroughs/w.md"
        v = CE.evaluate_blocking_close(self.root, p, "done", evidence=rel)
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "SATISFIED")

    def test_degated_path_legitimate(self):
        # post-mutation item text carries NO Blocks-Release -> DE-GATED
        p = _write_item(self.root, "aaa111", blocks_release="next")
        degated = p.read_text(encoding="utf-8").replace("- Blocks-Release: next\n", "")
        v = CE.evaluate_blocking_close(self.root, p, "done", item_text=degated)
        self.assertTrue(v.legitimate)
        self.assertEqual(v.path, "DE-GATED")

    def test_non_blocking_item_unchecked(self):
        p = _write_item(self.root, "aaa111", blocks_release=None)
        v = CE.evaluate_blocking_close(self.root, p, "done")
        self.assertTrue(v.legitimate)
        self.assertEqual(v.severity, "ok")

    def test_parked_blocker_warns(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        v = CE.evaluate_blocking_close(self.root, p, "parked")
        self.assertTrue(v.legitimate)
        self.assertEqual(v.severity, "warn")

    def test_priority_demote_of_blocker_warns(self):
        # post-mutation priority medium, prior high -> demote warn
        p = _write_item(self.root, "aaa111", blocks_release="next", priority="medium")
        v = CE.evaluate_blocking_close(
            self.root,
            p,
            "open",
            item_text=p.read_text(encoding="utf-8"),
            prior_priority="high",
        )
        self.assertTrue(v.legitimate)
        self.assertEqual(v.severity, "warn")


class EvidenceResolverTests(unittest.TestCase):
    """V-03: shared resolver accepts a real in-tree artifact, rejects nonexistent/unsafe."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_accepts_in_tree_artifact(self):
        art = self.root / ".aw" / "records" / "specs" / "s.md"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("x\n", encoding="utf-8")
        self.assertTrue(
            CE.resolve_evidence_artifact(self.root, ".aw/records/specs/s.md")
        )

    def test_rejects_nonexistent(self):
        self.assertFalse(
            CE.resolve_evidence_artifact(self.root, ".aw/records/specs/nope.md")
        )

    def test_rejects_traversal(self):
        self.assertFalse(CE.resolve_evidence_artifact(self.root, "../../etc/passwd"))

    def test_rejects_non_records_path(self):
        src = self.root / "agent_workflows" / "x.py"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text("x\n", encoding="utf-8")
        self.assertFalse(
            CE.resolve_evidence_artifact(self.root, "agent_workflows/x.py")
        )

    def test_specs_evidence_resolvable_unchanged(self):
        # specs' stricter predicate still requires an executed IPD; a non-executed records file fails.
        from agent_workflows import specs

        specdir = self.root / ".aw" / "records" / "specs"
        specdir.mkdir(parents=True, exist_ok=True)
        specfile = specdir / "sp.md"
        specfile.write_text("# Spec\n\n- Status: implementing\n", encoding="utf-8")
        # a records file that is NOT an executed IPD -> rejected by specs' stricter check
        other = self.root / ".aw" / "records" / "walkthroughs" / "w.md"
        other.parent.mkdir(parents=True, exist_ok=True)
        other.write_text("x\n", encoding="utf-8")
        self.assertFalse(
            specs._evidence_resolvable(specfile, ".aw/records/walkthroughs/w.md")
        )
        # an executed IPD -> accepted
        ex = self.root / ".aw" / "records" / "plans" / "executed" / "e.ipd.md"
        ex.parent.mkdir(parents=True, exist_ok=True)
        ex.write_text("x\n", encoding="utf-8")
        self.assertTrue(
            specs._evidence_resolvable(specfile, ".aw/records/plans/executed/e.ipd.md")
        )


class SetterGateTests(unittest.TestCase):
    """V-04: aw backlog set done fails with the teaching error and succeeds via the three paths."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _set(self, path, **kw):
        base = dict(
            dir=str(self.root),
            path=str(path),
            status="done",
            message="",
            apply=True,
            blocks_release=None,
            evidence=None,
            force=False,
        )
        base.update(kw)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_set(_args(**base))
        return rc, out.getvalue(), err.getvalue()

    def test_bare_blocking_close_refused_with_three_fixes(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        rc, _out, err = self._set(p)
        self.assertEqual(rc, 1)
        self.assertIn("refused", err)
        self.assertIn("From-Backlog", err)
        self.assertIn("--evidence", err)
        self.assertIn("--blocks-release -", err)
        # nothing written to done/
        self.assertFalse((self.root / ".aw/records/backlog/done" / p.name).exists())
        self.assertTrue(p.exists())

    def test_handoff_makes_close_succeed(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        rc, _out, _err = self._set(p)
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / ".aw/records/backlog/done" / p.name).exists())

    def test_evidence_makes_close_succeed(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        art = self.root / ".aw" / "records" / "walkthroughs" / "w.md"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text("x\n", encoding="utf-8")
        rc, _out, _err = self._set(p, evidence=".aw/records/walkthroughs/w.md")
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / ".aw/records/backlog/done" / p.name).exists())

    def test_same_call_degate_makes_close_succeed(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        rc, _out, _err = self._set(p, blocks_release="-")
        self.assertEqual(rc, 0)
        moved = self.root / ".aw/records/backlog/done" / p.name
        self.assertTrue(moved.exists())
        self.assertNotIn("Blocks-Release", moved.read_text(encoding="utf-8"))

    def test_non_blocking_close_unaffected(self):
        p = _write_item(self.root, "aaa111", blocks_release=None)
        rc, _out, _err = self._set(p)
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / ".aw/records/backlog/done" / p.name).exists())


def _git(root, *args):
    import subprocess

    return subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )


class ConsistencyCheckTests(unittest.TestCase):
    """V-05: aw check rules fire on fixtures and are clean otherwise."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _init_git(self):
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@e.com")
        _git(self.root, "config", "user.name", "T")
        _git(self.root, "config", "commit.gpgsign", "false")

    def test_blocking_item_closed_without_gate_flagged_when_staged(self):
        # COMMIT-SCOPED: the backstop only fires on a done+blocking item STAGED in this commit
        # (a hand-edit bypass), not on historical done items.
        self._init_git()
        p = _write_item(self.root, "aaa111", status="done", blocks_release="next")
        _git(self.root, "add", str(p.relative_to(self.root)))
        drift = CE.check_release_gate_consistency(self.root)
        self.assertTrue(
            any(d.rule == "check.blocking-item-closed-without-gate" for d in drift)
        )

    def test_historical_done_blocker_grandfathered_when_unstaged(self):
        # An UNSTAGED (already-committed/historical) done+blocking item is NOT flagged.
        self._init_git()
        p = _write_item(self.root, "aaa111", status="done", blocks_release="next")
        _git(self.root, "add", str(p.relative_to(self.root)))
        _git(self.root, "commit", "-q", "-m", "seed")
        drift = CE.check_release_gate_consistency(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.blocking-item-closed-without-gate"],
            [],
        )

    def test_done_with_handoff_is_clean_when_staged(self):
        self._init_git()
        p = _write_item(self.root, "aaa111", status="done", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        _git(self.root, "add", str(p.relative_to(self.root)))
        drift = CE.check_release_gate_consistency(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.blocking-item-closed-without-gate"],
            [],
        )

    def test_from_backlog_gate_mismatch_flagged(self):
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="r9z9z9")
        drift = CE.check_release_gate_consistency(self.root)
        self.assertTrue(
            any(d.rule == "check.from-backlog-gate-mismatch" for d in drift)
        )

    def test_matching_gate_is_clean(self):
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        drift = CE.check_release_gate_consistency(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.from-backlog-gate-mismatch"], []
        )


class WarnSurfaceTests(unittest.TestCase):
    """V-06: warn transitions succeed (exit 0) and orphaned-live-blocker is a non-blocking warning."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_parked_blocker_succeeds_with_warning(self):
        p = _write_item(self.root, "aaa111", blocks_release="next")
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = B.run_set(
                _args(
                    dir=str(self.root),
                    path=str(p),
                    status="parked",
                    message="",
                    apply=True,
                    blocks_release=None,
                    evidence=None,
                    force=False,
                )
            )
        self.assertEqual(rc, 0)  # allowed
        self.assertIn("warning", err.getvalue())
        self.assertTrue((self.root / ".aw/records/backlog/parked" / p.name).exists())

    def test_orphaned_live_blocker_is_warn_not_error(self):
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        # it is NOT an exit-blocking consistency error:
        errors = CE.check_release_gate_consistency(self.root)
        self.assertEqual(
            [d for d in errors if d.rule == "check.orphaned-live-blocker"], []
        )
        # it IS surfaced as a warning:
        warns = CE.release_gate_warnings(self.root)
        self.assertTrue(any(d.rule == "check.orphaned-live-blocker" for d in warns))

    def test_orphaned_live_blocker_carries_cut_and_paste_fix(self):
        # The warning must include a runnable Fix command naming the item's id6, so the
        # attention view can surface a cut-and-paste remedy rather than only prose.
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        warns = CE.release_gate_warnings(self.root)
        w = next(d for d in warns if d.rule == "check.orphaned-live-blocker")
        self.assertIn("Fix: aw backlog set done aaa111", w.detail)

    def test_multiple_blockers_build_one_plan_handoff_index(self):
        """The advisory warning path scans plans once, not once per open blocker."""
        _write_item(self.root, "aaa111", status="open", blocks_release="next")
        _write_item(self.root, "bbb222", status="open", blocks_release="release2")
        _write_item(self.root, "ccc333", status="open", blocks_release="next")
        _write_plan(self.root, "pl0001", from_backlog="aaa111", blocks_release="next")
        _write_plan(
            self.root, "pl0002", from_backlog="bbb222", blocks_release="different"
        )

        real_iter = CE._iter_plan_ipds
        calls = 0

        def counted_iter(repo_root):
            nonlocal calls
            calls += 1
            yield from real_iter(repo_root)

        with patch.object(CE, "_iter_plan_ipds", side_effect=counted_iter):
            warnings = CE.release_gate_warnings(self.root)

        self.assertEqual(calls, 1)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].rule, "check.orphaned-live-blocker")
        self.assertIn("done aaa111", warnings[0].detail)


if __name__ == "__main__":
    unittest.main()
