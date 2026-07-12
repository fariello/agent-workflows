# IPD: MUST-mirror rules for agent private "brain" IPDs and walkthroughs into .agents/

- Date: 2026-07-12
- Concern: convention enforcement across agent toolchains. Some agents (notably Antigravity IDE with
  Gemini) create IPDs and "walkthrough" documents in a private/hidden "brain" directory that is
  REQUIRED for the agent to operate, and by default do NOT mirror them into the project's tracked
  `.agents/` tree. That loses provenance and breaks this repo's plan lifecycle + doc conventions.
  This IPD adds the MUST-mirror RULES to the managed contract block; the `.agents/docs/walkthroughs/`
  HOME is provided by IPD 0033-01.
- Scope: the MUST-mirror RULES only - authored into the managed `AGENT-WORKFLOWS` block (which the
  installer writes to `AGENTS.md` and, per IPD 0030-01, to any existing `CLAUDE.md`/`GEMINI.md`), plus
  a reference to the plan + walkthrough naming conventions. Docs/DECISIONS. The `.agents/docs/`
  tree + `walkthroughs/` scaffold and its README are NOT in this IPD - they are provided by IPD
  `20260712-0033-01` (this IPD DEPENDS on that home existing).
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-08). Awaiting flesh-out.
- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): fleshed out and RE-SCOPED after two
  dependencies landed in review: the `.agents/docs/walkthroughs/` HOME moved to IPD 0033-01, and the
  AGENTS.md-reach reality (Claude Code + default Gemini do NOT read AGENTS.md; survey
  `docs/research/2026-07-12-agent-instruction-file-discovery-survey.md`) means these rules must ride
  the SAME managed block that IPD 0030-01 mirrors into `CLAUDE.md`/`GEMINI.md`. This IPD is now just
  the RULES. Approach committed; promoted to to-review.
