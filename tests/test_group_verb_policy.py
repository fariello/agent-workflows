"""Outcome tests for setid length policy enforcement across all aw group backends.

Covers the refusal (> 24 chars), warning (15-24 chars), and quiet boundaries
(<= 14 chars quiet; 24 chars warns without refusal) for every artifact type
in `artifact_types.TYPE_BACKENDS` that implements the `group` verb.
Iterates the backend registry dynamically so newly registered types are covered
automatically without editing test lists.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess

import pytest

from agent_workflows import artifact_types, cli, config, research_contract as R


GROUP_TYPES = sorted(
    t for t, verbs in artifact_types.TYPE_BACKENDS.items() if "group" in verbs
)


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def _run_group(artifact_type: str, setid: str, repo_dir: Path) -> tuple[int, str, str]:
    """Run `aw group <type> zzzzzz --set <setid> --dir <repo_dir>` in-process with captured output."""
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(
            ["group", artifact_type, "zzzzzz", "--set", setid, "--dir", str(repo_dir)]
        )
    return rc, buf_out.getvalue(), buf_err.getvalue()


def test_group_verb_policy_sanity():
    """Sanity check: registry yields non-empty group types including plans and research,
    and policy length constants match the expected defaults (14 and 24).
    """
    assert len(GROUP_TYPES) > 0, "GROUP_TYPES must not be empty"
    assert "plans" in GROUP_TYPES, "plans backend must support group verb"
    assert "research" in GROUP_TYPES, "research backend must support group verb"
    assert config.SETID_WARN_LENGTH_DEFAULT == 14
    assert config.SETID_MAX_LENGTH_DEFAULT == 24


@pytest.mark.parametrize("artifact_type", GROUP_TYPES)
def test_group_setid_refusal(artifact_type: str, temp_git_repo: Path):
    """(a) REFUSAL: a setid of length SETID_MAX_LENGTH_DEFAULT + 1 (25 chars)
    exits 2 with the 'error:' prefix, names the length and maximum, and short-circuits
    before selector resolution (no unmatched selector error).
    """
    max_len = config.SETID_MAX_LENGTH_DEFAULT
    setid = "a" * (max_len + 1)
    rc, out, _ = _run_group(artifact_type, setid, temp_git_repo)

    assert rc == 2
    assert f"is {len(setid)} characters" in out
    assert f"{max_len}-character maximum" in out
    assert out.startswith("error:")
    # Short-circuits before selector lookup, so the unmatched-selector error is absent
    assert "zzzzzz" not in out


@pytest.mark.parametrize("artifact_type", GROUP_TYPES)
def test_group_setid_warning(artifact_type: str, temp_git_repo: Path):
    """(b) WARNING: a setid of length SETID_WARN_LENGTH_DEFAULT + 1 (15 chars)
    prints a warning with the 'note:' prefix, names the length and 'strongly preferred',
    and does NOT contain '{max_len}-character maximum'. The command exits 2 because
    the selector 'zzzzzz' matches nothing; the warning is emitted before resolution fails.
    """
    warn_len = config.SETID_WARN_LENGTH_DEFAULT
    max_len = config.SETID_MAX_LENGTH_DEFAULT
    setid = "a" * (warn_len + 1)
    rc, out, _ = _run_group(artifact_type, setid, temp_git_repo)

    # Command exits 2 because selector resolution fails after warning emission
    assert rc == 2
    assert "note:" in out
    assert f"is {len(setid)} characters" in out
    assert "strongly preferred" in out
    assert f"{max_len}-character maximum" not in out
    # Selector resolution failed after the warning
    assert "zzzzzz" in out


@pytest.mark.parametrize("artifact_type", GROUP_TYPES)
def test_group_setid_quiet_at_warn_limit(artifact_type: str, temp_git_repo: Path):
    """(c1) QUIET BOUNDARY 1: a setid of length SETID_WARN_LENGTH_DEFAULT (14 chars)
    emits neither 'note:' nor 'error:' from the length guard. Only the unmatched-selector
    error is emitted.
    """
    warn_len = config.SETID_WARN_LENGTH_DEFAULT
    max_len = config.SETID_MAX_LENGTH_DEFAULT
    setid = "a" * warn_len
    rc, out, _ = _run_group(artifact_type, setid, temp_git_repo)

    assert rc == 2
    assert "note:" not in out
    assert "characters" not in out
    assert "strongly preferred" not in out
    assert f"{max_len}-character maximum" not in out
    assert "zzzzzz" in out


@pytest.mark.parametrize("artifact_type", GROUP_TYPES)
def test_group_setid_warn_not_refused_at_max(artifact_type: str, temp_git_repo: Path):
    """(c2) QUIET BOUNDARY 2: a setid of length SETID_MAX_LENGTH_DEFAULT (24 chars)
    warns ('note:', names length) but is NOT refused (no '{max_len}-character maximum').
    """
    max_len = config.SETID_MAX_LENGTH_DEFAULT
    setid = "a" * max_len
    rc, out, _ = _run_group(artifact_type, setid, temp_git_repo)

    assert rc == 2
    assert "note:" in out
    assert f"is {len(setid)} characters" in out
    assert f"{max_len}-character maximum" not in out
    assert "zzzzzz" in out


def _seed_research_record(
    repo_dir: Path,
    date_str: str,
    set_id: str,
    order: str,
    id6: str,
    slug: str,
    kind: str = "notes",
    fm_order: str | None = None,
) -> Path:
    rdir = repo_dir / ".aw" / "records" / "research"
    rdir.mkdir(parents=True, exist_ok=True)
    filename = f"{date_str}-{set_id}-{order}-{id6}-{slug}.{kind}.md"
    path = rdir / filename
    actual_fm_order = fm_order if fm_order is not None else order
    path.write_text(
        f"---\n"
        f"id: {id6}\n"
        f"created: {date_str}\n"
        f"set: {set_id}\n"
        f"order: {actual_fm_order}\n"
        f"topic: []\n"
        f"model:\n"
        f"kind: {kind}\n"
        f"status: active\n"
        f"outcome: informational\n"
        f"summary: Test record {id6}.\n"
        f"consumed-by: []\n"
        f"---\n"
        f"# Test record {id6}\n",
        encoding="utf-8",
    )
    return path


def _run_group_research(
    selectors: list[str],
    setid: str,
    repo_dir: Path,
    *,
    order: int | None = None,
    apply: bool = False,
) -> tuple[int, str, str]:
    """Run `aw group research <selectors...> --set <setid> [--order <order>] [--apply] --dir <repo_dir>` in-process."""
    cmd = ["group", "research", *selectors, "--set", setid]
    if order is not None:
        cmd.extend(["--order", str(order)])
    if apply:
        cmd.append("--apply")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _run_research_setassign(
    selectors: list[str],
    setid: str,
    repo_dir: Path,
    *,
    order: int | None = None,
    apply: bool = False,
) -> tuple[int, str, str]:
    """Run `aw research set-assign <selectors...> --set <setid> [--order <order>] [--apply] --dir <repo_dir>` in-process."""
    cmd = ["research", "set-assign", *selectors, "--set", setid]
    if order is not None:
        cmd.extend(["--order", str(order)])
    if apply:
        cmd.append("--apply")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def test_group_research_bare_multi_preserves_order(temp_git_repo: Path):
    """E-01/V-01: Bare regroup over two records at Orders 03 and 07 preserves each Order."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "03", "aaaaaa", "first-doc"
    )
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "07", "bbbbbb", "second-doc"
    )

    rc, out, err = _run_group_research(
        ["aaaaaa", "bbbbbb"], "ns", temp_git_repo, apply=True
    )
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "03",
        "07",
    ], f"Observed orders {orders} from names {names}; output: {out}"


