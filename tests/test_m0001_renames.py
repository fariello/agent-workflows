"""Outcome tests for m0001 step-3 rename map, citation plan, and scratch apply.

IPD dky26u (E-01..E-04 / V-01..V-04). Spec 4sd62s Section 5.2 step 3, OQ-26,
OQ-27, OQ-28, and AC-41 cases (2) and (3).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest.mock
from pathlib import Path
from typing import Dict, List

import pytest

from agent_workflows import (
    artifact_core,
    artifact_naming,
    layout_migration,
)
from agent_workflows.migrations import m0001_metadata_v2, m0001_renames

pytestmark = pytest.mark.core


_DEFAULT_GITIGNORE = (
    "/state/\n"
    "/config/local.json\n"
    "records/history.jsonl\n"
    "records/plans/INDEX.json\n"
    "records/runs/\n"
    "# spec 20260817-2124-01 reference\n"
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
    """Capture relative POSIX path -> SHA-256 hex digest outside .git/."""
    out: Dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
    return out


# --------------------------------------------------------------------------------------
# V-01: classify_name, build_rename_map, journal reuse, and refusals (a), (b), (c)
# --------------------------------------------------------------------------------------


def test_classify_name_legacy_6letter_slug_vs_clustered_4digit_set() -> None:
    """AC-41 case (2): 6-letter slug word is legacy; clustered 4-digit Set id is not."""
    assert (
        m0001_renames.classify_name(
            "20260712-1033-01-assess-bugs-and-tests-walkthrough.walkthrough.md"
        )
        == "legacy"
    )
    assert (
        m0001_renames.classify_name(
            "20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md"
        )
        == "legacy"
    )
    assert (
        m0001_renames.classify_name(
            "20260730-2152-01-agents-artifact-organization.spec.md"
        )
        == "legacy"
    )
    assert (
        m0001_renames.classify_name("20261101-1234-01-ab12cd-some-plan.ipd.md")
        == "clustered"
    )
    assert (
        m0001_renames.classify_name("20261101-9999-01-abcdef-some-plan.ipd.md")
        == "clustered"
    )
    assert m0001_renames.classify_name("README.md") == "other"


def test_build_rename_map_mints_reuses_journal_and_honors_logged_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mints id6 for id-less records, reuses journal id6, and uses logged Order."""
    repo = _init_repo(tmp_path, monkeypatch, name="map_rules")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "implemented").mkdir(parents=True)
    (rec / "walkthroughs").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "comms" / "inbox").mkdir(parents=True)
    (rec / "prompt-library").mkdir(parents=True)
    (rec / "research" / "plan-review" / "pkg.data").mkdir(parents=True)

    # Id-less spec whose slug starts with a 6-letter word ('agents')
    (rec / "specs" / "implemented" / "20260730-2152-01-agents-org.spec.md").write_text(
        "# Spec\n\n- Status: implemented\n", encoding="utf-8"
    )

    # Id-less walkthrough
    (
        rec / "walkthroughs" / "20260712-1033-01-assess-bugs-walkthrough.walkthrough.md"
    ).write_text("# Walkthrough\n", encoding="utf-8")

    # Existing-Id plan with Set and logged Order: 17 (filename NN is 01)
    (
        rec
        / "plans"
        / "executed"
        / "20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md"
    ).write_text(
        "# IPD: Wvlk\n\n- Id: wvlk84\n- Set: awphysical\n- Order: 17\n- Status: executed\n",
        encoding="utf-8",
    )

    # Existing-Id plan with no Set (defaults set to id6) and Order: 0
    (rec / "plans" / "executed" / "20260808-0004-00-adopter-orch.ipd.md").write_text(
        "# IPD: Orch\n\n- Id: lus9ou\n- Set: plans-adopter (plans adopter)\n- Order: 0\n- Status: executed\n",
        encoding="utf-8",
    )
    (rec / "plans" / "executed" / "20260815-2156-01-standalone.ipd.md").write_text(
        "# IPD: Standalone\n\n- Id: 4o5lt9\n- Status: executed\n",
        encoding="utf-8",
    )

    # OQ-02 exclusions that must never be mapped
    (rec / "comms" / "inbox" / "20260801-1200-01-msg.md").write_text(
        "msg\n", encoding="utf-8"
    )
    (rec / "prompt-library" / "20260801-1200-01-tmpl.prompt.md").write_text(
        "tmpl\n", encoding="utf-8"
    )
    (
        rec
        / "research"
        / "plan-review"
        / "20260712-0156-14-chatgpt-modular-report-template.md"
    ).write_text("template\n", encoding="utf-8")
    (
        rec / "research" / "plan-review" / "pkg.data" / "20260801-1200-01-data.md"
    ).write_text("data\n", encoding="utf-8")

    # Read-only preview (journal=None) writes nothing
    preview = m0001_renames.build_rename_map(repo, journal=None)
    assert len(preview) == 5
    assert not (repo / ".aw" / "state" / "durable" / "migrations" / "m0001").exists()

    wvlk = preview.get_by_id6("wvlk84")
    assert wvlk is not None
    assert wvlk.minted is False
    assert (
        wvlk.new_name
        == "20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md"
    )

    lus = preview.get_by_id6("lus9ou")
    assert lus is not None
    assert lus.new_name == "20260808-plans-adopter-00-lus9ou-adopter-orch.ipd.md"

    solo = preview.get_by_id6("4o5lt9")
    assert solo is not None
    assert solo.new_name == "20260815-4o5lt9-01-4o5lt9-standalone.ipd.md"

    # Journaled dry-run calls reuse the exact minted ids
    journal_path = tmp_path / "journal.json"
    map1 = m0001_renames.build_rename_map(repo, journal=journal_path)
    assert journal_path.is_file()
    saved = json.loads(journal_path.read_text(encoding="utf-8"))
    assert len(saved["minted_ids"]) == 2

    map2 = m0001_renames.build_rename_map(repo, journal=journal_path)
    assert map1.path_map == map2.path_map
    assert [e.id6 for e in map1] == [e.id6 for e in map2]


