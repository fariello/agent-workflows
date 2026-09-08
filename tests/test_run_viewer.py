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
from unittest import TestCase

from agent_workflows import cli, run_viewer
from agent_workflows.term import Term

# --------------------------------------------------------------------------------------------------
# Fixture helpers for the unresolvable-target refusal (runsverify 7wei1o E-05)
#
# FIXTURE-BASED ON PURPOSE. Per this module's header hazard, a new test must NOT read the live
# repository via `dir="."`: `.aw/records/runs/` is gitignored and absent in every fresh checkout and
# in every isolated lane worktree the runner allocates by default, so a refusal test keyed to live
# run records would be unrunnable exactly where it is actually run.
# --------------------------------------------------------------------------------------------------

#: A resolvable run id in the fixture below. Its trailing digits double as the substring-match case.
_FIXTURE_RUN = "run-20260901T000000Z-2367239"
#: A Set the fixture declares (two runs carry it), i.e. the legitimate setid-resolution case.
_FIXTURE_SETID = "runnernorm"


def _build_viewer_fixture(root: Path) -> Path:
    """Write four driver run records under ``root``, then return ``root``.

    Shaped to carry all four resolution cases the refusal must tell apart: two real Set ids, a run-id
    substring, a leaf-name COLLISION (a Set genuinely named ``status``, which no real set id
    collides with, so it must be constructed), and ordinary JSON keys/values (``driver``, ``options``,
    ``run_id``, ``main``, ``clean``) that the resolver's old raw-substring fallback over-matched.
    """
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
                    # Ordinary JSON keys/values. Every one of these strings is a token the old
                    # fallback matched by raw substring, resolving it to effectively every run.
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
    """Invoke `aw runs` through the REAL cli entry point. Returns ``(stdout, stderr, rc)``.

    Captures the streams SEPARATELY because the refusal's human message goes to stderr on purpose
    (so it never lands in a report a caller is parsing on stdout), and a combined capture could not
    tell the two apart.
    """
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = cli.main(["runs", "--dir", str(root), *argv])
    except SystemExit as exc:  # argparse usage errors exit rather than return
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

    def test_discover_run_dirs(self):
        runs = run_viewer.discover_run_dirs(self.root)
        self.assertTrue(len(runs) > 0)
        self.assertTrue(all(r.is_dir() for r in runs))
        self.assertTrue(all(r.name.startswith("run-") for r in runs))

    def test_resolve_target_runs_empty(self):
        all_runs = run_viewer.discover_run_dirs(self.root)
        resolved = run_viewer.resolve_target_runs([], self.root)
        self.assertEqual(len(resolved), len(all_runs))

    def test_resolve_target_runs_by_substring_and_setid(self):
        resolved = run_viewer.resolve_target_runs(["2367239"], self.root)
        self.assertEqual(len(resolved), 1)
        self.assertIn("2367239", resolved[0].name)

        # Match by setid
        resolved_set = run_viewer.resolve_target_runs(["runnernorm"], self.root)
        self.assertTrue(len(resolved_set) >= 1)

    def test_load_run_summary_state_json(self):
        runs = run_viewer.resolve_target_runs(["2367239"], self.root)
        self.assertEqual(len(runs), 1)
        summary = run_viewer.load_run_summary(runs[0], self.root)
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

    def test_load_run_summary_fallback_report_md(self, tmp_path_factory=None):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            run_d = Path(td) / "run-20260825T000000Z-999999"
            run_d.mkdir()
            report = run_d / "execution-report.md"
            report.write_text(
                "# Execution Report: run-20260825T000000Z-999999\n\n"
                "- Created: 2026-08-25T00:00:00+00:00\n"
                "- Updated: 2026-08-25T01:00:00+00:00\n"
                "- Selectors: `testset`\n\n"
                "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |\n"
                "|---:|---|---|---|---|---|---:|---|\n"
                "| 1 | `abc123` | `testset` | `execute` | executed | verified | 1 | `ses_123` |\n",
                encoding="utf-8",
            )
            summary = run_viewer.load_run_summary(run_d, Path("."))
            self.assertIsNotNone(summary)
            self.assertEqual(summary.run_id, "run-20260825T000000Z-999999")
            self.assertEqual(len(summary.steps), 1)
            self.assertEqual(summary.steps[0].id6, "abc123")
            self.assertEqual(summary.steps[0].status, "executed")
            self.assertEqual(summary.steps[0].verification_status, "verified")

    def test_format_step_line(self):
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
        )
        line = run_viewer.format_step_line(step, term)
        self.assertIn("partial", line)
        self.assertIn("plan", line)
        self.assertIn("20260825-runnernorm-00-ryvoi5", line)
        self.assertIn("[attempts: 1]", line)
        self.assertIn("dependency-blocked", line)

    def test_format_run_human(self):
        term = Term(color=False)
        run_d = self._run_dir("run-20260827T212958Z-2367239")
        summary = run_viewer.load_run_summary(run_d, self.root)
        self.assertIsNotNone(summary)
        formatted = run_viewer.format_run_human(summary, term, detail=False)
        self.assertIn("run-20260827T212958Z-2367239", formatted)
        self.assertIn("[runnernorm]", formatted)
        self.assertIn("ryvoi5", formatted)
        self.assertIn("dg28i9", formatted)
        self.assertIn("puot79", formatted)

        # Test detail mode
        formatted_detail = run_viewer.format_run_human(summary, term, detail=True)
        self.assertIn("! incomplete:", formatted_detail)
        self.assertIn("* summary:", formatted_detail)

        # Test short mode
        formatted_short = run_viewer.format_run_human(summary, term, short=True)
        self.assertIn("│ Status", formatted_short)
        self.assertIn("Item", formatted_short)
        self.assertIn("Action", formatted_short)
        self.assertIn("Verified", formatted_short)
        self.assertNotIn("Attempts", formatted_short)
        self.assertNotIn("Total Cost", formatted_short)
        self.assertNotIn("Total Tok", formatted_short)

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

    def test_run_viewer_cli_short(self):
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
            short=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Verified", out)
        self.assertNotIn("Total Tok", out)
        self.assertNotIn("Summary across", out)
        self.assertNotIn("Breakdown by Status:", out)

    def test_run_viewer_cli_summary_only(self):
        """`--summary-only` renders the aggregate tables, asserted on an OWNED fixture.

        This test used to run against the LIVE repository (`dir="."`, `last=2`) and asserted
        `Breakdown by Status:` unconditionally. That is two separate dependencies on ambient state,
        and both bite:

        * `Breakdown by Status:` is emitted ONLY when the selected runs carry cost/token data
          (`run_viewer.py:2215-2216` prints `No recorded cost/token data for the selected runs.`
          instead). Whether the two most recent runs happen to have cost data is not a property of
          this code, so the assertion passed or failed depending on what the maintainer had last run.
          Measured: with a live `aw oc run revsweep` in progress, the two newest runs had no cost
          data and this test failed.
        * `dir="."` resolves a DIFFERENT `.aw/state` inside a git worktree, where `discover_run_dirs`
          returns 0 runs (backlog `dh0uno`), which is why this class contributes ~14 phantom failures
          to any worktree run.

        Fixed the way `i79rgh` already fixed the `--issues` cases in this same file: build a run
        fixture in a tempdir, WITH cost data, so the assertion tests the renderer rather than the
        maintainer's recent activity.
        """
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
                        # Cost/token data is what gates the aggregate tables; without it the
                        # renderer takes the "No recorded cost/token data" branch by design.
                        # It is read from ATTEMPTS (`run_viewer.py:597-604`), not from a
                        # top-level key, so the fixture must carry an attempt record.
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

            ns = argparse.Namespace(
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
                code = run_viewer.run_viewer_cli(ns)
            self.assertEqual(code, 0)
            out = buf.getvalue()
            self.assertIn("Summary across", out)
            self.assertIn("Breakdown by Status:", out)
            self.assertNotIn("pid:", out)

    def test_run_viewer_cli_short_and_summary_only_conflict(self):
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
            short=True,
            summary_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn("error: --summary-only/-S cannot be used with --short/-s", out)

    def test_run_viewer_cli_latest_only(self):
        ns = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            last=3,
            since=None,
            detail=False,
            short=False,
            summary_only=False,
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("Data from", out)
        self.assertIn("Verified", out)
        self.assertNotIn("Summary across", out)

    def test_run_viewer_cli_latest_only_single_run(self):
        ns = argparse.Namespace(
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
            summary_only=False,
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("run-", out)
        self.assertNotIn("Data from", out)

    def test_run_viewer_cli_latest_only_conflict(self):
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
            latest_only=True,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn(
            "error: --latest-only/-L cannot be used with --summary-only/-S", out
        )

    def test_run_viewer_cli_json(self):
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
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        parsed = json.loads(buf.getvalue())
        self.assertIn("runs", parsed)
        self.assertEqual(len(parsed["runs"]), 1)
        self.assertEqual(parsed["runs"][0]["run_id"], "run-20260827T212958Z-2367239")

    def test_run_viewer_cli_agent(self):
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
            json=False,
            agent=True,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        lines = [line for line in buf.getvalue().strip().splitlines() if line]
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["run_id"], "run-20260827T212958Z-2367239")

    def test_run_viewer_cli_filters(self):
        # Filter by set
        ns = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set="ipddeps",
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("ipddeps", out)

        # Filter by status
        ns_st = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status="partial",
            failed=False,
            active=False,
            latest=False,
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns_st)
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("partial", out)

    def test_aw_cli_entry_points(self):
        # aw runs --last
        buf = io.StringIO()
        with redirect_stdout(buf):
            try:
                cli.main(["runs", "--dir", str(self.root), "--last", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf.getvalue())

        # aw runs -l
        buf_l = io.StringIO()
        with redirect_stdout(buf_l):
            try:
                cli.main(["runs", "--dir", str(self.root), "-l", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf_l.getvalue())

        # aw runs -l 2
        buf_l2 = io.StringIO()
        with redirect_stdout(buf_l2):
            try:
                cli.main(["runs", "--dir", str(self.root), "-l", "2", "--json"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data_l2 = json.loads(buf_l2.getvalue())
        self.assertLessEqual(len(data_l2["runs"]), 2)

        # aw runs --last 2
        buf_n = io.StringIO()
        with redirect_stdout(buf_n):
            try:
                cli.main(["runs", "--dir", str(self.root), "--last", "2", "--json"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data = json.loads(buf_n.getvalue())
        self.assertLessEqual(len(data["runs"]), 2)

        # aw runs --latest (backwards-compat)
        buf_compat = io.StringIO()
        with redirect_stdout(buf_compat):
            try:
                cli.main(["runs", "--dir", str(self.root), "--latest", "--no-color"])
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf_compat.getvalue())

        # aw run list --last
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            try:
                cli.main(
                    ["runs", "list", "--dir", str(self.root), "--last", "--no-color"]
                )
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        self.assertIn("run-", buf2.getvalue())

        # aw run list --last 2
        buf3 = io.StringIO()
        with redirect_stdout(buf3):
            try:
                cli.main(
                    ["runs", "list", "--dir", str(self.root), "--last", "2", "--json"]
                )
            except SystemExit as exc:
                self.assertEqual(exc.code, 0)
        data3 = json.loads(buf3.getvalue())
        self.assertLessEqual(len(data3["runs"]), 2)

        # aw runs --last 0 (validation error)
        with redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exc_ctx:
                cli.main(["runs", "--dir", str(self.root), "--last", "0"])
            self.assertEqual(exc_ctx.exception.code, 2)

    def test_parse_since_timestamp_relative(self):
        from datetime import datetime, timezone

        fixed_now = datetime(2026, 8, 27, 19, 0, 0, tzinfo=timezone.utc)
        # 1d = 24 hours
        dt_1d = run_viewer.parse_since_timestamp("1d", fixed_now)
        self.assertEqual(dt_1d, datetime(2026, 8, 26, 19, 0, 0, tzinfo=timezone.utc))

        # 0.5d = 12 hours
        dt_half_d = run_viewer.parse_since_timestamp("0.5d", fixed_now)
        self.assertEqual(dt_half_d, datetime(2026, 8, 27, 7, 0, 0, tzinfo=timezone.utc))

        # 2h = 2 hours
        dt_2h = run_viewer.parse_since_timestamp("2h", fixed_now)
        self.assertEqual(dt_2h, datetime(2026, 8, 27, 17, 0, 0, tzinfo=timezone.utc))

        # 1.5h = 90 mins
        dt_1_5h = run_viewer.parse_since_timestamp("1.5h", fixed_now)
        self.assertEqual(dt_1_5h, datetime(2026, 8, 27, 17, 30, 0, tzinfo=timezone.utc))

        # 1w = 7 days
        dt_1w = run_viewer.parse_since_timestamp("1w", fixed_now)
        self.assertEqual(dt_1w, datetime(2026, 8, 20, 19, 0, 0, tzinfo=timezone.utc))

        # 1m = ~30 days
        dt_1m = run_viewer.parse_since_timestamp("1m", fixed_now)
        self.assertTrue((fixed_now - dt_1m).days >= 30)

        # 1y = ~365 days
        dt_1y = run_viewer.parse_since_timestamp("1y", fixed_now)
        self.assertTrue((fixed_now - dt_1y).days >= 365)

    def test_parse_since_timestamp_dates(self):
        from datetime import datetime, timezone

        dt_ymd = run_viewer.parse_since_timestamp("2026-08-25")
        self.assertEqual(dt_ymd, datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc))

        dt_dense = run_viewer.parse_since_timestamp("20260825")
        self.assertEqual(dt_dense, datetime(2026, 8, 25, 0, 0, 0, tzinfo=timezone.utc))

        dt_iso = run_viewer.parse_since_timestamp("2026-08-27T13:00:00Z")
        self.assertEqual(dt_iso, datetime(2026, 8, 27, 13, 0, 0, tzinfo=timezone.utc))

    def test_parse_since_timestamp_invalid(self):
        with self.assertRaises(ValueError):
            run_viewer.parse_since_timestamp("invalid-date-or-spec")

    def test_run_viewer_cli_since_filter(self):
        # Filtering with --since 10y should return runs
        ns = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="10y",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        self.assertIn("run-", buf.getvalue())

        # Filtering with a specific run ID should include that run and subsequent runs
        ns_run_id = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="run-20260827T212854Z-2364829",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf_run = io.StringIO()
        with redirect_stdout(buf_run):
            code_run = run_viewer.run_viewer_cli(ns_run_id)
        self.assertEqual(code_run, 0)
        self.assertIn("run-20260827T212854Z-2364829", buf_run.getvalue())
        self.assertIn("run-20260827T212958Z-2367239", buf_run.getvalue())

        # Filtering with an invalid --since should return code 2
        ns_bad = argparse.Namespace(
            dir=str(self.root),
            target=[],
            set=None,
            ipd=None,
            status=None,
            failed=False,
            active=False,
            latest=False,
            since="not-a-timespec",
            detail=False,
            json=False,
            agent=False,
            no_color=True,
        )
        buf_bad = io.StringIO()
        with redirect_stdout(buf_bad):
            code_bad = run_viewer.run_viewer_cli(ns_bad)
        self.assertEqual(code_bad, 2)

    def test_extract_log_metrics_opencode(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            log_p = Path(td) / "session.jsonl"
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
                            },
                            "cost": 0.081,
                        },
                    }
                ),
            ]
            log_p.write_text("\n".join(lines), encoding="utf-8")
            cost, toks = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost, 0.133, places=3)
            self.assertEqual(toks["total"], 3500)
            self.assertEqual(toks["input"], 3000)
            self.assertEqual(toks["output"], 500)
            self.assertEqual(toks["cache"], 60)

    def test_extract_log_metrics_usage_shape(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            log_p = Path(td) / "session.jsonl"
            lines = [
                json.dumps(
                    {
                        "type": "agent_response",
                        "usage": {
                            "total_tokens": 500,
                            "input_tokens": 400,
                            "output_tokens": 100,
                        },
                        "cost": 0.015,
                    }
                )
            ]
            log_p.write_text("\n".join(lines), encoding="utf-8")
            cost, toks = run_viewer.extract_log_metrics(log_p)
            self.assertAlmostEqual(cost, 0.015, places=3)
            self.assertEqual(toks["total"], 500)
            self.assertEqual(toks["input"], 400)
            self.assertEqual(toks["output"], 100)

    def test_format_step_line_cost_badge(self):
        term = Term(color=False)
        step = run_viewer.StepSummary(
            position=1,
            id6="abc123",
            setid="testset",
            action="execute",
            status="executed",
            configured_file="",
            stem="testset-abc123",
            cost=12.3456,
            tokens={"total": 50000},
        )
        line = run_viewer.format_step_line(step, term)
        self.assertIn("[$12.35]", line)
        self.assertIn("executed", line)

    def test_format_run_human_with_cost_and_detail(self):
        term = Term(color=False)
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
        run = run_viewer.RunSummary(
            run_id="run-20260829T000000Z-111111",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00+00:00",
            setids=["testset"],
            steps=[step1, step2],
            counts={"executed": 1, "reviewed": 1},
            total_cost=15.75,
            total_tokens={"total": 150000, "input": 120000, "output": 30000},
        )
        formatted = run_viewer.format_run_human(run, term, detail=True)
        self.assertIn("$15.75", formatted)
        self.assertIn("150.00K tok", formatted)
        self.assertIn("$10.50", formatted)
        self.assertIn("$5.25", formatted)
        self.assertIn("$ cost: $10.50", formatted)
        self.assertIn("* tokens: 100.00K tot", formatted)

    def test_multi_run_summary_dict_and_format(self):
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
        )
        step2 = run_viewer.StepSummary(
            position=2,
            id6="a2",
            setid="s1",
            action="review",
            status="reviewed",
            configured_file="",
            stem="s1-a2",
            cost=6.00,
            tokens={"total": 60000},
        )
        step3 = run_viewer.StepSummary(
            position=1,
            id6="b1",
            setid="s2",
            action="review",
            status="reviewed",
            configured_file="",
            stem="s2-b1",
            cost=8.00,
            tokens={"total": 80000},
        )
        step4 = run_viewer.StepSummary(
            position=2,
            id6="b2",
            setid="s2",
            action="execute",
            status="queued",
            configured_file="",
            stem="s2-b2",
            cost=None,
            tokens={},
        )
        run1 = run_viewer.RunSummary(
            run_id="run-1",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00Z",
            setids=["s1"],
            steps=[step1, step2],
            counts={"executed": 1, "reviewed": 1},
            total_cost=16.00,
            total_tokens={"total": 160000},
        )
        run2 = run_viewer.RunSummary(
            run_id="run-2",
            run_dir=Path("."),
            created_at="2026-08-29T01:00:00Z",
            setids=["s2"],
            steps=[step3, step4],
            counts={"reviewed": 1, "queued": 1},
            total_cost=8.00,
            total_tokens={"total": 80000},
        )
        summary_dict = run_viewer.build_multi_run_summary_dict([run1, run2])
        self.assertEqual(summary_dict["runs_count"], 2)
        self.assertEqual(summary_dict["steps_count"], 4)
        self.assertEqual(summary_dict["steps_with_cost"], 3)
        self.assertEqual(summary_dict["total_cost"], 24.00)
        self.assertEqual(summary_dict["avg_cost_per_run"], 12.00)

        # Check by_status
        self.assertEqual(summary_dict["by_status"]["executed"]["total_cost"], 10.00)
        self.assertEqual(
            summary_dict["by_status"]["executed"]["avg_cost_per_step"], 10.00
        )
        self.assertEqual(
            summary_dict["by_status"]["executed"]["avg_cost_per_run"], 5.00
        )
        self.assertEqual(summary_dict["by_status"]["reviewed"]["total_cost"], 14.00)
        self.assertEqual(
            summary_dict["by_status"]["reviewed"]["avg_cost_per_step"], 7.00
        )
        self.assertEqual(
            summary_dict["by_status"]["reviewed"]["avg_cost_per_run"], 7.00
        )
        self.assertEqual(summary_dict["by_status"]["queued"]["count"], 1)
        self.assertEqual(summary_dict["by_status"]["queued"]["steps_with_cost"], 0)

        # Check by_action
        self.assertEqual(summary_dict["by_action"]["review"]["avg_cost_per_step"], 7.00)
        self.assertEqual(summary_dict["by_action"]["review"]["avg_cost_per_run"], 7.00)
        self.assertEqual(
            summary_dict["by_action"]["execute"]["avg_cost_per_step"], 10.00
        )
        self.assertEqual(summary_dict["by_action"]["execute"]["avg_cost_per_run"], 5.00)

        # Check format_multi_run_summary text with color=False
        text = run_viewer.format_multi_run_summary([run1, run2], term)
        self.assertIn("Summary across 2 runs (4 steps)", text)
        self.assertIn(
            "Total Cost:   $24.00 (across 3/4 steps with usage; avg $12.00/run)", text
        )
        self.assertIn("Breakdown by Status:", text)
        self.assertIn("╭", text)
        self.assertIn("│ Status", text)
        self.assertIn("Type", text)
        self.assertIn("Cost", text)
        self.assertIn("Tokens", text)
        self.assertIn("In", text)
        self.assertIn("Out", text)
        self.assertIn("Cached", text)
        self.assertIn("Total", text)
        self.assertIn("Avg", text)
        self.assertIn("reviewed", text)
        self.assertIn("$14.00", text)
        self.assertIn("$7.00", text)
        self.assertIn("executed", text)
        self.assertIn("$10.00", text)
        self.assertIn("queued", text)
        self.assertIn("╰", text)

        # Check format_multi_run_summary text with color=True
        color_term = Term(color=True)
        color_text = run_viewer.format_multi_run_summary([run1, run2], color_term)
        self.assertIn("Summary across 2 runs (4 steps)", color_text)
        self.assertIn("Total Cost:", color_text)
        self.assertIn("Breakdown by Status:", color_text)
        self.assertIn("Breakdown by Action:", color_text)
        self.assertIn("╭", color_text)
        self.assertIn("╰", color_text)

    def test_multi_run_summary_breakdown_with_verification(self):
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
            tokens={"total": 100000, "input": 10000, "output": 5000, "cache": 85000},
            exec_cost=7.00,
            exec_tokens={"total": 70000, "input": 7000, "output": 3500, "cache": 59500},
            verify_cost=3.00,
            verify_tokens={
                "total": 30000,
                "input": 3000,
                "output": 1500,
                "cache": 25500,
            },
        )
        run1 = run_viewer.RunSummary(
            run_id="run-1",
            run_dir=Path("."),
            created_at="2026-08-29T00:00:00Z",
            setids=["s1"],
            steps=[step1],
            counts={"executed": 1},
            total_cost=10.00,
            total_tokens={
                "total": 100000,
                "input": 10000,
                "output": 5000,
                "cache": 85000,
            },
            exec_cost=7.00,
            exec_tokens={"total": 70000, "input": 7000, "output": 3500, "cache": 59500},
            verify_cost=3.00,
            verify_tokens={
                "total": 30000,
                "input": 3000,
                "output": 1500,
                "cache": 25500,
            },
        )

        # Single run format
        run_txt = run_viewer.format_run_human(run1, term)
        self.assertIn("Total:        $10.00, 100.00K tok", run_txt)
        self.assertIn("- Execute:  $7.00, 70.00K tok", run_txt)
        self.assertIn("- Verify:   $3.00, 30.00K tok", run_txt)

        # Step details format
        details = run_viewer.render_step_details([step1], term)
        details_txt = "\n".join(details)
        self.assertIn("$ cost: $10.00 (exec: $7.00, verify: $3.00)", details_txt)
        self.assertIn("[exec: 70.00K, verify: 30.00K]", details_txt)

        # Multi-run summary format
        summary_dict = run_viewer.build_multi_run_summary_dict([run1])
        self.assertIn("by_phase", summary_dict)
        self.assertEqual(summary_dict["by_phase"]["execution"]["total_cost"], 7.00)
        self.assertEqual(summary_dict["by_phase"]["verification"]["total_cost"], 3.00)
        self.assertEqual(summary_dict["by_phase"]["total"]["total_cost"], 10.00)

        sum_txt = run_viewer.format_multi_run_summary([run1], term)
        self.assertIn("Total Cost:   $10.00", sum_txt)
        self.assertIn("Total Tokens: 100.00K", sum_txt)
        self.assertIn("Breakdown for Verified Executions (1 step):", sum_txt)
        self.assertIn("execution", sum_txt)
        self.assertIn("verification", sum_txt)
        self.assertIn("total", sum_txt)
        self.assertIn("70%", sum_txt)
        self.assertIn("30%", sum_txt)
        self.assertIn("100%", sum_txt)

    def test_multi_run_cli_json_summary(self):
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
            json=True,
            agent=False,
            no_color=True,
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 0)
        parsed = json.loads(buf.getvalue())
        self.assertIn("runs", parsed)
        self.assertIn("summary", parsed)
        self.assertEqual(parsed["summary"]["runs_count"], 2)
        self.assertIn("by_status", parsed["summary"])
        self.assertIn("by_action", parsed["summary"])

    def test_format_duration(self):
        self.assertEqual(run_viewer.format_duration(None), "0s")
        self.assertEqual(run_viewer.format_duration(-5), "0s")
        self.assertEqual(run_viewer.format_duration(5.4), "5.4s")
        self.assertEqual(run_viewer.format_duration(45), "45s")
        self.assertEqual(run_viewer.format_duration(125), "2m 05s")
        self.assertEqual(run_viewer.format_duration(3665), "1h 01m 05s")

    def test_inspect_run_pid_and_runtime(self):
        import tempfile
        from datetime import datetime, timezone

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

    def test_format_run_human_pid_and_runtime(self):
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
        self.assertIn("0 steps: 2 executed", lines[2])
        self.assertIn(
            "$5.50, 50.00K tok (40.00K in, 10.00K out, 30.00K cached)", lines[3]
        )

    def test_audit_step_artifact_and_summary(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pending_dir = root / ".aw" / "records" / "plans" / "pending"
            executed_dir = root / ".aw" / "records" / "plans" / "executed"
            pending_dir.mkdir(parents=True)
            executed_dir.mkdir(parents=True)

            # Plan 1: In pending with status approved, but step is complete (loc & status mismatch)
            p1 = pending_dir / "20260829-test-01-item01.ipd.md"
            p1.write_text("- Id: item01\n- Status: approved\n")

            # Plan 2: In executed with status executed, step executed (clean)
            p2 = executed_dir / "20260829-test-02-item02.ipd.md"
            p2.write_text("- Id: item02\n- Status: executed\n")

            st1 = run_viewer.StepSummary(
                position=1,
                id6="item01",
                setid="test",
                action="execute",
                status="complete",
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
            self.assertEqual(a1.file_status, "approved")

            a2 = run_viewer.audit_step_artifact(st2, repo_root=root)
            self.assertFalse(a2.location_mismatch)
            self.assertFalse(a2.status_mismatch)
            self.assertFalse(a2.missing_entirely)

            a3 = run_viewer.audit_step_artifact(st3, repo_root=root)
            self.assertTrue(a3.missing_entirely)

            term = Term(color=False)
            sum_txt = run_viewer.format_artifact_audit_summary([a1, a2, a3], term)
            self.assertIn("Artifact & Status Discrepancies", sum_txt)
            self.assertIn("Expected", sum_txt)
            self.assertIn("Actual", sum_txt)
            self.assertIn("20260829-test-01-item01", sum_txt)
            self.assertIn("pending/", sum_txt)
            self.assertIn("approved", sum_txt)
            self.assertIn("20260829-test-03-item03", sum_txt)
            self.assertIn("missing", sum_txt)

            # Check table rendering decoration
            tbl = run_viewer.render_steps_table([st1, st2, st3], term, repo_root=root)
            self.assertIn("Issue", tbl)
            self.assertIn("YES", tbl)
            self.assertIn("no", tbl)

            # Check in-flight tagging when step is live
            st1_live = run_viewer.StepSummary(
                position=1,
                id6="item01",
                setid="test",
                action="execute",
                status="complete",
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

    def test_run_viewer_cli_issues_flag(self):
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
                        "status": "complete",
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
                code = run_viewer.run_viewer_cli(ns)
            self.assertEqual(code, 0)
            out = buf.getvalue()
            self.assertIn("Artifact & Status Discrepancies", out)
            self.assertIn("20260829-test-01-item01", out)
            self.assertNotIn("pid:", out)

    def test_run_viewer_cli_issues_flag_empty_state(self):
        """The NEGATIVE polarity of `--issues` (i79rgh E-02), on its own fixture.

        The populated case above only shows that a discrepancy is REPORTED. Without this
        test, an `--issues` implementation that reported a discrepancy unconditionally
        would still pass, and the empty-state string would be untested. Both polarities
        are pinned on fixtures so neither depends on the live repository's health.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # A CLEAN repo: the plan is in executed/ with `- Status: executed`, which is
            # exactly what a step whose run status is `complete` should look like, so
            # audit_step_artifact finds neither a location nor a status mismatch.
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
                        "status": "complete",
                        "configured_file": (
                            ".aw/records/plans/executed/20260829-test-01-item01.ipd.md"
                        ),
                        "stem": "20260829-test-01-item01",
                    }
                ],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

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
                code = run_viewer.run_viewer_cli(ns)
            self.assertEqual(code, 0)
            out = buf.getvalue()
            self.assertEqual(out.strip(), "no artifact or status discrepancies found")
            self.assertNotIn("Artifact & Status Discrepancies", out)

    def test_run_viewer_cli_issues_conflict(self):
        ns = argparse.Namespace(
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
            code = run_viewer.run_viewer_cli(ns)
        self.assertEqual(code, 2)
        out = buf.getvalue()
        self.assertIn("error: --issues/-i cannot be used with --summary-only/-S", out)


class UnresolvableTargetRefusalTests(TestCase):
    """`aw runs <unresolvable-target>` must REFUSE, not report success having done nothing.

    runsverify 7wei1o E-05. The defect: `aw runs` carries two shapes at once, so its routing branch
    is leaf-or-viewer with no third outcome, and any first positional that is not a registered leaf
    name became a TARGET by construction. A target matching nothing was then silently DROPPED and the
    command still exited 0.

    The measured harm, and why this is not a cosmetic exit code: `aw runs verify <run-id>` names no
    leaf (the leaf is `verify-ledger`), so it rendered the run's ordinary report and exited 0 while
    verifying nothing at all. Until 2026-09-05 the spec documented that exact spelling and seven
    shipped recovery messages in `run_evidence.py` told operators to run it, precisely when a ledger
    might be corrupt. An operator asking for an integrity check got a normal-looking report and a
    success exit, and reasonably concluded nothing was wrong.

    Every exit code below is asserted on the return of the real `cli.main`, which is the process exit
    code. Measuring the same thing in a shell REQUIRES `cmd >/dev/null 2>&1; echo $?` rather than a
    pipe, because a piped `$?` reports the last pipeline stage; that mistake produced a false finding
    elsewhere in this Set (`zrzfkw`, corrected 2026-09-06).
    """

    def test_runs_verify_run_id_is_refused(self):
        """THE MOTIVATING CASE: the near-miss leaf spelling must fail loudly and suggest the leaf."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["verify", _FIXTURE_RUN])

            self.assertEqual(code, 2, out + err)
            # It must NAME the unresolved token, so a future refactor cannot degrade the refusal to a
            # bare exit code, and must SUGGEST the one-edit correction.
            self.assertIn("verify", err)
            self.assertIn("verify-ledger", err)
            # And it must NOT have rendered the run's report, which is what made the bug convincing.
            self.assertNotIn(_FIXTURE_RUN, out)

    def test_wholly_unknown_token_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["totalgibberish"])

            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", err)
            # The old behaviour, explicitly gone.
            self.assertNotIn("no matching runs found", out)

    def test_mixed_resolvable_and_unresolvable_is_refused_not_partially_rendered(self):
        """The MOST misleading variant, refused deliberately (E-04).

        `aw runs totalgibberish <real-run-id>` printed the real run at exit 0 with the bogus token
        silently dropped, so the output LOOKED like a complete answer to the question asked. A
        partially-honored request that looks complete is the whole defect, so a request is either
        honored in full or refused, never quietly narrowed.
        """
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["totalgibberish", _FIXTURE_RUN])

            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", err)
            self.assertNotIn(_FIXTURE_RUN, out)

    def test_refusal_message_goes_to_stderr_not_stdout(self):
        """Keeps a refusal out of a report a caller may be parsing on stdout."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["totalgibberish"])
            self.assertEqual(code, 2)
            self.assertIn("totalgibberish", err)
            self.assertEqual(out, "")

    def test_refusal_is_honored_by_the_agent_renderer(self):
        """The machine path is the one automation READS, so it must refuse too (F-11).

        `--agent` and `--json` both emitted `{"runs": []}` and returned 0 from a branch that ran
        BEFORE the human line, so a human-only refusal would have left the fail-open exactly where it
        silently misleads a script.
        """
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["totalgibberish", "--agent"])

            self.assertEqual(code, 2, out + err)
            record = json.loads(out.strip())
            # A conformant aw.agent/v1 error record, NOT a bare empty payload...
            self.assertEqual(record["schema"], "aw.agent/v1")
            self.assertEqual(record["kind"], "error")
            self.assertEqual(record["outcome"], "cannot-run")
            self.assertFalse(record["complete"])
            # ...whose `exit` AGREES with the process exit code (asserted by the conformance matrix).
            self.assertEqual(record["exit"], code)
            self.assertEqual(record["unresolved_targets"], ["totalgibberish"])
            self.assertNotIn("runs", record)

    def test_refusal_is_honored_by_the_json_renderer(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["totalgibberish", "--json"])

            self.assertEqual(code, 2, out + err)
            record = json.loads(out)
            self.assertEqual(record["kind"], "error")
            self.assertEqual(record["exit"], code)
            self.assertEqual(record["unresolved_targets"], ["totalgibberish"])

    def test_refusal_reaches_through_the_escape_hatch(self):
        """The hatch decides a token is a TARGET; it never claims the target EXISTS."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["--", "no-such-target-xyz"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("no-such-target-xyz", err)

    def test_every_unresolved_token_is_named_not_just_the_first(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["bogus-one", "bogus-two"])
            self.assertEqual(code, 2, out + err)
            self.assertIn("bogus-one", err)
            self.assertIn("bogus-two", err)

    # ---- The anti-regression half (E-03). This change can only fail in ONE direction: by refusing
    # ---- an invocation that used to work. These are the cases that must stay exit 0.

    def test_every_resolvable_target_shape_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            for argv in (
                [_FIXTURE_RUN],  # a full run id
                ["2367239"],  # a run-id SUBSTRING
                [_FIXTURE_SETID],  # a Set id
                ["lanectn"],  # a second Set id
                [
                    str(root / ".aw" / "records" / "runs" / _FIXTURE_RUN)
                ],  # a directory path
                [],  # bare: "all runs"
            ):
                with self.subTest(argv=argv):
                    out, err, code = _run_viewer(root, argv)
                    self.assertEqual(code, 0, out + err)

    def test_every_viewer_flag_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            for argv in (
                ["--last", "1"],
                ["--latest-only"],
                ["--issues"],
                ["--summary-only"],
                ["--short"],
                ["--detail"],
                ["--since", "2026-09-01"],
                ["--since", "7d"],
                ["--since", _FIXTURE_RUN],
                ["--set", "lanectn"],
                ["--ipd", "aaa111"],
                ["--agent"],
                ["--json"],
            ):
                with self.subTest(argv=argv):
                    out, err, code = _run_viewer(root, argv)
                    self.assertEqual(code, 0, out + err)

    def test_bare_call_on_an_empty_repository_is_still_success(self):
        """OQ-01: asking for EVERYTHING and finding nothing is a healthy state, not a failed request.

        The distinction the refusal draws is between "you asked for something SPECIFIC that does not
        exist" (an error) and "you asked for everything and there is nothing" (not an error).
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".aw" / "records").mkdir(parents=True)
            out, err, code = _run_viewer(root, [])
            self.assertEqual(code, 0, out + err)
            self.assertIn("no matching runs found", out)

    def test_a_filter_that_excludes_everything_is_still_success(self):
        """A resolvable target plus a filter that matches nothing is an empty RESULT, not a refusal."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["--set", "no-such-set"])
            self.assertEqual(code, 0, out + err)
            self.assertIn("no matching runs found", out)

    def test_a_leaf_named_target_is_reachable_through_the_hatch_and_exits_zero(self):
        """The AMBIGUITY RULE is preserved: the hatch still reaches a Set that collides with a leaf.

        The fixture CONSTRUCTS the collision (a Set genuinely named `status`) because none exists
        among the repo's real set ids, so this cannot be covered by observation alone.
        """
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["--", "status"])
            self.assertEqual(code, 0, out + err)
            self.assertIn("run-20260902T010000Z-3333333", out)

    def test_bare_leaf_name_without_the_hatch_still_routes_to_the_leaf(self):
        """The other half of the ambiguity rule: the LEAF wins, and the refusal must not invert it."""
        out, err, code = _run_viewer(Path("."), ["status"])
        self.assertNotEqual(code, 0)
        # The LEAF's own usage error (it demands its required target), not the viewer's refusal.
        self.assertIn("target", (out + err).lower())
        self.assertNotIn("no run matched target", out + err)

    def test_already_correct_refusals_keep_their_own_messages(self):
        """The new refusal must not shadow the validation that already exits 2 for other reasons."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            for argv, expected in (
                (["--since", "bogusdate"], "invalid date"),
                (["--summary-only", "--short"], "cannot be used with"),
                (["--latest-only", "--summary-only"], "cannot be used with"),
                (["--issues", "--summary-only"], "cannot be used with"),
            ):
                with self.subTest(argv=argv):
                    out, err, code = _run_viewer(root, argv)
                    self.assertEqual(code, 2, out + err)
                    self.assertIn(expected, out + err)
                    self.assertNotIn("no run matched target", out + err)


class ResolverSetidNarrowingTests(TestCase):
    """The resolver's `state.json` fallback must read the setid FIELD, not raw file text.

    runsverify 7wei1o E-07. This is LOAD-BEARING for the refusal above, not a cleanup: the old
    fallback was `if f'"{t_str}"' in content` over the whole file, so any quoted JSON key or value
    anywhere matched. Measured against 106 live run records BEFORE the fix: `status`, `run`,
    `opencode`, `driver`, `run_id` and `options` each resolved 106 of 106, `clean` 105, `main` 96,
    `json` 79, `execute` 53, `approved` 46, `verified` 13. None of those is a Set id. A mistyped token
    that happened to be a JSON key therefore resolved to EVERY run in the repository and reported
    success, which is the same fail-open one layer down: such a token is never "unresolved", so it
    would be silently exempted from the refusal.
    """

    def test_ordinary_json_keys_and_values_no_longer_resolve(self):
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            for token in (
                "opencode",  # a value under the `driver` key
                "driver",  # a key
                "run_id",  # a key
                "options",  # a key
                "main",  # a value under `options.base_branch`
                "clean",  # a value under `options.worktree`
                "execute",  # every queue item's `action`
                "complete",  # every queue item's `status`
                "queue",  # a key
                "position",  # a key
            ):
                with self.subTest(token=token):
                    self.assertEqual(
                        run_viewer.resolve_target_runs([token], root),
                        [],
                        f"{token!r} must not resolve: it is JSON structure, not a Set id",
                    )

    def test_real_setids_and_run_id_substrings_still_resolve(self):
        """The anti-regression half: a narrowing that breaks setid lookup is a failed fix."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            # Two runs carry `runnernorm`; one carries `lanectn`; one carries the collision `status`.
            self.assertEqual(
                len(run_viewer.resolve_target_runs([_FIXTURE_SETID], root)), 2
            )
            self.assertEqual(len(run_viewer.resolve_target_runs(["lanectn"], root)), 1)
            self.assertEqual(len(run_viewer.resolve_target_runs(["status"], root)), 1)
            # A run-id substring is a DIFFERENT, earlier rule and is untouched by the narrowing.
            resolved = run_viewer.resolve_target_runs(["2367239"], root)
            self.assertEqual(len(resolved), 1)
            self.assertIn("2367239", resolved[0].name)

    def test_detailed_resolver_separates_unresolved_from_absent(self):
        """E-01: the caller must be able to tell "asked for nothing" from "asked for the missing"."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))

            # 1. A real id: resolved, nothing unresolved.
            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                [_FIXTURE_RUN], root
            )
            self.assertEqual(len(runs), 1)
            self.assertEqual(unresolved, [])

            # 2. A bogus token: nothing resolved, and it is NAMED.
            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                ["totalgibberish"], root
            )
            self.assertEqual(runs, [])
            self.assertEqual(unresolved, ["totalgibberish"])

            # 3. Both: the real one resolves AND the bogus one is still reported (the mixed case,
            #    which used to render a plausible partial answer at exit 0).
            runs, unresolved = run_viewer.resolve_target_runs_detailed(
                ["totalgibberish", _FIXTURE_RUN], root
            )
            self.assertEqual(len(runs), 1)
            self.assertEqual(unresolved, ["totalgibberish"])

            # 4. A BARE call is distinguishable from "all tokens unresolved": it resolves every run
            #    and reports nothing unresolved, which is what keeps an empty repository exit 0.
            runs, unresolved = run_viewer.resolve_target_runs_detailed([], root)
            self.assertEqual(len(runs), 4)
            self.assertEqual(unresolved, [])

    def test_setid_resolves_from_run_level_selectors_too(self):
        """A run whose queue is empty is still reachable by the Set it was LAUNCHED with."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "runs" / "run-20260905T000000Z-4444444"
            d.mkdir(parents=True)
            (d / "state.json").write_text(
                json.dumps({"run_id": d.name, "selectors": ["emptyset"], "queue": []}),
                encoding="utf-8",
            )
            self.assertEqual(len(run_viewer.resolve_target_runs(["emptyset"], root)), 1)

    def test_malformed_state_json_does_not_raise(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / ".aw" / "records" / "runs" / "run-20260905T000000Z-5555555"
            d.mkdir(parents=True)
            (d / "state.json").write_text("{not json at all", encoding="utf-8")
            self.assertEqual(run_viewer.resolve_target_runs(["anything"], root), [])


class RunsRepairHelpTests(TestCase):
    """`aw runs repair` must be documented and discoverable.

    `repair` is routed from `aw runs`' first POSITIONAL token (ssk6nf E-04) so that every READ
    path stays side-effect free. The cost of that design is that argparse never learns `repair`
    is a verb, so it consumed `--help` and printed the generic `runs` help: a user asking about
    the one MUTATING verb was shown a page describing a read-only inspector, and the verb was
    findable only by reading an executed plan. These tests pin the fix at both layers.

    Fixture-based on purpose: per this module's header hazard, a new test must NOT read the live
    repository via dir=".".
    """

    def test_repair_help_describes_the_repair_verb_not_the_inspector(self):
        """`aw runs repair --help` prints REPAIR's help, exits 0, and never claims read-only."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(["runs", "repair", "--help"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("usage: aw runs repair", out)
        # The decision it makes, both branches, since that is what an operator needs to trust it.
        self.assertIn("executed", out)
        self.assertIn("interrupted", out)
        # Its refusals: a live holder must not be repaired under, and success is never fabricated.
        self.assertIn("live driver", out)
        # It must NOT be the generic read-only inspector page.
        self.assertNotIn("Zero or more run IDs", out)

    def test_repair_help_accepts_short_flag(self):
        """`-h` is honoured identically; a user should not have to guess the long form."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main(["runs", "repair", "-h"])
        self.assertEqual(code, 0)
        self.assertIn("usage: aw runs repair", buf.getvalue())

    def test_runs_help_advertises_repair(self):
        """The `runs` page must name `repair` and stop calling itself unqualified read-only.

        Without this, the verb is invisible to anyone who has not read plan ssk6nf.
        """
        buf = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with redirect_stdout(buf):
                cli.main(["runs", "--help"])
        self.assertEqual(ctx.exception.code, 0)
        out = buf.getvalue()
        self.assertIn("repair", out)
        self.assertIn("aw runs repair --help", out)

    def test_repair_without_a_target_errors_and_shows_usage(self):
        """A bare `aw runs repair` must say what is missing AND how to use it (exit 2)."""
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
            code = run_viewer.run_viewer_cli(ns)
        out = buf.getvalue()
        self.assertEqual(code, 2)
        self.assertIn("needs a run id", out)
        self.assertIn("usage: aw runs repair", out)

    def test_repair_on_a_non_run_directory_exits_2(self):
        """A path that is not a run dir is a usage error, not a crash or a silent no-op."""
        with tempfile.TemporaryDirectory() as td:
            code, message = run_viewer.repair_run(Path(td), Path(td))
        self.assertEqual(code, 2)
        self.assertIn("not a run directory", message)

    def test_repair_is_a_no_op_when_nothing_is_running(self):
        """Repair must be safe to re-run: no `running` steps means no change and exit 0."""
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
            before = (run_dir / "state.json").read_text(encoding="utf-8")

            code, message = run_viewer.repair_run(run_dir, root)

            self.assertEqual(code, 0)
            self.assertIn("nothing to repair", message)
            # Truly a no-op: state.json is byte-identical afterwards.
            self.assertEqual(
                before, (run_dir / "state.json").read_text(encoding="utf-8")
            )

    def test_repair_refuses_an_unresolvable_target_instead_of_silently_succeeding(self):
        """`aw runs repair <unresolvable>` must refuse, not exit 0 having repaired nothing.

        runsverify 7wei1o E-08. The resolve loop simply never executed when nothing matched, so `rc`
        stayed 0 and NOTHING was printed (measured before the fix: exit 0, zero bytes of output).
        That is the worst place for this defect on the whole surface, because `repair` is the ONE
        mutating verb here and the operator was told nothing at all. Note the adjacent no-target case
        was already correct, so this closed an inconsistency inside a single function.
        """
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["repair", "totalgibberish"])

            self.assertEqual(code, 2, out + err)
            self.assertIn("totalgibberish", out + err)  # names the token
            # A refused mutation must not have written anything.
            state_files = sorted(
                (root / ".aw" / "records" / "runs").glob("*/state.json")
            )
            self.assertEqual(len(state_files), 4)
            for sf in state_files:
                self.assertNotIn("interrupted", sf.read_text(encoding="utf-8"))

    def test_repair_still_works_on_a_resolvable_target(self):
        """The E-08 anti-regression half: a real target still repairs (or no-ops) at exit 0."""
        with tempfile.TemporaryDirectory() as td:
            root = _build_viewer_fixture(Path(td))
            out, err, code = _run_viewer(root, ["repair", _FIXTURE_RUN])
            self.assertEqual(code, 0, out + err)
            self.assertIn("nothing to repair", out)

    def test_format_step_duration(self):
        self.assertEqual(run_viewer.format_step_duration(None), "-")
        self.assertEqual(run_viewer.format_step_duration(-5.0), "-")
        self.assertEqual(run_viewer.format_step_duration(0), "00:00:00")
        self.assertEqual(run_viewer.format_step_duration(45), "00:00:45")
        self.assertEqual(run_viewer.format_step_duration(1167), "00:19:27")
        self.assertEqual(run_viewer.format_step_duration(10479), "02:54:39")
        self.assertEqual(run_viewer.format_step_duration(97676), "1d 03:07:56")

    def test_extract_step_elapsed(self):
        # 1. Empty or non-existent attempts
        sec, text = run_viewer.extract_step_elapsed({})
        self.assertIsNone(sec)
        self.assertIsNone(text)

        sec, text = run_viewer.extract_step_elapsed({"attempts": []})
        self.assertIsNone(sec)
        self.assertIsNone(text)

        # 2. Single finished attempt
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

        # 3. Multiple attempts (e.g. interrupted + retry)
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
        self.assertEqual(sec_m, 600.0 + 630.0)
        self.assertEqual(text_m, "00:20:30")

        # 4. In-flight attempt (running / live)
        now_mock = datetime(2026, 9, 5, 21, 30, 0, tzinfo=timezone.utc)
        item_live = {
            "attempts": [
                {
                    "attempt": 1,
                    "started_at": "2026-09-05T21:15:41Z",
                }
            ]
        }
        sec_live, text_live = run_viewer.extract_step_elapsed(
            item_live, is_live=True, now=now_mock
        )
        self.assertEqual(sec_live, 859.0)
        self.assertEqual(text_live, "00:14:19")

    def test_render_steps_table_elapsed_column(self):
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
        self.assertIn("-", tbl)

        # In short mode, Elapsed should NOT appear
        tbl_short = run_viewer.render_steps_table([st1, st2], term, short=True)
        self.assertNotIn("Elapsed", tbl_short)
        self.assertNotIn("00:19:27", tbl_short)

    def test_render_step_details_includes_elapsed(self):
        term = Term(color=False)
        st = run_viewer.StepSummary(
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
        details = run_viewer.render_step_details([st], term)
        self.assertTrue(any("elapsed: 00:19:27" in d for d in details))


class AnalyticsIsolationTests(TestCase):
    """Analytics isolation and reservation tests (runanalytics Order 01, `xbwq8n`).

    Validates E-02 / V-02:
      1. discover_run_dirs rejects reserved analytics trees and nested analytics snapshots.
      2. resolve_target_runs (and resolve_target_runs_detailed) given the explicit path of
         `analytics/snapshots/run-*` returns empty and reports the unresolvable target.
      3. Explicit file targets (state.json, events.jsonl, execution-report.md) inside analytics
         are also rejected.
      4. Canonical, .aw/runs, and .agents/runs execution runs are returned in unchanged order.
      5. format_unresolvable_target_message includes actionable diagnostic naming the reserved analytics tree.
    """

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        # Real runs in canonical root
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

        # Analytics tree with nested snapshot runs
        self.analytics_dir = self.runs_dir / "analytics"
        self.snap_run = self.analytics_dir / "snapshots" / "run-20260903T000000Z-9"
        self.snap_run.mkdir(parents=True)
        (self.snap_run / "state.json").write_text(
            json.dumps({"run_id": self.snap_run.name, "setid": "analyticsset"}),
            encoding="utf-8",
        )
        (self.snap_run / "events.jsonl").write_text("{}", encoding="utf-8")
        (self.snap_run / "execution-report.md").write_text("# Report", encoding="utf-8")

        # Legacy runs
        self.legacy_aw = self.root / ".aw" / "runs" / "run-20260904T000000Z-3"
        self.legacy_aw.mkdir(parents=True)
        (self.legacy_aw / "state.json").write_text(
            json.dumps({"run_id": self.legacy_aw.name}),
            encoding="utf-8",
        )

        self.legacy_agents = self.root / ".agents" / "runs" / "run-20260905T000000Z-4"
        self.legacy_agents.mkdir(parents=True)
        (self.legacy_agents / "state.json").write_text(
            json.dumps({"run_id": self.legacy_agents.name}),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discover_run_dirs_excludes_analytics_and_nested_snapshots(self):
        found = run_viewer.discover_run_dirs(self.root)
        found_names = [p.name for p in found]
        self.assertIn("run-20260901T000000Z-1", found_names)
        self.assertIn("run-20260902T000000Z-2", found_names)
        self.assertIn("run-20260904T000000Z-3", found_names)
        self.assertIn("run-20260905T000000Z-4", found_names)
        self.assertNotIn("run-20260903T000000Z-9", found_names)
        self.assertNotIn("analytics", found_names)

    def test_discover_run_dirs_preserves_order_across_roots(self):
        found = run_viewer.discover_run_dirs(self.root)
        expected = [self.run_1, self.run_2, self.legacy_aw, self.legacy_agents]
        self.assertEqual(found, expected)

    def test_resolve_target_runs_refuses_explicit_analytics_directory_target(self):
        # Target explicitly by path to the snapshot directory (where the measured leak was)
        resolved = run_viewer.resolve_target_runs([str(self.snap_run)], self.root)
        self.assertEqual(resolved, [])

        # Detailed resolution reports it as unresolved
        resolved_dirs, unresolved = run_viewer.resolve_target_runs_detailed(
            [str(self.snap_run)], self.root
        )
        self.assertEqual(resolved_dirs, [])
        self.assertEqual(unresolved, [str(self.snap_run)])

    def test_resolve_target_runs_refuses_explicit_analytics_file_targets(self):
        for fname in ("state.json", "events.jsonl", "execution-report.md"):
            file_target = self.snap_run / fname
            resolved = run_viewer.resolve_target_runs([str(file_target)], self.root)
            self.assertEqual(
                resolved,
                [],
                f"File target {fname} inside analytics must not resolve to a run",
            )
            resolved_dirs, unresolved = run_viewer.resolve_target_runs_detailed(
                [str(file_target)], self.root
            )
            self.assertEqual(resolved_dirs, [])
            self.assertEqual(unresolved, [str(file_target)])

    def test_format_unresolvable_target_message_names_reserved_analytics_tree(self):
        msg = run_viewer.format_unresolvable_target_message(
            [str(self.snap_run)], repo_root=self.root
        )
        self.assertIn("error: no run matched target", msg)
        self.assertIn("reserved analytics tree", msg)
        self.assertIn("analytics artifacts cannot be targeted as execution runs", msg)

    def test_resolve_ledger_path_rejects_analytics_tree(self):
        from agent_workflows.run_cli import resolve_ledger_path

        snap_ledger = self.snap_run / "ledger.jsonl"
        snap_ledger.write_text("{}", encoding="utf-8")
        self.assertIsNone(resolve_ledger_path(str(snap_ledger), self.root))
        self.assertIsNone(
            resolve_ledger_path(f"analytics/snapshots/{self.snap_run.name}", self.root)
        )
