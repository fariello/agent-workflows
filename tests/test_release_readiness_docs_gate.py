"""Behavioral tests for wiring docs checks into the release-readiness gate.

Verifies that gate_docs_checks computes findings from docs/, distinguishes clean
from dirty trees, fails closed on missing trees or checker errors, supports
explicit injection hermetically, and serializes DocFinding objects cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path


from agent_workflows import docs_check as dc
from agent_workflows import release_readiness as rr


def _setup_go_fixture(repo_root: Path) -> Path:
    """Create minimal repo structure satisfying all non-subprocess gates."""
    changelog = repo_root / "CHANGELOG.md"
    changelog.write_text("## 1.0.0 - 2026-10-02\nInitial release\n", encoding="utf-8")
    vdir = repo_root / ".aw" / "system"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "VERSION").write_text("1.0.0\n", encoding="utf-8")
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "index.md").write_text(
        "# Documentation\nClean text with ASCII hyphen.\n", encoding="utf-8"
    )
    return docs_dir


def test_dirty_docs_tree_fails_gate(tmp_path: Path) -> None:
    """Arm (a): falsifiability - a docs tree with a violation fails gate_docs_checks."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "violation.md").write_text(
        "Prose with an em \u2014 dash.\n", encoding="utf-8"
    )

    res = rr.gate_docs_checks(repo_root=tmp_path)
    assert res.name == "docs_checks"
    assert res.passed is False
    assert "1 doc finding(s)" in res.detail
    assert len(res.evidence.get("findings", [])) == 1


def test_clean_docs_tree_passes_gate(tmp_path: Path) -> None:
    """Arm (b): a clean docs tree passes gate_docs_checks."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "clean.md").write_text(
        "# Documentation\nClean text with ASCII hyphen.\n", encoding="utf-8"
    )

    res = rr.gate_docs_checks(repo_root=tmp_path)
    assert res.name == "docs_checks"
    assert res.passed is True
    assert res.detail == "docs checks pass"
    assert res.evidence == {"findings": []}


def test_missing_docs_directory_fails_gate(tmp_path: Path) -> None:
    """Arm (c): an absent docs directory fails closed with a distinct detail."""
    res = rr.gate_docs_checks(repo_root=tmp_path)
    assert res.name == "docs_checks"
    assert res.passed is False
    assert res.detail != "docs checks pass"
    assert "doc finding(s)" not in res.detail
    assert res.detail == "docs tree missing or not a directory: docs"
    assert res.evidence.get("missing") is True
    assert res.evidence.get("path") == "docs"
    assert res.evidence.get("findings") == []


def test_explicit_injection_bypasses_filesystem(tmp_path: Path) -> None:
    """Arm (d): explicit injection bypasses filesystem checks for empty and non-empty sequences."""
    # tmp_path has no docs/ dir
    res_empty = rr.gate_docs_checks([], repo_root=tmp_path)
    assert res_empty.passed is True
    assert res_empty.detail == "docs checks pass"
    assert res_empty.evidence == {"findings": []}

    res_dirty = rr.gate_docs_checks(
        ["doc.md:1: [check] test finding"], repo_root=tmp_path
    )
    assert res_dirty.passed is False
    assert res_dirty.detail == "1 doc finding(s)"
    assert res_dirty.evidence["findings"] == ["doc.md:1: [check] test finding"]


def test_json_dumps_with_doc_finding_evidence(tmp_path: Path) -> None:
    """Arm (e): DocFinding dataclass is normalized to str so to_dict() is JSON serializable."""
    df = dc.DocFinding("docs/guide.md", 10, "no-unicode-dashes", "em dash found")
    gate = rr.gate_docs_checks([df], repo_root=tmp_path)
    assert gate.passed is False
    assert isinstance(gate.evidence["findings"][0], str)

    report = rr.build_report(
        suite_passed=True,
        doc_findings=[df],
        repo_root=tmp_path,
        run_subprocess_gates=False,
    )
    dumped = json.dumps(report.to_dict())
    assert isinstance(dumped, str)
    assert "no-unicode-dashes" in dumped


def test_end_to_end_contrast_pair(tmp_path: Path) -> None:
    """Arm (f): clean tree yields VERDICT_GO while dirty tree yields VERDICT_NO_GO on docs_checks."""
    docs_dir = _setup_go_fixture(tmp_path)

    # 1. Clean docs tree -> VERDICT_GO and failing_gates is empty
    report_clean = rr.build_report(
        suite_passed=True,
        repo_root=tmp_path,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        run_subprocess_gates=False,
    )
    assert report_clean.verdict == rr.VERDICT_GO
    assert report_clean.failing_gates() == []

    # 2. Dirty docs tree -> VERDICT_NO_GO and failing_gates has exactly docs_checks
    (docs_dir / "dirty.md").write_text(
        "Prose with an em \u2014 dash.\n", encoding="utf-8"
    )
    report_dirty = rr.build_report(
        suite_passed=True,
        repo_root=tmp_path,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        run_subprocess_gates=False,
    )
    assert report_dirty.verdict == rr.VERDICT_NO_GO
    assert report_dirty.failing_gates() == ["docs_checks"]


def test_checker_exception_handled_cleanly(tmp_path: Path) -> None:
    """Arm (g): checker exceptions fail closed cleanly without crashing build_report."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "corrupt.md").write_bytes(b"\xff\xfe\x00\x00invalid-utf8")

    gate = rr.gate_docs_checks(repo_root=tmp_path)
    assert gate.name == "docs_checks"
    assert gate.passed is False
    assert gate.detail == "docs check could not run: UnicodeDecodeError"
    assert gate.evidence.get("error") == "UnicodeDecodeError"
    assert gate.evidence.get("findings") == []

    report = rr.build_report(
        suite_passed=True,
        repo_root=tmp_path,
        residual_risk_signed=True,
        residual_risk_signer="qa",
        run_subprocess_gates=False,
    )
    assert isinstance(report, rr.ReleaseReadinessReport)
    assert "docs_checks" in report.failing_gates()
