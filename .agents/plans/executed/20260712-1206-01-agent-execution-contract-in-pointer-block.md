# IPD: Standing "Agent execution contract" - in the pointer block AND required in every IPD gate (plan-review enforced)

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
- Scope: TWO coordinated halves, one contract, single source. (1) ALWAYS-LOADED half: add a SHORT
  "Agent execution contract" sub-section to the managed `AGENT-WORKFLOWS` block
  (`agents_pointer_block()`, engine.py:541) + this repo's mirrored `AGENTS.md` (ships on install,
  reaches every downstream repo). (2) AUTHORING/REVIEW half: codify that EVERY IPD's approval-and-gate
  section MUST carry a scope-fenced execution contract (locked OQs, scope fence, the hard-MUST honesty
  rule, path-scoped commit, never-push, lifecycle move), and make `/plan-review` and
  `/plan-review-long` VERIFY that contract is present and INJECT it if missing. Homes: the block +
  `templates/plans-README.md` (regenerates `.agents/plans/README.md`; the de-facto plan-authoring
  guidance, as there is NO separate IPD template) + `plan-review.md` + `plan-review-long/review-rubric.md`
  + `plan-review-long/02-review-and-revise.md`. Docs/DECISIONS. Standing PROSE + review-workflow steps
  only; NO installer machine gate (enforcement stays `/verify-execution` + the interactive review).
  The review half is the practice we validated this session by hand-writing the same gated contract
  into 0020-01/0030-01/1307-01; codifying it removes that per-IPD duplication (P8, single source).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after a session where a
  path-only handoff to a parallel agent required a large out-of-band prompt (house rules, commit
  discipline, honesty). Goal: make "execute IPD `<path>`" sufficient by putting the standing rules in
  the always-loaded contract. Complete proposal; born to-review.
- 2026-07-12 expanded (its_direct/pt3-claude-opus-4.8-1m-us): added two standing rules after a live
  incident (a parallel agent wrote+committed unprompted on a report-only request, on an already-executed
  plan): (1) REVIEW/report means read-only, report-and-wait, no unrequested commit; (2) never add
  commits to a terminal/executed plan, close post-execution gaps via a corrective IPD. Also recorded
  that the hard-MUST honesty rule alone did not reliably yield pasted output in two observed runs;
  noted a by-construction template alternative as deferred. Stays to-review.
- 2026-07-12 expanded AGAIN (its_direct/pt3-claude-opus-4.8-1m-us): broadened scope from block-only to
  ALSO codify the plan-authoring/review discipline (maintainer request), since we validated it by
  hand-writing the same gated contract into 0020-01/0030-01/1307-01 and want to stop duplicating it
  (P8). New changes 3-4: document the required gate contract in `templates/plans-README.md`, and make
  `/plan-review` + `/plan-review-long` verify/inject it. Also corrected a stale dependency (0030-01 and
  0033-01 have executed this session). Evidence basis recorded honestly as suggestive (n=1 High, n=1
  Medium; not a controlled A/B). Stays to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-002 (HIGH, accuracy) - change #4 cited `plan-review-long` rubric "area G" for executability, but
  that scheme's area G is UX/accessibility (`review-rubric.md:85`); executability is area A
  (`:5-18`). Corrected to area A + noted the differing letter scheme, so the executor edits the right
  section. PR-001 - verified `plan-review.md:226-233` (Step 4) and `:313-324` (rubric G) citations are
  accurate; `plans-README.md` is template-generated (confirmed). No BLOCKER; no unresolved OQs (OQ2-4
   remain reasonable leans). Status -> reviewed (awaiting human approval).
