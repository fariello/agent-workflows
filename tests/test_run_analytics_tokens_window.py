#!/usr/bin/env python3
"""Tests for per-component token cost, the agent dimension, and `aw runs analyze --since/--until`.

Behavioral only: every test drives the public functions or the `run_analyze` leaf and asserts on
returned values, exit codes, and the published bundle's embedded data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import run_analytics_cli as analytics_cli
from agent_workflows import run_dashboard as dash

from tests.test_run_dashboard import _write_run

UTC = dt.timezone.utc


def _f(value: float | None) -> float:
    assert value is not None
    return value


def _epoch(text: str) -> float:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def _set_created(run: Path, created: str | None) -> None:
    state = json.loads((run / "state.json").read_text())
    if created is None:
        state.pop("created_at", None)
    else:
        state["created_at"] = created
    (run / "state.json").write_text(json.dumps(state))


def _args(repo: Path, **kw) -> argparse.Namespace:
    base = dict(
        dir=str(repo),
        path=False,
        list=False,
        open=False,
        rebuild=False,
        keep_snapshot=None,
        targets=[],
        agent=False,
        json=False,
        color=False,
        no_color=True,
        fields=None,
        verbose=False,
        limit=None,
        since=None,
        until=None,
    )
    base.update(kw)
    return argparse.Namespace(**base)


def _embedded(index_html: str) -> dict:
    m = re.search(
        r'<script type="application/json" id="dash-data">(.*?)</script>',
        index_html,
        re.DOTALL,
    )
    assert m is not None
    return json.loads(m.group(1))


class SplitCostTests(unittest.TestCase):
    def test_parts_sum_exactly_to_recorded_cost(self) -> None:
        parts, method = dash.split_cost(
            1.2345,
            input_tokens=1000,
            output_tokens=200,
            cache_read_tokens=50_000,
            at=_epoch("2026-09-10T00:00:00Z"),
        )
        self.assertEqual(method, "apportioned")
        self.assertAlmostEqual(
            sum(v for v in parts.values() if v is not None), 1.2345, places=12
        )
        # No reasoning tokens were given, so that part is zero; every other part is positive.
        self.assertEqual(parts["cost_reasoning"], 0.0)
        self.assertTrue(
            all(
                v is not None and v > 0
                for k, v in parts.items()
                if k != "cost_reasoning"
            )
        )

    def test_weights_follow_era_rates(self) -> None:
        # Era B: input 5.50, output 27.50, cache 0.55 per Mtok. Equal token counts -> 10 : 50 : 1.
        parts, _ = dash.split_cost(
            61.0,
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cache_read_tokens=1_000_000,
            at=_epoch("2026-09-10T00:00:00Z"),
        )
        self.assertAlmostEqual(_f(parts["cost_input"]), 10.0)
        self.assertAlmostEqual(_f(parts["cost_output"]), 50.0)
        self.assertAlmostEqual(_f(parts["cost_cache_read"]), 1.0)

    def test_free_cache_era_gives_cache_no_share(self) -> None:
        parts, _ = dash.split_cost(
            3.0,
            input_tokens=100,
            output_tokens=100,
            cache_read_tokens=10_000_000,
            at=_epoch("2026-08-01T00:00:00Z"),
        )
        self.assertEqual(parts["cost_cache_read"], 0.0)
        self.assertAlmostEqual(_f(parts["cost_input"]) + _f(parts["cost_output"]), 3.0)

    def test_no_recorded_cost_means_no_split(self) -> None:
        parts, method = dash.split_cost(
            None, input_tokens=10, output_tokens=10, cache_read_tokens=10, at=1.8e9
        )
        self.assertEqual(method, "none")
        self.assertEqual(set(parts.values()), {None})

    def test_no_tokens_means_no_split(self) -> None:
        parts, method = dash.split_cost(
            0.5, input_tokens=0, output_tokens=0, cache_read_tokens=0, at=1.8e9
        )
        self.assertEqual(method, "none")
        self.assertEqual(set(parts.values()), {None})


class RowColumnsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self.tmp.name) / "runs"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_unpriceable_step_costs_are_not_split(self) -> None:
        # The shared fixture's step costs (0.1 per step) match no recovered rate set, so the split
        # is WITHHELD rather than guessed; the recorded total is untouched.
        run = _write_run(self.runs, "run-20260910T000000Z-1")
        _set_created(run, "2026-09-10T00:00:00+00:00")
        rows, _ = dash.collect_rows([run], cache_path=None)
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r["agent"], "oc / Some Model")
            self.assertEqual(r["cost_split"], "none")
            self.assertIsNone(r["cost_input"])
            self.assertIsNotNone(r["cost"])

    def test_priced_steps_split_per_step_including_reasoning(self) -> None:
        run = _write_run(self.runs, "run-20260910T000000Z-p")
        _set_created(run, "2026-09-10T00:00:00+00:00")
        sess = run / "sessions" / "01-abc123-attempt-1.jsonl"
        tok = {
            "input": 1000,
            "output": 200,
            "reasoning": 100,
            "cache": {"read": 50000, "write": 0},
        }
        # Exactly the Opus 5.5 rates: 4.40 / 22.00 / 0.22, reasoning at the output rate.
        cost = (1000 * 4.4 + 300 * 22.0 + 50000 * 0.22) / 1e6
        sess.write_text(
            json.dumps(
                {
                    "type": "step_finish",
                    "timestamp": 1_788_000_000_000,
                    "part": {"tokens": tok, "cost": cost},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        rows, _ = dash.collect_rows([run], cache_path=None)
        main = next(r for r in rows if r["attempt"] == 1 and r["role"] == "main")
        self.assertEqual(main["cost_split"], "per-step")
        self.assertAlmostEqual(main["cost_input"], 1000 * 4.4 / 1e6, places=12)
        self.assertAlmostEqual(main["cost_output"], 200 * 22.0 / 1e6, places=12)
        self.assertAlmostEqual(main["cost_reasoning"], 100 * 22.0 / 1e6, places=12)
        self.assertAlmostEqual(main["cost_cache_read"], 50000 * 0.22 / 1e6, places=12)
        parts = sum(
            main[k]
            for k in ("cost_input", "cost_output", "cost_reasoning", "cost_cache_read")
        )
        self.assertAlmostEqual(parts, main["cost"], places=12)
        payload = dash.build_payload(rows, {"runs": 1})
        for col in (
            "agent",
            "cost_input",
            "cost_output",
            "cost_reasoning",
            "cost_cache_read",
            "cost_split",
        ):
            self.assertEqual(len(payload["columns"][col]), len(rows))

    def test_unrecorded_model_agent_is_not_doubled(self) -> None:
        run = _write_run(self.runs, "run-20260910T000000Z-2")
        state = json.loads((run / "state.json").read_text())
        state["options"] = {"opencode": "opencode"}
        (run / "state.json").write_text(json.dumps(state))
        rows, _ = dash.collect_rows([run], cache_path=None)
        self.assertEqual({r["agent"] for r in rows}, {"(unrecorded, oc)"})

    def test_antigravity_without_recorded_cost_has_no_split(self) -> None:
        run = _write_run(self.runs, "run-20260910T000000Z-3", host="agy")
        state = json.loads((run / "state.json").read_text())
        state["queue"][0]["attempts"][0].pop("cost")
        (run / "state.json").write_text(json.dumps(state))
        rows, _ = dash.collect_rows([run], cache_path=None)
        self.assertEqual(rows[0]["agent"], "agy / Flash")
        self.assertIsNone(rows[0]["cost_input"])
        self.assertEqual(rows[0]["cost_split"], "none")


class DateWindowParseTests(unittest.TestCase):
    NOW = dt.datetime(2026, 10, 17, 12, 0, tzinfo=UTC)

    def test_date_only_until_includes_whole_day(self) -> None:
        start, end = analytics_cli.parse_date_window("2026-10-01", "2026-10-31")
        self.assertEqual(start, dt.datetime(2026, 10, 1, tzinfo=UTC))
        self.assertEqual(end, dt.datetime(2026, 11, 1, tzinfo=UTC))

    def test_timestamp_until_is_taken_as_is(self) -> None:
        _, end = analytics_cli.parse_date_window(None, "2026-10-31T06:00:00Z")
        self.assertEqual(end, dt.datetime(2026, 10, 31, 6, tzinfo=UTC))

    def test_relative_since(self) -> None:
        start, end = analytics_cli.parse_date_window("30d", None, now=self.NOW)
        self.assertEqual(start, self.NOW - dt.timedelta(days=30))
        self.assertIsNone(end)

    def test_no_window(self) -> None:
        self.assertEqual(analytics_cli.parse_date_window(None, None), (None, None))

    def test_bad_value_and_empty_window_refuse(self) -> None:
        with self.assertRaises(analytics_cli.DateWindowError):
            analytics_cli.parse_date_window("not-a-date", None)
        with self.assertRaises(analytics_cli.DateWindowError):
            analytics_cli.parse_date_window("2026-10-05", "2026-10-01")


class DateWindowFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = Path(self.tmp.name) / "runs"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_filters_by_state_created_and_dir_stamp(self) -> None:
        a = _write_run(self.runs, "run-20260901T000000Z-a")
        b = _write_run(self.runs, "run-20261005T000000Z-b")
        _set_created(b, "2026-10-05T00:00:00+00:00")
        c = _write_run(self.runs, "run-20261120T000000Z-c")
        _set_created(c, None)  # falls back to the directory-name stamp
        start, end = analytics_cli.parse_date_window("2026-10-01", "2026-10-31")
        kept, undated = analytics_cli.filter_runs_by_window([a, b, c], start, end)
        self.assertEqual([p.name for p in kept], [b.name])
        self.assertEqual(undated, 0)

    def test_undated_run_is_excluded_and_counted(self) -> None:
        d = _write_run(self.runs, "undated-run")
        _set_created(d, None)
        start, end = analytics_cli.parse_date_window("2026-01-01", None)
        kept, undated = analytics_cli.filter_runs_by_window([d], start, end)
        self.assertEqual((kept, undated), ([], 1))
        kept, undated = analytics_cli.filter_runs_by_window([d], None, None)
        self.assertEqual((len(kept), undated), (1, 0))


class AnalyzeWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        self.runs = self.repo / ".aw" / "records" / "runs"
        old = _write_run(self.runs, "run-20260901T000000Z-1111111")
        _set_created(old, "2026-09-01T00:00:00+00:00")
        new = _write_run(self.runs, "run-20261005T000000Z-2222222")
        _set_created(new, "2026-10-05T00:00:00+00:00")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _run(self, **kw):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = analytics_cli.run_analyze(_args(self.repo, **kw))
        return rc, out.getvalue()

    def test_window_scopes_dashboard_and_reports_it(self) -> None:
        rc, out = self._run(since="2026-10-01", until="2026-10-31")
        self.assertEqual(rc, 0)
        self.assertIn("analyzed 1 run(s)", out)
        self.assertIn("in window 2026-10-01T00:00:00Z .. 2026-11-01T00:00:00Z", out)
        index = (self.runs / "analytics" / "latest" / "index.html").read_text()
        data = _embedded(index)
        self.assertEqual(set(data["columns"]["run"]), {"run-20261005T000000Z-2222222"})
        self.assertEqual(data["info"]["window"]["since"], "2026-10-01T00:00:00Z")
        self.assertEqual(data["info"]["window"]["until"], "2026-11-01T00:00:00Z")

    def test_agent_mode_record_carries_window(self) -> None:
        rc, out = self._run(since="2026-10-01", agent=True)
        self.assertEqual(rc, 0)
        records = [json.loads(line) for line in out.splitlines() if line.strip()]
        result = next(r for r in records if r.get("kind") == "result")
        self.assertIn("runs:1", result["evidence"])
        self.assertIn("window:2026-10-01T00:00:00Z..", result["evidence"])

    def test_no_window_keeps_every_run(self) -> None:
        rc, out = self._run()
        self.assertEqual(rc, 0)
        self.assertIn("analyzed 2 run(s)", out)
        self.assertNotIn("in window", out)
        data = _embedded(
            (self.runs / "analytics" / "latest" / "index.html").read_text()
        )
        self.assertEqual(len(set(data["columns"]["run"])), 2)
        self.assertNotIn("window", data["info"])

    def test_bad_window_is_cannot_run_and_publishes_nothing(self) -> None:
        rc, out = self._run(since="2026-10-31", until="2026-10-01")
        self.assertEqual(rc, analytics_cli.EXIT_CANNOT_RUN)
        self.assertIn("--until", out)
        self.assertFalse((self.runs / "analytics" / "latest" / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
