"""Tests for the local pre-commit executed-transition gate (ipdgates Order dulzpy).

The hook (agent_workflows.hooks.executed_transition_gate) refuses a raw (non-finalize) plan->executed
commit: a plan that gains `- Status: executed`/`done` or is `git mv`-ed into executed/ with NO matching
finalize journal in .aw/state/ is REFUSED; finalize's own commit (which leaves a finalize journal at
ready-to-commit) PASSES; prompts/non-plan/ordinary commits are not gated. LOCAL best-effort only.

integpath 29wvmj adds the MERGE-AWARE second accepting path and its tests
(`MergeAwareInTreeEvidenceTests` below): during a merge, an incoming-side `lifecycle(<id6>): finalize`
commit is accepted as proof finalize performed the transition, because the journal lives under
gitignored `.aw/state/` and cannot travel with a lane branch. Those tests drive REAL git merges rather
than mocking `MERGE_HEAD`, since the defect being fixed is precisely that real merge state was never read.
"""

from __future__ import annotations

import os
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


class MergeAwareInTreeEvidenceTests(unittest.TestCase):
    """The merge-aware in-tree evidence path (integpath 29wvmj, E-01..E-05).

    Every case here performs a REAL git merge. Nothing mocks `MERGE_HEAD`, because the defect this
    fixes is that real merge state was never consulted, so a mocked fixture would pass against the
    very bug it is meant to detect.
    """

    FINALIZE_SUBJECT = "lifecycle({id6}): finalize {id6} -> executed"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._git("init", "-q", ".")
        self._git("config", "user.email", "t@e.com")
        self._git("config", "user.name", "T")
        (self.root / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")
        self._write_plan_at("pending", "abc123", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "base")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # --- helpers ---
    def _git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(["git", *args], cwd=str(cwd or self.root), check=True)

    def _out(self, *args: str, cwd: Path | None = None) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()

    def _plan_name(self, id6: str) -> str:
        return f"20260824-demo-01-{id6}-demo.ipd.md"

    def _write_plan_at(self, bucket: str, id6: str, status: str = "approved") -> Path:
        d = self.root / ".aw" / "records" / "plans" / bucket
        d.mkdir(parents=True, exist_ok=True)
        p = d / self._plan_name(id6)
        text = LT._completed_plan_text(plan_id=id6, scope_paths="grandfathered")
        if status != "approved":
            text = text.replace("- Status: approved", f"- Status: {status}")
        p.write_text(text, encoding="utf-8")
        return p

    def _make_lane(
        self, id6: str, *, finalize_commit: bool, branch: str | None = None
    ) -> str:
        """A lane branch that carries ``id6`` into executed/; optionally with finalize's own subject."""
        branch = branch or f"lane-{id6}"
        self._git("checkout", "-q", "-b", branch, self.base_branch)
        pending = (
            self.root / ".aw" / "records" / "plans" / "pending" / self._plan_name(id6)
        )
        if not pending.is_file():
            self._write_plan_at("pending", id6, status="approved")
            self._git("add", "-A")
            self._git("commit", "-q", "-m", f"add plan {id6}")
        dest_dir = self.root / ".aw" / "records" / "plans" / "executed"
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._git(
            "mv",
            f".aw/records/plans/pending/{self._plan_name(id6)}",
            f".aw/records/plans/executed/{self._plan_name(id6)}",
        )
        dest = dest_dir / self._plan_name(id6)
        dest.write_text(
            dest.read_text(encoding="utf-8").replace(
                "- Status: approved", "- Status: executed"
            ),
            encoding="utf-8",
        )
        self._git("add", "-A")
        subject = (
            self.FINALIZE_SUBJECT.format(id6=id6)
            if finalize_commit
            else f"records: move {id6} into executed/"
        )
        self._git("commit", "-q", "-m", subject)
        self._git("checkout", "-q", self.base_branch)
        return branch

    def _diverge(self, marker: str) -> None:
        """Make the base branch diverge so a merge cannot fast-forward."""
        (self.root / f"{marker}.txt").write_text(marker, encoding="utf-8")
        self._git("add", f"{marker}.txt")
        self._git("commit", "-q", "-m", f"diverge {marker}")

    def _begin_hand_merge(self, branch: str) -> None:
        """The HAND sequence: `git merge --no-commit`, which leaves MERGE_HEAD for `pre-commit`."""
        subprocess.run(
            ["git", "merge", "--no-ff", "--no-commit", branch],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
        )
        git_dir = Path(self._out("rev-parse", "--absolute-git-dir"))
        self.assertTrue(
            (git_dir / "MERGE_HEAD").is_file(),
            "fixture precondition: the hand merge must leave a real MERGE_HEAD",
        )

    # --- E-01: the detector ---
    def test_detector_returns_incoming_sha_during_merge_and_empty_outside(self):
        self.assertEqual(GATE._merge_incoming_commits(self.root), [])
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        lane_head = self._out("rev-parse", branch)
        self._begin_hand_merge(branch)
        self.assertEqual(GATE._merge_incoming_commits(self.root), [lane_head])

    def test_detector_resolves_git_dir_from_a_worktree_where_dot_git_is_a_file(self):
        # E-01 exists BECAUSE of this case: in a worktree `.git` is a FILE, so a hardcoded
        # `<root>/.git/MERGE_HEAD` would silently never match and the bug would stay live in
        # exactly the lane worktrees this Set is about.
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        lane_head = self._out("rev-parse", branch)
        wt = self.root / "wt"
        self._git("worktree", "add", "-q", "--detach", str(wt), self.base_branch)
        dot_git = wt / ".git"
        self.assertTrue(
            dot_git.is_file(), "fixture precondition: .git must be a FILE here"
        )
        subprocess.run(
            ["git", "merge", "--no-ff", "--no-commit", branch],
            cwd=str(wt),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(GATE._merge_incoming_commits(wt), [lane_head])

    def test_detector_fails_closed_when_no_merge_head(self):
        # Absent MERGE_HEAD means NOT a merge, hence the caller refuses. An unclassifiable state must
        # never be treated as a merge.
        self._make_lane("abc123", finalize_commit=True)
        self.assertEqual(GATE._merge_incoming_commits(self.root), [])

    # --- E-02 / E-03: accept real evidence, keep refusing everything else ---
    def test_merge_with_matching_finalize_commit_passes(self):
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        self._begin_hand_merge(branch)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 0, msgs)

    def test_merge_without_finalize_commit_still_refused(self):
        # V-03 case (c): a merge is NOT a blanket exemption. This is the hand-edit staged inside a
        # merge commit that the gate exists to catch.
        branch = self._make_lane("abc123", finalize_commit=False)
        self._diverge("d1")
        self._begin_hand_merge(branch)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        joined = " ".join(msgs)
        self.assertIn("abc123", joined)
        self.assertIn("lifecycle(abc123): finalize", joined)

    def test_merge_with_finalize_commit_for_a_different_id6_is_refused(self):
        # The evidence is PLAN-BOUND: finalize for plan A must not authorize plan B.
        self._write_plan_at("pending", "other1", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "add other plan")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        branch = self._make_lane("abc123", finalize_commit=False)
        # Put a finalize commit for a DIFFERENT id6 on the same lane.
        self._git("checkout", "-q", branch)
        (self.root / "unrelated.txt").write_text("x", encoding="utf-8")
        self._git("add", "unrelated.txt")
        self._git("commit", "-q", "-m", self.FINALIZE_SUBJECT.format(id6="other1"))
        self._git("checkout", "-q", self.base_branch)
        self._diverge("d1")
        self._begin_hand_merge(branch)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertIn("abc123", " ".join(msgs))

    def test_finalize_commit_already_on_head_is_not_evidence(self):
        # INCOMING-SIDE-ONLY (`HEAD..MERGE_HEAD`): an old finalize commit on HEAD cannot be replayed
        # as evidence for a different plan arriving now.
        self._git(
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            self.FINALIZE_SUBJECT.format(id6="abc123"),
        )
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        branch = self._make_lane("abc123", finalize_commit=False)
        self._diverge("d1")
        self._begin_hand_merge(branch)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1, msgs)

    def test_hand_edit_outside_a_merge_still_refused(self):
        # E-03 case (a), and the message must be the UNCHANGED non-merge wording.
        p = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / self._plan_name("abc123")
        )
        p.write_text(
            p.read_text(encoding="utf-8").replace(
                "- Status: approved", "- Status: executed"
            ),
            encoding="utf-8",
        )
        self._git("add", "-A")
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        joined = " ".join(msgs)
        self.assertIn("NO matching finalize evidence in .aw/state/", joined)
        self.assertNotIn("this merge carries", joined)

    def test_git_mv_outside_a_merge_still_refused(self):
        # E-03 case (b).
        (self.root / ".aw" / "records" / "plans" / "executed").mkdir(
            parents=True, exist_ok=True
        )
        self._git(
            "mv",
            f".aw/records/plans/pending/{self._plan_name('abc123')}",
            f".aw/records/plans/executed/{self._plan_name('abc123')}",
        )
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertIn("moved into executed/", " ".join(msgs))

    def test_plan_without_readable_id_refused_even_during_a_merge(self):
        # E-03 case (d): with no id6 the in-tree predicate has nothing to bind to, so a merge must not
        # rescue it.
        self._git("checkout", "-q", "-b", "lane-noid", self.base_branch)
        dest_dir = self.root / ".aw" / "records" / "plans" / "executed"
        dest_dir.mkdir(parents=True, exist_ok=True)
        self._git(
            "mv",
            f".aw/records/plans/pending/{self._plan_name('abc123')}",
            f".aw/records/plans/executed/{self._plan_name('abc123')}",
        )
        dest = dest_dir / self._plan_name("abc123")
        dest.write_text(
            "\n".join(
                line
                for line in dest.read_text(encoding="utf-8").splitlines()
                if not line.startswith("- Id:")
            )
            + "\n",
            encoding="utf-8",
        )
        self._git("add", "-A")
        self._git("commit", "-q", "-m", self.FINALIZE_SUBJECT.format(id6="abc123"))
        self._git("checkout", "-q", self.base_branch)
        self._diverge("d1")
        self._begin_hand_merge("lane-noid")
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        self.assertIn("no readable", " ".join(msgs))

    # --- E-04: the refusal must be actionable, and must not teach the bypass ---
    def test_merge_case_refusal_is_actionable_and_names_no_bypass(self):
        branch = self._make_lane("abc123", finalize_commit=False)
        self._diverge("d1")
        self._begin_hand_merge(branch)
        rc, msgs = GATE.check(self.root)
        self.assertEqual(rc, 1)
        joined = " ".join(msgs)
        self.assertIn("abc123", joined)
        self.assertIn("lifecycle(abc123): finalize", joined)
        self.assertIn("aw ipd finalize", joined)
        # The refusal must not name the bypass, nor tell the operator to mutate a tree (z2isfg
        # wording discipline; AGENTS.md forbids touching a co-worker's work).
        for forbidden in ("--no-verify", "git stash", "git reset", "git clean"):
            self.assertNotIn(forbidden, joined)

    # --- E-05 end to end through the installed hook, both git stages ---
    def _install_hook(self, *hook_names: str) -> None:
        hooks_dir = Path(self._out("rev-parse", "--absolute-git-dir")) / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        for name in hook_names:
            script = hooks_dir / name
            script.write_text(
                "#!/bin/bash\nexec python3 -m agent_workflows ipd-executed-gate\n",
                encoding="utf-8",
            )
            script.chmod(0o755)

    def _merge(self, *args: str) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        return subprocess.run(
            ["git", "merge", *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_installed_pre_commit_hook_accepts_evidenced_hand_merge(self):
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        self._install_hook("pre-commit")
        self._merge("--no-ff", "--no-commit", branch)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
        proc = subprocess.run(
            ["git", "commit", "-m", "integrate lane"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_installed_pre_merge_commit_hook_gates_an_automated_merge(self):
        # E-06 / V-06: the stage git ACTUALLY runs for an automated merge. Before this, an automated
        # merge carrying a plan into executed/ was not gated at all.
        branch = self._make_lane("abc123", finalize_commit=False)
        self._diverge("d1")
        self._install_hook("pre-merge-commit")
        proc = self._merge("--no-ff", "--no-edit", "-m", "integrate lane", branch)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("abc123", proc.stdout + proc.stderr)

    def test_installed_pre_merge_commit_hook_accepts_evidenced_automated_merge(self):
        branch = self._make_lane("abc123", finalize_commit=True)
        self._diverge("d1")
        self._install_hook("pre-merge-commit")
        proc = self._merge("--no-ff", "--no-edit", "-m", "integrate lane", branch)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_octopus_merge_evidence_is_found_on_every_incoming_side(self):
        # An octopus merge legitimately has several incoming sides, and at pre-merge-commit time git
        # exposes them as several GITHEAD_<sha> variables. Evidence must be searched across all.
        self._write_plan_at("pending", "other1", status="approved")
        self._git("add", "-A")
        self._git("commit", "-q", "-m", "add other plan")
        self.base_branch = self._out("rev-parse", "--abbrev-ref", "HEAD")
        b1 = self._make_lane("abc123", finalize_commit=True)
        b2 = self._make_lane("other1", finalize_commit=True)
        self._diverge("d1")
        self._install_hook("pre-merge-commit")
        proc = self._merge("--no-edit", "-m", "octopus integrate", b1, b2)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class PreCommitConfigStageRegistrationTests(unittest.TestCase):
    """`.pre-commit-config.yaml` must install and register the gate for BOTH git stages (E-06).

    This is a CONFIGURATION assertion only. It is NOT evidence that the stage fires; that is proven by
    the real-merge tests above, which install the hook and run actual merges.
    """

    def setUp(self) -> None:
        self.cfg_path = Path(__file__).resolve().parents[1] / ".pre-commit-config.yaml"
        self.cfg = self.cfg_path.read_text(encoding="utf-8")

    def test_both_hook_types_are_installed_by_default(self):
        import yaml

        data = yaml.safe_load(self.cfg)
        self.assertEqual(
            data.get("default_install_hook_types"), ["pre-commit", "pre-merge-commit"]
        )

    def test_only_the_gate_opts_into_pre_merge_commit(self):
        # default_stages is pinned to pre-commit so installing the second hook type does not also run
        # the content-MUTATING hooks (ruff --fix, whitespace fixers) mid-merge.
        import yaml

        data = yaml.safe_load(self.cfg)
        self.assertEqual(data.get("default_stages"), ["pre-commit"])
        opted_in = [
            hook["id"]
            for repo in data["repos"]
            for hook in repo["hooks"]
            if "pre-merge-commit" in (hook.get("stages") or [])
        ]
        self.assertEqual(opted_in, ["ipd-executed-transition-gate"])


if __name__ == "__main__":
    unittest.main()
