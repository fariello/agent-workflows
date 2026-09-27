"""Tests for finished carrier verification turn in runs.

carrierwarn Order 01 (`cnzrxb`) E-06.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import check_engine as ce
from agent_workflows import oc_runipd, runner_shared
from agent_workflows.render_stream import refusal_of_item
from tests import support
from tests.test_oc_runipd import _CONFORMING_PLAN, _init_repo_with_conforming_plan


class CarrierFinishedVerificationTests(unittest.TestCase):
    """Outcome tests for carrier finished verification turn in runs (E-06)."""

    def setUp(self) -> None:
        support.declare_execution_role(self)

    def _mk_run_dir(self, repo: Path) -> Path:
        run_dir = repo / ".aw" / "records" / "runs" / "run-test"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (run_dir / "sessions").mkdir(parents=True, exist_ok=True)
        return run_dir

    def _setup_repo_with_plans(
        self,
        td: str,
        *,
        carrier_target: str = "pl000b",
    ) -> tuple[Path, Path, Path]:
        repo = Path(td) / "repo"
        # Plan B
        plan_b = _init_repo_with_conforming_plan(repo, "pl000b")

        # Project config with carrier cutover
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text(
            json.dumps({"cutovers": {"carrier_obligations": "20260901"}}),
            encoding="utf-8",
        )

        # Plan A deferring to carrier_target
        pending = repo / ".aw" / "records" / "plans" / "pending"
        plan_a_text = _CONFORMING_PLAN.format(id6="pl000a")
        # Add deferred carrier row
        plan_a_text = plan_a_text.replace(
            "## Deferred / out of scope (with reason)\n\nnone.",
            f"## Deferred / out of scope (with reason)\n\n- Row 1 deferred\n  - Carrier: {carrier_target}",
        )
        plan_a = pending / "20260828-demo-01-pl000a-demo.ipd.md"
        plan_a.write_text(plan_a_text, encoding="utf-8")

        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "add plan a and config"], cwd=repo, check=True
        )

        return repo, plan_a, plan_b

    def _oc_state_and_item(self, repo: Path, plan_b: Path) -> tuple[dict, dict]:
        item = {
            "position": 1,
            "id6": "pl000b",
            "setid": "demo",
            "status": "queued",
            "configured_file": str(plan_b.relative_to(repo)),
            "action": "execute",
        }
        state = {
            "run_id": "run-test",
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:00:00+00:00",
            "selectors": ["demo"],
            "repo": str(repo),
            "queue": [item],
            "set_sessions": {},
            "session_id": None,
            "options": {
                "opencode": "/bin/true",
                "model": "opus",
                "self_finalize": True,
                "isolate_worktree": True,
                "no_audit": False,
            },
        }
        return state, item

    def test_carrier_verification_resolved_integrates_without_refusal(self) -> None:
        """Case (a): double answers verification turn by adding Carrier-Evidence ->
        B integrates, A's row resolved, no refusal recorded."""
        with tempfile.TemporaryDirectory() as td:
            repo, plan_a, plan_b = self._setup_repo_with_plans(
                td, carrier_target="pl000b"
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan_b)

            verification_turn_called = []

            def fake_run(state, rd, itm, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                log_suffix = kwargs.get("log_suffix", "")

                if kwargs.get("fresh_session") or log_suffix == "verify":
                    (
                        rd
                        / "outcomes"
                        / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                    ).write_text(
                        json.dumps(
                            {
                                "verdict": "VERIFIED",
                                "tests_run": ["python3 -m unittest tests.test_demo -v"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "vses", str(rd / "vlog"), ["oc"]

                if log_suffix == "carrier-verification":
                    verification_turn_called.append(kwargs)
                    wt = Path(work_dir)
                    # Add Carrier-Evidence to plan A in the lane worktree
                    wt_plan_a = (
                        wt / ".aw" / "records" / "plans" / "pending" / plan_a.name
                    )
                    text = wt_plan_a.read_text(encoding="utf-8")
                    text = text.replace(
                        "- Carrier: pl000b",
                        "- Carrier: pl000b\n  - Carrier-Evidence: .aw/records/plans/executed/20260828-demo-01-pl000b-demo.ipd.md",
                    )
                    wt_plan_a.write_text(text, encoding="utf-8")
                    subprocess.run(["git", "add", str(wt_plan_a)], cwd=wt, check=True)
                    subprocess.run(
                        ["git", "commit", "-qm", "carrier-evidence on plan a"],
                        cwd=wt,
                        check=True,
                    )
                    return 0, "ses1", str(rd / "carrier-verif-log"), ["oc"]

                # Main execution turn
                target_dir = Path(work_dir) if work_dir else Path(state["repo"])
                (target_dir / "src").mkdir(parents=True, exist_ok=True)
                (target_dir / "src" / "demo.txt").write_text("done\n", encoding="utf-8")
                subprocess.run(
                    ["git", "add", "src/demo.txt"], cwd=target_dir, check=True
                )
                subprocess.run(
                    ["git", "commit", "-qm", "demo: create src/demo.txt"],
                    cwd=target_dir,
                    check=True,
                )
                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                ).write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(verification_turn_called), 1)
            self.assertEqual(item["status"], "executed")
            self.assertIsNone(refusal_of_item(item))

            # In main repo after integration, plan A's obligation is carried and resolved
            remaining = ce.find_obligations_carried_by(repo, "pl000b")
            self.assertEqual(remaining, [])

    def test_carrier_verification_unresolved_records_refusal_and_still_integrates(
        self,
    ) -> None:
        """Case (b): double changes nothing -> item B carries unresolved-verification
        refusal record AND STILL INTEGRATES, refusal readable on item."""
        with tempfile.TemporaryDirectory() as td:
            repo, plan_a, plan_b = self._setup_repo_with_plans(
                td, carrier_target="pl000b"
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan_b)

            verification_turn_called = []

            def fake_run(state, rd, itm, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                log_suffix = kwargs.get("log_suffix", "")

                if kwargs.get("fresh_session") or log_suffix == "verify":
                    (
                        rd
                        / "outcomes"
                        / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                    ).write_text(
                        json.dumps(
                            {
                                "verdict": "VERIFIED",
                                "tests_run": ["python3 -m unittest tests.test_demo -v"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "vses", str(rd / "vlog"), ["oc"]

                if log_suffix == "carrier-verification":
                    verification_turn_called.append(kwargs)
                    # Agent does nothing to resolve plan A
                    return 0, "ses1", str(rd / "carrier-verif-log"), ["oc"]

                target_dir = Path(work_dir) if work_dir else Path(state["repo"])
                (target_dir / "src").mkdir(parents=True, exist_ok=True)
                (target_dir / "src" / "demo.txt").write_text("done\n", encoding="utf-8")
                subprocess.run(
                    ["git", "add", "src/demo.txt"], cwd=target_dir, check=True
                )
                subprocess.run(
                    ["git", "commit", "-qm", "demo: create src/demo.txt"],
                    cwd=target_dir,
                    check=True,
                )
                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                ).write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(verification_turn_called), 1)
            # Item STILL INTEGRATED
            self.assertEqual(item["status"], "executed")

            ref = refusal_of_item(item)
            self.assertIsNotNone(ref)
            self.assertEqual(ref.code, runner_shared.CARRIER_VERIFICATION_REFUSAL_CODE)
            self.assertEqual(ref.code, "carrier-verification-unresolved")
            self.assertIn("pl000b", ref.reason)
            self.assertIn("Carrier-Evidence", ref.remedy)
            self.assertIn("re-point", ref.remedy)

            # Structural bound: drive perform_carrier_verification a second time on same attempt
            att = item["attempts"][0]
            self.assertTrue(att.get("carrier_verification_asked"))
            rem = runner_shared.perform_carrier_verification(
                target_repo=repo,
                b_id6="pl000b",
                item=item,
                attempt=att,
                state=state,
                run_dir=run_dir,
                plan_path=plan_b,
                attempt_no=1,
                raw_launcher=fake_run,
                host_labels=runner_shared.OC_HOST_LABELS,
                tracker=None,
                work_dir=repo,
                session_turn_counts=None,
            )
            # Still exactly 1 verification call made, structural bound prevented second turn
            self.assertEqual(len(verification_turn_called), 1)
            self.assertEqual(len(rem), 1)

    def test_no_verification_turn_when_no_carrier_obligation(self) -> None:
        """Case (c): no plan names B -> no verification turn is dispatched (call count unchanged)."""
        with tempfile.TemporaryDirectory() as td:
            repo, plan_a, plan_b = self._setup_repo_with_plans(
                td, carrier_target="pl000z"
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan_b)

            verification_turn_called = []

            def fake_run(state, rd, itm, plan_path, prompt_path, attempt_no, **kwargs):
                work_dir = kwargs.get("work_dir")
                log_suffix = kwargs.get("log_suffix", "")

                if kwargs.get("fresh_session") or log_suffix == "verify":
                    (
                        rd
                        / "outcomes"
                        / f"{itm['position']:02d}-{itm['id6']}-verification.json"
                    ).write_text(
                        json.dumps(
                            {
                                "verdict": "VERIFIED",
                                "tests_run": ["python3 -m unittest tests.test_demo -v"],
                            }
                        ),
                        encoding="utf-8",
                    )
                    return 0, "vses", str(rd / "vlog"), ["oc"]

                if log_suffix == "carrier-verification":
                    verification_turn_called.append(kwargs)
                    return 0, "ses1", str(rd / "carrier-verif-log"), ["oc"]

                target_dir = Path(work_dir) if work_dir else Path(state["repo"])
                (target_dir / "src").mkdir(parents=True, exist_ok=True)
                (target_dir / "src" / "demo.txt").write_text("done\n", encoding="utf-8")
                subprocess.run(
                    ["git", "add", "src/demo.txt"], cwd=target_dir, check=True
                )
                subprocess.run(
                    ["git", "commit", "-qm", "demo: create src/demo.txt"],
                    cwd=target_dir,
                    check=True,
                )
                (
                    rd / "outcomes" / f"{itm['position']:02d}-{itm['id6']}.json"
                ).write_text(
                    json.dumps(
                        {
                            "disposition": "executed",
                            "pushed": False,
                            "defect_report": {"state": "none-found", "findings": []},
                        }
                    ),
                    encoding="utf-8",
                )
                return 0, "ses1", str(rd / "log"), ["oc"]

            with mock.patch.object(oc_runipd, "run_opencode", fake_run):
                oc_runipd.execute_item(run_dir, state, item, recovery=False)

            self.assertEqual(len(verification_turn_called), 0)
            self.assertEqual(item["status"], "executed")

    def test_launcher_path_invariant_and_session_continuity(self) -> None:
        """Case (d): verification turn goes through resume_via_launcher with attempt session,
        branching correctly for OC (resume_session) and AGY (session_id + use_continue=False)."""
        with tempfile.TemporaryDirectory() as td:
            repo, plan_a, plan_b = self._setup_repo_with_plans(
                td, carrier_target="pl000b"
            )
            run_dir = self._mk_run_dir(repo)
            state, item = self._oc_state_and_item(repo, plan_b)

            # Test OC host branch
            oc_calls = []

            def oc_launcher(*args, **kwargs):
                oc_calls.append((args, kwargs))
                return 0, "ses-oc", Path("/tmp/log"), ["oc"]

            att_oc = {"session_id": "ses-oc-123"}
            runner_shared.perform_carrier_verification(
                target_repo=repo,
                b_id6="pl000b",
                item=item,
                attempt=att_oc,
                state=state,
                run_dir=run_dir,
                plan_path=plan_b,
                attempt_no=1,
                raw_launcher=oc_launcher,
                host_labels=runner_shared.OC_HOST_LABELS,
                tracker=None,
                work_dir=repo,
            )

            self.assertEqual(len(oc_calls), 1)
            oc_args, oc_kwargs = oc_calls[0]
            self.assertEqual(oc_kwargs.get("resume_session"), "ses-oc-123")
            self.assertEqual(oc_kwargs.get("log_suffix"), "carrier-verification")
            self.assertEqual(oc_kwargs.get("label_suffix"), "carrier-verification")
            self.assertEqual(oc_kwargs.get("work_dir"), repo)

            # Test AGY host branch
            agy_calls = []

            def agy_launcher(*args, **kwargs):
                agy_calls.append((args, kwargs))
                return 0, "ses-agy", Path("/tmp/log"), ["agy"]

            att_agy = {"session_id": "ses-agy-456"}
            runner_shared.perform_carrier_verification(
                target_repo=repo,
                b_id6="pl000b",
                item=item,
                attempt=att_agy,
                state=state,
                run_dir=run_dir,
                plan_path=plan_b,
                attempt_no=1,
                raw_launcher=agy_launcher,
                host_labels=runner_shared.AGY_HOST_LABELS,
                tracker=None,
                work_dir=repo,
            )

            self.assertEqual(len(agy_calls), 1)
            agy_args, agy_kwargs = agy_calls[0]
            self.assertEqual(agy_kwargs.get("session_id"), "ses-agy-456")
            self.assertIs(agy_kwargs.get("use_continue"), False)
            self.assertEqual(agy_kwargs.get("log_suffix"), "carrier-verification")
            self.assertEqual(agy_kwargs.get("label_suffix"), "carrier-verification")
            self.assertEqual(agy_kwargs.get("work_dir"), repo)


if __name__ == "__main__":
    unittest.main()
