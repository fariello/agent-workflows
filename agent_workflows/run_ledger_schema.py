"""Run-ledger + evidence-contract schemas: the typed record vocabulary for durable execution facts.

awoptimize Order 02 (`viuzu4`) E-01. Defines versioned, typed schemas for every state-changing record
in a workflow run, so what was REQUIRED, ATTEMPTED, OBSERVED, and independently VERIFIED are separate
durable facts rather than a model's prose. This is the type layer; the append-only store (Order 03),
evidence capture + validators + completion predicates (Order 04) build on it, and requirement freezing
lives beside it in run_freeze.py (Order 02 E-04/E-05).

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

# The CURRENT ledger schema version emitted for new ledgers. Bumped 1 -> 2 by execset Order 02
# (3m4e54) to add the Set-coordination event kinds (question/decision/skip/lane/checkpoint) and the
# `investigator` role WITHOUT breaking existing v1 ledgers.
LEDGER_SCHEMA_VERSION = 2

# Version-compatibility rule (net-new per 3m4e54 E-01): a ledger record is ACCEPTED when its
# schema_version is any of the supported versions. A v1 ledger still validates (backward compatible);
# a v2 ledger additionally admits the new coordination kinds below. The new kinds require v2 (a v1
# record carrying a v2-only kind is rejected), so an old reader that only knows v1 never sees a kind
# it cannot interpret. This is an ADD-ONLY, monotonic compatibility discipline: no v1 record shape
# changed, and no previously-valid ledger becomes invalid.
SUPPORTED_SCHEMA_VERSIONS: FrozenSet[int] = frozenset((1, 2))

# ---- enumerated vocabularies ---------------------------------------------------------------------

# Actor ROLES. The role that authored a record; used by E-05/E-06 to enforce that an executor cannot
# author a verifier decision (identity-collision refusal) and that only a coordinator holds terminal
# authority. `investigator` (added by 3m4e54 E-01, reconciling the prior divergence where
# verify_roles.ROLE_INVESTIGATOR existed but this ledger omitted it) is a READ-ONLY diagnostic role.
ROLES: FrozenSet[str] = frozenset(
    (
        "coordinator",
        "executor",
        "investigator",
        "verifier",
        "corrector",
        "human",
        "runtime",
    )
)

# The v1 (original awoptimize Order 02) record kinds. These validate at BOTH v1 and v2.
RECORD_KINDS_V1: FrozenSet[str] = frozenset(
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

# The v2-only Set-coordination kinds (3m4e54 E-01). Each makes a decision, skip, lane, or checkpoint
# attributable and hash-chained. A record carrying one of these MUST declare schema_version 2.
RECORD_KINDS_V2_ONLY: FrozenSet[str] = frozenset(
    (
        "question_raised",
        "question_disposition",
        "human_answer",
        "autonomous_decision",
        "scope_deferred",
        "work_claim",
        "lane_outcome",
        "integration_result",
        "set_checkpoint",
    )
)

# Record KINDS (the closed set: v1 kinds + v2-only kinds).
RECORD_KINDS: FrozenSet[str] = RECORD_KINDS_V1 | RECORD_KINDS_V2_ONLY

# ---- v2 coordination-kind value vocabularies -----------------------------------------------------

# A question's disposition: how an autonomously-raised question was resolved.
QUESTION_DISPOSITIONS: FrozenSet[str] = frozenset(
    ("decided_autonomously", "deferred_subgraph", "deferred_ipd", "answered_by_human")
)

# The outcome of a single scheduled lane (one unit of scheduled work).
LANE_OUTCOMES: FrozenSet[str] = frozenset(
    ("performed", "blocked", "failed", "deferred", "unknown_outcome", "skipped")
)

# The result of integrating a completed lane's work into the main worktree.
INTEGRATION_RESULTS: FrozenSet[str] = frozenset(
    ("integrated", "conflict", "rolled_back", "skipped")
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
    # ---- v2 Set-coordination kinds (3m4e54 E-01) ----
    # A question the coordinator raised at runtime (never appended to the approved IPD's authoring
    # Open Questions). `question_id` is a stable per-run D<number>/Q<number>-style handle.
    "question_raised": (
        ("question_id", str),
        ("context", str),
        ("affected_nodes", list),
    ),
    # How a raised question was resolved. `prev` optionally points to a record this supersedes
    # (reusing the append-a-newer-record idiom per OQ-03; empty string = not a supersession).
    "question_disposition": (
        ("question_id", str),
        ("disposition", str),
        ("prev", str),
    ),
    # A recorded human answer to a raised question (only ever authored by the human role).
    "human_answer": (("question_id", str), ("answer", str)),
    # An autonomous decision made in lieu of prompting. `consultation_preferred` marks a choice the
    # coordinator would have preferred to consult a human on but proceeded with a robust default.
    # `prev` supersedes an earlier decision (reversal) per OQ-03.
    "autonomous_decision": (
        ("decision_id", str),
        ("selected_option", str),
        ("confidence", str),
        ("consultation_preferred", bool),
        ("reversible", bool),
        ("prev", str),
    ),
    # A skipped/deferred scope unit. `scope` = the subgraph/IPD id deferred; `blocks` = the node ids
    # blocked as a consequence (descendants), so independent work is provably NOT blocked.
    "scope_deferred": (("scope", str), ("reason", str), ("blocks", list)),
    # A single-writer claim on a schedulable node (a lane). `lane_id` is the manifest node id.
    "work_claim": (("lane_id", str), ("node", str)),
    # The outcome of one scheduled lane.
    "lane_outcome": (("lane_id", str), ("outcome", str)),
    # The result of integrating a lane's work into the main worktree.
    "integration_result": (("lane_id", str), ("result", str)),
    # A durable Set-level checkpoint binding the Set state to the coordinator's timestamped position.
    "set_checkpoint": (("set_id", str), ("set_state", str)),
}

# The v1 kinds whose per-kind fields are part of the v1 contract (used to gate v2-only kinds).
_V2_ONLY_KINDS: FrozenSet[str] = RECORD_KINDS_V2_ONLY


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
        and ver not in SUPPORTED_SCHEMA_VERSIONS
    ):
        findings.append(
            Finding(
                "RL-E012",
                "schema_version",
                "unsupported schema_version {0} (supported: {1})".format(
                    ver, sorted(SUPPORTED_SCHEMA_VERSIONS)
                ),
            )
        )

    kind = rec.get("kind")
    if kind not in RECORD_KINDS:
        findings.append(
            Finding("RL-E013", "kind", "unknown record kind '{0}'".format(kind))
        )
    # Version gate: a v2-only coordination kind requires schema_version >= 2, so a v1 reader never
    # encounters a kind it cannot interpret (add-only forward compatibility).
    elif (
        kind in _V2_ONLY_KINDS
        and isinstance(ver, int)
        and not isinstance(ver, bool)
        and ver < 2
    ):
        findings.append(
            Finding(
                "RL-E018",
                "kind",
                "record kind '{0}' requires schema_version >= 2 (got {1})".format(
                    kind, ver
                ),
            )
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

    # ---- v2 Set-coordination value + authority rules (3m4e54 E-01) ----
    if (
        kind == "question_disposition"
        and rec.get("disposition") not in QUESTION_DISPOSITIONS
    ):
        findings.append(
            Finding(
                "RL-E050",
                "disposition",
                "question disposition must be one of {0}".format(
                    sorted(QUESTION_DISPOSITIONS)
                ),
            )
        )
    if kind == "human_answer" and rec.get("actor") != "human":
        # A human answer can ONLY be authored by the human role; consent is never synthesized.
        findings.append(
            Finding(
                "RL-E051",
                "actor",
                "human_answer must be authored by the 'human' role",
            )
        )
    if kind == "lane_outcome" and rec.get("outcome") not in LANE_OUTCOMES:
        findings.append(
            Finding(
                "RL-E052",
                "outcome",
                "lane outcome must be one of {0}".format(sorted(LANE_OUTCOMES)),
            )
        )
    if kind == "integration_result":
        if rec.get("result") not in INTEGRATION_RESULTS:
            findings.append(
                Finding(
                    "RL-E053",
                    "result",
                    "integration result must be one of {0}".format(
                        sorted(INTEGRATION_RESULTS)
                    ),
                )
            )
        # Integration into the authoritative main worktree is a coordinator-only act.
        if rec.get("actor") not in ("coordinator", "runtime"):
            findings.append(
                Finding(
                    "RL-E054",
                    "actor",
                    "integration_result must be authored by coordinator/runtime, not the executor",
                )
            )
    if kind == "set_checkpoint":
        # Import locally to avoid a module import cycle (set_state imports nothing from here).
        from agent_workflows import set_state as _ss

        if rec.get("set_state") not in _ss.ALL_SET_STATES:
            findings.append(
                Finding(
                    "RL-E055",
                    "set_state",
                    "set_checkpoint set_state must be a set_-prefixed Set state ({0})".format(
                        sorted(_ss.ALL_SET_STATES)
                    ),
                )
            )
        # Only the coordinator (or runtime) may checkpoint the Set state (coordinator-only authority).
        if rec.get("actor") not in ("coordinator", "runtime"):
            findings.append(
                Finding(
                    "RL-E056",
                    "actor",
                    "set_checkpoint must be authored by coordinator/runtime",
                )
            )
    if kind == "autonomous_decision":
        # An autonomous decision is the coordinator/executor's to record; it is NEVER a human_answer.
        if rec.get("actor") not in ("coordinator", "executor", "runtime"):
            findings.append(
                Finding(
                    "RL-E057",
                    "actor",
                    "autonomous_decision must be authored by coordinator/executor/runtime",
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
