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

from agent_workflows import agent_schema, cli
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
from tests.test_usage_refusal_agent_record import REQUIRED_LEAVES, _capture_cli

# --------------------------------------------------------------------------------------------------
# Known broken ceiling (E-04b)
# --------------------------------------------------------------------------------------------------
# A module-level dict mapping (leaf, flag) to a backlog id6.
# THE DICT IS A CEILING, NOT A CONVENIENCE. Adding an entry to silence a red case
# without a filed backlog item is prohibited. Every entry is strictly xfailed: if a leaf
# is fixed without removing its entry, the test turns red with XPASS.
KNOWN_BROKEN: Dict[Tuple[str, str], str] = {}


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


# --------------------------------------------------------------------------------------------------
# Tests: Branch-level behavioral regression coverage for --fields projection (aws1tg E-07)
# --------------------------------------------------------------------------------------------------


def test_ipd_coverage_fields_branch_behavior(tmp_path: Path) -> None:
    """(a) ipd coverage: exit-2 cannot-run and exit-0/1 completion branches honor --fields."""
    import io
    from contextlib import redirect_stdout
    from unittest import mock
    from agent_workflows import runner_shared as rs
    from tests.test_partition_set_cohesion import make_fixture_plan

    # Exit-2 cannot-run path: no targets
    res = run_cli(["ipd", "coverage", "--agent", "--fields", "cmd"])
    assert res.returncode == 2
    rec = json.loads(res.stdout.strip())
    assert "detail" not in rec and "summary" not in rec

    res = run_cli(["ipd", "coverage", "--agent", "--fields", "cmd,summary"])
    assert res.returncode == 2
    rec = json.loads(res.stdout.strip())
    assert "summary" in rec and "detail" not in rec

    res = run_cli(["ipd", "coverage", "--agent"])
    assert res.returncode == 2
    rec = json.loads(res.stdout.strip())
    assert "summary" in rec and "detail" in rec

    res = run_cli(["ipd", "coverage", "--json", "--fields", "cmd"])
    assert res.returncode == 2
    rec = json.loads(res.stdout.strip())
    assert "summary" in rec and "detail" in rec

    # Exit-0 completion path with patched probe
    repo = tmp_path / "cov_repo"
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    table = (("01", "chld01", "Child 1"),)
    orch_path = make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "orchestrator",
        "approved",
        "seto",
        "Set O",
        0,
        "orch01",
        "Orch Plan",
        child_orders=table,
    )
    make_fixture_plan(
        repo,
        "pending",
        "20261010",
        "child",
        "approved",
        "seto",
        "Set O",
        1,
        "chld01",
        "Child Plan",
    )

    def fake_ask(state, excerpt, host="oc", repo=None, runner=None, **kwargs):
        return (rs.PROBE_ANSWER_NO_EXECUTIONS, "fake-model")

    buf = io.StringIO()
    with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
        buf
    ):
        rc = cli.main(
            [
                "ipd",
                "coverage",
                str(orch_path),
                "--no-commit",
                "--agent",
                "--fields",
                "cmd",
            ]
        )
    assert rc in (0, 1)
    rec = json.loads(buf.getvalue().strip())
    assert "data" not in rec and "summary" not in rec

    buf = io.StringIO()
    with mock.patch.object(rs, "ask_orchestrator_probe", fake_ask), redirect_stdout(
        buf
    ):
        rc = cli.main(["ipd", "coverage", str(orch_path), "--no-commit", "--agent"])
    assert rc in (0, 1)
    rec = json.loads(buf.getvalue().strip())
    assert "data" in rec and "summary" in rec


