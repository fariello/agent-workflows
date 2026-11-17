"""Outcome tests for the migration chain, metadata_schema stamp, and read-path gate.

IPD g8na48 (E-04 / V-01..V-05). Spec 4sd62s Sections 5.1 and 5.3, AC-11, C12.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows.install_wizard import ProjectPolicy, persist_project_policy
from agent_workflows.migrations import chain
from agent_workflows.project_context import resolve_project_context
from agent_workflows.project_schema import Preset, ProjectRole, parse_portable_policy


pytestmark = pytest.mark.core


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )


def _legacy_plan_text(id6: str = "lg0001", status: str = "approved") -> str:
    return (
        f"# IPD: Legacy plan {id6}\n\n"
        f"- Id: {id6}\n"
        f"- Status: {status}\n"
        "- Set: legacy\n"
        "- Order: 1\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 draft (tester): created\n"
    )


# --------------------------------------------------------------------------------------
# V-01: Stamp read/write, legacy record detection, and require_current_schema
# --------------------------------------------------------------------------------------


def test_stamp_round_trip_repo_local_preserves_keys_and_trailing_newline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """write_metadata_schema adds metadata_schema while preserving sibling keys and newline."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True)
    proj_file = cfg_dir / "project.json"
    initial = {
        "schema_version": 2,
        "preset": "private-target",
        "role": "target",
        "cutovers": {"dependency_schema": "2026-09-01"},
        "custom_extra": {"keep": True},
    }
    proj_file.write_text(json.dumps(initial, indent=2) + "\n", encoding="utf-8")

    assert chain.read_metadata_schema(repo) is None

    written = chain.write_metadata_schema(repo, 2)
    assert written == proj_file
    raw_bytes = proj_file.read_bytes()
    assert raw_bytes.endswith(b"}\n")
    assert not raw_bytes.endswith(b"\n\n")

    parsed = json.loads(raw_bytes.decode("utf-8"))
    assert parsed["schema_version"] == 2
    assert parsed["preset"] == "private-target"
    assert parsed["cutovers"] == {"dependency_schema": "2026-09-01"}
    assert parsed["custom_extra"] == {"keep": True}
    assert parsed["metadata_schema"] == 2
    assert chain.read_metadata_schema(repo) == 2


