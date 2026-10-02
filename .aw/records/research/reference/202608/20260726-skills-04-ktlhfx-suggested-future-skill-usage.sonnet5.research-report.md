---
id: ktlhfx
created: 20260802
set: skills
order: 04
topic: []
model: sonnet5
kind: research-report
status: reference
outcome: informational
summary: Migrated from 20260726-skills-04-ktlhfx-suggested-future-skill-usage.sonnet5.research-report.md.
consumed-by: []
---
# Suggested Future Skill Usage for `fariello/agent-workflows`

**Prepared by:** Claude Sonnet 5
**Date:** July 26, 2026
**Inputs:** the live `fariello/agent-workflows` repository (README as of this date); the reconciliation of four independent reports on agent-workflows' clean-delta/delivery architecture (`20260726-0054-05-aw-delivery-and-clean-delta_reconciliation-report.md`); the reconciliation of four independent reports on the external-delivery host probe (`20260726-1045-05-external-delivery-host-probe_reconciliation-report.md`).

**What this document is:** a single, opinionated synthesis of where `agent-workflows` should end up on skill usage, host delivery, and the clean-delta/tracked split — reasoned from the two reconciliation reports rather than from either individual source report or model. Where this changes or corrects something I said in this conversation earlier today, that is called out explicitly rather than silently revised.

**What this document is not:** a replacement for the reconciliation reports' own detail. Where a recommendation here compresses a longer discussion, the relevant section number in the delivery reconciliation report is cited so you can go back to the full reasoning.

---

## 1. Executive summary

