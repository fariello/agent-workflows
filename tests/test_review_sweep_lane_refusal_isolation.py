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
import types
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


@pytest.mark.parametrize("runner_name", ["oc", "agy"])
def test_deferred_review_is_parked_next_review_lands_and_retry_integrates(
    tmp_path: Path, runner_name: str
) -> None:
    """Transient merge-retry review deferral parks off the sweep lane so Review 2 lands cleanly,
    and retrying Review 1 integrates from the parked branch once main's overlapping dirt clears."""
    repo = _create_test_repo(tmp_path)
    fake_bin = _make_fake_agent_script(tmp_path)
    run_id = f"run-rev-defer-{runner_name}"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)

    plans = [
        _create_plan_file(
            repo,
            id6,
            setid="revq",
            order=n,
            status="to-review",
            action="review",
            commit=False,
        )
        for n, id6 in ((1, "rd0001"), (2, "rd0002"))
    ]
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "add review plans"], cwd=repo, check=True)

    items: list[dict[str, Any]] = [
        {
            "id6": id6,
            "setid": "revq",
            "position": n,
            "action": "review",
            "review_handler": "plan-review",
            "status": "queued",
            "configured_file": str(p),
            "attempts": [],
        }
        for n, (id6, p) in enumerate(zip(("rd0001", "rd0002"), plans), start=1)
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
        "rd0001": {
            "commit": "review 1 deferred",
            "commit_plan_edit": True,
            "outcome": outcome,
        },
        "rd0002": {
            "commit": "review 2 clean",
            "commit_plan_edit": True,
            "outcome": outcome,
        },
    }

    # Dirty plan 1 in main so Review 1 hits dirty_tree_overlap -> merge-retry.
    original_plan1 = plans[0].read_text(encoding="utf-8")
    plans[0].write_text(
        original_plan1 + "\n<!-- dirty local edit -->\n", encoding="utf-8"
    )

    def run(item: dict[str, Any]) -> None:
        with (
            mock.patch.dict(
                os.environ, {"FAKE_PAYLOAD_MAP_JSON": json.dumps(payload_map)}
            ),
            coordinator_role(),
        ):
            driver.execute_item(run_dir, state, item, recovery=False)

    # 1. Review 1 is transiently deferred (merge-retry), parked off sweep lane, sweep lane reset.
    run(items[0])
    first = items[0]
    assert first["status"] == runner_shared.INTEGRATION_DEFERRED_STATUS
    parked = f"aw/parked/{run_id}/rd0001"
    assert first.get("preserved_branch") == parked
    assert first.get("review_parked_off_sweep_lane") == parked
    sweep = runner_shared.review_sweep_lane_handle(state)
    assert sweep is not None
    tip_before = first["attempts"][-1]["review_lane_tip_before"]
    assert _git(Path(sweep.path), "rev-parse", "HEAD") == tip_before
    assert "review 1 deferred" in _git(repo, "log", "--oneline", parked)

    # 2. Review 2 runs on the reset sweep lane and lands on main even while plan 1 is still dirty.
    run(items[1])
    assert items[1]["status"] == "reviewed", items[1].get("review_integration_refusal")
    log_main = _git(repo, "log", "--oneline", "main")
    assert "review 2 clean" in log_main
    assert "review 1 deferred" not in log_main

    # 3. Once main's dirty edit on plan 1 is cleared, retry integrates Review 1 from parked branch
    #    and deletes the temporary parked branch.
    plans[0].write_text(original_plan1, encoding="utf-8")
    with coordinator_role():
        results = driver.retry_deferred_integrations(run_dir, state)
    assert any(
        r.get("id6") == "rd0001" and r.get("outcome") == "integrated" for r in results
    )
    assert first["status"] == "reviewed"
    assert "review 1 deferred" in _git(repo, "log", "--oneline", "main")
    assert first.get("preserved_branch") is None
    assert first.get("review_parked_off_sweep_lane") is None
    assert _git(repo, "branch", "--list", parked) == ""


