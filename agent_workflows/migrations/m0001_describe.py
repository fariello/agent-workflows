"""Short-description normalization and safety validation for migration m0001.

Implements spec 4sd62s Section 4.2 SAFEGUARDS and OQ-31 (validation half) so the
m0001 describe runner can validate generated ``short_description`` candidates
with the same descriptive-value, leak-sanitizer, and absolute-path refusals that
``artifact_meta`` enforces at write time.
"""

from __future__ import annotations

import re
from pathlib import Path

from agent_workflows import artifact_meta, attention_contract, leak_sanitizer

_VALIDATION_VERB = "aw migrate metadata"
_FIELD_NAME = "short_description"

_LEADING_PUNCT = "`\"'([{<"
_TRAILING_PUNCT = "`\"'.,;:!?)]}>"
_WINDOWS_DRIVE_RE = re.compile(r"\b[A-Za-z]:[/\\]")


def normalize_description(text: str) -> str:
    """Strip surrounding whitespace and at most one matching pair of outer quotes."""
    cleaned = text.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ('"', "'"):
        return cleaned[1:-1]
    return cleaned


def build_describe_ruleset(repo: Path) -> leak_sanitizer.Ruleset:
    """Build the writer leak-sanitizer ruleset once for a describe run."""
    return artifact_meta._writer_ruleset(Path(repo))


def _check_no_absolute_paths(text: str) -> str | None:
    """Refuse absolute POSIX (>=2 segments, excluding '//') or Windows drive tokens."""
    for token in text.split():
        stripped = token.lstrip(_LEADING_PUNCT).rstrip(_TRAILING_PUNCT)
        if not stripped:
            continue
        raw_parts = (
            (stripped, stripped.split("=", 1)[1]) if "=" in stripped else (stripped,)
        )
        for raw_part in raw_parts:
            cand = raw_part.lstrip(_LEADING_PUNCT).rstrip(_TRAILING_PUNCT)
            if not cand:
                continue
            if _WINDOWS_DRIVE_RE.search(cand):
                return (
                    f"{_VALIDATION_VERB}: {_FIELD_NAME} must not contain "
                    f"absolute Windows drive path: {token!r}"
                )
            if (
                cand.startswith("/")
                and not cand.startswith("//")
                and cand.count("/") >= 2
            ):
                return (
                    f"{_VALIDATION_VERB}: {_FIELD_NAME} must not contain "
                    f"absolute multi-segment path: {token!r}"
                )
    return None


def validate(
    text: str,
    repo: Path,
    *,
    ruleset: leak_sanitizer.Ruleset | None = None,
) -> str | None:
    """Validate a candidate ``short_description`` after quote/whitespace normalization.

    Returns ``None`` when ``text`` passes all checks, or the first refusal reason string:
    empty/blank text, descriptive-value safety (>300 chars, newlines, control chars),
    leak-sanitizer ``fail`` or ``warn`` findings, or absolute-path tokens.
    """
    cleaned = normalize_description(text)
    if not cleaned or not cleaned.strip():
        return f"{_VALIDATION_VERB}: {_FIELD_NAME} must not be empty"

    refusal = attention_contract.refuse_unsafe_descriptive(
        _VALIDATION_VERB, _FIELD_NAME, cleaned
    )
    if refusal is not None:
        return refusal

    active_ruleset = ruleset if ruleset is not None else build_describe_ruleset(repo)
    findings = leak_sanitizer.scan_text(
        cleaned, _FIELD_NAME, active_ruleset, include_warn=True
    )
    if findings:
        first = findings[0]
        return (
            f"{_VALIDATION_VERB}: {_FIELD_NAME} refused by leak sanitizer "
            f"({first.rule})"
        )

    return _check_no_absolute_paths(cleaned)
