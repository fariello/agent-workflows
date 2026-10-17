"""Behavior tests pinning doctor machine diagnostic severity preservation.

IPD: 2t9l37 (Set wxpytg, Order 1).
Governs:
- Preservation of real severity in `doctor.inspect_repo` (explicit drift severity -> rule registry fallback -> error default).
- Exit-code neutrality: info-only drifts yield exit code 0 and status 'clean' while diagnostics report severity 'info'.
- End-to-end CLI behavior on `--agent --verbose` and `--json` surfaces.

Tests test observable behavior, command outputs, and exit codes only; no production source code inspection.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflows import artifact_core as core
from agent_workflows import check_engine, doctor
from tests.conformance_matrix import run_cli_inproc
from tests.support import init_repo


def run_cli(*args: str, cwd: Path | None = None):
    return run_cli_inproc(list(args), cwd=cwd)


def test_doctor_inspect_repo_preserves_diagnostic_severity_seam(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """doctor.inspect_repo preserves drift severity, rule-spec fallback, and default error."""
    repo = init_repo(tmp_path / "doctor_repo")

    drifts = [
        core.Drift(
            location="loc/explicit_info",
            rule="test.rule.info",
            detail="explicit info detail",
            severity="info",
        ),
        core.Drift(
            location="loc/explicit_warning",
            rule="test.rule.warning",
            detail="explicit warning detail",
            severity="warning",
        ),
        core.Drift(
            location="loc/registered_info",
            rule="doctor.dangling-doc-reference",
            detail="registered info detail",
            severity="",
        ),
        core.Drift(
            location="loc/unregistered_rule",
            rule="test.rule.unregistered",
            detail="unregistered rule detail",
            severity="",
        ),
    ]

    monkeypatch.setattr(
        doctor,
        "run_doctor",
        lambda repo_root, include_untracked=False, include_executed=False: drifts,
    )

    res = doctor.inspect_repo(repo)

    assert len(res.diagnostics) == 4
    by_key = {(d.location, d.rule): d.severity for d in res.diagnostics}
    assert by_key[("loc/explicit_info", "test.rule.info")] == "info"
    assert by_key[("loc/explicit_warning", "test.rule.warning")] == "warning"
    assert by_key[("loc/registered_info", "doctor.dangling-doc-reference")] == "info"
    assert by_key[("loc/unregistered_rule", "test.rule.unregistered")] == "error"


def test_doctor_inspect_repo_info_only_exit_code_and_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Info-only findings yield exit code 0 and status 'clean' while diagnostics report severity 'info'."""
    repo = init_repo(tmp_path / "doctor_repo_info")

    drifts = [
        core.Drift(
            location="loc/info_one",
            rule="doctor.dangling-doc-reference",
            detail="info drift 1",
            severity="info",
        ),
        core.Drift(
            location="loc/info_two",
            rule="test.rule.info",
            detail="info drift 2",
            severity="info",
        ),
    ]

    monkeypatch.setattr(
        doctor,
        "run_doctor",
        lambda repo_root, include_untracked=False, include_executed=False: drifts,
    )

    res = doctor.inspect_repo(repo)

    assert core.drift_exit_code(drifts) == 0
    assert res.exit_code == 0
    assert res.status == "clean"
    assert len(res.diagnostics) == 2
    for d in res.diagnostics:
        assert d.severity == "info"


def test_doctor_cli_preserves_diagnostic_severity_e2e(tmp_path: Path) -> None:
    """aw doctor --agent --verbose and --json preserve severity for dangling-doc-reference and untracked."""
    repo = init_repo(tmp_path / "doctor_cli_repo")

    agents_content = (
        "# AGENTS\n\n"
        "<!-- aw:block -->\n"
        "Reference to missing `docs/missing-thing.md`.\n"
        "<!-- /aw:block -->\n"
    )
    (repo / "AGENTS.md").write_text(agents_content, encoding="utf-8")
    (repo / "untracked-file.txt").write_text("untracked content\n", encoding="utf-8")

    proc_agent = run_cli("doctor", "--agent", "--verbose", cwd=repo)
    data_agent = json.loads(proc_agent.stdout)

    proc_json = run_cli("doctor", "--json", cwd=repo)
    data_json = json.loads(proc_json.stdout)

    allowed_severities = {"error", "warning", "info"}
    expected_untracked_severity = check_engine.rule_spec(
        "doctor.git-untracked"
    ).severity

    for surface_name, data in [("agent", data_agent), ("json", data_json)]:
        diagnostics = data.get("diagnostics", [])
        assert (
            len(diagnostics) > 0
        ), f"{surface_name}: diagnostics list must not be empty"

        for diag in diagnostics:
            sev = diag.get("severity")
            assert (
                sev in allowed_severities
            ), f"{surface_name}: diagnostic {diag} has invalid severity '{sev}'"

        dangling = [
            d for d in diagnostics if d.get("rule") == "doctor.dangling-doc-reference"
        ]
        assert (
            len(dangling) == 1
        ), f"{surface_name}: expected 1 dangling doc reference diagnostic, got {dangling}"
        assert (
            dangling[0].get("severity") == "info"
        ), f"{surface_name}: doctor.dangling-doc-reference diagnostic severity must be 'info', got '{dangling[0].get('severity')}'"

        untracked = [d for d in diagnostics if d.get("rule") == "doctor.git-untracked"]
        assert (
            len(untracked) >= 1
        ), f"{surface_name}: expected at least 1 doctor.git-untracked diagnostic"
        for u in untracked:
            assert (
                u.get("severity") == expected_untracked_severity
            ), f"{surface_name}: doctor.git-untracked diagnostic severity must match rule_spec, got '{u.get('severity')}'"
