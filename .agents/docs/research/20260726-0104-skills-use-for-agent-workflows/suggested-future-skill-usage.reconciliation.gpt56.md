# Reconciliation of the Three Suggested Future Skill Usage Reports

## Executive synthesis

The three reports agree on the architectural direction:

1. Agent Skills should become the primary reusable workflow format.
2. `.agents/skills/<skill-name>/SKILL.md` should be the canonical cross-agent project location.
3. Claude should receive a generated `.claude/skills` adapter because it does not natively use `.agents/skills`.
4. `assess` and `advise` should each be one dispatcher or harness skill, not one skill per assessment lens or advisory persona.
5. `AGENTS.md` should remain concise, always-on guidance rather than becoming a catalog of all workflows.
6. Deterministic code, durable artifacts, templates, documentation, and governance should remain outside the prose body of `SKILL.md`, while skills may reference or invoke them.
7. Compatibility shims are justified during migration and for host combinations without a tested native route.
8. Clean-delta operation requires global state and ownership tracking and must not silently modify a target repository.

The reports diverge mainly because they answer two different questions as though they were one:

- Should a capability be authored and packaged as a skill?
- Should a host expose that skill for implicit activation?

Those decisions should be separated. The consolidated recommendation is:

- Author every genuine user-facing capability as one canonical skill package.
- Merge aliases, depth variants, and stop points into modes of that skill.
- Generate host-specific exposure metadata or installation profiles from the canonical package.
- Permit implicit activation only for read-oriented, bounded workflows.
- Require explicit invocation, activation consent, and action-level confirmation for consequential workflows.
- If a host cannot enforce the required activation boundary, omit that skill from its auto-discovered installation profile and retain a thin manual shim. Do not maintain a second command-body implementation.

This preserves GPT-5.6's coherent single-source architecture while incorporating Sonnet 5's stronger safety and clean-delta controls. Gemini 3.1 Pro independently supports the same overall direction but is too abbreviated to settle most implementation choices.

## 1. Scope and method

This reconciliation compares:

- `suggested-future-skill-usage.gpt56(2).md`
- `suggested-future-skill-usage.sonnet5(1).md`
- `suggested-future-skill-usage.gemini31pro.md`

The reports were compared at four levels:

1. **Architectural claims:** canonical source, discovery paths, adapters, and installation modes.
2. **Capability disposition:** which current workflows become skills, merge into another skill, remain compatibility shims, or stay outside skills.
3. **Operational behavior:** clean-delta routing, ownership, artifact storage, activation, consent, and cloud availability.
4. **Evidence quality:** whether a statement is a repository observation, documented host behavior, proposed design, inference, or untested assumption.

Current official host documentation was also checked where a disputed host capability materially changes the recommendation. Documentation confirms capability, not successful behavior in this repository. Repository fixture tests remain necessary.

## 2. Report profiles

| Report | Primary contribution | Detail level | Main limitation |
|---|---|---:|---|
| GPT-5.6 | Complete canonical skill inventory, mode consolidation, catalog, installer, migration, and acceptance design | High | Clean-delta artifact routing and host-specific activation policy are underdeveloped |
| Sonnet 5 | Strong host delivery matrix, tracked versus clean-delta product modes, resolver contract, activation safety, and fixture protocol | High | Sometimes preserves manual commands where a canonical skill plus exposure policy is cleaner; a few host-confidence statements are outdated or overstated |
| Gemini 3.1 Pro | Independent confirmation of the main architecture and clean-delta ownership model | Low | Omits most workflow-by-workflow, metadata, migration, testing, cloud, and activation detail |

The length difference matters. Gemini's brevity is usually an omission, not disagreement. Sonnet and GPT address substantially more of the design surface.

## 3. Agreement matrix

Legend:

- **A**: explicit agreement
- **P**: partial or compatible agreement
- **O**: omitted
- **D**: divergent recommendation

