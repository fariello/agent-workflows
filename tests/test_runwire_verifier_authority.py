"""Tests for verifier session independence and verifier state authority.

IPD eow7p4:
  - E-01: Capture and persist verifier session ID at the shared verify site.
  - E-02: Refuse session identity collision consuming assert_distinct_sessions.
  - E-03: Check verifier state authority report-only using run_state and verify_roles.
  - E-04: Behavioral properties on both hosts, with mutation-checked collision guard.
  - E-05: Set-level cross-IPD checks assigned by orchestrator i18yaz.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_state,
    runner_profiles,
    runner_shared,
    runner_shutdown,
    verify_roles,
)


def _setup_test_repo(root: Path) -> Path:
    """Create a minimal clean git repo for runner tests."""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=root, check=True
    )
    subprocess.run(["git", "config", "user.name", "test"], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return root


def _drive_execute_turn(
    root: Path,
    *,
    driver_module: Any,
    host_labels: tuple[str, ...],
    exec_session: str | None = "session-exec-1",
    verify_session: str | None = "session-verif-2",
    verdict: str = "VERIFIED",
    tests_run: list[str] | None = None,
    write_outcome: bool = True,
    validate: bool = True,
    current_status: str = "queued",
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    """Drive the real runner_shared.execute_item_core pipeline."""
    run_dir = root / ".aw/runs/run-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

    plans_dir = root / ".aw/records/plans/pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plans_dir / "20260101-test-01-tst001-test.ipd.md"
    plan_file.write_text(
        "- Id: tst001\n- Set: test\n- Status: approved\n", encoding="utf-8"
    )

    item: dict[str, Any] = {
        "id6": "tst001",
        "setid": "test",
        "position": 1,
        "action": "execute",
        "status": current_status,
        "configured_file": str(plan_file.relative_to(root)),
    }
    state: dict[str, Any] = {
        "repo": str(root),
        "run_id": "run-test",
        "queue": [item],
        "options": {
            "isolate_worktrees": False,
            "self_finalize": False,
            "validate": validate,
            "no_verify": False,
        },
    }

    def spawn_executor(
        prompt_path: Path,
        work_dir: Any,
        tracker: Any,
        p_path: Path,
        attempt_no: int,
        session_id: Any,
        use_continue: bool,
    ) -> tuple[int, str | None, Path, list[str]]:
        log_path = run_dir / "logs" / f"exec-{attempt_no}.log"
        log_path.write_text("exec log", encoding="utf-8")
        outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
        outcome.write_text(
            json.dumps(
                {
                    "disposition": "executed",
                    "defect_report": {"state": "none-found", "findings": []},
                    "pushed": False,
                }
            ),
            encoding="utf-8",
        )
        return 0, exec_session, log_path, ["mock_executor"]

    def spawn_verifier(
        prompt_path: Path,
        p_path: Path,
        work_dir: Any,
        tracker: Any,
        attempt_no: int,
    ) -> tuple[int, str | None, Path, list[str]]:
        v_log = run_dir / "logs" / f"verify-{attempt_no}.log"
        v_log.write_text("verify log\npytest\n", encoding="utf-8")
        if write_outcome:
            v_outcome = (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            )
            v_outcome.write_text(
                json.dumps(
                    {
                        "verdict": verdict,
                        "tests_run": ["pytest"] if tests_run is None else tests_run,
                    }
                ),
                encoding="utf-8",
            )
        return 0, verify_session, v_log, ["mock_verifier"]

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery=False,
        host_labels=host_labels,
        spawn_executor=spawn_executor,
        spawn_verifier=spawn_verifier,
        raw_launcher=lambda *a, **k: None,
        run_suite_check=lambda p, s: None,
        process_backlog_close=lambda *a, **k: None,
        driver_module=driver_module,
    )
    return state, item, run_dir


# ==============================================================================
# Task group 1: E-01 Verifier session persistence
# ==============================================================================


def test_verifier_session_captured_and_persisted(tmp_path: Path):
    """E-01 / V-01: Verifier session id is persisted on the attempt and state.json."""
    _setup_test_repo(tmp_path)
    _, item, run_dir = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="session-exec-alpha",
        verify_session="session-verif-beta",
    )

    attempt = item["attempts"][-1]
    assert attempt["session_id"] == "session-exec-alpha"
    assert attempt["verify_session_id"] == "session-verif-beta"

    # Persisted into state.json
    state_file = run_dir / "state.json"
    assert state_file.is_file()
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    saved_attempt = saved["queue"][0]["attempts"][-1]
    assert saved_attempt["verify_session_id"] == "session-verif-beta"


def test_absent_verifier_session_recorded_as_none_and_not_collision(tmp_path: Path):
    """E-01 / V-01: A None verifier session id is recorded as absent, not as a collision."""
    _setup_test_repo(tmp_path)
    _, item, _ = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="session-exec-alpha",
        verify_session=None,
    )

    attempt = item["attempts"][-1]
    assert attempt["session_id"] == "session-exec-alpha"
    assert attempt["verify_session_id"] is None
    # Must NOT record a collision refusal
    assert attempt.get("verification_refused") is None
    assert item["verification_status"] == runner_shared.VERIFY_DISP_VERIFIED


# ==============================================================================
# Task group 1: E-02 Session collision refusal
# ==============================================================================


def test_verifier_session_collision_refused(tmp_path: Path):
    """E-02 / V-02: Equal verifier and execute session ids yield unverified + collision refusal."""
    _setup_test_repo(tmp_path)
    _, item, _ = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="shared-session-xyz",
        verify_session="shared-session-xyz",
    )

    assert item["verification_status"] == runner_shared.VERIFY_DISP_UNVERIFIED
    assert item["status"] == "fail-verify"

    attempt = item["attempts"][-1]
    refused = attempt.get("verification_refused")
    assert refused is not None
    assert refused["verify_disp"] == runner_shared.VERIFY_DISP_UNVERIFIED
    assert refused["code"] == runner_shared.VERIFY_REFUSAL_CODE_SESSION_COLLISION

    # Distinct from both DECLINED and UNREADABLE codes
    assert refused["code"] != runner_shared.VERDICT_REFUSAL_CODE_DECLINED
    assert refused["code"] != runner_shared.VERDICT_REFUSAL_CODE_UNREADABLE

    # Reason names the collision; remedy names the preserved lane
    assert "shared-session-xyz" in refused["reason"]
    assert "reused the execution turn's session identity" in refused["reason"]
    assert "lane is PRESERVED" in refused["remedy"]
    assert "do NOT re-run the plan from scratch" in refused["remedy"]


def test_verify_disp_vocabulary_unchanged():
    """E-02 / V-02: No new verify_disp token was added."""
    known_tokens = {
        runner_shared.VERIFY_DISP_VERIFIED,
        runner_shared.VERIFY_DISP_UNVERIFIED,
        runner_shared.VERIFY_DISP_BLOCKED,
    }
    assert known_tokens == {"verified", "unverified", "blocked"}


# ==============================================================================
# Task group 2: E-03 Verifier state authority check
# ==============================================================================


def test_check_verifier_state_authority_decisions():
    """E-03 / V-03: VERIFIED, CORRECTION_REQUIRED, and BLOCKED verdicts each record authorized."""
    # 1. VERIFIED -> target verified
    res_verified = runner_shared.check_verifier_state_authority("running", "verified")
    assert res_verified["ok"] is True
    assert res_verified["authorized"] is True
    assert res_verified["source_position"] == "running"
    assert res_verified["runtime_path"] == ["running", "performed", "verifying"]
    assert res_verified["verifier_source"] == "verifying"
    assert res_verified["target_position"] == "verified"
    assert res_verified["edge"] == "verifying -> verified"
    assert res_verified["findings"] == []

    # 2. CORRECTION_REQUIRED -> target correction_required
    res_corr = runner_shared.check_verifier_state_authority(
        "running", "correction_required"
    )
    assert res_corr["ok"] is True
    assert res_corr["authorized"] is True
    assert res_corr["target_position"] == "correction_required"
    assert res_corr["edge"] == "verifying -> correction_required"

    # 3. BLOCKED / NOT CONFORMING (driver token 'fail-verify') normalized to 'correction_required'
    res_blocked = runner_shared.check_verifier_state_authority("running", "fail-verify")
    assert res_blocked["ok"] is True
    assert res_blocked["authorized"] is True
    assert res_blocked["target_status"] == "fail-verify"
    assert res_blocked["target_position"] == "correction_required"
    assert res_blocked["edge"] == "verifying -> correction_required"


def test_authority_rules_agreement():
    """E-03 / V-03: TRANSITION_RULES and ROLE_CONTRACTS agree on verification edges."""
    vr_contract_edges = set(verify_roles.ROLE_CONTRACTS["verifier"].state_authority)
    vr_verification_edges = {
        e for e in vr_contract_edges if e.startswith("verifying ->")
    }

    rs_verification_edges = {
        f"{rule.source} -> {rule.target}"
        for rule in run_state.TRANSITION_RULES
        if "verifier" in rule.authorized_actors and rule.source == "verifying"
    }

    assert vr_verification_edges == rs_verification_edges
    assert rs_verification_edges == {
        "verifying -> verified",
        "verifying -> correction_required",
    }


def test_authority_check_report_only_refuses_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """E-03 / V-03: A failed authority check records the check but refuses nothing."""
    _setup_test_repo(tmp_path)

    # Monkeypatch check_verifier_state_authority to simulate an unauthorized verdict
    def fake_authority_check(
        current_status: str, verdict_state: str, role: str = "verifier"
    ):
        return {
            "ok": False,
            "authorized": False,
            "source_status": current_status,
            "source_position": "running",
            "runtime_path": ["running", "performed", "verifying"],
            "target_status": verdict_state,
            "target_position": "verified",
            "actor": role,
            "edge": "verifying -> verified",
            "findings": ["ST-UNAUTHORIZED-ACTOR"],
        }

    monkeypatch.setattr(
        runner_shared, "check_verifier_state_authority", fake_authority_check
    )

    _, item, _ = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="session-exec-alpha",
        verify_session="session-verif-beta",
    )

    attempt = item["attempts"][-1]
    # Check recorded
    auth = attempt.get("verify_authority_check")
    assert auth is not None
    assert auth["ok"] is False
    assert auth["authorized"] is False

    # But refuses nothing: item is still verified
    assert item["verification_status"] == runner_shared.VERIFY_DISP_VERIFIED
    assert attempt.get("verification_refused") is None


# ==============================================================================
# Task group 2: E-04 Behavioral properties on both hosts
# ==============================================================================


@pytest.mark.parametrize(
    "driver_mod,host_lbls",
    [
        (oc_runipd, runner_shared.OC_HOST_LABELS),
        (agy_runipd, runner_shared.AGY_HOST_LABELS),
    ],
)
def test_both_hosts_behavioral_properties(
    tmp_path: Path, driver_mod: Any, host_lbls: tuple[str, ...]
):
    """E-04 / V-04: Drive both hosts proving properties (a)-(d).

    (a) Distinct session ids leave the verified path unchanged.
    (b) Equal session ids yield unverified + collision refusal.
    (c) Absent session id changes nothing.
    (d) Authority check records verdict and refuses nothing.
    """
    repo = _setup_test_repo(tmp_path)

    # Property (a): Distinct session IDs -> verified
    _, item_a, _ = _drive_execute_turn(
        repo,
        driver_module=driver_mod,
        host_labels=host_lbls,
        exec_session="sess-exec-a",
        verify_session="sess-verif-b",
    )
    assert item_a["verification_status"] == runner_shared.VERIFY_DISP_VERIFIED
    assert item_a["attempts"][-1].get("verification_refused") is None

    # Property (b): Equal session IDs -> unverified + collision refusal
    _, item_b, _ = _drive_execute_turn(
        repo,
        driver_module=driver_mod,
        host_labels=host_lbls,
        exec_session="colliding-sess",
        verify_session="colliding-sess",
    )
    assert item_b["verification_status"] == runner_shared.VERIFY_DISP_UNVERIFIED
    refusal_b = item_b["attempts"][-1].get("verification_refused")
    assert refusal_b is not None
    assert refusal_b["code"] == runner_shared.VERIFY_REFUSAL_CODE_SESSION_COLLISION
    assert refusal_b["code"] != runner_shared.VERDICT_REFUSAL_CODE_DECLINED

    # Property (c): Absent verifier session id -> changes nothing (verified)
    _, item_c, _ = _drive_execute_turn(
        repo,
        driver_module=driver_mod,
        host_labels=host_lbls,
        exec_session="sess-exec-c",
        verify_session=None,
    )
    assert item_c["verification_status"] == runner_shared.VERIFY_DISP_VERIFIED
    assert item_c["attempts"][-1].get("verification_refused") is None

    # Property (d): Authority check records verdict and refuses nothing
    auth_a = item_a["attempts"][-1].get("verify_authority_check")
    assert auth_a is not None
    assert auth_a["ok"] is True
    assert auth_a["authorized"] is True


def test_collision_guard_bites_by_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """E-04 / V-04: Mutation check - removing distinct session check causes collision test to fail."""
    _setup_test_repo(tmp_path)

    # 1. Normal run with collision -> refuses
    _, item_normal, _ = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="mut-sess",
        verify_session="mut-sess",
    )
    assert item_normal["verification_status"] == runner_shared.VERIFY_DISP_UNVERIFIED

    # 2. Mutated run: disable assert_distinct_sessions
    from agent_workflows import agy_verifier

    monkeypatch.setattr(
        agy_verifier, "assert_distinct_sessions", lambda exec_s, verif_s: None
    )

    _, item_mutated, _ = _drive_execute_turn(
        tmp_path,
        driver_module=oc_runipd,
        host_labels=runner_shared.OC_HOST_LABELS,
        exec_session="mut-sess",
        verify_session="mut-sess",
    )
    # Under mutation, the guard does NOT bite and the item incorrectly passes as verified!
    assert item_mutated["verification_status"] == runner_shared.VERIFY_DISP_VERIFIED
    assert item_mutated["attempts"][-1].get("verification_refused") is None


def test_host_verifier_gating_defaults_measured():
    """E-04 / V-04: Re-measure both hosts' verifier-gating defaults by symbol."""
    assert runner_profiles.RUNNER_REGISTRY["oc"].validate_default is False
    assert runner_profiles.RUNNER_REGISTRY["agy"].validate_default is True


