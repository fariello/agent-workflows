# AI Coding Agent Instruction-File Discovery and Precedence Survey

**Research date:** 2026-07-12
**Scope:** How current AI coding agents discover, merge, prioritize, or ignore repository instruction files such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, tool-specific rules, and nested instruction files.

---

## Executive Conclusion

**Writing only to root `AGENTS.md` is not fully portable.**

The two most important gaps are:

- **Claude Code does not automatically read `AGENTS.md`.** It reads `CLAUDE.md`; Anthropic officially recommends importing `AGENTS.md` from `CLAUDE.md` or using a symlink.
  Source: <https://code.claude.com/docs/en/memory>

- **Gemini CLI defaults to `GEMINI.md`, not `AGENTS.md`.** It can be configured to read `AGENTS.md`, or `GEMINI.md` can import it, but neither happens by default.
  Source: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>

In both cases, the presence of the tool-specific file does not newly “turn off” `AGENTS.md`; rather, the tool does not natively discover `AGENTS.md` in the first place.

For an `AGENTS.md`-first framework, the strongest portable strategy is:

1. Always maintain the small managed block in root `AGENTS.md`.
2. When an existing `CLAUDE.md` or `GEMINI.md` is detected, also place the same small marker-delimited workflow pointer in that file.
3. Optionally create tiny adapters for detected tools, but do not create every possible tool file unconditionally.
4. Detect and warn where precedence is undocumented or another file can shadow `AGENTS.md`.
5. Do not treat repository-local `.agents/AGENTS.md` as equivalent to root `AGENTS.md`.

---

## 1. Instruction-File Behavior Matrix

“Both present” means root `AGENTS.md` plus the tool’s relevant root-level native file unless otherwise stated.

