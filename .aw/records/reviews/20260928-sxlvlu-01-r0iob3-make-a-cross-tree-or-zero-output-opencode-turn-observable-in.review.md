# Review findings: plan r0iob3

- Subject-Id: r0iob3
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `690a477a` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` CONFORMS
after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: `git status --porcelain --`
on the plan path was empty.

THE PLAN'S CENTRAL CLAIM IS TRUE, IMPORTANT, AND WELL MEASURED. Its headline finding is that the
backlog item's own scope note ("NOT urgent for this repository: the shipped mitigation means no
isolated turn reuses a session today") EXPIRED, and that reproduces exactly. F-05 reproduces: the
sweep branch's `or options.get("session")` fallback passes an operator-named session into the sweep
lane (shape (c) yields `ses_OP`), while shapes (a), (b) and (d) behave as the plan states, and the
decisive negative case (a recorded `REVIEW_SWEEP_SESSION_KEY` wins via the `or`, yielding `ses_SWEEP`)
holds too. F-06 reproduces verbatim against the real reconciler: a review item with an empty run
directory and `exit_code=0` returns `reviewed`, while an execute item returns `fail-verify`. F-09
reproduces (the stall path writes an `ipd-stalled` event, a lane snapshot and a red line; the
completion path has no zero-event check). The deliberate-stop precedence holds (`interrupted`, via
`runner_stop.STOPPED_DISPOSITION`). The plan's honesty about what it did NOT establish (F-07, the
denied sandbox, the cause unproven) is exemplary, and its decision to build a cause-agnostic detector
rather than wait on a diagnosis is the right call. Both open questions are resolved from evidence with
real reasoning, and OQ-02's distinction between opencode's contract and this driver's is exactly right.

WHAT REVIEW FOUND IS THAT E-01 WOULD HAVE DUPLICATED A SHIPPED PREDICATE, THAT THE HARM IS WORSE THAN
THE PLAN MEASURED, AND THAT TWO "IDENTICAL" THINGS ARE NOT IDENTICAL.

**E-01 WOULD HAVE BUILT A SECOND COPY OF A RULE THAT ALREADY SHIPPED, AND THE SHIPPED ONE REFUSES
THIS CASE DELIBERATELY (PR-101, HIGH, and the finding this review exists for).** `runner_shared.turn_attempted_nothing`
landed with EXECUTED plan `dy9ymn` (`.aw/records/plans/executed/20260919-reaskscore-03-dy9ymn-...ipd.md`,
all six E-items `[x]`). It already answers "did this finished turn provably attempt nothing?", already
returns a reasoned `ZeroWorkVerdict` rather than a bare bool, already has an impure collector
(`read_zero_work_evidence`) and a performer (`handle_zero_work_retry`) wired into BOTH hosts' dispatch
loops with budget arithmetic and a `zero-work-retry` event. E-01 proposed adding `turn_produced_no_work`
beside `extract_session_id`, which would have been a parallel rule for the same question, in a
repository whose own conventions section (the plan's own Step 0 note) warns that "a second reader of
the same file with different tolerance is how the two hosts' readers diverged". Measured, what actually
blocks the shipped predicate is TWO deliberate guards, not an absence: it refuses `action == "review"`
in terms ("whose zero-work case is a different question"), and `handle_zero_work_retry` opens
`if status != "partial": return status` while a silent review ends `reviewed`. So the correct work is to
ANSWER that deferred question inside the shipped rule.

**AND THE ARTIFACT E-01 CHOSE IS THE WEAKER ONE, WHICH IS MEASURABLE (PR-101 second half).** E-01
instructed the executor to "MEASURE THE LOG, NOT THE EXIT CODE". But a zero-events log is weaker
evidence than the shipped four-fact conjunction (no outcome file AND head unmoved AND no lane commit
beyond base AND clean tree). Demonstrated: for an attempt whose log is empty but whose tree is DIRTY,
the shipped predicate correctly refuses with "an uncommitted edit is work, and re-dispatching over it
risks the agent duplicating or fighting its own prior changes", whereas a log-only rule would have
scored that turn silent and been WRONG. A log can also be empty for transport reasons while files were
written. The plan was right that the exit code lies; it did not notice that the log can lie too, and
that the repository already chose stronger evidence.

**A SILENT TURN AFFIRMS `approved`, NOT MERELY `reviewed` (PR-103, HIGH).** F-06 measured the
`to-review` case. The branch actually reads `if status in ("reviewed", "approved"): return status`, so
it returns the plan's OWN CURRENT STATUS. Measured across the status matrix with an empty run directory
and `exit_code=0`: an already-`approved` plan is scored **`approved`** by a turn that produced nothing.
`approved` is the status the auto-approve and dispatch predicates read to decide a plan MAY EXECUTE, so
the harm is not only "a lifecycle advance" but an affirmation of execution authority by a turn that
never ran. E-04 as written targeted the bare `return "reviewed"` and would plausibly have left the
`approved` path intact.

**THE TWO SESSION EXPRESSIONS ARE NOT IDENTICAL AND THE SHARED ONE IS LESS GUARDED (PR-105, MEDIUM).**
E-03 said "the identical expression in `runner_shared.execute_item_core`" and "they are the same
expression in two places". Measured by re-deriving both: they share the `or options.get("session")`
fallback, which IS the defect, but `oc_runipd` gates on `turn_runs_in_review_sweep_lane(state, work_dir)`,
a REALPATH comparison against the recorded lane, while `runner_shared` gates on
`is_review and isolation_for_action(options, "review")`, a CONFIGURATION FLAG with no tree comparison at
all. Consequence, measured: the shared copy yields `ses_OP` for a review turn REGARDLESS of whether the
tree is the sweep lane, and its two `session_id = None` overrides sit on the production and generic
`isolate` EXECUTE branches, never on the review-sweep branch. A fix pasted twice would be wrong, and the
shared copy needs MORE than the oc copy does.

**E-02's DISPOSITION INSTRUCTION RESTS ON A WRONG DATA SHAPE AND A WRONG PREMISE (PR-104, MEDIUM).**
E-02 said `TURN_RETRY_CLASSIFICATION` "maps every persisted driver disposition" and that the executor
should "prefer an existing retryable row" because "a silent turn is plainly retryable in the
host-failure sense". Measured: it is a `tuple[tuple[str, bool, str], ...]` of 29 triples, not a mapping;
exactly TWO rows are retryable (`failed-safely`, `failed`), both host-failure rows whose reasons name a
nonzero exit, which would misdescribe a turn that exited ZERO; and the table's own `partial` row is
deliberately RESERVED for the shipped zero-work predicate. So the instruction pointed at the two rows
least appropriate to the case.

**E-02's SEAM AND E-05's COUNT (PR-102, PR-106, both MEDIUM).** E-02 said the wiring "must be in
`execute_item_core` and not in either host, or one host keeps the defect", but the shipped twin
`handle_zero_work_retry` is deliberately called from each host's DISPATCH LOOP after `execute_item`
returns, and its docstring records that placement as load-bearing because the check must precede
`cascade_dependency_blocked`. So there are two legitimate seams with different properties (recording
versus re-dispatching) and the plan asserted one without acknowledging the other. Separately, F-08 says
the falsified `xd9sll` sentence "appears in three places, not one" and argues that missing a site is how
the claim survives; measured, there are SEVEN sites (four in `oc_runipd.py`, three in `runner_shared.py`),
so F-08's own argument applies to F-08. Two of the four it missed assert the override in the same present
tense.

**THREE TEST FILES THE SURROUNDING COMMENTS CITE DO NOT EXIST (F-18, folded into PR-106).**
`tests/test_lane_session_isolation.py` (cited by `oc_runipd`'s `resume_session` comment as pinning "no
`--session` on a lane"), `tests/test_retry_consumption.py` and `tests/test_turn_bounds.py` were all
deleted by `19313eed`. No surviving test references `REVIEW_SWEEP_SESSION_KEY`, `sweep_lane_turn` or
`turn_runs_in_review_sweep_lane` at all, so E-03's negative cases are currently unpinned by anything. A
comment asserting a guarantee held by a nonexistent test is the same defect class this item exists to
fix, so E-05 now has to dispose of them while it is editing those very comments.

Everything else checked and HELD. The plan's deferral rows are honest and well reasoned, particularly
the refusal to widen `review_findings.review_attestation_missing` to plans, which F-11 correctly measures
as corpus-hostile ("zero review files existed against 428 plans") and which I confirmed is still
single-caller. The `plan_repo`/lane-read constraint in E-04 is correct and its cited rationale is verbatim
in the code. The spec-sync section is right that `25kzda` 5.5 is consumed rather than amended, and its
conditional instruction to declare the spec if a new disposition is needed is exactly the right shape,
which is why PR-104's option (c) points at it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-101 | HIGH | IN-SCOPE | C. Architecture (duplicate paths) / E. Testing | MEASURED at HEAD `690a477a`: `runner_shared.turn_attempted_nothing` on a silent REVIEW turn returns `attempted_nothing=False, proven=True, reason="this is a REVIEW action, whose scoring reads the plan's `- Status:` and whose zero-work case is a different question"`; `handle_zero_work_retry` opens `if status != "partial": return status`; `read_zero_work_evidence` and per-host call sites in `oc_runipd`/`agy_runipd` exist; `.aw/records/plans/executed/20260919-reaskscore-03-dy9ymn-...ipd.md` has all six E-items `[x]`. Also measured: with an empty log and a DIRTY tree the shipped predicate refuses ("an uncommitted edit is work") where a log-only rule would say silent | **E-01 WOULD HAVE BUILT A PARALLEL COPY OF A SHIPPED RULE, AND CHOSEN WEAKER EVIDENCE.** The zero-work predicate, its collector and its both-host performer already exist; what stops them here is two DELIBERATE guards (the `action == "review"` refusal and the `partial`-only trigger), not an absence. And the session log E-01 chose is measurably weaker than the shipped four-fact conjunction, so a log-only rule would misclassify a turn that edited files without emitting events. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 rewritten to EXTEND the shipped `turn_attempted_nothing` (or an evidence-sharing sibling) so it answers the review case, measuring the attempt's recorded facts rather than the log, with any log reading confined to the SUPPORTING role `host_truncation_of_attempt` already has, and the fail-closed "cannot prove" direction preserved. New F-13, F-14. V-01 rewritten to require the before/after review verdict, the EXECUTE-path non-regression, an UNMODIFIED `tests/test_reaskscore_composed.py` run, and proof that no second predicate was added. Required tests gained the shipped-predicate regression surface. |
| PR-103 | HIGH | IN-SCOPE | A. Correctness and data integrity / B. Authorization | MEASURED at HEAD `690a477a` driving the real `runner_shared.reconcile_disposition` over {review, execute} x {to-review, reviewed, approved, draft} x {exit 0, 1} with an empty run dir: review + `approved` + exit 0 -> **`approved`**; review + `to-review`/`draft` + exit 0 -> `reviewed`; execute -> `fail-verify`/`fail-gate` throughout. Source: `if status in ("reviewed", "approved"): return status` | **A ZERO-OUTPUT TURN AFFIRMS `approved`, WHICH IS EXECUTION AUTHORITY, NOT JUST A REVIEW.** F-06 measured only the `to-review` case, so E-04 targeted the bare `return "reviewed"` and would plausibly have left the `approved` path intact. `approved` is what the auto-approve and dispatch predicates read to decide a plan MAY EXECUTE, so a silent turn can affirm that a plan is cleared to run. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-04 now states the branch returns the plan's own status, names the `approved` case explicitly, and requires BOTH returns to be covered. New F-15. V-04 requires the `approved` before/after pasted beside the `reviewed` one. The Required tests disposition matrix gained the plan-status dimension. The approval gate now says a silent turn stops being scored `reviewed` OR `approved`. |
| PR-105 | MEDIUM | IN-SCOPE | A. Correctness / G. Executability | MEASURED at HEAD `690a477a` re-deriving both expressions: shared guard is `review_uses_sweep_session = is_review and isolation_for_action(options, "review")`; oc guard is `sweep_lane_turn = runner_shared.turn_runs_in_review_sweep_lane(state, work_dir)` (realpath). Shared copy yields `ses_OP` for a review turn with sweep isolation ON **or OFF**; `session_id = None` appears exactly twice inside `execute_item_core`, both on non-review branches | **THE "IDENTICAL EXPRESSION IN TWO PLACES" CLAIM IS FALSE, AND THE SHARED COPY IS THE LESS GUARDED.** They share only the defective fallback. `oc_runipd` compares TREES; `runner_shared` reads a CONFIG FLAG and has no tree check at all, so it carries the operator session even when the tree is not the sweep lane. A fix written once and pasted twice would be wrong, and the shared side needs strictly more than the oc side. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-03 now states the guards differ, quotes each, gives the measured consequence, and directs the executor to write the refusal against the ACTUAL guard at each site, reusing `turn_runs_in_review_sweep_lane` for the shared copy rather than restating it. New F-16. V-03 requires each site's guard quoted plus the shared copy's before/after for a non-sweep-tree review turn. |
| PR-104 | MEDIUM | IN-SCOPE | A. Correctness / G. Executability | MEASURED at HEAD `690a477a`: `TURN_RETRY_CLASSIFICATION` is `tuple[tuple[str, bool, str], ...]`, 29 rows; retryable on `failed-safely` and `failed` ONLY; `reviewed` ("a review outcome, not a failed execution"), `approved` and `partial` all present and non-retryable; the table's `partial` comment reserves that row for the zero-work predicate. Plan E-02 as authored: "maps every persisted driver disposition ... prefer an existing retryable row" | **E-02 DESCRIBED A MAPPING THAT IS A TUPLE, AND POINTED AT THE TWO ROWS LEAST APPROPRIATE TO THE CASE.** The only retryable rows are host-failure rows whose reasons name a nonzero exit, which misdescribes a turn that exited ZERO, while `partial` is deliberately reserved for the shipped predicate. The disposition choice is a contract decision, not a lookup. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 corrected with the measured shape and counts, and the premise replaced by THREE stated options (route through the shipped `partial`+zero-work path; reuse a non-retryable row and forfeit the rescue; append a triple and declare `25kzda` first), requiring the executor to record which and the retryability consequence. New F-17. V-02 requires the chosen TRIPLE quoted and the option named. |
| PR-102 | MEDIUM | IN-SCOPE | C. Architecture / G. Executability | `handle_zero_work_retry`'s docstring: it must be called "INSIDE the dispatch loop, immediately after `execute_item` RETURNS", because the check must precede `cascade_dependency_blocked` which "runs at the TOP of the loop"; its two call sites are in `oc_runipd` and `agy_runipd`, NOT in `execute_item_core`. Plan E-02 as authored: "must be wired THERE and not in either host, or one host keeps the defect" | **THE PLAN ASSERTED ONE SEAM WHILE THE SHIPPED TWIN FOR THE SAME CLASS OF CHECK DELIBERATELY USES THE OTHER.** Two legitimate seams exist with different properties: the shared in-core seam (simpler, shared by construction, recording only) and the post-return dispatch seam (per-host binding, but where a REQUEUE is still possible). Asserting the first without acknowledging the second would either forfeit the rescue silently or send the executor to add a second call beside the shipped one. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now describes both seams with their properties and the cascade-ordering reason, requires the executor to CHOOSE and state which and why, and requires extending the SHIPPED call rather than adding a second one if the post-return seam is chosen. V-02 requires the seam named plus per-host symmetry evidence when applicable. |
| PR-106 | MEDIUM | IN-SCOPE | A. Correctness / F. Honest documentation | MEASURED at HEAD `690a477a`: `grep -rc xd9sll agent_workflows/*.py` -> `oc_runipd.py:4`, `runner_shared.py:3`, i.e. SEVEN sites; F-08 names three. The two missed asserting sites are `runner_shared`'s `WHY ONE LANE FOR THE WHOLE SWEEP` block ("an opencode session's own directory binding overrode `--dir`") and `execute_item_core`'s `if isolate:` comment ("silently executing in the wrong worktree"). Separately `git log --oneline --diff-filter=D -1 --` names `19313eed` for `tests/test_lane_session_isolation.py`, `tests/test_retry_consumption.py` and `tests/test_turn_bounds.py`; `grep -rln` over `tests/` for the three sweep-session symbols returns nothing | **F-08 UNDERCOUNTS THE SITES ITS OWN ARGUMENT SAYS MUST ALL BE FIXED, AND THE COMMENTS CITE THREE DELETED TEST FILES AS LIVE GUARANTEES.** F-08 argues "correcting one and leaving two is how the falsified claim survives", which applies to the four it missed. And the same comment block cites `tests/test_lane_session_isolation.py` as pinning "no `--session` on a lane" when that file was deleted; no surviving test pins any sweep-session symbol, so E-03's negative cases are unpinned. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now requires enumerating ALL SEVEN sites with a per-site statement of whether it asserts the falsified mechanism, names the two missed asserting sites, and requires disposing of the three dead test citations (re-point at a surviving test, or state in the comment that the guarantee is unpinned). New F-18. V-05 requires the full seven-hit accounting first and the citation dispositions. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-101: the predicate E-01 specifies already exists and deliberately refuses this case. REPLAN the item, or repair it into an extension? | REPAIR into an extension of the shipped `turn_attempted_nothing`. The plan's GOAL (make a silent turn observable) is right and its other four items are unaffected; only E-01's mechanism was wrong. | (a) REPLAN the whole plan: rejected, four of five items stand and the goal is correct, so the repair is bounded to one E-item plus the validation that guards it. (b) Keep the new parallel predicate and leave the shipped one alone: rejected as the duplicate-path defect this repository repeatedly pays for, and the plan's own Step 0 conventions warn against exactly it. (c) Delete the shipped review-refusal guard outright: rejected as a decision beyond this review - the guard is a recorded `dy9ymn` design choice with a stated reason, so the plan must ANSWER the deferred question rather than silently drop the refusal, which is what the rewritten E-01 requires. | `runner_shared.turn_attempted_nothing`'s `action == "review"` refusal and its stated reason; `handle_zero_work_retry`'s `partial`-only guard; the executed plan `dy9ymn` with all E-items complete; the measured dirty-tree case showing the shipped conjunction is stronger than a log read. | yes |
| D-2 | PR-104: E-02's disposition instruction is unusable as written. Pick the disposition here, or hand the executor a decision? | HAND A BOUNDED DECISION: three named options with their consequences, requiring the executor to record which and why. | (a) Pick `partial` here and mandate it: TEMPTING, since it is the one row built for "the turn ran and produced nothing" and is already budget-bounded, but rejected because whether a silent REVIEW should be re-dispatched at all is a behavior question this review has no measurement for - the review path has no `partial` today and routing it there changes more than the record. (b) Pick a non-retryable row here: rejected, it forfeits the rescue by reviewer fiat. (c) Leave E-02's original "prefer a retryable row": rejected, measured to point at two host-failure rows that misdescribe an exit-0 turn. | The measured 29-row tuple with two retryable rows; `TURN_RETRY_CLASSIFICATION`'s own `partial` reason reserving it for the zero-work predicate; the plan's existing spec-sync clause already requiring `25kzda` be declared if a new status is needed, which makes option (c) safe to offer. | yes |
| D-3 | PR-102: which seam should E-02 use? | STATE BOTH with their properties and require the executor to choose and record. | (a) Mandate the in-core seam as the plan did: rejected, it silently forfeits the requeue and contradicts where the shipped twin for this class of check deliberately sits. (b) Mandate the post-return seam: rejected, if the refusal only needs RECORDING then the shared in-core seam is simpler and shared by construction, and mandating a per-host binding would add symmetry risk for no gain. | `handle_zero_work_retry`'s docstring on placement and the cascade-ordering reason; its two per-host call sites; `execute_item_core`'s own docstring claim to drive the gates identically on both hosts. | yes |
| D-4 | PR-106: three cited test files are deleted. File a separate backlog item, or fold the disposition into E-05? | FOLD INTO E-05, which is already editing those exact comments. | Filing a separate item: rejected as gratuitous coordination - E-05's whole subject is correcting false claims in these comments, a dead test citation IS a false claim in the same comments, and requiring a second artifact to fix a line the executor is already rewriting would leave the false citation in place meanwhile. | `git log --diff-filter=D` naming `19313eed` for all three paths; E-05's existing scope (the same comment block); the absence of any surviving test for the sweep-session symbols. | yes |

Every finding is `FIXED`; none is left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes`
question is owed and the repository's `HIGH` gate threshold is satisfied without one. PR-101 and PR-103
are `HIGH` and were FIXED in place rather than escalated, which is correct under the Fix Bar: each has
overall Remediation Risk Medium (a bounded, local plan edit with a clear verification path), not
Medium-High. No decision above is `Reversible: no`, so none requires escalation. OQ-01 and OQ-02 remain
`resolved` as authored; both resolutions were checked and stand. No new open question is created.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- No pre-review snapshot was owed: `git status --porcelain -- <plan>` was EMPTY before editing.
- **F-06 REPRODUCED VERBATIM, THEN WIDENED (PR-103).** Real `runner_shared.reconcile_disposition` in a
  scratch repo with one plan, an EMPTY run directory (no outcome file, no session log), `exit_code=0`:
  `action=review -> 'reviewed'`, `action=execute -> 'fail-verify'`. Across the status matrix:
  review/`to-review`/0 -> `reviewed`; review/`reviewed`/0 -> `reviewed`; review/`approved`/0 ->
  **`approved`**; review/`draft`/0 -> `reviewed`; every review/exit-1 -> `fail-gate`; every execute/0
  -> `fail-verify`; every execute/exit-1 -> `fail-gate`.
- **DELIBERATE-STOP PRECEDENCE CONFIRMED.** review + `stopped.stopped_deliberately` + exit 0 ->
  `'interrupted'`, equal to `runner_stop.STOPPED_DISPOSITION`.
- **F-05 REPRODUCED over all four shapes** by re-deriving `oc_runipd.run_opencode`'s expression:
  (a) execute, not isolated, `--session ses_OP` -> `ses_OP`; (b) execute, isolated -> `None`;
  (c) review in sweep lane, no sweep session -> `ses_OP` (the defect); (d) review not in sweep tree ->
  `None`. Plus the decisive negative: (c') review in sweep lane WITH a recorded
  `REVIEW_SWEEP_SESSION_KEY` -> `ses_SWEEP`, the operator id unused, so the sweep's own continuity is
  what E-03 must preserve.
- **PR-105, THE GUARD DIVERGENCE.** The same re-derivation over `runner_shared.execute_item_core`:
  execute/not-isolated -> `ses_OP`; execute/isolated -> `None`; review with sweep isolation ON ->
  `ses_OP`; review with sweep isolation **OFF** -> `ses_OP`. Guard spellings confirmed by
  `inspect.getsource`: shared is `review_uses_sweep_session = is_review and isolation_for_action(options,
  "review")`, oc is `sweep_lane_turn = runner_shared.turn_runs_in_review_sweep_lane(state, work_dir)`.
  `session_id = None` occurs exactly TWICE inside `execute_item_core`, on the spec/backlog-production
  branch and the generic `if isolate:` execute branch, never on the review-sweep branch. Both copies
  reach a launch: the shared one flows into `spawn_executor(prompt_path, work_dir, tracker, plan_path,
  attempt_no, session_id, use_continue)`.
- **PR-101, THE SHIPPED PREDICATE.** Real `runner_shared.turn_attempted_nothing` on a silent review
  turn -> `attempted_nothing=False, proven=True`, reason "this is a REVIEW action, whose scoring reads
  the plan's `- Status:` and whose zero-work case is a different question". On the equivalent EXECUTE
  shape -> `attempted_nothing=True, proven=True` with the full four-fact reason. Its refusal cases all
  answer correctly (outcome written / head moved / dirty tree / outcome unknowable).
  `ZERO_WORK_REFUSED_STATUSES` = `['dependency-blocked', 'fail-depend', 'integration-deferred',
  'interrupted', 'merge-retry', 'not-attempted', 'not-run', 'queued', 'running', 'unknown_outcome']`,
  which does NOT contain `reviewed`, so the review exclusion is carried by the action guard specifically.
  `handle_zero_work_retry`'s opening guard confirmed as `if status != "partial": return status`.
  Its call sites: `oc_runipd.py` and `agy_runipd.py`, one each, neither inside `execute_item_core`.
- **PR-101's EVIDENCE-STRENGTH DEMONSTRATION.** For an attempt with no outcome file, unmoved HEAD and a
  DIRTY tree, the shipped predicate refuses: "the shared checkout's tree is DIRTY, and an uncommitted
  edit is work; re-dispatching over it risks the agent duplicating or fighting its own prior changes".
  A zero-events-log rule would have called that turn silent.
- **PR-104, THE TABLE.** `TURN_RETRY_CLASSIFICATION` is a `tuple` of 29 `(name, retryable, reason)`
  triples. Retryable: `failed-safely`, `failed` only. Present and non-retryable: `reviewed` ("a review
  outcome, not a failed execution"), `approved`, `partial`, plus 24 others. `interrupted` present.
- **PR-106, THE SITE COUNT AND THE DEAD CITATIONS.** `grep -rc xd9sll agent_workflows/*.py` ->
  `oc_runipd.py:4`, `runner_shared.py:3`. The four `oc_runipd` hits are the `run_opencode` session
  comment, the `ajxr5d` block (two lines), and the `resume_session` comment; the three `runner_shared`
  hits are the `WHY ONE LANE FOR THE WHOLE SWEEP` block, `turn_runs_in_review_sweep_lane`'s docstring,
  and `execute_item_core`'s `if isolate:` comment. `git log --oneline --diff-filter=D -1 --` returns
  `19313eed test: trim test suite from 9,136 to under 2,000 tests` for
  `tests/test_lane_session_isolation.py`, `tests/test_retry_consumption.py` and
  `tests/test_turn_bounds.py`. `grep -rln` over `tests/` for `REVIEW_SWEEP_SESSION_KEY`,
  `review_sweep_session`, `sweep_lane_turn` and `turn_runs_in_review_sweep_lane` returns NOTHING.
- **F-11 CONFIRMED AND ITS CONSTRAINT UPHELD.** `review_findings.review_attestation_missing` is still
  called only from the spec transition inside `reconcile_disposition`, and the spec branch's
  lane-reading rationale is verbatim in the code, so E-04's instruction not to import it for plans is
  correct and was left intact.
- **THE PLAN'S OWN NEW TEST FILES DO NOT YET EXIST** (`tests/test_silent_turn_observability.py`,
  `tests/test_cross_tree_session_refusal.py`), as expected for a pending plan; the five standing
  surfaces its Required tests names (`test_oc_runipd.py`, `test_runner_shared.py`,
  `test_defect_report.py`, `test_review_lane_output_commit.py`, `test_interrupt_reconcile.py`) all
  exist. `tests/test_reaskscore_composed.py`, which pins the shipped predicate, was located and added
  to the Required tests as a regression surface.
- No pending-plan collision: `grep -rln` over `.aw/records/plans/pending/` for
  `reconcile_disposition`, `REVIEW_SWEEP_SESSION_KEY` and `turn_attempted_nothing` returns only this
  plan, so no sibling is editing the same semantics (several pending plans declare
  `runner_shared.py` as a FILE, which the runner's worktree isolation already handles).
- Post-revision suite re-check: `python3 -m pytest` -> `2937 passed, 2 skipped, 3 warnings in 46.35s`
  (plus the standard `201 tests were deselected` notice), confirming this review touched no code. The
  count differs from the 2935 observed during the immediately preceding review in this same lane
  because `main` advanced between them (the `pjuoyj` lane merged), which is why a baseline must be
  captured at the same commit as its after-state rather than carried across.
- `aw sanitize --agent` -> exit 0, no findings.

### Probe scripts

The three probe scripts backing these measurements were written under
`.aw/workflow-artifacts/plan-review-r0iob3/` (gitignored, so not committed): `probe_disposition.py`
(the F-06 reproduction, the full status matrix, the stop precedence, the retry table),
`probe_session.py` (both session expressions re-derived over F-05's shapes plus the guard comparison),
and `probe_shipped_predicate.py` (the shipped `turn_attempted_nothing` asked the review question, its
refusal matrix, and the log-versus-facts evidence-strength demonstration).
