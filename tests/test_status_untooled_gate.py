"""Tests for the commit-scoped untooled-status detector + its local pre-commit gate (proclint 79li67).

The detector (agent_workflows.check_engine.check_status_untooled) is COMMIT-SCOPED: it compares the
STAGED index against HEAD and flags each PLAN whose `- Status:` changed in this commit with NO matching
tool-authored `## Workflow history` transition line for the new status (predicate A - the fingerprint
of a careless hand-edit). The hook (agent_workflows.hooks.status_untooled_gate) wraps the same rule.

Proven here: a hand-edited status flip (no matching line) is FLAGGED; a change made via `aw set`
(matching attributed line present) is CLEAN; an UNCHANGED plan with a historically hand-set status is
NOT examined (commit-scoping, not a tree scan - no grandfathering); a plan moved OUT of executed/ IS
checked; a plan inside executed/ is NOT; a prompt/release (no `## Workflow history`) is not falsely
flagged; an ordinary commit with no plan status change is a fast no-op.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import check_engine as CE
from agent_workflows.hooks import status_untooled_gate as GATE


def _init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root, check=True)
    (root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")


def _commit_all(root: Path, msg: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    # --no-verify: these fixtures deliberately stage hand-edits; we drive the CHECK directly, and do
    # not want the repo's own installed hooks to interfere with fixture setup commits.
    subprocess.run(
        ["git", "commit", "-q", "--no-verify", "-m", msg], cwd=root, check=True
    )


def _stage_all(root: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def _plan_text(
    *,
    plan_id: str = "abc123",
    status: str = "approved",
    history: str = "",
) -> str:
    """A minimal plan IPD carrying `- Status:` + a `## Workflow history` section.

    ``history`` is the block of `- <date> ...` lines placed under the heading (may be empty)."""
    hist = history if history else "- 2026-08-24 draft (opencode): created."
    return (
        f"# IPD: demo\n\n"
        f"- Date: 2026-08-24\n"
        f"- Status: {status}\n"
        f"- Set: demo\n"
        f"- Id: {plan_id}\n\n"
        f"## Workflow history\n{hist}\n\n"
        f"## Goal\n\nx\n"
    )


class UntooledStatusDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _pending_dir(self) -> Path:
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _executed_dir(self) -> Path:
        d = self.root / ".aw" / "records" / "plans" / "executed"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_plan(
        self, plan_id: str, *, status: str = "approved", history: str = ""
    ) -> Path:
        name = f"20260824-demo-01-{plan_id}-demo.ipd.md"
        p = self._pending_dir() / name
        p.write_text(
            _plan_text(plan_id=plan_id, status=status, history=history),
            encoding="utf-8",
        )
        return p

    # --- refusal: careless hand-edit (no matching history line) ---
    def test_hand_edited_status_change_without_history_line_is_flagged(self):
        # Commit an approved plan whose history has NO 'reviewed' line, then hand-flip status to
        # 'reviewed' WITHOUT adding a matching history line -> looks hand-edited.
        p = self._write_plan(
            "abc123",
            status="approved",
            history="- 2026-08-24 approved (aw set): status set to approved",
        )
        _commit_all(self.root, "add plan (approved)")
        p.write_text(
            p.read_text().replace("- Status: approved", "- Status: reviewed"),
            encoding="utf-8",
        )
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(len(drift), 1, drift)
        self.assertEqual(drift[0].rule, "check.status-untooled")
        self.assertIn("reviewed", drift[0].detail)
        self.assertIn("aw set", drift[0].detail)
        # The hook wraps the same rule.
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertTrue(any("aw set" in m for m in msgs))

    def test_new_plan_added_with_status_but_no_matching_history_is_flagged(self):
        # A freshly ADDED plan (no HEAD) whose status has no matching history line is flagged.
        self._write_plan(
            "new123",
            status="approved",
            history="- 2026-08-24 draft (opencode): created.",
        )
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(len(drift), 1, drift)
        self.assertIn("approved", drift[0].detail)

    # --- clean: tooled change (matching attributed history line present) ---
    def test_tooled_status_change_with_matching_history_line_is_clean(self):
        p = self._write_plan(
            "abc123",
            status="approved",
            history="- 2026-08-24 approved (aw set): status set to approved",
        )
        _commit_all(self.root, "add plan (approved)")
        # Simulate what `aw set reviewed` produces: flip status AND append the matching attributed line.
        new_text = p.read_text().replace("- Status: approved", "- Status: reviewed")
        new_text = new_text.replace(
            "## Workflow history\n",
            "## Workflow history\n- 2026-08-24 reviewed (aw set): status set to reviewed\n",
            1,
        )
        p.write_text(new_text, encoding="utf-8")
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0, msgs)

    # --- commit-scoping: unchanged historical record is NOT examined ---
    def test_unchanged_plan_with_historically_handset_status_is_not_examined(self):
        # A plan whose status was hand-set long ago (no matching history line) but is NOT changed in
        # THIS commit must NOT be flagged - proving commit-scoping (no whole-tree scan, no grandfather).
        p = self._write_plan(
            "old999",
            status="approved",
            history="- 2026-08-24 draft (opencode): created.",  # no 'approved' line, but historical
        )
        _commit_all(self.root, "add plan with historically hand-set status")
        # Change something UNRELATED (not the status) in a different file.
        (self.root / "note.txt").write_text("hi\n", encoding="utf-8")
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])
        # Even editing the plan body (but not its status) does not re-examine the old status.
        p.write_text(p.read_text() + "\nmore body\n", encoding="utf-8")
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])

    # --- executed/ exclusion + moved-out-of-executed IS checked ---
    def test_plan_inside_executed_is_not_examined(self):
        # A plan already in executed/ that gains a status change is NOT examined (terminal/immutable;
        # its terminal transition is the dulzpy gate's concern, not this intermediate detector).
        d = self._executed_dir()
        p = d / "20260824-demo-01-exec01-demo.ipd.md"
        p.write_text(_plan_text(plan_id="exec01", status="executed"), encoding="utf-8")
        _commit_all(self.root, "add executed plan")
        p.write_text(
            p.read_text().replace("- Status: executed", "- Status: approved"),
            encoding="utf-8",
        )
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])

    def test_plan_moved_out_of_executed_is_checked(self):
        # A plan moved OUT of executed/ (back to pending, status flipped) IS a staged change with a
        # non-executed new path -> it IS examined, and with no matching history line it is flagged.
        src = self._executed_dir() / "20260824-demo-01-mv1234-demo.ipd.md"
        src.write_text(
            _plan_text(
                plan_id="mv1234",
                status="executed",
                history="- 2026-08-24 executed (aw set): finalized",
            ),
            encoding="utf-8",
        )
        _commit_all(self.root, "add executed plan")
        # git mv it to pending and flip status to approved with NO matching history line.
        dest = self._pending_dir() / src.name
        new_text = src.read_text().replace("- Status: executed", "- Status: approved")
        dest.write_text(new_text, encoding="utf-8")
        src.unlink()
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(len(drift), 1, drift)
        self.assertIn("approved", drift[0].detail)

    # --- history-less types (prompts/releases) are not falsely flagged ---
    def test_prompt_status_change_is_not_examined(self):
        pdir = self.root / ".aw" / "records" / "prompts" / "pending"
        pdir.mkdir(parents=True)
        pp = pdir / "20260824-p-01-pr0mp7-x.prompt.md"
        pp.write_text(
            "# Prompt\n\n- Status: draft\n- Id: pr0mp7\n\nbody\n", encoding="utf-8"
        )
        _commit_all(self.root, "add prompt")
        pp.write_text(
            pp.read_text().replace("- Status: draft", "- Status: approved"),
            encoding="utf-8",
        )
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])

    def test_release_status_change_is_not_examined(self):
        rdir = self.root / ".aw" / "records" / "releases"
        rdir.mkdir(parents=True)
        rp = rdir / "20260824-rel-01-re1234-x.release.md"
        rp.write_text(
            "# Release\n\n- Status: planned\n- Id: re1234\n- Version: next\n",
            encoding="utf-8",
        )
        _commit_all(self.root, "add release")
        rp.write_text(
            rp.read_text().replace("- Status: planned", "- Status: shipped"),
            encoding="utf-8",
        )
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])

    # --- ordinary commit: fast no-op ---
    def test_ordinary_commit_no_plan_status_change_is_noop(self):
        (self.root / "somefile.txt").write_text("hi\n", encoding="utf-8")
        _stage_all(self.root)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0)
        self.assertEqual(msgs, [])
        self.assertEqual(CE.check_status_untooled(self.root), [])

    def test_plan_body_edit_without_status_change_is_clean(self):
        # A plan edited (body only) whose status is unchanged is not flagged even if its history has
        # no line for its current status (the status did not CHANGE in this commit).
        p = self._write_plan(
            "body01",
            status="approved",
            history="- 2026-08-24 approved (aw set): status set to approved",
        )
        _commit_all(self.root, "add plan")
        p.write_text(p.read_text() + "\nextra body\n", encoding="utf-8")
        _stage_all(self.root)
        drift = CE.check_status_untooled(self.root)
        self.assertEqual(drift, [], [d.detail for d in drift])


class UntooledStatusGateEndToEndTests(unittest.TestCase):
    """Prove the installed pre-commit hook actually blocks a raw hand-edited status commit."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _init_git(self.root)
        hooks_dir = self.root / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        (hooks_dir / "pre-commit").write_text(
            "#!/bin/bash\nexec python3 -m agent_workflows ipd-status-untooled-gate\n",
            encoding="utf-8",
        )
        (hooks_dir / "pre-commit").chmod(0o755)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_raw_commit_of_hand_edited_status_is_blocked(self):
        d = self.root / ".aw" / "records" / "plans" / "pending"
        d.mkdir(parents=True, exist_ok=True)
        p = d / "20260824-demo-01-hnd001-demo.ipd.md"
        p.write_text(
            _plan_text(
                plan_id="hnd001",
                status="to-review",
                history="- 2026-08-24 to-review (aw set): created",
            ),
            encoding="utf-8",
        )
        # First commit bypasses the hook (fixture setup with a matching line is clean anyway).
        _commit_all(self.root, "add plan")
        # Hand-edit status to approved with NO matching history line, then a REAL commit (hook runs).
        p.write_text(
            p.read_text().replace("- Status: to-review", "- Status: approved"),
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        proc = subprocess.run(
            ["git", "commit", "-m", "raw status flip"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("aw set", proc.stdout + proc.stderr)
        # The change is left staged (commit refused).
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertTrue(status.stdout.strip())


if __name__ == "__main__":
    unittest.main()
