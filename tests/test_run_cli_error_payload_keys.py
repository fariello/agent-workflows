"""Behavioral tests for the run_cli._emit_error machine JSON payload key set.

Restores behavioral coverage (P16) that every machine-mode error emitted through
`run_cli._emit_error` without `extra` carries exactly the keys {"ok", "error", "exit_code"},
with ok is False and exit_code equal to the process's returned code, across leaves and in
both --agent and --json renderers (IPD e97wtz / backlog n2fx9i).
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from agent_workflows import cli, run_cli
from tests import support


class TestRunCliErrorPayloadKeys(unittest.TestCase):
    """Assert exact bare machine error payload key set and values across leaves and renderers."""

    def setUp(self) -> None:
        support.declare_execution_role(self)
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _cli(self, *argv: str) -> tuple[int, str]:
        with patch("sys.stdout", new_callable=io.StringIO) as out:
            rc = cli.main(list(argv))
        return rc, out.getvalue()

    def _payload(self, out: str, renderer: str) -> dict[str, Any]:
        if renderer == "--json":
            return json.loads(out)
        lines = [line for line in out.strip().splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"No non-empty lines found in output: {out!r}")
        return json.loads(lines[-1])

    def test_unknown_target_payload_has_exactly_the_three_keys(self) -> None:
        leaves = (
            ("runs", "verify-ledger"),
            ("runs", "show"),
            ("runs", "status"),
            ("run", "cancel"),
            ("run", "start"),
        )
        renderers = ("--agent", "--json")
        problems: list[str] = []

        for leaf in leaves:
            for renderer in renderers:
                with self.subTest(leaf=leaf, renderer=renderer):
                    rc, out = self._cli(
                        *leaf, "totalgibberish", "--dir", str(self.tmp), renderer
                    )
                    row_errors: list[str] = []
                    payload: dict[str, Any] = {}
                    try:
                        payload = self._payload(out, renderer)
                        if rc != run_cli.EXIT_INVALID_INVOCATION:
                            row_errors.append(
                                f"rc {rc} != {run_cli.EXIT_INVALID_INVOCATION}"
                            )
                        if set(payload.keys()) != {"ok", "error", "exit_code"}:
                            row_errors.append(
                                f"keys {set(payload.keys())} != {{'ok', 'error', 'exit_code'}}"
                            )
                        if payload.get("ok") is not False:
                            row_errors.append(f"ok {payload.get('ok')} is not False")
                        if payload.get("exit_code") != rc:
                            row_errors.append(
                                f"exit_code {payload.get('exit_code')} != {rc}"
                            )
                        err = payload.get("error")
                        if not isinstance(err, str) or not err:
                            row_errors.append(f"error is not non-empty str: {err!r}")
                        else:
                            if err.startswith("error: "):
                                row_errors.append(
                                    f"error {err!r} starts with 'error: '"
                                )
                            if "ledger.jsonl" not in err:
                                row_errors.append(
                                    f"error {err!r} does not contain 'ledger.jsonl'"
                                )
                    except Exception as e:
                        row_errors.append(f"exception: {e}")

                    if row_errors:
                        problems.append(
                            f"{' '.join(leaf)} {renderer}: " + "; ".join(row_errors)
                        )

                    self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                    self.assertEqual(set(payload), {"ok", "error", "exit_code"})
                    self.assertIs(payload["ok"], False)
                    self.assertEqual(payload["exit_code"], rc)
                    self.assertIsInstance(payload["error"], str)
                    self.assertTrue(payload["error"])
                    self.assertFalse(payload["error"].startswith("error: "))
                    self.assertIn("ledger.jsonl", payload["error"])

        self.assertEqual(
            problems, [], f"The following leaves/renderers drifted: {problems}"
        )

    def test_explicit_absent_path_payload_has_exactly_the_three_keys(self) -> None:
        rc, out = self._cli(
            "runs",
            "verify-ledger",
            str(self.tmp / "nowhere" / "ledger.jsonl"),
            "--agent",
        )
        payload = self._payload(out, "--agent")
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        self.assertEqual(set(payload), {"ok", "error", "exit_code"})
        self.assertIs(payload["ok"], False)
        self.assertEqual(payload["exit_code"], rc)
        self.assertIn("not found", payload["error"])
        self.assertNotIn("no driver run writes one", payload["error"])

    def test_empty_ledger_payload_has_exactly_the_three_keys(self) -> None:
        empty_ledger = self.tmp / "ledger.jsonl"
        empty_ledger.write_text("")
        leaves = (
            ("runs", "next"),
            ("runs", "status"),
            ("runs", "resume"),
            ("run", "cancel"),
        )
        for leaf in leaves:
            with self.subTest(leaf=leaf):
                rc, out = self._cli(*leaf, str(empty_ledger), "--agent")
                payload = self._payload(out, "--agent")
                self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                self.assertEqual(set(payload), {"ok", "error", "exit_code"})
                self.assertIs(payload["ok"], False)
                self.assertEqual(payload["exit_code"], rc)
                self.assertEqual(payload["error"], "ledger is empty")

    def test_human_stream_is_not_json(self) -> None:
        rc, out = self._cli("runs", "status", "totalgibberish", "--dir", str(self.tmp))
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        self.assertTrue(out.startswith("error: "))
        with self.assertRaises(ValueError):
            json.loads(out)
