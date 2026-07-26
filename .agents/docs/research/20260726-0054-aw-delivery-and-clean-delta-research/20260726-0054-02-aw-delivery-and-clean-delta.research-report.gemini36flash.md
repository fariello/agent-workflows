# Architectural Research Report: Agent-Workflows Delivery, Host Discovery, and Clean-Delta Contributions

**Date**: July 26, 2026  
**Author**: Principal Software Architect & Release Engineer (Antigravity IDE with Gemini 3.6 / Antigravity CLI)  
**Target Project**: `agent-workflows`  
**File Identifier**: `20260726-0002-01-aw-delivery-and-clean-delta-report.gemini36.md`  

---

## Executive Summary & Architectural Position

The `agent-workflows` project currently delivers reusable AI coding-agent workflows by mutating the target repository: placing workflow files under `.agents/workflows/`, adding command shims in `.opencode/commands/` and `.claude/commands/`, injecting managed blocks into `AGENTS.md` / `.gitignore`, and recording ownership in `.agents/agent-workflows/managed-sections.json`.

While this in-repo model works reliably when the developer owns the repository, it creates severe friction when contributing clean pull requests (PRs) to upstream repositories (such as `opencode` or `hermes`), which carry their own `AGENTS.md` and where **zero framework footprint** must be committed upstream.

This report evaluates how `agent-workflows` can enable **Clean-Delta PR Contributions** (zero committed footprint in upstream repos while retaining tracked IPDs/artifacts in a developer-controlled location) and **Low-Footprint / Do-Not-Advertise Installs** across multi-host AI agent environments—specifically Google Antigravity, OpenCode, Claude Code, Cursor, GitHub Copilot, OpenAI Codex CLI, and Gemini CLI.

### Key Architectural Recommendations

1. **Adopt Sibling Mini-Repo (Mechanism B) + Local Git Excludes (`.git/info/exclude`) as the Primary Clean-Delta Architecture**:
   - Rather than trying to hack out-of-repo file discovery into hosts that strictly enforce workspace boundaries (like Cursor or Copilot), place developer artifacts and local framework pointers inside a sibling repo `../<repo>.aw/` or locally exclude them via `.git/info/exclude`.
2. **Standardize on Host-Native Skills (`SKILL.md`) for Skill-Supporting Hosts (Mechanism F)**:
   - Deliver single-command capabilities (`release-review`, `plan-review`, `verify`, `spec`, `scaffold`) via host-native global/user skill directories (`~/.gemini/antigravity-cli/skills/`, `~/.claude/skills/`, `~/.config/opencode/skills/`). This achieves **true zero in-repo footprint** for Google Antigravity, OpenCode, Claude Code, and Gemini CLI without modifying the target repository.
3. **Keep Persona & Assessor Harnesses (`advise`, `assess`) as Orchestrated Workflows, Not Skills**:
   - Dialogue/persona harnesses (`advise-*`) and deep multi-lens auditors (`assess-*`) require multi-step state management and parameters (`lens`, `artifact`). They should remain multi-file workflows invoked via universal prompt pointers (`Read and execute <path>`) rather than converted into flat skills.
