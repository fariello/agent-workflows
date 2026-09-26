# IPD: Finalize xu3yxw and jfza7e through a runner with pasted evidence, and make the agent-record test assert validity

- Date: 2026-09-26
- Kind: child
- Concern: `/verify-execution` of `xu3yxw` + `jfza7e` (execution commits `309bc790`, `564fc488`) found the CODE now complete and green (bare suite `2489 passed, 2 skipped`; both mutation checks caught: a lexical within-shard sort fails `test_packing_oversized_component_split`, and dropping the `target_type == "ipd"` filter fails `test_in_selection_edges_mixed_type_fixture`; `aw partition -s approved --agent` emits one record that `agent_schema.validate_agent_record` accepts), but NEITHER PLAN IS EXECUTED. Both are still `- Status: approved` in `pending/`, no `aw ipd begin` receipt exists for either, and no `aw ipd finalize` ran, which is the lifecycle obligation `jfza7e`'s gate stated ("Plan `xu3yxw` must ALSO be finalized honestly: its `Observed evidence` blocks must be replaced with pasted output"). `xu3yxw`'s `Observed evidence` blocks are byte-identical to the paraphrased text flagged as F-6 (last touched in `309bc790`; zero code fences). One small test gap also remains: `test_cli_partition_agent_mode` calls `agent_schema.validate_agent_record(record)` and discards the returned error list, so it asserts nothing about validity (the function RETURNS errors, it does not raise; `render_jsonl_record` does raise, so production output is guarded, but the test would pass on an invalid record constructed any other way).
- Scope: IN: (a) make `test_cli_partition_agent_mode` assert `agent_schema.validate_agent_record(record) == []`; (b) replace `xu3yxw`'s six paraphrased `Observed evidence` blocks with pasted runner output re-derived at execution time; (c) finalize `xu3yxw` and `jfza7e` through the lifecycle. OUT: any change to `partition.py` behavior.
- Scope-Paths: tests/test_partition.py, .aw/records/plans/pending/20260926-partition-01-xu3yxw-add-aw-partition-command-to-cluster-dependent-plans-into-bal.ipd.md, .aw/records/plans/pending/20260926-partition-03-jfza7e-close-xu3yxw-execution-gaps-shared-edge-parser-dead-depth-fa.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: partition
- Order: 4
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: c8wjpi
- Approval: 2026-09-26, human ("approved"): Human approved in chat: 'Maybe you can execute it. Gemini reviewed. I approve it. Please go.'

## Workflow history
- 2026-09-26 approved (opencode/its_direct/pt3-claude-opus-5.5-1m-us, --by-human): Human approved in chat: 'Maybe you can execute it. Gemini reviewed. I approve it. Please go.'

- 2026-09-26 reviewed (antigravity): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed. Readiness GO - PENDING HUMAN APPROVAL.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Emitted by /verify-execution of xu3yxw + jfza7e; verdict INCOMPLETE (code complete and green, lifecycle not performed). Run record .aw/workflow-artifacts/verify-execution/20260926-183632/.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Both `xu3yxw` and `jfza7e` end in `executed/` through a real begin/finalize transaction, each with evidence a reader can re-check, and the agent-record test genuinely fails on an invalid record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the test gap

- [ ] E-01 In `tests/test_partition.py::test_cli_partition_agent_mode`, change the bare `agent_schema.validate_agent_record(record)` call to `assert agent_schema.validate_agent_record(record) == []`.
  - Depends on: none
  - Expected outcome: the test fails if the emitted record carries any schema error.
  - Execution state: pending

### Task group 2: honest evidence and the lifecycle

