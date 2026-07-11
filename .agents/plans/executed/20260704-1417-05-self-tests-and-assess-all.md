# IPD: Framework self-tests + `assess-all` rollup

- Date: 2026-07-04
- Concern: meta-hardening (the framework should hold itself to its own standards) and
  cross-concern orchestration (avoid producing N disconnected IPDs).
- Scope: two related additions - automated tests for the framework's own Python tools,
  and an `assess-all` orchestration workflow.
- Status: EXECUTED 2026-07-04 (both parts A and B). See DECISIONS.md D36.

## Part A: Framework self-tests

### Goal
Add automated tests for the framework's own executable code (`install-workflows.py`,
`scan_secrets.py`, and any future `run_checks.py`), so changes are verified rather than
relying solely on manual dogfooding.

### Why
The toolkit preaches `assess-testing` and a verification/evidence layer (the verification-evidence-layer IPD), yet its
own tools have zero automated tests - a credibility gap. Every installer change so far
has been validated by hand. This is the framework failing its own bar.

### Proposed design
- A `tests/` directory with tests for the tools: installer (fresh install, idempotent
  re-run, prune of stale files, legacy migration, AGENTS-file discovery, executable-bit
  preservation, dry-run makes no changes); scanner (detects a planted secret in tree AND
  history, redacts output, respects bounds, PII rules). Use the stdlib (`unittest`) to
  keep zero dependencies, consistent with the tools themselves.
- A minimal test runner command documented in CONTRIBUTING, and (composing with the verification-evidence-layer IPD)
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

- Part A composes with the verification-evidence-layer IPD (verify runs the self-tests) and the toolkit-discovery IPD (version).
- Part B benefits from the command-surface-redesign IPD (parameterized assess) and the verification-evidence-layer IPD (so the rollup can include
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

## Execution record (2026-07-04)

Open questions resolved by the human:
- Q1 (scope): build both parts now.
- Q3 (framework): stdlib unittest, zero dependencies.
- Q2 (assess-all default): confirm scope + cost first; default a sensible set; user picks
  all/group/subset; never silently run everything.
- Surface: assess-all is its own command reusing the lenses as the single source of truth.

Changes (A): `tests/` (support.py + test_installer.py + test_scan_secrets.py +
test_run_checks.py), 25 stdlib-unittest tests covering installer/scanner/run_checks;
CONTRIBUTING Self-tests section. Changes (B): `assess-all/assess-all.md` orchestration;
`assess-all` manifest row; installer `CATALOG_PREFIX_EXCEPTIONS = {"assess-all"}` so it
gets a shim despite the assess- prefix (with a self-test); README + index.md prose;
DECISIONS D36. Verified: all 25 tests pass and FAIL when a tool is deliberately broken
(neutered denylist -> denylist test failed; restored -> green); fresh install -> 14
shims/tool (adds assess-all). Dogfooded on this repo. Scope held (test mechanical tools
not prose; assess-all orchestrates, never redefines concerns).
