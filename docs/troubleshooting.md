# Troubleshooting

This document covers diagnosing a run that did not finish or did not pass. Every command here is
read-only and makes no writes.

## An incomplete run

Symptom: a run started but never reported complete.

1. Reconstruct the state from the ledger:

   ```
   aw runs status <run-id-or-path>
   ```

   This reports the reconstructed run and step state.

2. See which steps are runnable and which are blocked:

   ```
   aw runs show <run-id-or-path>
   ```

   The completion predicates show exactly which condition is not yet met (for example a
   verifier decision is missing, or a blocker is unresolved).

3. Check the evidence for the last step:

   ```
   aw runs evidence <run-id-or-path>
   ```

## A ledger that will not verify

Symptom: `aw runs verify-ledger` reports a broken chain or a sequence gap.

```
aw runs verify-ledger <run-id-or-path>
```

A broken link or a gap means a write was interrupted or the file was edited. Recovery truncates
the ledger to the last intact record; see [recovery.md](recovery.md).

## A capability shows unverified when you expected supported

This is by design when the evidence is missing, unproven, or expired. Render the support table
to see the reason (each unverified cell carries its reason in the registry). Re-run the host
probe to promote the capability with fresh evidence (see
[walkthroughs/host-probe.md](walkthroughs/host-probe.md)).

## A doc check fails

Run the documentation checks:

```
python3 -c "from agent_workflows import docs_check as c; from pathlib import Path; \
[print(f) for f in c.check_docs_dir(Path('docs'))]"
```

A finding names the file, the line, the check, and the message (a broken link, an unknown
`aw` subcommand, or an em/en dash in user-facing prose).

## Responsibility boundary

Diagnosis is read-only. Nothing here mutates the run, the ledger, or the repo. Recovery actions
are separate and documented in [recovery.md](recovery.md).

## Limitations

- The tools report WHAT is wrong deterministically. Deciding the fix, and applying it, is the
  operator's or the agent's job within the fence.
