# Recovery and rollback

This document covers resuming an interrupted run, recovering a corrupted ledger, and rolling
back an update safely. The modules are `agent_workflows/run_recovery.py` and
`compat_migration.py`.

## Resume an interrupted run

```
aw runs resume <run-id-or-path>
```

`resume` reconstructs the run state and reports the steps it can resume. It refuses to resume a
step whose side effect was interrupted (it will not silently re-apply a half-done mutation).
Under the hood `run_recovery.resume` and `plan_retry` decide what is safe to retry within the
retry budget.

## Recover a corrupted ledger

If `aw runs verify-ledger` reports a broken chain from an interrupted write,
`RunLedgerStore.recover` truncates the ledger to the last intact record. This preserves every
verified record and drops only the torn tail. It never rewrites history.

## Roll back an update

An update is reversible in two DISTINCT kinds, and the tool distinguishes them:

- An ADAPTER rollback reverts the generated set and runtime adapters to the last compatible
  state. It is fully reversible with no data loss (it reuses the journaled move-not-copy engine,
  so records move back, they are not deleted).
- A DATA-SCHEMA DOWNGRADE is when the older version cannot READ data written by the newer
  version (for example newer run-ledger records). This is NOT a safe adapter rollback. The tool
  WARNS and REFUSES it by default rather than corrupting the future data; the data is left
  intact.

`compat_migration.CompatRollback.assess` classifies the rollback and returns the warnings; only
a pure adapter rollback is `safe`. See the walkthrough
[walkthroughs/rollback.md](walkthroughs/rollback.md).

## Recover an interrupted update

`CompatRollback.recover_interrupted` reuses the migration manager's status and resume to drive a
partial migration to completion without record loss. A completed or absent transaction is a
no-op.

## Release readiness (decision only)

The final release-readiness review aggregates the gates into a GO or NO-GO verdict
(`agent_workflows/release_readiness.py`). It NEVER tags, publishes, deploys, or pushes; those are
separately authorized actions (see `RELEASING.md` and the release-review workflow). The review
runs the canonical leak scan and all IPD lint phases for real, checks the benchmark invariants,
the changelog and versioning, and the residual-risk sign-off, then emits the verdict. Reproduce
it:

```
python3 -m pytest tests/test_release_readiness.py -q
```

## Responsibility boundary

The tool resumes, recovers, and rolls back deterministically, and refuses an unsafe downgrade.
The human authorizes a release; the review only decides GO or NO-GO.

## Limitations

- A data-schema downgrade is refused, not performed, unless the operator explicitly opts in with
  full knowledge that the future data will be unreadable by the older version.
