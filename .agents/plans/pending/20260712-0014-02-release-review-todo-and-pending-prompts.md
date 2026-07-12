# IPD: /release-review pre-flight gates - cursory TODO.md review + pending plans/prompts prompt

- Date: 2026-07-12
- Concern: release-review completeness. Two related "did you mean to ship without addressing this?"
  gates that should be surfaced to the human EARLY, with an explicit abort-to-discuss path, rather
  than only noted in the final report.
- Scope: `.agents/workflows/release-review/` (Section 1 pre-flight / `00-run-protocol.md`,
  `08-final-ship-review.md`, and the pending-plans handling that already exists) + docs/DECISIONS.
  Behavioral: adds interactive prompts + an ABORT path; does not change the audit sections' substance.
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 drafted (its_direct/pt3-claude-opus-4.8-1m-us): captured from an interactive session
  (ITEM-02 + ITEM-03). Awaiting flesh-out.

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

## Open questions (to resolve during flesh-out / review)

1. Interaction with the non-interactive / lane model: what happens when `/release-review` runs
   non-interactively (no TTY to ask)? (Lean: skip the interactive ask, fall back to the existing
   loud WARNING in the report; never silently drop.)
2. Relationship to the existing final-report TODO/backlog reconciliation + pending-plans WARNING -
   keep both (early gate + final report), and make sure they do not contradict.
3. Exact "worth addressing before release?" heuristic for the cursory pass (keep it genuinely
   cursory, not a second full triage).
4. Does the pending-prompts gate also cover status/location mismatches (tie-in to D52/D54)?
5. Where the ABORT is recorded (a run artifact) so a resumed run knows why it stopped.

## Approval and execution gate

Proposal (`draft`). Flesh out -> `to-review` -> `/plan-review` -> resolve OQs -> human approve ->
execute -> validate -> commit (never push) -> `git mv` to executed/. Not auto-executed.