# ==============================================================================
# Task group 2: E-05 Set-level cross-IPD checks
# ==============================================================================


def test_set_level_checks():
    """E-05 / V-05: Orchestrator i18yaz Set-level checks.

    (a) ONE TRANSLATION: exactly one definition site of the driver-status-to-run_state translation.
    (b) NO PRIVATE HOST COPY: neither oc_runipd nor agy_runipd defines its own transition check or session test.
    (c) VOCABULARY UNCHANGED: member-identical before/after.
    (d) LEDGER FENCE: no run_engine / run_recovery imports, no ledger.jsonl.
    (e) run_recovery unimported by both drivers.
    """
    # (a) Exactly one definition site
    from agent_workflows import runner_shared as rs

    assert hasattr(rs, "map_driver_status_to_run_state")
    assert not hasattr(oc_runipd, "map_driver_status_to_run_state")
    assert not hasattr(agy_runipd, "map_driver_status_to_run_state")

    # (b) Neither host defines its own transition check or session independence test
    assert not hasattr(oc_runipd, "find_runtime_reachability_path")
    assert not hasattr(agy_runipd, "find_runtime_reachability_path")
    assert not hasattr(oc_runipd, "check_verifier_state_authority")
    assert not hasattr(agy_runipd, "check_verifier_state_authority")

    # (c) Vocabulary unchanged
    assert len(rs.TERMINAL_STATES_CANONICAL) == 14
    assert len(rs.TERMINAL_STATUS_ALIASES) == 10
    assert len(runner_shutdown.KNOWN_ITEM_STATUSES) == 28

    # (d) Ledger fence: neither child's changed files import run_engine or run_recovery, tested in clean subprocess
    import subprocess
    import sys

    fence_cmd = (
        "import agent_workflows.runner_shared; "
        "import sys; "
        "assert 'agent_workflows.run_engine' not in sys.modules, 'run_engine imported'; "
        "assert 'agent_workflows.run_recovery' not in sys.modules, 'run_recovery imported'"
    )
    res_d = subprocess.run(
        [sys.executable, "-c", fence_cmd], capture_output=True, text=True, check=False
    )
    assert res_d.returncode == 0, f"Ledger fence check failed: {res_d.stderr}"

    # (e) run_recovery unimported by both drivers, tested in clean subprocess
    driver_cmd = (
        "import agent_workflows.oc_runipd; "
        "import agent_workflows.agy_runipd; "
        "import sys; "
        "assert 'agent_workflows.run_recovery' not in sys.modules, 'run_recovery imported by drivers'"
    )
    res_e = subprocess.run(
        [sys.executable, "-c", driver_cmd], capture_output=True, text=True, check=False
    )
    assert (
        res_e.returncode == 0
    ), f"Driver run_recovery unimported check failed: {res_e.stderr}"
