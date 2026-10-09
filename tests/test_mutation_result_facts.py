"""Outcome tests for typed MutationResult facts across rename and group backends.

Tests observable behavior and outcomes across plans_refs, artifact_rename,
and research_refs (IPD x7unul, Set eeiytw Order 01).
No inspect, ast, regex or substring checks over production source code.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pytest

from agent_workflows import artifact_rename, plans_refs, research_refs


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    return tmp_path


# --------------------------------------------------------------------------------------
# (a) Facts are present across backends, preview and apply
# --------------------------------------------------------------------------------------


def test_plans_backend_facts_preview_and_apply(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    plan_file = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    plan_file.write_text("# Plan Demo\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init plans", "-q"], cwd=temp_repo, check=True
    )

    # Preview
    args_prev = argparse.Namespace(
        dir=str(temp_repo),
        id="abc123",
        slug="renamed-demo",
        apply=False,
    )
    res_prev = plans_refs.run_mv(args_prev)
    assert res_prev.rc == 0
    assert res_prev.applied is False
    assert res_prev.touched_paths == ()
    assert len(res_prev.targets) == 1
    t_prev = res_prev.targets[0]
    assert t_prev.id6 == "abc123"
    assert t_prev.kind == "rename"
    assert t_prev.old_path == ".aw/records/plans/20261001-eeiytw-01-abc123-demo.ipd.md"
    assert (
        t_prev.new_path
        == ".aw/records/plans/20261001-eeiytw-01-abc123-renamed-demo.ipd.md"
    )
    assert t_prev.detail == "-> 20261001-eeiytw-01-abc123-renamed-demo.ipd.md"

    # Apply
    args_apply = argparse.Namespace(
        dir=str(temp_repo),
        id="abc123",
        slug="renamed-demo",
        apply=True,
    )
    res_apply = plans_refs.run_mv(args_apply)
    assert res_apply.rc == 0
    assert res_apply.applied is True
    assert len(res_apply.touched_paths) > 0
    assert len(res_apply.targets) == 1
    t_apply = res_apply.targets[0]
    assert t_apply.id6 == "abc123"
    assert t_apply.kind == "rename"
    assert t_apply.old_path == ".aw/records/plans/20261001-eeiytw-01-abc123-demo.ipd.md"
    assert (
        t_apply.new_path
        == ".aw/records/plans/20261001-eeiytw-01-abc123-renamed-demo.ipd.md"
    )


def test_artifact_rename_backend_facts_preview_and_apply(temp_repo: Path):
    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    spec_file = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    spec_file.write_text("# Spec Demo\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init specs", "-q"], cwd=temp_repo, check=True
    )

    # Rename preview
    args_rn_prev = argparse.Namespace(
        dir=str(temp_repo),
        id="abc123",
        slug="renamed-demo",
        apply=False,
    )
    res_rn_prev = artifact_rename.run_rename_generic(args_rn_prev, "specs")
    assert res_rn_prev.rc == 0
    assert res_rn_prev.applied is False
    assert res_rn_prev.touched_paths == ()
    assert len(res_rn_prev.targets) == 1
    assert res_rn_prev.targets[0].id6 == "abc123"
    assert res_rn_prev.targets[0].kind == "rename"

    # Bare group specs (no --rename) apply - tests F-04 metadata-only write
    args_grp_apply = argparse.Namespace(
        dir=str(temp_repo),
        ids=["abc123"],
        set="newset",
        rename=False,
        apply=True,
    )
    res_grp_apply = artifact_rename.run_group_generic(args_grp_apply, "specs")
    assert res_grp_apply.rc == 0
    assert res_grp_apply.applied is True
    assert len(res_grp_apply.touched_paths) > 0
    assert len(res_grp_apply.targets) >= 1
    # Metadata update must be recorded as target
    assert any(
        t.kind == "update" and "newset" in t.detail for t in res_grp_apply.targets
    )


def test_research_backend_facts_preview_and_apply(temp_repo: Path):
    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    res_file = rdir / "20261001-seta-01-r1id66-demo.findings.md"
    res_file.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [testing]
model: gpt5
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init research", "-q"], cwd=temp_repo, check=True
    )

    # Preview
    args_prev = argparse.Namespace(
        dir=str(temp_repo),
        id="r1id66",
        slug="renamed-demo",
        apply=False,
    )
    res_prev = research_refs.run_mv(args_prev)
    assert res_prev.rc == 0
    assert res_prev.applied is False
    assert res_prev.touched_paths == ()
    assert len(res_prev.targets) >= 1
    assert res_prev.targets[0].id6 == "r1id66"

    # Apply
    args_apply = argparse.Namespace(
        dir=str(temp_repo),
        id="r1id66",
        slug="renamed-demo",
        apply=True,
    )
    res_apply = research_refs.run_mv(args_apply)
    assert res_apply.rc == 0
    assert res_apply.applied is True
    assert len(res_apply.touched_paths) > 0
    assert len(res_apply.targets) >= 1


# --------------------------------------------------------------------------------------
# (a2) Research index refusal is captured on drift
# --------------------------------------------------------------------------------------


def test_research_index_refusal_captured_on_drift(temp_repo: Path):
    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    # Valid doc to move
    r1 = rdir / "20261001-seta-01-r1id66-demo.findings.md"
    r1.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [testing]
model: gpt5
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")
    # Drift doc: missing frontmatter block
    r2 = rdir / "20261001-seta-02-r2id66-drift.findings.md"
    r2.write_text("# Drift doc with no frontmatter\n")

    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init research with drift", "-q"],
        cwd=temp_repo,
        check=True,
    )

    args = argparse.Namespace(
        dir=str(temp_repo),
        id="r1id66",
        slug="renamed-demo",
        apply=True,
    )
    res = research_refs.run_mv(args)
    # rc must remain 0
    assert res.rc == 0
    # Diagnostics must capture the drift finding with severity == "warning"
    assert len(res.diagnostics) >= 1
    drift_diag = next(
        (d for d in res.diagnostics if "r2id66" in d.location or "drift" in d.location),
        None,
    )
    assert drift_diag is not None
    assert drift_diag.severity == "warning"
    assert drift_diag.rule == "frontmatter-missing"
    # Notes must contain the not-regenerated note
    assert any(
        "manifest was not regenerated" in n and "aw index research" in n
        for n in res.notes
    )


def test_research_index_clean_no_drift_diagnostic(temp_repo: Path):
    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    r1 = rdir / "20261001-seta-01-r1id66-demo.findings.md"
    r1.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [testing]
model: gpt5
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init clean research", "-q"], cwd=temp_repo, check=True
    )

    args = argparse.Namespace(
        dir=str(temp_repo),
        id="r1id66",
        slug="renamed-demo",
        apply=True,
    )
    res = research_refs.run_mv(args)
    assert res.rc == 0
    assert len(res.diagnostics) == 0
    assert not any("manifest was not regenerated" in n for n in res.notes)


# --------------------------------------------------------------------------------------
# (b) Refusals carry a diagnostic
# --------------------------------------------------------------------------------------


def test_refusals_carry_diagnostics(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    f1 = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    f1.write_text("# Plan Demo\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init plans", "-q"], cwd=temp_repo, check=True
    )

    # 1. Unknown id6
    args_unk = argparse.Namespace(dir=str(temp_repo), id="zzzz99", slug="x")
    res_unk = plans_refs.run_mv(args_unk)
    assert res_unk.rc == 2
    assert len(res_unk.diagnostics) >= 1
    assert "no plans artifact matched 'zzzz99'" in res_unk.diagnostics[0].detail

    # 2. Missing id6 list
    args_noid = argparse.Namespace(dir=str(temp_repo), ids=[], set="newset")
    res_noid = plans_refs.run_set_assign(args_noid)
    assert res_noid.rc == 2
    assert len(res_noid.diagnostics) >= 1
    assert "at least one <id6> is required" in res_noid.diagnostics[0].detail

    # 3. Over-length setid (> 24 chars)
    args_longset = argparse.Namespace(dir=str(temp_repo), ids=["abc123"], set="a" * 30)
    res_longset = plans_refs.run_set_assign(args_longset)
    assert res_longset.rc == 2
    assert len(res_longset.diagnostics) >= 1
    assert (
        "over the 24-character maximum for a setid" in res_longset.diagnostics[0].detail
    )

    # 4. Unknown selector in specs
    args_specs_unk = argparse.Namespace(dir=str(temp_repo), id="zzzz99", slug="x")
    res_specs_unk = artifact_rename.run_rename_generic(args_specs_unk, "specs")
    assert res_specs_unk.rc == 2
    assert len(res_specs_unk.diagnostics) >= 1
    assert "no specs artifact matched 'zzzz99'" in res_specs_unk.diagnostics[0].detail

    # 5. Missing set in group specs
    args_specs_noset = argparse.Namespace(dir=str(temp_repo), ids=["abc123"], set="")
    res_specs_noset = artifact_rename.run_group_generic(args_specs_noset, "specs")
    assert res_specs_noset.rc == 2
    assert len(res_specs_noset.diagnostics) >= 1
    assert "--set <set-id> is required" in res_specs_noset.diagnostics[0].detail


# --------------------------------------------------------------------------------------
# (c) Human stdout is byte-identical
# --------------------------------------------------------------------------------------

# Fragment representing nested index regeneration lines; Order 03 will delete this fragment.
_NESTED_PLANS_INDEX_LINE = (
    "wrote        .aw/records/plans/INDEX.json, INDEX.md (1 plans)\n"
)
_NESTED_RESEARCH_INDEX_LINE = (
    "wrote        .aw/records/research/INDEX.json, INDEX.md (1 docs)\n"
)


def test_human_stdout_byte_identical(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    pf = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    pf.write_text("# Plan\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")

    sdir = temp_repo / ".aw/records/specs"
    sdir.mkdir(parents=True, exist_ok=True)
    sf1 = sdir / "20261001-abc123-01-abc123-demo.spec.md"
    sf1.write_text("# Spec\n\n- Id: abc123\n- Set: abc123\n- Order: 01\n")
    sf2 = sdir / "20261001-s2id66-01-s2id66-second.spec.md"
    sf2.write_text("# Spec 2\n\n- Id: s2id66\n- Set: s2id66\n- Order: 01\n")

    rdir = temp_repo / ".aw/records/research"
    rdir.mkdir(parents=True, exist_ok=True)
    rf = rdir / "20261001-seta-01-r1id66-res.findings.md"
    rf.write_text("""---
