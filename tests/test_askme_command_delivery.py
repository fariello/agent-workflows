"""Tests for askme command delivery, shims, pointer prose, and installer integration.

Requirements from IPD er11a0 (E-07):
(a) render both hosts' askme shims from real manifest for both layouts and assert they
    reference the same workflow body, carry the manifest's arg-hint, carry no deprecation
    notice, while another command's shim still does;
(b) assert agents_pointer_prose for both layouts names the layout's askme/askme.md;
(c) run the installer into a temporary repo and assert both askme.md shims are installed
    and that AGENTS.md contains contract_text() verbatim and the askme path;
(d) re-run the installer and assert the askme shims are unchanged and not reported as
    customized (no [preserved] tag and no 'has manual modifications' warning for them).
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import engine, reporting_contract
from tests.support import SOURCE_WORKFLOWS, init_repo


class AskmeCommandDeliveryTests(unittest.TestCase):
    """Test suite for askme command delivery, shims, pointer prose, and installer."""

    def test_askme_shims_rendered_from_manifest(self):
        """(a) Render both hosts' askme shims from real manifest for both layouts."""
        manifest = engine.parse_manifest(SOURCE_WORKFLOWS)
        wfs = {w.command: w for w in manifest}
        self.assertIn("askme", wfs)
        self.assertIn("handoff", wfs)
        askme_wf = wfs["askme"]
        handoff_wf = wfs["handoff"]

        for layout in ("aw", "legacy"):
            with self.subTest(layout=layout):
                opencode_shim = engine.shim_body(
                    "askme", askme_wf, "opencode", target_layout=layout
                )
                claude_shim = engine.shim_body(
                    "askme", askme_wf, "claude", target_layout=layout
                )

                # Reference same workflow body
                self.assertIn(f"@{askme_wf.body}", opencode_shim)
                self.assertIn(f"@{askme_wf.body}", claude_shim)

                # Carry manifest's arg-hint
                self.assertIn(askme_wf.arg_hint, opencode_shim)
                self.assertIn(askme_wf.arg_hint, claude_shim)

                # Carry no deprecation notice, but carry supported alias notice
                self.assertNotIn("Deprecation notice", opencode_shim)
                self.assertNotIn("Deprecation notice", claude_shim)
                self.assertIn("Supported alias", opencode_shim)
                self.assertIn("Supported alias", claude_shim)

                # Another command's shim still carries deprecation notice
                handoff_opencode = engine.shim_body(
                    "handoff", handoff_wf, "opencode", target_layout=layout
                )
                handoff_claude = engine.shim_body(
                    "handoff", handoff_wf, "claude", target_layout=layout
                )
                self.assertIn("Deprecation notice", handoff_opencode)
                self.assertIn("Deprecation notice", handoff_claude)

                # Neither askme shim is reported as customized
                self.assertFalse(engine.is_stale_shim_customized(opencode_shim))
                self.assertFalse(engine.is_stale_shim_customized(claude_shim))

    def test_agents_pointer_prose_names_askme(self):
        """(b) Assert agents_pointer_prose for both layouts names the layout's askme/askme.md."""
        aw_prose = engine.agents_pointer_prose("aw")
        legacy_prose = engine.agents_pointer_prose("legacy")

        self.assertIn(".aw/system/workflows/askme/askme.md", aw_prose)
        self.assertIn(".agents/workflows/askme/askme.md", legacy_prose)

        self.assertNotIn("keep it screen-sized", aw_prose)
        self.assertNotIn("keep it screen-sized", legacy_prose)

        for prose in (aw_prose, legacy_prose):
            self.assertIn("commands, never answers", prose)
            self.assertIn("even if you already applied it", prose)

    @pytest.mark.slow
    def test_installer_delivers_and_preserves_askme_shims(self):
        """(c) Run installer and assert askme shims and reporting contract in AGENTS.md;
        (d) re-run installer and assert askme shims unchanged and not customized.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            # First install
            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            # (c) Assert both askme.md shims are installed
            opencode_shim = repo / ".opencode" / "commands" / "askme.md"
            claude_shim = repo / ".claude" / "commands" / "askme.md"
            self.assertTrue(opencode_shim.is_file(), "OpenCode askme shim must exist")
            self.assertTrue(claude_shim.is_file(), "Claude askme shim must exist")

            opencode_text1 = opencode_shim.read_text(encoding="utf-8")
            claude_text1 = claude_shim.read_text(encoding="utf-8")
            self.assertIn("Supported alias", opencode_text1)
            self.assertIn("Supported alias", claude_text1)
            self.assertNotIn("Deprecation notice", opencode_text1)
            self.assertNotIn("Deprecation notice", claude_text1)

            # Assert AGENTS.md contains contract_text() verbatim and the askme path
            agents_md = repo / "AGENTS.md"
            self.assertTrue(agents_md.is_file(), "AGENTS.md must exist")
            agents_text = agents_md.read_text(encoding="utf-8")
            self.assertIn(
                reporting_contract.contract_text(),
                agents_text,
                "AGENTS.md must contain contract_text() verbatim",
            )
            self.assertIn(
                ".aw/system/workflows/askme/askme.md",
                agents_text,
                "AGENTS.md must contain the modern askme workflow path",
            )

            # Assert installed workflow body contains the "commands, never answers" rule
            installed_askme_body = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme_body.is_file(),
                "Installed askme workflow body must exist",
            )
            self.assertIn(
                "commands, never answers",
                installed_askme_body.read_text(encoding="utf-8"),
                "Installed askme workflow body must contain commands, never answers rule",
            )

            # (d) Re-run the installer
            buf2 = io.StringIO()
            with redirect_stdout(buf2):
                res2 = engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )
            out2 = buf2.getvalue()

            # Assert askme shims are unchanged
            self.assertEqual(
                opencode_shim.read_text(encoding="utf-8"),
                opencode_text1,
                "OpenCode askme shim should be unchanged on re-install",
            )
            self.assertEqual(
                claude_shim.read_text(encoding="utf-8"),
                claude_text1,
                "Claude askme shim should be unchanged on re-install",
            )

            # Assert not reported as customized (no [preserved] tag and no manual modifications warning)
            skipped = res2.get("skipped", [])
            for item in skipped:
                if "askme.md" in item:
                    self.assertNotIn(
                        "[preserved]",
                        item,
                        f"askme.md should not be skipped as [preserved]: {item}",
                    )

            self.assertNotIn(
                "Warning: .opencode/commands/askme.md has manual modifications", out2
            )
            self.assertNotIn(
                "Warning: .claude/commands/askme.md has manual modifications", out2
            )

    @pytest.mark.slow
    def test_installer_delivers_askme_no_scan_rule(self):
        """Assert installer delivers askme.md with no-scan rule and without replaced authorship sentence."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed_askme = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme.is_file(),
                "Installed askme workflow body must exist",
            )
            installed_text = installed_askme.read_text(encoding="utf-8")
            installed_words = " ".join(installed_text.split())

            # Conversation-only source of (a)
            self.assertIn(
                "whose edits appear in this conversation's own tool calls",
                installed_words,
            )
            self.assertIn(
                "establish them from the conversation, not by searching",
                installed_words,
            )

            # Prohibition on aw attention and recursive search of (b)
            self.assertIn("aw attention", installed_words)
            self.assertIn("aw find", installed_words)
            self.assertIn("grep -r", installed_words)

            # Empty-scope stop of (c)
            self.assertIn(
                "stop without asking a question",
                installed_words,
            )
            self.assertIn(
                "list the three ways to point `/askme` at a subject",
                installed_words,
            )

            # Replaced git log authorship sentence of (e) is absent
            self.assertNotIn(
                "In a shared checkout, confirm authorship before treating a record or question as yours",
                installed_words,
            )

            # Item 4 specifically does not contain the replaced authorship sentence
            self.assertIn("4. **Use the current conversation.**", installed_text)
            item_4_text = installed_text.split("4. **Use the current conversation.**")[
                1
            ].split("\n\n")[0]
            self.assertNotIn(
                "`git log` and the record's `- Author:` line settle it",
                item_4_text,
            )

    @pytest.mark.slow
    def test_installer_delivers_askme_recorded_answers_and_premise_rules(self):
        """Assert installer delivers askme.md with answer recording rules and premise check."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed_askme = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme.is_file(),
                "Installed askme workflow body must exist",
            )
            installed_text = installed_askme.read_text(encoding="utf-8")
            installed_words = " ".join(installed_text.split())

            # E-01: No reason was given phrase
            self.assertIn("No reason was given.", installed_text)
            self.assertIn(
                "Choosing an option is not giving a reason",
                installed_words,
            )

            # E-02: Append shape including via /askme
            self.assertIn("via /askme", installed_text)
            self.assertIn(
                '<existing text> RESOLVED <YYYY-MM-DD> by <the user | evidence> via /askme: <decision>. <reason as given, or "No reason was given.">',
                installed_text,
            )
            self.assertIn(
                "When the field is empty, write the `RESOLVED ...` text alone.",
                installed_words,
            )

            # E-03: Premise-check rule
            self.assertIn(
                "never repeat an unchecked premise",
                installed_words,
            )
            self.assertIn(
                "check it against the repository",
                installed_words,
            )

    @pytest.mark.slow
    def test_installer_delivers_askme_write_before_ask_rule(self):
        """Assert installer delivers askme.md with write-each-answer-before-next-question rule in ## Ask and wait."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed_askme = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme.is_file(),
                "Installed askme workflow body must exist",
            )
            installed_text = installed_askme.read_text(encoding="utf-8")
            start_idx = installed_text.find("## Ask and wait")
            self.assertNotEqual(start_idx, -1, "## Ask and wait heading must exist")
            end_idx = installed_text.find("\n## ", start_idx + len("## Ask and wait"))
            section = (
                installed_text[start_idx:end_idx]
                if end_idx != -1
                else installed_text[start_idx:]
            )
            self.assertIn(
                "Write each definite answer to its record before you compose or ask the next question.",
                section,
            )

    @pytest.mark.slow
    def test_installer_delivers_askme_refuses_code_comments_as_decision_rules(self):
        """Assert installer delivers askme.md with approved decision rule definition and comment refusal."""
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")

            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed_askme = (
                repo / ".aw" / "system" / "workflows" / "askme" / "askme.md"
            )
            self.assertTrue(
                installed_askme.is_file(),
                "Installed askme workflow body must exist",
            )
            installed_text = installed_askme.read_text(encoding="utf-8")
            installed_words = " ".join(installed_text.split())

            # Four sources of an approved decision rule
            self.assertIn("DECISIONS.md", installed_words)
            self.assertIn("has not been superseded", installed_words)
            self.assertIn("approved or implemented spec", installed_words)
            self.assertIn(
                "earlier open question that a human resolved", installed_words
            )
            self.assertIn(
                'one an agent resolved "by evidence" is not a rule',
                installed_words,
            )
            self.assertIn("decision the user gave in this session", installed_words)

            # Statement that code comment or default is not a rule
            self.assertIn(
                "A code comment or docstring, a function's default argument, the way the code currently behaves, and consistency with another command are evidence",
                installed_words,
            )
            self.assertIn(
                "they never answer a `Blocking: yes` question on their own",
                installed_words,
            )

            # Reconciled explicit-request paragraph
            self.assertIn(
                "Do not use this classification to ignore an explicit request to ask or rewrite a question.",
                installed_words,
            )
            self.assertIn(
                "If the user asked you to ask or rewrite a specific question, do so.",
                installed_words,
            )
            self.assertIn(
                "If an approved decision rule (as defined above) already settles it, say which rule and what it decides, and ask whether the user wants to reopen it.",
                installed_words,
            )
            self.assertIn(
                "If only evidence that is not a rule bears on it, ask the question and give that evidence in it.",
                installed_words,
            )

            # Noninteractive sentence
            self.assertIn(
                '"Evidence" here means an approved decision rule as defined above; a code comment or default is not one, so a `Blocking: yes` question it would answer stays open.',
                installed_words,
            )

            # Old contradictory sentence is removed
            self.assertNotIn(
                "explain the answer and its basis instead of asking the user to decide it again",
                installed_text,
            )


if __name__ == "__main__":
    unittest.main()
