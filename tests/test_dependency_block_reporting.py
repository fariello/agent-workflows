"""Behavioral tests for dependency-block reporting across producers and renderers.

Pins:
  (a) cascade_dependency_blocked producer output shape (bare tokens + reasons map);
  (b) frozen-record items (embedded reason, no map) render no second parenthetical or (blocked);
  (c) drain-shaped and post-E-01 cascade items render mapped reasons exactly once;
  (d) render_run_summary_table renders diagnostics for both canonical and legacy status tokens;
  (e) write_report emits ## Dependency blocks (why) for both canonical and legacy status tokens;
  (f) orchestrator items with refusal records surface per-child reasons in write_report while
      summary table renders the refusal line.
"""

from __future__ import annotations

import json
import unittest.mock as mock
from pathlib import Path
from typing import Any

import pytest

from agent_workflows.render_stream import (
    Palette,
    record_refusal,
    render_run_summary_table,
)
from agent_workflows.review_findings import GatingBlock
from agent_workflows.run_selection_policy import strip_dependency_reason_prefix
from agent_workflows.runner_shared import (
    AGY_HOST_LABELS,
    EXECUTION_SUCCESS_STATES,
    OC_HOST_LABELS,
    ORCH_DISPATCH_RECONSIDER,
    ORCH_DISPATCH_TERMINATE,
    ORCH_REASON_DEAD_CHILDREN,
    ORCH_REASON_UNFINISHED_CHILDREN,
    TERMINAL_STATES,
    TRANSIENT_DEPENDENCY_WAIT_KEY,
    OrchestratorDispatch,
    cascade_dependency_blocked,
    dependency_status_detailed,
    dispatch_orchestrator_item,
    render_transient_dependency_waits,
    write_report,
)


def _diag_lines(table_text: str) -> list[str]:
    """Extract diagnostic bullet lines from rendered summary table output."""
    return [line for line in table_text.splitlines() if line.strip().startswith("•")]


def test_cascade_producer_output_shape(tmp_path: Path) -> None:
    """Case (a): cascade_dependency_blocked writes bare tokens, parallel reasons, and no recovery."""
    prereq = {
        "position": 1,
        "id6": "aaa111",
        "status": "reviewed",
        "action": "execute",
    }
    dependent = {
        "position": 2,
        "id6": "bbb222",
        "status": "queued",
        "action": "execute",
        "dependencies": ["executed:aaa111"],
    }
    state: dict[str, Any] = {"queue": [prereq, dependent]}

    blocked = cascade_dependency_blocked(state, run_dir=tmp_path)

    assert [b["id6"] for b in blocked] == ["bbb222"]
    assert dependent["status"] == "fail-depend"
    assert dependent["unsatisfied_dependencies"] == ["executed:aaa111"]
    assert dependent["unsatisfied_dependency_reasons"] == {
        "executed:aaa111": "target aaa111 is reviewed"
    }
    assert dependent.get("dependency_block_recovery") is None

    events = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(events) == 1
    ev = events[0]
    assert ev["event"] == "dependency-blocked"
    assert ev["id6"] == "bbb222"
    assert ev["dependencies"] == ["executed:aaa111"]
    assert ev["reason"] == "prerequisite reached a non-success terminal state"
    assert set(ev.keys()) == {"at", "event", "id6", "dependencies", "reason"}


