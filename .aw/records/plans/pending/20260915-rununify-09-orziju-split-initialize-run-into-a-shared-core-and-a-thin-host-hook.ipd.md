# IPD: Split initialize_run into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `initialize_run` is written twice (409 lines in `oc_runipd.py`, 339 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 15 differing code lines of which only 6 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses.
- Scope: Extract the host-neutral core of `initialize_run` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_initialize_run.py
- Item-Dependencies: executed:sy7uwh
- Status: to-review
- Set: rununify
- Order: 9
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: orziju
- From-Backlog: alw22r

## Workflow history
- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `initialize_run` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: characterize before touching

- [ ] E-01 PIN THE CURRENT BEHAVIOR OF BOTH HOSTS FIRST, per the parent's E-02 constraint that no child may reconcile a symbol the characterization baseline has not pinned. Write characterization tests for `initialize_run` on BOTH hosts covering every branch the split will move, following the precedent of `tests/test_wtiso_characterization.py`. The parent's own measurement found the agy side is the less covered one, so prioritize agy branches with no existing coverage. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: none
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code and would fail if either host's observable behavior moved; the agy branches previously uncovered are named.
  - Execution state: pending

### Task group 2: the split

- [ ] E-02 Extract the host-neutral core into `runner_shared.py`, taking the oc logic, and define the hook boundary at the points named in Findings rather than wherever the code happens to divide. Each host keeps a thin function that supplies its own pieces and calls the core. Do NOT change behavior: this is a relocation with a parameter, and any place the two hosts genuinely differ becomes a hook input, not an `if host == ...` branch inside the core.
  - Depends on: E-01
  - Expected outcome: one core in `runner_shared`; each host's `initialize_run` is a thin caller; no host-name conditional inside the shared core.
  - Execution state: pending

- [ ] E-03 Resolve each measured difference explicitly and record the resolution, so no difference is settled by accident of which copy was pasted. Findings enumerates them; for each, state whether it resolved to oc (the default), to agy (a real capability oc lacks), or became a hook input, and why.
  - Depends on: E-02
  - Expected outcome: a per-difference resolution table in the execution report, with nothing marked "unchanged" that in fact moved.
  - Execution state: pending

### Task group 3: proof

