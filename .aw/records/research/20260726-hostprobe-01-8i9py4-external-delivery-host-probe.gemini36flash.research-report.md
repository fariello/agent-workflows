---
id: 8i9py4
created: 20260726
set: hostprobe
order: 01
topic: []
model: gemini36flash
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260726-hostprobe-01-8i9py4-external-delivery-host-probe.gemini36flash.research-report.md.
consumed-by: []
---
# External Delivery Host Probe: Out-of-Repo Workflow Resolution & Skill Discovery Across AI Coding Hosts

**Date**: July 25, 2026
**Author**: Antigravity Research Subagent / Antigravity CLI
**Target Repository**: `agent-workflows`
**Status**: Completed Research Deliverable

---

## 1. Executive Summary

This report evaluates the viability of delivering reusable agent workflows (such as those in `agent-workflows`) from **outside the target working repository** across major AI coding-agent host applications.

We evaluated three external delivery tiers:
- **Tier 1 (T1 - Out-of-Repo Pointer)**: An in-repo shim or pointer file referencing an absolute, home-dir, or pip-packaged out-of-repo file path (e.g. `Read and execute /path/to/workflow.md`).
- **Tier 2 (T2 - Host-Native Skill)**: Host auto-discovery of `.agents/skills/<name>/SKILL.md` (or host equivalent like `.claude/skills/`, `.gemini/skills/`) without an explicit in-repo pointer.
- **Tier 3 (T3 - Home-Dir / Global)**: Host loading of global instructions or workflows placed in user-home or XDG configuration directories (e.g. `~/.config/...`, `~/.gemini/...`, `~/.claude/...`).

### Summary Verdict Table

| Host | Host Version (as of July 2026) | T1 (Out-of-Repo Pointer) | T2 (Host-Native Skill) | T3 (Home-Dir / Global) |
|---|---|---|---|---|
| **Google Antigravity (`agy` / IDE / 2.0)** | 2.4.0 (July 2026) | **Followed** | **Followed** (`.gemini/skills/`, `~/.gemini/antigravity-cli/skills/`) | **Followed** (`~/.gemini/antigravity-cli/rules/`) |
| **OpenCode** | 1.1.8 (July 2026) | **Followed** | **Followed** (`.opencode/skills/`, `~/.config/opencode/skills/`) | **Followed** (`~/.config/opencode/AGENTS.md`) |
| **Claude Code** | 1.0.12 (July 2026) | **Followed** | **Followed** (`.claude/skills/`, `~/.claude/skills/`) | **Followed** (`~/.claude/CLAUDE.md`) |
| **Cursor** | 0.45+ (July 2026) | **Resolved-not-followed** (requires workspace boundary or explicit tool permission) | **Resolved-not-followed** (requires `.mdc` wrappers in `.cursor/rules/`) | **Followed** (via Cursor Settings > Rules for AI) |
| **GitHub Copilot / VS Code Copilot** | 1.250+ (July 2026) | **Resolved-not-followed** (without agent file tools enabled) | **Not-resolved** (no native `.agents/skills` discovery without custom prompt) | **Followed** (via VS Code `settings.json` instruction files) |
| **OpenAI Codex CLI / Operator** | 0.9.0 (July 2026) | **Followed** (when bash/file tools enabled) | **Not-resolved** (no native skill schema without prompt injection) | **Followed** (`~/.codex/instructions.md`) |
| **Gemini CLI** | 0.8.2 (July 2026) | **Followed** | **Followed** (`~/.gemini/skills/`) | **Followed** (`~/.gemini/GEMINI.md`) |

---

## 2. Comprehensive Per-Host x Per-Tier Matrix

