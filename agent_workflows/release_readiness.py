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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from agent_workflows import benchmark_thresholds as bt
from agent_workflows.runner_shared import pinned_child_env, pinned_module_argv

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
        if not self.gates:
            return VERDICT_NO_GO
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
            failing = self.failing_gates()
            detail = (
                ", ".join(failing) if failing else "empty gate set (no gates evaluated)"
            )
            lines.extend(["", f"Failing gates: {detail}"])
        return "\n".join(lines)


# ==================================================================================================
# Individual gate checkers
# ==================================================================================================


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def gate_leak_scan(repo_root: Optional[Path] = None) -> GateResult:
    """Run the CANONICAL leak scan (``aw sanitize --agent``) and require exit 0.

    Uses :func:`runner_shared.pinned_module_argv` (-c bootstrap) and
    :func:`runner_shared.pinned_child_env` (plan af7i6p) so it works without ``aw`` on
    PATH and runs the runner's own tooling rather than any package in the target tree.
    This is the same code path the ``aw sanitize`` CLI runs (no fork).

    The ``repo_root`` argument is caller-supplied. Without the pin, Python would seed
    sys.path[0] from cwd, causing the gate to execute the ``agent_workflows`` package
    found in that tree and report its exit code as the release verdict. Child stdin is
    denied via ``subprocess.DEVNULL``. Enforced behaviorally by
    ``tests/test_release_readiness_child_pin.py``.
    """
    root = repo_root or _repo_root()
    proc = subprocess.run(
        pinned_module_argv(["sanitize", "--agent"]),
        cwd=str(root),
        env=pinned_child_env(),
        stdin=subprocess.DEVNULL,
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
    """Run all IPD lint phases (``aw ipd lint --all --agent``) and require exit 0.

    Uses :func:`runner_shared.pinned_module_argv` (-c bootstrap) and
    :func:`runner_shared.pinned_child_env` (plan af7i6p) to execute the runner's own
    tooling. The ``repo_root`` argument is caller-supplied. Without the pin, Python would
    seed sys.path[0] from cwd, causing the gate to execute the ``agent_workflows``
    package found in that tree and report its exit code as the release verdict. Child
    stdin is denied via ``subprocess.DEVNULL``. Enforced behaviorally by
    ``tests/test_release_readiness_child_pin.py``.
    """
    root = repo_root or _repo_root()
    proc = subprocess.run(
        pinned_module_argv(["ipd", "lint", "--all", "--agent"]),
        cwd=str(root),
        env=pinned_child_env(),
        stdin=subprocess.DEVNULL,
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
    suite_passed: Optional[bool], counts: Optional[Dict[str, int]] = None
) -> GateResult:
    """The full test suite gate.

    The suite (``make test``) is too heavy to re-run inside a unit test, so the aggregator
    accepts the harness/CI result. ``suite_passed`` MUST come from a real run. When
    ``suite_passed`` is None, fails closed with "full suite result not supplied" rather
    than claiming a red suite that was never run.
    """
    if suite_passed is None:
        ev: Dict[str, Any] = dict(counts or {})
        ev["supplied"] = False
        return GateResult(
            name="full_suite",
            passed=False,
            detail="full suite result not supplied",
            evidence=ev,
        )
    return GateResult(
        name="full_suite",
        passed=bool(suite_passed),
        detail="full suite green" if suite_passed else "full suite RED",
        evidence=dict(counts or {}),
    )


def gate_generated_drift(
    drift_files: Optional[Sequence[str]] = None,
    repo_root: Optional[Path] = None,
) -> GateResult:
    """No generated/compiler drift: the drift set must be empty.

    When ``drift_files`` is None (the default), computes drift across canonical
    workflow packages under ``.aw/system/workflows`` via :mod:`workflow_loader`,
    :mod:`workflow_compiler`, and :func:`workflow_cli._compute_drift`. Explicit
    injection (including an empty sequence) bypasses filesystem inspection.
    """
    if drift_files is not None:
        drift = [str(f) for f in drift_files]
        return GateResult(
            name="generated_drift",
            passed=not drift,
            detail="no generated/compiler drift"
            if not drift
            else f"{len(drift)} drifted file(s)",
            evidence={"drift_files": drift},
        )

    root = repo_root or _repo_root()
    wf_rel = ".aw/system/workflows"
    wf_dir = root / ".aw" / "system" / "workflows"
    if not wf_dir.is_dir():
        return GateResult(
            name="generated_drift",
            passed=False,
            detail=f"workflow packages tree missing or not a directory: {wf_rel}",
            evidence={"missing": True, "path": wf_rel, "drift_files": []},
        )

    try:
        from agent_workflows import workflow_compiler, workflow_loader
        from agent_workflows.workflow_cli import _compute_drift

        yaml_paths = sorted(wf_dir.glob("*/workflow.yaml"))
        packages_checked = len(yaml_paths)
        if packages_checked == 0:
            return GateResult(
                name="generated_drift",
                passed=True,
                detail="no canonical workflow packages to check",
                evidence={"packages_checked": 0, "drift_files": []},
            )

        drift = []
        for yp in yaml_paths:
            pkg_dir = yp.parent
            pkg_name = pkg_dir.name
            res = workflow_loader.load_package(pkg_dir)
            if not res.ok or res.ir is None:
                if res.findings:
                    for f in res.findings:
                        drift.append(f"{pkg_name}: load failed: {f.code}")
                else:
                    drift.append(f"{pkg_name}: load failed: unknown")
                continue

            compiled = workflow_compiler.compile_workflow(res.ir)
            expected = workflow_compiler.render_generated_files(compiled)
            diffs = _compute_drift(Path(res.ir["source_root"]), expected)
            for kind, rel in diffs:
                drift.append(f"{pkg_name}/{rel}: {kind}")

        passed = not drift
        return GateResult(
            name="generated_drift",
            passed=passed,
            detail="no generated/compiler drift"
            if passed
            else f"{len(drift)} drifted file(s)",
            evidence={
                "packages_checked": packages_checked,
                "drift_files": drift,
            },
        )
    except Exception as exc:
        return GateResult(
            name="generated_drift",
            passed=False,
            detail=f"generated drift check could not run: {type(exc).__name__}",
            evidence={"error": type(exc).__name__, "drift_files": []},
        )


def gate_docs_checks(
    doc_findings: Optional[Sequence[str]] = None,
    repo_root: Optional[Path] = None,
) -> GateResult:
    """Documentation link/command/option checks pass: no findings.

    When ``doc_findings`` is None (the default), computes the findings live from
    ``docs/`` under ``repo_root`` via :func:`docs_check.check_docs_dir`. Explicit
    injection (including an empty sequence) bypasses filesystem inspection.
    """
    if doc_findings is not None:
        findings = [str(f) for f in doc_findings]
        passed = not findings
        return GateResult(
            name="docs_checks",
            passed=passed,
            detail="docs checks pass" if passed else f"{len(findings)} doc finding(s)",
            evidence={"findings": findings},
        )

    root = repo_root or _repo_root()
    docs_dir = root / "docs"
    if not docs_dir.is_dir():
        return GateResult(
            name="docs_checks",
            passed=False,
            detail="docs tree missing or not a directory: docs",
            evidence={"missing": True, "path": "docs", "findings": []},
        )

    try:
        from agent_workflows import docs_check

        raw_findings = docs_check.check_docs_dir(docs_dir)
    except Exception as exc:
        return GateResult(
            name="docs_checks",
            passed=False,
            detail=f"docs check could not run: {type(exc).__name__}",
            evidence={"error": type(exc).__name__, "findings": []},
        )

    findings = [str(f) for f in raw_findings]
    passed = not findings
    return GateResult(
        name="docs_checks",
        passed=passed,
        detail="docs checks pass" if passed else f"{len(findings)} doc finding(s)",
        evidence={"findings": findings},
    )


def gate_workflow_disposition(
    undispositioned: Optional[Sequence[str]] = None,
    repo_root: Optional[Path] = None,
) -> GateResult:
    """Every workflow has a complete disposition: none left undispositioned.

    When ``undispositioned`` is None (the default), computes the undispositioned
    set from :func:`migration_inventory.build_inventory` against ``.aw/system/workflows``.
    Explicit injection (including an empty sequence) bypasses filesystem inspection.
    """
    if undispositioned is not None:
        undone = [str(f) for f in undispositioned]
        return GateResult(
            name="workflow_disposition",
            passed=not undone,
            detail="all workflows dispositioned"
            if not undone
            else f"{len(undone)} undispositioned",
            evidence={"undispositioned": undone},
        )

    root = repo_root or _repo_root()
    wf_rel = ".aw/system/workflows"
    wf_dir = root / ".aw" / "system" / "workflows"
    if not wf_dir.is_dir():
        return GateResult(
            name="workflow_disposition",
            passed=False,
            detail=f"workflow packages tree missing or not a directory: {wf_rel}",
            evidence={"missing": True, "path": wf_rel, "undispositioned": []},
        )

    try:
        from agent_workflows import migration_inventory

        try:
            result = migration_inventory.build_inventory(wf_dir)
        except migration_inventory.InventoryError as err:
            undone = [str(err)]
            return GateResult(
                name="workflow_disposition",
                passed=False,
                detail=f"{len(undone)} undispositioned",
                evidence={"undispositioned": undone},
            )

        undone = [str(f) for f in result.findings]
        passed = not undone
        return GateResult(
            name="workflow_disposition",
            passed=passed,
            detail="all workflows dispositioned"
            if passed
            else f"{len(undone)} undispositioned",
            evidence={
                "undispositioned": undone,
                "dispositions": len(result.dispositions),
            },
        )
    except (SystemExit, Exception) as exc:
        return GateResult(
            name="workflow_disposition",
            passed=False,
            detail=f"workflow disposition check could not run: {type(exc).__name__}",
            evidence={"error": type(exc).__name__, "undispositioned": []},
        )


def gate_capability_freshness(
    stale_claims: Optional[Sequence[str]] = None,
    repo_root: Optional[Path] = None,
) -> GateResult:
    """Capability evidence is fresh: no expired/stale supported claim.

    When ``stale_claims`` is None (the default), loads the host matrix from
    ``.aw/system/workflows/conformance/tools/host_matrix.json`` under ``repo_root``,
    evaluating every claimed support boolean via :class:`HostCapabilityRegistry`.
    Explicit injection (including an empty sequence) bypasses filesystem inspection.
    """
    if stale_claims is not None:
        stale = [str(f) for f in stale_claims]
        return GateResult(
            name="capability_freshness",
            passed=not stale,
            detail="no stale capability claims"
            if not stale
            else f"{len(stale)} stale claim(s)",
            evidence={"stale_claims": stale},
        )

    root = repo_root or _repo_root()
    matrix_rel = ".aw/system/workflows/conformance/tools/host_matrix.json"
    matrix_file = (
        root
        / ".aw"
        / "system"
        / "workflows"
        / "conformance"
        / "tools"
        / "host_matrix.json"
    )
    if not matrix_file.is_file():
        return GateResult(
            name="capability_freshness",
            passed=False,
            detail=f"capability matrix missing: {matrix_rel}",
            evidence={"missing": True, "path": matrix_rel, "stale_claims": []},
        )

    try:
        from agent_workflows import host_capability_registry as hcr

        data = hcr.load_host_matrix(matrix_file)
        reg = hcr.HostCapabilityRegistry()
        reg.migrate_from_static_matrix(data)

        stale = []
        claims_checked = 0
        hosts_dict = data.get("hosts", {}) if isinstance(data, dict) else {}
        for host in sorted(hosts_dict.keys()):
            host_info = hosts_dict[host]
            if not isinstance(host_info, dict):
                continue
            for feat in sorted(host_info.keys()):
                feat_val = host_info[feat]
                if isinstance(feat_val, dict) and feat_val.get("supported") is True:
                    claims_checked += 1
                    eval_res = reg.query_capability(
                        host=host, exact_version="1.0.0", feature=feat
                    )
                    if not eval_res.is_supported:
                        reason = (
                            eval_res.reasons[0] if eval_res.reasons else "unverified"
                        )
                        stale.append(f"{host}:{feat}: {reason}")

        passed = not stale
        return GateResult(
            name="capability_freshness",
            passed=passed,
            detail="no stale capability claims"
            if passed
            else f"{len(stale)} stale claim(s)",
            evidence={
                "stale_claims": stale,
                "claims_checked": claims_checked,
            },
        )
    except Exception as exc:
        return GateResult(
            name="capability_freshness",
            passed=False,
            detail=f"capability freshness check could not run: {type(exc).__name__}",
            evidence={"error": type(exc).__name__, "stale_claims": []},
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
    """A CHANGELOG entry and a resolvable version exist (rejecting 'unknown')."""
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
        version_ok = bool(version_str and version_str != "unknown")
    except Exception:
        # Fall back to the tracked VERSION file if git describe is unavailable.
        vfile = root / ".aw" / "system" / "VERSION"
        if vfile.is_file():
            version_str = vfile.read_text(encoding="utf-8").strip()
            version_ok = bool(version_str and version_str != "unknown")
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
    manifest_present: Optional[bool] = None,
    consistent: Optional[bool] = None,
    repo_root: Optional[Path] = None,
) -> GateResult:
    """The release artifact manifest is present and consistent."""
    if manifest_present is not None and consistent is not None:
        passed = bool(manifest_present) and bool(consistent)
        return GateResult(
            name="artifact_manifest",
            passed=passed,
            detail="artifact manifest present and consistent"
            if passed
            else "artifact manifest missing or inconsistent",
            evidence={
                "present": bool(manifest_present),
                "consistent": bool(consistent),
            },
        )

    import re
    from agent_workflows import agent_schema

    root = repo_root or _repo_root()
    manifest_rel = ".aw/system/workflows/index.md"
    manifest_file = root / ".aw" / "system" / "workflows" / "index.md"

    problems: List[str] = []
    workflows_checked = 0

    if not manifest_file.is_file():
        comp_present = False
        comp_consistent = False
        problems.append(f"artifact manifest missing: {manifest_rel}")
    else:
        comp_present = True
        try:
            manifest_text = manifest_file.read_text(encoding="utf-8")
            from agent_workflows import engine

            workflows = engine.parse_manifest(manifest_file.parent)
            workflows_checked = len(workflows)
        except (SystemExit, Exception) as exc:
            comp_consistent = False
            msg = f"manifest parse failed: {type(exc).__name__}"
            if isinstance(exc, SystemExit):
                msg += f": {exc}"
            problems.append(msg)
        else:
            seen_commands: set[str] = set()
            for w in workflows:
                if w.command in seen_commands:
                    problems.append(f"duplicate command: {w.command}")
                seen_commands.add(w.command)

                for field_name, rel in (("body", w.body), ("lens", w.lens)):
                    if field_name == "body" and not rel:
                        problems.append(f"{w.command}: empty body path")
                    elif rel:
                        p = Path(rel)
                        if p.is_absolute() or bool(p.drive) or ".." in p.parts:
                            problems.append(
                                f"{w.command}: invalid {field_name} path: {agent_schema.redact_home_paths(rel)}"
                            )
                        else:
                            candidate = root / rel
                            is_valid = False
                            try:
                                if (
                                    candidate.is_file()
                                    and candidate.resolve().is_relative_to(
                                        root.resolve()
                                    )
                                ):
                                    is_valid = True
                            except (OSError, ValueError):
                                is_valid = False
                            if not is_valid:
                                problems.append(
                                    f"{w.command}: missing {field_name} file: {rel}"
                                )

            m_comment = re.search(
                r"<!--\s*WORKFLOWS-VERSION:\s*([^\s>]+)\s*-->", manifest_text
            )
            m_line = re.search(r"(?m)^Version:\s*`([^`]+)`", manifest_text)
            comment_v = m_comment.group(1) if m_comment else None
            line_v = m_line.group(1) if m_line else None

            if comment_v is not None and line_v is not None and comment_v != line_v:
                problems.append(
                    f"index.md version stamps disagree: comment={comment_v} vs line={line_v}"
                )

            unique_stamps = dict.fromkeys(
                [v for v in (comment_v, line_v) if v is not None]
            )
            if unique_stamps:
                version_file = root / ".aw" / "system" / "VERSION"
                version_file_rel = ".aw/system/VERSION"
                version_text: Optional[str] = None
                if version_file.is_file():
                    try:
                        version_text = version_file.read_text(encoding="utf-8").strip()
                    except Exception:
                        version_text = None

                for stamp_v in unique_stamps:
                    if version_text is None:
                        problems.append(
                            f"{version_file_rel} missing but index.md carries version stamp {stamp_v}"
                        )
                    elif version_text != stamp_v:
                        problems.append(
                            f"version stamp mismatch: index.md has {stamp_v} but {version_file_rel} has {version_text}"
                        )

            comp_consistent = not problems

    present_val = comp_present if manifest_present is None else bool(manifest_present)
    consistent_val = (
        (comp_consistent and present_val) if consistent is None else bool(consistent)
    )
    passed = present_val and consistent_val
    detail = (
        "artifact manifest present and consistent"
        if passed
        else (
            f"artifact manifest missing or inconsistent ({len(problems)} problem(s))"
            if problems
            else "artifact manifest missing or inconsistent"
        )
    )

    return GateResult(
        name="artifact_manifest",
        passed=passed,
        detail=detail,
        evidence={
            "present": present_val,
            "consistent": consistent_val,
            "workflows_checked": workflows_checked,
            "problems": problems,
        },
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
    """Aggregate gate results into a GO / NO-GO report (empty gates yield NO-GO). Performs NO release action."""
    return ReleaseReadinessReport(gates=tuple(gates))


def build_report(
    *,
    suite_passed: Optional[bool],
    suite_counts: Optional[Dict[str, int]] = None,
    drift_files: Optional[Sequence[str]] = None,
    doc_findings: Optional[Sequence[str]] = None,
    undispositioned: Optional[Sequence[str]] = None,
    stale_claims: Optional[Sequence[str]] = None,
    threshold_policy: Optional[bt.ThresholdPolicy] = None,
    manifest_present: Optional[bool] = None,
    manifest_consistent: Optional[bool] = None,
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
            gate_generated_drift(drift_files, repo_root=repo_root),
            gate_docs_checks(doc_findings, repo_root=repo_root),
            gate_workflow_disposition(undispositioned, repo_root=repo_root),
            gate_capability_freshness(stale_claims, repo_root=repo_root),
            gate_benchmark_thresholds(threshold_policy),
            gate_changelog_versioning(repo_root),
            gate_artifact_manifest(
                manifest_present, manifest_consistent, repo_root=repo_root
            ),
            gate_residual_risk(residual_risk_signed, residual_risk_signer),
        ]
    )
    return aggregate(gates)


def run_readiness(args: Any) -> int:
    """``aw releases readiness``: render the read-only GO / NO-GO release-readiness report."""
    import sys

    from agent_workflows.project_context import (
        nonsurveyable_root_refusal,
        resolve_verb_repo_root,
    )
    from agent_workflows.renderers import get_renderer
    from agent_workflows.result_types import (
        CommandResult,
        Diagnostic,
        NextAction,
        select_output,
    )

    repo_root = resolve_verb_repo_root(getattr(args, "dir", None))
    ctx = select_output(args)
    explicit_dir = bool(getattr(args, "dir", None))
    refusal = nonsurveyable_root_refusal(
        "releases readiness", repo_root, explicit_dir=explicit_dir
    )
    if not refusal.may_proceed:
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="releases readiness",
                status="cannot-run",
                exit_code=2,
                summary=refusal.summary,
                next_actions=(
                    [
                        NextAction(
                            command=refusal.next_action_command,
                            description=refusal.next_action_description,
                        )
                    ]
                    if refusal.next_action is not None
                    else []
                ),
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write((refusal.human_message or "") + "\n")
        return 2

    if getattr(args, "suite_passed", False):
        suite_passed: Optional[bool] = True
    elif getattr(args, "suite_failed", False):
        suite_passed = False
    else:
        suite_passed = None

    raw_signer = getattr(args, "residual_risk_signer", None)
    signer = str(raw_signer).strip() if raw_signer else ""

    try:
        report = build_report(
            suite_passed=suite_passed,
            residual_risk_signed=bool(signer),
            residual_risk_signer=signer or "",
            repo_root=repo_root,
            run_subprocess_gates=True,
        )
    except Exception as exc:
        msg = (
            f"aw releases readiness: could not build readiness report: "
            f"{type(exc).__name__}"
        )
        if ctx.is_agent or ctx.is_json:
            res = CommandResult(
                command="releases readiness",
                status="cannot-run",
                exit_code=2,
                summary=msg,
                verified=False,
                complete=False,
            )
            return get_renderer(ctx).emit(res, ctx)
        sys.stderr.write(msg + "\n")
        return 2

    is_go = report.is_go
    exit_code = 0 if is_go else 1
    failing = report.failing_gates()
    summary = "Verdict: GO" if is_go else f"Verdict: NO-GO ({', '.join(failing)})"

    if ctx.is_agent or ctx.is_json:
        diagnostics = [
            Diagnostic(
                location=g.name,
                rule=f"readiness.{g.name}",
                detail=g.detail,
                severity="error",
            )
            for g in report.gates
            if not g.passed
        ]
        res = CommandResult(
            command="releases readiness",
            status="clean" if is_go else "findings",
            exit_code=exit_code,
            summary=summary,
            diagnostics=diagnostics,
            data=report.to_dict(),
        )
        return get_renderer(ctx).emit(res, ctx)

    sys.stdout.write(report.render() + "\n")
    needs_hint = any(
        (g.name == "full_suite" and "not supplied" in g.detail)
        or (g.name == "residual_risk" and "sign-off missing" in g.detail)
        for g in report.gates
        if not g.passed
    )
    if needs_hint:
        sys.stderr.write(
            "Hint: pass --suite-passed or --suite-failed for full_suite, and "
            "--residual-risk-signer <name> for residual_risk.\n"
        )
    return exit_code


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
    "run_readiness",
]
