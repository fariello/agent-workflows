# IPD: Lint gate - an executed IPD must carry an executed workflow-history entry

- Date: 2026-08-13
- Kind: child
- Concern: Nothing programmatically enforces that a plan filed as `Status: executed` (in a terminal directory) actually recorded an `executed` line in its `## Workflow history`. The ipd-lifecycle + `/plan-review` runbooks REQUIRE it (D52; the ipd-structure spec), and it is followed by hand today, but a missing executed-history line would pass every current lint check - a silent provenance gap.
- Scope: `agent_workflows/ipd_lint.py` (add one post-transition presence check + error id `IPD-S405`) and `tests/test_ipd_lint.py` (or the existing ipd-lint test module). Salvaged from the retired `20260807-ipd-history-01-wrt0wq` (which is otherwise superseded: E-03/E-04 already shipped; E-01/E-02 structured-history grammar declined per the free-form prose-provenance convention, D52).
- Status: approved
- Approval: the human maintainer, 2026-08-15 (via chat) - approved for execution by Gemini 3.7 Flash High (second executor benchmark).
- Highest E allocated: 02
- Author: opencode Opus 4.8
- Id: 69xrut
- Set: ipdexechist
- Order: 1

## Workflow history

- 2026-08-13 draft (opencode Opus 4.8): created to salvage the one still-useful, convention-compatible item (former E-05) from the retired ipd-history plan wrt0wq. This is a PRESENCE check that fits the shipped free-form workflow-history convention (D52); it does NOT impose a machine-readable history grammar (that structured-history idea, former E-01/E-02, was considered and declined 2026-08-13, D131).
- 2026-08-13 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003. Verified from evidence that `lint_text` (ipd_lint.py:672) short-circuits terminal-dir plans to `legacy/not evaluated` before checks run, so the original E-02 ("check at post-transition, preserve the grandfather") was internally contradictory (PR-001, HIGH); rewrote E-02 to reconcile it and confirmed the spec (20260802-1904-01 S9.2 item 16) already REQUIRES the post-transition history-agreement this implements (PR-002); tightened V-02 to pin the exact post-PR-001 behavior + a mutation probe (PR-003). Scope decision (S405 going-forward only, legacy corpus stays grandfathered) resolved with the human maintainer and recorded in E-02. Structural lint conforming (author + review-finalize). Status to-review -> reviewed. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-08-15 re-validated (opencode Opus 4.8, orchestrator): confirmed still non-stale before approval - `ipd_lint.py` exists, `lint_text` terminal-dir short-circuit is at :672-674 (PR-001 claim still accurate), and IPD-S405 is not yet present (real unshipped work). Structural lint conforming.
- 2026-08-15 approved (the human maintainer, via chat; recorded by opencode Opus 4.8): approved for execution as the second Gemini 3.7 Flash High executor benchmark (a less pre-chewed plan than 0g0rid). Plans carry no TTY floor; attributed human approval, not agent self-approval. Status reviewed -> approved.

## Goal

Add a deterministic, fail-closed lint check so that a plan in a terminal directory with `Status: executed` MUST contain at least one `## Workflow history` line whose event token is `executed`. This turns the currently hand-followed "append an executed history entry before `git mv`" rule (D52; ipd-structure spec) into an enforced guard, without imposing any new history-line grammar on the shipped free-form convention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: The lint guard