4. **Decouple Framework Metadata from Tracked Git Repositories**:
   - Store local/clean-delta installation state in a per-repo section of the user-global config `~/.config/agent-workflows/config.json` or in a local-only manifest (`.git/info/exclude`'d `.agents/agent-workflows/managed-sections.json`), ensuring `git status` stays pristine.

---

## 1. Goal Restatement, Reframing & Premise Challenge

### Stated Goals & Evaluation

| Goal | Stated Intent | Assessment & Architectural Reframing | Verdict |
|---|---|---|---|
| **Goal 1: Clean-Delta Contribution** | Developer uses aw fully in an unowned upstream repo (`opencode`, `hermes`) without committing aw files, while keeping personal IPDs/artifacts tracked in a developer-controlled location. | **Core architectural driver.** Must be fully supported. Upstream git tree must remain 100% clean of framework files, manifests, and `AGENTS.md` modifications. | **KEEP (Primary Driver)** |
| **Goal 2: Low-Footprint / Do-Not-Advertise** | Use aw locally without advertising its presence in the repo tree, independent of the PR case. | Valid preference. Completely solved by the same local-exclusion and global-skills mechanisms that solve Goal 1. | **KEEP (Sub-case of Goal 1)** |
| **Goal 3: Per-Class Tracking Opt-Out** | Selectively keep specific artifact classes (plans/IPDs, prompts, research) local/untracked while using workflows. | Currently handled via `local/` subdirectories and `*.untracked.*` rules. **Reframing**: Rather than creating complex per-class gitignore filters, route personal developer artifacts to a developer-owned sibling repository (`../<repo>.aw/`). | **REFRAME & SIMPLIFY** |
| **Goal 4: Untrackable Framework + Manifest** | Keep aw framework files and manifest untracked in git. | High value. Storing the manifest in git is a liability for PR contributors. The manifest location must be decoupled from tracked repo files. | **KEEP** |

### Critical Premise Challenge
> **Skeptical View**: *Can we rely on hosts resolving out-of-repo path references in an uncommitted instruction file?*  
> **Answer**: **No, not universally.** File discovery mechanics are controlled by host applications, not LLMs. Tools like Google Antigravity, OpenCode, Claude Code, and Gemini CLI handle out-of-repo path execution seamlessly via file tools. However, IDE-bound agents like Cursor and VS Code Copilot restrict automated context indexing to the active workspace folder. Therefore, any design that relies *solely* on a global out-of-repo pointer will fail or require manual prompt intervention on IDE-bound hosts. The architecture must compose **global skills (T2/T3)** with **locally-excluded workspace shims (`.git/info/exclude`)** to work across all hosts.

---

## 2. Hard Problem Analysis: Host Discovery & Local Excludes

In a clean-delta scenario, `agent-workflows` must NOT commit shims to `.opencode/commands/` or `.claude/commands/`, and must NOT touch the tracked `AGENTS.md` or `.gitignore`.

### 2.1 Host Discovery Matrix (Without In-Repo Commits)

| Host | Local Exclude (`.git/info/exclude`) Discovery | Global User Instructions (`~/.config/...` / `CLAUDE.md` / `rules/`) | Out-of-Repo File Resolution | Co-existence with Upstream `AGENTS.md` |
|---|---|---|---|---|
| **Google Antigravity (`agy` / IDE / 2.0)** | **Proven**: Reads locally-excluded `AGENTS.md` or `.gemini/` files. | **Proven**: Auto-loads `~/.gemini/antigravity-cli/rules/` and `~/.gemini/antigravity-cli/skills/`. | **Proven**: Tool calls (`view_file`) resolve absolute disk paths outside workspace. | Local `.gemini/` or `AGENTS.md` pointers seamlessly complement upstream `AGENTS.md`. |
| **OpenCode** | **Proven**: Reads locally-excluded `.opencode/commands/*.md`. | **Proven**: Reads `~/.config/opencode/AGENTS.md` and `~/.config/opencode/skills/`. | **Proven**: Reads external path targets when instructed in command shim. | Local command shims override or supplement root `AGENTS.md`. |
| **Claude Code** | **Proven**: Reads locally-excluded `.claude/skills/` or `.claude/commands/`. | **Proven**: Auto-loads `~/.claude/CLAUDE.md` and `~/.claude/skills/`. | **Proven**: Reads external paths referenced in commands/skills. | Local skills append to `CLAUDE.md` context without modifying root files. |
| **Cursor** | **Proven**: Reads locally-excluded `.cursor/rules/*.mdc`. | **Proven**: Cursor Settings > General > Rules for AI (GUI configuration). | **Unproven / Restricted**: Enforces strict workspace root boundaries for indexing. | `.cursor/rules/*.mdc` locally excluded will not clash with upstream `AGENTS.md`. |
| **GitHub Copilot** | **Unproven**: Requires `.github/copilot-instructions.md`. | **Proven**: VS Code `settings.json` (`github.copilot.chat.codeGeneration.useInstructionFiles`). | **Not-resolved**: Text references to out-of-repo paths are not auto-fetched. | Global settings append instructions to workspace `copilot-instructions.md`. |
| **OpenAI Codex CLI** | **Proven**: Reads local workspace files. | **Proven**: `~/.codex/instructions.md`. | **Proven**: Bash execution tool allows reading external disk locations. | System prompt combines global instructions with local instructions. |
| **Gemini CLI** | **Proven**: Reads local instructions. | **Proven**: `~/.gemini/GEMINI.md` and `~/.gemini/skills/`. | **Proven**: Tool calls resolve absolute disk paths outside workspace. | Global `GEMINI.md` appends context to workspace rules. |

### 2.2 Ignore Homes: `.git/info/exclude` vs `core.excludesFile`

When hiding `agent-workflows` files in a target repository without modifying `.gitignore`:

1. **`.git/info/exclude` (Local per-clone ignore)**:
   - **Pros**: Local to the repository clone; never committed to git; visible only to the developer on that machine.
   - **Cons**: Per-clone (must be configured per git clone); not shared with collaborators.
   - **Host Behavior**: Git-aware hosts (Antigravity, OpenCode, Claude Code, Cursor) still read files on disk even if listed in `.git/info/exclude`. Git ignores them for commits, but agent file tools can view and execute them.
2. **`core.excludesFile` (User-global git ignore)**:
   - **Pros**: System-wide across all repositories owned by the user.
   - **Cons**: Too coarse; adding `.agents/` globally might accidentally ignore repo-native `.agents/` directories in other projects.

> **Rule**: `.git/info/exclude` is the correct, safest local ignore mechanism for clean-delta installations.

---

## 3. Deep-Dive: Host-Native Skills (`SKILL.md`)

Host-native skills represent the cleanest mechanism for delivering single-command capabilities without modifying repository files.

### 3.1 Host-Native Skill Discovery Paths

```
Global / User Skills (Zero In-Repo Footprint):
├── ~/.gemini/antigravity-cli/skills/<skill-name>/SKILL.md   (Google Antigravity)
├── ~/.claude/skills/<skill-name>/SKILL.md                    (Claude Code)
├── ~/.config/opencode/skills/<skill-name>/SKILL.md           (OpenCode)
└── ~/.gemini/skills/<skill-name>/SKILL.md                    (Gemini CLI)

Repository-Local Skills (Locally Excludable via .git/info/exclude):
├── .gemini/skills/<skill-name>/SKILL.md                      (Google Antigravity)
├── .claude/skills/<skill-name>/SKILL.md                      (Claude Code)
└── .opencode/skills/<skill-name>/SKILL.md                    (OpenCode)
```

### 3.2 Workflow Categorization: Skills vs Orchestrated Workflows

We should **NOT** mechanically convert every workflow into a `SKILL.md`. Workflows must be split into two distinct execution tiers:

```
                  ┌─────────────────────────────────────────┐
                  │       agent-workflows Framework         │
                  └────────────────────┬────────────────────┘
                                       │
           ┌───────────────────────────┴───────────────────────────┐
           ▼                                                       ▼
┌───────────────────────────────┐                       ┌───────────────────────────────┐
│   Tier A: Skill-Eligible      │                       │ Tier B: Orchestrated          │
│   Single-Command Capabilities │                       │ Persona & Assessor Harnesses  │
├───────────────────────────────┤                       ├───────────────────────────────┤
│ • release-review              │                       │ • advise                      │
│ • plan-review / -long         │                       │   (skeptic, architect, etc.)  │
│ • verify / verify-execution   │                       │ • assess / assess-all         │
│ • spec                        │                       │   (security, privacy, etc.)   │
│ • scaffold / setup-repo       │                       │ • incident / migrate          │
│ • getting-started / whatnext  │                       │ • benchmark                   │
└──────────────┬────────────────┘                       └──────────────┬────────────────┘
               │                                                       │
               ▼                                                       ▼
  Delivered as Global SKILL.md                             Invoked via Harness Body
  (Zero in-repo footprint)                              + Lens/Persona Specification
```

1. **Tier A: Skill-Eligible (Single-Command Capabilities)**:
   - Examples: `release-review`, `plan-review`, `verify`, `verify-execution`, `spec`, `scaffold`, `setup-repo`, `getting-started`, `whatnext`, `handoff`.
   - **Fit**: High. These have clear entry points, discrete steps, and predictable arguments (`$ARGUMENTS`).
   - **Delivery**: Package as `SKILL.md` files in global skill directories (`~/.gemini/antigravity-cli/skills/`, `~/.claude/skills/`, `~/.config/opencode/skills/`).
2. **Tier B: Orchestrated Harnesses (Persona & Assessor Frameworks)**:
   - Examples: `advise` (with 7+ personas like `skeptic`, `architect`, `red-teamer`) and `assess` (with 25+ concern lenses like `security`, `privacy`, `performance`).
   - **Fit**: Low for individual skill files. Creating 30+ separate skill directories would pollute the skill registry and create maintenance drift.
   - **Delivery**: Retain `advise.md` and `assess.md` as core harness workflows. The global `advise` or `assess` skill loads the shared harness body and dynamically injects the requested persona/lens file from the framework directory.

---

## 4. Evaluation of Candidate Architectures (Cost / Benefit / Risk Matrix)

| Mechanism | Description | Fit for Clean-Delta (PR) | Footprint on Target Repo | Host Dependency & Proof Required | Reversibility & Uninstall | Risk Level |
|---|---|---|---|---|---|---|
| **A) In-Repo + Local Git Exclude** | Install aw into `.agents/` & shims into `.opencode/`, `.claude/`, but exclude all aw paths in `.git/info/exclude`. | **High**: Git status stays clean; repo tree has files on disk. | **Low (disk only)**: 0 committed files. | **Proven** on Antigravity, OpenCode, Claude Code, Cursor. | **High**: Simple `rm` + clean `.git/info/exclude`. | Low |
| **B) Sibling Mini-Repo (`../<repo>.aw/`)** | Place developer artifacts (IPDs, docs) & aw framework in a sibling directory `../<repo>.aw/` tracked in developer's own git. | **Highest**: 100% clean upstream repo on disk and in git. | **Zero**: No files added to target repo tree. | **Proven** for tool-calling agents; requires absolute path pointer for IDE agents. | **Highest**: Delete or un-link `../<repo>.aw/`. | Low |
| **C) Home-Dir / Global Framework** | Framework installed in `~/.config/agent-workflows/`; referenced globally or via local pointer. | **High**: Shared single framework installation across repos. | **Zero to Low**: Requires local pointer unless host supports global skills. | **Proven** for global skill hosts; unproven for strict IDE sandboxes. | **High**: Remove global config entry. | Low |
| **D) Per-Class Nested `.gitignore`** | Use `local/` subdirectories and nested `.gitignore` rules in `.agents/plans/`, `.agents/prompts/`. | **Medium**: Protects local files from git tracking, but `.gitignore` changes pollute PRs. | **High**: Modifies tracked repo `.gitignore` & adds dirs. | **Proven**: Standard git behavior. | **Medium**: Requires git revert of `.gitignore`. | Medium |
| **E) Status Quo** | Document manual `.git/info/exclude` and `local/` usage. | **Poor**: High developer friction and manual configuration error rate. | **Variable**: Highly error-prone. | **Proven**. | **Manual**. | High (human error) |
| **F) Host-Native Skills (`SKILL.md`)** | Deliver skill-eligible workflows as `SKILL.md` in user global skills directories (`~/.claude/skills/`, `~/.gemini/...`). | **Highest**: 0 committed files, 0 repo files on disk. Native host discovery. | **Zero**: No repo files. | **Proven** on Antigravity, Claude Code, OpenCode, Gemini CLI. | **Highest**: Remove from user skills directory. | Low |

