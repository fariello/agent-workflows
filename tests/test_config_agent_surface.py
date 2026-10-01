"""Default-collected integration test for aw config --agent surface.

Validates the machine-readable aw.agent/v1 contract across:
(a) All seven config verbs on their success path.
(b) Not-found paths at exit 1 for config remove and config is.
(c) Refusal paths at exit 2 with schema-valid kind: error records.
(d) Nested foreign home paths in whole-config payloads (config show).
(e) Non-nested foreign home paths in value and item fields.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from agent_workflows import agent_schema

# Note: FOREIGN_USER uses a real non-placeholder account name ('testforeignuser')
# so it is not in the validator allowlist (u, alice, user, USER, <...>) and
# tests foreign home-path sanitization actively.
FOREIGN_USER = "testforeignuser"


def _run_cli_agent(args: list[str], tmp_path: Path) -> tuple[int, dict[str, Any]]:
    """Drive agent_workflows CLI as a subprocess with isolated XDG_CONFIG_HOME.

    Asserts the four required properties:
    1. stdout is non-empty.
    2. Exactly one line parses as an aw.agent/v1 record.
    3. agent_schema.validate_agent_record returns [] (validator-clean).
    4. Record exit matches process returncode (exit parity).
    """
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(tmp_path)

    cmd = [sys.executable, "-m", "agent_workflows"] + args
    proc = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 1. stdout is NON-EMPTY
    assert (
        proc.stdout.strip()
    ), f"stdout was empty for command {cmd}; stderr: {proc.stderr.strip()}"

    # 2. Exactly one aw.agent/v1 record parses out of it
    lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected exactly 1 line, got {len(lines)}: {lines}"
    rec = json.loads(lines[0])

    # 3. agent_schema.validate_agent_record returns []
    errs = agent_schema.validate_agent_record(rec)
    assert errs == [], f"Validation errors on {cmd}: {errs}"

    # 4. Record exit equals subprocess exit code
    assert (
        rec.get("exit") == proc.returncode
    ), f"Exit mismatch on {cmd}: record exit {rec.get('exit')} != process returncode {proc.returncode}"

    return proc.returncode, rec


# ==============================================================================
# Case Class (a): All seven verbs on success path
# ==============================================================================


def test_config_show_whole_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "show", "--agent"], tmp_path)
    assert rc == 0
    assert rec["cmd"] == "config-show"
    assert rec["outcome"] == "clean"
    assert rec["verified"] is True
    assert rec["complete"] is True
    assert "config" in rec


def test_config_show_var_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "show", "defaults.backup", "--agent"], tmp_path)
    assert rc == 0
    assert rec["cmd"] == "config-show"
    assert rec["outcome"] == "clean"
    assert rec["key"] == "defaults.backup"
    assert "value" in rec


def test_config_get_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "get", "defaults.backup", "--agent"], tmp_path)
    assert rc == 0
    assert rec["cmd"] == "config-get"
    assert rec["outcome"] == "clean"
    assert rec["key"] == "defaults.backup"


def test_config_set_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "set", "defaults.backup", "false", "--agent"], tmp_path
    )
    assert rc == 0
    assert rec["cmd"] == "config-set"
    assert rec["outcome"] == "clean"
    assert rec["key"] == "defaults.backup"
    assert rec["value"] is False


def test_config_unset_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "unset", "defaults.backup", "--agent"], tmp_path
    )
    assert rc == 0
    assert rec["cmd"] == "config-unset"
    assert rec["outcome"] == "clean"
    assert rec["key"] == "defaults.backup"


def test_config_add_success_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "add", "/tmp/item_a", "to", "repos.exclude", "--agent"], tmp_path
    )
    assert rc == 0
    assert rec["cmd"] == "config-add"
    assert rec["outcome"] == "clean"
    assert rec["added"] is True


def test_config_remove_success_agent(tmp_path: Path) -> None:
    # First add item
    _run_cli_agent(
        ["config", "add", "/tmp/item_b", "to", "repos.exclude", "--agent"], tmp_path
    )
    # Then remove item (hit)
    rc, rec = _run_cli_agent(
        ["config", "remove", "/tmp/item_b", "from", "repos.exclude", "--agent"],
        tmp_path,
    )
    assert rc == 0
    assert rec["cmd"] == "config-remove"
    assert rec["outcome"] == "clean"
    assert rec["removed"] is True


def test_config_is_success_agent(tmp_path: Path) -> None:
    # First add item
    _run_cli_agent(
        ["config", "add", "/tmp/item_c", "to", "repos.exclude", "--agent"], tmp_path
    )
    # Then check presence (hit)
    rc, rec = _run_cli_agent(
        ["config", "is", "/tmp/item_c", "in", "repos.exclude", "--agent"], tmp_path
    )
    assert rc == 0
    assert rec["cmd"] == "config-is"
    assert rec["outcome"] == "clean"
    assert rec["present"] is True


# ==============================================================================
# Case Class (b): Not-found path (exit 1, valid outcome)
# ==============================================================================


def test_config_remove_not_found_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "remove", "/tmp/absent_item", "from", "repos.exclude", "--agent"],
        tmp_path,
    )
    assert rc == 1
    assert rec["cmd"] == "config-remove"
    assert rec["outcome"] == "findings"
    assert rec["removed"] is False


def test_config_is_not_found_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "is", "/tmp/absent_item", "in", "repos.exclude", "--agent"],
        tmp_path,
    )
    assert rc == 1
    assert rec["cmd"] == "config-is"
    assert rec["outcome"] == "findings"
    assert rec["present"] is False


# ==============================================================================
# Case Class (c): Refusal paths (exit 2, kind: error)
# ==============================================================================


def test_config_show_refusal_bad_key_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "show", "no.such.key", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert rec["verified"] is False
    assert rec["complete"] is False


def test_config_get_refusal_missing_var_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "get", "", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert rec["verified"] is False
    assert rec["complete"] is False


def test_config_get_refusal_bad_key_foreign_path_agent(tmp_path: Path) -> None:
    bad_key = f"/home/{FOREIGN_USER}/secret"
    rc, rec = _run_cli_agent(["config", "get", bad_key, "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert FOREIGN_USER not in json.dumps(rec)


def test_config_set_refusal_bad_key_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(
        ["config", "set", "no.such.key", "val", "--agent"], tmp_path
    )
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


def test_config_unset_refusal_missing_var_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "unset", "", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


def test_config_unset_refusal_bad_key_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "unset", "no.such.key", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


def test_config_add_refusal_syntax_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "add", "", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


def test_config_remove_refusal_syntax_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "remove", "", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


def test_config_is_refusal_syntax_agent(tmp_path: Path) -> None:
    rc, rec = _run_cli_agent(["config", "is", "", "--agent"], tmp_path)
    assert rc == 2
    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"


# ==============================================================================
# Case Class (d): Nested foreign home path in config (config show)
# ==============================================================================


def test_config_show_nested_foreign_home_path_agent(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "agent-workflows"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"
    foreign_path = f"/home/{FOREIGN_USER}/project"
    cfg_file.write_text(
        json.dumps(
            {
                "config_version": 2,
                "repos": {"search": [foreign_path]},
                "defaults": {"backup": True, "prune": True},
            }
        )
    )

    rc, rec = _run_cli_agent(["config", "show", "--agent"], tmp_path)
    assert rc == 0
    assert rec["cmd"] == "config-show"
    assert rec["outcome"] == "clean"
    # Ensure foreign path was reduced and validated without raising
    nested_search = rec["config"]["repos"]["search"]
    assert foreign_path not in nested_search
    assert any(FOREIGN_USER in s for s in nested_search)


# ==============================================================================
# Case Class (e): Non-nested foreign home path in value and item
# ==============================================================================


def test_config_get_foreign_home_path_in_value_agent(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "agent-workflows"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "config.json"
    foreign_path = f"/home/{FOREIGN_USER}/src"
    cfg_file.write_text(
        json.dumps(
            {
                "config_version": 2,
                "repos": {"search": [foreign_path]},
                "defaults": {"backup": True, "prune": True},
            }
        )
    )

    rc, rec = _run_cli_agent(["config", "get", "repos.search", "--agent"], tmp_path)
    assert rc == 0
    assert rec["cmd"] == "config-get"
    assert rec["outcome"] == "clean"
    val = rec["value"]
    assert foreign_path not in val
    assert any(FOREIGN_USER in s for s in val)


def test_config_is_foreign_home_path_in_item_agent(tmp_path: Path) -> None:
    foreign_arg = f"/home/{FOREIGN_USER}/x"
    rc, rec = _run_cli_agent(
        ["config", "is", foreign_arg, "in", "repos.exclude", "--agent"],
        tmp_path,
    )
    assert rc == 1
    assert rec["cmd"] == "config-is"
    assert rec["outcome"] == "findings"
    assert rec["present"] is False
    assert rec["item"] != foreign_arg
    assert FOREIGN_USER in rec["item"]
