"""Tests for spec id6 filenames (IPD ha55fi).

Covers the three deliverables:
  E-01 - the `aw specs new` producer (mints id6, clustered filename, `- Id:` metadata, lints clean);
  E-02 - the `normalize_plan_names.is_conformant(..., require_id6=...)` matrix;
  E-03 - the `aw check specs` grandfather cutover (pre-cutover grandfathered, post-cutover enforced);
  E-04 - the `aw rename specs <legacy> --to-id6` minting conversion (+ idempotence on an id6 spec);
  E-05 - the `--to-id6` reference rewrite + fail-loud on an un-auto-rewritable full-path citation.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import cli


def _load_npn():
    return ce._load_normalizer()


class TestIsConformantRequireId6(unittest.TestCase):
    """E-02 / V-02: the additive require_id6 flag on the shared predicate."""

    def setUp(self):
        self.npn = _load_npn()
        self.assertIsNotNone(self.npn, "normalizer must be locatable")

    def test_legacy_spec_default_true_require_false(self):
        # A pure legacy timestamp name (slug not accidentally id6-shaped).
        legacy = "20260701-1200-01-old-task.spec.md"
        # Default preserves current behavior: legacy HHMM form conforms.
        self.assertTrue(self.npn.is_conformant(legacy, "spec"))
        # With require_id6 the legacy form is rejected (no id6 in the name).
        self.assertFalse(self.npn.is_conformant(legacy, "spec", require_id6=True))

    def test_clustered_spec_true_in_both_modes(self):
        clustered = "20260828-ap4jbr-01-ap4jbr-my-spec.spec.md"
        self.assertTrue(self.npn.is_conformant(clustered, "spec"))
        self.assertTrue(self.npn.is_conformant(clustered, "spec", require_id6=True))

    def test_other_types_default_behavior_unchanged(self):
        # A plan's legacy HHMM name still conforms by default (require_id6 not passed).
        plan_legacy = "20260701-1200-01-some-plan.ipd.md"
        self.assertTrue(self.npn.is_conformant(plan_legacy, "ipd"))
        # And the clustered plan name still conforms.
        plan_clustered = "20260701-setid-01-abc123-some-plan.ipd.md"
        self.assertTrue(self.npn.is_conformant(plan_clustered, "ipd"))


class _RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_specid6_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.tmp, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.tmp, check=True)
        self.specs = self.tmp / ".aw" / "records" / "specs"
        self.plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        self.specs.mkdir(parents=True, exist_ok=True)
        self.plans.mkdir(parents=True, exist_ok=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _commit(self):
        subprocess.run(["git", "add", "-A"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "fixture"], cwd=self.tmp, check=True
        )


class TestSpecProducer(_RepoTestCase):
    """E-01 / V-01: aw specs new."""

    def test_new_preview_then_apply_conformant(self):
        rc, out = self._run(["specs", "new", "--title", "My Spec", "--slug", "my-spec"])
        self.assertEqual(rc, 0, out)
        self.assertIn("would write", out)
        # nothing written on preview
        self.assertEqual(list(self.specs.glob("*.spec.md")), [])

        rc, out = self._run(
            ["specs", "new", "--title", "My Spec", "--slug", "my-spec", "--apply"]
        )
        self.assertEqual(rc, 0, out)
        files = list(self.specs.glob("*.spec.md"))
        self.assertEqual(len(files), 1, out)
        f = files[0]
        text = f.read_text(encoding="utf-8")
        # id6 present in the `- Id:` metadata
        import re

        m = re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", text)
        self.assertIsNotNone(m, text)
        id6 = m.group(1)
        # filename shape: YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md (setid == its own id6)
        self.assertRegex(f.name, rf"^\d{{8}}-{id6}-01-{id6}-my-spec\.spec\.md$")
        # name-check + content-check clean
        npn = _load_npn()
        self.assertTrue(npn.is_conformant(f.name, "spec", require_id6=True))
        rc, out = self._run(["specs", "check"])
        self.assertEqual(rc, 0, out)

    def test_new_requires_title(self):
        rc, out = self._run(["specs", "new", "--slug", "x"])
        self.assertEqual(rc, 2, out)


class TestCheckGrandfatherCutover(_RepoTestCase):
    """E-03 / V-03: aw check specs grandfathers pre-cutover, enforces post-cutover."""

    def _write_spec(self, name):
        (self.specs / name).write_text(
            "# Spec: X\n\n- Date: 2026-01-01\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-01-01 created (aw specs): x\n",
            encoding="utf-8",
        )

    def test_pre_cutover_legacy_grandfathered(self):
        # A spec dated the day BEFORE the cutover keeps its legacy name conformant.
        self._write_spec("20260827-1200-01-pre-cutover.spec.md")
        rc, out = self._run(["check", "specs", "names"])
        self.assertEqual(rc, 0, out)

    def test_cutover_boundary(self):
        # Exactly at the cutover date with a legacy name -> flagged; day before -> not flagged.
        before = "20260827-1200-01-day-before.spec.md"  # cutover is 20260828
        at = "20260828-1200-01-at-cutover.spec.md"
        self.assertFalse(ce._spec_requires_id6(before))
        self.assertTrue(ce._spec_requires_id6(at))

    def test_post_cutover_legacy_flagged_with_recovery(self):
        self._write_spec("20260828-1200-01-post-cutover.spec.md")
        rc, out = self._run(["check", "specs", "names"])
        self.assertEqual(rc, 1, out)
        # The engine-level drift carries the id6-minting recovery command (the human/agent
        # renderer canonicalizes the surface message, so assert on the engine detail directly).
        drift = ce.check_names(self.tmp, "specs")
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.name-nonconformant")
        self.assertIn("--to-id6", drift[0].detail)

    def test_post_cutover_clustered_ok(self):
        (self.specs / "20260828-abc123-01-abc123-post.spec.md").write_text(
            "# Spec: X\n\n- Date: 2026-08-28\n- Status: reviewed\n- Id: abc123\n\n"
            "## Workflow history\n\n- 2026-08-28 created (aw specs): x\n",
            encoding="utf-8",
        )
        rc, out = self._run(["check", "specs", "names"])
        self.assertEqual(rc, 0, out)


class TestToId6Rename(_RepoTestCase):
    """E-04/E-05 / V-04/V-05: --to-id6 minting rename + refs + idempotence + fail-loud."""

    def _write_legacy(self, name="20260701-1200-01-legacy.spec.md"):
        (self.specs / name).write_text(
            "# Spec: Legacy\n\n- Date: 2026-07-01\n- Status: reviewed\n- Author: a\n\n"
            "## Workflow history\n\n- 2026-07-01 created (aw specs): legacy\n",
            encoding="utf-8",
        )
        return self.specs / name

    def test_to_id6_preview_then_apply_injects_and_rewrites(self):
        src = self._write_legacy()
        citer = self.plans / "20260701-set-01-pl1234-cite.ipd.md"
        citer.write_text(
            "# IPD\n\nsee 20260701-1200-01-legacy.spec.md and "
            ".aw/records/specs/20260701-1200-01-legacy.spec.md\n",
            encoding="utf-8",
        )
        self._commit()

        rc, out = self._run(["rename", "specs", src.name, "--to-id6"])
        self.assertEqual(rc, 0, out)
        self.assertIn("would inject", out)
        self.assertIn("would rewrite", out)
        # still unrenamed on preview
        self.assertTrue(src.exists())

        rc, out = self._run(
            ["rename", "specs", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        self.assertFalse(src.exists())
        new_files = list(self.specs.glob("*.spec.md"))
        self.assertEqual(len(new_files), 1, out)
        new = new_files[0]
        import re

        m = re.search(
            r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", new.read_text(encoding="utf-8")
        )
        self.assertIsNotNone(m)
        id6 = m.group(1)
        self.assertRegex(new.name, rf"^20260701-{id6}-01-{id6}-legacy\.spec\.md$")
        # both the bare-filename citation and the full-path citation were rewritten
        cite_text = citer.read_text(encoding="utf-8")
        self.assertNotIn("20260701-1200-01-legacy.spec.md", cite_text)
        self.assertIn(new.name, cite_text)
        self.assertIn(f".aw/records/specs/{new.name}", cite_text)

    def test_to_id6_idempotent_on_clustered_spec(self):
        # A spec that already carries `- Id:` and a clustered name reuses its id6, no re-mint/rename.
        name = "20260701-o3bq8p-01-o3bq8p-legacy.spec.md"
        (self.specs / name).write_text(
            "# Spec: Legacy\n\n- Date: 2026-07-01\n- Status: reviewed\n- Id: o3bq8p\n\n"
            "## Workflow history\n\n- 2026-07-01 created (aw specs): legacy\n",
            encoding="utf-8",
        )
        self._commit()
        rc, out = self._run(["rename", "specs", "o3bq8p", "--to-id6"])
        self.assertEqual(rc, 0, out)
        self.assertIn("no re-mint", out)
        # name unchanged (already clustered with its own id6 as setid)
        self.assertTrue((self.specs / name).exists())

    def test_to_id6_fail_loud_on_unrewritable_path_citation(self):
        src = self._write_legacy()
        # a scanned file (a plan) cites the spec by a DIFFERENT directory path.
        bad = self.plans / "20260701-set-01-pl1234-bad.ipd.md"
        bad.write_text(
            "# IPD\n\nwrong dir: some/other/dir/20260701-1200-01-legacy.spec.md\n",
            encoding="utf-8",
        )
        self._commit()
        # preview warns
        rc, out = self._run(["rename", "specs", src.name, "--to-id6"])
        self.assertEqual(rc, 0, out)
        self.assertIn("WARNING", out)
        self.assertIn("some/other/dir", out)
        # apply fails loud, does not rename
        rc, out = self._run(
            ["rename", "specs", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("cannot auto-rewrite", out)
        self.assertTrue(src.exists())


if __name__ == "__main__":
    unittest.main()
