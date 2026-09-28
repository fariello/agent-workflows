# IPD: Require artifact type flag in aw partition and support backlog and specs

- Date: 2026-09-28
- Kind: child
- Concern: partition-typed-dispatch
- Scope: Make artifact type flag required in aw partition, supporting plans, backlog, and specs with type-specific candidate collection, status validation, runner action formatting, and chronological sorting
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, tests/test_partition.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Set: typepart
- Order: 1
- Highest E allocated: 05
- Author: Gabriele Fariello
- Id: j3rlrf
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved
- 2026-09-28 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; /plan-review (Codex/GPT-6); PR-001 through PR-005 fixed
- 2026-09-28 to-review (aw set): Restore tool-owned review transition after local commit hook rejected a manually replaced history line
- 2026-09-28 /plan-review (Codex/GPT-6): APPROVE WITH REVISIONS APPLIED; PR-001 through PR-005 fixed.

- 2026-09-28 to-review (Gabriele Fariello): author review-ready plan requiring artifact type in aw partition.
- 2026-09-28 draft (Gabriele Fariello): created.

## Goal

Extend `aw partition` to require an explicit artifact type (`-t, --type, --tree {plans,backlog,specs}`) and support backlog items and specs alongside plans. Validate status filters against the chosen artifact type's lifecycle, automatically emit type-appropriate runner action flags (`--action plan` for backlog items), and sort independent candidate items chronologically so that queue-drain partitioning (such as partitioning the 100 oldest backlog items into two shards) produces balanced, runnable graduation commands.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: CLI Type Requirement and Action Flag

- [ ] E-01 Add required `-t, --type, --tree` flag and optional `--action` and `--order-by` flags to `partition` CLI in `agent_workflows/cli.py`.
  - Require `-t, --type, --tree` with choices `plans`, `backlog`, `specs` (or canonicalize via `status_set.canonical_type`). Refuse invocations without `-t` with exit code 2 and a clear error message.
  - Add optional `--action` flag with choices `execute`, `plan`, `review` (defaulting to None for automatic derivation).
  - Add optional `-o, --order-by` with choices `depth`, `date`; default to `depth` for plans and `date` for backlog/specs. Preserve dependency-first order in either mode.
  - Update command description, help text, and examples to illustrate `-t plans`, `-t backlog`, and `-t specs`.
  - Depends on: none
  - Expected outcome: `aw partition` requires `-t` and parses typed flags and options cleanly.
  - Execution state: pending

### Task group 2: Typed Candidate Collection and Status Filtering

- [ ] E-02 Update `collect()` in `agent_workflows/partition.py` to support `backlog`, `specs`, and `plans`.
  - Accept `artifact_type: str`. Scan candidate items via `_att.scan(repo_root, type_filters=(artifact_type,))`.
  - Validate requested statuses (`-s, --status`) against `status_set.TYPE_STATUSES[artifact_type]`, then select only items with a determinate, runnable next action under `run_selection_policy.action_for_status` (plus the plan orchestrator refinement where relevant). In particular, backlog `open` is plannable, `graduated`/`blocked`/`parked`/`done` are not; spec `to-review` is reviewable and `approved` plannable, while `reviewed`/`implementing`/terminal states are not directly dispatchable by this verb. Do not silently convert an ineligible explicitly selected item into a command.
  - Apply status and priority filters equally to scanned, positional-selector, and stdin candidates. Resolve selectors through `_selectors.resolve` with its kind/ambiguity verdict; refuse unknown, ambiguous, wrong-type, or ineligible explicitly selected IDs with exit 2 and a clear message. A broad scan may exclude ineligible items. Deduplicate IDs before partitioning.
  - Depends on: E-01
  - Expected outcome: `collect()` accurately discovers candidate items for the specified artifact type, validates status filters against that type, and handles stdin and selectors.
  - Execution state: pending

### Task group 3: Ordering and Command Formatting

- [ ] E-03 Implement candidate ordering and deterministic shard ordering in `agent_workflows/partition.py`.
  - Derive creation date from the artifact filename, using `attention._extract_identity_parts(it)[0]` or a small shared public helper; `Item` has no `date` field, and `attention`'s existing date sort is by most-recent history, not creation. For `--max N`, select by dependency depth first, then requested key (`date` ascending or `id6`); this yields the oldest independent backlog items. Missing/unparseable dates sort after valid dates with `id6` as a stable tie-breaker.
  - Pass the same key into `partition()` for component and within-shard ordering so oldest-first remains visible in emitted commands; retain dependency-first ordering and balanced packing. Make `in_selection_edges` recognize same-type in-selection dependencies rather than hardcoding IPD targets; do not split an ordinary backlog/spec dependency component unless capacity forces a reported cut.
  - Depends on: E-02
  - Expected outcome: `--max` takes the oldest eligible independent records and each shard lists them oldest-first without losing dependency safety.
  - Execution state: pending

