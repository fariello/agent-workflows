"""Behavioral contract tests for aw find --agent stream emission.

IPD okiso1 (wdazvp):
Make aw find --agent emit a real aw.agent/v1 record stream so --limit and --fields
are honored, keeping --paths the byte-stable script surface.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import agent_schema
from agent_workflows import cli


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")

EXPECTED_PLANS_PATHS = (
    ".aw/records/plans/pending/20260927-setalpha-01-pln001-plan-one.ipd.md\n"
    ".aw/records/plans/pending/20260927-setalpha-02-pln002-plan-two.ipd.md\n"
    ".aw/records/plans/executed/20260927-setbeta-01-pln003-plan-three.ipd.md\n"
)

EXPECTED_PLANS_HUMAN = (
    "◕  pending       pln001  setalpha        .aw/records/plans/pending/20260927-setalpha-01-pln001-plan-one.ipd.md\n"
    "◕  pending       pln002  setalpha        .aw/records/plans/pending/20260927-setalpha-02-pln002-plan-two.ipd.md\n"
    "✓  executed      pln003  setbeta         .aw/records/plans/executed/20260927-setbeta-01-pln003-plan-three.ipd.md\n"
)


class TestFindAgentStream(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_find_agent_stream_")
        self.repo_root = Path(self.temp_dir)

        # 1. Three plans across two dispositions (pending, executed)
        plans_pending = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_executed = self.repo_root / ".aw" / "records" / "plans" / "executed"
        plans_pending.mkdir(parents=True, exist_ok=True)
        plans_executed.mkdir(parents=True, exist_ok=True)

        self.plan_1 = plans_pending / "20260927-setalpha-01-pln001-plan-one.ipd.md"
        self.plan_1.write_text(
            "# IPD: Plan One\n\n- Id: pln001\n- Status: approved\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.plan_2 = plans_pending / "20260927-setalpha-02-pln002-plan-two.ipd.md"
        self.plan_2.write_text(
            "# IPD: Plan Two\n\n- Id: pln002\n- Status: draft\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.plan_3 = plans_executed / "20260927-setbeta-01-pln003-plan-three.ipd.md"
        self.plan_3.write_text(
            "# IPD: Plan Three\n\n- Id: pln003\n- Status: executed\n- Set: setbeta\n",
            encoding="utf-8",
        )

        # 2. One spec in to-review
        specs_to_review = self.repo_root / ".aw" / "records" / "specs" / "to-review"
        specs_to_review.mkdir(parents=True, exist_ok=True)
        self.spec_1 = specs_to_review / "20260927-setalpha-01-spc001-spec-one.spec.md"
        self.spec_1.write_text(
            "# Spec: Spec One\n\n- Id: spc001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )

        # 3. One backlog item in open
        bkl_open = self.repo_root / ".aw" / "records" / "backlog" / "open"
        bkl_open.mkdir(parents=True, exist_ok=True)
        self.bkl_1 = bkl_open / "20260927-setbeta-01-bkl001-item-one.backlog.md"
        self.bkl_1.write_text(
            "- Id: bkl001\n- Status: open\n- Set: setbeta\n- Work-Kind: bug\n- Priority: high\n\n## Summary\nBacklog One\n",
            encoding="utf-8",
        )

        # 4. Cross-type id6 collision fixture (col001 claimed by both spec and backlog)
        self.coll_spec = (
            specs_to_review / "20260927-setalpha-01-col001-coll-spec.spec.md"
        )
        self.coll_spec.write_text(
            "# Spec: Coll Spec\n\n- Id: col001\n- Status: to-review\n- Set: setalpha\n",
            encoding="utf-8",
        )
        self.coll_bkl = bkl_open / "20260927-setalpha-01-col001-coll-bkl.backlog.md"
        self.coll_bkl.write_text(
            "- Id: col001\n- Status: open\n- Set: setalpha\n- Work-Kind: bug\n- Priority: low\n\n## Summary\nColl Backlog\n",
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def run_find(self, extra_args: list[str]) -> tuple[int, str, str]:
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with patch("sys.stdout", buf_out), patch("sys.stderr", buf_err):
            rc = cli.main(["find", *extra_args, "--dir", str(self.repo_root)])
        return rc, buf_out.getvalue(), buf_err.getvalue()

    def test_01_agent_stream_parses_json_and_schema_version(self):
        """E-01(1): Every stdout line under --agent parses as JSON and carries schema == 'aw.agent/v1'."""
        rc, out, _ = self.run_find(["plans", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertGreater(len(lines), 0, "Expected non-empty output")
        for line in lines:
            rec = json.loads(line)
            self.assertEqual(
                rec.get("schema"), "aw.agent/v1", f"Record missing valid schema: {line}"
            )

    def test_02_agent_stream_records_strictly_validate(self):
        """E-01(2): agent_schema.validate_agent_record returns [] for EVERY emitted record."""
        rc, out, _ = self.run_find(["plans", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertGreater(len(lines), 0)
        for line in lines:
            rec = json.loads(line)
            errs = agent_schema.validate_agent_record(rec)
            self.assertEqual(errs, [], f"Validation errors on record {line}: {errs}")

    def test_03_agent_stream_terminal_summary_accounting(self):
        """E-01(3): The terminal record has kind == 'summary' and emitted + omitted == total (fixture count 3)."""
        rc, out, _ = self.run_find(["plans", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertGreater(len(lines), 1)
        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("kind"), "summary")
        total = summary.get("total")
        emitted = summary.get("emitted")
        omitted = summary.get("omitted")
        self.assertEqual(total, 3, f"Expected 3 total plans in fixture, got {total}")
        self.assertEqual(emitted, 3)
        self.assertEqual(omitted, 0)
        self.assertEqual(emitted + omitted, total)
        self.assertTrue(summary.get("complete"))

    def test_04_agent_stream_limit_bounding_and_continuation(self):
        """E-01(4): Bounded --limit N emits exactly N items, complete: false, and runnable next."""
        rc, out, _ = self.run_find(["plans", "--agent", "--limit", "2"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        items = [json.loads(line) for line in lines[:-1]]
        summary = json.loads(lines[-1])

        self.assertEqual(
            len(items), 2, f"Expected 2 item records under --limit 2, got {len(items)}"
        )
        for it in items:
            self.assertEqual(it.get("kind"), "item")
            self.assertEqual(it.get("type"), "plans")

        self.assertEqual(summary.get("kind"), "summary")
        self.assertEqual(summary.get("total"), 3)
        self.assertEqual(summary.get("emitted"), 2)
        self.assertEqual(summary.get("omitted"), 1)
        self.assertFalse(summary.get("complete"))
        self.assertIn("next", summary)
        next_cmd = summary["next"]
        self.assertTrue(
            isinstance(next_cmd, str) and next_cmd.startswith("aw find plans")
        )

    def test_05_agent_stream_fields_projection(self):
        """E-01(5): With --fields path, each item carries path and drops non-envelope key id6."""
        rc, out, _ = self.run_find(["plans", "--agent", "--fields", "path"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        items = [json.loads(line) for line in lines[:-1]]
        self.assertGreater(len(items), 0)
        for it in items:
            self.assertEqual(it.get("kind"), "item")
            self.assertIn("path", it)
            self.assertNotIn(
                "id6", it, f"Non-envelope key 'id6' was not projected out: {it}"
            )

    def test_06_agent_stream_no_ansi_escapes(self):
        """E-01(6): No stdout line contains an ANSI escape code."""
        rc, out, _ = self.run_find(["plans", "--agent"])
        self.assertEqual(rc, 0)
        self.assertNotRegex(out, _ANSI_ESCAPE_RE, "Output contains ANSI escape codes")

    def test_07_agent_stream_limit_and_fields_retains_next(self):
        """E-01(7): --limit N --fields path still carries next on the summary record."""
        rc, out, _ = self.run_find(
            ["plans", "--agent", "--limit", "2", "--fields", "path"]
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("kind"), "summary")
        self.assertIn(
            "next", summary, "Summary dropped 'next' under --fields projection"
        )
        self.assertFalse(summary.get("complete"))

    def test_08_agent_stream_zero_match_lone_summary(self):
        """E-01(8): A zero-match vocabulary query emits exactly one summary record with total: 0 at exit 0,
        while a non-vocabulary zero-match selector is refused with exit 2 and cannot-run record (zyj8io).
        """
        # 1. Non-vocabulary selector exits 2 with cannot-run record
        rc, out, _ = self.run_find(["plans", "zzzzzz", "--agent"])
        self.assertEqual(rc, 2)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        err_rec = json.loads(lines[0])
        self.assertEqual(err_rec.get("kind"), "error")
        self.assertEqual(err_rec.get("outcome"), "cannot-run")
        self.assertEqual(err_rec.get("exit"), 2)
        self.assertEqual(err_rec.get("unresolved_targets"), ["zzzzzz"])

        # 2. Standing vocabulary selector with zero matches emits lone summary at exit 0
        rc, out, _ = self.run_find(["plans", "reusable", "--agent"])
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertEqual(
            len(lines), 1, f"Expected exactly one summary record, got {len(lines)}"
        )
        summary = json.loads(lines[0])
        self.assertEqual(summary.get("kind"), "summary")
        self.assertEqual(summary.get("total"), 0)
        self.assertEqual(summary.get("emitted"), 0)
        self.assertEqual(summary.get("omitted"), 0)
        self.assertTrue(summary.get("complete"))

    def test_09_agent_stream_brace_and_space_selector_next(self):
        """E-01(9): Selectors containing {x} or space yield runnable next without exception."""
        p_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        (
            p_dir / "20260927-setalpha-04-pln004-special-{x}-has space-one.ipd.md"
        ).write_text(
            "- Id: pln004\n- Status: draft\n- Set: setalpha\n", encoding="utf-8"
        )
        (
            p_dir / "20260927-setalpha-05-pln005-special-{x}-has space-two.ipd.md"
        ).write_text(
            "- Id: pln005\n- Status: draft\n- Set: setalpha\n", encoding="utf-8"
        )

        # Query with curly braces and space in selector
        rc, out, _ = self.run_find(
            ["plans", "{x}", "has space", "--agent", "--limit", "1"]
        )
        self.assertEqual(rc, 0)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        self.assertGreater(len(lines), 1)
        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("kind"), "summary")
        self.assertIn("next", summary)
        next_cmd = summary["next"]
        self.assertIn("'{x}'", next_cmd)
        self.assertIn("'has space'", next_cmd)
        self.assertFalse(summary.get("complete"))

    def test_10_agent_stream_closed_pipe_clean_exit(self):
        """E-01(10): --agent into closed pipe exits without a traceback."""
        cmd = [
            sys.executable,
            "-m",
            "agent_workflows",
            "find",
            "plans",
            "--agent",
            "--dir",
            str(self.repo_root),
        ]
        # Pipe into head -1 via shell to simulate broken pipe
        proc = subprocess.Popen(
            f"{' '.join(cmd)} | head -n 1",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        _, stderr = proc.communicate()
        self.assertNotIn(
            "Traceback", stderr, f"BrokenPipeError traceback leaked to stderr: {stderr}"
        )

    def test_11_agent_stream_nonpositive_limit_refusal(self):
        """OQ-02: Non-positive limit (0 or -1) is refused at exit 2 with cannot-run record."""
        rc0, out0, _ = self.run_find(["plans", "--agent", "--limit", "0"])
        self.assertEqual(rc0, 2)
        rec0 = json.loads(out0.strip())
        self.assertEqual(rec0.get("outcome"), "cannot-run")

        rc_neg, out_neg, _ = self.run_find(["plans", "--agent", "--limit", "-1"])
        self.assertEqual(rc_neg, 2)
        rec_neg = json.loads(out_neg.strip())
        self.assertEqual(rec_neg.get("outcome"), "cannot-run")

    def test_12_paths_byte_identity(self):
        """Assert --paths output is byte-identical across changes."""
        rc, out, err = self.run_find(["plans", "--paths"])
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, EXPECTED_PLANS_PATHS)

    def test_13_human_output_byte_identity(self):
        """Assert unflagged human output is byte-identical across changes."""
        rc, out, err = self.run_find(["plans", "--no-color"])
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        self.assertEqual(out, EXPECTED_PLANS_HUMAN)

    def test_14_agent_collision_diagnostics_in_summary(self):
        """E-03: Collision finding find.id6-collision is placed in summary diagnostics."""
        rc, out, err = self.run_find(["all", "col001", "--agent"])
        self.assertEqual(rc, 0)
        self.assertNotIn(
            "aw-find-warning:", err, "Warning line leaked to stderr in --agent mode"
        )
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        summary = json.loads(lines[-1])
        self.assertEqual(summary.get("kind"), "summary")
        diags = summary.get("diagnostics", [])
        rules = [d.get("rule") for d in diags]
        self.assertIn(
            "find.id6-collision",
            rules,
            f"Expected find.id6-collision in diagnostics: {diags}",
        )
