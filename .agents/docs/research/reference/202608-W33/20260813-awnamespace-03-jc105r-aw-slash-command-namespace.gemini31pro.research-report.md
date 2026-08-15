---
id: jc105r
created: 20260813
set: awnamespace
order: 03
topic: [slash-commands, namespace, installer, host-adapters]
model: gemini31pro
kind: research-report
status: reference
outcome: none-yet
summary: gemini31pro report.
consumed-by: []
---

# Slash Command Namespacing Across AI Coding Agents

## 1. Executive Summary & Recommended Portable Design
Creating a true nested namespace for slash commands (e.g., typing exactly `/aw migrate`) is highly host-dependent and generally **not portable** across the current landscape of AI coding agents. While some CLI-first tools offer namespace-like features—such as Claude Code's argument dispatch [cite: 2, 3] or Gemini CLI's colon-separated subdirectory namespacing [cite: 11]—the vast majority of IDE-integrated agents use a strict 1:1 mapping where a filename or folder name dictates the literal command string [cite: 1, 4, 7, 9, 12]. None of the surveyed tools natively support a space-separated nested command namespace through directories.

**The Single Most Portable Design:** The most robust, write-once-run-anywhere approach is the **Flat Prefix** pattern (Mechanism C). You should generate flat Markdown files (or skill directories) named `aw-<verb>` (e.g., `aw-migrate`), which produces the exact command `/aw-migrate` universally across all hosts. 

While achieving true `/aw migrate` is possible in Claude Code by writing a router script that parses trailing arguments [cite: 2], maintaining the flat `/aw-migrate` universally is the recommended path for lowest maintenance, highest compatibility, and predictable autocomplete behavior in IDEs.

## 2. Per-Host Implementation Details

### OpenCode
1. **Custom command mechanism:** Custom commands are defined as Markdown files placed in the `commands/` directory (e.g., `.opencode/commands/` for projects) [cite: 1]. 
2. **Namespacing:** (c) Flat prefix only. Filenames strictly dictate the command string [cite: 1]. 
   * **Exact invocation:** `/aw-migrate`
3. **Collision surface:** Built-in commands include `/compact`, `/init`, `/status`, `/mcp`, and `/model` [cite: 1]. The `/aw` prefix is safe from collision.
4. **Args & discovery:** Commands are discoverable via the built-in `/commands` command, and can accept trailing arguments in the TUI [cite: 1].
5. **Portability verdict:** Flat prefix (`/aw-migrate`).

### Claude Code (Anthropic)
1. **Custom command mechanism:** Commands are part of the Unified Skills System [cite: 2]. The canonical location is a directory under `.claude/skills/` containing a `SKILL.md` entrypoint (e.g., `.claude/skills/aw/SKILL.md`) [cite: 2]. Legacy flat files in `.claude/commands/` are also supported [cite: 2]. 
2. **Namespacing:** (b) Argument-based. Text following a command name is passed to the skill as arguments [cite: 2]. You could theoretically create one `.claude/skills/aw/SKILL.md` file that processes trailing text. 
   * **Exact invocation:** `/aw migrate` (where `/aw` is the command and `migrate` is the argument passed to it).
3. **Collision surface:** Built-ins include `/help`, `/clear`, `/model`, `/mcp`, and `/plan` [cite: 3]. `/aw` is safe.
4. **Args & discovery:** Commands auto-complete when typing `/` [cite: 3]. The skill receives the trailing text (`migrate`) to process [cite: 3].
5. **Portability verdict:** True `/aw <verb>` is possible via argument dispatch, but `/aw-migrate` as a distinct skill is more standard.

### Cursor
1. **Custom command mechanism:** Cursor has transitioned to the Agent Skills standard located in `.cursor/skills/` with `SKILL.md` files (compatible with `.claude/skills/`) [cite: 6]. The older system of `.cursor/commands/*.md` has been folded into skills but remains supported for backward compatibility [cite: 5]. 
2. **Namespacing:** (c) Flat prefix only. The skill folder name or the `.md` filename dictates the command [cite: 4, 6]. 
   * **Exact invocation:** `/aw-migrate`
3. **Collision surface:** Cursor features built-ins like `/run-everything`, `/plan`, `/mcp`, and `/debug` [cite: 4]. `/aw` is safe.
4. **Args & discovery:** Typing `/` in the Cursor chat surfaces available commands [cite: 4]. When selected, Cursor inserts the file's prompt text into the chat ready for the user to append context [cite: 4].
5. **Portability verdict:** Flat prefix (`/aw-migrate`).

