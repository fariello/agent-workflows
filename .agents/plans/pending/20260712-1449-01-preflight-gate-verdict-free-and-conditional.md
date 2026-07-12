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
  :197-205) and `.agents/workflows/release-review/01-current-state.md` (the pointer to it, :40 + exit
  gate :102). Docs/DECISIONS. Prose-only workflow change; the Section 8 terminal GO/NO-GO gate + 3-rung
  consent tree is UNCHANGED (it stays an unconditional interactive ask on every run).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised immediately after the defect was
  hit live (the aborted run 20260712-143730, deleted). Maintainer chose: pre-flight fires ONLY when a
  real signal exists (pending plans/prompts, status/location mismatch, obvious blocker), skips silently
  when clean, and is always verdict-free; the END gate stays an unconditional interactive ask. Complete
  proposal; born to-review.

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
5. **Docs + DECISIONS.** DECISIONS entry (Dnn = D72) recording the defect (premature verdict leak at a
   clean-repo pre-flight), the fix (conditional + verdict-free ask; end gate unchanged), and the
   general principle "a gate question must not leak the verdict it precedes". Note the aborted run
   20260712-143730 as the motivating incident.

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
2. Should the "gate question must not leak its verdict" principle be hoisted repo-wide now, or kept
   local to release-review for this IPD? (Lean: keep local now; note a follow-on. The maintainer may
   widen it.)
3. When a signal fires and the user says "proceed anyway", does the zero-residue rule (:204) still
   apply? (Lean: yes, unchanged - the user acknowledged the item; the audit still runs independently
   and must not be biased by the glance.)

## Approval and execution gate

`to-review`. All findings are prose edits to the pre-flight gate; the fix's Remediation Risk is Low
(instruction clarity, no behavior-code change, end gate untouched). Execution contract (follow
EXACTLY):

1. SCOPE FENCE. Edit ONLY `.agents/workflows/release-review/00-run-protocol.md` (pre-flight gate
   :197-205) and `.agents/workflows/release-review/01-current-state.md` (:40 pointer + :102 exit gate),
   plus `DECISIONS.md` (append D72). Do NOT touch the Section 8 gate, the 3-rung tree, or any other
   workflow. If a change seems to need more, STOP and report.
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
