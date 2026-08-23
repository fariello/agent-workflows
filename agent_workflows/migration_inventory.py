"""Migration disposition inventory + shared assess/advise harness + plan-review collapse.

awoptimize Order 14 (`h1d5aa`). This module is the FIRST migration stage of the workflow-family
migration. It does three things, all pure/deterministic and stdlib-only (D138), never touching a
runtime YAML parser (D139):

* E-01 -- a machine-validated DISPOSITION INVENTORY: exactly ONE reviewed disposition row for every
  manifest command, every assess lens, every advise persona, and the non-invokable conformance
  package. A completeness tool PROVES zero manifest rows/lenses/personas/conformance files are
  silently omitted, that every disposition has a valid canonical target, and that aliases are
  distinguishable from independent workflows.

* E-02 -- the SHARED assess+advise harness migration: `assess` (+ all lenses) and `advise` (+ all
  personas) become ONE canonical harness each, with typed lens/persona modules and generated catalog
  rows. Every lens resolves through the one assess harness; every persona through the one advise
  harness. A schema/parity check REJECTS a local lifecycle/evidence fork (a lens/persona may not
  redefine the harness lifecycle or evidence contract). The `assess-all` rollup requires an explicit
  scope/cost confirmation and de-duplicates its member set.

* E-03 -- the PLAN-REVIEW COLLAPSE: `plan-review` and `plan-review-long` become ONE modular canonical
  package that compiles BOTH the bounded step packets ("long" orchestrator view) AND a portable
  single-file view, with semantic-digest parity between them, keeping both command names as aliases.
  A mutation of EITHER generated view is detected as drift.

It BUILDS ON the existing system and does not fork it:
  * Order 01 compiler (`workflow_compiler.compile_workflow`) produces the projections;
  * Order 01 profile (`workflow_profile.semantic_digest`) is the ONE semantic-digest scheme;
  * Order 11 host adapters remain the generator surface for skills/adapters;
  * the manifest (`.aw/system/workflows/index.md`) is parsed via `engine.parse_manifest` and is the
    authority for the inventory -- no row is invented and none is dropped.

Scope fence (Order 14): it does NOT migrate the complex orchestrated workflows (Order 15), the
compact workflows / shims / promotion gates (Order 16), or delete legacy shims (Order 17). It reads
the manifest and workflow bodies; it never mutates them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

from agent_workflows import engine
from agent_workflows import workflow_compiler as _compiler
from agent_workflows import workflow_profile as _profile
from agent_workflows.engine import Workflow

# ==================================================================================================
# E-01: disposition vocabularies
# ==================================================================================================

# Execution mode: how the disposition target is intended to run once migrated.
EXECUTION_MODES: FrozenSet[str] = frozenset(
    (
        "deterministic",  # a deterministic runtime/command (no model reasoning needed)
        "guided",  # a guided/interactive walkthrough
        "orchestrated",  # a multi-context orchestration (release-review, assess-all, ...)
        "shared-harness",  # resolves through one shared harness + a typed lens/persona
        "non-invokable",  # not a runnable command (e.g. the conformance package)
    )
)

# Interaction mode: mirrors the Order-01 schema vocabulary so the inventory speaks one language.
INTERACTIONS: FrozenSet[str] = frozenset(("noninteractive", "optional", "interactive"))

# Risk class: mirrors the Order-01 schema RISKS vocabulary.
RISKS: FrozenSet[str] = frozenset(("read-only", "low", "medium", "high", "destructive"))

# Skill decision: whether the migrated target gets a discoverable skill (Order-11 policy input).
SKILL_DECISIONS: FrozenSet[str] = frozenset(
    (
        "skill",  # gets a discoverable Agent Skill package
        "thin-entry",  # a thin explicit skill entry point
        "no-skill",  # deterministic command; no extra skill
        "n/a",  # not applicable (non-invokable)
    )
)

# Orchestration decision: whether the target coordinates multiple contexts.
ORCHESTRATION_DECISIONS: FrozenSet[str] = frozenset(
    (
        "orchestrator",  # owns/drives a multi-context run
        "bounded-runtime",  # a bounded runtime (loads one packet at a time)
        "single-context",  # runs in one context
        "conditional",  # orchestrates only under a risk/scope condition
        "n/a",
    )
)

# Evidence level: how strong the completion evidence must be (maps onto the Order-01 evidence kinds).
EVIDENCE_LEVELS: FrozenSet[str] = frozenset(
    ("none", "inspection", "artifact", "command", "full")
)

# Migration owner: which Order OWNS migrating a given disposition. Order 14 owns the shared families +
# plan-review + the inventory itself; 15/16/17 own the rest. Making the owner an explicit column is
# what lets the completeness tool prove Order 14 did not silently claim rows it must defer.
MIGRATION_OWNERS: FrozenSet[str] = frozenset(
    (
        "order-14",  # this Order (shared families, plan-review, the inventory)
        "order-15",  # complex orchestrated workflows
        "order-16",  # compact workflows + shims + promotion gates
        "order-17",  # legacy shim removal
    )
)

# The catalog-row prefixes and standalone exceptions, taken from the engine so the inventory and the
# installer agree on what a "lens/persona catalog row" is versus an independent workflow.
LENS_PREFIX = "assess-"
PERSONA_PREFIX = "advise-"

# The non-invokable conformance package (a family with no manifest command row). Its entry file is the
# operator protocol; it is dispositioned exactly once, as non-invokable.
CONFORMANCE_ENTRY_RELPATH = "conformance/operator-protocol.md"
CONFORMANCE_TARGET = "conformance"


class InventoryError(ValueError):
    """Raised when the disposition inventory is internally inconsistent (fail closed)."""


@dataclass(frozen=True)
class Disposition:
    """One reviewed disposition row for a single migration subject.

    A subject is a manifest command, an assess lens, an advise persona, or the conformance package.
    ``canonical_target`` names the ONE canonical package the subject migrates onto; an ``alias`` row
    points its canonical target at another subject's target (which is how an alias is distinguished
    from an independent workflow: ``is_alias`` is True and ``canonical_target`` is not the subject's
    own id).
    """

    subject: str  # the manifest command / lens id / persona id / conformance id
    kind: str  # "command" | "lens" | "persona" | "conformance"
    family: str  # the family key (from the plan's disposition-by-family table)
    canonical_package: str  # the canonical package the subject resolves to
    execution_mode: str
    interaction: str
    risk: str
    skill_decision: str
    orchestration_decision: str
    evidence_level: str
    aliases: Tuple[str, ...] = ()
    migration_owner: str = "order-16"
    is_alias: bool = (
        False  # True iff this subject is an alias of another canonical package
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "family": self.family,
            "canonical_package": self.canonical_package,
            "execution_mode": self.execution_mode,
            "interaction": self.interaction,
            "risk": self.risk,
            "skill_decision": self.skill_decision,
            "orchestration_decision": self.orchestration_decision,
            "evidence_level": self.evidence_level,
            "aliases": list(self.aliases),
            "migration_owner": self.migration_owner,
            "is_alias": self.is_alias,
        }

    def validate(self) -> List[str]:
        """Return a list of vocabulary violations for this row (empty = valid)."""

        problems: List[str] = []
        if not self.subject:
            problems.append("empty subject")
        if self.kind not in ("command", "lens", "persona", "conformance"):
            problems.append("bad kind '{0}'".format(self.kind))
        if not self.canonical_package:
            problems.append("empty canonical_package")
        if self.execution_mode not in EXECUTION_MODES:
            problems.append("bad execution_mode '{0}'".format(self.execution_mode))
        if self.interaction not in INTERACTIONS:
            problems.append("bad interaction '{0}'".format(self.interaction))
        if self.risk not in RISKS:
            problems.append("bad risk '{0}'".format(self.risk))
        if self.skill_decision not in SKILL_DECISIONS:
            problems.append("bad skill_decision '{0}'".format(self.skill_decision))
        if self.orchestration_decision not in ORCHESTRATION_DECISIONS:
            problems.append(
                "bad orchestration_decision '{0}'".format(self.orchestration_decision)
            )
        if self.evidence_level not in EVIDENCE_LEVELS:
            problems.append("bad evidence_level '{0}'".format(self.evidence_level))
        if self.migration_owner not in MIGRATION_OWNERS:
            problems.append("bad migration_owner '{0}'".format(self.migration_owner))
        if self.is_alias and self.canonical_package == self.subject:
            problems.append("alias must not target its own subject id")
        return problems


# --------------------------------------------------------------------------------------------------
# The FROZEN disposition table for the families this Order owns + the family assignment for the rest.
# --------------------------------------------------------------------------------------------------

# Family assignment for each COMMAND row, from the plan's "Initial disposition by family" table. This
# is the reviewed grouping the Order freezes. Every non-catalog manifest command must appear here so
# the completeness tool can prove no command is unassigned.
_COMMAND_FAMILY: Dict[str, str] = {
    "release-review": "release review modes",
    "release-review-plan": "release review modes",
    "plan-review": "plan review aliases",
    "plan-review-long": "plan review aliases",
    "verify-execution": "verification/lifecycle",
    "ipd-lifecycle": "verification/lifecycle",
    "verify": "list-workflows/verify",
    "list-workflows": "list-workflows/verify",
    "assess": "assess + lenses",
    "assess-all": "assess + lenses",
    "advise": "advise + personas",
    "setup-repo": "setup-repo",
    "getting-started": "whatnext/handoff/research/spec/release-notes",
    "whatnext": "whatnext/handoff/research/spec/release-notes",
    "handoff": "whatnext/handoff/research/spec/release-notes",
    "research": "whatnext/handoff/research/spec/release-notes",
    "spec": "whatnext/handoff/research/spec/release-notes",
    "release-notes": "whatnext/handoff/research/spec/release-notes",
    "incident": "incident/migrate/benchmark",
    "migrate": "incident/migrate/benchmark",
    "benchmark": "incident/migrate/benchmark",
    "scaffold": "scaffold",
}

# Per-family disposition defaults (execution mode, skill, orchestration, evidence) reflecting the
# plan's recommended-implementation column. The completeness tool applies these; a command with no
# family entry is an omission (a hard failure), never a silent default.
_FAMILY_DEFAULTS: Dict[str, Dict[str, str]] = {
    "release review modes": {
        "execution_mode": "orchestrated",
        "skill_decision": "thin-entry",
        "orchestration_decision": "orchestrator",
        "evidence_level": "full",
        "risk": "high",
        "interaction": "interactive",
        "migration_owner": "order-15",
    },
    "plan review aliases": {
        "execution_mode": "shared-harness",
        "skill_decision": "skill",
        "orchestration_decision": "bounded-runtime",
        "evidence_level": "inspection",
        "risk": "low",
        "interaction": "interactive",
        "migration_owner": "order-14",
    },
    "verification/lifecycle": {
        "execution_mode": "deterministic",
        "skill_decision": "thin-entry",
        "orchestration_decision": "orchestrator",
        "evidence_level": "full",
        "risk": "medium",
        "interaction": "optional",
        "migration_owner": "order-15",
    },
    "assess + lenses": {
        "execution_mode": "shared-harness",
        "skill_decision": "skill",
        "orchestration_decision": "single-context",
        "evidence_level": "artifact",
        "risk": "read-only",
        "interaction": "optional",
        "migration_owner": "order-14",
    },
    "advise + personas": {
        "execution_mode": "shared-harness",
        "skill_decision": "skill",
        "orchestration_decision": "single-context",
        "evidence_level": "inspection",
        "risk": "read-only",
        "interaction": "interactive",
        "migration_owner": "order-14",
    },
    "setup-repo": {
        "execution_mode": "guided",
        "skill_decision": "thin-entry",
        "orchestration_decision": "orchestrator",
        "evidence_level": "artifact",
        "risk": "medium",
        "interaction": "interactive",
        "migration_owner": "order-15",
    },
    "whatnext/handoff/research/spec/release-notes": {
        "execution_mode": "guided",
        "skill_decision": "no-skill",
        "orchestration_decision": "single-context",
        "evidence_level": "inspection",
        "risk": "low",
        "interaction": "optional",
        "migration_owner": "order-16",
    },
    "list-workflows/verify": {
        "execution_mode": "deterministic",
        "skill_decision": "no-skill",
        "orchestration_decision": "single-context",
        "evidence_level": "command",
        "risk": "read-only",
        "interaction": "optional",
        "migration_owner": "order-16",
    },
    "incident/migrate/benchmark": {
        "execution_mode": "guided",
        "skill_decision": "skill",
        "orchestration_decision": "conditional",
        "evidence_level": "artifact",
        "risk": "medium",
        "interaction": "interactive",
        "migration_owner": "order-16",
    },
    "scaffold": {
        "execution_mode": "deterministic",
        "skill_decision": "thin-entry",
        "orchestration_decision": "single-context",
        "evidence_level": "artifact",
        "risk": "low",
        "interaction": "interactive",
        "migration_owner": "order-16",
    },
}

# The A/B alias pair this Order collapses: `plan-review-long` is an alias of `plan-review`.
_PLAN_REVIEW_CANONICAL = "plan-review"
_PLAN_REVIEW_ALIAS = "plan-review-long"

# `release-review-plan` is a mode/alias of `release-review` (Order 15 owns it, but the inventory must
# still record it as an alias so it is distinguishable from an independent workflow).
_RELEASE_REVIEW_CANONICAL = "release-review"
_RELEASE_REVIEW_ALIAS = "release-review-plan"


def _command_disposition(workflow: Workflow) -> Disposition:
    """Build the reviewed disposition for one manifest COMMAND row (fail closed on an unassigned
    command so no row is silently defaulted)."""

    cmd = workflow.command
    family = _COMMAND_FAMILY.get(cmd)
    if family is None:
        raise InventoryError(
            "manifest command '{0}' has no reviewed family assignment (silent omission)".format(
                cmd
            )
        )
    defaults = _FAMILY_DEFAULTS[family]

    is_alias = cmd in (_PLAN_REVIEW_ALIAS, _RELEASE_REVIEW_ALIAS)
    if cmd == _PLAN_REVIEW_ALIAS:
        canonical = _PLAN_REVIEW_CANONICAL
        aliases: Tuple[str, ...] = ()
    elif cmd == _RELEASE_REVIEW_ALIAS:
        canonical = _RELEASE_REVIEW_CANONICAL
        aliases = ()
    elif cmd == _PLAN_REVIEW_CANONICAL:
        canonical = cmd
        aliases = (_PLAN_REVIEW_ALIAS,)
    elif cmd == _RELEASE_REVIEW_CANONICAL:
        canonical = cmd
        aliases = (_RELEASE_REVIEW_ALIAS,)
    else:
        canonical = cmd
        aliases = ()

    return Disposition(
        subject=cmd,
        kind="command",
        family=family,
        canonical_package=canonical,
        execution_mode=defaults["execution_mode"],
        interaction=defaults["interaction"],
        risk=defaults["risk"],
        skill_decision=defaults["skill_decision"],
        orchestration_decision=defaults["orchestration_decision"],
        evidence_level=defaults["evidence_level"],
        aliases=aliases,
        migration_owner=defaults["migration_owner"],
        is_alias=is_alias,
    )


def _catalog_disposition(workflow: Workflow) -> Disposition:
    """Build the reviewed disposition for one assess-lens / advise-persona CATALOG row.

    Every lens resolves to the ONE `assess` harness; every persona to the ONE `advise` harness. That
    shared canonical target is what proves the family did not fork into N separate workflows.
    """

    cmd = workflow.command
    if cmd.startswith(LENS_PREFIX):
        return Disposition(
            subject=cmd,
            kind="lens",
            family="assess + lenses",
            canonical_package="assess",
            execution_mode="shared-harness",
            interaction="optional",
            risk="read-only",
            skill_decision="skill",
            orchestration_decision="single-context",
            evidence_level="artifact",
            aliases=(),
            migration_owner="order-14",
            is_alias=False,
        )
    if cmd.startswith(PERSONA_PREFIX):
        return Disposition(
            subject=cmd,
            kind="persona",
            family="advise + personas",
            canonical_package="advise",
            execution_mode="shared-harness",
            interaction="interactive",
            risk="read-only",
            skill_decision="skill",
            orchestration_decision="single-context",
            evidence_level="inspection",
            aliases=(),
            migration_owner="order-14",
            is_alias=False,
        )
    raise InventoryError("row '{0}' is not a lens/persona catalog row".format(cmd))


def _conformance_disposition() -> Disposition:
    """The single disposition for the non-invokable conformance package."""

    return Disposition(
        subject=CONFORMANCE_TARGET,
        kind="conformance",
        family="conformance (non-invokable)",
        canonical_package=CONFORMANCE_TARGET,
        execution_mode="non-invokable",
        interaction="noninteractive",
        risk="read-only",
        skill_decision="n/a",
        orchestration_decision="n/a",
        evidence_level="none",
        aliases=(),
        migration_owner="order-16",
        is_alias=False,
    )


# ==================================================================================================
# E-01: the inventory + the completeness tool
# ==================================================================================================


@dataclass
class InventoryResult:
    """The outcome of building + checking the disposition inventory.

    ``dispositions`` is keyed by subject id; ``findings`` is empty iff the inventory is complete and
    valid. Every finding names the omission/duplication/invalid-target it detected (falsifiable).
    """

    dispositions: Dict[str, Disposition]
    findings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "count": len(self.dispositions),
            "dispositions": {
                s: d.to_dict() for s, d in sorted(self.dispositions.items())
            },
            "findings": list(self.findings),
        }


def _workflows_root(source_root: Any) -> Path:
    return Path(source_root)


def enumerate_subjects(workflows: Sequence[Workflow]) -> Dict[str, List[Workflow]]:
    """Split parsed manifest rows into commands / lenses / personas, using the engine's own
    catalog-row classifier so the split matches the installer's."""

    commands: List[Workflow] = []
    lenses: List[Workflow] = []
    personas: List[Workflow] = []
    for w in workflows:
        if engine.is_concern_catalog_row(w):
            if w.command.startswith(LENS_PREFIX):
                lenses.append(w)
            elif w.command.startswith(PERSONA_PREFIX):
                personas.append(w)
        else:
            commands.append(w)
    return {"commands": commands, "lenses": lenses, "personas": personas}


