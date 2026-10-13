"""Agent surface conformance gate for CLI family roots (0qdl9e E-04).

Asserts that every CLI parser node carrying an argparse._SubParsersAction (family root)
emits a valid aw.agent/v1 record under --agent, exit code matches the record exit,
and adheres to the family root outcome shape (exit 0 default view, or exit 2 cannot-run error).

Exemptions are maintained in tests/conformance_matrix.py (FAMILY_ROOT_EXEMPTION_REGISTRY)
and must cite live backlog items and remain broken until fixed by the owning plan.
"""

from __future__ import annotations

import argparse
import json
from typing import Tuple

import pytest

from agent_workflows import cli
from agent_workflows.agent_schema import validate_agent_record
from agent_workflows.command_surface import (
    discover_parser_leaves,
    discover_parser_roots,
)
from tests.conformance_matrix import (
    FAMILY_ROOT_EXEMPTION_REGISTRY,
    run_cli,
)

_PARSER = cli._build_parser()
ROOTS = sorted(discover_parser_roots(_PARSER))
NON_EXEMPT_ROOTS = [r for r in ROOTS if r not in FAMILY_ROOT_EXEMPTION_REGISTRY]


def _evaluate_root(root: str) -> Tuple[bool, str]:
    """Execute ``aw <root> --agent`` and evaluate against agent conformance criteria.

    Returns (is_conforming, diagnostic_message).
    """
    argv = root.split() + ["--agent"]
    res = run_cli(argv)

    if not res.stdout.strip():
        return (
            False,
            f"stdout is empty for {root!r}. Returncode: {res.returncode}, Stderr: {res.stderr!r}",
        )

    last_rec = None
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if isinstance(data, dict) and data.get("kind") in (
                "result",
                "summary",
                "error",
            ):
                last_rec = data
        except Exception:
            pass

    if last_rec is None:
        return (
            False,
            f"No terminal result/summary/error record found for {root!r}.\n"
            f"Returncode: {res.returncode}\n"
            f"Stdout:\n{res.stdout}\n"
            f"Stderr:\n{res.stderr}",
        )

    val_errs = validate_agent_record(last_rec)
    if val_errs:
        return (
            False,
            f"validate_agent_record failed for {root!r}: {val_errs}\n"
            f"Record: {last_rec}\n"
            f"Stdout:\n{res.stdout}",
        )

    if last_rec.get("exit") != res.returncode:
        return (
            False,
            f"Exit code mismatch for {root!r}: rec['exit']={last_rec.get('exit')} != proc exit={res.returncode}\n"
            f"Record: {last_rec}\n"
            f"Stdout:\n{res.stdout}",
        )

    if "next" not in last_rec:
        return (
            False,
            f"'next' key missing from record for {root!r}\n"
            f"Record: {last_rec}\n"
            f"Stdout:\n{res.stdout}",
        )

    if res.returncode == 0:
        if last_rec.get("outcome") in ("cannot-run", "error"):
            return (
                False,
                f"Exit 0 record for {root!r} has unexpected failure outcome: {last_rec.get('outcome')!r}\n"
                f"Record: {last_rec}\n"
                f"Stdout:\n{res.stdout}",
            )
    else:
        if last_rec.get("kind") != "error":
            return (
                False,
                f"Non-zero exit record for {root!r} must have kind='error', got {last_rec.get('kind')!r}\n"
                f"Record: {last_rec}\n"
                f"Stdout:\n{res.stdout}",
            )
        if last_rec.get("outcome") != "cannot-run":
            return (
                False,
                f"Non-zero exit record for {root!r} must have outcome='cannot-run', got {last_rec.get('outcome')!r}\n"
                f"Record: {last_rec}\n"
                f"Stdout:\n{res.stdout}",
            )
        if res.returncode != 2:
            return (
                False,
                f"Expected returncode 2 for {root!r}, got {res.returncode}\n"
                f"Record: {last_rec}\n"
                f"Stdout:\n{res.stdout}",
            )
        if not last_rec.get("next"):
            return (
                False,
                f"Non-zero exit record for {root!r} requires non-empty 'next', got {last_rec.get('next')!r}\n"
                f"Record: {last_rec}\n"
                f"Stdout:\n{res.stdout}",
            )

    return True, ""