| Topic | GPT-5.6 | Sonnet 5 | Gemini 3.1 Pro | Reconciled position |
|---|:---:|:---:|:---:|---|
| Skills become primary workflow delivery | A | A | A | Adopt |
| `.agents/skills` as canonical project location | A | A | A | Adopt |
| `.claude/skills` generated adapter | A | A | A | Adopt |
| Standard Agent Skills package structure | A | A | P | Adopt |
| One skill per assessment lens | Rejects | Rejects | Rejects | Do not create |
| One `assess` harness skill | A | A | A | Adopt |
| One skill per advisory persona | Rejects | Rejects | Rejects | Do not create |
| One `advise` harness skill | A | A | A | Adopt |
| Consequential capabilities are canonical skills | A | P/D | P | Yes, with restricted exposure |
| `assess-all` merges into `assess` | A | D | O | Merge as an explicit multi-concern mode |
| `release-review-plan` merges into `release-review` | A | D/P | O | Merge as a stop-after-plan mode |
| `plan-review-long` remains internal | A | O | O | Keep internal |
| `list-workflows` merges into onboarding and CLI | A | D | O | Merge into `getting-started` plus catalog CLI |
| `AGENTS.md` remains concise and always-on | A | A | A | Adopt |
| Deterministic CLI remains outside skills | A | P | O | Adopt |
| Tracked project mode | P | A | P | Adopt |
| Clean-delta user-global mode | P | A | A | Adopt |
| Sibling artifact repository in clean-delta mode | O/P | A | A | Adopt |
| Deterministic context or artifact resolver | O/P | A | P | Adopt |
| Legacy command shims during migration | A | A | A | Adopt temporarily |
| Permanent dual command and skill bodies | Rejects | Risks implying | Not specified | Reject |
| Real copies or generated mirrors by default | A | D | O | Prefer generated real files |
| Symlinks as default | Rejects as default | Recommends | O | Optional optimization only |
| Cloud versus local skill boundary | O/P | A | O | Make explicit |
| Host fixture test before promises | A | A | O | Require |

## 4. Where all three agree

### 4.1 Skills should replace slash-command-shaped workflow implementations

All three reports treat skills as the future portable abstraction. This is the most important consensus. A skill is not merely a new command file extension. It is a named capability with:

- discovery metadata;
- an instruction entry point;
- progressive disclosure;
- references, assets, and optional scripts;
- host-specific activation and invocation behavior.

The practical implication is that `.agents/workflows` should no longer be the permanent canonical runtime format once migration is complete. It may remain temporarily as a build input or generated compatibility layer, but one authoritative implementation must win.

### 4.2 `.agents/skills` is the best cross-agent canonical project path

Every report selects `.agents/skills`. Current official documentation supports it for Codex, Cursor, Gemini CLI, Antigravity, OpenCode, and GitHub Copilot. Claude remains the important exception and needs a `.claude/skills` adapter.

This common path minimizes host-specific duplication and aligns the repository with the Agent Skills standard. It does not eliminate adapters because discovery paths and supported metadata still vary.

### 4.3 Assessments and advisory personas are internal selections, not separate skills

All reports reject a skill for every lens or persona. That is the right choice because lenses and personas share:

- the same orchestration harness;
- the same evidence collection pattern;
- the same output family;
- common policy and formatting rules;
- a selection step that can be expressed as an argument or follow-up question.

Publishing each lens or persona as a skill would inflate discovery catalogs, repeat descriptions, create drift, and consume host context budgets. Keep lenses and personas as references or structured catalog records loaded by `assess` and `advise`.

### 4.4 Always-on repository guidance should stay outside skills

The reports agree that root instructions still have a distinct job. `AGENTS.md` and host-native instruction mirrors should contain only rules that should apply throughout work in the repository, such as:

- repository invariants;
- safety and consent boundaries;
- the existence and location of the skill catalog;
- artifact handling rules that apply to every task;
- minimal host bootstrap guidance.

They should not embed the full workflow catalog, every persona, or detailed workflow procedures. Doing so defeats progressive disclosure and produces a large always-on prompt.

### 4.5 Compatibility remains necessary during migration

Every report retains some fallback route. This is justified because:

- Claude uses a different canonical project path;
- older host versions may not support skills;
- cloud and local surfaces discover different locations;
- explicit invocation syntax varies;
- activation controls differ;
- clean-delta installs cannot assume repository writes.

The reconciliation narrows this consensus: retain thin generated shims, not independently authored command implementations. Every shim must delegate to the same canonical skill or generated content.

### 4.6 Clean-delta operation needs external state and ownership

Sonnet and Gemini state this most clearly. GPT's install and ownership ideas are compatible but do not fully define clean-delta artifact routing.

A clean-delta promise means more than "do not track generated files." It means the tool must not create tracked or untracked files in the target repository unless the user explicitly changes mode. Therefore the system needs:

