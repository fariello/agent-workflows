"""Regression and contract conformance tests for aw show.

Asserts on exit codes, stdout/stderr streams, and parsed agent/json payloads.
No test reads production source (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import agent_schema, cli, command_surface
from tests import conformance_matrix
from tests.record_builder import RecordBuilder


class CliShowCommandTests(unittest.TestCase):
    """Behavioral tests for aw show across human, --agent, and --json surfaces."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aw_test_show_")
        self.repo_root = Path(self.temp_dir).resolve()

        # 1. Plans (displayed by aw show)
        plans_dir = self.repo_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True, exist_ok=True)
        self.p1_path = plans_dir / "20261014-showtest-01-p99001-sample-plan.ipd.md"
        self.p1_content = RecordBuilder().plan(
            title="Sample Plan",
            id6="p99001",
            status="to-review",
            set="showtest",
            order=1,
            body="Plan details.\n",
            text_only=True,
        )
        self.p1_path.write_text(self.p1_content, encoding="utf-8")

        # 2. Backlog (displayed by aw show)
        backlog_dir = self.repo_root / ".aw" / "records" / "backlog" / "open"
        backlog_dir.mkdir(parents=True, exist_ok=True)
        self.b1_path = (
            backlog_dir / "20261014-showtest-01-b99001-sample-item.backlog.md"
        )
        self.b1_content = RecordBuilder().backlog(
            id6="b99001",
            status="open",
            set="showtest",
            summary="Sample Item",
            body="Item details.\n",
            text_only=True,
        )
        self.b1_path.write_text(self.b1_content, encoding="utf-8")

        # 3. Releases (real artifact tree NOT searched/displayed by aw show)
        releases_dir = self.repo_root / ".aw" / "records" / "releases"
        releases_dir.mkdir(parents=True, exist_ok=True)
        self.rel_id6 = "r99001"
        self.rel_path = (
            releases_dir
            / f"20261014-{self.rel_id6}-01-{self.rel_id6}-v1-0-0.release.md"
        )
        self.rel_content = RecordBuilder().release(
            id6=self.rel_id6,
            version="1.0.0",
            status="shipped",
            body="# Release: 1.0.0\n\nRelease body.\n",
            text_only=True,
        )
        self.rel_path.write_text(self.rel_content, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _invoke(
        self, argv: list[str], repo: Path | None = None
    ) -> tuple[int, str, str]:
        buf = io.StringIO()
        err = io.StringIO()
        target_repo = repo or self.repo_root
        with patch("sys.stdout", buf), patch("sys.stderr", err):
            rc = cli.main(["show"] + argv + ["--dir", str(target_repo)])
        return rc, buf.getvalue(), err.getvalue()

    def test_unknown_token_refusal_across_all_surfaces(self) -> None:
        """Case 1: UNKNOWN non-vocabulary token (zzzzzz) exits 2 on all surfaces."""
        # Human surface
        rc_human, out_human, err_human = self._invoke(["zzzzzz"])
        self.assertEqual(rc_human, 2)
        self.assertEqual(out_human, "")
        self.assertIn("zzzzzz", err_human)
        self.assertIn("aw find", err_human)

        # Agent surface
        rc_agent, out_agent, err_agent = self._invoke(["zzzzzz", "--agent"])
        self.assertEqual(rc_agent, 2)
        self.assertEqual(err_agent, "")
        agent_data = json.loads(out_agent)
        agent_schema.assert_valid_agent_record(agent_data)
        self.assertEqual(agent_data["kind"], "error")
        self.assertEqual(agent_data["cmd"], "show")
        self.assertEqual(agent_data["outcome"], "cannot-run")
        self.assertEqual(agent_data["exit"], 2)
        self.assertFalse(agent_data["verified"])
        self.assertFalse(agent_data["complete"])
        self.assertEqual(agent_data["unresolved_selectors"], ["zzzzzz"])
        self.assertEqual(agent_data["unresolved_targets"], ["zzzzzz"])
        self.assertIn("zzzzzz", agent_data["error"])
        self.assertEqual(agent_data["next"], "aw find")

        # JSON surface
        rc_json, out_json, err_json = self._invoke(["zzzzzz", "--json"])
        self.assertEqual(rc_json, 2)
        self.assertEqual(err_json, "")
        json_data = json.loads(out_json)
        self.assertEqual(json_data["status"], "cannot-run")
        self.assertEqual(json_data["exit_code"], 2)
        self.assertFalse(json_data["verified"])
        self.assertFalse(json_data["complete"])
        self.assertEqual(json_data["data"]["unresolved_selectors"], ["zzzzzz"])
        self.assertEqual(json_data["data"]["unresolved_targets"], ["zzzzzz"])

    def test_home_path_redaction_across_all_surfaces(self) -> None:
        """Case 2: Home-path-shaped unknown token exits 2 with redacted path and no literal home."""
        home = Path.home()
        home_str = str(home)
        target_token = f"{home_str}/secret-missing-ref"
        redacted = f"{agent_schema.redact_home_paths(home_str)}/secret-missing-ref"

        # Human
        rc_h, out_h, err_h = self._invoke([target_token])
        self.assertEqual(rc_h, 2)
        self.assertEqual(out_h, "")
        self.assertIn(redacted, err_h)
        self.assertNotIn(home_str, err_h)
        self.assertNotIn(home_str, out_h)

        # Agent
        rc_a, out_a, err_a = self._invoke([target_token, "--agent"])
        self.assertEqual(rc_a, 2)
        self.assertEqual(err_a, "")
        self.assertNotIn(home_str, out_a)
        rec = json.loads(out_a)
        agent_schema.assert_valid_agent_record(rec)
        self.assertIn(redacted, rec["unresolved_selectors"])

        # JSON
        rc_j, out_j, err_j = self._invoke([target_token, "--json"])
        self.assertEqual(rc_j, 2)
        self.assertEqual(err_j, "")
        self.assertNotIn(home_str, out_j)
        json_data = json.loads(out_j)
        self.assertEqual(json_data["status"], "cannot-run")
        self.assertIn(redacted, json_data["data"]["unresolved_selectors"])

    def test_standing_vocabulary_zero_match_exits_0(self) -> None:
        """Case 3: Standing-vocabulary tokens with zero displayable matches exit 0."""
        for token in ("reusable", "prompt-library"):
            with self.subTest(token=token):
                # Human
                rc_h, out_h, err_h = self._invoke([token])
                self.assertEqual(rc_h, 0)
                self.assertEqual(err_h, "")
                self.assertIn(token, out_h)

                # Agent
                rc_a, out_a, err_a = self._invoke([token, "--agent"])
                self.assertEqual(rc_a, 0)
                self.assertEqual(err_a, "")
                rec = json.loads(out_a)
                agent_schema.assert_valid_agent_record(rec)
                self.assertEqual(rec["kind"], "result")
                self.assertEqual(rec["outcome"], "clean")
                self.assertEqual(rec["exit"], 0)
                self.assertTrue(rec["verified"])
                self.assertTrue(rec["complete"])
                self.assertEqual(rec["findings"], 0)

                # JSON
                rc_j, out_j, err_j = self._invoke([token, "--json"])
                self.assertEqual(rc_j, 0)
                self.assertEqual(err_j, "")
                json_data = json.loads(out_j)
                self.assertEqual(json_data["status"], "clean")
                self.assertEqual(json_data["exit_code"], 0)
                self.assertEqual(json_data["data"]["matches"], [])
                self.assertEqual(json_data["data"]["contents"], {})

    def test_non_displayed_real_artifact_exits_0(self) -> None:
        """Case 4: Real artifact in a non-displayed tree (releases) exits 0 and is not refused."""
        # Human
        rc_h, out_h, err_h = self._invoke([self.rel_id6])
        self.assertEqual(rc_h, 0)
        self.assertEqual(err_h, "")
        self.assertIn(self.rel_id6, out_h)

        # Agent
        rc_a, out_a, err_a = self._invoke([self.rel_id6, "--agent"])
        self.assertEqual(rc_a, 0)
        self.assertEqual(err_a, "")
        rec = json.loads(out_a)
        agent_schema.assert_valid_agent_record(rec)
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)

        # JSON
        rc_j, out_j, err_j = self._invoke([self.rel_id6, "--json"])
        self.assertEqual(rc_j, 0)
        self.assertEqual(err_j, "")
        json_data = json.loads(out_j)
        self.assertEqual(json_data["status"], "clean")
        self.assertEqual(json_data["exit_code"], 0)
        self.assertEqual(json_data["data"]["matches"], [])
        self.assertEqual(json_data["data"]["contents"], {})

    def test_matching_selectors_exit_0_and_return_content(self) -> None:
        """Case 5: Matching selector tokens by id6, setid, status, and filename substring."""
        test_tokens = ["p99001", "showtest", "to-review", "sample-plan"]
        for token in test_tokens:
            with self.subTest(token=token):
                # Human
                rc_h, out_h, err_h = self._invoke([token])
                self.assertEqual(rc_h, 0)
                self.assertEqual(err_h, "")
                self.assertIn(str(self.p1_path), out_h)
                self.assertIn(self.p1_content.strip(), out_h)

                # Agent
                rc_a, out_a, err_a = self._invoke([token, "--agent"])
                self.assertEqual(rc_a, 0)
                self.assertEqual(err_a, "")
                rec = json.loads(out_a)
                agent_schema.assert_valid_agent_record(rec)
                self.assertEqual(rec["kind"], "result")
                self.assertEqual(rec["outcome"], "clean")
                self.assertEqual(rec["exit"], 0)

                # JSON
                rc_j, out_j, err_j = self._invoke([token, "--json"])
                self.assertEqual(rc_j, 0)
                self.assertEqual(err_j, "")
                json_data = json.loads(out_j)
                self.assertEqual(json_data["status"], "clean")
                self.assertEqual(json_data["exit_code"], 0)
                self.assertIn(str(self.p1_path), json_data["data"]["matches"])
                self.assertIn(str(self.p1_path), json_data["data"]["contents"])
                self.assertEqual(
                    json_data["data"]["contents"][str(self.p1_path)], self.p1_content
                )

    def test_exit_contract_and_conformance_matrix(self) -> None:
        """Case 6: Exit codes observed are in declared exit_contract (0, 2), never 1."""
        decl = command_surface.get_declaration("show")
        self.assertEqual(decl.exit_contract, (0, 2))
        self.assertNotIn("domain_failure", conformance_matrix.required_scenarios(decl))

        # Collect exit codes from cases (1)-(5)
        observed_exits = set()
        for argv in [
            ["zzzzzz"],
            ["zzzzzz", "--agent"],
            ["zzzzzz", "--json"],
            ["prompt-library"],
            ["prompt-library", "--agent"],
            ["prompt-library", "--json"],
            [self.rel_id6],
            [self.rel_id6, "--agent"],
            [self.rel_id6, "--json"],
            ["p99001"],
            ["p99001", "--agent"],
            ["p99001", "--json"],
        ]:
            rc, _, _ = self._invoke(argv)
            observed_exits.add(rc)

        self.assertEqual(observed_exits, {0, 2})
        for code in observed_exits:
            self.assertIn(code, decl.exit_contract)
        self.assertNotIn(1, observed_exits)

    def test_history_flag_prints_one_row_per_history_line(self) -> None:
        """metastore `1ajqaa` E-03: `--history` renders the record's metadata history."""
        self.p1_path.write_text(
            RecordBuilder().plan(
                title="Sample Plan",
                id6="p99001",
                status="to-review",
                set="showtest",
                order=1,
                body="Plan details.\n",
                history=[
                    "- 2026-11-02 to-review (aw set): ready",
                    "- 2026-11-01 draft (author): created",
                ],
                text_only=True,
            ),
            encoding="utf-8",
        )
        rc, out, _ = self._invoke(["p99001", "--history"])
        self.assertEqual(rc, 0)
        self.assertIn("2026-11-02 to-review (aw set): ready", out)
        self.assertIn("2026-11-01 draft (author): created", out)
        self.assertNotIn("Plan details.", out)  # the body text is not printed
        rc_a, out_a, _ = self._invoke(["p99001", "--history", "--agent"])
        rec = json.loads(out_a.strip().splitlines()[-1])
        self.assertEqual((rc_a, rec["exit"]), (0, 0))
        self.assertIn("p99001-events:2", rec["evidence"])
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_format_json_prints_replayed_state(self) -> None:
        """metastore `1ajqaa` E-03: `--format json` prints parseable state; it conflicts with --agent."""
        rc, out, _ = self._invoke(["p99001", "--format", "json"])
        self.assertEqual(rc, 0)
        rec = json.loads(out)["data"]["records"][0]
        self.assertEqual(rec["status"], "to-review")
        self.assertIn("fields", rec)
        rc_text, out_text, _ = self._invoke(["p99001", "--format", "text"])
        self.assertEqual(rc_text, 0)
        self.assertEqual(
            out_text.count(self.p1_content), 1
        )  # explicit text == no-flag view
        rc_c, out_c, err_c = self._invoke(["p99001", "--agent", "--format", "json"])
        self.assertEqual(rc_c, 2)
        self.assertEqual(out_c, "")
        self.assertIn("conflicting output format flags", err_c)


if __name__ == "__main__":
    unittest.main()
