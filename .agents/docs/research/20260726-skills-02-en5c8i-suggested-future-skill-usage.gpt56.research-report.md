---
id: en5c8i
created: 20260802
set: skills
order: 02
topic: []
model: gpt56
kind: research-report
status: reference
outcome: informational
summary: Migrated from 20260726-skills-02-en5c8i-suggested-future-skill-usage.gpt56.research-report.md.
consumed-by: []
---
# Suggested Future Skill Usage for `agent-workflows`

## Executive recommendation

`agent-workflows` should make Agent Skills the canonical delivery format and reduce slash-command files to temporary compatibility adapters.

The right design is not one skill per existing manifest row. It is a compact set of task-oriented skills:

- Convert each real, user-invoked capability into a skill.
- Keep assessment lenses inside one `assess` skill.
- Keep advisory personas inside one `advise` skill.
- Fold duplicate modes into their parent skills:
  - `release-review-plan` becomes a mode of `release-review`.
  - `plan-review-long` becomes the internal progressive-disclosure structure of `plan-review`.
  - `assess-all` becomes the multi-concern mode of `assess`.
  - `list-workflows` becomes part of `getting-started` plus deterministic CLI catalog output.
- Keep repository conventions, durable state, deterministic utilities, and installer ownership outside skills.

This changes the conceptual model from:

> one neutral workflow body, plus host-specific command shims, plus a fallback instruction to read a path

to:

> one portable skill package per capability, natively discovered by most hosts, plus a generated Claude mirror and optional legacy command adapters

The existing draft external-delivery spec is correct that catalog rows should not become individual skills. It is too conservative, however, in classifying `assess`, `assess-all`, and `advise` as poor skill candidates. A skill is specifically designed to package an on-demand procedure with references, scripts, templates, and variants. The shared-harness-plus-lenses and shared-harness-plus-personas designs map naturally to that format.

This report is based on repository commit `e6f8522c8f15e6d7af43e5fa983ddf68b343173c`, dated July 25, 2026.

## 1. Why skills should become canonical

The repository currently has 58 manifest rows:

- 20 user-facing workflow or mode rows
- 31 assessment catalog rows
- 7 advisory persona catalog rows

Only 17 or fewer physical skills are needed. The current 58-row surface mixes four different concepts:

1. User-invoked capabilities
2. Modes of a capability
3. Catalog data
4. Host-specific command names

Agent Skills provide the missing packaging boundary. A skill folder can contain:

- a concise `SKILL.md` entry point;
- detailed reference files loaded only when needed;
- deterministic scripts;
- templates and other output assets.

That matches the existing repository architecture unusually well. The current modular release-review phases, assessment lenses, advisory personas, templates, and deterministic tools already have the right functional boundaries. Most of the work is relocation, metadata, path resolution, installation, and compatibility handling rather than prompt redesign.

Skills also correct a factual statement in the current workflow index. The index says Cursor, Codex, Antigravity, and Copilot have no repository-file invocation mechanism and must use “read and execute.” That is no longer true. All now support Agent Skills. Claude Code also documents that custom commands have been merged into skills, while retaining existing `.claude/commands/` compatibility.

## 2. Cross-agent discovery architecture

### 2.1 Canonical source path

Use this as the canonical tracked source:

```text
.agents/skills/<skill-name>/
```

This path is natively discovered at project scope by:

- OpenCode
- Codex
- Cursor
- Gemini CLI
- Antigravity
- GitHub Copilot

Claude Code's documented project path is `.claude/skills/`, not `.agents/skills/`. Therefore, generate a byte-equivalent or content-equivalent Claude mirror:

```text
.claude/skills/<skill-name>/
```

The mirror must be installer-owned and generated from `.agents/skills/`. It must never become a second manually maintained source.

### 2.2 User-global delivery

For an optional user-global installation:

