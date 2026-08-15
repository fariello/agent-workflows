---
id: obveju
created: 20260813
set: awnamespace
order: 01
topic: [slash-commands, namespace, installer, host-adapters]
model: gpt56medium
kind: research-report
status: reference
outcome: none-yet
summary: gpt56medium report.
consumed-by: []
---

# Namespaced slash commands across AI coding agents

**Research date and access date for all web sources:** 2026-08-13  
**Scope:** OpenCode, Claude Code, Cursor, GitHub Copilot, Windsurf, Gemini CLI and Gemini Code Assist, and Google Antigravity  
**Evidence policy:** Statements labeled **Documented** come from current official documentation. Statements labeled **Inference** are design conclusions from those facts. **Unknown** means the official documentation reviewed does not specify the behavior.

## 1. Executive summary and recommended portable design

No reviewed host documents a registry-level command hierarchy whose literal syntax is `/aw migrate`. Where a host supports a file-system or package namespace, it normally renders with a colon, notably Gemini CLI's `/aw:migrate` and Claude Code plugin skills such as `/aw:migrate`. The literal space form is instead an **argument dispatcher**: register one command named `aw`, accept the remainder of the input, treat its first token as the verb, validate it, and route to the corresponding workflow.

The recommended portable design is therefore a project-level `/aw` dispatcher plus generated flat aliases. Use `/aw <verb> [args...]` on OpenCode, Claude Code, VS Code-hosted GitHub Copilot, Gemini CLI, and Antigravity IDE, all of which officially document either arbitrary trailing command text or an argument mechanism. Treat Cursor and Windsurf support for trailing dispatcher text as requiring a small version-pinned smoke test because their current public docs document invocation but not argument substitution. Generate `/aw-<verb>` as the guaranteed fallback on those two hosts and as an optional discovery aid everywhere. Gemini Code Assist has no verified public project custom-command mechanism and should be marked unsupported unless a current product-specific mechanism is found.

Do not make subdirectory layout the cross-host abstraction. It produces `/aw:migrate` only on Gemini CLI, and a similar colon form for Claude Code plugins, while Cursor explicitly says category folders do not affect a skill's command name. A dispatcher also keeps the visible command list small, avoids a broad collection of globally collision-prone verbs, and mirrors the existing `aw <verb>` CLI.

## 2. Per-host findings

### 2.1 OpenCode

#### 1. Custom slash-command mechanism

**Documented.** Project commands are Markdown files under `.opencode/commands/`; global commands are under `~/.config/opencode/commands/`. The filename becomes the command name. The Markdown body is the prompt template, and YAML frontmatter may include `description`, `agent`, and `model`. Commands may alternatively be declared under the `command` key in `opencode.json(c)`. OpenCode's command documentation was last updated 2026-08-12. [OpenCode Commands](https://opencode.ai/docs/commands/)

```markdown
<!-- .opencode/commands/aw.md -->
---
description: Run an AW workflow: setup, assess, migrate, or another supported verb
---

Interpret `$1` as the AW verb and the remaining values as its arguments.
Validate the verb against the supported workflow registry, then run that workflow.

Full input: $ARGUMENTS
```