def build_inventory(source_root: Any) -> InventoryResult:
    """Build the complete disposition inventory from the live manifest + the conformance package.

    Raises :class:`InventoryError` only for a programmer error (an unassigned command family); an
    invalid vocabulary value or a missing canonical target is a FINDING, not an exception, so the
    completeness tool reports every problem at once instead of aborting on the first.
    """

    root = _workflows_root(source_root)
    workflows = engine.parse_manifest(root)
    subjects = enumerate_subjects(workflows)

    dispositions: Dict[str, Disposition] = {}
    findings: List[str] = []

    def _add(d: Disposition) -> None:
        if d.subject in dispositions:
            findings.append("duplicate disposition for '{0}'".format(d.subject))
            return
        dispositions[d.subject] = d

    for w in subjects["commands"]:
        _add(_command_disposition(w))
    for w in subjects["lenses"]:
        _add(_catalog_disposition(w))
    for w in subjects["personas"]:
        _add(_catalog_disposition(w))
    _add(_conformance_disposition())

    findings.extend(check_completeness(dispositions, workflows, root))
    return InventoryResult(dispositions=dispositions, findings=findings)


def check_completeness(
    dispositions: Mapping[str, Disposition],
    workflows: Sequence[Workflow],
    source_root: Any,
) -> List[str]:
    """PROVE the inventory is complete + valid. Returns a list of findings (empty = complete).

    Falsifiable checks (each detects a specific omission/error):
      1. every manifest row (command + lens + persona) has EXACTLY ONE disposition;
      2. the conformance package has exactly one disposition;
      3. every disposition passes vocabulary validation;
      4. every disposition's canonical target is valid: an independent workflow targets its OWN id,
         and an alias targets another EXISTING subject's canonical package (aliases distinguishable);
      5. no disposition exists for a subject that is not a real manifest row / conformance file;
      6. Order 14 (this Order) may only own the families it is scoped to migrate.
    """

    findings: List[str] = []
    root = _workflows_root(source_root)

    manifest_subjects = {w.command for w in workflows}
    all_subjects = set(manifest_subjects) | {CONFORMANCE_TARGET}

    # 1+2) every manifest row + the conformance file dispositioned exactly once, none omitted.
    for subj in sorted(all_subjects):
        if subj not in dispositions:
            findings.append(
                "subject '{0}' has NO disposition (silent omission)".format(subj)
            )

    # 5) no disposition for a subject that is not a real manifest row / conformance file.
    for subj in sorted(dispositions):
        if subj not in all_subjects:
            findings.append(
                "disposition '{0}' does not correspond to any manifest row or conformance file".format(
                    subj
                )
            )

    # 3) vocabulary validity.
    for subj, d in sorted(dispositions.items()):
        for problem in d.validate():
            findings.append("disposition '{0}': {1}".format(subj, problem))

    # 4) canonical-target validity + alias distinguishability.
    for subj, d in sorted(dispositions.items()):
        if d.is_alias:
            if d.canonical_package == subj:
                findings.append(
                    "alias '{0}' targets its own id (not distinguishable from an independent workflow)".format(
                        subj
                    )
                )
            elif d.canonical_package not in dispositions:
                findings.append(
                    "alias '{0}' targets unknown canonical package '{1}'".format(
                        subj, d.canonical_package
                    )
                )
        else:
            # An independent workflow / lens / persona resolves to a canonical package that must
            # itself be a dispositioned subject (its own id, or the shared harness id for a lens/
            # persona).
            if d.canonical_package not in dispositions:
                findings.append(
                    "'{0}' resolves to unknown canonical package '{1}'".format(
                        subj, d.canonical_package
                    )
                )

    # Conformance entry file must actually exist (a non-invokable subject still needs a real target).
    conf_entry = root / CONFORMANCE_ENTRY_RELPATH
    if not conf_entry.is_file():
        findings.append(
            "conformance entry file missing: {0}".format(CONFORMANCE_ENTRY_RELPATH)
        )

    # 6) Order-14 ownership fence: this Order only migrates the shared families + plan-review here.
    order14_allowed_families = {
        "assess + lenses",
        "advise + personas",
        "plan review aliases",
    }
    for subj, d in sorted(dispositions.items()):
        if d.migration_owner == "order-14" and d.family not in order14_allowed_families:
            findings.append(
                "'{0}' claims migration_owner order-14 but family '{1}' is out of Order-14 scope".format(
                    subj, d.family
                )
            )

    return findings


