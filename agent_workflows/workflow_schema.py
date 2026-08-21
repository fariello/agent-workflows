"""Canonical workflow schema: the single typed source of truth for workflow semantics.

This module OWNS the machine-checkable contract for a canonical workflow package, per the
`awoptimize` architecture Set (research `y1eb0q`; orchestrator `p070c8`) and the approved ADR
DECISIONS D139 (canonical workflow source is a typed YAML package compiled at build time to
generated projections). It is awoptimize Order 01 (`nmwy3m`) E-01: the versioned type system plus
pure validation of a parsed-and-normalized workflow mapping.

Scope (E-01): definitions + pure validation ONLY. This module has NO side effects: it does not read
the filesystem, parse YAML, call a model, use the network, or write anything. The build-time YAML
parse and the canonical-source loader live in the loader module (E-02/E-03); the compiler that emits
generated projections lives in the compiler module (E-04+). Keeping the schema pure means the
installed runtime can import it without any parser dependency (D139: no YAML parser in a runtime
path). It is stdlib-only (D138: dependency minimization; the standard library does this job) and
Python 3.9 compatible.

The schema validates a workflow that has ALREADY been parsed into a plain Python mapping (dicts,
lists, str, int, bool, None) by the build-time loader. It does not care whether the on-disk source
was YAML or anything else; it validates the normalized data structure. This keeps the source format
(D139: YAML) decoupled from the semantic contract.

What this module proves (deterministic, structural + state):

* every required field is present and every field has the declared type;
* identifiers (workflow id, requirement `R-*`, step `S-*`) match their grammar and are unique;
* step dependency edges reference existing steps, are not self-references, and contain no cycle;
* every step and validation check binds to at least one declared evidence predicate;
* permissions are internally consistent (a forbidden path cannot also be an allowed path; a
  read-only workflow declares no write/mutation permission);
* declared host-capability requirements are drawn from the known capability vocabulary;
* no step declares a TERMINAL lifecycle action (those belong to the runtime/coordinator, never a
  model-authored step -- D139 boundary and the awoptimize evidence contract).

What it explicitly does NOT establish: semantic correctness, coverage, whether an action is
meaningfully atomic, or whether evidence will actually be produced. Those remain the reviewer's and
the runtime's responsibility (mirrors the honest boundary `ipd_lint` states for IPDs).
"""

from __future__ import annotations

import re
from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
)

# --------------------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------------------

# The schema version. Bump on any breaking change to the contract; the loader/compiler record it in
# generated output so a consumer can detect a version mismatch rather than silently misparse.
SCHEMA_VERSION = 1


# --------------------------------------------------------------------------------------
# Enumerated vocabularies (closed sets; extension is a deliberate, reviewed edit here)
# --------------------------------------------------------------------------------------

# A workflow's INTENT: the broad activity class. Grounded in the current manifest families.
INTENTS: FrozenSet[str] = frozenset(
    (
        "review",  # e.g. plan-review, release-review
        "assess",  # single-concern assessment (lenses)
        "advise",  # interactive persona consultation
        "verify",  # evidence capture / cross-check
        "lifecycle",  # execution/transition gating
        "author",  # produce an artifact (spec, research-prompt, handoff)
        "orient",  # getting-started / whatnext / list-workflows
        "operate",  # setup-repo, migrate, incident, release-notes, benchmark
    )
)

# RISK class: how much damage a bad run can do. Drives default gate strictness.
RISKS: FrozenSet[str] = frozenset(("read-only", "low", "medium", "high", "destructive"))

# INTERACTION mode: whether the workflow needs a human in the loop.
INTERACTION_MODES: FrozenSet[str] = frozenset(
    ("noninteractive", "optional", "interactive")
)

# MUTATION boundary: what the workflow is permitted to change. Ordered from least to most.
MUTATION_BOUNDARIES: FrozenSet[str] = frozenset(
    (
        "none",  # reads only; produces a report/answer
        "planning-only",  # edits planning/prose artifacts only (plans, specs, docs)
        "product",  # edits product code/tests/config
        "external",  # side effects outside the repo (network, publish) -- gated
    )
)

