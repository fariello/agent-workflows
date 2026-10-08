"""Tests that doctor translates sanitizer severities into the canonical vocabulary (IPD 36sifo).

The 'fail' severity mapping is covered end-to-end through the real CLI over a fixture
repository. The 'warn' severity mapping is covered through a production seam by patching
leak_sanitizer.scan_working_tree_counted in doctor's namespace, because doctor calls the scanner
with include_warn=False by default (compiling zero warn rules), making a CLI-only warn finding
unreachable without altering doctor's scanning policy.

Tests test observable behavior, command outputs, structured payloads, and exit codes only;
no production source code inspection.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from agent_workflows import doctor
from agent_workflows import leak_sanitizer
from agent_workflows import term as T
from tests.support import git, init_repo, run_cli


CANONICAL_SEVERITIES = {"error", "warning", "info"}
RAW_SANITIZER_SEVERITIES = {"fail", "warn"}


def test_doctor_translates_fail_sanitizer_severity_end_to_end(tmp_path: Path) -> None:
    """Doctor CLI translates fail-severity sanitizer findings to canonical error end-to-end.

    Pins that:
    1. Every finding in data.report.sanitizer.findings has severity in {'error', 'warning', 'info'}
       (specifically 'error', not raw 'fail').
    2. Every sibling doctor.leak-* diagnostic in diagnostics has severity in the canonical set,
       and its detail string does not carry the raw 'fail:' prefix.
    3. The human report does not render the raw 'fail:' prefix in the finding line.
    4. Exit code is unchanged (remains 1 for leak findings).
    """
    repo = init_repo(tmp_path / "leak_repo")
    planted = "/home/" + "someuser/secret.txt"
    (repo / "leaking_file.py").write_text(f'P = "{planted}"\n', encoding="utf-8")
    git(repo, "add", "leaking_file.py")
    git(repo, "commit", "-qm", "commit leak")

    # 1. JSON CLI output
    proc_json = run_cli("doctor", "--dir", str(repo), "--json", cwd=repo)
    assert (
        proc_json.returncode == 1
    ), f"Expected exit code 1, got {proc_json.returncode}. Stderr: {proc_json.stderr}"

    data = json.loads(proc_json.stdout)
    san_findings = (
        data.get("data", {}).get("report", {}).get("sanitizer", {}).get("findings", [])
    )
    assert (
        len(san_findings) > 0
    ), f"Expected at least one sanitizer finding in: {proc_json.stdout}"

    for f in san_findings:
        sev = f.get("severity")
        assert (
            sev in CANONICAL_SEVERITIES
        ), f"Raw/non-canonical severity {sev!r} in sanitizer finding: {f}"
        assert (
            sev not in RAW_SANITIZER_SEVERITIES
        ), f"Raw sanitizer token {sev!r} found in finding: {f}"
        assert sev == "error", f"Expected 'fail' to translate to 'error', got {sev!r}"

    leak_diags = [
        d
        for d in data.get("diagnostics", [])
        if d.get("rule", "").startswith("doctor.leak-")
    ]
    assert (
        len(leak_diags) > 0
    ), f"Expected at least one doctor.leak-* diagnostic in: {proc_json.stdout}"
    for d in leak_diags:
        sev = d.get("severity")
        assert (
            sev in CANONICAL_SEVERITIES
        ), f"Raw/non-canonical severity {sev!r} in diagnostic: {d}"
        assert not d.get("detail", "").startswith(
            "fail:"
        ), f"Diagnostic detail retains raw 'fail:' prefix: {d}"
        assert d.get("detail", "").startswith(
            "error:"
        ), f"Diagnostic detail should start with 'error:': {d}"

    # 2. Human CLI output under NO_COLOR=1
    proc_human = run_cli("doctor", "--dir", str(repo), env={"NO_COLOR": "1"}, cwd=repo)
    assert (
        proc_human.returncode == 1
    ), f"Expected exit code 1, got {proc_human.returncode}"
    leak_lines = [
        line for line in proc_human.stdout.splitlines() if "leaking_file.py" in line
    ]
    assert (
        len(leak_lines) > 0
    ), f"Expected leaking_file.py in human output:\n{proc_human.stdout}"
    for line in leak_lines:
        assert "(fail:" not in line, f"Raw '(fail:' found in human report line: {line}"
        assert "(error:" in line, f"Expected '(error:' in human report line: {line}"


def test_doctor_translates_warn_sanitizer_severity_via_seam(tmp_path: Path) -> None:
    """Doctor translates warn-severity sanitizer findings to canonical warning via production seam.

    Pins that:
    1. SanitizerProbeResult.to_dict translates 'warn' -> 'warning'.
    2. probe_sanitizer builds drift with detail prefixed by 'warning:' and Drift.severity == 'warning'.
    3. render_human_report renders '(warning: ...)' instead of '(warn: ...)'.
    """
    repo = init_repo(tmp_path / "seam_repo")

    mock_finding = leak_sanitizer.Finding(
        location="sample.py:1",
        rule="derived:host",
        severity="warn",
        snippet="hostname_leak_token",
    )

    with patch.object(
        doctor.leak_sanitizer,
        "scan_working_tree_counted",
        return_value=([mock_finding], 1),
    ):
        res = doctor.probe_sanitizer(repo)

        # 1. Check to_dict serialization
        d = res.to_dict()
        assert len(d["findings"]) == 1
        finding_dict = d["findings"][0]
        assert finding_dict["severity"] in CANONICAL_SEVERITIES
        assert finding_dict["severity"] == "warning"
        assert finding_dict["severity"] not in RAW_SANITIZER_SEVERITIES

        # 2. Check probe_sanitizer drift construction
        assert len(res.drift) == 1
        drift = res.drift[0]
        assert drift.detail.startswith(
            "warning: "
        ), f"Expected detail starting with 'warning: ', got {drift.detail!r}"
        assert not drift.detail.startswith(
            "warn: "
        ), f"Raw 'warn: ' found in drift detail: {drift.detail!r}"
        assert (
            drift.severity == "warning"
        ), f"Expected drift.severity == 'warning', got {drift.severity!r}"

        # 3. Check human rendering
        report = doctor.DoctorReport(
            repo_root=repo,
            git=doctor.probe_git(repo),
            env=doctor.probe_environment(repo),
            attention=doctor.probe_attention(repo),
            artifacts=doctor.probe_artifacts(repo),
            sanitizer=res,
            all_drift=list(res.drift),
        )
        term = T.Term(color=False)
        rendered = doctor.render_human_report(report, term)
        leak_lines = [line for line in rendered.splitlines() if "sample.py" in line]
        assert (
            len(leak_lines) == 1
        ), f"Expected finding line in human report:\n{rendered}"
        assert (
            "(warn:" not in leak_lines[0]
        ), f"Raw '(warn:' in rendered output: {leak_lines[0]}"
        assert (
            "(warning:" in leak_lines[0]
        ), f"Expected '(warning:' in rendered output: {leak_lines[0]}"


def test_doctor_translates_unrecognized_sanitizer_severity_to_error_via_seam(
    tmp_path: Path,
) -> None:
    """Doctor conservatively maps unrecognized sanitizer severity tokens to canonical 'error'."""
    repo = init_repo(tmp_path / "seam_unknown_repo")

    mock_finding = leak_sanitizer.Finding(
        location="sample.py:1",
        rule="derived:host",
        severity="novel_future_token",
        snippet="token",
    )

    with patch.object(
        doctor.leak_sanitizer,
        "scan_working_tree_counted",
        return_value=([mock_finding], 1),
    ):
        res = doctor.probe_sanitizer(repo)
        d = res.to_dict()
        assert d["findings"][0]["severity"] == "error"
        assert res.drift[0].detail.startswith("error: ")
        assert res.drift[0].severity == "error"
