# External Delivery of Agent-Workflow Content: Host Resolution/Follow Probe

**Scope:** For each host, can it RESOLVE (load into context) and then FOLLOW (act on) agent-workflow instruction content that lives outside the working repository (T1), in a host-native skill file with no in-repo pointer (T2), or at a home-dir/global location (T3)?

**Method note:** This report is built entirely from published, dated vendor documentation, official GitHub repos, and public issue trackers retrieved via web search on 2026-07-26. No host application was actually launched and probed with a live `PROBE-OK.txt`-style fixture in this pass — that would require shell access to each tool's runtime, which was not available here. Every claim below is therefore a **documentation-verified** claim, not a **live-tested** one, and is labeled accordingly. Where docs are silent or sources conflict, this is stated explicitly rather than inferred.

---

## 1. Executive summary

| Host | T1 (out-of-repo pointer) | T2 (`.agents/skills/` in-repo, no pointer) | T3 (home-dir/global) |
|---|---|---|---|
| **Claude Code** (docs current as of ~2026-07-25, v2.1.2xx) | **Followed** — `@path` imports in CLAUDE.md accept absolute paths, expand at session start | **Not-resolved** for the literal `.agents/skills/` path — Claude Code only auto-discovers `.claude/skills/`; equivalent mechanism at `.claude/skills/` is Followed | **Followed** at `~/.claude/skills/`; literal `~/.agents/skills/` **not supported** |
| **OpenCode** (docs updated 2026-07-24) | **Followed** via `opencode.json` `instructions` array (accepts absolute paths and remote URLs); a bare `@path` mention inside AGENTS.md is **not auto-parsed** by the host itself | **Followed** — natively walks up to git worktree root scanning `.agents/skills/*/SKILL.md` | **Followed** — natively scans `~/.agents/skills/*/SKILL.md` |
| **Codex CLI (OpenAI)** (docs current, skills feature since ~April 2026) | **Not-resolved** — AGENTS.md has no native `@include`; a public feature request for it is still open (Apr 2026) | **Followed** — scans `.agents/skills` from CWD up to repo root | **Followed** — scans `$HOME/.agents/skills`; also an ADMIN tier at `/etc/codex/skills` |
| **GitHub Copilot (CLI / VS Code / cloud agent)** (docs current) | **Not-resolved** (documented negative) — Copilot CLI's own `@`-include explicitly refuses absolute paths and `~/`-paths by design | **Not-resolved** for the literal `.agents/skills/` path — Copilot's native project path is `.github/skills/`, not `.agents/skills/`; `.github/skills/` itself is Followed | **Followed** — official docs list `~/.agents/skills` as an accepted personal-skill location alongside `~/.copilot/skills` |
| **Cursor** (skills feature since v2.4, Jan 2026) | **Unknown** — `@file` references exist in rules but scope for absolute/out-of-repo paths is undocumented in the pages retrieved | **Unknown/likely Not-resolved** — official-adjacent sources confirm `.cursor/skills/` and `.claude/skills/`; no first-party confirmation of `.agents/skills/` at project level | **Not-resolved** (documented negative) — a maintainer-filed bug report explicitly states Cursor does not read `~/.agents/skills/` |
| **Google Antigravity** (Antigravity 2.0 v2.4.2 / IDE v2.1.1 / CLI v1.1.6, docs current) | **Unknown** — no documentation found describing an out-of-repo pointer/import mechanism | **Followed** — official docs give the exact path `<workspace-root>/.agents/skills/<skill-folder>/` | **Followed**, but at a different global path than the literal T3 spec: `~/.gemini/config/skills/`, not `~/.agents/skills/` |
| **Gemini CLI** (docs current, skills feature GA) | **Followed** — GEMINI.md/AGENTS.md `@file` imports officially support absolute paths | **Followed** — official docs name `.agents/skills/` as a first-class alias, taking precedence over `.gemini/skills/` at the same tier | **Followed** — `~/.agents/skills/` is the documented user-tier alias |

**Overall pattern:** The `.agents/skills/` convention (project) and `~/.agents/skills/` (global) as literally specified in the brief are natively, currently supported by **OpenCode, Codex CLI, Google Antigravity (project only — global path differs), and Gemini CLI**. They are **not** the native skills path for **Claude Code** (uses `.claude/skills/`) or **GitHub Copilot** (uses `.github/skills/` for project scope, though it does accept `~/.agents/skills/` for personal scope). **Cursor** currently appears to support neither the project nor the global `.agents/skills/` path natively, based on available evidence.

