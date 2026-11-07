"""Tests for artifact_meta registry, event schema, envelope, and refusals.

IPD tve77h / E-01, E-18, E-02, E-03, E-04.
"""

from __future__ import annotations

import json
from pathlib import Path
import socket
import pytest

from agent_workflows import artifact_meta as meta


pytestmark = pytest.mark.core


# --------------------------------------------------------------------------------------
# E-01 & V-01: Registry tests (-k registry)
# --------------------------------------------------------------------------------------


def test_registry_fields_ipd():
    fields = meta.registry_fields("ipd")
    expected_subset = {
        "plan_role",
        "review_depth",
        "pipeline",
        "scope_result",
        "short_description",
        "item_dependencies",
    }
    for f in expected_subset:
        assert f in fields, f"expected field {f!r} in registry_fields('ipd')"


def test_registry_unknown_field():
    for rtype in meta.SUPPORTED_TYPES:
        ev = {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "set",
            "fields": {"nonexistent_unknown_field_xyz": "value"},
        }
        with pytest.raises(
            ValueError, match="unknown field 'nonexistent_unknown_field_xyz'"
        ):
            meta.validate_event(ev, artifact_type=rtype)


def test_registry_transitions():
    # plan transition from approved to superseded is legal
    ok, reason = meta.validate_transition_edge("ipd", "approved", "superseded")
    assert ok, f"transition approved -> superseded should be legal: {reason}"

    # plan transition from executed to draft is NOT legal without override
    ok, reason = meta.validate_transition_edge("ipd", "executed", "draft")
    assert (
        not ok
    ), "transition executed -> draft should be illegal without allow-terminal-reopen"


# --------------------------------------------------------------------------------------
# E-18 & V-18: Op schemas (-k op_schema)
# --------------------------------------------------------------------------------------


def test_op_schema_review_unknown_payload_key():
    ev = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "/plan-review"},
        "op": "review",
        "round": 1,
        "review_kind": "gate",
        "verdict": "APPROVE",
        "bogus_payload_key": "some_value",
    }
    with pytest.raises(ValueError, match="unknown payload key 'bogus_payload_key'"):
        meta.validate_event(ev, artifact_type="ipd")


def test_op_schema_finalize_reserved():
    ev = {
        "v": 1,
        "seq": 3,
        "append": 3,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "finalize"},
        "op": "finalize",
    }
    with pytest.raises(
        ValueError, match="no registered payload schema for reserved op 'finalize'"
    ):
        meta.validate_event(ev, artifact_type="ipd")


def test_op_schema_rename_move_verb_refused():
    ev = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "aw rename"},
        "op": "rename",
        "verb": "move",
        "path": "plans/pending/20261102-test-01-abc123-slug.ipd.md",
    }
    with pytest.raises(ValueError, match="invalid rename verb 'move'"):
        meta.validate_event(ev, artifact_type="ipd")


def test_op_schema_coverage_valid():
    ev = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "coverage"},
        "op": "coverage",
        "coverage": "all covered",
        "coverage_fingerprint": "sha256-12345",
    }
    # Should not raise
    meta.validate_event(ev, artifact_type="ipd")


# --------------------------------------------------------------------------------------
# E-02 & V-02: Envelope validation (-k envelope)
# --------------------------------------------------------------------------------------


def test_envelope_canonical_round_trip():
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test_tool"},
        "op": "create",
        "path": "plans/pending/20261102-test-01-abc123-slug.ipd.md",
    }
    line = meta.encode_event(ev)
    # Quote the assertion that compares encode_event(decode_line(line)) with line
    assert meta.encode_event(meta.decode_line(line)) == line


def test_envelope_id6_validation():
    # Valid id6
    meta.validate_id6("abc123")
    # Refuse trailing newline in id6
    with pytest.raises(ValueError, match="invalid id6"):
        meta.validate_id6("abc123\n")


def test_envelope_actor_null_key():
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test", "model": None},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
    }
    with pytest.raises(ValueError, match="actor key 'model' must be omitted, not null"):
        meta.validate_envelope(ev)


def test_envelope_day_only_at_refused():
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-02",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
    }
    with pytest.raises(
        ValueError, match="at must be RFC 3339 UTC timestamp with time of day"
    ):
        meta.validate_envelope(ev)


def test_envelope_overrides():
    # Accepted override
    ev_ok = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "transition",
        "from": "executed",
        "to": "approved",
        "overrides": ["allow-terminal-reopen"],
    }
    meta.validate_envelope(ev_ok)

    # Empty overrides list
    ev_empty = dict(ev_ok, overrides=[])
    with pytest.raises(ValueError, match="overrides must be a non-empty list"):
        meta.validate_envelope(ev_empty)

    # Unknown override
    ev_unknown = dict(ev_ok, overrides=["force"])
    with pytest.raises(ValueError, match="unknown override 'force'"):
        meta.validate_envelope(ev_unknown)


# --------------------------------------------------------------------------------------
# E-03 & V-03: Writer-side refusals (-k refus)
# --------------------------------------------------------------------------------------