def test_stamp_creates_new_file_and_honors_home_config_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """write_metadata_schema initializes schema_version on new files and honors home config."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    # Case 1: unconfigured repo creates <repo>/.aw/config/project.json with schema_version
    repo = tmp_path / "unconfigured"
    repo.mkdir()
    _init_git_repo(repo)
    written = chain.write_metadata_schema(repo, 1)
    assert written == repo / ".aw" / "config" / "project.json"
    data = json.loads(written.read_text(encoding="utf-8"))
    assert data == {"schema_version": 2, "metadata_schema": 1}
    assert written.read_bytes().endswith(b"}\n")

    # Case 2: home clean-delta config_project override
    home_repo = tmp_path / "home_repo"
    home_repo.mkdir()
    _init_git_repo(home_repo)
    home_proj = aw_home / "projects" / "custom-home" / "config" / "project.json"
    home_proj.parent.mkdir(parents=True)
    home_proj.write_text(
        json.dumps({"schema_version": 2, "preset": "clean-delta"}, indent=2) + "\n",
        encoding="utf-8",
    )

    assert chain.read_metadata_schema(home_repo, config_project=home_proj) is None
    chain.write_metadata_schema(home_repo, 2, config_project=home_proj)
    assert chain.read_metadata_schema(home_repo, config_project=home_proj) == 2
    assert not (home_repo / ".aw" / "config" / "project.json").exists()


@pytest.mark.parametrize("bad_value", [True, False, "2", 0, -1, 1.5])
def test_stamp_rejects_invalid_values(
    tmp_path: Path, bad_value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read_metadata_schema and write_metadata_schema reject bool, non-int, and < 1."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    with pytest.raises(ValueError):
        chain.write_metadata_schema(repo, bad_value)  # type: ignore[arg-type]

    cfg_path = repo / ".aw" / "config" / "project.json"
    cfg_path.parent.mkdir(parents=True)
    cfg_path.write_text(
        json.dumps({"schema_version": 2, "metadata_schema": bad_value}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        chain.read_metadata_schema(repo)


def test_legacy_records_detection_v2_exclusions_and_migration_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """repo_has_legacy_records handles empty, v2-only, excluded, .aw/records, and .agents trees."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    assert chain.repo_has_legacy_records(repo) is False
    assert len(chain.MIGRATIONS) == 1
    m0001 = chain.MIGRATIONS[0]
    assert (m0001.number, m0001.name, m0001.target_schema) == (1, "metadata-v2", 2)
    assert m0001.is_pending(repo) is False

    # Excluded files, v2 mirrors, and installed skills do not trigger legacy detection.
    rec_root = repo / ".aw" / "records"
    (rec_root / "plans" / "pending").mkdir(parents=True)
    (rec_root / "reviews").mkdir(parents=True)
    (rec_root / "prompts" / "pending").mkdir(parents=True)
    (rec_root / "walkthroughs").mkdir(parents=True)
    (rec_root / "comms" / "inbox").mkdir(parents=True)
    (rec_root / "research" / "sample.data").mkdir(parents=True)
    (rec_root / "prompt-library").mkdir(parents=True)
    (repo / ".agents" / "skills" / "aw").mkdir(parents=True)

    (rec_root / "README.md").write_text("# Records\n", encoding="utf-8")
    (rec_root / "INDEX.md").write_text("# Index\n", encoding="utf-8")
    (rec_root / "STATUS.md").write_text("# Status\n", encoding="utf-8")
    (rec_root / "comms" / "msg.md").write_text("prose message\n", encoding="utf-8")
    (rec_root / "research" / "sample.data" / "notes.md").write_text(
        "raw research note\n", encoding="utf-8"
    )
    (rec_root / "prompt-library" / "tpl.md").write_text(
        "prompt tpl\n", encoding="utf-8"
    )
    (rec_root / "research" / "conformance-results-template.md").write_text(
        "tpl\n", encoding="utf-8"
    )
    (
        rec_root / "research" / "20260712-0156-14-chatgpt-modular-report-template.md"
    ).write_text("tpl\n", encoding="utf-8")
    (repo / ".agents" / "skills" / "aw" / "SKILL.md").write_text(
        "# Skill\n", encoding="utf-8"
    )

    # v2 mirror files
    (rec_root / "plans" / "pending" / "20261109-test-01-abc123-slug.ipd.md").write_text(
        "---\nid: abc123\nstatus: draft\n---\n\n# Plan\n", encoding="utf-8"
    )
    (rec_root / "reviews" / "20261109-test-01-abc123-slug.review.md").write_text(
        "---\nsubject: abc123\nsubject_type: ipd\n---\n\n## Round 1\n",
        encoding="utf-8",
    )
    (
        rec_root / "prompts" / "pending" / "20261109-test-01-prm001-slug.prompt.md"
    ).write_text(
        "<!-- aw-managed-prompt: id: prm001 | status: pending -->\n\nPrompt body.\n",
        encoding="utf-8",
    )
    (
        rec_root / "walkthroughs" / "20261109-test-01-wlk001-slug.walkthrough.md"
    ).write_text("---\nid: wlk001\n---\n\n# Walkthrough\n", encoding="utf-8")

    assert chain.repo_has_legacy_records(repo) is False
    assert m0001.is_pending(repo) is False

    # Adding a ## Workflow history heading marks it as legacy.
    legacy_plan = rec_root / "plans" / "pending" / "20261109-test-02-def456-leg.ipd.md"
    legacy_plan.write_text(_legacy_plan_text("def456", "draft"), encoding="utf-8")
    assert chain.repo_has_legacy_records(repo) is True
    assert m0001.is_pending(repo) is True

    # Removing it restores False; adding a prose-only .agents record returns True.
    legacy_plan.unlink()
    assert chain.repo_has_legacy_records(repo) is False

    agents_plan = repo / ".agents" / "plans" / "pending" / "20260701-0900-01-prose.md"
    agents_plan.parent.mkdir(parents=True)
    agents_plan.write_text(
        "# Implementation Plan Document (IPD) - Legacy Prose\n\nBody only.\n",
        encoding="utf-8",
    )
    assert chain.repo_has_legacy_records(repo) is True
    assert m0001.is_pending(repo) is True


