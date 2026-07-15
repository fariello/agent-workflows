"""Inter-agent comms convention: envelope + acknowledgement validators and vocabulary (D81).

This is the single, agent-agnostic source of truth for the ``.agents/comms/`` convention's
machine-checkable pieces:

- the message-envelope header vocabulary (``Kind``, the closed ack ``Status`` enum, the optional
  ``Not-Before`` scheduling gate) and a header parser/validator;
- the acknowledgement closed enum, its authorized-writer table (which party may legitimately assert
  each state), and an ack-file schema validator;
- a strict message-filename validator (traversal / control-char / oversize safety), mirroring the
  a-reference-agent session-key guards.

It is a foundation module (IPD 20260715-1033-01). It contains NO daemon, NO OpenCode server calls,
and does NOT itself write acks, deliver messages, act on ``Not-Before``, or perform discovery; those
belong to later IPDs (the payload-blind broker, the agent-side ack writer, discovery/registry). The
functions here are pure: they parse/validate in-memory values and never touch the network. Stdlib
only (zero runtime deps, D46).

See ``.agents/docs/specs/`` (the agent-comms-convention spec) and
``.agents/docs/research/20260714-2300-01-same-box-agent-wakeup-mechanisms.md`` for the design.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# --- Message kinds -----------------------------------------------------------------------------
# The semantic class of a message. Closed set.
KINDS = ("ask", "reply", "task", "handoff", "fyi")

# --- Acknowledgement state machine (closed enum; NO free text ever) ----------------------------
# An ack is metadata, never content: exactly one token from this closed set. Because it is closed,
# a token cannot smuggle instructions and cannot be an injection vector, so a payload-blind broker
# may route acks without ever reading a message payload.
#
# Authorized-writer-per-token: the BROKER writes only content-free DELIVERY observations (which only
# it knows and which carry no payload); the TARGET AGENT writes only its own read/work states (which
# only it can truthfully assert). The broker MUST NEVER forge a target state (e.g. `read`,
# `executed`); doing so is both incorrect and a breach of the payload-blind invariant.
#
# `unread` is intentionally NOT a token: it is modeled as the ABSENCE of a `read` ack after
# `delivered`, so there is a single source of truth.
BROKER_ACK_STATES = (
    "scheduled",  # Not-Before is in the future; not yet fired
    "queued",  # eligible, about to fire the nudge
    "delivered",  # nudge landed (headless message accepted, or attended toast shown)
    "agent-not-running",  # target could not be reached: no live agent
    "agent-not-responding",  # target reached but did not respond
    "expired",  # never became deliverable / cancelled
)
AGENT_ACK_STATES = (
    "read",  # target opened the inbox file
    "in-progress",  # target is working the message
    "done",  # target finished
    "not-done",  # target will not / did not complete
    "executed",  # target executed the requested work (a CLAIM, not proof)
    "not-executed",  # target declined / could not execute
)
ACK_STATES = BROKER_ACK_STATES + AGENT_ACK_STATES
ACK_STATE_SET = frozenset(ACK_STATES)

# Which party is the legitimate author of each state. Advisory metadata + an enforcement aid for the
# later broker (IPD 2) and agent-side writer (IPD 3); this module ships it as tested data.
ACK_WRITER = {state: "broker" for state in BROKER_ACK_STATES}
ACK_WRITER.update({state: "agent" for state in AGENT_ACK_STATES})

# Valid initial `Status:` values a SENDER may stamp on a new message (a fresh message is not yet
# delivered or worked). Kept minimal: an outbound message is either ready now or scheduled.
SENDER_INITIAL_STATES = frozenset({"queued", "scheduled"})

# --- Filename safety ---------------------------------------------------------------------------
# Envelope filenames flow into filesystem paths, so they are a trust boundary. Mirror the intent of
# a-reference-agent's `_is_path_unsafe` / `_is_session_key_unsafe` guards: reject parent-traversal, any
# path separator, a leading Windows drive letter, control characters, and cap the length.
MAX_FILENAME_LEN = 200
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def is_filename_safe(name: str) -> bool:
    """Return True if ``name`` is a safe single-segment message filename.

    Rejects: empty, over-length, parent-traversal (``..``), any ``/`` or ``\\`` separator, a leading
    Windows drive letter (``C:``), and any ASCII control character. This is a mandatory security
    control: a message filename must never be able to escape its inbox directory.
    """
    if not name or not isinstance(name, str):
        return False
    if len(name) > MAX_FILENAME_LEN:
        return False
    if ".." in name:
        return False
    if "/" in name or "\\" in name:
        return False
    if _CONTROL_CHARS_RE.search(name):
        return False
    # Leading Windows drive letter, e.g. "C:whatever".
    if len(name) >= 2 and name[0].isalpha() and name[1] == ":":
        return False
    return True


# --- Not-Before parsing ------------------------------------------------------------------------


def parse_not_before(value: str) -> Optional[datetime]:
    """Parse a ``Not-Before`` header value (ISO-8601) into a datetime, or None if unparseable.

    Accepts values that ``datetime.fromisoformat`` understands (including a trailing ``Z``, which is
    normalized to ``+00:00``). This module only PARSES/validates the value; acting on it (gating
    delivery until wall-clock reaches it) is the broker's job (IPD 2).
    """
    if not value or not isinstance(value, str):
        return None
    raw = value.strip()
    if raw.endswith("Z") or raw.endswith("z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


# --- Envelope header parsing/validation --------------------------------------------------------
_HEADER_SEP = "---"
_HEADER_LINE_RE = re.compile(r"^(?P<key>[A-Za-z][A-Za-z-]*):\s*(?P<val>.*)$")

# Recognized header keys. The payload body (after the `---` separator) is NEVER parsed here; a
# payload-blind broker reads only these header keys.
HEADER_KEYS = ("From", "To", "Kind", "Re", "Status", "Not-Before")
REQUIRED_HEADER_KEYS = ("From", "To", "Kind", "Status")


def parse_envelope_header(text: str) -> Dict[str, str]:
    """Parse the header block of a message file (everything BEFORE the first ``---`` line).

    Returns a dict of the header keys found. The payload body is deliberately ignored: this reads
    only routing/scheduling metadata, upholding the payload-blind invariant. Unknown header lines
    are ignored (kept lenient); malformed lines are skipped.
    """
    header: Dict[str, str] = {}
    for line in text.splitlines():
        if line.strip() == _HEADER_SEP:
            break
        m = _HEADER_LINE_RE.match(line)
        if not m:
            continue
        header[m.group("key")] = m.group("val").strip()
    return header


def validate_envelope_header(header: Dict[str, str]) -> List[str]:
    """Return a list of human-readable problems with an envelope header; empty means valid.

    Checks: required keys present and non-empty; ``Kind`` in the closed set; ``Status`` is a
    recognized ack state (sender initial state expected but any closed-enum value is accepted so the
    same validator serves in-flight messages); ``Not-Before`` (if present) parses as ISO-8601.
    Does NOT inspect the payload body.
    """
    problems: List[str] = []
    for key in REQUIRED_HEADER_KEYS:
        if not header.get(key, "").strip():
            problems.append(f"missing required header: {key}")

    kind = header.get("Kind", "").strip()
    if kind and kind not in KINDS:
        problems.append(f"Kind {kind!r} not in {KINDS}")

    status = header.get("Status", "").strip()
    if status and status not in ACK_STATE_SET:
        problems.append(f"Status {status!r} is not a recognized ack state")

    nb = header.get("Not-Before", "").strip()
    if nb and parse_not_before(nb) is None:
        problems.append(f"Not-Before {nb!r} is not a valid ISO-8601 datetime")

    return problems


def is_envelope_header_valid(header: Dict[str, str]) -> bool:
    """Convenience boolean form of :func:`validate_envelope_header`."""
    return not validate_envelope_header(header)


# --- Acknowledgement file schema ---------------------------------------------------------------
ACK_REQUIRED_FIELDS = ("re", "state", "by", "at")


def validate_ack(obj: Any) -> List[str]:
    """Return a list of problems with an ack-file object; empty means valid.

    An ack file is ``{"re": <msg-id>, "state": <closed-enum>, "by": <proj.agent>, "at": <ISO-8601>}``.
    The ``state`` MUST be one of the closed enum (this is what keeps acks from ever carrying free
    text / payload). ``at`` must parse as ISO-8601. This validator does NOT enforce authorized-writer
    (that needs the caller's identity, which the broker/agent supply in IPDs 2/3); use
    :func:`ack_writer_for` to look up the legitimate author.
    """
    problems: List[str] = []
    if not isinstance(obj, dict):
        return ["ack must be a JSON object"]
    for field in ACK_REQUIRED_FIELDS:
        if field not in obj or obj[field] in (None, ""):
            problems.append(f"ack missing required field: {field}")
    state = obj.get("state")
    if state is not None and state not in ACK_STATE_SET:
        problems.append(f"ack state {state!r} is not in the closed enum")
    at = obj.get("at")
    if isinstance(at, str) and at.strip() and parse_not_before(at) is None:
        problems.append(f"ack 'at' {at!r} is not a valid ISO-8601 datetime")
    return problems


def is_ack_valid(obj: Any) -> bool:
    """Convenience boolean form of :func:`validate_ack`."""
    return not validate_ack(obj)


def ack_writer_for(state: str) -> Optional[str]:
    """Return the legitimate author of an ack state (``"broker"`` or ``"agent"``), or None if the
    state is not a recognized ack state."""
    return ACK_WRITER.get(state)


def ack_filename(msg_id: str, from_agent: str, state: str) -> str:
    """Build the conventional ack filename ``<msg-id>.<from-agent>.<state>.json``.

    Purely a name builder (no I/O). The caller is responsible for validating ``state`` against the
    closed enum first (via :func:`validate_ack`) and for placing the file under
    ``.agents/comms/local/acks/``.
    """
    return f"{msg_id}.{from_agent}.{state}.json"
