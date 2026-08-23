# agent-workflows documentation

This is the operator, author, and security documentation for the agent-workflows execution
runtime and host integration (awoptimize Orders 01-17). It describes the real system: exact
commands, their outputs, the limitations, and the responsibility boundaries between the tool,
the agent, and the human.

All host support and benchmark performance tables in these docs are GENERATED from their
evidence registries (the capability registry for support, the threshold policy for release
bars) so the documented prose can never claim more than the recorded evidence. See
`agent_workflows/docs_render.py`.

## Documents

- [Architecture](architecture.md): the layers, the data flow, and the module map.
- [Authoring workflows](authoring.md): how to write a workflow and its validation predicates.
- [Skill selection](skill-selection.md): how a host discovers and dispatches a workflow.
- [Orchestration and isolation](orchestration.md): roles, isolation modes, and concurrency.
- [Evidence layer](evidence.md): the run ledger, provenance envelopes, and redaction.
- [Verification](verification.md): role contracts, verifier packets, and completion gates.
- [Benchmark](benchmark.md): the seeded corpus, metrics, and release thresholds.
- [Host adapters](host-adapters.md): per-host adapters and the support table.
- [Model profiles](model-profiles.md): evidence-backed defaults, not universal claims.
- [Security](security.md): the hardened boundaries and their runbooks.
- [Troubleshooting](troubleshooting.md): diagnosing an incomplete or failed run.
- [Recovery and rollback](recovery.md): resuming, recovering, and rolling back safely.

## Operator walkthroughs

The walkthroughs reproduce a task end to end from a clean fixture, without reading
implementation internals:

- [Diagnose an incomplete run](walkthroughs/incomplete-run.md)
- [Inspect evidence](walkthroughs/evidence-inspection.md)
- [Run a host probe](walkthroughs/host-probe.md)
- [Recover an interrupted update](walkthroughs/recovery.md)
- [Roll back safely](walkthroughs/rollback.md)

## Responsibility boundaries (who is accountable for what)

- The TOOL enforces deterministic gates (schema, hash chain, role contracts, thresholds). It
  refuses fail-open: an unproven claim defaults to "unverified", not "supported".
- The AGENT performs the work inside the fence. It cannot self-verify, cannot mutate outside
  its declared scope, and cannot record human approval.
- The HUMAN grants approval, consents to destructive tools, and authorizes a release. No agent
  can synthesize a human decision.

## Limitations

- These docs cover the current-state system. A support claim is only as fresh as its evidence
  record; a stale record renders as "unverified", not "supported".
- The release-readiness review (see [recovery.md](recovery.md) and the release notes) produces
  a GO or NO-GO decision only. It never tags, publishes, deploys, or pushes.
