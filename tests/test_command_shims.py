"""Unit tests for slash-command shims and the /aw dispatcher.

Covers:
- /aw dispatcher shim generation for OpenCode and Claude hosts
- generate_shim_members emitting the /aw dispatcher alongside back-compat aliases
- per-host grammar validation (validate_shim_grammar) positive and negative cases
"""

from __future__ import annotations

import unittest

from agent_workflows import engine as INS
from tests.support import SOURCE_WORKFLOWS


class CommandShimsTests(unittest.TestCase):
    """Tests for slash-command shims and /aw dispatcher generation."""

    def setUp(self) -> None:
        self.source = SOURCE_WORKFLOWS
        self.workflows = INS.parse_manifest(self.source)

    def test_generate_shim_members_emits_aw_dispatcher_and_retains_aliases(
        self,
    ) -> None:
        """generate_shim_members emits aw.md per host and retains per-workflow aliases."""
        shims = INS.generate_shim_members(
            self.workflows, self.source, target_layout="aw"
        )

        # Dispatcher emitted for both hosts
        self.assertIn(".opencode/commands/aw.md", shims)
        self.assertIn(".claude/commands/aw.md", shims)

        # READMEs present
        self.assertIn(".opencode/commands/README.md", shims)
        self.assertIn(".claude/commands/README.md", shims)

        # Back-compat aliases retained
        sample_commands = (
            "assess",
            "advise",
            "handoff",
            "verify",
            "plan-review",
            "setup-repo",
            "spec",
            "whatnext",
        )
        for cmd in sample_commands:
            self.assertIn(f".opencode/commands/{cmd}.md", shims)
            self.assertIn(f".claude/commands/{cmd}.md", shims)

        # Content of per-workflow shims matches shim_body unchanged
        wf_map = {w.command: w for w in self.workflows}
        for cmd in sample_commands:
            expected_oc = INS.shim_body(
                cmd, wf_map[cmd], "opencode", target_layout="aw"
            )
            expected_cl = INS.shim_body(cmd, wf_map[cmd], "claude", target_layout="aw")
            self.assertEqual(shims[f".opencode/commands/{cmd}.md"], expected_oc)
            self.assertEqual(shims[f".claude/commands/{cmd}.md"], expected_cl)

    def test_aw_dispatcher_shim_content_opencode(self) -> None:
        """aw_dispatcher_shim produces valid OpenCode dispatcher shim."""
        body_aw = INS.aw_dispatcher_shim(self.workflows, "opencode", target_layout="aw")
        self.assertTrue(body_aw.startswith("---\n"))
        self.assertIn("agent: build\n", body_aw)
        self.assertIn("description: ", body_aw)
        self.assertIn(
            "Read the workflow manifest @.aw/system/workflows/index.md.", body_aw
        )
        self.assertIn("$ARGUMENTS", body_aw)
        self.assertIn("If the user provided arguments,", body_aw)
        self.assertTrue(
            body_aw.endswith(
                "Treat the referenced file as the controlling instruction and follow it fully.\n"
            )
        )

        body_legacy = INS.aw_dispatcher_shim(
            self.workflows, "opencode", target_layout="legacy"
        )
        self.assertIn(
            "Read the workflow manifest @.agents/workflows/index.md.", body_legacy
        )

    def test_aw_dispatcher_shim_content_claude(self) -> None:
        """aw_dispatcher_shim produces valid Claude dispatcher shim."""
        body_aw = INS.aw_dispatcher_shim(self.workflows, "claude", target_layout="aw")
        self.assertTrue(body_aw.startswith("---\n"))
        self.assertIn("argument-hint: ", body_aw)
        self.assertNotIn("agent: build", body_aw)
        self.assertIn("description: ", body_aw)
        self.assertIn(
            "Read the workflow manifest @.aw/system/workflows/index.md.", body_aw
        )
        self.assertIn("$ARGUMENTS", body_aw)
        self.assertIn("If the user provided arguments,", body_aw)
        self.assertTrue(
            body_aw.endswith(
                "Treat the referenced file as the controlling instruction and follow it fully.\n"
            )
        )

        body_legacy = INS.aw_dispatcher_shim(
            self.workflows, "claude", target_layout="legacy"
        )
        self.assertIn(
            "Read the workflow manifest @.agents/workflows/index.md.", body_legacy
        )

    def test_validate_shim_grammar_positive_for_dispatcher_and_aliases(self) -> None:
        """validate_shim_grammar returns True for valid dispatcher and alias shims."""
        # Dispatchers
        oc_dispatcher = INS.aw_dispatcher_shim(
            self.workflows, "opencode", target_layout="aw"
        )
        cl_dispatcher = INS.aw_dispatcher_shim(
            self.workflows, "claude", target_layout="aw"
        )
        self.assertTrue(INS.validate_shim_grammar(oc_dispatcher, "opencode"))
        self.assertTrue(INS.validate_shim_grammar(cl_dispatcher, "claude"))

        oc_legacy_disp = INS.aw_dispatcher_shim(
            self.workflows, "opencode", target_layout="legacy"
        )
        cl_legacy_disp = INS.aw_dispatcher_shim(
            self.workflows, "claude", target_layout="legacy"
        )
        self.assertTrue(INS.validate_shim_grammar(oc_legacy_disp, "opencode"))
        self.assertTrue(INS.validate_shim_grammar(cl_legacy_disp, "claude"))

        # Aliases
        shims = INS.generate_shim_members(
            self.workflows, self.source, target_layout="aw"
        )
        for rel, content in shims.items():
            if rel.endswith("README.md"):
                continue
            tool = "claude" if rel.startswith(".claude") else "opencode"
            self.assertTrue(
                INS.validate_shim_grammar(content, tool),
                f"validate_shim_grammar returned False for valid shim: {rel}",
            )

    def test_validate_shim_grammar_negative_cases(self) -> None:
        """validate_shim_grammar rejects malformed shims."""
        valid_oc = INS.aw_dispatcher_shim(
            self.workflows, "opencode", target_layout="aw"
        )
        valid_cl = INS.aw_dispatcher_shim(self.workflows, "claude", target_layout="aw")

        # 1. Empty or non-string
        self.assertFalse(INS.validate_shim_grammar("", "opencode"))
        self.assertFalse(INS.validate_shim_grammar("   \n\n", "claude"))

        # 2. Unknown tool
        self.assertFalse(INS.validate_shim_grammar(valid_oc, "unknown_tool"))

        # 3. Missing front fence
        no_front_fence = valid_oc.lstrip("-\n")
        self.assertFalse(INS.validate_shim_grammar(no_front_fence, "opencode"))

        # 4. Missing closing fence
        no_closing_fence = valid_oc.replace("---\n", "", 1)
        self.assertFalse(INS.validate_shim_grammar(no_closing_fence, "opencode"))

        # 5. Missing description
        no_desc = "---\nagent: build\n---\nRead and execute @.aw/system/workflows/verify/verify.md.\n"
        self.assertFalse(INS.validate_shim_grammar(no_desc, "opencode"))

        # 6. OpenCode missing agent:
        oc_no_agent = "---\ndescription: test\n---\nRead and execute @.aw/system/workflows/verify/verify.md.\n"
        self.assertFalse(INS.validate_shim_grammar(oc_no_agent, "opencode"))

        # 7. Claude with agent: build present (invalid for Claude)
        cl_with_agent = valid_cl.replace("---\n", "---\nagent: build\n", 1)
        self.assertFalse(INS.validate_shim_grammar(cl_with_agent, "claude"))

        # 8. Missing target reference
        no_target = "---\ndescription: test\nagent: build\n---\nRead and execute some random path.\n"
        self.assertFalse(INS.validate_shim_grammar(no_target, "opencode"))

        # 9. Claude with argument-hint but no $ARGUMENTS in body
        cl_no_args = (
            "---\n"
            "description: test\n"
            'argument-hint: "[args]"\n'
            "---\n"
            "Read and execute @.aw/system/workflows/verify/verify.md.\n"
        )
        self.assertFalse(INS.validate_shim_grammar(cl_no_args, "claude"))

        # 10. $ARGUMENTS present without proper clause
        broken_args = (
            "---\n"
            "description: test\n"
            "agent: build\n"
            "---\n"
            "Read and execute @.aw/system/workflows/verify/verify.md.\n"
            "Just args $ARGUMENTS\n"
        )
        self.assertFalse(INS.validate_shim_grammar(broken_args, "opencode"))

    def test_is_shim_customized_does_not_flag_dispatcher(self) -> None:
        """is_shim_customized recognizes the dispatcher shim as non-customized standard shim."""
        oc = INS.aw_dispatcher_shim(self.workflows, "opencode", target_layout="aw")
        cl = INS.aw_dispatcher_shim(self.workflows, "claude", target_layout="aw")
        self.assertFalse(INS.is_shim_customized(oc))
        self.assertFalse(INS.is_shim_customized(cl))
        self.assertFalse(INS.is_shim_customized_vs_expected(oc, oc))
        self.assertFalse(INS.is_shim_customized_vs_expected(cl, cl))


if __name__ == "__main__":
    unittest.main()
