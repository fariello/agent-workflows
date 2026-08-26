"""Run evidence capture, false-completion validators, and deterministic completion predicates.

awoptimize Order 04 (`yndh7k`) E-01..E-03.

This module makes completion a deterministic PREDICATE over frozen requirements, valid captured
evidence, repository identity, and independent verifier decisions - not prose emitted by an executor.

Capabilities:
  * E-01: Capture tool/command invocations and artifact references into structured provenance
          envelopes (argv, cwd, timestamps, exit codes, output hashes, env allowlist, git HEAD,
          dirty digest, worktree path, actor, linked IDs).
  * E-02: Mechanically validate evidence against every known false-completion class with distinct
          stable reason codes (missing output, fabricated text, stale HEAD, wrong cwd, wrong worktree,
          mismatched command, expired host probe, truncated output, failed exit, absent artifact,
          hash mismatch, executor-authored verifier decision, redaction/truncation conflict).
  * E-03: Compute the deterministic completion predicate (`is_complete` / `evaluate_completion`)
          over frozen requirements, performed steps, independent verifier decisions, green commands,
          unresolved blockers/corrections, and coordinator terminal authority.

Pure stdlib implementation conforming to D138 (dependency minimization) and D139 (no runtime YAML).
"""

from __future__ import annotations

import datetime
import hashlib
import os
import subprocess
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from agent_workflows import run_ledger_schema as schema

# ---- constants and allowlists --------------------------------------------------------------------

DEFAULT_ENV_ALLOWLIST: FrozenSet[str] = frozenset(
    (
        "CI",
        "GIT_AUTHOR_NAME",
        "GIT_COMMITTER_NAME",
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PWD",
        "PYTHONPATH",
        "PYTHONUNBUFFERED",
        "SHELL",
        "TERM",
        "TMPDIR",
        "USER",
        "VIRTUAL_ENV",
    )
)

# Substrings that must never appear in unredacted environment keys
_SENSITIVE_KEY_SUBSTRINGS: Tuple[str, ...] = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASS",
    "AUTH",
    "CRED",
    "PRIVATE",
    "API",
)

# ---- findings and validation result structures ---------------------------------------------------


class EvidenceFinding(NamedTuple):
    code: str
    where: str
    message: str
    reason: str


class EvidenceValidationResult(NamedTuple):
    ok: bool
    findings: Tuple[EvidenceFinding, ...]


class CompletionPredicate(NamedTuple):
    name: str
    satisfied: bool
    details: str


class CompletionEvaluation(NamedTuple):
    is_complete: bool
    predicates: Dict[str, CompletionPredicate]
    missing_evidence: Tuple[str, ...]
    unresolved_blockers: Tuple[str, ...]
    reasons: Tuple[str, ...]


# ---- environment filtering and sanitization ------------------------------------------------------


