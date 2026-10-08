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
from pathlib import Path
import re
import subprocess
from contextlib import redirect_stderr, redirect_stdout

import pytest

from agent_workflows import artifact_types, cli, command_surface as cs, config, ipd_lint
from agent_workflows import research_contract as R


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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    names = [f.name for f in files if f.name != "INDEX.md"]
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
    kind: str | None = None,
    item_dependencies: str | None = None,
) -> Path:
    pdir = repo_dir / ".aw" / "records" / "plans" / disposition
    pdir.mkdir(parents=True, exist_ok=True)
    path = pdir / filename
    lines = [
        f"# IPD: Test plan {id6}",
        "",
        f"- Id: {id6}",
    ]
    if kind is not None:
        lines.append(f"- Kind: {kind}")
    lines.extend(
        [
            f"- Set: {set_line}",
            f"- Order: {order}",
        ]
    )
    if item_dependencies is not None:
        lines.append(f"- Item-Dependencies: {item_dependencies}")
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
    allow_invalid_order: bool = False,
) -> tuple[int, str, str]:
    """Run `aw group plans <selectors...> --set <setid> [--order <order>] [--rename] [--apply] [--allow-invalid-order] --dir <repo_dir>` in-process."""
    cmd = ["group", "plans", *selectors, "--set", setid]
    if order is not None:
        cmd.extend(["--order", str(order)])
    if rename:
        cmd.append("--rename")
    if apply:
        cmd.append("--apply")
    if allow_invalid_order:
        cmd.append("--allow-invalid-order")
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
    allow_invalid_order: bool = False,
) -> tuple[int, str, str]:
    """Run `aw rename plans --id <id6> [--set <setid>] [--order <order>] [--slug <slug>] [--apply] [--allow-invalid-order] --dir <repo_dir>` in-process."""
    cmd = ["rename", "plans", "--id", id6]
    if setid is not None:
        cmd.extend(["--set", setid])
    if order is not None:
        cmd.extend(["--order", str(order)])
    if slug is not None:
        cmd.extend(["--slug", slug])
    if apply:
        cmd.append("--apply")
    if allow_invalid_order:
        cmd.append("--allow-invalid-order")
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


def test_group_plans_refuses_child_at_order_zero(temp_git_repo: Path):
    """E-01/V-01 must-fail: aw group plans refuses a Kind: child at resolved Order 0 with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-probeset-01-chd001-probe-child-one.ipd.md",
        "chd001",
        kind="child",
        order=1,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["chd001"], "newset", temp_git_repo, order=0, rename=True, apply=True
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "child Order must be an integer >= 1" in combined
    assert "chd001" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists(), "Original file should still exist"
    assert seeded.read_text(encoding="utf-8") == original_text
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-probeset-01-chd001-probe-child-one.ipd.md"


def test_rename_plans_refuses_child_at_order_zero(temp_git_repo: Path):
    """E-01/V-01 must-fail: aw rename plans refuses a Kind: child at resolved Order 0 with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-probeset-02-chd002-probe-child-two.ipd.md",
        "chd002",
        kind="child",
        order=2,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_rename_plans("chd002", temp_git_repo, order=0, apply=True)
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "child Order must be an integer >= 1" in combined
    assert "chd002" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists(), "Original file should still exist"
    assert seeded.read_text(encoding="utf-8") == original_text
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-probeset-02-chd002-probe-child-two.ipd.md"


def test_group_plans_orchestrator_at_order_zero_permitted(temp_git_repo: Path):
    """E-01/V-01 guard: aw group plans permits an orchestrator at Order 0 unconditionally."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc001-probe-orch.ipd.md",
        "orc001",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["orc001"], "newset", temp_git_repo, order=0, rename=True, apply=True
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-newset-00-orc001-probe-orch.ipd.md"
    content = files[0].read_text(encoding="utf-8")
    assert "- Set: newset" in content
    assert "- Order: 0" in content
    assert "- Kind: orchestrator" in content


def test_group_plans_kindless_plan_at_order_zero_permitted(temp_git_repo: Path):
    """E-01/V-01 guard: aw group plans permits a plan without a - Kind: line at Order 0."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-01-knd001-probe-kindless.ipd.md",
        "knd001",
        kind=None,
        order=1,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["knd001"], "newset", temp_git_repo, order=0, rename=True, apply=True
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-newset-00-knd001-probe-kindless.ipd.md"
    content = files[0].read_text(encoding="utf-8")
    assert "- Set: newset" in content
    assert "- Order: 0" in content
    assert "- Kind:" not in content