def test_cascade_producer_output_shape_with_hint(tmp_path: Path) -> None:
    """Case (a2): cascade_dependency_blocked with hint writes dependency_block_recovery without altering events."""
    prereq = {
        "position": 1,
        "id6": "aaa111",
        "status": "reviewed",
        "action": "execute",
    }
    dependent = {
        "position": 2,
        "id6": "bbb222",
        "status": "queued",
        "action": "execute",
        "dependencies": ["executed:aaa111"],
    }
    state: dict[str, Any] = {"queue": [prereq, dependent]}
    hint = OC_HOST_LABELS.dependency_block_recovery

    blocked = cascade_dependency_blocked(state, run_dir=tmp_path, recovery_hint=hint)

    assert [b["id6"] for b in blocked] == ["bbb222"]
    assert dependent["status"] == "fail-depend"
    assert dependent["unsatisfied_dependencies"] == ["executed:aaa111"]
    assert dependent["unsatisfied_dependency_reasons"] == {
        "executed:aaa111": "target aaa111 is reviewed"
    }
    assert dependent.get("dependency_block_recovery") == hint

    events = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(events) == 1
    ev = events[0]
    assert ev["event"] == "dependency-blocked"
    assert ev["id6"] == "bbb222"
    assert ev["dependencies"] == ["executed:aaa111"]
    assert ev["reason"] == "prerequisite reached a non-success terminal state"
    assert set(ev.keys()) == {"at", "event", "id6", "dependencies", "reason"}


def test_frozen_record_no_duplicate_parenthetical_or_blocked() -> None:
    """Case (b): frozen-record item (embedded reason, no map) has no (blocked) fallback."""
    queue = [
        {
            "position": 1,
            "id6": "eee555",
            "setid": "test",
            "action": "execute",
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:aaa111 (target reviewed)"],
        }
    ]
    state: dict[str, Any] = {"queue": queue, "run_id": "run-frozen"}
    out = render_run_summary_table(state, pal=Palette(False))
    diags = _diag_lines(out)

    assert len(diags) == 1
    assert (
        "• eee555: dependency-blocked (executed:aaa111 (target reviewed))" in diags[0]
    )
    assert "(blocked)" not in out


def test_drain_and_cascade_mapped_reasons_rendered_once(tmp_path: Path) -> None:
    """Case (c): drain-shaped and post-E-01 cascade items render mapped reason exactly once."""
    # Synthesize a pending plan under tmp_path so the dependency resolves against
    # disk without coupling to the live repository. The dependency token must be a
    # legal six-character id6; a malformed token silently diverts to the unparseable-token
    # guard and asserts nothing about resolution.
    pending = tmp_path / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True)
    (pending / "20260919-s-01-drn999-dep.ipd.md").write_text(
        "# IPD: dep\n\n- Id: drn999\n- Status: approved\n", encoding="utf-8"
    )

    # Drain item: reasons derived via dependency_status_detailed
    drain_token = "executed:drn999"
    drain_item: dict[str, Any] = {
        "position": 1,
        "id6": "drn001",
        "setid": "test",
        "action": "execute",
        "status": "fail-depend",
        "dependencies": [drain_token],
    }
    state_drain: dict[str, Any] = {
        "queue": [drain_item],
        "repo": str(tmp_path),
        "run_id": "run-drain",
    }
    sat, un_deps, un_reasons = dependency_status_detailed(drain_item, state_drain)
    assert not sat

    # Guard against falling back to unparseable token, resolver error, or empty-reason substitute:
    drain_reason = un_reasons[drain_token]
    assert "unparseable dependency token" not in drain_reason
    assert "Cannot locate IPD" not in drain_reason
    assert f"{drain_token}: dependency not satisfied" not in drain_reason

    drain_item["unsatisfied_dependencies"] = un_deps
    drain_item["unsatisfied_dependency_reasons"] = un_reasons

    drain_out = render_run_summary_table(state_drain, pal=Palette(False))
    drain_diags = _diag_lines(drain_out)
    assert len(drain_diags) == 1
    assert "(blocked)" not in drain_diags[0]
    # Reason mapped from dependency_status_detailed appears in output, de-duplicated
    expected_drain_reason = strip_dependency_reason_prefix(
        drain_token, un_reasons[drain_token]
    )
    assert expected_drain_reason in drain_diags[0]
    assert drain_diags[0].count(drain_token) == 1

    # Post-E-01 cascade item: produced by calling cascade_dependency_blocked
    prereq = {
        "position": 1,
        "id6": "aaa111",
        "status": "reviewed",
        "action": "execute",
    }
    cascade_item = {
        "position": 2,
        "id6": "cas001",
        "setid": "test",
        "status": "queued",
        "action": "execute",
        "dependencies": ["executed:aaa111"],
    }
    state_cascade: dict[str, Any] = {
        "queue": [prereq, cascade_item],
        "run_id": "run-cascade",
    }
    cascade_dependency_blocked(state_cascade)

    cascade_out = render_run_summary_table(
        {"queue": [cascade_item], "run_id": "run-cascade-view"},
        pal=Palette(False),
    )
    cascade_diags = _diag_lines(cascade_out)
    assert len(cascade_diags) == 1
    assert (
        "• cas001: fail-depend (executed:aaa111 (target aaa111 is reviewed))"
        in cascade_diags[0]
    )
    assert "(blocked)" not in cascade_diags[0]