### Recommended Architecture: The Composite Clean-Delta Model (B + F + Local Exclude)

We recommend combining **Mechanism F (Global Skills)** for command invocation, **Mechanism B (Sibling Mini-Repo)** for developer artifact tracking, and **Mechanism A (`.git/info/exclude`)** as a local fallback shim layer:

```
Developer Workspace Layout:
├── target-repo/                              (Upstream Git Repo - 100% CLEAN)
│   ├── .git/
│   │   └── info/exclude                      (Locally excludes .agents/ pointer if present)
│   ├── src/
│   └── AGENTS.md                             (Untouched upstream AGENTS.md)
│
├── target-repo.aw/                           (Developer's Private Artifact Repo)
│   ├── .git/                                 (Developer's own git repository)
│   ├── plans/                                (Tracked IPDs: pending/, executed/)
│   ├── docs/                                 (Research reports & walkthroughs)
│   └── prompts/                              (Session prompts & handoffs)
│
└── ~/.config/agent-workflows/                (User-Global Installation & Framework)
    ├── config.json                           (Global config with per-repo registry)
    └── skills/                               (Global SKILL.md wrappers for Antigravity/Claude/OpenCode)
        ├── release-review/SKILL.md
        ├── plan-review/SKILL.md
        ├── assess/SKILL.md
        └── advise/SKILL.md
```

