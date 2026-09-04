# Exec Set (autonomous IPD Set execution)

Treat this file as a THIN entry point. The authoritative behavior lives in the deterministic runtime
(`aw ipd execute-set` and the Set coordinator), never in this prose. This workflow tells an agent or
human how to invoke that runtime, inspect it, answer a deferred question, and resume - without reading
the implementation.

`/exec-set` runs every approved, runnable child of an IPD Set with maximal SAFE parallelism, routes
each lane to the right model role, integrates results deterministically, and asks a human only under
the exact two-part stop rule. Planning is mandatory inside execution; `--plan-only` inspects the
compiled plan without launching a worker.

## Invocation

    /exec-set <set-id> [--plan-only]

or, explicitly (always available, in any agent):

    aw ipd execute-set <set-id> [--plan-only] [--resume <run-id>]

`--plan-only` compiles the Set into its execution manifest and prints the waves, serial fallbacks,
ownership, and model-role assignments; it launches no worker. `--resume <run-id>` reconstructs a
prior run's state and continues it without replaying completed side effects.

## What it does (authority stays in the runtime)

1. Compile the approved Set into a validated cross-IPD dependency graph and an immutable execution
   manifest (Order 01). Uncertain ownership serializes; an unapproved child is a deferred gate that
   blocks only its descendants.
2. Schedule the maximal provably-safe wave via the concurrency analyzer (Order 03); every node
   reaches a recorded disposition (running / deferred / serialized / blocked) - none is silently
   ignored.
3. Launch each write lane in an isolated git worktree with a fresh session and a per-path exclusive
   lease (Orders 03-04); a worker never writes coordinator-owned surfaces. A host capability is used
   only with current positive probe evidence, else a safe fallback or explicit refusal.
4. Record every autonomous decision, deferred question, and skip in the run ledger and durable
   projections (Order 02). A worker mutation is permitted only after the coordinator records an
   authorization.
5. Integrate returned path-scoped commits through the merge-and-revalidate gate; revalidate on the
   COMBINED HEAD (per-lane green never implies integrated green).
6. Stop the whole Set ONLY when `needs_human AND no_robust_decision AND cannot_defer_subgraph AND
   cannot_defer_ipd`, evaluated after draining independent work. A child's `STOP and report` returns
   control to the coordinator; it never terminates the Set (single-IPD execution is unchanged).

## Inspecting, answering, and resuming a run

- Run status:            `aw runs status <run-id>`
- Autonomous decisions:  `aw runs decisions <run-id>`
- Unresolved questions:  `aw runs questions <run-id>`
- Resume after an answer: `aw ipd execute-set --resume <run-id>`

An unresolved question is also promoted to an attention-visible blocked backlog item
(`Gate-Kind: decision`); answering it lets the run resume. Deferred work produces a PARTIAL result and
a durable walkthrough; a partial Set is NEVER reported complete.

## The final report

The report begins with completed / deferred / failed / remaining tables, lists the decisions and the
open questions, states whether combined-HEAD validation passed, and never calls a partial Set
complete. Treat any agent-authored "complete" as a claim that must agree with the ledger + lifecycle
state.

## What this workflow is not

- It never approves a plan or a spec (human approval is a separate, prior step) and never launches a
  worker in `--plan-only` mode.
- It never pushes, tags, publishes, deploys, or releases; those remain separate, explicitly approved
  gates.
