"""Tests for research document companion directories (IPD mtdxiu, Set rescomp).

Covers:
(a) index lists the companion and a .md inside it is not indexed and does not fail index;
(b) --check exits 1 on an orphan and 0 once fixed;
(c) mv carries the companion and rewrites a <stem>.data/t.csv citation;
(d) set-assign carries it;
(e) a colliding destination companion makes mv exit nonzero and move nothing;
(f) promote --to reference carries it into the shard;
(g) archive <id6> carries it;
(h) aw attention --check exits 0 with a companion present, including a non-Markdown file such as r.txt;
(j) with a conformantly named copy of the doc inside its companion, aw find <id6> lists one file and no duplicate warning;
(i) a conformantly named .md with front matter inside a companion does not affect aw research new order or id6 minting.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Tuple
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows import research_contract as R


class TestResearchCompanion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_rescomp_")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

        self.repo_dir = self.tmp / "repo"
        self.research_root = self.repo_dir / ".aw" / "records" / "research"
        self.research_root.mkdir(parents=True, exist_ok=True)

        self.env_patcher = patch.dict(
            os.environ,
            {
                "HOME": str(self.tmp),
                "XDG_CONFIG_HOME": str(self.tmp),
                "AW_NO_REEXEC": "1",
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        subprocess.run(
            ["git", "init", "-b", "main", "-q"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "tests@example.com"],
            cwd=self.repo_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=self.repo_dir, check=True
        )

        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "initial commit"],
            cwd=self.repo_dir,
            check=True,
        )

        # Install agent-workflows with private-target preset into the repo
        self._run_cli(
            ["install", str(self.repo_dir), "-y", "--preset", "private-target"]
        )

    def _run_cli(self, cmd: list[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        old_cwd = Path.cwd()
        os.chdir(self.repo_dir)
        try:
            with redirect_stdout(out), redirect_stderr(err):
                try:
                    rc = cli.main(cmd)
                except SystemExit as e:
                    rc = int(e.code or 0)
        finally:
            os.chdir(old_cwd)
        return rc, out.getvalue(), err.getvalue()

    def _create_report(
        self, set_id: str = "probe", slug: str = "rep", kind: str = "research-report"
    ) -> Tuple[Path, str, str]:
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                "--set",
                set_id,
                "--kind",
                kind,
                "--slug",
                slug,
                "--summary",
                "Summary test",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"research new failed: {err}")
        # Find created doc
        docs = [
            p
            for p in self.research_root.glob("*.md")
            if p.name not in ("INDEX.md", "README.md") and slug in p.name
        ]
        self.assertEqual(len(docs), 1)
        doc_path = docs[0]
        parsed, _ = R.parse_name(doc_path.name)
        assert parsed is not None
        return doc_path, doc_path.name[:-3], parsed.id6

    def test_a_index_lists_companion_and_skips_inner_md(self):
        """(a) index lists the companion and a .md inside it is not indexed and does not fail index."""
        doc_path, stem, id6 = self._create_report(slug="rep-a")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "data.csv").write_text("col1,col2\n1,2\n", encoding="utf-8")
        (comp_dir / "notes.md").write_text(
            "---\nid: inv001\nkind: notes\n---\nSome companion notes\n",
            encoding="utf-8",
        )

        # Regenerate index
        rc, out, err = self._run_cli(["research", "index"])
        self.assertEqual(rc, 0, f"index failed: {err}")
        self.assertIn("(1 docs)", out)

        index_json_path = self.research_root / "INDEX.json"
        self.assertTrue(index_json_path.is_file())
        entries = json.loads(index_json_path.read_text(encoding="utf-8"))
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id6"], id6)
        self.assertEqual(entries[0]["companion"], f"{stem}.data")

        # Confirm notes.md did not cause drift
        rc_check, out_check, err_check = self._run_cli(["research", "index", "--check"])
        self.assertEqual(rc_check, 0, f"index --check failed: {out_check}\n{err_check}")
        self.assertIn("clean", out_check)

    def test_b_check_exits_1_on_orphan_and_0_once_fixed(self):
        """(b) --check exits 1 on an orphan and 0 once fixed."""
        doc_path, stem, id6 = self._create_report(slug="rep-b")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "data.csv").write_text("x,y\n", encoding="utf-8")

        # Save content then remove the doc to create an orphan
        doc_text = doc_path.read_text(encoding="utf-8")
        doc_path.unlink()

        rc, out, err = self._run_cli(["research", "index", "--check"])
        self.assertEqual(rc, 1)
        self.assertIn("check.research-companion-orphaned", out)

        # Check with aw check -a research reports the same
        rc_check, out_chk, _ = self._run_cli(["check", "-a", "research"])
        self.assertEqual(rc_check, 1)
        self.assertIn("check.research-companion-orphaned", out_chk)

        # Restore doc and refresh index
        doc_path.write_text(doc_text, encoding="utf-8")
        self._run_cli(["research", "index"])
        rc_clean, out_clean, _ = self._run_cli(["research", "index", "--check"])
        self.assertEqual(rc_clean, 0, f"expected clean: {out_clean}")

    def test_c_mv_carries_companion_and_rewrites_citation(self):
        """(c) mv carries the companion and rewrites a <stem>.data/t.csv citation."""
        doc_path, stem, id6 = self._create_report(slug="rep-c")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "t.csv").write_text("a,b,c\n", encoding="utf-8")

        # Commit before mv so git mv tracks it
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add doc and companion"],
            cwd=self.repo_dir,
            check=True,
        )

        # Create another doc that cites <stem>.data/t.csv
        # Note: iter_scan_files scans paths in SCAN_ROOTS (e.g. DECISIONS.md, .aw/records/...)
        cite_file = self.repo_dir / "DECISIONS.md"
        cite_file.write_text(
            f"See data in {stem}.data/t.csv for details.\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "DECISIONS.md"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add citation"], cwd=self.repo_dir, check=True
        )

        # Preview mv
        rc_prev, out_prev, _ = self._run_cli(
            ["research", "mv", id6, "--slug", "renamed-c"]
        )
        self.assertEqual(rc_prev, 0)
        self.assertIn(f"--- would rename {comp_dir} ->", out_prev)

        # Apply mv
        rc, out, err = self._run_cli(
            [
                "research",
                "mv",
                id6,
                "--slug",
                "renamed-c",
                "--apply",
                "--no-interactive",
            ]
        )
        self.assertEqual(rc, 0, f"mv failed: {err}")

        # Check companion directory renamed
        self.assertFalse(comp_dir.exists())
        new_docs = [
            p
            for p in self.research_root.glob("*.md")
            if p.name not in ("INDEX.md", "README.md") and "renamed-c" in p.name
        ]
        self.assertEqual(len(new_docs), 1)
        new_stem = new_docs[0].name[:-3]
        new_comp_dir = self.research_root / f"{new_stem}.data"
        self.assertTrue(new_comp_dir.is_dir())
        self.assertTrue((new_comp_dir / "t.csv").is_file())

        # Check citation was rewritten
        cite_text = cite_file.read_text(encoding="utf-8")
        self.assertIn(f"{new_stem}.data/t.csv", cite_text)
        self.assertNotIn(f"{stem}.data/t.csv", cite_text)

        # Check git status shows renames when staged
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        res = subprocess.run(
            ["git", "status", "--short"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("R  ", res.stdout)

    def test_d_set_assign_carries_companion(self):
        """(d) set-assign carries it."""
        doc_path, stem, id6 = self._create_report(set_id="oldset", slug="rep-d")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "ledger.csv").write_text("1,2\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "doc d"], cwd=self.repo_dir, check=True)

        rc, out, err = self._run_cli(
            [
                "research",
                "set-assign",
                id6,
                "--set",
                "newset",
                "--apply",
                "--no-interactive",
            ]
        )
        self.assertEqual(rc, 0, f"set-assign failed: {err}")
        self.assertFalse(comp_dir.exists())

        new_docs = [
            p
            for p in self.research_root.glob("*.md")
            if p.name not in ("INDEX.md", "README.md") and "newset" in p.name
        ]
        self.assertEqual(len(new_docs), 1)
        new_comp = self.research_root / f"{new_docs[0].name[:-3]}.data"
        self.assertTrue(new_comp.is_dir())
        self.assertTrue((new_comp / "ledger.csv").is_file())

    def test_e_colliding_destination_companion_refuses_mv(self):
        """(e) a colliding destination companion makes mv exit nonzero and move nothing."""
        doc_path, stem, id6 = self._create_report(slug="rep-e")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "data.csv").write_text("1\n", encoding="utf-8")

        # Synthesize expected destination companion
        parsed, _ = R.parse_name(doc_path.name)
        assert parsed is not None
        dest_name = R.format_name(parsed._replace(slug="collide"))
        dest_comp = self.research_root / f"{dest_name[:-3]}.data"
        dest_comp.mkdir(parents=True, exist_ok=True)
        (dest_comp / "collision.txt").write_text("existing\n", encoding="utf-8")

        rc, out, err = self._run_cli(
            ["research", "mv", id6, "--slug", "collide", "--apply", "--no-interactive"]
        )
        self.assertNotEqual(rc, 0)
        self.assertTrue(doc_path.is_file(), "original doc should not be moved")
        self.assertTrue(comp_dir.is_dir(), "original companion should not be moved")
        self.assertTrue((dest_comp / "collision.txt").is_file())

    def test_f_promote_to_reference_carries_companion(self):
        """(f) promote --to reference carries it into the shard."""
        doc_path, stem, id6 = self._create_report(slug="rep-f")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "t.csv").write_text("1,2,3\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "doc f"], cwd=self.repo_dir, check=True)

        # Preview promote
        rc_prev, out_prev, _ = self._run_cli(
            ["research", "promote", id6, "--to", "reference"]
        )
        self.assertEqual(rc_prev, 0)
        self.assertIn("would move companion", out_prev)

        # Apply promote
        rc, out, err = self._run_cli(
            ["research", "promote", id6, "--to", "reference", "--apply"]
        )
        self.assertEqual(rc, 0, f"promote failed: {err}")

        # Check carried into reference shard
        sharded_docs = list((self.research_root / "reference").rglob("*.md"))
        self.assertEqual(len(sharded_docs), 1)
        sharded_doc = sharded_docs[0]
        sharded_comp = sharded_doc.parent / f"{sharded_doc.name[:-3]}.data"
        self.assertTrue(sharded_comp.is_dir())
        self.assertTrue((sharded_comp / "t.csv").is_file())
        self.assertFalse(comp_dir.exists())

    def test_g_archive_carries_companion(self):
        """(g) archive <id6> carries it."""
        doc_path, stem, id6 = self._create_report(slug="rep-g")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "archived.csv").write_text("old\n", encoding="utf-8")

        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", "doc g"], cwd=self.repo_dir, check=True)

        rc, out, err = self._run_cli(["archive", id6, "--apply"])
        self.assertEqual(rc, 0, f"archive failed: {err}")

        sharded_docs = list((self.research_root / "archive").rglob("*.md"))
        self.assertEqual(len(sharded_docs), 1)
        sharded_doc = sharded_docs[0]
        sharded_comp = sharded_doc.parent / f"{sharded_doc.name[:-3]}.data"
        self.assertTrue(sharded_comp.is_dir())
        self.assertTrue((sharded_comp / "archived.csv").is_file())
        self.assertFalse(comp_dir.exists())

    def test_h_attention_check_exits_0_with_companion(self):
        """(h) aw attention --check exits 0 with a companion present, including a non-Markdown file such as r.txt."""
        doc_path, stem, id6 = self._create_report(slug="rep-h")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        (comp_dir / "r.txt").write_text("raw text\n", encoding="utf-8")
        (comp_dir / "notes.md").write_text("notes\n", encoding="utf-8")

        self._run_cli(["research", "index"])

        rc, out, err = self._run_cli(["attention", "--check"])
        self.assertEqual(rc, 0, f"attention --check failed: {out}\n{err}")

    def test_j_find_lists_one_file_no_duplicate_warning(self):
        """(j) with a conformantly named copy of the doc inside its companion, aw find <id6> lists one file and no duplicate warning."""
        doc_path, stem, id6 = self._create_report(slug="rep-j")
        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        # Put conformant copy of doc inside companion
        (comp_dir / doc_path.name).write_text(
            doc_path.read_text(encoding="utf-8"), encoding="utf-8"
        )

        self._run_cli(["research", "index"])

        rc, out, err = self._run_cli(["find", id6])
        self.assertEqual(rc, 0, f"find failed: {err}")
        self.assertNotIn("claimed by 2 files", out)
        # Should only list 1 file
        lines = [line for line in out.strip().splitlines() if id6 in line]
        self.assertEqual(len(lines), 1)

    def test_i_inner_md_does_not_affect_new_order_or_id6_minting(self):
        """(i) a conformantly named .md with front matter inside a companion does not affect aw research new order or id6 minting."""
        doc_path, stem, id6 = self._create_report(set_id="orderset", slug="first")
        parsed, _ = R.parse_name(doc_path.name)
        assert parsed is not None
        self.assertEqual(parsed.order, "01")

        comp_dir = self.research_root / f"{stem}.data"
        comp_dir.mkdir(parents=True, exist_ok=True)
        # Place a fake order 02 inside companion
        fake_name = R.format_name(
            parsed._replace(order="02", id6="fake02", slug="inner")
        )
        fake_fm = "---\nid: fake02\ncreated: 20261012\nset: orderset\norder: '02'\ntopic: [t]\nmodel: ''\nkind: research-report\nstatus: todo\noutcome: none-yet\nsummary: s\nconsumed-by: []\n---\n"
        (comp_dir / fake_name).write_text(fake_fm, encoding="utf-8")

        # Now create second doc in the same set
        doc2_path, stem2, id2 = self._create_report(set_id="orderset", slug="second")
        parsed2, _ = R.parse_name(doc2_path.name)
        assert parsed2 is not None
        # It should receive order 02 because inner doc was skipped!
        self.assertEqual(parsed2.order, "02")
        self.assertNotEqual(id2, "fake02")


if __name__ == "__main__":
    unittest.main()