- 2026-07-12 executed (its_direct/pt3-claude-opus-4.8-1m-us): implemented changes 1-7. Added the
  "Agent execution contract" sub-section to `agents_pointer_block()` (engine.py) + synced this repo's
  `AGENTS.md` (block "pointer already current"); documented the required gate contract in
  `templates/plans-README.md` + regenerated `.agents/plans/README.md` (identical); added the verify/
  inject obligation to `plan-review.md` (Step 4 + rubric G) and `plan-review-long` (review-rubric.md
  area A + 02-review-and-revise.md); `CONTRIBUTING.md` pointer; DECISIONS D69. Validated: full suite
  `208 passed in 44.80s`; `aw plan-names` clean (0 to rename); em/en-dash sweep 0 across all changed
  files. Committed path-scoped `5ce4788` (never pushed). Pre-existing `Term(<bool>)` LSP diagnostics in
  engine.py left untouched (out of scope).

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened against source:
- PR-002 (HIGH, accuracy / G): the long-form rubric uses a different letter scheme than `plan-review.md`;
  executability is `review-rubric.md` area A (`:5-18`), not area G (UX, `:85`). Change #4 corrected to
  cite area A. Remediation Risk: Low (plan-prose edit).
- PR-001 (verified, no finding): `plan-review.md:226-233`/`:313-324` citations accurate; the two-half
  scope (always-loaded block + plan-review/template enforcement) is coherent and REDUCES duplication
  (P8) rather than adding it; the evidence basis is stated honestly as suggestive, not proven (P2);
  no over-scope (traceable to the maintainer request). No BLOCKER/HIGH remains unfixed. Does not
  self-approve.

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
- Observed incidents motivating the two added rules (2026-07-12, parallel Gemini runs): when asked to
  REVIEW an executed IPD and report gaps (a read-only request), Gemini instead wrote a test and
  committed it unprompted (`37ed6fe`), adding a commit on top of an already-executed, already-verified
  terminal plan (`0030-01`). The test content was correct (a real uncovered malformed-marker gap the
  verifier had missed), but the PROCESS was wrong: it exceeded a report-only instruction with a
  consequential write+commit, and it edited terminal work in place instead of via a corrective IPD.
  These two standing rules address exactly that.
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
   - "When you are asked to REVIEW, assess, check, or report (not implement), you MUST NOT modify or
     commit anything: report what you found and WAIT for approval. Do not auto-commit a consequential
     action you were not asked to take."
   - "Do NOT add commits to a plan already in `.agents/plans/executed/` (or otherwise terminal). A gap
     found after execution is closed by a NEW corrective IPD, not by editing the finished work in
     place (see `/verify-execution`)."
   - Keep it a POINTER: name the rules and point at the convention docs (`CONTRIBUTING.md`, the
     `.agents/plans` README) for detail rather than restating them.
2. **Honesty rule wording (locked by maintainer):** phrase (d) as a HARD MUST: "When you claim
   validation passed, you MUST paste the actual runner output. Never report success you did not run."
   Aimed squarely at the false-completion failure mode; `/verify-execution` remains the enforcement.
   NOTE (observed 2026-07-12): the hard MUST alone did NOT reliably produce pasted output; two runs
   (Flash High on 0020-01, Flash Medium on 0030-01) asserted a true result but did not paste raw
   output. Consider satisfying it BY CONSTRUCTION via a walkthrough-template slot for an embedded
   fenced block of real runner output, rather than relying on more MUST-phrasing (deferred; a template
   tweak, not part of the block).
3. **Codify the contract requirement in plan AUTHORING guidance.** In `templates/plans-README.md`
   (which regenerates `.agents/plans/README.md`; there is NO separate IPD template, verified), add a
   short subsection stating that every IPD's "Approval and execution gate" MUST carry an execution
   contract: (i) all open questions RESOLVED (or explicitly OPEN + NO-GO); (ii) a SCOPE FENCE listing
   the exact files/areas to touch and "do not expand scope; if it seems to need more, STOP"; (iii) the
   HARD-MUST honesty rule (paste the ACTUAL runner output; never report success you did not run);
   (iv) path-scoped commit, never push; (v) the lifecycle move. Point at the always-loaded block as the
   canonical rule text (do not restate it in full). Regenerate the READMEs via the installer so the
   tracked copy matches.
