"""Outcome tests for setid length policy enforcement and date preservation across aw group and rename.

Covers setid length policy enforcement across all aw group backends: refusal (> 24 chars),
warning (15-24 chars), and quiet boundaries (<= 14 chars quiet; 24 chars warns without refusal)
for every artifact type in `artifact_types.TYPE_BACKENDS` that implements the `group` verb.
Iterates the backend registry dynamically so newly registered types are covered
automatically without editing test lists.

Also covers date preservation for `aw group plans` and `aw rename plans` when front-matter `- Date:`
is absent or malformed, restoring date regression coverage deleted in `19313eed` (IPD 949enf).
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import re
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


def _seed_plan_record(
    repo_dir: Path,
    filename: str,
    id6: str,
    *,
    set_line: str = "oldset (old set)",
    order: int = 3,
    date_line: str | None = None,
    disposition: str = "pending",
) -> Path:
    pdir = repo_dir / ".aw" / "records" / "plans" / disposition
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / filename
    lines = [
        f"# IPD: Test plan {id6}",
        "",
        f"- Id: {id6}",
        f"- Set: {set_line}",
        f"- Order: {order}",
    ]
    if date_line is not None:
        lines.append(f"- Date: {date_line}")
    lines.extend(["", "## Goal", "", "Test goal.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _run_group_plans(
    selectors: list[str],
    setid: str,
    repo_dir: Path,
    *,
    order: int | None = None,
    rename: bool = False,
    apply: bool = False,
) -> tuple[int, str, str]:
    """Run `aw group plans <selectors...> --set <setid> [--order <order>] [--rename] [--apply] --dir <repo_dir>` in-process."""
    cmd = ["group", "plans", *selectors, "--set", setid]
    if order is not None:
        cmd.extend(["--order", str(order)])
    if rename:
        cmd.append("--rename")
    if apply:
        cmd.append("--apply")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def _run_rename_plans(
    id6: str,
    repo_dir: Path,
    *,
    setid: str | None = None,
    order: int | None = None,
    slug: str | None = None,
    apply: bool = False,
) -> tuple[int, str, str]:
    """Run `aw rename plans --id <id6> [--set <setid>] [--order <order>] [--slug <slug>] [--apply] --dir <repo_dir>` in-process."""
    cmd = ["rename", "plans", "--id", id6]
    if setid is not None:
        cmd.extend(["--set", setid])
    if order is not None:
        cmd.extend(["--order", str(order)])
    if slug is not None:
        cmd.extend(["--slug", slug])
    if apply:
        cmd.append("--apply")
    cmd.extend(["--dir", str(repo_dir)])
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(cmd)
    return rc, buf_out.getvalue(), buf_err.getvalue()


def test_group_plans_absent_date_preserves_filename_date(temp_git_repo: Path):
    """E-01/V-01: aw group plans preserves the filename date when - Date: front matter is absent."""
    _seed_plan_record(
        temp_git_repo,
        "20260714-oldset-03-abc123-probe.ipd.md",
        "abc123",
        date_line=None,
    )
    rc, out, err = _run_group_plans(
        ["abc123"], "newset", temp_git_repo, rename=True, apply=True
    )
    assert rc == 0, f"Command failed: {out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    names = [f.name for f in files]
    assert len(names) == 1
    assert names[0].startswith(
        "20260714"
    ), f"Filename date was clobbered: {names[0]}; output: {out}"


def test_group_plans_malformed_date_preserves_filename_date(temp_git_repo: Path):
    """E-01/V-01: aw group plans preserves the filename date when - Date: front matter is malformed."""
    _seed_plan_record(
        temp_git_repo,
        "20260715-oldset-03-def456-probe.ipd.md",
        "def456",
        date_line="2026-07-23 (fleshed 2026-07-26 from research)",
    )
    rc, out, err = _run_group_plans(
        ["def456"], "newset", temp_git_repo, rename=True, apply=True
    )
    assert rc == 0, f"Command failed: {out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    names = [f.name for f in files]
    assert len(names) == 1
    assert names[0].startswith(
        "20260715"
    ), f"Filename date was clobbered: {names[0]}; output: {out}"


def test_group_plans_good_date_guard(temp_git_repo: Path):
    """E-01/V-01 guard: aw group plans preserves date when - Date: front matter is valid."""
    _seed_plan_record(
        temp_git_repo,
        "20260716-oldset-03-ghi789-probe.ipd.md",
        "ghi789",
        date_line="20260716",
    )
    rc, out, err = _run_group_plans(
        ["ghi789"], "newset", temp_git_repo, rename=True, apply=True
    )
    assert rc == 0, f"Command failed: {out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    names = [f.name for f in files]
    assert len(names) == 1
    assert names[0].startswith(
        "20260716"
    ), f"Filename date was altered: {names[0]}; output: {out}"


def test_rename_plans_legacy_name_preserves_date(temp_git_repo: Path):
    """E-02/V-02: aw rename plans preserves the date from a legacy-formatted filename (F-07)."""
    _seed_plan_record(
        temp_git_repo,
        "20260723-1100-07-clean-delta-design-spec.ipd.md",
        "qrokie",
        order=7,
        date_line="2026-07-23 (fleshed 2026-07-26 from research)",
    )
    rc, out, err = _run_rename_plans(
        "qrokie", temp_git_repo, setid="newset", apply=True
    )
    assert rc == 0, f"Command failed: {out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    names = [f.name for f in files]
    assert len(names) == 1
    assert names[0].startswith(
        "20260723"
    ), f"Legacy filename date was clobbered: {names[0]}; output: {out}"


def test_rename_plans_clustered_name_control(temp_git_repo: Path):
    """E-02/V-02 control: aw rename plans already preserves date for modern clustered filename."""
    _seed_plan_record(
        temp_git_repo,
        "20260723-oldset-07-qrokie-clean-delta-design-spec.ipd.md",
        "qrokie",
        order=7,
        date_line=None,
    )
    rc, out, err = _run_rename_plans(
        "qrokie", temp_git_repo, setid="newset", apply=True
    )
    assert rc == 0, f"Command failed: {out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    names = [f.name for f in files]
    assert len(names) == 1
    assert names[0].startswith(
        "20260723"
    ), f"Clustered filename date was clobbered: {names[0]}; output: {out}"


def test_group_plans_preview_matches_apply(temp_git_repo: Path):
    """E-04/V-04: Dry-run preview advertises the same preserved-date name that apply writes."""
    _seed_plan_record(
        temp_git_repo,
        "20260714-oldset-03-abc123-probe.ipd.md",
        "abc123",
        date_line=None,
    )
    # Dry run
    rc_dry, out_dry, err_dry = _run_group_plans(
        ["abc123"], "newset", temp_git_repo, rename=True, apply=False
    )
    assert rc_dry == 0, f"Dry run failed: {out_dry}\n{err_dry}"
    m = re.search(r"---\s+would rename\s+\S+\s+->\s+(\S+)\s+---", out_dry)
    assert m is not None, f"Preview rename line not found in output:\n{out_dry}"
    previewed_name = m.group(1)

    # Apply run
    rc_app, out_app, err_app = _run_group_plans(
        ["abc123"], "newset", temp_git_repo, rename=True, apply=True
    )
    assert rc_app == 0, f"Apply failed: {out_app}\n{err_app}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    applied_name = files[0].name

    assert previewed_name == applied_name
    assert applied_name.startswith(
        "20260714"
    ), f"Expected preserved date 20260714, got {applied_name}"


def test_group_plans_two_successive_regroups_self_perpetuation(temp_git_repo: Path):
    """E-05/V-05: Real date survives two successive regroups, preventing self-perpetuation of 20260101."""
    _seed_plan_record(
        temp_git_repo,
        "20260714-oldset-03-abc123-probe.ipd.md",
        "abc123",
        date_line=None,
    )
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"

    # Regroup 1: into set A
    rc1, out1, err1 = _run_group_plans(
        ["abc123"], "seta", temp_git_repo, rename=True, apply=True
    )
    assert rc1 == 0, f"Regroup 1 failed: {out1}\n{err1}"
    files1 = sorted(pdir.glob("*.md"))
    assert len(files1) == 1
    name1 = files1[0].name

    # Regroup 2: into set B
    rc2, out2, err2 = _run_group_plans(
        ["abc123"], "setb", temp_git_repo, rename=True, apply=True
    )
    assert rc2 == 0, f"Regroup 2 failed: {out2}\n{err2}"
    files2 = sorted(pdir.glob("*.md"))
    assert len(files2) == 1
    name2 = files2[0].name

    # Assert real date survived both regroups without self-perpetuating 20260101
    assert name1.startswith("20260714") and name2.startswith("20260714"), (
        f"Self-perpetuation observed: regroup 1 produced {name1}, "
        f"and regroup 2 preserved/produced {name2}"
    )
