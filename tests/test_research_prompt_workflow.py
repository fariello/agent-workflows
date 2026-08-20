"""Unit tests for the research-prompt producer workflow.

Asserts:
- Workflow body file and README exist.
- Manifest row is registered as the 'research' verb pointing to the workflow body.
- Dispatcher routes /aw research to the workflow body.
- No standalone 'research-prompt' host shim is generated.
- Workflow body encodes the AGENTS.md prompt-purity contract:
  1. Only-the-prompt (no user instructions inside the emitted prompt)
  2. Self-contained
  3. Downloadable .md file
- Workflow body states the distinction from 'aw research' doc verb,
  targets .aw/records/prompts/pending/, carries leading HTML comment metadata,
  and specifies Status: pending without auto-committing.
"""

from __future__ import annotations

import unittest

from agent_workflows import engine as INS
from tests.support import REPO_ROOT, SOURCE_WORKFLOWS


class ResearchPromptWorkflowTests(unittest.TestCase):
    """Tests for research-prompt producer workflow files and manifest registration."""

    def setUp(self) -> None:
        self.workflow_dir = (
            REPO_ROOT / ".aw" / "system" / "workflows" / "research-prompt"
        )
        self.body_path = self.workflow_dir / "research-prompt.md"
        self.readme_path = self.workflow_dir / "README.md"
        self.index_path = REPO_ROOT / ".aw" / "system" / "workflows" / "index.md"
        self.workflows = INS.parse_manifest(SOURCE_WORKFLOWS)

    def test_workflow_files_exist(self) -> None:
        """The workflow body and README files must exist and not be empty."""
        self.assertTrue(
            self.body_path.is_file(),
            f"Workflow body not found at {self.body_path}",
        )
        self.assertTrue(
            self.readme_path.is_file(),
            f"Workflow README not found at {self.readme_path}",
        )
        body_text = self.body_path.read_text(encoding="utf-8")
        readme_text = self.readme_path.read_text(encoding="utf-8")
        self.assertGreater(len(body_text.strip()), 100)
        self.assertGreater(len(readme_text.strip()), 50)

    def test_manifest_registers_research_verb(self) -> None:
        """The manifest registers 'research' pointing to the workflow body."""
        wf_map = {w.command: w for w in self.workflows}
        self.assertIn(
            "research",
            wf_map,
            "Manifest does not contain 'research' workflow command row",
        )
        wf = wf_map["research"]
        self.assertEqual(
            wf.body,
            ".aw/system/workflows/research-prompt/research-prompt.md",
        )
        self.assertFalse(wf.lens)
        self.assertTrue(wf.description)

    def test_no_standalone_research_prompt_shims(self) -> None:
        """No standalone research-prompt host shims should exist or be generated."""
        shims = INS.generate_shim_members(
            self.workflows, SOURCE_WORKFLOWS, target_layout="aw"
        )
        self.assertNotIn(".opencode/commands/research-prompt.md", shims)
        self.assertNotIn(".claude/commands/research-prompt.md", shims)

        on_disk_oc = REPO_ROOT / ".opencode" / "commands" / "research-prompt.md"
        on_disk_cl = REPO_ROOT / ".claude" / "commands" / "research-prompt.md"
        self.assertFalse(
            on_disk_oc.exists(),
            f"Unexpected standalone shim found: {on_disk_oc}",
        )
        self.assertFalse(
            on_disk_cl.exists(),
            f"Unexpected standalone shim found: {on_disk_cl}",
        )

    def test_workflow_body_encodes_prompt_purity_and_contracts(self) -> None:
        """Workflow body encodes the three AGENTS.md prompt-purity rules and required contracts."""
        self.assertTrue(
            self.body_path.is_file(),
            f"Workflow body not found at {self.body_path}",
        )
        content = self.body_path.read_text(encoding="utf-8")

        # 1. Prompt-purity rule 1: only the prompt itself (no user-facing instructions inside)
        self.assertTrue(
            ("ONLY the prompt" in content or "only the prompt" in content.lower())
            and (
                "no user-facing instructions" in content.lower()
                or "no instructions for the user" in content.lower()
            ),
            "Workflow body must mandate that the prompt contains only the prompt with no user-facing instructions inside",
        )

        # 2. Prompt-purity rule 2: self-contained
        self.assertTrue(
            "self-contained" in content.lower(),
            "Workflow body must mandate that the prompt is self-contained",
        )

        # 3. Prompt-purity rule 3: downloadable .md file
        self.assertTrue(
            ("downloadable" in content.lower() and ".md" in content),
            "Workflow body must instruct target AI to return answer as a downloadable .md file",
        )

        # 4. Target path is .aw/records/prompts/pending/
        self.assertIn(
            ".aw/records/prompts/pending/",
            content,
            "Workflow body must target .aw/records/prompts/pending/",
        )

        # 5. Distinction from aw research / research records
        self.assertTrue(
            "aw research" in content
            and ("doc" in content.lower() or "record" in content.lower()),
            "Workflow body must state the distinction from 'aw research' doc creation",
        )

        # 6. Leading HTML comment pipeline metadata
        self.assertTrue(
            "<!-- aw-prompt:" in content
            or ("<!--" in content and "aw-prompt" in content),
            "Workflow body must specify the leading HTML comment metadata pattern",
        )

        # 7. Status: pending and never auto-commit
        self.assertIn("Status: pending", content)
        self.assertTrue(
            "never auto-commit" in content.lower()
            or "never auto-stage" in content.lower()
            or "never commit" in content.lower(),
            "Workflow body must specify never auto-committing",
        )

    def test_readme_content(self) -> None:
        """README.md contains the /aw research invocation, fallback, and index/doc pointers."""
        self.assertTrue(
            self.readme_path.is_file(),
            f"Workflow README not found at {self.readme_path}",
        )
        content = self.readme_path.read_text(encoding="utf-8")

        self.assertIn("/aw research", content)
        self.assertIn(
            "read and execute `.aw/system/workflows/research-prompt/research-prompt.md`",
            content,
        )
        self.assertIn(".aw/system/workflows/index.md", content)
        self.assertIn("aw research", content)

    def test_prompt_purity_negative_detection(self) -> None:
        """Negative test: a defective workflow body missing prompt-purity rules fails verification."""

        def check_purity(text: str) -> bool:
            has_only_prompt = ("only the prompt" in text.lower()) and (
                "no user-facing instructions" in text.lower()
                or "no instructions for the user" in text.lower()
            )
            has_self_contained = "self-contained" in text.lower()
            has_downloadable = "downloadable" in text.lower() and ".md" in text
            return has_only_prompt and has_self_contained and has_downloadable

        # Valid text
        valid_sample = (
            "The prompt contains ONLY the prompt itself with no user-facing instructions inside. "
            "It is self-contained and instructs the AI to return a downloadable .md file."
        )
        self.assertTrue(check_purity(valid_sample))

        # Missing 'only the prompt' / user instructions prohibition
        missing_only_prompt = "It is self-contained and instructs the AI to return a downloadable .md file."
        self.assertFalse(check_purity(missing_only_prompt))

        # Missing 'self-contained'
        missing_self_contained = "The prompt contains only the prompt itself with no user-facing instructions. Return a downloadable .md file."
        self.assertFalse(check_purity(missing_self_contained))

        # Missing 'downloadable .md'
        missing_downloadable = "The prompt contains only the prompt itself with no user-facing instructions. It is self-contained."
        self.assertFalse(check_purity(missing_downloadable))


if __name__ == "__main__":
    unittest.main()
