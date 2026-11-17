"""Outcome tests for m0001 step-4 log builder and file rewrite (IPD ghhzb6).

Covers E-01..E-03 / V-01..V-03: JSONL append-0 event ordering, pre-rename path
continuity, dual-clock separation, per-type 4.2/4.5c field destinations,
Scope-Exceeded and describer seams, SR-903 control-character/long-line import,
4.1 mirrors and banners, AC-40 prompt conversion, and excluded tree integrity.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_workflows import artifact_meta, attention_contract
from agent_workflows.migrations import m0001_convert, m0001_metadata_v2

pytestmark = pytest.mark.core

_DEFAULT_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/runs/\n"
)


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "repo",
) -> Path:
    """Create a fresh isolated git repo with AW_HOME pointed into tmp_path."""
    aw_home = tmp_path / f"aw_home_{name}"
    aw_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AW_HOME", str(aw_home))

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    (repo / ".aw" / "records").mkdir(parents=True)
    (repo / ".aw" / ".gitignore").write_text(_DEFAULT_GITIGNORE, encoding="utf-8")
    return repo


def _snapshot_hashes(root: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    return out


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [
        artifact_meta.decode_line(line)
        for line in path.read_text(encoding="utf-8").splitlines(keepends=True)
        if line.strip()
    ]


# --------------------------------------------------------------------------------------
# V-01: layout (AC-32, Scope-Exceeded, describer, SR-903), path_history, clock, fields
# --------------------------------------------------------------------------------------


def test_layout_ac32_sequence_sidecar_scope_exceeded_describer_and_sr903(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify append-0 event layout, sidecar append order, Scope-Exceeded, describer, and SR-903."""
    repo = _init_repo(tmp_path, monkeypatch, name="layout")
    rec = repo / ".aw" / "records"
    plan_dir = rec / "plans" / "executed"
    plan_dir.mkdir(parents=True)

    long_history = "x" * 5000 + "\x07bell\x1b[0m"
    plan_path = plan_dir / "20261101-demo-01-pl1001-layout-plan.ipd.md"
    plan_path.write_text(
        "# Layout Test Plan\n\n"
        "- Id: pl1001\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Date: 2026-11-01\n"
        "- Kind: leaf\n"
        "- Scope-Paths: `agent_workflows/x.py`, `tests/test_x.py`\n"
        "- Scope-Exceeded: agent_workflows/y.py (shared helper fix); docs/extra.md (doc update)\n"
        "- Item-Dependencies: none\n\n"
        "## Objective\n\n"
        "Verify layout construction.\n\n"
        "## Workflow history\n\n"
        f"- 2026-11-02 executed (codex): {long_history}\n"
        "- 2026-11-01 approved (human): approved by maintainer\n",
        encoding="utf-8",
    )

    sidecar_records = [
        {
            "op": "legacy",
            "source": "sidecar",
            "observed_day": "2026-11-01",
            "position": 0,
            "ordering_confidence": "unknown",
            "line": "- 2026-11-01 note (sidecar): recovered sidecar line",
        }
    ]

    describer_calls: List[Dict[str, Any]] = []

    def _describer(id6: str, art_type: str, rel_path: str, text: str) -> Dict[str, Any]:
        describer_calls.append({"id6": id6, "art_type": art_type, "rel_path": rel_path})
        return {
            "short_description": "Verify conversion layout",
            "model": "test-model-1",
            "prompt_version": "v1",
        }

    fixed_at = "2026-11-17T06:00:00Z"
    _id6, _art_type, events, meta = m0001_convert.build_record_log(
        plan_path,
        rec,
        repo_root=repo,
        sidecar_events=sidecar_records,
        describer=_describer,
        migration_at=fixed_at,
    )

    assert len(describer_calls) == 1
    assert [e["op"] for e in events] == ["checkpoint", "legacy", "legacy", "legacy"]
    assert [e["seq"] for e in events] == [0, 1, 2, 3]
    assert all(e["append"] == 0 for e in events)
    assert all(e["at"] == fixed_at for e in events)
    assert all(e["actor"] == {"tool": "aw migrate metadata"} for e in events)
    assert all(e["op"] not in ("finalize", "turn") for e in events)

    cp_fields = events[0]["fields"]
    assert cp_fields["scope_result"] == "exceeded"
    expected_oos = [
        {"path": "agent_workflows/y.py", "reason": "shared helper fix"},
        {"path": "docs/extra.md", "reason": "doc update"},
    ]
    assert cp_fields["out_of_scope_paths"] == expected_oos
    assert (
        cp_fields["scope_exceeded_raw"]
        == "agent_workflows/y.py (shared helper fix); docs/extra.md (doc update)"
    )
    assert cp_fields["short_description"] == "Verify conversion layout"
    assert cp_fields["description_source"] == "generated"
    assert cp_fields["description_model"] == "test-model-1"
    assert cp_fields["description_prompt_version"] == "v1"

    assert events[1]["source"] == "history"
    assert events[1]["ordering_confidence"] == "unknown"
    assert events[1]["line"].endswith(long_history)
    assert len(events[1]["line"]) > 5000
    assert events[2]["source"] == "history"
    assert events[2]["ordering_confidence"] == "unknown"
    assert events[3]["source"] == "sidecar"
    assert events[3]["ordering_confidence"] == "unknown"
    assert events[3]["line"] == "- 2026-11-01 note (sidecar): recovered sidecar line"

    state_cp, _, _, _ = artifact_meta.replay(
        "pl1001", "ipd", events[:1], records_root=rec, migration_import=True
    )
    state, _ev_log, _reviews, _by_kind = artifact_meta.replay(
        "pl1001", "ipd", events, records_root=rec, migration_import=True
    )
    assert state.last_seq == 3
    assert state.fields == state_cp.fields
    assert state.fields["scope_result"] == "exceeded"
    assert state.fields["out_of_scope_paths"] == expected_oos
    assert state.fields["last_history_day"] == "2026-11-02"
    assert meta["status"] == "executed"

    # Without describer or explicit short_description, short_description is omitted.
    _id2, _t2, events_no_desc, _m2 = m0001_convert.build_record_log(
        plan_path, rec, repo_root=repo, migration_at=fixed_at
    )
    assert "short_description" not in events_no_desc[0]["fields"]


