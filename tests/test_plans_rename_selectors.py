"""Tests for plans rename and group selector resolution (IPD 87m438).

Pins that `aw rename plans <sel>` and `aw group plans <sel>` accept the same universal
selector vocabulary as other types (filename, stem, path, id6), that the declared id6 is
preserved in the resulting filename (corruption trap), and that must-not-break guarantees hold.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess

import pytest

from agent_workflows import artifact_naming, cli


@pytest.fixture
def repo_with_plans(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )

    plans_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
    plans_dir.mkdir(parents=True, exist_ok=True)

    # Clustered plan fixture
    p_clustered = plans_dir / "20260929-mytest-01-ab12cd-my-plan.ipd.md"
    p_clustered.write_text(
        "# IPD: My Plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: ab12cd\n"
        "- Set: mytest\n"
        "- Order: 1\n",
        encoding="utf-8",
    )

    # Legacy plan fixture
    p_legacy = plans_dir / "20260808-0004-06-migrate-existing-plans.ipd.md"
    p_legacy.write_text(
        "# IPD: Migrate Existing Plans\n\n"
        "- Date: 2026-08-08\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: 7qx7ys\n"
        "- Set: plans-adopter (plans adopter)\n"
        "- Order: 6\n",
        encoding="utf-8",
    )

    # Standalone (set-less) plan fixture for E-02
    p_standalone = plans_dir / "20260929-st99zz-01-st99zz-standalone-plan.ipd.md"
    p_standalone.write_text(
        "# IPD: Standalone Plan\n\n"
        "- Date: 2026-09-29\n"
        "- Kind: child\n"
        "- Status: pending\n"
        "- Id: st99zz\n"
        "- Order: 1\n",
        encoding="utf-8",
    )

    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init plans"], cwd=tmp_path, check=True)

    files = {
        "clustered": p_clustered,
        "legacy": p_legacy,
        "standalone": p_standalone,
    }
    return tmp_path, files


def run_aw(repo: Path, *args: str) -> tuple[int, str]:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        rc = cli.main(["--no-interactive", *args, "--dir", str(repo)])
    return rc, buf_out.getvalue() + buf_err.getvalue()


# --------------------------------------------------------------------------------------
# E-01: Pin the refusal of filename, stem, and path, plus id6 control
# --------------------------------------------------------------------------------------


def test_rename_plans_by_filename(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = files["clustered"].name
    rc, out = run_aw(repo, "rename", "plans", sel, "--slug", "new-slug")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_rename_plans_by_stem(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = (
        files["clustered"].name[:-3]
        if files["clustered"].name.endswith(".md")
        else files["clustered"].name
    )
    rc, out = run_aw(repo, "rename", "plans", sel, "--slug", "new-slug")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_rename_plans_by_path(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = files["clustered"].relative_to(repo).as_posix()
    rc, out = run_aw(repo, "rename", "plans", sel, "--slug", "new-slug")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_group_plans_by_filename(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = files["clustered"].name
    rc, out = run_aw(repo, "group", "plans", sel, "--set", "newgroup")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_group_plans_by_stem(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = (
        files["clustered"].name[:-3]
        if files["clustered"].name.endswith(".md")
        else files["clustered"].name
    )
    rc, out = run_aw(repo, "group", "plans", sel, "--set", "newgroup")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_group_plans_by_path(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    sel = files["clustered"].relative_to(repo).as_posix()
    rc, out = run_aw(repo, "group", "plans", sel, "--set", "newgroup")
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    assert f"no plan has Id '{sel}'" not in out


def test_rename_and_group_by_id6_control(repo_with_plans: tuple[Path, dict[str, Path]]):
    repo, files = repo_with_plans
    # Clustered control
    rc_ren, out_ren = run_aw(repo, "rename", "plans", "ab12cd", "--slug", "new-slug")
    assert rc_ren == 0, f"Expected rc=0, got rc={rc_ren}. Output:\n{out_ren}"
    assert "would rename" in out_ren

    rc_grp, out_grp = run_aw(repo, "group", "plans", "ab12cd", "--set", "newgroup")
    assert rc_grp == 0, f"Expected rc=0, got rc={rc_grp}. Output:\n{out_grp}"
    assert "would set Set=newgroup" in out_grp

    # Legacy control
    rc_leg, out_leg = run_aw(repo, "rename", "plans", "7qx7ys", "--slug", "new-slug")
    assert rc_leg == 0, f"Expected rc=0, got rc={rc_leg}. Output:\n{out_leg}"
    assert "would rename" in out_leg


# --------------------------------------------------------------------------------------
# E-02: Pin the filename-corruption trap before writing the fix
# --------------------------------------------------------------------------------------


def test_corruption_pin_id6_preserved_on_filename_rename(
    repo_with_plans: tuple[Path, dict[str, Path]],
):
    repo, files = repo_with_plans
    # Rename clustered fixture by filename with --apply
    src_clustered = files["clustered"]
    rc, out = run_aw(
        repo,
        "rename",
        "plans",
        src_clustered.name,
        "--slug",
        "renamed-clustered",
        "--apply",
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    renamed_files = list(src_clustered.parent.glob("*renamed-clustered*"))
    assert len(renamed_files) == 1, f"Expected 1 renamed file, found: {renamed_files}"
    renamed = renamed_files[0]
    parsed = artifact_naming.parse_clustered(renamed.name)
    assert (
        parsed is not None
    ), f"Renamed file {renamed.name} does not match clustered grammar!"
    assert (
        parsed.group("id6") == "ab12cd"
    ), f"Corrupted id6! Expected 'ab12cd', got '{parsed.group('id6')}' in {renamed.name}"
    assert parsed.group("set") == "mytest"
    assert parsed.group("slug") == "renamed-clustered"

    # Rename legacy fixture by filename with --apply
    src_legacy = files["legacy"]
    rc_leg, out_leg = run_aw(
        repo, "rename", "plans", src_legacy.name, "--slug", "renamed-legacy", "--apply"
    )
    assert rc_leg == 0, f"Expected rc=0, got rc={rc_leg}. Output:\n{out_leg}"
    renamed_leg_files = list(src_legacy.parent.glob("*renamed-legacy*"))
    assert (
        len(renamed_leg_files) == 1
    ), f"Expected 1 renamed file, found: {renamed_leg_files}"
    renamed_leg = renamed_leg_files[0]
    parsed_leg = artifact_naming.parse_clustered(renamed_leg.name)
    assert (
        parsed_leg is not None
    ), f"Renamed file {renamed_leg.name} does not match clustered grammar!"
    assert (
        parsed_leg.group("id6") == "7qx7ys"
    ), f"Corrupted id6! Expected '7qx7ys', got '{parsed_leg.group('id6')}' in {renamed_leg.name}"
    assert parsed_leg.group("set") == "plans-adopter"


def test_corruption_pin_setless_plan_uses_declared_id6_as_setid(
    repo_with_plans: tuple[Path, dict[str, Path]],
):
    repo, files = repo_with_plans
    src_standalone = files["standalone"]
    rc, out = run_aw(
        repo,
        "rename",
        "plans",
        src_standalone.name,
        "--slug",
        "renamed-standalone",
        "--apply",
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    renamed_files = list(src_standalone.parent.glob("*renamed-standalone*"))
    assert len(renamed_files) == 1, f"Expected 1 renamed file, found: {renamed_files}"
    renamed = renamed_files[0]
    parsed = artifact_naming.parse_clustered(renamed.name)
    assert (
        parsed is not None
    ), f"Renamed file {renamed.name} does not match clustered grammar!"
    assert (
        parsed.group("id6") == "st99zz"
    ), f"Corrupted id6! Expected 'st99zz', got '{parsed.group('id6')}' in {renamed.name}"
    assert (
        parsed.group("set") == "st99zz"
    ), f"Corrupted setid! Expected 'st99zz', got '{parsed.group('set')}' in {renamed.name}"


# --------------------------------------------------------------------------------------
# E-06: Must-not-break guards
# --------------------------------------------------------------------------------------


def test_guard_order_preservation_e3hzyc(repo_with_plans: tuple[Path, dict[str, Path]]):
    """(a) e3hzyc: a bare `aw group plans <sel> --set X` with no --order preserves each plan's own Order,
    and with --rename keeps its NN slot.
    """
    repo, files = repo_with_plans
    src_legacy = files["legacy"]  # has - Order: 6 and - Set: plans-adopter
    rc, out = run_aw(
        repo,
        "group",
        "plans",
        src_legacy.name,
        "--set",
        "newgrp",
        "--rename",
        "--apply",
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    renamed_files = list(src_legacy.parent.glob("*newgrp*"))
    assert len(renamed_files) == 1, f"Expected 1 renamed file, got: {renamed_files}"
    renamed = renamed_files[0]
    parsed = artifact_naming.parse_clustered(renamed.name)
    assert parsed is not None
    assert (
        parsed.group("nn") == "06"
    ), f"Expected NN slot '06' preserved, got '{parsed.group('nn')}' in {renamed.name}"
    assert parsed.group("set") == "newgrp"
    assert parsed.group("id6") == "7qx7ys"
    text = renamed.read_text(encoding="utf-8")
    assert "- Order: 6" in text
    assert "- Set: newgrp" in text


def test_guard_no_clobber_order_and_date_vf03z3(
    repo_with_plans: tuple[Path, dict[str, Path]],
):
    """(b) vf03z3: a bare `aw rename plans <filename>` does not clobber - Order: to 0 and does not recompute date."""
    repo, files = repo_with_plans
    src_legacy = files["legacy"]  # date 20260808, order 6
    rc, out = run_aw(
        repo, "rename", "plans", src_legacy.name, "--slug", "noclobber-slug", "--apply"
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    renamed_files = list(src_legacy.parent.glob("*noclobber-slug*"))
    assert len(renamed_files) == 1, f"Expected 1 renamed file, got: {renamed_files}"
    renamed = renamed_files[0]
    parsed = artifact_naming.parse_clustered(renamed.name)
    assert parsed is not None
    assert (
        parsed.group("date") == "20260808"
    ), f"Date was recomputed! Expected '20260808', got '{parsed.group('date')}'"
    assert (
        parsed.group("nn") == "06"
    ), f"Order was clobbered to 0! Expected '06', got '{parsed.group('nn')}'"
    assert parsed.group("id6") == "7qx7ys"
    text = renamed.read_text(encoding="utf-8")
    assert "- Order: 6" in text


def test_guard_slug_derivation_5rzupk(repo_with_plans: tuple[Path, dict[str, Path]]):
    """(c) 5rzupk: a rename --order with no --slug changes only the Order facet and does not inject
    the <setid>-NN- cluster prefix into the slug.
    """
    repo, files = repo_with_plans
    src_clustered = files["clustered"]  # 20260929-mytest-01-ab12cd-my-plan.ipd.md
    rc, out = run_aw(
        repo, "rename", "plans", src_clustered.name, "--order", "2", "--apply"
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"
    renamed_files = list(src_clustered.parent.glob("*my-plan*"))
    assert len(renamed_files) == 1, f"Expected 1 file, got: {renamed_files}"
    renamed = renamed_files[0]
    parsed = artifact_naming.parse_clustered(renamed.name)
    assert parsed is not None
    assert (
        parsed.group("nn") == "02"
    ), f"Expected NN slot '02', got '{parsed.group('nn')}' in {renamed.name}"
    assert (
        parsed.group("slug") == "my-plan"
    ), f"Slug was corrupted by cluster prefix! Got: '{parsed.group('slug')}'"
    assert parsed.group("set") == "mytest"
    assert parsed.group("id6") == "ab12cd"


def test_guard_setid_expansion_ordering(repo_with_plans: tuple[Path, dict[str, Path]]):
    """(d) OQ-04: an expanded setid selector in group flattens in resolved sorted-path order,
    so sequential --order renumbers deterministically.
    """
    repo, _ = repo_with_plans
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    p1 = plans_dir / "20260929-expdemo-02-aa1111-plan-a.ipd.md"
    p1.write_text(
        "# IPD: Plan A\n\n- Date: 2026-09-29\n- Kind: child\n- Status: pending\n- Id: aa1111\n- Set: expdemo\n- Order: 2\n",
        encoding="utf-8",
    )
    p2 = plans_dir / "20260929-expdemo-01-bb2222-plan-b.ipd.md"
    p2.write_text(
        "# IPD: Plan B\n\n- Date: 2026-09-29\n- Kind: child\n- Status: pending\n- Id: bb2222\n- Set: expdemo\n- Order: 1\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add expdemo plans"], cwd=repo, check=True)

    rc, out = run_aw(
        repo,
        "group",
        "plans",
        "expdemo",
        "--set",
        "targetgrp",
        "--order",
        "10",
        "--rename",
        "--apply",
    )
    assert rc == 0, f"Expected rc=0, got rc={rc}. Output:\n{out}"

    # Sorted path order: p2 ("...-01-bb2222...") comes before p1 ("...-02-aa1111...")
    renamed_a = list(plans_dir.glob("*targetgrp*aa1111*"))
    renamed_b = list(plans_dir.glob("*targetgrp*bb2222*"))
    assert len(renamed_a) == 1 and len(renamed_b) == 1
    parsed_a = artifact_naming.parse_clustered(renamed_a[0].name)
    parsed_b = artifact_naming.parse_clustered(renamed_b[0].name)
    assert parsed_a is not None and parsed_b is not None
    assert (
        parsed_b.group("nn") == "10"
    ), f"Expected order 10 for first sorted path (bb2222), got '{parsed_b.group('nn')}'"
    assert (
        parsed_a.group("nn") == "11"
    ), f"Expected order 11 for second sorted path (aa1111), got '{parsed_a.group('nn')}'"


def test_guard_foreign_type_path_refusal_eby93o(
    repo_with_plans: tuple[Path, dict[str, Path]],
):
    """(e) Order 01 / eby93o containment: a foreign-type path handed to `aw rename plans` refuses."""
    repo, _ = repo_with_plans
    specs_dir = repo / ".aw" / "records" / "specs" / "pending"
    specs_dir.mkdir(parents=True, exist_ok=True)
    spec_path = specs_dir / "20260929-demospec-01-sp1111-demo-spec.spec.md"
    spec_content = "# Spec: Demo Spec\n\n- Date: 2026-09-29\n- Kind: spec\n- Status: draft\n- Id: sp1111\n- Set: demospec\n"
    spec_path.write_text(spec_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add spec"], cwd=repo, check=True)

    rc, out = run_aw(
        repo,
        "rename",
        "plans",
        str(spec_path.relative_to(repo)),
        "--slug",
        "hijacked",
        "--apply",
    )
    assert (
        rc == 2
    ), f"Expected rc=2 refusal for foreign type path, got rc={rc}. Output:\n{out}"
    assert "plans verb cannot act on" in out
    assert "not inside the plans records tree" in out
    # Spec file must be untouched on disk
    assert spec_path.exists()
    assert spec_path.read_text(encoding="utf-8") == spec_content


def test_guard_multi_match_refusal_and_force_f15(
    repo_with_plans: tuple[Path, dict[str, Path]],
):
    """(f) F-15 / OQ-05: a setid naming a multi-plan Set handed to `aw rename plans` refuses with candidate
    list and does NOT rename any file; with --force renames the first member.
    """
    repo, _ = repo_with_plans
    plans_dir = repo / ".aw" / "records" / "plans" / "pending"
    p1 = plans_dir / "20260929-multiset-01-m11111-first.ipd.md"
    p1_content = "# IPD: First\n\n- Date: 2026-09-29\n- Kind: child\n- Status: pending\n- Id: m11111\n- Set: multiset\n- Order: 1\n"
    p1.write_text(p1_content, encoding="utf-8")
    p2 = plans_dir / "20260929-multiset-02-m22222-second.ipd.md"
    p2_content = "# IPD: Second\n\n- Date: 2026-09-29\n- Kind: child\n- Status: pending\n- Id: m22222\n- Set: multiset\n- Order: 2\n"
    p2.write_text(p2_content, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add multiset plans"], cwd=repo, check=True)

    # 1. Without --force: MUST refuse at exit 2 and rename NOTHING
    rc, out = run_aw(
        repo, "rename", "plans", "multiset", "--slug", "renamed-multi", "--apply"
    )
    assert rc == 2, f"Expected rc=2 refusal, got rc={rc}. Output:\n{out}"
    assert "matched multiple files; rename targets one" in out
    assert "--force" in out
    assert p1.name in out or str(p1) in out
    assert p2.name in out or str(p2) in out
    # Both files must remain unchanged with their original names on disk
    assert p1.exists(), "p1 was renamed unexpectedly!"
    assert p2.exists(), "p2 was renamed unexpectedly!"
    assert p1.read_text(encoding="utf-8") == p1_content
    assert p2.read_text(encoding="utf-8") == p2_content

    # 2. With --force: renames the first candidate
    rc_force, out_force = run_aw(
        repo,
        "rename",
        "plans",
        "multiset",
        "--slug",
        "renamed-multi",
        "--force",
        "--apply",
    )
    assert (
        rc_force == 0
    ), f"Expected rc=0 with --force, got rc={rc_force}. Output:\n{out_force}"
    assert not p1.exists(), "p1 should have been renamed"
    assert p2.exists(), "p2 should NOT have been renamed"
    renamed_p1 = list(plans_dir.glob("*multiset*renamed-multi*"))
    assert len(renamed_p1) == 1
    parsed_renamed = artifact_naming.parse_clustered(renamed_p1[0].name)
    assert parsed_renamed is not None
    assert parsed_renamed.group("id6") == "m11111"
    assert parsed_renamed.group("slug") == "renamed-multi"
