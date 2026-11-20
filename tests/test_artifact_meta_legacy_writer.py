"""Core tests for the phase-B legacy writer (`write_legacy`, `render_legacy_text`,
`restore_legacy_snapshot`, and the phase-B branch of `artifact_meta.create`; plan 7yr827 E-02).

Uses `tmp_path` fixtures only and drives the real `artifact_meta` API without reading source.
"""

from __future__ import annotations

import hashlib
import io
import re
import sqlite3
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

from agent_workflows import artifact_meta as meta
from agent_workflows import cli
from agent_workflows import prompts as prompts_mod
from agent_workflows import selectors as sel

pytestmark = pytest.mark.core

DAY = "2030-01-02"
REPO_ROOT = Path(__file__).resolve().parent.parent


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=root)
    subprocess.run(["git", "config", "user.name", "T"], cwd=root)
    (root / ".aw" / "records").mkdir(parents=True)
    (root / ".aw" / "state").mkdir(parents=True)
    return root


def _write_rec(root: Path, rel: str, text: str) -> Path:
    p = root / ".aw" / "records" / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _render(
    tag: str = "same-status", *, history: bool = False, is_prompt: bool = False
):
    return meta.LegacyRender(tag, DAY, "aw set", history=history, is_prompt=is_prompt)


# --------------------------------------------------------------------------------------------------
# (1) In-place bullet edit and unset
# --------------------------------------------------------------------------------------------------


def test_inplace_bullet_edit_and_unset(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)
    plan_text = (
        "# IPD: Sample\n\n"
        "- Date: 2026-01-01\n"
        "- Kind: child\n"
        "- Scope-Paths: agent_workflows/a.py\n"
        "- Item-Dependencies: none\n"
        "- Status: draft\n"
        "- Set: oldset\n"
        "- Order: 1\n"
        "- Highest E allocated: 02\n"
        "- Id: ab1234\n\n"
        "## Workflow history\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\n"
        "G\n"
    )
    p = _write_rec(
        root, "plans/pending/20260101-oldset-01-ab1234-sample.ipd.md", plan_text
    )

    meta.write_legacy(
        p,
        [
            {
                "op": "set",
                "fields": {
                    "set": "newset",
                    "order": 3,
                    "plan_role": "orchestrator",
                    "pipeline": "quick",
                    "short_description": "Concise plan summary",
                    "scope_paths": "agent_workflows/a.py, tests/test_a.py",
                    "highest_e_allocated": "04",
                    "item_dependencies": "executed:cd5678",
                    "attended": "required",
                    "from_plan": "xy9999",
                    "supersedes": "zz0000",
                },
            }
        ],
        record_type="ipd",
        render=_render(),
        repo_root=root,
        project_context=ctx,
    )
    updated = p.read_text(encoding="utf-8")
    assert "- Kind: orchestrator\n" in updated
    assert "- Set: newset\n" in updated
    assert "- Order: 3\n" in updated
    assert "- Highest E allocated: 04\n" in updated
    assert "- Scope-Paths: agent_workflows/a.py, tests/test_a.py\n" in updated
    assert "- Item-Dependencies: executed:cd5678\n" in updated
    assert "- Pipeline: quick\n" in updated
    assert "- Short-Description: Concise plan summary\n" in updated
    assert "- Attended: required\n" in updated
    assert "- From-Plan: xy9999\n" in updated
    assert "- Supersedes: zz0000\n" in updated

    meta.write_legacy(
        p,
        [
            {
                "op": "unset",
                "fields": [
                    "attended",
                    "pipeline",
                    "short_description",
                    "from_plan",
                    "supersedes",
                ],
            }
        ],
        record_type="plans",
        render=_render(),
        repo_root=root,
        project_context=ctx,
    )
    cleared = p.read_text(encoding="utf-8")
    for absent in (
        "- Attended:",
        "- Pipeline:",
        "- Short-Description:",
        "- From-Plan:",
        "- Supersedes:",
    ):
        assert absent not in cleared
    assert "- Set: newset\n" in cleared


# --------------------------------------------------------------------------------------------------
# (2) New bullet anchor fallback (- Status:, - Id:, block end) and a88210 prose-only non-insertion
# --------------------------------------------------------------------------------------------------


