"""Regression test suite for non-surveyable directory validator refusal (IPD dirsilent-02 jei45f).

Pins that `aw specs check` and `aw backlog check` refuse at exit 2 when given
a non-surveyable --dir (such as a subdirectory of a real project) or when run
bare outside any AW project, rather than greenwashing with exit 0 and checked:0.

Pins:
- Subprocess execution with cwd outside any AW project and HOME isolated.
- Fixtures seeded with --records-backend repository, real spec, and real backlog item.
- Precondition: find_project_root is None for outside cwd.
- Non-zero root controls for both validators.
- Subdirectory refusal on human surface (exit 2, stderr names enclosing root and corrected command).
- Subdirectory refusal on --agent surface (exit 2, kind:error, outcome:cannot-run, path-free).
- Bare no-project refusal on human and --agent surfaces at exit 2.
- Anti-greenwashing invariant: no outcome:clean, no verified:true with checked:0.
- All three controls: root control, bare climb from subdirectory, single-file carve-out.
- Empty-but-real project surveyable clean control.
- Machine records validate via agent_schema.validate_agent_record with zero findings.
- Path-freeness: no fixture or root paths leak to stdout.
- Outcomes-not-structure: exercises real CLI execution only; tests observable behavior.
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
from agent_workflows.project_context import find_project_root

_SPEC_CONTENT = """# Spec: Test Spec

- Date: 2026-09-08
- Status: approved
- Author: tester
- Id: test01

## Body

Spec body text.

## Workflow history
- 2026-09-08 draft (tester): created.
- 2026-09-08 approved (tester): approved.
"""

_BACKLOG_CONTENT = """# Backlog: Test Item

- Id: b00001
- Status: open
- Set: testset
- Priority: high
- Work-Kind: bug
- Summary: Test item summary

