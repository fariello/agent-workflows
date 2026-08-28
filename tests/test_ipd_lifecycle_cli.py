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

from agent_workflows import cli
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
        if in_meta and ln.startswith("- Item-Dependencies:"):
            # ipddeps ovbnyq: an EXECUTION-READY fixture resolves its cross-IPD deps (the scaffold
            # emits `unresolved`, which is correctly blocked at pre-execution/pre-transition).
            out.append("- Item-Dependencies: none")
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

    def test_disjoint_dirty_paths_do_not_block_begin(self):
        # Path-overlap rule (ipdgates-03 OQ-01): uncommitted work OUTSIDE this plan's Scope-Paths
        # (here `dirty.txt` and an unrelated other-plan file) must NOT block begin, so a concurrent
        # multi-agent workflow is not thrashed.
        (self.root / "dirty.txt").write_text("x", encoding="utf-8")
        (self.root / "some_other_module.py").write_text("y = 1\n", encoding="utf-8")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_OK)
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").exists())

    def test_in_scope_dirty_path_refused_and_named(self):
        # An uncommitted change to a path INSIDE the frozen Scope-Paths (agent_workflows/demo.py)
        # makes the baseline ambiguous and must be refused, naming the offending path.
        demo = self.root / "agent_workflows" / "demo.py"
        demo.parent.mkdir(parents=True, exist_ok=True)
        demo.write_text("in_scope_change = True\n", encoding="utf-8")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("Scope-Paths", result.message)
        self.assertIn("agent_workflows/demo.py", result.message)
        self._no_receipt()

    def test_in_scope_dirty_under_declared_directory_refused(self):
        # A declared directory scope entry (tests/test_demo.py is a file, but the plan also implies
        # the tests area) - here we dirty the exact in-scope file and confirm refusal.
        f = self.root / "tests" / "test_demo.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("def test_x():\n    assert True\n", encoding="utf-8")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("tests/test_demo.py", result.message)
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
        # But they are NOT out-of-scope (they are inside Scope-Paths).
        self.assertEqual(audit["out_of_scope_paths"], [])


