# IPD: clean-delta contribution and artifact-tracking modes (evidence-grounded DESIGN SPEC, no build)

- Date: 2026-07-23 (fleshed 2026-07-26 from research)
- Concern: let a developer use agent-workflows in a repo they do NOT own and will PR upstream, leaving the upstream repo a clean delta with their own artifacts tracked elsewhere; and, more generally, choose how much agent-workflows footprint a repo carries (tracked, per-class opt-out, or clean-delta)
- Scope: produce the SPEC and phased plan for the two coherent modes (tracked; clean-delta) grounded in the committed research bundle. This IPD produces a DESIGN DOCUMENT ONLY - no product code. It defines the architecture, the per-host delivery decisions, the state/ownership model, migration, the same-version-reinstall behavior, downgrade-preservation, and a phased plan whose Phase 0 (a conformance harness) and later build phases become their OWN separate IPDs. It ABSORBS and records the resolution of IPD 05's deferred open questions. DEPENDS ON / references IPD 01 (manifest), IPD 02 (managed sections), IPD 03 (untracked convention), IPD 04 (conservative uninstall), IPD 05 (external-delivery spec + host-probe).
- Status: to-review
- Set: install-safety-and-ownership
- Order: 7
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-23 created as a draft stub (opencode its_direct/pt3-claude-opus-4.8-1m-us): spun out of the install-manifest discussion as the largest, most invasive piece. Preliminary; needs design discussion.
- 2026-07-25 reframed + blocked on research (opencode its_direct/pt3-claude-opus-4.8-1m-us): established CLEAN-DELTA contribution as the strongest driver (real cases: opencode, hermes, which carry their own AGENTS.md), alongside per-class tracking opt-out, do-not-advertise/low-footprint, and optionally untrackable framework + manifest. Q1 (per-repo manifest with version + checksum) and Q3 (backups for rollback) are ALREADY shipped (D103 manifest + `.agent-workflows-installer-backups/` + `--undo`), so this IPD REFERENCES them, not re-specs them. Because the design space was unresolved, authored research prompts instead of a premature spec and staged them under `.agents/prompts/pending/`. Also recorded a TODO.md backlog item (a "do not hand-edit inside aw:block" AGENTS.md directive).
- 2026-07-26 fleshed to a design spec from research (opencode its_direct/pt3-claude-opus-4.8-1m-us): the research is complete and immortalized at `.agents/docs/research/20260726-0054-aw-delivery-and-clean-delta-research/` (10 files: four clean-delta model reports + reconciliation `...-0054-05`; four host-probe model reports + reconciliation `...-1045-05`). Rewrote this stub into a spec-only IPD grounded in that evidence. Maintainer decisions at fleshing: flesh 07 as a design spec now (build + Phase 0 harness deferred to their own later IPDs); record IPD 05's now-resolved open questions HERE (07 absorbs them) plus the bundle README, leaving executed IPD 05 untouched.

## Goal

Define, from the reconciled evidence, TWO coherent artifact-footprint modes and the architecture that supports them, so a later IPD can build them safely:

