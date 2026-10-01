#!/usr/bin/env python3
"""Regression test suite pinning canonical status readers and spelling-independence (qvfd4l).

Pins behavior across the four measured reader surfaces:
  (1) render_stream.render_run_summary_table progress denominator
  (2) run_viewer run-listing filter loop (--failed and --status)
  (3) run_dashboard._outcome disposition classification
  (4) render_stream.render_run_summary_table diagnostics block

Every test exercises real entry points and asserts on returned or rendered outcomes.
Behavioral verification only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from agent_workflows import render_stream
from agent_workflows.render_stream import Refusal
from agent_workflows.run_dashboard import _outcome
from agent_workflows.runner_shared import TERMINAL_STATUS_ALIASES


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


def _progress_fraction(rendered: str) -> str:
    plain = _strip_ansi(rendered)
    for line in plain.splitlines():
        if "Progress:" in line:
            match = re.search(r"Progress:\s+([0-9]+/[0-9]+)", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse progress fraction from rendered output:\n{rendered}"
    )


def _totals_fraction(rendered: str) -> str:
    plain = _strip_ansi(rendered)
    for line in plain.splitlines():
        if "Total (" in line:
            match = re.search(r"Total\s+\(([0-9]+/[0-9]+)\s+items\s+run\)", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse totals fraction from rendered output:\n{rendered}"
    )


def _extract_diag(rendered: str) -> str:
    lines = _strip_ansi(rendered).splitlines()
    diag: list[str] = []
    in_diag = False
    for line in lines:
        if "Diagnostics / Blocked Items:" in line:
            in_diag = True
            diag.append(line)
            continue
        if in_diag:
            if (
                line.strip().startswith("•")
                or line.strip().startswith("→")
                or line.strip().startswith("Stranded")
                or line.strip().startswith("Recovery")
            ):
                if line.strip().startswith("Stranded") or line.strip().startswith(
                    "Recovery"
                ):
                    break
                diag.append(line)
            elif not line.strip():
                break
            else:
                diag.append(line)
    return "\n".join(diag) if diag else ""


def _state(queue: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "run_id": "run-test-reader-sweep",
        "repo": "/repo",
        "queue": queue,
        "options": {},
    }


class CanonicalStatusReaderSweepRegressionTests(unittest.TestCase):
    """E-05: Regression tests pinning the canonical spelling and spelling-independence."""

    # -------------------------------------------------------------------------
    # Surface 1: render_stream.render_run_summary_table progress denominator
    # -------------------------------------------------------------------------

    def test_progress_denominator_frozen_not_run_and_not_attempted_equal(self) -> None:
        """(a) Frozen non-dispatched entries render Progress: 0/3 under both not-run and not-attempted."""
        queue_not_run = [
            {"id6": "skp001", "action": "skip", "status": "not-run"},
            {"id6": "skp002", "action": "skip", "status": "not-run"},
            {"id6": "exe001", "action": "execute", "status": "queued"},
        ]
        queue_not_attempted = [
            {"id6": "skp001", "action": "skip", "status": "not-attempted"},
            {"id6": "skp002", "action": "skip", "status": "not-attempted"},
            {"id6": "exe001", "action": "execute", "status": "queued"},
        ]

        rendered_not_run = render_stream.render_run_summary_table(
            _state(queue_not_run), pal=render_stream.Palette(False)
        )
        rendered_not_attempted = render_stream.render_run_summary_table(
            _state(queue_not_attempted), pal=render_stream.Palette(False)
        )

        self.assertEqual(_progress_fraction(rendered_not_run), "0/3")
        self.assertEqual(_totals_fraction(rendered_not_run), "0/3")
        self.assertEqual(_progress_fraction(rendered_not_attempted), "0/3")
        self.assertEqual(_totals_fraction(rendered_not_attempted), "0/3")

    def test_progress_denominator_spelling_independence_over_alias_table(self) -> None:
        """(a) Across all pairs in TERMINAL_STATUS_ALIASES, skip items render identical progress fractions."""
        for leg, can in sorted(TERMINAL_STATUS_ALIASES.items()):
            # Test skip items with legacy vs canonical status
            q_leg = [
                {"id6": "skp001", "action": "skip", "status": leg},
                {"id6": "exe001", "action": "execute", "status": "queued"},
            ]
            q_can = [
                {"id6": "skp001", "action": "skip", "status": can},
                {"id6": "exe001", "action": "execute", "status": "queued"},
            ]
            rend_leg = render_stream.render_run_summary_table(
                _state(q_leg), pal=render_stream.Palette(False)
            )
            rend_can = render_stream.render_run_summary_table(
                _state(q_can), pal=render_stream.Palette(False)
            )
            self.assertEqual(
                _progress_fraction(rend_leg),
                _progress_fraction(rend_can),
                f"Progress fraction disagreed for pair ({leg!r}, {can!r})",
            )

    def test_progress_denominator_completed_work_still_counted(self) -> None:
        """(a) Progress denominator guard does not suppress genuine progress."""
        queue_exec = [
            {"id6": "exe001", "action": "execute", "status": "executed"},
            {"id6": "exe002", "action": "execute", "status": "queued"},
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue_exec), pal=render_stream.Palette(False)
        )
        self.assertEqual(_progress_fraction(rendered), "1/2")
        self.assertEqual(_totals_fraction(rendered), "1/2")

    # -------------------------------------------------------------------------
    # Surface 2: run_viewer run-listing filter loop (--failed and --status)
    # -------------------------------------------------------------------------

    def test_run_viewer_failed_filter_selects_canonical_and_legacy_failures(
        self,
    ) -> None:
        """(b) aw runs --failed selects both canonical and legacy failure tokens; non-failures excluded."""
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            runs_dir = repo_path / ".aw" / "records" / "runs"
            runs_dir.mkdir(parents=True)

            # Failure tokens: canonical fail-* and legacy tokens
            failure_pairs = [
                (leg, can)
                for leg, can in sorted(TERMINAL_STATUS_ALIASES.items())
                if can != "not-run"
            ]

            run_idx = 1
            for leg, can in failure_pairs:
                r_leg = runs_dir / f"run-20261001T0100{run_idx:02d}Z-leg{run_idx:02d}"
                r_leg.mkdir()
                (r_leg / "state.json").write_text(
                    json.dumps(
                        {
                            "run_id": r_leg.name,
                            "created_at": "2026-10-01T01:00:00Z",
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": f"lg{run_idx:04d}",
                                    "action": "execute",
                                    "status": leg,
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

                r_can = runs_dir / f"run-20261001T0200{run_idx:02d}Z-can{run_idx:02d}"
                r_can.mkdir()
                (r_can / "state.json").write_text(
                    json.dumps(
                        {
                            "run_id": r_can.name,
                            "created_at": "2026-10-01T02:00:00Z",
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": f"cn{run_idx:04d}",
                                    "action": "execute",
                                    "status": can,
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                run_idx += 1

            # Non-failure runs (negative cases)
            r_exec = runs_dir / "run-20261001T030000Z-executed"
            r_exec.mkdir()
            (r_exec / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": r_exec.name,
                        "created_at": "2026-10-01T03:00:00Z",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "ex0001",
                                "action": "execute",
                                "status": "executed",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            r_not_run = runs_dir / "run-20261001T040000Z-notrun"
            r_not_run.mkdir()
            (r_not_run / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": r_not_run.name,
                        "created_at": "2026-10-01T04:00:00Z",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "nr0001",
                                "action": "skip",
                                "status": "not-run",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            res_failed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "runs",
                    "--failed",
                    "--repo",
                    str(repo_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Every failure run must appear in output
            for i in range(1, run_idx):
                self.assertIn(f"leg{i:02d}", res_failed.stdout)
                self.assertIn(f"can{i:02d}", res_failed.stdout)

            # Non-failure runs must NOT appear
            self.assertNotIn("ex0001", res_failed.stdout)
            self.assertNotIn("nr0001", res_failed.stdout)

    def test_run_viewer_status_filter_matches_both_spellings(self) -> None:
        """(b) aw runs --status matches both canonical and legacy records for the same status."""
        with tempfile.TemporaryDirectory() as td:
            repo_path = Path(td)
            runs_dir = repo_path / ".aw" / "records" / "runs"
            runs_dir.mkdir(parents=True)

            r_fv = runs_dir / "run-20261001T010000Z-1111111"
            r_fv.mkdir()
            (r_fv / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": r_fv.name,
                        "created_at": "2026-10-01T01:00:00Z",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "fv0001",
                                "action": "execute",
                                "status": "fail-verify",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            r_pr = runs_dir / "run-20261001T020000Z-2222222"
            r_pr.mkdir()
            (r_pr / "state.json").write_text(
                json.dumps(
                    {
                        "run_id": r_pr.name,
                        "created_at": "2026-10-01T02:00:00Z",
                        "queue": [
                            {
                                "position": 1,
                                "id6": "pr0002",
                                "action": "execute",
                                "status": "partial",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            res_can = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "runs",
                    "--status",
                    "fail-verify",
                    "--repo",
                    str(repo_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("1111111", res_can.stdout)
            self.assertIn("2222222", res_can.stdout)

            res_leg = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agent_workflows",
                    "runs",
                    "--status",
                    "partial",
                    "--repo",
                    str(repo_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("1111111", res_leg.stdout)
            self.assertIn("2222222", res_leg.stdout)

    # -------------------------------------------------------------------------
    # Surface 3: run_dashboard._outcome disposition classification
    # -------------------------------------------------------------------------

    def test_run_dashboard_outcome_dispositions(self) -> None:
        """(c) run_dashboard._outcome classifies runner failure dispositions as failed."""
        self.assertEqual(_outcome("fail-lane", "main", None), "failed")
        self.assertEqual(_outcome("fail-begin", "main", None), "failed")
        self.assertEqual(_outcome("fail-gate", "main", None), "failed")
        self.assertEqual(_outcome("dependency-blocked", "main", None), "failed")
        self.assertEqual(_outcome("merge-needs-human", "main", None), "failed")
        self.assertEqual(_outcome("fail-depend", "main", None), "failed")
        self.assertEqual(_outcome("fail-merge", "main", None), "failed")
        self.assertEqual(_outcome("executed", "main", None), "success")

    def test_run_dashboard_outcome_alias_independence_and_exemptions(self) -> None:
        """(c) _outcome agrees for all alias pairs except the two deliberate partial exemptions."""
        # DELIBERATE EXEMPTIONS (OQ-03, E-04):
        # TERMINAL_STATUS_ALIASES is lossy for _outcome's three-way collapse:
        # canonical_terminal_status("partial") is "fail-verify" and
        # canonical_terminal_status("substantially-complete") is "fail-gate".
        # Folding them would destroy the shipped "partial" dashboard verdict,
        # so _outcome evaluates the raw token for ("substantially-complete", "partial") first.
        # These two pairs are asserted as asymmetric-by-design.
        self.assertEqual(_outcome("partial", "main", None), "partial")
        self.assertEqual(_outcome("fail-verify", "main", None), "failed")
        self.assertEqual(_outcome("substantially-complete", "main", None), "partial")
        self.assertEqual(_outcome("fail-gate", "main", None), "failed")

        exempt_pairs = {
            ("partial", "fail-verify"),
            ("substantially-complete", "fail-gate"),
        }

        for leg, can in sorted(TERMINAL_STATUS_ALIASES.items()):
            if (leg, can) in exempt_pairs:
                continue
            out_leg = _outcome(leg, "main", None)
            out_can = _outcome(can, "main", None)
            self.assertEqual(
                out_leg,
                out_can,
                f"_outcome disagreed for non-exempt pair ({leg!r}, {can!r}): {out_leg} != {out_can}",
            )

    # -------------------------------------------------------------------------
    # Surface 4: render_stream.render_run_summary_table diagnostics block
    # -------------------------------------------------------------------------

    def test_diagnostics_block_renders_for_canonical_and_legacy(self) -> None:
        """(d) Diagnostics block renders reason for both canonical and legacy status tokens."""
        state_fs = _state(
            [
                {
                    "id6": "item01",
                    "status": "failed-safely",
                    "driver_error": "driver boom",
                }
            ]
        )
        state_fg = _state(
            [{"id6": "item01", "status": "fail-gate", "driver_error": "driver boom"}]
        )
        state_mr = _state(
            [
                {
                    "id6": "item02",
                    "status": "merge-refused",
                    "integration_deferral": "base moved",
                }
            ]
        )
        state_fm = _state(
            [
                {
                    "id6": "item02",
                    "status": "fail-merge",
                    "integration_deferral": "base moved",
                }
            ]
        )

        out_fs = render_stream.render_run_summary_table(
            state_fs, pal=render_stream.Palette(False)
        )
        out_fg = render_stream.render_run_summary_table(
            state_fg, pal=render_stream.Palette(False)
        )
        out_mr = render_stream.render_run_summary_table(
            state_mr, pal=render_stream.Palette(False)
        )
        out_fm = render_stream.render_run_summary_table(
            state_fm, pal=render_stream.Palette(False)
        )

        diag_fs = _extract_diag(out_fs)
        diag_fg = _extract_diag(out_fg)
        diag_mr = _extract_diag(out_mr)
        diag_fm = _extract_diag(out_fm)

        self.assertIn("Diagnostics / Blocked Items:", diag_fs)
        self.assertIn("driver boom", diag_fs)
        self.assertIn("Diagnostics / Blocked Items:", diag_fg)
        self.assertIn("driver boom", diag_fg)

        self.assertIn("Diagnostics / Blocked Items:", diag_mr)
        self.assertIn("base moved", diag_mr)
        self.assertIn("Diagnostics / Blocked Items:", diag_fm)
        self.assertIn("base moved", diag_fm)

    def test_diagnostics_block_arm_precedence_refusal_wins(self) -> None:
        """(d) Diagnostics block: Refusal record wins over integration_deferral fallback."""
        refusal = Refusal(
            code="git-merge-conflict",
            reason="conflict in file.py",
            remedy="resolve conflict by hand",
        )
        item_refusal = {
            "id6": "item03",
            "status": "fail-merge",
            "refusal": refusal.to_dict(),
            "integration_deferral": "fallback deferral message",
        }
        state = _state([item_refusal])
        rendered = render_stream.render_run_summary_table(
            state, pal=render_stream.Palette(False)
        )
        diag = _extract_diag(rendered)

        self.assertIn("conflict in file.py", diag)
        self.assertIn("resolve conflict by hand", diag)
        self.assertNotIn("fallback deferral message", diag)

    def test_diagnostics_block_full_legacy_sweep(self) -> None:
        """(d) Diagnostics block: legacy tokens render reasons without regression."""
        leg_statuses = [
            "failed-safely",
            "integration-blocked",
            "merge-conflict",
            "merge-needs-human",
            "merge-refused",
            "merge-retry",
            "merge-unchecked",
        ]
        for st in leg_statuses:
            # Check integration_deferral arm
            state_def = _state(
                [
                    {
                        "id6": "it02",
                        "status": st,
                        "integration_deferral": f"deferral-{st}",
                    }
                ]
            )
            rend_def = render_stream.render_run_summary_table(
                state_def, pal=render_stream.Palette(False)
            )
            diag_def = _extract_diag(rend_def)
            if st != "failed-safely":
                # failed-safely is not in integration_deferral arm
                self.assertIn(
                    f"deferral-{st}", diag_def, f"Expected deferral reason for {st}"
                )
            else:
                self.assertEqual(
                    diag_def, "", "failed-safely should not render in deferral arm"
                )

            # Check driver_error arm
            state_drv = _state(
                [{"id6": "it01", "status": st, "driver_error": f"driver-{st}"}]
            )
            rend_drv = render_stream.render_run_summary_table(
                state_drv, pal=render_stream.Palette(False)
            )
            diag_drv = _extract_diag(rend_drv)
            if st in (
                "failed-safely",
                "integration-blocked",
                "merge-conflict",
                "merge-needs-human",
                "merge-refused",
            ):
                self.assertIn(
                    f"driver-{st}", diag_drv, f"Expected driver error for {st}"
                )
            else:
                self.assertEqual(
                    diag_drv, "", f"{st} should not render in driver_error arm"
                )
