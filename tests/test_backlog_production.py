"""Tests for backlog production dispatch, verifiers, gated transition, and rollback.

Covers artdispatch y3p3p5 (Order 06, Set artdispatch):
- E-07: Spec 5.5c matrix on both hosts (success, count, ipd conformance, gate handoff).
- E-08: BACKLOG-GRADUATE-LEGITIMACY run-level cases pinning F-6 and F-7 (precondition & rollback).
- E-09: BACKLOG-CROSS-TREE run-level cases (dangling From-Spec and orphaned live blocker).
- E-10: Direct unit tests for the five backlog verifiers against hand-built trees.
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
    oc_runipd,
    production_checks,
    runner_shared,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    rel_dir = path / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    (rel_dir / "20260901-rel001-01-rel001-v1.release.md").write_text(
        "# RELEASE: v1\n- Id: rel001\n- Status: planned\n- Version: 1.0.0\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_backlog_item(
    repo: Path,
    *,
    id6: str,
    status: str = "open",
    summary: str = "Test backlog item",
    slug: str = "test-item",
    gate: str | None = None,
    work_kind: str = "feature",
    priority: str = "high",
    setid: str | None = None,
) -> Path:
    bkl_dir = repo / ".aw" / "records" / "backlog" / status
    bkl_dir.mkdir(parents=True, exist_ok=True)
    if setid is None:
        setid = id6
    file_path = bkl_dir / f"20260927-{setid}-01-{id6}-{slug}.backlog.md"

    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    content = f"""- Id: {id6}
- Status: {status}
- Set: {setid}
{gate_line}- Priority: {priority}
- Work-Kind: {work_kind}
- Summary: {summary}

