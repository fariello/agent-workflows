"""Tests for authoring and review prompt pointers to the writing standard (IPD jhdti8 E-02).

Spec ecmw83 R-06:
1. Rendered backlog and spec (approved and implementing) production prompts contain the
   technical writing standard contract line between '## Production Contract' and the next '## ' heading.
2. The standard's path resolves to .aw/system/workflows/technical-writing/technical-writing.md
   when .aw/system/ is present.
3. The standard's path resolves to .agents/workflows/technical-writing/technical-writing.md
   when only .agents/workflows/ is present.
4. The three contract lines are identical once the leading item number is removed.
5. The non-isolated build_review_prompt output for an IPD item is still the single line
   '/plan-review <relative path>', remaining prose-free.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import pytest

from agent_workflows import runner_shared

pytestmark = pytest.mark.core


def _extract_contract_section(prompt: str) -> list[str]:
    lines = prompt.splitlines()
    in_contract = False
    contract_lines: list[str] = []
    for line in lines:
        if line.startswith("## Production Contract"):
            in_contract = True
            continue
        if in_contract:
            if line.startswith("## "):
                break
            contract_lines.append(line)
    return contract_lines


def _find_writing_standard_line(lines: list[str]) -> str:
    matches = [
        line for line in lines if "technical-writing/technical-writing.md" in line
    ]
    assert (
        len(matches) == 1
    ), f"Expected exactly one writing standard line, found: {matches}"
    return matches[0]


class ProductionPromptWritingStandardTests(unittest.TestCase):
    def test_production_prompts_writing_standard_aw_layout(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            (repo / ".aw" / "system").mkdir(parents=True)
            run_dir = repo / "run-001"
            run_dir.mkdir(parents=True)

            spec_app_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261001-demo-01-demo-test.spec.md"
            )
            spec_app_path.parent.mkdir(parents=True, exist_ok=True)
            spec_app_path.write_text(
                "# Spec\n- Id: demo01\n- Status: approved\n", encoding="utf-8"
            )

            spec_imp_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "implementing"
                / "20261001-demo-01-demo-test.spec.md"
            )
            spec_imp_path.parent.mkdir(parents=True, exist_ok=True)
            spec_imp_path.write_text(
                "# Spec\n- Id: demo01\n- Status: implementing\n", encoding="utf-8"
            )

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

            plan_path = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-tst01-test.ipd.md"
            )
            plan_path.parent.mkdir(parents=True, exist_ok=True)
            plan_path.write_text("# Plan\n- Id: tst001\n", encoding="utf-8")

            state = {"repo": str(repo), "run_id": "run-001"}
            spec_item = {"id6": "demo01"}
            backlog_item = {"id6": "bkl001"}
            plan_item = {"id6": "tst001"}

            prompt_spc_app = runner_shared.build_spec_production_prompt(
                spec_item, state, run_dir, spec_app_path, repo
            )
            prompt_spc_imp = runner_shared.build_spec_production_prompt(
                spec_item, state, run_dir, spec_imp_path, repo
            )
            prompt_bkl = runner_shared.build_backlog_production_prompt(
                backlog_item, state, run_dir, backlog_path, repo
            )

            expected_suffix = (
                "Write and proofread every plan you author or revise per "
                "`.aw/system/workflows/technical-writing/technical-writing.md`, "
                "including requirement 12 (diagrams). If that file is absent, "
                "report the missing dependency and do not claim compliance."
            )

            contract_lines_app = _extract_contract_section(prompt_spc_app)
            line_app = _find_writing_standard_line(contract_lines_app)
            self.assertTrue(line_app.startswith("9. "))
            self.assertIn(
                ".aw/system/workflows/technical-writing/technical-writing.md", line_app
            )

            contract_lines_imp = _extract_contract_section(prompt_spc_imp)
            line_imp = _find_writing_standard_line(contract_lines_imp)
            self.assertTrue(line_imp.startswith("9. "))
            self.assertIn(
                ".aw/system/workflows/technical-writing/technical-writing.md", line_imp
            )

            contract_lines_bkl = _extract_contract_section(prompt_bkl)
            line_bkl = _find_writing_standard_line(contract_lines_bkl)
            self.assertTrue(line_bkl.startswith("8. "))
            self.assertIn(
                ".aw/system/workflows/technical-writing/technical-writing.md", line_bkl
            )

            # Strip leading number and assert identical
            body_app = line_app.split(". ", 1)[1]
            body_imp = line_imp.split(". ", 1)[1]
            body_bkl = line_bkl.split(". ", 1)[1]

            self.assertEqual(body_app, expected_suffix)
            self.assertEqual(body_app, body_imp)
            self.assertEqual(body_app, body_bkl)

            # Assert non-isolated build_review_prompt output for IPD is single line /plan-review <relative path>
            review_prompt = runner_shared.build_review_prompt(
                plan_item, state, run_dir, plan_path, repo
            )
            self.assertEqual(
                review_prompt,
                "/plan-review .aw/records/plans/pending/20261001-test-01-tst01-test.ipd.md",
            )

    def test_production_prompts_writing_standard_legacy_layout(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            (repo / ".agents" / "workflows").mkdir(parents=True)
            run_dir = repo / "run-001"
            run_dir.mkdir(parents=True)

            spec_app_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "approved"
                / "20261001-demo-01-demo-test.spec.md"
            )
            spec_app_path.parent.mkdir(parents=True, exist_ok=True)
            spec_app_path.write_text(
                "# Spec\n- Id: demo01\n- Status: approved\n", encoding="utf-8"
            )

            spec_imp_path = (
                repo
                / ".aw"
                / "records"
                / "specs"
                / "implementing"
                / "20261001-demo-01-demo-test.spec.md"
            )
            spec_imp_path.parent.mkdir(parents=True, exist_ok=True)
            spec_imp_path.write_text(
                "# Spec\n- Id: demo01\n- Status: implementing\n", encoding="utf-8"
            )

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

            state = {"repo": str(repo), "run_id": "run-001"}
            spec_item = {"id6": "demo01"}
            backlog_item = {"id6": "bkl001"}

            prompt_spc_app = runner_shared.build_spec_production_prompt(
                spec_item, state, run_dir, spec_app_path, repo
            )
            prompt_spc_imp = runner_shared.build_spec_production_prompt(
                spec_item, state, run_dir, spec_imp_path, repo
            )
            prompt_bkl = runner_shared.build_backlog_production_prompt(
                backlog_item, state, run_dir, backlog_path, repo
            )

            expected_suffix = (
                "Write and proofread every plan you author or revise per "
                "`.agents/workflows/technical-writing/technical-writing.md`, "
                "including requirement 12 (diagrams). If that file is absent, "
                "report the missing dependency and do not claim compliance."
            )

            contract_lines_app = _extract_contract_section(prompt_spc_app)
            line_app = _find_writing_standard_line(contract_lines_app)
            self.assertTrue(line_app.startswith("9. "))
            self.assertIn(
                ".agents/workflows/technical-writing/technical-writing.md", line_app
            )

            contract_lines_imp = _extract_contract_section(prompt_spc_imp)
            line_imp = _find_writing_standard_line(contract_lines_imp)
            self.assertTrue(line_imp.startswith("9. "))
            self.assertIn(
                ".agents/workflows/technical-writing/technical-writing.md", line_imp
            )

            contract_lines_bkl = _extract_contract_section(prompt_bkl)
            line_bkl = _find_writing_standard_line(contract_lines_bkl)
            self.assertTrue(line_bkl.startswith("8. "))
            self.assertIn(
                ".agents/workflows/technical-writing/technical-writing.md", line_bkl
            )

            body_app = line_app.split(". ", 1)[1]
            body_imp = line_imp.split(". ", 1)[1]
            body_bkl = line_bkl.split(". ", 1)[1]

            self.assertEqual(body_app, expected_suffix)
            self.assertEqual(body_app, body_imp)
            self.assertEqual(body_app, body_bkl)
