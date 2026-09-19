# IPD: Wire the shape check into both runners ahead of the probe and report every finding before refusing

- Date: 2026-09-19
- Kind: child
- Concern: Review-time repair (child 02) is agent-performed and self-assessed, so it bounds and logs the repair without making it independent. Spec `r07vma` R8 puts a deterministic re-check in the run, which is what provides that independence: the run re-validates rather than trusting the review's verdict. It must also fix an operator-experience failure the maintainer named explicitly: a gate that reports one violation, gets fixed, then reports the next is the worst possible shape, so the run must collect EVERY finding across EVERY queued orchestrator and report them together before exiting.
  THE ORDERING IS LOAD-BEARING AND IS NOT AN OPTIMISATION. The shape check is free and deterministic; the probe spends a model call and has an availability failure mode (`could-not-ask` proceeds with a warning and a recorded hole). Running the shape check FIRST means the tidy violation costs nothing, and R9 plus criterion 11 require that a shape refusal spends zero model calls. Running the probe first would pay for a verdict on a plan the cheap check already refuses.
  THE PROBE MUST SURVIVE THIS CHANGE, and that is a governing-spec requirement rather than a preference. `25kzda` 2.5b (approved) states the coverage check is SEMANTIC, that "A syntactic rule MUST NOT be added in its place", and gives the measured reason: the dangerous violation is stated in PROSE and matches no checklist syntax. Spec `r07vma`'s own SR-001 records that its draft proposed retiring the probe and was wrong. Measured at HEAD `21eff5d8`: seven probe functions in `runner_shared` totalling 476 lines, plus `tests/test_orchestrator_probe.py` at 1265 lines.
- Scope: The runner-side consumer of child 01's shared function, on BOTH hosts. IN: a pre-queue shape check over the queued orchestrators, sited so it runs before any agent turn, lane worktree or session; collecting all findings across all queued orchestrators and reporting them together before refusing (R8); ordering it AHEAD of the existing probe so a shape refusal spends no model call (R9, criteria 9 and 11); and making the two refusals distinguishable by rule id (criterion 10). OUT: the grammar and function (child 01); the review consumer (child 02); migrating any orchestrator (child 04); the merged proof (child 05); and any edit to the probe's seven functions or its test file, which criterion 9 pins as intact.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_orchestrator_shape_gate.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:dpdyed
- Status: to-review
- Set: orchtyped
- Order: 3
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0xmk4e
- From-Spec: r07vma
- Blocks-Release: next
- Work-Kind: bug
- Priority: high

## Workflow history

- 2026-09-19 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from approved spec `r07vma` as Order 03 of Set `orchtyped`. Measured at HEAD `21eff5d8`: `enforce_orchestrator_probe_gate` is called from `initialize_run_core` and already collects all outcomes then partitions them into `blocking` and `unavailable`, so R8's batch shape is the house pattern rather than a new one; `queued_orchestrator_targets` already enumerates the queue's orchestrators and already skips an unreadable plan rather than refusing. This child extends both rather than duplicating either.

## Goal

Make a run refuse a non-conforming orchestrator deterministically, before it spends anything, having reported every finding across every queued orchestrator in one pass; and leave the semantic probe running behind that check so the prose case is still caught.

READ THE SCOPE PRECISELY: this child adds a CONSUMER and a gate ordering. It adds no rule (child 01 owns that) and removes no control. If its diff touches the probe's seven functions or `tests/test_orchestrator_probe.py`, it has violated criterion 9 and the reviewer should refuse it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the gate, on both hosts, from one object

