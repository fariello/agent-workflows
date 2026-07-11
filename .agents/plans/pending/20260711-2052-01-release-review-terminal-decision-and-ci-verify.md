# IPD: release-review terminal Go/No-Go DECISION block + push-then-verify-CI-with-gh on approval

- Date: 2026-07-11
- Concern: release-review usability + release execution. Make the Go/No-Go decision unmissable as the
  LAST output, and make approved release execution actually push and verify CI (via `gh`) rather
  than only recommending - without weakening the explicit-approval safety gate.
- Scope: `.agents/workflows/release-review/` (notably `00-run-protocol.md`, `08-final-ship-review.md`,
  Section 9 / the push+CI phase, `templates/final-response.md`, and the `ci-assessment.md` /
  `11-push-plan.md` artifacts) + docs/DECISIONS. Does NOT change the audit sections' substance.
- Status: draft
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 drafted (its_direct/pt3-claude-opus-4.8-1m-us): stub from an interactive session;
  requirements decided with the maintainer. Awaiting flesh-out of open questions.

## Goal

Two related release-review improvements: (1) the human's Go/No-Go decision, and the fact that the
workflow has STOPPED and is awaiting that call, must be the clearly-delimited LAST thing printed -
not buried in a wall of report text; (2) once the human approves release execution, release-review
must actually PUSH and then VERIFY the resulting CI run via `gh` (report pass/fail, wait for
completion), degrading gracefully when `gh` is unavailable - instead of merely producing a
push/CI recommendation. The explicit-approval safety gate (P10) is preserved.

## Decisions taken (maintainer, 2026-07-11)

1. **Unmissable terminal DECISION block.** After all report text and artifact paths, release-review's
   FINAL output is a visually-distinct, ruled DECISION block containing: the recommendation
   (GO / CONDITIONAL GO / NO-GO), any blocking or pending items named explicitly, and one clear line:
   "AWAITING YOUR GO/NO-GO. Reply GO to approve release execution (push + CI verify); nothing is
   pushed until you do." The controlling file MUST mandate this block be literally the last output -
   nothing (no summary, findings, or paths) prints after it.
2. **Keep the approval gate (P10).** Pushing remains Section 9 / release-execution, run ONLY after a
   GO or CONDITIONAL GO and explicit human approval. No surprise pushes for downstream users. (This
   is NOT "always auto-push".)
3. **On approval: push, THEN verify CI with `gh`.** When release execution proceeds, it MUST push and
   then poll GitHub Actions via `gh run` (identify the triggered run(s), wait for completion, report
   green/red with the failing job/step if red), rather than only recommending a push. If `gh` is
   absent/unauthenticated/not a GitHub remote, say so plainly and provide the manual check command;
   never fail the release on a missing tool - degrade gracefully.

## Project conventions discovered (Step 0)

- Today: `00-run-protocol.md:51` "never push/publish/deploy without explicit permission";
  Section 9 (`:244`) is release execution, run only after GO/CONDITIONAL GO + explicit approval and
  never automatically. Artifacts `ci-assessment.md` and `11-push-plan.md` already exist but frame CI
  as ASSESSMENT/recommendation, not push-then-verify. The final report uses
  `templates/final-response.md`; the Section 8 Go/No-Go + loud pending-plan WARNING live in
  `08-final-ship-review.md`. So the approval gate and a CI-assessment slot already exist; this IPD
  makes the ending unmissable and turns CI assessment into actual push+verify on approval.
- `gh` usage: the framework already uses `gh` opportunistically elsewhere (cross-OS CI watched via
  `gh run`); reuse that pattern. Must handle `gh` missing/unauthed.
- Safety: P10 (no push/remote changes without permission) is binding and preserved.
- Latest DECISIONS: D51 (this adds D53, assuming the plan-status IPD takes D52).
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

