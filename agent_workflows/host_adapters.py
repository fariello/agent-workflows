"""Generated Agent Skills packages and evidence-gated per-host adapter metadata.

awoptimize Order 11 (`bmd1ur`) E-01..E-03:
- E-01: Generate portable Agent Skills packages (`SKILL.md` router carrying an exact
        trigger description, the canonical semantic digest, an explicit-invocation
        option, reference files, templates, and deterministic scripts) each within a
        project context budget. v1 scopes OpenCode + Codex via the shared
        `.agents/skills/` target (per Order-10 OQ-01). Generated skills pass format
        validation; trigger descriptions distinguish use vs non-use; resource refs
        resolve within the package.
- E-02: Generate host-specific adapter metadata, EXTENDING the existing shim generator
        in :mod:`agent_workflows.engine` (`generate_shim_members`/`shim_body`/
        `COMMAND_SHIM_DIRS`) rather than forking a parallel adapter path (rubric C).
        Advertises a capability as `supported` ONLY where the Order-10
        :mod:`agent_workflows.host_capability_registry` marks it non-`unverified`;
        otherwise the row is emitted generated-but-flagged-`unverified` and never
        advertised as supported. Each adapter maps native features to canonical roles
        and falls back to external runtime coordination when a feature is absent.
- E-03: Restrict skills to discoverable on-demand capabilities + deterministic
        resources. Complex workflows become thin skill entry points; simple
        informational commands may remain generated commands; authoritative runtime
        behavior NEVER lives only in `SKILL.md` prose (it lives in the canonical
        source + runtime). Disabling a skill leaves the explicit runtime invocation
        usable.

This module is a PURE generator conforming to D138 (stdlib only) and D139 (no runtime
YAML). It does not run live host probes and does not define the capability registry; it
CONSUMES Order 10's registry as the gate for every `supported` claim, and REUSES (does
not fork) the :mod:`agent_workflows.engine` shim generator for command shims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from agent_workflows import engine
from agent_workflows.engine import (
    COMMAND_SHIM_DIRS,
    Workflow,
    generate_shim_members,
    shim_body,
    validate_shim_grammar,
)
from agent_workflows.host_capability_registry import (
    STATUS_UNVERIFIED,
    CapabilityEvaluation,
    HostCapabilityRegistry,
    SafetyError,
    assert_contained,
    assert_isolated_base,
)

# ==================================================================================================
# Constants & Vocabularies
# ==================================================================================================

# The shared on-demand Agent Skills directory target (Order-10 OQ-01: OpenCode + Codex v1).
SHARED_SKILLS_DIR: str = ".agents/skills"

# v1 hosts that generate a live-capable adapter/skill target. Other rows are generated
# but flagged unverified until Order-10 probes promote them.
V1_HOSTS: Tuple[str, ...] = ("opencode", "codex")

# All hosts we generate adapter metadata for (v1 + deferred/unverified rows).
ALL_ADAPTER_HOSTS: Tuple[str, ...] = (
    "opencode",
    "codex",
    "kiro",
    "gemini_cli",
    "claude_code",
    "antigravity",
)

# Per-host always-loaded pointer file (the thin instruction file every host reads up front).
HOST_POINTER_FILE: Dict[str, str] = {
    "opencode": "AGENTS.md",
    "codex": "AGENTS.md",
    "kiro": "AGENTS.md",
    "gemini_cli": "GEMINI.md",
    "claude_code": "CLAUDE.md",
    "antigravity": "AGENTS.md",
}

# Per-host on-demand skill directory candidate (native override; shared target otherwise).
HOST_SKILL_DIR: Dict[str, str] = {
    "opencode": SHARED_SKILLS_DIR,
    "codex": SHARED_SKILLS_DIR,
    "kiro": ".kiro/skills",
    "gemini_cli": ".gemini/skills",
    "claude_code": ".claude/skills",
    "antigravity": ".agents/skills",
}

# Noninteractive (headless) runtime invocation candidate per host. When a native feature
# is absent, an adapter falls back to this external runtime coordination command.
HOST_NONINTERACTIVE_RUNTIME: Dict[str, str] = {
    "opencode": "opencode run --format json",
    "codex": "codex exec",
    "kiro": "kiro-cli chat --no-interactive",
    "gemini_cli": "gemini -p --output-format stream-json",
    "claude_code": "claude -p",
    "antigravity": "agy run",
}

# Canonical role vocabulary that native host features map onto.
ROLE_ROUTER: str = "router"  # on-demand discovery/dispatch
ROLE_ISOLATED_EXECUTOR: str = "isolated_executor"  # subagent / fresh session
ROLE_NONINTERACTIVE_RUNTIME: str = "noninteractive_runtime"  # headless execution
ROLE_PERMISSION_GATE: str = "permission_gate"  # consent / permission control

ALL_CANONICAL_ROLES: Tuple[str, ...] = (
    ROLE_ROUTER,
    ROLE_ISOLATED_EXECUTOR,
    ROLE_NONINTERACTIVE_RUNTIME,
    ROLE_PERMISSION_GATE,
)

# Native-feature -> canonical-role mapping per host. A feature key ABSENT from a host's
# map means the host has no native feature for that role, so the adapter falls back to
# external runtime coordination (HOST_NONINTERACTIVE_RUNTIME).
HOST_FEATURE_ROLE_MAP: Dict[str, Dict[str, str]] = {
    "opencode": {
        "command": ROLE_ROUTER,
        "skill": ROLE_ROUTER,
        "subagent": ROLE_ISOLATED_EXECUTOR,
        "permissions": ROLE_PERMISSION_GATE,
        "run_json": ROLE_NONINTERACTIVE_RUNTIME,
    },
    "codex": {
        "skill": ROLE_ROUTER,
        "agents_pointer": ROLE_ROUTER,
        "exec": ROLE_NONINTERACTIVE_RUNTIME,
    },
    "kiro": {
        "skill_uri": ROLE_ROUTER,
        "custom_subagent": ROLE_ISOLATED_EXECUTOR,
    },
    "gemini_cli": {
        "skill": ROLE_ROUTER,
        "gemini_pointer": ROLE_ROUTER,
        "subagent": ROLE_ISOLATED_EXECUTOR,
    },
    "claude_code": {
        "skill": ROLE_ROUTER,
        "subagent": ROLE_ISOLATED_EXECUTOR,
        "context_fork": ROLE_ISOLATED_EXECUTOR,
    },
    "antigravity": {
        "runner_template": ROLE_NONINTERACTIVE_RUNTIME,
    },
}

# Default project context budget for a skill's main file (SKILL.md), in bytes. A skill's
# router must stay small so a host discovers many packages without loading all workflow
# text up front. Reference files and scripts hold the bulk; the router points at them.
DEFAULT_SKILL_MAIN_BUDGET_BYTES: int = 8192

# A workflow whose native command shim body exceeds this byte budget is "complex" and
# should be surfaced as a thin skill entry point; below it, a simple informational
# command may remain a generated command (E-03 discovery policy).
SIMPLE_COMMAND_BUDGET_BYTES: int = 1400

# Discovery/authority policy classes (E-03).
POLICY_SKILL_ENTRY_POINT: str = "skill_entry_point"
POLICY_GENERATED_COMMAND: str = "generated_command"


class AdapterGenerationError(ValueError):
    """Raised when adapter/skill generation would violate a generation invariant."""


# ==================================================================================================
# Skill Packages (E-01)
# ==================================================================================================


@dataclass
class SkillResource:
    """A reference file, template, or deterministic script inside a skill package."""

    relative_path: str
    content: str
    kind: str = "reference"  # reference | template | script

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "content": self.content,
            "kind": self.kind,
        }


@dataclass
class SkillPackage:
    """A portable Agent Skill package rooted at ``.agents/skills/<name>/``.

    The main file is ``SKILL.md`` (the router). Authoritative runtime semantics never
    live only in the router prose: the router carries the canonical semantic digest and
    an explicit runtime invocation, and points at reference files/scripts.
    """

    name: str
    skill_dir: str
    trigger_description: str
    semantic_digest: str
    explicit_invocation: str
    main_file_content: str
    resources: List[SkillResource] = field(default_factory=list)
    main_budget_bytes: int = DEFAULT_SKILL_MAIN_BUDGET_BYTES

    def main_file_path(self) -> str:
        return f"{self.skill_dir}/{self.name}/SKILL.md"

    def resource_paths(self) -> List[str]:
        return [
            f"{self.skill_dir}/{self.name}/{r.relative_path}" for r in self.resources
        ]

    def main_file_bytes(self) -> int:
        return len(self.main_file_content.encode("utf-8"))

    def within_budget(self) -> bool:
        return self.main_file_bytes() <= self.main_budget_bytes

    def to_files(self) -> Dict[str, str]:
        """Return the repo-relative path -> content map for the whole package."""
        files: Dict[str, str] = {self.main_file_path(): self.main_file_content}
        base = f"{self.skill_dir}/{self.name}"
        for r in self.resources:
            files[f"{base}/{r.relative_path}"] = r.content
        return files

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "skill_dir": self.skill_dir,
            "trigger_description": self.trigger_description,
            "semantic_digest": self.semantic_digest,
            "explicit_invocation": self.explicit_invocation,
            "main_file_path": self.main_file_path(),
            "main_file_bytes": self.main_file_bytes(),
            "resource_paths": self.resource_paths(),
        }


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "workflow"


def compute_workflow_semantic_digest(workflow: Workflow) -> str:
    """Compute the canonical semantic digest for a workflow's acceptance-relevant fields.

    Reuses :func:`agent_workflows.workflow_profile.semantic_digest` (the Order-01 canonical
    semantic-digest scheme) over a minimal compiled view so the skill router's digest is the
    SAME scheme used elsewhere - no second digest algorithm is invented.
    """
    from agent_workflows import workflow_profile

    compiled = {
        "manifest": {
            "id": workflow.command,
            "body": workflow.body,
            "description": workflow.description,
            "lens": workflow.lens,
        }
    }
    return workflow_profile.semantic_digest(compiled)


def _render_trigger_description(workflow: Workflow) -> str:
    """A single-line trigger description that distinguishes USE vs NON-USE.

    Format: "Use when <affirmative>. Do not use for <negative>." The presence of both an
    affirmative and a negative clause is what lets a host router decide use vs non-use.
    """
    desc = workflow.description.strip().rstrip(".")
    return (
        f"Use when the user asks to {workflow.command} "
        f"({desc}). "
        f"Do not use for unrelated requests or when no {workflow.command} action was requested."
    )


def _render_skill_main_file(
    workflow: Workflow,
    trigger_description: str,
    semantic_digest: str,
    explicit_invocation: str,
    resources: Sequence[SkillResource],
    target_layout: str = "aw",
) -> str:
    """Render the SKILL.md router. Authority stays in canonical source + runtime.

    The router is a thin discovery/dispatch file: it names the canonical body to read and
    execute, records the canonical semantic digest (for parity), lists the reference
    files/scripts by path, and gives the explicit runtime invocation. It does NOT inline
    the workflow's authoritative steps.
    """
    workflows_dir = engine.resolve_workflows_dir(target_layout)
    body_target = (
        workflow.body.replace(f"{engine.WORKFLOWS_DIR}/", f"{workflows_dir}/")
        if target_layout == "aw"
        and workflow.body.startswith(f"{engine.WORKFLOWS_DIR}/")
        else workflow.body
    )

    frontmatter = (
        "---\n"
        f"name: {workflow.command}\n"
        f"description: {trigger_description}\n"
        f"semantic-digest: {semantic_digest}\n"
        "---\n"
    )

    lines = [
        frontmatter,
        f"# Skill: {workflow.command}",
        "",
        "This skill is a discovery/dispatch router only. The authoritative workflow "
        "semantics, state machine, and evidence contract live in the canonical source and "
        "runtime, NOT in this file.",
        "",
        "## Canonical behavior",
        "",
        f"Read and execute @{body_target}. Treat that file as the controlling instruction "
        "and follow it fully.",
        "",
        f"- Canonical semantic digest: `{semantic_digest}`",
        "",
        "## Explicit invocation (works even if this skill is disabled)",
        "",
        f"    {explicit_invocation}",
        "",
    ]

    if resources:
        lines.append("## Package resources")
        lines.append("")
        for r in resources:
            lines.append(f"- `{r.relative_path}` ({r.kind})")
        lines.append("")

    return "\n".join(lines)


def build_skill_package(
    workflow: Workflow,
    skill_dir: str = SHARED_SKILLS_DIR,
    target_layout: str = "aw",
    main_budget_bytes: int = DEFAULT_SKILL_MAIN_BUDGET_BYTES,
    extra_resources: Optional[Sequence[SkillResource]] = None,
) -> SkillPackage:
    """Build one portable Agent Skill package for a workflow.

    The package contains a SKILL.md router (with trigger description, canonical semantic
    digest, explicit invocation, and resource references), one reference file (the pointer
    to the canonical body), and a deterministic verification script that recomputes the
    parity digest.
    """
    name = _slugify(workflow.command)
    semantic_digest = compute_workflow_semantic_digest(workflow)
    trigger = _render_trigger_description(workflow)

    workflows_dir = engine.resolve_workflows_dir(target_layout)
    body_target = (
        workflow.body.replace(f"{engine.WORKFLOWS_DIR}/", f"{workflows_dir}/")
        if target_layout == "aw"
        and workflow.body.startswith(f"{engine.WORKFLOWS_DIR}/")
        else workflow.body
    )
    explicit_invocation = f"read and execute {body_target}"

    resources: List[SkillResource] = [
        SkillResource(
            relative_path="reference/canonical-body.md",
            kind="reference",
            content=(
                f"# Canonical body pointer\n\n"
                f"The authoritative instruction for `{workflow.command}` is @{body_target}.\n"
                f"This skill package never duplicates that content; it points at it.\n"
            ),
        ),
        SkillResource(
            relative_path="scripts/verify_digest.py",
            kind="script",
            content=_render_digest_verify_script(name, semantic_digest),
        ),
    ]
    if extra_resources:
        resources.extend(extra_resources)

    main_content = _render_skill_main_file(
        workflow,
        trigger,
        semantic_digest,
        explicit_invocation,
        resources,
        target_layout=target_layout,
    )

    return SkillPackage(
        name=name,
        skill_dir=skill_dir,
        trigger_description=trigger,
        semantic_digest=semantic_digest,
        explicit_invocation=explicit_invocation,
        main_file_content=main_content,
        resources=resources,
        main_budget_bytes=main_budget_bytes,
    )


def _render_digest_verify_script(name: str, expected_digest: str) -> str:
    """A deterministic, self-contained script that verifies the skill's parity digest.

    It has no external dependencies (stdlib only) and is directly testable: given the
    expected digest baked in, it exits 0 when a supplied digest matches and 1 otherwise.
    """
    return (
        "#!/usr/bin/env python3\n"
        '"""Deterministic parity-digest verifier for the '
        + name
        + ' skill package."""\n'
        "from __future__ import annotations\n"
        "import sys\n"
        "\n"
        f'EXPECTED_DIGEST = "{expected_digest}"\n'
        "\n"
        "\n"
        "def verify(observed: str) -> bool:\n"
        '    """Return True iff the observed semantic digest matches the baked-in expected one."""\n'
        "    return observed == EXPECTED_DIGEST\n"
        "\n"
        "\n"
        "def main(argv: list[str]) -> int:\n"
        "    observed = argv[1] if len(argv) > 1 else ''\n"
        "    return 0 if verify(observed) else 1\n"
        "\n"
        "\n"
        'if __name__ == "__main__":\n'
        "    raise SystemExit(main(sys.argv))\n"
    )