def test_refusal_under_schema_v1_and_v2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """require_current_schema allows everything at v1 and enforces AC-11 cases 1-3 at v2."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    # 1. Legacy .aw/records repo, unstamped (AC-11 case 1)
    legacy_aw = tmp_path / "legacy_aw"
    legacy_aw.mkdir()
    _init_git_repo(legacy_aw)
    p = (
        legacy_aw
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-leg-01-lg0001-s.ipd.md"
    )
    p.parent.mkdir(parents=True)
    p.write_text(_legacy_plan_text("lg0001"), encoding="utf-8")

    # Under CURRENT_METADATA_SCHEMA == 1, nothing refuses.
    chain.require_current_schema(legacy_aw)

    # Under CURRENT_METADATA_SCHEMA == 2, unstamped legacy .aw/records refuses.
    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    with pytest.raises(chain.MetadataSchemaError, match="run `aw migrate metadata`"):
        chain.require_current_schema(legacy_aw)

    # 2. Unstamped .agents/ legacy repo (C12 shape (a)/(c)) refuses.
    legacy_agents = tmp_path / "legacy_agents"
    legacy_agents.mkdir()
    _init_git_repo(legacy_agents)
    ap = legacy_agents / ".agents" / "plans" / "20260701-0900-01-prose.md"
    ap.parent.mkdir(parents=True)
    ap.write_text("# Implementation Plan Document (IPD) - Prose\n", encoding="utf-8")
    with pytest.raises(chain.MetadataSchemaError, match="run `aw migrate metadata`"):
        chain.require_current_schema(legacy_agents)

    # 3. Repository explicitly stamped metadata_schema: 1 refuses (AC-11 case 2).
    stamped_1 = tmp_path / "stamped_1"
    stamped_1.mkdir()
    _init_git_repo(stamped_1)
    chain.write_metadata_schema(stamped_1, 1)
    with pytest.raises(chain.MetadataSchemaError, match="run `aw migrate metadata`"):
        chain.require_current_schema(stamped_1)

    # 4. Empty repository (unstamped) passes silently (AC-11 case 3).
    empty_repo = tmp_path / "empty_repo"
    empty_repo.mkdir()
    _init_git_repo(empty_repo)
    chain.require_current_schema(empty_repo)

    # 5. Repository stamped metadata_schema: 2 passes silently.
    chain.write_metadata_schema(legacy_aw, 2)
    chain.require_current_schema(legacy_aw)


# --------------------------------------------------------------------------------------
# V-02: artifact_meta read-path schema gate (check_freshness and read_at)
# --------------------------------------------------------------------------------------


def test_artifact_meta_read_and_read_at_refuse_legacy_under_v2_and_allow_v2_stubs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """read and read_at raise MetadataSchemaError on legacy fixtures when schema is 2."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / "legacy_repo"
    repo.mkdir()
    _init_git_repo(repo)
    records_root = repo / ".aw" / "records"
    state_root = repo / ".aw" / "state"
    plan = (
        records_root
        / "plans"
        / "pending"
        / "20261101-legacy-01-lg0001-legacy-plan.ipd.md"
    )
    plan.parent.mkdir(parents=True)
    state_root.mkdir(parents=True)
    plan.write_text(_legacy_plan_text("lg0001", "approved"), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-qm", "legacy"], cwd=repo, check=True, capture_output=True
    )

    ctx = type(
        "Ctx",
        (),
        {
            "target_repo": str(repo),
            "logical_roots": {"records": records_root, "state": state_root},
        },
    )()

    # Under CURRENT_METADATA_SCHEMA == 1, both read and read_at succeed.
    assert meta.read("lg0001", project_context=ctx).status == "approved"
    rat_ok = meta.read_at("lg0001", "HEAD", project_context=ctx)
    assert rat_ok.kind == "ok" and rat_ok.state is not None

    # Under CURRENT_METADATA_SCHEMA == 2, read, history, resolve, query, review_rows, and read_at refuse.
    monkeypatch.setattr(chain, "CURRENT_METADATA_SCHEMA", 2)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.read("lg0001", project_context=ctx)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.read_at("lg0001", "HEAD", project_context=ctx)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.history("lg0001", project_context=ctx)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.resolve("lg0001", project_context=ctx)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.query(project_context=ctx)
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.review_rows("lg0001", project_context=ctx)

    # .agents/-only repo where .aw/records does not exist still refuses via check_freshness pre-check.
    agents_repo = tmp_path / "agents_only"
    agents_repo.mkdir()
    _init_git_repo(agents_repo)
    (agents_repo / ".agents" / "plans").mkdir(parents=True)
    (agents_repo / ".agents" / "plans" / "20260701-0900-01-a.md").write_text(
        "# Plan\n", encoding="utf-8"
    )
    agents_ctx = resolve_project_context(
        target_repo=str(agents_repo), aw_home=str(aw_home)
    )
    with pytest.raises(chain.MetadataSchemaError, match="aw migrate metadata"):
        meta.query(project_context=agents_ctx)

    # Bare logical_roots-only v2 log-only stub stays isolated to tmp_path and succeeds under v2.
    stub_records = tmp_path / "stub" / "records"
    stub_state = tmp_path / "stub" / "state"
    (stub_records / "meta").mkdir(parents=True)
    stub_state.mkdir(parents=True)
    (stub_records / "meta" / "v20001.jsonl").write_text(
        meta.encode_event(
            {
                "v": 1,
                "seq": 1,
                "append": 1,
                "at": "2026-11-06T12:00:00Z",
                "actor": {"tool": "test"},
                "op": "create",
                "path": "plans/pending/v20001.ipd.md",
                "fields": {
                    "id": "v20001",
                    "type": "ipd",
                    "status": "draft",
                    "set": "test",
                    "order": 1,
                },
            }
        ),
        encoding="utf-8",
    )
    stub_ctx = type(
        "Ctx", (), {"logical_roots": {"records": stub_records, "state": stub_state}}
    )()
    assert meta.read("v20001", project_context=stub_ctx).id6 == "v20001"


