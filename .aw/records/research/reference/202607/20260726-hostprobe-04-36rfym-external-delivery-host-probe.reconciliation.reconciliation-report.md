---
id: 36rfym
created: 20260726
set: hostprobe
order: 04
topic: []
model: reconciliation
kind: reconciliation-report
status: reference
outcome: adopted
summary: Migrated from 20260726-hostprobe-04-36rfym-external-delivery-host-probe.reconciliation.reconciliation-report.md.
consumed-by: []
---
# Reconciliation of Four External-Delivery Host Probe Reports

**Reconciliation date:** July 26, 2026
**Reports compared:** Gemini 3.6 Flash Medium, Gemini 3.1 Pro, Claude Sonnet 5, and Codex
**Original question:** Whether seven coding-agent hosts reliably resolve and follow workflow content delivered through an out-of-repository pointer (T1), a host-native skill (T2), or a user-global location (T3)

## Executive conclusion

The four reports do not present four equally supported versions of the same result. They vary substantially in product versions, product surfaces, tier definitions, source quality, and whether “resolved” means host-side loading or a model choosing to call a file tool.

After normalizing those differences and checking the most material conflicts against current first-party documentation, the reconciled result is:

| Host | T1: exact passive out-of-repository pointer | T2: host-native skill, including an equivalent native path | T3: documented home or global mechanism | Confidence |
| --- | --- | --- | --- | --- |
| OpenCode 1.18.5 | **Not-resolved by the host** for a passive `@path` in `AGENTS.md`. **Followed through a different mechanism** when content is configured in `opencode.json` `instructions` | **Followed** from `.agents/skills/` | **Followed** | High |
| Claude Code 2.1.220 | **Followed after external-import approval** | **Followed** from `.claude/skills/`; `.agents/skills/` is not a native Claude root | **Followed** | High |
| OpenAI Codex CLI 0.145.0 | **Not-resolved by the documented `AGENTS.md` loader** | **Followed** from `.agents/skills/` | **Followed** | High |
| GitHub Copilot CLI | **Not-resolved** for absolute and `~/` imports, explicitly by design | **Followed** from `.github/skills/`, `.claude/skills/`, or `.agents/skills/` in current documentation | **Followed** | High |
| GitHub Copilot in VS Code 1.130 | **Unknown** for an arbitrary absolute local file outside the workspace | **Followed** from `.github/skills/`, `.claude/skills/`, or `.agents/skills/` | **Followed** | High for T2/T3; medium for T1 |
| Cursor 3.11 | **Unknown** for a passive absolute out-of-workspace `@filename` | **Followed** in the current Agent Skills implementation, including `.agents/skills/` according to the current Cursor documentation cited by the Codex report | **Followed** through user skills or User Rules | Medium |
| Google Antigravity 2.0 v2.4.2 | **Followed** through Rule `@filename` resolution of a true absolute path | **Followed** from `.agents/skills/` | **Followed** from its native `~/.gemini` locations | High |
| Gemini CLI 0.52.0 | **Followed** through absolute `GEMINI.md` imports | **Followed after activation consent** from `.agents/skills/` or `.gemini/skills/` | **Followed**, with the same skill-activation consent when a global skill is used | High |

The practical recommendation is therefore:

1. Make T2 the main cross-host delivery mechanism.
2. Use `.agents/skills/<name>/SKILL.md` for OpenCode, Codex, Copilot, Cursor, Antigravity, and Gemini CLI.
3. Add a Claude-specific `.claude/skills/<name>/SKILL.md` adapter.
4. Do not replace the existing repository shim with one universal absolute `@path`. T1 requires host-specific syntax and, for OpenCode and Codex, a different mechanism or weaker model-mediated behavior.
5. Treat T3 as an explicit, reversible installation into user-global state.

No report supplied a complete, reproducible host execution fixture with the requested path, nonce, diagnostic evidence, and observed side effect. “Followed” in the reconciled result therefore means current first-party documentation supports discovery or import and application of the content. It does not mean that all four researchers observed a live `PROBE-OK.txt` result.

## Reports and labels used in this reconciliation

| Short label | Report | Stated method | Important qualification |
| --- | --- | --- | --- |
| **G31** | Gemini 3.1 Pro | Architectural synthesis and general documentation knowledge | Explicitly says it could not run fixtures or perform live web research. Its versions and many capability claims are stale or unsupported. |
| **G36** | Gemini 3.6 Flash Medium | Documentation, search, and several claimed hands-on or reproducible tests | Gives no fixture paths, commands, nonces, logs, or side-effect results for those tests. Several cited versions and paths conflict with current first-party material. |
| **S5** | Claude Sonnet 5 | Dated web research using vendor docs, official repositories, and public issues | Strong source discipline overall, but sometimes interprets T2 or T3 as requiring the literal `.agents` path even though the brief allows a host-native equivalent. It also collapses or prioritizes the Copilot CLI surface where VS Code differs. |
| **C** | Codex | Dated first-party documentation and release research; local binary availability check | No host executables were available, so all verdicts were documentation-based. It separated host-side resolution from model/tool behavior and generally used the newest explicit releases. |

## Reconciliation method

### Normalized tier meanings

