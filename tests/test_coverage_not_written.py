"""Tests for coverage record write behavior and unwritten answer handling (IPD 7kczdo).

Validates:
E-01: Dirty plan write behavior: writes record without committing, reports committed=False with reason.
E-02: review_readiness reports coverage-record-not-written finding when record cannot be written,
      CONDITION_4_CODES includes it, and ReviewReadiness carries write_detail.
E-03: Human and agent output reporting record outcome ("record written and committed",
      "record written, not committed: <reason>", "record NOT written: <reason>"), and exiting 1 on not written.
E-04: In-process CLI driver tests, retirement re-check refusal, and mutation reproduction.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import coverage_record
from agent_workflows import orchestrator_readiness as readiness
from agent_workflows import runner_shared as rs
from agent_workflows.cli import main
from tests.test_ipd_lint import _conforming_child


def _init_fixture_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
    (root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (root / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)


def _create_orchestrator_and_child(
    repo: Path,
    *,
    setid: str = "tstcov",
    orch_id6: str = "orc001",
    chd_id6: str = "chd001",
    child_in_executed: bool = False,
    child_status: str = "to-review",
) -> tuple[Path, Path]:
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    exec_dir = repo / ".aw" / "records" / "plans" / "executed"

    chd_dir = exec_dir if child_in_executed else pending_dir
    chd_path = chd_dir / f"20261007-{setid}-01-{chd_id6}-child.ipd.md"
    chd_text = (
        _conforming_child()
        .replace("- Set: x", f"- Set: {setid}")
        .replace("- Order: 1", "- Order: 1")
        .replace("- Id: abc123", f"- Id: {chd_id6}")
        .replace("- Status: to-review", f"- Status: {child_status}")
    )
    chd_text = chd_text.replace(
        "## Deferred / out of scope (with reason)\n\n- x",
        "## Deferred / out of scope (with reason)\n\n- None\n  - Carrier-Declined: fixture",
    )
    chd_path.write_text(chd_text, encoding="utf-8")

    orch_path = pending_dir / f"20261007-{setid}-00-{orch_id6}-orchestrator.ipd.md"
    orch_lines = [
        f"# IPD: Orchestrator {orch_id6}",
        "",
        "- Date: 2026-10-07",
        "- Kind: orchestrator",
        f"- Id: {orch_id6}",
        f"- Set: {setid}",
        "- Order: 0",
        "- Status: to-review",
        "- Priority: medium",
        "- Work-Kind: chore",
        "- Author: tester",
        "- Highest E allocated: 01",
        "- Concern: fixture.",
        "- Scope: fixture.",
        "- Scope-Paths: none",
        "- Item-Dependencies: none",
        "",
        "## Workflow history",
        "",
        "- 2026-10-07 to-review (tester): created.",
        "",
        "## Goal",
        "",
        "Fixture goal.",
        "",
        "## Detailed Implementation Checklist (TODO)",
        "",
        f"- [ ] E-01 CONFIRM {chd_id6} REACHED executed",
        "  - Depends on: none",
        f"  - Expected outcome: {chd_id6} reads `- Status: executed` on disk.",
        "  - Execution state: pending",
        "",
        "## Child IPDs, sequence, and dependencies",
        "",
        "| Order | Id | Status | Plan | Depends on |",
        "|---|---|---|---|---|",
        f"| 01 | {chd_id6} | {child_status} | {chd_path.relative_to(repo)} | none |",
        "",
        "## Completion criteria (the whole Set is done only when)",
        "",
        "- None.",
        "",
        "## Cross-IPD validation",
        "",
        "- None.",
        "",
        "## Deferred / out of scope (with reason)",
        "",
        "- None",
        "  - Carrier-Declined: fixture",
        "",
        "## Scope check",
        "",
        "- None.",
        "",
        "## Required tests / validation",
        "",
        "- None.",
        "",
        "## Open questions",
        "",
        "- None.",
        "",
        "## Validation and cross-check (verify before reporting the Set complete)",
        "",
        "- [ ] V-01 validates E-01",
        "  - Required evidence: check.",
        "  - Observed evidence:",
        "  - Result: pending",
        "",
        "## Approval and execution gate",
        "",
        "- None.",
    ]
    orch_path.write_text("\n".join(orch_lines) + "\n", encoding="utf-8")
    return orch_path, chd_path


class TestCoverageNotWrittenCli(unittest.TestCase):
    """Test aw ipd coverage in-process across clean, dirty, --no-commit, and unwritten cases (E-01..E-04)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_fixture_repo(self.repo)
        self.orch_path, self.chd_path = _create_orchestrator_and_child(
            self.repo, setid="tstcov", orch_id6="orc001", chd_id6="chd001"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.repo, check=True)
        self.old_cwd = os.getcwd()
        os.chdir(self.repo)

    def tearDown(self) -> None:
        os.chdir(self.old_cwd)
        self._tmp.cleanup()

    def test_clean_committed_plan_written_and_committed(self) -> None:
        """A clean plan probed writes the record, commits it, prints status, and exits 0."""

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        buf = io.StringIO()
        with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
            buf
        ):
            ret = main(["ipd", "coverage", "orc001"])

        output = buf.getvalue()
        self.assertEqual(ret, 0, f"Expected exit 0, got {ret}. Output:\n{output}")
        self.assertIn("Orchestrator orc001 is ready for review.", output)
        self.assertIn("(record written and committed)", output)

        # Plan contains coverage metadata
        plan_text = self.orch_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: pass", plan_text)
        self.assertIn("- Coverage-Fingerprint:", plan_text)

        # Working tree is clean
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertEqual(st.stdout.strip(), "")

    def test_dirty_plan_written_not_committed_human_and_agent(self) -> None:
        """A dirty plan probed writes the record without commit, prints status, and exits 0 (E-01, E-03)."""
        # Introduce uncommitted change
        uncommitted = "\n<!-- author in-flight uncommitted edit -->\n"
        self.orch_path.write_text(
            self.orch_path.read_text(encoding="utf-8") + uncommitted, encoding="utf-8"
        )

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        # 1. Human rendering
        buf = io.StringIO()
        with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
            buf
        ):
            ret = main(["ipd", "coverage", "orc001"])

        output = buf.getvalue()
        self.assertEqual(ret, 0, f"Expected exit 0, got {ret}. Output:\n{output}")
        self.assertIn("Orchestrator orc001 is ready for review.", output)
        self.assertIn("(record written, not committed:", output)
        self.assertIn(
            "already has uncommitted changes; record written without commit", output
        )

        # File has both the uncommitted edit AND the coverage record
        text_now = self.orch_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: pass", text_now)
        self.assertIn("<!-- author in-flight uncommitted edit -->", text_now)

        # Working tree is still dirty
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertTrue(st.stdout.strip().startswith("M "))

        # 2. Agent rendering on dirty plan (reset first so it is probed again)
        # Revert plan back to dirty state without coverage record
        self.orch_path.write_text(
            self.orch_path.read_text(encoding="utf-8").replace("- Coverage: pass\n", "")
        )
        # Clear coverage lines
        lines = [
            line
            for line in self.orch_path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("- Coverage")
        ]
        self.orch_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        buf_agent = io.StringIO()
        with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
            buf_agent
        ):
            ret_agent = main(["ipd", "coverage", "orc001", "--agent"])

        self.assertEqual(ret_agent, 0)
        agent_payload = json.loads(buf_agent.getvalue())
        data = agent_payload.get("data", {})
        self.assertTrue(data.get("ready"))
        self.assertTrue(data.get("written"))
        self.assertFalse(data.get("committed"))
        self.assertIn(
            "already has uncommitted changes; record written without commit",
            data.get("write_detail", ""),
        )

    def test_no_commit_flag_suppresses_commit(self) -> None:
        """--no-commit writes the record without committing and notes commit suppressed (E-03)."""

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        buf = io.StringIO()
        with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
            buf
        ):
            ret = main(["ipd", "coverage", "orc001", "--no-commit"])

        output = buf.getvalue()
        self.assertEqual(ret, 0, f"Expected exit 0, got {ret}. Output:\n{output}")
        self.assertIn("Orchestrator orc001 is ready for review.", output)
        self.assertIn(
            "(record written, not committed: commit suppressed by --no-commit)", output
        )

        plan_text = self.orch_path.read_text(encoding="utf-8")
        self.assertIn("- Coverage: pass", plan_text)
        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.repo,
            capture_output=True,
            text=True,
        )
        self.assertTrue(st.stdout.strip().startswith("M "))

    def test_record_not_written_fails_and_exits_1(self) -> None:
        """When the coverage record cannot be written, exit code is 1 and error is printed (E-03)."""

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        # Mock coverage_record.write to simulate write failure
        write_fail = coverage_record.CoverageWriteResult(
            written=False,
            committed=False,
            detail="simulated write error: permission denied",
        )
        buf = io.StringIO()
        with mock.patch.object(
            rs, "ask_orchestrator_probe", fake_ask
        ), mock.patch.object(
            coverage_record, "write", return_value=write_fail
        ), redirect_stdout(buf):
            ret = main(["ipd", "coverage", "orc001"])

        output = buf.getvalue()
        self.assertEqual(
            ret,
            1,
            f"Expected exit 1 when record not written, got {ret}. Output:\n{output}",
        )
        self.assertIn("Orchestrator orc001 is not ready for review:", output)
        self.assertIn("[coverage-record-not-written]", output)
        self.assertIn(
            "(record NOT written: simulated write error: permission denied)", output
        )

        # Agent form also reports finding and exit 1
        buf_agent = io.StringIO()
        with mock.patch.object(
            rs, "ask_orchestrator_probe", fake_ask
        ), mock.patch.object(
            coverage_record, "write", return_value=write_fail
        ), redirect_stdout(buf_agent):
            ret_agent = main(["ipd", "coverage", "orc001", "--agent"])

        self.assertEqual(ret_agent, 1)
        agent_payload = json.loads(buf_agent.getvalue())
        data = agent_payload.get("data", {})
        self.assertFalse(data.get("ready"))
        self.assertFalse(data.get("written"))
        self.assertIn("coverage-record-not-written", data.get("finding_codes", []))