id: r1id66
created: 20261001
set: seta
order: 01
topic: [slash-commands]
model: reconciliation
kind: findings
status: active
outcome: adopted
summary: test
consumed-by: []
---
# Res
""")

    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(["git", "commit", "-m", "init all", "-q"], cwd=temp_repo, check=True)

    # 1. rename plans preview
    cmd1 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "plans",
        "abc123",
        "--slug",
        "renamed-demo",
        "--dir",
        str(temp_repo),
    ]
    p1 = subprocess.run(cmd1, capture_output=True, text=True, check=True)
    expected1 = "--- would rename 20261001-eeiytw-01-abc123-demo.ipd.md -> 20261001-eeiytw-01-abc123-renamed-demo.ipd.md ---\n"
    assert p1.stdout == expected1

    # 2. rename plans apply
    cmd2 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "plans",
        "abc123",
        "--slug",
        "renamed-demo",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)
    expected2 = "renamed .aw/records/plans/20261001-eeiytw-01-abc123-demo.ipd.md -> .aw/records/plans/20261001-eeiytw-01-abc123-renamed-demo.ipd.md\n"
    assert p2.stdout == expected2

    # 3. group plans apply
    cmd3 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "group",
        "plans",
        "abc123",
        "--set",
        "newgrp",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p3 = subprocess.run(cmd3, capture_output=True, text=True, check=True)
    expected3 = ""
    assert p3.stdout == expected3

    # 4. rename specs apply
    cmd4 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "specs",
        "abc123",
        "--slug",
        "renamed-spec",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p4 = subprocess.run(cmd4, capture_output=True, text=True, check=True)
    expected4 = "renamed .aw/records/specs/20261001-abc123-01-abc123-demo.spec.md -> .aw/records/specs/20261001-abc123-01-abc123-renamed-spec.spec.md\n"
    assert p4.stdout == expected4

    # 5. group specs --rename apply
    cmd5 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "group",
        "specs",
        "s2id66",
        "--set",
        "specgrp",
        "--rename",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p5 = subprocess.run(cmd5, capture_output=True, text=True, check=True)
    expected5 = (
        "renamed .aw/records/specs/20261001-s2id66-01-s2id66-second.spec.md -> .aw/records/specs/20261001-specgrp-01-s2id66-second.spec.md\n"
        "set metadata Set: specgrp in .aw/records/specs/20261001-specgrp-01-s2id66-second.spec.md\n"
    )
    assert p5.stdout == expected5

    # 6. research mv apply
    cmd6 = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "research",
        "mv",
        "r1id66",
        "--slug",
        "renamed-res",
        "--apply",
        "--no-commit",
        "--dir",
        str(temp_repo),
    ]
    p6 = subprocess.run(cmd6, capture_output=True, text=True, check=True)
    expected6 = (
        "renamed .aw/records/research/20261001-seta-01-r1id66-res.findings.md -> .aw/records/research/20261001-seta-01-r1id66-renamed-res.findings.md\n"
        "set metadata set/order/kind in .aw/records/research/20261001-seta-01-r1id66-renamed-res.findings.md\n"
    )
    assert p6.stdout == expected6


# --------------------------------------------------------------------------------------
# (d) Self-commit path-set is unchanged
# --------------------------------------------------------------------------------------


def test_self_commit_path_set_unchanged(temp_repo: Path):
    pdir = temp_repo / ".aw/records/plans"
    pdir.mkdir(parents=True, exist_ok=True)
    f1 = pdir / "20261001-eeiytw-01-abc123-demo.ipd.md"
    f1.write_text("# Plan\n\n- Id: abc123\n- Set: eeiytw\n- Order: 01\n")
    subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init plans", "-q"], cwd=temp_repo, check=True
    )

    cmd = [
        sys.executable,
        "-m",
        "agent_workflows.cli",
        "rename",
        "plans",
        "abc123",
        "--slug",
        "renamed-demo",
        "--apply",
        "--commit",
        "--dir",
        str(temp_repo),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "Committed 2 path(s)" in res.stdout
    assert ".aw/records/plans/20261001-eeiytw-01-abc123-demo.ipd.md" in res.stdout
    assert (
        ".aw/records/plans/20261001-eeiytw-01-abc123-renamed-demo.ipd.md" in res.stdout
    )