The original brief defines T2 as `.agents/skills/<name>/SKILL.md` **or an equivalent skills path**, and T3 as content in a home-directory or global location. Therefore:

- Claude Code support at `.claude/skills/` counts as T2 support even though the literal `.agents/skills/` path is not supported.
- A Cursor or Antigravity native user-global skill or rule location counts as T3 support even if it is not `~/.agents/skills/`.
- A report that says “Not-resolved” only because one literal example path is unsupported can still amount to a positive answer under the original tier definition.

For T1, the reconciliation uses the exact load-bearing distinction in the brief:

- **Host-resolved:** the application itself imports, expands, attaches, or discovers the external content.
- **Model-mediated read:** the model sees a path as text and may decide to call a Read, shell, or file tool.

These are not treated as equivalent. A permissive file tool proves that the file may be accessible; it does not prove that a passive pointer was resolved by the host.

### Verdict notation in comparison tables

- **F:** Followed or supported
- **RNF:** Resolved-not-followed
- **NR:** Not-resolved
- **U:** Unknown
- **O:** Omitted or declared not applicable
- **F-alt:** Followed through a different, explicitly identified host mechanism
- **Mixed:** The report contains inconsistent verdicts or combines different surfaces

## Agreement overview

### Unanimous agreement after normalization

Only four host-tier conclusions are supported by all four reports after equivalent native paths are counted:

| Host and tier | Shared conclusion | Qualifications that differed |
| --- | --- | --- |
| Claude Code T1 | **Followed** | G31 and G36 omitted the first-use external import approval. S5 and C included it. |
| Claude Code T3 | **Followed** | G31 named `~/.claude.json`, which is not the correct global workflow content path. The positive capability conclusion survives, but its path does not. |
| Gemini CLI T1 | **Followed** | G31 and G36 attributed success generally to tool access. S5 and C identified the host-native absolute import grammar. |
| Gemini CLI T3 | **Followed** | G31 and G36 omitted skill activation consent and the exact precedence model. |

### Three-report agreement

| Host and tier | Reports agreeing | Outlier or omission | Reconciled result |
| --- | --- | --- | --- |
| OpenCode T2 | G36, S5, C | G31: Unknown | **Followed** |
| OpenCode T3 | G36, S5, C | G31: Unknown | **Followed** |
| Claude Code T2 at a native equivalent path | G36, S5, C | G31: Not-resolved | **Followed** at `.claude/skills/` |
| Codex T3 | G36, S5, C | G31: Omitted as “N/A” | **Followed** |
| Copilot T3 | G36, S5, C | G31: Not-resolved | **Followed** |
| Antigravity T2 | G36, S5, C | G31: Unknown | **Followed** |
| Antigravity T3 | G36, S5, C | G31: Unknown | **Followed** at native `~/.gemini` paths |
| Gemini CLI T2 | G36, S5, C | G31: Not-resolved | **Followed after consent** |

### Genuine splits

| Issue | Split | Why the reports differ | Reconciliation |
| --- | --- | --- | --- |
| OpenCode T1 | G31/G36: F; S5/C: passive `@path` NR, configured alternative F | The positive reports treat a model’s Read tool or any external-content mechanism as T1 success. The negative reports test the exact passive `@path` host-loader claim. | **NR for the exact passive shim; F-alt through `opencode.json` instructions.** |
| Codex T1 | G36: F; S5/C: NR; G31: O | G36 equates file-tool access with host resolution. S5 and C apply the host-loader definition. | **NR by documented loader.** |
| Codex T2 | G36: NR; S5/C: F; G31: O | G36 uses an obsolete capability picture. Current Codex documentation explicitly lists `.agents/skills`. | **F.** |
| Copilot T1 | G31: NR; G36: RNF; S5: NR for CLI; C: U for VS Code | The reports examine different Copilot surfaces. CLI explicitly blocks absolute imports; VS Code documentation does not establish the same external-local-file boundary. | **CLI NR; VS Code U.** |
| Copilot T2 | G31/G36: NR; S5: native equivalent F but literal `.agents` NR; C: F including `.agents` | The reports use different documentation vintages and surfaces. Current GitHub and VS Code docs list `.agents/skills`. | **F in current CLI and VS Code documentation.** |
| Cursor T1 | G31/G36: RNF; S5/C: U | G31/G36 infer a workspace-bound resolution failure without a documented or reproduced context-attachment test. | **U.** |
| Cursor T2/T3 | G31 negative; G36 mixed; S5 negative or unknown for literal `.agents`; C positive | Cursor skills shipped recently, documentation changed quickly, and S5 relied partly on a February third-party installer issue. | **Current capability is positive, but confidence is lower than for other hosts. Re-test exact roots on Cursor 3.11.** |
| Antigravity T1 | G31: RNF; G36/C: F; S5: U | S5 did not retrieve the Rules page deeply enough. Current official Rules documentation explicitly defines true absolute `@filename` resolution. | **F.** |

## Master claim matrix

The entries below preserve each report’s substantive position, then give the normalized conclusion for the exact question.

