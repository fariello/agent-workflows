"""Behavior tests for aw index <type> write path across agent, json, and human audiences.

Drives the three index verbs (`plans`, `prompts`, `research`) as subprocesses
against isolated fixture repositories (never the live tree), asserting:
- Under `--agent`:
  (a) stdout is exactly one line that json.loads parses, agent_schema.validate_agent_record
      returns [], and its exit equals the process exit code;
  (b) FIRST run (no index files): applied is true, changes lists both INDEX.json and INDEX.md
      as repo-relative paths under the type's records dir, and target is the type;
  (c) SECOND run unchanged: applied is false and no changes key;
  (d) after editing only INDEX.md on disk, a third run reports exactly one change, INDEX.md;
  (e) no \\033 and no home-path prefix anywhere in stdout.
- Under `--json`: stdout parses as one JSON document whose data carries target, count,
  json_changed, md_changed and no absolute path anywhere in the document.
- Refusal/drift cases:
  - plans fixture with an extra plan lacking - Id: (write still happens, exit 0,
    record carries a diagnostic with rule id-missing);
  - research fixture with one frontmatter-invalid doc (exit 1, outcome findings,
    findings >= 1, a diagnostic naming that doc's repo-relative location and rule
    frontmatter-invalid, and the index files NOT written).
- Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact (prompts matches shared four-state format, vcqobe).
- Unsupported type: index specs --agent emits a kind:error record at exit 2.

In accordance with GUIDING_PRINCIPLES P16, this module performs zero static analysis:
no AST checks, no source code regex, no caller census, and no symbol-existence tests.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agent_schema, plans_index, prompts_index, research_index
from tests.conformance_matrix import REPO_ROOT, run_cli
from tests.test_index_check_agent_records import _create_fixture_repo
from tests.test_research_index import _write

VERBS = ("plans", "prompts", "research")

HUMAN_FIRST_RUN = {
    "plans": "wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    "prompts": "wrote        .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n",
    "research": "wrote        .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
}

HUMAN_SECOND_RUN = {
    "plans": "up to date   .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    "prompts": "up to date   .aw/records/prompts/INDEX.json, INDEX.md (1 prompts)\n",
    "research": "up to date   .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
}

HUMAN_MD_ONLY_RUN = {
    "plans": "updated      .aw/records/plans/INDEX.md (INDEX.json up to date; 1 plans)\n",
    "prompts": "updated      .aw/records/prompts/INDEX.md (INDEX.json up to date; 1 prompts)\n",
    "research": "updated      .agents/docs/research/INDEX.md (INDEX.json up to date; 1 docs)\n",
}

HUMAN_JSON_ONLY_RUN = {
    "plans": "updated      .aw/records/plans/INDEX.json (INDEX.md up to date; 1 plans)\n",
    "prompts": "updated      .aw/records/prompts/INDEX.json (INDEX.md up to date; 1 prompts)\n",
    "research": "updated      .agents/docs/research/INDEX.json (INDEX.md up to date; 1 docs)\n",
}


def _setup_fixture_for_verb(root: Path, verb: str) -> tuple[Path, str]:
    """Create isolated fixture repo and return (index_dir, rel_dir_posix)."""
    subprocess.run(["git", "init"], cwd=root, capture_output=True, check=True)
    _create_fixture_repo(root, mode="missing")
    if verb == "plans":
        index_dir = root / ".aw" / "records" / "plans"
        rel_dir = ".aw/records/plans"
    elif verb == "prompts":
        index_dir = root / ".aw" / "records" / "prompts"
        rel_dir = ".aw/records/prompts"
    elif verb == "research":
        # Remove .aw/records/research so research_index._roots resolves .agents/docs/research
        shutil.rmtree(root / ".aw" / "records" / "research", ignore_errors=True)
        _write(
            root,
            set_id="seta",
            order=1,
            id6="cccccc",
            slug="notes",
            status="reference",
            created="20260701",
        )
        index_dir = root / ".agents" / "docs" / "research"
        rel_dir = ".agents/docs/research"
    else:
        raise ValueError(f"Unknown verb {verb}")
    return index_dir, rel_dir


class IndexWriteSubprocessTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
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

    def _assert_no_leaks(self, text: str):
        self.assertNotIn("\033", text, "Escape sequence found in output")
        self.assertNotIn(str(self.root), text, "Fixture root path found in output")
        home = Path.home().as_posix()
        self.assertNotIn(home, text, "User home path found in output")

    # ----------------------------------------------------------------------------------
    # --agent audience assertions (E-01 a..e)
    # ----------------------------------------------------------------------------------

    def _run_agent_verb_lifecycle(self, verb: str):
        index_dir, rel_dir = _setup_fixture_for_verb(self.root, verb)

        # (b) FIRST run: no index files exist yet
        res1 = run_cli(["index", verb, "--agent"], cwd=self.root)
        self.assertEqual(res1.returncode, 0, f"First run {verb} failed: {res1.stderr}")
        lines1 = res1.stdout.splitlines()
        self.assertEqual(
            len(lines1),
            1,
            f"Expected exactly one line for {verb} first run, got: {res1.stdout!r}",
        )
        self._assert_no_leaks(res1.stdout)
        rec1 = json.loads(lines1[0])
        val_errors1 = agent_schema.validate_agent_record(rec1)
        self.assertEqual(
            val_errors1, [], f"Schema validation errors in first run for {verb}"
        )
        self.assertEqual(rec1.get("exit"), res1.returncode)
        self.assertEqual(rec1.get("cmd"), "index")
        self.assertEqual(rec1.get("target"), verb)
        self.assertIs(rec1.get("applied"), True)
        changes1 = rec1.get("changes")
        self.assertIsInstance(changes1, list)
        self.assertEqual(len(changes1), 2)
        change_paths1 = {c.get("path") for c in changes1}
        expected_paths = {f"{rel_dir}/INDEX.json", f"{rel_dir}/INDEX.md"}
        self.assertEqual(change_paths1, expected_paths)

        # (c) SECOND run unchanged: applied is False, no changes key
        res2 = run_cli(["index", verb, "--agent"], cwd=self.root)
        self.assertEqual(res2.returncode, 0, f"Second run {verb} failed: {res2.stderr}")
        lines2 = res2.stdout.splitlines()
        self.assertEqual(
            len(lines2),
            1,
            f"Expected exactly one line for {verb} second run, got: {res2.stdout!r}",
        )
        self._assert_no_leaks(res2.stdout)
        rec2 = json.loads(lines2[0])
        val_errors2 = agent_schema.validate_agent_record(rec2)
        self.assertEqual(
            val_errors2, [], f"Schema validation errors in second run for {verb}"
        )
        self.assertEqual(rec2.get("exit"), res2.returncode)
        self.assertIs(rec2.get("applied"), False)
        self.assertNotIn(
            "changes",
            rec2,
            f"changes key should not be present on second run for {verb}",
        )

        # (d) THIRD run: edit only INDEX.md on disk, reports exactly one change (INDEX.md)
        md_file = index_dir / "INDEX.md"
        md_file.write_text(
            md_file.read_text(encoding="utf-8") + "\n<!-- edit -->\n", encoding="utf-8"
        )

        res3 = run_cli(["index", verb, "--agent"], cwd=self.root)
        self.assertEqual(res3.returncode, 0, f"Third run {verb} failed: {res3.stderr}")
        lines3 = res3.stdout.splitlines()
        self.assertEqual(
            len(lines3),
            1,
            f"Expected exactly one line for {verb} third run, got: {res3.stdout!r}",
        )
        self._assert_no_leaks(res3.stdout)
        rec3 = json.loads(lines3[0])
        val_errors3 = agent_schema.validate_agent_record(rec3)
        self.assertEqual(
            val_errors3, [], f"Schema validation errors in third run for {verb}"
        )
        self.assertEqual(rec3.get("exit"), res3.returncode)
        self.assertIs(rec3.get("applied"), True)
        changes3 = rec3.get("changes")
        self.assertIsInstance(changes3, list)
        self.assertEqual(len(changes3), 1)
        self.assertEqual(changes3[0].get("path"), f"{rel_dir}/INDEX.md")

    def test_agent_write_plans(self):
        self._run_agent_verb_lifecycle("plans")

    def test_agent_write_prompts(self):
        self._run_agent_verb_lifecycle("prompts")

    def test_agent_write_research(self):
        self._run_agent_verb_lifecycle("research")

    # ----------------------------------------------------------------------------------
    # --json audience assertions
    # ----------------------------------------------------------------------------------

    def _run_json_verb_check(self, verb: str):
        index_dir, rel_dir = _setup_fixture_for_verb(self.root, verb)
        res = run_cli(["index", verb, "--json"], cwd=self.root)
        self.assertEqual(res.returncode, 0, f"JSON run {verb} failed: {res.stderr}")
        self._assert_no_leaks(res.stdout)
        doc = json.loads(res.stdout)
        self.assertIsInstance(doc, dict)
        self.assertIn("data", doc)
        data = doc["data"]
        self.assertEqual(data.get("target"), verb)
        self.assertEqual(data.get("count"), 1)
        self.assertIs(data.get("json_changed"), True)
        self.assertIs(data.get("md_changed"), True)
        self.assertNotIn("repo_root", data)

    def test_json_write_plans(self):
        self._run_json_verb_check("plans")

    def test_json_write_prompts(self):
        self._run_json_verb_check("prompts")

    def test_json_write_research(self):
        self._run_json_verb_check("research")

    # ----------------------------------------------------------------------------------
    # Refusal and drift cases
    # ----------------------------------------------------------------------------------

    def test_drift_plans_missing_id(self):
        index_dir, rel_dir = _setup_fixture_for_verb(self.root, "plans")
        (index_dir / "pending" / "20260701-seta-02-noid-plan.ipd.md").write_text(
            "# IPD: Plan lacking id\n\n"
            "- Date: 2026-07-01\n"
            "- Kind: child\n"
            "- Concern: test\n"
            "- Scope: test\n"
            "- Status: pending\n"
            "- Author: test\n"
            "- Set: seta\n"
            "- Order: 02\n\n"
            "## Goal\n\nTest\n",
            encoding="utf-8",
        )
        res = run_cli(["index", "plans", "--agent"], cwd=self.root)
        self.assertEqual(res.returncode, 0)
        lines = res.stdout.splitlines()
        self.assertEqual(len(lines), 1, f"Expected single line, got: {res.stdout!r}")
        self._assert_no_leaks(res.stdout)
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("exit"), 0)
        self.assertIs(rec.get("applied"), True)
        diagnostics = rec.get("diagnostics", [])
        rules = [d.get("rule") for d in diagnostics]
        self.assertIn("id-missing", rules)
        # Ensure index files were actually written
        self.assertTrue((index_dir / "INDEX.json").exists())
        self.assertTrue((index_dir / "INDEX.md").exists())

    def test_refusal_research_invalid_frontmatter(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _write(
            self.root,
            set_id="seta",
            order=1,
            id6="cccccc",
            slug="notes",
            status="bogus-status",
            created="20260701",
        )
        res = run_cli(["index", "research", "--agent"], cwd=self.root)
        self.assertEqual(res.returncode, 1)
        lines = res.stdout.splitlines()
        self.assertEqual(len(lines), 1, f"Expected single line, got: {res.stdout!r}")
        self._assert_no_leaks(res.stdout)
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("exit"), 1)
        self.assertEqual(rec.get("outcome"), "findings")
        self.assertGreaterEqual(rec.get("findings", 0), 1)
        diagnostics = rec.get("diagnostics", [])
        self.assertTrue(diagnostics, "Expected diagnostics in refusal record")
        self.assertTrue(
            any(
                d.get("rule") == "frontmatter-invalid"
                and "cccccc" in d.get("location", "")
                for d in diagnostics
            ),
            f"Expected frontmatter-invalid diagnostic for cccccc, got {diagnostics}",
        )
        # Ensure index files were NOT written
        research_dir = self.root / ".agents" / "docs" / "research"
        self.assertFalse((research_dir / "INDEX.json").exists())
        self.assertFalse((research_dir / "INDEX.md").exists())

    # ----------------------------------------------------------------------------------
    # Human audience invariance assertions
    # ----------------------------------------------------------------------------------

    def test_human_invariance_per_verb(self):
        for verb in VERBS:
            with self.subTest(verb=verb):
                verb_dir = self.root / f"human_{verb}"
                verb_dir.mkdir(parents=True, exist_ok=True)
                index_dir, _rel_dir = _setup_fixture_for_verb(verb_dir, verb)

                res1 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res1.returncode, 0)
                self.assertEqual(res1.stdout, HUMAN_FIRST_RUN[verb])

                res2 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res2.returncode, 0)
                self.assertEqual(res2.stdout, HUMAN_SECOND_RUN[verb])

                # Third run: append comment to INDEX.md
                with open(index_dir / "INDEX.md", "a", encoding="utf-8") as f:
                    f.write("\n<!-- comment -->\n")
                res3 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res3.returncode, 0)
                self.assertEqual(res3.stdout, HUMAN_MD_ONLY_RUN[verb])

                # Fourth run: overwrite INDEX.json with "{}\n"
                (index_dir / "INDEX.json").write_text("{}\n", encoding="utf-8")
                res4 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res4.returncode, 0)
                self.assertEqual(res4.stdout, HUMAN_JSON_ONLY_RUN[verb])

    # ----------------------------------------------------------------------------------
    # Unsupported-type regression assertion
    # ----------------------------------------------------------------------------------

    def test_unsupported_type_specs(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        res = run_cli(["index", "specs", "--agent"], cwd=self.root)
        self.assertEqual(res.returncode, 2)
        lines = res.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("kind"), "error")
        self.assertEqual(rec.get("outcome"), "cannot-run")
        self.assertEqual(rec.get("exit"), 2)

    # ----------------------------------------------------------------------------------
    # aw index all write path behavior assertions (E-04)
    # ----------------------------------------------------------------------------------

    def test_all_write_first_and_second_run(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _create_fixture_repo(self.root, mode="missing")

        # (a) First run on missing: compact --agent
        res1 = run_cli(["index", "all", "--agent"], cwd=self.root)
        self.assertEqual(res1.returncode, 0)
        lines1 = res1.stdout.splitlines()
        self.assertEqual(len(lines1), 1)
        self._assert_no_leaks(res1.stdout)
        rec1 = json.loads(lines1[0])
        val_errors1 = agent_schema.validate_agent_record(rec1)
        self.assertEqual(val_errors1, [])
        self.assertEqual(rec1.get("target"), "all")
        self.assertEqual(rec1.get("exit"), 0)
        self.assertEqual(rec1.get("outcome"), "ok")
        self.assertIs(rec1.get("applied"), True)
        self.assertEqual(rec1.get("changes"), 6)

        # (b) Second run unchanged: applied is False and no changes key
        res2 = run_cli(["index", "all", "--agent"], cwd=self.root)
        self.assertEqual(res2.returncode, 0)
        lines2 = res2.stdout.splitlines()
        self.assertEqual(len(lines2), 1)
        self._assert_no_leaks(res2.stdout)
        rec2 = json.loads(lines2[0])
        val_errors2 = agent_schema.validate_agent_record(rec2)
        self.assertEqual(val_errors2, [])
        self.assertEqual(rec2.get("exit"), 0)
        self.assertIs(rec2.get("applied"), False)
        self.assertNotIn("changes", rec2)

    def test_all_write_verbose_and_json_paths(self):
        expected_paths = {
            ".aw/records/plans/INDEX.json",
            ".aw/records/plans/INDEX.md",
            ".aw/records/prompts/INDEX.json",
            ".aw/records/prompts/INDEX.md",
            ".aw/records/research/INDEX.json",
            ".aw/records/research/INDEX.md",
        }

        # Check --agent --verbose on fresh missing fixture
        root_v = self.root / "verbose_run"
        root_v.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=root_v, capture_output=True, check=True)
        _create_fixture_repo(root_v, mode="missing")

        res_v = run_cli(["index", "all", "--agent", "--verbose"], cwd=root_v)
        self.assertEqual(res_v.returncode, 0)
        self.assertNotIn(str(root_v), res_v.stdout)
        self._assert_no_leaks(res_v.stdout)
        rec_v = json.loads(res_v.stdout.splitlines()[0])
        val_errors_v = agent_schema.validate_agent_record(rec_v)
        self.assertEqual(val_errors_v, [])
        changes_v = rec_v.get("changes", [])
        self.assertIsInstance(changes_v, list)
        self.assertEqual(len(changes_v), 6)
        self.assertEqual({c.get("path") for c in changes_v}, expected_paths)

        # Check --json on fresh missing fixture
        root_j = self.root / "json_run"
        root_j.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=root_j, capture_output=True, check=True)
        _create_fixture_repo(root_j, mode="missing")

        res_j = run_cli(["index", "all", "--json"], cwd=root_j)
        self.assertEqual(res_j.returncode, 0)
        self.assertNotIn(str(root_j), res_j.stdout)
        self._assert_no_leaks(res_j.stdout)
        doc_j = json.loads(res_j.stdout)
        self.assertIsInstance(doc_j, dict)
        changes_j = doc_j.get("changes", [])
        self.assertEqual(len(changes_j), 6)
        self.assertEqual({c.get("path") for c in changes_j}, expected_paths)
        data_j = doc_j.get("data", {})
        self.assertNotIn("repo_root", data_j)

    def test_all_write_mixed_outcome_refusal(self):
        subprocess.run(["git", "init"], cwd=self.root, capture_output=True, check=True)
        _create_fixture_repo(self.root, mode="missing")
        shutil.rmtree(self.root / ".aw" / "records" / "research", ignore_errors=True)
        _write(
            self.root,
            set_id="seta",
            order=1,
            id6="cccccc",
            slug="notes",
            status="bogus-status",
            created="20260701",
        )

        # --agent
        res_agent = run_cli(["index", "all", "--agent"], cwd=self.root)
        self.assertEqual(res_agent.returncode, 1)
        lines = res_agent.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        self._assert_no_leaks(res_agent.stdout)
        rec = json.loads(lines[0])
        val_errors = agent_schema.validate_agent_record(rec)
        self.assertEqual(val_errors, [])
        self.assertEqual(rec.get("exit"), 1)
        self.assertEqual(rec.get("outcome"), "findings")
        self.assertIs(rec.get("applied"), True)
        self.assertIs(rec.get("complete"), False)
        # 4 changes written (2 for plans, 2 for prompts)
        changes = rec.get("changes")
        self.assertEqual(changes if isinstance(changes, int) else len(changes), 4)
        diags = rec.get("diagnostics", [])
        self.assertTrue(
            any(
                d.get("rule") == "frontmatter-invalid"
                and "cccccc" in d.get("location", "")
                for d in diags
            ),
            f"Expected frontmatter-invalid diagnostic for cccccc, got {diags}",
        )
        research_dir = self.root / ".agents" / "docs" / "research"
        self.assertFalse((research_dir / "INDEX.json").exists())
        self.assertFalse((research_dir / "INDEX.md").exists())

        # --json document with exit_code == 1
        res_json = run_cli(["index", "all", "--json"], cwd=self.root)
        self.assertEqual(res_json.returncode, 1)
        doc = json.loads(res_json.stdout)
        self.assertEqual(doc.get("exit_code"), 1)

    def test_all_write_human_invariance(self):
        repo_all = self.root / "human_all"
        repo_all.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=repo_all, capture_output=True, check=True)
        _create_fixture_repo(repo_all, mode="missing")

        repo_single = self.root / "human_single"
        repo_single.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init"], cwd=repo_single, capture_output=True, check=True
        )
        _create_fixture_repo(repo_single, mode="missing")

        res_all = run_cli(["index", "all"], cwd=repo_all)
        res_p = run_cli(["index", "plans"], cwd=repo_single)
        res_pr = run_cli(["index", "prompts"], cwd=repo_single)
        res_r = run_cli(["index", "research"], cwd=repo_single)

        expected_stdout = res_p.stdout + res_pr.stdout + res_r.stdout
        expected_rc = max(res_p.returncode, res_pr.returncode, res_r.returncode)

        self.assertEqual(res_all.returncode, expected_rc)
        self.assertEqual(res_all.stdout, expected_stdout)


# --------------------------------------------------------------------------------------
# Missing-dir write refusal behavior tests (plan fbdxmh, E-03 a..e)
# --------------------------------------------------------------------------------------


class IndexWriteMissingDirTests(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self._temp_dir.name)

    def tearDown(self):
        self._temp_dir.cleanup()

    # (a) BARE GIT REPO (no .aw/): for each verb in VERBS
    def test_bare_repo_agent_refusal_per_verb(self):
        for verb in VERBS:
            with self.subTest(verb=verb):
                repo = self.temp_dir / f"repo_{verb}"
                repo.mkdir()
                subprocess.run(
                    ["git", "init"], cwd=repo, capture_output=True, check=True
                )
                home = self.temp_dir / f"home_{verb}"
                home.mkdir()

                with mock.patch.dict(os.environ):
                    os.environ.pop("AW_HOME", None)
                    os.environ.pop("XDG_CONFIG_HOME", None)
                    os.environ.pop("AW_CONFIG_DIR", None)
                    res = run_cli(
                        ["index", verb, "--agent"],
                        cwd=repo,
                        env_overrides={"HOME": str(home)},
                    )

                self.assertEqual(res.returncode, 2, f"{verb} rc != 2: {res.returncode}")
                self.assertNotIn(
                    "Traceback",
                    res.stderr,
                    f"{verb} Traceback on stderr: {res.stderr}",
                )
                lines = res.stdout.splitlines()
                self.assertEqual(
                    len(lines), 1, f"Expected 1 line for {verb}, got: {res.stdout}"
                )
                rec = json.loads(lines[0])
                val_errs = agent_schema.validate_agent_record(rec)
                self.assertEqual(
                    val_errs, [], f"Validation errors for {verb}: {val_errs}"
                )
                self.assertEqual(rec.get("kind"), "error")
                self.assertEqual(rec.get("cmd"), "index")
                self.assertEqual(rec.get("target"), verb)
                self.assertEqual(rec.get("outcome"), "cannot-run")
                self.assertEqual(rec.get("exit"), 2)
                self.assertIs(rec.get("verified"), False)
                self.assertIs(rec.get("complete"), False)
                self.assertIs(rec.get("applied"), False)
                self.assertEqual(rec.get("next"), "aw install .")
                diags = rec.get("diagnostics", [])
                self.assertEqual(len(diags), 1)
                self.assertEqual(diags[0].get("rule"), "records-dir-missing")
                self.assertNotIn(str(home), res.stdout)
                self.assertNotIn(str(repo), res.stdout)
                self.assertEqual([p for p in repo.iterdir() if p.name != ".git"], [])
                self.assertEqual(list(home.iterdir()), [])

    # (b) PARTIAL TREE: only .aw/records/plans/ created, aw index all --agent
    def test_partial_tree_all_write_refusal(self):
        repo = self.temp_dir / "repo_partial"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        (repo / ".aw" / "records" / "plans").mkdir(parents=True)
        home = self.temp_dir / "home_partial"
        home.mkdir()

        with mock.patch.dict(os.environ):
            os.environ.pop("AW_HOME", None)
            os.environ.pop("XDG_CONFIG_HOME", None)
            os.environ.pop("AW_CONFIG_DIR", None)
            res = run_cli(
                ["index", "all", "--agent"],
                cwd=repo,
                env_overrides={"HOME": str(home)},
            )

        self.assertEqual(res.returncode, 2, f"rc != 2: {res.returncode}")
        self.assertNotIn("Traceback", res.stderr)
        lines = [line for line in res.stdout.splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 1)
        for line in lines:
            r = json.loads(line)
            self.assertEqual(agent_schema.validate_agent_record(r), [])
        last_rec = json.loads(lines[-1])
        self.assertEqual(last_rec.get("kind"), "error")
        self.assertIn(last_rec.get("outcome"), ("cannot-run", "error"))
        self.assertEqual(last_rec.get("exit"), 2)

    # (c) --json and human mode per verb on a bare git repo
    def test_bare_repo_json_and_human_refusal_per_verb(self):
        for verb in VERBS:
            with self.subTest(verb=verb, audience="json"):
                repo = self.temp_dir / f"repo_json_{verb}"
                repo.mkdir()
                subprocess.run(
                    ["git", "init"], cwd=repo, capture_output=True, check=True
                )
                home = self.temp_dir / f"home_json_{verb}"
                home.mkdir()

                with mock.patch.dict(os.environ):
                    os.environ.pop("AW_HOME", None)
                    os.environ.pop("XDG_CONFIG_HOME", None)
                    os.environ.pop("AW_CONFIG_DIR", None)
                    res = run_cli(
                        ["index", verb, "--json"],
                        cwd=repo,
                        env_overrides={"HOME": str(home)},
                    )

                self.assertEqual(
                    res.returncode, 2, f"{verb} --json rc != 2: {res.returncode}"
                )
                doc = json.loads(res.stdout)
                self.assertEqual(doc.get("status"), "cannot-run")
                self.assertEqual(doc.get("exit_code"), 2)
                index_dir = doc.get("data", {}).get("index_dir")
                self.assertIsNotNone(index_dir)
                self.assertFalse(
                    Path(index_dir).is_absolute(), f"{index_dir} is absolute"
                )

            with self.subTest(verb=verb, audience="human"):
                repo = self.temp_dir / f"repo_human_{verb}"
                repo.mkdir()
                subprocess.run(
                    ["git", "init"], cwd=repo, capture_output=True, check=True
                )
                home = self.temp_dir / f"home_human_{verb}"
                home.mkdir()

                with mock.patch.dict(os.environ):
                    os.environ.pop("AW_HOME", None)
                    os.environ.pop("XDG_CONFIG_HOME", None)
                    os.environ.pop("AW_CONFIG_DIR", None)
                    res = run_cli(
                        ["index", verb],
                        cwd=repo,
                        env_overrides={"HOME": str(home)},
                    )

                self.assertEqual(
                    res.returncode, 2, f"{verb} human rc != 2: {res.returncode}"
                )
                self.assertEqual(res.stdout, "")
                self.assertIn("records directory", res.stderr)
                self.assertIn("aw install", res.stderr)

    # (d) EXPLICIT --dir INSIDE A PROJECT
    def test_explicit_dir_inside_project(self):
        repo = self.temp_dir / "repo_proj"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        home = self.temp_dir / "home_proj"
        home.mkdir()

        with mock.patch.dict(os.environ):
            os.environ.pop("AW_HOME", None)
            os.environ.pop("XDG_CONFIG_HOME", None)
            os.environ.pop("AW_CONFIG_DIR", None)
            res_inst = run_cli(
                ["install", ".", "-y", "--no-interactive"],
                cwd=repo,
                env_overrides={"HOME": str(home)},
            )
            self.assertEqual(
                res_inst.returncode, 0, f"install failed: {res_inst.stderr}"
            )

            sub = repo / "sub"
            sub.mkdir()

            res = run_cli(
                ["index", "plans", "--dir", "sub", "--agent"],
                cwd=repo,
                env_overrides={"HOME": str(home)},
            )

        self.assertEqual(res.returncode, 2, f"rc != 2: {res.returncode}")
        self.assertNotIn("Traceback", res.stderr)
        lines = res.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertEqual(rec.get("outcome"), "cannot-run")
        self.assertNotEqual(rec.get("next"), "aw install .")
        self.assertFalse((sub / ".aw").exists(), "sub/.aw was created")

    # (e) in-process quiet=True
    def test_inprocess_quiet_true(self):
        repo = self.temp_dir / "repo_quiet"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        home = self.temp_dir / "home_quiet"
        home.mkdir()

        with mock.patch.dict(os.environ, {"HOME": str(home), "AW_HOME": str(home)}):
            for mod, name in [
                (plans_index, "plans"),
                (prompts_index, "prompts"),
                (research_index, "research"),
            ]:
                with self.subTest(module=name):
                    args = argparse.Namespace(
                        dir=str(repo),
                        check=False,
                        agent=False,
                        json=False,
                        limit=None,
                        quiet=True,
                    )
                    out_buf = io.StringIO()
                    err_buf = io.StringIO()
                    with contextlib.redirect_stdout(
                        out_buf
                    ), contextlib.redirect_stderr(err_buf):
                        rc = mod.run_index(args)
                    self.assertEqual(rc, 2, f"{name} rc != 2: {rc}")
                    self.assertEqual(out_buf.getvalue(), "", f"{name} stdout not empty")
                    self.assertEqual(err_buf.getvalue(), "", f"{name} stderr not empty")


if __name__ == "__main__":
    unittest.main()
