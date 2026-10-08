"""Behavioral regression tests for precommit_scope_gate severity-derived exit code (IPD t6ledu).

Tests observable behavior and outcomes only: drives real hooks/precommit_scope_gate.check
and main entrypoint, asserting on real return values, exit codes, and output contracts.
Does not inspect source code via inspect/ast/regex or assert symbol/line censuses (GUIDING_PRINCIPLES P16).
"""

from unittest.mock import patch
import io
from agent_workflows import artifact_core as _ac
from agent_workflows import check_engine as _ce
from agent_workflows.hooks import precommit_scope_gate


def test_info_finding_reported_not_refused():
    """Case (a): a single info-severity finding yields exit 0 AND a non-empty messages list."""
    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.spec-criteria-uncovered",
            detail="uncovered criteria advisory",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        exit_code, messages = precommit_scope_gate.check()
    assert exit_code == 0
    assert len(messages) == 1
    assert "check.spec-criteria-uncovered" in messages[0]


def test_warning_finding_refused():
    """Case (b): a single warning finding yields exit 1."""
    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.setid-length-warn",
            detail="setid exceeds recommended length",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        exit_code, messages = precommit_scope_gate.check()
    assert exit_code == 1
    assert len(messages) == 1
    assert "check.setid-length-warn" in messages[0]


def test_error_finding_refused():
    """Case (c): a single error finding yields exit 1."""
    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.scope-drift",
            detail="scope drift error",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        exit_code, messages = precommit_scope_gate.check()
    assert exit_code == 1
    assert len(messages) == 1
    assert "check.scope-drift" in messages[0]


def test_empty_findings_clean():
    """Case (d): an empty findings list yields exit 0 with no messages."""
    with patch.object(_ce, "check_commit_invariants", return_value=[]):
        exit_code, messages = precommit_scope_gate.check()
    assert exit_code == 0
    assert messages == []


def test_info_with_preset_recovery_through_aggregator():
    """Case (e): finding with rule id registered info carrying a non-empty recovery,
    arriving through real check_commit_invariants with check_scope_drift patched.

    Pins PR-001 / F-9: check_commit_invariants enriches only `if not d.recovery`,
    so a pre-set recovery reaches the hook with empty severity. The hook must backfill
    severity before evaluating drift_exit_code, otherwise drift_exit_code treats
    empty severity as failing (exit 1).
    """
    d = _ac.Drift(
        location="test_plan.ipd.md",
        rule="check.spec-criteria-uncovered",
        detail="scope not audited or criteria uncovered",
        recovery="restrict the change to Scope-Paths",
    )
    with patch.object(_ce, "check_status_untooled", return_value=[]), patch.object(
        _ce, "check_staged_illegal_backlog_transition", return_value=[]
    ), patch.object(
        _ce, "check_release_gate_consistency", return_value=[]
    ), patch.object(_ce, "check_scope_drift", return_value=[d]):
        exit_code, messages = precommit_scope_gate.check()
    assert exit_code == 0
    assert len(messages) == 1
    assert "check.spec-criteria-uncovered" in messages[0]
    assert "fix: restrict the change to Scope-Paths" in messages[0]


def test_main_agent_mode_advisory_envelope():
    """main() in --agent mode emits outcome: clean, exit: 0, findings: 1 (PR-002 / F-10)."""
    import json

    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.spec-criteria-uncovered",
            detail="uncovered criteria advisory",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        out = io.StringIO()
        with patch("sys.stdout", out):
            rc = precommit_scope_gate.main(argv=["--agent"])
        assert rc == 0
        data = json.loads(out.getvalue())
        assert data["cmd"] == "precommit-scope-gate"
        assert data["outcome"] == "clean"
        assert data["exit"] == 0
        assert data["findings"] == 1


def test_main_json_mode_advisory_distinguished_summary():
    """main() in --json mode emits status: clean, exit_code: 0, with distinguishing summary (PR-002)."""
    import json

    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.spec-criteria-uncovered",
            detail="uncovered criteria advisory",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        out = io.StringIO()
        with patch("sys.stdout", out):
            rc = precommit_scope_gate.main(argv=["--json"])
        assert rc == 0
        data = json.loads(out.getvalue())
        assert data["command"] == "precommit-scope-gate"
        assert data["status"] == "clean"
        assert data["exit_code"] == 0
        assert len(data["diagnostics"]) == 1
        assert "advisory" in data["summary"].lower()


def test_main_human_mode_advisory_no_refusal_assertion():
    """main() in human mode prints advisory without asserting REFUSED (PR-002 / E-02)."""
    d = _ce.enrich_drift(
        _ac.Drift(
            location="test_doc.md",
            rule="check.spec-criteria-uncovered",
            detail="uncovered criteria advisory",
        )
    )
    with patch.object(_ce, "check_commit_invariants", return_value=[d]):
        err = io.StringIO()
        with patch("sys.stderr", err):
            rc = precommit_scope_gate.main(argv=[])
        assert rc == 0
        stderr_val = err.getvalue()
        assert "REFUSED this commit" not in stderr_val
        assert "check.spec-criteria-uncovered" in stderr_val