def test_refresh_sweep_lane_reports_false_when_lane_is_ahead_of_main(
    tmp_path: Path,
) -> None:
    """An unmerged commit sitting ahead of main on the sweep lane must NOT report refreshed=True."""
    repo = _create_test_repo(tmp_path)
    lane_path = tmp_path / "sweep-wt"
    base = _git(repo, "rev-parse", "HEAD")
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            "aw/lane/review-sweep-test",
            str(lane_path),
            base,
        ],
        cwd=repo,
        check=True,
    )
    handle = types.SimpleNamespace(path=lane_path, branch="aw/lane/review-sweep-test")

    # Equal to main -> already_current=True, refreshed=False.
    same = runner_shared.refresh_sweep_lane(repo, handle)
    assert same.refreshed is False
    assert same.already_current is True

    # Commit on sweep lane while main has not moved (lane is strictly ahead of main).
    (lane_path / "lane-only.txt").write_text("ahead\n", encoding="utf-8")
    subprocess.run(["git", "add", "lane-only.txt"], cwd=lane_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "lane ahead commit"], cwd=lane_path, check=True
    )
    ahead_head = _git(lane_path, "rev-parse", "HEAD")

    ahead = runner_shared.refresh_sweep_lane(repo, handle)
    assert ahead.refreshed is False
    assert ahead.already_current is False
    assert ahead.head == ahead_head
    assert _git(lane_path, "rev-parse", "HEAD") == ahead_head

    # Reset lane back to base, advance main -> now lane IS strictly behind main and fast-forwards.
    subprocess.run(["git", "reset", "--hard", base], cwd=lane_path, check=True)
    (repo / "main-advance.txt").write_text("main\n", encoding="utf-8")
    subprocess.run(["git", "add", "main-advance.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "main advance"], cwd=repo, check=True)
    new_main = _git(repo, "rev-parse", "HEAD")

    advanced = runner_shared.refresh_sweep_lane(repo, handle)
    assert advanced.refreshed is True
    assert advanced.head == new_main
    assert _git(lane_path, "rev-parse", "HEAD") == new_main


def test_resolve_exhausted_deferrals_parks_unparked_deferred_review(
    tmp_path: Path,
) -> None:
    """Even a legacy unparked deferred review gets parked off the sweep lane when exhausted."""
    repo = _create_test_repo(tmp_path)
    run_id = "run-exhaust-park"
    run_dir = repo / ".aw" / "records" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    lane_path = tmp_path / "sweep-exhaust"
    base = _git(repo, "rev-parse", "HEAD")
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "-b",
            f"aw/lane/review-sweep-{run_id}",
            str(lane_path),
            base,
        ],
        cwd=repo,
        check=True,
    )
    (lane_path / "rev-edit.txt").write_text("reviewed\n", encoding="utf-8")
    subprocess.run(["git", "add", "rev-edit.txt"], cwd=lane_path, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "unparked deferred review"], cwd=lane_path, check=True
    )

    state: dict[str, Any] = {
        "repo": str(repo),
        "run_id": run_id,
        runner_shared.REVIEW_SWEEP_LANE_KEY: {
            "lane_id": f"review-sweep-{run_id}",
            "worktree": str(lane_path),
            "branch": f"aw/lane/review-sweep-{run_id}",
            "base_commit": base,
            "retired": False,
        },
        "queue": [
            {
                "id6": "ex0001",
                "setid": "revx",
                "action": "review",
                "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                "integration_deferral": "dirty overlap",
                "integration_ladder": {
                    "deferred": True,
                    "status": runner_shared.INTEGRATION_DEFERRED_STATUS,
                },
                "attempts": [
                    {
                        "action": "review",
                        "review_lane_tip_before": base,
                        "disposition": runner_shared.INTEGRATION_DEFERRED_STATUS,
                    }
                ],
            }
        ],
    }

    resolved = runner_shared.resolve_exhausted_deferrals(
        run_dir,
        state,
        save_state=runner_shared.save_state,
        append_jsonl=runner_shared.append_jsonl,
    )
    assert resolved == ["ex0001"]
    item = state["queue"][0]
    parked = f"aw/parked/{run_id}/ex0001"
    assert item["status"] == runner_shared.INTEGRATION_BLOCKED_STATUS
    assert item.get("preserved_branch") == parked
    assert item.get("review_parked_off_sweep_lane") == parked
    assert _git(lane_path, "rev-parse", "HEAD") == base
    assert "unparked deferred review" in _git(repo, "log", "--oneline", parked)
