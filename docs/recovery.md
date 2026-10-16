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
Under the hood, `run_recovery.resume` inspects the ledger to determine which steps are safe to resume and reports any interrupted steps that require reconciliation; it does not evaluate or spend a retry budget on this path (`plan_retry` has no production callers today). Driver runs use their own retry substrate.

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
runs the canonical leak scan and all IPD lint phases for real, checks generated workflow drift,
documentation checks, workflow dispositions, capability freshness, benchmark invariants, the
changelog and versioning, the workflow artifact manifest, and the residual-risk sign-off, then
emits the verdict.

A gate whose input is absent (no `docs/`, no host matrix, no canonical `workflow.yaml` packages,
no workflow manifest, no `CHANGELOG.md`) is reported NOT-APPLICABLE, is never counted as passed,
does not force `NO-GO`, and is named in a WARNING line and as warning diagnostics. The `full_suite`
and `residual_risk` gates are never not-applicable. The accepted risk is that an input deleted by
mistake reads not-applicable, so review the WARNING line.

Run the read-only report from the CLI:

```
aw releases readiness --suite-passed --residual-risk-signer <name>
```

The command never runs the full test suite itself and never invents human attestations:

- `--suite-passed` / `--suite-failed` (mutually exclusive): attests the outcome of a real full
  test suite run. If neither flag is passed, the `full_suite` gate fails with `full suite result
  not supplied` rather than claiming a red suite that was not run.
- `--residual-risk-signer NAME`: attests the human residual-risk sign-off. Without a signer, the
  `residual_risk` gate fails with `residual-risk sign-off missing`.
- `--agent` / `--json`: emits a canonical `aw.agent/v1` result record or structured JSON.

Exit codes are `0` on `GO`, `1` on `NO-GO`, and `2` when the command cannot run (such as a
non-project `--dir` or conflicting flags). The `artifact_manifest` row checks
`.aw/system/workflows/index.md` presence and consistency on disk.

## Responsibility boundary

The tool resumes, recovers, and rolls back deterministically, and refuses an unsafe downgrade.
The human authorizes a release; the review only decides GO or NO-GO.

## Limitations

- A data-schema downgrade is refused, not performed, unless the operator explicitly opts in with
  full knowledge that the future data will be unreadable by the older version.
