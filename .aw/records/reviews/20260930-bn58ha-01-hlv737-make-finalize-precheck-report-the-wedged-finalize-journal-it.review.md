# Review findings: plan hlv737

- Subject-Id: hlv737
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (HIGH, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (MEDIUM, fixed), PR-405 (MEDIUM, fixed), PR-406 (LOW, fixed), PR-407 (LOW, fixed)

## Round 1

Reviewed at HEAD `6080b098` in an isolated review lane. The plan file was committed and byte-identical to
the lane input (`diff` reports no difference), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review;
`--phase review-finalize --agent` reports `conforming` after revision. The plan is `- Kind: child`, so the
`IPD-S407` orchestrator row check does not apply.

THE PLAN'S CENTRAL CLAIM IS TRUE AND I RE-REPRODUCED IT RATHER THAN READING IT. On a scratch git fixture
built from the repository's own `tests/support.ready_plan_text` shape, after `begin`, in-scope committed
work, and `_rollback_precommit` forced to `(False, "simulated rollback failure")` under
`fault_injection="after_move"`, the journal phase is `unknown-outcome` and the two surfaces disagree
exactly as F-1 states: `finalize_precheck` returns `(0, 'precheck passed (receipt valid, pre-transition
conforming; scope delta computed).', findings=())` while `finalize(apply=False)` and `finalize(apply=True)`
both return exit 2 with `finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt);
resolve manually and clear <path>`. F-4 (a `prepared` journal refuses nowhere), F-5 (a stale `complete`
journal refuses nowhere), F-6 (`committed-incomplete` disagrees in the OPPOSITE direction: precheck exit 1
`pre-transition gate did NOT conform`, `finalize` exit 0 `finalized abc123 -> executed`) and F-11 (that
`finalize(apply=False)` performs the resume, clears the journal and CONSUMES the receipt) all reproduced as
written. F-2, F-3, F-9 and F-10 verified by reading the cited symbols. This is a well-evidenced plan whose
diagnosis is right, whose fix direction is right, and whose most important judgement, excluding
`PHASE_COMMITTED_INCOMPLETE` from the refusing set because F-11 shows the `finalize` side of that case is
itself defective, is the correct call and is well argued.

WHAT REVIEW FOUND WERE TWO GAPS OF MEASUREMENT, both closed by prototyping E-02 rather than by reasoning
about it. Neither changes the production fix: E-02 as specified, at the site it specifies, is correct and I
would ship it. What was wrong was the plan's account of WHAT THE FIX DOES BESIDES REFUSING, and in a plan
whose whole subject is that two surfaces must agree, an incomplete account of the fix's reach is the defect
that matters.

FIRST, AND THE ONE THAT WOULD HAVE MADE A REQUIRED EVIDENCE ITEM UNSATISFIABLE. E-02 sites the new gate
BEFORE the begin-receipt read, which is correct and deliberate, but the consequence was never measured: the
gate PREEMPTS both receipt refusals whenever a journal is also wedged. Measured in both configurations. An
already-finalized plan (reached by a real clean `finalize`, so `plan_already_finalized`'s own predicate
fires) carrying a hand-wedged `unknown-outcome` journal returns at HEAD `(1, 'abc123 is ALREADY FINALIZED:
...', findings=('receipt-consumed-already-finalized',))` and under the prototype `(2, 'finalize journal for
abc123 is in unknown-outcome ...', findings=('finalize-journal-unknown-outcome',))`. A never-issued receipt
with the same journal goes from `(1, 'no begin receipt for abc123 ...',
findings=('receipt-never-issued', ...))` to the same exit 2. V-03 as authored demanded pasting the
no-receipt, already-finalized and stale-receipt findings tuples "showing the new id ABSENT from each",
which is satisfiable only when each fixture carries NO journal; an executor meeting V-03 literally on a
wedged fixture would have found the demand impossible and had to either weaken it or move the gate. THE
PREEMPTION IS THE RIGHT BEHAVIOR and that is why the fix is unchanged: `finalize(apply=False)` was measured
returning exit 2 with the journal message for BOTH those same states, so a precheck reporting the receipt
class instead would preserve the very disagreement this plan exists to remove. The remedy is therefore to
MEASURE and PIN it, not to relocate the gate: F-12 records both transcripts, E-06 pins all four cases
(each receipt refusal unchanged without a journal, each preempted with one, with `finalize`'s matching
code beside the wedged pair), V-06 demands that evidence, and V-03 now states the journal-free precondition
and why it is required. OQ-03 records the ordering decision with its measured basis so a later reader
cannot reorder the two gates believing it a free choice.

SECOND, F-7's CALLER INVENTORY WAS SHORT BY THE ONE CALLER THIS FIX ACTUALLY HELPS. F-7 calls
`runner_shared.compute_scope_reconciliation` "the ONE in-tree caller"; there are two. `grep` finds two
`ipd_lifecycle.finalize_precheck(` call sites in `runner_shared.py`, and the second,
`record_item_spec_edits`, calls the precheck directly in its empty-pair arm for the explicit reason that
`({}, {})` cannot distinguish "clean delta" from "precheck refused". Measured on a wedged plan: at HEAD the
per-item record is `{'state': 'reconciled', ...}`, so a run durably asserts in its own state that it
verified the scope delta of a plan whose finalize cannot proceed; with E-02 prototyped it is
`{'state': 'refused', ...}`. That is precisely what that arm's docstring says it is for ("printing a
positive all-clear for an item whose scope was never actually checked would reintroduce it"), so no
`runner_shared` edit is needed and the file correctly stays out of `- Scope-Paths:`. But it is a change to
what a RUN RECORD says, which a reader of F-7 alone would not expect, and it materially strengthens the
plan's own priority argument: F-8 said the exposure was to a hypothetical future preview caller, and in
fact one ships today and is already recording the wrong thing. Recorded as F-13, folded into the Goal as
the concrete beneficiary, noted in the scope check as a deliberate non-declaration, and covered by adding
the three `spec_edits`-owning test files to the required-tests list so the no-edit expectation is proved
rather than assumed.

THE SUITE IS GREEN AT THIS LANE'S HEAD, which contradicts an instruction E-05 gave. E-05 said "the
repository has at least one known pre-existing failure, so 'the suite is green' is not the expected result
and must not be asserted". Measured, bare, before any edit: `3344 passed, 2 skipped, 3 warnings in 61.84s`,
207 deselected, exit 0. That instruction is worse than a stale number, because it tells an executor to
EXPECT a failure and would license waving a genuine regression through as the inherited one. Corrected to
require re-derivation with the measured green state recorded as history rather than as the bar.

TWO SMALLER EVIDENCE CORRECTIONS. E-04's control set named `PHASE_PREPARED` as "a PRE-COMMIT phase" and
asserted three controls, but `_PRE_COMMIT_PHASES` has THREE members and all three were measured
non-refusing (`prepared`, `mutating`, `ready-to-commit`, each precheck 0 and `finalize(apply=False)` 0), so
a control naming one literal would silently stop covering a phase added to that frozenset. E-04 now
iterates the shipped constant. And the spec-sync section asserted `llbr2b` "remains accurate"; it does as a
matter of contract, but its Section 3.3 condition list will be incomplete after this change and its
bare `path:line` anchors for `finalize_precheck` (`:1885`, `:1919-1963`) have already drifted some 770
lines from where the symbol `ipd_lifecycle.finalize_precheck` actually sits. Neither is this plan's to
fix and both are now recorded for the next `llbr2b` revision rather than left for a reader to trip over.

NO SPEC AMENDMENT IS OWED and I verified the claim rather than accepting it. `finalize_precheck` appears in
exactly two specs. `25kzda`'s hit is its adjudication exception's "WHAT IT DOES NOT RELAX" paragraph, which
this plan cannot weaken in the direction it guards, because it adds a refusal and removes none.
`llbr2b`'s hits are its Section 3.3 table and its C-4 INVARIANT classification, and the condition added
here is likewise an invariant covered by Section 4.2's exclusion sentence as already written.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | HIGH | IN-SCOPE | A. Correctness / E. Testing (an unmeasured behavior change making a required evidence item unsatisfiable) | Prototype of E-02 at its stated site, measured against two fixtures. Already-finalized plus wedged journal: HEAD `(1, 'abc123 is ALREADY FINALIZED: ... lifecycle commit 4d1a50567d7e ...', ('receipt-consumed-already-finalized',))` -> prototype `(2, 'finalize journal for abc123 is in unknown-outcome ...', ('finalize-journal-unknown-outcome',))`. Never-issued receipt plus wedged journal: HEAD `(1, 'no begin receipt for abc123 ...', ('receipt-never-issued', 'missing begin receipt at <path>'))` -> prototype the same exit 2. `finalize(apply=False)` on BOTH states: exit 2 with the journal message | **Siting the gate before the receipt read PREEMPTS both receipt refusals when a journal is also wedged, and the plan neither measured nor mentioned it.** The behavior is CORRECT (it is what makes the precheck agree with `finalize`, which was measured returning exit 2 for both those states), so no production change is owed. What breaks is V-03, which demands the no-receipt and already-finalized findings tuples be pasted "showing the new id ABSENT from each": on a wedged fixture that is now false, so an executor meeting V-03 literally would have to either weaken the demand or move the gate down, and moving it down would re-open the disagreement the plan exists to close | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-12 records both transcripts in both configurations plus the `finalize` column that justifies the ordering. E-02 must now record the precedence consequence IN THE GATE'S COMMENT and name it intended, so a later reader does not "restore" the receipt refusal. New E-06 pins all four cases (each receipt refusal unchanged with NO journal, each preempted WITH one) and is required to build the already-finalized fixture through a real clean `finalize` so `plan_already_finalized` is genuinely exercised. New V-06 demands that evidence including `finalize`'s matching exit code. V-03 now states the journal-free precondition and why asserting without it would be false. New OQ-03 records the ordering decision, resolved from the measurement, with `Carrier-Declined`. `Highest E allocated` raised to 06 |
| PR-402 | HIGH | IN-SCOPE | Evidence accuracy (an incomplete caller inventory understating the fix's reach) | `grep -n "finalize_precheck(" agent_workflows/runner_shared.py` returns TWO call sites, `:26123` and `:30138`. The second is in `record_item_spec_edits`, whose docstring states it asks the precheck directly because `({}, {})` is ambiguous. Measured on a wedged plan: HEAD record `{'state': 'reconciled', 'declared': [], 'modified_not_declared': [], 'declared_not_modified': []}`; with E-02 prototyped `{'state': 'refused', ...}` | **F-7 calls `compute_scope_reconciliation` "the ONE in-tree caller" and there are TWO**, the missed one being the only caller whose OBSERVABLE OUTPUT this plan changes. It needs no edit (its `rc != 0` branch already means exactly this), so the production fix and the `- Scope-Paths:` set are both right. But a run at HEAD durably records `state='reconciled'` for a wedged item, meaning a permanent per-item record asserts a scope delta was verified for a plan whose finalize cannot proceed, and after this change it records `refused`. That is a change to what a run record SAYS, invisible to a reader of F-7, and it also corrects F-8's priority framing from "the exposure is to a future preview caller" to "one ships today and already records the wrong thing" | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New F-13 records the second caller, both measured record states, and why no edit is owed. F-7 reworded to "the FIRST of TWO" with its re-measurement under the prototype added. F-8 corrected to say no shipped path reports the wrong VERDICT while naming F-13's already-wrong record. The Goal section gains the concrete beneficiary, replacing a purely prospective justification. The scope check gains a "not over-scope despite changing what a run RECORDS" paragraph explaining why `runner_shared.py` stays undeclared. Required tests now include `tests/test_runner_shared.py`, `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`, which own the `spec_edits` assertions, so the no-edit expectation is proved |
| PR-403 | MEDIUM | IN-SCOPE | G. Plan executability (an instruction that licenses waving through a regression) | BARE `python3 -m pytest` at unmodified lane HEAD `6080b098`: `3344 passed, 2 skipped, 3 warnings in 61.84s (0:01:01)`, 207 deselected, exit 0. Green | **E-05 instructs the executor that "the repository has at least one known pre-existing failure, so 'the suite is green' is not the expected result and must not be asserted", and the suite IS green.** This is worse than a stale count. A stale count risks misreading growth as regression; an instruction to EXPECT a failure invites an executor meeting a real regression to classify it as the inherited one and proceed, which is exactly the outcome the before/after comparison exists to prevent | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 rewritten: the expectation of a pre-existing failure is removed, the measured green state is recorded as dated history rather than as the bar, re-derivation at execution is required, and any after-run failure is to be treated as this plan's until the before-run shows the same node id. V-05 restated to match, and the required-tests bullet updated |
| PR-404 | MEDIUM | IN-SCOPE | D. Anti-regression (a control that can silently stop covering a phase) | `LC._PRE_COMMIT_PHASES` is `frozenset((PHASE_PREPARED, PHASE_MUTATING, PHASE_READY_TO_COMMIT))`. Measured all three with a hand-written journal: each gives `finalize_precheck` exit 0 and `finalize(apply=False)` exit 0 | **E-04's control set names `PHASE_PREPARED` as "a PRE-COMMIT phase" and asserts three controls total, so two of the three pre-commit phases are uncovered and a phase added to the frozenset would escape the control entirely.** The control's whole purpose is to stop E-02 becoming a blanket "any journal refuses", and a control keyed on one literal member of a set cannot do that for the set | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now iterates `LC._PRE_COMMIT_PHASES` rather than naming a member, with all three measured values recorded, and its expected outcome restated as five assertions (three pre-commit phases, `complete`, no journal). F-4 retitled from `PHASE_PREPARED` to "the three pre-commit phases" with the review re-measurement. V-04 now requires the iteration line quoted, so a literal creeping back is visible |
| PR-405 | MEDIUM | IN-SCOPE | Evidence accuracy (an unqualified spec-accuracy claim) | `llbr2b` Section 3.3's "Conditions checked" cell enumerates the receipt, the accepted widening, `base_head`, the pre-transition lint and the reconciliation, and cites bare offsets `ipd_lifecycle.py:1885` and `:1919-1963`. The symbols `ipd_lifecycle.finalize_precheck` and its `receipt_is_current` stale arm both sit some 770 lines below those offsets in this lane | **The spec-sync section asserts `llbr2b` "remains accurate" without qualification, and two things about it are already or will be inaccurate.** The condition list becomes incomplete the moment this plan lands (it will not mention the journal), and its bare `path:line` anchors have already drifted by roughly 770 lines. Neither makes the CONTRACT wrong, so no amendment is owed and the plan's conclusion stands; but an unqualified "remains accurate" leaves the next `llbr2b` reviser to rediscover both | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten. `25kzda`'s guarantee quoted and the "adds a refusal, removes none" argument stated against it explicitly. `llbr2b` split into the contract conclusion (unchanged, C-4 invariant, Section 4.2 covers it as written) and two recorded editorial facts for its next revision: the condition cell will be incomplete but asserts no exhaustiveness, and its anchors have drifted with the current symbol location named |
| PR-406 | LOW | IN-SCOPE | G. Plan executability (a stale scope declaration) | Plan `- Scope:` as authored: "a control test proving the three NON-refusing phases are unchanged" and "`runner_shared.compute_scope_reconciliation`, whose existing `exit_code != 0` branch absorbs the new refusal" | **The `- Scope:` line encodes both corrected facts in their uncorrected form**, naming three control phases where there are five assertions across four phases, and one `runner_shared` caller where there are two. Left alone it would contradict the findings table inside the same document, which is the drift the workflow's sweep rule exists to catch | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope:` updated: four non-refusing phases, the new precedence test named in the IN list, and both `runner_shared` callers named in the OUT list with both branch conditions. Proposed-changes list renumbered to six entries including E-06 |
| PR-407 | LOW | IN-SCOPE | F. KISS / self-documentation (a Goal stated as hypothetical when a real case exists) | Goal as authored: "a driver or operator that previews with `finalize_precheck` ... is never told 'precheck passed'". F-13's measurement: a shipped caller records `state='reconciled'` for a wedged plan today | **The Goal justifies the fix entirely by a hypothetical trusting caller while a real one already records the wrong thing.** A reader deciding whether this bug deserves a release gate would read the weaker of the two available arguments | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Goal gains a paragraph naming `record_item_spec_edits` as the concrete beneficiary with both measured record states, so the release-gate justification rests on a measurement rather than on a trust argument |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-401: the gate's site preempts both receipt refusals when a journal is also wedged. Move the gate below the receipt read to preserve them, or keep the site and pin the preemption? | KEEP the site; pin both directions in E-06 and record the decision as OQ-03 | (a) Move the gate AFTER the receipt read so an already-finalized or receipt-less plan reports its receipt class; (b) keep the site and say nothing, as the plan did; (c) refuse only when a receipt EXISTS, making the journal gate subordinate | Decided by measurement, not preference. `finalize(apply=False)` on both wedged states returns exit 2 with the JOURNAL message, because `_early_recovery_result` runs before the precheck is ever called (`ipd_lifecycle.finalize`: `early = _early_recovery_result(...)` precedes `finalize_precheck(...)`). So options (a) and (c) would have the precheck report exit 1 where `finalize` reports exit 2, relocating the disagreement rather than removing it, which defeats the plan's stated purpose. A safety asymmetry points the same way: `PHASE_UNKNOWN_OUTCOME`'s own comment defines it "ambiguous/corrupt evidence; fail closed, never success", while already-finalized is a benign terminal observation, so surfacing the fail-closed class is the conservative choice when only one can be reported. Option (b) is what PR-401 exists to correct: it left V-03 demanding something measurement shows is false | yes |
| D-2 | PR-402: `record_item_spec_edits` changes its recorded state for a wedged item. Does that need a `runner_shared.py` edit or a declared scope path? | NEITHER; verify only, and name it in the plan | (a) Declare `agent_workflows/runner_shared.py` in `- Scope-Paths:` to make the effect visible; (b) leave F-7's "ONE caller" claim and note the second in prose only | Read the code before deciding: the `rc != 0` arm already sets `SPEC_RECONCILE_REFUSED` and its docstring states it exists because an empty pair cannot distinguish clean from refused, so the new refusal flows through an unmodified branch that already means exactly this. Option (a) is wrong mechanically as well as conceptually: finalize's reconciliation demands a `--scope-ack` for a declared-but-unmodified path, so declaring a file the plan does not touch would manufacture a reconciliation obligation for nothing. Option (b) fails because the change is to a DURABLE run record, and a plan that changes what a run records without saying so is the kind of surprise the scope fence exists to prevent. Covered instead by running the three test files that own the `spec_edits` assertions, which proves the no-edit expectation | yes |
| D-3 | PR-404: should the control iterate `_PRE_COMMIT_PHASES` or name the phases as literals? | ITERATE the shipped constant | (a) Name all three literals, which is more readable in the test source; (b) leave the single `PHASE_PREPARED` literal, as authored | Option (b) is the finding. Option (a) is the tempting fix and is still wrong for THIS test's purpose: the control exists to stop E-02 widening into "any journal refuses", and the set of phases that must not refuse is defined by the production constant, so a test that hardcodes today's membership stops being a control for the set the day the set changes. The repository already prefers this shape for exactly this reason (`ROLLUP_SHARED_GATES` is named explicitly so a test can assert against it rather than re-deriving it). Readability cost is one loop | yes |
| D-4 | PR-403: the suite is green but E-05 says to expect a pre-existing failure. Update the plan to record green, or just drop the sentence? | RECORD the measured green state as dated history AND require re-derivation; drop the expectation | (a) Delete the sentence and say nothing about the baseline's state; (b) write `3344 passed` in as the comparison target | Option (b) rots exactly as the plan's own live-artifact convention warns, since every merged lane adds tests and this plan executes after further merges. Option (a) is safe but throws away a useful fact: knowing the baseline was green on a stated date tells an executor that a failure is probably theirs, which is the whole decision the before/after comparison supports. Recording the number as HISTORY while making the BAR "re-derive it" keeps the signal without the rot, and matches how the repository handles other live-population counts | yes |
| D-5 | PR-405: `llbr2b` is `to-review` and its condition list will be incomplete after this plan. Amend it, or record the gap? | RECORD the gap; declare no spec path | (a) Amend `llbr2b` Section 3.3 in this plan, adding the journal row and fixing the drifted anchors; (b) assert "remains accurate" unqualified, as authored | The managed `AGENTS.md` block does permit and prefer a plan to carry a spec amendment it needs, and I weighed (a) seriously. It loses on two counts. The condition cell asserts no exhaustiveness, so the spec is not made FALSE and no contract drifts, which is the trigger the obligation attaches to; and editing a `to-review` spec's table would put a spec revision inside a narrow bug fix, widening the diff into a document whose own review has not completed. Option (b) is the finding: an unqualified accuracy claim leaves the next reviser to rediscover both the missing row and a roughly 770-line anchor drift. Recording them costs a paragraph and hands the next revision its worklist | yes |
