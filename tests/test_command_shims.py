"""Unit tests for slash-command shims and the /aw dispatcher.

Covers:
- /aw dispatcher shim generation for OpenCode and Claude hosts
- generate_shim_members emitting the /aw dispatcher alongside back-compat aliases
- per-host grammar validation (validate_shim_grammar) positive and negative cases
"""

from __future__ import annotations

import unittest

from agent_workflows import engine as INS
from agent_workflows import reporting_contract as RC
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
        self.assertIn(
            "Treat the referenced file as the controlling instruction and follow it fully.\n",
            body_aw,
        )
        # terseout `ntf6sx` E-03: the reporting POINTER is now the shim's last line. Asserted
        # here (not just its presence) so the controlling-instruction line keeps its place
        # immediately before it.
        self.assertTrue(body_aw.endswith(RC.shim_pointer_line()))

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
        self.assertIn(
            "Treat the referenced file as the controlling instruction and follow it fully.\n",
            body_aw,
        )
        # terseout `ntf6sx` E-03: the reporting POINTER is now the shim's last line.
        self.assertTrue(body_aw.endswith(RC.shim_pointer_line()))

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

    def test_per_workflow_shims_contain_deprecation_notice_and_dispatcher_does_not(
        self,
    ) -> None:
        """Every generated per-workflow shim carries deprecation notice; dispatcher does not (E-01/V-01)."""
        shims = INS.generate_shim_members(
            self.workflows, self.source, target_layout="aw"
        )
        wf_commands = {
            w.command for w in self.workflows if not INS.is_concern_catalog_row(w)
        }

        # Dispatcher shims do NOT contain deprecation notice
        for host in ("opencode", "claude"):
            disp_key = f".{host}/commands/aw.md"
            self.assertIn(disp_key, shims)
            self.assertNotIn("deprecated", shims[disp_key].lower())
            self.assertNotIn("deprecation", shims[disp_key].lower())

        # Every per-workflow shim contains deprecation notice mentioning /aw <verb>
        for cmd in wf_commands:
            for host in ("opencode", "claude"):
                shim_key = f".{host}/commands/{cmd}.md"
                self.assertIn(shim_key, shims)
                content = shims[shim_key]
                self.assertIn("deprecated", content.lower())
                self.assertIn(f"/aw {cmd}", content)
                self.assertIn("pruned", content.lower())
                self.assertIn("alias", content.lower())

    def test_deprecation_notice_placement_in_body_and_grammar_valid(
        self,
    ) -> None:
        """Notice is placed in the body after closing fence, not in frontmatter, and grammar passes (E-02/V-02)."""
        shims = INS.generate_shim_members(
            self.workflows, self.source, target_layout="aw"
        )
        for rel, content in shims.items():
            if rel.endswith("README.md"):
                continue
            tool = "claude" if rel.startswith(".claude") else "opencode"
            self.assertTrue(
                INS.validate_shim_grammar(content, tool),
                f"validate_shim_grammar returned False for {rel}",
            )
            if not rel.endswith("/aw.md"):
                lines = content.splitlines()
                closing_fence_idx = -1
                for idx in range(1, len(lines)):
                    if lines[idx].strip() == "---":
                        closing_fence_idx = idx
                        break
                self.assertGreater(closing_fence_idx, 0)
                frontmatter_text = "\n".join(lines[1:closing_fence_idx])
                body_text = "\n".join(lines[closing_fence_idx + 1 :])
                self.assertNotIn("deprecated", frontmatter_text.lower())
                self.assertNotIn("deprecation", frontmatter_text.lower())
                self.assertIn("deprecation notice", body_text.lower())

    def test_shim_drift_reconciliation_pre_notice_updates_customized_preserved(
        self,
    ) -> None:
        """Pre-notice shim is classified installer-owned and updates, while customized shim is preserved (E-02/V-02)."""
        wf_map = {w.command: w for w in self.workflows}
        spec_wf = wf_map["spec"]

        # 1. Post-notice generated shim is not customized
        current_expected = INS.shim_body(
            "spec", spec_wf, "opencode", target_layout="aw"
        )
        self.assertFalse(INS.is_shim_customized(current_expected))

        # 2. Pre-notice generated shim (without the deprecation line)
        pre_notice_lines = [
            line
            for line in current_expected.splitlines()
            if "deprecation" not in line.lower() and "deprecated" not in line.lower()
        ]
        pre_notice_shim = "\n".join(pre_notice_lines) + "\n"
        self.assertNotIn("deprecated", pre_notice_shim)
        self.assertFalse(
            INS.is_shim_customized(pre_notice_shim),
            "pre-notice generated shim must be recognized as installer-owned (not customized)",
        )

        # 3. Plan-level drift check for pre-notice shim without manifest (structural fallback)
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            plan = INS.InstallPlan(
                source_root=self.source,
                repo_root=repo_root,
                dry_run=False,
                backup=True,
                prune=True,
                no_color=True,
                yes=False,
                manifest=None,
            )
            # Pre-notice shim is NOT flagged as user modified -> updates silently
            self.assertFalse(
                INS._shim_is_user_modified(
                    plan,
                    ".opencode/commands/spec.md",
                    pre_notice_shim,
                    current_expected,
                ),
                "pre-notice shim must not be flagged as user modified",
            )

            # 4. Genuinely customized shim IS flagged as user modified
            customized_shim = (
                pre_notice_shim + "\n# User hand-edit: custom steps\necho 'custom'\n"
            )
            self.assertTrue(
                INS.is_shim_customized(customized_shim),
                "customized shim must be detected as customized",
            )
            self.assertTrue(
                INS._shim_is_user_modified(
                    plan,
                    ".opencode/commands/spec.md",
                    customized_shim,
                    current_expected,
                ),
                "customized shim must be flagged as user modified",
            )


if __name__ == "__main__":
    unittest.main()
