"""Canonical, single-source workspace LAYOUT MODEL (spec `kw5y2s`, Set `wslayout` Order 01).

This module is the one place that answers "what logical roots, record classes, state classes and
traversal exclusions does an AW workspace have?", and it emits that answer as deterministic JSON
plus a JSON Schema so NON-PYTHON tooling can read the hierarchy without re-implementing fragile
string heuristics (spec Sections 1.2, 4, 5).

ADDITIVE BY DESIGN. Order 01 creates this model and NOTHING consumes it yet: `artifact_types.py`,
`selectors.py`, `record_producers.py` and `project_schema.py` are refactored onto it by Orders 02
and 03. So every vocabulary here reproduces what those modules define TODAY, member for member,
which is what makes the later consolidation behavior-preserving rather than a silent redefinition.

THE VOCABULARY IS THE UNION of the two vocabularies that exist today (maintainer ruling
2026-09-01, spec Section 3.2): `artifact_types.ARTIFACT_TYPES` (the CLI type nouns) and
`record_producers.RecordClass` (the record routing classes). The model DOCUMENTS reality; it does
not redefine it. Nothing live is dropped, so `roadmaps` survives and `reviews`, `backlog` and
`other` are gained.

TWO CARVE-OUTS EXIST BECAUSE TWO CLASSES ARE NOT ORDINARY DIRECTORIES, and collapsing either one
into a plain `subpath` is a defect with a concrete failure mode:

* `records` is the records ROOT ITSELF (`_RECORD_CLASS_SUBPATHS["records"] == ""`). Modeling it as
  `subpath="records"` yields a nonsensical `records/records/` path; dropping the member breaks
  every existing `RecordClass.RECORDS` caller. It carries `is_root_alias=True` here (spec 3.2.1).
* `other` is a COMPUTED COMPLEMENT, not a directory: `selectors.record_dirs` derives it as
  everything under the records root that no other class owns, and `.aw/records/other/` does not
  exist. It carries `is_complement=True`. Giving it a literal `other` subpath would silently
  change traversal once Order 02 sources the sweep from here.

Stdlib-only. Python 3.9 is the floor (`pyproject.toml`, CI-enforced on 3.9 through 3.14), so this
module follows the universal house pattern of `from __future__ import annotations` plus `typing`
generics and avoids PEP 604 (`X | None`), which is the construct that genuinely fails on 3.9.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

# The layout document schema version. Bump only with a documented migration; the emitted schema
# pins it as an enum so a stale reader fails loudly instead of misparsing.
SCHEMA_VERSION = 1

# The FOUR logical roots (spec Section 4). Answers "which logical root", and is deliberately
# distinct from the SIX physical placement classes below; spec Section 5.1 item 4 forbids
# collapsing one into the other because they answer different questions.
LOGICAL_ROOTS: Dict[str, str] = {
    "system": ".aw/system",
    "config": ".aw/config",
    "state": ".aw/state",
    "records": ".aw/records",
}

# The SIX physical placement classes (`project_schema.RootClass`). Carried here so Order 03 can
# align that enum against one authority WITHOUT collapsing it to the four logical roots.
ROOT_CLASSES: Tuple[str, ...] = (
    "system",
    "config_project",
    "config_local",
    "state_durable",
    "state_runtime",
    "records",
)

# The record class whose subpath is empty because it denotes the records root itself. Exposed as a
# NAMED CONSTANT as well as a per-class flag so a consumer can special-case it without string
# literals (spec Section 3.2.1 permits either; this module provides both).
ROOT_ALIAS_RECORD_CLASS = "records"

# The CLI expansion token. NOT a record class and never one: `normalize_type("all")` returns it
# unchanged as an explicit special case before any alias lookup, and `expand_types` fans it out to
# every supported type. It is named here so Order 02 can keep that behavior while sourcing the
# vocabulary from this model; a silent loss of `all` would break every `aw <verb> all` invocation.
EXPANSION_TOKEN_ALL = "all"

# Durable state classes, RELATIVE TO THE DURABLE STATE ROOT (`.aw/state/durable`). `install` is a
# FILE (`install.json`, the install receipt), not a directory; that is the live value and Order 03
# must reproduce it, so it is recorded here verbatim rather than idealized to `install/`.
DURABLE_STATE_CLASSES: Dict[str, str] = {
    "install": "install.json",
    "history": "history",
    "actions": "actions",
    "migrations": "migrations",
    "routing_receipts": "routing_receipts",
}

# Runtime state classes, RELATIVE TO THE RUNTIME STATE ROOT (`.aw/state/runtime`).
RUNTIME_STATE_CLASSES: Dict[str, str] = {
    "transactions": "transactions",
    "locks": "locks",
    "staging": "staging",
    "backups": "backups",
    "cache": "cache",
    "tmp": "tmp",
}

# The state-root-relative prefixes used when EMITTING state classes, so a non-Python reader can
# join them onto the `state` logical root directly (spec Section 4.2 emits `durable/<class>`).
DURABLE_STATE_PREFIX = "durable"
RUNTIME_STATE_PREFIX = "runtime"

# Directories skipped during record traversal. PINNED to the current seven so consolidation is
# behavior-preserving: the spec's earlier draft also listed `node_modules`, `venv` and `.venv`, and
# adding them is a deliberate, separately validated behavior change, NOT a side effect of sourcing
# from this model (spec Section 3.4). Ordered (sorted) so the emitted document is deterministic;
# the ORDER is part of this contract, while membership is what consumers compare.
TRAVERSAL_EXCLUSIONS: Tuple[str, ...] = (
    ".git",
    ".system_generated",
    "__pycache__",
    "runs",
    "scratch",
    "temp",
    "tmp",
)


@dataclass(frozen=True)
class RecordClassDefinition:
    """One record class: where it lives, what its files look like, and how it is classified.

    `subpath` is relative to the records root and is EMPTY for the two carve-outs (`records`, the
    root alias, and `other`, the computed complement). Consult `is_root_alias` / `is_complement`
    before joining a path, never the emptiness of the string alone.
    """

    name: str
    subpath: str
    pattern: str
    description: str
    lifecycle_subdirs: Tuple[str, ...] = ()
    aliases: Tuple[str, ...] = ()
    # True for the nine types that carry a status lifecycle and are therefore directly resolvable
    # (`selectors.KNOWN_PRIMARY_TYPES`). False for `reviews` (a real tree with no lifecycle), for
    # the `other` complement, and for the `records` root alias.
    is_primary: bool = True
    # True ONLY for `records`: the records root itself, empty subpath (spec Section 3.2.1).
    is_root_alias: bool = False
    # True ONLY for `other`: computed as the complement of every owned directory, no directory of
    # its own (`selectors.record_dirs`).
    is_complement: bool = False


def _default_record_classes() -> Tuple[RecordClassDefinition, ...]:
    """The canonical record classes, in canonical order.

    ORDER IS LOAD-BEARING: dropping `reviews` and `records` from this sequence reproduces
    `artifact_types.ARTIFACT_TYPES` in its exact live order, which `expand_types` and the CLI's
    "valid types: ..." error message both depend on.
    """
    return (
        RecordClassDefinition(
            name="plans",
            subpath="plans",
            pattern="*.ipd.md",
            description="Implementation Plan Documents (IPDs)",
            lifecycle_subdirs=(
                "pending",
                "executed",
                "superseded",
                "not-executed",
                "reusable",
            ),
            aliases=("plan",),
        ),
        RecordClassDefinition(
            name="specs",
            subpath="specs",
            pattern="*.spec.md",
            description="Architectural specifications and proposals",
            aliases=("spec",),
        ),
        RecordClassDefinition(
            name="prompts",
            subpath="prompts",
            pattern="*.md",
            description="Handoff prompts and session prompts",
            lifecycle_subdirs=(
                "pending",
                "executed",
                "superseded",
                "not-executed",
                "reusable",
            ),
            aliases=("prompt",),
        ),
        RecordClassDefinition(
            name="research",
            subpath="research",
            pattern="*.md",
            description="Durable research reports and investigations",
            # Research keeps its RICHER `.<model>.<kind>.md` convention by explicit exception in
            # the naming-grammar spec, so a single type-suffix glob would not describe it; `*.md`
            # is the honest pattern here.
            aliases=("research",),
        ),
        RecordClassDefinition(
            name="backlog",
            subpath="backlog",
            pattern="*.backlog.md",
            description="Committed backlog items",
            lifecycle_subdirs=("open", "graduated", "blocked", "parked", "done"),
            aliases=("backlog",),
        ),
        RecordClassDefinition(
            name="walkthroughs",
            subpath="walkthroughs",
            pattern="*.walkthrough.md",
            description="Narrative walkthrough and verification logs",
            aliases=("walkthrough",),
        ),
        RecordClassDefinition(
            name="roadmaps",
            subpath="roadmaps",
            pattern="*.roadmap.md",
            description="Roadmap documents",
            aliases=("roadmap",),
        ),
        RecordClassDefinition(
            name="comms",
            subpath="comms",
            pattern="*.md",
            description="Inter-agent inbox/outbox communications",
            aliases=("comm",),
        ),
        RecordClassDefinition(
            name="releases",
            subpath="releases",
            pattern="*.release.md",
            description="Release records and release gate declarations",
            aliases=("release",),
        ),
        RecordClassDefinition(
            name="reviews",
            subpath="reviews",
            pattern="*.review.md",
            description="Plan review findings and gate records",
            aliases=("review",),
            # A real tree with NO status lifecycle, so it cannot join the primary types without
            # making `aw set` accept it; it is nonetheless owned, which is what keeps the `other`
            # complement from swallowing `.aw/records/reviews/` and re-opening the measured id6
            # collision that fix `d802e917` closed.
            is_primary=False,
        ),
        RecordClassDefinition(
            name="other",
            subpath="",
            pattern="*.md",
            description="Unclassified records and general documentation (computed complement of the owned trees; no directory of its own)",
            aliases=("other", "others", "misc"),
            is_primary=False,
            is_complement=True,
        ),
        RecordClassDefinition(
            name=ROOT_ALIAS_RECORD_CLASS,
            subpath="",
            pattern="*.md",
            description="The records root itself (carve-out; NOT a child directory)",
            is_primary=False,
            is_root_alias=True,
        ),
    )


# Legacy `.agents/` READ-ONLY subpath overrides. The legacy tree kept its `docs/` nesting, so this
# map is DECOUPLED from the final subpaths above; only the three doc-family classes differ, and a
# net-new class correctly inherits its final subpath by absence. Order 03 must keep migration reads
# working, so the model cannot assume one subpath per class.
LEGACY_RECORD_SUBPATH_OVERRIDES: Dict[str, str] = {
    "specs": "docs/specs",
    "research": "docs/research",
    "walkthroughs": "docs/walkthroughs",
}


@dataclass(frozen=True)
class LayoutModel:
    """The whole workspace layout: roots, record classes, state classes, traversal exclusions."""

    schema_version: int = SCHEMA_VERSION
    logical_roots: Mapping[str, str] = field(
        default_factory=lambda: dict(LOGICAL_ROOTS)
    )
    record_classes: Mapping[str, RecordClassDefinition] = field(
        default_factory=lambda: {rc.name: rc for rc in _default_record_classes()}
    )
    durable_state_classes: Mapping[str, str] = field(
        default_factory=lambda: dict(DURABLE_STATE_CLASSES)
    )
    runtime_state_classes: Mapping[str, str] = field(
        default_factory=lambda: dict(RUNTIME_STATE_CLASSES)
    )
    traversal_exclusions: Tuple[str, ...] = TRAVERSAL_EXCLUSIONS
    root_classes: Tuple[str, ...] = ROOT_CLASSES
    legacy_record_subpath_overrides: Mapping[str, str] = field(
        default_factory=lambda: dict(LEGACY_RECORD_SUBPATH_OVERRIDES)
    )

    # ---- derived vocabularies (what Orders 02 and 03 consume) ----

    def artifact_types(self, *, include_reviews: bool = True) -> Tuple[str, ...]:
        """The CLI TYPE nouns, in canonical order.

        `include_reviews=False` reproduces today's `artifact_types.ARTIFACT_TYPES` exactly; the
        default includes `reviews`, which the union ruling makes an accepted type noun (net-new
        behavior Order 02 owns and must test).
        """
        return tuple(
            name
            for name, rc in self.record_classes.items()
            if not rc.is_root_alias and (include_reviews or name != "reviews")
        )

    def alias_map(self) -> Dict[str, str]:
        """alias -> canonical class name, including the identity entries the live map carries."""
        out: Dict[str, str] = {}
        for name, rc in self.record_classes.items():
            if rc.is_root_alias:
                continue
            for alias in rc.aliases:
                out[alias] = name
        return out

    def primary_types(self) -> Tuple[str, ...]:
        """The types with a status lifecycle (`selectors.KNOWN_PRIMARY_TYPES`), canonical order."""
        return tuple(
            name
            for name, rc in self.record_classes.items()
            if rc.is_primary and not rc.is_root_alias and not rc.is_complement
        )

    def non_primary_record_dirs(self) -> Tuple[str, ...]:
        """Owned trees that are NOT primary (`selectors.NON_PRIMARY_RECORD_DIRS`).

        A real directory with no status lifecycle. It MUST stay out of the `other` sweep: when
        `reviews` was in neither the primary types nor the exclusions, a bare id6 matched twice and
        `aw set approved <id6>` refused for every reviewed plan.
        """
        return tuple(
            name
            for name, rc in self.record_classes.items()
            if not rc.is_primary
            and not rc.is_root_alias
            and not rc.is_complement
            and rc.subpath
        )

    def other_sweep_skip_dirs(self) -> Tuple[str, ...]:
        """Every directory the `other` complement must skip, sorted.

        The DERIVED union is what actually gates the sweep, so it is exposed here rather than left
        for a consumer to recompute (or to hardcode) from the three inputs.
        """
        return tuple(
            sorted(
                set(self.primary_types())
                | set(self.non_primary_record_dirs())
                | set(self.traversal_exclusions)
            )
        )

    def record_subpaths(self) -> Dict[str, str]:
        """class -> final records-root-relative subpath, preserving the `records` empty carve-out."""
        return {
            name: rc.subpath
            for name, rc in self.record_classes.items()
            if not rc.is_complement
        }

    def legacy_record_subpaths(self) -> Dict[str, str]:
        """class -> legacy `.agents/` subpath (final subpath unless overridden)."""
        out = self.record_subpaths()
        for name, legacy in self.legacy_record_subpath_overrides.items():
            if name in out:
                out[name] = legacy
        return out

    # ---- lookups ----

    def is_known_type(self, token: Optional[str]) -> bool:
        """True for a canonical class, a known alias, or the `all` expansion token.

        Mirrors `artifact_types.is_type_token`: falsy input (None, "") is False, never an error, and
        the `records` ROOT ALIAS is False because it is a record class, not a CLI type noun (use
        `resolve_class_name` for the routing question).
        """
        if not token:
            return False
        if token == EXPANSION_TOKEN_ALL:
            return True
        rc = self.record_classes.get(token)
        if rc is not None:
            return not rc.is_root_alias
        return token in self.alias_map()

    def normalize_type(self, token: Optional[str]) -> str:
        """Canonical class name for `token`; `all` passes through unchanged.

        RAISES `ValueError` for an unknown token, listing the valid set, which is exactly what
        `artifact_types.normalize_type` does today (including for `""` and `None`). This is
        deliberately NOT the degrade-to-empty convention `selectors.record_dirs` uses: that helper
        documents "returns [] for an unknown/unresolvable type rather than raising" and keeps its
        own contract. The two live helpers DISAGREE, and unifying them silently would be a behavior
        change, so each keeps its own semantics.
        """
        if token == EXPANSION_TOKEN_ALL:
            return EXPANSION_TOKEN_ALL
        if token:
            rc = self.record_classes.get(token)
            if rc is not None and not rc.is_root_alias:
                return token
            alias_target = self.alias_map().get(token)
            if alias_target is not None:
                return alias_target
        valid = ", ".join(self.artifact_types(include_reviews=False))
        raise ValueError(
            "unknown artifact type {0!r}; valid types: {1}, {2}".format(
                token, valid, EXPANSION_TOKEN_ALL
            )
        )

    def expand_type(self, token: str, supported: Tuple[str, ...]) -> List[str]:
        """`all` -> every `supported` type in canonical order; otherwise the single type."""
        norm = self.normalize_type(token)
        if norm == EXPANSION_TOKEN_ALL:
            return [t for t in self.artifact_types() if t in supported]
        if norm not in supported:
            raise ValueError(
                "type {0!r} is not supported here; supported: {1}".format(
                    norm, ", ".join(supported)
                )
            )
        return [norm]

    def resolve_class_name(self, record_type: str) -> str:
        """Canonical RECORD CLASS name for `record_type`, including the `records` root alias.

        WIDER THAN `normalize_type` BY DESIGN, and the difference is load-bearing. `normalize_type`
        answers the CLI question ("is this a valid type noun?") and must therefore REJECT `records`,
        because `records` is a record class but has never been an `ARTIFACT_TYPES` member and
        accepting it would silently widen the CLI surface. This method answers the RECORD ROUTING
        question, where `RecordClass.RECORDS` is a legitimate member every existing caller uses.
        Raises `ValueError` for an unknown token and for the `all` expansion token.
        """
        if record_type == ROOT_ALIAS_RECORD_CLASS:
            return ROOT_ALIAS_RECORD_CLASS
        norm = self.normalize_type(record_type)
        if norm == EXPANSION_TOKEN_ALL:
            raise ValueError(
                "{0!r} is an expansion token, not a record class".format(
                    EXPANSION_TOKEN_ALL
                )
            )
        return norm

    def get_record_class(self, record_type: str) -> RecordClassDefinition:
        """The definition for a class name, alias, or the `records` root alias."""
        return self.record_classes[self.resolve_class_name(record_type)]

    def get_record_subpath(self, record_type: str) -> str:
        """Records-root-relative subpath for a class or alias. Raises `ValueError` if unknown.

        Returns "" for BOTH carve-outs, which is why a caller joining a path must check
        `is_root_alias` / `is_complement` rather than assuming a nonempty subpath.
        """
        return self.record_classes[self.resolve_class_name(record_type)].subpath

    # ---- serialization ----

    def to_dict(self, framework_version: str) -> Dict[str, Any]:
        """The layout document (spec Section 4.2), built in a deterministic key order.

        The `records` ROOT ALIAS is deliberately OMITTED from the emitted `record_classes`: the
        spec's table excludes it by design, and emitting a class whose subpath is the records root
        is exactly the `records/records/` confusion the carve-out exists to prevent. It stays
        available to Python consumers through `record_classes` / `record_subpaths()`.
        """
        record_classes: Dict[str, Any] = {}
        for name, rc in self.record_classes.items():
            if rc.is_root_alias:
                continue
            entry: Dict[str, Any] = {
                "subpath": rc.subpath,
                "pattern": rc.pattern,
                "description": rc.description,
            }
            if rc.lifecycle_subdirs:
                entry["lifecycle_subdirs"] = list(rc.lifecycle_subdirs)
            entry["aliases"] = list(rc.aliases)
            record_classes[name] = entry

        return {
            "schema_version": self.schema_version,
            "framework_version": framework_version,
            "logical_roots": dict(self.logical_roots),
            "record_classes": record_classes,
            "state_classes": {
                "durable": {
                    name: "{0}/{1}".format(DURABLE_STATE_PREFIX, sub)
                    for name, sub in self.durable_state_classes.items()
                },
                "runtime": {
                    name: "{0}/{1}".format(RUNTIME_STATE_PREFIX, sub)
                    for name, sub in self.runtime_state_classes.items()
                },
            },
            "traversal_exclusions": list(self.traversal_exclusions),
        }

    def to_json(self, framework_version: str) -> str:
        """Deterministic JSON for the layout document, newline-terminated.

        Byte-stable for a given model + version (fixed key order, no set iteration), so a
        re-install at the same version is a no-op rather than a rewrite.
        """
        return (
            json.dumps(self.to_dict(framework_version), indent=2, ensure_ascii=False)
            + "\n"
        )

    def to_schema(self) -> Dict[str, Any]:
        """The JSON Schema validating the emitted layout document (spec Section 4.1)."""
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "AgentWorkflowsLayout",
            "type": "object",
            "required": [
                "schema_version",
                "framework_version",
                "logical_roots",
                "record_classes",
                "state_classes",
                "traversal_exclusions",
            ],
            "properties": {
                "schema_version": {"type": "integer", "enum": [self.schema_version]},
                "framework_version": {"type": "string"},
                "logical_roots": {
                    "type": "object",
                    "required": sorted(self.logical_roots),
                    "additionalProperties": {"type": "string"},
                },
                "record_classes": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "required": ["subpath", "pattern", "description"],
                        "properties": {
                            "subpath": {"type": "string"},
                            "pattern": {"type": "string"},
                            "description": {"type": "string"},
                            "lifecycle_subdirs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "aliases": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "state_classes": {
                    "type": "object",
                    "required": ["durable", "runtime"],
                    "properties": {
                        "durable": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                        "runtime": {
                            "type": "object",
                            "additionalProperties": {"type": "string"},
                        },
                    },
                },
                "traversal_exclusions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": False,
        }

    def to_schema_json(self) -> str:
        """Deterministic JSON text for `to_schema()`, newline-terminated."""
        return json.dumps(self.to_schema(), indent=2, ensure_ascii=False) + "\n"


def build_default_layout() -> LayoutModel:
    """The canonical layout model for this framework version."""
    return LayoutModel()
