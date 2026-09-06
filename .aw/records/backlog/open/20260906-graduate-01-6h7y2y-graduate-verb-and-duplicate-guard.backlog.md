- Id: 6h7y2y
- Status: open
- Set: graduate
- Priority: medium
- Work-Kind: feature
- Summary: no way to turn a spec or backlog item into an IPD through the runner, and no check that the work was not already done: needs both the verb and a duplicate/already-implemented guard

## Workflow history
- 2026-09-06 created (aw backlog): no way to turn a spec or backlog item into an IPD through the runner, and no check that the work was not already done: needs both the verb and a duplicate/already-implemented guard

TWO HALVES, AND THE SECOND IS THE ONE THAT MATTERS. The maintainer's framing (2026-09-05): "We
need backlogs for turning backlogs and specs into IPDs/IPD sets - HOWEVER, we need a way to make sure
that the spec / backlog items have not already been addressed. We don't want multiple IPDs for the
same things, especially if already implemented."

=== HALF 1: THE GRADUATION PATH DOES NOT EXIST ===

Spec `25kzda` describes it as shipped behavior. Section 1.3 lists "Author an IPD from an approved
spec" and "Graduate an open backlog item into an IPD" as dispositions of `aw <host> run`, and
Section 2.1 registers `--action plan`, whose legality rules (`:139`, `:270`) say it is legal
"only for an `approved` spec or `open` backlog item".

It cannot work. Measured 2026-09-05:

    $ aw oc run start --action plan 25kzda
    runipd: '25kzda' is a backlog item (...), not an IPD plan.

`runner_shared.discover_plans` walks only the two plans trees, so NO selector reaches a spec or a
backlog item however it is spelled. `--action plan` parses and its entire legal domain is
unreachable. Spec `6m4kow` (`to-review`) already recorded this measurement independently.

So today graduation happens by an agent reading an item and hand-authoring a plan. That works (it is
how most of the plans tree was built) but it is unenforced: nothing checks the handoff happened, and
nothing prevents it happening twice.

=== HALF 2: THE DUPLICATE / ALREADY-IMPLEMENTED GUARD ===

There is NO such check today. Verified: `check_engine` has `check.from-backlog-dangling` and
`check.from-spec-dangling`, which validate that a plan's `From-Backlog:`/`From-Spec:` id6
RESOLVES to a real artifact. Neither asks the reverse question - whether that source ALREADY has
plans, or whether its requirements are already implemented.

THE RAW MATERIAL EXISTS, which makes this tractable: 71 plans carry a source link, and grouping them
gives, for example, `From-Spec: 25kzda` x9, `From-Backlog: kjzlgw` x8, `From-Spec: 7ckptx` x7.

THE HARD PART, and why this must not be a naive uniqueness rule: MULTIPLE PLANS PER SOURCE ARE
LEGITIMATE AND NORMAL. A spec is deliberately decomposed into an ordered Set of child IPDs, and spec
`25kzda`'s own graduation text says a run "may produce more than one IPD, and a spec when the work
needs one, because a single item's design does not always decompose into exactly one plan". So
`count > 1` is not evidence of duplication. The 9-plan `25kzda` cluster is correct, not a defect.

WHAT THE GUARD ACTUALLY NEEDS TO DISTINGUISH:
  * LEGITIMATE DECOMPOSITION: several children of ONE Set, distinct Orders, non-overlapping scope.
  * ACCIDENTAL DUPLICATION: two plans in DIFFERENT Sets covering the same requirement, or a second
    plan authored for a source whose plans already reached `executed`.
  * ALREADY IMPLEMENTED: the source's work is done but its own status was never advanced, so a fresh
    graduation would re-do landed work. This is the expensive failure the maintainer is guarding
    against.

MINIMUM USEFUL VERSION, if the full classifier is too much: a PRE-GRADUATION WARNING that reports
every existing plan carrying this source id6 with its status and Set, so whoever graduates sees
"25kzda already has 9 plans, 7 executed" before authoring a tenth. Advisory and read-only; it does
not need to decide, only to show. That alone would prevent the costly case.

BLOCKED ON A KNOWN GAP FOR THE 'ALREADY IMPLEMENTED' HALF: there is no per-requirement tracking, so
'is requirement G5 built?' cannot be answered mechanically. A spec carries ONE whole-artifact status,
no partial-implementation state, and `implemented` requires only a resolvable citation rather than
semantic verification (`attention_contract.py:369-376` says so plainly). That question is tracked
separately in backlog `f1sw71`; this item can ship its plan-level guard without waiting for it, and
should say honestly which of the three cases above it can and cannot detect.

SEQUENCING NOTE: build the guard BEFORE or WITH the verb, not after. A working `--action plan` with
no duplicate check is a machine for generating redundant plans faster than a human can.