# ==================================================================================================
# E-02: shared assess/advise harness (typed lens/persona modules + generated catalog rows)
# ==================================================================================================

# The harness lifecycle + evidence contract are OWNED by the harness, never by a lens/persona. A lens/
# persona that redeclares any of these keys is a fork and is rejected. This is the load-bearing
# no-fork invariant.
HARNESS_RESERVED_KEYS: FrozenSet[str] = frozenset(
    (
        "lifecycle",  # the harness step lifecycle
        "evidence",  # the harness evidence contract
        "risk",  # the harness risk class
        "mutation_boundary",  # the harness scope fence
        "interaction",  # the harness interaction mode
        "steps",  # the harness step set
        "validations",  # the harness validations
    )
)


class HarnessForkError(ValueError):
    """Raised when a lens/persona attempts to fork the shared harness lifecycle/evidence."""


@dataclass(frozen=True)
class LensModule:
    """A typed assess lens: it contributes ONLY concern-specific content (rubric focus, lead
    personas). It may NOT redefine the harness lifecycle or evidence contract."""

    concern: str  # e.g. "security"
    lens_body: str  # canonical body path (informational)
    rubric_focus: str
    lead_personas: Tuple[str, ...] = ()

    def contribution(self) -> Dict[str, Any]:
        return {
            "concern": self.concern,
            "lens_body": self.lens_body,
            "rubric_focus": self.rubric_focus,
            "lead_personas": list(self.lead_personas),
        }