def validate_skill_package(package: SkillPackage) -> List[str]:
    """Validate a generated skill package. Returns a list of finding strings (empty = ok).

    Checks (falsifiable):
    - main file starts with YAML frontmatter and has description + semantic-digest fields;
    - trigger description distinguishes use vs non-use ("Use when" AND "Do not use");
    - every resource reference in the router body resolves to a package file;
    - the main file meets the byte budget;
    - the router carries the canonical semantic digest (authority link), not inlined steps;
    - an explicit runtime invocation is present.
    """
    findings: List[str] = []
    text = package.main_file_content
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        findings.append("SKILL.md missing opening YAML frontmatter fence")
    else:
        closing = -1
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                closing = idx
                break
        if closing == -1:
            findings.append("SKILL.md missing closing YAML frontmatter fence")
        else:
            fm = "\n".join(lines[1:closing])
            if "description:" not in fm:
                findings.append("SKILL.md frontmatter missing description")
            if "semantic-digest:" not in fm:
                findings.append("SKILL.md frontmatter missing semantic-digest")

    if "Use when" not in package.trigger_description:
        findings.append("trigger description lacks affirmative 'Use when' clause")
    if "Do not use" not in package.trigger_description:
        findings.append("trigger description lacks negative 'Do not use' clause")

    # Every referenced resource path must resolve to a real package file.
    declared = {r.relative_path for r in package.resources}
    for rel in re.findall(r"`([^`]+)`", text):
        # Skip the digest backtick and any non-path token.
        if "/" in rel and not rel.startswith(("http", "@")):
            if rel not in declared and rel != package.semantic_digest:
                findings.append(f"router references resource '{rel}' not in package")

    if not package.within_budget():
        findings.append(
            f"SKILL.md {package.main_file_bytes()} bytes exceeds budget "
            f"{package.main_budget_bytes}"
        )

    if package.semantic_digest not in text:
        findings.append("router does not carry the canonical semantic digest")

    if package.explicit_invocation not in text:
        findings.append("router does not carry the explicit runtime invocation")

    return findings


