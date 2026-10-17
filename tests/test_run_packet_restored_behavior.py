"""Behavioral tests for run_packet step packets, digest verification, and outcome envelopes.

Restores test coverage for 10 unguarded-unreached run_packet keys recorded in backlog item aq04yg
and rollup findings b1mx2w, whose behavioral tests were deleted at 19313eed^ (specifically
from tests/test_run_packet_gates.py).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from agent_workflows import (
    run_engine,
    run_freeze,
    run_ledger_schema,
    run_ledger_store,
    run_packet,
)

pytestmark = pytest.mark.core


# ======================================================================================
# Fixtures (E-01)
# ======================================================================================


@pytest.fixture
def packet_workflow() -> dict[str, Any]:
    """Workflow data defining steps S-01, S-02, and S-03 with requirements and permissions."""
    return {
        "schema_version": 1,
        "id": "test-step-packet-wf",
        "intent": "operate",
        "risk": "medium",
        "interaction": "optional",
        "mutation_boundary": "product",
        "summary": "Workflow for step packet rendering and gate verification",
        "permissions": {
            "allowed_paths": ["agent_workflows/**", "tests/**"],
            "forbidden_paths": ["secrets/**"],
        },
        "requirements": [
            {
                "id": "R-01",
                "text": "Render bounded step packet with strict contract fields",
                "evidence": ["test_report"],
            },
            {
                "id": "R-02",
                "text": "Reject unsupported prose in outcome envelopes",
                "evidence": ["test_report"],
            },
            {
                "id": "R-03",
                "text": "Stop headless runs at needs_input before gated side effects",
                "evidence": ["test_report"],
            },
        ],
        "steps": [
            {
                "id": "S-01",
                "action": "Implement bounded JIT step packet rendering",
                "satisfies": ["R-01"],
                "depends_on": [],
                "evidence": ["test_report", "artifact"],
                "stop_conditions": ["Packet size exceeds budget"],
                "expected_artifacts": ["agent_workflows/run_packet.py"],
            },
            {
                "id": "S-02",
                "action": "Implement outcome envelope validation",
                "satisfies": ["R-02"],
                "depends_on": ["S-01"],
                "evidence": ["test_report"],
                "stop_conditions": ["Unsupported prose detected"],
                "expected_artifacts": ["agent_workflows/run_packet.py"],
            },
            {
                "id": "S-03",
                "action": "Implement human decision gates and headless needs_input stop",
                "satisfies": ["R-03"],
                "depends_on": ["S-02"],
                "gates": ["human_review_gate"],
                "evidence": ["test_report"],
                "stop_conditions": ["Non-interactive consent synthesis attempted"],
                "expected_artifacts": ["agent_workflows/run_gates.py"],
            },
        ],
        "validations": [
            {"id": "V-01", "verifies": "R-01", "evidence": ["test_report"]},
            {"id": "V-02", "verifies": "R-02", "evidence": ["test_report"]},
            {"id": "V-03", "verifies": "R-03", "evidence": ["test_report"]},
        ],
    }


@pytest.fixture
def frozen_reqs() -> run_freeze.RequirementSet:
    """Frozen requirement set created from the raw requirements of the deleted test suite."""
    raw_requirements = {
        "must": [
            "Render bounded step packet with strict contract fields",
            "Reject unsupported prose in outcome envelopes",
            "Stop headless runs at needs_input before gated side effects",
        ],
        "scope": [
            "Touch only run_packet.py, run_gates.py, and test_run_packet_gates.py",
        ],
        "validation": [
            "Golden packet tests pass with size budget and digest verification",
        ],
        "output": [
            "Structured outcome envelope and gate decision records",
        ],
    }
    return run_freeze.freeze_requirements(raw_requirements)


@pytest.fixture
def released_engine(tmp_path: Path) -> run_engine.RunEngine:
    """RunEngine seeded with run and requirement_set records, with S-01 released and started."""
    ledger_path = tmp_path / "run.jsonl"
    store = run_ledger_store.RunLedgerStore(ledger_path)
    store.append(
        {
            "schema_version": run_ledger_schema.LEDGER_SCHEMA_VERSION,
            "kind": "run",
            "run_id": "run-00000001",
            "actor": "runtime",
            "workflow_digest": "a" * 64,
            "requirement_digest": "b" * 64,
            "repo": "test-repo",
            "head": "c" * 64,
            "parent": "",
        }
    )
    store.append(
        {
            "schema_version": run_ledger_schema.LEDGER_SCHEMA_VERSION,
            "kind": "requirement_set",
            "run_id": "run-00000001",
            "actor": "runtime",
            "requirement_digest": "b" * 64,
            "requirements": [{"id": "R-01"}],
            "scope_fence": {},
            "parent": "",
        }
    )
    workflow_data = {
        "id": "envelope-test-wf",
        "steps": [
            {
                "id": "S-01",
                "action": "execute task 1",
                "depends_on": [],
                "satisfies": ["R-01"],
                "evidence": ["test_report"],
            }
        ],
        "requirements": [{"id": "R-01", "description": "task 1 done"}],
    }
    engine = run_engine.RunEngine(workflow_data, store, run_id="run-00000001")
    engine.release_step("S-01")
    engine.start_step("S-01")
    return engine


# ======================================================================================
# E-02: Step packet contract and prompt rendering
# ======================================================================================


def test_golden_packet_contains_every_contract_field(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify rendered step packet carries all immutable metadata, requirements, and contract fields."""
    packet = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        attempt=1,
        frozen_requirements=frozen_reqs,
    )

    # 1. Immutable run & step metadata
    assert packet.run_id == "run-12345678"
    assert packet.workflow_id == "test-step-packet-wf"
    assert packet.step_id == "S-01"
    assert packet.attempt == 1
    assert run_ledger_schema.is_timestamp(packet.timestamp)

    # 2. Action & artifacts
    assert packet.action == "Implement bounded JIT step packet rendering"
    assert packet.expected_artifacts == ("agent_workflows/run_packet.py",)

    # 3. Evidence contract & stop conditions
    assert packet.evidence_contract == ("test_report", "artifact")
    assert packet.stop_conditions == ("Packet size exceeds budget",)
    assert packet.depends_on == ()

    # 4. Scope fence & permissions
    assert "allowed_paths" in packet.scope_fence
    assert "forbidden_paths" in packet.scope_fence
    assert packet.scope_fence["mutation_boundary"] == "product"
    assert packet.allowed_files == ("agent_workflows/**", "tests/**")

    # 5. Bound requirements (only R-01 for S-01, not R-02 or R-03)
    bound_ids = [r.id for r in packet.bound_requirements]
    assert bound_ids == ["R-01"]

    # 6. Exit checklist
    assert len(packet.exit_checklist) >= 3
    assert any("action" in item.lower() for item in packet.exit_checklist)
    assert any("evidence" in item.lower() for item in packet.exit_checklist)

    # 7. Source-to-requirement trace
    assert packet.trace == {"S-01": ["R-01"]}

    # 8. Deterministic digest
    assert run_ledger_schema.is_sha256(packet.packet_digest)

    # 9. Prompt rendering headings and content
    prompt = packet.render_prompt()
    assert "Implement bounded JIT step packet rendering" in prompt
    assert "## Bound Requirements & Success Criteria" in prompt
    assert "## Expected Artifacts" in prompt
    assert "## Required Evidence Contract" in prompt
    assert "## Allowed Scope & Tools" in prompt
    assert "## Stop Conditions" in prompt
    assert "## Step Exit Checklist" in prompt
    assert "- [ ] " in prompt
    assert "mutation_boundary: product" in prompt
    assert "Implement outcome envelope validation" not in prompt
    assert "Implement human decision gates and headless needs_input stop" not in prompt


