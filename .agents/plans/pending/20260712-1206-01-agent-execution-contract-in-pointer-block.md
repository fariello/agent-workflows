# IPD: Add a standing "Agent execution contract" to the managed pointer block

- Date: 2026-07-12
- Concern: handoff reliability / instruction reach. When an agent (this repo's maintainer, OpenCode,
  or a parallel Gemini/Antigravity run) is asked to "execute IPD `<path>`", a set of STANDING rules
  must apply that today are NOT written in one always-loaded place: (a) no em/en dashes in authored
  Markdown; (b) commit ONLY your own files path-scoped, never `git add -A` / bare commit / `-a`;
  (c) never push; (d) an HONESTY rule: when you claim validation passed you MUST paste the ACTUAL
  runner output, never report success you did not run; (e) move plans through the lifecycle. These are
  scattered across `CONTRIBUTING.md`, the `verify-execution`/`scaffold` workflow bodies, and per-IPD
  gate lines, so a fresh agent handed only a plan path does not reliably receive them. The honesty rule
  (d) is currently written NOWHERE as a standing expectation, yet it is the exact failure we hit twice
  this session (plans marked `executed` with fabricated "tests green").
- Scope: add a SHORT "Agent execution contract" sub-section to the managed `AGENT-WORKFLOWS` block
  (`agents_pointer_block()`, engine.py:541) and this repo's mirrored `AGENTS.md`, inside the existing
  markers (ONE block definition). Docs/DECISIONS. This IPD adds standing PROSE only; it does NOT add a
  machine gate (that stays `/verify-execution`).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after a session where a
  path-only handoff to a parallel agent required a large out-of-band prompt (house rules, commit
  discipline, honesty). Goal: make "execute IPD `<path>`" sufficient by putting the standing rules in
  the always-loaded contract. Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- The managed block is `agents_pointer_block()` (engine.py:541), delimited by
  `AGENT-WORKFLOWS:BEGIN/END`, written to the resolved `AGENTS.md` by `update_agents_pointer`
  (engine.py:1007) and mirrored verbatim into this repo's `AGENTS.md`. It already carries `###`
  sub-sections ("Guidelines for Antigravity & Other Agents", "Writing prompts for another AI",
  "Durable reference and walkthroughs documentation"), so an "Agent execution contract" sub-section
  fits the existing shape and single-definition rule.
- The rules already exist, but scattered and NOT always-loaded for the target agents:
  - No em/en dashes: `CONTRIBUTING.md:79`, `assess/references/prose-style.md:29`, per-IPD "House
    rule" lines. Not in the pointer block.
  - Path-scoped commit / no `add -A` / no bare commit: only in `verify-execution.md:37-38` (workflow
    scope), DECISIONS D66 (~:1981). Not a standing rule.
  - Never push: widespread (`scaffold.md`, `release-review/00-run-protocol.md:51`, every IPD gate).
  - Honesty ("paste real runner output; never assert success you did not run"): written NOWHERE as a
    standing rule. This is the highest-value addition.
- Reach: `AGENTS.md`-only does NOT reach Claude Code or default Gemini (survey
  `.agents/docs/research/20260712-0031-01-agent-instruction-file-discovery-survey.md`). So these rules
  only reach those agents once IPD `20260712-0030-01` mirrors the block into an existing
  `CLAUDE.md`/`GEMINI.md`. SOFT dependency on 0030-01 for full reach (the rules are correct in
  AGENTS.md meanwhile).
- Brevity budget: IPD `20260712-0014-04` (PB4-2) sets a combined ~6-8 line budget for ADDED contract
  prose across the block-editing IPDs, with overflow moving to referenced convention docs (the block
  is a POINTER, not a manual, P9). This IPD is now the FOURTH block-editing IPD (with 0014-04, 0030-01,
  and 0033-01-already-executed) and MUST be reconciled within that budget on whichever lands last.
