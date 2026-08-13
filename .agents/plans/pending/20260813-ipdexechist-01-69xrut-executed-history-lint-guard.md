# IPD: Lint gate - an executed IPD must carry an executed workflow-history entry

- Date: 2026-08-13
- Kind: child
- Concern: Nothing programmatically enforces that a plan filed as `Status: executed` (in a terminal directory) actually recorded an `executed` line in its `## Workflow history`. The ipd-lifecycle + `/plan-review` runbooks REQUIRE it (D52; the ipd-structure spec), and it is followed by hand today, but a missing executed-history line would pass every current lint check - a silent provenance gap.
- Scope: `agent_workflows/ipd_lint.py` (add one post-transition presence check + error id `IPD-S405`) and `tests/test_ipd_lint.py` (or the existing ipd-lint test module). Salvaged from the retired `20260807-ipd-history-01-wrt0wq` (which is otherwise superseded: E-03/E-04 already shipped; E-01/E-02 structured-history grammar declined per the free-form prose-provenance convention, D52).
- Status: to-review
- Highest E allocated: 02
- Author: opencode Opus 4.8
- Id: 69xrut
- Set: ipdexechist
- Order: 1
## Workflow history

- 2026-08-13 draft (opencode Opus 4.8): created to salvage the one still-useful, convention-compatible item (former E-05) from the retired ipd-history plan wrt0wq. This is a PRESENCE check that fits the shipped free-form workflow-history convention (D52); it does NOT impose a machine-readable history grammar (that structured-history idea, former E-01/E-02, was considered and declined 2026-08-13).

## Goal

Add a deterministic, fail-closed lint check so that a plan in a terminal directory with `Status: executed` MUST contain at least one `## Workflow history` line whose event token is `executed`. This turns the currently hand-followed "append an executed history entry before `git mv`" rule (D52; ipd-structure spec) into an enforced guard, without imposing any new history-line grammar on the shipped free-form convention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: The lint guard

- [ ] E-02 Add error id `IPD-S405` to `agent_workflows/ipd_lint.py`: at the `post-transition` checkpoint (and for a terminal-dir plan whose `Status:` is `executed`), verify the `## Workflow history` section contains at least one entry whose event token is `executed` (the token immediately after the leading `YYYY-MM-DD`, matching how existing lines read, e.g. `- 2026-08-13 executed (actor): ...`). Emit `IPD-S405` as a conformance error when absent. Do NOT require any transition/outcome grammar (free-form prose after the token is fine, per D52). Preserve the existing `legacy/not evaluated` disposition for un-migrated terminal-dir plans (the check applies when the plan is evaluated, e.g. `--phase post-transition`, not to a grandfathered legacy pass).
  - Depends on: none
  - Expected outcome: a terminal `executed` plan missing an `executed` history line fails lint with `IPD-S405`; a plan that has one passes; legacy grandfathered terminal plans are unaffected.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_lint.py` disposition vocabulary: `conforming` / `quarantined` / `legacy/not evaluated` / `error`; terminal-dir detection at `_is_terminal_dir` (~line 660); a terminal-dir file evaluated without `--legacy` yields `legacy/not evaluated` (lint_text ~673). The new check must run when the plan IS evaluated (post-transition), not override the grandfather path.
- Existing S-codes are `IPD-S401`..`IPD-S404`; `IPD-S405` is free.
- Workflow-history lines are free-form prose (D52, 2026-07-11), one appended line per workflow touch, shaped `- <YYYY-MM-DD> <event> (<actor>): <outcome>`; the event token IS reliably extractable even though the outcome is prose. This check keys only on the `executed` event token, so it is compatible with the free-form convention.
- The terminal transition (status change + history line + `git mv` + commit) is explicitly NOT an `E-*`/`V-*` item (ipd-structure spec); this guard checks the RESULT after transition, consistent with that.

## Findings

- Salvaged from `20260807-ipd-history-01-wrt0wq` E-05. That plan's E-03 (plan-review appends a reviewed history entry) and E-04 (approved/executed entries required before `git mv`) already SHIPPED (plan-review.md; AGENTS.md + ipd-lifecycle). Its E-01/E-02 (structured `[Status: x -> y]` grammar + `aw ipd log-event`) were DECLINED 2026-08-13 (they would reverse the deliberate free-form prose-provenance convention, D52, and are a spec-level decision if ever revisited). Only E-05 remained useful and convention-compatible; this plan is that item, right-sized.

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

- Optionally note the new `IPD-S405` guard in the ipd-structure spec's lint-rule list, if the reviewer finds a gap. No convention change (it enforces the existing D52 requirement).

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The disposition of the parent plan (retire wrt0wq; decline structured history; salvage only this guard) was decided by the human maintainer 2026-08-13. No open questions remain for this scoped item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: run the new ipd-lint tests and paste output - (a) a terminal `executed` fixture WITH an `executed` history line passes; (b) the same fixture WITHOUT that line fails with `IPD-S405` (falsifiable RED); (c) a legacy grandfathered terminal plan is unaffected. Also paste `aw ipd lint --phase post-transition` over a real `executed/` plan showing it is satisfied/grandfathered.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one deterministic lint guard enforcing an already-required, already-conventional provenance line.

Execution requires a GO `/plan-review` and explicit human approval. Scope fence: `agent_workflows/ipd_lint.py` (+ its test module) ONLY; do not touch history-line grammar, add a `log-event` CLI, or modify the free-form convention. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
