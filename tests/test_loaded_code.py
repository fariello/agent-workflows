"""Tests for loaded code detection, fingerprinting, and run initialization recording.

Validates the contracts of agent_workflows/loaded_code.py and its integration
with runner_shared.initialize_run_core (runfresh Order 02, `34zv7d`).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import loaded_code, runner_shared


class FingerprintBehavioralTests(unittest.TestCase):
    """Behavioral tests for fingerprint stability and sensitivity (E-01)."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        self.subpkg_dir = self.pkg_dir / "hooks"
        self.subpkg_dir.mkdir(parents=True, exist_ok=True)

        (self.pkg_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
        (self.pkg_dir / "core.py").write_text("a = 1\n", encoding="utf-8")
        (self.subpkg_dir / "hook1.py").write_text("b = 2\n", encoding="utf-8")
        (self.pkg_dir / "README.md").write_text("# Documentation\n", encoding="utf-8")

        self.pycache = self.pkg_dir / "__pycache__"
        self.pycache.mkdir(parents=True, exist_ok=True)
        (self.pycache / "core.cpython-314.pyc").write_bytes(b"\x01\x02\x03\x04")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp.cleanup()

    def test_fingerprint_stability_unchanged_repeat_call(self) -> None:
        """Repeat calls on an unchanged tree return the identical fingerprint."""
        fp1 = loaded_code.fingerprint(self.root)
        fp2 = loaded_code.fingerprint(self.root)
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)

    def test_fingerprint_sensitivity_top_level_py_change(self) -> None:
        """Modifying a top-level .py file changes the fingerprint."""
        fp_before = loaded_code.fingerprint(self.root)
        (self.pkg_dir / "core.py").write_text("a = 42\n", encoding="utf-8")
        fp_after = loaded_code.fingerprint(self.root)
        self.assertNotEqual(fp_before, fp_after)

    def test_fingerprint_sensitivity_subpackage_py_change(self) -> None:
        """Modifying a .py file in a subpackage changes the fingerprint."""
        fp_before = loaded_code.fingerprint(self.root)
        (self.subpkg_dir / "hook1.py").write_text("b = 99\n", encoding="utf-8")
        fp_after = loaded_code.fingerprint(self.root)
        self.assertNotEqual(fp_before, fp_after)

    def test_fingerprint_insensitivity_non_py_files(self) -> None:
        """Modifying non-.py files (markdown, text) does not alter the fingerprint."""
        fp_before = loaded_code.fingerprint(self.root)
        (self.pkg_dir / "README.md").write_text(
            "# Updated Documentation\n", encoding="utf-8"
        )
        (self.pkg_dir / "notes.txt").write_text("arbitrary notes\n", encoding="utf-8")
        fp_after = loaded_code.fingerprint(self.root)
        self.assertEqual(fp_before, fp_after)

    def test_fingerprint_insensitivity_pycache(self) -> None:
        """Modifying or adding bytecode files in __pycache__ does not alter the fingerprint."""
        fp_before = loaded_code.fingerprint(self.root)
        (self.pycache / "core.cpython-314.pyc").write_bytes(b"\xff\xfe\xfd\xfc")
        (self.pycache / "extra.pyc").write_bytes(b"\xaa\xbb\xcc")
        fp_after = loaded_code.fingerprint(self.root)
        self.assertEqual(fp_before, fp_after)


class LoadedCodeRecordTests(unittest.TestCase):
    """Behavioral tests for loaded_code_record memoization and target check (E-01)."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "core.py").write_text("a = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp.cleanup()

    def test_first_call_memoization_across_file_edit(self) -> None:
        """loaded_code_record memoizes the initial fingerprint across subsequent edits."""
        rec1 = loaded_code.loaded_code_record(self.root, package_root=self.root)
        self.assertEqual(rec1["package_root"], str(self.root.resolve()))
        self.assertTrue(rec1["is_target_checkout"])
        self.assertIn("recorded_at", rec1)

        # Mutate the file on disk
        (self.pkg_dir / "core.py").write_text("a = 1000\n", encoding="utf-8")

        # Second call returns the memoized fingerprint from process start
        rec2 = loaded_code.loaded_code_record(self.root, package_root=self.root)
        self.assertEqual(rec2["fingerprint"], rec1["fingerprint"])
        self.assertEqual(rec2["recorded_at"], rec1["recorded_at"])
        self.assertEqual(rec2["package_root"], rec1["package_root"])

    def test_per_call_is_target_checkout(self) -> None:
        """is_target_checkout is re-evaluated per call against the repo argument."""
        rec_target = loaded_code.loaded_code_record(self.root, package_root=self.root)
        self.assertTrue(rec_target["is_target_checkout"])

        other_repo = Path(self.tmp.name) / "other_repo"
        other_repo.mkdir()
        rec_non_target = loaded_code.loaded_code_record(
            other_repo, package_root=self.root
        )
        self.assertFalse(rec_non_target["is_target_checkout"])

        rec_none = loaded_code.loaded_code_record(None, package_root=self.root)
        self.assertFalse(rec_none["is_target_checkout"])


class CodeChangedTests(unittest.TestCase):
    """Behavioral tests for code_changed detection (E-02)."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pkg_dir = self.root / "agent_workflows"
        self.pkg_dir.mkdir(parents=True, exist_ok=True)
        (self.pkg_dir / "core.py").write_text("a = 1\n", encoding="utf-8")

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self.tmp.cleanup()

    def test_code_changed_first_call_when_no_memo(self) -> None:
        """First call with no memoized record establishes baseline and returns changed=False."""
        change = loaded_code.code_changed(self.root, package_root=self.root)
        self.assertFalse(change.changed)
        self.assertEqual(change.old, change.new)
        self.assertTrue(change.restartable)
        self.assertEqual(change.changed_files, [])

    def test_code_changed_no_edit(self) -> None:
        """code_changed reports changed=False when on-disk files are untouched."""
        loaded_code.loaded_code_record(self.root, package_root=self.root)
        change = loaded_code.code_changed(self.root, package_root=self.root)
        self.assertFalse(change.changed)
        self.assertEqual(change.old, change.new)
        self.assertTrue(change.restartable)
        self.assertEqual(change.changed_files, [])

    def test_code_changed_with_file_edit_names_changed_file(self) -> None:
        """code_changed reports changed=True and names the modified file in changed_files."""
        rec = loaded_code.loaded_code_record(self.root, package_root=self.root)
        (self.pkg_dir / "core.py").write_text("a = 9999\n", encoding="utf-8")

        change = loaded_code.code_changed(self.root, package_root=self.root)
        self.assertTrue(change.changed)
        self.assertEqual(change.old, rec["fingerprint"])
        self.assertNotEqual(change.new, change.old)
        self.assertTrue(change.restartable)
        self.assertEqual(change.changed_files, ["agent_workflows/core.py"])

    def test_code_changed_non_target_root_not_restartable(self) -> None:
        """When repo differs from package root, restartable is False."""
        other_repo = Path(self.tmp.name) / "other_repo"
        other_repo.mkdir()
        loaded_code.loaded_code_record(other_repo, package_root=self.root)

        change = loaded_code.code_changed(other_repo, package_root=self.root)
        self.assertFalse(change.restartable)