- [ ] E-01 ADD THE PRE-QUEUE SHAPE GATE IN `runner_shared`, calling child 01's function over the queued orchestrators, and re-export it to both hosts so there is ONE object. Reuse `queued_orchestrator_targets` for the enumeration rather than writing a second queue walk: it already selects `kind == "orchestrator"` from `state["queue"]`, already resolves each plan path, and already SKIPS an unreadable plan rather than refusing (a plan the runner cannot read is a different refusal the existing preflight owns).
  NO SYMBOL MAY BE ADDED TO `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports dozens of names from `oc_runipd` and zero flow the other way; a shared symbol goes in `runner_shared`. E-04 pins this with the refork guard.
  - Depends on: none
  - Expected outcome: one gate function in `runner_shared`, re-exported to both hosts; `oc.<sym> is agy.<sym>` is True; the oc-to-agy import count is not increased.
  - Execution state: pending

- [ ] E-02 SITE IT BEFORE ANY AGENT TURN, LANE WORKTREE, OR SESSION, and ORDER IT AHEAD OF THE PROBE. `enforce_orchestrator_probe_gate` is called from `initialize_run_core` after the run directory exists, and that siting is a PRICED EXCEPTION recorded in its own docstring: the probe needs somewhere durable to log its model call and its refusal must be readable in `aw runs`. The shape check has NO such need, because it spends nothing and produces no model call to log.
  SO DECIDE AND RECORD WHERE IT GOES, and this is the one genuine design choice in this child. Placing it with the three existing pre-queue gates (`enforce_draft_admission_gate`, `enforce_dependency_preflight`, `enforce_mixed_type_gate`), which all raise BEFORE the run directory is created, keeps the no-durable-write-ahead-of-a-refusal invariant intact and is the cleaner position. Placing it beside the probe makes its refusal readable in `aw runs` for symmetry with the probe's. State which you chose and why in a code comment, and note the consequence for criterion 11's evidence: if it raises before the run directory exists, "zero probe invocations" is provable by there being no run to probe.
  - Depends on: E-01
  - Expected outcome: a non-conforming orchestrator refuses the run with no agent turn, no lane worktree and no session; the chosen siting is justified in a comment naming the invariant it respects.
  - Execution state: pending

### Task group 2: the report, the coexistence, and the pins

- [ ] E-03 COLLECT EVERY FINDING ACROSS EVERY QUEUED ORCHESTRATOR AND REPORT THEM TOGETHER BEFORE REFUSING (R8). Follow the existing structure rather than inventing one: `enforce_orchestrator_probe_gate` already loops its targets, appends to `outcomes`, then partitions into `blocking` and `unavailable`. Generalise that shape across CHECK KINDS so a run can report shape findings and probe findings in one place, and do not stop at the first violation.
  THE MAINTAINER'S STATED REQUIREMENT, quoted because it is the acceptance bar: a cycle of "fix this, retry, now that is wrong, retry" is the worst possible operator experience, so a run must complete all checks and report on all of them before exiting.
  - Depends on: E-01
  - Expected outcome: a queue with three non-conforming orchestrators reports all three, with all their per-row findings, then exits once.
  - Execution state: pending

- [ ] E-04 PIN THAT THE PROBE STILL RUNS AND THAT THE TWO REFUSALS ARE TELLABLE APART (criteria 9 and 10). Add a test that an orchestrator whose ROWS all conform but which carries an obligation in its continuation lines or its `## Completion criteria` section is STILL refused, by the probe, after this change. Add a test that the shape refusal and the probe refusal name DIFFERENT rule ids, so an operator reading a refused run knows which control fired and therefore which remedy applies.
  ALSO ASSERT THE PROBE IS UNTOUCHED: `tests/test_orchestrator_probe.py` byte-unchanged in this child's diff, and the seven probe functions present. Add the refork-guard row for whatever symbol E-01 adds, and MUTATION-CHECK that guard (define a local copy in `agy_runipd`, show the guard fails, revert, show it passes), because the guard's aggregate test does not fail a one-sided row on its own.
  - Depends on: E-02, E-03
  - Expected outcome: the prose-only case still refuses via the probe; the two rule ids differ; the probe's test file is absent from this child's diff; the refork guard covers the new symbol and fails when mutated.
  - Execution state: pending

- [ ] E-05 PROVE A SHAPE REFUSAL SPENDS ZERO MODEL CALLS (criterion 11), which is the whole point of the ordering. Assert it by OBSERVATION rather than by reading the code path: inject the probe's spawn seam and assert it was never called, since `ask_orchestrator_probe`'s docstring records that every test injects that seam and that the real spawn is unreachable by construction.
  - Depends on: E-02
  - Expected outcome: a run refused by the shape check shows zero probe invocations, asserted through the injected seam.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `enforce_orchestrator_probe_gate` IS CALLED FROM `initialize_run_core`, not from `run_queue`. The queue is BUILT and then gated; `run_queue` is the dispatch loop where `queue_sort_key` orders by `dependency_depth` first. So a pre-queue gate refuses regardless of an item's dependencies or position, and a `DriverError` there means the dispatch loop never starts.
