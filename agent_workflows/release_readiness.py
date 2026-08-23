"""Release-readiness aggregation producing a GO / NO-GO verdict WITHOUT publishing.

awoptimize Order 18 (`0zst62`) E-05.

This module aggregates the release gates into a single :class:`ReleaseReadinessReport`
carrying a GO / NO-GO :data:`VERDICT_GO` / :data:`VERDICT_NO_GO` verdict. It is the checkable
core of the final release-readiness review.

INVARIANT (airtight, cited to RELEASING.md / release-review Section 9): this module NEVER
tags, publishes, deploys, or pushes. It computes a decision ONLY. The actual release is a
separately authorized action outside this Set. There is no code path here that runs
``git tag`` / ``git push`` / a registry upload; :func:`assert_no_release_action` documents and
enforces that a caller's requested action is decision-only.

The gates it aggregates (each a :class:`GateResult`):

  * ``full_suite``            - the full test suite (``make test``); heavy, so the aggregator
                                accepts an injected result and the live run is driven by the
                                test harness / CI, not re-run inside a unit test.
  * ``leak_scan``             - the canonical leak scan (``aw sanitize --agent``), exit 0.
  * ``ipd_lint``              - all IPD lint phases (``aw ipd lint --all --agent``), exit 0.
  * ``generated_drift``       - the generated/compiler set matches (no drift).
  * ``docs_checks``           - documentation link/command/option checks pass.
  * ``workflow_disposition``  - every workflow has a complete disposition.
  * ``capability_freshness``  - capability evidence is present + unexpired (no stale claim).
  * ``benchmark_thresholds``  - the benchmark release invariants hold (0 critical escapes,
                                100% evidence validity).
  * ``changelog_versioning``  - a CHANGELOG entry + a resolvable version exist.
  * ``artifact_manifest``     - the release artifact manifest is present + consistent.
  * ``residual_risk``         - the residual-risk sign-off is recorded.

The leak-scan and IPD-lint gates actually SHELL OUT (per the IPD); the rest are asserted with
deterministic logic / fixtures where a live subprocess is too heavy.

Pure stdlib (D138); no runtime YAML (D139). Python 3.9+.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_workflows import benchmark_thresholds as bt

VERDICT_GO = "GO"
VERDICT_NO_GO = "NO-GO"

# Actions this review is FORBIDDEN from performing (a separately authorized release action).
FORBIDDEN_RELEASE_ACTIONS: Tuple[str, ...] = (
    "tag",
    "publish",
    "deploy",
    "push",
    "release",
    "upload",
)


class ReleaseActionForbiddenError(RuntimeError):
    """Raised if a caller asks the readiness review to perform a release-mutating action."""


def assert_no_release_action(action: str) -> None:
    """Refuse any release-mutating action. The review is decision-only (RELEASING.md / S9)."""
    if (action or "").strip().lower() in FORBIDDEN_RELEASE_ACTIONS:
        raise ReleaseActionForbiddenError(
            f"release-readiness review is decision-only and must not '{action}'; "
            "tag/publish/deploy/push is a separately authorized action (RELEASING.md, "
            "release-review Section 9)"
        )


# ==================================================================================================
# Gate + report records
# ==================================================================================================


@dataclass
class GateResult:
    """The outcome of one release gate."""

    name: str
    passed: bool
    detail: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "evidence": dict(self.evidence),
        }


@dataclass
class ReleaseReadinessReport:
    """Aggregate of every release gate + a GO / NO-GO verdict."""

    gates: Tuple[GateResult, ...]

    @property
    def verdict(self) -> str:
        return VERDICT_GO if all(g.passed for g in self.gates) else VERDICT_NO_GO

    @property
    def is_go(self) -> bool:
        return self.verdict == VERDICT_GO

    def failing_gates(self) -> List[str]:
        return [g.name for g in self.gates if not g.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "failing_gates": self.failing_gates(),
            "gates": [g.to_dict() for g in self.gates],
        }

    def render(self) -> str:
        """Render a human-readable GO / NO-GO report (no dashes; ASCII only)."""
        lines = [
            "# Release Readiness Report",
            "",
            f"Verdict: {self.verdict}",
            "",
            "| Gate | Result | Detail |",
            "|---|---|---|",
        ]
        for g in self.gates:
            lines.append(
                f"| {g.name} | {'PASS' if g.passed else 'FAIL'} | {g.detail} |"
            )
        if not self.is_go:
            lines.extend(["", f"Failing gates: {', '.join(self.failing_gates())}"])
        return "\n".join(lines)


# ==================================================================================================
# Individual gate checkers
# ==================================================================================================


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def gate_leak_scan(repo_root: Optional[Path] = None) -> GateResult:
    """Run the CANONICAL leak scan (``aw sanitize --agent``) and require exit 0.

    Uses ``python3 -m agent_workflows sanitize --agent`` so it works without ``aw`` on PATH.
    This is the same code path the ``aw sanitize`` CLI runs (no fork).
    """
    root = repo_root or _repo_root()
    proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "sanitize", "--agent"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    passed = proc.returncode == 0
    return GateResult(
        name="leak_scan",
        passed=passed,
        detail="aw sanitize --agent exit 0"
        if passed
        else f"leak scan exit {proc.returncode}",
        evidence={"returncode": proc.returncode},
    )


def gate_ipd_lint(repo_root: Optional[Path] = None) -> GateResult:
    """Run all IPD lint phases (``aw ipd lint --all --agent``) and require exit 0."""
    root = repo_root or _repo_root()
    proc = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "ipd", "lint", "--all", "--agent"],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    passed = proc.returncode == 0
    return GateResult(
        name="ipd_lint",
        passed=passed,
        detail="aw ipd lint --all --agent exit 0"
        if passed
        else f"ipd lint exit {proc.returncode}",
        evidence={"returncode": proc.returncode},
    )


def gate_full_suite(
    suite_passed: bool, counts: Optional[Dict[str, int]] = None
) -> GateResult:
    """The full test suite gate.

    The suite (``make test``) is too heavy to re-run inside a unit test, so the aggregator
    accepts the harness/CI result. ``suite_passed`` MUST come from a real run.
    """
    return GateResult(
        name="full_suite",
        passed=bool(suite_passed),
        detail="full suite green" if suite_passed else "full suite RED",
        evidence=dict(counts or {}),
    )


def gate_generated_drift(drift_files: Sequence[str] = ()) -> GateResult:
    """No generated/compiler drift: the drift set must be empty."""
    drift = list(drift_files)
    return GateResult(
        name="generated_drift",
        passed=not drift,
        detail="no generated/compiler drift"
        if not drift
        else f"{len(drift)} drifted file(s)",
        evidence={"drift_files": drift},
    )


def gate_docs_checks(doc_findings: Sequence[str] = ()) -> GateResult:
    """Documentation link/command/option checks pass: no findings."""
    findings = list(doc_findings)
    return GateResult(
        name="docs_checks",
        passed=not findings,
        detail="docs checks pass"
        if not findings
        else f"{len(findings)} doc finding(s)",
        evidence={"findings": findings},
    )


def gate_workflow_disposition(undispositioned: Sequence[str] = ()) -> GateResult:
    """Every workflow has a complete disposition: none left undispositioned."""
    undone = list(undispositioned)
    return GateResult(
        name="workflow_disposition",
        passed=not undone,
        detail="all workflows dispositioned"
        if not undone
        else f"{len(undone)} undispositioned",
        evidence={"undispositioned": undone},
    )


def gate_capability_freshness(stale_claims: Sequence[str] = ()) -> GateResult:
    """Capability evidence is fresh: no expired/stale supported claim.

    A stale supported claim is a release blocker (documented support must render only proven,
    unexpired evidence). An empty stale set passes.
    """
    stale = list(stale_claims)
    return GateResult(
        name="capability_freshness",
        passed=not stale,
        detail="no stale capability claims"
        if not stale
        else f"{len(stale)} stale claim(s)",
        evidence={"stale_claims": stale},
    )


def gate_benchmark_thresholds(
    policy: Optional[bt.ThresholdPolicy] = None,
) -> GateResult:
    """The benchmark release invariants hold for every risk class.

    Reuses :meth:`benchmark_thresholds.RiskThresholds.validate_invariants`: 0 critical escapes
    and 100% evidence validity are non-negotiable. If any threshold has been relaxed to violate
    an invariant, the gate fails.
    """
    pol = policy or bt.ThresholdPolicy()
    violations: List[str] = []
    for risk_class, thresh in pol.thresholds.items():
        try:
            thresh.validate_invariants()
        except bt.ThresholdError as exc:
            violations.append(f"{risk_class}: {exc}")
    return GateResult(
        name="benchmark_thresholds",
        passed=not violations,
        detail="benchmark release invariants hold"
        if not violations
        else f"{len(violations)} invariant violation(s)",
        evidence={"violations": violations},
    )


def gate_changelog_versioning(repo_root: Optional[Path] = None) -> GateResult:
    """A CHANGELOG entry and a resolvable version exist."""
    root = repo_root or _repo_root()
    changelog = root / "CHANGELOG.md"
    has_changelog = changelog.is_file() and "##" in changelog.read_text(
        encoding="utf-8", errors="replace"
    )
    version_ok = False
    version_str = ""
    try:
        from agent_workflows import versioning as vmod

        version_str = vmod.resolve_version(root)
        version_ok = bool(version_str)
    except Exception:
        # Fall back to the tracked VERSION file if git describe is unavailable.
        vfile = root / ".aw" / "system" / "VERSION"
        if vfile.is_file():
            version_str = vfile.read_text(encoding="utf-8").strip()
            version_ok = bool(version_str)
    passed = has_changelog and version_ok
    return GateResult(
        name="changelog_versioning",
        passed=passed,
        detail="changelog entry + resolvable version present"
        if passed
        else "missing changelog entry or version",
        evidence={"changelog": has_changelog, "version": version_str},
    )


def gate_artifact_manifest(
    manifest_present: bool = True, consistent: bool = True
) -> GateResult:
    """The release artifact manifest is present and consistent."""
    passed = bool(manifest_present) and bool(consistent)
    return GateResult(
        name="artifact_manifest",
        passed=passed,
        detail="artifact manifest present and consistent"
        if passed
        else "artifact manifest missing or inconsistent",
        evidence={"present": manifest_present, "consistent": consistent},
    )


def gate_residual_risk(signed_off: bool, signer: str = "") -> GateResult:
    """The residual-risk sign-off is recorded (a human attestation)."""
    passed = bool(signed_off) and bool(signer)
    return GateResult(
        name="residual_risk",
        passed=passed,
        detail=f"residual risk signed off by {signer}"
        if passed
        else "residual-risk sign-off missing",
        evidence={"signed_off": signed_off, "signer": signer},
    )


# ==================================================================================================
# Aggregation
# ==================================================================================================


def aggregate(gates: Sequence[GateResult]) -> ReleaseReadinessReport:
    """Aggregate gate results into a GO / NO-GO report. Performs NO release action."""
    return ReleaseReadinessReport(gates=tuple(gates))


def build_report(
    *,
    suite_passed: bool,
    suite_counts: Optional[Dict[str, int]] = None,
    drift_files: Sequence[str] = (),
    doc_findings: Sequence[str] = (),
    undispositioned: Sequence[str] = (),
    stale_claims: Sequence[str] = (),
    threshold_policy: Optional[bt.ThresholdPolicy] = None,
    manifest_present: bool = True,
    manifest_consistent: bool = True,
    residual_risk_signed: bool = False,
    residual_risk_signer: str = "",
    repo_root: Optional[Path] = None,
    run_subprocess_gates: bool = True,
) -> ReleaseReadinessReport:
    """Build the full readiness report.

    The leak-scan and IPD-lint gates SHELL OUT when ``run_subprocess_gates`` is True (the IPD
    requirement that these actually run). Everything else is deterministic from the passed
    inputs. This function NEVER performs a release action.
    """
    gates: List[GateResult] = [
        gate_full_suite(suite_passed, suite_counts),
    ]
    if run_subprocess_gates:
        gates.append(gate_leak_scan(repo_root))
        gates.append(gate_ipd_lint(repo_root))
    gates.extend(
        [
            gate_generated_drift(drift_files),
            gate_docs_checks(doc_findings),
            gate_workflow_disposition(undispositioned),
            gate_capability_freshness(stale_claims),
            gate_benchmark_thresholds(threshold_policy),
            gate_changelog_versioning(repo_root),
            gate_artifact_manifest(manifest_present, manifest_consistent),
            gate_residual_risk(residual_risk_signed, residual_risk_signer),
        ]
    )
    return aggregate(gates)


__all__ = [
    "VERDICT_GO",
    "VERDICT_NO_GO",
    "FORBIDDEN_RELEASE_ACTIONS",
    "ReleaseActionForbiddenError",
    "assert_no_release_action",
    "GateResult",
    "ReleaseReadinessReport",
    "gate_leak_scan",
    "gate_ipd_lint",
    "gate_full_suite",
    "gate_generated_drift",
    "gate_docs_checks",
    "gate_workflow_disposition",
    "gate_capability_freshness",
    "gate_benchmark_thresholds",
    "gate_changelog_versioning",
    "gate_artifact_manifest",
    "gate_residual_risk",
    "aggregate",
    "build_report",
]
