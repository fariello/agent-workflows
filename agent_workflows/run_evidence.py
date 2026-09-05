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


# ==================================================================================================
# runcodes Order 1 (`wlxkoz`) E-01 / E-02: the deterministic `RUN-*` finding-code vocabulary
# ==================================================================================================
#
# WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT.
#
# Spec `25kzda` 4.2 fixes 13 stable `RUN-*` finding codes as the deterministic checker's PUBLIC
# vocabulary: each row pins an exact operator-facing message (ending in a recovery command) and a
# failure ACTION. This block is that vocabulary and NOTHING else. It is a NAMING layer over
# predicates that already ship elsewhere in this package; it is NOT a second completion authority.
# `evaluate_completion` / `is_complete` above remain the single completion predicate, and
# `aw ipd finalize` remains the only terminal-transition authority (`verify_roles` reserves terminal
# authority to the coordinator). Nothing here decides completion, and nothing here may claim to.
#
# WHY DATA RATHER THAN BRANCHING LOGIC. The whole policy - 13 codes, their verbatim text, their
# recovery commands, their abort semantics, and how much of the checker actually decides anything -
# has to be readable in ONE place and enumerable by a test. The parallel shipped `EV-*` taxonomy
# (see `validate_evidence`'s docstring at the class list, plus the bare string literals inside its
# conditionals) is the counterexample: those codes are docstring prose plus inline literals, so no
# test can enumerate them and a reworded message drifts silently. This block deliberately
# INTRODUCES the convention `EV-*` should have had. It does NOT refactor `EV-*` into it (out of
# scope for `wlxkoz`), and the `EV-*` codes are referenced here only as BINDINGS, never renamed.
#
# NO CONSUMER YET, STATED PLAINLY. Wiring these codes into `oc_runipd.py` / `agy_runipd.py` is
# deliberately deferred (`wlxkoz` OQ-01), so no live run emits any of these codes today. This
# vocabulary lands tested and importable and nothing consults it yet.


class RunFindingCode(NamedTuple):
    """One row of spec `25kzda` 4.2: a stable code, its verbatim text, and its binding.

    Fields:
      * ``code``            - the stable public finding code (spec 4.2 column 1).
      * ``inspects``        - what the check inspects (spec 4.2 column 2), for operator context.
      * ``pass_criterion``  - the pass criterion (spec 4.2 column 3).
      * ``message``         - the VERBATIM operator-facing message template (spec 4.2 column 4),
                              including the trailing recovery command. ``<...>`` placeholders are
                              replaced with quoted concrete values by the caller. Transcribed from
                              the spec, never composed here: a reworded message is a defect, and
                              :func:`spec_message_for` plus the test suite exist to catch one.
      * ``action``          - the VERBATIM failure action (spec 4.2 column 5).
      * ``abort``           - derived tri-state over ``action``: one of :data:`ABORT_ALWAYS`,
                              :data:`ABORT_CONDITIONAL`, :data:`ABORT_NEVER`. See the abort note
                              below; this is an INDEX over the verbatim string, not a new policy.
      * ``abort_classes``   - for an aborting row, the spec-4.1 abort class names that license it.
                              Every entry MUST be a member of :data:`ABORT_CLASSES` (4.1 is
                              EXHAUSTIVE), which :func:`validate_finding_table` enforces.
      * ``binding``         - one of :data:`BOUND`, :data:`UNBOUND_BY_DEPENDENCY`,
                              :data:`UNBOUND_UNBUILT` (E-02).
      * ``predicates``      - for a BOUND row, the shipped symbols that actually decide it, as
                              ``module.symbol`` strings. Recorded as data so a test can prove each
                              one still resolves, which is what stops the mapping rotting silently.
      * ``waiting_on``      - for an UNBOUND row, the missing machinery (and its owner, when one
                              exists). Empty for a BOUND row.
    """

    code: str
    inspects: str
    pass_criterion: str
    message: str
    action: str
    abort: str
    abort_classes: Tuple[str, ...]
    binding: str
    predicates: Tuple[str, ...]
    waiting_on: str


# ---- abort semantics (spec 25kzda 4.1) -----------------------------------------------------------
#
# THE ACTION IS AS LOAD-BEARING AS THE MESSAGE. Spec 4.1 enumerates SIX abort classes and closes
# with "No other finding may abort the whole queue". So transcribing a message while inventing its
# action would silently license aborting a whole queue on an item-local fault - and item-local
# failure is exactly what lets independent items keep running. Two of the 13 codes abort
# UNCONDITIONALLY; eight abort ONLY under a named 4.1 class; three never abort. Collapsing that
# distinction into a single boolean is the error this tri-state exists to prevent.

ABORT_ALWAYS = "always"
ABORT_CONDITIONAL = "conditional"
ABORT_NEVER = "never"

#: Spec 4.1's EXHAUSTIVE abort-class set, verbatim. Nothing outside this set may abort the queue.
ABORT_CLASSES: Tuple[str, ...] = (
    "Corrupt run ledger",
    "Ownership or lease conflict",
    "Unknown or non-idempotent external outcome",
    "Push attempt",
    "Hook-bypass attempt",
    "Identity or type ambiguity",
)


# ---- binding states (E-02) -----------------------------------------------------------------------
#
# WHY A CODE RECORDS ITS OWN BINDING STATE. An unbound code that HONESTLY REPORTS ITSELF UNBOUND is
# safe: a reader and a caller can both see that nothing decides it yet. A code silently wired to a
# predicate that does not answer its question is a fail-OPEN checker - it passes because nothing was
# checked. The second is the failure this three-state field exists to make impossible, so a binding
# is recorded only where a shipped predicate genuinely answers THAT code's question.

#: A shipped predicate decides this code; the code is a stable NAME over existing logic.
BOUND = "BOUND"
#: The deciding predicate needs machinery another plan or item owns. Named, not invented.
UNBOUND_BY_DEPENDENCY = "UNBOUND-BY-DEPENDENCY"
#: Nothing in the tree decides this yet, and no plan owns it.
UNBOUND_UNBUILT = "UNBOUND-UNBUILT"

BINDING_STATES: Tuple[str, ...] = (BOUND, UNBOUND_BY_DEPENDENCY, UNBOUND_UNBUILT)