Invocation: `/aw migrate --dry-run`

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **Unknown / do not rely on it.** The official page says the Markdown filename becomes the command name and gives no recursive directory or separator rule. It does not document `.opencode/commands/aw/migrate.md` as either `/aw:migrate` or `/aw migrate`.
- **Argument-based:** **Yes.** `$ARGUMENTS` receives all trailing text and `$1`, `$2`, and later positional placeholders are supported. Exact invocation: `/aw migrate --dry-run`. [OpenCode Commands, Arguments](https://opencode.ai/docs/commands/#arguments)
- **Flat prefix:** **Yes.** `.opencode/commands/aw-migrate.md` produces `/aw-migrate`. [OpenCode Commands, Markdown](https://opencode.ai/docs/commands/#markdown)

The space form is not a parser-level subcommand. It is one custom command named `aw` with `migrate` in its argument string.

#### 3. Collision surface

**Documented.** OpenCode lists all built-in TUI commands, and `/aw` is not in that list as of 2026-08-12. A custom command with the same name as a built-in overrides the built-in. [OpenCode TUI command list](https://opencode.ai/docs/tui#commands), [OpenCode collision rule](https://opencode.ai/docs/commands/#built-in)

#### 4. Arguments and discovery

`/aw migrate --dry-run` can expose `migrate` as `$1`, `--dry-run` as `$2`, and the entire string as `$ARGUMENTS`. The `description` is shown in the TUI while the user types the command. The docs do not describe verb-level autocomplete inside `$ARGUMENTS`, so users discover `/aw`, not a structured list of its verbs. [OpenCode arguments](https://opencode.ai/docs/commands/#arguments), [OpenCode description](https://opencode.ai/docs/commands/#description)

#### 5. Portability verdict

**Best shape:** `/aw <verb> [args...]`. It exactly matches the requested text, implemented as argument dispatch. Generate `/aw-migrate` aliases if verb-level autocomplete is more important than a compact command list.

### 2.2 Claude Code (Anthropic)

#### 1. Custom slash-command mechanism

**Documented.** Claude Code has merged custom commands into skills. Existing `.claude/commands/<name>.md` files still work, while the recommended project layout is `.claude/skills/<skill-name>/SKILL.md`; the personal layout is `~/.claude/skills/<skill-name>/SKILL.md`. A skill uses YAML frontmatter plus Markdown instructions. The directory name determines the command for project and personal skills. Current documentation contains version-specific behavior through at least Claude Code v2.1.227. [Claude Code skills and legacy commands](https://code.claude.com/docs/en/slash-commands)

```markdown
<!-- .claude/skills/aw/SKILL.md -->
---
description: Run an AW repository workflow
argument-hint: <verb> [args...]
arguments:
  - verb
disable-model-invocation: true
---

Validate `$verb` against the supported AW workflow registry.
Dispatch to that workflow. Preserve all additional values from `$ARGUMENTS`.
```

Invocation: `/aw migrate --dry-run`

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **Not as `/aw migrate`.** Claude documents a real colon namespace for plugin skills: a plugin named `aw` with `skills/migrate/SKILL.md` is `/aw:migrate`. Project skill category subfolders are not documented as a command family. Nested project-directory qualification is a different feature, such as `/apps/web:deploy`, and applies to monorepo scope and clashes. [Claude command-name rules](https://code.claude.com/docs/en/slash-commands#how-a-skill-gets-its-command-name)
- **Argument-based:** **Yes.** Text after a command becomes arguments. Skills support `$ARGUMENTS`, indexed values, shorthand such as `$0`, and named positional arguments. Exact invocation: `/aw migrate --dry-run`. [Claude Commands reference](https://code.claude.com/docs/en/commands), [Claude string substitutions](https://code.claude.com/docs/en/slash-commands#available-string-substitutions)
- **Flat prefix:** **Yes.** `.claude/skills/aw-migrate/SKILL.md` is `/aw-migrate`; the legacy `.claude/commands/aw-migrate.md` also remains valid. [Claude command-name rules](https://code.claude.com/docs/en/slash-commands#how-a-skill-gets-its-command-name)

#### 3. Collision surface

The current built-in and bundled command reference does not list `/aw`. For local skills, precedence across scopes is enterprise, then personal, then project. A local skill overrides a bundled skill with the same name; a skill overrides a same-named legacy command; plugin skills retain their `plugin-name:skill-name` namespace. Synced claude.ai skills lose to built-ins and local sources. [Claude skill precedence](https://code.claude.com/docs/en/slash-commands#where-skills-live), [Claude command reference](https://code.claude.com/docs/en/commands)

#### 4. Arguments and discovery

Claude supports `argument-hint`, which appears during autocomplete, plus named and positional substitutions. Typing `/` lists commands and typing letters filters them. A dispatcher can therefore appear as `/aw <verb> [args...]`, but the menu will not automatically enumerate verbs unless separate aliases are also installed. Plugin commands give genuine discoverable entries such as `/aw:migrate`. [Claude frontmatter reference](https://code.claude.com/docs/en/slash-commands#frontmatter-reference), [Claude Commands reference](https://code.claude.com/docs/en/commands)

#### 5. Portability verdict

**Best repository-native shape:** `/aw <verb> [args...]`. **Best true namespace if distributing a Claude plugin:** `/aw:<verb>`. The latter is host-specific and does not match the requested space syntax.

### 2.3 Cursor

#### 1. Custom slash-command mechanism

**Documented, current mechanism.** Cursor 2.4+ recommends Agent Skills and can migrate both workspace and user slash commands with `/migrate-to-skills`. A project skill is `.cursor/skills/<skill-name>/SKILL.md`; Cursor also reads `.agents/skills/`, plus compatible Claude and Codex skill directories. Skills use Markdown and may use YAML frontmatter, including `name`, `description`, and `paths`. Invoke a skill with `/skill-name` or attach it with `@skill-name`. [Cursor Skills](https://cursor.com/help/customization/skills)

```markdown
<!-- .cursor/skills/aw/SKILL.md -->
---
name: aw
description: Runs an AW workflow selected by the user's verb
---

Treat the text supplied with this invocation as `<verb> [args...]`.
Validate the verb and run the matching AW workflow.
```

Cursor's current public page acknowledges that workspace and user slash commands exist and can be migrated, but it no longer specifies their legacy file schema on that page. For new installations, skills are the better documented target.

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **No.** Cursor recursively scans category folders, but explicitly says the skill name comes from the folder containing `SKILL.md`, not the category folder. Thus `.cursor/skills/aw/migrate/SKILL.md` remains `/migrate`, not `/aw:migrate` or `/aw migrate`. [Cursor Skills](https://cursor.com/help/customization/skills)
- **Argument-based:** **Unknown in current official docs.** The docs show direct `/skill-name` invocation but do not document a trailing-argument placeholder or guarantee that `/aw migrate` passes `migrate` to the skill. This is likely usable as ordinary chat text, but that is an inference and should be smoke-tested on the pinned Cursor version.
- **Flat prefix:** **Yes.** `.cursor/skills/aw-migrate/SKILL.md` has skill name `aw-migrate` and is invoked as `/aw-migrate`. [Cursor Skills](https://cursor.com/help/customization/skills)

#### 3. Collision surface

Cursor's published CLI slash-command list does not include `/aw`, but IDE availability can differ from the CLI. The current Skills page does not document built-in-versus-custom collision precedence. Therefore `/aw` appears low-risk but collision resolution is **unknown** and must not be assumed. [Cursor CLI slash commands](https://cursor.com/docs/cli/reference/slash-commands), [Cursor Skills](https://cursor.com/help/customization/skills)

#### 4. Arguments and discovery

Typing `/skill-name` runs a skill, and `@skill-name` attaches one. The current official docs do not define argument interpolation, flags, or structured verb autocomplete for skills. Cursor's Customize UI can manage commands and skills, but no documented hierarchical command picker behavior was found. [Cursor customization overview](https://cursor.com/docs/customize-cursor), [Cursor Skills](https://cursor.com/help/customization/skills)

#### 5. Portability verdict

**Safe documented shape:** `/aw-<verb>`. **Candidate exact shape:** `/aw <verb>`, only after automated acceptance testing confirms that trailing text reaches the skill in every supported Cursor release. Do not infer namespace behavior from category subfolders.

### 2.4 GitHub Copilot chat and agent

#### 1. Custom slash-command mechanism

**Documented for local IDE agents.** Copilot prompt files are Markdown files with a `.prompt.md` extension, normally stored at workspace path `.github/prompts`. Optional YAML frontmatter includes `name`, `description`, `argument-hint`, `agent`, `model`, and `tools`; if `name` is absent, the filename is used. GitHub marks prompt files as public preview and limits them to VS Code, Visual Studio, and JetBrains IDEs. VS Code's current reference was updated 2026-08-12. [GitHub prompt-file tutorial](https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file), [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files)

```markdown
<!-- .github/prompts/aw.prompt.md -->
---
name: aw
description: Run an AW workflow
argument-hint: <verb> [args...]
agent: agent
---

Interpret the additional chat text as `<verb> [args...]`.
Validate the verb and execute the corresponding AW workflow.
```

Important scope limit: VS Code states that agents running on its Agent Host do not use prompt files and recommends converting such prompts to Agent Skills. The GitHub Copilot app's public slash-command reference covers GitHub-provided commands, not repository-defined prompt files. [VS Code prompt-file scope](https://code.visualstudio.com/docs/agent-customization/prompt-files), [GitHub Copilot app slash commands](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands)

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **Not documented.** Prompt command identity comes from the `name` field or filename. No official mapping from `.github/prompts/aw/migrate.prompt.md` to a namespace was found.
- **Argument-based:** **Yes in VS Code-hosted chat.** The docs explicitly allow extra information after the prompt name, with examples such as `/create-react-form formName=MyForm` and `/create-api for listing customers`. Exact invocation: `/aw migrate --dry-run`. This is trailing prompt text rather than typed positional interpolation. [VS Code, Use a prompt file in chat](https://code.visualstudio.com/docs/agent-customization/prompt-files#use-a-prompt-file-in-chat)
- **Flat prefix:** **Yes.** `.github/prompts/aw-migrate.prompt.md` or `name: aw-migrate` is invoked as `/aw-migrate`. [VS Code prompt-file format](https://code.visualstudio.com/docs/agent-customization/prompt-files#prompt-file-format)

#### 3. Collision surface

Neither the GitHub prompt-file guide nor the VS Code prompt-file reference documents collision precedence among built-ins, extension-contributed commands, user prompts, workspace prompts, and skills. `/aw` is not in the current GitHub Copilot app built-in list, but that list is context-dependent and can change. Treat the name as currently clear, not reserved by contract. [GitHub Copilot app slash commands](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands), [VS Code prompt-file FAQ](https://code.visualstudio.com/docs/agent-customization/prompt-files#frequently-asked-questions)

#### 4. Arguments and discovery

Prompt files can display `argument-hint`; `${input:name}` can collect structured user input, and users can append arbitrary extra information to the slash invocation. Prompt files appear beside Agent Skills after typing `/`, and VS Code offers a Quick Pick plus recommended actions. No nested verb menu is documented. [VS Code prompt-file format](https://code.visualstudio.com/docs/agent-customization/prompt-files#prompt-file-format), [VS Code prompt invocation](https://code.visualstudio.com/docs/agent-customization/prompt-files#use-a-prompt-file-in-chat)

#### 5. Portability verdict

**Best local IDE shape:** `/aw <verb> [args...]`. **Not portable to every Copilot surface:** GitHub.com, the GitHub Copilot app, cloud/Agent Host sessions, and different IDE integrations do not share one documented repository slash-command contract. Generate a Copilot Agent Skill in addition to, or instead of, a prompt file where that runtime is required, but do not claim that it registers the same slash command everywhere.

### 2.5 Windsurf

#### 1. Custom slash-command mechanism

**Documented.** Windsurf Cascade Workflows are Markdown files. Workspace workflows live at `.windsurf/workflows/*.md`; global workflows live at `~/.codeium/windsurf/global_workflows/*.md`; enterprise system paths also exist. A workflow contains a title, description, and ordered instructions, is limited to 12,000 characters, and is invoked as `/workflow-name`. Workflows are manual-only. [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)

```markdown
<!-- .windsurf/workflows/aw-migrate.md -->
# AW migrate

Migrate this repository using the AW migration workflow.

1. Validate prerequisites.
2. Run the migration workflow.
3. Report changes and validation results.
```

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **No documented command mapping.** Windsurf discovers `.windsurf/workflows/` directories at multiple workspace locations, but documents command syntax only as `/[workflow-name]`. It does not describe `workflows/aw/migrate.md` or a colon/space conversion.
- **Argument-based:** **Unknown.** The public Workflow page does not document parameters, placeholders, or trailing argument semantics for workflows.
- **Flat prefix:** **Yes.** A workflow named `aw-migrate` is invoked as `/aw-migrate`. [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)

#### 3. Collision surface

Windsurf documents precedence as system, workspace, global, then built-in. Therefore an enterprise system workflow named `aw` would override a workspace dispatcher, while a workspace workflow overrides global and built-in versions. The current docs do not identify `aw` as a built-in workflow. [Windsurf workflow priority](https://docs.windsurf.com/windsurf/cascade/workflows#workflow-priority)

#### 4. Arguments and discovery

Workflows are listed as available commands and are manually invoked by slash name. No official argument, flag, or nested autocomplete behavior is documented. Workflows can call other workflows, which is useful for alias wrappers, but the docs do not specify parameter forwarding. [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)

#### 5. Portability verdict

**Safe documented shape:** `/aw-<verb>`. `/aw <verb>` is ill-advised as the primary contract until a pinned-version test proves argument forwarding and that behavior is monitored across upgrades.

### 2.6 Gemini CLI and Gemini Code Assist

#### 1. Custom slash-command mechanism

**Gemini CLI, documented.** Custom commands are TOML files under project path `.gemini/commands/` or user path `~/.gemini/commands/`. Project commands override same-named user commands. `prompt` is required and `description` is optional. The official page was last updated 2026-04-30. [Gemini CLI custom commands](https://geminicli.com/docs/cli/custom-commands/)

```toml
# .gemini/commands/aw.toml
description = "Run an AW workflow: /aw <verb> [args...]"
prompt = """
Interpret the first token of this input as the AW verb.
Validate it and run the matching workflow, preserving remaining arguments:

{{args}}
"""
```

**Gemini Code Assist, unknown/unverified.** No current official Code Assist documentation describing repository-defined custom slash commands was located in the reviewed Google documentation. Do not assume Gemini CLI's `.gemini/commands/*.toml` loader is implemented by an IDE Code Assist surface merely because both products use Gemini.

#### 2. Namespacing and subcommands

- **Subdirectory namespacing, Gemini CLI:** **Yes, with a colon.** `.gemini/commands/aw/migrate.toml` becomes `/aw:migrate`, not `/aw migrate`. [Gemini CLI naming and namespacing](https://geminicli.com/docs/cli/custom-commands/#naming-and-namespacing)
- **Argument-based, Gemini CLI:** **Yes.** `{{args}}` receives all text following the command name. If absent, Gemini CLI appends the full typed command to the prompt. Exact invocation: `/aw migrate --dry-run`. [Gemini CLI handling arguments](https://geminicli.com/docs/cli/custom-commands/#handling-arguments)
- **Flat prefix, Gemini CLI:** **Yes.** `.gemini/commands/aw-migrate.toml` produces `/aw-migrate`.
- **Gemini Code Assist:** All three mechanisms are **unverified**.

#### 3. Collision surface

Gemini CLI explicitly documents project-over-user precedence. The custom-command page does not document custom-versus-built-in collision resolution, and the current command docs reviewed do not identify `/aw` as built-in. Use `/commands list` to inspect loaded command files and `/commands reload` after changes. [Gemini CLI custom commands](https://geminicli.com/docs/cli/custom-commands/)

#### 4. Arguments and discovery

`{{args}}` preserves raw text in the main prompt and is shell-escaped when substituted inside `!{...}`. `/commands list` shows available custom command files, `/commands reload` reloads them, and `description` appears in `/help`. Subdirectory commands are discoverable as colon-qualified names such as `/aw:migrate`. [Gemini CLI custom commands](https://geminicli.com/docs/cli/custom-commands/)

#### 5. Portability verdict

**Best matching shape:** `/aw <verb> [args...]` through one `aw.toml` dispatcher. **Best host-native namespace:** `/aw:<verb>`. Prefer the dispatcher for cross-host consistency and optionally generate colon aliases for Gemini-native discovery. Gemini Code Assist should be reported as unsupported/unverified, not silently treated as Gemini CLI.

### 2.7 Google Antigravity

#### 1. Custom slash-command mechanism

**Documented for Antigravity IDE.** Workflows are Markdown files, created as global or workspace customizations, and invoked as `/workflow-name`. Google's official codelab gives the concrete project path `.agents/workflows/startcycle.md` and shows YAML `description` frontmatter. The current Antigravity docs navigation identifies Antigravity 2.0 v2.8.0 and IDE v2.5.2. [Antigravity Workflows](https://antigravity.google/docs/ide/workflows), [Google codelab with `.agents/workflows`](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)

```markdown
<!-- .agents/workflows/aw.md -->
---
description: Run an AW workflow selected by verb
---

When the user invokes `/aw <verb> [args...]`, validate `<verb>` against the
supported AW workflow registry, then execute that workflow with the remaining input.
```

Antigravity CLI v1.1.12 publicly documents built-in slash commands and plugin components, but the reviewed CLI pages do not provide a file-level custom slash-command schema equivalent to the IDE workflow page. Scope the strong conclusion below to Antigravity IDE. [Antigravity CLI features](https://antigravity.google/docs/cli/features)

#### 2. Namespacing and subcommands

- **Subdirectory namespacing:** **Not documented.** The IDE docs specify `/workflow-name`; they do not map nested workflow paths to colon or space syntax.
- **Argument-based:** **Yes for the IDE, demonstrated by an official Google codelab.** It defines `/startcycle <idea>` and invokes it with a quoted idea. The analogous exact form is `/aw migrate --dry-run`. The workflow itself must interpret the input; no formal placeholder syntax is documented. [Google Antigravity codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)
- **Flat prefix:** **Yes.** A workflow file named `aw-migrate.md` is invoked as `/aw-migrate` under the documented `/workflow-name` rule. [Antigravity Workflows](https://antigravity.google/docs/ide/workflows)

#### 3. Collision surface

The current IDE and CLI docs reviewed do not list `/aw` as built-in and do not document custom-versus-built-in collision precedence. This is **unknown**, so installation should include a command inventory smoke test.

#### 4. Arguments and discovery

The official codelab instructs the user to type `/` to open the custom commands menu, choose `startcycle`, and then supply an idea. This supports discovery of the top-level workflow and trailing input, but no nested verb autocomplete or formal flag parser is documented. [Google Antigravity codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)

#### 5. Portability verdict

**Best IDE shape:** `/aw <verb> [args...]`, implemented by natural-language dispatch. **CLI status:** custom command registration is insufficiently documented in the reviewed public CLI pages; do not claim parity without a version-specific test.

## 3. Cross-host comparison

Legend: **Yes** means current official documentation supports the mechanism. **No** means documentation contradicts the mechanism. **Unknown** means no official contract was found. A colon namespace is real namespacing, but it does not match the requested space syntax.

| Host | Subdirectory or package namespace | Argument dispatcher | Flat prefix | Recommended exact invocation | Source and source date |
|---|---|---|---|---|---|
| OpenCode | Unknown | Yes, `$ARGUMENTS`, `$1...` | Yes | `/aw migrate --dry-run` | [Commands](https://opencode.ai/docs/commands/), updated 2026-08-12, accessed 2026-08-13 |
| Claude Code | Yes for plugins as `/aw:migrate`; no documented `/aw migrate` hierarchy | Yes, `$ARGUMENTS`, indexed and named args | Yes | `/aw migrate --dry-run`; optional plugin `/aw:migrate` | [Skills](https://code.claude.com/docs/en/slash-commands), current through at least v2.1.227, accessed 2026-08-13 |
| Cursor | No for category subfolders | Unknown | Yes | `/aw-migrate`; test `/aw migrate` before enabling | [Skills](https://cursor.com/help/customization/skills), Cursor 2.4+, accessed 2026-08-13 |
| GitHub Copilot in VS Code | Not documented | Yes, trailing chat text | Yes | `/aw migrate --dry-run` | [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files), updated 2026-08-12, accessed 2026-08-13 |
| GitHub Copilot app / Agent Host | No repository prompt-file contract | No verified custom dispatcher | No verified custom flat command | Unsupported through prompt files | [GitHub app commands](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands), [VS Code scope warning](https://code.visualstudio.com/docs/agent-customization/prompt-files), accessed 2026-08-13 |
| Windsurf | Not documented | Unknown | Yes | `/aw-migrate` | [Workflows](https://docs.windsurf.com/windsurf/cascade/workflows), accessed 2026-08-13 |
| Gemini CLI | Yes as `/aw:migrate` | Yes, `{{args}}` or default append | Yes | `/aw migrate --dry-run`; optional `/aw:migrate` | [Custom commands](https://geminicli.com/docs/cli/custom-commands/), updated 2026-04-30, accessed 2026-08-13 |
| Gemini Code Assist | Unverified | Unverified | Unverified | Unsupported/unverified | No public custom-command contract located in official docs reviewed on 2026-08-13 |
| Antigravity IDE | Not documented | Yes, demonstrated with trailing input | Yes | `/aw migrate --dry-run` | [Workflows](https://antigravity.google/docs/ide/workflows), Antigravity 2.0 v2.8.0 / IDE v2.5.2; [codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity), accessed 2026-08-13 |
| Antigravity CLI | Plugin components are called namespaced, exact custom workflow syntax not specified | Unknown | Unknown | Do not promise until tested | [CLI features](https://antigravity.google/docs/cli/features), CLI v1.1.12, accessed 2026-08-13 |

### Single most portable design

Implement a generated `aw` dispatcher whose prompt contract is:

```text
/aw <verb> [workflow-specific arguments and flags...]
```

The dispatcher should:

1. Parse the first token as a verb.
2. Match only a generated allowlist of installed workflow IDs.
3. Show compact usage and the valid verbs when the verb is absent or unknown.
4. Pass the untouched remainder to the selected workflow.
5. Avoid executing a similarly named workflow inferred by the model.

This gives the exact requested form on OpenCode, Claude Code, VS Code-hosted Copilot, Gemini CLI, and Antigravity IDE. On Cursor and Windsurf, publish `/aw-<verb>` as the supported shape unless a release-gated integration test confirms dispatcher arguments. Gemini Code Assist and non-IDE Copilot surfaces need an explicit unsupported status rather than a misleading shim.

For host-native enhancements, also generate `/aw:<verb>` where the host has a documented colon namespace, currently Gemini CLI and optionally a Claude Code plugin. These are convenience entries, not the portable API.

## 4. Back compatibility and deprecation

### Recommended rollout

1. **Release N, additive:** Install the new `/aw` dispatcher and keep every old flat name, such as `/assess` and `/setup-repo`. Update each old shim's description to say `Legacy alias for /aw assess` or the correct canonical form. Do not change behavior.
2. **Release N+1, visible notice:** Have legacy aliases print one concise notice before running: `Deprecated alias: use /aw assess. This alias remains available through <date or major version>.` Avoid repeating the notice more than once per session if the host makes that practical.
3. **At least one normal release cycle later:** Stop generating legacy aliases by default for new installations, but preserve aliases already present during upgrades unless the user opts into cleanup.
4. **Next major release:** Remove generated legacy aliases only with an explicit migration command or opt-in flag. Keep a compatibility package or generation option for teams with documentation and automation that still uses old names.

### Implementation pattern

Keep the actual workflows host-neutral in one canonical registry. Generate thin shims for each host. The dispatcher and all aliases should resolve the same workflow ID rather than duplicate the workflow text. Add contract tests for:

- `/aw` with no verb;
- every valid `/aw <verb>`;
- unknown verbs;
- quoted arguments and flags;
- every legacy alias;
- collision reporting;
- command-menu discoverability after installation.

### Host-specific alias notes

- **OpenCode:** Generate both `.opencode/commands/aw.md` and old-name Markdown files. Since custom commands override built-ins, refuse or loudly warn before installing an alias that shadows one. [OpenCode collision rule](https://opencode.ai/docs/commands/#built-in)
- **Claude Code:** Prefer one `.claude/skills/aw/SKILL.md` dispatcher. Legacy `.claude/commands/*.md` files still work, but a same-named skill wins. If aliases are skills, set `disable-model-invocation: true` so deprecated aliases do not enlarge Claude's automatic-selection surface. [Claude precedence and invocation control](https://code.claude.com/docs/en/slash-commands)
- **Cursor:** Cursor 2.4+'s `/migrate-to-skills` may convert old commands. Keep alias skills manually invocable and avoid near-duplicate descriptions that could encourage ambiguous automatic skill selection. [Cursor Skills](https://cursor.com/help/customization/skills)
- **GitHub Copilot:** Generate separate `.prompt.md` aliases for local IDE support. Prompt files are preview and do not reach Agent Host sessions, so do not treat them as universal Copilot aliases. [VS Code prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files)
- **Windsurf:** A legacy workflow may call another workflow, so a small alias workflow can delegate to a canonical flat workflow. Parameter forwarding is undocumented; aliases that need arguments should repeat the minimal dispatch instruction or remain separate generated shims. [Windsurf Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
- **Gemini CLI:** Generate `aw.toml`, optional `aw/<verb>.toml` colon aliases, and old flat TOML files. Run `/commands reload`; validate with `/commands list`. Project commands override user commands. [Gemini CLI custom commands](https://geminicli.com/docs/cli/custom-commands/)
- **Antigravity IDE:** Workflow-to-workflow calls are documented, so old names can be wrappers. Keep argument handling in the wrapper's natural-language contract because no placeholder syntax is documented. [Antigravity Workflows](https://antigravity.google/docs/ide/workflows)

## 5. Open risks, unknowns, and non-viable cases

1. **A space is not a namespace delimiter.** `/aw migrate` is portable only as model-visible argument dispatch. It lacks parser-enforced verb validation and verb-level autocomplete unless the shim supplies those behaviors.
2. **Dispatcher reliability is prompt-dependent.** Put an explicit, generated verb table in the dispatcher and require exact matching. For workflows with side effects, require confirmation and do not let the model invent or fuzzy-match a verb.
3. **Cursor:** category subfolders definitively do not create a namespace, and trailing argument behavior is not documented. Use flat-prefixed commands unless tested.
4. **Windsurf:** neither arguments nor nested namespace behavior is documented. Use flat-prefixed workflows as the supported contract.
5. **GitHub Copilot:** prompt files are preview, IDE-limited, and excluded from VS Code Agent Host. "Copilot" is not one uniform slash-command host. A compatibility matrix must distinguish VS Code extension-host chat, Visual Studio, JetBrains, GitHub.com, the GitHub Copilot app, and remote agents.
6. **Gemini Code Assist:** no verified public project custom-command loader was found. Do not install Gemini CLI TOML shims and claim IDE support.
7. **Antigravity CLI:** the IDE workflow mechanism is public, while current CLI pages do not give an equivalent custom command file contract. Keep IDE and CLI capabilities separate.
8. **Collision behavior is uneven:** OpenCode, Claude Code, Windsurf, and Gemini CLI document at least some precedence. Cursor, Copilot prompt files, and Antigravity do not fully document built-in/custom collision resolution. Installers should inventory `/aw` and all aliases before writing files, then fail with an actionable message on ambiguity.
9. **Colon aliases fragment documentation.** `/aw:migrate` is useful on Gemini CLI and Claude plugins, but should remain secondary if the goal is one cross-host user guide.
10. **Version drift:** Every host in this report is changing quickly. Pin minimum versions in generated metadata where possible and run end-to-end command discovery and invocation tests in CI or release qualification.

## 6. References

All references were accessed 2026-08-13.

1. OpenCode, **Commands**, last updated 2026-08-12: <https://opencode.ai/docs/commands/>
2. OpenCode, **TUI**, last updated 2026-08-12: <https://opencode.ai/docs/tui>
3. Anthropic, **Extend Claude with skills**, current documentation with behavior through at least v2.1.227: <https://code.claude.com/docs/en/slash-commands>
4. Anthropic, **Commands**, Claude Code command reference: <https://code.claude.com/docs/en/commands>
5. Cursor, **Skills**, including Cursor 2.4+ migration: <https://cursor.com/help/customization/skills>
6. Cursor, **Customize Cursor**: <https://cursor.com/docs/customize-cursor>
7. Cursor, **CLI slash commands**: <https://cursor.com/docs/cli/reference/slash-commands>
8. GitHub, **Your first prompt file**: <https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file>
9. Visual Studio Code, **Use prompt files in VS Code**, updated 2026-08-12: <https://code.visualstudio.com/docs/agent-customization/prompt-files>
10. GitHub, **Slash commands for the GitHub Copilot app**: <https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands>
11. Windsurf, **Workflows**: <https://docs.windsurf.com/windsurf/cascade/workflows>
12. Gemini CLI, **Custom commands**, last updated 2026-04-30: <https://geminicli.com/docs/cli/custom-commands/>
13. Google Antigravity, **Workflows**, Antigravity 2.0 v2.8.0 / IDE v2.5.2 documentation set: <https://antigravity.google/docs/ide/workflows>
14. Google for Developers, **Build Autonomous Developer Pipelines using agents.md and skills.md in Antigravity**: <https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity>
15. Google Antigravity, **Antigravity CLI Features**, CLI v1.1.12 documentation set: <https://antigravity.google/docs/cli/features>
