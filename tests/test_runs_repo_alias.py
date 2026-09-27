"""Tests for --repo alias of --dir on aw runs and aw run commands.

Plan 8y13kn / Backlog tqaxjw:
Accept --repo as an additive alias of --dir on `aw runs` (and `aw run` writing leaves
registered via the shared helper) so invocations compose with `aw oc run` continuation hints.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import pytest

from agent_workflows import cli
from agent_workflows import command_surface as cs


ARGV_SHAPES_REPO = [
    ["runs", "--repo", "/custom/repo"],
    ["runs", "run-x", "--repo", "/custom/repo"],
    ["runs", "list", "--repo", "/custom/repo"],
    ["runs", "show", "run-x", "--repo", "/custom/repo"],
    ["runs", "status", "run-x", "--repo", "/custom/repo"],
    ["runs", "analyze", "--repo", "/custom/repo"],
    ["runs", "query", "schema", "--repo", "/custom/repo"],
    ["runs", "export", "--repo", "/custom/repo"],
    ["runs", "submit", "--repo", "/custom/repo"],
    ["run", "start", "run-x", "--repo", "/custom/repo"],
]

ARGV_SHAPES_DIR = [
    ["runs", "--dir", "/custom/repo"],
    ["runs", "run-x", "--dir", "/custom/repo"],
    ["runs", "list", "--dir", "/custom/repo"],
    ["runs", "show", "run-x", "--dir", "/custom/repo"],
    ["runs", "status", "run-x", "--dir", "/custom/repo"],
    ["runs", "analyze", "--dir", "/custom/repo"],
    ["runs", "query", "schema", "--dir", "/custom/repo"],
    ["runs", "export", "--dir", "/custom/repo"],
    ["runs", "submit", "--dir", "/custom/repo"],
    ["run", "start", "run-x", "--dir", "/custom/repo"],
]


@pytest.mark.parametrize("argv", ARGV_SHAPES_REPO, ids=lambda a: " ".join(a[:3]))
def test_repo_alias_parses_to_dir_attr(argv: list[str]) -> None:
    parser = cli._build_parser()
    args = parser.parse_args(argv)
    assert getattr(args, "dir", None) == "/custom/repo"


@pytest.mark.parametrize("argv", ARGV_SHAPES_DIR, ids=lambda a: " ".join(a[:3]))
def test_dir_control_parses_to_dir_attr(argv: list[str]) -> None:
    parser = cli._build_parser()
    args = parser.parse_args(argv)
    assert getattr(args, "dir", None) == "/custom/repo"


def test_derived_coverage_every_dir_parser_accepts_repo() -> None:
    """Derive parser coverage: every runs/run parser accepting --dir must accept --repo."""
    parser = cli._build_parser()
    violations: list[str] = []

    def walk(
        p: argparse.ArgumentParser, prefix: str = "", seen: set[int] | None = None
    ) -> None:
        if seen is None:
            seen = set()
        if id(p) in seen:
            return
        seen.add(id(p))

        opts = {opt for a in p._actions for opt in a.option_strings}
        if prefix.startswith("runs") or prefix.startswith("run"):
            if "--dir" in opts and "--repo" not in opts:
                violations.append(f"{prefix} accepts --dir but missing --repo")

        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                seen_subs: set[int] = set()
                for name, sub in a.choices.items():
                    if id(sub) in seen_subs:
                        continue
                    seen_subs.add(id(sub))
                    sub_prefix = f"{prefix} {name}".strip() if prefix else name
                    walk(sub, sub_prefix, seen)

    walk(parser)
    assert not violations, f"Parsers accepting --dir without --repo: {violations}"


def test_end_to_end_runs_repo(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """End-to-end execution of `aw runs --repo <tmp>`."""
    runs_dir = tmp_path / ".aw" / "records" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    exit_code = cli.main(["runs", "--repo", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code != 2, f"Usage error (exit 2) encountered: {captured.err}"
    assert "unrecognized arguments" not in captured.err
    assert exit_code == 0
    assert "no matching runs found" in captured.out


def test_runs_list_declaration_both_directions() -> None:
    """Assert both directions of runs list declaration in command_surface."""
    decl = cs.get_declaration("runs list")
    assert decl is not None, "runs list declaration missing"
    assert "--repo" in decl.legacy_flags
    assert "--dir" in decl.legacy_flags

    # Check parser accepted flags
    parser = cli._build_parser()
    subparsers = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    runs_subparser = subparsers[0].choices["runs"]
    runs_sub = [
        a for a in runs_subparser._actions if isinstance(a, argparse._SubParsersAction)
    ][0]
    list_parser = runs_sub.choices["list"]
    accepted = {opt for act in list_parser._actions for opt in act.option_strings}

    assert set(decl.legacy_flags) - accepted == set()


def test_help_text_advertises_alias() -> None:
    """Confirm the help line displays `--dir, --repo DIR` for runs, a ledger leaf, and a separate leaf."""
    parser = cli._build_parser()
    subparsers = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    runs_parser = subparsers[0].choices["runs"]
    runs_sub = [
        a for a in runs_parser._actions if isinstance(a, argparse._SubParsersAction)
    ][0]
    show_parser = runs_sub.choices["show"]
    analyze_parser = runs_sub.choices["analyze"]

    def find_dir_repo_line(p: argparse.ArgumentParser) -> str:
        help_text = p.format_help()
        for line in help_text.splitlines():
            if "--dir" in line and "--repo" in line:
                return line.strip()
        return ""

    runs_line = find_dir_repo_line(runs_parser)
    show_line = find_dir_repo_line(show_parser)
    analyze_line = find_dir_repo_line(analyze_parser)

    assert runs_line.startswith(
        "--dir, --repo DIR"
    ), f"runs help rendered: {runs_line!r}"
    assert show_line.startswith(
        "--dir, --repo DIR"
    ), f"show help rendered: {show_line!r}"
    assert analyze_line.startswith(
        "--dir, --repo DIR"
    ), f"analyze help rendered: {analyze_line!r}"
