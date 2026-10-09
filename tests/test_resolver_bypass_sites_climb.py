"""Regression test suite for resolver-bypass sites climb (IPD dirsilent-03 sjsb04).

Pins:
- Subprocess execution with isolated HOME and lane PYTHONPATH.
- Fixtures seeded with --records-backend repository, real spec, real backlog item,
  sidecar history, and linked plan.
- Central assertion: bare-cwd climb for all six verbs (check, find, search,
  record-history, graduation, doctor) against nonzero observables.
- doctor negative: bare doctor from subdirectory does not report 'not installed'
  and names the project root rather than subdirectory as repository.
- doctor $HOME bound: isolated HOME that is an AW root and cwd at an uninstalled
  git repo under it names that repo and does not name HOME.
- Explicit --dir refusal on human and --agent surfaces for all five cli verbs.
- Anti-greenwashing negatives: no outcome:conforms/clean, no verified:true with 0 count.
- Four controls: explicit --dir <root>, bare invocation from root, relative --dir,
  and doctor 0/1 exit convention.
- Agent record schema validity via agent_schema.validate_agent_record with zero findings.
- Path-freeness: no fixture or root paths leak to stdout in agent records.
- Outcomes-not-structure: tests observable behavior only.
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

_SPEC_CONTENT = """# Spec: Test Spec

- Date: 2026-10-01
- Status: approved
- Author: tester
- Id: test01

## Body

probe keyword for search

## Workflow history
- 2026-10-01 draft (tester): created.
- 2026-10-01 approved (tester): approved.
"""

_BACKLOG_CONTENT = """# Backlog: Test Item

- Id: b00001
- Status: open
- Set: testset
- Priority: high
- Work-Kind: bug
- Summary: probe keyword for search

## Details
probe details
"""

_PLAN_CONTENT = """# IPD: Test Plan

- Date: 2026-10-01
- Id: p00001
- Status: pending
- Priority: high
- Work-Kind: bug
- Set: testset
- From-Backlog: b00001

