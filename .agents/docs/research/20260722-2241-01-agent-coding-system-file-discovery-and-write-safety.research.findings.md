# Agentic Coding Systems: Project File Discovery, Installation Targets, and Write-Safety Research

**Prepared for:** [`fariello/agent-workflows`](https://github.com/fariello/agent-workflows/)  
**Research date:** 2026-07-22  
**Primary consumer:** Claude Opus 4.8 coding agent and maintainers of the `agent-workflows` installer  
**Scope:** Fifteen representative, widely used agentic coding systems discussed in the preceding analysis  
**Confidence convention:** **High** means current official documentation or upstream source explicitly names the path or behavior; **Medium** means official documentation establishes most of the behavior but leaves precedence or mutation details incomplete; **Low** means the behavior is version-sensitive or not publicly specified and must be probed before enabling writes.

## Executive summary

The safest architecture for `agent-workflows` is a canonical, host-neutral source tree under `.agents/`, plus narrowly generated adapters in each host's native directory. The repository already largely follows that design: `.agents/workflows/` is canonical, `.opencode/commands/` and `.claude/commands/` are generated shims, and a managed pointer block is inserted into `AGENTS.md` and mirrored into existing `CLAUDE.md` or `GEMINI.md` files. That remains the correct direction, with one important 2026 update: **Codex and OpenCode now natively discover portable Agent Skills under `.agents/skills/<skill>/SKILL.md`**. GitHub Copilot also accepts that location. `.agents/workflows/`, `.agents/plans/`, `.agents/docs/`, and `.agents/comms/` are not automatically understood merely because they are beneath `.agents/`.

The cross-host baseline should therefore be:

```text
AGENTS.md                              # small managed pointer, broadly recognized
.agents/
├── workflows/                        # agent-workflows canonical bodies
├── skills/<name>/SKILL.md            # portable native skills where appropriate
├── plans/                             # framework artifact convention, not host-native
├── docs/                              # framework reference convention, not host-native
└── install-manifest.json              # proposed ownership/provenance ledger
```

Host adapters should be projections, not independent sources:

```text
.opencode/commands/*.md                # OpenCode command adapters
.claude/commands/*.md                  # Claude legacy command adapters, if retained
.claude/skills/<name>/SKILL.md         # only if Claude cannot consume/cross-link canonical skill
.github/agents/*.agent.md              # Copilot custom-agent adapters
.windsurf/workflows/*.md               # Windsurf manual workflow adapters
.kiro/steering/*.md                    # only for persistent steering, not workflow bodies
```

### Principal conclusions

1. **The model is not the file-discovery authority.** Claude Opus, GPT, Gemini, Fable, and other models do not independently decide which repository files are loaded. Claude Code, Codex, OpenCode, Kiro, Cursor, and other host applications do. The same model behaves differently in different hosts.
2. **`AGENTS.md` is the broadest shared always-on entry point.** Codex, Cursor, Kiro, Devin, Cline, OpenCode, and newer Windsurf/Cascade surfaces document support. Claude Code's native file remains `CLAUDE.md`, although it can import another file with `@AGENTS.md`.
3. **`.agents/skills/` is the strongest emerging portable capability path.** Codex, OpenCode, and GitHub Copilot explicitly document it. Do not generalize that to all content beneath `.agents/`.
4. **Installation of a coding host ordinarily does not alter a repository.** Repository mutation usually occurs only when the user invokes an initializer, creates a rule/workflow through the UI, installs a project-scoped skill/plugin, or lets an agent edit files. The installer must nevertheless treat all native host paths as shared namespaces because later initialization can create files there.
5. **Whole-file ownership is unsafe for shared entry points.** `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.gitignore`, `.mcp.json`, and host settings files may pre-exist or later be modified by users and tools. `agent-workflows` should own only marker-delimited blocks in these files.
6. **Directory ownership must be per file, not per directory.** It is safe to own `.opencode/commands/aw-*.md`; it is unsafe to regard all of `.opencode/commands/` as generated. The same applies to `.claude/`, `.github/`, `.windsurf/`, `.cursor/`, `.kiro/`, `.continue/`, `.roo/`, and `.devin/`.
7. **Never infer that a path is disposable from its leading dot.** Several hosts store user-authored rules, commands, hooks, MCP configuration, and permission settings in these directories. Pruning an unrecognized file would be data loss.

## Research method and boundaries

The findings use current official vendor documentation and upstream project documentation, supplemented by inspection of the public [`fariello/agent-workflows`](https://github.com/fariello/agent-workflows/) repository. The repository inspection found the existing canonical `.agents/workflows/` design, generated OpenCode and Claude command shims, managed instruction pointers, no-clobber claims, staged Git changes, and framework-owned pruning behavior. This report does not modify that repository.

There is no authoritative, stable ranking of the “15 most popular” coding-agent systems. The list below is a representative ecosystem sample selected for adoption, visibility, and relevance to the project: OpenAI Codex, Claude Code, OpenCode, GitHub Copilot, Gemini CLI, Google Antigravity, Kiro, Cursor, Windsurf/Cascade, Cline, Roo Code, Continue, Aider, Devin, and Hermes Agent.

Documentation and behavior change rapidly. Every adapter should carry a `verified_with` host version or documentation date, and CI should periodically probe actual discovery rather than treating this report as an eternal specification.

## Master path and behavior matrix

| Host | Always-on project instructions | Native project workflows, commands, agents, or skills | Other project configuration | Install/init mutation risk | Recommended `agent-workflows` posture |
|---|---|---|---|---|---|
| Codex | Root-to-CWD `AGENTS.md` / `AGENTS.override.md` | `.agents/skills/<name>/SKILL.md` | `.codex/config.toml` may be trusted only in approved projects; user config is `~/.codex/config.toml` | Base install low; skill installer or agent edits medium | Native portable skills plus managed `AGENTS.md` pointer; do not invent Codex slash-command files |
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, nested files, `.claude/rules/` | `.claude/skills/`; `.claude/commands/`; `.claude/agents/` | `.claude/settings.json`, `.claude/settings.local.json`, `.mcp.json` | `/init`, UI creation, plugins, and agent edits can create/modify files | Generate namespaced adapters; block-edit only shared files; prefer skills over legacy command duplication where feasible |
| OpenCode | `AGENTS.md`, documented compatibility fallbacks | `.opencode/agents/`, `.opencode/commands/`, `.opencode/skills/`, plus `.agents/skills/` | `opencode.json` / `opencode.jsonc`; `.opencode/` plugins/tools | `/init` can create instructions; project commands and skills share namespace | Keep command shims; add canonical `.agents/skills`; collision-check names before writing |
| GitHub Copilot | `.github/copilot-instructions.md`, path-specific `.github/instructions/*.instructions.md`, `AGENTS.md` on supported surfaces | `.github/agents/*.agent.md`; `.agents/skills/`, `.github/skills/`, or `.claude/skills/`; `.github/prompts/*.prompt.md` | MCP and hooks are surface-specific | Installing extension low; customization UI/CLI medium | Prefer `.agents/skills`; generate `.github/agents/` only for real persona/agent semantics |
| Gemini CLI | `GEMINI.md` hierarchy; filename can be configured, including `AGENTS.md` | `.gemini/commands/*.toml`; extensions have their own layout | `.gemini/settings.json`; project `.gemini/` | `/init` or command/extension installation can create files | Managed `GEMINI.md` block only if file exists or user opts in; generate commands only after a tested adapter exists |
| Antigravity | Workspace Rules from product-managed rule/workflow system | Documented Rules and Workflows, with `.agent/` singular used in ecosystem builds; exact current on-disk contract is version-sensitive | Workspace IDE settings | Product install low; UI-generated rules/workflows medium | Detection-first, no automatic `.agent/` writes until version probe confirms schema; universal fallback through `AGENTS.md` |
| Kiro | Root `AGENTS.md`; `.kiro/steering/*.md` | `.kiro/agents/`; Agent Skills and specs/hooks are Kiro-specific | `.kiro/specs/`, `.kiro/hooks/`, `.kiro/settings/` depending feature/version | “Generate Steering Docs” creates foundational files | Use `AGENTS.md` pointer; avoid synthesizing steering unless requested; never overwrite `product.md`, `tech.md`, or `structure.md` |
| Cursor | Root/nested `AGENTS.md`; `.cursor/rules/*.mdc` | Rules rather than a stable portable workflow directory | `.cursor/` project configuration | `/create-rule` or Customize UI creates rule files | Use `AGENTS.md`; generate Cursor rules only for Cursor-specific activation/globs, with unique filenames |
| Windsurf/Cascade | Root/nested `AGENTS.md`; `.windsurf/rules/*.md` | `.windsurf/workflows/*.md`; skills in current Cascade product | Workspace `.windsurf/`; global under `~/.codeium/windsurf/` | UI creates workflow in current workspace, not necessarily Git root | A Windsurf workflow adapter is worthwhile; write only namespaced files and account for same-name precedence |
| Cline | `.clinerules/*.md`; `AGENTS.md`; global `~/.agents/AGENTS.md` | `.cline/skills/` or documented Skills surface depending version; workflows/plugins are product-specific | `.clineignore` is being deprecated; other `.cline/` configuration | “New rule” creates `.clinerules/<name>.md` | Prefer root `AGENTS.md`; optional namespaced `.clinerules/aw-*.md`; do not create project `.agents/AGENTS.md` |
| Roo Code | `.roo/rules/`, mode-specific `.roo/rules-<mode>/`; `AGENTS.md` support varies by version | `.roomodes` for custom modes; command/skill surfaces version-sensitive | `.roo/` configuration | Mode/rule creation can create or rewrite configuration | Adapter behind capability/version detection; never merge `.roomodes` as unstructured text |
| Continue | `.continue/rules/*.md` | Prompts and agent configuration under `.continue/` and user/team configuration | `.continue/config.yaml` or newer hub/block model depending version | “Create rule” can write `.continue/rules/` | Generate a single namespaced pointer rule only when Continue support is selected |
| Aider | No native `AGENTS.md` discovery contract; conventions supplied with `--read`/config | No native project skill/workflow directory | `.aider.conf.yml`, `.aiderignore`, `.env`; history files commonly at root | First run can offer/add `.aider*` to `.gitignore`; auto-commit is enabled by default | Do not create native workflow files; optionally add an `--read` entry through a structured YAML merge only with opt-in |
| Devin CLI/Desktop | Root/nested `AGENTS.md`, `AGENTS.local.md`, `AGENT.md`, `CLAUDE.md`; `.devin/rules/` | Skills/plugins/hooks under Devin's documented extensibility locations | `.devin/config.json`; imports `.cursor/`, `.windsurf/`, `.claude/` | Base install low; generated rules/skills and imports can expose duplicates | Use `AGENTS.md`; avoid duplicate adapters across every imported directory unless deduplication is proven |
| Hermes Agent | No documented project instruction convention comparable to `AGENTS.md` | User-installed skills under `~/.hermes/skills/`; bundled/hub skills | `~/.hermes/config.yaml` and other user state | Skill install writes user scope, not normally repo | Universal “read and execute” fallback; do not write home configuration from a repo installer |

## Shared semantics that the installer must model

### Instruction files are cumulative, overriding, or exclusive depending on host

These cannot be represented by one universal “priority” field:

- Codex builds a chain from global scope and then from repository root down to CWD. At each directory it chooses only one of `AGENTS.override.md`, `AGENTS.md`, or configured fallbacks, and more local content appears later. It also imposes a default combined-size limit.
- Cursor combines Team, Project, and User Rules with documented precedence and also scopes nested `AGENTS.md` by directory.
- Claude Code loads `CLAUDE.md` and `.claude/rules/` according to hierarchy, imports, and path conditions. A large duplicated pointer can consume context repeatedly.
- OpenCode walks project ancestry for several resource types. Duplicate skill names are not necessarily merged or replaced.
- Windsurf resolves same-named workflows using system, workspace, global, and built-in priority. A generated `/release-review` can be shadowed without any file being overwritten.

Accordingly, installation success does not prove activation. `aw doctor` should distinguish:

```text
present -> syntactically valid -> discovered -> selected -> not shadowed -> executable
```

### A filename collision can be semantic clobber without byte clobber

Two files can coexist yet one may disappear from a menu, shadow another command, or produce duplicate skill entries. The manifest must therefore reserve both path and semantic identifier:

```json
{
  "logical_id": "release-review",
  "kind": "workflow",
  "canonical": ".agents/workflows/release-review/release-review.md",
  "adapters": [
    {"host": "opencode", "path": ".opencode/commands/aw-release-review.md", "command": "aw-release-review"},
    {"host": "windsurf", "path": ".windsurf/workflows/aw-release-review.md", "command": "aw-release-review"}
  ]
}
```

Namespacing adapters with `aw-` avoids colliding with built-ins or user content, but changing existing public commands is a compatibility decision. If existing `/release-review` names are retained, the installer should preflight all known native locations and refuse an ambiguous collision unless the existing file carries a matching ownership marker.

### Installation, initialization, and agent editing are different threat surfaces

| Event | Typical repository effect | Required response |
|---|---|---|
| Install host binary or IDE extension | Usually none | No action beyond optional detection |
| First launch | User-level state, cache, auth, logs; sometimes `.gitignore` prompt | Never treat newly appearing files as framework-owned |
| Run `/init` or “Generate Steering” | Creates instruction or steering files | Reconcile managed blocks after creation; do not overwrite generated human content |
| Create rule/workflow/agent through UI | Writes into host-native project directory | File-level ownership ledger and semantic collision check |
| Install project-scoped skill/plugin | Creates or modifies skills/config files | Validate destination and refuse replacement of unmanaged target |
| Allow coding agent to edit repo | Any authorized file may change | Hash drift detection; do not silently “repair” user/agent modifications |
| Upgrade host | Usually user-level binaries/state; interpretation can change | Compatibility probes and fixture tests; no destructive migration based only on version |

## 1. OpenAI Codex

**Confidence: High.**

### Discovery

Codex reads `AGENTS.md` before work. Globally it checks `$CODEX_HOME/AGENTS.override.md` and then `$CODEX_HOME/AGENTS.md`, where `CODEX_HOME` defaults to `~/.codex`. In a project, it walks from the repository root to the current working directory and, at each directory, checks `AGENTS.override.md`, then `AGENTS.md`, then administrator-configured fallback filenames. Only one instruction file per directory is selected, and the default combined size limit is 32 KiB. [OpenAI's `AGENTS.md` documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Codex now explicitly scans `.agents/skills` in each directory from CWD upward to the repository root. A skill is a directory containing `SKILL.md` with required `name` and `description`, plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`. Duplicate skill names are not merged; both may appear. Codex supports symlinked skill directories. User skills live in `$HOME/.agents/skills`, admin skills in `/etc/codex/skills`, and system skills are bundled. [OpenAI Build Skills](https://learn.chatgpt.com/docs/build-skills)

### Writes and collision behavior

Installing Codex itself should not write project files. Creating a skill manually or through `$skill-creator`, installing a project-local skill, running an agent that edits repository content, or explicitly creating project configuration can. User skill installation commonly targets user scope; project skills should be treated as repository content.

`AGENTS.override.md` is a hard semantic override at a directory. If a repository later gains a root `AGENTS.override.md`, a framework pointer stored only in root `AGENTS.md` will be ignored. This is not byte clobber, but it disables discovery. `aw doctor` must report it.

### Recommendation

- Make `.agents/skills/` a first-class canonical output for workflows that fit Agent Skills semantics.
- Keep `AGENTS.md` small and use a marker-delimited pointer to `.agents/workflows/index.md`.
- Never write `AGENTS.override.md` automatically.
- Do not generate fake Codex slash commands. Codex skills are the native extensibility path.
- Check the instruction byte budget and warn if the managed pointer or surrounding file could be truncated.

## 2. Claude Code

**Confidence: High for paths; Medium for cross-version command/skill migration.**

### Discovery

Claude Code's principal project instruction files are `./CLAUDE.md` and `./.claude/CLAUDE.md`; nested `CLAUDE.md` files scope instructions closer to relevant files. `.claude/rules/` contains modular rules, including path-scoped rules. Claude supports imports such as `@AGENTS.md`, which is preferable to duplicating the complete cross-host instructions. [Claude Code memory documentation](https://code.claude.com/docs/en/memory)

Project customizations include:

- `.claude/skills/<name>/SKILL.md` for Agent Skills;
- `.claude/commands/*.md` for custom slash commands, although current Claude documentation increasingly treats skills as the richer mechanism;
- `.claude/agents/*.md` for subagent definitions;
- `.claude/settings.json` for shared project settings;
- `.claude/settings.local.json` for uncommitted local overrides;
- `.mcp.json` for project MCP servers in documented configurations.

[Claude Code commands](https://code.claude.com/docs/en/commands) and [Claude Code Agent Skills](https://code.claude.com/docs/en/skills) describe the current extensibility surfaces.

### Writes and collision behavior

Installing Claude Code normally writes user-level state, not repository files. `/init` can create a project `CLAUDE.md`. The UI/commands for creating skills, agents, rules, hooks, or settings can create content within `.claude/`. Plugin installation can add user or project-facing customizations depending on scope.

The dangerous cases are:

- an `agent-workflows`-generated `CLAUDE.md` prevents `/init` from producing a useful project guide or invites wholesale regeneration;
- a generated `.claude/commands/release-review.md` collides with a user command of the same name;
- a generated skill duplicates a command and both appear as invocable features;
- rewriting `.claude/settings.json` destroys permissions, hooks, environment settings, or plugin state.

### Recommendation

- If `CLAUDE.md` does not exist, prefer a minimal file that imports `@AGENTS.md`, with an ownership marker, rather than copying the pointer text.
- If it exists, insert only a marker-delimited import/pointer block.
- Retain `.claude/commands/` shims for backward compatibility, but consider generating Agent Skills for new functionality.
- Never replace `.claude/settings.json`, `.claude/settings.local.json`, or `.mcp.json`; use a structured merge with exact-key ownership and explicit preview.
- Never prune files under `.claude/` that are absent from the framework manifest.

## 3. OpenCode

**Confidence: High.**

### Discovery

OpenCode supports custom agents in `.opencode/agents/`, commands in `.opencode/commands/`, and skills in `.opencode/skills/`. It also explicitly scans Claude-compatible `.claude/skills/` and portable `.agents/skills/`, both in the project hierarchy and corresponding user locations. Project-local skills are discovered while walking upward to the Git worktree. [OpenCode Agents](https://opencode.ai/docs/agents/) and [OpenCode Agent Skills](https://opencode.ai/docs/skills/)

OpenCode reads repository instructions from `AGENTS.md` and supports documented compatibility behavior for other tools. Configuration may be stored in `opencode.json` or `opencode.jsonc`, and `.opencode/` may also contain plugins, tools, themes, or other product resources depending on version. [OpenCode Rules](https://opencode.ai/docs/rules/) and [OpenCode Configuration](https://opencode.ai/docs/config/)

### Writes and collision behavior

The base installation is not expected to alter a repository. `/init` may create project instructions. Creating commands, agents, skills, plugins, or tools writes native project files. OpenCode discovers multiple directory layers, so same-named resources can coexist, shadow, or be presented ambiguously.

The existing `agent-workflows` command shim design is valid, but the installer must not own all of `.opencode/commands/`. A host upgrade is more likely to change parsing or precedence than to overwrite files. A user invoking a future generator with an existing command name is a more realistic collision.

### Recommendation

- Continue generating `.opencode/commands/` adapters, one namespaced file per logical workflow.
- Add `.agents/skills/` as the portable source where the workflow qualifies as a skill.
- Do not duplicate the same skill into `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` unless empirical tests show the host deduplicates identical names.
- Record command name as well as file path in the ownership manifest.
- Treat `opencode.json/jsonc` as user-owned structured configuration.

## 4. GitHub Copilot

**Confidence: High.**

### Discovery

GitHub Copilot spans several surfaces, and support is not identical across VS Code agent mode, Copilot CLI, coding agent, code review, and GitHub.com. Repository instructions commonly use `.github/copilot-instructions.md`; path-specific instructions use `.github/instructions/*.instructions.md`. Supported agent surfaces also recognize `AGENTS.md`.

Custom agents use `.github/agents/<name>.agent.md`. Prompt files use `.github/prompts/<name>.prompt.md`. Agent Skills can be stored in `.github/skills/`, `.claude/skills/`, or `.agents/skills/`; each skill has a `SKILL.md`. GitHub documents `.agents/skills/` as a valid project location across Copilot cloud agent, code review, CLI, app, and VS Code agent mode. [GitHub custom agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents), [GitHub Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), and [repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)

### Writes and collision behavior

Installing a Copilot IDE extension does not ordinarily create repository customization files. Adding a custom agent, prompt, skill, or instructions through supported editors or GitHub tooling does. The `.github/` namespace is especially sensitive because it also contains Actions workflows, issue templates, CODEOWNERS-related content, security configuration, and organization conventions.

Duplicate custom-agent or skill names can create ambiguous selection even when paths differ. Organizational policies may inject higher-level instructions that a repository installer cannot see or change.

### Recommendation

- Use `.agents/skills/` rather than copying skills into `.github/skills/`.
- Keep `AGENTS.md` as the universal workflow index pointer.
- Create `.github/agents/*.agent.md` only when `agent-workflows` is delivering a genuine custom agent or assessor persona, not merely a workflow.
- Never claim ownership of `.github/`; own exact files only.
- Do not edit `.github/copilot-instructions.md` without opt-in and marker-delimited merging.

## 5. Gemini CLI

**Confidence: High for instruction/config paths; Medium for evolving extensions and commands.**

### Discovery

Gemini CLI uses `GEMINI.md` context files. It searches hierarchical context according to its documented memory/import rules, with global context under `~/.gemini/GEMINI.md`. The context filename is configurable, so an installation may use `AGENTS.md` instead. [Gemini CLI context documentation](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md)

Project custom commands use `.gemini/commands/*.toml`, with global commands under `~/.gemini/commands/`. Project settings use `.gemini/settings.json`; extensions have manifests and resources governed by the extension system. [Gemini CLI commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md)

### Writes and collision behavior

Installation primarily creates user-level configuration and authentication state. `/init` and user requests can create `GEMINI.md`; command or extension installation can create `.gemini/` resources. If a project already customizes the context filename to `AGENTS.md`, independently writing a `GEMINI.md` adapter is redundant and may produce conflicting guidance.

### Recommendation

- Detect `.gemini/settings.json` and the configured context filenames before adding a `GEMINI.md` block.
- If `GEMINI.md` exists, use a managed pointer block. If absent, rely on `AGENTS.md` unless the user selects native Gemini support.
- Do not generate `.gemini/commands/` until there is a tested TOML adapter with argument and quoting semantics.
- Structured-merge `.gemini/settings.json`; never replace it.

## 6. Google Antigravity / Antigravity IDE

**Confidence: Medium for product concepts; Low-to-Medium for stable on-disk paths.**

### Discovery

Antigravity documents Rules and Workflows as persistent instructions and repeatable procedures. Current public documentation is less explicit and less stable about every filesystem path than the CLI-centric products. Implementations and examples frequently use `.agent/` **singular**, which must not be confused with the portable `.agents/` directory. [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)

There is no basis for treating arbitrary `.agents/workflows/` content as natively discovered by Antigravity. The universal `AGENTS.md` pointer plus explicit “read and execute” instruction remains the safe fallback.

### Writes and collision behavior

Installing the IDE should not be assumed to mutate the repository. Creating a Rule or Workflow in the product may create workspace files, but the location can depend on product version and workspace choice. An IDE may choose the open workspace rather than the Git root, which creates nested customization directories.

### Recommendation

- Implement an Antigravity capability probe before any native write: identify product version, workspace root, exact rules/workflows directories, and schema.
- Keep Antigravity native adapter generation experimental until fixture-tested on supported versions.
- Never equate `.agent/` and `.agents/`, migrate one into the other, or prune either based on the other's manifest.
- Continue documenting the explicit `.agents/workflows/...` execution fallback.

## 7. Kiro IDE and CLI

**Confidence: High.**

### Discovery

Kiro workspace steering lives in `.kiro/steering/*.md`; global steering lives in `~/.kiro/steering/`. Its “Generate Steering Docs” action creates `product.md`, `tech.md`, and `structure.md`. Steering supports always, file-match, manual, and automatic inclusion modes. Kiro also automatically recognizes `AGENTS.md` at the workspace root. [Kiro Steering](https://kiro.dev/docs/steering/)

Kiro has custom agents and other project resources under `.kiro/`, including specs and hooks. Custom agents do not necessarily inherit steering automatically; their resource declarations may need to include it. [Kiro CLI Steering](https://kiro.dev/docs/cli/steering/) and [Kiro custom agents](https://kiro.dev/docs/cli/custom-agents/)

### Writes and collision behavior

Installing Kiro should not write project files by itself. Generating steering explicitly creates the three foundational files. Generating specs, hooks, or agents adds files beneath `.kiro/`. If `agent-workflows` pre-creates those foundational filenames, it risks blocking or confusing Kiro's generator. If it rewrites them later, it destroys user/project knowledge.

### Recommendation

- Rely on root `AGENTS.md` for discovery.
- Do not create `.kiro/steering/product.md`, `tech.md`, or `structure.md`.
- Create a namespaced steering pointer such as `.kiro/steering/agent-workflows.md` only with explicit Kiro adapter selection.
- Own no Kiro spec, hook, or agent configuration unless the corresponding artifact type is deliberately implemented.

## 8. Cursor

**Confidence: High.**

### Discovery

Cursor Project Rules live in `.cursor/rules/*.mdc`; plain `.md` files in that directory are ignored when the rule format requires MDC frontmatter. Rules can be always applied, applied by file glob, selected intelligently by description, or manually invoked. Cursor also supports root and nested `AGENTS.md`, scoped by directory. [Cursor Rules](https://cursor.com/docs/rules.md)

### Writes and collision behavior

Installing Cursor should not alter the repository. `/create-rule` and the Customize UI create `.cursor/rules/` files. Imported remote rules are placed under a Cursor-managed imported subtree. Rule precedence includes Team, Project, and User Rules. A generated rule can coexist with but contradict an enforced Team Rule, or can be ignored because of invalid extension/frontmatter.

### Recommendation

- Use `AGENTS.md` for the universal pointer.
- Only generate `.cursor/rules/aw-agent-workflows.mdc` when Cursor-specific conditional activation is valuable.
- Validate MDC frontmatter and never put an ordinary `.md` shim into `.cursor/rules/` expecting it to load.
- Do not touch `.cursor/rules/imported/`.

## 9. Windsurf / Cascade

**Confidence: High for current documented paths.**

### Discovery

Workspace Workflows are Markdown files in `.windsurf/workflows/*.md`; global workflows live under `~/.codeium/windsurf/global_workflows/`. Windsurf discovers workflow directories in the current workspace, subdirectories, and parent directories up to the Git root. The UI creates a workflow in the **current workspace**, which may not be the repository root. Same-name precedence is system, workspace, global, then built-in. Workflows are manually invoked and have a documented character limit. [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)

Current Cascade also documents `AGENTS.md`, Rules, and Skills. Rules have historically lived in `.windsurf/rules/`; newer Devin Desktop/Cascade materials also describe `.devin/rules/`, reflecting product evolution. This version drift should be detected rather than guessed.

### Writes and collision behavior

Base IDE installation normally leaves repository content alone. UI creation writes workflow/rule files. Because discovery spans nested workspaces, a later user-created nested workflow can shadow a root-generated workflow without overwriting it. Enterprise system workflows can also override repository workflows.

### Recommendation

- Add an optional `.windsurf/workflows/aw-<name>.md` adapter because Windsurf has a real native workflow concept.
- Keep each adapter below the documented limit and point to the canonical body rather than copying it.
- Detect shadowing at nested, root, global, and if visible system scope.
- Do not migrate `.windsurf/` to `.devin/` automatically.

## 10. Cline

**Confidence: High.**

### Discovery

Cline's primary workspace rules are `.clinerules/*.md` or `.txt`. It also recognizes `AGENTS.md` in the project and `~/.agents/AGENTS.md` as a global cross-tool instruction file. The latter is a **home-directory path**, not a project-root `.agents/AGENTS.md` convention. It can also recognize selected Cursor and Windsurf rule formats. [Cline Rules](https://docs.cline.bot/customization/cline-rules)

Cline has Skills, Plugins, Hooks, MCP, and subagent/team features whose precise directories have evolved. Treat the current official Skills documentation as the authority at adapter implementation time rather than assuming the Claude or portable paths are recognized. [Cline Skills](https://docs.cline.bot/customization/skills)

### Writes and collision behavior

The “New rule file” action writes `.clinerules/<name>.md`. Imported/recognized cross-tool files can cause duplicate guidance if `agent-workflows` emits equivalent rules into several supported directories. `.clineignore` is documented as slated for deprecation, so it should not become a new dependency.

### Recommendation

- Use project root `AGENTS.md`; do not create `.agents/AGENTS.md` in a repository for Cline.
- Optionally generate `.clinerules/aw-agent-workflows.md` as a short pointer, not a full duplicate.
- Avoid emitting equivalent Cursor, Windsurf, and Cline rules simultaneously for a Cline-targeted installation unless deduplication is verified.

## 11. Roo Code

**Confidence: Medium.**

### Discovery

Roo Code uses project rules under `.roo/rules/` and mode-specific rule directories such as `.roo/rules-<mode>/`. Custom modes are represented in `.roomodes`, with global modes stored separately. Roo's command, skills, and compatibility behavior is changing quickly. [Roo Code custom instructions](https://docs.roocode.com/features/custom-instructions) and [Roo Code custom modes](https://docs.roocode.com/features/custom-modes)

### Writes and collision behavior

Creating modes or rules through Roo can create project files. `.roomodes` is structured configuration and may contain user-authored modes; treating it as generated text is unsafe. Multiple rule directories can intentionally apply to different modes.

### Recommendation

- Keep Roo support capability-gated by detected version.
- Prefer a single namespaced `.roo/rules/aw-agent-workflows.md` pointer when supported.
- Modify `.roomodes` only with a schema-aware merge, explicit preview, exact owned IDs, and backups.
- Do not prune any mode or rule not carrying framework provenance.

## 12. Continue

**Confidence: High for Rules; Medium for the broader fast-moving configuration model.**

### Discovery

Continue project Rules are Markdown files in `.continue/rules/`, with YAML frontmatter controlling name, globs, regex, description, and application behavior. Rule files load in lexical order. The agent can create a rule through an enabled tool, writing into `.continue/rules/`. [Continue Rules](https://docs.continue.dev/customize/deep-dives/rules)

Continue's broader configuration has transitioned from older JSON forms toward YAML and reusable hub blocks. Project/user prompts, models, MCP servers, and assistants should be implemented against the current version's schema rather than inferred from an old `.continue/config.json` example.

### Writes and collision behavior

Installing the IDE extension normally does not change repository files. Creating a local rule does. Lexical order means a filename change can alter effective precedence. A generated `01-agent-workflows.md` is more intrusive than a late, plainly named pointer.

### Recommendation

- Generate `.continue/rules/aw-agent-workflows.md` only when Continue is selected.
- Use minimal frontmatter and an explicit reference to the canonical workflow index.
- Do not force numeric ordering unless the user requests precedence.
- Structured-merge configuration; do not rewrite an entire Continue config.

## 13. Aider

**Confidence: High.**

### Discovery

Aider searches for `.aider.conf.yml` in the home directory, Git root, and current directory, loading them in that order so later files take priority. It can read convention/instruction files through the `read` option or CLI flags. A common convention filename is `CONVENTIONS.md`, but it is not a universal repository instruction standard automatically equivalent to `AGENTS.md`. [Aider YAML configuration](https://aider.chat/docs/config/aider_conf.html) and [Aider coding conventions](https://aider.chat/docs/usage/conventions.html)

Aider also uses `.aiderignore`; default history paths include `.aider.input.history` and `.aider.chat.history.md`. Its Git integration defaults include adding `.aider*` patterns to `.gitignore` and automatically committing model changes unless configured otherwise.

### Writes and collision behavior

Installing Aider itself is primarily user-level. On use, it may update `.gitignore`, create history files, and make Git commits. This is a materially different risk from IDE agents: even if the `agent-workflows` installer does not collide with an Aider configuration file, a later Aider session can change repository history and `.gitignore`.

### Recommendation

- Do not create a fake Aider workflow directory.
- Optional integration should structured-merge a `read: [AGENTS.md]` or canonical index entry into `.aider.conf.yml`, only with user opt-in.
- Preserve YAML comments and formatting or refuse the merge; generic parse-and-dump is a form of clobber.
- Detect and report Aider's auto-commit and `.gitignore` settings in `aw doctor`, but do not change them silently.

## 14. Devin CLI / Devin Desktop

**Confidence: High.**

### Discovery

Devin CLI recommends root `AGENTS.md`, supports `AGENTS.local.md`, `AGENT.md`, `.windsurfrules`, and `CLAUDE.md`, and discovers instruction files in subdirectories. It imports rules from `.cursor/rules/`, `.windsurf/rules/`, and `.claude/` according to configurable import settings. Shared configuration uses `.devin/config.json`; current desktop Cascade rules use `.devin/rules/`, with legacy Windsurf paths still recognized. [Devin Rules and `AGENTS.md`](https://docs.devin.ai/cli/extensibility/rules) and [Devin Desktop `AGENTS.md`](https://docs.devin.ai/desktop/cascade/agents-md)

### Writes and collision behavior

Base installation should not edit project instructions. Rule, skill, plugin, hook, agent, or local configuration creation can. Because Devin imports multiple competitors' rule formats, generating a pointer into all of them can multiply the same instructions in context.

`AGENTS.local.md` is intended for local uncommitted preferences. The framework must not create, track, or prune it. `.devin/config.json` controls whether external formats are imported and must be treated as user-owned structured configuration.

### Recommendation

- Use only the root `AGENTS.md` pointer by default.
- Do not generate `.devin/rules/`, `.cursor/rules/`, `.windsurf/rules/`, and `.claude/rules/` simultaneously merely to support Devin.
- If an assessor becomes a Devin-native skill or plugin, install it as a separate opt-in adapter with a distinct ID.
- Never touch `AGENTS.local.md`.

## 15. Hermes Agent

**Confidence: High for user skills; Medium for repository instruction interoperability.**

### Discovery

Hermes bundles skills and installs optional/user-created skills under `~/.hermes/skills/`. Skills use `SKILL.md` plus optional references, templates, and scripts. Configuration values requested by skills are stored under the user's Hermes configuration. The documented workflow is user-scoped rather than a project-root `.agents/` convention. [Hermes Working with Skills](https://github.com/hermes-agent-org/hermes/blob/main/website/docs/guides/work-with-skills.md)

### Writes and collision behavior

`hermes skills install` copies to the user-level Hermes skill tree. An agent may also create or update a skill. That creates a home-directory ownership problem: a repository installer should not mutate a user's global agent behavior merely because it was run in one project.

### Recommendation

- Do not write `~/.hermes/` from `aw install <repo>`.
- Provide an explicit, separate `aw integrate hermes --user` flow if global Hermes skill installation is later supported.
- The default repository behavior should be `AGENTS.md` plus the universal instruction to read `.agents/workflows/index.md`.

## Proposed installer architecture

### Canonical artifacts and generated adapters

Classify every installed file as one of:

| Class | Example | Update policy |
|---|---|---|
| Canonical immutable framework body | `.agents/workflows/assess/assess.md` | Replace only if prior installed hash matches manifest or file carries immutable generated header; otherwise report drift |
| Portable skill | `.agents/skills/security-assessment/SKILL.md` | Same as canonical body; preserve separately named user skills |
| Generated host adapter | `.opencode/commands/aw-assess.md` | Regenerate only when manifest proves ownership; keep content minimal |
| Shared-file managed block | `AGENTS.md`, existing `CLAUDE.md`, `GEMINI.md` | Replace marker-delimited block only; preserve byte-for-byte surrounding content |
| Structured shared configuration | `.mcp.json`, `.claude/settings.json`, `.gemini/settings.json`, `.roomodes`, YAML configs | Schema-aware exact-key merge, preview, backup, and conflict refusal |
| Runtime/user artifact | history, cache, auth, local settings | Never install, track, migrate, or prune |
| Workflow output | `.agents/plans/`, `workflow-artifacts/` | User/project-owned after creation; uninstall must preserve by default |

### Ownership manifest

Add a versioned manifest, for example `.agents/install-manifest.json`, containing:

```json
{
  "schema_version": 1,
  "installer": "agent-workflows",
  "installed_version": "1.2.3",
  "files": {
    ".opencode/commands/aw-assess.md": {
      "kind": "generated-adapter",
      "host": "opencode",
      "logical_id": "assess",
      "sha256": "..."
    }
  },
  "managed_blocks": {
    "AGENTS.md": {
      "id": "agent-workflows",
      "content_sha256": "..."
    }
  },
  "capabilities": {
    "codex": {"verified": true, "skills_path": ".agents/skills"},
    "antigravity": {"verified": false}
  }
}
```

The manifest itself must not be the only proof of ownership. Generated files should carry a short header such as `Generated by agent-workflows; edit the canonical body, not this adapter`, where the host format permits comments/frontmatter. Before replacement or deletion, require both a matching manifest entry and either a matching prior hash or an explicit force decision.

### Required collision algorithm

For every proposed destination:

1. Resolve repository root and reject destinations escaping it, including through symlinks.
2. Identify the logical command, skill, rule, or agent name, not just the path.
3. Search all host locations that can define the same logical identifier.
4. If destination is absent, create atomically.
5. If present and its current hash equals the manifest hash, update atomically.
6. If present with a recognized managed block, update only that block.
7. If present but modified, stop and report a three-way conflict; never overwrite under the label “generated.”
8. If a different path shadows the new artifact, install only with a warning or user choice.
9. Stage only the exact successful changes. Do not commit.

### Uninstall and pruning rules

- Remove only files whose current hash still matches the last installed hash.
- For modified generated files, leave them in place and report them.
- Remove only the managed block from shared instruction files. Delete the containing file only if it becomes empty and the manifest proves the installer originally created it.
- Preserve `.agents/plans/`, `.agents/docs/`, `.agents/comms/`, and `workflow-artifacts/` unless the user explicitly requests removal of generated outputs.
- Never recursively remove `.claude/`, `.opencode/`, `.github/`, `.cursor/`, `.windsurf/`, `.kiro/`, `.clinerules/`, `.roo/`, `.continue/`, `.devin/`, `.gemini/`, or `.agents/`.

## Recommended host support tiers

| Tier | Hosts | Installer behavior |
|---|---|---|
| Tier 1: native, tested | Codex, Claude Code, OpenCode | Generate and test native skills/commands plus instruction pointer |
| Tier 2: safe instruction discovery | GitHub Copilot, Gemini CLI, Kiro, Cursor, Devin, Cline | `AGENTS.md` pointer by default; optional tested adapters |
| Tier 3: native workflow adapter candidate | Windsurf/Cascade, Continue | Generate only when selected; collision and version tests required |
| Tier 4: capability-probed experimental | Antigravity, Roo Code | No automatic native writes without a positive version/schema probe |
| Tier 5: universal/manual | Aider, Hermes | Do not write native project files by default; provide explicit integration instructions |

## Test matrix for `agent-workflows`

### Filesystem fixtures

Each supported host needs fixtures for:

- clean repository;
- existing empty native directory;
- existing unrelated user files;
- exact filename collision;
- same logical identifier at a different discovery level;
- framework-owned unmodified file;
- framework-owned locally modified file;
- symlinked native directory or skill;
- nested working directory and monorepo;
- multiple worktrees;
- read-only file/directory;
- case-insensitive filesystem collision;
- non-UTF-8 or malformed configuration;
- install, reinstall, upgrade, downgrade, uninstall, and interrupted install.

### Behavioral probes

For each host/version, CI or a documented manual harness should prove:

1. Which instruction files are actually loaded.
2. Whether root and nested instructions merge or replace.
3. Which skills/commands/workflows appear in discovery UI or CLI.
4. What happens with duplicate names.
5. Whether symlinked adapters work.
6. Whether edits are hot-reloaded or require restart.
7. Whether an initializer modifies an existing file, refuses, merges, or replaces.
8. Whether installation after `aw install` changes tracked files.
9. Whether host uninstall removes project files. It ordinarily should not, but this must be observed.
10. Whether the host respects the canonical “read and execute” fallback.

### Golden invariants

- `aw install` never changes an unmanaged byte without explicit approval.
- Reinstall with identical inputs produces an empty Git diff.
- Installing or initializing a supported host after `aw install` cannot silently destroy canonical workflows.
- `aw install` after host initialization preserves all host-generated and user-authored content.
- A modified generated adapter is reported, not overwritten or deleted.
- Every native adapter resolves to exactly one canonical logical workflow.
- A host that is absent receives no unnecessary native directory unless the user requested portable artifacts in that directory.

## Immediate backlog for the project

1. Add `.agents/skills/` to the architecture as a portable, host-recognized namespace distinct from `.agents/workflows/`.
2. Define which existing workflows are true skills, which are manual workflows, and which are agents/assessors. Do not mechanically convert every Markdown file into `SKILL.md`.
3. Introduce `.agents/install-manifest.json` with file hashes, logical IDs, host, adapter kind, and installed version.
4. Namespace newly generated native IDs with `aw-`, or document and test compatibility rules for the existing unprefixed commands.
5. Add `aw doctor --hosts` to report detected products, project-native files, shadowing, duplicate identifiers, modified generated adapters, instruction size limits, and unsupported versions.
6. Add a dry-run collision report that shows canonical source, destination, existing owner, effective precedence, and action.
7. Replace any whole-file pointer updates with marker-delimited block edits.
8. Preserve YAML/JSONC/TOML formatting or decline structured merges when a round-trip-safe editor is unavailable.
9. Add a Windsurf workflow adapter proof of concept; its native workflow model maps well to this project.
10. Keep Antigravity and Roo native writes disabled until filesystem behavior is fixture-tested.
11. Document Aider's auto-commit and `.gitignore` behavior because it can surprise users even without a path collision.
12. Add scheduled documentation-drift checks for official host path pages and upstream releases.

## References

### Project inspected

- [`fariello/agent-workflows`](https://github.com/fariello/agent-workflows/)
- [`agent-workflows` architecture](https://github.com/fariello/agent-workflows/blob/main/ARCHITECTURE.md)
- [`agent-workflows` decisions](https://github.com/fariello/agent-workflows/blob/main/DECISIONS.md)

### Host documentation

- OpenAI, [Custom instructions with `AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- OpenAI, [Build skills](https://learn.chatgpt.com/docs/build-skills)
- Anthropic, [Claude Code memory](https://code.claude.com/docs/en/memory)
- Anthropic, [Claude Code commands](https://code.claude.com/docs/en/commands)
- Anthropic, [Claude Code skills](https://code.claude.com/docs/en/skills)
- OpenCode, [Agents](https://opencode.ai/docs/agents/)
- OpenCode, [Agent Skills](https://opencode.ai/docs/skills/)
- OpenCode, [Rules](https://opencode.ai/docs/rules/)
- OpenCode, [Configuration](https://opencode.ai/docs/config/)
- GitHub, [Create custom agents](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
- GitHub, [Add Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- GitHub, [Add repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)
- Google, [Gemini CLI hierarchical context](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md)
- Google, [Gemini CLI commands](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md)
- Google, [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)
- Kiro, [Steering](https://kiro.dev/docs/steering/)
- Kiro, [CLI Steering](https://kiro.dev/docs/cli/steering/)
- Cursor, [Rules](https://cursor.com/docs/rules.md)
- Windsurf, [Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- Cline, [Rules](https://docs.cline.bot/customization/cline-rules)
- Cline, [Skills](https://docs.cline.bot/customization/skills)
- Roo Code, [Custom instructions](https://docs.roocode.com/features/custom-instructions)
- Roo Code, [Custom modes](https://docs.roocode.com/features/custom-modes)
- Continue, [Rules](https://docs.continue.dev/customize/deep-dives/rules)
- Aider, [YAML configuration](https://aider.chat/docs/config/aider_conf.html)
- Aider, [Coding conventions](https://aider.chat/docs/usage/conventions.html)
- Devin, [Rules and `AGENTS.md`](https://docs.devin.ai/cli/extensibility/rules)
- Devin, [Desktop `AGENTS.md`](https://docs.devin.ai/desktop/cascade/agents-md)
- Hermes Agent, [Working with Skills](https://github.com/hermes-agent-org/hermes/blob/main/website/docs/guides/work-with-skills.md)

## Final assessment

The current `agent-workflows` design is close to the right abstraction boundary. `.agents/` should remain the product's canonical namespace, but the installer must distinguish **framework conventions** from **host-native conventions**. Today, only `.agents/skills/` has meaningful native multi-host discovery. Everything else under `.agents/` remains discoverable only through `AGENTS.md`, a native adapter, or an explicit instruction.

The engineering priority should not be maximizing the number of generated host directories. It should be building a provably non-destructive projection system: canonical artifacts, exact file ownership, semantic-ID collision detection, managed shared-file blocks, structured merges, drift-aware updates, and conservative uninstall. With those controls, additional host adapters are small and reversible. Without them, every new supported host multiplies the chance of silently overwriting user configuration or creating contradictory instructions.
