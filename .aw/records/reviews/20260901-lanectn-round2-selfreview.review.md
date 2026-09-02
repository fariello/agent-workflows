# Review: Set `lanectn` round 2 (disclosed self-review)

- Set: lanectn
- Plan-Id: h0zljh, cqx5v7, nna8yz, lhmrhx, y5od1h, xdr83v, 604wra
- Reviewed-At: 2026-09-01
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED
- Reviewed-Head: 868106a4

## Disclosure, stated first because it bounds everything below

I AUTHORED ALL SEVEN PLANS. This is a SELF-REVIEW and is weaker evidence than an independent one, for the
obvious reason: the same blind spots that produced a defect tend to hide it. Round 1 was independent
(`codex/gpt-5`, 19 findings across the seven records) and its findings are recorded per-plan in the
sibling `.review.md` files, all now `FIXED`. This record covers ROUND 2 only.

The most useful thing in this record is not the findings list. It is this: FOUR OF THE FIVE ROUND-2
FINDINGS ARE DEFECTS I INTRODUCED WHILE FIXING ROUND 1. Every individual fix was locally correct and
globally incomplete. That pattern is the thing worth inheriting, and it is the argument for a second pass
after any large remediation, self-review or not.

## Scope ledger

ELIGIBLE (7): the Set's orchestrator and six children, explicitly named by the maintainer.

- `.aw/records/plans/pending/20260901-lanectn-00-h0zljh-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-01-cqx5v7-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-02-nna8yz-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-03-lhmrhx-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-04-y5od1h-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-05-xdr83v-...ipd.md`
- `.aw/records/plans/pending/20260901-lanectn-06-604wra-...ipd.md`

NOT REVIEWED: (none).

