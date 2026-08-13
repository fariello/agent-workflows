---
id: 2bodwq
created: 20260813
set: awnamespace
order: 04
topic: [slash-commands, namespace, installer, host-adapters]
model: reconciliation
kind: reconciliation-report
status: active
outcome: adopted
summary: Deciding doc. Adopt a single /aw dispatcher fed by one host-neutral verb registry (public syntax /aw <verb> [args...]); do not install /aw-<verb> flat commands by default, offer them only per selected compatibility-risk host.
consumed-by: []
---

# Consolidated research report: namespaced slash commands across AI coding agents

**Prepared:** 2026-08-13  
**Updated decision:** 2026-08-13  
**Inputs consolidated:** `aw-namespace-research-report.gemini31pro.md`, `aw-namespace-research-report.gpt56medium.md`, and `aw-namespace-research-report.sonnet5.md`  
**Scope:** OpenCode, Claude Code, Cursor, GitHub Copilot, Windsurf / Cascade, Gemini CLI and Gemini Code Assist, and Google Antigravity

## 1. Executive summary

Use a single `/aw` command as the normal installation everywhere a repository-defined command can receive trailing text. The public syntax is `/aw <verb> [args...]`. Technically, `<verb>` is input to one command rather than a parser-level subcommand on most hosts, but that distinction does not matter to users when the dispatcher works reliably. OpenCode, Claude Code, and Gemini CLI document deterministic argument capture. VS Code Copilot and Antigravity accept trailing text through model-mediated interpretation, and maintainer field experience reports zero problems using `/aw <verb>` in Antigravity CLI with Gemini 3.5 or 3.6 Flash.

Do **not** install `/aw-<verb>` commands by default. Doing so would recreate the command-list pollution this namespace is intended to eliminate. Instead, the installer should identify the target environments, explain where `/aw <verb>` is undocumented or unverified, and only then offer an optional, host-scoped compatibility pack containing `/aw-<verb>` commands. A user who does not select a compatibility-risk host should see only `/aw`.

This recommendation deliberately distinguishes three claims: documented deterministic support, observed model-mediated success, and unverified support. "Not documented" does not mean "does not work." It means the framework should expose the uncertainty, test pinned versions, and offer fallback shims only when the user actually needs them.

## 2. Method and source reconciliation

The three model reports were compared claim by claim. Conflicts were resolved in this order:

1. Current official product documentation.
2. Current official examples and codelabs.
3. Official repositories, issues, and transition announcements.
4. Maintainer field evidence, clearly labeled as observed behavior rather than a vendor contract.
5. Third-party or community material when official documentation is silent.

The GPT and Sonnet reports contain the strongest primary-source coverage. The Gemini report reaches a conservative flat-command conclusion but misses some documented argument behavior. The consolidated recommendation also incorporates maintainer field evidence supplied after the three reports were produced.

### Confidence vocabulary

- **Deterministic dispatcher:** the host documents a placeholder or argument API that exposes text after `/aw`.
- **Model-mediated dispatcher:** the host accepts trailing text and the command instructions ask the model to interpret the first token as a verb.
- **Field-proven, undocumented:** repeated real use succeeds, but the vendor does not publish a stable argument contract.
- **Flat compatibility pack:** optional per-verb commands such as `/aw-migrate`, installed only for selected compatibility-risk hosts.
- **Unverified:** neither the reports nor current official documentation establish a stable repository command contract for the product surface.

## 3. Findings shared across the reports

1. No surveyed host defines a parser-level space namespace. In `/aw migrate`, `/aw` is the registered command and `migrate` is trailing input.
2. A single dispatcher still gives users the desired `/aw <verb>` experience when trailing input is available.
3. OpenCode, Claude Code, and Gemini CLI document argument capture suitable for deterministic dispatch.
4. Gemini CLI has genuine colon namespacing: `.gemini/commands/aw/migrate.toml` maps to `/aw:migrate`.
5. Claude Code plugins can expose colon commands such as `/aw:migrate`, but normal project skill organization does not create `/aw <verb>` subcommands.
6. Cursor category folders organize skills but do not create command namespaces.
7. Windsurf Workflows are documented as flat slash commands and do not document argument interpolation.
8. GitHub Copilot is several product surfaces, not one uniform custom-command host.
9. Gemini Code Assist does not inherit Gemini CLI's `.gemini/commands` contract merely because both products use Gemini.

