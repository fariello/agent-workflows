"""Tests for prompt id6 filenames (IPD ubac5n, the prompts twin of ha55fi).

Covers the two deliverables that are NOT the minting verb itself (that is
``tests/test_prompts_new.py``):

  E-03 - the `aw check prompts` grandfather cutover: a pre-cutover legacy name conforms, a
         post-cutover legacy name is REFUSED with the prompts recovery command, and the boundary is
         resolved config-FIRST with a non-``None`` module fallback;
  E-04 - the `aw rename prompts <legacy> --to-id6` REPAIR: the minted id6 goes into the single
         ``<!-- aw-prompt: ... -->`` comment and NEVER into a ``- Id:`` bullet, which for a prompt
         would be visible text above the body (approved spec `20260808-1958-01-prompt-purity-lint`
         R1/P4). Includes the regression this repair exists for, and the guard that specs' behavior
         is unchanged.

WHY E-04 IS A REPAIR AND NOT A NEW FEATURE, since a reader will otherwise wonder why the test asserts
an absence: ``--to-id6`` is a GENERIC flag on the shared rename verb, so `aw rename prompts <legacy>
--to-id6` already ran before this plan and already planned `would inject '- Id: <id6>'`. A prompt
carries neither a ``- Status:`` nor a ``- Date:`` bullet, so the injector's third anchor fired and the
bullet landed directly under the H1. Nothing caught it, because `aw prompts check` (the purity lint the
approved spec specifies) is NOT implemented. ``test_the_purity_regression_is_closed`` is the test that
would have caught it.
"""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine as ce
from agent_workflows import cli
from agent_workflows import config as cfg
from agent_workflows import prompts as prompts_mod

_ID_BULLET_RE = re.compile(r"(?m)^- Id:")


def _load_npn():
    return ce._load_normalizer()


class TestIsConformantForPrompts(unittest.TestCase):
    """The shared predicate's require_id6 matrix, applied to the `prompt` facet."""

    def setUp(self):
        self.npn = _load_npn()
        self.assertIsNotNone(self.npn, "normalizer must be locatable")

    def test_legacy_prompt_conforms_by_default_and_fails_under_require_id6(self):
        legacy = "20260701-1200-01-old-topic.prompt.md"
        self.assertTrue(self.npn.is_conformant(legacy, "prompt"))
        self.assertFalse(self.npn.is_conformant(legacy, "prompt", require_id6=True))

    def test_clustered_prompt_conforms_in_both_modes(self):
        clustered = "20260921-plainlang-01-ng0ga4-some-topic.prompt.md"
        self.assertTrue(self.npn.is_conformant(clustered, "prompt"))
        self.assertTrue(self.npn.is_conformant(clustered, "prompt", require_id6=True))

    def test_a_prompt_facet_on_a_non_prompt_expectation_is_nonconformant(self):
        """The facet must MATCH the type, so a prompt name is not accepted as a plan."""

        self.assertFalse(
            self.npn.is_conformant(
                "20260921-plainlang-01-ng0ga4-some-topic.prompt.md", "ipd"
            )
        )


class _PromptRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_promptid6_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        subprocess.run(["git", "init", "-q"], cwd=self.tmp, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.tmp, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.tmp, check=True)
        self.prompts = self.tmp / ".aw" / "records" / "prompts"
        self.pending = self.prompts / "pending"
        self.executed = self.prompts / "executed"
        self.plans = self.tmp / ".aw" / "records" / "plans" / "pending"
        self.config_dir = self.tmp / ".aw" / "config"
        for d in (self.pending, self.executed, self.plans, self.config_dir):
            d.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"prompt_id6": "2026-09-21"}}', encoding="utf-8"
        )

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

    def _write_prompt(
        self, name, *, bucket=None, comment=True, body="# Ask\n\nBody.\n"
    ):
        target = (bucket or self.pending) / name
        text = ""
        if comment:
            text += (
                "<!-- aw-prompt: Kind: research | Status: pending | Created: 2026-07-01 "
                ". This HTML comment is pipeline metadata only; it is invisible when pasted "
                "into a chat and is not part of the prompt. -->\n"
            )
        text += body
        target.write_text(text, encoding="utf-8")
        return target


