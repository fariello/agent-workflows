# IPD: Make the worker-role guard test able to fail again after the session scrub made it vacuous, and cover the agent-side evidence hole the scrub cannot reach

- Date: 2026-09-23
- Kind: child
- Concern: THREE OPEN ITEMS DESCRIBE ONE ROLE-MASKING FAMILY, AND THE FIX FOR TWO OF THEM CREATED THE THIRD. Backlog `8bif6g` (`high`, `Blocks-Release: next`) and `t49rmq` say a worker `AW_EXECUTION_ROLE` makes 31 runner tests fail, so a bare suite cannot validate a plan. That is FIXED: the root `conftest.py` pops `AW_EXECUTION_ROLE` at import time, before any test module is collected. VERIFIED at HEAD `22cf67d9` on the affected family: `tests/test_ipd_lifecycle_cli.py` gives `89 passed` both with and without `AW_EXECUTION_ROLE=worker` in the ambient environment, i.e. the marking no longer changes the result.
  THAT SCRUB IS WHAT MAKES `6z5yos` TRUE, AND `6z5yos` IS THE LIVE DEFECT THIS PLAN OWNS. `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` and `not LC.worker_role_active(os.environ)`. Both read the AMBIENT process environment, which conftest has already cleaned, so the assertion can no longer fail for ANY ambient value. PROVED: running that single test with `AW_EXECUTION_ROLE=worker` set on the command line gives `1 passed`. It passes while holding the exact value it exists to forbid, which makes it a guard that cannot guard.
  THE TWO EFFECTS ARE IN GENUINE TENSION AND THE CONFTEST SAYS SO, which is why this needs a decision rather than a one-line change. Its comment block argues against the alternatives on the record: not in the runners, because the marking on the agent is "DELIBERATE and load-bearing (it is what makes `AW-LIFECYCLE-ROLE-001` fire on a lane agent that tries to finalize its own plan, incident `i452hf`)"; and not by relaxing the guard test, because that test "is CORRECT as written" and backlog `1uq1cu` "names relaxing it as the wrong fix". It then states as an HONEST LIMIT that "a test that needs the marking must set it ITSELF, on an explicit env dict passed to the code under test, which is what every such test already does". The guard test is the ONE case that does not, because its subject IS the ambient environment. So the scrub's own stated escape hatch does not fit its own guard.
  THE EVIDENCE HOLE `8bif6g` ACTUALLY CARES ABOUT IS ONLY HALF CLOSED, and this is the part a reader should not miss. `8bif6g`'s harm is that an agent's measured baseline is false. The scrub fixes that for THIS repository's suite, because this repo ships that conftest. Measured, the runners STILL export the marking into the agent turn (`oc_runipd` and `agy_runipd` both set `child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER`), and nothing in `runner_shared` scrubs it for a suite invocation. A MANAGED TARGET REPOSITORY whose tests read the ambient role, and which does not ship this conftest, therefore still gets masked failures; the fix lives in the wrong layer to protect anyone but us.
  AND THE `env -u` BYPASS IS DOCUMENTED AS STILL OPEN, which is `c4yixg` and is deliberately NOT this plan's subject. `ipd_lifecycle` states the limit plainly: "the env marker is a SELECTOR, not a boundary ... and the measured incident DEFEATED it with `env -u AW_EXECUTION_ROLE`. Closing THAT needs an OS sandbox or a separate principal and is explicitly out of scope." It also records WHY agents reach for `env -u`: because lifecycle tests failed inside a lane, so "agents will keep reaching for it until that is fixed; instruction alone will not hold." The scrub removed that motivation, which strengthens `c4yixg`'s position without closing it.
