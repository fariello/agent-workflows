"""Behavior tests for the `aw index <type>` alias across agent, json, and human audiences.

Metastore `tqknnc` (spec `4sd62s` 4.5) made every typed `aw index` spelling an alias of
`aw index rebuild`: it rebuilds the gitignored metadata cache, prints one `index-alias` notice,
and writes no INDEX file. Plan `f6y2yy` retargeted this module off the deleted INDEX write path.
It drives the verbs (`plans`, `prompts`, `research`, `all`) against isolated fixture repositories
(never the live tree), asserting:
- Under `--agent`: stdout is exactly one line that json.loads parses,
  agent_schema.validate_agent_record returns [], its exit equals the process exit code, it names
  the spelling in an `index-alias` diagnostic, and it carries no escape code or home path.
- Under `--json`: stdout parses as one JSON document with no absolute path anywhere.
- Content findings move to `--check`: a plan lacking `- Id:` reports `id-missing`, and a
  frontmatter-invalid research doc reports `frontmatter-invalid` at exit 1.
- Human invariance: each typed spelling prints the same stdout as `aw index rebuild`.
- Unsupported type: `index specs --agent` emits a kind:error record at exit 2.
- Missing-dir refusal: a bare repo refuses at exit 2 and creates nothing.
- No run writes an INDEX file.

In accordance with GUIDING_PRINCIPLES P16, this module performs zero static analysis:
no AST checks, no source code regex, no caller census, and no symbol-existence tests.
"""

from __future__ import annotations

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

from agent_workflows import agent_schema, meta_cli
from tests.conformance_matrix import REPO_ROOT, run_cli_inproc as run_cli
from tests.record_builder import RecordBuilder
from tests.test_index_check_agent_records import _create_fixture_repo
from tests.test_research_index import _write

VERBS = ("plans", "prompts", "research")

NOTICE_TAIL = "is an alias of `aw index rebuild`; INDEX files are no longer generated"


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


