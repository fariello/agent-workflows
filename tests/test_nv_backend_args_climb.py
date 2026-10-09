"""Regression test suite for noun-verb backend args climb (IPD dirsilent-05 pua92o).

Pins:
- Subprocess execution with isolated HOME and lane PYTHONPATH.
- Fixtures seeded with --records-backend repository, real plan, real research record.
- Bare-cwd climb for index plans/research --check and preview group/rename/archive.
- Byte-and-mtime snapshot proving preview writes nothing to .aw/records/.
- Explicit --dir does not climb.
- Non-project invocation behaves as expected.
- Agent record schema validity and leak-free paths.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_workflows.agent_schema import validate_agent_record
from agent_workflows import engine, versioning

_PLAN_CONTENT = """# IPD: Test Plan

- Date: 2026-10-01
- Id: p00001
- Status: pending
- Priority: high
- Work-Kind: bug
- Set: testset

## Details
Plan details.
"""

_PLAN_SECOND_CONTENT = """# IPD: Second Plan

- Date: 2026-10-01
- Id: p00002
- Status: pending
- Priority: high
- Work-Kind: bug
- Set: testset

## Details
Second plan details.
"""

_PLAN_DONE_CONTENT = """# IPD: Done Plan

- Date: 2026-10-01
- Id: p00003
- Status: executed
- Priority: high
- Work-Kind: bug
- Set: testset

