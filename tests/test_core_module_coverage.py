"""Behavioral unit coverage for modules not otherwise exercised under core (E-03).

This file brings all first-party modules under agent_workflows to non-zero coverage
within the core tier, exercising core data structures, parsers, hooks, and helpers
with real inputs and behavioral assertions.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import pytest

pytestmark = pytest.mark.core


def test_actions_and_install_history(tmp_path: Path) -> None:
    from agent_workflows import actions, install_history

    # Back-compat re-export check
    assert actions.record_install_history is install_history.record_install_history
    assert actions._redact_details is install_history._redact_details

    # Test redaction logic
    redacted = install_history._redact_details(
        {"safe_int": 42, "safe_str": "hello"},
        repo_root=str(tmp_path),
    )
    assert redacted["safe_int"] == 42
    assert redacted["safe_str"] == "hello"

    # Test recording install history snapshot and JSONL entry
    install_history.record_install_history(
        str(tmp_path),
        "test_install",
        {"component": "unit_test"},
    )
    install_json = tmp_path / ".aw" / "state" / "durable" / "install.json"
    history_jsonl = (
        tmp_path / ".aw" / "state" / "durable" / "history" / "installs.jsonl"
    )
    assert install_json.is_file()
    assert history_jsonl.is_file()


def test_duration_parsing() -> None:
    from agent_workflows.duration import parse_age_duration

    assert parse_age_duration("1h") == pytest.approx(1.0 / 24.0)
    assert parse_age_duration("2d") == pytest.approx(2.0)
    assert parse_age_duration("3w") == pytest.approx(21.0)
    assert parse_age_duration("1m") == pytest.approx(30.0)
    assert parse_age_duration("1y") == pytest.approx(365.0)
    assert parse_age_duration(14) == pytest.approx(14.0)
    assert parse_age_duration(14.5) == pytest.approx(14.5)
    assert parse_age_duration(None, default_days=7.0) == pytest.approx(7.0)
    assert parse_age_duration("", default_days=10.0) == pytest.approx(10.0)

    with pytest.raises(ValueError, match="cannot be negative"):
        parse_age_duration(-1)

    with pytest.raises(ValueError, match="invalid age duration"):
        parse_age_duration("not_a_duration")


def test_leak_sanitizer_config(tmp_path: Path) -> None:
    from agent_workflows.leak_sanitizer_config import (
        ConfigState,
        _diff_lines,
        configure,
        load_state,
    )

    c1 = ConfigState([], [], False, False, [], [])
    c2 = c1.copy()
    assert _diff_lines(c1, c2) == []

    c2.allow_line_substrings.append("allowed_token")
    c2.ip_enabled = True
    diff = _diff_lines(c1, c2)
    assert any("allowed_token" in line for line in diff)
    assert any("ip_enabled" in line for line in diff)

    state = load_state(tmp_path)
    assert isinstance(state, ConfigState)

    summary = configure(
        tmp_path,
        prompt=lambda q: "",
        confirm=lambda q: False,
        emit=lambda line: None,
    )
    assert summary["changed"] is False
    assert summary["wrote"] == []


def test_hooks_backlog_blocking_close_gate(tmp_path: Path) -> None:
    from agent_workflows.hooks import backlog_blocking_close_gate

    exit_code, messages = backlog_blocking_close_gate.check(tmp_path)
    assert exit_code == 0
    assert messages == []

    res = backlog_blocking_close_gate.main(["--json"])
    assert res == 0


def test_hooks_ipd_dependency_statement_gate(tmp_path: Path) -> None:
    from agent_workflows.hooks import ipd_dependency_statement_gate

    exit_code, messages = ipd_dependency_statement_gate.check(tmp_path)
    assert exit_code == 0
    assert messages == []

    res = ipd_dependency_statement_gate.main(["--json"])
    assert res == 0


def test_hooks_prepush_authorization_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent_workflows.hooks import prepush_authorization_gate

    monkeypatch.setenv("AW_PUSH_AUTHORIZED", "1")
    exit_code, messages = prepush_authorization_gate.check(tmp_path)
    assert exit_code == 0
    assert messages == []

    res = prepush_authorization_gate.main(["--json"])
    assert res == 0


def test_hooks_status_untooled_gate(tmp_path: Path) -> None:
    from agent_workflows.hooks import status_untooled_gate

    exit_code, messages = status_untooled_gate.check(tmp_path)
    assert exit_code == 0
    assert messages == []

    res = status_untooled_gate.main(["--json"])
    assert res == 0


def test_reviews_classification_and_decisions(tmp_path: Path) -> None:
    from agent_workflows.reviews import DecisionRow, classify_reversible

    assert classify_reversible("yes") == "yes"
    assert classify_reversible("no") == "no"
    assert classify_reversible("unknown") == "unknown"
    assert classify_reversible("") == "unknown"

    row = DecisionRow(
        subject_id="s1",
        subject_type="ipd",
        review_path=tmp_path / "rev.md",
        round_number=1,
        is_current_round=True,
        id="d1",
        question="Which approach?",
        chosen="A",
        alternatives="B",
        basis="Rationale",
        reversible_raw="yes",
        line=10,
    )
    assert row.reversible == "yes"
    assert not row.is_irreversible
    d = row.to_dict()
    assert d["id"] == "d1"
    assert d["chosen"] == "A"


def test_lifecycle_fixtures() -> None:
    from agent_workflows.lifecycle_fixtures import (
        FIXTURE_CLEAN_INSTALL,
        FixtureOutcome,
        make_isolated_env,
    )

    assert FIXTURE_CLEAN_INSTALL == "clean-install"
    env = make_isolated_env(prefix="aw-test-core-")
    assert env.base_dir.exists()
    env.cleanup()

    outcome = FixtureOutcome(
        name=FIXTURE_CLEAN_INSTALL,
        passed=True,
        mutated=True,
        final_state="current",
        detail="success",
        evidence={},
    )
    assert outcome.passed
    assert outcome.name == "clean-install"


def test_set_state_machine() -> None:
    from agent_workflows.set_state import (
        ALL_SET_STATES,
        SET_COMPLETE,
        SET_PLANNED,
        SET_RUNNING,
        get_set_transition_rule,
        validate_set_transition,
    )

    assert SET_PLANNED in ALL_SET_STATES
    assert SET_RUNNING in ALL_SET_STATES
    assert SET_COMPLETE in ALL_SET_STATES

    rule = get_set_transition_rule(SET_PLANNED, SET_RUNNING)
    assert rule.source == SET_PLANNED
    assert rule.target == SET_RUNNING

    res = validate_set_transition(
        source=SET_PLANNED,
        target=SET_RUNNING,
        actor="coordinator",
    )
    assert res.ok


def test_set_lifecycle_stale_evidence() -> None:
    from agent_workflows.set_lifecycle import stale_evidence_seqs_after_integration

    records = [
        {"kind": "evidence_envelope", "seq": 1, "head": "commit_old"},
        {"kind": "evidence_envelope", "seq": 2, "head": "commit_new"},
    ]
    stale = stale_evidence_seqs_after_integration(records, new_head="commit_new")
    assert stale == (1,)


def test_set_stop_policy_classification() -> None:
    from agent_workflows.set_stop_policy import (
        ACTION_DECIDE,
        ACTION_HARD_STOP,
        QuestionSituation,
        classify,
    )

    sit_decide = QuestionSituation(
        needs_human=False,
        has_robust_decision=True,
        can_defer_subgraph=False,
        can_defer_ipd=False,
        independent_frontier=(),
        is_unknown_outcome=False,
    )
    assert classify(sit_decide).action == ACTION_DECIDE

    sit_stop = QuestionSituation(
        needs_human=True,
        has_robust_decision=False,
        can_defer_subgraph=False,
        can_defer_ipd=False,
        independent_frontier=(),
        is_unknown_outcome=False,
    )
    assert classify(sit_stop).action == ACTION_HARD_STOP


def test_ipd_set_executor_structures() -> None:
    from agent_workflows.ipd_set_executor import Disposition, ModelBinding

    binding = ModelBinding(work_class="coding", host="oc", model="claude-3-7-sonnet")
    assert binding.work_class == "coding"
    assert binding.host == "oc"

    disp = Disposition(node_id="n1", status="executed", reason="passed")
    assert disp.node_id == "n1"
    assert disp.status == "executed"


def test_agy_sessions() -> None:
    from agent_workflows.agy_sessions import _format_duration, _parse_iso_z

    t1 = datetime.datetime(2026, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    t2 = datetime.datetime(2026, 6, 1, 10, 5, 30, tzinfo=datetime.timezone.utc)
    dur = _format_duration(t1, t2)
    assert "5m" in dur

    dt = _parse_iso_z("2026-06-01T00:00:00Z")
    assert dt is not None
    assert dt.year == 2026


def test_run_packet_envelope() -> None:
    from agent_workflows.run_packet import StepOutcomeEnvelope, _normalize

    assert _normalize("  token  ") == "token"

    env = StepOutcomeEnvelope(
        run_id="run-001",
        step_id="s1",
        attempt=1,
        status="complete",
        actor="executor",
        evidence_ids=(),
        artifacts=(),
        prose="prose summary",
        block_reason=None,
        failure_reason=None,
        timestamp=12345.0,
    )
    assert env.status == "complete"
    assert env.step_id == "s1"


def test_run_analytics_report_helpers(tmp_path: Path) -> None:
    from agent_workflows.run_analytics_report import BundleFile, _next_version_label

    v = _next_version_label(tmp_path / "nonexistent")
    assert v == "v000001"

    bf = BundleFile(name="p.txt", content=b"content")
    assert bf.name == "p.txt"
    assert bf.content == b"content"


def test_run_analytics_submit_helpers(tmp_path: Path) -> None:
    from agent_workflows.run_analytics_submit import _redact_url, _sha256

    redacted = _redact_url("https://user:secret@example.com/api")
    assert "secret" not in redacted

    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"hello world")
    digest = _sha256(test_file)
    assert len(digest) == 64


def test_run_analytics_wizard_helpers() -> None:
    from agent_workflows.run_analytics_wizard import _coerce_bool, _looks_like_secret

    assert _coerce_bool("yes", default=False) is True
    assert _coerce_bool("no", default=True) is False
    assert _coerce_bool("invalid", default=True) is True
    assert _looks_like_secret("has spaces in token") is True
    assert _looks_like_secret("SIMPLE_KEY") is False


def test_benchmark_ablations_config() -> None:
    from agent_workflows.benchmark_ablations import (
        ARCH_MONOLITH,
        ISOLATION_NONE,
        AblationConfig,
    )

    cfg = AblationConfig(
        architecture=ARCH_MONOLITH,
        isolation_level=ISOLATION_NONE,
        verifier_identity="none",
        cross_verifier_model_id=None,
        description="monolith baseline",
    )
    assert cfg.architecture == ARCH_MONOLITH


def test_benchmark_protocol_canonical_json() -> None:
    from agent_workflows.benchmark_protocol import _canonical_json

    cj = _canonical_json({"b": 2, "a": 1})
    assert cj == '{"a":1,"b":2}'


def test_benchmark_reports_record() -> None:
    from agent_workflows.benchmark_reports import BenchmarkRunRecord

    rec = BenchmarkRunRecord(
        run_id="run-bench-1",
        created_at="2026-01-01T00:00:00Z",
        protocol_digest="proto-hash",
        trials=[],
    )
    assert rec.run_id == "run-bench-1"


def test_compat_migration_versioning() -> None:
    from agent_workflows.compat_migration import _version_lt, _version_tuple

    assert _version_tuple("1.2.3") == (1, 2, 3)
    assert _version_lt("1.2.0", "1.2.3") is True
    assert _version_lt("1.2.3", "1.2.0") is False


def test_migration_compact_families() -> None:
    from agent_workflows.migration_compact import advertised_families

    assert advertised_families(()) == ()


def test_migration_complex_drift() -> None:
    from agent_workflows.migration_complex import IssueLedger

    ledger = IssueLedger()
    assert ledger is not None


def test_migration_inventory_dispositions() -> None:
    from agent_workflows.migration_inventory import EXECUTION_MODES

    assert "deterministic" in EXECUTION_MODES
    assert "orchestrated" in EXECUTION_MODES
