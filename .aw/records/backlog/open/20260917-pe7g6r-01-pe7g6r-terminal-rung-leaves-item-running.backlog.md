- Id: pe7g6r
- Status: open
- Blocks-Release: next
- Set: pe7g6r
- Priority: high
- Work-Kind: bug
- Summary: test_the_terminal_rung_still_records_the_item_interrupted fails deterministically in isolation: after 3x SIGINT the in-flight item is left 'running', not 'interrupted', so main's exit-130 item bookkeeping is not preserved at the terminal rung

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): test_the_terminal_rung_still_records_the_item_interrupted fails deterministically in isolation: after 3x SIGINT the in-flight item is left 'running', not 'interrupted', so main's exit-130 item bookkeeping is not preserved at the terminal rung

FOUND BY: rununify Order 11 (`3dki3o`) E-02 while taking its execution baseline.

REPRODUCTION, deterministic (3 of 3 consecutive runs) at HEAD 761edad3:

    python3 -m pytest 'tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted' -o addopts='' -p no:randomly

    AssertionError: 'running' != 'interrupted'
    : the interrupted item must be recorded `interrupted`, got {... 'status': 'running'}

WHY IT IS INVISIBLE TODAY, which is the part worth fixing beyond the assertion. The class is marked
`@pytest.mark.slow`, and `pyproject.toml`'s `addopts` already supplies `-m 'not slow'`, so a BARE
`python3 -m pytest` (the run the execution contract mandates) DESELECTS it: the bare suite is
7715 passed, 0 failed at this HEAD while this contract is broken. It is only reachable with
`-m slow` or an explicit node id. So the regression can persist indefinitely without any red run.

WHAT THE TEST ASSERTS AND WHY IT MATTERS: the test's own docstring records the DECISION that
registering a SIGINT handler is a MODIFICATION which removes the default `KeyboardInterrupt` that
`main`'s exit-130 path and `execute_item`'s item-level bookkeeping both depended on, and that the
terminal rung PRESERVES both deliberately because later phases rely on the interrupted item being
recorded. An item left `running` is exactly the state its final assertion calls out as what must
never happen, and a stale `running` is what `aw runs` reports as a live run forever.

NOT CAUSED BY THE OBSERVING PLAN: `3dki3o` changes no product code (`git diff agent_workflows/` is
empty), and the failure reproduces with the plan's two new test files moved aside, with
`AW_EXECUTION_ROLE` unset, and with `AW_PIN_KEEP_ROOT` unset.

NOTE ON THE PLAN'S OWN PREDICTION: plan `3dki3o`'s Required tests item 8 predicted this exact failure
at review HEAD 6a3a671c and told the executor not to attribute it to the plan. This item exists so
the prediction becomes a tracked defect rather than a note inside one plan.
