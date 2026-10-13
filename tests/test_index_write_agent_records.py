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
- Human invariance: unflagged stdout on fixture matches legacy expected strings byte-exact.
- Unsupported type: index specs --agent emits a kind:error record at exit 2.

In accordance with GUIDING_PRINCIPLES P16, this module performs zero static analysis:
no AST checks, no source code regex, no caller census, and no symbol-existence tests.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import agent_schema
from tests.conformance_matrix import REPO_ROOT, run_cli
from tests.test_index_check_agent_records import _create_fixture_repo
from tests.test_research_index import _write

VERBS = ("plans", "prompts", "research")

HUMAN_FIRST_RUN = {
    "plans": "wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    "prompts": "wrote INDEX.json (1 prompts)\nwrote INDEX.md\n",
    "research": "wrote        .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
}

HUMAN_SECOND_RUN = {
    "plans": "up to date   .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n",
    "prompts": "wrote INDEX.json (1 prompts)\nwrote INDEX.md\n",
    "research": "up to date   .agents/docs/research/INDEX.json, INDEX.md (1 docs)\n",
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
                _setup_fixture_for_verb(verb_dir, verb)

                res1 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res1.returncode, 0)
                self.assertEqual(res1.stdout, HUMAN_FIRST_RUN[verb])

                res2 = run_cli(["index", verb], cwd=verb_dir)
                self.assertEqual(res2.returncode, 0)
                self.assertEqual(res2.stdout, HUMAN_SECOND_RUN[verb])

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


if __name__ == "__main__":
    unittest.main()
