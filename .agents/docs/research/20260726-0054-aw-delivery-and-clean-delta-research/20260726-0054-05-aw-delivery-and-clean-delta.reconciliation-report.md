# Reconciliation of Four Agent-Workflows Clean-Delta Architecture Reports

**Date:** July 26, 2026  
**Reports reconciled** (filenames normalized on filing into this bundle; models unchanged):

1. `20260726-0054-01-aw-delivery-and-clean-delta.research-report.gpt56.md` (OpenAI/Codex)
2. `20260726-0054-02-aw-delivery-and-clean-delta.research-report.gemini36flash.md`
3. `20260726-0054-03-aw-delivery-and-clean-delta.research-report.gemini31pro.md`
4. `20260726-0054-04-aw-delivery-and-clean-delta.research-report.sonnet5.md`

**Purpose:** Identify where the reports agree, where they differ, what each omitted, which disputed claims are supported by current official documentation, and what a single reconciled architecture should retain.

## Executive synthesis

The four reports agree on the product direction:

- Clean-delta contribution is the primary requirement.
- The target repository’s tracked `.gitignore`, root `AGENTS.md`, and host-specific instruction files must remain untouched in clean-delta mode.
- Developer-created artifacts need a tracking home outside the upstream repository.
- A sibling repository is the clearest artifact-tracking location.
- `.git/info/exclude` is preferable to a tracked `.gitignore` when local in-repository files are unavoidable.
- Host-native skills are useful for at least some workflows.
- Clean-delta mode requires per-repository state outside tracked upstream content.
- Same-version reinstall should recognize an already-correct installation rather than rewriting it.
- Conservative ownership, edited-file preservation, and reversible uninstall must continue.
- Future downgrade should remain possible without implementing a downgrade command now.

The reports diverge primarily on five questions:

1. **Should locally excluded in-repository files be the primary discovery mechanism or only a fallback?**
2. **Which hosts currently support personal or global `SKILL.md` discovery, and at what paths?**
3. **Are persona, assessor, and dialogue runbooks unsuitable for skills, or can they be explicit-invocation skills?**
4. **Should clean-delta state live in an untracked target-repository manifest or entirely outside the target?**
5. **Are five retained backups enough to preserve arbitrary future downgrade?**

After verification against current official documentation, the reconciled answer is:

> Use consent-gated user-scope skills as the primary local discovery mechanism; use a developer-owned sibling repository for artifacts; keep the authoritative per-repository mapping in user-global agent-workflows configuration; maintain a separate global ownership manifest for shared user-scope host files; keep a recovery snapshot in the companion repository; and treat locally excluded project shims or skills as a host-tested fallback, not the baseline.

This is closest to the OpenAI/Codex report’s architecture, strengthened by Sonnet’s warning about hosts that suppress ignored files and by the Gemini reports’ more concrete workflow taxonomy and reverse-migration considerations.

The most important factual corrections are:

- Current official documentation does provide personal or global skill paths for OpenCode, Claude Code, Codex, GitHub Copilot local surfaces, Cursor, Antigravity, and Gemini CLI.
- Antigravity’s documented global path is `~/.gemini/config/skills/`, not `~/.gemini/antigravity-cli/skills/`.
- Codex’s documented user path is `$HOME/.agents/skills`, not `~/.codex/skills`, `~/.codex/agents`, or `~/.codex/instructions.md`.
- GitHub Copilot documents personal skills at `~/.copilot/skills` and `~/.agents/skills`.
- Cursor documents user skills at `~/.cursor/skills` and `~/.agents/skills`.
- Git ignore rules hide intentionally untracked files from ordinary Git operations, but they do not affect already tracked files and can be overridden by force-add. A clean `git status` is not by itself proof of a clean pull request.
- Cursor officially ignores `.gitignore`-matched content for indexing. Its treatment of `.git/info/exclude` is plausible but not explicitly documented, so excluded-file discovery still requires a direct test.
- Five rotating backups preserve recent undo, not arbitrary future downgrade.

## 1. Method and evidence standard

### 1.1 Comparison method

Each report was read in full and decomposed into claims in these categories:

- goal framing;
- clean-delta definition;
- primary architecture;
- host discovery;
- skills paths and behavior;
- ignored-file behavior;
- artifact routing;
- manifest and ownership location;
- workflow-to-skill suitability;
- migration;
- same-version reinstall;
- downgrade preservation;
- CLI design;
- phased implementation;
- open questions and acceptance criteria.

Claims were classified as:

- **Full agreement:** materially the same recommendation.
- **Partial agreement:** same direction but different scope or priority.
- **Direct divergence:** mutually incompatible recommendations or factual assertions.
- **Omission:** one report addressed a material issue another did not.
- **Internally inconsistent:** a report took conflicting positions in different sections.

### 1.2 Verification standard

Consequential host claims were checked against current official documentation. “Documented” means the official documentation available on July 26, 2026 expressly states the behavior. It does not mean agent-workflows has reproduced the behavior.

Where official documentation does not say whether a host discovers a file excluded only through `.git/info/exclude`, that remains an empirical question. A general statement that the host reads a directory does not establish ignored-file discovery.

### 1.3 Source-age problem

Some apparent model disagreement was actually evidence-age disagreement. OpenCode’s current skill page was updated July 24 or 25, 2026, and several other host documents now describe paths that the Sonnet report said it could not confirm. Those portions of the Sonnet report were appropriately cautious based on its retrieved sources, but they are no longer the best current answer.

## 2. High-level agreement matrix