- Scope: Restore the guard's ability to fail, and close the agent-side half honestly. IN: (a) make `test_driver_own_process_is_not_worker_role` able to fail again, per OQ-01, by testing the property at a seam the session scrub does not pre-clean rather than by weakening the assertion; (b) add a test that the SCRUB ITSELF happens, since nothing currently asserts conftest's pop and a silent removal would restore 31 masked failures undetected; (c) decide and record, per OQ-02, whether the runners should scrub the marking for a suite invocation so a managed target repo gets the same protection without shipping our conftest. OUT: relaxing the guard assertion (backlog `1uq1cu` names that as the wrong fix and the conftest agrees); removing the marking from the agent turn, which is load-bearing for `AW-LIFECYCLE-ROLE-001` and incident `i452hf`; and the `env -u` bypass (`c4yixg`), which needs an OS sandbox or separate principal and is documented out of scope.
- Scope-Paths: conftest.py, tests/test_worker_role_refusal.py, tests/test_conftest_role_scrub.py
- Item-Dependencies: none
- Status: to-review
- Set: rolevac
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 8i0xa7
- From-Backlog: 6z5yos
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the three-item role-masking family, NARROWED by measurement. `8bif6g` and `t49rmq` are FIXED by the root conftest scrub (verified: `tests/test_ipd_lifecycle_cli.py` gives `89 passed` with and without the marking), and should be closed citing it rather than graduated. `- From-Backlog:` names `6z5yos` because it is the live defect, and `- Blocks-Release: next` is INHERITED from the family's gating members (`8bif6g` and `t49rmq` both carry it; a guard that cannot fail is exactly the false-evidence class the policy targets).
  THE FINDING IS THAT THE FIX FOR TWO ITEMS CREATED THE THIRD, and that the conftest ANTICIPATED the objection and its stated escape hatch does not cover its own guard. Proved the vacuity directly: the guard test passes `1 passed` while `AW_EXECUTION_ROLE=worker` is set on its own command line.
  I ALSO MEASURED THE HALF NOBODY OWNS: both runners still export the marking into the agent turn and nothing in `runner_shared` scrubs it for a suite run, so `8bif6g`'s evidence harm is closed for THIS repo (which ships the conftest) and still open for any managed target repo that does not. That is OQ-02 rather than silent scope, because it is a runner change with its own risk.

## Goal

Make the worker-role guard capable of failing again, assert that the session scrub itself still happens, and decide whether the protection belongs in the runner where a managed repo can inherit it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the tension before resolving it

- [ ] E-01 RE-MEASURE ALL THREE CLAIMS, because this plan asserts two are fixed by the very thing that broke the third.
  PROVE THE SCRUB WORKS: run an affected module (e.g. `tests/test_ipd_lifecycle_cli.py`) twice, once with `AW_EXECUTION_ROLE=worker` in the environment and once without, and show the counts are IDENTICAL. At authoring: `89 passed` both ways.
  PROVE THE GUARD IS VACUOUS: run `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` with `AW_EXECUTION_ROLE=worker` set and show it PASSES. At authoring: `1 passed`. This is the single most important measurement in the plan; if it now fails, the defect is gone and you must say so rather than proceeding.
  CONFIRM THE RUNNERS STILL EXPORT THE MARKING and that nothing scrubs it for a suite invocation, which is OQ-02's premise. At authoring both hosts set `child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER` and `runner_shared` has no scrub.
  READ THE CONFTEST COMMENT BLOCK BEFORE PROPOSING ANYTHING. It rejects two fixes by name with reasons, and a proposal that re-treads either without engaging its argument will be rejected at review.
  - Depends on: none
  - Expected outcome: the scrub's effectiveness, the guard's vacuity, and the runners' continued export all reproduced with pasted output; any claim that moved reported rather than absorbed.
  - Execution state: pending

### Task group 2: make the guard guard again

