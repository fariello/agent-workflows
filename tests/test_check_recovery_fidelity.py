"""Tests for plan wef7yo: check CLI recovery fidelity.

Pins the property that `aw check --json` machine findings preserve the rule-authored
`Drift.recovery` verbatim, without being overwritten or fabricated by human remediation
prose from `doctor.build_remediation`.

Covers:
- Populated engine recovery case (witness 1: check.live-bug-ungated)
- Empty engine recovery case (witness 2: check.name-nonconformant)
- Human/agent surface guard (agent record 'next' field preserves human remediation prose)
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agent_workflows import check_engine as ce
from agent_workflows import cli
from agent_workflows import doctor as _doctor
from agent_workflows.term import Term
from tests.test_check_engine_release_gate import _create_minimal_repo


class TestCheckRecoveryFidelity(unittest.TestCase):
    """Hermetic tests ensuring machine finding recovery fidelity via cli._run_check."""

    def test_machine_finding_recovery_fidelity_populated_case(self) -> None:
        """A rule with populated recovery publishes the engine's recovery verbatim."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )

            # Derive engine drift at run time (never hard-code literals)
            engine_drifts = ce.check_release_gates(repo)
            self.assertEqual(len(engine_drifts), 1)
            expected_drift = engine_drifts[0]
            self.assertEqual(expected_drift.rule, "check.live-bug-ungated")
            self.assertTrue(expected_drift.recovery)

            # Drive real CLI through _run_check with json=True
            args = argparse.Namespace(
                command="check",
                type="release-gates",
                dir=str(repo),
                all=False,
                agent=False,
                json=True,
                selector=[],
                strict_setid_length=False,
            )
            term = Term(color=False)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli._run_check(args, term)

            self.assertEqual(rc, 1)
            output = json.loads(buf.getvalue())
            findings = output["data"]["policy_findings"]
            self.assertEqual(len(findings), 1)

            published_finding = findings[0]
            self.assertEqual(published_finding["rule"], "check.live-bug-ungated")

            # (a) published recovery equals the engine Drift.recovery verbatim
            self.assertEqual(published_finding["recovery"], expected_drift.recovery)

    def test_machine_finding_recovery_fidelity_empty_case(self) -> None:
        """A rule with empty recovery publishes empty string, not fabricated human prose."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bad_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "badly-named-file.backlog.md"
            )
            bad_file.write_text(
                "- Id: bad001\n"
                "- Status: open\n"
                "- Set: bad001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Bad file name\n",
                encoding="utf-8",
            )

            # Derive engine drift and doctor human fix at run time
            engine_drifts = ce.check_types(repo, ["backlog"])
            drift_by_rule = {d.rule: d for d in engine_drifts}
            self.assertIn("check.name-nonconformant", drift_by_rule)
            expected_drift = drift_by_rule["check.name-nonconformant"]

            # Confirm engine recovery is empty for this rule
            self.assertEqual(expected_drift.recovery, "")

            # Compute human prose from doctor
            human_rem = _doctor.build_remediation(expected_drift, repo)
            self.assertTrue(human_rem.detailed_fix)

            # Drive real CLI through _run_check with json=True
            args = argparse.Namespace(
                command="check",
                type="backlog",
                dir=str(repo),
                all=False,
                agent=False,
                json=True,
                selector=[],
                strict_setid_length=False,
            )
            term = Term(color=False)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli._run_check(args, term)

            self.assertEqual(rc, 1)
            output = json.loads(buf.getvalue())
            findings = output["data"]["policy_findings"]
            finding_by_rule = {f["rule"]: f for f in findings}
            self.assertIn("check.name-nonconformant", finding_by_rule)

            published_finding = finding_by_rule["check.name-nonconformant"]

            # (c) published recovery equals engine Drift.recovery and is falsy (not fabricated)
            self.assertEqual(published_finding["recovery"], expected_drift.recovery)
            self.assertFalse(published_finding["recovery"])

            # (b) published recovery does NOT equal human remediation prose
            self.assertNotEqual(published_finding["recovery"], human_rem.detailed_fix)

    def test_human_and_agent_surface_fidelity_guard(self) -> None:
        """The human surface (--agent next field) still reflects human remediation prose."""
        with TemporaryDirectory() as tmp:
            repo = _create_minimal_repo(Path(tmp))
            bug_file = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20260920-bug001-01-bug001-test-defect.backlog.md"
            )
            bug_file.write_text(
                "- Id: bug001\n"
                "- Status: open\n"
                "- Set: bug001\n"
                "- Priority: medium\n"
                "- Work-Kind: bug\n"
                "- Summary: Live ungated bug\n",
                encoding="utf-8",
            )

            engine_drifts = ce.check_release_gates(repo)
            self.assertEqual(len(engine_drifts), 1)
            expected_drift = engine_drifts[0]
            human_rem = _doctor.build_remediation(expected_drift, repo)

            # Drive real CLI through _run_check with agent=True
            args = argparse.Namespace(
                command="check",
                type="release-gates",
                dir=str(repo),
                all=False,
                agent=True,
                json=False,
                selector=[],
                strict_setid_length=False,
            )
            term = Term(color=False)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli._run_check(args, term)

            self.assertEqual(rc, 1)

            # Parse agent record
            agent_record = None
            for line in buf.getvalue().splitlines():
                try:
                    parsed = json.loads(line)
                    if parsed.get("cmd") == "check":
                        agent_record = parsed
                        break
                except Exception:
                    pass

            self.assertIsNotNone(agent_record)
            # (d) agent record 'next' still matches human prose string
            self.assertEqual(agent_record["next"], human_rem.detailed_fix)


if __name__ == "__main__":
    unittest.main()
