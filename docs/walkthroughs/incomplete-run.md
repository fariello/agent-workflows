# Walkthrough: diagnose an incomplete run

Goal: from a clean state, produce and diagnose an incomplete run without reading any
implementation internals.

## What you need

- A checkout of this repository.
- Python 3.9 or newer.

## Steps

1. Reconstruct a run's state from its ledger. Point the command at a run id or a ledger path:

   ```
   aw runs status <run-id-or-path>
   ```

   The output reports each step and its state (pending, runnable, running, done, blocked).

2. Show the completion predicates to see exactly why the run is not complete:

   ```
   aw runs show <run-id-or-path>
   ```

   Each predicate is listed with its state. A run is incomplete when any predicate is not met,
   for example a missing verifier decision or an unresolved blocker.

3. Inspect the evidence for the last recorded step:

   ```
   aw runs evidence <run-id-or-path>
   ```

## Expected result

You can name the single unmet predicate that is holding the run open, using only the read-only
commands above. Nothing you ran mutated the run or the repository.

## Reproduce the diagnosis logic in a fixture

The completion evaluator that these commands use is deterministic. You can drive it directly:

```
python3 -c "from agent_workflows import lifecycle_fixtures as lf; \
o = lf.run_fixture('partial-state'); \
print('final state:', o.final_state, '| passed:', o.passed)"
```

A `partial-state` fixture is a genuine interrupted migration detected as PARTIAL and then
resumed to completion; the printed final state is no longer PARTIAL after recovery.
