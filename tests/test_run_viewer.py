"""Unit tests for `agent_workflows.run_viewer` (aw runs / run viewer).

Run records are intentionally gitignored, so tests construct the small, representative
record set they need instead of reading a developer's live repository.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest import TestCase

from agent_workflows import cli, run_viewer
from agent_workflows.term import Term

# --------------------------------------------------------------------------------------------------
# Fixture helpers for the unresolvable-target refusal (runsverify 7wei1o E-05)
# --------------------------------------------------------------------------------------------------

#: A resolvable run id in the fixture below. Its trailing digits double as the substring-match case.
_FIXTURE_RUN = "run-20260901T000000Z-2367239"
#: A Set the fixture declares (two runs carry it), i.e. the legitimate setid-resolution case.
_FIXTURE_SETID = "runnernorm"


def _build_viewer_fixture(root: Path) -> Path:
    """Write four driver run records under ``root``, then return ``root``."""
    runs = root / ".aw" / "records" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    specs = [
        (_FIXTURE_RUN, _FIXTURE_SETID),
        ("run-20260901T010000Z-1111111", _FIXTURE_SETID),
        ("run-20260902T000000Z-2222222", "lanectn"),
        # The leaf-name collision the `--` escape hatch exists for.
        ("run-20260902T010000Z-3333333", "status"),
    ]
    for run_id, setid in specs:
        d = runs / run_id
        d.mkdir(exist_ok=True)
        (d / "state.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "created_at": "2026-09-01T00:00:00+00:00",
                    "updated_at": "2026-09-01T01:00:00+00:00",
                    "driver": {
                        "path": "agent_workflows/oc_runipd.py",
                        "host": "opencode",
                    },
                    "options": {"base_branch": "main", "worktree": "clean"},
                    "selectors": [setid],
                    "queue": [
                        {
                            "position": 1,
                            "id6": "aaa111",
                            "setid": setid,
                            "action": "execute",
                            "status": "complete",
                            "configured_file": "",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
    return root


def _run_viewer(root: Path, argv: list[str]) -> tuple[str, str, int]:
    """Invoke `aw runs` through the REAL cli entry point. Returns ``(stdout, stderr, rc)``."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(["runs", "--dir", str(root), *argv])
    except SystemExit as exc:
        rc = int(exc.code or 0)
    return out.getvalue(), err.getvalue(), rc