| Destination | Hosts covered |
|---|---|
| `~/.agents/skills/` | OpenCode, Codex, Cursor, Gemini CLI, GitHub Copilot |
| `~/.claude/skills/` | Claude Code |
| `~/.gemini/config/skills/` | Antigravity |

Global installation must remain explicit and consent-gated. Local global skills do not automatically appear in every cloud execution environment. Repository-scoped skills are the dependable route for cloud agents because the skills travel with the cloned repository.

### 2.3 Canonical frontmatter

Keep the canonical `SKILL.md` frontmatter within the Agent Skills standard:

```yaml
---
name: assess
description: Assess one or more repository concerns and produce a reviewable implementation plan. Use when the user asks to assess, audit, or deeply review security, testing, accessibility, architecture, documentation, or another supported concern without implementing fixes.
license: MIT
metadata:
  agent-workflows-version: "..."
---
```

Do not make cross-agent behavior depend on host-specific fields such as:

- `disable-model-invocation`
- `argument-hint`
- `context`
- `agent`
- `paths`
- host-specific `allowed-tools` syntax

Those fields are useful in some hosts, but they are not uniformly portable. Where a host-specific policy is valuable, generate a host adapter or metadata overlay. Keep the core skill valid when every extension is ignored.

For expensive or consequential skills, put the invocation boundary directly in the portable description and body:

- “Use only when the user explicitly requests a full release review.”
- “Never publish, push, tag, deploy, or submit an HPC job without the skill's explicit human gate.”

This is more portable than assuming every host honors an explicit-only metadata field.

## 3. Recommended skill inventory

### 3.1 Complete conversion map

| Current surface | Recommended disposition | Resulting skill or component | Reason |
|---|---|---|---|
| `release-review` | Move | `release-review` skill | Clear, on-demand, complex task; existing phase modularity maps directly to progressive disclosure. |
| `release-review-plan` | Merge | Mode inside `release-review` | Same body and policies; it differs only by stopping before implementation. A separate skill would duplicate discovery metadata and invite drift. |
| `plan-review` | Move and restructure | `plan-review` skill | Strong skill candidate. Use the modular orchestration as the actual skill design. |
| `plan-review-long` | Merge and retire as a public capability | Internal references in `plan-review` | It is an implementation strategy for context reliability, not a distinct user goal. |
| `verify-execution` | Move | `verify-execution` skill | Bounded, explicit post-execution audit with clear inputs and outputs. |
| `getting-started` | Move and broaden | `getting-started` skill | Useful onboarding and routing surface, especially because internal lens and persona catalogs are not separately visible as skills. |
| `list-workflows` | Merge and retire as a skill | `getting-started` reference plus `aw skills list` | Native hosts already list skills. Keep a deterministic CLI catalog for version and detailed variants. |
| `whatnext` | Move | `whatnext` skill | Distinct read-mostly repository survey and recommendation task. |
| `handoff` | Move | `handoff` skill | Distinct session-continuity workflow with specific privacy and storage rules. |
| `verify` | Move | `verify` skill with `scripts/run_checks.py` | Ideal skill: judgment in instructions, deterministic discovery and execution in a script. |
| `spec` | Move | `spec` skill | Clear front-of-funnel artifact creation task. |
| `incident` | Move | `incident` skill | Clear post-incident analysis task with durable outputs and guardrails. |
| `release-notes` | Move | `release-notes` skill | Clear release-preparation task; keep publishing outside its authority. |
| `migrate` | Move | `migrate` skill | Clear assess-and-plan procedure for high-risk migrations. |
| `benchmark` | Move | `benchmark` skill with `scripts/bench_env.py` | Strong match for instructions plus deterministic helper. |
| `setup-repo` | Move | `setup-repo` skill with scripts and assets | Clear interactive configuration task; deterministic helpers and templates bundle naturally. |
| `scaffold` | Move and retarget | `scaffold-agent-workflow` or `scaffold-agent-skill` skill | It should create skills, assessment lenses, advisory personas, and supporting files rather than command shims. |
| `assess` | Move and broaden | `assess` skill | The current harness is exactly the skill entry point. Lenses become references. |
| `assess-all` | Merge | Multi-concern mode inside `assess` | Same harness, same lenses, same output class. The difference is selection and synthesis. |
| `assess-<concern>` rows | Keep as catalog data, not skills | `assess/references/lenses/*.md` plus catalog metadata | Thirty-one separate skills would flood discovery, duplicate the harness, and weaken cross-concern consistency. |
| `advise` | Move | `advise` skill | Interactive coaching is still an on-demand reusable procedure. |
| `advise-<persona>` rows | Keep as catalog data, not skills | `advise/references/personas/*.md` plus catalog metadata | Personas are variants selected by one skill, not standalone capabilities. |