def test_path_history_renamed_plan_records_checkpoint_old_then_rename_new(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify renamed legacy record gets checkpoint(old_rel), rename(new_rel), then legacy."""
    repo = _init_repo(tmp_path, monkeypatch, name="path_hist")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "executed").mkdir(parents=True)
    old_rel = ".aw/records/plans/executed/20261101-0900-01-rename-me.ipd.md"
    (repo / old_rel).write_text(
        "# Legacy Rename Plan\n\n"
        "- Id: rn0001\n"
        "- Status: executed\n"
        "- Set: demo\n"
        "- Date: 2026-11-01\n"
        "- Kind: leaf\n"
        "- Short-Description: Legacy rename plan\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n\n"
        "- 2026-11-01 executed (tester): initial history\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "add unclustered plan")

    res = m0001_metadata_v2.run(repo, apply=True, commit=False)
    assert res["status"] == "applied"
    assert res["conversion"]["by_type"]["ipd"] == 1

    log_path = rec / "meta" / "rn0001.jsonl"
    events = _read_jsonl(log_path)
    assert [e["op"] for e in events] == ["checkpoint", "rename", "legacy"]
    assert [e["seq"] for e in events] == [0, 1, 2]
    assert [e["append"] for e in events] == [0, 0, 0]

    old_rec_rel = "plans/executed/20261101-0900-01-rename-me.ipd.md"
    new_rec_rel = "plans/executed/20261101-demo-01-rn0001-rename-me.ipd.md"
    assert (rec / new_rec_rel).is_file()
    assert not (rec / old_rec_rel).exists()

    assert events[0]["path"] == old_rec_rel
    assert events[1]["path"] == new_rec_rel
    assert events[1]["verb"] == "rename"
    assert events[1]["actor"] == {"tool": "aw migrate metadata"}

    state, _ev, _rev, _bk = artifact_meta.replay(
        "rn0001", "ipd", events, records_root=rec, migration_import=True
    )
    assert state.path == new_rec_rel


def test_clock_ac19_filename_date_created_day_and_last_history_day(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify filename_date != created_day separation, missing Date -> None, and last_history_day."""
    repo = _init_repo(tmp_path, monkeypatch, name="clock")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)
    (rec / "specs" / "approved").mkdir(parents=True)

    # Plan where local-clock filename date differs from - Date:, with newest-first history.
    p1 = rec / "plans" / "pending" / "20261014-demo-01-ck0001-clock-diff.ipd.md"
    p1.write_text(
        "# Clock Diff\n\n"
        "- Id: ck0001\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n"
        "- Date: 2026-10-15\n"
        "- Kind: leaf\n"
        "- Item-Dependencies: none\n\n"
        "## Workflow history\n\n"
        "- 2026-10-20 approved (human): newest top entry\n"
        "- 2026-10-18 reviewed (reviewer): older second entry\n",
        encoding="utf-8",
    )
    # Spec without - Date:: filename_date populated, created_day must remain None/absent.
    s1 = rec / "specs" / "approved" / "20261014-demo-01-ck0002-no-date.spec.md"
    s1.write_text(
        "# No Date Spec\n\n"
        "- Id: ck0002\n"
        "- Status: approved\n"
        "- Set: demo\n"
        "- Order: 1\n\n"
        "## Workflow history\n\n"
        "- 2026-10-19 approved (human): approved\n",
        encoding="utf-8",
    )

    _, _, ev_p1, _ = m0001_convert.build_record_log(p1, rec, repo_root=repo)
    _, _, ev_s1, _ = m0001_convert.build_record_log(s1, rec, repo_root=repo)

    st_p1, _, _, _ = artifact_meta.replay(
        "ck0001", "ipd", ev_p1, records_root=rec, migration_import=True
    )
    assert st_p1.filename_date == "2026-10-14"
    assert st_p1.fields["filename_date"] == "2026-10-14"
    assert st_p1.fields["created_day"] == "2026-10-15"
    hb = attention_contract.history_block(p1.read_text(encoding="utf-8"))
    expected_hist = attention_contract.newest_history_record(hb.records)
    assert expected_hist is not None
    assert (
        st_p1.fields["last_history_day"]
        == expected_hist.lstrip("- ")[:10]
        == "2026-10-20"
    )

    st_s1, _, _, _ = artifact_meta.replay(
        "ck0002", "spec", ev_s1, records_root=rec, migration_import=True
    )
    assert st_s1.filename_date == "2026-10-14"
    assert st_s1.fields.get("created_day") is None
    assert st_s1.fields["last_history_day"] == "2026-10-19"


