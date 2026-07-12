# IPD: Release-review pre-flight gate - fire only on a real signal, and frame it verdict-free

- Date: 2026-07-12
- Concern: workflow correctness / review integrity. During a live release-review of this repo, the
  Section 1 pre-flight gate produced a badly-framed question: on a CLEAN repo (nothing found) it still
  fired an ask, and the agent, needing a reason to recommend "proceed", asserted "no blockers to
  discuss first" and pre-classified the one release signal as "not a pre-flight blocker". That LEAKED a
  readiness verdict before any audit ran, breaching the gate's own "cursory look, not a triage" /
  "zero residue, cannot bias the review" intent (00-run-protocol.md:201,204) and risking confirmation
  bias across Sections 2-8. Root cause (verified against source): the gate has (a) NO verdict-free
  framing rule anywhere; (b) NO guidance for the found-NOTHING case (it is written entirely around
  "if anything looks worth handling first"); and (c) example phrasing that primes a release-readiness
  framing ("these look like they might need attention before release ... or proceed?").
- Scope: `.agents/workflows/release-review/00-run-protocol.md` (the pre-flight gate definition,
  :197-205), `.agents/workflows/release-review/01-current-state.md` (the pointer to it, :40 + exit
  gate :102), and `.agents/workflows/release-review/README.md:68` (the runbook's own pre-flight summary,
  which also says "ask ONCE" and must not contradict the new conditional behavior; added by
  /plan-review-long PB-1); and, per OQ2 (hoist), the plan-review Memory kernels
  (`plan-review/plan-review.md`, `plan-review-long/plan-review-long.md`) gain the one-line no-verdict-leak
  principle. Docs/DECISIONS. Prose-only workflow change; the Section 8 terminal GO/NO-GO gate + 3-rung
  consent tree is UNCHANGED (it stays an unconditional interactive ask on every run).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised immediately after the defect was
  hit live (the aborted run 20260712-143730, deleted). Maintainer chose: pre-flight fires ONLY when a
  real signal exists (pending plans/prompts, status/location mismatch, obvious blocker), skips silently
  when clean, and is always verdict-free; the END gate stays an unconditional interactive ask. Complete
  proposal; born to-review.
