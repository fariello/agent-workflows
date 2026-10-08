"""Normative schema, validation, and serialization for the aw.agent/v1 protocol.

awcliux Order 03 (`8su0r3`) E-01 / E-02 / E-03.

Defines the closed record kinds, mandatory envelope fields, exit code classification,
anti-greenwashing outcome invariants, repo-relative path sanitization, and token-control
filtering for the machine convention. Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from agent_workflows.home_path_patterns import fused_home_path_pattern

# --------------------------------------------------------------------------------------------------
# Schema Constants
# --------------------------------------------------------------------------------------------------

SCHEMA_VERSION: str = "aw.agent/v1"

# Closed set of valid record kinds
RECORD_KINDS: tuple[str, ...] = ("result", "summary", "item", "error")

# Valid outcome states
VALID_OUTCOMES: tuple[str, ...] = (
    "clean",
    "ok",
    "conforms",
    "findings",
    "fail",
    "preview",
    "stale",
    "skipped",
    "partial",
    "unverified",
    "changed-unverified",
    "cannot-run",
    "error",
)

# Outcomes that signify complete success (MUST NEVER be used for skipped, partial,
# unverified, or cannot-run work)
POSITIVE_OUTCOMES: tuple[str, ...] = ("clean", "ok", "conforms")

# Incomplete or non-success outcomes
INCOMPLETE_OUTCOMES: tuple[str, ...] = (
    "skipped",
    "partial",
    "unverified",
    "changed-unverified",
    "cannot-run",
    "error",
    "findings",
    "fail",
)

# ANSI escape sequence regex pattern
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\033\[[0-9;]*[a-zA-Z]")

# Unsanitized path patterns (home paths, usernames, absolute OS prefixes)
# Derived from home_path_patterns (single source of truth, P8).
_HOME_PATH_RE = re.compile(fused_home_path_pattern())


# --------------------------------------------------------------------------------------------------
# Path and Evidence Sanitization
# --------------------------------------------------------------------------------------------------


_DRIVE_ABS_RE = re.compile(r"^[A-Za-z]:/")


def _relative_to_root(path: str, repo_root: str) -> Optional[str]:
    """Return ``path`` relative to ``repo_root`` as a forward-slashed string, or None if outside.

    Both sides are compared as ``os.path.normcase(os.path.realpath(...))`` so an 8.3 short name,
    a symlinked parent, or a case difference on a case-insensitive filesystem cannot defeat the
    match. A relative ``path`` is taken relative to ``repo_root``, matching how callers report it.
    """

    try:
        root_n = os.path.normcase(os.path.realpath(repo_root))
        p = path if os.path.isabs(path) else os.path.join(repo_root, path)
        p_n = os.path.normcase(os.path.realpath(p))
        if os.path.splitdrive(root_n)[0] != os.path.splitdrive(p_n)[0]:
            return None
        rel = os.path.relpath(p_n, root_n)
    except (OSError, ValueError):
        return None
    if rel == os.curdir:
        return "."
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return None
    # `normcase` lowercases on Windows; recover the caller's casing from the original path tail
    # when the component count matches so the emitted path keeps its real spelling.
    parts = rel.split(os.sep)
    orig_parts = [x for x in path.replace("\\", "/").split("/") if x]
    if (
        len(orig_parts) >= len(parts)
        and [os.path.normcase(x) for x in orig_parts[-len(parts) :]] == parts
    ):
        parts = orig_parts[-len(parts) :]
    return "/".join(parts)


def normalize_repo_path(
    path: Union[str, Path], repo_root: Optional[Union[str, Path]] = None
) -> str:
    """Normalize a filesystem path to be repo-relative, forward-slashed, and sanitizer-clean.

    Never returns absolute paths, home directories, usernames, or hostnames.
    """
    if not path:
        return ""

    path_str = str(path).replace("\\", "/")

    # If repo_root is provided, make path relative to repo_root. Compare NORMALIZED RESOLVED forms
    # (realpath + normcase) rather than raw strings: the same directory is routinely spelled two ways
    # (a Windows 8.3 short name such as `EXAMPL~1` from `tempfile` versus the long name `resolve()`
    # yields, or a macOS/Linux symlinked TMPDIR), and a spelling mismatch must not leak the absolute
    # path into an agent record.
    if repo_root is not None:
        rel_str = _relative_to_root(path_str, str(repo_root))
        if rel_str is not None:
            return rel_str

    # If the path looks absolute (POSIX `/...`, a Windows drive `C:/...`, or UNC `//host/...`),
    # strip it down to a relative tail. Without the drive-letter case a Windows absolute path fell
    # through unchanged and tripped the home-path validator.
    if _DRIVE_ABS_RE.match(path_str):
        path_str = path_str[2:]
    if path_str.startswith("/"):
        parts = [p for p in path_str.split("/") if p]
        # Look for well-known repo subdirs or keep trailing 2-3 components
        known_markers = (
            ".aw",
            ".agents",
            "agent_workflows",
            "tests",
            "docs",
            "plans",
            "records",
        )
        for i, part in enumerate(parts):
            if part in known_markers:
                return "/".join(parts[i:])
        # If no marker, strip root slashes
        return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]

    # Clean leading ./
    if path_str.startswith("./"):
        path_str = path_str[2:]

    return path_str


_REDACT_WINDOWS_HOME_RE = re.compile(r"([A-Za-z]:[\\/]+Users[\\/]+)[A-Za-z0-9._-]+")
_REDACT_POSIX_HOME_RE = re.compile(r"/home/[A-Za-z0-9._-]+")
_REDACT_USERS_HOME_RE = re.compile(r"(?<![A-Za-z]:)/Users/[A-Za-z0-9._-]+")


def redact_home_paths(text: Any) -> Any:
    """Redact home-style absolute path prefixes inside a string to '~'.

    Performs a lossy, idempotent rewrite of embedded home directory paths across
    all three classes detected by `_HOME_PATH_RE` (sourced from the shared
    `home_path_patterns` datum: POSIX `/home/<user>`, macOS `/Users/<user>`,
    and Windows `<drive>:\\Users\\<user>`).

    This is the counterpart that `normalize_repo_path` cannot serve because it operates
    on a whole path value rather than on paths embedded within free text (such as
    suggested command lines, diagnostic details, or summaries). Non-string inputs
    are returned unchanged.
    """
    if not isinstance(text, str):
        return text

    # Redact Windows paths first so drive prefixes remain intact
    text = _REDACT_WINDOWS_HOME_RE.sub(r"\g<1>~", text)
    text = _REDACT_POSIX_HOME_RE.sub("~", text)
    text = _REDACT_USERS_HOME_RE.sub("~", text)
    return text


def sanitize_evidence_item(
    evidence_obj: Any, repo_root: Optional[Union[str, Path]] = None
) -> Any:
    """Sanitize an evidence item so it names what was checked (e.g. check key/identifier)
    rather than raw file contents, secrets, or unsanitized absolute paths.
    """
    if hasattr(evidence_obj, "key"):
        # Evidence dataclass
        key = str(evidence_obj.key)
        val = getattr(evidence_obj, "value", None)
        if isinstance(val, (int, float, bool)):
            return f"{key}:{val}"
        if (
            isinstance(val, str)
            and not _ANSI_ESCAPE_RE.search(val)
            and not _HOME_PATH_RE.search(val)
        ):
            return f"{key}:{normalize_repo_path(val, repo_root)}"
        return key
    elif isinstance(evidence_obj, dict):
        key = str(evidence_obj.get("key", ""))
        val = evidence_obj.get("value")
        if isinstance(val, (int, float, bool)):
            return f"{key}:{val}" if key else str(val)
        if (
            isinstance(val, str)
            and not _ANSI_ESCAPE_RE.search(val)
            and not _HOME_PATH_RE.search(val)
        ):
            norm_val = normalize_repo_path(val, repo_root)
            return f"{key}:{norm_val}" if key else norm_val
        return key if key else "evidence"
    elif isinstance(evidence_obj, str):
        if _HOME_PATH_RE.search(evidence_obj):
            return normalize_repo_path(evidence_obj, repo_root)
        return evidence_obj
    return str(evidence_obj)


# --------------------------------------------------------------------------------------------------
# Schema Validation
# --------------------------------------------------------------------------------------------------


def validate_agent_record(record: Dict[str, Any]) -> List[str]:
    """Validate an aw.agent/v1 record against schema requirements and integrity invariants.

    Returns a list of error strings. If valid, returns an empty list.
    """
    errors: List[str] = []

    # 1. Schema version
    schema = record.get("schema")
    if schema != SCHEMA_VERSION:
        errors.append(f"Invalid schema: expected '{SCHEMA_VERSION}', got '{schema}'")

    # 2. Kind
    kind = record.get("kind")
    if kind not in RECORD_KINDS:
        errors.append(f"Invalid kind: '{kind}' must be one of {RECORD_KINDS}")

    # 3. Command
    cmd = record.get("cmd")
    if not isinstance(cmd, str) or not cmd.strip():
        errors.append("Field 'cmd' must be a non-empty string")

    # Exit code and outcome validation for result, summary, error (optional for item)
    if kind in ("result", "summary", "error"):
        # 4. Exit code
        exit_code = record.get("exit")
        if (
            exit_code is None
            or not isinstance(exit_code, int)
            or exit_code not in (0, 1, 2)
        ):
            errors.append(
                f"Field 'exit' must be an integer in (0, 1, 2), got '{exit_code}'"
            )

        # 5. Outcome
        outcome = record.get("outcome")
        if not isinstance(outcome, str):
            errors.append(f"Field 'outcome' must be a string, got '{type(outcome)}'")
        elif outcome not in VALID_OUTCOMES:
            errors.append(
                f"Unknown outcome '{outcome}'; expected one of {VALID_OUTCOMES}"
            )

    # 6. Kind-specific mandatory fields and invariants
    if kind == "result":
        outcome = record.get("outcome")
        exit_code = record.get("exit")
        if "verified" not in record or not isinstance(record["verified"], bool):
            errors.append("Result record missing boolean 'verified' field")
        if "complete" not in record or not isinstance(record["complete"], bool):
            errors.append("Result record missing boolean 'complete' field")

        # Anti-greenwashing rules for result:
        verified = record.get("verified", True)
        complete = record.get("complete", True)
        is_preview = outcome == "preview" or record.get("applied") is False

        if not verified and outcome in POSITIVE_OUTCOMES:
            errors.append(
                f"Greenwash violation: outcome cannot be '{outcome}' when verified=False"
            )
        if not complete and not is_preview and outcome in POSITIVE_OUTCOMES:
            errors.append(
                f"Greenwash violation: outcome cannot be '{outcome}' when complete=False"
            )
        if (
            outcome in ("skipped", "partial", "cannot-run", "error", "unverified")
            and outcome in POSITIVE_OUTCOMES
        ):
            errors.append(
                f"Greenwash violation: outcome cannot be positive for '{outcome}' state"
            )

        # Exit code parity check
        if exit_code == 0:
            if outcome in ("findings", "fail", "cannot-run", "error", "unverified"):
                errors.append(
                    f"Exit code mismatch: exit=0 incompatible with negative outcome '{outcome}'"
                )
        elif exit_code == 1:
            if outcome in POSITIVE_OUTCOMES:
                errors.append(
                    f"Exit code mismatch: exit=1 incompatible with clean outcome '{outcome}'"
                )
        elif exit_code == 2:
            if outcome not in ("cannot-run", "error"):
                errors.append(
                    f"Exit code mismatch: exit=2 requires outcome 'cannot-run' or 'error', got '{outcome}'"
                )

    elif kind == "summary":
        for req in ("total", "emitted", "omitted", "complete"):
            if req not in record:
                errors.append(f"Summary record missing required field '{req}'")
        if "complete" in record and not isinstance(record["complete"], bool):
            errors.append("Summary field 'complete' must be a boolean")
        for num_field in ("total", "emitted", "omitted"):
            if num_field in record and not isinstance(record[num_field], int):
                errors.append(f"Summary field '{num_field}' must be an integer")
        if (
            isinstance(record.get("total"), int)
            and isinstance(record.get("emitted"), int)
            and isinstance(record.get("omitted"), int)
        ):
            if record["emitted"] + record["omitted"] != record["total"]:
                errors.append(
                    f"Summary counts inconsistent: emitted ({record['emitted']}) + omitted ({record['omitted']}) != total ({record['total']})"
                )

    elif kind == "error":
        outcome = record.get("outcome")
        exit_code = record.get("exit")
        if exit_code != 2:
            errors.append(f"Error record must carry exit=2, got exit={exit_code}")
        if outcome not in ("error", "cannot-run"):
            errors.append(
                f"Error record must carry outcome 'error' or 'cannot-run', got '{outcome}'"
            )
        if record.get("complete") is True:
            errors.append("Error record cannot be marked complete=True")

    # 7. Check for ANSI escapes and unsanitized home paths in all string values
    def _check_string_values(val: Any, path_prefix: str = "") -> None:
        if isinstance(val, str):
            if _ANSI_ESCAPE_RE.search(val):
                errors.append(
                    f"ANSI escape code detected in field '{path_prefix}': {val!r}"
                )
            if _HOME_PATH_RE.search(val):
                errors.append(
                    f"Unsanitized absolute home path in field '{path_prefix}': {val!r}"
                )
        elif isinstance(val, dict):
            for k, v in val.items():
                _check_string_values(v, f"{path_prefix}.{k}" if path_prefix else str(k))
        elif isinstance(val, list):
            for i, v in enumerate(val):
                _check_string_values(v, f"{path_prefix}[{i}]")

    _check_string_values(record)

    return errors


def is_valid_agent_record(record: Dict[str, Any]) -> bool:
    """Return True if the record strictly passes aw.agent/v1 validation."""
    return len(validate_agent_record(record)) == 0


def assert_valid_agent_record(record: Dict[str, Any]) -> None:
    """Raise ValueError if the record violates any aw.agent/v1 schema rule."""
    errs = validate_agent_record(record)
    if errs:
        raise ValueError(f"Invalid aw.agent/v1 record: {'; '.join(errs)}")


# --------------------------------------------------------------------------------------------------
# Rule Text Extraction & Degradation Constants (Order 01 / wqiofa)
# --------------------------------------------------------------------------------------------------

LAST_RESORT_ERROR_DIAGNOSTIC: str = "aw.agent/v1 record failed schema validation"

_REDUCER_RULES: Sequence[tuple[re.Pattern[str], str]] = (
    # 1. Unsanitized home paths and ANSI escapes in path_prefix fields
    (re.compile(r"^(Unsanitized absolute home path in field '[^']+'): .*$"), r"\1"),
    (re.compile(r"^(ANSI escape code detected in field '[^']+'): .*$"), r"\1"),
    # 2. Exit field range violation
    (re.compile(r"^(Field 'exit' must be an integer in \(0, 1, 2\)), got .*$"), r"\1"),
    # 3. Outcome field violations
    (
        re.compile(r"^Unknown outcome '[^']*'; (expected one of .*)$"),
        r"Unknown outcome; \1",
    ),
    (re.compile(r"^(Field 'outcome' must be a string), got .*$"), r"\1"),
    # 4. Schema and Kind violations
    (re.compile(r"^(Invalid schema: expected '[^']+'), got .*$"), r"\1"),
    (
        re.compile(r"^Invalid kind: '[^']*' must be one of (.*)$"),
        r"Invalid kind: must be one of \1",
    ),
    # 5. Anti-greenwash invariants
    (
        re.compile(r"^Greenwash violation: outcome cannot be '[^']*' (when .*)$"),
        r"Greenwash violation: outcome cannot be positive \1",
    ),
    (
        re.compile(
            r"^Greenwash violation: outcome cannot be positive for '[^']*' (state)$"
        ),
        r"Greenwash violation: outcome cannot be positive for incomplete \1",
    ),
    # 6. Exit code parity mismatches
    (
        re.compile(
            r"^(Exit code mismatch: exit=0 incompatible with negative outcome).*$"
        ),
        r"\1",
    ),
    (
        re.compile(r"^(Exit code mismatch: exit=1 incompatible with clean outcome).*$"),
        r"\1",
    ),
    (
        re.compile(
            r"^(Exit code mismatch: exit=2 requires outcome 'cannot-run' or 'error'), got .*$"
        ),
        r"\1",
    ),
    # 7. Summary record counts
    (
        re.compile(
            r"^Summary counts inconsistent: emitted \([^)]*\) \+ omitted \([^)]*\) != total \([^)]*\)$"
        ),
        "Summary counts inconsistent: emitted + omitted != total",
    ),
    # 8. Error record invariants
    (re.compile(r"^(Error record must carry exit=2), got exit=.*$"), r"\1"),
    (
        re.compile(
            r"^(Error record must carry outcome 'error' or 'cannot-run'), got .*$"
        ),
        r"\1",
    ),
)


def reduce_violation_to_rule_text(violation: str) -> str:
    """Reduce a validation error string to its rule text, discarding the quoted offending value."""
    for pattern, repl in _REDUCER_RULES:
        if pattern.match(violation):
            return pattern.sub(repl, violation)
    if ": '" in violation or ': "' in violation:
        prefix, _, _ = violation.partition(": ")
        if prefix:
            return redact_home_paths(_ANSI_ESCAPE_RE.sub("", prefix))
    return redact_home_paths(_ANSI_ESCAPE_RE.sub("", violation))


# --------------------------------------------------------------------------------------------------
# Field Filtering & Projection (Token Control)
# --------------------------------------------------------------------------------------------------

_MANDATORY_FIELDS = {"schema", "kind", "cmd", "exit", "outcome", "complete", "verified"}

# Fields that a projection must not remove across any record kind. This is a kind-independent
# superset of _MANDATORY_FIELDS that preserves fields required for two distinct reasons:
# 1. Record validity (fields validate_agent_record consults):
#    - 'applied': preview exemption for result records with complete=False
#    - 'total', 'emitted', 'omitted': required accounting fields for summary records
# 2. Record usability that the caller cannot reconstruct:
#    - 'next': paging continuation or recovery command. Dropping 'next' from a record reporting
#      complete=False tells the caller its answer is partial while withholding the command to
#      fetch the remainder. Furthermore, docs/cli-output-contract.md Sections 11.1 and 11.4
#      state MUST requirements for empty results and cannot-run error records to carry 'next',
#      which a projected record would otherwise violate.
#
# Preserving a flat union rather than a per-kind mapping avoids a second structure to keep
# in sync with the validator, and failing closed (retaining a field the validator might consult
# or that the caller cannot reconstruct) prevents broken continuation and runtime crashes.
# For records that do not carry these optional/kind-specific fields, filtering is a no-op
# because only present keys are considered.
_PRESERVED_FIELDS = _MANDATORY_FIELDS | {
    "applied",
    "total",
    "emitted",
    "omitted",
    "next",
}


def filter_record_fields(
    record: Dict[str, Any], fields: Optional[Sequence[str]] = None
) -> Dict[str, Any]:
    """Project record fields down to requested set while preserving whatever the record's kind requires to remain valid."""
    if not fields:
        return dict(record)

    allowed = _PRESERVED_FIELDS | set(fields)
    return {k: v for k, v in record.items() if k in allowed}


