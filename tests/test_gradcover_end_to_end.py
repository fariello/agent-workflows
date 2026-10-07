"""End-to-end integration test proving that a graduation yields an orchestrator the runner accepts.

Covers Set gradcover, IPD wytlly (Order 12):
Shows, by driving the real runner over real records, that a graduation now either
hands off a Set the next review and orchestrate runs accept with no further probe call,
or fails visibly with the backlog item still open and the uncovered passage quoted.

NOTE ON PROBE DOUBLE:
The probe double answers in Order 02's format, decided from the excerpt it is handed:
if the excerpt contains the unowned line it returns `ORCHESTRATOR: CONTAINS EXECUTIONS`
then `QUOTE: <that line>`, otherwise `ORCHESTRATOR: CONTAINS NO EXECUTIONS`. That double
makes the model's judgement scripted, so this test proves the PLUMBING across surfaces,
not the model's named-owner credit (which Order 02's prompt carries).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    cli,
    coverage_record,
    ipd_lint,
    lane_containment,
    oc_runipd,
    run_viewer,
    runner_shared as rs,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))
UNOWNED_LINE = "the full suite passes after both children"


def _make_test_repo(path: Path) -> Path:
    """Seed a clean git repository with an initial commit and a planned fixture release."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    (path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (path / ".gitignore").write_text(
        ".aw/records/runs/\n.aw/worktrees/\n.aw/state/\n", encoding="utf-8"
    )
    rel_dir = path / ".aw" / "records" / "releases"
    rel_dir.mkdir(parents=True, exist_ok=True)
    (rel_dir / "20260901-rel001-01-rel001-v1.release.md").write_text(
        "# RELEASE: v1\n- Id: rel001\n- Status: planned\n- Version: 1.0.0\n",
        encoding="utf-8",
    )
    (path / ".aw" / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=path, check=True)
    return path


def _write_backlog_item(
    repo: Path,
    *,
    id6: str,
    setid: str,
    status: str = "open",
    summary: str = "Fixture backlog bug",
    slug: str = "fixture-bug",
    gate: str = "rel001",
    work_kind: str = "bug",
    priority: str = "high",
) -> Path:
    """Write a conforming backlog item in the specified status folder."""
    bkl_dir = repo / ".aw" / "records" / "backlog" / status
    bkl_dir.mkdir(parents=True, exist_ok=True)
    file_path = bkl_dir / f"20261004-{setid}-01-{id6}-{slug}.backlog.md"
    content = f"""- Id: {id6}
- Status: {status}
- Set: {setid}
- Blocks-Release: {gate}
- Priority: {priority}
- Work-Kind: {work_kind}
- Summary: {summary}

## Workflow history
- 2026-10-04 {status} (tester): created item
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _orchestrator_template(
    *,
    id6: str,
    setid: str,
    backlog_id6: str,
    child1_id6: str = "chd001",
    child2_id6: str = "chd002",
    completion_line: str = f"- {UNOWNED_LINE}",
    status: str = "to-review",
    gate: str = "rel001",
) -> str:
    """Render an orchestrator document that lints conforming at author."""
    return f"""# IPD: Test Orchestrator {id6}

- Date: 2026-10-04
- Kind: orchestrator
- Id: {id6}
- Set: {setid}
- Order: 0
- Status: {status}
- From-Backlog: {backlog_id6}
- Blocks-Release: {gate}
- Priority: high
- Work-Kind: bug
- Author: test
- Highest E allocated: 02
- Concern: Test orchestrator concern.
- Scope: Test orchestrator scope.
- Scope-Paths: tests/test_gradcover_end_to_end.py
- Item-Dependencies: none

## Workflow history
- 2026-10-04 {status} (test): created.

## Goal
Test orchestrator goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: orchestrate
- [ ] E-01 CONFIRM {child1_id6} REACHED executed
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending
- [ ] E-02 CONFIRM {child2_id6} REACHED executed
  - Depends on: E-01
  - Expected outcome: done
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Status | Plan | Depends on |
|---|---|---|---|---|
| 01 | {child1_id6} | pending | .aw/records/plans/pending/20261004-{setid}-01-{child1_id6}-test-child-1.ipd.md | none |
| 02 | {child2_id6} | pending | .aw/records/plans/pending/20261004-{setid}-02-{child2_id6}-test-child-2.ipd.md | none |

## Completion criteria (the whole Set is done only when)
{completion_line}

## Cross-IPD validation
- None.

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

## Validation and cross-check (verify before reporting the Set complete)
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""


def _child_template(
    *,
    id6: str,
    setid: str,
    order: int,
    backlog_id6: str,
    deps: str = "none",
    status: str = "to-review",
    gate: str = "rel001",
) -> str:
    """Render a child document that lints conforming at author."""
    return f"""# IPD: Test Child Plan {id6}

- Date: 2026-10-04
- Kind: child
- Concern: Test child {id6} concern.
- Scope: Test child {id6} scope.
- Scope-Paths: tests/test_gradcover_end_to_end.py
- Status: {status}
- From-Backlog: {backlog_id6}
- Blocks-Release: {gate}
- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Priority: high
- Work-Kind: bug
- Id: {id6}
- Item-Dependencies: {deps}

## Workflow history
- 2026-10-04 {status} (test): created.

## Goal
Test child {id6} goal.

## Detailed Implementation Checklist (TODO)
Execution-state rule: mark performed only after doing it.
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
- None.

## Findings
- None.

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
Validation-state rule: inspect evidence.
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- None.
"""