# Known HOST CAPABILITY requirements a workflow may declare. A workflow that requires a capability a
# host cannot prove is refused at generation time (Order 05 owns the evidence registry; here we only
# validate the requirement is a known token, never that a host supports it).
HOST_CAPABILITIES: FrozenSet[str] = frozenset(
    (
        "noninteractive_exec",  # can run headless (e.g. `codex exec`, `claude -p`)
        "structured_output",  # emits machine-readable (JSON/stream-json) output
        "subagent",  # can spawn an isolated child context
        "fresh_context",  # can start a clean/new session for a verifier
        "background_job",  # can run work in the background
        "worktree_isolation",  # can isolate a mutator in a separate git worktree
        "progress_events",  # can stream progress
        "skill_discovery",  # discovers packaged skills
    )
)

# EVIDENCE predicate kinds an outcome may require. Mirrors the Order 02 evidence-envelope families,
# named here so a step/validation can bind to a kind the runtime knows how to capture.
EVIDENCE_KINDS: FrozenSet[str] = frozenset(
    (
        "command",  # a captured command: argv, cwd, exit, output hash
        "diff",  # a repository diff / file-content change at a bound HEAD
        "artifact",  # a produced file/artifact with an inspectable path + digest
        "test_report",  # a structured test result
        "inspection",  # a documented human/verifier observation when capture is impossible
    )
)

# Tokens a step MUST NOT contain as an action verb: terminal lifecycle mutations are owned by the
# runtime/coordinator, never a model-authored workflow step (D139 boundary). These are matched
# case-insensitively as whole phrases in a step's declared `terminal_action` guard, not scanned from
# free prose (the schema validates the structured field, not English).
FORBIDDEN_STEP_TERMINAL_ACTIONS: FrozenSet[str] = frozenset(
    (
        "commit",
        "push",
        "tag",
        "release",
        "publish",
        "deploy",
        "git-mv-to-terminal",
        "set-terminal-status",
    )
)


# --------------------------------------------------------------------------------------
# Identifier grammars
# --------------------------------------------------------------------------------------

# Workflow id: lowercase kebab, matching the manifest command style (e.g. `plan-review`).
_WORKFLOW_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

# Requirement id: R- followed by two or more digits (stable, per-workflow scope), mirroring the
# IPD E-*/V-* grammar so the two systems read consistently.
_REQUIREMENT_ID_RE = re.compile(r"^R-[0-9]{2,}$")

# Step id: S- followed by two or more digits.
_STEP_ID_RE = re.compile(r"^S-[0-9]{2,}$")


def is_valid_workflow_id(token: Any) -> bool:
    """True iff ``token`` is a well-formed workflow id (lowercase-kebab)."""

    return isinstance(token, str) and bool(_WORKFLOW_ID_RE.match(token))


def is_valid_requirement_id(token: Any) -> bool:
    """True iff ``token`` is a well-formed requirement id (``R-NN``)."""

    return isinstance(token, str) and bool(_REQUIREMENT_ID_RE.match(token))


def is_valid_step_id(token: Any) -> bool:
    """True iff ``token`` is a well-formed step id (``S-NN``)."""

    return isinstance(token, str) and bool(_STEP_ID_RE.match(token))


# --------------------------------------------------------------------------------------
# Field contract
# --------------------------------------------------------------------------------------

# Required top-level fields on a workflow mapping and their expected Python types (post-parse).
# ``aliases`` etc. are optional and validated separately when present.
_REQUIRED_FIELDS: Tuple[Tuple[str, type], ...] = (
    ("schema_version", int),
    ("id", str),
    ("intent", str),
    ("risk", str),
    ("interaction", str),
    ("mutation_boundary", str),
    ("summary", str),
    ("requirements", list),
    ("steps", list),
    ("validations", list),
)

_OPTIONAL_FIELDS: Tuple[Tuple[str, type], ...] = (
    ("aliases", list),
    ("permissions", dict),
    ("host_capabilities", list),
    ("rollback", str),
    ("resumable", bool),
    ("orchestration", dict),
)

