"""Outcome tests for typed gate-pair validation at creation in aw backlog new (IPD 7vs14y).

Pins the closed gate vocabulary and ref validation on aw backlog new --status blocked:
(a) out-of-vocabulary kind refused (rc 2, stderr names --gate-kind, zero files)
(b) valid kind with malformed ref refused (rc 2, stderr names --gate-ref, zero files)
(c) one valid pair per kind in GATE_KINDS succeeds (rc 0, written file carries exact gate lines)
(d) valid blocked item passes aw backlog check (rc 0, create and check agree)
(e) --status open with invalid gate flags writes no Gate-Kind/Gate-Ref lines
"""

from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import attention_contract as A
from agent_workflows import cli


def _setup_repo(root: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    return root


def _extract_wrote_path(stdout: str) -> Path:
    for line in stdout.splitlines():
        if "wrote " in line:
            return Path(line.split("wrote ", 1)[1].strip())
    raise AssertionError(f"No 'wrote ' path found in stdout:\n{stdout}")


class BacklogNewGateVocabularyTests(unittest.TestCase):
    def test_out_of_vocabulary_kind_refused(self):
        """(a) out-of-vocabulary kind refused, rc 2, stderr names --gate-kind, zero files."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "new",
                        "--dir",
                        str(repo),
                        "--summary",
                        "item bad kind",
                        "--status",
                        "blocked",
                        "--gate-kind",
                        "bogus-kind",
                        "--gate-ref",
                        "x",
                        "--priority",
                        "low",
                        "--work-kind",
                        "chore",
                        "--apply",
                    ]
                )
            self.assertEqual(rc, 2)
            self.assertIn("--gate-kind", err.getvalue())
            self.assertEqual(list(repo.rglob("*.md")), [])

    def test_malformed_gate_ref_refused(self):
        """(b) valid kind with malformed ref refused, rc 2, stderr names --gate-ref, zero files."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "new",
                        "--dir",
                        str(repo),
                        "--summary",
                        "item bad ref",
                        "--status",
                        "blocked",
                        "--gate-kind",
                        "date",
                        "--gate-ref",
                        "notadate",
                        "--priority",
                        "low",
                        "--work-kind",
                        "chore",
                        "--apply",
                    ]
                )
            self.assertEqual(rc, 2)
            self.assertIn("--gate-ref", err.getvalue())
            self.assertEqual(list(repo.rglob("*.md")), [])

    def test_every_valid_gate_kind_succeeds(self):
        """(c) one valid pair per kind in GATE_KINDS succeeds with rc 0 and exact gate lines."""
        valid_pairs = [
            ("artifact", "docs/x.md"),
            ("date", "2026-12-01"),
            ("decision", "D12"),
            ("external", "vendor-fix"),
            ("issue", "https://example.com/i/1"),
            ("todo", "TODO.md"),
        ]
        self.assertEqual(set(kind for kind, _ in valid_pairs), set(A.GATE_KINDS))

        for kind, ref in valid_pairs:
            with self.subTest(kind=kind, ref=ref):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = _setup_repo(Path(tmp))
                    out, err = io.StringIO(), io.StringIO()
                    with redirect_stdout(out), redirect_stderr(err):
                        rc = cli.main(
                            [
                                "backlog",
                                "new",
                                "--dir",
                                str(repo),
                                "--summary",
                                f"valid item for {kind}",
                                "--status",
                                "blocked",
                                "--gate-kind",
                                kind,
                                "--gate-ref",
                                ref,
                                "--priority",
                                "low",
                                "--work-kind",
                                "chore",
                                "--apply",
                            ]
                        )
                    self.assertEqual(
                        rc, 0, f"Failed for {kind}: stderr={err.getvalue()}"
                    )
                    written_file = _extract_wrote_path(out.getvalue())
                    self.assertTrue(
                        written_file.is_file(), f"File does not exist: {written_file}"
                    )
                    content = written_file.read_text(encoding="utf-8")
                    self.assertIn(f"- Gate-Kind: {kind}\n", content)
                    self.assertIn(f"- Gate-Ref: {ref}\n", content)

    def test_created_valid_blocked_item_passes_check(self):
        """(d) a created valid blocked item passes aw backlog check (rc 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = cli.main(
                    [
                        "backlog",
                        "new",
                        "--dir",
                        str(repo),
                        "--summary",
                        "date blocked item for check",
                        "--status",
                        "blocked",
                        "--gate-kind",
                        "date",
                        "--gate-ref",
                        "2026-12-01",
                        "--priority",
                        "low",
                        "--work-kind",
                        "chore",
                        "--apply",
                    ]
                )
            self.assertEqual(rc, 0)
            out_chk, err_chk = io.StringIO(), io.StringIO()
            with redirect_stdout(out_chk), redirect_stderr(err_chk):
                rc_chk = cli.main(["backlog", "check", "--dir", str(repo)])
            self.assertEqual(
                rc_chk,
                0,
                f"backlog check failed: stdout={out_chk.getvalue()} stderr={err_chk.getvalue()}",
            )

    def test_open_status_with_invalid_gate_flags_writes_no_gate_lines(self):
        """(e) --status open with invalid gate flags writes NO - Gate-Kind: or - Gate-Ref: line."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = _setup_repo(Path(tmp))
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                cli.main(
                    [
                        "backlog",
                        "new",
                        "--dir",
                        str(repo),
                        "--summary",
                        "open item with discarded gate flags",
                        "--status",
                        "open",
                        "--gate-kind",
                        "bogus-kind",
                        "--gate-ref",
                        "notadate",
                        "--priority",
                        "low",
                        "--work-kind",
                        "chore",
                        "--apply",
                    ]
                )
            written_file = _extract_wrote_path(out.getvalue())
            self.assertTrue(
                written_file.is_file(), f"File does not exist: {written_file}"
            )
            content = written_file.read_text(encoding="utf-8")
            self.assertNotIn("- Gate-Kind:", content)
            self.assertNotIn("- Gate-Ref:", content)


if __name__ == "__main__":
    unittest.main()