def test_fields_plans_ipd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify every legacy plan/IPD field maps to its 4.2/4.5c log field or body section."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_ipd")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)

    p_listed = (
        rec / "plans" / "pending" / "20261105-metastore-02-pl2001-full-ipd.ipd.md"
    )
    p_listed.write_text(
        "# Full IPD\n\n"
        "- Id: pl2001\n"
        "- Status: to-review\n"
        "- Set: metastore\n"
        "- Order: 2\n"
        "- Date: 2026-11-05\n"
        "- Kind: leaf\n"
        "- Work-Kind: feature\n"
        "- Priority: high\n"
        "- Readiness: ready\n"
        "- Approval: pending\n"
        "- Coverage: covered (by self)\n"
        "- Coverage-Fingerprint: fp123abc\n"
        "- Coverage-Checked: 2026-11-05\n"
        "- Review-Depth: standard\n"
        "- Pipeline: quick\n"
        "- Attended: no\n"
        "- Item-Dependencies: executed:pl0000, state:spec:approved:sp0001\n"
        "- Blocks-Release: rl0001\n"
        "- From-Backlog: bk0001\n"
        "- From-Spec: sp0001\n"
        "- From-Plan: pl0000\n"
        "- Supersedes: pl0099\n"
        "- Scope-Paths:\n"
        "  - agent_workflows/a.py\n"
        "  - tests/test_a.py\n"
        "- Scope-Exceeded: docs/b.md (extra edit)\n"
        "- Author: Test Agent\n"
        "- Highest E allocated: E-05\n"
        "- Short-Description: Full plan fixture\n"
        "- Concern: Handle multi-line\n"
        "  concern prose carefully.\n"
        "- Motivation: Improve test clarity\n"
        "- Note: Historical note kept in body\n"
        "- Origin: Split from parent\n"
        "- Self-note: Author reminder\n"
        "- Supersedes-Note: Replaces older draft\n"
        "- Scope: Core module only\n"
        "- Summary: Detailed plan summary\n"
        "- Relation to prior work: Builds on sp0001\n\n"
        "## Execution Checklist\n\n- [ ] E-01\n",
        encoding="utf-8",
    )

    p_unres = rec / "plans" / "pending" / "20261105-metastore-03-pl2002-unres.ipd.md"
    p_unres.write_text(
        "# Unresolved Dep Plan\n\n"
        "- Id: pl2002\n"
        "- Status: draft\n"
        "- Set: metastore\n"
        "- Item-Dependencies: unresolved\n",
        encoding="utf-8",
    )

    p_absent = rec / "plans" / "pending" / "20261105-metastore-04-pl2003-absent.ipd.md"
    p_absent.write_text(
        "# Absent Dep Plan\n\n"
        "- Id: pl2003\n"
        "- Status: draft\n"
        "- Set: metastore\n",
        encoding="utf-8",
    )

    summary = m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    assert summary["by_type"]["ipd"] == 3

    ev1 = _read_jsonl(rec / "meta" / "pl2001.jsonl")
    st1, _, _, _ = artifact_meta.replay(
        "pl2001", "ipd", ev1, records_root=rec, migration_import=True
    )
    f1 = st1.fields
    assert f1["set"] == "metastore"
    assert f1["order"] == 2
    assert f1["created_day"] == "2026-11-05"
    assert f1["filename_date"] == "2026-11-05"
    assert f1["plan_role"] == "leaf"
    assert f1["work_kind"] == "feature"
    assert f1["priority"] == "high"
    assert f1["readiness"] == "ready"
    assert f1["approval"] == "pending"
    assert f1["coverage"] == "covered (by self)"
    assert f1["coverage_fingerprint"] == "fp123abc"
    assert f1["coverage_checked"] == "2026-11-05"
    assert f1["review_depth"] == "standard"
    assert f1["pipeline"] == "quick"
    assert f1["attended"] == "no"
    assert f1["dependency_declaration"] == "listed"
    assert len(f1["item_dependencies"]) == 2
    assert sorted(d["target_id6"] for d in f1["item_dependencies"]) == [
        "pl0000",
        "sp0001",
    ]
    assert f1["blocks_release"] == "rl0001"
    assert f1["from_backlog"] == "bk0001"
    assert f1["from_spec"] == "sp0001"
    assert f1["from_plan"] == "pl0000"
    assert f1["supersedes"] == "pl0099"
    assert f1["scope_paths"] == ["agent_workflows/a.py", "tests/test_a.py"]
    assert f1["scope_result"] == "exceeded"
    assert f1["out_of_scope_paths"] == [{"path": "docs/b.md", "reason": "extra edit"}]
    assert f1["author"] == "Test Agent"
    assert f1["highest_e_allocated"] == "E-05"
    assert f1["short_description"] == "Full plan fixture"

    rewritten1 = p_listed.read_text(encoding="utf-8")
    for sec in (
        "## Concern",
        "## Motivation",
        "## Note",
        "## Origin",
        "## Self-note",
        "## Supersedes-Note",
        "## Scope",
        "## Summary",
        "## Relation to prior work",
    ):
        assert sec in rewritten1
    assert "- Note:" not in rewritten1
    assert "- Plan-Role:" not in rewritten1

    ev2 = _read_jsonl(rec / "meta" / "pl2002.jsonl")
    st2, _, _, _ = artifact_meta.replay(
        "pl2002", "ipd", ev2, records_root=rec, migration_import=True
    )
    assert st2.fields["dependency_declaration"] == "unresolved"

    ev3 = _read_jsonl(rec / "meta" / "pl2003.jsonl")
    st3, _, _, _ = artifact_meta.replay(
        "pl2003", "ipd", ev3, records_root=rec, migration_import=True
    )
    assert st3.fields["dependency_declaration"] == "absent"