def test_new_bullet_anchor_fallback_and_a88210_prose_only_non_insertion() -> None:
    r = _render()

    # Anchor 1: after - Status:
    with_status = (
        "# IPD: A\n\n- Date: 2026-01-01\n- Status: draft\n- Id: aa0001\n\n## Goal\nG\n"
    )
    out_status = meta.render_legacy_text(
        with_status,
        [{"op": "set", "fields": {"attended": "required"}}],
        record_type="ipd",
        render=r,
    )
    assert out_status == (
        "# IPD: A\n\n- Date: 2026-01-01\n- Status: draft\n- Attended: required\n- Id: aa0001\n\n## Goal\nG\n"
    )

    # Anchor 2: after - Id: when - Status: is absent
    no_status = (
        "# IPD: B\n\n- Date: 2026-01-01\n- Id: bb0001\n- Author: a\n\n## Goal\nG\n"
    )
    out_id = meta.render_legacy_text(
        no_status,
        [{"op": "set", "fields": {"attended": "required"}}],
        record_type="ipd",
        render=r,
    )
    assert out_id == (
        "# IPD: B\n\n- Date: 2026-01-01\n- Id: bb0001\n- Attended: required\n- Author: a\n\n## Goal\nG\n"
    )

    # Anchor 3: end of existing metadata bullet block when neither - Status: nor - Id: is present
    block_only = "# IPD: C\n\n- Date: 2026-01-01\n- Author: a\n\n## Goal\nG\n"
    out_block = meta.render_legacy_text(
        block_only,
        [{"op": "set", "fields": {"attended": "required"}}],
        record_type="ipd",
        render=r,
    )
    assert out_block == (
        "# IPD: C\n\n- Date: 2026-01-01\n- Author: a\n- Attended: required\n\n## Goal\nG\n"
    )

    # a88210 prose-only plan: no metadata bullet block before first ## -> writes nothing into body
    prose_only = "# IPD: Prose Only\n\nThis plan has prose only and no metadata bullets.\n\n## Goal\nG\n"
    out_prose = meta.render_legacy_text(
        prose_only,
        [
            {
                "op": "set",
                "fields": {"attended": "required", "short_description": "Prose plan"},
            }
        ],
        record_type="ipd",
        render=r,
    )
    assert out_prose == prose_only


# --------------------------------------------------------------------------------------------------
# (3) Prompt aw-prompt comment edit, create comment rendering, and comment-less legacy purity
# --------------------------------------------------------------------------------------------------


def test_prompt_aw_prompt_comment_edit_create_and_commentless_purity(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)

    # Create via phase-B branch of artifact_meta.create
    create_preview = meta.create(
        "pr0001",
        "prompt",
        {
            "prompt_kind": "research",
            "set": "prset",
            "status": "pending",
            "created_day": "2030-01-02",
            "author": "opencode model-x",
            "targets": "gpt-6",
            "concerns": "metadata store",
            "results_go_to": ".aw/records/research/",
            "results": "none-yet",
            "grounding": "spec 4sd62s",
            "goal": "verify prompt rendering",
            "reviews_spec": "4sd62s",
            "basis": "phase B",
            "relation": "extends pr0000",
            "short_description": "Prompt short desc",
        },
        "You are a principal researcher.\n",
        destination="prompts/pending/20300102-prset-01-pr0001-probe.prompt.md",
        project_context=ctx,
        legacy_render=_render("pending", history=False, is_prompt=True),
        repo_root=root,
    )
    created_file = (
        root
        / ".aw"
        / "records"
        / "prompts/pending/20300102-prset-01-pr0001-probe.prompt.md"
    )
    assert created_file.is_file()
    assert create_preview.destination == created_file
    assert not (root / ".aw" / "records" / "meta" / "pr0001.jsonl").exists()
    created_lines = created_file.read_text(encoding="utf-8").splitlines()
    assert len(created_lines) == 2
    assert created_lines[0].startswith(
        "<!-- aw-prompt: Kind: research | Id: pr0001 | Set: prset | Status: pending"
    )
    assert "Short-Description: Prompt short desc" in created_lines[0]
    assert "Reviews-spec: 4sd62s" in created_lines[0]
    assert created_lines[1] == "You are a principal researcher."

    # Edit aw-prompt comment keys in place
    meta.write_legacy(
        created_file,
        [
            {
                "op": "set",
                "fields": {
                    "targets": "gemini-4, gpt-6",
                    "short_description": "Updated prompt desc",
                    "basis": "updated basis",
                },
            }
        ],
        record_type="prompt",
        render=_render("same-status", history=False, is_prompt=True),
        repo_root=root,
        project_context=ctx,
    )
    edited_lines = created_file.read_text(encoding="utf-8").splitlines()
    assert edited_lines[0].startswith("<!-- aw-prompt:")
    assert "Targets: gemini-4, gpt-6" in edited_lines[0]
    assert "Short-Description: Updated prompt desc" in edited_lines[0]
    assert "Basis: updated basis" in edited_lines[0]
    assert edited_lines[1] == "You are a principal researcher."
    assert "- Short-Description:" not in created_file.read_text(encoding="utf-8")

    # Comment-less legacy prompt purity: body stays byte-identical with zero bullets added
    bare_body = "# Legacy Prompt\n\nDo the work with zero preamble.\n"
    bare_file = _write_rec(
        root, "prompts/executed/20260701-0000-01-bare.prompt.md", bare_body
    )
    before_bytes = bare_file.read_bytes()
    meta.write_legacy(
        bare_file,
        [
            {
                "op": "set",
                "fields": {"short_description": "Must not be added", "set": "x"},
            }
        ],
        record_type="prompts",
        render=_render("same-status", history=False, is_prompt=True),
        repo_root=root,
        project_context=ctx,
    )
    assert bare_file.read_bytes() == before_bytes


