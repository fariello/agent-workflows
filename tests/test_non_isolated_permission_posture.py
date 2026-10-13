"""Tests for non-isolated unattended opencode turn permission posture (spec 7ckptx R4.1d)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import lane_containment, oc_runipd


class SentinelLaunchError(Exception):
    """Raised by fake Popen to intercept the agent launch and capture its env."""

    def __init__(self, env: dict[str, str] | None) -> None:
        super().__init__("agent launch intercepted")
        self.env = env or {}


_REAL_POPEN = subprocess.Popen


def _fake_popen(cmd: object, *args: object, **kwargs: object) -> object:
    cmd_list = cmd if isinstance(cmd, (list, tuple)) else [cmd]
    if cmd_list and (cmd_list[0] == "git" or str(cmd_list[0]).endswith("/git")):
        return _REAL_POPEN(cmd, *args, **kwargs)
    raise SentinelLaunchError(kwargs.get("env"))


def _run_turn_harness(
    *,
    work_dir: str | None = None,
    operator_config: str | None = None,
) -> tuple[dict[str, str], dict[str, object]]:
    """Drive run_opencode in an isolated temp repo without launching a real agent."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        (repo / "README").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

        run_dir = root / "run"
        run_dir.mkdir()
        plan_path = repo / "plan.ipd.md"
        plan_path.write_text("# Plan\n", encoding="utf-8")
        prompt_path = repo / "prompt.md"
        prompt_path.write_text("prompt\n", encoding="utf-8")

        state = {
            "run_id": "run-test-posture",
            "repo": str(repo),
            "options": {"opencode": "/bin/false"},
        }
        item = {
            "id6": "tst001",
            "setid": "tstset",
            "position": 1,
            "action": "execute",
        }

        fixed_observation = lane_containment.evaluate_policy_observation(
            json.dumps({"permission": {"question": "deny"}}),
            {"question": "deny"},
            host_version="1.18.35",
        )

        with mock.patch.dict(os.environ):
            if operator_config is not None:
                os.environ["OPENCODE_CONFIG_CONTENT"] = operator_config
            else:
                os.environ.pop("OPENCODE_CONFIG_CONTENT", None)

            with mock.patch(
                "agent_workflows.oc_runipd.observe_opencode_policy",
                return_value=fixed_observation,
            ):
                with mock.patch("subprocess.Popen", side_effect=_fake_popen):
                    try:
                        oc_runipd.run_opencode(
                            state,
                            run_dir,
                            item,
                            plan_path,
                            prompt_path,
                            attempt_no=1,
                            work_dir=work_dir,
                        )
                    except SentinelLaunchError as exc:
                        child_env = exc.env

        return child_env, item


class NonIsolatedPermissionPostureTests(unittest.TestCase):
    def test_non_isolated_no_operator_value_denies_question_only(self) -> None:
        """(a) NON-ISOLATED, no operator value: config is {"permission": {"question": "deny"}}."""
        child_env, _ = _run_turn_harness(work_dir=None, operator_config=None)
        self.assertIn("OPENCODE_CONFIG_CONTENT", child_env)
        decoded = json.loads(child_env["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(decoded, {"permission": {"question": "deny"}})
        self.assertNotIn("external_directory", decoded.get("permission", {}))

    def test_isolated_no_operator_value_denies_both_classes(self) -> None:
        """(b) ISOLATED: decoded value denies both external_directory and question."""
        with tempfile.TemporaryDirectory() as lane_temp:
            child_env, _ = _run_turn_harness(work_dir=lane_temp, operator_config=None)
        self.assertIn("OPENCODE_CONFIG_CONTENT", child_env)
        decoded = json.loads(child_env["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(
            decoded,
            {"permission": {"external_directory": "deny", "question": "deny"}},
        )

    def test_non_isolated_with_operator_value_merges_and_preserves_keys(self) -> None:
        """(c) NON-ISOLATED with operator value: merges, preserves extra keys and allow for external_directory."""
        operator_val = json.dumps(
            {
                "permission": {"external_directory": "allow", "question": "allow"},
                "x": 1,
            }
        )
        child_env, item = _run_turn_harness(work_dir=None, operator_config=operator_val)
        self.assertIn("OPENCODE_CONFIG_CONTENT", child_env)
        decoded = json.loads(child_env["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(decoded.get("x"), 1)
        self.assertEqual(
            decoded.get("permission"),
            {"external_directory": "allow", "question": "deny"},
        )
        host_posture = item.get("host_posture", {})
        self.assertEqual(host_posture.get("policy_source"), "merged-with-operator")

    def test_non_isolated_posture_record_reports_partial_denial(self) -> None:
        """(d) NON-ISOLATED posture record: posture == 'partial-denial' and reason mentions external_directory."""
        _, item = _run_turn_harness(work_dir=None, operator_config=None)
        host_posture = item.get("host_posture", {})
        self.assertEqual(host_posture.get("posture"), "partial-denial")
        self.assertEqual(host_posture.get("requested_policy"), {"question": "deny"})
        self.assertIn("policy_observation", host_posture)
        reason = host_posture.get("reason", "")
        self.assertIn("external_directory", reason)
        self.assertIn("not denied", reason)

    def test_isolated_posture_record_reports_denied(self) -> None:
        """(e) The isolated posture record still has posture == 'denied'."""
        with tempfile.TemporaryDirectory() as lane_temp:
            _, item = _run_turn_harness(work_dir=lane_temp, operator_config=None)
        host_posture = item.get("host_posture", {})
        self.assertEqual(host_posture.get("posture"), "denied")
        self.assertEqual(
            host_posture.get("requested_policy"),
            {"external_directory": "deny", "question": "deny"},
        )

    def test_non_isolated_with_unparseable_operator_value_loudly_overrides(
        self,
    ) -> None:
        """(f) NON-ISOLATED with unparseable operator value: loud override and question denied."""
        child_env, item = _run_turn_harness(work_dir=None, operator_config="not json")
        self.assertIn("OPENCODE_CONFIG_CONTENT", child_env)
        decoded = json.loads(child_env["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(decoded, {"permission": {"question": "deny"}})
        host_posture = item.get("host_posture", {})
        self.assertEqual(
            host_posture.get("policy_source"), "override-unparseable-operator"
        )
