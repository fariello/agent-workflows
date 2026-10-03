"""Tests for runwire state translation and report-only transition check.

IPD 32jpl1:
  - E-02: Totality over driver vocabulary.
  - E-04: Inert on happy path, loud on real violation, exception safety.
  - E-05: Both hosts drive shared funnel without private copies (behavioral proof).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import (
    agy_runipd,
    oc_runipd,
    run_state,
    runner_shared,
    runner_shutdown,
)


def _make_queue_item(
    *,
    position: int = 1,
    id6: str = "item01",
    setid: str = "runwire",
    action: str = "execute",
    status: str = "queued",
) -> dict[str, Any]:
    return {
        "position": position,
        "id6": id6,
        "setid": setid,
        "action": action,
        "status": status,
    }


def test_totality_over_driver_vocabulary():
    """Assert every member of runner_shutdown.KNOWN_ITEM_STATUSES is accounted for.

    E-02: Asserts the property (totality) and NEVER a hardcoded count.
    Reads the intentionally-unmapped list directly from production data.
    """
    unaccounted: list[str] = []
    observed_tokens: list[str] = []

    for token in runner_shutdown.KNOWN_ITEM_STATUSES:
        observed_tokens.append(token)
        mapped = runner_shared.map_driver_status_to_run_state(token)
        if mapped is not None:
            assert (
                mapped in run_state.ALL_STATES
            ), f"Token {token!r} mapped to unknown run_state {mapped!r}"
        else:
            if token not in runner_shared.INTENTIONALLY_UNMAPPED_DRIVER_STATUSES:
                unaccounted.append(token)

    assert (
        not unaccounted
    ), f"Tokens in KNOWN_ITEM_STATUSES without translation decision: {unaccounted}"
    assert len(observed_tokens) > 0


def test_translation_mapping_decisions():
    """Verify specific mapping rows and normalization through canonical_terminal_status.

    E-01: Explicit decisions for driver tokens, consuming run_state constants.
    """
    # Recommended rows
    assert (
        runner_shared.map_driver_status_to_run_state("queued")
        == run_state.STATE_RUNNABLE
    )
    assert (
        runner_shared.map_driver_status_to_run_state("running")
        == run_state.STATE_RUNNING
    )
    assert (
        runner_shared.map_driver_status_to_run_state("executed")
        == run_state.STATE_COMPLETE
    )
    assert (
        runner_shared.map_driver_status_to_run_state("already-landed")
        == run_state.STATE_COMPLETE
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-verify")
        == run_state.STATE_CORRECTION_REQUIRED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-gate")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-begin")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-lane")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-merge")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("failed") == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("fail-depend")
        == run_state.STATE_BLOCKED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("interrupted")
        == run_state.STATE_BLOCKED
    )

    # Normalization through canonical_terminal_status
    assert (
        runner_shared.map_driver_status_to_run_state("partial")
        == run_state.STATE_CORRECTION_REQUIRED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("failed-safely")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("dependency-blocked")
        == run_state.STATE_BLOCKED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("substantially-complete")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("blocked")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("integration-blocked")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("merge-conflict")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("merge-needs-human")
        == run_state.STATE_FAILED
    )
    assert (
        runner_shared.map_driver_status_to_run_state("merge-refused")
        == run_state.STATE_FAILED
    )

    # Intentionally unmapped tokens return None
    for token in runner_shared.INTENTIONALLY_UNMAPPED_DRIVER_STATUSES:
        assert runner_shared.map_driver_status_to_run_state(token) is None

    # Nothing maps to cancelled
    for token in runner_shutdown.KNOWN_ITEM_STATUSES:
        assert (
            runner_shared.map_driver_status_to_run_state(token)
            != run_state.STATE_CANCELLED
        )

    # Non-strings and unknown return None
    assert runner_shared.map_driver_status_to_run_state(None) is None
    assert runner_shared.map_driver_status_to_run_state(123) is None
    assert runner_shared.map_driver_status_to_run_state("unknown-future-token") is None


def test_reachability_paths_and_unreachable_pairs():
    """Verify runtime-authorized reachability search over run_state.

    E-03 / E-04: Reachable paths found for coarse driver progressions;
    unreachable pairs return None and validate_transition identifies why.
    """
    # Direct and coarse reachable paths
    p_runnable_running = runner_shared.find_runtime_reachability_path(
        "runnable", "running"
    )
    assert p_runnable_running == ["runnable", "running"]

    p_running_complete = runner_shared.find_runtime_reachability_path(
        "running", "complete"
    )
    assert p_running_complete == [
        "running",
        "performed",
        "verifying",
        "verified",
        "complete",
    ]

    p_running_correction = runner_shared.find_runtime_reachability_path(
        "running", "correction_required"
    )
    assert p_running_correction == [
        "running",
        "performed",
        "verifying",
        "correction_required",
    ]

    p_correction_runnable = runner_shared.find_runtime_reachability_path(
        "correction_required", "runnable"
    )
    assert p_correction_runnable == ["correction_required", "runnable"]

    p_running_blocked = runner_shared.find_runtime_reachability_path(
        "running", "blocked"
    )
    assert p_running_blocked == ["running", "blocked"]

    p_runnable_blocked = runner_shared.find_runtime_reachability_path(
        "runnable", "blocked"
    )
    assert p_runnable_blocked == ["runnable", "running", "blocked"]

    # Same state returns [state]
    assert runner_shared.find_runtime_reachability_path("running", "running") == [
        "running"
    ]

    # Genuinely unreachable pairs under runtime actor
    assert runner_shared.find_runtime_reachability_path("complete", "runnable") is None
    res_complete = run_state.validate_transition("complete", "runnable", "runtime")
    assert not res_complete.ok
    assert res_complete.findings[0].code == "ST-TERMINAL-STATE"

    assert runner_shared.find_runtime_reachability_path("verified", "running") is None
    res_verified = run_state.validate_transition("verified", "running", "runtime")
    assert not res_verified.ok
    assert res_verified.findings[0].code == "ST-ILLEGAL-TRANSITION"

    assert runner_shared.find_runtime_reachability_path("running", "cancelled") is None
    res_cancelled = run_state.validate_transition("running", "cancelled", "runtime")
    assert not res_cancelled.ok
    assert res_cancelled.findings[0].code == "ST-UNAUTHORIZED-ACTOR"


def test_save_state_funnel_persistence_and_outcomes(tmp_path: Path):
    """Prove that save_state persists check records on items across reloads.

    E-03 / E-04:
      - Initial observation records initial outcome and persists position.
      - Next save reads prior position from persisted state.json, not memory.
      - Checked-legal records collapsed_path.
      - Skipped-unmapped records which side was unmapped.
      - Checked-illegal records violation and edge.
      - Unchanged re-save records nothing new.
      - Violation survives subsequent legal save.
    """
    dummy_called = []

    def dummy_report(path: Path, st: dict[str, Any]) -> None:
        dummy_called.append(path)

    run_dir = tmp_path / "run1"
    run_dir.mkdir()

    # Step 1: Initial observation
    state = {
        "run_id": "run-001",
        "queue": [_make_queue_item(status="queued")],
    }
    runner_shared.save_state(run_dir, state, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved1 = json.load(f)

    item1 = saved1["queue"][0]
    assert item1["run_state_position"] == "runnable"
    assert item1["run_state_check"]["outcome"] == "initial"
    assert item1["run_state_check"]["position"] == "runnable"
    assert len(item1["run_state_violations"]) == 0

    # Step 2: Reload state from disk (proving no in-memory cache dependence)
    loaded_state = runner_shared.load_state(run_dir)
    loaded_state["queue"][0]["status"] = "running"
    runner_shared.save_state(run_dir, loaded_state, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved2 = json.load(f)

    item2 = saved2["queue"][0]
    assert item2["run_state_position"] == "running"
    assert item2["run_state_check"]["outcome"] == "checked-legal"
    assert item2["run_state_check"]["source"] == "runnable"
    assert item2["run_state_check"]["target"] == "running"
    assert item2["run_state_check"]["path"] == ["runnable", "running"]
    assert item2["run_state_check"]["collapsed_path"] == []
    assert len(item2["run_state_violations"]) == 0

    # Step 3: Unchanged status re-save: records nothing new
    check_before = dict(item2["run_state_check"])
    runner_shared.save_state(run_dir, saved2, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved3 = json.load(f)
    assert saved3["queue"][0]["run_state_check"] == check_before

    # Step 4: Advance to executed (coarse transition running -> complete)
    saved3["queue"][0]["status"] = "executed"
    runner_shared.save_state(run_dir, saved3, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved4 = json.load(f)

    item4 = saved4["queue"][0]
    assert item4["run_state_position"] == "complete"
    assert item4["run_state_check"]["outcome"] == "checked-legal"
    assert item4["run_state_check"]["source"] == "running"
    assert item4["run_state_check"]["target"] == "complete"
    assert item4["run_state_check"]["collapsed_path"] == [
        "performed",
        "verifying",
        "verified",
    ]
    assert len(item4["run_state_violations"]) == 0

    # Step 5: Illegal transition from complete -> runnable (executed -> queued)
    saved4["queue"][0]["status"] = "queued"
    runner_shared.save_state(run_dir, saved4, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved5 = json.load(f)

    item5 = saved5["queue"][0]
    assert item5["run_state_check"]["outcome"] == "checked-illegal"
    assert item5["run_state_check"]["source"] == "complete"
    assert item5["run_state_check"]["target"] == "runnable"
    assert item5["run_state_check"]["edge"] == "complete->runnable"
    assert item5["run_state_check"]["code"] == "ST-TERMINAL-STATE"
    assert len(item5["run_state_violations"]) == 1
    assert item5["run_state_violations"][0]["edge"] == "complete->runnable"

    # Step 6: Subsequent legal save (queued -> running): violation survives!
    saved5["queue"][0]["status"] = "running"
    runner_shared.save_state(run_dir, saved5, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved6 = json.load(f)

    item6 = saved6["queue"][0]
    assert item6["run_state_check"]["outcome"] == "checked-legal"
    assert len(item6["run_state_violations"]) == 1
    assert item6["run_state_violations"][0]["edge"] == "complete->runnable"

    # Step 7: Transition to unmapped status records skipped-unmapped, NOT a violation
    saved6["queue"][0]["status"] = "retired"
    runner_shared.save_state(run_dir, saved6, write_report=dummy_report)

    with open(run_dir / "state.json") as f:
        saved7 = json.load(f)

    item7 = saved7["queue"][0]
    assert item7["run_state_check"]["outcome"] == "skipped-unmapped"
    assert item7["run_state_check"]["unmapped_side"] == "target"
    assert item7["run_state_position"] is None
    # Violations count does not increase!
    assert len(item7["run_state_violations"]) == 1


@pytest.mark.parametrize(
    "sequence",
    [
        # Coarse success sequence
        ["queued", "running", "executed"],
        # Retry sequence after verifier rejection
        ["queued", "running", "fail-verify", "queued"],
        # Interrupted resume sequence
        ["queued", "running", "interrupted", "queued"],
        # Dependency block at dispatch
        ["queued", "fail-depend"],
        # Repeated saves with unchanged status
        ["queued", "queued", "running", "running", "executed", "executed"],
        # Normal gate failure
        ["queued", "running", "fail-gate"],
        # Normal lane failure
        ["queued", "running", "fail-lane"],
    ],
)
def test_real_driver_sequences_inertness(sequence: list[str], tmp_path: Path):
    """Assert all real driver sequences record ZERO violations.

    E-04: The inertness invariant requires that normal driver behavior
    never triggers illegal transition violations.
    """
    run_dir = tmp_path / "test_run"
    run_dir.mkdir(exist_ok=True)

    state = {
        "run_id": "seq-run",
        "queue": [_make_queue_item(status=sequence[0])],
    }

    for status in sequence:
        state["queue"][0]["status"] = status
        runner_shared.save_state(run_dir, state, write_report=lambda p, s: None)

    with open(run_dir / "state.json") as f:
        persisted = json.load(f)

    item = persisted["queue"][0]
    assert (
        len(item["run_state_violations"]) == 0
    ), f"Sequence {sequence} unexpectedly recorded violations: {item['run_state_violations']}"


def test_save_state_exception_safety(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Assert any exception during transition check is recorded and save_state never raises.

    E-03 / E-04: Report-only code must never wedge a run.
    """

    def broken_map(status: Any) -> str | None:
        raise RuntimeError("simulated mapping fault")

    monkeypatch.setattr(runner_shared, "map_driver_status_to_run_state", broken_map)

    run_dir = tmp_path / "fault_run"
    run_dir.mkdir()

    state = {
        "run_id": "fault-run-001",
        "queue": [_make_queue_item(status="queued")],
    }

    # Must NOT raise
    runner_shared.save_state(run_dir, state, write_report=lambda p, s: None)

    # state.json must still be written
    assert (run_dir / "state.json").exists()
    with open(run_dir / "state.json") as f:
        persisted = json.load(f)

    item = persisted["queue"][0]
    assert "simulated mapping fault" in item.get("run_state_check_error", "")
    assert item.get("run_state_check", {}).get("outcome") == "error"


