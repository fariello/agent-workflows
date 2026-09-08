- Id: 6h7y2y
- Status: graduated
- Set: graduate
- Priority: medium
- Work-Kind: feature
- Summary: no way to turn a spec or backlog item into an IPD through the runner, and no check that the work was not already done: needs both the verb and a duplicate/already-implemented guard

## Workflow history
- 2026-09-08 graduated (aw set): PARTIALLY graduated to the graduate Set: orchestrator y9s4vm, child 01 jxxec8 (the read-only advisory pre-graduation view, this item's own 'minimum useful version', stating its limits in its OUTPUT), child 02 iuxtjy (make a spec selector reachable for the plan action by CONSUMING the existing discover_specs, and call the view there). Guard is Order 01 per this item's sequencing note. See the PARTIAL OBSOLESCENCE section appended. HALF 2 graduated whole. HALF 1 NARROWED: two of its three premises are overtaken by shipped work, one of which landed the day BEFORE this item was filed. FIRST, --action plan no longer misroutes; it FAILS CLOSED with a named refusal that starts no run (ACTION_IMPLEMENTED is frozenset({'review'})), landed a3bb14bf on 2026-09-05 against this item's 2026-09-06 filing. SECOND, 'no selector reaches a spec however it is spelled' is FALSE for specs: runner_shared.discover_specs exists, adds no path literal, and finds 9 specs including 25kzda; executed plan 5slbpi E-05 shipped it. WHAT SURVIVES: discover_specs has ONE consumer (the review sweep) so a spec cannot be the SUBJECT of a plan action, and there is no discover_backlog at all. THIS ITEM IS ITS OWN BEST ARGUMENT FOR HALF 2: spec 6m4kow already has THREE executed plans, so the view it asks for would have prevented two of its own stale premises. Numbers updated: 125 source-linked plans (was 71) across 72 sources, 17 with more than one. If iuxtjy OQ-01 defers the backlog half, this item stays graduated rather than going done.
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

## PARTIAL OBSOLESCENCE OF HALF 1, measured 2026-09-08 at HEAD a2e0438a during graduation

TWO OF HALF 1's THREE PREMISES ARE OVERTAKEN BY SHIPPED WORK, and one of them shipped the day BEFORE
this item was filed. Half 2 (the guard) is unaffected and is graduated whole.

FIRST, `--action plan` NO LONGER MISROUTES; IT FAILS CLOSED. This item's reproduction shows
`aw oc run start --action plan 25kzda` yielding "'25kzda' is a backlog item (...), not an IPD plan."
That is no longer the failure mode. Measured:

    ACTION_CHOICES     = ('review', 'plan', 'execute')
    ACTION_IMPLEMENTED = frozenset({'review'})
    enforce_requested_action('plan', ...) -> DriverError:
      "--action plan is not implemented yet. Only --action review is available; plan's per-type
       legality table (spec 25kzda 2.6) needs the per-type dispatch this runner does not have.
       No run was started. To review instead, run: aw oc review <selector>"

That landed in `a3bb14bf` ("revsweep 76gsmv") on 2026-09-05, and this item was filed 2026-09-06
(`46424252`). So the operator-facing hazard the item leads with was already gone when it was written.
The refusal must NOT be re-implemented.

SECOND, "NO SELECTOR REACHES A SPEC OR A BACKLOG ITEM HOWEVER IT IS SPELLED" IS NOW FALSE FOR SPECS.
`runner_shared.discover_specs` exists, is documented as "the SPEC sibling of `discover_plans`", reads
identity through `check_engine._ITEM_ID_RE`, status through `selectors.read_front_matter_status`, and
enumerates through `check_engine._iter_spec_records` so it adds NO new path literal (guarded by an AST
test rejecting a new `"records/specs"` literal in that module). Measured, it finds 9 specs including
`25kzda` at `status='approved'`. Executed plan `5slbpi` E-05 shipped it: "Let needs-review discovery
reach the SPECS tree".

WHAT SURVIVES OF HALF 1, and it is what was graduated: `discover_specs` has exactly ONE consumer, the
review sweep (`runner_shared.py:1107`). It is not wired into selector expansion or the queue builder,
so a spec still cannot be the SUBJECT of a `plan` action. And there is no backlog equivalent at all:
no `discover_backlog` exists, so that half means BUILDING an enumeration rather than consuming one,
which is a materially larger change. Plan `iuxtjy` OQ-01 escalates whether it belongs there or in a
follow-on; if it is deferred, this item should be set `graduated` rather than `done`.

THIS ITEM IS ITS OWN BEST ARGUMENT FOR HALF 2, and the finding is recorded because it is the clearest
possible demonstration. Spec `6m4kow`, which this item cites as having independently recorded the same
measurement, ALREADY has THREE executed plans carrying `From-Spec: 6m4kow` (`eyh1fu`, `5slbpi`,
`wpomxa`). Had the pre-graduation view this item asks for existed, whoever filed it would have seen
those three and scoped Half 1 differently from the start, and would not have written two premises that
had already shipped. That is exactly the waste the guard prevents.

HALF 2's NUMBERS UPDATED, since the item's are five days stale: 125 plans carry a source link (the
item recorded 71) across 72 distinct sources, of which 17 have MORE THAN ONE plan. Largest clusters:
`From-Spec: 25kzda` x9 (8 executed, 1 not-executed), `From-Backlog: kjzlgw` x8 (all executed),
`From-Spec: 7ckptx` x7 (4 executed, 3 approved), `From-Spec: kw5y2s` x6 (all executed),
`From-Backlog: 1ap48y` x4 (3 executed, 1 superseded). The item's central design constraint holds: the
nine-plan `25kzda` cluster is CORRECT decomposition, so no `count > 1` rule may be built.

Also re-verified as still true: no reverse-direction, duplicate, or already-implemented check exists
(only the forward `check.from-backlog-dangling` and `check.from-spec-dangling`); and the
already-implemented case remains mechanically unanswerable for the reason this item gives, tracked by
backlog `f1sw71` (still open).

GRADUATED to the `graduate` Set: orchestrator `y9s4vm`, child 01 `jxxec8` (the read-only advisory
pre-graduation view, the item's "minimum useful version", which states its own limits in its OUTPUT),
child 02 `iuxtjy` (make a spec selector reachable for the `plan` action by CONSUMING `discover_specs`,
and call the view there so the guard is reached). The guard is Order 01 because this item's sequencing
note requires it: "A working `--action plan` with no duplicate check is a machine for generating
redundant plans faster than a human can." `iuxtjy` closes this item.
