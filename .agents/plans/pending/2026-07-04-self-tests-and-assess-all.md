# IPD: Framework self-tests + `assess-all` rollup

- Date: 2026-07-04
- Concern: meta-hardening (the framework should hold itself to its own standards) and
  cross-concern orchestration (avoid producing N disconnected IPDs).
- Scope: two related additions - automated tests for the framework's own Python tools,
  and an `assess-all` orchestration workflow.
- Status: PENDING (proposal for human approval; not executed)

## Part A: Framework self-tests

### Goal
Add automated tests for the framework's own executable code (`install-workflows.py`,
`scan_secrets.py`, and any future `run_checks.py`), so changes are verified rather than
relying solely on manual dogfooding.

### Why
The toolkit preaches `assess-testing` and a verification/evidence layer (IPD 3), yet its
own tools have zero automated tests - a credibility gap. Every installer change so far
has been validated by hand. This is the framework failing its own bar.

### Proposed design
- A `tests/` directory with tests for the tools: installer (fresh install, idempotent
  re-run, prune of stale files, legacy migration, AGENTS-file discovery, executable-bit
  preservation, dry-run makes no changes); scanner (detects a planted secret in tree AND
  history, redacts output, respects bounds, PII rules). Use the stdlib (`unittest`) to
  keep zero dependencies, consistent with the tools themselves.
- A minimal test runner command documented in CONTRIBUTING, and (composing with IPD 3)
  the framework's own `verify` should run these.
- Scope guard: test the mechanical tools, not the instruction prose (prose is reviewed
  by the assess/prose lenses, not unit-tested).

## Part B: `assess-all` rollup orchestration

### Goal
Run the assess family (all or a chosen subset) and produce ONE prioritized,
cross-concern plan, instead of 34 separate IPDs the user must reconcile by hand.

### Why
Running each assess concern separately yields many IPDs with overlapping and sometimes
conflicting findings and no cross-concern prioritization. A rollup gives a single "here
is the state of this repo across all concerns, prioritized" view - much more useful for
a real release decision, and a natural companion to `release-review`.

### Proposed design
- An `assess-all` workflow that runs the selected lenses (default: all; or a group like
  "security" or "docs"), then SYNTHESIZES: dedupes overlapping findings, resolves
  cross-concern priority (a Blocker security finding outranks a Low prose nit), and
  emits one consolidated IPD plus a rollup run record, with links to any per-concern run
  records.
- Reuses the assess harness per lens; the new part is the synthesis/prioritization
  layer. Honest about cost (running many lenses is expensive) and offers subset/group
  selection.
- Relationship to `release-review`: `release-review` is the broad fix-in-place review;
  `assess-all` is the broad propose-a-plan review. Cross-reference, do not duplicate.

## Scope check

- Over-scope (A): do not attempt to unit-test the instruction bodies or the LLM behavior;
  test only deterministic tool code. Over-scope (B): assess-all is orchestration, not a
  new concern; it must not become a second place that defines concerns (the lenses stay
  the source of truth).
- Under-scope: self-tests must cover the migration/prune paths (highest-risk installer
  behavior), not just the happy path.

## Dependencies / sequencing

- Part A composes with IPD 3 (verify runs the self-tests) and IPD 2 (version).
- Part B benefits from IPD 1 (parameterized assess) and IPD 3 (so the rollup can include
  verification evidence). Lower priority than the trust/usability IPDs.

## Required validation

- Self-tests pass on the current tools and fail when a tool is deliberately broken.
- `assess-all` on a repo produces one coherent, de-duplicated, cross-prioritized IPD and
  a rollup record; subset/group selection works.

## Open questions

1. Split A and B into separate execution IPDs? (They are independent; A is
   meta-hardening, B is a feature.)
2. `assess-all` default: run everything (expensive) or require a group/subset?
3. Test framework: stdlib `unittest` (zero deps, recommended) vs. pytest (nicer, adds a
   dev dependency).

## Approval and execution gate

Proposal only. Part A (self-tests) is low-risk meta-hardening and a good early build;
Part B (assess-all) is a larger feature best done after the parameterized-assess and
verification IPDs. Approve/reorder before execution.