| Topic | Gemini 3.6 Flash Medium | Gemini 3.1 Pro | Claude Sonnet 5 | OpenAI/Codex | Reconciled result |
|---|---|---|---|---|---|
| Clean-delta is primary | Yes | Yes | Yes | Yes | Full agreement |
| Fold low-footprint into clean-delta | Mostly | Yes | Yes, while preserving conceptual distinction | Mostly, but reframes secrecy claim | One implementation mode; document distinct motivations |
| Do not modify tracked `.gitignore` | Yes | Yes | Yes | Yes | Full agreement |
| Do not modify upstream `AGENTS.md` | Yes | Yes | Yes | Yes | Full agreement |
| Use sibling repository for artifacts | Yes | Yes | Yes, sometimes optional | Yes, required for tracked personal artifacts | Strong agreement; make it the normal clean-delta artifact home |
| Primary discovery | Global skills plus excluded fallback | Excluded in-repo files | Global skills plus excluded fallback | Global skills; excluded fallback only after testing | Divergence; skills-first wins on current evidence |
| `.git/info/exclude` | Primary/fallback and claimed proven | Primary | Important fallback with major discovery caveat | Experimental fallback | Use only when local target files are necessary |
| `core.excludesFile` | Too broad | Not developed | Do not have installer write it | Considered but not preferred | Installer should not modify it |
| Global skills exist broadly | Claimed for a subset, with wrong paths | Defer due fragmentation | Confirmed for four, denied or uncertain for others | Confirmed for all seven local host families | Current official docs support all seven local families |
| Skills should be selective | Yes | Yes | Yes | Yes | Full agreement |
| Persona/assessor workflows | Keep as harnesses, perhaps one wrapper skill | Poor fit; use bootstrap pointer | Poor fit; permanent shim track | Can be explicit-invocation skills after testing | Do not create one skill per lens; use explicit harness skills or host adapters |
| Mode stored outside tracked upstream content | Yes | Yes | Yes | Yes | Full agreement |
| Authoritative mode location | Global config or untracked manifest | Global config | Untracked in-target manifest | Global config plus companion recovery snapshot | Global config is authoritative |
| Separate global skill ownership | Implied, not fully designed | Omitted | Yes, with references | Yes | Required |
| Same-version install | Reconcile and report | Silent no-op | Visible no-op; warn on drift | Visible verified no-op; explicit repair | OpenAI/Codex and Sonnet are strongest |
| Per-file installed version | Yes | No | Yes | Yes | Add it |
| Five backups preserve downgrade | Says yes | Says yes | Only recent versions | Only recent versions | Backups alone are insufficient |
| Conformance harness before delivery | Open questions, but build excludes first | Test later | Test high-risk hosts, but build A first | Phase 0 before relying on host behavior | Build the harness first |
| Remote/cloud distinction | Largely omitted | Omitted | Partially addressed | Explicit | Must be explicit |
| Acceptance criteria | Limited | Minimal | Open questions | Detailed 15-point list | Retain and extend detailed criteria |

## 3. Where all four reports agree

### 3.1 Clean-delta is the real driver

Every report treats clean-delta contribution as the strongest and most objectively testable requirement. All agree that a developer should be able to use agent-workflows while contributing to an upstream repository without placing agent-workflows content in the pull request.

The reports use slightly different language:

- Gemini 3.6 calls it the “core architectural driver.”
- Gemini 3.1 calls inability to avoid PR pollution a foundational adoption flaw.
- Sonnet calls clean-delta “the real product.”
- OpenAI/Codex defines it as a precise property of the index, branch diff, and pull request.

The OpenAI/Codex definition is the most operationally complete because it does not equate a clean working tree with a clean pull request. The reconciled definition should be:

> The target repository’s index, branch diff against the relevant upstream merge base, and proposed pull request contain only the developer’s genuine contribution. No agent-workflows file, managed block, ignore rule, manifest, instruction edit, backup, or generated artifact appears in that delta.

### 3.2 Tracked target instruction and ignore files must remain untouched

All four agree that clean-delta mode must not:

- edit the target’s tracked `.gitignore`;
- insert an agent-workflows pointer into root `AGENTS.md`;
- mirror a pointer into tracked `CLAUDE.md` or `GEMINI.md`;
- commit generated host shims;
- commit the current per-repository ownership manifest.

This is the clearest point of consensus.

### 3.3 Developer artifacts need physical separation

All four reports reject keeping personal plans, prompts, research, and run records only as ignored files in the upstream repository if the user wants them versioned.

They converge on a sibling repository such as:

```text
../opencode.aw/
```

The companion repository provides:

- developer-controlled Git history;
- a separate remote if desired;
- a place for lifecycle moves;
- a clean audit trail for plans and run records;
- no relationship to the upstream pull request.

Gemini 3.1 and Sonnet treat sibling artifact routing as secondary to locally excluded framework files. Gemini 3.6 and OpenAI/Codex more strongly integrate the companion into the architecture. The reconciled design should make a companion repository the standard artifact home whenever the user requests their artifacts to remain tracked.

### 3.4 Per-class tracking should be expressed through location

All reports are skeptical of complex per-class ignore machinery. They differ on whether to extend `local/` lanes or route whole classes externally, but they agree that physical path should determine tracking behavior.

The strongest shared principle is:

> The directory to which a workflow writes expresses whether that artifact is tracked and by which repository.

This should remain the design rule. A routing table is clearer than new suffix conventions and managed ignore blocks.

### 3.5 Same-version installation should be detected

All four agree that reinstalling the exact same version should not rewrite correct files.

They differ only on presentation and drift handling:

- Gemini 3.1 prefers a silent no-op.
- Gemini 3.6 prefers reconciliation and a concise status.
- Sonnet prefers a visible no-op and warnings only for inconsistency.
- OpenAI/Codex distinguishes verified no-op, missing files, edited files, changed configuration, and absent manifests.

The reconciled behavior should use the OpenAI/Codex state table:

| State | Result |
|---|---|
| Same version, manifest present, hashes and routes match | Visible verified no-op, exit 0 |
| Managed file missing | Report drift; recreate only with `--repair` or confirmation |
| Managed file edited | Preserve and report |
| Configuration changed | Show and reconcile only requested configuration |
| Manifest absent | Inspect and require explicit adoption or clean installation |

### 3.6 Global host mutations require ownership discipline

Gemini 3.6, Sonnet, and OpenAI/Codex explicitly recognize that writing to a shared user skills directory creates a new ownership scope. Gemini 3.1 largely omits it.

The agreed requirements are:

- explicit consent before writing global host files;
- hashes for files last written by agent-workflows;
- edited-file preservation;
- no deletion of unrecognized same-named files;
- awareness that several repositories may depend on one global installation.

This requires a global ownership manifest separate from any target-repository manifest.

## 4. Primary architecture divergence