def test_build_rename_map_refusals_and_unmapped_duplicates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuses collision with unmapped plan, duplicate filename, duplicate id6, and unknown facet; reports unmapped duplicates."""
    # (a) Collision with unmapped plan + unmapped duplicate pair reported without refusal
    repo_a = _init_repo(tmp_path, monkeypatch, name="refusal_a")
    plans_a = repo_a / ".aw" / "records" / "plans" / "executed"
    plans_a.mkdir(parents=True)
    (plans_a / "20260817-awphysical-01-cwjnj0-existing.ipd.md").write_text(
        "- Id: cwjnj0\n- Set: awphysical\n- Order: 1\n- Status: executed\n",
        encoding="utf-8",
    )
    # Two unmapped plans already sharing (dup, 2) must be reported, not refused
    (plans_a / "20260818-dup-02-du0001-first.ipd.md").write_text(
        "- Id: du0001\n- Set: dup\n- Order: 2\n- Status: executed\n",
        encoding="utf-8",
    )
    (plans_a / "20260819-dup-02-du0002-second.ipd.md").write_text(
        "- Id: du0002\n- Set: dup\n- Order: 2\n- Status: superseded\n",
        encoding="utf-8",
    )
    clean_map = m0001_renames.build_rename_map(repo_a)
    assert len(clean_map.unmapped_plan_duplicates) == 1
    assert clean_map.unmapped_plan_duplicates[0][0] == ("dup", 2)

    # Adding legacy plan landing on (awphysical, 1) must refuse naming both paths
    (plans_a / "20260817-1357-01-assess-collision.ipd.md").write_text(
        "- Id: wvlk84\n- Set: awphysical\n- Order: 1\n- Status: executed\n",
        encoding="utf-8",
    )
    with pytest.raises(m0001_renames.RenameRefusalError) as exc_a:
        m0001_renames.build_rename_map(repo_a)
    assert "20260817-1357-01-assess-collision.ipd.md" in str(exc_a.value)
    assert "20260817-awphysical-01-cwjnj0-existing.ipd.md" in str(exc_a.value)

    # (b) Duplicate legacy filenames in different dirs
    repo_b = _init_repo(tmp_path, monkeypatch, name="refusal_b")
    (repo_b / ".aw" / "records" / "specs" / "implemented").mkdir(parents=True)
    (repo_b / ".aw" / "records" / "specs" / "superseded").mkdir(parents=True)
    (
        repo_b
        / ".aw"
        / "records"
        / "specs"
        / "implemented"
        / "20260801-1200-01-same.spec.md"
    ).write_text("# S1\n", encoding="utf-8")
    (
        repo_b
        / ".aw"
        / "records"
        / "specs"
        / "superseded"
        / "20260801-1200-01-same.spec.md"
    ).write_text("# S2\n", encoding="utf-8")
    with pytest.raises(m0001_renames.RenameRefusalError) as exc_b:
        m0001_renames.build_rename_map(repo_b)
    assert "specs/implemented/20260801-1200-01-same.spec.md" in str(exc_b.value)
    assert "specs/superseded/20260801-1200-01-same.spec.md" in str(exc_b.value)

    # (c) Reused/minted id6 colliding with another record's id6
    repo_c = _init_repo(tmp_path, monkeypatch, name="refusal_c")
    specs_c = repo_c / ".aw" / "records" / "specs" / "implemented"
    specs_c.mkdir(parents=True)
    (specs_c / "20260801-demo-01-xx1111-clustered.spec.md").write_text(
        "- Id: xx1111\n- Status: implemented\n", encoding="utf-8"
    )
    (specs_c / "20260802-1200-01-legacy-one.spec.md").write_text(
        "- Status: implemented\n", encoding="utf-8"
    )
    bad_journal = {
        "minted_ids": {
            "specs/implemented/20260802-1200-01-legacy-one.spec.md": "xx1111"
        }
    }
    with pytest.raises(m0001_renames.RenameRefusalError) as exc_c:
        m0001_renames.build_rename_map(repo_c, journal=bad_journal)
    assert "xx1111" in str(exc_c.value)
    assert "20260802-1200-01-legacy-one.spec.md" in str(exc_c.value)
    assert "20260801-demo-01-xx1111-clustered.spec.md" in str(exc_c.value)

    # Unknown facet refuses naming the file
    repo_f = _init_repo(tmp_path, monkeypatch, name="refusal_facet")
    specs_f = repo_f / ".aw" / "records" / "specs" / "implemented"
    specs_f.mkdir(parents=True)
    (specs_f / "20260802-1200-01-weird.bogus.md").write_text(
        "# Weird\n", encoding="utf-8"
    )
    with pytest.raises(m0001_renames.RenameRefusalError) as exc_f:
        m0001_renames.build_rename_map(repo_f)
    assert "20260802-1200-01-weird.bogus.md" in str(exc_f.value)


def test_build_rename_map_seeds_global_id6s_once_and_reuses_journal_with_zero_scans(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seeds global_id6s once across four uncached mints, tracks collisions in memory, and skips scanning on journal reuse."""
    repo = _init_repo(tmp_path, monkeypatch, name="single_global_scan")
    rec = repo / ".aw" / "records"
    specs_dir = rec / "specs" / "implemented"
    research_dir = rec / "research"
    specs_dir.mkdir(parents=True)
    research_dir.mkdir(parents=True)

    for idx, slug in enumerate(("alpha", "beta", "gamma", "delta"), start=1):
        (specs_dir / f"2026080{idx}-1200-01-{slug}.spec.md").write_text(
            f"# Spec {slug}\n\n- Status: implemented\n", encoding="utf-8"
        )

    # A clustered research document quoting `- Id: qut111` in its body so only
    # global_id6s (unbounded body scan) observes `qut111`.
    (research_dir / "20260805-demo-01-rs0001-quoting.reference-research.md").write_text(
        "# Research\n\n- Id: rs0001\n- Status: reviewed\n\n"
        "```markdown\n- Id: qut111\n```\n",
        encoding="utf-8",
    )

    seen_pools: List[frozenset[str]] = []
    orig_generate = artifact_core.generate_id6

    def _recording_generate(existing, _rng=None):
        seen_pools.append(frozenset(existing))
        return orig_generate(existing, _rng)

    journal: Dict[str, object] = {}
    with (
        unittest.mock.patch.object(
            artifact_core, "global_id6s", wraps=artifact_core.global_id6s
        ) as mock_global,
        unittest.mock.patch.object(
            artifact_core, "generate_id6", wraps=_recording_generate
        ) as mock_gen,
    ):
        map1 = m0001_renames.build_rename_map(repo, journal=journal)

        assert mock_global.call_count == 1
        assert mock_gen.call_count == 4
        assert len(map1.entries) == 4
        minted_ids = [entry.id6 for entry in map1.entries]
        assert len(set(minted_ids)) == 4
        assert len(seen_pools) == 4
        for idx, (pool_snap, minted_id) in enumerate(zip(seen_pools, minted_ids)):
            assert "qut111" in pool_snap
            assert set(minted_ids[:idx]).issubset(pool_snap)
            assert minted_id not in pool_snap

        # Second call reusing journal["minted_ids"] performs zero global_id6s scans
        # and zero generate_id6 calls, returning the identical RenameMap.
        mock_global.reset_mock()
        mock_gen.reset_mock()
        map2 = m0001_renames.build_rename_map(repo, journal=journal)
        assert mock_global.call_count == 0
        assert mock_gen.call_count == 0
        assert map2 == map1