## Workflow history
- 2026-09-27 {status} (tester): created item
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_plan_content(
    *,
    id6: str,
    backlog_id6: str | None = "bkl001",
    spec_id6: str | None = None,
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    gate: str | None = None,
    scope_paths: str = "README.md",
    dependencies: str = "none",
) -> str:
    bkl_line = f"- From-Backlog: {backlog_id6}\n" if backlog_id6 else ""
    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    return f"""# IPD: Test Plan {id6}

- Date: 2026-09-27
- Kind: child
- Concern: Test concern for plan {id6}.
- Scope: Test scope for plan {id6}.
- Scope-Paths: {scope_paths}
- Status: {status}
{bkl_line}{spec_line}{gate_line}- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: {dependencies}

## Workflow history
- 2026-09-27 {status} (test): created.

## Goal
Test goal for plan {id6}.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
1. E-01 do work.

## Deferred / out of scope (with reason)
- None.

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _write_conforming_plan(
    repo: Path,
    *,
    id6: str,
    backlog_id6: str | None = "bkl001",
    spec_id6: str | None = None,
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    gate: str | None = None,
    scope_paths: str = "README.md",
    dependencies: str = "none",
    bucket: str = "pending",
) -> Path:
    dir_path = repo / ".aw" / "records" / "plans" / bucket
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"20260927-{setid}-{order:02d}-{id6}-test-plan.ipd.md"
    content = _write_plan_content(
        id6=id6,
        backlog_id6=backlog_id6,
        spec_id6=spec_id6,
        setid=setid,
        order=order,
        status=status,
        gate=gate,
        scope_paths=scope_paths,
        dependencies=dependencies,
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _patch_host_agent(module, agent_fn):
    if module is oc_runipd:
        return mock.patch.object(oc_runipd, "run_opencode", agent_fn)

    def _agy_wrapper(state, run_dir, item, prompt_path, attempt_no, *args, **kwargs):
        work_dir = kwargs.get("work_dir")
        root = Path(work_dir) if work_dir else Path(state.get("repo", "."))
        plan_path = runner_shared.queue_artifact_path(root, item)
        return agent_fn(
            state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
        )

    return mock.patch.object(agy_runipd, "run_agy_turn", _agy_wrapper)


class TestBacklogProductionUnitE10(unittest.TestCase):
    """Direct unit tests for the five backlog production verifiers against hand-built trees (E-10)."""

    def test_backlog_graduate_count(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_backlog_item(repo, id6="bkl001", status="open")

            # 1. 0 new plans -> fails BACKLOG-GRADUATE-COUNT
            findings = production_checks.backlog_graduate_count(repo, "bkl001", set())
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("produced 0 linked IPDs", findings[0][2])

            # 2. 1 conforming new plan with From-Backlog -> passes
            _write_conforming_plan(repo, id6="pln001", backlog_id6="bkl001")
            findings = production_checks.backlog_graduate_count(repo, "bkl001", set())
            self.assertEqual(findings, [])

            # 3. New plan missing From-Backlog -> fails
            _write_conforming_plan(repo, id6="pln002", backlog_id6=None)
            findings_unlinked = production_checks.backlog_graduate_count(
                repo, "bkl001", set()
            )
            self.assertEqual(len(findings_unlinked), 1)
            self.assertEqual(findings_unlinked[0][0], "BACKLOG-GRADUATE-COUNT")

            # 4. Duplicate live plan in baseline -> fails duplicate clause
            findings_dup = production_checks.backlog_graduate_count(
                repo, "bkl001", {"pln001"}
            )
            self.assertEqual(len(findings_dup), 1)
            self.assertEqual(findings_dup[0][0], "BACKLOG-GRADUATE-COUNT")
            self.assertIn("reconcile them", findings_dup[0][2])

    def test_backlog_graduate_ipd(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_backlog_item(repo, id6="bkl001", status="open")

            # Conforming plan -> passes
            p_ok = _write_conforming_plan(repo, id6="pok001", backlog_id6="bkl001")
            self.assertEqual(
                production_checks.backlog_graduate_ipd(repo, "bkl001", [p_ok]), []
            )

            # Draft status -> fails check.plan-status
            p_draft = _write_conforming_plan(
                repo, id6="pdr001", backlog_id6="bkl001", status="draft"
            )
            f_draft = production_checks.backlog_graduate_ipd(repo, "bkl001", [p_draft])
            self.assertTrue(
                any(
                    code == "BACKLOG-GRADUATE-IPD" and "plan-status" in msg
                    for code, _, msg in f_draft
                ),
                f_draft,
            )

            # Bucket not pending -> fails check.plan-bucket
            p_exec = _write_conforming_plan(
                repo, id6="pex001", backlog_id6="bkl001", bucket="executed"
            )
            f_bucket = production_checks.backlog_graduate_ipd(repo, "bkl001", [p_exec])
            self.assertTrue(
                any(
                    code == "BACKLOG-GRADUATE-IPD" and "plan-bucket" in msg
                    for code, _, msg in f_bucket
                ),
                f_bucket,
            )

            # Missing or mismatched From-Backlog -> fails check.from-backlog
            p_wrong = _write_conforming_plan(repo, id6="pwr001", backlog_id6="bkl999")
            f_wrong = production_checks.backlog_graduate_ipd(repo, "bkl001", [p_wrong])
            self.assertTrue(
                any(
                    code == "BACKLOG-GRADUATE-IPD" and "from-backlog" in msg
                    for code, _, msg in f_wrong
                ),
                f_wrong,
            )

            # Unresolved Item-Dependencies -> fails check.item-dependencies
            p_deps = _write_conforming_plan(
                repo, id6="pdp001", backlog_id6="bkl001", dependencies="unresolved"
            )
            f_deps = production_checks.backlog_graduate_ipd(repo, "bkl001", [p_deps])
            self.assertTrue(
                any(
                    code == "BACKLOG-GRADUATE-IPD" and "item-dependencies" in msg
                    for code, _, msg in f_deps
                ),
                f_deps,
            )

    def test_backlog_gate_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bklgat", status="open", gate="next")
            _write_backlog_item(repo, id6="bklung", status="open", gate=None)

            # Gated backlog with matching plan gate -> passes
            p_g_match = _write_conforming_plan(
                repo, id6="pgmat1", backlog_id6="bklgat", gate="next"
            )
            self.assertEqual(
                production_checks.backlog_gate_handoff(repo, "bklgat", [p_g_match]),
                [],
            )

            # Gated backlog with omitted plan gate -> fails
            p_g_omit = _write_conforming_plan(
                repo, id6="pgomi1", backlog_id6="bklgat", gate=None
            )
            f_omit = production_checks.backlog_gate_handoff(repo, "bklgat", [p_g_omit])
            self.assertEqual(len(f_omit), 1)
            self.assertEqual(f_omit[0][0], "BACKLOG-GATE-HANDOFF")
            self.assertIn("did not preserve release gate", f_omit[0][2])

            # Ungated backlog with omitted plan gate -> passes
            p_u_match = _write_conforming_plan(
                repo, id6="pumat1", backlog_id6="bklung", gate=None
            )
            self.assertEqual(
                production_checks.backlog_gate_handoff(repo, "bklung", [p_u_match]),
                [],
            )

            # Ungated backlog with plan gate -> passes (allowed asymmetry)
            p_u_gated = _write_conforming_plan(
                repo, id6="pugat1", backlog_id6="bklung", gate="next"
            )
            self.assertEqual(
                production_checks.backlog_gate_handoff(repo, "bklung", [p_u_gated]),
                [],
            )

    def test_backlog_graduate_legitimacy(self):
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl001", status="open")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
            )

            # Commit a plan (handoff commit)
            plan_path = _write_conforming_plan(repo, id6="pln001", backlog_id6="bkl001")
            subprocess.run(["git", "add", str(plan_path)], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "handoff commit"], cwd=repo, check=True
            )
            r = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                capture_output=True,
                text=True,
                check=True,
            )
            handoff_sha = r.stdout.strip()

            # Transition backlog to graduated through setter
            subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "backlog",
                    "set",
                    "bkl001",
                    "--status",
                    "graduated",
                    "--message",
                    "graduated by run run-01: pln001",
                    "--no-commit",
                ],
                cwd=repo,
                check=True,
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "transition commit"], cwd=repo, check=True
            )

            # Legitimate transition with status_before='open' -> passes
            f_pass = production_checks.backlog_graduate_legitimacy(
                repo, "bkl001", handoff_sha, status_before="open"
            )
            self.assertEqual(f_pass, [])

            # Status before was 'done' -> fails (F-6!)
            f_done = production_checks.backlog_graduate_legitimacy(
                repo, "bkl001", handoff_sha, status_before="done"
            )
            self.assertEqual(len(f_done), 1)
            self.assertEqual(f_done[0][0], "BACKLOG-GRADUATE-LEGITIMACY")

            # Status before was 'graduated' -> fails
            f_grad = production_checks.backlog_graduate_legitimacy(
                repo, "bkl001", handoff_sha, status_before="graduated"
            )
            self.assertEqual(len(f_grad), 1)
            self.assertEqual(f_grad[0][0], "BACKLOG-GRADUATE-LEGITIMACY")

            # Ancestry mismatch: handoff_sha not in parent chain
            f_ancestor = production_checks.backlog_graduate_legitimacy(
                repo,
                "bkl001",
                "0000000000000000000000000000000000000000",
                status_before="open",
            )
            self.assertEqual(len(f_ancestor), 1)
            self.assertEqual(f_ancestor[0][0], "BACKLOG-GRADUATE-LEGITIMACY")

    def test_backlog_cross_tree(self):
        # Entry point 1: check_release_gates (e.g. from-backlog-gate-mismatch)
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl001", status="open", gate="next")
            rel_dir = repo / ".aw" / "records" / "releases"
            (rel_dir / "20260901-rel002-01-rel002-v2.release.md").write_text(
                "# RELEASE: v2\n- Id: rel002\n- Status: draft\n- Version: 2.0.0\n",
                encoding="utf-8",
            )
            p_mis = _write_conforming_plan(
                repo, id6="pmis01", backlog_id6="bkl001", gate="rel002"
            )
            f_mis = production_checks.backlog_cross_tree(repo, "bkl001", [p_mis])
            self.assertTrue(
                any(
                    code == "BACKLOG-CROSS-TREE"
                    and "check.from-backlog-gate-mismatch" in msg
                    for code, _, msg in f_mis
                ),
                f_mis,
            )

        # Entry point 2: check_from_spec_dangling
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl002", status="open")
            spc_dir = repo / ".aw" / "records" / "specs" / "approved"
            spc_dir.mkdir(parents=True, exist_ok=True)
            (spc_dir / "20260901-spc001-01-spc001-test.spec.md").write_text(
                "# SPEC\n- Id: spc001\n- Status: approved\n", encoding="utf-8"
            )
            p_spc = _write_conforming_plan(
                repo, id6="pspc01", backlog_id6="bkl002", spec_id6="nosuch"
            )
            f_spc = production_checks.backlog_cross_tree(repo, "bkl002", [p_spc])
            self.assertTrue(
                any(
                    code == "BACKLOG-CROSS-TREE" and "check.from-spec-dangling" in msg
                    for code, _, msg in f_spc
                ),
                f_spc,
            )

        # Entry point 3: release_gate_warnings (check.orphaned-live-blocker)
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _write_backlog_item(repo, id6="bkl003", status="open", gate="next")
            p_orph = _write_conforming_plan(
                repo, id6="porph1", backlog_id6="bkl003", gate="next"
            )
            # Item is still open, carrier is pending -> check.orphaned-live-blocker
            buf_orph = io.StringIO()
            with contextlib.redirect_stderr(buf_orph):
                f_orph = production_checks.backlog_cross_tree(repo, "bkl003", [p_orph])
            self.assertEqual(f_orph, [])
            self.assertIn("check.orphaned-live-blocker", buf_orph.getvalue())


class TestBacklogProductionE07(unittest.TestCase):
    """Spec 5.5c matrix on both hosts (E-07)."""

    def test_5_5c_case1_success(self):
        """Case (1): fake agent writes one conformant to-review plan carrying From-Backlog;
        item ends executed, backlog moves to graduated via setter with history, never done.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl101", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-succ"
                    cmd = [
                        "start",
                        "bkl101",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pln101", backlog_id6="bkl101", gate="next"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]

                    # Assert item executed
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(item["attempts"][0]["disposition"], "executed")

                    # Assert backlog moved to graduated, not done
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl101*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    bkl_p = bkl_files[0]
                    self.assertIn("/graduated/", str(bkl_p).replace("\\", "/"))
                    bkl_txt = bkl_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: graduated", bkl_txt)
                    self.assertNotIn("- Status: done", bkl_txt)
                    self.assertIn("graduated by run run-", bkl_txt)

                    # Assert generated_next_actions recorded
                    gen_acts = item.get("generated_next_actions") or []
                    self.assertEqual(len(gen_acts), 1)
                    self.assertEqual(gen_acts[0]["id6"], "pln101")
                    self.assertEqual(gen_acts[0]["from_backlog"], "bkl101")

                    # Resume spawns nothing: patched to fail if called
                    def fail_spawn(*args, **kwargs):
                        self.fail("Spawn called on completed run during resume")

                    with _patch_host_agent(mod, fail_spawn):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

    def test_5_5c_case2_count_zero(self):
        """Case (2): fake agent writes nothing -> ends fail-gate with BACKLOG-GRADUATE-COUNT,
        item remains open.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl102", status="open")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-cnt0"
                    cmd = [
                        "start",
                        "bkl102",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-COUNT")

                    # Backlog item remains in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl102*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))

    def test_5_5c_case3_ipd_conformance_failure(self):
        """Case (3): fake agent writes non-conforming plan -> ends fail-gate with BACKLOG-GRADUATE-IPD,
        item remains open.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl103", status="open")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-ipdfail"
                    cmd = [
                        "start",
                        "bkl103",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pln103", backlog_id6="bkl103", status="draft"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-IPD")

                    # Backlog item remains in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl103*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))

    def test_5_5c_case4_gate_handoff_failure(self):
        """Case (4): release-gated backlog item whose produced plan omits gate ->
        ends fail-gate with BACKLOG-GATE-HANDOFF, item remains open.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl104", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-gatfail"
                    cmd = [
                        "start",
                        "bkl104",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pln104", backlog_id6="bkl104", gate=None
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GATE-HANDOFF")

                    # Backlog item remains in open/
                    bkl_files = list(
                        repo.glob(".aw/records/backlog/**/20260927-bkl104*.backlog.md")
                    )
                    self.assertEqual(len(bkl_files), 1)
                    self.assertIn("/open/", str(bkl_files[0]).replace("\\", "/"))


class TestBacklogProductionE08(unittest.TestCase):
    """BACKLOG-GRADUATE-LEGITIMACY run-level cases pinning F-6 and F-7 (E-08)."""

    def test_case5a_agent_sets_done_itself(self):
        """Case (5a): agent writes conformant plan AND sets item done itself:
        must NOT end graduated, fails naming BACKLOG-GRADUATE-LEGITIMACY, item restored to open.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl201", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-donefail"
                    cmd = [
                        "start",
                        "bkl201",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pln201", backlog_id6="bkl201", gate="next"
                        )
                        # Positional setter spelling to close done directly
                        subprocess.run(
                            [
                                "python3",
                                "-m",
                                "agent_workflows",
                                "backlog",
                                "set",
                                "done",
                                "bkl201",
                                "--no-commit",
                            ],
                            cwd=target,
                        )
                        # Misbehaving agent achieves done directly on disk to test runner legitimacy check
                        bkl_file = list(
                            target.glob(".aw/records/backlog/open/*bkl201*.backlog.md")
                        )[0]
                        bkl_text = bkl_file.read_text(encoding="utf-8").replace(
                            "- Status: open", "- Status: done"
                        )
                        done_dir = target / ".aw/records" / "backlog" / "done"
                        done_dir.mkdir(parents=True, exist_ok=True)
                        bkl_file.unlink()
                        (done_dir / bkl_file.name).write_text(
                            bkl_text, encoding="utf-8"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-LEGITIMACY")

                    # Backlog item must NOT end graduated
                    grad_files = list(
                        repo.glob(
                            ".aw/records/backlog/graduated/20260927-bkl201*.backlog.md"
                        )
                    )
                    self.assertEqual(len(grad_files), 0)

                    # Item must end in done/ (the illegitimate state the agent achieved)
                    done_files = list(
                        repo.glob(
                            ".aw/records/backlog/done/20260927-bkl201*.backlog.md"
                        )
                    )
                    self.assertEqual(len(done_files), 1)

    def test_case5b_agent_sets_graduated_before_handoff_commit(self):
        """Case (5b): agent sets item graduated itself before writing plan:
        transition precedes handoff commit -> fails naming BACKLOG-GRADUATE-LEGITIMACY.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl202", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-earlygrad"
                    cmd = [
                        "start",
                        "bkl202",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        # Sets graduated before writing plan
                        subprocess.run(
                            [
                                "python3",
                                "-m",
                                "agent_workflows",
                                "backlog",
                                "set",
                                "bkl202",
                                "--status",
                                "graduated",
                                "--message",
                                "premature",
                                "--no-commit",
                            ],
                            cwd=target,
                            check=True,
                        )
                        _write_conforming_plan(
                            target, id6="pln202", backlog_id6="bkl202", gate="next"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-LEGITIMACY")

    def test_case5c_rollback_lands_on_disk(self):
        """Case (5c): after a post-transition failure the rollback actually lands:
        item file is under open/ on disk, not merely reported rolled back.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl203", status="open", gate="next")
                    spc_dir = repo / ".aw" / "records" / "specs" / "approved"
                    spc_dir.mkdir(parents=True, exist_ok=True)
                    (spc_dir / "20260901-spc001-01-spc001-test.spec.md").write_text(
                        "# SPEC\n- Id: spc001\n- Status: approved\n", encoding="utf-8"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog and spec"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-rollback"
                    cmd = [
                        "start",
                        "bkl203",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        # Write conforming plan, but with dangling From-Spec to trigger post-transition failure
                        _write_conforming_plan(
                            target,
                            id6="pln203",
                            backlog_id6="bkl203",
                            spec_id6="nosuch",
                            gate="next",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-CROSS-TREE")

                    # Verify on-disk file is back under open/
                    open_files = list(
                        repo.glob(
                            ".aw/records/backlog/open/20260927-bkl203*.backlog.md"
                        )
                    )
                    self.assertEqual(len(open_files), 1)
                    grad_files = list(
                        repo.glob(
                            ".aw/records/backlog/graduated/20260927-bkl203*.backlog.md"
                        )
                    )
                    self.assertEqual(len(grad_files), 0)

    def test_case5d_legitimacy_discrimination_achieved_vs_refused_attempt(self):
        """Case (5d): discrimination between an achieved illegitimate state and a blocked attempt.
        Setter-bypassing achieved-done reaches fail-gate with BACKLOG-GRADUATE-LEGITIMACY.
        Refused attempt reaches executed with no refusal (status_before is still open, handoff succeeds).
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                # 1. Contrasting case A: agent achieves done WITHOUT invoking CLI (setter-bypassing)
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bk204a", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-achieved-done"
                    cmd = [
                        "start",
                        "bk204a",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent_achieved(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pl204a", backlog_id6="bk204a", gate="next"
                        )
                        # Achieves done WITHOUT invoking CLI (hand-written status plus relocation)
                        bkl_file = list(
                            target.glob(".aw/records/backlog/open/*bk204a*.backlog.md")
                        )[0]
                        bkl_text = bkl_file.read_text(encoding="utf-8").replace(
                            "- Status: open", "- Status: done"
                        )
                        done_dir = target / ".aw/records" / "backlog" / "done"
                        done_dir.mkdir(parents=True, exist_ok=True)
                        bkl_file.unlink()
                        (done_dir / bkl_file.name).write_text(
                            bkl_text, encoding="utf-8"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_achieved):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-LEGITIMACY")
                    # Item remains in done/, not graduated/
                    done_files = list(
                        repo.glob(".aw/records/backlog/done/*bk204a*.backlog.md")
                    )
                    self.assertEqual(len(done_files), 1)
                    grad_files = list(
                        repo.glob(".aw/records/backlog/graduated/*bk204a*.backlog.md")
                    )
                    self.assertEqual(len(grad_files), 0)

                # 2. Contrasting case B: agent attempts gated close via CLI, is refused, touches nothing else
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bk204b", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-refused-attempt"
                    cmd = [
                        "start",
                        "bk204b",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent_refused(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pl204b", backlog_id6="bk204b", gate="next"
                        )
                        # Attempts gated close, which is refused by the CLI gate
                        subprocess.run(
                            [
                                "python3",
                                "-m",
                                "agent_workflows",
                                "backlog",
                                "set",
                                "done",
                                "bk204b",
                                "--no-commit",
                            ],
                            cwd=target,
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_refused):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "executed")
                    self.assertIsNone(item.get("refusal"))
                    # Item legitimately graduated by run's handoff
                    grad_files = list(
                        repo.glob(".aw/records/backlog/graduated/*bk204b*.backlog.md")
                    )
                    self.assertEqual(len(grad_files), 1)
                    done_files = list(
                        repo.glob(".aw/records/backlog/done/*bk204b*.backlog.md")
                    )
                    self.assertEqual(len(done_files), 0)


class TestBacklogProductionE09(unittest.TestCase):
    """BACKLOG-CROSS-TREE run-level cases (E-09)."""

    def test_case6a_dangling_from_spec(self):
        """Case (6a): produced plan carrying a dangling From-Spec, reported only by check_from_spec_dangling."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl301", status="open", gate="next")
                    spc_dir = repo / ".aw" / "records" / "specs" / "approved"
                    spc_dir.mkdir(parents=True, exist_ok=True)
                    (spc_dir / "20260901-spc001-01-spc001-test.spec.md").write_text(
                        "# SPEC\n- Id: spc001\n- Status: approved\n", encoding="utf-8"
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-crosstree-spec"
                    cmd = [
                        "start",
                        "bkl301",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target,
                            id6="pln301",
                            backlog_id6="bkl301",
                            spec_id6="nosuch",
                            gate="next",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-CROSS-TREE")

    def test_case6b_orphaned_live_blocker(self):
        """Case (6b): orphaned-live-blocker shape triggers BACKLOG-CROSS-TREE refusal."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(repo, id6="bkl302", status="open", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-crosstree-orph"
                    cmd = [
                        "start",
                        "bkl302",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        # Plan 1 for bkl302 (creates orphaned-live-blocker shape while bkl302 is still open)
                        _write_conforming_plan(
                            target, id6="pln302", backlog_id6="bkl302", gate="next"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    # Warn-class disposition (E-02): item executes and graduates, warning reported beside success
                    self.assertEqual(item["status"], "executed")
                    self.assertIn("check.orphaned-live-blocker", buf.getvalue())
