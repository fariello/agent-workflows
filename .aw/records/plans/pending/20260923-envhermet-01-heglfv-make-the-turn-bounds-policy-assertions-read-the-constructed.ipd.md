# IPD: Make the turn-bounds policy assertions read the constructed child env instead of the ambient one

- Date: 2026-09-23
- Kind: child
- Concern: ONE NON-HERMETIC ASSERTION HAS BEEN FILED AS A BACKLOG ITEM TWENTY-THREE TIMES, AND IT IS LIVE AT HEAD `22cf67d9`. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts `policy_key not in main_env` for a NON-isolated turn, where `main_env` is the environment the runner would hand a child. When `OPENCODE_CONFIG_CONTENT` is already present in the AMBIENT environment it is inherited into that constructed env, so the assertion fails for a reason that has nothing to do with the code under test.
  MEASURED BOTH WAYS. Bare: `144 passed`. With `OPENCODE_CONFIG_CONTENT` set in the environment: `1 failed, 143 passed`, the failure being exactly that test with `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`. So the defect reproduces deterministically and the trigger is a single environment variable.
  THE TRIGGER IS THE RUNNER'S OWN NORMAL BEHAVIOR, WHICH IS WHY IT KEEPS BEING REDISCOVERED. `run_opencode` always sets `OPENCODE_CONFIG_CONTENT` for a turn, so every agent executing a plan inside a lane runs the suite with that variable ambient and sees this failure. Twenty-three separate items describe it in near-identical words (`06ngnx`, `1ixbnr`, `3q0fcm`, `4vn040`, `7p08pw`, `8dp3zp`, `cfgj8s`, `hco0mk`, `j08jky`, `j8gcyq`, `mepbmp`, `ph0wlt`, `pmmnuw`, `pzbcto`, `q8s57d`, `r67fl1`, `rfu7mk`, `se8vsp`, `tem4g9`, `tng9xf`, `to77re`, `wx72g3`, `zgndje`), which is the strongest possible evidence that the agents hitting it cannot tell it from a real regression.
  THE HARM IS TO EVIDENCE, AND IT CUTS BOTH WAYS. An agent following the execution contract measures a baseline and compares failure sets by node id. This failure appears in BOTH measurements and cancels, so the usual outcome is a wasted investigation. The dangerous outcome is the other one: an agent that reads the failure as real either "fixes" a correct test or reports a regression that does not exist, and an agent that learns to ignore a red node in this file will ignore a genuine one next to it.
  THE ASSERTION ITSELF IS CORRECT AND MUST SURVIVE. `R4.1` genuinely requires that a non-isolated turn receive NO denial policy, because it works in the main checkout where an external-directory denial would refuse its ordinary work, and the test's own comment says exactly that. The defect is that the test reads a value the ambient environment can supply, not that it asserts the wrong thing. Several of the twenty-three items propose "make the test tolerate the variable", which would DELETE the `R4.1` guarantee; that is the wrong fix and this plan forbids it.
- Scope: Make the assertion measure what the runner CONSTRUCTS rather than what the process inherited, so it is true or false for code reasons only. IN: (a) make the non-isolated policy assertion hermetic against an ambient `OPENCODE_CONFIG_CONTENT`, per OQ-01, without weakening what `R4.1` asserts; (b) audit the rest of `tests/test_turn_bounds.py` for the same ambient-read pattern, since twenty-three filings name several different test methods and the family may be wider than one assertion; (c) prove hermeticity by running the file with the variable set. OUT: the duplicate-filing half, which is child 02 (`fwgq2u`); removing the variable from `run_opencode`, which is load-bearing for a turn's configuration; and the conftest-style session scrub used for `AW_EXECUTION_ROLE`, which is rejected under OQ-01 for a reason recorded there.
- Scope-Paths: tests/test_turn_bounds.py
- Item-Dependencies: none
- Status: to-review
- Set: envhermet
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: heglfv
- From-Backlog: mepbmp
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the twenty-three-item turn-bounds family. `- From-Backlog:` names `mepbmp` as the representative carrier (it states the mechanism most precisely: the assertion expects no policy but `run_opencode` now always sets the variable); the full list is enumerated in the Concern so no filing is lost. `- Blocks-Release: next` is INHERITED, every member carries it.
  MEASURED BOTH STATES rather than trusting any filing: bare `144 passed`, and with `OPENCODE_CONFIG_CONTENT` set `1 failed, 143 passed` with the failing assertion pasted. The trigger is one variable and the failure is deterministic.
  THE IMPORTANT AUTHORING DECISION is that the assertion must NOT be relaxed. Several of the twenty-three items suggest tolerating the variable, which would delete the `R4.1` guarantee the test exists to defend; the fix belongs at the SEAM (what the test reads), which is the same lesson `rolevac` `8i0xa7` records for the role guard.

