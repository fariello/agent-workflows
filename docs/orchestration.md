# Orchestration and isolation

The orchestrator decides who does the work, how isolated they are, and when work may run in
parallel. The logic lives in `agent_workflows/orchestrate_isolation.py` and the role contracts
in `verify_roles.py`.

## Roles

The canonical roles are coordinator, executor, investigator, verifier, corrector, human, and
runtime. Each role has a contract (`verify_roles.get_role_contract`) that answers, deterministically:

- Can it mutate product code? Test code?
- Can it author a step attempt? A verifier decision? A terminal transaction?
- Can it record a human approval? Author a correction?

A verifier decision cannot be authored by the executor role. Only the human role can record a
human approval; no other role can synthesize one.

## Isolation modes

- `fresh_session`: a clean session (preferred for a verifier).
- `independent_subagent`: an isolated subagent (preferred where the host supports it).
- `fork`: allowed only for read-only side work that benefits from inherited context. A fork is
  strictly rejected for a verifier.
- `same_session_diagnostic`: a non-authoritative diagnostic only; it can never act as a
  completion gate.
- `two_process_fallback`: used on hosts without native subagents. A serializable handoff packet
  carries the run context between processes.

`resolve_isolation_mode` downgrades a requested mode to the two-process fallback when the host
lacks the capability.

## Concurrency

`analyze_concurrency_eligibility` parallelizes independent read-only investigations and
serializes mutations by default. Parallel mutation is allowed only with all of: separate
worktrees, disjoint file ownership, dependency independence, no shared generated files, and a
deterministic merge order with a serial fallback plan. Any conflict refuses parallel mutation
and falls back to the serial plan.

## Merge and revalidate

`execute_merge_and_revalidate_gate` never trusts a per-lane green result. It detects a stale
base, refuses unresolved conflict markers, refuses a file-ownership collision, enforces the
declared scope fence over the combined diff, and runs a FULL post-integration revalidation. A
timed-out lane is strictly a failure.

## Responsibility boundary

The coordinator owns the terminal transaction. A same-session audit is a diagnostic, not a
gate. The human authorizes; the runtime executes; the verifier judges independently.

## Limitations

- A host that lacks native subagents runs verification in a fresh session or via the
  two-process fallback, never as a same-session diagnostic.