def _index_files(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix() for p in root.rglob("INDEX.*") if p.is_file()
    )


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

    def _single_record(self, res) -> dict:
        lines = res.stdout.splitlines()
        self.assertEqual(len(lines), 1, f"Expected single line, got: {res.stdout!r}")
        self._assert_no_leaks(res.stdout)
        rec = json.loads(lines[0])
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertEqual(rec.get("exit"), res.returncode)
        return rec

    # ----------------------------------------------------------------------------------
    # --agent and --json audience assertions on the alias
    # ----------------------------------------------------------------------------------

    def test_agent_alias_record_per_verb(self):
        for verb in (*VERBS, "all"):
            with self.subTest(verb=verb):
                repo = self.root / f"agent_{verb}"
                repo.mkdir()
                _setup_fixture_for_verb(repo, "plans" if verb == "all" else verb)
                for argv in (["--agent"], ["--agent", "--verbose"]):
                    res = run_cli(["index", verb, *argv], cwd=repo)
                    self.assertEqual(res.returncode, 0, res.stderr)
                    rec = self._single_record(res)
                    self.assertEqual(rec.get("cmd"), "index rebuild")
                    self.assertEqual(rec.get("outcome"), "ok")
                    self.assertIn(
                        ("index-alias", f"aw index {verb}"),
                        [
                            (d.get("rule"), d.get("location"))
                            for d in rec.get("diagnostics", [])
                        ],
                    )
                    self.assertEqual(rec["findings_by_severity"]["error"], 0)
                self.assertEqual(_index_files(repo), [])

    def test_json_alias_document_per_verb(self):
        for verb in (*VERBS, "all"):
            with self.subTest(verb=verb):
                repo = self.root / f"json_{verb}"
                repo.mkdir()
                _setup_fixture_for_verb(repo, "plans" if verb == "all" else verb)
                res = run_cli(["index", verb, "--json"], cwd=repo)
                self.assertEqual(res.returncode, 0, res.stderr)
                self._assert_no_leaks(res.stdout)
                doc = json.loads(res.stdout)
                self.assertIsInstance(doc, dict)
                self.assertEqual(doc.get("exit_code"), 0)
                self.assertNotIn("repo_root", doc.get("data", {}))
                notices = [
                    d
                    for d in doc.get("diagnostics", [])
                    if d.get("rule") == "index-alias"
                ]
                self.assertEqual(len(notices), 1)
                self.assertEqual(
                    notices[0].get("detail"), f"`aw index {verb}` {NOTICE_TAIL}"
                )
                self.assertEqual(_index_files(repo), [])

    # ----------------------------------------------------------------------------------
    # Refusal and drift cases (content findings are reported by --check)
    # ----------------------------------------------------------------------------------

    def test_drift_plans_missing_id(self):
        index_dir, rel_dir = _setup_fixture_for_verb(self.root, "plans")
        (index_dir / "pending" / "20260701-seta-02-noid-plan.ipd.md").write_text(
            RecordBuilder().plan(
                title="Plan lacking id",
                when="2026-07-01",
                plan_role="child",
                author="test",
                set="seta",
                order=2,
                body="## Goal\n\nTest",
                raw_fields={"Id": None, "Status": "pending"},
                text_only=True,
            ),
            encoding="utf-8",
        )
        res = run_cli(["index", "plans", "--check", "--agent"], cwd=self.root)
        self.assertEqual(res.returncode, 1)
        rec = self._single_record(res)
        self.assertEqual(rec.get("outcome"), "findings")
        rules = [d.get("rule") for d in rec.get("diagnostics", [])]
        self.assertIn("id-missing", rules)
        self.assertIn("index-alias", rules)
        # The alias itself still rebuilds and writes no INDEX file.
        res_rb = run_cli(["index", "plans", "--agent"], cwd=self.root)
        self.assertEqual(res_rb.returncode, 0)
        self.assertEqual(self._single_record(res_rb).get("outcome"), "ok")
        self.assertFalse((index_dir / "INDEX.json").exists())
        self.assertFalse((index_dir / "INDEX.md").exists())

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
        res = run_cli(["index", "research", "--check", "--agent"], cwd=self.root)
        self.assertEqual(res.returncode, 1)
        rec = self._single_record(res)
        self.assertEqual(rec.get("outcome"), "findings")
        self.assertGreaterEqual(rec.get("findings", 0), 1)
        diagnostics = rec.get("diagnostics", [])
        self.assertTrue(
            any(
                d.get("rule") == "frontmatter-invalid"
                and "cccccc" in d.get("location", "")
                for d in diagnostics
            ),
            f"Expected frontmatter-invalid diagnostic for cccccc, got {diagnostics}",
        )
        run_cli(["index", "research", "--agent"], cwd=self.root)
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

                res_rb = run_cli(["index", "rebuild"], cwd=verb_dir)
                self.assertEqual(res_rb.returncode, 0)
                self.assertNotIn(NOTICE_TAIL, res_rb.stderr)
                for _ in range(2):
                    res = run_cli(["index", verb], cwd=verb_dir)
                    self.assertEqual(res.returncode, 0)
                    self.assertEqual(res.stdout, res_rb.stdout)
                    self.assertEqual(res.stderr, f"`aw index {verb}` {NOTICE_TAIL}\n")
                self.assertEqual(_index_files(verb_dir), [])

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
    # aw index all alias behavior assertions
    # ----------------------------------------------------------------------------------

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

        # --agent --check: one record, the research finding, exit 1
        res_agent = run_cli(["index", "all", "--check", "--agent"], cwd=self.root)
        self.assertEqual(res_agent.returncode, 1)
        rec = self._single_record(res_agent)
        self.assertEqual(rec.get("outcome"), "findings")
        self.assertEqual(rec.get("target"), "all")
        diags = rec.get("diagnostics", [])
        self.assertTrue(
            any(
                d.get("rule") == "frontmatter-invalid"
                and "cccccc" in d.get("location", "")
                for d in diags
            ),
            f"Expected frontmatter-invalid diagnostic for cccccc, got {diags}",
        )

        # --json --check document with exit_code == 1, blamed on research alone
        res_json = run_cli(["index", "all", "--check", "--json"], cwd=self.root)
        self.assertEqual(res_json.returncode, 1)
        doc = json.loads(res_json.stdout)
        self.assertEqual(doc.get("exit_code"), 1)
        by_type = doc.get("data", {}).get("by_type", {})
        self.assertEqual(by_type.get("plans", {}).get("exit_code"), 0)
        self.assertEqual(by_type.get("prompts", {}).get("exit_code"), 0)
        self.assertEqual(by_type.get("research", {}).get("exit_code"), 1)

        # The alias without --check rebuilds and writes no INDEX file anywhere.
        res_rb = run_cli(["index", "all", "--agent"], cwd=self.root)
        self.assertEqual(res_rb.returncode, 0)
        research_dir = self.root / ".agents" / "docs" / "research"
        self.assertFalse((research_dir / "INDEX.json").exists())
        self.assertFalse((research_dir / "INDEX.md").exists())
        self.assertEqual(_index_files(self.root), [])

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
        res_rb = run_cli(["index", "rebuild"], cwd=repo_single)

        # `aw index all` is ONE alias: one rebuild's output and one notice, not a per-type loop.
        self.assertEqual(res_all.returncode, res_rb.returncode)
        self.assertEqual(res_all.stdout, res_rb.stdout)
        self.assertEqual(res_all.stderr.count(NOTICE_TAIL), 1)
        self.assertEqual(_index_files(repo_all), [])


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
                self.assertEqual(rec.get("cmd"), "index rebuild")
                self.assertEqual(rec.get("outcome"), "cannot-run")
                self.assertEqual(rec.get("exit"), 2)
                self.assertIs(rec.get("verified"), False)
                self.assertIs(rec.get("complete"), False)
                self.assertNotEqual(rec.get("applied"), True)
                self.assertEqual(rec.get("next"), "aw install .")
                diags = rec.get("diagnostics", [])
                self.assertEqual(
                    [d.get("rule") for d in diags],
                    ["index-alias", "records-dir-missing"],
                )
                self.assertEqual(diags[0].get("location"), f"aw index {verb}")
                self.assertNotIn(str(home), res.stdout)
                self.assertNotIn(str(repo), res.stdout)
                self.assertEqual([p for p in repo.iterdir() if p.name != ".git"], [])
                self.assertEqual(list(home.iterdir()), [])

    # (b) PARTIAL TREE: only .aw/records/plans/ created, aw index all --agent. A records root
    # exists, so the alias rebuilds the cache; it creates no records directory and no INDEX file.
    def test_partial_tree_all_rebuilds_without_creating_dirs(self):
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

        self.assertEqual(res.returncode, 0, f"rc != 0: {res.returncode}")
        self.assertNotIn("Traceback", res.stderr)
        lines = [line for line in res.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertEqual(rec.get("outcome"), "ok")
        self.assertEqual(rec.get("exit"), 0)
        self.assertIn(
            {"location": "aw index all", "rule": "index-alias"},
            rec.get("diagnostics", []),
        )
        self.assertEqual(
            sorted(p.name for p in (repo / ".aw" / "records").iterdir()), ["plans"]
        )
        self.assertEqual(list((repo / ".aw" / "records" / "plans").iterdir()), [])
        self.assertEqual(_index_files(repo), [])
        self.assertEqual(list(home.iterdir()), [])

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
                self.assertNotIn(str(repo), res.stdout)
                self.assertNotIn(str(home), res.stdout)
                missing = [
                    d
                    for d in doc.get("diagnostics", [])
                    if d.get("rule") == "records-dir-missing"
                ]
                self.assertEqual(len(missing), 1)
                self.assertFalse(
                    Path(missing[0]["location"]).is_absolute(),
                    f"{missing[0]['location']} is absolute",
                )
                self.assertEqual([p for p in repo.iterdir() if p.name != ".git"], [])

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
                self.assertIn("records directory", res.stdout)
                self.assertIn("aw install", res.stdout)
                self.assertEqual(res.stderr, f"`aw index {verb}` {NOTICE_TAIL}\n")
                self.assertEqual([p for p in repo.iterdir() if p.name != ".git"], [])

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

    # (e) in-process caller: the rebuild API returns a refusal and prints nothing
    def test_inprocess_rebuild_refusal_is_silent(self):
        repo = self.temp_dir / "repo_quiet"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        home = self.temp_dir / "home_quiet"
        home.mkdir()

        with mock.patch.dict(os.environ, {"HOME": str(home), "AW_HOME": str(home)}):
            out_buf = io.StringIO()
            err_buf = io.StringIO()
            with (
                contextlib.redirect_stdout(out_buf),
                contextlib.redirect_stderr(err_buf),
            ):
                result = meta_cli.index_rebuild(repo)
        self.assertEqual(result.exit_code, 2, f"rc != 2: {result.exit_code}")
        self.assertEqual(result.status, "cannot-run")
        self.assertEqual(out_buf.getvalue(), "", "stdout not empty")
        self.assertEqual(err_buf.getvalue(), "", "stderr not empty")
        self.assertEqual([p for p in repo.iterdir() if p.name != ".git"], [])


if __name__ == "__main__":
    unittest.main()
