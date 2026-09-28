# IPD: Require artifact type flag in aw partition and support backlog and specs

- Date: 2026-09-28
- Kind: child
- Concern: partition-typed-dispatch
- Scope: Make artifact type flag required in aw partition, supporting plans, backlog, and specs with type-specific candidate collection, status validation, runner action formatting, and chronological sorting
- Scope-Paths: agent_workflows/partition.py, agent_workflows/cli.py, tests/test_partition.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: high
- Set: typepart
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: j3rlrf

## Workflow history

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
  - Add optional `-o, --order-by` flag with choices `depth`, `date`, `priority`, `id6`.
  - Update command description, help text, and examples to illustrate `-t plans`, `-t backlog`, and `-t specs`.
  - Depends on: none
  - Expected outcome: `aw partition` requires `-t` and parses typed flags and options cleanly.
  - Execution state: pending

### Task group 2: Typed Candidate Collection and Status Filtering

- [ ] E-02 Update `collect()` in `agent_workflows/partition.py` to support `backlog`, `specs`, and `plans`.
  - Accept `artifact_type: str`. Scan candidate items via `_att.scan(repo_root, type_filters=(artifact_type,))`.
  - Filter terminal items according to artifact type: for `plans`, exclude terminal dirs (`DIR_TERMINAL`); for `backlog`, exclude status `done`; for `specs`, exclude status `implemented`.
  - Validate requested statuses (`-s, --status`) against `status_set.VALID_STATUSES[artifact_type]`. If a status is outside the valid vocabulary for that artifact type (e.g. `-t plans -s open`), refuse with exit 2 and an attributable error message explaining that the status does not belong to the selected artifact type.
  - In stdin mode (`--stdin`), resolve IDs against `artifact_type` and report unknown or non-matching IDs on stderr.
  - For positional selectors, resolve against `artifact_type` via `_selectors.resolve_selectors(repo_root, artifact_type, list(selectors))`.
  - Depends on: E-01
  - Expected outcome: `collect()` accurately discovers candidate items for the specified artifact type, validates status filters against that type, and handles stdin and selectors.
  - Execution state: pending

### Task group 3: Ordering and Command Formatting

- [ ] E-03 Implement chronological backlog ordering and automatic runner action formatting in `agent_workflows/partition.py`.
  - When candidates are truncated with `--max N` (or ordered within a component), sort by:
    - If `order_by == "date"`: `(it.date or "", it.id)`
    - If `order_by == "depth"` or default: `(depths.get(it.id, 0), it.date or "", it.id)`. For backlog items, dependency depth is 0, so candidate truncation naturally selects the oldest items by date ascending.
  - Update `format_shard` to accept `action: Optional[str] = None`.
  - Determine default action when `args.action` is not provided:
    - For `backlog`: default action is `plan` (producing `aw oc run --action plan <ids...>`).
    - For `plans`: default action is `execute` (producing `aw oc run <ids...>`).
    - For `specs`: default action is `plan` (or `review` if status is `to-review`).
  - Pass the resolved action to `format_shard` and include `--action <action>` in the formatted command when action is not `execute`.
  - Depends on: E-02
  - Expected outcome: Backlog items without dependencies partition into balanced shards ordered chronologically, generating ready-to-run graduation commands with `--action plan`.
  - Execution state: pending

### Task group 4: End-to-End Validation and Suite Pass