- Tracked mode (today's model): agent-workflows content + a tracked per-repo manifest + shims + managed instruction blocks live in the repo and are committed. Unchanged; remains the default for a repo that intentionally adopts agent-workflows.
- Clean-delta mode: NO tracked or baseline local agent-workflows files in the target; the host discovers workflows via user-scope host-native skills; the developer's own artifacts (IPDs, prompts, research, run records) are tracked in a developer-owned SIBLING companion repository; authoritative per-repo mode/routing lives in user-global agent-workflows config; a separate global ownership manifest owns any shared user-scope host files.

Do NOT expose independent low-level toggles that can create incoherent states (e.g. an untracked manifest with tracked shims). Per-class opt-out and do-not-advertise are motivations SERVED by these two modes (plus the existing per-file `.untracked.` convention and the `local/` lanes for the sensitive subset), not separate mechanisms.

Why it matters: a developer contributing upstream (opencode, hermes) must leave the upstream repo a clean delta - no agent-workflows file, managed block, ignore rule, manifest, instruction edit, backup, or artifact in the pull request - while still fully using agent-workflows and tracking their own work. The research shows this is achievable TODAY on documented host behavior via host-native skills, but only if the build is gated on a live conformance harness first.

## Evidence base (committed research)

All claims below trace to `.agents/docs/research/20260726-0054-aw-delivery-and-clean-delta-research/`:

- Clean-delta reconciliation: `20260726-0054-05-aw-delivery-and-clean-delta.reconciliation-report.md`.
- Host-probe reconciliation: `20260726-1045-05-external-delivery-host-probe.reconciliation-report.md`.
- Eight underlying model reports (gpt56, gemini36flash, gemini31pro, sonnet5 for each set).

Grade: DOCUMENTATION-GRADED as of 2026-07-26. No report ran a live fixture, so every host verdict means "documented", not "reproduced". This is the single most important constraint on the phased plan (Phase 0).

## Findings (drivers; from the reconciliations)

| ID | Severity | Persona | Area | Finding | Evidence |
|----|----------|---------|------|---------|----------|
| C1 | HIGH | contributor | clean-delta definition | A clean PR is a property of the INDEX and the merge-base branch diff, not merely a clean working tree; `.git/info/exclude` reduces but does not guarantee it (force-add, already-tracked files, prior commits, upstream path collisions). Verification must check the merge-base diff. | clean-delta reconciliation Sec 3.1, 6.1 |
| C2 | HIGH | any host user | discovery mechanism | Host-native SKILLS (T2) are the primary cross-host discovery path: `.agents/skills/<name>/SKILL.md` for OpenCode, Codex, Copilot (CLI + VS Code), Cursor, Antigravity, Gemini CLI; Claude Code needs a `.claude/skills/` adapter. A universal passive out-of-repo `@path` shim (T1) is NOT viable (OpenCode/Codex do not resolve it, Copilot CLI refuses it, Copilot-VS Code/Cursor unproven; only Claude/Antigravity/Gemini CLI resolve absolute imports, some with a consent step). | host-probe reconciliation exec table, Sec 5-6 |
| C3 | HIGH | contributor | artifact home | Developer artifacts that must stay tracked belong in a developer-owned SIBLING companion repository (e.g. `../<repo>.aw/`), not as ignored files in the target. Every producing workflow must know which repo receives file creation / `git mv` / status / commits (never the target for artifacts). | clean-delta reconciliation Sec 3.3, 9 |
| C4 | MEDIUM | maintainer | state location | The authoritative per-repo mode + routing lives in USER-GLOBAL agent-workflows config (a per-repo section), NOT an in-target manifest (which vanishes with a clone and reintroduces target footprint). A SEPARATE global ownership manifest owns shared user-scope skill files, with per-file hashes and dependent-repo awareness. | clean-delta reconciliation Sec 8 |
| C5 | MEDIUM | maintainer | lifecycle prose | ~8 producing runbooks hard-instruct "commit this (never push)"; those must become conditional on the resolved artifact root via a SINGLE resolver (P8), not per-runbook edits. A deterministic `context` resolver returns target root, mode, companion root, per-class routes, and whether the current command may commit in target/companion/neither/both. | clean-delta reconciliation Sec 9.3 |
| C6 | MEDIUM | maintainer | reinstall/downgrade | Same-version reinstall should be a VISIBLE verified no-op with a state table (missing/edited/config-changed/absent-manifest cases), not a silent no-op or an auto-repair. Five rotating backups do NOT preserve arbitrary future downgrade; record per-file source version + a transaction id + from/to version so downgrade stays POSSIBLE without building it now. | clean-delta reconciliation Sec 3.5, 11, 12 |
| C7 | HIGH | maintainer | evidence gate | Everything is documentation-graded; a Phase 0 CONFORMANCE HARNESS (clean temp home + temp repo, external content, a unique nonce side-effect, host diagnostics, precedence + permission runs, local vs cloud) MUST pass per exact host/version before the installer advertises any tier. | both reconciliations (harness-first sequencing) |
| C8 | MEDIUM | contributor | cloud boundary | Workstation user-scope skills, sibling paths, and `.git/info/exclude` state do NOT necessarily transfer to a remote/cloud clone. The first feature is LOCAL clean-delta; remote clean-delta is a separate design. | both reconciliations (cloud/local distinction) |
| C9 | LOW | maintainer | skill taxonomy | Do not create one skill per persona/lens. Use portable capability skills (plan-review, release-review, verify, scaffold, spec) + explicit harness skills for advise/assess (one per harness, resolving the selected persona/lens), with automatic invocation disabled where the host supports it. Keep only concise universal guidance in always-on rules. | both reconciliations (skill taxonomy) |
| C10 | LOW | contributor | ownership of skills | Writing to a shared user skills dir is a new ownership scope: explicit consent, per-file hashes, edited-file preservation, no deletion of unrecognized same-named files, dependent-repo reference awareness. | clean-delta reconciliation Sec 3.6, 8.3 |

## Resolution of IPD 05's deferred open questions (absorbed here)

IPD 05 (executed) deferred the per-host resolve-and-follow question and treated skills as a candidate tier. The research resolves them; recorded here (05 is not edited):

- OQ (05): does a host resolve+follow out-of-repo content? RESOLVED: T2 skills-first is the reliable cross-host answer; T1 passive out-of-repo pointer is NOT universal (host-probe reconciliation). 05's "candidate tiers" are now evidence-ranked: T2 primary, T3 consent-gated, T1 host-specific-only, in-repo-excluded as a tested fallback.
- OQ (05): skills classification. RESOLVED to the C9 taxonomy (capability skills + explicit harness skills; not one-per-lens).
- OQ (05): home-dir consent. RESOLVED: user-scope skills and any global write are consent-gated with a separate global ownership manifest (C10).

## Recommended architecture (spec)

```
User-scope host skill (T2)  ->  agent-workflows resolver  ->  packaged workflow/harness
Target repository            =  genuine code changes ONLY
Companion repository         =  tracked plans/prompts/research/runs + lifecycle state snapshot
User-global aw config        =  authoritative target->companion mapping, mode, enabled hosts
User-global ownership manifest = ownership of global skill/host files + dependent repos
Package installation         =  canonical workflow bodies + resolver
```

Per-host T2 layout (from the host-probe reconciliation; subject to Phase 0 reproduction): `.agents/skills/<name>/SKILL.md` for OpenCode, Codex, Copilot, Cursor, Antigravity, Gemini CLI; `.claude/skills/<name>/SKILL.md` adapter for Claude Code; global paths per host (e.g. Antigravity `~/.gemini/config/skills/`). Locally-excluded in-repo shims/skills are allowed ONLY after an exact host/version test and only when a host lacks a usable user-scope mechanism.

## Proposed changes (this IPD: DOCUMENTS ONLY)

| Step | Source | Change | Files | Risk | Validation |
|------|--------|--------|-------|------|------------|
| 1 | C1-C10 | Write the design-spec document: the two modes, the recommended architecture, the per-host T2/T3 delivery table with the T1-not-universal caveat, the state/ownership model (user-global config per-repo section + global ownership manifest), the resolver contract, the skill taxonomy, and the local-vs-cloud boundary. | a spec doc under `.agents/docs/specs/` | Low | spec present + internally consistent with the reconciliations; no em/en dashes |
| 2 | C6 | Document the same-version-reinstall STATE TABLE and the downgrade-PRESERVATION record (per-file source version + transaction id + from/to version; backups remain for recent undo), as the contract a build IPD must implement. Reference the shipped D103 manifest + backups/`--undo` (do not re-spec). | the spec doc | Low | state table + downgrade record documented; references D103/D106 |
| 3 | C5 | Document the resolver contract (`context --repo <path> --json` returning target root/mode/companion/routes/commit-permissions) and the rule that producing workflows call the resolver instead of parsing config, so the ~8 "commit (never push)" runbooks become conditional via ONE source (P8). No runbook edits in this IPD. | the spec doc | Low | resolver contract + single-source rule documented |
| 4 | C1, migration | Document the migration procedures (tracked->clean-delta and clean-delta->tracked): explicit action, dry-run, manifest-driven removal (never a blanket `git rm --cached -r`), companion creation-and-validation before removal, edited-file preservation, and merge-base-diff verification (a new removal commit may not yield a clean PR; note interactive-rebase/fresh-branch). | the spec doc | Low | both directions documented; branch-diff verification stated |
| 5 | C7, C8 | Document the PHASED PLAN and explicitly DEFER the build: Phase 0 = a conformance harness (its own IPD); Phase 1 = resolver + state/ownership + companion mapping (its own IPD); Phase 2 = packaged user skills for the C9 subset (its own IPD, gated on Phase 0); Phase 3 = clean-delta install + migration; Phase 4 = fallback project adapters. Label the initial feature LOCAL clean-delta; remote is separate. | the spec doc | Low | phased plan documented; each build phase named as a future IPD; build explicitly deferred |
| 6 | all | Docs/decision sync: a DECISIONS entry (pin at execution) recording the two-mode model + skills-first delivery + the deferral, noting it consumes the research bundle and resolves IPD 05's open questions; CHANGELOG note (a spec/roadmap artifact, not a shipped feature); cross-reference IPD 01-05 and the bundle. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; extends the ownership set; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Recommended later step |
|------|------|--------|------------------------|
| Building ANY of clean-delta mode, skills delivery, the resolver, migration | functionality | Documentation-graded; build gated on the Phase 0 harness. | Per-phase build IPDs, gated on Phase 0 evidence. |
| The Phase 0 conformance harness ITSELF | functionality | It is the first buildable, evidence-producing step and deserves its own IPD + plan-review. | Its own IPD, next in this workstream. |
| Remote / cloud clean-delta | functionality | Workstation-local mechanisms do not necessarily reach a cloud clone (C8). | A separate design after local clean-delta. |
| The "do not hand-edit inside aw:block" AGENTS.md directive | scope | Its own concern; already in TODO.md. | Its own IPD. |
| Per-class-only opt-out as a distinct mechanism | complexity | Served by the two modes + the existing `.untracked.` convention + `local/` lanes; a third mechanism is not warranted. | Only if a real gap appears. |

## Scope check

- Over-scope: none - this IPD produces ONLY the design spec + docs. No product code, no build, no runbook edits, no harness.
- Under-scope: the spec MUST define exactly two coherent modes (no incoherent low-level toggles); MUST be skills-first per the evidence (T1 not universal, C2); MUST route tracked artifacts to a sibling companion (C3); MUST keep authoritative state in user-global config + a separate global ownership manifest (C4/C10); MUST define merge-base-diff verification (C1); MUST specify the resolver + single-source conditional-commit rule (C5); MUST document the reinstall state table + downgrade-preservation record referencing the shipped manifest/backups (C6); MUST gate any build on a Phase 0 conformance harness and label the feature local-only (C7/C8); MUST record the resolution of IPD 05's open questions without editing executed IPD 05.

## Required tests / validation

- Documents only; no pytest delta. Validation is: the spec doc exists under `.agents/docs/specs/` (named per `YYYYMMDD-HHMM-NN-<slug>` convention) and is internally consistent with the two reconciliations (every C-finding is reflected; the per-host table matches the host-probe verdicts; the phased plan defers the build and names each phase as a future IPD); the DECISIONS/CHANGELOG entries reference the bundle and the IPD-05 resolution; run `python -m pytest -q` to confirm NO regression (documents only) and paste ACTUAL output; `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- A new spec doc under `.agents/docs/specs/`, DECISIONS, CHANGELOG. Cross-reference the research bundle, IPD 01-05, and TODO.md's aw:block item.

## Open questions

- OQ1 (per-class opt-out as its own mode): RESOLVED (maintainer + evidence). Not a separate mechanism; served by the two modes plus the existing per-file convention and `local/` lanes.
- OQ2 (where per-repo state lives): RESOLVED (evidence, C4). User-global config per-repo section is authoritative; a separate global ownership manifest owns shared skill files; the in-target manifest is retained only for tracked-mode repos.
- OQ3 (provenance when untracked): RESOLVED (maintainer 2026-07-25). Guard ACCIDENTAL loss, not malicious tampering (git history is not tamper-proof); in-file Workflow-history sections carry narrative provenance regardless of tracking; no new provenance subsystem.
- OQ4 (remaining EMPIRICAL unknowns): OPEN by design - these are the Phase 0 harness's job, NOT blockers for this SPEC: per-host excluded-file discovery, Cursor exact roots on the pinned build, cloud-surface skill availability, duplicate-name skill precedence, Gemini CLI noninteractive consent, sibling-repo read/write under host sandboxes. The spec records them as release blockers for the build phases.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. It produces DOCUMENTS ONLY; it does NOT build clean-delta mode, skills delivery, the resolver, or the harness. Any build IPD that follows MUST pass /plan-review + explicit human approval, and MUST NOT ship a delivery tier before the Phase 0 conformance harness reproduces the documented host behavior for that exact host/version.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Run the full suite to confirm no regression and paste ACTUAL output. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope (in particular, do NOT start building). Never create or push a tag / Release / PyPI upload. Never edit the executed IPD 05; record its resolution here.

CHECKPOINTED EXECUTION: (1) the design-spec doc (architecture + per-host delivery + state/ownership + resolver + skill taxonomy + cloud boundary); (2) reinstall state table + downgrade-preservation record; (3) resolver contract + single-source conditional-commit rule; (4) migration both directions + merge-base verification; (5) phased plan with build explicitly deferred to per-phase IPDs; (6) DECISIONS + CHANGELOG. Run the full suite after doc changes to confirm no regression; pause and report if scope grows toward a build.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute the document steps, validate internal consistency + no test regression; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
4. Then author the Phase 0 conformance-harness IPD as the first buildable step; every build phase is its own gated IPD.