# --------------------------------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------------------------------


def render_jsonl_record(record: Dict[str, Any]) -> str:
    """Render an agent record as a single-line, compact JSONL string terminated by newline."""
    assert_valid_agent_record(record)
    return json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"


LAST_RESORT_ERROR_RECORD: Dict[str, Any] = {
    "schema": SCHEMA_VERSION,
    "kind": "error",
    "cmd": "aw",
    "exit": 2,
    "outcome": "error",
    "verified": False,
    "complete": False,
    "error": LAST_RESORT_ERROR_DIAGNOSTIC,
    "next": None,
}

LAST_RESORT_JSONL_RECORD: str = (
    json.dumps(LAST_RESORT_ERROR_RECORD, separators=(",", ":"), ensure_ascii=False)
    + "\n"
)


def build_substitute_error_record(
    errors: Sequence[str],
    cmd: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a conforming aw.agent/v1 substitute error record carrying rule-text-only violations."""
    clean_cmd = "aw"
    if isinstance(cmd, str) and cmd.strip():
        stripped = cmd.strip()
        if not _HOME_PATH_RE.search(stripped) and not _ANSI_ESCAPE_RE.search(stripped):
            clean_cmd = stripped

    reduced_rules = [reduce_violation_to_rule_text(err) for err in errors]
    if reduced_rules:
        error_msg = f"Invalid aw.agent/v1 record: {'; '.join(reduced_rules)}"
    else:
        error_msg = LAST_RESORT_ERROR_DIAGNOSTIC

    return {
        "schema": SCHEMA_VERSION,
        "kind": "error",
        "cmd": clean_cmd,
        "exit": 2,
        "outcome": "error",
        "verified": False,
        "complete": False,
        "error": error_msg,
        "next": None,
    }


def render_guarded_jsonl_record(
    record: Dict[str, Any],
    *,
    strict: Optional[bool] = None,
    guarded: Optional[bool] = None,
) -> str:
    """Render an agent record as a single-line compact JSONL string, degrading invalid records in production.

    When `strict` is True, raises `ValueError` on schema violations with the original unredacted message.
    When `strict` is False (or `guarded=True`), catches `ValueError` and returns a conforming substitute
    error record carrying rule-text-only violations.
    When neither is passed (`strict is None` and `guarded is None`), defaults to strict under pytest
    (detected via `PYTEST_CURRENT_TEST` in `os.environ`) and guarded in production.
    """
    if guarded is not None:
        if strict is not None:
            raise ValueError("Cannot specify both strict and guarded")
        strict = not guarded
    if strict is None:
        strict = "PYTEST_CURRENT_TEST" in os.environ

    try:
        return render_jsonl_record(record)
    except ValueError as exc:
        if strict:
            raise

        # Production / guarded mode: build a conforming substitute error record
        errors: List[str]
        cmd_val: Optional[str] = None
        if isinstance(record, dict):
            cmd_val = record.get("cmd")
            errors = validate_agent_record(record)
        else:
            errors = []

        if not errors:
            exc_msg = str(exc)
            prefix = "Invalid aw.agent/v1 record: "
            if exc_msg.startswith(prefix):
                errors = [
                    e.strip() for e in exc_msg[len(prefix) :].split("; ") if e.strip()
                ]
            else:
                errors = [exc_msg]

        try:
            substitute = build_substitute_error_record(errors, cmd=cmd_val)
            assert_valid_agent_record(substitute)
            return (
                json.dumps(substitute, separators=(",", ":"), ensure_ascii=False) + "\n"
            )
        except Exception:
            return LAST_RESORT_JSONL_RECORD


def degrade_validation_error_to_record(
    exc: ValueError,
    cmd: Optional[str] = None,
    *,
    strict: Optional[bool] = None,
    guarded: Optional[bool] = None,
) -> str:
    """Degrade an already-raised schema ValueError into a conforming JSONL error record."""
    if guarded is not None:
        if strict is not None:
            raise ValueError("Cannot specify both strict and guarded")
        strict = not guarded
    if strict is None:
        strict = "PYTEST_CURRENT_TEST" in os.environ

    if strict:
        raise exc

    exc_msg = str(exc)
    prefix = "Invalid aw.agent/v1 record: "
    if exc_msg.startswith(prefix):
        errors = [e.strip() for e in exc_msg[len(prefix) :].split("; ") if e.strip()]
    else:
        errors = [exc_msg]

    try:
        substitute = build_substitute_error_record(errors, cmd=cmd)
        assert_valid_agent_record(substitute)
        return json.dumps(substitute, separators=(",", ":"), ensure_ascii=False) + "\n"
    except Exception:
        return LAST_RESORT_JSONL_RECORD