@dataclass(frozen=True)
class PersonaModule:
    """A typed advise persona: it contributes ONLY the expert charter. It may NOT redefine the harness
    lifecycle or evidence contract."""

    persona: str  # e.g. "skeptic"
    persona_body: str  # canonical body path (informational)
    charter: str

    def contribution(self) -> Dict[str, Any]:
        return {
            "persona": self.persona,
            "persona_body": self.persona_body,
            "charter": self.charter,
        }


@dataclass(frozen=True)
class SharedHarness:
    """The ONE canonical harness a whole family resolves through.

    ``harness_id`` is "assess" or "advise". ``harness_ir`` is the Order-01 normalized IR the harness
    compiles from (it OWNS the lifecycle + evidence). Lens/persona modules attach to it; they never
    carry their own lifecycle. ``compiled`` is the Order-01 compiled projection (cached) so the
    semantic digest uses the ONE Order-01/Order-11 scheme.
    """

    harness_id: str
    harness_ir: Mapping[str, Any]

    def compiled(self) -> Dict[str, Any]:
        return _compiler.compile_workflow(self.harness_ir)

    def semantic_digest(self) -> str:
        # ONE digest scheme: the Order-01 profile semantic digest over the Order-01 compiled view.
        return _profile.semantic_digest(self.compiled())


