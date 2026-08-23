# Walkthrough: recover an interrupted update

Goal: from a clean state, produce a genuinely interrupted update and recover it to completion
without record loss.

## Reproduce in an isolated fixture

The `interrupted-update` lifecycle fixture creates a real interrupted migration (via the
migration engine's fault injection) in an isolated environment, then recovers it:

```
python3 -c "from agent_workflows import lifecycle_fixtures as lf; \
o = lf.run_fixture('interrupted-update'); \
print('interrupted then recovered:', o.passed); \
print('final state:', o.final_state); \
print('recover status:', o.evidence['recover_status'])"
```

Expected output: the update was interrupted, recovery reported `recovered` (or `completed`), and
the final state is no longer PARTIAL. No records were lost: the migration engine moves records
back rather than deleting them.

## The corresponding operator commands

Against a real run and repo, the same recovery is driven by:

```
aw run resume <run-id-or-path>
```

`resume` refuses to resume a step whose side effect was interrupted, so it never silently
re-applies a half-done mutation.

## What this proves

A green implementation suite does not by itself prove clean recovery. This walkthrough exercises
a real interrupted starting state and shows the recovery path completing it safely.
