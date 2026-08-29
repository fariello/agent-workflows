# IPD: runner truth alignment: the runner must consume what the repository declares

- Date: 2026-08-29
- Kind: orchestrator
- Concern: Three shipped-runner defects in which `aw <host> run` acts on a DIFFERENT truth than the repository declares: it runs the lane branch's copy of the tooling instead of its own, it measures the wrong tree when deciding execution authority, and it cannot read the `Item-Dependencies` field that 11 pending plans declare.
- Scope: The runner's alignment with declared repository truth, in three independent children: (01) nested `aw` invocations must run the RUNNER's tooling, not the lane branch's checked-out copy; (02) `aw ipd begin`'s in-scope-dirty gate must measure the tree the turn will actually execute in; (03) runner preflight must consume the SHARED `Item-Dependencies` predicate instead of a private legacy regex. Excludes the session/worktree granularity defect (backlog xd9sll), already fixed in `c0e9599`, and excludes any change to the dependency GRAMMAR or the four non-runner surfaces that already consume it correctly.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lifecycle.py, tests/test_lane_tool_identity.py, tests/test_begin_dirty_gate_scope.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: to-review
- Set: lanetruth
- Order: 0
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: y0gg8o
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog items `tfx39h` and `l6rh0z` (both filed this session from live evidence in the wtiso runs) plus `y9lcem`, filed from finding SR-001 of the `25kzda` spec review. Sibling item `xd9sll` was closed `done` rather than graduated, because it was already fixed in `c0e9599` with 6 falsifiable tests; it is cited here as prior art, not as a child.

## Goal

Make the runner act on the repository's declared truth. Each child closes one place where it does not: it executes tooling from the tree it is operating ON rather than the tree it IS, it decides execution authority from a tree the turn will never touch, and it silently ignores a declared dependency graph. All three are shipped-code defects in a verb used daily, and all three fail SILENTLY rather than closed, which is the opposite of the posture spec `25kzda` requires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the three children

- [ ] E-01 Execute child `af7i6p` (Order 01): pin nested `aw` invocations to the runner's own tooling. This runs FIRST because until it lands, every other lifecycle fix (including `z2isfg`'s) is void inside a lane whose base predates it, so validating a lane-side fix would be unsound.
  - Depends on: none
  - Expected outcome: child `af7i6p` reaches `executed` with its own validation evidence; a nested `aw` in a lane reports the RUNNER's module path and version.
  - Execution state: pending

- [ ] E-02 Execute child `z2isfg` (Order 02): scope `begin`'s in-scope-dirty gate to the tree the turn will actually execute in.
  - Depends on: E-01
  - Expected outcome: child `z2isfg` reaches `executed`; an isolated lane is granted execution authority even when a co-worker has dirtied an in-scope path in the MAIN tree.
  - Execution state: pending

- [ ] E-03 Execute child `8guhs0` (Order 03): make runner preflight consume the shared `Item-Dependencies` predicate.
  - Depends on: E-01
  - Expected outcome: child `8guhs0` reaches `executed`; a declared `executed:<id6>` edge appears in the frozen queue and gates launch.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Graduated from | Depends on | Why |
| --- | --- | --- | --- | --- | --- |
| 01 | `af7i6p` | nested `aw` in a lane must run the runner's own tooling | backlog `tfx39h` | none | Must land first: it is the defect that makes OTHER fixes ineffective inside lanes. |
| 02 | `z2isfg` | scope `begin`'s dirty gate to the executing tree | backlog `l6rh0z` | `af7i6p` | Touches `ipd_lifecycle.py`, which is exactly the module a stale lane copy would shadow, so its fix is only verifiable in a lane once 01 lands. |
| 03 | `8guhs0` | runner preflight consumes the shared dependency predicate | backlog `y9lcem` (spec review SR-001) | `af7i6p` | Independent of 02 in subject matter, but sequenced after 01 for the same tool-identity reason. |