class TestReviewReadinessUnitAndRetirement(unittest.TestCase):
    """Unit tests for review_readiness findings and retirement-time re-check refusal (E-02, E-04)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        _init_fixture_repo(self.repo)
        self.orch_path, self.chd_path = _create_orchestrator_and_child(
            self.repo,
            setid="tstret",
            orch_id6="orc002",
            chd_id6="chd002",
            child_in_executed=True,
            child_status="executed",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.repo, check=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_review_readiness_unit_not_written_finding(self) -> None:
        """review_readiness(ask=True) produces coverage-record-not-written when written=False (E-02)."""

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        write_fail = coverage_record.CoverageWriteResult(
            written=False, committed=False, detail="disk failure"
        )
        with mock.patch.object(coverage_record, "write", return_value=write_fail):
            res = readiness.review_readiness(
                self.repo, self.orch_path, ask=True, asker=fake_ask
            )

        self.assertFalse(res.ready)
        self.assertFalse(res.written)
        self.assertEqual(res.write_detail, "disk failure")
        codes = [f.code for f in res.findings]
        self.assertIn(readiness.CODE_COVERAGE_NOT_WRITTEN, codes)
        matching = [
            f for f in res.findings if f.code == readiness.CODE_COVERAGE_NOT_WRITTEN
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].detail, "disk failure")
        self.assertEqual(matching[0].remedy, readiness.REMEDY_COVERAGE_NOT_WRITTEN)
        self.assertIn(readiness.CODE_COVERAGE_NOT_WRITTEN, readiness.CONDITION_4_CODES)

    def test_executions_without_quotes_does_not_add_not_written_finding(self) -> None:
        """executions answer without quotes carries coverage-fail and NOT coverage-record-not-written (E-02)."""

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_EXECUTIONS, "unknown-format", ())

        res = readiness.review_readiness(
            self.repo, self.orch_path, ask=True, asker=fake_ask
        )
        self.assertFalse(res.ready)
        codes = [f.code for f in res.findings]
        self.assertIn(readiness.CODE_COVERAGE_FAIL, codes)
        self.assertNotIn(readiness.CODE_COVERAGE_NOT_WRITTEN, codes)

    def test_review_readiness_unit_written_not_committed_is_ready(self) -> None:
        """A written but not committed record returns ready=True, committed=False, and non-empty write_detail (E-02)."""
        # Introduce uncommitted modification
        self.orch_path.write_text(
            self.orch_path.read_text(encoding="utf-8") + "\n<!-- dirty -->\n",
            encoding="utf-8",
        )

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        res = readiness.review_readiness(
            self.repo, self.orch_path, ask=True, asker=fake_ask
        )
        self.assertTrue(res.ready)
        self.assertTrue(res.written)
        self.assertFalse(res.committed)
        self.assertIn(
            "already has uncommitted changes; record written without commit",
            res.write_detail,
        )
        codes = [f.code for f in res.findings]
        self.assertNotIn(readiness.CODE_COVERAGE_NOT_WRITTEN, codes)

    def test_retirement_recheck_refuses_when_coverage_not_written(self) -> None:
        """dispatch_orchestrator_item refuses retirement when review_readiness finds coverage-record-not-written (E-02, E-04)."""
        state = {
            "queue": [
                {
                    "id6": "orc002",
                    "kind": "orchestrator",
                    "setid": "tstret",
                    "status": "approved",
                    "action": "orchestrate",
                    "configured_file": str(self.orch_path),
                },
                {
                    "id6": "chd002",
                    "kind": "child",
                    "setid": "tstret",
                    "status": "executed",
                    "action": "execute",
                    "configured_file": str(self.chd_path),
                },
            ],
            "options": {"model": "test-model"},
        }
        item = state["queue"][0]

        def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
            return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

        write_fail = coverage_record.CoverageWriteResult(
            written=False, committed=False, detail="simulated write failure"
        )
        run_dir = self.repo / ".aw" / "state" / "runs" / "run-test"
        run_dir.mkdir(parents=True, exist_ok=True)
        with mock.patch.object(coverage_record, "write", return_value=write_fail):
            decision = rs.dispatch_orchestrator_item(
                self.repo,
                run_dir,
                state,
                item,
                actor="test-runner",
                terminal_states=rs.TERMINAL_STATES,
                success_states=rs.SUCCESS_STATES,
                host="oc",
                asker=fake_ask,
            )

        self.assertEqual(decision.outcome, rs.ORCH_DISPATCH_TERMINATE)
        self.assertEqual(decision.reason, rs.ORCH_REASON_FINALIZE_REFUSED)
        self.assertIn("retirement re-check refused", decision.detail)
        self.assertIn("simulated write failure", decision.detail)
        self.assertIn(readiness.REMEDY_COVERAGE_NOT_WRITTEN, decision.detail)
