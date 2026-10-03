#!/usr/bin/env python3
"""Tests for runsdash (`97i0ao`): session facts and the drill-down run dashboard.

Stdlib unittest only.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import run_analytics_cli as analytics_cli
from agent_workflows import run_analytics_spa as spa
from agent_workflows import run_dashboard as dash
from agent_workflows import verifier_corroboration as vc


def _jl(path: Path, objs) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(o) for o in objs) + "\n\nnot json\n", encoding="utf-8"
    )


def _oc_session(path: Path, *, steps: int = 2, cost: float = 0.1) -> None:
    objs = []
    t = 1_787_949_977_000
    for i in range(steps):
        objs.append({"type": "step_start", "timestamp": t + i * 1000, "part": {}})
        objs.append(
            {
                "type": "tool_use",
                "timestamp": t + i * 1000 + 100,
                "part": {
                    "tool": "bash",
                    "state": {
                        "status": "completed",
                        "input": {"command": "python3 -m pytest tests"},
                        "time": {"start": t, "end": t + 500},
                    },
                },
            }
        )
        objs.append(
            {
                "type": "tool_use",
                "timestamp": t + i * 1000 + 200,
                "part": {
                    "tool": "read",
                    "state": {
                        "status": "error",
                        "input": {"filePath": "a.py"},
                        "time": {"start": t, "end": t + 10},
                    },
                },
            }
        )
        objs.append(
            {
                "type": "step_finish",
                "timestamp": t + i * 1000 + 900,
                "part": {
                    "tokens": {
                        "total": 110,
                        "input": 100,
                        "output": 10,
                        "reasoning": 0,
                        "cache": {"write": 0, "read": 1000},
                    },
                    "cost": cost,
                },
            }
        )
    _jl(path, objs)


def _agy_session(path: Path) -> None:
    objs = [
        {"event": "init", "init": {"tools": []}},
        {
            "event": "step_update",
            "step_update": {
                "step_index": 0,
                "state": "DONE",
                "step_type": "user_input",
            },
        },
        {
            "event": "step_update",
            "step_update": {
                "step_index": 1,
                "state": "DONE",
                "step_type": "agent_response",
                "duration_seconds": 4.0,
                "usage": {
                    "input_tokens": 200,
                    "output_tokens": 20,
                    "thinking_tokens": 5,
                    "cache_read_tokens": 50,
                },
            },
        },
        {
            "event": "step_update",
            "step_update": {
                "step_index": 2,
                "state": "ACTIVE",
                "step_type": "tool",
                "tool_name": "run_command",
            },
        },
        {
            "event": "step_update",
            "step_update": {
                "step_index": 2,
                "state": "DONE",
                "step_type": "tool",
                "tool_name": "run_command",
                "duration_seconds": 1.5,
                "tool_info": {"parameters": {"CommandLine": "git status"}},
            },
        },
        {
            "event": "step_update",
            "step_update": {
                "step_index": 3,
                "state": "ERROR",
                "step_type": "tool",
                "tool_name": "view_file",
                "duration_seconds": 0.1,
                "tool_info": {"parameters": {"AbsolutePath": "/x/b.py"}},
            },
        },
        {"event": "result", "result": {"status": "SUCCESS"}},
    ]
    _jl(path, objs)


def _write_run(runs_root: Path, run_id: str, *, host: str = "oc") -> Path:
    run = runs_root / run_id
    sess = run / "sessions"
    if host == "oc":
        _oc_session(sess / "01-abc123-attempt-1.jsonl")
        _oc_session(sess / "01-abc123-attempt-1-verify.jsonl", steps=1, cost=0.05)
        _oc_session(sess / "01-abc123-attempt-2.jsonl", steps=1)
        _oc_session(sess / "01-abc123-attempt-2-gate-answer.jsonl", steps=1, cost=0.01)
        options = {"opencode": "opencode", "model": "uri/some-model"}
        driver = {"id": "oc_runipd"}
    else:
        _agy_session(sess / "01-abc123-attempt-1.jsonl")
        options = {"cost_attribution": {"host": "agy", "model": "Flash"}}
        driver = {"id": "agy_runipd"}

    def log(n: str) -> str:
        return str(sess / n)

    attempts = [
        {
            "number": 1,
            "action": "execute",
            "disposition": "partial",
            "log": log("01-abc123-attempt-1.jsonl"),
            "started_at": "2026-09-01T00:00:00+00:00",
            "ended_at": "2026-09-01T00:10:00+00:00",
            "tokens": {"input": 1, "output": 1, "cache": 0, "total": 2},
            "cost": 9.99,
        }
    ]
    if host == "oc":
        attempts[0]["verify_log"] = log("01-abc123-attempt-1-verify.jsonl")
        attempts[0]["verification"] = "unverified"
        attempts.append(
            {
                "number": 2,
                "action": "execute",
                "recovery": True,
                "disposition": "executed",
                "log": log("01-abc123-attempt-2.jsonl"),
                "started_at": "2026-09-01T00:10:00+00:00",
                "ended_at": "2026-09-01T00:15:00+00:00",
            }
        )
    state = {
        "run_id": run_id,
        "created_at": "2026-09-01T00:00:00+00:00",
        "driver": driver,
        "options": options,
        "queue": [
            {
                "id6": "abc123",
                "setid": "demo",
                "action": "execute",
                "kind": "child",
                "status": "executed",
                "attempts": attempts,
            }
        ],
    }
    run.mkdir(parents=True, exist_ok=True)
    (run / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (run / "events.jsonl").write_text("", encoding="utf-8")
    return run


class SessionStatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_opencode_session(self) -> None:
        p = self.root / "s.jsonl"
        _oc_session(p, steps=3, cost=0.2)
        st = dash.session_stats(p)
        self.assertEqual(st["format"], "oc")
        self.assertEqual(st["steps"], 3)
        self.assertEqual(st["input"], 300)
        self.assertEqual(st["output"], 30)
        self.assertEqual(st["cache_read"], 3000)
        self.assertAlmostEqual(st["cost"], 0.6)
        self.assertEqual(st["tool_calls"], 6)
        self.assertEqual(st["tool_errors"], 3)
        self.assertEqual(st["categories"], {"shell": 3, "read": 3})
        self.assertEqual(st["commands"], {"test": 3})
        self.assertEqual(st["tool_err"], {"read": 3})
        self.assertEqual(st["files_read"], 1)

    def test_antigravity_session(self) -> None:
        p = self.root / "a.jsonl"
        _agy_session(p)
        st = dash.session_stats(p)
        self.assertEqual(st["format"], "agy")
        self.assertEqual(st["steps"], 1)
        self.assertEqual(st["input"], 200)
        self.assertEqual(st["output"], 20)
        self.assertEqual(st["reasoning"], 5)
        self.assertEqual(st["cache_read"], 50)
        self.assertFalse(st["has_cost"])
        # ACTIVE tool steps are not counted; DONE and ERROR are.
        self.assertEqual(st["tool_calls"], 2)
        self.assertEqual(st["tool_errors"], 1)
        self.assertEqual(st["commands"], {"git": 1})
        self.assertEqual(st["result_status"], "SUCCESS")

    def test_missing_file_is_empty_not_error(self) -> None:
        st = dash.session_stats(self.root / "nope.jsonl")
        self.assertEqual(st["steps"], 0)

    def test_command_kind(self) -> None:
        self.assertEqual(dash.command_kind("cd x && python3 -m pytest -q"), "test")
        self.assertEqual(dash.command_kind("git diff --stat"), "git")
        self.assertEqual(dash.command_kind("aw ipd lint foo"), "aw")
        self.assertEqual(dash.command_kind("rg -n foo ."), "inspect")
        self.assertEqual(dash.command_kind("echo hi"), "other")


class CollectRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runs = self.root / "runs"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_one_row_per_session_with_roles(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-1")
        rows, info = dash.collect_rows([run], cache_path=self.root / "c.json")
        roles = sorted((r["attempt"], r["role"]) for r in rows)
        self.assertEqual(
            roles, [(1, "main"), (1, "verify"), (2, "gate-answer"), (2, "main")]
        )
        main1 = next(r for r in rows if r["attempt"] == 1 and r["role"] == "main")
        self.assertEqual(main1["model"], "some-model")
        self.assertEqual(main1["host"], "oc")
        self.assertEqual(main1["outcome"], "partial")
        self.assertEqual(main1["token_source"], "log")
        # Log numbers win over the state.json summary.
        self.assertEqual(main1["input"], 200)
        self.assertAlmostEqual(main1["cost"], 0.2)
        self.assertEqual(main1["wall"], 600)
        verify = next(r for r in rows if r["role"] == "verify")
        self.assertEqual(verify["outcome"], "failed")
        gate = next(r for r in rows if r["role"] == "gate-answer")
        self.assertTrue(gate["recovery"])
        self.assertEqual(gate["id6"], "abc123")
        self.assertEqual(info["sessions"], 4)

    def test_state_fallback_when_log_missing(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-2")
        (run / "sessions" / "01-abc123-attempt-1.jsonl").unlink()
        rows, _ = dash.collect_rows([run], cache_path=None)
        main1 = next(r for r in rows if r["attempt"] == 1 and r["role"] == "main")
        self.assertEqual(main1["token_source"], "state")
        self.assertEqual(main1["total_tokens"], 2)
        self.assertAlmostEqual(main1["cost"], 9.99)
        self.assertFalse(main1["has_log"])

    def test_unrecorded_model_is_labeled_per_host(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-3")
        state = json.loads((run / "state.json").read_text())
        state["options"] = {"opencode": "opencode"}
        (run / "state.json").write_text(json.dumps(state))
        rows, _ = dash.collect_rows([run], cache_path=None)
        self.assertEqual({r["model"] for r in rows}, {"(unrecorded, oc)"})

    def test_antigravity_run(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-4", host="agy")
        rows, _ = dash.collect_rows([run], cache_path=None)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["host"], "agy")
        self.assertEqual(rows[0]["model"], "Flash")
        # agy logs carry no cost; the state figure is the only one.
        self.assertAlmostEqual(rows[0]["cost"], 9.99)

    def test_per_row_model_attribution_across_roles(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-two-model")
        state = json.loads((run / "state.json").read_text())
        state["options"]["model"] = "uri/executor-model"
        state["options"]["verify_model"] = "uri/verifier-model"
        state["queue"][0]["attempts"][0]["model"] = "uri/attempt-exec-model"
        state["queue"][0]["attempts"][0]["verify_model"] = "uri/attempt-verify-model"
        (run / "state.json").write_text(json.dumps(state))
        rows, _ = dash.collect_rows([run], cache_path=None)
        main_row = next(r for r in rows if r["attempt"] == 1 and r["role"] == "main")
        verify_row = next(
            r for r in rows if r["attempt"] == 1 and r["role"] == "verify"
        )
        self.assertEqual(main_row["model"], "attempt-exec-model")
        self.assertEqual(verify_row["model"], "attempt-verify-model")
        self.assertNotEqual(main_row["model"], verify_row["model"])

    def test_stats_cache_reuse_and_invalidation(self) -> None:
        run = _write_run(self.runs, "run-20260901T000000Z-5")
        cpath = self.root / "cache.json"
        _, first = dash.collect_rows([run], cache_path=cpath)
        self.assertEqual((first["cache_hits"], first["cache_misses"]), (0, 4))
        _, second = dash.collect_rows([run], cache_path=cpath)
        self.assertEqual((second["cache_hits"], second["cache_misses"]), (4, 0))
        _oc_session(run / "sessions" / "01-abc123-attempt-2.jsonl", steps=5)
        _, third = dash.collect_rows([run], cache_path=cpath)
        self.assertEqual((third["cache_hits"], third["cache_misses"]), (3, 1))


class RenderTests(unittest.TestCase):
    def test_offline_and_escaped(self) -> None:
        row: dict = {c: None for c in dash.COLUMNS}
        row.update(
            {
                "run": "run-x",
                "set": "</script><script>alert(1)</script>",
                "model": "m & <b>",
                "tools": {"bash": 2},
                "tool_err": {"bash": 1},
            }
        )
        payload = dash.build_payload([row], {"runs": 1})
        doc = dash.render_dashboard(payload)
        self.assertEqual(spa.scan_for_network_references(doc), [])
        self.assertNotIn("</script><script>alert", doc)
        m = re.search(
            r'<script type="application/json" id="dash-data">(.*?)</script>',
            doc,
            re.DOTALL,
        )
        assert m is not None
        data = json.loads(m.group(1))
        self.assertEqual(data["columns"]["set"], ["</script><script>alert(1)</script>"])
        self.assertEqual(data["tool_names"], ["bash"])
        self.assertEqual(data["tools"], [[0, 2, 1]])
        self.assertEqual(data["tool_categories"], {"bash": "shell"})

    def test_assets_ship_beside_module(self) -> None:
        base = Path(dash.__file__).parent / dash.ASSETS_DIRNAME
        for name in ("dashboard.js", "dashboard.css"):
            self.assertTrue((base / name).is_file(), name)


class AnalyzePublishesDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name).resolve()
        self.runs = self.repo / ".aw" / "records" / "runs"
        _write_run(self.runs, "run-20260901T000000Z-1111111")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bundle_has_dashboard_and_classic_report(self) -> None:
        args = argparse.Namespace(
            dir=str(self.repo),
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
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            rc = analytics_cli.run_analyze(args)
        self.assertEqual(rc, 0)
        latest = self.runs / "analytics" / "latest"
        index = (latest / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="dash-data"', index)
        self.assertTrue((latest / analytics_cli.CLASSIC_REPORT_FILENAME).is_file())
        manifest = json.loads((latest / "manifest.json").read_text(encoding="utf-8"))
        names = {f["name"] for f in manifest["files"]}
        self.assertTrue({"index.html", "report.html", "analysis.json"} <= names)
        m = re.search(r'id="dash-data">(.*?)</script>', index, re.DOTALL)
        assert m is not None
        data = json.loads(m.group(1))
        self.assertEqual(data["n"], 4)

    def test_dashboard_failure_falls_back_to_classic(self) -> None:
        orig = analytics_cli._render_dashboard_html

        def boom(*a, **k):
            raise RuntimeError("x")

        analytics_cli._render_dashboard_html = boom
        try:
            docs = analytics_cli._bundle_documents(self.repo, [], generated_label="t")
        finally:
            analytics_cli._render_dashboard_html = orig
        self.assertEqual(docs["index.html"], docs["report.html"])


class TestUnifiedToolExtractionRouting(unittest.TestCase):
    """E-07: Behavioral tests pinning cross-consumer tool call agreement between dashboard and corroboration."""

    def test_cross_consumer_tool_agreement_matrix(self) -> None:
        """Matrix of oc and agy events: session_stats and extract_session_commands derive from the same call."""
        events = [
            # oc bash
            {
                "type": "tool_use",
                "part": {
                    "tool": "bash",
                    "state": {
                        "status": "completed",
                        "input": {"command": "pytest tests"},
                    },
                },
            },
            # agy run_command
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_name": "run_command",
                    "duration_seconds": 1.0,
                    "tool_info": {"parameters": {"CommandLine": "git status"}},
                },
            },
            # oc padded tool name
            {
                "type": "tool_use",
                "part": {
                    "tool": " bash ",
                    "state": {"status": "completed", "input": {"command": "make test"}},
                },
            },
            # agy padded tool name
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_name": " run_command ",
                    "duration_seconds": 1.0,
                    "tool_info": {"parameters": {"CommandLine": "python3 main.py"}},
                },
            },
            # oc blank command
            {
                "type": "tool_use",
                "part": {
                    "tool": "bash",
                    "state": {"status": "completed", "input": {"command": "   "}},
                },
            },
            # agy blank command
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_name": "run_command",
                    "duration_seconds": 1.0,
                    "tool_info": {"parameters": {"CommandLine": "   "}},
                },
            },
            # all four delegations
            {
                "type": "tool_use",
                "part": {"tool": "task", "state": {"status": "completed", "input": {}}},
            },
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_name": "browser_subagent",
                    "duration_seconds": 1.0,
                    "tool_info": {},
                },
            },
            {
                "type": "tool_use",
                "part": {
                    "tool": "subagent",
                    "state": {"status": "completed", "input": {}},
                },
            },
            {
                "event": "step_update",
                "step_update": {
                    "state": "DONE",
                    "step_type": "tool",
                    "tool_name": "invoke_subagent",
                    "duration_seconds": 1.0,
                    "tool_info": {},
                },
            },
            # error
            {
                "type": "tool_use",
                "part": {
                    "tool": "read",
                    "state": {"status": "error", "input": {"filePath": "missing.py"}},
                },
            },
        ]
        with tempfile.TemporaryDirectory() as td:
            for idx, ev in enumerate(events):
                p = Path(td) / f"event_{idx}.jsonl"
                p.write_text(json.dumps(ev) + "\n", encoding="utf-8")
                stats = dash.session_stats(p)
                extracted = vc.extract_session_commands(p)

                tc = vc.tool_call_from_event(ev)
                self.assertIsNotNone(tc)
                assert tc is not None

                # 1. Tool name agreement
                self.assertEqual(set(stats["tools"].keys()), {tc.tool})

                # 2. Command text presence
                cmd_count = sum(stats["commands"].values())
                if tc.command is not None:
                    self.assertEqual(cmd_count, 1)
                    self.assertEqual(len(extracted.commands), 1)
                    self.assertEqual(extracted.commands[0].command, tc.command)
                else:
                    self.assertEqual(cmd_count, 0)
                    self.assertEqual(len(extracted.commands), 0)

                # 3. Error flag agreement
                err_count = stats["tool_errors"]
                self.assertEqual(err_count, 1 if tc.error else 0)

                # 4. Delegation flag agreement
                del_count = stats["categories"].get("subagent", 0)
                self.assertEqual(del_count, 1 if tc.delegation else 0)
                self.assertEqual(extracted.delegation_count, 1 if tc.delegation else 0)

    def test_dashboard_subagent_categories_e04(self) -> None:
        """E-04: TOOL_CATEGORIES maps task, browser_subagent, subagent, invoke_subagent to subagent."""
        for name in ("task", "browser_subagent", "subagent", "invoke_subagent"):
            self.assertEqual(dash.tool_category(name), "subagent")

    def test_dashboard_schema_version_is_3(self) -> None:
        """E-04 / OQ-02: DASHBOARD_SCHEMA_VERSION is 3."""
        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 3)


if __name__ == "__main__":
    unittest.main()
