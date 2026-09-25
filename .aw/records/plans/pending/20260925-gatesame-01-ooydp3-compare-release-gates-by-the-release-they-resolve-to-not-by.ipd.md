# IPD: Compare release gates by the release they resolve to, not by spelling

- Date: 2026-09-25
- Kind: child
- Concern: `check_engine` compares a backlog item's `Blocks-Release` with its handoff plan's by raw string, so `next` and the release id6 `next` resolves to are treated as different gates. That fires a false `check.from-backlog-gate-mismatch` and, worse, makes `evaluate_blocking_close` REFUSE a legitimate handoff close (reproduced in a scratch repo).
- Scope: IN: one shared helper in `check_engine.py` deciding whether two gate values denote the same release, used at the two comparison sites (`evaluate_blocking_close`'s HANDOFF branch and `check_release_gate_consistency`'s mismatch branch); tests. OUT: `check.blocks-release-dangling` (an unresolvable value stays that rule's job).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_release_gate.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: gatesame
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: ooydp3
- From-Backlog: 4le6yz
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog 4le6yz. Reproduced at HEAD in a scratch repo: item `next`, plan `f33nrj`, both resolving to the same release file, yields a gate-mismatch Drift AND `evaluate_blocking_close(...,'done')` -> legitimate=False. The live tree is quiet only because the two cited carriers have since executed.

## Goal

A gate written as `next` and the same gate written as the release's id6 are one gate everywhere the toolkit compares them.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: shared comparison

- [ ] E-01 Add `_same_release(repo_root, a, b) -> bool` in `check_engine.py`: True when the strings are equal, or when `releases.resolve_release(repo_root, a)` and `releases.resolve_release(repo_root, b)` both resolve and return the same path. If either does not resolve, fall back to string equality (the dangling case is `check.blocks-release-dangling`'s job, not this one's).
  - Depends on: none
  - Expected outcome: the helper exists and is pure apart from the release lookup.
  - Execution state: pending

- [ ] E-02 Use `_same_release` at both comparison sites: `evaluate_blocking_close`'s HANDOFF branch (the `carrier_br == blocks_release` test) and `check_release_gate_consistency`'s mismatch test (`carrier_br != item_br`). Resolve each release at most once per call, not once per carrier.
  - Depends on: E-01
  - Expected outcome: no raw string comparison of two gate values remains in those two functions.
  - Execution state: pending

### Task group 2: tests

- [ ] E-03 Add tests to `tests/test_check_engine_release_gate.py` building a scratch repo with one planned release record: (a) item `next` + open plan with `From-Backlog` and the release id6 -> no `check.from-backlog-gate-mismatch`; (b) same pair -> `evaluate_blocking_close(..., 'done')` is legitimate with basis `HANDOFF`; (c) plan naming a DIFFERENT release id6 -> mismatch still reported.
  - Depends on: E-02
  - Expected outcome: all three pass; (a) and (b) fail against the pre-change comparison.
  - Execution state: pending

- [ ] E-04 Run the bare suite and `python3 -m agent_workflows check release-gates --agent` on the real tree.
  - Depends on: E-03
  - Expected outcome: suite green; release-gates still conforms.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `releases.resolve_release(repo_root, value)` is the one resolver for a `Blocks-Release` value (`next` or an id6).
- `evaluate_blocking_close` is the ONE close-legitimacy predicate shared by the setter, `aw check` and the opt-in hook (AGENTS.md, Release gates), so fixing it there fixes every surface.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `check_engine.evaluate_blocking_close` | A legitimate handoff close is refused when the item says `next` and the plan says the id6. | scratch repo `/tmp/opencode/r4le`: `CloseVerdict(legitimate=False, ... 'would silently drop that release gate')` |
| F-2 | MED | `check_engine.check_release_gate_consistency` | Same spelling difference reported as `check.from-backlog-gate-mismatch`. | same scratch repo: one mismatch Drift |
| F-3 | INFO | live tree | Quiet today only because the cited carriers (`h90ij1`, `z1yefm`) are executed and terminal carriers are skipped. | `check release-gates` -> 0 findings |

## Proposed changes (ordered, validatable)

1. E-01: add the shared same-release predicate.
2. E-02: route both comparison sites through it.
3. E-03: behavior tests for same, same-close, and genuinely different.
4. E-04: bare suite and live release-gates check.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: none known; the two sites are the only gate-to-gate comparisons found by grep.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine_release_gate.py -o addopts="" -q` plus the V-03 revert.
- Bare `python3 -m pytest`.

## Spec / documentation sync

N/A: the release-gate contract in AGENTS.md already says `next` resolves to the single planned release; this makes the code honor it. No spec text changes.

## Open questions

### OQ-01: When one side cannot be resolved, should the comparison fail closed?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved from repository evidence: an unresolvable value is already reported at error by `check.blocks-release-dangling`, so falling back to string equality here avoids double-reporting while never treating two different releases as one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the helper's diff.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of both sites and `grep -n "carrier_br ==\|carrier_br !=" agent_workflows/check_engine.py` showing no raw comparison remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the three tests passing; then restore the raw `!=` / `==` comparisons IN THE WORKTREE, paste (a) and (b) FAILING while (c) still passes, and restore.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the release-gates result line, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.
