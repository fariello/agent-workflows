# IPD: Auto-engaging parallel read-only audit lanes (shared convention for release-review + plan-review)

- Date: 2026-07-13
- Concern: review throughput without sacrificing safety or correctness. Reviewing several plans (or
  several independent audit surfaces) one at a time single-threads the expensive part - reading source,
  verifying every `path:line` claim, running the rubric/personas/security lens. That work is
  parallelizable across independent units; the WRITES (in-place edits, commits) and the interactive
  human decisions are not. Today release-review's parallel audit lanes are OPTIONAL ("the agent may
  use..."), and plan-review has no parallel mode at all. Make the safe fan-out AUTO-ENGAGE when it pays
  off (2+ eligible units), define the convention ONCE, and apply it to both workflows.
- Scope: `.agents/workflows/release-review/00-run-protocol.md` (the shared sibling file both
  plan-review workflows already reference) - promote the existing "Optional controlled parallel audit
  mode" (line 346+) into the canonical AUTO-PARALLEL convention with the >=2 trigger and the
  coordinator-owns-mutations rule; `.agents/workflows/release-review/README.md` + Section files as
  needed to name the trial MODE; `.agents/workflows/plan-review-long/plan-review-long.md` (+ its step
  files) to inherit the convention for multi-plan review; `.agents/workflows/plan-review/plan-review.md`
  to DOCUMENT that the single-file portable variant stays serial by design. Docs/DECISIONS. Prose-only
  workflow change; no code.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-13 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised after a 4-plan /plan-review batch
  was single-threaded; the maintainer asked for automatic parallel fan-out gated on 2+ plans, with
  corrective actions handed to the coordinator, and extended the same idea to release-review as a named
  trial mode. Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED against source)