1. **Make host-native skills the primary cross-agent delivery mechanism**, not the manual "Read and execute `.agents/workflows/<path>`" instruction that today's README treats as the universal fallback for Codex, Cursor, Antigravity, and VS Code Copilot. Current first-party documentation, reconciled across four independent probes, now supports a shared `.agents/skills/<name>/SKILL.md` project root for OpenCode, Codex, GitHub Copilot (CLI and VS Code), Cursor (provisionally), Antigravity, and Gemini CLI. Only Claude Code needs a different native root (`.claude/skills/`).
2. **Do not convert every workflow into a skill.** Split the sixteen-plus workflows into three buckets: portable capability skills (auto-triggerable, safe, one skill each), explicit harness skills (one skill per harness — `assess`, `advise` — not one per lens or persona), and non-skill always-on guidance that stays in `AGENTS.md`. This is the one point every source report agrees on.
3. **Treat "Read and execute" as a last resort, not a co-equal delivery path.** It should remain only for the specific host/tier combinations where skills are genuinely unresolved (Codex T1, Copilot CLI T1) or still unverified (Cursor and VS Code Copilot's arbitrary-absolute-path T1), not as a blanket fallback once skills exist.
4. **The clean-delta initiative and the skills initiative are the same architectural decision**, not two separate roadmap items. Once workflows are delivered as user-global skills rather than in-repo shims, clean-delta contribution stops being a special mode and becomes the *default* consequence of how delivery works. This is worth internalizing before you build either one in isolation.
5. **Nothing here should be shipped from documentation alone.** Both reconciliation reports converge on the same warning: no report supplied a reproducible fixture test (a real host, a real version, a nonce file, an observed side effect). Every recommendation below is "current first-party documentation supports this," not "this has been observed to work." Section 8 gives the fixture protocol both reports independently converged on.

---

## 2. Reconciled host delivery matrix

This supersedes the host matrix in my earlier standalone research in this conversation (the `external-delivery-host-probe_research-prompt.md` report). Two things changed since that report: newer host releases were checked, and the reconciliation applied the brief's own tier definitions more consistently (an "equivalent native path" counts as tier support even when the literal `.agents/skills/` string doesn't apply — my earlier report was sometimes stricter than the brief actually asked for, e.g. on Copilot's `.agents/skills/` support).

| Host (pinned version where known) | T1 — out-of-repo pointer | T2 — host-native skill | T3 — home/global | Confidence |
|---|---|---|---|---|
| OpenCode 1.18.5 | **Not-resolved** for a passive `@path` in `AGENTS.md`. **Followed via a different mechanism** — the `opencode.json` `instructions` array | **Followed** from `.agents/skills/` | **Followed** | High |
| Claude Code 2.1.220 | **Followed**, after a one-time external-import approval dialog | **Followed** at `.claude/skills/` — `.agents/skills/` is *not* a native Claude root | **Followed** | High |
| OpenAI Codex CLI 0.145.0 | **Not-resolved** by the documented `AGENTS.md` loader (no `@include` exists) | **Followed** from `.agents/skills/` | **Followed** | High |
| GitHub Copilot CLI | **Not-resolved** for absolute and `~/` imports — explicitly refused by design | **Followed** from `.github/skills/`, `.claude/skills/`, or `.agents/skills/` | **Followed** | High |
| GitHub Copilot in VS Code 1.130 | **Unknown** for an arbitrary absolute file outside the workspace | **Followed** from the same three roots as CLI | **Followed** | High for T2/T3; medium for T1 |
| Cursor 3.11 | **Unknown** for a passive absolute out-of-workspace `@filename` | **Followed provisionally**, including `.agents/skills/` per current docs — re-verify exact roots before relying on it | **Followed** through user skills or User Rules | Medium |
| Google Antigravity 2.0 v2.4.2 | **Followed** — Rules explicitly support true absolute `@filename` resolution | **Followed** from `.agents/skills/` | **Followed**, but at `~/.gemini/config/skills/`, not `~/.agents/skills/` | High |
| Gemini CLI 0.52.0 | **Followed** — `GEMINI.md`/`AGENTS.md` imports explicitly support absolute paths | **Followed after activation consent**, from `.agents/skills/` or `.gemini/skills/` | **Followed**, same consent gate | High |

**The one universal caveat that applies to every row:** "Followed" here means *current first-party documentation states the host does this*, not that any of the four source reports (or my own earlier research) actually ran the host and watched a file get created. Section 8 below exists because of this gap.

**What this means concretely for the repo's design:** a single `.agents/skills/<name>/SKILL.md` tree, shipped alongside a `.claude/skills/<name>/SKILL.md` mirror for Claude Code, now covers host-native, no-pointer-required discovery for all seven host families in the brief. That is a materially stronger position than the repo's current README describes ("Codex, Cursor, Antigravity, VS Code Copilot: ... tell the agent 'Read and execute ...'") — three of those four hosts (Codex, Antigravity, and — provisionally — Cursor and VS Code Copilot) can now discover a skill with zero user action at all.

---

## 3. Skill taxonomy for this repo's actual workflows

All four source reports in the delivery reconciliation converge on rejecting "one skill per workflow, mechanically." The reconciled taxonomy is three buckets (delivery reconciliation §7.3). Mapped onto the real workflow list from the repo's own README:

### 3.1 Portable capability skills — one skill each, safe to auto-trigger where the host allows it

These are read-only or clearly-scoped, high-frequency, and don't do anything a user would be surprised by if the model decided to run them proactively:

| Workflow | Recommended skill | Auto-invoke? |
|---|---|---|
| `plan-review` | `plan-review` skill | Yes — reviewing a plan before code exists is low-risk |
| `verify` | `verify` skill | Yes, with tool-approval prompts preserved (it already confirms per-check) |
| `spec` | `spec` skill | Yes — "this request looks under-specified" is a good proactive trigger |
| `list-workflows` | `list-workflows` skill | Yes — pure discovery, no side effects |
| `getting-started` | `getting-started` skill | Yes — orientation only, explicitly read-only today |

`verify-execution`, `release-review-plan`, and `scaffold` are reasonable second-wave additions to this bucket — all either read-only or scoped to framework files rather than the user's code.

### 3.2 Explicit harness skills — one skill per harness, never one per lens or persona

This is the most consequential correction across all four source reports for the delivery reconciliation, and it directly overturns the more permissive framing I gave in the earlier conversation turn (I suggested "one skill per concern, e.g. `assess-security`, `assess-performance`..."). The reconciled position (§7.2–7.3) is more conservative and, on reflection, more correct:

> Registry explosion is a real cost. Twenty lens-skills and seven persona-skills competing for the same "does this match?" decision creates false-trigger risk and a bloated always-in-context skill listing, for benefit that a single well-described dispatcher skill already provides.

So:

| Harness | Recommended skill | Auto-invoke? | Notes |
|---|---|---|---|
| `assess <concern>` | **one** `assess` skill that accepts a concern argument and loads the matching lens from `.agents/workflows/assess/lenses/` at activation time | No (or narrow, tested description only) | Where a host supports disabling model-invocation (Claude Code, Cursor), set it. Where it doesn't (OpenCode's skill frontmatter has no such field), rely on a narrow description and test trigger behavior before shipping. |
| `advise <persona>` | **one** `advise` skill that accepts a persona argument and loads the matching charter from `.agents/workflows/advise/personas/` | No | Same reasoning — coaching/interrogation workflows shouldn't fire without being asked. |
| `assess-all` | keep as a command/manual invocation, not a skill | No | This is a deliberately expensive, multi-concern rollup — it should never be something the model decides to run on its own. |

