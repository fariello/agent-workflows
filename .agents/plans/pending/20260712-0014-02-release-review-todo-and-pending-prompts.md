# IPD: /release-review pre-flight gates - cursory TODO.md review + pending plans/prompts prompt

- Date: 2026-07-12
- Concern: release-review completeness. Two related "did you mean to ship without addressing this?"
  gates that should be surfaced to the human EARLY, with an explicit abort-to-discuss path, rather
  than only noted in the final report.
- Scope: `.agents/workflows/release-review/` (Section 1 pre-flight / `00-run-protocol.md`,
  `08-final-ship-review.md`, and the pending-plans handling that already exists) + docs/DECISIONS.
  Behavioral: adds interactive prompts + an ABORT path; does not change the audit sections' substance.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-02 + ITEM-03). Awaiting flesh-out.
- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): fleshed out against the existing
  release-review structure (Section 1 discovery; the TODO + pending-plans policies; the
  ask-the-user bounded exception). OQs leaned. Approach committed; promoted to to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Verified: no existing pre-flight gate to duplicate; `:166-168` intent-ask is the right precedent;
  Section 1 exit gate is the checkbox home. PB-1: state the gate is SERIAL/pre-lane (before parallel
  audit lanes) so an abort saves the whole run. PB-2: "forget and proceed" must not leak cursory
  judgments into findings/plan/report - Section 7 reconciles independently from the full list. OQs
  leaned; none escalated. Status -> reviewed.

## Project conventions discovered (Step 0, VERIFIED against source)

- Section 1 (`01-current-state.md`) ALREADY discovers/inventories both signals: backlog/TODO sources
  (:36) and pending agent plans + staged prompts (:37), and lists them for the Section 8 warning; its
  exit gate (:98-99) requires both be inventoried. So this IPD does NOT add discovery - it adds an
  EARLY INTERACTIVE GATE that consumes that Section 1 inventory before the audit proceeds.
- `00-run-protocol.md` has the substantive policies: "TODO.md and tracked-backlog reconciliation"
  (:170-182, the thorough triage feeding Section 7 + the Section 8 report) and "Pending agent plans
  and staged prompts" (:184-195, the loud Section 8 WARNING). This IPD adds the early ask+ABORT on
  TOP of these; the final-report reconciliation/WARNING stay.
- Precedent for pausing to ask: "Asking for missing intent (bounded exception to autonomous
  operation)" (:166-168) already sanctions a small, bounded set of questions to the user, degrading
  gracefully (non-interactive -> best-effort + record + continue). The new gates follow the SAME
  pattern: ask when interactive; when non-interactive, fall back to the existing loud WARNING, never
  silently drop.
- `.agents/prompts/pending/` may not exist in a given repo; discovery already tolerates absence.
- House rule: no em dashes in authored Markdown.

## Goal