# --------------------------------------------------------------------------------------
# V-03: project_schema.parse_portable_policy validation and round trip
# --------------------------------------------------------------------------------------


def test_project_schema_parse_portable_policy_round_trip_and_rejection() -> None:
    """parse_portable_policy round-trips valid metadata_schema and rejects invalid types."""
    parsed = parse_portable_policy({"schema_version": 2, "metadata_schema": 2})
    assert parsed.metadata_schema == 2
    dumped = parsed.to_dict()
    assert dumped["metadata_schema"] == 2
    assert "metadata_schema" not in (parsed.unknown_fields or {})

    parsed_absent = parse_portable_policy({"schema_version": 2})
    assert parsed_absent.metadata_schema is None
    assert "metadata_schema" not in parsed_absent.to_dict()

    for bad_val in (True, False, "2", 0, -1, 2.5):
        with pytest.raises(ValueError, match="metadata_schema"):
            parse_portable_policy({"schema_version": 2, "metadata_schema": bad_val})


# --------------------------------------------------------------------------------------
# V-05: install_wizard.persist_project_policy preserves metadata_schema on reinstall
# --------------------------------------------------------------------------------------


def test_reinstall_preserves_metadata_schema_normal_and_fallback(
    tmp_path: Path,
) -> None:
    """persist_project_policy keeps metadata_schema=2 across normal and fallback rebuilds."""
    aw_home = tmp_path / "aw_home"
    aw_home.mkdir()
    policy = ProjectPolicy(
        preset=Preset.PRIVATE_TARGET.value,
        role=ProjectRole.TARGET.value,
        aw_home=str(aw_home),
    )

    # Normal try-branch reinstall
    repo_normal = tmp_path / "repo_normal"
    repo_normal.mkdir()
    _init_git_repo(repo_normal)
    cfg_normal = repo_normal / ".aw" / "config" / "project.json"
    cfg_normal.parent.mkdir(parents=True)
    cfg_normal.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "metadata_schema": 2,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    persist_project_policy(str(repo_normal), policy, replace_config=False)
    normal_bytes = cfg_normal.read_bytes()
    assert normal_bytes.endswith(b"}\n") and not normal_bytes.endswith(b"\n\n")
    assert json.loads(normal_bytes.decode("utf-8"))["metadata_schema"] == 2

    # Fallback except-ValueError-branch reinstall (malformed sibling key triggers ValueError)
    repo_fallback = tmp_path / "repo_fallback"
    repo_fallback.mkdir()
    _init_git_repo(repo_fallback)
    cfg_fallback = repo_fallback / ".aw" / "config" / "project.json"
    cfg_fallback.parent.mkdir(parents=True)
    cfg_fallback.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "invalid-legacy-preset-value",
                "role": "target",
                "metadata_schema": 2,
                "extra_preserved": "yes",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    persist_project_policy(str(repo_fallback), policy, replace_config=False)
    fallback_bytes = cfg_fallback.read_bytes()
    assert fallback_bytes.endswith(b"}\n") and not fallback_bytes.endswith(b"\n\n")
    rebuilt = json.loads(fallback_bytes.decode("utf-8"))
    assert rebuilt["metadata_schema"] == 2
    assert rebuilt["extra_preserved"] == "yes"