- [ ] E-04 Add `tests/test_rununify_initialize_run.py`: the core resolves to the SAME OBJECT from both hosts; an AST scan proves neither runner still holds a second implementation (repo-wide, per the parent's F10, not a pairwise check); each host's hook still supplies its OWN host-specific pieces; and the hazard named in Findings is asserted directly.
  - Depends on: E-02, E-03
  - Expected outcome: a suite that fails if the symbol is re-forked, if a host's specifics collapse into the other's, or if the named hazard regresses.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-01 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `initialize_run` differs in only FIFTEEN code lines, and MOST of them disappear once child 06 unifies `PlanRecord`: agy's `kind is None -> _plan_kind(p_path)` fallback exists solely because its record lacked the field. Ordering this after child 06 shrinks the work rather than duplicating it. |
| F-2 | HIGH | `initialize_run`, both hosts | THE HAZARD THIS SPLIT CARRIES: The frozen `state['queue']` shape is read by RESUME. If the two hosts write different queue-entry keys today, a shared writer changes what a resume of an in-flight run finds. Prove a pre-existing run directory from BOTH hosts still resumes. |
| F-3 | MED | `initialize_run` | DIFFERENCE, verification resolution: oc calls `resolve_launch_pair(args)`, agy calls its own `resolve_verification_decision(args)` which already delegates to `runner_shared.resolve_verification_decision`. Plan `ybkmzp` built that shared resolver and wired BOTH hosts to it; oc's `resolve_launch_pair` additionally resolves the LAUNCH profile. Keep both concerns, and do not collapse the launch-profile half into the verification half. |
| F-4 | MED | `initialize_run` | DIFFERENCE, the `kind` fallback: agy re-reads `- Kind:` from disk when the manifest entry lacks it. Child 06 deletes `_plan_kind`, so this branch must be GONE by the time this plan runs, not ported. |
| F-5 | MED | `initialize_run` | DIFFERENCE, the queue entry: agy writes a `kind` key into each queue entry; oc does not. Once the record is unified, decide ONE shape and state which, because the frozen queue is read by resume. |
| F-6 | MED | `initialize_run` | DIFFERENCE, two shared-gate calls: `enforce_draft_admission_gate` and `enforce_mixed_type_gate` differ only in wrapped-line formatting after normalization; no behavioral difference. |
| F-7 | MED | `initialize_run` | DIFFERENCE, the state dict: differs only by the keys implied above. |

## Proposed changes (ordered, validatable)

1. Characterize both hosts' current behavior for every branch the split will move (E-01).
2. Extract the host-neutral core to `runner_shared`, oc as the source, hooks at the boundaries F-3+ name (E-02).
3. Resolve and RECORD every measured difference, one by one (E-03).
4. Add the anti-re-fork and hazard suite (E-04).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived.
- Any behavior change, feature addition, or flag change. This is a relocation with a parameter.

## Scope check

- Over-scope: none. Three source files plus one new test file, one symbol.
- Under-scope: this plan does not attempt to shrink `initialize_run` itself. Making the shared core smaller is a
  legitimate later refactor, but bundling it here would make the no-behavior-change claim unverifiable.

## Required tests / validation

1. The E-01 characterization suite, green BEFORE and AFTER the split. This is the load-bearing proof of
   no behavior change; both hosts' suites alone are NOT sufficient, because the parent measured them as
   asymmetric (95 oc tests versus 21 agy at the time), so an agy-side regression can hide behind green.
2. `tests/test_rununify_initialize_run.py` (new): shared-core object identity across hosts; AST scan proving no
   re-fork; each host's hook supplying its own pieces; and a direct assertion of F-2's hazard.
3. NON-VACUITY: sabotage the shared core and show BOTH the characterization suite and the new suite
   FAIL, naming the branch; then restore. A relocation suite that cannot fail proves nothing.
4. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
5. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time.

## Spec / documentation sync

No `.spec.md` change expected: this is an internal refactor with no operator-visible contract change. IF
execution finds that a spec sentence describes the divergence being removed, amend it in the SAME change
and add the spec path to `Scope-Paths`, per the repository's spec-amendment rule.

## Open questions

### OQ-01: Where exactly does the hook boundary belong?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: At the points Findings names as genuinely host-specific, and nowhere
  else. The test is mechanical rather than aesthetic: if a candidate boundary would require the shared
  core to contain an `if host == ...` branch, the boundary is in the wrong place, because that branch is
  the duplication this Set exists to remove wearing a different shape.

### OQ-02: What if the split cannot be done without changing behavior?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: STOP AND REPORT rather than proceeding. The parent's hard constraint
  is that a child may not change behavior, and E-01's characterization suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted green run of the characterization suite against UNMODIFIED code, plus the list of agy branches it newly covers, plus a sabotage of one pinned branch showing the suite FAILS (a characterization test that cannot fail pins nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted proof that the shared core is ONE object reachable identically from both hosts, that each host's `initialize_run` is now a thin caller, and a grep/AST result showing NO host-name conditional inside the shared core.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the per-difference resolution table, each row stating oc / agy / hook-input and the reason, covering every difference Findings enumerates with none left unaddressed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_initialize_run.py -o addopts=""` green, including the F-2 hazard assertion. (b) The characterization suite green AFTER the split, alongside its pre-split run, so the comparison is visible. (c) The NON-VACUITY control from Required tests item 3. (d) Bare `python3 -m pytest` with no new failure, plus both hosts' suites green by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS: F-2's hazard and its direct assertion in E-04, and V-01's sabotage,
because a characterization suite is the only thing standing between this relocation and a silent
behavior change on the less-covered host.