- [x] E-02 Add error id `IPD-S405` to `agent_workflows/ipd_lint.py` enforcing that a `Status: executed` plan carries an `executed` `## Workflow history` line (the token immediately after the leading `YYYY-MM-DD`, e.g. `- 2026-08-13 executed (actor): ...`; free-form prose after the token is fine per D52, no transition/outcome grammar). MUST RESOLVE the gate conflict (see Findings PR-001): `lint_text` (ipd_lint.py:~672) currently short-circuits EVERY terminal-dir plan to `legacy/not evaluated` BEFORE `check_checkpoint` runs, so `--phase post-transition` on a moved executed plan evaluates nothing today. The executor MUST make the S405 history check run at `post-transition` on the just-transitioned plan (the ipd-lifecycle step-5 invocation, ipd-lifecycle.md:71) WITHOUT re-imposing the full structural linter on the historical `executed/` corpus - i.e. the legacy grandfather stays for the other structural checks, but a `post-transition` evaluation performs the S405 history-presence check. This implements spec `20260802-1904-01` Section 9.2 item 16 (post-transition MUST verify the workflow-history entry agrees), which is specified but currently unimplemented. SCOPE DECISION (resolved 2026-08-13, human maintainer): GOING-FORWARD ONLY. S405 fires ONLY when a plan is evaluated at `--phase post-transition` (the ipd-lifecycle step-5 invocation on the just-transitioned plan). The historical `executed/` corpus MUST keep returning `legacy/not evaluated` under default evaluation and MUST NOT be newly failed; do NOT audit or migrate old plans, and do NOT make S405 fire under `--legacy` or default terminal-dir evaluation. Minimal mechanism: run the S405 history-presence check inside the `post-transition` path only (e.g. before/around the terminal-dir grandfather return, guarded on `checkpoint == "post-transition"`), leaving every other structural check grandfathered for terminal-dir plans. STOP-and-report if it cannot be done without broadening legacy-corpus linting.
  - Depends on: none
  - Expected outcome: `aw ipd lint --phase post-transition` on a just-transitioned executed plan MISSING an `executed` history line fails with `IPD-S405`; the same plan WITH the line passes; the historical `executed/` corpus under DEFAULT evaluation still returns `legacy/not evaluated` and is NOT newly failed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `ipd_lint.py` disposition vocabulary: `conforming` / `quarantined` / `legacy/not evaluated` / `error`; terminal-dir detection at `_is_terminal_dir` (~line 660); a terminal-dir file evaluated without `--legacy` yields `legacy/not evaluated` (lint_text ~673). The new check must run when the plan IS evaluated (post-transition), not override the grandfather path.
- Existing S-codes are `IPD-S401`..`IPD-S404`; `IPD-S405` is free.
- Workflow-history lines are free-form prose (D52, 2026-07-11), one appended line per workflow touch, shaped `- <YYYY-MM-DD> <event> (<actor>): <outcome>`; the event token IS reliably extractable even though the outcome is prose. This check keys only on the `executed` event token, so it is compatible with the free-form convention.
- The terminal transition (status change + history line + `git mv` + commit) is explicitly NOT an `E-*`/`V-*` item (ipd-structure spec); this guard checks the RESULT after transition, consistent with that.

## Findings

- Salvaged from `20260807-ipd-history-01-wrt0wq` E-05. That plan's E-03 (plan-review appends a reviewed history entry) and E-04 (approved/executed entries required before `git mv`) already SHIPPED (plan-review.md; AGENTS.md + ipd-lifecycle). Its E-01/E-02 (structured `[Status: x -> y]` grammar + `aw ipd log-event`) were DECLINED 2026-08-13 (D131). Only E-05 remained useful and convention-compatible; this plan is that item, right-sized.
- PR-001 (review 2026-08-13, HIGH, verified): `lint_text` (ipd_lint.py:672-673) returns `LintResult(DISPOSITION_LEGACY, [])` for ANY terminal-dir plan (`executed`/`superseded`/`not-executed`) unless `legacy=True`, BEFORE `check_checkpoint` runs. So `aw ipd lint --phase post-transition` on a moved executed plan currently evaluates NOTHING (returns `legacy/not evaluated`, exit 0) - observed on every awphysical transition. The original E-02 framing ("preserve the legacy grandfather; check at post-transition") was internally contradictory: the grandfather is exactly what blocks the check. E-02 rewritten to require reconciling this: run S405 at post-transition on the just-transitioned plan without broadening legacy-corpus linting.
- PR-002 (review, MEDIUM, verified): the spec `20260802-1904-01-ipd-structure-and-linting.spec.md` ALREADY requires this. Section 9.2 item 16 (spec:444): "terminal status, history, directory, and lifecycle-commit metadata agree at `post-transition`"; Section 10 table (spec:419): post-transition verifies "workflow-history entry ... agree". And `checkpoint_allows_status` (ipd_schema.py:517) says post-transition is "only meaningful once terminal". So S405 IMPLEMENTS a specified-but-unimplemented requirement; it is not a new convention. Spec-sync updated accordingly.
- PR-003 (review, MEDIUM, verified): V-02's "over a real executed/ plan showing it is satisfied/grandfathered" was ambiguous given PR-001. V-02 rewritten to pin exact behavior: S405 fires at post-transition on a missing-line fixture (RED), passes with the line, and the historical `executed/` corpus is not newly failed.

