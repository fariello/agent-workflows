# IPD: Attention view and stranded lane drift performance optimization

- Date: 2026-09-17
- Kind: child
- Concern: performance
- Scope: agent_workflows/attention.py, agent_workflows/runner_shared.py, agent_workflows/worktree_lease.py
- Scope-Paths: agent_workflows/attention.py,agent_workflows/runner_shared.py,agent_workflows/worktree_lease.py,tests/test_attention.py
- Item-Dependencies: none
- Status: to-review
- Set: attperf (attention-performance)
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: 2hj0el

## Workflow history

- 2026-09-17 to-review (Antigravity): /assess performance: assessed; proposed 5 changes.

## Goal

Optimize the performance of unfiltered `aw attention` and cross-tree artifact scanning, reducing runtime by 60-70% by eliminating ~1,000 redundant git subprocess calls in `stranded_lane_drift`, memoizing worktree registration, avoiding whole-document lowercasing, and section-slicing question parsing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Stranded lane inspection memoization and pruning

- [ ] E-01 Memoize worktree registration within `stranded_lane_drift` and `worktree_lease` so `git worktree list` is called at most once per sweep.
  - Depends on: none
  - Expected outcome: `_registered_worktrees` runs at most once during an attention pass instead of 176 times.
  - Execution state: pending
- [ ] E-02 Prune live git status and branch checks for historical runs whose items are already recorded terminal with no preserved worktrees.
  - Depends on: none
  - Expected outcome: Runs without active or preserved lanes bypass live `inspect_lane` probes.
  - Execution state: pending

### Task group 2: Document scan and parsing efficiency

- [ ] E-03 Eliminate whole-document `text.lower()` calls across artifact scanning loops, restricting caseless checks to header slices.
  - Depends on: none
  - Expected outcome: `str.lower()` allocations drop significantly in document scanning.
  - Execution state: pending
- [ ] E-04 Update `count_question_stats` to locate the `## Open questions` section boundary and slice only that section before splitting lines.
  - Depends on: none
  - Expected outcome: Full-document line splitting is avoided during question counting.
  - Execution state: pending

### Task group 3: Release metadata memoization and benchmarks

- [ ] E-05 Memoize planned release lookup during `matches_blocking` and sort key evaluation, and add performance regression benchmarks.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: Release descriptor is parsed once per pass and regression benchmark passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Clustered plan naming `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` in `.aw/records/plans/pending/`.
- Deterministic read-only execution: `aw attention` never writes state or touches git working copies.
- Profiling-backed optimization: all performance improvements must be verified by `cProfile` and timing benchmarks.

## Findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| P-01 | High | Low (complexity) | Architect | Unmemoized git subprocess loop in `stranded_lane_drift` executes ~1000 git calls on unfiltered `aw attention` taking 6.0s |
| P-02 | Medium | Low (complexity) | Software engineer | Whole-file string lowercasing repeated 8000+ times across scan loops generates tens of megabytes of ephemeral string churn |
| P-03 | Medium | Low (complexity) | Software engineer | `count_question_stats` splits entire document into lines even when open questions section is small or absent |
| P-04 | Medium | Low (complexity) | Software engineer | Unmemoized disk parsing of planned release metadata during filter evaluation and sorting |
| P-05 | Low | Low (complexity) | Power user | Eager argparse option registration across 100+ subcommands in 12,000-line `cli.py` costs ~0.55s on startup |

## Proposed changes (ordered, validatable)

1. Add worktree cache parameter to `stranded_lane_records` and `_registered_worktrees` (Low Remediation Risk).
2. Skip live git probes for cleanly finished historical runs (Low Remediation Risk).
3. Restrict caseless checks to header regions (Low Remediation Risk).
4. Boundary-slice open questions section in `count_question_stats` (Low Remediation Risk).
5. Memoize planned release descriptor during filter evaluation (Low Remediation Risk).

## Deferred / out of scope (with reason)

- P-05 (CLI parser eager option registration): Deferred to a broader CLI framework optimization pass because refactoring all 100+ subcommands carries wider surface area across the package.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Bare test suite: `python3 -m pytest`
- Targeted tests: `python3 -m pytest tests/test_attention.py tests/test_worktree_lease.py`
- Timing benchmark: unfiltered `aw attention` wall-clock execution time under 3 seconds.

## Spec / documentation sync

- N/A. Preserves existing attention view contracts and specifications.

## Open questions

### OQ-01: Cache lifetime for worktree registration

- Blocking: no
- Status: open
- Owner: Antigravity
- Resolution or deferral rationale: A local cache dictionary scoped to a single `stranded_lane_drift()` invocation guarantees zero stale-cache drift across multiple CLI commands.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Test confirms `git worktree list` is called at most once during `stranded_lane_drift`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Test confirms completed runs without preserved worktrees do not invoke git status.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Profile shows reduction in `str.lower` call count during artifact scan.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Test confirms `count_question_stats` returns identical unresolved and resolved counts.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Benchmark confirms unfiltered `aw att` runtime drops below 3.0 seconds.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must be human-approved before execution and is not auto-run.
