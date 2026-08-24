"""Tests for the local pre-commit executed-transition gate (ipdgates Order dulzpy).

The hook (agent_workflows.hooks.executed_transition_gate) refuses a raw (non-finalize) plan->executed
commit: a plan that gains `- Status: executed`/`done` or is `git mv`-ed into executed/ with NO matching
finalize journal in .aw/state/ is REFUSED; finalize's own commit (which leaves a finalize journal at
ready-to-commit) PASSES; prompts/non-plan/ordinary commits are not gated. LOCAL best-effort only.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import ipd_lifecycle as LC
from agent_workflows.hooks import executed_transition_gate as GATE

import tests.test_ipd_lifecycle_cli as LT  # reuse the plan fixtures


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, msg: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=root, check=True)


def _stage(root: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


class PreCommitExecutedGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        (self.root / "agent_workflows").mkdir()
        (self.root / "tests").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_plan(
        self, plan_id: str, scope_paths: str = "grandfathered", name=None
    ) -> Path:
        name = name or f"20260824-demo-01-{plan_id}-demo.ipd.md"
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        p.write_text(
            LT._completed_plan_text(plan_id=plan_id, scope_paths=scope_paths),
            encoding="utf-8",
        )
        return p

    def _executed_dir(self) -> Path:
        d = self.root / ".aw" / "records" / "plans" / "executed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # --- no-op / negative cases ---
    def test_ordinary_commit_no_plan_transition_is_noop(self):
        (self.root / "somefile.txt").write_text("hi\n", encoding="utf-8")
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0)
        self.assertEqual(msgs, [])

    def test_nonterminal_plan_change_not_gated(self):
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        # Edit the plan but keep it pending (no executed).
        p.write_text(p.read_text() + "\n<!-- edit -->\n", encoding="utf-8")
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0, msgs)

    def test_prompt_executed_transition_not_gated(self):
        # A PROMPT gaining executed status must NOT be gated (record_type discriminator).
        pdir = self.root / ".aw" / "records" / "prompts" / "executed"
        pdir.mkdir(parents=True)
        (pdir / "20260824-p-01-pr0mp7-x.prompt.md").write_text(
            "# Prompt\n\n- Status: executed\n- Id: pr0mp7\n\nbody\n", encoding="utf-8"
        )
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0, msgs)

    # --- refusal cases (raw bypass) ---
    def test_hand_edited_status_executed_without_receipt_refused(self):
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan (approved)")
        # Hand-edit status to executed IN PLACE (no move), no finalize journal.
        p.write_text(
            p.read_text().replace("- Status: approved", "- Status: executed"),
            encoding="utf-8",
        )
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("abc123" in m and "aw ipd finalize" in m for m in msgs))

    def test_git_mv_into_executed_without_receipt_refused(self):
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        # git mv the plan into executed/ (status already flipped) with no finalize journal.
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        dest = self._executed_dir() / p.name
        dest.write_text(text, encoding="utf-8")
        p.unlink()
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("moved into executed/" in m for m in msgs))

    def test_finalize_journal_at_ready_to_commit_passes(self):
        # Simulate exactly finalize's own commit state: a plan staged into executed/ WITH a finalize
        # journal at ready-to-commit whose dest matches.
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        dest_rel = ".aw/records/plans/executed/" + p.name
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        (self._executed_dir() / p.name).write_text(text, encoding="utf-8")
        p.unlink()
        # Write a finalize journal like ipd_lifecycle does, at ready-to-commit.
        journal = {
            "schema_version": 1,
            "plan_id": "abc123",
            "original_path": ".aw/records/plans/pending/" + p.name,
            "dest_path": dest_rel,
            "phase": LC.PHASE_READY_TO_COMMIT,
        }
        LC._write_finalize_journal(self.root, journal)
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0, msgs)

    def test_stale_journal_wrong_dest_refused(self):
        # A journal whose dest does NOT match the staged executed path is not evidence for THIS
        # transition (proves the predicate binds to the transitioned file).
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        (self._executed_dir() / p.name).write_text(text, encoding="utf-8")
        p.unlink()
        journal = {
            "schema_version": 1,
            "plan_id": "abc123",
            "dest_path": ".aw/records/plans/executed/SOME-OTHER-plan.ipd.md",
            "phase": LC.PHASE_READY_TO_COMMIT,
        }
        LC._write_finalize_journal(self.root, journal)
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)

    def test_journal_wrong_phase_refused(self):
        # A journal in a non-finalize-transaction phase (e.g. prepared) is not acceptance evidence.
        p = self._write_plan("abc123")
        _commit_all(self.root, "add plan")
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        dest_rel = ".aw/records/plans/executed/" + p.name
        (self._executed_dir() / p.name).write_text(text, encoding="utf-8")
        p.unlink()
        journal = {
            "schema_version": 1,
            "plan_id": "abc123",
            "dest_path": dest_rel,
            "phase": LC.PHASE_PREPARED,
        }
        LC._write_finalize_journal(self.root, journal)
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)

    # --- end-to-end: real begin+finalize passes; grandfathered plan still needs finalize ---
    def test_real_finalize_own_commit_passes_via_installed_hook(self):
        p = self._write_plan("abc123", scope_paths="grandfathered")
        _commit_all(self.root, "init")
        # Install the real hook and run begin+finalize; finalize's own commit must pass.
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "pre-commit").write_text(
            "#!/bin/bash\nexec python3 -m agent_workflows ipd-executed-gate\n",
            encoding="utf-8",
        )
        (hooks_dir / "pre-commit").chmod(0o755)
        LC.begin(self.root, p, "opencode/test", timestamp="t")
        result = LC.finalize(self.root, p, "opencode/test", "dogfood", apply=True)
        self.assertEqual(
            result.exit_code, LC.EXIT_OK, f"{result.message} / {result.findings}"
        )
        self.assertTrue((self._executed_dir() / p.name).is_file())

    def test_grandfathered_plan_without_finalize_is_refused(self):
        # OQ-01 option B: even a grandfathered plan needs to have run finalize (leaving a journal);
        # a raw executed transition of a grandfathered plan with no journal is refused.
        p = self._write_plan("gf1234", scope_paths="grandfathered")
        _commit_all(self.root, "add grandfathered plan")
        text = p.read_text().replace("- Status: approved", "- Status: executed")
        (self._executed_dir() / p.name).write_text(text, encoding="utf-8")
        p.unlink()
        _stage(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