def _write_orchestrator_plan(
    repo: Path,
    *,
    id6: str = "orc001",
    setid: str = "set001",
    backlog_id6: str = "bkl001",
    child1_id6: str = "chd001",
    child2_id6: str = "chd002",
    completion_line: str = f"- {UNOWNED_LINE}",
    status: str = "to-review",
    gate: str = "rel001",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261004-{setid}-00-{id6}-test-orch.ipd.md"
    content = _orchestrator_template(
        id6=id6,
        setid=setid,
        backlog_id6=backlog_id6,
        child1_id6=child1_id6,
        child2_id6=child2_id6,
        completion_line=completion_line,
        status=status,
        gate=gate,
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _write_child_plan(
    repo: Path,
    *,
    id6: str,
    setid: str = "set001",
    order: int = 1,
    backlog_id6: str = "bkl001",
    deps: str = "none",
    status: str = "to-review",
    gate: str = "rel001",
) -> Path:
    p_dir = repo / ".aw" / "records" / "plans" / "pending"
    p_dir.mkdir(parents=True, exist_ok=True)
    file_path = p_dir / f"20261004-{setid}-{order:02d}-{id6}-test-child-{order}.ipd.md"
    content = _child_template(
        id6=id6,
        setid=setid,
        order=order,
        backlog_id6=backlog_id6,
        deps=deps,
        status=status,
        gate=gate,
    )
    file_path.write_text(content, encoding="utf-8")
    return file_path


def _patch_host_agent(module: Any, agent_fn: Any) -> Any:
    """Patch the host launcher function with agent_fn."""
    if module is oc_runipd:
        return mock.patch.object(oc_runipd, "run_opencode", agent_fn)

    def _agy_wrapper(
        state: Any,
        run_dir: Any,
        item: Any,
        prompt_path: Any,
        attempt_no: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        work_dir = kwargs.get("work_dir")
        root = Path(work_dir) if work_dir else Path(state.get("repo", "."))
        plan_path = rs.queue_artifact_path(root, item)
        return agent_fn(
            state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
        )

    return mock.patch.object(agy_runipd, "run_agy_turn", _agy_wrapper)


@pytest.mark.slow
class TestGradcoverEndToEnd(unittest.TestCase):
    """Integration test suite validating IPD wytlly end-to-end across hosts."""

    def setUp(self) -> None:
        from agent_workflows import selectors as _sel

        _sel._record_dirs_cached.cache_clear()

    def tearDown(self) -> None:
        from agent_workflows import selectors as _sel

        _sel._record_dirs_cached.cache_clear()

    def test_fixture_templates_conform_at_author(self) -> None:
        """Verify fixture templates lint conforming at author checkpoint."""
        orch_txt = _orchestrator_template(
            id6="orc001", setid="set001", backlog_id6="bkl001"
        )
        chd1_txt = _child_template(
            id6="chd001", setid="set001", order=1, backlog_id6="bkl001"
        )
        chd2_txt = _child_template(
            id6="chd002", setid="set001", order=2, backlog_id6="bkl001", deps="none"
        )

        res_orch = ipd_lint.lint_text(orch_txt, checkpoint="author")
        self.assertEqual(
            res_orch.disposition, "conforming", [d.code for d in res_orch.diagnostics]
        )
        res_chd1 = ipd_lint.lint_text(chd1_txt, checkpoint="author")
        self.assertEqual(
            res_chd1.disposition, "conforming", [d.code for d in res_chd1.diagnostics]
        )
        res_chd2 = ipd_lint.lint_text(chd2_txt, checkpoint="author")
        self.assertEqual(
            res_chd2.disposition, "conforming", [d.code for d in res_chd2.diagnostics]
        )

    def test_e01_e06_e07_success_path_graduate_review_orchestrate(self) -> None:
        """Task group 1: success scenario across graduation (Run A), review (Run B), and orchestrate (Run C)."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl001", setid="set001", gate="rel001"
                    )
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    # -------------------------------------------------------------
                    # RUN A (E-01): Graduation with correction turn
                    # -------------------------------------------------------------
                    run_id_a = f"run-{host_label}-grad-succ"
                    cmd_a = [
                        "start",
                        "bkl001",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id_a,
                        "--retry-budget",
                        "1",
                    ]
                    args_a = mod.build_parser().parse_args(cmd_a)
                    buf_a = io.StringIO()
                    with contextlib.redirect_stdout(buf_a), contextlib.redirect_stderr(
                        buf_a
                    ):
                        run_dir_a = mod.initialize_run(args_a)

                    probe_calls_a: list[str] = []

                    def probe_double_a(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls_a.append(host)
                        if UNOWNED_LINE in excerpt and "Owner:" not in excerpt:
                            reply = f"ORCHESTRATOR: CONTAINS EXECUTIONS\nQUOTE: {UNOWNED_LINE}"
                        else:
                            reply = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    turn_counter_a = [0]

                    def fake_agent_a(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter_a[0] += 1
                        work_dir = Path(kwargs["work_dir"])
                        if turn_counter_a[0] == 1:
                            # Turn 1: write orchestrator with unowned line and 2 children
                            _write_orchestrator_plan(
                                work_dir,
                                id6="orc001",
                                setid="set001",
                                backlog_id6="bkl001",
                                completion_line=f"- {UNOWNED_LINE}",
                            )
                            _write_child_plan(
                                work_dir,
                                id6="chd001",
                                setid="set001",
                                order=1,
                                backlog_id6="bkl001",
                            )
                            _write_child_plan(
                                work_dir,
                                id6="chd002",
                                setid="set001",
                                order=2,
                                backlog_id6="bkl001",
                                deps="none",
                            )
                        else:
                            # Correction turn: rewrite unowned line to assign owner chd002
                            orch_files = list(
                                work_dir.glob(
                                    ".aw/records/plans/pending/*-orc001-*.ipd.md"
                                )
                            )
                            self.assertEqual(len(orch_files), 1)
                            txt = orch_files[0].read_text(encoding="utf-8")
                            txt = txt.replace(
                                f"- {UNOWNED_LINE}", f"- {UNOWNED_LINE}. Owner: chd002"
                            )
                            orch_files[0].write_text(txt, encoding="utf-8")
                        return (
                            0,
                            f"session-a-{turn_counter_a[0]}",
                            rdir / "log.txt",
                            ["cmd"],
                        )

                    with _patch_host_agent(mod, fake_agent_a), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double_a
                    ):
                        with contextlib.redirect_stdout(
                            buf_a
                        ), contextlib.redirect_stderr(buf_a):
                            mod.run_queue(run_dir_a, retry_incomplete=False)

                    # Run A Assertions (E-01 / V-01)
                    self.assertEqual(
                        len(probe_calls_a),
                        2,
                        "Expected exactly 2 probe calls during Run A",
                    )
                    state_a = json.loads(
                        (run_dir_a / "state.json").read_text(encoding="utf-8")
                    )
                    item_a = state_a["queue"][0]
                    self.assertEqual(item_a["status"], "executed")
                    self.assertEqual(rs.production_set_retry_attempts(item_a), 1)

                    corr_attempts = [
                        a
                        for a in item_a.get("attempts", [])
                        if a.get("action") == "production-set-correction"
                    ]
                    self.assertEqual(len(corr_attempts), 1)
                    findings_given = corr_attempts[0].get("findings_given") or []
                    self.assertTrue(
                        any(
                            f[0] == "BACKLOG-GRADUATE-SET" and UNOWNED_LINE in f[2]
                            for f in findings_given
                            if isinstance(f, (list, tuple)) and len(f) >= 3
                        ),
                        f"First attempt findings must carry BACKLOG-GRADUATE-SET with quoted line: {findings_given}",
                    )

                    # Backlog item transitioned to graduated on main
                    bkl_files_a = list(
                        repo.glob(
                            ".aw/records/backlog/**/20261004-set001-01-bkl001-*.backlog.md"
                        )
                    )
                    self.assertEqual(len(bkl_files_a), 1)
                    self.assertIn("/graduated/", str(bkl_files_a[0]).replace("\\", "/"))
                    bkl_txt_a = bkl_files_a[0].read_text(encoding="utf-8")
                    self.assertIn("- Status: graduated", bkl_txt_a)

                    # Orchestrator on main has current pass record
                    orch_files_a = list(
                        repo.glob(".aw/records/plans/pending/*-orc001-*.ipd.md")
                    )
                    self.assertEqual(len(orch_files_a), 1)
                    orch_txt_a = orch_files_a[0].read_text(encoding="utf-8")
                    self.assertIn("- Coverage: pass", orch_txt_a)
                    self.assertIn("- Coverage-Fingerprint:", orch_txt_a)
                    self.assertTrue(coverage_record.is_current(orch_txt_a))
                    self.assertIn("coverage pass", orch_txt_a)

                    # Git status on main is clean
                    st_a = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertEqual(st_a.stdout.strip(), "")

                    # -------------------------------------------------------------
                    # RUN B (E-06): Review run over the produced Set
                    # -------------------------------------------------------------
                    run_id_b = f"run-{host_label}-rev-succ"
                    cmd_b = [
                        "start",
                        "set001",
                        "--action",
                        "review",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id_b,
                    ]
                    args_b = mod.build_parser().parse_args(cmd_b)
                    buf_b = io.StringIO()
                    with contextlib.redirect_stdout(buf_b), contextlib.redirect_stderr(
                        buf_b
                    ):
                        run_dir_b = mod.initialize_run(args_b)

                    probe_calls_b: list[str] = []

                    def probe_double_b(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls_b.append(host)
                        reply = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    reviewed_order: list[str] = []

                    def fake_reviewer_b(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        w_dir = Path(kwargs.get("work_dir") or state["repo"])
                        t_id6 = item["id6"]
                        reviewed_order.append(t_id6)
                        buf_cli = io.StringIO()
                        with contextlib.redirect_stdout(
                            buf_cli
                        ), contextlib.redirect_stderr(buf_cli):
                            rc = cli.main(
                                [
                                    "ipd",
                                    "set",
                                    "reviewed",
                                    t_id6,
                                    "--dir",
                                    str(w_dir),
                                    "--yes",
                                    "--message",
                                    f"reviewed {t_id6} successfully",
                                ]
                            )
                        self.assertEqual(
                            rc,
                            0,
                            f"Expected aw ipd set reviewed to succeed on {t_id6}: {buf_cli.getvalue()}",
                        )
                        return 0, "session-b-sweep", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_reviewer_b), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double_b
                    ):
                        with contextlib.redirect_stdout(
                            buf_b
                        ), contextlib.redirect_stderr(buf_b):
                            mod.run_queue(run_dir_b, retry_incomplete=False)

                    # Run B Assertions (E-06 / V-06)
                    self.assertEqual(
                        len(probe_calls_b),
                        0,
                        "Run B must make zero probe calls across the whole run",
                    )
                    self.assertEqual(
                        set(reviewed_order),
                        {"chd001", "chd002", "orc001"},
                        "All three plans must be reviewed",
                    )

                    state_b = json.loads(
                        (run_dir_b / "state.json").read_text(encoding="utf-8")
                    )
                    for q_item in state_b["queue"]:
                        self.assertEqual(q_item["status"], "reviewed")
                        ref = q_item.get("refusal") or {}
                        self.assertNotEqual(
                            ref.get("code"), "IPD-REVIEW-ORCHESTRATOR-READY"
                        )

                    # All three plans read - Status: reviewed
                    for p_id in ("orc001", "chd001", "chd002"):
                        p_file = list(
                            repo.glob(f".aw/records/plans/pending/*-{p_id}-*.ipd.md")
                        )[0]
                        self.assertIn(
                            "- Status: reviewed", p_file.read_text(encoding="utf-8")
                        )

                    # -------------------------------------------------------------
                    # RUN C (E-07): Orchestrate run after children executed
                    # -------------------------------------------------------------
                    # Move children to executed/ with - Status: executed
                    exec_dir = repo / ".aw" / "records" / "plans" / "executed"
                    exec_dir.mkdir(parents=True, exist_ok=True)
                    for c_id in ("chd001", "chd002"):
                        c_p = list(
                            repo.glob(f".aw/records/plans/pending/*-{c_id}-*.ipd.md")
                        )[0]
                        c_txt = c_p.read_text(encoding="utf-8").replace(
                            "- Status: reviewed", "- Status: executed"
                        )
                        (exec_dir / c_p.name).write_text(c_txt, encoding="utf-8")
                        c_p.unlink()

                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "children executed"],
                        cwd=repo,
                        check=True,
                    )

                    # Approve orchestrator
                    buf_appr = io.StringIO()
                    with contextlib.redirect_stdout(
                        buf_appr
                    ), contextlib.redirect_stderr(buf_appr):
                        rc_appr = cli.main(
                            [
                                "ipd",
                                "set",
                                "approved",
                                "orc001",
                                "--dir",
                                str(repo),
                                "--by-human",
                                "--message",
                                "approved for execution",
                                "--yes",
                            ]
                        )
                    self.assertEqual(
                        rc_appr, 0, f"Approval failed: {buf_appr.getvalue()}"
                    )

                    run_id_c = f"run-{host_label}-orch-succ"
                    cmd_c = [
                        "start",
                        "set001",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id_c,
                    ]
                    args_c = mod.build_parser().parse_args(cmd_c)
                    buf_c = io.StringIO()
                    with contextlib.redirect_stdout(buf_c), contextlib.redirect_stderr(
                        buf_c
                    ):
                        run_dir_c = mod.initialize_run(args_c)

                    probe_calls_c: list[str] = []

                    def probe_double_c(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls_c.append(host)
                        reply = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    def fail_agent_c(*args: Any, **kwargs: Any) -> Any:
                        self.fail(
                            "Agent turn must NOT be called for orchestrate action"
                        )

                    with _patch_host_agent(mod, fail_agent_c), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double_c
                    ):
                        with contextlib.redirect_stdout(
                            buf_c
                        ), contextlib.redirect_stderr(buf_c):
                            mod.run_queue(run_dir_c, retry_incomplete=False)

                    # Run C Assertions (E-07 / V-07)
                    self.assertEqual(
                        len(probe_calls_c), 0, "Run C must make zero probe calls"
                    )
                    state_c = json.loads(
                        (run_dir_c / "state.json").read_text(encoding="utf-8")
                    )
                    item_c = state_c["queue"][0]
                    self.assertEqual(item_c["action"], "orchestrate")
                    self.assertEqual(item_c["status"], "executed")

                    events_c = [
                        json.loads(line)
                        for line in (run_dir_c / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    self.assertTrue(
                        any(
                            ev.get("event") == "orchestrator-finalized"
                            and ev.get("id6") == "orc001"
                            for ev in events_c
                        ),
                        "Expected orchestrator-finalized event in events.jsonl",
                    )

                    orch_exec_files = list(
                        repo.glob(".aw/records/plans/executed/*-orc001-*.ipd.md")
                    )
                    self.assertEqual(len(orch_exec_files), 1)
                    self.assertIn(
                        "- Status: executed",
                        orch_exec_files[0].read_text(encoding="utf-8"),
                    )

    def test_e02_refusal_scenario_and_setter_refusals(self) -> None:
        """Task group 2: refusal scenario (Run A uncorrected), preserved lane, run_viewer, and in-lane setter refusals."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl002", setid="set002", gate="rel001"
                    )
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-refusal"
                    cmd = [
                        "start",
                        "bkl002",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--retry-budget",
                        "1",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args)

                    probe_calls: list[str] = []

                    def probe_double(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls.append(host)
                        if UNOWNED_LINE in excerpt:
                            reply = f"ORCHESTRATOR: CONTAINS EXECUTIONS\nQUOTE: {UNOWNED_LINE}"
                        else:
                            reply = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    turn_counter = [0]

                    def fake_agent(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        turn_counter[0] += 1
                        work_dir = Path(kwargs["work_dir"])
                        if turn_counter[0] == 1:
                            # Turn 1: writes orchestrator with unowned line and 2 children
                            _write_orchestrator_plan(
                                work_dir,
                                id6="orc002",
                                setid="set002",
                                backlog_id6="bkl002",
                                completion_line=f"- {UNOWNED_LINE}",
                            )
                            _write_child_plan(
                                work_dir,
                                id6="chd001",
                                setid="set002",
                                order=1,
                                backlog_id6="bkl002",
                            )
                            _write_child_plan(
                                work_dir,
                                id6="chd002",
                                setid="set002",
                                order=2,
                                backlog_id6="bkl002",
                                deps="none",
                            )
                        else:
                            # Correction turn: does NOT fix the unowned line (leaves checked sections unchanged)
                            pass
                        return (
                            0,
                            f"session-{turn_counter[0]}",
                            rdir / "log.txt",
                            ["cmd"],
                        )

                    with _patch_host_agent(mod, fake_agent), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double
                    ):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    # E-02 Assertions (V-02)
                    self.assertEqual(
                        len(probe_calls),
                        1,
                        "Expected exactly 1 probe call: fingerprint unchanged on correction",
                    )
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertEqual(rs.production_set_retry_attempts(item), 1)

                    refusal = item.get("refusal") or {}
                    self.assertEqual(refusal.get("code"), "BACKLOG-GRADUATE-SET")
                    self.assertIn(UNOWNED_LINE, refusal.get("reason", ""))

                    # Main tree untouched: backlog item is still open, no linked plans on main
                    bkl_main = list(
                        repo.glob(
                            ".aw/records/backlog/**/20261004-set002-01-bkl002-*.backlog.md"
                        )
                    )[0]
                    self.assertIn("/open/", str(bkl_main).replace("\\", "/"))
                    self.assertIn(
                        "- Status: open", bkl_main.read_text(encoding="utf-8")
                    )
                    plans_main = list(repo.glob(".aw/records/plans/**/*.ipd.md"))
                    self.assertEqual(len(plans_main), 0)

                    # Preserved worktree
                    self.assertIn("preserved_worktree", item)
                    pw = Path(item["preserved_worktree"])
                    self.assertTrue(pw.is_dir())

                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    self.assertTrue(
                        any(
                            ev.get("event") == lane_containment.LANE_PRESERVED_EVENT
                            for ev in events
                        )
                    )

                    # Preserved orchestrator has committed - Coverage: fail quoting line
                    orch_pw_files = list(
                        pw.glob(".aw/records/plans/pending/*-orc002-*.ipd.md")
                    )
                    self.assertEqual(len(orch_pw_files), 1)
                    orch_pw_txt = orch_pw_files[0].read_text(encoding="utf-8")
                    self.assertIn("- Coverage: fail", orch_pw_txt)
                    self.assertIn("## Coverage findings", orch_pw_txt)
                    self.assertIn(UNOWNED_LINE, orch_pw_txt)

                    # run_viewer detail view contains quoted line
                    summary = run_viewer.load_run_summary(run_dir, repo_root=repo)
                    term = run_viewer.Term(color=False)
                    rendered_detail = run_viewer.format_run_human(
                        summary, term, detail=True, repo_root=repo
                    )
                    self.assertIn("! refused [BACKLOG-GRADUATE-SET]:", rendered_detail)
                    self.assertIn(UNOWNED_LINE, rendered_detail)

                    # In-lane setter refusals
                    bkl_pw = list(
                        pw.glob(
                            ".aw/records/backlog/**/20261004-set002-01-bkl002-*.backlog.md"
                        )
                    )[0]
                    bkl_pw_bytes_before = bkl_pw.read_bytes()
                    orch_pw_bytes_before = orch_pw_files[0].read_bytes()

                    buf_bkl_set = io.StringIO()
                    with contextlib.redirect_stdout(
                        buf_bkl_set
                    ), contextlib.redirect_stderr(buf_bkl_set):
                        rc_bkl_set = cli.main(
                            [
                                "backlog",
                                "set",
                                "graduated",
                                "bkl002",
                                "--dir",
                                str(pw),
                                "--no-commit",
                            ]
                        )
                    self.assertNotEqual(rc_bkl_set, 0)
                    self.assertEqual(bkl_pw.read_bytes(), bkl_pw_bytes_before)
                    out_bkl_set = buf_bkl_set.getvalue()
                    self.assertTrue(
                        UNOWNED_LINE in out_bkl_set
                        or "coverage-fail" in out_bkl_set
                        or "BACKLOG-GRADUATE-SET" in out_bkl_set,
                        f"Expected quoted line or coverage-fail in backlog set output: {out_bkl_set}",
                    )

                    buf_ipd_set = io.StringIO()
                    with contextlib.redirect_stdout(
                        buf_ipd_set
                    ), contextlib.redirect_stderr(buf_ipd_set):
                        rc_ipd_set = cli.main(
                            [
                                "ipd",
                                "set",
                                "reviewed",
                                "orc002",
                                "--dir",
                                str(pw),
                                "--yes",
                                "--message",
                                "attempt in-lane review",
                            ]
                        )
                    self.assertNotEqual(rc_ipd_set, 0)
                    self.assertEqual(
                        orch_pw_files[0].read_bytes(), orch_pw_bytes_before
                    )
                    out_ipd_set = buf_ipd_set.getvalue()
                    self.assertTrue(
                        UNOWNED_LINE in out_ipd_set or "coverage-fail" in out_ipd_set,
                        f"Expected quoted line or coverage-fail in ipd set output: {out_ipd_set}",
                    )

    def test_e03_resume_scenario(self) -> None:
        """Task group 2: resume an earlier refused handoff brought onto main."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_backlog_item(
                        repo, id6="bkl003", setid="set003", gate="rel001"
                    )
                    subprocess.run(["git", "add", "."], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add backlog"], cwd=repo, check=True
                    )

                    # 1. Run earlier refused graduation
                    run_id_ref = f"run-{host_label}-earlier-ref"
                    cmd_ref = [
                        "start",
                        "bkl003",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id_ref,
                        "--retry-budget",
                        "0",
                    ]
                    args_ref = mod.build_parser().parse_args(cmd_ref)
                    buf_ref = io.StringIO()
                    with contextlib.redirect_stdout(
                        buf_ref
                    ), contextlib.redirect_stderr(buf_ref):
                        run_dir_ref = mod.initialize_run(args_ref)

                    def fake_agent_ref(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        work_dir = Path(kwargs["work_dir"])
                        _write_orchestrator_plan(
                            work_dir,
                            id6="orc003",
                            setid="set003",
                            backlog_id6="bkl003",
                            completion_line=f"- {UNOWNED_LINE}",
                        )
                        _write_child_plan(
                            work_dir,
                            id6="chd001",
                            setid="set003",
                            order=1,
                            backlog_id6="bkl003",
                        )
                        _write_child_plan(
                            work_dir,
                            id6="chd002",
                            setid="set003",
                            order=2,
                            backlog_id6="bkl003",
                            deps="none",
                        )
                        return 0, "session-ref", rdir / "log.txt", ["cmd"]

                    def probe_double_ref(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        reply = (
                            f"ORCHESTRATOR: CONTAINS EXECUTIONS\nQUOTE: {UNOWNED_LINE}"
                        )
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    with _patch_host_agent(mod, fake_agent_ref), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double_ref
                    ):
                        with contextlib.redirect_stdout(
                            buf_ref
                        ), contextlib.redirect_stderr(buf_ref):
                            mod.run_queue(run_dir_ref, retry_incomplete=False)

                    state_ref = json.loads(
                        (run_dir_ref / "state.json").read_text(encoding="utf-8")
                    )
                    item_ref = state_ref["queue"][0]
                    self.assertEqual(item_ref["status"], "fail-gate")
                    branch = item_ref["preserved_branch"]
                    self.assertTrue(branch)

                    # 2. Merge preserved branch into main (simulating an earlier integrated handoff)
                    subprocess.run(
                        ["git", "merge", branch, "-m", "merge preserved handoff"],
                        cwd=repo,
                        check=True,
                    )

                    bkl_main_pre = list(
                        repo.glob(
                            ".aw/records/backlog/**/20261004-set003-01-bkl003-*.backlog.md"
                        )
                    )[0]
                    self.assertIn("/open/", str(bkl_main_pre).replace("\\", "/"))
                    self.assertIn(
                        "- Status: open", bkl_main_pre.read_text(encoding="utf-8")
                    )

                    # 3. Resume graduation in a new run
                    run_id_res = f"run-{host_label}-resumed"
                    cmd_res = [
                        "start",
                        "bkl003",
                        "--action",
                        "plan",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id_res,
                        "--retry-budget",
                        "1",
                    ]
                    args_res = mod.build_parser().parse_args(cmd_res)
                    buf_res = io.StringIO()
                    with contextlib.redirect_stdout(
                        buf_res
                    ), contextlib.redirect_stderr(buf_res):
                        run_dir_res = mod.initialize_run(args_res)

                    probe_calls_res: list[str] = []

                    def probe_double_res(
                        state: Any,
                        excerpt: str,
                        host: str,
                        repo: Path,
                        runner: Any = None,
                    ) -> tuple[str, str, tuple[str, ...]]:
                        probe_calls_res.append(host)
                        reply = "ORCHESTRATOR: CONTAINS NO EXECUTIONS"
                        cls = rs.classify_probe_reply(reply, excerpt=excerpt)
                        return cls.answer, reply, cls.quotes

                    prompt_captured: list[str] = []

                    def fake_agent_res(
                        state: Any,
                        rdir: Any,
                        item: Any,
                        plan_path: Any,
                        prompt_path: Any,
                        attempt_no: Any,
                        **kwargs: Any,
                    ) -> tuple[int, str, Path, list[str]]:
                        p_txt = Path(prompt_path).read_text(encoding="utf-8")
                        prompt_captured.append(p_txt)
                        work_dir = Path(kwargs["work_dir"])
                        orch_p = list(
                            work_dir.glob(".aw/records/plans/pending/*-orc003-*.ipd.md")
                        )[0]
                        txt = orch_p.read_text(encoding="utf-8")
                        txt = txt.replace(
                            f"- {UNOWNED_LINE}", f"- {UNOWNED_LINE}. Owner: chd002"
                        )
                        orch_p.write_text(txt, encoding="utf-8")
                        return 0, "session-res", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent_res), mock.patch.object(
                        rs, "ask_orchestrator_probe", probe_double_res
                    ):
                        with contextlib.redirect_stdout(
                            buf_res
                        ), contextlib.redirect_stderr(buf_res):
                            mod.run_queue(run_dir_res, retry_incomplete=False)

                    # Resume Assertions (E-03 / V-03)
                    self.assertTrue(prompt_captured)
                    self.assertIn("Continue this handoff", prompt_captured[0])
                    self.assertIn("orc003", prompt_captured[0])
                    self.assertIn(UNOWNED_LINE, prompt_captured[0])

                    state_res = json.loads(
                        (run_dir_res / "state.json").read_text(encoding="utf-8")
                    )
                    item_res = state_res["queue"][0]
                    self.assertEqual(item_res["status"], "executed")

                    findings_all = [
                        f
                        for att in item_res.get("attempts", [])
                        for f in att.get("findings_given", [])
                        + att.get("findings_after", [])
                    ]
                    self.assertFalse(
                        any(
                            isinstance(f, (list, tuple))
                            and f[0] == "BACKLOG-GRADUATE-COUNT"
                            for f in findings_all
                        ),
                        "Resume handoff must not report BACKLOG-GRADUATE-COUNT",
                    )

                    # Exactly one - Set: among active plans whose - From-Backlog: names bkl003
                    active_plans = list(repo.glob(".aw/records/plans/pending/*.ipd.md"))
                    linked_plans = [
                        p
                        for p in active_plans
                        if "- From-Backlog: bkl003" in p.read_text(encoding="utf-8")
                    ]
                    sets = {
                        re.search(
                            r"^- Set:\s*(\S+)", p.read_text(encoding="utf-8"), re.M
                        ).group(1)
                        for p in linked_plans
                    }
                    self.assertEqual(sets, {"set003"})
                    ids = {
                        re.search(
                            r"^- Id:\s*(\S+)", p.read_text(encoding="utf-8"), re.M
                        ).group(1)
                        for p in linked_plans
                    }
                    self.assertEqual(ids, {"orc003", "chd001", "chd002"})

                    self.assertEqual(len(probe_calls_res), 1)

                    bkl_main_post = list(
                        repo.glob(
                            ".aw/records/backlog/**/20261004-set003-01-bkl003-*.backlog.md"
                        )
                    )[0]
                    self.assertIn("/graduated/", str(bkl_main_post).replace("\\", "/"))
                    self.assertIn(
                        "- Status: graduated", bkl_main_post.read_text(encoding="utf-8")
                    )

                    orch_main_post = list(
                        repo.glob(".aw/records/plans/pending/*-orc003-*.ipd.md")
                    )[0]
                    orch_txt_post = orch_main_post.read_text(encoding="utf-8")
                    self.assertIn("- Coverage: pass", orch_txt_post)
                    self.assertTrue(coverage_record.is_current(orch_txt_post))

    def test_e05_one_predicate_parity(self) -> None:
        """Task group 3: cross-surface parity of the one readiness predicate across five surfaces."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            orch = _write_orchestrator_plan(
                repo, id6="orc005", setid="set005", backlog_id6="bkl005"
            )
            _write_child_plan(
                repo, id6="chd001", setid="set005", order=1, backlog_id6="bkl005"
            )
            _write_child_plan(
                repo,
                id6="chd002",
                setid="set005",
                order=2,
                backlog_id6="bkl005",
                deps="none",
            )

            # Pre-write coverage FAIL with one quote
            quotes = (UNOWNED_LINE,)
            coverage_record.write(
                orch,
                "fail",
                quotes=quotes,
                model="fixture",
                tool="test",
                repo=repo,
                commit=False,
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "pre-write coverage fail"],
                cwd=repo,
                check=True,
            )

            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path.cwd())

            # -------------------------------------------------------------
            # Surface 1: aw ipd set reviewed <id6> --yes --message ... --agent
            # -------------------------------------------------------------
            proc1 = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "set",
                    "reviewed",
                    "orc005",
                    "--dir",
                    str(repo),
                    "--yes",
                    "--message",
                    "attempt review",
                    "--agent",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc1.returncode, 1)
            lines1 = [line for line in proc1.stdout.splitlines() if line.strip()]
            self.assertTrue(lines1)
            payload1 = json.loads(lines1[-1])
            findings1 = payload1.get("data", {}).get("findings", [])
            self.assertTrue(findings1)
            s1_inner_code = findings1[0]["code"]
            s1_quote = findings1[0]["detail"]
            self.assertIn(UNOWNED_LINE, s1_quote)

            # -------------------------------------------------------------
            # Surface 2: aw ipd lint --phase review-finalize --agent <plan>
            # -------------------------------------------------------------
            proc2 = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "ipd",
                    "lint",
                    str(orch),
                    "--phase",
                    "review-finalize",
                    "--agent",
                    "--verbose",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertNotEqual(proc2.returncode, 0)
            lines2 = [line for line in proc2.stdout.splitlines() if line.strip()]
            self.assertTrue(lines2)
            payload2 = json.loads(lines2[-1])
            diags2 = payload2.get("diagnostics") or payload2.get("data", {}).get(
                "diagnostics", []
            )
            s408_diags = [d for d in diags2 if d.get("rule") == "IPD-S408"]
            self.assertTrue(s408_diags)
            d2_detail = s408_diags[0]["detail"]
            s2_inner_code = d2_detail.split()[0]
            self.assertIn(UNOWNED_LINE, d2_detail)

            # -------------------------------------------------------------
            # Surface 3: aw check plans --agent
            # -------------------------------------------------------------
            proc3 = subprocess.run(
                [
                    "python3",
                    "-m",
                    "agent_workflows",
                    "check",
                    "plans",
                    "--agent",
                    "--verbose",
                    "--dir",
                    str(repo),
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertNotEqual(proc3.returncode, 0)
            lines3 = [line for line in proc3.stdout.splitlines() if line.strip()]
            self.assertTrue(lines3)
            payload3 = json.loads(lines3[-1])
            diags3 = payload3.get("diagnostics") or payload3.get("data", {}).get(
                "diagnostics", []
            )
            orch_diags = [
                d
                for d in diags3
                if d.get("rule") == "check.orchestrator-not-review-ready"
            ]
            self.assertTrue(orch_diags)
            d3_detail = orch_diags[0]["detail"]
            s3_inner_code = d3_detail.split()[0]
            self.assertIn(UNOWNED_LINE, d3_detail)

            # Assert inner finding codes agree on surfaces 1-3
            self.assertEqual(s1_inner_code, "coverage-fail")
            self.assertEqual(s2_inner_code, "coverage-fail")
            self.assertEqual(s3_inner_code, "coverage-fail")

            # -------------------------------------------------------------
            # Surface 4: Backlog production run (in process)
            # -------------------------------------------------------------
            with tempfile.TemporaryDirectory() as td4:
                repo4 = _make_test_repo(Path(td4))
                _write_backlog_item(repo4, id6="bkl054", setid="set054", gate="rel001")
                subprocess.run(["git", "add", "."], cwd=repo4, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "add backlog"], cwd=repo4, check=True
                )

                cmd4 = [
                    "start",
                    "bkl054",
                    "--action",
                    "plan",
                    "--repo",
                    str(repo4),
                    "--run-id",
                    "run-oc-parity4",
                    "--retry-budget",
                    "0",
                ]
                args4 = oc_runipd.build_parser().parse_args(cmd4)
                buf4 = io.StringIO()
                with contextlib.redirect_stdout(buf4), contextlib.redirect_stderr(buf4):
                    run_dir4 = oc_runipd.initialize_run(args4)

                probe_calls_4: list[str] = []

                def fake_probe_4(
                    state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
                ) -> tuple[str, str, tuple[str, ...]]:
                    probe_calls_4.append(host)
                    return (rs.PROBE_ANSWER_NO_EXECUTIONS, "no executions", ())

                def fake_agent_4(
                    state: Any,
                    rdir: Any,
                    item: Any,
                    plan_path: Any,
                    prompt_path: Any,
                    attempt_no: Any,
                    **kwargs: Any,
                ) -> tuple[int, str, Path, list[str]]:
                    work_dir = Path(kwargs["work_dir"])
                    orch_p = _write_orchestrator_plan(
                        work_dir, id6="orc054", setid="set054", backlog_id6="bkl054"
                    )
                    _write_child_plan(
                        work_dir,
                        id6="chd001",
                        setid="set054",
                        order=1,
                        backlog_id6="bkl054",
                    )
                    _write_child_plan(
                        work_dir,
                        id6="chd002",
                        setid="set054",
                        order=2,
                        backlog_id6="bkl054",
                        deps="none",
                    )
                    coverage_record.write(
                        orch_p,
                        "fail",
                        quotes=quotes,
                        model="fixture",
                        tool="test",
                        repo=work_dir,
                        commit=False,
                    )
                    return 0, "session-4", rdir / "log.txt", ["cmd"]

                with _patch_host_agent(oc_runipd, fake_agent_4), mock.patch.object(
                    rs, "ask_orchestrator_probe", fake_probe_4
                ):
                    with contextlib.redirect_stdout(buf4), contextlib.redirect_stderr(
                        buf4
                    ):
                        oc_runipd.run_queue(run_dir4, retry_incomplete=False)

                state4 = json.loads(
                    (run_dir4 / "state.json").read_text(encoding="utf-8")
                )
                item4 = state4["queue"][0]
                self.assertEqual(item4["status"], "fail-gate")
                refusal4 = item4.get("refusal") or {}
                s4_surface_code = refusal4.get("code")
                s4_reason = refusal4.get("reason", "")
                self.assertEqual(s4_surface_code, "BACKLOG-GRADUATE-SET")
                self.assertIn("orc054", s4_reason)
                self.assertIn(UNOWNED_LINE, s4_reason)
                self.assertEqual(
                    len(probe_calls_4),
                    0,
                    "Surface 4 must make 0 probe calls when fail record is current",
                )

            # -------------------------------------------------------------
            # Surface 5: runner_shared.dispatch_orchestrator_item (in process)
            # -------------------------------------------------------------
            with tempfile.TemporaryDirectory() as td5:
                repo5 = _make_test_repo(Path(td5))
                orch5 = _write_orchestrator_plan(
                    repo5, id6="orc055", setid="set055", backlog_id6="bkl055"
                )
                _write_child_plan(
                    repo5, id6="chd001", setid="set055", order=1, backlog_id6="bkl055"
                )
                _write_child_plan(
                    repo5,
                    id6="chd002",
                    setid="set055",
                    order=2,
                    backlog_id6="bkl055",
                    deps="none",
                )

                # Move children to executed/
                exec_dir5 = repo5 / ".aw" / "records" / "plans" / "executed"
                exec_dir5.mkdir(parents=True, exist_ok=True)
                for cid in ("chd001", "chd002"):
                    cp = list(
                        repo5.glob(f".aw/records/plans/pending/*-{cid}-*.ipd.md")
                    )[0]
                    cp_txt = cp.read_text(encoding="utf-8").replace(
                        "- Status: to-review", "- Status: executed"
                    )
                    (exec_dir5 / cp.name).write_text(cp_txt, encoding="utf-8")
                    cp.unlink()

                coverage_record.write(
                    orch5,
                    "fail",
                    quotes=quotes,
                    model="fixture",
                    tool="test",
                    repo=repo5,
                    commit=False,
                )
                subprocess.run(["git", "add", "."], cwd=repo5, check=True)
                subprocess.run(
                    ["git", "commit", "-qm", "dispatch setup"], cwd=repo5, check=True
                )

                state5 = {
                    "schema_version": 1,
                    "run_id": "run-dispatch-parity",
                    "repo": str(repo5),
                    "options": {},
                    "queue": [
                        {
                            "position": 1,
                            "id6": "orc055",
                            "setid": "set055",
                            "action": "orchestrate",
                            "kind": "orchestrator",
                            "status": "approved",
                            "dependencies": [],
                            "attempts": [],
                        }
                    ],
                }
                run_dir5 = repo5 / "run-dispatch-parity"
                run_dir5.mkdir(parents=True, exist_ok=True)
                (run_dir5 / "state.json").write_text(
                    json.dumps(state5), encoding="utf-8"
                )
                item5 = state5["queue"][0]

                probe_calls_5: list[str] = []

                def fake_probe_5(
                    state: Any, excerpt: str, host: str, repo: Path, runner: Any = None
                ) -> tuple[str, str, tuple[str, ...]]:
                    probe_calls_5.append(host)
                    return (rs.PROBE_ANSWER_NO_EXECUTIONS, "no executions", ())

                dec5 = rs.dispatch_orchestrator_item(
                    repo5,
                    run_dir5,
                    state5,
                    item5,
                    actor="tester",
                    terminal_states={"executed", "failed", "fail-depend"},
                    success_states={"executed"},
                    asker=fake_probe_5,
                )

                self.assertEqual(dec5.outcome, rs.ORCH_DISPATCH_TERMINATE)
                s5_surface_code = dec5.reason
                self.assertEqual(s5_surface_code, rs.ORCH_REASON_FINALIZE_REFUSED)
                self.assertIn("retirement re-check refused: orc055:", dec5.detail)
                self.assertIn(UNOWNED_LINE, dec5.detail)
                self.assertEqual(
                    len(probe_calls_5),
                    0,
                    "Surface 5 must make 0 probe calls when fail record is current",
                )


if __name__ == "__main__":
    unittest.main()
