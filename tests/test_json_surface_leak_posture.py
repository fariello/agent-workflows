"""Behavioral tests for the --json and --agent machine surface leak posture.

Pins:
- The agreement between redact_home_paths and _HOME_PATH_RE across all enumerated home classes.
- The leak posture of all CommandResult channels under JsonRenderer (envelope redacted, data exempt).
- Preservation of container types and scalar values in Evidence.value under redaction.
- Redaction of the next channel in to_agent_record without crashing.
- End-to-end CLI subprocess verification for --json and --agent.

Leak tokens are assembled from fragments at runtime so this test file contains no literal leak (F-20).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from typing import Any, Dict

from agent_workflows.agent_schema import (
    _HOME_PATH_RE,
    assert_valid_agent_record,
    redact_home_paths,
    validate_agent_record,
)
from agent_workflows.renderers import JsonRenderer
from agent_workflows.result_types import (
    Change,
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
)


def _frag(part1: str, part2: str) -> str:
    """Helper to assemble sensitive path prefixes without containing literal leak strings."""
    return part1 + part2


# Planted path fragments assembled dynamically at runtime
_POSIX_ROOT = _frag("/ho", "me/")
_MAC_ROOT = _frag("/Use", "rs/")
_WIN_BS_ROOT = _frag("C:\\Use", "rs\\")
_WIN_FS_ROOT = _frag("C:/Use", "rs/")

_USERNAME = "tester"
_TAIL = "project/file.txt"

PLANTED_POSIX = f"{_POSIX_ROOT}{_USERNAME}/{_TAIL}"
PLANTED_MAC = f"{_MAC_ROOT}{_USERNAME}/{_TAIL}"
PLANTED_WIN_BS = f"{_WIN_BS_ROOT}{_USERNAME}\\{_TAIL.replace('/', chr(92))}"
PLANTED_WIN_FS = f"{_WIN_FS_ROOT}{_USERNAME}/{_TAIL}"


class HomePathRedactionAgreementTests(unittest.TestCase):
    """Test agreement between redact_home_paths and _HOME_PATH_RE (E-02, V-02).

    An unenumerated fourth class is not caught by any test and is a known bound.
    """

    CLASS_CASES = {
        "posix": PLANTED_POSIX,
        "macos": PLANTED_MAC,
        "windows_backslash": PLANTED_WIN_BS,
        "windows_forward_slash": PLANTED_WIN_FS,
    }

    def test_posix_class_agreement(self) -> None:
        raw = self.CLASS_CASES["posix"]
        self.assertIsNotNone(
            _HOME_PATH_RE.search(raw), "Control: detector must match raw POSIX path"
        )
        redacted = redact_home_paths(raw)
        self.assertIsNone(
            _HOME_PATH_RE.search(redacted),
            f"POSIX path must be clean after redaction: {redacted}",
        )
        self.assertEqual(
            redact_home_paths(redacted), redacted, "Redaction must be idempotent"
        )

    def test_macos_class_agreement(self) -> None:
        raw = self.CLASS_CASES["macos"]
        self.assertIsNotNone(
            _HOME_PATH_RE.search(raw), "Control: detector must match raw macOS path"
        )
        redacted = redact_home_paths(raw)
        self.assertIsNone(
            _HOME_PATH_RE.search(redacted),
            f"macOS path must be clean after redaction: {redacted}",
        )
        self.assertEqual(
            redact_home_paths(redacted), redacted, "Redaction must be idempotent"
        )

    def test_windows_backslash_class_agreement(self) -> None:
        raw = self.CLASS_CASES["windows_backslash"]
        self.assertIsNotNone(
            _HOME_PATH_RE.search(raw),
            "Control: detector must match raw Windows backslash path",
        )
        redacted = redact_home_paths(raw)
        self.assertIsNone(
            _HOME_PATH_RE.search(redacted),
            f"Windows backslash path must be clean after redaction: {redacted}",
        )
        self.assertEqual(
            redact_home_paths(redacted), redacted, "Redaction must be idempotent"
        )

    def test_windows_forward_slash_class_agreement(self) -> None:
        raw = self.CLASS_CASES["windows_forward_slash"]
        self.assertIsNotNone(
            _HOME_PATH_RE.search(raw),
            "Control: detector must match raw Windows forward slash path",
        )
        redacted = redact_home_paths(raw)
        self.assertIsNone(
            _HOME_PATH_RE.search(redacted),
            f"Windows forward slash path must be clean after redaction: {redacted}",
        )
        self.assertEqual(
            redact_home_paths(redacted), redacted, "Redaction must be idempotent"
        )

    def test_embedded_and_already_redacted_paths(self) -> None:
        embedded = f"run aw foo {PLANTED_POSIX} --verbose"
        self.assertIsNotNone(_HOME_PATH_RE.search(embedded))
        redacted_embedded = redact_home_paths(embedded)
        self.assertIsNone(_HOME_PATH_RE.search(redacted_embedded))
        self.assertEqual(redacted_embedded, f"run aw foo ~/{_TAIL} --verbose")
        self.assertEqual(redact_home_paths(redacted_embedded), redacted_embedded)

        already_tilde = f"~/{_TAIL}"
        self.assertEqual(redact_home_paths(already_tilde), already_tilde)
        self.assertIsNone(_HOME_PATH_RE.search(already_tilde))

        already_win = f"{_WIN_BS_ROOT}~\\{_TAIL.replace('/', chr(92))}"
        self.assertEqual(redact_home_paths(already_win), already_win)
        self.assertIsNone(_HOME_PATH_RE.search(already_win))

    def test_no_path_and_non_string_types(self) -> None:
        no_path = "no home path here: /var/log/syslog /etc/hosts"
        self.assertEqual(redact_home_paths(no_path), no_path)
        self.assertIsNone(_HOME_PATH_RE.search(no_path))

        self.assertIsNone(redact_home_paths(None))
        self.assertEqual(redact_home_paths(42), 42)
        self.assertEqual(redact_home_paths(3.14), 3.14)
        self.assertIs(redact_home_paths(True), True)


class JsonSurfaceChannelMatrixTests(unittest.TestCase):
    """Test every CommandResult channel under JsonRenderer (E-03, E-04, E-06, V-03, V-04)."""

    def setUp(self) -> None:
        self.result = CommandResult(
            command="test",
            status="findings",
            exit_code=1,
            summary=f"Run check with {PLANTED_POSIX}",
            diagnostics=[
                Diagnostic(
                    location=PLANTED_POSIX,
                    rule="check.test-rule",
                    detail=f"Found violation at {PLANTED_POSIX}",
                    fix=f"aw ipd lint {PLANTED_POSIX} --phase author",
                )
            ],
            changes=[
                Change(
                    path=PLANTED_POSIX,
                    kind="modify",
                    detail=f"Modified file at {PLANTED_POSIX}",
                    applied=True,
                )
            ],
            evidence=[
                Evidence(
                    key="evidence-key",
                    value=f"Evidence path is {PLANTED_POSIX}",
                    detail=f"Evidence detail has {PLANTED_POSIX}",
                )
            ],
            next_actions=[
                NextAction(
                    command=f"aw ipd lint {PLANTED_POSIX} --phase author",
                    description=f"Lint plan at {PLANTED_POSIX}",
                )
            ],
            data={"logical_roots": [PLANTED_POSIX], "exempt_path": PLANTED_POSIX},
        )
        rendered_str = JsonRenderer().render(self.result)
        self.payload: Dict[str, Any] = json.loads(rendered_str)

    def test_summary_redacted(self) -> None:
        summary_val = self.payload["summary"]
        self.assertIsNone(_HOME_PATH_RE.search(summary_val))
        self.assertIn("Run check with ~/", summary_val)

    def test_diagnostics_channels_redacted(self) -> None:
        diag = self.payload["diagnostics"][0]
        self.assertIsNone(_HOME_PATH_RE.search(diag["location"]))
        self.assertIsNone(_HOME_PATH_RE.search(diag["detail"]))
        self.assertIsNone(_HOME_PATH_RE.search(diag["fix"]))
        self.assertIn("Found violation at ~/", diag["detail"])
        self.assertEqual(diag["fix"], f"aw ipd lint ~/{_TAIL} --phase author")

    def test_changes_channels_redacted(self) -> None:
        change = self.payload["changes"][0]
        self.assertIsNone(_HOME_PATH_RE.search(change["path"]))
        self.assertIsNone(_HOME_PATH_RE.search(change["detail"]))
        self.assertIn("Modified file at ~/", change["detail"])

    def test_evidence_channels_redacted(self) -> None:
        ev = self.payload["evidence"][0]
        self.assertIsNone(_HOME_PATH_RE.search(str(ev["value"])))
        self.assertIsNone(_HOME_PATH_RE.search(ev["detail"]))
        self.assertIn("Evidence path is ~/", ev["value"])
        self.assertIn("Evidence detail has ~/", ev["detail"])

    def test_next_actions_channels_redacted(self) -> None:
        na = self.payload["next_actions"][0]
        self.assertIsNone(_HOME_PATH_RE.search(na["command"]))
        self.assertIsNone(_HOME_PATH_RE.search(na["description"]))
        self.assertEqual(na["command"], f"aw ipd lint ~/{_TAIL} --phase author")
        self.assertIn("Lint plan at ~/", na["description"])

    def test_data_channel_exempt_and_unredacted(self) -> None:
        data_val = self.payload["data"]
        # Invariant: data remains an unredacted passthrough (approved spec kw5y2s)
        self.assertIsNotNone(
            _HOME_PATH_RE.search(data_val["exempt_path"]),
            "data must retain raw home path to satisfy spec kw5y2s Section 2.4",
        )
        self.assertIsNotNone(
            _HOME_PATH_RE.search(data_val["logical_roots"][0]),
            "data.logical_roots must retain absolute paths",
        )


class EvidenceValueContainerShapesTests(unittest.TestCase):
    """Test that Evidence.value container shapes and types survive redaction (E-08, V-08)."""

    def test_string_shape(self) -> None:
        ev = Evidence(key="k", value=PLANTED_POSIX)
        val = ev.to_dict()["value"]
        self.assertIsInstance(val, str)
        self.assertIsNone(_HOME_PATH_RE.search(val))
        self.assertEqual(val, f"~/{_TAIL}")

    def test_dict_shape(self) -> None:
        ev = Evidence(
            key="k", value={"count": 5, "path": PLANTED_POSIX, "label": "test"}
        )
        val = ev.to_dict()["value"]
        self.assertIsInstance(val, dict)
        self.assertIsNone(_HOME_PATH_RE.search(str(val)))
        self.assertEqual(val["count"], 5)
        self.assertEqual(val["path"], f"~/{_TAIL}")
        self.assertEqual(val["label"], "test")

    def test_list_shape(self) -> None:
        ev = Evidence(key="k", value=[PLANTED_POSIX, 123, "plain"])
        val = ev.to_dict()["value"]
        self.assertIsInstance(val, list)
        self.assertIsNone(_HOME_PATH_RE.search(str(val)))
        self.assertEqual(val[0], f"~/{_TAIL}")
        self.assertEqual(val[1], 123)
        self.assertEqual(val[2], "plain")

    def test_nested_container_shape(self) -> None:
        ev = Evidence(
            key="k",
            value=[{"roots": [PLANTED_POSIX, PLANTED_WIN_BS]}, {"other": 99}],
        )
        val = ev.to_dict()["value"]
        self.assertIsInstance(val, list)
        self.assertIsInstance(val[0], dict)
        self.assertIsNone(_HOME_PATH_RE.search(str(val)))
        self.assertEqual(val[0]["roots"][0], f"~/{_TAIL}")
        self.assertEqual(val[1]["other"], 99)

    def test_scalar_shapes_byte_identical(self) -> None:
        scalars = [42, 3.14, True, False, None]
        for s in scalars:
            ev = Evidence(key="scalar", value=s)
            val = ev.to_dict()["value"]
            self.assertEqual(val, s)
            self.assertIs(type(val), type(s))


class AgentRecordNextRedactionTests(unittest.TestCase):
    """Test that CommandResult.to_agent_record redacts the next channel (E-07, V-07)."""

    def test_to_agent_record_redacts_next_command(self) -> None:
        cmd_str = f"aw ipd lint {PLANTED_POSIX} --phase author"
        res = CommandResult(
            command="check",
            status="findings",
            exit_code=1,
            next_actions=[NextAction(command=cmd_str)],
        )
        rec = res.to_agent_record()
        self.assertIsNone(_HOME_PATH_RE.search(rec["next"]))
        self.assertEqual(rec["next"], f"aw ipd lint ~/{_TAIL} --phase author")
        self.assertEqual(validate_agent_record(rec), [])
        assert_valid_agent_record(rec)


class CliSubprocessLeakPostureTests(unittest.TestCase):
    """End-to-end CLI subprocess execution asserting leak postures (E-06, V-06)."""

    def test_cli_json_surface_envelope_clean(self) -> None:
        # Run aw check --json in a subprocess
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "check", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertIn(
            proc.returncode, (0, 1), f"Command failed unexpectedly: {proc.stderr}"
        )
        data = json.loads(proc.stdout)

        def assert_no_leaks(obj: Any, path: str = "") -> None:
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if path == "" and k == "data":
                        continue  # data is explicitly exempt
                    assert_no_leaks(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    assert_no_leaks(item, f"{path}[{i}]")
            elif isinstance(obj, str):
                self.assertIsNone(
                    _HOME_PATH_RE.search(obj),
                    f"Home path leak detected at {path}: {obj}",
                )

        assert_no_leaks(data)

    def test_aw_check_plans_agent_no_crash(self) -> None:
        # Run aw check plans --agent with PYTHONHASHSEED=1 which previously crashed on field 'next'
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "1"
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "check", "plans", "--agent"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertNotIn(
            "ValueError", proc.stderr, "stderr must not contain ValueError traceback"
        )
        lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
        self.assertGreaterEqual(len(lines), 1, "Must emit at least one line on stdout")
        rec = json.loads(lines[0])
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(validate_agent_record(rec), [])
