"""Tests for workflow-artifacts pruning (muza7y).

Verifies the pure planner, reader-safety rules, confinement checks,
CLI routing, preview/apply parity, exit contract, and documentation.
"""

from __future__ import annotations

import datetime
import hashlib
import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import cli
from agent_workflows import command_surface
from agent_workflows import set_records
from agent_workflows import workflow_artifacts_prune as wap


def _hash_tree(root: Path) -> str:
    """Compute deterministic sha256 digest of tree structure and contents."""
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        h.update(rel.encode("utf-8"))
        if path.is_file() and not path.is_symlink():
            try:
                h.update(path.read_bytes())
            except OSError:
                pass
    return h.hexdigest()


class TestWorkflowArtifactsPrune(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.artifacts_root = self.tmp / set_records.RUN_ARTIFACTS_SUBDIR
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.today = datetime.date(2026, 9, 25)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _create_run(
        self,
        workflow: str,
        run_id: str,
        files: dict[str, str] | None = None,
        mtime: float | None = None,
    ) -> Path:
        run_dir = self.artifacts_root / workflow / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if files:
            for fname, content in files.items():
                fpath = run_dir / fname
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(content, encoding="utf-8")
        if mtime is not None:
            os.utime(run_dir, (mtime, mtime))
            for p in run_dir.rglob("*"):
                os.utime(p, (mtime, mtime))
        return run_dir

    def test_keep_last_and_retention(self):
        """Newest keep_last (5) runs kept, older runs beyond 5 deleted if >30d."""
        # 7 dated runs in assess-bugs, all older than 30 days relative to 2026-09-25
        dates = [
            "20260701-01",
            "20260702-02",
            "20260703-03",
            "20260704-04",
            "20260705-05",
            "20260706-06",
            "20260707-07",
        ]
        ipd_file = self.tmp / "dummy.ipd.md"
        ipd_file.write_text("# IPD\n", encoding="utf-8")
        for rid in dates:
            self._create_run(
                "assess-bugs",
                rid,
                {"ipd-link.md": f"- Path: {ipd_file.as_posix()}\n"},
            )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=5,
            older_than_days=30,
            today=self.today,
        )

        entries = [e for e in plan.entries if e.workflow == "assess-bugs"]
        self.assertEqual(len(entries), 7)
        # Newest 5: 20260707, 20260706, 20260705, 20260704, 20260703
        kept_newest = [
            e for e in entries if e.decision == "keep" and e.reason == "newest-N"
        ]
        self.assertEqual(len(kept_newest), 5)
        kept_ids = {e.run_id for e in kept_newest}
        self.assertEqual(
            kept_ids,
            {
                "20260707-07",
                "20260706-06",
                "20260705-05",
                "20260704-04",
                "20260703-03",
            },
        )
        # 2 oldest deleted: 20260702, 20260701
        deleted = [e for e in entries if e.decision == "delete"]
        self.assertEqual(len(deleted), 2)
        deleted_ids = {e.run_id for e in deleted}
        self.assertEqual(deleted_ids, {"20260702-02", "20260701-01"})
        for d in deleted:
            self.assertEqual(d.reason, "aged")

    def test_younger_than_days_kept(self):
        """Runs younger than older_than_days are kept even beyond keep_last."""
        # keep_last=0 so keep_last protects nothing
        self._create_run(
            "young-wf", "20260920-young", {"data.txt": "x"}
        )  # age 5d < 30d
        self._create_run(
            "young-wf", "20260701-old", {"data.txt": "y"}
        )  # age 86d >= 30d

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        wf_entries = {e.run_id: e for e in plan.entries if e.workflow == "young-wf"}
        self.assertEqual(wf_entries["20260920-young"].decision, "keep")
        self.assertEqual(wf_entries["20260920-young"].reason, "younger-than-D")
        self.assertEqual(wf_entries["20260701-old"].decision, "delete")
        self.assertEqual(wf_entries["20260701-old"].reason, "aged")

    def test_undated_run_mtime_fallback(self):
        """Undated run id falls back to newest mtime inside the dir."""
        # 45 days before 2026-09-25: 2026-08-11
        dt_old = datetime.datetime(2026, 8, 11, 12, 0, 0)
        ts_old = dt_old.timestamp()

        # Undated run with old mtime -> treated as aged
        self._create_run(
            "custom-wf", "undated-old-run", {"report.txt": "ok"}, mtime=ts_old
        )

        # Undated run with today mtime -> treated as young
        ts_today = datetime.datetime(2026, 9, 25, 12, 0, 0).timestamp()
        self._create_run(
            "custom-wf", "undated-young-run", {"report.txt": "ok"}, mtime=ts_today
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        wf_entries = {e.run_id: e for e in plan.entries if e.workflow == "custom-wf"}
        self.assertEqual(wf_entries["undated-old-run"].decision, "delete")
        self.assertEqual(wf_entries["undated-old-run"].reason, "aged")
        self.assertEqual(wf_entries["undated-young-run"].decision, "keep")
        self.assertEqual(wf_entries["undated-young-run"].reason, "younger-than-D")

    def test_dated_run_with_today_mtime_is_aged_undated_check(self):
        """A run with id 20260703-... but mtime today is treated as aged (date from id wins)."""
        ts_today = datetime.datetime.now().timestamp()
        self._create_run(
            "custom-wf",
            "20260703-120000",
            {"dummy.txt": "freshly modified file"},
            mtime=ts_today,
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entry = next(e for e in plan.entries if e.run_id == "20260703-120000")
        self.assertEqual(entry.decision, "delete")
        self.assertEqual(entry.reason, "aged")
        self.assertEqual(entry.age_days, 84)

    def test_depth_and_non_dir_skipped(self):
        """Only depth 2 directories are candidates; depth 1 files and symlinks are skipped."""
        # Depth 1 file: README.md
        readme = self.artifacts_root / "README.md"
        readme.write_text("# Workflow artifacts README\n", encoding="utf-8")

        # Depth 1 symlink pointing outside
        ext_dir = self.tmp / "ext_target"
        ext_dir.mkdir(parents=True, exist_ok=True)
        sym_wf = self.artifacts_root / "sym-wf"
        sym_wf.symlink_to(ext_dir)

        # Valid workflow with a symlinked run dir
        wf_dir = self.artifacts_root / "valid-wf"
        wf_dir.mkdir(parents=True, exist_ok=True)
        sym_run = wf_dir / "sym-run"
        sym_run.symlink_to(ext_dir)

        # Valid normal run
        self._create_run("valid-wf", "20260701-valid", {"file.txt": "abc"})

        plan = wap.plan_prune(self.artifacts_root, today=self.today)
        self.assertEqual(len(plan.entries), 1)
        self.assertEqual(plan.entries[0].run_id, "20260701-valid")

    def test_planner_purity_sha256_identical(self):
        """Calling plan_prune on a tree performs zero filesystem writes."""
        self._create_run("wf-1", "20260701-01", {"a.txt": "a"})
        self._create_run("wf-2", "20260702-02", {"b.txt": "b"})
        before_hash = _hash_tree(self.artifacts_root)

        _ = wap.plan_prune(self.artifacts_root, today=self.today)

        after_hash = _hash_tree(self.artifacts_root)
        self.assertEqual(before_hash, after_hash)

    def test_reader_safety_open_questions(self):
        """An aged run with open questions is kept regardless of age or keep_last."""
        # Run with unresolved questions
        self._create_run(
            "generic-wf",
            "20260701-open-q",
            {
                set_records.OPEN_QUESTIONS_FILE: "# Open questions\n\n## Q-1\n- Context: need help\n",
            },
        )
        # Run with resolved (empty marker) questions
        self._create_run(
            "generic-wf",
            "20260701-closed-q",
            {
                set_records.OPEN_QUESTIONS_FILE: "# Open questions\n\n_No unresolved questions._\n",
            },
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entries = {e.run_id: e for e in plan.entries if e.workflow == "generic-wf"}
        self.assertEqual(entries["20260701-open-q"].decision, "keep")
        self.assertEqual(entries["20260701-open-q"].reason, "open-questions")
        self.assertEqual(entries["20260701-closed-q"].decision, "delete")
        self.assertEqual(entries["20260701-closed-q"].reason, "aged")

    def test_reader_safety_pinned(self):
        """A run listed in keep_ids is kept with reason pinned."""
        self._create_run("generic-wf", "20260701-pinned", {"dummy.txt": "x"})

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            keep_ids=["20260701-pinned"],
            today=self.today,
        )
        entry = next(e for e in plan.entries if e.run_id == "20260701-pinned")
        self.assertEqual(entry.decision, "keep")
        self.assertEqual(entry.reason, "pinned")

    def test_reader_safety_assess_unreviewed_decisions(self):
        """An assess-shape run with prose decisions.md and no open-questions.md is kept as unreviewed-decisions."""
        # Unreviewed decisions without resolvable ipd-link.md
        self._create_run(
            "assess",
            "20260701-unreviewed",
            {
                "decisions.md": "# Decisions\n\nOpen question: should we proceed?\n",
            },
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entry = next(e for e in plan.entries if e.run_id == "20260701-unreviewed")
        self.assertEqual(entry.decision, "keep")
        self.assertEqual(entry.reason, "unreviewed-decisions")

    def test_assess_with_resolvable_ipd_link_is_prunable(self):
        """An assess run with resolvable ipd-link.md pointing to existing IPD is prunable."""
        ipd_file = self.tmp / "test-plan.ipd.md"
        ipd_file.write_text("# IPD\n- Id: test01\n", encoding="utf-8")

        self._create_run(
            "assess",
            "20260701-resolved",
            {
                "decisions.md": "# Decisions\nKey decisions\n",
                "ipd-link.md": f"- Path: {ipd_file.as_posix()}\n",
            },
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entry = next(e for e in plan.entries if e.run_id == "20260701-resolved")
        self.assertEqual(entry.decision, "delete")
        self.assertEqual(entry.reason, "aged")

    def test_reader_safety_release_review_unfinished(self):
        """A release-review run missing 12-final-response.md is kept as unfinished-run."""
        # In-progress or aborted run missing 12-final-response.md
        self._create_run(
            "release-review",
            "20260701-in-progress",
            {
                "00-run-metadata.md": "status: aborted-pre-flight\n",
                "08-checkpoints.md": "section 1 complete\n",
            },
        )
        # Completed run having 12-final-response.md
        self._create_run(
            "release-review",
            "20260701-completed",
            {
                "00-run-metadata.md": "status: complete\n",
                "12-final-response.md": "# Final response\nAll checks passed.\n",
            },
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entries = {e.run_id: e for e in plan.entries if e.workflow == "release-review"}
        self.assertEqual(entries["20260701-in-progress"].decision, "keep")
        self.assertEqual(entries["20260701-in-progress"].reason, "unfinished-run")
        self.assertEqual(entries["20260701-completed"].decision, "delete")
        self.assertEqual(entries["20260701-completed"].reason, "aged")

    def test_reader_safety_assess_no_ipd_sole_durable_output(self):
        """An assess run whose ipd-link.md records no IPD was created is kept as sole-durable-output."""
        self._create_run(
            "assess",
            "20260701-no-ipd",
            {
                "report.md": "Assessment report\n",
                "ipd-link.md": "Created: none.\nReason: adequate state.\n",
            },
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )
        entry = next(e for e in plan.entries if e.run_id == "20260701-no-ipd")
        self.assertEqual(entry.decision, "keep")
        self.assertEqual(entry.reason, "sole-durable-output")

    def test_symlink_confinement_sentinel_safe(self):
        """apply_prune does not delete symlink targets or follow symlinks out of root."""
        # Create external target dir with sentinel file
        ext_dir = self.artifacts_root / "external_target"
        ext_dir.mkdir(parents=True, exist_ok=True)
        sentinel = ext_dir / "sentinel.txt"
        sentinel.write_text("precious payload", encoding="utf-8")

        # Create depth-1 README file
        readme = self.artifacts_root / "README.md"
        readme.write_text("depth 1 file\n", encoding="utf-8")

        # Create a workflow dir with a symlink to ext_dir
        wf_dir = self.artifacts_root / "symlink-wf"
        wf_dir.mkdir(parents=True, exist_ok=True)
        sym_run = wf_dir / "symlinked-run"
        sym_run.symlink_to(ext_dir)

        # Normal deletable run
        normal_run = self._create_run("symlink-wf", "20260701-delete", {"f.txt": "del"})

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=0,
            older_than_days=30,
            today=self.today,
        )

        # Verify plan did not include symlink run
        self.assertNotIn("symlinked-run", [e.run_id for e in plan.entries])

        # Even if a malicious/malformed plan entry pointing to the symlink is constructed:
        malicious_entry = wap.PruneEntry(
            workflow="symlink-wf",
            run_id="symlinked-run",
            path=sym_run,
            age_days=100,
            decision="delete",
            reason="aged",
            size_bytes=10,
        )
        plan.entries.append(malicious_entry)

        stderr_buf = io.StringIO()
        with redirect_stderr(stderr_buf):
            deleted = wap.apply_prune(plan)

        # Sentinel file still exists! External dir still exists!
        self.assertTrue(sentinel.is_file())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "precious payload")
        self.assertTrue(ext_dir.is_dir())
        self.assertTrue(readme.is_file())

        # Normal run was deleted
        self.assertIn(normal_run, deleted)
        self.assertFalse(normal_run.exists())

    def test_canonical_tree_e09(self):
        """Unified E-09 fixture containing all specified runs in one tree."""
        ipd_file = self.tmp / "real.ipd.md"
        ipd_file.write_text("# IPD\n", encoding="utf-8")

        # 1. assess-bugs with 7 dated runs (completed with resolvable ipd-link.md)
        for i in range(1, 8):
            self._create_run(
                "assess-bugs",
                f"2026070{i}-bug{i}",
                {"ipd-link.md": f"- Path: {ipd_file.as_posix()}\n"},
            )

        # 2. release-review with 2 runs
        # Completed run (aged)
        self._create_run(
            "release-review",
            "20260701-rr-done",
            {"12-final-response.md": "Final response\n"},
        )
        # Unfinished run (missing completion artifact)
        self._create_run(
            "release-review",
            "20260702-rr-inprog",
            {"00-run-metadata.md": "status: running\n"},
        )

        # 3. one undated run id (old mtime)
        ts_old = datetime.datetime(2026, 7, 1, 12, 0, 0).timestamp()
        self._create_run(
            "custom-wf", "undated-legacy-run", {"file.txt": "old"}, mtime=ts_old
        )

        # 4. README file at depth 1
        readme = self.artifacts_root / "README.md"
        readme.write_text("Depth 1 README\n", encoding="utf-8")

        # 5. symlinked run dir whose target holds a sentinel file
        ext_target = self.artifacts_root / "ext_target_dir"
        ext_target.mkdir(parents=True, exist_ok=True)
        sentinel = ext_target / "sentinel.txt"
        sentinel.write_text("sentinel content\n", encoding="utf-8")
        sym_wf = self.artifacts_root / "sym-wf"
        sym_wf.mkdir(parents=True, exist_ok=True)
        sym_run = sym_wf / "sym-run"
        sym_run.symlink_to(ext_target)

        # 6. one aged run with an unresolved open-questions.md
        self._create_run(
            "exec-wf",
            "20260701-openq",
            {set_records.OPEN_QUESTIONS_FILE: "## Q1\nContext: unresolved\n"},
        )

        # 7. one aged assess run with prose decisions.md and no open-questions.md
        self._create_run(
            "assess",
            "20260701-assess-unrev",
            {"decisions.md": "# Decisions\nOpen questions for user\n"},
        )

        # 8. one aged assess run whose ipd-link.md records no IPD
        self._create_run(
            "assess",
            "20260702-assess-noipd",
            {"ipd-link.md": "Created: none.\nReason: adequate state\n"},
        )

        # Pinned run
        pinned_run_id = (
            "20260701-bug1"  # oldest assess-bugs run, otherwise would delete
        )

        plan = wap.plan_prune(
            self.artifacts_root,
            keep_last=5,
            older_than_days=30,
            keep_ids=[pinned_run_id],
            today=self.today,
        )

        by_id = {e.run_id: e for e in plan.entries}

        # Assert: newest N kept per workflow
        for i in range(3, 8):
            self.assertEqual(by_id[f"2026070{i}-bug{i}"].decision, "keep")
            self.assertEqual(by_id[f"2026070{i}-bug{i}"].reason, "newest-N")
        # 20260702-bug2 is outside newest 5 and >30d -> delete aged
        self.assertEqual(by_id["20260702-bug2"].decision, "delete")
        self.assertEqual(by_id["20260702-bug2"].reason, "aged")

        # Pinned keep
        self.assertEqual(by_id[pinned_run_id].decision, "keep")
        self.assertEqual(by_id[pinned_run_id].reason, "pinned")

        # Reader safety: unfinished-run
        self.assertEqual(by_id["20260702-rr-inprog"].decision, "keep")
        self.assertEqual(by_id["20260702-rr-inprog"].reason, "unfinished-run")

        # Reader safety: open-questions
        self.assertEqual(by_id["20260701-openq"].decision, "keep")
        self.assertEqual(by_id["20260701-openq"].reason, "open-questions")

        # Reader safety: unreviewed-decisions
        self.assertEqual(by_id["20260701-assess-unrev"].decision, "keep")
        self.assertEqual(by_id["20260701-assess-unrev"].reason, "unreviewed-decisions")

        # Reader safety: sole-durable-output
        self.assertEqual(by_id["20260702-assess-noipd"].decision, "keep")
        self.assertEqual(by_id["20260702-assess-noipd"].reason, "sole-durable-output")

        # Undated run falls back to mtime -> aged
        # (It is the only run in custom-wf, so under keep_last=5 it would be kept as newest-N if keep_last applies,
        # but custom-wf has only 1 run, so index is 0 < keep_last=5)
        self.assertEqual(by_id["undated-legacy-run"].decision, "keep")
        self.assertEqual(by_id["undated-legacy-run"].reason, "newest-N")

        # Symlink target and depth 1 file not in plan
        self.assertNotIn("sym-run", by_id)
        self.assertNotIn("README.md", by_id)

        # Apply prune deletes exactly the previewed set
        previewed_deletes = {e.path for e in plan.deletions}
        deleted_paths = set(wap.apply_prune(plan))
        self.assertEqual(previewed_deletes, deleted_paths)

        # Sentinel and README untouched
        self.assertTrue(sentinel.is_file())
        self.assertTrue(ext_target.is_dir())
        self.assertTrue(readme.is_file())


class TestCliSurface(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.artifacts_root = self.tmp / set_records.RUN_ARTIFACTS_SUBDIR
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.today = datetime.date(2026, 9, 25)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _create_run(
        self,
        workflow: str,
        run_id: str,
        files: dict[str, str] | None = None,
    ) -> Path:
        run_dir = self.artifacts_root / workflow / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if files:
            for fname, content in files.items():
                fpath = run_dir / fname
                fpath.parent.mkdir(parents=True, exist_ok=True)
                fpath.write_text(content, encoding="utf-8")
        return run_dir

    def test_cli_preview_byte_identity(self):
        """Preview leaves tree byte-identical."""
        self._create_run("wf", "20260701-old", {"f.txt": "hello"})
        before_hash = _hash_tree(self.artifacts_root)

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            rc = cli.main(["archive", "workflow-artifacts", "--dir", str(self.tmp)])

        self.assertEqual(rc, 0)
        after_hash = _hash_tree(self.artifacts_root)
        self.assertEqual(before_hash, after_hash)

    def test_cli_preview_output_format(self):
        """Preview prints would delete, named keeps with reason, kept count, reclaimable bytes, closing hint."""
        # 1 candidate for deletion (>30d, beyond keep_last=0)
        self._create_run("wf-del", "20260701-aged", {"file.txt": "abcde"})
        # 1 reader safety keep (open questions)
        self._create_run(
            "wf-keep",
            "20260701-questions",
            {set_records.OPEN_QUESTIONS_FILE: "# Questions\n\n## Q1\nUnresolved\n"},
        )

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            rc = cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                ]
            )

        self.assertEqual(rc, 0)
        out = stdout_buf.getvalue()
        self.assertIn("would delete wf-del/20260701-aged", out)
        self.assertIn("aged)", out)
        self.assertIn("keep wf-keep/20260701-questions (open-questions)", out)
        self.assertIn("kept: 1 run(s)", out)
        self.assertIn("reclaimable: 5 bytes", out)
        self.assertIn("preview only; re-run with --apply to delete", out)

    def test_cli_apply_matches_preview(self):
        """Under --apply, deleted lines match preview's would delete lines and candidate is removed."""
        self._create_run("wf-del", "20260701-aged", {"file.txt": "abcde"})
        self._create_run(
            "wf-keep",
            "20260701-questions",
            {set_records.OPEN_QUESTIONS_FILE: "# Questions\n\n## Q1\nUnresolved\n"},
        )

        # Capture preview output
        preview_buf = io.StringIO()
        with redirect_stdout(preview_buf):
            cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                ]
            )
        preview_lines = [
            line
            for line in preview_buf.getvalue().splitlines()
            if line.startswith("would delete")
        ]

        # Capture apply output
        apply_buf = io.StringIO()
        with redirect_stdout(apply_buf):
            rc = cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                    "--apply",
                ]
            )

        self.assertEqual(rc, 0)
        apply_lines = [
            line
            for line in apply_buf.getvalue().splitlines()
            if line.startswith("deleted")
        ]

        # Check exact line match under replacement
        expected_apply = [
            line.replace("would delete", "deleted") for line in preview_lines
        ]
        self.assertEqual(apply_lines, expected_apply)

        # Check filesystem: delete target is gone, keep target remains
        self.assertFalse((self.artifacts_root / "wf-del" / "20260701-aged").exists())
        self.assertTrue(
            (self.artifacts_root / "wf-keep" / "20260701-questions").exists()
        )

    def test_cli_missing_tree_exits_zero(self):
        """A missing tree exits 0 with an empty result."""
        empty_tmp = self.tmp / "no_artifacts_here"
        empty_tmp.mkdir()

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            rc = cli.main(["archive", "workflow-artifacts", "--dir", str(empty_tmp)])

        self.assertEqual(rc, 0)
        out = stdout_buf.getvalue()
        self.assertTrue("no workflow artifacts" in out or "CLEAN" in out)

    def test_cli_repeated_keep_pins_both(self):
        """--keep given twice pins both runs against deletion."""
        self._create_run("wf", "20260701-pin1", {"f.txt": "1"})
        self._create_run("wf", "20260701-pin2", {"f.txt": "2"})

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            rc = cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                    "--keep",
                    "20260701-pin1",
                    "--keep",
                    "20260701-pin2",
                ]
            )

        self.assertEqual(rc, 0)
        out = stdout_buf.getvalue()
        self.assertIn("keep wf/20260701-pin1 (pinned)", out)
        self.assertIn("keep wf/20260701-pin2 (pinned)", out)
        self.assertNotIn("would delete", out)

    def test_cli_default_age_is_30_days(self):
        """Asserting effective age default is 30 days when --age is absent."""
        # Run age: 20 days ago (between 14 and 30 days)
        # In 2026-09-25 context: 20 days ago is 2026-09-05
        today = datetime.date.today()
        d20 = today - datetime.timedelta(days=20)
        rid20 = d20.strftime("%Y%m%d-20d")
        self._create_run("wf", rid20, {"f.txt": "data"})

        # Run with default --age: 20d < 30d -> kept as younger-than-D
        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                ]
            )
        out = stdout_buf.getvalue()
        self.assertNotIn(f"would delete wf/{rid20}", out)

        # Run with explicit --age 14d: 20d >= 14d -> deleted as aged
        stdout_buf2 = io.StringIO()
        with redirect_stdout(stdout_buf2):
            cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--keep-last",
                    "0",
                    "--age",
                    "14d",
                ]
            )
        out2 = stdout_buf2.getvalue()
        self.assertIn(f"would delete wf/{rid20}", out2)

    def test_cli_exit_contract(self):
        """Route exit code is strictly within (0, 2)."""
        # Clean run -> 0
        rc_clean = cli.main(["archive", "workflow-artifacts", "--dir", str(self.tmp)])
        self.assertEqual(rc_clean, 0)

        # Invalid age -> 2
        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            rc_invalid = cli.main(
                [
                    "archive",
                    "workflow-artifacts",
                    "--dir",
                    str(self.tmp),
                    "--age",
                    "not-a-duration",
                ]
            )
        self.assertEqual(rc_invalid, 2)

    def test_cli_archive_all_does_not_touch_workflow_artifacts(self):
        """aw archive all sweeps plans and research, but does not touch workflow-artifacts."""
        self._create_run("wf", "20260701-old", {"f.txt": "untouched"})

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            # archive all with apply should not touch workflow-artifacts
            cli.main(["archive", "all", "--dir", str(self.tmp), "--apply"])

        # Run directory in workflow-artifacts still exists untouched
        self.assertTrue((self.artifacts_root / "wf" / "20260701-old").exists())

    def test_command_surface_declaration(self):
        """Verifies CommandDeclaration for archive has --keep-last in legacy_flags."""
        decl = command_surface.get_declaration("archive")
        self.assertIsNotNone(decl)
        self.assertIn("--keep-last", decl.legacy_flags)
        self.assertIn("--keep", decl.legacy_flags)
        self.assertIn("--apply", decl.legacy_flags)
        self.assertEqual(decl.exit_contract, (0, 2))