## Details
Done plan details.
"""


def _snapshot_tree(root: Path) -> dict[str, tuple[bytes, int, int]]:
    records_dir = root / ".aw" / "records"
    snapshot: dict[str, tuple[bytes, int, int]] = {}
    if not records_dir.exists():
        return snapshot
    for p in sorted(records_dir.rglob("*")):
        if p.is_file():
            st = p.stat()
            rel = p.relative_to(root).as_posix()
            snapshot[rel] = (p.read_bytes(), st.st_mtime_ns, st.st_size)
    return snapshot


class NvBackendArgsClimbTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.fix_root = Path(self.td.name).resolve()

        self.fakehome = self.fix_root / "fakehome"
        self.fakehome.mkdir()

        self.proj_root = self.fix_root / "real_project"
        self.proj_root.mkdir()
        subprocess.run(
            ["git", "init", str(self.proj_root)],
            check=True,
            capture_output=True,
        )

        pkg_version = versioning.resolve_version(engine.resolve_source_root(None))
        self.pkg_version = pkg_version

        (self.proj_root / ".aw" / "system").mkdir(parents=True)
        (self.proj_root / ".aw" / "system" / "VERSION").write_text(
            pkg_version + "\n", encoding="utf-8"
        )
        (self.proj_root / ".aw" / "config").mkdir(parents=True)
        (self.proj_root / ".aw" / "config" / "project.json").write_text(
            json.dumps(
                {
                    "preset": "private-target",
                    "records_backend": "repository",
                    "delivery_mode": "tracked",
                }
            ),
            encoding="utf-8",
        )

        self.deep_subdir = self.proj_root / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

        self.outside_cwd = self.fix_root / "outside"
        self.outside_cwd.mkdir()

        self.repo_root = Path(__file__).resolve().parents[1]
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(self.repo_root)
        self.env["AW_NO_REEXEC"] = "1"
        self.env["HOME"] = str(self.fakehome)

        # Seed research records with a nonzero observable (stale index)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "docone",
                "--apply",
            ],
            cwd=self.proj_root,
            env=self.env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [sys.executable, "-m", "agent_workflows", "index", "research"],
            cwd=self.proj_root,
            env=self.env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "research",
                "new",
                "--kind",
                "findings",
                "--slug",
                "doctwo",
                "--apply",
            ],
            cwd=self.proj_root,
            env=self.env,
            check=True,
            capture_output=True,
        )

        # Seed plan records with a nonzero observable (stale index)
        plans_pending = self.proj_root / ".aw" / "records" / "plans" / "pending"
        plans_pending.mkdir(parents=True)
        (plans_pending / "20261001-testset-01-p00001-plan.ipd.md").write_text(
            _PLAN_CONTENT, encoding="utf-8"
        )
        subprocess.run(
            [sys.executable, "-m", "agent_workflows", "index", "plans"],
            cwd=self.proj_root,
            env=self.env,
            check=True,
            capture_output=True,
        )
        (plans_pending / "20261001-testset-02-p00002-plan.ipd.md").write_text(
            _PLAN_SECOND_CONTENT, encoding="utf-8"
        )

        # Executed plan for archive
        plans_executed = self.proj_root / ".aw" / "records" / "plans" / "executed"
        plans_executed.mkdir(parents=True)
        (plans_executed / "20261001-testset-03-p00003-done.ipd.md").write_text(
            _PLAN_DONE_CONTENT, encoding="utf-8"
        )

    def tearDown(self):
        self.td.cleanup()

    def _run_cli(
        self, *args: str, cwd: Path | None = None, env: dict | None = None
    ) -> subprocess.CompletedProcess:
        run_cwd = cwd if cwd is not None else self.outside_cwd
        run_env = env if env is not None else self.env
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args],
            cwd=run_cwd,
            env=run_env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _parse_and_validate_agent_record(
        self, stdout: str, allowed_paths: tuple[Path, ...] = ()
    ) -> dict:
        forbidden_paths = [
            str(self.proj_root),
            str(self.deep_subdir),
            str(self.fix_root),
            str(self.fakehome),
        ]
        for p in forbidden_paths:
            if not any(str(p).startswith(str(allowed)) for allowed in allowed_paths):
                self.assertNotIn(
                    p,
                    stdout,
                    f"Forbidden path {p} leaked into agent stdout:\n{stdout}",
                )

        record = None
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("schema") == "aw.agent/v1":
                record = data
                break

        self.assertIsNotNone(
            record, f"No aw.agent/v1 record found in stdout:\n{stdout}"
        )
        findings = validate_agent_record(record)
        self.assertEqual(
            findings,
            [],
            f"Agent record failed schema validation: {findings}\nRecord: {record}",
        )
        return record

    def test_assertion_a_bare_index_check_climb(self):
        """Bare index plans --check and index research --check climb from deep."""
        # Plans index check agent mode
        proc_plans_deep = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.deep_subdir
        )
        proc_plans_root = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.proj_root
        )
        rec_plans_deep = self._parse_and_validate_agent_record(proc_plans_deep.stdout)
        rec_plans_root = self._parse_and_validate_agent_record(proc_plans_root.stdout)
        self.assertEqual(proc_plans_deep.returncode, proc_plans_root.returncode)
        self.assertEqual(rec_plans_deep["outcome"], rec_plans_root["outcome"])
        self.assertEqual(rec_plans_deep["exit"], rec_plans_root["exit"])
        self.assertEqual(rec_plans_deep["findings"], rec_plans_root["findings"])
        self.assertGreater(rec_plans_root["findings"], 0)

        # Plans index check human mode
        proc_plans_deep_h = self._run_cli(
            "index", "plans", "--check", cwd=self.deep_subdir
        )
        proc_plans_root_h = self._run_cli(
            "index", "plans", "--check", cwd=self.proj_root
        )
        self.assertEqual(proc_plans_deep_h.returncode, proc_plans_root_h.returncode)
        self.assertEqual(proc_plans_deep_h.stdout, proc_plans_root_h.stdout)

        # Research index check agent mode
        proc_rsch_deep = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.deep_subdir
        )
        proc_rsch_root = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.proj_root
        )
        rec_rsch_deep = self._parse_and_validate_agent_record(proc_rsch_deep.stdout)
        rec_rsch_root = self._parse_and_validate_agent_record(proc_rsch_root.stdout)
        self.assertEqual(proc_rsch_deep.returncode, proc_rsch_root.returncode)
        self.assertEqual(rec_rsch_deep["outcome"], rec_rsch_root["outcome"])
        self.assertEqual(rec_rsch_deep["exit"], rec_rsch_root["exit"])
        self.assertEqual(rec_rsch_deep["findings"], rec_rsch_root["findings"])
        self.assertGreater(rec_rsch_root["findings"], 0)

        # Research index check human mode
        proc_rsch_deep_h = self._run_cli(
            "index", "research", "--check", cwd=self.deep_subdir
        )
        proc_rsch_root_h = self._run_cli(
            "index", "research", "--check", cwd=self.proj_root
        )
        self.assertEqual(proc_rsch_deep_h.returncode, proc_rsch_root_h.returncode)
        self.assertEqual(proc_rsch_deep_h.stdout, proc_rsch_root_h.stdout)

    def test_assertion_b_preview_write_verbs_propose_and_write_nothing(self):
        """Bare group, rename, archive preview from deep proposes same paths and writes nothing."""
        # Group plans preview
        snap_before_group = _snapshot_tree(self.proj_root)
        proc_group_deep = self._run_cli(
            "group", "plans", "p00001", "--set", "newset", cwd=self.deep_subdir
        )
        proc_group_root = self._run_cli(
            "group", "plans", "p00001", "--set", "newset", cwd=self.proj_root
        )
        self.assertEqual(proc_group_deep.returncode, 0)
        self.assertEqual(proc_group_root.returncode, 0)
        self.assertEqual(proc_group_deep.stdout, proc_group_root.stdout)
        self.assertIn("20261001-testset-01-p00001-plan.ipd.md", proc_group_deep.stdout)
        snap_after_group = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_group, snap_after_group)

        # Rename plans preview
        snap_before_rename = _snapshot_tree(self.proj_root)
        proc_rename_deep = self._run_cli(
            "rename", "plans", "p00001", "--slug", "newslug", cwd=self.deep_subdir
        )
        proc_rename_root = self._run_cli(
            "rename", "plans", "p00001", "--slug", "newslug", cwd=self.proj_root
        )
        self.assertEqual(proc_rename_deep.returncode, 0)
        self.assertEqual(proc_rename_root.returncode, 0)
        self.assertEqual(proc_rename_deep.stdout, proc_rename_root.stdout)
        self.assertIn(
            "20261001-testset-01-p00001-newslug.ipd.md", proc_rename_deep.stdout
        )
        snap_after_rename = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_rename, snap_after_rename)

        # Archive plans preview
        snap_before_archive = _snapshot_tree(self.proj_root)
        proc_archive_deep = self._run_cli(
            "archive", "plans", "p00003", cwd=self.deep_subdir
        )
        proc_archive_root = self._run_cli(
            "archive", "plans", "p00003", cwd=self.proj_root
        )
        self.assertEqual(proc_archive_deep.returncode, 0)
        self.assertEqual(proc_archive_root.returncode, 0)
        self.assertEqual(proc_archive_deep.stdout, proc_archive_root.stdout)
        self.assertIn(
            "20261001-testset-03-p00003-done.ipd.md", proc_archive_deep.stdout
        )
        snap_after_archive = _snapshot_tree(self.proj_root)
        self.assertEqual(snap_before_archive, snap_after_archive)

    def test_assertion_c_explicit_dir_does_not_climb(self):
        """Explicit --dir <deep> does not climb and result differs from root."""
        # Index plans explicit dir
        proc_plans_exp = self._run_cli(
            "index",
            "plans",
            "--check",
            "--agent",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        rec_plans_exp = self._parse_and_validate_agent_record(proc_plans_exp.stdout)
        proc_plans_root = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.proj_root
        )
        rec_plans_root = self._parse_and_validate_agent_record(proc_plans_root.stdout)
        self.assertNotEqual(rec_plans_exp["outcome"], rec_plans_root["outcome"])
        self.assertNotEqual(rec_plans_exp["exit"], rec_plans_root["exit"])

        # Index research explicit dir
        proc_rsch_exp = self._run_cli(
            "index",
            "research",
            "--check",
            "--agent",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        rec_rsch_exp = self._parse_and_validate_agent_record(proc_rsch_exp.stdout)
        proc_rsch_root = self._run_cli(
            "index", "research", "--check", "--agent", cwd=self.proj_root
        )
        rec_rsch_root = self._parse_and_validate_agent_record(proc_rsch_root.stdout)
        self.assertNotEqual(rec_rsch_exp["outcome"], rec_rsch_root["outcome"])
        self.assertNotEqual(rec_rsch_exp["exit"], rec_rsch_root["exit"])

        # Group plans explicit dir
        proc_group_exp = self._run_cli(
            "group",
            "plans",
            "p00001",
            "--set",
            "newset",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_group_exp.returncode, 2)
        self.assertIn("no plans artifact matched", proc_group_exp.stdout)

        # Rename plans explicit dir
        proc_rename_exp = self._run_cli(
            "rename",
            "plans",
            "p00001",
            "--slug",
            "newslug",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_rename_exp.returncode, 2)
        self.assertIn("no plans artifact matched", proc_rename_exp.stdout)

        # Archive plans explicit dir
        proc_archive_exp = self._run_cli(
            "archive",
            "plans",
            "p00003",
            "--dir",
            str(self.deep_subdir),
            cwd=self.proj_root,
        )
        self.assertEqual(proc_archive_exp.returncode, 2)
        self.assertIn("no plan or Set matches", proc_archive_exp.stdout)

    def test_assertion_d_outside_project_unaltered(self):
        """Bare index plans --check from outside AW project behaves identically."""
        proc_outside = self._run_cli(
            "index", "plans", "--check", "--agent", cwd=self.outside_cwd
        )
        rec_outside = self._parse_and_validate_agent_record(proc_outside.stdout)
        self.assertEqual(proc_outside.returncode, 0)
        self.assertEqual(rec_outside["outcome"], "conforms")
        self.assertEqual(rec_outside["findings"], 2)
        diag_rules = [d.get("rule") for d in rec_outside.get("diagnostics", [])]
        self.assertEqual(
            diag_rules, ["check.stale-index-missing", "check.stale-index-missing"]
        )

        proc_outside_h = self._run_cli(
            "index", "plans", "--check", cwd=self.outside_cwd
        )
        self.assertEqual(proc_outside_h.returncode, 0)
        self.assertIn("check.stale-index-missing", proc_outside_h.stdout)