_ALL_FIELD_NAMES: FrozenSet[str] = frozenset(
    name for name, _t in (_REQUIRED_FIELDS + _OPTIONAL_FIELDS)
)


class Finding(NamedTuple):
    """One validation finding. ``code`` is a stable rule code; ``where`` locates it (a dotted path
    like ``steps[2].depends_on`` or ``id``); ``message`` is human-readable."""

    code: str
    where: str
    message: str


class ValidationResult(NamedTuple):
    """The outcome of validating a workflow mapping. ``ok`` is True iff there are no findings."""

    ok: bool
    findings: Tuple[Finding, ...]


def _t_name(t: type) -> str:
    return {
        int: "integer",
        str: "string",
        list: "list",
        dict: "mapping",
        bool: "boolean",
    }.get(t, t.__name__)


def validate_workflow(data: Any) -> ValidationResult:
    """Validate a parsed-and-normalized workflow mapping against the schema (E-01).

    ``data`` is the plain Python structure the build-time loader produced (dicts/lists/scalars).
    Returns a :class:`ValidationResult`; it never raises on invalid input and never mutates ``data``.
    Findings are ordered deterministically (by discovery order, which is stable for a given input).
    """

    findings: List[Finding] = []

    if not isinstance(data, Mapping):
        return ValidationResult(
            False, (Finding("WF-E001", "", "workflow must be a mapping"),)
        )

    # 1) schema_version
    ver = data.get("schema_version")
    if not isinstance(ver, int) or isinstance(ver, bool):
        findings.append(
            Finding("WF-E002", "schema_version", "schema_version must be an integer")
        )
    elif ver != SCHEMA_VERSION:
        findings.append(
            Finding(
                "WF-E003",
                "schema_version",
                "schema_version {0} is not the supported version {1}".format(
                    ver, SCHEMA_VERSION
                ),
            )
        )

    # 2) required fields present + typed
    for name, typ in _REQUIRED_FIELDS:
        if name == "schema_version":
            continue  # handled above
        if name not in data:
            findings.append(
                Finding("WF-E010", name, "required field '{0}' is missing".format(name))
            )
            continue
        val = data[name]
        # bool is a subclass of int; guard so a bool never satisfies an int field, and vice versa.
        if typ is int and (not isinstance(val, int) or isinstance(val, bool)):
            findings.append(
                Finding(
                    "WF-E011",
                    name,
                    "field '{0}' must be an {1}".format(name, _t_name(typ)),
                )
            )
        elif typ is not int and not isinstance(val, typ):
            findings.append(
                Finding(
                    "WF-E011",
                    name,
                    "field '{0}' must be a {1}".format(name, _t_name(typ)),
                )
            )

    # 3) optional fields, when present, must be the right type
    for name, typ in _OPTIONAL_FIELDS:
        if name in data and not isinstance(data[name], typ):
            findings.append(
                Finding(
                    "WF-E012",
                    name,
                    "optional field '{0}' must be a {1}".format(name, _t_name(typ)),
                )
            )

    # 4) unknown top-level fields are rejected for a new workflow (closed schema)
    if isinstance(data, Mapping):
        for key in data.keys():
            if key not in _ALL_FIELD_NAMES:
                findings.append(
                    Finding("WF-E013", str(key), "unknown field '{0}'".format(key))
                )

    # If the basic shape is broken, deeper checks would be noise; return what we have.
    if any(f.code in ("WF-E010", "WF-E011") for f in findings):
        return ValidationResult(False, tuple(findings))

    # 5) id + enums
    if not is_valid_workflow_id(data.get("id")):
        findings.append(
            Finding("WF-E020", "id", "id must be lowercase-kebab (e.g. 'plan-review')")
        )
    _check_enum(findings, data, "intent", INTENTS, "WF-E021")
    _check_enum(findings, data, "risk", RISKS, "WF-E022")
    _check_enum(findings, data, "interaction", INTERACTION_MODES, "WF-E023")
    _check_enum(findings, data, "mutation_boundary", MUTATION_BOUNDARIES, "WF-E024")

    # 6) aliases (optional): each a valid workflow id, none equal to the id itself
    aliases = data.get("aliases")
    if isinstance(aliases, list):
        for i, a in enumerate(aliases):
            if not is_valid_workflow_id(a):
                findings.append(
                    Finding(
                        "WF-E025",
                        "aliases[{0}]".format(i),
                        "alias must be lowercase-kebab",
                    )
                )
            elif a == data.get("id"):
                findings.append(
                    Finding(
                        "WF-E026",
                        "aliases[{0}]".format(i),
                        "alias duplicates the workflow id",
                    )
                )

    # 7) host_capabilities (optional): each a known token
    caps = data.get("host_capabilities")
    if isinstance(caps, list):
        for i, c in enumerate(caps):
            if c not in HOST_CAPABILITIES:
                findings.append(
                    Finding(
                        "WF-E027",
                        "host_capabilities[{0}]".format(i),
                        "unknown host capability '{0}'".format(c),
                    )
                )

    # 8) permissions consistency
    _validate_permissions(findings, data)

    # 9) requirements
    req_ids = _validate_requirements(findings, data.get("requirements", []))

    # 10) steps (ids, dependency graph, evidence binding, forbidden terminal actions).
    # The returned step-id set is not needed here (validation is via appended findings); the
    # compiler (E-04) will re-derive ids from the same helper when it needs them.
    _validate_steps(
        findings, data.get("steps", []), req_ids, data.get("mutation_boundary")
    )

    # 11) validations (ids, one-to-one-ish binding to requirements + evidence)
    _validate_validations(findings, data.get("validations", []), req_ids)

    return ValidationResult(len(findings) == 0, tuple(findings))


