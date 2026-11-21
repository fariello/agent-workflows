"""Cache-parity behavioral tests for moved readers (spec `4sd62s` AC-1a, AC-8, AC-18; IPD `ffceq0` E-12 / V-12).

Exercises `aw find` (all types), `aw attention --format json`, `aw check meta --agent`,
`aw check all --agent`, and `aw ipd lint` across cold, warm, deleted, and corrupt SQLite cache
states, external edits outside `artifact_meta`, unparseable record replacements, the legacy
`.agents/` record root, and a companion-records fixture. Calls the real `aw` CLI and never reads
production source code.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import patch

import pytest

from agent_workflows import artifact_meta, cli, meta_cli

pytestmark = pytest.mark.core

_ALL_FIND_TYPES = (
    "plans",
    "specs",
    "backlog",
    "research",
    "prompts",
    "releases",
    "walkthroughs",
)
_COMMANDS = ("find", "attention", "check_meta", "check_all", "ipd_lint")
_CACHE_STATES = ("cold", "warm", "deleted", "corrupt")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _run_cli(argv: List[str]) -> Tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            rc = cli.main(argv)
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
    return rc, out.getvalue(), err.getvalue()


def _cache_files(state_root: Path) -> List[Path]:
    db = state_root / "index.db"
    return [
        db,
        Path(f"{db}-wal"),
        Path(f"{db}-shm"),
        Path(f"{db}-journal"),
    ]


def _delete_cache(state_root: Path) -> None:
    for p in _cache_files(state_root):
        if p.exists():
            p.unlink()


def _corrupt_cache(state_root: Path) -> None:
    _delete_cache(state_root)
    state_root.mkdir(parents=True, exist_ok=True)
    # Deterministic non-SQLite garbage bytes so corruption recovery is reproducible.
    garbage = bytes((i * 73 + 19) % 256 for i in range(4096))
    (state_root / "index.db").write_bytes(garbage)


def _plan_text(status: str = "draft") -> str:
    return (
        "# IPD: Clean Parity Plan\n\n"
        "- Date: 2026-11-01\n"
        "- Kind: child\n"
        "- Concern: Verify cache parity across reader commands.\n"
        "- Scope: Exercise cache states on a minimal fixture.\n"
        "- Scope-Paths: tests/test_readers_cache_parity.py\n"
        "- Item-Dependencies: none\n"
        f"- Status: {status}\n"
        "- Work-Kind: chore\n"
        "- Priority: low\n"
        "- Set: cset\n"
        "- Order: 01\n"
        "- Highest E allocated: 01\n"
        "- Author: tester\n"
        "- Review-Depth: simple\n"
        "- Id: pln001\n\n"
        "## Workflow history\n"
        f"- 2026-11-01 {status} (tester): fixture state\n\n"
        "## Goal\n\n"
        "Verify cache parity across all five moved reader surfaces.\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "- [ ] E-01 Run parity command\n"
        "  - Depends on: none\n"
        "  - Expected outcome: command outputs match across cache states\n"
        "  - Execution state: pending\n\n"
        "## Project conventions discovered (Step 0)\n\n"
        "- Core tests run via pytest.\n\n"
        "## Findings\n\n"
        "- None.\n\n"
        "## Proposed changes (ordered, validatable)\n\n"
        "1. Run parity assertions.\n\n"
        "## Deferred / out of scope (with reason)\n\n"
        "None.\n\n"
        "## Scope check\n\n"
        "- Over-scope: none.\n"
        "- Under-scope: none.\n\n"
        "## Required tests / validation\n\n"
        "Run pytest on the cache parity suite.\n\n"
        "## Spec / documentation sync\n\n"
        "N/A.\n\n"
        "## Open questions\n\n"
        "None.\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: paste pytest output showing every case passed\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n\n"
        "## Approval and execution gate\n\n"
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n"
    )


def _build_corpus_repo(tmp_path: Path, name: str = "corpus") -> Tuple[Path, Path]:
    repo = (tmp_path / name).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".aw/state/\n", encoding="utf-8")

    wf_dir = repo / ".aw" / "system" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    (wf_dir / "index.md").write_text("# Workflows\n", encoding="utf-8")

    cfg_dir = repo / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "placements": {
                    "system": "target-tracked",
                    "config_project": "target-tracked",
                    "config_local": "target-ignored",
                    "state_durable": "target-tracked",
                    "state_runtime": "target-ignored",
                    "records": "target-tracked",
                },
                "records_backend": "repository",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    recs = repo / ".aw" / "records"
    for sub in (
        "plans/pending",
        "specs/approved",
        "backlog/open",
        "research",
        "prompts/pending",
        "releases",
        "walkthroughs",
    ):
        (recs / sub).mkdir(parents=True, exist_ok=True)

    plan_p = recs / "plans" / "pending" / "20261101-cset-01-pln001-clean-plan.ipd.md"
    plan_p.write_text(_plan_text("draft"), encoding="utf-8")

    (
        recs / "specs" / "approved" / "20261101-spc001-01-spc001-clean-spec.spec.md"
    ).write_text(
        "# Spec: Clean Spec\n\n"
        "- Date: 2026-11-01\n"
        "- Id: spc001\n"
        "- Status: approved\n"
        "- Set: spc001\n"
        "- Order: 01\n\n"
        "## Workflow history\n"
        "- 2026-11-01 approved (by-human): approved\n\n"
        "## Overview\n\nClean spec body.\n",
        encoding="utf-8",
    )

    (
        recs / "backlog" / "open" / "20261101-bklset-01-bkl001-clean-item.backlog.md"
    ).write_text(
        "- Id: bkl001\n"
        "- Status: open\n"
        "- Set: bklset\n"
        "- Priority: low\n"
        "- Work-Kind: chore\n"
        "- Summary: Clean backlog item\n\n"
        "## Workflow history\n"
        "- 2026-11-01 created (aw backlog): Clean backlog item\n\n"
        "### Problem Statement\n\nClean backlog body.\n",
        encoding="utf-8",
    )

    (
        recs
        / "research"
        / "20261101-rset-01-res001-clean-study-claude.research-report.md"
    ).write_text(
        "---\n"
        "id: res001\n"
        "created: 20261101\n"
        "set: rset\n"
        "order: 01\n"
        "topic: [cache]\n"
        "model: claude\n"
        "kind: research-report\n"
        "status: reference\n"
        "outcome: informational\n"
        "summary: Clean study\n"
        "consumed-by: []\n"
        "---\n"
        "# Clean Study\n\nStudy body.\n",
        encoding="utf-8",
    )

    (
        recs
        / "prompts"
        / "pending"
        / "20261101-pset-01-prm001-clean-prompt.research-prompt.md"
    ).write_text(
        "<!-- aw-prompt: Kind: research | Id: prm001 | Set: pset | Status: pending | Created: 2026-11-01 -->\n"
        "# Clean Prompt\n\nPrompt body.\n",
        encoding="utf-8",
    )

    (recs / "releases" / "20261101-rel001-01-rel001-v1-0-0.release.md").write_text(
        "# Release: 1.0.0\n\n"
        "- Date: 2026-11-01\n"
        "- Id: rel001\n"
        "- Version: 1.0.0\n"
        "- Status: planned\n"
        "- Set: rel001 (1.0.0)\n"
        "- Order: 01\n\n"
        "## Summary\n\nRelease body.\n",
        encoding="utf-8",
    )

    (
        recs
        / "walkthroughs"
        / "20261101-wset-01-wlk001-clean-walkthrough.walkthrough.md"
    ).write_text(
        "# Walkthrough: Clean Walkthrough\n\n"
        "- Date: 2026-11-01\n"
        "- Id: wlk001\n"
        "- Set: wset\n"
        "- Order: 01\n\n"
        "## Summary\n\nWalkthrough body.\n",
        encoding="utf-8",
    )

    return repo, plan_p


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def _invoke_surface(repo: Path, plan_p: Path, command: str) -> Tuple[int, str]:
    if command == "find":
        chunks: List[str] = []
        rc_final = 0
        for rec_type in _ALL_FIND_TYPES:
            rc, out, err = _run_cli(["find", rec_type, "--agent", "--dir", str(repo)])
            assert err == "", f"aw find {rec_type} wrote to stderr: {err!r}"
            if rc != 0:
                rc_final = rc
            chunks.append(f"=== {rec_type} (rc={rc}) ===\n{_normalize(out)}")
        return rc_final, "".join(chunks)

    if command == "attention":
        rc, out, err = _run_cli(
            ["attention", "--all", "--format", "json", "--dir", str(repo)]
        )
        assert err == "", f"aw attention wrote to stderr: {err!r}"
        return rc, _normalize(out)

    if command == "check_meta":
        rc, out, err = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
        assert err == "", f"aw check meta wrote to stderr: {err!r}"
        return rc, _normalize(out)

    if command == "check_all":
        rc, out, err = _run_cli(["check", "all", "--agent", "--dir", str(repo)])
        assert err == "", f"aw check all wrote to stderr: {err!r}"
        return rc, _normalize(out)

    if command == "ipd_lint":
        prev_cwd = os.getcwd()
        os.chdir(repo)
        try:
            rc, out, err = _run_cli(["ipd", "lint", "--agent"])
        finally:
            os.chdir(prev_cwd)
        assert err == "", f"aw ipd lint wrote to stderr: {err!r}"
        return rc, _normalize(out)

    raise ValueError(f"Unknown command: {command}")


# --------------------------------------------------------------------------------------------------
# 5 commands x 4 cache states = 20 cache-parity cases (AC-1a, AC-8)
# --------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _cold_references(
    tmp_path_factory: pytest.TempPathFactory,
) -> Dict[str, Tuple[int, str]]:
    """Compute the cold-cache reference `(exit_code, output)` once per command."""
    refs: Dict[str, Tuple[int, str]] = {}
    base = tmp_path_factory.mktemp("parity_refs")
    for cmd in _COMMANDS:
        ref_repo, ref_plan = _build_corpus_repo(base, f"ref_{cmd}")
        assert not (ref_repo / ".aw" / "state" / "index.db").exists()
        ref_rc, ref_out = _invoke_surface(ref_repo, ref_plan, cmd)
        assert ref_out.strip() != ""
        refs[cmd] = (ref_rc, ref_out)
    return refs


@pytest.mark.parametrize("command", _COMMANDS)
@pytest.mark.parametrize("cache_state", _CACHE_STATES)
def test_command_cache_state_parity(
    tmp_path: Path,
    _cold_references: Dict[str, Tuple[int, str]],
    command: str,
    cache_state: str,
) -> None:
    ref_rc, ref_out = _cold_references[command]

    repo, plan_p = _build_corpus_repo(tmp_path, f"target_{command}_{cache_state}")
    state_dir = repo / ".aw" / "state"
    db_path = state_dir / "index.db"

    if cache_state == "cold":
        assert not db_path.exists()
    elif cache_state == "warm":
        rc_rb, _, err_rb = _run_cli(["index", "rebuild", "--agent", "--dir", str(repo)])
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        _invoke_surface(repo, plan_p, command)
        assert db_path.is_file()
    elif cache_state == "deleted":
        rc_rb, _, err_rb = _run_cli(["index", "rebuild", "--agent", "--dir", str(repo)])
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        _delete_cache(state_dir)
        assert not db_path.exists()
    elif cache_state == "corrupt":
        rc_rb, _, err_rb = _run_cli(["index", "rebuild", "--agent", "--dir", str(repo)])
        assert rc_rb == 0 and err_rb == ""
        assert db_path.is_file()
        _corrupt_cache(state_dir)
        assert db_path.is_file()

    got_rc, got_out = _invoke_surface(repo, plan_p, command)
    assert got_rc == ref_rc, (
        f"{command} ({cache_state}) rc={got_rc} != cold ref rc={ref_rc}\n"
        f"got:\n{got_out}\nref:\n{ref_out}"
    )
    assert (
        got_out == ref_out
    ), f"{command} ({cache_state}) output diverged from cold reference"
    if cache_state in ("warm", "corrupt"):
        assert (
            db_path.is_file()
        ), f"{command} ({cache_state}) did not leave a usable on-disk index.db"


# --------------------------------------------------------------------------------------------------
# External edit outside artifact_meta (simulating git pull)
# --------------------------------------------------------------------------------------------------


def test_external_status_edit_visible_without_rebuild(tmp_path: Path) -> None:
    repo, plan_p = _build_corpus_repo(tmp_path, "ext_edit")

    # Populate and warm the on-disk cache, then verify initial status is draft.
    rc_rb, _, err_rb = _run_cli(["index", "rebuild", "--agent", "--dir", str(repo)])
    assert rc_rb == 0 and err_rb == ""
    assert (repo / ".aw" / "state" / "index.db").is_file()

    rc_f0, out_f0, _ = _run_cli(
        ["find", "plans", "draft", "--paths", "--dir", str(repo)]
    )
    assert rc_f0 == 0
    assert "pln001" in out_f0

    rc_a0, out_a0, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a0 == 0
    data0 = json.loads(out_a0)
    plan_item0 = next(it for it in data0["items"] if it["id"] == "pln001")
    assert plan_item0["native_status"] == "draft"

    # Edit `- Status:` directly on disk outside artifact_meta (as git pull does).
    plan_p.write_text(_plan_text("to-review"), encoding="utf-8")

    # Next aw find and aw attention must reflect the change with no rebuild.
    rc_f1, out_f1, _ = _run_cli(
        ["find", "plans", "to-review", "--paths", "--dir", str(repo)]
    )
    assert rc_f1 == 0
    assert "pln001" in out_f1

    rc_f_old, out_f_old, _ = _run_cli(
        ["find", "plans", "draft", "--paths", "--dir", str(repo)]
    )
    assert rc_f_old == 0
    assert "pln001" not in out_f_old

    rc_a1, out_a1, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a1 == 0
    data1 = json.loads(out_a1)
    plan_item1 = next(it for it in data1["items"] if it["id"] == "pln001")
    assert plan_item1["native_status"] == "to-review"


# --------------------------------------------------------------------------------------------------
# Invalid / unparseable record replacement reported, not omitted and not served stale
# --------------------------------------------------------------------------------------------------


def test_invalid_replacement_reported_not_omitted_or_stale(tmp_path: Path) -> None:
    repo, plan_p = _build_corpus_repo(tmp_path, "invalid_replace")
    ctx = meta_cli.meta_context(repo)

    # Warm the cache with the valid draft plan.
    rc_a0, out_a0, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a0 == 0
    assert json.loads(out_a0)["valid"] is True

    # Case 1: replace record with invalid UTF-8 bytes.
    plan_p.write_bytes(b"\xff\xfe\x00\x00unparseable-record")
    q1 = artifact_meta.query(project_context=ctx)
    assert "pln001" in q1.incomplete
    assert all(st.id6 != "pln001" for st in q1)

    rc_a1, out_a1, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a1 == 1
    att1 = json.loads(out_a1)
    assert att1["valid"] is False
    assert all(it.get("id") != "pln001" for it in att1["items"])
    assert any(
        "pln001" in v.get("location", "") and v.get("rule") == "attention.unreadable"
        for v in att1["violations"]
    )

    rc_m1, out_m1, _ = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
    assert rc_m1 == 1
    meta_items1 = [json.loads(ln) for ln in out_m1.splitlines() if ln.strip()]
    assert any(
        rec.get("kind") == "item"
        and rec.get("rule") == "meta.invalid-record"
        and "pln001" in rec.get("location", "")
        for rec in meta_items1
    )

    # Case 2: restore valid markdown and introduce a corrupt metadata log.
    plan_p.write_text(_plan_text("draft"), encoding="utf-8")
    meta_dir = repo / ".aw" / "records" / "meta"
    meta_dir.mkdir(parents=True, exist_ok=True)
    (meta_dir / "pln001.jsonl").write_text("{corrupt json line\n", encoding="utf-8")

    q2 = artifact_meta.query(project_context=ctx)
    assert "pln001" in q2.incomplete
    assert all(st.id6 != "pln001" for st in q2)

    rc_a2, out_a2, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a2 == 1
    att2 = json.loads(out_a2)
    assert att2["valid"] is False
    pln_rows2 = [it for it in att2["items"] if it.get("id") == "pln001"]
    assert not pln_rows2 or pln_rows2[0]["native_status"] != "draft"
    assert any(
        "pln001" in v.get("location", "") or "pln001" in v.get("detail", "")
        for v in att2["violations"]
    )

    rc_m2, out_m2, _ = _run_cli(["check", "meta", "--agent", "--dir", str(repo)])
    assert rc_m2 == 1
    meta_items2 = [json.loads(ln) for ln in out_m2.splitlines() if ln.strip()]
    assert any(
        rec.get("kind") == "item"
        and rec.get("rule") == "meta.invalid-log"
        and "pln001.jsonl" in rec.get("location", "")
        for rec in meta_items2
    )


# --------------------------------------------------------------------------------------------------
# Legacy .agents/ record root parity
# --------------------------------------------------------------------------------------------------


def test_legacy_agents_record_root_visible_in_find_and_attention(
    tmp_path: Path,
) -> None:
    repo = (tmp_path / "legacy_agents").resolve()
    repo.mkdir()
    _git(repo, "init", "-q")

    plan_rel = ".agents/plans/pending/20261101-legset-01-leg001-legacy-plan.ipd.md"
    plan_p = repo / plan_rel
    plan_p.parent.mkdir(parents=True, exist_ok=True)
    plan_p.write_text(
        "# IPD: Legacy Root Plan\n\n"
        "- Date: 2026-11-01\n"
        "- Id: leg001\n"
        "- Status: approved\n"
        "- Set: legset\n"
        "- Order: 01\n\n"
        "## Goal\n\nVerify legacy .agents/ record root stays visible.\n",
        encoding="utf-8",
    )

    # Cold run
    rc_f_cold, out_f_cold, err_f_cold = _run_cli(
        ["find", "plans", "leg001", "--paths", "--dir", str(repo)]
    )
    assert rc_f_cold == 0 and err_f_cold == ""
    assert out_f_cold.strip() == plan_rel

    rc_a_cold, out_a_cold, err_a_cold = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a_cold == 0 and err_a_cold == ""
    att_cold = json.loads(out_a_cold)
    assert att_cold["valid"] is True
    assert len(att_cold["items"]) == 1
    assert att_cold["items"][0]["id"] == "leg001"
    assert att_cold["items"][0]["path"] == plan_rel
    assert att_cold["items"][0]["native_status"] == "approved"
    assert att_cold["items"][0]["attention_class"] == "ready"

    # Warm run must be byte-identical
    rc_f_warm, out_f_warm, _ = _run_cli(
        ["find", "plans", "leg001", "--paths", "--dir", str(repo)]
    )
    assert rc_f_warm == 0
    assert out_f_warm == out_f_cold

    rc_a_warm, out_a_warm, _ = _run_cli(
        ["attention", "--all", "--format", "json", "--dir", str(repo)]
    )
    assert rc_a_warm == 0
    assert out_a_warm == out_a_cold


# --------------------------------------------------------------------------------------------------
# Companion-repository fixture (AC-18 contribution)
# --------------------------------------------------------------------------------------------------


def test_companion_fixture_find_cache_parity(tmp_path: Path) -> None:
    target = (tmp_path / "target_repo").resolve()
    companion = (tmp_path / "target_repo.aw").resolve()
    target.mkdir()
    companion.mkdir()
    _git(target, "init", "-q")
    _git(companion, "init", "-q")

    cfg_dir = target / ".aw" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "public-target-private-companion",
                "records_backend": "companion",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (cfg_dir / "local.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "companion_dir": str(companion),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    comp_plan = (
        companion
        / "records"
        / "plans"
        / "pending"
        / "20261101-cmpset-01-cmp001-companion-plan.ipd.md"
    )
    comp_plan.parent.mkdir(parents=True, exist_ok=True)
    comp_plan.write_text(
        "# IPD: Companion Plan\n\n"
        "- Date: 2026-11-01\n"
        "- Id: cmp001\n"
        "- Status: approved\n"
        "- Set: cmpset\n"
        "- Order: 01\n\n"
        "## Goal\n\nCompanion records lookup parity.\n",
        encoding="utf-8",
    )

    state_dir = target / ".aw" / "state"
    rc_cold, out_cold, err_cold = _run_cli(
        ["find", "plans", "cmp001", "--agent", "--dir", str(target)]
    )
    assert rc_cold == 0 and err_cold == ""
    records_cold = [json.loads(ln) for ln in out_cold.splitlines() if ln.strip()]
    assert any(
        r.get("kind") == "item" and "cmp001" in r.get("path", "") for r in records_cold
    )

    # Warm run
    rc_warm, out_warm, _ = _run_cli(
        ["find", "plans", "cmp001", "--agent", "--dir", str(target)]
    )
    assert rc_warm == 0
    assert out_warm == out_cold

    # Deleted cache run
    _delete_cache(state_dir)
    rc_del, out_del, _ = _run_cli(
        ["find", "plans", "cmp001", "--agent", "--dir", str(target)]
    )
    assert rc_del == 0
    assert out_del == out_cold