| Host | Tier | G31 | G36 | S5 | C | Reconciled |
| --- | --- | --- | --- | --- | --- | --- |
| OpenCode | T1 | F | F | NR for passive `@`; F-alt via config | NR for passive `@`; F-alt via config | **NR exact shim; F-alt configured** |
| OpenCode | T2 | U | F | F | F | **F** |
| OpenCode | T3 | U | F | F | F | **F** |
| Claude Code | T1 | F | F | F | F | **F after approval** |
| Claude Code | T2 | NR | F | F at `.claude`; NR only for literal `.agents` | F at `.claude` | **F at native equivalent** |
| Claude Code | T3 | F | F | F at native path | F | **F** |
| Codex | T1 | O | F | NR | NR | **NR by host loader** |
| Codex | T2 | O | NR | F | F | **F** |
| Codex | T3 | O | F | F | F | **F** |
| Copilot | T1 | NR | RNF | NR for CLI | U for VS Code | **CLI NR; VS Code U** |
| Copilot | T2 | NR | NR | F at native `.github`; claimed NR at literal `.agents` | F including `.agents` | **F in current docs** |
| Copilot | T3 | NR | F | F | F | **F** |
| Cursor | T1 | RNF | RNF | U | U | **U** |
| Cursor | T2 | NR | Mixed: summary RNF, matrix NR | U, leaning NR for literal `.agents` | F | **F provisionally; version-pin and test** |
| Cursor | T3 | NR | F | NR only for literal `~/.agents` | F at native paths/UI rules | **F at native equivalent; exact `~/.agents` needs confirmation** |
| Antigravity | T1 | RNF | F | U | F | **F** |
| Antigravity | T2 | U | F | F | F | **F** |
| Antigravity | T3 | U | F | F at a different native path | F | **F** |
| Gemini CLI | T1 | F | F | F | F | **F** |
| Gemini CLI | T2 | NR | F | F | F after consent | **F after consent** |
| Gemini CLI | T3 | F | F | F | F | **F** |

## Detailed reconciliation by host

### OpenCode

#### Agreements

G36, S5, and C agree that OpenCode supports both project skills and global skills. S5 and C specifically identify `.agents/skills/`, `.opencode/skills/`, and Claude-compatible skill roots. G31 leaves both T2 and T3 unknown rather than contradicting them with evidence.

#### Divergence

G31 and G36 call T1 Followed because OpenCode exposes file-reading tools or allegedly executes a command shim. Neither supplies a reproducible fixture. S5 and C distinguish the exact passive pointer from configured instruction sources.