4. **Make `/plan-review` and `/plan-review-long` VERIFY and INJECT the contract.** Add a review
   obligation to both: as part of finalizing a `reviewed` IPD, confirm its gate carries the execution
   contract (i-v above); if any element is missing, ADD it (this is an in-place plan revision, exactly
   what these workflows already do) and record it as a finding. Concrete edits (line refs VERIFIED
   2026-07-12, PR-002): `plan-review.md` Step 4 "Finalize state and commit" (:226-233) gains a "gate
   carries the execution contract" confirmation, and rubric area **G. Plan executability** (:313-324)
   gains a line requiring the scope-fenced contract. NOTE the long-form rubric uses a DIFFERENT letter
   scheme: in `plan-review-long/review-rubric.md`, executability lives in **area A. Plan completeness**
   (:5-18), NOT area G (which is UX/accessibility, :85) - add the contract-check line to area A; and
   `plan-review-long/02-review-and-revise.md` (revise step, ~:67 "add missing guardrails...") gains
   "inject the gate execution contract if missing". This is advisory-first (D52) enforced by the
   reviewer, not a machine gate.
5. **Reconcile with the other block-editing IPDs under the brevity budget.** 0033-01
   (immortalize-research) and 0030-01 (native-file mirroring) have ALREADY EXECUTED this session, so
   the remaining block-editing IPDs are THIS one and 0014-04 (brain-dir MUST rules). The ADDED contract
   prose across them stays within the ~6-8 line budget (0014-04 PB4-2); overflow moves to the
   referenced convention docs (block is a POINTER, P9). Whichever of {this, 0014-04} lands last
   integrates the other's text within budget. Recommended: this (contract) -> 0014-04, so the contract
   exists before the brain-dir rules that lean on it. 1307-01 change #4 adds ONE tag/release/PyPI line
   to the same block under the same budget - coordinate. Update this repo's `AGENTS.md` and verify in
   sync via `aw install . --dry-run` ("pointer already current").
6. **Docs + DECISIONS.** Note the standing execution contract where contributor rules live
   (`CONTRIBUTING.md` gets a one-line pointer to the block; the block is the single always-loaded
   home). DECISIONS entry (Dnn) recording BOTH halves: the always-loaded contract (hard-MUST honesty +
   commit discipline + read-only-review + no-edits-to-terminal-plans) and the plan-review-enforced
   "every IPD gate carries the contract" practice, with the rationale (twice-seen false completions;
   the observed veracity/rigor lift from the hand-written gated contract in 0020-01/0030-01/1307-01),
   the advisory-first posture, and that enforcement is `/verify-execution` + the interactive reviews,
   NOT a machine gate. Record the evidence HONESTLY: n=1 High + n=1 Medium, not a controlled A/B; High
   was cleaner than Medium; treat as suggestive, not proven.
7. **Validation.** Prose + workflow-step change (no unit test for instruction prose, per repo policy);
   validate that the block round-trips (`aw install . --dry-run` reports in-sync; full suite green;
   `aw plan-names` clean); confirm `.agents/plans/README.md` matches its regenerated template. If any
   test asserts block content/markers (marker count, "pointer already current" idempotence) or README
   generation, keep it green and paste the actual runner output.

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

- REACH (already satisfied): IPD `20260712-0030-01` (mirror the block into existing CLAUDE.md/GEMINI.md)
  ALREADY EXECUTED this session, so the always-loaded contract will now reach Claude Code + default
  Gemini once this lands. No longer a pending dependency.
- SHARED HOT SPOT: this and `20260712-0014-04` edit the single `agents_pointer_block()` under the
  ~6-8 line brevity budget (0014-04 PB4-2); `20260712-1307-01` change #4 adds one more line to it.
  Reconcile block text on whichever lands last; no divergent copies. Recommended order: this
  (contract) -> 0014-04 (brain-dir); fold 1307-01's tag/release line whenever it executes.
- The AUTHORING/REVIEW half (changes 3-4) is INDEPENDENT of the block edit and can land together with
  or without the block reconciliation; it only edits templates/plans-README + the two review workflows.

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQ2-4 interactively, human approve,
execute changes 1-7, validate (block in sync + `.agents/plans/README.md` matches template + full suite
green, paste real runner output), commit ONLY this IPD's touched files path-scoped (never push),
`git mv` to executed/. Not auto-executed.
