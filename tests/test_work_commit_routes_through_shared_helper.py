"""Behavioral tests for aw commit routing through the shared offer_commit helper (IPD yfo6z6)."""

from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from agent_workflows import cli
from agent_workflows import git_commit_helper as gch
from tests import support

_PLAN = """# IPD: Demo work plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement for review.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
- Priority: medium
- Work-Kind: chore
- Set: wk
- Order: 1
- Highest E allocated: 01
- Author: tester
- Id: wk0001

## Workflow history
- 2026-08-28 approved (aw set): approved

## Goal
A real goal statement.

## Detailed Implementation Checklist (TODO)

### Task group 1: work
- [ ] E-01 Do a real observable thing.
  - Depends on: none
  - Expected outcome: a real observable result.
  - Execution state: pending

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: a real falsifiable evidence statement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _git_subcommand(argv) -> str | None:
    """Return the git SUBCOMMAND of argv, or None when argv is not a git invocation.

    Skips global flags git accepts before its subcommand (-C <dir>, -c <cfg>, etc.).
    """
    try:
        tokens = [str(token) for token in argv]
    except TypeError:
        tokens = [str(argv)]
    if not tokens:
        return None
    if Path(tokens[0]).name not in ("git", "git.exe"):
        return None
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if not token.startswith("-"):
            return token
        # -C <dir> and -c <cfg> consume the following token.
        if token in ("-C", "-c"):
            index += 2
            continue
        index += 1
    return None


class _GitArgvRecorder:
    """Record spawned subprocess.Popen invocations while delegating to real Popen."""

    def __init__(self) -> None:
        self.argvs: list[list[str]] = []
        self._patch = None

    def __enter__(self):
        real_popen = subprocess.Popen

        def recording_popen(args, *a, **kw):
            if isinstance(args, (str, bytes)):
                self.argvs.append([args if isinstance(args, str) else args.decode()])
            else:
                self.argvs.append([str(token) for token in args])
            return real_popen(args, *a, **kw)

        self._patch = mock.patch.object(subprocess, "Popen", recording_popen)
        self._patch.start()
        return self

    def __exit__(self, *exc) -> None:
        if self._patch is not None:
            self._patch.stop()

    def git_subcommands(self) -> list[str]:
        return [sub for sub in (_git_subcommand(argv) for argv in self.argvs) if sub]


class WorkCommitRoutesThroughSharedHelperTest(unittest.TestCase):
    def setUp(self):
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        self.plan_path = self.plans / "20260828-wk-01-wk0001-demo.ipd.md"
        self.plan_path.write_text(_PLAN, encoding="utf-8")
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "f.py").write_text("print('hello')\n", encoding="utf-8")
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = e.code if isinstance(e.code, int) else 1
        output = out.getvalue() + err.getvalue()
        return rc, output

    def _head(self) -> str:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def test_commit_with_plan_delegates_to_shared_helper(self):
        """aw commit <plan> routes through the shared offer_commit helper with scope posture."""
        (self.root / "src" / "feature.py").write_text(
            "print('plan feature')\n", encoding="utf-8"
        )
        recorded = []
        real_offer = gch.offer_commit

        def spy(repo_root, paths, **kwargs):
            recorded.append((Path(repo_root), list(paths), dict(kwargs)))
            return real_offer(repo_root, paths, **kwargs)

        with mock.patch.object(gch, "offer_commit", spy):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "add feature",
                    "--",
                    "src/feature.py",
                ]
            )

        self.assertEqual(rc, 0, out)
        self.assertEqual(
            len(recorded), 1, f"Expected 1 call to offer_commit, got {len(recorded)}"
        )
        repo_root, paths, kwargs = recorded[0]
        self.assertEqual(repo_root, self.root)
        self.assertEqual(paths, ["src/feature.py"])
        self.assertEqual(kwargs.get("on_unrelated_staged"), "scope")
        show = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(show.stdout.strip(), "src/feature.py")

    def test_commit_no_plan_delegates_to_shared_helper(self):
        """aw commit --no-plan routes through the shared offer_commit helper with scope posture."""
        (self.root / "src" / "feature.py").write_text(
            "print('no-plan feature')\n", encoding="utf-8"
        )
        recorded = []
        real_offer = gch.offer_commit

        def spy(repo_root, paths, **kwargs):
            recorded.append((Path(repo_root), list(paths), dict(kwargs)))
            return real_offer(repo_root, paths, **kwargs)

        with mock.patch.object(gch, "offer_commit", spy):
            rc, out = self._run(
                [
                    "commit",
                    "--no-plan",
                    "-m",
                    "add no-plan feature",
                    "--dir",
                    str(self.root),
                    "--",
                    "src/feature.py",
                ]
            )

        self.assertEqual(rc, 0, out)
        self.assertEqual(
            len(recorded), 1, f"Expected 1 call to offer_commit, got {len(recorded)}"
        )
        repo_root, paths, kwargs = recorded[0]
        self.assertEqual(repo_root, self.root)
        self.assertEqual(paths, ["src/feature.py"])
        self.assertEqual(kwargs.get("on_unrelated_staged"), "scope")
        show = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(show.stdout.strip(), "src/feature.py")

    def test_commit_no_plan_preserves_coworker_staged_path(self):
        """A pre-staged coworker change is absent from HEAD commit and remains staged afterward."""
        (self.root / "coworker.txt").write_text(
            "coworker staged content\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "coworker.txt"], cwd=self.root, check=True)
        (self.root / "src" / "feature.py").write_text(
            "print('feature with coworker')\n", encoding="utf-8"
        )

        rc, out = self._run(
            [
                "commit",
                "--no-plan",
                "-m",
                "add feature",
                "--dir",
                str(self.root),
                "--",
                "src/feature.py",
            ]
        )
        self.assertEqual(rc, 0, out)
        show = (
            subprocess.run(
                ["git", "show", "--name-only", "--format=", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .splitlines()
        )
        self.assertIn("src/feature.py", show)
        self.assertNotIn("coworker.txt", show)

        staged = (
            subprocess.run(
                ["git", "diff", "--name-only", "--cached"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
            .splitlines()
        )
        self.assertIn("coworker.txt", staged)
        self.assertNotIn("src/feature.py", staged)

    def test_commit_holds_no_forked_git_commit_path_of_its_own(self):
        """With the shared helper stubbed to commit nothing, neither plan nor --no-plan mode spawns git commit."""
        stub = gch.CommitOutcome(
            status=gch.STATUS_NOTHING_TO_COMMIT,
            message="stubbed: the shared helper committed nothing",
            staged=[],
            commit=None,
        )

        # Plan-governed mode
        (self.root / "src" / "feature.py").write_text(
            "print('plan fork test')\n", encoding="utf-8"
        )
        head_before = self._head()
        with (
            _GitArgvRecorder() as recorder,
            mock.patch.object(gch, "offer_commit", lambda *a, **k: stub),
        ):
            rc, out = self._run(
                [
                    "commit",
                    "wk0001",
                    "--dir",
                    str(self.root),
                    "-m",
                    "plan fork test",
                    "--",
                    "src/feature.py",
                ]
            )
        self.assertEqual(rc, 1, out)
        commits = [sub for sub in recorder.git_subcommands() if sub == "commit"]
        self.assertEqual(
            commits, [], f"Expected no git commit invocations, found: {commits}"
        )
        self.assertEqual(self._head(), head_before)

        # Plan-less mode
        (self.root / "src" / "feature.py").write_text(
            "print('no-plan fork test')\n", encoding="utf-8"
        )
        head_before = self._head()
        with (
            _GitArgvRecorder() as recorder,
            mock.patch.object(gch, "offer_commit", lambda *a, **k: stub),
        ):
            rc, out = self._run(
                [
                    "commit",
                    "--no-plan",
                    "-m",
                    "no-plan fork test",
                    "--dir",
                    str(self.root),
                    "--",
                    "src/feature.py",
                ]
            )
        self.assertEqual(rc, 1, out)
        commits = [sub for sub in recorder.git_subcommands() if sub == "commit"]
        self.assertEqual(
            commits, [], f"Expected no git commit invocations, found: {commits}"
        )
        self.assertEqual(self._head(), head_before)

    def test_recorder_observes_real_git_commit_sanity(self):
        """Sanity check: the recorder genuinely observes git commit when the real helper is unstubbed."""
        (self.root / "src" / "feature.py").write_text(
            "print('sanity feature')\n", encoding="utf-8"
        )
        with _GitArgvRecorder() as recorder:
            rc, out = self._run(
                [
                    "commit",
                    "--no-plan",
                    "-m",
                    "sanity commit",
                    "--dir",
                    str(self.root),
                    "--",
                    "src/feature.py",
                ]
            )
        self.assertEqual(rc, 0, out)
        commits = [sub for sub in recorder.git_subcommands() if sub == "commit"]
        self.assertTrue(
            len(commits) >= 1,
            f"Expected recorder to observe git commit, but saw: {recorder.git_subcommands()!r}",
        )


if __name__ == "__main__":
    unittest.main()
