"""Behavioral tests guarding release-readiness subprocess child pinning and stdin denial.

Guards the two shelling-out gates in release_readiness:
- gate_leak_scan
- gate_ipd_lint

No source-reading or code-structure tests (no ast, no inspect, no substring search).
Tests observe runtime behavior and outcomes only.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from agent_workflows import release_readiness


def test_gates_do_not_execute_decoy_package_in_caller_repo_root(tmp_path: Path) -> None:
    """A decoy agent_workflows package in caller repo_root must not be executed.

    Before pinning, Python seeds sys.path[0] from cwd, running the decoy and
    producing a false verdict. With the af7i6p pin in place, the runner's own
    package executes instead, so the decoy's exit code is never returned.
    """
    # Initialize a git repository in tmp_path so the real leak scanner does not
    # reject the directory before scanning (PR-002).
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    # Initialize a plans directory so ipd lint locates a plans tree rather than
    # refusing at exit 2 (gonzhl).
    (tmp_path / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)

    # Build synthetic decoy package in tmp_path.
    decoy_pkg = tmp_path / "agent_workflows"
    decoy_pkg.mkdir()
    (decoy_pkg / "__init__.py").write_text("# decoy package\n", encoding="utf-8")
    (decoy_pkg / "__main__.py").write_text(
        "import sys\nsys.exit(42)\n",
        encoding="utf-8",
    )

    # Test gate_leak_scan against the decoy tree.
    leak_result = release_readiness.gate_leak_scan(tmp_path)
    assert (
        leak_result.evidence.get("returncode") != 42
    ), "gate_leak_scan executed decoy package in repo_root (returncode=42)"
    assert leak_result.passed is True
    assert leak_result.evidence.get("returncode") == 0

    # Test gate_ipd_lint against the decoy tree.
    lint_result = release_readiness.gate_ipd_lint(tmp_path)
    assert (
        lint_result.evidence.get("returncode") != 42
    ), "gate_ipd_lint executed decoy package in repo_root (returncode=42)"
    assert lint_result.passed is True
    assert lint_result.evidence.get("returncode") == 0


def test_gate_subprocesses_deny_stdin_and_pin_env() -> None:
    """Both gates must pass stdin=subprocess.DEVNULL and env to subprocess.run.

    Also asserts that the trailing argv arguments match the documented commands:
    ['sanitize', '--agent'] and ['ipd', 'lint', '--all', '--agent'].
    """
    recorded_calls: list[tuple[list[str], dict]] = []

    def spy_run(argv, **kwargs):
        recorded_calls.append((list(argv), dict(kwargs)))
        return subprocess.CompletedProcess(argv, returncode=0, stdout="", stderr="")

    with patch.object(release_readiness.subprocess, "run", side_effect=spy_run):
        leak_res = release_readiness.gate_leak_scan()
        lint_res = release_readiness.gate_ipd_lint()

    assert len(recorded_calls) == 2, f"expected 2 calls, got {len(recorded_calls)}"

    leak_argv, leak_kwargs = recorded_calls[0]
    lint_argv, lint_kwargs = recorded_calls[1]

    # Verify stdin and env kwargs for both gate calls.
    for name, kwargs in [("leak_scan", leak_kwargs), ("ipd_lint", lint_kwargs)]:
        assert (
            "stdin" in kwargs
        ), f"stdin absent from {name} subprocess kwargs: {kwargs}"
        assert (
            kwargs["stdin"] is subprocess.DEVNULL
        ), f"stdin is not DEVNULL in {name}: {kwargs.get('stdin')}"
        assert "env" in kwargs, f"env absent from {name} subprocess kwargs: {kwargs}"
        assert kwargs["env"] is not None, f"env is None in {name} subprocess kwargs"

    # Verify trailing argv arguments remain unchanged.
    assert leak_argv[-2:] == [
        "sanitize",
        "--agent",
    ], f"unexpected leak_scan trailing argv: {leak_argv}"
    assert lint_argv[-4:] == [
        "ipd",
        "lint",
        "--all",
        "--agent",
    ], f"unexpected ipd_lint trailing argv: {lint_argv}"

    # Verify GateResults are constructed as expected.
    assert leak_res.passed is True
    assert leak_res.name == "leak_scan"
    assert lint_res.passed is True
    assert lint_res.name == "ipd_lint"
