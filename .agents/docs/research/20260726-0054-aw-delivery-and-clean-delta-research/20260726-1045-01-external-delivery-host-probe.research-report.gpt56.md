# External Delivery of Coding-Agent Workflows: Host Resolution and Execution Evidence

**Research date:** July 25, 2026  
**Access date for all cited web sources:** July 25, 2026  
**Question:** Can each host reliably resolve and then follow workflow instructions that live outside the working repository, or that live in a host-native `SKILL.md`?

## Scope and verdict method

This report evaluates three delivery tiers:

- **T1, out-of-repository pointer:** A repository instruction file or shim points to an absolute, home-directory, packaged-data, or otherwise out-of-repository path.
- **T2, host-native skill:** The host discovers a project skill such as `.agents/skills/<name>/SKILL.md` without an explicit pointer to that file.
- **T3, home-directory or global:** The host discovers instruction or skill content from a documented user-global location.

The verdict labels mean:

- **Followed:** Official host documentation states that the host discovers or imports the content and supplies or applies its instructions to the agent. This is evidence of supported behavior, not a claim that a probabilistic model will obey every instruction on every run.
- **Resolved-not-followed:** The host loaded the content, but reliable evidence showed that the agent did not act on an instruction found only there.
- **Not-resolved:** The documented host mechanism does not parse or load the pointer form under evaluation.
- **Unknown:** Primary evidence does not establish whether an arbitrary out-of-repository pointer is resolved and followed.

No target host executable was available in the research environment. Commands named `opencode`, `claude`, `codex`, `cursor`, `antigravity`, and `gemini` were absent; the available `code` launcher reported that VS Code was not installed. Consequently, no side-effect probe is presented as executed. All results below are based on current official documentation, release notes, and official source repositories. This limitation matters most for negative claims and for model-selected skill activation.

## Executive summary

| Host and evaluated version | T1: out-of-repository pointer | T2: host-native skill | T3: home-directory/global |
| --- | --- | --- | --- |
| OpenCode 1.18.5, released July 24, 2026 | **Not-resolved** for a passive `@path` in `AGENTS.md`; configured references and instruction sources are supported alternatives | **Followed** from `.agents/skills/<name>/SKILL.md` | **Followed** from documented global rule, command, and skill locations |
| Claude Code 2.1.220, released July 25, 2026 | **Followed**, after first-use approval for an external import from a project file | **Followed** through the equivalent `.claude/skills/<name>/SKILL.md`; `.agents/skills` is not documented as a Claude Code skill root | **Followed** from `~/.claude/CLAUDE.md`, `~/.claude/rules/`, and `~/.claude/skills/` |
| OpenAI Codex CLI 0.145.0, released July 21, 2026 | **Not-resolved by the documented instruction loader** for a passive `@path`; an agent might still read a named path if tools and permissions allow, but that is not host import behavior | **Followed** from `.agents/skills/<name>/SKILL.md` | **Followed** from `~/.codex/AGENTS.md` and `$HOME/.agents/skills/` |
| GitHub Copilot in VS Code 1.130, released July 22, 2026 | **Unknown** for an arbitrary absolute or packaged-data link outside the workspace; Markdown-linked instructions are supported when enabled, but the external-path boundary is not specified | **Followed** from `.agents/skills/<name>/SKILL.md` and other documented skill roots | **Followed** from `~/.copilot/instructions`, `~/.copilot/skills`, and compatible Claude/Agent paths |
| Cursor 3.11, released July 10, 2026 | **Unknown** for a passive absolute out-of-workspace `@filename` reference | **Followed** from `.agents/skills/<name>/SKILL.md` | **Followed** from `~/.agents/skills`, `~/.cursor/skills`, and Cursor User Rules |
| Google Antigravity 2.0 v2.3.1, documented July 25, 2026 | **Followed**: Rules explicitly resolve true absolute `@filename` paths | **Followed** from `<workspace-root>/.agents/skills/<name>/SKILL.md` | **Followed** from `~/.gemini/GEMINI.md` and `~/.gemini/config/skills/<name>/SKILL.md` |
| Gemini CLI 0.52.0, released July 22, 2026 | **Followed**: `GEMINI.md` imports support absolute paths | **Followed after activation consent** from `.agents/skills/<name>/SKILL.md` or `.gemini/skills/<name>/SKILL.md` | **Followed** from `~/.gemini/GEMINI.md`, `~/.agents/skills`, or `~/.gemini/skills` |