def test_group_research_bare_single_preserves_order(temp_git_repo: Path):
    """E-01/V-01: Bare regroup over a single record at Order 03 preserves its Order."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "03", "aaaaaa", "first-doc"
    )

    rc, out, err = _run_group_research(["aaaaaa"], "ns", temp_git_repo, apply=True)
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "03"
    ], f"Observed orders {orders} from names {names}; output: {out}"


def test_group_research_explicit_renumber(temp_git_repo: Path):
    """E-04/V-04 guard (a): Explicit --order 1 sequentially renumbers from 01."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "03", "aaaaaa", "first-doc"
    )
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "07", "bbbbbb", "second-doc"
    )

    rc, out, err = _run_group_research(
        ["aaaaaa", "bbbbbb"], "ns", temp_git_repo, order=1, apply=True
    )
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "01",
        "02",
    ], f"Observed orders {orders} from names {names}; output: {out}"


def test_group_research_explicit_order_zero(temp_git_repo: Path):
    """E-04/V-04 guard (b): Explicit --order 0 correctly targets 00."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "03", "aaaaaa", "first-doc"
    )

    rc, out, err = _run_group_research(
        ["aaaaaa"], "ns", temp_git_repo, order=0, apply=True
    )
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "00"
    ], f"Observed orders {orders} from names {names}; output: {out}"


def test_group_research_tier_disagreement_follows_filename(temp_git_repo: Path):
    """E-04/V-04 guard (c): Tier disagreement resolves from filename (00), not frontmatter (03)."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "00", "aaaaaa", "first-doc", fm_order="03"
    )

    rc, out, err = _run_group_research(["aaaaaa"], "ns", temp_git_repo, apply=True)
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "00"
    ], f"Observed orders {orders} from names {names}; output: {out}"


def test_research_setassign_spelling_preserves_order(temp_git_repo: Path):
    """E-04/V-04 guard (d): aw research set-assign spelling also preserves Order when bare."""
    _seed_research_record(
        temp_git_repo, "20260901", "oldset", "03", "aaaaaa", "first-doc"
    )

    rc, out, err = _run_research_setassign(["aaaaaa"], "ns", temp_git_repo, apply=True)
    assert rc == 0
    rdir = temp_git_repo / ".aw" / "records" / "research"
    files = sorted(rdir.glob("*.md"))
    names = [f.name for f in files]
    orders = [R.parse_name(n)[0].order for n in names]
    assert orders == [
        "03"
    ], f"Observed orders {orders} from names {names}; output: {out}"