def _check_enum(
    findings: List[Finding], data: Mapping, field: str, vocab: FrozenSet[str], code: str
) -> None:
    val = data.get(field)
    if val not in vocab:
        findings.append(
            Finding(
                code,
                field,
                "{0} '{1}' is not one of {2}".format(field, val, sorted(vocab)),
            )
        )


def _validate_permissions(findings: List[Finding], data: Mapping) -> None:
    """Permissions block (optional). Shape:

        permissions:
          allowed_paths: [ "agent_workflows/**", "tests/**" ]
          forbidden_paths: [ "**/local/**" ]
    A path cannot be both allowed and forbidden. A ``read-only`` risk or ``none`` mutation boundary
    must not declare any allowed write path (contradiction).
    """

    perms = data.get("permissions")
    if not isinstance(perms, Mapping):
        return
    allowed = perms.get("allowed_paths", [])
    forbidden = perms.get("forbidden_paths", [])
    if not isinstance(allowed, list):
        findings.append(
            Finding(
                "WF-E030", "permissions.allowed_paths", "allowed_paths must be a list"
            )
        )
        allowed = []
    if not isinstance(forbidden, list):
        findings.append(
            Finding(
                "WF-E031",
                "permissions.forbidden_paths",
                "forbidden_paths must be a list",
            )
        )
        forbidden = []
    overlap = sorted(
        set(a for a in allowed if isinstance(a, str))
        & set(f for f in forbidden if isinstance(f, str))
    )
    for path in overlap:
        findings.append(
            Finding(
                "WF-E032",
                "permissions",
                "path '{0}' is both allowed and forbidden".format(path),
            )
        )
    # read-only / none-mutation contradiction
    if (
        data.get("risk") == "read-only" or data.get("mutation_boundary") == "none"
    ) and any(isinstance(a, str) for a in allowed):
        findings.append(
            Finding(
                "WF-E033",
                "permissions.allowed_paths",
                "a read-only / mutation_boundary=none workflow must not declare allowed write paths",
            )
        )