def test_fields_backlog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify backlog item 4.2/4.5c field destinations and body sections."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_bk")
    rec = repo / ".aw" / "records"
    (rec / "backlog" / "done").mkdir(parents=True)

    bk_path = (
        rec / "backlog" / "done" / "20261103-metastore-01-bk1001-sample-item.backlog.md"
    )
    bk_path.write_text(
        "# Backlog Sample\n\n"
        "- Id: bk1001\n"
        "- Status: done\n"
        "- Set: metastore\n"
        "- Priority: high\n"
        "- Work-Kind: bug\n"
        "- Close-Evidence: commit abc123\n"
        "- Release-Exempt-Kind: internal-tooling\n"
        "- Release-Exempt-Ref: docs/exempt.md\n"
        "- Gate-Kind: spec\n"
        "- Gate-Ref: sp0001\n"
        "- Gate-Summary: gated on sp0001\n"
        "- Blocks-Release: rl0001\n"
        "- Graduated-To: pl0001, pl0002\n"
        "- Summary: Backlog summary moved to body\n"
        "- Scope: Limited to CLI layer\n\n"
        "## Workflow history\n\n"
        "- 2026-11-03 done (tester): verified\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    ev = _read_jsonl(rec / "meta" / "bk1001.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "bk1001", "backlog", ev, records_root=rec, migration_import=True
    )
    f = st.fields
    assert st.id6 == "bk1001"
    assert st.status == "done"
    assert f["set"] == "metastore"
    assert f["priority"] == "high"
    assert f["work_kind"] == "bug"
    assert f["close_evidence"] == "commit abc123"
    assert f["release_exempt_kind"] == "internal-tooling"
    assert f["release_exempt_ref"] == "docs/exempt.md"
    assert f["gate_kind"] == "spec"
    assert f["gate_ref"] == "sp0001"
    assert f["gate_summary"] == "gated on sp0001"
    assert f["blocks_release"] == "rl0001"
    assert f["graduated_to"] == ["pl0001", "pl0002"]

    text = bk_path.read_text(encoding="utf-8")
    assert "## Summary\n\nBacklog summary moved to body\n" in text
    assert "## Scope\n\nLimited to CLI layer\n" in text
    assert "## Workflow history" not in text