def filter_environment(
    env: Optional[Mapping[str, str]] = None,
    allowlist: Optional[Sequence[str]] = None,
) -> Dict[str, str]:
    """Sanitize environment variables against an explicit allowlist and sensitive keyword filter.
    Never leaks raw secrets into ledger records."""
    source = os.environ if env is None else env
    allowed_keys = (
        frozenset(allowlist) if allowlist is not None else DEFAULT_ENV_ALLOWLIST
    )
    sanitized: Dict[str, str] = {}
    for k, v in source.items():
        if k in allowed_keys:
            upper_k = k.upper()
            if any(sub in upper_k for sub in _SENSITIVE_KEY_SUBSTRINGS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = str(v)
    return sanitized


# ---- git provenance helpers ----------------------------------------------------------------------


def get_git_head(repo_dir: Union[str, Path] = ".") -> str:
    """Resolve current git commit SHA (or 'unversioned' if not a git repo or git is absent)."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode == 0:
            head = proc.stdout.strip()
            if head:
                return head
    except (OSError, subprocess.SubprocessError):
        pass
    return "unversioned"


def get_git_dirty_digest(repo_dir: Union[str, Path] = ".") -> str:
    """Compute deterministic SHA-256 digest of git porcelain status or 'clean'."""
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode == 0:
            status_text = proc.stdout
            if not status_text.strip():
                return "clean"
            return hashlib.sha256(status_text.encode("utf-8")).hexdigest()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unversioned"


def _porcelain_paths(repo_dir: Union[str, Path] = ".") -> Optional[List[str]]:
    """Repo-relative paths with ANY uncommitted state (staged, unstaged, or untracked).

    Returns a de-duplicated list of paths from ``git status --porcelain`` (both the staged and the
    worktree side of a rename are included), or ``None`` when git is unavailable / not a repo. An
    empty list means a clean tree.
    """
    try:
        # -uall lists untracked files INDIVIDUALLY rather than collapsing a wholly-new directory to
        # its directory name, so a new in-scope file (e.g. a fresh tests/test_x.py under a new dir) is
        # attributable to the exact path a Scope-Paths matcher can compare.
        proc = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    paths: List[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: XY<space>path  (rename/copy: XY<space>old -> new).
        entry = line[3:] if len(line) > 3 else line.strip()
        if " -> " in entry:
            old, new = entry.split(" -> ", 1)
            paths.append(old.strip().strip('"'))
            paths.append(new.strip().strip('"'))
        else:
            paths.append(entry.strip().strip('"'))
    # Stable, de-duplicated.
    seen: Set[str] = set()
    out: List[str] = []
    for p in paths:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def dirty_within(
    repo_dir: Union[str, Path],
    scope_paths: Sequence[str],
    matcher: Callable[[str, str], bool],
) -> str:
    """Path-scoped dirty check: is any uncommitted path INSIDE ``scope_paths``?

    Unlike :func:`get_git_dirty_digest` (which reports the WHOLE tree), this reports non-clean only
    when an uncommitted path (staged, unstaged, or untracked; both sides of a rename) matches at
    least one ``scope_paths`` entry via ``matcher(path, pattern)``. Disjoint uncommitted work
    elsewhere is intentionally IGNORED - this is the path-overlap rule (ipdgates-03 OQ-01) that
    preserves a concurrent multi-agent workflow, where other agents may have unrelated uncommitted
    changes on disjoint paths.

    ``matcher`` is injected (rather than reimplementing the Scope-Paths grammar here) so the caller
    supplies the SAME matcher its scope comparison uses, guaranteeing begin and finalize agree.

    Returns:
      * ``"clean"``          - no uncommitted path is inside ``scope_paths`` (or ``scope_paths`` is empty);
      * a ``\\n``-joined string of the offending in-scope paths (sorted) - when at least one matches;
      * ``"unversioned"``    - git is unavailable / not a repo (fail-closed, mirrors get_git_dirty_digest).
    """
    if not scope_paths:
        return "clean"
    paths = _porcelain_paths(repo_dir)
    if paths is None:
        return "unversioned"
    hits = sorted({p for p in paths if any(matcher(p, pat) for pat in scope_paths)})
    if not hits:
        return "clean"
    return "\n".join(hits)


def get_worktree_path(repo_dir: Union[str, Path] = ".") -> str:
    """Resolve normalized absolute worktree path."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return str(Path(proc.stdout.strip()).resolve())
    except (OSError, subprocess.SubprocessError):
        pass
    return str(Path(repo_dir).resolve())


# ---- E-01: Evidence Capture builders -------------------------------------------------------------


def build_tool_event(
    run_id: str,
    argv: Sequence[str],
    cwd: str,
    exit_code: int,
    stdout: Union[str, bytes],
    stderr: Union[str, bytes] = "",
    *,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    truncated: bool = False,
    max_bytes: Optional[int] = None,
    env: Optional[Mapping[str, str]] = None,
    env_allowlist: Optional[Sequence[str]] = None,
    actor: str = "executor",
    parent: str = "",
    seq: int = 0,
) -> Dict[str, Any]:
    """Build a schema-conforming `tool_event` ledger record with provenance."""
    stdout_bytes = stdout.encode("utf-8") if isinstance(stdout, str) else stdout
    stderr_bytes = stderr.encode("utf-8") if isinstance(stderr, str) else stderr

    stdout_sha256 = hashlib.sha256(stdout_bytes).hexdigest()
    stderr_sha256 = hashlib.sha256(stderr_bytes).hexdigest()

    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    ts = start_time or now_iso

    rec: Dict[str, Any] = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "tool_event",
        "seq": seq,
        "run_id": run_id,
        "actor": actor,
        "timestamp": ts,
        "parent": parent,
        "argv": list(argv),
        "cwd": str(cwd),
        "exit_code": int(exit_code),
        "stdout_sha256": stdout_sha256,
        "stderr_sha256": stderr_sha256,
        "stdout_len": len(stdout_bytes),
        "stderr_len": len(stderr_bytes),
        "truncated": bool(truncated),
        "env": filter_environment(env, env_allowlist),
    }
    if start_time:
        rec["start_time"] = start_time
    if end_time:
        rec["end_time"] = end_time
    if max_bytes is not None:
        rec["max_bytes"] = int(max_bytes)

    return rec


