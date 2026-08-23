# Architecture

agent-workflows compiles portable, host-neutral workflows into per-host adapters, runs them
under a deterministic evidence-and-verification runtime, and gates release readiness. The
design goal is honest execution: "done" and "tests passed" mean what they say because the
gates are deterministic and the evidence is tamper-evident.

## Layers

1. Schema and compiler (`agent_workflows/workflow_schema.py`, `workflow_compiler.py`,
   `workflow_loader.py`, `workflow_source.py`). A workflow is authored once in a host-neutral
   form; the compiler produces a semantic view whose digest is stable across profiles.
2. Profiles (`workflow_profile.py`). A profile tunes TRANSPORT knobs only (packet size, output
   format, an evidence-backed reasoning tier). A profile never changes a workflow's semantics,
   its MUST requirements, its validation predicates, or its scope fence.
3. Runtime (`run_engine.py`, `run_state.py`, `run_freeze.py`, `run_packet.py`). The runtime
   drives a workflow's steps through a DAG, freezes the requirements a step is judged against,
   and packages a step packet for an actor.
4. Evidence and ledger (`run_evidence.py`, `run_ledger_store.py`, `run_ledger_schema.py`). Each
   step attempt lands a provenance envelope in an append-only, SHA-256 hash-chained ledger.
5. Verification and roles (`verify_roles.py`, `run_gates.py`). Role contracts decide who may
   mutate, who may verify, and who may finalize. A verifier decision cannot be authored by the
   executor role.
6. Isolation and orchestration (`orchestrate_isolation.py`). Isolation modes and a concurrency
   analyzer decide when work may run in parallel and how isolated lanes merge and revalidate.
7. Host integration (`host_capability_registry.py`, `host_adapters.py`). Capabilities are
   proven by live probes; adapters advertise a feature as supported only where the registry
   promoted it.
8. Benchmark (`benchmark_*.py`). A seeded corpus with hidden ground truth measures agent
   behavior; a threshold policy sets the release bar.
9. Compatibility (`compat_migration.py`). A previewable, idempotent migration/update with a
   rollback and an explicit data-schema-downgrade warning.

## Data flow (one run)

1. The host discovers a workflow (see [skill-selection.md](skill-selection.md)) and dispatches
   it to an actor with a specific role.
2. The runtime freezes the step requirements and issues a step packet.
3. The actor performs the step and records a step-attempt outcome plus a provenance envelope in
   the ledger.
4. A verifier (an isolated actor, never the executor) reviews a verifier packet and records a
   decision.
5. The coordinator computes the completion predicate; only when every predicate holds is the
   run finalized.

## Module map (where to look)

- Compiler and profiles: `workflow_compiler.py`, `workflow_profile.py`.
- Runtime and ledger: `run_engine.py`, `run_ledger_store.py`, `run_evidence.py`.
- Roles and gates: `verify_roles.py`, `run_gates.py`, `orchestrate_isolation.py`.
- Host integration: `host_capability_registry.py`, `host_adapters.py`.
- Benchmark: `benchmark_thresholds.py`, `benchmark_corpus.py`, `benchmark_reports.py`.
- Compatibility: `compat_migration.py`.
- Security hardening (Order 18): `security_hardening.py`.
- Docs generation and checks (Order 18): `docs_render.py`, `docs_check.py`.
- Release readiness (Order 18): `release_readiness.py`.

## Design invariants

- Fail closed. An unproven, missing, or expired claim defaults to "unverified", never
  "supported".
- Deterministic gates. The schema, the hash chain, the role contracts, and the thresholds are
  all checkable without a model or a network.
- No forked scanners. Leak and secret checks reuse the one canonical leak sanitizer and secret
  scanner (see [security.md](security.md)).