# --------------------------------------------------------------------------------------
# V-02: plan_citation_rewrites guard, gitignored scratch, protected spans, report
# --------------------------------------------------------------------------------------


def test_plan_citation_rewrites_guard_and_gitignored_scratch_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refuses external records placement; scans scratch copy inside gitignored dir."""
    # External placement refusal
    ext_records = tmp_path / "external_records"
    (ext_records / "specs").mkdir(parents=True)
    scratch_bad = tmp_path / "scratch_bad"
    (scratch_bad / ".aw" / "config").mkdir(parents=True)
    (scratch_bad / ".aw" / "records").mkdir(parents=True)
    (scratch_bad / ".aw" / "config" / "project.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "preset": "private-target",
                "role": "target",
                "records_backend": "companion",
                "placements": {
                    "records": "companion-tracked",
                },
                "custom_paths": {"records": str(ext_records)},
            }
        ),
        encoding="utf-8",
    )
    # Also test symlink escape from .aw/records -> ext_records
    scratch_sym = tmp_path / "scratch_sym"
    (scratch_sym / ".aw").mkdir(parents=True)
    (scratch_sym / ".aw" / "records").symlink_to(ext_records)
    with pytest.raises(m0001_renames.RenameRefusalError, match="outside"):
        m0001_renames.plan_citation_rewrites(
            scratch_sym,
            {"20260801-1200-01-a.spec.md": "20260801-aa1111-01-aa1111-a.spec.md"},
        )

    # Scratch copy under gitignored .aw/state/ inside a real git init fixture
    repo = _init_repo(tmp_path, monkeypatch, name="gitignored_scratch")
    _git(repo, "add", ".aw/.gitignore")
    _git(repo, "commit", "-m", "init")

    scratch_in_state = (
        repo / ".aw" / "state" / "durable" / "migrations" / "m0001" / "scratch" / "repo"
    )
    (scratch_in_state / ".aw" / "records" / "specs" / "implemented").mkdir(parents=True)
    (scratch_in_state / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    (
        scratch_in_state
        / ".aw"
        / "records"
        / "specs"
        / "implemented"
        / "20260801-1200-01-old-spec.spec.md"
    ).write_text("# Spec\n", encoding="utf-8")
    (
        scratch_in_state
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261101-demo-01-pl0001-citing.ipd.md"
    ).write_text(
        "# IPD\n\n- Id: pl0001\n\nSee 20260801-1200-01-old-spec.spec.md.\n",
        encoding="utf-8",
    )
    rmap = m0001_renames.build_rename_map(scratch_in_state)
    plan = m0001_renames.plan_citation_rewrites(scratch_in_state, rmap)
    assert plan.total_substituted == 1
    assert plan.location_counts == {"records/plans": 1}


def test_plan_citation_rewrites_protects_spans_exemptions_fences_and_sums_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Protects history, review verdicts, exemptions, and fences; location counts match total."""
    repo = _init_repo(tmp_path, monkeypatch, name="plan_spans")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "implemented").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / "agent_workflows").mkdir(parents=True)
    (repo / "docs").mkdir(parents=True)

    old_spec = "20260808-0004-01-artifact-organization.spec.md"
    (rec / "specs" / "implemented" / old_spec).write_text(
        "# Spec\n\n- Status: implemented\n", encoding="utf-8"
    )
    # Exempted legacy names
    ex_plan = "20260808-0004-06-migrate-existing-plans.ipd.md"
    (rec / "plans" / "executed" / ex_plan).write_text(
        "- Id: 7qx7ys\n- Set: plans-adopter\n- Order: 6\n- Status: executed\n",
        encoding="utf-8",
    )
    ex_wvlk = "20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md"
    (rec / "plans" / "executed" / ex_wvlk).write_text(
        "- Id: wvlk84\n- Set: awphysical\n- Order: 17\n- Status: executed\n",
        encoding="utf-8",
    )

    # Plan with body citation, history-section citation, and fenced-code citation
    (
        rec / "plans" / "executed" / "20261101-demo-01-pl0001-body-and-hist.ipd.md"
    ).write_text(
        "# Plan\n\n"
        "- Id: pl0001\n\n"
        f"Body cites {old_spec} and `20260808-0004-01`.\n\n"
        "```sh\n"
        f"cat {old_spec}\n"
        "```\n\n"
        "## Workflow history\n\n"
        f"- 2026-11-01 note (alice): legacy {old_spec}\n",
        encoding="utf-8",
    )

    # Review with body citation and - Verdict: line citation
    (rec / "reviews" / "20261101-demo-01-pl0001-rev.review.md").write_text(
        "# Review\n\n"
        f"- Verdict: APPROVED against {old_spec}\n\n"
        f"Body prose also mentions {old_spec}.\n",
        encoding="utf-8",
    )

    # Exempted test file and check_engine file
    (repo / "tests" / "test_plans_rename_selectors.py").write_text(
        f'p = "{ex_plan}"\n# non-exempt: {old_spec}\n',
        encoding="utf-8",
    )
    (repo / "agent_workflows" / "check_engine.py").write_text(
        f"# misparse `20260817-1357-01-assess-...` and `{ex_wvlk}`\n"
        f"# real spec: {old_spec}\n",
        encoding="utf-8",
    )
    (repo / "docs" / "guide.md").write_text(
        f"Read {old_spec} and [pin](https://example.invalid/o/r/blob/0123456789abcdef/{old_spec}).\n",
        encoding="utf-8",
    )

    rmap = m0001_renames.build_rename_map(repo)
    plan = m0001_renames.plan_citation_rewrites(repo, rmap)

    assert plan.warnings == ()
    assert sum(plan.location_counts.values()) == plan.total_substituted
    assert (
        plan.location_counts["records/plans"] == 2
    )  # full name + short handle in body
    assert plan.location_counts["records/reviews"] == 1
    assert plan.location_counts["tests"] == 1
    assert plan.location_counts["agent_workflows"] == 1
    assert plan.location_counts["docs"] == 1
    assert plan.total_substituted == 6

    reasons = {occ.reason for occ in plan.unchanged_occurrences}
    assert {
        "history-section",
        "verdict-line",
        "exemption",
        "fenced-or-permalink",
    }.issubset(reasons)


