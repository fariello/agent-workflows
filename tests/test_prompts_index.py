"""Tests for prompts manifest index generation and drift checking (Plan dx0u4s).

Stdlib unittest, zero external deps. Verifies:
- build_index_json lists every bucketed prompt with id6, set, order, disposition, kind
- build_index_md formats browse-by-set human view
- check_drift reports check.stale-index-missing when index files absent
- check_drift reports check.stale-index-stale when index files out of date
- check_drift reports name-metadata-mismatch when filename id6 != comment Id
- run_index CLI behavior
"""

from __future__ import annotations

import argparse
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import artifact_core as _core
from agent_workflows import prompts_index


class _PromptsFixtureBase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.prompts_dir = self.root / ".aw" / "records" / "prompts"

        for bucket in ("pending", "executed", "superseded", "untracked"):
            (self.prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

        # 1. Clustered prompt with metadata comment
        (
            self.prompts_dir / "pending" / "20260920-seta-01-abc123-slug-one.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: research | Id: abc123 | Set: seta | Order: 01 | Status: pending | Slug: slug-one -->\n\nPrompt one.\n",
            encoding="utf-8",
        )

        # 2. Legacy prompt with metadata comment (no Id:)
        (
            self.prompts_dir / "executed" / "20260810-1544-01-legacy-prompt.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-10 -->\n\nPrompt two.\n",
            encoding="utf-8",
        )

        # 3. Legacy prompt with no comment
        (
            self.prompts_dir / "superseded" / "20260717-1950-01-no-comment.prompt.md"
        ).write_text(
            "# Legacy prompt\n\nBody.\n",
            encoding="utf-8",
        )

        # 4. Untracked file (should be ignored)
        (self.prompts_dir / "untracked" / "20260920-untracked.prompt.md").write_text(
            "# Untracked\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()


class PromptsIndexTests(_PromptsFixtureBase):
    def test_scan_and_build_index_json(self):
        entries, drift = prompts_index.scan_prompts(self.prompts_dir)
        self.assertEqual(len(entries), 3)

        json_str = prompts_index.build_index_json(entries)
        data = json.loads(json_str)
        self.assertEqual(len(data), 3)

        by_path = {item["path"]: item for item in data}
        p1 = by_path["pending/20260920-seta-01-abc123-slug-one.prompt.md"]
        self.assertEqual(p1["id6"], "abc123")
        self.assertEqual(p1["set_id"], "seta")
        self.assertEqual(p1["order"], 1)
        self.assertEqual(p1["disposition"], "pending")
        self.assertEqual(p1["kind"], "research")

        p2 = by_path["executed/20260810-1544-01-legacy-prompt.prompt.md"]
        self.assertEqual(p2["disposition"], "executed")
        self.assertEqual(p2["kind"], "run-once")

        p3 = by_path["superseded/20260717-1950-01-no-comment.prompt.md"]
        self.assertEqual(p3["disposition"], "superseded")

    def test_build_index_md(self):
        entries, _ = prompts_index.scan_prompts(self.prompts_dir)
        md_str = prompts_index.build_index_md(entries)
        self.assertIn("# Prompts by topic (Set)", md_str)
        self.assertIn("## seta", md_str)
        self.assertIn("abc123", md_str)

    def test_check_drift_missing_index(self):
        drift = prompts_index.check_drift(self.root, self.prompts_dir)
        rules = [d.rule for d in drift]
        self.assertIn("check.stale-index-missing", rules)
        # Stale-index-missing is info severity, so exit code should be 0
        self.assertEqual(_core.drift_exit_code(drift), 0)

    def test_check_drift_stale_index(self):
        # Generate clean indexes
        entries, _ = prompts_index.scan_prompts(self.prompts_dir)
        (self.prompts_dir / "INDEX.json").write_text(
            prompts_index.build_index_json(entries), encoding="utf-8"
        )
        (self.prompts_dir / "INDEX.md").write_text(
            prompts_index.build_index_md(entries), encoding="utf-8"
        )

        drift = prompts_index.check_drift(self.root, self.prompts_dir)
        self.assertEqual(drift, [])

        # Tamper with INDEX.json
        (self.prompts_dir / "INDEX.json").write_text("[]\n", encoding="utf-8")
        drift_stale = prompts_index.check_drift(self.root, self.prompts_dir)
        rules = [d.rule for d in drift_stale]
        self.assertIn("check.stale-index-stale", rules)

    def test_check_drift_name_metadata_mismatch(self):
        # Create a prompt where filename id6 != comment Id
        (
            self.prompts_dir / "pending" / "20260920-setb-01-xyz789-mismatch.prompt.md"
        ).write_text(
            "<!-- aw-prompt: Kind: research | Id: dif123 | Set: setb | Order: 01 | Status: pending | Slug: mismatch -->\n\nPrompt.\n",
            encoding="utf-8",
        )
        drift = prompts_index.check_drift(self.root, self.prompts_dir)
        mismatch_drifts = [d for d in drift if d.rule == "name-metadata-mismatch"]
        self.assertTrue(len(mismatch_drifts) >= 1)
        self.assertTrue(any("xyz789" in d.detail for d in mismatch_drifts))


class PromptsContentValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.prompts_dir = self.root / ".aw" / "records" / "prompts"
        for bucket in ("pending", "executed", "superseded", "not-executed", "reusable"):
            (self.prompts_dir / bucket).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_rule_prompt_metadata_missing_post_cutover(self):
        from agent_workflows import check_engine as ce

        # Post-cutover dated prompt without comment -> MUST report check.prompt-metadata-missing
        p_post = (
            self.prompts_dir
            / "pending"
            / "20260925-seta-01-abc123-new-prompt.prompt.md"
        )
        p_post.write_text("# Body only\n", encoding="utf-8")
        drift = ce.validate_prompt_content(p_post, repo_root=self.root)
        rules = [d.rule for d in drift]
        self.assertIn("check.prompt-metadata-missing", rules)

        # Pre-cutover dated prompt without comment -> Grandfathered, no error
        p_pre = self.prompts_dir / "pending" / "20260810-0100-01-old-prompt.prompt.md"
        p_pre.write_text("# Body only\n", encoding="utf-8")
        drift_pre = ce.validate_prompt_content(p_pre, repo_root=self.root)
        self.assertEqual(drift_pre, [])

    def test_rule_prompt_id_mismatch(self):
        from agent_workflows import check_engine as ce

        # Clustered prompt filename with abc123, comment with dif999
        p = (
            self.prompts_dir
            / "pending"
            / "20260920-seta-01-abc123-test-mismatch.prompt.md"
        )
        p.write_text(
            "<!-- aw-prompt: Kind: research | Id: dif999 | Set: seta | Order: 01 | Status: pending | Slug: test-mismatch -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift = ce.validate_prompt_content(p, repo_root=self.root)
        rules = [d.rule for d in drift]
        self.assertIn("check.prompt-id-mismatch", rules)

        # Matching id
        p_ok = (
            self.prompts_dir / "pending" / "20260920-seta-01-abc123-test-ok.prompt.md"
        )
        p_ok.write_text(
            "<!-- aw-prompt: Kind: research | Id: abc123 | Set: seta | Order: 01 | Status: pending | Slug: test-ok -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift_ok = ce.validate_prompt_content(p_ok, repo_root=self.root)
        self.assertEqual(drift_ok, [])

    def test_rule_prompt_status_mismatch(self):
        from agent_workflows import check_engine as ce

        # Prompt in executed/ with comment Status: pending
        p1 = self.prompts_dir / "executed" / "20260808-1948-01-spec-review.prompt.md"
        p1.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: pending | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift1 = ce.validate_prompt_content(p1, repo_root=self.root)
        rules1 = [d.rule for d in drift1]
        self.assertIn("check.prompt-status-mismatch", rules1)

        # Prompt in pending/ with comment Status: executed
        p2 = self.prompts_dir / "pending" / "20260808-1948-01-spec-review.prompt.md"
        p2.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift2 = ce.validate_prompt_content(p2, repo_root=self.root)
        rules2 = [d.rule for d in drift2]
        self.assertIn("check.prompt-status-mismatch", rules2)

        # Prompt in executed/ with comment Status: executed -> Clean
        p3 = self.prompts_dir / "executed" / "20260808-1948-01-spec-review.prompt.md"
        p3.write_text(
            "<!-- aw-prompt: Kind: run-once | Status: executed | Created: 2026-08-08 -->\n\nBody.\n",
            encoding="utf-8",
        )
        drift3 = ce.validate_prompt_content(p3, repo_root=self.root)
        self.assertEqual(drift3, [])


class RunIndexOutputTests(_PromptsFixtureBase):
    def _run(self, **overrides):
        ns = dict(
            dir=str(self.root),
            limit=None,
            check=False,
            quiet=False,
            no_color=False,
            color=False,
            agent=False,
            json=False,
        )
        ns.update(overrides)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = prompts_index.run_index(argparse.Namespace(**ns))
        return rc, buf.getvalue()

    def _generate_clean_indexes(self):
        entries, _ = prompts_index.scan_prompts(self.prompts_dir)
        (self.prompts_dir / "INDEX.json").write_text(
            prompts_index.build_index_json(entries), encoding="utf-8"
        )
        (self.prompts_dir / "INDEX.md").write_text(
            prompts_index.build_index_md(entries), encoding="utf-8"
        )

    def test_a_first_run_writes_both_indexes(self):
        rc, out = self._run(no_color=True)
        self.assertEqual(rc, 0)
        self.assertEqual(
            out,
            "wrote        .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n",
        )
        self.assertTrue((self.prompts_dir / "INDEX.json").is_file())
        self.assertTrue((self.prompts_dir / "INDEX.md").is_file())

    def test_b_second_run_reports_up_to_date(self):
        self._generate_clean_indexes()
        rc, out = self._run(no_color=True)
        self.assertEqual(rc, 0)
        self.assertEqual(
            out,
            "up to date   .aw/records/prompts/INDEX.json, INDEX.md (3 prompts)\n",
        )

    def test_c_third_run_after_md_only_change_reports_updated(self):
        self._generate_clean_indexes()
        md_path = self.prompts_dir / "INDEX.md"
        md_path.write_text(
            md_path.read_text(encoding="utf-8") + "\n<!-- extra -->\n",
            encoding="utf-8",
        )
        rc, out = self._run(no_color=True)
        self.assertEqual(rc, 0)
        self.assertEqual(
            out,
            "updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 3 prompts)\n",
        )

    def test_d_fourth_run_after_json_only_change_reports_updated(self):
        self._generate_clean_indexes()
        (self.prompts_dir / "INDEX.json").write_text("{}\n", encoding="utf-8")
        rc, out = self._run(no_color=True)
        self.assertEqual(rc, 0)
        self.assertEqual(
            out,
            "updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 3 prompts)\n",
        )

    def test_e_quiet_suppresses_output_and_restores_files(self):
        self._generate_clean_indexes()
        md_path = self.prompts_dir / "INDEX.md"
        clean_md = md_path.read_text(encoding="utf-8")
        md_path.write_text(clean_md + "\n<!-- extra -->\n", encoding="utf-8")
        rc, out = self._run(quiet=True)
        self.assertEqual(rc, 0)
        self.assertEqual(out, "")
        self.assertEqual(md_path.read_text(encoding="utf-8"), clean_md)


class IndexOutcomeWordsAreNotLifecycleStatusesTests(_PromptsFixtureBase):
    """Spec `uonrjg` R10.3 / criteria A14 and A20, matching plans_index and research_index."""

    def _run(self, **overrides):
        ns = dict(
            dir=str(self.root),
            limit=None,
            check=False,
            quiet=False,
            no_color=False,
            color=False,
            agent=False,
            json=False,
        )
        ns.update(overrides)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = prompts_index.run_index(argparse.Namespace(**ns))
        return rc, buf.getvalue()

    def test_f_force_color_renders_generic_outcome_words_and_never_unknown_glyph(
        self,
    ):
        with mock.patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False):
            rc1, out1 = self._run()
        self.assertEqual(rc1, 0)
        self.assertIn("wrote", out1)
        self.assertNotIn("?", out1)
        self.assertIn("\033[1;38;5;46mwrote\033[0m", out1)

        with mock.patch.dict(os.environ, {"FORCE_COLOR": "1"}, clear=False):
            rc2, out2 = self._run()
        self.assertEqual(rc2, 0)
        self.assertIn("up to date", out2)
        self.assertNotIn("?", out2)
        self.assertIn("\033[1;38;5;46mup to date\033[0m", out2)

    def test_g_machine_and_suppressed_modes_emit_no_ansi(self):
        cases = (
            ("--agent", {"agent": True}, {}),
            ("--json", {"json": True}, {}),
            ("--no-color", {"no_color": True}, {}),
            ("NO_COLOR=1", {}, {"NO_COLOR": "1"}),
            ("TERM=dumb", {}, {"TERM": "dumb"}),
            ("piped stdout (not a tty)", {}, {}),
        )
        for label, overrides, env in cases:
            with self.subTest(mode=label):
                patched = dict(env)
                with mock.patch.dict(os.environ, patched, clear=False):
                    if "NO_COLOR" not in patched:
                        os.environ.pop("NO_COLOR", None)
                    os.environ.pop("FORCE_COLOR", None)
                    _rc, out = self._run(**overrides)
                self.assertNotIn(
                    "\033",
                    out,
                    f"criterion A14/A11 violation: `aw index prompts` emitted ANSI in {label} mode.",
                )


if __name__ == "__main__":
    unittest.main()
