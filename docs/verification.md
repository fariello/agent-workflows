# Verification

Verification decides whether a run is complete. The gates are deterministic and enforced by
`agent_workflows/verify_roles.py`, `run_gates.py`, and `run_evidence.py`.

## Role contracts

A role contract (`get_role_contract`) states, per role, what it may author and mutate. The
non-negotiable rules:

- An executor cannot author a verifier decision (no self-verification).
- Only the human role can record a human approval.
- Only the coordinator can author the terminal transaction.

Attempting a forbidden action raises a typed error (for example
`SelfVerificationForbiddenError`, `ProductMutationForbiddenError`, `TerminalAuthorityError`).

## Verifier packets

`build_verifier_packet` freezes what the verifier judges: the run id, the base and head
commits, the worktree path, the frozen requirements, the declared scope, and the actual diff.
The verifier reviews the packet in isolation (a fresh session or an independent subagent, never
a fork; see [orchestration.md](orchestration.md)). Executor prose leaking into a verifier packet
is detected (`ExecutorProseLeakError`).

## Completion predicates

`evaluate_completion` computes every predicate that must hold before a run finalizes: the
evidence is valid, each verifier decision was authored by the verifier role, no blocker or
correction is unresolved, and the coordinator holds terminal authority. `is_complete` is True
only when all predicates hold.

## Inspecting a verdict

```
aw runs show <run-id-or-path>
aw run finalize <run-id-or-path>
```

`aw runs show` prints the completion predicates and their state. `aw run finalize` records
terminal completion, and only the coordinator may do so.

## Responsibility boundary

The verifier judges independently of the executor. The coordinator finalizes. The human
approves. The runtime never grades its own homework.

## Limitations

- Verification proves the declared predicates hold. If a predicate is too weak, the run can pass
  while still being wrong; strengthen the predicate (see [authoring.md](authoring.md)).
