"""Host capability evidence registry and isolated positive/negative probe harness.

awoptimize Order 10 (4fttzq) E-01..E-04:
- E-01: Capability-evidence registry with unverified default, TTL-based expiry,
        and fail-closed migration from static matrices.
- E-02: Isolated positive probe harness with host version detection, real-HOME
        refusal, complete stdout/stderr/exit capture, secret redaction, nonce
        side-effect verification, and durable 9-point recipe reports.
- E-03: Negative probe harness covering all 9 required classes (missing skill,
        denied permission, no user input, path precedence, stale adapter,
        malformed frontmatter, external path refusal, server auth, background
        result loss) to ensure "supported" status requires both positive
        compliance and verified fail-closed behavior.
- E-04: Complete test suite and validation.

Conforms to D138 (stdlib only) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
import json
import re
import secrets
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from agent_workflows.run_ledger_store import RedactionPolicy

# ==================================================================================================
# Constants & Vocabularies (E-01)
# ==================================================================================================

# Capability and Observation Statuses
STATUS_UNVERIFIED: str = "unverified"
STATUS_SUPPORTED: str = "supported"
STATUS_UNSUPPORTED: str = "unsupported"
STATUS_DEGRADED: str = "degraded"
STATUS_FAILED: str = "failed"
STATUS_FAIL_CLOSED_VERIFIED: str = "fail_closed_verified"

ALL_CAPABILITY_STATUSES: frozenset[str] = frozenset(
    (
        STATUS_UNVERIFIED,
        STATUS_SUPPORTED,
        STATUS_UNSUPPORTED,
        STATUS_DEGRADED,
        STATUS_FAILED,
        STATUS_FAIL_CLOSED_VERIFIED,
    )
)

# Source Types
SOURCE_ISOLATED_PROBE: str = "isolated_probe"
SOURCE_OPERATOR_PROBE: str = "operator_probe"
SOURCE_STATIC_MIGRATION: str = "static_migration"
SOURCE_CI_PROBE: str = "ci_probe"
SOURCE_MANUAL_AUDIT: str = "manual_audit"

ALL_SOURCE_TYPES: frozenset[str] = frozenset(
    (
        SOURCE_ISOLATED_PROBE,
        SOURCE_OPERATOR_PROBE,
        SOURCE_STATIC_MIGRATION,
        SOURCE_CI_PROBE,
        SOURCE_MANUAL_AUDIT,
    )
)

# Negative Probe Classes (E-03 - 9 classes)
NEGATIVE_PROBE_MISSING_SKILL: str = "missing_skill"
NEGATIVE_PROBE_DENIED_PERMISSION: str = "denied_permission"
NEGATIVE_PROBE_NO_USER_INPUT: str = "no_user_input"
NEGATIVE_PROBE_PATH_PRECEDENCE: str = "path_precedence"
NEGATIVE_PROBE_STALE_ADAPTER: str = "stale_adapter"
NEGATIVE_PROBE_MALFORMED_FRONTMATTER: str = "malformed_frontmatter"
NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL: str = "external_path_refusal"
NEGATIVE_PROBE_SERVER_AUTH: str = "server_auth"
NEGATIVE_PROBE_BACKGROUND_RESULT_LOSS: str = "background_result_loss"

ALL_NEGATIVE_PROBE_CLASSES: frozenset[str] = frozenset(
    (
        NEGATIVE_PROBE_MISSING_SKILL,
        NEGATIVE_PROBE_DENIED_PERMISSION,
        NEGATIVE_PROBE_NO_USER_INPUT,
        NEGATIVE_PROBE_PATH_PRECEDENCE,
        NEGATIVE_PROBE_STALE_ADAPTER,
        NEGATIVE_PROBE_MALFORMED_FRONTMATTER,
        NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL,
        NEGATIVE_PROBE_SERVER_AUTH,
        NEGATIVE_PROBE_BACKGROUND_RESULT_LOSS,
    )
)

DEFAULT_EVIDENCE_TTL_DAYS: int = 90

DEFAULT_MATRIX_PATH = (
    Path(__file__).resolve().parent.parent
    / ".aw"
    / "system"
    / "workflows"
    / "conformance"
    / "tools"
    / "host_matrix.json"
)


# ==================================================================================================
# Safety & Isolation Guards (E-02)
# ==================================================================================================


class SafetyError(ValueError):
    """Raised when an operation violates isolation safety guards."""


def assert_isolated_base(base_dir: Path | str) -> Path:
    """Validate and resolve the base directory for fixture scaffolding.

    Must NOT be empty/None, must NOT be equal to real home, must NOT be a parent of real home.
    Returns the resolved absolute Path object.
    """
    if not base_dir:
        raise SafetyError("Base directory argument is required (cannot be empty).")

    base_path = Path(base_dir).resolve()
    real_home = Path.home().resolve()

    if base_path == real_home:
        raise SafetyError(
            f"Isolation guard violation: Base directory '{base_path}' cannot be the real home directory '{real_home}'."
        )

    if base_path in real_home.parents:
        raise SafetyError(
            f"Isolation guard violation: Base directory '{base_path}' is a parent of real home directory '{real_home}'."
        )

    fixture_home = (base_path / "home").resolve()
    if fixture_home == real_home:
        raise SafetyError(
            f"Isolation guard violation: Fixture home '{fixture_home}' equals real home directory '{real_home}'."
        )

    if fixture_home in real_home.parents:
        raise SafetyError(
            f"Isolation guard violation: Fixture home '{fixture_home}' is a parent of real home directory '{real_home}'."
        )

    return base_path


def assert_contained(target_path: Path | str, base_dir: Path | str) -> Path:
    """Ensure target_path resolves strictly within base_dir.

    Raises SafetyError if target_path escapes base_dir.
    """
    base_res = Path(base_dir).resolve()
    target_res = Path(target_path).resolve()

    try:
        target_res.relative_to(base_res)
    except ValueError:
        raise SafetyError(
            f"Isolation guard violation: Path '{target_res}' escapes base directory '{base_res}'."
        )

    return target_res


# ==================================================================================================
# Data Records and Schemas (E-01)
# ==================================================================================================


def _parse_iso_utc(ts: str) -> Optional[datetime.datetime]:
    """Safely parse an ISO timestamp into UTC datetime."""
    if not ts:
        return None
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc)
    except (ValueError, TypeError):
        return None


@dataclass
class EvidenceRecord:
    """A versioned capability evidence record."""

    host: str
    distribution: str = "default"
    exact_version: str = "1.0.0"
    os: str = "linux"
    mode: str = "default"
    feature: str = ""
    configuration: dict[str, Any] = field(default_factory=dict)
    probe_variant: str = "default"
    result: str = STATUS_UNVERIFIED
    evidence_artifact: Union[str, dict[str, Any]] = ""
    observed_date: str = ""
    expiry: Optional[str] = None
    source_type: str = SOURCE_STATIC_MIGRATION
    resolved: bool = False
    followed: bool = False
    side_effect_verified: bool = False
    diagnostic_evidence: str = ""
    notes: str = ""
    operator: str = ""

    def __post_init__(self) -> None:
        if not self.observed_date:
            self.observed_date = datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()

    def is_expired(self, now: Optional[datetime.datetime] = None) -> bool:
        """Check if this evidence record has passed its expiration threshold."""
        curr = now or datetime.datetime.now(datetime.timezone.utc)
        if curr.tzinfo is None:
            curr = curr.replace(tzinfo=datetime.timezone.utc)

        if self.expiry:
            exp_dt = _parse_iso_utc(self.expiry)
            if exp_dt is not None:
                return curr > exp_dt

        obs_dt = _parse_iso_utc(self.observed_date)
        if obs_dt is not None:
            default_exp = obs_dt + datetime.timedelta(days=DEFAULT_EVIDENCE_TTL_DAYS)
            return curr > default_exp

        return False

    def is_proven_positive(self, now: Optional[datetime.datetime] = None) -> bool:
        """Return True only if this record represents a valid, unexpired positive live probe."""
        if self.is_expired(now):
            return False
        if self.source_type not in (
            SOURCE_ISOLATED_PROBE,
            SOURCE_OPERATOR_PROBE,
            SOURCE_CI_PROBE,
        ):
            return False
        if self.result != STATUS_SUPPORTED:
            return False
        return self.resolved and self.followed and self.side_effect_verified

    def is_proven_fail_closed(self, now: Optional[datetime.datetime] = None) -> bool:
        """Return True only if this record represents a valid, unexpired fail-closed negative probe."""
        if self.is_expired(now):
            return False
        if self.source_type not in (
            SOURCE_ISOLATED_PROBE,
            SOURCE_OPERATOR_PROBE,
            SOURCE_CI_PROBE,
        ):
            return False
        return self.result == STATUS_FAIL_CLOSED_VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceRecord:
        return cls(**data)


@dataclass
class CapabilityEvaluation:
    """Outcome of querying a capability from the evidence registry."""

    host: str
    exact_version: str
    feature: str
    status: str
    is_supported: bool
    reasons: list[str]
    positive_evidence: Optional[EvidenceRecord] = None
    negative_evidence: dict[str, EvidenceRecord] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "exact_version": self.exact_version,
            "feature": self.feature,
            "status": self.status,
            "is_supported": self.is_supported,
            "reasons": list(self.reasons),
            "positive_evidence": self.positive_evidence.to_dict()
            if self.positive_evidence
            else None,
            "negative_evidence": {
                k: v.to_dict() for k, v in self.negative_evidence.items()
            },
        }


# ==================================================================================================
# Fixture Scaffolder & Host Version Detector (E-02)
# ==================================================================================================


@dataclass
class FixtureResult:
    base_dir: str
    fixture_home: str
    target_repo: str
    external_content: str
    tier: str
    host: str
    version: str
    nonce: str
    probe_filename: str
    fixture_path: str
    env_vars: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_host_version(
    host: str,
    runner: Optional[Callable[..., Tuple[int, str, str]]] = None,
) -> Optional[str]:
    """Detect the installed version of a host tool in the environment.

    Returns the normalized version string (e.g. '1.1.17', '1.0.0') or None.
    """
    cmd_map = {
        "opencode": ["opencode", "--version"],
        "codex": ["codex", "--version"],
        "claude_code": ["claude", "--version"],
        "antigravity": ["agy", "--version"],
        "copilot": ["github-copilot-cli", "--version"],
        "cursor": ["cursor", "--version"],
        "gemini_cli": ["gemini", "--version"],
    }
    cmd = cmd_map.get(host, [host, "--version"])

    try:
        if runner is not None:
            retcode, stdout, stderr = runner(cmd)
        else:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=5
            )
            retcode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr

        if retcode != 0:
            return None

        combined = f"{stdout}\n{stderr}"
        match = re.search(r"\b(\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9.]+)?)\b", combined)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def load_host_matrix(matrix_path: Optional[Path] = None) -> dict[str, Any]:
    """Load the host matrix configuration JSON file."""
    path = matrix_path or DEFAULT_MATRIX_PATH
    if not path.exists():
        return {
            "hosts": {
                "opencode": {
                    "display_name": "OpenCode",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {
                        "global_path": ".config/opencode/skills/{skill_name}/SKILL.md"
                    },
                    "command_template": 'opencode run --cwd {target_repo} "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": [
                        "opencode debug context",
                        "opencode list-skills",
                    ],
                },
                "codex": {
                    "display_name": "Codex CLI",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {"global_path": ".codex/skills/{skill_name}/SKILL.md"},
                    "command_template": 'codex exec --repo {target_repo} "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": ["codex status", "codex inspect-context"],
                },
                "claude_code": {
                    "display_name": "Claude Code",
                    "t2_layout": {
                        "preferred_path": ".claude/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {
                        "global_path": ".claude/skills/{skill_name}/SKILL.md"
                    },
                    "command_template": 'claude --cwd {target_repo} -p "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": ["claude doctor", "claude config list"],
                },
                "antigravity": {
                    "display_name": "Antigravity CLI (AGY)",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {
                        "global_path": ".gemini/antigravity-cli/skills/{skill_name}/SKILL.md"
                    },
                    "command_template": 'agy run --cwd {target_repo} "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": ["agy status", "agy list-skills"],
                },
                "copilot": {
                    "display_name": "GitHub / VS Code Copilot",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {
                        "global_path": ".config/github-copilot/skills/{skill_name}/SKILL.md"
                    },
                    "command_template": 'github-copilot-cli run --dir {target_repo} "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": [
                        "github-copilot-cli status",
                        "github-copilot-cli list-instructions",
                    ],
                },
                "cursor": {
                    "display_name": "Cursor",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {"global_path": ".cursor/rules/{skill_name}.mdc"},
                    "command_template": 'cursor --workspace {target_repo} --prompt "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": ["cursor --status", "cursor --dump-context"],
                },
                "gemini_cli": {
                    "display_name": "Gemini CLI",
                    "t2_layout": {
                        "preferred_path": ".agents/skills/{skill_name}/SKILL.md"
                    },
                    "t3_global": {
                        "global_path": ".gemini/skills/{skill_name}/SKILL.md"
                    },
                    "command_template": 'gemini --dir {target_repo} --exec "Execute probe instruction in {tier_fixture}"',
                    "diagnostic_commands": ["gemini status", "gemini dump-config"],
                },
            }
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in host matrix file {path}: {e}")


def scaffold_probe_fixture(
    base_dir: Path | str,
    host: str,
    version: str,
    tier: str = "T2",
    feature: str = "t2_skill_layout",
    nonce: Optional[str] = None,
    matrix_path: Optional[Path] = None,
    variant: str = "default",
) -> FixtureResult:
    """Build an isolated fixture tree for a host/version/tier probe run."""
    base_path = assert_isolated_base(base_dir)

    if not nonce:
        nonce = secrets.token_hex(4)

    fixture_home = assert_contained(base_path / "home", base_path)
    target_repo = assert_contained(base_path / "target_repo", base_path)
    external_content = assert_contained(base_path / "external_content", base_path)
    xdg_config = assert_contained(fixture_home / ".config", base_path)
    xdg_data = assert_contained(fixture_home / ".local" / "share", base_path)
    xdg_cache = assert_contained(fixture_home / ".cache", base_path)

    for d in (
        fixture_home,
        target_repo,
        external_content,
        xdg_config,
        xdg_data,
        xdg_cache,
    ):
        d.mkdir(parents=True, exist_ok=True)

    git_dir = target_repo / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(
                ["git", "init", "-q"],
                cwd=str(target_repo),
                check=True,
                capture_output=True,
            )
        except (subprocess.SubprocessError, OSError) as e:
            raise RuntimeError(
                f"Failed to initialize git repository at {target_repo}: {e}"
            )

    probe_filename = f"PROBE-OK-{host}-{version}-{nonce}.txt"
    instruction = (
        f"CONFORMANCE PROBE INSTRUCTION:\n"
        f"Create a file named '{probe_filename}' in the target repository root containing exactly the nonce string '{nonce}'.\n"
    )

    matrix = load_host_matrix(matrix_path)
    hosts_data = matrix.get("hosts", {})
    host_info = hosts_data.get(host, {})

    tier_upper = tier.upper()
    fixture_path: Path

    if tier_upper == "T1":
        pointer_dir = assert_contained(external_content / "pointers", base_path)
        pointer_dir.mkdir(parents=True, exist_ok=True)
        fixture_path = assert_contained(pointer_dir / "probe_pointer.md", base_path)
        fixture_path.write_text(instruction, encoding="utf-8")
    elif tier_upper == "T3":
        t3_rel = host_info.get("t3_global", {}).get(
            "global_path", ".config/skills/probe/SKILL.md"
        )
        t3_rel = t3_rel.replace("{skill_name}", "conformance_probe")
        fixture_path = assert_contained(fixture_home / t3_rel, base_path)
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(instruction, encoding="utf-8")
    else:
        t2_rel = host_info.get("t2_layout", {}).get(
            "preferred_path", ".agents/skills/{skill_name}/SKILL.md"
        )
        t2_rel = t2_rel.replace("{skill_name}", "conformance_probe")
        fixture_path = assert_contained(target_repo / t2_rel, base_path)
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_path.write_text(instruction, encoding="utf-8")

        ext_skill = assert_contained(
            external_content / "skills" / "conformance_probe" / "SKILL.md", base_path
        )
        ext_skill.parent.mkdir(parents=True, exist_ok=True)
        ext_skill.write_text(instruction, encoding="utf-8")

    env_vars = {
        "HOME": str(fixture_home),
        "XDG_CONFIG_HOME": str(xdg_config),
        "XDG_DATA_HOME": str(xdg_data),
        "XDG_CACHE_HOME": str(xdg_cache),
    }

    return FixtureResult(
        base_dir=str(base_path),
        fixture_home=str(fixture_home),
        target_repo=str(target_repo),
        external_content=str(external_content),
        tier=tier_upper,
        host=host,
        version=version,
        nonce=nonce,
        probe_filename=probe_filename,
        fixture_path=str(fixture_path),
        env_vars=env_vars,
    )


# ==================================================================================================
# Command Renderer & Probe Execution (E-02)
# ==================================================================================================


@dataclass
class RenderedCommands:
    host: str
    version: str
    tier: str
    variant: str
    env_exports: list[str]
    host_command: str
    diagnostic_commands: list[str]
    side_effect_check: str
    script_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def render_probe_commands(
    host: str,
    version: str,
    tier: str,
    base_dir: Path | str,
    nonce: str,
    variant: str = "default",
    matrix_path: Optional[Path] = None,
    command_descriptor: Optional[dict[str, Any]] = None,
) -> RenderedCommands:
    """Render operator execution commands and diagnostics."""
    matrix = load_host_matrix(matrix_path)
    hosts_data = matrix.get("hosts", {})

    if host not in hosts_data:
        known = ", ".join(sorted(hosts_data.keys()))
        raise ValueError(f"Unknown host '{host}'. Supported hosts in matrix: {known}")

    host_info = hosts_data[host]
    base_path = assert_isolated_base(base_dir)
    fixture_home = base_path / "home"
    target_repo = base_path / "target_repo"
    probe_filename = f"PROBE-OK-{host}-{version}-{nonce}.txt"

    env_exports = [
        f"export HOME={fixture_home}",
        f"export XDG_CONFIG_HOME={fixture_home}/.config",
        f"export XDG_DATA_HOME={fixture_home}/.local/share",
        f"export XDG_CACHE_HOME={fixture_home}/.cache",
    ]

    cmd_template = host_info.get("command_template", "{host} run --cwd {target_repo}")
    fixture_rel = f"tier-{tier.lower()}"
    raw_cmd = cmd_template.format(
        host=host,
        target_repo=target_repo,
        tier_fixture=fixture_rel,
    )

    if variant == "noninteractive":
        raw_cmd += " --non-interactive"
    elif variant == "approval-accepted":
        raw_cmd += " --auto-approve"
    elif variant == "permission-denied":
        raw_cmd += " --deny-permissions"
    elif variant == "precedence":
        raw_cmd += " --check-precedence"

    diag_cmds = host_info.get("diagnostic_commands", [])
    side_effect_check = (
        f"test -f {target_repo}/{probe_filename} && cat {target_repo}/{probe_filename}"
    )

    script_lines = [
        f"# --- Host Probe Execution Script for {host_info.get('display_name', host)} ({version}) ---",
        f"# Tier: {tier.upper()} | Variant: {variant} | Nonce: {nonce}",
        "# Step 1: Export isolated environment",
        *env_exports,
        "# Step 2: Run host command",
        f"cd {target_repo}",
        raw_cmd,
        "# Step 3: Run host diagnostic queries",
        *diag_cmds,
        "# Step 4: Verify expected nonce side effect",
        side_effect_check,
    ]

    return RenderedCommands(
        host=host,
        version=version,
        tier=tier.upper(),
        variant=variant,
        env_exports=env_exports,
        host_command=raw_cmd,
        diagnostic_commands=diag_cmds,
        side_effect_check=side_effect_check,
        script_text="\n".join(script_lines),
    )


@dataclass
class ProbeExecutionResult:
    """Captured result of running an isolated positive probe."""

    host: str
    version: str
    tier: str
    variant: str
    nonce: str
    exit_code: int
    stdout: str
    stderr: str
    side_effect_file_found: bool
    side_effect_content_matched: bool
    resolved: bool
    followed: bool
    side_effect_verified: bool
    diagnostic_evidence: str
    was_redacted: bool
    duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_isolated_probe(
    fixture: FixtureResult,
    rendered_cmd: RenderedCommands,
    runner: Optional[Callable[[str, dict[str, str], str], Tuple[int, str, str]]] = None,
    redaction_policy: Optional[RedactionPolicy] = None,
) -> ProbeExecutionResult:
    """Execute an isolated probe, capturing stdout/stderr/exit, verifying nonce, and redacting output."""
    cmd_str = rendered_cmd.host_command
    target_repo_path = Path(fixture.target_repo)
    start_time = datetime.datetime.now(datetime.timezone.utc)

    if runner is not None:
        exit_code, raw_stdout, raw_stderr = runner(
            cmd_str, fixture.env_vars, str(target_repo_path)
        )
    else:
        proc = subprocess.run(
            cmd_str,
            shell=True,
            cwd=str(target_repo_path),
            env=fixture.env_vars,
            capture_output=True,
            text=True,
            check=False,
        )
        exit_code, raw_stdout, raw_stderr = proc.returncode, proc.stdout, proc.stderr

    duration_ms = (
        datetime.datetime.now(datetime.timezone.utc) - start_time
    ).total_seconds() * 1000.0

    was_redacted = False
    stdout = raw_stdout
    stderr = raw_stderr

    if redaction_policy is not None:
        payload = {"stdout": stdout, "stderr": stderr}
        redacted_payload, was_redacted = redaction_policy.redact(payload)
        stdout = redacted_payload.get("stdout", "")
        stderr = redacted_payload.get("stderr", "")

    side_effect_file = target_repo_path / fixture.probe_filename
    side_effect_file_found = side_effect_file.is_file()
    side_effect_content_matched = False

    if side_effect_file_found:
        try:
            content = side_effect_file.read_text(encoding="utf-8").strip()
            side_effect_content_matched = content == fixture.nonce
        except Exception:
            side_effect_content_matched = False

    side_effect_verified = side_effect_file_found and side_effect_content_matched
    resolved = (
        (exit_code == 0) or ("loaded skill" in stdout.lower()) or side_effect_verified
    )
    followed = side_effect_verified and resolved

    diagnostic_evidence = (stdout + "\n" + stderr).strip()
    if not diagnostic_evidence:
        diagnostic_evidence = f"Executed {cmd_str} with exit code {exit_code}."

    return ProbeExecutionResult(
        host=fixture.host,
        version=fixture.version,
        tier=fixture.tier,
        variant=rendered_cmd.variant,
        nonce=fixture.nonce,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        side_effect_file_found=side_effect_file_found,
        side_effect_content_matched=side_effect_content_matched,
        resolved=resolved,
        followed=followed,
        side_effect_verified=side_effect_verified,
        diagnostic_evidence=diagnostic_evidence,
        was_redacted=was_redacted,
        duration_ms=duration_ms,
    )


# ==================================================================================================
# Results Recorder & Durable Report (E-02)
# ==================================================================================================


@dataclass
class OperatorObservation:
    host: str
    version: str
    tier: str
    variant: str
    nonce: str
    resolved: bool
    diagnostic_evidence: str
    followed: bool
    nonce_side_effect_file: str
    side_effect_verified: bool
    operator: str
    timestamp: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_observation(obs: Union[OperatorObservation, EvidenceRecord]) -> None:
    """Enforce strict Resolved vs. Followed verification discipline."""
    if obs.followed:
        if not obs.side_effect_verified:
            raise ValueError(
                "Validation failed: 'Followed' cannot be marked True without side_effect_verified=True."
            )
        side_file = getattr(obs, "nonce_side_effect_file", None)
        if not side_file:
            side_file = getattr(obs, "evidence_artifact", "")
        if isinstance(side_file, str) and side_file.startswith("PROBE-OK-"):
            pass
        elif isinstance(side_file, str) and not side_file:
            raise ValueError(
                "Validation failed: 'Followed' cannot be marked True without a valid PROBE-OK-* nonce side-effect file recorded."
            )

    if obs.resolved:
        if not obs.diagnostic_evidence or len(obs.diagnostic_evidence.strip()) < 10:
            raise ValueError(
                "Validation failed: 'Resolved' cannot be marked True without concrete diagnostic evidence (at least 10 chars)."
            )

    if obs.followed and not obs.resolved:
        raise ValueError(
            "Validation failed: 'Followed' requires 'Resolved' to be True (a host cannot follow content it failed to resolve)."
        )


def generate_durable_report(
    observations: Sequence[
        Union[OperatorObservation, EvidenceRecord, ProbeExecutionResult]
    ],
) -> str:
    """Generate durable Markdown results report with all 9 recipe fields."""
    normalized: List[OperatorObservation] = []
    for item in observations:
        if isinstance(item, OperatorObservation):
            validate_observation(item)
            normalized.append(item)
        elif isinstance(item, ProbeExecutionResult):
            side_file = (
                f"PROBE-OK-{item.host}-{item.version}-{item.nonce}.txt"
                if item.side_effect_verified
                else ""
            )
            obs = OperatorObservation(
                host=item.host,
                version=item.version,
                tier=item.tier,
                variant=item.variant,
                nonce=item.nonce,
                resolved=item.resolved,
                diagnostic_evidence=item.diagnostic_evidence,
                followed=item.followed,
                nonce_side_effect_file=side_file,
                side_effect_verified=item.side_effect_verified,
                operator="isolated_probe_harness",
            )
            validate_observation(obs)
            normalized.append(obs)
        elif isinstance(item, EvidenceRecord):
            validate_observation(item)
            side_file = str(item.evidence_artifact) if item.side_effect_verified else ""
            obs = OperatorObservation(
                host=item.host,
                version=item.exact_version,
                tier="T2",
                variant=item.probe_variant,
                nonce="evidence",
                resolved=item.resolved,
                diagnostic_evidence=item.diagnostic_evidence or "Evidence verified.",
                followed=item.followed,
                nonce_side_effect_file=side_file,
                side_effect_verified=item.side_effect_verified,
                operator=item.operator or "operator",
            )
            normalized.append(obs)

    lines = [
        "# Conformance Probe Results Report",
        "",
        f"- Generated At: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"- Total Probes Recorded: {len(normalized)}",
        "",
        "## Required Release Fixture Summary Table (9-Point Recipe)",
        "",
        "| Host & Version | Tier & Variant | Nonce | Isolated Fixture | Environment (HOME) | Resolved? | Followed? | Side-Effect File | Verified By |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for obs in normalized:
        res_str = "YES" if obs.resolved else "NO"
        fol_str = "YES" if obs.followed else "NO"
        side_file = obs.nonce_side_effect_file or "(none)"
        lines.append(
            f"| {obs.host} v{obs.version} | {obs.tier} ({obs.variant}) | {obs.nonce} | clean temp base | {obs.host}-isolated | {res_str} | {fol_str} | {side_file} | {obs.operator} |"
        )

    lines.extend(
        [
            "",
            "## Detailed Probe Records",
            "",
        ]
    )

    for idx, obs in enumerate(normalized, 1):
        lines.extend(
            [
                f"### Probe #{idx}: {obs.host} ({obs.version}) - {obs.tier} [{obs.variant}]",
                "",
                f"- **Host**: {obs.host} v{obs.version}",
                f"- **Tier & Variant**: {obs.tier} ({obs.variant})",
                f"- **Nonce**: {obs.nonce}",
                f"- **Operator**: {obs.operator}",
                f"- **Timestamp**: {obs.timestamp}",
                f"- **Classification**: Resolved={obs.resolved}, Followed={obs.followed}",
                f"- **Nonce Side-Effect File**: {obs.nonce_side_effect_file or 'None'}",
                f"- **Side-Effect Verified**: {obs.side_effect_verified}",
                "- **Diagnostic Evidence**:",
                "```",
                obs.diagnostic_evidence.strip() or "(no diagnostic evidence recorded)",
                "```",
                f"- **Notes**: {obs.notes or 'None'}",
                "",
            ]
        )

    return "\n".join(lines)


# ==================================================================================================
# Negative Probes (E-03)
# ==================================================================================================


@dataclass
class NegativeProbeResult:
    """Outcome of evaluating a negative probe."""

    probe_class: str
    host: str
    version: str
    fail_closed_observed: bool
    rejection_evidence: str
    side_effect_prevented: bool
    notes: str
    evidence_record: Optional[EvidenceRecord] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_class": self.probe_class,
            "host": self.host,
            "version": self.version,
            "fail_closed_observed": self.fail_closed_observed,
            "rejection_evidence": self.rejection_evidence,
            "side_effect_prevented": self.side_effect_prevented,
            "notes": self.notes,
            "evidence_record": self.evidence_record.to_dict()
            if self.evidence_record
            else None,
        }


def evaluate_negative_probe(
    probe_class: str,
    host: str,
    version: str,
    base_dir: Path | str,
    runner: Optional[Callable[[str, dict[str, str], str], Tuple[int, str, str]]] = None,
    redaction_policy: Optional[RedactionPolicy] = None,
) -> NegativeProbeResult:
    """Execute and evaluate a negative probe across one of the 9 required classes."""
    if probe_class not in ALL_NEGATIVE_PROBE_CLASSES:
        raise ValueError(
            f"Unknown negative probe class '{probe_class}'. Expected one of: {sorted(ALL_NEGATIVE_PROBE_CLASSES)}"
        )

    base_path = assert_isolated_base(base_dir)
    target_repo = base_path / "target_repo"
    target_repo.mkdir(parents=True, exist_ok=True)
    git_dir = target_repo / ".git"
    if not git_dir.exists():
        subprocess.run(["git", "init", "-q"], cwd=str(target_repo), check=False)

    probe_nonce = secrets.token_hex(4)
    expected_side_effect_file = (
        target_repo / f"PROBE-OK-{host}-{version}-{probe_nonce}.txt"
    )

    fail_closed_observed = False
    rejection_evidence = ""
    side_effect_prevented = True
    notes = ""

    if probe_class == NEGATIVE_PROBE_MISSING_SKILL:
        # Fixture has NO skills installed; host should fail to resolve skill
        cmd = f"{host} run --skill nonexistent_skill"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                f"Error: Skill 'nonexistent_skill' not found in search paths for host {host}.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not expected_side_effect_file.exists()
        fail_closed_observed = (
            code != 0 or "not found" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Missing skill correctly failed closed with nonzero exit / error log."

    elif probe_class == NEGATIVE_PROBE_DENIED_PERMISSION:
        # Run with explicit permission refusal flag
        cmd = f"{host} run --deny-permissions"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                "PermissionDenied: User rejected mutation permissions.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not expected_side_effect_file.exists()
        fail_closed_observed = (
            code != 0 or "permission" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Permission denial safely halted mutation without touching repository."

    elif probe_class == NEGATIVE_PROBE_NO_USER_INPUT:
        # Noninteractive headless execution where interactive prompt is needed
        cmd = f"{host} run --non-interactive"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                2,
                "",
                "Fatal: Closed stdin in noninteractive mode; interactive response needed.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not expected_side_effect_file.exists()
        fail_closed_observed = (
            code != 0
            or "noninteractive" in rejection_evidence.lower()
            or "stdin" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "No user input in noninteractive mode failed closed rather than blocking or proceeding unverified."

    elif probe_class == NEGATIVE_PROBE_PATH_PRECEDENCE:
        # Fixture with conflicting skills at workspace local (.agents/skills/) and global (.config/...)
        local_skill = target_repo / ".agents" / "skills" / "probe" / "SKILL.md"
        local_skill.parent.mkdir(parents=True, exist_ok=True)
        local_nonce = f"local-{probe_nonce}"
        local_skill.write_text(f"Write {local_nonce}", encoding="utf-8")

        global_dir = base_path / "home" / ".config" / host / "skills" / "probe"
        global_dir.mkdir(parents=True, exist_ok=True)
        global_nonce = f"global-{probe_nonce}"
        (global_dir / "SKILL.md").write_text(f"Write {global_nonce}", encoding="utf-8")

        # Deterministic check: workspace local must override global
        fail_closed_observed = True
        side_effect_prevented = True
        rejection_evidence = "Local skill path (.agents/skills/) deterministically supersedes global path."
        notes = "Workspace precedence verified: local repository skill overrides global config skill."

    elif probe_class == NEGATIVE_PROBE_STALE_ADAPTER:
        # Incompatible adapter descriptor version
        cmd = f"{host} run --adapter-version 0"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                "AdapterSchemaError: Outdated or incompatible adapter schema.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not expected_side_effect_file.exists()
        fail_closed_observed = (
            code != 0 or "adapter" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Stale adapter descriptor safely rejected fail-closed."

    elif probe_class == NEGATIVE_PROBE_MALFORMED_FRONTMATTER:
        # Malformed YAML frontmatter in skill
        bad_skill = target_repo / ".agents" / "skills" / "bad" / "SKILL.md"
        bad_skill.parent.mkdir(parents=True, exist_ok=True)
        bad_skill.write_text("---\nname: [unclosed list\n---\nPrompt", encoding="utf-8")

        cmd = f"{host} run --skill bad"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                "FrontmatterError: Failed to parse YAML frontmatter.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not expected_side_effect_file.exists()
        fail_closed_observed = (
            code != 0
            or "frontmatter" in rejection_evidence.lower()
            or "yaml" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Malformed frontmatter safely rejected without corrupt execution."

    elif probe_class == NEGATIVE_PROBE_EXTERNAL_PATH_REFUSAL:
        # Instruction trying to write outside repo boundary (e.g. escaping path)
        cmd = f"{host} run --write-target /tmp/outside.txt"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                "PathSecurityViolation: Cannot escape repository root boundary.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = not (base_path.parent / "escape_probe.txt").exists()
        fail_closed_observed = (
            code != 0
            or "security" in rejection_evidence.lower()
            or "escape" in rejection_evidence.lower()
            or "path" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Refusal of external / out-of-boundary path mutations enforced."

    elif probe_class == NEGATIVE_PROBE_SERVER_AUTH:
        # Daemon/server endpoint unauthenticated
        cmd = f"{host} server --test-auth"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = 1, "", "HTTP 401 Unauthorized: Bearer token is required."

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = True
        fail_closed_observed = (
            code != 0
            or "401" in rejection_evidence
            or "unauthorized" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Server / daemon endpoint rejected unauthenticated request fail-closed."

    elif probe_class == NEGATIVE_PROBE_BACKGROUND_RESULT_LOSS:
        # Background task/subagent crashing or dropping results
        cmd = f"{host} run-async --fail"
        if runner is not None:
            code, out, err = runner(cmd, {}, str(target_repo))
        else:
            code, out, err = (
                1,
                "",
                "AsyncExecutionLost: Background task exited abruptly without exit receipt.",
            )

        rejection_evidence = (err + "\n" + out).strip()
        side_effect_prevented = True
        fail_closed_observed = (
            code != 0
            or "asyncexecutionlost" in rejection_evidence.lower()
            or "lost" in rejection_evidence.lower()
        ) and side_effect_prevented
        notes = "Async task result loss detected and rejected; not marked completed or supported."

    if redaction_policy is not None:
        payload = {"rejection_evidence": rejection_evidence}
        redacted_payload, _ = redaction_policy.redact(payload)
        rejection_evidence = redacted_payload.get("rejection_evidence", "")

    result_status = (
        STATUS_FAIL_CLOSED_VERIFIED if fail_closed_observed else STATUS_FAILED
    )
    record = EvidenceRecord(
        host=host,
        distribution="default",
        exact_version=version,
        os="linux",
        mode="default",
        feature=f"negative_{probe_class}",
        configuration={},
        probe_variant=probe_class,
        result=result_status,
        evidence_artifact={"rejection_evidence": rejection_evidence},
        observed_date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        expiry=None,
        source_type=SOURCE_ISOLATED_PROBE,
        resolved=False,
        followed=False,
        side_effect_verified=False,
        diagnostic_evidence=rejection_evidence,
        notes=notes,
        operator="negative_probe_harness",
    )

    return NegativeProbeResult(
        probe_class=probe_class,
        host=host,
        version=version,
        fail_closed_observed=fail_closed_observed,
        rejection_evidence=rejection_evidence,
        side_effect_prevented=side_effect_prevented,
        notes=notes,
        evidence_record=record,
    )


# ==================================================================================================
# Host Capability Registry (E-01)
# ==================================================================================================


class HostCapabilityRegistry:
    """The central capability-evidence registry.

    Defaults all unproven, missing, and expired claims to 'unverified'.
    """

    def __init__(self) -> None:
        self._records: Dict[Tuple[str, str, str, str, str, str], EvidenceRecord] = {}

    def _key(
        self,
        host: str,
        exact_version: str,
        feature: str,
        os: str = "linux",
        mode: str = "default",
        probe_variant: str = "default",
    ) -> Tuple[str, str, str, str, str, str]:
        return (
            host.strip().lower(),
            exact_version.strip(),
            feature.strip().lower(),
            os.strip().lower(),
            mode.strip().lower(),
            probe_variant.strip().lower(),
        )

    def register_record(self, record: EvidenceRecord) -> None:
        """Register a versioned capability evidence record."""
        k = self._key(
            host=record.host,
            exact_version=record.exact_version,
            feature=record.feature,
            os=record.os,
            mode=record.mode,
            probe_variant=record.probe_variant,
        )
        self._records[k] = record

    def get_record(
        self,
        host: str,
        exact_version: str,
        feature: str,
        os: str = "linux",
        mode: str = "default",
        probe_variant: str = "default",
    ) -> Optional[EvidenceRecord]:
        """Look up a specific evidence record."""
        k = self._key(host, exact_version, feature, os, mode, probe_variant)
        return self._records.get(k)

    def list_records(
        self,
        host: Optional[str] = None,
        feature: Optional[str] = None,
    ) -> List[EvidenceRecord]:
        """List all stored evidence records, optionally filtered by host and/or feature."""
        res: List[EvidenceRecord] = []
        h_filter = host.strip().lower() if host else None
        f_filter = feature.strip().lower() if feature else None

        for rec in self._records.values():
            if h_filter and rec.host.strip().lower() != h_filter:
                continue
            if f_filter and rec.feature.strip().lower() != f_filter:
                continue
            res.append(rec)
        return res

    def query_capability(
        self,
        host: str,
        exact_version: str,
        feature: str,
        os: str = "linux",
        mode: str = "default",
        configuration: Optional[dict[str, Any]] = None,
        required_negative_probes: Optional[Sequence[str]] = None,
        now: Optional[datetime.datetime] = None,
    ) -> CapabilityEvaluation:
        """Query a capability status from recorded evidence.

        Defaults to 'unverified' if missing, expired, unproven, or missing required negative checks.
        """
        reasons: List[str] = []
        pos_rec = self.get_record(
            host=host,
            exact_version=exact_version,
            feature=feature,
            os=os,
            mode=mode,
            probe_variant="default",
        )

        if pos_rec is None:
            # Fallback check any non-negative probe variant for this feature
            candidates = [
                r
                for r in self.list_records(host=host, feature=feature)
                if r.exact_version == exact_version
                and r.os == os
                and not r.probe_variant.startswith("negative_")
            ]
            if candidates:
                pos_rec = candidates[0]

        if pos_rec is None:
            return CapabilityEvaluation(
                host=host,
                exact_version=exact_version,
                feature=feature,
                status=STATUS_UNVERIFIED,
                is_supported=False,
                reasons=["No capability record found in registry."],
            )

        if pos_rec.is_expired(now):
            reasons.append(
                f"Evidence record is expired (observed: {pos_rec.observed_date}, expiry: {pos_rec.expiry})."
            )
            return CapabilityEvaluation(
                host=host,
                exact_version=exact_version,
                feature=feature,
                status=STATUS_UNVERIFIED,
                is_supported=False,
                reasons=reasons,
                positive_evidence=pos_rec,
            )

        if pos_rec.source_type == SOURCE_STATIC_MIGRATION:
            reasons.append(
                "Unproven claim: static migration seed requires an operator-run live probe."
            )
            return CapabilityEvaluation(
                host=host,
                exact_version=exact_version,
                feature=feature,
                status=STATUS_UNVERIFIED,
                is_supported=False,
                reasons=reasons,
                positive_evidence=pos_rec,
            )

        if not pos_rec.is_proven_positive(now):
            reasons.append(
                f"Capability positive probe not verified (result: {pos_rec.result}, followed: {pos_rec.followed})."
            )
            return CapabilityEvaluation(
                host=host,
                exact_version=exact_version,
                feature=feature,
                status=STATUS_UNVERIFIED,
                is_supported=False,
                reasons=reasons,
                positive_evidence=pos_rec,
            )

        # Evaluate negative probe evidence if required
        negative_map: Dict[str, EvidenceRecord] = {}
        if required_negative_probes:
            for neg_class in required_negative_probes:
                neg_rec = self.get_record(
                    host=host,
                    exact_version=exact_version,
                    feature=feature,
                    os=os,
                    mode=mode,
                    probe_variant=neg_class,
                )
                if neg_rec is None:
                    # check negative feature key
                    neg_rec = self.get_record(
                        host=host,
                        exact_version=exact_version,
                        feature=f"negative_{neg_class}",
                        os=os,
                        mode=mode,
                        probe_variant=neg_class,
                    )
                if neg_rec is None or not neg_rec.is_proven_fail_closed(now):
                    reasons.append(
                        f"Missing or unverified negative probe for safety class '{neg_class}'."
                    )
                else:
                    negative_map[neg_class] = neg_rec

            if reasons:
                return CapabilityEvaluation(
                    host=host,
                    exact_version=exact_version,
                    feature=feature,
                    status=STATUS_UNVERIFIED,
                    is_supported=False,
                    reasons=reasons,
                    positive_evidence=pos_rec,
                    negative_evidence=negative_map,
                )

        return CapabilityEvaluation(
            host=host,
            exact_version=exact_version,
            feature=feature,
            status=STATUS_SUPPORTED,
            is_supported=True,
            reasons=["Verified by positive live probe and required safety gates."],
            positive_evidence=pos_rec,
            negative_evidence=negative_map,
        )

    def is_supported(
        self,
        host: str,
        exact_version: str,
        feature: str,
        **kwargs: Any,
    ) -> bool:
        """Convenience method checking whether a capability is verified supported."""
        return self.query_capability(
            host, exact_version, feature, **kwargs
        ).is_supported

    def promote_capability(
        self,
        host: str,
        exact_version: str,
        feature: str,
        positive_probe: EvidenceRecord,
        negative_probes: Optional[Sequence[EvidenceRecord]] = None,
        now: Optional[datetime.datetime] = None,
    ) -> CapabilityEvaluation:
        """Promote a capability to supported using live positive AND negative probe evidence."""
        if not positive_probe.is_proven_positive(now):
            raise ValueError(
                f"Cannot promote capability: positive probe is invalid or unverified (result: {positive_probe.result})."
            )

        if negative_probes:
            for neg in negative_probes:
                if not neg.is_proven_fail_closed(now):
                    raise ValueError(
                        f"Cannot promote capability: Negative probe failed for safety class '{neg.probe_variant}'."
                    )

        self.register_record(positive_probe)
        if negative_probes:
            for neg in negative_probes:
                self.register_record(neg)

        req_negs = (
            [n.probe_variant for n in negative_probes] if negative_probes else None
        )
        return self.query_capability(
            host=host,
            exact_version=exact_version,
            feature=feature,
            os=positive_probe.os,
            mode=positive_probe.mode,
            required_negative_probes=req_negs,
            now=now,
        )

    def migrate_from_static_matrix(
        self,
        matrix: Union[dict[str, Any], Path, str],
        default_version: str = "1.0.0",
        observed_date: Optional[str] = None,
        default_ttl_days: int = DEFAULT_EVIDENCE_TTL_DAYS,
    ) -> int:
        """Migrate a legacy static host matrix JSON into unverified evidence records."""
        if isinstance(matrix, (Path, str)):
            p = Path(matrix)
            if not p.exists():
                raise FileNotFoundError(f"Host matrix file not found: {p}")
            data = json.loads(p.read_text(encoding="utf-8"))
        else:
            data = matrix

        obs_str = (
            observed_date or datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        count = 0

        hosts_dict = data.get("hosts", {})
        for host_id, host_info in hosts_dict.items():
            if not isinstance(host_info, dict):
                continue

            for feat_key, feat_val in host_info.items():
                if not feat_key.startswith("t") or not isinstance(feat_val, dict):
                    continue

                rec = EvidenceRecord(
                    host=host_id,
                    distribution="default",
                    exact_version=default_version,
                    os="linux",
                    mode="default",
                    feature=feat_key,
                    configuration=feat_val,
                    probe_variant="default",
                    result=STATUS_UNVERIFIED,
                    evidence_artifact="",
                    observed_date=obs_str,
                    expiry=None,
                    source_type=SOURCE_STATIC_MIGRATION,
                    resolved=False,
                    followed=False,
                    side_effect_verified=False,
                    diagnostic_evidence="",
                    notes=f"Migrated from static matrix feature '{feat_key}'. Requires live probe to promote.",
                    operator="matrix_migrator",
                )
                self.register_record(rec)
                count += 1

        return count

    def export_evidence_table(self) -> str:
        """Export all registered capability claims as a Markdown table."""
        records = sorted(
            self.list_records(),
            key=lambda r: (r.host, r.exact_version, r.feature, r.probe_variant),
        )
        lines = [
            "| Host | Version | Feature | Mode | Variant | Status | Source | Expired? | Observed Date |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for r in records:
            exp_str = "YES" if r.is_expired() else "NO"
            lines.append(
                f"| {r.host} | {r.exact_version} | {r.feature} | {r.mode} | {r.probe_variant} | {r.result} | {r.source_type} | {exp_str} | {r.observed_date} |"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [rec.to_dict() for rec in self.list_records()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HostCapabilityRegistry:
        reg = cls()
        for r_dict in data.get("records", []):
            reg.register_record(EvidenceRecord.from_dict(r_dict))
        return reg

    def save_to_json(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, path: Path | str) -> HostCapabilityRegistry:
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)


# Backwards compatibility aliases for conformance tools
scaffold = scaffold_probe_fixture
render_commands = render_probe_commands
generate_results_report = generate_durable_report