- user-global skill installation;
- a global repository mapping;
- a global ownership manifest;
- a recovery snapshot or rollback record;
- a deterministic resolver for state and artifact locations;
- an external artifact store, preferably a sibling companion repository when versioned artifacts are desired.

## 5. Genuine divergences and their resolution

### 5.1 Packaging consequential workflows as skills

**GPT-5.6:** Converts consequential capabilities such as `setup-repo`, `migrate`, `incident`, `release-notes`, `release-review`, and scaffolding into skills.

**Sonnet 5:** Calls them manual-only and, especially on hosts without a strong disable-auto field, sometimes recommends not shipping them as skills at all.

**Gemini 3.1 Pro:** Lists some consequential capabilities as skills but does not define activation policy.

**Why they differ:** GPT optimizes for one coherent capability format. Sonnet optimizes for preventing accidental activation. These goals do not conflict if packaging and exposure are separate.

**Resolution:** Keep one canonical skill package for every real capability, including consequential ones. Generate per-host exposure:

- Claude and Cursor: use documented `disable-model-invocation: true` in generated copies for explicit-only skills.
- OpenCode: set skill permission to `ask` so the host prompts before loading the skill. This is consent-gated activation, though it is not identical to explicit-user-only invocation.
- Gemini CLI: rely on documented activation confirmation, then verify the exact prompt frequency and behavior in fixtures.
- Hosts without an adequate activation boundary: omit consequential skills from the auto-discovered profile and expose a thin manual compatibility shim.

Activation consent does not replace action consent. A skill that may edit, publish, migrate, or change configuration must still preview material actions and obtain confirmation at the point required by the workflow.

### 5.2 `assess-all`

**GPT-5.6:** Merges it into `assess`.

**Sonnet 5:** Retains it as a manual command because it is broad and costly.

**Gemini 3.1 Pro:** Does not settle the issue.

**Resolution:** Merge it into `assess` as a multi-concern mode. It shares the same harness, lenses, evidence model, and output schema. Breadth and cost are invocation-policy concerns, not reasons for a second capability implementation.

The `assess` skill should:

- accept one, several, or all concerns;
- make the all-concerns path explicit rather than infer it casually;
- show expected scope or cost before a broad run;
- request confirmation if the run is materially expensive;
- keep each concern's findings separately attributable before synthesis.

### 5.3 `release-review-plan`

**GPT-5.6:** Merges it into `release-review`.

**Sonnet 5:** Retains it as a separate second-wave skill or surface.

**Gemini 3.1 Pro:** Omits the distinction.

**Resolution:** Make it a mode of `release-review`, such as `plan-only` or `stop-after-plan`. It uses the same domain, evidence, policies, and output progression. Its distinguishing feature is a stop point, not a separate capability.

This reduces discovery noise and prevents the plan-only and execution paths from drifting.

### 5.4 `plan-review-long`

**GPT-5.6:** Treats it as an internal long-form implementation of `plan-review`.

**Sonnet 5 and Gemini 3.1 Pro:** Do not address it.

**Resolution:** Keep it internal. The public `plan-review` skill should select depth based on request, plan size, risk, or an explicit `deep` option. A user should not need to know which implementation file is longer.

### 5.5 `list-workflows`

**GPT-5.6:** Merges it into `getting-started` and a deterministic catalog command.

**Sonnet 5:** Keeps it as a portable skill.

**Gemini 3.1 Pro:** Omits it.

**Resolution:** Do not create a separate `list-workflows` skill. Native hosts already expose skill discovery, while this repository also needs to list non-skill internal selections such as lenses and personas. Use:

- `getting-started` for conversational orientation and recommendations;
- `aw skills list` or an equivalent deterministic CLI command for exact machine-readable and human-readable inventory;
- the structured catalog as the source of truth.

This avoids consuming a skill slot merely to repeat metadata already present in the catalog.

### 5.6 Product modes

**GPT-5.6:** Proposes repository, user, hybrid, and legacy installation modes.

**Sonnet 5:** Proposes two coherent product modes: tracked and clean-delta.

**Gemini 3.1 Pro:** Focuses on clean-delta behavior.

**Resolution:** Present only two user-facing product modes:

1. **Tracked mode:** repository-scoped skills and repository-local artifacts or state are allowed and managed.
2. **Clean-delta mode:** user-global skills, no target repository writes, and external artifacts and state.

