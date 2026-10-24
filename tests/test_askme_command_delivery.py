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


if __name__ == "__main__":
    unittest.main()