@pytest.mark.parametrize("status", ["fail-depend", "dependency-blocked"])
def test_summary_table_diagnostics_rendered_for_canonical_and_legacy_statuses(
    status: str,
) -> None:
    """Case (d): summary table renders diagnostics for both fail-depend and dependency-blocked."""
    queue = [
        {
            "position": 1,
            "id6": "eee555",
            "setid": "test",
            "action": "execute",
            "status": status,
            "unsatisfied_dependencies": ["executed:aaa111"],
            "unsatisfied_dependency_reasons": {
                "executed:aaa111": "target aaa111 is reviewed"
            },
        }
    ]
    state: dict[str, Any] = {"queue": queue, "run_id": f"run-{status}"}
    out = render_run_summary_table(state, pal=Palette(False))
    diags = _diag_lines(out)

    assert len(diags) == 1
    assert (
        f"• eee555: {status} (executed:aaa111 (target aaa111 is reviewed))" in diags[0]
    )


@pytest.mark.parametrize("status", ["fail-depend", "dependency-blocked"])
def test_write_report_dependency_blocks_section_for_canonical_and_legacy_statuses(
    tmp_path: Path, status: str
) -> None:
    """Case (e): write_report emits ## Dependency blocks (why) for fail-depend and dependency-blocked."""
    queue = [
        {
            "position": 1,
            "id6": "eee555",
            "setid": "test",
            "action": "execute",
            "status": status,
            "unsatisfied_dependencies": ["executed:aaa111"],
            "unsatisfied_dependency_reasons": {
                "executed:aaa111": "target aaa111 is reviewed"
            },
        }
    ]
    state: dict[str, Any] = {"queue": queue, "run_id": f"run-report-{status}"}
    write_report(tmp_path, state, labels=OC_HOST_LABELS)

    report_text = (tmp_path / "execution-report.md").read_text()
    assert "## Dependency blocks (why)" in report_text
    assert "- `eee555` (position 1):" in report_text
    assert "- `executed:aaa111`: target aaa111 is reviewed" in report_text


def test_orchestrator_item_surfaces_child_in_report_not_summary_table(
    tmp_path: Path,
) -> None:
    """Case (f): orchestrator items surface children in write_report; summary table renders refusal."""
    item = {
        "position": 1,
        "id6": "orc999",
        "setid": "test",
        "action": "orchestrate",
        "status": "fail-depend",
        "unsatisfied_dependencies": ["executed:chi001"],
        "unsatisfied_dependency_reasons": {"executed:chi001": "child chi001 is queued"},
    }
    record_refusal(
        item,
        code="unfinished-children",
        reason="Set carries unfinished children. chi001 is queued",
        remedy="execute children",
    )
    state: dict[str, Any] = {"queue": [item], "run_id": "run-orchestrator"}

    # Summary table renders refusal line, swallowing dependency arm
    out = render_run_summary_table(state, pal=Palette(False))
    diags = _diag_lines(out)
    assert len(diags) == 1
    assert (
        "• orc999: fail-depend (Set carries unfinished children. chi001 is queued)"
        in diags[0]
    )
    assert "executed:chi001" not in out

    # write_report revives per-child reason under ## Dependency blocks (why)
    write_report(tmp_path, state, labels=OC_HOST_LABELS)
    report_text = (tmp_path / "execution-report.md").read_text()
    assert "## Dependency blocks (why)" in report_text
    assert "- `executed:chi001`: child chi001 is queued" in report_text


