"""Verifier test evidence corroboration.

Compares claimed test commands from verifier outcomes against observed tool calls
extracted from the verifier turn's session log (OpenCode or Antigravity), returning
a three-state fail-open corroboration verdict: `corroborated`, `uncorroborated`,
or `indeterminate`.

DESIGN CONSTRAINTS AND SCOPE BOUNDARIES:
- Pure stdlib-only reader: never imports runner_shared, run_dashboard, or either
  host runner. Never raises exceptions on malformed, missing, truncated, or hostile inputs.
- Fail-open asymmetry: every unknown, missing, unreadable, delegated, or unresolved
  case resolves to `indeterminate`, never to `uncorroborated`. An `uncorroborated`
  verdict is reserved strictly for a fully observed, non-delegated turn where shell
  commands were observed, all observed commands resolved, and no claimed command matched.
- No refusal or downgrade: this module is a measurement and predicate only.

DECISION: OBSERVATIONAL VERDICT, REFUSAL FORBIDDEN:
========================================================================================
The verdict computed by this module and recorded by `runner_shared.execute_item_core`
is strictly observational. An `uncorroborated` verdict MUST NOT refuse, downgrade, or
alter any item disposition, verification status, or integration decision (such as
`runner_shared.integration_is_earned`). This policy is forced by three measured facts:
(1) GUIDING_PRINCIPLES.md P15 forbids "any mechanism whose justification is 'in case
    the agent lies'", and the maintainer rulings of 2026-09-08 and 2026-09-20 reject
    gates keyed on suspected deception; reason 3 of the four recorded reasons in
    `runner_shared`'s pre-work-suite-baseline block applies to this module verbatim:
    an agent attempting to fabricate would have write access to this file.
(2) Spec `25kzda` Section 5.1's HONEST LIMIT paragraph permits only comparisons that
    make an outcome MORE permissive and explicitly forbids using an observation to
    disbelieve the agent; a corroboration refusal is the forbidden sign.
(3) The extraction predicate has known false positives that make it unsafe to strand a
    lane on: specifically, the Antigravity `step_type == "subagent"` delegation shape
    is unobserved by the reader, causing genuine test delegations to resolve to
    `uncorroborated` (tracked as bug `iuhx9d`).
IMPERATIVE: A future consumer may read this verdict and may make an outcome MORE
permissive on it, but MUST NOT refuse, downgrade, or change a disposition on it. A
reader who believes a refusal is warranted opens a new decision rather than wiring
one here.
========================================================================================

CLOSED-SET VERDICT CONDITIONS:
========================================================================================
The turn-level corroboration verdict is partitioned into a closed set of conditions:

1. `corroborated` (reason_code: "corroborated"):
   At least one claimed command matched an observed non-errored shell command.

2. `indeterminate` (six distinct reason codes for all unknown/incomplete conditions):
   (a) "log-unreadable": The session log path is nonexistent, a directory, binary,
       or cannot be read due to filesystem/OS permissions.
   (b) "log-empty": The session log exists but contains zero valid JSON event lines.
   (c) "claims-empty": The list of claimed test commands is empty.
   (d) "delegation-present": The turn delegated work to a subagent (`task` on OpenCode
       or `browser_subagent` on Antigravity). Subagent tool calls do not appear in the
       parent session log, making commands unobservable.
   (e) "missing-command-text": Shell calls were executed, but every shell call lacked
       command text (or no shell command text was observable).
   (f) "indirection-unresolved": An observed command is an unresolved indirection
       (e.g. `make <target>` where the target is not in the declared known test indirection
       allowlist). The module refuses to guess whether the target runs tests, failing open.

3. `uncorroborated` (reason_code: "uncorroborated"):
   The session log was read successfully, at least one shell command was observed,
   no subagent delegation occurred, every observed command was checked without finding
   an unresolved indirection, and NO claimed command matched any observed command.
========================================================================================
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NamedTuple

__all__ = [
    "CORROBORATED",
    "INDETERMINATE_CLAIMS_EMPTY",
    "INDETERMINATE_DELEGATION",
    "INDETERMINATE_INDIRECTION_UNRESOLVED",
    "INDETERMINATE_LOG_EMPTY",
    "INDETERMINATE_LOG_UNREADABLE",
    "INDETERMINATE_MISSING_COMMAND_TEXT",
    "KNOWN_TEST_INDIRECTIONS",
    "TEST_RUNNER_PREFIXES",
    "UNCORROBORATED",
    "VERIFY_COMMAND_PREFIXES",
    "ClaimMatch",
    "CorroborationVerdict",
    "MatchResult",
    "ObservedCommand",
    "SessionReadResult",
    "ToolCall",
    "check_verifier_corroboration",
    "compute_verifier_corroboration",
    "corroborate_verifier_turn",
    "extract_session_commands",
    "match_claims_to_observed",
    "match_single_claim",
    "normalize_command",
    "session_event_host",
    "split_command_segments",
    "tool_call_from_event",
]

# --- Verdict and Reason Code Constants ------------------------------------------------

CORROBORATED: str = "corroborated"
UNCORROBORATED: str = "uncorroborated"
INDETERMINATE: str = "indeterminate"

INDETERMINATE_LOG_UNREADABLE: str = "log-unreadable"
INDETERMINATE_LOG_EMPTY: str = "log-empty"
INDETERMINATE_CLAIMS_EMPTY: str = "claims-empty"
INDETERMINATE_DELEGATION: str = "delegation-present"
INDETERMINATE_MISSING_COMMAND_TEXT: str = "missing-command-text"
INDETERMINATE_INDIRECTION_UNRESOLVED: str = "indirection-unresolved"

# --- Indirection and Prefix Declarations ---------------------------------------------

# KNOWN-INCOMPLETE ALLOWLIST:
# Observed commands known to run a test suite without naming test runners directly.
# At minimum `make test` and `make test-all`, whose bodies in Makefile run `python3 -m pytest tests/`.
# Parsing the Makefile is explicitly prohibited to avoid coupling a log reader to build-file syntax.
# Any other indirection command (e.g. `make check`, `make suite`) is handled by the
# `indirection-unresolved` indeterminate condition to ensure fail-open safety.
KNOWN_TEST_INDIRECTIONS: frozenset[str] = frozenset(
    {
        "make test",
        "make test-all",
    }
)

# Recognized test-runner command prefixes for matching against known indirections.
# When an observed command matches KNOWN_TEST_INDIRECTIONS, it corroborates any claim
# whose first token is in this set.
TEST_RUNNER_PREFIXES: frozenset[str] = frozenset(
    {
        "python",
        "python3",
        "pytest",
        "unittest",
        "make",
        "cargo",
        "npm",
        "node",
        "uv",
        "tox",
        "sh",
        "bash",
        "./",
        "bin/",
    }
)

# Accepted verification command prefixes (stdlib-only copy matching runner_shared convention).
VERIFY_COMMAND_PREFIXES: tuple[str, ...] = (
    "python",
    "python3",
    "pytest",
    "make",
    "git",
    "aw",
    "sh",
    "bash",
    "cargo",
    "npm",
    "node",
    "uv",
    "tox",
    "./",
    "bin/",
)

# Known subagent tool names whose invocations make child tool calls unobservable.
SUBAGENT_TOOLS: frozenset[str] = frozenset(
    {
        "task",  # OpenCode
        "browser_subagent",  # Antigravity
        "subagent",
        "invoke_subagent",
    }
)


# --- Data Structures ------------------------------------------------------------------


class ToolCall(NamedTuple):
    """Normalized record of a single tool call from a session log."""

    tool: str
    host: str
    command: str | None
    path: str | None
    seconds: float
    error: bool
    delegation: bool
    command_missing: bool = False


@dataclass(frozen=True)
class ObservedCommand:
    """One shell command invocation observed in a session log."""

    command: str
    tool: str  # e.g. "bash" or "run_command"
    host: str  # "oc" or "agy"
    error: bool = False


@dataclass(frozen=True)
class SessionReadResult:
    """Ordered shell commands and execution counts extracted from a session log."""

    commands: list[ObservedCommand] = field(default_factory=list)
    delegation_count: int = 0
    missing_command_count: int = 0
    reason_code: str = ""
    format: str = ""  # "oc", "agy", or ""


@dataclass(frozen=True)
class ClaimMatch:
    """Per-claim match evaluation."""

    claim: str
    matched: bool
    matched_command: ObservedCommand | None = None
    indirection: bool = False


@dataclass(frozen=True)
class MatchResult:
    """Structured result of matching claims against observed commands."""

    claims: list[ClaimMatch] = field(default_factory=list)
    unmatched_claims: list[str] = field(default_factory=list)
    unmatched_observed: list[ObservedCommand] = field(default_factory=list)
    matched_claims: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CorroborationVerdict:
    """Turn-level corroboration assessment."""

    verdict: str  # "corroborated" | "uncorroborated" | "indeterminate"
    reason_code: str
    claimed_count: int
    observed_count: int
    matched_count: int
    delegation_count: int
    missing_command_count: int
    matched_claims: list[str] = field(default_factory=list)
    unmatched_claims: list[str] = field(default_factory=list)
    observed_commands: list[ObservedCommand] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {
            "claimed": self.claimed_count,
            "observed": self.observed_count,
            "matched": self.matched_count,
            "delegations": self.delegation_count,
            "missing_command_text": self.missing_command_count,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason_code": self.reason_code,
            "claimed_count": self.claimed_count,
            "observed_count": self.observed_count,
            "matched_count": self.matched_count,
            "delegation_count": self.delegation_count,
            "missing_command_count": self.missing_command_count,
            "counts": self.counts,
        }


# --- Log Extraction (E-01, E-02) -----------------------------------------------------


def session_event_host(obj: Any) -> str:
    """Identify session event host format ('agy', 'oc', or '').

    Checks 'event' in obj first, then 'type' and 'part' in obj.
    """
    if not isinstance(obj, (dict, Mapping)):
        return ""
    if "event" in obj:
        return "agy"
    if "type" in obj and "part" in obj:
        return "oc"
    return ""


def _to_float(v: Any) -> float:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return 0.0


def tool_call_from_event(obj: Any) -> ToolCall | None:
    """Extract a normalized ToolCall record from a single session event object.

    Pure stdlib-only. Takes ONE already-decoded JSON object and returns a ToolCall
    record if the event is a completed/terminal tool call, or None if the event is
    not a tool call (such as step_finish, step_start, error, result, agent_response,
    or a non-terminal tool state).

    DESIGN DECISIONS:
    1. Tool-Name Whitespace (E-02, resolving F-07):
       The tool name is stripped via .strip() on BOTH hosts.
       Rationale:
       (a) An unstripped tool name is a host-formatting artifact rather than a
           distinct tool.
       (b) run_dashboard was internally inconsistent because run_dashboard.tool_category
           does .strip() before lookup, causing categories={'shell': 1} alongside
           tools={' bash ': 1}.
       (c) Stripping ensures the dashboard's tools counter agrees with its own
           categories counter.

    2. Whitespace-Only Command Text (E-03, resolving F-08):
       A command string that is empty after stripping is treated as ABSENT
       (command=None, command_missing=True).
       Rationale:
       (a) A blank string is not an executable command; counting it as one inflates
           the dashboard's commands histogram with an un-actionable 'other' bucket.
       (b) The distinguishable command_missing=True flag allows extract_session_commands
           to increment missing_command_count for shell calls without command text,
           while cleanly distinguishing them from non-shell calls (command_missing=False).

    3. Subagent Vocabulary (E-04, resolving F-09):
       The delegation flag is set for any tool name in SUBAGENT_TOOLS:
       {'task', 'browser_subagent', 'subagent', 'invoke_subagent'}.
       Evidence:
       - 'invoke_subagent' is referenced in-tree as a real Antigravity tool name
         (stall_progress lists 'invoke_subagent' alongside 'schedule' and 'manage_task'
         as tool names that start background tasks, and its docstring cites it).
       - 'subagent' has no in-tree occurrence outside SUBAGENT_TOOLS and CATEGORY_ORDER.
       - Neither appears in committed fixtures, which use only 'task' and
         'browser_subagent'. This is a consistency fix backed by one in-tree reference.
    """
    if not isinstance(obj, (dict, Mapping)):
        return None

    if "event" in obj:
        su = obj.get("step_update")
        if not isinstance(su, (dict, Mapping)):
            return None
        state = su.get("state")
        stype = su.get("step_type")
        if (state != "DONE" and state != "ERROR") or stype != "tool":
            return None
        tool_name = str(su.get("tool_name") or "").strip()
        is_error = state == "ERROR"
        is_delegation = tool_name in SUBAGENT_TOOLS
        secs = _to_float(su.get("duration_seconds"))
        info = su.get("tool_info")
        info_dict = info if isinstance(info, (dict, Mapping)) else {}
        params = info_dict.get("parameters")
        params_dict = params if isinstance(params, (dict, Mapping)) else {}

        command: str | None = None
        command_missing = False
        if tool_name == "run_command":
            raw_cmd = params_dict.get("CommandLine")
            if raw_cmd is None:
                command_missing = True
            else:
                s_cmd = str(raw_cmd)
                if not s_cmd.strip():
                    command_missing = True
                else:
                    command = s_cmd

        fpath = params_dict.get("AbsolutePath") or params_dict.get("TargetFile")
        path = str(fpath) if fpath else None
        return ToolCall(
            tool_name,
            "agy",
            command,
            path,
            secs,
            is_error,
            is_delegation,
            command_missing,
        )

    if "type" in obj and "part" in obj:
        if obj.get("type") != "tool_use":
            return None
        part = obj.get("part")
        part_dict = part if isinstance(part, (dict, Mapping)) else {}
        tool_name = str(part_dict.get("tool") or "").strip()
        state = part_dict.get("state")
        state_dict = state if isinstance(state, (dict, Mapping)) else {}
        is_error = state_dict.get("status") == "error"
        is_delegation = tool_name in SUBAGENT_TOOLS

        t = state_dict.get("time")
        t_dict = t if isinstance(t, (dict, Mapping)) else {}
        end_val = t_dict.get("end")
        secs = (
            (_to_float(end_val) - _to_float(t_dict.get("start"))) / 1000.0
            if end_val
            else 0.0
        )

        inp = state_dict.get("input")
        inp_dict = inp if isinstance(inp, (dict, Mapping)) else {}
        command = None
        command_missing = False
        if tool_name == "bash":
            raw_cmd = inp_dict.get("command")
            if raw_cmd is None:
                command_missing = True
            else:
                s_cmd = str(raw_cmd)
                if not s_cmd.strip():
                    command_missing = True
                else:
                    command = s_cmd

        fpath = inp_dict.get("filePath")
        path = str(fpath) if fpath else None
        return ToolCall(
            tool_name,
            "oc",
            command,
            path,
            secs,
            is_error,
            is_delegation,
            command_missing,
        )

    return None


def extract_session_commands(path: Path | str) -> SessionReadResult:
    """Extract ordered shell commands and non-shell signals from a session log.

    Pure stdlib-only. Never raises exceptions on nonexistent, directory, binary,
    truncated, or malformed files.
    """
    try:
        p = Path(path)
    except (TypeError, ValueError, OSError):
        return SessionReadResult(reason_code=INDETERMINATE_LOG_UNREADABLE)

    try:
        if not p.exists() or p.is_dir():
            return SessionReadResult(reason_code=INDETERMINATE_LOG_UNREADABLE)
        if p.stat().st_size == 0:
            return SessionReadResult(reason_code=INDETERMINATE_LOG_EMPTY)
        # Check for binary file (null bytes)
        with open(p, "rb") as bf:
            chunk = bf.read(1024)
            if b"\x00" in chunk:
                return SessionReadResult(reason_code=INDETERMINATE_LOG_UNREADABLE)
    except OSError:
        return SessionReadResult(reason_code=INDETERMINATE_LOG_UNREADABLE)

    commands: list[ObservedCommand] = []
    delegation_count = 0
    missing_command_count = 0
    session_format = ""
    valid_events = 0

    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line or line[0] != "{":
                    continue
                try:
                    obj = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                if not isinstance(obj, dict):
                    continue

                valid_events += 1

                # Discriminate host format:
                host = session_event_host(obj)
                if host:
                    session_format = host

                tc = tool_call_from_event(obj)
                if tc is not None:
                    if tc.delegation:
                        delegation_count += 1
                    elif tc.command is not None:
                        commands.append(
                            ObservedCommand(
                                command=tc.command,
                                tool=tc.tool,
                                host=tc.host,
                                error=tc.error,
                            )
                        )
                    elif tc.command_missing:
                        missing_command_count += 1
    except OSError:
        return SessionReadResult(reason_code=INDETERMINATE_LOG_UNREADABLE)

    if valid_events == 0:
        return SessionReadResult(reason_code=INDETERMINATE_LOG_EMPTY)

    return SessionReadResult(
        commands=commands,
        delegation_count=delegation_count,
        missing_command_count=missing_command_count,
        reason_code="",
        format=session_format,
    )


# --- Tolerant Command Matcher (E-03) --------------------------------------------------

_CHAINING_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||[;|])\s*")


def normalize_command(cmd: str) -> str:
    """Collapse internal whitespace and strip leading/trailing spaces."""
    return " ".join(cmd.strip().split())


def split_command_segments(cmd: str) -> list[str]:
    """Split a chained shell command into individual pipeline/command segments."""
    norm = normalize_command(cmd)
    if not norm:
        return []
    segments = [s.strip() for s in _CHAINING_SPLIT_RE.split(norm) if s.strip()]
    if norm not in segments:
        segments.append(norm)
    return segments


def is_unresolved_indirection(cmd_str: str) -> bool:
    """Decide whether an observed command is an unresolved test indirection.

    Matches commands that invoke an indirection tool (`make`) where the target is not
    in the declared known indirection set (`make test`, `make test-all`). The general
    case of F-5(b) fails open rather than guessing.
    """
    norm = normalize_command(cmd_str)
    if not norm:
        return False
    if norm in KNOWN_TEST_INDIRECTIONS:
        return False
    first_token = norm.split()[0].lower()
    return first_token == "make"


def match_single_claim(claim_str: str, observed: ObservedCommand) -> bool:
    """Tolerantly match one claimed test command against one observed shell invocation.

    RULE: Match is tolerant in the direction that costs nothing and strict nowhere:
    1. Exact equality after whitespace normalization.
    2. Truncation: claim truncated to max_len with trailing '...' matches if its prefix
       is contained in or prefixes the observed command.
    3. Prose wrapping: claim is a prose sentence containing the command, or observed
       contains the claim (containment in either direction is preferred over strict equality).
    4. Chained commands: any segment of a chained command (&&, ;, ||, |) matches the claim.
    5. Indirection: an observed command in KNOWN_TEST_INDIRECTIONS matches any claim whose
       first token is a test-runner prefix.
    """
    c_norm = normalize_command(claim_str)
    o_norm = normalize_command(observed.command)

    if not c_norm or not o_norm:
        return False

    # 1. Exact equality
    if c_norm == o_norm:
        return True

    # 2. Known indirection check
    if o_norm in KNOWN_TEST_INDIRECTIONS:
        first_token = c_norm.split()[0].lower().rstrip(":")
        if first_token in TEST_RUNNER_PREFIXES:
            return True

    # Check against full observed string and each chained segment
    segments = split_command_segments(observed.command)

    for seg in segments:
        s_norm = normalize_command(seg)
        if not s_norm:
            continue

        if c_norm == s_norm:
            return True

        # Truncation check: claim ends with '...'
        if c_norm.endswith("..."):
            stem = c_norm[:-3].strip()
            if stem and (s_norm.startswith(stem) or stem in s_norm):
                return True

        # Containment in either direction (prose-wrapping or extra flags)
        if s_norm in c_norm or c_norm in s_norm:
            return True

        # Indirection check per segment
        if s_norm in KNOWN_TEST_INDIRECTIONS:
            first_token = c_norm.split()[0].lower().rstrip(":")
            if first_token in TEST_RUNNER_PREFIXES:
                return True

    return False


def match_claims_to_observed(
    claims: Sequence[str],
    observed_commands: Sequence[ObservedCommand],
) -> MatchResult:
    """Match a sequence of claimed commands against observed log commands."""
    claim_matches: list[ClaimMatch] = []
    unmatched_claims: list[str] = []
    matched_claims: list[str] = []
    matched_observed_indices: set[int] = set()

    for claim in claims:
        norm_claim = normalize_command(claim)
        if not norm_claim:
            continue

        matched = False
        matching_cmd: ObservedCommand | None = None
        is_indir = False

        for idx, obs in enumerate(observed_commands):
            if match_single_claim(claim, obs):
                matched = True
                matching_cmd = obs
                matched_observed_indices.add(idx)
                if normalize_command(obs.command) in KNOWN_TEST_INDIRECTIONS:
                    is_indir = True
                break

        if matched:
            matched_claims.append(claim)
            claim_matches.append(
                ClaimMatch(
                    claim=claim,
                    matched=True,
                    matched_command=matching_cmd,
                    indirection=is_indir,
                )
            )
        else:
            unmatched_claims.append(claim)
            claim_matches.append(ClaimMatch(claim=claim, matched=False))

    unmatched_observed = [
        obs
        for idx, obs in enumerate(observed_commands)
        if idx not in matched_observed_indices
    ]

    return MatchResult(
        claims=claim_matches,
        unmatched_claims=unmatched_claims,
        unmatched_observed=unmatched_observed,
        matched_claims=matched_claims,
    )


# --- Three-State Turn-Level Verdict (E-04) --------------------------------------------


def corroborate_verifier_turn(
    log_path: Path | str,
    claimed_commands: Sequence[str],
) -> CorroborationVerdict:
    """Compute the three-state corroboration verdict for a verifier turn.

    Returns:
        CorroborationVerdict with verdict in ("corroborated", "uncorroborated", "indeterminate")
        and a machine-readable reason code from the closed set.
    """
    clean_claims = [c for c in (normalize_command(x) for x in claimed_commands) if c]

    # Read the session log
    read_res = extract_session_commands(log_path)

    # 1. Log absent or unreadable
    if read_res.reason_code == INDETERMINATE_LOG_UNREADABLE:
        return CorroborationVerdict(
            verdict=INDETERMINATE,
            reason_code=INDETERMINATE_LOG_UNREADABLE,
            claimed_count=len(clean_claims),
            observed_count=len(read_res.commands),
            matched_count=0,
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            unmatched_claims=list(clean_claims),
            observed_commands=read_res.commands,
        )

    # 2. Log empty
    if read_res.reason_code == INDETERMINATE_LOG_EMPTY:
        return CorroborationVerdict(
            verdict=INDETERMINATE,
            reason_code=INDETERMINATE_LOG_EMPTY,
            claimed_count=len(clean_claims),
            observed_count=len(read_res.commands),
            matched_count=0,
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            unmatched_claims=list(clean_claims),
            observed_commands=read_res.commands,
        )

    # 3. Claims list empty
    if not clean_claims:
        return CorroborationVerdict(
            verdict=INDETERMINATE,
            reason_code=INDETERMINATE_CLAIMS_EMPTY,
            claimed_count=0,
            observed_count=len(read_res.commands),
            matched_count=0,
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            unmatched_claims=[],
            observed_commands=read_res.commands,
        )

    # 4. Delegation to subagent occurred
    if read_res.delegation_count > 0:
        return CorroborationVerdict(
            verdict=INDETERMINATE,
            reason_code=INDETERMINATE_DELEGATION,
            claimed_count=len(clean_claims),
            observed_count=len(read_res.commands),
            matched_count=0,
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            unmatched_claims=list(clean_claims),
            observed_commands=read_res.commands,
        )

    # 5. Missing command text on shell calls (or zero observed shell commands)
    if len(read_res.commands) == 0:
        return CorroborationVerdict(
            verdict=INDETERMINATE,
            reason_code=INDETERMINATE_MISSING_COMMAND_TEXT,
            claimed_count=len(clean_claims),
            observed_count=0,
            matched_count=0,
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            unmatched_claims=list(clean_claims),
            observed_commands=[],
        )

    # Run matcher against observed commands
    match_res = match_claims_to_observed(clean_claims, read_res.commands)

    # Corroborated when at least one claim matched an observed non-errored command
    non_errored_matches = [
        cm
        for cm in match_res.claims
        if cm.matched and cm.matched_command and not cm.matched_command.error
    ]

    if non_errored_matches:
        return CorroborationVerdict(
            verdict=CORROBORATED,
            reason_code=CORROBORATED,
            claimed_count=len(clean_claims),
            observed_count=len(read_res.commands),
            matched_count=len(match_res.matched_claims),
            delegation_count=read_res.delegation_count,
            missing_command_count=read_res.missing_command_count,
            matched_claims=match_res.matched_claims,
            unmatched_claims=match_res.unmatched_claims,
            observed_commands=read_res.commands,
        )

    # 6. Unresolved indirection: an observed command has an indirection prefix (e.g. make)
    # but names no test target this module can resolve. Fail-open to indeterminate.
    for obs in read_res.commands:
        if is_unresolved_indirection(obs.command):
            return CorroborationVerdict(
                verdict=INDETERMINATE,
                reason_code=INDETERMINATE_INDIRECTION_UNRESOLVED,
                claimed_count=len(clean_claims),
                observed_count=len(read_res.commands),
                matched_count=0,
                delegation_count=read_res.delegation_count,
                missing_command_count=read_res.missing_command_count,
                unmatched_claims=match_res.unmatched_claims,
                observed_commands=read_res.commands,
            )

    # Single uncorroborated case: log read, shell commands observed, no delegation,
    # no unresolved indirection, and no claims matched.
    return CorroborationVerdict(
        verdict=UNCORROBORATED,
        reason_code=UNCORROBORATED,
        claimed_count=len(clean_claims),
        observed_count=len(read_res.commands),
        matched_count=0,
        delegation_count=read_res.delegation_count,
        missing_command_count=read_res.missing_command_count,
        unmatched_claims=match_res.unmatched_claims,
        observed_commands=read_res.commands,
    )


# Function aliases for consumer convenience
check_verifier_corroboration = corroborate_verifier_turn
compute_verifier_corroboration = corroborate_verifier_turn