class TestCheckGrandfatherCutover(_PromptRepoTestCase):
    """E-03 / V-03."""

    def test_pre_cutover_legacy_is_grandfathered(self):
        self._write_prompt("20260920-1200-01-pre-cutover.prompt.md")
        self.assertEqual(ce.check_names(self.tmp, "prompts"), [])
        rc, out = self._run(["check", "prompts", "names"])
        self.assertEqual(rc, 0, out)

    def test_post_cutover_legacy_is_refused_with_the_prompts_recovery_command(self):
        self._write_prompt("20260921-1200-01-post-cutover.prompt.md")
        drift = ce.check_names(self.tmp, "prompts")
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.name-nonconformant")
        # The recovery command must name the PROMPTS converter, not the spec one.
        self.assertIn("aw rename prompts", drift[0].detail)
        self.assertNotIn("aw rename specs", drift[0].detail)
        self.assertIn("prompt dated at/after the id6 cutover", drift[0].detail)
        rc, out = self._run(["check", "prompts", "names"])
        self.assertEqual(rc, 1, out)

    def test_the_boundary_is_exact(self):
        self.assertFalse(
            ce._prompt_requires_id6("20260920-1200-01-day-before.prompt.md", self.tmp)
        )
        self.assertTrue(
            ce._prompt_requires_id6("20260921-1200-01-at-cutover.prompt.md", self.tmp)
        )

    def test_post_cutover_clustered_conforms(self):
        self._write_prompt("20260921-someset-01-abc123-post.prompt.md")
        self.assertEqual(ce.check_names(self.tmp, "prompts"), [])

    def test_a_configured_date_beats_the_module_constant(self):
        """Config-FIRST: a repository moves its own boundary without editing Python."""

        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"prompt_id6": "2026-10-15"}}', encoding="utf-8"
        )
        self._write_prompt("20260921-1200-01-now-grandfathered.prompt.md")
        self.assertEqual(ce.check_names(self.tmp, "prompts"), [])
        self._write_prompt("20261015-1200-01-at-new-cutover.prompt.md")
        self.assertEqual(len(ce.check_names(self.tmp, "prompts")), 1)

    def test_an_unconfigured_repo_falls_back_to_the_constant_not_to_None(self):
        """The fallback is what keeps the error tier REACHABLE.

        A `None` here would grandfather every prompt forever and make the rule decoration, which is the
        failure mode `CARRIER_CUTOVER_DATE`'s comment records. So an unconfigured repository must still
        refuse a post-cutover legacy name.
        """

        (self.config_dir / "project.json").unlink()
        self.assertIsNone(cfg.resolve_cutover_date(self.tmp, "prompt_id6"))
        self.assertIsNotNone(ce.PROMPT_ID6_CUTOVER_DATE)
        self._write_prompt("20260920-1200-01-pre.prompt.md")
        self.assertEqual(ce.check_names(self.tmp, "prompts"), [])
        self._write_prompt("20260921-1200-01-at.prompt.md")
        self.assertEqual(len(ce.check_names(self.tmp, "prompts")), 1)

    def test_an_unparseable_leading_date_is_treated_as_pre_cutover(self):
        """Mirrors `_spec_requires_id6`: a missing date is another rule's defect, not this one's."""

        self.assertFalse(ce._prompt_requires_id6("no-date-here.prompt.md", self.tmp))

    def test_the_feature_is_registered_so_an_install_stamps_a_boundary(self):
        self.assertIn("prompt_id6", cfg.KNOWN_FEATURE_CUTOVERS)
        stamped = cfg.sync_cutovers_on_install(self.tmp, install_timestamp="2026-10-01")
        # An EXISTING value is preserved; a re-install never moves an established boundary.
        self.assertEqual(stamped["prompt_id6"], "2026-09-21")

    def test_specs_are_unaffected_by_the_prompt_cutover(self):
        """The two cutovers are independent; a prompt boundary must not judge a spec."""

        specs = self.tmp / ".aw" / "records" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        (specs / "20260827-1200-01-pre-spec-cutover.spec.md").write_text(
            "# Spec: X\n\n- Date: 2026-01-01\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-01-01 created (aw specs): x\n",
            encoding="utf-8",
        )
        self.assertEqual(ce.check_names(self.tmp, "specs"), [])


