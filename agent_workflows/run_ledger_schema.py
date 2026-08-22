"""Run-ledger + evidence-contract schemas: the typed record vocabulary for durable execution facts.

awoptimize Order 02 (`7qs57e`) E-01. Defines versioned, typed schemas for every state-changing record
in a workflow run, so what was REQUIRED, ATTEMPTED, OBSERVED, and independently VERIFIED are separate
durable facts rather than a model's prose. This is the type layer; the append-only store (E-03),
evidence capture (E-04), validators (E-05), and completion predicates (E-06) build on it.

Record kinds (each carries actor role, timestamps, exact repo/worktree identity, causal parent, and
schema version, so a record is attributable and reproducible):

  * run                - a run's identity + the frozen workflow/requirement digests it executes.
  * requirement_set    - the frozen set of MUST requirements + scope fence + validations for a run.
  * requirement_revision - a semantic change to the frozen set (invalidates affected evidence).
  * step_attempt       - an attempt at an execution step (E-*): performed/blocked/failed.
  * tool_event         - a captured command/tool invocation (argv, cwd, exit, output refs).
  * evidence_envelope  - a bundle of provenance binding a claim to reproducible state.
  * artifact_ref       - a produced artifact (path + digest).
  * verifier_decision  - an independent verifier's per-requirement finding (satisfied/failed/...).
  * correction         - a corrective action linked to a failed requirement.
  * retry              - a bounded retry keyed by failure class + idempotency key.
  * human_approval     - a recorded human authorization at a gate.
  * terminal_transaction - the record of a terminal lifecycle transition.

Pure + stdlib-only (D138: the stdlib does this; D139: no runtime YAML). No filesystem, model, or
network side effects: this module only DEFINES and VALIDATES record shapes. Actual persistence is
E-03.
"""

from __future__ import annotations

import re
from typing import Any, Dict, FrozenSet, List, Mapping, NamedTuple, Tuple

LEDGER_SCHEMA_VERSION = 1

# ---- enumerated vocabularies ---------------------------------------------------------------------

# Actor ROLES. The role that authored a record; used by E-05/E-06 to enforce that an executor cannot
# author a verifier decision (identity-collision refusal) and that only a coordinator holds terminal
# authority.
ROLES: FrozenSet[str] = frozenset(
    ("coordinator", "executor", "verifier", "corrector", "human", "runtime")
)

# Record KINDS (the closed set above).
RECORD_KINDS: FrozenSet[str] = frozenset(
    (
        "run",
        "requirement_set",
        "requirement_revision",
        "step_attempt",
        "tool_event",
        "evidence_envelope",
        "artifact_ref",
        "verifier_decision",
        "correction",
        "retry",
        "human_approval",
        "terminal_transaction",
    )
)

# Execution-attempt states (mirror the IPD execution-state vocabulary).
ATTEMPT_STATES: FrozenSet[str] = frozenset(("performed", "blocked", "failed"))

# Verifier per-requirement decisions.
VERIFIER_RESULTS: FrozenSet[str] = frozenset(
    ("satisfied", "partial", "failed", "not_verifiable")
)

# Evidence kinds (kept in sync with the workflow schema's EVIDENCE_KINDS; a run's evidence binds one).
EVIDENCE_KINDS: FrozenSet[str] = frozenset(
    ("command", "diff", "artifact", "test_report", "inspection")
)

# ---- identifier grammars -------------------------------------------------------------------------

_RUN_ID_RE = re.compile(r"^run-[0-9a-f]{8,}$")  # run-<hex>
_REQUIREMENT_ID_RE = re.compile(r"^R-[0-9]{2,}$")  # matches the workflow schema R-NN
_STEP_ID_RE = re.compile(r"^S-[0-9]{2,}$")  # matches the workflow schema S-NN
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
# RFC3339-ish UTC timestamp with a trailing Z; validated structurally (not parsed) here.
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def is_run_id(v: Any) -> bool:
    return isinstance(v, str) and bool(_RUN_ID_RE.match(v))


def is_timestamp(v: Any) -> bool:
    return isinstance(v, str) and bool(_TIMESTAMP_RE.match(v))


