"""Outcome tests for `runner_shared.dependency_depth` on large, deep queues.

A run's queue order is sorted by dependency depth. On a 209-plan review queue with a 71-deep
chain the depth walk took over 15 minutes before the run printed anything (2026-11-11), because
it walked every path rather than every node. These tests drive the public function and check the
depths it returns and that a deep, densely linked queue finishes quickly.
"""

from __future__ import annotations

import time
import unittest

from agent_workflows import runner_shared


def _entry(id6: str, deps: list[str], action: str = "review", **extra) -> dict:
    return {
        "id6": id6,
        "dependencies": [f"executed:{d}" for d in deps],
        "action": action,
        "setid": extra.get("setid", "big"),
        "kind": extra.get("kind"),
        "order": extra.get("order", 1),
    }


def _ladder(n: int) -> dict:
    """Node i depends on i-1 and i-2: the path count grows like Fibonacci(n)."""
    ids = [f"ld{i:04d}" for i in range(n)]
    by_id = {}
    for i, x in enumerate(ids):
        deps = [ids[j] for j in (i - 1, i - 2) if j >= 0]
        by_id[x] = _entry(x, deps)
    return by_id


class DependencyDepthScalingTests(unittest.TestCase):
    def test_deep_dense_chain_depths_are_exact(self) -> None:
        by_id = _ladder(80)
        start = time.monotonic()
        depths = [runner_shared.dependency_depth(x, by_id) for x in by_id]
        elapsed = time.monotonic() - start
        self.assertEqual(depths, list(range(80)))
        # Unmemoized this is ~Fibonacci(80) calls (never finishes); memoized it is instant.
        self.assertLess(elapsed, 5.0)

    def test_orchestrator_review_sits_after_its_children(self) -> None:
        by_id = _ladder(30)
        by_id["orch00"] = _entry("orch00", [], kind="orchestrator", order=0)
        self.assertEqual(runner_shared.dependency_depth("orch00", by_id), 30)

    def test_cycle_still_terminates_with_seen_relative_answer(self) -> None:
        by_id = {
            "cya001": _entry("cya001", ["cyb002"]),
            "cyb002": _entry("cyb002", ["cyc003"]),
            "cyc003": _entry("cyc003", ["cya001"]),
        }
        self.assertEqual(
            [runner_shared.dependency_depth(x, by_id) for x in sorted(by_id)],
            [3, 3, 3],
        )

    def test_out_of_queue_target_contributes_nothing(self) -> None:
        by_id = {"in0001": _entry("in0001", ["gone99"])}
        self.assertEqual(runner_shared.dependency_depth("in0001", by_id), 0)


if __name__ == "__main__":
    unittest.main()
