#!/usr/bin/env python3
"""Cross-consumer behavioral tests for per-attempt model attribution (attmodel r5fk4k E-06).

Tests that run_dashboard.collect_rows, run_analytics.build_run_facts, and
run_analytics_statistics.model_comparison read the per-attempt model fields correctly,
preserving historical fallbacks and per-host unrecorded labels.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import run_analytics as analytics
from agent_workflows import run_analytics_schema as schema
from agent_workflows import run_analytics_statistics as stats
from agent_workflows import run_dashboard as dash


def _oc_session(
    path: Path, *, cost: float = 0.1, input_tok: int = 100, output_tok: int = 20
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "type": "step_finish",
            "part": {
                "cost": cost,
                "tokens": {"input": input_tok, "output": output_tok, "cache_read": 0},
            },
        }
    )
    path.write_text(line + "\n", encoding="utf-8")


def _write_run(
    root: Path,
    run_id: str,
    *,
    options: dict | None = None,
    attempts: list | None = None,
    sessions: list[str] | None = None,
    driver_id: str = "oc_runipd",
) -> Path:
    run_dir = root / run_id
    sess_dir = run_dir / "sessions"
    sess_dir.mkdir(parents=True, exist_ok=True)

    if sessions:
        for sname in sessions:
            _oc_session(sess_dir / sname)

    state = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:30:00Z",
        "repo": "/repo",
        "runbook": "standard",
        "runbook_sha256": "0" * 64,
        "manifest": [],
        "manifest_sha256": "0" * 64,
        "selectors": {},
        "driver": {"id": driver_id},
        "options": options or {"opencode": "opencode"},
        "set_sessions": {},
        "queue": [
            {
                "id6": "tst001",
                "setid": "testset",
                "position": 1,
                "action": "execute",
                "kind": "child",
                "status": "executed",
                "attempts": attempts or [],
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    return run_dir


class AttemptModelConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_case_a_two_model_run_reports_two_models_across_dashboard_rows(
        self,
    ) -> None:
        """Case (a): A run with distinct executor and verifier models reports both across rows."""
        options = {
            "opencode": "opencode",
            "model": "uri/executor-model",
            "verify_model": "uri/verifier-model",
        }
        attempts = [
            {
                "number": 1,
                "action": "execute",
                "disposition": "executed",
                "log": "sessions/01-tst001-attempt-1.jsonl",
                "verify_log": "sessions/01-tst001-attempt-1-verify.jsonl",
                "model": "uri/executor-model",
                "verify_model": "uri/verifier-model",
                "started_at": "2026-09-01T00:00:00+00:00",
                "ended_at": "2026-09-01T00:05:00+00:00",
                "cost": 0.5,
                "verify_cost": 0.2,
            }
        ]
        run_dir = _write_run(
            self.root,
            "run-case-a",
            options=options,
            attempts=attempts,
            sessions=["01-tst001-attempt-1.jsonl", "01-tst001-attempt-1-verify.jsonl"],
        )
        rows, _ = dash.collect_rows([run_dir], cache_path=None)
        main_row = next(r for r in rows if r["role"] == "main")
        verify_row = next(r for r in rows if r["role"] == "verify")
        self.assertEqual(main_row["model"], "executor-model")
        self.assertEqual(verify_row["model"], "verifier-model")
        self.assertNotEqual(main_row["model"], verify_row["model"])

    def test_case_b_attempt_grain_fact_takes_attempt_model(self) -> None:
        """Case (b): The same run's ATTEMPT-grain fact takes the attempt model while phase facts stay separate."""
        options = {
            "opencode": "opencode",
            "model": "provA/executor-model",
            "verify_model": "provB/verifier-model",
        }
        attempts = [
            {
                "number": 1,
                "action": "execute",
                "disposition": "executed",
                "log": "sessions/01-tst001-attempt-1.jsonl",
                "verify_log": "sessions/01-tst001-attempt-1-verify.jsonl",
                "model": "provA/executor-model",
                "verify_model": "provB/verifier-model",
                "started_at": "2026-09-01T00:00:00+00:00",
                "ended_at": "2026-09-01T00:05:00+00:00",
                "cost": 0.5,
                "verify_cost": 0.2,
            }
        ]
        run_dir = _write_run(
            self.root,
            "run-case-b",
            options=options,
            attempts=attempts,
            sessions=["01-tst001-attempt-1.jsonl", "01-tst001-attempt-1-verify.jsonl"],
        )
        run_facts = analytics.build_run_facts(run_dir)
        att_fact = next(f for f in run_facts.facts if f.grain == schema.Grain.ATTEMPT)
        exec_phase_fact = next(
            f
            for f in run_facts.facts
            if f.grain == schema.Grain.PHASE and f.phase == schema.Phase.EXECUTE
        )
        verify_phase_fact = next(
            f
            for f in run_facts.facts
            if f.grain == schema.Grain.PHASE and f.phase == schema.Phase.VERIFY
        )
        self.assertEqual(att_fact.model, "provA/executor-model")
        self.assertEqual(exec_phase_fact.model, "provA/executor-model")
        self.assertEqual(verify_phase_fact.model, "provB/verifier-model")

    def test_case_c_observed_host_model_beats_frozen_model(self) -> None:
        """Case (c): Observed host_model outranks frozen launch model in precedence."""
        attempt = {
            "host_model": "provObserved/model-turn-1",
            "host_model_source": "export-session-current",
            "model": "provFrozen/launch-model",
            "model_source": "options",
        }
        state = {"options": {"model": "provRun/run-model"}}
        model, source = schema.resolve_attempt_model(attempt, state, role="execute")
        self.assertEqual(model, "provObserved/model-turn-1")
        self.assertEqual(source, "export-session-current")

    def test_case_d_run_with_no_per_attempt_fields_matches_historical_output(
        self,
    ) -> None:
        """Case (d): A historical run with no attempt-level model fields falls back to run options."""
        options = {"opencode": "opencode", "model": "uri/historical-model"}
        attempts = [
            {
                "number": 1,
                "action": "execute",
                "disposition": "executed",
                "log": "sessions/01-tst001-attempt-1.jsonl",
                "started_at": "2026-09-01T00:00:00+00:00",
                "ended_at": "2026-09-01T00:05:00+00:00",
                "cost": 0.5,
            }
        ]
        run_dir = _write_run(
            self.root,
            "run-case-d",
            options=options,
            attempts=attempts,
            sessions=["01-tst001-attempt-1.jsonl"],
        )
        rows, _ = dash.collect_rows([run_dir], cache_path=None)
        self.assertEqual(rows[0]["model"], "historical-model")
        self.assertEqual(rows[0]["model_source"], "options")

        run_facts = analytics.build_run_facts(run_dir)
        att_fact = next(f for f in run_facts.facts if f.grain == schema.Grain.ATTEMPT)
        self.assertEqual(att_fact.model, "uri/historical-model")

    def test_case_e_model_comparison_under_threshold_refuses(self) -> None:
        """Case (e): model_comparison fed a population under 80% coverage refuses with observed coverage."""
        population = [{"model": "prov/model-a", "cost": 1.0} for _ in range(4)] + [
            {"model": "", "cost": 1.0} for _ in range(6)
        ]
        res = stats.model_comparison(population)
        self.assertEqual(res.verdict, stats.Verdict.REFUSED)
        self.assertEqual(res.values["observed_coverage"], 0.4)
        self.assertEqual(res.values["attempts_with_model"], 4)
        self.assertIn("below the declared threshold", res.reason)

    def test_case_f_unclaimed_verify_session_resolves_verifier_model(self) -> None:
        """Case (f): An unclaimed verify session file for an existing attempt resolves the verifier model."""
        options = {
            "opencode": "opencode",
            "model": "uri/executor-model",
            "verify_model": "uri/verifier-model",
        }
        attempts = [
            {
                "number": 1,
                "action": "execute",
                "disposition": "executed",
                "log": "sessions/01-tst001-attempt-1.jsonl",
                # verify_log is deliberately omitted so the file is unclaimed
                "model": "uri/executor-model",
                "verify_model": "uri/verifier-model",
                "started_at": "2026-09-01T00:00:00+00:00",
                "ended_at": "2026-09-01T00:05:00+00:00",
                "cost": 0.5,
            }
        ]
        run_dir = _write_run(
            self.root,
            "run-case-f",
            options=options,
            attempts=attempts,
            sessions=["01-tst001-attempt-1.jsonl", "01-tst001-attempt-1-verify.jsonl"],
        )
        rows, _ = dash.collect_rows([run_dir], cache_path=None)
        v_rows = [r for r in rows if r["role"] == "verify"]
        self.assertTrue(len(v_rows) >= 1)
        v_row = v_rows[0]
        self.assertEqual(v_row["model"], "verifier-model")

    def test_case_g_unrecorded_model_retains_labeled_sentinel_per_row(self) -> None:
        """Case (g): A row resolving no model carries (unrecorded, <host>) rather than bare unrecorded."""
        options = {"opencode": "opencode"}
        attempts = [
            {
                "number": 1,
                "action": "execute",
                "disposition": "executed",
                "log": "sessions/01-tst001-attempt-1.jsonl",
                "started_at": "2026-09-01T00:00:00+00:00",
                "ended_at": "2026-09-01T00:05:00+00:00",
            }
        ]
        run_dir = _write_run(
            self.root,
            "run-case-g",
            options=options,
            attempts=attempts,
            sessions=["01-tst001-attempt-1.jsonl"],
        )
        rows, _ = dash.collect_rows([run_dir], cache_path=None)
        self.assertEqual({r["model"] for r in rows}, {"(unrecorded, oc)"})
        self.assertEqual({r["model_source"] for r in rows}, {"unrecorded"})


if __name__ == "__main__":
    unittest.main()