- Enforcement posture: advisory-first (D52). MUST prose in the contract; the machine enforcement of the
  honesty rule stays `/verify-execution` (D66), which re-runs validation independently.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Add an "Agent execution contract" sub-section to `agents_pointer_block()`** (engine.py:541) and
   this repo's mirrored `AGENTS.md`, inside the existing markers (ONE definition). Terse MUST bullets,
   roughly (final wording reconciled under the brevity budget, change #3):
   - "When you execute a plan/IPD or any task in this repo you MUST: write no em dashes or en dashes in
     authored Markdown (use a hyphen or reword); commit ONLY the files you changed, path-scoped
     (`git commit -m msg -- <path>`), never `git add -A`, a bare `git commit`, or `git commit -a`;
     never push. When you report that tests/validation passed you MUST paste the ACTUAL runner output;
     never report success you did not run. Move plans through the lifecycle (`.agents/plans/*`) per the
     AGENT-PLANS block; the tracked copy is the source of truth."
   - Keep it a POINTER: name the rules and point at the convention docs (`CONTRIBUTING.md`, the
     `.agents/plans` README) for detail rather than restating them.
2. **Honesty rule wording (locked by maintainer):** phrase (d) as a HARD MUST: "When you claim
   validation passed, you MUST paste the actual runner output. Never report success you did not run."
   Aimed squarely at the false-completion failure mode; `/verify-execution` remains the enforcement.
3. **Reconcile with the other block-editing IPDs under the brevity budget.** After 0014-04 (brain-dir
   MUST rules), 0033-01 (immortalize-research, already executed), 0030-01 (native-file mirroring), and
   THIS contract all land, the ADDED contract prose stays within ~6-8 lines in the pointer block;
   overflow moves to the referenced convention docs. Whichever of {0014-04, 0030-01, this} lands last
   integrates the others' text within budget. Recommended order overall:
   0030-01 (reach) -> this (contract) -> 0014-04 (brain-dir), so the contract is present and reaching
   Claude/Gemini before the brain-dir rules that lean on it. Update this repo's `AGENTS.md` to match
   and verify in sync via `aw install . --dry-run` ("pointer already current").
4. **Docs + DECISIONS.** Note the standing execution contract where contributor rules live
   (`CONTRIBUTING.md` gets a one-line pointer to the block; the block is now the single always-loaded
   home). DECISIONS entry (Dnn) recording the contract, the hard-MUST honesty rule and its rationale
   (twice-seen false completions), the advisory-first posture, and that `/verify-execution` is the
   enforcement, not a machine gate in the installer.
5. **Validation.** Prose-contract change (no unit test for instruction prose, per repo policy);
   validate that the block round-trips (`aw install . --dry-run` reports in-sync; full suite green;
   `aw plan-names` clean). If any test asserts block content/markers (e.g. marker count, "pointer
   already current" idempotence), keep it green and paste the actual runner output.

## Deferred / out of scope

- Any machine gate that blocks a commit lacking pasted test output (not detectable in-installer;
  `/verify-execution` covers it post-hoc).
- A separate standalone "parallel-agent collaboration" doc: the always-loaded block is the right home;
  a standalone doc would be a second source of truth and would not be auto-loaded by Claude/Gemini.
- Restating the FULL house-style guide in the block (stays in `CONTRIBUTING.md` /
  `assess/references/prose-style.md`; the block only points).

## Open questions (v1 leans for review)

1. Honesty rule strength: RESOLVED (maintainer) - HARD MUST: "When you claim validation passed you
   MUST paste the actual runner output; never report success you did not run."
2. Does the contract belong in its OWN `###` sub-section, or folded into the existing "Guidelines for
   Antigravity & Other Agents" sub-section? (Lean: its own short sub-section "Agent execution
   contract" - it applies to ANY task, not only running a workflow.)
3. How much of the commit discipline to state inline vs. point to a doc, given the brevity budget.
   (Lean: state the four MUSTs as one dense line each and point to `CONTRIBUTING.md` /
   `.agents/plans` README for the rest.)
4. Landing order relative to 0030-01/0014-04 (change #3 recommends 0030-01 -> this -> 0014-04).
   Confirm at approval.

## Dependencies / sequencing

- SOFT-but-important: IPD `20260712-0030-01` (mirrors the block into CLAUDE.md/GEMINI.md) - without it
  the contract under-reaches Claude Code + default Gemini, the agents this most needs to reach.
- SHARED HOT SPOT: this, `20260712-0014-04`, and `20260712-0030-01` all edit the single
  `agents_pointer_block()` under the 6-8 line brevity budget (0014-04 PB4-2). Reconcile block text on
  whichever lands last; no divergent copies. Recommended order: 0030-01 -> this -> 0014-04.

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQ2-4 interactively, human approve,
execute changes 1-5, validate (block in sync + full suite green, paste real runner output), commit
ONLY this IPD's touched files path-scoped (never push), `git mv` to executed/. Not auto-executed.
