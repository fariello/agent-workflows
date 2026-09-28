"""Tests for host capability preflight wiring into shared dispatch (IPD iot7hc)."""

from __future__ import annotations

import ast
from contextlib import contextmanager
import json
from pathlib import Path
from typing import Any
import pytest

from agent_workflows import host_sandbox_profile as hsp
from agent_workflows import render_stream
from agent_workflows import run_selection_policy as rsp
from agent_workflows import runner_shared
from tests.test_host_capability_extension import synthetic_gated_action


@contextmanager
def bound_contract_action(
    runner_action: str = "execute", contract_action: str = "_gated_for_test"
):
    """Temporarily map a runner action to a contract action in runner_shared."""
    table = getattr(runner_shared, "RUNNER_ACTION_TO_CONTRACT_ACTION", None)
    if table is None:
        yield
        return
    saved = dict(table)
    table[runner_action] = contract_action
    try:
        yield
    finally:
        table.clear()
        table.update(saved)


def test_runner_shared_references_preflight_host_capabilities() -> None:
    """Case 1 (E-02): runner_shared must reference preflight_host_capabilities.

    Inverse of E-01 baseline (where rg -c exits 1 with zero call sites).
    AST inspection proves the dispatch point directly references the preflight.
    """
    rs_path = Path(runner_shared.__file__)
    tree = ast.parse(rs_path.read_text(encoding="utf-8"))
    referenced_names = (
        {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        | {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.alias))
        }
        | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    )
    assert (
        "preflight_host_capabilities" in referenced_names
    ), "runner_shared does not reference preflight_host_capabilities; gate is unreachable"


def test_execute_item_core_refuses_when_host_capability_unavailable_and_starts_no_session(
    tmp_path: Path,
) -> None:
    """Case 2 (E-02): execute_item_core drives preflight refusal when capability is missing.

    Asserts:
    - item status ends fail-gate
    - attempts entry has disposition fail-gate and preflight message
    - refusal recorded via render_stream.record_refusal with verbatim message
    - recovery command carries real CLI host noun (opencode, not oc_runipd)
    - events.jsonl records host-capability-unavailable event
    - no session is launched (spawn_executor/spawn_verifier not called)
    - no prompt file is written
    """
    if not hasattr(runner_shared, "RUNNER_ACTION_TO_CONTRACT_ACTION"):
        pytest.skip("pending runner_shared wiring (E-03/E-04)")

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    plan_dir = repo_dir / ".aw/records/plans/pending"
    plan_dir.mkdir(parents=True)
    plan_file = plan_dir / "20260928-test01-01-tst001-test-item.ipd.md"
    plan_file.write_text(
        "# IPD: Test item\n\n- Scope-Paths: agent_workflows/runner_shared.py\n",
        encoding="utf-8",
    )

    run_dir = tmp_path / "run"
    run_dir.mkdir()

    item: dict[str, Any] = {
        "position": 1,
        "id6": "tst001",
        "setid": "test01",
        "action": "execute",
        "status": "queued",
        "configured_file": str(plan_file),
        "path": str(plan_file),
    }
    state: dict[str, Any] = {
        "repo": str(repo_dir),
        "queue": [item],
        "run_id": "run-test-wiring",
    }

    def fail_spawn(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Session must not be started for a capability-refused item")

    # Use forced_runner_safety_verdicts and synthetic_gated_action (shipped test seams)
    with (
        hsp.forced_runner_safety_verdicts(
            {hsp.CAP_COMMIT_GATEWAY: (False, "forced unavailable for test")}
        ),
        synthetic_gated_action(),
        bound_contract_action("execute", "_gated_for_test"),
    ):
        runner_shared.execute_item_core(
            run_dir,
            state,
            item,
            recovery=False,
            host_labels=runner_shared.OC_HOST_LABELS,
            spawn_executor=fail_spawn,
            spawn_verifier=fail_spawn,
            raw_launcher=fail_spawn,
            run_suite_check=lambda p, s: None,
            process_backlog_close=lambda *a, **k: None,
        )

    # 1. Terminal status must be fail-gate
    assert item["status"] == "fail-gate"

    # 2. Attempt entry recorded with disposition fail-gate
    attempts = item.get("attempts", [])
    assert len(attempts) == 1
    assert attempts[0]["disposition"] == "fail-gate"
    assert "host_capability_unavailable" in attempts[0]

    # 3. Refusal recorded through render_stream
    refusal = render_stream.refusal_of_item(item)
    assert refusal is not None
    assert refusal.code == rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE
    assert "commit_gateway" in refusal.reason
    assert "[RUN-HOST-CAPABILITY]" in refusal.reason
    # Recovery command uses CLI noun 'opencode', not internal 'oc_runipd' (F-12)
    assert "aw opencode run tst001" in refusal.reason
    assert "oc_runipd" not in refusal.reason
    assert (
        refusal.remedy == rsp.DISPOSITION_REMEDIES[rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE]
    )

    # 4. events.jsonl has host-capability-unavailable event
    events_file = run_dir / "events.jsonl"
    assert events_file.exists()
    events = [
        json.loads(line)
        for line in events_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    refusal_events = [
        e for e in events if e.get("event") == "host-capability-unavailable"
    ]
    assert len(refusal_events) == 1
    assert refusal_events[0]["id6"] == "tst001"
    assert hsp.CAP_COMMIT_GATEWAY in refusal_events[0]["missing"]

    # 5. No prompt file written
    prompt_dir = run_dir / "prompts"
    if prompt_dir.exists():
        assert list(prompt_dir.glob("*")) == []


def test_refused_item_derived_disposition_is_host_capability_unavailable() -> None:
    """Case 3 (E-02, PR-101): derive_item_disposition returns SKIP_HOST_CAPABILITY_UNAVAILABLE.

    This is the rendering case: proves that record_refusal allows derive_item_disposition
    to derive the spec's code rather than falling back to 'acted_on' (F-10).
    """
    item: dict[str, Any] = {
        "position": 1,
        "id6": "tst001",
        "setid": "test01",
        "action": "execute",
        "status": "fail-gate",
    }
    render_stream.record_refusal(
        item,
        code=rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE,
        reason="[RUN-HOST-CAPABILITY] Host opencode cannot enforce commit_gateway",
        remedy=rsp.DISPOSITION_REMEDIES[rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE],
    )
    disp = rsp.derive_item_disposition(item, render_stream.refusal_of_item)
    assert disp.code == rsp.SKIP_HOST_CAPABILITY_UNAVAILABLE
    assert (
        disp.reason
        == "[RUN-HOST-CAPABILITY] Host opencode cannot enforce commit_gateway"
    )


def test_dependent_of_capability_refused_item_cascades_to_fail_depend(
    tmp_path: Path,
) -> None:
    """Case 4 (E-05): cascade_dependency_blocked cascades fail-gate to fail-depend."""
    prereq = {
        "position": 1,
        "id6": "cap001",
        "setid": "test",
        "action": "execute",
        "status": "fail-gate",
    }
    dependent = {
        "position": 2,
        "id6": "dep001",
        "setid": "test",
        "action": "execute",
        "status": "queued",
        "dependencies": ["executed:cap001"],
    }
    state: dict[str, Any] = {"queue": [prereq, dependent], "run_id": "run-cascade"}
    blocked = runner_shared.cascade_dependency_blocked(state, run_dir=tmp_path)

    assert [b["id6"] for b in blocked] == ["dep001"]
    assert dependent["status"] == "fail-depend"
    assert dependent["unsatisfied_dependencies"] == ["executed:cap001"]