This preserves the current UX (`/assess security`, `/assess performance`) exactly — the skill *is* the dispatcher, parameterized the same way the command is today — it just adds the benefit of the model being able to *suggest* running it in hosts that support skill-based reasoning, without creating twenty separate discoverable entities.

### 3.3 Consequential/side-effecting workflows — keep manual-invocation-only, whether or not they're wrapped as skills

| Workflow | Status | Reasoning |
|---|---|---|
| `setup-repo` | Manual-only | Makes real repo changes; today's confirm-per-step design should not become "the model decided to run this" |
| `release-review` | Manual-only | Fixes in place — same reasoning |
| `migrate` | Manual-only | High-risk migration planning; should never be model-initiated |
| `incident` | Manual-only | Post-mortems are a deliberate human act |
| `release-notes` | Manual-only | Touches changelog/version files |
| `scaffold` | Manual-only (borderline) | Framework-file-only blast radius is smaller, but still a deliberate authoring act |

Wherever a host provides a "disable model invocation" flag (Claude Code's `disable-model-invocation: true`; Cursor has an equivalent per the reconciliation), set it on all six of these, whether they're shipped as skills or remain plain commands. Where the host has no such flag (OpenCode's skill frontmatter is limited to `name`, `description`, `license`, `compatibility`, `metadata` — there is no manual-only field), the safer choice for these six is to **not** ship them as auto-discoverable skills at all; keep them as `.opencode/commands/` shims exactly as today, since a skill listing with no invocation gate is a strictly worse position than a command that requires the user to type `/release-review`.

### 3.4 Non-skill always-on guidance

Only the genuinely universal, short conventions belong in the always-loaded `AGENTS.md` pointer block (and its `CLAUDE.md`/`GEMINI.md` mirrors) — not the workflow catalog, not lens descriptions, not persona charters. This is already roughly how the repo's `AGENTS.md` pointer works; the recommendation is to resist the temptation to grow it once skills exist, since skills' entire value proposition is that detailed content shouldn't be always-resident.

---

## 4. Two coherent product modes, not independent toggles

This is the single most important structural point in the delivery reconciliation (§17.1), and it reframes the skills question rather than sitting alongside it:

> Keep two coherent modes — **tracked** and **clean-delta** — and do not expose independent low-level toggles that can create incoherent combinations such as an untracked manifest with tracked shims.

Applied to skill delivery specifically:

### 4.1 Tracked mode (today's default)

- Continue generating `.opencode/commands/` and `.claude/commands/` shims as today.
- **Add** generated `.agents/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md` trees, populated from the same canonical `.agents/workflows/<name>/` bodies — generated artifacts, not hand-forked content, exactly like the existing no-clobber/idempotent command-shim generation.
- Keep the `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` pointer block and the "Read and execute" instruction as the fallback for the specific host/tier cells that are still Not-resolved or Unknown in §2 above (Codex T1, Copilot CLI T1, and — until independently tested — Cursor/VS Code Copilot T1).
- This mode still writes files into the target repo, so it is not what makes clean-delta contribution possible on its own.

### 4.2 Clean-delta mode

This is where skill delivery actually earns its keep. The delivery reconciliation's clean-delta architecture (§4.5, §17) depends on skills being resolvable *without any file written into the target repository at all*:

```text
User-scope host skill (installed once, at the documented T3 path)
    -> agent-workflows resolver
    -> packaged workflow or harness body
    -> target repository as code context only
    -> companion (sibling) repository as artifact root
```

Concretely, for clean-delta mode:

1. Install skills at the **T3 (user-global) paths** from §2 — `~/.claude/skills/`, `~/.agents/skills/` (covers OpenCode, Codex, Copilot, Gemini CLI, and provisionally Cursor), and `~/.gemini/config/skills/` for Antigravity specifically. No project-level `.agents/skills/` or `.claude/skills/` directory is written into the target at all.
2. This installation is **consent-gated and machine-scoped**, not per-repository. A given machine installs the skill set once; each repository the user works in then *registers* as a dependent of that installation (a repo-scoped fact) without re-triggering the consent flow (a machine-scoped fact). Getting this distinction right matters for uninstall: removing a global skill needs to check whether any other registered repository still depends on it before deleting it — this is explicitly one of the requirements the delivery reconciliation flags as commonly under-specified (§8.3, "Global ownership manifest").
3. The target repository's tracked `AGENTS.md`, `.gitignore`, and any other tracked file remain completely untouched — there is no pointer to write, because the host already discovers the skill from its own global skill root, independent of anything in the repo.
4. Developer artifacts (plans, run records, research) route to a sibling companion repository (e.g. `../<repo-name>.aw/`), never into the target, tracked or untracked. Every workflow that currently writes to `.agents/plans/pending/` or `workflow-artifacts/<workflow>/<run-id>/` needs to call a resolver rather than assume the target repo root — see §4.3.
5. Where a host's T1/T2 is genuinely unresolved (Codex, Copilot CLI) and the workflow absolutely needs to reach content that skills can't deliver, the only acceptable fallback is a **locally excluded** (`.git/info/exclude`, never a tracked `.gitignore` or `core.excludesFile`) project file — and only after a host/version-specific test proves the host actually discovers content hidden that way. This is not proven for any host today; treat it as a tested Phase 4 fallback, not a baseline (§4.5, §14.2).

### 4.3 The resolver contract

Both reconciliation reports converge on needing a single deterministic resolver rather than letting each workflow parse configuration independently (delivery reconciliation §9.3):

```bash
agent-workflows context --repo "$PWD" --json
```

returning target root, install mode, companion root, per-artifact-class routes, effective framework version, enabled host integrations, and whether the *current* command may commit in the target, the companion, neither, or both. Every workflow — skill-delivered or command-delivered — should call this rather than hardcoding `.agents/plans/pending/` as a target-relative path. This is a prerequisite for clean-delta mode to work at all, independent of the skills question, and should land in the same phase as the skill-generation work (see §7).

---

## 5. Per-host delivery policy

Combining the T1/T2/T3 verdicts from §2 into an actual "what do we generate, and where" table:

| Host | Primary delivery (T2/T3) | Fallback policy (T1) | Notes for this repo specifically |
|---|---|---|---|
| OpenCode | `.agents/skills/` (project, tracked mode) or `~/.agents/skills/` / `~/.config/opencode/skills/` (user, clean-delta mode) | Do not rely on passive `@path` in `AGENTS.md`. If a true out-of-repo pointer is needed, generate an `opencode.json` `instructions` entry instead. | OpenCode-native `/command` shims can be retired in favor of skills once tested; OpenCode's skill permission model (`allow`/`ask`/`deny`) is the closest thing it has to Claude's manual-invocation flag — use `ask` for the six consequential workflows in §3.3. |
| Claude Code | `.claude/skills/` (project) or `~/.claude/skills/` (user) — **not** `.agents/skills/** | Use a `CLAUDE.md` absolute-path `@import` where a true pointer is unavoidable; document the one-time approval dialog to users so it isn't mistaken for a bug. | Claude Code supports symlinked skill directories (confirmed in current release notes) — worth using so the generated `.claude/skills/` tree doesn't duplicate the canonical `.agents/workflows/` bodies on disk. |
| Codex CLI | `.agents/skills/` (project, CWD to repo root) or `$HOME/.agents/skills/` (user) | No passive `@path` exists; don't build anything that assumes it will appear. `~/.codex/AGENTS.md` remains the right place for genuinely global, always-on instructions. | Codex also supports symlinked skill folders — same dedup opportunity as Claude Code. |
| GitHub Copilot CLI | `.github/skills/`, `.claude/skills/`, or `.agents/skills/` (project); `~/.copilot/skills/` or `~/.agents/skills/` (user) | Absolute and `~/`-relative imports are explicitly refused by design — don't build a fallback that depends on them for this surface. | This is a real, documented refusal, not an unverified gap — treat it differently from Cursor/VS Code Copilot's merely-unknown T1. |
| GitHub Copilot in VS Code | Same three roots as CLI | Unknown for arbitrary absolute out-of-workspace files — needs its own fixture before relying on it either way. | Do not assume CLI and VS Code behave identically just because they share a vendor and a skill-root convention; the reconciliation explicitly treats them as different surfaces. |
| Cursor | Provisionally `.agents/skills/` (project) and native user-skill roots (user) — re-verify exact aliases on the pinned build before shipping | Unknown for passive absolute `@filename` — do not build a release-blocking dependency on it. | Lowest-confidence host in the whole matrix; Cursor's own docs pages were not independently text-extractable during either research pass (JS-rendered). Budget explicit test time here before general availability. |
| Google Antigravity | `.agents/skills/` (project/workspace) or `~/.gemini/config/skills/` (user — **not** `~/.agents/skills/`) | `@filename` absolute-path resolution in Rules is documented and can be used directly. | The global-path mismatch with the literal brief spec is real and easy to miss — don't assume Antigravity's user path matches the other six hosts. |
| Gemini CLI | `.agents/skills/` or `.gemini/skills/` (project); `~/.agents/skills/` or `~/.gemini/skills/` (user) | Absolute `@file.md` imports in `GEMINI.md`/`AGENTS.md` are documented and usable directly. | Skill activation requires a per-activation user consent prompt — this is not a one-time gate like Claude Code's import approval; expect it every time a skill fires, and don't design a workflow that assumes silent activation. |

---

## 6. What this changes from my earlier answer in this conversation

In the interest of not silently revising a position:

1. **I previously suggested converting each `assess` lens and each `advise` persona into its own individually-discoverable skill** (`assess-security`, `advise-red-teamer`, etc.). The reconciled position across all four source reports, and my own re-reading, is more conservative: **one dispatcher skill per harness**, parameterized exactly like the current `/assess <concern>` command, not twenty-plus separate skills. The registry-explosion and false-trigger costs are real and this repo's own README already treats `/assess` and `/advise` as single parameterized commands for good reason — that reasoning transfers directly to skills.
2. **I previously said Cursor "appears to support neither the project nor the global `.agents/skills/` path"** based on a single maintainer-filed bug report about a third-party installer. The reconciliation is more careful here: that bug report establishes a point-in-time installer compatibility problem, not necessarily current Cursor behavior, and current Cursor documentation (medium confidence, since the docs pages are JS-rendered and hard to independently verify) now describes `.agents/skills/` support. The honest position is **"provisionally followed, re-verify on the pinned build"**, not a flat negative.
3. **I previously treated GitHub Copilot's literal `.agents/skills/` project path as unsupported**, recommending `.github/skills/` instead. Current first-party documentation (both the Copilot CLI page and the VS Code Agent Skills page) now lists `.agents/skills/` alongside `.github/skills/` and `.claude/skills/` as accepted project roots. `.github/skills/` is still worth generating for maximum compatibility with older Copilot documentation states, but it's no longer the *only* option.
4. **I hadn't previously separated Copilot CLI from Copilot in VS Code as cleanly as this reconciliation does.** They are different surfaces with different T1 evidence quality (CLI: documented refusal; VS Code: genuinely unknown) — worth keeping distinct in any future host-support documentation this repo publishes.

---

## 7. Suggested phased rollout

Adapting the delivery reconciliation's phase sequence (§14.2) specifically to the skills work:

**Phase 0 — conformance harness (build before promising anything above).**
Exact host/version tests for: skill discovery at the documented T2/T3 paths; explicit vs. automatic invocation; precedence when a same-named skill exists at project and user scope; `.git/info/exclude` discovery (if the fallback path is ever pursued); companion-repository read/write access from within each host's sandbox; local vs. cloud-surface availability; uninstall and edited-file preservation. See §8 for the exact fixture protocol both source reports converged on.

**Phase 1 — resolver and artifact-root abstraction.**
The `agent-workflows context` resolver from §4.3, per-repository global config, companion-repository mapping, global ownership manifest for shared skill installations. This has to exist before clean-delta skill delivery is meaningful, independent of which workflows become skills.

**Phase 2 — portable skills, small and tested first.**
Ship §3.1's bucket first (`plan-review`, `verify`, `spec`, `list-workflows`, `getting-started`) to the documented T2 paths in §5, generated for every host except where §2 marks the tier Unknown or Not-resolved. Add the `assess` and `advise` dispatcher skills from §3.2 once the harness proves invocation-gating behaves as expected per host.

**Phase 3 — clean-delta install and migration.**
Transactional, zero-target-write install using the Phase 1 resolver; explicit `migrate --to-clean-delta` / `migrate --to-tracked` in both directions; same-version verified no-op; recent-undo metadata. This is where the six consequential workflows from §3.3 get their manual-invocation-only skill wrappers (or stay as plain commands on hosts with no invocation-gate field).

**Phase 4 — fallback adapters, only with direct evidence.**
Locally excluded project skills/shims, Claude's `--add-dir` skill discovery as a companion-repository integration path, Antigravity global-workflow ownership if its storage contract proves stable. Nothing in this phase should be assumed working from documentation alone — this is exactly the bucket both reconciliation reports warn against building first.

---

## 8. The fixture protocol to run before any of this ships

Both reconciliation reports arrived at essentially the same required test independently (delivery reconciliation §14.2 "Phase 0"; host-probe reconciliation "Required release fixture"). Before relying on any row in §2 or §5 in production:

1. Clean temporary home directory and empty temporary git repository per host/version under test.
2. Workflow content placed outside every workspace root (for T1) or at the documented T2/T3 path (for T2/T3).
3. A random nonce, with an instruction *only* in that external content, to create `PROBE-OK-<host>-<version>-<nonce>.txt`.
4. Capture host diagnostics that prove resolution independent of the side effect — context/memory/instruction/skill listings, not just the final file.
5. Verify the specific nonce's side effect occurred (not just "a file appeared").
6. Add a conflicting instruction at a second, higher-precedence location producing a *different* nonce, to establish precedence empirically rather than by assumption.
7. Run once with permission denied, once with approval accepted, and — where relevant (Claude Code's import dialog, Gemini CLI's activation consent) — once non-interactively, to see what happens without a human present to click approve.
8. Run the same fixture against both the local surface and, where one exists, the cloud/remote surface — do not assume local T3 skill installation is visible to a cloud session for any host; this is explicitly unconfirmed across the board.
9. Record host version, settings, fixture tree, exact commands, logs, and final filesystem state — "Resolved" should only be recorded from host diagnostics or direct context evidence, and "Followed" only when the unique nonce side effect is actually observed.

Until this has run, every "Followed" verdict in this document — including the ones I'm recommending you build against — should be read as "the best current documentation-based estimate," not as a tested fact.

---

## 9. Open risks this document does not resolve

Carried forward from the host-probe reconciliation's "Remaining unknowns," because they're still unresolved and still relevant to the design above:

- Cursor's exact support and collision behavior across `.agents/`, `.cursor/`, `.claude/`, and `.codex/` skill aliases, at both project and user scope.
- Arbitrary out-of-workspace T1 resolution for Copilot in VS Code and for Cursor — both still genuinely unknown, not just under-documented.
- Duplicate-name skill precedence in OpenCode, Copilot, Cursor, and Antigravity, where primary documentation is incomplete.
- Whether Gemini CLI's per-activation consent gate can be bypassed or pre-approved for non-interactive/CI use — this matters directly for any unattended `agent-workflows` automation.
- Whether machine-local (T3) skill installations are synchronized, copied, or simply unavailable in each host's cloud-agent surface. This is unresolved for every host in the matrix, not just some of them, and should be treated as a hard boundary ("local clean-delta" only) rather than assumed to extend to cloud sessions until proven otherwise.

These should stay as explicit release blockers in whatever tracking this repo uses for the clean-delta and skills work, rather than being quietly assumed away by the time of implementation.