def test_group_plans_multi_plan_order_zero_with_orchestrator_first(temp_git_repo: Path):
    """E-01/V-01 guard: multi-plan --order 0 with orchestrator named first yields 00/01/02."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-scatset-00-ggg777-orch.ipd.md",
        "ggg777",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    _seed_plan_record(
        temp_git_repo,
        "20260920-scatset-05-eee555-child-one.ipd.md",
        "eee555",
        kind="child",
        order=5,
        item_dependencies="none",
    )
    _seed_plan_record(
        temp_git_repo,
        "20260920-scatset-09-fff666-child-two.ipd.md",
        "fff666",
        kind="child",
        order=9,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["ggg777", "eee555", "fff666"],
        "asmset",
        temp_git_repo,
        order=0,
        rename=True,
        apply=True,
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 3
    assert files[0].name == "20260920-asmset-00-ggg777-orch.ipd.md"
    assert files[1].name == "20260920-asmset-01-eee555-child-one.ipd.md"
    assert files[2].name == "20260920-asmset-02-fff666-child-two.ipd.md"
    f0 = files[0].read_text(encoding="utf-8")
    f1 = files[1].read_text(encoding="utf-8")
    f2 = files[2].read_text(encoding="utf-8")
    assert "- Order: 0" in f0
    assert "- Order: 1" in f1
    assert "- Order: 2" in f2


def test_group_plans_bare_regroup_preserves_each_plan_order(temp_git_repo: Path):
    """E-01/V-01 guard: bare regroup (no --order) preserves each plan's existing Order on both branches."""
    # Branch 1: clustering rename (--rename)
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-04-iii888-child-four.ipd.md",
        "iii888",
        kind="child",
        order=4,
        item_dependencies="none",
    )
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-07-jjj999-child-seven.ipd.md",
        "jjj999",
        kind="child",
        order=7,
        item_dependencies="none",
    )
    rc1, out1, err1 = _run_group_plans(
        ["iii888", "jjj999"],
        "bareset",
        temp_git_repo,
        order=None,
        rename=True,
        apply=True,
    )
    assert rc1 == 0, f"Expected rc 0, got {rc1}. Output:\n{out1}\n{err1}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    f_888 = pdir / "20260920-bareset-04-iii888-child-four.ipd.md"
    f_999 = pdir / "20260920-bareset-07-jjj999-child-seven.ipd.md"
    assert f_888.exists()
    assert f_999.exists()
    assert "- Order: 4" in f_888.read_text(encoding="utf-8")
    assert "- Order: 7" in f_999.read_text(encoding="utf-8")

    # Branch 2: metadata-only (no --rename)
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-05-kkk000-child-five.ipd.md",
        "kkk000",
        kind="child",
        order=5,
        item_dependencies="none",
    )
    rc2, out2, err2 = _run_group_plans(
        ["kkk000"], "metaset", temp_git_repo, order=None, rename=False, apply=True
    )
    assert rc2 == 0, f"Expected rc 0, got {rc2}. Output:\n{out2}\n{err2}"
    f_000 = pdir / "20260920-oldset-05-kkk000-child-five.ipd.md"
    assert f_000.exists()
    content_000 = f_000.read_text(encoding="utf-8")
    assert "- Set: metaset" in content_000
    assert "- Order: 5" in content_000