### GitHub Copilot (Chat)
1. **Custom command mechanism:** Custom "prompt files" are stored in `.github/prompts/` (workspace) or `%APPDATA%\Code\User\prompts\` (user profile) as Markdown files [cite: 7]. 
2. **Namespacing:** (c) Flat prefix only. A file named `NAME.prompt.md` becomes `/NAME` [cite: 7]. 
   * **Exact invocation:** `/aw-migrate` (from a file named `aw-migrate.prompt.md`).
3. **Collision surface:** Copilot has built-ins (e.g., `/tests`, `/fix`, `/explain`) [cite: 8]. `/aw` is safe.
4. **Args & discovery:** Custom prompts are discovered in the chat input when typing `/` [cite: 8].
5. **Portability verdict:** Flat prefix (`/aw-migrate`).

### Windsurf
1. **Custom command mechanism:** "Workflows" are defined as Markdown files within `.windsurf/workflows/` directories [cite: 9, 10]. 
2. **Namespacing:** (c) Flat prefix only. Users invoke them in Cascade using `/[workflow-name]`, which is exactly the filename without the `.md` suffix [cite: 9, 10].
   * **Exact invocation:** `/aw-migrate`
3. **Collision surface:** Windsurf uses `.windsurfrules` files and built-in Cascade slash commands [cite: 10]. `/aw` is safe.
4. **Args & discovery:** Workflows are invoked in Cascade via the slash command and act as a sequence of steps for the agent [cite: 9]. 
5. **Portability verdict:** Flat prefix (`/aw-migrate`).

### Gemini CLI & Gemini Code Assist
1. **Custom command mechanism:** 
   * *Gemini CLI:* Custom slash commands are loaded from `.toml` files in `.gemini/commands/` [cite: 11]. 
   * *Gemini Code Assist (IDE):* Prompts are added manually via the IDE's Prompt Library [cite: 11].
2. **Namespacing:** (a) Subdirectory namespacing is natively supported by the CLI. Subdirectories are used to create namespaced commands, with the path separator converted to a colon (`:`) [cite: 11]. For example, `/.gemini/commands/aw/migrate.toml` becomes `/aw:migrate` [cite: 11]. Code Assist uses (c) Flat prefix only.
   * **Exact invocation:** `/aw:migrate` (CLI) or `/aw-migrate` (Code Assist).
3. **Collision surface:** Gemini CLI has extensive built-ins (`/about`, `/agents`, `/mcp`, `/skills`) [cite: 11]. `/aw` is safe.
4. **Args & discovery:** Gemini CLI provides an interactive TUI menu, and arguments are injected via `{{args}}` in the TOML definition [cite: 11].
5. **Portability verdict:** Fragmented. CLI supports `/aw:migrate`; IDE requires flat `/aw-migrate`.

### Antigravity CLI
1. **Custom command mechanism:** Custom "Skills" are markdown files containing a `SKILL.md` placed in `.agents/skills/` [cite: 12]. 
2. **Namespacing:** (c) Flat prefix only. A skill name automatically becomes available as a slash command [cite: 13].
   * **Exact invocation:** `/aw-migrate`
3. **Collision surface:** Antigravity has extensive built-ins including `/skills`, `/mcp`, `/agents`, and `/hooks` [cite: 13]. `/aw` is safe.
4. **Args & discovery:** Discoverable by typing `/` or listing via the `/skills` built-in command [cite: 12].
5. **Portability verdict:** Flat prefix (`/aw-migrate`).

## 3. Cross-Host Comparison Table

| Host | Mechanism | Exact Invocation | Source |
| :--- | :--- | :--- | :--- |
| **OpenCode** | Flat prefix | `/aw-migrate` | [cite: 1] |
| **Claude Code** | Argument dispatch | `/aw migrate` | [cite: 2, 3] |
| **Cursor** | Flat prefix | `/aw-migrate` | [cite: 4, 5, 6] |
| **GitHub Copilot** | Flat prefix | `/aw-migrate` | [cite: 7, 8] |
| **Windsurf** | Flat prefix | `/aw-migrate` | [cite: 9, 10] |
| **Gemini CLI** | Subdirectory namespace | `/aw:migrate` | [cite: 11] |
| **Gemini Code Assist** | Flat prefix | `/aw-migrate` | [cite: 11] |
| **Antigravity CLI** | Flat prefix | `/aw-migrate` | [cite: 12, 13] |

## 4. Back-compat + Deprecation Recommendation
If moving from legacy flat commands (e.g., `/assess`, `/setup-repo`) to a new `/aw-*` convention, follow this migration path:
1. **Duplicate Generation:** Update the framework to generate BOTH the old file (e.g., `.cursor/skills/assess/SKILL.md`) and the new file (e.g., `.cursor/skills/aw-assess/SKILL.md`).
2. **Deprecation Notice:** Inject a Markdown blockquote at the very top of the old command prompt text: `> **DEPRECATION WARNING:** The /assess command is deprecated. Please use /aw-assess going forward.`
3. **Claude Code Special Handling:** Because Claude Code merges commands into its unified skills system, creating two full skill directories for the same prompt could clutter the agent's context window [cite: 2]. Place the legacy aliases in the `.claude/commands/` folder (which is supported for backward compatibility) and the new canonical commands in the `.claude/skills/` directory [cite: 2].

## 5. Open Risks & Unknowns
* **Argument Handling in IDEs:** IDE agents (Cursor, Copilot, Windsurf) treat custom slash commands primarily as text-expansion templates or context inclusions [cite: 4, 7, 9]. If your workflows require runtime parameters to dictate branching logic (e.g., `/aw migrate --dry-run`), IDEs will struggle because they expect the user to just type context into the chat bar after the command expands. Only CLI tools (Claude Code, Antigravity, Gemini CLI) handle argument string injection and programmatic routing natively.
* **Windsurf Rules Constraints:** Windsurf supports workflows via `.windsurf/workflows/*.md`, but concurrent Cascade features and `.windsurfrules` might auto-trigger if prompt intents cross paths [cite: 10]. Workflow descriptions must clearly state they are for manual invocation only [cite: 9].

## 6. References
* [1] OpenCode: "Commands | OpenCode", https://opencode.ai/docs/commands/, accessed Aug 13, 2026.
* [2] Claude Code: "3.2 — Custom Slash Commands and Skills", https://claudecertificationguide.com/learn/3-claude-code-config/3-2-slash-commands-skills, accessed Aug 13, 2026.
* [3] Claude Code: "Slash Commands in the SDK - Claude Code Docs", https://code.claude.com/docs/en/agent-sdk/slash-commands, accessed Aug 13, 2026.
* [4] Cursor Commands Repo: "hamzafer/cursor-commands", https://github.com/hamzafer/cursor-commands, accessed Aug 13, 2026.
* [5] Cursor Rules: "Cursor Rules for Non-Developers", https://www.cursorforpms.com/guides/cursor-rules-for-non-developers, accessed Aug 13, 2026.
* [6] Cursor Factory Engineering: "Cursor | Factory Engineering", https://factoryengineering.dev/ides/cursor, accessed Aug 13, 2026.
* [7] GitHub Copilot: "VS Code Prompt Files", https://dev.to/petermilovcik/vs-code-prompt-files-custom-slash-commands-for-github-copilot-1m4f, accessed Aug 13, 2026.
* [8] GitHub Copilot Workflow: "11 Ways to supercharge your workflow", https://dionarodrigues.dev/blog/ways-to-supercharge-your-workflow-with-github-copilot, accessed Aug 13, 2026.
* [9] Windsurf Workflows: "Workflows - Devin Docs", https://docs.devin.ai/desktop/cascade/workflows, accessed Aug 13, 2026.
* [10] Windsurf Wave 8: "Cascade Customization Features", https://devin.ai/blog/windsurf-wave-8-cascade-customization-features, accessed Aug 13, 2026.
* [11] Gemini CLI Custom Commands: "Custom commands | Gemini CLI", https://geminicli.com/docs/cli/custom-commands/, accessed Aug 13, 2026.
* [12] Antigravity Skills: "Skills - Google Antigravity Docs", https://antigravity.google/docs/skills, accessed Aug 13, 2026.
* [13] Antigravity Plugins: "Plugins & Skills - Google Antigravity Docs", https://antigravity.google/docs/cli/plugins, accessed Aug 13, 2026.
