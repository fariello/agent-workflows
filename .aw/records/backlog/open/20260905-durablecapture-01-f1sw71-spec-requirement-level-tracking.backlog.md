- Id: f1sw71
- Status: open
- Set: durablecapture
- Priority: low
- Work-Kind: feature
- Summary: attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist

## Workflow history
- 2026-09-05 created (aw backlog): attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist

OPEN QUESTION, NOT A DECIDED FIX. Filed at the maintainer's request (2026-09-05) so the question
survives; the maintainer explicitly did not commit to it: "I'm not sure if having a spec is
sufficient, since we're not really going back to them for 'hey, what's in the specs that we still
need to address'. Maybe that should be a thing? Definitely not sure."

WHAT IS TRUE TODAY.

Specs ARE visible at the whole-artifact level. `aw attention` maps spec `approved` -> `ready` and
`implementing` -> `active` (`attention_contract.py:201-211`), so a spec awaiting implementation
does show up. Measured 2026-09-05: 27 specs total - 15 `implemented`, 5 `approved`, 2 `draft`, 2
`deferred`, 1 `to-review`, 1 `superseded`, 1 `implementing`; 9 of them in ready/active.

WHAT IS MISSING - three distinct gaps.

  1. NO PER-REQUIREMENT MODEL. Specs write `[Must]`-tagged goals in prose (e.g. "G5 [Must]"), and
     NOTHING PARSES THEM. `agent_workflows/specs.py` (1006 lines) has no requirement model:
     grepping for requirement/R[0-9]/partial yields 2 incidental hits (`:988`, `:1003`), both about
     evidence-artifact resolution. There is no `G5 -> plan` join key, i.e. no requirement-level
     counterpart to `From-Backlog`/`From-Spec`.

  2. NO PARTIAL-IMPLEMENTATION STATE. A spec is `approved` or `implementing` or `implemented`.
     There is no way to say "6 of 9 requirements are built". So an `approved` spec can sit for weeks
     with half its requirements unbuilt and nothing asks WHICH half.

  3. `implemented` IS NOT SEMANTICALLY VERIFIED, which the code states honestly at
     `attention_contract.py:369-376`: `aw specs` enforces "presence + format + resolvability, NOT
     semantic verification that the work truly happened". And `check.from-spec-dangling`
     (`check_engine.py:123-125`) validates only that a `From-Spec` id6 resolves TO A SPEC - never
     that the spec's requirements are covered.

EVIDENCE THAT THIS IS A REAL RISK, not hypothetical. Long-sitting specs by last workflow-history
date:
    2026-08-08  deferred     20260725-0957-01-external-delivery-and-skills      (gate -> TODO.md)
    2026-08-08  deferred     20260726-1239-01-clean-delta-and-tracking-modes    (gate -> TODO.md)
    2026-08-18  approved     20260808-1958-01-prompt-purity-lint
    2026-08-27  approved     20260824-2000-01-research-lifecycle-reliability
    2026-08-29  implementing 20260829-c4gd2h-01-runner-lifecycle-graceful-quit

`c4gd2h` is the sharpest case: it has been `implementing` for weeks and its four stop levels are
partially wired, but there is no machine-readable way to ask which of its requirements shipped. That
uncertainty was hit directly while filing the stop-level discoverability item (`1m3nul`), which had
to caution the implementer to verify which levels exist before documenting them. A requirement-level
view would have answered that question outright.

Also note spec `25kzda` section 2.1 (the retry budget) is a live example of a requirement whose
helpers shipped, whose flag is pending, and whose consumption does not exist at all - three different
implementation states inside ONE spec section. See `trjfyy`.

WHAT WOULD NEED DECIDING FIRST, before any implementation:
  * Do requirements get stable ids in the spec (`R1`..`Rn` / `G1`..`Gn`), and are they parsed?
  * Does a plan declare WHICH requirements it implements, and is that validated as resolvable?
  * Does `aw attention` gain a "requirements outstanding" view, or is this only an `aw check` rule?
  * Is `implemented` then computed from requirement coverage rather than asserted?
  * Cost/benefit: this adds authoring burden to every spec. Is the ~27-spec corpus large enough to
    justify it, and would it be retrofitted or apply only going forward?

DEPENDENCY NOTE. This is deliberately NOT a blocker for `jys5dp` (the durable-capture enforcement
rule). That item's conclusion is that a spec is not a SUFFICIENT carrier for a known defect precisely
because of the gaps above; it routes obligations to backlog items and plans instead, which works
today. Resolve this question on its own timeline.
