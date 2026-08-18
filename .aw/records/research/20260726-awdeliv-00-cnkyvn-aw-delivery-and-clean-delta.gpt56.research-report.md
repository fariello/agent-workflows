---
id: cnkyvn
created: 20260726
set: awdeliv
order: 00
topic: []
model: gpt56
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260726-awdeliv-00-cnkyvn-aw-delivery-and-clean-delta.gpt56.research-report.md.
consumed-by: []
---
# Agent Workflows Delivery and Clean-Delta Architecture

**Research date:** July 25, 2026
**Scope:** OpenCode, Claude Code, Codex, GitHub Copilot and VS Code Copilot, Cursor, Google Antigravity, Gemini CLI, Git behavior, installer ownership, migration, and rollback preservation
**Evidence standard:** Official product documentation and official Git documentation. “Documented” means the cited current documentation says the behavior exists. It does not mean the agent-workflows project has reproduced it. Where official documentation does not state a minimum version or does not address ignored files, that limitation is explicit.

## Executive recommendation

Build one new mode named `--clean-delta`. Do not build a generic `--no-track` mode yet, and do not use `--deep` for any tracking choice.

`--clean-delta` should use this architecture:

1. Keep the target repository’s index and tracked files completely untouched.
2. Create or select a sibling companion repository, such as `../opencode.aw/`, owned by the developer. Store plans, prompts, research, run records, and the clean-delta state manifest there.
3. Deliver a curated, task-oriented subset of agent-workflows as host-native user-scope skills. Use each host’s documented global skill directory, with explicit consent before modifying it.
4. Store the canonical target-repository-to-companion-repository mapping in the user-global agent-workflows config. Store a readable copy of the effective mapping and install provenance in the companion repository.
5. Parameterize every artifact-producing workflow around an explicit `artifact_root`. In clean-delta mode, it resolves to the companion repository, never to `.agents/` in the target.
6. Keep the current in-repo shim plus pointer design as the default for repositories the user owns. Skills should complement it initially and may replace selected shims only after host-specific conformance tests pass.
7. Offer locally excluded project skills or pointer files only as a host-specific fallback. They leave the Git delta clean but still put hidden agent-workflows files inside the target checkout, can be force-added, and are not yet documented as discoverable when ignored by every host.

This composition is the simplest design that satisfies the strongest requirement without depending on unproven out-of-repository `Read and execute` behavior. The global skill is the discovery mechanism. The companion repository is the artifact and versioning mechanism. The target repository needs neither a shim nor a modified instruction file.

There is one important qualification: this design is reliable only for local host sessions that can read the developer’s user-scope skills and can access the companion directory. Remote cloud agents do not automatically receive local home-directory skills, local `.git/info/exclude`, or a sibling repository. A clean-delta installation must therefore declare its execution boundary. “Local clean-delta” can be supported now. “Remote clean-delta” needs a separate delivery mechanism and should not be promised by this feature.

## 1. Goals, reframed

### 1.1 Keep

#### Clean-delta contribution

Keep this as the primary requirement and define it precisely:

> After installation and normal use, `git status`, the branch diff against upstream, and the proposed pull request contain only the developer’s intentional contribution. No agent-workflows path, manifest, ignore rule, instruction edit, or generated artifact is tracked by the target repository.

The requirement concerns the target repository’s Git delta, not necessarily the absence of every local file under the checkout. Nevertheless, a design with no agent-workflows files in the checkout is preferable because it reduces accidental disclosure and force-add risk.

#### Developer-owned artifact history

Keep this as a first-class requirement:

> Plans, IPDs, prompts, research, run records, and lifecycle moves remain versioned in a Git repository controlled by the developer.

This cannot be satisfied by `.git/info/exclude`, a global ignore file, or an untracked directory. It requires another repository. A sibling companion repository is clearer and easier to inspect than a hidden store under the home directory.

#### Reversible ownership

Keep conservative uninstall and edited-file preservation. Extend ownership to global skills and companion files instead of assuming every managed object lives under the target repository.

### 1.2 Reframe

#### “Do not advertise”

Reframe this as **no target-repository disclosure**, not secrecy. A tool should not promise that its use is undetectable. Shell history, editor state, process lists, logs, generated text, commit style, companion repository remotes, or uploaded session telemetry may reveal usage. The installer can promise only that it does not modify tracked target-repository content in clean-delta mode.

#### Per-class tracking opt-out

Reframe this as artifact routing, not as a proliferation of ignore rules:

```text
class -> artifact root -> tracking policy
```

For example:

```text
plans    -> ../opencode.aw/plans/    -> tracked
prompts  -> ../opencode.aw/prompts/  -> tracked
research -> ../opencode.aw/research/ -> tracked
comms    -> .agents/comms/local/     -> untracked
```

The current “directory choice is the tracking choice” principle is good. Preserve it. Do not add filename suffixes, nested ignore blocks, and per-class configuration when one routed directory already expresses the choice.

#### “Untrackable framework + manifest”

Split this into two cases:

- In an owned repository, locally excluding an otherwise in-repo framework may be useful but is not the cleanest architecture.
- In clean-delta mode, the framework should be user-global or in the companion repository, and the target-repository manifest should not exist at all.

The phrase “untrackable manifest” hides an ownership problem. If the manifest itself is ignored and later lost, conservative uninstall loses its authority. Clean-delta state belongs outside the target, not merely ignored inside it.

### 1.3 Drop for now

Do not build a generic `--no-track`. It is ambiguous about whether artifacts are discarded, left untracked, stored elsewhere, or excluded globally. It also does not promise a clean pull request.

Do not use `--deep`. The name says nothing about tracking, discovery, location, or side effects.

Do not build arbitrary per-file or per-class ignore generation until real use demonstrates that directory routing is insufficient.

## 2. The discovery problem

The current architecture couples four separate concerns:

1. installer source;
2. host discovery;
3. workflow execution;
4. artifact storage.

Package data already solved installer source, but shims and instruction pointers still make discovery depend on an in-repository workflow copy. That coupling is what works against clean-delta.

A sibling repository alone does not solve discovery. Nor does a global framework directory. The host must first know that the capability exists. Asking the user to tell the agent to read an external path works because the prompt itself supplies discovery, but it is repetitive, path-sensitive, easy to mistype, and dependent on the host’s sandbox and path access. It is an acceptable escape hatch, not a product architecture.

Host-native skills provide the missing discovery layer. They expose a small name and description to the host, and load the full instructions on demand. Current official documentation now describes user-scope skills for all seven requested host families, although paths, frontmatter extensions, precedence, consent, and remote-session behavior differ.

The correct dependency chain is therefore:

```text
host-native user skill
    -> reads per-repository mapping
    -> executes packaged workflow
    -> writes artifacts to companion repository
    -> leaves target repository untouched
```

The target repository’s own `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` remains in place and continues to supply upstream project instructions. The user skill supplies an on-demand procedure. Neither must overwrite the other.

## 3. Host-by-host evidence

### Evidence labels

- **Documented:** Current official documentation explicitly describes the path or behavior.
- **Not documented:** The current official documentation reviewed does not settle the claim.
- **Must reproduce:** A conformance test is required before agent-workflows may promise the behavior.

Unless a minimum version is stated below, the official page does not provide one. Pin the exact installed host version in the conformance matrix instead of translating “current docs” into an invented minimum.

### 3.1 OpenCode

#### Documented discovery

OpenCode documents project skills at:

- `.opencode/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`

It documents global skills at:

- `~/.config/opencode/skills/<name>/SKILL.md`
- `~/.claude/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

For project skills, OpenCode walks upward from the current working directory to the Git worktree. Global skills are also loaded. Skills are listed by name and description and loaded on demand with the native skill tool. The documented frontmatter is `name` and `description`, plus optional `license`, `compatibility`, and string-to-string `metadata`; unknown fields are ignored. See [OpenCode Agent Skills](https://opencode.ai/docs/skills/).

OpenCode also documents global instructions at `~/.config/opencode/AGENTS.md` and project instructions in `AGENTS.md`. Project and global categories both apply. An `AGENTS.md` wins over `CLAUDE.md` within the project category, while the OpenCode global file wins over `~/.claude/CLAUDE.md` within the global category. Its global `opencode.json` can list instruction files and remote URLs, and those instructions are combined with `AGENTS.md`. See [OpenCode Rules](https://opencode.ai/docs/rules/).

#### Clean-delta assessment

**Best path:** a user skill in `~/.agents/skills/agent-workflows-*` or `~/.config/opencode/skills/agent-workflows-*`.

This coexists with an upstream root `AGENTS.md` because the skill and the project instructions are separate discovery channels. Avoid putting an agent-workflows pointer into the global `AGENTS.md`: it would load in every project, spend context on unused procedures, and require per-repository branching inside an always-on instruction.

OpenCode’s global `instructions` setting is a viable host-specific alternative for always-on content, including external files, but it is not needed for on-demand workflows.

**Not documented:** whether a project skill excluded through `.git/info/exclude` is still discovered. The docs describe filesystem paths, not Git filtering. Do not infer support.

### 3.2 Claude Code

#### Documented discovery

Claude Code documents:

- personal skills: `~/.claude/skills/<name>/SKILL.md`;
- project skills: `.claude/skills/<name>/SKILL.md`;
- plugin skills: `<plugin>/skills/<name>/SKILL.md`.

Enterprise skill delivery is also supported through managed settings. Personal skills override project skills with the same name; project skills override bundled skills. Claude can invoke a skill automatically from its description or directly as `/skill-name`. Existing `.claude/commands/*.md` continue to work, but a same-named skill takes precedence. Claude Code follows the Agent Skills open standard and adds host-specific fields and features. See [Claude Code Skills](https://code.claude.com/docs/en/skills).

The current documentation is unusually version-specific in several places. For example, it states that bundled `/verify` and `/code-review` became user-invoked-only in v2.1.215, and describes fixes through v2.1.217. Those statements show that behavior changes within the 2.1 series. They do not establish a single minimum version for all personal-skill behavior.

Claude also documents a personal project-specific `CLAUDE.local.md`, normally Git-ignored, which loads alongside an upstream `CLAUDE.md`. It documents absolute and relative `@` imports, including external imports, with an approval dialog for external imports originating in project memory. It further documents that `--add-dir` automatically discovers `.claude/skills/` in the added directory, while other configuration is not loaded unless separately enabled. See [Claude Code Memory](https://code.claude.com/docs/en/memory).

Claude Code currently states that it reads `CLAUDE.md`, not `AGENTS.md`, unless a `CLAUDE.md` imports or links the latter. Therefore an upstream repository that has only `AGENTS.md` does not automatically provide those instructions to Claude Code.

#### Clean-delta assessment

**Best path:** personal skills in `~/.claude/skills/`. This produces no target-repository footprint and coexists with upstream `CLAUDE.md`.

**Useful fallback:** launch Claude with `--add-dir ../opencode.aw` and place skills under `../opencode.aw/.claude/skills/`. This provides per-companion discovery without installing into the shared personal directory, but it changes the launch command and requires directory access consent.

**Possible pointer fallback:** a locally excluded `CLAUDE.local.md` can import an external companion file. This is documented as a personal project mechanism, but the file still exists in the target checkout. Use `.git/info/exclude`, not tracked `.gitignore`, if zero tracked pollution is required.

**Remote limitation:** Claude’s documentation states that cloud and Cowork sessions do not read the machine’s `~/.claude/skills/`. Cloud sessions can load committed project skills or account-enabled skills. A local clean-delta design therefore does not automatically work in Claude cloud sessions.

**Not documented:** whether `.git/info/exclude` affects Claude’s skill scanner. The `CLAUDE.local.md` documentation assumes Git-ignored local files load, which is positive evidence for local memory files, not necessarily for project skill directories.

### 3.3 Codex

#### Documented discovery

Codex documents repository skills under `.agents/skills` in each directory from the current working directory to the repository root, user skills at `~/.agents/skills`, administrator skills at `/etc/codex/skills`, and bundled system skills. It also documents support for symlinked skill folders and says Codex follows the target when scanning. See [Build Skills for Codex](https://developers.openai.com/codex/skills).

The minimal common `SKILL.md` frontmatter is `name` and `description`. Codex can add optional UI, invocation, and tool dependency metadata through `agents/openai.yaml`, but that file is not portable and should be generated only for Codex when needed.

Codex separately documents global instructions in `~/.codex/AGENTS.md` or `AGENTS.override.md`. It concatenates global instructions with project instructions from the repository root down to the current directory. A closer project instruction appears later and therefore has greater specificity. See [Codex AGENTS.md Guidance](https://developers.openai.com/codex/guides/agents-md).

#### Clean-delta assessment

**Best path:** user skills in `~/.agents/skills/`. This leaves upstream `AGENTS.md` untouched and preserves its normal project-instruction role.

Because `~/.agents/skills` is also documented by OpenCode, Cursor, GitHub Copilot, and Gemini CLI, it is the best candidate for a shared portable installation. It is not universal because Claude Code and Antigravity document different primary global paths.

Do not place a per-repository pointer in `~/.codex/AGENTS.md`. Global instructions apply to every repository. A small generic sentence that says “when an agent-workflows skill is explicitly invoked, use the mapping” is unnecessary because the skill already supplies that behavior.

**Remote limitation:** user-home skills are a local discovery mechanism. Codex cloud environments need the skill to be available in that environment through their own user setup, plugin distribution, or committed project files. A sibling directory on the developer workstation is not present in a cloud clone.

**Not documented:** whether a Git-ignored repository skill is discovered. Codex documents the path scanner, not its relationship to Git ignore rules. Test before supporting a locally excluded `.agents/skills` fallback.

### 3.4 GitHub Copilot and VS Code Copilot

#### Documented discovery

GitHub documents project skills in:

- `.github/skills/<name>/SKILL.md`
- `.claude/skills/<name>/SKILL.md`
- `.agents/skills/<name>/SKILL.md`

It documents personal skills in:

- `~/.copilot/skills/<name>/SKILL.md`
- `~/.agents/skills/<name>/SKILL.md`

The documentation says skills work with Copilot cloud agent, Copilot code review, GitHub Copilot CLI, the GitHub Copilot app, and agent mode in VS Code. The minimal frontmatter is `name` and `description`, with optional `license`; `allowed-tools` is a Copilot extension that can preapprove shell access and therefore should not be emitted by default. See [Adding Agent Skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills).

GitHub also documents repository agent instructions in `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`, plus `.github/copilot-instructions.md` and path-specific instruction files. The nearest `AGENTS.md` takes precedence among agent instruction files. Personal instructions have higher priority than repository instructions, and repository instructions have higher priority than organization instructions, although all relevant sets are provided. See [Adding Repository Custom Instructions for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions).

The official skill page also states that the `gh skill` command is public preview and requires GitHub CLI 2.90.0 or later. That version applies to `gh skill`, not necessarily to every Copilot skill consumer.

#### Clean-delta assessment

**Best local path:** `~/.agents/skills/` or `~/.copilot/skills/` for VS Code agent mode and local Copilot CLI/app sessions.

This coexists with an upstream `AGENTS.md` because the user skill is an on-demand capability and the repository file is project guidance.

**Cloud limitation:** the documentation groups local and cloud consumers on one page but does not say that a workstation’s personal skill directory is uploaded to Copilot cloud agent or code review. It cannot be assumed. A local `.git/info/exclude` file is also absent from a GitHub-hosted clone. For remote cloud use, require a separate documented installation mechanism, such as a skill installed in the remote environment or a repository-committed skill. The latter conflicts with zero PR footprint.

**Not documented:** whether VS Code Copilot discovers a project skill ignored through `.git/info/exclude`, and whether personal skills are synchronized to each cloud surface. Both require reproduction.

### 3.5 Cursor

#### Documented discovery

Cursor documents project skills at `.agents/skills/` and `.cursor/skills/`, and user skills at `~/.agents/skills/` and `~/.cursor/skills/`. For compatibility, it also reads project and user Claude and Codex skill directories. Cursor automatically discovers skills at startup and can invoke them automatically or via `/`. See [Cursor Agent Skills](https://cursor.com/docs/skills).

Cursor’s current documentation refers to its `/migrate-to-skills` feature in Cursor 2.4. This is a documented point release for that migration feature, not a complete minimum-version statement for all skill locations.

The required common frontmatter is `name` and `description`. Cursor adds `paths`, `disable-model-invocation`, and `metadata`. A portable skill should not rely on these extensions. A Cursor-specific rendered variant may add `disable-model-invocation: true` for costly or assessor-style workflows.

Cursor also documents global User Rules in its Customize interface and repository `AGENTS.md` files at root and nested paths. Parent and nested `AGENTS.md` instructions are combined, with the more specific file taking precedence. User Rules apply to Agent Chat, not Inline Edit. See [Cursor Rules](https://cursor.com/docs/rules).

#### Clean-delta assessment

**Best path:** `~/.agents/skills/` or `~/.cursor/skills/`.

Use skills rather than User Rules because User Rules are always a broad personalization layer, have a UI-managed lifecycle, and are not appropriate for a suite of on-demand procedures.

**Not documented:** whether a project skill ignored by Git is still discovered. The docs say Cursor scans directories, but do not expressly state that Git ignore status is irrelevant.

### 3.6 Google Antigravity

#### Documented discovery

The current Antigravity 2.0 documentation, shown for v2.3.1 when researched, documents:

- workspace skills: `<workspace-root>/.agents/skills/<skill-folder>/`;
- global skills: `~/.gemini/config/skills/<skill-folder>/`.

It retains backward compatibility for `.agent/skills`. A `SKILL.md` requires `description`; `name` is optional and defaults to the folder name. Skills use progressive disclosure and can be selected automatically from their descriptions. See [Google Antigravity Skills](https://antigravity.google/docs/skills).

Antigravity also documents global rules in `~/.gemini/GEMINI.md`, workspace rules in `.agents/rules`, and global or workspace workflows invoked as slash commands. Absolute paths in rule `@` references are documented. See [Google Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows).

#### Clean-delta assessment

**Best path:** global skills in `~/.gemini/config/skills/`.

Antigravity’s global workflows may be a closer semantic match for explicit runbooks than skills. However, the documentation page does not expose a stable filesystem path for global workflow files in the cited text. Do not automate global workflow installation until that path and ownership behavior are documented or reproduced. Skills already have a documented path and should be the first integration.

Avoid using `~/.gemini/GEMINI.md` as an agent-workflows pointer. It is global, always applied, and also used by Gemini tooling. Mutating it has a large blast radius.

**Not documented:** whether `.git/info/exclude` is consulted during workspace skill discovery. Test before supporting a locally excluded workspace skill.

### 3.7 Gemini CLI

#### Documented discovery

Gemini CLI’s Agent Skills documentation, last updated April 30, 2026, describes:

- user skills: `~/.gemini/skills/` or `~/.agents/skills/`;
- workspace skills: `.gemini/skills/` or `.agents/skills/`;
- extension and built-in tiers.

Workspace skills have higher precedence than user skills, and the `.agents/skills` alias wins over `.gemini/skills` within the same tier. Discovery injects names and descriptions, activation requires user consent, and the skill directory is added to allowed file paths. Gemini CLI also provides `skills link`, install, enable, disable, list, reload, and uninstall commands. See [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/).

Gemini’s context documentation, last updated June 18, 2026, describes global `~/.gemini/GEMINI.md`, hierarchical workspace `GEMINI.md` files, just-in-time context, absolute and relative imports, and a configurable context filename list that can include `AGENTS.md`. See [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md/).

#### Clean-delta assessment

**Best path:** `~/.agents/skills/` for cross-host portability, or `~/.gemini/skills/` for a Gemini-only installation.

Gemini’s explicit activation consent and allowed-path expansion are positive for companion-repository access, but the exact relationship between the skill directory and an arbitrary sibling artifact root still needs a test. A skill can explain the mapping, but the host sandbox must permit writes to the companion directory.

Do not add agent-workflows to global `GEMINI.md`; it is always-on and may affect both Gemini CLI and Antigravity.

**Not documented:** whether workspace skills excluded through Git remain discoverable. Test it.

## 4. Cross-host skill format and suitability

### 4.1 Portable core

Generate one canonical skill source with only:

```yaml
---
name: plan-review
description: Reviews an implementation plan for completeness, feasibility, risk, and verification. Use when the user asks to review or challenge a plan.
---
```

The body should use plain Markdown and relative references within the skill directory. Treat these as the portable core:

- lowercase hyphenated directory and name;
- `name`;
- `description`;
- Markdown body;
- optional `scripts/`, `references/`, and `assets/` directories, but no assumption that every host grants execution automatically.

Render host-specific variants only where useful:

- Claude: invocation controls, subagent context, or dynamic context only in a Claude variant.
- Cursor: `disable-model-invocation` or `paths` only in a Cursor variant.
- Copilot: never emit `allowed-tools: shell` by default.
- Codex: put UI and dependency metadata in `agents/openai.yaml`, not in portable frontmatter.
- Antigravity: include `name` even though optional, for portability.

OpenCode explicitly ignores unknown frontmatter fields, but that does not establish that every other host does. Unknown portable fields should therefore be avoided. A host that does not recognize `SKILL.md` normally ignores the directory as ordinary files, but this too is not a universal contractual guarantee if the directory is in a host-specific configuration path.

### 4.2 Which workflows should become skills

Good first-wave skills are on-demand, bounded, and recognizable from user intent:

- release-review;
- plan-review;
- verify;
- scaffold;
- spec;
- code or change assessment;
- research execution;
- artifact finalization, if it has a clear trigger and bounded output.

These fit progressive disclosure and do not need to occupy every session’s instruction context.

Persona, assessor, and dialogue runbooks need more care:

- `advise` and `assess` can be skills if their descriptions make the trigger narrow and the user can invoke them explicitly.
- A persistent “always act as persona X” directive is not a skill. It belongs in a user rule or explicit session prompt.
- A long conversational protocol that must govern the entire session may not reliably survive as an implicitly chosen skill. Prefer explicit invocation and test adherence after compaction.
- Workflows that differ only by a few parameters should share one skill plus a parameterized reference, not become dozens of near-duplicate skills.

Do not mechanically convert every workflow. Start with five or six high-frequency procedures, run trigger and adherence tests, then expand only where skills improve discovery over the existing shims.

### 4.3 Replace or complement

For normal tracked installs, skills should initially **complement** the shim and `AGENTS.md` pointer model:

- Existing users retain stable commands.
- Hosts without proven skill support continue to work.
- The project can compare discovery, invocation, and adherence.

For clean-delta local installs on a proven host, skills should **replace** target-repository shims and pointers. Writing both defeats the purpose.

For Antigravity, native workflows may eventually replace command-like skills after their global storage and ownership semantics are verified.

## 5. Candidate mechanisms: cost, benefit, and risk

| Mechanism | Needs served | Target footprint | Discovery dependency | Benefits | Costs and risks | Reversibility and proof |
|---|---|---:|---|---|---|---|
| **A. In-repo files locally excluded; artifacts external** | 1, 2, 3, 4 | Files exist locally, none tracked if exclusions are correct | Host must scan ignored files; external artifact path must be writable | Small change to installer; retains familiar paths | Force-add can expose files; exclude is per clone; existing tracked files are not affected; hidden files can collide with upstream additions; does not itself version artifacts | Record exclusions and files in external state. Must test discovery with `.git/info/exclude` for every host/version |
| **B. Sibling companion repository plus local pointer or no pointer** | 1, 2, 3, 4 | Zero if no pointer; local-only if pointer | No-pointer form needs global discovery; pointer form needs ignored-file discovery and out-of-repo reads | Clean ownership boundary; artifact Git history; easy backup and inspection | Host sandbox may block sibling access; path moves break mapping; two repositories to manage | Companion manifest plus global mapping. Test access, lifecycle moves, and path canonicalization |
| **C. Home-directory/global framework** | 1, 2, 4 | Zero | Host-global skill or config discovery | True zero-checkout footprint; one installation can serve many repos | Shared mutable namespace; version conflicts among repos; consent required; remote agents do not inherit workstation home | Separate global ownership manifest and reference counts or one selected global version. Test each host directory |
| **D. Per-class nested `.gitignore`** | 3, sometimes 4 | Tracked ignore files unless themselves locally excluded | None for Git; workflow paths must match lanes | Familiar Git behavior; clear in owned repositories | Pollutes PRs; ignored artifacts are not versioned; tracked files remain tracked; many blocks add complexity | Existing managed blocks can uninstall. No value for clean-delta |
| **E. Status quo and documentation only** | Partial 2 and 3 | Existing full footprint | Existing shims and pointers | No engineering work | Does not solve clean-delta or external versioning; makes user repeat manual external reads | Existing uninstall only |
| **F. Host-native skills** | 1, 2, 4, and discovery for 3 | Zero at user scope; local-only at ignored project scope; tracked at committed project scope | Host/version-specific skill discovery | Best on-demand discovery; progressive context; shared `~/.agents/skills` across five host families | No single universal global path; cloud sessions differ; trigger reliability is probabilistic; global mutation needs consent | Global manifest, per-host conformance tests, explicit invocation tests, and uninstall that preserves edited skills |
| **G. Recommended composition: B + C/F** | 1, 2, 3, 4 | Zero | Proven user skills plus sibling access | Separates discovery, execution, and artifact history; no target pollution | Requires workflow path parameterization and global ownership model | Strong: companion state plus global skill ownership; clean uninstall has no target cleanup |
| **H. Git worktree dedicated to tooling** | Partial 1 and 2 | Separate worktree may contain files, but contribution branch can remain clean | Host operates in tooling worktree; code delta transfer required | Strong filesystem isolation | Confusing branch/worktree lifecycle; generated artifacts and code changes split; upstream `AGENTS.md` still applies; more Git expertise required | Git-native but operationally heavy. Defer |
| **I. Wrapper launcher that injects host flags/config** | 1, 2, 4 | Zero | Host must expose launch-time instruction or add-directory flags | Can bind target and companion deterministically | Per-host wrapper maintenance; IDE launches may bypass it; shell aliases are not portable | Useful for Claude `--add-dir`; otherwise defer until a concrete gap remains |

### Candidate verdicts

- **Build G.**
- Use **F** as the discovery layer and **B** as the artifact/state layer.
- Keep **A** as a documented, explicitly experimental fallback.
- Keep **D** only for normal owned-repository installs.
- Do not present **E** as solving clean-delta.
- Defer **H** and general-purpose **I**.

## 6. End-to-end clean-delta walkthrough

### 6.1 Install

The user runs:

```bash
agent-workflows install --clean-delta --host opencode --artifact-repo ../opencode.aw
```

The installer:

1. Resolves the target to a canonical path and confirms it is a Git worktree.
2. Inspects the index and working tree. It does not require a clean tree, but records the pre-install `git status --porcelain=v2` for verification.
3. Creates or selects `../opencode.aw/`.
4. Initializes that directory as a separate Git repository only after confirmation. If it already exists, it verifies its root and remote rather than assuming ownership.
5. Writes the companion layout:

   ```text
   opencode.aw/
   ├── .agent-workflows/
   │   └── state.json
   ├── plans/
   ├── prompts/
   ├── research/
   ├── runs/
   └── comms/
   ```

6. Adds the canonical target path and class routing to the user-global config:

   ```json
   {
     "repos": {
       "/abs/path/opencode": {
         "mode": "clean-delta",
         "artifact_root": "/abs/path/opencode.aw",
         "artifact_routes": {
           "plans": "plans",
           "prompts": "prompts",
           "research": "research",
           "runs": "runs",
           "comms": "comms"
         }
       }
     }
   }
   ```

7. Shows the exact user-scope host directory it proposes to modify and requests consent.
8. Installs only the selected, skill-eligible subset in the host’s global skill directory. It records hashes, source version, source revision when applicable, and ownership in a global agent-workflows manifest.
9. Writes companion `state.json` with the effective routing, agent-workflows version, target identity, and host integration. This file may be tracked because the companion belongs to the developer.
10. Verifies that the target’s tracked and untracked status is byte-for-byte equivalent to the pre-install status. If it differs, installation fails and rolls back.

### 6.2 Use

The developer starts the local host in the target repository. The upstream repository’s own `AGENTS.md` or host equivalent loads normally.

The host also lists the user-scope agent-workflows skills. The developer invokes one explicitly, for example:

```text
/plan-review
```

or uses natural language that matches the description.

The skill:

1. identifies the canonical working repository;
2. reads the mapping from the user-global config through an agent-workflows resolver command;
3. confirms the resolved artifact root;
4. runs the workflow against the target code;
5. writes the plan and run record under `../opencode.aw/`;
6. performs lifecycle moves within the companion repository, such as `plans/pending` to `plans/executed`;
7. commits only when the runbook explicitly calls for a commit, and commits in the companion repository, never in the target.

The resolver command is important. Do not make every skill parse JSON or duplicate XDG and path-canonicalization logic. A small command such as:

```bash
agent-workflows context --repo "$PWD" --json
```

should return the effective mode, artifact root, routes, host, and version. The host may call it from a subdirectory, so the resolver must identify the enclosing Git root first.

### 6.3 Produce the pull request

Before commit or PR creation, a clean-delta verification command checks:

```bash
agent-workflows verify-clean-delta --repo /abs/path/opencode
```

It fails if any known agent-workflows path is tracked, staged, untracked, or modified in the target, including:

- `.agents/agent-workflows/`;
- `.agents/workflows/`;
- generated host shims;
- agent-workflows managed blocks;
- backup directories;
- an agent-workflows modification to `.gitignore`, `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`.

It should also compare the branch diff against the merge base and inspect staged content. Merely checking `git status` is insufficient after a commit.

The companion repository may have its own commits and remote. They are unrelated to the upstream pull request.

### 6.4 Uninstall

The user runs:

```bash
agent-workflows uninstall --clean-delta --repo /abs/path/opencode
```

The installer:

1. reads global and companion state;
2. removes the per-repository mapping;
3. does not delete the companion repository by default;
4. reports the companion path and offers a separate explicit archive or remove action;
5. decrements or re-evaluates global skill ownership;
6. removes a global skill only when no configured repository needs that installed integration and the current hash matches the installer-written hash;
7. preserves edited global skills and reports them;
8. verifies that the target repository remains unchanged.

Never recursively delete a companion repository as an implicit part of uninstall. It contains the developer’s history.

## 7. Ownership, manifest, backup, and lifecycle design

### 7.1 Use three scopes of state

#### User-global config

Store user choices and target mappings:

- canonical target path;
- mode;
- companion path;
- artifact routes;
- enabled hosts;
- requested global skill channel or version.

This is the authoritative local routing source because the target must remain untouched.

#### Global ownership manifest

Store ownership for user-scope host mutations:

- absolute managed path;
- host;
- logical skill ID;
- installed content hash;
- installed source version;
- installed source revision, when the build is not uniquely identified by a release version;
- repositories currently depending on it;
- install transaction ID.

Do not overload each target repository’s manifest to own a shared home-directory file.

#### Companion state

Store a readable, versioned snapshot of:

- target identity and last known path;
- effective artifact routes;
- agent-workflows version used for each run or install;
- lifecycle conventions;
- generated artifact provenance.

The companion copy helps recovery if the user-global config is lost, but it should not silently override a conflicting global mapping. Recovery must be explicit.

### 7.2 Path identity

Canonical absolute paths are necessary but insufficient because repositories move. Record:

- canonical path;
- Git common directory identity where available;
- primary remote URL as a hint, never as a unique identity;
- companion repository identifier.

On a path miss, search only configured nearby candidates or require the user to repair the mapping. Do not scan the entire home directory.

### 7.3 Backups

Keep the current backup behavior for in-repo tracked mode. For clean-delta:

- back up edited global host files before overwrite;
- keep backups outside the target;
- never put backups in the companion’s normal artifact lanes unless the user requests it;
- index each backup with source path, prior hash, prior source version if known, transaction ID, and timestamp.

Retaining only five backups is enough for recent `--undo`, not for future arbitrary downgrade. Do not claim otherwise.

### 7.4 Lifecycle

The current convention-only `git mv` model remains acceptable if every producing runbook resolves the correct repository before moving or committing. Change the instruction from an implicit relative path to:

> Resolve `artifact_root`. Perform lifecycle moves and any artifact-only commit inside that repository. Never commit or push the target repository unless the workflow’s code-change purpose explicitly requires it.

The existing “commit this artifact, never push” language must identify which repository receives the commit. In clean-delta mode, it is the companion.

## 8. Migration and compatibility

### 8.1 Existing tracked installation to clean-delta

This is a migration, not a reinstall.

Recommended flow:

1. Verify the old manifest.
2. Create and validate the companion repository.
3. Copy or move user artifacts into the companion, preserving their relative history only if the user chooses a Git history migration.
4. Install global skills and verify discovery.
5. Remove unedited installer-owned target files and managed blocks using the existing conservative uninstall rules.
6. Preserve edited owned files and stop. The target cannot be declared clean-delta until the user resolves them.
7. Do not modify tracked `.gitignore` to hide leftovers.
8. Verify the complete branch diff and index.
9. Record migration completion in global and companion state.

There are two valid artifact-history choices:

- **Simple default:** move current artifact files to the companion and start new history there.
- **Advanced explicit option:** use `git filter-repo` or a history extraction workflow to preserve artifact history. This is destructive and complex and should never run automatically.

If old agent-workflows files were committed on the developer’s contribution branch, migration must remove them from the branch diff. If they exist in upstream history, clean-delta cannot erase upstream’s own files and should not try.

### 8.2 Clean-delta upgrade

An upgrade should:

1. leave the target untouched;
2. update global skills through the global ownership manifest;
3. preserve edited global skill files;
4. update companion state;
5. run host discovery checks;
6. verify clean delta again.

If two repositories request incompatible framework versions in one shared global skill directory, do not oscillate files on each invocation. Initially support one selected global skill version and warn about the conflict. Later, consider versioned skill names only if real compatibility failures occur. Versioned names degrade invocation ergonomics and should not be the first design.

### 8.3 Same-version reinstall

Use these semantics:

| State | Behavior |
|---|---|
| Same version, manifest present, hashes match, routes match | No-op with one concise “already installed and verified” result |
| Same version, manifest present, installer-owned file missing | Report drift; require `--repair` or interactive confirmation to recreate |
| Same version, manifest present, file edited | Preserve it; report drift; never overwrite without an explicit replace decision |
| Same version, manifest present, config differs | Reconcile only the requested configuration after showing the change |
| Manifest absent | Do not call it a no-op. Inspect, report unmanaged candidates, and require explicit `--adopt` or clean install |

Silent no-op hides drift. Automatic reconcile can overwrite user changes. A verified no-op is the correct default.

### 8.4 Preserve future downgrade without building it now

Backups alone suffice only for immediate restoration when:

- the needed transaction is still retained;
- the old files were captured;
- the user wants the exact previous bytes;
- no cross-file migration logic is required.

Backups do not suffice for an arbitrary future downgrade because the last-five policy can delete the needed state and because a coherent older installation may require files that were absent from the latest transaction.

The simplest forward-compatible record is:

- top-level effective installed version;
- per-managed-file source version;
- per-managed-file installed hash;
- one source revision for the transaction when the release version does not uniquely identify the bytes;
- install transaction ID;
- backup index with from-version and to-version.

Per-file source version is worthwhile because managed installations can become mixed after edited files are preserved, optional host integrations differ, or a partial repair occurs. A single top-level version would falsely imply homogeneity.

Do not store an install Git commit ID when a published package version uniquely identifies immutable package data. Store a source revision for development snapshots, unreleased builds, or mutable package sources. Future downgrade can then render the requested old package and use the same hash-aware install transaction machinery. No downgrade command is needed now.

## 9. Open design decisions

### 9.1 Where the per-repository choice lives

**Recommendation:** authoritative mapping in user-global config, ownership in a global manifest, recovery snapshot in the companion.

Do not put clean-delta choice in the target manifest because the target manifest must not exist. Do not treat `.git/info/exclude` as configuration; it expresses only Git visibility and cannot identify artifact routes, host integration, version, or ownership.

### 9.2 Committed or local

In clean-delta mode, no choice is committed to the target. This means collaborators do not inherit the setup. That is correct for a private contributor workflow.

The companion configuration may be committed because the companion belongs to the developer. It may contain absolute paths, so separate portable policy from machine-local bindings:

- tracked companion file: relative layout, workflow version, artifact policy;
- user-global config: absolute target and companion paths.

### 9.3 Interactive or flag-driven

Support both:

- `--clean-delta` is the explicit noninteractive mode selector.
- `--artifact-repo PATH` specifies the companion.
- `--host HOST` may repeat.
- `--yes` may accept ordinary reversible writes, but must not bypass a security or host-consent prompt that the host itself requires.
- Interactive install should explain target writes, global writes, and companion writes separately.

Do not infer clean-delta merely because the target remote is not owned by the user. Ownership cannot be determined reliably from Git remotes.

### 9.4 Prior choices to revisit

#### Tracked-by-default per-repo manifest

Keep it for normal tracked installs. It is correct for shared repository ownership and conservative uninstall. Do not use it for clean-delta.

#### In-repo shims

Keep for compatibility in normal installs. Stop treating them as the universal discovery abstraction. On hosts with proven skills, consider a later option to prefer skills and reduce shim proliferation.

#### Root `AGENTS.md` pointer

Keep only where always-on workflow awareness is demonstrably valuable. A pointer that merely tells the model where commands live may be redundant once skills are reliably discovered. Re-evaluate it host by host after skill conformance testing.

The current mirroring into existing `CLAUDE.md` and `GEMINI.md` increases shared-file mutation and conflict risk. In clean-delta mode it must be disabled. In normal mode, make it opt-in once native skills cover the same discovery need.

#### Backups inside the target

The current backup directory itself creates target-checkout footprint. It is acceptable for normal installs, but clean-delta backups must live in a user-state directory or companion-specific private state, never inside the target.

## 10. Phased implementation plan

### Phase 0: conformance harness

Build before changing delivery:

1. A fixture repository with its own `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.
2. A unique test skill at every documented project and user path.
3. A `.git/info/exclude` variant and a `core.excludesFile` variant.
4. A sibling companion directory with read and write probes.
5. Tests for automatic discovery, explicit invocation, precedence, ignored-file discovery, external path access, artifact creation, and uninstall.
6. A results matrix keyed by exact host name, surface, version, operating system, and local versus cloud execution.

Do not ship host support based only on documentation. Documentation establishes plausibility; the harness establishes agent-workflows support.

### Phase 1: artifact-root abstraction

Safe to build without host evidence:

1. Introduce the `artifact_root` resolver.
2. Update all producing and lifecycle runbooks to use it.
3. Make artifact commits explicitly target the artifact repository.
4. Add `verify-clean-delta`.
5. Extend config schema with a hard-allowlisted per-repository object.
6. Add companion state and recovery validation.

This work is useful even before skill delivery and removes the largest architectural coupling.

### Phase 2: companion repository clean-delta mode

Build:

1. `install --clean-delta`;
2. `--artifact-repo`;
3. zero-target-write transaction checks;
4. migration from tracked mode;
5. clean-delta uninstall that preserves the companion;
6. global backup location.

At this phase, manual invocation may remain the temporary fallback for hosts whose skill integration has not passed conformance.

### Phase 3: portable global skills

Start with the documented shared path `~/.agents/skills` for:

- OpenCode;
- Codex;
- GitHub Copilot local surfaces;
- Cursor;
- Gemini CLI.

Add rendered installs for:

- Claude Code: `~/.claude/skills`;
- Antigravity: `~/.gemini/config/skills`.

Install only five or six selected skills. Require consent, maintain a global ownership manifest, preserve edited files, and test explicit invocation before testing automatic routing.

### Phase 4: host-specific improvements

Only after evidence:

- Claude `--add-dir` companion skill mode;
- OpenCode global `instructions` integration if always-on content remains necessary;
- Antigravity global workflows;
- Cursor-specific invocation controls;
- Codex plugin packaging for broad distribution;
- Gemini `skills link` as an alternative to copied installation;
- `gh skill` integration after its public-preview behavior stabilizes.

### Defer or reject

- arbitrary per-class nested ignore generation;
- hidden in-target manifest as the clean-delta state store;
- automatic mutation of global host instruction files;
- automatic deletion of companion repositories;
- versioned global skill names;
- remote-cloud clean-delta claims without a remote delivery design;
- history rewriting during ordinary migration;
- universal wrapper launchers.

## 11. Open questions and evidence required

| Question | Why it matters | Evidence that closes it |
|---|---|---|
| Does each host discover a project `SKILL.md` ignored by `.git/info/exclude`? | Determines whether locally excluded project skills are a valid fallback | Reproduction on each exact host/version, with skill listed and invoked while `git status` remains clean |
| Does `core.excludesFile` behave equivalently for host discovery? | Could provide one user policy across clones | Same reproduction, plus collision tests across unrelated repositories |
| Can each local host read and write the sibling companion path under default sandbox settings? | Required for external artifacts | Read, create, rename, `git mv`, commit, and cleanup test with no broad permission escalation |
| How does each host resolve same-named user and project skills? | Upstream may define a conflicting skill | Official precedence where available plus a two-skill reproduction |
| Do ignored local instruction files coexist with upstream `AGENTS.md` or equivalents? | Needed for pointer fallback | Context inspection showing both sources, ordering, and conflict behavior |
| Which host versions first support each skill path? | Needed for installer compatibility checks | Official changelog or source history plus execution test on oldest supported version |
| Are user skills available in remote or cloud surfaces? | Local success does not imply cloud success | Official remote-environment documentation and a clean remote session test |
| Does a host sync or copy personal skills without explicit consent? | Affects privacy and ownership | Official synchronization documentation and settings inspection |
| Does automatic skill routing reliably select assessor and dialogue workflows? | Determines skill subset | Trigger evaluation set with positive, negative, and ambiguous prompts; measure false positives and missed triggers |
| Does instruction adherence survive compaction and long sessions? | Long runbooks may degrade | Long-session eval with compaction and post-compaction verification |
| What happens when the target path moves? | Absolute mappings can stale | Rename/move tests using Git common directory and remote hints; explicit repair UX |
| What happens when two repositories require different agent-workflows versions? | Shared global skills can conflict | Compatibility test across adjacent released versions; decide whether one global version is sufficient |
| Where exactly are Antigravity global workflow files stored and owned? | Needed before automating workflow delivery | Official filesystem documentation or reproduced creation, restart, update, and deletion |
| Does Copilot cloud agent receive local personal skills? | Critical for GitHub-hosted work | Official statement or remote session showing the skill without repository files |
| Can clean-delta verification detect prior committed pollution after it is no longer in the working tree? | `git status` alone misses it | Merge-base diff, index, and commit-history fixture tests |

## 12. Required acceptance criteria

Do not label a host “clean-delta supported” until all of these pass for an exact version and surface:

1. The target repository begins with its own instruction file.
2. No target tracked file is modified.
3. No agent-workflows file is staged or committed in the target.
4. The user-scope skill is discovered after a fresh host start.
5. Explicit invocation loads the intended workflow.
6. The workflow reads target code.
7. The workflow writes an artifact into the companion repository.
8. A lifecycle move occurs inside the companion repository.
9. Any artifact commit occurs only in the companion repository.
10. The target branch diff against upstream contains only the genuine code change.
11. Uninstall removes only unedited globally owned skill files.
12. An edited global skill is preserved and reported.
13. The upstream instruction file remains effective throughout.
14. Reinstalling the same verified version is a reported no-op.
15. A missing or changed managed file produces drift, not silent overwrite.

## 13. Bottom line

The existing design is sound for repositories that intentionally adopt agent-workflows. It is not a suitable foundation for clean external contribution because it treats target-repository files as both the discovery mechanism and the storage location.

The minimal architectural correction is not “ignore more files.” It is to separate:

- discovery into host-native user skills;
- artifacts into a developer-owned companion repository;
- routing into user-global per-repository config;
- ownership into scope-appropriate manifests;
- target code into the untouched upstream checkout.

Build `--clean-delta` around that separation. Keep locally excluded in-repository discovery as an experimentally supported fallback, not the default. Preserve the existing tracked mode for shared adoption. Defer cloud claims, universal out-of-repository pointers, and broad per-class ignore machinery until concrete evidence shows they are needed.

## Official sources

All sources were accessed July 25, 2026.

- [Git: gitignore documentation](https://git-scm.com/docs/gitignore)
- [OpenCode: Agent Skills](https://opencode.ai/docs/skills/)
- [OpenCode: Rules and instruction discovery](https://opencode.ai/docs/rules/)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/skills)
- [Claude Code: How Claude remembers your project](https://code.claude.com/docs/en/memory)
- [OpenAI Codex: Build skills](https://developers.openai.com/codex/skills)
- [OpenAI Codex: Custom instructions with AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [GitHub Copilot: Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [GitHub Copilot: Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- [Cursor: Agent Skills](https://cursor.com/docs/skills)
- [Cursor: Rules](https://cursor.com/docs/rules)
- [Google Antigravity: Skills](https://antigravity.google/docs/skills)
- [Google Antigravity: Rules and Workflows](https://antigravity.google/docs/rules-workflows)
- [Gemini CLI: Agent Skills](https://geminicli.com/docs/cli/skills/)
- [Gemini CLI: GEMINI.md context](https://geminicli.com/docs/cli/gemini-md/)