For T1 (out-of-repo pointers), reliable **host-level** resolution — i.e., a documented import/include mechanism that accepts absolute paths — exists in **Claude Code**, **Gemini CLI**, and **OpenCode** (via config, not via bare `@` in AGENTS.md). It is explicitly **absent or blocked** in **Codex CLI** and **GitHub Copilot CLI** (the latter by explicit design decision). It is **unverified** for **Cursor** and **Antigravity**.

---

## 2. Per-host × per-tier results table

| Host | Version / doc date | Tier | Resolved? | Followed? | How verified | Notes | Date checked |
|---|---|---|---|---|---|---|---|
| Claude Code | Docs dated ~2026-07-25 (v2.1.2xx line) | T1 | Yes | Yes | Official docs (`code.claude.com/docs/en/memory`) | `@path` import accepts relative and absolute paths; expands at launch; first external import triggers a one-time approval dialog (declining disables it, no re-prompt) | 2026-07-26 |
| Claude Code | same | T2 (`.agents/skills/`) | No | — | Official docs (`code.claude.com/docs/en/skills`) | Native skill discovery is `.claude/skills/` only; `.agents/skills/` is not among the documented discovery paths | 2026-07-26 |
| Claude Code | same | T3 (`~/.agents/skills/`) | No (Yes at `~/.claude/skills/`) | — (Yes at native path) | Same docs | Personal skills load from `~/.claude/skills/`; enterprise > personal > project precedence | 2026-07-26 |
| OpenCode | Docs updated 2026-07-24 | T1 | Yes (via config) / Partial (via bare `@`) | Yes (via config) | Official docs (`opencode.ai/docs/rules/`) | `opencode.json` `instructions` array loads arbitrary paths and remote URLs, merged into context. A bare `@path` mention in AGENTS.md is explicitly **not** auto-parsed by the host — docs recommend either the config array or an explicit "read this file via your Read tool" instruction, which then depends on model behavior, not host parsing | 2026-07-26 |
| OpenCode | same | T2 | Yes | Yes | Official docs (`opencode.ai/docs/skills/`) | Walks up from CWD to git worktree root; matches `.opencode/skills/`, `.claude/skills/`, and `.agents/skills/` at every level along the way | 2026-07-26 |
| OpenCode | same | T3 | Yes | Yes | Same docs | Global: `~/.config/opencode/skills/`, `~/.claude/skills/`, and `~/.agents/skills/` all loaded | 2026-07-26 |
| Codex CLI (OpenAI) | Docs current; skills feature introduced ~Apr 2026 | T1 | No | — | Official docs (`developers.openai.com/codex/guides/agents-md`) + open GitHub feature request #17401 (Apr 2026) | AGENTS.md composition is directory-walk concatenation only; no `@include` directive exists. A feature request to add one is open and unresolved | 2026-07-26 |
| Codex CLI | same | T2 | Yes | Yes | Official docs (`developers.openai.com/codex/skills.md`) | Exact path: scans `.agents/skills` in `$CWD`, each parent up to repo root, and `$REPO_ROOT/.agents/skills` | 2026-07-26 |
| Codex CLI | same | T3 | Yes | Yes | Same docs | `$HOME/.agents/skills` (USER scope); additionally `/etc/codex/skills` (ADMIN scope, machine-wide) | 2026-07-26 |
| GitHub Copilot (CLI) | Docs current | T1 | No | — | Official docs (`docs.github.com/.../add-custom-instructions`) | Explicit statement: absolute paths and `~/`-paths are **not loaded** for `@`-includes; references must stay within the repo or the custom-instructions directory | 2026-07-26 |
| GitHub Copilot (CLI / VS Code / cloud agent) | Docs current | T2 (`.agents/skills/`) | No (Yes at `.github/skills/`) | — (Yes at native path) | Official docs (`docs.github.com/.../add-skills`, Microsoft Learn) | Project-scope skills live at `.github/skills/`, not `.agents/skills/`; a community discussion (Jan 2026) reports inconsistent auto-discovery requiring `/skills reload`, and disputes about whether an extra metadata file is needed — flagged as unresolved/conflicting community reports vs. official docs | 2026-07-26 |
| GitHub Copilot | same | T3 | Yes | Yes | Official docs (two GitHub Docs pages) | Personal-skill docs explicitly list `~/.copilot/skills` **or** `~/.agents/skills` as accepted locations | 2026-07-26 |
| Cursor | Skills feature since v2.4 (~Jan 2026); docs pages JS-rendered, not fully fetchable | T1 | Unknown | Unknown | Cursor Docs "Rules" page (partial fetch) + secondary sources | `@filename` inclusion is documented for rules, but scope restriction (repo-only vs. absolute) is not stated in the retrieved text; flagged as unverified | 2026-07-26 |
| Cursor | same | T2 | Unknown (leans No) | Unknown | Vendor-adjacent (a Cursor DevRel X/Twitter post, Jan 2026) + a filed GitHub bug (Feb 2026) | Confirmed native paths: `.cursor/skills/`, `.claude/skills/` (project); `~/.cursor/skills/`, `~/.claude/skills/` (global). No first-party page found confirming `.agents/skills/` at project scope | 2026-07-26 |
| Cursor | same | T3 | No | — | GitHub issue `vercel-labs/skills#421` (filed 2026-02-25) | Bug report explicitly states Cursor does not load skills installed at `~/.agents/skills/`, only `~/.cursor/skills/` (and Claude/Codex-compatible paths) | 2026-07-26 |
| Google Antigravity | Antigravity 2.0 v2.4.2 / IDE v2.1.1 / CLI v1.1.6 | T1 | Unknown | Unknown | Official docs site navigation reviewed (`antigravity.google/docs/*`); no import/include mechanism documented | No evidence found either way; flagged as unverified rather than negative | 2026-07-26 |
| Google Antigravity | same | T2 | Yes | Yes | Official docs (`antigravity.google/docs/skills`) | Exact path `<workspace-root>/.agents/skills/<skill-folder>/`; docs state Antigravity now defaults to `.agents/skills` with legacy fallback to `.agent/skills` (singular) | 2026-07-26 |
| Google Antigravity | same | T3 | Partial | Partial | Same docs | Global skills load, but from `~/.gemini/config/skills/`, not the literal `~/.agents/skills/` specified in the brief — a real but differently-pathed T3 mechanism | 2026-07-26 |
| Gemini CLI | Docs current, skills feature GA | T1 | Yes | Yes | Official docs (`github.com/google-gemini/gemini-cli/.../gemini-md.md`, Android Studio docs) | `@file.md` imports in GEMINI.md/AGENTS.md explicitly support absolute paths (e.g. `@/absolute/path/to/file.md`) | 2026-07-26 |
| Gemini CLI | same | T2 | Yes | Yes | Official docs (`github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md`) | `.agents/skills/` is a documented first-class alias to `.gemini/skills/`, taking precedence within the same tier; activation requires the model to call an `activate_skill` tool and the user to approve a UI consent prompt | 2026-07-26 |
| Gemini CLI | same | T3 | Yes | Yes | Same docs | `~/.agents/skills/` is the documented user-tier alias; same consent-gated activation applies | 2026-07-26 |

