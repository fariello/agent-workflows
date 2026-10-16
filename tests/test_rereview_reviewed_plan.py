"""Tests for re-review of reviewed and approved plans (IPD ggsdrl / backlog dbr23q).

Behavioral tests verifying:
(a) table-driven decide_rereview_admission cases
(b) driver start with --action review --yes --prepare-only freezes action=review, rereview=True, status=queued, plan untouched
(c) driver start with --action review without --yes exits nonzero and leaves no run directory
(d) status sweeps ('reviews', 'all') and reviewed orchestrators keep refusal under --action review
(e) --action execute and default action derive as before
(f) execute_item_core demotes in review lane, turn sees to-review with demotion line, disposition is reviewed
(g) execute_item_core with a no-op turn ends fail-gate
(h) execute_item_core with full_auto set ends reviewed without auto-approve
(i) refusal from a later gate leaves the plan untouched
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    cli,
    oc_runipd,
    run_selection_policy,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    return path


def _write_plan(
    repo: Path,
    *,
    id6: str,
    setid: str = "rereview",
    order: int = 1,
    status: str = "reviewed",
    kind: str = "child",
    readiness: str | None = "go-pending-approval",
) -> Path:
    plan_dir = repo / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    if kind == "orchestrator":
        order = 0
    plan_path = plan_dir / f"20261015-{setid}-{order:02d}-{id6}-test-plan.ipd.md"

    lines = [
        f"# IPD: Test Plan {id6}",
        "",
        "- Date: 2026-10-15",
        f"- Id: {id6}",
        f"- Set: {setid}",
        f"- Order: {order}",
        f"- Status: {status}",
        f"- Kind: {kind}",
        "- Concern: Test concern.",
        "- Scope: Test scope.",
        "- Scope-Paths: none",
        "- Priority: medium",
        "- Work-Kind: feature",
        "- Author: test",
        "- Highest E allocated: 01",
    ]
    if status == "approved":
        lines.append("- Approval: 2026-10-15, approved by human")
    if readiness is not None:
        lines.append(f"- Readiness: {readiness}")
    lines.append("- Item-Dependencies: none")
    lines.append("")
    lines.append("## Workflow history")
    lines.append("")
    if status == "approved":
        lines.append("- 2026-10-15 approved (test): status set to approved")
    if status in ("reviewed", "approved"):
        lines.append("- 2026-10-15 reviewed (test): /plan-review (test): APPROVE")
    lines.append("- 2026-10-15 to-review (test): authored")
    lines.append("- 2026-10-15 draft (test): created")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append("A test goal.")
    lines.append("")
    lines.append("## Detailed Implementation Checklist (TODO)")
    lines.append("")
    lines.append("- [ ] E-01 Test action item")
    lines.append("  - Depends on: none")
    lines.append("  - Expected outcome: done")
    lines.append("  - Execution state: pending")
    lines.append("")

    if kind == "orchestrator":
        lines.extend(
            [
                "## Child IPDs, sequence, and dependencies",
                "",
                "| Order | Id | Status | Plan | Depends on |",
                "|---|---|---|---|---|",
                f"| 01 | chld01 | pending | .aw/records/plans/pending/20261015-{setid}-01-chld01-test.ipd.md | none |",
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
                "  - Required evidence: none",
                "  - Observed evidence:",
                "  - Result: pending",
                "",
                "## Approval and execution gate",
                "",
                "- Size assessment: standard",
                "- Cohesion rationale: not required",
            ]
        )
    else:
        lines.extend(
            [
                "## Project conventions discovered (Step 0)",
                "",
                "- None.",
                "",
                "## Findings",
                "",
                "- None.",
                "",
                "## Proposed changes (ordered, validatable)",
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
                "## Spec / documentation sync",
                "",
                "- None.",
                "",
                "## Open questions",
                "",
                "- None.",
                "",
                "## Validation and cross-check (verify before reporting done)",
                "",
                "- [ ] V-01 validates E-01",
                "  - Required evidence: none",
                "  - Observed evidence:",
                "  - Result: pending",
                "",
                "## Approval and execution gate",
                "",
                "- Size assessment: standard",
                "- Cohesion rationale: not required",
            ]
        )

    plan_path.write_text("\n".join(lines), encoding="utf-8")
    subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", f"add plan {id6}"], cwd=repo, check=True)
    return plan_path


class TestRereviewAdmissionGate(unittest.TestCase):
    """(a) Table-driven unit tests for decide_rereview_admission."""

    def test_rereview_admission_cases(self) -> None:
        candidates = [
            ("rvw001", "reviewed", "child"),
            ("app001", "approved", "child"),
        ]

        # 1. assume_yes admits all candidates
        v1 = run_selection_policy.decide_rereview_admission(
            candidates, interactive=False, assume_yes=True
        )
        self.assertEqual(v1.admitted, ("rvw001", "app001"))
        self.assertEqual(v1.refused, ())
        self.assertFalse(v1.needs_prompt)
        self.assertIsNone(v1.message)

        # 2. Interactive with exact phrase admits all candidates
        v2 = run_selection_policy.decide_rereview_admission(
            candidates,
            interactive=True,
            assume_yes=False,
            response="re-review",
        )
        self.assertEqual(v2.admitted, ("rvw001", "app001"))
        self.assertEqual(v2.refused, ())
        self.assertFalse(v2.needs_prompt)
        self.assertIsNone(v2.message)

        # 3. Interactive with 'y', 'yes', empty, None, or wrong phrase refuses all
        for bad_resp in ("y", "yes", "Y", "", " ", None, "confirm", "re-review please"):
            with self.subTest(response=bad_resp):
                v3 = run_selection_policy.decide_rereview_admission(
                    candidates,
                    interactive=True,
                    assume_yes=False,
                    response=bad_resp,
                )
                self.assertEqual(v3.admitted, ())
                self.assertEqual(v3.refused, ("rvw001", "app001"))
                self.assertIsNotNone(v3.message)
                self.assertIn("rvw001", v3.message)
                self.assertIn("app001", v3.message)
                self.assertIn("--yes", v3.message)
                self.assertIn("re-review", v3.message)
                self.assertIn("approval", v3.message.lower())
                self.assertIn("withdrawn", v3.message.lower())

        # 4. Unattended without yes refuses all
        v4 = run_selection_policy.decide_rereview_admission(
            candidates,
            interactive=False,
            assume_yes=False,
            response=None,
        )
        self.assertEqual(v4.admitted, ())
        self.assertEqual(v4.refused, ("rvw001", "app001"))
        self.assertIsNotNone(v4.message)
        self.assertIn("rvw001", v4.message)
        self.assertIn("app001", v4.message)
        self.assertIn("--yes", v4.message)
        self.assertIn("re-review", v4.message)

        # 5. Empty candidates list produces empty verdict
        v5 = run_selection_policy.decide_rereview_admission(
            [], interactive=False, assume_yes=True
        )
        self.assertEqual(v5.admitted, ())
        self.assertEqual(v5.refused, ())


class TestRereviewQueueBuilder(unittest.TestCase):
    """(b), (c), (d), (e), (i) Queue building, legality, and prepare-only tests."""

    def test_prepare_only_freezes_rereview_and_leaves_plans_byte_identical(
        self,
    ) -> None:
        """(b) start <id6> --action review --yes --prepare-only --unattended."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    p_rvw = _write_plan(repo, id6="rvw001", status="reviewed")
                    p_app = _write_plan(repo, id6="app001", status="approved")
                    rvw_bytes_before = p_rvw.read_bytes()
                    app_bytes_before = p_app.read_bytes()

                    argv = [
                        "start",
                        "rvw001",
                        "app001",
                        "--action",
                        "review",
                        "--yes",
                        "--prepare-only",
                        "--unattended",
                        "--repo",
                        str(repo),
                    ]
                    rc = mod.main(argv)
                    self.assertEqual(rc, 0)

                    # Inspect the state.json created in .aw/records/runs/
                    runs = list((repo / ".aw" / "records" / "runs").glob("run-*"))
                    self.assertEqual(len(runs), 1)
                    state = json.loads(
                        (runs[0] / "state.json").read_text(encoding="utf-8")
                    )
                    queue = state["queue"]
                    self.assertEqual(len(queue), 2)
                    for item in queue:
                        self.assertEqual(item["action"], "review")
                        self.assertTrue(item.get("rereview"))
                        self.assertEqual(item["status"], "queued")
                        self.assertEqual(item["review_handler"], "plan-review")

                    # Plan files MUST be byte-identical before execution
                    self.assertEqual(p_rvw.read_bytes(), rvw_bytes_before)
                    self.assertEqual(p_app.read_bytes(), app_bytes_before)

    def test_unattended_without_yes_refuses_and_creates_no_run_dir(self) -> None:
        """(c) Unattended without --yes exits nonzero and creates no run directory."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(repo, id6="rvw001", status="reviewed")

                    argv = [
                        "start",
                        "rvw001",
                        "--action",
                        "review",
                        "--prepare-only",
                        "--unattended",
                        "--repo",
                        str(repo),
                    ]
                    err_buf = io.StringIO()
                    with contextlib.redirect_stderr(err_buf):
                        rc = mod.main(argv)
                    self.assertNotEqual(rc, 0)
                    self.assertIn("rvw001", err_buf.getvalue())
                    self.assertIn("--yes", err_buf.getvalue())
                    runs_dir = repo / ".aw" / "records" / "runs"
                    if runs_dir.exists():
                        self.assertEqual(list(runs_dir.glob("run-*")), [])

    def test_status_sweeps_and_orchestrators_keep_refusal(self) -> None:
        """(d) reviews/all selectors and reviewed orchestrator keep refusal."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(repo, id6="rvw001", status="reviewed")
                    _write_plan(
                        repo,
                        id6="orc001",
                        status="reviewed",
                        kind="orchestrator",
                        order=0,
                    )

                    # 1. 'reviews' selector under --action review does not re-review reviewed plans
                    err_buf = io.StringIO()
                    with contextlib.redirect_stderr(err_buf):
                        _ = mod.main(
                            [
                                "start",
                                "reviews",
                                "--action",
                                "review",
                                "--yes",
                                "--prepare-only",
                                "--unattended",
                                "--repo",
                                str(repo),
                            ]
                        )
                    # Matching nothing to review exits 0 (healthy state) or skips rvw001
                    runs_dir = repo / ".aw" / "records" / "runs"
                    if runs_dir.exists():
                        for rd in runs_dir.glob("run-*"):
                            st = json.loads(
                                (rd / "state.json").read_text(encoding="utf-8")
                            )
                            q_ids = [it["id6"] for it in st.get("queue", [])]
                            self.assertNotIn("rvw001", q_ids)

                    # 2. Orchestrator named by id6 keeps refusal under --yes
                    err_buf2 = io.StringIO()
                    with contextlib.redirect_stderr(err_buf2):
                        rc2 = mod.main(
                            [
                                "start",
                                "orc001",
                                "--action",
                                "review",
                                "--yes",
                                "--prepare-only",
                                "--unattended",
                                "--repo",
                                str(repo),
                            ]
                        )
                    self.assertNotEqual(rc2, 0)
                    self.assertIn(
                        "is illegal for 1 selected item(s)", err_buf2.getvalue()
                    )

    def test_action_execute_and_default_derive_as_before(self) -> None:
        """(e) --action execute and default action on reviewed/approved plans derive execute."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_plan(repo, id6="app001", status="approved")

                    # default action on approved plan derives execute
                    rc = mod.main(
                        [
                            "start",
                            "app001",
                            "--prepare-only",
                            "--unattended",
                            "--repo",
                            str(repo),
                        ]
                    )
                    self.assertEqual(rc, 0)
                    runs = list((repo / ".aw" / "records" / "runs").glob("run-*"))
                    st = json.loads(
                        (runs[0] / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(st["queue"][0]["action"], "execute")
                    self.assertNotIn("rereview", st["queue"][0])

    def test_refusal_from_later_gate_leaves_plan_unchanged(self) -> None:
        """(i) A refusal from a later gate (unresolvable sibling) leaves plan unchanged."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    p_app = _write_plan(repo, id6="app001", status="approved")
                    app_bytes_before = p_app.read_bytes()

                    # Missing id "nosuch" fails resolution
                    err_buf = io.StringIO()
                    with contextlib.redirect_stderr(err_buf):
                        rc = mod.main(
                            [
                                "start",
                                "app001",
                                "nosuch",
                                "--action",
                                "review",
                                "--yes",
                                "--prepare-only",
                                "--unattended",
                                "--repo",
                                str(repo),
                            ]
                        )
                    self.assertNotEqual(rc, 0)
                    self.assertEqual(p_app.read_bytes(), app_bytes_before)