def _validate_requirements(findings: List[Finding], reqs: Sequence[Any]) -> Set[str]:
    """Each requirement: {id: R-NN, text: str, evidence: [<kind>, ...]}. Returns the set of ids."""

    ids: Set[str] = set()
    for i, r in enumerate(reqs):
        where = "requirements[{0}]".format(i)
        if not isinstance(r, Mapping):
            findings.append(Finding("WF-E040", where, "requirement must be a mapping"))
            continue
        rid = r.get("id")
        if not is_valid_requirement_id(rid):
            findings.append(
                Finding("WF-E041", where + ".id", "requirement id must match 'R-NN'")
            )
        elif rid in ids:
            findings.append(
                Finding(
                    "WF-E042",
                    where + ".id",
                    "duplicate requirement id '{0}'".format(rid),
                )
            )
        else:
            ids.add(str(rid))
        if not isinstance(r.get("text"), str) or not r.get("text", "").strip():
            findings.append(
                Finding(
                    "WF-E043",
                    where + ".text",
                    "requirement text must be a nonempty string",
                )
            )
        ev = r.get("evidence", [])
        if not isinstance(ev, list) or not ev:
            findings.append(
                Finding(
                    "WF-E044",
                    where + ".evidence",
                    "requirement must bind >=1 evidence kind",
                )
            )
        else:
            for j, kind in enumerate(ev):
                if kind not in EVIDENCE_KINDS:
                    findings.append(
                        Finding(
                            "WF-E045",
                            where + ".evidence[{0}]".format(j),
                            "unknown evidence kind '{0}'".format(kind),
                        )
                    )
    return ids


def _validate_steps(
    findings: List[Finding],
    steps: Sequence[Any],
    req_ids: Set[str],
    mutation_boundary: Any,
) -> Set[str]:
    """Each step: {id: S-NN, action: str, satisfies: [R-NN,...], depends_on: [S-NN,...],
    evidence: [<kind>,...], stop_conditions?: [str], terminal_action?: str}. Validates ids,
    dependency edges (existing, non-self, acyclic), evidence binding, requirement references, and the
    forbidden-terminal-action guard. Returns the set of step ids."""

    ids: Set[str] = set()
    # First pass: collect ids so dependency checks can reference the full set.
    for i, s in enumerate(steps):
        if isinstance(s, Mapping) and is_valid_step_id(s.get("id")):
            sid = str(s.get("id"))
            if sid in ids:
                findings.append(
                    Finding(
                        "WF-E051",
                        "steps[{0}].id".format(i),
                        "duplicate step id '{0}'".format(sid),
                    )
                )
            else:
                ids.add(sid)

    dep_edges: Dict[str, List[str]] = {}
    for i, s in enumerate(steps):
        where = "steps[{0}]".format(i)
        if not isinstance(s, Mapping):
            findings.append(Finding("WF-E050", where, "step must be a mapping"))
            continue
        sid = s.get("id")
        if not is_valid_step_id(sid):
            findings.append(
                Finding("WF-E052", where + ".id", "step id must match 'S-NN'")
            )
        if not isinstance(s.get("action"), str) or not s.get("action", "").strip():
            findings.append(
                Finding(
                    "WF-E053",
                    where + ".action",
                    "step action must be a nonempty string",
                )
            )

        # satisfies -> existing requirement ids
        satisfies = s.get("satisfies", [])
        if not isinstance(satisfies, list) or not satisfies:
            findings.append(
                Finding(
                    "WF-E054",
                    where + ".satisfies",
                    "step must satisfy >=1 requirement id",
                )
            )
        else:
            for j, rid in enumerate(satisfies):
                if rid not in req_ids:
                    findings.append(
                        Finding(
                            "WF-E055",
                            where + ".satisfies[{0}]".format(j),
                            "unknown requirement id '{0}'".format(rid),
                        )
                    )

        # depends_on -> existing step ids, non-self
        deps = s.get("depends_on", [])
        if deps and not isinstance(deps, list):
            findings.append(
                Finding("WF-E056", where + ".depends_on", "depends_on must be a list")
            )
            deps = []
        clean_deps: List[str] = []
        for j, d in enumerate(deps or []):
            if d == sid:
                findings.append(
                    Finding(
                        "WF-E057",
                        where + ".depends_on[{0}]".format(j),
                        "step depends on itself",
                    )
                )
            elif not is_valid_step_id(d) or d not in ids:
                findings.append(
                    Finding(
                        "WF-E058",
                        where + ".depends_on[{0}]".format(j),
                        "unknown step dependency '{0}'".format(d),
                    )
                )
            else:
                clean_deps.append(d)
        if is_valid_step_id(sid):
            dep_edges[str(sid)] = clean_deps

        # evidence binding
        ev = s.get("evidence", [])
        if not isinstance(ev, list) or not ev:
            findings.append(
                Finding(
                    "WF-E059", where + ".evidence", "step must bind >=1 evidence kind"
                )
            )
        else:
            for j, kind in enumerate(ev):
                if kind not in EVIDENCE_KINDS:
                    findings.append(
                        Finding(
                            "WF-E05A",
                            where + ".evidence[{0}]".format(j),
                            "unknown evidence kind '{0}'".format(kind),
                        )
                    )

        # forbidden terminal action guard
        ta = s.get("terminal_action")
        if (
            isinstance(ta, str)
            and ta.strip().lower() in FORBIDDEN_STEP_TERMINAL_ACTIONS
        ):
            findings.append(
                Finding(
                    "WF-E05B",
                    where + ".terminal_action",
                    "step declares a runtime-owned terminal action '{0}' (forbidden in a workflow step)".format(
                        ta
                    ),
                )
            )

    # cycle detection over the cleaned dependency graph
    cycle = _find_cycle(dep_edges)
    if cycle is not None:
        findings.append(
            Finding(
                "WF-E05C",
                "steps",
                "dependency cycle detected: {0}".format(" -> ".join(cycle)),
            )
        )

    return ids