02 and 03 are mutually independent and MAY be executed in either order or in parallel once 01 is verified. The declared edges are `executed:af7i6p` on both, deliberately NOT a 01 -> 02 -> 03 chain, so a failure in 02 does not block 03.

Each child carries `- From-Backlog:` naming its source item and inherits `- Blocks-Release: next`.

## Completion criteria (the whole Set is done only when)

1. All three children are in `.aw/records/plans/executed/` with status `executed`, each finalized by `aw ipd finalize` (never a hand-move).
2. A nested `aw` invoked by the runner inside a lane provably runs the RUNNER's tooling: same module path and version as the parent, demonstrated with a lane whose checked-out `agent_workflows/` differs.
3. An isolated lane receives execution authority when the only dirty in-scope path belongs to another party in the main tree, and still refuses when the LANE's own frozen base is genuinely ambiguous.
4. A plan declaring `- Item-Dependencies: executed:<id6>` produces a frozen queue containing that edge (not `[]`), and a dependent is not launched while its prerequisite is unverified.
5. The runner no longer defines a private dependency regex; one shared predicate serves all surfaces, asserted by a guard test.
6. Full suite green against the recorded baseline (see Required tests), leak scan clean, `aw ipd lint --phase pre-transition` conforming for every child.

## Cross-IPD validation

- After all three land, run ONE end-to-end `aw oc run` over a two-plan Set where B declares `executed:<A-id6>`, with a co-worker's uncommitted edit present on an in-scope path, and with the lane based on a commit that predates the current tooling. All three defects would previously have fired in that single run: the lane would run stale tooling, `begin` would refuse B for someone else's dirt, and the queue would ignore the edge. Paste the run's `state.json` queue (showing the edge and correct gating) and the child argv/version evidence.
- Confirm no regression to the `c0e9599` fix from backlog `xd9sll`: `tests/test_lane_session_isolation.py` must still pass unchanged, since children 01-03 touch the same two driver modules.

## Deferred / out of scope (with reason)

