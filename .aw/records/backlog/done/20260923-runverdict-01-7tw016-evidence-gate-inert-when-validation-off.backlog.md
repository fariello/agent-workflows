- Id: 7tw016
- Status: done
- Set: runverdict
- Priority: medium
- Work-Kind: followup
- Summary: The verifier-evidence gate has no effect when validation is OFF, which is oc's shipped default

## Workflow history
- 2026-09-26 done (aw set): NOT A DEFECT (retired, not implemented): the premise cannot occur. runner_shared computes validate once and the SAME variable guards the whole verifier block and is passed to integration_is_earned; every verify_disp assignment is inside that guard, so with validation OFF no verifier runs and no failed-evidence state exists. Reachable only by calling integration_is_earned directly in a test. Whether oc should validate by default is a separate policy question (runner_profiles RUNNER_REGISTRY oc validate_default), not this defect.
- 2026-09-23 created (aw backlog): The verifier-evidence gate has no effect when validation is OFF, which is oc's shipped default

MEASURED while executing plan `bxx9af` (runverdict Order 05), by calling the real `runner_shared.integration_is_earned` rather than reasoning about it.

WHAT IS WRONG. `bxx9af` makes a VERIFIED verdict with no test activity record as `unverified`, which correctly refuses integration on the validation-ON path. But the validation-OFF branch of `integration_is_earned` NEVER READS `verify_disp` at all, so the new refusal is inert there:

    validate=True,  verify_disp='unverified', suite=None      -> earned=False signal=verifier-declined
    validate=False, verify_disp='unverified', suite=PASSING   -> earned=True  signal=driver-run-suite

WHY IT MATTERS. `runner_profiles.RUNNER_REGISTRY['oc'].validate_default` is False while `['agy']` is True, so on OC'S SHIPPED DEFAULT an item whose verification showed no evidence still integrates on the suite signal. The guarantee holds on agy's default and on oc only under `--validate`.

WHY IT WAS NOT FIXED IN `bxx9af`. It is arguably CORRECT as it stands: when validation is off no verifier ran, so there is no verdict to honor and the driver-run suite is the intended trust signal. Changing it would widen that plan into the integration gate, which its own scope fence forbids. `bxx9af` therefore claims no guarantee broader than measured (in-tree comment at the gate, plus `IntegrationInteractionTests::test_validation_off_ignores_the_verdict_entirely`, whose docstring states it pins the TRUE behavior and not the desirable one).

THE REAL QUESTION FOR A HUMAN, which is why this is `followup` and not `bug`: should an item whose verifier PRODUCED an outcome that failed the evidence check be treated differently from an item where NO verifier ran at all? Today both are invisible to the validation-OFF branch. A defensible fix is to refuse when a verification was ATTEMPTED and failed its evidence check, while leaving the no-verifier-ran case on the suite signal. That distinction is already available in state: `verify_evidence_absent` is set only in the first case.

NOT A DEFECT INTRODUCED BY `bxx9af`: this is pre-existing behavior of `integration_is_earned` (plan F-17 measured it at review and it reproduced at execution unchanged).