### 1. Mandate the terminal DECISION block as the LAST output
Add to `00-run-protocol.md` (and enforce in `08-final-ship-review.md` + `templates/final-response.md`):
the final response MUST END with a delimited DECISION block (a ruled banner) stating recommendation +
named blockers/pending items + the explicit "AWAITING YOUR GO/NO-GO ... nothing is pushed until you
do" line. It is a forcing function: nothing prints after it. Specify the exact block format in the
template so runs are consistent.

### 2. Redefine the push phase as push-then-verify-CI (on approval only)
Rework Section 9 / the push step: on explicit GO approval, push the approved ref, then use `gh` to
find and WAIT on the triggered GitHub Actions run(s) and report the outcome (green -> done; red ->
name the failing workflow/job/step and surface it). Record it in `ci-assessment.md` /
`11-push-plan.md` (what was pushed, the run URL/ID, and the result). Keep it Section-9-gated
(post-approval) - the audit sections and the Go/No-Go are unchanged.

### 3. `gh` graceful degradation
Specify behavior when `gh` is unavailable/unauthenticated or the remote is not GitHub: report that CI
could not be auto-verified, give the manual command / URL, and do NOT block or fail the release on
the tool's absence. "if available" is honored explicitly.

### 4. Docs + DECISIONS
Reconcile the release-review README/docs and `00-run-protocol.md` narrative to describe the terminal
DECISION block and the push+CI-verify-on-approval behavior. Add DECISIONS D53. Note the preserved
approval gate so the change is not read as "auto-push".

### 5. (If the plan-status IPD lands) adopt its conventions
If `20260711-1945-01-plan-status-vocabulary-and-workflow-provenance` executes first, this IPD's own
Status/Workflow-history follow that convention, and release-review's own commit discipline aligns
with it. Independent otherwise (sequence-agnostic; reconcile against whichever lands first).

## Deferred / out of scope

- "Always auto-push with no approval" - rejected (violates P10; surprises downstream users).
- A configurable auto-push opt-in - deferred; can be a follow-on if wanted, but not shipped as
  default behavior here.
- Changing the audit sections (1-8) substance - unchanged; this is ending-UX + release-execution
  mechanics only.

## Scope check (P6 / P7)

Additive/behavioral within release-review: a mandated final block (forcing function, no new
subsystem) + turning an existing CI-assessment slot into push-then-verify on approval + `gh`
graceful degradation. Approval gate preserved, so no new risk for downstream users. General-case:
benefits any repo; `gh`-optional so non-GitHub repos are unaffected.

## Required tests / validation

Prose workflow (not unit-tested per the repo's "test mechanical parts, not instruction prose"
policy). Validation is manual/dogfooded: run `/release-review` on this repo and confirm the final
output is the DECISION block (nothing after it); on a GO, confirm it pushes and reports the CI run
via `gh`; simulate `gh` absent and confirm graceful degradation with a manual command. Any
mechanical helper added (e.g. a CI-poll snippet) gets a test.

## Spec / documentation sync

Change #4 (release-review docs + DECISIONS D53). No product-code behavior change beyond release
execution mechanics; the safety posture (approval-gated push) is unchanged.

## Open questions

1. Exact DECISION-block format/banner (characters, fields order) - define in
   `templates/final-response.md`.
2. CONDITIONAL GO: does push+CI-verify apply the same way (push after the named conditions are
   satisfied + approved), or only on a clean GO?
3. CI wait behavior: block until the run completes (with a timeout), or report the run URL/ID and a
   status snapshot without long-waiting? (Cross-OS matrix runs can take minutes.)
4. Multi-run/matrix: report the aggregate plus the first failing job, or every job?
5. Where the push target/branch/remote is confirmed (reuse `11-push-plan.md`), and behavior when
   there are multiple remotes.

## Approval and execution gate

This IPD is a proposal (currently `draft`; not yet `to-review`). Flesh out the open questions, move
to `to-review`, optionally `/plan-review`, and human-approve before execution. NOT auto-executed. On
approval: implement changes 1-4, validate manually (per above), commit (never push - ironically this
IPD's own execution follows the very commit-not-push discipline), then set `Status: executed` and
`git mv` to `.agents/plans/executed/`.