---

## 5. Lifecycle, Migration, and Version Compatibility Analysis

### 5.1 Migration Paths

1. **Tracked-Mode $\rightarrow$ Clean-Delta Mode**:
   - Running `aw install --clean-delta` on a repo previously installed in tracked mode:
     1. Reads `.agents/agent-workflows/managed-sections.json`.
     2. Removes tracked command shims (`.opencode/commands/`, `.claude/commands/`) and managed blocks in `AGENTS.md` / `.gitignore`.
     3. Appends `.agents/` entries to `.git/info/exclude`.
     4. Initializes `../<repo>.aw/` if requested, moving existing pending/executed IPDs into the sibling repo.
     5. Updates the manifest location to local-only status or registers the repo in `~/.config/agent-workflows/config.json`.
2. **Clean-Delta Mode $\rightarrow$ Tracked-Mode**:
   - Running `aw install --tracked` reinstalls in-repo shims, restores managed blocks in `AGENTS.md`, and removes entries from `.git/info/exclude`.

### 5.2 Re-Installing the Exact Same Version
When running `aw install` for a version already recorded as installed in the manifest:
- **Engine Behavior**: Reconcile silently by default. Inspect on-disk files against manifest sha256 hashes.
- **Output**: Report missing or corrupted files restored; report user-modified files preserved. If zero drift is detected, report: `agent-workflows v1.2.1 already up to date; zero changes needed.`