def assert_no_lens_fork(contribution: Mapping[str, Any]) -> None:
    """Reject a lens/persona contribution that tries to redefine a harness-reserved key (fork)."""

    for key in contribution.keys():
        if key in HARNESS_RESERVED_KEYS:
            raise HarnessForkError(
                "lens/persona contribution may not set harness-reserved key '{0}' (lifecycle/evidence fork)".format(
                    key
                )
            )


@dataclass
class HarnessRegistry:
    """A family's shared harness plus its lens/persona modules. Every member resolves through the ONE
    harness; a member that forks the harness is refused at registration time."""

    harness: SharedHarness
    lenses: Dict[str, LensModule] = field(default_factory=dict)
    personas: Dict[str, PersonaModule] = field(default_factory=dict)

    def register_lens(self, lens: LensModule) -> None:
        assert_no_lens_fork(lens.contribution())
        self.lenses[lens.concern] = lens

    def register_persona(self, persona: PersonaModule) -> None:
        assert_no_lens_fork(persona.contribution())
        self.personas[persona.persona] = persona

    def resolve_lens(self, concern: str) -> Tuple[str, LensModule]:
        """Resolve a concern to (harness_id, lens). Every concern resolves through the SAME harness."""

        if concern not in self.lenses:
            raise InventoryError("unknown lens concern '{0}'".format(concern))
        return self.harness.harness_id, self.lenses[concern]

    def resolve_persona(self, persona: str) -> Tuple[str, PersonaModule]:
        if persona not in self.personas:
            raise InventoryError("unknown persona '{0}'".format(persona))
        return self.harness.harness_id, self.personas[persona]

    def catalog_rows(self) -> List[Dict[str, Any]]:
        """Generate the catalog rows for every member, all bound to the harness's ONE semantic digest
        so a member row cannot silently drift from the harness."""

        digest = self.harness.semantic_digest()
        rows: List[Dict[str, Any]] = []
        for concern in sorted(self.lenses):
            rows.append(
                {
                    "command": "{0}-{1}".format(self.harness.harness_id, concern),
                    "harness": self.harness.harness_id,
                    "member": concern,
                    "kind": "lens",
                    "semantic_digest": digest,
                }
            )
        for persona in sorted(self.personas):
            rows.append(
                {
                    "command": "{0}-{1}".format(self.harness.harness_id, persona),
                    "harness": self.harness.harness_id,
                    "member": persona,
                    "kind": "persona",
                    "semantic_digest": digest,
                }
            )
        return rows


