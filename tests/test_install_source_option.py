"""Regression tests for --source as a string through the CLI (IPD rs03r2).

Verifies that passing --source as a string works end-to-end through the CLI parser,
that both install and setup subparsers parse --source as a pathlib.Path, and that
engine.resolve_source_root accepts either str or Path interchangeably.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from agent_workflows import cli, engine
from tests.support import REPO_ROOT, init_repo


def test_install_with_source_string_end_to_end(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drive --source as a string through cli.main into a real target repo without --dry-run."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("NO_COLOR", "1")

    target_repo = init_repo(tmp_path / "target")
    source_str = str(REPO_ROOT)

    # Note: minimum policy signal -y auto-supplies default preset. No --dry-run!
    code = cli.main(["install", "--source", source_str, str(target_repo), "-y"])
    assert code == 0

    installed_version = target_repo / ".aw" / "system" / "VERSION"
    installed_legacy = target_repo / ".agents" / "workflows" / "VERSION"
    assert installed_version.is_file() or installed_legacy.is_file()


def test_parsed_source_root_type_for_install_and_setup() -> None:
    """Verify both install and setup subparsers yield a Path for --source."""
    parser = cli._build_parser()

    args_install = parser.parse_args(["install", "--source", "/some/path", "target"])
    assert isinstance(args_install.source_root, Path)

    args_setup = parser.parse_args(["setup", "--source", "/some/path"])
    assert isinstance(args_setup.source_root, Path)


def test_resolve_source_root_str_path_parity() -> None:
    """Verify resolve_source_root returns the same Path when passed str vs Path."""
    source_str = str(REPO_ROOT)
    source_path = Path(source_str)

    resolved_from_str = engine.resolve_source_root(source_str)
    resolved_from_path = engine.resolve_source_root(source_path)

    assert isinstance(resolved_from_str, Path)
    assert isinstance(resolved_from_path, Path)
    assert resolved_from_str == resolved_from_path


def test_setup_diagnostics_probe(tmp_path: Path) -> None:
    """Verify setup-parsed namespace passes _diagnostics_ok without AttributeError."""
    target_repo = init_repo(tmp_path / "setup_target")
    parser = cli._build_parser()
    args = parser.parse_args(["setup", "--source", str(REPO_ROOT), "-y"])

    # Probe _diagnostics_ok directly to avoid running real aw setup side effects
    ok = cli._diagnostics_ok(target_repo, args)
    assert ok is True
