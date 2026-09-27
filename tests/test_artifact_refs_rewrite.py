"""Outcome tests for artifact reference rewriting (IPD 5xzld0).

Pins the four defects and one permalink guard when renaming a legacy artifact:
(a) Citation in .aw/records/reviews/ is rewritten;
(b) Citation in tests/ is rewritten (non-interactive mode);
(c) Short handle (bare date-time-nn) maps to new short handle (not full stem);
(d) Fenced transcript is preserved byte-identical while out-of-fence citation is rewritten;
(e) Shared legacy prefix across multiple records is skipped and warned;
(f) Pinned commit permalink is preserved byte-identical.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


class _RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_refs_rewrite_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.tmp, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.tmp, check=True)
        self.specs = self.tmp / ".aw" / "records" / "specs"
        self.plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        self.reviews = self.tmp / ".aw" / "records" / "reviews"
        self.prompts = self.tmp / ".aw" / "records" / "prompts" / "executed"
        self.tests_dir = self.tmp / "tests"
        self.config_dir = self.tmp / ".aw" / "config"

        self.specs.mkdir(parents=True, exist_ok=True)
        self.plans.mkdir(parents=True, exist_ok=True)
        self.reviews.mkdir(parents=True, exist_ok=True)
        self.prompts.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"spec_id6": "2026-08-28"}}',
            encoding="utf-8",
        )
        self.spec_name = "20260701-1200-01-legacy.spec.md"
        self.spec_file = self.specs / self.spec_name
        self.spec_file.write_text(
            "# Spec: Legacy\n\n- Date: 2026-07-01\n- Status: draft\n",
            encoding="utf-8",
        )

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def _new_spec_name(self) -> str:
        specs = [
            p.name for p in self.specs.glob("*.spec.md") if p.name != self.spec_name
        ]
        self.assertEqual(
            len(specs), 1, f"expected exactly 1 renamed spec, found {specs}"
        )
        return specs[0]


class TestArtifactRefsRewrite(_RepoTestCase):
    def test_a_reviews_citation_rewritten(self):
        review_file = self.reviews / "20260702-01-legacy.review.md"
        review_file.write_text(
            f"Review citing .aw/records/specs/{self.spec_name} in full.\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, f"rename failed with rc={rc}:\n{out}")
        new_name = self._new_spec_name()
        content = review_file.read_text(encoding="utf-8")
        self.assertNotIn(self.spec_name, content)
        self.assertIn(new_name, content)

    def test_b_tests_citation_rewritten_noninteractive(self):
        test_file = self.tests_dir / "test_something.py"
        test_file.write_text(
            f"# Citation of .aw/records/specs/{self.spec_name}\nSPEC = '{self.spec_name}'\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, f"rename failed with rc={rc}:\n{out}")
        new_name = self._new_spec_name()
        content = test_file.read_text(encoding="utf-8")
        self.assertNotIn(self.spec_name, content)
        self.assertIn(new_name, content)

    def test_c_short_handle_maps_to_short_handle(self):
        plan_file = self.plans / "20260701-testset-01-abcdef-my-plan.ipd.md"
        plan_file.write_text(
            "- References: `20260701-1200-01` short handle citation\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, f"rename failed with rc={rc}:\n{out}")
        new_name = self._new_spec_name()
        # new_name is YYYYMMDD-<id6>-01-<id6>-legacy.spec.md
        parts = new_name.split("-")
        date_str, id6 = parts[0], parts[1]
        expected_short = f"{date_str}-{id6}-01"
        full_stem = new_name[:-3]  # without .md

        content = plan_file.read_text(encoding="utf-8")
        self.assertIn(f"`{expected_short}`", content)
        self.assertNotIn(full_stem, content)

    def test_d_fenced_transcript_preserved_and_outside_rewritten(self):
        plan_file = self.plans / "20260701-testset-01-abcdef-my-plan.ipd.md"
        fence_block = (
            "```sh\n"
            f"--- would rename .aw/records/specs/{self.spec_name} -> somewhere ---\n"
            "```"
        )
        plan_file.write_text(
            f"# Plan\n\nOutside citation: .aw/records/specs/{self.spec_name}\n\n{fence_block}\n",
            encoding="utf-8",
        )
        rc, out = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, f"rename failed with rc={rc}:\n{out}")
        new_name = self._new_spec_name()
        content = plan_file.read_text(encoding="utf-8")
        self.assertIn(f"Outside citation: .aw/records/specs/{new_name}", content)
        self.assertIn(fence_block, content)

    def test_e_shared_legacy_prefix_skipped_and_warned(self):
        other_prompt = self.prompts / "20260701-1200-01-other.prompt.md"
        other_prompt.write_text(
            "<!-- aw-prompt: kind=task -->\nPrompt text\n",
            encoding="utf-8",
        )
        plan_file = self.plans / "20260701-testset-01-abcdef-my-plan.ipd.md"
        initial_plan_text = (
            "# Plan\n\n- Cites: 20260701-1200-01-other and `20260701-1200-01`\n"
        )
        plan_file.write_text(initial_plan_text, encoding="utf-8")

        # Preview path
        rc_prev, out_prev = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--no-commit"]
        )
        self.assertEqual(rc_prev, 0, f"preview failed with rc={rc_prev}:\n{out_prev}")
        self.assertIn(
            "--- WARNING: legacy prefix '20260701-1200-01' is shared by 2 artifacts; "
            "short-handle citations of it were NOT rewritten ---",
            out_prev,
        )

        # Apply path
        rc_app, out_app = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc_app, 0, f"apply failed with rc={rc_app}:\n{out_app}")
        content = plan_file.read_text(encoding="utf-8")
        self.assertEqual(content, initial_plan_text)
        self.assertIn(
            "--- WARNING: legacy prefix '20260701-1200-01' is shared by 2 artifacts; "
            "short-handle citations of it were NOT rewritten ---",
            out_app,
        )

    def test_f_pinned_permalink_preserved(self):
        plan_file = self.plans / "20260701-testset-01-abcdef-my-plan.ipd.md"
        initial_plan_text = (
            "# Plan\n\n"
            f"[Perm](https://example.invalid/o/r/blob/0123456789abcdef/.aw/records/specs/{self.spec_name})\n"
        )
        plan_file.write_text(initial_plan_text, encoding="utf-8")

        rc, out = self._run(
            ["rename", "specs", self.spec_name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, f"rename failed with rc={rc}:\n{out}")
        content = plan_file.read_text(encoding="utf-8")
        self.assertEqual(content, initial_plan_text)

    def test_call_site_group_generic_rewrites_tests_and_reviews(self):
        spec2 = self.specs / "20260701-grp-01-s11111-my-spec.spec.md"
        spec2.write_text(
            "# Spec\n\n- Date: 2026-07-01\n- Id: s11111\n- Status: draft\n",
            encoding="utf-8",
        )
        rev = self.reviews / "20260701-rev-01-r11111-rev.review.md"
        rev.write_text(f"Cites {spec2.name}\n", encoding="utf-8")
        tst = self.tests_dir / "test_group.py"
        tst.write_text(f"Cites {spec2.name}\n", encoding="utf-8")

        rc, out = self._run(
            [
                "group",
                "specs",
                "s11111",
                "--set",
                "newgrp",
                "--rename",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, f"group failed with rc={rc}:\n{out}")
        new_name = "20260701-newgrp-01-s11111-my-spec.spec.md"
        self.assertIn(new_name, rev.read_text(encoding="utf-8"))
        self.assertIn(new_name, tst.read_text(encoding="utf-8"))

    def test_call_site_plans_refs_shared_prefix_warning_and_reviews_rewrite(self):
        # Shared prefix with self.spec_name (20260701-1200-01)
        plan = self.plans / "20260701-1200-01-legacy.ipd.md"
        plan.write_text(
            "# Plan\n\n- Date: 2026-07-01\n- Id: p11111\n- Status: draft\n",
            encoding="utf-8",
        )
        rev = self.reviews / "20260701-rev-02-r22222-rev.review.md"
        rev.write_text(f"Cites {plan.name}\n", encoding="utf-8")

        rc, out = self._run(
            [
                "rename",
                "plans",
                "p11111",
                "--slug",
                "new-slug",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, f"plans rename failed with rc={rc}:\n{out}")
        self.assertIn(
            "--- WARNING: legacy prefix '20260701-1200-01' is shared by 2 artifacts; "
            "short-handle citations of it were NOT rewritten ---",
            out,
        )
        self.assertIn(
            "20260701-p11111-00-p11111-new-slug.ipd.md",
            rev.read_text(encoding="utf-8"),
        )

    def test_call_site_research_refs_reviews_and_tests_rewrite(self):
        research_dir = self.tmp / ".aw" / "records" / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        rsch = research_dir / "20260701-seta-01-r33333-rsch.reference-research.md"
        rsch.write_text("# Research\n", encoding="utf-8")
        rev = self.reviews / "20260701-rev-03-r33333-rev.review.md"
        rev.write_text(f"Cites {rsch.name}\n", encoding="utf-8")
        tst = self.tests_dir / "test_rsch.py"
        tst.write_text(f"Cites {rsch.name}\n", encoding="utf-8")

        rc, out = self._run(
            [
                "rename",
                "research",
                "r33333",
                "--slug",
                "new-rsch",
                "--apply",
                "--no-commit",
            ]
        )
        self.assertEqual(rc, 0, f"research rename failed with rc={rc}:\n{out}")
        new_name = "20260701-seta-01-r33333-new-rsch.reference-research.md"
        self.assertIn(new_name, rev.read_text(encoding="utf-8"))
        self.assertIn(new_name, tst.read_text(encoding="utf-8"))
