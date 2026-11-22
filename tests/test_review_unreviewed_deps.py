"""`--review-unreviewed-deps`: a review may start against a `to-review` prerequisite, and is
flagged for re-review when that prerequisite's steps later change (spec 25kzda 2.9, 2026-11-13).

Every test drives real code (the dependency predicate, the cascade, the basis recorder, the
partition CLI) over plan files on disk and asserts on what it returns or prints.
"""

from __future__ import annotations

import argparse
import io
import subprocess
from pathlib import Path

from agent_workflows import partition, review_basis, runner_shared
from tests.record_builder import RecordBuilder


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    return repo


def _plan(
    repo: Path,
    id6: str,
    order: int,
    status: str,
    deps: str = "",
    step: str = "Do it",
    *,
    subdir: str = "pending",
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / subdir
        / f"20261113-rudset-{order:02d}-{id6}-p.ipd.md"
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        RecordBuilder().plan(
            title=id6,
            when="2026-11-13",
            plan_role="child",
            status=status,
            set="rudset",
            order=order,
            id6=id6,
            item_dependencies=deps or "none",
            scope_paths="README.md",
            body=(
                f"## Detailed Implementation Checklist (TODO)\n"
                f"- [ ] E-01 {step}\n- [ ] V-01 Verify it"
            ),
            text_only=True,
        ),
        encoding="utf-8",
    )
    return p


def _edge(id6: str):
    return runner_shared.parse_dependency_token(f"executed:{id6}")


def _state(repo: Path, flag: bool, queue=None):
    return {
        "repo": str(repo),
        "queue": queue or [],
        "options": {"review_unreviewed_deps": flag},
    }