- 2026-07-12 /plan-review-long (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PB4-1 (survey citation -> note canonical .agents/docs/research archive), PB4-2 (added a ~6-8-line
  combined AGENTS-block brevity budget across the three block-editing IPDs, overflow to docs), PB4-3
  (name the AGENT-PLANS block + .agents/plans README as the doc home). All 5 OQs resolved
  interactively with the maintainer (universal rule + example; prose-only enforcement; independent
  walkthrough NN; 0033-01 -> 0030-01 -> this order). Evidence re-verified against source. No
  BLOCKER/HIGH. Status -> reviewed (awaiting human approval to execute).
- 2026-07-12 external review (Gemini in Antigravity IDE, relayed by maintainer): corroborated the
  plan set and the execution order; supplied the concrete Antigravity brain-dir path
  (`~/.gemini/antigravity-ide/brain/<conversation-id>`) now captured in Step 0 as reported/to-verify.
  Also asserted Antigravity reads AGENTS.md (unconfirmed vs. the survey); noted as a reach caveat.
  Enrichment only; approach and findings unchanged; remains reviewed.

## Project conventions discovered (Step 0, VERIFIED against source)

- The managed block is `agents_pointer_block()` (engine.py:541), delimited by
  `AGENT-WORKFLOWS:BEGIN/END`; the installer writes it to the resolved `AGENTS.md`
  (`update_agents_pointer`, engine.py:1007) and this repo's `AGENTS.md` mirrors it verbatim. This IPD
  ADDS a sub-section to THAT block (single definition), so the rules ship to every installed repo.
- Reach caveat (VERIFIED, survey sections 3A/3B/5): `AGENTS.md`-only does NOT reach Claude Code or
  default Gemini CLI (non-recognition). So these MUST-mirror rules only reliably reach those agents
  once IPD 0030-01 mirrors the block into an existing `CLAUDE.md`/`GEMINI.md`. HARD DEPENDENCY on
  0030-01 for full effect (the rules are still correct in AGENTS.md meanwhile; they just under-reach
  Claude/Gemini until 0030-01 lands). Survey archived canonically at
  `.agents/docs/research/plan-review/` (the `docs/research/` copy is the pre-0033-01 location and is
  superseded once 0033-01 lands).
- Walkthrough HOME: `.agents/docs/walkthroughs/` is scaffolded (dir + Category-1 no-clobber README)
  by IPD 0033-01, which also defines the `YYYYMMDD-HHMM-NN-<slug>.md` naming. HARD DEPENDENCY: this
  IPD references that path/convention but does NOT create the dir or README (avoids the two IPDs both
  scaffolding it - single source).
- Naming: `YYYYMMDD-HHMM-NN-<slug>.md`, LOCAL time (D48/D50/D55). Walkthroughs use the
  `...-<slug>-walkthrough.md` variant. `aw plan-names` (D56) + the normalizer enforce the plan names;
  0033-01 extends that coverage to `.agents/docs/**`.
- Enforcement posture: advisory-first (D52) - MUST prose in the contract, not a hard machine gate
  (hidden brain-dir layouts are agent-specific and not generally detectable).
- Concrete offender path (REPORTED by Gemini in Antigravity IDE 2026-07-12, NOT independently
  verified): Antigravity keeps session walkthroughs and task checklists under
  `~/.gemini/antigravity-ide/brain/<conversation-id>`. Useful as the motivating example for the rule
  and as a potential detector target IF a detector is ever built (deferred per OQ3). Treat as a lead
  to confirm, not an established fact; the rule stays agent-agnostic regardless.
- Reach discrepancy to note: Gemini's review asserted "Antigravity reads `AGENTS.md`", but the
  instruction-file survey lists Antigravity IDE root-`AGENTS.md` behavior as undocumented / needs
  empirical test. If the IDE does NOT reliably read `AGENTS.md`, that STRENGTHENS the 0030-01
  dependency (mirror the block into an existing `GEMINI.md` so these rules actually reach Antigravity).
  Unresolved; do not assume AGENTS.md alone reaches Antigravity.
- House rule: no em dashes in authored Markdown.

## Decisions taken (maintainer, 2026-07-12)

1. **MUST-mirror IPDs:** a plan/IPD an agent creates in a private/brain/hidden working dir MUST have
   an exact, conventions-compliant copy in `.agents/plans/*` and be moved through the lifecycle there;
   the tracked copy is the source of truth, not the brain copy.
2. **MUST-mirror walkthroughs:** a narrative "walkthrough" MUST be copied to
   `.agents/docs/walkthroughs/YYYYMMDD-HHMM-NN-<slug>-walkthrough.md`.
3. **Where the rules live:** the managed `AGENT-WORKFLOWS` block (agent-agnostic MUST prose), so it
   ships to every installed repo (and, via 0030-01, to CLAUDE.md/GEMINI.md).
4. **Advisory-first:** MUST prose, no hard machine gate for v1.

## Proposed changes (ordered, validatable)

1. **Add a "Private working state" MUST sub-section to `agents_pointer_block()`** (engine.py:541) and
   this repo's mirrored `AGENTS.md`, inside the existing markers (ONE block definition, shared with
   0030-01/0033-01). Agent-agnostic prose, roughly:
   - "If you keep plans/IPDs in a private, hidden, or tool-internal directory (a 'brain'/memory/
     scratch dir), you MUST also keep an exact, conventions-compliant copy under `.agents/plans/`
     (`YYYYMMDD-HHMM-NN-<slug>.md`, local time, with front-matter `Status:` and `## Workflow history`)
     and move THAT copy through the lifecycle (pending -> executed/superseded/not-executed). The
     tracked `.agents/plans/` copy is the source of truth; the private copy is disposable."
   - "If you produce a narrative walkthrough / session summary, you MUST save a copy to
     `.agents/docs/walkthroughs/YYYYMMDD-HHMM-NN-<slug>-walkthrough.md`."
   - Keep it SHORT (the block is a pointer, not a manual); phrase for "any agent that keeps private
     working state," with a parenthetical naming the known offenders ("e.g. Antigravity/Gemini",
     resolving OQ1 as: universal rule + a brief named example).