- [ ] E-02 RESTORE THE GUARD'S ABILITY TO FAIL, per OQ-01, WITHOUT WEAKENING WHAT IT ASSERTS. The property it defends is real and worth defending: the DRIVER's own process must never be worker-marked, or `driver_begin` would refuse.
  THE PROBLEM IS THE SEAM, NOT THE ASSERTION. The assertion is correct; it simply reads a value that conftest has already cleaned, so it is testing a post-condition of the test harness rather than a property of the driver. Move the question to a seam the scrub does not pre-clean: ask whether the DRIVER's environment-construction code produces an unmarked environment, rather than whether THIS process happens to be unmarked.
  DO NOT SIMPLY DELETE OR SKIP IT, and do not relax it to an unconditional pass. Backlog `1uq1cu` names relaxing it as the wrong fix and the conftest's own comment agrees ("This scrub is what makes that assertion true again inside a runner turn, rather than weakening it"). A guard that is deleted and a guard that cannot fail are the same thing.
  IF THE HONEST ANSWER IS THAT THE AMBIENT PROPERTY IS UNTESTABLE POST-SCRUB, SAY SO EXPLICITLY and convert the test into one that asserts the scrub happened (E-03's subject), rather than leaving a test whose name promises a guarantee it does not check. A misleading test name is worse than an absent test.
  - Depends on: E-01
  - Expected outcome: a test that FAILS when the driver's own environment construction would be worker-marked and passes otherwise, demonstrated failing by a deliberate local mutation; the assertion's strength is unchanged or stronger; no skip, no unconditional pass.
  - Execution state: pending

- [ ] E-03 ASSERT THAT THE SCRUB ITSELF HAPPENS. Nothing currently tests conftest's `os.environ.pop("AW_EXECUTION_ROLE", None)`, so deleting that line would silently restore 31 masked failures and, with E-02 landed, would ALSO be invisible to the guard.
  THIS IS THE LOAD-BEARING TEST OF THE PAIR, because every other test in the affected families now depends on the scrub for its meaning. The scrub is currently an unasserted invariant that 31 tests silently rely on.
  TEST THE EFFECT, NOT THE SOURCE TEXT. A grep for the `pop` line would pass while the line sat in a branch that never runs; assert the ambient variable is absent during a test session instead. Note this is self-referential (the thing under test is what cleaned the environment), so state plainly in the test docstring what it does and does not prove.
  - Depends on: E-01
  - Expected outcome: a test that fails if the conftest scrub is removed, demonstrated by removing it locally; it asserts the observable effect rather than the presence of a source line; its docstring states the self-referential limit.
  - Execution state: pending

### Task group 3: the half nobody owns

- [ ] E-04 DECIDE AND RECORD WHETHER THE RUNNERS SHOULD SCRUB THE MARKING FOR A SUITE INVOCATION, per OQ-02. Implement only if OQ-02 resolves that it belongs here; otherwise AUTHOR A SUCCESSOR PLAN carrying the measurement, rather than filing a backlog item, since the asymmetry is already measured and what is missing is a reviewed design.
  THE ASYMMETRY IS THE POINT: the conftest fix protects THIS repository because this repository ships that conftest. A managed target repo whose own tests read the ambient role gets no protection, and `8bif6g`'s harm (a false measured baseline feeding a `V-*` evidence block) applies there identically.
  DO NOT REMOVE THE MARKING FROM THE AGENT TURN. It is load-bearing for `AW-LIFECYCLE-ROLE-001` and incident `i452hf`; the conftest comment is explicit that removing it there "would restore a real defect to fix a reporting one". Any fix must distinguish the AGENT's environment (marked, deliberately) from a SUITE subprocess the agent launches (which is not a managed worker).
  IF THAT DISTINCTION CANNOT BE DRAWN RELIABLY, SAY SO AND DEFER. The runner cannot always know that a given subprocess is a test run, and a heuristic that guesses wrong in the unsafe direction (unmarking a real lifecycle call) is worse than the reporting defect it fixes. A recorded refusal with the reason is an acceptable outcome for this E-item.
  - Depends on: E-02, E-03
  - Expected outcome: OQ-02 answered against the measured asymmetry; either a runner-side scrub that provably cannot unmark a lifecycle call, or a recorded decision naming why the distinction is undrawable, with a successor PLAN authored either way; never a heuristic that can unmark the agent turn.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE WORKER MARKING ON THE AGENT IS DELIBERATE AND LOAD-BEARING: it is what makes `AW-LIFECYCLE-ROLE-001` fire on a lane agent that tries to finalize its own plan (incident `i452hf`). No fix here may remove it.
- THE MARKING IS A SELECTOR, NOT A BOUNDARY, stated in `ipd_lifecycle`: the measured incident defeated it with `env -u AW_EXECUTION_ROLE`, and closing that needs an OS sandbox or a separate principal. That is `c4yixg` and is out of scope.
- A TEST THAT NEEDS THE MARKING SETS IT ITSELF on an explicit env dict (conftest's stated honest limit), which every such test already does. The guard test is the sole exception because its subject IS the ambient value, and that exception is this plan's defect.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `tests/test_worker_role_refusal.py::ChildEnvWorkerRoleTests::test_driver_own_process_is_not_worker_role` | The guard reads the AMBIENT environment, which conftest pops at import, so it cannot fail for any ambient value. It passes while holding the exact value it forbids. | run with `AW_EXECUTION_ROLE=worker` on the command line: `1 passed` |
| F-2 | HIGH (narrowing) | `conftest.py` | `8bif6g`/`t49rmq` are FIXED: the marking no longer changes suite results. They should be closed citing the scrub, not graduated. | `tests/test_ipd_lifecycle_cli.py`: `89 passed` both with and without `AW_EXECUTION_ROLE=worker` |
| F-3 | HIGH | `oc_runipd`, `agy_runipd`, `runner_shared` | Both runners still export the marking into the agent turn and nothing scrubs it for a suite invocation, so `8bif6g`'s evidence harm is closed only for repos shipping this conftest. A managed target repo is still exposed. | both hosts set `child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER`; no scrub found in `runner_shared` |
| F-4 | MED | `conftest.py` | The scrub is an UNASSERTED invariant that 31 tests depend on for their meaning; deleting the `pop` line would silently restore the masked failures. | no test found asserting the pop or its effect |
| F-5 | INFO | `ipd_lifecycle` finalize role check | The `env -u` bypass (`c4yixg`) remains open by design, and the code records that agents reached for `env -u` BECAUSE lifecycle tests failed in a lane. The scrub removes that motivation, strengthening `c4yixg` without closing it. | "the env marker is a SELECTOR, not a boundary ... DEFEATED it with `env -u AW_EXECUTION_ROLE`" |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the scrub's effectiveness, the guard's vacuity, and the runners' continued export.
2. E-02 moves the guard to a seam the scrub does not pre-clean, so it can fail again without weakening its assertion.
3. E-03 asserts the scrub itself, closing the unasserted-invariant hole E-02 otherwise deepens.
4. E-04 answers OQ-02 on the runner-side scrub, implementing it only if the agent-versus-suite distinction can be drawn safely.

## Deferred / out of scope (with reason)

- RELAXING THE GUARD ASSERTION. Backlog `1uq1cu` names it as the wrong fix and the conftest comment concurs; E-02 must change the SEAM, not the strength.
- REMOVING THE MARKING FROM THE AGENT TURN. Load-bearing for `AW-LIFECYCLE-ROLE-001` and incident `i452hf`.
- THE `env -u AW_EXECUTION_ROLE` BYPASS (`c4yixg`). Documented as needing an OS sandbox or separate principal; explicitly out of scope in the code that hosts the check. Noted here because F-5 changes its context, not its status.
- RE-FIXING `8bif6g`/`t49rmq`. F-2: fixed by the scrub. They are records acts (close citing the conftest), and this plan deliberately does not perform those closes.
- `s0303g` AND `770fkp`, the two already-terminal members of this family (`graduated` and `done` respectively). Their state is correct and nothing here reopens them.

## Scope check

- Over-scope: `conftest.py` is in scope ONLY for E-03's assertion target and any comment correction the decisions require. Do not remove or weaken the scrub itself, which 31 tests now depend on.
- Under-scope: if E-04 resolves that a runner-side scrub belongs here, `agent_workflows/runner_shared.py` and both host drivers become in-scope paths that this plan does NOT currently declare. Declare them before editing, or file the follow-on and leave them alone.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_worker_role_refusal.py` and the new scrub-assertion module.
- E-02's restored guard MUST be demonstrated FAILING under a deliberate mutation; a guard that has never been seen to fail is the exact defect this plan exists to fix, and shipping a second one would be worse than leaving the first.
- E-03's test MUST be demonstrated FAILING with the conftest scrub removed locally.
- The affected families (`tests/test_ipd_lifecycle_cli.py` and the begin/finalize, worktree-isolation, fail-closed-integration and backlog-close-in-lane modules the conftest names) must stay green, proving the scrub was not disturbed.

## Spec / documentation sync

- The conftest comment block's "HONEST LIMITS" should record that the guard test is the one case its escape hatch does not cover, since that gap is what F-1 measures.
- If E-04 lands a runner-side scrub, spec `25kzda` may need to record what environment a suite invocation receives; declare that `.spec.md` in `- Scope-Paths:` before editing, per the spec-amendment rule. No spec edit is anticipated otherwise.

## Open questions

### OQ-01: At which seam should the driver's unmarked-environment property be tested?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires a demonstrated-failing guard whichever seam is chosen, and it also permits the honest outcome of converting the test if the ambient property is genuinely untestable after the scrub. The candidates are: assert over the driver's env-CONSTRUCTION function (testable, deterministic, and independent of the ambient value, which is why it is preferred), or spawn a subprocess with a deliberately marked environment and assert the driver refuses there (closest to the real incident, but slower and it tests the refusal rather than the driver's own cleanliness). What must NOT happen is a third option of asserting the ambient value with a skip when it is absent, which is a guard that silently does nothing in the common case.

### OQ-02: Should the runners scrub the marking for a suite invocation, so a managed target repo is protected too?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking; E-04 permits a recorded refusal with its reason. The case FOR: `8bif6g`'s harm is false measured evidence, the conftest fix only protects repositories that ship that conftest, and a managed target repo whose tests read the ambient role is still exposed (F-3), so today the fix sits in the wrong layer to help anyone but us. The case AGAINST: the runner cannot reliably tell a test subprocess from a lifecycle call, and a heuristic that unmarks a real `aw ipd begin`/`finalize` would restore incident `i452hf` in order to fix a reporting defect, which the conftest's own comment already rejects as the wrong trade. Escalated to the maintainer because it is a runner behavior change touching a load-bearing safety marker on both hosts.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted identical counts for an affected module with and without `AW_EXECUTION_ROLE=worker`; pasted `1 passed` for the guard test run WITH the marking set; and the quoted runner lines showing the marking is still exported with no suite-side scrub.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the restored guard pasted FAILING under a deliberate mutation of the driver's env construction, and PASSING unmutated; plus a statement of which OQ-01 seam was chosen and why. A guard not demonstrated failing does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new test pasted FAILING with conftest's `pop` removed locally and PASSING with it restored; plus the test docstring showing the self-referential limit is stated.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: OQ-02's recorded answer; if implemented, proof that a lifecycle call cannot be unmarked by the new path (a test asserting the agent turn is still marked); if refused, the named reason plus the successor PLAN's id6. Either way, the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