---

## 3. Per-host detail

### 3.1 Claude Code

**T1 — out-of-repo pointer.** Claude Code's `CLAUDE.md` supports an `@path` import syntax that explicitly accepts both relative and absolute filesystem paths; imported content is expanded and loaded into context at session launch alongside the referencing file. This means a shim whose body is `Read and execute @/abs/path/outside/repo/workflow.md` would be **resolved** by the host itself (not merely by model-initiated file reads) — the content is mechanically substituted before Claude ever sees the raw shim. There is a consent gate: the *first* time a session encounters an external import, an approval dialog appears; declining leaves imports disabled for that session with no automatic re-prompt (users must manually re-approve). Because the imported content becomes ordinary conversational context rather than an enforced instruction, "followed" still depends on normal instruction-following, but this is the standard mechanism CLAUDE.md instructions already rely on, so it should be treated as functionally equivalent to in-repo CLAUDE.md content once loaded.
*(Source: code.claude.com/docs/en/memory)*

**T2 — host-native skills at the literal `.agents/skills/` path.** Claude Code's documented skill-discovery locations are Enterprise (managed settings), Personal (`~/.claude/skills/`), Project (`.claude/skills/`), and Plugin (`<plugin>/skills/`). `.agents/skills/` is not among them. A file placed at `.agents/skills/<name>/SKILL.md` with no other pointer will **not** be auto-discovered by Claude Code. The equivalent, host-native mechanism at `.claude/skills/<name>/SKILL.md` **is** auto-discovered and acted on, including nested per-directory discovery in monorepos and live file-watching within a session.
*(Source: code.claude.com/docs/en/skills)*