- THE BATCH-REPORT SHAPE ALREADY EXISTS in that gate: loop targets, append `outcomes`, partition into `blocking` and `unavailable`. E-03 generalises it across check kinds rather than rebuilding it.
- `queued_orchestrator_targets` SCOPES TO THE QUEUE ON PURPOSE (its docstring: "Never the whole corpus"), because `aw oc run all` would otherwise make the cost a function of the tree. It also SKIPS an unreadable plan rather than refusing, leaving that to the existing preflight. E-01 reuses it.
- THE THREE EXISTING PRE-QUEUE GATES RAISE BEFORE THE RUN DIRECTORY EXISTS (`enforce_draft_admission_gate`, `enforce_dependency_preflight`, `enforce_mixed_type_gate`), and the probe's post-directory siting is documented as a deliberate PRICED EXCEPTION because it must log a model call. The shape check has no such need, which is the argument E-02 must weigh.
- NO SYMBOL FLOWS FROM `oc_runipd` TO `agy_runipd` WITHOUT COST: agy already imports dozens of names from oc and none flow back. Shared symbols belong in `runner_shared`, and `tests/test_runner_refork_guard.py` is the pin.
- THE REFORK GUARD'S AGGREGATE TEST DOES NOT FAIL A ONE-SIDED ROW (measured previously in this repository: 4 of 46 shipped rows are legitimately one-sided and pass), so a mutation check is the only real proof that a new row is enforced.
- SUITE BARE: `python3 -m pytest`; compare failing NODE IDS, not totals.

## Findings

