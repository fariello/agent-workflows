# Review: Classify a review history record by its structure, not by review words in its prose

- Subject-Id: xpta5g
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-derived at HEAD `0891a94d`. The target plan was committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0) BEFORE review and again at
`--phase review-finalize` after every revision; the single `IPD-Z602` density advisory raised at one
point was assessed semantically (its three "clauses" were one deliverable plus two rationale
sentences) and resolved by relabelling the rationale rather than by splitting a cohesive item.

THE DIAGNOSIS IS CORRECT AND I REPRODUCED ALL THREE DEFECTS EXACTLY, which matters because this plan
narrows the un-overridable half of the approval gate and a wrong premise would be expensive. Built
the three in-memory plans the Concern describes and ran both `newest_verdict` and
`approval_refusals`: `ycg597` returns polarity `None` with the tooled `reviewed (aw set): status set
to reviewed` line as its source and ZERO refusals, so a `REJECT - NEEDS REPLAN` review is genuinely
shadowed; `nwrb0j` returns `negative` and ONE refusal sourced from a descope line; `gv36a7` returns
`negative` and ONE refusal sourced from a record whose verdict token is outside `VERDICTS`. F-1's
reason for rejecting an actor-based discriminator is sound and F-2 re-measures exactly: over every
tracked plan, ZERO `negative` results come from the `negative_readiness_asserted` fallback, so
removing it costs no live refusal. I also re-implemented the proposed rule from the plan's own prose
and ran the nine-row classifier table: 0 mismatches, and the three rows that change are exactly the
intended True-to-False transitions. F-3's `positive->neutral` analysis re-measured precisely: 12 of 12
are `reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION ...` lines. The
author's work is careful and the rule is right.