The strongest portable T2 path today is `.agents/skills/<name>/SKILL.md`: OpenCode, Codex, GitHub Copilot in VS Code, Cursor, Antigravity, and Gemini CLI all document it. Claude Code is the major exception and requires `.claude/skills/<name>/SKILL.md`, a plugin skill, or a symlinked entry in a Claude skill root.

For the exact current shim body `Read and execute @.agents/workflows/<path>`, migration to an absolute path is not uniformly safe. Claude Code, Antigravity, and Gemini CLI have explicit import or reference semantics. OpenCode explicitly says it does not automatically parse file references in `AGENTS.md`. Codex documents instruction-file discovery but not `@` import expansion. VS Code/Copilot and Cursor support references, but their current primary documentation does not establish that arbitrary absolute paths outside the workspace are accepted.

## Per-host and per-tier results

| Host | Version | Tier | Resolved? | Followed? | How verified | Notes | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenCode | 1.18.5 | T1 | No for passive `@path` in `AGENTS.md` | No by host loader | Official Rules documentation | `opencode.json` instruction sources and configured references are supported alternatives; arbitrary absolute local instruction paths were not explicitly demonstrated in the Rules examples | 2026-07-25 |
| OpenCode | 1.18.5 | T2 | Yes | Yes, when selected and permitted | Official Agent Skills documentation | Auto-discovers `.agents/skills`, `.opencode/skills`, and `.claude/skills`; skill body is loaded on demand | 2026-07-25 |
| OpenCode | 1.18.5 | T3 | Yes | Yes | Official Rules, Commands, and Agent Skills documentation | Global rules: `~/.config/opencode/AGENTS.md`; global skills include `~/.agents/skills` | 2026-07-25 |
| Claude Code | 2.1.220 | T1 | Yes | Yes, subject to model adherence | Official memory/import documentation | Relative and absolute imports are supported; an external import in a project file triggers a first-use approval dialog | 2026-07-25 |
| Claude Code | 2.1.220 | T2 | Yes at Claude-native path | Yes | Official Skills documentation | Uses `.claude/skills/<name>/SKILL.md`, not the portable `.agents/skills` path | 2026-07-25 |
| Claude Code | 2.1.220 | T3 | Yes | Yes | Official memory and Skills documentation | Personal rules and skills apply across projects; local cloud sessions do not inherit machine-local skills | 2026-07-25 |
| Codex | 0.145.0 | T1 | No documented `@` expansion | No by documented loader | Official `AGENTS.md` discovery documentation | Codex may use its Read tool on a path described in prose, but this is model/tool behavior rather than host resolution | 2026-07-25 |
| Codex | 0.145.0 | T2 | Yes | Yes, implicitly or explicitly invoked | Official Skills documentation | Scans `.agents/skills` from current directory to repository root | 2026-07-25 |
| Codex | 0.145.0 | T3 | Yes | Yes | Official `AGENTS.md` and Skills documentation | Global instructions in Codex home; user skills in `$HOME/.agents/skills` | 2026-07-25 |
| GitHub Copilot / VS Code | VS Code 1.130 | T1 | Unknown outside workspace | Unknown | Official custom-instructions documentation | Markdown-linked referenced instructions require `chat.includeReferencedInstructions`; docs do not define the arbitrary external absolute-path boundary | 2026-07-25 |
| GitHub Copilot / VS Code | VS Code 1.130 | T2 | Yes | Yes | Official Agent Skills documentation | Project roots include `.agents/skills`; metadata is discovered first, body loaded when relevant | 2026-07-25 |
| GitHub Copilot / VS Code | VS Code 1.130 | T3 | Yes | Yes | Official custom-instructions and Agent Skills documentation | User instructions and skills have documented home/profile roots; settings can disable locations | 2026-07-25 |
| Cursor | 3.11 | T1 | Unknown outside workspace | Unknown | Official Rules documentation | `@filename` references are supported in rules, but arbitrary absolute external resolution is not documented | 2026-07-25 |
| Cursor | 3.11 | T2 | Yes | Yes | Official Agent Skills documentation and 2.4 release notes | Auto-discovers `.agents/skills`; model-selected invocation is description-dependent | 2026-07-25 |
| Cursor | 3.11 | T3 | Yes | Yes | Official Agent Skills and Rules documentation | User skills are file-backed; User Rules are configured in Cursor, not necessarily distributed as files | 2026-07-25 |
| Google Antigravity | 2.0 v2.3.1 | T1 | Yes | Yes, subject to model adherence | Official Rules and Workflows documentation | A true absolute `@filename` path is attempted first; missing absolute paths fall back to workspace-relative resolution | 2026-07-25 |
| Google Antigravity | 2.0 v2.3.1 | T2 | Yes | Yes | Official Agent Skills documentation | Native workspace path is `.agents/skills`; legacy `.agent/skills` remains supported | 2026-07-25 |
| Google Antigravity | 2.0 v2.3.1 | T3 | Yes | Yes | Official Rules and Agent Skills documentation | Global rules and global skills use different `~/.gemini` subpaths | 2026-07-25 |
| Gemini CLI | 0.52.0 | T1 | Yes | Yes, subject to model adherence | Official `GEMINI.md` documentation | Imports support relative and absolute paths; imported content is part of concatenated context sent with every prompt | 2026-07-25 |
| Gemini CLI | 0.52.0 | T2 | Yes | Yes after user consent | Official Agent Skills documentation | Discovers `.agents/skills` and `.gemini/skills`; activation displays a confirmation prompt | 2026-07-25 |
| Gemini CLI | 0.52.0 | T3 | Yes | Yes | Official `GEMINI.md` and Agent Skills documentation | Global context and skills are documented; user skill activation still has the consent step | 2026-07-25 |