- [ ] E-04 Update existing partition tests, add typed backlog/spec test cases, and verify full suite pass.
  - Update existing tests in `tests/test_partition.py` to pass `-t plans`.
  - Add test cases in `tests/test_partition.py` covering:
    - Missing `-t/--type` exits 2 with required argument error.
    - Invalid status for type (e.g. `-t plans -s open`) exits 2 with clear explanation.
    - Backlog partitioning with `-t backlog -s open -n 2 --max 100` produces two balanced shards with `aw oc run --action plan ...`.
    - Stdin resolution for backlog items.
  - Run targeted tests via `python3 -m pytest tests/test_partition.py`.
  - Run pre-transition lint via `python3 -m agent_workflows ipd lint`.
  - Run full suite bare via `python3 -m pytest`.
  - Depends on: E-03
  - Expected outcome: All targeted tests and the full test suite pass cleanly without regressions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows.partition.collect`: Defined in `agent_workflows/partition.py` (line 231), candidate selection entry point.
- `agent_workflows.partition.format_shard`: Defined in `agent_workflows/partition.py` (line 197), constructs runner command strings.
- `agent_workflows.attention.scan`: Defined in `agent_workflows/attention.py`, cross-tree artifact scanner supporting `type_filters`.
- `agent_workflows.status_set.canonical_type`: Normalizes singular and plural type tokens (`plans`, `specs`, `backlog`).
- `agent_workflows.status_set.VALID_STATUSES`: Dictionary of valid statuses per canonical type.

## Findings

1. `aw partition` was originally authored in plan `xu3yxw` specifically to partition `plans` and prevent cutting inter-plan dependency edges across concurrent runner queues.
2. In `agent_workflows/partition.py`, `collect()` hardcodes `type_filters=("plans",)` and filters non-terminal items via plan-only disposition helpers.
3. Attempting to partition backlog items via `aw partition -n 3 -s open` fails because plans do not have an `open` status (which belongs to backlog) and backlog records are ignored.
4. Runner dispatch for backlog items requires `--action plan` to graduate them into plans, whereas `format_shard` currently formats commands as `aw oc run <ids...>` (default action execute).
5. Requiring `-t, --type, --tree` makes the artifact type explicit, enables validation of status flags against the chosen type's native lifecycle, allows automatic action formatting, and supports chronological backlog ordering.

## Proposed changes (ordered, validatable)

1. Modify `agent_workflows/cli.py`: Add required `-t, --type, --tree` argument, optional `--action` argument, and optional `-o, --order-by` argument to `partition` subparser.
2. Modify `agent_workflows/partition.py`: Update `collect()` to accept and scan by `artifact_type`, validate status filters, update candidate sorting with chronological date tie-breaking, and update `format_shard()` to emit `--action`.
3. Modify `tests/test_partition.py`: Update existing test invocations to pass `-t plans` and add test coverage for missing `-t`, status validation, backlog partitioning with `--action plan`, and stdin resolution.

## Deferred / out of scope (with reason)

Modifying the graph packing algorithm (`in_selection_edges`, `components`, `partition`) is out of scope: independent items (such as backlog items) already pack as singleton components with balanced greedy capacity, which is mathematically optimal for non-dependent items.

## Scope check

- Over-scope: No changes to runner internals or other CLI verbs.
- Under-scope: None; covers CLI parsing, candidate collection, status validation, command formatting, and tests.

## Required tests / validation

- Unit tests for CLI parsing (missing `-t`, invalid `-t`, valid flags).
- Unit tests for candidate collection across `plans`, `backlog`, and `specs` with status validation.
- Unit tests for command formatting with action flags.
- Targeted test run of `tests/test_partition.py`.
- Pre-transition lint check via `python3 -m agent_workflows ipd lint`.
- Bare full test suite pass via `python3 -m pytest`.

## Spec / documentation sync

Update `aw partition --help` description, argument help, and examples to document the required `-t/--type` flag.

## Open questions

### OQ-01: What should the default runner action be when `--action` is omitted?

- Blocking: no
- Status: resolved
- Owner: Gabriele Fariello
- Resolution or deferral rationale: When partitioning `backlog`, the runner action is `plan` (backlog graduation). When partitioning `plans`, the default is `execute`. When partitioning `specs`, `to-review` specs default to `review` while `approved` specs default to `plan`. An explicit `--action` flag overrides the default.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted test output showing missing `-t` returns exit 2, invalid type returns exit 2, and valid flags are accepted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted test output demonstrating candidate collection across `plans`, `backlog`, and `specs`, terminal exclusion per type, and status validation rejection of mismatched lifecycle statuses.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted test output demonstrating `--max` on backlog items selects oldest items by date, and `format_shard` outputs `--action plan` for backlog shards and `--action review` when specified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted actual output from `python3 -m pytest tests/test_partition.py`, pre-transition lint report, and bare `python3 -m pytest` full suite run.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: All open questions above are resolved. Scope fence: the declared implementation paths are `agent_workflows/partition.py`, `agent_workflows/cli.py`, and `tests/test_partition.py`; do not expand scope casually. If genuine work needs another path, make the edit and justify it during the two-way finalize scope reconciliation (`--scope-reason` for extra paths, `--scope-ack` for declared paths left unchanged). Paste the ACTUAL runner output whenever reporting tests passed; never claim a run that did not occur. Commit only files this task changed through path-scoped `aw commit j3rlrf -- <paths>`; verify the staged set and never push. After all E/V evidence is recorded and `aw ipd lint --phase pre-transition` conforms, the runner owns `aw ipd finalize` when executing under `aw oc run`/`aw agy run`; a direct executor uses `aw ipd finalize j3rlrf --actor <agent/model> --message <summary> --apply` to write the terminal status/history, move the plan, and commit. Never hand-move the plan or double-finalize. Publishing to `main` by hand, if authorized separately, uses `aw integration-lock -- git merge --ff-only <branch>` with the tip re-read inside the lock.