def test_refusals_301_char_short_description(tmp_path: Path):
    long_desc = "a" * 301
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
        "fields": {"short_description": long_desc},
    }
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events("ipd", [ev], records_root=tmp_path)
    print("Refusal reason for 301-char short_description:", exc_info.value)
    assert (
        "exceeds" in str(exc_info.value)
        or "300" in str(exc_info.value)
        or "short_description" in str(exc_info.value)
    )


def test_refusals_short_description_newline(tmp_path: Path):
    desc = "line1\nline2"
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
        "fields": {"short_description": desc},
    }
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events("ipd", [ev], records_root=tmp_path)
    print("Refusal reason for newline in short_description:", exc_info.value)
    assert "newline" in str(exc_info.value).lower()


def test_refusals_actor_session_id(tmp_path: Path):
    ses_id = "ses_" + "01234567890123456789"
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test", "run_id": ses_id},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
    }
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events("ipd", [ev], records_root=tmp_path)
    print("Refusal reason for session ID in actor:", exc_info.value)
    assert "session-id" in str(exc_info.value) or "leak" in str(exc_info.value).lower()


def test_refusals_message_hostname(tmp_path: Path):
    hname = socket.gethostname()
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
        "message": f"ran on host {hname} successfully",
    }
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events("ipd", [ev], records_root=tmp_path)
    reason = str(exc_info.value)
    print("Refusal reason for message hostname:", reason)
    assert "derived:" in reason or "host" in reason.lower()


def test_refusals_message_absolute_posix_path(tmp_path: Path):
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
        "message": "refer to file /opt/x/a.md for details",
    }
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events("ipd", [ev], records_root=tmp_path)
    print("Refusal reason for absolute POSIX path in message:", exc_info.value)
    assert "absolute" in str(exc_info.value).lower()


def test_refusals_path_home_and_dots(tmp_path: Path):
    home_path = str(Path.home() / "a.md")
    ev1 = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": home_path,
    }
    with pytest.raises(ValueError) as exc1:
        meta.validate_new_events("ipd", [ev1], records_root=tmp_path)
    print("Refusal reason for absolute home path:", exc1.value)

    ev2 = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "../a.md",
    }
    with pytest.raises(ValueError) as exc2:
        meta.validate_new_events("ipd", [ev2], records_root=tmp_path)
    print("Refusal reason for '..' in path:", exc2.value)


def test_refusals_accepted_relative_path_and_slash_command(tmp_path: Path):
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/x.ipd.md",
        "message": "ran /plan-review",
    }
    # Should be accepted without error
    meta.validate_new_events("ipd", [ev], records_root=tmp_path)


def test_refusals_5000_char_legacy_line_migration_import(tmp_path: Path):
    long_line = "x" * 5000
    ev = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "migration"},
        "op": "legacy",
        "source": "history",
        "line": long_line,
    }
    # Refused without migration_import=True
    with pytest.raises(ValueError) as exc_info:
        meta.validate_new_events(
            "ipd", [ev], records_root=tmp_path, migration_import=False
        )
    print("Refusal reason for 5000-char line without migration_import:", exc_info.value)

    # Accepted with migration_import=True
    meta.validate_new_events("ipd", [ev], records_root=tmp_path, migration_import=True)


# --------------------------------------------------------------------------------------
# E-04 & V-04: Structured dependency values (-k dependenc)
# --------------------------------------------------------------------------------------


def test_dependencies_shapes():
    shapes = {}
    # 1. executed:abc123
    d1, e1 = meta.parse_item_dependencies_field("executed:abc123")
    shapes["executed:abc123"] = (d1, e1)

    # 2. exists:spec:def456
    d2, e2 = meta.parse_item_dependencies_field("exists:spec:def456")
    shapes["exists:spec:def456"] = (d2, e2)

    # 3. state:spec:approved:def456
    d3, e3 = meta.parse_item_dependencies_field("state:spec:approved:def456")
    shapes["state:spec:approved:def456"] = (d3, e3)

    # 4. none
    d4, e4 = meta.parse_item_dependencies_field("none")
    shapes["none"] = (d4, e4)

    # 5. unresolved
    d5, e5 = meta.parse_item_dependencies_field("unresolved")
    shapes["unresolved"] = (d5, e5)

    # 6. absent field
    d6, e6 = meta.parse_item_dependencies_field(None)
    shapes["absent"] = (d6, e6)

    print("Parsed stored dependency values:")
    for k, v in shapes.items():
        print(f"  {k} -> {v}")

    # Assert six distinct shapes
    vals = list(shapes.values())
    assert len(vals) == 6
    # Each shape must be distinct
    unique_shapes = set()
    for d, e in vals:
        unique_shapes.add((d, json.dumps(e, sort_keys=True)))
    assert (
        len(unique_shapes) == 6
    ), f"expected 6 distinct shapes, got {len(unique_shapes)}"

    # none is distinct from absent
    assert shapes["none"] != shapes["absent"]
    assert shapes["none"][0] == "none"
    assert shapes["absent"][0] == "absent"
