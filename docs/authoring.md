# Authoring workflows

A workflow is authored once in a host-neutral form and compiled into per-host adapters. This
document covers what a workflow declares and how its validation predicates work.

## What a workflow declares

- A command name (for example `assess`) and a body path (the canonical instruction).
- A human-readable description and an optional argument hint.
- MUST requirements: the falsifiable conditions the work is judged against.
- Validation predicates: deterministic checks that decide whether a step is complete.
- A scope fence: the paths a step is permitted to touch.

The compiler produces a SEMANTIC view of the workflow whose digest is stable
(`agent_workflows/workflow_compiler.py`). A profile may change transport knobs but not this
digest; the semantic-parity check (`workflow_profile.check_parity`) proves it.

## Profiles tune transport, never semantics

A profile (`workflow_profile.py`) may set only these keys: `name`, `max_packet_chars`,
`output_format`, `reasoning_level`, `verifier_policy`. Any other key is rejected. The reasoning
tier must be one of `low`, `medium`, `high`, `max`, and it is evidence-backed by the benchmark
(see [benchmark.md](benchmark.md)). A profile can never widen or drop the scope fence.

## Validation predicates must be falsifiable

A validation predicate asserts a concrete, checkable fact: a test ran and passed, a file
exists, a digest matches. "Looks done" is not a predicate. The completion evaluator
(`run_evidence.evaluate_completion`) refuses to mark a run complete unless every predicate
holds and the evidence is present, unredacted where required, and authored by the right role.

## Responsibility boundary

The author decides WHAT must be true. The runtime decides WHETHER it is true, deterministically.
The author cannot relax a gate by wording; a predicate either holds against the evidence or it
does not.

## Limitations

- A workflow body is host-neutral prose plus a canonical digest. It does not embed host-specific
  transport; that is the adapter's job (see [host-adapters.md](host-adapters.md)).
- Authoritative runtime behavior must never live only in a skill router's prose. The router
  points at the canonical body via a digest; it does not inline it (see
  [skill-selection.md](skill-selection.md)).