Treat `legacy` as a temporary compatibility state, not a permanent product mode. Treat `hybrid` as an implementation technique or exceptional deployment profile, not a normal mode, because mixing local and global ownership makes drift and cleanup harder to explain.

### 5.7 Artifact routing

**GPT-5.6:** Correctly keeps durable state outside skill bodies but largely preserves current artifact locations.

**Sonnet 5 and Gemini 3.1 Pro:** Route clean-delta artifacts to a sibling companion repository using global mapping and ownership state.

**Resolution:** Artifact location depends on product mode:

| Concern | Tracked mode | Clean-delta mode |
|---|---|---|
| Skill discovery | Repository `.agents/skills` plus adapters | User-global paths |
| Plans and durable outputs | Repository paths such as `.agents/plans` or configured project paths | Companion artifact repository |
| Repository mapping | Optional local config | Required global mapping |
| Ownership manifest | Recommended | Required |
| Target repository writes | Allowed within declared scope | Prohibited by default |
| Recovery state | Repository history plus manifest | Global recovery snapshot and companion history |

The CLI should expose a deterministic resolver, for example:

```text
agent-workflows context --repo "$PWD" --json
```

Skills and scripts should query that resolver rather than independently guessing paths.

### 5.8 Symlinks versus generated real files

**GPT-5.6:** Prefers real-file mirrors.

**Sonnet 5:** Recommends symlinks for some Claude and Codex deduplication.

**Gemini 3.1 Pro:** Does not decide.

**Resolution:** Use generated real directories or files as the portable default. Symlinks are supported by some hosts, including current Codex and Claude versions, but they remain fragile across:

- Windows configurations;
- archives and package managers;
- WSL and container boundaries;
- cloud repository ingestion;
- hosts that copy rather than preserve links;
- older host versions.

Symlinks may be an opt-in local optimization after a fixture proves discovery and packaging behavior. The ownership manifest must record whether an installed target is a copy or link.

### 5.9 Evidence labels in the host matrix

Sonnet's matrix uses language close to "followed" for paths derived from documentation even though the report also says no end-to-end fixture was run. GPT generally separates documentation from validation more carefully. Gemini does not provide an evidence matrix.

**Resolution:** Use these labels:

- **Documented:** current official documentation explicitly supports the behavior.
- **Fixture-verified:** the repository's probe observed the behavior on a named host version and surface.
- **Inferred:** documentation or neighboring behavior suggests it, but it was not explicit.
- **Unknown:** insufficient evidence.

Never label a behavior "working," "supported in this repository," or "followed" solely because a documentation page names the path.

## 6. Reconciled host delivery matrix

This table records documented behavior as of July 26, 2026. It is not a substitute for repository fixtures.

| Host | Documented project path relevant to canonical design | Documented user-global path | Explicit or guarded activation relevant here | Adapter decision |
|---|---|---|---|---|
| Codex | `.agents/skills` from CWD through repository root | `~/.agents/skills` | Explicit mention via `$` or `/skills`; implicit description matching; skills can be disabled in Codex config | Canonical path directly |
| Cursor | `.agents/skills`; also `.cursor/skills`; compatibility paths include `.claude/skills` and `.codex/skills` | Documented global skill locations | Supports `disable-model-invocation: true` | Canonical path directly; generated metadata when needed |
| Gemini CLI | `.agents/skills` or `.gemini/skills` | `~/.agents/skills` or `~/.gemini/skills` | Documentation says activation requires user confirmation | Canonical path directly; fixture confirmation behavior |
| Antigravity | `.agents/skills`; backward-compatible `.agent/skills` | `~/.gemini/config/skills` | Host behavior must be fixture-tested | Canonical project path; separate global target |
| OpenCode | `.agents/skills`; also `.opencode/skills` and `.claude/skills` | Corresponding global locations including `~/.agents/skills` | Skill permissions allow `allow`, `deny`, or `ask`; `ask` prompts before loading | Canonical path directly; generated permission policy |
| GitHub Copilot | `.agents/skills`; also `.github/skills` and `.claude/skills` | `~/.agents/skills` or `~/.copilot/skills` for supported local surfaces | Selection is description-driven; exact activation controls vary by surface | Canonical path directly; test local and cloud separately |
| Claude Code | `.claude/skills` | `~/.claude/skills` | Supports `disable-model-invocation: true`; command compatibility remains | Generate Claude adapter |

Two boundary conditions are especially important:

