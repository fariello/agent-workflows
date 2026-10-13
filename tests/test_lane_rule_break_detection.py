"""Tests for lane rule-break detection (IPD 62sdwr E-05).

Verifies detection of untooled status changes and hook-skipping commits across both
hosts (`oc_runipd` and `agy_runipd`), asserting:
(a) hand-edited plan status receives fix-it turn,
(b) hand `git mv` into executed/ receives fix-it turn,
(c) --no-verify commit past refusing hook receives fix-it turn,
(d) tooled retirement via aw ipd set superseded lands retired without fix-it turn,
(e) hand retirement without history line receives fix-it turn,
(f) clean tooled run lands executed without fix-it turn,
(g) hook unavailable cases (missing config, missing pre-commit, exit 3) do not fail,
(h) delivered prompt text contains specific fix instructions and never tells agent to run aw ipd finalize,
(i) lane working tree is byte-identical before and after the hook check.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests import support
from tests.test_oc_runipd import _init_repo_with_conforming_plan

_HOSTS = (
    ("oc", oc_runipd, "run_opencode", runner_shared.OC_HOST_LABELS),
    ("agy", agy_runipd, "run_agy_turn", runner_shared.AGY_HOST_LABELS),
)

_SYSTEM_PRE_COMMIT_CONFIG = """repos:
- repo: local
  hooks:
  - id: refuse-content
    name: refuse bad content
    entry: python3 -c "import sys; sys.exit(1 if any('REFUSE_HOOK' in open(f).read() for f in sys.argv[1:]) else 0)"
    language: system
    files: \\.txt$
"""

_STAGED_GATE_PRE_COMMIT_CONFIG = """repos:
- repo: local
  hooks:
  - id: check-staged-executed
    name: check staged executed
    entry: python3 -c "import subprocess, sys; out = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True); sys.exit(1 if 'executed/' in out else 0)"
    language: system
    pass_filenames: false
    always_run: true