Current OpenCode documentation says that OpenCode does not automatically parse file references in `AGENTS.md`. It recommends the `instructions` field in `opencode.json` or explicit prose telling the model to use the Read tool. The former is host configuration; the latter is model-mediated behavior. [OpenCode Rules](https://opencode.ai/docs/rules/)

#### Reconciled result

- **T1 exact shim:** Not-resolved by the host.
- **T1 alternative:** Supported through `opencode.json` instruction sources. An absolute local instruction path should still receive a pinned fixture because the displayed examples emphasize relative paths, globs, and remote URLs.
- **T2:** Followed from `.agents/skills/<name>/SKILL.md`.
- **T3:** Followed from `~/.config/opencode/AGENTS.md` and documented global skill roots.

#### Report-specific omissions

- G31 omits all supported skill roots, global locations, precedence, permission gates, and the current release.
- G36 omits `.agents/skills/` from its OpenCode project-path summary, even though that is the literal interoperability path under study. It also reports version `1.1.8`, while the current release used by C is `1.18.5`, released July 24, 2026. [OpenCode v1.18.5](https://github.com/anomalyco/opencode/releases/tag/v1.18.5)
- S5 and C give the most useful T1 distinction. C adds OpenCode external references and permission caveats; S5 adds environment variables that can disable Claude-compatible roots.

### Claude Code

#### Agreements

All four reports agree that T1 and T3 are supported. Three reports agree that Claude has a native skill mechanism when the allowed “equivalent skills path” wording is applied.

#### Divergence

G31 says Claude has no documented `.claude/skills/` discovery and uses version `0.2.x`. Both statements are obsolete. Current Claude Code documentation lists personal `~/.claude/skills/`, project `.claude/skills/`, enterprise skills, and plugin skills. [Claude Code Skills](https://code.claude.com/docs/en/skills)

G31 also names `~/.claude.json` as the global workflow mechanism. That file is not the documented global instruction or skill location relevant here. The relevant content locations are `~/.claude/CLAUDE.md`, `~/.claude/rules/`, and `~/.claude/skills/`.

G36 says T1 works through a command shim and file tools but omits the stronger host-native import semantics. S5 and C correctly identify `@path` import expansion in `CLAUDE.md`, including absolute paths. Current documentation also records a first-use approval dialog for imports resolving outside the working directory. [Claude Code Memory and Imports](https://code.claude.com/docs/en/memory)

#### Reconciled result

- **T1:** Followed after approval for an external import originating in a project instruction file.
- **T2:** Followed at `.claude/skills/<name>/SKILL.md`, not at `.agents/skills/`.
- **T3:** Followed at the documented `~/.claude` instruction, rule, and skill locations.

#### Report-specific omissions

- G31 omits the native skills system, approval flow, correct global content locations, precedence, cloud-session limitation, and current version.
- G36 omits the external-import approval and cloud versus local distinction. Its version `1.0.12` is stale relative to `2.1.220`, released July 25, 2026. [Claude Code v2.1.220](https://github.com/anthropics/claude-code/releases/tag/v2.1.220)
- S5 adds skill-list budget and restart caveats.
- C uniquely adds documented support in v2.1.203 and later for symlinked skill directories, which is directly relevant to minimizing repository duplication.

### OpenAI Codex CLI

#### Agreements

S5 and C agree on all three tiers: T1 is not host-resolved, T2 is supported from `.agents/skills/`, and T3 is supported. G36 agrees only on T3. G31 incorrectly treats Codex as an API rather than the requested Codex host and therefore omits it.

#### Divergence

G36 reports T1 Followed “when bash/file tools [are] enabled.” This proves possible file access, not `AGENTS.md` import expansion. Current Codex documentation describes global and project instruction-file discovery but does not define `@include` or `@path` expansion. [Codex `AGENTS.md` Guide](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

G36 reports T2 Not-resolved and claims there is no native skill schema. Current Codex documentation explicitly describes `.agents/skills` discovery from the current directory to repository root, plus user and admin scopes. [OpenAI Build Skills](https://learn.chatgpt.com/docs/build-skills)

G36’s `~/.codex/instructions.md` path is also incorrect for current Codex global instructions. The documented default is `~/.codex/AGENTS.md`, with `AGENTS.override.md` taking priority at that level.

#### Reconciled result

- **T1:** Not-resolved by the documented loader. A model may still read a path when permitted, but that is not a reliable host import.
- **T2:** Followed from `.agents/skills/`.
- **T3:** Followed from Codex-home instructions and `$HOME/.agents/skills`.

#### Report-specific omissions

- G31 omits the product surface entirely.
- G36 omits current skills support, actual global paths, instruction precedence, duplicate-skill behavior, and version-current evidence. Its version `0.9.0` is stale relative to `0.145.0`, released July 21, 2026. [Codex 0.145.0](https://github.com/openai/codex/releases/tag/rust-v0.145.0)
- S5 adds an open feature request for composable `AGENTS.md` includes and skill-list context-budget caveats.
- C adds symlinked skill-folder support and a concrete release-qualification fixture design.

### GitHub Copilot and VS Code Copilot

#### Surface correction

This is the most important scope correction in the comparison. “GitHub Copilot” is not one behavior:

- Copilot CLI has explicit file-reference boundary documentation.
- Copilot in VS Code has VS Code-specific instruction and skill roots.
- Copilot cloud agent and code review have separate filesystem and customization behavior.

Raw report verdicts cannot be reconciled without naming the surface.

#### T1

G31 says Not-resolved due to workspace confinement. G36 says Resolved-not-followed. S5 establishes a stronger, first-party negative for Copilot CLI: relative `@` references are loaded only within the repository or custom-instructions directory, while absolute and `~/` paths are not loaded. [GitHub Copilot CLI Custom Instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)

C examines Copilot in VS Code and finds the arbitrary external absolute-file boundary unspecified. These conclusions are compatible:

- **Copilot CLI:** Not-resolved.
- **Copilot in VS Code:** Unknown until a fixture establishes arbitrary absolute local-file behavior.

#### T2

G31 and G36 say no native skills support. S5 says `.github/skills/` works but `.agents/skills/` does not. C says current VS Code supports `.github/skills/`, `.claude/skills/`, and `.agents/skills/`.

Current first-party documentation resolves this conflict in favor of C and newer documentation:

- GitHub’s current Copilot CLI page lists project skills in `.github/skills`, `.claude/skills`, or `.agents/skills`, and personal skills in `~/.copilot/skills` or `~/.agents/skills`. [GitHub Copilot CLI Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
- VS Code’s Agent Skills page lists the same three project roots and three personal roots, and says skills work across VS Code, Copilot CLI, and Copilot cloud agent. [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)

S5’s literal `.agents/skills/` negative was therefore already outdated or surface-limited by the time of reconciliation, even though its `.github/skills/` equivalent would still count as a positive T2 answer under the original brief.

#### T3

G36, S5, and C agree that a user-global mechanism exists. G31’s blanket negative is contradicted by current first-party skill and instruction documentation.

#### Reconciled result

- **T1:** CLI Not-resolved; VS Code arbitrary absolute local path Unknown.
- **T2:** Followed in current CLI and VS Code documentation, including the literal `.agents/skills/` path.
- **T3:** Followed through documented personal instruction and skill roots.

#### Report-specific omissions

- G31 omits Copilot’s current skills system, user-global support, surface differences, settings, and precedence.
- G36 omits the current native Agent Skills standard and relies on a stale `useInstructionFiles` framing.
- S5 provides the best CLI T1 negative but overgeneralizes the project skill-path limitation.
- C provides the best VS Code-specific current path inventory, but does not separately give the explicit Copilot CLI T1 refusal that S5 found.

### Cursor

#### Agreements

All four reports recognize some workspace or permissions boundary around out-of-workspace access. None provides a live attachment-and-side-effect probe. G36 and C agree that a user-global mechanism exists, although they describe it differently.

#### Divergence

G31 is based on Cursor `0.40+`, describes Cursor as relying strictly on `.cursorrules`, and denies modern skills. Cursor introduced Agent Skills in version 2.4 on January 22, 2026, so that product model is obsolete. [Cursor 2.4](https://cursor.com/changelog/2-4)

G36’s summary says Cursor T2 is Resolved-not-followed, while its detailed matrix says Resolved No and Followed No. That is an internal contradiction. It also treats `.cursor/rules/*.mdc` wrappers as the only path, which confuses rules with the newer Agent Skills feature.

S5 is careful about weak evidence but relies on a February 2026 issue against a third-party skill installer to reject `~/.agents/skills/`. That issue can establish a point-in-time installer compatibility problem, not necessarily Cursor 3.11 behavior in July 2026. It also evaluates the literal `~/.agents/skills/` example as though T3 required that exact location, even though the brief allows any host-native global location.

C cites current Cursor Agent Skills documentation for project roots `.agents/skills/`, `.cursor/skills/`, `.claude/skills/`, and `.codex/skills/`, plus corresponding user roots. The current Cursor docs page is client-rendered and could not be independently text-extracted during this reconciliation, so those exact roots receive medium rather than high confidence.

#### Reconciled result

- **T1:** Unknown. Current Rules documentation confirms `@filename` references but does not provide sufficiently retrievable evidence for arbitrary absolute out-of-workspace host resolution.
- **T2:** Followed in Cursor’s current Agent Skills implementation, provisionally including `.agents/skills/`. Pin Cursor 3.11 and verify exact roots.
- **T3:** Followed through native user skills or User Rules. The literal `~/.agents/skills/` alias should be verified on the pinned build.

#### Report-specific omissions

- G31 omits all post-2.4 skills behavior and uses an obsolete rule-only product model.
- G36 omits a coherent resolved/followed distinction for T2 and gives no evidence for its workspace-bound T1 claim.
- S5 contributes the best warning about rapidly changing Cursor behavior and weak retrievability, but turns a literal-path issue into a broader T3 negative.
- C contributes the newest version and most complete current path set, but its Cursor path claims need a reproducible fixture because the primary page is difficult to independently archive.

### Google Antigravity

#### Agreements

G36, S5, and C agree that T2 and T3 exist. G31 leaves them unknown. G36 and C agree that T1 is Followed.

#### Divergence

G31 calls T1 Resolved-not-followed and attributes unreliability to WSL and Python virtual environments. That caveat concerns executing a Python-dependent workflow, not whether Antigravity resolves the external instruction file. It is not evidence that an instruction imported through a Rule was resolved but ignored.

G36 claims hands-on T1 and T2 tests but provides no fixture details. It also names global roots under `~/.gemini/antigravity-cli/`, which conflict with the current Antigravity documentation cited by S5 and C.

S5 marks T1 Unknown because it did not deeply retrieve the Rules page. Current official documentation now makes the result explicit: a Rule can reference `@filename`; a true absolute path is tried first, then a workspace-relative fallback if the absolute target does not exist. [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)

Current Antigravity documentation identifies workspace skills under `.agents/skills/`, global rules at `~/.gemini/GEMINI.md`, and global skills under `~/.gemini/config/skills/`. [Antigravity Skills](https://antigravity.google/docs/skills)

#### Reconciled result

- **T1:** Followed through Rule absolute-path references.
- **T2:** Followed from `.agents/skills/`.
- **T3:** Followed from native `~/.gemini` rule and skill locations.

#### Report-specific omissions

- G31 omits current native rules, workflows, skills, and global paths.
- G36 omits a reproducible fixture and cites nonportable `file:///home/...` paths as sources. Its Antigravity version `2.4.0` is behind the current documentation banner `2.4.2`.
- S5 contributes the best careful statement of evidence limits, but its T1 search was incomplete.
- C contributes the decisive T1 Rules citation and distinguishes deterministic activation modes from model-selected rules.

### Gemini CLI

#### Agreements

All four reports agree on T1 and T3. G36, S5, and C agree on T2. This is the strongest overall host consensus.

#### Divergence

G31 says T2 is Not-resolved. Current Gemini CLI documentation directly contradicts that conclusion by listing `.gemini/skills/` and `.agents/skills/` at workspace scope, with corresponding user roots. [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)

G31 and G36 explain T1 mostly through generic CLI file access. S5 and C identify the stronger host mechanism: `GEMINI.md` imports accept absolute paths and incorporate the imported content into combined context. [Gemini CLI `GEMINI.md`](https://geminicli.com/docs/cli/gemini-md/)

Only S5 and C include the activation sequence that materially qualifies “Followed”: discovery exposes metadata, the model calls `activate_skill`, the UI asks for consent, and the body is injected only after approval.

#### Reconciled result

- **T1:** Followed through an official absolute import mechanism.
- **T2:** Followed after activation consent.
- **T3:** Followed. Global skills retain the activation-consent qualification.

#### Report-specific omissions

- G31 omits all native skills support, exact paths, consent, precedence, and the current version.
- G36 omits the `.agents/skills/` interoperability alias, consent flow, and precedence. Its version `0.8.2` is stale relative to `0.52.0`, released July 22, 2026. [Gemini CLI v0.52.0](https://github.com/google-gemini/gemini-cli/releases/tag/v0.52.0)
- S5 and C agree closely. S5 adds an unattended/headless consent question; C adds `/memory show` as a resolution diagnostic and a more explicit precedence summary.

## Version reconciliation

Several disagreements are explained or aggravated by comparing incompatible versions.

| Host | G31 | G36 | S5 | C | Reconciled version basis |
| --- | --- | --- | --- | --- | --- |
| OpenCode | Unspecified in summary; `1.25+` appears only for Copilot | `1.1.8` | Docs updated July 24, 2026 | `1.18.5`, July 24 | **1.18.5** |
| Claude Code | `0.2.x` | `1.0.12` | `2.1.2xx` line | `2.1.220`, July 25 | **2.1.220** |
| Codex CLI | Declared N/A | `0.9.0` | Current docs, no exact release | `0.145.0`, July 21 | **0.145.0** |
| Copilot / VS Code | `1.25+` without surface clarity | `1.250+` | Current docs, multiple surfaces | VS Code `1.130`, July 22 | **Surface-specific current docs; VS Code 1.130 for IDE claims** |
| Cursor | `0.40+` | `0.45+` | Skills since `2.4` | `3.11`, July 10 | **3.11** |
| Antigravity | `2026.x` | `2.4.0` | `2.4.2` docs banner | `2.3.1` at July 25 | **2.4.2 current docs banner** |
| Gemini CLI | `1.5+` | `0.8.2` | Current docs | `0.52.0`, July 22 | **0.52.0** |

The version table exposes two recurring problems:

1. G31 and G36 often use old or malformed versions while presenting July 2026 conclusions.
2. Antigravity’s rapidly updated documentation changed between C’s July 25 capture (`2.3.1`) and S5’s or the current July 26 capture (`2.4.2`). This does not invalidate C’s cited path behavior, but the reconciled report uses the newer banner.

## Precedence and shadowing comparison

| Host | Best-supported precedence finding | Reports contributing it | Material omission or conflict |
| --- | --- | --- | --- |
| OpenCode | First matching rule file wins within each category; project and global categories are both used. Skill access may be allowed, denied, or approval-gated. | S5, C | G31/G36 provide little usable precedence evidence. Complete duplicate-skill collision order remains insufficiently documented. |
| Claude Code | Instructions load broad to specific. For same-named skills: enterprise over personal over project; plugin skills are namespaced. | G36, S5, C | G36 states the skill order but omits that behavioral instructions remain context, not enforcement. |
| Codex | Instruction files are composed broad to specific; more local content appears later. Same-named skills are not silently merged into one winner. | S5, C | G31 omits Codex; G36 omits precedence. |
| Copilot | CLI combines applicable instructions and does not define a general precedence order. VS Code documents priority among personal, repository, and organization instructions, but multiple surfaces differ. | S5, C | G31’s “in-repo always wins” is unsupported as a universal statement. |
| Cursor | Rules and skills require version-specific treatment. Current reports disagree on exact skill-root collision behavior. | S5, C | No report supplies a duplicate-name fixture. |
| Antigravity | Current primary docs establish locations and activation modes but do not clearly establish global-versus-workspace duplicate-skill precedence. | C | G36 asserts local override without a supporting citation or fixture. |
| Gemini CLI | Built-in < extension < user < workspace. Within a tier, `.agents/skills` overrides `.gemini/skills` for a duplicate name. | S5, C | G31/G36 omit this silent-shadowing risk. |

## Reliability, consent, and execution caveats

| Caveat | G31 | G36 | S5 | C | Reconciled assessment |
| --- | --- | --- | --- | --- | --- |
| Host resolution versus model file-tool behavior | Frequently conflated | Frequently conflated | Explicitly separated | Explicitly separated | Must remain separate for T1 qualification. |
| Live side-effect fixture | Explicitly absent | Claimed for some rows, not documented | Explicitly absent | Explicitly absent after binary availability check | No reproducible live result exists in the four reports. |
| Claude external-import approval | Omitted | Omitted | Included | Included | Required deployment qualification. |
| Gemini skill activation consent | Omitted | Omitted | Included | Included | Required deployment qualification, especially for unattended use. |
| Model-selected skill invocation | Largely omitted | Largely omitted | Included | Included | Auto-discovery does not guarantee automatic execution. Explicit invocation is safer. |
| Local versus cloud host state | Omitted | Omitted | Included for Claude and Copilot | Included for Claude, Copilot, and recommendations | A machine-local T3 installation does not automatically travel to a cloud agent. |
| Permission or feature settings | General sandbox assertions | Some generic tool flags | Several host-specific settings | Several host-specific settings | Must be included in release fixtures. |
| Version drift | Uses broad old ranges | Uses several old versions | Generally current docs | Exact releases, mostly current | Pin versions and re-run probes. |

## Omissions by report

### Gemini 3.1 Pro

G31 omits or materially undercovers:

- the requested current version and date for most hosts;
- Codex CLI as a host;
- modern Agent Skills support in OpenCode, Copilot, Cursor, Antigravity, and Gemini CLI;
- exact T2 and T3 paths for most hosts;
- Claude external-import approval;
- Gemini skill activation consent;
- surface differences within Copilot;
- precedence and shadowing beyond unsupported generalizations;
- complete per-host, per-tier rows;
- reproducible tests;
- claim-level citations and a complete source list.

Its useful contributions are limited but not zero:

- it correctly predicts T1 support in Claude Code and Gemini CLI;
- it correctly flags T3 as a consent-sensitive mutation;
- it warns that generic IDE and CLI behaviors may differ.

### Gemini 3.6 Flash Medium

G36 omits or materially undercovers:

- reproducible details for every claimed hands-on test;
- a clean distinction between host import and model/tool access;
- current versions for OpenCode, Claude Code, Codex, Cursor, and Gemini CLI;
- the current Codex skills system;
- the current Copilot skills system;
- the `.agents/skills/` OpenCode interoperability root;
- Claude external-import approval;
- Gemini activation consent and precedence;
- a reliable Cursor T2 verdict;
- a portable, independently checkable source list.

It contributes:

- a complete 21-cell matrix;
- early recognition that Antigravity, OpenCode, and Claude have native skill mechanisms;
- the correct high-level recommendation to use host-native skills and IDE-specific fallbacks.

However, its “hands-on test” labels should not be treated as test evidence because the report gives no fixture, command, diagnostic, nonce, or observed side effect.

### Claude Sonnet 5

S5 omits or undercovers:

- the current VS Code `.agents/skills/` support that resolves its Copilot T2 negative;
- the Antigravity Rules page that resolves T1 positively;
- a current, independently retrievable basis for Cursor’s exact roots;
- exact release numbers for several hosts;
- live fixtures.

It contributes substantial unique value:

- the clearest evidence-quality disclaimer;
- an explicit Copilot CLI T1 negative from first-party documentation;
- a Codex include feature request as corroborating negative evidence;
- skill-list context-budget and restart caveats;
- careful warnings about Cursor documentation quality;
- a strong unattended-consent caveat for Gemini CLI;
- a more complete claim-level source list than G31 or G36.

Its main analytical error is treating some literal `.agents` path failures as a negative tier result even though the original brief explicitly permits host-native equivalent paths.

### Codex

C omits or undercovers:

- the explicit Copilot CLI T1 prohibition that S5 found;
- the newer Antigravity `2.4.2` banner visible one day later;
- a reproducible host fixture because no target binary was installed;
- an independently archivable Cursor skills page.

It contributes:

- exact current releases for six of seven hosts;
- the most complete current cross-host `.agents/skills/` convergence;
- the decisive Antigravity absolute-path Rule behavior;
- the strongest distinction between host resolution and model/tool behavior;
- OpenCode external-reference and configured-instruction alternatives;
- Claude and Codex symlink support relevant to reducing repository footprint;
- cloud/local distribution caveats;
- a concrete fixture and precedence-test design;
- the most implementable cross-host recommendation.

## Evidence-quality assessment

| Report | Coverage completeness | Version accuracy | Primary-source quality | Resolved/followed discipline | Test reproducibility | Overall use in final reconciliation |
| --- | --- | --- | --- | --- | --- | --- |
| G31 | Low | Low | Low | Low | None, explicitly | Used mainly as a record of early assumptions and broad negatives |
| G36 | High row coverage | Low to medium | Low to medium | Low | None despite test labels | Used for comparison, but no disputed claim is accepted solely from it |
| S5 | High | Medium to high | High | High | None, explicitly | Major source for CLI-specific negatives, caveats, and omissions |
| C | High | High | High | High | None, explicitly, with environment check | Main baseline, corrected by S5 on Copilot CLI and by newer Antigravity version evidence |

This assessment is not a model ranking. It evaluates these four artifacts against the original brief’s requirements.

## Reconciled implementation guidance

### Preferred T2 layout

| Host | Project discovery entry | User-global discovery entry | Installation note |
| --- | --- | --- | --- |
| OpenCode | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` or OpenCode-native root | Permissions may ask, allow, or deny skill loading. |
| Claude Code | `.claude/skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Symlinked skill directories are supported in current versions. |
| Codex | `.agents/skills/<name>/SKILL.md` | `$HOME/.agents/skills/<name>/SKILL.md` | Symlinked skill directories are supported. |
| Copilot CLI / VS Code | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | Keep surface-specific settings and cloud filesystem availability in mind. |
| Cursor | `.agents/skills/<name>/SKILL.md` on the pinned current build | Current native user skill root | Verify exact aliases on Cursor 3.11 before release. |
| Antigravity | `.agents/skills/<name>/SKILL.md` | `~/.gemini/config/skills/<name>/SKILL.md` | Global path differs from the shared project path. |
| Gemini CLI | `.agents/skills/<name>/SKILL.md` | `~/.agents/skills/<name>/SKILL.md` | Activation requires user consent. |

### T1 host-specific policy

| Host | Recommended T1 treatment |
| --- | --- |
| OpenCode | Generate `opencode.json` instruction configuration or use a configured reference. Do not rely on passive `@path` expansion in `AGENTS.md`. |
| Claude Code | Use a `CLAUDE.md` absolute or home-path import and document the approval prompt. |
| Codex | Do not rely on passive `@path`. Prefer T2 or an explicit model-mediated Read instruction only where weaker reliability is acceptable. |
| Copilot CLI | Do not use absolute or `~/` imports. They are explicitly not loaded. |
| Copilot in VS Code | Keep as Unknown until an external-file fixture passes on the target build and settings. |
| Cursor | Keep as Unknown until an external absolute `@filename` fixture proves both attachment and side effect. |
| Antigravity | Use a Rule with absolute `@filename`; select an activation mode appropriate to the required determinism. |
| Gemini CLI | Use an absolute import in `GEMINI.md`; inspect combined memory to prove resolution. |

### Required release fixture

Before shipping any delivery tier, test each exact host and version with:

1. A clean temporary home directory and empty temporary Git repository.
2. External workflow content outside every workspace root.
3. A random nonce and an instruction only in that content to create `PROBE-OK-<host>-<version>-<nonce>.txt`.
4. Host diagnostics proving resolution, such as context, memory, instruction, or skill listings.
5. Verification of the exact nonce side effect.
6. A conflicting repository instruction producing a different nonce to establish precedence.
7. A permissions-denied run, an approval-accepted run, and, where relevant, a noninteractive run.
8. Separate runs for local and cloud surfaces.
9. Captured host version, settings, fixture tree, commands, logs, and final filesystem state.

Record **Resolved** only from host diagnostics or direct context evidence. Record **Followed** only when the unique side effect occurs.

## Remaining unknowns

The reconciliation does not erase these evidence gaps:

- Cursor 3.11 exact support and collision behavior for every `.agents`, `.cursor`, `.claude`, and `.codex` project and user skill alias.
- Arbitrary out-of-workspace T1 resolution in Copilot for VS Code.
- Arbitrary out-of-workspace T1 resolution in Cursor.
- Duplicate-name skill precedence in OpenCode, Copilot, Cursor, and Antigravity where primary docs are incomplete.
- Noninteractive or CI behavior for Gemini CLI’s activation-consent gate.
- Whether absolute local paths in OpenCode’s `instructions` array behave identically to documented relative files and remote URLs on the pinned release.
- Whether machine-local T3 content is synchronized, copied, or unavailable in each cloud-agent surface.

These unknowns should remain explicit release blockers wherever the implementation depends on them.

## Sources used to adjudicate conflicts

All links were checked July 26, 2026 unless the source is a dated release page.

1. OpenCode, [Rules](https://opencode.ai/docs/rules/)
2. OpenCode, [Agent Skills](https://opencode.ai/docs/skills/)
3. OpenCode, [release v1.18.5](https://github.com/anomalyco/opencode/releases/tag/v1.18.5)
4. Anthropic, [Claude Code Memory and Imports](https://code.claude.com/docs/en/memory)
5. Anthropic, [Claude Code Skills](https://code.claude.com/docs/en/skills)
6. Anthropic, [Claude Code release v2.1.220](https://github.com/anthropics/claude-code/releases/tag/v2.1.220)
7. OpenAI, [Custom Instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
8. OpenAI, [Build Skills](https://learn.chatgpt.com/docs/build-skills)
9. OpenAI, [Codex release 0.145.0](https://github.com/openai/codex/releases/tag/rust-v0.145.0)
10. GitHub, [Copilot CLI Custom Instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
11. GitHub, [Copilot CLI Agent Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)
12. Microsoft, [VS Code Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills)
13. Microsoft, [VS Code 1.130](https://code.visualstudio.com/updates/v1_130)
14. Cursor, [Agent Skills](https://cursor.com/docs/skills)
15. Cursor, [Rules](https://cursor.com/docs/rules)
16. Cursor, [release 2.4](https://cursor.com/changelog/2-4)
17. Cursor, [changelog containing release 3.11](https://cursor.com/changelog/page/1)
18. Google, [Antigravity Rules and Workflows](https://antigravity.google/docs/rules-workflows)
19. Google, [Antigravity Skills](https://antigravity.google/docs/skills)
20. Google, [Gemini CLI GEMINI.md](https://geminicli.com/docs/cli/gemini-md/)
21. Google, [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/skills/)
22. Google, [Gemini CLI release v0.52.0](https://github.com/google-gemini/gemini-cli/releases/tag/v0.52.0)

## Final reconciled answer

The four reports converge most strongly on T2 and T3, but only after the original brief’s “equivalent native path” wording is applied consistently. The current evidence supports a shared `.agents/skills/` project tier for every evaluated host except Claude Code, which needs a `.claude/skills/` adapter. T3 exists for every host but is consent-sensitive, surface-dependent, and subject to shadowing.

The reports do not support a universal T1 shim. Claude Code, Antigravity, and Gemini CLI have documented absolute import or reference behavior. OpenCode requires a configured instruction mechanism for host-level reliability. Codex lacks passive `@path` expansion. Copilot CLI explicitly refuses absolute and home-relative imports. Copilot in VS Code and Cursor remain unproven for arbitrary absolute files outside the workspace.

The safest architecture is therefore a T2-first multi-host installer, a Claude-specific skill adapter, optional and reversible T3 installation, and host-specific T1 only where first-party import semantics and a version-pinned side-effect fixture both support it.
