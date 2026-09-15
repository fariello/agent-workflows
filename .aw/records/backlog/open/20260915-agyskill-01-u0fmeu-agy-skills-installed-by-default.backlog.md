- Id: u0fmeu
- Status: open
- Blocks-Release: next
- Set: agyskill
- Priority: high
- Work-Kind: feature
- Summary: Installer must install Antigravity (agy) skills and unified /aw router

## Workflow history
- 2026-09-15 created (aw backlog): Installer must install Antigravity skills and unified /aw router

### Problem
Antigravity discovers workspace slash commands and agent skills through `.agents/skills/<name>/SKILL.md`. Target repositories initialized or updated with agent-workflows can run individual workflow skills (such as `/assess-ransomware-resilience`), but `/aw` itself does not appear as an Antigravity command. Furthermore, these Antigravity (`agy`) skills are not deterministically installed and maintained by the agent-workflows installer.

In `agent_workflows/host_adapters.py`, `antigravity` is currently excluded from `V1_HOSTS` (`V1_HOSTS = ("opencode", "codex")`), and `HOST_FEATURE_ROLE_MAP["antigravity"]` does not map `"skill": ROLE_ROUTER`. Consequently, the installer does not generate a root `.agents/skills/aw/SKILL.md` skill to route `/aw` subcommands.

### Requirements
1. **Mandatory Installer Delivery**: The agent-workflows installer (`aw install`, `aw setup-repo`, `aw host install`) MUST install Antigravity (`agy`) skills by default whenever Antigravity is present or targeted as an agent host.
2. **Unified `/aw` Command Router**: The installer must generate `.agents/skills/aw/SKILL.md` defining the top-level `/aw` command router skill, exposing the full CLI and workflow surface to Antigravity users directly via the chat slash command menu.
3. **First-Class Host Support**: Update `agent_workflows/host_adapters.py` so `antigravity` is properly integrated into host capability mappings and feature roles, matching OpenCode and Codex feature parity.
4. **Verification**: Add test coverage ensuring `aw install` and host adapter generator routines emit `.agents/skills/aw/SKILL.md` and keep all installed skill definitions synchronized with repo workflows.