# --------------------------------------------------------------------------------------------------
# (4) Research --- YAML front matter field edit
# --------------------------------------------------------------------------------------------------


def test_research_yaml_front_matter_field_edit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)
    research_text = (
        "---\n"
        "id: rs0001\n"
        "created: 20260901\n"
        "set: oldset\n"
        "order: 01\n"
        "topic: [alpha]\n"
        "kind: research-report\n"
        "status: todo\n"
        "outcome: none-yet\n"
        "consumed-by: []\n"
        "---\n\n"
        "# Research Title\n\n"
        "Body prose.\n"
    )
    p = _write_rec(
        root,
        "research/20260901-oldset-01-rs0001-topic.research-report.md",
        research_text,
    )
    meta.write_legacy(
        p,
        [
            {
                "op": "set",
                "fields": {
                    "set": "newset",
                    "order": "02",
                    "research_kind": "findings",
                    "outcome": "ingested",
                    "priority": "high",
                    "consumed_by": ["ab1234", "cd5678"],
                    "topic": ["alpha", "beta"],
                    "short_description": "YAML research summary",
                },
            }
        ],
        record_type="research",
        render=_render("same-status", history=False),
        repo_root=root,
        project_context=ctx,
    )
    out = p.read_text(encoding="utf-8")
    assert out == (
        "---\n"
        "id: rs0001\n"
        "created: 20260901\n"
        "set: newset\n"
        "order: 02\n"
        "topic: [alpha, beta]\n"
        "kind: findings\n"
        "status: todo\n"
        "outcome: ingested\n"
        "consumed-by: [ab1234, cd5678]\n"
        "priority: high\n"
        "short-description: YAML research summary\n"
        "---\n\n"
        "# Research Title\n\n"
        "Body prose.\n"
    )

    meta.write_legacy(
        p,
        [{"op": "unset", "fields": ["priority", "short_description"]}],
        record_type="research",
        render=_render("same-status", history=False),
        repo_root=root,
        project_context=ctx,
    )
    after_unset = p.read_text(encoding="utf-8")
    assert "priority:" not in after_unset
    assert "short-description:" not in after_unset


# --------------------------------------------------------------------------------------------------
# (5) ## Workflow history prepend (blank line kept, without blank line kept, section creation, legacy op)
# --------------------------------------------------------------------------------------------------