### 3.2 Net result

The public skill set should contain approximately 15 to 17 skills, depending on whether onboarding and scaffolding remain separately exposed:

```text
assess
advise
benchmark
getting-started
handoff
incident
migrate
plan-review
release-notes
release-review
scaffold-agent-skill
setup-repo
spec
verify
verify-execution
whatnext
```

That is a better discovery surface than 58 entries. It preserves every substantive capability while removing modes and catalog records from the top-level namespace.

## 4. Detailed treatment of assessments

### 4.1 Assessments should become a skill

The current draft spec says assessor or persona workflows may need a different mapping. They do need a different mapping, but not a different delivery mechanism.

The correct mapping is:

```text
.agents/skills/assess/
├── SKILL.md
├── references/
│   ├── catalog.md
│   ├── multi-concern.md
│   ├── fix-decision-policy.md
│   ├── personas.md
│   ├── prose-style.md
│   └── lenses/
│       ├── accessibility.md
│       ├── api-design.md
│       ├── architecture.md
│       ├── ...
│       └── use-cases.md
├── scripts/
│   └── scan_secrets.py
└── assets/
    ├── closing-report.md
    ├── findings.csv
    ├── ipd.md
    └── run-report.md
```

`SKILL.md` should contain:

- the assessment contract;
- single-concern versus multi-concern mode selection;
- concern resolution and alias rules;
- non-execution boundary;
- required outputs;
- the instruction to load only the selected lens or lenses;
- the closing gate.

It should not contain all 31 rubrics. Those belong in `references/lenses/`.

### 4.2 Do not make one skill per concern

Creating `assess-security`, `assess-testing`, and every other concern as separate skills would cause four problems:

1. Discovery bloat: skill metadata is loaded before activation.
2. Harness drift: every concern would need to preserve the same non-execution, evidence, output, and IPD rules.
3. Poor synthesis: `assess-all` would need cross-skill orchestration and shared state across independently packaged capabilities.
4. Naming competition: generic host-provided skills such as security review or code review could collide with a large family.

The current shared-harness design is correct. Preserve it inside one skill.

### 4.3 Merge `assess-all`

The existing `assess-all` workflow adds selection, cost confirmation, de-duplication, conflict resolution, and one consolidated IPD. Those are a mode of assessment, not a separate capability.

Recommended invocation model:

- “Use the assess skill for security.”
- “Assess testing in `src/`.”
- “Assess security, privacy, and data exfiltration together.”
- “Run a full assessment across all concerns.”

The skill resolves the request into:

- `single` mode;
- `subset` mode;
- `group` mode;
- `all` mode.

For multi-concern modes, it loads `references/multi-concern.md` in addition to the selected lenses.

## 5. Detailed treatment of advisory personas

`advise` should also become one skill:

```text
.agents/skills/advise/
├── SKILL.md
└── references/
    ├── catalog.md
    └── personas/
        ├── architect.md
        ├── domain-expert.md
        ├── naive-user.md
        ├── red-teamer.md
        ├── skeptic.md
        ├── spec-editor.md
        └── staff-engineer.md
```

The main skill contains the dialogue contract, consent boundary, artifact-editing restriction, and session-summary output. It loads exactly one persona charter.