def _harness_ir(harness_id: str, summary: str, interaction: str) -> Dict[str, Any]:
    """Build a minimal, schema-shaped normalized IR for a family harness.

    This is the ONE lifecycle+evidence contract the whole family shares. Lens/persona modules never
    carry their own; they attach concern/charter content on top of this. The IR is deliberately
    small: the point is that all members compile from THIS, so the semantic digest is shared.
    """

    workflow = {
        "schema_version": 1,
        "id": harness_id,
        "intent": "assess" if harness_id == "assess" else "advise",
        "risk": "read-only",
        "interaction": interaction,
        "mutation_boundary": "planning-only",
        "summary": summary,
        "requirements": [
            {
                "id": "R-01",
                "text": "Apply the shared harness lifecycle to the selected member.",
                "evidence": ["inspection"],
            }
        ],
        "steps": [
            {
                "id": "S-01",
                "action": "Resolve the member and apply the shared harness lifecycle.",
                "satisfies": ["R-01"],
                "depends_on": [],
                "evidence": ["inspection"],
            }
        ],
        "validations": [{"verifies": "R-01", "evidence": ["inspection"]}],
    }
    return {
        "ir_version": 1,
        "digest": hashlib.sha256(harness_id.encode("utf-8")).hexdigest(),
        "source_root": "(synthetic-harness)",
        "workflow": workflow,
        "resources": {},
    }


