"""End-to-end behavioral tests for companion-safe runner prompts, carrier checks,
companion record routing, and the fail-closed public-target merge guard.

Covers IPD v8tqje (Set companion-bugs, Order 03; backlog rvxmzz items 6, 7, and 8).
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import (
    agy_runipd,
    lane_containment,
    oc_runipd,
    project_context,
    runner_shared,
    storage,
    worktree_lease,
)
from tests import support
from tests.support import init_repo


def _make_env(tmp_root: Path) -> dict[str, str]:
    home = tmp_root / "home"
    aw_home = tmp_root / "aw_home"
    home.mkdir(parents=True, exist_ok=True)
    aw_home.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["AW_NO_REEXEC"] = "1"
    env["HOME"] = str(home)
    env["AW_HOME"] = str(aw_home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["AW_CONFIG_DIR"] = str(home / ".config" / "agent-workflows")
    env["GIT_AUTHOR_NAME"] = "Test Author"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "Test Committer"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    return env


@contextlib.contextmanager
def _patched_env(env: dict[str, str]):
    keys = (
        "HOME",
        "AW_HOME",
        "XDG_CONFIG_HOME",
        "AW_CONFIG_DIR",
        "AW_NO_REEXEC",
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
    )
    saved = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ[k] = env[k]
    project_context._RESOLVE_CTX_CACHE.clear()
    project_context._resolve_stored_physical_classes_cached.cache_clear()
    try:
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        project_context._RESOLVE_CTX_CACHE.clear()
        project_context._resolve_stored_physical_classes_cached.cache_clear()


def _provision_companion_repos(
    td_path: Path,
    *,
    init_companion_git: bool = True,
    initial_companion_commit: bool = True,
    commit_project_json: bool = True,
) -> tuple[Path, Path, dict[str, str]]:
    """Provision real target + companion repositories configured as public-target-private-companion."""
    target = td_path / "target_repo"
    companion = td_path / "companion_repo"
    init_repo(target)
    (target / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    support.git(target, "add", "app.py")
    support.git(target, "commit", "-m", "initial target commit")

    companion.mkdir(parents=True, exist_ok=True)
    if init_companion_git:
        init_repo(companion)

    env = _make_env(td_path)
    (target / ".aw" / "config").mkdir(parents=True, exist_ok=True)
    (target / ".aw" / "system").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "plans" / "pending").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "plans" / "executed").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "reviews").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "specs").mkdir(parents=True, exist_ok=True)
    (companion / "records" / "backlog" / "open").mkdir(parents=True, exist_ok=True)

    proj_data = {
        "schema_version": 2,
        "preset": "public-target-private-companion",
        "delivery_mode": "tracked",
        "records_backend": "companion",
        "git_policies": {"records": "companion-git"},
        "cutovers": {
            "durable_carrier": "2026-01-01",
            "carrier_obligations": "2026-01-01",
        },
    }
    proj_json = target / ".aw" / "config" / "project.json"
    proj_json.write_text(json.dumps(proj_data, indent=2) + "\n", encoding="utf-8")
    local_json = target / ".aw" / "config" / "local.json"
    local_json.write_text(
        json.dumps({"companion_dir": companion.resolve().as_posix()}, indent=2) + "\n",
        encoding="utf-8",
    )
    storage.write_local_attachment_record(
        target, companion, "test-proj", ["config", "durable_state", "records"]
    )
    (target / ".aw" / ".gitignore").write_text(
        "/config/local.json\n/state/\n/records/\n", encoding="utf-8"
    )
    stage_paths = [".aw/.gitignore"]
    if commit_project_json:
        stage_paths.append(".aw/config/project.json")
    subprocess.run(
        ["git", "-C", str(target), "add", "-f", *stage_paths],
        env=env,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(target), "commit", "-m", "commit companion target config"],
        env=env,
        capture_output=True,
        check=True,
    )

    if init_companion_git and initial_companion_commit:
        (companion / "records" / "README.md").write_text(
            "# Companion records\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(companion), "add", "--", "records/README.md"],
            env=env,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(companion), "commit", "-m", "initial companion records"],
            env=env,
            capture_output=True,
            check=True,
        )

    return target, companion, env


def _add_lane_worktree(
    target: Path, lane_id: str, env: dict[str, str]
) -> tuple[Path, worktree_lease.WorktreeHandle]:
    base = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    branch = f"aw/lane/{lane_id}"
    wt = target.parent / f"wt-{lane_id}"
    subprocess.run(
        ["git", "-C", str(target), "worktree", "add", "-b", branch, str(wt), base],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    handle = worktree_lease.WorktreeHandle(
        lane_id=lane_id, path=wt, branch=branch, base_commit=base
    )
    return wt, handle


def _plan_text(
    *,
    id6: str,
    setid: str = "cmpset",
    order: int = 1,
    slug: str = "sample",
    status: str = "to-review",
    deferred_block: str = "None.",
    extra_history: str = "",
) -> str:
    if not extra_history and status in ("reviewed", "approved", "auto-approved"):
        extra_history = "- 2026-11-21 /plan-review (test): APPROVED"
    hist = f"\n{extra_history}" if extra_history else ""
    readiness_line = (
        "- Readiness: go-pending-approval\n"
        if status in ("reviewed", "approved", "auto-approved")
        else ""
    )
    return (
        f"# IPD: Sample plan {id6}\n\n"
        f"- Date: 2026-11-21\n"
        f"- Kind: child\n"
        f"- Concern: {slug}\n"
        f"- Scope: `app.py`\n"
        f"- Scope-Paths: app.py\n"
        f"- Status: {status}\n"
        f"{readiness_line}"
        f"- Short-Description: Sample companion plan {id6}\n"
        f"- Work-Kind: bug\n"
        f"- Priority: high\n"
        f"- Set: {setid}\n"
        f"- Order: {order}\n"
        f"- Highest E allocated: 01\n"
        f"- Author: Test\n"
        f"- Id: {id6}\n\n"
        f"## Workflow history\n\n"
        f"- 2026-11-21 {status} (test): seeded.{hist}\n\n"
        f"## Goal\n\n"
        f"Update `app.py` behavior safely.\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"- [ ] E-01 Update `app.py`\n"
        f"  - Depends on: none\n"
        f"  - Expected outcome: `app.py` exports `VALUE = 2`.\n"
        f"  - Execution state: pending\n\n"
        f"## Project conventions discovered (Step 0)\n\n"
        f"- `app.py` exports `VALUE`.\n\n"
        f"## Findings\n\n"
        f"1. `app.py` currently exports `VALUE = 1` instead of `2`.\n\n"
        f"## Proposed changes (ordered, validatable)\n\n"
        f"1. Update `app.py` to export `VALUE = 2`.\n\n"
        f"## Deferred / out of scope (with reason)\n\n"
        f"{deferred_block}\n\n"
        f"## Scope check\n\n"
        f"- Over-scope: none.\n"
        f"- Under-scope: none.\n\n"
        f"## Required tests / validation\n\n"
        f"- `python3 -m pytest`\n\n"
        f"## Spec / documentation sync\n\n"
        f"- N/A.\n\n"
        f"## Open questions\n\n"
        f"None.\n\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [ ] V-01 validates E-01\n"
        f"  - Required evidence: Pasted test output proving `VALUE == 2`.\n"
        f"  - Observed evidence:\n"
        f"  - Result: pending\n\n"
        f"## Approval and execution gate\n\n"
        f"- Size assessment: standard\n"
        f"- Cohesion rationale: not required\n\n"
        f"Commit only modified paths through `aw commit {id6} -- <paths>` and never push.\n"
    )


def _git_head(repo: Path, env: dict[str, str]) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _passing_validation_runner(_combined_diff: str, _merged_files: Any) -> bool:
    return True


class CompanionPromptPurityTests(unittest.TestCase):
    """E-01 / V-01: R1 prompt purity, writable lane staging, R5.1a seal, and non-isolated invariance."""

    def test_stage_companion_artifact_is_writable_link_independent_and_rejects_escapes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, _handle = _add_lane_worktree(target, "stg001", env)
            records_root = companion / "records"
            plan_path = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-stg001-sample.ipd.md"
            )
            plan_path.write_text(_plan_text(id6="stg001"), encoding="utf-8")

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_path, records_root
                )
                self.assertEqual(
                    staged.relative_to(wt).as_posix(),
                    ".aw/records/plans/pending/20261121-cmpset-01-stg001-sample.ipd.md",
                )
                self.assertTrue(staged.is_file())
                self.assertFalse(staged.is_symlink())
                st_staged = os.stat(staged, follow_symlinks=False)
                st_src = os.stat(plan_path, follow_symlinks=False)
                self.assertEqual(stat.S_IMODE(st_staged.st_mode), 0o644)
                self.assertEqual(st_staged.st_nlink, 1)
                self.assertNotEqual(
                    (st_staged.st_dev, st_staged.st_ino),
                    (st_src.st_dev, st_src.st_ino),
                )
                # Writable copy allows in-place edits without mutating companion source
                staged.write_text("# edited in lane\n", encoding="utf-8")
                self.assertIn(
                    "Sample plan stg001", plan_path.read_text(encoding="utf-8")
                )

                # Escape attempts are rejected
                outside_file = td_path / "outside.md"
                outside_file.write_text("secret\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    lane_containment.stage_companion_lane_artifact(
                        wt, outside_file, records_root
                    )
                with self.assertRaises(ValueError):
                    lane_containment.stage_companion_lane_artifact(
                        wt,
                        records_root / "plans" / ".." / ".." / "outside.md",
                        records_root,
                    )
                # Symlink inside lane staging path is rejected
                wt_sym, _ = _add_lane_worktree(target, "sym001", env)
                (wt_sym / ".aw").mkdir(parents=True, exist_ok=True)
                (wt_sym / ".aw" / "records").symlink_to(records_root)
                with self.assertRaises(ValueError):
                    lane_containment.stage_companion_lane_artifact(
                        wt_sym, plan_path, records_root
                    )

    def test_companion_prompts_satisfy_r1_purity_preserve_r5_seal_and_non_isolated(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, _handle = _add_lane_worktree(target, "pur001", env)
            records_root = companion / "records"
            plan_path = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-pur001-sample.ipd.md"
            )
            plan_path.write_text(_plan_text(id6="pur001"), encoding="utf-8")
            spec_path = (
                records_root / "specs" / "20261121-sp1111-01-sp1111-sample.spec.md"
            )
            spec_path.write_text(
                "# Spec: sample\n\n- Id: sp1111\n- Status: approved\n", encoding="utf-8"
            )
            backlog_path = (
                records_root
                / "backlog"
                / "open"
                / "20261121-cmpset-01-bk2222-sample.backlog.md"
            )
            backlog_path.write_text(
                "- Id: bk2222\n- Status: open\n- Summary: sample\n", encoding="utf-8"
            )

            run_dir = td_path / "run-20261121T150000Z-9999"
            run_dir.mkdir(parents=True, exist_ok=True)
            state: dict[str, Any] = {
                "run_id": run_dir.name,
                "repo": str(target),
                "options": {"self_finalize": True},
            }
            item: dict[str, Any] = {
                "position": 1,
                "id6": "pur001",
                "setid": "cmpset",
                "artifact_type": "ipd",
                "attempts": [{"number": 1}],
            }

            with _patched_env(env):
                # Direct calls with external companion paths must stage and satisfy R1 purity
                review_prompt = runner_shared.build_review_prompt(
                    item, state, run_dir, plan_path, target, lane_root=wt
                )
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(review_prompt, wt), []
                )
                self.assertNotIn(str(companion), review_prompt)
                self.assertIn(
                    "/plan-review .aw/records/plans/pending/20261121-cmpset-01-pur001-sample.ipd.md",
                    review_prompt,
                )

                exec_prompt = runner_shared.build_prompt(
                    item,
                    state,
                    run_dir,
                    plan_path,
                    recovery=False,
                    lane_root=wt,
                    labels=runner_shared.AGY_HOST_LABELS,
                )
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(exec_prompt, wt), []
                )
                self.assertNotIn(str(companion), exec_prompt)
                self.assertIn(
                    "Plan file at launch: .aw/records/plans/pending/20261121-cmpset-01-pur001-sample.ipd.md",
                    exec_prompt,
                )

                spec_item = {"position": 2, "id6": "sp1111", "artifact_type": "spec"}
                spec_prompt = runner_shared.build_spec_production_prompt(
                    spec_item, state, run_dir, spec_path, target, lane_root=wt
                )
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(spec_prompt, wt), []
                )
                self.assertNotIn(str(companion), spec_prompt)
                self.assertIn(
                    ".aw/records/specs/20261121-sp1111-01-sp1111-sample.spec.md",
                    spec_prompt,
                )

                backlog_item = {
                    "position": 3,
                    "id6": "bk2222",
                    "artifact_type": "backlog",
                }
                backlog_prompt = runner_shared.build_backlog_production_prompt(
                    backlog_item, state, run_dir, backlog_path, target, lane_root=wt
                )
                self.assertEqual(
                    lane_containment.absolute_paths_outside_lane(backlog_prompt, wt), []
                )
                self.assertNotIn(str(companion), backlog_prompt)
                self.assertIn(
                    ".aw/records/backlog/open/20261121-cmpset-01-bk2222-sample.backlog.md",
                    backlog_prompt,
                )

                # R5.1a sealed audit snapshot remains 0444 and link-independent
                staged_plan = (
                    wt
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20261121-cmpset-01-pur001-sample.ipd.md"
                )
                manifest = lane_containment.materialize_lane_inputs(
                    lane_root=wt,
                    plan_path=staged_plan,
                    runbook_path=None,
                    repo=wt,
                )
                self.assertTrue(
                    lane_containment.verify_lane_input_manifest(wt).conforming
                )
                self.assertTrue(lane_containment.verify_lane_input_seal(wt).sealed)
                self.assertTrue(
                    lane_containment.verify_link_independence(wt).independent
                )
                sealed_entry = manifest.entry(lane_containment.INPUT_CLASS_PLAN)
                assert sealed_entry is not None
                with self.assertRaises(PermissionError):
                    (wt / sealed_entry.path).write_text("clobber", encoding="utf-8")

                # collect_lane_submissions must NOT overwrite agent edits to staged plan
                staged_plan.write_text("# modified by agent\n", encoding="utf-8")
                lane_containment.collect_lane_submissions(
                    run_dir=run_dir,
                    item=item,
                    run_id=run_dir.name,
                    lane_root=wt,
                    plan_path=plan_path,
                )
                self.assertEqual(
                    staged_plan.read_text(encoding="utf-8"), "# modified by agent\n"
                )
                # Subsequent retry/recovery staging with overwrite=False preserves lane edits
                re_resolved = lane_containment.resolve_companion_lane_path(
                    wt, plan_path, repo=target, overwrite=False
                )
                self.assertEqual(re_resolved, staged_plan)
                self.assertEqual(
                    staged_plan.read_text(encoding="utf-8"), "# modified by agent\n"
                )

                # Non-isolated (`lane_root=None`) remains byte-identical (spec 7ckptx R1.3)
                non_iso_review = runner_shared.build_review_prompt(
                    item, state, run_dir, plan_path, target, lane_root=None
                )
                self.assertEqual(non_iso_review, f"/plan-review {plan_path.as_posix()}")
                non_iso_paths = lane_containment.project_worker_paths(
                    item=item,
                    run_id=run_dir.name,
                    run_dir=run_dir,
                    plan_path=plan_path,
                    lane_root=None,
                )
                self.assertEqual(non_iso_paths.prompt_plan, str(plan_path))
                self.assertEqual(non_iso_paths.prompt_run_dir, str(run_dir))

    def test_execute_item_core_companion_review_dispatch_preserves_r1_and_routes_to_companion(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-dsp001-dispatch.ipd.md"
            )
            plan_src.write_text(_plan_text(id6="dsp001"), encoding="utf-8")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "add",
                    "--",
                    "records/plans/pending/20261121-cmpset-01-dsp001-dispatch.ipd.md",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(companion), "commit", "-m", "seed dispatch plan"],
                env=env,
                check=True,
                capture_output=True,
            )

            run_dir = td_path / "run-20261121T151000Z-7777"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, Any] = {
                "position": 1,
                "id6": "dsp001",
                "setid": "cmpset",
                "action": "review",
                "artifact_type": "ipd",
                "configured_file": ".aw/records/plans/pending/20261121-cmpset-01-dsp001-dispatch.ipd.md",
                "status": "queued",
                "attempts": [],
            }
            state: dict[str, Any] = {
                "run_id": run_dir.name,
                "repo": str(target),
                "queue": [item],
                "options": {
                    "isolate_worktree": True,
                    "self_finalize": True,
                    "review_mode": "single",
                },
            }
            main_head_before = _git_head(target, env)
            comp_head_before = _git_head(companion, env)
            observed: dict[str, Any] = {}

            def _fake_spawn_executor(
                prompt_path: Path,
                work_dir: Path | None,
                _tracker: Any,
                _plan_path: Path,
                _attempt_no: int,
                _session_id: str | None,
                _use_continue: bool,
            ) -> tuple[int, str | None, Path, list[str]]:
                assert work_dir is not None
                prompt_text = Path(prompt_path).read_text(encoding="utf-8")
                observed["prompt_text"] = prompt_text
                observed["work_dir"] = Path(work_dir)
                observed["outside"] = lane_containment.absolute_paths_outside_lane(
                    prompt_text, Path(work_dir)
                )
                observed["sealed"] = lane_containment.verify_lane_input_seal(
                    Path(work_dir), revision=1
                ).sealed
                staged_p = (
                    Path(work_dir)
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20261121-cmpset-01-dsp001-dispatch.ipd.md"
                )
                staged_p.write_text(
                    _plan_text(id6="dsp001", status="reviewed"), encoding="utf-8"
                )
                rev_p = (
                    Path(work_dir)
                    / ".aw"
                    / "records"
                    / "reviews"
                    / "20261121-cmpset-01-dsp001-dispatch.review.md"
                )
                rev_p.parent.mkdir(parents=True, exist_ok=True)
                rev_p.write_text(
                    "# Review findings: ipd dsp001\n\n- Verdict: APPROVE\n",
                    encoding="utf-8",
                )
                log_p = run_dir / "dsp001.log"
                log_p.write_text("AW-REVIEW: DONE\n", encoding="utf-8")
                return 0, "sess-dsp001", log_p, ["fake-host"]

            with _patched_env(env):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fake_spawn_executor,
                    spawn_verifier=_fake_spawn_executor,
                    raw_launcher=lambda *_a, **_kw: (0, None, run_dir / "raw.log", []),
                    run_suite_check=lambda _p, _l: None,
                    process_backlog_close=lambda *_a, **_kw: None,
                    driver_module=oc_runipd,
                )

            self.assertEqual(observed.get("outside"), [])
            self.assertNotIn(str(companion), observed.get("prompt_text", ""))
            self.assertTrue(observed.get("sealed"))
            self.assertTrue(item.get("review_integrated"), item)
            self.assertEqual(_git_head(target, env), main_head_before)
            self.assertNotEqual(_git_head(companion, env), comp_head_before)
            self.assertIn("- Status: reviewed", plan_src.read_text(encoding="utf-8"))
            self.assertTrue(
                (
                    records_root
                    / "reviews"
                    / "20261121-cmpset-01-dsp001-dispatch.review.md"
                ).is_file()
            )

    def test_companion_retry_preserves_staged_edits_and_spec_reconcile_reads_staged_copy(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-rty001-retry.ipd.md"
            )
            plan_src.write_text(_plan_text(id6="rty001"), encoding="utf-8")
            spec_src = (
                records_root / "specs" / "20261121-spc111-01-spc111-sample.spec.md"
            )
            spec_src.write_text(
                "# Spec: sample\n\n- Id: spc111\n- Status: to-review\n",
                encoding="utf-8",
            )
            run_dir = td_path / "run-20261121T152000Z-8888"
            run_dir.mkdir(parents=True, exist_ok=True)
            item: dict[str, Any] = {
                "position": 1,
                "id6": "rty001",
                "setid": "cmpset",
                "action": "review",
                "artifact_type": "ipd",
                "configured_file": ".aw/records/plans/pending/20261121-cmpset-01-rty001-retry.ipd.md",
                "status": "queued",
                "attempts": [],
            }
            state: dict[str, Any] = {
                "run_id": run_dir.name,
                "repo": str(target),
                "queue": [item],
                "options": {
                    "isolate_worktree": True,
                    "self_finalize": True,
                    "review_mode": "single",
                },
            }
            seen_on_attempt: dict[int, str] = {}

            def _fake_spawn_retry(
                _prompt_path: Path,
                work_dir: Path | None,
                _tracker: Any,
                _plan_path: Path,
                attempt_no: int,
                _session_id: str | None,
                _use_continue: bool,
            ) -> tuple[int, str | None, Path, list[str]]:
                assert work_dir is not None
                staged_p = (
                    Path(work_dir)
                    / ".aw"
                    / "records"
                    / "plans"
                    / "pending"
                    / "20261121-cmpset-01-rty001-retry.ipd.md"
                )
                seen_on_attempt[attempt_no] = staged_p.read_text(encoding="utf-8")
                log_p = run_dir / f"rty001-a{attempt_no}.log"
                if attempt_no == 1:
                    staged_p.write_text(
                        _plan_text(
                            id6="rty001",
                            status="to-review",
                            extra_history="- 2026-11-21 partial-attempt-1: preserved",
                        ),
                        encoding="utf-8",
                    )
                    log_p.write_text("partial\n", encoding="utf-8")
                    return 1, "sess-rty1", log_p, ["fake-host"]
                staged_p.write_text(
                    _plan_text(id6="rty001", status="reviewed"), encoding="utf-8"
                )
                rev_p = (
                    Path(work_dir)
                    / ".aw"
                    / "records"
                    / "reviews"
                    / "20261121-cmpset-01-rty001-retry.review.md"
                )
                rev_p.parent.mkdir(parents=True, exist_ok=True)
                rev_p.write_text("# Review\n", encoding="utf-8")
                log_p.write_text("AW-REVIEW: DONE\n", encoding="utf-8")
                return 0, "sess-rty1", log_p, ["fake-host"]

            with _patched_env(env):
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=False,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fake_spawn_retry,
                    spawn_verifier=_fake_spawn_retry,
                    raw_launcher=lambda *_a, **_kw: (0, None, run_dir / "raw.log", []),
                    run_suite_check=lambda _p, _l: None,
                    process_backlog_close=lambda *_a, **_kw: None,
                    driver_module=oc_runipd,
                )
                item["status"] = "queued"
                runner_shared.execute_item_core(
                    run_dir,
                    state,
                    item,
                    recovery=True,
                    host_labels=runner_shared.OC_HOST_LABELS,
                    spawn_executor=_fake_spawn_retry,
                    spawn_verifier=_fake_spawn_retry,
                    raw_launcher=lambda *_a, **_kw: (0, None, run_dir / "raw.log", []),
                    run_suite_check=lambda _p, _l: None,
                    process_backlog_close=lambda *_a, **_kw: None,
                    driver_module=oc_runipd,
                )
                self.assertIn("partial-attempt-1: preserved", seen_on_attempt[2])

                # Companion spec review reconcile reads staged lane spec & staged lane review record
                from agent_workflows import review_findings

                wt_spec, _ = _add_lane_worktree(target, "spc111", env)
                staged_spec = lane_containment.stage_companion_lane_artifact(
                    wt_spec, spec_src, records_root
                )
                staged_spec.write_text(
                    "# Spec: sample\n\n- Id: spc111\n- Status: reviewed\n",
                    encoding="utf-8",
                )
                lane_rev = (
                    wt_spec
                    / ".aw"
                    / "records"
                    / "reviews"
                    / "20261121-spc111-01-spc111-sample.review.md"
                )
                lane_rev.parent.mkdir(parents=True, exist_ok=True)
                lane_rev.write_text(
                    review_findings.render_review(
                        subject_id="spc111",
                        subject_type="spec",
                        reviewed_at="2026-11-21",
                        reviewer="test",
                        verdict="APPROVE",
                        rounds=[
                            review_findings.Round(
                                number=1,
                                findings=(),
                                decisions=(),
                            )
                        ],
                    ),
                    encoding="utf-8",
                )
                spec_item = {
                    "position": 2,
                    "id6": "spc111",
                    "action": "review",
                    "artifact_type": "spec",
                    "configured_file": ".aw/records/specs/20261121-spc111-01-spc111-sample.spec.md",
                }
                disp, _ = runner_shared.reconcile_disposition(
                    target, spec_item, run_dir, exit_code=0, plan_repo=wt_spec
                )
                self.assertEqual(disp, "reviewed", spec_item)


class CompanionCarrierCheckTests(unittest.TestCase):
    """E-02 / V-02: check_review_lane_artifacts resolves companion sibling carriers and evidence."""

    def test_check_review_lane_artifacts_passes_valid_companion_carriers_and_fails_missing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, handle = _add_lane_worktree(target, "car001", env)
            records_root = companion / "records"

            # Sibling pending carrier and executed evidence live in companion
            sib_plan = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-02-sib111-sibling.ipd.md"
            )
            sib_plan.write_text(_plan_text(id6="sib111", order=2), encoding="utf-8")
            exe_plan = (
                records_root
                / "plans"
                / "executed"
                / "20261121-cmpset-00-exe222-done.ipd.md"
            )
            exe_plan.write_text(
                _plan_text(id6="exe222", order=0, status="executed"), encoding="utf-8"
            )

            valid_deferred = (
                "- Deferred follow-up work.\n"
                "  - Carrier: sib111\n"
                "- Completed prerequisite.\n"
                "  - Carrier: exe222\n"
                "  - Carrier-Evidence: .aw/records/plans/executed/20261121-cmpset-00-exe222-done.ipd.md"
            )
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-car001-target.ipd.md"
            )
            plan_src.write_text(
                _plan_text(id6="car001", deferred_block=valid_deferred),
                encoding="utf-8",
            )

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_src, records_root
                )
                norm_p = staged.relative_to(wt).as_posix()

                # Linked worktree inherits companion context (pbdtss)
                ok, reason = runner_shared.check_review_lane_artifacts(
                    target, handle, [norm_p]
                )
                self.assertTrue(ok, reason)

                # Unconfigured plain directory fallback resolves against `repo`
                unconf_dir = td_path / "unconfigured_wt"
                (unconf_dir / norm_p).parent.mkdir(parents=True, exist_ok=True)
                (unconf_dir / norm_p).write_text(
                    staged.read_text(encoding="utf-8"), encoding="utf-8"
                )
                unconf_handle = worktree_lease.WorktreeHandle(
                    lane_id="unconf",
                    path=unconf_dir,
                    branch=handle.branch,
                    base_commit=handle.base_commit,
                )
                ok_fb, reason_fb = runner_shared.check_review_lane_artifacts(
                    target, unconf_handle, [norm_p]
                )
                self.assertTrue(ok_fb, reason_fb)

                # Nonexistent carrier fails at error severity
                bad_deferred = "- Missing follow-up.\n  - Carrier: zzz999"
                staged.write_text(
                    _plan_text(id6="car001", deferred_block=bad_deferred),
                    encoding="utf-8",
                )
                bad_ok, bad_reason = runner_shared.check_review_lane_artifacts(
                    target, handle, [norm_p]
                )
                self.assertFalse(bad_ok)
                self.assertIn("zzz999", bad_reason)
                self.assertIn("check.ipd-uncarried-obligation", bad_reason)


class CompanionRecordRoutingAndMergeGuardTests(unittest.TestCase):
    """E-03 / E-04 / V-03 / V-04: companion routing for review/execute and target merge guard."""

    def test_companion_review_integration_routes_to_initialized_companion_and_leaves_main_untouched(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(
                td_path, init_companion_git=True, initial_companion_commit=True
            )
            wt, handle = _add_lane_worktree(target, "rev001", env)
            records_root = companion / "records"

            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-rev001-sample.ipd.md"
            )
            plan_src.write_text(_plan_text(id6="rev001"), encoding="utf-8")
            untouched_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-02-unt002-untouched.ipd.md"
            )
            untouched_src.write_text(
                _plan_text(id6="unt002", order=2), encoding="utf-8"
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "add",
                    "--",
                    "records/plans/pending/20261121-cmpset-01-rev001-sample.ipd.md",
                    "records/plans/pending/20261121-cmpset-02-unt002-untouched.ipd.md",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(companion), "commit", "-m", "seed companion plans"],
                env=env,
                check=True,
                capture_output=True,
            )
            # Unrelated untracked file in companion must never be swept into the commit
            unrelated = records_root / "unrelated.md"
            unrelated.write_text("do not commit me\n", encoding="utf-8")

            main_head_before = _git_head(target, env)
            comp_head_before = _git_head(companion, env)

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_src, records_root
                )
                lane_containment.stage_companion_lane_artifact(
                    wt, untouched_src, records_root
                )
                # Simulate review turn updating the staged plan and creating a .review.md
                revised_text = _plan_text(
                    id6="rev001",
                    status="reviewed",
                    extra_history="- 2026-11-21 /plan-review (test): APPROVED",
                )
                staged.write_text(revised_text, encoding="utf-8")
                review_file = (
                    wt
                    / ".aw"
                    / "records"
                    / "reviews"
                    / "20261121-cmpset-01-rev001-sample.review.md"
                )
                review_file.parent.mkdir(parents=True, exist_ok=True)
                review_file.write_text(
                    "# Review findings: ipd rev001\n\n- Verdict: APPROVE\n",
                    encoding="utf-8",
                )

                # commit_review_lane_output must not commit private records onto target branch
                c_sha, c_paths = runner_shared.commit_review_lane_output(
                    target, handle, "rev001", host_label="aw oc run"
                )
                self.assertIsNone(c_sha)
                self.assertEqual(c_paths, ())

                integrated, reason, kind = oc_runipd.integrate_review_lane_branch(
                    target, handle, "rev001"
                )
                self.assertTrue(integrated, reason)
                self.assertEqual(kind, "integrated")
                self.assertEqual(_git_head(target, env), main_head_before)

                # Companion files updated and path-scoped commit created
                self.assertEqual(plan_src.read_text(encoding="utf-8"), revised_text)
                comp_review = (
                    records_root
                    / "reviews"
                    / "20261121-cmpset-01-rev001-sample.review.md"
                )
                self.assertTrue(comp_review.is_file())
                self.assertNotEqual(_git_head(companion, env), comp_head_before)

                show_files = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(companion),
                        "show",
                        "--name-only",
                        "--format=",
                        "HEAD",
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.splitlines()
                self.assertEqual(
                    sorted(p for p in show_files if p.strip()),
                    [
                        "records/plans/pending/20261121-cmpset-01-rev001-sample.ipd.md",
                        "records/reviews/20261121-cmpset-01-rev001-sample.review.md",
                    ],
                )
                commit_msg = subprocess.run(
                    ["git", "-C", str(companion), "log", "-1", "--format=%B"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                self.assertIn("AW-Item: rev001", commit_msg)
                self.assertIn("AW-Runner: aw oc run", commit_msg)
                self.assertTrue(unrelated.is_file())

    def test_companion_review_handles_unborn_head_and_unversioned_companion(
        self,
    ) -> None:
        # Case 1: initialized git companion with unborn HEAD (zero commits)
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(
                td_path, init_companion_git=True, initial_companion_commit=False
            )
            self.assertFalse(storage._git_has_commits(companion))
            wt, handle = _add_lane_worktree(target, "unb001", env)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-unb001-sample.ipd.md"
            )
            plan_src.write_text(_plan_text(id6="unb001"), encoding="utf-8")
            main_head_before = _git_head(target, env)

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_src, records_root
                )
                staged.write_text(
                    _plan_text(id6="unb001", status="reviewed"), encoding="utf-8"
                )
                rev_file = (
                    wt
                    / ".aw"
                    / "records"
                    / "reviews"
                    / "20261121-cmpset-01-unb001-sample.review.md"
                )
                rev_file.parent.mkdir(parents=True, exist_ok=True)
                rev_file.write_text("# Review\n", encoding="utf-8")

                ok, reason, kind = agy_runipd.integrate_review_lane_branch(
                    target, handle, "unb001"
                )
                self.assertTrue(ok, reason)
                self.assertEqual(kind, "integrated")
                self.assertEqual(_git_head(target, env), main_head_before)
                self.assertTrue(storage._git_has_commits(companion))
                show_files = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(companion),
                        "show",
                        "--name-only",
                        "--format=",
                        "HEAD",
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.splitlines()
                self.assertEqual(
                    sorted(p for p in show_files if p.strip()),
                    [
                        "records/plans/pending/20261121-cmpset-01-unb001-sample.ipd.md",
                        "records/reviews/20261121-cmpset-01-unb001-sample.review.md",
                    ],
                )

        # Case 2: unversioned companion (no .git directory)
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(
                td_path, init_companion_git=False, initial_companion_commit=False
            )
            self.assertFalse((companion / ".git").exists())
            wt, handle = _add_lane_worktree(target, "unv001", env)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-unv001-sample.ipd.md"
            )
            plan_src.write_text(_plan_text(id6="unv001"), encoding="utf-8")
            main_head_before = _git_head(target, env)

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_src, records_root
                )
                revised = _plan_text(id6="unv001", status="reviewed")
                staged.write_text(revised, encoding="utf-8")

                ok, reason, kind = oc_runipd.integrate_review_lane_branch(
                    target, handle, "unv001"
                )
                self.assertTrue(ok, reason)
                self.assertEqual(kind, "integrated")
                self.assertEqual(_git_head(target, env), main_head_before)
                self.assertEqual(plan_src.read_text(encoding="utf-8"), revised)

    def test_companion_review_validates_before_writing_to_companion(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, handle = _add_lane_worktree(target, "bad001", env)
            records_root = companion / "records"
            plan_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-bad001-sample.ipd.md"
            )
            orig_text = _plan_text(id6="bad001")
            plan_src.write_text(orig_text, encoding="utf-8")
            comp_head_before = _git_head(companion, env)
            main_head_before = _git_head(target, env)

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, plan_src, records_root
                )
                staged.write_text(
                    _plan_text(
                        id6="bad001", deferred_block="- Uncarried.\n  - Carrier: zzz999"
                    ),
                    encoding="utf-8",
                )
                ok, reason, kind = oc_runipd.integrate_review_lane_branch(
                    target, handle, "bad001"
                )
                self.assertFalse(ok)
                self.assertEqual(kind, runner_shared.INTEGRATION_REFUSAL_CONFLICT)
                self.assertIn("zzz999", reason)
                # Neither companion nor target was mutated
                self.assertEqual(plan_src.read_text(encoding="utf-8"), orig_text)
                self.assertEqual(_git_head(companion, env), comp_head_before)
                self.assertEqual(_git_head(target, env), main_head_before)

    def test_companion_execute_integration_splits_code_and_records(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            wt, handle = _add_lane_worktree(target, "exe001", env)
            records_root = companion / "records"
            pending_src = (
                records_root
                / "plans"
                / "pending"
                / "20261121-cmpset-01-exe001-sample.ipd.md"
            )
            pending_src.write_text(
                _plan_text(id6="exe001", status="approved"), encoding="utf-8"
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(companion),
                    "add",
                    "--",
                    "records/plans/pending/20261121-cmpset-01-exe001-sample.ipd.md",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(companion), "commit", "-m", "seed approved plan"],
                env=env,
                check=True,
                capture_output=True,
            )

            with _patched_env(env):
                staged = lane_containment.stage_companion_lane_artifact(
                    wt, pending_src, records_root
                )
                # Commit code change on target lane branch
                (wt / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(wt), "add", "--", "app.py"],
                    env=env,
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(wt),
                        "commit",
                        "-m",
                        "work(exe001): update app.py",
                    ],
                    env=env,
                    check=True,
                    capture_output=True,
                )

                # Simulate lane moving plan from pending/ to executed/ inside gitignored .aw/records
                lane_exec_path = (
                    wt
                    / ".aw"
                    / "records"
                    / "plans"
                    / "executed"
                    / "20261121-cmpset-01-exe001-sample.ipd.md"
                )
                lane_exec_path.parent.mkdir(parents=True, exist_ok=True)
                lane_exec_path.write_text(
                    _plan_text(id6="exe001", status="executed"), encoding="utf-8"
                )
                staged.unlink()

                ok, reason, kind = oc_runipd.integrate_lane_branch(
                    target, handle, "exe001", _passing_validation_runner
                )
                self.assertTrue(ok, reason)
                self.assertEqual(kind, "integrated")

                # Target main got app.py and ZERO .aw/records/** paths
                self.assertEqual(
                    (target / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n"
                )
                target_tree = subprocess.run(
                    ["git", "-C", str(target), "ls-tree", "-r", "--name-only", "HEAD"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.splitlines()
                self.assertFalse(
                    any(
                        p == ".aw/records" or p.startswith(".aw/records/")
                        for p in target_tree
                    ),
                    target_tree,
                )

                # Companion got executed plan and removed pending plan atomically
                comp_exec = (
                    records_root
                    / "plans"
                    / "executed"
                    / "20261121-cmpset-01-exe001-sample.ipd.md"
                )
                self.assertTrue(comp_exec.is_file())
                self.assertFalse(pending_src.exists())
                comp_show = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(companion),
                        "show",
                        "--name-status",
                        "--format=",
                        "HEAD",
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout
                self.assertIn("20261121-cmpset-01-exe001-sample.ipd.md", comp_show)

    def test_fail_closed_merge_guard_refuses_aw_records_file_symlink_and_rename(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            target, companion, env = _provision_companion_repos(td_path)
            main_head_before = _git_head(target, env)

            # 1. Force-committed .aw/records/** file on lane branch
            wt1, handle1 = _add_lane_worktree(target, "lek001", env)
            leak_file = wt1 / ".aw" / "records" / "plans" / "pending" / "leak.ipd.md"
            leak_file.parent.mkdir(parents=True, exist_ok=True)
            leak_file.write_text("# Private leak\n", encoding="utf-8")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(wt1),
                    "add",
                    "-f",
                    "--",
                    ".aw/records/plans/pending/leak.ipd.md",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(wt1), "commit", "-m", "force add private record"],
                env=env,
                check=True,
                capture_output=True,
            )

            # 2. Force-committed symlink at literal .aw/records on lane branch
            wt2, handle2 = _add_lane_worktree(target, "lek002", env)
            (wt2 / ".aw").mkdir(parents=True, exist_ok=True)
            (wt2 / ".aw" / "records").symlink_to(companion / "records")
            subprocess.run(
                ["git", "-C", str(wt2), "add", "-f", "--", ".aw/records"],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(wt2), "commit", "-m", "force add records symlink"],
                env=env,
                check=True,
                capture_output=True,
            )

            # 3. Rename of tracked file into .aw/records/**
            (target / "notes.md").write_text("public note\n", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(target), "add", "--", "notes.md"],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(target), "commit", "-m", "add notes.md"],
                env=env,
                check=True,
                capture_output=True,
            )
            main_head_with_notes = _git_head(target, env)
            wt3, handle3 = _add_lane_worktree(target, "lek003", env)
            (wt3 / ".aw" / "records").mkdir(parents=True, exist_ok=True)
            shutil.move(
                str(wt3 / "notes.md"), str(wt3 / ".aw" / "records" / "moved.md")
            )
            subprocess.run(
                ["git", "-C", str(wt3), "add", "-f", "--", ".aw/records/moved.md"],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(wt3), "rm", "--", "notes.md"],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(wt3), "commit", "-m", "rename notes into records"],
                env=env,
                check=True,
                capture_output=True,
            )

            with _patched_env(env):
                # Refused across BOTH oc and agy wrappers and BOTH execute and review
                for call_name, res in [
                    (
                        "oc execute file",
                        oc_runipd.integrate_lane_branch(
                            target, handle1, "lek001", _passing_validation_runner
                        ),
                    ),
                    (
                        "agy execute file",
                        agy_runipd.integrate_lane_branch(
                            target, handle1, "lek001", _passing_validation_runner
                        ),
                    ),
                    (
                        "oc review file",
                        oc_runipd.integrate_review_lane_branch(
                            target, handle1, "lek001"
                        ),
                    ),
                    (
                        "agy review file",
                        agy_runipd.integrate_review_lane_branch(
                            target, handle1, "lek001"
                        ),
                    ),
                ]:
                    ok, reason, kind = res
                    self.assertFalse(ok, f"{call_name} should refuse")
                    self.assertEqual(
                        kind, runner_shared.INTEGRATION_REFUSAL_CONFLICT, call_name
                    )
                    self.assertIn(
                        ".aw/records/plans/pending/leak.ipd.md", reason, call_name
                    )

                ok_sym, reason_sym, kind_sym = oc_runipd.integrate_lane_branch(
                    target, handle2, "lek002", _passing_validation_runner
                )
                self.assertFalse(ok_sym)
                self.assertEqual(kind_sym, runner_shared.INTEGRATION_REFUSAL_CONFLICT)
                self.assertIn(".aw/records", reason_sym)

                ok_ren, reason_ren, kind_ren = agy_runipd.integrate_lane_branch(
                    target, handle3, "lek003", _passing_validation_runner
                )
                self.assertFalse(ok_ren)
                self.assertEqual(kind_ren, runner_shared.INTEGRATION_REFUSAL_CONFLICT)
                self.assertIn(".aw/records/moved.md", reason_ren)

                # Target main HEAD and index remain completely unchanged
                self.assertEqual(_git_head(target, env), main_head_with_notes)
                self.assertNotEqual(main_head_with_notes, main_head_before)
                status = subprocess.run(
                    ["git", "-C", str(target), "status", "--porcelain"],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertEqual(status, "")

                # Direct helper still supports branch-committed record collection (E-03(a))
                r_ok, r_reason, _r_kind, r_sha, routed = (
                    runner_shared.route_companion_lane_records(
                        target,
                        handle1,
                        "lek001",
                        host_label="aw oc run",
                        action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
                        validate_review=False,
                        include_branch_records=True,
                    )
                )
                self.assertTrue(r_ok, r_reason)
                self.assertIsNotNone(r_sha)
                self.assertIn("plans/pending/leak.ipd.md", routed)
                self.assertTrue(
                    (
                        companion / "records" / "plans" / "pending" / "leak.ipd.md"
                    ).is_file()
                )

    def test_private_target_mode_still_permits_aw_records_merges(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            env = _make_env(td_path)
            repo = td_path / "private_repo"
            init_repo(repo)
            (repo / ".aw" / "config").mkdir(parents=True, exist_ok=True)
            (repo / ".aw" / "config" / "project.json").write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "preset": "private-target",
                        "delivery_mode": "tracked",
                        "records_backend": "repository",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "add",
                    "--",
                    "app.py",
                    ".aw/config/project.json",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "initial private repo"],
                env=env,
                check=True,
                capture_output=True,
            )

            wt, handle = _add_lane_worktree(repo, "prv001", env)
            plan_file = (
                wt
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261121-cmpset-01-prv001-private.ipd.md"
            )
            plan_file.parent.mkdir(parents=True, exist_ok=True)
            plan_file.write_text(_plan_text(id6="prv001"), encoding="utf-8")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(wt),
                    "add",
                    "--",
                    ".aw/records/plans/pending/20261121-cmpset-01-prv001-private.ipd.md",
                ],
                env=env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "-C", str(wt), "commit", "-m", "review(prv001): add plan"],
                env=env,
                check=True,
                capture_output=True,
            )

            with _patched_env(env):
                ok, reason, kind = oc_runipd.integrate_review_lane_branch(
                    repo, handle, "prv001"
                )
                self.assertTrue(ok, reason)
                self.assertEqual(kind, "integrated")
                self.assertTrue(
                    (
                        repo
                        / ".aw"
                        / "records"
                        / "plans"
                        / "pending"
                        / "20261121-cmpset-01-prv001-private.ipd.md"
                    ).is_file()
                )


if __name__ == "__main__":
    unittest.main()
