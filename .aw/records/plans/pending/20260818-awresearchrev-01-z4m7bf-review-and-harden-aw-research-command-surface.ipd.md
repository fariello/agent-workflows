# IPD: review and harden aw research command surface

- Date: 2026-08-18
- Kind: child
- Concern: The `aw research` command surface (subparsers at cli.py:770: new, new-comparison, set-assign, mv, check-refs, index, find, promote, check-miscategorized; backends research_cmd/research_refs/research_index/research_archive; its own `.<model>.<kind>.md` grammar in research_contract.py) grew organically and, under the new noun-verb grammar being introduced by Set awcmdsurf, several research subverbs (find/index/mv/set-assign/archive) now OVERLAP the cross-cutting verbs (`aw find/index/rename/group/archive research`). TODO item #30 asks to confirm the surface is well thought out; this is a REVIEW-and-harden task, not a large build - audit for consistency with the new grammar, decide which subverbs should fold into the cross-cutting verbs vs stay research-specific (new/new-comparison/promote/check-miscategorized), document the findings, and apply the modest agreed fixes.
- Scope: IN: a focused audit of the research subverb surface against the awcmdsurf noun-verb grammar, a documented recommendation of fold-vs-keep per subverb, and the small consistency fixes that are clearly agreed (with a test). OUT: any large rewrite of the research backends or its `.<model>.<kind>.md` grammar; the actual cross-cutting-verb implementation (that is Set awcmdsurf); anything requiring a maintainer judgment call (captured as an OQ rather than changed unilaterally).
- Status: draft
- Set: awresearchrev
- Order: 1
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: z4m7bf

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): from TODO item #30; audit the aw research surface for consistency with the awcmdsurf noun-verb grammar and apply modest agreed fixes.

## Goal

Confirm the `aw research` command surface is coherent under the new noun-verb grammar, document which
subverbs should fold into the cross-cutting verbs vs stay research-specific, and apply the small,
clearly-agreed consistency fixes - keeping this a modest review-and-harden, not a rewrite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: audit

- [ ] E-01 Audit the research subverb surface (cli.py:770: new, new-comparison, set-assign, mv, check-refs, index, find, promote, check-miscategorized) against the awcmdsurf noun-verb grammar and produce a documented fold-vs-keep recommendation per subverb: which map onto the cross-cutting `aw find/index/rename/group/archive research` (candidates: find, index, mv, set-assign, and any archive) and which stay research-specific (new, new-comparison, promote, check-miscategorized). Record the findings in this IPD's Findings table.
  - Depends on: none
  - Expected outcome: a per-subverb fold-vs-keep table exists in this plan, with rationale and any coordination notes with Set awcmdsurf.
  - Execution state: pending

### Task group 2: harden

- [ ] E-02 Apply the modest, clearly-agreed consistency fixes surfaced by E-01 (e.g. aligning flag/help/exit-code conventions, or wiring an alias/deprecation note where a research subverb overlaps a cross-cutting verb) that do NOT require a maintainer judgment call, and add or update a test asserting the fixed behavior. Anything needing a maintainer decision is left as an OQ rather than changed.
  - Depends on: E-01
  - Expected outcome: the agreed fixes land with a passing test; contested items are captured as OQs, not silently changed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Research subparsers live at cli.py:770 with backends research_cmd/research_refs/research_index/research_archive; research keeps its own artifact grammar `.<model>.<kind>.md` (research_contract.py) distinct from the plan/spec naming grammar.
- Set awcmdsurf introduces cross-cutting verbs (`find/search/index/rename/group/archive/check <type>`); research is one of the types, so several research subverbs now have a cross-cutting equivalent.
- Fold-vs-keep is the crux: mechanical, type-generic operations (find/index/mv/set-assign/archive) are natural cross-cutting-verb candidates; research-domain-specific operations (new, new-comparison, promote, check-miscategorized) should stay under `aw research`.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | research subverbs find/index/mv/set-assign/archive overlap the awcmdsurf cross-cutting verbs. | These are fold candidates; E-01 records the recommendation and coordinates with awcmdsurf. |
| F2 | new/new-comparison/promote/check-miscategorized are research-domain-specific. | These stay under `aw research`; no fold. |
| F3 | Research uses its own `.<model>.<kind>.md` grammar. | Any fold must preserve research's naming/contract; the cross-cutting verb dispatches into the research backend, not the plans one. |
| F4 | This is a review task per TODO #30, not a rebuild. | Keep changes modest; escalate judgment calls to OQ. |

## Proposed changes (ordered, validatable)

1. Produce the documented fold-vs-keep audit and record it in Findings (E-01). 2. Apply the modest agreed consistency fixes + a test; capture contested items as OQs (E-02).

## Deferred / out of scope (with reason)

- Implementing the cross-cutting verbs themselves: that is Set awcmdsurf; this plan only audits research's relationship to them and applies research-side alignment.
- Any rewrite of the research backends or the `.<model>.<kind>.md` grammar: out of scope; explicitly a review-and-harden.
- Fold decisions that require a maintainer call: deferred to OQ, not changed unilaterally.

## Scope check

- Over-scope: none - no backend rewrite; contested changes are deferred to OQ.
- Under-scope: none - the audit is documented and the clearly-agreed fixes are applied and tested.

## Required tests / validation

The E-02 test for whatever consistency fix lands, plus the full serial suite; the audit itself is validated by the documented fold-vs-keep table with rationale.

## Spec / documentation sync

Update the `aw research` help text if any subverb is aliased/deprecated in favor of a cross-cutting verb; coordinate wording with Set awcmdsurf. Otherwise N/A.

## Open questions

### OQ-01: which overlapping research subverbs should be aliased vs hard-deprecated once the awcmdsurf cross-cutting verbs land?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Recommendation: keep overlapping research subverbs as thin aliases into the cross-cutting verbs initially (no breakage), and let a maintainer decide any hard-deprecation timeline; this coordinates with Set awcmdsurf and is non-blocking for the audit.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the completed fold-vs-keep table from Findings with per-subverb rationale and the awcmdsurf coordination note.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the diff summary of the applied consistency fix(es), the passing test run asserting the new behavior, and the list of items deferred to OQ rather than changed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The executor
(opencode Opus 4.8, or Gemini via `agy` with opencode owning verification and commits) performs each E,
verifies each V with pasted evidence, commits path-scoped, never pushes, and transitions the plan into
`executed/` only after `aw ipd lint --phase pre-transition` conforms and every V is `pass`. Coordinates
with Set awcmdsurf.
