- Id: yos8rq
- Status: graduated
- Graduated-To: citesym
- Set: yos8rq
- Priority: medium
- Work-Kind: chore
- Summary: plan-review mandates path:line citations but never says to re-locate by symbol, so line drift reads as a false claim

## Workflow history
- 2026-09-25 graduated (aw set): graduated into citesym plan x7i14a (review-side half; authoring half shipped via mzc019)
- 2026-09-16 created (aw backlog): plan-review mandates path:line citations but never says to re-locate by symbol, so line drift reads as a false claim

## What is missing

`plan-review` mandates `path:line` as THE evidence citation format in five places
(`.aw/system/workflows/plan-review/plan-review.md:107` "Verify material claims with `path:line`
evidence", `:173` the findings-table Evidence field, `:260` the decision-row Basis field, `:555` and
`:571` the final-report table), mirrored into `plan-review-long/01-discover-and-snapshot.md:67`,
`plan-review-long/02-review-and-revise.md:30`, `plan-review-long/report-template.md:22`,
`spec-review/spec-review.md:42`/`:134`/`:167`/`:309`/`:375`/`:392`, and
`verify-execution/verify-execution.md:15`/`:94`/`:111`/`:198`/`:211` plus
`verify-execution/intent-audit.md:8`/`:12`/`:26`/`:45`.

NOWHERE in any of them does it say to identify the evidence BY SYMBOL, or what to do when a cited
line number no longer points at the cited thing. `AGENTS.md:38` says only "real citations".
`aw ipd lint` does not inspect citations at all (no citation check exists in
`agent_workflows/ipd_lint.py`). So the format the workflows mandate is the one that decays fastest,
and the decay is unhandled.

## Why it matters: the drift is large, fast, and already recorded

Measured drifts recorded in this repo's own backlog history:

- `.aw/records/backlog/graduated/20260829-runverdict-03-rbftpl-...backlog.md:10`: "EVERY LINE NUMBER
  HAD DRIFTED ENORMOUSLY and was re-located BY SYMBOL at HEAD 8b4e1570: the v_data read cited at
  `oc_runipd.py:2171-2172` is now `:6421-6422` (~4250 lines)".
- `.aw/records/backlog/graduated/20260905-depblock-01-nueip1-...backlog.md:9`: "EVERY line number had
  drifted by 1300 to 3400 lines and was re-located by symbol".
- `.aw/records/backlog/graduated/20260901-nogitmsg-01-okm6e6-...backlog.md:10`: "a ~1190-line drift".
- `.aw/records/backlog/graduated/20260905-runviewdisc-01-1f9m2j-...backlog.md:9`: "re-located by
  symbol because this item's line numbers drifted ~158 lines".
- `.aw/records/backlog/graduated/20260907-actmodel-01-0k74my-...backlog.md:15`: "a 42-line drift".

The cause is structural, not sloppiness: this repo runs many concurrent plans against a small number
of very large files, so an author's citation can be stale before the review reads it.

## The concrete harm

A reviewer reading a stale `path:line` sees the cited line contain something else, and must choose
between two readings with no rule to guide it: the plan made a FALSE CLAIM (a real finding), or the
plan made a TRUE claim against an earlier revision (cosmetic). Reviewers have been re-deriving that
judgement per run, inconsistently, e.g.
an untracked local session transcript from 2026-08-24: "line
numbers drift throughout (2249 vs 2222, 4461 vs 4505) ... This is a systematic LOW finding." Nothing
in the workflow told it that; it decided.

The worse direction is a reviewer treating drift as a fabricated citation and issuing a finding
against a plan whose substance is correct, which costs an author a revision round for nothing.

## The mitigation already exists, but only in ad-hoc prompt text

Hand-written run prompts already carry the rule, proving it is the known-good practice and merely
uninstalled. From an untracked local session prompt of 2026-09-08 (item H):

    H. VERIFY YOUR CITATIONS BY RUNNING THEM. Line numbers in oc_runipd.py and agy_runipd.py moved
    ~70 and ~95 lines in a single day, and both files are being edited by live runs right now.
    Re-locate by symbol, never by remembered line number.

That text appears only in disposable session transcripts, never in a workflow, `AGENTS.md`, or the
`ipd-spec`.

## Proposed direction (not decided; a maintainer scope call)

1. AUTHORING rule: a citation naming a code location SHOULD carry the SYMBOL (function/class/constant)
   alongside the line, e.g. `oc_runipd.py:6421 (queue_sort_key)`, so it is re-locatable after drift.
   Candidate homes: the `ipd-spec` spec, and the "real citations" clause at `AGENTS.md:38` /
   `agent_workflows/engine.py:1184`.
2. REVIEW rule: `plan-review` Step 1 should state the disposition explicitly. A citation whose SYMBOL
   resolves but whose LINE has moved is a LOW/cosmetic finding at most (arguably none); a citation
   whose symbol does NOT resolve is a genuine evidence finding. This removes the per-run judgement
   call. Home: near `plan-review.md:107`, and the mirrors in `plan-review-long`, `spec-review`,
   `verify-execution`.
3. OPTIONAL and unscoped: a lint that checks a `path:line (symbol)` citation still resolves. Deliberately
   listed last, because it is a much larger change than the two prose rules and the prose rules capture
   most of the value.

## Out of scope

Changing the `path:line` format itself, or dropping line numbers. The line number is useful when
fresh; the gap is that nothing says how to survive it going stale.
