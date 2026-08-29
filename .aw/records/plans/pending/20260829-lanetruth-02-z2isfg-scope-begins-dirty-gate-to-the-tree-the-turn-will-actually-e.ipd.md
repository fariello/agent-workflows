# IPD: scope begin's dirty gate to the tree the turn will actually execute in

- Date: 2026-08-29
- Kind: child
- Concern: For an isolated lane the runner runs `aw ipd begin` against the MAIN repo, so its in-scope-dirty gate measures the MAIN working tree. But the turn will execute in a fresh worktree at the frozen base, where those paths are clean by construction. A concurrent agent's uncommitted edit to a commonly-scoped file therefore withholds execution authority from an unrelated lane, and the suggested remedy is one the operator is forbidden to apply.
- Scope: Make `begin`'s in-scope-dirty ambiguity check measure the tree the turn will actually execute in, without weakening it for the non-isolated case where the main tree genuinely IS the execution tree. Excludes any change to the receipt's location or contents beyond the baseline it records, and excludes making the non-isolated check ownership-aware (backlog `077yqc`).
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, tests/test_begin_dirty_gate_scope.py
- Item-Dependencies: executed:af7i6p
- Status: to-review
- Set: lanetruth
- Order: 2
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: z2isfg
- Blocks-Release: next
- From-Backlog: l6rh0z

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `l6rh0z`, filed this session after the refusal was observed live in run-20260829T184625Z-3940528. Declares `executed:af7i6p` because this plan edits `ipd_lifecycle.py`, exactly the module a stale lane copy shadows, so its fix is only soundly verifiable in a lane once tool identity is pinned.
- 2026-08-29 /plan-review of orchestrator y0gg8o (opencode (its_direct/pt3-claude-opus-5-1m-us)): CROSS-REFERENCE, no change to this plan's substance. The dependency rationale in the line above is FALSE and is corrected in the owning orchestrator (`y0gg8o`, child-table correction). Verified: `driver_begin` runs with `cwd=str(repo)` (oc_runipd.py:370; agy_runipd.py:495) and the lane worktree is not allocated until AFTER begin returns (oc_runipd.py:1958 then :1987; agy_runipd.py:2030 then :2059), so `aw ipd begin` is NEVER lane-shadowed and this plan's fix cannot be voided by a stale lane copy. The `executed:af7i6p` edge is retained as EDIT SERIALIZATION (this plan also touches `oc_runipd.py`), not as a correctness prerequisite. Also recorded there: this plan's E-03 case (b) cannot be built by choosing an older lane base, because `allocate_isolation_worktree` hardcodes `base_commit="HEAD"` (oc_runipd.py:478); construct it by writing into a lane before begin. Orchestrator OQ-02 (whether to also fix the non-isolated check) is now `resolved`: only the isolated path, with `077yqc` owning ownership-awareness.

## Goal

Decide execution authority from the tree that will actually be executed in. Today an isolated lane is refused because of dirt in a tree it will never touch, and because that dirt belongs to a co-worker the operator may not commit or stash, the refusal has no legitimate remedy. The ambiguity the gate protects against does not exist for a fresh worktree pinned to an explicit commit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the right tree