1. **Local global skills are not cloud delivery.** Claude's local `~/.claude/skills` are not read by Claude cloud or Cowork. Cloud use requires repository-scoped skills or supported account or plugin distribution. Similar local-versus-cloud distinctions must be tested for every host surface.
2. **Claude command compatibility is transitional leverage.** Claude documents that skills and commands coexist and that a skill wins a name collision. This makes migration easier, but it is not a reason to maintain both indefinitely.

Cursor's `.agents/skills` support should now be labeled documented, not merely provisional. Current official plain-text documentation states it directly.

## 7. Final capability disposition

### 7.1 Public skill inventory

The consolidated target is sixteen public skills:

| Skill | Source capability or consolidation | Default activation class | Notes |
|---|---|---|---|
| `assess` | `assess`, `assess-all`, assessment lenses | Bounded implicit for narrow scopes; explicit for all-concerns | Lenses remain references or catalog records |
| `advise` | `advise`, advisory personas | Bounded implicit | Personas remain references or catalog records |
| `benchmark` | `benchmark` | Bounded implicit if read-only | Confirm before costly or external runs |
| `getting-started` | onboarding plus `list-workflows` conversation | Implicit allowed | Exact inventory comes from CLI/catalog |
| `handoff` | `handoff` | Implicit allowed if read-only | Writing or sending remains separately confirmed |
| `incident` | `incident` | Explicit or consent-gated | Investigation may be implicit only if no operational action occurs |
| `migrate` | `migrate` | Explicit or consent-gated | Preview changes and support rollback |
| `plan-review` | `plan-review`, `plan-review-long` | Implicit allowed | Depth is an internal mode |
| `release-notes` | `release-notes` | Explicit or consent-gated when writing | Drafting may be safe; publishing is consequential |
| `release-review` | `release-review`, `release-review-plan` | Explicit or consent-gated | Plan-only is a stop mode |
| `scaffold-agent-skill` | scaffold workflow | Explicit or consent-gated | Generates files; validate package |
| `setup-repo` | `setup-repo` | Explicit or consent-gated | Must declare owned writes |
| `spec` | `spec` | Implicit allowed for drafting | File writes still follow mode and consent |
| `verify` | `verify` | Implicit allowed for read-only checks | Commands should be declared and bounded |
| `verify-execution` | `verify-execution` | Explicit or consent-gated | Executes plan or verification steps |
| `whatnext` | `whatnext` | Implicit allowed | Recommendation-only unless user authorizes action |

The activation class is a policy target, not a universal frontmatter field. Adapters must translate it to the strongest mechanism each host supports.

### 7.2 Surfaces that should not remain public skills

| Current surface | Final treatment | Reason |
|---|---|---|
| `assess-all` | Mode of `assess` | Same harness and output family |
| Individual assessment lenses | References selected by `assess` | Avoid catalog explosion and duplicated orchestration |
| Individual advisory personas | References selected by `advise` | Same harness and output family |
| `release-review-plan` | Mode of `release-review` | Only changes stop point |
| `plan-review-long` | Internal reference or deep mode of `plan-review` | Implementation depth is not a capability |
| `list-workflows` | `getting-started` plus deterministic catalog CLI | Native catalogs already enumerate skills |
| Legacy slash commands | Generated transitional shims | Compatibility only, never a second source |

### 7.3 Components that remain outside skills

| Component | Why it stays outside | How skills use it |
|---|---|---|
| `AGENTS.md` and native instruction mirrors | Always-on repository policy | Skills inherit its universal constraints |
| Deterministic Python package and CLI | Testable computation, filesystem operations, catalogs, resolution, installation | Skills call commands or scripts |
| Structured catalog | Exact inventory, aliases, modes, safety class, host adapters | Skills and installer consume it |
| `.agents/plans` and other durable outputs | Project state, not reusable instructions | Resolver returns mode-correct location |
| Templates | Reusable assets, not prompt body | Skills copy or render them |
| Lens and persona content | Internal selections beneath two harnesses | Loaded on demand as references |
| Documentation and governance | Human-facing maintenance and contribution policy | Linked, not injected by default |
| Communication templates | Assets with independent lifecycle | Selected and rendered by skills |
| Workflow artifacts | User or project outputs | Written only to resolver-approved locations |

## 8. Canonical package and generated adapters

### 8.1 Source layout