- Backlog `xd9sll` (session reuse pinning a turn to the previous lane's worktree): already fixed in `c0e9599`; the item was closed `done` with evidence rather than graduated. Not a child, but its tests are a regression surface for this Set.
- Backlog `qyaime` (external_directory permission deadlock) and `dh0uno` (state roots resolved relative to the lane): both `graduated` already and owned by the `wtiso` Set. Children here must not duplicate that work; where this Set's fixes reduce the blast radius of those defects, say so without claiming to close them.
- The `Item-Dependencies` GRAMMAR and the four surfaces that already consume it correctly (`check_engine.py`, `ipd_lint.py`, `ipd_set_plan.py`, the `ipd-dependency-statement-gate` hook). Verified working; child 03 adds the missing fifth consumer only.
- Spec `25kzda`'s stale preamble and the section 2.10 claim that five surfaces already share the predicate (review findings SR-001/SR-002). Spec text is the maintainer's to amend; this Set makes the code match what section 2.10 asserts.
- The wider runner-consolidation program in `25kzda` (`aw hooks install`, `aw <host> prompt`, the hash-chained ledger with `AW-Run:`/`AW-Item:` trailers, the per-host capability descriptor). All genuinely unbuilt and much larger than this corrective Set.

## Scope check

- Over-scope: none. Each Scope-Path is touched by exactly one child, except the two driver modules which children 01 and 03 both touch (01 changes how nested `aw` is launched; 03 changes how the queue is built). The children declare this overlap and 03 depends on 01 so the edits serialize.
- Under-scope: `xd9sll`, `qyaime`, `dh0uno`, and the spec-text findings are named under Deferred with reasons rather than silently dropped.

## Required tests / validation

- `python3 -m pytest -n auto` (default fast subset) and `python3 -m pytest -m "" -n auto` (full). RECORDED BASELINE at authoring time: the fast subset was `2871 passed, 3 skipped, 4 xfailed`; the full run was `4 failed, 3198 passed, 3 skipped, 4 xfailed`, where the 4 failures are PRE-EXISTING and unrelated (`test_command_surface_declarations`, `test_cli_conformance_matrix` x2, `test_cli` subparser descriptions; undeclared CLI parser leaves from concurrent `run_cli` work, reproduced on a clean tree by stashing unrelated edits). Each child MUST re-establish this baseline before and after its own work and MUST NOT claim those 4 as caused or fixed here.
- `tests/test_lane_session_isolation.py` must pass unchanged (the `xd9sll` regression surface).
- Each child adds its own test module and each must demonstrate FALSIFIABILITY: the new assertions must be shown to FAIL against the pre-fix code, not merely pass after it. A guard that cannot fail is not evidence.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming per child.

## Open questions

### OQ-01: Should the runner keep reading the legacy `Dependencies:`/`Depends-on:` field at all?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, remove it. Measured: 0 of 22 pending plans that declare dependencies use the legacy field, and 11 use `Item-Dependencies`, so nothing tracked depends on the old name. Keeping two accepted names is exactly how the two parsers diverged in the first place. Child 03 removes the private regex and adds a guard asserting the runner does not define one, which is what makes the divergence non-recurring. If any untracked or adopter plan still uses the legacy field, the fail-closed preflight from child 03 surfaces it as a missing statement rather than silently treating it as `none`.

### OQ-02: Should child 02 fix the main-tree dirty check as well, or only the isolated path?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Child 02's lean is to fix ONLY the isolated path (measure the lane) and leave the non-isolated dirty refusal intact, since for a non-isolated turn the main tree genuinely IS the execution tree and the ambiguity protection is correct there. The open part is whether the non-isolated check should additionally become ownership-aware, which is backlog `077yqc`'s subject at the finalize end. Child 02 states the boundary and does not expand into `077yqc`.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste child `af7i6p`'s terminal status and location proving it is `executed` in `.aw/records/plans/executed/`, plus its own V-item evidence showing a nested `aw` in a lane reporting the RUNNER's module path and version while the lane's checked-out `agent_workflows/` differs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste child `z2isfg`'s terminal status and location, plus its evidence showing (a) an isolated lane granted authority with an in-scope path dirty in the MAIN tree, and (b) a genuinely ambiguous lane base still refused.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste child `8guhs0`'s terminal status and location, plus its evidence showing a frozen queue containing a declared `executed:<id6>` edge (contrast against today's measured `dependencies: []`), a dependent NOT launched while its prerequisite is unverified, a malformed/cyclic statement refused at preflight before any session starts, and the guard proving the runner defines no private dependency regex. Additionally paste the cross-IPD end-to-end run described under Cross-IPD validation and the unchanged `tests/test_lane_session_isolation.py` result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This is a Set rather than one plan because the three defects are in different subsystems (process launch, lifecycle authority, queue construction), have different test surfaces, and are independently valuable: any one can ship alone and improve correctness. They are orchestrated together because they share one root theme and because child 01 must precede the others for their validation to be sound inside a lane.

Execution contract: each child commits ONLY the files it changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never pushes. Before every commit the executor MUST run `git diff --cached --name-only` and unstage anything it did not modify. This repository is a SHARED CHECKOUT with other agents and humans working concurrently; at authoring time a concurrent session had uncommitted work in `agent_workflows/` and `tests/`, and a path-scoped commit still commits whatever is already staged for those paths.

Children 01 and 03 both modify `oc_runipd.py` and `agy_runipd.py`. The executor must re-read those files before editing rather than reusing a stale view, and must keep both drivers symmetric: a one-driver-only fix is a defect, and each child must assert symmetry in its tests the way `tests/test_lane_session_isolation.py` already does.

Post-gate lifecycle: no child may be moved to `executed/` until every one of its `V-*` items is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. This orchestrator is finalized only after all three children are `executed` and the Cross-IPD validation above has been performed.
