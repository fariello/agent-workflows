"""Behavioral gate asserting that every leaf declaring a shared common-parent machine flag honors it.

Motivated by xym8g8, where `aw sanitize --json` exited 0 with zero stdout bytes because
subcommand handlers can accept `--json` or `--fields` declared on the shared `common`
argparse parent yet silently fail to honor them in their handlers.

Universes are IMPORTED directly from `tests.test_agent_surface_conformance` (both `UNIVERSE`
and `MUTATION_UNIVERSE`), rather than recomputing or copying them. Reusing the exact same
candidate sets and registry subtractions ensures that this gate and the `--agent` sweep
remain synchronized and cannot drift apart.

Exemptions are governed by docs/cli-output-contract.md Section 1.3: verbatim-forwarding
host-driver leaves (`aw oc run`, `aw agy run`, review/integrate aliases, `aw run as`,
`aw run ipd`, `aw agy sessions|view|exec`) declare no `--json` or `--agent` flags because
downstream parsers own those flags. That exemption is derived from parser declaration
and pinned against the Section 1.3 contract list.

Broken leaves are registered in KNOWN_BROKEN with strict xfail, requiring a resolvable
backlog item for every entry.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pytest

from agent_workflows import cli
from agent_workflows.agent_schema import _PRESERVED_FIELDS
from tests.conformance_matrix import (
    RUNNABLE_ARGV,
    InstalledProjectTemplate,
    IsolatedProject,
    build_installed_project_template,
    clone_isolated_project,
    run_cli,
)
from tests.test_agent_surface_conformance import (
    MUTATION_UNIVERSE,
    UNIVERSE,
)

# --------------------------------------------------------------------------------------------------
# Known broken ceiling (E-04b)
# --------------------------------------------------------------------------------------------------
# A module-level dict mapping (leaf, flag) to a backlog id6.
# THE DICT IS A CEILING, NOT A CONVENIENCE. Adding an entry to silence a red case
# without a filed backlog item is prohibited. Every entry is strictly xfailed: if a leaf
# is fixed without removing its entry, the test turns red with XPASS.
KNOWN_BROKEN: Dict[Tuple[str, str], str] = {
    # --json unhonored on five leaves (jfdk7p):
    ("config get", "--json"): "jfdk7p",
    ("config is", "--json"): "jfdk7p",
    ("upgrade-test env", "--json"): "jfdk7p",
    ("upgrade-test probe", "--json"): "jfdk7p",
    ("upgrade-test clean", "--json"): "jfdk7p",
    # --fields unhonored on nine leaves (aws1tg):
    ("ipd coverage", "--fields"): "aws1tg",
    ("partition", "--fields"): "aws1tg",
    ("upgrade-test env", "--fields"): "aws1tg",
    ("upgrade-test list", "--fields"): "aws1tg",
    ("upgrade-test probe", "--fields"): "aws1tg",
    ("upgrade-test sandboxes", "--fields"): "aws1tg",
    ("oc update-models", "--fields"): "aws1tg",
    ("storage reattach", "--fields"): "aws1tg",
    ("upgrade-test clean", "--fields"): "aws1tg",
    # --fields unhonored on parser usage refusal on four leaves (4y614a):
    ("ipd scaffold", "--fields"): "4y614a",
    ("research new", "--fields"): "4y614a",
    ("research new-comparison", "--fields"): "4y614a",
    ("storage move", "--fields"): "4y614a",
}


# Note on sanctioned_raw: Leaves whose --agent output is registered as sanctioned_raw
# in EXEMPTION_REGISTRY (such as `aw path`) are already excluded from UNIVERSE during
# universe computation in test_agent_surface_conformance, so no extra skip is needed.


# --------------------------------------------------------------------------------------------------
# Section 1.3 exemption population (E-04a)
# --------------------------------------------------------------------------------------------------
# Pinned to the verbatim-forwarding host-driver commands documented in Section 1.3 plus __complete.
SECTION_1_3_EXEMPT_LEAVES: Dict[str, str] = {
    "run as": "Forwarded driver leaf: delegates argv to host runner parser; downstream owns flags.",
    "run ipd": "Forwarded driver leaf: delegates argv to host runner parser; downstream owns flags.",
    "oc runipd": "Forwarded driver leaf: delegates argv verbatim to OpenCode runner parser.",
    "oc review": "Forwarded driver leaf: canonical driver invocation forwarding to OpenCode runner.",
    "oc integrate": "Forwarded driver leaf: canonical driver invocation forwarding to OpenCode runner.",
    "agy runipd": "Forwarded driver leaf: delegates argv verbatim to Antigravity runner parser.",
    "agy review": "Forwarded driver leaf: canonical driver invocation forwarding to Antigravity runner.",
    "agy integrate": "Forwarded driver leaf: canonical driver invocation forwarding to Antigravity runner.",
    "agy sessions": "Forwarded driver leaf: delegates argv verbatim to agy_sessions parser.",
    "agy view": "Forwarded driver leaf: delegates argv verbatim to agy_view parser.",
    "agy exec": "Forwarded driver leaf: delegates argv verbatim to agy_run parser.",
    "__complete": "Internal shell completion hook: machine-only suppressed leaf.",
}


def _discover_leaf_parsers(
    parser: argparse.ArgumentParser, prefix: str = ""
) -> List[Tuple[str, argparse.ArgumentParser]]:
    """Recursively extract all canonical leaf (name, parser) pairs from an argparse parser tree.

    Deduplicates by parser object identity so aliases are not counted twice,
    following the identity rule documented in command_surface.discover_parser_leaves.
    """
    subparsers_actions = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    if not subparsers_actions:
        leaf = prefix.strip()
        return [(leaf, parser)] if leaf else []

    leaves: List[Tuple[str, argparse.ArgumentParser]] = []
    for sa in subparsers_actions:
        seen_parsers: List[Tuple[str, argparse.ArgumentParser]] = []
        for choice_name, subparser in sa.choices.items():
            if any(subparser is prior for _, prior in seen_parsers):
                continue
            seen_parsers.append((choice_name, subparser))
            full_name = f"{prefix} {choice_name}".strip()
            leaves.extend(_discover_leaf_parsers(subparser, full_name))
    return leaves


def _parser_option_strings(parser: argparse.ArgumentParser) -> Set[str]:
    opts: Set[str] = set()
    for action in parser._actions:
        opts.update(action.option_strings)
    return opts


# --------------------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def scoped_repo_dir(tmp_path_factory) -> Path:
    """A minimal initialized git repo with a minimal .aw folder.

    Used by expensive whole-tree inspection commands (doctor, check) so their
    conformance check verifies the emit contract without traversing this
    repository's full records tree.
    """
    temp_dir = tmp_path_factory.mktemp("scoped_aw_project")
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
    (temp_dir / ".aw" / "records" / "plans").mkdir(parents=True)
    return temp_dir


@pytest.fixture(scope="session")
def installed_template(tmp_path_factory) -> InstalledProjectTemplate:
    """Session-scoped installed-project template."""
    base = tmp_path_factory.mktemp("aw_installed_template")
    return build_installed_project_template(base)


@pytest.fixture
def isolated_mutation_project(
    tmp_path: Path, installed_template: InstalledProjectTemplate
) -> IsolatedProject:
    """Per-leaf isolated clone of the installed project template."""
    return clone_isolated_project(installed_template, tmp_path / "leaf_iso")


# --------------------------------------------------------------------------------------------------
# Parametrize parameter builders
# --------------------------------------------------------------------------------------------------


def _json_read_params() -> List[pytest.param]:
    params = []
    for leaf in UNIVERSE:
        reason = KNOWN_BROKEN.get((leaf, "--json"))
        if reason:
            params.append(
                pytest.param(
                    leaf, id=leaf, marks=pytest.mark.xfail(strict=True, reason=reason)
                )
            )
        else:
            params.append(pytest.param(leaf, id=leaf))
    return params


def _json_mutation_params() -> List[pytest.param]:
    params = []
    for leaf in MUTATION_UNIVERSE:
        reason = KNOWN_BROKEN.get((leaf, "--json"))
        if reason:
            params.append(
                pytest.param(
                    leaf, id=leaf, marks=pytest.mark.xfail(strict=True, reason=reason)
                )
            )
        else:
            params.append(pytest.param(leaf, id=leaf))
    return params


def _fields_read_params() -> List[pytest.param]:
    params = []
    for leaf in UNIVERSE:
        reason = KNOWN_BROKEN.get((leaf, "--fields"))
        if reason:
            params.append(
                pytest.param(
                    leaf, id=leaf, marks=pytest.mark.xfail(strict=True, reason=reason)
                )
            )
        else:
            params.append(pytest.param(leaf, id=leaf))
    return params


def _fields_mutation_params() -> List[pytest.param]:
    params = []
    for leaf in MUTATION_UNIVERSE:
        reason = KNOWN_BROKEN.get((leaf, "--fields"))
        if reason:
            params.append(
                pytest.param(
                    leaf, id=leaf, marks=pytest.mark.xfail(strict=True, reason=reason)
                )
            )
        else:
            params.append(pytest.param(leaf, id=leaf))
    return params


# --------------------------------------------------------------------------------------------------
# Assertion helpers
# --------------------------------------------------------------------------------------------------


def _assert_json_parseable(leaf: str, full_argv: List[str], res) -> None:
    try:
        json.loads(res.stdout)
    except Exception as exc:
        raise AssertionError(
            f"Leaf {leaf!r} failed to emit parseable JSON under --json!\n"
            f"Argv: {full_argv}\n"
            f"Exit code: {res.returncode}\n"
            f"Stdout prefix: {res.stdout[:300]!r}\n"
            f"Stderr prefix: {res.stderr[:300]!r}\n"
            f"Parse error: {exc}"
        ) from exc


def _assert_fields_honored(leaf: str, full_argv: List[str], res) -> None:
    terminal_recs = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            if isinstance(r, dict) and r.get("kind") in ("result", "summary", "error"):
                terminal_recs.append(r)
        except Exception:
            continue

    assert terminal_recs, (
        f"Leaf {leaf!r} emitted NO terminal record under --agent --fields cmd (vacuous pass guard)!\n"
        f"Argv: {full_argv}\n"
        f"Exit code: {res.returncode}\n"
        f"Stdout: {res.stdout[:300]!r}\n"
        f"Stderr: {res.stderr[:300]!r}"
    )

    allowed_keys = _PRESERVED_FIELDS | {"cmd"}
    for idx, r in enumerate(terminal_recs):
        unrequested = set(r.keys()) - allowed_keys
        assert not unrequested, (
            f"Leaf {leaf!r} terminal record #{idx} carries unrequested keys outside preserved envelope:\n"
            f"Unrequested keys: {sorted(unrequested)}\n"
            f"Record: {r}\n"
            f"Argv: {full_argv}\n"
            f"Exit code: {res.returncode}\n"
            f"Stderr: {res.stderr[:300]!r}"
        )


# --------------------------------------------------------------------------------------------------
# Tests: --json flag honored (E-02)
# --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("leaf", _json_read_params())
def test_json_flag_honored_read(leaf: str, scoped_repo_dir: Path) -> None:
    """Assert read/check leaf emits parseable JSON on stdout under --json."""
    extra_argv = RUNNABLE_ARGV.get(leaf, [])
    full_argv = leaf.split() + extra_argv + ["--json"]
    cwd: Optional[Path] = scoped_repo_dir if leaf in ("doctor", "check") else None
    res = run_cli(full_argv, cwd=cwd)
    _assert_json_parseable(leaf, full_argv, res)


@pytest.mark.parametrize("leaf", _json_mutation_params())
def test_json_flag_honored_mutation(
    leaf: str, isolated_mutation_project: IsolatedProject
) -> None:
    """Assert mutation leaf emits parseable JSON on stdout under --json."""
    iso = isolated_mutation_project
    extra_argv = RUNNABLE_ARGV.get(leaf, [])
    full_argv = leaf.split() + extra_argv + ["--json"]
    res = run_cli(
        full_argv,
        cwd=iso.project_dir,
        env_overrides=iso.env_overrides,
    )
    _assert_json_parseable(leaf, full_argv, res)


# --------------------------------------------------------------------------------------------------
# Tests: --fields flag honored (E-03)
# --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("leaf", _fields_read_params())
def test_fields_flag_honored_read(leaf: str, scoped_repo_dir: Path) -> None:
    """Assert read/check leaf honors --fields cmd under --agent."""
    extra_argv = RUNNABLE_ARGV.get(leaf, [])
    full_argv = leaf.split() + extra_argv + ["--agent", "--fields", "cmd"]
    cwd: Optional[Path] = scoped_repo_dir if leaf in ("doctor", "check") else None
    res = run_cli(full_argv, cwd=cwd)
    _assert_fields_honored(leaf, full_argv, res)


@pytest.mark.parametrize("leaf", _fields_mutation_params())
def test_fields_flag_honored_mutation(
    leaf: str, isolated_mutation_project: IsolatedProject
) -> None:
    """Assert mutation leaf honors --fields cmd under --agent."""
    iso = isolated_mutation_project
    extra_argv = RUNNABLE_ARGV.get(leaf, [])
    full_argv = leaf.split() + extra_argv + ["--agent", "--fields", "cmd"]
    res = run_cli(
        full_argv,
        cwd=iso.project_dir,
        env_overrides=iso.env_overrides,
    )
    _assert_fields_honored(leaf, full_argv, res)


# --------------------------------------------------------------------------------------------------
# Tests: Section 1.3 exemption pinned & KNOWN_BROKEN ceiling contract (E-04)
# --------------------------------------------------------------------------------------------------


def test_exemption_population_pinned() -> None:
    """The set of canonical leaves declaring no --json must equal Section 1.3 leaves plus __complete.

    Pinned against Section 1.3 so the exemption population cannot silently widen or drift.
    """
    parser = cli._build_parser()
    leaves = _discover_leaf_parsers(parser)
    no_json_leaves = {
        name for name, p in leaves if "--json" not in _parser_option_strings(p)
    }
    assert no_json_leaves == set(SECTION_1_3_EXEMPT_LEAVES.keys()), (
        f"Leaves without --json diverged from Section 1.3 exemption list:\n"
        f"Extra without --json: {no_json_leaves - set(SECTION_1_3_EXEMPT_LEAVES.keys())}\n"
        f"Missing (now declare --json): {set(SECTION_1_3_EXEMPT_LEAVES.keys()) - no_json_leaves}"
    )


def test_known_broken_citations_resolve() -> None:
    """Every citation in KNOWN_BROKEN must resolve to a valid backlog item via aw find backlog."""
    seen_citations = set(KNOWN_BROKEN.values())
    assert seen_citations, "KNOWN_BROKEN must not be empty while broken leaves exist"
    for cit in sorted(seen_citations):
        res = run_cli(["find", "backlog", cit])
        assert res.returncode == 0 and cit in res.stdout, (
            f"KNOWN_BROKEN citation {cit!r} failed to resolve via aw find backlog:\n"
            f"Exit: {res.returncode}\nStdout: {res.stdout}"
        )


def test_known_broken_no_dead_entries() -> None:
    """Every entry in KNOWN_BROKEN must name a leaf in UNIVERSE or MUTATION_UNIVERSE."""
    all_universe_leaves = set(UNIVERSE) | set(MUTATION_UNIVERSE)
    for leaf, flag in KNOWN_BROKEN:
        assert leaf in all_universe_leaves, (
            f"KNOWN_BROKEN entry for ({leaf!r}, {flag!r}) names a leaf not present in "
            f"UNIVERSE or MUTATION_UNIVERSE."
        )
        assert flag in (
            "--json",
            "--fields",
        ), f"KNOWN_BROKEN entry for ({leaf!r}, {flag!r}) has unknown flag {flag!r}."
