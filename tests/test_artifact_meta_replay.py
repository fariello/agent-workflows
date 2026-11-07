"""Tests for artifact_meta replay, owned fields, loader, and mirrors.

IPD tve77h / E-05, E-06, E-07.
"""

from __future__ import annotations

from pathlib import Path
import random
import pytest

from agent_workflows import artifact_meta as meta


pytestmark = pytest.mark.core


# --------------------------------------------------------------------------------------
# E-05 & V-05: Replay refusal rules and shuffle test
# --------------------------------------------------------------------------------------


def _valid_plan_log_events(id6: str = "abc123") -> list[dict]:
    return [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "create_tool"},
            "op": "create",
            "path": "plans/pending/20261102-test-01-abc123-slug.ipd.md",
            "fields": {
                "status": "draft",
                "set": "test",
                "order": 1,
                "id": id6,
                "type": "ipd",
            },
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "status_set"},
            "op": "transition",
            "from": "draft",
            "to": "to-review",
        },
        {
            "v": 1,
            "seq": 3,
            "append": 3,
            "at": "2026-11-06T12:02:00Z",
            "actor": {"tool": "plan_review"},
            "op": "review",
            "round": 1,
            "review_kind": "gate",
            "verdict": "APPROVE",
            "readiness": "go",
        },
        {
            "v": 1,
            "seq": 4,
            "append": 4,
            "at": "2026-11-06T12:03:00Z",
            "actor": {"tool": "status_set"},
            "op": "transition",
            "from": "to-review",
            "to": "approved",
        },
        {
            "v": 1,
            "seq": 5,
            "append": 4,
            "at": "2026-11-06T12:03:00Z",
            "actor": {"tool": "status_set"},
            "op": "set",
            "fields": {"approval": "2026-11-06 recorded via aw set"},
        },
    ]


def test_replay_shuffle():
    events = _valid_plan_log_events("abc123")
    ordered_lines = [meta.encode_event(e) for e in events]
    state_ordered, _, _, _ = meta.replay("abc123", "ipd", ordered_lines)

    # Replay 10 random permutations
    for seed in range(10):
        shuffled_lines = list(ordered_lines)
        random.Random(seed).shuffle(shuffled_lines)
        state_shuffled, _, _, _ = meta.replay("abc123", "ipd", shuffled_lines)
        assert state_shuffled == state_ordered, f"shuffle mismatch for seed {seed}"


