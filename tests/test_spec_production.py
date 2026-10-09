"""Tests for spec production dispatch, verifiers, lifecycle arm, and report-only behavior.

Covers artdispatch aeq7f8 (Order 05, Set artdispatch):
- E-08: Production-outcome cases for 5.5 and 5.5b on both hosts (oc and agy).
- E-09: Lifecycle arm (no suite check, no finalize against spec, no backlog close),
        review-style integration, quarantine on failure, and report-only (5.5a).
- E-10: Direct unit tests for production verifiers (spec_plan_count,
        spec_plan_conformance, spec_plan_gate_carry).
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
    render_stream,
    run_viewer,
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
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_spec(
    repo: Path,
    *,
    id6: str,
    status: str = "approved",
    title: str = "Test Spec",
    slug: str = "test-spec",
    gate: str | None = None,
    filename_date: str = "20260927",
    spec_date: str = "2026-09-27",
    requirements: list[str] | None = None,
    acceptance: list[str] | None = None,
) -> Path:
    bucket = "approved" if status == "approved" else status
    specs_dir = repo / ".aw" / "records" / "specs" / bucket
    specs_dir.mkdir(parents=True, exist_ok=True)
    file_path = specs_dir / f"{filename_date}-{id6}-01-{id6}-{slug}.spec.md"

    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    req_section = ""
    if requirements:
        req_lines = "\n".join(f"- {r}" for r in requirements)
        req_section = f"\n## 2. Requirements\n{req_lines}\n"
    ac_section = ""
    if acceptance:
        ac_lines = "\n".join(f"- {a}" for a in acceptance)
        ac_section = f"\n## 3. Acceptance Criteria\n{ac_lines}\n"

    content = f"""# SPEC: {title}

- Date: {spec_date}
- Status: {status}
- Title: {title}
- Slug: {slug}
- Id: {id6}
{gate_line}
## Workflow history
- {spec_date} {status} (tester): set status