def build_evidence_envelope(
    run_id: str,
    evidence_kind: str,
    binds: Sequence[str],
    head: str,
    worktree: str,
    *,
    dirty_digest: str = "clean",
    actor: str = "executor",
    parent: str = "",
    seq: int = 0,
    timestamp: Optional[str] = None,
    tool_event_hash: Optional[str] = None,
    tool_event_seq: Optional[int] = None,
    stdout_sha256: Optional[str] = None,
    artifact_path: Optional[str] = None,
    artifact_sha256: Optional[str] = None,
    probe_nonce: Optional[str] = None,
    probe_timestamp: Optional[str] = None,
    probe_ttl_seconds: Optional[float] = None,
    extra_provenance: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a schema-conforming `evidence_envelope` ledger record binding claims to provenance."""
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    rec: Dict[str, Any] = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "evidence_envelope",
        "seq": seq,
        "run_id": run_id,
        "actor": actor,
        "timestamp": ts,
        "parent": parent,
        "evidence_kind": str(evidence_kind),
        "binds": list(binds),
        "head": str(head),
        "worktree": str(worktree),
        "dirty_digest": str(dirty_digest),
    }
    if tool_event_hash:
        rec["tool_event_hash"] = str(tool_event_hash)
    if tool_event_seq is not None:
        rec["tool_event_seq"] = int(tool_event_seq)
    if stdout_sha256:
        rec["stdout_sha256"] = str(stdout_sha256)
    if artifact_path:
        rec["artifact_path"] = str(artifact_path)
    if artifact_sha256:
        rec["artifact_sha256"] = str(artifact_sha256)
    if probe_nonce:
        rec["probe_nonce"] = str(probe_nonce)
    if probe_timestamp:
        rec["probe_timestamp"] = str(probe_timestamp)
    if probe_ttl_seconds is not None:
        rec["probe_ttl_seconds"] = float(probe_ttl_seconds)
    if extra_provenance:
        rec.update(extra_provenance)

    return rec


def build_artifact_ref(
    run_id: str,
    path: str,
    sha256: str,
    *,
    binds: Optional[Sequence[str]] = None,
    head: Optional[str] = None,
    worktree: Optional[str] = None,
    actor: str = "executor",
    parent: str = "",
    seq: int = 0,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a schema-conforming `artifact_ref` ledger record."""
    ts = timestamp or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    rec: Dict[str, Any] = {
        "schema_version": schema.LEDGER_SCHEMA_VERSION,
        "kind": "artifact_ref",
        "seq": seq,
        "run_id": run_id,
        "actor": actor,
        "timestamp": ts,
        "parent": parent,
        "path": str(path),
        "sha256": str(sha256),
    }
    if binds is not None:
        rec["binds"] = list(binds)
    if head is not None:
        rec["head"] = str(head)
    if worktree is not None:
        rec["worktree"] = str(worktree)
    return rec


def capture_command(
    run_id: str,
    argv: Sequence[str],
    cwd: Union[str, Path] = ".",
    *,
    binds: Optional[Sequence[str]] = None,
    evidence_kind: str = "command",
    env_allowlist: Optional[Sequence[str]] = None,
    actor: str = "executor",
    parent: str = "",
    timeout: float = 60.0,
    max_output_bytes: Optional[int] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Execute a command, capture provenance (start/end, exit, stdout/stderr SHA-256, HEAD, dirty digest,
    worktree, env allowlist), and return (tool_event, evidence_envelope)."""
    norm_cwd = str(Path(cwd).resolve())
    head = get_git_head(norm_cwd)
    dirty_digest = get_git_dirty_digest(norm_cwd)
    worktree = get_worktree_path(norm_cwd)

    start_dt = datetime.datetime.now(datetime.timezone.utc)
    start_time = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        proc = subprocess.run(
            list(argv),
            cwd=norm_cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        exit_code = proc.returncode
        stdout_raw = proc.stdout
        stderr_raw = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout_raw = exc.stdout or b""
        stderr_raw = (exc.stderr or b"") + b"\nCommand timed out."
    except Exception as exc:
        exit_code = 127
        stdout_raw = b""
        stderr_raw = str(exc).encode("utf-8")

    end_dt = datetime.datetime.now(datetime.timezone.utc)
    end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    truncated = False
    if max_output_bytes is not None and len(stdout_raw) > max_output_bytes:
        stdout_raw = stdout_raw[:max_output_bytes]
        truncated = True

    tool_event = build_tool_event(
        run_id=run_id,
        argv=argv,
        cwd=norm_cwd,
        exit_code=exit_code,
        stdout=stdout_raw,
        stderr=stderr_raw,
        start_time=start_time,
        end_time=end_time,
        truncated=truncated,
        max_bytes=max_output_bytes,
        env_allowlist=env_allowlist,
        actor=actor,
        parent=parent,
    )

    bound_ids = list(binds) if binds else []
    envelope = build_evidence_envelope(
        run_id=run_id,
        evidence_kind=evidence_kind,
        binds=bound_ids,
        head=head,
        worktree=worktree,
        dirty_digest=dirty_digest,
        actor=actor,
        parent=parent,
        stdout_sha256=tool_event["stdout_sha256"],
        timestamp=end_time,
    )

    return tool_event, envelope


# ---- E-02: Evidence Validators -------------------------------------------------------------------


def validate_evidence(
    record_or_envelope: Mapping[str, Any],
    *,
    expected_head: Optional[str] = None,
    expected_cwd: Optional[str] = None,
    expected_worktree: Optional[str] = None,
    expected_command: Optional[Sequence[str]] = None,
    require_full_output: bool = True,
    max_probe_age_seconds: Optional[float] = None,
    current_time: Optional[datetime.datetime] = None,
    check_filesystem: bool = True,
    expected_file_content: Optional[Union[str, bytes]] = None,
    referenced_tool_event: Optional[Mapping[str, Any]] = None,
) -> EvidenceValidationResult:
    """Validate captured evidence against all known false-completion classes, rejecting violations
    with distinct stable reason codes.

    False-completion classes covered:
      * EV-MISSING-OUTPUT: Missing required output or empty stdout hash.
      * EV-FABRICATED-TEXT: Claimed evidence without captured provenance envelope or tool event.
      * EV-STALE-HEAD: Commit HEAD does not match expected/target HEAD.
      * EV-WRONG-CWD: Working directory does not match expected target directory.
      * EV-WRONG-WORKTREE: Worktree path does not match expected worktree.
      * EV-COMMAND-MISMATCH: Captured command argv does not match expected required command.
      * EV-EXPIRED-PROBE: Host probe timestamp has expired beyond TTL.
      * EV-TRUNCATED-OUTPUT: Required full output was truncated.
      * EV-FAILED-EXIT: Command finished with non-zero exit code.
      * EV-ABSENT-ARTIFACT: Referenced artifact file is missing from filesystem.
      * EV-HASH-MISMATCH: File or output content hash does not match recorded digest.
      * EV-EXECUTOR-VERIFIER: Verifier decision authored by executor role rather than verifier.
      * EV-REDACTION-CONFLICT: Required validation payload was masked/redacted, failing closed.
    """
    findings: List[EvidenceFinding] = []

    if not isinstance(record_or_envelope, Mapping):
        return EvidenceValidationResult(
            False,
            (
                EvidenceFinding(
                    "EV-FABRICATED-TEXT",
                    "",
                    "Evidence must be a structured record mapping, got manual text or invalid type",
                    "fabricated manual text: no captured envelope",
                ),
            ),
        )

    kind = record_or_envelope.get("kind")

    # 1. Fabricated manual text / unknown kind
    if kind not in schema.RECORD_KINDS:
        findings.append(
            EvidenceFinding(
                "EV-FABRICATED-TEXT",
                "kind",
                f"Unknown or fabricated record kind '{kind}'",
                "fabricated manual text: no captured tool event in ledger",
            )
        )
        return EvidenceValidationResult(False, tuple(findings))

    # 2. Verifier decision authored by executor
    if kind == "verifier_decision":
        actor = record_or_envelope.get("actor")
        if actor != "verifier":
            findings.append(
                EvidenceFinding(
                    "EV-EXECUTOR-VERIFIER",
                    "actor",
                    f"verifier_decision authored by role '{actor}', must be 'verifier'",
                    "executor-authored verifier decision",
                )
            )

    # 3. Tool event checks
    if kind == "tool_event":
        exit_code = record_or_envelope.get("exit_code")
        if exit_code != 0:
            findings.append(
                EvidenceFinding(
                    "EV-FAILED-EXIT",
                    "exit_code",
                    f"Command failed with non-zero exit code {exit_code}",
                    "failed exit code",
                )
            )

        stdout_sha256 = record_or_envelope.get("stdout_sha256")
        if not stdout_sha256 or stdout_sha256 == hashlib.sha256(b"").hexdigest():
            if require_full_output:
                findings.append(
                    EvidenceFinding(
                        "EV-MISSING-OUTPUT",
                        "stdout_sha256",
                        "Command output is missing or empty when output verification was required",
                        "missing output",
                    )
                )

        if require_full_output and record_or_envelope.get("truncated") is True:
            findings.append(
                EvidenceFinding(
                    "EV-TRUNCATED-OUTPUT",
                    "truncated",
                    "Required output was truncated, violating full-evidence contract",
                    "truncated required output",
                )
            )

        if expected_cwd is not None:
            actual_cwd = Path(record_or_envelope.get("cwd", "")).resolve()
            exp_cwd = Path(expected_cwd).resolve()
            if actual_cwd != exp_cwd:
                findings.append(
                    EvidenceFinding(
                        "EV-WRONG-CWD",
                        "cwd",
                        f"Command ran in cwd '{actual_cwd}', expected '{exp_cwd}'",
                        "wrong working directory",
                    )
                )

        if expected_command is not None:
            actual_argv = list(record_or_envelope.get("argv", []))
            exp_argv = list(expected_command)
            if actual_argv != exp_argv:
                findings.append(
                    EvidenceFinding(
                        "EV-COMMAND-MISMATCH",
                        "argv",
                        f"Command argv {actual_argv} does not match expected {exp_argv}",
                        "mismatched command",
                    )
                )

    # 4. Evidence envelope checks
    if kind == "evidence_envelope":
        head = record_or_envelope.get("head")
        if expected_head is not None and expected_head != "unversioned":
            if head != expected_head:
                findings.append(
                    EvidenceFinding(
                        "EV-STALE-HEAD",
                        "head",
                        f"Evidence captured at commit HEAD '{head}', expected '{expected_head}'",
                        "stale repository HEAD",
                    )
                )

        worktree = record_or_envelope.get("worktree")
        if expected_worktree is not None:
            actual_wt = Path(worktree or "").resolve()
            exp_wt = Path(expected_worktree).resolve()
            if actual_wt != exp_wt:
                findings.append(
                    EvidenceFinding(
                        "EV-WRONG-WORKTREE",
                        "worktree",
                        f"Evidence worktree '{actual_wt}' does not match expected '{exp_wt}'",
                        "wrong worktree path",
                    )
                )

        # Host probe expiration check
        probe_ts_str = record_or_envelope.get("probe_timestamp")
        probe_ttl = record_or_envelope.get("probe_ttl_seconds")
        if probe_ts_str and (
            probe_ttl is not None or max_probe_age_seconds is not None
        ):
            ttl = probe_ttl if probe_ttl is not None else max_probe_age_seconds
            now = current_time or datetime.datetime.now(datetime.timezone.utc)
            try:
                probe_dt = datetime.datetime.fromisoformat(
                    probe_ts_str.replace("Z", "+00:00")
                )
                age_seconds = (now - probe_dt).total_seconds()
                if ttl is not None and age_seconds > ttl:
                    findings.append(
                        EvidenceFinding(
                            "EV-EXPIRED-PROBE",
                            "probe_timestamp",
                            f"Host capability probe expired: age {age_seconds:.1f}s exceeds TTL {ttl:.1f}s",
                            "expired host probe",
                        )
                    )
            except (ValueError, TypeError):
                findings.append(
                    EvidenceFinding(
                        "EV-EXPIRED-PROBE",
                        "probe_timestamp",
                        f"Unparseable probe timestamp '{probe_ts_str}'",
                        "expired host probe",
                    )
                )

        # Truncation / Redaction conflict
        if record_or_envelope.get("redacted") is True and require_full_output:
            if record_or_envelope.get("redaction_blocks_verification") is True:
                findings.append(
                    EvidenceFinding(
                        "EV-REDACTION-CONFLICT",
                        "redacted",
                        "Required verification payload was redacted, preventing conclusive check",
                        "redaction truncation conflict",
                    )
                )

    # 5. Artifact ref checks
    if kind == "artifact_ref":
        artifact_path_str = record_or_envelope.get("path")
        expected_sha = record_or_envelope.get("sha256")

        if check_filesystem and artifact_path_str:
            art_path = Path(artifact_path_str)
            if not art_path.is_file():
                findings.append(
                    EvidenceFinding(
                        "EV-ABSENT-ARTIFACT",
                        "path",
                        f"Referenced artifact '{artifact_path_str}' does not exist on disk",
                        "absent artifact",
                    )
                )
            else:
                actual_sha = hashlib.sha256(art_path.read_bytes()).hexdigest()
                if expected_sha and actual_sha != expected_sha:
                    findings.append(
                        EvidenceFinding(
                            "EV-HASH-MISMATCH",
                            "sha256",
                            f"Artifact content SHA-256 '{actual_sha}' does not match recorded digest '{expected_sha}'",
                            "hash mismatch",
                        )
                    )

        if expected_file_content is not None and expected_sha:
            content_bytes = (
                expected_file_content.encode("utf-8")
                if isinstance(expected_file_content, str)
                else expected_file_content
            )
            content_sha = hashlib.sha256(content_bytes).hexdigest()
            if content_sha != expected_sha:
                findings.append(
                    EvidenceFinding(
                        "EV-HASH-MISMATCH",
                        "sha256",
                        f"Provided content SHA-256 '{content_sha}' does not match recorded digest '{expected_sha}'",
                        "hash mismatch",
                    )
                )

    return EvidenceValidationResult(len(findings) == 0, tuple(findings))


def validate_ledger_evidence(
    records: Sequence[Mapping[str, Any]],
    *,
    expected_head: Optional[str] = None,
    expected_worktree: Optional[str] = None,
    current_time: Optional[datetime.datetime] = None,
    check_filesystem: bool = False,
) -> EvidenceValidationResult:
    """Validate all evidence records within a complete ledger trajectory."""
    all_findings: List[EvidenceFinding] = []
    for idx, rec in enumerate(records):
        val_res = validate_evidence(
            rec,
            expected_head=expected_head,
            expected_worktree=expected_worktree,
            current_time=current_time,
            check_filesystem=check_filesystem,
        )
        for f in val_res.findings:
            where_ctx = f"records[{idx}].{f.where}" if f.where else f"records[{idx}]"
            all_findings.append(EvidenceFinding(f.code, where_ctx, f.message, f.reason))
    return EvidenceValidationResult(len(all_findings) == 0, tuple(all_findings))


# ---- E-03: Completion Predicates -----------------------------------------------------------------


def evaluate_completion(
    records: Sequence[Mapping[str, Any]],
    *,
    frozen_requirements: Optional[Sequence[str]] = None,
    coordinator_authority: bool = True,
    expected_head: Optional[str] = None,
    expected_worktree: Optional[str] = None,
    check_filesystem: bool = False,
) -> CompletionEvaluation:
    """Compute the deterministic completion predicate over a run's ledger records.

    Completion is COMPUTED, not claimed. Returns is_complete=True only if:
      1. Every frozen requirement is covered with an independent verifier pass decision.
      2. Every required execution step (E-*) has reached state 'performed'.
      3. All verifier decisions are authored by the 'verifier' role (no self-verification).
      4. All command invocations and evidence envelopes are valid and green (exit 0, hash match).
      5. No unresolved blockers or uncorrected failures remain.
      6. Coordinator terminal authority is present.
      7. Ledger sequence and records are structurally intact.
    """
    predicates: Dict[str, CompletionPredicate] = {}
    missing_evidence: List[str] = []
    unresolved_blockers: List[str] = []
    reasons: List[str] = []

    if not records:
        predicates["ledger_intact"] = CompletionPredicate(
            "ledger_intact", False, "Ledger is empty: no run record found"
        )
        return CompletionEvaluation(
            is_complete=False,
            predicates=predicates,
            missing_evidence=("run",),
            unresolved_blockers=(),
            reasons=("ledger is empty",),
        )

    # 1. Structural schema & sequence validation
    schema_val = schema.validate_records(records)
    if not schema_val.ok:
        predicates["ledger_intact"] = CompletionPredicate(
            "ledger_intact",
            False,
            f"Ledger failed schema validation: {schema_val.findings}",
        )
        reasons.append("ledger failed schema validation")
    else:
        predicates["ledger_intact"] = CompletionPredicate(
            "ledger_intact", True, "Ledger sequence and schemas are valid"
        )

    # 2. Extract active requirements
    active_requirements: Set[str] = set()
    if frozen_requirements is not None:
        active_requirements.update(frozen_requirements)

    for rec in records:
        kind = rec.get("kind")
        if kind == "requirement_set":
            for req in rec.get("requirements", []):
                rid = req.get("id")
                if rid:
                    active_requirements.add(rid)

    # 3. Track step attempts, corrections, verifier decisions, tool events
    step_states: Dict[str, str] = {}  # step_id -> latest state
    corrections_logged: Dict[str, int] = {}  # item_id -> latest correction seq
    verifier_decisions: Dict[
        str, Tuple[str, str, int]
    ] = {}  # req_id -> (actor, result, seq)
    failed_tool_events: List[Tuple[int, Sequence[str], int]] = []

    for idx, rec in enumerate(records):
        kind = rec.get("kind")
        seq = rec.get("seq", idx)

        if kind == "step_attempt":
            step_id = rec.get("step", "")
            state = rec.get("state", "")
            if step_id:
                step_states[step_id] = state

        elif kind == "correction":
            target_req = rec.get("corrects_requirement", "")
            if target_req:
                corrections_logged[target_req] = seq
                unresolved_blockers.append(
                    f"Correction logged at seq {seq} for {target_req}"
                )

        elif kind == "verifier_decision":
            req_id = rec.get("requirement", "")
            result = rec.get("result", "")
            actor = rec.get("actor", "")
            if req_id:
                verifier_decisions[req_id] = (actor, result, seq)

        elif kind == "tool_event":
            argv = rec.get("argv", [])
            exit_code = rec.get("exit_code", 0)
            if exit_code != 0:
                failed_tool_events.append((seq, argv, exit_code))

    # 4. Evidence validity across ledger
    evidence_val = validate_ledger_evidence(
        records,
        expected_head=expected_head,
        expected_worktree=expected_worktree,
        check_filesystem=check_filesystem,
    )
    if not evidence_val.ok:
        reasons.extend(f"{f.code}: {f.message}" for f in evidence_val.findings)
        predicates["evidence_valid"] = CompletionPredicate(
            "evidence_valid",
            False,
            f"Evidence validation findings: {evidence_val.findings}",
        )
    else:
        predicates["evidence_valid"] = CompletionPredicate(
            "evidence_valid", True, "All captured evidence is valid"
        )

    # 5. Predicate: Requirements Covered
    if not active_requirements:
        predicates["requirements_covered"] = CompletionPredicate(
            "requirements_covered", False, "No frozen requirements defined for run"
        )
        missing_evidence.append("frozen requirement_set")
        reasons.append("no frozen requirements defined")
    else:
        missing_reqs = []
        for req_id in sorted(active_requirements):
            decision = verifier_decisions.get(req_id)
            if not decision:
                missing_reqs.append(req_id)
            elif decision[1] not in ("satisfied", "pass"):
                missing_reqs.append(f"{req_id} ({decision[1]})")
        if missing_reqs:
            predicates["requirements_covered"] = CompletionPredicate(
                "requirements_covered",
                False,
                f"Missing or unsatisfied requirements: {missing_reqs}",
            )
            missing_evidence.extend(f"verifier_decision for {r}" for r in missing_reqs)
            reasons.append(f"unsatisfied requirements: {missing_reqs}")
        else:
            predicates["requirements_covered"] = CompletionPredicate(
                "requirements_covered",
                True,
                f"All {len(active_requirements)} frozen requirements satisfied",
            )

    # 6. Predicate: Step Attempts Performed
    if not step_states:
        predicates["steps_performed"] = CompletionPredicate(
            "steps_performed", False, "No step attempts recorded"
        )
        missing_evidence.append("step_attempt")
        reasons.append("no step attempts recorded")
    else:
        unperformed = [s for s, state in step_states.items() if state != "performed"]
        if unperformed:
            predicates["steps_performed"] = CompletionPredicate(
                "steps_performed",
                False,
                f"Steps not performed: {unperformed}",
            )
            reasons.append(f"unperformed steps: {unperformed}")
        else:
            predicates["steps_performed"] = CompletionPredicate(
                "steps_performed",
                True,
                f"All {len(step_states)} step attempts performed",
            )

    # 7. Predicate: Verifier Independence (actor == "verifier", never executor)
    non_independent_verifiers = [
        f"{r} (actor={actor})"
        for r, (actor, res, s) in verifier_decisions.items()
        if actor != "verifier"
    ]
    if non_independent_verifiers:
        predicates["verifier_independent"] = CompletionPredicate(
            "verifier_independent",
            False,
            f"Self-verified decisions detected: {non_independent_verifiers}",
        )
        reasons.append(f"executor self-verification: {non_independent_verifiers}")
    else:
        predicates["verifier_independent"] = CompletionPredicate(
            "verifier_independent",
            True,
            "All verifier decisions authored by independent verifier role",
        )

    # 8. Predicate: Commands Green and Valid
    if failed_tool_events:
        # Check if failed tool events were subsequently retried / corrected
        unresolved_tool_failures = []
        for seq, argv, code in failed_tool_events:
            # Check if there is a later successful tool event with same command or retry
            subsequent_success = any(
                rec.get("kind") == "tool_event"
                and rec.get("seq", 0) > seq
                and rec.get("exit_code") == 0
                and rec.get("argv") == argv
                for rec in records
            )
            if not subsequent_success:
                unresolved_tool_failures.append(f"seq {seq} ({argv}) exit {code}")

        if unresolved_tool_failures:
            predicates["commands_green"] = CompletionPredicate(
                "commands_green",
                False,
                f"Failed commands without subsequent success: {unresolved_tool_failures}",
            )
            reasons.append(f"unresolved failed commands: {unresolved_tool_failures}")
        else:
            predicates["commands_green"] = CompletionPredicate(
                "commands_green", True, "All command failures were successfully retried"
            )
    else:
        predicates["commands_green"] = CompletionPredicate(
            "commands_green", True, "All executed commands succeeded"
        )

    # 9. Predicate: No Unresolved Blockers or Corrections
    active_unresolved_corrections = []
    for req_id, cor_seq in corrections_logged.items():
        decision = verifier_decisions.get(req_id)
        if (
            not decision
            or decision[2] <= cor_seq
            or decision[1] not in ("satisfied", "pass")
        ):
            active_unresolved_corrections.append(req_id)

    if active_unresolved_corrections:
        predicates["no_blockers"] = CompletionPredicate(
            "no_blockers",
            False,
            f"Unresolved corrections for requirements: {active_unresolved_corrections}",
        )
        reasons.append(f"unresolved corrections: {active_unresolved_corrections}")
    else:
        predicates["no_blockers"] = CompletionPredicate(
            "no_blockers", True, "No unresolved corrections or blockers"
        )

    # 10. Predicate: Coordinator Terminal Authority
    if not coordinator_authority:
        predicates["coordinator_authority"] = CompletionPredicate(
            "coordinator_authority",
            False,
            "Coordinator terminal authority is absent",
        )
        reasons.append("coordinator terminal authority absent")
    else:
        predicates["coordinator_authority"] = CompletionPredicate(
            "coordinator_authority",
            True,
            "Coordinator terminal authority present",
        )

    all_predicates_pass = all(p.satisfied for p in predicates.values())
    is_comp = all_predicates_pass and (len(reasons) == 0)

    return CompletionEvaluation(
        is_complete=is_comp,
        predicates=predicates,
        missing_evidence=tuple(missing_evidence),
        unresolved_blockers=tuple(unresolved_blockers),
        reasons=tuple(reasons),
    )


def is_complete(
    records: Sequence[Mapping[str, Any]],
    *,
    frozen_requirements: Optional[Sequence[str]] = None,
    coordinator_authority: bool = True,
    expected_head: Optional[str] = None,
    expected_worktree: Optional[str] = None,
    check_filesystem: bool = False,
) -> bool:
    """Return True if and only if all deterministic completion predicates evaluate to True."""
    evaluation = evaluate_completion(
        records,
        frozen_requirements=frozen_requirements,
        coordinator_authority=coordinator_authority,
        expected_head=expected_head,
        expected_worktree=expected_worktree,
        check_filesystem=check_filesystem,
    )
    return evaluation.is_complete