def test_both_hosts_save_state_and_mutation_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Behaviorally prove that both hosts route through runner_shared and carry no private copy.

    E-05:
      1. Drive oc_runipd.save_state and agy_runipd.save_state with the same sequence.
         Assert both persist identical check records in state.json.
      2. Mutation-check by monkeypatching the shared translation in runner_shared
         and showing BOTH hosts' recorded outcomes change accordingly.
    """
    sequence = ["queued", "running", "executed"]

    dir_oc = tmp_path / "oc_run"
    dir_agy = tmp_path / "agy_run"
    dir_oc.mkdir()
    dir_agy.mkdir()

    state_oc = {
        "run_id": "oc-001",
        "queue": [_make_queue_item(status=sequence[0])],
    }
    state_agy = {
        "run_id": "agy-001",
        "queue": [_make_queue_item(status=sequence[0])],
    }

    for status in sequence:
        state_oc["queue"][0]["status"] = status
        state_agy["queue"][0]["status"] = status
        oc_runipd.save_state(dir_oc, state_oc)
        agy_runipd.save_state(dir_agy, state_agy)

    with open(dir_oc / "state.json") as f:
        res_oc = json.load(f)["queue"][0]
    with open(dir_agy / "state.json") as f:
        res_agy = json.load(f)["queue"][0]

    # Verify both hosts produced identical check outcomes
    assert res_oc["run_state_check"] == res_agy["run_state_check"]
    assert res_oc["run_state_position"] == res_agy["run_state_position"] == "complete"
    assert res_oc["run_state_violations"] == res_agy["run_state_violations"] == []

    # MUTATION CHECK: monkeypatch shared translation in runner_shared
    original_map = runner_shared.map_driver_status_to_run_state

    def mutated_map(status: Any) -> str | None:
        if status == "executed":
            return None
        return original_map(status)

    monkeypatch.setattr(runner_shared, "map_driver_status_to_run_state", mutated_map)

    dir_oc_mut = tmp_path / "oc_mut"
    dir_agy_mut = tmp_path / "agy_mut"
    dir_oc_mut.mkdir()
    dir_agy_mut.mkdir()

    state_oc_mut = {
        "run_id": "oc-mut",
        "queue": [_make_queue_item(status="running")],
    }
    state_agy_mut = {
        "run_id": "agy-mut",
        "queue": [_make_queue_item(status="running")],
    }

    oc_runipd.save_state(dir_oc_mut, state_oc_mut)
    agy_runipd.save_state(dir_agy_mut, state_agy_mut)

    # Now step to 'executed' under mutation
    state_oc_mut["queue"][0]["status"] = "executed"
    state_agy_mut["queue"][0]["status"] = "executed"
    oc_runipd.save_state(dir_oc_mut, state_oc_mut)
    agy_runipd.save_state(dir_agy_mut, state_agy_mut)

    with open(dir_oc_mut / "state.json") as f:
        mut_oc = json.load(f)["queue"][0]
    with open(dir_agy_mut / "state.json") as f:
        mut_agy = json.load(f)["queue"][0]

    # Under mutation, both hosts now record skipped-unmapped because 'executed' mapped to None
    assert mut_oc["run_state_check"]["outcome"] == "skipped-unmapped"
    assert mut_agy["run_state_check"]["outcome"] == "skipped-unmapped"
    assert mut_oc["run_state_check"] == mut_agy["run_state_check"]