def _validate_validations(
    findings: List[Finding], vals: Sequence[Any], req_ids: Set[str]
) -> None:
    """Each validation: {id: V-NN?, verifies: R-NN, evidence: [<kind>,...]}. A validation must target
    an existing requirement and bind evidence. (The V-id grammar reuses the requirement digits.)"""

    seen_targets: Set[str] = set()
    for i, v in enumerate(vals):
        where = "validations[{0}]".format(i)
        if not isinstance(v, Mapping):
            findings.append(Finding("WF-E060", where, "validation must be a mapping"))
            continue
        target = v.get("verifies")
        if target not in req_ids:
            findings.append(
                Finding(
                    "WF-E061",
                    where + ".verifies",
                    "validation targets unknown requirement '{0}'".format(target),
                )
            )
        else:
            seen_targets.add(target)
        ev = v.get("evidence", [])
        if not isinstance(ev, list) or not ev:
            findings.append(
                Finding(
                    "WF-E062",
                    where + ".evidence",
                    "validation must bind >=1 evidence kind",
                )
            )
        else:
            for j, kind in enumerate(ev):
                if kind not in EVIDENCE_KINDS:
                    findings.append(
                        Finding(
                            "WF-E063",
                            where + ".evidence[{0}]".format(j),
                            "unknown evidence kind '{0}'".format(kind),
                        )
                    )
    # every requirement must be verified by at least one validation
    for rid in sorted(req_ids - seen_targets):
        findings.append(
            Finding(
                "WF-E064",
                "validations",
                "requirement '{0}' has no validation".format(rid),
            )
        )


def _find_cycle(edges: Mapping[str, Sequence[str]]) -> Optional[List[str]]:
    """Return one cycle as an ordered node list (first node repeated at the end) or None. Deterministic
    (nodes and neighbors are visited in sorted order)."""

    WHITE, GREY, BLACK = 0, 1, 2
    color: Dict[str, int] = {n: WHITE for n in edges}
    stack: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        color[node] = GREY
        stack.append(node)
        for nxt in sorted(edges.get(node, ())):
            if nxt not in color:
                continue
            if color[nxt] == GREY:
                idx = stack.index(nxt)
                return stack[idx:] + [nxt]
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found is not None:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for start in sorted(edges):
        if color[start] == WHITE:
            found = visit(start)
            if found is not None:
                return found
    return None