def check_authority_not_inlined(
    package: SkillPackage, canonical_body_text: str
) -> List[str]:
    """E-03: authoritative runtime behavior must NEVER live only in SKILL.md prose.

    The router must POINT at the canonical body (via read-and-execute + digest), not
    inline its authoritative steps. Returns findings if the router appears to embed the
    canonical body content rather than reference it.
    """
    findings: List[str] = []
    body = canonical_body_text.strip()
    if not body:
        return findings
    # If a substantial run of the canonical body is copied verbatim into the router, the
    # authority has leaked into the wrapper.
    sample = body[:200]
    if sample and sample in package.main_file_content:
        findings.append(
            "authoritative canonical body content is inlined into SKILL.md (must reference, not inline)"
        )
    return findings


# ==================================================================================================
# Per-host adapter metadata (E-02) - EXTENDS engine.py's shim generator
# ==================================================================================================


@dataclass
class HostAdapter:
    """Evidence-gated adapter metadata for a single host.

    Fields/commands here are advertised as SUPPORTED only where the Order-10 registry
    marks the capability non-`unverified`. Unverified rows are still generated, but flagged
    `unverified` and never advertised as supported.
    """

    host: str
    exact_version: str
    pointer_file: str
    skill_dir: str
    role_map: Dict[str, str]
    supported_features: List[str]
    unverified_features: List[str]
    fallback_runtime: str
    capability_reasons: Dict[str, List[str]] = field(default_factory=dict)
    is_v1: bool = False

    def advertises_supported(self, feature: str) -> bool:
        return feature in self.supported_features

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "exact_version": self.exact_version,
            "pointer_file": self.pointer_file,
            "skill_dir": self.skill_dir,
            "role_map": dict(self.role_map),
            "supported_features": sorted(self.supported_features),
            "unverified_features": sorted(self.unverified_features),
            "fallback_runtime": self.fallback_runtime,
            "capability_reasons": {
                k: list(v) for k, v in self.capability_reasons.items()
            },
            "is_v1": self.is_v1,
        }


