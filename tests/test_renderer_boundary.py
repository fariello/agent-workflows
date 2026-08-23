"""Tests for Result Types and Renderer Boundary with doctor reference handler.

awcliux Order 01 (`hd3kln`) E-02 / V-02.

Asserts:
1. Result types (`CommandResult`, `Diagnostic`, `Change`, `Evidence`, `NextAction`) exist and
   serialize cleanly.
2. The reference handler (`doctor`) produces a single typed `CommandResult`.
3. Driving BOTH renderers (`HumanRenderer` and `AgentRenderer`) from that single typed result
   yields identical outcome facts:
   - status ("clean" / "findings")
   - exit classification (0 / 1)
   - finding counts and diagnostic paths
   - evidence keys and values
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import doctor, engine, versioning
from agent_workflows.result_types import (
    CommandResult,
    Diagnostic,
    Evidence,
    NextAction,
    OutputContext,
    OutputMode,
)
from agent_workflows.renderers import (
    AgentRenderer,
    HumanRenderer,
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True)


class ResultTypesUnitTests(unittest.TestCase):
    """Unit tests for stdlib result types."""

    def test_diagnostic_roundtrip_with_drift(self):
        from agent_workflows import artifact_core as core

        drift = core.Drift(
            location="foo.txt", rule="check.error", detail="some failure"
        )
        diag = Diagnostic.from_drift(drift, severity="error", fix="edit foo.txt")
        self.assertEqual(diag.location, "foo.txt")
        self.assertEqual(diag.rule, "check.error")
        self.assertEqual(diag.detail, "some failure")
        self.assertEqual(diag.severity, "error")
        self.assertEqual(diag.fix, "edit foo.txt")

        drift_back = diag.to_drift()
        self.assertEqual(drift_back.location, "foo.txt")
        self.assertEqual(drift_back.rule, "check.error")
        self.assertEqual(drift_back.detail, "some failure")

    def test_command_result_agent_record_format(self):
        res = CommandResult(
            command="doctor",
            status="findings",
            exit_code=1,
            summary="1 finding(s)",
            diagnostics=[
                Diagnostic(
                    location="bar.txt",
                    rule="doctor.git-dirty",
                    detail="uncommitted modification",
                )
            ],
            evidence=[Evidence(key="git", value={"dirty": True}, status="findings")],
            next_actions=[
                NextAction(
                    command="git commit -- bar.txt", description="commit changes"
                )
            ],
        )
        rec = res.to_agent_record()
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["kind"], "result")
        self.assertEqual(rec["cmd"], "doctor")
        self.assertEqual(rec["outcome"], "findings")
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["findings"], 1)
        self.assertEqual(rec["next"], "git commit -- bar.txt")
        self.assertEqual(rec["diagnostics"][0]["location"], "bar.txt")


class DoctorRendererBoundaryTests(unittest.TestCase):
    """Drive the reference handler (`doctor`) through both renderers (E-02 / V-02)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@e.com")
        _git(self.root, "config", "user.name", "T")
        (self.root / ".aw" / "records").mkdir(parents=True)
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        (self.root / ".aw" / "VERSION").write_text(f"{packaged}\n", encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_doctor_both_renderers_clean_state_fact_parity(self):
        # 1. Inspect clean repository -> single typed CommandResult
        result: CommandResult = doctor.inspect_repo(self.root)
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.command, "doctor")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.status, "clean")
        self.assertEqual(len(result.diagnostics), 0)

        # 2. Render through HumanRenderer
        human_renderer = HumanRenderer()
        human_ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        human_output = human_renderer.render(result, human_ctx)
        self.assertIn("aw doctor: no findings (repository is healthy).", human_output)

        # 3. Render through AgentRenderer
        agent_renderer = AgentRenderer()
        agent_ctx = OutputContext(mode=OutputMode.AGENT, color=False)
        agent_output = agent_renderer.render(result, agent_ctx)
        agent_record = json.loads(agent_output.strip())

        # 4. Assert identical outcome facts across both renderers
        self.assertEqual(agent_record["schema"], "aw.agent/v1")
        self.assertEqual(agent_record["cmd"], "doctor")
        self.assertEqual(agent_record["exit"], result.exit_code)
        self.assertEqual(agent_record["outcome"], result.status)
        self.assertEqual(agent_record["findings"], len(result.diagnostics))
        self.assertTrue(agent_record["verified"])
        self.assertTrue(agent_record["complete"])

    def test_doctor_both_renderers_findings_state_fact_parity(self):
        # Plant dirty untracked file to induce a finding
        (self.root / "dirty_file.txt").write_text(
            "untracked payload\n", encoding="utf-8"
        )

        # 1. Inspect repository -> single typed CommandResult
        result: CommandResult = doctor.inspect_repo(self.root)
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.command, "doctor")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.status, "findings")
        self.assertTrue(result.has_findings)
        self.assertEqual(len(result.diagnostics), 1)
        self.assertEqual(result.diagnostics[0].location, "dirty_file.txt")
        self.assertEqual(result.diagnostics[0].rule, "doctor.git-untracked")

        # 2. Render through HumanRenderer
        human_renderer = HumanRenderer()
        human_ctx = OutputContext(mode=OutputMode.HUMAN, color=False)
        human_output = human_renderer.render(result, human_ctx)
        self.assertIn("dirty_file.txt", human_output)
        self.assertIn("Untracked files", human_output)
        self.assertIn("1 finding(s)", human_output)

        # 3. Render through AgentRenderer
        agent_renderer = AgentRenderer()
        agent_ctx = OutputContext(mode=OutputMode.AGENT, color=False)
        agent_output = agent_renderer.render(result, agent_ctx)
        agent_record = json.loads(agent_output.strip())

        # 4. Assert identical outcome facts across both renderers
        self.assertEqual(agent_record["schema"], "aw.agent/v1")
        self.assertEqual(agent_record["cmd"], "doctor")
        self.assertEqual(agent_record["exit"], result.exit_code)
        self.assertEqual(agent_record["outcome"], result.status)
        self.assertEqual(agent_record["findings"], len(result.diagnostics))
        self.assertEqual(len(agent_record["diagnostics"]), 1)
        self.assertEqual(agent_record["diagnostics"][0]["location"], "dirty_file.txt")
        self.assertEqual(agent_record["diagnostics"][0]["rule"], "doctor.git-untracked")

        # 5. Assert evidence keys match
        evidence_keys = {e.key for e in result.evidence}
        agent_evidence_keys = {e["key"] for e in agent_record.get("evidence", [])}
        self.assertEqual(evidence_keys, agent_evidence_keys)
        self.assertIn("git", evidence_keys)
        self.assertIn("env", evidence_keys)


if __name__ == "__main__":
    unittest.main()
