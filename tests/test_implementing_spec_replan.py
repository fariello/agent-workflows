"""Behavioral tests for implementing spec re-planning (plan 2hgxi1 / backlog 2wkzf7).

Validates E-06:
(1) spec_uncited_trace_ids predicate coverage across post-cutover, deferred, executed,
    superseded, unqualified, and grandfathered specs.
(2) runner_action parity: returns 'plan' only for ('spec', 'implementing', uncited_trace_ids=True)
    and leaves every other (type, status) answer unchanged.
(3) End-to-end success on both hosts (oc and agy): item ends executed, spec remains implementing,
    history records stage note, next actions populated, path-scoped commit.
(4) End-to-end refusal on both hosts (oc and agy): failing SPEC-PLAN-TRACE leaves spec byte-identical.
(5) Unchanged dispatch: fully-cited post-cutover and grandfathered implementing specs freeze-refuse
    as undetermined action.
(6) --action plan --prepare-only admitted for eligible spec and refused with reworded legality message
    for ineligible spec.
(7) classify_paths previews eligible spec as 'plan'.
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
    run_selection_policy,
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
    status: str = "implementing",
    title: str = "Test Spec",
    slug: str = "test-spec",
    gate: str | None = None,
    filename_date: str = "20261001",
    spec_date: str = "2026-10-01",
    requirements: list[str] | None = None,
    acceptance: list[str] | None = None,
) -> Path:
    specs_dir = repo / ".aw" / "records" / "specs" / status
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


def _write_plan(
    repo: Path,
    *,
    id6: str,
    spec_id6: str | None = "spc001",
    setid: str = "demo",
    order: int = 1,
    status: str = "to-review",
    bucket: str = "pending",
    filename_date: str = "20261001",
    e_items: list[str] | None = None,
    v_items: list[str] | None = None,
) -> Path:
    dir_path = repo / ".aw" / "records" / "plans" / bucket
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{filename_date}-{setid}-{order:02d}-{id6}-test-plan.ipd.md"

    spec_line = f"- From-Spec: {spec_id6}\n" if spec_id6 else ""
    highest_e = f"{len(e_items):02d}" if e_items else "01"

    if e_items:
        e_body_lines = []
        for i, text in enumerate(e_items, 1):
            e_body_lines.append(
                f"- [ ] E-{i:02d} {text}\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"
            )
        e_body = "\n\n".join(e_body_lines)
    else:
        e_body = """- [ ] E-01 Work item\n  - Depends on: none\n  - Expected outcome: done\n  - Execution state: pending"""

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
        v_body = """- [ ] V-01 validates E-01\n  - Required evidence: check.\n  - Observed evidence:\n  - Result: pending"""

    content = f"""# IPD: Test Plan {id6}

- Date: 2026-10-01
- Kind: child
- Concern: Test concern for plan {id6}.
- Scope: Test scope for plan {id6}.
- Scope-Paths: README.md
- Status: {status}
{spec_line}- Set: {setid}
- Order: {order}
- Highest E allocated: {highest_e}
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: none

## Workflow history
- 2026-10-01 {status} (test): created.

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