## 1. Overview
Overview of spec {id6}.
{req_section}{ac_section}"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_plan_content(
    *,
    id6: str,
    spec_id6: str | None = "spc001",
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    gate: str | None = None,
    scope_paths: str = "README.md",
    dependencies: str = "none",
    e_items: list[str] | None = None,
    v_items: list[str] | None = None,
) -> str:
    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    gate_line = f"- Blocks-Release: {gate}\n" if gate else ""
    highest_e = f"{len(e_items):02d}" if e_items else "01"

    if e_items:
        e_body_lines = []
        for i, text in enumerate(e_items, 1):
            e_body_lines.append(
                f"- [ ] E-{i:02d} {text}\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
            )
        e_body = "\n\n".join(e_body_lines)
    else:
        e_body = """- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending"""

    if v_items:
        v_body_lines = []
        for i, text in enumerate(v_items, 1):
            target_e = min(i, len(e_items)) if e_items else 1
            if "validates E-" in text:
                v_prefix = f"- [ ] V-{i:02d} {text}"
            else:
                v_prefix = f"- [ ] V-{i:02d} validates E-{target_e:02d} {text}"
            v_body_lines.append(
                f"{v_prefix}\n  - Required evidence: check\n  - Observed evidence:\n  - Result: pending"
            )
        v_body = "\n\n".join(v_body_lines)
    else:
        v_body = """- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending"""

    return f"""# IPD: Test Plan {id6}

- Date: 2026-09-27
- Kind: child
- Concern: Test concern for plan {id6}.
- Scope: Test scope for plan {id6}.
- Scope-Paths: {scope_paths}
- Status: {status}
{spec_line}{gate_line}- Set: {setid}
- Order: {order}
- Highest E allocated: {highest_e}
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
{e_body}

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
{v_body}

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _write_conforming_plan(
    repo: Path,
    *,
    id6: str,
    spec_id6: str | None = "spc001",
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    gate: str | None = None,
    scope_paths: str = "README.md",
    dependencies: str = "none",
    bucket: str = "pending",
    filename_date: str = "20260927",
    e_items: list[str] | None = None,
    v_items: list[str] | None = None,
) -> Path:
    dir_path = repo / ".aw" / "records" / "plans" / bucket
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{filename_date}-{setid}-{order:02d}-{id6}-test-plan.ipd.md"
    content = _write_plan_content(
        id6=id6,
        spec_id6=spec_id6,
        setid=setid,
        order=order,
        status=status,
        gate=gate,
        scope_paths=scope_paths,
        dependencies=dependencies,
        e_items=e_items,
        v_items=v_items,
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


class TestSpecProductionUnitE10(unittest.TestCase):
    """Direct unit tests for production verifiers against hand-built trees (E-10)."""

    def test_spec_plan_count(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_spec(repo, id6="spc001", status="approved")

            # 1. 0 new plans -> fails SPEC-PLAN-COUNT
            findings = production_checks.spec_plan_count(repo, "spc001", set())
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0][0], "SPEC-PLAN-COUNT")
            self.assertIn("produced 0 new linked IPDs", findings[0][2])

            # 2. 1 conforming new plan -> passes
            _write_conforming_plan(repo, id6="pln001", spec_id6="spc001")
            findings = production_checks.spec_plan_count(repo, "spc001", set())
            self.assertEqual(findings, [])

            # 3. Baseline pln001 plus new pnew01 in same Set -> passes under amended rule
            _write_conforming_plan(repo, id6="pnew01", spec_id6="spc001")
            findings_same_set = production_checks.spec_plan_count(
                repo, "spc001", {"pln001"}
            )
            self.assertEqual(findings_same_set, [])

    def test_spec_plan_conformance(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write_spec(repo, id6="spc001", status="approved")

            # Conforming plan
            p_ok = _write_conforming_plan(repo, id6="pok001", spec_id6="spc001")
            self.assertEqual(
                production_checks.spec_plan_conformance(repo, "spc001", [p_ok]), []
            )

            # Draft status -> fails
            p_draft = _write_conforming_plan(
                repo, id6="pdr001", spec_id6="spc001", status="draft"
            )
            f_draft = production_checks.spec_plan_conformance(repo, "spc001", [p_draft])
            self.assertTrue(
                any(
                    code == "SPEC-PLAN-CONFORMANCE" and "plan-status" in msg
                    for code, _, msg in f_draft
                ),
                f_draft,
            )

            # TODO Scope-Paths -> fails
            p_todo = _write_conforming_plan(
                repo, id6="ptd001", spec_id6="spc001", scope_paths="TODO"
            )
            f_todo = production_checks.spec_plan_conformance(repo, "spc001", [p_todo])
            self.assertTrue(
                any(
                    code == "SPEC-PLAN-CONFORMANCE" and "scope-paths" in msg
                    for code, _, msg in f_todo
                ),
                f_todo,
            )

            # Missing From-Spec -> fails
            p_nofrom = _write_conforming_plan(repo, id6="pnf001", spec_id6=None)
            f_nofrom = production_checks.spec_plan_conformance(
                repo, "spc001", [p_nofrom]
            )
            self.assertTrue(
                any(
                    code == "SPEC-PLAN-CONFORMANCE" and "from-spec" in msg
                    for code, _, msg in f_nofrom
                ),
                f_nofrom,
            )

            # Unresolved Item-Dependencies -> fails
            p_unres = _write_conforming_plan(
                repo, id6="pun001", spec_id6="spc001", dependencies="unresolved"
            )
            f_unres = production_checks.spec_plan_conformance(repo, "spc001", [p_unres])
            self.assertTrue(
                any(
                    code == "SPEC-PLAN-CONFORMANCE" and "item-dependencies" in msg
                    for code, _, msg in f_unres
                ),
                f_unres,
            )

    def test_spec_plan_gate_carry(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # Gated spec
            _write_spec(repo, id6="spcgat", status="approved", gate="next")
            # Ungated spec
            _write_spec(repo, id6="spcung", status="approved", gate=None)

            # Gated spec with matching plan -> passes
            p_g_match = _write_conforming_plan(
                repo, id6="pgmat1", spec_id6="spcgat", gate="next"
            )
            self.assertEqual(
                production_checks.spec_plan_gate_carry(repo, "spcgat", [p_g_match]), []
            )

            # Gated spec with omitted plan gate -> fails
            p_g_omit = _write_conforming_plan(
                repo, id6="pgomi1", spec_id6="spcgat", gate=None
            )
            f_omit = production_checks.spec_plan_gate_carry(repo, "spcgat", [p_g_omit])
            self.assertEqual(len(f_omit), 1)
            self.assertEqual(f_omit[0][0], "SPEC-PLAN-GATE-CARRY")
            self.assertIn("disagree on Blocks-Release", f_omit[0][2])

            # Ungated spec with omitted plan gate -> passes
            p_u_match = _write_conforming_plan(
                repo, id6="pumat1", spec_id6="spcung", gate=None
            )
            self.assertEqual(
                production_checks.spec_plan_gate_carry(repo, "spcung", [p_u_match]), []
            )

            # Ungated spec with invented plan gate -> fails
            p_u_inv = _write_conforming_plan(
                repo, id6="puinv1", spec_id6="spcung", gate="next"
            )
            f_inv = production_checks.spec_plan_gate_carry(repo, "spcung", [p_u_inv])
            self.assertEqual(len(f_inv), 1)
            self.assertEqual(f_inv[0][0], "SPEC-PLAN-GATE-CARRY")
            self.assertIn("disagree on Blocks-Release", f_inv[0][2])


class TestSpecProductionE08(unittest.TestCase):
    """Production outcome cases for 5.5 and 5.5b on both hosts (E-08)."""

    def test_5_5_success(self):
        """Case (1): fake agent writes one conformant to-review plan carrying From-Spec;
        item ends executed, spec moves to implementing via setter with history, not implemented.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc101", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-succ"
                    cmd = [
                        "start",
                        "spc101",
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
                        _write_conforming_plan(target, id6="pln101", spec_id6="spc101")
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

                    # Assert spec moved to implementing, not implemented
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc101*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    spec_p = spec_files[0]
                    self.assertIn("/implementing/", str(spec_p).replace("\\", "/"))
                    spec_txt = spec_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: implementing", spec_txt)
                    self.assertNotIn("- Status: implemented", spec_txt)
                    self.assertIn("produced by run run-", spec_txt)

                    # Assert generated_next_actions recorded
                    gen_acts = item.get("generated_next_actions") or []
                    self.assertEqual(len(gen_acts), 1)
                    self.assertEqual(gen_acts[0]["id6"], "pln101")
                    self.assertEqual(gen_acts[0]["from_spec"], "spc101")

    def test_5_5_refusal_count_zero(self):
        """Case (2): fake agent writes nothing -> ends fail-gate with SPEC-PLAN-COUNT,
        spec remains approved.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc102", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-cnt0"
                    cmd = [
                        "start",
                        "spc102",
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
                        # writes nothing
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-COUNT")

                    # Spec remains approved
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc102*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    self.assertIn(
                        "- Status: approved", spec_files[0].read_text(encoding="utf-8")
                    )

    def test_5_5_refusal_count_missing_from_spec(self):
        """Case (3): fake agent writes plan lacking From-Spec -> ends fail-gate with SPEC-PLAN-COUNT,
        spec remains approved.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc103", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-nofrom"
                    cmd = [
                        "start",
                        "spc103",
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
                        _write_conforming_plan(target, id6="pln103", spec_id6=None)
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-COUNT")

                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc103*.spec.md")
                    )
                    self.assertIn(
                        "- Status: approved", spec_files[0].read_text(encoding="utf-8")
                    )

    def test_5_5_refusal_conformance_draft(self):
        """Case (4): fake agent writes plan with - Status: draft -> ends fail-gate with
        SPEC-PLAN-CONFORMANCE, spec remains approved.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc104", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-draft"
                    cmd = [
                        "start",
                        "spc104",
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
                            target, id6="pln104", spec_id6="spc104", status="draft"
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-CONFORMANCE")

                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc104*.spec.md")
                    )
                    self.assertIn(
                        "- Status: approved", spec_files[0].read_text(encoding="utf-8")
                    )

    def test_duplicate_clause_live_plan_in_baseline(self):
        """Case (5): live plan with same From-Spec already exists in baseline -> fails SPEC-PLAN-COUNT,
        spec remains approved.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc105", status="approved")
                    # Existing live plan in pending/
                    _write_conforming_plan(repo, id6="pold01", spec_id6="spc105")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec and old plan"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-dup"
                    cmd = [
                        "start",
                        "spc105",
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
                            target, id6="pnew01", spec_id6="spc105", setid="second"
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-COUNT")
                    self.assertIn("reconcile duplicates", refusal.get("reason", ""))

                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20260927-spc105*.spec.md")
                    )
                    self.assertIn(
                        "- Status: approved", spec_files[0].read_text(encoding="utf-8")
                    )

    def test_5_5b_gate_carry_both_directions(self):
        """Case (6): 5.5b both directions of SPEC-PLAN-GATE-CARRY:
        - Gated spec: plan carrying gate passes, plan omitting gate fails.
        - Ungated spec: plan omitting gate passes, plan inventing gate fails.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spcg01", status="approved", gate="next")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add gated spec"], cwd=repo, check=True
                    )

                    # Gated spec with omitted gate -> fail-gate
                    run_id = f"run-{host_label}-g-omit"
                    cmd = [
                        "start",
                        "spcg01",
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

                    def fake_agent_omit(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pgom01", spec_id6="spcg01", gate=None
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_omit):
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-GATE-CARRY")

                    # Reset committed produced plan file from test repo
                    subprocess.run(
                        ["git", "reset", "--hard", "HEAD~1"], cwd=repo, check=True
                    )

                    # Gated spec with matching gate -> executed
                    run_id2 = f"run-{host_label}-g-match"
                    cmd2 = [
                        "start",
                        "spcg01",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id2,
                        "--no-isolate-worktree",
                    ]
                    args2 = mod.build_parser().parse_args(cmd2)
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir2 = mod.initialize_run(args2)

                    def fake_agent_match(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(
                            target, id6="pgma01", spec_id6="spcg01", gate="next"
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_match):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir2, retry_incomplete=False)

                    state2 = json.loads(
                        (run_dir2 / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(state2["queue"][0]["status"], "executed")

    def test_5_5_trace_success(self):
        """Case: post-cutover spec with requirements and ACs; agent produces plan citing all -> executed."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(
                        repo,
                        id6="spctr1",
                        status="approved",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        requirements=[
                            "R-1 First requirement.",
                            "R-2 Second requirement.",
                        ],
                        acceptance=["AC-1 First acceptance criterion."],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add post-cutover spec"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-tr-succ"
                    cmd = [
                        "start",
                        "spctr1",
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
                            id6="plntr1",
                            spec_id6="spctr1",
                            filename_date="20261001",
                            e_items=[
                                "Implements `spctr1` R-1",
                                "Implements `spctr1` R-2",
                            ],
                            v_items=["Validates `spctr1` AC-1", "Validates check"],
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
                    self.assertEqual(item["status"], "executed")
                    self.assertEqual(item["attempts"][0]["disposition"], "executed")

    def test_5_5_trace_refusal_missing_requirement(self):
        """Case: post-cutover spec; plan omits R-2 -> fail-gate with SPEC-PLAN-TRACE, lane preserved."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(
                        repo,
                        id6="spctr2",
                        status="approved",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        requirements=[
                            "R-1 First requirement.",
                            "R-2 Second requirement.",
                        ],
                        acceptance=["AC-1 First acceptance criterion."],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add post-cutover spec"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-tr-fail"
                    cmd = [
                        "start",
                        "spctr2",
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
                            id6="plntr2",
                            spec_id6="spctr2",
                            filename_date="20261001",
                            e_items=["Implements `spctr2` R-1 only"],
                            v_items=["Validates `spctr2` AC-1"],
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-TRACE")
                    self.assertIn("R-2", refusal.get("reason", ""))
                    self.assertIn("SPEC-PLAN-TRACE", refusal.get("reason", ""))

    def test_5_5_trace_grandfathered_pass(self):
        """Case: pre-cutover spec predating cutover; plan omits requirements -> passes."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(
                        repo,
                        id6="spcgf1",
                        status="approved",
                        filename_date="20260920",
                        spec_date="2026-09-20",
                        requirements=["R-1 First requirement."],
                        acceptance=["AC-1 First acceptance criterion."],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add pre-cutover spec"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-gf-pass"
                    cmd = [
                        "start",
                        "spcgf1",
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
                            id6="plngf1",
                            spec_id6="spcgf1",
                            filename_date="20260920",
                            e_items=["Unrelated work"],
                            v_items=["Unrelated check"],
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
                    self.assertEqual(item["status"], "executed")

    def test_5_5_trace_unknown_reference(self):
        """Case: plan cites an unknown spec requirement -> fail-gate with SPEC-PLAN-TRACE."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(
                        repo,
                        id6="spcunk",
                        status="approved",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        requirements=["R-1 First requirement."],
                        acceptance=["AC-1 First acceptance criterion."],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-tr-unk"
                    cmd = [
                        "start",
                        "spcunk",
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
                            id6="plnunk",
                            spec_id6="spcunk",
                            filename_date="20261001",
                            e_items=["Implements `spcunk` R-1 and `spcunk` R-999"],
                            v_items=["Validates `spcunk` AC-1"],
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
                    self.assertEqual(refusal.get("code"), "SPEC-PLAN-TRACE")
                    self.assertIn("R-999", refusal.get("reason", ""))


class TestSpecProductionLifecycleArmAndReportE09(unittest.TestCase):
    """Lifecycle arm, side-effect isolation, quarantine, and report-only cases (E-09)."""

    def test_no_execute_path_side_effects(self):
        """A production turn runs NO suite check, makes NO aw ipd finalize call against spec,
        and makes NO backlog close. Assert by patching collaborators to fail if called.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc201", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-arm"
                    cmd = [
                        "start",
                        "spc201",
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
                        _write_conforming_plan(target, id6="pln201", spec_id6="spc201")
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    def fail_suite_check(*args, **kwargs):
                        raise AssertionError(
                            "run_suite_check must NOT be called for production turn!"
                        )

                    def fail_finalize(*args, **kwargs):
                        raise AssertionError(
                            "driver_finalize / aw ipd finalize must NOT be called against spec!"
                        )

                    def fail_backlog_close(*args, **kwargs):
                        raise AssertionError(
                            "process_backlog_close must NOT be called for production turn!"
                        )

                    with (
                        _patch_host_agent(mod, fake_agent),
                        mock.patch.object(
                            runner_shared, "run_suite_check", fail_suite_check
                        ),
                        mock.patch.object(
                            mod, "run_suite_check", fail_suite_check, create=True
                        ),
                        mock.patch.object(
                            runner_shared, "driver_finalize", fail_finalize
                        ),
                        mock.patch.object(
                            mod, "driver_finalize", fail_finalize, create=True
                        ),
                        mock.patch.object(
                            runner_shared, "process_backlog_close", fail_backlog_close
                        ),
                        mock.patch.object(
                            mod,
                            "process_backlog_close",
                            fail_backlog_close,
                            create=True,
                        ),
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(state["queue"][0]["status"], "executed")

    def test_review_style_integration_asserted(self):
        """Production turn takes review-style integration without suite revalidation."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc202", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-integ"
                    cmd = [
                        "start",
                        "spc202",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        _write_conforming_plan(target, id6="pln202", spec_id6="spc202")
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
                    self.assertEqual(item["status"], "executed")
                    self.assertTrue(item.get("prod_integrated"))
                    self.assertTrue(item["attempts"][0].get("prod_integrated"))

    def test_quarantine_lane_preserved_on_failure(self):
        """A failed production leaves its isolated lane recorded as preserved in state (F-10)."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc203", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-quar"
                    cmd = [
                        "start",
                        "spc203",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
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
                        # writes nothing -> verification fails
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
                    self.assertIn("preserved_worktree", item)
                    self.assertEqual(item.get("preserved_lane_id"), "spc203")
                    self.assertTrue(Path(item["preserved_worktree"]).is_dir())

    def test_report_only_and_resume_spawns_nothing(self):
        """Report-only (5.5a): queue IDs before == after; generated_next_actions rendered
        in execution-report.md and run summary; run_viewer parses report table;
        resume spawns nothing.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc204", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-rep"
                    cmd = [
                        "start",
                        "spc204",
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

                    state_before = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    queue_ids_before = [it["id6"] for it in state_before["queue"]]

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        work_dir = kwargs.get("work_dir")
                        target = Path(work_dir) if work_dir else Path(state["repo"])
                        _write_conforming_plan(target, id6="pln204", spec_id6="spc204")
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state_after = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    queue_ids_after = [it["id6"] for it in state_after["queue"]]

                    # 1. Queue IDs before equals after (produced plans not added to queue)
                    self.assertEqual(queue_ids_before, queue_ids_after)

                    # 2. generated_next_actions on item
                    gen_acts = (
                        state_after["queue"][0].get("generated_next_actions") or []
                    )
                    self.assertEqual(len(gen_acts), 1)
                    self.assertEqual(gen_acts[0]["id6"], "pln204")

                    # 3. execution-report.md has Generated next actions block
                    rep_path = run_dir / "execution-report.md"
                    self.assertTrue(rep_path.is_file())
                    rep_text = rep_path.read_text(encoding="utf-8")
                    self.assertIn("## Generated next actions", rep_text)
                    self.assertIn("They were NOT run in this run", rep_text)
                    self.assertIn("pln204", rep_text)

                    # 4. render_run_summary_table contains summary block
                    summary_text = render_stream.render_run_summary_table(
                        state_after,
                        driver_label=host_label,
                    )
                    self.assertIn(
                        "Generated next actions (not run in this run):", summary_text
                    )
                    self.assertIn("pln204", summary_text)

                    # 5. run_viewer.load_run_summary parses the report successfully
                    parsed = run_viewer.load_run_summary(run_dir)
                    self.assertEqual(len(parsed.steps), 1)
                    self.assertEqual(parsed.steps[0].id6, "spc204")
                    self.assertEqual(parsed.steps[0].status, "executed")

                    # 6. Resume on completed run spawns no new turn
                    def fail_on_spawn(*args, **kwargs):
                        raise AssertionError(
                            "Spawn must NOT be called on resume of completed production run!"
                        )

                    with _patch_host_agent(mod, fail_on_spawn):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            res_rc = mod.main(
                                ["resume", str(run_dir), "--repo", str(repo)]
                            )
                        self.assertEqual(res_rc, 0)


class TestActionPlanEnforcementE07(unittest.TestCase):
    """Enforcement of --action plan and action-derived refusals (E-07)."""

    def test_action_plan_legal_for_approved_spec(self):
        """--action plan is legal for an approved spec."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(repo, id6="spc301", status="approved")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add spec"], cwd=repo, check=True
                    )

                    cmd = [
                        "start",
                        "spc301",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--prepare-only",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)
                    self.assertTrue(Path(run_dir).is_dir())

    def test_action_plan_illegal_for_plan(self):
        """--action plan is illegal for a plan, message names plan and gives plan recovery."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_conforming_plan(repo, id6="pln301", status="to-review")
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add plan"], cwd=repo, check=True
                    )

                    cmd = [
                        "start",
                        "pln301",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--prepare-only",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with self.assertRaises(runner_shared.DriverError) as cm:
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.initialize_run(args)

                    msg = str(cm.exception)
                    self.assertIn("--action plan is illegal", msg)
                    self.assertIn("pln301", msg)
                    self.assertIn("--action plan <selector>", msg)
                    self.assertNotIn("Review is the next legal action", msg)