def map_feature_to_role(host: str, feature: str) -> Optional[str]:
    """Map a native host feature to its canonical role, or None if the host lacks it."""
    return HOST_FEATURE_ROLE_MAP.get(host, {}).get(feature)


def resolve_role_target(host: str, role: str) -> str:
    """Resolve how a host serves a canonical role.

    Returns the native feature name if the host has one for that role, else the external
    runtime-coordination fallback command (never silently absent).
    """
    for feature, mapped_role in HOST_FEATURE_ROLE_MAP.get(host, {}).items():
        if mapped_role == role:
            return feature
    return HOST_NONINTERACTIVE_RUNTIME.get(host, "external runtime coordination")


def build_host_adapter(
    host: str,
    registry: HostCapabilityRegistry,
    exact_version: str,
    candidate_features: Optional[Sequence[str]] = None,
    now: Any = None,
) -> HostAdapter:
    """Build one host adapter, gating every supported claim through the Order-10 registry.

    A feature is placed in ``supported_features`` ONLY when
    ``registry.query_capability(...).is_supported`` is True (i.e. the registry did NOT
    return `unverified`). Otherwise it is placed in ``unverified_features`` with the
    registry's reasons recorded. Features the host has no native mapping for are omitted
    from both lists and served by the fallback runtime via :func:`resolve_role_target`.
    """
    if host not in HOST_FEATURE_ROLE_MAP:
        raise AdapterGenerationError(f"Unknown adapter host '{host}'")

    feats = (
        list(candidate_features)
        if candidate_features is not None
        else list(HOST_FEATURE_ROLE_MAP[host].keys())
    )

    supported: List[str] = []
    unverified: List[str] = []
    reasons: Dict[str, List[str]] = {}
    role_map: Dict[str, str] = {}

    for feat in feats:
        role = map_feature_to_role(host, feat)
        if role is not None:
            role_map[feat] = role
        evaluation: CapabilityEvaluation = registry.query_capability(
            host=host,
            exact_version=exact_version,
            feature=feat,
            now=now,
        )
        if evaluation.is_supported and evaluation.status != STATUS_UNVERIFIED:
            supported.append(feat)
        else:
            unverified.append(feat)
            reasons[feat] = list(evaluation.reasons)

    return HostAdapter(
        host=host,
        exact_version=exact_version,
        pointer_file=HOST_POINTER_FILE.get(host, "AGENTS.md"),
        skill_dir=HOST_SKILL_DIR.get(host, SHARED_SKILLS_DIR),
        role_map=role_map,
        supported_features=supported,
        unverified_features=unverified,
        fallback_runtime=HOST_NONINTERACTIVE_RUNTIME.get(
            host, "external runtime coordination"
        ),
        capability_reasons=reasons,
        is_v1=host in V1_HOSTS,
    )