## Details
Details text.
"""


class ValidatorNonsurveyableDirTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.fix_root = Path(self.td.name).resolve()

        # Isolated HOME
        self.fakehome = self.fix_root / "fakehome"
        self.fakehome.mkdir()

        # Real project root
        self.proj_root = self.fix_root / "real_project"
        self.proj_root.mkdir()
        subprocess.run(
            ["git", "init", str(self.proj_root)],
            check=True,
            capture_output=True,
        )

        # Config with records_backend repository
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

        # Real spec
        specs_dir = self.proj_root / ".aw" / "records" / "specs" / "approved"
        specs_dir.mkdir(parents=True)
        self.spec_file = specs_dir / "20260908-test01-01-test.spec.md"
        self.spec_file.write_text(_SPEC_CONTENT, encoding="utf-8")

        # Real backlog item
        backlog_dir = self.proj_root / ".aw" / "records" / "backlog" / "open"
        backlog_dir.mkdir(parents=True)
        self.backlog_file = backlog_dir / "20260908-b00001-01-test.item.md"
        self.backlog_file.write_text(_BACKLOG_CONTENT, encoding="utf-8")

        # Deep subdirectory inside real project
        self.deep_subdir = self.proj_root / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

        # Working directory completely outside any AW project
        self.outside_cwd = self.fix_root / "outside"
        self.outside_cwd.mkdir()

        # Subprocess environment with isolated HOME and lane PYTHONPATH
        self.repo_root = Path(__file__).resolve().parents[1]
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(self.repo_root)
        self.env["AW_NO_REEXEC"] = "1"
        self.env["HOME"] = str(self.fakehome)

    def tearDown(self):
        self.td.cleanup()

    def _run_cli(
        self, *args: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        run_cwd = cwd if cwd is not None else self.outside_cwd
        return subprocess.run(
            [sys.executable, "-m", "agent_workflows", *args],
            cwd=run_cwd,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def _parse_and_validate_agent_record(
        self, stdout: str, allowed_paths: tuple[Path, ...] = ()
    ) -> dict:
        # Validate path-freeness for stdout: no fixture paths or roots should appear
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

    def test_precondition_outside_is_not_project(self):
        """Precondition: outside_cwd must not be inside any AW project."""
        self.assertIsNone(
            find_project_root(self.outside_cwd),
            "outside_cwd must not be under an AW project",
        )

    def test_specs_check_subdirectory_refusal_human(self):
        """aw specs check --dir <subdir> exits 2 and names the enclosing root on stderr."""
        proc = self._run_cli("specs", "check", "--dir", str(self.deep_subdir))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn(str(self.proj_root), proc.stderr)
        self.assertIn(f"Run with: aw specs check --dir {self.proj_root}", proc.stderr)
        self.assertNotIn("is not installed in it", proc.stderr)

    def test_specs_check_subdirectory_refusal_agent(self):
        """aw specs check --agent --dir <subdir> exits 2 and emits a path-free cannot-run error record."""
        proc = self._run_cli(
            "specs", "check", "--agent", "--dir", str(self.deep_subdir)
        )
        self.assertEqual(proc.returncode, 2)
        rec = self._parse_and_validate_agent_record(proc.stdout)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["cmd"], "specs check")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertFalse(rec.get("verified", True))
        self.assertFalse(rec.get("complete", True))

        # Anti-greenwashing invariants
        self.assertNotEqual(rec["outcome"], "clean")
        self.assertFalse(rec.get("verified", False) and rec.get("checked") == 0)

    def test_specs_check_bare_no_project_refusal_human(self):
        """Bare aw specs check outside any project exits 2."""
        proc = self._run_cli("specs", "check")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("no AW project found here", proc.stderr)

    def test_specs_check_bare_no_project_refusal_agent(self):
        """Bare aw specs check --agent outside any project exits 2 with cannot-run."""
        proc = self._run_cli("specs", "check", "--agent")
        self.assertEqual(proc.returncode, 2)
        rec = self._parse_and_validate_agent_record(proc.stdout)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["cmd"], "specs check")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)

        # Anti-greenwashing invariants
        self.assertNotEqual(rec["outcome"], "clean")
        self.assertFalse(rec.get("verified", False) and rec.get("checked") == 0)

    def test_backlog_check_subdirectory_refusal_human(self):
        """aw backlog check --dir <subdir> exits 2 and names the enclosing root on stderr."""
        proc = self._run_cli("backlog", "check", "--dir", str(self.deep_subdir))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn(str(self.proj_root), proc.stderr)
        self.assertIn(f"Run with: aw backlog check --dir {self.proj_root}", proc.stderr)
        self.assertNotIn("is not installed in it", proc.stderr)

    def test_backlog_check_subdirectory_refusal_agent(self):
        """aw backlog check --agent --dir <subdir> exits 2 and emits a path-free cannot-run record."""
        proc = self._run_cli(
            "backlog", "check", "--agent", "--dir", str(self.deep_subdir)
        )
        self.assertEqual(proc.returncode, 2)
        rec = self._parse_and_validate_agent_record(proc.stdout)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["cmd"], "backlog check")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertFalse(rec.get("verified", True))
        self.assertFalse(rec.get("complete", True))

        # Anti-greenwashing invariants
        self.assertNotEqual(rec["outcome"], "clean")
        self.assertFalse(rec.get("verified", False) and rec.get("checked") == 0)

    def test_backlog_check_bare_no_project_refusal_human(self):
        """Bare aw backlog check outside any project exits 2."""
        proc = self._run_cli("backlog", "check")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout.strip(), "")
        self.assertIn("no AW project found here", proc.stderr)

    def test_backlog_check_bare_no_project_refusal_agent(self):
        """Bare aw backlog check --agent outside any project exits 2 with cannot-run."""
        proc = self._run_cli("backlog", "check", "--agent")
        self.assertEqual(proc.returncode, 2)
        rec = self._parse_and_validate_agent_record(proc.stdout)
        self.assertEqual(rec["kind"], "error")
        self.assertEqual(rec["cmd"], "backlog check")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)

        # Anti-greenwashing invariants
        self.assertNotEqual(rec["outcome"], "clean")
        self.assertFalse(rec.get("verified", False) and rec.get("checked") == 0)

    def test_control_surveyable_root_reports_nonzero_artifacts(self):
        """Control 1: --dir <root> checks real artifacts with nonzero count at exit 0."""
        # Specs check human
        proc_sp = self._run_cli("specs", "check", "--dir", str(self.proj_root))
        self.assertEqual(proc_sp.returncode, 0)
        self.assertIn("all specs conform. 1 specs checked.", proc_sp.stdout)

        # Specs check agent (nonzero checked asserted)
        proc_sp_agent = self._run_cli(
            "specs", "check", "--agent", "--dir", str(self.proj_root)
        )
        self.assertEqual(proc_sp_agent.returncode, 0)
        rec_sp = self._parse_and_validate_agent_record(proc_sp_agent.stdout)
        self.assertEqual(rec_sp["outcome"], "clean")
        self.assertEqual(rec_sp["exit"], 0)
        self.assertTrue(rec_sp["verified"])
        self.assertEqual(rec_sp["checked"], 1)

        # Backlog check human (countless success line preserved)
        proc_bl = self._run_cli("backlog", "check", "--dir", str(self.proj_root))
        self.assertEqual(proc_bl.returncode, 0)
        self.assertIn("all backlog items conform.", proc_bl.stdout)
        self.assertNotIn("0", proc_bl.stdout)

        # Backlog check agent (nonzero checked asserted)
        proc_bl_agent = self._run_cli(
            "backlog", "check", "--agent", "--dir", str(self.proj_root)
        )
        self.assertEqual(proc_bl_agent.returncode, 0)
        rec_bl = self._parse_and_validate_agent_record(proc_bl_agent.stdout)
        self.assertEqual(rec_bl["outcome"], "clean")
        self.assertEqual(rec_bl["exit"], 0)
        self.assertTrue(rec_bl["verified"])
        self.assertEqual(rec_bl["checked"], 1)

    def test_control_climb_from_subdirectory(self):
        """Control 2: bare invocation from subdirectory climbs to project root at exit 0."""
        # Specs check climb
        proc_sp = self._run_cli("specs", "check", cwd=self.deep_subdir)
        self.assertEqual(proc_sp.returncode, 0)
        self.assertIn("all specs conform. 1 specs checked.", proc_sp.stdout)

        proc_sp_agent = self._run_cli("specs", "check", "--agent", cwd=self.deep_subdir)
        self.assertEqual(proc_sp_agent.returncode, 0)
        rec_sp = self._parse_and_validate_agent_record(proc_sp_agent.stdout)
        self.assertEqual(rec_sp["checked"], 1)

        # Backlog check climb
        proc_bl = self._run_cli("backlog", "check", cwd=self.deep_subdir)
        self.assertEqual(proc_bl.returncode, 0)
        self.assertIn("all backlog items conform.", proc_bl.stdout)

        proc_bl_agent = self._run_cli(
            "backlog", "check", "--agent", cwd=self.deep_subdir
        )
        self.assertEqual(proc_bl_agent.returncode, 0)
        rec_bl = self._parse_and_validate_agent_record(proc_bl_agent.stdout)
        self.assertEqual(rec_bl["checked"], 1)

    def test_control_specs_check_single_file_carve_out(self):
        """Control 3: aw specs check <file> --dir <subdir> checks the file at exit 0."""
        proc_human = self._run_cli(
            "specs",
            "check",
            str(self.spec_file),
            "--dir",
            str(self.deep_subdir),
        )
        self.assertEqual(proc_human.returncode, 0)
        self.assertIn("all specs conform. 1 specs checked.", proc_human.stdout)

        proc_agent = self._run_cli(
            "specs",
            "check",
            str(self.spec_file),
            "--agent",
            "--dir",
            str(self.deep_subdir),
        )
        self.assertEqual(proc_agent.returncode, 0)
        # Note: in single-file mode, the agent record may include evidence referencing the spec
        rec = self._parse_and_validate_agent_record(
            proc_agent.stdout, allowed_paths=(self.spec_file,)
        )
        self.assertEqual(rec["outcome"], "clean")
        self.assertEqual(rec["exit"], 0)
        self.assertEqual(rec["checked"], 1)

    def test_control_empty_but_real_project_clean(self):
        """Control 4: surveyable empty project reports clean at exit 0 with 0 specs checked."""
        empty_root = self.fix_root / "empty_project"
        empty_root.mkdir()
        subprocess.run(
            ["git", "init", str(empty_root)],
            check=True,
            capture_output=True,
        )
        (empty_root / ".aw" / "records" / "specs" / "draft").mkdir(parents=True)
        (empty_root / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)

        proc_sp = self._run_cli("specs", "check", "--dir", str(empty_root))
        self.assertEqual(proc_sp.returncode, 0)
        self.assertIn("all specs conform. 0 specs checked.", proc_sp.stdout)

        proc_bl = self._run_cli("backlog", "check", "--dir", str(empty_root))
        self.assertEqual(proc_bl.returncode, 0)
        self.assertIn("all backlog items conform.", proc_bl.stdout)


if __name__ == "__main__":
    unittest.main()
