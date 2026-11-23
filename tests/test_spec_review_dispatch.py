"""Tests for spec review dispatch, disposition, approval gate, and output scoping (artdispatch 2ptgds).

Covers:
- E-07: Dispatch and outcome cases on both hosts (oc and agy):
  (1) Prompt is /spec-review and review_handler is spec-review, while plan review is plan-review.
  (2) Conforming record + setter -> ends reviewed, survives directory move to reviewed/.
  (3) Refusal: unchanged status when agent writes nothing -> ends fail-gate with refusal.
  (4) Refusal: hand-edited status without record -> ends fail-gate with missing attestation refusal.
- E-08: Crash-fix, approval gate, and output scoping cases on both hosts:
  (1) Crash fix (F-6): --full-auto spec review ends reviewed with no DriverError and no auto-approve.
  (2) Approval gate (F-7): reviewed spec sets needs_input: True; item_needs_approval for plans unchanged.
  (3) Scope (F-8): extra writes reported out-of-scope; legacy-named spec committed via allowed_paths.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import (
    agy_runipd,
    cli,
    oc_runipd,
    runner_shared,
)
from agent_workflows.runner_shared import queue_artifact_path
from tests.record_builder import RecordBuilder

_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))


def _set_spec_status(
    spec_path: Path, repo_root: Path, status: str = "reviewed"
) -> None:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            rc = cli.main(
                [
                    "specs",
                    "set",
                    str(spec_path),
                    "--status",
                    status,
                    "--dir",
                    str(repo_root),
                    "--no-commit",
                    "--yes",
                ]
            )
        except SystemExit as exc:
            rc = exc.code
    if rc != 0:
        raise RuntimeError(f"specs set failed with {rc}: {buf.getvalue()}")


def _make_test_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=path, check=True)
    return path


def _patch_host_agent(module, agent_fn):
    if module is oc_runipd:
        return mock.patch.object(oc_runipd, "run_opencode", agent_fn)

    def _agy_wrapper(state, run_dir, item, prompt_path, attempt_no, *args, **kwargs):
        work_dir = kwargs.get("work_dir")
        root = Path(work_dir) if work_dir else Path(state.get("repo", "."))
        plan_path = runner_shared.queue_artifact_path(root, item)
        return agent_fn(
            state, run_dir, item, plan_path, prompt_path, attempt_no, **kwargs
        )

    return mock.patch.object(agy_runipd, "run_agy_turn", _agy_wrapper)


class TestSpecReviewDispatchE07(unittest.TestCase):
    """E-07 Dispatch and outcome cases on both runner hosts."""

    def test_case1_prompt_and_handler_record_spec_and_plan(self):
        """Case (1): to-review spec's prompt is /spec-review and handler is spec-review;
        to-review plan's prompt is /plan-review and handler is plan-review in the same run.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    RecordBuilder(repo).spec(
                        id6="spc001",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    RecordBuilder(repo).plan(
                        id6="pln001",
                        title="Test pln001",
                        when="2026-09-27",
                        set="demo",
                        order=1,
                        status="to-review",
                        scope_paths="README.md",
                        author="tester",
                        priority="medium",
                        work_kind="feature",
                        slug="test-plan",
                        highest_e_allocated="01",
                        history=["- 2026-09-27 to-review (tester): to-review"],
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c1"
                    cmd = [
                        "start",
                        "spc001",
                        "pln001",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                        "--allow-mixed",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    prompts_observed: dict[str, str] = {}

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        first_line = prompt_path.read_text(
                            encoding="utf-8"
                        ).splitlines()[0]
                        prompts_observed[item["id6"]] = first_line
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    queue = state["queue"]
                    by_id = {it["id6"]: it for it in queue}

                    # Assert prompt commands
                    self.assertTrue(
                        prompts_observed["spc001"].startswith("/spec-review "),
                        f"Expected /spec-review for spec, got: {prompts_observed['spc001']}",
                    )
                    self.assertTrue(
                        prompts_observed["pln001"].startswith("/plan-review "),
                        f"Expected /plan-review for plan, got: {prompts_observed['pln001']}",
                    )

                    # Assert review_handler on attempt and item
                    self.assertEqual(by_id["spc001"]["review_handler"], "spec-review")
                    self.assertEqual(
                        by_id["spc001"]["attempts"][0]["review_handler"], "spec-review"
                    )
                    self.assertEqual(by_id["pln001"]["review_handler"], "plan-review")
                    self.assertEqual(
                        by_id["pln001"]["attempts"][0]["review_handler"], "plan-review"
                    )

                    # Assert events carry review_handler
                    events = [
                        json.loads(line)
                        for line in (run_dir / "events.jsonl")
                        .read_text(encoding="utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    start_events = {
                        e["id6"]: e for e in events if e.get("event") == "ipd-started"
                    }
                    self.assertEqual(
                        start_events["spc001"].get("review_handler"), "spec-review"
                    )
                    self.assertEqual(
                        start_events["pln001"].get("review_handler"), "plan-review"
                    )

    def test_case2_advanced_with_conforming_record_and_directory_move(self):
        """Case (2): fake agent writes a conforming review record and runs aw specs set reviewed <id6>.
        Item ends reviewed and spec file is in reviewed/, surviving the directory move.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    spec_path = RecordBuilder(repo).spec(
                        id6="spc002",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c2"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        RecordBuilder(repo).review(
                            subject="spc002",
                            set="s1",
                            order=1,
                            subject_type="spec",
                            reviewed_at="2026-09-27",
                            reviewer="test-agent",
                            verdict="APPROVE",
                        )
                        _set_spec_status(plan_path, repo)
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            rc = mod.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(rc, 0)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "reviewed")

                    # Verify spec file moved from to-review/ to reviewed/
                    self.assertFalse(spec_path.exists())
                    new_path = (
                        repo / ".aw" / "records" / "specs" / "reviewed" / spec_path.name
                    )
                    self.assertTrue(new_path.exists())

                    # Verify discover_specs finds it at the new path
                    resolved = queue_artifact_path(repo, item)
                    self.assertEqual(resolved.resolve(), new_path.resolve())

    def test_case3_refusal_unchanged_status_when_agent_writes_nothing(self):
        """Case (3): fake agent exits 0 and writes nothing.
        Item ends fail-gate, refusal names unchanged status, and spec is still to-review.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    spec_path = RecordBuilder(repo).spec(
                        id6="spc003",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c3"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        # Exit 0 without touching anything
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            rc = mod.run_queue(run_dir, retry_incomplete=False)

                    self.assertNotEqual(rc, 0)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")
                    self.assertTrue(spec_path.exists())

                    refusal = item.get("refusal", {})
                    self.assertEqual(
                        refusal.get("code"), runner_shared.SPEC_REVIEW_REFUSAL_CODE
                    )
                    self.assertIn("to-review", refusal.get("reason", ""))
                    self.assertIn("/spec-review", refusal.get("remedy", ""))

    def test_case4_refusal_missing_attestation_when_status_edited_without_record(self):
        """Case (4): fake agent hand-edits - Status: reviewed without writing a review record.
        Item ends fail-gate naming the missing attestation.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    RecordBuilder(repo).spec(
                        id6="spc004",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c4"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        # Hand-edit status without creating a review record
                        plan_path.write_text(
                            RecordBuilder().spec(
                                id6="spc004",
                                status="reviewed",
                                title="Test Spec",
                                slug="test-spec",
                                when="2026-09-27",
                                author="tester",
                                history=["- 2026-09-27 to-review (tester): set status"],
                                text_only=True,
                            ),
                            encoding="utf-8",
                        )
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            rc = mod.run_queue(run_dir, retry_incomplete=False)

                    self.assertNotEqual(rc, 0)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "fail-gate")

                    refusal = item.get("refusal", {})
                    self.assertEqual(
                        refusal.get("code"), runner_shared.SPEC_REVIEW_REFUSAL_CODE
                    )
                    self.assertIn(
                        "no review record names spc004", refusal.get("reason", "")
                    )
                    self.assertIn("/spec-review", refusal.get("remedy", ""))


class TestSpecReviewApprovalAndScopeE08(unittest.TestCase):
    """E-08 Crash-fix, approval gate, and output scoping cases."""

    def test_crash_fix_full_auto_spec_review(self):
        """F-6: a --full-auto run that reviews a spec to reviewed ends reviewed with NO DriverError
        recorded and no set_plan_approved call; spec is not auto-approved.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    RecordBuilder(repo).spec(
                        id6="spc005",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c5"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                        "--full-auto",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        RecordBuilder(repo).review(
                            subject="spc005",
                            set="s1",
                            order=1,
                            subject_type="spec",
                            reviewed_at="2026-09-27",
                            reviewer="test-agent",
                            verdict="APPROVE",
                        )
                        _set_spec_status(plan_path, repo)
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    mock_set_plan_approved = mock.MagicMock()
                    with (
                        _patch_host_agent(mod, fake_agent),
                        mock.patch.object(
                            mod, "set_plan_approved", mock_set_plan_approved
                        ),
                    ):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            rc = mod.run_queue(run_dir, retry_incomplete=False)

                    self.assertEqual(rc, 0)
                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "reviewed")
                    self.assertNotIn("driver_error", item)
                    self.assertFalse(item.get("auto_approved", False))
                    mock_set_plan_approved.assert_not_called()

    def test_approval_gate_visibility_and_plan_control(self):
        """F-7: reviewed spec's human-approval gate is visible via needs_input on the item;
        item_needs_approval answers for plans are unchanged.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    RecordBuilder(repo).spec(
                        id6="spc006",
                        status="to-review",
                        title="Test Spec",
                        slug="test-spec",
                        when="2026-09-27",
                        author="tester",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c6"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        RecordBuilder(repo).review(
                            subject="spc006",
                            set="s1",
                            order=1,
                            subject_type="spec",
                            reviewed_at="2026-09-27",
                            reviewer="test-agent",
                            verdict="APPROVE",
                        )
                        _set_spec_status(plan_path, repo)
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertTrue(
                        item.get("needs_input"), "Spec should carry needs_input: True"
                    )

        # Control assertions: item_needs_approval for plans is unchanged
        self.assertFalse(runner_shared.item_needs_approval("reviewed", "review"))
        self.assertTrue(runner_shared.item_needs_approval("reviewed", "execute"))
        self.assertFalse(runner_shared.item_needs_approval("approved", "execute"))
        self.assertFalse(runner_shared.item_needs_approval("to-review", "review"))

    def test_output_scoping_extra_write_and_legacy_named_spec(self):
        """F-8: extra file written by agent is out of scope and not committed;
        spec whose filename does not carry its id6 still has its own file committed.
        """
        for host_label, mod in _HOSTS:
            with self.subTest(host=host_label):
                with tempfile.TemporaryDirectory() as td:
                    repo = _make_test_repo(Path(td))
                    # Write legacy-named spec lacking id6 in filename
                    specs_dir = repo / ".aw" / "records" / "specs" / "to-review"
                    specs_dir.mkdir(parents=True, exist_ok=True)
                    spec_path = specs_dir / "20260827-1514-01-test-spec.spec.md"
                    spec_path.write_text(
                        RecordBuilder().spec(
                            id6="4w7d6s",
                            status="to-review",
                            title="Test Spec",
                            slug="test-spec",
                            when="2026-09-27",
                            author="tester",
                            text_only=True,
                        ),
                        encoding="utf-8",
                    )
                    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
                    subprocess.run(
                        ["git", "commit", "-m", "init"], cwd=repo, check=True
                    )

                    run_id = f"run-{host_label}-c7"
                    cmd = [
                        "start",
                        "reviews",
                        "--type",
                        "spec",
                        "--repo",
                        str(repo),
                        "--run-id",
                        run_id,
                        "--no-isolate-worktree",
                    ]
                    args = mod.build_parser().parse_args(cmd)
                    buf = io.StringIO()
                    with (
                        contextlib.redirect_stdout(buf),
                        contextlib.redirect_stderr(buf),
                    ):
                        run_dir = mod.initialize_run(args)

                    extra_path = repo / "extra_unrelated_file.txt"

                    def fake_agent(
                        state, rdir, item, plan_path, prompt_path, attempt_no, **kwargs
                    ):
                        RecordBuilder(repo).review(
                            subject="4w7d6s",
                            set="s1",
                            order=1,
                            subject_type="spec",
                            reviewed_at="2026-09-27",
                            reviewer="test-agent",
                            verdict="APPROVE",
                        )
                        # Advance spec via setter
                        _set_spec_status(plan_path, repo)
                        # Write an extra file
                        extra_path.write_text("extra", encoding="utf-8")
                        return 0, "session", rdir / "log.txt", ["cmd"]

                    with _patch_host_agent(mod, fake_agent):
                        with (
                            contextlib.redirect_stdout(buf),
                            contextlib.redirect_stderr(buf),
                        ):
                            mod.run_queue(run_dir, retry_incomplete=False)

                    state = json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )
                    item = state["queue"][0]
                    self.assertEqual(item["status"], "reviewed")

                    # Extra file is untracked/uncommitted
                    status_res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertIn("?? extra_unrelated_file.txt", status_res.stdout)

                    # Last commit should contain the legacy-named spec and the review record
                    commit_files = subprocess.run(
                        [
                            "git",
                            "diff-tree",
                            "--no-commit-id",
                            "--name-only",
                            "-r",
                            "HEAD",
                        ],
                        cwd=repo,
                        capture_output=True,
                        text=True,
                        check=True,
                    ).stdout.splitlines()

                    # Both the moved spec and review record committed
                    self.assertTrue(
                        any("4w7d6s" in f for f in commit_files),
                        f"Expected review record in commit files, got: {commit_files}",
                    )
                    self.assertTrue(
                        any(spec_path.name in f for f in commit_files),
                        f"Expected legacy-named spec {spec_path.name} in commit files, got: {commit_files}",
                    )
                    self.assertNotIn("extra_unrelated_file.txt", commit_files)