```text
.agents/
  skills/
    assess/
      SKILL.md
      references/
        lenses/
      scripts/
    advise/
      SKILL.md
      references/
        personas/
    release-review/
      SKILL.md
      references/
      assets/
  catalog.json
```

The canonical `SKILL.md` should use standard, portable metadata:

```yaml
---
name: release-review
description: Review release readiness, create a plan, or continue through approved release checks. Use only when the user requests release review work.
---
```

Required behavioral details belong in the instructions and references. Host-specific fields may be added to generated adapters, but canonical correctness must not depend on a field that other hosts ignore.

### 8.2 Catalog responsibilities

The structured catalog should record at least:

- canonical skill name;
- summary and trigger language;
- aliases and former command names;
- modes;
- activation class;
- action risk class;
- canonical path;
- referenced lenses, personas, templates, and scripts;
- generated host targets;
- local versus cloud availability;
- minimum tested host versions;
- ownership and version information;
- deprecation status for legacy shims.

The catalog should generate human documentation and compatibility surfaces. Hand-maintained inventory tables will drift.

### 8.3 Adapter rules

Adapters should be deterministic build outputs:

- `.claude/skills/<name>` mirrors each selected canonical skill with Claude-specific metadata.
- Host-specific activation settings are generated from the catalog.
- Legacy command files are small wrappers or generated content with a deprecation notice.
- Real files are the default.
- Every generated output is recorded in an ownership manifest.
- User edits to generated files are detected before replacement.

## 9. Tracked and clean-delta modes

### 9.1 Tracked mode

Tracked mode is appropriate when a team wants repository-visible workflow configuration:

- install canonical skills under `.agents/skills`;
- generate `.claude/skills` and any necessary adapters;
- permit declared project artifact and state directories;
- track generated or source files according to repository policy;
- use the repository's version control for review and rollback;
- maintain an ownership manifest so upgrades distinguish tool-owned from user-owned files.

Existing slash-command shims may remain for a deprecation window. New capability work should modify the canonical skill, then regenerate the shim.

### 9.2 Clean-delta mode

Clean-delta mode must preserve a clean target repository:

- install skills in user-global discovery locations;
- do not modify root instructions or tracked `.gitignore`;
- do not create locally ignored project shims as the normal design;
- store global configuration, mapping, ownership, and recovery data outside the target repository;
- route durable outputs to a configured companion artifact repository;
- return resolved paths through one deterministic CLI contract;
- refuse ambiguous repository identity or artifact routing rather than guessing;
- distinguish local delivery from cloud delivery.

Locally excluded project shims or skill directories may be evaluated as a fallback, but they should ship only after fixture evidence shows they are required and reliable. They inherently weaken the zero-delta guarantee because they still create target-repository files.

### 9.3 Resolver invariants

The resolver should:

1. identify the target repository using a stable identity, not only its current absolute path;
2. return the active product mode;
3. return skill, plan, artifact, template, and state roots;
4. expose whether each location is writable and owned;
5. return cloud availability separately from local availability;
6. fail closed when mappings conflict;
7. produce JSON for skills and scripts and concise text for humans;
8. avoid editing the target repository merely to discover context.

## 10. Report-specific strengths, omissions, and corrections

### 10.1 GPT-5.6

**Strongest contributions**

- Provides the most complete workflow-by-workflow conversion map.
- Correctly merges aliases, depth variants, and stop points into modes.
- Defines a coherent sixteen-skill end state.
- Separates reusable instructions from deterministic CLI behavior, durable state, templates, and governance.
- Proposes a structured catalog, ownership tracking, drift handling, migration phases, and acceptance criteria.
- Prefers portable real-file mirrors.
- Correctly warns against host-specific metadata in the canonical source.

**Omissions or underdeveloped areas**

- Does not fully specify the companion repository and resolver required for a strict clean-delta promise.
- Treats repository, user, hybrid, and legacy as peer install modes, which creates more user-facing combinations than necessary.
- Does not emphasize consequential workflow activation and action consent enough.
- Gives less attention to local-versus-cloud availability.
- Does not distinguish documented host support from fixture-verified behavior as systematically as the consolidated matrix should.

**Disposition**

Use GPT's capability taxonomy, package structure, catalog, and consolidation decisions as the architectural backbone. Add Sonnet's two-mode product model, resolver, exposure policy, cloud boundary, and fixture discipline.

### 10.2 Sonnet 5

**Strongest contributions**

