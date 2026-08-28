"""agentadhere Phase 2 (IPD 8dto0g): atomic workflow primitives aw work/test/commit/finish.

Covers:
  E-01/V-01 - aw work begin: validate (fail closed) + allocate isolated worktree via worktree_lease.
  E-02/V-02 - aw test: capture command/exit/output/env bound to the tree; honest forgeable label.
  E-03/V-03 - aw commit: commit only in-scope paths via git_commit_helper.offer_commit; refuse
              out-of-scope; no add -A / no push.
  E-04/V-04 - aw finish: require bound evidence, non-authoritative transition only (never executed).
"""

from __future__ import annotations

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows import work_cmd


_PLAN = """# IPD: Demo work plan

- Date: 2026-08-28
- Kind: child
- Concern: A real concern statement for review.
- Scope: A real scope statement.
- Scope-Paths: src/, tests/
- Item-Dependencies: none
- Status: approved
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


class WorkPrimitivesTest(unittest.TestCase):
    def setUp(self):
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
        (self.plans / "20260828-wk-01-wk0001-demo.ipd.md").write_text(
            _PLAN, encoding="utf-8"
        )
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        # gitignore the worktrees + state so the throwaway repo does not embed them
        (self.root / ".gitignore").write_text(
            ".aw/worktrees/\n.aw/state/\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=self.root, check=True)

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    # ---- E-01 / V-01: aw work begin ----

    def test_work_begin_validates_and_allocates_worktree(self):
        rc, out = self._run(["work", "begin", "wk0001", "--dir", str(self.root)])
        self.assertEqual(rc, 0, out)
        self.assertIn("allocated worktree", out)
        lease = self.root / ".aw" / "state" / "work" / "wk0001" / "work-lease.json"
        self.assertTrue(lease.is_file(), out)
        data = json.loads(lease.read_text(encoding="utf-8"))
        self.assertEqual(data["plan_id"], "wk0001")
        self.assertIn("worktree_path", data)
        # the worktree really exists
        wt = subprocess.run(
            ["git", "worktree", "list"], cwd=self.root, capture_output=True, text=True
        )
        self.assertIn("wk0001", wt.stdout)

    def test_work_begin_fails_closed_on_findings(self):
        # a badly-named plan triggers check.name-nonconformant -> fail closed, no worktree
        (self.plans / "badname.ipd.md").write_text(
            _PLAN.replace("- Id: wk0001", "- Id: bad001").replace(
                "- Set: wk", "- Set: bad"
            ),
            encoding="utf-8",
        )
        rc, out = self._run(["work", "begin", "bad001", "--dir", str(self.root)])
        self.assertEqual(rc, 1, out)
        self.assertIn("refusing to start", out)
        self.assertIn("check.name-nonconformant", out)
        self.assertFalse(
            (
                self.root / ".aw" / "state" / "work" / "bad001" / "work-lease.json"
            ).exists()
        )

    def test_work_begin_uses_shared_worktree_lease(self):
        # single-worktree-path proof: work_cmd imports and calls worktree_lease.allocate_worktree
        import inspect

        src = inspect.getsource(work_cmd)
        self.assertIn("worktree_lease", src)
        self.assertIn("allocate_worktree", src)

    # ---- E-02 / V-02: aw test ----

    def test_test_captures_passing_evidence(self):
        rc, out = self._run(
            [
                "test",
                "wk0001",
                "--dir",
                str(self.root),
                "--",
                "python",
                "-c",
                "print('hi')",
            ]
        )
        self.assertEqual(rc, 0, out)
        ev = self.root / ".aw" / "state" / "work" / "wk0001" / "test-evidence.json"
        self.assertTrue(ev.is_file())
        rec = json.loads(ev.read_text(encoding="utf-8"))
        self.assertEqual(rec["exit_code"], 0)
        self.assertEqual(rec["command"], ["python", "-c", "print('hi')"])
        self.assertIn("git_tree", rec)
        self.assertIn("git_head", rec)
        self.assertIn("started_at", rec)
        self.assertEqual(rec["assurance"], "local-forgeable")  # honest label

    def test_test_captures_failing_exit_faithfully(self):
        rc, out = self._run(
            [
                "test",
                "wk0001",
                "--dir",
                str(self.root),
                "--",
                "python",
                "-c",
                "import sys;sys.exit(3)",
            ]
        )
        self.assertEqual(rc, 1, out)  # mirrors the command's failure
        rec = json.loads(
            (
                self.root / ".aw" / "state" / "work" / "wk0001" / "test-evidence.json"
            ).read_text()
        )
        self.assertEqual(rec["exit_code"], 3)  # not silently "passed"

    # ---- E-03 / V-03: aw commit ----

    def test_commit_only_in_scope_paths(self):
        (self.root / "src" / "feature.py").write_text("print('x')\n", encoding="utf-8")
        subprocess.run(["git", "add", "src/feature.py"], cwd=self.root, check=True)
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
        self.assertIn("committed", out)
        show = subprocess.run(
            ["git", "show", "--stat", "--format=%s", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertIn("add feature", show.stdout)
        self.assertIn("src/feature.py", show.stdout)
        self.assertNotIn(".ipd.md", show.stdout)  # only the in-scope path

    def test_commit_refuses_out_of_scope_staged(self):
        (self.root / "outofscope.txt").write_text("y\n", encoding="utf-8")
        subprocess.run(["git", "add", "outofscope.txt"], cwd=self.root, check=True)
        (self.root / "src" / "g.py").write_text("print('g')\n", encoding="utf-8")
        head_before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()
        rc, out = self._run(
            ["commit", "wk0001", "--dir", str(self.root), "-m", "g", "--", "src/g.py"]
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("out-of-scope", out)
        self.assertIn("outofscope.txt", out)
        head_after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True
        ).stdout.strip()
        self.assertEqual(head_before, head_after)  # no commit made

    def test_commit_delegates_to_shared_helper(self):
        import inspect

        src = inspect.getsource(work_cmd.run_commit)
        self.assertIn("_gch.offer_commit", src)
        # no forked commit path: run_commit must not shell out to `git commit` itself
        self.assertNotIn('_git(repo_root, ["commit"', src)
        self.assertNotIn("git commit", src)

    # ---- E-04 / V-04: aw finish ----

    def _write_evidence(self, exit_code=0, stale=False):
        ev_dir = self.root / ".aw" / "state" / "work" / "wk0001"
        ev_dir.mkdir(parents=True, exist_ok=True)
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=self.root,
            capture_output=True,
            text=True,
        ).stdout.strip()
        rec = {
            "schema_version": "aw.work-evidence/v1",
            "plan_id": "wk0001",
            "assurance": "local-forgeable",
            "command": ["true"],
            "exit_code": exit_code,
            "git_tree": "0" * 40 if stale else tree,
            "git_head": "x",
        }
        (ev_dir / "test-evidence.json").write_text(json.dumps(rec), encoding="utf-8")

    def test_finish_refuses_executed(self):
        self._write_evidence()
        rc, out = self._run(
            ["finish", "wk0001", "--dir", str(self.root), "--to", "executed"]
        )
        self.assertEqual(rc, 2, out)
        self.assertIn("aw ipd finalize", out)

    def test_finish_refuses_when_evidence_absent(self):
        rc, out = self._run(
            ["finish", "wk0001", "--dir", str(self.root), "--to", "reviewed"]
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("no test evidence", out)
        # status unchanged
        self.assertIn(
            "- Status: approved",
            (self.plans / "20260828-wk-01-wk0001-demo.ipd.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_finish_refuses_stale_tree_evidence(self):
        self._write_evidence(stale=True)
        rc, out = self._run(
            ["finish", "wk0001", "--dir", str(self.root), "--to", "reviewed"]
        )
        self.assertEqual(rc, 1, out)
        self.assertIn("STALE tree", out)

    def test_finish_transitions_non_authoritative_with_evidence(self):
        self._write_evidence()
        rc, out = self._run(
            ["finish", "wk0001", "--dir", str(self.root), "--to", "reviewed"]
        )
        self.assertEqual(rc, 0, out)
        self.assertIn(
            "- Status: reviewed",
            (self.plans / "20260828-wk-01-wk0001-demo.ipd.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_finish_never_pushes_or_tags(self):
        import inspect

        # No git push/tag invocation in run_finish (docstring mentions of "pushes"/"tags" are fine;
        # assert the absence of an actual git push/tag COMMAND).
        src = inspect.getsource(work_cmd.run_finish)
        self.assertNotIn('"push"', src)
        self.assertNotIn('"tag"', src)
        self.assertNotIn("git push", src)
        self.assertNotIn("git tag", src)


if __name__ == "__main__":
    unittest.main()
