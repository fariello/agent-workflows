# IPD: release-review terminal Go/No-Go DECISION block + push-then-verify-CI-with-gh on approval

- Date: 2026-07-11
- Concern: release-review usability + release execution. Make the Go/No-Go decision unmissable as the
  LAST output, and make approved release execution actually push and verify CI (via `gh`) rather
  than only recommending - without weakening the explicit-approval safety gate.
- Scope: `.agents/workflows/release-review/` (notably `00-run-protocol.md`, `08-final-ship-review.md`,
  Section 9 / the push+CI phase, `templates/final-response.md`, and the `ci-assessment.md` /
  `11-push-plan.md` artifacts) + docs/DECISIONS. Does NOT change the audit sections' substance.
- Status: approved
- Approval: approved by maintainer 2026-07-11 (reviewed; OQ1-5 resolved; approval gate preserved).
  Ready to execute changes 1-4.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-11 drafted (its_direct/pt3-claude-opus-4.8-1m-us): stub from an interactive session;
  requirements decided with the maintainer. Awaiting flesh-out of open questions.
- 2026-07-11 to-review (its_direct/pt3-claude-opus-4.8-1m-us): OQ2-5 resolved with the maintainer
  (bounded-timeout CI poll; CONDITIONAL GO pushes only after conditions met + re-approval; report
  aggregate + every failing job; push target from 11-push-plan.md, explicit choice on multiple
  remotes). Plan-status IPD (D52) landed first, so change #5 adopts that convention and this IPD's
  DECISIONS entry is D53. Approach committed; promoted to to-review for /plan-review.