@dataclass
class AdapterBundle:
    """The complete generated artifact set for a repo: shims (reused from engine.py),
    skill packages, and per-host adapters."""

    shims: Dict[str, str]
    skill_packages: List[SkillPackage]
    host_adapters: Dict[str, HostAdapter]

    def skill_files(self) -> Dict[str, str]:
        files: Dict[str, str] = {}
        for pkg in self.skill_packages:
            files.update(pkg.to_files())
        return files

    def to_dict(self) -> dict[str, Any]:
        return {
            "shim_paths": sorted(self.shims.keys()),
            "skill_packages": [p.to_dict() for p in self.skill_packages],
            "host_adapters": {h: a.to_dict() for h, a in self.host_adapters.items()},
        }


def generate_adapter_bundle(
    workflows: List[Workflow],
    source_root: Any,
    registry: HostCapabilityRegistry,
    versions: Optional[Mapping[str, str]] = None,
    target_layout: str = "aw",
    skill_dir: str = SHARED_SKILLS_DIR,
    hosts: Sequence[str] = ALL_ADAPTER_HOSTS,
) -> AdapterBundle:
    """Generate the whole artifact bundle.

    Command shims REUSE :func:`agent_workflows.engine.generate_shim_members` (the existing
    canonical shim-generation path) - this module does NOT re-implement shim rendering.
    Skill packages are added as a NEW artifact family (E-01). Per-host adapter metadata is
    generated with every `supported` claim gated by the Order-10 registry (E-02).
    """
    # REUSE engine.py's shim generator - do not fork.
    shims = generate_shim_members(workflows, source_root, target_layout=target_layout)

    skill_packages = [
        build_skill_package(w, skill_dir=skill_dir, target_layout=target_layout)
        for w in workflows
        if classify_discovery_policy(w, target_layout=target_layout)
        == POLICY_SKILL_ENTRY_POINT
    ]

    versions = versions or {}
    adapters: Dict[str, HostAdapter] = {}
    for host in hosts:
        adapters[host] = build_host_adapter(
            host,
            registry,
            exact_version=versions.get(host, "1.0.0"),
        )

    return AdapterBundle(
        shims=shims,
        skill_packages=skill_packages,
        host_adapters=adapters,
    )