class RunViewerTests(TestCase):
    def setUp(self):
        self.maxDiff = None
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)
        self._create_run_fixtures()

    def tearDown(self):
        self._temporary_directory.cleanup()

    def _run_dir(self, run_id):
        return self.root / ".aw" / "records" / "runs" / run_id

    def _create_run_fixtures(self):
        records = (
            (
                "run-20260827T212854Z-2364829",
                "2026-08-27T12:00:00+00:00",
                [
                    {
                        "position": 1,
                        "id6": "pre001",
                        "setid": "ipddeps",
                        "action": "execute",
                        "status": "executed",
                        "verification_status": "verified",
                    }
                ],
            ),
            (
                "run-20260827T212958Z-2367239",
                "2026-08-27T13:00:00+00:00",
                [
                    {
                        "position": 1,
                        "id6": "ryvoi5",
                        "setid": "runnernorm",
                        "action": "execute",
                        "status": "partial",
                        "last_outcome": {
                            "disposition": "dependency-blocked",
                            "summary": "Waiting for dependency.",
                            "incomplete_requirements": ["dependency remains pending"],
                        },
                    },
                    {
                        "position": 2,
                        "id6": "dg28i9",
                        "setid": "runnernorm",
                        "action": "execute",
                        "status": "substantially-complete",
                        "verification_status": "verified",
                    },
                    {
                        "position": 3,
                        "id6": "puot79",
                        "setid": "runnernorm",
                        "action": "execute",
                        "status": "executed",
                        "verification_status": "verified",
                    },
                ],
            ),
            (
                "run-20260828T000000Z-999999",
                "2026-08-28T00:00:00+00:00",
                [
                    {
                        "position": 1,
                        "id6": "last01",
                        "setid": "other",
                        "action": "execute",
                        "status": "executed",
                        "verification_status": "verified",
                    }
                ],
            ),
        )
        for run_id, timestamp, queue in records:
            run_dir = self._run_dir(run_id)
            run_dir.mkdir(parents=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": run_id,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "driver": {"path": "agent_workflows/oc_runipd.py"},
                        "queue": queue,
                    }
                ),
                encoding="utf-8",
            )

    def _interrupted_fixture(self, root, file_status, bucket, run_status="interrupted"):
        """One synthetic plan at ``file_status`` in ``bucket``/, audited against ``run_status``."""
        d = root / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260908-intr-01-intr01-a-slug.ipd.md").write_text(
            f"# IPD: a slug\n\n- Id: intr01\n- Status: {file_status}\n"
        )
        step = run_viewer.StepSummary(
            position=1,
            id6="intr01",
            setid="intr",
            action="execute",
            status=run_status,
            configured_file="",
            stem="20260908-intr-01-intr01-a-slug",
        )
        return step, run_viewer.audit_step_artifact(step, repo_root=root)

    def test_discover_and_resolve_runs(self):
        runs = run_viewer.discover_run_dirs(self.root)
        self.assertTrue(len(runs) > 0)
        self.assertTrue(all(r.is_dir() for r in runs))
        self.assertTrue(all(r.name.startswith("run-") for r in runs))

        # resolve empty matches all
        resolved = run_viewer.resolve_target_runs([], self.root)
        self.assertEqual(len(resolved), len(runs))

        # resolve by substring and setid
        resolved_sub = run_viewer.resolve_target_runs(["2367239"], self.root)
        self.assertEqual(len(resolved_sub), 1)
        self.assertIn("2367239", resolved_sub[0].name)
        resolved_set = run_viewer.resolve_target_runs(["runnernorm"], self.root)
        self.assertTrue(len(resolved_set) >= 1)

        # load summary state json
        summary = run_viewer.load_run_summary(resolved_sub[0], self.root)
        self.assertIsNotNone(summary)
        self.assertEqual(summary.run_id, "run-20260827T212958Z-2367239")
        self.assertEqual(summary.driver, "OpenCode")
        self.assertIn("runnernorm", summary.setids)
        self.assertEqual(len(summary.steps), 3)
        s1 = summary.steps[0]
        self.assertEqual(s1.id6, "ryvoi5")
        self.assertEqual(s1.status, "partial")
        self.assertEqual(s1.disposition, "dependency-blocked")
        self.assertTrue(len(s1.incomplete_requirements) > 0)
        s2 = summary.steps[1]
        self.assertEqual(s2.id6, "dg28i9")
        self.assertEqual(s2.status, "substantially-complete")
        self.assertEqual(s2.verification_status, "verified")

        # fallback execution-report.md
        with tempfile.TemporaryDirectory() as td:
            run_d = Path(td) / "run-20260825T000000Z-999999"
            run_d.mkdir()
            (run_d / "execution-report.md").write_text(
                "# Execution Report: run-20260825T000000Z-999999\n\n"
                "- Created: 2026-08-25T00:00:00+00:00\n"
                "- Updated: 2026-08-25T01:00:00+00:00\n"
                "- Selectors: `testset`\n\n"
                "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |\n"
                "|---:|---|---|---|---|---|---:|---|\n"
                "| 1 | `abc123` | `testset` | `execute` | executed | verified | 1 | `ses_123` |\n",
                encoding="utf-8",
            )
            fb_summary = run_viewer.load_run_summary(run_d, Path("."))
            self.assertIsNotNone(fb_summary)
            self.assertEqual(fb_summary.run_id, "run-20260825T000000Z-999999")
            self.assertEqual(len(fb_summary.steps), 1)
            self.assertEqual(fb_summary.steps[0].id6, "abc123")
            self.assertEqual(fb_summary.steps[0].status, "executed")
            self.assertEqual(fb_summary.steps[0].verification_status, "verified")

    def test_format_step_and_run_human(self):
        term = Term(color=False)
        step = run_viewer.StepSummary(
            position=1,
            id6="ryvoi5",
            setid="runnernorm",
            action="execute",
            status="partial",
            configured_file=".aw/records/plans/pending/20260825-runnernorm-00-ryvoi5-test.ipd.md",
            stem="20260825-runnernorm-00-ryvoi5",
            attempts_count=1,
            disposition="dependency-blocked",
            cost=12.3456,
            tokens={"total": 50000},
        )
        line = run_viewer.format_step_line(step, term)
        self.assertIn("fail-verify", line)
        self.assertIn("plan", line)
        self.assertIn("20260825-runnernorm-00-ryvoi5", line)
        self.assertIn("[attempts: 1]", line)
        self.assertIn("dependency-blocked", line)
        self.assertIn("[$12.35]", line)

        run_d = self._run_dir("run-20260827T212958Z-2367239")
        summary = run_viewer.load_run_summary(run_d, self.root)
        self.assertIsNotNone(summary)
        formatted = run_viewer.format_run_human(summary, term, detail=False)
        self.assertIn("run-20260827T212958Z-2367239", formatted)
        self.assertIn("[runnernorm]", formatted)
        self.assertIn("ryvoi5", formatted)
        self.assertIn("dg28i9", formatted)
        self.assertIn("puot79", formatted)

        formatted_detail = run_viewer.format_run_human(summary, term, detail=True)
        self.assertIn("! incomplete:", formatted_detail)
        self.assertIn("* summary:", formatted_detail)

        formatted_short = run_viewer.format_run_human(summary, term, short=True)
        self.assertIn("│ Status", formatted_short)
        self.assertIn("Landed", formatted_short)
        self.assertIn("Item", formatted_short)
        self.assertIn("Action", formatted_short)
        self.assertIn("Verified", formatted_short)
        self.assertNotIn("Attempts", formatted_short)
        self.assertNotIn("Total Cost", formatted_short)

        # with cost and token detail
        step1 = run_viewer.StepSummary(
            position=1,
            id6="abc123",
            setid="testset",
            action="execute",
            status="executed",
            configured_file="",
            stem="testset-abc123",
            cost=10.50,
            tokens={"total": 100000, "input": 80000, "output": 20000},
        )
        step2 = run_viewer.StepSummary(
            position=2,
            id6="def456",
            setid="testset",
            action="review",
            status="reviewed",
            configured_file="",
            stem="testset-def456",
            cost=5.25,
            tokens={"total": 50000, "input": 40000, "output": 10000},
        )
        run_with_cost = run_viewer.RunSummary(
            run_id="run-20260829T000000Z-111111",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00+00:00",
            setids=["testset"],
            steps=[step1, step2],
            counts={"executed": 1, "reviewed": 1},
            total_cost=15.75,
            total_tokens={"total": 150000, "input": 120000, "output": 30000},
        )
        formatted_cost = run_viewer.format_run_human(run_with_cost, term, detail=True)
        self.assertIn("$15.75", formatted_cost)
        self.assertIn("150.00K tok", formatted_cost)
        self.assertIn("$ cost: $10.50", formatted_cost)
        self.assertIn("* tokens: 100.00K tot", formatted_cost)

    def test_run_viewer_cli_target_human(self):
        ns = argparse.Namespace(
            dir=str(self.root),
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            short=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("run-20260827T212958Z-2367239", out)
        self.assertIn("runnernorm", out)

    def test_run_viewer_cli_flags_short_summary_latest(self):
        # short mode
        ns_short = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=True,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_short), 0)
        out = buf.getvalue()
        self.assertIn("Verified", out)
        self.assertNotIn("Total Tok", out)
        self.assertNotIn("Summary across", out)

        # summary_only mode on fixture with cost
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / ".aw" / "records" / "runs" / "run-20260829T000000Z-222222"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260829T000000Z-222222",
                "driver": "OpenCode",
                "queue": [
                    {
                        "position": 1,
                        "id6": "item01",
                        "setid": "test",
                        "action": "execute",
                        "status": "complete",
                        "disposition": "executed",
                        "configured_file": "",
                        "stem": "20260829-test-01-item01",
                        "attempts": [
                            {
                                "attempt": 1,
                                "cost": 1.25,
                                "tokens": {
                                    "total": 1000,
                                    "input": 600,
                                    "output": 300,
                                    "cache": 100,
                                },
                            }
                        ],
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state))

            ns_sum = argparse.Namespace(
                dir=str(root),
                target=[],
                set=None,
                ipd=None,
                status=None,
                failed=False,
                active=False,
                latest=False,
                last=2,
                since=None,
                detail=False,
                short=False,
                summary_only=True,
                latest_only=False,
                issues=False,
                json=False,
                agent=False,
                no_color=True,
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(run_viewer.run_viewer_cli(ns_sum), 0)
            out = buf.getvalue()
            self.assertIn("Summary across", out)
            self.assertIn("Breakdown by Status:", out)

        # conflict between short and summary_only
        ns_conflict = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=True,
            summary_only=True,
            latest_only=False,
            issues=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_conflict), 2)
        self.assertIn("cannot be used with", buf.getvalue())

        # latest_only
        ns_latest = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=5,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=True,
            issues=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_latest), 0)
        out = buf.getvalue()
        self.assertIn("Data from", out)
        self.assertIn("Verified", out)
        self.assertNotIn("Summary across", out)

        # conflict between summary_only and latest_only
        ns_latest_conf = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            latest_only=True,
            issues=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_latest_conf), 2)
        self.assertIn("cannot be used with --summary-only", buf.getvalue())

    def test_run_viewer_cli_formats_and_filters(self):
        # json mode
        ns_json = argparse.Namespace(
            dir=str(self.root),
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=None,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_json), 0)
        data = json.loads(buf.getvalue())
        self.assertIn("runs", data)
        self.assertEqual(len(data["runs"]), 1)
        self.assertEqual(data["runs"][0]["run_id"], "run-20260827T212958Z-2367239")

        # agent mode
        ns_agent = argparse.Namespace(
            dir=str(self.root),
            target=["run-20260827T212958Z-2367239"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=None,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=False,
            agent=True,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_agent), 0)
        lines = [line for line in buf.getvalue().strip().splitlines() if line]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["run_id"], "run-20260827T212958Z-2367239")

        # filters: status and set
        ns_filter = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set="runnernorm",
            ipd=None,
            status="partial",
            failed=False,
            active=False,
            latest=False,
            last=None,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_filter), 0)
        filt_data = json.loads(buf.getvalue())
        self.assertEqual(len(filt_data["runs"]), 1)
        self.assertEqual(filt_data["runs"][0]["run_id"], "run-20260827T212958Z-2367239")

        # aw cli entry point: aw runs
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli.main(["runs", "--dir", str(self.root), "--json", "2367239"])
        self.assertEqual(rc, 0)
        self.assertIn("2367239", buf.getvalue())

    def test_parse_since_timestamp_and_cli(self):
        fixed_now = datetime(2026, 8, 27, 19, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            run_viewer.parse_since_timestamp("1d", fixed_now),
            datetime(2026, 8, 26, 19, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            run_viewer.parse_since_timestamp("2h", fixed_now),
            datetime(2026, 8, 27, 17, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            run_viewer.parse_since_timestamp("1.5h", fixed_now),
            datetime(2026, 8, 27, 17, 30, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            run_viewer.parse_since_timestamp("1w", fixed_now),
            datetime(2026, 8, 20, 19, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            run_viewer.parse_since_timestamp("2026-08-29"),
            datetime(2026, 8, 29, 0, 0, 0, tzinfo=timezone.utc),
        )
        with self.assertRaises(ValueError):
            run_viewer.parse_since_timestamp("invalid-date")
        with self.assertRaises(ValueError):
            run_viewer.parse_since_timestamp("")

        # CLI since filter
        ns = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=None,
            since="2026-08-27T12:30:00+00:00",
            detail=False,
            short=False,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns), 0)
        data = json.loads(buf.getvalue())
        run_ids = [r["run_id"] for r in data["runs"]]
        self.assertIn("run-20260827T212958Z-2367239", run_ids)
        self.assertIn("run-20260828T000000Z-999999", run_ids)
        self.assertNotIn("run-20260827T212854Z-2364829", run_ids)

    def test_extract_log_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            log_p = Path(td) / "session.jsonl"
            # OpenCode step format
            lines = [
                json.dumps(
                    {
                        "type": "step_finish",
                        "part": {
                            "tokens": {
                                "input": 1000,
                                "output": 200,
                                "total": 1200,
                                "cache": {"read": 50, "write": 10},
                            },
                            "cost": 0.052,
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "step_finish",
                        "part": {
                            "tokens": {
                                "input": 2000,
                                "output": 300,
                                "total": 2300,
                                "cache": {"read": 100, "write": 20},
                            },
                            "cost": 0.098,
                        },
                    }
                ),
            ]
            log_p.write_text("\n".join(lines), encoding="utf-8")
            cost, toks = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost, 0.15)
            self.assertEqual(toks["total"], 3500)
            self.assertEqual(toks["input"], 3000)
            self.assertEqual(toks["output"], 500)
            self.assertEqual(toks["cache"], 180)

            # Antigravity format
            lines_ag = [
                json.dumps(
                    {
                        "event": "step_update",
                        "step_update": {
                            "step_index": 1,
                            "state": "DONE",
                            "step_type": "agent_response",
                            "usage": {
                                "input_tokens": 1000,
                                "output_tokens": 250,
                                "cache_read_tokens": 5000,
                                "thinking_tokens": 120,
                                "total_tokens": 1250,
                            },
                            "cost": 0.025,
                        },
                    }
                ),
                json.dumps(
                    {
                        "event": "step_update",
                        "step_update": {
                            "step_index": 2,
                            "state": "DONE",
                            "step_type": "agent_response",
                            "usage": {
                                "input_tokens": 2000,
                                "output_tokens": 300,
                                "cache_read_tokens": 4000,
                                "thinking_tokens": 80,
                                "total_tokens": 2300,
                            },
                            "cost": 0.050,
                        },
                    }
                ),
            ]
            log_p.write_text("\n".join(lines_ag), encoding="utf-8")
            cost_ag, toks_ag = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost_ag, 0.075)
            self.assertEqual(toks_ag["total"], 3550)
            self.assertEqual(toks_ag["input"], 3000)
            self.assertEqual(toks_ag["output"], 550)
            self.assertEqual(toks_ag["cache"], 9000)
            self.assertEqual(toks_ag["reasoning"], 200)

    def test_multi_run_summary_and_json(self):
        term = Term(color=False)
        step1 = run_viewer.StepSummary(
            position=1,
            id6="a1",
            setid="s1",
            action="execute",
            status="executed",
            configured_file="",
            stem="s1-a1",
            cost=10.00,
            tokens={"total": 100000},
            verification_status="verified",
        )
        step2 = run_viewer.StepSummary(
            position=2,
            id6="a2",
            setid="s1",
            action="execute",
            status="failed",
            configured_file="",
            stem="s1-a2",
            cost=5.00,
            tokens={"total": 50000},
            verification_status="failed",
        )
        run1 = run_viewer.RunSummary(
            run_id="run-1",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00+00:00",
            setids=["s1"],
            steps=[step1, step2],
            counts={"executed": 1, "failed": 1},
            total_cost=15.00,
            total_tokens={"total": 150000},
        )
        run2 = run_viewer.RunSummary(
            run_id="run-2",
            run_dir=Path("."),
            created_at="2026-08-29T01:00:00+00:00",
            setids=["s2"],
            steps=[],
            counts={"executed": 2},
            total_cost=20.00,
            total_tokens={"total": 200000},
        )
        multi = run_viewer.format_multi_run_summary([run1, run2], term)
        self.assertIn("Summary across 2 runs", multi)
        self.assertIn("Total Cost:   $15.00", multi)
        self.assertIn("Total Tokens: 150.00K", multi)
        self.assertIn("Breakdown by Status:", multi)
        self.assertIn("executed", multi)
        self.assertIn("failed", multi)

        # multi run cli json summary
        ns = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=2,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            latest_only=False,
            issues=False,
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns), 0)
        parsed = json.loads(buf.getvalue())
        self.assertIn("summary", parsed)
        self.assertEqual(parsed["summary"]["runs_count"], 2)
        self.assertIn("by_status", parsed["summary"])

    def test_runtime_and_pid_inspection(self):
        self.assertEqual(run_viewer.format_duration(None), "0s")
        self.assertEqual(run_viewer.format_duration(-5), "0s")
        self.assertEqual(run_viewer.format_duration(5.4), "5.4s")
        self.assertEqual(run_viewer.format_duration(125), "2m 05s")
        self.assertEqual(run_viewer.format_duration(3665), "1h 01m 05s")

        with tempfile.TemporaryDirectory() as td:
            rd = Path(td) / "run-20260829T100000Z-99999"
            rd.mkdir()
            (rd / "driver.lock").write_text(
                "pid=99999 started=2026-08-29T10:00:00+00:00"
            )
            (rd / "state.json").write_text(
                json.dumps({"updated_at": "2026-08-29T10:05:30+00:00"})
            )

            dt = datetime(2026, 8, 29, 10, 0, 0, tzinfo=timezone.utc)
            pid, pid_state, is_live, runtime_secs, runtime_str = (
                run_viewer.inspect_run_pid_and_runtime(
                    rd, "2026-08-29T10:00:00Z", "2026-08-29T10:05:30Z", dt
                )
            )
            self.assertEqual(pid, 99999)
            self.assertEqual(runtime_secs, 330.0)
            self.assertEqual(runtime_str, "5m 30s")

        term = Term(color=False)
        run = run_viewer.RunSummary(
            run_id="run-20260829T100000Z-12345",
            run_dir=Path("."),
            created_at="2026-08-29T10:00:00+00:00",
            setids=["myset"],
            steps=[],
            counts={"executed": 2},
            total_cost=5.50,
            total_tokens={
                "total": 50000,
                "input": 40000,
                "output": 10000,
                "cache": 30000,
            },
            pid=12345,
            pid_state="exited",
            is_live=False,
            runtime_seconds=125.0,
            runtime_str="2m 05s",
        )
        out = run_viewer.format_run_human(run, term)
        lines = out.splitlines()
        self.assertIn("run-20260829T100000Z-12345", lines[0])
        self.assertIn("pid: 12345 [exited]", lines[1])
        self.assertIn("runtime: 2m 05s", lines[1])

    def test_audit_step_artifact_and_verdicts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            pending_dir.mkdir(parents=True)
            executed_dir.mkdir(parents=True)

            p1 = pending_dir / "20260829-test-01-item01.ipd.md"
            p1.write_text("- Id: item01\n- Status: approved\n")
            p2 = executed_dir / "20260829-test-02-item02.ipd.md"
            p2.write_text("- Id: item02\n- Status: executed\n")

            st1 = run_viewer.StepSummary(
                position=1,
                id6="item01",
                setid="test",
                action="execute",
                status="executed",
                configured_file="",
                stem="20260829-test-01-item01",
            )
            st2 = run_viewer.StepSummary(
                position=2,
                id6="item02",
                setid="test",
                action="execute",
                status="executed",
                configured_file="",
                stem="20260829-test-02-item02",
            )
            st3 = run_viewer.StepSummary(
                position=3,
                id6="item03",
                setid="test",
                action="execute",
                status="queued",
                configured_file="",
                stem="20260829-test-03-item03",
            )

            a1 = run_viewer.audit_step_artifact(st1, repo_root=root)
            self.assertTrue(a1.location_mismatch)
            self.assertTrue(a1.status_mismatch)
            self.assertFalse(a1.missing_entirely)
            self.assertEqual(a1.actual_dir, "pending")
            self.assertEqual(a1.expected_dir, "executed")

            a2 = run_viewer.audit_step_artifact(st2, repo_root=root)
            self.assertFalse(a2.location_mismatch)
            self.assertFalse(a2.status_mismatch)
            self.assertFalse(a2.missing_entirely)

            a3 = run_viewer.audit_step_artifact(st3, repo_root=root)
            self.assertTrue(a3.missing_entirely)

            term = Term(color=False)
            sum_txt = run_viewer.format_artifact_audit_summary([a1, a2, a3], term)
            self.assertIn("Artifact & Status Differences", sum_txt)
            self.assertIn("Expected", sum_txt)
            self.assertIn("Actual", sum_txt)

            tbl = run_viewer.render_steps_table([st1, st2, st3], term, repo_root=root)
            self.assertIn("Issue", tbl)
            self.assertIn("YES", tbl)
            self.assertIn("no", tbl)

            st1_live = run_viewer.StepSummary(
                position=1,
                id6="item01",
                setid="test",
                action="execute",
                status="executed",
                configured_file="",
                stem="20260829-test-01-item01",
                is_live=True,
            )
            a1_live = run_viewer.audit_step_artifact(st1_live, repo_root=root)
            self.assertTrue(a1_live.is_live)
            sum_live_txt = run_viewer.format_artifact_audit_summary([a1_live], term)
            self.assertIn("[in flight]", sum_live_txt)
            tbl_live = run_viewer.render_steps_table([st1_live], term, repo_root=root)
            self.assertIn("YES (in flight)", tbl_live)

    def test_interrupted_discrepancy_and_sibling_statuses(self):
        # Case A: run interrupted + plan approved in pending -> no discrepancy
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            step, audit = self._interrupted_fixture(root, "approved", "pending")
            self.assertFalse(audit.missing_entirely)
            self.assertFalse(audit.location_mismatch)
            self.assertFalse(audit.status_mismatch)
            self.assertFalse(audit.has_discrepancy)
            self.assertEqual(run_viewer.step_issue_reasons(audit, step), [])
            self.assertFalse(run_viewer.step_has_issue(audit, step))

            term = Term(color=False)
            tbl = run_viewer.render_steps_table([step], term, repo_root=root)
            self.assertIn("Issue", tbl)
            self.assertNotIn("YES", tbl)

        # Case A breadth: tolerates in-flight statuses
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "plans" / "pending"
            d.mkdir(parents=True, exist_ok=True)
            for fstatus in (
                "approved",
                "to-review",
                "draft",
                "reviewed",
                "queued",
                "running",
            ):
                (d / "20260908-intr-02-intr02-a-slug.ipd.md").write_text(
                    f"# IPD: a slug\n\n- Id: intr02\n- Status: {fstatus}\n"
                )
                step = run_viewer.StepSummary(
                    position=1,
                    id6="intr02",
                    setid="intr",
                    action="execute",
                    status="interrupted",
                    configured_file="",
                    stem="20260908-intr-02-intr02-a-slug",
                )
                audit = run_viewer.audit_step_artifact(step, repo_root=root)
                self.assertFalse(audit.status_mismatch)
                self.assertFalse(audit.location_mismatch)

        # Case D: run interrupted + plan in executed -> flags both axes
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            step, audit = self._interrupted_fixture(root, "executed", "executed")
            self.assertFalse(audit.missing_entirely)
            self.assertTrue(audit.location_mismatch)
            self.assertTrue(audit.status_mismatch)
            self.assertTrue(audit.has_discrepancy)
            self.assertTrue(run_viewer.step_has_issue(audit, step))
            self.assertIn(
                "YES",
                run_viewer.render_steps_table(
                    [step], Term(color=False), repo_root=root
                ),
            )

        # Sibling terminal failure statuses remain status mismatches
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for run_status in (
                "failed",
                "failed-safely",
                "partial",
                "not-attempted",
                "merge-conflict",
                "cancelled",
            ):
                _step, audit = self._interrupted_fixture(
                    root, "approved", "pending", run_status=run_status
                )
                self.assertFalse(audit.location_mismatch)
                self.assertTrue(audit.status_mismatch)

    def test_run_viewer_cli_issues_flag(self):
        # 1. Populated issues case
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            pending_dir.mkdir(parents=True)
            p1 = pending_dir / "20260829-test-01-item01.ipd.md"
            p1.write_text("- Id: item01\n- Status: approved\n")

            run_dir = root / ".aw" / "records" / "runs" / "run-20260829T000000Z-111111"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260829T000000Z-111111",
                "queue": [
                    {
                        "position": 1,
                        "id6": "item01",
                        "setid": "test",
                        "action": "execute",
                        "status": "executed",
                        "configured_file": "",
                        "stem": "20260829-test-01-item01",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state))

            ns = argparse.Namespace(
                dir=str(root),
                target=[],
                set=None,
                ipd=None,
                status=None,
                failed=False,
                active=False,
                latest=False,
                last=1,
                since=None,
                detail=False,
                short=False,
                summary_only=False,
                latest_only=False,
                issues=True,
                json=False,
                agent=False,
                no_color=True,
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(run_viewer.run_viewer_cli(ns), 0)
            out = buf.getvalue()
            self.assertIn("Artifact & Status Differences", out)
            self.assertIn("20260829-test-01-item01", out)

        # 2. Empty state (clean repo)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            executed_dir.mkdir(parents=True)
            (executed_dir / "20260829-test-01-item01.ipd.md").write_text(
                "- Id: item01\n- Status: executed\n", encoding="utf-8"
            )

            run_dir = root / ".aw" / "records" / "runs" / "run-20260829T000000Z-111111"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260829T000000Z-111111",
                "queue": [
                    {
                        "position": 1,
                        "id6": "item01",
                        "setid": "test",
                        "action": "execute",
                        "status": "executed",
                        "configured_file": ".aw/records/plans/executed/20260829-test-01-item01.ipd.md",
                        "stem": "20260829-test-01-item01",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            ns_clean = argparse.Namespace(
                dir=str(root),
                target=[],
                set=None,
                ipd=None,
                status=None,
                failed=False,
                active=False,
                latest=False,
                last=1,
                since=None,
                detail=False,
                short=False,
                summary_only=False,
                latest_only=False,
                issues=True,
                json=False,
                agent=False,
                no_color=True,
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(run_viewer.run_viewer_cli(ns_clean), 0)
            self.assertEqual(
                buf.getvalue().strip(), "no artifact or status discrepancies found"
            )

        # 3. Conflict with summary_only
        ns_conf = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=1,
            since=None,
            detail=False,
            short=False,
            summary_only=True,
            latest_only=False,
            issues=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns_conf), 2)
        self.assertIn("cannot be used with --summary-only", buf.getvalue())


class UnresolvableTargetRefusalTests(TestCase):
    def test_unresolvable_target_refusal(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))

            # Near-miss leaf spelling
            out, err, code = _run_viewer(root, ["verify", _FIXTURE_RUN])
            self.assertEqual(code, 2, out + err)
            self.assertIn("verify", err)
            self.assertIn("verify-ledger", err)
            self.assertNotIn(_FIXTURE_RUN, out)

            # Wholly unknown token
            out, err, code = _run_viewer(root, ["totalgibberish"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", err)
            self.assertEqual(out, "")

            # Mixed resolvable and unresolvable
            out, err, code = _run_viewer(root, ["totalgibberish", _FIXTURE_RUN])
            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", err)
            self.assertNotIn(_FIXTURE_RUN, out)

            # Escape hatch with unresolvable target
            out, err, code = _run_viewer(root, ["--", "no-such-target-xyz"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("no-such-target-xyz", err)

            # Every unresolved token named
            out, err, code = _run_viewer(root, ["bogus-one", "bogus-two"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("bogus-one", err)
            self.assertIn("bogus-two", err)

            # Agent renderer refusal
            out, err, code = _run_viewer(root, ["totalgibberish", "--agent"])
            self.assertEqual(code, 2, out + err)
            record = json.loads(out.strip())
            self.assertEqual(record["schema"], "aw.agent/v1")
            self.assertEqual(record["kind"], "error")
            self.assertEqual(record["exit"], code)
            self.assertEqual(record["unresolved_targets"], ["totalgibberish"])

            # JSON renderer refusal
            out, err, code = _run_viewer(root, ["totalgibberish", "--json"])
            self.assertEqual(code, 2, out + err)
            rec_json = json.loads(out)
            self.assertEqual(rec_json["kind"], "error")
            self.assertEqual(rec_json["exit"], code)
            self.assertEqual(rec_json["unresolved_targets"], ["totalgibberish"])

    def test_resolvable_targets_and_flags_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            for argv in (
                [_FIXTURE_RUN],
                ["2367239"],
                [_FIXTURE_SETID],
                ["lanectn"],
                [str(root / ".aw" / "records" / "runs" / _FIXTURE_RUN)],
                [],
            ):
                with self.subTest(argv=argv):
                    out, err, code = _run_viewer(root, argv)
                    self.assertEqual(code, 0, out + err)

            for flag in (
                ["--last", "1"],
                ["--latest-only"],
                ["--issues"],
                ["--summary-only"],
                ["--short"],
                ["--detail"],
                ["--no-color"],
            ):
                with self.subTest(flag=flag):
                    out, err, code = _run_viewer(root, flag)
                    self.assertEqual(code, 0, out + err)

            # Empty repository is success
            with tempfile.TemporaryDirectory() as td_empty:
                out, err, code = _run_viewer(Path(td_empty), [])
                self.assertEqual(code, 0, out + err)

            # Filter excluding everything is success
            out, err, code = _run_viewer(root, ["--status", "no-such-status-xyz"])
            self.assertEqual(code, 0, out + err)

    def test_leaf_routing_and_legacy_refusals(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))

            # Colliding leaf name with hatch routes to target
            out, err, code = _run_viewer(root, ["--", "status"])
            self.assertEqual(code, 0, out + err)
            self.assertIn("3333333", out)

            # Bare leaf name routes to leaf command
            out, err, code = _run_viewer(Path("."), ["status"])
            self.assertNotEqual(code, 0)
            self.assertIn("target", (out + err).lower())
            self.assertNotIn("no run matched target", out + err)

            # Existing argument validation refusal preserved
            out, err, code = _run_viewer(root, ["--short", "--summary-only"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("cannot be used with", out + err)


class ResolverSetidNarrowingTests(TestCase):
    def test_resolver_setid_narrowing(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            # JSON keys and values do not resolve
            for token in (
                "opencode",
                "driver",
                "run_id",
                "options",
                "main",
                "clean",
                "execute",
                "complete",
                "queue",
            ):
                with self.subTest(token=token):
                    self.assertEqual(run_viewer.resolve_target_runs([token], root), [])

            # Real setids and substrings resolve
            self.assertEqual(
                len(run_viewer.resolve_target_runs([_FIXTURE_SETID], root)), 2
            )
            self.assertEqual(len(run_viewer.resolve_target_runs(["lanectn"], root)), 1)
            self.assertEqual(len(run_viewer.resolve_target_runs(["status"], root)), 1)
            resolved = run_viewer.resolve_target_runs(["2367239"], root)
            self.assertEqual(len(resolved), 1)
            self.assertIn("2367239", resolved[0].name)

        # Empty queue with selectors resolves
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "runs" / "run-20260905T000000Z-4444444"
            d.mkdir(parents=True)
            (d / "state.json").write_text(
                json.dumps({"run_id": d.name, "selectors": ["emptyset"], "queue": []}),
                encoding="utf-8",
            )
            self.assertEqual(len(run_viewer.resolve_target_runs(["emptyset"], root)), 1)

    def test_detailed_resolver_and_error_handling(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                [_FIXTURE_RUN], root
            )
            self.assertEqual(len(runs), 1)
            self.assertEqual(unresolved, [])

            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                ["totalgibberish"], root
            )
            self.assertEqual(runs, [])
            self.assertEqual(unresolved, ["totalgibberish"])

            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                ["totalgibberish", _FIXTURE_RUN], root
            )
            self.assertEqual(len(runs), 1)
            self.assertEqual(unresolved, ["totalgibberish"])

            runs, unresolved = run_viewer.resolve_target_runs_detailed([], root)
            self.assertEqual(len(runs), 4)
            self.assertEqual(unresolved, [])

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "runs" / "run-20260905T000000Z-5555555"
            d.mkdir(parents=True)
            (d / "state.json").write_text("{not json at all", encoding="utf-8")
            self.assertEqual(run_viewer.resolve_target_runs(["anything"], root), [])


class RunsRepairHelpTests(TestCase):
    def test_runs_repair_cli_help_and_execution(self):
        # --help and -h
        for flag in ("--help", "-h"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(cli.main(["runs", "repair", flag]), 0)
            out = buf.getvalue()
            self.assertIn("usage: aw runs repair", out)
            self.assertIn("executed", out)
            self.assertIn("interrupted", out)

        # runs --help advertises repair
        buf = io.StringIO()
        with self.assertRaises(SystemExit):
            with redirect_stdout(buf):
                cli.main(["runs", "--help"])
        self.assertIn("repair", buf.getvalue())

        # repair without target errors with exit 2
        ns = argparse.Namespace(
            dir=".",
            target=["repair"],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=1,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=False,
            issues=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(run_viewer.run_viewer_cli(ns), 2)
        self.assertIn("needs a run id", buf.getvalue())

        # non-run dir exits 2
        with tempfile.TemporaryDirectory() as td:
            code, message = run_viewer.repair_run(Path(td), Path(td))
            self.assertEqual(code, 2)
            self.assertIn("not a run directory", message)

        # no-op when nothing running
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / ".aw" / "records" / "runs" / "run-20260829T000000Z-222222"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260829T000000Z-222222",
                "repo": str(root),
                "queue": [
                    {
                        "position": 1,
                        "id6": "item01",
                        "setid": "test",
                        "action": "execute",
                        "status": "complete",
                        "configured_file": "x.ipd.md",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
            code, message = run_viewer.repair_run(run_dir, root)
            self.assertEqual(code, 0)
            self.assertIn("nothing to repair", message)

        # refuses unresolvable target and works on resolvable target
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["repair", "totalgibberish"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", out + err)

            out, err, code = _run_viewer(root, ["repair", _FIXTURE_RUN])
            self.assertEqual(code, 0, out + err)
            self.assertIn("nothing to repair", out)

    def test_step_elapsed_duration_and_rendering(self):
        # format_step_duration
        self.assertEqual(run_viewer.format_step_duration(None), "-")
        self.assertEqual(run_viewer.format_step_duration(-5.0), "-")
        self.assertEqual(run_viewer.format_step_duration(0), "00:00:00")
        self.assertEqual(run_viewer.format_step_duration(45), "00:00:45")
        self.assertEqual(run_viewer.format_step_duration(1167), "00:19:27")
        self.assertEqual(run_viewer.format_step_duration(10479), "02:54:39")
        self.assertEqual(run_viewer.format_step_duration(97676), "1d 03:07:56")

        # extract_step_elapsed
        sec, text = run_viewer.extract_step_elapsed({})
        self.assertIsNone(sec)
        self.assertIsNone(text)

        item = {
            "attempts": [
                {
                    "attempt": 1,
                    "started_at": "2026-09-05T21:10:20Z",
                    "ended_at": "2026-09-05T21:29:47Z",
                }
            ]
        }
        sec, text = run_viewer.extract_step_elapsed(item)
        self.assertEqual(sec, 1167.0)
        self.assertEqual(text, "00:19:27")

        item_multi = {
            "attempts": [
                {
                    "attempt": 1,
                    "started_at": "2026-09-05T20:00:00+00:00",
                    "interrupted_at": "2026-09-05T20:10:00+00:00",
                },
                {
                    "attempt": 2,
                    "started_at": "2026-09-05T20:15:00+00:00",
                    "ended_at": "2026-09-05T20:25:30+00:00",
                },
            ]
        }
        sec_m, text_m = run_viewer.extract_step_elapsed(item_multi)
        self.assertEqual(sec_m, 1230.0)
        self.assertEqual(text_m, "00:20:30")

        now_mock = datetime(2026, 9, 5, 21, 30, 0, tzinfo=timezone.utc)
        item_live = {"attempts": [{"attempt": 1, "started_at": "2026-09-05T21:15:41Z"}]}
        sec_live, text_live = run_viewer.extract_step_elapsed(
            item_live, is_live=True, now=now_mock
        )
        self.assertEqual(sec_live, 859.0)
        self.assertEqual(text_live, "00:14:19")

        # render steps table and details
        term = Term(color=False)
        st1 = run_viewer.StepSummary(
            position=1,
            id6="step01",
            setid="test",
            action="execute",
            status="executed",
            configured_file="",
            stem="20260905-test-01-step01",
            attempts_count=1,
            elapsed_seconds=1167.0,
            elapsed_str="00:19:27",
        )
        st2 = run_viewer.StepSummary(
            position=2,
            id6="step02",
            setid="test",
            action="execute",
            status="queued",
            configured_file="",
            stem="20260905-test-02-step02",
            attempts_count=0,
            elapsed_seconds=None,
            elapsed_str=None,
        )
        tbl = run_viewer.render_steps_table([st1, st2], term)
        self.assertIn("Elapsed", tbl)
        self.assertIn("00:19:27", tbl)
        tbl_short = run_viewer.render_steps_table([st1, st2], term, short=True)
        self.assertNotIn("Elapsed", tbl_short)

        details = run_viewer.render_step_details([st1], term)
        self.assertTrue(any("elapsed: 00:19:27" in d for d in details))


class AnalyticsIsolationTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.runs_dir = self.root / ".aw" / "records" / "runs"
        self.runs_dir.mkdir(parents=True)
        self.run_1 = self.runs_dir / "run-20260901T000000Z-1"
        self.run_1.mkdir()
        (self.run_1 / "state.json").write_text(
            json.dumps({"run_id": self.run_1.name, "setid": "realset1"}),
            encoding="utf-8",
        )
        self.run_2 = self.runs_dir / "run-20260902T000000Z-2"
        self.run_2.mkdir()
        (self.run_2 / "state.json").write_text(
            json.dumps({"run_id": self.run_2.name, "setid": "realset2"}),
            encoding="utf-8",
        )

        self.analytics_dir = self.runs_dir / "analytics"
        self.snap_run = self.analytics_dir / "snapshots" / "run-20260903T000000Z-9"
        self.snap_run.mkdir(parents=True)
        (self.snap_run / "state.json").write_text(
            json.dumps({"run_id": self.snap_run.name, "setid": "analyticsset"}),
            encoding="utf-8",
        )
        (self.snap_run / "events.jsonl").write_text("{}", encoding="utf-8")
        (self.snap_run / "execution-report.md").write_text("# Report", encoding="utf-8")

        self.legacy_aw = self.root / ".aw" / "runs" / "run-20260904T000000Z-3"
        self.legacy_aw.mkdir(parents=True)
        (self.legacy_aw / "state.json").write_text(
            json.dumps({"run_id": self.legacy_aw.name}), encoding="utf-8"
        )

        self.legacy_agents = self.root / ".agents" / "runs" / "run-20260905T000000Z-4"
        self.legacy_agents.mkdir(parents=True)
        (self.legacy_agents / "state.json").write_text(
            json.dumps({"run_id": self.legacy_agents.name}), encoding="utf-8"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discover_run_dirs_excludes_analytics_and_preserves_order(self):
        found = run_viewer.discover_run_dirs(self.root)
        found_names = [p.name for p in found]
        self.assertIn("run-20260901T000000Z-1", found_names)
        self.assertIn("run-20260902T000000Z-2", found_names)
        self.assertIn("run-20260904T000000Z-3", found_names)
        self.assertIn("run-20260905T000000Z-4", found_names)
        self.assertNotIn("run-20260903T000000Z-9", found_names)
        self.assertNotIn("analytics", found_names)
        self.assertEqual(
            found, [self.run_1, self.run_2, self.legacy_aw, self.legacy_agents]
        )

    def test_analytics_isolation_and_rejections(self):
        # directory target
        resolved = run_viewer.resolve_target_runs([str(self.snap_run)], self.root)
        self.assertEqual(resolved, [])
        resolved_dirs, unresolved = run_viewer.resolve_target_runs_detailed(
            [str(self.snap_run)], self.root
        )
        self.assertEqual(resolved_dirs, [])
        self.assertEqual(unresolved, [str(self.snap_run)])

        # file targets
        for fname in ("state.json", "events.jsonl", "execution-report.md"):
            file_target = self.snap_run / fname
            self.assertEqual(
                run_viewer.resolve_target_runs([str(file_target)], self.root), []
            )

        # format unresolvable target message
        msg = run_viewer.format_unresolvable_target_message(
            [str(self.snap_run)], repo_root=self.root
        )
        self.assertIn("error: no run matched target", msg)
        self.assertIn("reserved analytics tree", msg)

        # resolve_ledger_path rejects analytics
        from agent_workflows.run_cli import resolve_ledger_path

        snap_ledger = self.snap_run / "ledger.jsonl"
        snap_ledger.write_text("{}", encoding="utf-8")
        self.assertIsNone(resolve_ledger_path(str(snap_ledger), self.root))


class SharedLifecycleRenderingTests(TestCase):
    @staticmethod
    def _step(status, *, action="execute", disposition=None, verification=None):
        return run_viewer.StepSummary(
            position=1,
            id6="zzz999",
            setid="demo",
            action=action,
            status=status,
            configured_file=".aw/records/plans/pending/x.ipd.md",
            stem="demo-zzz999",
            disposition=disposition,
            verification_status=verification,
        )

    @staticmethod
    def _term(color=True):
        return Term(color=color, unicode=True, depth="256" if color else None)

    def test_section_7_2_statuses_and_badges_render_proper_lifecycle(self):
        cases = (
            ("executed", "\u2713", "1;38;5;46"),
            ("verified", "\u2713", "1;38;5;46"),
            ("ran", "\u21a9\ufe0e", "1;38;5;220"),
            ("unknown_outcome", "\u2718", "1;38;5;196"),
            ("fail-verify", "\u2718", "1;38;5;196"),
            ("interrupted", "\u21a9\ufe0e", "1;38;5;220"),
            ("fail-gate", "\u26a0\ufe0e", "1;38;5;208"),
            ("failed", "\u2718", "1;38;5;196"),
            ("queued", "\u25d5", "1;38;5;45"),
            ("needs_input", "\u2026", "1;38;5;214"),
            ("not-run", "\u2205", "38;5;244"),
        )
        term = self._term()
        for status, glyph, sgr in cases:
            with self.subTest(status=status):
                line = run_viewer.format_step_line(self._step(status), term)
                self.assertIn(f"\033[{sgr}m{glyph}\033[0m", line)
                self.assertIn(f"\033[{sgr}m{status}\033[0m", line)

        # ran and unknown_outcome are never styled as success (green 46)
        for st in ("ran", "unknown_outcome"):
            line = run_viewer.format_step_line(self._step(st), term)
            self.assertNotIn("38;5;46", line)

        # review and verification badges
        review_line = run_viewer.format_step_line(
            self._step("executed", action="review"), term
        )
        self.assertIn("\033[1;38;5;220m[review]\033[0m", review_line)

        ok_badge = run_viewer.format_step_line(
            self._step("executed", verification="verified"), term
        )
        self.assertIn("\033[1;38;5;46m[verified]\033[0m", ok_badge)
        bad_badge = run_viewer.format_step_line(
            self._step("failed", verification="failed"), term
        )
        self.assertIn("\033[1;38;5;196m[verify-failed]\033[0m", bad_badge)

        # disposition sharing shared vocabulary
        disp_line = run_viewer.format_step_line(
            self._step("fail-verify", disposition="fail-depend"), term
        )
        self.assertIn("\033[1;38;5;208mfail-depend\033[0m", disp_line)

        # color off has no ANSI
        term_no_color = self._term(color=False)
        for st in ("executed", "ran", "fail-gate", "unknown_outcome"):
            line = run_viewer.format_step_line(self._step(st), term_no_color)
            self.assertNotIn("\033", line)
            self.assertIn(st, line)

        # variation selector survives rendering
        for st, gr in (("fail-gate", "\u26a0\ufe0e"), ("ran", "\u21a9\ufe0e")):
            line = run_viewer.format_step_line(self._step(st), term)
            self.assertIn(gr, line)
            self.assertNotIn("\u26a0\ufe0f", line)
            self.assertNotIn("\u21a9\ufe0f", line)

        # machine modes emit no ANSI
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _build_viewer_fixture(root)
            for flag in ("--agent", "--json"):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    cli.main(["runs", "--dir", str(root), flag])
                self.assertNotIn("\033", buf.getvalue())

    def test_running_actions_and_step_line_formatting(self):
        term = self._term()
        # action-aware activity
        rev = run_viewer.format_step_line(self._step("running", action="review"), term)
        self.assertIn("\033[1;38;5;220m\u25ce\033[0m", rev)
        exe = run_viewer.format_step_line(self._step("running", action="execute"), term)
        self.assertIn("\033[1;38;5;220m\u25b6\033[0m", exe)

        # unmapped action falls back to active
        plan_line = run_viewer.format_step_line(
            self._step("running", action="plan"), term
        )
        self.assertIn("\033[1;38;5;220m\u25cf\033[0m", plan_line)

        # artifact type word carries no escape
        line_type = run_viewer.format_step_line(self._step("executed"), term)
        self.assertIn("plan", line_type)
        self.assertNotIn("\033[1;38;5;33mplan", line_type)

        # cost badge stays generic
        step_cost = self._step("executed")
        step_cost.cost = 1.25
        line_cost = run_viewer.format_step_line(step_cost, term)
        self.assertIn("\033[38;5;220m[$1.25]\033[0m", line_cost)

        # glyph pads by visible width
        from agent_workflows.term import visible_width

        term_plain = self._term(color=False)
        widths = set()
        for status in ("blocked", "ran", "executed", "queued", "needs_input"):
            line = run_viewer.format_step_line(self._step(status), term_plain)
            widths.add(visible_width(line[: line.index("plan")]))
        self.assertEqual(len(widths), 1)

        # audit and analytics tables share vocabulary
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rd = root / ".aw" / "records" / "runs" / "run-20260920T120000Z-4242"
            rd.mkdir(parents=True)
            queue = [
                {
                    "position": 1,
                    "id6": "aaa111",
                    "setid": "demo",
                    "action": "execute",
                    "status": "ran",
                },
                {
                    "position": 2,
                    "id6": "bbb222",
                    "setid": "demo",
                    "action": "execute",
                    "status": "unknown_outcome",
                },
            ]
            (rd / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": rd.name,
                        "created_at": "2026-09-20T12:00:00+00:00",
                        "updated_at": "2026-09-20T12:30:00+00:00",
                        "driver": {"path": "agent_workflows/oc_runipd.py"},
                        "queue": queue,
                    }
                ),
                encoding="utf-8",
            )
            summary = run_viewer.load_run_summary(rd, root)
            self.assertIsNotNone(summary)
            out = run_viewer.format_run_human(
                summary, self._term(), short=True, repo_root=root
            )
            self.assertIn("\033[1;38;5;220mran\033[0m", out)
            self.assertIn("\033[1;38;5;196munknown_outcome\033[0m", out)


# ==================================================================================================
# runrecon-02 (`fduoj4`) E-04: read surface reports projected status without mutating
# ==================================================================================================


def _abandoned_run_fixture(
    root: Path, *, outcome: Any = None, action: str = "execute"
) -> Path:
    run_id = "run-20260902T013603Z-1758564"
    d = root / ".aw" / "records" / "runs" / run_id
    (d / "outcomes").mkdir(parents=True, exist_ok=True)
    if outcome is not None:
        (d / "outcomes" / "02-97df1z.json").write_text(
            json.dumps(outcome), encoding="utf-8"
        )
    (d / "state.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "repo": str(root),
                "created_at": "2026-09-02T01:36:03+00:00",
                "updated_at": "2026-09-02T01:36:03+00:00",
                "queue": [
                    {
                        "position": 2,
                        "id6": "97df1z",
                        "setid": "e32j35",
                        "action": action,
                        "status": "running",
                        "configured_file": ".aw/records/plans/pending/20260902-e32j35-02-97df1z-x.ipd.md",
                        "last_outcome": None,
                        "attempts": [{"number": 1, "log": None}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return d


def _only_step(run_dir: Path, root: Path) -> run_viewer.StepSummary:
    summary = run_viewer.load_run_summary(run_dir, root)
    assert summary is not None
    return summary.steps[0]


_RECORDED = {
    "disposition": "substantially-complete",
    "summary": "aw ipd lint --phase pre-transition reports conforming",
    "commits": ["209227d54f1fd7e34115ee9a198c74513a99567d"],
    "pushed": False,
}


class ProjectedStatusReadsTheRecordedOutcomeTests(TestCase):
    def test_projected_status_from_outcome_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = _abandoned_run_fixture(root, outcome=_RECORDED)
            summary = run_viewer.load_run_summary(d, root)
            assert summary is not None
            step = summary.steps[0]
            self.assertEqual(step.status, "fail-gate?")
            self.assertEqual(step.persisted_status, "running")
            self.assertTrue(step.is_projected)
            self.assertTrue(step.status.endswith(run_viewer.PROJECTION_SUFFIX))
            self.assertEqual(summary.counts, {"fail-gate?": 1})

            # Read path writes nothing
            state_file = d / "state.json"
            before_bytes = state_file.read_bytes()
            before_mtime = state_file.stat().st_mtime_ns
            run_viewer.load_run_summary(d, root)
            self.assertEqual(state_file.read_bytes(), before_bytes)
            self.assertEqual(state_file.stat().st_mtime_ns, before_mtime)

        # Step with no recorded outcome reads abandoned
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = _abandoned_run_fixture(root, outcome=None)
            self.assertEqual(_only_step(d, root).status, run_viewer.ABANDONED)

        # Self-claimed executed is downgraded to fail-gate?
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = _abandoned_run_fixture(root, outcome={"disposition": "executed"})
            self.assertEqual(_only_step(d, root).status, "fail-gate?")

    def test_projected_status_action_gates(self):
        for action in ("review", "orchestrate"):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                d = _abandoned_run_fixture(root, outcome=_RECORDED, action=action)
                self.assertEqual(_only_step(d, root).status, run_viewer.ABANDONED)


class RepairReportsRecoveredProvenanceTests(TestCase):
    def test_repair_reports_recovered_provenance_and_help(self):
        from agent_workflows import runner_shared

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = _abandoned_run_fixture(root, outcome=_RECORDED)
            code, message = run_viewer.repair_run(d, root)
            self.assertEqual(code, 0)
            self.assertIn("97df1z running -> fail-gate", message)
            self.assertIn(runner_shared.RECOVERED_FROM_OUTCOME, message)
            self.assertIn("209227d54f1fd7e34115ee9a198c74513a99567d", message)
            self.assertIn("unresolved here", message)

            persisted = json.loads((d / "state.json").read_text(encoding="utf-8"))
            item = persisted["queue"][0]
            self.assertEqual(item["status"], "fail-gate")
            self.assertEqual(
                item[runner_shared.RECOVERY_PROVENANCE_KEY],
                runner_shared.RECOVERED_FROM_OUTCOME,
            )

        # Repair with no outcome reconciles to interrupted
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = _abandoned_run_fixture(root, outcome=None)
            code, message = run_viewer.repair_run(d, root)
            self.assertEqual(code, 0)
            self.assertIn("97df1z running -> interrupted", message)
            self.assertNotIn("recovered-from-outcome", message)

        # Repair help text checks
        help_text = run_viewer.REPAIR_HELP
        self.assertNotIn("not the step's own", help_text)
        self.assertNotIn("ydbhfd", help_text)
        self.assertIn("outcomes/<NN>-<id6>.json", help_text)
        self.assertIn("recovered-from-outcome", help_text)
        self.assertIn("downgraded to `substantially-complete`", help_text)
        for dash in ("\u2014", "\u2013"):
            self.assertNotIn(dash, help_text)