- [ ] E-01 In `ipd_lifecycle.check_begin`, separate "where the receipt lives" from "which tree is the baseline". The dirty check currently calls `dirty_within(str(repo_root), scope_paths, _scope_match)` (ipd_lifecycle.py:702-722), conflating the two. Add an explicit execution-tree parameter (defaulting to `repo_root`, preserving today's behavior for every existing caller) and evaluate in-scope dirtiness against THAT tree. The receipt must continue to be written under the main repo's state root and must continue to record the correct frozen base commit.
  - Depends on: none
  - Expected outcome: `check_begin` accepts an explicit execution tree; with no argument its behavior is byte-identical to today; the receipt's `base_head` is unchanged in both paths.
  - Execution state: pending

- [ ] E-02 Have the runner pass the lane worktree as the execution tree when a turn is isolated. `driver_begin` currently runs against the main repo by design (the receipt is anchored there); it must now also declare the lane as the baseline tree. When the turn is NOT isolated, pass nothing so the main tree remains the baseline and the existing refusal is preserved verbatim. Keep both drivers symmetric.
  - Depends on: E-01
  - Expected outcome: an isolated turn's begin measures the lane; a non-isolated turn's begin measures the main tree; the two drivers agree.
  - Execution state: pending

### Task group 2: prove both directions

- [ ] E-03 Add `tests/test_begin_dirty_gate_scope.py` proving BOTH directions, since a fix that merely stops refusing would be a safety regression: (a) with an in-scope path dirty in the MAIN tree, an isolated lane IS granted authority and the receipt records the correct frozen base; (b) with an in-scope path genuinely dirty in the LANE itself, begin STILL refuses with the ambiguity message; (c) the non-isolated path retains today's refusal unchanged; (d) the refusal message, when it fires, names paths from the tree actually measured.
  - Depends on: E-01, E-02
  - Expected outcome: all four assertions pass; (a) is shown to FAIL against pre-fix code (that is the bug), and (b)/(c) are shown to fail if the check is naively removed rather than rescoped.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The gate and its intent are explicit in the source. `ipd_lifecycle.py:700-701` states: "Disjoint uncommitted work elsewhere is intentionally ignored so a concurrent multi-agent workflow is not thrashed; finalize's scope reconciliation still catches out-of-scope changes." That intent is correct and is precisely what breaks here: in a shared checkout another agent's edit to a commonly-scoped file is NOT disjoint from a broad `Scope-Paths`, so it thrashes the lane anyway.
- The refusal is a hard `EXIT_CANNOT_RUN` with the message "refusing to begin: uncommitted changes to paths INSIDE this plan's Scope-Paths make the frozen base ambiguous" (ipd_lifecycle.py:713-722), so a refused item is recorded `begin refused (no execution authority)` and never launches.
- Observed live: run-20260829T184625Z-3940528 recorded `ipd-begin-refused` for `rchpms` at 18:46:28Z naming `agent_workflows/cli.py`. `rchpms` declares `agent_workflows/cli.py` in its Scope-Paths, and a CONCURRENT session had `cli.py` dirty in the main tree at that moment. The lane that would have been created for `rchpms` would have been clean at its base.
- `cli.py` is in the Scope-Paths of many plans, so in a shared checkout it is frequently dirty for someone. This makes the defect high-frequency, not theoretical.
- The operator cannot apply the message's own remedy. `AGENTS.md` forbids committing, stashing, or reverting another party's uncommitted work, so "Commit or stash these in-scope changes first" is unavailable when the dirt is not yours.
- A worktree created by `worktree_lease.allocate_worktree` is checked out at an explicit commit, so its in-scope paths are clean by construction; the ambiguity the check exists to prevent cannot arise there.
- `aw ipd begin` already accepts `--dir`, which is a viable transport for the execution-tree argument if a CLI-level path is preferred over a function parameter.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `ipd_lifecycle.py:702-722` | The dirty check measures `repo_root`, which for an isolated turn is the MAIN tree, not the tree the turn will execute in. State that cannot affect the lane's frozen base denies the lane authority. | source; `dirty_within(str(repo_root), ...)` |
| F2 | HIGH | run-20260829T184625Z-3940528 | Live refusal: `rchpms` denied on `agent_workflows/cli.py`, dirty from a CONCURRENT session, while its own lane would have been clean. | events.jsonl `ipd-begin-refused`; console text |
| F3 | MED | `AGENTS.md` shared-checkout contract vs `ipd_lifecycle.py:719-721` | The refusal instructs the operator to commit or stash the offending changes, which the contract forbids when they belong to another party. The error is therefore unactionable in exactly the case it fires. | contract text vs message text |
| F4 | MED | conceptual | Because `cli.py` and similar files appear in many plans' Scope-Paths, any concurrent agent editing a common file can silently withhold authority from unrelated lanes across the whole queue. | 22 pending plans; `cli.py` widely scoped |
| F5 | LOW | relation to `077yqc` | This is the BEGIN-end instance of the same ownership blindness that `077yqc` records at the FINALIZE end (`_paths_changed_by_this_execution` unions the whole porcelain with no ownership filter). This one fails closed; that one misattributes. | backlog `077yqc` |

## Proposed changes (ordered, validatable)

1. Split baseline-tree from state-location inside `check_begin`, defaulting to today's behavior (E-01).
2. Have the runner declare the lane as the baseline when isolated, and nothing when not (E-02).
3. Prove the fix rescopes rather than removes the protection (E-03).

## Deferred / out of scope (with reason)

- Making the NON-isolated dirty check ownership-aware is backlog `077yqc`'s subject and is deliberately not attempted here. For a non-isolated turn the main tree genuinely IS the execution tree, so the ambiguity protection is correct as written; only its application to isolated lanes is wrong.
- Backlog `xmqv5l` (begin freezes a whole-file digest, so recording V-item evidence invalidates the receipt) is a different defect in the same receipt machinery and is `graduated` under the `wtiso` Set. Not touched.
- Changing where receipts live (backlog `dh0uno`). This plan explicitly PRESERVES the current receipt location and only changes which tree is measured.

## Scope check

- Over-scope: none. `ipd_lifecycle.py` carries F1/F3, `oc_runipd.py` carries the caller change, and the test module is new and required by E-03.
- Under-scope: `077yqc`, `xmqv5l`, and `dh0uno` are named under Deferred with reasons.

## Required tests / validation

- The new `tests/test_begin_dirty_gate_scope.py` must pass, with the (a) case shown to FAIL pre-fix and the (b)/(c) cases shown to fail under a naive removal of the check. Both directions are mandatory: a fix that only stops refusing has removed a safety property rather than corrected it.
- Existing receipt/lifecycle tests must pass unchanged, in particular anything asserting the refusal for a non-isolated dirty tree.
- `python3 -m pytest -n auto` and `python3 -m pytest -m "" -n auto` against the Set's recorded baseline: fast `2871 passed, 3 skipped, 4 xfailed`; full `4 failed, 3198 passed, 3 skipped, 4 xfailed`, those 4 being the PRE-EXISTING CLI-surface failures. Do not claim them as caused or fixed.
- End-to-end: reproduce F2's exact conditions (dirty an in-scope path in the main tree, then run an isolated lane for a plan declaring that path) and show the lane now begins, with its receipt recording the correct frozen base.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Spec `25kzda` section 5.2 treats single-writer leasing and scope discipline as safety properties; this plan sharpens which tree those properties are evaluated against. No spec text change required, but the executor should record that the isolated case is now measured against the lane.
- The refusal message text is user-facing. If it is reworded, keep it free of em/en dashes per the execution contract, and make it name the tree it measured so the next operator is not misled the way F3 describes.

## Open questions

### OQ-01: Should the isolated path skip the check entirely, or measure the lane?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: MEASURE THE LANE, do not skip. Skipping would be defensible in theory, since a freshly allocated worktree at an explicit commit is clean by construction, but it would silently stop protecting the case where a lane is REUSED or has been written into before begin (which the preserved-lane recovery paths make possible). Measuring the lane keeps the invariant honest in both cases and costs nothing.

### OQ-02: Should the fix be plumbed as a function parameter or via the existing `--dir` flag?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Lean function parameter with a default, because it keeps the semantics explicit at the call site and avoids overloading `--dir`, which already means "repo root" for state resolution and would then mean two things at once. The executor must state which it shipped and must ensure the default preserves existing behavior for all current callers either way.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the changed `check_begin` signature and dirty-check call. Paste a test or transcript proving that with NO execution-tree argument the behavior and the receipt's `base_head` are identical to pre-fix for an existing caller.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the runner call sites showing the lane passed when isolated and omitted when not, for BOTH drivers. Paste a run transcript for an isolated turn showing begin granted while an in-scope path is dirty in the main tree.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste all four assertions passing. Then paste FALSIFIABILITY evidence: (a) fails against pre-fix code; (b) and (c) fail if the check is removed instead of rescoped. Paste the refusal message from case (b) showing it names lane paths, and the non-isolated refusal from case (c) unchanged.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with concurrent agents and humans; at authoring time another session had uncommitted work in `agent_workflows/` and `tests/`. Note the irony and the hazard: the very condition this plan fixes (a co-worker's dirty in-scope file) is likely to be present while executing it, and `agent_workflows/cli.py` is NOT in this plan's Scope-Paths, so do not touch it.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