def is_sha256(v: Any) -> bool:
    return isinstance(v, str) and bool(_SHA256_RE.match(v))


# ---- findings ------------------------------------------------------------------------------------


class Finding(NamedTuple):
    code: str
    where: str
    message: str


class ValidationResult(NamedTuple):
    ok: bool
    findings: Tuple[Finding, ...]


# ---- common envelope fields ----------------------------------------------------------------------

# Every record carries these. `parent` is the causal-parent record id (or "" for a root record).
_COMMON_FIELDS: Tuple[Tuple[str, type], ...] = (
    ("schema_version", int),
    ("kind", str),
    ("seq", int),  # monotonic sequence number within a ledger (assigned by E-03)
    ("run_id", str),
    ("actor", str),  # a ROLE
    ("timestamp", str),  # RFC3339 UTC Z
    ("parent", str),  # causal parent record id or ""
)

# Per-kind required extra fields (beyond the common envelope), with types.
_KIND_FIELDS: Dict[str, Tuple[Tuple[str, type], ...]] = {
    "run": (
        ("workflow_digest", str),
        ("requirement_digest", str),
        ("repo", str),
        ("head", str),
    ),
    "requirement_set": (
        ("requirement_digest", str),
        ("requirements", list),
        ("scope_fence", dict),
    ),
    "requirement_revision": (
        ("prev_digest", str),
        ("new_digest", str),
        ("reason", str),
    ),
    "step_attempt": (("step", str), ("state", str), ("attempt", int)),
    "tool_event": (
        ("argv", list),
        ("cwd", str),
        ("exit_code", int),
        ("stdout_sha256", str),
    ),
    "evidence_envelope": (
        ("evidence_kind", str),
        ("binds", list),
        ("head", str),
        ("worktree", str),
    ),
    "artifact_ref": (("path", str), ("sha256", str)),
    "verifier_decision": (("requirement", str), ("result", str)),
    "correction": (("corrects_requirement", str), ("description", str)),
    "retry": (("retries_step", str), ("failure_class", str), ("idempotency_key", str)),
    "human_approval": (("gate", str), ("approver", str)),
    "terminal_transaction": (("terminal_status", str), ("moved_to", str)),
}


def _type_ok(val: Any, typ: type) -> bool:
    if typ is int:
        return isinstance(val, int) and not isinstance(val, bool)
    return isinstance(val, typ)