## Goal

Make the turn-bounds policy assertions depend only on the environment the runner constructs, so the file is green on any machine and red only for a real defect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce and scope the pattern

- [ ] E-01 REPRODUCE THE FAILURE AND FIND EVERY INSTANCE OF THE PATTERN, before editing.
  REPRODUCE: run `tests/test_turn_bounds.py` bare, then with `OPENCODE_CONFIG_CONTENT` set, and paste both summaries. At authoring: `144 passed` versus `1 failed, 143 passed`.
  AUDIT THE WHOLE FILE, because the twenty-three filings name SEVERAL method names and this plan should not fix one assertion and leave siblings. Find every assertion whose subject is an environment the test did not fully construct, and list them. If only one exists, say so; the filings' varied wording may simply be varied descriptions of one test.
  CONFIRM THE TRIGGER'S SOURCE: verify `run_opencode` sets `OPENCODE_CONFIG_CONTENT` for a turn, so the reader understands the ambient value is normal rather than an odd local setup.
  DO NOT ASSUME THE OTHER `test_turn_bounds` FAILURES SHARE THIS CAUSE. Some filings mention `AW_EXECUTION_ROLE` instead; that is `rolevac`'s subject and already scrubbed. Separate the two rather than folding them together.
  - Depends on: none
  - Expected outcome: both runs pasted, a complete list of ambient-reading assertions in the file, the trigger's source confirmed, and any filing whose cause is actually the role variable identified as out of scope.
  - Execution state: pending

### Task group 2: fix the seam

- [ ] E-02 MAKE THE ASSERTIONS HERMETIC, per OQ-01, WITHOUT WEAKENING `R4.1`.
  THE GUARANTEE MUST SURVIVE UNCHANGED: a non-isolated turn must receive NO denial policy. Do not relax the assertion to "policy absent OR inherited", and do not delete it. Several of the twenty-three items propose exactly that, and it would convert a live guarantee into a comment.
  FIX WHAT THE TEST READS. The question `R4.1` asks is whether the runner ADDS the policy, which is answerable from the constructed env compared against its baseline, independently of what the parent process happened to carry.
  IF YOU CHOOSE TO CONTROL THE ENVIRONMENT INSTEAD, SCOPE IT TO THE TEST. A session-wide scrub is rejected here (OQ-01) because `rolevac` `8i0xa7` is currently repairing a guard that a session scrub made VACUOUS; repeating that pattern in the same repository, in the same week, would be a self-inflicted repeat of a known defect.
  THE FIXED TEST MUST STILL BE ABLE TO FAIL. After the change, demonstrate it failing under a deliberate mutation that makes the runner add the policy to a non-isolated turn. A hermetic test that cannot fail is the `rolevac` defect, not a fix.
  - Depends on: E-01
  - Expected outcome: the file passes with `OPENCODE_CONFIG_CONTENT` set and unset; `R4.1`'s assertion is unchanged in strength; the test is demonstrated still able to fail; no session-wide scrub introduced.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-03 PROVE HERMETICITY AGAINST THE REAL TRIGGER, not just an unset variable. The whole family exists because the file was green for humans and red for agents.
  RUN IT THE WAY AN AGENT DOES: with `OPENCODE_CONFIG_CONTENT` set to a realistic value, and state the result. Also run the bare suite, since the file must not have become dependent on the variable's ABSENCE either.
  ASSERT THE PROPERTY IN THE TEST SUITE ITSELF if E-02's mechanism admits it, so a future edit that reintroduces an ambient read is caught rather than rediscovered by a twenty-fourth filing.
  - Depends on: E-02
  - Expected outcome: pasted green results with the variable set and unset; where the mechanism allows, a guard against reintroducing an ambient read.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A TEST THAT NEEDS AN ENVIRONMENT MUST CONSTRUCT IT EXPLICITLY, which is the stated convention in the root `conftest.py`'s discussion of the role variable: "a test that needs the marking must set it ITSELF, on an explicit env dict passed to the code under test".