def test_fields_releases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify release 4.2/4.5c field destinations and Summary body section."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_rel")
    rec = repo / ".aw" / "records"
    (rec / "releases" / "planned").mkdir(parents=True)

    rl_path = (
        rec / "releases" / "planned" / "20261104-v2rel-01-rl1001-release-two.release.md"
    )
    rl_path.write_text(
        "# Release 0.2.0\n\n"
        "- Id: rl1001\n"
        "- Status: planned\n"
        "- Set: v2rel\n"
        "- Order: 1\n"
        "- Version: v0.2.0\n"
        "- Summary: Release summary text\n\n"
        "## Workflow history\n\n"
        "- 2026-11-04 planned (human): scoped\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    ev = _read_jsonl(rec / "meta" / "rl1001.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "rl1001", "release", ev, records_root=rec, migration_import=True
    )
    assert st.id6 == "rl1001"
    assert st.status == "planned"
    assert st.fields["set"] == "v2rel"
    assert st.fields["order"] == 1
    assert st.fields["version"] == "v0.2.0"

    text = rl_path.read_text(encoding="utf-8")
    assert "## Summary\n\nRelease summary text\n" in text
    assert "## Workflow history" not in text


def test_fields_specs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify spec 4.2/4.5c log fields and legacy body section destinations."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_spec")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "approved").mkdir(parents=True)

    sp_path = (
        rec / "specs" / "approved" / "20261001-metastore-01-sp1001-spec-fields.spec.md"
    )
    sp_path.write_text(
        "# Spec Fields Test\n\n"
        "- Id: sp1001\n"
        "- Status: approved\n"
        "- Date: 2026-10-01\n"
        "- Set: metastore\n"
        "- Order: 1\n"
        "- Work-Kind: feature\n"
        "- Priority: medium\n"
        "- Blocks-Release: rl1001\n"
        "- From-Backlog: bk1001\n"
        "- From-Spec: sp0009\n"
        "- Supersedes: sp0002\n"
        "- Gate-Kind: pr\n"
        "- Gate-Ref: pr-42\n"
        "- Gate-Summary: wait on pr-42\n"
        "- Author: Spec Author\n"
        "- Canonical: yes\n"
        "- Constrained-by: sp0001\n"
        "- Evidence: verified in suite\n"
        "- Extends: sp0003\n"
        "- From-Plan: pl1001\n"
        "- Graduated-To: pl1002\n"
        "- Implemented-by: agent_workflows/x.py\n"
        "- Motivation: Why this spec exists\n"
        "- Origin: Initial architecture memo\n"
        "- Parent: sp0000\n"
        "- Related: sp0004\n"
        "- Sources: docs/arch.md\n"
        "- Scope: Spec boundary\n"
        "- Summary: Spec summary\n\n"
        "## Details\n\nBody text.\n\n"
        "## Workflow history\n\n"
        "- 2026-10-01 approved (human): approved\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    ev = _read_jsonl(rec / "meta" / "sp1001.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "sp1001", "spec", ev, records_root=rec, migration_import=True
    )
    f = st.fields
    assert f["created_day"] == "2026-10-01"
    assert f["set"] == "metastore"
    assert f["order"] == 1
    assert f["work_kind"] == "feature"
    assert f["priority"] == "medium"
    assert f["blocks_release"] == "rl1001"
    assert f["from_backlog"] == "bk1001"
    assert f["from_spec"] == "sp0009"
    assert f["supersedes"] == "sp0002"
    assert f["gate_kind"] == "pr"
    assert f["gate_ref"] == "pr-42"
    assert f["gate_summary"] == "wait on pr-42"
    assert f["author"] == "Spec Author"
    assert f["canonical"] == "yes"

    text = sp_path.read_text(encoding="utf-8")
    for heading in (
        "## Constrained-by",
        "## Evidence",
        "## Extends",
        "## From-Plan",
        "## Graduated-To",
        "## Implemented-by",
        "## Motivation",
        "## Origin",
        "## Parent",
        "## Related",
        "## Sources",
        "## Scope",
        "## Summary",
    ):
        assert heading in text


