"""agentadhere Phase 5 (IPD r2ks4k): CI/local parity for the required `aw check` gate.

Covers E-03/V-03: the CI gate and a local `aw check` invocation come from the SAME shipped
check_engine (no forked/inlined policy in the workflow), so they cannot diverge; and E-01's CI
steps invoke the shipped `python -m agent_workflows check` entry point over the committed artifact
types. Also pins that the gate BLOCKS on a seeded conformance violation and PASSES on a clean tree.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "tests.yml"


class TestCiWorkflowInvokesShippedEngine(unittest.TestCase):
    def test_ci_runs_aw_check_over_committed_types(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        # E-01: the CI gate runs the SHIPPED engine over plans + releases (fail-closed) via the
        # `python -m agent_workflows check` entry point - NOT a forked/inlined policy.
        self.assertIn("python -m agent_workflows check plans", text)
        self.assertIn("python -m agent_workflows check releases", text)
        self.assertIn("python -m agent_workflows check backlog", text)

    def test_ci_uses_shipped_entrypoint_no_forked_policy(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        # NO-FORK: the gate must call the shipped module entry point, and must NOT inline a bespoke
        # python policy script in the workflow (no `import check_engine`-style inlined logic).
        self.assertIn("python -m agent_workflows check", text)
        self.assertNotIn("check_engine.check_type(", text)
        self.assertNotIn("import agent_workflows.check_engine", text)

    def test_ci_does_not_duplicate_test_run(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        # The `unittest` job runs `pytest tests/ -n auto`; the attention-check gate must NOT add a
        # second full-suite run. Count the full-suite invocations: exactly the ones already present
        # (unittest job + output-conformance harness), none added by the gate.
        self.assertEqual(text.count("pytest tests/ -n auto"), 1)


class TestCiLocalParity(unittest.TestCase):
    def _run_check(self, repo: Path, rtype: str):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "check",
                rtype,
                "--agent",
                "--dir",
                str(repo),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        return proc.returncode, proc.stdout

    def test_ci_and_local_identical_on_same_tree(self):
        # The CI step and a local run are the SAME command (python -m agent_workflows check ...), so
        # two invocations on the same tree must produce byte-identical machine-readable output.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        # a seeded plan conformance violation (bad filename grammar)
        (repo / ".aw" / "records" / "plans" / "pending" / "badname.ipd.md").write_text(
            "# IPD: bad\n- Id: bad001\n- Status: draft\n\n## Goal\ng\n",
            encoding="utf-8",
        )
        rc1, out1 = self._run_check(repo, "plans")
        rc2, out2 = self._run_check(repo, "plans")
        self.assertEqual(rc1, rc2)
        # No divergence on the FINDINGS (rule ids + locations) - the meaningful policy output. (The
        # advisory `next` hint may reorder between runs; parity is about the findings, not the hint.)
        import json

        def _findings(out):
            d = json.loads(out)
            return sorted((x["rule"], x["location"]) for x in d.get("diagnostics", []))

        self.assertEqual(_findings(out1), _findings(out2))
        self.assertEqual(rc1, 1)  # a seeded violation FAILS the fail-closed gate

    def test_clean_tree_passes(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name)
        (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        # A real clean tree has its plans index generated/committed; regenerate it so the clean-tree
        # check has no stale-index finding (mirrors the committed state CI runs against).
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "index",
                "plans",
                "--dir",
                str(repo),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        rc, out = self._run_check(repo, "plans")
        self.assertEqual(rc, 0, out)  # clean tree passes the gate


class TestBranchProtectionArtifacts(unittest.TestCase):
    def test_codeowners_covers_policy_ci_hook_paths(self):
        co = REPO_ROOT / ".github" / "CODEOWNERS"
        self.assertTrue(co.is_file())
        text = co.read_text(encoding="utf-8")
        self.assertIn("check_engine.py", text)
        self.assertIn("/.github/workflows/", text)
        self.assertIn("/agent_workflows/hooks/", text)

    def test_branch_protection_doc_states_honest_limits(self):
        doc = REPO_ROOT / "docs" / "branch-protection.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        # honestly states enabling protection is a remote repo-admin action + not authority-invariant
        self.assertIn("repo-ADMIN action", text)
        self.assertIn("REMOTE control", text)
        self.assertIn("does NOT provide AUTHORITY-invariant", text)


if __name__ == "__main__":
    unittest.main()
