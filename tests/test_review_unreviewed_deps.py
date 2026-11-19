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


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    return repo


def _plan(
    repo: Path, id6: str, order: int, status: str, deps: str = "", step: str = "Do it"
) -> Path:
    p = (
        repo
        / ".aw"
        / "records"
        / "plans"
        / "pending"
        / f"20261113-rudset-{order:02d}-{id6}-p.ipd.md"
    )
    dep_line = f"- Item-Dependencies: {deps}\n" if deps else ""
    p.write_text(
        f"# IPD: {id6}\n\n- Kind: child\n- Status: {status}\n- Set: rudset\n- Order: {order}\n"
        f"- Id: {id6}\n{dep_line}- Scope-Paths: README.md\n\n"
        f"## Detailed Implementation Checklist (TODO)\n- [ ] E-01 {step}\n- [ ] V-01 Verify it\n",
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
    pre.write_text(
        pre.read_text().replace("- Status: to-review", "- Status: reviewed"),
        encoding="utf-8",
    )
    assert review_basis.provisional_targets(repo, item, _state(repo, True)) == []
    review_basis.record_basis(
        repo, "bbb002", [], run_id="run-y", at="2026-11-13T01:00:00Z"
    )
    assert review_basis.stale_bases(repo) == []


def test_unchanged_prerequisite_that_gets_reviewed_prunes_the_record(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path)
    pre = _plan(repo, "aaa001", 1, "to-review")
    item = {"id6": "bbb002", "action": "review", "dependencies": ["executed:aaa001"]}
    targets = review_basis.provisional_targets(repo, item, _state(repo, True))
    path = review_basis.record_basis(repo, "bbb002", targets, run_id="r", at="t")
    assert path is not None and path.is_file()
    pre.write_text(
        pre.read_text().replace("- Status: to-review", "- Status: reviewed"),
        encoding="utf-8",
    )
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
        "# IPD: orchestrator\n\n- Kind: orchestrator\n- Status: to-review\n- Set: rudset\n"
        "- Order: 0\n- Id: ord000\n- Scope-Paths: README.md\n\n"
        "## Child IPDs, sequence, and dependencies\n\n| Order | Id | Summary |\n|---|---|---|\n"
        + "\n".join(rows)
        + "\n\n## Detailed Implementation Checklist (TODO)\n- [ ] E-01 Run children\n- [ ] V-01 Verify\n",
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
    first = next((repo / ".aw" / "records" / "plans" / "pending").glob("*-ch0001-*"))
    first.write_text(
        first.read_text().replace("- Status: to-review", "- Status: reviewed"),
        encoding="utf-8",
    )

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
    p1 = _plan(repo, "pre001", 1, "to-review")
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
    p1.write_text(
        p1.read_text(encoding="utf-8").replace(
            "- Status: to-review", "- Status: reviewed"
        ),
        encoding="utf-8",
    )
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