class ReconciliationTests(unittest.TestCase):
    """ipdgates Order qmt3yk: the finalize two-way scope reconciliation (surface + attribute)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _plan(self, scope_paths: str, plan_id: str = "abc123") -> Path:
        plan = _write_plan(
            self.root,
            _completed_plan_text(plan_id=plan_id, scope_paths=scope_paths),
            f"20260824-demo-01-{plan_id}-demo.ipd.md",
        )
        _commit_all(self.root, f"add plan {plan_id}")
        return plan

    def _begin(self, plan: Path):
        return LC.begin(self.root, plan, "opencode/test", timestamp="t")

    def _write(self, rel: str, content: str = "x\n"):
        (self.root / rel).write_text(content, encoding="utf-8")

    def test_out_of_scope_headless_missing_reason_fails_closed_naming_command(self):
        plan = self._plan("agent_workflows/demo.py")  # tests/extra.py is out of scope
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "work incl. out-of-scope")
        result = LC.finalize(self.root, plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        # Fail-closed: names the missing path and the exact --scope-reason re-invocation.
        self.assertIn("--scope-reason", result.message)
        self.assertTrue(any("tests/extra.py" in f for f in result.findings))
        self.assertTrue(plan.is_file())  # unmoved

    def test_out_of_scope_headless_with_reason_records_and_proceeds(self):
        plan = self._plan("agent_workflows/demo.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "work incl. out-of-scope")
        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "did the work",
            apply=True,
            scope_reasons={"tests/extra.py": "needed mid-stream"},
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        moved = self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        self.assertTrue(moved.is_file())
        # Reason recorded verbatim in the terminal history.
        self.assertIn("needed mid-stream", moved.read_text())
        self.assertIn("out-of-scope tests/extra.py", moved.read_text())

    def test_out_of_scope_empty_reason_does_not_finalize(self):
        plan = self._plan("agent_workflows/demo.py")
        self._begin(plan)
        self._write("tests/extra.py")
        _commit_all(self.root, "out of scope only")
        # An empty reason is treated as no reason -> refuse.
        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/extra.py": "   "},
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(plan.is_file())

    def test_in_scope_unmodified_headless_ack_records_and_proceeds(self):
        # demo.py touched; tests/declared.py declared but NOT touched -> needs an ack.
        plan = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        _commit_all(self.root, "touch only demo.py")
        # Missing ack -> fail closed.
        r_missing = LC.finalize(self.root, plan, "opencode/test", "m", apply=True)
        self.assertEqual(r_missing.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(any("tests/declared.py" in f for f in r_missing.findings))
        # Ack supplied -> proceeds and records.
        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "did it",
            apply=True,
            scope_acks={"tests/declared.py": "not-needed"},
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        moved = self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        self.assertIn(
            "in-scope-unmodified tests/declared.py: not-needed", moved.read_text()
        )

    def test_both_directions_at_once(self):
        # out-of-scope (tests/extra.py) AND in-scope-unmodified (tests/declared.py) in one finalize.
        plan = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "in-scope + out-of-scope, declared untouched")
        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/extra.py": "discovered mid-stream"},
            scope_acks={"tests/declared.py": "not-needed"},
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        moved_text = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        ).read_text()
        self.assertIn("out-of-scope tests/extra.py: discovered mid-stream", moved_text)
        self.assertIn("in-scope-unmodified tests/declared.py: not-needed", moved_text)

    def test_clean_delta_is_frictionless_no_reconciliation_note(self):
        plan = self._plan("agent_workflows/demo.py, tests/test_demo.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/test_demo.py")
        _commit_all(self.root, "clean in-scope work")
        result = LC.finalize(self.root, plan, "opencode/test", "clean", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        moved_text = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        ).read_text()
        self.assertNotIn("Scope reconciliation", moved_text)

    def test_tty_batched_prompt_collects_both_directions(self):
        # Simulate a TTY: ONE batched prompt returns reasons + acks for both directions.
        plan = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "both directions")
        calls = {"n": 0}

        def fake_prompt(out_of_scope, in_scope_unmodified):
            calls["n"] += 1
            # ONE call covering BOTH directions.
            self.assertIn("tests/extra.py", out_of_scope)
            self.assertIn("tests/declared.py", in_scope_unmodified)
            return {
                "reasons": {p: "prompted reason" for p in out_of_scope},
                "acks": {p: "prompted-ack" for p in in_scope_unmodified},
            }

        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "m",
            apply=True,
            interactive=True,
            prompt=fake_prompt,
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertEqual(calls["n"], 1, "reconciliation must use ONE batched prompt")
        moved_text = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        ).read_text()
        self.assertIn("prompted reason", moved_text)
        self.assertIn("prompted-ack", moved_text)

    def test_tty_empty_reason_from_prompt_does_not_finalize(self):
        plan = self._plan("agent_workflows/demo.py")
        self._begin(plan)
        self._write("tests/extra.py")
        _commit_all(self.root, "out of scope")

        def refusing_prompt(out_of_scope, in_scope_unmodified):
            return {"reasons": {p: "" for p in out_of_scope}, "acks": {}}

        result = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "m",
            apply=True,
            interactive=True,
            prompt=refusing_prompt,
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(plan.is_file())

    def test_cli_scope_flag_parsing(self):
        self.assertEqual(
            LC._parse_scope_reason_flags(
                ["a/b.py=why one", "c/d.py=why two", "bad-no-eq"]
            ),
            {"a/b.py": "why one", "c/d.py": "why two"},
        )
        self.assertEqual(
            LC._parse_scope_ack_flags(["tests/", "docs/=not-needed"]),
            {"tests/": "acknowledged", "docs/": "not-needed"},
        )


class RollbackFailureSemanticsTests(unittest.TestCase):
    """ipdgates Order 3xh53a: crash-safe two-phase failure semantics for aw ipd finalize."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(
            self.root,
            _completed_plan_text(
                scope_paths="agent_workflows/demo.py, tests/test_demo.py"
            ),
            "20260824-demo-01-abc123-demo.ipd.md",
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _begin_and_work(self):
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        _commit_all(self.root, "in-scope work")

    def _executed_path(self) -> Path:
        return self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    # --- E-01: journal + lock ---
    def test_journal_records_ownership_and_is_atomic_before_mutation(self):
        # A fault at the very first mutation checkpoint leaves the plan untouched; the journal
        # captured the ownership snapshot before mutating.
        self._begin_and_work()
        head_before = self._head()
        orig_bytes = self.plan.read_text()
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="before_mutation",
        )
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        # Rolled back: plan unchanged, no executed file, HEAD unchanged, journal cleared.
        self.assertTrue(self.plan.is_file())
        self.assertEqual(self.plan.read_text(), orig_bytes)
        self.assertFalse(self._executed_path().exists())
        self.assertEqual(self._head(), head_before)
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))

    def test_second_finalizer_is_locked_out_with_retry_diagnostic(self):
        self._begin_and_work()
        LC.acquire_finalize_lock(self.root, "abc123")
        # Simulate a DIFFERENT live owner by rewriting the lock's pid to this process's parent-ish
        # (use current pid but assert acquire from a fresh call raises when pid != os.getpid()).
        lock = LC.finalize_lock_path(self.root)
        import json as _json
        import os as _os

        data = _json.loads(lock.read_text())
        data["pid"] = (
            _os.getpid()
        )  # our pid; to force the "live other" path, temporarily fake it
        # Force a foreign live pid: pid 1 (init) is always alive and != our pid.
        data["pid"] = 1
        lock.write_text(_json.dumps(data), encoding="utf-8")
        with self.assertRaises(LC.TransactionLockError):
            LC.acquire_finalize_lock(self.root, "abc123")
        # Cleanup so tearDown is clean.
        lock.unlink()

    def test_stale_lock_is_reclaimed_via_dead_pid(self):
        # A lock whose recorded PID is dead is reclaimable (consults the record, not blind delete).
        lock = LC.finalize_lock_path(self.root)
        lock.parent.mkdir(parents=True, exist_ok=True)
        import json as _json

        # PID 2**31-1 is not a running process.
        lock.write_text(
            _json.dumps({"plan_id": "abc123", "pid": 2**31 - 1}), encoding="utf-8"
        )
        LC.acquire_finalize_lock(
            self.root, "abc123"
        )  # must NOT raise (stale -> reclaim)
        import os as _os

        self.assertEqual(_json.loads(lock.read_text())["pid"], _os.getpid())
        LC.release_finalize_lock(self.root)

    # --- E-02: pre-commit rollback + crash/restart ---
    def test_fault_after_move_rolls_back_plan_and_index(self):
        self._begin_and_work()
        head_before = self._head()
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_move",
        )
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertTrue(self.plan.is_file())  # restored to pending
        self.assertFalse(self._executed_path().exists())
        self.assertEqual(self._head(), head_before)

    def test_fault_after_index_rolls_back(self):
        self._begin_and_work()
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_index",
        )
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertTrue(self.plan.is_file())
        self.assertFalse(self._executed_path().exists())

    def test_crash_restart_before_commit_recovers_on_reinvocation(self):
        # A pre-commit fault leaves a rolled-back state; a fresh finalize then succeeds cleanly.
        # The ORIGINAL begin receipt (plan digest unchanged) is still current after the rollback, so
        # recovery is a plain re-finalize that resumes against the frozen base - NOT a re-begin. (A
        # re-begin here would recapture a base AT the in-scope work commit, which is only relevant to
        # scope reconciliation, not this pre-commit-rollback recovery path. The prior version of this
        # test re-begin'd and passed only because the whole-tree dirty check refused that re-begin and
        # thereby preserved the original receipt; the begin baseline check is now Scope-Paths-scoped
        # -- ipdgates-03 OQ-01 path-overlap rule -- so the recovery no longer depends on that refusal.)
        self._begin_and_work()
        LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_move",
        )
        # The original receipt is still valid (plan digest unchanged); re-finalize resumes and succeeds.
        result = LC.finalize(
            self.root, self.plan, "opencode/test", "recovered", apply=True
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(self._executed_path().is_file())

    def test_rollback_preserves_disjoint_dirty_and_staged_work(self):
        self._begin_and_work()
        # Create disjoint dirty + staged work that rollback must NOT touch.
        (self.root / "unrelated_dirty.txt").write_text("dirty\n", encoding="utf-8")
        (self.root / "unrelated_staged.txt").write_text("staged\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "unrelated_staged.txt"], cwd=self.root, check=True
        )
        LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_move",
        )
        # Disjoint work survived untouched.
        self.assertEqual((self.root / "unrelated_dirty.txt").read_text(), "dirty\n")
        self.assertEqual((self.root / "unrelated_staged.txt").read_text(), "staged\n")
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("unrelated_staged.txt", staged)

    def test_rollback_failure_retains_journal_and_reports_not_restored(self):
        self._begin_and_work()
        with mock.patch.object(
            LC,
            "_rollback_precommit",
            return_value=(False, "simulated rollback failure"),
        ):
            result = LC.finalize(
                self.root,
                self.plan,
                "opencode/test",
                "m",
                apply=True,
                fault_injection="after_move",
            )
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("NOT reported", result.message)
        # Journal retained in unknown-outcome.
        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_UNKNOWN_OUTCOME)

    # --- E-03: commit boundary + post-commit resume ---
    def test_committed_incomplete_then_same_command_resume(self):
        self._begin_and_work()
        # Force post-transition to fail so the lifecycle commit exists but is committed-incomplete.
        real_lint = L.lint_file

        def failing_post(path, *, checkpoint="author", legacy=False):
            r = real_lint(path, checkpoint=checkpoint, legacy=legacy)
            if checkpoint == "post-transition":
                from agent_workflows.ipd_lint import Diagnostic, LintResult

                return LintResult(
                    S.DISPOSITION_ERROR, [Diagnostic(0, 0, "IPD-TEST", "sim")], []
                )
            return r

        with mock.patch.object(L, "lint_file", failing_post):
            r1 = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(r1.exit_code, LC.EXIT_FINDINGS)
        self.assertIsNotNone(r1.commit)  # the lifecycle commit DID happen
        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_COMMITTED_INCOMPLETE)
        self.assertTrue(
            LC.receipt_path_for(self.root, "abc123").exists()
        )  # receipt NOT consumed
        head_after_commit = self._head()

        # Same-command resume (plan now in executed/): reruns ONLY post-transition, no 2nd commit.
        moved = self._executed_path()
        r2 = LC.finalize(self.root, moved, "opencode/test", "m", apply=True)
        self.assertEqual(r2.exit_code, LC.EXIT_OK, f"{r2.message} / {r2.findings}")
        self.assertEqual(
            self._head(), head_after_commit, "resume must not create a second commit"
        )
        self.assertIsNone(
            LC.read_finalize_journal(self.root, "abc123")
        )  # journal completed
        self.assertFalse(
            LC.receipt_path_for(self.root, "abc123").exists()
        )  # receipt consumed

    def test_persistent_post_transition_failure_stays_incomplete(self):
        self._begin_and_work()
        real_lint = L.lint_file

        def failing_post(path, *, checkpoint="author", legacy=False):
            r = real_lint(path, checkpoint=checkpoint, legacy=legacy)
            if checkpoint == "post-transition":
                from agent_workflows.ipd_lint import Diagnostic, LintResult

                return LintResult(
                    S.DISPOSITION_ERROR, [Diagnostic(0, 0, "IPD-TEST", "sim")], []
                )
            return r

        with mock.patch.object(L, "lint_file", failing_post):
            LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
            # A resume that STILL fails post-transition stays committed-incomplete (no success).
            moved = self._executed_path()
            r2 = LC.finalize(self.root, moved, "opencode/test", "m", apply=True)
        self.assertEqual(r2.exit_code, LC.EXIT_FINDINGS)
        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_COMMITTED_INCOMPLETE)

    def test_corrupt_journal_at_partial_state_is_unknown_outcome(self):
        self._begin_and_work()
        # Plant an unknown-outcome journal; a re-invocation must fail closed (never infer success).
        jpath = LC.finalize_journal_path(self.root, "abc123")
        jpath.parent.mkdir(parents=True, exist_ok=True)
        import json as _json

        jpath.write_text(
            _json.dumps({"plan_id": "abc123", "phase": LC.PHASE_UNKNOWN_OUTCOME}),
            encoding="utf-8",
        )
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("unknown-outcome", result.message)

    def test_clean_finalize_completes_and_consumes_receipt(self):
        # Baseline: the fully clean transaction completes, clears the journal, consumes the receipt.
        self._begin_and_work()
        result = LC.finalize(self.root, self.plan, "opencode/test", "clean", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(self._executed_path().is_file())
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").exists())
        # No finalize lock left behind.
        self.assertFalse(LC.finalize_lock_path(self.root).exists())


class DelegationAndBypassRemovalTests(unittest.TestCase):
    """ipdgates Order wezhxg: `aw set executed <plan>` delegates into aw ipd finalize (no raw bypass)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(
            self.root,
            _completed_plan_text(
                scope_paths="agent_workflows/demo.py, tests/test_demo.py"
            ),
            "20260824-demo-01-abc123-demo.ipd.md",
        )
        _commit_all(self.root, "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_cli(self, argv):
        import io
        from contextlib import redirect_stdout, redirect_stderr

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _begin_and_work(self):
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        _commit_all(self.root, "in-scope work")

    def _executed_path(self) -> Path:
        return self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name

    def test_set_executed_plan_without_actor_fails_closed_naming_command(self):
        # No raw ungated move: aw set executed <plan> without --actor fails closed (exit 2).
        self._begin_and_work()
        rc, out = self._run_cli(["set", "executed", "abc123", "--yes"])
        self.assertEqual(rc, 2)
        self.assertIn("--actor", out)
        self.assertTrue(self.plan.is_file())  # not moved
        self.assertFalse(self._executed_path().exists())

    def test_set_executed_plan_with_actor_delegates_into_finalize(self):
        self._begin_and_work()
        rc, out = self._run_cli(
            [
                "set",
                "executed",
                "abc123",
                "--actor",
                "opencode/test",
                "--message",
                "did it",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertTrue(self._executed_path().is_file())
        moved = self._executed_path().read_text()
        self.assertIn("- Status: executed", moved)
        self.assertIn("opencode/test", moved)
        self.assertNotIn("executed (aw set)", moved)

    def test_ipd_set_executed_also_delegates(self):
        self._begin_and_work()
        rc, out = self._run_cli(
            [
                "ipd",
                "set",
                "executed",
                "abc123",
                "--actor",
                "opencode/test",
                "--message",
                "did it",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertTrue(self._executed_path().is_file())

    def test_done_alias_delegates(self):
        self._begin_and_work()
        rc, out = self._run_cli(
            [
                "set",
                "done",
                "abc123",
                "--actor",
                "opencode/test",
                "--message",
                "did it",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, out)
        self.assertTrue(self._executed_path().is_file())

    def test_prompt_executed_transition_not_diverted(self):
        # A PROMPT terminal `executed` transition keeps the raw path (proves record_type key).
        pdir = self.root / ".aw" / "records" / "prompts" / "pending"
        pdir.mkdir(parents=True)
        prompt = pdir / "20260824-demoprompt-01-pr0mp7-x.prompt.md"
        prompt.write_text(
            "# Prompt\n\n- Status: draft\n- Id: pr0mp7\n\nbody\n", encoding="utf-8"
        )
        _commit_all(self.root, "add prompt")
        rc, out = self._run_cli(["set", "executed", "pr0mp7", "--yes"])
        self.assertEqual(rc, 0, out)
        self.assertTrue(
            (
                self.root / ".aw" / "records" / "prompts" / "executed" / prompt.name
            ).is_file()
        )

    def test_plan_retirement_superseded_not_diverted(self):
        # Plan RETIREMENT (superseded) keeps the raw RETIRED + git-mv path (not finalize).
        retire = _write_plan(
            self.root,
            _completed_plan_text(plan_id="ret123", scope_paths="grandfathered"),
            "20260824-demo-02-ret123-retire.ipd.md",
        )
        _commit_all(self.root, "add retire plan")
        rc, out = self._run_cli(["set", "superseded", "ret123", "--yes"])
        self.assertEqual(rc, 0, out)
        self.assertTrue(
            (
                self.root / ".aw" / "records" / "plans" / "superseded" / retire.name
            ).is_file()
        )

    def test_nonterminal_plan_transition_not_diverted(self):
        # A nonterminal plan transition (to approved) keeps the raw path.
        draft = _write_plan(
            self.root,
            _completed_plan_text(plan_id="drf123", scope_paths="grandfathered")
            .replace("- Status: approved", "- Status: to-review")
            .replace("- Approval: 2026-08-24, human: approved\n", ""),
            "20260824-demo-03-drf123-draft.ipd.md",
        )
        _commit_all(self.root, "add draft plan")
        rc, out = self._run_cli(["set", "approved", "drf123", "--by-human", "--yes"])
        self.assertEqual(rc, 0, out)
        self.assertIn("- Status: approved", draft.read_text())

    def test_missing_receipt_delegation_refuses_no_fabrication(self):
        # Recovery path: delegating with NO begin receipt refuses (finalize's fail-closed), and does
        # NOT fabricate a back-dated begin or an ungated move.
        rc, out = self._run_cli(
            [
                "set",
                "executed",
                "abc123",
                "--actor",
                "opencode/test",
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertEqual(rc, 1)  # finalize findings (no receipt)
        self.assertTrue(self.plan.is_file())
        self.assertFalse(self._executed_path().exists())


if __name__ == "__main__":
    unittest.main()