| Tool | Reads `AGENTS.md` automatically? | Native file(s) | If both are present | Does native file suppress `AGENTS.md`? | Nested/directory scope | Official source and freshness |
|---|---|---|---|---|---|---|
| **Claude Code** | **No.** Anthropic states that Claude Code reads `CLAUDE.md`, not `AGENTS.md`. | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md`, `~/.claude/CLAUDE.md`, managed-policy `CLAUDE.md`; also `.claude/rules/*.md` | Only `CLAUDE.md` is automatically read. `AGENTS.md` is included only through `@AGENTS.md`, a symlink, or generation-time incorporation by `/init`. | **No causal suppression:** `AGENTS.md` is ignored whether or not `CLAUDE.md` exists. From a framework perspective, however, `CLAUDE.md` is the only native project instruction surface. | Parent `CLAUDE.md` files are concatenated root-to-current-directory; closer files appear later. Subdirectory files are loaded when Claude works in those directories. `.claude/rules` supports path-scoped rules. | Anthropic Claude Code memory docs, checked **2026-07-12**. <https://code.claude.com/docs/en/memory> |
| **Gemini CLI 0.50.0** | **No by default.** Default filename is `GEMINI.md`. | `GEMINI.md`, configurable `context.fileName`; global `~/.gemini/GEMINI.md`; workspace `.gemini/settings.json` | Default: only `GEMINI.md`. Configure `context.fileName` with both names, or import `@AGENTS.md` from `GEMINI.md`. When configured with multiple names, files are combined; exact conflict resolution is not documented. | **No causal suppression:** default Gemini ignores `AGENTS.md` even if no `GEMINI.md` exists. | Hierarchical loading from global and workspace contexts; matching files are combined. Subdirectory context can be loaded as work enters that area. | Gemini CLI **v0.50.0, released 2026-07-08**; official docs and source checked **2026-07-12**. <https://geminicli.com/docs/changelogs/latest/> and <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md> |
| **Gemini Code Assist — VS Code** | No documented automatic support for plural `AGENTS.md`. | `GEMINI.md`, including global `~/.gemini/GEMINI.md` and project hierarchy | Only documented native context is `GEMINI.md`. Coexistence with `AGENTS.md` is not documented because `AGENTS.md` is not documented as an input. | Effectively yes for portability, but not because of suppression: `AGENTS.md` is not a documented source. | Hierarchical project context; more-specific context may supplement or override broader context. | Google Code Assist docs, checked **2026-07-12**. <https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer> |
| **Gemini Code Assist — IntelliJ** | Not plural `AGENTS.md`. Official docs mention singular `AGENT.md`. | `GEMINI.md` or root `AGENT.md`; manual `@file` context | Exact behavior when both documented filenames exist is not specified. Plural `AGENTS.md` is not documented. | `AGENTS.md` is not a documented source. | Root behavior is documented; full nested precedence is not clearly specified. | Google Code Assist docs, checked **2026-07-12**. <https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer> |
| **Google Antigravity IDE** | **Undocumented.** Current IDE rule docs do not clearly say that root `AGENTS.md` is loaded. | Global `~/.gemini/GEMINI.md`; workspace `.agents/rules/` and legacy `.agent/rules/`; `.agents/skills/` and other agent facilities | Root `AGENTS.md` plus root `GEMINI.md` coexistence in the IDE is not documented. Do not assume CLI behavior applies to the IDE. | **Undocumented / needs empirical test.** | Workspace rules can be Always On, manual, model-selected, or glob-scoped. Antigravity also maintains private artifacts/knowledge under `~/.gemini/antigravity/`. | Google Antigravity IDE docs, checked **2026-07-12**. <https://antigravity.google/docs/rules-workflows> |
| **Google Antigravity CLI** | **Yes.** Official CLI material states that root `GEMINI.md` and `AGENTS.md` are parsed. | `GEMINI.md`, `AGENTS.md` | Both are parsed; exact ordering or conflict precedence is undocumented. | No documented suppression. | Active-directory behavior is documented; complete nested conflict semantics are not. | Google Antigravity CLI/migration docs, checked **2026-07-12**. <https://antigravity.google/docs/cli-best-practices> |
| **OpenAI Codex CLI / Codex** | **Yes.** | `AGENTS.md`, `AGENTS.override.md`; configurable fallback filenames; user `~/.codex/AGENTS.md` | In each directory Codex checks `AGENTS.override.md`, then `AGENTS.md`, then configured fallback names. At most one file is selected per directory. A root `CLAUDE.md` or `GEMINI.md` is ignored by default. | No. `AGENTS.md` takes priority over configured fallback names in the same directory. | Files from repository root through current directory are combined; closer-directory instructions appear later and take precedence. | OpenAI Codex docs, checked **2026-07-12**. <https://developers.openai.com/codex/guides/agents-md> |
| **Cursor editor/agent** | **Yes.** | `.cursor/rules/*.mdc`; `AGENTS.md`; legacy `.cursorrules` is not described in the current official rules page | `AGENTS.md` and Cursor project rules are supported, but exact conflict precedence between them is not clearly documented. Root `CLAUDE.md` support is not clearly documented for the editor surface. | No documented suppression, but conflict behavior with `.cursor/rules` is insufficiently specified. | Nested `AGENTS.md` files are supported; parent and child instructions are combined, with more-specific guidance winning. `.cursor/rules` can use file globs. | Cursor rules docs, checked **2026-07-12**. <https://cursor.com/docs/rules.md> |
| **Cursor CLI** | **Yes.** | `AGENTS.md`, `CLAUDE.md`, `.cursor/rules` | Cursor CLI says it reads root `AGENTS.md` and `CLAUDE.md` when present, alongside Cursor rules. Exact conflict ordering is undocumented. | **No.** Both are loaded. | Project and scoped rule behavior is supported; exact cross-format conflict resolution is undocumented. | Cursor CLI docs, checked **2026-07-12**. <https://cursor.com/docs/cli/using.md> |
| **GitHub Copilot coding agent / GitHub.com** | **Yes.** | `AGENTS.md`, `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`; documented support also includes `CLAUDE.md` and `GEMINI.md` for some coding-agent surfaces | Documentation lists `CLAUDE.md`/`GEMINI.md` as alternatives to `AGENTS.md`, but does not precisely define what happens when root files coexist. **Needs empirical test.** | **Undocumented.** Do not assume deterministic merge or precedence. | Nested `AGENTS.md` files are supported; nearest applicable file takes precedence. Path-specific `.instructions.md` files are scoped by `applyTo`. | GitHub Copilot docs, checked **2026-07-12**. <https://docs.github.com/en/copilot/reference/custom-instructions-support> |
| **GitHub Copilot CLI / VS Code Copilot Chat** | **Yes**, though support differs by surface. | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`, `AGENTS.md`; some docs also mention `CLAUDE.md`/`GEMINI.md` | Root `AGENTS.md` and `.github/copilot-instructions.md` are documented as both being used. Repository-wide and matching path-specific instructions are also combined. Conflicting instructions may be nondeterministic. Official Copilot CLI pages are inconsistent about `CLAUDE.md`/`GEMINI.md` support. | `.github` instructions do not suppress `AGENTS.md`; both are used. Native-file coexistence with `CLAUDE.md`/`GEMINI.md` remains uncertain. | Root and nested/path-specific rules are supported. | GitHub docs, checked **2026-07-12**; documentation inconsistency noted. <https://docs.github.com/en/copilot/reference/custom-instructions-support> |
| **OpenCode** | **Yes.** | Project `AGENTS.md`; global `~/.config/opencode/AGENTS.md`; `CLAUDE.md` fallback; arbitrary files through `opencode.json` `instructions` | If both project `AGENTS.md` and `CLAUDE.md` exist, **only `AGENTS.md` is used**. `CLAUDE.md` is a fallback. | **No—the reverse. `AGENTS.md` suppresses the fallback `CLAUDE.md`.** | Searches upward and uses the first matching local rules file rather than concatenating every ancestor. Additional files may be configured explicitly. | OpenCode rules docs, updated **2026-07-10**. <https://opencode.ai/docs/rules/> |
| **Windsurf** | **Yes**, including lowercase `agents.md`. | `AGENTS.md`/`agents.md`, `.windsurf/rules/` | Root and nested `AGENTS.md` participate in Windsurf’s rule system. Exact precedence against `.windsurf/rules` is not documented. | No documented suppression. | Root is always on; nested files are scoped to their directory tree. Ancestor instructions are inherited. | Windsurf docs, checked **2026-07-12**. <https://docs.windsurf.com/es/windsurf/cascade/agents-md> |
| **Cline** | **Yes.** | `.clinerules/`, root `AGENTS.md`; compatibility with `.cursorrules` and `.windsurfrules`; global `~/.agents/AGENTS.md` | Multiple detected rule sources are exposed in the rule panel and can be enabled. Workspace rules override global rules, but exact precedence among several workspace formats is undocumented. | No documented suppression. | Workspace/global layers are documented. Nested repository `AGENTS.md` hierarchy is not clearly documented. | Cline rules docs, checked **2026-07-12**. <https://docs.cline.bot/customization/cline-rules> |
| **Zed** | **Yes, but through first-match selection.** | Ordered project candidates: `.rules`, `.cursorrules`, `.windsurfrules`, `.clinerules`, `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`; personal `~/.config/zed/AGENTS.md` | Zed uses the **first matching project file**. With only root `AGENTS.md` and `CLAUDE.md`, `AGENTS.md` wins and `CLAUDE.md` is ignored. A higher-listed file such as `.rules` suppresses `AGENTS.md`. | **Yes, some higher-priority native/compatibility files can suppress `AGENTS.md`.** `CLAUDE.md` and `GEMINI.md` do not; they are lower priority. | A full nested `AGENTS.md` hierarchy is not documented in the cited project-context behavior. | Zed agent settings docs, checked **2026-07-12**. <https://zed.dev/docs/ai/instructions> |
| **JetBrains AI agents** | Surface-specific. Junie: yes. Claude Agent: no. Copilot: yes. | Junie uses `AGENTS.md`; Claude Agent uses `CLAUDE.md`; GitHub Copilot integration supports `AGENTS.md` and `CLAUDE.md` | Junie and Claude Agent each use their own documented source. JetBrains Copilot supports both, but exact conflict order is undocumented. | Claude Agent effectively ignores `AGENTS.md`; Junie uses it; Copilot coexistence is undocumented. | Junie documentation describes root `AGENTS.md`; nested behavior is not clearly documented. | JetBrains docs, current around **June–July 2026**, checked **2026-07-12**. <https://www.jetbrains.com/help/ai-assistant/agents.html> |
| **Aider** | **Not automatically.** | `.aider.conf.yml`; instructions can be loaded with `--read`, `/read`, or configured `read: AGENTS.md` | `AGENTS.md` is used only when explicitly configured or read. | No native-file suppression; it is simply not auto-discovered. | Aider configuration has home, Git-root, and current-directory levels; later configuration wins. No automatic nested `AGENTS.md` hierarchy. | Aider docs, checked **2026-07-12**. <https://aider.chat/docs/usage/conventions.html> |
| **Amazon Q Developer** | No official automatic `AGENTS.md` support found. | `.amazonq/rules/*.md` | Root `AGENTS.md` is not a documented input. | Effectively ignored unless separately referenced through some custom workflow. | Rules are stored in project `.amazonq/rules/`; consult tool-specific scoping. | AWS documentation, checked **2026-07-12**. <https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/third-party-context-project-rules.html> |

### Note on legacy `.cursorrules`

Cursor’s current official rules page centers on `.cursor/rules` and `AGENTS.md`. I did not find a current official statement defining legacy `.cursorrules` coexistence or precedence in Cursor itself.

Other tools such as Cline and Zed explicitly recognize `.cursorrules`, but that does not establish current Cursor behavior.

Treat Cursor’s legacy file as:

> **Undocumented / requires empirical testing**

Source: <https://cursor.com/docs/rules.md>

---

## 2. The `AGENTS.md` Convention

The `agents.md` convention recommends:

- A root `AGENTS.md` for repository-wide instructions.
- Additional nested `AGENTS.md` files for package- or directory-specific instructions.
- The closest applicable `AGENTS.md` taking precedence over broader files.
- Direct user instructions taking precedence over file-based instructions.
- Plain Markdown, with no mandatory schema.

Source: <https://agents.md/>

The convention **does not define a universal precedence rule between `AGENTS.md` and `CLAUDE.md`, `GEMINI.md`, `.cursor/rules`, or other vendor-specific formats**. That behavior is left to each tool.

The `agents.md` site lists a broad ecosystem of supporting tools, but “support” does not always mean default automatic discovery. Its own instructions note, for example, that Aider must be configured to read the file and Gemini must be configured through `context.fileName`.

Therefore:

> `AGENTS.md` is a useful cross-tool convention, but it is not yet a universal loader contract.

---

## 3. Direct Answers to A–E

### A. Coexistence and precedence

**Verdict: there is no universal coexistence rule.**

- **Claude Code:** only `CLAUDE.md`; `AGENTS.md` requires import or symlink.
  Source: <https://code.claude.com/docs/en/memory>

- **Gemini CLI:** only `GEMINI.md` by default; both can be configured or imported, but conflict order is undocumented.
  Source: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>

- **OpenCode:** `AGENTS.md` wins; `CLAUDE.md` is fallback only.
  Source: <https://opencode.ai/docs/rules/>

- **Cursor CLI:** both are read; exact conflict order is undocumented.
  Source: <https://cursor.com/docs/cli/using.md>

- **Zed:** first-match list; `AGENTS.md` beats `CLAUDE.md` and `GEMINI.md`, but earlier rule files can beat `AGENTS.md`.
  Source: <https://zed.dev/docs/ai/instructions>

- **GitHub Copilot coding agent:** supports several formats, but exact root coexistence among `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` is not fully documented.
  Source: <https://docs.github.com/en/copilot/reference/custom-instructions-support>

---

### B. Does a tool-specific file suppress `AGENTS.md`?

**Verdict: sometimes `AGENTS.md` is effectively absent, but usually not because the native file’s presence toggles it off.**

- Claude Code and default Gemini simply do not auto-read `AGENTS.md`, even when no native file exists.
- OpenCode does the opposite: `AGENTS.md` suppresses the `CLAUDE.md` fallback.
- Zed can suppress `AGENTS.md` when a higher-priority first-match file such as `.rules` or `.cursorrules` exists.
- Cursor CLI reads both.
- Copilot’s `AGENTS.md` plus `CLAUDE.md`/`GEMINI.md` coexistence remains undocumented.

Your core risk is real, but its most common form is:

> **Non-recognition, not conditional shadowing.**

---

### C. Symlink/import escape hatch

**Verdict: use native imports where officially supported; do not make symlinks the universal strategy.**

- Claude Code officially supports `@AGENTS.md` in `CLAUDE.md`.
- Anthropic also documents `CLAUDE.md -> AGENTS.md` symlinks, but recommends imports as the easier cross-platform approach because Windows symlinks require additional privileges or Developer Mode.
- Gemini supports `@AGENTS.md` imports and configurable filename lists through `context.fileName`.
- Aider should use `read: AGENTS.md` or `--read`, not a symlink convention.
- Amazon Q and other native-rule systems need a tool-specific adapter; no general `@AGENTS.md` mechanism was verified.

Sources:

- <https://code.claude.com/docs/en/memory>
- <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>
- <https://aider.chat/docs/usage/conventions.html>

A symlink is compact but fragile across Windows, Git configurations, editors, containers, and tools that need native-file-specific additions.

---

### D. Nested files

**Verdict: nested support is common, but “override” versus “add” differs.**

- **Codex:** root-to-current-directory files are combined; closer instructions occur later and take precedence.
- **Claude Code:** parent files are concatenated; closer files are later, while subdirectory files can be loaded lazily.
- **Gemini CLI:** hierarchical contexts are combined.
- **Cursor:** parent and nested `AGENTS.md` instructions are combined, with the more-specific scope winning.
- **Windsurf:** root instructions are always on; nested files are scoped and inherit ancestor rules.
- **GitHub Copilot:** nearest applicable `AGENTS.md` is primary; path-specific instruction files can add scoped rules.
- **OpenCode:** uses the first local match found while walking upward, rather than combining every local ancestor file.
- **Cline, Zed, and Junie:** a complete nested `AGENTS.md` hierarchy was not clearly documented in the reviewed official sources.

---

### E. Repository `.agents/AGENTS.md`

**Verdict: no mainstream agent was found that treats `<repo>/.agents/AGENTS.md` as the repository-wide project instruction file.**

Important near-matches:

- Cline supports **global** `~/.agents/AGENTS.md`, which is in the user’s home directory, not the repository’s `.agents/` folder.
- Antigravity uses repository `.agents/rules/`, `.agents/skills/`, and related facilities, but not a documented project-level `.agents/AGENTS.md`.
- Hierarchical tools may treat `<repo>/.agents/AGENTS.md` as instructions for files **inside `.agents/`**, not for the repository as a whole.
- Codex and similar upward-search tools do not descend into an arbitrary hidden directory looking for project-wide instructions.

Your framework should not treat `.agents/AGENTS.md` as an equivalent fallback to root `AGENTS.md`.

At most, treat it as legacy framework metadata that should be:

- Migrated;
- Copied;
- Preserved with a warning; or
- Reported as non-standard.

---

## 4. What This Means for an `AGENTS.md`-First Framework

### `AGENTS.md`-only is not safe enough

Root `AGENTS.md` gives strong coverage for:

- Codex;
- OpenCode;
- Cursor;
- GitHub Copilot;
- Windsurf;
- Cline;
- Zed, unless a higher-priority file wins;
- Junie; and
- Several other compatible agents.

It does not reliably reach:

- Claude Code;
- Default Gemini CLI;
- Gemini Code Assist in VS Code;
- JetBrains Claude Agent;
- Aider without configuration;
- Amazon Q Developer;
- Potentially Antigravity IDE, whose root-file behavior remains insufficiently documented.

### Recommended installer behavior

#### 1. Always maintain root `AGENTS.md`

Continue creating or updating:

```text
<repo>/AGENTS.md
```

Use an idempotent marker-delimited block.

Do **not** substitute:

```text
<repo>/.agents/AGENTS.md
```

for the root file.

When a legacy `.agents/AGENTS.md` exists, the installer should:

- Preserve it unless migration is explicitly approved;
- Ensure root `AGENTS.md` also contains the managed block; and
- Report that `.agents/AGENTS.md` is not a mainstream project-level discovery location.

#### 2. Patch existing native files

For a framework whose goal is to advertise reusable workflows, the safest pattern is to insert the **same small managed pointer block** into an existing:

```text
CLAUDE.md
GEMINI.md
```

This is preferable to importing the entire root `AGENTS.md` because:

- The repository may contain extensive user-owned instructions.
- Tools such as Cursor CLI may already load both files, causing duplicated context.
- The framework needs only to expose its workflow index, not redefine all project policy.
- A small identical managed block is easier to compare, update, and remove.

Example:

```markdown
<!-- AGENT-WORKFLOWS:BEGIN -->
## Agent workflows

Reusable workflows are installed under `.agents/workflows/`.
Read `.agents/workflows/index.md` for available workflows and invocation instructions.
<!-- AGENT-WORKFLOWS:END -->
```

#### 3. Offer canonical-import mode separately

If a repository owner explicitly wants root `AGENTS.md` to be the canonical source of **all** shared policy, use native imports.

`CLAUDE.md`:

```markdown
@AGENTS.md
```

`GEMINI.md`:

```markdown
@AGENTS.md
```

Claude officially recommends this approach; Gemini supports the same import syntax.

This should be a separate installer mode because it has different semantics from merely publishing the framework’s workflow pointer.

#### 4. Create adapters only when justified

Recommended default policy:

- Existing `CLAUDE.md`: patch its managed block.
- Existing `GEMINI.md`: patch its managed block.
- Tool clearly detected but native file absent: offer to create a tiny adapter.
- Tool not detected: do not populate the repository with every vendor’s instruction file.
- File cannot be edited safely: warn with exact remediation instructions.

Detection signals might include:

- Tool configuration directories;
- Existing native files;
- Repository settings; or
- An explicit installer option.

#### 5. Detect first-match shadowing

For Zed, inspect its documented first-match sequence.

If a higher-priority file such as:

```text
.rules
.cursorrules
.windsurfrules
.clinerules
```

exists, root `AGENTS.md` may never be selected.

The installer should either:

- Add its small managed block to the active higher-priority file; or
- Warn that Zed will not load root `AGENTS.md`.

Do not silently assume all supported files merge.

#### 6. Treat undocumented coexistence as a warning

Warn rather than guessing for:

- GitHub Copilot coding agent with root `AGENTS.md` plus root `CLAUDE.md` or `GEMINI.md`;
- Antigravity IDE root-file behavior;
- Cursor editor precedence between `AGENTS.md` and `.cursor/rules`;
- Current Cursor behavior for legacy `.cursorrules`;
- Multiple Gemini context filenames containing contradictory instructions.

#### 7. Add an installer “doctor” report

A validation command should report something like:

```text
Root AGENTS.md:                    present and managed
Legacy .agents/AGENTS.md:         present; not project-wide for mainstream agents
Claude Code:                      CLAUDE.md exists; managed block present
Gemini:                           GEMINI.md exists; managed block missing
OpenCode:                         covered by root AGENTS.md
Codex:                            covered by root AGENTS.md
Zed:                              .rules shadows AGENTS.md
Amazon Q:                         .amazonq/rules exists; no framework adapter
Unknown coexistence conflicts:    1
```

This is more dependable than trying to force one universal layout onto tools whose loaders genuinely differ.

---

## 5. Recommended Policy Decision

For the three proposed options:

### (a) Keep `AGENTS.md` only

**Not recommended.**

It silently misses Claude Code, default Gemini, and several other tools.

### (b) Write a managed pointer block into existing `CLAUDE.md` and `GEMINI.md`

**Recommended.**

It solves the core risk with minimal repository intrusion.

Use a small framework-specific pointer block rather than duplicating the complete project instructions.

### (c) Detect and warn on shadowing

**Also recommended, in addition to (b).**

It is required for first-match tools and undocumented coexistence cases.

### Combined recommendation

> Maintain root `AGENTS.md` as the primary cross-tool surface; mirror only the framework’s small managed workflow pointer into existing native instruction files; optionally create native adapters for detected tools; and warn whenever loader behavior is unknown or another file shadows the root instruction file.

---

## 6. Confidence and Freshness

Research was checked on **2026-07-12**.

### High confidence

Official behavior is explicit for:

- Claude Code;
- Gemini CLI default filename and configuration;
- Codex;
- OpenCode;
- Cline;
- Windsurf;
- Zed;
- Aider; and
- Amazon Q’s native rule directory.

### Medium confidence

Supported inputs are documented, but exact cross-file conflict order is not, for:

- Cursor;
- GitHub Copilot;
- Antigravity CLI;
- Gemini with multiple configured context filenames;
- JetBrains Copilot integration.

### Needs empirical testing

- Antigravity IDE automatic loading of root `AGENTS.md` or root `GEMINI.md`;
- GitHub Copilot coding agent when root `AGENTS.md` and root `CLAUDE.md`/`GEMINI.md` coexist;
- Current Cursor handling of legacy `.cursorrules`;
- Exact model behavior when two merged instruction files directly contradict each other.

These products change quickly.

In particular, Gemini CLI, Antigravity, Copilot coding agents, Cursor, and IDE-integrated agents should be retested against their current versions before relying on undocumented precedence behavior.

---

## 7. Primary Sources

- AGENTS.md convention: <https://agents.md/>
- Anthropic Claude Code memory/instructions: <https://code.claude.com/docs/en/memory>
- Gemini CLI context files: <https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md>
- Gemini CLI changelog: <https://geminicli.com/docs/changelogs/latest/>
- Gemini Code Assist: <https://developers.google.com/gemini-code-assist/docs/use-agentic-chat-pair-programmer>
- Google Antigravity rules/workflows: <https://antigravity.google/docs/rules-workflows>
- Google Antigravity CLI guidance: <https://antigravity.google/docs/cli-best-practices>
- OpenAI Codex `AGENTS.md`: <https://developers.openai.com/codex/guides/agents-md>
- Cursor rules: <https://cursor.com/docs/rules.md>
- Cursor CLI: <https://cursor.com/docs/cli/using.md>
- GitHub Copilot custom-instruction support: <https://docs.github.com/en/copilot/reference/custom-instructions-support>
- OpenCode rules: <https://opencode.ai/docs/rules/>
- Windsurf `AGENTS.md`: <https://docs.windsurf.com/es/windsurf/cascade/agents-md>
- Cline rules: <https://docs.cline.bot/customization/cline-rules>
- Zed agent instructions: <https://zed.dev/docs/ai/instructions>
- JetBrains AI agents: <https://www.jetbrains.com/help/ai-assistant/agents.html>
- Aider conventions: <https://aider.chat/docs/usage/conventions.html>
- Amazon Q Developer project rules: <https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/third-party-context-project-rules.html>
