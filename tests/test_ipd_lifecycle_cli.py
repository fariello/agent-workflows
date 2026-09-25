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
from tests import support


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
    """A conforming child IPD that lints CONFORMING at the pre-execution checkpoint.

    DELEGATES to the ONE shared fixture builder (`tests/support.ready_plan_text`). This file used to
    carry its own copy, and twenty-one such copies is why `planprio` (`lkexaw`) making `Priority` and
    `Work-Kind` required at the ready-to-execute gate broke 175 tests across 21 files at once. See that
    function's note for why it resolves real vocabulary values rather than the `grandfathered` sentinel.
    """

    return support.ready_plan_text(plan_id=plan_id, scope_paths=scope_paths)


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

    def test_happy_path_writes_and_resumes_bound_untracked_receipt(self):
        # 1. Sanity: the fixture is genuinely ready-to-execute.
        res = L.lint_file(self.plan, checkpoint="pre-execution")
        self.assertEqual(
            res.disposition,
            S.DISPOSITION_CONFORMING,
            [d.message for d in res.diagnostics],
        )

        # 2. Happy path writes bound receipt
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

        # 3. Receipt is gitignored and untracked
        rel = ".aw/state/ipd-lifecycle/abc123.receipt.json"
        proc = subprocess.run(
            ["git", "status", "--porcelain", rel],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn(" M ", proc.stdout)
        self.assertNotIn("A  ", proc.stdout)

        # 4. Resume re-reads same receipt deterministically
        r2 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t2").receipt
        assert r2 is not None
        self.assertEqual(r["plan_content_digest"], r2["plan_content_digest"])
        self.assertEqual(r["requirement_digest"], r2["requirement_digest"])
        self.assertEqual(r["base_head"], r2["base_head"])
        self.assertEqual(r["scope_paths"], r2["scope_paths"])
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.assertEqual(stored["requirement_digest"], r2["requirement_digest"])
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))

    def test_receipt_invalidation_and_persistence(self):
        """A change to the plan's frozen contract invalidates receipt; non-contract edits & disjoint commits persist."""
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))

        # Scope addition invalidates
        rescoped = self.plan.read_text().replace(
            "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
            "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, agent_workflows/extra.py",
        )
        self.assertFalse(LC.receipt_is_current(stored, rescoped))

        # E-item rewrite invalidates
        retasked = self.plan.read_text().replace(
            "- [ ] E-01 ", "- [ ] E-01 REWRITTEN ", 1
        )
        self.assertFalse(LC.receipt_is_current(stored, retasked))

        # Non-contract edit (trailing prose) preserves validity
        commented = self.plan.read_text() + "\n<!-- a non-contract edit -->\n"
        self.assertTrue(LC.receipt_is_current(stored, commented))

        # Disjoint commit preserves validity
        (self.root / "unrelated.txt").write_text("hello", encoding="utf-8")
        _commit_all(self.root, "unrelated change on a disjoint path")
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

    def test_dirty_paths_and_scope_refusal(self):
        """Disjoint dirty work does not block begin; in-scope dirty work is refused."""
        # 1. Disjoint dirty path does not block
        (self.root / "dirty.txt").write_text("x", encoding="utf-8")
        (self.root / "some_other_module.py").write_text("y = 1\n", encoding="utf-8")
        result = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(result.exit_code, LC.EXIT_OK)
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").exists())

        # Clean receipt for subsequent failure tests
        LC.receipt_path_for(self.root, "abc123").unlink()

        # 2. In-scope dirty file refused
        demo = self.root / "agent_workflows" / "demo.py"
        demo.parent.mkdir(parents=True, exist_ok=True)
        demo.write_text("in_scope_change = True\n", encoding="utf-8")
        res2 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res2.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("Scope-Paths", res2.message)
        self.assertIn("agent_workflows/demo.py", res2.message)
        self._no_receipt()
        demo.unlink()

        # 3. In-scope dirty under directory refused
        f = self.root / "tests" / "test_demo.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("def test_x():\n    assert True\n", encoding="utf-8")
        res3 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res3.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("tests/test_demo.py", res3.message)
        self._no_receipt()

    def test_invalid_preconditions_fail_closed(self):
        """Missing actor, missing id, or non-conforming lint fails closed and writes nothing."""
        # Missing actor
        res1 = LC.begin(self.root, self.plan, "", timestamp="t")
        self.assertEqual(res1.exit_code, LC.EXIT_CANNOT_RUN)
        self._no_receipt()

        # Non-conforming lint (draft status)
        bad = (
            self.plan.read_text()
            .replace("- Status: approved", "- Status: draft")
            .replace("- Approval: 2026-08-24, human: approved\n", "")
        )
        self.plan.write_text(bad, encoding="utf-8")
        _commit_all(self.root, "make plan draft")
        res2 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res2.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(res2.findings)
        self._no_receipt()

        # Missing id
        noid = bad.replace("- Id: abc123\n", "")
        self.plan.write_text(noid, encoding="utf-8")
        _commit_all(self.root, "strip id")
        res3 = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res3.exit_code, LC.EXIT_CANNOT_RUN)

    def test_interrupted_write_leaves_no_valid_receipt(self):
        # Simulate a crash during atomic write: os.replace raises AFTER temp file is written.
        with mock.patch.object(LC.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self._no_receipt()
        rdir = LC.receipt_dir(self.root)
        leftovers = list(rdir.glob(".receipt-*.tmp")) if rdir.exists() else []
        self.assertEqual(
            leftovers, [], "atomic write must not leave a temp file behind"
        )


class BeginCliTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)
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

    def test_cli_happy_path_and_untracked_receipt(self):
        """CLI happy path exits 0, writes receipt, and mutates no tracked file."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = LC.run_begin(self._ns())
        self.assertEqual(rc, LC.EXIT_OK, buf.getvalue())
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").is_file())

        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in proc.stdout.splitlines():
            self.assertNotIn(".aw/records/plans", line)
            self.assertFalse(line.startswith("M "), line)
            self.assertFalse(line.startswith("A "), line)

    def test_cli_refusal_exit_codes(self):
        """CLI returns exit 2 on unresolved selector and exit 1 on non-conforming lint."""
        # Unresolved selector -> 2
        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            rc1 = LC.run_begin(self._ns(plan="nosuchplan"))
        self.assertEqual(rc1, LC.EXIT_CANNOT_RUN)

        # Non-conforming lint -> 1
        bad = (
            self.plan.read_text()
            .replace("- Status: approved", "- Status: draft")
            .replace("- Approval: 2026-08-24, human: approved\n", "")
        )
        self.plan.write_text(bad, encoding="utf-8")
        _commit_all(self.root, "draft")
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = LC.run_begin(self._ns())
        self.assertEqual(rc2, LC.EXIT_FINDINGS)


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

    def test_finalize_happy_path_preview_and_evidence_surfacing(self):
        """Finalize preview leaves tree untouched; apply=True moves plan with evidence and computes in-scope commits."""
        self._begin()
        self._do_inscope_work_and_commit()

        # Preview without apply does not move plan
        prev = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=False)
        self.assertEqual(prev.exit_code, LC.EXIT_OK)
        self.assertIsNone(prev.commit)
        self.assertTrue(self.plan.is_file())

        # Real apply moves plan with evidence
        result = LC.finalize(
            self.root, self.plan, "opencode/test", "did the work", apply=True
        )
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertIsNotNone(result.commit)
        self.assertFalse(self.plan.exists())
        moved = self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
        self.assertTrue(moved.is_file())
        moved_text = moved.read_text()
        self.assertIn("opencode/test", moved_text)
        self.assertIn("- Status: executed", moved_text)
        self.assertEqual(
            result.evidence["pre_transition"]["disposition"], S.DISPOSITION_CONFORMING
        )
        self.assertEqual(
            result.evidence["post_transition"]["disposition"], S.DISPOSITION_CONFORMING
        )

        # Lifecycle commit is path-scoped
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
                f.startswith(".aw/records/plans/"), f"touched non-plan: {f}"
            )

        # Intervening in-scope commits surfaced
        audit = result.evidence["scope_audit"]
        self.assertIn("agent_workflows/demo.py", audit["intervening_in_scope_commits"])
        self.assertIn("tests/test_demo.py", audit["intervening_in_scope_commits"])
        self.assertEqual(audit["out_of_scope_paths"], [])

    def test_scope_boundary_enforcement(self):
        """Undeclared paths are refused; declared paths finalize successfully."""
        # 1. Undeclared path refused
        plan1 = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="def456", scope_paths="agent_workflows/demo.py"
            ),
            "20260824-demo-02-def456-narrow.ipd.md",
        )
        _commit_all(self.root, "add narrow plan")
        LC.begin(self.root, plan1, "opencode/test", timestamp="t")
        (self.root / "tests" / "test_empty_state_ux.py").write_text(
            "x\n", encoding="utf-8"
        )
        _commit_all(self.root, "out-of-scope edit")
        res1 = LC.finalize(self.root, plan1, "opencode/test", "m", apply=True)
        self.assertEqual(res1.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(any("tests/test_empty_state_ux.py" in f for f in res1.findings))
        self.assertTrue(plan1.is_file())

        # 2. Declared path succeeds
        plan2 = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="def789",
                scope_paths="agent_workflows/demo.py, tests/test_empty_state_ux.py",
            ),
            "20260824-demo-02-def789-wide.ipd.md",
        )
        _commit_all(self.root, "add wide plan")
        LC.begin(self.root, plan2, "opencode/test", timestamp="t")
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        (self.root / "tests" / "test_empty_state_ux.py").write_text(
            "z\n", encoding="utf-8"
        )
        _commit_all(self.root, "in-scope work incl. declared extra path")
        res2 = LC.finalize(self.root, plan2, "opencode/test", "m", apply=True)
        self.assertEqual(res2.exit_code, LC.EXIT_OK)

    def test_precondition_refusals(self):
        """Absent receipt, missing actor/message, or incomplete checklist fail closed."""
        # Absent receipt
        res_norcpt = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(res_norcpt.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(self.plan.is_file())

        # Missing actor / message
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

        # Incomplete checklist (pre-transition non-conforming)
        plan_inc = _write_plan(
            self.root,
            _ready_plan_text(plan_id="inc123"),
            "20260824-demo-02-inc123-incomplete.ipd.md",
        )
        _commit_all(self.root, "add incomplete plan")
        LC.begin(self.root, plan_inc, "opencode/test", timestamp="t")
        res_inc = LC.finalize(self.root, plan_inc, "opencode/test", "m", apply=True)
        self.assertEqual(res_inc.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(plan_inc.is_file())

    def test_receipt_staleness_and_self_execution_edits(self):
        """Contract rewrites and scope additions refuse; self-execution checklist/evidence edits succeed."""
        self._begin()

        # Contract rewrite refuses as stale
        self.plan.write_text(
            self.plan.read_text().replace(
                "- [x] E-01 ", "- [x] E-01 REWRITTEN REQUIREMENT ", 1
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "rewrite requirement")
        res_stale = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(res_stale.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any(
                "stale" in f.lower() or "digest" in f.lower()
                for f in res_stale.findings
            )
        )

        # Scope addition refuses without a reason
        self.tearDown()
        self.setUp()
        self._begin()
        self.plan.write_text(
            self.plan.read_text().replace(
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, agent_workflows/snuck_in.py",
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "scope edit")
        res_snuck = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(res_snuck.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any(
                "snuck_in.py" in f and "--scope-reason" in f for f in res_snuck.findings
            )
        )

        # Conforming self-execution edits succeed without stale refusal
        self.tearDown()
        self.setUp()
        self._begin()
        edited = self.plan.read_text()
        edited = edited.replace("- [ ] E-01 ", "- [x] E-01 ", 1).replace(
            "  - Execution state: pending", "  - Execution state: performed", 1
        )
        edited = (
            edited.replace("- [ ] V-01 validates E-01", "- [x] V-01 validates E-01", 1)
            .replace(
                "  - Observed evidence:\n",
                "  - Observed evidence: pasted real command output here.\n",
                1,
            )
            .replace("  - Result: pending", "  - Result: pass", 1)
        )
        edited += "\n- 2026-08-24 executed (opencode/test): all V items verified.\n"
        self.plan.write_text(edited, encoding="utf-8")
        _commit_all(self.root, "execute the plan")
        code, message, _evidence, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code, LC.EXIT_OK, f"{message} findings={findings}")
        self.assertFalse(
            [f for f in findings if "stale" in f.lower() or "digest" in f.lower()]
        )

    def test_fail_loud_index_refresh_aborts_transaction(self):
        """A failing owned plans-index refresh must FAIL the transaction, never swallow + succeed."""
        self._begin()
        self._do_inscope_work_and_commit()
        with mock.patch.object(
            LC, "_refresh_plans_index_fail_loud", side_effect=RuntimeError("index boom")
        ):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertNotEqual(result.exit_code, LC.EXIT_OK)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("index", result.message.lower())
        self.assertIn("COMMITTED-INCOMPLETE", result.message)
        journal = LC.read_finalize_journal(self.root, "abc123")
        assert journal is not None
        self.assertEqual(journal["phase"], LC.PHASE_COMMITTED_INCOMPLETE)


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

    def test_headless_reconciliation_with_reasons_and_clean_delta(self):
        """Headless reconciliation accepts reasons/acks in both directions, and clean delta needs no notes."""
        # 1. Clean delta is frictionless
        plan_clean = self._plan("agent_workflows/demo.py, tests/test_demo.py")
        self._begin(plan_clean)
        self._write("agent_workflows/demo.py")
        self._write("tests/test_demo.py")
        _commit_all(self.root, "clean in-scope work")
        res_clean = LC.finalize(
            self.root, plan_clean, "opencode/test", "clean", apply=True
        )
        self.assertEqual(res_clean.exit_code, LC.EXIT_OK)
        moved_clean = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan_clean.name
        ).read_text()
        self.assertNotIn("Scope reconciliation", moved_clean)

        # 2. Both directions at once (out-of-scope + in-scope-unmodified)
        self.tearDown()
        self.setUp()
        plan_both = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan_both)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "both directions work")
        res_both = LC.finalize(
            self.root,
            plan_both,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/extra.py": "discovered mid-stream"},
            scope_acks={"tests/declared.py": "not-needed"},
        )
        self.assertEqual(res_both.exit_code, LC.EXIT_OK)
        moved_both = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan_both.name
        ).read_text()
        self.assertIn("out-of-scope tests/extra.py: discovered mid-stream", moved_both)
        self.assertIn("in-scope-unmodified tests/declared.py: not-needed", moved_both)

    def test_headless_reconciliation_refusals(self):
        """Missing or empty reasons/acks fail closed and refuse finalization."""
        # Missing out-of-scope reason fails closed naming command
        plan1 = self._plan("agent_workflows/demo.py")
        self._begin(plan1)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "work incl. out-of-scope")
        res1 = LC.finalize(self.root, plan1, "opencode/test", "m", apply=True)
        self.assertEqual(res1.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("--scope-reason", res1.message)
        self.assertTrue(plan1.is_file())

        # Empty reason refuses
        res2 = LC.finalize(
            self.root,
            plan1,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/extra.py": "   "},
        )
        self.assertEqual(res2.exit_code, LC.EXIT_FINDINGS)

        # Missing in-scope-unmodified ack fails closed
        self.tearDown()
        self.setUp()
        plan2 = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan2)
        self._write("agent_workflows/demo.py")
        _commit_all(self.root, "touch only demo.py")
        res3 = LC.finalize(self.root, plan2, "opencode/test", "m", apply=True)
        self.assertEqual(res3.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(any("tests/declared.py" in f for f in res3.findings))

    def test_tty_interactive_reconciliation(self):
        """Batched prompt collects both directions; empty prompt response refuses."""
        plan = self._plan("agent_workflows/demo.py, tests/declared.py")
        self._begin(plan)
        self._write("agent_workflows/demo.py")
        self._write("tests/extra.py")
        _commit_all(self.root, "both directions")
        calls = {"n": 0}

        def fake_prompt(out_of_scope, in_scope_unmodified):
            calls["n"] += 1
            self.assertIn("tests/extra.py", out_of_scope)
            self.assertIn("tests/declared.py", in_scope_unmodified)
            return {
                "reasons": {p: "prompted reason" for p in out_of_scope},
                "acks": {p: "prompted-ack" for p in in_scope_unmodified},
            }

        res = LC.finalize(
            self.root,
            plan,
            "opencode/test",
            "m",
            apply=True,
            interactive=True,
            prompt=fake_prompt,
        )
        self.assertEqual(res.exit_code, LC.EXIT_OK)
        self.assertEqual(calls["n"], 1)
        moved_text = (
            self.root / ".aw" / "records" / "plans" / "executed" / plan.name
        ).read_text()
        self.assertIn("prompted reason", moved_text)
        self.assertIn("prompted-ack", moved_text)

        # Empty reason from prompt fails closed
        self.tearDown()
        self.setUp()
        plan2 = self._plan("agent_workflows/demo.py")
        self._begin(plan2)
        self._write("tests/extra.py")
        _commit_all(self.root, "out of scope")
        res2 = LC.finalize(
            self.root,
            plan2,
            "opencode/test",
            "m",
            apply=True,
            interactive=True,
            prompt=lambda oos, isu: {"reasons": {p: "" for p in oos}, "acks": {}},
        )
        self.assertEqual(res2.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(plan2.is_file())

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


class AdditiveScopeWideningTests(unittest.TestCase):
    """rcptwiden `63425h` E-04: an ADDITIVE `Scope-Paths` widening finalizes with a recorded reason.

    THE DEFECT THIS CLOSES IS AN INCENTIVE INVERSION, not an inconvenience. An agent that discovered
    mid-execution that it must touch an undeclared file had two options and the system punished the
    honest one: DECLARING the path changed the plan's frozen region, so `receipt_is_current` returned
    False and finalize refused as STALE, while editing the file WITHOUT declaring it finalized (and, if
    the edit was merely uncommitted, was DISREGARDED and demanded no reason at all). Measured three
    times in run `run-20260917T023628Z-4108757` on `i3d6ml`, `tx6q0h` and `sy7uwh`: $95.71 and 3h10m of
    a $212.60 run, three lanes stranded, one orchestrator left `dependency-blocked`.

    BOTH VARIANTS ARE ASSERTED THROUGHOUT, and that is the point rather than thoroughness for its own
    sake. The reason requirement CANNOT ride on the existing out-of-scope reconciliation, because that
    is computed against the RECEIPT's OLD fence: for an UNCOMMITTED added path `out_of_scope_paths` is
    EMPTY, so a requirement expressed that way would be silently vacuous in the commonest case. The
    uncommitted variant is therefore where a fake implementation would hide, and every test below that
    can run in both runs in both.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()
        self.plan = _write_plan(
            self.root, _completed_plan_text(), "20260824-demo-01-abc123-demo.ipd.md"
        )
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        _commit_all(self.root, "init")
        res = LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        self.assertEqual(res.exit_code, LC.EXIT_OK, res.message)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _do_the_work_and_widen(self, *, commit: bool, added="tests/test_extra.py"):
        """Do in-scope work, ALSO touch an undeclared file, and DECLARE it (the honest act)."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("y\n", encoding="utf-8")
        (self.root / added).write_text("z\n", encoding="utf-8")
        self.plan.write_text(
            self.plan.read_text().replace(
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, " + added,
            ),
            encoding="utf-8",
        )
        self.assertIn(added, self.plan.read_text(), "the widening did not apply")
        if commit:
            _commit_all(self.root, "in-scope work plus the newly declared path")
        else:
            # The plan edit itself must be committed for the UNCOMMITTED variant to be about the
            # ADDED FILE being uncommitted rather than about the plan being dirty.
            subprocess.run(
                ["git", "add", "--", str(self.plan.relative_to(self.root))],
                cwd=self.root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-q", "-m", "declare the newly needed path"],
                cwd=self.root,
                check=True,
            )

    def test_widening_finalizes_when_each_added_path_carries_a_reason(self):
        """THE FIX, in both variants: the honest declaration now completes."""
        for commit in (True, False):
            with self.subTest(committed=commit):
                self.setUp()
                self._do_the_work_and_widen(commit=commit)
                result = LC.finalize(
                    self.root,
                    self.plan,
                    "opencode/test",
                    "did the work",
                    apply=True,
                    scope_reasons={
                        "tests/test_extra.py": "the approved work needed this test file"
                    },
                )
                self.assertEqual(
                    result.exit_code,
                    LC.EXIT_OK,
                    f"{result.message} / {result.findings}",
                )
                moved = (
                    self.root
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / self.plan.name
                )
                self.assertTrue(moved.is_file(), "the plan did not reach executed/")
                text = moved.read_text()
                # THE ACCEPTED WIDENING IS ON THE PERMANENT RECORD, labelled as a widening rather
                # than as an out-of-scope edit, and named exactly ONCE.
                self.assertIn("widened-scope tests/test_extra.py", text)
                self.assertIn("the approved work needed this test file", text)
                self.assertEqual(
                    text.count("tests/test_extra.py:"),
                    1,
                    "the path must be recorded once, not once per demand",
                )
                self.assertNotIn("out-of-scope tests/test_extra.py", text)
                # And the evidence records the accept explicitly.
                widening = result.evidence.get("frozen_region_widening", {})
                self.assertTrue(widening.get("accepted"))
                self.assertEqual(widening.get("added_paths"), ["tests/test_extra.py"])
                self.assertEqual(
                    result.evidence["scope_audit"]["widened_paths"],
                    ["tests/test_extra.py"],
                )
                self.tearDown()

    def test_widening_audit_and_deduplication(self):
        """Audits widened paths and verifies one reason satisfies both out-of-scope and widened demands."""
        # Uncommitted added path: in widened_paths, not out_of_scope_paths
        self._do_the_work_and_widen(commit=False)
        rc, _msg, evidence, _f = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(rc, LC.EXIT_OK)
        audit = evidence["scope_audit"]
        self.assertEqual(audit["out_of_scope_paths"], [])
        self.assertIn("tests/test_extra.py", audit["disregarded_unowned_paths"])
        self.assertEqual(audit["widened_paths"], ["tests/test_extra.py"])

        # Committed added path: present in both, one reason satisfies both
        self.tearDown()
        self.setUp()
        self._do_the_work_and_widen(commit=True)
        rc2, _msg2, evidence2, _f2 = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(rc2, LC.EXIT_OK)
        audit2 = evidence2["scope_audit"]
        self.assertIn("tests/test_extra.py", audit2["out_of_scope_paths"])
        self.assertIn("tests/test_extra.py", audit2["widened_paths"])

        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "did the work",
            apply=True,
            scope_reasons={"tests/test_extra.py": "one reason, both demands"},
        )
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
        moved = self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
        self.assertEqual(
            moved.read_text().count("tests/test_extra.py:"),
            1,
            "one supplied reason must produce ONE record, not one per demand",
        )

    def test_widening_refusals_and_failure_modes(self):
        """Widening is refused on missing reason, empty reason, requirement rewrite, path removal, or directory addition."""
        # 1. Missing reason refuses (both committed and uncommitted)
        for commit in (True, False):
            with self.subTest(case="missing_reason", committed=commit):
                self.setUp()
                self._do_the_work_and_widen(commit=commit)
                res = LC.finalize(
                    self.root, self.plan, "opencode/test", "m", apply=True
                )
                self.assertEqual(res.exit_code, LC.EXIT_FINDINGS)
                self.assertTrue(self.plan.is_file())
                self.tearDown()

        # 2. Empty reason refuses
        self.setUp()
        self._do_the_work_and_widen(commit=False)
        res_empty = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/test_extra.py": "   "},
        )
        self.assertEqual(res_empty.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(self.plan.is_file())
        self.tearDown()

        # 3. Requirement rewrite still refuses as STALE
        self.setUp()
        self._do_the_work_and_widen(commit=True)
        self.plan.write_text(
            self.plan.read_text().replace(
                "- [x] E-01 ", "- [x] E-01 REWRITTEN REQUIREMENT ", 1
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "also rewrite a frozen requirement")
        res_rewrite = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/test_extra.py": "needed it"},
        )
        self.assertEqual(res_rewrite.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", res_rewrite.message)
        self.tearDown()

        # 4. Scope removal refuses and names removed path
        self.setUp()
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        self.plan.write_text(
            self.plan.read_text().replace(
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
                "- Scope-Paths: agent_workflows/demo.py",
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "narrow the fence after begin")
        res_rem = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(res_rem.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", res_rem.message)
        self.assertTrue(
            any("REMOVED" in f and "tests/test_demo.py" in f for f in res_rem.findings)
        )
        self.tearDown()

        # 5. Directory addition refuses and names offending entry
        self.setUp()
        self._do_the_work_and_widen(commit=True, added="tests/test_extra.py")
        self.plan.write_text(
            self.plan.read_text().replace(", tests/test_extra.py", ", tests/"),
            encoding="utf-8",
        )
        _commit_all(self.root, "widen to a whole directory")
        res_dir = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/": "I would like the whole tree please"},
        )
        self.assertEqual(res_dir.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", res_dir.message)
        self.assertTrue(
            any("tests/" in f and "DIRECTORY or GLOB" in f for f in res_dir.findings)
        )
        self.assertTrue(self.plan.is_file())


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
    def test_clean_finalize_and_journal_lifecycle(self):
        """Clean transaction completes, clears journal, consumes receipt, and leaves no lock; pre-mutation fault rolls back."""
        # Clean finalize
        self._begin_and_work()
        result = LC.finalize(self.root, self.plan, "opencode/test", "clean", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue(self._executed_path().is_file())
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").exists())
        self.assertFalse(LC.finalize_lock_path(self.root).exists())

        # Reset for fault before mutation
        self.tearDown()
        self.setUp()
        self._begin_and_work()
        head_before = self._head()
        orig_bytes = self.plan.read_text()
        res_fault = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="before_mutation",
        )
        self.assertEqual(res_fault.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertTrue(self.plan.is_file())
        self.assertEqual(self.plan.read_text(), orig_bytes)
        self.assertFalse(self._executed_path().exists())
        self.assertEqual(self._head(), head_before)
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))

    def test_lock_contention_and_stale_reclamation(self):
        """Second finalizer is locked out when lock is held; dead PID lock is reclaimed."""
        self._begin_and_work()
        LC.acquire_finalize_lock(self.root, "abc123")
        lock = LC.finalize_lock_path(self.root)
        import json as _json
        import os as _os

        import subprocess as _subprocess
        import sys as _sys

        # A genuinely LIVE pid that is not ours. Not PID 1: that is `init` on POSIX but names no
        # process at all on Windows (whose PIDs are multiples of 4), so it would test nothing there.
        other = _subprocess.Popen(
            [_sys.executable, "-c", "import time; time.sleep(60)"]
        )
        self.addCleanup(other.wait)
        self.addCleanup(other.kill)
        data = _json.loads(lock.read_text())
        data["pid"] = other.pid
        lock.write_text(_json.dumps(data), encoding="utf-8")
        with self.assertRaises(LC.TransactionLockError):
            LC.acquire_finalize_lock(self.root, "abc123")
        self.assertIsNone(
            other.poll(), "the liveness probe must OBSERVE the holder, never kill it"
        )

        # Reclaim stale lock (dead PID 2**31 - 1)
        lock.write_text(
            _json.dumps({"plan_id": "abc123", "pid": 2**31 - 1}), encoding="utf-8"
        )
        LC.acquire_finalize_lock(self.root, "abc123")
        self.assertEqual(_json.loads(lock.read_text())["pid"], _os.getpid())
        LC.release_finalize_lock(self.root)

    def test_precommit_fault_rollback_and_recovery(self):
        """Pre-commit faults roll back plan and index, preserve disjoint work, and recover on restart."""
        self._begin_and_work()
        head_before = self._head()

        # Disjoint dirty + staged work that rollback must not touch
        (self.root / "unrelated_dirty.txt").write_text("dirty\n", encoding="utf-8")
        (self.root / "unrelated_staged.txt").write_text("staged\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "unrelated_staged.txt"], cwd=self.root, check=True
        )

        res = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_move",
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertTrue(self.plan.is_file())
        self.assertFalse(self._executed_path().exists())
        self.assertEqual(self._head(), head_before)
        self.assertEqual((self.root / "unrelated_dirty.txt").read_text(), "dirty\n")
        self.assertEqual((self.root / "unrelated_staged.txt").read_text(), "staged\n")

        # Re-finalize recovers cleanly
        res_rec = LC.finalize(
            self.root, self.plan, "opencode/test", "recovered", apply=True
        )
        self.assertEqual(res_rec.exit_code, LC.EXIT_OK)
        self.assertTrue(self._executed_path().is_file())

    def test_postcommit_committed_incomplete_and_resume(self):
        """Fault after commit lands in committed-incomplete; resume finishes without second commit."""
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
            r1 = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(r1.exit_code, LC.EXIT_FINDINGS)
        self.assertIsNotNone(r1.commit)
        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_COMMITTED_INCOMPLETE)
        self.assertTrue(LC.receipt_path_for(self.root, "abc123").exists())
        head_after_commit = self._head()

        # Persistent failure stays incomplete
        with mock.patch.object(L, "lint_file", failing_post):
            r_stay = LC.finalize(
                self.root, self._executed_path(), "opencode/test", "m", apply=True
            )
        self.assertEqual(r_stay.exit_code, LC.EXIT_FINDINGS)

        # Successful resume reruns only post-transition, creates no second commit, consumes receipt
        r2 = LC.finalize(
            self.root, self._executed_path(), "opencode/test", "m", apply=True
        )
        self.assertEqual(r2.exit_code, LC.EXIT_OK)
        self.assertEqual(self._head(), head_after_commit)
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").exists())

    def test_unrecoverable_failures_and_unknown_outcome(self):
        """Rollback failure retains journal in unknown outcome; corrupt/unknown-outcome journal fails closed."""
        self._begin_and_work()
        with mock.patch.object(
            LC,
            "_rollback_precommit",
            return_value=(False, "simulated rollback failure"),
        ):
            res = LC.finalize(
                self.root,
                self.plan,
                "opencode/test",
                "m",
                apply=True,
                fault_injection="after_move",
            )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("NOT reported", res.message)
        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_UNKNOWN_OUTCOME)

        # Reinvocation with unknown outcome fails closed
        res_reinv = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(res_reinv.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("unknown-outcome", res_reinv.message)


class TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout(unittest.TestCase):
    """plan `u23gbn`: the relocation is in the SHARED transaction body, so EVERY plan gets it.

    WHY THIS CLASS EXISTS RATHER THAN LEAVING IT TO THE ROLLUP SUITE. `_finalize_transaction` has
    exactly two callers, `finalize` (every ordinary plan, and `aw set executed`) and
    `retire_orchestrator`. The maintainer resolved the architecture question (OQ-03) to change that
    SHARED body in place rather than fork a rollup-specific one, precisely because a forked copy's
    divergence would be invisible: the test pinning gate parity checks only that a gate's NAME is
    listed. So the blast radius is the ordinary terminal transition, and it must be asserted HERE, on
    the path 500+ plans take, not only on the four-per-corpus rollup path.
    """

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

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def _porcelain(self) -> list:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return [ln for ln in out.splitlines() if ln.strip()]

    def _begin_and_work(self):
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        (self.root / "agent_workflows" / "demo.py").write_text("x\n", encoding="utf-8")
        (self.root / "tests" / "test_demo.py").write_text("x\n", encoding="utf-8")
        _commit_all(self.root, "in-scope work")

    def test_the_shared_tree_is_never_mid_move_during_an_ordinary_finalize(self):
        """Sampled at the instant before the shared checkout is written at all."""
        self._begin_and_work()
        # A peer's unrelated uncommitted edit, which must be untouched throughout.
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _commit_all(self.root, "peer base")
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        samples = {}
        real_land = LC.land_worktree_commit

        def spy(repo_root, landed, *, expected_base=None):
            samples["pre-shared-write"] = self._porcelain()
            return real_land(repo_root, landed, expected_base=expected_base)

        pre = self._head()
        with mock.patch.object(LC, "land_worktree_commit", spy):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} {result.findings}"
        )

        sampled = samples["pre-shared-write"]
        self.assertEqual(
            [ln for ln in sampled if ln[:1] == "R"],
            [],
            f"the shared checkout holds a staged rename mid-transaction: {sampled}",
        )
        self.assertEqual(
            [ln for ln in sampled if "/executed/" in ln],
            [],
            f"the moved plan is present in the shared tree mid-transaction: {sampled}",
        )
        self.assertEqual(
            [ln for ln in sampled if "peer.txt" not in ln and "/INDEX." not in ln],
            [],
            f"unexpected shared-tree residue mid-transaction: {sampled}",
        )
        # The peer's bytes survive verbatim, and main advanced by exactly one commit.
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"),
            "peer v2 UNCOMMITTED\n",
        )
        count = subprocess.run(
            ["git", "rev-list", "--count", f"{pre}..HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(count, "1")

    def test_shared_tree_stability_and_narrow_edit_release(self):
        """Shared tree is never mid-move during finalize; edit release refuses unsafe cases."""
        self._begin_and_work()
        (self.root / "peer.txt").write_text("peer v1\n", encoding="utf-8")
        _commit_all(self.root, "peer base")
        (self.root / "peer.txt").write_text("peer v2 UNCOMMITTED\n", encoding="utf-8")

        samples = {}
        real_land = LC.land_worktree_commit

        def spy(repo_root, landed, *, expected_base=None):
            samples["pre-shared-write"] = self._porcelain()
            return real_land(repo_root, landed, expected_base=expected_base)

        with mock.patch.object(LC, "land_worktree_commit", spy):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} {result.findings}"
        )

        sampled = samples["pre-shared-write"]
        self.assertEqual([ln for ln in sampled if ln[:1] == "R"], [])
        self.assertEqual([ln for ln in sampled if "/executed/" in ln], [])
        self.assertEqual(
            [ln for ln in sampled if "peer.txt" not in ln and "/INDEX." not in ln], []
        )
        self.assertEqual(
            (self.root / "peer.txt").read_text(encoding="utf-8"),
            "peer v2 UNCOMMITTED\n",
        )

        # Edit release helper is narrow and lossless
        self.tearDown()
        self.setUp()
        self._begin_and_work()
        original = self.plan.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT, not ours\n"
        self.plan.write_text(peer_bytes, encoding="utf-8")
        plan_rel = LC._repo_relative(self.root, self.plan)
        dest_rel = plan_rel.replace("/pending/", "/executed/")
        head = self._head()
        for name, kwargs in {
            "foreign bytes": dict(mirrored_bytes=original, committed_bytes=original),
            "no committed bytes": dict(mirrored_bytes=peer_bytes, committed_bytes=None),
            "commit does not carry them": dict(
                mirrored_bytes=peer_bytes, committed_bytes=peer_bytes
            ),
        }.items():
            with self.subTest(case=name):
                released = LC._release_own_plan_edit_before_landing(
                    self.root,
                    plan_rel,
                    landed=head,
                    dest_rel=dest_rel,
                    **kwargs,
                )
                self.assertIsNone(released)
                self.assertEqual(self.plan.read_text(encoding="utf-8"), peer_bytes)

    def test_coordinator_commit_isolation_and_worktree_cleanup(self):
        """Commit is produced outside shared checkout and no coordinator worktree or branch is left behind."""
        self._begin_and_work()
        real_git = LC._git
        commit_roots = []

        def spy_git(root, args):
            if args and args[0] == "commit":
                commit_roots.append(Path(root).resolve())
            return real_git(root, args)

        with mock.patch.object(LC, "_git", spy_git):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
        self.assertTrue(commit_roots, "no git commit was observed at all")
        for root in commit_roots:
            self.assertNotEqual(root, self.root.resolve())

        worktrees = subprocess.run(
            ["git", "worktree", "list"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        branches = subprocess.run(
            ["git", "branch", "--list"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertNotIn("aw-coordinator-", worktrees)
        self.assertNotIn("aw/coordinator/", branches)

    def test_uncommitted_plan_edits_and_peer_conflict_refusal(self):
        """Uncommitted plan edits ride the lifecycle commit, while conflicting peer edits roll back cleanly."""
        self._begin_and_work()
        self.plan.write_text(
            self.plan.read_text(encoding="utf-8")
            + "\nUNCOMMITTED EVIDENCE EDIT BY THE EXECUTOR\n",
            encoding="utf-8",
        )
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} {result.findings}"
        )
        moved = self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
        self.assertIn("UNCOMMITTED EVIDENCE EDIT", moved.read_text(encoding="utf-8"))

        # Conflicting peer edit during commit rolls back and is NOT committed incomplete
        self.tearDown()
        self.setUp()
        self._begin_and_work()
        head = self._head()
        original = self.plan.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT IN FLIGHT, uncommitted\n"
        real_git = LC._git

        def spy_git(root, args):
            if (
                args
                and args[0] == "commit"
                and Path(root).resolve() != self.root.resolve()
            ):
                self.plan.write_text(peer_bytes, encoding="utf-8")
            return real_git(root, args)

        with mock.patch.object(LC, "_git", spy_git):
            result2 = LC.finalize(
                self.root, self.plan, "opencode/test", "m", apply=True
            )

        self.assertNotEqual(result2.exit_code, LC.EXIT_OK)
        self.assertIn("would be overwritten", result2.message)
        self.assertEqual(self.plan.read_text(encoding="utf-8"), peer_bytes)
        self.assertEqual(self._head(), head)
        journal = LC.read_finalize_journal(self.root, "abc123")
        if journal is not None:
            self.assertNotEqual(journal.get("phase"), LC.PHASE_COMMITTED_INCOMPLETE)


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

    def test_set_executed_delegation_variants(self):
        """aw set executed, aw ipd set executed, and aw set done all delegate into finalize."""
        variants = [
            ["set", "executed", "abc123"],
            ["ipd", "set", "executed", "abc123"],
            ["set", "done", "abc123"],
        ]
        for cmd_prefix in variants:
            with self.subTest(cmd=" ".join(cmd_prefix)):
                self.setUp()
                self._begin_and_work()
                rc, out = self._run_cli(
                    cmd_prefix
                    + [
                        "--actor",
                        "opencode/test",
                        "--message",
                        "did it",
                        "--yes",
                    ]
                )
                self.assertEqual(rc, 0, out)
                exec_path = (
                    self.root
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / self.plan.name
                )
                self.assertTrue(exec_path.is_file())
                moved = exec_path.read_text(encoding="utf-8")
                self.assertIn("- Status: executed", moved)
                self.assertIn("opencode/test", moved)
                self.tearDown()

    def test_non_delegated_transitions_preserve_direct_paths(self):
        """Prompt execution, retirement (superseded), and nonterminal transitions do not delegate."""
        # 1. Prompt terminal executed transition keeps raw path
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

        # 2. Plan retirement (superseded) keeps raw git-mv path
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

        # 3. Nonterminal plan transition (to approved) keeps raw path
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

    def test_delegation_refusals(self):
        """Missing actor fails closed (exit 2) and missing receipt refuses (exit 1)."""
        # Missing actor fails closed
        self._begin_and_work()
        rc, out = self._run_cli(["set", "executed", "abc123", "--yes"])
        self.assertEqual(rc, 2)
        self.assertIn("--actor", out)
        self.assertTrue(self.plan.is_file())
        self.assertFalse(self._executed_path().exists())

        # Missing begin receipt refuses (finalize fail-closed)
        plan_noreceipt = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="norcpt",
                scope_paths="agent_workflows/demo.py, tests/test_demo.py",
            ),
            "20260824-demo-01-norcpt-demo.ipd.md",
        )
        _commit_all(self.root, "add plan norcpt")
        rc, out = self._run_cli(
            [
                "set",
                "executed",
                "norcpt",
                "--actor",
                "opencode/test",
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertEqual(rc, 1)
        self.assertTrue(plan_noreceipt.is_file())
        self.assertFalse(
            (
                self.root
                / ".aw"
                / "records"
                / "plans"
                / "executed"
                / plan_noreceipt.name
            ).exists()
        )


class ParenthesizedActorIsRefusedBeforeAnyWrite(unittest.TestCase):
    """Plan fn2l1u E-01/E-02/E-07: refuse the unparseable actor at the SETTER, not after the commit.

    The defect this closes: a parenthesized actor made the history line unparseable to the readers,
    IPD-S406 fired as POST-transition validation (i.e. AFTER the lifecycle commit), and finalize landed
    in COMMITTED-INCOMPLETE telling the operator to re-run the same command - which could not succeed,
    because the offending text was now in the file. The only escape was hand-editing a plan already in
    `executed/`, which trips the executed-transition gate too, so one bad character cost two gate
    bypasses. Every refusal below therefore asserts BOTH the nonzero exit AND that nothing was written.
    """

    BAD = "opencode (its_direct/some-model)"
    GOOD = "opencode/its_direct/some-model"

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
        from contextlib import redirect_stderr

        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _head(self) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def _assert_nothing_written(self, before_text: str, before_head: str) -> None:
        self.assertEqual(
            self.plan.read_text(encoding="utf-8"),
            before_text,
            "a refused setter must leave the plan file byte-identical",
        )
        self.assertEqual(self._head(), before_head, "a refused setter must not commit")
        self.assertTrue(self.plan.is_file(), "the plan must not be moved")

    def test_actor_validation_and_direct_writer_refusal(self):
        """E-01/E-02: actor validation guard and direct writer fail-closed behavior."""
        from agent_workflows import attention_contract as AC
        from agent_workflows import status_set as SS

        self.assertIsNone(AC.actor_refusal(self.GOOD))
        self.assertIsNotNone(AC.actor_refusal(self.BAD))
        self.assertIsNotNone(AC.actor_refusal(""))
        self.assertIsNotNone(AC.actor_refusal("   "))
        self.assertIsNotNone(AC.actor_refusal(None))
        msg = AC.actor_refusal(self.BAD) or ""
        self.assertIn("key=value", msg)
        self.assertIn("parenthesis", msg)

        # Direct caller of the writer that skipped CLI pre-flight raises ValueError
        rec = SS.read_artifact_record(self.plan, self.root)
        self.assertIsNotNone(rec)
        assert rec is not None
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        ns = argparse.Namespace(actor=self.BAD, message="m")
        with self.assertRaises(ValueError) as ctx:
            SS.apply_status_change(rec, "reviewed", self.root, ns)
        self.assertIn("parenthesis", str(ctx.exception))
        self._assert_nothing_written(before, head)

        # Finalize refuses the actor BEFORE checking if plan exists
        res = LC.finalize(
            Path("/nonexistent/repo"),
            Path("/nonexistent/repo/p.ipd.md"),
            self.BAD,
            "msg",
            apply=True,
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("parenthesis", res.message)

    def test_cli_set_refuses_parenthesized_actor_across_subcommands(self):
        """CLI subcommands (set nonterminal, ipd set, set executed) refuse parenthesized actor."""
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        subcmds = [
            ["set", "reviewed", "abc123"],
            ["ipd", "set", "reviewed", "abc123"],
            ["set", "executed", "abc123"],
        ]
        for cmd in subcmds:
            with self.subTest(cmd=" ".join(cmd)):
                rc, out = self._run_cli(
                    cmd + ["--actor", self.BAD, "--message", "m", "--yes"]
                )
                self.assertNotEqual(rc, 0, out)
                self.assertIn("parenthesis", out)
                self._assert_nothing_written(before, head)
                self.assertFalse(
                    (
                        self.root
                        / ".aw"
                        / "records"
                        / "plans"
                        / "executed"
                        / self.plan.name
                    ).exists()
                )

    def test_the_slash_form_is_ACCEPTED_so_the_guard_is_not_over_broad(self):
        """A valid slash form is accepted and records the actor verbatim."""
        rc, out = self._run_cli(
            [
                "set",
                "reviewed",
                "abc123",
                "--actor",
                self.GOOD,
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertEqual(rc, 0, out)
        text = self.plan.read_text(encoding="utf-8")
        self.assertIn(f"reviewed ({self.GOOD})", text)
        self.assertIn("- Status: reviewed", text)


class ScaffoldStopsWritingTheShapeItsOwnSetterRefuses(unittest.TestCase):
    """Plan fn2l1u E-05 / V-05: NORMALIZE the author, AND SAY SO."""

    BAD = "opencode (its_direct/some-model)"
    WANT = "opencode model=its_direct/some-model"

    def test_author_normalization_and_contract_acceptance(self):
        from agent_workflows import attention_contract as AC

        self.assertEqual(A.normalize_author(self.BAD), self.WANT)
        for good in ("opencode/its_direct/some-model", "aw set", "human maintainer"):
            with self.subTest(good=good):
                self.assertEqual(A.normalize_author(good), good)
        self.assertIsNone(AC.actor_refusal(A.normalize_author(self.BAD)))
        self.assertIsNotNone(AC.actor_refusal(self.BAD))

    def test_scaffold_output_and_history_line_parsing(self):
        """Scaffold emitted author is normalized and the history line parses cleanly."""
        from agent_workflows import record_history as RH

        text = A.build_skeleton(
            kind=S.KIND_CHILD,
            title="T",
            author=self.BAD,
            when="2026-09-09",
            set_name="demo",
            order=1,
            plan_id="aaa111",
        )
        self.assertIn(f"- Author: {self.WANT}", text)
        self.assertIn(f"- 2026-09-09 draft ({self.WANT}): created.", text)
        self.assertNotIn(self.BAD, text)

        line = next(
            ln.strip()
            for ln in text.splitlines()
            if ln.strip().startswith("- 2026-09-09 draft ")
        )
        _d, workflow, actor, message = RH._parse_record_line(line)
        self.assertEqual(workflow, "draft")
        self.assertEqual(actor, self.WANT)
        self.assertEqual(message, "created.")

    def test_run_scaffold_notice_behavior(self):
        """OQ-02 notice is printed when normalizing, and omitted when author is untouched."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        # Case 1: author normalized -> notice printed
        target1 = root / "20260909-demo-01-aaa111-t.ipd.md"
        args1 = argparse.Namespace(
            kind=S.KIND_CHILD,
            title="T",
            author=self.BAD,
            set="demo",
            order=1,
            path=str(target1),
            apply=True,
            overwrite=False,
            priority="medium",
            work_kind="chore",
        )
        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            rc1 = A.run_scaffold(args1)
        out1 = buf1.getvalue()
        self.assertEqual(rc1, 0, out1)
        self.assertIn("normalized --author", out1)
        self.assertIn(self.WANT, out1)

        # Case 2: clean author -> no notice
        target2 = root / "20260909-demo-01-aaa112-t.ipd.md"
        args2 = argparse.Namespace(
            kind=S.KIND_CHILD,
            title="T",
            author="opencode/its_direct/some-model",
            set="demo",
            order=1,
            path=str(target2),
            apply=True,
            overwrite=False,
            priority="medium",
            work_kind="chore",
        )
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = A.run_scaffold(args2)
        self.assertEqual(rc2, 0, buf2.getvalue())
        self.assertNotIn("normalized", buf2.getvalue())


if __name__ == "__main__":
    unittest.main()
