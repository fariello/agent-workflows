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
        """A change to the plan's frozen CONTRACT invalidates the receipt (OQ-01 rule (a)).

        SEMANTIC CHANGE (wtiso-03 `rchpms` E-03, backlog `xmqv5l`): the validity key is now the
        FROZEN REGION (``Scope-Paths`` + E/V requirement text), not the whole file. This test
        previously appended an HTML comment and asserted the receipt went stale; that edit lies
        OUTSIDE the frozen region, and under the new rule it correctly does NOT invalidate, because a
        conforming execution MUST edit its own plan and was being punished for it.

        The test therefore now asserts the guard on BOTH sides so its protective intent is kept
        rather than loosened: a real requirement/scope change DOES invalidate (the tight guard), and
        a non-contract edit does NOT (the xmqv5l fix).
        """
        LC.begin(self.root, self.plan, "opencode/test", timestamp="t")
        stored = LC.read_receipt(self.root, "abc123")
        assert stored is not None
        self.assertTrue(LC.receipt_is_current(stored, self.plan.read_text()))

        # TIGHT GUARD (the assertion that carries this test's original intent): changing the
        # reviewed contract - a declared Scope-Paths entry - makes this a DIFFERENT plan than the
        # one the pre-execution gate approved, so the receipt MUST go stale.
        rescoped = self.plan.read_text().replace(
            "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
            "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, agent_workflows/extra.py",
        )
        self.assertNotEqual(rescoped, self.plan.read_text(), "scope edit did not apply")
        self.assertFalse(LC.receipt_is_current(stored, rescoped))

        # TIGHT GUARD: rewriting an E-item's action text is likewise a contract change.
        retasked = self.plan.read_text().replace(
            "- [ ] E-01 ", "- [ ] E-01 REWRITTEN ", 1
        )
        self.assertNotEqual(
            retasked, self.plan.read_text(), "E-text edit did not apply"
        )
        self.assertFalse(LC.receipt_is_current(stored, retasked))

        # THE xmqv5l FIX: a non-contract edit (here, trailing prose) no longer invalidates.
        commented = self.plan.read_text() + "\n<!-- a non-contract edit -->\n"
        self.assertTrue(LC.receipt_is_current(stored, commented))

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
        """finalize refuses as STALE when the plan's frozen REQUIREMENTS changed after begin.

        SEMANTIC CHANGE 1 (wtiso-03 `rchpms` E-03, backlog `xmqv5l`): staleness is keyed on the
        frozen region, so the edit that must trigger the refusal is a REQUIREMENT/SCOPE change, not
        any byte change. This test used to append an HTML comment, which no longer invalidates (by
        design - see `receipt_is_current`).

        SEMANTIC CHANGE 2 (rcptwiden `63425h` E-04): the edit it then used - ADDING a `Scope-Paths`
        entry - is no longer a STALE refusal either, because an ADDITIVE widening whose every other
        frozen category is byte-identical is now an accept-with-a-recorded-reason. That case is
        asserted in :class:`AdditiveScopeWideningTests` below (it still REFUSES without a reason, so
        nothing silently finalizes). The STALE assertion therefore moves to an edit that genuinely
        rewrites the reviewed contract: an E-item's action text, which is never a widening.
        """
        self._begin()
        # Change the reviewed CONTRACT after begin -> the frozen-region digest no longer matches, and
        # the difference is NOT confined to an additive scope declaration.
        self.plan.write_text(
            self.plan.read_text().replace(
                "- [x] E-01 ", "- [x] E-01 REWRITTEN REQUIREMENT ", 1
            ),
            encoding="utf-8",
        )
        self.assertIn(
            "REWRITTEN REQUIREMENT", self.plan.read_text(), "E-text edit did not apply"
        )
        _commit_all(self.root, "rewrite a frozen requirement after begin")
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any("stale" in f.lower() or "digest" in f.lower() for f in result.findings)
        )
        self.assertTrue(self.plan.is_file(), "plan must be left unmoved")

    def test_scope_addition_still_refuses_without_a_reason(self):
        """The case this test used to cover still REFUSES; only the REASON it gives changed.

        Guards against the one way rcptwiden `63425h` could have made the gate worse: an added
        `Scope-Paths` entry must never SILENTLY finalize. It refuses, the plan stays put, and the
        refusal now names the missing per-path `--scope-reason` instead of a stale receipt.
        """
        self._begin()
        self.plan.write_text(
            self.plan.read_text().replace(
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, agent_workflows/snuck_in.py",
            ),
            encoding="utf-8",
        )
        self.assertIn("snuck_in.py", self.plan.read_text(), "scope edit did not apply")
        _commit_all(self.root, "edit plan scope after begin")
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(
            any(
                "agent_workflows/snuck_in.py" in f and "--scope-reason" in f
                for f in result.findings
            ),
            f"expected a per-path reason demand, got {result.findings}",
        )
        self.assertTrue(self.plan.is_file(), "plan must be left unmoved")

    def test_self_finalize_after_checklist_edits_no_stale_refusal(self):
        """END-TO-END xmqv5l REGRESSION: a self-executing agent's own checklist edits must NOT
        make finalize refuse as STALE.

        This is the exact live failure backlog `xmqv5l` reports (observed on run 7kbtkw): begin,
        execute, and in the course of executing correctly mark every E item performed, fill each V
        item's evidence, and append a `## Workflow history` line - then finalize refused with "the
        begin receipt ... is STALE" and the run was left substantially-complete. The refusal is
        asserted against here through the REAL `finalize_precheck` path, not just the predicate.
        """
        self._begin()
        edited = self.plan.read_text()
        # Exactly the edits a conforming execution makes to its own plan.
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
        _commit_all(self.root, "execute the plan (checklist + evidence + history)")

        code, message, _evidence, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(code, LC.EXIT_OK, f"{message} findings={findings}")
        self.assertFalse(
            [f for f in findings if "stale" in f.lower() or "digest" in f.lower()],
            f"self-execution edits wrongly reported the receipt stale: {findings}",
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
        """A failing owned plans-index refresh must FAIL the transaction, never swallow + succeed.

        THE CLASSIFICATION MOVED, THE GATE DID NOT (plan `u23gbn` E-07). The refresh now runs AFTER
        the reconciliation, because the plan move happens in a coordinator-owned worktree: refreshing
        during the mutating phase scanned a SHARED disk that still showed the plan at `pending/`, so
        the manifest described the OLD layout, converged, and the gate PASSED -- then the merge
        relocated the file and the manifest was instantly stale, i.e. the gate inverted into a false
        pass. Running it after the merge means a failure is POST-COMMIT, hence EXIT_FINDINGS +
        committed-incomplete rather than EXIT_CANNOT_RUN + rollback. It is emphatically still fail-loud:
        finalize does not report success.
        """
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

    def test_widening_REFUSES_when_an_added_path_lacks_a_reason(self):
        """THE F-9 CONTROL: the accept is NOT unconditional, and not vacuous when uncommitted.

        A paste showing only the committed variant would not establish this: for the uncommitted
        variant the added path never enters `out_of_scope_paths`, so a reason requirement inherited
        from that set would demand nothing and this test would pass while the gate was open.
        """
        for commit in (True, False):
            with self.subTest(committed=commit):
                self.setUp()
                self._do_the_work_and_widen(commit=commit)
                result = LC.finalize(
                    self.root, self.plan, "opencode/test", "m", apply=True
                )
                self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
                self.assertTrue(
                    any(
                        "tests/test_extra.py" in f and "--scope-reason" in f
                        for f in result.findings
                    ),
                    f"expected a reason demand for the added path, got {result.findings}",
                )
                self.assertTrue(self.plan.is_file(), "the plan must be left unmoved")
                self.assertIn("--scope-reason tests/test_extra.py=", result.message)
                self.tearDown()

    def test_an_empty_reason_for_an_added_path_still_refuses(self):
        """A blank reason is no reason, exactly as for an out-of-scope edit."""
        self._do_the_work_and_widen(commit=False)
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/test_extra.py": "   "},
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertTrue(self.plan.is_file())

    def test_ONE_reason_satisfies_both_demands_in_the_committed_case(self):
        """A widened path that is ALSO out-of-scope must not cost two answers.

        In the committed-cohesive variant the same path appears in BOTH `out_of_scope_paths` (judged
        against the receipt's old fence) and `widened_paths`, so without deduplication the honest
        declaration would demand two reasons where the concealed edit demands none.
        """
        self._do_the_work_and_widen(commit=True)
        rc, _msg, evidence, _f = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(rc, LC.EXIT_OK)
        audit = evidence["scope_audit"]
        self.assertIn("tests/test_extra.py", audit["out_of_scope_paths"])
        self.assertIn("tests/test_extra.py", audit["widened_paths"])

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

    def test_the_uncommitted_added_path_is_NOT_in_out_of_scope(self):
        """THE MEASUREMENT F-9 RESTS ON, pinned so a future refactor cannot quietly undo it.

        `finalize_precheck` judges out-of-scope against the RECEIPT's frozen `scope_paths`, so a path
        added to the plan AFTER begin is measured against the OLD fence and, being merely dirty, is
        DISREGARDED as unowned. This is exactly why the widening demand must be its own.
        """
        self._do_the_work_and_widen(commit=False)
        rc, _msg, evidence, _f = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(rc, LC.EXIT_OK)
        audit = evidence["scope_audit"]
        self.assertEqual(
            audit["out_of_scope_paths"],
            [],
            "if this ever becomes non-empty, the widening demand's independence needs re-deriving",
        )
        self.assertIn("tests/test_extra.py", audit["disregarded_unowned_paths"])
        self.assertEqual(audit["widened_paths"], ["tests/test_extra.py"])

    def test_a_requirement_rewrite_still_refuses_as_STALE_even_with_reasons(self):
        """GUARD-NOT-TOO-LOOSE, end to end: supplying reasons cannot buy a contract rewrite."""
        self._do_the_work_and_widen(commit=True)
        self.plan.write_text(
            self.plan.read_text().replace(
                "- [x] E-01 ", "- [x] E-01 REWRITTEN REQUIREMENT ", 1
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "also rewrite a frozen requirement")
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/test_extra.py": "needed it"},
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", result.message)
        self.assertTrue(
            any("requirement also changed" in f.lower() for f in result.findings),
            f"the refusal should say WHY it is not a widening: {result.findings}",
        )
        self.assertTrue(self.plan.is_file())

    def test_a_removal_refuses_and_NAMES_the_removed_path(self):
        """E-05 end to end: a contract REDUCTION is refused loudly, with the path named."""
        (self.root / "agent_workflows" / "demo.py").write_text("y\n", encoding="utf-8")
        self.plan.write_text(
            self.plan.read_text().replace(
                "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py",
                "- Scope-Paths: agent_workflows/demo.py",
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "narrow the fence after begin")
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", result.message)
        self.assertTrue(
            any("REMOVED" in f and "tests/test_demo.py" in f for f in result.findings),
            f"the removed path must be named: {result.findings}",
        )
        self.assertTrue(self.plan.is_file())

    def test_a_directory_addition_refuses_and_NAMES_the_offending_entry(self):
        """E-08 end to end: a fence-neutering widening must not be accepted with one reason."""
        self._do_the_work_and_widen(commit=True, added="tests/test_extra.py")
        self.plan.write_text(
            self.plan.read_text().replace(", tests/test_extra.py", ", tests/"),
            encoding="utf-8",
        )
        self.assertIn(
            "- Scope-Paths: agent_workflows/demo.py, tests/test_demo.py, tests/",
            self.plan.read_text(),
        )
        _commit_all(self.root, "widen to a whole directory")
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            scope_reasons={"tests/": "I would like the whole tree please"},
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("STALE", result.message)
        self.assertTrue(
            any("tests/" in f and "DIRECTORY or GLOB" in f for f in result.findings),
            f"the offending entry must be named: {result.findings}",
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

    def test_fault_after_index_is_committed_incomplete_not_rolled_back(self):
        """The `after_index` checkpoint is now POST-COMMIT, so it resumes rather than rolls back.

        RENAMED AND RE-ASSERTED (plan `u23gbn` E-07), not weakened. `after_index` fires immediately
        after the fail-loud plans-index refresh, and that refresh moved to AFTER the reconciliation
        (the plan move happens in a coordinator-owned worktree, so refreshing during the mutating phase
        scanned a disk that did not yet reflect the transition and the gate falsely passed). By the time
        this fault fires the lifecycle commit has LANDED, so the honest outcome is
        committed-incomplete: reverting a landed lifecycle commit is exactly what `_resume_post_commit`
        refuses to do. The PRE-commit checkpoints (`before_mutation`, `after_move`, `before_commit`)
        still roll back, which their own tests assert.
        """
        self._begin_and_work()
        result = LC.finalize(
            self.root,
            self.plan,
            "opencode/test",
            "m",
            apply=True,
            fault_injection="after_index",
        )
        self.assertEqual(result.exit_code, LC.EXIT_FINDINGS)
        self.assertIn("COMMITTED-INCOMPLETE", result.message)
        # The commit landed: the plan IS at executed/ and the pending copy is gone.
        self.assertFalse(self.plan.exists())
        self.assertTrue(self._executed_path().is_file())
        journal = LC.read_finalize_journal(self.root, "abc123")
        assert journal is not None
        self.assertEqual(journal["phase"], LC.PHASE_COMMITTED_INCOMPLETE)

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

    def test_the_commit_is_produced_outside_the_shared_checkout(self):
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
            with self.subTest(root=str(root)):
                self.assertNotEqual(root, self.root.resolve())

    def test_an_UNCOMMITTED_plan_edit_still_rides_the_lifecycle_commit(self):
        """BEHAVIOR PRESERVATION, measured on the pre-change code before being relied on.

        A self-executing agent marks its own E/V items and fills evidence, and often has not committed
        those edits when finalize runs. Before this change the transaction edited and committed the
        plan file IN PLACE, so those uncommitted bytes were carried into the lifecycle commit
        (measured). A coordinator worktree snapshots a COMMIT, so the transaction must mirror the
        plan's CURRENT bytes in or it would silently drop the agent's evidence.
        """
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
        assert result.commit is not None
        blob = subprocess.run(
            [
                "git",
                "show",
                f"{result.commit}:.aw/records/plans/executed/{self.plan.name}",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        self.assertIn(
            "UNCOMMITTED EVIDENCE EDIT",
            blob,
            "the executor's uncommitted evidence edits were dropped from the lifecycle commit",
        )

    def test_a_refused_reconciliation_rolls_back_and_is_NOT_committed_incomplete(self):
        """The classification must match reality: an unlanded commit is not "committed".

        In this ordering the ff-only merge IS the branch advance, so a refusal leaves the lifecycle
        commit unreachable from the branch. Calling that `committed-incomplete` would assert a landed
        commit that does not exist.
        """
        self._begin_and_work()
        head = self._head()
        original = self.plan.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT IN FLIGHT, uncommitted\n"
        real_git = LC._git

        def spy_git(root, args):
            # The peer's edit to the plan lands while the worktree is committing, so the ff-only
            # merge would have to overwrite it.
            if (
                args
                and args[0] == "commit"
                and Path(root).resolve() != self.root.resolve()
            ):
                self.plan.write_text(peer_bytes, encoding="utf-8")
            return real_git(root, args)

        with mock.patch.object(LC, "_git", spy_git):
            result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)

        self.assertNotEqual(result.exit_code, LC.EXIT_OK, result.message)
        self.assertIn("would be overwritten", result.message)
        # THE PEER'S BYTES SURVIVE, and the branch never moved.
        self.assertEqual(self.plan.read_text(encoding="utf-8"), peer_bytes)
        self.assertEqual(self._head(), head)
        journal = LC.read_finalize_journal(self.root, "abc123")
        if journal is not None:
            self.assertNotEqual(journal.get("phase"), LC.PHASE_COMMITTED_INCOMPLETE)

    def test_the_edit_release_is_narrow_and_provably_lossless(self):
        """The helper that unblocks OUR OWN edit must refuse every other case, or it is a data hazard.

        It exists only because the shared tree legitimately holds the transaction's own uncommitted
        plan bytes at finalize time. It must therefore write NOTHING when the bytes are not provably
        (a) exactly what this transaction mirrored in and (b) exactly what the landed commit carries.
        """
        self._begin_and_work()
        original = self.plan.read_text(encoding="utf-8")
        peer_bytes = original + "\nPEER EDIT, not ours\n"
        self.plan.write_text(peer_bytes, encoding="utf-8")
        plan_rel = LC._repo_relative(self.root, self.plan)
        dest_rel = plan_rel.replace("/pending/", "/executed/")
        head = self._head()

        cases = {
            # The bytes on disk are NOT what we mirrored in: somebody else's content.
            "foreign bytes": dict(mirrored_bytes=original, committed_bytes=original),
            # We know what we mirrored, but nothing records what the commit carries.
            "no committed bytes": dict(mirrored_bytes=peer_bytes, committed_bytes=None),
            # The commit does not carry these bytes (there is no such commit content at all here).
            "commit does not carry them": dict(
                mirrored_bytes=peer_bytes, committed_bytes=peer_bytes
            ),
        }
        for name, kwargs in cases.items():
            with self.subTest(case=name):
                released = LC._release_own_plan_edit_before_landing(
                    self.root,
                    plan_rel,
                    landed=head,
                    dest_rel=dest_rel,
                    **kwargs,
                )
                self.assertIsNone(released, f"{name}: it must write nothing")
                self.assertEqual(
                    self.plan.read_text(encoding="utf-8"),
                    peer_bytes,
                    f"{name}: the bytes on disk were modified",
                )

    def test_no_coordinator_worktree_or_branch_is_left_behind(self):
        self._begin_and_work()
        result = LC.finalize(self.root, self.plan, "opencode/test", "m", apply=True)
        self.assertEqual(result.exit_code, LC.EXIT_OK, result.message)
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

    def test_the_shared_validator_has_exactly_one_definition(self):
        """E-01: the guard is LIFTED, not copied; two definitions of a valid actor could drift."""
        from agent_workflows import attention_contract as AC

        self.assertIsNone(AC.actor_refusal(self.GOOD))
        self.assertIsNotNone(AC.actor_refusal(self.BAD))
        self.assertIsNotNone(AC.actor_refusal(""))
        self.assertIsNotNone(AC.actor_refusal("   "))
        self.assertIsNotNone(AC.actor_refusal(None))
        # The refusal is operator-facing documentation: it must name the ACCEPTED shape, not merely
        # reject the bad one.
        msg = AC.actor_refusal(self.BAD) or ""
        self.assertIn("key=value", msg)
        self.assertIn("parenthesis", msg)

    def test_no_import_cycle_between_the_writer_and_the_lifecycle(self):
        """E-01's real constraint: `status_set` must reach the helper without a cycle."""
        import subprocess as sp

        r = sp.run(
            [
                "python3",
                "-c",
                "import agent_workflows.status_set, agent_workflows.ipd_lifecycle",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_aw_set_nonterminal_refuses_and_writes_nothing(self):
        """E-07, THE GATE-BREAKING PATH: a NON-terminal transition is where the damage happened."""
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        rc, out = self._run_cli(
            [
                "set",
                "reviewed",
                "abc123",
                "--actor",
                self.BAD,
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertNotEqual(rc, 0, out)
        self.assertIn("parenthesis", out)
        self._assert_nothing_written(before, head)

    def test_aw_ipd_set_refuses_too_since_every_spelling_shares_one_writer(self):
        """The point of guarding the shared writer: no CLI spelling can bypass it."""
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        rc, out = self._run_cli(
            [
                "ipd",
                "set",
                "reviewed",
                "abc123",
                "--actor",
                self.BAD,
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertNotEqual(rc, 0, out)
        self.assertIn("parenthesis", out)
        self._assert_nothing_written(before, head)

    def test_aw_set_executed_refuses_before_the_finalize_transaction(self):
        """E-02: the terminal spelling, which delegates into `finalize`, refuses at the same guard."""
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        rc, out = self._run_cli(
            [
                "set",
                "executed",
                "abc123",
                "--actor",
                self.BAD,
                "--message",
                "m",
                "--yes",
            ]
        )
        self.assertNotEqual(rc, 0, out)
        self.assertIn("parenthesis", out)
        self._assert_nothing_written(before, head)
        self.assertFalse(
            (
                self.root / ".aw" / "records" / "plans" / "executed" / self.plan.name
            ).exists()
        )

    def test_the_writer_itself_raises_as_a_fail_closed_backstop(self):
        """A DIRECT caller of the writer that skipped the CLI pre-flight must still be refused."""
        from agent_workflows import status_set as SS

        rec = SS.read_artifact_record(self.plan, self.root)
        self.assertIsNotNone(rec)
        assert rec is not None
        before, head = self.plan.read_text(encoding="utf-8"), self._head()
        ns = argparse.Namespace(actor=self.BAD, message="m")
        with self.assertRaises(ValueError) as ctx:
            SS.apply_status_change(rec, "reviewed", self.root, ns)
        self.assertIn("parenthesis", str(ctx.exception))
        self._assert_nothing_written(before, head)

    def test_finalize_refuses_the_actor_BEFORE_it_even_checks_the_plan_exists(self):
        """E-02: proof the gate precedes every mutation - it precedes the file-exists check."""
        res = LC.finalize(
            Path("/nonexistent/repo"),
            Path("/nonexistent/repo/p.ipd.md"),
            self.BAD,
            "msg",
            apply=True,
        )
        self.assertEqual(res.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertIn("parenthesis", res.message)
        # Contrast: a VALID actor gets past the actor gate and fails later, on the missing file.
        ok = LC.finalize(
            Path("/nonexistent/repo"),
            Path("/nonexistent/repo/p.ipd.md"),
            self.GOOD,
            "msg",
            apply=True,
        )
        self.assertIn("plan file not found", ok.message)

    def test_finalize_precheck_takes_no_actor_so_it_never_was_a_hole(self):
        """Corrects the plan's original claim of four unguarded finalize paths (its F-4)."""
        import inspect

        self.assertEqual(
            list(inspect.signature(LC.finalize_precheck).parameters),
            ["repo_root", "plan_path"],
        )

    def test_the_slash_form_is_ACCEPTED_so_the_guard_is_not_over_broad(self):
        """A guard that refused every actor would be worse than none.

        Note `aw set --yes` also performs its own path-scoped self-commit of the rewritten artifact
        (`selfcommit jgcm68`), so HEAD legitimately moves here; the property under test is that the
        transition is ACCEPTED and records the actor verbatim.
        """
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

    def test_no_call_site_in_the_package_passes_a_parenthesized_actor(self):
        """F-18: a call site the new guard would refuse is a trap, even when unreachable."""
        import re as _re
        from pathlib import Path as _P

        offenders = []
        for path in sorted(_P("agent_workflows").glob("*.py")):
            for i, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if '"--actor",' in line or "'--actor'," in line:
                    continue
                m = _re.search(r'"--actor",\s*"([^"]*\([^"]*)"', line)
                if m:
                    offenders.append(f"{path}:{i}: {m.group(1)}")
        self.assertEqual(
            offenders, [], f"parenthesized actor literals remain: {offenders}"
        )


class ScaffoldStopsWritingTheShapeItsOwnSetterRefuses(unittest.TestCase):
    """Plan fn2l1u E-05 / V-05, resolving OQ-02: NORMALIZE the author, AND SAY SO.

    `--author` reaches TWO places, not one: the `- Author:` front-matter field and the scaffold's own
    first history line, `- <date> draft (<author>): created.`. A parenthesized author therefore made
    scaffold WRITE an unparseable record into every new plan (F-15), which is worse than merely
    teaching the shape. The maintainer's OQ-02 ruling took a third option over silent normalization:
    normalize, but print one line, so the string the caller typed is not silently replaced.
    """

    BAD = "opencode (its_direct/some-model)"
    WANT = "opencode model=its_direct/some-model"

    def test_the_author_is_normalized_to_the_key_value_shape(self):
        self.assertEqual(A.normalize_author(self.BAD), self.WANT)

    def test_an_author_with_no_parenthesis_is_untouched(self):
        for good in ("opencode/its_direct/some-model", "aw set", "human maintainer"):
            with self.subTest(good=good):
                self.assertEqual(A.normalize_author(good), good)

    def test_BOTH_write_sites_get_the_normalized_author(self):
        """Normalizing only the front matter would leave the history line unparseable."""
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

    def test_the_scaffolded_history_line_actually_PARSES(self):
        """The point of the whole item: a brand-new plan must not be born unparseable."""
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
        line = next(
            ln.strip()
            for ln in text.splitlines()
            if ln.strip().startswith("- 2026-09-09 draft ")
        )
        _d, workflow, actor, message = RH._parse_record_line(line)
        self.assertEqual(workflow, "draft")
        self.assertEqual(actor, self.WANT)
        self.assertEqual(message, "created.")

    def test_the_normalized_author_would_be_ACCEPTED_as_an_actor(self):
        """Closes the loop: the shape scaffold now emits is the shape the setter accepts."""
        from agent_workflows import attention_contract as AC

        self.assertIsNone(AC.actor_refusal(A.normalize_author(self.BAD)))
        self.assertIsNotNone(AC.actor_refusal(self.BAD))

    def test_run_scaffold_PRINTS_that_it_normalized(self):
        """OQ-02 requires a NOTICE; a silent rewrite does not satisfy the item."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        target = root / "20260909-demo-01-aaa111-t.ipd.md"
        args = argparse.Namespace(
            kind=S.KIND_CHILD,
            title="T",
            author=self.BAD,
            set="demo",
            order=1,
            path=str(target),
            apply=True,
            overwrite=False,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.run_scaffold(args)
        out = buf.getvalue()
        self.assertEqual(rc, 0, out)
        self.assertIn("normalized --author", out)
        self.assertIn(self.WANT, out)
        self.assertEqual(
            len([ln for ln in out.splitlines() if "normalized --author" in ln]),
            1,
            "the notice must be ONE line and must not read as an error",
        )
        self.assertNotIn("error", out.lower().split("normalized")[0])

    def test_no_notice_is_printed_when_nothing_changed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        target = root / "20260909-demo-01-aaa112-t.ipd.md"
        args = argparse.Namespace(
            kind=S.KIND_CHILD,
            title="T",
            author="opencode/its_direct/some-model",
            set="demo",
            order=1,
            path=str(target),
            apply=True,
            overwrite=False,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = A.run_scaffold(args)
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertNotIn("normalized", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