### 4.1 Gemini 3.1: excluded in-repository framework first

Gemini 3.1 recommends a “phantom installation”:

- write `.agents/`, shims, and a manifest into the target checkout;
- exclude them using `.git/info/exclude`;
- route artifacts to a sibling repository;
- defer broad skills work.

Benefits:

- minimal change from the current installer;
- familiar paths remain;
- explicit local files can be inspected;
- target Git output is ordinarily clean.

Weaknesses:

- the target checkout is not actually footprint-free;
- force-add can expose the files;
- an upstream update can introduce the same path and create collisions;
- files already tracked are not affected by ignore rules;
- discovery by hosts that suppress ignored files is unproven;
- the per-clone state disappears on reclone;
- a local target manifest can be lost with the checkout;
- it does not solve cloud execution.

The architecture is a plausible fallback, but not a safe universal baseline.

### 4.2 Sonnet: skills first where proven, excluded shims as a permanent second track

Sonnet recommends:

- global skills for skill-shaped workflows;
- locally excluded shims and manifest for persona/dialogue workflows and unsupported hosts;
- sibling repository for developer artifacts;
- global manifest for user skill ownership.

This is much closer to the final architecture. Its most valuable contribution is the warning that excluded-file discovery may fail when a host uses Git ignore state for indexing or awareness.

Its main weakness is source incompleteness. It incorrectly concluded that:

- Copilot lacked personal skills;
- Codex’s user path was unresolved;
- Antigravity’s global path was unconfirmed.

Current official documentation resolves all three.

### 4.3 Gemini 3.6: composite model with excessive certainty

Gemini 3.6 recommends a broad composition of:

- sibling repository;
- global skills;
- `.git/info/exclude` fallback;
- global per-repository config.

Architecturally, this resembles the reconciled result. The problem is evidentiary overreach. It labels several host behaviors “proven” without presenting reproducible evidence and gives multiple incorrect paths.

The report is useful as an implementation sketch, but its host matrix cannot be treated as authoritative.

### 4.4 OpenAI/Codex: clean separation of discovery, routing, state, and ownership

The OpenAI/Codex report recommends:

- user-scope skills for discovery;
- companion repository for developer artifacts;
- user-global per-repository mapping;
- separate global ownership manifest;
- companion recovery state;
- no target manifest or target file in the baseline;
- locally excluded project files only as a tested fallback;
- conformance harness before host promises.

This architecture has the fewest cross-couplings and the strongest uninstall model. It also most directly addresses the hard problem: the target no longer needs a pointer because the host’s user skill is the discovery path.

Its principal omission is that it did not emphasize enough that Cursor’s official ignore behavior makes Candidate A riskier than a generic “not documented” label suggests.

### 4.5 Reconciled architecture

The reconciled architecture should use:

```text
User-scope host skill
    -> agent-workflows resolver
    -> packaged workflow or harness
    -> target repository as code context
    -> companion repository as artifact root
```

Scopes:

```text
Target repository
    genuine code changes only

Companion repository
    tracked plans, prompts, research, runs, lifecycle state snapshot

User-global agent-workflows config
    authoritative target-to-companion mapping and mode

User-global ownership manifest
    ownership of global skills and other host files

Package installation
    canonical workflow bodies and resolver executable
```

Locally excluded project shims or skills are allowed only after an exact host/version test demonstrates discovery and only when a host-specific requirement remains.

## 5. Host discovery claims: report comparison and verified resolution

### 5.1 Verified current host matrix