# ==================================================================================================
# Skill-authority discovery policy (E-03)
# ==================================================================================================


def classify_discovery_policy(workflow: Workflow, target_layout: str = "aw") -> str:
    """Classify a workflow as a thin skill entry point vs a simple generated command.

    Complex workflows (whose canonical shim body exceeds the simple-command budget, or
    which carry a lens / non-trivial argument handling) become thin SKILL entry points;
    simple informational commands may remain generated commands.
    """
    if workflow.lens:
        return POLICY_SKILL_ENTRY_POINT
    body = shim_body(
        workflow.command, workflow, "opencode", target_layout=target_layout
    )
    if len(body.encode("utf-8")) > SIMPLE_COMMAND_BUDGET_BYTES:
        return POLICY_SKILL_ENTRY_POINT
    if workflow.arg_hint and workflow.arg_hint != "none":
        return POLICY_SKILL_ENTRY_POINT
    return POLICY_GENERATED_COMMAND


def disabled_skill_still_invocable(package: SkillPackage) -> bool:
    """E-03: disabling a skill must leave the explicit runtime invocation usable.

    A skill is "disable-safe" when its explicit invocation references the canonical body
    directly (a read-and-execute pointer), so removing/disabling the skill package does
    not remove the ability to run the workflow.
    """
    inv = package.explicit_invocation.strip()
    return inv.startswith("read and execute ") and (
        ".aw/system/workflows/" in inv or ".agents/workflows/" in inv
    )