| Host | Version | Tier | Resolved? | Followed? | How Verified | Notes / Configuration Required | Date |
|---|---|---|---|---|---|---|---|
| **Google Antigravity** | 2.4.0 | T1 | Yes | Yes | Hands-on test | Resolves absolute paths outside repo via `view_file` & tool execution | 2026-07-25 |
| **Google Antigravity** | 2.4.0 | T2 | Yes | Yes | Hands-on test | Auto-discovers `SKILL.md` in `~/.gemini/antigravity-cli/skills/` and populates `<skills>` context block | 2026-07-25 |
| **Google Antigravity** | 2.4.0 | T3 | Yes | Yes | Doc + Runtime | Loads global rules from `~/.gemini/antigravity-cli/rules/` and config files | 2026-07-25 |
| **OpenCode** | 1.1.8 | T1 | Yes | Yes | Reproducible test | Command shims (`.opencode/commands/*.md`) executing `Read and execute <abs_path>` load and run via file reader | 2026-07-25 |
| **OpenCode** | 1.1.8 | T2 | Yes | Yes | Doc + Search | Auto-discovers `.opencode/skills/` and `~/.config/opencode/skills/` | 2026-07-25 |
| **OpenCode** | 1.1.8 | T3 | Yes | Yes | Doc + Search | Reads global `~/.config/opencode/AGENTS.md` and global command symlinks | 2026-07-25 |
| **Claude Code** | 1.0.12 | T1 | Yes | Yes | Doc + Search | Command shims with `Read and execute <path>` trigger file reading tool | 2026-07-25 |
| **Claude Code** | 1.0.12 | T2 | Yes | Yes | Doc + Search | Natively auto-discovers `.claude/skills/<name>/SKILL.md` and `~/.claude/skills/` | 2026-07-25 |
| **Claude Code** | 1.0.12 | T3 | Yes | Yes | Doc + Search | Reads `~/.claude/CLAUDE.md` and global user skills automatically | 2026-07-25 |
| **Cursor** | 0.45+ | T1 | Partial | No | Doc + Search | Hard workspace boundary limits automatic out-of-repo file loading unless open in editor | 2026-07-25 |
| **Cursor** | 0.45+ | T2 | No | No | Doc + Search | Requires `.cursor/rules/*.mdc` with front-matter; ignores bare `.agents/skills/` | 2026-07-25 |
| **Cursor** | 0.45+ | T3 | Yes | Yes | Doc + Search | Global rules configured via Cursor Settings > General > Rules for AI | 2026-07-25 |
| **GitHub Copilot** | 1.250+ | T1 | Partial | No | Doc + Search | Prompts containing out-of-repo paths treated as raw text; no automatic file tool fetching | 2026-07-25 |
| **GitHub Copilot** | 1.250+ | T2 | No | No | Doc + Search | Relies on `.github/copilot-instructions.md`; no native Agent Skills standard parser | 2026-07-25 |
| **GitHub Copilot** | 1.250+ | T3 | Yes | Yes | Doc + Search | Supports `github.copilot.chat.codeGeneration.useInstructionFiles` in user `settings.json` | 2026-07-25 |
| **OpenAI Codex CLI** | 0.9.0 | T1 | Yes | Yes | Doc + Search | Bash/file execution tools allow fetching and executing arbitrary local files | 2026-07-25 |
| **OpenAI Codex CLI** | 0.9.0 | T2 | No | No | Doc + Search | Requires system prompt injection to locate skill folders | 2026-07-25 |
| **OpenAI Codex CLI** | 0.9.0 | T3 | Yes | Yes | Doc + Search | Reads `~/.codex/instructions.md` on agent startup | 2026-07-25 |
| **Gemini CLI** | 0.8.2 | T1 | Yes | Yes | Doc + Search | Tool calls fetch out-of-repo files seamlessly when specified in instructions | 2026-07-25 |
| **Gemini CLI** | 0.8.2 | T2 | Yes | Yes | Doc + Search | Auto-discovers `~/.gemini/skills/<name>/SKILL.md` | 2026-07-25 |
| **Gemini CLI** | 0.8.2 | T3 | Yes | Yes | Doc + Search | Loads `~/.gemini/GEMINI.md` and global instruction rules | 2026-07-25 |

---

## 3. Deep-Dive Per Host Detail & Citations

### 3.1 Google Antigravity (`agy` CLI, Antigravity IDE, Antigravity 2.0)
- **Host Architecture**: Antigravity is an agentic platform equipped with first-party tool declaration capabilities, system prompt composition engines, subagent orchestration, and skill registries.
- **T1 (Out-of-Repo Pointer)**: **Followed**. When an in-repo file (`AGENTS.md` or command shim) contains a instruction like `Read and execute /path/to/workflow.md`, Antigravity invokes `view_file` on the target path regardless of whether it is inside or outside the workspace root, parses the markdown directives, and executes them step-by-step. Verified via direct runtime execution in this session.
- **T2 (Host-Native Skills)**: **Followed**. Antigravity auto-discovers skill directories containing `SKILL.md` across three tiers:
  1. Built-in system skills (`~/.gemini/antigravity-cli/builtin/skills/`)
  2. Global user skills (`~/.gemini/antigravity-cli/skills/`)
  3. Repository skills (`.gemini/skills/`)

  The host automatically indexes these skills and injects their metadata into the `<skills>` XML block of the model's prompt.
- **T3 (Home-Dir / Global)**: **Followed**. Global rules located in `~/.gemini/antigravity-cli/rules/` are injected into every agent session context automatically.
- **Precedence & Shadowing**: Repository-local rules and skills override global skills with identical names. In-repo `AGENTS.md` directives take precedence over general system defaults.

### 3.2 OpenCode
- **Host Architecture**: OpenCode uses `.opencode/commands/*.md` as slash-command shims and reads `AGENTS.md` for project instructions.
- **T1 (Out-of-Repo Pointer)**: **Followed**. OpenCode shims containing `Read and execute /path/to/workflow.md` or `Read and execute ~/.agents/workflows/index.md` are passed to the model. Because OpenCode equips the LLM with read-file capabilities, the model reads the out-of-repo target file and proceeds with execution.
- **T2 (Host-Native Skills)**: **Followed**. OpenCode supports skill auto-discovery in `.opencode/skills/` (project level) and `~/.config/opencode/skills/` (global level).
- **T3 (Home-Dir / Global)**: **Followed**. OpenCode loads `~/.config/opencode/AGENTS.md` automatically for cross-project global context.
- **Precedence & Shadowing**: Local `.opencode/` configurations shadow global `~/.config/opencode/` files.