- 2026-07-12 /plan-review-long (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  PB-1 (MEDIUM, internal-consistency): `README.md:68` also summarizes the gate as an unconditional "ask
  ONCE" and was MISSING from the original 2-file scope; leaving it would drift out of sync. Added to
  scope + change #5. OQ2 resolved (maintainer): HOIST the no-verdict-leak principle repo-wide (new
  change #6; plan-review Memory kernels added to scope). All cited path:line claims verified accurate.
  No BLOCKER/HIGH. Status -> reviewed.

- 2026-07-12 executed (its_direct/pt3-claude-opus-4.8-1m-us): implemented changes 1-7. Pre-flight gate
  reworded in `00-run-protocol.md` (conditional-on-signal, verdict-free framing rule, found-nothing
  skip); `01-current-state.md` pointer + exit gate updated; `README.md:68` summary synced; the
  no-verdict-leak principle hoisted into both plan-review Memory kernels (item 9); DECISIONS D72.
  Validated: full suite `212 passed in 44.34s`; `aw plan-names` clean; em/en-dash sweep 0. Committed
  path-scoped `3250c98` (never pushed). Section 8 terminal gate + 3-rung tree untouched, as scoped.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review-long` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH
REVISIONS APPLIED** (pending human sign-off).
- PB-1 (MEDIUM, rubric E, IN-SCOPE, FIXED): scope fence too narrow - `README.md:68` (the runbook's own
  pre-flight summary) says "ask ONCE" unconditionally and would contradict the reworded gate. Added it
  to scope + a change to keep it in sync. Remediation Risk: Low.
- OQ2 (FIXED via maintainer decision): hoist the no-verdict-leak principle repo-wide; added change #6
  (plan-review Memory kernels + one shared principle) and widened scope.
- Verified accurate (no finding): `00-run-protocol.md:197-205,204`, `01-current-state.md:40,102`; no
  other pre-flight references beyond the three now in scope. Rubric A (completeness) satisfied incl. the
  gate execution contract. No BLOCKER/HIGH remains. Does not self-approve.

## Project conventions discovered (Step 0, VERIFIED against source)

- Pre-flight gate lives in `00-run-protocol.md:197-205` and is pointed to from `01-current-state.md:40`
  with an exit-gate item at `01-current-state.md:102`. Its stated purpose (`:199`): catch "did you mean
  to ship without handling this?" before a full review.
- The residue rule (`:204`, "forget and proceed ... zero residue, cannot bias the review") governs what
  happens AFTER the answer; it does NOT constrain the FRAMING of the question. VERIFIED by
  `git grep` that NO "verdict-free / do not assert / neutral" framing rule exists anywhere in
  `.agents/workflows/release-review/`.
- The trigger (`:202`, "If anything looks worth handling first, ASK ...") is written only for the
  found-SOMETHING case; the found-NOTHING case has no phrasing guidance, which is the vacuum the agent
  filled with a premature "no blockers" verdict.
- The example phrasing (`:202`) embeds "before release", priming a readiness framing even though the
  gate is explicitly NOT a readiness assessment (that is Section 8's job).
- The non-interactive fallback (`:205`) already SKIPS the ask and relies on the Section 8 loud WARNING;
  making the interactive ask conditional-on-a-signal is consistent with that posture.
- Section 8 terminal gate (D53, D71): the mandated `RELEASE REVIEW DECISION` block + 3-rung consent
  tree is the real readiness verdict and interactive ask; it is unconditional and is NOT touched here.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Make the pre-flight ask CONDITIONAL on a real signal** (`00-run-protocol.md:201-202`). Reword so
   the interactive ask fires ONLY when the cursory look surfaces something that genuinely should be
   confirmed, addressed, or actively ignored before contemplating a release: a pending agent plan/IPD
   or staged prompt, a status/location mismatch, or an obviously risky/blocking TODO item. When the
   look is CLEAN (no such signal), SKIP the ask and proceed silently to the audit (do not manufacture a
   question, and do not manufacture a "nothing found" verdict). This mirrors the existing
   non-interactive skip (`:205`).
2. **Add a VERDICT-FREE framing rule** (new bullet in the gate). When the ask DOES fire, it MUST name
   the specific items found and ask what to do about them (address-first/abort vs. proceed); it MUST
   NOT assert or imply any release-readiness verdict - no "no blockers", "looks clean", "release-ready",
   or pre-classification of a signal as "not a blocker". The readiness call is Section 8's alone,
   earned from the full audit. Rationale: a gate question must not leak the verdict the gate precedes.
3. **Fix the example phrasing** (`:202`) to be verdict-free and item-anchored, e.g.: "Found <items>.
   Handle any of these before I audit (abort to discuss), or proceed?" Remove the "might need attention
   before release" readiness priming.
4. **Update `01-current-state.md`** (:40 pointer + :102 exit-gate item) to match: the pre-flight ask is
   conditional (fires only on a real signal), verdict-free when it fires, and skipped-when-clean; the
   exit-gate item reads "applied (asked only if a signal existed; verdict-free; else proceeded)".
5. **Update `README.md:68` (the runbook's own pre-flight summary)** so it does NOT contradict the new
   behavior. It currently says "ask ONCE whether anything should be handled ... On 'yes' the review
   ABORTS ... on 'no' it forgets the glance and proceeds" - an UNCONDITIONAL always-ask. Reword to:
   ask ONLY when the cursory look surfaces a real signal (else proceed silently), and keep it
   verdict-free. (Found by /plan-review-long PB-1: this file was missing from the original 2-file
   scope and would have drifted out of sync with `00-run-protocol.md`.)
6. **Hoist the no-verdict-leak principle repo-wide (OQ2 RESOLVED).** State it once in a shared home:
   `../release-review/00-run-protocol.md` already houses cross-cutting rules, but plan-review is a
   sibling family, so put the one-line principle where BOTH families see it - add it to the plan-review
   Memory kernel (`plan-review/plan-review.md` and `plan-review-long/plan-review-long.md`) AND reference
   it from the pre-flight gate: "An interactive gate/question MUST NOT assert or imply the verdict it
   precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is
   formed only from the gated work's evidence." Keep it terse; single definition referenced, not
   restated. This widens the fix from release-review-only to all interactive gates (maintainer chose
   to hoist now rather than defer).
7. **Docs + DECISIONS.** DECISIONS entry (next free number at execution time; likely D72/D73)
   recording the defect (premature verdict leak at a clean-repo pre-flight), the fix (conditional +
   verdict-free ask; end gate unchanged), the repo-wide no-verdict-leak principle (OQ2), and the
   motivating aborted run 20260712-143730.

## Deferred / out of scope

- The Section 8 terminal GO/NO-GO gate and 3-rung consent tree (D53/D71): unchanged; it stays an
  unconditional interactive ask every run.
- Generalizing the "gate question must not leak its verdict" rule into other workflows (e.g.
  plan-review interactive OQ prompts): worth considering later, but this IPD is scoped to the
  release-review pre-flight gate that actually failed. Capture as a possible follow-on.
- Any machine enforcement (this is instruction prose; no unit test for prose per repo policy).

## Open questions (v1 leans for review)

1. Found-nothing behavior: RESOLVED (maintainer) - SKIP the ask when clean; fire only on a real signal
   (pending plans/prompts, status/location mismatch, obvious blocker). The END gate still always asks.
2. Hoist the "no-verdict-leak" principle repo-wide? RESOLVED (maintainer) - YES, hoist it now. Add the
   principle "a gate question must not leak the verdict it precedes" to a shared home so it also covers
   `plan-review`/`plan-review-long` interactive OQ prompts and any future gate. See change #6.
3. When a signal fires and the user says "proceed anyway", does the zero-residue rule (:204) still
   apply? (Lean: yes, unchanged - the user acknowledged the item; the audit still runs independently
   and must not be biased by the glance.)

## Approval and execution gate

`to-review`. All findings are prose edits to the pre-flight gate; the fix's Remediation Risk is Low
(instruction clarity, no behavior-code change, end gate untouched). Execution contract (follow
EXACTLY):

1. SCOPE FENCE. Edit ONLY `.agents/workflows/release-review/00-run-protocol.md` (pre-flight gate
   :197-205), `.agents/workflows/release-review/01-current-state.md` (:40 pointer + :102 exit gate),
   `.agents/workflows/release-review/README.md:68` (the pre-flight summary), the plan-review Memory
   kernels `.agents/workflows/plan-review/plan-review.md` + `.agents/workflows/plan-review-long/plan-review-long.md`
   (one-line no-verdict-leak principle, change #6), plus `DECISIONS.md` (append the next free number,
   NOT a hardcoded D72 - IPD 1544-01 also targets D72; whichever lands second takes the next number).
   Do NOT touch the Section 8 gate, the 3-rung tree, or any other workflow. If a change seems to need
   more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: prose-only (no unit test for instruction prose per repo policy); run the FULL test suite
   and paste the ACTUAL runner output; confirm `aw plan-names` stays clean. If any test asserts
   workflow-file content, keep it green.
4. COMMIT only this IPD's touched files, PATH-SCOPED (`git commit -m msg -- <path> ...`); never
   `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit that move path-scoped.

HARD MUST: paste the real test output; stay inside the scope fence; never push. Not auto-executed;
requires human approval. THEN re-run `/release-review` fresh (per the maintainer's sequence:
fix the workflow first, then start the review anew).
