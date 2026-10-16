"""Behavioral sweep and edge-case verification for usage refusal records under --agent and --json.

awcliux 0z7ds3 E-05.
Asserts that usage refusals arising during argument parsing or early required-flag checks
emit an aw.agent/v1 cannot-run error record on stdout under --agent and a structured JSON
object under --json, without altering human stderr text or exit codes.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys

import pytest

from agent_workflows import agent_schema, cli


def _capture_cli(argv: list[str]) -> tuple[int, str, str]:
    """Execute cli.main in-process capturing stdout, stderr, and exit code."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code if code is not None else 0, out.getvalue(), err.getvalue()


def _discover_required_arg_leaves() -> list[str]:
    """Extract every canonical leaf parser that carries at least one required argument."""
    parser = cli._build_parser()
    leaf_map: dict[str, argparse.ArgumentParser] = {}

    def walk(p: argparse.ArgumentParser, prefix: str = "") -> None:
        subparsers_actions = [
            a for a in p._actions if isinstance(a, argparse._SubParsersAction)
        ]
        if not subparsers_actions:
            leaf = prefix.strip()
            if leaf:
                leaf_map[leaf] = p
            return
        for sa in subparsers_actions:
            seen: list[tuple[str, argparse.ArgumentParser]] = []
            for choice, subp in sa.choices.items():
                if any(subp is prior for _, prior in seen):
                    continue
                seen.append((choice, subp))
                walk(subp, f"{prefix} {choice}".strip())

    walk(parser)

    def has_required_arg(p: argparse.ArgumentParser) -> bool:
        for action in p._actions:
            if action.option_strings:
                if action.required:
                    return True
            else:
                if action.nargs not in ("?", "*", argparse.REMAINDER):
                    return True
        return False

    required = [name for name, p in leaf_map.items() if has_required_arg(p)]
    return sorted(required)


# Named, reasoned exclusion set for leaves whose handler-free refusal is impossible.
# Measured at 0 leaves for this surface: all 68 required-argument leaves refuse cleanly.
EXCLUDED_LEAVES: set[str] = set()

REQUIRED_LEAVES: list[str] = [
    leaf for leaf in _discover_required_arg_leaves() if leaf not in EXCLUDED_LEAVES
]


def test_exclusion_set_size_and_members() -> None:
    """Explicit visibility of the exclusion set size and members."""
    assert len(EXCLUDED_LEAVES) == 0
    assert len(REQUIRED_LEAVES) == 68


@pytest.mark.parametrize("leaf", REQUIRED_LEAVES)
def test_required_arg_leaf_agent_mode(leaf: str) -> None:
    """Case 1: Every required-arg leaf emits a valid cannot-run record under --agent."""
    rc, out, err = _capture_cli(leaf.split() + ["--agent"])
    assert rc == 2
    assert out.strip() != "", f"Empty stdout for leaf '{leaf}'"

    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])

    val_errs = agent_schema.validate_agent_record(rec)
    assert val_errs == [], f"Schema validation failed for leaf '{leaf}': {val_errs}"

    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == f"aw {leaf} --help"

    # Leak checks: no machine-identifying absolute paths
    assert "/home/" not in out, f"Unsanitized /home/ path in stdout: {out!r}"
    assert "/tmp/" not in out, f"Unsanitized /tmp/ path in stdout: {out!r}"


@pytest.mark.parametrize("leaf", REQUIRED_LEAVES)
def test_required_arg_leaf_json_mode(leaf: str) -> None:
    """Case 2: Every required-arg leaf emits a cannot-run JSON object under --json."""
    rc, out, err = _capture_cli(leaf.split() + ["--json"])
    assert rc == 2
    assert out.strip() != "", f"Empty stdout for leaf '{leaf}' under --json"

    data = json.loads(out)
    assert isinstance(data, dict)
    assert data["status"] == "cannot-run"
    assert data["exit_code"] == 2
    assert "next_actions" in data
    assert any(a.get("command") == f"aw {leaf} --help" for a in data["next_actions"])


def test_human_control_ipd_scaffold() -> None:
    """Case 3: Human invocation keeps stdout empty and preserves stderr diagnostic."""
    rc, out, err = _capture_cli(["ipd", "scaffold"])
    assert rc == 2
    assert out == ""
    assert "the following arguments are required:" in err
    assert "Next  aw ipd scaffold --help" in err


def test_conflicting_flags_ipd_scaffold() -> None:
    """Case 4: Combining --agent and --json emits no machine line on stdout."""
    rc, out, err = _capture_cli(["ipd", "scaffold", "--agent", "--json"])
    assert rc == 2
    assert out == ""


def test_flag_after_double_dash_forwarding() -> None:
    """Case 5: A token after bare -- on a forwarding command is not treated as mode."""
    rc, out, err = _capture_cli(["test", "--", "--agent"])
    assert "aw.agent/v1" not in out


def test_unknown_command_agent_mode() -> None:
    """Case 6: Top-level unknown command emits cmd: aw and next: aw --help."""
    rc, out, err = _capture_cli(["nosuch", "--agent"])
    assert rc == 2
    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "aw"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw --help"


@pytest.mark.parametrize(
    "leaf_tokens, leaf_name",
    [
        (["backlog", "new"], "backlog new"),
        (["specs", "new"], "specs new"),
        (["prompts", "new"], "prompts new"),
    ],
)
def test_e04_missing_required_handler_leaves(
    leaf_tokens: list[str], leaf_name: str
) -> None:
    """Case 7: Missing-required handler refusals emit a valid record and keep human stdout empty."""
    # Machine mode: --agent
    rc_agent, out_agent, err_agent = _capture_cli(leaf_tokens + ["--agent"])
    assert rc_agent == 2
    lines = [line for line in out_agent.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["kind"] == "error"
    assert rec["cmd"] == leaf_name
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == f"aw {leaf_name} --help"

    # Human mode: no flags
    rc_human, out_human, err_human = _capture_cli(leaf_tokens)
    assert rc_human == 2
    assert out_human == ""
    assert err_human.strip() != ""


def test_global_flag_position() -> None:
    """Case 8: Global flag before leaf is captured accurately across command structures."""
    for argv, expected_leaf in [
        (["--agent", "ipd", "scaffold"], "ipd scaffold"),
        (["--agent", "ipd", "set"], "ipd set"),
    ]:
        rc, out, err = _capture_cli(argv)
        assert rc == 2
        lines = [line for line in out.strip().splitlines() if line.strip()]
        rec = json.loads(lines[-1])
        assert agent_schema.validate_agent_record(rec) == []
        assert rec["kind"] == "error"
        assert rec["cmd"] == expected_leaf
        assert rec["outcome"] == "cannot-run"
        assert rec["exit"] == 2
        assert rec["next"] == f"aw {expected_leaf} --help"


def test_invalid_choice_on_family() -> None:
    """Case 9: Invalid choice on a subcommand family emits family cmd and next."""
    rc, out, err = _capture_cli(["ipd", "nosuch", "--agent"])
    assert rc == 2
    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "ipd"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw ipd --help"


def test_representative_subprocess() -> None:
    """Subprocess proof of the real console entry point."""
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "ipd", "scaffold", "--agent"],
        capture_output=True,
        timeout=15,
    )
    assert res.returncode == 2
    lines = [line for line in res.stdout.decode().strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "ipd scaffold"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw ipd scaffold --help"