- Provides the clearest tracked versus clean-delta product model.
- Defines the strongest clean-delta artifact routing and companion-repository design.
- Emphasizes a deterministic context resolver.
- Distinguishes safe auto-trigger candidates from consequential workflows.
- Recognizes that local global installation does not imply cloud availability.
- Proposes a useful per-host fixture protocol.
- Correctly keeps lenses and personas beneath harness skills.

**Divergences or corrections**

- Keeping `assess-all` command-only conflates costly activation with capability packaging. It should be an explicit mode of `assess`.
- Keeping `release-review-plan` separate creates unnecessary discovery and implementation duplication. It should be a `release-review` mode.
- A standalone `list-workflows` skill is redundant when `getting-started`, native discovery, and a deterministic catalog CLI exist.
- Consequential workflows should still have canonical skill packages. Hosts that cannot safely expose them should receive a restricted profile or thin shim, not a separate permanent command implementation.
- Symlinks should not be the default portable adapter mechanism.
- Documentation-derived host routes should be labeled documented, not operationally followed or verified.
- Cursor's `.agents/skills` support is now explicit in current official documentation and should not be classified merely as provisional.
- OpenCode's `ask` permission is a meaningful activation gate: it prompts before loading the skill. It is not exactly the same as explicit invocation, but it is stronger than the report's characterization of it as merely the closest available approximation.
- Gemini documentation confirms activation consent, but claims about consent recurrence should remain limited to what fixtures observe.

**Disposition**

Adopt Sonnet's operational and safety model while replacing command-versus-skill branching with canonical-skill packaging plus host exposure profiles.

### 10.3 Gemini 3.1 Pro

**Strongest contributions**

- Independently confirms `.agents/skills` as the canonical cross-agent location and `.claude/skills` as the adapter.
- Independently confirms one `assess` and one `advise` harness rather than per-lens or per-persona skills.
- Correctly preserves minimal universal instructions and fallback shims.
- Explicitly supports a sibling artifact repository, global mapping, global ownership manifest, and recovery snapshot for clean-delta operation.
- Correctly says clean-delta should not modify root `AGENTS.md` or tracked `.gitignore`.

**Omissions**

- No complete current-to-future workflow map.
- No decision on `assess-all`, `release-review-plan`, `plan-review-long`, or `list-workflows`.
- No meaningful activation or consent model.
- No host-by-host evidence matrix.
- No local-versus-cloud distinction.
- No canonical frontmatter or adapter-generation policy.
- No structured catalog design.
- No symlink-versus-copy analysis.
- No phased migration or acceptance test suite.
- No discussion of deterministic code, templates, and references at the same depth as GPT.

**Disposition**

Treat Gemini as corroboration of the core architecture and clean-delta principles, not as a complete implementation plan. It presents no evidence requiring reversal of the more detailed reconciled choices.

## 11. Consolidated implementation plan

### Phase 0: Freeze evidence vocabulary

- Adopt documented, fixture-verified, inferred, and unknown labels.
- Record host version, surface, operating system, installation scope, and date for every fixture result.
- Do not convert documentation claims into compatibility promises.

### Phase 1: Establish the catalog and policy model

- Create a machine-readable catalog for capabilities, aliases, modes, activation classes, action risks, and adapter targets.
- Define tracked and clean-delta modes.
- Define ownership, drift, rollback, and upgrade behavior.
- Define the resolver JSON contract.

### Phase 2: Build representative skills

Convert three contrasting capabilities first:

1. `plan-review`: read-oriented, implicitly matchable, with internal depth.
2. `assess`: dispatcher with one, several, or all lenses.
3. `setup-repo` or `release-review`: consequential, explicit or consent-gated, with action confirmation.

These exercise progressive disclosure, internal selection, script or asset use, and host activation controls.

### Phase 3: Generate and test adapters

- Generate Claude skill copies with explicit-only metadata where required.
- Generate host permission settings from activation policy.
- Generate legacy shims without duplicating workflow bodies.
- Test real-file copies first.
- Test symlinks only as an optional profile.

### Phase 4: Implement tracked and clean-delta routing

- Build the deterministic resolver.
- Add global mapping, ownership, and recovery records.
- Add companion artifact repository initialization and validation.
- Verify that clean-delta operations do not change `git status`, ignored-file state, root instructions, or tracked ignore rules.

### Phase 5: Convert the remaining inventory