def test_replay_refusal_seq_gap():
    events = _valid_plan_log_events("abc123")
    events[2]["seq"] = 4  # gap: 1, 2, 4
    events[2]["append"] = 4
    lines = [meta.encode_event(e) for e in events[:3]]
    with pytest.raises(ValueError, match="seq-gap"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_seq_duplicate():
    events = _valid_plan_log_events("abc123")
    events[2]["seq"] = 2  # duplicate seq 2
    events[2]["append"] = 2
    lines = [meta.encode_event(e) for e in events[:3]]
    with pytest.raises(ValueError, match="seq-duplicate"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_bad_initial_event():
    # Initial event starting at seq 2
    events = _valid_plan_log_events("abc123")
    events[0]["seq"] = 2
    events[0]["append"] = 2
    lines = [meta.encode_event(e) for e in events]
    with pytest.raises(ValueError, match="bad-initial-event"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_identity_changed():
    events = _valid_plan_log_events("abc123")
    events[0]["fields"]["id"] = "xyz999"
    lines = [meta.encode_event(e) for e in events]
    with pytest.raises(ValueError, match="identity-changed"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_unsupported_version():
    events = _valid_plan_log_events("abc123")
    events[0]["v"] = 2
    lines = [meta.encode_event(e) for e in events]
    with pytest.raises(ValueError, match="unsupported-version"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_append_mismatch():
    events = _valid_plan_log_events("abc123")
    # seq 4 and seq 5 share append 4; change seq 5 to have a different actor
    events[4]["actor"] = {"tool": "different_tool"}
    lines = [meta.encode_event(e) for e in events]
    with pytest.raises(ValueError, match="append-mismatch"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_illegal_transition():
    events = _valid_plan_log_events("abc123")
    # Change seq 2 to jump to executed directly
    events[1]["to"] = "executed"
    lines = [meta.encode_event(e) for e in events[:2]]
    with pytest.raises(ValueError, match="illegal-transition"):
        meta.replay("abc123", "ipd", lines)


def test_replay_refusal_transition_from_mismatch():
    events = _valid_plan_log_events("abc123")
    events[1]["from"] = "approved"  # mismatch, current is draft
    lines = [meta.encode_event(e) for e in events[:2]]
    with pytest.raises(ValueError, match="transition-from-mismatch"):
        meta.replay("abc123", "ipd", lines)


def test_replay_terminal_reopen_transition():
    # Build a log up to executed
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": "plans/pending/test.ipd.md",
            "fields": {"status": "draft", "id": "trm123", "type": "ipd"},
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "test"},
            "op": "transition",
            "from": "draft",
            "to": "reviewed",
        },
        {
            "v": 1,
            "seq": 3,
            "append": 3,
            "at": "2026-11-06T12:02:00Z",
            "actor": {"tool": "test"},
            "op": "transition",
            "from": "reviewed",
            "to": "executed",
            "path": "plans/executed/test.ipd.md",
        },
    ]

    # Without overrides, executed -> approved is refused
    reopen_ev = {
        "v": 1,
        "seq": 4,
        "append": 4,
        "at": "2026-11-06T12:03:00Z",
        "actor": {"tool": "status_set"},
        "op": "transition",
        "from": "executed",
        "to": "approved",
    }
    with pytest.raises(ValueError, match="illegal-transition"):
        meta.replay(
            "trm123", "ipd", [meta.encode_event(e) for e in events + [reopen_ev]]
        )

    # With allow-terminal-reopen override, executed -> approved is accepted
    reopen_ev["overrides"] = ["allow-terminal-reopen"]
    state, _, _, _ = meta.replay(
        "trm123", "ipd", [meta.encode_event(e) for e in events + [reopen_ev]]
    )
    assert state.status == "approved"


# --------------------------------------------------------------------------------------
# E-06 & V-06: Event-owned field rules (-k owned)
# --------------------------------------------------------------------------------------


def test_owned_fields_readiness_and_review_depth():
    # readiness and review_depth cannot be set via generic set
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": "plans/pending/test.ipd.md",
            "fields": {"status": "draft", "id": "own123", "type": "ipd"},
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "test"},
            "op": "set",
            "fields": {"readiness": "go"},
        },
    ]
    with pytest.raises(
        ValueError, match="refuse set of review-owned field 'readiness'"
    ):
        meta.replay("own123", "ipd", [meta.encode_event(e) for e in events])

    events[1]["fields"] = {"review_depth": "complex"}
    with pytest.raises(
        ValueError, match="refuse set of review-owned field 'review_depth'"
    ):
        meta.replay("own123", "ipd", [meta.encode_event(e) for e in events])

    # Valid gate review setting readiness and review_depth
    valid_review = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:01:00Z",
        "actor": {"tool": "/plan-review"},
        "op": "review",
        "round": 1,
        "review_kind": "gate",
        "verdict": "APPROVE",
        "readiness": "go",
        "review_depth": "complex",
    }
    state, _, _, _ = meta.replay(
        "own123", "ipd", [meta.encode_event(events[0]), meta.encode_event(valid_review)]
    )
    # Quote the assertion that a gate review with readiness: go replays to state.fields['readiness'] == 'go'
    assert state.fields["readiness"] == "go"
    assert state.fields["review_depth"] == "complex"


def test_owned_fields_refinement_cannot_carry_readiness():
    ev0 = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "specs/pending/test.spec.md",
        "fields": {"status": "draft", "id": "ref123", "type": "spec"},
    }
    refine_ev = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:01:00Z",
        "actor": {"tool": "refiner"},
        "op": "review",
        "round": 1,
        "review_kind": "refinement",
        "verdict": "REVIEWED - MATERIAL CHANGES APPLIED",
        "readiness": "go",
    }
    # Quote the assertion that a refinement event with readiness is refused
    with pytest.raises(
        ValueError, match="refinement review must not carry 'readiness'"
    ):
        meta.replay(
            "ref123", "spec", [meta.encode_event(ev0), meta.encode_event(refine_ev)]
        )


def test_owned_fields_approval_rules():
    # approval set outside transition to approved append is refused
    events = [
        {
            "v": 1,
            "seq": 1,
            "append": 1,
            "at": "2026-11-06T12:00:00Z",
            "actor": {"tool": "test"},
            "op": "create",
            "path": "plans/pending/test.ipd.md",
            "fields": {"status": "draft", "id": "app123", "type": "ipd"},
        },
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "test"},
            "op": "set",
            "fields": {"approval": "2026-11-06 recorded"},
        },
    ]
    with pytest.raises(
        ValueError, match="set of approval outside transition to approved append"
    ):
        meta.replay("app123", "ipd", [meta.encode_event(e) for e in events])

    # approval must not survive a transition away from approved
    valid_approve = [
        events[0],
        {
            "v": 1,
            "seq": 2,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "test"},
            "op": "transition",
            "from": "draft",
            "to": "approved",
        },
        {
            "v": 1,
            "seq": 3,
            "append": 2,
            "at": "2026-11-06T12:01:00Z",
            "actor": {"tool": "test"},
            "op": "set",
            "fields": {"approval": "2026-11-06 recorded"},
        },
        {
            "v": 1,
            "seq": 4,
            "append": 4,
            "at": "2026-11-06T12:02:00Z",
            "actor": {"tool": "test"},
            "op": "transition",
            "from": "approved",
            "to": "draft",
        },
        # Missing unset of approval!
    ]
    with pytest.raises(
        ValueError,
        match="approval must be unset in the append containing a transition away from approved",
    ):
        meta.replay("app123", "ipd", [meta.encode_event(e) for e in valid_approve])