- [ ] E-05 Format only legal, homogeneous runner actions for each invocation in `agent_workflows/partition.py`.
  - Derive each candidate's next action from `run_selection_policy.action_for_status`; an explicit `--action` constrains legality and never forces a transition. Since one generated command has one global action, refuse a selection mixing `review`, `plan`, and `execute` with exit 2 and advise filtering by `-s` or `--action`; do not emit a partial queue.
  - Include `--action plan` or `--action review` in both `aw oc/agy run` and `aw run as <profile>` formats; omit `--action execute` to preserve the existing default. `--run none` remains IDs-only and must be described as non-executable output.
  - Depends on: E-02
  - Expected outcome: Every emitted command is legal for every selected item, including homogeneous spec review and plan batches, with no silent skips or action mismatch.
  - Execution state: pending

### Task group 4: End-to-End Validation and Suite Pass

- [ ] E-04 Update existing partition tests, add typed backlog/spec test cases, and verify full suite pass.
  - Update existing tests in `tests/test_partition.py` to pass `-t plans`.
  - Add test cases in `tests/test_partition.py` covering:
    - Missing `-t/--type` exits 2 with required argument error.
    - Invalid status for type (e.g. `-t plans -s open`) exits 2 with clear explanation.
    - Backlog partitioning with `-t backlog -s open -n 2 --max 100` selects the oldest eligible 100, produces two balanced oldest-first shards, and emits `aw oc run --action plan ...`.
    - Specs `to-review` versus `approved` action, mixed-action refusal, explicit action legality, and profile formatting.
    - Stdin and positional resolution for each type, including status/priority filtering, wrong-type and ambiguous IDs, duplicate IDs, and non-runnable statuses.
    - Same-type dependency grouping and reported cuts, plus no regression in plan dependency ordering.
  - Run targeted tests via `python3 -m pytest tests/test_partition.py`.
  - Run pre-transition lint via `python3 -m agent_workflows ipd lint`.
  - Run full suite bare via `python3 -m pytest`.
  - Depends on: E-03, E-05
  - Expected outcome: All targeted tests and the full test suite pass cleanly without regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows.partition.collect`: Defined in `agent_workflows/partition.py` (line 231), candidate selection entry point.
- `agent_workflows.partition.format_shard`: Defined in `agent_workflows/partition.py` (line 197), constructs runner command strings.
- `agent_workflows.attention.scan`: Defined in `agent_workflows/attention.py`, cross-tree artifact scanner supporting `type_filters`.
- `agent_workflows.status_set.canonical_type`: Normalizes singular and plural type tokens (`plans`, `specs`, `backlog`).
- `agent_workflows.status_set.TYPE_STATUSES`: Dictionary of valid statuses per canonical type (`agent_workflows/status_set.py:41`).
- `agent_workflows.run_selection_policy.action_for_status`: Canonical status-to-action policy (`agent_workflows/run_selection_policy.py:333`).
- `agent_workflows.attention._extract_identity_parts`: Extracts creation date from artifact filename (`agent_workflows/attention.py:2493`); `Item` has no `date` field.

## Findings

1. `aw partition` was originally authored in plan `xu3yxw` specifically to partition `plans` and prevent cutting inter-plan dependency edges across concurrent runner queues.
2. In `agent_workflows/partition.py`, `collect()` hardcodes `type_filters=("plans",)` and filters non-terminal items via plan-only disposition helpers.
3. Attempting to partition backlog items via `aw partition -n 3 -s open` fails because plans do not have an `open` status (which belongs to backlog) and backlog records are ignored.
4. Runner dispatch for backlog items requires `--action plan` to graduate them into plans, whereas `format_shard` currently formats commands as `aw oc run <ids...>` (default action execute). The canonical action table marks only `open` backlog plannable and distinguishes spec `to-review` from `approved`.
5. `partition()` re-sorts each shard by `(depth, id6)`, so sorting only in `collect()` cannot produce oldest-first output. `in_selection_edges()` currently recognizes only IPD dependencies.
6. Requiring `-t, --type, --tree` makes the artifact type explicit, enables validation of status flags against the chosen type's native lifecycle, allows automatic action formatting, and supports chronological backlog ordering.

## Proposed changes (ordered, validatable)

1. Modify `agent_workflows/cli.py`: Add required `-t, --type, --tree` argument, optional `--action` argument, and optional `-o, --order-by` argument to `partition` subparser.
2. Modify `agent_workflows/partition.py`: Update `collect()` to accept and scan by `artifact_type`, validate status/action eligibility, resolve selectors safely, preserve dependency-first chronological ordering through partitioning, and format only homogeneous legal actions.
3. Modify `tests/test_partition.py`: Characterize existing plan behavior and cover typed candidate selection, oldest-first output, dependencies, action legality, all command formats, and failure paths using observable CLI output and exit codes.

## Deferred / out of scope (with reason)

Changing the greedy shard-capacity algorithm is out of scope. The existing balancing and cut reporting remain; typed dependency-edge recognition and deterministic output ordering are in scope because they are necessary for correct backlog/spec support.

## Scope check

- Over-scope: No changes to runner internals or other CLI verbs.
- Under-scope: None after review revisions; covers CLI parsing, candidate collection, action legality, dependency safety, ordering, formatting, and outcome tests.

## Required tests / validation

- Unit tests for CLI parsing (missing `-t`, invalid `-t`, valid flags).
- Unit tests for candidate collection across `plans`, `backlog`, and `specs` with status validation.
- Outcome tests for action flags in host and profile commands, homogeneous-action enforcement, selector failures, and oldest-first `--max` plus shard ordering.
- Targeted test run of `tests/test_partition.py`.
- Pre-transition lint check via `python3 -m agent_workflows ipd lint`.
- Bare full test suite pass via `python3 -m pytest`.

## Spec / documentation sync

Update `aw partition --help` description, argument help, and examples to document the required `-t/--type` flag.

## Open questions

### OQ-01: What should the default runner action be when `--action` is omitted?

- Blocking: no
- Status: resolved
- Owner: Codex/GPT-6
- Resolution or deferral rationale: Read-only policy probe on 2026-09-28 returned `backlog/open -> plan`, `backlog/graduated -> skip`, `spec/to-review -> review`, `spec/approved -> plan`, `spec/reviewed -> undetermined`, and `ipd/approved -> execute` via `run_selection_policy.action_for_status` (`agent_workflows/run_selection_policy.py:333`). Thus automatic action comes from each item's legal next action, and explicit `--action` is a legality constraint, not an override; a mixed-action invocation refuses before output.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted test output showing missing `-t` returns exit 2, invalid type returns exit 2, and valid flags are accepted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted CLI test output demonstrating candidate collection across `plans`, `backlog`, and `specs`; rejection of mismatched lifecycle statuses, wrong-type/ambiguous explicit selectors, and non-runnable explicit items; identical filter behavior for scan, selector, and stdin modes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted CLI test output demonstrating `--max` selects oldest eligible backlog items and command IDs remain oldest-first within each shard, with dependency grouping and cut reporting preserved.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted actual output from `python3 -m pytest tests/test_partition.py`, pre-transition lint report, and bare `python3 -m pytest` full suite run.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Pasted CLI test output showing backlog `plan`, spec `review`/`plan`, mixed-action and illegal explicit-action refusals (exit 2), and correct host/profile/IDs-only formatting.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: All open questions above are resolved. Scope fence: the declared implementation paths are `agent_workflows/partition.py`, `agent_workflows/cli.py`, and `tests/test_partition.py`; do not expand scope casually. If genuine work needs another path, make the edit and justify it during the two-way finalize scope reconciliation (`--scope-reason` for extra paths, `--scope-ack` for declared paths left unchanged). Paste the ACTUAL runner output whenever reporting tests passed; never claim a run that did not occur. Commit only files this task changed through path-scoped `aw commit j3rlrf -- <paths>`; verify the staged set and never push. After all E/V evidence is recorded and `aw ipd lint --phase pre-transition` conforms, the runner owns `aw ipd finalize` when executing under `aw oc run`/`aw agy run`; a direct executor uses `aw ipd finalize j3rlrf --actor <agent/model> --message <summary> --apply` to write the terminal status/history, move the plan, and commit. Never hand-move the plan or double-finalize. Publishing to `main` by hand, if authorized separately, uses `aw integration-lock -- git merge --ff-only <branch>` with the tip re-read inside the lock.