def build_assess_harness(source_root: Any) -> HarnessRegistry:
    """Build the shared `assess` harness registry from the live manifest lenses (one harness; every
    lens a typed module)."""

    root = _workflows_root(source_root)
    workflows = engine.parse_manifest(root)
    harness = SharedHarness(
        harness_id="assess",
        harness_ir=_harness_ir(
            "assess", "Assess one concern deeply and propose an IPD.", "optional"
        ),
    )
    reg = HarnessRegistry(harness=harness)
    for w in workflows:
        if w.command.startswith(LENS_PREFIX) and engine.is_concern_catalog_row(w):
            concern = w.command[len(LENS_PREFIX) :]
            reg.register_lens(
                LensModule(
                    concern=concern,
                    lens_body=w.lens,
                    rubric_focus=w.description,
                    lead_personas=(),
                )
            )
    return reg


def build_advise_harness(source_root: Any) -> HarnessRegistry:
    """Build the shared `advise` harness registry from the live manifest personas."""

    root = _workflows_root(source_root)
    workflows = engine.parse_manifest(root)
    harness = SharedHarness(
        harness_id="advise",
        harness_ir=_harness_ir(
            "advise", "Interrogate and coach with an expert persona.", "interactive"
        ),
    )
    reg = HarnessRegistry(harness=harness)
    for w in workflows:
        if w.command.startswith(PERSONA_PREFIX) and engine.is_concern_catalog_row(w):
            persona = w.command[len(PERSONA_PREFIX) :]
            reg.register_persona(
                PersonaModule(
                    persona=persona,
                    persona_body=w.lens,
                    charter=w.description,
                )
            )
    return reg


# ---- rollup (assess-all) scope/cost confirmation + de-duplication -------------------------------


class RollupConfirmationError(ValueError):
    """Raised when a rollup runs without an explicit scope/cost confirmation."""


@dataclass(frozen=True)
class RollupPlan:
    """A resolved, de-duplicated rollup member set with an explicit confirmation.

    ``confirmed`` MUST be True before :func:`plan_rollup` returns; a rollup that has not confirmed
    scope/cost is refused (that is the explicit scope/cost confirmation the plan requires).
    """

    members: Tuple[str, ...]
    estimated_cost_units: int
    confirmed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "members": list(self.members),
            "estimated_cost_units": self.estimated_cost_units,
            "confirmed": self.confirmed,
        }


def plan_rollup(
    registry: HarnessRegistry,
    requested: Optional[Sequence[str]] = None,
    *,
    confirmed: bool = False,
    cost_per_member: int = 1,
) -> RollupPlan:
    """Resolve a rollup member set with de-duplication + a mandatory scope/cost confirmation.

    ``requested`` None means "all lenses". Duplicate members are collapsed (de-dup rule). The rollup
    is REFUSED unless ``confirmed`` is True: the caller must have shown the user the scope and cost
    and received explicit confirmation. This is the rollup-confirmation gate.
    """

    available = sorted(registry.lenses)
    if requested is None:
        members = list(available)
    else:
        # de-duplicate while preserving first-seen order, and reject unknown members.
        seen: set = set()
        members = []
        for m in requested:
            if m not in registry.lenses:
                raise InventoryError("rollup requested unknown lens '{0}'".format(m))
            if m in seen:
                continue
            seen.add(m)
            members.append(m)
    cost = len(members) * cost_per_member
    if not confirmed:
        raise RollupConfirmationError(
            "rollup over {0} members (~{1} cost units) requires explicit scope/cost confirmation".format(
                len(members), cost
            )
        )
    return RollupPlan(members=tuple(members), estimated_cost_units=cost, confirmed=True)


# ==================================================================================================
# E-03: plan-review collapse -- ONE package -> two views -> semantic-digest parity + drift detection
# ==================================================================================================

# Both legacy command names, from ONE canonical package. `plan-review` is canonical; `plan-review-long`
# is its alias. Both compile from the same IR, so both share the semantic digest + arguments.
PLAN_REVIEW_COMMAND = "plan-review"
PLAN_REVIEW_ALIAS = "plan-review-long"


