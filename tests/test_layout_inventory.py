"""Tests for layout inventory classification and preflight gate behavior (IPD vv6y7e).

Validates that:
(1) the three single-trigger shapes (.agents/skills, .aw/.gitignore, .aw/setup-repo-needed.md)
    each dry-run cleanly;
(2) a combined shape carrying all three triggers dry-runs cleanly;
(3) an applied migration on the combined shape leaves all three paths present and byte-identical,
    and creates .aw/system/;
(4) direct classify_item assertions for the three paths match expected dispositions;
(5) a negative control with an unknown path (.agents/mystery.txt) still blocks and refuses;
(6) rollback after an applied migration leaves all three paths present.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict

import pytest

from agent_workflows import (
    attention,
    cli,
    layout_inventory,
    layout_migration,
    project_context,
)
from agent_workflows.layout_migration import MigrationError, PreflightGateError


@pytest.fixture(autouse=True)
def isolate_aw_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    aw_home = tmp_path / "isolated_aw_home"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))
    return aw_home


def _make_git_repo(repo_dir: Path, extra_files: Dict[str, bytes]) -> Path:
    repo_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main", str(repo_dir)], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "Test User"], check=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "core.autocrlf", "false"],
        check=True,
    )

    base_files = {
        ".agents/workflows/VERSION": b"1.0.0\n",
        ".agents/workflows/index.md": b"# Index\n",
        ".agents/plans/README.md": b"# Plans\n",
    }
    all_files = dict(base_files)
    all_files.update(extra_files)
    for rel, content in all_files.items():
        p = repo_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    subprocess.run(
        ["git", "-C", str(repo_dir), "add", "."], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "commit", "-m", "initial"],
        check=True,
        capture_output=True,
    )
    return repo_dir


def test_case_1_single_trigger_shapes_dry_run_cleanly(tmp_path: Path) -> None:
    """Case 1: the three single-trigger shapes each dry-run cleanly."""
    single_triggers = [
        ("skills", {".agents/skills/assess/SKILL.md": b"# Assess Skill\n"}),
        ("gitignore", {".aw/.gitignore": b"# AW gitignore\n"}),
        ("setup_marker", {".aw/setup-repo-needed.md": b"# Setup needed\n"}),
    ]
    for name, extra in single_triggers:
        repo = _make_git_repo(tmp_path / f"repo_single_{name}", extra)
        mgr = layout_migration.MigrationManager(str(repo))
        plan = mgr.execute_migration(dry_run=True, leftover_disposition="remove")
        assert plan.is_valid, f"Expected dry-run to succeed for single trigger {name}"


def test_case_2_combined_shape_dry_runs_cleanly(tmp_path: Path) -> None:
    """Case 2: a combined shape carrying all three triggers dry-runs cleanly."""
    combined_files = {
        ".agents/skills/assess/SKILL.md": b"# Assess Skill\n",
        ".aw/.gitignore": b"# AW gitignore\n",
        ".aw/setup-repo-needed.md": b"# Setup needed\n",
    }
    repo = _make_git_repo(tmp_path / "repo_combined_dry_run", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    plan = mgr.execute_migration(dry_run=True, leftover_disposition="remove")
    assert plan.is_valid, "Expected dry-run to succeed for combined shape"


def test_case_3_applied_migration_preserves_paths_and_creates_aw_system(
    tmp_path: Path,
) -> None:
    """Case 3: applied migration preserves all three paths and creates .aw/system/."""
    skills_bytes = b"# Skill Assess Payload\n"
    gitignore_bytes = b"# .aw/.gitignore Payload\n"
    marker_bytes = b"# Setup Marker Payload\n"

    combined_files = {
        ".agents/skills/assess/SKILL.md": skills_bytes,
        ".aw/.gitignore": gitignore_bytes,
        ".aw/setup-repo-needed.md": marker_bytes,
    }
    repo = _make_git_repo(tmp_path / "repo_applied", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    mgr.execute_migration(dry_run=False, leftover_disposition="remove")

    skills_path = repo / ".agents/skills/assess/SKILL.md"
    gitignore_path = repo / ".aw/.gitignore"
    marker_path = repo / ".aw/setup-repo-needed.md"
    system_dir = repo / ".aw/system"

    assert (
        skills_path.exists()
    ), "Expected .agents/skills/assess/SKILL.md to be preserved in place"
    assert (
        skills_path.read_bytes() == skills_bytes
    ), "Expected skills file to be byte-identical"

    assert gitignore_path.exists(), "Expected .aw/.gitignore to be skipped in place"
    assert (
        gitignore_path.read_bytes().replace(b"\r\n", b"\n").startswith(gitignore_bytes)
    ), "Expected .aw/.gitignore to preserve existing content"
    assert (
        b"records/*/untracked/" in gitignore_path.read_bytes()
    ), "Expected standard ignore patterns to be ensured"

    assert (
        marker_path.exists()
    ), "Expected .aw/setup-repo-needed.md to be skipped in place"
    assert (
        marker_path.read_bytes() == marker_bytes
    ), "Expected setup marker to be byte-identical"

    assert system_dir.is_dir(), "Expected .aw/system directory to be created"


def test_case_4_direct_classify_item_assertions() -> None:
    """Case 4: direct classify_item assertions for the three paths."""
    skills_res = layout_inventory.classify_item("agents", "skills/assess/SKILL.md")
    assert skills_res == {
        "ownership": "host-adapter-candidate",
        "lifecycle_class": "host-adapter-candidate",
        "expected_destination_class": "host-adapter-in-place",
        "disposition": "preserve",
    }

    # Also verify directory entries yielded by walker
    assert (
        layout_inventory.classify_item("agents", "skills")["disposition"] == "preserve"
    )
    assert (
        layout_inventory.classify_item("agents", "skills/assess")["disposition"]
        == "preserve"
    )

    gitignore_res = layout_inventory.classify_item("partial-aw", ".gitignore")
    assert gitignore_res == {
        "ownership": "system",
        "lifecycle_class": "system",
        "expected_destination_class": "system",
        "disposition": "skip",
    }

    marker_res = layout_inventory.classify_item("partial-aw", "setup-repo-needed.md")
    assert marker_res == {
        "ownership": "system",
        "lifecycle_class": "system",
        "expected_destination_class": "system",
        "disposition": "skip",
    }


def test_aw_inbox_lane_does_not_block_and_survives_applied_migration(
    tmp_path: Path,
) -> None:
    """A tracked .aw/inbox/README.md (written by every recent install) must not refuse the
    migration with unknown-owner, and must be left byte-identical in place."""
    readme_bytes = b"# Inbox lane\n"
    repo = _make_git_repo(
        tmp_path / "repo_inbox",
        {
            ".aw/inbox/README.md": readme_bytes,
            ".aw/.gitignore": b"/inbox/*\n!/inbox/README.md\n",
        },
    )
    mgr = layout_migration.MigrationManager(str(repo))
    assert mgr.execute_migration(dry_run=True, leftover_disposition="remove").is_valid

    mgr.execute_migration(dry_run=False, leftover_disposition="remove")
    assert (repo / ".aw/inbox/README.md").read_bytes() == readme_bytes
    assert (repo / ".aw/system").is_dir()


def test_case_5_negative_control_unknown_path_blocks_and_refuses(
    tmp_path: Path,
) -> None:
    """Case 5: negative control where an unrelated unknown path still blocks and refuses."""
    mystery_res = layout_inventory.classify_item("agents", "mystery.txt")
    assert mystery_res == {
        "ownership": "unknown",
        "lifecycle_class": "review-required",
        "expected_destination_class": "unknown",
        "disposition": "block-unknown",
    }

    repo = _make_git_repo(
        tmp_path / "repo_mystery", {".agents/mystery.txt": b"whoami\n"}
    )
    mgr = layout_migration.MigrationManager(str(repo))
    with pytest.raises(PreflightGateError) as exc_info:
        mgr.execute_migration(dry_run=True, leftover_disposition="remove")
    assert "agents:mystery.txt has unknown owner/disposition" in str(exc_info.value)


def test_case_6_rollback_leaves_all_three_paths_present(tmp_path: Path) -> None:
    """Case 6: after applied migration, rollback_migration() leaves all three paths present."""
    skills_bytes = b"# Skill Assess Payload\n"
    gitignore_bytes = b"# .aw/.gitignore Payload\n"
    marker_bytes = b"# Setup Marker Payload\n"

    combined_files = {
        ".agents/skills/assess/SKILL.md": skills_bytes,
        ".aw/.gitignore": gitignore_bytes,
        ".aw/setup-repo-needed.md": marker_bytes,
    }
    repo = _make_git_repo(tmp_path / "repo_rollback", combined_files)
    mgr = layout_migration.MigrationManager(str(repo))
    mgr.execute_migration(dry_run=False, leftover_disposition="remove")

    rb_res = mgr.rollback_migration()
    assert rb_res.get("status") == "rolled_back"

    skills_path = repo / ".agents/skills/assess/SKILL.md"
    gitignore_path = repo / ".aw/.gitignore"
    marker_path = repo / ".aw/setup-repo-needed.md"

    assert (
        skills_path.exists()
    ), "Expected .agents/skills/assess/SKILL.md to remain present after rollback"
    assert (
        skills_path.read_bytes() == skills_bytes
    ), "Expected skills file to be byte-identical after rollback"

    assert (
        gitignore_path.exists()
    ), "Expected .aw/.gitignore to remain present after rollback"
    assert (
        gitignore_path.read_bytes().replace(b"\r\n", b"\n").startswith(gitignore_bytes)
    ), "Expected .aw/.gitignore to preserve existing content after rollback"

    assert (
        marker_path.exists()
    ), "Expected .aw/setup-repo-needed.md to remain present after rollback"
    assert (
        marker_path.read_bytes() == marker_bytes
    ), "Expected setup marker to be byte-identical after rollback"


def test_populated_aw_tree_stays_in_place_and_is_not_nested(tmp_path: Path) -> None:
    """A repo already carrying `.aw/records`, `.aw/system`, `.aw/config` (a split-brain repo:
    current layout plus a residual `.agents/skills`) must migrate WITHOUT relocating those
    files onto doubled paths such as `.aw/records/records/...`."""
    files = {
        ".aw/records/plans/pending/p.ipd.md": b"# plan\n",
        ".aw/system/layout.json": b"{}\n",
        ".aw/config/policy.json": b"{}\n",
        ".agents/skills/assess/SKILL.md": b"# skill\n",
    }
    repo = _make_git_repo(tmp_path / "repo_populated_aw", files)
    layout_migration.MigrationManager(str(repo)).execute_migration(
        dry_run=False, leftover_disposition="defer"
    )
    for rel, content in files.items():
        if rel.startswith(".aw/"):
            assert (repo / rel).read_bytes() == content, rel
    for doubled in ("records/records", "system/system", "config/config"):
        assert not (repo / ".aw" / doubled).exists(), doubled


def test_every_legacy_agents_path_the_toolkit_reads_migrates(tmp_path: Path) -> None:
    """Legacy `.agents/` paths the toolkit still reads must neither refuse the migration nor be
    dropped: each lands at its modern `.aw/` equivalent, and `.agents/AGENTS.md` stays put."""
    moves = {
        ".agents/specs/s.spec.md": ".aw/records/specs/s.spec.md",
        ".agents/walkthroughs/w.walkthrough.md": ".aw/records/walkthroughs/w.walkthrough.md",
        ".agents/roadmaps/r.roadmap.md": ".aw/records/roadmaps/r.roadmap.md",
        ".agents/reviews/v.review.md": ".aw/records/reviews/v.review.md",
        ".agents/releases/x.release.md": ".aw/records/releases/x.release.md",
        ".agents/records/plans/pending/q.ipd.md": ".aw/records/plans/pending/q.ipd.md",
        ".agents/runs/run-1/state.json": ".aw/records/runs/run-1/state.json",
        ".agents/state/install.json": ".aw/state/durable/install.json",
        ".agents/inbox/drop.md": ".aw/inbox/drop.md",
        ".agents/research-models.toml": ".aw/config/research-models.toml",
        ".agents/config.json": ".aw/config/config.json",
    }
    kept = {".agents/AGENTS.md": b"# pointer\n"}
    files = {src: f'{{"payload": "{src}"}}\n'.encode() for src in moves}
    files.update(kept)
    repo = _make_git_repo(tmp_path / "repo_legacy_paths", files)
    mgr = layout_migration.MigrationManager(str(repo))
    assert mgr.execute_migration(dry_run=True, leftover_disposition="defer").is_valid

    mgr.execute_migration(dry_run=False, leftover_disposition="defer")
    import json

    for src, dst in moves.items():
        if dst == ".aw/config/config.json":
            # The switch phase stamps `records_backend` into this file; the payload survives.
            assert json.loads((repo / dst).read_text())["payload"] == src
        else:
            assert (repo / dst).read_bytes() == files[src], f"{src} -> {dst}"
        assert not (repo / src).exists(), f"{src} was not moved"
    assert (repo / ".agents/AGENTS.md").read_bytes() == kept[".agents/AGENTS.md"]


def test_refusal_names_the_unrecognized_top_level_path(tmp_path: Path) -> None:
    """An unknown directory is reported ONCE, at its top-level repo path, with a next step."""
    repo = _make_git_repo(
        tmp_path / "repo_unknown_dir",
        {".agents/mystery/a/b.md": b"x\n", ".agents/mystery/c.md": b"y\n"},
    )
    with pytest.raises(PreflightGateError) as exc_info:
        layout_migration.MigrationManager(str(repo)).execute_migration(
            dry_run=True, leftover_disposition="defer"
        )
    msg = str(exc_info.value)
    assert "classify: .agents/mystery." in msg
    assert "Nothing was changed" in msg
    assert (repo / ".agents/mystery/c.md").exists()


def _git_out(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_workflow_artifacts_classify_and_map_to_untracked_workflow_artifacts(
    tmp_path: Path,
) -> None:
    """workflow-artifacts classifies as state-runtime and maps to untracked workflow-artifacts/."""
    expected_cls = {
        "ownership": "state-runtime",
        "lifecycle_class": "state-runtime",
        "expected_destination_class": "workflow-artifacts",
        "disposition": "migrate",
    }
    assert layout_inventory.classify_item("workflow-artifacts", ".") == expected_cls
    assert (
        layout_inventory.classify_item(
            "workflow-artifacts", "assess-bugs/20260726-115243/report.md"
        )
        == expected_cls
    )
    assert (
        layout_inventory._legacy_class(
            "workflow-artifacts", "assess-bugs/20260726-115243/report.md"
        )
        == "state-runtime"
    )

    repo = _make_git_repo(
        tmp_path / "repo_wa_map",
        {
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": b"# Bug report\n",
            "workflow-artifacts/README.md": b"# Run scratch\n",
        },
    )
    roots = layout_inventory._default_roots(repo)
    inv_res = layout_inventory.inventory(repo, roots, include_paths=False)
    assert inv_res["valid"], inv_res["errors"]

    map_res = layout_inventory.build_migration_map(
        repo, inv_res, target_backend="repository"
    )
    assert map_res["valid"], map_res["errors"]

    wa_items = [
        item for item in map_res["items"] if item["source_root"] == "workflow-artifacts"
    ]
    assert wa_items
    by_rel = {item["source_relpath"]: item for item in wa_items}

    assert by_rel["."]["destination_root_class"] == "workflow-artifacts"
    assert by_rel["."]["destination_relpath"] == "workflow-artifacts"
    assert by_rel["."]["track_ignore_expectation"] == "untracked"

    report_item = by_rel["assess-bugs/20260726-115243/report.md"]
    assert report_item["destination_root_class"] == "workflow-artifacts"
    assert (
        report_item["destination_relpath"]
        == "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    )
    assert report_item["track_ignore_expectation"] == "untracked"

    readme_item = by_rel["README.md"]
    assert readme_item["destination_root_class"] == "workflow-artifacts"
    assert readme_item["destination_relpath"] == "workflow-artifacts/README.md"
    assert readme_item["track_ignore_expectation"] == "untracked"

    assert all(
        not item["destination_relpath"].startswith("records/") for item in wa_items
    )


def test_migrate_layout_cli_routes_workflow_artifacts_and_passes_attention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """aw migrate-layout --yes moves legacy workflow-artifacts to .aw/workflow-artifacts/ untracked."""
    tracked_wa = {
        "workflow-artifacts/assess-bugs/20260726-115243/report.md": b"# Assess bugs\n",
        "workflow-artifacts/advise-architect/20260727-100000/notes.md": b"# Architect notes\n",
        "workflow-artifacts/plan-review/20260728-090000/review.md": b"# Plan review\n",
        "workflow-artifacts/README.md": b"# Legacy run scratch README\n",
    }
    repo = _make_git_repo(
        tmp_path / "repo_legacy_121",
        {
            ".agents/plans/pending/20260701-01-plan.md": b"# IPD: Sample\n\n- Status: approved\n",
            **tracked_wa,
        },
    )
    untracked_rel = "workflow-artifacts/verify/20260729-080000/evidence.txt"
    untracked_bytes = b"pytest output: 10 passed\n"
    untracked_path = repo / untracked_rel
    untracked_path.parent.mkdir(parents=True, exist_ok=True)
    untracked_path.write_bytes(untracked_bytes)

    monkeypatch.chdir(repo)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("AW_NONINTERACTIVE", "1")

    rc = cli.main(["migrate-layout", "--yes"])
    assert rc == 0

    all_wa = dict(tracked_wa)
    all_wa[untracked_rel] = untracked_bytes
    for src_rel, expected_bytes in all_wa.items():
        dst = repo / ".aw" / src_rel
        assert dst.is_file(), f"Missing migrated artifact: {dst}"
        assert dst.read_bytes() == expected_bytes

    assert not (repo / "workflow-artifacts").exists()
    for bad in (
        "assess-bugs",
        "advise-architect",
        "plan-review",
        "verify",
        "README.md",
    ):
        assert not (repo / ".aw" / "records" / bad).exists(), bad

    assert _git_out(repo, "status", "--porcelain").stdout.strip() == ""
    assert (
        _git_out(
            repo, "ls-files", "--", ".aw/workflow-artifacts", "workflow-artifacts"
        ).stdout.strip()
        == ""
    )

    ign = _git_out(
        repo,
        "check-ignore",
        "-v",
        ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md",
    )
    assert ign.returncode == 0, ign.stderr
    assert ".aw/.gitignore" in ign.stdout

    att_doc = json.loads(attention.render_json(*attention.scan(repo), repo_root=repo))
    assert att_doc["valid"] is True, att_doc
    uninventoried = [
        v
        for v in att_doc.get("violations", [])
        if v.get("rule") == "attention.uninventoried-tree"
    ]
    assert uninventoried == []
    assert cli.main(["attention", "--check", "--dir", str(repo)]) == 0


def test_workflow_artifacts_edge_cases_merge_collision_rename_home_and_rollback(
    tmp_path: Path, isolate_aw_home: Path
) -> None:
    """Verify merge/collision guard, rename_to_grammar, home backend, and rollback + gitignore fallback."""
    # (a.1) Pre-existing non-colliding .aw/workflow-artifacts/ merges cleanly
    existing_bytes = b"# Newer run\n"
    legacy_bytes = b"# Older legacy run\n"
    repo_merge = _make_git_repo(
        tmp_path / "repo_wa_merge",
        {
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": legacy_bytes,
        },
    )
    pre_existing = (
        repo_merge / ".aw/workflow-artifacts/assess-bugs/20260901-101010/report.md"
    )
    pre_existing.parent.mkdir(parents=True, exist_ok=True)
    pre_existing.write_bytes(existing_bytes)

    mgr_merge = layout_migration.MigrationManager(str(repo_merge))
    mgr_merge.execute_migration(dry_run=False, leftover_disposition="remove")
    assert pre_existing.read_bytes() == existing_bytes
    assert (
        repo_merge / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).read_bytes() == legacy_bytes
    assert not (repo_merge / "workflow-artifacts").exists()

    # (a.2) Pre-existing non-identical collision fails closed leaving both files untouched
    foreign_bytes = b"# Different foreign bytes\n"
    repo_collide = _make_git_repo(
        tmp_path / "repo_wa_collide",
        {
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": legacy_bytes,
        },
    )
    dst_collide = (
        repo_collide / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    )
    dst_collide.parent.mkdir(parents=True, exist_ok=True)
    dst_collide.write_bytes(foreign_bytes)

    mgr_collide = layout_migration.MigrationManager(str(repo_collide))
    with pytest.raises(MigrationError, match="Refusing to overwrite"):
        mgr_collide.execute_migration(dry_run=False, leftover_disposition="remove")
    assert (
        repo_collide / "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).read_bytes() == legacy_bytes
    assert dst_collide.read_bytes() == foreign_bytes

    # (b) rename_to_grammar=True leaves .aw/workflow-artifacts/.../report.md unchanged
    repo_rename = _make_git_repo(
        tmp_path / "repo_wa_rename",
        {
            ".agents/plans/pending/20260701-01-plan.md": b"# IPD: Sample\n\n- Status: approved\n",
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": legacy_bytes,
        },
    )
    mgr_rename = layout_migration.MigrationManager(str(repo_rename))
    mgr_rename.execute_migration(
        dry_run=False, leftover_disposition="remove", rename_to_grammar=True
    )
    assert (
        repo_rename / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).read_bytes() == legacy_bytes
    assert not (
        repo_rename / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.ipd.md"
    ).exists()
    assert (repo_rename / ".aw/records/plans/pending/20260701-01-plan.ipd.md").is_file()

    # (c) Configured home backend moves records under AW_HOME while workflow-artifacts stays repo-local
    repo_home = _make_git_repo(
        tmp_path / "repo_wa_home",
        {
            ".aw/config/project.json": (
                json.dumps({"schema_version": 2, "records_backend": "home"}, indent=2)
                + "\n"
            ).encode("utf-8"),
            ".agents/plans/pending/20260701-01-homeplan.md": b"# IPD: Home\n\n- Status: approved\n",
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": legacy_bytes,
        },
    )
    mgr_home = layout_migration.MigrationManager(
        str(repo_home), aw_home=str(isolate_aw_home)
    )
    mgr_home.execute_migration(
        target_backend="home", dry_run=False, leftover_disposition="remove"
    )
    home_records = project_context.project_records_dir(
        repo_home, aw_home=isolate_aw_home
    )
    assert (home_records / "plans/pending/20260701-01-homeplan.md").is_file()
    assert (
        repo_home / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).read_bytes() == legacy_bytes
    assert not (home_records.parent / "workflow-artifacts").exists()
    assert not (home_records / "assess-bugs").exists()

    # (d.1) Standalone execute_migration + rollback_migration restores tracked files and index
    repo_rb = _make_git_repo(
        tmp_path / "repo_wa_rollback",
        {
            "workflow-artifacts/assess-bugs/20260726-115243/report.md": legacy_bytes,
        },
    )
    mgr_rb = layout_migration.MigrationManager(str(repo_rb))
    mgr_rb.execute_migration(dry_run=False, leftover_disposition="remove")
    assert not (repo_rb / "workflow-artifacts").exists()
    assert (
        repo_rb / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).is_file()

    rb_res = mgr_rb.rollback_migration()
    assert rb_res.get("status") == "rolled_back"
    assert (
        repo_rb / "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).read_bytes() == legacy_bytes
    assert not (repo_rb / ".aw/workflow-artifacts").exists()
    assert (
        _git_out(
            repo_rb, "status", "--porcelain", "--", "workflow-artifacts", ".agents"
        ).stdout.strip()
        == ""
    )
    assert (
        _git_out(repo_rb, "ls-files", "--", "workflow-artifacts").stdout.strip()
        == "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    )

    # (d.2) Rollback with legacy root .gitignore ignoring workflow-artifacts/ while force-tracked in HEAD
    repo_rb_ign = _make_git_repo(
        tmp_path / "repo_wa_rollback_ignored",
        {
            ".gitignore": b"workflow-artifacts/\n",
        },
    )
    forced_file = (
        repo_rb_ign / "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    )
    forced_file.parent.mkdir(parents=True, exist_ok=True)
    forced_file.write_bytes(legacy_bytes)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_rb_ign),
            "add",
            "-f",
            "workflow-artifacts/assess-bugs/20260726-115243/report.md",
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo_rb_ign),
            "commit",
            "-m",
            "force-track workflow artifact",
        ],
        check=True,
        capture_output=True,
    )

    mgr_rb_ign = layout_migration.MigrationManager(str(repo_rb_ign))
    mgr_rb_ign.execute_migration(dry_run=False, leftover_disposition="remove")
    assert not (repo_rb_ign / "workflow-artifacts").exists()
    assert (
        repo_rb_ign / ".aw/workflow-artifacts/assess-bugs/20260726-115243/report.md"
    ).is_file()

    rb_ign_res = mgr_rb_ign.rollback_migration()
    assert rb_ign_res.get("status") == "rolled_back"
    assert forced_file.read_bytes() == legacy_bytes
    assert not (repo_rb_ign / ".aw/workflow-artifacts").exists()
    assert (
        _git_out(
            repo_rb_ign, "status", "--porcelain", "--", "workflow-artifacts", ".agents"
        ).stdout.strip()
        == ""
    )
    assert (
        _git_out(repo_rb_ign, "ls-files", "--", "workflow-artifacts").stdout.strip()
        == "workflow-artifacts/assess-bugs/20260726-115243/report.md"
    )
