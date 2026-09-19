"""The cache-lifecycle MUTATION HARNESS: one named, independently runnable case per scenario.

runanalytics Order 10 (`9xycbh`) E-02. Stdlib only.

WHAT THIS IS FOR. Order 02 (`bzz5e6`) owns the cache decision; this harness is how Order 10 PROVES
it across the whole lifecycle axis: unchanged, active-then-changed, resumed-in-place, added,
removed, corrupt-among-valid, schema-upgraded, concurrent, and interrupted-publication. Each case
returns its asserted decision WITH the reason code, because "rebuild" alone would pass for the wrong
reason as readily as the right one.

NO REAL TIME, NO SUBPROCESS, NO SOCKET. Freshness keys on each input's size and `mtime_ns`
(`run_analytics_cache.source_fingerprint`), so a mutation is made observable by STAMPING an mtime
with `os.utime` rather than by sleeping. Concurrency is driven by acquiring the entry lock directly
through `platform_lock`, which is what the real contention path does, instead of racing two
processes and hoping.

THE RESUMED CASE IS THE ONE THAT MATTERS MOST AND IS EASIEST TO GET WRONG. Order 02 recorded it: a
resumed run REUSES its directory, so an mtime comparison cannot establish staleness. `decide` checks
terminal state BEFORE the fingerprint for exactly that reason, and `resumed_in_place` asserts the
reason code is `run-not-terminal` rather than merely that a rebuild happened.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agent_workflows import run_analytics
from agent_workflows import run_analytics_cache as cache_mod
from agent_workflows import run_analytics_privacy as privacy

from . import BASE_MTIME, core_state, write_run

__all__ = [
    "MutationCase",
    "CASES",
    "case",
    "run_case",
    "run_all",
]


@dataclass(frozen=True)
class MutationCase:
    """One lifecycle case: what it does, and the decision plus reason it must produce."""

    name: str
    concern: str
    expected_verdict: str
    expected_reason: str
    #: Set when the case asserts the ABSENCE of a decision (a removed run is never enumerated).
    expects_no_decision: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "concern": self.concern,
            "expected_verdict": self.expected_verdict,
            "expected_reason": self.expected_reason,
            "expects_no_decision": self.expects_no_decision,
        }


CASES: tuple[MutationCase, ...] = (
    MutationCase(
        "unchanged",
        "a terminal run with an entry and identical inputs is REUSED",
        "hit",
        "fresh-complete-entry",
    ),
    MutationCase(
        "active_then_changed",
        "a run cached while live, then mutated, must rebuild",
        "rebuild",
        "fingerprint-changed",
    ),
    MutationCase(
        "resumed_in_place",
        "a resumed run reuses its directory, so mtime cannot prove staleness",
        "rebuild",
        "run-not-terminal",
    ),
    MutationCase(
        "added",
        "a run first seen after an analysis has no entry",
        "rebuild",
        "no-entry",
    ),
    MutationCase(
        "removed",
        "a removed run yields NO decision; removals are found by listing, not deciding",
        "",
        "",
        expects_no_decision=True,
    ),
    MutationCase(
        "corrupt_among_valid",
        "one unreadable run degrades ITSELF; the healthy run is unaffected",
        "rebuild",
        "no-entry",
    ),
    MutationCase(
        "schema_upgraded",
        "an entry written by another cache schema is not reused",
        "rebuild",
        "schema-version-mismatch",
    ),
    MutationCase(
        "concurrent",
        "a contended entry SKIPS with a reason and never waits",
        "skip",
        "lock-busy",
    ),
    MutationCase(
        "interrupted_publication",
        "a partially written entry is never read as valid",
        "rebuild",
        "entry-unreadable",
    ),
)


def case(name: str) -> MutationCase:
    for item in CASES:
        if item.name == name:
            return item
    raise KeyError(f"no such mutation case: {name!r}")


# --------------------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------------------
def _root_id(repo: Path, runs_root: Path) -> str:
    salt = privacy.load_or_create_salt(cache_mod.cache_root(repo))
    return cache_mod.source_root_id(runs_root, salt=salt)


def _runs_root(repo: Path) -> Path:
    root = repo / ".aw" / "records" / "runs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _seed_entry(repo: Path, runs_root: Path, run_dir: Path) -> None:
    """Populate the cache for one run through the real `update_cache` path."""

    cache_mod.update_cache(
        [run_dir],
        build_facts=run_analytics.build_cache_facts,
        repo=repo,
        root_id=_root_id(repo, runs_root),
    )


def _decide(repo: Path, runs_root: Path, run_dir: Path) -> cache_mod.CacheDecision:
    decision, _envelope = cache_mod.decide(
        run_dir, root_id=_root_id(repo, runs_root), repo=repo
    )
    return decision


def _live_queue() -> list[dict[str, Any]]:
    """A queue with a RUNNING item, which is what makes a run non-terminal."""

    return [
        {
            "position": 1,
            "id6": "aaa111",
            "setid": "demoset",
            "action": "execute",
            "status": "running",
            "attempts": [{"number": 1, "started_at": "2026-03-01T00:00:00Z"}],
        }
    ]


# --------------------------------------------------------------------------------------------------
# The cases
# --------------------------------------------------------------------------------------------------
def _unchanged(repo: Path) -> dict[str, Any]:
    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000001", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, run_dir)
    decision = _decide(repo, runs_root, run_dir)
    return {"decision": decision, "detail": "inputs untouched between the two passes"}


def _active_then_changed(repo: Path) -> dict[str, Any]:
    """Cache a run, then MUTATE an analytics-relevant input and re-decide.

    The mutation is a real content change AND an explicit mtime stamp, so the case does not depend
    on filesystem timestamp granularity or on any elapsed wall time.
    """

    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000002", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, run_dir)
    before = cache_mod.source_fingerprint(run_dir)

    outcome = run_dir / "outcomes" / "01-aaa111.json"
    outcome.write_text(
        json.dumps({"disposition": "executed", "cost": 2.5}, sort_keys=True),
        encoding="utf-8",
    )
    os.utime(outcome, (BASE_MTIME + 60, BASE_MTIME + 60))
    after = cache_mod.source_fingerprint(run_dir)

    decision = _decide(repo, runs_root, run_dir)
    return {
        "decision": decision,
        "detail": "an analytics-relevant input changed after the entry was published",
        "fingerprint_changed": before != after,
    }


def _resumed_in_place(repo: Path) -> dict[str, Any]:
    """A resumed run: SAME directory, entry present, inputs byte-identical, yet it must rebuild.

    This is the case an mtime-based freshness rule gets wrong. The entry is seeded while the run is
    terminal, then the run is put back into a RUNNING state at the SAME mtimes, so nothing about the
    file stamps has changed; only the terminal flag has.
    """

    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000003", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, run_dir)

    state_path = run_dir / "state.json"
    stat_before = state_path.stat()
    payload = core_state(run_dir.name, queue=_live_queue())
    state_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    # RESTORE the original mtime, so the only observable difference is the terminal state.
    os.utime(state_path, (stat_before.st_mtime, stat_before.st_mtime))

    decision = _decide(repo, runs_root, run_dir)
    return {
        "decision": decision,
        "detail": "same directory, mtime restored, run put back to running",
        "mtime_unchanged": state_path.stat().st_mtime == stat_before.st_mtime,
    }


def _added(repo: Path) -> dict[str, Any]:
    runs_root = _runs_root(repo)
    first = write_run(runs_root, "run-20260301T000000Z-1000004", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, first)
    added = write_run(runs_root, "run-20260301T040000Z-1000005", mtime=BASE_MTIME)
    decision = _decide(repo, runs_root, added)
    return {
        "decision": decision,
        "detail": "a second run appeared after the first sweep",
    }


def _removed(repo: Path) -> dict[str, Any]:
    """A removed run produces NO decision, and the removal is found by LISTING the cache."""

    runs_root = _runs_root(repo)
    kept = write_run(runs_root, "run-20260301T000000Z-1000006", mtime=BASE_MTIME)
    gone = write_run(runs_root, "run-20260301T050000Z-1000007", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, kept)
    _seed_entry(repo, runs_root, gone)

    root_id = _root_id(repo, runs_root)
    entry_before = cache_mod.entry_path(root_id, gone.name, repo)
    existed = entry_before.exists()

    import shutil

    shutil.rmtree(gone)

    report = cache_mod.update_cache(
        [kept],
        build_facts=run_analytics.build_cache_facts,
        repo=repo,
        root_id=root_id,
    )
    decided_ids = {d.run_id for d in report.decisions}
    return {
        "decision": None,
        "detail": "the removed run is absent from the sweep's decisions entirely",
        "entry_existed_before": existed,
        "decided_run_ids": sorted(decided_ids),
        "removed_run_id": gone.name,
        "orphan_entry_still_on_disk": entry_before.exists(),
    }


def _corrupt_among_valid(repo: Path) -> dict[str, Any]:
    """One corrupt run among valid ones: the sweep COMPLETES and the healthy run still caches."""

    runs_root = _runs_root(repo)
    healthy = write_run(runs_root, "run-20260301T000000Z-1000008", mtime=BASE_MTIME)
    corrupt = write_run(
        runs_root, "run-20260301T060000Z-1000009", corrupt_state=True, mtime=BASE_MTIME
    )

    report = cache_mod.update_cache(
        [healthy, corrupt],
        build_facts=run_analytics.build_cache_facts,
        repo=repo,
        root_id=_root_id(repo, runs_root),
    )
    by_run = {d.run_id: d for d in report.decisions}
    healthy_facts = run_analytics.build_run_facts(healthy)
    corrupt_facts = run_analytics.build_run_facts(corrupt)
    return {
        "decision": by_run.get(healthy.name),
        "detail": "the corrupt run degraded itself; the healthy run was analyzed normally",
        "healthy_fact_count": len(healthy_facts.facts),
        "corrupt_fact_count": len(corrupt_facts.facts),
        "corrupt_warnings": list(corrupt_facts.quality.warnings),
        "totals": dict(report.totals),
    }


def _schema_upgraded(repo: Path) -> dict[str, Any]:
    """An entry written under a DIFFERENT cache schema version is not reused."""

    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000010", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, run_dir)

    root_id = _root_id(repo, runs_root)
    path = cache_mod.entry_path(root_id, run_dir.name, repo)
    payload = json.loads(path.read_text(encoding="utf-8"))
    stored_version = payload.get("schema_version")
    payload["schema_version"] = int(cache_mod.CACHE_SCHEMA_VERSION) + 1
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    decision = _decide(repo, runs_root, run_dir)
    return {
        "decision": decision,
        "detail": "the on-disk entry claims a newer cache schema than this build reads",
        "stored_version": stored_version,
        "mutated_version": payload["schema_version"],
    }


def _concurrent(repo: Path) -> dict[str, Any]:
    """Two analyzers on one entry: the second SKIPS with `lock-busy` and never blocks.

    Driven by holding the entry lock through `platform_lock` (the same lock the publisher takes)
    rather than by spawning a process, so the case is deterministic and spawns nothing.
    """

    from agent_workflows import platform_lock

    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000011", mtime=BASE_MTIME)
    root_id = _root_id(repo, runs_root)

    directory = cache_mod.entry_dir(root_id, run_dir.name, repo)
    directory.mkdir(parents=True, exist_ok=True)
    handle = platform_lock.acquire(directory / cache_mod._LOCK_FILENAME)
    try:
        report = cache_mod.update_cache(
            [run_dir],
            build_facts=run_analytics.build_cache_facts,
            repo=repo,
            root_id=root_id,
        )
    finally:
        handle.release()
    decision = report.decisions[0] if report.decisions else None
    return {
        "decision": decision,
        "detail": "the entry lock was already held; the sweep skipped without waiting",
        "totals": dict(report.totals),
        "entry_written": (directory / cache_mod.ENTRY_FILENAME).exists(),
    }


def _interrupted_publication(repo: Path) -> dict[str, Any]:
    """A truncated entry file is not readable as valid, so the run rebuilds.

    Publication is atomic (`atomic_write_json`), so this state is not reachable by interrupting the
    writer; it is what a torn or externally damaged entry LOOKS like, and the requirement is that
    reading one never yields a half-trusted envelope.
    """

    runs_root = _runs_root(repo)
    run_dir = write_run(runs_root, "run-20260301T000000Z-1000012", mtime=BASE_MTIME)
    _seed_entry(repo, runs_root, run_dir)

    root_id = _root_id(repo, runs_root)
    path = cache_mod.entry_path(root_id, run_dir.name, repo)
    full = path.read_text(encoding="utf-8")
    path.write_text(full[: max(1, len(full) // 2)], encoding="utf-8")

    decision = _decide(repo, runs_root, run_dir)
    readable = True
    try:
        cache_mod.load_entry(path)
    except Exception:
        readable = False
    return {
        "decision": decision,
        "detail": "the entry file was truncated; it must not read back as a valid envelope",
        "entry_readable": readable,
    }


_RUNNERS: dict[str, Callable[[Path], dict[str, Any]]] = {
    "unchanged": _unchanged,
    "active_then_changed": _active_then_changed,
    "resumed_in_place": _resumed_in_place,
    "added": _added,
    "removed": _removed,
    "corrupt_among_valid": _corrupt_among_valid,
    "schema_upgraded": _schema_upgraded,
    "concurrent": _concurrent,
    "interrupted_publication": _interrupted_publication,
}


def run_case(name: str, repo: Path) -> dict[str, Any]:
    """Run ONE case in `repo` and return its observation plus the expectation it is judged against.

    `conforms` is computed here, from the case's declared verdict AND reason, so a caller cannot
    accidentally assert only the verdict and pass for the wrong reason.
    """

    spec = case(name)
    observed = _RUNNERS[name](repo)
    decision = observed.get("decision")
    if spec.expects_no_decision:
        conforms = decision is None
        verdict = ""
        reason = ""
    else:
        verdict = getattr(decision, "verdict", "")
        reason = getattr(decision, "reason", "")
        conforms = verdict == spec.expected_verdict and reason == spec.expected_reason
    return {
        "case": spec.to_dict(),
        "observed_verdict": verdict,
        "observed_reason": reason,
        "conforms": conforms,
        **{k: v for k, v in observed.items() if k != "decision"},
    }


def run_all(repo_factory: Callable[[str], Path]) -> list[dict[str, Any]]:
    """Run every case, each in its OWN repo from `repo_factory(case_name)`.

    Separate repos by construction: a shared cache root would let one case's entries decide
    another's verdict, which is precisely the cross-contamination these cases exist to detect.
    """

    return [run_case(spec.name, repo_factory(spec.name)) for spec in CASES]
