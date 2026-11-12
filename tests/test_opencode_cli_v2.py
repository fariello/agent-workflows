"""Outcome tests for `opencode_cli`: the OpenCode v1/v2 argv adapter.

OpenCode v2 rejects `run --dir` and `run --variant` ("Unrecognized flag") and moved `export` under
`session`. These tests drive the adapter's public functions and assert on the argv they return,
including a fake `opencode` binary that answers `--version` like the real v1 and v2 builds.
"""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import opencode_cli

V1_RUN = [
    "opencode",
    "run",
    "--session",
    "ses_1",
    "--dir",
    "/w",
    "--format",
    "json",
    "--model",
    "prov/m",
    "--variant",
    "high",
    "--auto",
    "--title",
    "t",
    "--file",
    "/w/p.md",
    "--",
    "prompt --dir /x --variant low",
]


class AdaptRunArgvTests(unittest.TestCase):
    def test_v2_drops_dir_and_folds_variant_into_model(self) -> None:
        out = opencode_cli.adapt_run_argv(V1_RUN, major=2)
        self.assertEqual(
            out,
            [
                "opencode",
                "run",
                "--session",
                "ses_1",
                "--format",
                "json",
                "--model",
                "prov/m#high",
                "--auto",
                "--title",
                "t",
                "--file",
                "/w/p.md",
                "--",
                "prompt --dir /x --variant low",
            ],
        )

    def test_v1_and_unknown_are_unchanged(self) -> None:
        self.assertEqual(opencode_cli.adapt_run_argv(V1_RUN, major=1), V1_RUN)
        with mock.patch.object(opencode_cli, "major_version", return_value=None):
            self.assertEqual(opencode_cli.adapt_run_argv(V1_RUN), V1_RUN)

    def test_v2_variant_without_model_is_dropped(self) -> None:
        argv = ["opencode", "run", "--variant", "low", "--", "p"]
        self.assertEqual(
            opencode_cli.adapt_run_argv(argv, major=2), ["opencode", "run", "--", "p"]
        )

    def test_v2_model_already_carrying_variant_is_kept(self) -> None:
        argv = ["opencode", "run", "--model", "p/m#low", "--variant", "high", "--", "x"]
        self.assertEqual(
            opencode_cli.adapt_run_argv(argv, major=2),
            ["opencode", "run", "--model", "p/m#low", "--", "x"],
        )

    def test_embedded_run_under_wrapper_prefix(self) -> None:
        wrapped = ["bwrap", "--ro-bind", "/", "/"] + V1_RUN
        out = opencode_cli.adapt_embedded_run_argv(wrapped, "opencode", 2)
        self.assertEqual(out[:4], ["bwrap", "--ro-bind", "/", "/"])
        self.assertNotIn("--dir", out[4 : out.index("--")])
        self.assertEqual(
            opencode_cli.adapt_embedded_run_argv(wrapped, "opencode", None), wrapped
        )

    def test_export_argv_by_generation(self) -> None:
        self.assertEqual(
            opencode_cli.export_argv("oc", "ses_1", major=2),
            ["oc", "session", "export", "ses_1"],
        )
        self.assertEqual(
            opencode_cli.export_argv("oc", "ses_1", major=1), ["oc", "export", "ses_1"]
        )

    def test_parse_major(self) -> None:
        self.assertEqual(opencode_cli.parse_major("opencode v2.2.7"), 2)
        self.assertEqual(opencode_cli.parse_major("1.14.3\n"), 1)
        self.assertIsNone(opencode_cli.parse_major("no version here"))


class MajorVersionProbeTests(unittest.TestCase):
    def _fake(self, tmp: Path, text: str) -> str:
        p = tmp / "opencode"
        p.write_text(f"#!/bin/sh\necho '{text}'\n", encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
        return str(p)

    def test_reads_real_binary_version_outside_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            v2 = self._fake(Path(d), "opencode v2.2.7")
            opencode_cli.major_version.cache_clear()
            env = {k: v for k, v in os.environ.items() if k != "PYTEST_CURRENT_TEST"}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(opencode_cli.major_version(v2), 2)
                self.assertTrue(opencode_cli.is_v2(v2))
            opencode_cli.major_version.cache_clear()

    def test_never_spawns_under_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            v2 = self._fake(Path(d), "opencode v2.2.7")
            opencode_cli.major_version.cache_clear()
            with mock.patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "x"}):
                self.assertIsNone(opencode_cli.major_version(v2))
            opencode_cli.major_version.cache_clear()


if __name__ == "__main__":
    unittest.main()
