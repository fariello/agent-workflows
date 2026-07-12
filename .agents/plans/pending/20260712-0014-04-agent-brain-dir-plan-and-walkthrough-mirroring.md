# IPD: Enforce mirroring of agent private "brain" IPDs and walkthroughs into .agents/

- Date: 2026-07-12
- Concern: convention enforcement across agent toolchains. Some agents (notably Antigravity IDE with
  Gemini) create IPDs and "walkthrough" documents in a private/hidden "brain" directory that is
  REQUIRED for the agent to operate, and by default do NOT mirror them into the project's tracked
  `.agents/` tree. That loses provenance and breaks this repo's plan lifecycle + doc conventions.
- Scope: `AGENTS.md` (the always-read contract) as explicit MUST rules (agent-agnostic), the plan +
  walkthrough naming conventions, and a scaffolded `.agents/docs/walkthroughs/` directory + README
  (Category-1, no-clobber, via `setup-repo`). Docs/DECISIONS.
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-08). Awaiting flesh-out.

## Goal / decisions taken (maintainer, 2026-07-12)

1. **MUST-mirror IPDs.** Any plan/IPD an agent creates in a private/brain/hidden working directory
   MUST have an exact, conventions-compliant copy in `.agents/plans/*` (correct
   `YYYYMMDD-HHMM-NN-<slug>.md` name, front-matter `Status:`, `## Workflow history`), and MUST be
   moved through the lifecycle there (pending -> executed/superseded/not-executed). The brain copy is
   never the source of truth; the tracked `.agents/plans/` copy is.
2. **MUST-mirror walkthroughs.** Any "walkthrough" / narrative summary an agent produces MUST be
   copied to `.agents/docs/walkthroughs/` using the same convention:
   `YYYYMMDD-HHMM-NN-<slug>-walkthrough.md`.
3. **Where the rules live.** In `AGENTS.md` (every agent reads it) as agent-AGNOSTIC MUST rules -
   phrased for "any agent that keeps private working state," so it is not Antigravity-specific but
   covers it. Marker-delimited so `setup-repo` can install/update the block in downstream repos.
4. **Scaffold.** `setup-repo` creates `.agents/docs/walkthroughs/` with a short Category-1 README
   (generated, no-clobber), consistent with the D49 directory-README convention.

## Open questions (to resolve during flesh-out / review)

1. Do we add an explicit Antigravity/Gemini-named callout in addition to the universal rule, or keep
   it purely general? (Maintainer chose: universal in AGENTS.md; decide at review whether to add a
   named note for the concrete offender.)
2. `.agents/docs/` may not exist yet - confirm the tree (`.agents/docs/walkthroughs/`) and whether
   `docs/` gets its own README too (D49).
3. Enforcement level: MUST prose only (advisory-first, consistent with D52), or also a check (e.g. a
   `setup-repo`/verify note that flags a brain dir with un-mirrored plans)? (Lean: prose MUST for v1;
   a detector is hard to generalize across hidden-dir layouts.)
4. NN sequencing for walkthroughs: share the plan per-minute sequence rules, or independent? (Lean:
   same `YYYYMMDD-HHMM-NN` scheme, independent counter within walkthroughs/.)

## Approval and execution gate

Proposal (`draft`). Flesh out -> `to-review` -> `/plan-review` -> resolve OQs -> human approve ->
execute -> validate -> commit (never push) -> `git mv` to executed/. Not auto-executed.
