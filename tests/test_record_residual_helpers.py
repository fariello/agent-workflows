"""Direct behavioral tests for agent record validation, id6 collision sets, and artifact type inference.

Restores core-tier behavioral coverage for record-handling residual helpers recorded in
backlog item nzc6dm, plan v44udc, and findings wo21z5:
- agent_schema.validate_agent_record (group 22)
- artifact_rename._existing_type_id6s (group 23)
- doctor._infer_artifact_type (group 34)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_workflows import agent_schema, artifact_core, artifact_rename, doctor

pytestmark = pytest.mark.core


class TestValidateAgentRecord:
    """Direct behavioral tests for validate_agent_record and is_valid_agent_record."""

    def test_validate_agent_record_valid_record(self) -> None:
        good = {
            "schema": agent_schema.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "x",
            "exit": 0,
            "outcome": "ok",
            "verified": True,
            "complete": True,
        }
        assert agent_schema.validate_agent_record(good) == []
        assert agent_schema.is_valid_agent_record(good) is True

    def test_validate_agent_record_invalid_exit_code(self) -> None:
        good = {
            "schema": agent_schema.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "x",
            "exit": 0,
            "outcome": "ok",
            "verified": True,
            "complete": True,
        }
        assert agent_schema.validate_agent_record(dict(good, exit=7)) == [
            "Field 'exit' must be an integer in (0, 1, 2), got '7'"
        ]

    def test_validate_agent_record_empty_record(self) -> None:
        errors = agent_schema.validate_agent_record({})
        assert "Invalid schema: expected 'aw.agent/v1', got 'None'" in errors
        assert (
            "Invalid kind: 'None' must be one of ('result', 'summary', 'item', 'error')"
            in errors
        )
        assert "Field 'cmd' must be a non-empty string" in errors
        assert agent_schema.is_valid_agent_record({}) is False

    def test_validate_agent_record_missing_verified_and_complete(self) -> None:
        rec = {
            "schema": agent_schema.SCHEMA_VERSION,
            "kind": "result",
            "cmd": "x",
            "exit": 0,
            "outcome": "ok",
        }
        errors = agent_schema.validate_agent_record(rec)
        assert "Result record missing boolean 'verified' field" in errors
        assert "Result record missing boolean 'complete' field" in errors


class TestExistingTypeId6s:
    """Direct behavioral tests for artifact_rename._existing_type_id6s collision guard."""

    def test_existing_type_id6s_collects_clustered_and_legacy_ids(
        self, tmp_path: Path
    ) -> None:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        pending_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        (pending_dir / "20261001-sx-01-abc123-x.ipd.md").write_text(
            "- Id: abc123\n", encoding="utf-8"
        )
        (pending_dir / "legacy.md").write_text("- Id: zzz999\n", encoding="utf-8")
        assert artifact_rename._existing_type_id6s(tmp_path, "plans") == {
            "abc123",
            "zzz999",
        }

    def test_existing_type_id6s_empty_repo(self, tmp_path: Path) -> None:
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        assert artifact_rename._existing_type_id6s(tmp_path, "plans") == set()


class TestInferArtifactType:
    """Direct behavioral tests for doctor._infer_artifact_type and build_remediation."""

    def test_infer_artifact_type_mappings(self) -> None:
        assert doctor._infer_artifact_type("") is None
        assert doctor._infer_artifact_type("README.md") is None
        assert (
            doctor._infer_artifact_type(".aw/records/plans/pending/a.ipd.md") == "plans"
        )
        assert doctor._infer_artifact_type("x.spec.md") == "specs"
        assert doctor._infer_artifact_type(".agents/prompts/a") == "prompts"
        assert doctor._infer_artifact_type("x.backlog.md") == "backlog"
        assert doctor._infer_artifact_type(".aw/records/research/x") == "research"
        assert doctor._infer_artifact_type("x.walkthrough.md") == "walkthroughs"
        assert doctor._infer_artifact_type(".aw/records/comms/a") == "comms"
        assert doctor._infer_artifact_type("x.release.md") == "releases"

    def test_build_remediation_summary_fix_routes_to_inferred_type(
        self, tmp_path: Path
    ) -> None:
        loc_spec = ".aw/records/specs/20261001-abc123-01-abc123-x.spec.md"
        rem_spec = doctor.build_remediation(
            artifact_core.Drift(loc_spec, "check.name-nonconformant", "d"), tmp_path
        )
        assert "aw rename specs abc123" in rem_spec.summary_fix

        loc_backlog = ".aw/records/backlog/open/20261001-sx-01-abc123-x.backlog.md"
        rem_backlog = doctor.build_remediation(
            artifact_core.Drift(loc_backlog, "check.name-nonconformant", "d"), tmp_path
        )
        assert "aw rename backlog abc123" in rem_backlog.summary_fix