## Host details

### OpenCode 1.18.5

OpenCode 1.18.5 was released July 24, 2026. Its Rules documentation was updated the same day. [OpenCode changelog](https://opencode.ai/changelog)

#### T1

The current passive shim form is not a host-level OpenCode import. The official Rules documentation states that OpenCode “doesn’t automatically parse file references in `AGENTS.md`.” It recommends either:

1. adding instruction files through the `instructions` field in `opencode.json`; or
2. writing explicit prose that tells the model to use its Read tool when it encounters a reference.

The second approach is model-mediated and therefore weaker than host resolution. A line such as `Read and execute @/opt/package/workflow.md` might cause a capable model to read the file, but OpenCode has not itself expanded or attached that reference. [OpenCode Rules](https://opencode.ai/docs/rules/)

OpenCode now also supports configured external references. A reference can point to an absolute path, a `~/` path, a relative directory, or a Git repository. The host gives the agent the resolved path and description and permits access through the external-directory boundary. This proves reliable path resolution, but a reference directory’s contents are inspected on demand rather than automatically injected as mandatory workflow instructions. [OpenCode References](https://opencode.ai/docs/references/)

For this framework, the safest OpenCode T1 alternative is an installer-managed `opencode.json` entry whose `instructions` list names the workflow file, or a configured reference plus a small in-repository directive. Before relying on an absolute file in `instructions`, add a version-pinned side-effect test because the current documentation demonstrates relative files and remote URLs but does not explicitly show an absolute local file in that field.

#### T2

OpenCode auto-discovers:

- `.opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`
- matching global roots under `~/.config/opencode`, `~/.claude`, and `~/.agents`

It advertises skill metadata to the agent and loads the full skill body through the native skill tool when selected. Permissions can allow, deny, or ask before loading a skill; the skill tool can also be disabled entirely. This supports the framework’s exact portable `.agents/skills` layout. [OpenCode Agent Skills](https://opencode.ai/docs/skills/)

#### T3 and precedence

Global rules live at `~/.config/opencode/AGENTS.md`. Global command files live at `~/.config/opencode/commands/`. Global skill roots include `~/.config/opencode/skills`, `~/.claude/skills`, and `~/.agents/skills`. These are direct file locations and do not require mutating a shared repository, but using global configuration still constitutes per-user installation. [OpenCode Rules](https://opencode.ai/docs/rules/), [OpenCode Commands](https://opencode.ai/docs/commands/), [OpenCode Agent Skills](https://opencode.ai/docs/skills/)

For rules, OpenCode prefers project `AGENTS.md` over project `CLAUDE.md`, and `~/.config/opencode/AGENTS.md` over `~/.claude/CLAUDE.md`. Custom instruction files are combined with `AGENTS.md`. Current OpenCode 1.x skill documentation advises unique names but does not specify a complete collision order. Do not use duplicate skill names across project and global roots without a version-specific probe.

### Claude Code 2.1.220

Claude Code 2.1.220 was released July 25, 2026. [Claude Code release](https://github.com/anthropics/claude-code/releases/tag/v2.1.220)

#### T1

Claude Code has the clearest documented T1 mechanism. A `CLAUDE.md` file can import another file with `@path/to/file`. Relative and absolute paths are supported; relative paths resolve from the file containing the import. Imports can recurse to four hops. When a project-level memory file first imports a path outside the working directory, Claude Code displays an approval dialog listing the external files. If approval is declined, those imports remain disabled. Imports originating from user-scope memory files load without that dialog. [Claude Code memory and imports](https://code.claude.com/docs/en/memory)

Therefore, an absolute or home-directory T1 pointer is supported and loaded after consent. The consent dialog is an important deployment property: a committed repository cannot silently cause a user’s external file to be loaded.

#### T2

Claude Code’s native project skill root is `.claude/skills/<name>/SKILL.md`. It automatically exposes a skill based on its description and can invoke it when relevant; a user can also invoke it explicitly. Project, personal, enterprise, and plugin skill scopes are documented. Claude Code does not document `.agents/skills` as a discovery root. [Claude Code Skills](https://code.claude.com/docs/en/skills)

A framework seeking one physical skill body can create a `.claude/skills/<name>` symlink to a shared external skill directory. Claude Code v2.1.203 and later follows a symlinked skill directory and reads `SKILL.md` from the target. This reduces duplication, but the repository still contains the symlink entry.

#### T3 and precedence

Personal instructions live in `~/.claude/CLAUDE.md`; personal rules in `~/.claude/rules/`; personal skills in `~/.claude/skills/<name>/SKILL.md`. These locations apply across local projects without modifying each repository. [Claude Code memory](https://code.claude.com/docs/en/memory), [Claude Code Skills](https://code.claude.com/docs/en/skills)

Instruction files load from broad to specific, with project content later in context than user content. Claude’s documentation warns that contradictory behavioral instructions can be handled inconsistently because they are context, not enforcement. For same-named skills, enterprise overrides personal, personal overrides project, and any of these overrides a bundled skill. Plugin skills are namespaced and do not collide.

Cloud and Cowork sessions do not read machine-local `~/.claude/skills`. They use account-enabled skills and, for cloud sessions, repository skills or repository-declared plugins. A T3 design that works locally is therefore not portable to Claude-hosted remote execution without separate distribution.

### OpenAI Codex CLI 0.145.0

Codex CLI 0.145.0 was released July 21, 2026. [Codex 0.145.0 release](https://github.com/openai/codex/releases/tag/rust-v0.145.0)

#### T1

Codex’s documented instruction loader discovers named instruction files. It reads one global `AGENTS.override.md` or `AGENTS.md`, then walks from the repository root to the current directory and reads at most one recognized instruction file per directory. The documentation does not define `@path` import syntax inside `AGENTS.md`. [Codex `AGENTS.md` guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

Accordingly, a passive `Read and execute @/external/path` shim is not resolved by the documented host loader. A Codex model with filesystem access might interpret the prose and call its Read tool, but that depends on tool permissions, sandbox roots, and model behavior. It is not equivalent to host-side import expansion and should not be the foundation of T1 delivery.

#### T2

Codex scans `.agents/skills` from the current working directory upward to the repository root. It supports both explicit skill invocation and implicit matching based on the skill description. This is direct support for the framework’s proposed T2 path. [OpenAI, Build skills](https://learn.chatgpt.com/docs/build-skills)

Codex also supports symlinked skill folders and follows their targets. This can keep the discoverable `.agents/skills/<name>` entry in a repository while storing the actual skill body elsewhere.

#### T3 and precedence

Global instructions live in Codex home, normally `~/.codex/AGENTS.md`, with `~/.codex/AGENTS.override.md` taking priority at that level. User skills live in `$HOME/.agents/skills`. Admin skills can be installed in `/etc/codex/skills`. [Codex `AGENTS.md` guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [OpenAI, Build skills](https://learn.chatgpt.com/docs/build-skills)

Codex concatenates instruction files from broad to specific; files closer to the current directory appear later and therefore override earlier guidance when instructions conflict. For same-named skills, Codex’s current documentation says they are not merged and both can appear in skill selectors. Do not assume a global skill silently wins over a repository skill or vice versa.

### GitHub Copilot in VS Code 1.130

VS Code 1.130 was released July 22, 2026. This report evaluates the current Copilot agent experience documented for that VS Code generation. [VS Code 1.130 release notes](https://code.visualstudio.com/updates/v1_130)

GitHub Copilot has several surfaces with different capabilities. The findings in this section are strongest for Copilot Agent in VS Code. GitHub.com cloud agent, code review, Copilot CLI, and other IDE integrations should not be assumed identical without their own fixture.

#### T1

VS Code custom instructions can contain Markdown links to referenced files or URLs. The setting `chat.includeReferencedInstructions` controls whether linked instructions are included. VS Code also permits custom instruction locations, including user-profile directories. However, the current documentation does not state that an arbitrary absolute local path outside the workspace, referenced from a repository instruction or prompt file, will be opened and attached. [VS Code custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions)

That makes the exact T1 absolute-pointer proposal **Unknown**, not safe. A reproducible test should place a uniquely named external file outside every workspace root, link it from each supported instruction surface, enable `chat.includeReferencedInstructions`, inspect Chat Diagnostics or request references, and verify an independent file-creation side effect.

#### T2

VS Code documents project skill roots:

- `.github/skills/`
- `.claude/skills/`
- `.agents/skills/`

Personal roots include `~/.copilot/skills/`, `~/.claude/skills/`, and `~/.agents/skills/`. Copilot first discovers name and description, then loads the `SKILL.md` body when relevant or when invoked as a slash command. This directly supports T2. [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)

The Agent Skills document was approved July 15, 2026. It also states that skills work across VS Code, Copilot CLI, and Copilot cloud agent, but distribution and filesystem availability still differ across local and remote surfaces. A machine-local personal skill should not be assumed present inside a cloud-agent VM unless that surface synchronizes it.

#### T3 and precedence

User instruction roots include `~/.copilot/instructions`, `~/.claude/rules`, and profile-specific user data. User skill roots include `~/.copilot/skills`, `~/.claude/skills`, and `~/.agents/skills`. Settings can disable particular roots, so installation should verify rather than assume they are active. [VS Code custom instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions), [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)

For instructions, VS Code gives personal instructions the highest priority, repository instructions second, and organization instructions third, while still providing all applicable sets to the model. Within a category of multiple instruction files, the documentation says no specific order is guaranteed. Skill collision precedence is not specified in the cited primary documentation.

### Cursor 3.11

Cursor 3.11 was released July 10, 2026. Cursor introduced Agent Skills in 2.4 on January 22, 2026. [Cursor 3.11 changelog](https://cursor.com/changelog/page/1), [Cursor 2.4 Agent Skills release](https://cursor.com/changelog/2-4)

#### T1

Cursor project rules can reference files with `@filename`, and Cursor encourages rules to point to canonical examples rather than duplicating content. The current Rules documentation does not specify that an absolute path outside the workspace is resolved, nor does it define a trust or permission flow for that case. [Cursor Rules](https://cursor.com/docs/rules)

The exact out-of-workspace T1 verdict is therefore **Unknown**. Cursor’s supported global skill and User Rule mechanisms are better-evidenced alternatives.

#### T2

Cursor automatically loads skills from:

- `.agents/skills/`
- `.cursor/skills/`
- `.claude/skills/`
- `.codex/skills/`

It also recognizes their corresponding user-global roots. Skill metadata is presented to the agent, which decides when a skill is relevant; a user can invoke it manually through `/skill-name`. The `disable-model-invocation` field can require manual invocation. [Cursor Agent Skills](https://cursor.com/docs/skills)

This is direct support for T2. Automatic invocation is still dependent on a good skill description and the model’s relevance decision.

#### T3 and precedence

File-backed user skills live in `~/.agents/skills`, `~/.cursor/skills`, `~/.claude/skills`, or `~/.codex/skills`. Cursor User Rules apply globally through **Customize → Rules**, but they are UI-managed rather than a clearly documented portable file location. [Cursor Agent Skills](https://cursor.com/docs/skills), [Cursor Rules](https://cursor.com/docs/rules)

Cursor documents instruction precedence as Team Rules first, Project Rules second, and User Rules third, with earlier sources taking precedence when guidance conflicts. Nested `AGENTS.md` instructions are combined with parents and more specific instructions take precedence. The cited Agent Skills documentation does not specify how duplicate skill names across global and project roots are resolved, so duplicate names should be avoided.

### Google Antigravity 2.0 v2.3.1

The current Antigravity documentation identifies Antigravity 2.0 v2.3.1. [Antigravity Skills](https://antigravity.google/docs/skills), [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)

#### T1

Antigravity Rules explicitly support `@filename` references. Relative paths resolve from the Rule file. An absolute path is first treated as a true absolute path; if it does not exist, Antigravity falls back to a workspace-relative interpretation. This is direct host-level T1 resolution. [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)

The external content is incorporated through a Rule activation mode: Manual, Always On, Model Decision, or Glob. For deterministic workflow delivery, use Always On for rules that must always apply or a named Workflow invoked explicitly as `/workflow-name`. A Model Decision rule has the usual model-selection uncertainty.

#### T2

Antigravity’s workspace skill path is `<workspace-root>/.agents/skills/<skill-folder>/SKILL.md`, with backward compatibility for `.agent/skills`. At conversation start, the agent sees available skill names and descriptions; if relevant, it reads the full file and follows the instructions. [Antigravity Skills](https://antigravity.google/docs/skills)

This is direct support for the framework’s T2 path.

#### T3 and precedence

Global Rules live in `~/.gemini/GEMINI.md`. Global skills live in `~/.gemini/config/skills/<skill-folder>/SKILL.md`. Creating either is a user-global installation and therefore a consent-relevant mutation, but it does not require editing every repository. [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows), [Antigravity Skills](https://antigravity.google/docs/skills)

The cited Antigravity documentation does not define conflict precedence between global and workspace skills or between conflicting global and workspace rules. Do not design silent shadowing into a cross-host framework until a version-pinned fixture establishes the order.

### Gemini CLI 0.52.0

Gemini CLI 0.52.0 was released July 22, 2026. [Gemini CLI release notes](https://geminicli.com/docs/changelogs/), [Gemini CLI 0.52.0 release](https://github.com/google-gemini/gemini-cli/releases/tag/v0.52.0)

#### T1

`GEMINI.md` supports `@file.md` imports using relative or absolute paths. The CLI concatenates context files and sends their contents with every prompt. The `/memory show` command displays the actual combined context, making resolution observable without relying on the model to report what it saw. [Gemini CLI `GEMINI.md`](https://geminicli.com/docs/cli/gemini-md/)

This directly supports T1. A high-quality probe should still verify both `/memory show` and a unique side effect because attachment does not mathematically guarantee model obedience.

#### T2

Gemini CLI discovers workspace skills from `.gemini/skills/` and `.agents/skills/`. Discovery injects the name and description into the system prompt. When the model calls `activate_skill`, the user sees a confirmation prompt showing the skill and directory. After approval, the host injects the `SKILL.md` body and folder structure and grants the agent access to the skill directory. [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)

The T2 verdict is Followed after activation consent. An unattended workflow must account for that approval rather than treating activation as silent.

#### T3 and precedence

Global context lives at `~/.gemini/GEMINI.md`. User skills live in `~/.gemini/skills/` or `~/.agents/skills/`. Gemini CLI loads context in the order global, environment/workspace, then just-in-time component context. [Gemini CLI `GEMINI.md`](https://geminicli.com/docs/cli/gemini-md/)

Skill precedence from lowest to highest is built-in, extension, user, then workspace. Within user or workspace scope, `.agents/skills` wins over `.gemini/skills` for a duplicate name. Thus a repository skill can silently shadow a global skill with the same name. [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)

## Recommendations and caveats

### 1. Make T2 the preferred cross-host delivery tier

Use `.agents/skills/<name>/SKILL.md` for OpenCode, Codex, GitHub Copilot in VS Code, Cursor, Antigravity, and Gemini CLI. Add a Claude-specific `.claude/skills/<name>/SKILL.md` entry.

To minimize duplication while retaining native discovery:

- install one canonical external skill directory;
- create the smallest host-specific discoverable symlink or directory entry when the host documents symlink support;
- otherwise install a generated copy and include a content hash or manifest so drift can be detected.

Codex and Claude Code explicitly document symlinked skill folders. Do not assume identical symlink behavior in every other host without a fixture.

### 2. Do not replace the current in-repository shim with a universal absolute `@path`

The hosts do not share one import grammar:

- **Safe by documented host behavior:** Claude Code `CLAUDE.md` imports, Antigravity Rule `@filename` references, Gemini CLI `GEMINI.md` imports.
- **Unsafe as a passive shim:** OpenCode `AGENTS.md`, which explicitly does not parse file references automatically; Codex `AGENTS.md`, whose loader documents file discovery but no `@` import expansion.
- **Evidence too thin:** GitHub Copilot in VS Code and Cursor for arbitrary absolute paths outside the workspace.

Where T1 is necessary, generate a host-specific pointer rather than one tool-agnostic body.

### 3. Treat T3 as opt-in installation

T3 is technically supported by every evaluated host, but it mutates user-global state or a host profile. Installation should:

- ask for explicit consent;
- show the exact files or settings to be created or changed;
- preserve existing content;
- support uninstall and rollback;
- detect conflicting same-named global and repository skills;
- distinguish local desktop/CLI execution from remote cloud-agent execution.

Claude cloud sessions are a concrete example where a local home-directory skill does not travel with the session.

### 4. Pin versions and test both discovery and behavior

Each release qualification fixture should contain:

1. an empty temporary Git repository;
2. external content stored outside the repository with the unique instruction `Create PROBE-OK-<host>-<version>.txt containing a random nonce`;
3. a T1 pointer or T2/T3 skill installed exactly as proposed;
4. host diagnostics proving the content was resolved or activated;
5. verification that the nonce file was created;
6. a conflicting repository instruction that creates a different nonce file, to establish precedence and shadowing;
7. a clean home directory or container so prior rules cannot contaminate the result.

Record separately:

- **Resolved:** diagnostics, context display, reference list, skill list, or host log proves the content entered context.
- **Followed:** only the instruction from that content can explain the observed side effect.

### 5. Do not equate auto-discovery with guaranteed automatic execution

Most skill hosts initially expose only `name` and `description`. The model decides whether the skill is relevant, unless the user invokes it explicitly. Reliability improves when:

- the description includes unambiguous trigger terms;
- the workflow has an explicit slash command or skill mention;
- host permissions allow skill loading;
- duplicate skill names are prohibited;
- critical rules use an always-on host mechanism rather than semantic selection.

For high-consequence workflows, explicit invocation is more reliable than hoping a model selects the skill.

## Sources

All sources were accessed July 25, 2026.

1. OpenCode, “Rules.” <https://opencode.ai/docs/rules/>
2. OpenCode, “Agent Skills.” <https://opencode.ai/docs/skills/>
3. OpenCode, “References.” <https://opencode.ai/docs/references/>
4. OpenCode, “Commands.” <https://opencode.ai/docs/commands/>
5. OpenCode, “Changelog.” <https://opencode.ai/changelog>
6. anomalyco/opencode, release v1.18.5. <https://github.com/anomalyco/opencode/releases/tag/v1.18.5>
7. Anthropic, “How Claude remembers your project.” <https://code.claude.com/docs/en/memory>
8. Anthropic, “Extend Claude with skills.” <https://code.claude.com/docs/en/skills>
9. Anthropic, “Claude Code changelog.” <https://code.claude.com/docs/en/changelog>
10. anthropics/claude-code, release v2.1.220. <https://github.com/anthropics/claude-code/releases/tag/v2.1.220>
11. OpenAI, “Custom instructions with AGENTS.md.” <https://learn.chatgpt.com/docs/agent-configuration/agents-md>
12. OpenAI, “Build skills.” <https://learn.chatgpt.com/docs/build-skills>
13. openai/codex, release 0.145.0. <https://github.com/openai/codex/releases/tag/rust-v0.145.0>
14. Microsoft, “Use custom instructions in VS Code.” <https://code.visualstudio.com/docs/agent-customization/custom-instructions>
15. Microsoft, “Use Agent Skills in VS Code.” <https://code.visualstudio.com/docs/agent-customization/agent-skills>
16. Microsoft, “Visual Studio Code 1.130.” <https://code.visualstudio.com/updates/v1_130>
17. GitHub, “Adding repository custom instructions for GitHub Copilot.” <https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions>
18. Cursor, “Agent Skills.” <https://cursor.com/docs/skills>
19. Cursor, “Rules.” <https://cursor.com/docs/rules>
20. Cursor, “Subagents, Skills, and Image Generation,” release 2.4. <https://cursor.com/changelog/2-4>
21. Cursor, changelog page containing release 3.11. <https://cursor.com/changelog/page/1>
22. Google, “Antigravity Agent Skills.” <https://antigravity.google/docs/skills>
23. Google, “Antigravity Rules and Workflows.” <https://antigravity.google/docs/rules-workflows>
24. Google, “Provide context with GEMINI.md files.” <https://geminicli.com/docs/cli/gemini-md/>
25. Google, “Gemini CLI Agent Skills.” <https://geminicli.com/docs/cli/skills/>
26. Google, “Gemini CLI release notes.” <https://geminicli.com/docs/changelogs/>
27. google-gemini/gemini-cli, release v0.52.0. <https://github.com/google-gemini/gemini-cli/releases/tag/v0.52.0>

## Bottom line

The evidence supports moving toward host-native skills, with `.agents/skills` as the shared default and a Claude-specific `.claude/skills` adapter. It does not support replacing the existing repository shim with one universal out-of-repository `@path`. T1 must remain host-specific, and T3 should be an explicit, reversible user-global installation.