THE DOMINANT FINDING IS PR-801, AND IT IS ABOUT WHAT THE PLAN DID NOT MEASURE. The plan describes the
classifier as feeding two functions ("which `history_has_review_record` and `newest_verdict` both
consume") and probed exactly those two plus `is_plan_review_approved`. There are four consumers, and
the two it missed matter because they move in the OPPOSITE direction from the one being fixed.
`is_plan_review_approved` consumes `history_has_review_record` as the PROVENANCE requirement for a
present `- Readiness:` field (rdattest `8v5pwa`: a field no review produced asserts a clearance that
never happened), and `plan_readiness.recheck_readiness` consumes `newest_verdict` twice, for its
condition-3 verdict and for the `cite_review_entry` citation it WRITES into a plan's history.
Recognizing fewer records makes `newest_verdict` strictly safer, since the worst case is `None` and
`None` refuses nothing. It makes `history_has_review_record` STRICTER, and a genuine review the
classifier no longer recognizes withdraws a real attestation. Measured over all 776 plans, the
proposed rule withdraws it from six (`hblwtx`, `2pyjga`, `ha55fi`, `75ov5j`, `k99n3m`, `y7xygb`), and
one of those is not a forgery at all: `hblwtx` records `- 2026-08-19 reviewed (opencode): self-review
- verified anchors (Item:34, 6 construction sites, ...)`, a real self-review whose message leads with
neither a verdict token nor `plan-review`/`spec-review`, so rule B correctly declines it. All six are
in `executed/`, `is_plan_review_approved` flips ZERO, and the `approval_refusals` verdict refusal
changes ZERO anywhere, so the change is safe today. But the plan asserted a two-consumer blast radius
and shipped a probe that could not see this, and "nothing live moves" is a conclusion a reviewer
should not have to derive.

PR-802 IS THE FINDING A RE-REVIEWER SHOULD CHECK SECOND, because it undercuts the plan's own safety
argument. E-02 says to keep `_HISTORY_RECORD_PARTS_RE` unchanged "(one parser, per its comment)", and
that comment reads "`tests/test_plan_readiness.py` asserts there is only ONE encoding of this
vocabulary, so do not add a third parser." That file was DELETED in `19313eed` ("test: trim test suite
from 9,136 to under 2,000 tests", 2548 lines), along with
`tests/test_plan_readiness_recheck.py` (917 lines). A grep of the entire test tree for that pattern or
for "ONE encoding" returns nothing. So does a grep for
`ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, which this module's
own `_CLEARED_NEGATIVE_READINESS_RE` note names as the test whose reddening caught the 2026-09-19
incident that cost 2h10m and $55.02 for zero integrated work. Two invariants that guard exactly this
module are gone, four surviving comments still cite them as live, and the only tests anywhere
referencing `is_review_history_entry` or `history_has_review_record` are the two
`test_spec_review_attestation.py` tables. The plan's conventions section notes the file is gone and
then draws no consequence from it. So this plan rewrites an unguarded predicate while citing its
missing guard as the reason a risky step is safe.

PR-803 WOULD HAVE STRANDED THE EXECUTOR AT THE LAST STEP. The gate says to "set backlog `ycg597`,
`nwrb0j` and `gv36a7` to `done` citing this plan." All three items are `graduated` and all three carry
`- Blocks-Release: next`, while the plan declares `- From-Backlog: ycg597` alone. Run against the
shipped predicate `check_engine.evaluate_blocking_close(..., 'done')`: `ycg597` returns
`legitimate=True` ("gate 'next' handed off to a From-Backlog plan or spec"), and `nwrb0j` and `gv36a7`
both return `legitimate=False` ("backlog item carries Blocks-Release 'next'; closing it `done` would
silently drop that release gate"). So two of three closes are refused, after every E-item is done and
every V-item is evidenced. The correct route is the SATISFIED one, citing the executed plan as in-tree
evidence, and NOT `--blocks-release -`, which de-gates a blocker rather than discharging it.

PR-804 IS A DRIFTED MEASUREMENT PLUS THE CONVENTION IT BROKE. F-3's counts no longer hold: I
re-measured 38 whole-tree flips rather than 37 (one additional `None->neutral`) and, more
importantly, ONE PENDING FLIP rather than zero. `je74a0` moves `None -> neutral` because its newest
record is the bare `- 2026-09-25 reviewed (aw set): status set to reviewed` line the fix stops
honoring, revealing the real `/plan-review ... REVIEWED - OPEN QUESTIONS` review beneath it. That is
the fix working, and it changes no refusal, but E-06's expected outcome read "0 flips in `pending/`"
as a bar, so a correct execution would have appeared to fail its own acceptance criterion. The same
finding covers the convention break: F-3 cites a machine-local absolute scratch path in a tracked
artifact. `aw sanitize --agent` reports clean only because that particular path carries no username.

PR-805 IS THE OTHER SIDE OF PR-801 AND I RECORD IT AS A BENEFIT, because it is evidence the change is
right rather than merely narrower. Of the nine plans carrying `- Readiness: no-go` (the
`recheck_readiness` population), two currently source condition 3 from a NON-review line: `je74a0`
from `reviewed (aw set): status set to reviewed`, and `drzbs9` from `reviewed (aw set): set
Item-Dependencies to none`. Both would write a citation reading "the review of <date> (no finding ids
stated in its record)". After the fix they cite the real reviews, with finding spans `OQ-03..F-3` and
`PR-501..OQ-05`. So the fix repairs an attestation the plan never claims, in a consumer it never
named.

PR-806 IS RIGHT-SIZING AND THE GATE. The count lint passed at seven items. The gate was two sentences
with `Cohesion rationale: not required`, and it is missing more than usual here: this plan changes the
un-overridable half of the approval gate, and a human approving it should be told that the narrowing
withdraws six attestations, that one of the six is a genuine review, and that the module has no
regression guard until E-03 and E-07 land. It had no scope fence over a module where the difference
between editing a function BODY and editing a shared regex is the whole safety argument, no stop
conditions, and an unconditional finalize instruction.

CONTRACT CHECKS. `aw check release-gates --agent` reports `findings:0` at this HEAD. All three source
items are `Work-Kind: bug` carrying `- Blocks-Release: next`, and the plan correctly inherits the
gate, satisfying the every-live-bug rule. `- From-Backlog: ycg597` resolves. No `.spec.md` names
`is_review_history_entry` or `newest_verdict`, so the plan's no-spec-amendment claim is correct
(re-verified). One finding this review INTRODUCED and then fixed: OQ-01 and the two new Deferred rows
owed durable carriers, which `evaluate_durable_carrier` reported at `error` severity; each now carries
a substantive `Carrier-Declined` and the predicate returns zero findings on this plan. I also recorded
the pre-existing suite failure (`test_blast_radius_zero_across_pending_plans`, stranded prerequisite
`72qlya` referenced by pending plan `je74a0`, reproducing at `0891a94d` and at `25eb9a08`) so V-09
cannot absorb it as this plan's damage.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression | Plan Scope says the classifier is one "which `history_has_review_record` and `newest_verdict` both consume"; `is_plan_review_approved` calls `history_has_review_record` as the provenance requirement for a present `- Readiness:` field; `plan_readiness.recheck_readiness` calls `newest_verdict` for condition 3 AND for `cite_review_entry`; measured over 776 plans: `history_has_review_record` withdraws for 6 plans (`hblwtx`, `2pyjga`, `ha55fi`, `75ov5j`, `k99n3m`, `y7xygb`), `is_plan_review_approved` flips 0, `approval_refusals` verdict refusal changes 0; `hblwtx`'s record is `- 2026-08-19 reviewed (opencode): self-review - verified anchors (Item:34, ...)` | THE BLAST RADIUS IS FOUR CONSUMERS AND THE PLAN MEASURED TWO, AND THE TWO IT MISSED MOVE IN THE OPPOSITE DIRECTION. Narrowing the classifier makes `newest_verdict` strictly safer, because its worst case is `None` and `None` refuses nothing. It makes `history_has_review_record` STRICTER, and that predicate is the provenance gate on a present `- Readiness:` field, so a GENUINE review the rule no longer recognizes withdraws a real attestation and would refuse unattended promotion. Six plans lose it and one of them is not a forgery: a real self-review whose message leads with neither a verdict token nor the workflow name. All six are terminal so nothing live moves, but the plan asserted a two-consumer radius, shipped a probe that could not see this, and left "nothing live moves" for a reviewer to derive. `recheck_readiness` is the fourth consumer and also unnamed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the rule is unchanged; the fix is measurement and disclosure) | FIXED | Added F-4 with all six withdrawals, the `hblwtx` record quoted, and the direction each consumer moves. Added a `## Goal` paragraph and a "WHICH DIRECTION EACH CONSUMER MOVES" paragraph in Proposed changes stating it once. Scope sentence corrected to FOUR consumers; a conventions bullet names all four and how each is reached. E-08 rewritten to measure four predicates, with V-08 requiring the withdrawals ENUMERATED per plan with each record QUOTED, and stating that a histogram does not satisfy the item. A Deferred row records the six with a substantive `Carrier-Declined`, and a second row records the REJECTED widening of rule B with the reason (fix the writer, not the reader). |
| PR-802 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `19313eed` deleted `tests/test_plan_readiness.py` (2548 lines) and `tests/test_plan_readiness_recheck.py` (917 lines); `_HISTORY_RECORD_PARTS_RE`'s comment cites the first as asserting "there is only ONE encoding of this vocabulary, so do not add a third parser"; the `_CLEARED_NEGATIVE_READINESS_RE` note cites `ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` as the test that caught the 2026-09-19 incident (2h10m, $55.02, zero integrated work); grep of the whole test tree for either returns NOTHING; four surviving comments across `plan_readiness` and `readiness_recheck` still cite the deleted files | THE SAFETY NET E-02 CITES DOES NOT EXIST, SO THIS PLAN REWRITES AN UNGUARDED PREDICATE. Two invariants died with those files: the ONE-PARSER rule that E-02 leans on when it says "keep `_HISTORY_RECORD_PARTS_RE` unchanged (one parser, per its comment)", and the LIVE-PENDING-CORPUS rule that this module's own incident note names as what turned a classifier regression red before it cost another run. Nothing in the tree now catches either a second parser or a classifier change that newly refuses a live plan. The plan's conventions section notices the file is gone and draws no consequence; citing a deleted test as the reason a risky step is safe is the most expensive form of stale citation, because it reads as verified. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (two focused tests over existing predicates) | FIXED | Added F-5 with both deleted files, both dead invariants, the incident cost, and the four stale citations. Added E-03 (one-parser guard, with a deliberate-failure proof required by V-03 because a scan test passes vacuously when it matches nothing) and E-07 (live-pending-corpus guard, asserting on the `approval_refusals` REFUSAL rather than on polarity, since review measured one correct polarity change in `pending/` and zero refusal changes, so a polarity assertion would fail on a correct change). E-02 now also corrects the four stale citations, with V-02 requiring `grep -rn "tests/test_plan_readiness" agent_workflows/` to return nothing. Added a "WHAT PROTECTS THIS CHANGE" paragraph and two Scope-check bullets. |
| PR-803 | MEDIUM | IN-SCOPE | G. Plan executability / A. Correctness | Gate: "set backlog `ycg597`, `nwrb0j` and `gv36a7` to `done` citing this plan"; all three are `graduated` with `- Blocks-Release: next`; plan declares `- From-Backlog: ycg597` only; measured `check_engine.evaluate_blocking_close(..., 'done')`: `ycg597` legitimate=True ("gate 'next' handed off to a From-Backlog plan or spec"), `nwrb0j` and `gv36a7` legitimate=False ("closing it `done` would silently drop that release gate") | THE GATE'S FINAL INSTRUCTION IS REFUSED BY A SHIPPED PREDICATE, AND IT FAILS AT THE MOST EXPENSIVE MOMENT. The close-legitimacy rule fails closed for a release-blocking item unless the gate is provably handed off, satisfied by cited evidence, or explicitly cleared. One `From-Backlog` field legitimizes exactly one item, so an executor who has finished every E-item and evidenced every V-item is then refused on two of three closes with no instruction for what to do about it. The likely improvisations are both wrong: passing `--blocks-release -` de-gates a real release blocker, and leaving the items open silently strands work the plan did complete. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-6 with the per-item predicate verdicts. Rewrote the gate's closing paragraph: close `ycg597` via the handoff, close `nwrb0j` and `gv36a7` with `aw backlog set done <path> --evidence <this executed plan>`, explicitly forbid `--blocks-release -` with the reason (de-gating is not discharging, and the work genuinely is done), and require the verdict be re-derived per item at execution time rather than trusting the three names. |
| PR-804 | MEDIUM | IN-SCOPE | A. Correctness (live-artifact criterion) / repo convention | F-3 records 37 whole-tree flips and "pending/ 0 verdict flips"; re-measured at review by reimplementing the rule from the plan's prose: 38 flips (`None->positive` 17, `positive->neutral` 12, `None->neutral` 9) and ONE pending flip, `je74a0` `None -> neutral`, sourced from `- 2026-09-25 reviewed (aw set): status set to reviewed`; E-06's expected outcome read "0 flips in `pending/`"; F-3 also cites a machine-local absolute scratch path | A COUNT MEASURED AT AUTHORING WAS WRITTEN AS AN ACCEPTANCE BAR, AND THE CORPUS HAS SINCE MOVED, so a CORRECT execution would appear to fail its own criterion. The new pending flip is the fix WORKING: `je74a0`'s newest record is exactly the bare setter line this plan stops honoring, so the real `/plan-review` review beneath it becomes readable. It changes no refusal. Under the plan's literal bar ("0 flips in `pending/`") an executor must either stop or quietly rewrite the criterion. Separately, citing a machine-local absolute path in a tracked artifact is the class of string the leak-sanitizer exists to keep out of shared output; it passes today only because this particular path carries no username. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 rewritten with the re-measured numbers, the pending flip explained as the fix working, an explicit statement that both counts are observations and never bars, and the absolute path replaced by a description. E-08's expected outcome converted to PROPERTIES (zero refusal changes, zero auto-approve flips, no flip to `negative`, withdrawals enumerated and terminal) with an instruction to re-derive at execution time, and it now requires the scratch dir be inside the workspace. A conventions bullet forbids the absolute-path citation. |
| PR-805 | LOW | IN-SCOPE | F. Honest documentation (an unclaimed benefit) | Of the 9 plans carrying `- Readiness: no-go`, `je74a0` sources condition 3 from `reviewed (aw set): status set to reviewed` and `drzbs9` from `reviewed (aw set): set Item-Dependencies to none`; both produce `cite_review_entry` -> "the review of <date> (no finding ids stated in its record)"; after the fix they cite the real reviews with spans `OQ-03..F-3` and `PR-501..OQ-05` | THE FIX REPAIRS A LIVE ATTESTATION THE PLAN NEVER MENTIONS, in the consumer PR-801 shows it never named. `recheck_readiness` writes a citation INTO a plan's history, so a citation sourced from a bare setter line is a durable inaccuracy in a tracked artifact, not just a transient misread. Two of nine live `no-go` plans have one today. Recording this is not decoration: it is the clearest positive evidence that the classifier change is correct rather than merely narrower, and it belongs in the plan so a later reader weighing the six withdrawals against the benefits can see both sides. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-9 with both plans, both current citations and both corrected ones, and cross-referenced it from the "WHICH DIRECTION EACH CONSUMER MOVES" paragraph. Also added F-7 re-verifying that the `readiness re-check` label stays a non-review under both rules and WHY (`cite_review_entry` deliberately derives a citation carrying no verdict token), and F-8 recording that the nine-row classifier table is internally consistent with the stated rule. |
| PR-806 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Gate as authored: two sentences plus `Cohesion rationale: not required`; compare pending plan `t0jyb2`, whose gate carries a what-a-human-is-approving paragraph, a scope fence framed as a DECLARATION, an honesty rule, genuine stop conditions and conditional runner/executor finalize ownership | THE GATE WAS MISSING MOST OF ITS REQUIRED ELEMENTS ON A PLAN THAT CHANGES THE UN-OVERRIDABLE HALF OF THE APPROVAL GATE. It said nothing about what a human is approving, and the three things that most need saying are precisely the ones a reader cannot see from the plan's framing: the narrowing withdraws six attestations (one for a genuine review), the module has no regression guard until E-03 and E-07 land, and one pending plan's polarity changes. It had no scope fence, which matters unusually much here because the difference between editing a function BODY and editing the shared `_HISTORY_RECORD_PARTS_RE` is the entire safety argument. No stop conditions, and an unconditional `aw ipd finalize` instruction that is wrong under a runner that owns the transition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: a what-a-human-is-approving paragraph ranking the four consequences; a per-symbol scope fence framed as a DECLARATION cross-referencing the new EXPLICITLY NOT IN SCOPE list; the hard-MUST honesty rule naming V-01/V-02 (the tests must be shown failing against unmodified code, and V-02's intermediate state only exists if the items were done in order), V-03 (a scan test passes vacuously) and V-08 (a histogram hides the six withdrawals); three genuine stop conditions; and conditional runner/executor finalize ownership. Substantive cohesion rationale added explaining the 7-to-9 item growth. The `IPD-Z602` density advisory raised on the new E-03 was assessed semantically and resolved by relabelling its rationale clauses, since the item has one deliverable. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The narrowing withdraws the review attestation from six plans, one for a genuine self-review. Accept it, widen rule B to admit such a preamble, or send the plan back? | Accept it, disclose it with all six enumerated, and fix the SHAPE at the writer via E-06's workflow rule. | (a) Widen rule B to admit `self-review`, `round N` and similar preambles - rejected: every widening re-opens the shadowing route the plan exists to close, and the message HEAD is precisely the position F-1 establishes as the only reliable signal. (b) Ask the maintainer - rejected: the repository answers it, since all six are in `executed/` where the provenance requirement gates nothing (a terminal plan is never promoted), so the measured live cost is zero and the residual is a cosmetic inaccuracy on settled artifacts. (c) Special-case `hblwtx` - rejected: a per-record exception in a classifier is unreviewable and would not generalize. | Measured 6 withdrawals, all terminal; `is_plan_review_approved` flips 0; `approval_refusals` verdict refusal changes 0; `is_plan_review_approved`'s docstring on what the provenance requirement is for | yes |
| D-2 | E-07's corpus guard: assert on `newest_verdict` polarity or on the `approval_refusals` refusal? | On the REFUSAL. | (a) On polarity - rejected on measurement: the correct change moves exactly one pending polarity (`je74a0`, `None` -> `neutral`), so a polarity assertion would fail on a correct implementation and train the next author to weaken it. (b) On both - rejected: the polarity half is the one that legitimately moves, so including it makes the test flap on every future classifier refinement while adding no safety the refusal assertion lacks. | Measured 1 pending polarity change and 0 pending refusal changes; 309 of 776 plans are decided by the `- Readiness:` field before prose is read | yes |
| D-3 | Two of the three backlog closes are refused. Prescribe `--evidence`, or clear the gates? | Prescribe the SATISFIED route, citing the executed plan, and explicitly forbid `--blocks-release -`. | (a) Clear the gates with `--blocks-release -` - rejected: that de-gates a real release blocker rather than discharging it, and the work genuinely will be done, so the evidence route is the truthful one. (b) Add `nwrb0j` and `gv36a7` to `- From-Backlog:` - rejected: the field is singular in every shipped usage and `evaluate_blocking_close` matches one id6, so a multi-value field would be an untested schema change made under time pressure at the end of an execution. (c) Leave the two items open - rejected: it silently strands completed work outside the attention view. | `check_engine.evaluate_blocking_close` verdicts measured per item; the three documented fixes (HANDOFF / SATISFIED / DE-GATED) in AGENTS.md's close-legitimacy rule | yes |
| D-4 | The plan cites a deleted test as its anti-fork guarantee. Restore the guard here, or file it? | Restore it here, as E-03, with a deliberate-failure proof. | (a) File it separately - rejected: E-02's own justification for touching a shared regex's neighbourhood is that guard, so shipping E-02 without it means the plan's stated safety rests on nothing for however long the follow-on takes. (b) Just correct the comment to say the guard is gone - rejected: it removes a false citation and leaves the invariant unenforced, and a second parser is the documented route by which this exact defect class returns. | `19313eed` deletion of both files; grep of the whole test tree returning nothing for the cited assertions; `_HISTORY_RECORD_PARTS_RE`'s own "do not add a third parser" comment | yes |
| D-5 | F-3's numbers no longer hold and one pending flip now exists. Update the numbers, or make the criterion a property? | Both: re-measure F-3 AND convert E-08's expected outcome to properties with an explicit re-derivation instruction. | (a) Only update the numbers - rejected: the corpus moved once between authoring and review and will move again, so a fresh count is a fresh bar that will be stale at execution; the plan-review rubric's live-artifact convention requires the property. (b) Only state the property and drop the numbers - rejected: the numbers are useful CONTEXT for judging whether a re-derived measurement is in the expected shape, and deleting them would discard the author's real work. | Re-measured 38 flips versus the recorded 37, and 1 pending flip versus the recorded 0; plan-review Rubric G on live-artifact success criteria | yes |
