"""Tests for orchestrator status transition gate and backward plan moves (IPD 26m1nb).

Validates:
E-01: Orchestrator readiness gate in run_set_command refusing unready orchestrators.
E-02: Set-wide transition seeing pending child statuses (children first, orchestrator last).
E-03: Backward and draft transitions exempt from the readiness gate.
E-04: Subprocess tests against fixture repos, agent record validity, no-loop case, scaffold draft.
E-05: Non-terminal backward plan moves requiring --message, warnings, and APPROVAL WITHDRAWN.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema, coverage_record
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
    return repo


def _make_orchestrator(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "tstset",
    status: str = "draft",
    child_rows: list[tuple[str, str, str]] | None = None,
    checklist_item: str = "- [ ] E-01 CONFIRM chd001 REACHED executed\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending",
    omit_child_table: bool = False,
    readiness: str | None = None,
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
    ]
    if readiness:
        lines.append(f"- Readiness: {readiness}")
    lines.extend(
        [
            "- Priority: medium",
            "- Work-Kind: chore",
            "- Author: test",
            "- Highest E allocated: 01",
            "- Concern: test concern.",
            "- Scope: test scope.",
            "- Scope-Paths: none",
            "- Item-Dependencies: none",
        ]
    )
    if status == "approved":
        lines.append("- Approval: 2026-10-04, test: approved")
    lines.extend(
        [
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
            checklist_item,
            "",
        ]
    )
    if not omit_child_table:
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
            ]
        )
        for ord_tok, c_id6, c_path in child_rows:
            lines.append(f"| {ord_tok} | {c_id6} | pending | {c_path} | none |")
        lines.append("")

    lines.extend(
        [
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
    broken_lint: bool = False,
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
    if broken_lint:
        text = text.replace("## Goal\n", "")
    child_path.write_text(text, encoding="utf-8")
    return child_path


def _run_cli(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path.cwd())
    cmd = ["python3", "-m", "agent_workflows"] + args + ["--dir", str(repo)]
    return subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, env=env, check=False
    )


class TestOrchestratorStatusGate(unittest.TestCase):
    """Subprocess tests validating the orchestrator status gate."""

    def test_four_forward_targets_refused_for_unready_orchestrator(self):
        """Case 1: each of the four forward targets refused for an unready orchestrator."""
        for target in ("to-review", "reviewed", "approved", "auto-approved"):
            with tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                _make_orchestrator(repo, status="draft")
                # child chd001 is missing on disk
                proc = _run_cli(repo, ["ipd", "set", target, "orc001", "--yes"])
                self.assertEqual(
                    proc.returncode,
                    1,
                    f"Expected exit 1 for target '{target}' but got {proc.returncode}. Output:\n{proc.stdout + proc.stderr}",
                )

    def test_human_output_remedy_and_no_delete_suggestion(self):
        """Case 2: human output contains child id6/quoted passage, remedy command, and does not suggest deleting checklist."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, status="draft")
            # Child is in draft
            _make_child(repo, id6="chd001", status="draft")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            proc = _run_cli(repo, ["ipd", "set", "to-review", "orc001", "--yes"])
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertIn("chd001", combined)
            self.assertIn("Remedy:", combined)
            self.assertIn("aw ipd set to-review", combined)
            self.assertNotIn("delete the checklist", combined.lower())

    def test_agent_record_validation_and_no_absolute_paths(self):
        """Case 3: --agent record validates with validate_agent_record and carries no absolute path."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, status="draft")
            # Coverage is absent
            _make_child(repo, id6="chd001", status="to-review")

            proc = _run_cli(
                repo, ["ipd", "set", "to-review", "orc001", "--agent", "--yes"]
            )
            self.assertEqual(proc.returncode, 1)
            lines = [line for line in proc.stdout.splitlines() if line.strip()]
            self.assertTrue(lines, "Expected JSONL output under --agent")
            payload = json.loads(lines[-1])

            errors = agent_schema.validate_agent_record(payload)
            self.assertEqual(errors, [], f"Agent record failed validation: {errors}")

            # Check no absolute path leaks
            raw_json = json.dumps(payload)
            self.assertIsNone(
                agent_schema._HOME_PATH_RE.search(raw_json),
                f"Absolute home path leaked in agent output: {raw_json}",
            )
            self.assertNotIn(str(td), raw_json)

    def test_nothing_on_disk_changed_after_refusal(self):
        """Case 4: file bytes are unchanged after a refusal."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, status="draft")
            child = _make_child(repo, id6="chd001", status="draft")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            orch_before = orch.read_bytes()
            child_before = child.read_bytes()

            proc = _run_cli(repo, ["ipd", "set", "to-review", "orc001", "--yes"])
            self.assertEqual(proc.returncode, 1)

            self.assertEqual(orch.read_bytes(), orch_before)
            self.assertEqual(child.read_bytes(), child_before)

    def test_dry_run_refuses_before_preview(self):
        """Dry-run on an unready orchestrator refuses with findings instead of previewing."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, status="draft")
            # Child missing
            proc = _run_cli(repo, ["ipd", "set", "to-review", "orc001", "--dry-run"])
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertIn("not ready for review", combined)
            self.assertNotIn("(dry-run)", combined)

    def test_same_status_noop_on_unready_orchestrator_succeeds(self):
        """Same-status no-op write on a not-ready orchestrator is not gated."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, status="draft")
            # draft -> draft is same-status
            proc = _run_cli(repo, ["ipd", "set", "draft", "orc001", "--yes"])
            self.assertEqual(proc.returncode, 0)

    def test_one_command_set_transition_e02_success_and_refuse(self):
        """Case 5: Set-wide transition seeing pending child transitions, children first, orchestrator last."""
        # 1. Success form: children and orchestrator both draft, children valid, coverage pass
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo, id6="orc001", setid="succeedset", status="draft"
            )
            child = _make_child(repo, id6="chd001", setid="succeedset", status="draft")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            proc = _run_cli(repo, ["ipd", "set", "to-review", "succeedset", "--yes"])
            self.assertEqual(
                proc.returncode,
                0,
                f"Expected exit 0 for valid Set-wide transition, got {proc.returncode}. Output:\n{proc.stdout + proc.stderr}",
            )
            self.assertIn("- Status: to-review", child.read_text(encoding="utf-8"))
            self.assertIn("- Status: to-review", orch.read_text(encoding="utf-8"))

        # 2. Refuse form: child fails lint -> writes none
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo, id6="orc001", setid="failsset", status="draft"
            )
            child = _make_child(
                repo, id6="chd001", setid="failsset", status="draft", broken_lint=True
            )
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            orch_before = orch.read_bytes()
            child_before = child.read_bytes()

            proc = _run_cli(repo, ["ipd", "set", "to-review", "failsset", "--yes"])
            self.assertEqual(proc.returncode, 1)
            combined = proc.stdout + proc.stderr
            self.assertIn("chd001", combined)
            self.assertIn("child-lint-failing", combined)
            self.assertEqual(orch.read_bytes(), orch_before)
            self.assertEqual(child.read_bytes(), child_before)

    def test_no_loop_case_oq03(self):
        """Case 6: promote, demote, then a second promotion on unchanged text is refused."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, status="draft")
            _make_child(repo, id6="chd001", status="to-review")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            # 1. Promote to to-review (succeeds)
            p1 = _run_cli(repo, ["ipd", "set", "to-review", "orc001", "--yes"])
            self.assertEqual(p1.returncode, 0)
            self.assertIn("- Status: to-review", orch.read_text(encoding="utf-8"))

            # 2. Review/demote finds uncovered obligation and writes fail verdict; demoted to draft
            coverage_record.write(
                orch,
                "fail",
                quotes=["uncovered obligation"],
                model="fixture",
                tool="test",
            )
            p2 = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "draft",
                    "orc001",
                    "--message",
                    "demoting for uncovered obligation",
                    "--yes",
                ],
            )
            self.assertEqual(p2.returncode, 0)
            self.assertIn("- Status: draft", orch.read_text(encoding="utf-8"))

            # 3. Second promotion on unchanged text: coverage verdict is fail!
            # Demotion loop is prevented by construction: promotion is refused.
            p3 = _run_cli(repo, ["ipd", "set", "to-review", "orc001", "--yes"])
            self.assertEqual(p3.returncode, 1)
            combined = p3.stdout + p3.stderr
            self.assertIn("coverage-fail", combined)
            self.assertIn("uncovered obligation", combined)

    def test_backward_and_draft_moves_exempt_from_readiness_e03(self):
        """Case 7: backward and draft moves succeed on an unready orchestrator."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            # Orchestrator at reviewed, but no coverage record and child missing
            orch = _make_orchestrator(repo, status="reviewed")

            # reviewed -> to-review is a legal backward move with --message
            p1 = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "to-review",
                    "orc001",
                    "--message",
                    "send back for review",
                    "--yes",
                ],
            )
            self.assertEqual(p1.returncode, 0)
            self.assertIn("- Status: to-review", orch.read_text(encoding="utf-8"))

            # to-review -> draft is a legal move to draft with --message
            p2 = _run_cli(
                repo,
                [
                    "ipd",
                    "set",
                    "draft",
                    "orc001",
                    "--message",
                    "rework in draft",
                    "--yes",
                ],
            )
            self.assertEqual(p2.returncode, 0)
            self.assertIn("- Status: draft", orch.read_text(encoding="utf-8"))

    def test_e05_backward_pairs_message_requirement_and_approval_withdrawn(self):
        """Case 8: all backward pairs require --message, warn loudly, record APPROVAL WITHDRAWN, strip Readiness."""
        backward_pairs = [
            ("approved", "reviewed", True),
            ("approved", "to-review", True),
            ("approved", "draft", True),
            ("auto-approved", "reviewed", True),
            ("auto-approved", "to-review", True),
            ("auto-approved", "draft", True),
            ("reviewed", "to-review", False),
            ("reviewed", "draft", False),
            ("to-review", "draft", False),
        ]
        for src, dst, is_approval_withdrawal in backward_pairs:
            with tempfile.TemporaryDirectory() as td:
                repo = _init_repo(Path(td))
                orch = _make_orchestrator(
                    repo,
                    status=src,
                    readiness="go-pending-approval"
                    if src in ("reviewed", "approved")
                    else None,
                )

                # 1. Refused without --message (rc 2)
                p_no_msg = _run_cli(repo, ["ipd", "set", dst, "orc001", "--yes"])
                self.assertEqual(
                    p_no_msg.returncode,
                    2,
                    f"Expected exit 2 for {src} -> {dst} without --message",
                )
                self.assertIn("--message", p_no_msg.stdout + p_no_msg.stderr)

                # 2. Succeeded with --message (rc 0)
                p_msg = _run_cli(
                    repo,
                    [
                        "ipd",
                        "set",
                        dst,
                        "orc001",
                        "--message",
                        "demoting reason",
                        "--yes",
                    ],
                )
                self.assertEqual(
                    p_msg.returncode,
                    0,
                    f"Expected exit 0 for {src} -> {dst} with --message",
                )
                text = orch.read_text(encoding="utf-8")
                self.assertIn(f"- Status: {dst}", text)

                # 3. Warning emitted to stderr
                self.assertIn(f"DEMOTED orc001: {src} -> {dst}:", p_msg.stderr)
                if is_approval_withdrawal:
                    self.assertIn("APPROVAL WITHDRAWN", p_msg.stderr)
                    self.assertIn(
                        f"demoted {src} -> {dst}: APPROVAL WITHDRAWN: demoting reason",
                        text,
                    )
                else:
                    self.assertIn(f"demoted {src} -> {dst}: demoting reason", text)

                # 4. If target is draft or to-review, - Readiness: is stripped
                if dst in ("draft", "to-review"):
                    self.assertNotIn("- Readiness:", text)

        # Terminal reopen still refused
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            p_dir = repo / ".aw" / "records" / "plans" / "executed"
            orch_path = p_dir / "20261004-tstset-00-orc001-test.ipd.md"
            orch_path.write_text(
                "# IPD: Test\n\n- Date: 2026-10-04\n- Kind: orchestrator\n- Id: orc001\n- Set: tstset\n- Order: 0\n- Status: executed\n- Priority: medium\n- Work-Kind: chore\n- Author: test\n- Highest E allocated: 01\n- Concern: x\n- Scope: x\n- Scope-Paths: none\n- Item-Dependencies: none\n\n## Workflow history\n- 2026-10-04 executed (aw ipd finalize): finalized\n\n## Goal\nx\n\n## Detailed Implementation Checklist (TODO)\n- [ ] E-01 x\n  - Depends on: none\n  - Expected outcome: x\n  - Execution state: performed\n\n## Validation and cross-check (verify before reporting the Set complete)\n- [ ] V-01 validates E-01\n  - Required evidence: x\n  - Observed evidence: pass\n  - Result: pass\n\n## Approval and execution gate\n- None.\n",
                encoding="utf-8",
            )
            p_reopen = _run_cli(
                repo,
                ["ipd", "set", "approved", "orc001", "--message", "reopen", "--yes"],
            )
            self.assertEqual(p_reopen.returncode, 2)
            self.assertIn("terminal disposition", p_reopen.stdout + p_reopen.stderr)

    def test_non_orchestrator_child_plan_unaffected(self):
        """Case 9: non-orchestrator child plan is unaffected by the readiness gate."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            child = _make_child(repo, id6="chd001", status="draft")
            # Moves to to-review without needing coverage or child table
            proc = _run_cli(repo, ["ipd", "set", "to-review", "chd001", "--yes"])
            self.assertEqual(proc.returncode, 0)
            self.assertIn("- Status: to-review", child.read_text(encoding="utf-8"))

    def test_generic_setter_and_auto_approved_refusal(self):
        """Case 10: aw set to-review and aw set auto-approved refuse unready orchestrator and name remedy."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, status="draft")
            _make_child(repo, id6="chd001", status="to-review")

            # 1. Generic aw set to-review
            p1 = _run_cli(repo, ["set", "to-review", "orc001", "--yes"])
            self.assertEqual(p1.returncode, 1)
            self.assertIn("coverage-record-absent", p1.stdout + p1.stderr)
            self.assertIn("aw ipd coverage orc001", p1.stdout + p1.stderr)

            # 2. aw set auto-approved
            p2 = _run_cli(
                repo,
                ["set", "auto-approved", "orc001", "--actor", "full-auto", "--yes"],
            )
            self.assertEqual(p2.returncode, 1)
            self.assertIn("coverage-record-absent", p2.stdout + p2.stderr)
            self.assertIn("aw ipd coverage orc001", p2.stdout + p2.stderr)

    def test_scaffold_orchestrator_dry_run_emits_draft(self):
        """Case 11: aw ipd scaffold --kind orchestrator dry-run still emits Status: draft."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path.cwd())
            proc = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "scaffold",
                    "--kind",
                    "orchestrator",
                    "--title",
                    "Scaffold Test",
                    "--set",
                    "tstset",
                    "--order",
                    "0",
                    "--author",
                    "test",
                    "--priority",
                    "medium",
                    "--work-kind",
                    "chore",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("- Status: draft", proc.stdout)


if __name__ == "__main__":
    unittest.main()
