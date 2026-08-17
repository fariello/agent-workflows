---
id: x9whzs
created: 20260802
set: skills
order: 01
topic: []
model: gemini31pro
kind: research-report
status: reference
outcome: informational
summary: Migrated from 20260726-skills-01-x9whzs-suggested-future-skill-usage.gemini31pro.research-report.md.
consumed-by: []
---
# Suggested Future Skill Usage Architecture for fariello/agent-workflows

This document outlines the strategic reconfiguration of the `agent-workflows` repository to transition from `/command` style shims to a host-native skills architecture. 

## 1. The Core Strategy: Moving to T2 Native Skills

The primary cross-host delivery mechanism should be transitioned to T2 (host-native skills). This relies on placing skill definitions where the host application automatically discovers them.

*   **Universal Path:** Use `.agents/skills/<name>/SKILL.md` as the primary standard, which is supported by OpenCode, Codex, Copilot, Cursor, Antigravity, and Gemini CLI.
*   **Claude Adapter:** You must add a specific `.claude/skills/<name>/SKILL.md` adapter, as Claude Code does not natively use the `.agents/skills/` root.

## 2. What Should Move to Skills

Mechanical conversion of every single workflow into a separate skill is not recommended. Instead, segment the capabilities:

### Portable Capability Skills
Workflows that represent high-frequency, bounded capabilities should be moved to dedicated skills.
*   These include workflows for `plan-review`, `release-review`, `verify`, `scaffold`, and `spec`.
*   Moving these bounded tasks to user-scope host skills provides a clean-delta approach, eliminating footprint in the target repository.

### Explicit Harness Skills
Persona and assessor workflows (e.g., `advise`, `assess`) should not be converted into a 1:1 list of separate skills. Doing so risks registry explosion and auto-trigger false positives. 
*   Instead, they should be implemented as explicit harness skills, such as `advise <persona>` or `assess <lens>`. 
*   The skill resolves and loads the selected packaged persona or lens dynamically.
*   For hosts that support it, automatic invocation should be disabled so these act like explicit slash commands.

## 3. What Should Stay As-Is (Cross-Agent Compatibility)

While native skills are the future, several architectural components and fallbacks must remain in place to guarantee compatibility across diverse execution environments, including complex virtual environments across Windows, Linux, and WSL.

### Retain Fallback Shims
Do not replace the existing repository shim with one universal absolute `@path` pointer. 
*   Passive out-of-repository pointers (T1) are inconsistently resolved; for example, Copilot CLI explicitly blocks absolute imports.
*   Locally excluded project shims or skills should be kept as a host-tested fallback when a host lacks a usable user-scope mechanism. 

### Universal Instructions and Root Files
*   The target repository’s root `AGENTS.md` and tracked `.gitignore` must remain untouched in clean-delta mode.
*   Only concise, genuinely universal instructions should go into user rules or global instruction files. Do not place the whole workflow catalog there.

### Artifact Routing
*   Developer-created artifacts (plans, prompts, research, runs) need a tracking home outside the upstream repository.
*   A sibling repository remains the clearest artifact-tracking location and should be retained as the normal clean-delta artifact home.

## 4. State and Installation Management
*   The authoritative per-repository mapping and routing state must be kept in a user-global agent-workflows configuration. 
*   A separate global ownership manifest is required to manage shared user-scope host files, ensuring explicit consent and clean uninstalls.
*   A recovery snapshot should be maintained in the companion artifact repository.