The reports' previous conservative conclusion, that flat commands should exist everywhere, is rejected as a default product design. Reliability remains important, but it should be addressed through targeted installer choices rather than globally duplicating every verb in slash autocomplete.

## 4. Material disparities and resolutions

### 4.1 OpenCode argument dispatch

One input report classifies OpenCode as flat-only. The other two identify `$ARGUMENTS` and positional `$1`, `$2`, and later placeholders.

**Resolution:** OpenCode supports a deterministic `/aw <verb>` dispatcher. Subdirectory namespacing remains undocumented. Generate `.opencode/commands/aw.md`, not one default file per verb. [OpenCode Commands](https://opencode.ai/docs/commands/)

### 4.2 Claude Code namespaces and positional indexing

All reports agree that `/aw <verb>` works through argument dispatch. Current skill documentation supports `$ARGUMENTS`, indexed values such as `$ARGUMENTS[0]`, shorthand `$0`, and named positional arguments. OpenCode uses `$1` for its first positional argument, so shared templates require host-specific rendering.

**Resolution:** use one project skill at `.claude/skills/aw/SKILL.md`. A Claude plugin may optionally expose `/aw:<verb>`, but colon commands should not become the portable public API. [Claude Code Skills](https://code.claude.com/docs/en/slash-commands), [Claude Code Commands](https://code.claude.com/docs/en/commands)

### 4.3 Copilot trailing text

One report treats Copilot as strictly flat. Another points to the official VS Code example `/create-api for listing customers`.

**Resolution:** supported VS Code prompt files accept trailing text, so `/aw migrate` is syntactically valid. Dispatch is model-mediated because no `$ARGUMENTS`-style contract is documented. Other Copilot surfaces, including the GitHub app and Agent Host, do not share the same repository prompt-file contract. [VS Code Prompt Files](https://code.visualstudio.com/docs/agent-customization/prompt-files), [GitHub Copilot App Commands](https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands)

### 4.4 Antigravity IDE and Antigravity CLI

The reports split Antigravity into two surfaces. IDE Workflows demonstrate trailing input. CLI Skills become slash commands, but the official CLI page does not document placeholders or a nested invocation syntax.

**Resolution:** official docs establish model-mediated `/aw <verb>` for the IDE more strongly than for the CLI. However, maintainer field evidence reported on 2026-08-13 says `/aw <verb>` has worked without issue in Antigravity CLI, usually with Gemini 3.5 or 3.6 Flash. This is meaningful product evidence and justifies making `/aw` the normal Antigravity CLI installation. It remains an observed behavior, not a published compatibility guarantee, so the installer may describe it as field-proven and offer the optional compatibility pack.

[Antigravity IDE Workflows](https://antigravity.google/docs/ide/workflows), [Antigravity CLI Plugins and Skills](https://antigravity.google/docs/cli/plugins), [Google Antigravity codelab](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)

### 4.5 Gemini Code Assist

The supplied reports do not establish a current repository-installed slash-command mechanism for Gemini Code Assist with sufficient primary-source support. Google's product transition also changed which users remain on Code Assist.

**Resolution:** do not reuse the Gemini CLI adapter. Ask about this surface during installation and state that AW slash-command support is unverified. If a working custom-command mechanism is later confirmed, test `/aw <verb>` before offering flat fallbacks. [Google transition announcement](https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)

### 4.6 Windsurf product continuity

The current Workflow page is under Devin Desktop documentation and says Workflows are Cascade-specific.

**Resolution:** maintain Windsurf / Cascade as a compatibility-risk adapter. The flat workflow name is documented; trailing-argument behavior is not. Prefer a real version test where possible. Otherwise let the installer offer the compatibility pack only to users targeting this surface. [Current Cascade Workflows documentation](https://docs.devin.ai/desktop/cascade/workflows)

## 5. Per-host findings and installation policy

### OpenCode

- **Definition:** project `.opencode/commands/<name>.md`; global `~/.config/opencode/commands/<name>.md`; optional YAML frontmatter; JSON configuration is also supported.
- **Dispatch:** deterministic through `$ARGUMENTS` and positional `$1`, `$2`, and later values.
- **Primary installation:** `.opencode/commands/aw.md` invoked as `/aw migrate --dry-run`.
- **Namespace:** no documented directory-to-command namespace.
- **Collision:** a custom command overrides a same-named built-in. `/aw` was not in the reviewed built-in list.
- **Discovery:** one `/aw` entry appears; the dispatcher should print verb help when invoked without arguments.
- **Policy:** install only `/aw`. Do not ask about flat compatibility unless a collision or version test fails. Confidence: high.

### Claude Code

- **Definition:** preferred `.claude/skills/<name>/SKILL.md`; legacy `.claude/commands/<name>.md` remains supported.
- **Dispatch:** deterministic through `$ARGUMENTS`, indexed values, shorthand values, and named arguments.
- **Primary installation:** `.claude/skills/aw/SKILL.md` invoked as `/aw migrate --dry-run`.
- **Namespace:** plugins can expose `/aw:migrate`; project directory nesting does not provide the desired space namespace.
- **Collision:** local skills can override bundled skills, and skills beat same-named legacy commands.
- **Discovery:** `/` filtering and `argument-hint` are documented. Verbs should also be listed in the skill description and no-argument help.
- **Policy:** install only `/aw`. Do not generate colon or flat variants by default. Confidence: high.

### Cursor

- **Definition:** current Agent Skills in `.cursor/skills/<name>/SKILL.md`; Cursor also reads `.agents/skills/` and compatibility directories.
- **Dispatch:** no official positional or aggregate argument substitution was established by the reports.
- **Primary candidate:** one `aw` skill invoked as `/aw migrate --dry-run`, with model-mediated routing instructions.
- **Namespace:** category folders do not affect skill names.
- **Collision:** precedence is not clearly documented.
- **Policy:** compatibility-risk host. Install `/aw` first, but tell the user support is not contractually verified. Offer host-scoped `/aw-<verb>` commands only if the user wants a conservative fallback. Confidence: high for flat skills, low for argument dispatch.

### GitHub Copilot

- **Definition in supported local IDE chat:** `.github/prompts/<name>.prompt.md` with optional `name`, `description`, `argument-hint`, `agent`, `model`, and `tools` frontmatter.
- **Dispatch:** VS Code accepts trailing text, but routing is model-mediated.
- **Primary candidate:** `.github/prompts/aw.prompt.md` invoked as `/aw migrate --dry-run`.
- **Surface limitation:** prompt files are preview and limited to supported IDE experiences. VS Code says Agent Host agents do not use them. The GitHub Copilot app exposes GitHub-defined commands, not repository prompt files.
- **Policy:** for supported local IDE chat, install `/aw` and label it model-mediated. For the app, Agent Host, or remote surfaces, report that no equivalent repository command is verified. Offer flat commands only where the selected surface can load them and the user explicitly opts in. Confidence: medium for local prompt files, low outside that surface.

### Windsurf / Cascade

- **Definition:** `.windsurf/workflows/*.md`, with global and enterprise locations also documented.
- **Dispatch:** no argument placeholder or forwarding contract is documented.
- **Primary candidate:** `.windsurf/workflows/aw.md` invoked as `/aw migrate --dry-run`, subject to a version smoke test or model-mediated routing.
- **Namespace:** no nested command mapping is documented.
- **Surface limitation:** Workflows are Cascade-specific and unsupported by Devin Local Agent.
- **Policy:** compatibility-risk host. Explain the uncertainty, then ask whether to install `/aw-<verb>` workflows. Confidence: high for flat workflows, low for argument dispatch.

### Gemini CLI

- **Definition:** project `.gemini/commands/*.toml`; global `~/.gemini/commands/*.toml`; required `prompt`, optional `description`.
- **Dispatch:** deterministic through `{{args}}`; default argument appending is also documented.
- **Primary installation:** `.gemini/commands/aw.toml` invoked as `/aw migrate --dry-run`.
- **Native namespace:** `.gemini/commands/aw/migrate.toml` becomes `/aw:migrate`.
- **Policy:** install only `/aw`. Do not generate colon or flat commands by default because both add one entry per verb. Confidence: high.

### Gemini Code Assist

- **Definition and custom slash-command contract:** unverified by the consolidated primary-source record.
- **Policy:** ask whether the user targets Code Assist and explain that `/aw <verb>` installation is not currently verified. Do not silently emit Gemini CLI files. A flat fallback should be offered only if the installer has a confirmed Code Assist adapter. Confidence: low.

### Antigravity IDE

- **Definition:** workspace or global Workflows invoked as `/workflow-name`; Google's codelab uses `.agents/workflows/<name>.md`.
- **Dispatch:** trailing input is demonstrated, though no formal placeholder syntax is documented.
- **Primary installation:** `.agents/workflows/aw.md` invoked as `/aw migrate --dry-run`.
- **Policy:** install only `/aw` by default. Offer flat compatibility only if a supported-version test fails or the user requests it. Confidence: medium.

### Antigravity CLI

- **Definition:** `.agents/skills/<name>.md` for workspace skills and `~/.gemini/antigravity-cli/skills/` globally. Skills become slash commands.
- **Dispatch:** no placeholder is documented, but repeated maintainer use of `/aw <verb>` has reportedly produced zero issues with Gemini 3.5 and 3.6 Flash.
- **Primary installation:** one `aw` skill invoked as `/aw migrate --dry-run`.
- **Namespace:** plugin bundles are described as namespaced, but official docs do not specify a user invocation such as `/aw:migrate` for plugin skills.
- **Policy:** install only `/aw` by default. Mark behavior as field-proven but not guaranteed by the vendor. Offer flat compatibility as an explicit opt-in, not as the presumed safe default. Confidence: high in observed behavior, low in the formal contract.

## 6. Cross-host comparison

| Host surface | `/aw <verb>` basis | Default install | Ask about `/aw-<verb>`? | Exact normal invocation |
|---|---|---|---|---|
| OpenCode | Documented deterministic arguments | `/aw` | No, unless test or collision fails | `/aw migrate --dry-run` |
| Claude Code | Documented deterministic arguments | `/aw` | No | `/aw migrate --dry-run` |
| Cursor | Model-mediated, unverified contract | `/aw` candidate | Yes | `/aw migrate --dry-run` |
| Copilot, supported local IDE chat | Documented trailing text, model-mediated | `/aw` | Optional, if the selected IDE loads the fallback | `/aw migrate --dry-run` |
| Copilot app / Agent Host / remote | No verified shared repository contract | None or surface-specific adapter | Explain limitation first | Unverified |
| Windsurf / Cascade | Trailing arguments undocumented | `/aw` candidate | Yes | `/aw migrate --dry-run` |
| Gemini CLI | Documented `{{args}}` | `/aw` | No | `/aw migrate --dry-run` |
| Gemini Code Assist | Repository command contract unverified | None | Only with a verified adapter | Unverified |
| Antigravity IDE | Trailing input demonstrated | `/aw` | Normally no | `/aw migrate --dry-run` |
| Antigravity CLI | Maintainer field-proven, undocumented | `/aw` | Offer as optional insurance | `/aw migrate --dry-run` |

## 7. Recommended framework and installer design

### 7.1 One semantic registry and one visible namespace

Define workflows once in a host-neutral manifest:

```yaml
namespace: aw
verbs:
  setup:
    workflow: setup-repo
  assess:
    workflow: assess
  migrate:
    workflow: migrate
```

Generate one host-specific `/aw` dispatcher from this registry. The dispatcher owns the verb allowlist, help text, argument forwarding, and safety metadata. Host templates handle placeholder differences without changing the public syntax.

### 7.2 Installer flow

The installer should detect configured hosts where possible and ask only about ambiguous surfaces. A recommended interaction is:

1. **Target selection:** "Which coding environments will use AW workflows?"
2. **Risk disclosure, only when needed:** "`/aw <verb>` is not formally documented or is not verified in: Cursor, Windsurf / Cascade, Gemini Code Assist, and some GitHub Copilot surfaces. Antigravity CLI works in maintainer use but lacks a documented argument contract."
3. **Compatibility choice:** "Install per-verb compatibility commands such as `/aw-migrate` for these selected environments? This adds one slash-menu entry per verb."
4. **Default answer:** No. Install only `/aw` unless the user opts in.

When targets are known, scope the choice per host. Selecting flat compatibility for Windsurf must not create flat commands in Claude Code, OpenCode, or Gemini CLI.

Suggested noninteractive options:

```text
aw install                         # /aw only, warns about selected risk hosts
aw install --compat=cursor         # flat compatibility only for Cursor
aw install --compat=cursor,windsurf
aw install --compat=all-risk-hosts # explicit, never implied
```

If the installer can run a real host smoke test, prefer evidence over a generic prompt. A successful `/aw` argument-routing test should suppress the fallback recommendation for that host and version.

### 7.3 Dispatcher contract

Every `/aw` dispatcher should:

1. Treat the first trailing token as an exact verb ID.
2. Reject unknown verbs and display the generated allowlist.
3. Forward the remaining input to the selected workflow.
4. Avoid fuzzy matching or invented verbs.
5. Preserve confirmation requirements for destructive or externally visible actions.
6. Return compact usage and the verb list when invoked without a verb.

Example:

```text
/aw
Usage: /aw <verb> [args...]
Available verbs: assess, migrate, setup

/aw migarte
Unknown AW verb: migarte
Nothing was run. Available verbs: assess, migrate, setup
```

### 7.4 Discovery without slash-menu pollution

Do not solve discovery by registering every verb. Use:

- A concise `/aw` description that names the most common verbs.
- `/aw` with no arguments as built-in help.
- `/aw help` and `/aw help <verb>` for full discovery.
- Host-native `argument-hint` fields where available.
- Repository documentation generated from the same verb registry.

This keeps one slash entry while preserving discoverability.

## 8. Back compatibility and deprecation

Existing commands such as `/assess`, `/setup-repo`, and `/assess-<verb>` should not be joined by another permanent layer of aliases.

### New installations

- Install only `/aw` on normal hosts.
- Offer `/aw-<verb>` only for user-selected compatibility-risk hosts.
- Do not install old flat command names.
- Do not install colon variants by default.

### Upgrades

1. Install `/aw` first and verify it without removing existing commands.
2. Inventory old flat commands and show the exact slash entries they occupy.
3. Ask whether to keep them for a temporary transition or remove them now.
4. If retained, make them thin aliases to the canonical workflow registry and print a concise deprecation notice.
5. Stop regenerating deprecated aliases after the published transition window.
6. Remove them only through an explicit migration choice or major-version policy.

The compatibility pack and legacy aliases are separate concepts. A team may temporarily retain `/assess` while declining `/aw-assess`, or remove old commands while selecting `/aw-assess` only for one problematic host.

### Collision policy

- Refuse to overwrite an unrelated existing `/aw` command without explicit approval.
- If `/aw` is owned by an older AW installation, update it in place.
- Show collisions before asking about compatibility commands.
- Never resolve a collision by silently generating all flat verbs.

## 9. Validation requirements

Qualify each supported host and version with these tests:

1. `/aw` appears in slash autocomplete.
2. `/aw` with no verb returns help and runs nothing.
3. `/aw <known-verb>` selects the intended workflow.
4. Unknown verbs do not fuzzy-match.
5. Additional flags, quoted strings, and paths survive forwarding.
6. The tested model does not reinterpret the verb as ordinary prose.
7. Existing `/aw` collisions are detected.
8. Optional `/aw-<verb>` commands are generated only for selected hosts.
9. Legacy aliases still work only during their declared support window.
10. Local IDE, CLI, app, Agent Host, and remote surfaces are reported separately.

Record host version and, for model-mediated dispatch, model name. Antigravity CLI's current positive field evidence should be converted into repeatable tests across the supported Gemini model set. An undocumented behavior may be accepted as supported when regression-tested, but it must remain labeled separately from a vendor guarantee.

## 10. Final recommendation

Adopt `/aw <verb> [args...]` as the single normal user interface. Install one `/aw` command, teach it to dispatch from a generated verb registry, and use `/aw`, `/aw help`, and argument hints for discovery.

Do not install `/aw-<verb>` universally. Ask about environments where `/aw <verb>` is undocumented, model-mediated, or unverified, then offer a host-scoped flat compatibility pack with an explicit warning that it adds one slash-menu entry per verb. Cursor and Windsurf / Cascade are the clearest candidates for that question. Some Copilot surfaces and Gemini Code Assist may lack a viable repository command adapter altogether. Antigravity CLI should default to `/aw` because it works in maintainer practice, while retaining the optional fallback because its argument contract is not documented.

This design accepts a small, clearly disclosed compatibility risk in exchange for the core product goal: one coherent AW namespace instead of another proliferation of slash commands.

## 11. References

All web sources were accessed 2026-08-13 unless otherwise noted.

### Primary product documentation

1. OpenCode, **Commands**, updated 2026-08-12: <https://opencode.ai/docs/commands/>
2. OpenCode, **TUI**: <https://opencode.ai/docs/tui>
3. Anthropic, **Extend Claude with skills**: <https://code.claude.com/docs/en/slash-commands>
4. Anthropic, **Commands**: <https://code.claude.com/docs/en/commands>
5. Cursor, **Skills**: <https://cursor.com/help/customization/skills>
6. Cursor, **Customize Cursor**: <https://cursor.com/docs/customize-cursor>
7. Cursor, **CLI slash commands**: <https://cursor.com/docs/cli/reference/slash-commands>
8. GitHub, **Your first prompt file**: <https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file>
9. Visual Studio Code, **Use prompt files in VS Code**, updated 2026-08-12: <https://code.visualstudio.com/docs/agent-customization/prompt-files>
10. GitHub, **Slash commands for the GitHub Copilot app**: <https://docs.github.com/en/copilot/reference/github-copilot-app-reference/slash-commands>
11. Cascade / Devin Desktop, **Workflows**: <https://docs.devin.ai/desktop/cascade/workflows>
12. Gemini CLI, **Custom commands**, updated 2026-04-30: <https://geminicli.com/docs/cli/custom-commands/>
13. Google, **Transitioning Gemini CLI to Antigravity CLI**, published 2026-05-19: <https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/>
14. Google Antigravity, **IDE Workflows**: <https://antigravity.google/docs/ide/workflows>
15. Google Antigravity, **CLI Plugins and Skills**, CLI v1.1.12 documentation set: <https://antigravity.google/docs/cli/plugins>
16. Google for Developers, **Build Autonomous Developer Pipelines using agents.md and skills.md in Antigravity**: <https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity>

### Field evidence

17. AW maintainer report, 2026-08-13: repeated successful use of `/aw <verb>`-style commands in Antigravity CLI, usually with Gemini 3.5 or 3.6 Flash, with zero observed issues. This is operational evidence, not an official vendor contract.

### Input reports

18. `aw-namespace-research-report.gemini31pro.md`
19. `aw-namespace-research-report.gpt56medium.md`
20. `aw-namespace-research-report.sonnet5.md`

The input reports also cite community sources and issue trackers. Those were useful for identifying historical inconsistencies, but the final recommendation prefers the primary documentation above and clearly labeled field evidence.
