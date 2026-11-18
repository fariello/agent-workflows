"""Run progress counts only work this run can dispatch, in BOTH halves of the fraction.

A Set with some members already executed must open at `0/<live>` and count 1, 2, ... for the live
members. `dispatchable_work_total` fixed the denominator on 2026-09-22; the sequence index
(`execution_index`) still counted pre-executed members, so a 10-member Set with 4 already executed
announced its first live plan as 5 of 6. The OpenCode host also still used `len(queue)` as the
denominator. Originally fixed on the never-landed branch `statusbar-run-progress` (504de21e).
"""

from __future__ import annotations

import unittest

from agent_workflows import oc_runipd, render_stream


def _queue(n_total: int, n_pre_executed: int) -> list[dict]:
    queue = []
    for i in range(1, n_total + 1):
        st = "executed" if i <= n_pre_executed else "approved"
        queue.append(
            {
                "id6": f"item{i:02d}",
                "position": i,
                "status": st,
                "initial_status": st,
                "action": "execute",
                "set": "s",
                "order": i,
            }
        )
    return queue


class PartiallyExecutedSetProgressTests(unittest.TestCase):
    def test_first_live_plan_is_one_of_live_workload(self):
        queue = _queue(10, 4)
        state = {"queue": queue, "run_order": oc_runipd.run_order_rationale(queue)}
        total = render_stream.dispatchable_work_total(queue)
        self.assertEqual(total, 6)

        first = queue[4]
        oc_runipd.update_execution_order(state, first)
        seq = render_stream.execution_index(first, state)
        self.assertEqual(seq, 1, "first live plan must be 1 of 6, not 5 of 6")
        self.assertIn("0/6", render_stream.format_progress_bar(seq - 1, total))

        first["status"] = "executed"
        second = queue[5]
        oc_runipd.update_execution_order(state, second)
        self.assertEqual(render_stream.execution_index(second, state), 2)

    def test_fully_live_queue_is_unchanged(self):
        queue = _queue(3, 0)
        state = {"queue": queue, "run_order": oc_runipd.run_order_rationale(queue)}
        for expected, item in enumerate(queue, start=1):
            oc_runipd.update_execution_order(state, item)
            self.assertEqual(render_stream.execution_index(item, state), expected)
            item["status"] = "executed"


class ResumedItemProgressTests(unittest.TestCase):
    """An item resumed after a later item settled counts that item as done.

    Measured on a live review run: the first item in the run order paused for a human answer, the
    next item was reviewed, and on resume the live statusline read `0/3` beside `1 ok`.
    """

    def test_resumed_first_item_counts_later_settled_item(self):
        queue = _queue(3, 0)
        state = {"queue": queue, "run_order": oc_runipd.run_order_rationale(queue)}
        first, second, _third = queue
        oc_runipd.update_execution_order(state, first)
        first["status"] = "awaiting-human"
        first["attempts"] = [{"n": 1}]
        oc_runipd.update_execution_order(state, second)
        second["status"] = "reviewed"
        second["attempts"] = [{"n": 1}]
        first["status"] = "running"

        done = render_stream.completed_work_count(first, state)
        self.assertEqual(done, 1)
        self.assertIn("1/3", render_stream.format_progress_bar(done, 3))

    def test_nothing_settled_reads_zero(self):
        queue = _queue(3, 0)
        state = {"queue": queue, "run_order": oc_runipd.run_order_rationale(queue)}
        self.assertEqual(render_stream.completed_work_count(queue[0], state), 0)

    def test_pre_executed_members_are_not_counted(self):
        queue = _queue(10, 4)
        state = {"queue": queue, "run_order": oc_runipd.run_order_rationale(queue)}
        self.assertEqual(render_stream.completed_work_count(queue[4], state), 0)


if __name__ == "__main__":
    unittest.main()