def test_group_plans_metadata_only_refuses_child_at_order_zero(temp_git_repo: Path):
    """E-02/V-02: aw group plans metadata-only (no --rename) refuses Kind: child at Order 0 with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-03-ddd444-probe-child-meta.ipd.md",
        "ddd444",
        kind="child",
        order=3,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["ddd444"], "metaset", temp_git_repo, order=0, rename=False, apply=True
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "child Order must be an integer >= 1" in combined
    assert "ddd444" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_group_plans_preview_refuses_child_at_order_zero(temp_git_repo: Path):
    """E-02/V-02: aw group plans dry-run preview refuses Kind: child at Order 0 with exit 2 and prints no 'would rename' line."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-01-chd003-probe-preview.ipd.md",
        "chd003",
        kind="child",
        order=1,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["chd003"], "newset", temp_git_repo, order=0, rename=True, apply=False
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "child Order must be an integer >= 1" in combined
    assert "would rename" not in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_rename_plans_preview_refuses_child_at_order_zero(temp_git_repo: Path):
    """E-03/V-03: aw rename plans dry-run preview refuses Kind: child at Order 0 with exit 2 and prints no 'would rename' line."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-02-chd004-probe-prev-rename.ipd.md",
        "chd004",
        kind="child",
        order=2,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_rename_plans("chd004", temp_git_repo, order=0, apply=False)
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "child Order must be an integer >= 1" in combined
    assert "would rename" not in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_group_plans_allow_invalid_order_permits_write(temp_git_repo: Path):
    """E-04/V-04: aw group plans with --allow-invalid-order permits writing Order 0, prints note, and result lints IPD-M104."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-01-chd005-probe-override.ipd.md",
        "chd005",
        kind="child",
        order=1,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["chd005"],
        "newset",
        temp_git_repo,
        order=0,
        rename=True,
        apply=True,
        allow_invalid_order=True,
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "note:" in combined
    assert "chd005" in combined
    assert "child Order must be an integer >= 1" in combined

    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    written_file = files[0]
    assert written_file.name == "20260920-newset-00-chd005-probe-override.ipd.md"
    content = written_file.read_text(encoding="utf-8")
    assert "- Order: 0" in content

    # Assert IPD-M104 diagnostic is emitted on lint
    lint_res = ipd_lint.lint_file(written_file)
    m104 = [d for d in lint_res.diagnostics if d.code == "IPD-M104"]
    assert len(m104) > 0, f"Expected IPD-M104 diagnostic, got: {lint_res.diagnostics}"
    assert "child Order must be an integer >= 1" in m104[0].message


def test_rename_plans_allow_invalid_order_permits_write(temp_git_repo: Path):
    """E-04/V-04: aw rename plans with --allow-invalid-order permits writing Order 0 and prints note."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-02-chd006-probe-rename-override.ipd.md",
        "chd006",
        kind="child",
        order=2,
        item_dependencies="none",
    )
    rc, out, err = _run_rename_plans(
        "chd006", temp_git_repo, order=0, apply=True, allow_invalid_order=True
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "note:" in combined
    assert "chd006" in combined
    assert "child Order must be an integer >= 1" in combined

    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    written_file = files[0]
    assert written_file.name == "20260920-oldset-00-chd006-probe-rename-override.ipd.md"
    content = written_file.read_text(encoding="utf-8")
    assert "- Order: 0" in content


def test_group_and_rename_command_surface_declarations():
    """E-04/V-04: --allow-invalid-order is declared on rename and group only, and subset property passes."""
    p = cli._build_parser()
    sub = next(
        a.choices
        for a in p._actions
        if getattr(a, "choices", None) and "rename" in a.choices
    )

    # 1. Non-mutating read verbs do NOT accept --allow-invalid-order
    for read_verb in ("check", "find", "search", "index"):
        opts = {opt for act in sub[read_verb]._actions for opt in act.option_strings}
        assert (
            "--allow-invalid-order" not in opts
        ), f"Read verb {read_verb} must not accept --allow-invalid-order"

    # 2. Both mutating verbs accept --allow-invalid-order
    for mut_verb in ("rename", "group"):
        opts = {opt for act in sub[mut_verb]._actions for opt in act.option_strings}
        assert (
            "--allow-invalid-order" in opts
        ), f"Mutating verb {mut_verb} must accept --allow-invalid-order"

    # 3. Both CommandDeclarations declare --allow-invalid-order and declared-accepted subset is empty
    for v in ("rename", "group"):
        decl = cs.get_declaration(v)
        assert decl is not None
        assert "--allow-invalid-order" in decl.legacy_flags
        accepted = {opt for act in sub[v]._actions for opt in act.option_strings}
        diff = set(decl.legacy_flags) - accepted
        assert diff == set(), f"Undeclared or missing flags for {v}: {diff}"
        assert decl.exit_contract == (0, 2)


def test_group_plans_refuses_orchestrator_at_nonzero_order(temp_git_repo: Path):
    """E-01/V-01 must-fail: aw group plans refuses a Kind: orchestrator at resolved nonzero Order with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-probeset-00-orc001-probe-orch.ipd.md",
        "orc001",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["orc001"], "newset", temp_git_repo, order=5, rename=True, apply=True
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc001" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists(), "Original file should still exist"
    assert seeded.read_text(encoding="utf-8") == original_text
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-probeset-00-orc001-probe-orch.ipd.md"