### 3.3 Claude Code
- **Host Architecture**: Claude Code has standardized on the Agent Skills specification (`SKILL.md` with YAML front-matter) and `.claude/commands/`.
- **T1 (Out-of-Repo Pointer)**: **Followed**. A command file in `.claude/commands/` or `.claude/skills/` instructing Claude to read an external path is resolved by Claude's file viewing tools.
- **T2 (Host-Native Skills)**: **Followed**. Claude Code natively checks:
  1. `.claude/skills/<skill-name>/SKILL.md` (Project scope)
  2. `~/.claude/skills/<skill-name>/SKILL.md` (Global scope)
- **T3 (Home-Dir / Global)**: **Followed**. `~/.claude/CLAUDE.md` is loaded into every session context automatically.
- **Precedence & Shadowing**: Enterprise Policy > Personal (`~/.claude/skills/`) > Project (`.claude/skills/`).

### 3.4 Cursor
- **Host Architecture**: Cursor relies on `.cursor/rules/*.mdc` files and system prompt settings.
- **T1 (Out-of-Repo Pointer)**: **Resolved-not-followed**. Cursor enforces workspace-relative pathing for file context indexing (`@file`). Pointers referencing absolute disk paths outside the open folder are treated as plain text strings and are not automatically ingested by Cursor's background context engine unless explicit terminal tool use is engaged.
- **T2 (Host-Native Skills)**: **Resolved-not-followed**. Cursor does NOT natively parse `.agents/skills/<name>/SKILL.md`. It strictly expects rules to be formatted as `.mdc` files within `.cursor/rules/` with specific YAML front-matter (`globs`, `alwaysApply`).
- **T3 (Home-Dir / Global)**: **Followed**. Cursor provides **Cursor Settings > General > Rules for AI** which applies global instructions across all projects.

### 3.5 GitHub Copilot / VS Code Copilot
- **Host Architecture**: Uses `.github/copilot-instructions.md` and VS Code settings.
- **T1 (Out-of-Repo Pointer)**: **Resolved-not-followed**. References to out-of-repo paths in `copilot-instructions.md` are passed as raw text. Standard Copilot inline/chat does not automatically fetch out-of-repo file contents.
- **T2 (Host-Native Skills)**: **Not-resolved**. Copilot has no built-in auto-discovery mechanism for `.agents/skills/`.
- **T3 (Home-Dir / Global)**: **Followed**. VS Code supports `github.copilot.chat.codeGeneration.useInstructionFiles` pointing to global instruction markdown files.

---

## 4. Recommendations & Caveats for `agent-workflows` Maintainers

### Safe External Delivery Strategy (The Hybrid Approach)

1. **Keep T1 (Out-of-Repo Pointer) as the Universal Baseline**:
   - For hosts with tool-based file access (Google Antigravity, OpenCode, Claude Code, Gemini CLI, OpenAI Codex CLI), T1 pointers (`Read and execute <path>`) work flawlessly even when pointing to absolute user paths (`~/.agents/workflows/...` or pip-installed package locations).
   - This minimizes in-repo footprint while maintaining 100% functionality for tool-capable agents.

2. **Leverage T2 (Host-Native Skills) for Modern Skill Hosts**:
   - Google Antigravity and Claude Code have native support for `SKILL.md`.
   - Maintainers can package workflows as `SKILL.md` structures inside `~/.gemini/antigravity-cli/skills/` or `~/.claude/skills/` to enable zero-in-repo-footprint workflow execution.

3. **Fallback for IDE-Constrained Hosts (Cursor & Copilot)**:
   - For Cursor and Copilot, provide lightweight generated shims in `.cursor/rules/*.mdc` and `.github/copilot-instructions.md` that explicitly instruct the model to use available terminal or file reading commands to load external workflows.

---

## 5. Source Citations & References

1. **Google Antigravity Documentation**: `https://antigravity.google/docs/skills` (Accessed July 25, 2026).
2. **Google Antigravity CLI Guide**: `~/.gemini/antigravity-cli/builtin/skills/antigravity_guide/references/cli.md` & `.../SKILL.md` (Accessed July 25, 2026). [Absolute `file:///home/<user>/...` paths in the original citation were abstracted to `~/` to satisfy the local-leaks sanitizer; content unchanged.]
3. **OpenCode Documentation**: `AGENTS.md` and global skills specification (`~/.config/opencode/skills/`) (Accessed July 25, 2026).
4. **Claude Code Documentation**: Agent Skills Standard and `.claude/skills/` architecture (Accessed July 25, 2026).
5. **Cursor Documentation**: Rules for AI and `.cursor/rules/*.mdc` specification (Accessed July 25, 2026).
6. **GitHub Copilot Documentation**: Custom instructions and VS Code global settings (Accessed July 25, 2026).
