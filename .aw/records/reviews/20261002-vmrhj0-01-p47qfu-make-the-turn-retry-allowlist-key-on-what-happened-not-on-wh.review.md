# Review findings: plan p47qfu

- Subject-Id: p47qfu
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REJECT - NEEDS REPLAN
- Findings: PR-001 (BLOCKER, replan), PR-002 (HIGH, open), PR-003 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T032734Z-4093657` at HEAD `0b09c3347`. The plan was
committed and byte-identical to the sealed lane input (rev-5), so no pre-review snapshot was needed. `- Kind: child`,
so `IPD-S407`/`IPD-S408` do not apply. `aw ipd lint --phase author --agent` was clean before review.

Re-measured by importing the shipped module: F-01, F-02, F-05 and F-10 reproduce exactly
(`TURN_RETRYABLE_DISPOSITIONS == {'failed-safely'}`; `turn_failure_is_retryable({}, 'fail-gate')` False;
`canonical_terminal_status('failed-safely') == 'fail-gate'`; `reconcile_disposition(..., exit_code=1)` with no
outcome returns `fail-gate`). F-04 reproduces (`driver_error` assigned only in `runner_shared.refuse_undispatchable_typed_entry`,
`oc_runipd.run_queue`'s and `agy_runipd.run_queue`'s `except DriverError` arms). What does NOT hold is the plan's
premise that those producers feed the retry predicate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A correctness / D invariants / reachability | `runner_shared.execute_item_core` sole `handle_turn_failure_retry(` call (after `reconcile_disposition`); `oc_runipd.run_queue` `if runner_shared.refuse_undispatchable_typed_entry(...): ... continue` before `execute_item`; `oc_runipd.run_queue` / `agy_runipd.run_queue` `except DriverError as exc: runnable["driver_error"] = str(exc)` after `execute_item` raises | The three F-03 marker producers never reach `turn_failure_is_retryable`: the dispatcher refusal skips execution, and both `DriverError` arms run after `execute_item_core` has already raised past the retry site. The only retry-site disposition spelled `failed-safely` is `FINALIZE_RETRY_EXHAUSTED_STATUS`, which carries `finalize_refusal` and is refused. So E-01/E-02 would pass unit tests and change no real run, and the reachable case the Concern names (F-10, rung-5 `fail-gate`) carries no `driver_error`. Recorded as plan F-12. | C:High; U:Low; S:Low; F:High; Overall:High | REPLAN | Plan rejected. A sound replan sets the host-failure evidence where the run learns the host failed INSIDE `execute_item_core` (rung 5 of `reconcile_disposition` when `exit_code != 0`, possibly a `spawn_executor` failure), then re-authors E-01, E-02, V-01, V-02, F-03, F-04, F-07 and the Scope check. The test cases in E-04 (a)-(e) and the spec amendment in E-05 can carry over once the producer is real. |
| PR-002 | HIGH | UNDER-SCOPE | C retries / B safety | spec `25kzda` 5.5 "host nonzero exit that did not create an ambiguous side effect"; `reconcile_disposition` rung 5 `return ("fail-verify" if exit_code == 0 else "fail-gate"), outcome` | The only real producer reachable for this class (rung 5) cannot tell a clean crash from a turn that mutated the lane or ran gates before exiting nonzero, which is the spec's own exclusion. Choosing a side-effect discriminator, or accepting the risk, decides whether the runner newly spends paid correction turns on failures refused today. That is a risk-appetite decision for the maintainer. | C:Medium-High; U:Low; S:Medium; F:Medium-High; Overall:Medium-High | OPEN | Escalated to the plan as OQ-02 (`- Blocking: yes`, `- Finding: PR-002`), with options (a) retry only when the lane shows no commits and no dirty paths, (b) retry every rung-5 nonzero exit, (c) keep fail-closed and narrow the plan to the spec table, the comment and the canonicalization pin. |
| PR-003 | LOW | IN-SCOPE | G executability | V-02 "all five verdicts named in E-01's expected outcome" | The five verdicts are listed in E-02's expected outcome, not E-01's. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now cites E-02. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can PR-001 be repaired with bounded edits by moving the marker write to rung 5? | No. REPLAN, and the producer question goes to the maintainer as OQ-02 | Rewrite E-01 to mark every rung-5 nonzero exit (silently picks option (b) of OQ-02 and widens paid retries); keep the plan and add a reachability spike E-item (it would still ship dead wiring if the spike failed) | `runner_shared.reconcile_disposition` rung 5; spec `25kzda` 5.5 side-effect clause; `runner_shared.execute_item_core` retry call site | yes |