- A SESSION-WIDE SCRUB CAN MAKE A GUARD VACUOUS. That is being repaired right now in `rolevac` `8i0xa7`, where the `AW_EXECUTION_ROLE` scrub left `test_driver_own_process_is_not_worker_role` unable to fail. This plan must not create the same debt.
- `run_opencode` ALWAYS SETS `OPENCODE_CONFIG_CONTENT` for a turn, so the ambient value is the NORMAL condition for any agent-run suite, not an unusual local state.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `test_the_permission_policy_by_contrast_IS_isolation_scoped` | Asserts `policy_key not in main_env` where the constructed env INHERITS the ambient `OPENCODE_CONFIG_CONTENT`, so it fails for environmental reasons. | bare `144 passed`; with the variable set `1 failed, 143 passed` on `assert 'OPENCODE_CONFIG_CONTENT' not in {...}` |
| F-2 | HIGH | `run_opencode` | The trigger is the runner's own normal behavior, so every lane agent that runs the suite sees this failure; that is why twenty-three separate items describe it. | 23 enumerated backlog items, near-identical wording |
| F-3 | HIGH | the twenty-three filings | Several propose making the test TOLERATE the variable, which would delete the `R4.1` guarantee that a non-isolated turn gets no denial policy. The assertion is correct; only its input is wrong. | the test's own comment: "a non-isolated turn must get NO denial policy ... where external-directory denial would refuse its ordinary work (R4.1)" |
| F-4 | MED | scope separation | Some filings attribute the failure to `AW_EXECUTION_ROLE` instead, which is `rolevac`'s subject and already scrubbed in `conftest.py`. Conflating the two would produce a fix aimed at the wrong variable. | `rolevac` `8i0xa7`; the conftest scrub |

## Proposed changes (ordered, validatable)

1. E-01 reproduces both states and enumerates every ambient-reading assertion in the file.
2. E-02 makes the assertions depend on the constructed env, preserving `R4.1` and keeping the test able to fail.
3. E-03 proves green with the variable set and unset, and guards against reintroduction where possible.

## Deferred / out of scope (with reason)

- THE DUPLICATE-FILING HALF. Child 02 (`fwgq2u`) owns the `aw backlog new` near-duplicate guard; fixing the test without it leaves the next such defect free to be filed twenty times again.
- REMOVING `OPENCODE_CONFIG_CONTENT` FROM `run_opencode`. It carries the turn's configuration; removing it to satisfy a test would break the runner to fix a test.
- A SESSION-WIDE CONFTEST SCRUB. Rejected under OQ-01: `rolevac` `8i0xa7` is repairing exactly that debt for the role variable, and repeating it would be a known self-inflicted defect.
- THE `AW_EXECUTION_ROLE`-CAUSED FAILURES some filings describe. Already scrubbed; `rolevac` owns the remaining vacuity.

## Scope check

- Over-scope: `tests/test_turn_bounds.py` is the only declared path. Do not edit `lane_containment` or either runner to make a test pass; if the test cannot be made hermetic without a production change, STOP and report rather than widening.
- Under-scope: if E-01 finds ambient-reading assertions in OTHER test files, do not silently fix them here; report them, since they are outside this plan's declared path and may belong to a sibling plan.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- `tests/test_turn_bounds.py` must be pasted GREEN in two conditions: with `OPENCODE_CONFIG_CONTENT` set and with it unset.
- E-02's fixed test MUST be demonstrated FAILING under a deliberate mutation making a non-isolated turn carry the policy. Per F-3 and the `rolevac` precedent, a hermetic test that cannot fail is not a fix.

## Spec / documentation sync

- `R4.1` lives in a spec governing turn bounds and lane containment. This plan does not change the requirement, so no amendment is expected; if E-02 reveals the spec's wording is what invites the ambient reading, declare that `.spec.md` in `- Scope-Paths:` before amending it, per the spec-amendment rule.

## Open questions

### OQ-01: Construct-and-compare, or scope the environment to the test?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires `R4.1` preserved and the test demonstrably still able to fail under either mechanism. CONSTRUCT-AND-COMPARE (assert on what the runner ADDS relative to a controlled baseline) is preferred: it answers the requirement's actual question, it is immune to any ambient value, and it cannot make the test vacuous. SCOPING THE ENVIRONMENT (clear the variable for this test only, via a context manager or monkeypatch) is simpler and acceptable, but it asserts absence in an environment the test forced, which is one step further from what production does. A SESSION-WIDE SCRUB is REJECTED, not merely dispreferred: it is the mechanism that made `rolevac` `8i0xa7`'s guard vacuous, and adopting it here would knowingly create the same debt.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: both runs pasted (bare and with the variable set), the enumerated list of ambient-reading assertions, confirmation that `run_opencode` sets the variable, and any filing reassigned to the role-variable cause.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the file pasted green with the variable SET; a diff or quote showing `R4.1`'s assertion was not weakened; and the test pasted FAILING under a deliberate mutation that adds the policy to a non-isolated turn.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted green results in both environment conditions, plus the bare `python3 -m pytest` summary line; and, if a reintroduction guard was added, the test pasted failing when an ambient read is restored.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