def test_fields_prompts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify staged prompt comment fields, colon substrings, and body bullets preservation."""
    repo = _init_repo(tmp_path, monkeypatch, name="fields_prompt")
    rec = repo / ".aw" / "records"
    (rec / "prompts" / "retired").mkdir(parents=True)

    pr_path = (
        rec / "prompts" / "retired" / "20260910-metastore-01-pr2001-audit-prompt.md"
    )
    pr_path.write_text(
        "<!-- aw-prompt: Id: pr2001 | Status: retired | Kind: review | Created: 2026-09-10 | "
        "Set: metastore | Author: Tester | Targets: agent_workflows/a.py; tests/b.py | "
        "Concerns: hygiene: stale paths; tiers: marker parity | Results: docs/out.md | "
        "Results-go-to: .aw/records/research/out.md | Grounding: sp0001 | "
        "Goal: audit modules | Reviews-spec: sp0001 | Basis: code read | Relation: follow-up "
        ". Agent instructions: follow carefully. -->\n\n"
        "# Prompt Body Title\n\n"
        "- Executor: codex\n"
        "- Core: true\n"
        "- Thorough: yes\n"
        "- Purpose: evaluate state\n\n"
        "## Workflow history\n\n"
        "- 2026-09-12 retired (human): finished\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    ev = _read_jsonl(rec / "meta" / "pr2001.jsonl")
    st, _, _, _ = artifact_meta.replay(
        "pr2001", "prompt", ev, records_root=rec, migration_import=True
    )
    f = st.fields
    assert st.status == "retired"
    assert f["prompt_kind"] == "review"
    assert f["created_day"] == "2026-09-10"
    assert f["set"] == "metastore"
    assert f["author"] == "Tester"
    assert f["targets"] == ["agent_workflows/a.py; tests/b.py"]
    assert f["concerns"] == ["hygiene: stale paths; tiers: marker parity"]
    assert f["results"] == ["docs/out.md"]
    assert f["results_go_to"] == [".aw/records/research/out.md"]
    assert f["grounding"] == "sp0001"
    assert f["goal"] == "audit modules"
    assert f["reviews_spec"] == "sp0001"
    assert f["basis"] == "code read"
    assert f["relation"] == "follow-up"

    rewritten = pr_path.read_text(encoding="utf-8")
    first_line = rewritten.splitlines()[0]
    assert first_line.startswith("<!-- aw-managed-prompt:")
    assert "<!-- aw-prompt:" not in rewritten
    assert "Agent instructions" not in first_line
    assert "- Executor: codex" in rewritten
    assert "- Core: true" in rewritten
    assert "- Thorough: yes" in rewritten
    assert "- Purpose: evaluate state" in rewritten
    assert "## Workflow history" not in rewritten


# --------------------------------------------------------------------------------------
# V-02: mirrors, banners, AC-40 cases 1 & 2, fenced-history guard, and exclusions
# --------------------------------------------------------------------------------------


def test_mirror_and_banner_all_standard_types_plus_fenced_history_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify 4.1 YAML mirror, aw-managed banner, and fenced ## Workflow history preservation."""
    repo = _init_repo(tmp_path, monkeypatch, name="mirrors")
    rec = repo / ".aw" / "records"
    (rec / "plans" / "pending").mkdir(parents=True)
    (rec / "backlog" / "open").mkdir(parents=True)
    (rec / "releases" / "planned").mkdir(parents=True)
    (rec / "specs" / "draft").mkdir(parents=True)

    plan_path = rec / "plans" / "pending" / "20261106-demo-01-mr0001-fenced.ipd.md"
    plan_path.write_text(
        "# Plan With Fenced History\n\n"
        "- Id: mr0001\n"
        "- Status: to-review\n"
        "- Set: demo\n"
        "- Summary: Real plan summary.\n\n"
        "## Evidence Block\n\n"
        "```markdown\n"
        "## Workflow history\n\n"
        "- 2026-10-01 note (example): fenced sample must remain\n"
        "```\n\n"
        "## Workflow history\n\n"
        "- 2026-11-06 to-review (author): ready\n",
        encoding="utf-8",
    )
    (rec / "backlog" / "open" / "20261106-demo-01-mr0002-item.backlog.md").write_text(
        "# Item\n\n- Id: mr0002\n- Status: open\n- Priority: low\n- Work-Kind: chore\n",
        encoding="utf-8",
    )
    (
        rec / "releases" / "planned" / "20261106-demo-01-mr0003-rel.release.md"
    ).write_text(
        "# Rel\n\n- Id: mr0003\n- Status: planned\n- Set: demo\n- Order: 1\n",
        encoding="utf-8",
    )
    (rec / "specs" / "draft" / "20261106-demo-01-mr0004-spec.spec.md").write_text(
        "# Spec\n\n- Id: mr0004\n- Status: draft\n- Set: demo\n",
        encoding="utf-8",
    )

    m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)

    expected = [
        (plan_path, "mr0001", "to-review"),
        (
            rec / "backlog" / "open" / "20261106-demo-01-mr0002-item.backlog.md",
            "mr0002",
            "open",
        ),
        (
            rec / "releases" / "planned" / "20261106-demo-01-mr0003-rel.release.md",
            "mr0003",
            "planned",
        ),
        (
            rec / "specs" / "draft" / "20261106-demo-01-mr0004-spec.spec.md",
            "mr0004",
            "draft",
        ),
    ]
    for path, id6, status in expected:
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert lines[0] == "---"
        assert lines[1] == f"id: {id6}"
        assert lines[2] == f"status: {status}"
        assert lines[3] == "---"
        assert lines[4].startswith("<!-- aw-managed:")
        parsed = artifact_meta.parse_artifact_mirror(text)
        assert parsed == {"id": id6, "status": status}

    plan_text = plan_path.read_text(encoding="utf-8")
    assert "## Summary\n\nReal plan summary.\n" in plan_text
    assert "- 2026-10-01 note (example): fenced sample must remain" in plan_text
    assert "- 2026-11-06 to-review (author): ready" not in plan_text