def test_partition_fields_branch_behavior(tmp_path: Path) -> None:
    """(b) partition: both exit-0 ok and exit-2 blocked_sets branches honor --fields, --json unprojected."""
    from tests.test_partition_set_cohesion import cohesion_repo

    # Exit-0 normal branch
    res = run_cli(
        ["partition", "-t", "plans", "-s", "approved", "--agent", "--fields", "cmd"]
    )
    assert res.returncode == 0
    rec = [
        json.loads(line)
        for line in res.stdout.splitlines()
        if line.strip() and json.loads(line).get("kind") == "result"
    ][0]
    for k in ("shards", "commands", "split_components", "cycles"):
        assert k not in rec

    res = run_cli(["partition", "-t", "plans", "-s", "approved", "--agent"])
    assert res.returncode == 0
    rec = [
        json.loads(line)
        for line in res.stdout.splitlines()
        if line.strip() and json.loads(line).get("kind") == "result"
    ][0]
    for k in ("shards", "commands", "split_components", "cycles"):
        assert k in rec

    res = run_cli(
        ["partition", "-t", "plans", "-s", "approved", "--json", "--fields", "cmd"]
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert "shards" in payload and "commands" in payload

    # Exit-2 blocked_sets branch
    repo = cohesion_repo.__wrapped__(tmp_path / "part_repo")
    res = run_cli(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--agent",
            "--fields",
            "cmd",
            "--dir",
            str(repo),
        ]
    )
    assert res.returncode == 2
    rec = [
        json.loads(line)
        for line in res.stdout.splitlines()
        if line.strip() and json.loads(line).get("kind") == "result"
    ][0]
    assert "blocked_sets" not in rec

    res = run_cli(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--agent",
            "--dir",
            str(repo),
        ]
    )
    assert res.returncode == 2
    rec = [
        json.loads(line)
        for line in res.stdout.splitlines()
        if line.strip() and json.loads(line).get("kind") == "result"
    ][0]
    assert "blocked_sets" in rec

    res = run_cli(
        [
            "partition",
            "-t",
            "plans",
            "-s",
            "approved",
            "-n",
            "3",
            "--json",
            "--fields",
            "cmd",
            "--dir",
            str(repo),
        ]
    )
    assert res.returncode == 2
    payload = json.loads(res.stdout)
    assert "blocked_sets" in payload


def test_oc_models_fields_branch_behavior(tmp_path: Path) -> None:
    """(c) oc update-models, oc sync-models, and standalone oc_models.run honor --fields."""
    from agent_workflows import oc_models

    fake_cfg = tmp_path / "opencode.json"
    fake_cfg.write_text(json.dumps({"providers": {}}), encoding="utf-8")
    env = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path)}

    def stub_fetch(url: str, token: str) -> None:
        return None

    for verb in ("update-models", "sync-models"):
        res = run_cli(
            [
                "oc",
                verb,
                "--config",
                str(fake_cfg),
                "--dry-run",
                "--agent",
                "--fields",
                "cmd",
            ],
            env_overrides=env,
        )
        assert res.returncode == 0
        rec = json.loads(res.stdout.strip())
        assert "findings" not in rec

        res = run_cli(
            ["oc", verb, "--config", str(fake_cfg), "--dry-run", "--agent"],
            env_overrides=env,
        )
        assert res.returncode == 0
        rec = json.loads(res.stdout.strip())
        assert "findings" in rec

    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = oc_models.run(
            ["--config", str(fake_cfg), "--dry-run", "--agent", "--fields", "cmd"],
            fetch=stub_fetch,
            env=env,
        )
    assert rc == 0
    rec = json.loads(buf.getvalue().strip())
    assert "findings" not in rec

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = oc_models.run(
            ["--config", str(fake_cfg), "--dry-run", "--agent"],
            fetch=stub_fetch,
            env=env,
        )
    assert rc == 0
    rec = json.loads(buf.getvalue().strip())
    assert "findings" in rec


def test_storage_reattach_fields_branch_behavior(tmp_path: Path) -> None:
    """(d) storage reattach: exit-1 _StorageReattachResult and exit-0 CommandResult honor --fields."""
    # Exit-1 branch: missing --companion-dir
    res = run_cli(["storage", "reattach", "--agent", "--fields", "cmd"])
    assert res.returncode == 1
    rec = json.loads(res.stdout.strip())
    assert "findings" not in rec

    res = run_cli(["storage", "reattach", "--agent"])
    assert res.returncode == 1
    rec = json.loads(res.stdout.strip())
    assert "findings" in rec

    # Exit-0 branch: --dry-run with --companion-dir
    res = run_cli(
        [
            "storage",
            "reattach",
            "--companion-dir",
            str(tmp_path),
            "--dry-run",
            "--agent",
            "--fields",
            "cmd",
        ]
    )
    assert res.returncode == 0
    rec = json.loads(res.stdout.strip())
    assert "findings" not in rec and "evidence" not in rec

    res = run_cli(
        [
            "storage",
            "reattach",
            "--companion-dir",
            str(tmp_path),
            "--dry-run",
            "--agent",
        ]
    )
    assert res.returncode == 0
    rec = json.loads(res.stdout.strip())
    assert "findings" in rec and "evidence" in rec