def test_rename_plans_refuses_orchestrator_at_nonzero_order(temp_git_repo: Path):
    """E-01/V-01 must-fail: aw rename plans refuses a Kind: orchestrator at resolved nonzero Order with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-probeset-00-orc002-probe-orch-rename.ipd.md",
        "orc002",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_rename_plans("orc002", temp_git_repo, order=7, apply=True)
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc002" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists(), "Original file should still exist"
    assert seeded.read_text(encoding="utf-8") == original_text
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-probeset-00-orc002-probe-orch-rename.ipd.md"


def test_group_plans_kindless_plan_at_nonzero_order_permitted(temp_git_repo: Path):
    """E-01/V-01 guard (b): aw group plans permits a plan without a - Kind: line at a nonzero Order."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-01-knd002-probe-kindless-nonzero.ipd.md",
        "knd002",
        kind=None,
        order=1,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["knd002"], "newset", temp_git_repo, order=5, rename=True, apply=True
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    assert files[0].name == "20260920-newset-05-knd002-probe-kindless-nonzero.ipd.md"
    content = files[0].read_text(encoding="utf-8")
    assert "- Set: newset" in content
    assert "- Order: 5" in content
    assert "- Kind:" not in content


def test_group_plans_bare_regroup_preserves_orchestrator_order_zero(
    temp_git_repo: Path,
):
    """E-01/V-01 guard (d): bare regroup (no --order) preserves orchestrator Order 0 on both branches."""
    # Branch 1: clustering rename (--rename)
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc003-orch-bare.ipd.md",
        "orc003",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    rc1, out1, err1 = _run_group_plans(
        ["orc003"],
        "bareset",
        temp_git_repo,
        order=None,
        rename=True,
        apply=True,
    )
    assert rc1 == 0, f"Expected rc 0, got {rc1}. Output:\n{out1}\n{err1}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    f_003 = pdir / "20260920-bareset-00-orc003-orch-bare.ipd.md"
    assert f_003.exists()
    assert "- Order: 0" in f_003.read_text(encoding="utf-8")
    assert "- Kind: orchestrator" in f_003.read_text(encoding="utf-8")

    # Branch 2: metadata-only (no --rename)
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc004-orch-meta.ipd.md",
        "orc004",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    rc2, out2, err2 = _run_group_plans(
        ["orc004"], "metaset", temp_git_repo, order=None, rename=False, apply=True
    )
    assert rc2 == 0, f"Expected rc 0, got {rc2}. Output:\n{out2}\n{err2}"
    f_004 = pdir / "20260920-oldset-00-orc004-orch-meta.ipd.md"
    assert f_004.exists()
    content_004 = f_004.read_text(encoding="utf-8")
    assert "- Set: metaset" in content_004
    assert "- Order: 0" in content_004
    assert "- Kind: orchestrator" in content_004