## Proposed changes (ordered, validatable)

1. `ipd_lint.py`: add `IPD-S405`; in the post-transition path, for a terminal-dir `Status: executed` plan, scan `## Workflow history` bullet lines and require at least one whose first token after the date is `executed`; emit the error if none.
2. Tests: a plan WITH an executed history line passes; an otherwise-identical plan WITHOUT one fails with `IPD-S405`; a legacy grandfathered terminal plan is unaffected.

## Deferred / out of scope (with reason)

- Machine-readable / structured workflow-history grammar and an `aw ipd log-event` CLU (former ipd-history E-01/E-02): declined 2026-08-13 (conflicts with the shipped free-form prose convention, D52; would be its own spec/DECISIONS change).
- Retroactively adding executed-history lines to the existing `executed/` corpus: out of scope; legacy terminal plans stay grandfathered (`legacy/not evaluated`).

## Scope check

- Over-scope: none - a single presence check + tests.
- Under-scope: the check, its error id, and falsifiable tests (present-passes / absent-fails / legacy-unaffected) are included.

## Required tests / validation

- New ipd-lint tests: executed-with-history passes; executed-without-history fails `IPD-S405`; legacy grandfathered terminal plan unaffected.
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- Sanity: `aw ipd lint --phase post-transition` over this repo's real `executed/` plans behaves as intended (they carry executed lines, or are grandfathered legacy).
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- `IPD-S405` IMPLEMENTS spec `20260802-1904-01-ipd-structure-and-linting.spec.md` Section 9.2 item 16 / Section 10 post-transition row (workflow-history entry agreement), which is specified but currently unimplemented (verified PR-002). Update that spec's lint-rule list / error-code table to name `IPD-S405` as the concrete check for the post-transition history-agreement requirement. This is NOT a convention change (it enforces the existing D52 + spec requirement).

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The disposition of the parent plan (retire wrt0wq; decline structured history; salvage only this guard) was decided by the human maintainer 2026-08-13. No open questions remain for this scoped item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-02 validates E-02
  - Required evidence: run the new ipd-lint tests and paste output pinning the exact post-PR-001 behavior: (a) `lint_text`/`lint_file` at `--phase post-transition` on a terminal `executed` fixture WITH an `executed` history line -> conforming (no IPD-S405); (b) the same fixture WITHOUT that line at `--phase post-transition` -> error including `IPD-S405` (falsifiable RED); (c) the historical `executed/` corpus is NOT newly failed - e.g. a real executed plan lacking the line under the DEFAULT (non-post-transition) evaluation still returns `legacy/not evaluated` (grandfather preserved for structural checks), demonstrating S405 does not blanket-fail the corpus. Additionally mutation-probe: with the S405 check disabled, (b) goes GREEN (proving the test gates real behavior). Paste actual `aw ipd lint --phase post-transition` output for a real transitioned plan.
  - Observed evidence: `PostTransitionExecutedHistoryTests` in `tests/test_ipd_lint.py` passed (4/4 tests: with history conforms; without history fails IPD-S405; default evaluation on terminal dir returns legacy; real executed plan conforms at post-transition). Mutation probe demonstrated RED on disabling S405 (`AssertionError: 'conforming' != 'error'`) and GREEN on restoration. Actual CLI runs: `aw ipd lint --phase post-transition .agents/plans/executed/20260815-humanapproval-01-0g0rid-by-human-attestation.md` output `disposition: conforming` (exit 0); `aw ipd lint --all .` returned `counts: conforming=4, quarantined=0, legacy/not evaluated=159, error=0` (exit 0); full test suite passed (934 passed, 1 skipped).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one deterministic lint guard enforcing an already-required, already-conventional provenance line.

Execution requires a GO `/plan-review` and explicit human approval. Scope fence: `agent_workflows/ipd_lint.py` (+ its test module) ONLY; do not touch history-line grammar, add a `log-event` CLI, or modify the free-form convention. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
