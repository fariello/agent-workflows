# Review findings: plan q32qeg

- Subject-Id: q32qeg
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `b321b602` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize --agent`
conforms after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: the plan was
committed and unmodified, byte-identical to its `.aw/state/lane-inputs/rev-5/` copy. No production
code was modified by this review; every measurement was taken in an out-of-tree heredoc importing
the shipped modules, with `git status --short` empty throughout.

**EVERY AUTHORED FINDING ABOUT THE EXISTING CODE REPRODUCED.** F-01: `_CLASSIFICATION_EXITS` is
exactly `{'all_clear': 0, 'item_failure': 1, 'invalid_invocation': 2, 'needs_input': 3,
'run_wide': 4, 'interrupted': 130}`, `_CLASSIFICATION_PRIORITY` ranks `AGGREGATE_NEEDS_INPUT` ahead
of `AGGREGATE_ITEM_FAILURE`, and `aggregate_run_exit` raises its candidate from
`any(result.item.needs_input for result in item_results)`. F-02: `rg -n "aggregate_run_exit"` over
both drivers returns nothing, and over `tests/` returns nothing. F-03: exactly one
`deliberate_stop_exit_code` call per host, each the final `return` of `run_queue`, with the other
integer returns (`2`, `143`/`130`) living in `main`'s handlers. F-04: `NEEDS_INPUT_KEY` is
`"needs_input"`, byte-equal to both siblings, with the three equalities already asserted. F-05: the
third write site is real and fires on success (`elif queue_entry_type(item) == "spec" and
disposition == "reviewed": item[NEEDS_INPUT_KEY] = True`), and such an entry has
`item_reached_success` True and exits 0 today. F-09: all six `ABORT_CLASSES` strings grep to zero
outside `run_evidence.py`. F-10: the malformed entry exits 1 under both `stopped` arms, measured.
F-13: neither driver emits an `aw.agent/v1` record, so the 0/1/2 restriction does not bind.

**REVIEW DID NOT STOP AT RE-READING. It IMPLEMENTED E-01 exactly as authored and re-ran the plan's
own F-08 sweep, and the plan's central safety claim DID NOT REPRODUCE.** That is PR-801, the only
consequential finding in this round and the reason this review was worth running.

**PR-801 (HIGH): E-01's SIX CLAUSES MUST BE ORDERED, AND THE AUTHORED READING BREAKS THE
DELIBERATE-STOP CONCESSION THE PLAN PROMISES TO PRESERVE.** As written, clause 2 says a `queued`
entry under `stopped=True` "becomes `AggregatedItem(..., benign_skip=True)`" and clause 5 says a
human-gated entry "becomes `AggregatedItem(..., needs_input=True)`", with nothing stating which wins
when both match. Implementing them as independent field assignments, review's sweep over the same
672-combination cross product reported `differing combos: 300` and `all differences are 1->3: False`,
against the plan's stated `294` and True. The 6 extra rows are exactly
`('queued', <each of 6 actions>, needs_input=True, stopped=True, 0, 3)`. The mechanism is in the
aggregator: `aggregate_run_exit` raises the `needs_input` candidate WITHOUT consulting that item's
contribution, and `_CLASSIFICATION_PRIORITY` ranks `needs_input` above `all_clear`, so one excused
`queued` item carrying the flag outranks the exit 0 the whole concession exists to produce. Measured
directly on the plan's own E-05(d) queue plus a gate flag: `old = 0`, authored-E-01 `new = 3`.
Suppressing `needs_input` on clause 2's arm restores the plan's numbers exactly
(`294`, both properties True). This is not a style preference: spec `c4gd2h` A1/A4 REQUIRE exit 0 for
a graceful wind-down, spec `25kzda` 5.6's 130 row was narrowed in writing to record that, and
`deliberate_stop_exit_code`'s docstring cites A1/A4 for the same contract. The plan's own Scope says
it does not re-decide when a stop occurred; returning 3 there would re-decide what a stop MEANS.
Critically, NO SHIPPED TEST CATCHES THIS, and none of F-07's eight scenarios combines a stop with a
gated remainder, so the authored plan had no tripwire for its own worst case.

**PR-802 (MEDIUM): F-06's SWEEP MEASURED ONE `stopped` ARM, WHICH IS THE EVIDENCE GAP THAT LET
PR-801 THROUGH.** F-06 concludes that every combination exiting 0 today while carrying the flag has
`item_reached_success` True, citing 15 pairs. Re-measured, that is exactly right under
`stopped=False` (15 pairs, all True) and false under `stopped=True`, where 20 pairs exit 0 and the 5
`queued` ones are all `item_reached_success=False`. The conclusion about the conjunct's safety
survives; the general claim does not, and the 5 counterexamples are precisely the class PR-801 is
about. Both halves are now recorded so a later reader cannot re-derive the narrow claim and
re-introduce the defect.

**PR-803 (MEDIUM): THE GATED-`queued` ENTRY IS UNREACHABLE AT QUEUE BUILD AND REACHABLE AFTERWARDS,
so PR-801's case is live rather than theoretical and clause 2's suppression must not be simplified
away as dead code.** At build the two are mutually exclusive by construction (measured: zero
status/action pairs yield `queued` plus the flag, because `initial_queue_status` freezes a `reviewed`
plan as `reviewed` for exactly the non-`review` actions `item_needs_approval` reports True for). But
the flag is frozen once and never cleared, while `item["status"] = "queued"` is written at six later
sites, and the `--full-auto` bridge sets it on an item whose entry may already carry the flag.

**PR-806 (MEDIUM): THE PLAN NAMES THE WRONG SHIPPED TEST AS ITS REGRESSION GUARD.** Both the gate
prose and V-05(e) point the executor at `test_approval_gate_visibility_and_plan_control`. That test
asserts `item.get("needs_input")` and never reads `run_queue`'s return value, so it stays GREEN under
the naive single-conjunct predicate. Review wired the naive mapping in memory and ran the file's
rc-asserting tests: the two that go RED are
`TestSpecReviewDispatchE07::test_case2_advanced_with_conforming_record_and_directory_move` and
`TestSpecReviewApprovalAndScopeE08::test_crash_fix_full_auto_spec_review`, both on
`AssertionError: 3 != 0`, on both hosts. The plan's underlying claim is correct and its citation is
not, which matters because an executor who runs only the named test concludes the naive predicate is
safe.

**PR-805 (LOW): THE BASELINE HAD ALREADY DRIFTED BY 60 TESTS.** F-12 records `3102 passed, 2 skipped`
at `925458df` and required tests item 4 asked for "a count increased over `3102 passed`". Review's
clean-tree bare run at `b321b602` reads `3162 passed, 2 skipped, 3 warnings in 48.59s`. An executor
asserting the authored total would fail for a reason unrelated to their change, which is the
live-artifact convention the rubric names.

**PR-804 (LOW): ONE CITATION IN THE EVIDENCE CHAIN IS A STALE DOCSTRING CLAIM, AND THE PLAN'S TEST
ACCOUNTING IS OFF BY ONE.** `exit_code_statuses`'s docstring asserts that
`tests/test_runner_stop_levels12.py` "pins that both call it"; that file does not exist and the name
greps to exactly one place, the docstring itself. Nothing in the plan's reasoning depends on it (the
one-site-per-host claim is verified two other ways), so this is recorded rather than acted on, and
explicitly left out of scope. Separately, OQ-03 says `exit_code_statuses` is asserted across hosts by
`test_runner_shared.py` "and four further test files call the pair directly": `rg -ln` returns 5
files and `test_runner_shared.py` is not among them, so it is 5 direct callers plus the identity test.

**WHAT REVIEW CHECKED AND FOUND SOUND.** The `run_evidence` fence holds: `_CLASSIFICATION_EXITS` is
the sole integer site and the plan writes no literal. The lazy-import precedent E-02 cites is real
(`evaluate_unverifiable_admission` does `from agent_workflows import run_evidence` in its body). The
cross-host identity mechanism E-06 extends is real and locatable by symbol
(`CrossHostSuccessBarEqualityTests.test_cross_host_success_bar_constants_and_tokens`'s `for name in
(...)` tuple). Both new symbol names are free (zero hits repository-wide). The mutation-proof method
the plan mandates was verified performable rather than assumed (F-20): `mock.patch.object` on a
`runner_shared` attribute IS seen by a sibling function calling it by global name. Every
`Carrier-Declined` row is sound; the exit-4 gap and the two-table conflict are both recorded in
spec `25kzda` 5.6's own rows as pre-existing and unowned, and this plan neither widens nor narrows
either. Right-sizing is appropriate: 6 E-items, each one deliverable, with the two test items
separated by subject rather than bundled.

Every finding is FIXED by in-place revision. None was deferred, so no escalation to a
`- Blocking: yes` question is owed and none was written. OQ-01 and OQ-02 survive review unchanged and
are UPHELD on re-measured evidence. OQ-03 is upheld with its count corrected. OQ-04 is NEW, raised
and resolved by review, recording the exit-0 answer PR-801 requires and why the repository rather
than reviewer taste decides it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | IN-SCOPE | A. Correctness and data integrity / D. Anti-regression | `run_evidence.aggregate_run_exit`'s `if any(result.item.needs_input for result in item_results)` branch (raises the candidate without reading the item's contribution); `run_evidence._CLASSIFICATION_PRIORITY` ranking `AGGREGATE_NEEDS_INPUT` above `AGGREGATE_ALL_CLEAR`; `runner_stop.deliberate_stop_exit_code` docstring citing spec `c4gd2h` A1/A4; spec `25kzda` 5.6's 130 row ("a DELIBERATE stop exits **0**, not 130"); review's two-variant sweep printing `variant A: total=672 diffs=300 pairs={(1, 3): 294, (0, 3): 6}` vs `variant B: total=672 diffs=294 pairs={(1, 3): 294}`; direct probe on E-05(d)'s queue plus a gate flag printing `old = 0 literal-E01 new = 3` | E-01's SIX CLAUSES WERE UNORDERED AND THE AUTHORED READING BREAKS THE DELIBERATE-STOP CONCESSION THE PLAN PROMISES TO PRESERVE. Clause 2 excuses a `queued` item under a stop; clause 5 sets `needs_input`; nothing said which wins. Implemented as independent assignments, one gated-but-excused item turns a correct operator-requested wind-down from spec-mandated exit 0 into exit 3, and the plan's own F-08 sweep does not reproduce (300 differing, 6 of them `(0, 3)`). No shipped test catches it and none of F-07's eight scenarios covers it, so the authored plan had no tripwire for its own worst case. | C:Low; U:Low; S:Low; F:Low; Overall:Low (one keyword argument in one new function, plus the test that pins it) | FIXED | E-01 now states the clauses are ORDERED and are to be written as one `if`/`elif` chain; clause 2 explicitly suppresses `needs_input` even when the entry's flag is True and explains the aggregator mechanism; clause 1 likewise sets it False; clause 5 is marked subordinate; clause 3 notes the gate DOES apply on the not-stopped arm. Added F-14 with both sweep variants. Added E-05 case (d2), the gated-stop exit-0 test, as the second load-bearing case. Added V-01(e), a BY-VALUE clause-order proof, and V-05(d-ii), a second mutation proof. Added OQ-04 recording the exit-0 answer and its spec basis. Expected outcomes, Proposed changes, Scope check, gate prose and required tests all swept. |
| PR-802 | MEDIUM | IN-SCOPE | A. Correctness (evidence sufficiency) | review probe printing `stopped=False: 15 pairs exit 0; all reached_success=True; counterexamples=[]` and `stopped=True: 20 pairs exit 0; all reached_success=False; counterexamples=[('queued','execute'),('queued','review'),('queued','plan'),('queued','skip'),('queued','orchestrate')]` | F-06's SAFETY SWEEP COVERED ONE `stopped` ARM AND THE OTHER HAS 5 COUNTEREXAMPLES. The finding states as general that every combination exiting 0 today with the flag has `item_reached_success` True; that holds for `stopped=False` and fails for `stopped=True`. The conclusion about the conjunct's safety survives, but the general claim is what made PR-801's case look impossible, so leaving it unqualified invites the defect's reintroduction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 narrowed in place with both arms stated and a pointer to the new F-15, which carries the per-arm measurement and explains that the 5 `queued` cases are covered by clause 2's ORDERING rather than by the conjunct. |
| PR-803 | MEDIUM | UNDER-SCOPE | C. Architecture and operability | `initial_queue_status`/`item_needs_approval` cross-probe printing zero reachable pairs at queue build; `rg -n '\["status"\] = "queued"' agent_workflows/*.py` listing six `runner_shared` sites plus the two host copies; the `--full-auto` branch setting `item["action"]="execute"` and `item["status"]="queued"` immediately above the spec gate write | THE REACHABILITY OF PR-801's CASE WAS UNRECORDED, IN BOTH DIRECTIONS. It is unreachable at queue build (the two conditions are mutually exclusive by construction) and reachable afterwards (the flag is frozen once and never cleared, while `queued` is re-written at six later sites and persisted across a resume). Without this recorded, an executor who probes only the queue builder concludes clause 2's suppression is dead code and simplifies it away, restoring the defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-16 with the build-time non-reachability measurement, the six re-queue sites, and the `--full-auto` path named as the clearest one, plus an explicit instruction not to treat the suppression as dead code. OQ-04's resolution repeats the reachability point where an executor will read it. |
| PR-804 | LOW | IN-SCOPE | A. Correctness (evidence accuracy) | `ls tests/test_runner_stop_levels12.py` -> No such file; `rg -Fn "test_runner_stop_levels12" .` returning only the `runner_shared.py` docstring line; `rg -ln "deliberate_stop_exit_code" tests/` returning exactly 5 files with `test_runner_shared.py` absent | TWO CITATIONS IN THE EVIDENCE CHAIN DO NOT RESOLVE. `exit_code_statuses`'s docstring claims a test file that does not exist pins both hosts calling the predicate (the defect is the docstring's; the surrounding claim is independently true). And OQ-03's "four further test files" undercounts: there are 5 direct callers plus the identity test. Neither changes a decision, and both are worth recording so an executor who goes looking does not conclude the plan is wrong, and so the dangling reference is not inherited silently again. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-19 with both measurements. Added a Step-0 conventions bullet recording the stale docstring, stating that nothing in the plan depends on the missing file, and declaring the docstring fix explicitly OUT of scope so it is not swept into the commit. OQ-03's count corrected in place to 5 plus the identity test. Scope check's under-scope list extended to six items naming the left-alone docstring. |
| PR-805 | LOW | IN-SCOPE | G. Plan executability (live-artifact convention) | review's clean-tree bare run `3162 passed, 2 skipped, 3 warnings in 48.59s` at HEAD `b321b602`, against F-12's `3102 passed, 2 skipped` at `925458df` | THE SUITE TOTAL WAS STATED AS A BAR AND HAD ALREADY DRIFTED BY 60 TESTS. Required tests item 4 asked for "a count increased over `3102 passed`", which an executor would fail for reasons unrelated to this change. A count over a live, moving population belongs in prose as context and must be re-derived at execution time. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The baseline paragraph now carries BOTH measurements, labels both as context, states the 60-test drift as the reason, and requires the executor's own before-baseline. Required tests item 4 and V-06(e) rewritten to demand a delta against the executor's own figure. Added F-18. The Step-0 conventions bullet carries both numbers. |
| PR-806 | MEDIUM | IN-SCOPE | E. Testing and verification | in-memory naive wiring via `mock.patch.object` on `runner_shared.exit_code_statuses` (spy) and `runner_stop.deliberate_stop_exit_code` (naive aggregate), yielding `AssertionError: 3 != 0` at `tests/test_spec_review_dispatch.py:381` and `:581`, each on `host='oc'` and `host='agy'`; `test_approval_gate_visibility_and_plan_control` GREEN under the same mutation; the class boundaries at `:235` and `:526` | THE PLAN NAMES THE WRONG SHIPPED TEST AS THE GUARD AGAINST ITS OWN WORST CASE. The gate prose and V-05(e) cite `test_approval_gate_visibility_and_plan_control`, which asserts only the flag and never `run_queue`'s return code, so it stays GREEN under the naive predicate. An executor who runs the named test and sees green concludes the naive predicate is safe, which is exactly the silent failure the plan's gate paragraph exists to prevent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-17 with the two tests that actually go RED, their assertion sites, and the explicit note that the named test does not. V-05(e) now requires the full file passing and names those two, forbidding substitution of the wrong one as false evidence. Required tests item 3 rewritten the same way. The gate's silent-failure paragraph rewritten to carry TWO failure modes, with the corrected test names on the first and E-05(d2)/E-06 on the second. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | When a deliberate stop excuses a `queued` item that CARRIES the `needs_input` flag, should the run exit 0 (stop concession wins) or 3 (gate wins)? | EXIT 0. Clause 2 is ordered ahead of clause 5 and suppresses `needs_input` on the excused arm. | (a) Exit 3, letting the gate win - rejected: it breaks an approved spec. Spec `c4gd2h` A1/A4 require exit 0 for a graceful wind-down, spec `25kzda` 5.6's 130 row was narrowed in writing to record exactly that, and `deliberate_stop_exit_code`'s docstring cites A1/A4; the plan's own Scope disclaims re-deciding the stop contract. (b) Leave the clauses unordered and let the implementer choose - rejected: that is the authored state and it is what produced the defect, measured. (c) Clear the flag on the entry when re-queueing - rejected: it mutates durable run state, which spec `c4gd2h` R22 forbids and which this plan explicitly promises not to do. | `aggregate_run_exit`'s `if any(result.item.needs_input ...)` branch reading the field regardless of contribution; `_CLASSIFICATION_PRIORITY` ranking `needs_input` above `all_clear`; spec `c4gd2h` A1/A4 via `deliberate_stop_exit_code`'s docstring; spec `25kzda` 5.6's 130 row; the two-variant 672-combination sweep (`300`/6-bad vs `294`/all-good). | yes |
| D-2 | E-06's sweep asserts three numbers (672, 294, and non-emptiness). Should the test hardcode them? | NO for the counts, YES for the properties. Derive the total from `len(runner_shutdown.KNOWN_ITEM_STATUSES) * len(actions) * 2 * 2`, report the differing count, and assert only the PROPERTIES (non-empty; all `needs_input=True`; all exactly `(1, 3)`). | (a) Hardcode 672 and 294 - rejected: both are cross products over a mutable frozenset, so adding a status breaks the test for a reason unrelated to this contract; that is the same staleness class as PR-805. (b) Assert nothing numeric and only "some differences exist" - rejected: the `(1, 3)`-exhaustive property is the ONLY tripwire for PR-801, and weakening it would let that defect ship silently. | `runner_shutdown.KNOWN_ITEM_STATUSES` is a `frozenset` of 28 members read at runtime; the plan-review rubric's live-artifact convention; review's own measurement that the 294 figure changes to 300 under a wrong clause order, i.e. the count is diagnostic but the property is the contract. | yes |
| D-3 | PR-804 found a false claim inside `exit_code_statuses`'s docstring (a test file that does not exist). Should this plan fix it? | NO. Record it in the plan's Step-0 conventions and in F-19, and declare it explicitly out of scope. | (a) Fix the docstring in the same commit - rejected: `runner_shared.py` is in `- Scope-Paths:` so it would pass the scope gate, but it is an unrelated correction riding a behavioral change, and the plan's own fence exists to keep this change reviewable. (b) Say nothing - rejected: the plan leans on the surrounding claim, so an executor who goes looking finds a missing file and cannot tell whether the plan is wrong. (c) File it as new backlog - not done by review, which must not create artifacts beyond the plan and this record; recorded here instead so a maintainer can file it. | The plan-review workflow forbids modifying code and limits review to planning documents; the plan's declared scope fence; `rg -Fn "test_runner_stop_levels12"` returning only the docstring line, establishing the claim is self-referential and load-bearing nowhere. | yes |
| D-4 | PR-801 is HIGH. Does it make this plan NO-GO, or is escalation to a `- Blocking: yes` question owed? | NEITHER. It was FIXED by in-place revision, so no unfixed HIGH remains, no escalation is owed, and the readiness is `go-pending-approval`. | (a) NO-GO on the HIGH - rejected: the workflow is explicit that severity is for reporting and the Fix Bar alone decides fixing; this fix is Low Remediation Risk on every axis (one keyword argument in a function that does not yet exist, plus a test). (b) Escalate as a blocking open question - rejected: escalation is owed only for a finding left OPEN or DEFERRED at or above the gate threshold, and this one is FIXED. (c) REPLAN - rejected: the plan's approach is sound and its diagnosis correct; one clause needed an ordering rule, which is a bounded edit. | The `plan-review` Fix Bar and readiness vocabulary; `aw ipd lint --phase review-finalize --agent` conforming after revision (exit 0, findings 0); `review_findings_gate` absent from `.aw/config/project.json` so the default `HIGH` threshold applies and no finding sits unfixed at it. | yes |
| D-5 | Should review add a seventh test case to E-05, or fold the gated-stop assertion into the existing case (d)? | ADD IT AS A SEPARATE CASE (d2). | (a) Fold it into (d) as an extra assertion - rejected: (d) pins the ungated stop concession, which is shipped behavior this plan preserves, while (d2) pins a behavior no shipped test covers and which the authored plan got wrong; one failing test naming one defect is what makes the mutation proof legible. (b) Rely on E-06's sweep alone - rejected: the sweep reports a count and a property over 672 rows, so its failure names a class rather than the case, and a reader debugging it has to reconstruct which row mattered. | The plan's own right-sizing convention (one concern per item, one test surface per assertion); review's mutation run showing the sweep and a targeted case fail for the same cause but with very different diagnostics. | yes |