1. **Cursory TODO.md review (ITEM-02).** If a `TODO.md` (or the project's backlog) exists,
   `/release-review` does a CURSORY pass and evaluates whether any item is plausibly worth addressing
   BEFORE this release. If yes, it ASKS the human. If the human says yes, `/release-review` ABORTS so
   the items can be discussed/addressed first. If the answer is no (nothing worth pre-release), it
   FORGETS everything it learned from the TODO and proceeds as if it never looked (no residue in the
   report, no re-litigating). This is distinct from the existing thorough TODO/backlog reconciliation
   in the final report - this is an early go/no-go sanity gate.
2. **Pending plans / prompts prompt (ITEM-03).** `/release-review` MUST ask about anything in
   `.agents/plans/pending/` and `.agents/prompts/pending/` (prepared-but-unexecuted plans/IPDs and
   staged prompts), with the SAME treatment as the TODO gate: if any look in-scope/worth-doing-first,
   ask; on yes, ABORT to discuss; on no, proceed. (Today these are surfaced as a WARNING in the
   Section 8 report; this adds the early interactive ask + abort path.)

## Decisions taken (maintainer, 2026-07-12)

1. Both gates run EARLY (pre-audit / Section 1 pre-flight) so an abort saves the whole review.
2. ABORT-to-discuss is a first-class outcome (not a NO-GO report at the end).
3. "Forget and proceed" on a no answer: the cursory look must not bias or clutter the rest of the
   run.

## Proposed changes (ordered, validatable)

1. **New "Section 1 pre-flight gate" in `00-run-protocol.md`.** After Section 1 discovery (which
   already inventories TODO sources and pending plans/prompts) and BEFORE the audit sections - and
   specifically BEFORE any parallel audit lanes start (PB-1: the gate is serial/pre-lane so an abort
   saves the whole run) - add an interactive pre-flight gate with two parts:
   - **TODO gate:** do a CURSORY pass over discovered `TODO.md`/backlog items (NOT the full Section-7
     triage) and judge whether any plausibly ought to be handled before this release. If yes, ASK the
     user (a short, specific question naming the candidate items). If the user says yes -> ABORT the
     run to discuss. If no -> FORGET the cursory impressions and proceed (PB-2: do NOT carry the
      cursory judgments into findings, the execution plan, or the report; the thorough Section-7
      reconciliation runs INDEPENDENTLY from the full item list, so this glance leaves no residue and
      cannot bias severity).
   - **Pending plans/prompts gate:** MUST ask about anything in `.agents/plans/pending/` and
     `.agents/prompts/pending/` (plus status/location mismatches), same ask -> ABORT-or-proceed
     shape.
2. **ABORT is a first-class outcome.** Define an explicit ABORTED-PRE-FLIGHT result: stop before the
   audit, record why (which gate, which items) in `00-run-metadata.md` (or a small
   `01-preflight-gate.md`), and tell the user how to resume after they have discussed/addressed the
   items. Distinct from a Section 8 NO-GO (which comes after a full audit).
3. **Non-interactive fallback (OQ1).** When there is no TTY (another IDE / CI runner), SKIP the
   interactive ask and fall back to the EXISTING loud Section 8 WARNING path - never silently drop,
   never block a headless run. Mirror the `:166-168` intent-question precedent exactly.
4. **Keep the existing reconciliation/WARNING (OQ2).** The Section 7 TODO reconciliation and the
   Section 8 pending-plans WARNING remain unchanged; the pre-flight gate is an ADDITIONAL early
   safety net, not a replacement. Cross-reference so they do not contradict.
5. **Wire Section 1 + exit gate.** Update `01-current-state.md` to run the pre-flight gate after
   discovery and record its outcome; add an exit-gate checkbox that the gate was applied (asked, or
   fell back to WARNING when non-interactive). Update the release-review README/reference + DECISIONS.

## Open questions (v1 leans for review)

1. **Non-interactive behavior: RESOLVED lean** - skip the ask, fall back to the existing loud WARNING;
   never silently drop or block (matches the `:166-168` precedent). Confirm.
2. **Relationship to existing reconciliation/WARNING: RESOLVED lean** - keep BOTH (early gate + final
   report); they are complementary. Confirm.
3. **"Worth before release?" heuristic: RESOLVED lean** - genuinely cursory (obvious release blockers
   / clearly-risky items only), explicitly NOT a second full triage; the thorough pass stays in
   Section 7. Confirm the phrasing keeps it light.
4. **Pending-prompts gate scope: RESOLVED lean** - cover `.agents/plans/pending/`,
   `.agents/prompts/pending/`, AND status/location mismatches (ties into D52/D54). Confirm.
5. **Where ABORT is recorded: RESOLVED lean** - `00-run-metadata.md` (a small dedicated
   `01-preflight-gate.md` if cleaner) with the gate + items + resume note. Confirm.
6. Should the two gates be ONE combined question or TWO separate asks? (Lean: present both signals in
   ONE bounded pre-flight prompt to minimize interruption, listing TODO candidates and pending
   plans/prompts together; the user answers once.)

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened: Section 1 already inventories both signals
(01-current-state.md:36-37, exit gate :98-99); the substantive policies live in 00-run-protocol.md
(:170-182 TODO, :184-195 pending plans); the ask-user bounded exception (:166-168) is the precedent
to mirror; no existing pre-flight gate exists to duplicate. Findings: PB-1 gate is serial/pre-lane
(abort saves the run); PB-2 "forget and proceed" must leave no residue in findings/plan/report. OQ1-6
leaned for confirmation. This is a prose-workflow change (no unit tests per the repo policy;
validation is dogfooded). This IPD does not self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ1-6 leans), execute changes 1-5, validate (dogfood +
suite green for any mechanical bits), commit (never push), `git mv` to executed/. Not auto-executed.
