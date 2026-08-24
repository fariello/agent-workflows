"""Tests for `aw ipd begin` fail-closed execution-start receipt (ipdgates Order 03, xjbvu2).

Stdlib unittest, git-backed throwaway repos (the receipt binds a real base HEAD and refuses a dirty
tree). Verifies: the happy path writes exactly one atomic receipt binding plan Id / content digest /
frozen requirement+scope digest / exact Scope-Paths / base HEAD / actor / timestamp; a resume re-reads
the same receipt deterministically; a plan-digest change invalidates a prior receipt; and every
fail-closed path (non-conforming lint = exit 1, dirty/ambiguous baseline / missing actor / unresolved
selector / interrupted write = no valid receipt) leaves NO execution authority.
"""

from __future__ import annotations

import argparse
import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import ipd_authoring as A
from agent_workflows import ipd_lifecycle as LC
from agent_workflows import ipd_lint as L
from agent_workflows import ipd_schema as S


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    # Mirror the real repo: the begin receipt lives in the gitignored .aw/state/ tree, so writing it
    # never dirties the worktree (a second begin on a clean base must still succeed).
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


def _ready_plan_text(
    *,
    plan_id: str = "abc123",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    """A conforming child IPD that lints CONFORMING at the pre-execution checkpoint."""
    txt = A.build_skeleton(
        kind="child",
        title="demo",
        author="tester",
        when="2026-08-24",
        set_name="demo",
        order=1,
        plan_id=plan_id,
    )
    out = []
    in_meta = True
    for ln in txt.splitlines():
        if ln.startswith("## "):
            in_meta = False
        if in_meta and ln.startswith("- Status:"):
            out.append("- Status: approved")
            continue
        if in_meta and ln.startswith("- Scope-Paths:"):
            out.append("- Scope-Paths: " + scope_paths)
            continue
        out.append(ln)
        if in_meta and ln.startswith("- Author:"):
            out.append("- Approval: 2026-08-24, human: approved")
    return "\n".join(out) + "\n"


def _completed_plan_text(
    *,
    plan_id: str = "abc123",
    scope_paths: str = "agent_workflows/demo.py, tests/test_demo.py",
) -> str:
    """A ready-plan whose single E-01/V-01 is marked performed/pass so it lints CONFORMING at
    the pre-transition checkpoint (finalize requires this)."""
    t = _ready_plan_text(plan_id=plan_id, scope_paths=scope_paths)
    t = t.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
        "  - Execution state: pending", "  - Execution state: performed", 1
    )
    t = (
        t.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
        .replace(
            "  - Observed evidence:\n", "  - Observed evidence: done, verified.\n", 1
        )
        .replace("  - Result: pending", "  - Result: pass", 1)
    )
    return t


def _write_plan(root: Path, text: str, name: str) -> Path:
    d = root / ".aw" / "records" / "plans" / "pending"
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


class BeginHappyPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        self.plan = _write_plan(
            self.root,
            _ready_plan_text(),
            "20260824-demo-01-abc123-demo.ipd.md",
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_pre_execution_gate_conforms_first(self):
        # Sanity: the fixture is genuinely ready-to-execute.
        res = L.lint_file(self.plan, checkpoint="pre-execution")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

    def test_happy_path_writes_bound_receipt(self):
        result = LC.begin(
            self.root, self.plan, "opencode/test", timestamp="2026-08-24T00:00:00Z"
        )
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
        rcpt_path = LC.receipt_path_for(self.root, "abc123")
        self.assertTrue(rcpt_path.is_file())
        r = result.receipt
        assert r is not None
        self.assertEqual(r["plan_id"], "abc123")
        self.assertEqual(
            r["plan_content_digest"], LC.plan_content_digest(self.plan.read_text())
        )
        self.assertTrue(r["requirement_digest"])
        self.assertEqual(
            r["scope_paths"], ["agent_workflows/demo.py", "tests/test_demo.py"]
        )
        self.assertEqual(r["actor"], "opencode/test")
        self.assertEqual(r["timestamp"], "2026-08-24T00:00:00Z")
        self.assertNotEqual(r["base_head"], "unversioned")
        self.assertEqual(r["pre_execution"]["disposition"], S.DISPOSITION_CONFORMING)

    def test_receipt_is_gitignored_and_untracked(self):
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        rel = ".aw/state/ipd-lifecycle/abc123.receipt.json"
        # git does not see it (either ignored by an installed .gitignore, or simply never added):
        proc = subprocess.run(
            ["git", "status", "--porcelain", rel],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        # An untracked file WOULD appear as '?? path' unless ignored; assert it is NOT staged/tracked.
        self.assertNotIn(" M ", proc.stdout)
        self.assertNotIn("A  ", proc.stdout)

    def test_resume_rereads_same_receipt_deterministically(self):
        r1 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t1").receipt
        r2 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t2").receipt
        assert r1 is not None and r2 is not None
        # The stable bindings (plan digest, requirement digest, base, scope) are identical on re-run.
        self.assertEqual(r1["plan_content_digest"], r2["plan_content_digest"])
        self.assertEqual(r1["requirement_digest"], r2["requirement_digest"])
        self.assertEqual(r1["base_head"], r2["base_head"])
        self.assertEqual(r1["scope_paths"], r2["scope_paths"])
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.assertEqual(stored["requirement_digest"], r2["requirement_digest"])
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))

    def test_plan_digest_change_invalidates_prior_receipt(self):
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))
        # A change to the plan's own content invalidates the receipt (OQ-01 rule (a)).
        changed = self.plan.read_text() + "\n<!-- a material edit -->\n"
        self.assertFalse(LC.receipt_is_current(stored, changed))

    def test_receipt_persists_after_unrelated_disjoint_commit(self):
        # OQ-01 lifetime: HEAD moving on DISJOINT paths does NOT invalidate the receipt.
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        (self.root / "unrelated.txt").write_text("hello", encoding="utf-8")
        _commit_all(self.root, "unrelated change on a disjoint path")
        # The plan content is unchanged, so the receipt remains current (digest-based validity).
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))


class BeginFailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        self.plan = _write_plan(
            self.root, _ready_plan_text(), "20260824-demo-01-abc123-demo.ipd.md"
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _no_receipt(self):
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").exists())

    def test_missing_actor_is_cannot_run_and_writes_nothing(self):
        result = LC.begin(self.root, self.plan, "", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self._no_receipt()

    def test_dirty_worktree_refused(self):
        (self.root / "dirty.txt").write_text("x", encoding="utf-8")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("DIRTY", result.message.upper())
        self._no_receipt()

    def test_non_conforming_lint_is_findings_and_writes_nothing(self):
        # Draft status is not ready-to-execute -> pre-execution gate fails (exit 1).
        bad = (
            self.plan.read_text()
            .replace("- Status: approved", "- Status: draft")
            .replace("- Approval: 2026-08-24, human: approved\n", "")
        )
        self.plan.write_text(bad, encoding="utf-8")
        _commit_all(self.root, "make plan draft")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(result.findings)
        self._no_receipt()

    def test_missing_id_is_cannot_run(self):
        noid = self.plan.read_text().replace("- Id: abc123\n", "")
        self.plan.write_text(noid, encoding="utf-8")
        _commit_all(self.root, "strip id")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)

    def test_interrupted_write_leaves_no_valid_receipt(self):
        # Simulate a crash during the atomic write: os.replace raises AFTER the temp file is written.
        with mock.patch.object(LC.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        # No partial/valid receipt at the destination, and no leftover temp file.
        self._no_receipt()
        rdir = LC.receipt_dir(self.root)
        leftovers = list(rdir.glob(".receipt-*.tmp")) if rdir.exists() else []
        self.assertEqual(
            leftovers, [], "atomic write must not leave a temp file behind"
        )


class BeginCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        self.plan = _write_plan(
            self.root, _ready_plan_text(), "20260824-demo-01-abc123-demo.ipd.md"
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _ns(self, **kw) -> argparse.Namespace:
        base = dict(
            plan="abc123",
            actor="opencode/test",
            dir=str(self.root),
            agent=False,
            json=False,
            no_color=True,
        )
        base.update(kw)
        return argparse.Namespace(**base)

    def test_cli_happy_path_exit_0_and_writes_receipt(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = LC.run_begin(self._ns())
        self.assertEqual(rc, LC.EXIT_OK, buf.getvalue())
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").is_file())

    def test_cli_unresolved_selector_exit_2(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = LC.run_begin(self._ns(plan="nosuchplan"))
        self.assertEqual(rc, LC.EXIT_CANNOT_RUN)

    def test_cli_non_conforming_exit_1(self):
        bad = (
            self.plan.read_text()
            .replace("- Status: approved", "- Status: draft")
            .replace("- Approval: 2026-08-24, human: approved\n", "")
        )
        self.plan.write_text(bad, encoding="utf-8")
        _commit_all(self.root, "draft")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = LC.run_begin(self._ns())
        self.assertEqual(rc, LC.EXIT_FINDINGS)

    def test_cli_mutates_no_tracked_file(self):
        LC.run_begin(self._ns())
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        # Only the gitignored receipt may exist; no tracked file is modified/staged.
        for line in proc.stdout.splitlines():
            self.assertNotIn(".aw/records/plans", line)
            self.assertFalse(line.startswith("M "), line)
            self.assertFalse(line.startswith("A "), line)


class FinalizeTests(unittest.TestCase):
    """ipdgates Order v7e88a: the atomic terminal transaction with scope comparison + evidence."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(
            self.root, _completed_plan_text(), "20260824-demo-01-abc123-demo.ipd.md"
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _begin(self):
        return LC.begin(self.root, self.plan, "opencode/test", timestamp="t")

    def _do_inscope_work_and_commit(self):
        (self.root / "agent_workflows" / "demo.py").write_text(
            "print('x')\n", encoding="utf-8"
        )
        (self.root / "tests" / "test_demo.py").write_text(
            "def test():\n    pass\n", encoding="utf-8"
        )
        _commit_all(self.root, "in-scope work")

    def test_positive_finalize_succeeds_with_attribution_and_evidence(self):
        self._begin()
        self._do_inscope_work_and_commit()
        result = LC.finalize(
            self.root, self.plan, "opencode/test", "did the work", apply=True
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertIsNotNone(result.commit)
        # Plan moved to executed/, pending copy gone.
        self.assertFalse(self.plan.exists())
        moved = self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
        self.assertTrue(moved.is_file())
        # Attributed history (non-generic actor) + terminal status.
        moved_text = moved.read_text()
        self.assertIn("opencode/test", moved_text)
        self.assertIn("- Status: executed", moved_text)
        self.assertNotIn("(aw set)", moved_text)
        # Three-phase gate evidence captured.
        self.assertIn("pre_execution", result.evidence)
        self.assertEqual(
            result.evidence["pre_transition"]["disposition"], S.DISPOSITION_CONFORMING
        )
        self.assertEqual(
            result.evidence["post_transition"]["disposition"], S.DISPOSITION_CONFORMING
        )
        # The lifecycle commit is path-scoped: only the plan move + the owned index.
        proc = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        touched = [ln for ln in proc.stdout.splitlines() if ln.strip()]
        for f in touched:
            self.assertTrue(
                f.startswith(".aw/records/plans/"),
                f"lifecycle commit touched a non-plan path: {f}",
            )

    def test_p7dqwz_counterexample_refuses_out_of_scope_path(self):
        # Scope-Paths allows ONLY agent_workflows/demo.py; changing tests/test_empty_state_ux.py
        # (the p7dqwz signature) must be refused, and the plan must stay pending/unchanged.
        plan = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="def456", scope_paths="agent_workflows/demo.py"
            ),
            "20260824-demo-02-def456-narrow.ipd.md",
        )
        _commit_all(self.root, "add narrow plan")
        LC.begin(self.root, plan, "opencode/test", timestamp="t")
        (self.root / "tests" / "test_empty_state_ux.py").write_text(
            "x\n", encoding="utf-8"
        )
        _commit_all(self.root, "out-of-scope edit (p7dqwz signature)")
        result = LC.finalize(self.root, plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any("tests/test_empty_state_ux.py" in f for f in result.findings),
            result.findings,
        )
        # Plan unmoved, still pending.
        self.assertTrue(plan.is_file())
        self.assertFalse(
            (self.root / ".aw" / "records" / "plans" / "executed" / plan.name).exists()
        )

    def test_positive_when_extra_path_is_in_scope(self):
        # The SAME extra path, but declared in Scope-Paths, finalizes successfully.
        plan = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="def456",
                scope_paths="agent_workflows/demo.py, tests/test_empty_state_ux.py",
            ),
            "20260824-demo-02-def456-wide.ipd.md",
        )
        _commit_all(self.root, "add wide plan")
        LC.begin(self.root, plan, "opencode/test", timestamp="t")
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        (self.root / "tests" / "test_empty_state_ux.py").write_text(
            "z\n", encoding="utf-8"
        )
        _commit_all(self.root, "in-scope work incl. the extra declared path")
        result = LC.finalize(self.root, plan, "opencode/test", "m", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )

    def test_evidence_absent_refuses(self):
        # No begin receipt -> finalize refuses (no execution authority).
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(any("receipt" in f.lower() for f in result.findings))
        self.assertTrue(self.plan.is_file())

    def test_stale_receipt_refuses(self):
        self._begin()
        # Edit the plan AFTER begin -> receipt digest no longer matches.
        self.plan.write_text(
            self.plan.read_text() + "\n<!-- edit -->\n", encoding="utf-8"
        )
        _commit_all(self.root, "edit plan after begin")
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any("stale" in f.lower() or "digest" in f.lower() for f in result.findings)
        )

    def test_pre_transition_nonconforming_refuses(self):
        # A begin receipt exists, but the plan's checklist is incomplete -> pre-transition fails.
        plan = _write_plan(
            self.root,
            _ready_plan_text(plan_id="def456"),  # E/V still pending
            "20260824-demo-02-def456-incomplete.ipd.md",
        )
        _commit_all(self.root, "add incomplete plan")
        LC.begin(self.root, plan, "opencode/test", timestamp="t")
        result = LC.finalize(self.root, plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(plan.is_file())

    def test_fail_loud_index_refresh_aborts_transaction(self):
        # If the owned plans-index refresh fails, finalize must FAIL (not swallow + report success).
        self._begin()
        self._do_inscope_work_and_commit()
        with mock.patch.object(
            LC, "_refresh_plans_index_fail_loud", side_effect=RuntimeError("index boom")
        ):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("index", result.message.lower())

    def test_missing_actor_or_message_cannot_run(self):
        self._begin()
        self._do_inscope_work_and_commit()
        self.assertEqual(
            LC.finalize(self.root, self.plan, "", "m", apply=True).exit_code,
            LC.EXIT_CANNOT_RUN,
        )
        self.assertEqual(
            LC.finalize(self.root, self.plan, "a", "", apply=True).exit_code,
            LC.EXIT_CANNOT_RUN,
        )

    def test_preview_without_apply_does_not_move(self):
        self._begin()
        self._do_inscope_work_and_commit()
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=False)
        self.assertEqual(result.exit_code, LC.EXIT_OK)
        self.assertIsNone(result.commit)
        self.assertTrue(self.plan.is_file())  # not moved in preview

    def test_intervening_in_scope_commits_are_computed_and_surfaced(self):
        # OQ-01 (b) COMPUTATION: this Order computes the in-Scope-Paths paths touched by a
        # commit since base and surfaces them in evidence (authorship-aware collision ENFORCEMENT
        # is Order 06). The normal single-actor flow (begin -> in-scope commit -> finalize) must
        # still SUCCEED - the in-scope commit is this execution's own sanctioned work, not a refusal.
        self._begin()
        self._do_inscope_work_and_commit()
        result = LC.finalize(
            self.root, self.plan, "opencode/test", "did the work", apply=True
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        audit = result.evidence["scope_audit"]
        # The in-scope commit paths are computed + surfaced (the substrate Order 06 builds on).
        self.assertIn("agent_workflows/demo.py", audit["intervening_in_scope_commits"])
        self.assertIn("tests/test_demo.py", audit["intervening_in_scope_commits"])
        # But they are NOT unexplained-path refusals (they are inside Scope-Paths).
        self.assertEqual(audit["unexplained_paths"], [])


if __name__ == "__main__":
    unittest.main()