Do not publish each persona as a separate skill. A persona alone does not define the task lifecycle, consent model, or durable output. Making it a separate skill would either lose those guarantees or duplicate them seven times.

The skill description should mention common trigger language, including:

- “advise me”
- “grill this plan”
- “act as a skeptic”
- “interrogate this architecture”
- “coach me as a staff engineer”
- “review the requirements with a spec editor”

This preserves natural invocation without requiring a portable argument-substitution mechanism.

## 6. What should stay outside skills

### 6.1 `AGENTS.md` and native instruction mirrors

Keep always-applicable repository contracts in `AGENTS.md`, including:

- the execution and commit contract;
- plan lifecycle rules;
- durable research and walkthrough rules;
- inter-agent communication safety;
- upload-ready prompt requirements;
- deterministic leak-sanitizer requirement;
- self-contained interactive question requirements;
- repository-specific writing rules.

Remove the workflow index and “read and execute this path” routing instructions from the always-loaded block. Skills are natively discoverable, so duplicating the catalog in `AGENTS.md` wastes context and creates drift.

Continue mirroring the managed always-on block into existing `CLAUDE.md` and `GEMINI.md` files where needed. `AGENTS.md` has broad support, but not every host surface treats every native instruction filename identically. These files are compatibility adapters for durable rules, not workflow carriers.

For GitHub Copilot, `AGENTS.md` is supported in several agent surfaces, while `.github/copilot-instructions.md` remains the broadest repository-instruction path across Copilot Chat and cloud surfaces. The installer should offer a managed section there when Copilot coverage is requested.

### 6.2 Durable project state

Keep these structures substantially as they are:

```text
.agents/plans/
.agents/docs/
.agents/prompts/
.agents/comms/
workflow-artifacts/
```

They are not executable capabilities. They are project state, evidence, lifecycle, and communication conventions. Putting them inside skill folders would make generated project records look like installed skill resources and would impair stable paths and version control.

Skills may create, read, or update these structures according to their contracts, but they should not own the structures as private skill state.

### 6.3 Deterministic CLI and Python package

Keep deterministic operations in Python:

- install, update, uninstall, and status;
- repository registration and multi-repository setup;
- ownership manifest and drift detection;
- plan status and filename normalization;
- leak sanitization;
- communications validation;
- test-command discovery and execution;
- benchmark environment collection;
- secret scanning.

The skill should tell the agent when to run a script and how to interpret its output. It should not reimplement deterministic behavior in prose.

### 6.4 Source repository documentation and governance

Keep these root documents:

- `README.md`
- `ARCHITECTURE.md`
- `DECISIONS.md`
- `GUIDING_PRINCIPLES.md`
- `CONTRIBUTING.md`
- `RELEASING.md`
- `CHANGELOG.md`
- `CITATION.cff`
- `LICENSE`
- `NOTICE`

They document the product, contribution model, and decision history. They are not skill runtime resources.

## 7. Recommended physical layout

```text
agent-workflows/
├── .agents/
│   ├── skills/                         # canonical portable skill source
│   │   ├── assess/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   ├── scripts/
│   │   │   └── assets/
│   │   ├── advise/
│   │   ├── release-review/
│   │   ├── plan-review/
│   │   ├── verify/
│   │   └── ...
│   ├── agent-workflows/
│   │   ├── catalog.json                # installer and CLI catalog
│   │   ├── VERSION
│   │   └── managed-sections.json       # target-side ownership record
│   ├── plans/
│   ├── docs/
│   ├── prompts/
│   └── comms/
├── .claude/
│   ├── skills/                         # generated mirror, optional by install mode
│   └── commands/                       # legacy-only generated shims
├── .opencode/
│   └── commands/                       # legacy-only generated shims
├── agent_workflows/
├── tests/
├── AGENTS.md
└── ...
```

### 7.1 Catalog design

