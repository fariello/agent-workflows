"""Behavioral tests for the run_cli._emit_error machine JSON payload key set.

Restores behavioral coverage (P16) that every machine-mode error emitted through
`run_cli._emit_error` without `extra` splits by renderer:
--json emits a bare {"ok", "error", "exit_code"} dict, while --agent emits a
schema-valid aw.agent/v1 error record that retains the three legacy keys and
honors --fields (IPD 2t033b / backlog jndec6).
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from agent_workflows import agent_schema, cli, run_cli
from tests import support

SAMPLE_WORKFLOW = {
    "id": "wf-test-01",
    "steps": [{"id": "S-01", "action": "run tests", "depends_on": [], "satisfies": []}],
    "requirements": [{"id": "R-01", "description": "basic requirement"}],
}


def _create_scratch_repo(path: Path) -> Path:
    (path / ".aw" / "records").mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=str(path),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return path


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

    def test_unknown_target_payload_keys_per_renderer(self) -> None:
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
                        if renderer == "--json":
                            if set(payload.keys()) != {"ok", "error", "exit_code"}:
                                row_errors.append(
                                    f"keys {set(payload.keys())} != {{'ok', 'error', 'exit_code'}}"
                                )
                            if payload.get("ok") is not False:
                                row_errors.append(
                                    f"ok {payload.get('ok')} is not False"
                                )
                            if payload.get("exit_code") != rc:
                                row_errors.append(
                                    f"exit_code {payload.get('exit_code')} != {rc}"
                                )
                        else:  # --agent
                            lines = [
                                line
                                for line in out.strip().splitlines()
                                if line.strip()
                            ]
                            if len(lines) != 1:
                                row_errors.append(f"expected 1 line, got {len(lines)}")
                            validation = agent_schema.validate_agent_record(payload)
                            if validation:
                                row_errors.append(f"validation failed: {validation}")
                            if payload.get("kind") != "error":
                                row_errors.append(
                                    f"kind {payload.get('kind')} != 'error'"
                                )
                            if payload.get("outcome") != "cannot-run":
                                row_errors.append(
                                    f"outcome {payload.get('outcome')} != 'cannot-run'"
                                )
                            expected_cmd = " ".join(leaf)
                            if payload.get("cmd") != expected_cmd:
                                row_errors.append(
                                    f"cmd {payload.get('cmd')} != {expected_cmd}"
                                )
                            if not (
                                payload.get("exit")
                                == payload.get("exit_code")
                                == rc
                                == 2
                            ):
                                row_errors.append(
                                    f"exit/exit_code mismatch: exit={payload.get('exit')}, exit_code={payload.get('exit_code')}, rc={rc}"
                                )
                            if payload.get("ok") is not False:
                                row_errors.append(
                                    f"ok {payload.get('ok')} is not False"
                                )
                            expected_next = f"aw {expected_cmd} --help"
                            if payload.get("next") != expected_next:
                                row_errors.append(
                                    f"next {payload.get('next')} != {expected_next}"
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
                    if renderer == "--json":
                        self.assertEqual(set(payload), {"ok", "error", "exit_code"})
                        self.assertEqual(payload["exit_code"], rc)
                    else:
                        lines = [
                            line for line in out.strip().splitlines() if line.strip()
                        ]
                        self.assertEqual(len(lines), 1)
                        self.assertEqual(
                            agent_schema.validate_agent_record(payload), []
                        )
                        self.assertEqual(payload["kind"], "error")
                        self.assertEqual(payload["outcome"], "cannot-run")
                        self.assertEqual(payload["cmd"], " ".join(leaf))
                        self.assertEqual(payload["exit"], 2)
                        self.assertEqual(payload["exit_code"], 2)
                        self.assertEqual(payload["next"], f"aw {' '.join(leaf)} --help")
                    self.assertIs(payload["ok"], False)
                    self.assertIsInstance(payload["error"], str)
                    self.assertTrue(payload["error"])
                    self.assertFalse(payload["error"].startswith("error: "))
                    self.assertIn("ledger.jsonl", payload["error"])

        self.assertEqual(
            problems, [], f"The following leaves/renderers drifted: {problems}"
        )

    def test_explicit_absent_path_payload_keys_per_renderer(self) -> None:
        rc, out = self._cli(
            "runs",
            "verify-ledger",
            str(self.tmp / "nowhere" / "ledger.jsonl"),
            "--agent",
        )
        lines = [line for line in out.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        payload = self._payload(out, "--agent")
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        self.assertEqual(agent_schema.validate_agent_record(payload), [])
        self.assertEqual(payload["kind"], "error")
        self.assertEqual(payload["outcome"], "cannot-run")
        self.assertEqual(payload["cmd"], "runs verify-ledger")
        self.assertEqual(payload["exit"], 2)
        self.assertEqual(payload["exit_code"], 2)
        self.assertIs(payload["ok"], False)
        self.assertEqual(payload["next"], "aw runs verify-ledger --help")
        self.assertIn("not found", payload["error"])
        self.assertNotIn("no driver run writes one", payload["error"])

    def test_empty_ledger_payload_keys_per_renderer(self) -> None:
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
                lines = [line for line in out.strip().splitlines() if line.strip()]
                self.assertEqual(len(lines), 1)
                payload = self._payload(out, "--agent")
                self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                self.assertEqual(agent_schema.validate_agent_record(payload), [])
                self.assertEqual(payload["kind"], "error")
                self.assertEqual(payload["outcome"], "cannot-run")
                self.assertEqual(payload["cmd"], " ".join(leaf))
                self.assertEqual(payload["exit"], 2)
                self.assertEqual(payload["exit_code"], 2)
                self.assertIs(payload["ok"], False)
                self.assertEqual(payload["next"], f"aw {' '.join(leaf)} --help")
                self.assertEqual(payload["error"], "ledger is empty")

    def test_fields_projection_honored_under_agent_and_ignored_under_json(self) -> None:
        invocations = (
            ("runs", "status", "totalgibberish", "--dir", str(self.tmp)),
            ("run", "cancel", "totalgibberish", "--dir", str(self.tmp)),
        )
        for inv in invocations:
            with self.subTest(inv=inv, renderer="--agent"):
                rc, out = self._cli(*inv, "--agent", "--fields", "cmd")
                self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                lines = [line for line in out.strip().splitlines() if line.strip()]
                self.assertEqual(len(lines), 1)
                payload = json.loads(lines[0])
                self.assertEqual(agent_schema.validate_agent_record(payload), [])
                self.assertTrue(
                    set(payload) <= agent_schema._PRESERVED_FIELDS | {"cmd"}
                )
                self.assertNotIn("error", payload)
            with self.subTest(inv=inv, renderer="--json"):
                rc, out = self._cli(*inv, "--json", "--fields", "cmd")
                self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                payload = json.loads(out)
                self.assertEqual(set(payload), {"ok", "error", "exit_code"})

    def test_ledger_read_failure_emits_unprefixed_error(self) -> None:
        ledger = self.tmp / "ledger.jsonl"
        ledger.write_text("")
        with patch(
            "agent_workflows.run_ledger_store.RunLedgerStore.read_records",
            side_effect=OSError("boom"),
        ):
            for cmd in (("runs", "show"), ("runs", "evidence")):
                with self.subTest(cmd=cmd, renderer="--agent"):
                    rc, out = self._cli(*cmd, str(ledger), "--agent")
                    self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                    lines = [line for line in out.strip().splitlines() if line.strip()]
                    self.assertEqual(len(lines), 1)
                    payload = json.loads(lines[0])
                    self.assertEqual(agent_schema.validate_agent_record(payload), [])
                    self.assertEqual(payload["kind"], "error")
                    self.assertTrue(
                        payload["error"].startswith("failed to read ledger:")
                    )
                    self.assertFalse(payload["error"].startswith("error: "))

                with self.subTest(cmd=cmd, renderer="--json"):
                    rc, out = self._cli(*cmd, str(ledger), "--json")
                    self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
                    payload = json.loads(out)
                    self.assertTrue(
                        payload["error"].startswith("failed to read ledger:")
                    )
                    self.assertFalse(payload["error"].startswith("error: "))

    def test_home_path_redacted_in_error_payload(self) -> None:
        p = "/".join(["", "home", "someuser", "nope.json"])
        rc, out = self._cli(
            "run", "init", "--workflow", p, "--dir", str(self.tmp), "--agent"
        )
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        lines = [line for line in out.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(agent_schema.validate_agent_record(payload), [])
        self.assertNotIn("someuser", out)

    def test_non_two_refusal_stays_bare_under_agent(self) -> None:
        scratch = self.tmp / "scratch_repo"
        scratch.mkdir()
        _create_scratch_repo(scratch)
        wf = scratch / "workflow.json"
        wf.write_text(json.dumps(SAMPLE_WORKFLOW))
        rc1, _out1 = self._cli(
            "run",
            "init",
            "--workflow",
            str(wf),
            "--run-id",
            "run-0123456789abcdef",
            "--dir",
            str(scratch),
            "--agent",
        )
        self.assertEqual(rc1, run_cli.EXIT_OK)
        rc2, out2 = self._cli(
            "run",
            "init",
            "--workflow",
            str(wf),
            "--run-id",
            "run-0123456789abcdef",
            "--dir",
            str(scratch),
            "--agent",
        )
        self.assertEqual(rc2, run_cli.EXIT_OPERATIONAL)
        payload = json.loads(out2.strip().splitlines()[-1])
        self.assertIs(payload["ok"], False)
        self.assertEqual(payload["exit_code"], 6)
        self.assertNotIn("schema", payload)

    def test_human_stream_is_not_json(self) -> None:
        rc, out = self._cli("runs", "status", "totalgibberish", "--dir", str(self.tmp))
        self.assertEqual(rc, run_cli.EXIT_INVALID_INVOCATION)
        self.assertTrue(out.startswith("error: "))
        with self.assertRaises(ValueError):
            json.loads(out)
