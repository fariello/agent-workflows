- Id: isjodh
- Status: open
- Set: isjodh
- Priority: medium
- Work-Kind: followup
- Summary: Admit a non-plan dependency target (spec/backlog) into --with-dependencies, which currently refuses it

## Workflow history
- 2026-09-20 created (aw backlog): Admit a non-plan dependency target (spec/backlog) into --with-dependencies, which currently refuses it

THE GAP. Spec 25kzda :166 says `--with-dependencies` subjects "any newly introduced type" to the mixed-type gate, which presupposes a `spec` or `backlog` dependency target can join the queue, and `ipd_schema.ITEM_DEP_TYPES` admits `exists:spec:<id6>` and `state:backlog:<status>:<id6>` as legal grammar. depclosure 01 (`dhycim`) shipped the closure PLAN-TARGETS-ONLY: `runner_shared.closure_target_admission` REFUSES a non-plan target, naming the type. So the shipped flag is narrower than the approved spec. The narrowing is deliberate, loud, and stated in the flag's own --help; it is filed here so it is tracked rather than living only inside one plan record.

WHAT A FIXING PLAN MUST DO, all three, because doing one alone ships a worse state than the refusal:
1. GIVE A NON-PLAN TARGET A QUEUE ENTRY. `discover_plans` walks the two plans trees only, so the manifest cannot carry one. Either extend discovery (which makes a live MIXED selection reachable for the first time - a real behavioral change deserving its own review) or construct a second queue-entry shape (which every downstream consumer must then learn).
2. FIX THE LOOP THAT FEEDS THE MIXED-TYPE GATE. `initialize_run_core` hands `enforce_mixed_type_gate` its `selected_plan_paths` list, NOT `queue_ids`, and that list is built by resolving `manifest["plans"][id6]` inside `except (DriverError, KeyError): continue`. A manifest-absent target is therefore dropped BEFORE `classify_paths` types it, so admitting a non-plan target without touching this loop produces an expansion the gate silently cannot gate - the opposite of what spec :166 asks for.
3. GUARD THE QUEUE BUILDER. Its per-item first statement is an unguarded `manifest["plans"][id6]` that runs AFTER the run directory is created, so an id6 reaching it without an entry raises a bare KeyError with durable state already written, losing the no-durable-state property the refusal has.

`enforce_mixed_type_gate`'s docstring records points 1 and 2 inline, so the next reader meets them there too.
