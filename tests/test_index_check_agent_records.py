"""Behavior tests for index <type> --check across agent, json, and human audiences.

Drives the three index check verbs (`plans`, `prompts`, `research`) as subprocesses
against isolated fixture repositories, asserting:
- Under `--agent`: stdout parses as aw.agent/v1 JSONL, validate_agent_record is clean,
  the record's exit equals the process exit code, and no line contains a TAB character.
- Under `--json`: stdout parses as a valid single JSON document.
- Under human (no flag): stdout preserves the exact legacy lines and per-verb clean wording.

In accordance with GUIDING_PRINCIPLES P16, this module performs zero static analysis:
no AST checks, no source code regex, no caller census, and no symbol-existence tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema

# Reuses tests.conformance_matrix.run_cli (which passes cwd and pins NO_COLOR/COLUMNS)
# rather than forking a subprocess harness.
from tests.conformance_matrix import REPO_ROOT, run_cli


def _create_fixture_repo(root: Path, *, mode: str = "missing") -> None:
    """Create a fixture repo with plans, prompts, and research records.

    Modes:
    - "missing": valid record files, missing INDEX.json / INDEX.md (info severity, exit 0)
    - "clean": indexes generated and matching content (clean, exit 0)
    - "stale": indexes present but content outdated (warning severity, exit 1)
    """
    # 1. Plans
    plans_dir = root / ".aw" / "records" / "plans"
    (plans_dir / "pending").mkdir(parents=True, exist_ok=True)
    (plans_dir / "pending" / "20260701-seta-01-aaaaaa-plan.ipd.md").write_text(
        "# IPD: Test plan\n\n"
        "- Date: 2026-07-01\n"
        "- Kind: child\n"
        "- Concern: test.\n"
        "- Scope: test.\n"
        "- Status: pending\n"
        "- Author: test\n"
        "- Id: aaaaaa\n"
        "- Set: seta\n"
        "- Order: 01\n\n"
        "## Goal\n\nTest plan.\n",
        encoding="utf-8",
    )

    # 2. Prompts
    prompts_dir = root / ".aw" / "records" / "prompts"
    (prompts_dir / "pending").mkdir(parents=True, exist_ok=True)
    (prompts_dir / "pending" / "20260701-seta-01-bbbbbb-prompt.prompt.md").write_text(
        "<!-- aw-prompt: Kind: research | Id: bbbbbb | Set: seta | Order: 01 | Status: pending | Slug: prompt -->\n\n"
        "Prompt body.\n",
        encoding="utf-8",
    )

    # 3. Research
    research_dir = root / ".aw" / "records" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    (research_dir / "20260701-seta-01-cccccc-notes.md").write_text(
        "# Research notes\n\n"
        "- Id: cccccc\n"
        "- Created: 2026-07-01\n"
        "- Set: seta\n"
        "- Order: 01\n"
        "- Status: reference\n"
        "- Kind: notes\n"
        "- Topics: [test]\n\n"
        "Research body.\n",
        encoding="utf-8",
    )

    if mode == "clean":
        from agent_workflows import plans_index, prompts_index, research_index

        p_entries, _ = plans_index.scan_plans(plans_dir)
        (plans_dir / "INDEX.json").write_text(
            plans_index.build_index_json(p_entries), encoding="utf-8"
        )
        (plans_dir / "INDEX.md").write_text(
            plans_index.build_index_md(p_entries), encoding="utf-8"
        )

        pr_entries, _ = prompts_index.scan_prompts(prompts_dir)
        (prompts_dir / "INDEX.json").write_text(
            prompts_index.build_index_json(pr_entries), encoding="utf-8"
        )
        (prompts_dir / "INDEX.md").write_text(
            prompts_index.build_index_md(pr_entries), encoding="utf-8"
        )

        r_entries, _ = research_index._scan_docs(research_dir, repo_root=root)
        (research_dir / "INDEX.json").write_text(
            research_index.build_index_json(r_entries), encoding="utf-8"
        )
        (research_dir / "INDEX.md").write_text(
            research_index.build_index_md(r_entries), encoding="utf-8"
        )

    elif mode == "stale":
        (plans_dir / "INDEX.json").write_text("{}", encoding="utf-8")
        (plans_dir / "INDEX.md").write_text("# Old\n", encoding="utf-8")

        (prompts_dir / "INDEX.json").write_text("{}", encoding="utf-8")
        (prompts_dir / "INDEX.md").write_text("# Old\n", encoding="utf-8")

        (research_dir / "INDEX.json").write_text("{}", encoding="utf-8")
        (research_dir / "INDEX.md").write_text("# Old\n", encoding="utf-8")


VERBS = ("plans", "prompts", "research")
CLEAN_MESSAGES = {
    "plans": "plans index --check: clean\n",
    "prompts": "prompts index --check: clean\n",
    "research": "index --check: clean\n",
}


class IndexCheckSubprocessTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
        # Guarantee tree-relative import root in subprocesses under both pytest and unittest
        _current_pp = os.environ.get("PYTHONPATH", "")
        if str(REPO_ROOT) not in _current_pp.split(os.pathsep):
            self._old_pp = _current_pp
            os.environ["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{_current_pp}".rstrip(
                os.pathsep
            )
        else:
            self._old_pp = None

    def tearDown(self):
        self._temp_dir.cleanup()
        if self._old_pp is not None:
            os.environ["PYTHONPATH"] = self._old_pp

    # ----------------------------------------------------------------------------------
    # Human audience assertions: must pass at base commit and remain unchanged
    # ----------------------------------------------------------------------------------

    def test_human_clean_output_per_verb(self):
        _create_fixture_repo(self.root, mode="clean")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check"], cwd=self.root)
                self.assertEqual(res.returncode, 0)
                self.assertEqual(res.stdout, CLEAN_MESSAGES[verb])

    def test_human_drifting_output_per_verb(self):
        _create_fixture_repo(self.root, mode="missing")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check"], cwd=self.root)
                self.assertEqual(res.returncode, 0)
                self.assertIn("INDEX.json: check.stale-index-missing:", res.stdout)
                self.assertIn("INDEX.md: check.stale-index-missing:", res.stdout)

    def test_human_stale_output_per_verb(self):
        _create_fixture_repo(self.root, mode="stale")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check"], cwd=self.root)
                self.assertEqual(res.returncode, 1)
                self.assertIn("INDEX.json: check.stale-index-stale:", res.stdout)
                self.assertIn("INDEX.md: check.stale-index-stale:", res.stdout)

    # ----------------------------------------------------------------------------------
    # --agent audience assertions: FAIL at base commit (prints TSV lines with tabs)
    # ----------------------------------------------------------------------------------

    def test_agent_clean_fixture_emits_valid_record(self):
        _create_fixture_repo(self.root, mode="clean")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--agent"], cwd=self.root)
                lines = [line for line in res.stdout.splitlines() if line.strip()]
                self.assertTrue(lines, f"Expected output for {verb} under --agent")
                for line in lines:
                    self.assertNotIn(
                        "\t", line, f"Tab character found in output line for {verb}"
                    )
                records = [json.loads(line) for line in lines]
                terminal = records[-1]
                val_errors = agent_schema.validate_agent_record(terminal)
                self.assertEqual(
                    val_errors, [], f"Schema validation errors for {verb}: {val_errors}"
                )
                self.assertEqual(terminal.get("exit"), res.returncode)
                self.assertEqual(res.returncode, 0)

    def test_agent_missing_fixture_emits_valid_record(self):
        _create_fixture_repo(self.root, mode="missing")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--agent"], cwd=self.root)
                lines = [line for line in res.stdout.splitlines() if line.strip()]
                self.assertTrue(lines, f"Expected output for {verb} under --agent")
                for line in lines:
                    self.assertNotIn(
                        "\t", line, f"Tab character found in output line for {verb}"
                    )
                records = [json.loads(line) for line in lines]
                terminal = records[-1]
                val_errors = agent_schema.validate_agent_record(terminal)
                self.assertEqual(
                    val_errors, [], f"Schema validation errors for {verb}: {val_errors}"
                )
                self.assertEqual(terminal.get("exit"), res.returncode)
                self.assertEqual(res.returncode, 0)

    def test_agent_stale_fixture_emits_valid_record(self):
        _create_fixture_repo(self.root, mode="stale")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--agent"], cwd=self.root)
                lines = [line for line in res.stdout.splitlines() if line.strip()]
                self.assertTrue(lines, f"Expected output for {verb} under --agent")
                for line in lines:
                    self.assertNotIn(
                        "\t", line, f"Tab character found in output line for {verb}"
                    )
                records = [json.loads(line) for line in lines]
                terminal = records[-1]
                val_errors = agent_schema.validate_agent_record(terminal)
                self.assertEqual(
                    val_errors, [], f"Schema validation errors for {verb}: {val_errors}"
                )
                self.assertEqual(terminal.get("exit"), res.returncode)
                self.assertEqual(res.returncode, 1)

    # ----------------------------------------------------------------------------------
    # --json audience assertions: FAIL at base commit (prints human prose)
    # ----------------------------------------------------------------------------------

    def test_json_clean_fixture_emits_json_document(self):
        _create_fixture_repo(self.root, mode="clean")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--json"], cwd=self.root)
                self.assertEqual(res.returncode, 0)
                try:
                    parsed = json.loads(res.stdout)
                except json.JSONDecodeError as exc:
                    self.fail(
                        f"{verb} --json output failed to parse as JSON: {exc}\nOutput was: {res.stdout!r}"
                    )
                self.assertIsInstance(parsed, dict)

    def test_json_missing_fixture_emits_json_document(self):
        _create_fixture_repo(self.root, mode="missing")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--json"], cwd=self.root)
                self.assertEqual(res.returncode, 0)
                try:
                    parsed = json.loads(res.stdout)
                except json.JSONDecodeError as exc:
                    self.fail(
                        f"{verb} --json output failed to parse as JSON: {exc}\nOutput was: {res.stdout!r}"
                    )
                self.assertIsInstance(parsed, dict)

    def test_json_stale_fixture_emits_json_document(self):
        _create_fixture_repo(self.root, mode="stale")
        for verb in VERBS:
            with self.subTest(verb=verb):
                res = run_cli(["index", verb, "--check", "--json"], cwd=self.root)
                self.assertEqual(res.returncode, 1)
                try:
                    parsed = json.loads(res.stdout)
                except json.JSONDecodeError as exc:
                    self.fail(
                        f"{verb} --json output failed to parse as JSON: {exc}\nOutput was: {res.stdout!r}"
                    )
                self.assertIsInstance(parsed, dict)

    # ----------------------------------------------------------------------------------
    # aw index all --check behavior assertions (E-03)
    # ----------------------------------------------------------------------------------

    def test_all_clean_fixture_agent_and_json(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _create_fixture_repo(self.root, mode="clean")

        # (a) --agent: rc == 0, exactly one line, validate_agent_record [], target == "all", exit == 0, outcome == "conforms"
        res_agent = run_cli(["index", "all", "--check", "--agent"], cwd=self.root)
        self.assertEqual(res_agent.returncode, 0)
        lines = [line for line in res_agent.stdout.splitlines() if line.strip()]
        self.assertEqual(
            len(lines), 1, f"Expected exactly one line, got: {res_agent.stdout!r}"
        )
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("target"), "all")
        self.assertEqual(rec.get("exit"), 0)
        self.assertEqual(rec.get("outcome"), "conforms")

        # --json: parses with one json.loads call with exit_code == 0, data["target"] == "all", data["by_type"] keys exactly plans, prompts, research, no repo_root or human_rendered
        res_json = run_cli(["index", "all", "--check", "--json"], cwd=self.root)
        self.assertEqual(res_json.returncode, 0)
        parsed = json.loads(res_json.stdout)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed.get("exit_code"), 0)
        data = parsed.get("data", {})
        self.assertEqual(data.get("target"), "all")
        self.assertEqual(
            set(data.get("by_type", {}).keys()), {"plans", "prompts", "research"}
        )
        self.assertNotIn("repo_root", data)
        self.assertNotIn("human_rendered", data)

    def test_all_partial_stale_fixture(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _create_fixture_repo(self.root, mode="clean")
        plans_md = self.root / ".aw" / "records" / "plans" / "INDEX.md"
        plans_md.write_text(
            plans_md.read_text(encoding="utf-8") + "\n# Extra\n", encoding="utf-8"
        )

        # (b) --agent: rc == 1, exactly one line with exit == 1, outcome == "findings", findings >= 1, check.stale-index-stale diagnostic
        res_agent = run_cli(["index", "all", "--check", "--agent"], cwd=self.root)
        self.assertEqual(res_agent.returncode, 1)
        lines = [line for line in res_agent.stdout.splitlines() if line.strip()]
        self.assertEqual(
            len(lines), 1, f"Expected exactly one line, got: {res_agent.stdout!r}"
        )
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("exit"), 1)
        self.assertEqual(rec.get("outcome"), "findings")
        self.assertGreaterEqual(rec.get("findings", 0), 1)
        diags = rec.get("diagnostics", [])
        rules = [d.get("rule") for d in diags]
        self.assertIn("check.stale-index-stale", rules)

        # --json: exit_code == 1, research exit_code == 0
        res_json = run_cli(["index", "all", "--check", "--json"], cwd=self.root)
        self.assertEqual(res_json.returncode, 1)
        parsed = json.loads(res_json.stdout)
        self.assertEqual(parsed.get("exit_code"), 1)
        by_type = parsed.get("data", {}).get("by_type", {})
        self.assertEqual(by_type.get("research", {}).get("exit_code"), 0)

    def test_all_human_mode_invariance(self):
        for mode in ("clean", "partial_stale"):
            with self.subTest(mode=mode):
                repo_all = self.root / f"all_{mode}"
                repo_all.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "init"], cwd=repo_all, capture_output=True, check=True
                )
                _create_fixture_repo(repo_all, mode="clean")

                repo_single = self.root / f"single_{mode}"
                repo_single.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["git", "init"], cwd=repo_single, capture_output=True, check=True
                )
                _create_fixture_repo(repo_single, mode="clean")

                if mode == "partial_stale":
                    p_all = repo_all / ".aw" / "records" / "plans" / "INDEX.md"
                    p_all.write_text(
                        p_all.read_text(encoding="utf-8") + "\n# Extra\n",
                        encoding="utf-8",
                    )
                    p_single = repo_single / ".aw" / "records" / "plans" / "INDEX.md"
                    p_single.write_text(
                        p_single.read_text(encoding="utf-8") + "\n# Extra\n",
                        encoding="utf-8",
                    )

                res_all = run_cli(["index", "all", "--check"], cwd=repo_all)

                res_plans = run_cli(["index", "plans", "--check"], cwd=repo_single)
                res_prompts = run_cli(["index", "prompts", "--check"], cwd=repo_single)
                res_research = run_cli(
                    ["index", "research", "--check"], cwd=repo_single
                )

                expected_stdout = (
                    res_plans.stdout + res_prompts.stdout + res_research.stdout
                )
                expected_rc = max(
                    res_plans.returncode,
                    res_prompts.returncode,
                    res_research.returncode,
                )

                self.assertEqual(res_all.returncode, expected_rc)
                self.assertEqual(res_all.stdout, expected_stdout)

    def test_all_repo_relative_diagnostic_locations(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _create_fixture_repo(self.root, mode="clean")
        (self.root / "README.md").write_text(
            "Citing RSCH-zzzzzz here.\n", encoding="utf-8"
        )

        res_agent = run_cli(["index", "all", "--check", "--agent"], cwd=self.root)
        lines = [line for line in res_agent.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        diags = rec.get("diagnostics", [])
        danglers = [d for d in diags if "dangling" in d.get("rule", "")]
        self.assertTrue(danglers, f"Expected dangling-citation diagnostic, got {diags}")
        self.assertEqual(danglers[0].get("location"), "README.md:1")

        # neither --agent --verbose nor --json stdout contains fixture root path
        res_verbose = run_cli(
            ["index", "all", "--check", "--agent", "--verbose"], cwd=self.root
        )
        self.assertNotIn(str(self.root), res_verbose.stdout)
        self.assertNotIn(str(self.root), res_agent.stdout)

        res_json = run_cli(["index", "all", "--check", "--json"], cwd=self.root)
        self.assertNotIn(str(self.root), res_json.stdout)


if __name__ == "__main__":
    unittest.main()