def test_orchestrator_terminate_carries_recovery_hint_and_reconsider_does_not(
    tmp_path: Path,
) -> None:
    """Orchestrator TERMINATE carries recovery_hint; RECONSIDER leaves it absent and status queued."""
    repo = Path.cwd()
    hint = OC_HOST_LABELS.dependency_block_recovery

    # TERMINATE path
    item_term = {
        "position": 1,
        "id6": "orc001",
        "setid": "test",
        "action": "orchestrate",
        "status": "queued",
    }
    state_term: dict[str, Any] = {
        "queue": [item_term],
        "repo": str(repo),
        "run_id": "run-term",
    }
    dispatch_term = OrchestratorDispatch(
        outcome=ORCH_DISPATCH_TERMINATE,
        reason=ORCH_REASON_DEAD_CHILDREN,
        detail="child chi001 (failed)",
        unfinished=(("chi001", "failed"),),
        unauthored_rows=(),
        eligibility=None,
    )
    with mock.patch(
        "agent_workflows.runner_shared.decide_orchestrator_dispatch",
        return_value=dispatch_term,
    ):
        dispatch_orchestrator_item(
            repo,
            tmp_path,
            state_term,
            item_term,
            actor="test-actor",
            terminal_states=TERMINAL_STATES,
            success_states=EXECUTION_SUCCESS_STATES,
            recovery_hint=hint,
        )

    assert item_term["status"] == "fail-depend"
    assert item_term.get("dependency_block_recovery") == hint
    assert item_term["unsatisfied_dependencies"] == ["executed:chi001"]

    # RECONSIDER path
    item_rec = {
        "position": 2,
        "id6": "orc002",
        "setid": "test",
        "action": "orchestrate",
        "status": "queued",
    }
    state_rec: dict[str, Any] = {
        "queue": [item_rec],
        "repo": str(repo),
        "run_id": "run-rec",
    }
    dispatch_rec = OrchestratorDispatch(
        outcome=ORCH_DISPATCH_RECONSIDER,
        reason=ORCH_REASON_UNFINISHED_CHILDREN,
        detail="child chi002 (queued)",
        unfinished=(("chi002", "queued"),),
        unauthored_rows=(),
        eligibility=None,
    )
    with mock.patch(
        "agent_workflows.runner_shared.decide_orchestrator_dispatch",
        return_value=dispatch_rec,
    ):
        dispatch_orchestrator_item(
            repo,
            tmp_path,
            state_rec,
            item_rec,
            actor="test-actor",
            terminal_states=TERMINAL_STATES,
            success_states=EXECUTION_SUCCESS_STATES,
            recovery_hint=hint,
        )

    assert item_rec["status"] == "queued"
    assert item_rec.get("dependency_block_recovery") is None


