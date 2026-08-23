"""Normative schema, validation, and serialization for the aw.agent/v1 protocol.

awcliux Order 03 (`8su0r3`) E-01 / E-02 / E-03.

Defines the closed record kinds, mandatory envelope fields, exit code classification,
anti-greenwashing outcome invariants, repo-relative path sanitization, and token-control
filtering for the machine convention. Stdlib only (Python 3.9+).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

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
_HOME_PATH_RE = re.compile(
    r"(?:/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+|/Users/(?!<|user/)[A-Za-z0-9._-]+|[A-Za-z]:[\\/]+Users[\\/]+(?!<)[A-Za-z0-9._-]+)"
)


# --------------------------------------------------------------------------------------------------
# Path and Evidence Sanitization
# --------------------------------------------------------------------------------------------------


def normalize_repo_path(
    path: Union[str, Path], repo_root: Optional[Union[str, Path]] = None
) -> str:
    """Normalize a filesystem path to be repo-relative, forward-slashed, and sanitizer-clean.

    Never returns absolute paths, home directories, usernames, or hostnames.
    """
    if not path:
        return ""

    path_str = str(path).replace("\\", "/")

    # If repo_root is provided, make path relative to repo_root
    if repo_root is not None:
        try:
            root_resolved = Path(repo_root).resolve()
            p_resolved = Path(path_str).resolve()
            rel = p_resolved.relative_to(root_resolved)
            return str(rel).replace("\\", "/")
        except (ValueError, Exception):
            pass

    # If the path looks absolute or starts with /home or /Users, strip down to relative tail
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
# Field Filtering & Projection (Token Control)
# --------------------------------------------------------------------------------------------------

_MANDATORY_FIELDS = {"schema", "kind", "cmd", "exit", "outcome", "complete", "verified"}


def filter_record_fields(
    record: Dict[str, Any], fields: Optional[Sequence[str]] = None
) -> Dict[str, Any]:
    """Project record fields down to requested set while preserving mandatory envelope fields."""
    if not fields:
        return dict(record)

    allowed = _MANDATORY_FIELDS | set(fields)
    return {k: v for k, v in record.items() if k in allowed}


# --------------------------------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------------------------------


def render_jsonl_record(record: Dict[str, Any]) -> str:
    """Render an agent record as a single-line, compact JSONL string terminated by newline."""
    assert_valid_agent_record(record)
    return json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