def test_packet_omits_unrelated_bulk_context(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify packet prompt for S-01 does not include actions of S-02 and S-03."""
    packet = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
    )
    rendered_text = packet.render_prompt()
    assert "Implement bounded JIT step packet rendering" in rendered_text
    assert "Implement outcome envelope validation" not in rendered_text
    assert "Implement human decision gates" not in rendered_text


def test_render_prompt_empty_sections() -> None:
    """Verify minimal packet renders prompt omitting empty requirement, artifact, evidence, and stop sections."""
    minimal_wf = {
        "id": "m",
        "steps": [{"id": "S", "action": "act"}],
        "permissions": "non-mapping",
    }
    packet = run_packet.build_step_packet(minimal_wf, step_id="S")
    prompt = packet.render_prompt()

    assert "## Bound Requirements & Success Criteria" not in prompt
    assert "## Expected Artifacts" not in prompt
    assert "## Required Evidence Contract" not in prompt
    assert "## Stop Conditions" not in prompt
    # Allowed tools default is non-empty, and exit checklist is always present
    assert "## Allowed Scope & Tools" in prompt
    assert "## Step Exit Checklist" in prompt


def test_packet_workflow_wrapper(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify workflow wrapped under a top-level 'workflow' key unwraps to the same workflow_id."""
    wrapped = {"workflow": packet_workflow}
    packet = run_packet.build_step_packet(
        workflow=wrapped,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
    )
    assert packet.workflow_id == "test-step-packet-wf"


def test_packet_tool_default_and_explicit(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify explicit allowed_tools overrides default and omitting it yields DEFAULT_ALLOWED_TOOLS."""
    packet_default = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
    )
    assert packet_default.allowed_tools == run_packet.DEFAULT_ALLOWED_TOOLS

    packet_explicit = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
        allowed_tools=("view_file",),
    )
    assert packet_explicit.allowed_tools == ("view_file",)


def test_unknown_step_id_raises_key_error(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify requesting a packet for an unlisted step id raises KeyError."""
    with pytest.raises(KeyError, match="S-99"):
        run_packet.build_step_packet(
            packet_workflow,
            step_id="S-99",
            run_id="run-12345678",
            frozen_requirements=frozen_reqs,
        )


# ======================================================================================
# E-03: Requirement binding and digest determinism
# ======================================================================================


def test_packet_digest_changes_when_bound_requirement_changes(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify packet digest is sensitive to requirement changes and deterministic for identical inputs."""
    pinned_ts = "2026-01-01T00:00:00Z"

    packet_orig = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
        timestamp=pinned_ts,
    )

    # Modify requirement R-01 in frozen set
    modified_reqs = {
        "must": [
            "Render bounded step packet with strict contract fields (revised)",
            "Reject unsupported prose in outcome envelopes",
            "Stop headless runs at needs_input before gated side effects",
        ],
        "scope": [
            "Touch only run_packet.py, run_gates.py, and test_run_packet_gates.py",
        ],
        "validation": [
            "Golden packet tests pass with size budget and digest verification",
        ],
        "output": [
            "Structured outcome envelope and gate decision records",
        ],
    }
    frozen_modified = run_freeze.freeze_requirements(modified_reqs)

    packet_modified = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_modified,
        timestamp=pinned_ts,
    )

    assert packet_orig.packet_digest != packet_modified.packet_digest

    # Stability assertion with identical pinned timestamp
    packet_repeat = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
        timestamp=pinned_ts,
    )
    assert packet_orig.packet_digest == packet_repeat.packet_digest
    assert packet_orig.to_json() == packet_repeat.to_json()


def test_packet_digest_roundtrip_and_field_sensitivity(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify _compute_packet_digest matches packet.packet_digest and is sensitive to field changes."""
    packet = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
        timestamp="2026-01-01T00:00:00Z",
    )
    payload = packet.to_dict()

    # Round trip: computing digest from to_dict() returns same digest
    assert run_packet._compute_packet_digest(payload) == packet.packet_digest

    # Field sensitivity: changing any field produces a different digest
    mutated_payload = dict(payload)
    mutated_payload["action"] = "Different action text"
    assert run_packet._compute_packet_digest(mutated_payload) != packet.packet_digest


def test_requirement_binding_branches() -> None:
    """Verify all five requirement binding branches and whitespace normalization."""
    # 1. Raw requirement with no frozen set
    wf_raw = {
        "id": "wf-raw",
        "steps": [{"id": "S-01", "satisfies": ["R-RAW"]}],
        "requirements": [{"id": "R-RAW", "text": "Raw requirement text"}],
    }
    p_raw = run_packet.build_step_packet(wf_raw, step_id="S-01")
    req_raw = p_raw.bound_requirements[0]
    assert req_raw.id == "R-RAW"
    assert req_raw.category == "must"
    assert req_raw.text == "Raw requirement text"
    assert req_raw.digest == hashlib.sha256(b"Raw requirement text").hexdigest()

    # 2. Raw requirement with "description" and no "text"
    wf_desc = {
        "id": "wf-desc",
        "steps": [{"id": "S-01", "satisfies": ["R-DESC"]}],
        "requirements": [{"id": "R-DESC", "description": "Description text"}],
    }
    p_desc = run_packet.build_step_packet(wf_desc, step_id="S-01")
    req_desc = p_desc.bound_requirements[0]
    assert req_desc.text == "Description text"
    assert req_desc.category == "must"
    assert req_desc.digest == hashlib.sha256(b"Description text").hexdigest()

    # 3. Raw requirement differing from frozen item only by whitespace (reaches _normalize)
    frozen_set = run_freeze.freeze_requirements(
        {"must": ["first thing", "second thing"]}
    )
    wf_ws = {
        "id": "wf-ws",
        "steps": [{"id": "S-01", "satisfies": ["R-WS"]}],
        "requirements": [{"id": "R-WS", "text": "  second\n  thing "}],
    }
    p_ws = run_packet.build_step_packet(
        wf_ws, step_id="S-01", frozen_requirements=frozen_set
    )
    req_ws = p_ws.bound_requirements[0]
    # Positional fallback would bind "first thing", but whitespace normalization binds "second thing"
    assert req_ws.text == "second thing"
    assert (
        req_ws.digest
        == "731e48108ea479aa8217dfedff7cf7e05d5dcc081316df9d35e1ab73cef40d71"
    )

    # 4. Positional fallback: satisfies id neither frozen nor raw
    wf_pos = {
        "id": "wf-pos",
        "steps": [{"id": "S-01", "satisfies": ["X-9", "Y-9"]}],
    }
    p_pos = run_packet.build_step_packet(
        wf_pos, step_id="S-01", frozen_requirements=frozen_set
    )
    assert [r.text for r in p_pos.bound_requirements] == [
        "first thing",
        "second thing",
    ]

    # 5. Satisfies id that equals a frozen id directly
    wf_fid = {
        "id": "wf-fid",
        "steps": [{"id": "S-01", "satisfies": ["M-01"]}],
    }
    p_fid = run_packet.build_step_packet(
        wf_fid, step_id="S-01", frozen_requirements=frozen_set
    )
    req_fid = p_fid.bound_requirements[0]
    assert req_fid.id == "M-01"
    assert req_fid.text == "first thing"
    assert req_fid.category == "must"

    # 6. _normalize function contract
    assert run_packet._normalize("  a \n\t b  ") == "a b"


# ======================================================================================
# E-04: Serialization and budget enforcement
# ======================================================================================


def test_packet_serialization_roundtrip() -> None:
    """Verify StepPacket to_dict and to_json produce valid serializable JSON with all fields."""
    wf = {
        "id": "wf-roundtrip",
        "steps": [
            {
                "id": "S-01",
                "action": "test action",
                "satisfies": ["R-01", "R-02"],
                "depends_on": ["S-00"],
                "evidence": ["command"],
                "expected_artifacts": ["art.txt"],
                "stop_conditions": ["error"],
            }
        ],
        "requirements": [
            {"id": "R-01", "text": "Requirement 1"},
            {"id": "R-02", "text": "Requirement 2"},
        ],
        "permissions": {
            "allowed_paths": ["src/**"],
            "forbidden_paths": ["secret/**"],
        },
    }
    packet = run_packet.build_step_packet(
        wf, step_id="S-01", run_id="run-00000002", attempt=2
    )
    json_str = packet.to_json()
    parsed = json.loads(json_str)

    assert parsed["run_id"] == "run-00000002"
    assert parsed["step_id"] == "S-01"
    assert parsed["attempt"] == 2
    assert len(parsed["bound_requirements"]) == 2
    assert parsed["depends_on"] == ["S-00"]
    assert parsed["expected_artifacts"] == ["art.txt"]
    assert parsed["evidence_contract"] == ["command"]
    assert parsed["allowed_files"] == ["src/**"]
    assert parsed["scope_fence"]["forbidden_paths"] == ["secret/**"]

    # Compact JSON has no newline and parses identically
    compact_str = packet.to_json(indent=None)
    assert "\n" not in compact_str
    assert json.loads(compact_str) == parsed

    # BoundRequirement.to_dict keys
    assert set(parsed["bound_requirements"][0].keys()) == {
        "id",
        "category",
        "text",
        "digest",
    }


def test_packet_to_dict_sequence_types(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify to_dict returns plain lists for sequences and serializes via standard json.dumps."""
    packet = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
    )
    p_dict = packet.to_dict()

    assert isinstance(p_dict["bound_requirements"], list)
    assert isinstance(p_dict["allowed_tools"], list)
    assert isinstance(p_dict["allowed_files"], list)
    assert isinstance(p_dict["expected_artifacts"], list)
    assert isinstance(p_dict["evidence_contract"], list)
    assert isinstance(p_dict["stop_conditions"], list)
    assert isinstance(p_dict["depends_on"], list)
    assert isinstance(p_dict["exit_checklist"], list)
    assert isinstance(p_dict["scope_fence"]["allowed_paths"], list)
    assert isinstance(p_dict["scope_fence"]["forbidden_paths"], list)

    # Standard json.dumps succeeds without custom encoder
    dumped = json.dumps(p_dict)
    assert isinstance(dumped, str)


def test_packet_size_budget_enforcement(
    packet_workflow: dict[str, Any], frozen_reqs: run_freeze.RequirementSet
) -> None:
    """Verify packet rendering respects size budget and raises PacketBudgetExceededError if exceeded."""
    # Under budget (8192 bytes)
    packet = run_packet.build_step_packet(
        workflow=packet_workflow,
        step_id="S-01",
        run_id="run-12345678",
        frozen_requirements=frozen_reqs,
        budget_bytes=8192,
    )
    assert len(packet.render_prompt().encode("utf-8")) < 8192

    # Exceeding budget (50 bytes) raises PacketBudgetExceededError (subclass of RunPacketError)
    with pytest.raises(run_packet.PacketBudgetExceededError) as exc_info:
        run_packet.build_step_packet(
            workflow=packet_workflow,
            step_id="S-01",
            run_id="run-12345678",
            frozen_requirements=frozen_reqs,
            budget_bytes=50,
        )
    assert isinstance(exc_info.value, run_packet.RunPacketError)


# ======================================================================================
# E-05: Outcome envelope validation and to_dict
# ======================================================================================


def test_outcome_envelope_to_dict() -> None:
    """Verify StepOutcomeEnvelope.to_dict produces exact expected structure."""
    # Minimal envelope
    minimal = run_packet.StepOutcomeEnvelope(
        run_id="r", step_id="s", attempt=1, status="blocked"
    )
    assert minimal.to_dict() == {
        "run_id": "r",
        "step_id": "s",
        "attempt": 1,
        "status": "blocked",
        "actor": "executor",
        "evidence_ids": [],
        "artifacts": [],
    }

    # Full envelope with optional fields set
    full = run_packet.StepOutcomeEnvelope(
        run_id="r",
        step_id="s",
        attempt=1,
        status="failed",
        actor="coordinator",
        evidence_ids=("ev-1",),
        artifacts=({"path": "out.txt", "sha256": "abc"},),
        prose="Prose explanation",
        block_reason="Blocked reason",
        failure_reason="Failure reason",
        timestamp="2026-01-01T00:00:00Z",
    )
    d = full.to_dict()
    assert d["prose"] == "Prose explanation"
    assert d["block_reason"] == "Blocked reason"
    assert d["failure_reason"] == "Failure reason"
    assert d["timestamp"] == "2026-01-01T00:00:00Z"
    assert d["actor"] == "coordinator"
    assert d["evidence_ids"] == ["ev-1"]
    assert d["artifacts"] == [{"path": "out.txt", "sha256": "abc"}]


def test_validate_outcome_envelope_acceptance() -> None:
    """Verify performed, blocked, and failed envelopes are accepted, including plain mappings."""
    # 1. Performed with evidence and required kinds
    env_performed = run_packet.StepOutcomeEnvelope(
        run_id="run-00000001",
        step_id="S-01",
        attempt=1,
        status="performed",
        evidence_ids=("ev-12345",),
    )
    res_p = run_packet.validate_outcome_envelope(
        env_performed,
        expected_run_id="run-00000001",
        expected_step_id="S-01",
        expected_attempt=1,
        required_evidence_kinds=["test_report"],
    )
    assert res_p.ok is True
    assert res_p.envelope is not None
    assert res_p.envelope.status == "performed"
    assert res_p.envelope.evidence_ids == ("ev-12345",)

    # 2. Blocked with block_reason
    env_blocked = run_packet.StepOutcomeEnvelope(
        run_id="run-00000001",
        step_id="S-01",
        attempt=1,
        status="blocked",
        block_reason="Waiting for dependency",
    )
    res_b = run_packet.validate_outcome_envelope(
        env_blocked,
        expected_run_id="run-00000001",
        expected_step_id="S-01",
        expected_attempt=1,
    )
    assert res_b.ok is True
    assert res_b.envelope is not None
    assert res_b.envelope.block_reason == "Waiting for dependency"

    # 3. Failed with failure_reason
    env_failed = run_packet.StepOutcomeEnvelope(
        run_id="run-00000001",
        step_id="S-01",
        attempt=1,
        status="failed",
        failure_reason="Unit test assertion failed",
    )
    res_f = run_packet.validate_outcome_envelope(
        env_failed,
        expected_run_id="run-00000001",
        expected_step_id="S-01",
        expected_attempt=1,
    )
    assert res_f.ok is True
    assert res_f.envelope is not None
    assert res_f.envelope.failure_reason == "Unit test assertion failed"

    # 4. Plain mapping input accepted
    raw_map = {
        "run_id": "run-00000001",
        "step_id": "S-01",
        "attempt": 1,
        "status": "blocked",
        "block_reason": "Waiting for dependency",
    }
    res_m = run_packet.validate_outcome_envelope(raw_map)
    assert res_m.ok is True
    assert res_m.envelope is not None
    assert res_m.envelope.run_id == "run-00000001"


@pytest.mark.parametrize(
    "raw_input,validate_kwargs,expected_code,expected_where",
    [
        (
            "I have finished S-01 and all tests pass",
            {},
            "OE-UNSUPPORTED-PROSE",
            None,
        ),
        (
            {"prose": "Everything is complete and working."},
            {},
            "OE-UNSUPPORTED-PROSE",
            None,
        ),
        (
            {"run_id": "run-1", "step_id": "S-1", "status": "performed"},
            {},
            "OE-INVALID-STRUCTURE",
            "attempt",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-1",
                "attempt": True,
                "status": "performed",
            },
            {},
            "OE-INVALID-STRUCTURE",
            "attempt",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-1",
                "attempt": 1,
                "status": "bogus",
            },
            {},
            "OE-INVALID-STATUS",
            "status",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-1",
                "attempt": 1,
                "status": "performed",
                "actor": "unauthorized_bot",
            },
            {},
            "OE-FOREIGN-ACTOR",
            "actor",
        ),
        (
            {
                "run_id": "run-mismatched",
                "step_id": "S-1",
                "attempt": 1,
                "status": "performed",
            },
            {"expected_run_id": "run-expected"},
            "OE-RUN-MISMATCH",
            "run_id",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-mismatched",
                "attempt": 1,
                "status": "performed",
            },
            {"expected_step_id": "S-expected"},
            "OE-STEP-MISMATCH",
            "step_id",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-1",
                "attempt": 5,
                "status": "performed",
            },
            {"expected_attempt": 1},
            "OE-WRONG-ATTEMPT",
            "attempt",
        ),
        (
            {
                "run_id": "run-1",
                "step_id": "S-1",
                "attempt": 1,
                "status": "performed",
                "evidence_ids": [],
            },
            {"required_evidence_kinds": ["test_report"]},
            "OE-MISSING-EVIDENCE",
            "evidence_ids",
        ),
    ],
    ids=[
        "raw_string_unsupported_prose",
        "mapping_prose_no_status",
        "missing_attempt",
        "attempt_is_bool",
        "status_bogus",
        "foreign_actor",
        "mismatched_run_id",
        "mismatched_step_id",
        "wrong_attempt_number",
        "performed_missing_evidence",
    ],
)
def test_validate_outcome_envelope_rejections(
    raw_input: Any,
    validate_kwargs: dict[str, Any],
    expected_code: str,
    expected_where: str | None,
) -> None:
    """Verify validate_outcome_envelope rejects invalid envelopes with exact finding codes."""
    val_res = run_packet.validate_outcome_envelope(raw_input, **validate_kwargs)
    assert val_res.ok is False
    finding_codes = [f.code for f in val_res.findings]
    assert expected_code in finding_codes
    if expected_where is not None:
        wheres = [f.where for f in val_res.findings if f.code == expected_code]
        assert expected_where in wheres
    if expected_code == "OE-UNSUPPORTED-PROSE" and isinstance(raw_input, str):
        assert val_res.envelope is None


def test_validate_outcome_envelope_controls() -> None:
    """Verify controls: performed without evidence ok when no required kinds, non-mappings dropped."""
    # Performed with empty evidence but no required evidence kinds is accepted
    res_no_req = run_packet.validate_outcome_envelope(
        {
            "run_id": "run-1",
            "step_id": "S-1",
            "attempt": 1,
            "status": "performed",
            "evidence_ids": [],
        },
        required_evidence_kinds=None,
    )
    assert res_no_req.ok is True

    # Non-mapping entries in artifacts and non-string in evidence_ids are sanitized
    res_sanitized = run_packet.validate_outcome_envelope(
        {
            "run_id": "run-1",
            "step_id": "S-1",
            "attempt": 1,
            "status": "performed",
            "evidence_ids": ["ev-valid", 999, None],
            "artifacts": [{"path": "a.txt"}, "invalid-str", 42],
        }
    )
    assert res_sanitized.ok is True
    assert res_sanitized.envelope is not None
    assert res_sanitized.envelope.evidence_ids == ("ev-valid",)
    assert res_sanitized.envelope.artifacts == ({"path": "a.txt"},)


# ======================================================================================
# E-06: Outcome envelope application and fail-closed ledger behavior
# ======================================================================================


def test_apply_outcome_envelope_accepted(
    released_engine: run_engine.RunEngine,
) -> None:
    """Verify accepted performed envelope records step_attempt and sha-bearing artifact_ref."""
    envelope = run_packet.StepOutcomeEnvelope(
        run_id="run-00000001",
        step_id="S-01",
        attempt=1,
        status="performed",
        actor="executor",
        evidence_ids=("ev-cmd-12345",),
        artifacts=(
            {"path": "output.txt", "sha256": "d" * 64},
            {"path": "nosha.txt"},
        ),
        prose="All unit tests passed cleanly.",
    )

    snapshot = run_packet.apply_outcome_envelope(
        released_engine, envelope, required_evidence_kinds=["test_report"]
    )
    assert snapshot.state == "performed"
    assert released_engine.step_state("S-01") == "performed"

    # Ledger gains exactly one step_attempt and one artifact_ref
    records = released_engine.store.read_records()
    step_attempts = [r for r in records if r.get("kind") == "step_attempt"]
    assert len(step_attempts) == 1
    assert step_attempts[0]["step"] == "S-01"
    assert step_attempts[0]["state"] == "performed"

    artifact_refs = [r for r in records if r.get("kind") == "artifact_ref"]
    assert len(artifact_refs) == 1
    assert artifact_refs[0]["path"] == "output.txt"
    assert artifact_refs[0]["sha256"] == "d" * 64


def test_apply_outcome_envelope_plain_mapping_accepted(
    tmp_path: Path,
) -> None:
    """Verify applying a plain mapping outcome envelope updates engine state and records step_attempt."""
    ledger_path = tmp_path / "run.jsonl"
    store = run_ledger_store.RunLedgerStore(ledger_path)
    store.append(
        {
            "schema_version": run_ledger_schema.LEDGER_SCHEMA_VERSION,
            "kind": "run",
            "run_id": "run-00000001",
            "actor": "runtime",
            "workflow_digest": "a" * 64,
            "requirement_digest": "b" * 64,
            "repo": "test-repo",
            "head": "c" * 64,
            "parent": "",
        }
    )
    store.append(
        {
            "schema_version": run_ledger_schema.LEDGER_SCHEMA_VERSION,
            "kind": "requirement_set",
            "run_id": "run-00000001",
            "actor": "runtime",
            "requirement_digest": "b" * 64,
            "requirements": [{"id": "R-01"}],
            "scope_fence": {},
            "parent": "",
        }
    )
    workflow_data = {
        "id": "envelope-test-wf",
        "steps": [
            {
                "id": "S-01",
                "action": "execute task 1",
                "depends_on": [],
                "satisfies": ["R-01"],
            }
        ],
        "requirements": [{"id": "R-01", "description": "task 1 done"}],
    }
    engine = run_engine.RunEngine(workflow_data, store, run_id="run-00000001")
    engine.release_step("S-01")
    engine.start_step("S-01")

    raw_env = {
        "run_id": "run-00000001",
        "step_id": "S-01",
        "attempt": 1,
        "status": "performed",
        "actor": "executor",
    }
    snapshot = run_packet.apply_outcome_envelope(engine, raw_env)
    assert snapshot.state == "performed"
    assert engine.step_state("S-01") == "performed"


@pytest.mark.parametrize(
    "raw_input",
    [
        "I have finished S-01 and all 100 tests pass!",
        {"prose": "Everything is complete and working perfectly."},
        {"message": "done", "status_text": "success"},
        {"step": "S-01", "result": "performed"},
    ],
    ids=[
        "prose_string",
        "mapping_prose",
        "mapping_message",
        "mapping_result_missing_fields",
    ],
)
def test_apply_outcome_envelope_unsupported_prose_fail_closed(
    released_engine: run_engine.RunEngine, raw_input: Any
) -> None:
    """Verify unsupported prose inputs raise OutcomeEnvelopeError and do not mutate state or ledger."""
    records_before = len(released_engine.store.read_records())

    with pytest.raises(run_packet.OutcomeEnvelopeError):
        run_packet.apply_outcome_envelope(released_engine, raw_input)

    assert len(released_engine.store.read_records()) == records_before
    assert released_engine.step_state("S-01") == "running"


@pytest.mark.parametrize(
    "envelope,kwargs,expected_exc",
    [
        (
            "plain prose string",
            {},
            run_packet.UnsupportedProseError,
        ),
        (
            run_packet.StepOutcomeEnvelope(
                run_id="run-00000001",
                step_id="S-01",
                attempt=1,
                status="performed",
                actor="unauthorized_foreign_bot",
                evidence_ids=("ev-1",),
            ),
            {},
            run_packet.ForeignActorError,
        ),
        (
            run_packet.StepOutcomeEnvelope(
                run_id="run-00000001",
                step_id="S-01",
                attempt=5,
                status="performed",
                actor="executor",
                evidence_ids=("ev-1",),
            ),
            {},
            run_packet.WrongAttemptError,
        ),
        (
            run_packet.StepOutcomeEnvelope(
                run_id="run-00000001",
                step_id="S-01",
                attempt=1,
                status="performed",
                actor="executor",
                evidence_ids=(),
            ),
            {"required_evidence_kinds": ["test_report"]},
            run_packet.MissingEvidenceError,
        ),
        (
            run_packet.StepOutcomeEnvelope(
                run_id="run-00000001",
                step_id="S-01",
                attempt=1,
                status="bogus",
                actor="executor",
            ),
            {},
            run_packet.InvalidOutcomeEnvelopeError,
        ),
        (
            run_packet.StepOutcomeEnvelope(
                run_id="run-99999999",
                step_id="S-01",
                attempt=1,
                status="performed",
                actor="executor",
                evidence_ids=("ev-1",),
            ),
            {},
            run_packet.InvalidOutcomeEnvelopeError,
        ),
    ],
    ids=[
        "prose_string",
        "foreign_actor",
        "wrong_attempt",
        "missing_evidence",
        "bogus_status",
        "mismatched_run_id",
    ],
)
def test_apply_outcome_envelope_typed_exceptions_fail_closed(
    released_engine: run_engine.RunEngine,
    envelope: Any,
    kwargs: dict[str, Any],
    expected_exc: type[Exception],
) -> None:
    """Verify rejections raise specific typed exceptions and leave ledger and running state unchanged."""
    records_before = len(released_engine.store.read_records())

    with pytest.raises(expected_exc):
        run_packet.apply_outcome_envelope(released_engine, envelope, **kwargs)

    assert len(released_engine.store.read_records()) == records_before
    assert released_engine.step_state("S-01") == "running"