def test_family_root_census() -> None:
    """Assert ROOTS is non-empty, disjoint from leaves, and includes all exemption keys."""
    assert len(ROOTS) > 0, "ROOTS must be non-empty"
    leaves = discover_parser_leaves(_PARSER)
    overlap = set(ROOTS) & leaves
    assert not overlap, f"Roots and leaves must be disjoint; found overlap: {overlap}"
    for exempt_root in FAMILY_ROOT_EXEMPTION_REGISTRY:
        assert (
            exempt_root in ROOTS
        ), f"Exempted root {exempt_root!r} is not in discovered parser roots"


def test_discover_parser_roots_synthetic() -> None:
    """Assert discover_parser_roots behavior on a synthetic argparse tree.

    Excludes aliases, reports nested roots with full paths, and excludes leaves.
    """
    parser = argparse.ArgumentParser(prog="dummy")
    subparsers = parser.add_subparsers(dest="sub")

    # One root with an alias
    grp_parser = subparsers.add_parser("grp", aliases=["g"])
    grp_sub = grp_parser.add_subparsers(dest="grp_sub")

    # One nested root under grp
    nested_parser = grp_sub.add_parser("nested")
    nested_sub = nested_parser.add_subparsers(dest="nested_sub")
    nested_sub.add_parser("leaf1")

    # One leaf directly under top-level parser
    subparsers.add_parser("leaf0")

    # One leaf directly under grp
    grp_sub.add_parser("leaf2")

    roots = discover_parser_roots(parser)
    assert "grp" in roots
    assert "grp nested" in roots
    assert "g" not in roots
    assert "leaf0" not in roots
    assert "grp leaf2" not in roots
    assert "grp nested leaf1" not in roots
    assert roots == {"grp", "grp nested"}


@pytest.mark.parametrize("root", NON_EXEMPT_ROOTS)
def test_family_root_agent_conformance(root: str) -> None:
    """Assert non-exempt family root satisfies --agent output and schema contract."""
    conforming, diagnostic = _evaluate_root(root)
    assert conforming, diagnostic


def test_family_root_exemption_registry_contract() -> None:
    """Assert FAMILY_ROOT_EXEMPTION_REGISTRY entries have known_broken kind and cite live items."""
    valid_dirs = ("/backlog/open/", "/backlog/graduated/", "/backlog/blocked/")
    for root, entry in FAMILY_ROOT_EXEMPTION_REGISTRY.items():
        assert (
            entry.reason_kind == "known_broken"
        ), f"Entry for {root!r} must have reason_kind='known_broken', got {entry.reason_kind!r}"
        assert entry.citation.strip(), f"Entry for {root!r} has empty citation"
        assert entry.reason.strip(), f"Entry for {root!r} has empty reason"

        res = run_cli(["find", "backlog", entry.citation.strip()])
        assert res.returncode == 0, (
            f"Citation {entry.citation!r} for {root!r} failed to resolve via 'aw find backlog':\n"
            f"Exit: {res.returncode}\nStderr: {res.stderr}\nStdout: {res.stdout}"
        )
        assert any(d in res.stdout for d in valid_dirs), (
            f"Citation {entry.citation!r} for {root!r} is not a LIVE backlog item (must be in open, graduated, or blocked). "
            f"If it has moved to done or parked, delete this entry from FAMILY_ROOT_EXEMPTION_REGISTRY.\n"
            f"aw find backlog output:\n{res.stdout}"
        )


@pytest.mark.parametrize("root", sorted(FAMILY_ROOT_EXEMPTION_REGISTRY.keys()))
def test_exempted_family_root_still_nonconforming(root: str) -> None:
    """Assert exempted family roots are still non-conforming (self-pruning gate)."""
    entry = FAMILY_ROOT_EXEMPTION_REGISTRY[root]
    conforming, diagnostic = _evaluate_root(root)
    assert not conforming, (
        f"Exempted family root {root!r} now conforms! The executor of cited backlog item "
        f"{entry.citation} must delete this entry from FAMILY_ROOT_EXEMPTION_REGISTRY in tests/conformance_matrix.py."
    )