- 2026-07-11 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Re-opened the evidence: corrected the Step-0 source claims (cited Remote push policy `:399-401` +
  CI section `:425-427`; clarified ci-assessment.md/11-push-plan.md are generated, not templated).
  PR-2 (DECISION block is APPENDED after the full ~18-section report, not a truncation), PR-3
  (preserve lanes-must-not-push `:357` + Section-9-serial `:366`), PR-4 (update the existing "CI
  assessment summary" section in final-response.md:40). All OQs resolved. Status -> reviewed.

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

- Today (VERIFIED against source by /plan-review): `00-run-protocol.md:51` "never push/publish/deploy
  without explicit permission"; Section 9 (`:244`) is release execution, run only after
  GO/CONDITIONAL GO + explicit approval and never automatically; the "Remote push policy" (`:399-401`)
  is the controlling push text (creates `11-push-plan.md`, push only if permitted); the "CI and
  GitHub Actions" section (`:425-427`) writes `ci-assessment.md`. Both `ci-assessment.md` and
  `11-push-plan.md` are GENERATED artifacts (defined `:293`/`:290`) with NO template file (they are
  generated, not template-backed) - confirmed: only a "CI assessment summary" SECTION exists in
  `templates/final-response.md:40`. They frame CI as ASSESSMENT/recommendation, not push-then-verify.
  The final report (`templates/final-response.md`, ~18 sections per `:462`) is LARGE; the Section 8
  Go/No-Go + loud pending-plan WARNING live in `08-final-ship-review.md`. Parallel lanes must not push
  (`:357`) and Section 9 must stay serial (`:366`). So the approval gate and a CI-assessment slot
  already exist; this IPD makes the ending unmissable (block APPENDED after the full report) and turns
  CI assessment into actual push+verify on approval, in the serial Section-9 phase only.
- `gh` usage: the framework already uses `gh` opportunistically elsewhere (cross-OS CI watched via
  `gh run`); reuse that pattern. Must handle `gh` missing/unauthed.
- Safety: P10 (no push/remote changes without permission) is binding and preserved.
- Latest DECISIONS: D52 (the plan-status IPD landed); this adds D53.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

### 1. Mandate the terminal DECISION block as the LAST output
Add to `00-run-protocol.md` (and enforce in `08-final-ship-review.md` + `templates/final-response.md`):
the final response MUST END with a delimited DECISION block (a ruled banner) stating recommendation +
named blockers/pending items + the explicit "AWAITING YOUR GO/NO-GO ... nothing is pushed until you
do" line. It is a forcing function: nothing prints after it. Specify the exact block format in the
template so runs are consistent.
- PLAN-REVIEW NOTE (PR-2): the current final report is LARGE - `final-response.md:462` and the two
  tables plus ~18 named sections (summary, Fix Bar, validations, CI assessment, schema, personas,
  push/no-push, GO recommendation, ...). "Nothing prints after the block" must NOT be read as
  "replace the report". The DECISION block is APPENDED as the final element AFTER the full report
  body; the report still prints in full, then the block is the literal last thing. State this
  explicitly so the change is additive, not a truncation of the existing report.

### 2. Redefine the push phase as push-then-verify-CI (on approval only)
Rework the release-execution push step, whose controlling text is `00-run-protocol.md:244` (Section 9
gate), the **"Remote push policy" (`00-run-protocol.md:399-401`)**, and the **"CI and GitHub Actions"
section (`00-run-protocol.md:425-427`, which writes `ci-assessment.md`)** - cite these, not a vague
"Section 9". On explicit GO approval, push the approved ref, then use `gh` to find and poll the
triggered GitHub Actions run(s) with a BOUNDED timeout (OQ3), and report the outcome (green -> done;
red -> report the AGGREGATE plus EVERY failing workflow/job/step, OQ4). Record it in
`ci-assessment.md` and `11-push-plan.md` (what was pushed, the run URL/ID, and the result). Keep it
Section-9-gated (post-approval); the audit sections and the Go/No-Go are unchanged.
- PLAN-REVIEW NOTE (PR-3): preserve the parallelism rules - `00-run-protocol.md:357` ("Lanes must not
  push to a remote") and `:366` ("Section 9 release execution must remain serial"). The push + CI
  verify MUST run in the serial Section-9 phase, NEVER inside a parallel audit lane. Say so.
- CONDITIONAL GO (OQ2): a CONDITIONAL GO does not push; conditions are met, the human re-approves
  with an explicit GO, and then this same push-then-verify path runs.

### 3. `gh` graceful degradation
Specify behavior when `gh` is unavailable/unauthenticated or the remote is not GitHub: report that CI
could not be auto-verified, give the manual command / URL, and do NOT block or fail the release on
the tool's absence. "if available" is honored explicitly. Push target comes from `11-push-plan.md`
(remote + branch + ref); on multiple remotes or ambiguity, require an explicit human choice, never a
default guess (OQ5, P10).

### 4. Docs + DECISIONS
Reconcile the release-review README/docs and `00-run-protocol.md` narrative to describe the terminal
DECISION block and the push+CI-verify-on-approval behavior. Update the existing **"CI assessment
summary" section in `templates/final-response.md:40`** to cover the push+verify result (PR-4). Add
DECISIONS D53. Note the preserved approval gate so the change is not read as "auto-push".

### 5. Adopt the plan-status conventions (D52 landed first)
`20260711-1945-01-plan-status-vocabulary-and-workflow-provenance` executed first (D52), so this IPD
already follows that convention (front-matter readiness `Status:`, `## Workflow history`,
commit-not-push). Additionally, reconcile release-review's own commit discipline with D52 where it
touches plans, and confirm the terminal-DECISION-block wording does not conflict with D52's
commit-not-push posture (release-review still never pushes without the explicit GO gate).

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

1. **DECISION-block format/banner: RESOLVED at execution** - a ruled banner defined in
   `templates/final-response.md` (exact characters/field order chosen when the template is written;
   fields: recommendation, named blockers/pending items, the AWAITING-GO/NO-GO line). Detail, not
   approach.
2. **CONDITIONAL GO: RESOLVED** - a CONDITIONAL GO does NOT push yet. The human satisfies the named
   conditions, then gives explicit GO, and the SAME push-then-verify path runs. No push on a bare
   conditional.
3. **CI wait behavior: RESOLVED** - poll with a BOUNDED timeout (default ~10-15 min, statable): wait
   for the definitive green/red for typical runs, report progress; if it exceeds the timeout, report
   the `gh run` URL + last status and stop (never hang). Reuses the repo's own CI-watching pattern.
4. **Multi-run/matrix: RESOLVED** - on red, report the AGGREGATE pass/fail AND name EVERY failing
   job (matrix failures are often OS-specific; the full picture matters), not just the first.
5. **Push target: RESOLVED** - reuse `11-push-plan.md`, which names the exact remote + branch + ref
   the DECISION block references. If there are multiple remotes or any ambiguity (origin vs upstream,
   a fork), require an EXPLICIT human choice; never guess a default remote (P10).

## Plan-review record (2026-07-11)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off to move `approved`). Evidence re-opened against source; findings:
- PR-1 (accuracy): Step-0 source claims sharpened - cite the Remote push policy (`:399-401`) and the
  CI section (`:425-427`); clarified that `ci-assessment.md` and `11-push-plan.md` are generated (not
  template-backed) and only a "CI assessment summary" section exists in `final-response.md:40`.
- PR-2 (gap): DECISION block is APPENDED after the full ~18-section report (`final-response.md:462`),
  not a truncation - stated explicitly so the change is additive.
- PR-3 (gap): preserve `:357` (lanes must not push) and `:366` (Section 9 serial); push+verify runs
  only in the serial Section-9 phase.
- PR-4 (consistency): update the existing "CI assessment summary" section in `final-response.md:40`.
No new open questions; OQ1-5 all resolved. This IPD does not self-approve.

## Approval and execution gate

This IPD is `reviewed` (`/plan-review` done, revisions applied); awaiting explicit human sign-off to
move `approved`. NOT auto-executed. On approval: implement changes 1-4, validate manually (per
above), commit (never push - fittingly, this IPD's own execution follows the very commit-not-push
discipline it documents), then set `Status: executed` and
`git mv` to `.agents/plans/executed/`.