| Id | Severity | Location (symbol / content anchor) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.enforce_orchestrator_probe_gate`; `25kzda` 2.5b | The probe must survive: an approved spec forbids substituting a syntactic rule for the semantic check, and `r07vma`'s SR-001 records that its own draft proposed exactly that and was wrong. This child therefore ADDS a gate and touches no probe function. | the spec text; 476 lines across seven functions measured |
| F-2 | HIGH | `initialize_run_core`; the three pre-queue gates | Siting is a real choice with an invariant attached: the pre-queue gates raise before any durable write, while the probe's later siting is a documented priced exception for logging a model call. The shape check has no logging need, so the earlier position is available and cleaner. | the gate's docstring; the three sibling gates' placement |
| F-3 | HIGH | `enforce_orchestrator_probe_gate`'s outcomes/partition structure | R8's batch reporting is the house pattern already, so it must be generalised rather than reimplemented; a second reporting path would diverge. | source read |
| F-4 | MEDIUM | `tests/test_runner_refork_guard.py` | The guard's aggregate test passes a one-sided row, so adding a row is not self-enforcing and E-04 must mutation-check it. | previously measured: 4 of 46 rows one-sided and passing |
| F-5 | MEDIUM | `ask_orchestrator_probe`'s spawn seam | Criterion 11 is provable by injection: the docstring records that every test injects the seam and the real spawn is unreachable by construction, so E-05 asserts zero invocations rather than reasoning about the code path. | the docstring |
| F-6 | LOW | `queued_orchestrator_targets` | It skips an unreadable plan rather than refusing, so the shape gate inherits that behaviour and must not silently convert a skip into a pass. An unreadable plan is the existing preflight's refusal. | the docstring |

## Proposed changes (ordered, validatable)

1. E-01 adds one gate in `runner_shared`, re-exported to both hosts, reusing the existing queue enumeration.
2. E-02 sites it before any agent turn and ahead of the probe, with the siting choice justified.
3. E-03 generalises the existing collect-then-partition structure across check kinds.
4. E-04 pins the probe's survival, the distinguishable rule ids, and the refork guard with a mutation check.
5. E-05 proves a shape refusal spends zero model calls, by injection.

## Deferred / out of scope (with reason)

- THE GRAMMAR AND THE SHARED FUNCTION: child 01 (`dpdyed`). This child calls it.
  - Carrier-Declined: Owned by a named sibling in this Set.
- THE REVIEW CONSUMER AND ITS REPAIR LOOP: child 02 (`r3xk1f`). Independent consumer, separately reviewable.
  - Carrier-Declined: Owned by a named sibling in this Set.
- MIGRATING THE EXISTING ORCHESTRATORS: child 04 (`68uhp0`). This child will make every live orchestrator refuse once it lands, which is EXPECTED and is why child 04 depends on it; that ordering is deliberate so the migration is verified against the same gate a run applies.
  - Carrier-Declined: Owned by a named sibling in this Set.
- RETIRING, WEAKENING, OR REORDERING THE PROBE BEHIND THE SHAPE CHECK: forbidden by `25kzda` 2.5b and pinned by criterion 9. Ordering the shape check first is not weakening the probe; deleting or gating it would be.
  - Carrier-Declined: An explicit non-goal the governing spec forbids.
- TYPING THE ORCHESTRATOR'S PROSE SECTIONS so the probe becomes unnecessary: out of scope and out of this Set. Spec Section 3a limit 1 records the residue as an honest limit.
  - Carrier: d1u4sy

## Scope check

- Over-scope: `tests/test_runner_refork_guard.py` is declared because E-04 adds a row and mutation-checks it, which is a real edit rather than a read.
- Under-scope: if E-02's siting decision places the gate somewhere this plan does not declare (for example a host-level entry point rather than `initialize_run_core`'s shared path), that path must be DECLARED before editing. The siting is deliberately left as a recorded decision rather than prescribed, so the executor should expect to amend `- Scope-Paths:` and say so.

## Required tests / validation

`python3 -m pytest` BARE, in an isolated worktree, baseline measured there, compared by failing NODE ID.

EXPECT THE LIVE CORPUS TO REFUSE once this lands, and do NOT fix it here: measured at HEAD `21eff5d8`, zero of 32 live orchestrator rows conform, so every pending orchestrator will refuse until child 04 migrates them. Tests must therefore use FIXTURES rather than the repository's own plans, and an executor who finds themselves editing a real orchestrator to make a test pass has taken child 04's work and should stop.

Beyond the suite: the object-identity check across both hosts; a three-violation queue reporting all findings in one pass; the prose-only case still refused by the probe; both rule ids side by side; the refork-guard mutation check; and zero probe invocations on a shape refusal.

## Spec / documentation sync

N/A with reason: spec `r07vma` R8/R9 and criteria 9 through 11 are implemented as written, and `25kzda` 2.5b is respected rather than amended (the probe keeps its mechanism and its position relative to the agent turn; only a cheaper check is added ahead of it). No `.spec.md` path is declared. If an executor concludes the ordering requires amending 2.5b, that is a finding to report rather than an edit to make, because 2.5b is approved and its prohibition is what this child is built around.

## Open questions

### OQ-01: Should the shape gate refuse before the run directory exists, or beside the probe so its refusal is readable in `aw runs`?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: NOT blocking: E-02 requires the executor to CHOOSE and JUSTIFY, and both positions satisfy R8 and R9. The trade is recorded because it is not obvious. Refusing early keeps the invariant that no durable write precedes a refusal, which the three sibling pre-queue gates all honour, and makes criterion 11 trivially provable since there is no run to probe. Refusing late makes the shape refusal durable and readable in `aw runs` exactly as the probe's is, which is what an operator reading a failed run expects, and the probe's docstring records that durability as the reason for its own placement. PROPOSED DIRECTION: refuse EARLY with the sibling pre-queue gates, and accept that the refusal is read from the process output rather than from `aw runs`, since a shape violation is fixed by editing a plan rather than by inspecting run state. If that proves annoying in practice, moving it later is a small change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste object-identity output showing the gate symbol resolves to the SAME object from `runner_shared`, `oc_runipd` and `agy_runipd`. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase. Paste the call showing `queued_orchestrator_targets` is reused rather than a second queue walk added.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the code comment recording WHICH siting was chosen and WHY, naming the invariant it respects. Paste proof a refused run left NO agent turn, NO lane worktree and NO session (an empty `sessions/` directory plus a zero attempt count is acceptable). State plainly whether a run directory exists in the refusal path, since that determines how criterion 11 is evidenced.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the output of a queue containing THREE non-conforming orchestrators, showing every finding for all three reported together before a single exit. Confirm no early return exists by showing the collect-then-partition structure in the diff. A run that reported one violation and exited FAILS this item regardless of the exit code.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a fixture orchestrator whose ROWS all conform but which carries an obligation in its continuation lines or `## Completion criteria`, and show it is STILL refused by the probe after this change. Paste the shape refusal and the probe refusal side by side, showing DIFFERENT rule ids. Paste `git status`/`git diff --stat` proving `tests/test_orchestrator_probe.py` is byte-unchanged and the seven probe functions are intact. Paste the refork-guard MUTATION check: define a local copy of the new symbol in `agy_runipd`, show the guard FAILS, revert, show it passes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the test that injects the probe's spawn seam and asserts ZERO invocations on a run the shape check refused. Show the injection, not just the assertion, so a reader can see the real spawn was never reachable.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 5 E-leaves in 2 groups. The gate and its siting are one concern; the report, the coexistence pins and the zero-cost proof are the surfaces that prove it behaves.
- Cohesion rationale: E-01 and E-02 are one gate and its position, inseparable because the position is what makes it cost nothing. E-03 through E-05 are the three properties the spec's criteria demand of that gate (batch reporting, coexistence with the probe, zero model calls), and each is meaningless without the gate existing. Splitting the pins into their own child would leave a gate whose required properties are unproven.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. When reporting tests passed, paste the ACTUAL runner output. This is a SHARED CHECKOUT: other agents are editing this tree concurrently, so never revert or commit a file you did not change. In particular do NOT edit any real orchestrator to make a test pass; that is child 04's work and doing it here hides the migration's cost.

Post-gate lifecycle: requires `/plan-review` then explicit human approval (`aw ipd set approved 0xmk4e --by-human --message ...`). Do NOT hand-write a `- Readiness:` field. Its `- Item-Dependencies:` refuse dispatch until `dpdyed` is executed. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