# ---- the 13 codes -------------------------------------------------------------------------------
#
# BINDINGS RE-MEASURED 2026-09-05 (E-02 requires re-verification, not trust). Three of `wlxkoz`
# finding F3's bindings had changed since F3 was recorded at HEAD `738980ec`, because both plans it
# was waiting on have since EXECUTED:
#
#   * `RUN-HOST-CAPABILITY` is now BOUND, not UNBOUND-BY-DEPENDENCY: `hostcap-01` (`mjx7ne`)
#     executed and shipped `host_sandbox_profile.preflight_host_capabilities` plus that code's
#     verbatim message.
#   * `RUN-BASELINE-OWNERSHIP` is now BOUND, not UNBOUND-UNBUILT: the per-path lease overlap check
#     F3 said nobody had built ships as `worktree_lease.LeaseTable.claim` (`m2wwns`), and
#     `dirty_within` decides the pre-existing-dirty-path half.
#   * `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY` stay UNBOUND, but WAITING ON SOMETHING ELSE.
#     `runtrail-01` (`m73aet`) executed and the `AW-Run:`/`AW-Item:` trailers exist - but only as
#     WRITERS. Nothing reads a trailer back, and `m73aet`'s own executed receipt states
#     "`RUN-COMMIT-GATEWAY` remains wholly unbuilt" and "nothing in the tree PASSES trailers yet".
#     Writing a trailer is not proving a commit's tree diff equals the item-owned delta, so binding
#     these two now would be exactly the fail-open error described above.
#
# Net: 10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT (F3 recorded 9 / 2 / 2).