NOT IN SCOPE, recorded so its absence is deliberate rather than an oversight: the `wslayout` Set
(`rh5tt6` and five children, authored by `antigravity`) was never a candidate and is therefore an
incidental file under the workflow's rule 0.1. It has its own separate review record with a REJECT
verdict, and I have read neither those plans nor that review, so I assert nothing about them.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | HIGH | UNDER-SCOPE | G. Traceability / B. Security | Coverage computed programmatically over the spec and the six children: 36 of 38 requirements owned | The three requirements I had added to the spec that same morning (`R3.3a-1a`, `R3.3a-1b`, `R3.3a-2`, the built-in secret floor and its fail-closed rule) were owned by NO plan. I amended an approved spec and then did not assign the new obligations, so nothing in the Set would have built the floor. This is the same defect class as round 1's `y5od1h` PR-002, one layer up: a security requirement with no implementer instead of no normative basis. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | MOOT by supersession rather than by assignment, which is the honest description: the maintainer decided to withdraw the permit-and-copy branch entirely, so `R3.3a` was amended to withdraw `R3.3a-1/-1a/-1b/-2`, `R3.3b`, and `R3.4`. There is now no floor to own. Coverage re-verified after the withdrawal: 36 live requirements, 36 owned exactly once, zero unowned, zero duplicated. |
| SR-002 | HIGH | IN-SCOPE | C. Architecture / G. Plan executability | Every child's `Scope-Paths` named only `oc_runipd.py` and `agy_runipd.py` (plus `worktree_lease.py` for `y5od1h`), while five children instructed the executor to place logic in "host-neutral functions both drivers call" | I mandated shared code and gave it nowhere to live. The fence named only the two driver modules, and the same plans said not to touch anything outside the fence. So the instruction required an action the plan forbade. An executor following it literally would either halt or quietly breach the fence, which is precisely the behavior this scaffolding exists to prevent. Improvising a home inside one driver and importing it from the other is not a fix: it makes one host the de-facto shared library, the opposite of host-neutral. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added spec `R2.6` (the shared-code home MUST be DECLARED in the implementing plan's scope, stated as an obligation on the PLAN rather than on the code) with criterion `A5c` (single definition, established by AST or the import graph, and a rule defined in one driver and imported by the other explicitly FAILS). Named the module `agent_workflows/lane_containment.py`, added it FIRST in all six children's `Scope-Paths`, and wrote an explicit instruction into each host-neutral paragraph not to improvise a home. The plan that reaches it first creates it; later plans extend it. |
| SR-003 | MEDIUM | UNDER-SCOPE | G. Traceability | `cqx5v7` E-06 (the collection receipt added in response to round 1's `xdr83v` PR-001) cited no requirement id; `grep -i 'receipt\|collected' ` over the spec returned nothing outside the unrelated begin-receipt text | A plan obligation with no normative basis. This is the same PR-005 class that got the predecessor `tch3bo` REJECTED, reintroduced by me one round later while fixing a different finding. I invented a real and necessary requirement (retention cannot answer "was this collected?" from the input manifest) and then failed to write it into the spec, so the plan asserted an obligation nothing authorized. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added spec `R2.5` (collection MUST be RECORDED, not inferred; attempt-keyed, with per-submission source digest and destination result; absence means NOT collected; a FAILED collection recorded as failed rather than omitted) with criterion `A5b` covering all four states. `cqx5v7` E-06 now cites `R2.5` and `R2.6`, and `xdr83v` consumes the record for collection state while using the input manifest only for driver-written content. |
| SR-004 | MEDIUM | IN-SCOPE | E. Testing / G. Accuracy | The orchestrator's completion criteria and E-02 both enumerated "A1-A20 plus A7b, A7c, A8b, A8c, A12b", omitting `A7b-1`, `A7b-2`, `A7b-3` added the same morning | The whole-Set verification would have demonstrated a stale criteria list and reported success while three criteria went undemonstrated. A verification that enumerates its own scope from a stale list cannot catch what the list omits. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | The enumeration now names the surviving criteria and explicitly records which were WITHDRAWN with `R3.3a` (`A7b`, `A7b-1`, `A7b-2`, `A7b-3`, `A7c`) and which was AMENDED (`A6`, now testing refusal rather than a permitted repair), so an executor cannot demonstrate a withdrawn criterion or silently skip a live one. Completion criterion 8 was rewritten from "a secret-bearing path is refused with a derived vocabulary" to "a missing-input report is REFUSED and nothing is copied", with a note that adding a secret vocabulary now FAILS the criterion rather than exceeding it. |
| SR-005 | LOW | IN-SCOPE | G. Accuracy | The orchestrator's partition proof asserted 36 requirements while the amended spec declared 38 | A proof stating a count that no longer matched its source. Low severity because the partition itself was sound, but a stale count in a document whose entire purpose is to assert completeness undermines the one thing it exists to establish. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The proof now states 34 live requirements at the time of writing and, more importantly, describes WHAT it verifies rather than quoting a number: acyclicity AND metadata-versus-prose agreement. Coverage is re-verified programmatically rather than asserted. |

## What round 2 verified CLEAN, so the record is not only failures

Each of these was checked mechanically, not by reading:

- E/V bijection in all six children: every `E-*` has a `V-*` that names it. No orphans either direction.
- Every gate element present in all seven: the paste-actual-output honesty rule, the scope fence, the
  path-scoped-and-never-push rule, and the lifecycle move.
- No plan claims execution or a terminal status.
- No requirement claimed by two children (which would fork ownership).
- The dependency graph is acyclic AND its machine-readable `Item-Dependencies` matches every child's
  prose. This is the check round 1 caught me omitting (PR-001/PR-002 on the orchestrator, `y5od1h`, and
  `604wra`), and it is now the one I run first.

## The two structural lessons, recorded because they will recur

1. AN ACYCLIC GRAPH THAT DISAGREES WITH ITS OWN PROSE IS EXACTLY AS DANGEROUS AS A CYCLIC ONE, and it
   passes `aw ipd lint`. Round 1 caught my "PARTITION PROOF" asserting completeness when it had only
   checked acyclicity; two children's metadata omitted edges their prose required, so a scheduler reading
   metadata could have started work before the seams existed. Check BOTH properties, and treat the
   verification of a claim as part of the claim.
2. A REMEDIATION PASS NEEDS ITS OWN REVIEW. Four of five round-2 findings were introduced by round-1
   fixes: I amended a spec without assigning the new requirements (SR-001), mandated shared code without
   a declared home (SR-002), added an obligation without a requirement (SR-003), and left two
   enumerations stale (SR-004, SR-005). Each fix was locally correct. The failure was never re-checking
   the whole after changing the parts.

## Honest limits of this review

1. It is a SELF-REVIEW. An independent reviewer would likely find things I cannot see, and round 1
   demonstrably did.
2. It audited STRUCTURE and INTERNAL CONSISTENCY (traceability, coverage, bijection, the dependency
   graph, gate elements, criteria enumeration). It did NOT re-derive whether the spec's requirements are
   the right requirements; that judgment was made when the maintainer approved `7ckptx` and amended it
   twice.
3. It asserts nothing about the `wslayout` Set, which was out of scope and which I have not read.
4. `aw check plans` reports a large `check.scope-drift` count against several unrelated plans in this
   checkout. Measured during this review and recorded here so it is not mistaken for a finding against
   this Set: the delta from my work is ZERO (682 before, 682 after, same checkout with only my edits
   stashed). The cause is pre-existing and is the `dh0uno`-class attribution problem, since those plans
   hold live begin receipts whose frozen base is roughly 336 commits old, so every path changed by anyone
   since is attributed to them.

## Plans reviewed and not reviewed

REVIEWED:

- `.aw/records/plans/pending/20260901-lanectn-00-h0zljh-worker-lane-containment-adopt-spec-7ckptx.ipd.md`: REVIEWED. SR-001, SR-002, SR-004, SR-005 all FIXED. 3 E / 3 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-01-cqx5v7-lane-relative-prompt-and-closed-loop-submission-collection.ipd.md`: REVIEWED. SR-002, SR-003 FIXED. 6 E / 6 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-02-nna8yz-lane-input-materialization-with-a-sealed-manifest-and-clean.ipd.md`: REVIEWED. SR-002 FIXED. 5 E / 5 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-03-lhmrhx-per-host-permission-posture-and-driver-side-turn-bounds.ipd.md`: REVIEWED. SR-002 FIXED. 6 E / 6 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md`: REVIEWED. SR-001, SR-002 FIXED; also amended by the `R3.3a` withdrawal, which retired its E-03 entirely and narrowed E-04 and E-05. 6 E / 6 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-05-xdr83v-retention-preserve-a-lane-holding-unclassifiable-content.ipd.md`: REVIEWED. SR-002, SR-003 FIXED. 3 E / 3 V, lint conforming.
- `.aw/records/plans/pending/20260901-lanectn-06-604wra-shared-containment-predicates-and-their-fail-loud-discipline.ipd.md`: REVIEWED. SR-002 FIXED. 4 E / 4 V, lint conforming.

Verdict: REVIEWED. Open questions: 0 open across the Set.

Required next step: MAINTAINER APPROVAL. `reviewed` means the review occurred; it does not mean approved
or ready to execute, and only the human may approve. Note for that decision: this round was a
self-review, so an independent pass before execution would be reasonable given that four of its five
findings were self-inflicted.

NOT REVIEWED:

- (none)
