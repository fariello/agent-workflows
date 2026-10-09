"""Tests for orchestrator review readiness with retired children (spec 25kzda 2.5d, IPD 2pv5xd).

Validates:
E-01: review_readiness() routes retired child in child table to CODE_CHILD_TERMINAL.
E-02: CODE_CHILD_TERMINAL finding code, REMEDY_CHILD_TERMINAL remedy, human and agent renderings.
E-03: Child retirement via aw set appends history to orchestrator, commits both, handles skip cases.
E-04: Spec 25kzda Section 2.5d condition 2 amended and conforms.
E-05: Parity and behavioral test suite across modules.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import coverage_record
from agent_workflows import orchestrator_readiness as readiness
from agent_workflows import runner_shared as rs
from tests import support
from tests.test_ipd_lint import _conforming_child, _executed_child


def _init_repo(tmp_dir: Path) -> Path:
    repo = tmp_dir.resolve()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=repo, check=True
    )
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    (repo / ".aw" / "records" / "plans" / "superseded").mkdir(
        parents=True, exist_ok=True
    )
    (repo / ".aw" / "records" / "plans" / "not-executed").mkdir(
        parents=True, exist_ok=True
    )
    return repo


def _make_orchestrator(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "tstset",
    status: str = "to-review",
    child_rows: list[tuple[str, str, str]] | None = None,
    checklist_item: str = "- [ ] E-01 CONFIRM chd001 REACHED executed\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending",
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
    ]
    if status == "approved":
        lines.append("- Approval: 2026-10-04, test approved")
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
            "## Child IPDs, sequence, and dependencies",
            "",
            "| Order | Id | Status | Plan | Depends on |",
            "|---|---|---|---|---|",
        ]
    )
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
    directory: str = "pending",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / directory
    p_dir.mkdir(parents=True, exist_ok=True)
    child_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test.ipd.md"

    if directory == "executed" or status == "executed":
        text = (
            _executed_child()
            .replace("- Set: x", f"- Set: {setid}")
            .replace("- Order: 1", f"- Order: {order}")
            .replace("- Id: abc123", f"- Id: {id6}")
        )
    else:
        text = (
            _conforming_child()
            .replace("- Set: x", f"- Set: {setid}")
            .replace("- Order: 1", f"- Order: {order}")
            .replace("- Id: abc123", f"- Id: {id6}")
            .replace("- Status: to-review", f"- Status: {status}")
        )
    child_path.write_text(text, encoding="utf-8")
    return child_path


class TestOrchestratorChildRetired(unittest.TestCase):
    """Test review readiness and status transitions when children are retired."""

    def test_retired_child_table_row_refused_with_child_terminal_status(self):
        """A retired child (superseded or not-executed) in the child table yields child-terminal-status."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                child_rows=[
                    (
                        "01",
                        "chd001",
                        ".aw/records/plans/not-executed/20261004-tstset-01-chd001-test.ipd.md",
                    )
                ],
            )
            _make_child(
                repo, id6="chd001", status="not-executed", directory="not-executed"
            )
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_TERMINAL, codes)
            f = next(f for f in res.findings if f.code == readiness.CODE_CHILD_TERMINAL)
            self.assertEqual(f.remedy, readiness.REMEDY_CHILD_TERMINAL)
            self.assertEqual(f.subject, "chd001")
            self.assertIn("not-executed", f.detail)

    def test_retired_child_wrong_directory_refused(self):
        """A terminal status in the wrong directory yields child-terminal-status."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                child_rows=[
                    (
                        "01",
                        "chd001",
                        ".aw/records/plans/pending/20261004-tstset-01-chd001-test.ipd.md",
                    )
                ],
            )
            # not-executed under pending/
            _make_child(repo, id6="chd001", status="not-executed", directory="pending")
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_TERMINAL, codes)

        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(
                repo,
                child_rows=[
                    (
                        "01",
                        "chd002",
                        ".aw/records/plans/not-executed/20261004-tstset-01-chd002-test.ipd.md",
                    )
                ],
            )
            # superseded under not-executed/
            _make_child(
                repo, id6="chd002", status="superseded", directory="not-executed"
            )
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            res = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res.ready)
            codes = [f.code for f in res.findings]
            self.assertIn(readiness.CODE_CHILD_TERMINAL, codes)

    def test_renderings_human_and_agent(self):
        """Human and agent renderings correctly present child-terminal-status and remedies."""
        f_term = readiness.Finding(
            code=readiness.CODE_CHILD_TERMINAL,
            subject="chd001",
            detail="child chd001 has status 'not-executed' (terminal or retired child may not remain in '## Child IPDs' table)",
            remedy=readiness.REMEDY_CHILD_TERMINAL,
        )
        r_term = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f_term,),
            id6="orc001",
            setid="tstset",
        )
        human_out = readiness.render_human(r_term, target_status="approved")
        self.assertIn("child-terminal-status", human_out)
        self.assertIn("chd001", human_out)
        self.assertIn(readiness.REMEDY_CHILD_TERMINAL, human_out)

        agent_out = readiness.render_agent(r_term)
        self.assertEqual(agent_out.get("outcome"), "findings")
        self.assertEqual(agent_out.get("exit"), 1)
        data = agent_out.get("data", {})
        self.assertIn("child-terminal-status", data.get("finding_codes", []))
        self.assertEqual(data.get("notes"), [])
        finding_entry = next(
            f
            for f in data.get("findings", [])
            if f.get("code") == "child-terminal-status"
        )
        self.assertEqual(finding_entry.get("remedy"), readiness.REMEDY_CHILD_TERMINAL)

        # Non-terminal draft child still uses child-status-not-ready and REMEDY_CHILD_STATUS
        f_draft = readiness.Finding(
            code=readiness.CODE_CHILD_STATUS,
            subject="chd002",
            detail="child chd002 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)",
            remedy=readiness.REMEDY_CHILD_STATUS,
        )
        r_draft = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f_draft,),
            id6="orc001",
            setid="tstset",
        )
        human_draft = readiness.render_human(r_draft)
        self.assertIn("child-status-not-ready", human_draft)
        self.assertIn(readiness.REMEDY_CHILD_STATUS, human_draft)

    def test_retirement_appends_orchestrator_history_and_commits_both(self):
        """Retiring a child appends a history line to the orchestrator and commits both files."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, id6="orc001", setid="tstset")
            _make_child(repo, id6="chd001", setid="tstset", status="to-review")

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo, check=True
            )

            res = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "chd001",
                "--commit",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(
                res.returncode, 0, f"CLI failed: {res.stderr}\n{res.stdout}"
            )

            # Verify orchestrator workflow history was prepended with child retirement line
            orch_text = orch.read_text(encoding="utf-8")
            self.assertIn("child chd001 retired not-executed", orch_text)
            self.assertIn("same-status", orch_text)

            # Verify git show HEAD lists both files
            show = subprocess.run(
                ["git", "show", "--stat", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("orc001", show.stdout)
            self.assertIn("chd001", show.stdout)

    def test_skip_conditions_no_set_dirty_whole_set(self):
        """Orchestrator history prepend skips cleanly for no-Set, dirty orchestrator, and whole-Set retirement."""
        # 1. Dirty orchestrator
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, id6="orc001", setid="tstset")
            _make_child(repo, id6="chd001", setid="tstset", status="to-review")

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo, check=True
            )

            # Make orchestrator dirty in worktree
            orch.write_text(
                orch.read_text(encoding="utf-8") + "\n<!-- dirty edit -->\n"
            )
            orch_before = orch.read_text(encoding="utf-8")

            res = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "chd001",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("has uncommitted changes", res.stdout + res.stderr)
            # Orchestrator was NOT modified further by the setter
            self.assertEqual(orch.read_text(encoding="utf-8"), orch_before)

        # 2. Whole-Set retirement
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            orch = _make_orchestrator(repo, id6="orc001", setid="tstset")
            _make_child(repo, id6="chd001", setid="tstset", status="to-review")

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo, check=True
            )

            res = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "chd001",
                "orc001",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(res.returncode, 0)
            # Find orchestrator at destination
            dest_orch = repo / ".aw" / "records" / "plans" / "not-executed" / orch.name
            orch_text = dest_orch.read_text(encoding="utf-8")
            # Has its own retirement line, but NOT a "child chd001 retired" line
            self.assertNotIn("child chd001 retired", orch_text)

        # 3. No Set
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            # Standalone plan with no Set
            pending_dir = repo / ".aw" / "records" / "plans" / "pending"
            standalone = pending_dir / "20261004-pl0099-plan.ipd.md"
            standalone.write_text(
                "# IPD: Standalone\n\n- Id: pl0099\n- Date: 2026-10-04\n- Status: to-review\n"
                "- Priority: medium\n- Work-Kind: chore\n- Scope-Paths: none\n- Item-Dependencies: none\n\n"
                "## Workflow history\n\n- 2026-10-04 to-review (test): init\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo, check=True
            )

            res = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "pl0099",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("has no Set", res.stdout + res.stderr)

    def test_agent_mode_next_actions_and_changes(self):
        """Under --agent, stdout is valid JSON with next_actions carrying the remedy hint."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            _make_orchestrator(repo, id6="orc001", setid="tstset")
            _make_child(repo, id6="chd001", setid="tstset", status="to-review")

            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo, check=True
            )

            res = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "chd001",
                "--agent",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(res.returncode, 0)
            payload = json.loads(res.stdout.strip())
            self.assertEqual(payload.get("schema"), "aw.agent/v1")
            self.assertEqual(payload.get("outcome"), "clean")
            self.assertEqual(payload.get("next"), "aw ipd coverage orc001")

            # Check changes carries the orchestrator update
            changes = payload.get("changes", [])
            orch_change = next(
                (c for c in changes if "orc001" in c.get("path", "")), None
            )
            self.assertIsNotNone(orch_change)
            self.assertEqual(orch_change.get("kind"), "update")

        # Check under --json that next_actions carries the full description hint
        with tempfile.TemporaryDirectory() as td2:
            repo2 = _init_repo(Path(td2))
            _make_orchestrator(repo2, id6="orc002", setid="tstset")
            _make_child(repo2, id6="chd002", setid="tstset", status="to-review")

            subprocess.run(["git", "add", "-A"], cwd=repo2, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "initial commit"], cwd=repo2, check=True
            )

            res_json = support.run_cli(
                "ipd",
                "set",
                "not-executed",
                "chd002",
                "--json",
                "--yes",
                "--dir",
                str(repo2),
                cwd=repo2,
            )
            self.assertEqual(res_json.returncode, 0)
            payload_json = json.loads(res_json.stdout.strip())
            next_actions = payload_json.get("next_actions", [])
            self.assertTrue(len(next_actions) > 0)
            cov_na = next(
                (
                    na
                    for na in next_actions
                    if "aw ipd coverage orc002" in na.get("command", "")
                ),
                None,
            )
            self.assertIsNotNone(cov_na)
            self.assertIn("orc002", cov_na.get("description", ""))
            self.assertIn("## Child IPDs", cov_na.get("description", ""))

    def test_runner_continue_handoff_text_carries_new_remedy(self):
        """The runner correction prompt builder re-reads REMEDIES by code and includes REMEDY_CHILD_TERMINAL."""
        f_term = readiness.Finding(
            code=readiness.CODE_CHILD_TERMINAL,
            subject="chd001",
            detail="child chd001 has status 'not-executed'",
            remedy=readiness.REMEDY_CHILD_TERMINAL,
        )
        r_term = readiness.ReviewReadiness(
            applies=True,
            ready=False,
            findings=(f_term,),
            id6="orc001",
            setid="tstset",
        )
        decision = rs.ReviewOrchestratorRetryDecision(
            retry=True,
            exhausted=False,
            reason="ready_findings",
            attempts=0,
            budget=3,
            key="orc001",
        )
        prompt = rs.build_review_orchestrator_correction_prompt(
            {"id6": "orc001"},
            r_term,
            "to-review",
            1,
            decision,
        )
        self.assertIn("child-terminal-status", prompt)
        self.assertIn(
            "remove or reassign the retired child's row in the orchestrator's ## Child IPDs table",
            prompt,
        )
        self.assertIn("aw ipd coverage orc001", prompt)
        self.assertIn("aw ipd set <status> chd001", prompt)
        self.assertIn("do not delete the checklist", prompt)

    def test_orchestrator_ready_after_retired_row_removed(self):
        """Under Option B, removing the retired child's row and updating coverage makes orchestrator ready."""
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            checklist = (
                "- [x] E-01 CONFIRM chd002 REACHED executed\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: performed\n"
                "- [ ] E-02 CONFIRM chd001 REACHED executed\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: pending"
            )
            orch = _make_orchestrator(
                repo,
                id6="orc001",
                setid="tstset",
                child_rows=[
                    (
                        "01",
                        "chd002",
                        ".aw/records/plans/executed/20261004-tstset-01-chd002-test.ipd.md",
                    ),
                    (
                        "02",
                        "chd001",
                        ".aw/records/plans/not-executed/20261004-tstset-02-chd001-test.ipd.md",
                    ),
                ],
                checklist_item=checklist,
            )
            # Update metadata to reflect 02
            orch_text = orch.read_text(encoding="utf-8")
            orch_text = orch_text.replace(
                "- Highest E allocated: 01", "- Highest E allocated: 02"
            )
            orch_text = orch_text.replace(
                "- [ ] V-01 validates E-01\n  - Required evidence: check.\n  - Observed evidence:\n  - Result: pending",
                "- [x] V-01 validates E-01\n  - Required evidence: check.\n  - Observed evidence: pass.\n  - Result: pass\n\n- [ ] V-02 validates E-02\n  - Required evidence: check.\n  - Observed evidence:\n  - Result: pending",
            )
            orch.write_text(orch_text, encoding="utf-8")

            _make_child(
                repo, id6="chd002", order=1, status="executed", directory="executed"
            )
            _make_child(
                repo,
                id6="chd001",
                order=2,
                status="not-executed",
                directory="not-executed",
            )
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            # 1. Unready with retired child row
            res1 = readiness.review_readiness(repo, orch, ask=False)
            self.assertFalse(res1.ready)
            codes = [f.code for f in res1.findings]
            self.assertIn(readiness.CODE_CHILD_TERMINAL, codes)

            # 2. Remove retired child row from table and remove E-02 / V-02 from orchestrator
            text_now = orch.read_text(encoding="utf-8")
            # Remove chd001 row
            text_lines = [
                line for line in text_now.splitlines() if "| 02 | chd001 |" not in line
            ]
            text_clean = "\n".join(text_lines)
            # Remove E-02 checklist item
            e02_block = (
                "- [ ] E-02 CONFIRM chd001 REACHED executed\n"
                "  - Depends on: none\n"
                "  - Expected outcome: done\n"
                "  - Execution state: pending\n"
            )
            text_clean = text_clean.replace(e02_block, "")
            # Remove V-02 item
            v02_block = (
                "\n\n- [ ] V-02 validates E-02\n"
                "  - Required evidence: check.\n"
                "  - Observed evidence:\n"
                "  - Result: pending"
            )
            text_clean = text_clean.replace(v02_block, "")
            text_clean = text_clean.replace(
                "- Highest E allocated: 02", "- Highest E allocated: 01"
            )
            orch.write_text(text_clean, encoding="utf-8")

            # Refresh coverage record pass
            coverage_record.write(orch, "pass", model="fixture", tool="test")

            # 3. Now review readiness passes
            res2 = readiness.review_readiness(repo, orch, ask=False)
            self.assertTrue(res2.ready, [f.detail for f in res2.findings])

            # 4. Status setter can approve the orchestrator
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "ready state"], cwd=repo, check=True
            )
            res_set = support.run_cli(
                "ipd",
                "set",
                "approved",
                "orc001",
                "--yes",
                "--dir",
                str(repo),
                cwd=repo,
            )
            self.assertEqual(
                res_set.returncode,
                0,
                f"Approval failed: {res_set.stderr}\n{res_set.stdout}",
            )


if __name__ == "__main__":
    unittest.main()
