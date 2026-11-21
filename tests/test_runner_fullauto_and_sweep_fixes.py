"""Behavioral regression tests for --full-auto commit cleanliness and review-sweep diff isolation."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent_workflows import agy_runipd, runner_shared


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _init_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (repo / ".aw" / "records" / "reviews").mkdir(parents=True)
    (repo / ".aw" / "records" / "runs").mkdir(parents=True)
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "init")
    return repo


def _valid_ipd(
    id6: str, *, status: str, readiness: str | None = None, deferred_body: str = "None."
) -> str:
    readiness_line = f"- Readiness: {readiness}\n" if readiness else ""
    review_hist = (
        f"- 2026-11-21 /plan-review (test): APPROVE; review record .aw/records/reviews/20261121-sample-01-{id6}-sample.review.md\n"
        if readiness
        else ""
    )
    return (
        f"# IPD: Sample plan {id6}\n\n"
        f"- Date: 2026-11-21\n"
        f"- Kind: child\n"
        f"- Concern: sample\n"
        f"- Scope: `README.md`\n"
        f"- Scope-Paths: README.md, .aw/records/plans/pending/20261121-sample-01-{id6}-sample.ipd.md\n"
        f"- Item-Dependencies: none\n"
        f"- Status: {status}\n"
        f"{readiness_line}"
        f"- Short-Description: Sample plan {id6}\n"
        f"- Work-Kind: bug\n"
        f"- Priority: high\n"
        f"- Set: sample\n"
        f"- Order: 1\n"
        f"- Highest E allocated: 01\n"
        f"- Author: Test\n"
        f"- Id: {id6}\n\n"
        f"## Workflow history\n\n"
        f"{review_hist}"
        f"- 2026-11-21 {status} (Test): ready.\n\n"
        f"## Goal\n\n"
        f"Verify {id6} cleanly.\n\n"
        f"## Detailed Implementation Checklist (TODO)\n\n"
        f"### Task group 1: Update\n\n"
        f"- [ ] E-01 Update README.md\n"
        f"  - Depends on: none\n"
        f"  - Expected outcome: README.md updated.\n"
        f"  - Execution state: pending\n\n"
        f"## Project conventions discovered (Step 0)\n\n"
        f"- Standard repo conventions.\n\n"
        f"## Findings\n\n"
        f"None.\n\n"
        f"## Proposed changes (ordered, validatable)\n\n"
        f"1. Edit README.md.\n\n"
        f"## Deferred / out of scope (with reason)\n\n"
        f"{deferred_body}\n\n"
        f"## Scope check\n\n"
        f"- Over-scope: none.\n"
        f"- Under-scope: none.\n\n"
        f"## Required tests / validation\n\n"
        f"- Run targeted tests.\n\n"
        f"## Spec / documentation sync\n\n"
        f"- N/A: test fixture.\n\n"
        f"## Open questions\n\n"
        f"None.\n\n"
        f"## Validation and cross-check (verify before reporting done)\n\n"
        f"- [ ] V-01 validates E-01\n"
        f"  - Required evidence: Pasted git diff of README.md.\n"
        f"  - Observed evidence:\n"
        f"  - Result: pending\n\n"
        f"## Approval and execution gate\n\n"
        f"- Size assessment: standard\n"
        f"- Cohesion rationale: not required\n\n"
        f"Approve before execution.\n"
    )


class FullAutoAndReviewSweepFixTests(unittest.TestCase):
    def test_set_plan_approved_commits_on_git_repo_leaving_main_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            plan = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261121-sample-01-fa0001-sample.ipd.md"
            )
            plan.write_text(
                _valid_ipd(
                    "fa0001", status="reviewed", readiness="go-pending-approval"
                ),
                encoding="utf-8",
            )
            _git(repo, "add", str(plan.relative_to(repo)))
            _git(repo, "commit", "-m", "add reviewed plan")
            before_head = _git(repo, "rev-parse", "HEAD")

            runner_shared.set_plan_approved(
                repo,
                "fa0001",
                runner_shared.FULL_AUTO_APPROVAL_MESSAGE,
                labels=runner_shared.AGY_HOST_LABELS,
                argv_builder=runner_shared.pinned_module_argv,
                run_checked=agy_runipd.run_checked,
            )

            after_head = _git(repo, "rev-parse", "HEAD")
            self.assertNotEqual(
                after_head,
                before_head,
                "set_plan_approved must commit auto-approved on a Git repo so main does not stay dirty",
            )
            self.assertEqual(
                _git(repo, "status", "--porcelain", "--", str(plan.relative_to(repo))),
                "",
            )
            self.assertEqual(_git(repo, "diff", "--name-only"), "")
            self.assertIn("- Status: auto-approved", plan.read_text(encoding="utf-8"))

    def test_set_plan_approved_uses_no_commit_outside_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            non_git = Path(td) / "plain"
            non_git.mkdir()
            captured: list[list[str]] = []

            def fake_run_checked(
                argv: list[str], cwd: Path | None = None, **kwargs: object
            ) -> str:
                captured.append(list(argv))
                return ""

            runner_shared.set_plan_approved(
                non_git,
                "fa0002",
                runner_shared.FULL_AUTO_APPROVAL_MESSAGE,
                labels=runner_shared.AGY_HOST_LABELS,
                argv_builder=lambda args: ["aw", *args],
                run_checked=fake_run_checked,
            )
            self.assertEqual(len(captured), 1)
            self.assertIn("--no-commit", captured[0])

    def test_review_integration_ignores_unrelated_broken_plan_already_on_main(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _init_repo(Path(td))
            plan_ok = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261121-sample-01-rv0001-sample.ipd.md"
            )
            plan_ok.write_text(
                _valid_ipd("rv0001", status="to-review"), encoding="utf-8"
            )
            _git(repo, "add", str(plan_ok.relative_to(repo)))
            _git(repo, "commit", "-m", "add valid plan rv0001")
            sweep_start_base = _git(repo, "rev-parse", "HEAD")

            # Allocate a shared review-sweep lane at sweep_start_base.
            run_dir = repo / ".aw" / "records" / "runs" / "run-test-sweep"
            run_dir.mkdir(parents=True, exist_ok=True)
            state: dict[str, object] = {"run_id": "run-test-sweep"}
            handle, _ = runner_shared.acquire_review_sweep_lane(
                repo, run_dir, state, save_state=lambda _rd, _st: None
            )
            self.assertEqual(handle.base_commit, sweep_start_base)

            # Simulate an unrelated commit landing on main with an uncarried obligation in another plan.
            plan_bad = (
                repo
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261121-other-01-bad999-other.ipd.md"
            )
            plan_bad.write_text(
                _valid_ipd(
                    "bad999",
                    status="to-review",
                    deferred_body="- Follow-up work with no carrier at all.",
                ),
                encoding="utf-8",
            )
            _git(repo, "add", str(plan_bad.relative_to(repo)))
            _git(
                repo,
                "commit",
                "-m",
                "unrelated main commit with uncarried obligation in bad999",
            )
            new_main_head = _git(repo, "rev-parse", "HEAD")

            # 1. Re-acquiring the shared sweep lane refreshes base_commit to current main.
            refreshed_handle, refresh = runner_shared.acquire_review_sweep_lane(
                repo, run_dir, state, save_state=lambda _rd, _st: None
            )
            self.assertIsNotNone(refresh)
            assert refresh is not None
            self.assertTrue(refresh.refreshed)
            self.assertEqual(refreshed_handle.base_commit, new_main_head)

            # 2. Commit a clean review of rv0001 on the sweep branch, then integrate even if a
            # caller passes a STALE base_commit pointing before bad999 landed on main.
            wt = Path(refreshed_handle.path)
            wt_plan_ok = wt / plan_ok.relative_to(repo)
            wt_plan_ok.write_text(
                _valid_ipd("rv0001", status="reviewed", readiness="go"),
                encoding="utf-8",
            )
            wt_review = (
                wt
                / ".aw"
                / "records"
                / "reviews"
                / "20261121-sample-01-rv0001-sample.review.md"
            )
            wt_review.parent.mkdir(parents=True, exist_ok=True)
            wt_review.write_text(
                "# Review of rv0001\n\nVerdict: APPROVE\n", encoding="utf-8"
            )
            _git(
                wt,
                "add",
                str(plan_ok.relative_to(repo)),
                str(wt_review.relative_to(wt)),
            )
            _git(wt, "commit", "-m", "plan-review: rv0001 reviewed")

            stale_handle = SimpleNamespace(
                lane_id=refreshed_handle.lane_id,
                branch=refreshed_handle.branch,
                path=refreshed_handle.path,
                base_commit=sweep_start_base,
            )
            integrated, reason, kind = agy_runipd.integrate_review_lane_branch(
                repo, stale_handle, "rv0001"
            )
            self.assertTrue(
                integrated,
                f"expected clean review to integrate, got: {kind} / {reason}",
            )
            self.assertEqual(kind, "integrated")
            self.assertIn("- Status: reviewed", plan_ok.read_text(encoding="utf-8"))

            # 3. Conversely, if a review branch ITSELF introduces an uncarried obligation,
            # integration MUST still refuse it.
            wt_plan_bad_self = wt / plan_ok.relative_to(repo)
            wt_plan_bad_self.write_text(
                _valid_ipd(
                    "rv0001",
                    status="reviewed",
                    readiness="go",
                    deferred_body="- Uncarried follow-up introduced by this review itself.",
                ),
                encoding="utf-8",
            )
            _git(wt, "add", str(plan_ok.relative_to(repo)))
            _git(wt, "commit", "-m", "plan-review: introduce uncarried obligation")
            integrated_bad, reason_bad, _kind_bad = (
                agy_runipd.integrate_review_lane_branch(
                    repo, refreshed_handle, "rv0001"
                )
            )
            self.assertFalse(integrated_bad)
            self.assertIn("uncarried obligation", reason_bad)


if __name__ == "__main__":
    unittest.main()