Replace the Markdown table as the machine-readable source of truth with a structured catalog, for example:

```json
{
  "schema_version": 2,
  "framework_version": "1.3.0",
  "skills": [
    {
      "name": "assess",
      "path": ".agents/skills/assess",
      "modes": ["single", "subset", "group", "all"],
      "aliases": ["audit"],
      "variants": {
        "type": "lens",
        "directory": "references/lenses"
      }
    }
  ]
}
```

Generate human-readable catalog documentation from this data. Do not parse a large Markdown table as the long-term installation API.

The catalog should distinguish:

- skill;
- mode;
- variant;
- alias;
- host adapter;
- deterministic dependency.

This prevents the present confusion where all are represented as command rows.

## 8. Slash commands and compatibility

### 8.1 What users should retain

Preserve familiar names:

- `release-review`
- `plan-review`
- `verify`
- `assess`
- `advise`
- `setup-repo`

Claude Code and Cursor expose skills through slash-style invocation natively. Claude Code explicitly documents that custom commands and skills now share the same invocation surface, with skills taking precedence when names collide. Therefore, migrating a Claude command to a same-named skill preserves the user's `/name` habit.

Other hosts use different explicit selectors:

- Codex: skill selector or `$skill-name`
- Gemini CLI: skill activation and `/skills` management
- OpenCode: native skill tool, selected by the model
- GitHub Copilot: model selection based on the skill description
- Antigravity: model activation, with user consent

Natural-language invocation must remain first class:

- “Run release-review.”
- “Assess security.”
- “Use the skeptic persona to advise me on this plan.”

Do not make correctness depend on `$ARGUMENTS`.

### 8.2 Legacy shim policy

Keep `.opencode/commands/` and `.claude/commands/` only as a transition feature:

1. Existing installations continue to work.
2. A new `--legacy-command-shims` option installs or retains them.
3. Default new skill-based installs do not require them.
4. Shims should invoke the skill by name or point to its `SKILL.md`, not to `.agents/workflows/`.
5. Warn once when updating a legacy install.
6. Remove installer-owned shims only after verifying the corresponding skill is installed.
7. Preserve user-edited or unowned command files.

For Claude, the command shim can be retired quickly because the same-named skill supplies `/name`. For OpenCode, retain the optional shim longer if explicit slash invocation is an important user affordance, even though skill discovery works.

## 9. Installer and package changes

The installer is currently deeply coupled to `.agents/workflows/`, `index.md`, generated command shims, and in-repository version detection. The migration requires deliberate changes.

### 9.1 Source and package resolution

Change packaged data from:

```text
agent_workflows/_data/.agents/workflows/
```

to:

```text
agent_workflows/_data/.agents/skills/
agent_workflows/_data/.agents/agent-workflows/catalog.json
agent_workflows/_data/.agents/agent-workflows/VERSION
```

Keep a compatibility reader for the old packaged path through at least one major migration window.

### 9.2 Install modes

Offer explicit modes:

| Mode | Writes | Use |
|---|---|---|
| `repo` | `.agents/skills/`, `.claude/skills/` as needed, managed instruction blocks, state scaffolding | Maximum project and cloud portability |
| `user` | user-global skill locations, global ownership manifest | Personal reuse across local repositories |
| `hybrid` | user-global skills plus minimal repo state and cloud adapters | Local low-footprint use with selected repo support |
| `legacy` | `.agents/workflows/` and command shims | Compatibility and downgrade only |

Do not silently choose user-global installation. It changes personal agent configuration and must require explicit consent.

### 9.3 Ownership and drift

Retain the existing ownership-manifest principles:

- path-parameterized;
- hash what the installer actually wrote;
- preserve user drift;
- persist decline decisions;
- atomic updates;
- safe uninstall.

Extend each record with:

- scope: repo or user;
- artifact type: skill, mirror, legacy shim, managed section, state scaffold;
- canonical skill name;
- source version;
- source digest;
- generated-from path;
- host;
- install mode.