def test_write_report_renders_one_recovery_line_for_each_producer(
    tmp_path: Path,
) -> None:
    """write_report renders exactly one - Recovery: line per blocked item across all three producers."""
    hint = OC_HOST_LABELS.dependency_block_recovery
    cascade_item = {
        "position": 1,
        "id6": "cas001",
        "setid": "test",
        "action": "execute",
        "status": "fail-depend",
        "unsatisfied_dependencies": ["executed:prereq1"],
        "unsatisfied_dependency_reasons": {
            "executed:prereq1": "target prereq1 is failed"
        },
        "dependency_block_recovery": hint,
    }
    drain_item = {
        "position": 2,
        "id6": "drn001",
        "setid": "test",
        "action": "execute",
        "status": "fail-depend",
        "unsatisfied_dependencies": ["executed:prereq2"],
        "unsatisfied_dependency_reasons": {
            "executed:prereq2": "target prereq2 is missing"
        },
        "dependency_block_recovery": hint,
    }
    orch_item = {
        "position": 3,
        "id6": "orc001",
        "setid": "test",
        "action": "orchestrate",
        "status": "fail-depend",
        "unsatisfied_dependencies": ["executed:chi001"],
        "unsatisfied_dependency_reasons": {"executed:chi001": "child chi001 is failed"},
        "dependency_block_recovery": hint,
    }
    state: dict[str, Any] = {
        "queue": [cascade_item, drain_item, orch_item],
        "run_id": "run-three-producers",
    }
    write_report(tmp_path, state, labels=OC_HOST_LABELS)
    report_text = (tmp_path / "execution-report.md").read_text()

    assert "## Dependency blocks (why)" in report_text
    recovery_lines = [
        line.strip()
        for line in report_text.splitlines()
        if line.strip().startswith("- Recovery:")
    ]
    assert len(recovery_lines) == 3
    for line in recovery_lines:
        assert line == f"- Recovery: {hint}"


def test_drain_and_cascade_report_renders_correct_host_attribution(
    tmp_path: Path,
) -> None:
    """Report renders host-specific recovery hints without cross-host misattribution."""
    for host_name, labels in [("oc", OC_HOST_LABELS), ("agy", AGY_HOST_LABELS)]:
        h_dir = tmp_path / host_name
        h_dir.mkdir()
        item = {
            "position": 1,
            "id6": f"{host_name}001",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "unsatisfied_dependencies": ["executed:dep1"],
            "unsatisfied_dependency_reasons": {
                "executed:dep1": "target dep1 is failed"
            },
            "dependency_block_recovery": labels.dependency_block_recovery,
        }
        state: dict[str, Any] = {"queue": [item], "run_id": f"run-{host_name}"}
        write_report(h_dir, state, labels=labels)
        report_text = (h_dir / "execution-report.md").read_text()

        assert f"- Recovery: {labels.dependency_block_recovery}" in report_text
        other_cmd = (
            "aw agy runipd resume" if host_name == "oc" else "aw oc runipd resume"
        )
        assert other_cmd not in report_text