**T3 — home-dir/global.** Same conclusion as T2 but for personal scope: `~/.claude/skills/` is real and auto-discovered; `~/.agents/skills/` is not documented as a discovery path for Claude Code.

**Precedence/shadowing.** When skills of the same name exist at multiple levels, enterprise overrides personal, which overrides project; a skill at any level overrides a bundled skill of the same name. Project-level skill activation additionally requires accepting a workspace-trust dialog the first time.

**Reliability caveats.** Skill listings are budget-capped (roughly 1% of the model's context window by default); when the cap is exceeded, descriptions for least-used skills are silently trimmed first, which can suppress a skill's activation without any error. New top-level skill directories require a Claude Code restart to be picked up; edits to existing skill files are picked up live.

---

### 3.2 OpenCode

**T1 — out-of-repo pointer.** OpenCode does not treat a bare `@path` reference inside `AGENTS.md` as something it auto-parses and inlines — its own documentation is explicit that "OpenCode doesn't automatically parse file references in AGENTS.md." The documented, host-level way to pull in out-of-repo content is the `instructions` array in `opencode.json` (or the global `~/.config/opencode/opencode.json`), which accepts arbitrary filesystem paths, glob patterns, and even remote URLs (fetched with a 5-second timeout); everything listed there is combined with `AGENTS.md` content. So: a config-driven out-of-repo pointer is **resolved and followed** by the host; a bare `@path` shim placed directly in `AGENTS.md` is **not** resolved by OpenCode itself — the maintainer's suggested workaround is to write explicit natural-language instructions telling the model to use its Read tool on such references, which then depends on ordinary model behavior rather than a guaranteed host mechanism.
*(Source: opencode.ai/docs/rules/)*

**T2 — host-native skills at `.agents/skills/`.** Confirmed exactly as specified in the brief. OpenCode walks up from the current working directory to the git worktree root, loading any matching `skills/*/SKILL.md` under `.opencode/`, and any matching `.claude/skills/*/SKILL.md` or `.agents/skills/*/SKILL.md` found along the way — with no separate pointer required.
*(Source: opencode.ai/docs/skills/)*

**T3 — home-dir/global.** Also confirmed exactly: global definitions load from `~/.config/opencode/skills/*/SKILL.md`, `~/.claude/skills/*/SKILL.md`, and `~/.agents/skills/*/SKILL.md`.

**Precedence/shadowing.** For rule files, the first matching filename wins per category (e.g., `AGENTS.md` beats `CLAUDE.md` if both exist); `~/.config/opencode/AGENTS.md` beats the Claude-compatibility fallback `~/.claude/CLAUDE.md`. For skills, access itself can be gated per-pattern via `allow`/`deny`/`ask` permissions in `opencode.json`.

**Reliability caveats.** Claude Code compatibility (including the `~/.claude/skills/` fallback) can be disabled wholesale via `OPENCODE_DISABLE_CLAUDE_CODE=1` or selectively via `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1`, meaning the presence of a compatible skill path is not a permanent guarantee across environments.

---

### 3.3 Codex CLI (OpenAI)

**T1 — out-of-repo pointer.** Codex's `AGENTS.md` discovery is a pure directory-walk-and-concatenate model: global file in `$CODEX_HOME` (default `~/.codex`), then project files walking from repo root down to the working directory, joined with blank lines. There is no `@include`/`@path` directive. A GitHub feature request (`openai/codex#17401`, filed April 2026) explicitly asks for one, citing Claude Code's and Cursor's existing syntax as precedent, and remains open — confirming this is a real, currently-unaddressed gap rather than an oversight in the documentation search. A shim reading `Read and execute @/abs/path/workflow.md` will **not** be mechanically resolved by the Codex host; it would only be "followed" if the underlying model chooses to read the referenced file using its own filesystem tools, which is model behavior, not a documented host guarantee.
*(Sources: developers.openai.com/codex/guides/agents-md; github.com/openai/codex/issues/17401)*

**T2 — host-native skills at `.agents/skills/`.** Confirmed exactly as specified. Codex scans `.agents/skills` in every directory from the current working directory up to the repository root (`$CWD/.agents/skills`, intermediate parents, and `$REPO_ROOT/.agents/skills`), with no additional pointer needed. If two skills share a name, Codex does not silently merge or override — both remain selectable, which avoids silent shadowing at the cost of possible duplicate-name confusion.
*(Source: developers.openai.com/codex/skills.md)*

**T3 — home-dir/global.** Confirmed: `$HOME/.agents/skills` (USER scope) is a documented discovery location, alongside an ADMIN-tier `/etc/codex/skills` for machine-wide skills and a SYSTEM tier bundled with Codex itself.

**Precedence/shadowing.** Codex's AGENTS.md model is override-by-locality (files closer to the working directory win) but skills are not deduplicated by name across scopes — an explicit design choice documented by OpenAI.

**Reliability caveats.** The initial skills list shown to the model is capped at 2% of the context window (or 8,000 characters if the window size is unknown); with many installed skills, descriptions are shortened first, and some skills may be omitted from the list entirely with a warning. Skill changes are detected automatically in most cases, but the docs note a restart may be required if an update doesn't appear.

---

### 3.4 GitHub Copilot (CLI / VS Code agent mode / cloud coding agent)

**T1 — out-of-repo pointer.** This is a **documented negative result**. GitHub's own docs for Copilot CLI custom instructions state that `@`-style file references inside `.github/copilot-instructions.md`, `AGENTS.md`, or `CLAUDE.md` are read immediately and support nested references — but only when the referenced file **stays inside the repository**, or inside the custom-instructions directory for personal/local instructions. The same page explicitly says absolute paths and paths beginning with `~/` are **not loaded**. This is a clean, host-documented refusal to resolve out-of-repo pointers via this mechanism — not merely an omission.
*(Source: docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)*

**T2 — host-native skills at `.agents/skills/`.** Copilot's project-scope skill path is `.github/skills/<name>/SKILL.md`, not `.agents/skills/`. A skill placed only at `.agents/skills/<name>/SKILL.md` with no pointer will **not** be discovered by Copilot at project scope. The `.github/skills/` mechanism itself works as intended: Copilot lists available skills by name/description, and when it selects one, injects the full `SKILL.md` body into the agent's context. A community discussion thread (January 2026) reports friction — some users needed `/skills reload` after adding files, and there was confusion (later partially resolved in the thread) about whether an additional metadata file beyond `SKILL.md` was required; this is flagged as a community-reported inconsistency that partially contradicts the cleaner picture in official docs, rather than as an established fact.
*(Sources: docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills; learn.microsoft.com/en-us/visualstudio/ide/copilot-agent-skills; github.com/orgs/community/discussions/183396)*

**T3 — home-dir/global.** Confirmed as specified. Two separate official GitHub Docs pages state that personal skills, shared across projects, can be placed at `~/.copilot/skills` **or** `~/.agents/skills` in the local home directory — meaning Copilot does recognize the literal T3 path from the brief, even though it does not recognize the literal T2 path.

**Precedence/shadowing.** Copilot's instruction layers (personal GitHub.com settings, path-scoped `*.instructions.md`, repo-wide `copilot-instructions.md`, `AGENTS.md`, org-level policy) are documented as merging together, with higher-priority layers winning only where they directly conflict with a lower layer on the same point — not suppressing lower layers wholesale.

**Reliability caveats.** Path-specific custom instructions (`*.instructions.md` with `applyTo`) are, per GitHub's own docs, currently only supported for the Copilot cloud agent and Copilot code review — not uniformly across every Copilot surface. Skill and instruction behavior differs somewhat between Copilot CLI, VS Code agent mode, JetBrains, and the cloud coding agent; this report treats Copilot CLI as the primary reference surface since it has the most complete official documentation, and flags that IDE-specific nuances were not separately verified here.

---

### 3.5 Cursor

Cursor is the host with the thinnest first-party documentation retrievable in this pass — its main docs pages (`cursor.com/docs/rules`, `cursor.com/docs/skills`) are JavaScript-rendered and returned largely empty content on direct fetch, so this section leans more heavily on secondary sources, a vendor DevRel social post, and public GitHub issues than the other hosts. Confidence here is correspondingly lower.

**T1 — out-of-repo pointer.** Cursor's Rules docs confirm `@filename` is used to pull files into a rule's context, and this same `@`-mention mechanism is used to manually invoke rules in chat. However, the retrieved documentation text does not state whether `@`-references are restricted to the repository (as Copilot explicitly is) or permit absolute/home-directory paths (as Claude Code and Gemini CLI explicitly do). This is marked **Unknown** rather than assumed either way.
*(Source: cursor.com/docs/rules, partial fetch)*

**T2 — host-native skills at `.agents/skills/`.** The clearest first-party signal found is a January 2026 post from a Cursor developer-relations account stating Agent Skills in Cursor support `.cursor/skills/` (project), `.claude/skills/` (project, Claude-compatibility), `~/.cursor/skills/` (global), and `~/.claude/skills/` (global) — with no mention of `.agents/skills/` at either scope. No official Cursor documentation page confirming `.agents/skills/` support was found in this pass, though some third-party aggregator sites claim Cursor "also reads from `.agents/skills/`." Given the direct conflict between a first-party statement (silent on `.agents/skills/`) and third-party claims (asserting support), and given the confirmed negative for the home-dir case (below), this is marked **Unknown, leaning Not-resolved** for project scope.

**T3 — home-dir/global.** This is a **documented negative result**, not merely an absence of evidence. A bug report filed against a third-party skill-installer tool (`vercel-labs/skills#421`, filed 2026-02-25) states plainly that Cursor's official global-skill support is limited to `~/.cursor/skills` (with compatibility for `~/.codex/skills` and `~/.claude/skills`) and does **not** extend to `~/.agents/skills` — the bug being that the installer was defaulting to the unsupported path. This is a maintainer/community-confirmed negative for the literal T3 path specified in the brief.
*(Source: github.com/vercel-labs/skills/issues/421)*

**Precedence/shadowing.** For rules, Cursor's documented precedence order is Team Rules → Project Rules → User Rules, with all applicable rules merged and earlier sources in that order taking priority on conflicts. Cursor also natively reads `AGENTS.md` (including nested subdirectory files, more-specific instructions taking precedence over less-specific ones), positioned as a simpler, portable alternative to `.cursor/rules`.

**Reliability caveats.** Agent Skills support in Cursor is very recent (introduced in v2.4, reported as of January 2026) and appears to still be actively changing — a Cursor community forum post from mid-January 2026 notes that creating a "New Cursor Rule" now generates a `SKILL.md` under `.cursor/skills` by default even though Cursor's own docs at the time still described skills as nightly-only, suggesting the officially documented state and the shipped behavior were out of sync at that point. Any claim about Cursor's skills behavior should be treated as version-sensitive and re-verified against the specific Cursor build in use.

---

### 3.6 Google Antigravity

**T1 — out-of-repo pointer.** No documentation was found in this pass describing an `@`-style import/include mechanism for Antigravity's rules or AGENTS.md-equivalent files that would resolve a pointer to a path outside the workspace. This is recorded as **Unknown** — an absence of evidence, not evidence of absence — since Antigravity's docs are extensive on skills but the "Rules" and "Rules/Workflows" pages were not deeply fetched in this pass.

**T2 — host-native skills at `.agents/skills/`.** Confirmed exactly as specified, directly from Antigravity's official documentation: workspace-specific skills live at `<workspace-root>/.agents/skills/<skill-folder>/`, discovered with no separate pointer required. The docs explicitly note that Antigravity "now defaults to `.agents/skills`, but still maintains backward support for `.agent/skills`" (singular) — implying the path changed at some point and both are currently honored.
*(Source: antigravity.google/docs/skills, current version banner: Antigravity 2.0 v2.4.2)*

**T3 — home-dir/global.** Partially confirmed, but at a different path than literally specified. Antigravity's documented global-skill location is `~/.gemini/config/skills/<skill-folder>/`, not `~/.agents/skills/`. A real, host-native, home-directory skill mechanism exists and is followed — but a workflow author relying on the literal `~/.agents/skills/` path from the brief would find it unsupported for Antigravity specifically, even though the sibling tool Gemini CLI (same underlying model family, same company) does support that exact alias.

**Reliability caveats.** Antigravity's skill activation model — discovery via name/description, then full-content read on activation, then execution — mirrors Claude Code's and Gemini CLI's progressive-disclosure pattern, and is described as the agent deciding "based on context," i.e., best-effort matching rather than a guaranteed trigger. No consent-gate language (of the kind documented for Gemini CLI) was found in the Antigravity skills page for skill activation specifically, which is worth flagging as a difference worth re-checking given how closely related the two products are.

---

### 3.7 Gemini CLI

**T1 — out-of-repo pointer.** Confirmed as a clean **Followed** result. GEMINI.md (and its configurable `AGENTS.md`/`CONTEXT.md` aliases via `context.fileName` in `settings.json`) supports an `@file.md` import syntax that is explicitly documented to accept absolute paths, e.g. `@/absolute/path/to/file.md`, in addition to relative paths like `@./components/instructions.md` and `@../shared/style-guide.md`. Imports are recursive and content is inlined into context at the point of reference. A related open GitHub issue (`google-gemini/gemini-cli#15544`, filed December 2025) requesting *recursive* imports specifically for shared conventions across projects suggests deeper nesting edge cases were still being refined as of that filing, though basic absolute-path import is documented as working.
*(Sources: github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md; developer.android.com/studio/gemini/agent-files)*

**T2 — host-native skills at `.agents/skills/`.** Confirmed exactly and unambiguously, directly from the official Gemini CLI GitHub repository docs. Workspace-tier skills are discovered at `.gemini/skills/` **or** the `.agents/skills/` alias, with `.agents/skills/` explicitly documented to take precedence over `.gemini/skills/` when both exist and share a skill name at the same tier. The docs frame `.agents/skills/` explicitly as "an interoperable path for managing agent-specific expertise that remains compatible across different AI tools" — i.e., Google designed this alias specifically to support the kind of tool-agnostic workflow-sharing scheme described in the research prompt's background.
*(Source: github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md)*

**T3 — home-dir/global.** Confirmed exactly: user-tier skills load from `~/.gemini/skills/` **or** the `~/.agents/skills/` alias, with the same precedence rule (alias wins within a tier).

**Precedence/shadowing.** Full documented precedence order, lowest to highest: built-in skills < extension-bundled skills < user skills < workspace skills. Within the user or workspace tier, the `.agents/skills/` alias beats the `.gemini/skills/` directory if both define a same-named skill.

**Reliability caveats.** This is the one host in this report with an explicit, documented **consent gate on activation, not just on installation**: when the model decides to activate a skill, it must call an `activate_skill` tool, and the user is shown a confirmation prompt naming the skill and the directory it will gain file-access to, before the `SKILL.md` body is added to context. This means even a perfectly-discovered, host-native skill is not silently "followed" — a human must approve activation in an interactive session (behavior in fully non-interactive/headless invocations was not confirmed in this pass and should be checked separately if the target workflow needs unattended operation).

---

## 4. Recommendations and caveats

**Tiers that look safe to build on today, per host, based on current documentation:**

- **If your target is Codex CLI, OpenCode, or Gemini CLI:** the literal `.agents/skills/` (project) and `~/.agents/skills/` (global) paths from the brief are all first-party, currently-documented, no-extra-pointer-required mechanisms. This is the strongest and most portable result in the report — three independently-built hosts converge on the identical literal path.
- **If your target also includes Google Antigravity:** the project-level `.agents/skills/` path also works, but the global path does not — plan for a separate `~/.gemini/config/skills/` fallback if you need Antigravity's global tier specifically.
- **If your target also includes GitHub Copilot:** the global `~/.agents/skills` path is documented and should work, but the project-level path must be `.github/skills/`, not `.agents/skills/` — a workflow that only ships to `.agents/skills/` at project scope will silently fail to be discovered by Copilot even though it works for four other hosts.
- **If your target also includes Claude Code:** neither the project nor the global literal `.agents/skills/` path is auto-discovered; ship to `.claude/skills/` and `~/.claude/skills/` instead (which is also read by OpenCode and Cursor as a compatibility fallback, so this isn't wasted effort for a multi-host strategy).
- **If your target also includes Cursor:** treat both T2 and T3 for Cursor as unsupported until independently re-verified against the exact Cursor build in use; the one first-party signal found lists `.cursor/skills/` and `.claude/skills/` only, and a maintainer-filed bug explicitly rules out `~/.agents/skills/`.

**T1 (out-of-repo pointer) is the least portable tier.** It is genuinely host-resolved (not just model-followed) only in Claude Code, Gemini CLI, and OpenCode-via-config. It is explicitly and deliberately blocked in GitHub Copilot CLI (a real security/scoping decision, not an oversight), and simply doesn't exist as a host feature in Codex CLI (though a feature request is open). For Cursor and Antigravity, the honest state is "unknown" — this report could not confirm or deny it from available documentation, and it should not be assumed to work in either direction without a live test.

**Where the evidence is genuinely thin and a live test is warranted before shipping anything:**
- Cursor, for all three tiers — official docs pages were not fully retrievable (JavaScript rendering), so this report leans on a single DevRel social post and third-party aggregators of varying reliability.
- Antigravity T1 (no evidence found either way).
- GitHub Copilot's skill-discovery reliability specifically — community reports of needing `/skills reload` and conflicting claims about a required metadata file suggest real friction beyond what the clean official-docs description implies.
- Whether Gemini CLI's activation consent-gate can be bypassed or pre-approved for non-interactive/CI use, which matters if the target workflow needs to run unattended.

**What this report could not do:** actually launch any of these seven hosts and drop a `PROBE-OK.txt`-creating fixture to observe the side effect directly. Every "Followed" verdict above rests on the host vendor's own documentation stating that discovered/imported content is injected into the agent's working context and that the agent is expected to act on it — which is strong evidence but is not the same as a reproduced, timestamped, side-effect-observed test. Anyone building the T1/T2/T3 delivery mechanism described in the brief should validate the specific claims most load-bearing to their design (starting with the Codex/OpenCode/Gemini CLI/Antigravity convergence on `.agents/skills/`, since that is the basis for the biggest footprint reduction) with an actual fixture-drop test before relying on it in production tooling.

---

## 5. Sources

1. Claude Code — Extend Claude with skills. https://code.claude.com/docs/en/skills — accessed 2026-07-26
2. Claude Code — How Claude remembers your project (CLAUDE.md imports). https://code.claude.com/docs/en/memory — accessed 2026-07-26
3. Claude Code — Documentation Index / skills.md raw. https://code.claude.com/docs/en/skills.md — accessed 2026-07-26
4. OpenCode — Agent Skills. https://opencode.ai/docs/skills/ — accessed 2026-07-26 (page states "Last updated: Jul 24, 2026")
5. OpenCode — Rules. https://opencode.ai/docs/rules/ — accessed 2026-07-26 (page states "Last updated: Jul 24, 2026")
6. OpenAI Codex — Build skills. https://developers.openai.com/codex/skills.md — accessed 2026-07-26
7. OpenAI Codex — Custom instructions with AGENTS.md. https://developers.openai.com/codex/guides/agents-md — accessed 2026-07-26
8. GitHub — `openai/codex` Issue #17401, "feat: @include directive for composable AGENTS.md files." https://github.com/openai/codex/issues/17401 — filed 2026-04-11, accessed 2026-07-26
9. GitHub Docs — Adding custom instructions for GitHub Copilot CLI. https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions — accessed 2026-07-26
10. GitHub Docs — Adding agent skills for GitHub Copilot CLI. https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills — accessed 2026-07-26
11. GitHub Docs — Adding agent skills for GitHub Copilot (cloud agent). https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills — accessed 2026-07-26
12. Microsoft Learn — Use Agent Skills with GitHub Copilot (Visual Studio). https://learn.microsoft.com/en-us/visualstudio/ide/copilot-agent-skills — accessed 2026-07-26
13. GitHub — Community Discussion #183396, "How to Add Agent Skills in Copilot CLI." https://github.com/orgs/community/discussions/183396 — accessed 2026-07-26
14. Cursor Docs — Rules. https://cursor.com/docs/rules — accessed 2026-07-26 (partial fetch, JS-rendered)
15. Cursor Docs — Agent Skills (page reference only; full content not retrievable). https://cursor.com/docs/skills — accessed 2026-07-26
16. Daniel San (Cursor DevRel) — X/Twitter post on Cursor Agent Skills paths. https://x.com/dani_avila7/status/2010814983026733119 — posted 2026-01-12, accessed 2026-07-26
17. GitHub — `vercel-labs/skills` Issue #421, "The default installation directory for Cursor global skills is incorrect." https://github.com/vercel-labs/skills/issues/421 — filed 2026-02-25, accessed 2026-07-26
18. Google Antigravity Docs — Agent Skills. https://antigravity.google/docs/skills — accessed 2026-07-26 (version banner: Antigravity 2.0 v2.4.2)
19. Gemini CLI (google-gemini/gemini-cli) — Agent Skills. https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md — accessed 2026-07-26
20. Gemini CLI (google-gemini/gemini-cli) — Provide context with GEMINI.md files. https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md — accessed 2026-07-26
21. Android Developers — Customize Gemini using AGENTS.md files. https://developer.android.com/studio/gemini/agent-files — accessed 2026-07-26
22. GitHub — `google-gemini/gemini-cli` Issue #15544, "Support Recursive Imports in Context Files (GEMINI.md)." https://github.com/google-gemini/gemini-cli/issues/15544 — filed 2025-12-25, accessed 2026-07-26

**Sources consulted but not cited as primary evidence** (secondary/aggregator sites used only for triangulation, not as sole support for any claim in the executive summary or results table): agensi.io (multiple pages on skill directory locations for Cursor, OpenCode, Gemini CLI), promptspace.in, agentskills.me, thepromptindex.com, codex.danielvaughan.com, agentpatterns.ai, wmedia.es, hackernoon.com, inventivehq.com, agyn.io.