The global installation needs its own global ownership manifest. A repository manifest cannot safely own files shared by multiple repositories.

### 9.4 Mirrors

Treat `.claude/skills/<name>` as a generated mirror of `.agents/skills/<name>`:

- compare against the last-written hash;
- regenerate only installer-owned, unchanged files;
- never overwrite a user-edited mirror without consent;
- remove only when no installed scope still owns it.

Avoid symlinks as the default. Some hosts support them, but Windows, packaging, cloud clones, and archive distribution make real files more dependable.

## 10. Content migration details

### 10.1 Convert READMEs into entry points

The existing per-workflow `README.md` files mainly explain invocation. Skills should not carry redundant README files. Use:

- `SKILL.md` for the capability entry point;
- `references/` for instructions read on demand;
- `scripts/` for helpers;
- `assets/` for copied templates.

Delete or stop shipping per-skill README files unless a file contains runtime instructions that belong in `SKILL.md`.

### 10.2 Resolve paths from the skill root

Every skill instruction that currently names `.agents/workflows/...` must be rewritten to use relative paths from the skill root.

Examples:

```text
../release-review/fix-decision-policy.md
```

should not remain as a cross-skill dependency. Instead:

- package the needed policy inside the skill;
- generate the duplicate from one authoring source; or
- make a small essential rule explicit in both skills and enforce equivalence with a test.

Cross-skill filesystem references are fragile because hosts differ in what directories become readable when a skill activates. A skill should remain functional when installed alone.

### 10.3 Shared policy strategy

Use a build-time single source of truth:

```text
agent_workflows/skill_sources/shared/
```

or an equivalent authoring directory for:

- Fix Bar;
- persona definitions reused by review and assessment;
- prose style;
- common closing-report rules;
- standard artifact naming.

During build or release, materialize the required shared files into each independently installable skill. Validate generated copies against the canonical digest. This preserves standalone installation without accepting manual duplication.

Do not make one “shared-policy” skill that must activate before another skill. Skill selection is not a dependency resolver.

### 10.4 Templates are assets

Files that an agent copies or fills should move to `assets/`, including:

- IPD template;
- run-report template;
- findings CSV;
- release-review report templates;
- setup repository README and lifecycle templates.

Files the agent reads to make decisions belong in `references/`.

## 11. What should not be converted

Do not convert these into skills:

- every assessment lens as a separate skill;
- every advisory persona as a separate skill;
- `VERSION`;
- the install ownership manifest;
- the plan lifecycle directories;
- docs, research, and walkthrough trees;
- prompt lifecycle directories;
- inter-agent comms folders;
- run artifacts;
- CI workflows;
- package release metadata;
- deterministic CLI commands that need no model judgment;
- always-applicable repository rules from `AGENTS.md`;
- a separate `release-review-plan` skill;
- a separate `plan-review-long` skill;
- a separate `assess-all` skill;
- a standalone `list-workflows` skill.

## 12. Phased migration plan

### Phase 1: Catalog and validation foundation

1. Add a structured skill catalog.
2. Add schema validation for the catalog.
3. Add Agent Skills validation for every skill.
4. Add tests that names, descriptions, paths, resources, and catalogs agree.
5. Add tests limiting skill count and description budget.

### Phase 2: Convert three representative capabilities

Convert:

1. `verify`, to test bundled scripts and permissions.
2. `assess`, to test lenses, templates, single and multi-concern modes.
3. `release-review`, to test large progressive-disclosure runbooks.

These exercise almost every architectural requirement before the full migration.

### Phase 3: Host matrix validation

For each supported host, test:

- discovery at project scope;
- explicit invocation;
- implicit invocation;
- resource loading;
- script execution with normal approval behavior;
- writing expected artifacts;
- no accidental loading of unrelated lenses or phases;
- same-name collision behavior;
- cloud behavior where applicable.

Record host name, version, path, invocation, result, and date.