def test_review_accepts_to_review_prerequisite_only_with_flag(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _plan(repo, "aaa001", 1, "to-review")
    review = {"id6": "bbb002", "action": "review"}
    ok, why = runner_shared.edge_satisfied(
        _edge("aaa001"), review, _state(repo, False), {}
    )
    assert not ok and "to-review" in why
    ok, _ = runner_shared.edge_satisfied(
        _edge("aaa001"), review, _state(repo, True), {}
    )
    assert ok


def test_flag_never_relaxes_execute_or_draft(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _plan(repo, "aaa001", 1, "to-review")
    _plan(repo, "ccc003", 3, "draft")
    ok, _ = runner_shared.edge_satisfied(
        _edge("aaa001"), {"id6": "bbb002", "action": "execute"}, _state(repo, True), {}
    )
    assert not ok
    ok, _ = runner_shared.edge_satisfied(
        _edge("ccc003"), {"id6": "bbb002", "action": "review"}, _state(repo, True), {}
    )
    assert not ok


def test_failed_prerequisite_review_does_not_cascade_under_flag(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _plan(repo, "aaa001", 1, "to-review")
    queue = [
        {
            "id6": "aaa001",
            "action": "review",
            "status": "fail-gate",
            "dependencies": [],
        },
        {
            "id6": "bbb002",
            "action": "review",
            "status": "queued",
            "dependencies": ["executed:aaa001"],
        },
    ]
    st = _state(repo, True, queue)
    assert runner_shared.cascade_dependency_blocked(st) == []
    assert queue[1]["status"] == "queued"
    st_strict = _state(repo, False, [dict(q) for q in queue])
    blocked = runner_shared.cascade_dependency_blocked(st_strict)
    assert [b["id6"] for b in blocked] == ["bbb002"]


def test_basis_goes_stale_when_prerequisite_steps_change_and_clears_when_settled(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    pre = _plan(repo, "aaa001", 1, "to-review")
    _plan(repo, "bbb002", 2, "to-review", deps="executed:aaa001")
    item = {"id6": "bbb002", "action": "review", "dependencies": ["executed:aaa001"]}
    targets = review_basis.provisional_targets(repo, item, _state(repo, True))
    assert [t["id6"] for t in targets] == ["aaa001"]
    review_basis.record_basis(
        repo, "bbb002", targets, run_id="run-x", at="2026-11-13T00:00:00Z"
    )

    # Ticking a checkbox or changing only status is not a design change.
    pre.write_text(
        pre.read_text().replace("- [ ] E-01", "- [x] E-01"), encoding="utf-8"
    )
    assert review_basis.stale_bases(repo, prune=False) == []

    # The prerequisite's review rewrites a step: the dependent is now stale.
    pre.write_text(
        pre.read_text().replace("Do it", "Do something else entirely"), encoding="utf-8"
    )
    stale = review_basis.stale_bases(repo)
    assert [(s.consumer, s.target) for s in stale] == [("bbb002", "aaa001")]
    out = io.StringIO()
    lines = review_basis.report_stale_bases(repo, host="oc", stream=out)
    assert "aw oc run --action review bbb002" in out.getvalue() and lines

    # Re-reviewing the dependent against a now-reviewed prerequisite records no provisional basis,
    # which clears the warning.
    _plan(repo, "aaa001", 1, "reviewed", step="Do something else entirely")
    assert review_basis.provisional_targets(repo, item, _state(repo, True)) == []
    review_basis.record_basis(
        repo, "bbb002", [], run_id="run-y", at="2026-11-13T01:00:00Z"
    )
    assert review_basis.stale_bases(repo) == []


def test_unchanged_prerequisite_that_gets_reviewed_prunes_the_record(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    _plan(repo, "aaa001", 1, "to-review")
    item = {"id6": "bbb002", "action": "review", "dependencies": ["executed:aaa001"]}
    targets = review_basis.provisional_targets(repo, item, _state(repo, True))
    path = review_basis.record_basis(repo, "bbb002", targets, run_id="r", at="t")
    assert path is not None and path.is_file()
    _plan(repo, "aaa001", 1, "reviewed")
    assert review_basis.stale_bases(repo) == []
    assert not path.exists()


def test_partition_splits_a_chain_and_emits_the_flag(tmp_path: Path, capsys) -> None:
    repo = _repo(tmp_path)
    # A Set whose orchestrator keeps it in one shard (the metastore shape), with a chain of children.
    rows = []
    prev = ""
    for n in range(1, 7):
        pid = f"ch{n:04d}"
        _plan(repo, pid, n, "to-review", deps=f"executed:{prev}" if prev else "")
        rows.append(f"| {n:02d} | {pid} | child {n} |")
        prev = pid
    orch = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261113-rudset-00-ord000-o.ipd.md"
    )
    orch.write_text(
        RecordBuilder().plan(
            title="orchestrator",
            when="2026-11-13",
            plan_role="orchestrator",
            status="to-review",
            set="rudset",
            order=0,
            id6="ord000",
            scope_paths="README.md",
            body=(
                "## Child IPDs, sequence, and dependencies\n\n"
                "| Order | Id | Summary |\n|---|---|---|\n"
                + "\n".join(rows)
                + "\n\n## Detailed Implementation Checklist (TODO)\n"
                "- [ ] E-01 Run children\n- [ ] V-01 Verify"
            ),
            text_only=True,
        ),
        encoding="utf-8",
    )

    def run(flag: bool, expect_rc: int = 0) -> list[str]:
        args = argparse.Namespace(
            dir=str(repo),
            artifact_type="plans",
            selectors=[],
            shards=3,
            status=["to-review"],
            status_not=[],
            priority=[],
            action="review",
            order_by=None,
            max=None,
            run="oc",
            as_profile=None,
            model=None,
            variant=None,
            json=False,
            agent=False,
            stdin=False,
            allow_partial_sets=False,
            skip_ineligible=False,
            include_active=True,
            with_dependencies=False,
            review_unreviewed_deps=flag,
            fields=None,
        )
        rc = partition.run_partition(args, None)
        out = capsys.readouterr().out
        assert rc == expect_rc, out
        return [ln for ln in out.splitlines() if ln.startswith("aw oc run")]

    # Like metastore mid-review: one member already reviewed, awaiting approval.
    _plan(repo, "ch0001", 1, "reviewed")

    # Without the flag, an already-reviewed member no longer refuses a review batch; the Set is
    # kept in one shard because its chain must be reviewed in order.
    strict = run(False)
    assert len(strict) == 1 and "--review-unreviewed-deps" not in strict[0]
    assert "ch0001" not in strict[0]
    relaxed = run(True)
    assert len(relaxed) == 3
    assert "ch0001" not in " ".join(relaxed)
    assert all(c.endswith("--review-unreviewed-deps") for c in relaxed)


def test_stale_advice_says_the_run_succeeded_and_groups_by_changed_prerequisite() -> (
    None
):
    stale = [
        review_basis.StaleBasis("bbb002", "aaa001", "reviewed", "r", "run-x"),
        review_basis.StaleBasis("ccc003", "aaa001", "reviewed", "r", "run-x"),
        review_basis.StaleBasis("ccc003", "ddd004", "reviewed", "r", "run-x"),
    ]
    text = "\n".join(review_basis.stale_report_lines(stale, host="agy"))
    assert "not a failure" in text
    assert "aaa001 -> bbb002 ccc003" in text and "ddd004 -> ccc003" in text
    assert "re-review now with: aw agy run --action review bbb002 ccc003" in text

    waiting = "\n".join(
        review_basis.stale_report_lines(
            stale, host="agy", other_live_runs=["run-live-1"]
        )
    )
    assert "Not yet: 1 other run(s) are still active (run-live-1)" in waiting
    assert "Then re-review with: aw agy run --action review bbb002 ccc003" in waiting
    assert "re-review now" not in waiting


def test_stale_bases_handles_shared_settled_changed_and_missing_prerequisites(
    tmp_path: Path,
) -> None:
    """Overlapping targets across many consumers: settled prunes cleanly, modified & missing flag all consumers."""
    repo = _repo(tmp_path)
    _plan(repo, "pre001", 1, "to-review")
    p2 = _plan(repo, "pre002", 2, "to-review")
    p3 = _plan(repo, "pre003", 3, "to-review")

    # Multiple consumers depend on overlapping targets (including duplicate edges in item deps).
    for cid, order, deps in (
        ("con001", 4, "executed:pre001, executed:pre002"),
        ("con002", 5, "executed:pre001, executed:pre002"),
        ("con003", 6, "executed:pre001"),
        ("con004", 7, "executed:pre003"),
    ):
        _plan(repo, cid, order, "to-review", deps=deps)
        dep_list = [d.strip() for d in deps.split(",")]
        dep_list.append(
            dep_list[0]
        )  # duplicate edge should deduplicate in provisional_targets
        targets = review_basis.provisional_targets(
            repo,
            {"id6": cid, "action": "review", "dependencies": dep_list},
            _state(repo, True),
        )
        assert len({t["id6"] for t in targets}) == len(targets)
        review_basis.record_basis(
            repo, cid, targets, run_id="run-shared", at="2026-11-19T00:00:00Z"
        )

    # Settle pre001 unchanged -> con003 (which depends only on pre001) should prune on stale_bases().
    _plan(repo, "pre001", 1, "reviewed")
    # Modify pre002's step text -> con001 and con002 both go stale on pre002.
    p2.write_text(
        p2.read_text(encoding="utf-8").replace("Do it", "Do something different"),
        encoding="utf-8",
    )
    # Delete pre003 -> con004 sees "prerequisite plan not found".
    p3.unlink()

    stale = review_basis.stale_bases(repo, prune=True)
    got = {(s.consumer, s.target, s.reason) for s in stale}
    assert (
        "con001",
        "pre002",
        "pre002's steps or scope changed (now to-review) since con001 was reviewed against it",
    ) in got
    assert (
        "con002",
        "pre002",
        "pre002's steps or scope changed (now to-review) since con002 was reviewed against it",
    ) in got
    assert ("con004", "pre003", "prerequisite plan not found") in got
    assert len(got) == 3

    # con003 was pruned because its sole target pre001 settled without design change.
    bdir = review_basis.basis_dir(repo)
    assert not (bdir / "con003.json").exists()
    assert (bdir / "con001.json").is_file()
    assert (bdir / "con002.json").is_file()
    assert (bdir / "con004.json").is_file()


def test_stale_bases_skips_and_prunes_terminal_and_missing_consumers(
    tmp_path: Path,
) -> None:
    """Already-executed, superseded, and missing consumers are never reported and get pruned."""
    repo = _repo(tmp_path)
    pre = _plan(repo, "pre001", 1, "to-review")
    pending_rev = _plan(repo, "con001", 2, "reviewed", deps="executed:pre001")
    pending_app = _plan(repo, "con002", 3, "approved", deps="executed:pre001")
    exec_plan = _plan(repo, "con003", 4, "to-review", deps="executed:pre001")
    sup_plan = _plan(repo, "con004", 5, "superseded", deps="executed:pre001")

    for cid in ("con001", "con002", "con003", "con004", "mis005"):
        targets = review_basis.provisional_targets(
            repo,
            {"id6": cid, "action": "review", "dependencies": ["executed:pre001"]},
            _state(repo, True),
        )
        review_basis.record_basis(
            repo, cid, targets, run_id="run-1", at="2026-11-22T00:00:00Z"
        )

    # Move con003 into executed/ and mark executed; modify prerequisite pre001 so all would be stale.
    _plan(repo, "con003", 4, "executed", deps="executed:pre001", subdir="executed")
    exec_plan.unlink()
    pre.write_text(
        pre.read_text(encoding="utf-8").replace("Do it", "Changed design"),
        encoding="utf-8",
    )
    assert pending_rev.is_file() and pending_app.is_file() and sup_plan.is_file()

    stale = review_basis.stale_bases(repo, prune=True)
    assert {(s.consumer, s.consumer_status) for s in stale} == {
        ("con001", "reviewed"),
        ("con002", "approved"),
    }

    bdir = review_basis.basis_dir(repo)
    assert (bdir / "con001.json").is_file()
    assert (bdir / "con002.json").is_file()
    assert not (bdir / "con003.json").exists()
    assert not (bdir / "con004.json").exists()
    assert not (bdir / "mis005.json").exists()


def test_stale_report_separates_approved_and_suggests_partition_for_large_lists() -> (
    None
):
    """Report separates approved vs unapproved consumers and suggests aw partition --split-sets for >8 plans."""
    mixed = [
        review_basis.StaleBasis(
            "rev001",
            "pre001",
            "reviewed",
            "changed",
            "run-1",
            consumer_status="reviewed",
        ),
        review_basis.StaleBasis(
            "app001",
            "pre001",
            "reviewed",
            "changed",
            "run-1",
            consumer_status="approved",
        ),
        review_basis.StaleBasis(
            "app002",
            "pre001",
            "reviewed",
            "changed",
            "run-1",
            consumer_status="approved",
        ),
    ]
    mixed_text = "\n".join(review_basis.stale_report_lines(mixed, host="agy"))
    assert "1 unapproved (need re-review), 2 already approved" in mixed_text
    assert "re-review now with: aw agy run --action review rev001" in mixed_text
    assert (
        "Optional (already approved, 2 plan(s)): aw agy run --action review app001 app002"
        in mixed_text
    )

    # Large all-approved list (>8) suggests aw partition --action review --split-sets
    large = [
        review_basis.StaleBasis(
            f"app{i:03d}",
            "pre001",
            "approved",
            "changed",
            "run-1",
            consumer_status="approved",
        )
        for i in range(1, 11)
    ]
    large_text = "\n".join(review_basis.stale_report_lines(large, host="agy"))
    assert "all 10 flagged plan(s) are already approved" in large_text
    assert (
        "aw partition -t plans --action review --run agy --split-sets "
        "app001 app002 app003 app004 app005 app006 app007 app008 app009 app010"
        in large_text
    )


def test_stale_bases_skips_and_prunes_orchestrator_consumers(tmp_path: Path) -> None:
    """Kind: orchestrator consumers can never be re-reviewed, so stale_bases skips and prunes them."""
    repo = _repo(tmp_path)
    pre = _plan(repo, "pre001", 1, "to-review")
    _plan(repo, "ch0001", 2, "approved", deps="executed:pre001")
    orch = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / "20261113-rudset-00-ord000-o.ipd.md"
    )
    orch.write_text(
        RecordBuilder().plan(
            title="orchestrator",
            plan_role="orchestrator",
            status="approved",
            set="rudset",
            order=0,
            id6="ord000",
            scope_paths="README.md",
            body="## Detailed Implementation Checklist (TODO)\n- [ ] E-01 Run children\n- [ ] V-01 Verify",
            text_only=True,
        ),
        encoding="utf-8",
    )
    for cid in ("ch0001", "ord000"):
        targets = review_basis.provisional_targets(
            repo,
            {"id6": cid, "action": "review", "dependencies": ["executed:pre001"]},
            _state(repo, True),
        )
        review_basis.record_basis(
            repo, cid, targets, run_id="run-1", at="2026-11-22T00:00:00Z"
        )

    pre.write_text(
        pre.read_text(encoding="utf-8").replace("Do it", "Changed step"),
        encoding="utf-8",
    )
    stale = review_basis.stale_bases(repo, prune=True)
    assert [s.consumer for s in stale] == ["ch0001"]
    bdir = review_basis.basis_dir(repo)
    assert (bdir / "ch0001.json").is_file()
    assert not (bdir / "ord000.json").exists()


def test_stale_report_caps_many_changed_prerequisites() -> None:
    """Reports with more than MAX_TARGET_DETAIL_LINES changed prerequisites cap the detail list."""
    total_targets = review_basis.MAX_TARGET_DETAIL_LINES + 5
    stale = [
        review_basis.StaleBasis(
            f"con{i:03d}",
            f"pre{i:03d}",
            "reviewed",
            "changed",
            "run-1",
            consumer_status="reviewed",
        )
        for i in range(1, total_targets + 1)
    ]
    lines = review_basis.stale_report_lines(stale, host="agy")
    arrow_lines = [ln for ln in lines if " -> " in ln and ln.startswith("    ")]
    assert len(arrow_lines) == review_basis.MAX_TARGET_DETAIL_LINES
    assert any("... and 5 more changed prerequisite(s)" in ln for ln in lines)
