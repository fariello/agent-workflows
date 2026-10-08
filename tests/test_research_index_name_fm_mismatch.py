"""Tests for research index name-vs-frontmatter mismatch detection (IPD okw4ke).

Verifies that `aw research index --check` catches mismatches between filename facets
and front matter for:
- order (two-digit NN mismatch)
- kind (semantic mismatch, while accepting normalized kind aliases)
- model (mismatch or empty front matter on a filename with a model facet,
  while accepting front-matter model on a filename without a model facet).
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests import support


class ResearchIndexNameFmMismatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="aw_test_rfm_")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

        self.repo_dir = self.tmp_dir / "repo"
        support.init_repo(self.repo_dir)

        self.env = {
            "HOME": str(self.tmp_dir),
            "XDG_CONFIG_HOME": str(self.tmp_dir / ".config"),
            "AW_NO_REEXEC": "1",
        }

        # Install agent-workflows into target repo
        support.run_cli(
            "install",
            ".",
            "-y",
            "--preset",
            "private-target",
            cwd=self.repo_dir,
            env=self.env,
        )

        # Create two research files in set 'tst' using 'research new --apply' subprocess
        # 1. Plain file (order 01)
        support.run_cli(
            "research",
            "new",
            "--set",
            "tst",
            "--slug",
            "plaindoc",
            "--kind",
            "research-report",
            "--apply",
            cwd=self.repo_dir,
            env=self.env,
        )
        # 2. Model file (will be order 02 with .gpt56. facet)
        support.run_cli(
            "research",
            "new",
            "--set",
            "tst",
            "--slug",
            "modeldoc",
            "--kind",
            "research-report",
            "--model",
            "gpt56",
            "--apply",
            cwd=self.repo_dir,
            env=self.env,
        )

        rroot = self.repo_dir / ".aw" / "records" / "research"
        plain_files = list(rroot.glob("*plaindoc.research-report.md"))
        self.assertEqual(len(plain_files), 1)
        self.plain_file = plain_files[0]
        self.assertIn("-01-", self.plain_file.name)

        model_files = list(rroot.glob("*modeldoc.gpt56.research-report.md"))
        self.assertEqual(len(model_files), 1)
        self.model_file = model_files[0]

        # Generate initial index
        proc = support.run_cli("research", "index", cwd=self.repo_dir, env=self.env)
        self.assertEqual(proc.returncode, 0, f"index failed: {proc.stderr}")

    def _check(self):
        return support.run_cli(
            "research", "index", "--check", cwd=self.repo_dir, env=self.env
        )

    # Flagged cases

    def test_flagged_order_mismatch(self):
        orig = self.plain_file.read_text(encoding="utf-8")
        self.addCleanup(self.plain_file.write_text, orig, encoding="utf-8")
        self.plain_file.write_text(
            orig.replace("order: 01", "order: 05"), encoding="utf-8"
        )

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("name-frontmatter-mismatch", output)
        self.assertIn("order 05 != name 01", output)

    def test_flagged_kind_mismatch(self):
        orig = self.plain_file.read_text(encoding="utf-8")
        self.addCleanup(self.plain_file.write_text, orig, encoding="utf-8")
        self.plain_file.write_text(
            orig.replace("kind: research-report", "kind: findings"), encoding="utf-8"
        )

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("name-frontmatter-mismatch", output)
        self.assertIn("kind findings != name research-report", output)

    def test_flagged_model_mismatch(self):
        orig = self.model_file.read_text(encoding="utf-8")
        self.addCleanup(self.model_file.write_text, orig, encoding="utf-8")
        self.model_file.write_text(
            orig.replace("model: gpt56", "model: sonnet5"), encoding="utf-8"
        )

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("name-frontmatter-mismatch", output)
        self.assertIn("model sonnet5 != name gpt56", output)

    def test_flagged_model_empty_on_model_name(self):
        orig = self.model_file.read_text(encoding="utf-8")
        self.addCleanup(self.model_file.write_text, orig, encoding="utf-8")
        self.model_file.write_text(
            orig.replace("model: gpt56", "model:"), encoding="utf-8"
        )

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("name-frontmatter-mismatch", output)
        self.assertIn("model (empty) != name gpt56", output)

    # Clean cases

    def test_clean_untouched_files(self):
        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, f"expected clean check, got: {output}")
        self.assertNotIn("name-frontmatter-mismatch", output)
        self.assertIn("index --check: clean", output)

    def test_clean_kind_alias(self):
        orig = self.plain_file.read_text(encoding="utf-8")
        self.addCleanup(self.plain_file.write_text, orig, encoding="utf-8")
        # Legacy kind alias 'research' normalizes to 'research-report'
        self.plain_file.write_text(
            orig.replace("kind: research-report", "kind: research"), encoding="utf-8"
        )

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, f"expected clean check, got: {output}")
        self.assertNotIn("name-frontmatter-mismatch", output)
        self.assertIn("index --check: clean", output)

    def test_clean_model_on_name_without_model_facet(self):
        orig = self.plain_file.read_text(encoding="utf-8")
        self.addCleanup(self.plain_file.write_text, orig, encoding="utf-8")
        # Spec Section 4.4: front matter model without filename model facet is legal
        content = orig.replace("model: \n", "model: gpt56\n").replace(
            "model:\n", "model: gpt56\n"
        )
        self.plain_file.write_text(content, encoding="utf-8")
        # Refresh index so INDEX.json records the front matter model
        support.run_cli("research", "index", cwd=self.repo_dir, env=self.env)

        proc = self._check()
        output = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 0, f"expected clean check, got: {output}")
        self.assertNotIn("name-frontmatter-mismatch", output)
        self.assertIn("index --check: clean", output)
