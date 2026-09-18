# IPD: Attention view and stranded lane drift performance optimization

- Date: 2026-09-17
- Kind: child
- Concern: performance
- Scope: agent_workflows/attention.py, agent_workflows/runner_shared.py, agent_workflows/worktree_lease.py
- Scope-Paths: agent_workflows/attention.py,agent_workflows/runner_shared.py,agent_workflows/worktree_lease.py,tests/test_attention.py,tests/test_worktree_lease.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: attperf (attention-performance)
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: 2hj0el

## Workflow history
- 2026-09-18 reviewed (aw set): /plan-review: approve with revisions applied; PR-001, PR-002, PR-003, PR-004, PR-005

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
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Scoped locally to a single `stranded_lane_drift()` invocation, guaranteeing zero stale-cache drift across distinct CLI invocations.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run `python3 -m pytest tests/test_worktree_lease.py -k test_registered_worktrees_memoized` and paste actual runner output showing `_git` worktree query is executed at most once per pass.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Run `python3 -m pytest tests/test_attention.py -k test_stranded_lane_terminal_pruning` and paste actual runner output proving cleanly terminal runs bypass live `inspect_lane` git invocations.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Run profile verification `python3 -c "import cProfile..."` and paste stats proving whole-document lowercasing is eliminated.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Run `python3 -m pytest tests/test_attention.py -k test_count_question_stats` and paste actual runner output verifying section boundary slicing returns identical counts.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Run timing benchmark `% time python3 -m agent_workflows.cli att` and paste actual terminal output proving unfiltered runtime drops below 3.0 seconds.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract:
- Human approval required: This plan must be human-approved (`Status: approved`) before execution and is not auto-run.
- Open questions: All open questions must be resolved before execution begins.
- Scope fence: The executor must touch only the paths declared in `Scope-Paths`. If a change outside the fence is genuinely required, make it and justify it with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. Do NOT stop and report for out-of-scope edits.
- Honesty rule: When reporting tests passed, paste the ACTUAL runner output; never claim success without running.
- Clean commits: Commit ONLY files modified for this task, path-scoped (`git commit -m msg -- <paths>`), and NEVER push.
- Post-gate move: Move to `.aw/records/plans/executed/` via `aw ipd finalize` once lint passes and all validation items are verified with concrete pasted evidence.