def test_rename_plans_repair_direction_orchestrator_to_order_zero_permitted(
    temp_git_repo: Path,
):
    """E-01/V-01 guard (e): repairing an invalid orchestrator to Order 0 via aw rename plans is permitted."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-05-orc005-probe-repair.ipd.md",
        "orc005",
        kind="orchestrator",
        order=5,
        item_dependencies="none",
    )
    rc, out, err = _run_rename_plans("orc005", temp_git_repo, order=0, apply=True)
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    repaired_file = files[0]
    assert repaired_file.name == "20260920-oldset-00-orc005-probe-repair.ipd.md"
    content = repaired_file.read_text(encoding="utf-8")
    assert "- Order: 0" in content
    assert "- Kind: orchestrator" in content


def test_group_plans_multi_plan_positional_refuses_orchestrator_at_nonzero_order(
    temp_git_repo: Path,
):
    """E-01/V-01 positional: multi-plan resolves per plan; orchestrator at non-zero positional order is refused."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-01-chd010-child.ipd.md",
        "chd010",
        kind="child",
        order=1,
        item_dependencies="none",
    )
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc010-orch.ipd.md",
        "orc010",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    # Child resolves to 1 (valid); orchestrator resolves to 1+1=2 (invalid!)
    rc, out, err = _run_group_plans(
        ["chd010", "orc010"], "newset", temp_git_repo, order=1, rename=True, apply=True
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc010" in combined
    assert "--allow-invalid-order" in combined


def test_group_plans_metadata_only_refuses_orchestrator_at_nonzero_order(
    temp_git_repo: Path,
):
    """E-02/V-02: aw group plans metadata-only (no --rename) refuses Kind: orchestrator at nonzero Order with exit 2 and writes nothing."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc006-probe-orch-meta.ipd.md",
        "orc006",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["orc006"], "metaset", temp_git_repo, order=5, rename=False, apply=True
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc006" in combined
    assert "--allow-invalid-order" in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_group_plans_preview_refuses_orchestrator_at_nonzero_order(temp_git_repo: Path):
    """E-02/V-02: aw group plans dry-run preview refuses Kind: orchestrator at nonzero Order with exit 2 and prints no 'would rename' line."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc007-probe-preview.ipd.md",
        "orc007",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_group_plans(
        ["orc007"], "newset", temp_git_repo, order=5, rename=True, apply=False
    )
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc007" in combined
    assert "would rename" not in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_rename_plans_preview_refuses_orchestrator_at_nonzero_order(
    temp_git_repo: Path,
):
    """E-02/V-02: aw rename plans dry-run preview refuses Kind: orchestrator at nonzero Order with exit 2 and prints no 'would rename' line."""
    seeded = _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc008-probe-prev-rename.ipd.md",
        "orc008",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    original_text = seeded.read_text(encoding="utf-8")
    rc, out, err = _run_rename_plans("orc008", temp_git_repo, order=7, apply=False)
    assert rc == 2, f"Expected rc 2, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "orchestrator Order must be 0" in combined
    assert "orc008" in combined
    assert "would rename" not in combined
    assert seeded.exists()
    assert seeded.read_text(encoding="utf-8") == original_text


def test_group_plans_allow_invalid_order_permits_orchestrator_write(
    temp_git_repo: Path,
):
    """E-02/V-02: aw group plans with --allow-invalid-order permits writing nonzero Order to orchestrator, prints note, and result lints IPD-M104."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc009-probe-override.ipd.md",
        "orc009",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    rc, out, err = _run_group_plans(
        ["orc009"],
        "newset",
        temp_git_repo,
        order=5,
        rename=True,
        apply=True,
        allow_invalid_order=True,
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "note:" in combined
    assert "orc009" in combined
    assert "orchestrator Order must be 0" in combined

    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    written_file = files[0]
    assert written_file.name == "20260920-newset-05-orc009-probe-override.ipd.md"
    content = written_file.read_text(encoding="utf-8")
    assert "- Order: 5" in content

    # Assert IPD-M104 diagnostic is emitted on lint
    lint_res = ipd_lint.lint_file(written_file)
    m104 = [d for d in lint_res.diagnostics if d.code == "IPD-M104"]
    assert len(m104) > 0, f"Expected IPD-M104 diagnostic, got: {lint_res.diagnostics}"
    assert "orchestrator Order must be 0" in m104[0].message


def test_rename_plans_allow_invalid_order_permits_orchestrator_write(
    temp_git_repo: Path,
):
    """E-02/V-02: aw rename plans with --allow-invalid-order permits writing nonzero Order to orchestrator and prints note."""
    _seed_plan_record(
        temp_git_repo,
        "20260920-oldset-00-orc011-probe-rename-override.ipd.md",
        "orc011",
        kind="orchestrator",
        order=0,
        item_dependencies="none",
    )
    rc, out, err = _run_rename_plans(
        "orc011", temp_git_repo, order=7, apply=True, allow_invalid_order=True
    )
    assert rc == 0, f"Expected rc 0, got {rc}. Output:\n{out}\n{err}"
    combined = out + err
    assert "note:" in combined
    assert "orc011" in combined
    assert "orchestrator Order must be 0" in combined

    pdir = temp_git_repo / ".aw" / "records" / "plans" / "pending"
    files = sorted(pdir.glob("*.md"))
    assert len(files) == 1
    written_file = files[0]
    assert written_file.name == "20260920-oldset-07-orc011-probe-rename-override.ipd.md"
    content = written_file.read_text(encoding="utf-8")
    assert "- Order: 7" in content
