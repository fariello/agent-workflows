"""Behavioral regression test for the read-only --source-citations detector.

IPD 68hdic (Set zftbta).
Guards:
- E-02: dead_filename_citations passes through suffixes so .py files can be inspected,
  with the discriminating negative proving failure if suffixes is dropped.
- E-08: Citations whose files exist on disk outside selectors.record_dirs are not flagged.
- E-03: The sentinel record_type="any" reaches citations across all record types.
- E-04: Test files (test_*.py, *_test.py) are excluded so test fixtures do not force exit=1.
- Exit code parity: exit 0 on clean tree, 1 on findings.
- No assertions are coupled to live repository record counts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_workflows import cli
from agent_workflows.artifact_refs import (
    check_source_citations,
    dead_filename_citations,
)


def _setup_fake_repo(tmp_path: Path) -> dict[str, Path]:
    plans_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)
    real_plan = plans_dir / "20260901-testset-01-a1b2c3-real-plan.ipd.md"
    real_plan.write_text("# Real Plan\n- Id: a1b2c3\n", encoding="utf-8")

    pkg_dir = tmp_path / "agent_workflows"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    resolving_py = pkg_dir / "resolving.py"
    resolving_py.write_text(
        "# cites 20260901-testset-01-a1b2c3-real-plan.ipd.md\n", encoding="utf-8"
    )

    dangling_py = pkg_dir / "dangling.py"
    dangling_py.write_text(
        "# cites 20260901-testset-02-d4e5f6-fake-plan.ipd.md\n", encoding="utf-8"
    )

    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    test_fixture_py = tools_dir / "test_dummy.py"
    test_fixture_py.write_text(
        "# cites 20260901-testset-03-x1y2z3-test-fixture.ipd.md\n", encoding="utf-8"
    )

    # File that exists on disk outside selectors.record_dirs
    runbook_dir = tools_dir / "ipdrunner"
    runbook_dir.mkdir(parents=True, exist_ok=True)
    runbook_file = runbook_dir / "20260823-pending-ipds-overnight-execution-runbook.md"
    runbook_file.write_text("# Runbook\n", encoding="utf-8")
    runbook_cite_py = pkg_dir / "runbook_cite.py"
    runbook_cite_py.write_text(
        'default_rb = "20260823-pending-ipds-overnight-execution-runbook.md"\n',
        encoding="utf-8",
    )

    return {
        "real_plan": real_plan,
        "resolving_py": resolving_py,
        "dangling_py": dangling_py,
        "test_fixture_py": test_fixture_py,
        "runbook_file": runbook_file,
        "runbook_cite_py": runbook_cite_py,
    }


def test_constructed_repo_source_scan(tmp_path: Path):
    """Scan constructed repository: reports planted dangler, excludes test fixtures and disk files."""
    paths = _setup_fake_repo(tmp_path)

    danglers, skipped_tests, scanned = check_source_citations(tmp_path)
    assert skipped_tests == 1
    assert len(danglers) == 1

    d = danglers[0]
    assert d.file == paths["dangling_py"]
    assert d.line == 1
    assert d.id6 == "20260901-testset-02-d4e5f6-fake-plan.ipd.md"


def test_discriminating_negative_for_suffixes_passthrough(tmp_path: Path):
    """Prove E-02: dead_filename_citations without .py suffix cannot see source files."""
    _setup_fake_repo(tmp_path)

    # When suffixes is restricted to default text suffixes (.md, .txt),
    # no .py source files are opened, returning 0 findings (the E-02 defect).
    results_text_only = dead_filename_citations(
        tmp_path,
        "any",
        scan_roots=("agent_workflows",),
        suffixes=(".md", ".txt"),
    )
    assert len(results_text_only) == 0

    # With suffixes=(".py",), the planted dangler in agent_workflows/dangling.py is found.
    results_py = dead_filename_citations(
        tmp_path,
        "any",
        scan_roots=("agent_workflows",),
        suffixes=(".py",),
    )
    assert len(results_py) == 1
    assert results_py[0].id6 == "20260901-testset-02-d4e5f6-fake-plan.ipd.md"


def test_cli_check_source_citations_exit_codes_and_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Test CLI exit codes (1 on findings, 0 on clean) and --agent JSONL output."""
    paths = _setup_fake_repo(tmp_path)

    # 1. Dirty tree: exit 1
    exit_code = cli.main(["check", "--source-citations", "--dir", str(tmp_path)])
    out, err = capsys.readouterr()
    assert exit_code == 1
    assert (
        "agent_workflows/dangling.py:1: 20260901-testset-02-d4e5f6-fake-plan.ipd.md"
        in out
    )
    assert "Skipped 1 test file(s) under scanned roots." in err

    # 2. Dirty tree with --agent: exit 1 and valid JSONL
    exit_code_agent = cli.main(
        ["check", "--source-citations", "--agent", "--dir", str(tmp_path)]
    )
    out_agent, _ = capsys.readouterr()
    assert exit_code_agent == 1
    record = json.loads(out_agent.strip())
    assert record["schema"] == "aw.agent/v1"
    assert record["cmd"] == "check"
    assert record["outcome"] == "findings"
    assert record["exit"] == 1
    assert record["findings"] == 1

    # 3. Clean tree: remove the dangling citation
    paths["dangling_py"].write_text(
        "# clean file with no citations\n", encoding="utf-8"
    )

    exit_code_clean = cli.main(["check", "--source-citations", "--dir", str(tmp_path)])
    out_clean, err_clean = capsys.readouterr()
    assert exit_code_clean == 0
    assert "agent_workflows/dangling.py" not in out_clean
    assert "Skipped 1 test file(s) under scanned roots." in err_clean

    # 4. Clean tree with --agent: exit 0 and valid JSONL
    exit_code_clean_agent = cli.main(
        ["check", "--source-citations", "--agent", "--dir", str(tmp_path)]
    )
    out_clean_agent, _ = capsys.readouterr()
    assert exit_code_clean_agent == 0
    record_clean = json.loads(out_clean_agent.strip())
    assert record_clean["schema"] == "aw.agent/v1"
    assert record_clean["cmd"] == "check"
    assert record_clean["outcome"] == "clean"
    assert record_clean["exit"] == 0
    assert record_clean["findings"] == 0