class TestRereviewExecutionTurn(unittest.TestCase):
    """(f), (g), (h) Driving execute_item_core for a rereview item."""

    def test_execute_item_core_rereview_demotes_and_turn_sees_to_review(self) -> None:
        """(f) Review turn sees demoted to-review plan with demotion line; disposition is reviewed."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="app001", status="approved")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-rereview-f"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "app001",
                "setid": "rereview",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "rereview": True,
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-rereview-f",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "isolate_worktree": False,
                    "full_auto": False,
                },
                "queue": [item],
            }

            seen_plan_text = {}

            def fake_run(st, rd, it, p_rec, prompt_file, att_no, *a, **kw):
                # Check what plan fake_run sees
                curr_plan = Path(st["repo"]) / it["configured_file"]
                text = curr_plan.read_text(encoding="utf-8")
                seen_plan_text["text"] = text

                # Turn updates the plan to reviewed with fresh Readiness
                updated = text.replace("- Status: to-review", "- Status: reviewed")
                updated = updated.replace(
                    "## Workflow history\n",
                    "## Workflow history\n\n- 2026-10-16 reviewed (opencode): /plan-review: APPROVE\n- Readiness: go-pending-approval\n",
                )
                if "- Readiness:" not in updated:
                    updated = updated.replace(
                        "- Status: reviewed\n",
                        "- Status: reviewed\n- Readiness: go-pending-approval\n",
                    )
                curr_plan.write_text(updated, encoding="utf-8")
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # Assert what the turn saw
            self.assertIn("text", seen_plan_text)
            self.assertIn("- Status: to-review", seen_plan_text["text"])
            self.assertNotIn("- Approval:", seen_plan_text["text"])
            self.assertIn("APPROVAL WITHDRAWN", seen_plan_text["text"])
            self.assertIn("re-review requested via oc review", seen_plan_text["text"])

            # Assert disposition
            self.assertEqual(item["status"], "reviewed")

    def test_execute_item_core_rereview_noop_ends_fail_gate(self) -> None:
        """(g) A fake turn that does nothing ends fail-gate."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="app002", status="approved")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-rereview-g"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "app002",
                "setid": "rereview",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "rereview": True,
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-rereview-g",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "isolate_worktree": False,
                    "full_auto": False,
                },
                "queue": [item],
            }

            def fake_noop_run(st, rd, it, p_rec, prompt_file, att_no, *a, **kw):
                # Fake turn does NOT update the plan to reviewed; does nothing
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_noop_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "fail-gate")

    def test_execute_item_core_full_auto_skips_auto_approve(self) -> None:
        """(h) Successful re-review with full_auto set ends reviewed and never auto-approves."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            plan_path = _write_plan(repo, id6="app003", status="approved")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-rereview-h"
            run_dir.mkdir(parents=True)

            item = {
                "position": 1,
                "id6": "app003",
                "setid": "rereview",
                "configured_file": str(plan_path.relative_to(repo)),
                "artifact_type": "ipd",
                "action": "review",
                "rereview": True,
                "status": "queued",
                "review_handler": "plan-review",
                "attempts": [],
            }
            state = {
                "run_id": "run-test-rereview-h",
                "repo": str(repo),
                "options": {
                    "action": "review",
                    "isolate_worktree": False,
                    "full_auto": True,
                },
                "queue": [item],
            }

            def fake_review_run(st, rd, it, p_rec, prompt_file, att_no, *a, **kw):
                curr_plan = Path(st["repo"]) / it["configured_file"]
                text = curr_plan.read_text(encoding="utf-8")
                updated = text.replace("- Status: to-review", "- Status: reviewed")
                updated = updated.replace(
                    "## Workflow history\n",
                    "## Workflow history\n\n- 2026-10-16 reviewed (opencode): /plan-review: APPROVE\n- Readiness: go-pending-approval\n",
                )
                if "- Readiness:" not in updated:
                    updated = updated.replace(
                        "- Status: reviewed\n",
                        "- Status: reviewed\n- Readiness: go-pending-approval\n",
                    )
                curr_plan.write_text(updated, encoding="utf-8")
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_review_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(item["status"], "reviewed")
            self.assertFalse(item.get("auto_approved", False))
            curr_plan = repo / item["configured_file"]
            self.assertIn("- Status: reviewed", curr_plan.read_text(encoding="utf-8"))
            self.assertNotIn(
                "- Status: auto-approved", curr_plan.read_text(encoding="utf-8")
            )


class TestReviewArgvExpansion(unittest.TestCase):
    """Test CLI review argv expansion with --yes flag."""

    def test_expand_host_review_argv_forwards_yes(self) -> None:
        expanded = cli.expand_host_review_argv(["jmogmv", "--yes"])
        self.assertEqual(expanded, ["jmogmv", "--yes", "--action", "review"])


if __name__ == "__main__":
    unittest.main()