# --------------------------------------------------------------------------------------
# V-04: apply_step3, byte-identical protected spans, idempotency, resume, m0001_metadata_v2
# --------------------------------------------------------------------------------------


def test_apply_step3_protected_bytes_moves_idempotency_and_resume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-41 case (3), byte-identical protected spans, second call no-op, and journal resume."""
    repo = _init_repo(tmp_path, monkeypatch, name="apply_step3")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "implemented").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (rec / "reviews").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / "TODO.md").write_text(
        "See 20260808-0004-01-artifact-org.spec.md for details.\n",
        encoding="utf-8",
    )

    old_spec = "20260808-0004-01-artifact-org.spec.md"
    spec_file = rec / "specs" / "implemented" / old_spec
    spec_hist = "## Workflow history\n\n- 2026-08-08 implemented (alice): cites 20260808-0004-01-artifact-org.spec.md\n"
    spec_file.write_bytes(
        ("# Spec\n\n- Status: implemented\n\n" + spec_hist).encode("utf-8")
    )

    ex_plan = "20260808-0004-06-migrate-existing-plans.ipd.md"
    (rec / "plans" / "executed" / ex_plan).write_bytes(
        b"- Id: 7qx7ys\n- Set: plans-adopter\n- Order: 6\n- Status: executed\n"
    )

    plan_file = rec / "plans" / "executed" / "20261101-demo-01-pl0001-citer.ipd.md"
    hist_block = (
        "## Workflow history\n\n"
        f"- 2026-11-01 executed (bob): cites {old_spec} and 20260808-0004-01\n"
    )
    fence_block = f"```sh\necho {old_spec}\n```\n"
    plan_file.write_bytes(
        (
            "# Plan\n\n- Id: pl0001\n\n"
            f"Body cites {old_spec}.\n\n" + fence_block + "\n" + hist_block
        ).encode("utf-8")
    )

    rev_file = rec / "reviews" / "20261101-demo-01-pl0001-rev.review.md"
    verdict_line = f"- Verdict: APPROVED ({old_spec})\n"
    rev_file.write_bytes(
        ("# Review\n\n" + verdict_line + f"\nBody: {old_spec}\n").encode("utf-8")
    )

    ex_file = repo / "tests" / "test_plans_rename_selectors.py"
    ex_file.write_text(f'p = "{ex_plan}"\n', encoding="utf-8")

    # Capture protected bytes prior to apply
    orig_spec_hist_bytes = spec_hist.encode("utf-8")
    orig_plan_hist_bytes = hist_block.encode("utf-8")
    orig_fence_bytes = fence_block.encode("utf-8")
    orig_verdict_bytes = verdict_line.encode("utf-8")
    orig_ex_bytes = ex_file.read_bytes()

    rmap = m0001_renames.build_rename_map(repo)
    cplan = m0001_renames.plan_citation_rewrites(repo, rmap)
    journal_path = tmp_path / "step3_journal.json"
    m0001_renames.apply_step3(repo, rmap, cplan, journal_path)

    # AC-41 case (3): no mapped file matches _LEGACY_TIMESTAMP_RE; new paths exist, old do not
    for entry in rmap:
        assert not (rec / entry.old_rel).exists()
        assert (rec / entry.new_rel).is_file()
        assert (
            artifact_naming._LEGACY_TIMESTAMP_RE.match(Path(entry.new_rel).name) is None
        )

    # Protected spans remain byte-identical
    plan_after = plan_file.read_bytes()
    assert orig_plan_hist_bytes in plan_after
    assert orig_fence_bytes in plan_after
    assert old_spec.encode("utf-8") not in plan_after.split(b"```sh")[0]
    assert orig_verdict_bytes in rev_file.read_bytes()
    assert old_spec not in rev_file.read_text(encoding="utf-8").splitlines()[-1]
    assert ex_file.read_bytes() == orig_ex_bytes
    new_spec_entry = rmap.get_by_id6(
        rmap.entries[0].id6
        if rmap.entries[0].old_name == old_spec
        else rmap.entries[1].id6
    )
    assert new_spec_entry is not None
    assert orig_spec_hist_bytes in (rec / new_spec_entry.new_rel).read_bytes()
    assert new_spec_entry.new_name in (repo / "TODO.md").read_text(encoding="utf-8")

    # Idempotent second call changes no file
    snap_before_second = _snapshot_hashes(repo)
    m0001_renames.apply_step3(repo, rmap, cplan, journal=None)
    assert _snapshot_hashes(repo) == snap_before_second

    # Interrupted call resumes from journal to identical state
    repo_res = _init_repo(tmp_path, monkeypatch, name="resume_step3")
    rec_res = repo_res / ".aw" / "records"
    (rec_res / "specs" / "implemented").mkdir(parents=True)
    (rec_res / "plans" / "executed").mkdir(parents=True)
    (rec_res / "specs" / "implemented" / old_spec).write_text(
        "# Spec\n\n- Status: implemented\n", encoding="utf-8"
    )
    (rec_res / "plans" / "executed" / ex_plan).write_text(
        "- Id: 7qx7ys\n- Set: plans-adopter\n- Order: 6\n- Status: executed\n",
        encoding="utf-8",
    )
    (repo_res / "TODO.md").write_text(f"Ref {old_spec}\n", encoding="utf-8")

    rmap_res = m0001_renames.build_rename_map(repo_res)
    cplan_res = m0001_renames.plan_citation_rewrites(repo_res, rmap_res)
    # Seed journal simulating interruption after TODO.md rewrite and first move
    j_res = tmp_path / "resume_journal.json"
    m0001_renames.apply_step3(repo_res, rmap_res, cplan_res, j_res)
    expected_hashes = _snapshot_hashes(repo_res)

    # Now replay on a fresh copy interrupted midway
    repo_int = _init_repo(tmp_path, monkeypatch, name="interrupted_step3")
    rec_int = repo_int / ".aw" / "records"
    (rec_int / "specs" / "implemented").mkdir(parents=True)
    (rec_int / "plans" / "executed").mkdir(parents=True)
    (rec_int / "specs" / "implemented" / old_spec).write_text(
        "# Spec\n\n- Status: implemented\n", encoding="utf-8"
    )
    (rec_int / "plans" / "executed" / ex_plan).write_text(
        "- Id: 7qx7ys\n- Set: plans-adopter\n- Order: 6\n- Status: executed\n",
        encoding="utf-8",
    )
    (repo_int / "TODO.md").write_text(f"Ref {old_spec}\n", encoding="utf-8")

    # Reuse minted id6 from rmap_res so target filename matches expected_hashes
    minted_seed = {e.old_rel: e.id6 for e in rmap_res if e.minted}
    j_int = tmp_path / "int_journal.json"
    j_int.write_text(json.dumps({"minted_ids": minted_seed}), encoding="utf-8")
    rmap_int = m0001_renames.build_rename_map(repo_int, j_int)
    cplan_int = m0001_renames.plan_citation_rewrites(repo_int, rmap_int)

    # Simulate partial completion: TODO.md already rewritten, first file not moved yet
    (repo_int / "TODO.md").write_bytes(
        f"Ref {rmap_int.name_map[old_spec]}\n".encode("utf-8")
    )
    j_state = json.loads(j_int.read_text(encoding="utf-8"))
    j_state["step3_progress"] = {"rewritten_files": ["TODO.md"], "moved_files": []}
    j_int.write_text(json.dumps(j_state), encoding="utf-8")

    m0001_renames.apply_step3(repo_int, rmap_int, cplan_int, j_int)
    assert _snapshot_hashes(repo_int) == expected_hashes


def test_m0001_metadata_v2_step3_wiring_dry_run_apply_rollback_and_missing_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """m0001_metadata_v2 wires step 3 into dry run, apply, rollback, and missing-root check."""
    repo = _init_repo(tmp_path, monkeypatch, name="v2_wiring")
    rec = repo / ".aw" / "records"
    (rec / "specs" / "implemented").mkdir(parents=True)
    (rec / "plans" / "executed").mkdir(parents=True)
    (repo / "docs").mkdir(parents=True)

    old_spec = "20260817-2124-01-records-taxonomy.spec.md"
    (rec / "specs" / "implemented" / old_spec).write_text(
        "# Spec\n\n- Status: implemented\n- Short-Description: Taxonomy spec\n",
        encoding="utf-8",
    )
    (rec / "plans" / "executed" / "20261101-demo-01-pl0001-plan.ipd.md").write_text(
        f"# Plan\n\n- Id: pl0001\n- Short-Description: Plan citing spec\n\nCites {old_spec}.\n\n"
        f"## Workflow history\n\n- 2026-11-01 executed (tester): {old_spec}\n",
        encoding="utf-8",
    )
    (repo / "docs" / "ref.md").write_text(f"Spec {old_spec}.\n", encoding="utf-8")
    (repo / "TODO.md").write_text(f"See {old_spec}.\n", encoding="utf-8")
    _git(repo, "add", ".aw/.gitignore", ".aw/records", "docs", "TODO.md")
    _git(repo, "commit", "-m", "init v2 wiring fixture")

    orig_hashes = _snapshot_hashes(repo)

    # Dry run computes renames & citations in scratch without touching tracked files
    dry = m0001_metadata_v2.run(repo, apply=False)
    assert dry["status"] == "dry_run"
    assert dry["renames"]["entry_count"] == 1
    assert dry["citations"]["total_substituted"] == 4
    assert dry["citations"]["location_counts"] == {
        ".aw": 1,
        "TODO.md": 1,
        "docs": 1,
        "records/plans": 1,
    }
    assert dry["citations"]["unchanged_counts_by_reason"] == {"history-section": 1}
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
    for rel, digest in orig_hashes.items():
        assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == digest

    # Missing scan root in scratch copy refuses cleanly
    scratch_repo = Path(dry["scratch_dir"]) / "repo"
    with pytest.raises(layout_migration.MigrationError, match="missing scan root"):
        (scratch_repo / "TODO.md").unlink()
        m0001_metadata_v2._verify_scratch_scan_roots(
            repo,
            rec,
            scratch_repo,
            m0001_renames.M0001_SCAN_ROOTS,
        )

    # Apply moves renamed file and rewrites citations while keeping history byte-identical
    applied = m0001_metadata_v2.run(repo, apply=True, commit=False)
    assert applied["status"] == "applied"
    old_rel, new_rel = next(iter(applied["rename_map"].items()))
    new_name = Path(new_rel).name
    assert not (rec / old_rel).exists()
    assert (rec / new_rel).is_file()
    assert new_name in (repo / "docs" / "ref.md").read_text(encoding="utf-8")
    assert new_name in (repo / "TODO.md").read_text(encoding="utf-8")
    plan_text = (
        rec / "plans" / "executed" / "20261101-demo-01-pl0001-plan.ipd.md"
    ).read_text(encoding="utf-8")
    assert f"Cites {new_name}." in plan_text
    assert "## Workflow history" not in plan_text
    plan_log_text = (rec / "meta" / "pl0001.jsonl").read_text(encoding="utf-8")
    assert f"- 2026-11-01 executed (tester): {old_spec}" in plan_log_text

    # Rollback restores exact pre-apply bytes across tracked checkout files
    rb = m0001_metadata_v2.rollback(repo)
    assert rb["status"] == "rolled_back"
    assert not (rec / new_rel).exists()
    assert (rec / old_rel).is_file()
    for rel, digest in orig_hashes.items():
        assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == digest
    assert _git(repo, "status", "--porcelain").stdout.strip() == ""
