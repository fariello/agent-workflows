"""Tests for leak-sanitizer machine-readable CLI flags (--json and --fields).

Reuses the scratch git repository fixture (_init_repo and _commit) and runtime
leak token synthesis pattern from tests/test_local_leaks.py.

Stdout and stderr are captured into separate streams rather than combined via
tests/test_local_leaks.py's _run helper. The combined helper masked the defect:
`check-local-leaks --json` wrote 0 bytes to stdout while printing human prose to
stderr, which merged into non-empty output and hid that the machine payload was
completely missing on stdout. By capturing stdout and stderr separately, these
tests verify that stdout carries the parseable JSON payload and stderr carries
no payload.

CLI invocations drive cli.main in-process using contextlib.redirect_stdout and
contextlib.redirect_stderr with scratch repo paths passed as positional `dir`
arguments, preserving process working directory across parallel pytest-xdist
workers. XDG_CONFIG_HOME is pinned to the temporary test directory to isolate
against ambient user configuration.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import cli
from agent_workflows import leak_sanitizer as ls


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True)
    return path


def _commit(repo: Path, rel: str, content: str, msg: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", rel], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", msg], check=True)


def _capture_cli_separate(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code if code is not None else 0, out.getvalue(), err.getvalue()


class LeakSanitizerMachineFlagsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(Path(self._tmp.name) / "cfg")

        def _restore_xdg():
            if self._old_xdg is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = self._old_xdg

        self.addCleanup(_restore_xdg)

    def test_json_flag_emits_parseable_payload_across_spellings_and_states(self):
        expected_keys = {
            "schema",
            "command",
            "status",
            "exit_code",
            "summary",
            "verified",
            "complete",
            "diagnostics",
            "changes",
            "evidence",
            "next_actions",
            "data",
        }

        cases = [
            ("clean", "clean_file.txt", "harmless content\n", 0, "clean"),
            (
                "planted",
                "leak_file.txt",
                "/home/" + "someuser" + "/secret/path\n",
                1,
                "findings",
            ),
        ]

        spellings = ["check-local-leaks", "sanitize"]

        for state_name, filename, file_content, expected_code, expected_status in cases:
            for spelling in spellings:
                with self.subTest(state=state_name, spelling=spelling):
                    repo = _init_repo(
                        Path(self._tmp.name) / f"repo_{state_name}_{spelling}"
                    )
                    _commit(repo, filename, file_content, f"commit {state_name}")

                    code, stdout, stderr = _capture_cli_separate(
                        [spelling, str(repo), "--json"]
                    )

                    self.assertEqual(
                        code,
                        expected_code,
                        f"Expected exit code {expected_code} for {state_name} tree with {spelling}, got {code}. stdout={stdout!r}, stderr={stderr!r}",
                    )

                    self.assertTrue(
                        stdout.strip(),
                        f"Expected non-empty JSON stdout for {state_name} tree with {spelling}, but stdout was empty. stderr={stderr!r}",
                    )

                    try:
                        payload = json.loads(stdout)
                    except json.JSONDecodeError as exc:
                        self.fail(
                            f"Failed to parse JSON stdout for {state_name} tree with {spelling}: {exc}. stdout={stdout!r}"
                        )

                    self.assertEqual(
                        set(payload.keys()),
                        expected_keys,
                        f"Payload keys mismatch for {state_name} tree with {spelling}",
                    )
                    self.assertEqual(
                        payload["command"],
                        "check-local-leaks",
                        f"Expected command 'check-local-leaks', got {payload.get('command')}",
                    )
                    self.assertEqual(
                        payload["exit_code"],
                        expected_code,
                        f"Expected exit_code {expected_code}, got {payload.get('exit_code')}",
                    )
                    self.assertEqual(
                        payload["status"],
                        expected_status,
                        f"Expected status {expected_status}, got {payload.get('status')}",
                    )

                    # Ensure stderr carries no JSON payload
                    if stderr.strip():
                        with self.assertRaises(
                            ValueError,
                            msg=f"stderr should not carry a JSON payload for {state_name} with {spelling}",
                        ):
                            json.loads(stderr)

    def test_fields_projection_scopes_to_agent_output(self):
        # Key set preserved by projection for this command under --agent --fields cmd,outcome:
        # Envelope keys preserved by agent_schema.filter_record_fields:
        # _MANDATORY_FIELDS ('schema', 'kind', 'cmd', 'outcome', 'exit', 'verified', 'complete')
        # + _PRESERVED_FIELDS ('next')
        # + requested fields ('cmd', 'outcome')
        # Total projected keys: schema, kind, cmd, outcome, exit, verified, complete, next.
        expected_projected_keys = {
            "schema",
            "kind",
            "cmd",
            "outcome",
            "exit",
            "verified",
            "complete",
            "next",
        }

        spellings = ["check-local-leaks", "sanitize"]
        for spelling in spellings:
            with self.subTest(spelling=spelling):
                repo = _init_repo(Path(self._tmp.name) / f"repo_fields_{spelling}")
                _commit(repo, "clean_file.txt", "harmless content\n", "commit clean")

                # 1. Presence case: with --fields cmd,outcome
                code_proj, out_proj, err_proj = _capture_cli_separate(
                    [spelling, str(repo), "--agent", "--fields", "cmd,outcome"]
                )
                self.assertEqual(code_proj, 0)
                self.assertTrue(
                    out_proj.strip(), f"Expected stdout for {spelling} with --fields"
                )
                rec_proj = json.loads(out_proj.strip())

                # Assert exact projected key set
                self.assertEqual(
                    set(rec_proj.keys()),
                    expected_projected_keys,
                    f"Projected keys mismatch for {spelling} under --agent --fields cmd,outcome",
                )
                # Assert unrequested domain keys are absent
                self.assertNotIn("findings", rec_proj)
                self.assertNotIn("evidence", rec_proj)

                # 2. Absence case: without --fields
                code_full, out_full, err_full = _capture_cli_separate(
                    [spelling, str(repo), "--agent"]
                )
                self.assertEqual(code_full, 0)
                self.assertTrue(
                    out_full.strip(), f"Expected stdout for {spelling} without --fields"
                )
                rec_full = json.loads(out_full.strip())

                # Assert unrequested domain keys ARE present when --fields is omitted (ruling out vacuous projection)
                self.assertIn(
                    "findings",
                    rec_full,
                    f"Expected 'findings' key in full unprojected record for {spelling}",
                )
                self.assertIn(
                    "evidence",
                    rec_full,
                    f"Expected 'evidence' key in full unprojected record for {spelling}",
                )

    def test_fix_machine_flags_and_human_controls(self):
        spellings = ["check-local-leaks", "sanitize"]
        human_fix_prose = (
            "would rewrite:",
            "rewrote:",
            "Needs manual edit",
            "No auto-fixable local leaks found.",
        )

        for spelling in spellings:
            # (a) --fix --dry-run on a planted home path under --agent
            with self.subTest(spelling=spelling, case="fix-dry-run-agent"):
                repo = _init_repo(Path(self._tmp.name) / f"repo_fix_dry_{spelling}")
                planted = "/home/" + "user_a" + "/path.txt\n"
                _commit(repo, "planted.txt", planted, "commit leak")
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(repo), "--fix", "--dry-run", "--agent"]
                )
                self.assertEqual(code, 0)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("outcome"), "preview")
                self.assertIs(rec.get("applied"), False)
                self.assertEqual(rec.get("exit"), 0)
                self.assertEqual(
                    [c["path"] for c in rec.get("changes", [])], ["planted.txt"]
                )
                self.assertIsNotNone(rec.get("next"))
                self.assertIn("--yes", rec.get("next"))
                self.assertEqual(
                    (repo / "planted.txt").read_text(encoding="utf-8"), planted
                )
                for prose in human_fix_prose:
                    self.assertNotIn(prose, stderr)
                if stderr.strip():
                    with self.assertRaises(ValueError):
                        json.loads(stderr)

            # (b) --fix --yes on a planted home path under --agent
            with self.subTest(spelling=spelling, case="fix-yes-agent"):
                repo = _init_repo(Path(self._tmp.name) / f"repo_fix_yes_{spelling}")
                planted = "/home/" + "user_b" + "/path.txt\n"
                _commit(repo, "planted.txt", planted, "commit leak")
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(repo), "--fix", "--yes", "--agent"]
                )
                self.assertEqual(code, 0)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertIs(rec.get("applied"), True)
                self.assertEqual(rec.get("exit"), 0)
                self.assertEqual(
                    [c["path"] for c in rec.get("changes", [])], ["planted.txt"]
                )
                content = (repo / "planted.txt").read_text(encoding="utf-8")
                self.assertNotIn("user_b", content)
                for prose in human_fix_prose:
                    self.assertNotIn(prose, stderr)
                if stderr.strip():
                    with self.assertRaises(ValueError):
                        json.loads(stderr)

            # (c) --fix --yes on a clean tree under --agent
            with self.subTest(spelling=spelling, case="fix-yes-clean-agent"):
                repo = _init_repo(Path(self._tmp.name) / f"repo_clean_{spelling}")
                _commit(repo, "clean.txt", "clean content\n", "commit clean")
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(repo), "--fix", "--yes", "--agent"]
                )
                self.assertEqual(code, 0)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("exit"), 0)
                self.assertEqual(rec.get("outcome"), "clean")
                self.assertFalse(rec.get("changes"))
                for prose in human_fix_prose:
                    self.assertNotIn(prose, stderr)
                if stderr.strip():
                    with self.assertRaises(ValueError):
                        json.loads(stderr)

            # (d) --fix --yes on a private-repo identity token under --agent
            with self.subTest(spelling=spelling, case="fix-yes-private-repo-agent"):
                repo = _init_repo(Path(self._tmp.name) / f"repo_priv_{spelling}")
                priv_content = "see " + ls._R1 + " repo\n"
                _commit(repo, "priv.txt", priv_content, "commit priv")
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(repo), "--fix", "--yes", "--agent"]
                )
                self.assertEqual(code, 1)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("outcome"), "findings")
                self.assertGreaterEqual(rec.get("findings", 0), 1)
                self.assertTrue(
                    any(
                        d.get("rule") == "private-repo"
                        for d in rec.get("diagnostics", [])
                    )
                )
                self.assertEqual(
                    (repo / "priv.txt").read_text(encoding="utf-8"), priv_content
                )
                for prose in human_fix_prose:
                    self.assertNotIn(prose, stderr)
                if stderr.strip():
                    with self.assertRaises(ValueError):
                        json.loads(stderr)

            # (e) --fix with neither --yes nor --dry-run under --agent
            with self.subTest(spelling=spelling, case="fix-no-attestation-agent"):
                repo = _init_repo(Path(self._tmp.name) / f"repo_noattest_{spelling}")
                planted = "/home/" + "user_e" + "/path.txt\n"
                _commit(repo, "planted.txt", planted, "commit leak")
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(repo), "--fix", "--agent"]
                )
                self.assertEqual(code, 2)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("kind"), "error")
                self.assertEqual(rec.get("outcome"), "cannot-run")
                self.assertNotIn("[y/N]", stdout)
                self.assertEqual(
                    (repo / "planted.txt").read_text(encoding="utf-8"), planted
                )
                for prose in human_fix_prose:
                    self.assertNotIn(prose, stderr)
                if stderr.strip():
                    with self.assertRaises(ValueError):
                        json.loads(stderr)

        # One --json row for (a) asserting CommandResult.to_dict key names
        repo_json = _init_repo(Path(self._tmp.name) / "repo_fix_dry_json")
        planted_json = "/home/" + "user_json" + "/path.txt\n"
        _commit(repo_json, "planted.txt", planted_json, "commit leak")
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(repo_json), "--fix", "--dry-run", "--json"]
        )
        self.assertEqual(code, 0)
        rec_json = json.loads(stdout)
        self.assertEqual(rec_json.get("status"), "preview")
        self.assertEqual(rec_json.get("exit_code"), 0)
        changes = rec_json.get("changes", [])
        self.assertTrue(changes)
        self.assertEqual(changes[0].get("path"), "planted.txt")
        self.assertEqual(
            (repo_json / "planted.txt").read_text(encoding="utf-8"), planted_json
        )
        for prose in human_fix_prose:
            self.assertNotIn(prose, stderr)
        if stderr.strip():
            with self.assertRaises(ValueError):
                json.loads(stderr)

        # HUMAN-path controls (no machine flag) on a fresh planted repo
        # --fix --dry-run (stdout empty, stderr exactly `would rewrite: <rel>\n`, exit 0, file unchanged)
        repo_h1 = _init_repo(Path(self._tmp.name) / "repo_human_dry")
        planted_h1 = "/home/" + "user_h1" + "/path.txt\n"
        _commit(repo_h1, "planted.txt", planted_h1, "commit leak")
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(repo_h1), "--fix", "--dry-run"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "would rewrite: planted.txt\n")
        self.assertEqual(
            (repo_h1 / "planted.txt").read_text(encoding="utf-8"), planted_h1
        )

        # --fix --yes (stdout empty, stderr exactly `rewrote: <rel>\n`, exit 0)
        repo_h2 = _init_repo(Path(self._tmp.name) / "repo_human_yes")
        planted_h2 = "/home/" + "user_h2" + "/path.txt\n"
        _commit(repo_h2, "planted.txt", planted_h2, "commit leak")
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(repo_h2), "--fix", "--yes"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "rewrote: planted.txt\n")

        # --fix --yes on a clean tree (stderr exactly `No auto-fixable local leaks found.\n`)
        repo_h3 = _init_repo(Path(self._tmp.name) / "repo_human_clean")
        _commit(repo_h3, "clean.txt", "clean content\n", "commit clean")
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(repo_h3), "--fix", "--yes"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "No auto-fixable local leaks found.\n")

    def test_exit_2_error_coverage_and_human_controls(self):
        non_git_dir = Path(self._tmp.name) / "not_a_git_repo"
        non_git_dir.mkdir(parents=True, exist_ok=True)
        old_ceiling = os.environ.get("GIT_CEILING_DIRECTORIES")
        os.environ["GIT_CEILING_DIRECTORIES"] = str(non_git_dir.parent)

        def _restore_ceiling():
            if old_ceiling is None:
                os.environ.pop("GIT_CEILING_DIRECTORIES", None)
            else:
                os.environ["GIT_CEILING_DIRECTORIES"] = old_ceiling

        self.addCleanup(_restore_ceiling)

        spellings = ["check-local-leaks", "sanitize"]
        for spelling in spellings:
            # Plain scan outside git repo under --agent
            with self.subTest(spelling=spelling, case="non-git-scan-agent"):
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(non_git_dir), "--agent"]
                )
                self.assertEqual(code, 2)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("kind"), "error")
                self.assertEqual(rec.get("outcome"), "cannot-run")
                self.assertEqual(rec.get("exit"), 2)
                self.assertIs(rec.get("verified"), False)
                self.assertIs(rec.get("complete"), False)
                self.assertEqual(rec.get("next"), "aw sanitize --help")
                self.assertEqual(stderr, "")

            # --fix --yes outside git repo under --agent
            with self.subTest(spelling=spelling, case="non-git-fix-yes-agent"):
                code, stdout, stderr = _capture_cli_separate(
                    [spelling, str(non_git_dir), "--fix", "--yes", "--agent"]
                )
                self.assertEqual(code, 2)
                self.assertEqual(len(stdout.strip().splitlines()), 1)
                rec = json.loads(stdout.strip())
                self.assertEqual(rec.get("kind"), "error")
                self.assertEqual(rec.get("outcome"), "cannot-run")
                self.assertEqual(rec.get("exit"), 2)
                self.assertIs(rec.get("verified"), False)
                self.assertIs(rec.get("complete"), False)
                self.assertEqual(rec.get("next"), "aw sanitize --help")
                self.assertEqual(stderr, "")

        # Non-git scan under --json
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(non_git_dir), "--json"]
        )
        self.assertEqual(code, 2)
        rec = json.loads(stdout)
        self.assertEqual(rec.get("exit_code"), 2)
        self.assertEqual(rec.get("status"), "cannot-run")
        self.assertIn("not a git repository", rec.get("summary", ""))
        self.assertEqual(stderr, "")

        # OSError branch with --wheel <missing-path> against valid repo
        valid_repo = _init_repo(Path(self._tmp.name).resolve() / "repo_oserror")
        missing_wheel = str(valid_repo / "nonexistent.whl")
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(valid_repo), "--wheel", missing_wheel, "--agent"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(len(stdout.strip().splitlines()), 1)
        rec = json.loads(stdout.strip())
        self.assertEqual(rec.get("kind"), "error")
        self.assertEqual(rec.get("outcome"), "cannot-run")
        self.assertEqual(rec.get("exit"), 2)
        self.assertIs(rec.get("verified"), False)
        self.assertIs(rec.get("complete"), False)
        self.assertEqual(rec.get("next"), "aw sanitize --help")
        self.assertEqual(stderr, "")

        # HUMAN-path controls (no machine flag)
        # Non-git scan
        code, stdout, stderr = _capture_cli_separate(["sanitize", str(non_git_dir)])
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr, "check-local-leaks: not a git repository or git unavailable\n"
        )

        # Non-git --fix --yes
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(non_git_dir), "--fix", "--yes"]
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr, "check-local-leaks: not a git repository or git unavailable\n"
        )

        # OSError human control
        code, stdout, stderr = _capture_cli_separate(
            ["sanitize", str(valid_repo), "--wheel", missing_wheel]
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr.startswith("check-local-leaks: [Errno 2]"))
        self.assertTrue(
            missing_wheel in stderr or repr(missing_wheel) in stderr,
            f"Expected {missing_wheel!r} in {stderr!r}",
        )
