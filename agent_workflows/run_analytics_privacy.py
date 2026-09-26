#!/usr/bin/env python3
"""THE ONE privacy boundary every analytics fact crosses before it is persisted.

WHY THIS MODULE EXISTS, AND WHY IT IS AN ALLOWLIST. The analytics cache summarizes driver run
records that demonstrably contain private data: every ``state.json`` in this repository's own run
corpus carries an ABSOLUTE maintainer home path in both its ``repo`` and its ``driver.path``
fields, and the corpus also holds prompt and session transcripts. So the FIRST field an ingester
reads is already a forbidden value, and a filter built by enumerating known-bad keys would pass
every test written from that same enumeration and then leak on the first field nobody imagined.
An enumerated forbidden set can never be proven complete; an allowlist can. :func:`project_facts`
therefore passes ONLY explicitly named keys of explicitly named types and REFUSES everything
else, naming the offending key. The forbidden-value list in this package's plans is a TEST CORPUS
for the read-side check, never the implementation strategy.

TWO SIDES, DELIBERATELY DIFFERENT CODE. This module is the WRITE-side guarantee. The independent
READ-side proof is :mod:`agent_workflows.leak_sanitizer` (re-exported as ``local_leaks``, driven
by ``aw sanitize --agent``), which already detects home paths, handles, hostnames, private remotes
and secret-shaped strings. That engine is the verification oracle and is NOT reimplemented here:
it is deliberately one engine behind a thin re-export so there is ONE detection code path, and a
second sanitizer in ``run_analytics_*`` would be exactly the drift that rule forbids. A projector
that refused nothing and a detector that was not looking are indistinguishable, so the tests pair
every clean scan with a CONTROL scan proving the same invocation flags the same canary raw.

THE HASHING CONTRACT, STATED CONCRETELY BECAUSE AN UNSPECIFIED SALT IS A SHARED SALT.
Identifiers that must be correlatable across entries but must not be reversible (a source-root
path, a hostname, an absolute path) are replaced by :func:`pseudonymize`, which is
``sha256(salt || domain || value)`` truncated to 16 hex characters and prefixed with its domain.

* WHERE THE SALT LIVES: in ``salt`` beside the cache, inside the reserved analytics subtree
  (``<resolved-runs-root>/analytics/cache/salt``). That tree is gitignored by construction
  (``.aw/.gitignore`` carries ``records/runs/``), so the salt cannot reach git history. It is
  created 0600 on first use with :func:`secrets.token_hex`.
* WHY NOT ``.aw/config/local.json``: that is a user-facing configuration surface whose keys the
  setup wizard manages, and a cryptographic salt is not a setting a human should see or edit.
* IT IS NEVER COMMITTED and is per-box. It is not shared, published, or exported.
* CORRELATION SCOPE is therefore ONE BOX AND ONE CACHE GENERATION. The cache is disposable, so
  losing the salt with the cache is CORRECT: a rebuilt cache SHOULD mint fresh identifiers,
  because a durable salt outliving the data it pseudonymizes is precisely what enables
  cross-submission correlation without consent. Rotating the salt invalidates correlation BY
  DESIGN. Any wider scope is an explicit, opt-in decision belonging to the sanitized-export
  surface, never a default here.

WHAT A PASSING IMPLEMENTATION MAY NOT CLAIM. The output of this module is MINIMIZED and REDACTED.
It is NOT anonymous and NOT cleared for public release. Residual re-identification risk remains:
timestamps, durations and cost magnitudes are retained deliberately (they are the analytics
payload) and a sufficiently determined observer with side knowledge can correlate them. A
downstream consumer must not read "cache-projected" as "safe to publish"; export and submission
carry their own explicit human-controlled gate.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from pathlib import Path
from typing import Any, Iterable, Mapping

__all__ = [
    "PrivacyRefusal",
    "ALLOWED_METRIC_KEYS",
    "ALLOWED_EVENT_KEYS",
    "ALLOWED_SCALAR_TYPES",
    "PSEUDONYM_DOMAINS",
    "SALT_FILENAME",
    "salt_path",
    "load_or_create_salt",
    "pseudonymize",
    "project_facts",
    "project_metric_facts",
    "project_event_facts",
    "redact_text",
]


class PrivacyRefusal(ValueError):
    """A fact carried a key or a value type the allowlist does not name, so it was REFUSED.

    Deliberately a refusal rather than a silent drop. A projector that dropped an unknown key
    would let a caller believe its fact was persisted whole, and the difference between "refused"
    and "dropped" is the difference between a boundary a test can prove and one it cannot.
    """

    def __init__(self, key: str, reason: str) -> None:
        self.key = key
        self.reason = reason
        super().__init__(f"privacy refusal: key {key!r} {reason}")


# --- The allowlist -----------------------------------------------------------------------------
# EVERY name here is a metric or an identifier that carries no content, no path, no host identity
# and no free text. Adding a key is a deliberate act: it widens the boundary, so it belongs with a
# test that proves the new key cannot carry a transcript, a path or a command line.

#: Numeric, boolean, enumerated and pseudonymized facts a cache entry may retain.
ALLOWED_METRIC_KEYS: frozenset[str] = frozenset(
    {
        # --- identity (opaque or repo-internal, never a path and never a host) ---
        "run_id",
        "source_root_id",
        "set_id",
        "ipd_id6",
        "position",
        "attempt",
        "node_id",
        # --- time (raw observations, unsummarized: the analytics payload) ---
        "created_at",
        "updated_at",
        "started_at",
        "ended_at",
        "duration_seconds",
        "wall_seconds",
        "observed_activity_seconds",
        "unattributed_seconds",
        "overlap_seconds",
        # --- token components: an OPEN map lives under `tokens`, see _project_number_map ---
        "tokens",
        "token_total",
        # --- money ---
        "cost",
        "cost_currency",
        "price_source",
        "price_source_version",
        "price_effective_from",
        "price_effective_to",
        "cost_is_estimate",
        # --- resource samples ---
        "cpu_seconds",
        "max_rss_bytes",
        "load_average",
        "sample_count",
        # --- categorical labels (closed vocabularies, never free text) ---
        "phase",
        "activity",
        "driver",
        "driver_generation",
        "host_kind",
        "model",
        "provider",
        "model_variant",
        "outcome",
        "disposition",
        "status",
        # --- counts and quality markers ---
        "event_count",
        "step_count",
        "turn_count",
        "parse_error_count",
        "missing_field_count",
        "is_complete",
        "is_terminal",
        "quality_flags",
        "warnings",
    }
)

#: Keys a per-event fact record may retain. Deliberately narrower than the metric set: an event
#: payload is arbitrary by construction, so only its shape is kept and never its content.
ALLOWED_EVENT_KEYS: frozenset[str] = frozenset(
    {
        "event_type",
        "timestamp",
        "sequence",
        "phase",
        "activity",
        "duration_seconds",
        "tokens",
        "token_total",
        "cost",
        "outcome",
        "payload_byte_count",
        "payload_field_count",
        "quality_flags",
    }
)

#: Scalar types a projected value may be. Note ``str`` is allowed only for keys whose vocabulary
#: is closed or whose value this module produced (a pseudonym, an ISO timestamp, an enum label);
#: :func:`_project_scalar` enforces that per key rather than trusting the type alone.
ALLOWED_SCALAR_TYPES: tuple[type, ...] = (bool, int, float, str, type(None))

#: Keys whose string value is FREE-FORM ENOUGH to need shape checking rather than bare typing.
#: Each is constrained to a conservative character class so a transcript, a path or a command line
#: cannot ride in through a field whose name sounds harmless.
_CLOSED_VOCABULARY_KEYS: frozenset[str] = frozenset(
    {
        "phase",
        "activity",
        "driver",
        "driver_generation",
        "host_kind",
        "model",
        "provider",
        "model_variant",
        "outcome",
        "disposition",
        "status",
        "event_type",
        "cost_currency",
        "price_source",
        "price_source_version",
        "set_id",
        "ipd_id6",
        "node_id",
        "run_id",
    }
)

#: A label may contain letters, digits and the few separators the package's own vocabularies use.
#: It may NOT contain a path separator, a space, a quote or a shell metacharacter, which is what
#: keeps a command line or an absolute path out of a categorical field.
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+@/-]{0,127}$")
#: ``model`` values legitimately carry ``/`` (``provider/model``), so the separator is permitted
#: above; an absolute path is still refused because a leading ``/`` fails the first character
#: class and ``..`` fails the label check via :func:`_looks_like_path`.
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$"
)
_PSEUDONYM_RE = re.compile(r"^[a-z][a-z0-9-]{0,15}:[0-9a-f]{16}$")
#: A run id as the drivers mint it: ``run-<UTC stamp>-<pid>``.
_RUN_ID_RE = re.compile(r"^run-\d{8}T\d{6}Z-\d+$")

#: Keys whose value MUST already be a pseudonym produced by :func:`pseudonymize`. A raw value here
#: is a refusal, not a value to be hashed on the fly: hashing at the boundary would hide from the
#: caller that it handed over something identifying.
_PSEUDONYM_REQUIRED_KEYS: frozenset[str] = frozenset({"source_root_id"})

#: Keys holding an OPEN map of numeric components. The map's KEYS are provider-chosen, so they are
#: shape-checked as labels rather than allowlisted by name: measured, the token vocabulary in this
#: repo's corpus is ``input``/``output``/``cache``/``total`` plus an occasional ``reasoning``, and a
#: closed set would silently drop the next provider's component key.
_OPEN_NUMBER_MAP_KEYS: frozenset[str] = frozenset({"tokens", "load_average"})

#: Keys holding a list of short closed-vocabulary labels.
_LABEL_LIST_KEYS: frozenset[str] = frozenset({"quality_flags", "warnings"})

#: Pseudonym domains this module mints. The domain is part of the hashed input, so the same raw
#: value in two domains yields two unrelated pseudonyms and a cross-domain join is impossible.
PSEUDONYM_DOMAINS: frozenset[str] = frozenset(
    {"root", "host", "path", "user", "branch", "remote"}
)

SALT_FILENAME = "salt"
_SALT_BYTES = 32


# --- Salt --------------------------------------------------------------------------------------
def salt_path(cache_dir: Path | str) -> Path:
    """The salt file beside the cache. See the module docstring for why it lives HERE."""

    return Path(cache_dir) / SALT_FILENAME


def load_or_create_salt(cache_dir: Path | str) -> str:
    """Read the per-box salt, minting it 0600 on first use.

    Idempotent and concurrency-tolerant: two analyzers racing to create it both end up reading
    one value, because the create path writes to a unique temp name and falls back to re-reading
    when the rename loses the race.
    """

    target = salt_path(cache_dir)
    try:
        existing = target.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, NotADirectoryError):
        existing = ""
    except OSError:
        existing = ""
    if existing:
        return existing

    target.parent.mkdir(parents=True, exist_ok=True)
    minted = secrets.token_hex(_SALT_BYTES)
    tmp = target.parent / f".{SALT_FILENAME}.{os.getpid()}.tmp"
    # Owner-only on EVERY OS (a protected current-user-only DACL on Windows, where 0o600 is
    # ignored). A leftover tmp from a crashed writer with this pid is removed first, because the
    # private create is exclusive.
    from agent_workflows import private_file

    try:
        tmp.unlink()
    except OSError:
        pass
    try:
        private_file.create_private_file(tmp, (minted + "\n").encode("utf-8"))
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    # O_EXCL-style publication: never clobber a salt another process just published, because
    # replacing it would silently invalidate every pseudonym already in the cache.
    try:
        os.link(str(tmp), str(target))
    except FileExistsError:
        pass
    except OSError:
        # A filesystem without hard links: fall back to a plain rename, accepting the small race.
        try:
            os.replace(str(tmp), str(target))
        except OSError:
            pass
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    try:
        return target.read_text(encoding="utf-8").strip() or minted
    except OSError:
        return minted


def pseudonymize(value: str, *, salt: str, domain: str = "path") -> str:
    """``<domain>:<16 hex>`` derived from ``sha256(salt || domain || value)``.

    Not reversible without the salt, and not correlatable across boxes or across cache
    generations, because the salt is per-box and dies with the cache. The domain participates in
    the digest, so the same raw string in two domains yields two unrelated pseudonyms.
    """

    if domain not in PSEUDONYM_DOMAINS:
        raise PrivacyRefusal(
            domain, f"is not a known pseudonym domain {sorted(PSEUDONYM_DOMAINS)}"
        )
    if not salt:
        raise PrivacyRefusal(domain, "cannot be pseudonymized without a salt")
    digest = hashlib.sha256(
        salt.encode("utf-8")
        + b"\x00"
        + domain.encode("utf-8")
        + b"\x00"
        + str(value).encode("utf-8")
    ).hexdigest()
    return f"{domain}:{digest[:16]}"


# --- Value-level projection --------------------------------------------------------------------
def _looks_like_path(text: str) -> bool:
    """Conservative structural test for a filesystem path, used to refuse one in a label field."""

    if text.startswith(("/", "~", "\\\\")) or ".." in text:
        return True
    if re.match(r"^[A-Za-z]:[\\/]", text):
        return True
    return False


def _project_scalar(key: str, value: Any) -> Any:
    """Pass one allowlisted scalar or REFUSE it. The type check alone is not the boundary."""

    if value is None or isinstance(value, bool) or isinstance(value, (int, float)):
        if isinstance(value, float) and (
            value != value or value in (float("inf"), float("-inf"))
        ):
            raise PrivacyRefusal(
                key, "is a non-finite number, which no metric fact may be"
            )
        return value
    if not isinstance(value, str):
        raise PrivacyRefusal(
            key, f"has type {type(value).__name__}, which the allowlist does not permit"
        )

    text = value
    if key in _PSEUDONYM_REQUIRED_KEYS:
        if not _PSEUDONYM_RE.match(text):
            raise PrivacyRefusal(
                key,
                "must already be a pseudonym from pseudonymize(); a raw value is refused",
            )
        return text
    if key.endswith("_at") or key in {
        "timestamp",
        "price_effective_from",
        "price_effective_to",
    }:
        if not _TIMESTAMP_RE.match(text):
            raise PrivacyRefusal(key, "must be an ISO-8601 timestamp")
        return text
    if key == "run_id":
        if not _RUN_ID_RE.match(text) and not _PSEUDONYM_RE.match(text):
            raise PrivacyRefusal(key, "must be a driver run id or a pseudonym")
        return text
    if key in _CLOSED_VOCABULARY_KEYS:
        if _PSEUDONYM_RE.match(text):
            return text
        if _looks_like_path(text):
            raise PrivacyRefusal(
                key, "looks like a filesystem path, which no label may carry"
            )
        if not _LABEL_RE.match(text):
            raise PrivacyRefusal(
                key,
                "is not a short closed-vocabulary label (no spaces, quotes or free text)",
            )
        return text
    if _PSEUDONYM_RE.match(text):
        return text
    raise PrivacyRefusal(key, "is a string on a key whose values are not free text")


def _project_number_map(key: str, value: Any) -> dict[str, float | int]:
    """Pass an OPEN map of numeric components, shape-checking its provider-chosen keys."""

    if not isinstance(value, Mapping):
        raise PrivacyRefusal(
            key,
            f"must be a mapping of component name to number, got {type(value).__name__}",
        )
    projected: dict[str, float | int] = {}
    for raw_name, raw_number in value.items():
        name = str(raw_name)
        if not _LABEL_RE.match(name) or _looks_like_path(name):
            raise PrivacyRefusal(f"{key}.{name}", "is not a short component label")
        if isinstance(raw_number, bool) or not isinstance(raw_number, (int, float)):
            raise PrivacyRefusal(f"{key}.{name}", "must be a number")
        if isinstance(raw_number, float) and (
            raw_number != raw_number or raw_number in (float("inf"), float("-inf"))
        ):
            raise PrivacyRefusal(f"{key}.{name}", "must be a finite number")
        projected[name] = raw_number
    return projected


def _project_label_list(key: str, value: Any) -> list[str]:
    """Pass a list of short closed-vocabulary labels, refusing free text (warnings included).

    ``warnings`` is the field most likely to smuggle content, because a naive implementation
    formats an exception message into it and an exception message routinely contains a path.
    """

    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise PrivacyRefusal(key, "must be a list of short labels")
    projected: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            raise PrivacyRefusal(
                key, f"contains a {type(entry).__name__}; only short labels are allowed"
            )
        if _looks_like_path(entry):
            raise PrivacyRefusal(key, "contains a filesystem path")
        if not _LABEL_RE.match(entry):
            raise PrivacyRefusal(
                key,
                f"contains {entry[:24]!r}, which is not a short label (free text is refused)",
            )
        projected.append(entry)
    return projected


def project_facts(
    facts: Mapping[str, Any],
    *,
    allowed: frozenset[str],
    where: str = "fact",
) -> dict[str, Any]:
    """THE single projection function. Pass allowlisted keys; REFUSE every other key.

    ``where`` names the record kind in a refusal so a caller can tell a metric fact from an event
    fact without a traceback. Key order is normalized (sorted) so the encoded form is byte-stable
    and independent of the producer's dict ordering.
    """

    if not isinstance(facts, Mapping):
        raise PrivacyRefusal(where, f"must be a mapping, got {type(facts).__name__}")
    projected: dict[str, Any] = {}
    for raw_key in sorted(facts.keys(), key=str):
        key = str(raw_key)
        if key not in allowed:
            raise PrivacyRefusal(
                key,
                f"is not in the {where} allowlist, so it is refused rather than dropped "
                f"(the boundary is an allowlist: add the key deliberately with a test)",
            )
        value = facts[raw_key]
        if key in _OPEN_NUMBER_MAP_KEYS:
            projected[key] = _project_number_map(key, value)
        elif key in _LABEL_LIST_KEYS:
            projected[key] = _project_label_list(key, value)
        else:
            projected[key] = _project_scalar(key, value)
    return projected


def project_metric_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Project one per-run metric fact record."""

    return project_facts(facts, allowed=ALLOWED_METRIC_KEYS, where="metric")


def project_event_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Project one per-event fact record: shape only, never payload content."""

    return project_facts(facts, allowed=ALLOWED_EVENT_KEYS, where="event")


def redact_text(text: str, *, salt: str) -> str:
    """Replace identifying substrings in a DIAGNOSTIC string with pseudonyms.

    Diagnostics are the second-most likely leak after facts, because the natural way to report a
    failure is to interpolate the offending path. This is NOT a substitute for the allowlist and
    is never applied to a fact: it exists so a message the cache records about ITSELF is safe.
    Only structural forms are rewritten (absolute POSIX/Windows home paths and ``~`` paths); a
    string that survives is still subject to the allowlist wherever it would be persisted.
    """

    if not text:
        return text

    def _replace(match: "re.Match[str]") -> str:
        return pseudonymize(match.group(0), salt=salt, domain="path")

    redacted = re.sub(r"/(?:home|Users)/[^\s:,;'\")\]}]+", _replace, text)
    redacted = re.sub(r"[A-Za-z]:[\\/]+Users[\\/]+[^\s:,;'\")\]}]+", _replace, redacted)
    redacted = re.sub(r"~/[^\s:,;'\")\]}]+", _replace, redacted)
    return redacted