- [ ] E-02 Re-derive and PASTE `xu3yxw`'s evidence. For each of its V-01..V-06, run the command its `Required evidence` names against the CURRENT code (which includes `jfza7e`'s corrections) and replace the paraphrased `Observed evidence` with the literal command and output in a fenced block, sanitizing any machine-local home paths (e.g. `rootdir: <worktree-root>`) so the `local-leaks` hook does not reject the commit. Note on V-01, V-02 and V-06 that the passing output reflects the `jfza7e` corrections (commit `564fc488`) where the original implementation was deficient (including V-01's grep now matching line 59 due to `_parse_item_dependency_edge` usage). Do not tick or untick anything else.
  - Depends on: E-01
  - Expected outcome: every `xu3yxw` `Observed evidence` block contains a pasted command and its output without machine-local path leaks.
  - Execution state: pending

- [ ] E-03 Finalize both plans through the lifecycle, `xu3yxw` first, then `jfza7e`, each passing `aw ipd lint --phase pre-transition` before its transition. Because the code for both already sits on `feat/aw-partition`, begin and finalize are bookkeeping transactions over already-committed work; if the runner's scope reconciliation sees the earlier execution commits as out-of-window, justify with `--scope-reason` naming `309bc790` / `564fc488` rather than re-implementing. In `.aw/worktrees/feat-partition`, note that `AW-LIFECYCLE-ROLE-001` gates hand begin/finalize unless driven by a runner (`aw oc run` / `aw agy run`) or run with driver attestation, and `aw ipd begin` must precede `aw ipd finalize` to issue the matching receipt.
  - Depends on: E-02
  - Expected outcome: both plans are in `.aw/records/plans/executed/` with `- Status: executed` and a finalize history line.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_schema.validate_agent_record` RETURNS a list of error strings; `assert_valid_agent_record` raises; `render_jsonl_record` calls the raising form.
- In a managed lane worktree a non-runner `aw ipd finalize` refuses with `AW-LIFECYCLE-ROLE-001`, so the transition must be driven by `aw oc run` / `aw agy run` (or by a hand executor only where no runner owns the checkout).
- Behavioral tests only (maintainer ruling 2026-09-26); run bare `python3 -m pytest`, narrowed with `-o addopts=""`.

## Findings

Measured 2026-09-26 in the `feat/aw-partition` worktree at `564fc488`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | plans `xu3yxw`, `jfza7e` | Neither was begun or finalized; both still `approved` in `pending/`. | front matter `- Status: approved`; no receipt for either id6 under `.aw/state`; last `xu3yxw` commit `309bc790` |
| F-2 | HIGH | plan `xu3yxw` V-01..V-06 | Evidence still paraphrased, as flagged in F-6 of `jfza7e`. | zero code fences in the plan; V-06 "tests/test_partition.py passed 12 in 2.60s" |
| F-3 | LOW | `tests/test_partition.py::test_cli_partition_agent_mode` | Validity result discarded. | bare statement `agent_schema.validate_agent_record(record)` |

## Proposed changes (ordered, validatable)

1. E-01: assert the validator's result.
2. E-02: paste `xu3yxw`'s evidence.
3. E-03: finalize both plans.

## Deferred / out of scope (with reason)

No items deferred; all identified work is addressed in the implementation checklist.

## Scope check

- Over-scope: none.
- Under-scope: none; the lifecycle is included explicitly because it was the part of `jfza7e`'s gate that was not performed.

## Required tests / validation

- `python3 -m pytest tests/test_partition.py -o addopts=""`.
- Bare `python3 -m pytest`.
- `aw ipd lint --phase pre-transition` on both plans before finalize.

## Spec / documentation sync

None.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the changed assertion and the passing `test_cli_partition_agent_mode` output, then its FAILING output when the emitted record's `outcome` is temporarily set to an invalid value in the test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -c '```' <xu3yxw plan>` showing at least 12 fence lines (six fenced blocks), and one of the rewritten blocks verbatim.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep -E "xu3yxw|jfza7e"`, both plans' `- Status:` lines, and each plan's finalize history line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `/plan-review` and explicit human approval. Born `to-review` (D65): E-03 performs a lifecycle transaction on two other plans and may need scope justification, which is not purely mechanical.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the one test assertion and the two plan files named in `- Scope-Paths:`. An out-of-scope edit, if one proves necessary, is made and justified at finalize with `--scope-reason`; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every `Observed evidence` block pastes the ACTUAL command and output. Run the suite BARE as `python3 -m pytest`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). This plan's own terminal transition is `aw ipd finalize`: the runner owns it when this plan runs in a lane; a hand executor runs it only when no runner is driving.
