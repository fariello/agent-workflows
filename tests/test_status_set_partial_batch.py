"""Tests for partial status batch application across setters (IPD f42oxd, Set setbatch).

Covers:
- SKIP branch via --skip-refused (partial batch application, exit 1).
- ASK branch on interactive terminals (prompt [y/N], y=apply rest, n/EOF=refuse).
- REFUSE branch (all-or-nothing default, non-interactive, dry-run, agent/json).
- Per-gate mixed batches for all six converted gates:
  (a) validate_transition_allowed (status.invalid_transition)
  (b) evaluate_blocking_close (check.blocking-item-closed-without-gate)
  (c) evaluate_handoff_ready (check.graduation-incomplete)
  (d) terminal reopen (status.terminal_reopen_refused, exit 2)
  (e) backward move without --message (status.backward_plan_message_required, exit 2)
  (f) orchestrator review readiness (status.orchestrator_not_ready)
- Schema validation under --agent using agent_schema.validate_agent_record.
- Confirmation refusal under --agent/--json retaining --skip-refused in retry command.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema
from tests.test_ipd_lint import _conforming_child


def _init_repo(tmp_dir: Path) -> Path:
    repo = tmp_dir.resolve()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "specs").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "backlog").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "prompts" / "draft").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "prompts" / "active").mkdir(parents=True, exist_ok=True)
    return repo


def _run_cli(
    repo: Path,
    args: list[str],
    input_str: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path.cwd())
    # Strip CI and AW_NONINTERACTIVE so --interactive triggers term.is_interactive()
    env.pop("CI", None)
    env.pop("AW_NONINTERACTIVE", None)
    if extra_env:
        env.update(extra_env)
    cmd = ["python3", "-m", "agent_workflows"] + args + ["--dir", str(repo)]
    return subprocess.run(
        cmd,
        cwd=repo,
        input=input_str,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _make_orchestrator(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "tstset",
    status: str = "draft",
    child_rows: list[tuple[str, str, str]] | None = None,
) -> Path:
    pending_dir = repo / ".aw" / "records" / "plans" / "pending"
    orch_path = pending_dir / f"20261004-{setid}-00-{id6}-test.ipd.md"

    if child_rows is None:
        child_rows = [
            (
                "01",
                "chd001",
                f".aw/records/plans/pending/20261004-{setid}-01-chd001-test.ipd.md",
            )
        ]

    lines = [
        f"# IPD: Orchestrator {id6}",
        "",
        "- Date: 2026-10-04",
        "- Kind: orchestrator",
        f"- Id: {id6}",
        f"- Set: {setid}",
        "- Order: 0",
        f"- Status: {status}",
        "- Priority: medium",
        "- Work-Kind: chore",
        "- Author: test",
        "- Highest E allocated: 01",
        "- Concern: test concern.",
        "- Scope: test scope.",
        "- Scope-Paths: none",
        "- Item-Dependencies: none",
        "",
        "## Workflow history",
        "",
        f"- 2026-10-04 {status} (test): created.",
        "",
        "## Goal",
        "",
        "Test orchestrator goal.",
        "",
        "## Detailed Implementation Checklist (TODO)",
        "",
        "- [ ] E-01 CONFIRM chd001 REACHED executed\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending",
        "",
        "## Child IPDs, sequence, and dependencies",
        "",
        "| Order | Id | Status | Plan | Depends on |",
        "|---|---|---|---|---|",
    ]
    for ord_tok, c_id6, c_path in child_rows:
        lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
    lines.extend(
        [
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
            "- None.",
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
            "## Validation and cross-cross (verify before reporting the Set complete)",
            "",
            "- [ ] V-01 validates E-01\n  - Required evidence: check.\n  - Observed evidence:\n  - Result: pending",
            "",
            "## Approval and execution gate",
            "",
            "- None.",
            "",
        ]
    )
    orch_path.write_text("\n".join(lines), encoding="utf-8")
    return orch_path


def _make_child(
    repo: Path,
    *,
    id6: str = "chd001",
    setid: str = "tstset",
    order: int = 1,
    status: str = "to-review",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    child_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test.ipd.md"

    text = (
        _conforming_child()
        .replace("- Set: x", f"- Set: {setid}")
        .replace("- Order: 1", f"- Order: {order}")
        .replace("- Id: abc123", f"- Id: {id6}")
        .replace("- Status: to-review", f"- Status: {status}")
    )
    child_path.write_text(text, encoding="utf-8")
    return child_path


def _setup_mixed_fixture(repo: Path) -> tuple[Path, Path, Path]:
    """Create mixed fixture: 1 unready orchestrator + 2 ready plans."""
    orch = _make_orchestrator(repo, id6="orc001", setid="setbatch", status="draft")
    # Missing coverage / missing child makes orc001 unready for to-review
    p1 = _make_child(repo, id6="pla001", setid="setbatch", order=1, status="draft")
    p2 = _make_child(repo, id6="pla002", setid="setbatch", order=2, status="draft")
    return orch, p1, p2


class TestStatusSetPartialBatch(unittest.TestCase):
    """Test suite verifying partial status batch application across setters (IPD f42oxd)."""

    def test_case_01_non_interactive_without_flag_refuses_byte_compare(self):
        """Case 1: non-interactive without flag refuses, writes nothing (byte-compare), exit 1."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()
            b_p1 = p1.read_bytes()
            b_p2 = p2.read_bytes()

            proc = _run_cli(
                repo, ["ipd", "set", "to-review", "orc001", "pla001", "pla002", "--yes"]
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not ready for review", proc.stdout + proc.stderr)
            self.assertIn("--skip-refused", proc.stdout + proc.stderr)

            # Assert bytes on disk unchanged
            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertEqual(p1.read_bytes(), b_p1)
            self.assertEqual(p2.read_bytes(), b_p2)

    def test_case_02_skip_refused_applies_passing_and_agent_record_validates(self):
        """Case 2: --skip-refused applies two, skips one, exit 1, both lists in --agent output."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            # Verify unready orchestrator was unchanged on disk
            self.assertEqual(orch.read_bytes(), b_orch)

            # Verify passing plans were applied
            self.assertIn("- Status: to-review", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", p2.read_text(encoding="utf-8"))

            lines = [line for line in proc.stdout.splitlines() if line.strip()]
            self.assertTrue(lines)
            rec = json.loads(lines[-1])

            errs = agent_schema.validate_agent_record(rec)
            self.assertEqual(errs, [], f"Agent record validation failed: {errs}")

            self.assertEqual(rec["outcome"], "findings")
            self.assertEqual(rec["exit"], 1)
            self.assertTrue(rec["verified"])
            self.assertTrue(rec["complete"])
            self.assertTrue(rec.get("applied"))

            data = rec["data"]
            self.assertEqual(len(data["items"]), 2)
            self.assertEqual(len(data["skipped"]), 1)
            self.assertEqual(data["skipped"][0]["id6"], "orc001")
            self.assertEqual(
                data["skipped"][0]["rule"], "status.orchestrator_not_ready"
            )

            diags = rec.get("diagnostics", [])
            self.assertEqual(len(diags), 1)
            self.assertEqual(diags[0]["rule"], "status.orchestrator_not_ready")

    def test_case_03_interactive_answered_yes_applies_two(self):
        """Case 3: --interactive with stdin y\\n applies two passing records."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--interactive",
                ],
                input_str="y\n",
            )
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertIn("Apply the remaining 2 and skip these 1?", combined)
            self.assertIn("Applied 2, skipped 1 (refused):", combined)

            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertIn("- Status: to-review", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", p2.read_text(encoding="utf-8"))

    def test_case_04_interactive_answered_no_and_eof_writes_nothing(self):
        """Case 4: interactive with n\\n and empty stdin writes nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()
            b_p1 = p1.read_bytes()
            b_p2 = p2.read_bytes()

            # Answer 'n'
            proc_no = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--interactive",
                ],
                input_str="n\n",
            )
            self.assertEqual(proc_no.returncode, 1)
            self.assertIn(
                "Apply the remaining 2 and skip these 1?",
                proc_no.stdout + proc_no.stderr,
            )
            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertEqual(p1.read_bytes(), b_p1)
            self.assertEqual(p2.read_bytes(), b_p2)

            # EOF (empty input)
            proc_eof = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--interactive",
                ],
                input_str="",
            )
            self.assertEqual(proc_eof.returncode, 1)
            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertEqual(p1.read_bytes(), b_p1)
            self.assertEqual(p2.read_bytes(), b_p2)

    def test_case_05_agent_interactive_without_flag_never_prompts_and_refuses(self):
        """Case 5: --agent --interactive without flag never prompts and refuses."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()
            b_p1 = p1.read_bytes()
            b_p2 = p2.read_bytes()

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--interactive",
                    "--agent",
                    "--yes",
                ],
                input_str="y\n",
            )
            self.assertEqual(proc.returncode, 1)
            # Ensure no prompt text in stdout
            self.assertNotIn("Apply the remaining", proc.stdout)
            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertEqual(p1.read_bytes(), b_p1)
            self.assertEqual(p2.read_bytes(), b_p2)

    def test_case_06_all_refused_refuses_with_gate_exit_code(self):
        """Case 6: all refused refuses with today's exit code."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, id6="orc001", setid="setbatch", status="draft")
            _make_orchestrator(repo, id6="orc002", setid="setbatch", status="draft")

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "orc002",
                    "--skip-refused",
                    "--yes",
                ],
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not ready for review", proc.stdout + proc.stderr)

    def test_case_07_no_refusals_is_unchanged_exit_0(self):
        """Case 7: no refusals is unchanged (exit 0)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p1 = _make_child(
                repo, id6="pla001", setid="setbatch", order=1, status="draft"
            )
            p2 = _make_child(
                repo, id6="pla002", setid="setbatch", order=2, status="draft"
            )

            proc = _run_cli(
                repo, ["ipd", "set", "to-review", "pla001", "pla002", "--yes"]
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("- Status: to-review", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", p2.read_text(encoding="utf-8"))

    def test_case_08_yes_alone_does_not_skip(self):
        """Case 8: --yes alone does not skip."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _orch, p1, _p2 = _setup_mixed_fixture(repo)

            b_p1 = p1.read_bytes()
            proc = _run_cli(
                repo, ["ipd", "set", "to-review", "orc001", "pla001", "pla002", "--yes"]
            )
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(p1.read_bytes(), b_p1)

    def test_case_09_dry_run_skip_refused_previews_and_writes_nothing(self):
        """Case 9: --dry-run --skip-refused previews two, lists skipped, writes nothing."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch, p1, p2 = _setup_mixed_fixture(repo)

            b_orch = orch.read_bytes()
            b_p1 = p1.read_bytes()
            b_p2 = p2.read_bytes()

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--dry-run",
                    "--skip-refused",
                ],
            )
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertIn("Applied 2, skipped 1 (refused):", combined)
            self.assertIn("orc001", combined)

            self.assertEqual(orch.read_bytes(), b_orch)
            self.assertEqual(p1.read_bytes(), b_p1)
            self.assertEqual(p2.read_bytes(), b_p2)

    def test_case_10_terminal_reopen_only_batch_exits_2(self):
        """Case 10: a terminal-reopen-only batch still exits 2."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p_dir = repo / ".aw" / "records" / "plans" / "executed"
            plan = p_dir / "20261004-tstset-01-ex0001-test.ipd.md"
            plan.write_text(
                _conforming_child()
                .replace(
                    "- Status: to-review", "- Status: executed\n- Disposition: executed"
                )
                .replace("- Id: abc123", "- Id: ex0001"),
                encoding="utf-8",
            )

            proc = _run_cli(repo, ["ipd", "set", "to-review", "ex0001", "--yes"])
            self.assertEqual(proc.returncode, 2)
            self.assertIn(
                "Refusing to move 1 plan(s) out of a terminal disposition",
                proc.stdout + proc.stderr,
            )

    def test_case_11_gate_a_invalid_transition_mixed_batch(self):
        """Gate (a): validate_transition_allowed lands in data.skipped with status.invalid_transition."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p1 = _make_child(
                repo, id6="pla001", setid="setbatch", order=1, status="draft"
            )
            prompt_file = (
                repo
                / ".aw"
                / "records"
                / "prompts"
                / "draft"
                / "20261004-prm001-test.prompt.md"
            )
            prompt_file.write_text(
                "# Prompt\n\n- Id: prm001\n- Status: draft\n\n## Goal\nTest\n",
                encoding="utf-8",
            )

            # Target status 'reviewed' is legal for plans but invalid for prompts
            proc = _run_cli(
                repo,
                [
                    "set",
                    "reviewed",
                    "pla001",
                    "prm001",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            self.assertIn("- Status: reviewed", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: draft", prompt_file.read_text(encoding="utf-8"))

            rec = json.loads(
                [line for line in proc.stdout.splitlines() if line.strip()][-1]
            )
            self.assertEqual(
                rec["data"]["skipped"][0]["rule"], "status.invalid_transition"
            )

    def test_case_12_gate_b_blocking_close_mixed_batch(self):
        """Gate (b): evaluate_blocking_close lands in data.skipped."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            b_dir = repo / ".aw" / "records" / "backlog"
            # Item 1: High priority + blocks-release, no evidence -> illegitimate close
            b1 = b_dir / "20261004-bkl001-item1.backlog.md"
            b1.write_text(
                "# Item 1\n\n- Id: bkl001\n- Status: open\n- Priority: high\n- Work-Kind: bug\n- Blocks-Release: yes\n- Author: test\n\n## Summary\nx\n",
                encoding="utf-8",
            )
            # Item 2: Low priority, un-gated (no blocks-release line) -> legitimate close
            b2 = b_dir / "20261004-bkl002-item2.backlog.md"
            b2.write_text(
                "# Item 2\n\n- Id: bkl002\n- Status: open\n- Priority: low\n- Work-Kind: chore\n- Author: test\n\n## Summary\nx\n",
                encoding="utf-8",
            )

            proc = _run_cli(
                repo,
                [
                    "backlog",
                    "set",
                    "done",
                    "bkl001",
                    "bkl002",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            # bkl001 skipped (still open), bkl002 applied (done)
            self.assertIn("- Status: open", b1.read_text(encoding="utf-8"))
            b2_done = repo / ".aw" / "records" / "backlog" / "done" / b2.name
            target_b2 = b2_done if b2_done.exists() else b2
            self.assertIn("- Status: done", target_b2.read_text(encoding="utf-8"))

            rec = json.loads(
                [line for line in proc.stdout.splitlines() if line.strip()][-1]
            )
            self.assertTrue(rec["data"]["skipped"][0]["rule"].startswith("check."))

    def test_case_13_gate_c_handoff_ready_mixed_batch(self):
        """Gate (c): evaluate_handoff_ready lands in data.skipped with check.graduation-incomplete."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            b_dir = repo / ".aw" / "records" / "backlog"
            # bkl001: no plan authored -> graduation not ready
            b1 = b_dir / "20261004-bkl001-item1.backlog.md"
            b1.write_text(
                "# Item 1\n\n- Id: bkl001\n- Status: open\n- Priority: medium\n- Work-Kind: feature\n- Author: test\n\n## Summary\nx\n",
                encoding="utf-8",
            )
            # bkl002: has conforming to-review plan -> graduation ready
            b2 = b_dir / "20261004-bkl002-item2.backlog.md"
            b2.write_text(
                "# Item 2\n\n- Id: bkl002\n- Status: open\n- Priority: medium\n- Work-Kind: feature\n- Author: test\n\n## Summary\nx\n",
                encoding="utf-8",
            )
            p2 = _make_child(
                repo, id6="pla002", setid="setbatch", order=2, status="to-review"
            )
            p2_text = p2.read_text(encoding="utf-8").replace(
                "- Id: pla002", "- Id: pla002\n- From-Backlog: bkl002"
            )
            p2.write_text(p2_text, encoding="utf-8")

            proc = _run_cli(
                repo,
                [
                    "backlog",
                    "set",
                    "graduated",
                    "bkl001",
                    "bkl002",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            self.assertIn("- Status: open", b1.read_text(encoding="utf-8"))
            b2_grad = repo / ".aw" / "records" / "backlog" / "graduated" / b2.name
            target_b2 = b2_grad if b2_grad.exists() else b2
            self.assertIn("- Status: graduated", target_b2.read_text(encoding="utf-8"))

            rec = json.loads(
                [line for line in proc.stdout.splitlines() if line.strip()][-1]
            )
            self.assertEqual(
                rec["data"]["skipped"][0]["rule"], "check.graduation-incomplete"
            )

    def test_case_14_gate_d_terminal_reopen_mixed_batch(self):
        """Gate (d): terminal reopen lands in data.skipped with status.terminal_reopen_refused."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p_dir = repo / ".aw" / "records" / "plans" / "executed"
            p1 = p_dir / "20261004-tstset-01-ex0001-test.ipd.md"
            p1.write_text(
                _conforming_child()
                .replace(
                    "- Status: to-review", "- Status: executed\n- Disposition: executed"
                )
                .replace("- Id: abc123", "- Id: ex0001"),
                encoding="utf-8",
            )
            p2 = _make_child(
                repo, id6="pla002", setid="setbatch", order=2, status="draft"
            )

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "ex0001",
                    "pla002",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            # ex0001 skipped (still executed), pla002 applied (to-review)
            self.assertIn("- Status: executed", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", p2.read_text(encoding="utf-8"))

            rec = json.loads(
                [line for line in proc.stdout.splitlines() if line.strip()][-1]
            )
            self.assertEqual(
                rec["data"]["skipped"][0]["rule"], "status.terminal_reopen_refused"
            )

    def test_case_15_gate_e_backward_plan_message_required_mixed_batch(self):
        """Gate (e): backward move without --message lands in data.skipped with status.backward_plan_message_required."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            # p1 is reviewed demoting to to-review (requires --message)
            p1 = _make_child(
                repo, id6="pla001", setid="setbatch", order=1, status="reviewed"
            )
            # p2 is draft advancing to to-review (forward, no message required)
            p2 = _make_child(
                repo, id6="pla002", setid="setbatch", order=2, status="draft"
            )

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "pla001",
                    "pla002",
                    "--skip-refused",
                    "--yes",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 1)

            self.assertIn("- Status: reviewed", p1.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", p2.read_text(encoding="utf-8"))

            rec = json.loads(
                [line for line in proc.stdout.splitlines() if line.strip()][-1]
            )
            self.assertEqual(
                rec["data"]["skipped"][0]["rule"],
                "status.backward_plan_message_required",
            )

    def test_case_16_agent_confirmation_refusal_retains_skip_refused_flag(self):
        """Confirmation refusal under --agent --skip-refused without --yes exits 2 and retains --skip-refused."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _setup_mixed_fixture(repo)

            proc = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "pla001",
                    "pla002",
                    "--skip-refused",
                    "--agent",
                ],
            )
            self.assertEqual(proc.returncode, 2)
            lines = [line for line in proc.stdout.splitlines() if line.strip()]
            self.assertTrue(lines)
            rec = json.loads(lines[-1])

            self.assertEqual(rec["outcome"], "cannot-run")
            self.assertEqual(rec["exit"], 2)
            # next action command must carry --skip-refused and --yes
            next_cmd = rec.get("next") or ""
            self.assertIn("--skip-refused", next_cmd)
            self.assertIn("--yes", next_cmd)

            # diagnostics has the skipped orchestrator
            diags = rec.get("diagnostics", [])
            self.assertTrue(
                any(d.get("rule") == "status.orchestrator_not_ready" for d in diags)
            )


if __name__ == "__main__":
    unittest.main()
