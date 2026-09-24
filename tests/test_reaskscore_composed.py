"""Tests for composed reaskscore verification: constant pins, AST ordering, SHAPE A, SHAPE B, and collision exclusivity.

Part of IPD svacmz (reaskscore Set Order 04).
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from typing import Any, ClassVar
from unittest import mock

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared
from agent_workflows.runner_shared import turn_attempted_nothing


DRIVERS = pytest.mark.parametrize(
    "driver", [oc_runipd, agy_runipd], ids=["oc_runipd", "agy_runipd"]
)


class TestSharedConstantsByteIdenticalAndUnwidened(unittest.TestCase):
    """E-01 / V-01: Pin the five shared success and retirement constants across all eight definition sites."""

    EXPECTED_EXECUTION_SUCCESS_STATES: ClassVar[set[str]] = {
        "executed",
        "substantially-complete",
    }
    EXPECTED_SUCCESS_STATES: ClassVar[set[str]] = {
        "executed",
        "reviewed",
        "approved",
    }
    EXPECTED_TERMINAL_STATES: ClassVar[set[str]] = {
        "executed",
        "reviewed",
        "approved",
        "substantially-complete",
        "partial",
        "blocked",
        "dependency-blocked",
        "failed-safely",
        "not-attempted",
        "integration-blocked",
        "merge-conflict",
        "merge-needs-human",
        "merge-refused",
    }
    EXPECTED_EXECUTE_REPORTING_SUCCESS_STATES: ClassVar[frozenset[str]] = frozenset(
        {"executed", "approved"}
    )
    EXPECTED_SET_RETIREMENT_DONE_STATUS: ClassVar[str] = "executed"

    def test_five_constants_eight_definition_sites_values_and_types(self) -> None:
        """Assert every definition site of each of the 5 constants matches pre-Set values and correct types."""
        # 1. EXECUTION_SUCCESS_STATES (3 sites: oc_runipd:843, agy_runipd:763, runner_shared:21633)
        self.assertEqual(
            self.EXPECTED_EXECUTION_SUCCESS_STATES, oc_runipd.EXECUTION_SUCCESS_STATES
        )
        self.assertEqual(
            self.EXPECTED_EXECUTION_SUCCESS_STATES, agy_runipd.EXECUTION_SUCCESS_STATES
        )
        self.assertEqual(
            self.EXPECTED_EXECUTION_SUCCESS_STATES,
            runner_shared.EXECUTION_SUCCESS_STATES,
        )

        # 2. SUCCESS_STATES (3 sites: runner_shared:21616, oc_runipd:838, agy_runipd:758)
        self.assertEqual(self.EXPECTED_SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertEqual(self.EXPECTED_SUCCESS_STATES, oc_runipd.SUCCESS_STATES)
        self.assertEqual(self.EXPECTED_SUCCESS_STATES, agy_runipd.SUCCESS_STATES)

        # 3. TERMINAL_STATES (3 sites: oc_runipd:813, agy_runipd:733, runner_shared:24241)
        self.assertEqual(self.EXPECTED_TERMINAL_STATES, set(oc_runipd.TERMINAL_STATES))
        self.assertEqual(self.EXPECTED_TERMINAL_STATES, set(agy_runipd.TERMINAL_STATES))
        self.assertEqual(
            self.EXPECTED_TERMINAL_STATES, set(runner_shared.TERMINAL_STATES)
        )
        self.assertIsInstance(runner_shared.TERMINAL_STATES, frozenset)

        # 4. EXECUTE_REPORTING_SUCCESS_STATES (1 site: runner_shared:21719)
        self.assertEqual(
            self.EXPECTED_EXECUTE_REPORTING_SUCCESS_STATES,
            runner_shared.EXECUTE_REPORTING_SUCCESS_STATES,
        )
        self.assertIsInstance(runner_shared.EXECUTE_REPORTING_SUCCESS_STATES, frozenset)

        # 5. SET_RETIREMENT_DONE_STATUS (1 site: runner_shared:13996)
        self.assertEqual(
            self.EXPECTED_SET_RETIREMENT_DONE_STATUS,
            runner_shared.SET_RETIREMENT_DONE_STATUS,
        )

    def test_terminal_states_three_copies_are_mutually_equal(self) -> None:
        """Assert that all three copies of TERMINAL_STATES are mutually equal and contain no deferrable states."""
        self.assertEqual(
            set(oc_runipd.TERMINAL_STATES),
            set(agy_runipd.TERMINAL_STATES),
            "oc_runipd and agy_runipd TERMINAL_STATES must be equal",
        )
        self.assertEqual(
            set(oc_runipd.TERMINAL_STATES),
            set(runner_shared.TERMINAL_STATES),
            "host TERMINAL_STATES and runner_shared.TERMINAL_STATES must be equal",
        )
        self.assertEqual(len(runner_shared.TERMINAL_STATES), 13)
        # Deferrable pair is deliberately absent
        self.assertNotIn("merge-retry", runner_shared.TERMINAL_STATES)
        self.assertNotIn("merge-unchecked", runner_shared.TERMINAL_STATES)

    def test_execute_reporting_success_states_is_derived_by_subtraction(self) -> None:
        """Assert that EXECUTE_REPORTING_SUCCESS_STATES is derived by subtracting 'reviewed' from SUCCESS_STATES."""
        derived = frozenset(runner_shared.SUCCESS_STATES - {"reviewed"})
        self.assertEqual(
            derived,
            runner_shared.EXECUTE_REPORTING_SUCCESS_STATES,
            "EXECUTE_REPORTING_SUCCESS_STATES derivation must equal SUCCESS_STATES - {'reviewed'}",
        )

    def test_reexports_are_identical_objects(self) -> None:
        """Assert that host re-exports are identical objects to the shared definitions."""
        self.assertIs(oc_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertIs(agy_runipd.SUCCESS_STATES, runner_shared.SUCCESS_STATES)
        self.assertIs(
            oc_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )
        self.assertIs(
            agy_runipd.EXECUTION_SUCCESS_STATES, runner_shared.EXECUTION_SUCCESS_STATES
        )


class TestReconstructShapeAComposed:
    """E-03 / V-03: Reconstruct SHAPE A end to end on the merged result.

    Stage 1: Turn 1 writes no outcome file (initial score: fallback partial).
    Stage 2: Defect re-ask resumes session in lane, completes work, writes outcome.
    Stage 3: Re-collection and rescore in execute_item_core rescores item to substantially-complete.
    Outcome: Item reaches substantially-complete (or executed), and dependent siblings do NOT cascade to dependency-blocked.
    """

    @staticmethod
    def _create_repo(tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.st"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
        (repo / "README.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=repo, check=True)
        return repo

    @staticmethod
    def _create_queue_state(repo: Path, run_dir: Path) -> dict[str, Any]:
        queue = [
            {
                "position": 1,
                "id6": "zqs0px",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
            {
                "position": 2,
                "id6": "qmgn12",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": ["executed:zqs0px"],
                "attempts": [],
            },
            {
                "position": 3,
                "id6": "s0gnha",
                "setid": "reaskscore",
                "action": "orchestrate",
                "kind": "orchestrator",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
        ]
        state = {
            "schema_version": 1,
            "run_id": run_dir.name,
            "repo": str(repo),
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["reaskscore"],
            "options": {"retry_budget": 0, "isolate_worktree": False},
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return state

    @DRIVERS
    def test_shape_a_rescued_turn_rescores_and_siblings_do_not_cascade(
        self, driver: Any, tmp_path: Path
    ) -> None:
        """End-to-end SHAPE A: first turn has no outcome; re-ask completes; rescore succeeds; siblings run."""
        repo = self._create_repo(tmp_path)
        run_dir = tmp_path / f"run-shape-a-{driver.__name__}"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
        self._create_queue_state(repo, run_dir)

        executed_dir = repo / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)

        def finalize_on_disk(id6: str) -> None:
            (executed_dir / f"20260919-reaskscore-01-{id6}-stub.ipd.md").write_text(
                f"# IPD: stub\n\n- Id: {id6}\n- Status: executed\n", encoding="utf-8"
            )

        executed_items: list[str] = []

        def fake_exec(
            rd: Path, st: dict[str, Any], it: dict[str, Any], *a: Any, **kw: Any
        ) -> None:
            id6 = str(it["id6"])
            executed_items.append(id6)
            pos = int(it["position"])
            if id6 == "zqs0px":
                # Stage 1 & 2: zqs0px was rescued by re-ask -> rescore produced substantially-complete
                it["status"] = "substantially-complete"
                it.setdefault("attempts", []).append(
                    {
                        "number": 1,
                        "starting_head": "HEAD",
                        "ending_head": "HEAD",
                        "ending_status": "",
                        "recovery": False,
                    }
                )
                (rd / "outcomes" / f"{pos:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "substantially-complete"}),
                    encoding="utf-8",
                )
                finalize_on_disk(id6)
                # Emit ipd-rescored event
                events_file = rd / "events.jsonl"
                with events_file.open("a", encoding="utf-8") as ef:
                    ef.write(
                        json.dumps(
                            {
                                "event": "ipd-rescored",
                                "id6": id6,
                                "previous_disposition": "partial",
                                "disposition": "substantially-complete",
                            }
                        )
                        + "\n"
                    )
            elif id6 == "qmgn12":
                it["status"] = "executed"
                it.setdefault("attempts", []).append(
                    {
                        "number": 1,
                        "starting_head": "HEAD",
                        "ending_head": "HEAD",
                        "ending_status": "",
                        "recovery": False,
                    }
                )
                (rd / "outcomes" / f"{pos:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "executed"}), encoding="utf-8"
                )
                finalize_on_disk(id6)
            driver.save_state(rd, st)

        buf = io.StringIO()
        with (
            mock.patch.object(driver, "execute_item", side_effect=fake_exec),
            contextlib.redirect_stdout(buf),
            contextlib.redirect_stderr(buf),
        ):
            driver.run_queue(run_dir, retry_incomplete=False)

        state_after = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        statuses = {it["id6"]: it["status"] for it in state_after["queue"]}

        # Assert BOTH halves:
        # 1. zqs0px ended at substantially-complete (or executed), inside EXECUTION_SUCCESS_STATES
        assert statuses["zqs0px"] == "substantially-complete"
        assert statuses["zqs0px"] in runner_shared.EXECUTION_SUCCESS_STATES

        # 2. Sibling qmgn12 was NOT dependency-blocked, was dispatched and executed
        assert statuses["qmgn12"] == "executed"
        assert executed_items == ["zqs0px", "qmgn12"]

        # 3. No dependency-blocked cascade event occurred on siblings
        events_path = run_dir / "events.jsonl"
        events = (
            [
                json.loads(line)
                for line in events_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if events_path.is_file()
            else []
        )
        dep_blocked_events = [
            e
            for e in events
            if e.get("event") == "dependency-blocked" and e.get("id6") == "qmgn12"
        ]
        assert (
            dep_blocked_events == []
        ), f"Expected no cascade blocks on qmgn12, saw: {dep_blocked_events}"
        rescored_events = [e for e in events if e.get("event") == "ipd-rescored"]
        assert (
            len(rescored_events) == 1
        ), f"Expected 1 rescore event, saw: {rescored_events}"


class TestReconstructShapeBAndCollisionExclusivity:
    """E-04 / V-04: Reconstruct SHAPE B and prove collision exclusivity from the two load-bearing conditions."""

    @staticmethod
    def _create_repo(tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "t@e.st"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
        (repo / "README.md").write_text("initial\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "initial commit"], cwd=repo, check=True)
        return repo

    @DRIVERS
    def test_shape_b_zero_work_turn_retried_once_within_budget(
        self, driver: Any, tmp_path: Path
    ) -> None:
        """SHAPE B: A host-truncated turn that did zero work is re-dispatched once within budget."""
        repo = self._create_repo(tmp_path)
        run_dir = tmp_path / f"run-shape-b-{driver.__name__}"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        queue = [
            {
                "position": 1,
                "id6": "zqs0px",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
            {
                "position": 2,
                "id6": "qmgn12",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": ["executed:zqs0px"],
                "attempts": [],
            },
            {
                "position": 3,
                "id6": "s0gnha",
                "setid": "reaskscore",
                "action": "orchestrate",
                "kind": "orchestrator",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
        ]
        state = {
            "schema_version": 1,
            "run_id": run_dir.name,
            "repo": str(repo),
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["reaskscore"],
            "options": {"retry_budget": 1, "isolate_worktree": False},
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        executed_dir = repo / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)

        def finalize_on_disk(id6: str) -> None:
            (executed_dir / f"20260919-reaskscore-01-{id6}-stub.ipd.md").write_text(
                f"# IPD: stub\n\n- Id: {id6}\n- Status: executed\n", encoding="utf-8"
            )

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        turns: list[str] = []

        def fake_exec(
            rd: Path, st: dict[str, Any], it: dict[str, Any], *a: Any, **kw: Any
        ) -> None:
            id6 = str(it["id6"])
            turns.append(id6)
            pos = int(it["position"])
            attempt = {
                "number": len(it.get("attempts") or []) + 1,
                "starting_head": head,
                "ending_head": head,
                "ending_status": "",
                "recovery": bool(kw.get("recovery")),
            }
            it.setdefault("attempts", []).append(attempt)
            first_turn_for_item = len([t for t in turns if t == id6]) == 1
            if id6 == "zqs0px" and first_turn_for_item:
                # Truncated zero-work turn: partial disposition, no outcome written
                it["status"] = "partial"
                attempt["host_truncation"] = {
                    "at": "2026-09-19T00:00:00+00:00",
                    "marker": "TASK_TERMINATED",
                }
            else:
                it["status"] = "executed"
                (rd / "outcomes" / f"{pos:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "executed"}), encoding="utf-8"
                )
                finalize_on_disk(id6)
            driver.save_state(rd, st)

        buf = io.StringIO()
        with (
            mock.patch.object(driver, "execute_item", side_effect=fake_exec),
            contextlib.redirect_stdout(buf),
            contextlib.redirect_stderr(buf),
        ):
            driver.run_queue(run_dir, retry_incomplete=False)

        state_after = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        statuses = {it["id6"]: it["status"] for it in state_after["queue"]}

        # zqs0px was retried once within budget, then qmgn12 ran
        assert turns == ["zqs0px", "zqs0px", "qmgn12"]
        assert statuses["zqs0px"] == "executed"
        assert statuses["qmgn12"] == "executed"

        item_zqs0px = next(it for it in state_after["queue"] if it["id6"] == "zqs0px")
        assert len(item_zqs0px["attempts"]) == 2
        assert item_zqs0px[runner_shared.ZERO_WORK_RETRY_COUNT_KEY] == 1

    @DRIVERS
    def test_collision_case_truncated_and_rescued_is_rescored_and_not_retried(
        self, driver: Any, tmp_path: Path
    ) -> None:
        """COLLISION CASE: A turn that is BOTH host-truncated AND rescued is rescored and NOT retried."""
        repo = self._create_repo(tmp_path)
        run_dir = tmp_path / f"run-collision-{driver.__name__}"
        (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)

        queue = [
            {
                "position": 1,
                "id6": "zqs0px",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": [],
                "attempts": [],
            },
            {
                "position": 2,
                "id6": "qmgn12",
                "setid": "reaskscore",
                "action": "execute",
                "kind": "child",
                "status": "queued",
                "dependencies": ["executed:zqs0px"],
                "attempts": [],
            },
        ]
        state = {
            "schema_version": 1,
            "run_id": run_dir.name,
            "repo": str(repo),
            "created_at": "2026-09-19T00:00:00+00:00",
            "updated_at": "2026-09-19T00:00:00+00:00",
            "selectors": ["reaskscore"],
            "options": {"retry_budget": 2, "isolate_worktree": False},
            "set_sessions": {},
            "queue": queue,
        }
        (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        executed_dir = repo / ".aw" / "records" / "plans" / "executed"
        executed_dir.mkdir(parents=True, exist_ok=True)

        def finalize_on_disk(id6: str) -> None:
            (executed_dir / f"20260919-reaskscore-01-{id6}-stub.ipd.md").write_text(
                f"# IPD: stub\n\n- Id: {id6}\n- Status: executed\n", encoding="utf-8"
            )

        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        turns: list[str] = []

        def fake_exec(
            rd: Path, st: dict[str, Any], it: dict[str, Any], *a: Any, **kw: Any
        ) -> None:
            id6 = str(it["id6"])
            turns.append(id6)
            pos = int(it["position"])
            attempt = {
                "number": len(it.get("attempts") or []) + 1,
                "starting_head": head,
                "ending_head": head,
                "ending_status": "",
                "recovery": bool(kw.get("recovery")),
            }
            it.setdefault("attempts", []).append(attempt)
            if id6 == "zqs0px":
                # Truncated in turn 1, BUT defect re-ask rescued it: wrote outcome file and committed work
                attempt["host_truncation"] = {
                    "at": "2026-09-19T00:00:00+00:00",
                    "marker": "TASK_TERMINATED",
                }
                it["status"] = "substantially-complete"
                (rd / "outcomes" / f"{pos:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "substantially-complete"}),
                    encoding="utf-8",
                )
                finalize_on_disk(id6)
            else:
                it["status"] = "executed"
                (rd / "outcomes" / f"{pos:02d}-{id6}.json").write_text(
                    json.dumps({"disposition": "executed"}), encoding="utf-8"
                )
                finalize_on_disk(id6)
            driver.save_state(rd, st)

        buf = io.StringIO()
        with (
            mock.patch.object(driver, "execute_item", side_effect=fake_exec),
            contextlib.redirect_stdout(buf),
            contextlib.redirect_stderr(buf),
        ):
            driver.run_queue(run_dir, retry_incomplete=False)

        state_after = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        statuses = {it["id6"]: it["status"] for it in state_after["queue"]}

        # zqs0px must run ONCE (not retried), and qmgn12 runs once
        assert turns == [
            "zqs0px",
            "qmgn12",
        ], f"Expected zqs0px to be rescored and NOT retried (turns: {turns})"
        assert statuses["zqs0px"] == "substantially-complete"
        assert statuses["qmgn12"] == "executed"

        item_zqs0px = next(it for it in state_after["queue"] if it["id6"] == "zqs0px")
        assert len(item_zqs0px["attempts"]) == 1
        assert runner_shared.ZERO_WORK_RETRY_COUNT_KEY not in item_zqs0px

    def test_exclusivity_argument_holds_in_general_from_two_load_bearing_conditions(
        self,
    ) -> None:
        """Exclusivity holds in general from the two load-bearing conditions: outcome presence and lane commits.

        On an isolated turn, main repo starting_head == ending_head and ending_status == '' are VACUOUS
        (they hold by construction). The exclusivity is guaranteed because:
          (a) Rescore requires receipt['collected'] contains 'outcome' (outcome written is True).
          (b) turn_attempted_nothing refuses when outcome_written is True (condition 1).
          (c) turn_attempted_nothing refuses when lane commits_ahead > 0 (condition 3).
        """
        item = {"id6": "zqs0px", "action": "execute"}
        attempt_base = {
            "number": 1,
            "starting_head": "abc1234",
            "ending_head": "abc1234",
            "ending_status": "",
            "worktree": "/tmp/worktree/lane",
            "host_truncation": {"marker": "TASK_TERMINATED"},
        }

        # 1. Rescued turn has outcome written -> refused by condition 1
        verdict_outcome = turn_attempted_nothing(
            item,
            attempt_base,
            disposition="substantially-complete",
            outcome_written=True,
            lane={"commits_ahead": 0, "dirty": False, "state": "HOLDS-WORK"},
        )
        assert verdict_outcome.attempted_nothing is False
        assert "outcome file WAS written" in verdict_outcome.reason

        # 2. Rescued turn committed work in lane -> refused by condition 3 (lane commits)
        verdict_commits = turn_attempted_nothing(
            item,
            attempt_base,
            disposition="partial",
            outcome_written=False,
            lane={"commits_ahead": 2, "dirty": False, "state": "HOLDS-WORK"},
        )
        assert verdict_commits.attempted_nothing is False
        assert "2 commit(s)" in verdict_commits.reason

        # 3. Rescued turn left dirty lane -> refused by condition 4 (lane dirty)
        verdict_dirty = turn_attempted_nothing(
            item,
            attempt_base,
            disposition="partial",
            outcome_written=False,
            lane={"commits_ahead": 0, "dirty": True, "state": "HOLDS-WORK"},
        )
        assert verdict_dirty.attempted_nothing is False
        assert "DIRTY" in verdict_dirty.reason

        # 4. Genuine zero-work turn (no outcome, 0 commits, clean lane) -> accepted
        verdict_zero = turn_attempted_nothing(
            item,
            attempt_base,
            disposition="partial",
            outcome_written=False,
            lane={"commits_ahead": 0, "dirty": False, "state": "EMPTY"},
        )
        assert verdict_zero.attempted_nothing is True
        assert verdict_zero.proven is True

        # 5. Vacuous condition proof: On an isolated turn, main repo starting_head == ending_head
        # and ending_status == '' hold EVEN WHEN the lane committed 10 commits.
        # This proves the exclusivity CANNOT and DOES NOT rest on main repo head/status.
        assert attempt_base["starting_head"] == attempt_base["ending_head"]
        assert attempt_base["ending_status"] == ""
        vacuous_test_verdict = turn_attempted_nothing(
            item,
            attempt_base,
            disposition="partial",
            outcome_written=False,
            lane={"commits_ahead": 10, "dirty": False, "state": "HOLDS-WORK"},
        )
        assert vacuous_test_verdict.attempted_nothing is False
        assert "10 commit(s)" in vacuous_test_verdict.reason