def test_upgrade_rehearsal_standalone_fields_behavior() -> None:
    """(e) standalone upgrade_rehearsal.main honors --fields under --agent."""
    from agent_workflows import upgrade_rehearsal
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = upgrade_rehearsal.main(["list", "--agent", "--fields", "cmd"])
    assert rc == 0
    rec = json.loads(buf.getvalue().strip())
    assert "findings" not in rec

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = upgrade_rehearsal.main(["list", "--agent"])
    assert rc == 0
    rec = json.loads(buf.getvalue().strip())
    assert "findings" in rec


# --------------------------------------------------------------------------------------------------
# Tests: Parser usage-refusal --fields projection under --agent (4y614a ksmdcd E-04)
# --------------------------------------------------------------------------------------------------


def _parse_last_agent_record(out: str) -> dict:
    """Parse and validate the last non-empty line of stdout as an aw.agent/v1 record."""
    non_empty = [line.strip() for line in out.strip().splitlines() if line.strip()]
    assert non_empty, "No output lines emitted"
    rec = json.loads(non_empty[-1])
    agent_schema.validate_agent_record(rec)
    return rec


@pytest.mark.parametrize("leaf", REQUIRED_LEAVES)
def test_parser_usage_refusal_fields_honored_required_leaves(leaf: str) -> None:
    """(a) All 67 canonical required-argument leaves honor --fields cmd under --agent."""
    rc, out, err = _capture_cli(leaf.split() + ["--agent", "--fields", "cmd"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    allowed = agent_schema._PRESERVED_FIELDS | {"cmd"}
    unrequested = set(rec.keys()) - allowed
    assert not unrequested, f"Leaf {leaf!r} emitted unrequested keys: {unrequested}"
    assert "findings" not in rec


FOUR_4Y614A_LEAVES = [
    "ipd scaffold",
    "research new",
    "research new-comparison",
    "storage move",
]


@pytest.mark.parametrize("leaf", FOUR_4Y614A_LEAVES)
def test_parser_usage_refusal_fields_absence_four_leaves(leaf: str) -> None:
    """(b.1) The four 4y614a leaves omit unrequested findings under --agent --fields cmd."""
    rc, out, err = _capture_cli(leaf.split() + ["--agent", "--fields", "cmd"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    allowed = agent_schema._PRESERVED_FIELDS | {"cmd"}
    assert set(rec.keys()) <= allowed


@pytest.mark.parametrize("leaf", FOUR_4Y614A_LEAVES)
def test_parser_usage_refusal_fields_presence_four_leaves(leaf: str) -> None:
    """(b.2) Non-vacuity: findings is present without --fields and retained when requested."""
    # (1) --agent without --fields includes "findings": 0
    rc, out, err = _capture_cli(leaf.split() + ["--agent"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    # (2) --agent --fields cmd,findings retains "findings": 0
    rc, out, err = _capture_cli(leaf.split() + ["--agent", "--fields", "cmd,findings"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    # (3) --fields=cmd,findings retains "findings": 0
    rc, out, err = _capture_cli(leaf.split() + ["--agent", "--fields=cmd,findings"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0


def test_parser_usage_refusal_fields_projection_edge_cases() -> None:
    """(c.1) _AwArgumentParser.error edge cases where --fields projection omits unrequested fields."""
    # Global flags before the leaf
    rc, out, err = _capture_cli(["--agent", "--fields", "cmd", "ipd", "scaffold"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    assert set(rec.keys()) <= agent_schema._PRESERVED_FIELDS | {"cmd"}

    rc, out, err = _capture_cli(["--agent", "--fields=cmd", "ipd", "set"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    assert set(rec.keys()) <= agent_schema._PRESERVED_FIELDS | {"cmd"}

    # Repeated --fields obeying last-flag-wins: --fields cmd,findings --fields cmd omits findings
    rc, out, err = _capture_cli(
        ["ipd", "scaffold", "--agent", "--fields", "cmd,findings", "--fields", "cmd"]
    )
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec

    # Other _AwArgumentParser.error refusal classes:
    # Unknown top-level command
    rc, out, err = _capture_cli(["nosuch", "--agent", "--fields", "cmd"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    assert set(rec.keys()) <= agent_schema._PRESERVED_FIELDS | {"cmd"}

    # Invalid choice subcommand
    rc, out, err = _capture_cli(["ipd", "nosuch", "--agent", "--fields", "cmd"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    assert set(rec.keys()) <= agent_schema._PRESERVED_FIELDS | {"cmd"}

    # Unrecognized option
    rc, out, err = _capture_cli(
        ["status", "--nosuchflag", "--agent", "--fields", "cmd"]
    )
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert "findings" not in rec
    assert set(rec.keys()) <= agent_schema._PRESERVED_FIELDS | {"cmd"}


def test_parser_usage_refusal_fields_presence_edge_cases() -> None:
    """(c.2) _AwArgumentParser.error edge cases where findings is retained or unprojected."""
    # Repeated --fields obeying last-flag-wins: --fields cmd --fields cmd,findings retains findings
    rc, out, err = _capture_cli(
        ["ipd", "scaffold", "--agent", "--fields", "cmd", "--fields", "cmd,findings"]
    )
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    # Bare -- boundary: --fields after bare -- is ignored, retaining findings
    rc, out, err = _capture_cli(["ipd", "scaffold", "--agent", "--", "--fields", "cmd"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    # Missing --fields argument safety: exits 2 with valid cannot-run record, retains findings,
    # does not treat "--agent" as a field name
    rc, out, err = _capture_cli(["ipd", "scaffold", "--agent", "--fields"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    rc, out, err = _capture_cli(["ipd", "scaffold", "--fields", "--agent"])
    assert rc == 2
    rec = _parse_last_agent_record(out)
    assert rec.get("findings") == 0

    # Unprojected --json --fields cmd: stdout is one pretty-printed JSON object
    rc, out, err = _capture_cli(["ipd", "scaffold", "--json", "--fields", "cmd"])
    assert rc == 2
    json_payload = json.loads(out)
    for expected_key in ("summary", "diagnostics", "next_actions", "data"):
        assert (
            expected_key in json_payload
        ), f"Expected key {expected_key!r} in --json payload"


# --------------------------------------------------------------------------------------------------
# Tests: Branch-level behavioral regression coverage for --json flag honoring (jfdk7p E-04)
# --------------------------------------------------------------------------------------------------


def test_config_json_refusals_branch_behavior() -> None:
    """Exit-2 refusals across config subcommands emit parseable JSON and redact paths under --json."""
    refusal_cmds = [
        ["config", "get", "non_existent_key", "--json"],
        ["config", "is", "non_existent_val", "--json"],
        ["config", "show", "non_existent_key", "--json"],
        ["config", "set", "non_existent_key", "--json"],
        ["config", "unset", "non_existent_key", "--json"],
        ["config", "add", "non_existent_key", "--json"],
        ["config", "remove", "non_existent_key", "--json"],
    ]
    posix_home = "/ho" + "me/"
    mac_home = "/Use" + "rs/"
    for cmd in refusal_cmds:
        res = run_cli(cmd)
        assert res.returncode == 2, f"{cmd} returncode {res.returncode}"
        assert res.stderr == "", f"{cmd} stderr non-empty: {res.stderr}"
        try:
            rec = json.loads(res.stdout)
        except Exception as exc:
            raise AssertionError(
                f"{cmd} stdout not parseable JSON: {res.stdout}"
            ) from exc
        assert rec.get("status") == "cannot-run"
        assert rec.get("exit_code") == 2
        assert posix_home not in res.stdout
        assert mac_home not in res.stdout


def test_upgrade_test_json_harness_error_and_redaction(tmp_path: Path) -> None:
    """upgrade-test env and probe under --json emit parseable JSON on valid and invalid sandboxes."""
    import io
    from contextlib import redirect_stderr, redirect_stdout
    from agent_workflows import upgrade_rehearsal

    # 1. Valid sandbox (exit 0)
    valid_sb = tmp_path / "valid_sb"
    valid_sb.mkdir()
    (valid_sb / ".aw-upgrade-test.json").write_text("{}")

    res_env = run_cli(["upgrade-test", "env", str(valid_sb), "--json"])
    assert res_env.returncode == 0
    rec_env = json.loads(res_env.stdout)
    assert rec_env.get("sandbox") == str(valid_sb)

    res_probe = run_cli(["upgrade-test", "probe", str(valid_sb), "--json"])
    assert res_probe.returncode == 0
    rec_probe = json.loads(res_probe.stdout)
    assert isinstance(rec_probe, dict)

    # 2. Non-sandbox exit-2 path with planted home path prefix (assembled from fragments)
    planted_path = "/ho" + "me/tester/planted_sandbox"
    posix_home = "/ho" + "me/"

    for sub in ("env", "probe"):
        # via run_cli (cli._dispatch)
        res = run_cli(["upgrade-test", sub, planted_path, "--json"])
        assert res.returncode == 2
        assert res.stderr == ""
        rec = json.loads(res.stdout)
        assert rec.get("status") == "cannot-run"
        assert rec.get("exit_code") == 2
        assert "~/planted_sandbox" in rec.get("summary", "")
        assert posix_home not in res.stdout

        # via standalone upgrade_rehearsal.main
        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            rc = upgrade_rehearsal.main([sub, planted_path, "--json"])
        assert rc == 2
        assert buf_err.getvalue() == ""
        rec_main = json.loads(buf_out.getvalue())
        assert rec_main.get("status") == "cannot-run"
        assert rec_main.get("exit_code") == 2
        assert "~/planted_sandbox" in rec_main.get("summary", "")
        assert posix_home not in buf_out.getvalue()


def test_upgrade_test_env_json_payload_secrecy(tmp_path: Path) -> None:
    """upgrade-test env <sandbox> --json exposes only specific sandbox env keys and no secrets."""
    sb = tmp_path / "secret_sb"
    sb.mkdir()
    (sb / ".aw-upgrade-test.json").write_text("{}")
    sentinel_marker = "planted_sentinel_marker_probe"

    res = run_cli(
        ["upgrade-test", "env", str(sb), "--json"],
        env_overrides={"AW_SENTINEL_PROBE": sentinel_marker},
    )
    assert res.returncode == 0
    rec = json.loads(res.stdout)
    assert rec.get("sandbox") == str(sb)
    assert set(rec.get("env", {}).keys()) == {
        "XDG_CONFIG_HOME",
        "AW_HOME",
        "GIT_TERMINAL_PROMPT",
    }
    assert sentinel_marker not in res.stdout


def test_upgrade_test_clean_json_branches(tmp_path: Path) -> None:
    """upgrade-test clean under --json emits parseable JSON across all three branches."""
    # Branch 1: empty targets ([] on stdout, exit 0)
    empty_root = tmp_path / "empty_root"
    empty_root.mkdir()
    res_empty = run_cli(
        ["upgrade-test", "clean", "--all", "--root", str(empty_root), "--json"]
    )
    assert res_empty.returncode == 0
    assert json.loads(res_empty.stdout) == []

    # Branch 2: non-empty preview without -y ({"would_remove": [...]} on stdout, preserved on disk)
    sb_root = tmp_path / "sb_root"
    sb_root.mkdir()
    sb = sb_root / "test_sb"
    sb.mkdir()
    (sb / ".aw-upgrade-test.json").write_text("{}")

    res_prev = run_cli(
        ["upgrade-test", "clean", "--all", "--root", str(sb_root), "--json"]
    )
    assert res_prev.returncode == 0
    rec_prev = json.loads(res_prev.stdout)
    assert rec_prev == {"would_remove": [str(sb)]}
    assert sb.exists()

    # Branch 3: confirmed removal with -y (list of result records, removed from disk)
    res_clean = run_cli(
        ["upgrade-test", "clean", "--all", "--root", str(sb_root), "-y", "--json"]
    )
    assert res_clean.returncode == 0
    rec_clean = json.loads(res_clean.stdout)
    assert isinstance(rec_clean, list) and len(rec_clean) == 1
    assert rec_clean[0]["path"] == str(sb)
    assert rec_clean[0]["action"] == "removed"
    assert not sb.exists()