def test_prompt_ac40_case1_commented_and_case2_commentless(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify AC-40 case 1 (aw-prompt comment) and case 2 (commentless D177 filename prompt)."""
    repo = _init_repo(tmp_path, monkeypatch, name="ac40")
    rec = repo / ".aw" / "records"
    (rec / "prompts" / "pending").mkdir(parents=True)
    (rec / "prompts" / "retired").mkdir(parents=True)

    # Case 1: existing <!-- aw-prompt: ... --> comment
    case1 = rec / "prompts" / "pending" / "20261010-metastore-01-ac40c1-with-comment.md"
    case1.write_text(
        "<!-- aw-prompt: Id: ac40c1 | Status: pending | Kind: research | Created: 2026-10-10 . Do not skip instructions. -->\n\n"
        "# Prompt Case 1\n\nPrompt body line.\n\n"
        "## Workflow history\n\n- 2026-10-10 pending (author): created\n",
        encoding="utf-8",
    )

    # Case 2: commentless D177 staged prompt (no aw-prompt comment anywhere)
    case2 = rec / "prompts" / "retired" / "20260711-metastore-01-ac40c2-d177-gpt54.md"
    case2.write_text(
        "# Commentless Prompt\n\n"
        "Direct prompt text without HTML comment.\n\n"
        "## Workflow history\n\n- 2026-07-11 retired (human): legacy completed\n",
        encoding="utf-8",
    )

    res = m0001_convert.convert_records(repo, records_root=rec, repo_root=repo)
    assert res["by_type"]["prompt"] == 2

    for path, id6, exp_status in (
        (case1, "ac40c1", "pending"),
        (case2, "ac40c2", "retired"),
    ):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert lines[0].startswith("<!-- aw-managed-prompt:")
        assert not any(ln.strip() == "---" for ln in lines[:6])
        assert "Do not skip instructions" not in lines[0]
        assert "<!-- aw-prompt:" not in text
        assert "## Workflow history" not in text
        parsed = artifact_meta.parse_staged_prompt_mirror(text)
        assert parsed == {"id": id6, "status": exp_status}
        ev = _read_jsonl(rec / "meta" / f"{id6}.jsonl")
        st, _, _, _ = artifact_meta.replay(
            id6, "prompt", ev, records_root=rec, migration_import=True
        )
        assert st.id6 == id6
        assert st.status == exp_status

    ev1 = _read_jsonl(rec / "meta" / "ac40c1.jsonl")
    st1, _, _, _ = artifact_meta.replay(
        "ac40c1", "prompt", ev1, records_root=rec, migration_import=True
    )
    assert st1.fields["prompt_kind"] == "research"
    assert st1.fields["set"] == "metastore"


def test_excluded_comms_data_readmes_non_5_trees_and_six_templates_byte_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify full v2 pipeline leaves comms, .data/, READMEs, and 6 templates untouched while converting all 8 record types."""
    repo = _init_repo(tmp_path, monkeypatch, name="excluded")
    rec = repo / ".aw" / "records"

    # Seed convertible records across types plus protected excluded files.
    (rec / "plans" / "pending").mkdir(parents=True)
    plan = rec / "plans" / "pending" / "20261106-demo-01-ex0001-real.ipd.md"
    plan.write_text(
        "# Real Plan\n\n- Id: ex0001\n- Status: approved\n- Set: demo\n- Short-Description: Real plan\n",
        encoding="utf-8",
    )
    (rec / "research" / "findings").mkdir(parents=True)
    (
        rec / "research" / "findings" / "20261106-demo-01-rs0001-study.research.md"
    ).write_text(
        "---\nid: rs0001\nstatus: complete\nshort-description: Study\n---\n\n# Research\n",
        encoding="utf-8",
    )
    (rec / "walkthroughs").mkdir(parents=True)
    (rec / "walkthroughs" / "20261106-demo-01-wt0001-walkthrough.md").write_text(
        "# Walkthrough\n\n- Id: wt0001\n- Short-Description: Walkthrough\n",
        encoding="utf-8",
    )
    (rec / "roadmaps").mkdir(parents=True)
    (rec / "roadmaps" / "20261106-demo-01-rm0001-roadmap.md").write_text(
        "# Roadmap\n\n- Id: rm0001\n- Short-Description: Roadmap\n",
        encoding="utf-8",
    )
    (rec / "reviews").mkdir(parents=True)
    (rec / "reviews" / "20261106-demo-01-ex0001-real.review.md").write_text(
        "# Review\n\n- Subject-Id: ex0001\n- Subject-Type: ipd\n- Verdict: PASS\n\n## Round 1\n",
        encoding="utf-8",
    )

    protected: Dict[Path, bytes] = {
        rec / "README.md": b"# Records README\nDo not modify.\n",
        rec / "plans" / "README.md": b"# Plans README\n",
        rec
        / "comms"
        / "shared"
        / "inbox"
        / "20261106-msg.md": b"# Comms Msg\nUntouched.\n",
        rec / ".data" / "cache.md": b"# Data File\nRaw bytes.\n",
        rec / "plans" / ".data" / "notes.md": b"# Nested Data\nRaw bytes.\n",
        # Six protected templates: 4 in prompt-library + 2 named templates.
        rec
        / "prompts"
        / "prompt-library"
        / "tpl1.md": b"<!-- aw-prompt: Id: tp0001 -->\nTemplate 1\n",
        rec / "prompts" / "prompt-library" / "tpl2.md": b"Template 2\n",
        rec / "prompts" / "prompt-library" / "tpl3.md": b"Template 3\n",
        rec / "prompts" / "prompt-library" / "tpl4.md": b"Template 4\n",
        rec
        / "prompts"
        / "conformance-results-template.md": b"# Conformance Template\n",
        rec
        / "research"
        / "20260712-0156-14-chatgpt-modular-report-template.md": b"# ChatGPT Report Template\n",
    }
    for p, content in protected.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    _git(repo, "add", ".aw/.gitignore", ".aw/records")
    _git(repo, "commit", "-m", "add plan plus protected trees and templates")

    before_hashes = {
        p.relative_to(repo).as_posix(): hashlib.sha256(content).hexdigest()
        for p, content in protected.items()
    }

    res = m0001_metadata_v2.run(repo, apply=True, commit=False)
    assert res["status"] == "applied"
    assert res["conversion"]["by_type"]["ipd"] == 1
    assert res["conversion"]["by_type"]["research"] == 1
    assert res["conversion"]["by_type"]["walkthrough"] == 1
    assert res["conversion"]["by_type"]["roadmap"] == 1
    assert res["conversion"]["by_type"]["review"] == 1
    assert (rec / "meta" / "ex0001.jsonl").is_file()
    assert (rec / "meta" / "rs0001.jsonl").is_file()
    assert (rec / "meta" / "wt0001.jsonl").is_file()
    assert (rec / "meta" / "rm0001.jsonl").is_file()

    for p, orig_bytes in protected.items():
        rel = p.relative_to(repo).as_posix()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == before_hashes[rel], rel
        assert p.read_bytes() == orig_bytes, rel

    # Dry-run after conversion doesn't alter repo bytes either.
    snap = _snapshot_hashes(repo)
    assert (
        snap[".aw/records/comms/shared/inbox/20261106-msg.md"]
        == before_hashes[".aw/records/comms/shared/inbox/20261106-msg.md"]
    )