@pytest.mark.parametrize(
    "case_name",
    [
        "case_i_drain_external",
        "case_ii_findings_gate",
        "case_iii_cascade_token_free",
        "case_iv_frozen_record",
        "case_v_report_and_transient_waits",
        "case_vi_mid_sentence_no_overstrip",
        "case_vii_declared_bare_id6",
    ],
)
def test_dependency_reason_rendering_all_producer_shapes(
    case_name: str, tmp_path: Path
) -> None:
    """Tabled coverage for all seven reason shapes from the three live producers (E-06).

    Asserts token occurrence counts in rendered output across summary table,
    write_report, and render_transient_dependency_waits.
    """
    pending = tmp_path / ".aw" / "records" / "plans" / "pending"
    pending.mkdir(parents=True, exist_ok=True)

    if case_name == "case_i_drain_external":
        # (i) Drain/external shape from dependency_status_detailed against synthesized root
        (pending / "20260919-s-01-c1dep1-dep.ipd.md").write_text(
            "# IPD: dep\n\n- Id: c1dep1\n- Status: approved\n", encoding="utf-8"
        )
        token = "executed:c1dep1"
        item = {
            "position": 1,
            "id6": "c1itm1",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "dependencies": [token],
        }
        state = {"queue": [item], "repo": str(tmp_path), "run_id": "run-case-1"}
        sat, un_deps, un_reasons = dependency_status_detailed(item, state)
        assert not sat
        item["unsatisfied_dependencies"] = un_deps
        item["unsatisfied_dependency_reasons"] = un_reasons

        diags = _diag_lines(render_run_summary_table(state, pal=Palette(False)))
        assert len(diags) == 1
        # Token occurrence count in rendered line is exactly 1 (stripped from reason)
        assert diags[0].count(token) == 1
        assert un_reasons[token] not in diags[0]
        assert strip_dependency_reason_prefix(token, un_reasons[token]) in diags[0]

    elif case_name == "case_ii_findings_gate":
        # (ii) Findings-gate shape: prefix is bare id6, not token
        gb = GatingBlock("c2dep2", "F-01", "high", "open", "finding", "", "")
        reason = gb.describe()
        token = "executed:c2dep2"
        item = {
            "position": 1,
            "id6": "c2itm1",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "unsatisfied_dependencies": [token],
            "unsatisfied_dependency_reasons": {token: reason},
        }
        state = {"queue": [item], "run_id": "run-case-2"}
        diags = _diag_lines(render_run_summary_table(state, pal=Palette(False)))
        assert len(diags) == 1
        # Token occurrence count is exactly 1, and bare target id6 count is exactly 1
        assert diags[0].count(token) == 1
        assert diags[0].count("c2dep2") == 1
        assert reason not in diags[0]
        assert strip_dependency_reason_prefix(token, reason) in diags[0]

    elif case_name == "case_iii_cascade_token_free":
        # (iii) cascade_dependency_blocked token-free shape, byte-identical to HEAD
        prereq = {
            "position": 1,
            "id6": "aaa111",
            "status": "reviewed",
            "action": "execute",
        }
        cas = {
            "position": 2,
            "id6": "cas001",
            "setid": "test",
            "status": "queued",
            "action": "execute",
            "dependencies": ["executed:aaa111"],
        }
        state = {"queue": [prereq, cas], "run_id": "run-case-3"}
        cascade_dependency_blocked(state, run_dir=tmp_path)
        diags = _diag_lines(
            render_run_summary_table(
                {"queue": [cas], "run_id": "run-case-3-view"}, pal=Palette(False)
            )
        )
        assert len(diags) == 1
        assert (
            diags[0]
            == "  • cas001: fail-depend (executed:aaa111 (target aaa111 is reviewed))"
        )
        assert diags[0].count("executed:aaa111") == 1

    elif case_name == "case_iv_frozen_record":
        # (iv) Frozen-record item (embedded reason, no map)
        item = {
            "position": 1,
            "id6": "eee555",
            "setid": "test",
            "action": "execute",
            "status": "dependency-blocked",
            "unsatisfied_dependencies": ["executed:aaa111 (target reviewed)"],
        }
        state = {"queue": [item], "run_id": "run-case-4"}
        out = render_run_summary_table(state, pal=Palette(False))
        diags = _diag_lines(out)
        assert len(diags) == 1
        assert (
            diags[0]
            == "  • eee555: dependency-blocked (executed:aaa111 (target reviewed))"
        )
        assert "(blocked)" not in out
        assert diags[0].count("executed:aaa111") == 1

    elif case_name == "case_v_report_and_transient_waits":
        # (v) write_report and render_transient_dependency_waits for drain item
        (pending / "20260919-s-01-c5dep1-dep.ipd.md").write_text(
            "# IPD: dep\n\n- Id: c5dep1\n- Status: approved\n", encoding="utf-8"
        )
        token = "executed:c5dep1"
        item = {
            "position": 1,
            "id6": "c5itm1",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "dependencies": [token],
        }
        state = {"queue": [item], "repo": str(tmp_path), "run_id": "run-case-5"}
        _, un_deps, un_reasons = dependency_status_detailed(item, state)
        item["unsatisfied_dependencies"] = un_deps
        item["unsatisfied_dependency_reasons"] = un_reasons

        # write_report check
        rep_dir = tmp_path / "rep"
        rep_dir.mkdir()
        write_report(rep_dir, state, labels=OC_HOST_LABELS)
        rep_text = (rep_dir / "execution-report.md").read_text()
        rep_lines = [line for line in rep_text.splitlines() if f"- `{token}`:" in line]
        assert len(rep_lines) == 1
        # Token occurrence count is exactly 1 (backtick label only)
        assert rep_lines[0].count(token) == 1
        assert strip_dependency_reason_prefix(token, un_reasons[token]) in rep_lines[0]

        # render_transient_dependency_waits check
        trans_item = {
            "position": 1,
            "id6": "c5itm1",
            "setid": "test",
            "action": "execute",
            "status": "queued",
            TRANSIENT_DEPENDENCY_WAIT_KEY: {
                "unsatisfied_dependencies": [token],
                "unsatisfied_dependency_reasons": un_reasons,
                "detail": f"{token}: prerequisite drain wait detail",
            },
        }
        t_lines = render_transient_dependency_waits({"queue": [trans_item]})
        t_dep_lines = [line for line in t_lines if f"- `{token}`:" in line]
        assert len(t_dep_lines) == 1
        # Token occurrence count is exactly 1
        assert t_dep_lines[0].count(token) == 1
        assert (
            strip_dependency_reason_prefix(token, un_reasons[token]) in t_dep_lines[0]
        )
        # Why this is not terminal line loses leading token prefix
        detail_lines = [line for line in t_lines if "Why this is not terminal:" in line]
        assert len(detail_lines) == 1
        assert detail_lines[0].count(token) == 0
        assert "prerequisite drain wait detail" in detail_lines[0]

    elif case_name == "case_vi_mid_sentence_no_overstrip":
        # (vi) Mid-sentence token mention preserved
        token = "executed:bbb222"
        reason = "executed:bbb222: waits on executed:aaa111 which is pending"
        item = {
            "position": 1,
            "id6": "c6itm1",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "unsatisfied_dependencies": [token],
            "unsatisfied_dependency_reasons": {token: reason},
        }
        state = {"queue": [item], "run_id": "run-case-6"}
        diags = _diag_lines(render_run_summary_table(state, pal=Palette(False)))
        assert len(diags) == 1
        # Token occurrence count is exactly 1
        assert diags[0].count(token) == 1
        # Inner mid-sentence token is preserved intact
        assert "executed:aaa111" in diags[0]
        assert "waits on executed:aaa111 which is pending" in diags[0]

    elif case_name == "case_vii_declared_bare_id6":
        # (vii) Declared bare-id6 shape (F-11 / PR-001)
        (pending / "20260919-s-01-c7dep1-dep.ipd.md").write_text(
            "# IPD: dep\n\n- Id: c7dep1\n- Status: approved\n", encoding="utf-8"
        )
        bare_token = "c7dep1"
        item = {
            "position": 1,
            "id6": "c7itm1",
            "setid": "test",
            "action": "execute",
            "status": "fail-depend",
            "dependencies": [bare_token],
        }
        state = {"queue": [item], "repo": str(tmp_path), "run_id": "run-case-7"}
        sat, un_deps, un_reasons = dependency_status_detailed(item, state)
        assert not sat
        assert un_deps == [bare_token]
        # Map key is the bare id6 AS DECLARED
        assert list(un_reasons.keys()) == [bare_token]
        # Reason itself begins with canonical prefix
        assert un_reasons[bare_token].startswith(f"executed:{bare_token}:")

        item["unsatisfied_dependencies"] = un_deps
        item["unsatisfied_dependency_reasons"] = un_reasons
        diags = _diag_lines(render_run_summary_table(state, pal=Palette(False)))
        assert len(diags) == 1
        # Canonical prefix is stripped, so executed:c7dep1 does not appear in line
        assert diags[0].count(f"executed:{bare_token}") == 0
        # id6 occurrence count in rendered line falls from 3 to 2 (unstripped would be 3)
        assert diags[0].count(bare_token) == 2
        assert (
            strip_dependency_reason_prefix(bare_token, un_reasons[bare_token])
            in diags[0]
        )
