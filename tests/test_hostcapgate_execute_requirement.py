"""Behavioral tests proving the fresh-verifier host capability gate for execute actions (y9m1ya).

Five falsifiable properties asserted on outcomes across both runner hosts:
(a) INERTNESS: a capable host dispatches execute items without host capability refusal;
(b) REACHABILITY: an incapable host descriptor refuses execute items with fail-gate,
    host_capability_unavailable, no agent session started, and no repository mutation;
(c) CASCADE: a host-capability-refused item cascades unsatisfied dependencies to its
    dependents, while independent items continue without aborting the run;
(d) MESSAGE: recorded operator message matches the spec verbatim template naming the
    real capability, the real item, action 'execute', and an invocable recovery command;
(e) UNCLASSIFIED ACTIONS UNTOUCHED: review actions on an incapable host remain unclassified
    and are not refused by this gate.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    render_stream,
    runner_shared,
)
from agent_workflows import (
    host_sandbox_profile as hsp,
)
from agent_workflows import (
    run_selection_policy as rsp,
)
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN, _init_repo_with_conforming_plan


class TestHostCapGateExecuteRequirement(unittest.TestCase):
    """Behavioral tests for the execute action fresh-verifier capability requirement."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _state_and_item(
        self,
        repo: Path,
        plan: Path,
        cli_host: str,
        *,
        action: str = "execute",
        supports_fresh_verifier: bool = True,
        item_id: str = "exe001",
    ) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": item_id,
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan.relative_to(repo)),
            "action": action,
        }
        options = {
            "model": "test-model",
            "self_finalize": False,
            "isolate_worktree": False,
            "no_audit": True,
            "no_verify": True,
        }
        if cli_host == "opencode":
            options["opencode"] = "/bin/true"

        state = {
            "run_id": "run-test",
            "created_at": "2026-10-09T00:00:00+00:00",
            "updated_at": "2026-10-09T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "host_capabilities": {
                "host": cli_host,
                "observed_at": "2026-10-09T00:00:00+00:00",
                "descriptor": {
                    "supports_fresh_verifier_session": supports_fresh_verifier,
                },
            },
            "options": options,
        }
        return state, item

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "events.jsonl").touch()
        return run_dir

    # -------------------------------------------------------------------------
    # Property (a): INERTNESS
    # -------------------------------------------------------------------------

    def test_capable_host_execute_item_dispatches_inert_opencode(self) -> None:
        """Capable host execute item dispatches normally on OpenCode."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "exe001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo, plan, "opencode", supports_fresh_verifier=True
            )

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("opencode")
                (run_dir / "outcomes" / "01-exe001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                dest = repo / ".aw" / "records" / "plans" / "executed" / plan.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                plan.rename(dest)
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            with (
                mock.patch.object(oc_runipd, "run_opencode", fake_turn),
                mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(launched, ["opencode"])
            self.assertEqual(item["status"], "executed")
            self.assertIsNone(render_stream.refusal_of_item(item))

            events_path = run_dir / "events.jsonl"
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            cap_events = [
                e for e in events if e.get("event") == "host-capability-unavailable"
            ]
            self.assertEqual(cap_events, [])

    def test_capable_host_execute_item_dispatches_inert_antigravity(self) -> None:
        """Capable host execute item dispatches normally on Antigravity."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo,
                plan,
                "antigravity",
                supports_fresh_verifier=True,
                item_id="agy001",
            )

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("antigravity")
                (run_dir / "outcomes" / "01-agy001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                dest = repo / ".aw" / "records" / "plans" / "executed" / plan.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                plan.rename(dest)
                return 0, "ses1", str(run_dir / "log"), ["agy"]

            with (
                mock.patch.object(agy_runipd, "run_agy_turn", fake_turn),
                mock.patch.object(
                    agy_runipd, "driver_begin", lambda *a, **k: (0, "ok")
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(launched, ["antigravity"])
            self.assertEqual(item["status"], "executed")
            self.assertIsNone(render_stream.refusal_of_item(item))

            events_path = run_dir / "events.jsonl"
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            cap_events = [
                e for e in events if e.get("event") == "host-capability-unavailable"
            ]
            self.assertEqual(cap_events, [])

    # -------------------------------------------------------------------------
    # Property (b): REACHABILITY
    # -------------------------------------------------------------------------

    def test_incapable_host_execute_item_refused_no_session_no_mutation_opencode(
        self,
    ) -> None:
        """Incapable host descriptor refuses OpenCode execute item with fail-gate, no session, no mutation."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "exe001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo, plan, "opencode", supports_fresh_verifier=False
            )

            head_before = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("opencode")
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            with (
                mock.patch.object(oc_runipd, "run_opencode", fake_turn),
                mock.patch.object(oc_runipd, "driver_begin", lambda *a, **k: (0, "ok")),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            # 1. No agent session was started
            self.assertEqual(
                launched, [], "no session must be started on capability refusal"
            )

            # 2. Item recorded fail-gate status
            self.assertEqual(item["status"], "fail-gate")

            # 3. Refusal recorded with reason code host_capability_unavailable
            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            assert refusal is not None
            self.assertEqual(refusal.code, rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE)
            self.assertEqual(refusal.code, "host_capability_unavailable")
            self.assertIn("supports_fresh_verifier_session", refusal.reason)

            # 4. Attempt recorded with fail-gate disposition
            self.assertTrue(item.get("attempts"))
            last_attempt = item["attempts"][-1]
            self.assertEqual(last_attempt["disposition"], "fail-gate")
            self.assertIn("host_capability_unavailable", last_attempt)

            # 5. Events recorded host-capability-unavailable event
            events_path = run_dir / "events.jsonl"
            self.assertTrue(events_path.is_file())
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            cap_events = [
                e for e in events if e.get("event") == "host-capability-unavailable"
            ]
            self.assertEqual(len(cap_events), 1)
            self.assertEqual(cap_events[0]["id6"], "exe001")
            self.assertEqual(
                cap_events[0]["missing"], ["supports_fresh_verifier_session"]
            )

            # 6. No mutation occurred in repository
            head_after = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            self.assertEqual(head_before, head_after)
            git_status = subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=repo, text=True
            ).strip()
            # Only uncommitted run records may exist under .aw/records/runs
            status_lines = [
                line
                for line in git_status.splitlines()
                if not line.endswith(".aw/records/runs/run-test")
                and ".aw/records/runs" not in line
            ]
            self.assertEqual(
                status_lines, [], "no tracked repository mutation must occur"
            )

    def test_incapable_host_execute_item_refused_no_session_no_mutation_antigravity(
        self,
    ) -> None:
        """Incapable host descriptor refuses Antigravity execute item with fail-gate, no session, no mutation."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo,
                plan,
                "antigravity",
                supports_fresh_verifier=False,
                item_id="agy001",
            )

            head_before = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("antigravity")
                return 0, "ses1", str(run_dir / "log"), ["agy"]

            with (
                mock.patch.object(agy_runipd, "run_agy_turn", fake_turn),
                mock.patch.object(
                    agy_runipd, "driver_begin", lambda *a, **k: (0, "ok")
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(
                launched, [], "no session must be started on capability refusal"
            )
            self.assertEqual(item["status"], "fail-gate")

            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            assert refusal is not None
            self.assertEqual(refusal.code, rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE)
            self.assertEqual(refusal.code, "host_capability_unavailable")
            self.assertIn("supports_fresh_verifier_session", refusal.reason)

            head_after = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            self.assertEqual(head_before, head_after)

    # -------------------------------------------------------------------------
    # Property (c): CASCADE AND INDEPENDENT CONTINUATION
    # -------------------------------------------------------------------------

    def test_refused_item_cascades_dependents_and_independent_items_continue(
        self,
    ) -> None:
        """Refused execute item cascades dependency-not-met to dependents, and independent items continue."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan_refused = _init_repo_with_conforming_plan(repo, "ref001")

            pending = repo / ".aw" / "records" / "plans" / "pending"
            plan_dep = pending / "20261009-demo-02-dep001-dependent.ipd.md"
            plan_dep.write_text(
                _CONFORMING_PLAN.format(id6="dep001").replace(
                    "- Item-Dependencies: none", "- Item-Dependencies: executed:ref001"
                ),
                encoding="utf-8",
            )
            plan_ind = pending / "20261009-demo-03-ind001-independent.ipd.md"
            plan_ind.write_text(
                _CONFORMING_PLAN.format(id6="ind001"),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "add plans"], cwd=repo, check=True)

            run_dir = self._mk_run_dir(repo)

            item_ref = {
                "position": 1,
                "id6": "ref001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan_refused.relative_to(repo)),
                "action": "execute",
            }
            item_dep = {
                "position": 2,
                "id6": "dep001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan_dep.relative_to(repo)),
                "action": "execute",
                "dependencies": ["executed:ref001"],
            }
            item_ind = {
                "position": 3,
                "id6": "ind001",
                "setid": "demo",
                "status": "queued",
                "configured_file": str(plan_ind.relative_to(repo)),
                "action": "execute",
                "dependencies": [],
            }

            state = {
                "run_id": "run-test",
                "created_at": "2026-10-09T00:00:00+00:00",
                "updated_at": "2026-10-09T00:00:00+00:00",
                "selectors": ["demo"],
                "repo": str(repo),
                "queue": [item_ref, item_dep, item_ind],
                "set_sessions": {},
                "session_id": None,
                "host_capabilities": {
                    "host": "opencode",
                    "observed_at": "2026-10-09T00:00:00+00:00",
                    "descriptor": {
                        "supports_fresh_verifier_session": False,
                    },
                },
                "options": {
                    "model": "test-model",
                    "opencode": "/bin/true",
                    "self_finalize": False,
                    "isolate_worktree": False,
                    "no_audit": True,
                },
            }

            # 1. Execute item_ref on incapable host -> refused with fail-gate
            oc_runipd.execute_item(run_dir, state, item_ref, recovery=False)
            self.assertEqual(item_ref["status"], "fail-gate")

            # 2. Check dependent item_dep -> unsatisfied dependency causes dependency cascade
            sat_dep, unsat_dep, _reasons_dep = runner_shared.dependency_status_detailed(
                item_dep, state
            )
            self.assertFalse(sat_dep, "dependent item must have unsatisfied dependency")
            self.assertIn("executed:ref001", unsat_dep)

            # 3. Check independent item_ind -> dependencies satisfied; run is not aborted
            sat_ind, unsat_ind, _reasons_ind = runner_shared.dependency_status_detailed(
                item_ind, state
            )
            self.assertTrue(sat_ind, "independent item must be runnable")
            self.assertEqual(unsat_ind, [])

    def test_preflight_verdict_declares_cascade_and_does_not_abort(self) -> None:
        """preflight_host_capabilities explicitly specifies cascade_dependents=True, aborts_run=False."""
        caps = hsp.HostSandboxCapabilities(platform="linux")
        pre = hsp.preflight_host_capabilities(
            hsp.ACTION_EXECUTE, caps, host="opencode", item="exe001"
        )
        self.assertFalse(pre.ok)
        self.assertTrue(pre.cascade_dependents)
        self.assertFalse(pre.aborts_run)

    # -------------------------------------------------------------------------
    # Property (d): OPERATOR MESSAGE AND INVOCABLE RECOVERY COMMAND
    # -------------------------------------------------------------------------

    def test_operator_message_spec_verbatim_and_recovery_invocable_opencode(
        self,
    ) -> None:
        """OpenCode refusal message matches spec verbatim template and recovery command is invocable."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "exe001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo, plan, "opencode", supports_fresh_verifier=False
            )

            oc_runipd.execute_item(run_dir, state, item, recovery=False)

            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            assert refusal is not None

            expected_message = (
                "[RUN-HOST-CAPABILITY] Host opencode cannot enforce "
                "supports_fresh_verifier_session required by exe001 action execute. "
                "No work started for this item. Choose a capable host or enable and "
                "re-probe that capability, then run: aw opencode run exe001"
            )
            self.assertEqual(refusal.reason, expected_message)

            # Check that the recovery command name is invocable
            proc = subprocess.run(
                ["aw", "opencode", "run", "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode, 0, f"recovery command failed: {proc.stderr}"
            )

    def test_operator_message_spec_verbatim_and_recovery_invocable_antigravity(
        self,
    ) -> None:
        """Antigravity refusal message matches spec verbatim template and recovery command is invocable."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "agy001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo,
                plan,
                "antigravity",
                supports_fresh_verifier=False,
                item_id="agy001",
            )

            agy_runipd.execute_item(run_dir, state, item, recovery=False)

            refusal = render_stream.refusal_of_item(item)
            self.assertIsNotNone(refusal)
            assert refusal is not None

            expected_message = (
                "[RUN-HOST-CAPABILITY] Host antigravity cannot enforce "
                "supports_fresh_verifier_session required by agy001 action execute. "
                "No work started for this item. Choose a capable host or enable and "
                "re-probe that capability, then run: aw antigravity run agy001"
            )
            self.assertEqual(refusal.reason, expected_message)

            # Check that the recovery command name is invocable
            proc = subprocess.run(
                ["aw", "antigravity", "run", "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                proc.returncode, 0, f"recovery command failed: {proc.stderr}"
            )

    # -------------------------------------------------------------------------
    # Property (e): UNCLASSIFIED ACTIONS UNTOUCHED
    # -------------------------------------------------------------------------

    def test_unclassified_review_action_not_refused_on_incapable_host_opencode(
        self,
    ) -> None:
        """Review action on incapable host descriptor is not refused by capability preflight (OpenCode)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "rev001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo,
                plan,
                "opencode",
                action="review",
                supports_fresh_verifier=False,
                item_id="rev001",
            )

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("opencode")
                (run_dir / "outcomes" / "01-rev001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "substantially-complete",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(run_dir / "log"), ["opencode"]

            with (
                mock.patch.object(oc_runipd, "run_opencode", fake_turn),
            ):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(launched, ["opencode"], "review turn must be launched")
            refusal = render_stream.refusal_of_item(item)
            self.assertTrue(
                refusal is None or refusal.code != rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE,
                "review action must not be refused by host capability check",
            )

            events_path = run_dir / "events.jsonl"
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            cap_events = [
                e for e in events if e.get("event") == "host-capability-unavailable"
            ]
            self.assertEqual(cap_events, [])

    def test_unclassified_review_action_not_refused_on_incapable_host_antigravity(
        self,
    ) -> None:
        """Review action on incapable host descriptor is not refused by capability preflight (Antigravity)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            plan = _init_repo_with_conforming_plan(repo, "rev001")
            run_dir = self._mk_run_dir(repo)
            state, item = self._state_and_item(
                repo,
                plan,
                "antigravity",
                action="review",
                supports_fresh_verifier=False,
                item_id="rev001",
            )

            launched: list[str] = []

            def fake_turn(*a: object, **k: object) -> tuple[int, str, str, list[str]]:
                launched.append("antigravity")
                (run_dir / "outcomes" / "01-rev001.json").write_text(
                    json.dumps(
                        {
                            "disposition": "substantially-complete",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(run_dir / "log"), ["agy"]

            with (
                mock.patch.object(agy_runipd, "run_agy_turn", fake_turn),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(launched, ["antigravity"], "review turn must be launched")
            refusal = render_stream.refusal_of_item(item)
            self.assertTrue(
                refusal is None or refusal.code != rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE,
                "review action must not be refused by host capability check",
            )

            events_path = run_dir / "events.jsonl"
            events = [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            cap_events = [
                e for e in events if e.get("event") == "host-capability-unavailable"
            ]
            self.assertEqual(cap_events, [])


if __name__ == "__main__":
    unittest.main()
