"""Security hardening for the new execution + host-integration attack surface.

awoptimize Order 18 (`0zst62`) E-03.

This module hardens and PROVES the security boundaries of the new execution runtime
(Orders 03-06) and host integration (Orders 09-13) surface. It does NOT invent new
scanners: leak/secret detection REUSES the repo's canonical tooling:

  * ``agent_workflows.leak_sanitizer`` (the ``aw sanitize`` / ``aw check-local-leaks``
    leak sanitizer), and
  * ``.aw/system/workflows/assess/tools/scan_secrets.py`` (the secret scanner).

The eight boundary properties (E-03) each get one deterministic, falsifiable checker
that returns a :class:`BoundaryResult` (``ok`` plus a machine-readable ``reason``):

  1. ``check_local_server_binding``  - local headless servers bind loopback + require auth.
  2. ``check_external_file_access``  - external files are consented AND path-contained.
  3. ``check_skill_least_privilege`` - a skill entry point carries no inlined authority.
  4. ``check_evidence_redaction``    - evidence is redacted before it lands (reuses the
                                        run ledger RedactionPolicy) AND passes the
                                        canonical leak/secret scanners.
  5. ``check_real_home_excluded``    - host probes refuse the real HOME (reuses the
                                        capability-registry isolation guard).
  6. ``check_untrusted_text_isolated`` - repository/tool/inter-agent text is treated as
                                          DATA, never executed as instructions.
  7. ``check_destructive_tool_gated`` - destructive tools require a human gate (reuses the
                                         role contracts: only ``human`` may consent).
  8. ``scan_artifact_for_leaks`` / ``scan_text_for_secrets`` - thin adapters over the
     EXISTING sanitizer + secret scanner (no fork).

Pure stdlib (D138); no runtime YAML (D139). Python 3.9+.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from agent_workflows import host_adapters as ha
from agent_workflows import host_capability_registry as hcr
from agent_workflows import leak_sanitizer as ls
from agent_workflows import verify_roles as vr
from agent_workflows.run_ledger_store import RedactionPolicy

# ==================================================================================================
# Result records
# ==================================================================================================


@dataclass
class BoundaryResult:
    """The outcome of a single security-boundary check.

    ``ok`` is True only when the boundary HOLDS (a fail-closed / refusal path). ``reason``
    is a machine-readable explanation; ``evidence`` carries any structured findings.
    """

    boundary: str
    ok: bool
    reason: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "boundary": self.boundary,
            "ok": self.ok,
            "reason": self.reason,
            "evidence": dict(self.evidence),
        }


# Boundary identifiers (stable machine strings).
BOUNDARY_SERVER_BINDING = "local_server_binding"
BOUNDARY_EXTERNAL_FILE = "external_file_access"
BOUNDARY_SKILL_PRIVILEGE = "skill_least_privilege"
BOUNDARY_EVIDENCE_REDACTION = "evidence_redaction"
BOUNDARY_REAL_HOME = "real_home_excluded"
BOUNDARY_UNTRUSTED_TEXT = "untrusted_text_isolated"
BOUNDARY_DESTRUCTIVE_GATE = "destructive_tool_gated"

ALL_BOUNDARIES: Tuple[str, ...] = (
    BOUNDARY_SERVER_BINDING,
    BOUNDARY_EXTERNAL_FILE,
    BOUNDARY_SKILL_PRIVILEGE,
    BOUNDARY_EVIDENCE_REDACTION,
    BOUNDARY_REAL_HOME,
    BOUNDARY_UNTRUSTED_TEXT,
    BOUNDARY_DESTRUCTIVE_GATE,
)

# Loopback / non-routable addresses a local headless server MAY bind to.
LOOPBACK_HOSTS: frozenset = frozenset(("127.0.0.1", "::1", "localhost", "127.0.0.0/8"))


# ==================================================================================================
# 1. Local server binding: loopback + authenticated
# ==================================================================================================


def check_local_server_binding(
    bind_host: str,
    requires_auth: bool,
    auth_token: str = "",
) -> BoundaryResult:
    """A local headless server MUST bind a loopback address AND require authentication.

    Rationale: local headless servers may be unauthenticated by DEFAULT; the new host
    integration must bind loopback and require auth. A bind to ``0.0.0.0`` / a routable
    address, or an unauthenticated endpoint, FAILS closed.
    """
    normalized = (bind_host or "").strip().lower()
    is_loopback = normalized in LOOPBACK_HOSTS or normalized.startswith("127.")
    if not is_loopback:
        return BoundaryResult(
            boundary=BOUNDARY_SERVER_BINDING,
            ok=False,
            reason=(
                f"server bound to non-loopback address '{bind_host}'; a local headless "
                "server must bind 127.0.0.1/::1/localhost only"
            ),
            evidence={"bind_host": bind_host},
        )
    if not requires_auth or not auth_token:
        return BoundaryResult(
            boundary=BOUNDARY_SERVER_BINDING,
            ok=False,
            reason="loopback server exposes an unauthenticated endpoint; auth token required",
            evidence={"bind_host": bind_host, "requires_auth": requires_auth},
        )
    return BoundaryResult(
        boundary=BOUNDARY_SERVER_BINDING,
        ok=True,
        reason="server binds loopback and requires an auth token",
        evidence={"bind_host": bind_host},
    )


# ==================================================================================================
# 2. External file access: consented + contained
# ==================================================================================================


def check_external_file_access(
    target_path: Path | str,
    base_dir: Path | str,
    consented: bool,
) -> BoundaryResult:
    """An external file access MUST be explicitly consented AND contained under ``base_dir``.

    Reuses the capability-registry containment guard (:func:`host_capability_registry.assert_contained`),
    so a path that escapes the sandbox base fails closed, and an un-consented access is refused
    before any read.
    """
    if not consented:
        return BoundaryResult(
            boundary=BOUNDARY_EXTERNAL_FILE,
            ok=False,
            reason="external file access refused: no explicit operator consent recorded",
            evidence={"target": str(target_path)},
        )
    try:
        contained = hcr.assert_contained(target_path, base_dir)
    except hcr.SafetyError as exc:
        return BoundaryResult(
            boundary=BOUNDARY_EXTERNAL_FILE,
            ok=False,
            reason=f"external file access escapes the consented base: {exc}",
            evidence={"target": str(target_path), "base": str(base_dir)},
        )
    return BoundaryResult(
        boundary=BOUNDARY_EXTERNAL_FILE,
        ok=True,
        reason="external file access consented and contained under base",
        evidence={"target": str(contained), "base": str(Path(base_dir).resolve())},
    )


# ==================================================================================================
# 3. Skill least privilege: no inlined authority
# ==================================================================================================


def check_skill_least_privilege(
    package: ha.SkillPackage,
    canonical_body_text: str = "",
) -> BoundaryResult:
    """A generated skill entry point MUST be a least-privilege pointer, not an inlined authority.

    Reuses :func:`host_adapters.check_authority_not_inlined` and
    :func:`host_adapters.validate_skill_package`. A skill whose main file inlines the canonical
    authoritative body (rather than referencing it) or overflows the entry-point budget fails
    closed.
    """
    authority_findings = ha.check_authority_not_inlined(package, canonical_body_text)
    validation_findings = ha.validate_skill_package(package)
    findings = list(authority_findings) + list(validation_findings)
    if findings:
        return BoundaryResult(
            boundary=BOUNDARY_SKILL_PRIVILEGE,
            ok=False,
            reason="skill entry point violates least privilege",
            evidence={"findings": findings},
        )
    return BoundaryResult(
        boundary=BOUNDARY_SKILL_PRIVILEGE,
        ok=True,
        reason="skill entry point is a least-privilege pointer with no inlined authority",
        evidence={"main_file_bytes": package.main_file_bytes()},
    )


# ==================================================================================================
# 4. Evidence redaction (reuses the ledger RedactionPolicy + canonical scanners)
# ==================================================================================================


def default_redaction_policy(
    extra_patterns: Sequence[str] = (),
    extra_keys: Sequence[str] = (),
) -> RedactionPolicy:
    """A redaction policy that masks common secret-bearing keys before evidence lands.

    Reuses the run ledger :class:`RedactionPolicy` (Order 03/04); does not fork it.
    """
    keys = [
        "authorization",
        "auth_token",
        "token",
        "api_key",
        "apikey",
        "secret",
        "password",
        "bearer",
        *extra_keys,
    ]
    return RedactionPolicy(patterns=list(extra_patterns), sensitive_keys=keys)


def check_evidence_redaction(
    payload: Mapping[str, Any],
    policy: Optional[RedactionPolicy] = None,
    repo_root: Optional[Path] = None,
) -> BoundaryResult:
    """Evidence MUST be redacted before it lands AND MUST NOT leak secrets/identifiers.

    Two-stage: (1) apply the ledger RedactionPolicy to the payload, then (2) run the CANONICAL
    leak sanitizer (:func:`leak_sanitizer.scan_text`) over the redacted text. If the redacted
    evidence still trips a leak rule, the boundary fails closed.
    """
    pol = policy or default_redaction_policy()
    redacted, _ = pol.redact(payload)
    text = _flatten(redacted)
    root = repo_root or Path(__file__).resolve().parent.parent
    ruleset = ls.build_ruleset(root)
    findings = ls.scan_text(text, "evidence", ruleset)
    fail_findings = [f for f in findings if getattr(f, "severity", "fail") == "fail"]
    if fail_findings:
        return BoundaryResult(
            boundary=BOUNDARY_EVIDENCE_REDACTION,
            ok=False,
            reason="redacted evidence still trips the canonical leak sanitizer",
            evidence={"findings": [_finding_repr(f) for f in fail_findings]},
        )
    return BoundaryResult(
        boundary=BOUNDARY_EVIDENCE_REDACTION,
        ok=True,
        reason="evidence redacted and clean under the canonical leak sanitizer",
        evidence={"redacted": redacted.get("redacted", False)},
    )


def _flatten(obj: Any) -> str:
    """Flatten a nested mapping/sequence into a single scannable text blob."""
    parts: List[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for k, v in value.items():
                parts.append(str(k))
                walk(v)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
        else:
            parts.append(str(value))

    walk(obj)
    return "\n".join(parts)


def _finding_repr(f: Any) -> str:
    rule = getattr(f, "rule", getattr(f, "name", "?"))
    where = getattr(f, "where", getattr(f, "location", "?"))
    return f"{rule}@{where}"


# ==================================================================================================
# 5. Real HOME excluded from probes (reuses capability-registry isolation guard)
# ==================================================================================================


def check_real_home_excluded(base_dir: Path | str) -> BoundaryResult:
    """A host probe MUST run against an isolated base, never the real HOME.

    Reuses :func:`host_capability_registry.assert_isolated_base`, which refuses a base equal
    to (or a parent of) the real home directory.
    """
    try:
        resolved = hcr.assert_isolated_base(base_dir)
    except hcr.SafetyError as exc:
        return BoundaryResult(
            boundary=BOUNDARY_REAL_HOME,
            ok=False,
            reason=f"probe base rejected by isolation guard: {exc}",
            evidence={"base": str(base_dir)},
        )
    return BoundaryResult(
        boundary=BOUNDARY_REAL_HOME,
        ok=True,
        reason="probe base is isolated from the real HOME",
        evidence={"base": str(resolved)},
    )


# ==================================================================================================
# 6. Untrusted text isolated as data
# ==================================================================================================

# Markers a prompt-injection attempt in untrusted repository/tool/inter-agent text would use to
# try to escalate from DATA into INSTRUCTIONS. Detection here means the text is refused as an
# instruction source; it is still safe to READ as data.
_INJECTION_MARKERS: Tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard the above",
    "you are now",
    "system prompt:",
    "run the following command",
    "execute this",
    "delete all",
    "exfiltrate",
    "reveal your instructions",
    "override the",
)


def classify_untrusted_text(text: str) -> Tuple[bool, Tuple[str, ...]]:
    """Return (contains_injection_attempt, matched_markers).

    Purely a classifier; it does NOT execute anything. The security posture is that untrusted
    text is ALWAYS data, so a positive match simply flags an injection attempt for logging.
    """
    lowered = (text or "").lower()
    hits = tuple(m for m in _INJECTION_MARKERS if m in lowered)
    return (bool(hits), hits)


def check_untrusted_text_isolated(
    text: str,
    treated_as_instructions: bool,
) -> BoundaryResult:
    """Untrusted repository/tool/inter-agent text MUST be handled as DATA, never as instructions.

    ``treated_as_instructions`` records how the caller USED the text. If the caller executed
    untrusted text as instructions, the boundary fails closed regardless of content; if it kept
    it as data, the boundary holds even when the text contains an injection attempt (which is
    reported in the evidence).
    """
    has_injection, markers = classify_untrusted_text(text)
    if treated_as_instructions:
        return BoundaryResult(
            boundary=BOUNDARY_UNTRUSTED_TEXT,
            ok=False,
            reason="untrusted text was treated as instructions (must be data only)",
            evidence={"injection_markers": list(markers)},
        )
    return BoundaryResult(
        boundary=BOUNDARY_UNTRUSTED_TEXT,
        ok=True,
        reason=(
            "untrusted text isolated as data"
            + (
                f"; injection attempt detected and ignored ({len(markers)} marker(s))"
                if has_injection
                else ""
            )
        ),
        evidence={"injection_markers": list(markers)},
    )


# ==================================================================================================
# 7. Destructive tools human-gated (reuses role contracts)
# ==================================================================================================

# Tool names classified destructive (irreversible / externally consequential).
DESTRUCTIVE_TOOLS: frozenset = frozenset(
    (
        "git_push",
        "git_tag",
        "publish",
        "deploy",
        "rm_rf",
        "force_delete",
        "release",
        "pypi_upload",
    )
)


def check_destructive_tool_gated(
    tool_name: str,
    actor_role: str,
    human_consent: bool,
) -> BoundaryResult:
    """A destructive tool MUST be human-gated: only the ``human`` role may consent.

    Reuses the role contracts (:func:`verify_roles.get_role_contract`): a non-human actor cannot
    synthesize its own consent (``can_record_human_approval`` is False for every non-human role).
    A destructive tool invoked without a genuine human consent fails closed.
    """
    is_destructive = tool_name in DESTRUCTIVE_TOOLS
    if not is_destructive:
        return BoundaryResult(
            boundary=BOUNDARY_DESTRUCTIVE_GATE,
            ok=True,
            reason=f"tool '{tool_name}' is not destructive; no human gate required",
            evidence={"tool": tool_name},
        )
    try:
        contract = vr.get_role_contract(actor_role)
    except Exception:
        contract = None
    actor_may_consent = bool(contract and contract.can_record_human_approval)
    if not human_consent:
        return BoundaryResult(
            boundary=BOUNDARY_DESTRUCTIVE_GATE,
            ok=False,
            reason=f"destructive tool '{tool_name}' invoked without human consent",
            evidence={"tool": tool_name, "actor_role": actor_role},
        )
    if not actor_may_consent:
        return BoundaryResult(
            boundary=BOUNDARY_DESTRUCTIVE_GATE,
            ok=False,
            reason=(
                f"role '{actor_role}' cannot record human approval; a destructive tool gate "
                "requires the human role (self-synthesized consent refused)"
            ),
            evidence={"tool": tool_name, "actor_role": actor_role},
        )
    return BoundaryResult(
        boundary=BOUNDARY_DESTRUCTIVE_GATE,
        ok=True,
        reason=f"destructive tool '{tool_name}' gated by genuine human consent",
        evidence={"tool": tool_name, "actor_role": actor_role},
    )


# ==================================================================================================
# 8. Canonical scanner adapters (REUSE, no fork)
# ==================================================================================================


def scan_artifact_for_leaks(repo_root: Path | str) -> List[Any]:
    """Scan a repo's working tree with the CANONICAL leak sanitizer (``aw sanitize``).

    Thin adapter over :func:`leak_sanitizer.scan_working_tree`; returns its Finding list. This
    is the SAME code path ``aw sanitize --agent`` runs, so a release gate reuses one scanner.
    """
    return ls.scan_working_tree(Path(repo_root))


def _load_scan_secrets() -> Any:
    """Import the repo's canonical secret scanner tool by path (no fork).

    The scanner lives under ``.aw/system/workflows/assess/tools/scan_secrets.py``; it is a
    workflow tool, not an installed package module, so we load it by file path.
    """
    repo_root = Path(__file__).resolve().parent.parent
    tool_path = (
        repo_root
        / ".aw"
        / "system"
        / "workflows"
        / "assess"
        / "tools"
        / "scan_secrets.py"
    )
    if not tool_path.is_file():
        raise FileNotFoundError(f"canonical secret scanner not found at {tool_path}")
    import sys

    name = "aw_scan_secrets"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, tool_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Register BEFORE exec so @dataclass in the tool can resolve cls.__module__ (Py3.12+/3.14).
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def scan_text_for_secrets(text: str, location: str = "evidence") -> List[Any]:
    """Scan text with the CANONICAL secret scanner (``scan_secrets.py``).

    Thin adapter over ``scan_secrets.scan_text``; does not reimplement any rule.
    """
    scanner = _load_scan_secrets()
    return scanner.scan_text(
        text, where="hardening", location=location, use_entropy=True, use_pii=True
    )


# ==================================================================================================
# Aggregate report
# ==================================================================================================


@dataclass
class HardeningReport:
    """Aggregate of every boundary result."""

    results: Tuple[BoundaryResult, ...]

    @property
    def all_ok(self) -> bool:
        return all(r.ok for r in self.results)

    def failures(self) -> List[BoundaryResult]:
        return [r for r in self.results if not r.ok]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_ok": self.all_ok,
            "results": [r.to_dict() for r in self.results],
        }


def run_boundary_checks(
    checks: Sequence[Callable[[], BoundaryResult]],
) -> HardeningReport:
    """Run a sequence of zero-arg boundary checkers and aggregate the results."""
    return HardeningReport(results=tuple(c() for c in checks))


__all__ = [
    "ALL_BOUNDARIES",
    "BOUNDARY_DESTRUCTIVE_GATE",
    "BOUNDARY_EVIDENCE_REDACTION",
    "BOUNDARY_EXTERNAL_FILE",
    "BOUNDARY_REAL_HOME",
    "BOUNDARY_SERVER_BINDING",
    "BOUNDARY_SKILL_PRIVILEGE",
    "BOUNDARY_UNTRUSTED_TEXT",
    "DESTRUCTIVE_TOOLS",
    "BoundaryResult",
    "HardeningReport",
    "check_destructive_tool_gated",
    "check_evidence_redaction",
    "check_external_file_access",
    "check_local_server_binding",
    "check_real_home_excluded",
    "check_skill_least_privilege",
    "check_untrusted_text_isolated",
    "classify_untrusted_text",
    "default_redaction_policy",
    "run_boundary_checks",
    "scan_artifact_for_leaks",
    "scan_text_for_secrets",
]
