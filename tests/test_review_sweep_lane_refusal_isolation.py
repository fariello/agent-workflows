"""One terminally refused review must not block the later reviews of the same run (backlog cm36w7).

Assures, on both hosts, with a real git repo and the real review path:
- a review whose integration is refused terminally ends with a terminal status, its commit is moved
  to aw/parked/<run_id>/<id6>, and the shared sweep lane is reset to the tip it had before that review;
- the NEXT review in the same run integrates to main, and main contains its commit but not the refused
  review's commit.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from tests.support import coordinator_role
from tests.test_question_parking import (
    _create_plan_file,
    _create_test_repo,
    _make_fake_agent_script,
)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_refused_review_is_parked_and_next_review_integrates(
    tmp_path: Path, runner_name: str
) -> None:
    repo = _create_test_repo(tmp_path)
    fake_bin = _make_fake_agent_script(tmp_path)
    run_id = f"run-rev-isolate-{runner_name}"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    plans = [
        _create_plan_file(
            repo,
            id6,
            setid="revi",
            order=n,
            status="to-review",
            action="review",
            commit=False,
        )
        for n, id6 in ((1, "ri0001"), (2, "ri0002"))
    ]
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add review plans"], cwd=repo, check=True)

    items: list[dict[str, Any]] = [
        {
            "id6": id6,
            "setid": "revi",
            "position": n,
            "action": "review",
            "review_handler": "plan-review",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        for n, (id6, p) in enumerate(zip(("ri0001", "ri0002"), plans), start=1)
    ]
    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": run_id,
        "queue": items,
        "options": {
            "no_verify": True,
            "validate": False,
            "self_finalize": False,
            "isolate_review": True,
            "output_mode": "quiet",
        },
    }
    driver = oc_runipd if runner_name == "oc" else agy_runipd
    state["options"]["opencode" if runner_name == "oc" else "agy"] = str(fake_bin)
    runner_shared.save_state(run_dir, state)

    outcome = {
        "disposition": "reviewed",
        "verdict": "APPROVE WITH REVISIONS APPLIED",
        "defect_report": {"state": "none-found", "findings": []},
        "pushed": False,
    }
    payload_map = {
        "ri0001": {
            "commit": "review 1 refused",
            "commit_plan_edit": True,
            "outcome": outcome,
        },
        "ri0002": {
            "commit": "review 2 pass",
            "commit_plan_edit": True,
            "outcome": outcome,
        },
    }

    real_integrate = driver.integrate_review_lane_branch

    def integrate(
        r: Path, h: Any, id6: str, *a: Any, **k: Any
    ) -> tuple[bool, str, str]:
        if id6 == "ri0001":
            return (
                False,
                "integration refused: check.ipd-uncarried-obligation",
                runner_shared.INTEGRATION_REFUSAL_CONFLICT,
            )
        return real_integrate(r, h, id6, *a, **k)

    def run(item: dict[str, Any]) -> None:
        with (
            mock.patch.object(
                driver, "integrate_review_lane_branch", side_effect=integrate
            ),
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}
            ),
            coordinator_role(),
        ):
            driver.execute_item(run_dir, state, item, recovery=False)

    run(items[0])
    first = items[0]
    assert first["status"] == runner_shared.INTEGRATION_REFUSAL_CONFLICT
    parked = f"aw/parked/{run_id}/ri0001"
    assert first.get("preserved_branch") == parked
    sweep = runner_shared.review_sweep_lane_handle(state)
    assert sweep is not None
    tip_before = first["attempts"][-1]["review_lane_tip_before"]
    assert _git(Path(sweep.path), "rev-parse", "HEAD") == tip_before
    assert _git(Path(sweep.path), "status", "--porcelain") == ""
    assert "review 1 refused" in _git(repo, "log", "--oneline", parked)

    run(items[1])
    assert items[1]["status"] == "reviewed", items[1].get("review_integration_refusal")
    log_main = _git(repo, "log", "--oneline", "main")
    assert "review 2 pass" in log_main
    assert "review 1 refused" not in log_main
