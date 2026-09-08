- Id: f1sw71
- Status: graduated
- Set: durablecapture
- Priority: low
- Work-Kind: feature
- Summary: attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist

## Workflow history
- 2026-09-08 graduated (aw set): FULLY LIVE, graduated to DECISION plan si24ia (not an implementation plan: this is an open question whose requester said 'definitely not sure', and building a requirement model would answer its five questions on the maintainer's behalf). All three gaps re-verified; two numbers corrected (specs.py is 1066 lines not 1006, hits at :1048/:1063; corpus is 28 specs with 6 approved, not 27/5). KEY NEW FINDING the item lacks: there is NO single parsable requirement convention. Measured across all 28 specs: six incompatible id forms, and THIRTEEN specs match none, stating requirements as bare prose MUST, including release-gating 25kzda. So a retrofit means inventing ids from prose for 13 specs, which reframes the item's own cost/benefit question. Also: three live specs carry no - Id: at all, so a <spec-id6>.<req-id> join key could not reference their requirements.
- 2026-09-05 created (aw backlog): attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist

GRADUATED 2026-09-08 TO A DECISION PLAN, NOT AN IMPLEMENTATION. Plan `si24ia`
(`.aw/records/plans/pending/20260908-specreq-01-si24ia-...ipd.md`, carrying `- From-Backlog: f1sw71`)
measures the corpus, costs three options including doing nothing, answers this item's five questions
with evidence, and RECOMMENDS. It deliberately builds nothing: this item is an open question whose
requester said "definitely not sure", and a plan that built a requirement model would answer these five
questions on the maintainer's behalf and impose authoring burden on every future spec from an agent's
guess.

FULLY LIVE, NOTHING OBSOLETE. No plan carries `- From-Backlog: f1sw71`, and SIX pending plans
(`rnkqrc`, `m867ox`, `y9s4vm`, `jxxec8`, `iuxtjy`, `st5klo`) each name this item and exclude it as out of
scope, two of them as numbered findings. So the gap is live, unclaimed, and independently recognized by
adjacent work.

ALL THREE GAPS RE-VERIFIED AT HEAD `fac69fbd`, with two stale numbers corrected. `specs.py` is now 1066
lines, not 1006, and its two incidental `requirement` hits moved from `:988,:1003` to `:1048,:1063`;
`validate_spec` (`:211-326`) still checks only status, gate, history, priority and work-kind. The corpus
is 28 specs, not 27, with 6 `approved` rather than 5 (12 non-terminal in total); the item's "9 in
ready/active" still holds. `SPEC_STATUSES` (`attention_contract.py:241-253`) is nine values with no
partial state, and `_SPEC_MAP` (`:262-272`) maps `approved`->ready and `implementing`->active as
described. `APPROVAL_FLOOR` (`:453-463`) still admits in its own words that `aw specs` enforces
"presence + format + resolvability, NOT semantic verification". Both named examples check out: `c4gd2h`
has been `implementing` since 2026-08-30 with ONE history line, carries `- Blocks-Release: next`, and
holds 23 `- R<n>.` bullets nothing parses; and `25kzda` 2.1's retry budget really is one requirement in
three states (`validate_retry_budget` IS called from `runner_shared.py`, while `plan_retry` and
`retry_budget_remaining` have zero production callers).

THE FINDING THIS ITEM DOES NOT HAVE, and it reframes the cost/benefit question the item asks. THERE IS
NO SINGLE PARSABLE REQUIREMENT CONVENTION. Measured across all 28 specs, one grep per form:
`- G<n> \`[Must]\`` in 7 specs, `- R<n>.` in 1 (23 ids), `- R<n> (MUST)` in 3, `- **R-<n>**` in 2,
`| I-<n> |` table rows in 1 (15 ids), and dotted `R<n>.<n>` sub-ids in 1. THIRTEEN of the 28 match NONE
and state requirements as bare prose `MUST`, INCLUDING `25kzda`, the release-gating run spec. Note also
that the item's example string "G5 [Must]" is not the literal form; it is `- G5 \`[Must]\`` (backticked).
So this is not "add a parser": 13 specs would need requirement ids INVENTED from prose, which is human
judgment about what a spec's discrete requirements even are. That is the strongest available input to
the item's own last question and it argues for a cheaper answer than the full mechanism.

ONE MORE PREREQUISITE THE ITEM DOES NOT MENTION: three live specs carry NO `- Id:` at all (the oldest
`approved` one and both `deferred` ones), so they are unreachable by id6 selector and a join key of the
form `<spec-id6>.<req-id>` could not reference their requirements. Recorded in the plan as its OQ-03.

`graduated` NOT `done`: the question is handed off, not answered. Whether this item then closes `done`
or stays open depends on the maintainer's response to `si24ia`'s recommendation.

ORIGINAL ITEM TEXT FOLLOWS, uncorrected.

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
