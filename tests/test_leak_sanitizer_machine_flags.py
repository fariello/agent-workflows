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