class TestImplementingSpecReplan(unittest.TestCase):
    """Behavioral tests for implementing spec re-planning (E-06)."""

    def test_case_1_predicate_coverage(self):
        """Case (1): spec_uncited_trace_ids predicate coverage.
        Post-cutover spec declaring R-1, R-2, R-3 [Deferred], AC-1 with executed plan
        citing 'spc R-1' and 'spc AC-1' -> returns ['R-2'].
        Superseded plan citing R-2 -> does not change it.
        Unqualified citation of R-2 -> does not cover it.
        Grandfathered 20260927 spec -> returns [].
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _make_test_repo(repo)

            # Post-cutover spec
            _write_spec(
                repo,
                id6="spc001",
                filename_date="20261001",
                spec_date="2026-10-01",
                requirements=["R-1 First", "R-2 Second", "R-3 [Deferred] Third"],
                acceptance=["AC-1 First criterion"],
            )

            # Linked plan in executed/ citing spc001 R-1 and spc001 AC-1
            _write_plan(
                repo,
                id6="pln001",
                spec_id6="spc001",
                status="executed",
                bucket="executed",
                e_items=["`spc001` R-1 Implement first requirement"],
                v_items=["`spc001` AC-1 Validate first criterion"],
            )

            uncited = production_checks.spec_uncited_trace_ids(repo, "spc001")
            self.assertEqual(uncited, ["R-2"])

            # Superseded plan citing R-2 does NOT cover it
            _write_plan(
                repo,
                id6="pln002",
                spec_id6="spc001",
                status="superseded",
                bucket="superseded",
                e_items=["`spc001` R-2 Implement second requirement"],
            )
            uncited_after_sup = production_checks.spec_uncited_trace_ids(repo, "spc001")
            self.assertEqual(uncited_after_sup, ["R-2"])

            # Unqualified R-2 citation in an active plan does NOT cover it
            _write_plan(
                repo,
                id6="pln003",
                spec_id6="spc001",
                status="to-review",
                bucket="pending",
                e_items=["R-2 Unqualified citation"],
            )
            uncited_unqual = production_checks.spec_uncited_trace_ids(repo, "spc001")
            self.assertEqual(uncited_unqual, ["R-2"])

            # Grandfathered spec returns []
            _write_spec(
                repo,
                id6="spcold",
                filename_date="20260927",
                spec_date="2026-09-27",
                requirements=["R-1 First", "R-2 Second"],
                acceptance=["AC-1 First criterion"],
            )
            uncited_old = production_checks.spec_uncited_trace_ids(repo, "spcold")
            self.assertEqual(uncited_old, [])

    def test_case_2_runner_action_parity(self):
        """Case (2): runner_action returns 'plan' only for ('spec', 'implementing', uncited_trace_ids=True)
        and leaves every other (type, status) answer unchanged.
        """
        # Refinement works
        self.assertEqual(
            run_selection_policy.runner_action(
                "spec", "implementing", uncited_trace_ids=True
            ),
            "plan",
        )
        self.assertEqual(
            run_selection_policy.runner_action(
                "spec", "implementing", uncited_trace_ids=False
            ),
            "undetermined",
        )
        self.assertEqual(
            run_selection_policy.runner_action(
                "spec", "implementing", uncited_trace_ids=None
            ),
            "undetermined",
        )
        self.assertEqual(
            run_selection_policy.runner_action("spec", "implementing"),
            "undetermined",
        )

        # Check parity across all other table entries
        for spec_type, table in run_selection_policy._ACTION_TABLES.items():
            for status in table.keys():
                if spec_type == "spec" and status == "implementing":
                    continue
                unrefined = run_selection_policy.runner_action(spec_type, status)
                with_kw = run_selection_policy.runner_action(
                    spec_type, status, uncited_trace_ids=True
                )
                self.assertEqual(
                    unrefined,
                    with_kw,
                    f"Mismatch for ({spec_type}, {status}): {unrefined} vs {with_kw}",
                )

    def test_case_3_end_to_end_success(self):
        """Case (3): End to end success on both hosts.
        Fixture spec in implementing with R-1 cited and R-2 uncited.
        Fake agent writes conformant plan citing spc003 R-2.
        Item ends executed, spec file remains in specs/implementing/ with - Status: implementing,
        history gains note, generated_next_actions names plan, git commit touches only spec.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    _write_spec(
                        repo,
                        id6="spc003",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        status="implementing",
                        requirements=[
                            "R-1 First",
                            "R-2 Second",
                            "R-3 [Deferred] Third",
                        ],
                        acceptance=["AC-1 First criterion"],
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        spec_id6="spc003",
                        status="executed",
                        bucket="executed",
                        e_items=["`spc003` R-1 Implement first"],
                        v_items=["`spc003` AC-1 Validate first"],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "initial spec and executed plan"],
                        cwd=repo,
                        check=True,
                    )

                    run_id = f"run-{host_label}-succ"
                    cmd = [
                        "start",
                        "spc003",
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
                        _write_plan(
                            target,
                            id6="plnnew",
                            spec_id6="spc003",
                            status="to-review",
                            bucket="pending",
                            e_items=["`spc003` R-2 Cover second requirement"],
                        )
                        return 0, "session-01", rdir / "log.txt", ["cmd"]

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

                    # generated_next_actions names plnnew
                    next_actions = item.get("generated_next_actions") or []
                    self.assertEqual(len(next_actions), 1)
                    self.assertEqual(next_actions[0]["id6"], "plnnew")

                    # Spec file is still under specs/implementing/
                    spec_files = list(
                        repo.glob(".aw/records/specs/**/20261001-spc003*.spec.md")
                    )
                    self.assertEqual(len(spec_files), 1)
                    spec_p = spec_files[0]
                    self.assertIn("/implementing/", str(spec_p).replace("\\", "/"))

                    spec_text = spec_p.read_text(encoding="utf-8")
                    self.assertIn("- Status: implementing", spec_text)
                    self.assertNotIn("- Status: implemented", spec_text)
                    self.assertIn(
                        f"note (aw specs): stage planned by run {run_id}:", spec_text
                    )

                    # Git log shows note commit touching only spec file
                    log_res = subprocess.check_output(
                        ["git", "log", "-n", "1", "--stat", "--oneline"],
                        cwd=repo,
                        text=True,
                    )
                    self.assertIn(
                        "note(spec): record planned stage for spc003", log_res
                    )
                    self.assertIn(
                        "20261001-spc003-01-spc003-test-spec.spec.md", log_res
                    )
                    self.assertNotIn(".ipd.md", log_res)

    def test_case_4_end_to_end_refusal(self):
        """Case (4): End to end refusal when fake agent does not cite R-2.
        Fails with SPEC-PLAN-TRACE naming R-2; spec file is byte-identical.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    spec_path = _write_spec(
                        repo,
                        id6="spc004",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        status="implementing",
                        requirements=["R-1 First", "R-2 Second"],
                        acceptance=["AC-1 First criterion"],
                    )
                    _write_plan(
                        repo,
                        id6="pln001",
                        spec_id6="spc004",
                        status="executed",
                        bucket="executed",
                        e_items=["`spc004` R-1 Implement first"],
                        v_items=["`spc004` AC-1 Validate first"],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "initial spec and executed plan"],
                        cwd=repo,
                        check=True,
                    )
                    before_text = spec_path.read_text(encoding="utf-8")

                    run_id = f"run-{host_label}-fail"
                    cmd = [
                        "start",
                        "spc004",
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
                        # Fails to cite R-2
                        _write_plan(
                            target,
                            id6="plnnew",
                            spec_id6="spc004",
                            status="to-review",
                            bucket="pending",
                            e_items=["Unrelated work"],
                        )
                        return 0, "session-01", rdir / "log.txt", ["cmd"]

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

                    # Spec file is byte-identical
                    after_text = spec_path.read_text(encoding="utf-8")
                    self.assertEqual(before_text, after_text)

    def test_case_5_unchanged_dispatch(self):
        """Case (5): Unchanged dispatch: fully-cited post-cutover spec and grandfathered spec
        both refuse at freeze with [RUN-UNDETERMINED-ACTION] and create no run directory.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    # Fully cited post-cutover
                    _write_spec(
                        repo,
                        id6="spcful",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        status="implementing",
                        requirements=["R-1 First"],
                        acceptance=["AC-1 First"],
                    )
                    _write_plan(
                        repo,
                        id6="plnful",
                        spec_id6="spcful",
                        status="executed",
                        bucket="executed",
                        e_items=["`spcful` R-1 Covered"],
                        v_items=["`spcful` AC-1 Covered"],
                    )

                    # Grandfathered spec with uncited IDs
                    _write_spec(
                        repo,
                        id6="spcold",
                        filename_date="20260927",
                        spec_date="2026-09-27",
                        status="implementing",
                        requirements=["R-1 Uncited"],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add specs"], cwd=repo, check=True
                    )

                    for target_id6 in ("spcful", "spcold"):
                        cmd = [
                            "start",
                            target_id6,
                            "--repo",
                            str(repo),
                            "--run-id",
                            f"run-{host_label}-{target_id6}",
                        ]
                        args = mod.build_parser().parse_args(cmd)
                        buf = io.StringIO()
                        with self.assertRaises(runner_shared.DriverError) as cm:
                            with contextlib.redirect_stdout(
                                buf
                            ), contextlib.redirect_stderr(buf):
                                mod.initialize_run(args)
                        self.assertIn("RUN-UNDETERMINED-ACTION", str(cm.exception))

    def test_case_6_action_plan_preflight(self):
        """Case (6): --action plan --prepare-only is admitted for eligible spec
        and refused with reworded legality sentence for fully-cited one.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    # Eligible spec
                    _write_spec(
                        repo,
                        id6="spceli",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        status="implementing",
                        requirements=["R-1 Uncited"],
                    )

                    # Fully cited spec
                    _write_spec(
                        repo,
                        id6="spcful",
                        filename_date="20261001",
                        spec_date="2026-10-01",
                        status="implementing",
                        requirements=["R-1 First"],
                    )
                    _write_plan(
                        repo,
                        id6="plnful",
                        spec_id6="spcful",
                        status="executed",
                        bucket="executed",
                        e_items=["`spcful` R-1 Covered"],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "add specs"], cwd=repo, check=True
                    )

                    # Admitted for eligible spec
                    cmd_ok = [
                        "start",
                        "spceli",
                        "--action",
                        "plan",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--run-id",
                        f"run-{host_label}-prep-ok",
                    ]
                    args_ok = mod.build_parser().parse_args(cmd_ok)
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(
                        buf
                    ):
                        run_dir = mod.initialize_run(args_ok)
                    self.assertTrue(run_dir.is_dir())

                    # Refused for fully cited spec
                    cmd_fail = [
                        "start",
                        "spcful",
                        "--action",
                        "plan",
                        "--prepare-only",
                        "--repo",
                        str(repo),
                        "--run-id",
                        f"run-{host_label}-prep-fail",
                    ]
                    args_fail = mod.build_parser().parse_args(cmd_fail)
                    with self.assertRaises(runner_shared.DriverError) as cm:
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            mod.initialize_run(args_fail)
                    err_msg = str(cm.exception)
                    self.assertIn(
                        "--action plan is illegal for 1 selected item(s)", err_msg
                    )
                    self.assertIn(
                        "Plan is the next legal action only for an approved spec, an implementing spec with uncited non-deferred TRACE ids, or an open backlog item",
                        err_msg,
                    )

    def test_case_7_classify_paths_preview(self):
        """Case (7): classify_paths previews eligible spec as 'plan'."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _make_test_repo(repo)

            p_elig = _write_spec(
                repo,
                id6="spceli",
                filename_date="20261001",
                spec_date="2026-10-01",
                status="implementing",
                requirements=["R-1 Uncited"],
            )
            p_ful = _write_spec(
                repo,
                id6="spcful",
                filename_date="20261001",
                spec_date="2026-10-01",
                status="implementing",
                requirements=["R-1 First"],
            )
            _write_plan(
                repo,
                id6="plnful",
                spec_id6="spcful",
                status="executed",
                bucket="executed",
                e_items=["`spcful` R-1 Covered"],
            )

            classification = run_selection_policy.classify_paths(repo, [p_elig, p_ful])
            item_by_id = {it.path.name.split("-")[1]: it for it in classification.items}
            self.assertEqual(item_by_id["spceli"].action, "plan")
            self.assertEqual(item_by_id["spcful"].action, "undetermined")

            preview = run_selection_policy.render_action_preview(classification)
            self.assertIn("1 plan, 1 undetermined", preview)


if __name__ == "__main__":
    unittest.main()