### 5.3 Preserving Revert Options Cleanly
To preserve the ability to revert to an older `agent-workflows` release without over-engineering a full rollback engine today:
- **Minimal Manifest Data**: Each file entry in `managed-sections.json` must record:
  - `installed_version` (e.g. `1.2.1`)
  - `sha256` (hash of content last written by installer)
  - `installed_at` (ISO timestamp)
- **Installer Backups**: Retain the existing git-independent backup engine (`.agent-workflows-installer-backups/<timestamp>/`). Because workflow files and shims are tiny (< 100 KB total), timestamped file backups provide 100% full-state restore capability with zero risk of git corruption.

---

## 6. End-to-End Walkthrough & Design Recommendations

### 6.1 End-to-End Walkthrough: Clean-Delta PR Lifecycle

```
[Step 1: Setup Clean-Delta Repo]
  $ cd ~/projects/opencode
  $ aw install --clean-delta --sibling
  -> Upstream repo git status: PRISTINE (0 changed files)
  -> Created sibling artifact repo: ~/projects/opencode.aw/
  -> Appended local exclusions to .git/info/exclude
  -> Installed global skills to ~/.config/opencode/skills/ & ~/.gemini/...

[Step 2: Developer Invokes Workflow in Antigravity / OpenCode]
  Developer types: "assess security" or "/plan-review"
  -> Host reads global SKILL.md from user skills directory
  -> Agent executes workflow instructions
  -> Generated IPD written to ~/projects/opencode.aw/plans/pending/20260726-0010-01-security-fix.md

[Step 3: Implementation & Validation]
  Developer writes code in ~/projects/opencode/src/
  Developer verifies fixes via test suite
  Agent moves IPD to ~/projects/opencode.aw/plans/executed/
  Developer commits IPD in sibling repo:
    $ cd ~/projects/opencode.aw && git add . && git commit -m "docs: IPD for security fix"

[Step 4: Submitting Upstream Pull Request]
  $ cd ~/projects/opencode
  $ git status
  -> Shows ONLY genuine code changes in src/
  -> Zero agent-workflows files, zero modified .gitignore, zero modified AGENTS.md
  $ git push origin feature/security-fix
  -> Upstream PR opened with 100% CLEAN DELTA!

[Step 5: Clean Uninstall (Optional)]
  $ aw uninstall --clean-delta
  -> Removes local exclude lines from .git/info/exclude
  -> Leaves ~/projects/opencode.aw/ untouched so developer keeps all IPD history!
```

