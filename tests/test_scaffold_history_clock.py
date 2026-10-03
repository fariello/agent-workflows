"""Outcome tests for the scaffold's workflow history clock parity (IPD 9wcei0).

Asserts that `aw ipd scaffold` stamps a new plan's `draft` history record from the
UTC clock per spec `2vev8j` Section 4.4, while leaving human-facing timestamp names
(the `- Date:` metadata field and the filename prefix) on the LOCAL clock per
`DECISIONS.md` D55.

Validates that:
1. Under timezones east and west of UTC, the recorded `draft` date equals UTC.
2. The filename prefix and `- Date:` front-matter field equal local date.
3. Both the derived-name branch and explicit `--path` branch of `run_scaffold` conform.
4. `check_engine.check_lifecycle_transitions` returns no `check.lifecycle-transition-invalid`
   finding across all three lifecycle states:
   - scaffold only (draft)
   - scaffold + one transition (draft -> to-review)
   - scaffold + two transitions (draft -> to-review -> reviewed)
5. Timezone changes are isolated to the code under test via a context manager with an
   unconditional restore in a `finally` block, avoiding process pollution under
   `pytest-randomly` / `pytest-xdist`.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import os
import re
import tempfile
import time
import unittest
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import ipd_authoring as A
from agent_workflows import status_set as SS


@contextlib.contextmanager
def temporary_timezone(tz: str):
    """Context manager setting process TZ for code under test with unconditional restore."""
    old_tz = os.environ.get("TZ")
    os.environ["TZ"] = tz
    time.tzset()
    try:
        yield
    finally:
        if old_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = old_tz
        time.tzset()


@contextlib.contextmanager
def temporary_cwd(target: Path):
    """Context manager switching current working directory with unconditional restore."""
    old_cwd = Path.cwd()
    os.chdir(target)
    try:
        yield
    finally:
        os.chdir(old_cwd)


class ScaffoldHistoryClockTests(unittest.TestCase):
    """Behavioral outcome guard for the scaffold history clock and lifecycle validity."""

    # POSIX fixed-offset timezones that stay in the skew window across all wall-clock hours:
    # XXX-24 (UTC+24): local date is always one day ahead of UTC.
    # XXX+23:59 (UTC-23:59): local date is one day behind UTC except during the final minute of UTC day.
    EAST_TZ = "XXX-24"
    WEST_TZ = "XXX+23:59"

    def _setup_repo(self, tmpdir: Path) -> tuple[Path, Path]:
        repo = tmpdir / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        pending = repo / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        cfg = repo / ".aw" / "config"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "project.json").write_text('{"schema_version": 2}', encoding="utf-8")
        return repo, pending

    def _extract_plan_details(self, plan_path: Path) -> tuple[str, str, str]:
        """Extract (- Date:, draft_history_date, plan_id) from plan markdown."""
        text = plan_path.read_text(encoding="utf-8")
        front_date = ""
        draft_date = ""
        plan_id = ""
        for line in text.splitlines():
            if line.startswith("- Date:"):
                front_date = line.split(":", 1)[1].strip()
            elif line.startswith("- Id:"):
                plan_id = line.split(":", 1)[1].strip()
            elif "draft" in line and "created." in line:
                m = re.search(r"-\s+(\d{4}-\d{2}-\d{2})\s+draft", line)
                if m:
                    draft_date = m.group(1)
        return front_date, draft_date, plan_id

    def _run_state_check(
        self,
        *,
        tz: str,
        state: str,
        explicit_path: bool = False,
    ):
        with temporary_timezone(tz):
            local_date = datetime.date.today().strftime("%Y-%m-%d")
            local_compact = datetime.date.today().strftime("%Y%m%d")
            utc_date = (
                datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y-%m-%d")
            )

            # Precondition: fail loudly if zone is not in skew window
            self.assertNotEqual(
                local_date,
                utc_date,
                f"Precondition failed: local_date {local_date} must differ from utc_date {utc_date} under {tz}",
            )

            with tempfile.TemporaryDirectory() as td:
                tmpdir = Path(td)
                repo, pending = self._setup_repo(tmpdir)

                with temporary_cwd(repo):
                    target_arg = None
                    if explicit_path:
                        plan_file = (
                            pending
                            / f"{local_compact}-probeset-01-xxxx01-probe-plan.ipd.md"
                        )
                        target_arg = str(plan_file)

                    args = argparse.Namespace(
                        kind="child",
                        title="Probe Plan",
                        path=target_arg,
                        set="probeset",
                        order=1,
                        author="probe/agent",
                        priority="low",
                        work_kind="chore",
                        apply=True,
                    )
                    rc = A.run_scaffold(args)
                    self.assertEqual(rc, 0, "run_scaffold must succeed")

                    plans = list(pending.glob("*.ipd.md"))
                    self.assertEqual(
                        len(plans), 1, "exactly one plan must be scaffolded"
                    )
                    plan_path = plans[0]

                    # Filename date prefix must remain local per DECISIONS.md D55
                    self.assertTrue(
                        plan_path.name.startswith(local_compact),
                        f"Plan filename '{plan_path.name}' must start with local date {local_compact}",
                    )

                    front_date, draft_date, plan_id = self._extract_plan_details(
                        plan_path
                    )

                    # - Date: front-matter metadata field must remain local per DECISIONS.md D55
                    self.assertEqual(
                        front_date,
                        local_date,
                        f"- Date: field must be local {local_date}, got {front_date}",
                    )

                    # Perform lifecycle transitions based on target state
                    if state in ("one_transition", "two_transitions"):
                        rec = SS.read_artifact_record(plan_path, repo)
                        self.assertIsNotNone(rec)
                        ns1 = argparse.Namespace(actor="aw set", message="to to-review")
                        plan_path, _ = SS.apply_status_change(
                            rec, "to-review", repo, ns1
                        )

                    if state == "two_transitions":
                        rec = SS.read_artifact_record(plan_path, repo)
                        self.assertIsNotNone(rec)
                        ns2 = argparse.Namespace(actor="aw set", message="reviewed ok")
                        plan_path, _ = SS.apply_status_change(
                            rec, "reviewed", repo, ns2
                        )

                    # Check lifecycle transitions through check_engine
                    drift = ce.check_lifecycle_transitions(repo, include_untracked=True)
                    invalid_drifts = [
                        d
                        for d in drift
                        if d.rule == "check.lifecycle-transition-invalid"
                    ]

                    # Collect failure causes to report both date and checker errors together
                    errors = []
                    if draft_date != utc_date:
                        errors.append(
                            f"draft history date must be UTC {utc_date}, got {draft_date} (local: {local_date})"
                        )
                    if invalid_drifts:
                        errors.append(
                            f"check.lifecycle-transition-invalid findings: {[d.detail for d in invalid_drifts]}"
                        )

                    self.assertEqual(
                        errors,
                        [],
                        f"Scaffold history clock failure for state '{state}' under TZ={tz}: {errors}",
                    )

    def test_east_timezone_scaffold_only(self):
        """East of UTC (local > UTC): scaffold alone is checked."""
        self._run_state_check(tz=self.EAST_TZ, state="scaffold_only")

    def test_east_timezone_one_transition(self):
        """East of UTC (local > UTC): scaffold + to-review fires check failure when unfixed."""
        self._run_state_check(tz=self.EAST_TZ, state="one_transition")

    def test_east_timezone_two_transitions(self):
        """East of UTC (local > UTC): scaffold + to-review + reviewed is checked."""
        self._run_state_check(tz=self.EAST_TZ, state="two_transitions")

    def test_west_timezone_scaffold_only(self):
        """West of UTC (local < UTC): scaffold alone is checked."""
        self._run_state_check(tz=self.WEST_TZ, state="scaffold_only")

    def test_west_timezone_one_transition(self):
        """West of UTC (local < UTC): scaffold + to-review is checked."""
        self._run_state_check(tz=self.WEST_TZ, state="one_transition")

    def test_west_timezone_two_transitions(self):
        """West of UTC (local < UTC): scaffold + to-review + reviewed is checked."""
        self._run_state_check(tz=self.WEST_TZ, state="two_transitions")

    def test_explicit_path_branch_east(self):
        """Scaffold with explicit --path branch under east timezone records UTC history date."""
        self._run_state_check(
            tz=self.EAST_TZ, state="one_transition", explicit_path=True
        )

    def test_explicit_path_branch_west(self):
        """Scaffold with explicit --path branch under west timezone records UTC history date."""
        self._run_state_check(
            tz=self.WEST_TZ, state="one_transition", explicit_path=True
        )


if __name__ == "__main__":
    unittest.main()
