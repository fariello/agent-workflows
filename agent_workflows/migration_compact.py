"""Compact-workflow migration: typed contracts, generated shims/skills, and promotion gates.

awoptimize Order 16 (`g6zjao`). This module is the THIRD and FINAL migration stage of the
workflow-family migration (Order 14 = inventory + shared assess/advise + plan-review collapse;
Order 15 = complex orchestrated coordinators). It migrates the COMPACT / deterministic-first
workflows -- getting-started, list-workflows, whatnext, handoff, research (whose body dir is
`research-prompt/`), verify, spec, release-notes, scaffold -- WITHOUT imposing the multi-agent
orchestration overhead the complex families needed, generates ALL legacy command shims + selected
skill entry points from the canonical packages, and gates every migrated family on its risk-class
benchmark evidence.

Everything here is pure/deterministic and stdlib-only (D138), never touching a runtime YAML parser
(D139), and NON-DESTRUCTIVE: it READS the live manifest + workflow bodies and BUILDS typed contracts
and generated projections over them; it never rewrites the manifest index or a workflow body.

It BUILDS ON the existing system and does not fork it:

  * Order 14 `migration_inventory` -- the disposition INVENTORY. A compact command is resolved to its
    canonical package + BODY DIRECTORY through the inventory / the manifest, NOT by assuming the
    directory equals the command name (e.g. `research` -> `research-prompt/`).
  * Order 11 `host_adapters` + Order 01 `engine` -- the ONE shim/skill generator
    (`engine.generate_shim_members` / `engine.shim_body`, and `host_adapters.build_skill_package`).
    This module REUSES that generator; it does NOT re-implement shim rendering.
  * Order 13 `benchmark_thresholds` + `benchmark_metrics` -- the ONE risk-class promotion gate
    (`evaluate_release_gate` + `ThresholdPolicy`). A family that FAILS its gate stays on the legacy
    path with a recorded reason + a corrective backlog item, and is NEVER advertised as migrated.
    Thresholds are consumed as-is; this module cannot weaken one (the policy owns invariants).

Scope fence (Order 16): the compact packages it migrates are exactly the nine listed above. It does
NOT remove legacy shims (Order 17), migrate the shared/complex families (Orders 14/15), or publish a
release. Old invocations MUST keep working: every compact command still generates its legacy shim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

from agent_workflows import engine
from agent_workflows import host_adapters as _adapters
from agent_workflows.benchmark_metrics import MetricSummary, MetricValue
from agent_workflows.benchmark_thresholds import (
    ThresholdPolicy,
    evaluate_release_gate,
)
from agent_workflows.engine import (
    Workflow,
    generate_shim_members,
    is_concern_catalog_row,
    shim_body,
    validate_shim_grammar,
)

# ==================================================================================================
# Shared error
# ==================================================================================================


class CompactMigrationError(ValueError):
    """Raised when a compact-workflow contract is violated (fail closed)."""


# ==================================================================================================
# E-01: the compact workflows + their typed contracts
# ==================================================================================================

# The nine compact manifest COMMANDS this Order migrates. This is the scope fence mirrored as data so
# a fixture can prove every migrated command is a real manifest row (no invented command, none
# dropped). `research` is listed by its COMMAND name; its body directory is `research-prompt/`, which
# is why a compact package resolves its body through the manifest, never by assuming dir == command.
COMPACT_COMMANDS: Tuple[str, ...] = (
    "getting-started",
    "list-workflows",
    "whatnext",
    "handoff",
    "research",
    "verify",
    "spec",
    "release-notes",
    "scaffold",
)

# How a compact package runs. A compact package is either a SINGLE-CONTEXT guided package (it runs in
# one context, no subagent) or a DETERMINISTIC-FIRST package (a deterministic runtime/command does the
# load-bearing work). NEITHER spawns a subagent it does not need -- that is the load-bearing
# no-needless-orchestration invariant this Order proves.
MODE_SINGLE_CONTEXT: str = "single-context"
MODE_DETERMINISTIC_FIRST: str = "deterministic-first"
COMPACT_MODES: FrozenSet[str] = frozenset(
    (MODE_SINGLE_CONTEXT, MODE_DETERMINISTIC_FIRST)
)

# The write boundary a compact package is allowed. A read-only package may NOT write; a
# planning/prose package writes only planning/prose artifacts (never source or a release); a
# consented-write package writes only behind explicit per-write consent.
WRITE_READ_ONLY: str = "read-only"
WRITE_PLANNING_ONLY: str = "planning-only"
WRITE_CONSENTED: str = "consented-write"
WRITE_BOUNDARIES: FrozenSet[str] = frozenset(
    (WRITE_READ_ONLY, WRITE_PLANNING_ONLY, WRITE_CONSENTED)
)

# Interaction mode, mirroring the Order-01 / Order-14 vocabulary so this module speaks one language.
INTERACTIONS: FrozenSet[str] = frozenset(("noninteractive", "optional", "interactive"))


@dataclass(frozen=True)
class TypedContract:
    """The typed input/output + boundary contract of ONE compact workflow.

    ``needs_subagent`` is the load-bearing field: a compact package sets it False, and
    :meth:`validate` REFUSES a compact package that both claims a compact mode AND declares it needs a
    subagent (that is needless orchestration). A deterministic-first package names the reusable
    ``script`` that does its load-bearing work.
    """

    command: str
    mode: str
    input_kind: str  # "arguments" | "none" | "context"
    output_kind: str  # e.g. "recommendation" | "artifact" | "catalog" | "evidence"
    write_boundary: str
    interaction: str
    needs_subagent: bool = False
    script: Optional[str] = (
        None  # a reusable deterministic script, where fragility warrants it
    )

    def validate(self) -> List[str]:
        """Return a list of contract violations (empty = valid)."""

        problems: List[str] = []
        if not self.command:
            problems.append("empty command")
        if self.mode not in COMPACT_MODES:
            problems.append("bad mode '{0}'".format(self.mode))
        if self.write_boundary not in WRITE_BOUNDARIES:
            problems.append("bad write_boundary '{0}'".format(self.write_boundary))
        if self.interaction not in INTERACTIONS:
            problems.append("bad interaction '{0}'".format(self.interaction))
        if not self.input_kind:
            problems.append("empty input_kind")
        if not self.output_kind:
            problems.append("empty output_kind")
        # The no-needless-orchestration invariant: a compact package must not need a subagent.
        if self.needs_subagent:
            problems.append(
                "compact package '{0}' declares needs_subagent=True (needless orchestration)".format(
                    self.command
                )
            )
        # A deterministic-first package must name the deterministic script doing the work.
        if self.mode == MODE_DETERMINISTIC_FIRST and not self.script:
            problems.append(
                "deterministic-first package '{0}' names no reusable script".format(
                    self.command
                )
            )
        return problems

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "mode": self.mode,
            "input_kind": self.input_kind,
            "output_kind": self.output_kind,
            "write_boundary": self.write_boundary,
            "interaction": self.interaction,
            "needs_subagent": self.needs_subagent,
            "script": self.script,
        }


# The FROZEN typed contracts for the nine compact workflows, reflecting the plan's disposition (the
# whatnext/handoff/research/spec/release-notes family is guided single-context planning/prose; the
# list-workflows/verify family is deterministic-first read-only/evidence; scaffold is a
# deterministic-first authoring package). None needs a subagent.
_COMPACT_CONTRACTS: Dict[str, TypedContract] = {
    "getting-started": TypedContract(
        command="getting-started",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="context",
        output_kind="recommendation",
        write_boundary=WRITE_READ_ONLY,
        interaction="optional",
        needs_subagent=False,
    ),
    "list-workflows": TypedContract(
        command="list-workflows",
        mode=MODE_DETERMINISTIC_FIRST,
        input_kind="arguments",
        output_kind="catalog",
        write_boundary=WRITE_READ_ONLY,
        interaction="optional",
        needs_subagent=False,
        script="list_workflows_catalog",
    ),
    "whatnext": TypedContract(
        command="whatnext",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="arguments",
        output_kind="recommendation",
        write_boundary=WRITE_CONSENTED,
        interaction="optional",
        needs_subagent=False,
    ),
    "handoff": TypedContract(
        command="handoff",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="arguments",
        output_kind="artifact",
        write_boundary=WRITE_PLANNING_ONLY,
        interaction="optional",
        needs_subagent=False,
    ),
    "research": TypedContract(
        command="research",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="arguments",
        output_kind="artifact",
        write_boundary=WRITE_PLANNING_ONLY,
        interaction="optional",
        needs_subagent=False,
    ),
    "verify": TypedContract(
        command="verify",
        mode=MODE_DETERMINISTIC_FIRST,
        input_kind="arguments",
        output_kind="evidence",
        write_boundary=WRITE_CONSENTED,
        interaction="optional",
        needs_subagent=False,
        script="run_checks",
    ),
    "spec": TypedContract(
        command="spec",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="arguments",
        output_kind="artifact",
        write_boundary=WRITE_PLANNING_ONLY,
        interaction="interactive",
        needs_subagent=False,
    ),
    "release-notes": TypedContract(
        command="release-notes",
        mode=MODE_SINGLE_CONTEXT,
        input_kind="context",
        output_kind="artifact",
        write_boundary=WRITE_CONSENTED,
        interaction="interactive",
        needs_subagent=False,
    ),
    "scaffold": TypedContract(
        command="scaffold",
        mode=MODE_DETERMINISTIC_FIRST,
        input_kind="arguments",
        output_kind="artifact",
        write_boundary=WRITE_CONSENTED,
        interaction="interactive",
        needs_subagent=False,
        script="scaffold_generate",
    ),
}


@dataclass(frozen=True)
class CompactPackage:
    """A migrated compact workflow: its canonical package id, resolved body path, typed contract.

    ``body`` is resolved from the manifest row (NOT assumed to be the command name), which is how the
    `research` -> `research-prompt/research-prompt.md` mapping is honored. ``semantic_digest`` reuses
    the ONE Order-01/Order-11 semantic-digest scheme so a compact package's digest matches its shim's.
    """

    command: str
    canonical_package: str
    body: str
    contract: TypedContract
    semantic_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "canonical_package": self.canonical_package,
            "body": self.body,
            "contract": self.contract.to_dict(),
            "semantic_digest": self.semantic_digest,
        }


def _workflow_by_command(source_root: Any) -> Dict[str, Workflow]:
    """Index the live manifest by command (the ONE manifest authority, via engine.parse_manifest)."""

    return {w.command: w for w in engine.parse_manifest(source_root)}


def resolve_body_dir(command: str, source_root: Any) -> str:
    """Resolve a compact COMMAND to its BODY DIRECTORY via the manifest (never assuming dir==command).

    Returns the leading directory segment of the manifest body path (e.g. `research` ->
    `research-prompt`). This is the explicit mapping the plan's PR-001 revision requires: a compact
    command is resolved through the manifest / Order-14 inventory, not by assuming the directory name
    equals the command name.
    """

    workflows = _workflow_by_command(source_root)
    if command not in workflows:
        raise CompactMigrationError(
            "compact command '{0}' is not a live manifest row".format(command)
        )
    body = workflows[command].body
    # body is like ".aw/system/workflows/research-prompt/research-prompt.md"; the body dir is the
    # segment after the workflows dir.
    for prefix in (
        engine.AW_SYSTEM_WORKFLOWS_DIR + "/",
        engine.WORKFLOWS_DIR + "/",
    ):
        if body.startswith(prefix):
            rest = body[len(prefix) :]
            return rest.split("/", 1)[0]
    # Fallback: the directory portion of the body path.
    return body.rsplit("/", 1)[0].rsplit("/", 1)[-1] if "/" in body else body


def build_compact_package(command: str, source_root: Any) -> CompactPackage:
    """Build ONE migrated compact package from the live manifest + its frozen typed contract.

    Fails closed if the command is not one of the nine compact commands, is not a live manifest row,
    or has no frozen contract. Reuses the Order-11 semantic-digest scheme so the package digest is the
    SAME scheme the generated shim/skill will carry.
    """

    if command not in COMPACT_COMMANDS:
        raise CompactMigrationError(
            "'{0}' is not a compact workflow this Order migrates".format(command)
        )
    workflows = _workflow_by_command(source_root)
    if command not in workflows:
        raise CompactMigrationError(
            "compact command '{0}' is not a live manifest row".format(command)
        )
    contract = _COMPACT_CONTRACTS.get(command)
    if contract is None:
        raise CompactMigrationError(
            "compact command '{0}' has no frozen typed contract".format(command)
        )
    problems = contract.validate()
    if problems:
        raise CompactMigrationError(
            "compact contract for '{0}' invalid: {1}".format(
                command, "; ".join(problems)
            )
        )
    workflow = workflows[command]
    digest = _adapters.compute_workflow_semantic_digest(workflow)
    return CompactPackage(
        command=command,
        canonical_package=command,
        body=workflow.body,
        contract=contract,
        semantic_digest=digest,
    )


def build_all_compact_packages(source_root: Any) -> Dict[str, CompactPackage]:
    """Build every compact package (keyed by command). Used by the completeness check + generators."""

    return {cmd: build_compact_package(cmd, source_root) for cmd in COMPACT_COMMANDS}


def assert_no_needless_subagent(package: CompactPackage) -> None:
    """Fail closed if a compact package would spawn a subagent it does not need.

    This is the falsifiable no-needless-orchestration guard: a compact package's contract must carry
    ``needs_subagent=False``; a package that flips it True is refused here (mirroring how a lens that
    forks the harness is refused in Order 14).
    """

    if package.contract.needs_subagent:
        raise CompactMigrationError(
            "compact package '{0}' would spawn a needless subagent".format(
                package.command
            )
        )


def check_compact_completeness(source_root: Any) -> List[str]:
    """PROVE the compact migration is complete + valid. Returns findings (empty = complete).

    Falsifiable checks:
      1. every one of the nine compact commands is a live manifest row (none invented/dropped);
      2. every compact command resolves to a body dir via the manifest (research -> research-prompt);
      3. every compact contract is valid + needs no subagent;
      4. no compact command is silently a catalog row (assess-/advise-), which would have no shim.
    """

    findings: List[str] = []
    workflows = _workflow_by_command(source_root)
    for cmd in COMPACT_COMMANDS:
        if cmd not in workflows:
            findings.append(
                "compact command '{0}' is not a live manifest row (silent omission)".format(
                    cmd
                )
            )
            continue
        w = workflows[cmd]
        if is_concern_catalog_row(w):
            findings.append(
                "compact command '{0}' is a catalog row (would generate no shim)".format(
                    cmd
                )
            )
        try:
            body_dir = resolve_body_dir(cmd, source_root)
        except CompactMigrationError as exc:
            findings.append(str(exc))
            body_dir = ""
        if not body_dir:
            findings.append(
                "compact command '{0}' has no resolvable body dir".format(cmd)
            )
        contract = _COMPACT_CONTRACTS.get(cmd)
        if contract is None:
            findings.append("compact command '{0}' has no typed contract".format(cmd))
        else:
            findings.extend(
                "compact command '{0}': {1}".format(cmd, p) for p in contract.validate()
            )
    return findings


# ==================================================================================================
# E-02: generate ALL legacy command shims + selected skill entry points (REUSE engine.py generator)
# ==================================================================================================


@dataclass
class CompactProjection:
    """The generated projections for the compact packages: legacy shims + selected skill packages.

    ``shims`` maps a repo-relative shim path -> content, produced by the ONE
    :func:`engine.generate_shim_members` generator (reused, not forked). ``skill_packages`` are the
    selected skill entry points, produced by the ONE :func:`host_adapters.build_skill_package`
    generator. Both preserve command names + argument behavior.
    """

    shims: Dict[str, str]
    skill_packages: Dict[str, _adapters.SkillPackage]

    def shim_for(self, command: str) -> Dict[str, str]:
        """Return every generated shim path -> content whose file is `<command>.md`."""

        suffix = "/{0}.md".format(command)
        return {p: c for p, c in self.shims.items() if p.endswith(suffix)}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shim_paths": sorted(self.shims),
            "skill_packages": {
                name: pkg.to_dict() for name, pkg in sorted(self.skill_packages.items())
            },
        }


def generate_compact_projection(
    source_root: Any,
    target_layout: str = "aw",
    skill_commands: Optional[Sequence[str]] = None,
) -> CompactProjection:
    """Generate ALL legacy command shims + selected skill entry points from the canonical packages.

    Command shims REUSE :func:`agent_workflows.engine.generate_shim_members` -- the ONE canonical shim
    generator -- over the WHOLE live manifest, so every legacy command (compact + shared + complex)
    still generates its shim and old invocations keep working. This module does NOT re-implement shim
    rendering.

    Selected skill entry points REUSE :func:`agent_workflows.host_adapters.build_skill_package` (which
    itself extends the engine generator). By default the compact commands the Order-11 discovery
    policy classifies as skill entry points get a skill; ``skill_commands`` overrides that selection.
    """

    workflows = engine.parse_manifest(source_root)
    by_command = {w.command: w for w in workflows}

    # REUSE the engine generator for shims -- do not fork.
    shims = generate_shim_members(workflows, source_root, target_layout=target_layout)

    if skill_commands is None:
        selected = [
            cmd
            for cmd in COMPACT_COMMANDS
            if cmd in by_command
            and _adapters.classify_discovery_policy(
                by_command[cmd], target_layout=target_layout
            )
            == _adapters.POLICY_SKILL_ENTRY_POINT
        ]
    else:
        selected = list(skill_commands)

    skill_packages: Dict[str, _adapters.SkillPackage] = {}
    for cmd in selected:
        if cmd not in by_command:
            raise CompactMigrationError(
                "selected skill command '{0}' is not a live manifest row".format(cmd)
            )
        # REUSE the Order-11 skill generator -- do not fork.
        skill_packages[cmd] = _adapters.build_skill_package(
            by_command[cmd], target_layout=target_layout
        )

    return CompactProjection(shims=shims, skill_packages=skill_packages)


@dataclass(frozen=True)
class ShimResolution:
    """The resolution of ONE legacy command shim: which package + digest it resolves to.

    ``resolves_package`` is the canonical package the shim points at (its body path), and
    ``semantic_digest`` is the canonical digest bound to it. A generated shim that resolves to the
    wrong package or a drifted digest fails the resolution check.
    """

    command: str
    body_target: str
    semantic_digest: str
    view_digest: str  # byte digest of the generated shim (for drift detection)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "body_target": self.body_target,
            "semantic_digest": self.semantic_digest,
            "view_digest": self.view_digest,
        }


def _shim_view_digest(text: str) -> str:
    """Byte-level digest of a generated shim view (a hand-edit changes this -> drift detected)."""

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_shim(
    command: str,
    source_root: Any,
    tool: str = "opencode",
    target_layout: str = "aw",
) -> ShimResolution:
    """Resolve a legacy command to the package + canonical digest its generated shim carries.

    Reuses :func:`engine.shim_body` to render the SAME shim the generator emits, and binds it to the
    Order-11 canonical semantic digest so an alias cannot silently mask drift: the resolution records
    the body target the shim points at AND the digest of the canonical package. A hand-edit of the
    generated shim changes ``view_digest`` (the drift signal).
    """

    workflows = _workflow_by_command(source_root)
    if command not in workflows:
        raise CompactMigrationError(
            "command '{0}' is not a live manifest row".format(command)
        )
    workflow = workflows[command]
    body = shim_body(command, workflow, tool, target_layout=target_layout)
    if not validate_shim_grammar(body, tool):
        raise CompactMigrationError(
            "generated shim for '{0}' fails grammar validation".format(command)
        )
    workflows_dir = engine.resolve_workflows_dir(target_layout)
    body_target = (
        workflow.body.replace(engine.WORKFLOWS_DIR + "/", workflows_dir + "/")
        if target_layout == "aw"
        and workflow.body.startswith(engine.WORKFLOWS_DIR + "/")
        else workflow.body
    )
    return ShimResolution(
        command=command,
        body_target=body_target,
        semantic_digest=_adapters.compute_workflow_semantic_digest(workflow),
        view_digest=_shim_view_digest(body),
    )


def detect_shim_drift(baseline: str, candidate: str) -> bool:
    """Return True iff a candidate shim differs byte-for-byte from the baseline (drift).

    A HAND-EDIT of a generated shim changes its bytes, so this returns True. An identical
    regeneration returns False. This is the falsifiable drift check the plan requires.
    """

    return _shim_view_digest(baseline) != _shim_view_digest(candidate)


def argument_parity(command: str, source_root: Any, target_layout: str = "aw") -> bool:
    """Prove the generated shim preserves the command's ARGUMENT behavior (argument golden parity).

    A command with a real ``arg_hint`` (or the generic default) must emit `$ARGUMENTS` handling; a
    command whose ``arg_hint == "none"`` must NOT. This checks the generated shim against the
    manifest's declared argument behavior, so a shim that drops or invents argument handling fails.
    """

    workflows = _workflow_by_command(source_root)
    if command not in workflows:
        raise CompactMigrationError(
            "command '{0}' is not a live manifest row".format(command)
        )
    workflow = workflows[command]
    body = shim_body(command, workflow, "opencode", target_layout=target_layout)
    takes_arguments = "$ARGUMENTS" in body
    expects_arguments = workflow.arg_hint.strip() != "none"
    return takes_arguments == expects_arguments


def skill_resolves_package(
    package: CompactPackage, skill: _adapters.SkillPackage
) -> bool:
    """Prove a generated skill entry point resolves the correct package + canonical digest.

    A skill resolves its package correctly iff it carries the SAME canonical semantic digest as the
    compact package and its explicit invocation points at the package's body. A skill bound to a
    different digest (silent drift) returns False.
    """

    if skill.semantic_digest != package.semantic_digest:
        return False
    if not _adapters.disabled_skill_still_invocable(skill):
        return False
    # The skill's explicit invocation must reference the package body's directory.
    return package.body.rsplit("/", 1)[-1].rsplit(".", 1)[
        0
    ] in skill.explicit_invocation or (skill.name in skill.explicit_invocation)


def old_invocation_still_works(
    command: str, source_root: Any, target_layout: str = "aw"
) -> bool:
    """Prove the OLD legacy invocation of a compact command still works during migration.

    The old invocation is the generated legacy command shim. It "still works" iff the generator emits
    a grammatically valid shim for the command that points at the canonical body (a read-and-execute
    pointer). This is what keeps `/getting-started`, `/verify`, `/research`, ... usable after
    migration.
    """

    projection = generate_compact_projection(source_root, target_layout=target_layout)
    matches = projection.shim_for(command)
    if not matches:
        return False
    workflows_dir = engine.resolve_workflows_dir(target_layout)
    for content in matches.values():
        # Grammar-validate against whichever tool grammar the shim satisfies.
        ok = validate_shim_grammar(content, "opencode") or validate_shim_grammar(
            content, "claude"
        )
        if not ok:
            return False
        if ("@" + workflows_dir + "/") not in content and (
            "@.agents/workflows/" not in content
        ):
            return False
    return True


# ==================================================================================================
# E-03: per-family benchmark PROMOTION GATES (REUSE Order 13) + honest legacy fallback
# ==================================================================================================

# The migration path a family lands on after its promotion gate. `migrated` families are ADVERTISED
# as migrated; `legacy-fallback` families stay on the legacy path with an explicit reason + a
# corrective backlog item and are NEVER advertised as migrated.
PATH_MIGRATED: str = "migrated"
PATH_LEGACY_FALLBACK: str = "legacy-fallback"


@dataclass(frozen=True)
class CorrectiveBacklogItem:
    """A typed corrective backlog item recorded for a family that FAILED its promotion gate.

    This is data, not a file write (non-destructive, per the Order 14/15 precedent): a fixture asserts
    a failing family produces exactly one of these with the gate findings, and that the family is not
    advertised as migrated. ``status`` mirrors the Order-`backlog` vocabulary (`open`).
    """

    family: str
    reason: str
    findings: Tuple[str, ...]
    status: str = "open"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family,
            "reason": self.reason,
            "findings": list(self.findings),
            "status": self.status,
        }


@dataclass(frozen=True)
class PromotionDecision:
    """The per-family promotion-gate decision.

    ``advertised`` is True ONLY when ``migration_path == PATH_MIGRATED`` (a passing gate). A failing
    family carries ``migration_path == PATH_LEGACY_FALLBACK``, ``advertised == False``, and a
    :class:`CorrectiveBacklogItem`. This is the load-bearing evidence-gated-and-reversible invariant.
    """

    family: str
    risk_class: str
    passed: bool
    migration_path: str
    advertised: bool
    findings: Tuple[str, ...]
    corrective_item: Optional[CorrectiveBacklogItem] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family": self.family,
            "risk_class": self.risk_class,
            "passed": self.passed,
            "migration_path": self.migration_path,
            "advertised": self.advertised,
            "findings": list(self.findings),
            "corrective_item": (
                self.corrective_item.to_dict() if self.corrective_item else None
            ),
        }


def _mv(name: str, value: Any, n: int) -> MetricValue:
    return MetricValue(name=name, value=value, sample_size=n)


def build_metric_summary(
    *,
    requirement_recall: float,
    task_correctness: float,
    evidence_validity: float,
    test_integrity: float = 1.0,
    critical_escapes: int = 0,
    scope_violations: int = 0,
    sample_size: int = 10,
) -> MetricSummary:
    """Build a MetricSummary fixture the Order-13 gate can evaluate (test/fixture seam).

    This does NOT invent a metric scheme: it constructs the SAME :class:`MetricSummary` the Order-13
    ``evaluate_release_gate`` consumes, so the promotion gate is exercised through the real gate, not
    a reimplementation. ``critical_escapes`` is encoded as the defect-escape rate over the sample so
    the gate's `zero_critical_escapes` check sees the intended count.
    """

    n = max(1, sample_size)
    escape_rate = float(critical_escapes) / float(n)
    zero = _mv("_", 0.0, n)
    return MetricSummary(
        sample_size=n,
        completed_trials=n,
        pending_trials=0,
        requirement_recall=_mv("requirement_recall", requirement_recall, n),
        task_correctness=_mv("task_correctness", task_correctness, n),
        evidence_validity=_mv("evidence_validity", evidence_validity, n),
        false_completion_detection=_mv("false_completion_detection", 1.0, n),
        defect_escape=_mv("defect_escape", escape_rate, n),
        regression_rate=_mv("regression_rate", 0.0, n),
        scope_violations=_mv("scope_violations", int(scope_violations), n),
        test_integrity=_mv("test_integrity", test_integrity, n),
        skill_activation_precision=zero,
        skill_activation_recall=zero,
        total_retries=_mv("total_retries", 0, n),
        total_human_interventions=_mv("total_human_interventions", 0, n),
        wall_time_seconds=_mv("wall_time_seconds", {"mean": 0.0, "total": 0.0}, n),
        tokens=_mv("tokens", 0, n),
    )


def evaluate_promotion_gate(
    family: str,
    metrics: MetricSummary,
    risk_class: str,
    policy: Optional[ThresholdPolicy] = None,
) -> PromotionDecision:
    """Run the Order-13 promotion gate for a family and decide its migration path.

    REUSES :func:`agent_workflows.benchmark_thresholds.evaluate_release_gate` (the ONE risk-class
    gate); this module never re-derives a threshold and cannot weaken one (the policy owns
    invariants). A PASS advertises the family as migrated; a FAIL keeps it on the legacy path with an
    explicit reason + a corrective backlog item and does NOT advertise it as migrated.
    """

    policy = policy or ThresholdPolicy()
    result = evaluate_release_gate(
        metrics, policy, risk_class=risk_class, model_profile_name=family
    )
    if result.passed:
        return PromotionDecision(
            family=family,
            risk_class=risk_class,
            passed=True,
            migration_path=PATH_MIGRATED,
            advertised=True,
            findings=(),
            corrective_item=None,
        )
    reason = (
        "family '{0}' failed its {1} promotion gate; staying on legacy path".format(
            family, risk_class
        )
    )
    corrective = CorrectiveBacklogItem(
        family=family,
        reason=reason,
        findings=tuple(result.findings),
    )
    return PromotionDecision(
        family=family,
        risk_class=risk_class,
        passed=False,
        migration_path=PATH_LEGACY_FALLBACK,
        advertised=False,
        findings=tuple(result.findings),
        corrective_item=corrective,
    )


def advertised_families(decisions: Sequence[PromotionDecision]) -> Tuple[str, ...]:
    """Return the families ADVERTISED as migrated (passing gates only).

    A failing family is never in this set -- that is the "never advertise a failing family as
    migrated" invariant, made queryable.
    """

    return tuple(
        sorted(
            d.family
            for d in decisions
            if d.advertised and d.migration_path == PATH_MIGRATED
        )
    )


def legacy_fallback_families(
    decisions: Sequence[PromotionDecision],
) -> Dict[str, CorrectiveBacklogItem]:
    """Return {family: corrective backlog item} for every family kept on the legacy path."""

    out: Dict[str, CorrectiveBacklogItem] = {}
    for d in decisions:
        if d.migration_path == PATH_LEGACY_FALLBACK and d.corrective_item is not None:
            out[d.family] = d.corrective_item
    return out


# ==================================================================================================
# Agent-facing report (pasteable evidence)
# ==================================================================================================


def render_agent_report(source_root: Any, target_layout: str = "aw") -> str:
    """Render a deterministic JSON report of the compact migration + projection completeness.

    Pasteable evidence: it names the compact completeness findings (empty == complete), each compact
    package's resolved body + digest, and the generated shim/skill projection summary.
    """

    packages = build_all_compact_packages(source_root)
    projection = generate_compact_projection(source_root, target_layout=target_layout)
    report = {
        "compact_completeness_findings": check_compact_completeness(source_root),
        "packages": {c: p.to_dict() for c, p in sorted(packages.items())},
        "projection": projection.to_dict(),
    }
    return json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False)


__all__ = [
    "CompactMigrationError",
    # E-01
    "COMPACT_COMMANDS",
    "MODE_SINGLE_CONTEXT",
    "MODE_DETERMINISTIC_FIRST",
    "COMPACT_MODES",
    "WRITE_READ_ONLY",
    "WRITE_PLANNING_ONLY",
    "WRITE_CONSENTED",
    "WRITE_BOUNDARIES",
    "INTERACTIONS",
    "TypedContract",
    "CompactPackage",
    "resolve_body_dir",
    "build_compact_package",
    "build_all_compact_packages",
    "assert_no_needless_subagent",
    "check_compact_completeness",
    # E-02
    "CompactProjection",
    "generate_compact_projection",
    "ShimResolution",
    "resolve_shim",
    "detect_shim_drift",
    "argument_parity",
    "skill_resolves_package",
    "old_invocation_still_works",
    # E-03
    "PATH_MIGRATED",
    "PATH_LEGACY_FALLBACK",
    "CorrectiveBacklogItem",
    "PromotionDecision",
    "build_metric_summary",
    "evaluate_promotion_gate",
    "advertised_families",
    "legacy_fallback_families",
    # report
    "render_agent_report",
    # reused generators (not forked):
    "generate_shim_members",
    "shim_body",
    "validate_shim_grammar",
]
