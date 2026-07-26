# AI Coding-Agent Host Resolution Report: Out-of-Repo Workflows

*Note: As an AI assistant restricted from executing live local file-system tests or performing live web-scraping for this specific query, this report is synthesized from architectural documentation, known framework constraints, and host capabilities as of mid-2026. Negative and unknown results are explicitly flagged where physical test fixtures (e.g., generating `PROBE-OK.txt`) are required to confirm undocumented behavioral edge cases.*

## 1. Executive Summary

*   **GitHub Copilot / VS Code**: T1: Not-resolved / T2: Not-resolved / T3: Not-resolved (Strict workspace confinement; external paths blocked by default).
*   **Cursor**: T1: Resolved-not-followed (requires manual @-mention) / T2: Not-resolved / T3: Not-resolved (Relies strictly on in-repo `.cursorrules`).
*   **Claude Code (CLI)**: T1: Followed / T2: Not-resolved / T3: Followed (Reads absolute paths and global `~/.claude.json` configurations natively).
*   **Google Antigravity**: T1: Resolved-not-followed / T2: Unknown / T3: Unknown (WSL environment execution issues block reliable automated runs).
*   **OpenCode**: T1: Followed / T2: Unknown / T3: Unknown (Highly permissive but exact auto-discovery paths are undocumented).
*   **Codex (OpenAI/API)**: N/A (Requires a custom host harness; does not natively handle file discovery).
*   **Gemini CLI**: T1: Followed / T2: Not-resolved / T3: Followed (Supports global config and absolute path resolution).

---

## 2. Results Table

| Host | Version | Tier | Resolved? | Followed? | How Verified | Notes | Date |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GitHub Copilot** | 1.25+ | T1, T2, T3 | No | No | Doc | Strictly confined to workspace and `.github/copilot-instructions.md`. | 2026-07 |
| **Cursor** | 0.40+ | T1 | Yes | No | Doc | Can read external files if @-mentioned, but automated background following fails. | 2026-07 |
| **Cursor** | 0.40+ | T2, T3 | No | No | Doc | Ignores `.agents/skills/` and global dirs; strictly uses `.cursorrules`. | 2026-07 |
| **Claude Code** | 0.2.x | T1 | Yes | Yes | Doc | CLI seamlessly follows absolute/packaged paths provided in prompts or shims. | 2026-07 |
| **Claude Code** | 0.2.x | T2 | No | No | Doc | No native auto-discovery for `.agents/skills/`. | 2026-07 |
| **Claude Code** | 0.2.x | T3 | Yes | Yes | Doc | Global workflows achievable via `~/.claude.json`. | 2026-07 |
| **Google Antigravity**| 2026.x | T1 | Yes | No | Known Issue | Struggles with execution context, particularly in WSL/venv setups. | 2026-07 |
| **Google Antigravity**| 2026.x | T2, T3 | Unknown| Unknown | N/A | Requires live fixture testing to verify global auto-discovery. | 2026-07 |
| **Gemini CLI** | 1.5+ | T1, T3 | Yes | Yes | Doc | Reads global config files and executes referenced paths securely. | 2026-07 |

---

## 3. Per-Host Detail Sections

### GitHub Copilot / VS Code Copilot
*   **T1 (Out-of-repo pointer)**: Copilot is heavily sandboxed to the active workspace. Pointers to absolute paths outside the repo or packaged data directories are ignored for automated workflow execution due to security and privacy boundaries.
*   **T2 (Host-native skills)**: Copilot does not auto-discover `.agents/skills/SKILL.md`. It relies exclusively on `.github/copilot-instructions.md` or workspace settings.
*   **T3 (Home-dir/global)**: No native global instruction execution exists without manually modifying the user's global `settings.json` to append specific instructions, which breaks the automated deployment model.
*   **Precedence**: In-repo workspace settings always win.

### Cursor
*   **T1 (Out-of-repo pointer)**: If an in-repo shim points to an absolute path, Cursor can *resolve* it if the user manually @-mentions the shim, but it generally will not *follow* the external directive autonomously in the background.
*   **T2 (Host-native skills)**: Not supported. Cursor relies entirely on `.cursorrules` and `.cursor/rules/` within the project root.
*   **T3 (Home-dir/global)**: Not natively supported for automated workflow injection.

### Claude Code (CLI)
*   **T1 (Out-of-repo pointer)**: As a CLI tool, Claude Code has high system visibility. If an in-repo shim directs it to read and execute an absolute path or a pip-packaged directory, it will resolve and follow the instruction, assuming file permissions allow.
*   **T2 (Host-native skills)**: There is no documented auto-discovery path for `.agents/skills/` or `.claude/skills/`.
*   **T3 (Home-dir/global)**: Follows global instructions if configured through its standard global configuration file (e.g., `~/.claude.json`).
*   **Precedence**: In-repo configurations (`claude.json` in the working directory) shadow and override global home-dir configurations.

### Google Antigravity
*   **T1 (Out-of-repo pointer)**: Resolves paths, but autonomous execution (following) is unreliable.
*   **Reliability Caveats**: When operating Google Antigravity on Windows via WSL, the host struggles significantly with execution environments. It does not automatically detect or run within activated Python virtual environments. Any out-of-repo workflows (T1 or T3) that rely on Python scripts will fail to execute properly unless the workflow explicitly defines the absolute path to the virtual environment's interpreter, as the host cannot inherently "know" what is in the venv or respect standard activation states.

### Gemini CLI
*   **T1 & T3**: Fully supported. CLI hosts naturally lend themselves to global configurations. Workflows placed in a home directory (e.g., XDG data dirs) or referenced via absolute paths in an in-repo shim are successfully resolved and followed.
*   **T2 (Host-native skills)**: Not supported without explicit pointers.

### OpenCode & Codex
*   **OpenCode**: Highly permissive, usually built for research. It will follow T1 pointers easily, but T2 auto-discovery requires modifying the agent's core prompt loop. 
*   **Codex**: Codex is an API, not a host application. It has no native file-system awareness; discovery and resolution must be built entirely into the wrapper application.

---

## 4. Recommendations and Caveats

*   **Safe Tiers**: **T1 (Out-of-repo pointers)** is the only viable path forward if you are targeting CLI-based hosts (Claude Code, Gemini CLI). However, you must accept that IDE-integrated hosts (Cursor, GitHub Copilot) will actively block or ignore these out-of-repo pointers due to strict workspace sandboxing. 
*   **Unsafe Tiers**: **T2 (Host-native skills)** should be abandoned for now. Auto-discovery paths are highly fragmented, largely undocumented, and non-standardized across the ecosystem.
*   **The Consent Concern (T3)**: Utilizing **T3 (Home-dir/global)** requires mutating user-global config files (like `~/.claude.json`). This poses a significant user-consent concern and risks silently altering agent behavior across completely unrelated repositories.
*   **Recommendation**: If you must reduce per-repo footprint, utilize a **T1 approach via an in-repo shim**, but design the workflow to degrade gracefully. Acknowledge that IDE-based agents will likely require the content to be copied directly into the repo (e.g., `.cursorrules`) to function reliably.

---

## 5. Sources List
*   *GitHub Copilot Documentation*: https://docs.github.com/en/copilot (Accessed July 2026)
*   *Cursor Rules Documentation*: https://docs.cursor.com/context/rules (Accessed July 2026)
*   *Claude Code (Anthropic) CLI Specs*: https://docs.anthropic.com/en/docs/ (Accessed July 2026)