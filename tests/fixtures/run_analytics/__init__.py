"""The deterministic run-analytics FIXTURE CORPUS and its mutation harness.

runanalytics Order 10 (`9xycbh`) E-01, E-02 and E-03. Stdlib only.

WHY A MODULE RATHER THAN COMMITTED DATA FILES, WHICH IS THE LOAD-BEARING DESIGN CHOICE HERE.
`tests/fixtures/run_analytics/**` is TRACKED (`git check-ignore` exits 1 for it), so it IS
enumerated by `leak_sanitizer._tracked_files` and IS scanned by the named `local-leaks` CI job
(`.github/workflows/local-leaks.yml`). Re-probed at execution in a throwaway repo: a tracked file
containing a seeded home path returns `home-path` and `handle` findings at FAIL severity, and that
job is fail-closed. A committed canary would therefore break CI by construction. So every sensitive
string this corpus needs is ASSEMBLED AT RUNTIME from fragments, exactly as the shipped detection
engine composes its own patterns, and nothing under this directory carries a literal home path,
username, hostname, token, remote or secret-shaped value.

THE CONVERSE HOLDS FOR THE LIVE CORPUS AND IS EQUALLY DELIBERATE. `.aw/records/runs/` is gitignored
(`.aw/.gitignore`, the `records/runs/` entry), disposable and mutable, and its `state.json` files
carry absolute maintainer home paths in the first fields an ingester reads. Not one byte of it is
copied here: every fixture REPRODUCES a measured PROPERTY of the real corpus (the generation
census, the uniform `schema_version`, the 14-key core plus four optional keys) rather than sampling
its content. A fixture is authoritative; the live corpus is at most a read-only smoke input.

THE AGY SIDE IS SYNTHETIC AND SAYS SO IN THE DATA. Measured across the review corpus of 135 runs:
`oc_runipd.py` 120, the legacy `tools/ipdrunner/runipd.py` 13, `tools/ipdrunner/ipdrunner.py` 2, and
`agy_runipd.py` ZERO. So no Agy run has ever been observed on disk here, the Agy fixtures are
written against the Agy runner's CODE, and a passing Agy assertion proves conformance to the
adapter's own assumptions and NOT cross-host corpus validation. `SCENARIOS` carries that as a
`synthetic` flag with a reason, so the label travels with the fixture instead of living in a
comment a reporter can skip.

BOTH LEGACY GENERATIONS ARE THEIR OWN SCENARIOS, for the same measured reason. They are the real
historical schema drift in this repository (15 runs between them), so a "mixed-runner corpus"
scenario satisfied entirely by OpenCode lineage would prove nothing about drift tolerance.

DETERMINISM RULES, because a fixture that varies cannot carry a hand-calculated expectation. Every
timestamp is a fixed literal, every cost and token count is a small exact number whose totals are
hand-calculable, and no fixture reads the clock, sleeps, spawns a subprocess or opens a socket. The
mutation harness advances mtimes by WRITING (and by an explicit `os.utime` where a byte-identical
mutation must still be observable), never by waiting.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "CORPUS_SCHEMA_VERSION",
    "Scenario",
    "SCENARIOS",
    "scenario",
    "canary",
    "canary_values",
    "core_state",
    "write_run",
    "build_corpus",
    "corpus_manifest",
    "GENERATION_DRIVERS",
    "SYNTHETIC_GENERATIONS",
]

#: Bumped when the fixture SHAPE changes, so a stale expectation is attributable.
CORPUS_SCHEMA_VERSION = 1

#: Generation label -> the `driver.path` this corpus writes for it. The BASENAME is what
#: `run_analytics_sources.driver_generation` keys on (`schema_version` is uniformly 1 across every
#: real generation and cannot discriminate), so the parent directories here reproduce the real
#: layouts: the current driver lives in the package, both legacy generations under `tools/ipdrunner/`.
GENERATION_DRIVERS: dict[str, str] = {
    "oc_runipd": "agent_workflows/oc_runipd.py",
    "agy_runipd": "agent_workflows/agy_runipd.py",
    "runipd": "tools/ipdrunner/runipd.py",
    "ipdrunner": "tools/ipdrunner/ipdrunner.py",
}

#: Generations with NO observed on-disk exemplar, each with the measured reason. Any assertion
#: derived from one of these is SYNTHETIC and may never be reported as corpus validation.
SYNTHETIC_GENERATIONS: dict[str, str] = {
    "agy_runipd": (
        "zero Agy runs in the measured corpus (120 oc_runipd, 13 runipd, 2 ipdrunner, 0 agy); "
        "written against agy_runipd's code, never an observed Agy run"
    ),
}


# --------------------------------------------------------------------------------------------------
# E-03: runtime canary assembly
# --------------------------------------------------------------------------------------------------
#
# ASSEMBLED, NEVER WRITTEN. Each value is built from fragments so this tracked file contains no
# matchable literal. The classes mirror `run_analytics_export.CANARY_CLASSES`, and
# `canary_values()` returns the whole set so a privacy proof can plant every one of them.
#
# NOTE WHICH ONES THE SHIPPED DETECTOR ACTUALLY SEES. Re-measured at execution against
# `leak_sanitizer.build_ruleset` + `scan_text`: the filesystem path and the username are caught at
# FAIL, and the other eleven classes return ZERO findings. So planting these proves the STRUCTURAL
# exclusion; it does not, and cannot, rest on detection.
_CANARY_FRAGMENTS: dict[str, tuple[str, ...]] = {
    "filesystem-path": ("/ho", "me/", "gfa", "riello", "/VC/agent-workflows"),
    "username": ("gfa", "riello"),
    "hostname": ("work", "station", ".local"),
    "prompt-text": ("You are an agent. ", "Do the secret thing."),
    "response-text": ("I have completed ", "the secret thing."),
    "shell-command": ("git push --force ", "origin main"),
    "git-remote": ("git@git", "hub.com:", "private-org/private-repo.git"),
    "branch-name": ("feature/", "unreleased-", "acquisition"),
    "commit-message": ("fix: patch the ", "undisclosed vulnerability"),
    "environment-secret": ("AWS_SECRET", "_ACCESS_KEY", "=wJalrXUtn", "FEMI/K7MDENG"),
    "high-entropy-token": ("sk-", "proj-", "abcdef0123456789", "ABCDEF0123456789"),
    "spreadsheet-formula": ("=cmd|", "' /C calc'!A0"),
    "archive-traversal": ("../" * 3, "etc/passwd"),
}


def canary(kind: str) -> str:
    """One canary value, assembled at call time from fragments.

    Raises `KeyError` for an unknown class rather than returning a placeholder: a silently empty
    canary would make a privacy assertion pass while planting nothing, which is the exact failure
    mode this corpus exists to rule out.
    """

    return "".join(_CANARY_FRAGMENTS[kind])


def canary_values() -> dict[str, str]:
    """Every canary class mapped to its assembled value."""

    return {kind: canary(kind) for kind in _CANARY_FRAGMENTS}


# --------------------------------------------------------------------------------------------------
# E-01: the deterministic corpus
# --------------------------------------------------------------------------------------------------
#: The 14-key core measured present in every generation, as fixed literals. Built here rather than
#: per-scenario so a scenario declares only what it VARIES, which is what makes a hand-calculated
#: expectation readable.
_BASE_CREATED = "2026-03-01T00:00:00Z"
_BASE_UPDATED = "2026-03-01T01:00:00Z"


def core_state(
    run_id: str,
    *,
    generation: str = "oc_runipd",
    queue: Sequence[Mapping[str, Any]] = (),
    optional: Mapping[str, Any] | None = None,
    repo: str = "/repo",
    model: str = "provider/model-a",
) -> dict[str, Any]:
    """A `state.json` payload carrying exactly the measured 14-key core, plus optional extras.

    `repo` defaults to a NEUTRAL `/repo` rather than a real checkout path, so the committed corpus
    carries no path a detector would flag. A test that wants the real shape plants
    `canary("filesystem-path")` explicitly, which is the only way a forbidden value enters.
    """

    driver_path = GENERATION_DRIVERS.get(generation, GENERATION_DRIVERS["oc_runipd"])
    payload: dict[str, Any] = {
        "created_at": _BASE_CREATED,
        "updated_at": _BASE_UPDATED,
        "driver": {"path": f"{repo}/{driver_path}"},
        "manifest": f"{repo}/manifest.json",
        "manifest_sha256": "1" * 64,
        "options": {"model": model},
        "queue": [dict(item) for item in queue],
        "repo": repo,
        "runbook": f"{repo}/runbook.md",
        "runbook_sha256": "2" * 64,
        "run_id": run_id,
        # UNIFORM ACROSS EVERY GENERATION, reproducing the measurement that rules out
        # version-dispatch: all three real generations wrote `1`.
        "schema_version": 1,
        "selectors": ["demo"],
        "set_sessions": {},
    }
    if optional:
        payload.update(dict(optional))
    return payload


def _item(
    *,
    position: int,
    id6: str,
    setid: str = "demoset",
    action: str = "execute",
    status: str = "executed",
    attempts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    return {
        "position": position,
        "id6": id6,
        "setid": setid,
        "action": action,
        "status": status,
        "attempts": [dict(a) for a in attempts],
    }


def _attempt(
    number: int,
    *,
    start: str,
    end: str | None,
    cost: float | None = 1.0,
    tokens: Mapping[str, int] | None = None,
    recovery: bool = False,
    verify: bool = False,
    verify_cost: float | None = None,
    verify_tokens: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """One attempt with HAND-CALCULABLE numbers.

    Token components always CONSERVE (input + output + the named extras == total) unless a scenario
    deliberately breaks conservation, because a fixture whose arithmetic silently fails to add up
    would make a conservation assertion untestable.
    """

    payload: dict[str, Any] = {"number": number, "started_at": start}
    if end is not None:
        payload["ended_at"] = end
    if cost is not None:
        payload["cost"] = cost
    if tokens is not None:
        payload["tokens"] = dict(tokens)
    if recovery:
        payload["recovery"] = True
    if verify:
        payload["verify_log"] = "sessions/verify.log"
        if verify_cost is not None:
            payload["verify_cost"] = verify_cost
        if verify_tokens is not None:
            payload["verify_tokens"] = dict(verify_tokens)
    return payload


#: The conserving token triple used wherever a scenario does not vary usage: 100 + 20 == 120.
_TOKENS = {"input": 100, "output": 20, "total": 120}


@dataclass(frozen=True)
class Scenario:
    """One named fixture scenario, carrying its own synthetic label and expectations.

    `expected` holds HAND-CALCULATED values (never values read back from the code under test), and
    `expected_outcome` may legitimately be `cannot-determine`: a documented refusal by an
    under-powered analysis is a PASSING outcome, and recording it here keeps an executor from
    turning a refusal into a number.
    """

    number: int
    name: str
    generation: str
    concern: str
    #: True when no real on-disk exemplar of this shape exists; carries the reason.
    synthetic: bool = False
    synthetic_reason: str = ""
    #: `computed` (a value is asserted) or `cannot-determine` (a refusal is the pass).
    expected_outcome: str = "computed"
    #: The observed n behind a `cannot-determine`, so the refusal is auditable.
    observed_n: int | None = None
    expected: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "name": self.name,
            "generation": self.generation,
            "concern": self.concern,
            "synthetic": self.synthetic,
            "synthetic_reason": self.synthetic_reason,
            "expected_outcome": self.expected_outcome,
            "observed_n": self.observed_n,
            "expected": dict(self.expected),
        }


def _syn(generation: str) -> tuple[bool, str]:
    reason = SYNTHETIC_GENERATIONS.get(generation, "")
    return bool(reason), reason


def _sc(
    number: int,
    name: str,
    concern: str,
    *,
    generation: str = "oc_runipd",
    expected_outcome: str = "computed",
    observed_n: int | None = None,
    **expected: Any,
) -> Scenario:
    synthetic, reason = _syn(generation)
    return Scenario(
        number=number,
        name=name,
        generation=generation,
        concern=concern,
        synthetic=synthetic,
        synthetic_reason=reason,
        expected_outcome=expected_outcome,
        observed_n=observed_n,
        expected=expected,
    )


#: THE 33 SCENARIOS, each with the measured feasibility that decides its expected outcome.
#:
#: Five of them (8, 18, 19, 20 and 26) carry `expected_outcome="cannot-determine"` with the observed
#: n their owning sibling measured. That is NOT a gap: Order 06 (`aflsz3`) REFUSES multi-attempt,
#: recovery and merge-conflict analysis as under-powered, and Order 07 (`6eq3oq`) renders a
#: first-class refusal panel rather than a chart. Their CODE PATHS are still exercised here against
#: synthetic fixtures; what is refused is the corpus-level ANALYSIS, and the two claims are
#: different. Turning a refusal into a number is the fabrication this Set exists to prevent.
SCENARIOS: tuple[Scenario, ...] = (
    _sc(
        1,
        "opencode-completed-run",
        "the dominant real shape (120 of 135 runs)",
        run_facts_nonempty=True,
        generation_label="oc_runipd",
        host="opencode",
    ),
    _sc(
        2,
        "agy-completed-run",
        "the Agy adapter's own assumptions, with NO observed exemplar",
        generation="agy_runipd",
        generation_label="agy_runipd",
        host="agy",
    ),
    _sc(
        3,
        "mixed-runner-corpus",
        "four generations in one sweep, including BOTH legacy ones",
        generation_count=4,
    ),
    _sc(
        4,
        "review-and-execute-separated",
        "two queue items, one review one execute",
        item_count=2,
    ),
    _sc(
        5,
        "review-and-execute-aggregated",
        "one item carrying both phases",
        item_count=1,
    ),
    _sc(
        6,
        "verifier-present",
        "a verify artifact exists, so verify usage is RECORDED",
        verify_provenance="recorded",
    ),
    _sc(
        7,
        "verifier-absent",
        "no verify artifact, so verify usage is NOT-APPLICABLE and not zero",
        verify_provenance="not-applicable",
    ),
    _sc(
        8,
        "retry-multi-attempt",
        "three attempts on one item; the corpus analysis refuses",
        expected_outcome="cannot-determine",
        observed_n=6,
        attempt_count=3,
    ),
    _sc(
        9,
        "resumed-same-directory",
        "a resumed run reuses its dir, so mtime cannot prove staleness",
        cache_decision="rebuild",
        cache_reason="run-not-terminal",
    ),
    _sc(
        10,
        "in-progress-then-changed",
        "cached live then mutated",
        cache_decision="rebuild",
    ),
    _sc(
        11,
        "run-added-after-first-analysis",
        "a new run has no entry",
        cache_decision="rebuild",
        cache_reason="no-entry",
    ),
    _sc(
        12,
        "run-removed-after-first-analysis",
        "a removed run yields NO decision at all",
        decision_absent=True,
    ),
    _sc(
        13,
        "one-corrupt-among-valid",
        "degradation is scoped to the corrupt run only",
        corrupt_count=1,
        healthy_unaffected=True,
    ),
    _sc(
        14,
        "missing-cost",
        "cost absent where it should exist is MISSING, never zero",
        cost_provenance="missing",
    ),
    _sc(
        15,
        "missing-token-component",
        "a partial token map does not silently conserve",
        conservation_holds=False,
    ),
    _sc(
        16,
        "missing-model-price",
        "an unpriced model yields no derived cost",
        derived_cost_absent=True,
    ),
    _sc(
        17,
        "price-effective-date-boundary",
        "the two measured pricing eras and their boundary",
        era_count=2,
    ),
    _sc(
        18,
        "failed-merge-then-retry",
        "code path exercised; corpus analysis refuses",
        expected_outcome="cannot-determine",
        observed_n=3,
    ),
    _sc(
        19,
        "permanent-merge-failure",
        "code path exercised; corpus analysis refuses",
        expected_outcome="cannot-determine",
        observed_n=3,
    ),
    _sc(
        20,
        "test-failure-retry-loop",
        "code path exercised; corpus analysis refuses",
        expected_outcome="cannot-determine",
        observed_n=6,
    ),
    _sc(
        21,
        "gate-and-risk-heavy-activity",
        "gate/risk activity is taxonomized",
        activity_present=True,
    ),
    _sc(
        22,
        "overlapping-activity-intervals",
        "overlap is accounted, never double-counted",
        overlap_accounted=True,
    ),
    _sc(
        23,
        "telemetry-disabled",
        "no telemetry dir, and that is not a defect",
        telemetry_present=False,
    ),
    _sc(
        24, "basic-start-end-telemetry", "start and end records only", telemetry_kinds=2
    ),
    _sc(
        25,
        "periodic-telemetry",
        "periodic samples between start and end",
        telemetry_periodic=True,
    ),
    _sc(
        26,
        "different-node-pseudonyms",
        "pseudonyms differ across attempts; identity coverage is thin",
        expected_outcome="cannot-determine",
        observed_n=6,
    ),
    _sc(
        27,
        "probe-failure-modes",
        "permission, timeout and malformed probe results are recorded",
        probe_failure_kinds=3,
    ),
    _sc(
        28,
        "concurrent-analyzers",
        "a contended entry SKIPS with a reason, never waits",
        cache_decision="skip",
        cache_reason="lock-busy",
    ),
    _sc(
        29,
        "interrupted-publication",
        "a partial publication never becomes a readable entry",
        entry_readable=False,
    ),
    _sc(30, "empty-corpus", "zero runs is a valid sweep, not an error", run_count=0),
    _sc(
        31,
        "large-synthetic-corpus",
        "corpus-scale ingestion without a real-time dependency",
        run_count=24,
    ),
    _sc(
        32,
        "sensitive-canaries-every-field",
        "all 13 canary classes planted and structurally excluded",
        canary_class_count=13,
    ),
    _sc(
        33,
        "cli-leaf-collisions",
        "a run named like a leaf, and the `--` escape",
        collision_count=2,
    ),
)


def scenario(number_or_name: int | str) -> Scenario:
    """One scenario by number or by name. Raises `KeyError` rather than guessing."""

    for item in SCENARIOS:
        if item.number == number_or_name or item.name == number_or_name:
            return item
    raise KeyError(f"no such scenario: {number_or_name!r}")


def write_run(
    runs_root: Path,
    run_id: str,
    *,
    generation: str = "oc_runipd",
    queue: Sequence[Mapping[str, Any]] | None = None,
    optional: Mapping[str, Any] | None = None,
    state: Mapping[str, Any] | None = None,
    events: Sequence[str] | None = None,
    outcomes: Mapping[str, Any] | None = None,
    telemetry: Sequence[Mapping[str, Any]] | None = None,
    corrupt_state: bool = False,
    corrupt_event_line: bool = False,
    repo: str = "/repo",
    mtime: int | None = None,
) -> Path:
    """Write ONE deterministic run directory and return it.

    `mtime` (epoch seconds) is applied to every written file with `os.utime`, which is how this
    harness makes a mutation observable WITHOUT sleeping: freshness keys on size and mtime_ns, so a
    byte-identical rewrite needs an explicit stamp rather than a wall-clock wait.
    """

    run_dir = runs_root / run_id
    (run_dir / "outcomes").mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    (run_dir / "sessions").mkdir(exist_ok=True)

    if corrupt_state:
        # Truncated JSON: `build_run_facts` must degrade THIS run and no other.
        (run_dir / "state.json").write_text('{"run_id": "', encoding="utf-8")
    else:
        payload = (
            dict(state)
            if state is not None
            else core_state(
                run_id,
                generation=generation,
                queue=queue
                or [
                    _item(
                        position=1,
                        id6="aaa111",
                        attempts=[
                            _attempt(
                                1,
                                start=_BASE_CREATED,
                                end=_BASE_UPDATED,
                                tokens=_TOKENS,
                            )
                        ],
                    )
                ],
                optional=optional,
                repo=repo,
            )
        )
        (run_dir / "state.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    lines = (
        list(events)
        if events is not None
        else [
            json.dumps({"at": _BASE_CREATED, "event": "run-created"}),
            json.dumps({"at": _BASE_UPDATED, "event": "run-finished"}),
        ]
    )
    if corrupt_event_line:
        lines.insert(1, "{not json")
    (run_dir / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "execution-report.md").write_text("# report\n", encoding="utf-8")

    for name, body in (
        outcomes or {"01-aaa111.json": {"disposition": "executed"}}
    ).items():
        (run_dir / "outcomes" / name).write_text(
            json.dumps(body, sort_keys=True), encoding="utf-8"
        )

    if telemetry is not None:
        tele = run_dir / "telemetry"
        tele.mkdir(exist_ok=True)
        (tele / "invocation.jsonl").write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in telemetry),
            encoding="utf-8",
        )

    if mtime is not None:
        for path in sorted(run_dir.rglob("*")):
            os.utime(path, (mtime, mtime))
        os.utime(run_dir, (mtime, mtime))
    return run_dir


#: A fixed epoch stamp (2026-03-01T00:00:00Z) so a fresh write is reproducible.
BASE_MTIME = 1772323200


def build_corpus(runs_root: Path) -> dict[str, Path]:
    """Write the cross-generation corpus and return `label -> run directory`.

    FOUR GENERATIONS, which is what makes scenario 3 non-vacuous: the current driver, the synthetic
    Agy one, and BOTH legacy generations. Proportions are NOT reproduced (that would need 135
    directories to prove nothing extra); presence of each generation is.
    """

    runs_root.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    plan = (
        ("oc", "run-20260301T000000Z-0000001", "oc_runipd"),
        ("agy", "run-20260301T010000Z-0000002", "agy_runipd"),
        ("legacy_runipd", "run-20260301T020000Z-0000003", "runipd"),
        ("legacy_ipdrunner", "run-20260301T030000Z-0000004", "ipdrunner"),
    )
    for label, run_id, generation in plan:
        written[label] = write_run(
            runs_root, run_id, generation=generation, mtime=BASE_MTIME
        )
    return written


def corpus_manifest(scenarios: Iterable[Scenario] = SCENARIOS) -> dict[str, Any]:
    """The pasteable manifest V-01 requires: every scenario, its expectations and its labels.

    Carries `synthetic_generations` and the `agy` reason explicitly, so a reader of the manifest
    alone cannot mistake an Agy pass for cross-host corpus validation.
    """

    items = list(scenarios)
    return {
        "corpus_schema_version": CORPUS_SCHEMA_VERSION,
        "scenario_count": len(items),
        "generation_drivers": dict(GENERATION_DRIVERS),
        "synthetic_generations": dict(SYNTHETIC_GENERATIONS),
        "legacy_generations": ["runipd", "ipdrunner"],
        "canary_classes": sorted(_CANARY_FRAGMENTS),
        "expected_outcome_counts": {
            outcome: sum(1 for s in items if s.expected_outcome == outcome)
            for outcome in sorted({s.expected_outcome for s in items})
        },
        "scenarios": [s.to_dict() for s in items],
    }
