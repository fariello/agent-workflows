"""Tests for live failed-safely writers and downstream contract behavior (o58r3r / 79d4ix).

Pins the observable behavior of all live producers writing 'failed-safely'
and verifies that retryability, ledger observation, and --retry-incomplete
operate consistently against that spelling.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import (
    agy_runipd,
    lane_containment,
    oc_runipd,
    runner_shared,
    runner_shutdown,
)
from tests.test_typed_queue_entries import (
    _build_queue_for_selector,
    _make_test_repo,
    _write_plan,
)

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _drive_case_a(mod, repo: Path) -> tuple[int, dict, Path]:
    """Drive run_queue with execute_item raising DriverError (sub-case a)."""
    _write_plan(repo, id6="pln001", setid="s1", order=1, status="approved")
    data = _build_queue_for_selector(mod, repo, "pln001")
    run_dir = Path(data["run_dir"])
    state_file = run_dir / "state.json"

    spawn_target = (
        "agent_workflows.oc_runipd.execute_item"
        if mod is oc_runipd
        else "agent_workflows.agy_runipd.execute_item"
    )

    buf = io.StringIO()
    with patch(
        spawn_target, side_effect=runner_shared.DriverError("simulated host failure")
    ):
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            rv = mod.run_queue(run_dir, False)

    state = json.loads(state_file.read_text(encoding="utf-8"))
    item = state["queue"][0]
    return rv, item, run_dir


class TestFailedSafelyLiveWriters(unittest.TestCase):
    """Behavioral tests pinning live failed-safely writers and contracts."""

    def test_case_a_run_queue_driver_error_on_both_hosts(self):
        """Case (a): execute_item raising DriverError leaves item failed-safely and returns 1."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    rv, item, run_dir = _drive_case_a(mod, repo)
                    self.assertEqual(rv, 1)
                    self.assertEqual(item.get("status"), "failed-safely")
                    self.assertIn(
                        "simulated host failure", item.get("driver_error", "")
                    )

    def test_case_b_refuse_undispatchable_typed_entry(self):
        """Case (b): refuse_undispatchable_typed_entry on backlog review writes failed-safely."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir()
            run_dir = Path(td) / "run"
            run_dir.mkdir()
            item = {"artifact_type": "backlog", "action": "review", "id6": "bkg001"}
            state = {"repo": str(repo), "queue": [item]}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                ret = runner_shared.refuse_undispatchable_typed_entry(
                    repo,
                    run_dir,
                    state,
                    item,
                    save_state=lambda rd, st: None,
                    append_jsonl=runner_shared.append_jsonl,
                )
            self.assertTrue(ret)
            self.assertEqual(item.get("status"), "failed-safely")

            events_file = run_dir / "events.jsonl"
            self.assertTrue(events_file.is_file())
            events = [
                json.loads(line)
                for line in events_file.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "item-refused")
            self.assertEqual(events[0]["status"], "failed-safely")

    def test_case_c_bound_expiry_record(self):
        """Case (c): lane_containment.bound_expiry_record disposition is failed-safely."""
        rec = lane_containment.bound_expiry_record("turn", 30.0, "2026-10-13T00:00:00Z")
        self.assertEqual(rec.get("disposition"), "failed-safely")

    def test_case_d_handle_turn_failure_retry_exhausted(self):
        """Case (d): handle_turn_failure_retry with budget 0 writes failed-safely."""
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td)
            item = {"id6": "tst001", "type": "ipd"}
            state = {"options": {"retry_budget": 0}}
            attempt: dict = {}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                ret_disp = runner_shared.handle_turn_failure_retry(
                    run_dir=run_dir,
                    state=state,
                    item=item,
                    attempt=attempt,
                    attempt_no=1,
                    disposition="failed-safely",
                    host_labels=None,
                    save_state=lambda *a: None,
                    append_jsonl=lambda *a: None,
                )
            self.assertEqual(ret_disp, "failed-safely")
            self.assertEqual(item.get("status"), "failed-safely")

    def test_case_e_canonical_status_retryability_hazard(self):
        """Case (e): observed token is retryable; canonical_terminal_status(token) is not."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _, item, _ = _drive_case_a(oc_runipd, repo)
            token = item["status"]

            retryable_raw, why_raw = runner_shared.turn_failure_is_retryable({}, token)
            self.assertTrue(retryable_raw)

            canonical = runner_shared.canonical_terminal_status(token)
            retryable_canon, why_canon = runner_shared.turn_failure_is_retryable(
                {}, canonical
            )
            self.assertFalse(retryable_canon)

    def test_case_f_ledger_coherence_under_observe_ledger(self):
        """Case (f): ledger holding the observed token is coherent under observe_ledger."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _, item, run_dir = _drive_case_a(oc_runipd, repo)
            coherent, detail = runner_shutdown.observe_ledger(run_dir)
            self.assertTrue(coherent, f"Expected ledger to be coherent, got: {detail}")

    def test_case_g_retry_incomplete_requeues_on_both_hosts(self):
        """Case (g): run_queue with retry_incomplete=True requeues item in observed state."""
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    rv1, item, run_dir = _drive_case_a(mod, repo)
                    self.assertEqual(rv1, 1)

                    dispatched = []

                    def fake_execute(rd, st, runnable, **kwargs):
                        dispatched.append(runnable["id6"])
                        runnable["status"] = "executed"
                        mod.save_state(rd, st)

                    spawn_target = (
                        "agent_workflows.oc_runipd.execute_item"
                        if mod is oc_runipd
                        else "agent_workflows.agy_runipd.execute_item"
                    )

                    buf = io.StringIO()
                    with patch(spawn_target, side_effect=fake_execute):
                        with contextlib.redirect_stdout(
                            buf
                        ), contextlib.redirect_stderr(buf):
                            rv2 = mod.run_queue(run_dir, retry_incomplete=True)

                    self.assertEqual(rv2, 0)
                    self.assertIn("pln001", dispatched)

    def test_case_h_all_producers_consistent_with_case_a(self):
        """Case (h): producers in (b), (c), (d) and finalize-exhausted match token from (a)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _make_test_repo(Path(td))
            _, item_a, _ = _drive_case_a(oc_runipd, repo)
            token_a = item_a["status"]

            # (b)
            run_dir_b = Path(td) / "b"
            run_dir_b.mkdir()
            item_b = {"artifact_type": "backlog", "action": "review", "id6": "bkg001"}
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                runner_shared.refuse_undispatchable_typed_entry(
                    repo,
                    run_dir_b,
                    {"repo": str(repo), "queue": [item_b]},
                    item_b,
                    save_state=lambda rd, st: None,
                    append_jsonl=runner_shared.append_jsonl,
                )
            status_b = item_b["status"]

            # (c)
            rec_c = lane_containment.bound_expiry_record(
                "turn", 30.0, "2026-10-13T00:00:00Z"
            )
            status_c = rec_c["disposition"]

            # (d)
            run_dir_d = Path(td) / "d"
            run_dir_d.mkdir()
            item_d = {"id6": "tst001", "type": "ipd"}
            state_d = {"options": {"retry_budget": 0}}
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                runner_shared.handle_turn_failure_retry(
                    run_dir=run_dir_d,
                    state=state_d,
                    item=item_d,
                    attempt={},
                    attempt_no=1,
                    disposition=token_a,
                    host_labels=None,
                    save_state=lambda *a: None,
                    append_jsonl=lambda *a: None,
                )
            status_d = item_d["status"]

            # finalize-exhausted status
            status_finalize = runner_shared.FINALIZE_RETRY_EXHAUSTED_STATUS

            self.assertEqual(status_b, token_a)
            self.assertEqual(status_c, token_a)
            self.assertEqual(status_d, token_a)
            self.assertEqual(status_finalize, token_a)