- `00-run-protocol.md` ALREADY defines controlled parallel read-only audit lanes (Section "Optional
  controlled parallel audit mode", :346-378): lanes must be read-only, must not edit tracked files,
  must not update registers/commit/push/assign official IDs/make final decisions; the main agent owns
  synthesis, dedup, IDs, registers, and commits; Sections 7/8/9 stay serial. So the DISCIPLINE already
  exists - this IPD makes it AUTO-ENGAGE and names the canonical trigger, rather than inventing rules.
- Both plan-review variants already reference the sibling policy files: `plan-review.md:10-11` and
  `plan-review-long.md:24-25` point at `../release-review/00-run-protocol.md` (and fix-decision-policy).
  So a convention defined THERE is inherited by both without duplication (single source, P8).
- release-review Sections 7 (implementation), 8 (final review), 9 (release execution) are REQUIRED to
  stay serial/continuous (00-run-protocol + the section files). Auto-parallel therefore applies ONLY to
  the audit phase (release-review Sections 2-6; plan-review's per-plan review/verify phase).
- The 4-plan batch this session showed the real hazards a parallel mode MUST handle: (a) concurrent
  writers to one git index collide - hence coordinator-owns-commits; (b) a lane reviewing one unit
  cannot see another's edits - hence a coordinator CROSS-UNIT conflict pass; (c) interactive OQ
  resolution is one-human-serial and cannot be fanned out.
- Subagents run in parallel with EACH OTHER but the coordinator blocks until they return (not
  fire-and-forget). The win is concurrent analysis, not background async.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Define the canonical auto-parallel convention once in `00-run-protocol.md`.** Extend the existing
   "Optional controlled parallel audit mode" into an "Auto-parallel read-only audit lanes" convention:
   - TRIGGER: engage automatically when there are >= 2 INDEPENDENT eligible units to audit (2+ plans in
     a plan-review batch; or 2+ independent audit surfaces in a release-review, e.g. code/tests/docs/
     packaging). With <= 1 unit, stay fully serial (fan-out is pure overhead). A flag may force-on or
     force-off (e.g. `--parallel`/`--no-parallel` / an equivalent instruction) but the DEFAULT is the
     auto rule.
   - LANES (parallel, read-only): each lane reviews ONE unit in isolation - read it, verify claims at
     `path:line` against source, apply the rubric + personas + security lens, and RETURN a findings
     report (+ proposed edits as suggestions). Lanes MUST NOT edit tracked files, resolve open
     questions, commit, push, assign official IDs, or make final decisions. (This is the existing lane
     rule, now the default when triggered.)
   - COORDINATOR (serial, sole writer): synthesizes lane reports; runs a CROSS-UNIT conflict/overlap
     pass (lanes cannot see each other); resolves open questions INTERACTIVELY with the human; applies
     all in-place edits; makes all path-scoped commits; sets terminal status. Everything that writes,
     decides with the human, or spans units happens here, one at a time.
   - HONEST SCOPE: parallel = the read/verify/rubric/propose phase ONLY. Synthesis, cross-unit pass,
     interactive resolution, edits, and commits are serial through the coordinator. Mutation/ship
     phases (release-review 7/8/9) never parallelize.
2. **release-review: make it a named trial MODE (not a new command).** In `README.md` and the relevant
   section framing, name the auto-engaged behavior "parallel audit mode (trial)"; announce when it
   engages (>=2 independent surfaces) and that Sections 2-6 fan out read-only while 7/8/9 stay serial.
   No new command/shim; `/release-review` auto-engages per the convention (or via the flag). Keep it
   marked TRIAL while we gain experience.
3. **plan-review-long: inherit the convention for multi-plan batches.** In `plan-review-long.md` (and
   the discover/review steps), state that when the scope ledger has >= 2 ELIGIBLE plans, the review/
   verify phase fans out one read-only lane per plan per the `00-run-protocol.md` convention, and the
   coordinator does synthesis + cross-plan conflict pass + interactive OQ resolution + all edits/commits
   serially. Single eligible plan -> serial as today.
4. **plan-review (single-file): document serial-by-design.** Add a one-line note that the portable
   single-file variant does NOT auto-fan-out (a lone portable file spawning subagents is awkward and not
   universally available); it reviews serially and points at plan-review-long for the parallel batch
   mode. Preserve the deliberate parity note between the two.
5. **Docs + DECISIONS.** DECISIONS entry (next free number) recording the auto-parallel convention, the
   >=2 trigger, the coordinator-owns-mutations rule, the serial mutation/ship phases, and that it is a
   TRIAL. Note it builds on the existing lane rules rather than inventing them.

## Deferred / out of scope

- True fire-and-forget background execution (not available; the coordinator blocks until lanes return).
- Parallelizing any WRITE, interactive-decision, or ship phase (explicitly forbidden by the convention).
- A separate `/release-review-parallel` command (rejected: release-review already has the lanes concept;
  a named mode avoids a duplicate runbook/shim).
- Cross-REPO parallel review (this is within-run, within-repo lanes).
- Tuning HOW MANY lanes at once / batching very large sets - start with one lane per unit; revisit if it
  strains context or tooling (open question).

## Open questions (v1 leans for review)

1. Trigger granularity for release-review: what counts as an "independent audit surface" for the >=2
   rule (code/tests/docs/packaging/schemas/deprecation)? (Lean: reuse the allowed lane scopes already
   listed in `00-run-protocol.md`; engage when 2+ of those are non-trivially present.)
2. Flag surface: exact opt-in/opt-out flag names, or purely instruction-driven for the trial? (Lean:
   instruction-driven + the auto rule for now; formalize flag names only if a CLI/command surface needs
   them.)
3. Lane count ceiling: cap concurrent lanes (e.g. to bound context/tooling load) or one-per-unit
   always? (Lean: one-per-unit for the trial; add a cap only if it bites.)
4. Should lanes propose concrete EDIT TEXT or only FINDINGS? (Lean: findings + optional proposed edits
   as suggestions; the coordinator keeps independent judgment and is the sole writer - do not let lane
   edit-text get rubber-stamped.)

## Dependencies / sequencing

- Independent of the 1.2.1/1.3.0 code fixes (this is workflow prose, no code).
- Touches release-review + both plan-review workflows + their shared `00-run-protocol.md`; land as one
  coherent change so the convention and its two consumers stay in sync (no drift).

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY: `.agents/workflows/release-review/00-run-protocol.md` (the canonical
   convention), `.agents/workflows/release-review/README.md` + the minimal Section-file framing needed
   to name the trial mode, `.agents/workflows/plan-review-long/plan-review-long.md` (+ its step files if
   needed), `.agents/workflows/plan-review/plan-review.md` (the serial-by-design note), and
   `DECISIONS.md` (next free number). Do NOT change the lane SAFETY rules (read-only, coordinator owns
   mutations, 7/8/9 serial) - only make them auto-engage. If a change seems to need more, STOP and
   report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: prose/workflow change (no unit test for instruction prose per repo policy); run the FULL
   test suite and paste the ACTUAL runner output; confirm `aw plan-names` clean and shims regenerate if
   any manifest description changed (none expected). If any test asserts workflow-file content, keep it
   green.
4. COMMIT only this IPD's touched files, PATH-SCOPED; never `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.

HARD MUST: paste the real test output; keep the lane safety rules (read-only lanes, serial coordinator
mutations, serial 7/8/9) intact; stay inside the scope fence; never push. Not auto-executed; requires
human approval.