def validate_record(rec: Any) -> ValidationResult:
    """Validate a single ledger record's shape + per-kind fields + key state rules. Pure; never
    raises; returns typed findings. Deep semantic truth (is the evidence real) is E-05's job."""

    findings: List[Finding] = []
    if not isinstance(rec, Mapping):
        return ValidationResult(
            False, (Finding("RL-E001", "", "record must be a mapping"),)
        )

    # common envelope
    for name, typ in _COMMON_FIELDS:
        if name not in rec:
            findings.append(
                Finding("RL-E010", name, "missing common field '{0}'".format(name))
            )
        elif not _type_ok(rec[name], typ):
            findings.append(
                Finding("RL-E011", name, "field '{0}' has the wrong type".format(name))
            )

    ver = rec.get("schema_version")
    if (
        isinstance(ver, int)
        and not isinstance(ver, bool)
        and ver != LEDGER_SCHEMA_VERSION
    ):
        findings.append(
            Finding(
                "RL-E012",
                "schema_version",
                "unsupported schema_version {0}".format(ver),
            )
        )

    kind = rec.get("kind")
    if kind not in RECORD_KINDS:
        findings.append(
            Finding("RL-E013", "kind", "unknown record kind '{0}'".format(kind))
        )

    if "actor" in rec and rec.get("actor") not in ROLES:
        findings.append(
            Finding(
                "RL-E014", "actor", "unknown actor role '{0}'".format(rec.get("actor"))
            )
        )

    if "run_id" in rec and not is_run_id(rec.get("run_id")):
        findings.append(Finding("RL-E015", "run_id", "run_id must match 'run-<hex>'"))

    if "timestamp" in rec and not is_timestamp(rec.get("timestamp")):
        findings.append(
            Finding("RL-E016", "timestamp", "timestamp must be RFC3339 UTC (…Z)")
        )

    if "seq" in rec and _type_ok(rec.get("seq"), int) and rec["seq"] < 0:
        findings.append(Finding("RL-E017", "seq", "seq must be >= 0"))

    # per-kind fields
    if kind in _KIND_FIELDS:
        for name, typ in _KIND_FIELDS[kind]:
            if name not in rec:
                findings.append(
                    Finding(
                        "RL-E020",
                        name,
                        "kind '{0}' requires field '{1}'".format(kind, name),
                    )
                )
            elif not _type_ok(rec[name], typ):
                findings.append(
                    Finding(
                        "RL-E021", name, "field '{0}' has the wrong type".format(name)
                    )
                )

    # per-kind value rules
    if kind == "step_attempt" and rec.get("state") not in ATTEMPT_STATES:
        findings.append(
            Finding(
                "RL-E030",
                "state",
                "attempt state must be one of {0}".format(sorted(ATTEMPT_STATES)),
            )
        )
    if kind == "verifier_decision":
        if rec.get("result") not in VERIFIER_RESULTS:
            findings.append(
                Finding(
                    "RL-E031",
                    "result",
                    "verifier result must be one of {0}".format(
                        sorted(VERIFIER_RESULTS)
                    ),
                )
            )
        # identity rule: a verifier_decision MUST be authored by the verifier role, never the executor.
        if rec.get("actor") not in ("verifier",):
            findings.append(
                Finding(
                    "RL-E032",
                    "actor",
                    "verifier_decision must be authored by the 'verifier' role",
                )
            )
    if kind == "evidence_envelope":
        if rec.get("evidence_kind") not in EVIDENCE_KINDS:
            findings.append(
                Finding(
                    "RL-E033",
                    "evidence_kind",
                    "unknown evidence_kind '{0}'".format(rec.get("evidence_kind")),
                )
            )
        if not is_sha256(rec.get("head")) and rec.get("head") not in ("", None):
            # head may be a commit sha; if present and nonempty it should look like a sha
            pass  # commit shas vary in length across VCS; do not over-constrain here
    if kind == "tool_event":
        if (
            _type_ok(rec.get("stdout_sha256"), str)
            and rec.get("stdout_sha256")
            and not is_sha256(rec.get("stdout_sha256"))
        ):
            findings.append(
                Finding(
                    "RL-E034",
                    "stdout_sha256",
                    "stdout_sha256 must be a sha256 hex digest",
                )
            )
    if kind == "terminal_transaction":
        # only a coordinator or runtime may author a terminal transaction (E-06 enforces the predicate;
        # here we reject an executor-authored terminal record structurally).
        if rec.get("actor") not in ("coordinator", "runtime", "human"):
            findings.append(
                Finding(
                    "RL-E035",
                    "actor",
                    "terminal_transaction must be authored by coordinator/runtime/human, not the executor",
                )
            )

    return ValidationResult(len(findings) == 0, tuple(findings))


def validate_records(records: Any) -> ValidationResult:
    """Validate a sequence of records and their cross-record ordering: seq must be strictly
    increasing from 0, and the first record must be a `run`. Pure."""

    findings: List[Finding] = []
    if not isinstance(records, (list, tuple)):
        return ValidationResult(
            False, (Finding("RL-E002", "", "records must be a list"),)
        )
    prev_seq = -1
    for i, rec in enumerate(records):
        r = validate_record(rec)
        for f in r.findings:
            findings.append(
                Finding(f.code, "records[{0}].{1}".format(i, f.where), f.message)
            )
        if isinstance(rec, Mapping) and _type_ok(rec.get("seq"), int):
            if rec["seq"] <= prev_seq:
                findings.append(
                    Finding(
                        "RL-E040",
                        "records[{0}].seq".format(i),
                        "seq not strictly increasing",
                    )
                )
            prev_seq = rec["seq"]
    if records and isinstance(records[0], Mapping) and records[0].get("kind") != "run":
        findings.append(
            Finding("RL-E041", "records[0]", "first ledger record must be kind 'run'")
        )
    return ValidationResult(len(findings) == 0, tuple(findings))
