---
id: z0wxwa
created: 20260726
set: awdeliv
order: 02
topic: []
model: gemini31pro
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260726-awdeliv-02-z0wxwa-aw-delivery-and-clean-delta.gemini31pro.research-report.md.
consumed-by: []
---
# File: agent-workflows-architecture.gemini31pro.md

## 1. Goal Analysis and Reframing

I have reviewed the current architecture and the desired behaviors. The assumption that we can safely inject managed directories into any target repository and track them by default is a foundational flaw if we want this tooling to be universally adopted. Developers will not use a tool that pollutes their pull requests or forces them to explain rogue `AGENTS.md` files to upstream maintainers.

Here is a rigorous evaluation of your stated goals:

*   **1. Clean-delta contribution:** *Keep this. This is the primary driver.* If the tool cannot operate invisibly in a foreign repository, its utility is severely capped.
*   **2. Do-not-advertise / low-footprint:** *Merge with Goal 1.* The mechanism to achieve a clean delta inherently solves the privacy/stealth requirement. Treating them separately will lead to over-engineered configuration flags.
*   **3. Per-class tracking opt-out:** *Reframe this.* Allowing mixed tracked/untracked states within the *same* directories (e.g., via `local/` lanes or `*.untracked` suffixes) is a recipe for Git accidents and deployment drift. We must enforce strict physical separation: tracked artifacts go in one root, untracked/local artifacts go in another.
*   **4. Untrackable framework + manifest:** *Keep this, but elevate it.* The framework and manifest should be untrackable *by default* in foreign repos.

## 2. Recommended Architecture: The "Phantom Installation" Model

We must abandon the idea that the target repo's Git history is the source of truth for our framework files. We need an architecture that guarantees host discovery without Git footprint.

I recommend **Mechanism A (In-repo, locally excluded)** combined with a **Sibling Directory for Artifacts**.

### End-to-End Walkthrough (The Clean-Delta PR Case)

1.  **Installation:** The developer runs `aw install --clean`.
2.  **Framework Injection:** The installer writes `.agents/` and the manifest directly into the target repo (`~/src/upstream-repo/`).
3.  **Git Exclusion (The Core Trick):** The installer *does not* touch `.gitignore`. Instead, it appends `/.agents/` to `.git/info/exclude`.
    *   *Result:* The files are physically present on disk for local AI agents to discover, but Git is entirely blind to them. They will never accidentally enter a PR.
4.  **Artifact Routing:** The developer's global config (`~/.config/agent-workflows/config.json`) maps this repo's output artifacts (plans, prompts, IPDs) to a sibling directory they control: `~/src/upstream-repo.aw-artifacts/`. This sibling directory is its own independent Git repository.
5.  **Execution:** The local AI host (e.g., Claude Code, Cursor) scans the workspace, physically sees `.agents/AGENTS.md` and the shims, and follows them. The workflows run and execute plans, writing outputs to the sibling directory.
6.  **Uninstall:** `aw uninstall` reads the local manifest, deletes the unedited `.agents/` files, and removes the entry from `.git/info/exclude`. Zero trace remains.

## 3. Host Discovery & The `SKILL.md` Problem

In a clean-delta scenario, the host must discover workflows without relying on a committed `.gitignore` or tracked `AGENTS.md`.

### 3a. Host-Native Discovery Realities
*   **Cursor / VS Code Copilot:** Rely on `.vscode/settings.json` (can be excluded via `.git/info/exclude`) or global settings. Very reliable for local, untracked files.
*   **Claude Code:** Auto-discovers `.claude/skills/`. However, if this directory is not tracked, Claude still reads the physical disk.
*   **Antigravity:** For cross-environment setups (e.g., Antigravity executing against a WSL filesystem from a Windows host), relying on local `.git/info/exclude` discovery often fails silently if the agent loses context of the active virtual environment or cannot accurately map the boundary between the host and the VM. Host discovery mechanisms here must not assume unified filesystem visibility; if the tooling lives in WSL, the agent must be natively invoked within that same context.