"""


def _state_and_item(repo: Path, plan: Path) -> tuple[dict, dict]:
    item = {
        "position": 1,
        "id6": "det001",
        "setid": "demo",
        "status": "queued",
        "configured_file": str(plan.relative_to(repo)),
        "action": "execute",
    }
    state = {
        "run_id": "run-detect-test",
        "created_at": "2026-10-12T00:00:00+00:00",
        "updated_at": "2026-10-12T00:00:00+00:00",
        "selectors": ["demo"],
        "repo": str(repo),
        "queue": [item],
        "set_sessions": {},
        "session_id": None,
        "options": {
            "opencode": "/bin/true",
            "agy": "/bin/true",
            "model": "opus",
            "self_finalize": True,
            "isolate_worktree": True,
            "no_audit": False,
            "retry_budget": 2,
        },
    }
    return state, item


class LaneRuleBreakDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _setup_repo(
        self, pre_commit_cfg: str | None = None
    ) -> tuple[tempfile.TemporaryDirectory, Path, Path, Path, dict, dict]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        repo = Path(temp.name) / "repo"
        plan = _init_repo_with_conforming_plan(repo, "det001")
        if pre_commit_cfg:
            (repo / ".pre-commit-config.yaml").write_text(
                pre_commit_cfg, encoding="utf-8"
            )
            subprocess.run(
                ["git", "add", ".pre-commit-config.yaml"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "add pre-commit config"], cwd=repo, check=True
            )
        run_dir = repo / ".aw" / "records" / "runs" / "run-detect-test"
        (run_dir / "outcomes").mkdir(parents=True)
        (run_dir / "prompts").mkdir(parents=True)
        state, item = _state_and_item(repo, plan)
        return temp, repo, plan, run_dir, state, item

    def test_case_a_hand_edit_status_receives_fix_it_turn(self):
        """Case (a): Hand-editing a plan's status sends the item back as a fix-it turn."""
        for label, mod, spawn_name, host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, plan, run_dir, state, item = self._setup_repo()
                call_count = 0

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        (
                            rd
                            / "outcomes"
                            / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                        ).write_text(
                            json.dumps(
                                {
                                    "verdict": "VERIFIED",
                                    "tests_run": ["python3 -m pytest"],
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "vses", str(rd / "vlog"), ["x"]
                    nonlocal call_count
                    call_count += 1
                    wt = Path(kwargs["work_dir"])
                    plan_file = next(
                        (wt / ".aw" / "records" / "plans" / "pending").glob("*det001*")
                    )
                    if call_count == 1:
                        # Attempt 1: Hand-edit status without a history line
                        text = plan_file.read_text(encoding="utf-8").replace(
                            "- Status: approved", "- Status: to-review"
                        )
                        plan_file.write_text(text, encoding="utf-8")
                        subprocess.run(
                            ["git", "commit", "-qam", "hand edit status"],
                            cwd=wt,
                            check=True,
                        )
                    else:
                        # Attempt 2: Revert hand edit back to approved
                        text = plan_file.read_text(encoding="utf-8").replace(
                            "- Status: to-review", "- Status: approved"
                        )
                        plan_file.write_text(text, encoding="utf-8")
                        # Also create demo.txt so execution succeeds
                        (wt / "src").mkdir(parents=True, exist_ok=True)
                        (wt / "src" / "demo.txt").write_text("done", encoding="utf-8")
                        subprocess.run(["git", "add", "."], cwd=wt, check=True)
                        subprocess.run(
                            ["git", "commit", "-qam", "revert hand edit"],
                            cwd=wt,
                            check=True,
                        )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                # Run attempt 1
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get("refusal", {}).get("code"),
                    runner_shared.UNTOOLED_STATUS_REFUSAL_CODE,
                )
                self.assertIn(
                    "Workflow history", str(item.get("untooled_status_refusal") or "")
                )

                # Check prompt delivered for attempt 2
                prompt_text = runner_shared.build_prompt(
                    item, state, run_dir, plan, recovery=True, labels=host_labels
                )
                self.assertIn("## untooled-status-change", prompt_text)
                self.assertIn(plan.name, prompt_text)
                self.assertNotIn("run `aw ipd finalize`", prompt_text)
                self.assertIn(
                    "leave the plan in `pending/` and let the runner finalize it",
                    prompt_text,
                )

                # Run attempt 2 (agent reverts hand-edit)
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=True)

                self.assertNotEqual(item["status"], "queued")
                self.assertEqual(item["status"], "executed")

    def test_case_b_hand_move_into_executed_receives_fix_it_turn(self):
        """Case (b): `git mv` into executed/ without finalize commit sends item back as fix-it turn."""
        for label, mod, spawn_name, host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, plan, run_dir, state, item = self._setup_repo()
                call_count = 0

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        (
                            rd
                            / "outcomes"
                            / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                        ).write_text(
                            json.dumps(
                                {
                                    "verdict": "VERIFIED",
                                    "tests_run": ["python3 -m pytest"],
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "vses", str(rd / "vlog"), ["x"]
                    nonlocal call_count
                    call_count += 1
                    wt = Path(kwargs["work_dir"])
                    pending_dir = wt / ".aw" / "records" / "plans" / "pending"
                    exec_dir = wt / ".aw" / "records" / "plans" / "executed"
                    exec_dir.mkdir(parents=True, exist_ok=True)
                    if call_count == 1:
                        # Attempt 1: hand mv to executed/
                        plan_file = next(pending_dir.glob("*det001*"))
                        dest = exec_dir / plan_file.name
                        text = plan_file.read_text(encoding="utf-8").replace(
                            "- Status: approved", "- Status: executed"
                        )
                        plan_file.write_text(text, encoding="utf-8")
                        subprocess.run(
                            ["git", "mv", str(plan_file), str(dest)], cwd=wt, check=True
                        )
                        subprocess.run(
                            ["git", "commit", "-qam", "hand mv to executed"],
                            cwd=wt,
                            check=True,
                        )
                    else:
                        # Attempt 2: ensure plan is in pending/ and clean
                        exec_plans = list(exec_dir.glob("*det001*"))
                        if exec_plans:
                            plan_file = exec_plans[0]
                            dest = pending_dir / plan_file.name
                            text = plan_file.read_text(encoding="utf-8").replace(
                                "- Status: executed", "- Status: approved"
                            )
                            plan_file.write_text(text, encoding="utf-8")
                            subprocess.run(
                                ["git", "mv", str(plan_file), str(dest)],
                                cwd=wt,
                                check=True,
                            )
                        (wt / "src").mkdir(parents=True, exist_ok=True)
                        (wt / "src" / "demo.txt").write_text("done", encoding="utf-8")
                        subprocess.run(["git", "add", "."], cwd=wt, check=True)
                        subprocess.run(
                            ["git", "commit", "-qam", "clean attempt 2"],
                            cwd=wt,
                            check=True,
                        )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                # Run attempt 1
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get("refusal", {}).get("code"),
                    runner_shared.UNTOOLED_STATUS_REFUSAL_CODE,
                )
                self.assertIn(
                    "entered 'executed/'",
                    str(item.get("untooled_status_refusal") or ""),
                )

                # Check prompt delivered
                prompt_text = runner_shared.build_prompt(
                    item, state, run_dir, plan, recovery=True, labels=host_labels
                )
                self.assertIn("## untooled-status-change", prompt_text)
                self.assertIn(plan.name, prompt_text)
                self.assertNotIn("run `aw ipd finalize`", prompt_text)
                self.assertIn(
                    "leave the plan in `pending/` and let the runner finalize it",
                    prompt_text,
                )

                # Run attempt 2 (agent reverts move)
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=True)

                self.assertEqual(item["status"], "executed")

    def test_case_c_hook_bypass_content_receives_fix_it_turn(self):
        """Case (c): A commit made with --no-verify that fails pre-commit receives a fix-it turn."""
        for label, mod, spawn_name, host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, plan, run_dir, state, item = self._setup_repo(
                    pre_commit_cfg=_SYSTEM_PRE_COMMIT_CONFIG
                )
                call_count = 0
                lane_status_before = ""

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        (
                            rd
                            / "outcomes"
                            / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                        ).write_text(
                            json.dumps(
                                {
                                    "verdict": "VERIFIED",
                                    "tests_run": ["python3 -m pytest"],
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "vses", str(rd / "vlog"), ["x"]
                    nonlocal call_count, lane_status_before
                    call_count += 1
                    wt = Path(kwargs["work_dir"])
                    (wt / "src").mkdir(parents=True, exist_ok=True)
                    if call_count == 1:
                        # Attempt 1: commit with --no-verify adding REFUSE_HOOK
                        (wt / "src" / "bad.txt").write_text(
                            "contains REFUSE_HOOK", encoding="utf-8"
                        )
                        subprocess.run(["git", "add", "."], cwd=wt, check=True)
                        subprocess.run(
                            ["git", "commit", "-m", "bypass commit", "--no-verify"],
                            cwd=wt,
                            check=True,
                        )
                        lane_status_before = subprocess.check_output(
                            ["git", "status", "--porcelain"], cwd=wt, text=True
                        )
                    else:
                        # Attempt 2: fix content cleanly
                        (wt / "src" / "bad.txt").write_text(
                            "clean content", encoding="utf-8"
                        )
                        (wt / "src" / "demo.txt").write_text("done", encoding="utf-8")
                        subprocess.run(["git", "add", "."], cwd=wt, check=True)
                        subprocess.run(
                            ["git", "commit", "-m", "clean fix commit", "--no-verify"],
                            cwd=wt,
                            check=True,
                        )

                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                # Run attempt 1
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get("refusal", {}).get("code"),
                    runner_shared.HOOK_BYPASS_REFUSAL_CODE,
                )
                self.assertIn(
                    "refuse bad content", str(item.get("hook_bypass_refusal") or "")
                )

                # Check prompt delivered
                prompt_text = runner_shared.build_prompt(
                    item, state, run_dir, plan, recovery=True, labels=host_labels
                )
                self.assertIn("## hook-bypass", prompt_text)
                self.assertIn("refuse bad content", prompt_text)
                self.assertIn("do not use --no-verify", prompt_text)

                # Run attempt 2 (agent fixes content)
                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=True)

                self.assertEqual(item["status"], "executed")

    def test_case_d_tooled_retirement_lands_retired_without_fix_it(self):
        """Case (d): A plan retired via aw ipd set superseded lands as retired with no fix-it turn."""
        for label, mod, spawn_name, _host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, _plan, run_dir, state, item = self._setup_repo()

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        (
                            rd
                            / "outcomes"
                            / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                        ).write_text(
                            json.dumps(
                                {
                                    "verdict": "VERIFIED",
                                    "tests_run": ["python3 -m pytest"],
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "vses", str(rd / "vlog"), ["x"]
                    wt = Path(kwargs["work_dir"])
                    pending = next(
                        (wt / ".aw" / "records" / "plans" / "pending").glob("*det001*")
                    )
                    sup = wt / ".aw" / "records" / "plans" / "superseded"
                    sup.mkdir(parents=True, exist_ok=True)
                    text = pending.read_text(encoding="utf-8").replace(
                        "- Status: approved", "- Status: superseded"
                    )
                    text = text.replace(
                        "## Workflow history\n",
                        "## Workflow history\n- 2026-10-12 superseded (aw set): premise spent\n",
                    )
                    pending.write_text(
                        "RETIRED 2026-10-12: premise spent.\n\n" + text,
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "mv", str(pending), str(sup / pending.name)],
                        cwd=wt,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qam", "aw ipd set superseded det001"],
                        cwd=wt,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "blocked",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], runner_shared.RETIRED_STATUS)
                self.assertFalse(item.get("recovery_next"))

    def test_case_e_hand_retirement_receives_fix_it_turn(self):
        """Case (e): A hand-edited retirement without a history line receives a fix-it turn."""
        for label, mod, spawn_name, _host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, _plan, run_dir, state, item = self._setup_repo()

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    wt = Path(kwargs["work_dir"])
                    pending = next(
                        (wt / ".aw" / "records" / "plans" / "pending").glob("*det001*")
                    )
                    sup = wt / ".aw" / "records" / "plans" / "superseded"
                    sup.mkdir(parents=True, exist_ok=True)
                    text = pending.read_text(encoding="utf-8").replace(
                        "- Status: approved", "- Status: superseded"
                    )
                    pending.write_text(
                        "RETIRED 2026-10-12: premise spent.\n\n" + text,
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "mv", str(pending), str(sup / pending.name)],
                        cwd=wt,
                        check=True,
                    )
                    subprocess.run(
                        ["git", "commit", "-qam", "hand retire det001"],
                        cwd=wt,
                        check=True,
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "blocked",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "queued")
                self.assertTrue(item.get("recovery_next"))
                self.assertEqual(
                    item.get("refusal", {}).get("code"),
                    runner_shared.UNTOOLED_STATUS_REFUSAL_CODE,
                )
                self.assertIn(
                    "Workflow history", str(item.get("untooled_status_refusal") or "")
                )

    def test_case_f_clean_tooled_run_lands_executed(self):
        """Case (f): Clean execution through tools lands executed with no fix-it turn."""
        for label, mod, spawn_name, _host_labels in _HOSTS:
            with self.subTest(host=label):
                _td, _repo, _plan, run_dir, state, item = self._setup_repo()

                def fake_run(st, rd, itm, *_args, **kwargs):
                    if itm.get("id6") != "det001" or not kwargs.get("work_dir"):
                        return 0, "probe-ses", str(rd / "log"), ["x"]
                    if (
                        kwargs.get("fresh_session")
                        or kwargs.get("log_suffix") == "verify"
                    ):
                        (
                            rd
                            / "outcomes"
                            / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                        ).write_text(
                            json.dumps(
                                {
                                    "verdict": "VERIFIED",
                                    "tests_run": ["python3 -m pytest"],
                                }
                            ),
                            encoding="utf-8",
                        )
                        return 0, "vses", str(rd / "vlog"), ["x"]
                    wt = Path(kwargs["work_dir"])
                    (wt / "src").mkdir(parents=True, exist_ok=True)
                    (wt / "src" / "demo.txt").write_text("clean", encoding="utf-8")
                    subprocess.run(["git", "add", "."], cwd=wt, check=True)
                    subprocess.run(
                        ["git", "commit", "-qam", "clean commit"], cwd=wt, check=True
                    )
                    (
                        rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                    ).write_text(
                        json.dumps(
                            {
                                "disposition": "executed",
                                "pushed": False,
                                "defect_report": {
                                    "state": "none-found",
                                    "findings": [],
                                },
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "ses1", str(rd / "log"), ["x"]

                with mock.patch.object(mod, spawn_name, fake_run):
                    mod.execute_item(run_dir, state, item, recovery=False)

                self.assertEqual(item["status"], "executed")
                self.assertFalse(item.get("recovery_next"))

    def test_hook_bypass_staged_gate_move_into_executed(self):
        """A --no-verify commit that moves a plan into executed/ is caught by the staged-index gate."""
        _td, repo, plan, _run_dir, _state, _item = self._setup_repo(
            pre_commit_cfg=_STAGED_GATE_PRE_COMMIT_CONFIG
        )
        base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()

        # Move plan to executed with --no-verify
        exec_dir = repo / ".aw" / "records" / "plans" / "executed"
        exec_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "mv", str(plan), str(exec_dir / plan.name)], cwd=repo, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "bypass move", "--no-verify"], cwd=repo, check=True
        )
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()

        passed, msg = runner_shared.check_lane_hook_bypass(repo, base, head)
        self.assertFalse(passed)
        self.assertIn("check staged executed", msg)

    def test_hook_checking_unavailable_conditions(self):
        """Hook checking returns unavailable when config is absent, pre-commit is uninstalled, or exit 3."""
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            subprocess.run(
                ["git", "init", "-b", "main"], cwd=r, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"], cwd=r, check=True
            )
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=r, check=True)
            (r / "x.txt").write_text("x", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=r, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=r, check=True)
            b = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=r, text=True
            ).strip()
            (r / "x.txt").write_text("x2", encoding="utf-8")
            subprocess.run(["git", "commit", "-am", "h"], cwd=r, check=True)
            h = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=r, text=True
            ).strip()

            # 1. No .pre-commit-config.yaml
            passed, msg = runner_shared.check_lane_hook_bypass(r, b, h)
            self.assertTrue(passed)
            self.assertIn("unavailable", msg)
            self.assertIn(".pre-commit-config.yaml absent", msg)

            # Add config
            (r / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

            # 2. pre-commit missing
            with mock.patch("shutil.which", return_value=None):
                passed, msg = runner_shared.check_lane_hook_bypass(r, b, h)
                self.assertTrue(passed)
                self.assertIn("unavailable", msg)
                self.assertIn("pre-commit not installed", msg)

            # 3. pre-commit exit 3 (environment install error)
            orig_sub_run = subprocess.run

            def fake_pre_commit_run(cmd, *a, **k):
                if cmd and "pre-commit" in cmd[0]:
                    return mock.Mock(returncode=3, stdout="", stderr="network error")
                return orig_sub_run(cmd, *a, **k)

            with mock.patch("subprocess.run", side_effect=fake_pre_commit_run):
                passed, msg = runner_shared.check_lane_hook_bypass(r, b, h)
                self.assertTrue(passed)
                self.assertIn("unavailable", msg)
                self.assertIn("exit 3", msg)

            # 4. base == head
            passed, msg = runner_shared.check_lane_hook_bypass(r, b, b)
            self.assertTrue(passed)
            self.assertEqual(msg, "")

    def test_lane_working_tree_unchanged_by_hook_check(self):
        """The lane's working tree is byte-identical before and after check_lane_hook_bypass."""
        _td, repo, _plan, _run_dir, _state, _item = self._setup_repo(
            pre_commit_cfg=_SYSTEM_PRE_COMMIT_CONFIG
        )
        base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
        (repo / "f.txt").write_text("REFUSE_HOOK", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "bypass", "--no-verify"], cwd=repo, check=True
        )
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()

        st_before = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo, text=True
        )
        passed, _msg = runner_shared.check_lane_hook_bypass(repo, base, head)
        self.assertFalse(passed)
        st_after = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo, text=True
        )
        self.assertEqual(st_before, st_after)
        self.assertEqual(st_before, "")
