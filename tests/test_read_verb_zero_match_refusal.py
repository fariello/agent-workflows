"""Behavioral tests for read-verb zero-match selector refusal (IPD yxsfjc E-08).

Asserts on exit codes, stdout/stderr bytes, and parsed records only. Never asserts on
source code text or inspect (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import agent_schema, cli


class ReadVerbZeroMatchRefusalTests(unittest.TestCase):
    """Behavioral test suite driving read verbs through cli.main across all surfaces."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_zero_match_")
        self.repo_root = Path(self.temp_dir)

        # Plans
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.p1_path = plans_dir / "20261012-test-01-p10001-plan-one.ipd.md"
        self.p1_content = (
            "# IPD: Plan One\n\n"
            "- Id: p10001\n"
            "- Status: to-review\n"
            "- Readiness: no-go\n"
            "- Set: test\n"
            "- Order: 1\n"
            "- From-Backlog: b10001\n\n"
            "## Open questions\nNone\n"
        )
        self.p1_path.write_text(self.p1_content, encoding="utf-8")

        self.p2_path = plans_dir / "20261012-test-02-p20002-plan-two.ipd.md"
        self.p2_content = (
            "# IPD: Plan Two\n\n"
            "- Id: p20002\n"
            "- Status: to-review\n"
            "- Set: test\n"
            "- Order: 2\n\n"
            "## Open questions\nNone\n"
        )
        self.p2_path.write_text(self.p2_content, encoding="utf-8")

        # Backlog
        backlog_dir = self.repo_root / ".aw" / "records" / "backlog" / "open"
        backlog_dir.mkdir(parents=True, exist_ok=True)
        (backlog_dir / "20261012-test-01-b10001-item.backlog.md").write_text(
            "# Backlog: Item One\n\n- Id: b10001\n- Status: open\n\nContent.\n",
            encoding="utf-8",
        )
        (backlog_dir / "20261012-test-02-b20002-item.backlog.md").write_text(
            "# Backlog: Item Two\n\n- Id: b20002\n- Status: open\n\nNon-plan.\n",
            encoding="utf-8",
        )

        # Reviews
        reviews_dir = self.repo_root / ".aw" / "records" / "reviews"
        reviews_dir.mkdir(parents=True, exist_ok=True)
        self.r1_path = reviews_dir / "20261012-test-01-p10001-plan-one.review.md"
        self.r1_content = (
            "# Review findings: plan p10001\n\n"
            "- Subject-Id: p10001\n"
            "- Subject-Type: ipd\n"
            "- Reviewed-At: 2026-10-12\n"
            "- Reviewer: test-agent\n"
            "- Verdict: APPROVE\n\n"
            "## Round 1\n\n"
            "### Decisions\n\n"
            "| ID | Question | Chosen | Alternatives considered | Basis | Reversible |\n"
            "|----|----------|--------|-------------------------|-------|------------|\n"
            "| D-1 | Question 1? | Yes | No | Reversible basis | yes |\n"
            "| D-2 | Question 2? | No | Yes | Irreversible basis | no |\n"
        )
        self.r1_path.write_text(self.r1_content, encoding="utf-8")

        # History sidecar
        history_file = self.repo_root / ".aw" / "records" / "history.jsonl"
        history_file.write_text(
            json.dumps(
                {
                    "id6": "p10001",
                    "date": "2026-10-12",
                    "workflow": "review",
                    "actor": "agent",
                    "message": "reviewed p10001",
                }
            )
            + "\n"
            + json.dumps(
                {
                    "id6": "orph01",
                    "date": "2026-10-12",
                    "workflow": "archive",
                    "actor": "agent",
                    "message": "archived without artifact",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _invoke(
        self, argv: list[str], repo: Path | None = None
    ) -> tuple[int, str, str]:
        buf = io.StringIO()
        err = io.StringIO()
        target_repo = repo or self.repo_root
        with patch("sys.stdout", buf), patch("sys.stderr", err):
            rc = cli.main(argv + ["--dir", str(target_repo)])
        return rc, buf.getvalue(), err.getvalue()

    def test_unknown_token_refusal_across_all_verbs_and_surfaces(self) -> None:
        """UNKNOWN token zzzzzz exits 2 with cannot-run across all 4 verbs and 3 surfaces."""
        verbs = [
            ("reviews decisions", ["reviews", "decisions"]),
            ("record-history", ["record-history"]),
            ("graduation", ["graduation"]),
            ("ipd recheck-readiness", ["ipd", "recheck-readiness"]),
        ]
        surfaces = [
            ("human", []),
            ("agent", ["--agent"]),
            ("json", ["--json"]),
        ]

        for verb_name, prefix in verbs:
            for surface_name, flags in surfaces:
                with self.subTest(verb=verb_name, surface=surface_name):
                    rc, out, err = self._invoke(prefix + ["zzzzzz"] + flags)
                    self.assertEqual(
                        rc,
                        2,
                        f"{verb_name} on {surface_name} should exit 2 for unknown token",
                    )

                    if surface_name == "human":
                        self.assertEqual(
                            out,
                            "",
                            f"{verb_name} human stdout should be empty on zero-match refusal",
                        )
                        self.assertIn("zzzzzz", err)
                        self.assertNotIn("Proceed.", err)
                        self.assertNotIn("Proceed.", out)
                    elif surface_name == "agent":
                        record = json.loads(out)
                        agent_schema.assert_valid_agent_record(record)
                        self.assertEqual(record["kind"], "error")
                        self.assertEqual(record["outcome"], "cannot-run")
                        self.assertEqual(record["exit"], 2)
                        self.assertFalse(record["verified"])
                        self.assertFalse(record["complete"])
                        self.assertIn("zzzzzz", record["unresolved_selectors"])
                        self.assertIn("zzzzzz", record["unresolved_targets"])
                    elif surface_name == "json":
                        data = json.loads(out)
                        self.assertEqual(data["exit_code"], 2)
                        self.assertEqual(data["status"], "cannot-run")
                        self.assertFalse(data["verified"])
                        self.assertFalse(data["complete"])
                        self.assertIn("zzzzzz", data["data"]["unresolved_selectors"])
                        self.assertIn("zzzzzz", data["data"]["unresolved_targets"])

    def test_real_but_empty_token_across_all_verbs(self) -> None:
        """REAL-BUT-EMPTY tokens exit 0 and return clean empty answers."""
        # reviews decisions: p20002 has no review record
        rc, out, err = self._invoke(["reviews", "decisions", "p20002"])
        self.assertEqual(rc, 0)
        self.assertIn("no review record matches `p20002`", out)
        self.assertEqual(err, "")

        # record-history: p20002 has no history in sidecar
        rc, out, err = self._invoke(["record-history", "p20002"])
        self.assertEqual(rc, 0)
        self.assertIn("no sidecar history for id6 p20002", out)
        self.assertEqual(err, "")

        # graduation: p20002 has no linking plan or spec
        rc, out, err = self._invoke(["graduation", "p20002"])
        self.assertEqual(rc, 0)
        self.assertIn(
            "nothing yet: no plan or spec links to source p20002. Proceed.", out
        )
        self.assertEqual(err, "")

    def test_vocabulary_tokens_not_refused(self) -> None:
        """VOCABULARY token 'approved' is exempt as a standing question and not refused."""
        for cmd in [
            ["reviews", "decisions", "approved"],
            ["record-history", "approved"],
            ["graduation", "approved"],
            ["ipd", "recheck-readiness", "approved"],
        ]:
            with self.subTest(cmd=cmd):
                rc, out, err = self._invoke(cmd)
                self.assertEqual(rc, 0, f"{cmd} should exit 0")

    def test_matching_tokens_exit_0(self) -> None:
        """MATCHING tokens exit 0 with their normal populated outputs."""
        # reviews decisions: p10001 has decisions
        rc, out, err = self._invoke(["reviews", "decisions", "p10001"])
        self.assertEqual(rc, 0)
        self.assertIn("Question 1?", out)
        self.assertIn("Question 2?", out)

        # record-history: p10001 has history
        rc, out, err = self._invoke(["record-history", "p10001"])
        self.assertEqual(rc, 0)
        self.assertIn("reviewed p10001", out)

        # graduation: b10001 is cited by p10001
        rc, out, err = self._invoke(["graduation", "b10001"])
        self.assertEqual(rc, 0)
        self.assertIn("p10001", out)

        # ipd recheck-readiness: p10001 re-checked
        rc, out, err = self._invoke(["ipd", "recheck-readiness", "p10001"])
        self.assertEqual(rc, 0)
        self.assertIn("p10001", out)

    def test_reviews_decisions_irreversible_not_refused(self) -> None:
        """reviews decisions --irreversible with matching selector does not refuse."""
        rc, out, err = self._invoke(
            ["reviews", "decisions", "p10001", "--irreversible"]
        )
        self.assertEqual(rc, 0)
        self.assertIn("Question 2?", out)
        self.assertNotIn("Question 1?", out)

    def test_record_history_orphan_with_sidecar_records(self) -> None:
        """record-history for an id6 with sidecar entries but no artifact prints them at exit 0."""
        rc, out, err = self._invoke(["record-history", "orph01"])
        self.assertEqual(rc, 0)
        self.assertIn("archived without artifact", out)

    def test_graduation_kind_does_not_change_existence_judgment(self) -> None:
        """graduation --kind narrows links only and does not cause a refusal for a real source."""
        # b10001 is a backlog item, so --kind spec finds zero spec links, but does not refuse
        rc, out, err = self._invoke(["graduation", "b10001", "--kind", "spec"])
        self.assertEqual(rc, 0)
        self.assertIn(
            "nothing yet: no plan or spec links to source b10001. Proceed.", out
        )

    def test_recheck_readiness_mixed_invocation_refuses_before_mutation(
        self,
    ) -> None:
        """ipd recheck-readiness with mixed tokens refuses at exit 2 before mutating anything."""
        rc, out, err = self._invoke(
            [
                "ipd",
                "recheck-readiness",
                "p10001",
                "zzzzzz",
                "--apply",
                "--stale-findings",
            ]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn("zzzzzz", err)
        # Content remains byte-identical
        self.assertEqual(self.p1_path.read_text(encoding="utf-8"), self.p1_content)
        self.assertEqual(self.r1_path.read_text(encoding="utf-8"), self.r1_content)

    def test_recheck_readiness_non_plan_artifact_exits_2(self) -> None:
        """ipd recheck-readiness on a real non-plan artifact id6 (F-12) exits 2."""
        # Human surface
        rc, out, err = self._invoke(["ipd", "recheck-readiness", "b20002"])
        self.assertEqual(rc, 2)
        self.assertIn("error: selector matched no plan: b20002", err)

        # Agent surface
        rc_agent, out_agent, err_agent = self._invoke(
            ["ipd", "recheck-readiness", "b20002", "--agent"]
        )
        self.assertEqual(rc_agent, 2)
        agent_data = json.loads(out_agent)
        self.assertEqual(agent_data["kind"], "error")
        self.assertEqual(agent_data["outcome"], "cannot-run")
        self.assertEqual(agent_data["exit"], 2)

        # JSON surface
        rc_json, out_json, err_json = self._invoke(
            ["ipd", "recheck-readiness", "b20002", "--json"]
        )
        self.assertEqual(rc_json, 2)
        json_data = json.loads(out_json)
        self.assertEqual(json_data["status"], "cannot-run")
        self.assertEqual(json_data["exit_code"], 2)

    def test_reviews_decisions_unknown_in_empty_reviews_repo_exits_2(
        self,
    ) -> None:
        """reviews decisions <unknown> exits 2 even in a repository with zero review records."""
        empty_dir = tempfile.mkdtemp(prefix="aw_test_empty_reviews_")
        try:
            empty_root = Path(empty_dir)
            rc, out, err = self._invoke(
                ["reviews", "decisions", "zzzzzz"], repo=empty_root
            )
            self.assertEqual(rc, 2)
            self.assertEqual(out, "")
            self.assertIn("zzzzzz", err)
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_agent_surface_home_path_redaction(self) -> None:
        """Home-path prefixes in unknown selectors are redacted in the --agent record."""
        fake_home = "/home/" + "testuser/secretplan"  # split: leak guard
        rc, out, err = self._invoke(["reviews", "decisions", fake_home, "--agent"])
        self.assertEqual(rc, 2)
        self.assertNotIn("/home/" + "testuser", out)
        record = json.loads(out)
        agent_schema.assert_valid_agent_record(record)
        self.assertIn("~/secretplan", record["unresolved_selectors"])
        self.assertIn("~/secretplan", record["unresolved_targets"])
        self.assertIn("~/secretplan", record["error"])


if __name__ == "__main__":
    unittest.main()
