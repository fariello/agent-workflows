from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from agent_workflows import cli, engine


def test_fresh_install_precommit_config_states_all_carrier_rule(tmp_path: Path) -> None:
    res = engine.create_backlog_close_gate_hook(tmp_path, use_git=False, install=True)
    assert res["created"] == [engine.PRE_COMMIT_CONFIG]
    pc_file = tmp_path / engine.PRE_COMMIT_CONFIG
    assert pc_file.exists()
    content = pc_file.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert data and "repos" in data
    hook_ids = [
        hook["id"] for repo in data.get("repos", []) for hook in repo.get("hooks", [])
    ]
    assert "backlog-blocking-close-gate" in hook_ids
    assert (
        "an EXECUTED From-Backlog" not in content
    ), "found singular wording: 'an EXECUTED From-Backlog'"
    assert re.search(
        r"HANDOFF[^)]*\bEVERY\b[^)]*From-Backlog", content, re.IGNORECASE
    ), "missing ALL-carrier rule (EVERY ... From-Backlog) in HANDOFF clause"


def test_append_install_precommit_config_states_all_carrier_rule(
    tmp_path: Path,
) -> None:
    existing_yaml = (
        "repos:\n"
        "  - repo: https://github.com/pre-commit/pre-commit-hooks\n"
        "    rev: v4.4.0\n"
        "    hooks:\n"
        "      - id: trailing-whitespace\n"
    )
    pc_file = tmp_path / engine.PRE_COMMIT_CONFIG
    pc_file.write_text(existing_yaml, encoding="utf-8")
    res = engine.create_backlog_close_gate_hook(tmp_path, use_git=False, install=True)
    assert any("appended" in n for n in res["notes"])
    content = pc_file.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    hook_ids = [
        hook["id"] for repo in data.get("repos", []) for hook in repo.get("hooks", [])
    ]
    assert "trailing-whitespace" in hook_ids
    assert "backlog-blocking-close-gate" in hook_ids
    assert (
        "an EXECUTED From-Backlog" not in content
    ), "found singular wording: 'an EXECUTED From-Backlog'"
    assert re.search(
        r"HANDOFF[^)]*\bEVERY\b[^)]*From-Backlog", content, re.IGNORECASE
    ), "missing ALL-carrier rule (EVERY ... From-Backlog) in HANDOFF clause"


def test_cli_help_description_states_all_carrier_rule(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("COLUMNS", "200")
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["backlog-blocking-close-gate", "--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    # Collapse runs of whitespace and hyphen-newlines per PR-002
    normalized = re.sub(r"-\s*\n\s*", "-", out)
    normalized = re.sub(r"\s+", " ", normalized)
    assert (
        "an EXECUTED From-Backlog" not in normalized
    ), "found singular wording: 'an EXECUTED From-Backlog'"
    assert re.search(
        r"HANDOFF:[^)]*\bEVERY\b[^)]*From-Backlog", normalized, re.IGNORECASE
    ), "missing ALL-carrier rule (EVERY ... From-Backlog) in HANDOFF clause"
