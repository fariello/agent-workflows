"""Behavioral tests for engine.py opt-in hooks, shim customization, managed blocks, and lane merge.

Restores test coverage for 12 unguarded-unreached engine keys recorded in backlog item 7df9md
and rollup findings b1mx2w, whose behavioral tests were deleted at 19313eed^ (specifically
from tests/test_command_shims.py and tests/test_comms.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agent_workflows import engine, manifest
from tests.support import SOURCE_WORKFLOWS

pytestmark = pytest.mark.core


# ======================================================================================
# E-02: Opt-in pre-commit and pre-push hook installers
# ======================================================================================

_USER_CONFIG = (
    "repos:\n"
    "  - repo: https://example.invalid/user-hook\n"
    "    rev: v1\n"
    "    hooks:\n"
    "      - id: user-hook\n"
)


@pytest.mark.parametrize(
    "installer,hook_id",
    [
        (engine.create_dependency_gate_hook, "ipd-dependency-statement-gate"),
        (engine.create_precommit_scope_gate_hook, "aw-precommit-scope-gate"),
        (
            engine.create_prepush_authorization_gate_hook,
            "aw-prepush-authorization-gate",
        ),
    ],
    ids=["dependency_gate", "precommit_scope_gate", "prepush_authorization_gate"],
)
def test_optin_hook_installer(tmp_path: Path, installer, hook_id: str) -> None:
    """Verify opt-out, dry-run, fresh create, idempotency, and no-clobber append behaviors."""
    pc_file = tmp_path / engine.PRE_COMMIT_CONFIG

    # (a) OPT-OUT: install=False returns empty dict and creates nothing
    res_optout = installer(tmp_path, use_git=False, install=False)
    assert res_optout == {"created": [], "skipped": [], "notes": []}
    assert not pc_file.exists()

    # (b) DRY-RUN with no config: writes nothing, emits creation note naming hook id
    res_dry_fresh = installer(tmp_path, use_git=False, install=True, dry_run=True)
    assert not pc_file.exists()
    assert any(
        f"would create {engine.PRE_COMMIT_CONFIG}" in n and hook_id in n
        for n in res_dry_fresh["notes"]
    )

    # (c) FRESH CREATE: writes config with top-level repos list and hook id
    res_create = installer(tmp_path, use_git=False, install=True)
    assert res_create["created"] == [engine.PRE_COMMIT_CONFIG]
    assert pc_file.exists()
    content_c = pc_file.read_text(encoding="utf-8")
    assert hook_id in content_c
    doc_c = yaml.safe_load(content_c)
    assert (
        isinstance(doc_c, dict)
        and "repos" in doc_c
        and isinstance(doc_c["repos"], list)
    )
    bytes_c = pc_file.read_bytes()

    # (d) IDEMPOTENT: second install reports skipped already wired and leaves file byte-identical
    res_idempotent = installer(tmp_path, use_git=False, install=True)
    assert any("already wired" in s for s in res_idempotent["skipped"])
    assert pc_file.read_bytes() == bytes_c

    # (e) & (f) Pre-existing user config in a separate subfolder
    append_dir = tmp_path / "append_case"
    append_dir.mkdir()
    append_pc = append_dir / engine.PRE_COMMIT_CONFIG
    append_pc.write_text(_USER_CONFIG, encoding="utf-8")
    bytes_before = append_pc.read_bytes()

    # (f) DRY-RUN APPEND: returns would append note and leaves file byte-unchanged
    res_dry_append = installer(append_dir, use_git=False, install=True, dry_run=True)
    assert any(
        n.startswith("would append") and hook_id in n for n in res_dry_append["notes"]
    )
    assert append_pc.read_bytes() == bytes_before

    # (e) NO-CLOBBER APPEND: user config prefix survives, new hook appended exactly once in YAML
    res_append = installer(append_dir, use_git=False, install=True)
    assert any(
        n.startswith("appended the") and hook_id in n for n in res_append["notes"]
    )
    content_e = append_pc.read_text(encoding="utf-8")
    assert content_e.startswith(_USER_CONFIG.rstrip("\n"))
    doc_e = yaml.safe_load(content_e)
    hook_ids = [h["id"] for r in doc_e.get("repos", []) for h in r.get("hooks", [])]
    assert hook_ids == ["user-hook", hook_id]


# ======================================================================================
# E-03: Recursive lane migration and non-clobbering tree merge
# ======================================================================================


def test_migrate_local_lanes_collision_preserves_old_and_moves_uniques(
    tmp_path: Path,
) -> None:
    """migrate_local_lanes_to_untracked merges trees non-clobberingly and cleans empty dirs."""
    local_inbox = tmp_path / ".aw" / "records" / "comms" / "local" / "inbox"
    untracked_inbox = tmp_path / ".aw" / "records" / "comms" / "untracked" / "inbox"
    deep_dir = local_inbox / "deep"
    deep_dir.mkdir(parents=True, exist_ok=True)
    untracked_inbox.mkdir(parents=True, exist_ok=True)

    (local_inbox / "a.md").write_text("unique_a", encoding="utf-8")
    (local_inbox / "b.md").write_text("OLD", encoding="utf-8")
    (untracked_inbox / "b.md").write_text("NEW", encoding="utf-8")
    (deep_dir / "c.md").write_text("unique_c", encoding="utf-8")

    res = engine.migrate_local_lanes_to_untracked(tmp_path, {})
    assert ".aw/records/comms/untracked" in res
    assert (untracked_inbox / "a.md").read_text(encoding="utf-8") == "unique_a"
    assert (untracked_inbox / "deep" / "c.md").read_text(encoding="utf-8") == "unique_c"
    assert (untracked_inbox / "b.md").read_text(encoding="utf-8") == "NEW"
    assert (local_inbox / "b.md").read_text(encoding="utf-8") == "OLD"
    assert not deep_dir.exists()


def test_migrate_local_lanes_no_collision_idempotent(tmp_path: Path) -> None:
    """When only local/ exists, it is renamed to untracked/, and subsequent call is no-op."""
    local_dir = tmp_path / ".aw" / "records" / "comms" / "local"
    local_dir.mkdir(parents=True, exist_ok=True)
    (local_dir / "message.md").write_text("payload", encoding="utf-8")

    res1 = engine.migrate_local_lanes_to_untracked(tmp_path, {})
    assert not local_dir.exists()
    untracked_dir = tmp_path / ".aw" / "records" / "comms" / "untracked"
    assert (untracked_dir / "message.md").read_text(encoding="utf-8") == "payload"
    assert ".aw/records/comms/untracked" in res1

    res2 = engine.migrate_local_lanes_to_untracked(tmp_path, {})
    assert (untracked_dir / "message.md").read_text(encoding="utf-8") == "payload"
    assert ".aw/records/comms/untracked" not in res2


# ======================================================================================
# E-04: Slash-command shim grammar validation
# ======================================================================================

_OC = (
    "---\n"
    "description: test\n"
    "agent: build\n"
    "---\n"
    "Read and execute @.aw/system/workflows/verify/verify.md.\n"
)
_CL = (
    "---\n"
    "description: test\n"
    "---\n"
    "Read and execute @.aw/system/workflows/verify/verify.md.\n"
)
_CL_HINT = (
    "---\n"
    "description: test\n"
    'argument-hint: "[args]"\n'
    "---\n"
    "Read and execute @.aw/system/workflows/verify/verify.md.\n"
    "If the user provided arguments, use them: $ARGUMENTS\n"
)
_OC_ARGS = (
    "---\n"
    "description: test\n"
    "agent: build\n"
    "---\n"
    "Read and execute @.aw/system/workflows/verify/verify.md.\n"
    "If the user provided arguments, use them: $ARGUMENTS\n"
)


def test_validate_shim_grammar_positive() -> None:
    """Positive cases: controls, dispatchers across tools/layouts, and generated alias shims."""
    assert engine.validate_shim_grammar(_OC, "opencode") is True
    assert engine.validate_shim_grammar(_CL, "claude") is True
    assert engine.validate_shim_grammar(_CL_HINT, "claude") is True
    assert engine.validate_shim_grammar(_OC_ARGS, "opencode") is True

    workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
    for tool in ("opencode", "claude"):
        for layout in ("aw", "legacy"):
            dispatcher = engine.aw_dispatcher_shim(
                workflows, tool, target_layout=layout
            )
            assert engine.validate_shim_grammar(dispatcher, tool) is True

    shims = engine.generate_shim_members(
        workflows, SOURCE_WORKFLOWS, target_layout="aw"
    )
    non_readme_shims = {k: v for k, v in shims.items() if not k.endswith("README.md")}
    assert len(non_readme_shims) > 0
    for rel, content in non_readme_shims.items():
        tool = "claude" if rel.startswith(".claude") else "opencode"
        assert engine.validate_shim_grammar(content, tool) is True, f"Failed for {rel}"


@pytest.mark.parametrize(
    "case_name,text,tool",
    [
        ("empty_string", "", "opencode"),
        ("whitespace_only", "   \n\n", "claude"),
        ("unknown_tool", _OC, "unknown_tool"),
        ("missing_opening_fence", "\n".join(_OC.splitlines()[1:]), "opencode"),
        (
            "missing_closing_fence",
            "\n".join(line for i, line in enumerate(_OC.splitlines()) if i != 3),
            "opencode",
        ),
        (
            "no_description",
            "---\nagent: build\n---\nRead and execute @.aw/system/workflows/verify/verify.md.\n",
            "opencode",
        ),
        ("opencode_without_agent", _CL, "opencode"),
        ("claude_with_agent", _OC, "claude"),
        (
            "no_workflow_body_reference",
            "---\ndescription: test\nagent: build\n---\nRead and execute some random path.\n",
            "opencode",
        ),
        (
            "claude_argument_hint_without_arguments",
            (
                "---\n"
                "description: test\n"
                'argument-hint: "[args]"\n'
                "---\n"
                "Read and execute @.aw/system/workflows/verify/verify.md.\n"
            ),
            "claude",
        ),
        (
            "arguments_without_clause",
            (
                "---\n"
                "description: test\n"
                "agent: build\n"
                "---\n"
                "Read and execute @.aw/system/workflows/verify/verify.md.\n"
                "Just args $ARGUMENTS\n"
            ),
            "opencode",
        ),
    ],
    ids=[
        "empty_string",
        "whitespace_only",
        "unknown_tool",
        "missing_opening_fence",
        "missing_closing_fence",
        "no_description",
        "opencode_without_agent",
        "claude_with_agent",
        "no_workflow_body_reference",
        "claude_argument_hint_without_arguments",
        "arguments_without_clause",
    ],
)
def test_validate_shim_grammar_negative(case_name: str, text: str, tool: str) -> None:
    """Each negative row applies exactly one defect against a valid control and returns False."""
    assert engine.validate_shim_grammar(text, tool) is False


# ======================================================================================
# E-05: Shim customization detection and drift decisions
# ======================================================================================


def test_is_shim_customized_predicates() -> None:
    """is_shim_customized and is_stale_shim_customized correctly identify standard vs modified."""
    workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
    oc_disp = engine.aw_dispatcher_shim(workflows, "opencode", target_layout="aw")
    cl_disp = engine.aw_dispatcher_shim(workflows, "claude", target_layout="aw")

    # Dispatchers are standard
    assert engine.is_shim_customized(oc_disp) is False
    assert engine.is_stale_shim_customized(oc_disp) is False
    assert engine.is_shim_customized(cl_disp) is False
    assert engine.is_stale_shim_customized(cl_disp) is False

    # Generated alias shims are standard
    shims = engine.generate_shim_members(
        workflows, SOURCE_WORKFLOWS, target_layout="aw"
    )
    non_readme_shims = {k: v for k, v in shims.items() if not k.endswith("README.md")}
    assert len(non_readme_shims) > 0
    for rel, content in non_readme_shims.items():
        assert (
            engine.is_shim_customized(content) is False
        ), f"Flagged standard alias: {rel}"
        assert engine.is_stale_shim_customized(content) is False

    # Appended handwritten line is customized
    custom_oc = oc_disp + "\nmy own extra instruction\n"
    assert engine.is_shim_customized(custom_oc) is True
    assert engine.is_stale_shim_customized(custom_oc) is True

    # Missing Read and execute line is customized
    no_read = (
        "---\ndescription: custom\nagent: build\n---\nDo something else entirely.\n"
    )
    assert engine.is_shim_customized(no_read) is True
    assert engine.is_stale_shim_customized(no_read) is True

    # Empty content is not customized
    assert engine.is_stale_shim_customized("") is False
    assert engine.is_shim_customized("") is False


def test_is_shim_customized_vs_expected() -> None:
    """is_shim_customized_vs_expected ignores description changes but flags body changes."""
    workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
    oc_disp = engine.aw_dispatcher_shim(workflows, "opencode", target_layout="aw")

    assert engine.is_shim_customized_vs_expected(oc_disp, oc_disp) is False

    diff_desc = oc_disp.replace("description: ", "description: completely different ")
    assert engine.is_shim_customized_vs_expected(diff_desc, oc_disp) is False

    added_body = oc_disp + "\nadded body instruction\n"
    assert engine.is_shim_customized_vs_expected(added_body, oc_disp) is True


def test_shim_is_user_modified_three_regimes(tmp_path: Path) -> None:
    """_shim_is_user_modified across no-manifest, recorded-hash, and unrecorded manifest regimes."""
    workflows = engine.parse_manifest(SOURCE_WORKFLOWS)
    cl_disp = engine.aw_dispatcher_shim(workflows, "claude", target_layout="aw")
    foreign_text = (
        "---\ndescription: foreign\n---\nForeign instruction without target ref\n"
    )
    rel = ".claude/commands/aw.md"

    # Regime 1: NO MANIFEST -> structural fallback
    plan_none = engine.InstallPlan(
        source_root=SOURCE_WORKFLOWS,
        repo_root=tmp_path,
        dry_run=True,
        backup=False,
        prune=False,
        manifest=None,
    )
    assert engine._shim_is_user_modified(plan_none, rel, cl_disp, cl_disp) is False
    assert engine._shim_is_user_modified(plan_none, rel, foreign_text, cl_disp) is True

    # Regime 2: MANIFEST WITH A RECORDED HASH
    # Record foreign text so recorded-hash answer DISAGREES with structural answer:
    # On-disk matching recorded foreign text -> NOT modified (False; structural says True)
    # On-disk cl_disp differing from recorded hash -> IS modified (True; structural says False)
    m_recorded = manifest.Manifest()
    m_recorded.record(rel, foreign_text)
    plan_recorded = engine.InstallPlan(
        source_root=SOURCE_WORKFLOWS,
        repo_root=tmp_path,
        dry_run=True,
        backup=False,
        prune=False,
        manifest=m_recorded,
    )
    assert (
        engine._shim_is_user_modified(plan_recorded, rel, foreign_text, cl_disp)
        is False
    )
    assert engine._shim_is_user_modified(plan_recorded, rel, cl_disp, cl_disp) is True
    # Confirm disagreement with structural fallback on identical content:
    assert engine.is_stale_shim_customized(foreign_text) is True
    assert engine.is_stale_shim_customized(cl_disp) is False

    # Regime 3: MANIFEST WITHOUT AN ENTRY FOR PATH -> structural fallback
    m_empty = manifest.Manifest()
    plan_empty = engine.InstallPlan(
        source_root=SOURCE_WORKFLOWS,
        repo_root=tmp_path,
        dry_run=True,
        backup=False,
        prune=False,
        manifest=m_empty,
    )
    assert engine._shim_is_user_modified(plan_empty, rel, cl_disp, cl_disp) is False
    assert engine._shim_is_user_modified(plan_empty, rel, foreign_text, cl_disp) is True


# ======================================================================================
# E-06: Pointer block and sectioned managed block
# ======================================================================================


def test_agents_pointer_block() -> None:
    """agents_pointer_block wraps untrusted notice in AGENTS markers with layout-aware paths."""
    p_legacy = engine.agents_pointer_block(target_layout="legacy")
    assert p_legacy.startswith(engine.AGENTS_BEGIN)
    assert p_legacy.endswith(engine.AGENTS_END + "\n")
    assert ".agents/comms/untracked/inbox/" in p_legacy
    assert "UNTRUSTED" in p_legacy

    p_aw = engine.agents_pointer_block(target_layout="aw")
    assert p_aw.startswith(engine.AGENTS_BEGIN)
    assert p_aw.endswith(engine.AGENTS_END + "\n")
    assert ".aw/records/comms/untracked/inbox/" in p_aw
    assert "UNTRUSTED" in p_aw


def test_agents_managed_block() -> None:
    """agents_managed_block renders delimited sections (aw:pointer then aw:reporting) stably."""
    b1 = engine.agents_managed_block(target_layout="aw")
    b2 = engine.agents_managed_block(target_layout="aw")
    lines = b1.splitlines()
    assert lines[0] == "<!-- aw:block -->"
    assert lines[-1] == "<!-- /aw:block -->"

    idx_ptr = b1.find("aw:pointer")
    idx_rep = b1.find("aw:reporting")
    assert idx_ptr != -1
    assert idx_rep != -1
    assert idx_ptr < idx_rep

    assert engine.AGENTS_BEGIN not in b1
    assert b1 == b2