@dataclass(frozen=True)
class PlanReviewViews:
    """The two compiled views of the ONE plan-review package.

    ``single_file`` is the portable single-file prompt bundle (the `plan-review` view). ``long`` is
    the list of bounded step packets (the `plan-review-long` orchestrator view). Both derive from the
    same compiled projection, so :func:`plan_review_parity` proves they cannot diverge.
    """

    compiled: Mapping[str, Any]
    single_file: str
    long: Tuple[Dict[str, Any], ...]
    aliases: Tuple[str, ...]

    def semantic_digest(self) -> str:
        return _profile.semantic_digest(self.compiled)

    def view_digest(self, view: str) -> str:
        """A byte-level digest of one generated view. A mutation of EITHER view changes ITS digest
        (drift detection), while both share the semantic digest (parity)."""

        if view == "single_file":
            blob = self.single_file
        elif view == "long":
            blob = json.dumps(
                list(self.long),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        else:
            raise InventoryError("unknown view '{0}'".format(view))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def compile_plan_review(package_root: Any) -> PlanReviewViews:
    """Compile the ONE canonical plan-review package into BOTH views.

    Reuses the Order-01 loader + compiler; both views come from the SAME compiled projection so they
    are guaranteed to carry the same semantic digest + arguments. Both command names are recorded as
    aliases of the one package.
    """

    from agent_workflows import workflow_loader as _loader

    result = _loader.load_package(package_root)
    if not result.ok or result.ir is None:
        raise InventoryError(
            "plan-review package failed to load: {0}".format(
                [f.message for f in result.findings]
            )
        )
    return _plan_review_views_from_ir(result.ir)


def plan_review_views_from_ir(ir: Mapping[str, Any]) -> PlanReviewViews:
    """Build both plan-review views from an already-loaded IR (test-friendly seam)."""

    return _plan_review_views_from_ir(ir)


def _plan_review_views_from_ir(ir: Mapping[str, Any]) -> PlanReviewViews:
    compiled = _compiler.compile_workflow(ir)
    single_file = compiled["prompt_bundle"]  # the portable single-file view
    long_view = tuple(
        compiled["step_packets"]
    )  # the bounded step packets (long orchestrator)
    aliases = tuple(
        sorted({PLAN_REVIEW_ALIAS} | set(compiled["manifest"].get("aliases", [])))
    )
    return PlanReviewViews(
        compiled=compiled,
        single_file=single_file,
        long=long_view,
        aliases=aliases,
    )


@dataclass(frozen=True)
class PlanReviewParity:
    """Outcome of the plan-review one-source parity check."""

    ok: bool
    semantic_digest: str
    aliases_ok: bool
    reason: str


def plan_review_parity(views: PlanReviewViews) -> PlanReviewParity:
    """Prove both command names compile from one package and share the semantic digest + arguments.

    The single semantic digest over the compiled projection covers BOTH views (they derive from it),
    so a shared digest that is stable IS the parity proof. Also proves both legacy names are present
    as aliases of the one package.
    """

    digest = views.semantic_digest()
    manifest = views.compiled.get("manifest", {})
    descriptor = views.compiled.get("command_descriptor", {})
    canonical_id = manifest.get("id")
    alias_set = set(views.aliases)

    aliases_ok = canonical_id == PLAN_REVIEW_COMMAND and PLAN_REVIEW_ALIAS in alias_set
    # "share the arguments" == both resolve to the same command descriptor argument policy.
    takes_argument = descriptor.get("takes_argument")
    reason_parts: List[str] = []
    if not aliases_ok:
        reason_parts.append(
            "expected canonical '{0}' with alias '{1}'".format(
                PLAN_REVIEW_COMMAND, PLAN_REVIEW_ALIAS
            )
        )
    if takes_argument is None:
        reason_parts.append("command descriptor missing argument policy")
    ok = aliases_ok and takes_argument is not None
    return PlanReviewParity(
        ok=ok,
        semantic_digest=digest,
        aliases_ok=aliases_ok,
        reason="; ".join(reason_parts)
        if reason_parts
        else "one source; both views parity",
    )


def detect_view_drift(
    baseline: PlanReviewViews, candidate: PlanReviewViews, view: str
) -> bool:
    """Return True iff ``candidate``'s named generated view differs from ``baseline``'s (drift).

    A mutation of EITHER generated view (single-file OR the long step packets) changes that view's
    byte digest, so this returns True. Identical views return False.
    """

    return baseline.view_digest(view) != candidate.view_digest(view)


# ==================================================================================================
# Agent-facing report (for the completeness-tool evidence paste)
# ==================================================================================================


def render_agent_report(source_root: Any) -> str:
    """Render a deterministic, ANSI-free JSON report of the inventory completeness result.

    This is the pasteable completeness-tool output (V-01 evidence): it names the row count, the ok
    flag, and every finding. Emitted as a single JSON object for machine + human consumption.
    """

    result = build_inventory(source_root)
    return json.dumps(result.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)


__all__ = [
    # E-01
    "EXECUTION_MODES",
    "INTERACTIONS",
    "RISKS",
    "SKILL_DECISIONS",
    "ORCHESTRATION_DECISIONS",
    "EVIDENCE_LEVELS",
    "MIGRATION_OWNERS",
    "Disposition",
    "InventoryResult",
    "InventoryError",
    "build_inventory",
    "check_completeness",
    "enumerate_subjects",
    "render_agent_report",
    "CONFORMANCE_TARGET",
    "CONFORMANCE_ENTRY_RELPATH",
    # E-02
    "HARNESS_RESERVED_KEYS",
    "HarnessForkError",
    "LensModule",
    "PersonaModule",
    "SharedHarness",
    "HarnessRegistry",
    "assert_no_lens_fork",
    "build_assess_harness",
    "build_advise_harness",
    "RollupPlan",
    "RollupConfirmationError",
    "plan_rollup",
    # E-03
    "PLAN_REVIEW_COMMAND",
    "PLAN_REVIEW_ALIAS",
    "PlanReviewViews",
    "PlanReviewParity",
    "compile_plan_review",
    "plan_review_views_from_ir",
    "plan_review_parity",
    "detect_view_drift",
]