def build_support_table(adapters: Mapping[str, HostAdapter]) -> str:
    """Generate a support table FROM the adapters (which are gated by the registry).

    Documented prose generated from this table cannot exceed a recorded claim: a feature
    shows `supported` only if the registry promoted it; everything else shows `unverified`.
    This is produced in-code/tests (per the scope fence, AGENTS.md is not hand-edited here).
    """
    lines = [
        "| Host | Version | Feature | Role | Status |",
        "|---|---|---|---|---|",
    ]
    for host in sorted(adapters):
        a = adapters[host]
        for feat in sorted(set(a.supported_features) | set(a.unverified_features)):
            role = a.role_map.get(feat, "(fallback runtime)")
            status = "supported" if feat in a.supported_features else STATUS_UNVERIFIED
            lines.append(f"| {host} | {a.exact_version} | {feat} | {role} | {status} |")
    return "\n".join(lines)


def get_isolation_capabilities(host: str, platform_name: Optional[str] = None) -> Any:
    """The x03wgn Layer 4 ISOLATION capability snapshot for `host` (wtiso-07 `1o4eif` E-02).

    A thin pass-through to `host_sandbox_profile.detect_host_capabilities` so an adapter
    consumer can read the snapshot without importing the sandbox module directly and
    without this module reimplementing sandbox semantics (x03wgn Section 6 Layer 4: "the
    shared orchestrator chooses the strongest safe protocol supported by the adapter";
    adapters stay thin).

    This is deliberately SEPARATE from the `host_capability_registry` skill-probe evidence
    registry, which answers a different question (which SKILL features a host verifiably
    supports). Isolation capability is decided by an EXECUTED sandbox probe, not by a
    recorded evidence row, so the two must not be conflated.

    Imported lazily to keep module import cost off the default path: the sandbox probe
    module is only needed when someone actually asks about isolation.
    """
    from agent_workflows.host_sandbox_profile import detect_host_capabilities

    return detect_host_capabilities(host, platform_name)


# Re-export the engine symbols this module extends, so consumers/tests can confirm the
# reused (not forked) shim-generation path.
__all__ = [
    "SHARED_SKILLS_DIR",
    "V1_HOSTS",
    "ALL_ADAPTER_HOSTS",
    "SkillResource",
    "SkillPackage",
    "HostAdapter",
    "AdapterBundle",
    "AdapterGenerationError",
    "build_skill_package",
    "validate_skill_package",
    "check_authority_not_inlined",
    "compute_workflow_semantic_digest",
    "map_feature_to_role",
    "resolve_role_target",
    "build_host_adapter",
    "generate_adapter_bundle",
    "classify_discovery_policy",
    "disabled_skill_still_invocable",
    "build_support_table",
    "get_isolation_capabilities",
    # extended engine.py symbols (reused, not forked):
    "generate_shim_members",
    "shim_body",
    "validate_shim_grammar",
    "COMMAND_SHIM_DIRS",
    # Order-10 gate + safety guards (consumed):
    "SafetyError",
    "assert_contained",
    "assert_isolated_base",
]