| Host | Verified project skill paths | Verified user/global skill paths | Important limitation |
|---|---|---|---|
| OpenCode | `.opencode/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.config/opencode/skills/`, `~/.claude/skills/`, `~/.agents/skills/` | Ignored project-skill discovery is not documented |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` | Local personal skills do not automatically transfer to Cowork or cloud sessions |
| Codex | `.agents/skills/` from CWD upward to repo root | `$HOME/.agents/skills` | Local discovery does not establish cloud-environment availability |
| GitHub Copilot local surfaces | `.github/skills/`, `.claude/skills/`, `.agents/skills/` | `~/.copilot/skills`, `~/.agents/skills` | Official docs list cloud consumers too, but do not state that a workstation’s personal directory is synchronized to them |
| Cursor | `.agents/skills/`, `.cursor/skills/`, plus compatibility paths | `~/.agents/skills`, `~/.cursor/skills`, plus compatibility paths | `.gitignore` content is ignored for indexing; `.git/info/exclude` equivalence needs testing |
| Antigravity | `<workspace-root>/.agents/skills/` | `~/.gemini/config/skills/` | Do not confuse this with Gemini CLI’s user path |
| Gemini CLI | `.gemini/skills/`, `.agents/skills/` | `~/.gemini/skills/`, `~/.agents/skills/` | Skill activation includes a consent step |

Official sources:

- [OpenCode Agent Skills](https://opencode.ai/docs/skills/)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Codex Skills](https://developers.openai.com/codex/skills)
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Antigravity Skills](https://antigravity.google/docs/skills)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)

### 5.2 OpenCode

#### Report positions

- Gemini 3.6 correctly identifies `~/.config/opencode/skills`, but overstates ignored-shim and external-path behavior as proven.
- Gemini 3.1 mentions OpenCode only generally and provides no exact current path matrix.
- Sonnet accurately identifies OpenCode’s project and user skill paths and correctly marks ignored-file discovery unproven.
- OpenAI/Codex provides the fullest path and precedence analysis.

#### Resolution

User-scope skills are documented and should be the primary OpenCode clean-delta discovery mechanism. The global `instructions` setting can load external instruction files, but it is an always-on mechanism and should not replace on-demand skills unless a genuine always-on requirement remains.

Do not claim that `.git/info/exclude` project shims are discovered until reproduced.

### 5.3 Claude Code

#### Report positions

- All four recognize `~/.claude/skills`.
- Gemini 3.6 claims locally excluded project skills and commands are proven.
- Gemini 3.1 assumes physical presence is enough.
- Sonnet raises the strongest ignored-file awareness concern.
- OpenAI/Codex identifies `CLAUDE.local.md`, external imports, `--add-dir` skill discovery, and cloud limitations.

#### Resolution

Use personal `~/.claude/skills` for local clean-delta discovery. Claude Code also documents that `.claude/skills` inside a directory supplied through `--add-dir` is automatically loaded, making the companion repository a viable host-specific discovery source if the user accepts a modified launch command.

Do not infer that locally excluded project skills are passively discovered. Claude’s documented `CLAUDE.local.md` mechanism is positive evidence for ignored local instruction files, but it does not prove every ignored skill path.

Cloud and Cowork sessions do not read the workstation’s `~/.claude/skills`. That limitation was omitted by the Gemini reports and only partially addressed by Sonnet.

### 5.4 Codex

#### Report positions

- Gemini 3.6 incorrectly lists `~/.codex/instructions.md` for global instructions and does not give the current documented skills path.
- Gemini 3.1 does not provide a verified path.
- Sonnet reports conflicting third-party paths and therefore treats global skills as unproven.
- OpenAI/Codex uses the current official documentation.

#### Resolution

Codex documents:

- repository skills under `.agents/skills` from CWD to repository root;
- user skills under `$HOME/.agents/skills`;
- administrator skills under `/etc/codex/skills`;
- global instructions under `~/.codex/AGENTS.md`, not `~/.codex/instructions.md`.

This is a strong zero-target-footprint path for local Codex use.

### 5.5 GitHub Copilot and VS Code

#### Report positions

- Gemini 3.6 treats Copilot skills and external paths as weak or unresolved and relies on settings.
- Gemini 3.1 treats local VS Code settings as the main route.
- Sonnet says no personal skill path was found.
- OpenAI/Codex documents current personal paths but distinguishes local from cloud.

#### Resolution

Current GitHub documentation expressly lists:

- project skills at `.github/skills`, `.claude/skills`, and `.agents/skills`;
- personal skills at `~/.copilot/skills` and `~/.agents/skills`;
- consumers including Copilot cloud agent, code review, CLI, app, and VS Code agent mode.

The safe conclusion is narrower than “personal skills work everywhere.” The documentation does not say that a local home-directory skill is synchronized into GitHub’s remote cloud execution environment. Therefore:

- personal skills are a valid local Copilot route;
- remote cloud availability remains an open question;
- `.git/info/exclude` cannot help a remote clone because the local exclude file is not present there.

### 5.6 Cursor

#### Report positions

- Gemini 3.6 calls excluded `.cursor/rules` discovery proven and out-of-repository access restricted.
- Gemini 3.1 assumes local files are reliable.
- Sonnet cites Cursor ignore behavior and predicts excluded project files may be suppressed.
- OpenAI/Codex documents user skills but merely labels exclude interaction “not documented.”

#### Resolution

Cursor officially documents:

- user skills at `~/.cursor/skills` and `~/.agents/skills`;
- project skills at `.cursor/skills` and `.agents/skills`;
- compatibility with Claude and Codex skill paths;
- automatic ignoring of `.gitignore`-matched content for indexing.

Cursor’s documentation does not explicitly say whether `.git/info/exclude` is processed identically, although its troubleshooting advice uses `git check-ignore`, which makes equivalence plausible. Sonnet’s risk assessment is therefore directionally correct but not fully proven.

The reconciled stance:

- use user skills;
- do not build the baseline around excluded project rules;
- directly test `.git/info/exclude` before offering that fallback.

### 5.7 Antigravity

#### Report positions

- Gemini 3.6 gives incorrect paths such as `~/.gemini/antigravity-cli/skills` and `.gemini/skills`.
- Gemini 3.1 gives no verified path.
- Sonnet says global scope was not confirmed.
- OpenAI/Codex gives the current official paths.

#### Resolution

Antigravity’s current official documentation gives:

- workspace: `<workspace-root>/.agents/skills/<skill-folder>/`;
- global: `~/.gemini/config/skills/<skill-folder>/`.

It also says `.agent/skills` remains backward-compatible.

The global path is now documented and should be treated as available for the documented Antigravity version, subject to reproduction before the installer advertises support.

### 5.8 Gemini CLI

#### Report positions

All reports that discuss Gemini CLI recognize a user-level mechanism, though Gemini 3.6 conflates some Antigravity and Gemini paths.

#### Resolution

Gemini CLI documents:

- workspace skills at `.gemini/skills` or `.agents/skills`;
- user skills at `~/.gemini/skills` or `~/.agents/skills`;
- workspace precedence over user skills;
- explicit activation consent;
- link, install, list, reload, enable, disable, and uninstall commands.

This is one of the best-documented clean-delta hosts for local use.

## 6. The `.git/info/exclude` disagreement

### 6.1 What Git guarantees

Git documentation guarantees:

- `.git/info/exclude` is appropriate for per-clone patterns that should not be shared;
- `core.excludesFile` is intended for user-global ignore patterns;
- ignore rules apply to intentionally untracked files;
- already tracked files are not affected.

Ordinary `git status` and `git add` respect ignore rules. However:

- `git add -f` can force-add ignored files;
- ignore rules do not erase files already in the index;
- an earlier commit containing agent-workflows content remains in the branch history;
- an upstream repository may later add a path that collides with the local ignored path;
- a clean working tree is not sufficient proof of a clean PR.

Gemini 3.1’s assertion that Git becomes “entirely blind” and the files “will never accidentally enter a PR” is therefore too strong. Gemini 3.6 and Sonnet make similar structural-guarantee claims in places. The correct wording is:

> `.git/info/exclude` prevents ordinary Git status and add behavior from surfacing intentionally untracked local files. It reduces accidental inclusion but does not make inclusion impossible and does not affect tracked or previously committed content.

### 6.2 What hosts may do

The reports split sharply:

- Gemini 3.6 labels discovery “proven” for several hosts.
- Gemini 3.1 assumes raw filesystem visibility.
- Sonnet warns that host indexing may respect Git ignore state.
- OpenAI/Codex declines to infer behavior without tests.

The reconciled conclusion is:

- Sonnet identified the right risk.
- OpenAI/Codex applied the right evidence standard.
- Gemini 3.6 and Gemini 3.1 overclaimed.

### 6.3 `.git/info/exclude` versus `core.excludesFile`

Gemini 3.6 and Sonnet correctly argue that `.git/info/exclude` is the safer local ignore home.

The reconciled recommendation is stronger:

- The installer may manage a clearly marked section of `.git/info/exclude` in a fallback mode.
- The installer should not write agent-workflows repository paths into `core.excludesFile`.
- User-global ignore modification changes Git behavior in unrelated repositories and creates collision risk with repositories that legitimately track `.agents`, `.claude`, `.cursor`, or similar paths.

## 7. Which workflows belong in skills

### 7.1 Agreement

All reports reject mechanical conversion of every workflow into a separate skill.

They broadly agree that these are strong candidates:

- release review;
- plan review;
- verification;
- scaffold;
- specification;
- setup or getting-started procedures;
- bounded research or assessment procedures.

### 7.2 Persona and assessor disagreement

Gemini 3.6, Gemini 3.1, and Sonnet characterize `advise`, `assess`, and persona or lens workflows as poor skill fits. OpenAI/Codex is more permissive and recommends explicit invocation plus testing.

Current host behavior supports a middle position:

- Claude Code and Cursor expressly support disabling model invocation, which makes a skill behave like an explicit slash command.
- Claude Code says custom commands and skills are converging and can carry complex procedures and supporting resources.
- Antigravity and Gemini skills can bundle scripts and references.
- Copilot skills can include scripts, examples, and other resources.

Therefore, complexity and multi-file composition do not categorically disqualify a workflow from being a skill.

The real problems are:

- auto-trigger false positives;
- registry explosion if every persona or lens becomes a separate skill;
- host-specific invocation controls;
- parameter portability;
- sustained conversational behavior after activation;
- lifecycle and artifact-root access.

### 7.3 Reconciled skill taxonomy

Use three forms:

#### Portable capability skills

One skill per high-frequency bounded capability:

- `plan-review`;
- `release-review`;
- `verify`;
- `scaffold`;
- `spec`.

#### Explicit harness skills

One skill per harness, not per persona or lens:

- `advise <persona>`;
- `assess <lens>`;

The skill resolves and loads the selected packaged persona or lens. On hosts that support an explicit-invocation flag, disable automatic invocation. On other hosts, use a narrow description and test trigger behavior.

#### Non-skill always-on guidance

Only concise, genuinely universal instructions should enter user rules or global instruction files. Do not place the whole workflow catalog there.

This preserves the Gemini reports’ concern about registry explosion while accepting the OpenAI/Codex point that explicit skills can replace many command shims.

## 8. State and manifest location

### 8.1 Report positions

- Gemini 3.6 recommends user-global config or a locally excluded target manifest.
- Gemini 3.1 recommends user-global config.
- Sonnet recommends the untracked in-target manifest as authoritative.
- OpenAI/Codex recommends three scopes: user-global mapping, global ownership manifest, and companion recovery state.

### 8.2 Evaluation

An in-target untracked manifest has one advantage: it stays physically near the files it owns.

It has several weaknesses:

- it disappears with the clone;
- it still creates target-checkout footprint;
- it is not available if the clean-delta design uses no target files;
- it cannot own shared global skill files cleanly;
- it is a poor authoritative source when the target moves;
- it does not solve cross-repository reference counting.

The user-global config already exists, honors XDG, and is the only location common to zero-target-file mode.

### 8.3 Reconciled state model

Use:

1. **User-global config:** authoritative per-repository choice, target path identity, companion path, artifact routes, enabled hosts.
2. **Global ownership manifest:** exact global host files, hashes, source versions, source revision when required, and dependent repositories.
3. **Companion state:** versioned recovery snapshot and human-readable effective policy.
4. **Normal tracked-mode target manifest:** retain the existing tracked manifest only for repositories that intentionally adopt agent-workflows.
5. **Fallback local target manifest:** only if a host-specific excluded-project-file mode actually installs target files. It is then a cache or ownership aid, not the only authoritative mapping.

## 9. Artifact routing and lifecycle

### 9.1 Shared recommendation

All four reports endorse moving personal artifacts outside the target and retaining lifecycle history in a developer-controlled repository.

### 9.2 Important omission in three reports

The original workflow convention instructs agents to perform plan lifecycle moves and, in some cases, commit artifacts. Once artifacts move to a companion repository, every workflow must know which repository receives:

- file creation;
- `git mv`;
- `git status`;
- artifact-only commits;
- never-push instructions.

The OpenAI/Codex report addresses this most directly with an `artifact_root` resolver and an explicit rule that artifact commits occur in the companion, not the target. The other reports show the intended result but do not fully specify a common resolver contract.

### 9.3 Reconciled resolver

Provide a deterministic command:

```bash
agent-workflows context --repo "$PWD" --json
```

It should return:

- canonical target root;
- install mode;
- companion root;
- per-class routes;
- effective framework version;
- enabled host integration;
- whether the current command may commit in the target, companion, neither, or both.

Every producing workflow should call the resolver instead of parsing config independently.

## 10. Migration reconciliation

### 10.1 Tracked to clean-delta

All reports treat this as a migration, but their mechanics differ.

- Gemini 3.6 removes tracked shims and managed blocks, then moves artifacts.
- Gemini 3.1 proposes `git rm --cached -r .agents/`.
- Sonnet calls for explicit migration and a dry-run preview.
- OpenAI/Codex uses the existing manifest and conservative uninstall rules, preserving edited files and refusing to declare success until the branch diff is clean.

The reconciled procedure:

1. Require an explicit `migrate --to-clean-delta` or `install --clean-delta --migrate` action.
2. Show a dry-run.
3. Read the existing manifest.
4. Create and validate the companion before removing anything.
5. Copy or move personal artifacts to the companion.
6. Install and test user skills.
7. Remove only unedited installer-owned target files and managed blocks.
8. Preserve edited files and stop for user resolution.
9. Do not add tracked ignore changes.
10. Examine the index and branch diff against upstream.
11. If agent-workflows content was committed on the contribution branch, do not assume a new removal commit produces the desired clean PR. The branch may need an interactive rebase, commit amendment, or clean cherry-pick onto a fresh branch, depending on history.
12. Record completion in user-global and companion state.

An unconditional `git rm --cached` is too broad and may remove user-owned or upstream-owned files. Use manifest ownership and exact paths.

### 10.2 Clean-delta to tracked

Gemini 3.6 is the only report to describe the reverse direction explicitly.

The reverse migration should:

1. require explicit confirmation;
2. verify the target has no path conflicts;
3. render current in-repo workflows and host shims;
4. add managed instruction and ignore blocks only where the user selected them;
5. write the tracked per-repository manifest last;
6. preserve the companion repository unless the user explicitly changes artifact routing;
7. remove fallback `.git/info/exclude` entries only after target ownership is established;
8. leave global skills installed if other repositories depend on them.

This is a worthwhile addition to the reconciled design.

## 11. Same-version reinstall reconciliation

Gemini 3.1’s silent no-op is too quiet because it hides whether the installer actually verified state. Gemini 3.6’s “reconcile silently” language risks automatic restoration of files the user deliberately removed. Sonnet and OpenAI/Codex are more conservative.

The reconciled behavior:

- verified correct state: one-line no-op;
- drift: report exact differences;
- missing file: require repair;
- edited file: preserve;
- unmanaged same-named global skill: do not adopt or overwrite automatically;
- changed routing: show the requested transition;
- absent manifest: explicit adoption only.

## 12. Downgrade preservation reconciliation

### 12.1 Report positions

- Gemini 3.6 says timestamped backups provide full-state restore and recommends per-file version, hash, and timestamp.
- Gemini 3.1 says top-level installed version plus backups is sufficient.
- Sonnet says backups cover only the retained recent history and recommends per-file installed version.
- OpenAI/Codex says backups alone are insufficient for arbitrary future downgrade and recommends per-file source version, installed hash, transaction provenance, and optional source revision.

### 12.2 Resolution

The existing five-backup retention cannot preserve arbitrary downgrade. The needed backup may be deleted after six installations. A backup also does not by itself identify a coherent released source version unless its transaction metadata says so.

Record:

- effective top-level version;
- per-file source version;
- per-file installed hash;
- transaction ID;
- from-version and to-version;
- source revision only for development snapshots or mutable sources;
- backup path and retention status.

Backups remain useful for exact recent undo. Future downgrade should re-render an immutable older package version through the same conservative transaction engine. No downgrade command is required now.

## 13. CLI and mode naming

### 13.1 Report positions

- Gemini 3.6 suggests `--clean-delta`, `--tracked`, and `--sibling`.
- Gemini 3.1 suggests `--phantom` or `--clean-delta`.
- Sonnet accepts `--clean-delta`, `--no-track`, or `--deep`.
- OpenAI/Codex recommends only `--clean-delta`, rejects ambiguous `--no-track`, and rejects `--deep`.

### 13.2 Resolution

Use:

```text
agent-workflows install --clean-delta
agent-workflows install --clean-delta --artifact-repo PATH
agent-workflows migrate --to-clean-delta
agent-workflows migrate --to-tracked
agent-workflows verify-clean-delta
```

Do not use:

- `--deep`, which has no semantic relationship to tracking;
- `--no-track`, which does not say where artifacts go;
- `--phantom`, which is memorable but less precise and can imply concealment beyond what the tool can promise.

Interactive selection is useful when no mode flag is given, but automation must be fully flag-driven.

## 14. Phased implementation reconciliation

### 14.1 What the reports proposed

- Gemini 3.6 builds `.git/info/exclude` and sibling routing first, skills second.
- Gemini 3.1 builds phantom mode first, sibling routing second, skills last.
- Sonnet builds excluded shims and manifest first, then proven global skills.
- OpenAI/Codex builds a conformance harness and artifact-root abstraction before host delivery.

### 14.2 Reconciled sequence

#### Phase 0: conformance harness

Build exact host/version tests for:

- user skill discovery;
- explicit invocation;
- automatic invocation;
- precedence and same-name collision;
- `.git/info/exclude` project-file discovery;
- sibling read and write access;
- cloud versus local availability;
- uninstall and edited-file preservation.

#### Phase 1: artifact-root and state abstraction

Build:

- per-repository global config;
- companion repository mapping;
- resolver command;
- per-class route handling;
- lifecycle and commit-target updates;
- global ownership manifest;
- clean-delta verification.

#### Phase 2: portable user skills

Package a small, tested subset:

- `plan-review`;
- `release-review`;
- `verify`;
- `scaffold`;
- `spec`;
- optionally `advise` and `assess` as explicit harness skills.

Target the documented user paths for each host.

#### Phase 3: clean-delta install and migration

Implement:

- transactional zero-target-write install;
- explicit migration in both directions;
- companion preservation;
- global skill dependency tracking;
- same-version verified no-op;
- recent undo metadata.

#### Phase 4: fallback project adapters

Only after direct evidence, add:

- locally excluded project skills;
- locally excluded command shims;
- Claude `--add-dir` integration;
- Antigravity global workflows if their storage and ownership contract is stable;
- other host-specific adapters.

This sequence avoids building the riskiest mechanism first.

## 15. Unique contributions and omissions by report

### 15.1 Gemini 3.6 Flash Medium

#### Strong contributions

- Clear executive recommendation and readable architecture diagrams.
- Concrete workflow taxonomy, including more actual workflow names than the other reports.
- Explicit reverse migration from clean-delta to tracked mode.
- Strong endorsement of global config for per-repository mapping.
- Recognition that artifact history belongs in a sibling repository.
- Useful end-to-end example showing plan lifecycle and companion commits.

#### Material inaccuracies or overstatements

- Incorrect Antigravity global path: `~/.gemini/antigravity-cli/skills/`.
- Incorrect Antigravity project path: `.gemini/skills/`.
- Incorrect Codex global instruction path: `~/.codex/instructions.md`.
- Unsupported “proven” labels for ignored-file discovery and out-of-repository reads.
- Overstates Candidate B as proven for tool-calling agents.
- Says the last five backups provide complete future restore capability.
- Suggests silent reconciliation that could recreate deliberately removed files.

#### Omissions

- Local versus cloud execution boundary.
- Correct Copilot personal skill paths.
- Correct Codex user skill path.
- Shared global-skill dependency/reference handling in enough detail.
- Force-add, tracked-file, and prior-commit limitations of ignore rules.
- Branch-diff acceptance criteria.
- Exact companion-path identity and move recovery.

### 15.2 Gemini 3.1 Pro

#### Strong contributions

- Very concise identification of the core product problem.
- Strong physical-separation principle for tracked and untracked artifacts.
- Clear warning about WSL or host/VM filesystem boundaries.
- Correct preference for user-global mode configuration.
- Correct rejection of tracked `.gitignore` changes.

#### Material inaccuracies or overstatements

- Treats `.git/info/exclude` as making Git “entirely blind.”
- Assumes hosts read excluded files simply because they exist on disk.
- Describes `SKILL.md` schemas as too fragmented, which is not consistent with the current Agent Skills standard and current host documentation.
- Suggests `.agents/AGENTS.md` as a discovery artifact without establishing that hosts read it.
- Recommends unconditional `git rm --cached -r .agents/`, which may exceed manifest ownership.
- Treats five backups as sufficient for future revert.
- Recommends silent same-version no-op without proving state verification to the user.

#### Omissions

- Exact host-by-host skill paths.
- Official citations and version dates.
- Copilot, Codex, Antigravity, and Gemini current skill details.
- Cloud/local distinction.
- Global skill ownership manifest and multi-repository references.
- Reverse migration.
- Companion recovery state.
- Artifact resolver contract.
- Clean-delta branch-diff verification.
- Detailed acceptance criteria.

### 15.3 Claude Sonnet 5

#### Strong contributions

- Best critique of the assumption that Git-ignored files remain discoverable to the host.
- Correct warning that `.git/info/exclude` and `.gitignore` may be equivalent from a Git-aware host’s perspective.
- Best explanation of why manual “read and execute” prompts are unwieldy.
- Strong global ownership and multi-repository reference-count analysis.
- Correct visible no-op and drift-warning behavior.
- Correct conclusion that five backups cover only recent versions.
- Valuable distinction between clean-delta as a binary property and low-footprint as a spectrum.
- Good recommendation for an explicit migration dry-run.

#### Material inaccuracies or outdated conclusions

- Says GitHub Copilot has no documented personal skill path. Current docs list `~/.copilot/skills` and `~/.agents/skills`.
- Says Codex’s global skill path is unresolved. Current official docs list `$HOME/.agents/skills`.
- Says Antigravity global skills are unconfirmed. Current official docs list `~/.gemini/config/skills`.
- Treats persona/dialogue workflows as permanently requiring shims, overlooking explicit-invocation skill controls.
- Claims host-specific fields are generally documented as ignored by other hosts. OpenCode says this explicitly, but it is not a universal contract.
- Says the sibling artifact location does not create a host dependency because the host need not follow it. Producing, moving, and committing artifacts still require host access.
- In one place says global skill installation is consent-gated per repo; elsewhere says once per machine. The distinction should be: consent for shared installation is machine-scoped, while per-repository dependency registration is repo-scoped.

#### Omissions

- Current official paths that became available or were missed.
- A fully external target-to-companion mapping architecture.
- Path identity and repository-move recovery.
- Verification that prior commits do not pollute the PR.
- Detailed acceptance criteria.
- A clean zero-target-file baseline for non-skill content.
- Reverse migration from clean-delta to tracked.

### 15.4 OpenAI/Codex

#### Strong contributions

- Most complete current official host-path matrix.
- Strongest separation of discovery, artifacts, routing, and ownership.
- Best three-scope state model.
- Best local versus cloud distinction.
- Best artifact-root resolver and lifecycle-commit analysis.
- Best same-version state table.
- Best future-downgrade provenance model.
- Best conformance-harness-first sequencing.
- Only report with detailed acceptance criteria and branch-diff verification.
- Correctly rejects ambiguous mode names.

#### Weaknesses or areas underemphasized

- Did not give enough weight to Cursor’s official `.gitignore` indexing behavior when assessing excluded project files.
- Did not describe reverse migration to tracked mode as explicitly as Gemini 3.6.
- Could have distinguished more clearly between machine-level consent to install a shared skill and per-repository registration of dependency on it.
- Its initial curated skill list was cautious but did not fully connect to the actual larger workflow taxonomy supplied by Gemini 3.6.
- It did not explore the WSL/host filesystem boundary highlighted by Gemini 3.1.
- It could have stated more forcefully that the installer should never write repo-specific patterns into `core.excludesFile`.
- It could have specified an explicit migration dry-run command.

## 16. Consolidated claim ledger

| Claim | G3.6 | G3.1 | Sonnet 5 | OpenAI/Codex | Reconciled verdict |
|---|---:|---:|---:|---:|---|
| Clean-delta should be a named mode | Yes | Yes | Yes | Yes | Adopt `--clean-delta` |
| Target tracked `.gitignore` must remain unchanged | Yes | Yes | Yes | Yes | Correct |
| Upstream `AGENTS.md` must remain unchanged | Yes | Yes | Yes | Yes | Correct |
| Sibling repository should hold tracked personal artifacts | Yes | Yes | Yes | Yes | Correct |
| Framework should remain physically in target by default | Sometimes | Yes | Yes for fallback | No | Reject as baseline |
| `.git/info/exclude` makes target files safe from all PR inclusion | Implied | Yes | Nearly | No | False; it reduces ordinary inclusion only |
| Installer should modify `core.excludesFile` | No | Not stated | No | Not preferred | Do not modify |
| User skills exist for OpenCode | Yes | Implied | Yes | Yes | Documented |
| User skills exist for Claude Code | Yes | Yes | Yes | Yes | Documented |
| User skills exist for Codex | Incomplete | Unclear | Says unresolved | Yes | Documented at `$HOME/.agents/skills` |
| User skills exist for Copilot | Says weak | No detail | Says no | Yes | Documented locally |
| User skills exist for Cursor | GUI focus | No detail | Yes | Yes | Documented |
| Global skills exist for Antigravity | Yes, wrong path | No detail | Says unconfirmed | Yes | Documented at `~/.gemini/config/skills` |
| User skills exist for Gemini CLI | Yes | No detail | Yes | Yes | Documented |
| Local user skills automatically work in cloud sessions | Implied | Omitted | Cautious | No | Not generally established |
| Every workflow should become a separate skill | No | No | No | No | Correct rejection |
| Persona workflows cannot be skills | Mostly | Yes | Yes | No | Too categorical |
| One harness skill with parameters is viable | Yes | Bootstrap only | Not developed | Yes | Recommended after tests |
| Clean-delta mode belongs in user-global config | Yes | Yes | No | Yes | Majority and architecture favor global config |
| Untracked target manifest should be authoritative | Optional | No | Yes | No | Reject as sole authority |
| Shared global skills need separate ownership | Partial | No | Yes | Yes | Required |
| Global skill uninstall needs dependent-repo awareness | Omitted | Omitted | Yes | Yes | Required |
| Same-version correct install should be silent | No | Yes | No | No | Use visible verified no-op |
| Drift should auto-repair | Yes | Unclear | No | No | Require explicit repair |
| Five backups preserve arbitrary downgrade | Yes | Yes | No | No | False |
| Per-file source version should be recorded | Yes | No | Yes | Yes | Record it |
| Install commit ID is always needed | No | No | No | No | Only source revision for nonimmutable builds |
| Conformance tests should precede host claims | Partial | Later | Yes for disputes | Yes | Required Phase 0 |
| Reverse migration should be supported | Yes | No | No | Implicit | Add explicitly |
| Clean PR verification must compare merge-base diff | No | No | No | Yes | Required |

## 17. Final reconciled recommendation

### 17.1 Product modes

Keep two coherent modes:

- **Tracked mode:** current shared-repository adoption model, with tracked per-repository manifest, shims where needed, and managed instruction blocks.
- **Clean-delta mode:** no tracked or baseline local agent-workflows files in the target; user skills for discovery; companion repository for artifacts; global config and ownership state.

Do not expose independent low-level toggles that can create incoherent combinations such as an untracked manifest with tracked shims.

### 17.2 Clean-delta installation

1. Resolve and record target identity.
2. Create or select the companion repository.
3. Register artifact routes in user-global config.
4. Install consent-gated user skills at documented host paths.
5. Record global ownership and dependent repositories.
6. Validate skill discovery and companion access.
7. Verify the target index and merge-base diff are unchanged.
8. Write a recovery snapshot in the companion.

### 17.3 Use

1. The upstream repository’s own instruction files load normally.
2. The user invokes an agent-workflows skill.
3. The skill calls the resolver.
4. The resolver returns target and artifact roots.
5. Code work occurs in the target.
6. Plans, research, prompts, and run records occur in the companion.
7. Artifact lifecycle moves and commits occur in the companion.
8. Code commits occur in the target only when explicitly part of the requested development task.

### 17.4 Fallback

Use a locally excluded project shim or skill only when:

- the host lacks a usable user-scope mechanism for the needed workflow or surface;
- an exact host/version test demonstrates the ignored file remains discoverable or explicitly invocable;
- the user accepts local target-checkout footprint;
- uninstall ownership is recorded outside tracked upstream content.

### 17.5 Cloud boundary

Label the initial feature **local clean-delta**. Do not imply that workstation skills, sibling paths, or `.git/info/exclude` state transfer into a remote cloud clone.

Remote clean-delta needs its own design, possibly involving:

- account-synchronized skills;
- remote environment bootstrap;
- plugins;
- securely mounted external artifact storage;
- a developer-owned fork or separate artifact service.

None should be assumed as part of the first implementation.

## 18. Open evidence required

1. Does each host discover project skills excluded only through `.git/info/exclude`?
2. Does Cursor treat `.git/info/exclude` identically to `.gitignore` for indexing and Agent access?
3. Can every local host read, create, move, and commit files in a sibling companion repository under default sandbox settings?
4. Which user skills, if any, synchronize to each cloud execution surface?
5. How do same-named user and project skills resolve on every exact supported host version?
6. Can `advise` and `assess` be reliable explicit harness skills without false automatic activation?
7. Does skill adherence survive long sessions and compaction?
8. What happens when the target repository or companion moves?
9. How should a shared user skill version conflict be handled when two repositories request incompatible agent-workflows releases?
10. Where exactly are Antigravity global workflow files stored, and can they be safely owned and removed?
11. What WSL, container, SSH, or host/VM combinations must the installer support?
12. Can `verify-clean-delta` identify prior agent-workflows commits and recommend a safe history repair without mutating history automatically?

## 19. Final assessment of the four reports

No single report should be adopted unchanged.

- Gemini 3.6 has a useful composite architecture and concrete workflow inventory but too many unsupported “proven” claims and several incorrect paths.
- Gemini 3.1 has a crisp physical-separation model but is too dependent on ignored-file discovery and is substantially incomplete for the current host landscape.
- Sonnet supplies the most valuable critique missing from the others, namely that ignored files may be invisible to the host as well as Git, but its host-path conclusions were overtaken by current official documentation.
- OpenAI/Codex provides the strongest overall architecture and evidence coverage, but should absorb Sonnet’s stronger ignore-file warning, Gemini 3.6’s reverse migration and workflow inventory, and Gemini 3.1’s host/VM filesystem caution.

The reconciled architecture is therefore not a compromise average. It is a selective synthesis:

- retain the shared goals;
- choose skills-first discovery based on current official documentation;
- retain excluded files only as tested fallback;
- use the companion repository for tracked personal artifacts;
- keep authoritative mode and routing state outside the target;
- add scope-appropriate ownership records;
- verify the branch delta, not only the working tree;
- preserve recent undo and future downgrade through explicit provenance;
- separate local clean-delta from remote execution claims.

## Official sources used to resolve disagreements

All sources were checked July 26, 2026.

- [Git ignore documentation](https://git-scm.com/docs/gitignore)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills/)
- [OpenCode Rules](https://opencode.ai/docs/rules/)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Memory](https://code.claude.com/docs/en/memory)
- [Codex Skills](https://developers.openai.com/codex/skills)
- [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [GitHub Copilot Repository Instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Cursor Ignore File](https://cursor.com/docs/reference/ignore-file)
- [Cursor Rules](https://cursor.com/docs/rules)
- [Antigravity Skills](https://antigravity.google/docs/skills)
- [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)
- [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)
