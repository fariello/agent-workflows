- Id: vmrhj0
- Status: open
- Set: vmrhj0
- Priority: medium
- Work-Kind: chore
- Summary: the turn-retry allowlist admits only the legacy token failed-safely while its canonical replacement fail-gate is non-retryable, so whether a host-failure turn is retryable depends on which vocabulary generation wrote the disposition

## Workflow history
- 2026-09-30 created (aw backlog): the turn-retry allowlist admits only the legacy token failed-safely while its canonical replacement fail-gate is non-retryable, so whether a host-failure turn is retryable depends on which vocabulary generation wrote the disposition

FOUND WHILE AUTHORING plan `4gx141` (backlog `rb4wgj`), whose E-04 must state which disposition token spec 25kzda 5.5's host-failure rows mean and therefore surfaced this.

WHAT WAS MEASURED, at HEAD `20869a79`, by importing the shipped module. `runner_shared.TURN_RETRYABLE_DISPOSITIONS` is `frozenset({'failed-safely'})`, i.e. the turn-retry allowlist has exactly one member. That member is a LEGACY token: `TERMINAL_STATUS_ALIASES` maps `'failed-safely' -> 'fail-gate'`, and `'failed-safely' in TERMINAL_STATES_CANONICAL` is False. Its canonical replacement IS non-retryable: `turn_failure_is_retryable({}, 'fail-gate')` returns False with the reason 'lifecycle gate or clean-base gate refused; not a host failure to retry without human action'.

WHY THIS IS NOT (YET) A BUG, stated so nobody escalates it without new evidence. The retry path still FIRES, because live code paths still write `failed-safely`: the dispatcher refusal in `runner_shared` (`item['status'] = 'failed-safely'`), both hosts' `DriverError` arms (`runnable['status'] = 'failed-safely'` in `oc_runipd` and `agy_runipd`), and `lane_containment.BOUND_EXPIRY_DISPOSITION`. So no turn that reaches the allowlist is wrongly refused today.

WHY IT IS WORTH TRACKING ANYWAY. `reconcile_disposition`'s documented five rungs end in `return ('fail-verify' if exit_code == 0 else 'fail-gate')`, so the nonzero-exit fallback (which is spec 5.5's 'host nonzero exit' class by name) produces `fail-gate`, which is NOT in the allowlist. Whether a host-failure turn is retryable therefore depends on WHICH PRODUCER wrote the disposition rather than on what happened, and a future statusvocab migration that retires the legacy token would silently empty the allowlist.

WHY IT IS NOT FIXED BY SIMPLY ADDING `fail-gate`. That would be a behavior change in the UNSAFE direction: `fail-gate` is also what a lifecycle gate refusal and a clean-base refusal write, and spec 5.5 forbids retrying a human approval gate. A correct fix needs a producer-by-producer audit distinguishing the host-failure writers of `fail-gate` from the gate-refusal writers, which is why it was deferred out of `4gx141` rather than absorbed into it.

WHERE. `runner_shared.TURN_RETRYABLE_DISPOSITIONS`, `runner_shared.TURN_RETRY_CLASSIFICATION`, `runner_shared.turn_failure_is_retryable`, `runner_shared.TERMINAL_STATUS_ALIASES`, `runner_shared.reconcile_disposition`; spec `25kzda` section 5.5. Recorded as OQ-01 (deferred) in plan `4gx141`, whose E-04 spec table is the artifact that makes this question visible to the audit.