def test_workflow_history_prepend_blank_line_rules_and_legacy_op() -> None:
    r = _render("note", history=True)

    # With existing blank line under ## Workflow history: keep blank line and insert after it
    with_blank = (
        "# IPD: H1\n\n- Status: draft\n- Id: hb0001\n\n"
        "## Workflow history\n\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )
    out_with_blank = meta.render_legacy_text(
        with_blank,
        [{"op": "note", "message": "added note"}],
        record_type="ipd",
        render=r,
    )
    assert out_with_blank == (
        "# IPD: H1\n\n- Status: draft\n- Id: hb0001\n\n"
        "## Workflow history\n\n"
        f"- {DAY} note (aw set): added note\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )

    # Without blank line under ## Workflow history: keep zero blank line
    no_blank = (
        "# IPD: H2\n\n- Status: draft\n- Id: hb0002\n\n"
        "## Workflow history\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )
    out_no_blank = meta.render_legacy_text(
        no_blank,
        [{"op": "note", "message": "added note"}],
        record_type="ipd",
        render=r,
    )
    assert out_no_blank == (
        "# IPD: H2\n\n- Status: draft\n- Id: hb0002\n\n"
        "## Workflow history\n"
        f"- {DAY} note (aw set): added note\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )

    # Section-absent creation: before first ## for non-prompts, at end of file for prompts
    no_section_plan = "# IPD: H3\n\n- Status: draft\n- Id: hb0003\n\n## Goal\nG\n"
    out_created_plan = meta.render_legacy_text(
        no_section_plan,
        [{"op": "note", "message": "created section"}],
        record_type="ipd",
        render=r,
    )
    assert out_created_plan == (
        "# IPD: H3\n\n- Status: draft\n- Id: hb0003\n\n"
        "## Workflow history\n"
        f"- {DAY} note (aw set): created section\n\n"
        "## Goal\nG\n"
    )

    no_section_prompt = (
        "<!-- aw-prompt: Kind: run-once | Id: hp0001 | Status: pending -->\n"
        "## Section One\nPrompt body.\n"
    )
    out_created_prompt = meta.render_legacy_text(
        no_section_prompt,
        [{"op": "note", "message": "prompt note"}],
        record_type="prompt",
        render=_render("note", history=True, is_prompt=True),
    )
    assert out_created_prompt == (
        "<!-- aw-prompt: Kind: run-once | Id: hp0001 | Status: pending -->\n"
        "## Section One\nPrompt body.\n"
        "## Workflow history\n"
        f"- {DAY} note (aw set): prompt note\n"
    )

    # op == "legacy" (source == "history") verbatim prepend
    out_legacy = meta.render_legacy_text(
        with_blank,
        [
            {
                "op": "legacy",
                "source": "history",
                "line": "- 2030-01-05 note (lane): status unchanged (no lifecycle transition)",
            }
        ],
        record_type="ipd",
        render=_render("legacy", history=False),
    )
    assert out_legacy == (
        "# IPD: H1\n\n- Status: draft\n- Id: hb0001\n\n"
        "## Workflow history\n\n"
        "- 2030-01-05 note (lane): status unchanged (no lifecycle transition)\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )


# --------------------------------------------------------------------------------------------------
# (6) Phase-B create dry_run vs apply, lock acquisition, and source_digest mismatch refusal
# --------------------------------------------------------------------------------------------------


def test_phase_b_create_preview_apply_lock_and_source_digest_refusal(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)
    rel_dest = "plans/pending/20300102-crset-01-cr0001-new-plan.ipd.md"
    dest = root / ".aw" / "records" / rel_dest

    preview = meta.create(
        "cr0001",
        "ipd",
        {
            "status": "draft",
            "plan_role": "child",
            "set": "crset",
            "order": 1,
            "work_kind": "feature",
            "priority": "high",
            "short_description": "Create test plan",
        },
        "# IPD: New Plan\n\n## Goal\nTest phase-B create.\n",
        destination=rel_dest,
        dry_run=True,
        project_context=ctx,
        legacy_render=_render("draft", history=True),
        repo_root=root,
        message="created.",
    )
    assert isinstance(preview, meta.WritePreview)
    assert preview.changed is True
    assert not dest.exists()
    assert not (root / ".aw" / "records" / "meta" / "cr0001.jsonl").exists()
    assert not (root / ".aw" / "state" / "meta_journal" / "cr0001.json").exists()

    applied = meta.create(
        "cr0001",
        "ipd",
        {
            "status": "draft",
            "plan_role": "child",
            "set": "crset",
            "order": 1,
            "work_kind": "feature",
            "priority": "high",
            "short_description": "Create test plan",
        },
        "# IPD: New Plan\n\n## Goal\nTest phase-B create.\n",
        destination=rel_dest,
        dry_run=False,
        project_context=ctx,
        legacy_render=_render("draft", history=True),
        repo_root=root,
        message="created.",
    )
    assert applied.text == preview.text
    assert dest.read_text(encoding="utf-8") == preview.text
    # Lock was acquired under <state>/locks/meta-<id6>.lock
    assert (root / ".aw" / "state" / "locks" / "meta-cr0001.lock").exists()
    # No v2 log or recovery journal created
    assert not (root / ".aw" / "records" / "meta" / "cr0001.jsonl").exists()
    assert not (root / ".aw" / "state" / "meta_journal" / "cr0001.json").exists()

    # source_digest mismatch refusal leaves existing file byte-identical
    digest_before = _sha256(dest)
    with pytest.raises(ValueError, match="source digest"):
        meta.create(
            "cr0001",
            "ipd",
            {"status": "draft", "set": "crset"},
            "# IPD: Overwrite\n",
            destination=rel_dest,
            project_context=ctx,
            legacy_render=_render("draft", history=False),
            repo_root=root,
            source_digest="0" * 64,
        )
    assert _sha256(dest) == digest_before


# --------------------------------------------------------------------------------------------------
# (7) Refused set readiness leaves sha256 identical + restore_legacy_snapshot (D-5)
# --------------------------------------------------------------------------------------------------


def test_set_readiness_refusal_sha256_and_restore_legacy_snapshot(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)
    pre_pass_text = (
        "# IPD: Snapshot\n\n"
        "- Date: 2026-01-01\n"
        "- Kind: child\n"
        "- Status: to-review\n"
        "- Set: snap\n"
        "- Order: 1\n"
        "- Id: sn0001\n\n"
        "## Workflow history\n"
        "- 2026-01-01 to-review (aw set): status set to to-review\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )
    p = _write_rec(
        root, "plans/pending/20260101-snap-01-sn0001-snapshot.ipd.md", pre_pass_text
    )
    digest_before = _sha256(p)

    # AC-15: set readiness is refused by write_legacy and render_legacy_text; target sha256 unchanged
    with pytest.raises(ValueError, match="readiness"):
        meta.write_legacy(
            p,
            [{"op": "set", "fields": {"readiness": "go"}}],
            record_type="plans",
            render=_render(),
            repo_root=root,
            project_context=ctx,
        )
    digest_after = _sha256(p)
    assert digest_before == digest_after
    print(f"set_readiness_refusal_sha256: before={digest_before} after={digest_after}")

    with pytest.raises(ValueError, match="readiness"):
        meta.render_legacy_text(
            pre_pass_text,
            [{"op": "set", "fields": {"readiness": "go"}}],
            record_type="ipd",
            render=_render(),
            repo_root=root,
        )

    # D-5: restore_legacy_snapshot reverts premature - Status:, - Readiness:, and review history
    corrupted_text = (
        "# IPD: Snapshot\n\n"
        "- Date: 2026-01-01\n"
        "- Kind: child\n"
        "- Status: reviewed\n"
        "- Readiness: go\n"
        "- Set: snap\n"
        "- Order: 1\n"
        "- Id: sn0001\n\n"
        "## Workflow history\n"
        "- 2026-01-02 /plan-review (agy): APPROVE; readiness go\n"
        "- 2026-01-02 reviewed (aw set): status set to reviewed\n"
        "- 2026-01-01 to-review (aw set): status set to to-review\n"
        "- 2026-01-01 draft (a): created.\n\n"
        "## Goal\nG\n"
    )
    restored = meta.restore_legacy_snapshot(
        corrupted_text, pre_pass_text, record_type="ipd"
    )
    assert restored == pre_pass_text

    # Also test restoring when pre-pass ALREADY carried a prior - Readiness: value
    pre_with_rd = pre_pass_text.replace(
        "- Status: to-review\n", "- Status: to-review\n- Readiness: no-go\n"
    )
    changed_rd = pre_with_rd.replace(
        "- Readiness: no-go\n", "- Readiness: go\n"
    ).replace("- Status: to-review\n", "- Status: reviewed\n")
    restored_rd = meta.restore_legacy_snapshot(
        changed_rd, pre_with_rd, record_type="ipd"
    )
    assert restored_rd == pre_with_rd


# --------------------------------------------------------------------------------------------------
# (8) Tracked-corpus 5-type byte-identity and State equality round trip
# --------------------------------------------------------------------------------------------------


_CORPUS_BULLET_FIELDS: Dict[str, str] = {
    "Set": "set",
    "Order": "order",
    "Version": "version",
    "Priority": "priority",
    "Work-Kind": "work_kind",
    "Kind": "plan_role",
    "Pipeline": "pipeline",
    "Blocks-Release": "blocks_release",
    "From-Backlog": "from_backlog",
    "From-Spec": "from_spec",
    "From-Plan": "from_plan",
    "Supersedes": "supersedes",
    "Scope-Paths": "scope_paths",
    "Highest E allocated": "highest_e_allocated",
    "Graduated-To": "graduated_to",
    "Short-Description": "short_description",
    "Attended": "attended",
}

_CORPUS_PROMPT_FIELDS: Dict[str, str] = {
    "Kind": "prompt_kind",
    "Set": "set",
    "Author": "author",
    "Targets": "targets",
    "Concerns": "concerns",
    "Results": "results",
    "Results-go-to": "results_go_to",
    "Grounding": "grounding",
    "Goal": "goal",
    "Reviews-spec": "reviews_spec",
    "Basis": "basis",
    "Relation": "relation",
    "Short-Description": "short_description",
}


def _pick_writable_field(plural: str, text: str) -> Optional[Tuple[str, str]]:
    if plural == "prompts":
        first = text.split("\n", 1)[0]
        if "<!-- aw-prompt:" not in first:
            return None
        inner = first.split("<!-- aw-prompt:", 1)[1].rsplit("-->", 1)[0]
        inner = inner.split(" . This HTML comment", 1)[0]
        for seg in inner.split("|"):
            if ":" in seg:
                k, v = seg.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in _CORPUS_PROMPT_FIELDS and v:
                    return (_CORPUS_PROMPT_FIELDS[k], v)
        return None
    region = sel.metadata_region(text)
    for ln in region.splitlines():
        m = re.match(r"^-\s*([A-Za-z][A-Za-z0-9 /-]*?):\s*(.+?)\s*$", ln)
        if m and m.group(1) in _CORPUS_BULLET_FIELDS:
            return (_CORPUS_BULLET_FIELDS[m.group(1)], m.group(2))
    return None


def test_tracked_corpus_five_type_byte_identity_round_trip(tmp_path: Path) -> None:
    src_records = REPO_ROOT / ".aw" / "records"
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)

    per_type_counts: Dict[str, int] = {}
    selected: List[Tuple[str, Path, str, str, str]] = []

    for plural in ("plans", "specs", "backlog", "releases", "prompts"):
        files = sorted(
            p
            for p in (src_records / plural).rglob("*.md")
            if p.name != "README.md" and "untracked" not in p.parts
        )
        picked_for_type = 0
        for p in files:
            txt = p.read_text(encoding="utf-8")
            picked = _pick_writable_field(plural, txt)
            if picked is None:
                continue
            rel = p.relative_to(src_records)
            dest = root / ".aw" / "records" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(p.read_bytes())

            id6 = sel.read_front_matter_id(txt)
            if not id6:
                m_id = re.search(r"-([0-9a-z]{6})-", p.name)
                id6 = m_id.group(1) if m_id else ""
            assert id6, f"Missing id6 for selected corpus file {rel}"

            fk, fv = picked
            selected.append((plural, dest, id6, fk, fv))
            picked_for_type += 1
            if picked_for_type == 8:
                break
        per_type_counts[plural] = picked_for_type

    assert set(per_type_counts.keys()) == {
        "plans",
        "specs",
        "backlog",
        "releases",
        "prompts",
    }
    assert all(cnt >= 1 for cnt in per_type_counts.values())
    assert len(selected) >= 33

    states_before: Dict[str, meta.State] = {}
    raw_before_map: Dict[str, bytes] = {}
    for plural, dest, id6, fk, fv in selected:
        raw_before_map[str(dest)] = dest.read_bytes()
        states_before[id6] = meta.read(id6, project_context=ctx)

    for plural, dest, id6, fk, fv in selected:
        meta.write_legacy(
            dest,
            [{"op": "set", "fields": {fk: fv}}],
            record_type=plural,
            render=_render("same-status", history=False),
            repo_root=root,
            project_context=ctx,
        )

    identical = 0
    for plural, dest, id6, fk, fv in selected:
        state_after = meta.read(id6, project_context=ctx)
        raw_after = dest.read_bytes()
        assert states_before[id6] == state_after, f"State changed on {dest}"
        assert (
            raw_before_map[str(dest)] == raw_after
        ), f"Bytes changed on {dest} ({fk}={fv!r})"
        identical += 1

    assert identical == len(selected)
    print(f"corpus_round_trip: {identical}/{len(selected)} byte-identical")


# --------------------------------------------------------------------------------------------------
# (9) Prompt prompt_kind and created_day round-trip via create, aw prompts new, and stale cache
# --------------------------------------------------------------------------------------------------


def test_prompt_create_and_cli_new_preserve_prompt_kind_and_created_day(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)

    # Path 1: artifact_meta.create on a legacy root -> artifact_meta.read
    meta.create(
        "pr1001",
        "prompt",
        {
            "prompt_kind": "session-handoff",
            "set": "prset",
            "status": "pending",
            "created_day": "2030-01-02",
        },
        "Hand off this work cleanly.\n",
        destination="prompts/pending/20300102-prset-01-pr1001-handoff.prompt.md",
        project_context=ctx,
        legacy_render=_render("pending", history=False, is_prompt=True),
        repo_root=root,
    )
    st_created = meta.read("pr1001", project_context=ctx)
    assert st_created.type == "prompt"
    assert st_created.fields["prompt_kind"] == "session-handoff"
    assert st_created.fields["created_day"] == "2030-01-02"
    assert st_created.created_day == "2030-01-02"

    # Path 2: aw prompts new via cli.main -> artifact_meta.read
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(
            [
                "prompts",
                "new",
                "--slug",
                "cache-roundtrip",
                "--kind",
                "research",
                "--set",
                "prset",
                "--date",
                "2030-01-03",
                "--apply",
                "--dir",
                str(root),
            ]
        )
    assert rc == 0, out.getvalue() + err.getvalue()
    cli_files = sorted(
        (root / ".aw" / "records" / "prompts" / "pending").glob(
            "*cache-roundtrip.prompt.md"
        )
    )
    assert len(cli_files) == 1
    cli_text = cli_files[0].read_text(encoding="utf-8")
    cli_id6 = prompts_mod.read_metadata_id6(cli_text)
    assert cli_id6 is not None

    st_cli = meta.read(cli_id6, project_context=ctx)
    assert st_cli.type == "prompt"
    assert st_cli.fields["prompt_kind"] == "research"
    assert st_cli.fields["created_day"] == "2030-01-03"
    assert st_cli.created_day == "2030-01-03"


def test_stale_prompt_cache_rebuilt_under_legacy_loader_version(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    ctx = meta.legacy_context(root)

    meta.create(
        "pr2001",
        "prompt",
        {
            "prompt_kind": "research",
            "set": "prset",
            "status": "pending",
            "created_day": "2030-02-04",
        },
        "Analyze cache rebuild behavior.\n",
        destination="prompts/pending/20300204-prset-01-pr2001-rebuild.prompt.md",
        project_context=ctx,
        legacy_render=_render("pending", history=False, is_prompt=True),
        repo_root=root,
    )
    initial = meta.read("pr2001", project_context=ctx)
    assert initial.fields["prompt_kind"] == "research"
    assert initial.fields["created_day"] == "2030-02-04"
    assert initial.created_day == "2030-02-04"

    # Simulate a pre-legacy_v8 index.db with NULL prompt_kind/created_day and an older schema_hash
    db_path = root / ".aw" / "state" / "index.db"
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "UPDATE prompt SET prompt_kind = NULL, created_day = NULL WHERE id6 = ?",
            ("pr2001",),
        )
        con.execute(
            "UPDATE artifacts SET created_day = NULL WHERE id6 = ?",
            ("pr2001",),
        )
        con.execute(
            "UPDATE meta SET value = 'stale_legacy_v7_schema_hash' WHERE key = 'schema_hash'"
        )
        con.commit()
    finally:
        con.close()

    rebuilt = meta.read("pr2001", project_context=ctx)
    assert rebuilt.fields["prompt_kind"] == "research"
    assert rebuilt.fields["created_day"] == "2030-02-04"
    assert rebuilt.created_day == "2030-02-04"

    con = sqlite3.connect(str(db_path))
    try:
        stored_hash = con.execute(
            "SELECT value FROM meta WHERE key = 'schema_hash'"
        ).fetchone()[0]
        assert stored_hash == meta.compute_schema_hash()
        assert con.execute(
            "SELECT prompt_kind, created_day FROM prompt WHERE id6 = ?", ("pr2001",)
        ).fetchone() == ("research", "2030-02-04")
        assert con.execute(
            "SELECT created_day FROM artifacts WHERE id6 = ?", ("pr2001",)
        ).fetchone() == ("2030-02-04",)
    finally:
        con.close()