RUN_FINDING_CODES: Tuple[RunFindingCode, ...] = (
    RunFindingCode(
        code="RUN-FROZEN-IDENTITY",
        inspects=(
            "Canonical path, stable ID, type, content digest, and action packet digest at each "
            "step boundary"
        ),
        pass_criterion=(
            "Current item is the same frozen identity; any content change is explained by a "
            "completed prior step and followed by a new freeze event"
        ),
        message=(
            "[RUN-FROZEN-IDENTITY] <item> changed outside its recorded step. Contain the item "
            "and inspect identity/ownership with: aw runs show <run-id>"
        ),
        action=(
            "FAIL ITEM after containment; ABORT RUN only for identity/type ambiguity or "
            "ownership conflict"
        ),
        abort=ABORT_CONDITIONAL,
        abort_classes=("Identity or type ambiguity", "Ownership or lease conflict"),
        binding=BOUND,
        predicates=(
            "run_freeze.freeze_requirements",
            "run_freeze.diff_requirements",
            "run_freeze.refuse_drop_or_redefine",
            "run_evidence.validate_evidence[EV-HASH-MISMATCH]",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-STRUCTURE-PREFLIGHT",
        inspects="Type parser and type-specific structural checker",
        pass_criterion=(
            "File has one known type, one legal status when applicable, and valid required "
            "metadata"
        ),
        message=(
            "[RUN-STRUCTURE-PREFLIGHT] <item> violates <finding-code>: <detail>. Repair it, run "
            "aw check <type> <selector>, then: aw <host> run --resume <run-id>"
        ),
        action="FAIL ITEM; ABORT RUN if identity/type is ambiguous",
        abort=ABORT_CONDITIONAL,
        abort_classes=("Identity or type ambiguity",),
        binding=BOUND,
        predicates=(
            "ipd_lint.lint_text",
            "ipd_lint.lint_file",
            "check_engine.check_type",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-BASELINE-OWNERSHIP",
        inspects=(
            "Starting HEAD/index/worktree snapshot, pre-existing dirty paths, active path leases"
        ),
        pass_criterion=(
            "No pre-existing or concurrently leased path overlaps this action's mutation scope"
        ),
        message=(
            "[RUN-BASELINE-OWNERSHIP] <paths> already contain unowned changes or an active "
            "lease. Resolve the owner or wait, then: aw <host> run --resume <run-id>"
        ),
        action="ABORT RUN",
        abort=ABORT_ALWAYS,
        abort_classes=("Ownership or lease conflict",),
        binding=BOUND,
        predicates=(
            "worktree_lease.LeaseTable.claim",
            "worktree_lease.assert_worker_scope",
            "run_evidence.dirty_within",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-LEDGER-INTEGRITY",
        inspects=(
            "Append-only event sequence, schema, record hashes, parent links, packet/evidence "
            "digests"
        ),
        pass_criterion=(
            "Ledger is parseable, monotonic, hash-valid, and all referenced evidence exists"
        ),
        message=(
            "[RUN-LEDGER-INTEGRITY] Run <run-id> has invalid or missing ledger evidence at "
            "<record>. Inspect it with: aw runs verify <run-id>"
        ),
        action="ABORT RUN",
        abort=ABORT_ALWAYS,
        abort_classes=("Corrupt run ledger",),
        binding=BOUND,
        predicates=(
            "run_ledger_store.RunLedgerStore.verify_chain",
            "run_ledger_store.BrokenChainError",
            "run_evidence.validate_ledger_evidence",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-HOST-CAPABILITY",
        inspects=(
            "Current descriptor for exact host/version/mode, capability evidence, expiry, and "
            "action requirements"
        ),
        pass_criterion=(
            "Every required host-dependent guarantee is positively supported by current evidence "
            "at the required assurance"
        ),
        message=(
            "[RUN-HOST-CAPABILITY] Host <host> cannot enforce <capability> required by <item> "
            "action <action>. No work started for this item. Choose a capable host or enable and "
            "re-probe that capability, then run: aw <host> run <selector>"
        ),
        action="FAIL ITEM; cascade dependents; continue independent items",
        abort=ABORT_NEVER,
        abort_classes=(),
        binding=BOUND,
        predicates=(
            "host_sandbox_profile.preflight_host_capabilities",
            "host_sandbox_profile.format_host_capability_finding",
            "host_sandbox_profile.check_action_capabilities",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-HOST-ATTEMPT",
        inspects=(
            "Captured argv-list launch event, timeout/cancel state, exit code, stdout/stderr "
            "hashes, terminal envelope"
        ),
        pass_criterion=(
            "Host process was launched by the engine, did not time out, exited 0, and returned a "
            "valid evidence-linked envelope"
        ),
        message=(
            "[RUN-HOST-ATTEMPT] <item> has no valid completed host attempt: <detail>. Inspect "
            "evidence, then retry with: aw <host> run --resume <run-id>"
        ),
        action=(
            "RETRY for spawn/nonzero failures; FAIL ITEM for timeout, cancellation, or exhausted "
            "budget"
        ),
        abort=ABORT_NEVER,
        abort_classes=(),
        binding=BOUND,
        predicates=(
            "run_evidence.capture_command",
            "run_evidence.validate_evidence[EV-FAILED-EXIT]",
            "run_evidence.validate_evidence[EV-MISSING-OUTPUT]",
            "run_evidence.validate_evidence[EV-COMMAND-MISMATCH]",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-FRESH-VERIFIER",
        inspects="Verifier session ID, parentage, packet digest, verifier findings envelope",
        pass_criterion=(
            "Verifier used a fresh session with no executor-session inheritance and addressed the "
            "frozen predicates"
        ),
        message=(
            "[RUN-FRESH-VERIFIER] <item> has no valid independent verification attempt. Retry "
            "verification with: aw <host> run --resume <run-id>"
        ),
        action="RETRY, then FAIL ITEM",
        abort=ABORT_NEVER,
        abort_classes=(),
        binding=BOUND,
        predicates=(
            "agy_verifier.assert_distinct_sessions",
            "agy_verifier.run_fresh_verifier",
            "run_evidence.validate_evidence[EV-EXECUTOR-VERIFIER]",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-SCOPE-DELTA",
        inspects=(
            "`git diff` and untracked paths from the step baseline through the candidate terminal "
            "commit"
        ),
        pass_criterion=(
            "Every action-owned changed path matches the frozen scope; pre-existing and other-run "
            "paths are excluded"
        ),
        message=(
            "[RUN-SCOPE-DELTA] <item> changed out-of-scope paths: <paths>. The changes were "
            "quarantined and restored to baseline. Revise and re-review the scope, then start: "
            "aw <host> run <selector>"
        ),
        action=(
            "FAIL ITEM after containment; cascade dependents; continue independent items"
        ),
        abort=ABORT_NEVER,
        abort_classes=(),
        binding=BOUND,
        predicates=(
            "ipd_lifecycle._frozen_scope_paths",
            "ipd_lifecycle._reconcile_scope",
            "check_engine.check_scope_drift",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-COMMIT-CONTENTS",
        inspects=(
            "Run-owned commits identified by immutable run/item trailers, commit parents, trees, "
            "and action-owned delta"
        ),
        pass_criterion=(
            "A required commit exists; its path union equals the action-owned delta; it contains "
            "no unrelated or pre-existing changes; commit parentage is reconciled"
        ),
        message=(
            "[RUN-COMMIT-CONTENTS] Commit <sha> does not contain exactly the paths owned by "
            "<item>: <detail>. The item was quarantined. Correct its work in a new attempt with: "
            "aw <host> run <selector>"
        ),
        action=(
            "FAIL ITEM after containment; ABORT RUN only if ownership/parentage is ambiguous"
        ),
        abort=ABORT_CONDITIONAL,
        abort_classes=("Ownership or lease conflict",),
        binding=UNBOUND_BY_DEPENDENCY,
        predicates=(),
        waiting_on=(
            "a trailer READ-BACK predicate. `runtrail-01` (`m73aet`) executed and "
            "`git_commit_helper.run_item_trailers` WRITES `AW-Run:`/`AW-Item:`, but nothing reads "
            "a trailer back or proves a commit's tree diff equals the item-owned delta; "
            "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet"
        ),
    ),
    RunFindingCode(
        code="RUN-COMMIT-GATEWAY",
        inspects="Captured commit-gateway event and argv",
        pass_criterion=(
            "The engine, not the agent, invoked `git commit ... -- <explicit paths>` as an argv "
            "list; no `-a`, broad add, shell string, or `--no-verify` occurred"
        ),
        message=(
            "[RUN-COMMIT-GATEWAY] <item> lacks a valid path-scoped, hook-respecting commit "
            "receipt. The item was quarantined. Retry through a capable host with: aw <host> run "
            "<selector>"
        ),
        action="FAIL ITEM after containment; ABORT RUN for a hook-bypass attempt",
        abort=ABORT_CONDITIONAL,
        abort_classes=("Hook-bypass attempt",),
        binding=UNBOUND_BY_DEPENDENCY,
        predicates=(),
        waiting_on=(
            "a captured commit-gateway RECEIPT. `git_commit_helper.offer_commit` is a helper the "
            "driver CHOOSES to call, not a boundary an agent cannot evade, and "
            "`host_sandbox_profile` declares `supports_commit_gateway` False-by-default and NEVER "
            "PROBED for exactly that reason; `m73aet`'s executed receipt states this code "
            "'remains wholly unbuilt'"
        ),
    ),
    RunFindingCode(
        code="RUN-NO-PUSH",
        inspects=(
            "Enforced tool policy, network policy receipt, all captured process events, "
            "starting/ending remote config and remote-tracking refs"
        ),
        pass_criterion=(
            "Capability preflight proved push denial; no push event or unexplained remote-state "
            "change exists"
        ),
        message=(
            "[RUN-NO-PUSH] Host <host> could not prove push prevention for <item>. No work may "
            "start without that capability. Choose a capable host and run: aw <host> run "
            "<selector>"
        ),
        action="FAIL ITEM if refused at preflight; ABORT RUN if a push was attempted",
        abort=ABORT_CONDITIONAL,
        abort_classes=("Push attempt",),
        binding=UNBOUND_UNBUILT,
        predicates=(),
        waiting_on=(
            "host push-denial ENFORCEMENT (backlog `d07nz2`). `host_sandbox_profile` declares "
            "`supports_deny_push` False and NEVER probes it, because no such enforcement exists "
            "in this package; `check_engine.check_push_authorization` is LOCAL, bypassable "
            "pre-push FEEDBACK that explicitly disclaims being an authority boundary, so binding "
            "this code to it would be a fail-open inference"
        ),
    ),
    RunFindingCode(
        code="RUN-CHECK-FRESHNESS",
        inspects=(
            "Check command end times, final product-change time, checked HEAD/worktree digest, "
            "captured outputs"
        ),
        pass_criterion=(
            "Every required check ran after the last relevant change against the exact candidate "
            "state; exit was 0 and required output was nonempty"
        ),
        message=(
            "[RUN-CHECK-FRESHNESS] Check <recipe> is missing, stale, or failed for <item>. Run "
            "the registered check through the runner, then: aw <host> run --resume <run-id>"
        ),
        action="RETRY, then FAIL ITEM",
        abort=ABORT_NEVER,
        abort_classes=(),
        binding=BOUND,
        predicates=(
            "run_evidence.validate_evidence[EV-STALE-HEAD]",
            "run_evidence.validate_evidence[EV-WRONG-CWD]",
            "run_evidence.validate_evidence[EV-WRONG-WORKTREE]",
            "run_evidence.validate_evidence[EV-TRUNCATED-OUTPUT]",
            "run_evidence.get_git_head",
        ),
        waiting_on="",
    ),
    RunFindingCode(
        code="RUN-CROSS-TREE",
        inspects="Full deterministic repository checker",
        pass_criterion=(
            "All reference, release-gate, dependency, status/location, naming, and index "
            "invariants pass"
        ),
        message=(
            "[RUN-CROSS-TREE] Repository invariant <finding-code> failed after <item>: <detail>. "
            "Contain the item, repair it, run aw check all, then: aw <host> run --resume <run-id>"
        ),
        action=(
            "FAIL ITEM; ABORT RUN only for identity/type ambiguity or ownership conflict"
        ),
        abort=ABORT_CONDITIONAL,
        abort_classes=("Identity or type ambiguity", "Ownership or lease conflict"),
        binding=BOUND,
        predicates=(
            "check_engine.check_types",
            "check_engine.check_refs",
            "check_engine.check_release_gate_consistency",
            "check_engine.check_ipd_dependencies",
        ),
        waiting_on="",
    ),
)

#: Code -> row, for O(1) lookup by callers that hold only a code string.
RUN_FINDING_CODES_BY_CODE: Dict[str, RunFindingCode] = {
    row.code: row for row in RUN_FINDING_CODES
}


def run_finding_codes() -> Tuple[str, ...]:
    """The 13 stable finding codes of spec `25kzda` 4.2, in spec order."""
    return tuple(row.code for row in RUN_FINDING_CODES)


def spec_message_for(code: str, **placeholders: Any) -> str:
    """Render a code's VERBATIM spec message, optionally substituting ``<...>`` placeholders.

    With no placeholders the spec template is returned unchanged, which is what a test asserts
    against the spec text. Each ``placeholders`` key names a bare placeholder token (``item``,
    ``run_id`` for ``<run-id>``, ``finding_code`` for ``<finding-code>``, and so on): underscores
    map to hyphens, so ``run_id="r1"`` replaces ``<run-id>``. An UNKNOWN code raises `KeyError`
    rather than returning a plausible-looking string, because a typo'd code must not silently
    produce a message no operator can act on.
    """
    row = RUN_FINDING_CODES_BY_CODE[code]
    message = row.message
    for key, value in placeholders.items():
        message = message.replace("<" + key.replace("_", "-") + ">", str(value))
    return message


def may_abort_run(code: str) -> bool:
    """True when this finding may EVER abort the whole queue (always or conditionally).

    Deliberately reports "may", not "does": spec 4.1 licenses eight of the 13 codes to abort only
    under a named abort class, so a caller deciding to abort must also establish that class. Use
    :func:`abort_classes_for` for it. Reading a conditional row as an unconditional abort would let
    an item-local fault stop a whole queue, which spec 4.1's closing rule forbids.
    """
    return RUN_FINDING_CODES_BY_CODE[code].abort in (ABORT_ALWAYS, ABORT_CONDITIONAL)


def abort_classes_for(code: str) -> Tuple[str, ...]:
    """The spec-4.1 abort classes that license aborting on this finding (empty when it never may)."""
    return RUN_FINDING_CODES_BY_CODE[code].abort_classes


def bound_run_finding_codes() -> Tuple[str, ...]:
    """The codes a shipped predicate actually decides today."""
    return tuple(row.code for row in RUN_FINDING_CODES if row.binding == BOUND)


def unbound_run_finding_codes() -> Tuple[str, ...]:
    """The codes that exist as NAMES with no predicate behind them yet.

    An honest caller reporting one of these must say the check did not run. Treating an unbound code
    as a passing check is the fail-open reading this vocabulary is built to prevent.
    """
    return tuple(row.code for row in RUN_FINDING_CODES if row.binding != BOUND)


def validate_finding_table() -> EvidenceValidationResult:
    """Self-check the table's internal invariants (not the spec text; a test asserts that).

    Enforced here so a later edit cannot quietly break a structural rule:
      * exactly 13 codes, each unique, each named ``RUN-*``;
      * every ``binding`` is a known state, and BOUND rows carry at least one predicate while
        unbound rows carry none and name what they wait on;
      * every ``abort`` is a known tri-state, every ``abort_classes`` entry is one of spec 4.1's
        SIX classes (4.1 is exhaustive), an aborting row names at least one class, and a
        never-aborting row names none;
      * every message begins with its own ``[CODE]`` prefix and ends in a recovery command
        (spec 4.1: "Every recovery message ends with a command").
    """
    findings: List[EvidenceFinding] = []

    def _fail(code: str, where: str, message: str, reason: str) -> None:
        findings.append(EvidenceFinding(code, where, message, reason))

    if len(RUN_FINDING_CODES) != 13:
        _fail(
            "RC-COUNT",
            "RUN_FINDING_CODES",
            f"spec 25kzda 4.2 defines 13 codes, table has {len(RUN_FINDING_CODES)}",
            "finding-code table size does not match the spec",
        )
    seen: Set[str] = set()
    for row in RUN_FINDING_CODES:
        where = row.code
        if row.code in seen:
            _fail(
                "RC-DUPLICATE", where, f"duplicate code {row.code!r}", "duplicate code"
            )
        seen.add(row.code)
        if not row.code.startswith("RUN-"):
            _fail(
                "RC-NAME", where, f"{row.code!r} is not a RUN-* code", "bad code name"
            )
        if row.binding not in BINDING_STATES:
            _fail(
                "RC-BINDING",
                where,
                f"unknown binding state {row.binding!r}",
                "unknown binding state",
            )
        if row.binding == BOUND:
            if not row.predicates:
                _fail(
                    "RC-BINDING",
                    where,
                    "BOUND code names no deciding predicate",
                    "a BOUND code must name the shipped predicate that decides it",
                )
            if row.waiting_on:
                _fail(
                    "RC-BINDING",
                    where,
                    "BOUND code also declares waiting_on",
                    "a BOUND code waits on nothing",
                )
        else:
            if row.predicates:
                _fail(
                    "RC-BINDING",
                    where,
                    "unbound code names predicates",
                    "an unbound code must not claim a deciding predicate",
                )
            if not row.waiting_on:
                _fail(
                    "RC-BINDING",
                    where,
                    "unbound code does not say what it waits on",
                    "an unbound code must name the missing machinery",
                )
        if row.abort not in (ABORT_ALWAYS, ABORT_CONDITIONAL, ABORT_NEVER):
            _fail(
                "RC-ABORT",
                where,
                f"unknown abort state {row.abort!r}",
                "bad abort state",
            )
        for cls in row.abort_classes:
            if cls not in ABORT_CLASSES:
                _fail(
                    "RC-ABORT-CLASS",
                    where,
                    f"{cls!r} is not one of spec 4.1's six abort classes",
                    "spec 4.1's abort-class set is exhaustive",
                )
        if row.abort == ABORT_NEVER and row.abort_classes:
            _fail(
                "RC-ABORT-CLASS",
                where,
                "a never-aborting code names abort classes",
                "only an aborting code may name an abort class",
            )
        if row.abort != ABORT_NEVER and not row.abort_classes:
            _fail(
                "RC-ABORT-CLASS",
                where,
                "an aborting code names no spec 4.1 abort class",
                "an abort must cite one of the six enumerated classes",
            )
        if not row.message.startswith("[" + row.code + "]"):
            _fail(
                "RC-MESSAGE",
                where,
                "message does not begin with its own [CODE] prefix",
                "operator-facing message must carry its code",
            )
        if ": aw " not in row.message:
            _fail(
                "RC-RECOVERY",
                where,
                "message does not end in a recovery command",
                "spec 4.1: every recovery message ends with a command",
            )
    return EvidenceValidationResult(len(findings) == 0, tuple(findings))


# ==================================================================================================
# runcodes Order 2 (`zub5f1`) E-01 / E-02: `--unverifiable-ok` aggregate neutrality
# ==================================================================================================
#
# WHAT THIS IS. Spec `25kzda` 2.1 and 4.10 specify `--unverifiable-ok`, a flag that makes an
# unverifiable item NEUTRAL in the AGGREGATE exit-code calculation while leaving the item's own
# outcome and verification label UNTOUCHED. This block is that aggregation rule, as a PURE function
# over already-decided per-item results: no ledger, no subprocess, no run directory, no live run.
# Purity is the point, not a style preference - the whole rule is then testable in isolation, and
# the two defects it can realistically ship (see below) are both provable by a unit test.
#
# THE FLAG IS DOUBLY CONSTRAINED AND BOTH CONSTRAINTS ARE THE POINT.
#   1. It may change ONLY the aggregate. Spec 4.10's `PROMPT-UNVERIFIABLE` row fixes the item at
#      `outcome: ran`, `verification: unavailable` REGARDLESS of the flag, so an implementation that
#      relabeled the item under the flag would satisfy a naive aggregate test while breaking the
#      actual contract. :func:`aggregate_run_exit` therefore never authors an item's outcome or
#      label; it reads them and passes them through unchanged (see `ItemAggregation.item`).
#   2. It is LEGAL ONLY after contractless prompts were admitted (spec 2.1: "legal only when
#      contractless prompts were explicitly admitted by `--allow-unverifiable` or the interactive
#      `run unverifiable` confirmation"). Honoring it standalone would be the fail-OPEN reading of
#      the same words, so a standalone invocation is REFUSED and falls back to the DEFAULT
#      (non-neutral) aggregate.
#
# WHY A THREE-VALUED CONTRIBUTION AND NOT AN INTEGER SUM. Spec 4.10 phrases the default as "exit
# contribution 1 ... or neutral", which invites summing integers. That design cannot express the
# rule: a VERIFIED item also contributes 0, and spec 5.6 grants exit 0 only when "every other
# actionable item is verified and every other skip is benign". So "every other item verified plus
# one neutral" (exit 0) and "one neutral plus one non-verified skip" (NOT exit 0) have the same
# integer sum and must produce different exits. Contributions are therefore the three named values
# :data:`CONTRIBUTION_SUCCESS` / :data:`CONTRIBUTION_NEUTRAL` / :data:`CONTRIBUTION_FAILURE`, and
# integers appear in exactly ONE place: :data:`_CLASSIFICATION_EXITS`, the mapping onto spec 5.6's
# exit table.
#
# WHICH EXIT TABLE. Spec 5.6's RUN table (0/1/2/3/4/130), NOT `run_cli.py`'s constants. This package
# ships TWO exit tables that DISAGREE at the same numbers: `run_cli.EXIT_BLOCKED` is 3 and
# `run_cli.EXIT_INVALID_EVIDENCE` is 4, whereas spec 5.6's 3 is "human input required" and its 4 is
# the six run-wide classes. `run_cli`'s table governs the READ-ONLY inspection commands
# (`aw runs show|evidence|verify-ledger`); this predicate implements the RUN aggregate. Reconciling
# the two tables is a separate concern that no plan currently owns; naming the one in force is the
# cheap correct move for the next reader.
#
# THE PER-ITEM VOCABULARY IS NOT DEFINED HERE, AND IS NOT YET BUILT ANYWHERE. Spec 5.6's `ran`
# outcome and 4.10's `unavailable` / `verification_unavailable` labels grep to ZERO in this package
# (measured): `run_state.ALL_STATES` is the step/run state machine (`pending`..`complete`, no `ran`)
# and `run_ledger_schema.LANE_OUTCOMES` is `performed|blocked|failed|deferred|unknown_outcome|
# skipped`. That vocabulary belongs to the runner surface, which this plan explicitly excludes. So
# an :class:`AggregatedItem` carries its outcome and verification label as OPAQUE pass-through
# strings and keys neutrality off the explicit :attr:`AggregatedItem.unverifiable` flag, never off a
# string this module invents.
#
# NO CONSUMER YET, STATED PLAINLY. Neither `--unverifiable-ok` nor its precondition
# `--allow-unverifiable` (nor the interactive `run unverifiable` confirmation) exists as a CLI
# surface: all three grep to zero outside a prose comment at `run_selection_policy.py:168`. When
# they are built (owned by `runflags-01` / `uyeko5`) they bind to this function's
# ``unverifiable_ok`` and ``unverifiable_admitted`` PARAMETERS. Until then NO operator can reach
# this rule; it lands tested and importable and nothing consults it yet.


# ---- per-item aggregate contribution (three-valued; see the note above) ---------------------------

#: The item helps the run reach exit 0: it is deterministically verified, or a benign skip.
CONTRIBUTION_SUCCESS = "success"
#: The item neither helps nor blocks exit 0. DISTINCT FROM SUCCESS: a run of one neutral item plus
#: one non-verified item is NOT exit 0, because spec 5.6 requires every OTHER actionable item to be
#: verified. Collapsing neutral into success is the defect this value exists to prevent.
CONTRIBUTION_NEUTRAL = "neutral"
#: The item blocks exit 0.
CONTRIBUTION_FAILURE = "failure"

CONTRIBUTIONS: Tuple[str, ...] = (
    CONTRIBUTION_SUCCESS,
    CONTRIBUTION_NEUTRAL,
    CONTRIBUTION_FAILURE,
)


# ---- aggregate classifications, and the ONE place integers appear --------------------------------

#: Every actionable item verified; remaining items benign skips; any contractless `ran`/`unavailable`
#: item was made aggregate-neutral by frozen `--unverifiable-ok` (spec 5.6 exit 0).
AGGREGATE_ALL_CLEAR = "all_clear"
#: At least one item failed, ended `dependency_not_met`, or ended `ran`/`unavailable` without the
#: flag; no run-wide integrity failure (spec 5.6 exit 1).
AGGREGATE_ITEM_FAILURE = "item_failure"
#: Invalid invocation, selector, or unknown type (spec 5.6 exit 2). A REFUSED `--unverifiable-ok`
#: is NOT reported here: see :func:`aggregate_run_exit`'s refusal note.
AGGREGATE_INVALID_INVOCATION = "invalid_invocation"
#: Human input or explicit acknowledgement is required (spec 5.6 exit 3).
AGGREGATE_NEEDS_INPUT = "needs_input"
#: One of spec 4.1's six enumerated run-wide classes (spec 5.6 exit 4).
AGGREGATE_RUN_WIDE = "run_wide"
#: User interruption (spec 5.6 exit 130).
AGGREGATE_INTERRUPTED = "interrupted"

#: THE ONLY PLACE INTEGERS APPEAR. Spec `25kzda` 5.6's run exit table, transcribed. Deliberately
#: NOT `run_cli.py`'s inspection-command constants, which mean different things at 3 and 4.
_CLASSIFICATION_EXITS: Dict[str, int] = {
    AGGREGATE_ALL_CLEAR: 0,
    AGGREGATE_ITEM_FAILURE: 1,
    AGGREGATE_INVALID_INVOCATION: 2,
    AGGREGATE_NEEDS_INPUT: 3,
    AGGREGATE_RUN_WIDE: 4,
    AGGREGATE_INTERRUPTED: 130,
}

#: Priority order, HIGHEST FIRST. Spec 5.6 says a default-contributing unverifiable item yields
#: "exit 1 unless a higher-priority exit applies", and spec's non-maskable list keeps a human gate
#: and a run-wide class outranking a neutralized item. Encoding the precedence as DATA is what makes
#: that rule checkable rather than an emergent property of `if` ordering.
_CLASSIFICATION_PRIORITY: Tuple[str, ...] = (
    AGGREGATE_INTERRUPTED,
    AGGREGATE_RUN_WIDE,
    AGGREGATE_NEEDS_INPUT,
    AGGREGATE_INVALID_INVOCATION,
    AGGREGATE_ITEM_FAILURE,
    AGGREGATE_ALL_CLEAR,
)


# ---- the six classes `--unverifiable-ok` may NEVER mask (spec 25kzda `:938`) ----------------------
#
# CARRIED AS DATA, NOT PROSE. Spec 5.6 closes the unverifiable rule with an EXHAUSTIVE list of what
# the flag cannot mask. A prose-only guard ("other items still fail") does not cover a human gate
# (exit 3) or a run-wide class (exit 4) being OUTRANKED rather than merely non-neutral, so the list
# is enumerable and a test asserts against it. Each entry names the shipped representation the
# aggregate recognizes, or records honestly that there is none yet.


class NonMaskableClass(NamedTuple):
    """One row of spec `25kzda` `:938`: a class `--unverifiable-ok` may never mask.

    Fields:
      * ``name``        - the class, in the spec's own words.
      * ``aggregate``   - the aggregate classification an item of this class forces. A class whose
                          classification outranks :data:`AGGREGATE_ITEM_FAILURE` is one the flag
                          cannot mask BY OUTRANKING, which is stricter than merely not neutralizing.
      * ``represented`` - True when this tree ships a way to signal the class to the aggregate.
      * ``signal``      - how a caller signals it (an :class:`AggregatedItem` field plus value, or a
                          run-wide argument), or the missing machinery when ``represented`` is False.
    """

    name: str
    aggregate: str
    represented: bool
    signal: str


NON_MASKABLE_CLASSES: Tuple[NonMaskableClass, ...] = (
    NonMaskableClass(
        name="a failed prompt process",
        aggregate=AGGREGATE_ITEM_FAILURE,
        represented=True,
        signal="AggregatedItem(contribution_hint=CONTRIBUTION_FAILURE) i.e. outcome `failed`",
    ),
    NonMaskableClass(
        name="scope/containment failure",
        aggregate=AGGREGATE_ITEM_FAILURE,
        represented=True,
        signal="AggregatedItem(contribution_hint=CONTRIBUTION_FAILURE); decided upstream by "
        "ipd_lifecycle._reconcile_scope / check_engine.check_scope_drift (RUN-SCOPE-DELTA)",
    ),
    NonMaskableClass(
        name="host-capability refusal",
        aggregate=AGGREGATE_ITEM_FAILURE,
        represented=True,
        signal="AggregatedItem(contribution_hint=CONTRIBUTION_FAILURE); decided upstream by "
        "host_sandbox_profile.preflight_host_capabilities (RUN-HOST-CAPABILITY)",
    ),
    NonMaskableClass(
        name="dependency-not-met item",
        aggregate=AGGREGATE_ITEM_FAILURE,
        represented=True,
        signal="AggregatedItem(dependency_not_met=True)",
    ),
    NonMaskableClass(
        name="human gate",
        aggregate=AGGREGATE_NEEDS_INPUT,
        represented=True,
        signal="AggregatedItem(needs_input=True), matching run_gates.GATE_STATUS_NEEDS_INPUT",
    ),
    NonMaskableClass(
        name="run-wide abort class",
        aggregate=AGGREGATE_RUN_WIDE,
        represented=True,
        signal="aggregate_run_exit(run_wide_abort_class=<one of ABORT_CLASSES>)",
    ),
)


# ---- the aggregation inputs and result -----------------------------------------------------------


class AggregatedItem(NamedTuple):
    """One already-decided per-item result, as INPUT to the aggregate.

    THIS TYPE DECIDES NOTHING ABOUT THE ITEM. Its ``outcome`` and ``verification`` are OPAQUE
    pass-through strings this module never authors, compares against a vocabulary of its own, or
    rewrites (see the block note: spec 5.6's `ran` and 4.10's `unavailable` are not built anywhere
    in this package yet, and minting them here is outside this plan's fence). Neutrality is keyed
    off :attr:`unverifiable`, an explicit boolean the caller sets, so the aggregate never has to
    guess a label's meaning.

    Fields:
      * ``item_id``            - opaque identifier, for reporting only.
      * ``outcome``            - the item's own final outcome, PASSED THROUGH UNCHANGED.
      * ``verification``       - the item's own verification label, PASSED THROUGH UNCHANGED.
      * ``unverifiable``       - True for an explicitly acknowledged contractless prompt that ran to
                                transport completion (spec 4.10 `PROMPT-UNVERIFIABLE`). This, and
                                only this, is what `--unverifiable-ok` may neutralize.
      * ``verified``           - True when every required deterministic predicate passed. Only a
                                verified item (or a benign skip) can help a run reach exit 0.
      * ``benign_skip``        - True for a skip that spec 5.6 counts as benign (a non-runnable type,
                                a terminal/standing status). A NON-benign skip is not verified and
                                therefore blocks exit 0.
      * ``dependency_not_met`` - True for spec `:938`'s dependency-not-met class.
      * ``needs_input``        - True when a human gate stopped the item (spec `:938`).
      * ``contribution_hint``  - an explicit contribution for a class with no dedicated field
                                (notably a plain failure). ``None`` means "derive it".
    """

    item_id: str
    outcome: str = ""
    verification: str = ""
    unverifiable: bool = False
    verified: bool = False
    benign_skip: bool = False
    dependency_not_met: bool = False
    needs_input: bool = False
    contribution_hint: Optional[str] = None


class ItemAggregation(NamedTuple):
    """How ONE item contributed, alongside the item it contributed for.

    ``item`` is the input :class:`AggregatedItem`, carried through BY IDENTITY. That is the
    machine-checkable form of spec 4.10's constraint: the aggregate cannot have relabeled an item
    whose record it merely re-exposes.
    """

    item: AggregatedItem
    contribution: str
    reason: str


class RunAggregation(NamedTuple):
    """The aggregate verdict: a classification, its spec-5.6 exit code, and why.

    Fields:
      * ``classification``   - one of the ``AGGREGATE_*`` values.
      * ``exit_code``        - spec 5.6's code for that classification. THE ONLY INTEGER HERE.
      * ``items``            - per-item contributions, in input order, each carrying its untouched
                               source item.
      * ``reasons``          - stable explanation strings, the shape this module already uses for a
                               negative verdict (:attr:`CompletionEvaluation.reasons`).
      * ``refusals``         - illegal-invocation refusals as DATA, in the module's existing
                               :class:`CompletionPredicate` shape. Non-empty means a requested
                               policy was NOT applied.
      * ``unverifiable_ok_applied`` - whether neutrality was ACTUALLY applied. False whenever the
                               flag was refused, so a caller cannot mistake a refusal for a grant.
    """

    classification: str
    exit_code: int
    items: Tuple[ItemAggregation, ...]
    reasons: Tuple[str, ...]
    refusals: Tuple[CompletionPredicate, ...]
    unverifiable_ok_applied: bool


#: The refusal predicate name for a standalone `--unverifiable-ok` (E-02).
REFUSAL_UNVERIFIABLE_OK_UNADMITTED = "unverifiable_ok_requires_admission"


def non_maskable_classes() -> Tuple[str, ...]:
    """Spec `25kzda` `:938`'s classes that `--unverifiable-ok` may never mask, in spec order."""
    return tuple(row.name for row in NON_MASKABLE_CLASSES)


def classify_item_contribution(
    item: AggregatedItem,
    *,
    unverifiable_ok: bool = False,
) -> ItemAggregation:
    """Classify ONE item's aggregate contribution as :data:`CONTRIBUTIONS`, three-valued.

    PURE: data in, data out. The item's ``outcome`` and ``verification`` are read and carried, never
    written - the returned :class:`ItemAggregation` holds the SAME :class:`AggregatedItem`, so
    ``result.item is item``.

    ``unverifiable_ok`` here is the ALREADY-VALIDATED policy: :func:`aggregate_run_exit` owns the
    admission precondition and passes False when it refused, so this function cannot be the place a
    standalone flag leaks through.
    """
    if item.needs_input:
        return ItemAggregation(
            item, CONTRIBUTION_FAILURE, "human gate stopped the item"
        )
    if item.dependency_not_met:
        return ItemAggregation(item, CONTRIBUTION_FAILURE, "dependency not met")
    if item.contribution_hint is not None:
        if item.contribution_hint not in CONTRIBUTIONS:
            return ItemAggregation(
                item,
                CONTRIBUTION_FAILURE,
                f"unknown contribution hint {item.contribution_hint!r}",
            )
        # A caller may not hint an unverifiable item into neutrality or success: that decision
        # belongs to the flag, checked below, and nowhere else.
        if item.unverifiable and item.contribution_hint != CONTRIBUTION_FAILURE:
            return ItemAggregation(
                item,
                CONTRIBUTION_FAILURE,
                "an unverifiable item's contribution is decided by --unverifiable-ok, not by a hint",
            )
        return ItemAggregation(
            item, item.contribution_hint, f"explicit hint {item.contribution_hint}"
        )
    if item.unverifiable:
        # SPEC 4.10 / 5.6, THE WHOLE POINT OF THIS MODULE BLOCK. The item's own outcome and
        # verification label are identical on both branches; only the contribution differs.
        if unverifiable_ok:
            return ItemAggregation(
                item,
                CONTRIBUTION_NEUTRAL,
                "unverifiable, made aggregate-neutral by frozen --unverifiable-ok",
            )
        return ItemAggregation(
            item,
            CONTRIBUTION_FAILURE,
            "unverifiable and --unverifiable-ok was not frozen",
        )
    if item.verified:
        return ItemAggregation(item, CONTRIBUTION_SUCCESS, "deterministically verified")
    if item.benign_skip:
        return ItemAggregation(item, CONTRIBUTION_SUCCESS, "benign skip")
    return ItemAggregation(
        item, CONTRIBUTION_FAILURE, "neither verified nor a benign skip"
    )


def aggregate_run_exit(
    items: Sequence[AggregatedItem],
    *,
    unverifiable_ok: bool = False,
    unverifiable_admitted: bool = False,
    invalid_invocation: Optional[str] = None,
    run_wide_abort_class: Optional[str] = None,
    interrupted: bool = False,
) -> RunAggregation:
    """The aggregate exit classification for a run, as a PURE function (spec `25kzda` 5.6).

    Pure means exactly what it says: no ledger, no run directory, no subprocess, no clock, no
    filesystem. It takes already-decided per-item results and returns a value, which is why the
    whole `--unverifiable-ok` rule is provable by a unit test with no live run.

    THE PRECONDITION (E-02, spec 2.1). ``unverifiable_ok`` is legal ONLY when contractless prompts
    were explicitly admitted. ``unverifiable_admitted`` is that admission. Passing
    ``unverifiable_ok=True`` with ``unverifiable_admitted=False`` is REFUSED: the returned
    :attr:`RunAggregation.refusals` names the missing precondition, :attr:`unverifiable_ok_applied`
    is False, and the aggregate is the DEFAULT one in which an unverifiable item contributes
    :data:`CONTRIBUTION_FAILURE`. It is NOT reported as an invalid invocation (exit 2), because
    downgrading a fail-closed refusal into "your command line was malformed" would lose the actual
    verdict about the items; and it is emphatically NOT honored, because silently granting
    neutrality to an unadmitted flag is the fail-OPEN reading spec 2.1 forbids.

    REFUSAL IS RETURNED AS DATA, NEVER RAISED. This module reports every negative verdict as a
    value (:class:`CompletionPredicate` plus accumulated ``reasons``; compare
    ``EV-REDACTION-CONFLICT``, which reports "verification could not conclude" as a finding). It
    contains zero ``raise`` statements and defines no exception class, and a raise would also defeat
    purity in practice, since a caller could not evaluate the aggregate in order to inspect it.

    THE FLAG'S LIMITS (spec `:936`, `:938`). Neutrality is narrow. It never suppresses another
    item's failure, and it never outranks a higher-priority exit: a human gate still yields exit 3
    and a run-wide abort class still yields exit 4. Those limits are carried as data in
    :data:`NON_MASKABLE_CLASSES` and :data:`_CLASSIFICATION_PRIORITY`.

    NEITHER FLAG EXISTS AS A CLI SURFACE YET (`--unverifiable-ok`, `--allow-unverifiable`, and the
    interactive `run unverifiable` confirmation all grep to zero). They arrive here as parameters;
    `runflags-01` (`uyeko5`) owns building them and binding them to these two arguments.
    """
    reasons: List[str] = []
    refusals: List[CompletionPredicate] = []

    # ---- E-02: the admission precondition, checked BEFORE the flag can affect anything ----------
    effective_unverifiable_ok = bool(unverifiable_ok)
    if unverifiable_ok and not unverifiable_admitted:
        effective_unverifiable_ok = False
        refusals.append(
            CompletionPredicate(
                REFUSAL_UNVERIFIABLE_OK_UNADMITTED,
                False,
                "--unverifiable-ok is legal only when contractless prompts were explicitly "
                "admitted by --allow-unverifiable or the interactive `run unverifiable` "
                "confirmation; that admission is absent, so aggregate neutrality was NOT applied "
                "and the default aggregate stands",
            )
        )
        reasons.append(
            "refused --unverifiable-ok: missing precondition (contractless prompts were not "
            "explicitly admitted)"
        )

    item_results = tuple(
        classify_item_contribution(item, unverifiable_ok=effective_unverifiable_ok)
        for item in items
    )

    candidates: List[str] = []
    if interrupted:
        candidates.append(AGGREGATE_INTERRUPTED)
        reasons.append("run was interrupted")
    if run_wide_abort_class is not None:
        candidates.append(AGGREGATE_RUN_WIDE)
        if run_wide_abort_class in ABORT_CLASSES:
            reasons.append(f"run-wide abort class: {run_wide_abort_class}")
        else:
            # Spec 4.1's set is EXHAUSTIVE, so an unknown class is still run-wide (never silently
            # downgraded) but is reported as unrecognized rather than laundered into a known one.
            reasons.append(
                f"run-wide abort class {run_wide_abort_class!r} is not one of spec 4.1's six "
                "enumerated classes"
            )
    if any(result.item.needs_input for result in item_results):
        candidates.append(AGGREGATE_NEEDS_INPUT)
        reasons.append("a human gate requires input")
    if invalid_invocation is not None:
        candidates.append(AGGREGATE_INVALID_INVOCATION)
        reasons.append(f"invalid invocation: {invalid_invocation}")
    # A human-gated item ALSO contributes failure (it is certainly not success), and that is
    # deliberate: it is _CLASSIFICATION_PRIORITY, not an `if` here, that makes exit 3 outrank exit 1.
    # Keeping the precedence in one data table is what lets a test assert it directly.
    if any(result.contribution == CONTRIBUTION_FAILURE for result in item_results):
        candidates.append(AGGREGATE_ITEM_FAILURE)
        for result in item_results:
            if result.contribution == CONTRIBUTION_FAILURE:
                reasons.append(f"{result.item.item_id}: {result.reason}")
    if not candidates:
        candidates.append(AGGREGATE_ALL_CLEAR)

    classification = next(c for c in _CLASSIFICATION_PRIORITY if c in candidates)
    return RunAggregation(
        classification=classification,
        exit_code=_CLASSIFICATION_EXITS[classification],
        items=item_results,
        reasons=tuple(reasons),
        refusals=tuple(refusals),
        unverifiable_ok_applied=effective_unverifiable_ok,
    )


def validate_non_maskable_table() -> EvidenceValidationResult:
    """Self-check :data:`NON_MASKABLE_CLASSES` (structure only; a test asserts the spec text).

    Enforced so a later edit cannot quietly weaken the list:
      * exactly six classes, spec `:938` being exhaustive, each named once;
      * every ``aggregate`` is a known classification that maps to an exit code;
      * no row's aggregate is :data:`AGGREGATE_ALL_CLEAR`, since a class that could yield exit 0
        would BE masked;
      * every row says how it is signalled, whether or not it is represented.
    """
    findings: List[EvidenceFinding] = []
    if len(NON_MASKABLE_CLASSES) != 6:
        findings.append(
            EvidenceFinding(
                "NM-COUNT",
                "NON_MASKABLE_CLASSES",
                f"spec 25kzda :938 enumerates 6 classes, table has {len(NON_MASKABLE_CLASSES)}",
                "non-maskable class table size does not match the spec",
            )
        )
    seen: Set[str] = set()
    for row in NON_MASKABLE_CLASSES:
        if row.name in seen:
            findings.append(
                EvidenceFinding(
                    "NM-DUPLICATE", row.name, "duplicate class", "duplicate class"
                )
            )
        seen.add(row.name)
        if row.aggregate not in _CLASSIFICATION_EXITS:
            findings.append(
                EvidenceFinding(
                    "NM-AGGREGATE",
                    row.name,
                    f"unknown aggregate classification {row.aggregate!r}",
                    "unknown aggregate classification",
                )
            )
        elif row.aggregate == AGGREGATE_ALL_CLEAR:
            findings.append(
                EvidenceFinding(
                    "NM-AGGREGATE",
                    row.name,
                    "a non-maskable class may not classify as all-clear",
                    "a class that can yield exit 0 would be masked",
                )
            )
        if not row.signal:
            findings.append(
                EvidenceFinding(
                    "NM-SIGNAL",
                    row.name,
                    "row does not say how the class is signalled",
                    "every class must name its signal or its missing machinery",
                )
            )
    return EvidenceValidationResult(len(findings) == 0, tuple(findings))
