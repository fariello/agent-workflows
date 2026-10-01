- Id: hc6n7r
- Status: open
- Set: denypush
- Priority: low
- Work-Kind: followup
- Summary: Decide whether a carried non-blocking open question should gate its plan dispatch, and if so wire the Carrier field to an enforced dependency edge (29 open carried questions across 23 pending plans, zero edge-backed)

## Workflow history
- 2026-10-01 created (aw backlog): Decide whether a carried non-blocking open question should gate its plan dispatch, and if so wire the Carrier field to an enforced dependency edge (29 open carried questions across 23 pending plans, zero edge-backed)

THE MEASURED GAP. A plan records a maintainer decision it cannot answer by writing `- Carrier: <id6>` on the open question, naming the backlog item that durably holds the decision. That field is DOCUMENTATION ONLY: nothing makes the plan wait for the decision. Measured 2026-10-01 over every pending and reusable plan by parsing each with `ipd_lint.parse` and comparing each open-and-carried question against the plan own `Item-Dependencies` text: 29 open questions across 23 plans carry a Carrier, and ZERO are backed by a `state:backlog:done:<carrier>` edge. The population is LIVE and grows as plans are authored, so re-derive the number rather than trusting this one.

WHY IT MATTERS. An approved plan with a carried, unanswered decision executes normally. The pre-execution checkpoint (`ipd_lint.check_checkpoint`) refuses only an open question carrying `Blocking: yes`, and a carried decision is typically and correctly `Blocking: no` per the 2026-09-10 maintainer ruling. So the plan ships, reaches `executed/`, and `aw attention` classes it done, after which D156 forbids rewriting what it records. The decision window closes having never opened. Measured instance: the `denypush` Set, whose four plans were all approved while three maintainer decisions sat open on carrier `wcbpqf`; plan `d5ntkj` gates two of them by hand with a `state:backlog:done:wcbpqf` edge, which is the per-instance remedy this item generalizes.

THE DECISION THIS ITEM HOLDS, and it is the maintainer because it sits on the boundary the 2026-09-10 ruling drew: should a carried non-blocking question gate dispatch AT ALL? That ruling says a non-blocking question does not make a plan NO-GO. A general carrier-to-edge rule would instead make such plans `dependency-blocked`, which is a different mechanism reaching a similar outcome. Whether that honors the ruling intent (the question is still not NO-GO, it merely waits) or evades it (the plan still does not run) is a judgement about what the ruling was FOR; its recorded rationale concerns plans HELD for reasons their authors judged non-stopping and is silent on waiting.

IF THE ANSWER IS YES, the candidate mechanism and its severity tier are already scouted. A new `check_engine.RULE_REGISTRY` rule reporting a carried open question with no matching edge. Register it `warning`, following `check.review-decision-unescalated`, NOT `error` like `check.ipd-uncarried-obligation`: 29 pending plans would be findings on day one and an error tier would turn `aw check` red for authors who did nothing wrong. Note `check.ipd-uncarried-obligation` is the OPPOSITE case (an obligation with no carrier at all), so it cannot be widened to cover this. A stronger variant would refuse at `aw ipd set approved`, which is a bigger behavioral change deserving its own review.

IF THE ANSWER IS NO, record that in `.aw/records/plans/README.md` beside the Carrier documentation, so the next author learns that Carrier is deliberately documentation and that gating is a per-plan hand-declared edge. That is a real outcome, not a non-answer: it stops this being re-derived.