def test_owned_fields_coverage_and_scope():
    ev0 = {
        "v": 1,
        "seq": 1,
        "append": 1,
        "at": "2026-11-06T12:00:00Z",
        "actor": {"tool": "test"},
        "op": "create",
        "path": "plans/pending/test.ipd.md",
        "fields": {"status": "draft", "id": "cov123", "type": "ipd"},
    }
    # Generic set of coverage is refused
    set_cov = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:01:00Z",
        "actor": {"tool": "test"},
        "op": "set",
        "fields": {"coverage": "all covered"},
    }
    with pytest.raises(
        ValueError, match="refuse set of coverage-owned field 'coverage'"
    ):
        meta.replay(
            "cov123", "ipd", [meta.encode_event(ev0), meta.encode_event(set_cov)]
        )

    # Generic set of scope_result outside transition to executed is refused
    set_scope = {
        "v": 1,
        "seq": 2,
        "append": 2,
        "at": "2026-11-06T12:01:00Z",
        "actor": {"tool": "test"},
        "op": "set",
        "fields": {"scope_result": "within"},
    }
    with pytest.raises(
        ValueError, match="set of 'scope_result' outside transition to executed append"
    ):
        meta.replay(
            "cov123", "ipd", [meta.encode_event(ev0), meta.encode_event(set_scope)]
        )


# --------------------------------------------------------------------------------------
# E-07 & V-07: Loader and mirror parsers (-k "loader or mirror")
# --------------------------------------------------------------------------------------


def test_loader_invalid_log_fails_closed(tmp_path: Path):
    records_root = tmp_path / "records"
    state_root = tmp_path / "state"
    records_root.mkdir(parents=True)
    state_root.mkdir(parents=True)

    id6 = "inv123"
    meta_dir = records_root / "meta"
    meta_dir.mkdir(parents=True)
    log_p = meta_dir / f"{id6}.jsonl"

    # Step 1: Write valid log
    valid_events = _valid_plan_log_events(id6)
    log_p.write_text(
        "".join(meta.encode_event(e) for e in valid_events), encoding="utf-8"
    )

    # Read loads into cache successfully
    st = meta.read(
        id6,
        project_context=type(
            "Ctx", (), {"logical_roots": {"records": records_root, "state": state_root}}
        )(),
    )
    assert st.status == "approved"

    # Step 2: Replace with invalid log (e.g. sequence gap)
    invalid_events = _valid_plan_log_events(id6)
    invalid_events[1]["seq"] = 5  # gap
    invalid_events[1]["append"] = 5
    log_p.write_text(
        "".join(meta.encode_event(e) for e in invalid_events[:2]), encoding="utf-8"
    )

    # Next read fails closed naming defect
    with pytest.raises(ValueError, match="invalid record inv123: seq-gap"):
        meta.read(
            id6,
            project_context=type(
                "Ctx",
                (),
                {"logical_roots": {"records": records_root, "state": state_root}},
            )(),
        )

    # Assert no artifacts row with valid = 1 remains
    conn = meta.open_cache(records_root, state_root)
    valid_row = conn.execute(
        "SELECT valid FROM artifacts WHERE id6 = ? AND valid = 1", (id6,)
    ).fetchone()
    assert valid_row is None


def test_mirror_staged_prompt():
    prompt_text = (
        "<!-- aw-managed-prompt: id: prm123 | status: reusable . Pipeline metadata only. -->\n"
        "# My Staged Prompt\n"
        "Prompt body content here.\n"
    )
    data = meta.parse_staged_prompt_mirror(prompt_text)
    assert data["id"] == "prm123"
    assert data["status"] == "reusable"


def test_mirror_parse_error_on_second_key_walkthrough():
    # Walkthrough allows only 'id'
    bad_walkthrough = "---\nid: wlk123\nstatus: draft\n---\n# Walkthrough Title\n"
    with pytest.raises(
        ValueError, match="walkthrough front matter must have exactly 1 key"
    ):
        meta.parse_walkthrough_mirror(bad_walkthrough)


def test_mirror_parse_error_on_extra_keys_artifact():
    bad_artifact = (
        "---\nid: art123\nstatus: draft\nextra_key: unwanted\n---\n# Artifact Title\n"
    )
    with pytest.raises(ValueError, match="expected exactly 2 front-matter keys"):
        meta.parse_artifact_mirror(bad_artifact)