- Convert the remaining sixteen-skill target set.
- Merge aliases and variants according to the disposition table.
- Move lenses and personas beneath their harnesses.
- Move templates to assets and reusable detail to references.
- Keep deterministic operations in scripts or the existing package.

### Phase 6: Host fixture matrix

For each supported host and relevant local or cloud surface, test:

- project discovery;
- user-global discovery;
- explicit invocation;
- implicit matching for a safe skill;
- explicit-only or consent-gated behavior for a consequential skill;
- relative reference, asset, and script resolution;
- name collisions;
- duplicate-path behavior;
- copy and optional symlink behavior;
- upgrade and removal;
- tracked mode artifact routing;
- clean-delta zero-write behavior;
- cloud availability independent of local installation.

### Phase 7: Deprecate command shims

- Publish exact replacement skill names and modes.
- Keep telemetry-free local warnings or clear deprecation messages.
- Remove shims only after supported host combinations have a tested native route or an intentionally retained fallback.
- Never remove a fallback based solely on documentation.

## 12. Acceptance criteria

The migration is complete only when:

1. Every public capability has one canonical implementation.
2. The catalog enumerates all public skills, aliases, modes, lenses, personas, adapters, and risk classes.
3. No lens or persona is exposed as a separate public skill.
4. `assess-all`, `release-review-plan`, `plan-review-long`, and `list-workflows` have the reconciled dispositions above.
5. Canonical skills function without relying on nonstandard metadata.
6. Claude adapters and legacy shims are generated, owned, and drift-detectable.
7. Consequential skills cannot be silently activated on any claimed-supported host profile.
8. Action-level confirmations remain in place even after activation consent.
9. Tracked mode writes only to declared, owned locations.
10. Clean-delta mode leaves the target repository byte-for-byte unchanged unless the user explicitly authorizes a mode change.
11. The resolver returns stable and unambiguous locations.
12. Companion artifact repositories are recoverable and correctly mapped.
13. Local installation is never advertised as cloud availability.
14. Every host compatibility claim names a fixture-verified version and surface.
15. Real-file adapters work on Windows, macOS, and Linux for the supported matrix.
16. Upgrade and uninstall preserve user-modified or unowned files.
17. Documentation is generated from the structured catalog or validated against it.
18. Legacy command removal has an evidence-backed replacement path.

## 13. Remaining open questions

The reports do not fully resolve these points, and official documentation alone is insufficient:

- Exact activation-consent recurrence in each Gemini CLI version.
- Whether every relevant GitHub Copilot local and cloud surface applies the same skill discovery and activation semantics.
- Antigravity's practical handling of activation metadata and scripts.
- Collision precedence when the same skill name exists at multiple supported locations on every host.
- Cloud treatment of symlinks and generated adapter directories.
- The best stable repository identity when a repository is moved, forked, or has multiple worktrees.
- Whether companion artifacts should use one repository per target, one repository per user, or a configurable grouping.
- The deprecation window required by actual users of legacy commands.

These are fixture and product decisions, not reasons to postpone the canonical architecture.

## 14. Final recommendation

Reconfigure `fariello/agent-workflows` around one canonical Agent Skills catalog in `.agents/skills`, with generated `.claude/skills` adapters and temporary generated command shims.

Use GPT-5.6's sixteen-skill inventory and consolidation logic. Use Sonnet 5's tracked versus clean-delta model, companion artifact repository, deterministic resolver, activation safety, cloud boundary, and fixture protocol. Use Gemini 3.1 Pro as independent confirmation of the canonical path, harness design, fallback need, and clean-delta ownership principles.

The decisive design rule is:

> Package capabilities once; control discovery, activation, and action separately.

That rule eliminates permanent dual implementations without weakening safety. It also gives the project a portable core, host-specific adapters, an honest compatibility matrix, and a clean-delta mode that can be tested as a concrete invariant.

## Sources

### Compared reports

- `suggested-future-skill-usage.gpt56(2).md`
- `suggested-future-skill-usage.sonnet5(1).md`
- `suggested-future-skill-usage.gemini31pro.md`

### Current host and standard documentation checked

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenAI: Build skills for ChatGPT and Codex](https://learn.chatgpt.com/docs/build-skills.md)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Cursor skills](https://cursor.com/docs/skills.md)
- [Gemini CLI agent skills](https://geminicli.com/docs/cli/skills/)
- [Antigravity skills](https://antigravity.google/docs/skills)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [GitHub Copilot: Add skills to the coding agent](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)