class TestToId6RepairsPromptPurity(_PromptRepoTestCase):
    """E-04 / V-04: the conversion writes the id6 into the COMMENT, never as a bullet."""

    def test_preview_then_apply_writes_the_id6_into_the_metadata_comment(self):
        src = self._write_prompt(
            "20260701-1200-01-legacy-topic.prompt.md", bucket=self.executed
        )
        self._commit()

        rc, out = self._run(["rename", "prompts", src.name, "--to-id6"])
        self.assertEqual(rc, 0, out)
        self.assertIn("aw-prompt metadata comment", out)
        # The preview must NOT promise a bullet injection (that is the defect being repaired).
        self.assertNotIn("would inject '- Id:", out)
        self.assertTrue(src.exists(), "preview must not move the file")

        rc, out = self._run(
            ["rename", "prompts", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        self.assertFalse(src.exists())
        files = list(self.executed.glob("*.prompt.md"))
        self.assertEqual(len(files), 1, out)
        new = files[0]
        text = new.read_text(encoding="utf-8")
        id6 = prompts_mod.read_metadata_id6(text)
        self.assertIsNotNone(id6, text)
        assert id6 is not None
        self.assertRegex(
            new.name, rf"\A20260701-{id6}-01-{id6}-legacy-topic\.prompt\.md\Z"
        )

    def test_the_purity_regression_is_closed(self):
        """THE test this repair exists for: no `- Id:` bullet, and line 2 is still the body.

        Measured before the repair, on the real tree: the injector anchored after the first `# `
        heading (a prompt has no `- Status:`/`- Date:` bullet), so `- Id: <id6>` became line 3,
        directly under the H1, i.e. visible text inside a pasteable prompt.
        """

        src = self._write_prompt(
            "20260701-1200-01-purity.prompt.md",
            bucket=self.executed,
            body="# Research request\n\nThe prompt body.\n",
        )
        self._commit()
        rc, out = self._run(
            ["rename", "prompts", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        new = list(self.executed.glob("*.prompt.md"))[0]
        text = new.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertIsNone(
            _ID_BULLET_RE.search(text),
            "a `- Id:` bullet in a prompt is visible text above the body "
            "(prompt-purity-lint R1/P4)",
        )
        self.assertTrue(lines[0].startswith("<!-- aw-prompt: "), lines[0])
        self.assertEqual(text.count("<!-- aw-prompt:"), 1, text)
        # Exactly the original body follows the one comment line: nothing was inserted.
        self.assertEqual(lines[1:], ["# Research request", "", "The prompt body."])

    def test_the_conversion_is_idempotent_and_never_re_mints(self):
        name = "20260701-o3bq8p-01-o3bq8p-already.prompt.md"
        (self.executed / name).write_text(
            "<!-- aw-prompt: Kind: research | Id: o3bq8p | Status: executed "
            "| Created: 2026-07-01 -->\n# Ask\n",
            encoding="utf-8",
        )
        self._commit()
        rc, out = self._run(["rename", "prompts", "o3bq8p", "--to-id6"])
        self.assertEqual(rc, 0, out)
        self.assertIn("no re-mint", out)
        # And the message says where that id6 actually lives, not `- Id:`.
        self.assertIn("aw-prompt metadata comment", out)
        self.assertTrue((self.executed / name).exists())

    def test_a_prompt_with_no_metadata_comment_gets_no_new_line_above_its_body(self):
        """6 of the 17 measured prompts have no comment. Minting one would ADD a pre-body line.

        So the id6 lands in the FILENAME only, and the verb SAYS so rather than claiming a write.
        """

        src = self._write_prompt(
            "20260701-1200-01-bare.prompt.md",
            bucket=self.executed,
            comment=False,
            body="You are a research assistant.\n\nDo the thing.\n",
        )
        original = src.read_text(encoding="utf-8")
        self._commit()
        rc, out = self._run(
            ["rename", "prompts", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        self.assertIn("FILENAME ONLY", out)
        new = list(self.executed.glob("*.prompt.md"))[0]
        self.assertEqual(new.read_text(encoding="utf-8"), original)
        self.assertIsNone(_ID_BULLET_RE.search(new.read_text(encoding="utf-8")))

    def test_inbound_citations_are_rewritten(self):
        src = self._write_prompt(
            "20260701-1200-01-cited.prompt.md", bucket=self.executed
        )
        citer = self.plans / "20260701-set-01-pl1234-cite.ipd.md"
        citer.write_text(
            "# IPD\n\nsee 20260701-1200-01-cited.prompt.md\n", encoding="utf-8"
        )
        self._commit()
        rc, out = self._run(
            ["rename", "prompts", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        new = list(self.executed.glob("*.prompt.md"))[0]
        cite_text = citer.read_text(encoding="utf-8")
        self.assertNotIn("20260701-1200-01-cited.prompt.md", cite_text)
        self.assertIn(new.name, cite_text)

    def test_a_converted_prompt_then_conforms_post_cutover(self):
        """The whole point of the converter: the output passes the rule that refused the input."""

        src = self._write_prompt("20260921-1200-01-must-convert.prompt.md")
        self.assertEqual(len(ce.check_names(self.tmp, "prompts")), 1)
        self._commit()
        rc, out = self._run(
            ["rename", "prompts", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        self.assertEqual(ce.check_names(self.tmp, "prompts"), [])


class TestSpecsBehaviorIsUnchanged(_PromptRepoTestCase):
    """E-04's fence: the shared metadata writer must still inject a BULLET for a spec."""

    def test_a_spec_conversion_still_injects_the_id_bullet(self):
        (self.config_dir / "project.json").write_text(
            '{"cutovers": {"spec_id6": "2026-08-28", "prompt_id6": "2026-09-21"}}',
            encoding="utf-8",
        )
        specs = self.tmp / ".aw" / "records" / "specs"
        specs.mkdir(parents=True, exist_ok=True)
        src = specs / "20260701-1200-01-legacy.spec.md"
        src.write_text(
            "# Spec: Legacy\n\n- Date: 2026-07-01\n- Status: reviewed\n\n"
            "## Workflow history\n\n- 2026-07-01 created (aw specs): legacy\n",
            encoding="utf-8",
        )
        self._commit()
        rc, out = self._run(["rename", "specs", src.name, "--to-id6"])
        self.assertEqual(rc, 0, out)
        # The pre-existing literal wording is preserved for specs (its own tests assert it).
        self.assertIn("would inject '- Id:", out)
        rc, out = self._run(
            ["rename", "specs", src.name, "--to-id6", "--apply", "--no-commit"]
        )
        self.assertEqual(rc, 0, out)
        new = list(specs.glob("*.spec.md"))[0]
        text = new.read_text(encoding="utf-8")
        self.assertIsNotNone(
            _ID_BULLET_RE.search(text),
            "a spec DOES carry a `- Id:` bullet; the prompts repair must not remove it",
        )


if __name__ == "__main__":
    unittest.main()