## Details
Plan details
"""


class ResolverBypassSitesClimbTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.fix_root = Path(self.td.name).resolve()

        # Isolated fake HOME
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

        pkg_version = versioning.resolve_version(engine.resolve_source_root(None))
        self.pkg_version = pkg_version

        # .aw system & config with records_backend repository
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

        # Real spec
        specs_dir = self.proj_root / ".aw" / "records" / "specs" / "approved"
        specs_dir.mkdir(parents=True)
        self.spec_file = specs_dir / "20261001-test01-01-test.spec.md"
        self.spec_file.write_text(_SPEC_CONTENT, encoding="utf-8")

        # Real backlog item
        backlog_dir = self.proj_root / ".aw" / "records" / "backlog" / "open"
        backlog_dir.mkdir(parents=True)
        self.backlog_file = backlog_dir / "20261001-b00001-01-test.item.md"
        self.backlog_file.write_text(_BACKLOG_CONTENT, encoding="utf-8")

        # Sidecar history
        self.history_file = self.proj_root / ".aw" / "records" / "history.jsonl"
        self.history_file.write_text(
            json.dumps(
                {
                    "id6": "test01",
                    "date": "2026-10-01",
                    "status": "approved",
                    "author": "tester",
                }
            )
            + "\n",
            encoding="utf-8",
        )

        # Linked plan for graduation
        plans_dir = self.proj_root / ".aw" / "records" / "plans" / "pending"
        plans_dir.mkdir(parents=True)
        self.plan_file = plans_dir / "20261001-testset-01-p00001-plan.ipd.md"
        self.plan_file.write_text(_PLAN_CONTENT, encoding="utf-8")

        # Deep subdirectory inside real project
        self.deep_subdir = self.proj_root / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

        # Working directory completely outside any AW project
        self.outside_cwd = self.fix_root / "outside"
        self.outside_cwd.mkdir()

        # HOME-bound fixture: HOME is an AW project root with .aw/config
        self.home_aw = self.fix_root / "home_aw"
        self.home_aw.mkdir()
        (self.home_aw / ".aw" / "config").mkdir(parents=True)
        (self.home_aw / ".aw" / "config" / "project.json").write_text(
            json.dumps({"preset": "local-only", "records_backend": "home"}),
            encoding="utf-8",
        )
        self.uninstalled_git = self.home_aw / "src" / "uninstalled_repo"
        self.uninstalled_git.mkdir(parents=True)
        subprocess.run(
            ["git", "init", str(self.uninstalled_git)],
            check=True,
            capture_output=True,
        )

        # Environment
        self.repo_root = Path(__file__).resolve().parents[1]
        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(self.repo_root)
        self.env["AW_NO_REEXEC"] = "1"
        self.env["HOME"] = str(self.fakehome)

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

    def test_bare_cwd_climb_check(self):
        """Bare aw check specs from subdirectory climbs and reports 1 spec checked."""
        proc_deep = self._run_cli("check", "specs", cwd=self.deep_subdir)
        proc_root = self._run_cli("check", "specs", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, proc_root.returncode)
        self.assertIn("1 specs", proc_deep.stdout)
        self.assertIn("1 specs", proc_root.stdout)

    def test_bare_cwd_climb_find(self):
        """Bare aw find specs from subdirectory climbs and reports test01 spec."""
        proc_deep = self._run_cli("find", "specs", cwd=self.deep_subdir)
        proc_root = self._run_cli("find", "specs", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, 0)
        self.assertEqual(proc_root.returncode, 0)
        self.assertIn("test01", proc_deep.stdout)
        self.assertIn("test01", proc_root.stdout)

    def test_bare_cwd_climb_search(self):
        """Bare aw search probe from subdirectory climbs and reports matching file."""
        proc_deep = self._run_cli("search", "probe", cwd=self.deep_subdir)
        proc_root = self._run_cli("search", "probe", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, 0)
        self.assertEqual(proc_root.returncode, 0)
        self.assertIn("probe keyword for search", proc_deep.stdout)
        self.assertIn("probe keyword for search", proc_root.stdout)

    def test_bare_cwd_climb_record_history(self):
        """Bare aw record-history test01 from subdirectory climbs and reports history line."""
        proc_deep = self._run_cli("record-history", "test01", cwd=self.deep_subdir)
        proc_root = self._run_cli("record-history", "test01", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, 0)
        self.assertEqual(proc_root.returncode, 0)
        self.assertIn("History for test01", proc_deep.stdout)
        self.assertIn("History for test01", proc_root.stdout)

    def test_bare_cwd_climb_graduation(self):
        """Bare aw graduation b00001 from subdirectory climbs and reports linked plan."""
        proc_deep = self._run_cli("graduation", "b00001", cwd=self.deep_subdir)
        proc_root = self._run_cli("graduation", "b00001", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, 0)
        self.assertEqual(proc_root.returncode, 0)
        self.assertIn("1 linked artifact(s)", proc_deep.stdout)
        self.assertIn("1 linked artifact(s)", proc_root.stdout)
        self.assertIn("p00001", proc_deep.stdout)
        self.assertIn("p00001", proc_root.stdout)

    def test_bare_cwd_climb_doctor(self):
        """Bare aw doctor from subdirectory climbs, names project root, and reports installed version."""
        proc_deep = self._run_cli("doctor", cwd=self.deep_subdir)
        proc_root = self._run_cli("doctor", cwd=self.proj_root)
        self.assertEqual(proc_deep.returncode, proc_root.returncode)
        self.assertIn(
            f"Repository:  Target project repository ({self.proj_root})",
            proc_deep.stdout,
        )
        self.assertIn(
            f"Repository:  Target project repository ({self.proj_root})",
            proc_root.stdout,
        )
        self.assertNotIn(f"({self.deep_subdir})", proc_deep.stdout)
        self.assertNotIn("not installed", proc_deep.stdout)
        self.assertIn(self.pkg_version, proc_deep.stdout)

    def test_doctor_negative_not_installed(self):
        """From subdirectory, aw doctor output must NOT contain 'not installed' and must name root."""
        proc = self._run_cli("doctor", cwd=self.deep_subdir)
        self.assertNotIn("not installed", proc.stdout)
        self.assertIn(str(self.proj_root), proc.stdout)
        self.assertNotIn(str(self.deep_subdir), proc.stdout)

    def test_doctor_home_bound(self):
        """With isolated HOME an AW root and cwd at uninstalled git repo, doctor names that repo not HOME."""
        env_home = dict(self.env)
        env_home["HOME"] = str(self.home_aw)
        proc = self._run_cli("doctor", cwd=self.uninstalled_git, env=env_home)
        self.assertIn(
            f"Repository:  Target project repository ({self.uninstalled_git})",
            proc.stdout,
        )
        self.assertNotIn(
            f"Repository:  Target project repository ({self.home_aw})",
            proc.stdout,
        )

    def test_explicit_dir_refusal_human(self):
        """All five CLI verbs refuse with exit 2 on human surface when given non-surveyable --dir."""
        verbs = [
            ("check", ["check", "--dir", str(self.deep_subdir)]),
            ("find", ["find", "specs", "--dir", str(self.deep_subdir)]),
            ("search", ["search", "probe", "--dir", str(self.deep_subdir)]),
            (
                "record-history",
                ["record-history", "test01", "--dir", str(self.deep_subdir)],
            ),
            ("graduation", ["graduation", "b00001", "--dir", str(self.deep_subdir)]),
        ]
        for name, cmd in verbs:
            proc = self._run_cli(*cmd)
            self.assertEqual(
                proc.returncode, 2, f"Verb {name} did not exit 2: {proc.stderr}"
            )
            self.assertEqual(
                proc.stdout.strip(), "", f"Verb {name} had non-empty stdout"
            )
            self.assertIn(
                str(self.proj_root),
                proc.stderr,
                f"Verb {name} stderr missing enclosing root: {proc.stderr}",
            )
            self.assertIn(
                f"Run with: aw {name} --dir {self.proj_root}",
                proc.stderr,
                f"Verb {name} stderr missing corrected command: {proc.stderr}",
            )
            self.assertNotIn(
                "is not installed in it",
                proc.stderr,
                f"Verb {name} stderr falsely said AW not installed: {proc.stderr}",
            )

    def test_explicit_dir_refusal_agent(self):
        """All five CLI verbs emit a path-free cannot-run error record at exit 2 under --agent."""
        verbs = [
            ("check", ["check", "--agent", "--dir", str(self.deep_subdir)]),
            ("find", ["find", "specs", "--agent", "--dir", str(self.deep_subdir)]),
            ("search", ["search", "probe", "--agent", "--dir", str(self.deep_subdir)]),
            (
                "record-history",
                ["record-history", "test01", "--agent", "--dir", str(self.deep_subdir)],
            ),
            (
                "graduation",
                ["graduation", "b00001", "--agent", "--dir", str(self.deep_subdir)],
            ),
        ]
        for name, cmd in verbs:
            proc = self._run_cli(*cmd)
            self.assertEqual(
                proc.returncode, 2, f"Verb {name} did not exit 2 under --agent"
            )
            rec = self._parse_and_validate_agent_record(proc.stdout)
            self.assertEqual(rec["kind"], "error", f"Verb {name} kind != error")
            self.assertEqual(rec["cmd"], name, f"Verb {name} cmd mismatch")
            self.assertEqual(
                rec["outcome"], "cannot-run", f"Verb {name} outcome != cannot-run"
            )
            self.assertEqual(rec["exit"], 2, f"Verb {name} exit != 2")
            self.assertFalse(rec["complete"], f"Verb {name} complete != False")
            self.assertFalse(rec["verified"], f"Verb {name} verified != False")

    def test_anti_greenwash_invariants(self):
        """Confirm no positive outcome and no verified:true over 0 count on non-surveyable --dir."""
        verbs = [
            ("check", ["check", "--agent", "--dir", str(self.deep_subdir)]),
            ("find", ["find", "specs", "--agent", "--dir", str(self.deep_subdir)]),
            ("search", ["search", "probe", "--agent", "--dir", str(self.deep_subdir)]),
            (
                "record-history",
                ["record-history", "test01", "--agent", "--dir", str(self.deep_subdir)],
            ),
            (
                "graduation",
                ["graduation", "b00001", "--agent", "--dir", str(self.deep_subdir)],
            ),
        ]
        for name, cmd in verbs:
            proc = self._run_cli(*cmd)
            rec = self._parse_and_validate_agent_record(proc.stdout)
            self.assertNotIn(rec["outcome"], ("conforms", "clean", "ok"))
            self.assertFalse(rec.get("verified", False))

    def test_controls_root_explicit_dir(self):
        """Explicit --dir <root> still works for all six verbs at surveyable root."""
        commands = [
            ("check", ["check", "specs", "--dir", str(self.proj_root)], ("1 specs",)),
            ("find", ["find", "specs", "--dir", str(self.proj_root)], ("test01",)),
            (
                "search",
                ["search", "probe", "--dir", str(self.proj_root)],
                ("probe keyword for search",),
            ),
            (
                "record-history",
                ["record-history", "test01", "--dir", str(self.proj_root)],
                ("History for test01",),
            ),
            (
                "graduation",
                ["graduation", "b00001", "--dir", str(self.proj_root)],
                ("1 linked artifact(s)",),
            ),
            (
                "doctor",
                ["doctor", "--dir", str(self.proj_root)],
                (f"Target project repository ({self.proj_root})",),
            ),
        ]
        for name, cmd, needles in commands:
            proc = self._run_cli(*cmd)
            if name != "doctor" and name != "check":
                self.assertEqual(
                    proc.returncode, 0, f"Verb {name} failed on root: {proc.stderr}"
                )
            for needle in needles:
                self.assertIn(
                    needle, proc.stdout, f"Verb {name} output missing {needle}"
                )

    def test_controls_bare_root(self):
        """Bare invocation from root reports artifacts for all six verbs."""
        commands = [
            ("check", ["check", "specs"], ("1 specs",)),
            ("find", ["find", "specs"], ("test01",)),
            ("search", ["search", "probe"], ("probe keyword for search",)),
            ("record-history", ["record-history", "test01"], ("History for test01",)),
            ("graduation", ["graduation", "b00001"], ("1 linked artifact(s)",)),
            ("doctor", ["doctor"], (f"Target project repository ({self.proj_root})",)),
        ]
        for name, cmd, needles in commands:
            proc = self._run_cli(*cmd, cwd=self.proj_root)
            for needle in needles:
                self.assertIn(
                    needle, proc.stdout, f"Verb {name} output missing {needle}"
                )

    def test_controls_relative_dir(self):
        """A relative --dir resolves correctly to the project root and reports artifacts."""
        # Run from deep_subdir with relative path to proj_root ('../..')
        commands = [
            ("check", ["check", "specs", "--dir", "../.."], ("1 specs",)),
            ("find", ["find", "specs", "--dir", "../.."], ("test01",)),
            (
                "search",
                ["search", "probe", "--dir", "../.."],
                ("probe keyword for search",),
            ),
            (
                "record-history",
                ["record-history", "test01", "--dir", "../.."],
                ("History for test01",),
            ),
            (
                "graduation",
                ["graduation", "b00001", "--dir", "../.."],
                ("1 linked artifact(s)",),
            ),
            (
                "doctor",
                ["doctor", "--dir", "../.."],
                (f"Target project repository ({self.proj_root})",),
            ),
        ]
        for name, cmd, needles in commands:
            proc = self._run_cli(*cmd, cwd=self.deep_subdir)
            for needle in needles:
                self.assertIn(
                    needle, proc.stdout, f"Verb {name} relative --dir missing {needle}"
                )

    def test_controls_doctor_exit_convention(self):
        """Doctor returns 0 or 1, never 2 (diagnostic, not refusal)."""
        proc_deep = self._run_cli("doctor", "--dir", str(self.deep_subdir))
        self.assertIn(proc_deep.returncode, (0, 1))
        self.assertNotEqual(proc_deep.returncode, 2)