class InitializeRunLoadedCodeTests(unittest.TestCase):
    """Integration test asserting initialize_run_core records loaded_code and event (E-03, E-04)."""

    def setUp(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

        # Initialize mini git repo
        for cmd in (
            ["git", "init", "-q"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=self.root, check=True)

        pending = self.root / ".aw" / "records" / "plans" / "pending"
        pending.mkdir(parents=True, exist_ok=True)
        from tests.test_oc_runipd import _CONFORMING_PLAN

        (pending / "20260924-test-01-tst001-test.ipd.md").write_text(
            _CONFORMING_PLAN.format(id6="tst001"),
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        loaded_code._reset_for_tests()
        self._tmp.cleanup()

    def test_initialize_run_records_loaded_code_and_event(self) -> None:
        """initialize_run_core records loaded_code in driver state and driver-restart-unavailable event."""
        args = argparse.Namespace(
            repo=str(self.root),
            selectors=["all"],
            full_auto=False,
            output_mode="clean",
            verbosity=0,
            stall_timeout=600.0,
            session=None,
            self_finalize=True,
            isolate_worktree=True,
            max_items_per_session=4,
            prepare_only=True,
            action=None,
            run_id="run-20261006T000000Z-999999",
            manifest=None,
            runbook=None,
            types=None,
            allow_mixed=False,
            allow_drafts=False,
            allow_unverifiable=False,
            allow_dirty_base=False,
            allow_concurrent_driver=False,
            allow_uncovered_orchestrator_work=False,
            retry_budget=None,
            integration_retry_limit=None,
            on_integration_blocked=None,
        )

        from tests.test_hostdedup_third_host import SCRIPTED_HOST_LABELS

        run_dir = runner_shared.initialize_run_core(
            args,
            host="scripted",
            driver_path=None,
            host_options={"mock": True},
            labels=SCRIPTED_HOST_LABELS,
            expand_selectors_fn=lambda manifest, selectors, **kw: ["tst001"],
            enforce_dependency_preflight_fn=lambda *a, **kw: None,
            announce_run_order_fn=lambda rdir, st: None,
            run_order_rationale_fn=lambda queue, sel: "test rationale",
            write_report_fn=lambda rdir, st: None,
        )

        self.assertTrue(run_dir.exists())
        state = runner_shared.load_state(run_dir)
        driver = state["driver"]
        self.assertIn("loaded_code", driver)
        self.assertIsInstance(driver["loaded_code"], list)
        self.assertEqual(len(driver["loaded_code"]), 1)

        rec = driver["loaded_code"][0]
        self.assertIn("package_root", rec)
        self.assertIn("fingerprint", rec)
        self.assertIn("recorded_at", rec)
        self.assertIn("is_target_checkout", rec)
        # Fixture repo in /tmp is NOT the running package root, so is_target_checkout must be False
        self.assertFalse(rec["is_target_checkout"])

        # Check events.jsonl
        events_path = run_dir / "events.jsonl"
        self.assertTrue(events_path.is_file())
        events = [
            json.loads(line)
            for line in events_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        unavailable_events = [
            e for e in events if e.get("event") == "driver-restart-unavailable"
        ]
        self.assertEqual(len(unavailable_events), 1)
        ev = unavailable_events[0]
        self.assertEqual(ev["package_root"], rec["package_root"])
        self.assertEqual(ev["repo"], str(self.root.resolve()))