2. **Reconcile the block with 0030-01 and 0033-01, under a brevity budget (PB4-2).** Three IPDs now
   add prose to the SINGLE `agents_pointer_block()`: this IPD's brain-dir rules, 0033-01's
   immortalize-research directive, and 0030-01's native-file mirroring (which changes WHERE the block
   is written, not its text). The block is a POINTER, not a manual (P9). Governing constraint: after
   all three land, the added contract prose (research + brain-dir MUST rules) totals AT MOST ~6-8
   lines combined - terse MUST bullets that point at the conventions, not restate them. If it would
   exceed that, move the detail into a referenced convention doc (e.g. the plans/docs READMEs from
   0033-01) and keep only a one-line pointer in the block. Whichever IPD lands last integrates the
   others' text within this budget. Update this repo's `AGENTS.md` to match and verify in sync via
   `aw install . --dry-run` ("pointer already current").
3. **Docs + DECISIONS.** Note the brain-dir mirroring contract where the plan lifecycle is already
   documented: the AGENTS.md AGENT-PLANS block and the `.agents/plans` README (the same homes D52's
   plan-status rules use), plus a one-liner in README/ARCHITECTURE if it fits without bloat. DECISIONS
   entry (Dnn) recording the MUST-mirror rules, the advisory-first posture, the dependency on the
   `.agents/docs/walkthroughs/` home (0033-01) and on native-file mirroring for Claude/Gemini reach
   (0030-01), and Antigravity/Gemini as the motivating case.
4. **Validation.** Prose-contract change (no unit test for instruction prose, per repo policy);
   validate that the block round-trips (`aw install . --dry-run` reports in-sync; suite green;
   `aw plan-names` still clean). If any test asserts block content/markers, keep it green.

## Open questions (ALL RESOLVED with maintainer 2026-07-12 via /plan-review-long)

1. Named callout: RESOLVED - universal MUST rule + a brief "(e.g. Antigravity/Gemini)" parenthetical,
   NOT an Antigravity-only section.
2. Sequencing / walkthrough home: RESOLVED - the `.agents/docs/` tree + `walkthroughs/` home is owned
   by IPD 0033-01 (hard dependency). Confirmed execution order: 0033-01 -> 0030-01 -> this IPD.
3. Enforcement level: RESOLVED - MUST prose only for v1 (advisory-first, D52); a brain-dir detector
   is agent-specific and DEFERRED to a possible later follow-on.
4. Walkthrough `NN` sequencing: RESOLVED - same `YYYYMMDD-HHMM-NN` scheme, with an INDEPENDENT
   per-minute counter within `walkthroughs/` (separate area from plans; counters do not collide).
5. Block brevity budget: RESOLVED - the combined contract prose across the three block-editing IPDs
   (this, 0033-01, 0030-01) is AT MOST ~6-8 lines in the AGENTS pointer block; overflow moves to the
   referenced convention docs so the block stays a pointer (P9). (See change #2.)

## Dependencies / sequencing

- HARD: IPD `20260712-0033-01` (provides `.agents/docs/walkthroughs/` home + naming). Execute 0033-01
  first (or together).
- SOFT-but-important: IPD `20260712-0030-01` (mirrors the block into CLAUDE.md/GEMINI.md) - without
  it, these rules under-reach Claude Code + default Gemini, the very toolchains this targets.
  Recommended overall order: 0033-01 -> 0030-01 -> this IPD.
- All three share ONE `agents_pointer_block()` definition; reconcile block text on whichever lands
  last (no divergent copies).

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQs, human approve, execute changes
1-4, validate (block in sync + suite green), commit (never push), `git mv` to executed/. Not
auto-executed.