### 6.2 Answers to Open Design Questions

1. **Where should per-repo choices be recorded?**
   - In `~/.config/agent-workflows/config.json` under a `repos` object keyed by canonical absolute path:
     ```json
     {
       "repos": {
         "/home/user/projects/opencode": {
           "mode": "clean-delta",
           "sibling_dir": "/home/user/projects/opencode.aw",
           "installed_version": "1.2.1"
         }
       }
     }
     ```
   - *Why*: Keeps configuration 100% out of the target repo's git tree.
2. **Materialized in Repo vs Kept Purely Local?**
   - Kept **purely local** for `--clean-delta` installs; committed as `.agents/agent-workflows/managed-sections.json` ONLY for standard `--tracked` installs.
3. **Interactive vs Flag-Driven Selection?**
   - Support both!
   - CLI flags: `aw install --clean-delta`, `aw install --tracked`, `aw install --sibling`.
   - Interactive prompt during `aw install` or `/setup-repo`:
     ```
     Select installation mode:
       [1] Standard Tracked (Commits .agents/ and shims to repo - best for owned repos)
       [2] Clean-Delta (0 repo files committed, local .git/info/exclude - best for PR contributions)
       [3] Global Skills Only (0 repo files on disk, uses ~/.gemini or ~/.claude skills)
     ```

---

## 7. Phased Implementation Plan

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHASED IMPLEMENTATION                           │
└────────────────────────────────────────────────────────────────────────┘

  Phase 1: Local Exclude & Sibling Artifact Foundation (Immediate)
  ├── 1. Add `--clean-delta` flag to `aw install` / `engine.py`.
  ├── 2. Implement `.git/info/exclude` writer & clean remover.
  ├── 3. Support sibling artifact directory routing (`../<repo>.aw/`).
  └── 4. Update manifest location logic to support local-only config entries.

  Phase 2: Global Host-Native Skills Packaging (Short-Term)
  ├── 1. Author `SKILL.md` generators in `engine.py` for skill-eligible workflows.
  ├── 2. Target `~/.gemini/antigravity-cli/skills/`, `~/.claude/skills/`, `~/.config/opencode/skills/`.
  └── 3. Update `/list-workflows` and `getting-started` to report global skill availability.

  Phase 3: Automated Migration & Reconcile Engine (Medium-Term)
  ├── 1. Add `aw migrate --to-clean-delta` and `aw migrate --to-tracked`.
  ├── 2. Implement drift-aware silent reconciliation on identical-version reinstall.
  └── 3. Add `--sibling-dir` custom path support.
```

---

## 8. Open Questions & Required Evidence

1. **Host Discovery Proof for Cursor `.mdc` Local Exclusion**:
   - *Question*: Does Cursor's context engine reliably parse `.cursor/rules/*.mdc` files when they are listed in `.git/info/exclude`?
   - *Required Evidence*: Empirical test creating `.cursor/rules/probe.mdc` under `.git/info/exclude` and asserting that `@rule` indexing fires.
2. **VS Code Copilot Instruction File Multi-Root Scope**:
   - *Question*: Can VS Code Copilot read instruction files located in a sibling workspace folder without explicitly adding the sibling to the VS Code workspace file?
   - *Required Evidence*: Multi-root workspace test with `github.copilot.chat.codeGeneration.useInstructionFiles` pointing across roots.
