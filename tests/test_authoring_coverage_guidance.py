"""Tests for authoring coverage guidance (IPD dalmk4 E-05).

Asserts outcomes of generated guidance and templates:
1. Rendered backlog and spec production prompts contain the orchestrator rule items and aw ipd coverage.
2. aw ipd scaffold subprocess output emits the new orchestrator placeholders and keeps child distinct.
3. authoring_placeholders_resolved identifies newly scaffolded orchestrator and partially-resolved orchestrator with one placeholder left as stubs.
4. engine.agents_pointer_prose for both layouts contains the step (5) precondition, the "may RETIRE" scope and the quote sentence, and does not contain "The verdict is CACHED".
5. aw install into a fresh temp repository installs AGENTS.md with the step (5) precondition in its managed block.

P16 compliant: asserts generated outputs only, never reads production source or docstrings.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine, ipd_authoring, ipd_schema, runner_shared
from tests.support import init_repo, run_installer


class ProductionPromptCoverageGuidanceTests(unittest.TestCase):
    def test_rendered_prompts_contain_orchestrator_coverage_rules(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            run_dir = repo / "run-001"
            run_dir.mkdir(parents=True, exist_ok=True)
            spec_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261001-demo-01-demo-test.spec.md"
            )
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_text("# Spec\n- Id: demo01\n", encoding="utf-8")
            backlog_path = (
                repo
                / ".aw"
                / "records"
                / "backlog"
                / "open"
                / "20261001-bkl01-01-bkl01-test.backlog.md"
            )
            backlog_path.parent.mkdir(parents=True, exist_ok=True)
            backlog_path.write_text("# Backlog\n- Id: bkl001\n", encoding="utf-8")

            state = {"repo": str(repo)}
            spec_item = {"id6": "demo01"}
            backlog_item = {"id6": "bkl001"}

            prompt_spc = runner_shared.build_spec_production_prompt(
                spec_item, state, run_dir, spec_path, repo
            )
            prompt_bkl = runner_shared.build_backlog_production_prompt(
                backlog_item, state, run_dir, backlog_path, repo
            )

            for prompt_name, prompt in (("spec", prompt_spc), ("backlog", prompt_bkl)):
                self.assertIn("## Orchestrator plans (when you write a Set)", prompt)
                self.assertIn("aw ipd coverage <orchestrator-id6>", prompt)
                self.assertIn(
                    "1. Every item under `## Completion criteria`, `## Cross-IPD validation` and `## Required tests / validation` names, by id6, the child plan in this Set's `## Child IPDs` table that performs it.",
                    prompt,
                )
                self.assertIn(
                    "2. Work no existing child performs gets a NEW child plan and a table row, never a step on the orchestrator.",
                    prompt,
                )
                self.assertIn(
                    "3. The orchestrator's checklist contains only `CONFIRM <child-id6> REACHED <status>` rows, and you never delete it.",
                    prompt,
                )
                self.assertIn(
                    "4. Before you finish, run `aw ipd coverage <orchestrator-id6>` and fix every quoted finding it prints; it records its answer in the orchestrator plan, and the runner checks the whole Set again after your turn (`BACKLOG-GRADUATE-SET` / `SPEC-PLAN-SET`, Order 06), so an unfixed finding fails the item.",
                    prompt,
                )

                pos_contract = prompt.find("## Production Contract")
                pos_orch = prompt.find("## Orchestrator plans (when you write a Set)")
                pos_prohib = prompt.find("## Prohibitions")
                self.assertTrue(
                    pos_contract < pos_orch < pos_prohib,
                    f"{prompt_name} prompt section ordering expected contract < orch < prohib, got {pos_contract}, {pos_orch}, {pos_prohib}",
                )


class ScaffoldPlaceholderOutputTests(unittest.TestCase):
    def test_scaffold_subprocess_emits_expected_placeholders(self):
        # Orchestrator scaffold dry run
        cmd_orch = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "scaffold",
            "--kind",
            "orchestrator",
            "--title",
            "Test Orchestrator",
            "--set",
            "testset",
            "--author",
            "tester",
            "--order",
            "0",
            "--priority",
            "high",
            "--work-kind",
            "feature",
        ]
        res_orch = subprocess.run(cmd_orch, capture_output=True, text=True, check=True)
        out_orch = res_orch.stdout

        self.assertIn(
            '- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.',
            out_orch,
        )
        self.assertIn(
            "- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.",
            out_orch,
        )
        self.assertIn(
            "TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.",
            out_orch,
        )

        # Child scaffold dry run
        cmd_child = [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Test Child",
            "--set",
            "testset",
            "--author",
            "tester",
            "--order",
            "1",
            "--priority",
            "high",
            "--work-kind",
            "feature",
        ]
        res_child = subprocess.run(
            cmd_child, capture_output=True, text=True, check=True
        )
        out_child = res_child.stdout

        self.assertNotIn(
            "TODO: this plan runs no tests; name the child plan (by id6) that performs the whole-Set measurement.",
            out_child,
        )
        self.assertIn("TODO: how the executed plan is verified.", out_child)


class AuthoringPlaceholdersStubPredicateTests(unittest.TestCase):
    def test_orchestrator_scaffold_is_stub(self):
        orch_text = ipd_authoring.build_skeleton(
            kind="orchestrator",
            title="Test Orchestrator",
            author="tester",
            when="2026-10-06",
            set_name="testset",
            order=0,
            plan_id="tmp1d6",
        )
        self.assertFalse(
            ipd_authoring.authoring_placeholders_resolved(orch_text),
            "Freshly scaffolded orchestrator must be reported as a stub",
        )

    def test_orchestrator_with_one_placeholder_left_is_stub(self):
        orch_text = ipd_authoring.build_skeleton(
            kind="orchestrator",
            title="Test Orchestrator",
            author="tester",
            when="2026-10-06",
            set_name="testset",
            order=0,
            plan_id="tmp1d6",
        )
        # Replace every listed placeholder except the new ones
        cleaned = orch_text
        for ph in ipd_authoring._AUTHORING_PLACEHOLDERS:
            if ph not in (
                ipd_authoring._SECTION_BODY[ipd_schema.H_COMPLETION],
                ipd_authoring._SECTION_BODY[ipd_schema.H_CROSS_IPD],
                ipd_authoring._ORCH_SECTION_BODY[ipd_schema.H_REQUIRED_TESTS],
            ):
                cleaned = cleaned.replace(ph, "RESOLVED")

        # Also replace two of the three new placeholders
        cleaned = cleaned.replace(
            ipd_authoring._SECTION_BODY[ipd_schema.H_COMPLETION], "RESOLVED"
        )
        cleaned = cleaned.replace(
            ipd_authoring._SECTION_BODY[ipd_schema.H_CROSS_IPD], "RESOLVED"
        )

        # Leaving only the third new placeholder (H_REQUIRED_TESTS)
        self.assertFalse(
            ipd_authoring.authoring_placeholders_resolved(cleaned),
            "Orchestrator with one new placeholder left must still be reported as a stub",
        )

        # Once that final placeholder is resolved, it should report resolved
        cleaned = cleaned.replace(
            ipd_authoring._ORCH_SECTION_BODY[ipd_schema.H_REQUIRED_TESTS], "RESOLVED"
        )
        self.assertTrue(
            ipd_authoring.authoring_placeholders_resolved(cleaned),
            "Orchestrator with all placeholders replaced must be reported resolved",
        )


class AgentsPointerProseGuidanceTests(unittest.TestCase):
    def test_agents_pointer_prose_contains_coverage_guidance(self):
        expected_precondition = (
            "only once every plan you wrote is `to-review` or later, lints, and, for an "
            "orchestrator, passes `aw ipd coverage <id6>`: `aw backlog set graduated` refuses otherwise."
        )
        expected_scope = (
            "a run that may RETIRE an orchestrator asks a MODEL once per orchestrator "
            "it could retire, and asks again immediately before retiring it"
        )
        expected_quote = "The refusal QUOTES each uncovered passage."
        cached_sentence = "The verdict is CACHED"

        for layout in ("aw", "legacy"):
            prose = engine.agents_pointer_prose(target_layout=layout)
            self.assertIn(
                expected_precondition,
                prose,
                f"Layout {layout} missing step (5) precondition",
            )
            self.assertIn(
                expected_scope,
                prose,
                f"Layout {layout} missing 'may RETIRE' scope",
            )
            self.assertIn(
                expected_quote,
                prose,
                f"Layout {layout} missing quote sentence",
            )
            self.assertNotIn(
                cached_sentence,
                prose,
                f"Layout {layout} must not contain CACHED sentence",
            )


class FreshInstallManagedBlockTests(unittest.TestCase):
    def test_fresh_install_writes_agents_md_with_precondition(self):
        expected_precondition = (
            "only once every plan you wrote is `to-review` or later, lints, and, for an "
            "orchestrator, passes `aw ipd coverage <id6>`: `aw backlog set graduated` refuses otherwise."
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = init_repo(Path(tmp_dir))
            proc = run_installer(repo)
            self.assertEqual(
                proc.returncode,
                0,
                f"Installer failed: {proc.stderr}\n{proc.stdout}",
            )
            agents_md = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(expected_precondition, agents_md)


if __name__ == "__main__":
    unittest.main()
