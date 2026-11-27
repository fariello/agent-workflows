"""Behavioral tests for runner --pre-prompt, --post-prompt, and --prompt flags."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import agy_runipd, cli, oc_runipd, runner_shared
from tests.record_builder import RecordBuilder


def _init_repo_with_approved_plan(root: Path, id6: str = "prw001") -> tuple[Path, Path]:
    repo = root / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(
        ".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8"
    )
    (repo / "README.md").write_text("initial\n", encoding="utf-8")
    plan_path = Path(
        RecordBuilder(repo).plan(
            id6=id6,
            title="Prompt wrapper test plan",
            when="2026-11-27",
            set="prwset",
            order=1,
            slug="prompt-wrapper-test",
            status="approved",
            scope_paths="README.md",
            item_dependencies="none",
            priority="medium",
            work_kind="feature",
            readiness="go-pending-approval",
            approval="2026-11-27, test",
            history=[
                "- 2026-11-27 approved (aw set): approved for test",
                "- 2026-11-27 /plan-review (tester): APPROVE",
            ],
            body=(
                "## Goal\nTest operator prompt wrappers.\n\n"
                "## Detailed Implementation Checklist (TODO)\n"
                "### Task group 1: work\n"
                "- [ ] E-01 Update README.md\n"
                "  - Depends on: none\n"
                "  - Expected outcome: updated\n"
                "  - Execution state: pending\n\n"
                "## Project conventions discovered (Step 0)\nNone.\n\n"
                "## Findings\nNone.\n\n"
                "## Proposed changes (ordered, validatable)\nUpdate README.md.\n\n"
                "## Deferred / out of scope (with reason)\nNone.\n\n"
                "## Scope check\n- Over-scope: none.\n- Under-scope: none.\n\n"
                "## Required tests / validation\nV-01.\n\n"
                "## Spec / documentation sync\nNone.\n\n"
                "## Open questions\nNone.\n\n"
                "## Validation and cross-check (verify before reporting done)\n"
                "- [ ] V-01 validates E-01\n"
                "  - Required evidence: diff\n"
                "  - Observed evidence:\n"
                "  - Result: pending\n\n"
                "## Approval and execution gate\nApproved.\n"
            ),
        )
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
    return repo, plan_path


class RunnerPromptWrapperTests(unittest.TestCase):
    def test_both_hosts_register_pre_post_and_prompt_alias_on_start_and_resume(self):
        for name, mod in (("oc", oc_runipd), ("agy", agy_runipd)):
            with self.subTest(host=name):
                parser = mod.build_parser()
                args_post = parser.parse_args(
                    [
                        "start",
                        "all",
                        "--pre-prompt",
                        "Lead instruction",
                        "--post-prompt",
                        "Trail instruction",
                    ]
                )
                self.assertEqual(args_post.pre_prompt, "Lead instruction")
                self.assertEqual(args_post.post_prompt, "Trail instruction")

                args_alias = parser.parse_args(
                    [
                        "start",
                        "all",
                        "--prompt",
                        "Alias trail instruction",
                    ]
                )
                self.assertIsNone(args_alias.pre_prompt)
                self.assertEqual(args_alias.post_prompt, "Alias trail instruction")

                frozen = runner_shared.freeze_run_policy_flags(args_post)
                self.assertEqual(frozen["pre_prompt"], "Lead instruction")
                self.assertEqual(frozen["post_prompt"], "Trail instruction")

                # Resume preserves frozen values when omitted, and updates when passed.
                state = {"options": dict(frozen)}
                res_omitted = parser.parse_args(["resume", "run-123"])
                changed = runner_shared.apply_run_policy_flags_on_resume(
                    state, res_omitted
                )
                self.assertFalse(changed)
                self.assertEqual(state["options"]["pre_prompt"], "Lead instruction")
                self.assertEqual(state["options"]["post_prompt"], "Trail instruction")

                res_override = parser.parse_args(
                    ["resume", "run-123", "--prompt", "Updated trail"]
                )
                changed2 = runner_shared.apply_run_policy_flags_on_resume(
                    state, res_override
                )
                self.assertTrue(changed2)
                self.assertEqual(state["options"]["pre_prompt"], "Lead instruction")
                self.assertEqual(state["options"]["post_prompt"], "Updated trail")

    def test_apply_operator_prompt_wrappers_noop_and_order(self):
        base = "Base task prompt body."
        self.assertEqual(
            runner_shared.apply_operator_prompt_wrappers(base, {"options": {}}),
            base,
        )
        wrapped = runner_shared.apply_operator_prompt_wrappers(
            base,
            {
                "options": {
                    "pre_prompt": "Check edge cases first.",
                    "post_prompt": "Keep diff minimal.",
                }
            },
        )
        self.assertTrue(
            wrapped.startswith(
                "## Operator pre-prompt instructions\n\nCheck edge cases first.\n\nBase task prompt body."
            )
        )
        self.assertTrue(
            wrapped.endswith(
                "\n\n## Operator post-prompt instructions\n\nKeep diff minimal."
            )
        )

    def test_execute_item_wraps_initial_and_fresh_recovery_but_not_verifier_or_session_answer(
        self,
    ):
        with tempfile.TemporaryDirectory() as td:
            repo, plan_path = _init_repo_with_approved_plan(Path(td), "prw001")
            run_dir = repo / ".aw" / "records" / "runs" / "run-test"
            (run_dir / "prompts").mkdir(parents=True)
            (run_dir / "outcomes").mkdir(parents=True)
            (run_dir / "sessions").mkdir(parents=True)

            captured_prompts: list[tuple[str, str]] = []

            def fake_run_agy(
                state,
                rdir,
                item,
                prompt_path,
                attempt_no,
                session_id,
                use_continue,
                log_suffix="",
                **kwargs,
            ):
                p_name = Path(prompt_path).name
                if p_name == "prompt.md":
                    kind = "probe"
                elif "verify" in p_name or kwargs.get("telemetry_phase") == "verify":
                    kind = "verify"
                elif log_suffix:
                    kind = log_suffix
                else:
                    kind = "exec"
                captured_prompts.append(
                    (kind, Path(prompt_path).read_text(encoding="utf-8"))
                )
                if kind == "exec":
                    (repo / "README.md").write_text(
                        f"updated attempt {attempt_no}\n", encoding="utf-8"
                    )
                    out_p = rdir / "outcomes" / f"01-{item['id6']}.json"
                    out_p.write_text(
                        '{"disposition": "incomplete", "summary": "in progress"}\n',
                        encoding="utf-8",
                    )
                log_p = rdir / "sessions" / f"fake-{attempt_no}-{kind}.jsonl"
                log_p.write_text(
                    '{"type":"init","session_id":"sid-1"}\n'
                    '{"type":"result","status":"success"}\n',
                    encoding="utf-8",
                )
                return 0, "sid-1", log_p, ["agy"]

            item = {
                "id6": "prw001",
                "setid": "prwset",
                "position": 1,
                "artifact_type": "ipd",
                "action": "execute",
                "status": "queued",
                "configured_file": str(plan_path.relative_to(repo)),
                "dependencies": [],
                "attempts": [],
            }
            state = {
                "run_id": "run-test",
                "repo": str(repo),
                "queue": [item],
                "options": {
                    "isolate_worktree": False,
                    "verify": True,
                    "self_finalize": False,
                    "pre_prompt": "PRE_GUIDANCE_TOKEN",
                    "post_prompt": "POST_GUIDANCE_TOKEN",
                },
            }

            with (
                mock.patch.object(agy_runipd, "run_agy_turn", side_effect=fake_run_agy),
                mock.patch.object(
                    runner_shared,
                    "reconcile_disposition",
                    return_value=("incomplete", None),
                ),
            ):
                # Attempt 1 (initial)
                agy_runipd.execute_item(run_dir, state, item, recovery=False)
                # Attempt 2 (fresh-session recovery)
                agy_runipd.execute_item(run_dir, state, item, recovery=True)

            exec_prompts = [txt for kind, txt in captured_prompts if kind == "exec"]
            other_prompts = [txt for kind, txt in captured_prompts if kind != "exec"]
            self.assertEqual(len(exec_prompts), 2)
            for txt in exec_prompts:
                self.assertTrue(
                    txt.startswith(
                        "## Operator pre-prompt instructions\n\nPRE_GUIDANCE_TOKEN"
                    )
                )
                self.assertTrue(
                    txt.endswith(
                        "## Operator post-prompt instructions\n\nPOST_GUIDANCE_TOKEN"
                    )
                )
            # Probes, defect-reasks, and independent verifier turns must never carry operator wrappers.
            for txt in other_prompts:
                self.assertNotIn("PRE_GUIDANCE_TOKEN", txt)
                self.assertNotIn("POST_GUIDANCE_TOKEN", txt)
            # Also directly verify build_verifier_prompt is unaffected by state options.
            v_prompt = runner_shared.build_verifier_prompt(
                item, state, run_dir, plan_path, labels=runner_shared.AGY_HOST_LABELS
            )
            self.assertNotIn("PRE_GUIDANCE_TOKEN", v_prompt)
            self.assertNotIn("POST_GUIDANCE_TOKEN", v_prompt)

            # Same-session answer continuation must NOT re-wrap operator instructions.
            captured_prompts.clear()
            item["resume_with_answers"] = True
            item["answers_pending"] = [
                {
                    "id": "q1",
                    "question": "Continue?",
                    "answer": "Yes",
                }
            ]
            with (
                mock.patch.object(agy_runipd, "run_agy_turn", side_effect=fake_run_agy),
                mock.patch.object(
                    runner_shared,
                    "reconcile_disposition",
                    return_value=("incomplete", None),
                ),
            ):
                agy_runipd.execute_item(run_dir, state, item, recovery=True)
            ans_prompts = [txt for kind, txt in captured_prompts if kind == "exec"]
            self.assertEqual(len(ans_prompts), 1)
            self.assertNotIn("PRE_GUIDANCE_TOKEN", ans_prompts[0])
            self.assertNotIn("POST_GUIDANCE_TOKEN", ans_prompts[0])

    def test_expand_host_review_argv_preserves_pre_and_post_prompt_values(self):
        out = cli.expand_host_review_argv(
            ["--pre-prompt", "Check invariants", "--prompt", "Be strict"]
        )
        self.assertEqual(out[0], "reviews")
        self.assertIn("--pre-prompt", out)
        self.assertIn("Check invariants", out)
        self.assertIn("--prompt", out)
        self.assertIn("Be strict", out)
        self.assertEqual(out[-2:], ["--action", "review"])


if __name__ == "__main__":
    unittest.main()