### 3b. The `SKILL.md` Evaluation
We should **not** pivot our entire architecture to `SKILL.md`.
*   **Format constraints:** The schema is highly fragmented across hosts. A Claude `SKILL.md` is structurally different from a Copilot extension.
*   **Suitability:** `SKILL.md` is designed for stateless, functional tools (e.g., "fetch Jira ticket"). Our persona runbooks (advise, assess) and lifecycle plans require deep contextual chaining that breaks the standard skills contract.
*   **Recommendation:** Use `SKILL.md` purely as a *complementary pointer*. Generate a `.claude/skills/aw-bootstrap/SKILL.md` that simply tells the host: "For complex workflows, read `.agents/workflows/`." Do not attempt to mechanically translate our logic into individual skills.

## 4. Cost / Benefit / Risk Analysis of Mechanisms

| Mechanism | Description | Benefit | Cost / Risk | Proof Required |
| :--- | :--- | :--- | :--- | :--- |
| **A (Recommended)** | In-repo, excluded via `.git/info/exclude`. | 100% clean Git delta; zero host discovery friction (files exist locally). | Exclude lists are per-clone; not shared with collaborators. | Verify no hosts strictly filter context via `git ls-files` instead of raw filesystem reads. |
| **B** | Sibling "mini-repo" beside target. | Keeps target directory entirely pristine. | High friction. AI hosts natively struggle to resolve relative paths `../` outside the active workspace. | Requires testing host sandbox escapes (many block `../` reads for security). |
| **C** | Global install `~/.config/...` | Cleanest per-repo footprint. | Breaks repo-specific prompt tuning. | Proof that hosts will reliably execute workflows stored in a global user path. |
| **D** | Nested `.gitignore` opt-out. | Easy to build. | Clutters Git history with `.gitignore` modifications; high risk of user error. | None, but highly discouraged. |
| **E** | Status Quo. | No engineering effort. | Completely fails the clean-delta requirement. | N/A |
| **F** | `SKILL.md` delivery. | Natively supported by newer agents. | Highly fragmented; unsuitable for persona/dialogue workflows. | Schema mapping per host. |

## 5. Lifecycle, Migration, and Versioning

*   **Migration:** If a repo was installed the "tracked" way, running `aw configure --mode=phantom` must execute `git rm --cached -r .agents/`, commit the removal locally, and append to `.git/info/exclude`.
*   **Re-installing Exact Version:** The installer must read the manifest. If the top-level `installed_version` and the SHAs match, it should silently no-op and exit with `0`. Do not overwrite files needlessly.
*   **Revert Preservation:** Do not build complex Git commit reverting. The manifest tracking the `installed_version` + the existing timestamped backups (`.agent-workflows-installer-backups/`) is sufficient. The files are tiny text files. If a user needs to revert, we simply restore the last backup directory.

## 6. Open Design Questions & Recommendations

1.  **Configuration Location:** The choice of "tracked" vs "phantom" (clean-delta) MUST be stored in the USER-GLOBAL config (`~/.config/agent-workflows/config.json`) under a per-repo mapping: `"repos": { "/src/target": { "mode": "phantom" } }`. Putting this preference in the repo's manifest defeats the purpose of the clean delta.
2.  **UI/UX:** Use a flag during install: `aw install --phantom` (or `--clean-delta`). Make this sticky by writing it to the global config.
3.  **Prior Choices:** Deprecate the in-repo `AGENTS.md` pointer requirement for phantom mode. Rely on local shims excluded from Git.

## 7. Phased Execution Plan

*   **Phase 1 (Safe to build now):** Implement the `--phantom` install mode. Wire the installer to write to `.git/info/exclude` instead of `.gitignore`. Update the global config schema to track per-repo phantom states.
*   **Phase 2 (Requires host evidence):** Build the Sibling Artifact Routing. Test whether agents will reliably read/write to `../<repo>.aw-artifacts/` without violating their internal security sandboxes.
*   **Phase 3 (Defer):** `SKILL.md` generation. Wait for the cross-tool `.agents/skills/` standard to mature before investing heavy engineering cycles into fragmented schemas.

## 8. Open Questions for Further Evidence

1.  Do any of our target hosts (specifically newer versions of Cursor or Claude Code) enforce a strict `git ls-files` check before allowing context inclusion, which would break Mechanism A?
2.  When an agent is asked to write a plan file to an absolute path defined in our local config (pointing to the sibling repo), do the hosts' file-writing tools support this natively, or will they throw a sandbox error?