### Phase 4: Convert remaining capabilities

Move the remaining user-facing workflows, then fold:

- `release-review-plan`;
- `plan-review-long`;
- `assess-all`;
- `list-workflows`.

### Phase 5: Installer migration

1. Add `repo`, `user`, `hybrid`, and `legacy` modes.
2. Migrate ownership records.
3. Generate the Claude mirror.
4. Make legacy command shims optional.
5. Preserve safe downgrade to the last workflow-based release.

### Phase 6: Documentation and deprecation

1. Rewrite README examples around skills and natural language.
2. Update architecture and decisions.
3. Mark `.agents/workflows/` deprecated for one release line.
4. Stop installing workflow bodies by default.
5. Retain legacy migration and uninstall support.

## 13. Acceptance criteria

The reconfiguration is complete only when all of the following are true:

1. Every substantive current capability remains available.
2. No assessment lens or advisory persona is lost.
3. `assess` supports single, subset, group, and all-concern modes.
4. `release-review` supports planning-only and implementation modes.
5. `plan-review` uses progressive disclosure without a second public long-form capability.
6. Project skills are discovered in OpenCode, Codex, Cursor, Gemini CLI, Antigravity, GitHub Copilot, and Claude Code through the generated mirror.
7. Claude users can continue using familiar `/skill-name` invocation.
8. No portable skill depends on host-specific frontmatter for correctness.
9. Every skill works when installed independently.
10. Every script path resolves from the installed skill location.
11. Templates are treated as output assets, not eagerly loaded references.
12. Existing user-modified command shims are preserved.
13. Upgrade and uninstall remain ownership-aware and reversible.
14. Local user-global installation is never mistaken for cloud availability.
15. `AGENTS.md` contains only always-applicable repository rules, not the workflow catalog.
16. Deterministic checks remain scripts or CLI operations.
17. The old workflow installation can be detected, migrated, and safely downgraded during the compatibility window.

## 14. Bottom line

The repository should not merely wrap the existing `.agents/workflows/` files in `SKILL.md` entry points. It should use the skill migration to correct the ontology of the product:

- skills are capabilities;
- modes are internal choices;
- lenses and personas are references;
- scripts are deterministic tools;
- templates are assets;
- `AGENTS.md` carries always-on repository contracts;
- `.agents/plans`, `.agents/docs`, `.agents/prompts`, `.agents/comms`, and `workflow-artifacts` carry durable state;
- the installer and manifest own delivery, versioning, drift, and removal;
- command shims become optional compatibility adapters.

The most important practical decision is to make `.agents/skills/` canonical, generate `.claude/skills/` for Claude, and keep the assessment and advisory families consolidated. That yields native discovery across the supported agent ecosystem without sacrificing the repository's strongest existing properties: single-source policies, deterministic helpers, progressive disclosure, durable evidence, and conservative ownership.

## Sources

### Repository

- [`agent-workflows` repository](https://github.com/fariello/agent-workflows)
- [Current workflow manifest](https://github.com/fariello/agent-workflows/blob/e6f8522c8f15e6d7af43e5fa983ddf68b343173c/.agents/workflows/index.md)
- [Current architecture](https://github.com/fariello/agent-workflows/blob/e6f8522c8f15e6d7af43e5fa983ddf68b343173c/ARCHITECTURE.md)
- [Draft external-delivery and skills spec](https://github.com/fariello/agent-workflows/blob/e6f8522c8f15e6d7af43e5fa983ddf68b343173c/.agents/docs/specs/20260725-0957-01-external-delivery-and-skills.spec.md)

### Agent Skills and host documentation

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex skills](https://developers.openai.com/codex/skills)
- [GitHub Copilot agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [GitHub Copilot custom-instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support)
- [Cursor skills](https://cursor.com/docs/skills)
- [Gemini CLI skills](https://geminicli.com/docs/cli/skills/)
- [Antigravity skills](https://antigravity.google/docs/skills)
