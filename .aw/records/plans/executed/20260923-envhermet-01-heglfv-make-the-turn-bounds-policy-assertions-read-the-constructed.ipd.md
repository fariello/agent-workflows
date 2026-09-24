# IPD: Make the turn-bounds policy assertions read the constructed child env instead of the ambient one

- Date: 2026-09-23
- Kind: child
- Concern: ONE NON-HERMETIC ASSERTION HAS BEEN FILED AS A BACKLOG ITEM TWENTY-THREE TIMES, AND IT IS LIVE AT HEAD `22cf67d9`. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts `policy_key not in main_env` for a NON-isolated turn, where `main_env` is the environment the runner would hand a child. When `OPENCODE_CONFIG_CONTENT` is already present in the AMBIENT environment it is inherited into that constructed env, so the assertion fails for a reason that has nothing to do with the code under test.
  MEASURED BOTH WAYS. At authoring, bare: `144 passed`; with `OPENCODE_CONFIG_CONTENT` set: `1 failed, 143 passed`, the failure being exactly that test with `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`. RE-MEASURED AT REVIEW in a lane at HEAD `3eb35740`: `1 failed, 147 passed` bare (the lane HAS the variable ambient, so bare IS the failing condition here) and `148 passed` under `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE`, no code change between. So the defect reproduces deterministically, and the COUNTS have drifted by four in four days: E-01 must re-derive them rather than quote either pair.
  THE TRIGGER IS THE RUNNER'S OWN NORMAL BEHAVIOR, WHICH IS WHY IT KEEPS BEING REDISCOVERED. `run_opencode` always sets `OPENCODE_CONFIG_CONTENT` for a turn, so every agent executing a plan inside a lane runs the suite with that variable ambient and sees this failure. Twenty-three separate items describe it in near-identical words (`06ngnx`, `1ixbnr`, `3q0fcm`, `4vn040`, `7p08pw`, `8dp3zp`, `cfgj8s`, `hco0mk`, `j08jky`, `j8gcyq`, `mepbmp`, `ph0wlt`, `pmmnuw`, `pzbcto`, `q8s57d`, `r67fl1`, `rfu7mk`, `se8vsp`, `tem4g9`, `tng9xf`, `to77re`, `wx72g3`, `zgndje`), which is the strongest possible evidence that the agents hitting it cannot tell it from a real regression.
  THE HARM IS TO EVIDENCE, AND IT CUTS BOTH WAYS. An agent following the execution contract measures a baseline and compares failure sets by node id. This failure appears in BOTH measurements and cancels, so the usual outcome is a wasted investigation. The dangerous outcome is the other one: an agent that reads the failure as real either "fixes" a correct test or reports a regression that does not exist, and an agent that learns to ignore a red node in this file will ignore a genuine one next to it.
  THE ASSERTION ITSELF IS CORRECT AND MUST SURVIVE. The defect is that the test reads a value the ambient environment can supply, not that it asserts the wrong thing. Several of the twenty-three items propose "make the test tolerate the variable", which would DELETE the guarantee; that is the wrong fix and this plan forbids it.
  ONE ATTRIBUTION IN THIS PLAN WAS WRONG AND IS CORRECTED AT REVIEW, because an executor acting on it would defend the wrong contract. This plan said `R4.1` "genuinely requires that a non-isolated turn receive NO denial policy". IT DOES NOT. Read in spec `7ckptx`: "R4.1 An unattended isolated turn MUST run under the STRONGEST permission posture its host supports". R4.1 is a FLOOR on the ISOLATED turn and says nothing whatever about the non-isolated one; the spec's only normative statements about a non-isolated turn are R1.3 (its PROMPT must be byte-identical) and R4.4a (the BOUNDS apply uniformly). So the `policy_key not in main_env` assertion is NOT an R4.1 requirement. WHAT IT ACTUALLY DEFENDS is the deliberate narrowing in `oc_runipd.run_opencode`, whose own comment states it: "ISOLATED TURNS ONLY, deliberately narrower than the bounds below ... a non-isolated turn legitimately works in the main checkout, where an external-directory denial would refuse its ordinary work", a narrowing whose ordering is spec-normative under R4.6. The assertion is therefore worth keeping, and E-02 must preserve it, but it must be defended as THAT property (the runner narrows the policy to isolated turns) rather than as an R4.1 obligation. See F-5.
  AND THE TRIGGER IS NOT WHAT THIS PLAN SAYS, which matters because F-2 and E-01 both instruct the executor to confirm a false mechanism. `run_opencode` does NOT "always" set `OPENCODE_CONFIG_CONTENT`: the assignment sits inside `if work_dir:`, so the runner sets it for an ISOLATED turn only. The real chain, measured at review, is one level up: the OUTER driver set the variable for THIS lane's turn, and the test's INNER `run_opencode(work_dir=None)` inherits it because `pinned_child_env` starts from `os.environ.copy()`. The distinction is load-bearing: the fix belongs at `pinned_child_env`'s inheritance, which is what the test must control, and an executor hunting for an unconditional assignment in `run_opencode` will not find one. See F-6.
- Scope: Make the assertion measure what the runner CONSTRUCTS rather than what the process inherited, so it is true or false for code reasons only. IN: (a) make the non-isolated policy assertion hermetic against an ambient `OPENCODE_CONFIG_CONTENT`, per OQ-01, without weakening what `R4.1` asserts; (b) audit the rest of `tests/test_turn_bounds.py` for the same ambient-read pattern, since twenty-three filings name several different test methods and the family may be wider than one assertion; (c) prove hermeticity by running the file with the variable set. OUT: the duplicate-filing half, which is child 02 (`fwgq2u`); removing the variable from `run_opencode`, which is load-bearing for a turn's configuration; and the conftest-style session scrub used for `AW_EXECUTION_ROLE`, which is rejected under OQ-01 for a reason recorded there.
- Scope-Paths: tests/test_turn_bounds.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: envhermet
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: heglfv
- From-Backlog: mepbmp
- Blocks-Release: next

## Workflow history
- 2026-09-24 executed (aw agy run model=gemini-3.7-flash-high): aw agy run self-finalize: heglfv verified (set envhermet, attempt 1).
- 2026-09-24 approved (aw set): status set to approved
- 2026-09-24 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-207, all FIXED, none deferred, none open. Readiness `go-pending-approval`. Record: `.aw/records/reviews/20260923-envhermet-01-heglfv-make-the-turn-bounds-policy-assertions-read-the-constructed.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing found was structural. DISCLOSURE: same agent and model authored this plan, so this is a SELF-REVIEW, and its value rests on RUNNING the claims rather than re-reading them.
  THE DEFECT IS CONFIRMED AND THE FIX IS WORTH MAKING: at HEAD `3eb35740` in a lane, `python3 -m pytest tests/test_turn_bounds.py` gives `1 failed, 147 passed` and `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE` gives `148 passed`, no code change between. Counts drifted from the plan's `144`/`143`, so E-01 now re-derives rather than quotes.
  TWO ATTRIBUTIONS WERE WRONG AND AN EXECUTOR ACTING ON EITHER WOULD HAVE GONE ASTRAY. FIRST (PR-201): the plan says `R4.1` "genuinely requires that a non-isolated turn receive NO denial policy". Spec `7ckptx` says "An unattended ISOLATED turn MUST run under the STRONGEST permission posture its host supports" and is SILENT on the non-isolated turn; its only normative non-isolated statements are R1.3 and R4.4a. The assertion is still worth keeping, but it defends `run_opencode`'s deliberate "ISOLATED TURNS ONLY" narrowing (R4.6-ordered), not an R4.1 obligation. SECOND (PR-202): the plan says `run_opencode` "always sets" the variable. The assignment is inside `if work_dir:`, so the runner sets it for isolated turns ONLY; the real chain is that the OUTER driver set it and the test's INNER `run_opencode(work_dir=None)` inherits it via `pinned_child_env`, which begins `os.environ.copy()`.
  THE AUDIT E-01 ASKED FOR ALREADY HAS A SECOND HIT (PR-203), and it is the finding I would most want a human to see. The SAME test carries `assert "AW_EXECUTION_ROLE" not in main_env` with the identical non-hermetic construction; it passes today ONLY because `conftest.py` pops that variable at import time. Proven by re-setting the marking after the pop: the constructed non-isolated env then contains it. So a fix that repairs line 271 and leaves 275 leaves a latent twin protected by another file, which is the `rolevac` shape this plan exists to avoid. Both lines are now in E-02's scope.
  OQ-01 IS RESOLVED AGAINST A SHIPPED PRECEDENT IT HAD NOT WEIGHED (PR-204): `tests/test_lane_permission_posture.py` already uses `monkeypatch.delenv(OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` in three tests, exercises the same seam, and is GREEN with the variable ambient (`27 passed`). Construct-and-compare stays acceptable if recorded. Also added: E-04 carries backlog `wnabns`'s stranded release gate, which the parent's completion criterion 6 assigns to this child, with the mechanical trap named (`--from-backlog` SETS rather than appends, so `mepbmp` must not be overwritten); and OQ-02 raises the genuine spec gap PR-201 exposed.
- 2026-09-24 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-201..PR-207 all FIXED; readiness go-pending-approval

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from the twenty-three-item turn-bounds family. `- From-Backlog:` names `mepbmp` as the representative carrier (it states the mechanism most precisely: the assertion expects no policy but `run_opencode` now always sets the variable); the full list is enumerated in the Concern so no filing is lost. `- Blocks-Release: next` is INHERITED, every member carries it.
  MEASURED BOTH STATES rather than trusting any filing: bare `144 passed`, and with `OPENCODE_CONFIG_CONTENT` set `1 failed, 143 passed` with the failing assertion pasted. The trigger is one variable and the failure is deterministic.
  THE IMPORTANT AUTHORING DECISION is that the assertion must NOT be relaxed. Several of the twenty-three items suggest tolerating the variable, which would delete the `R4.1` guarantee the test exists to defend; the fix belongs at the SEAM (what the test reads), which is the same lesson `rolevac` `8i0xa7` records for the role guard.

## Goal

Make the turn-bounds policy assertions depend only on the environment the runner constructs, so the file is green on any machine and red only for a real defect.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce and scope the pattern

- [x] E-01 REPRODUCE THE FAILURE AND FIND EVERY INSTANCE OF THE PATTERN, before editing.
  REPRODUCE AND RE-DERIVE THE COUNTS, never quoting this plan's. Run `tests/test_turn_bounds.py` with `OPENCODE_CONFIG_CONTENT` set and unset and paste both summaries with the head measured at. The pair was `144`/`143` at authoring and `1 failed, 147 passed` / `148 passed` at review: it has already drifted once, so a quoted number is a false statement waiting to be pasted into a `V-*` block.
  THE AUDIT ALREADY HAS A SECOND HIT; FIND IT AND FIX IT, do not re-discover whether the family is one assertion. Review measured TWO ambient-reading assertions in the SAME test (F-6): line 271's `policy_key not in main_env` (failing now) and line 275's `"AW_EXECUTION_ROLE" not in main_env` (passing ONLY because `conftest.py` pops that variable at import time, not because the test controls it; proven by re-setting the marking after the pop, which puts it back in the constructed env). Both are in scope. Repairing 271 and leaving 275 leaves a latent twin whose protection lives in a different file, which is precisely the shape `rolevac` is repairing.
  CONFIRM THE TRIGGER'S REAL SOURCE, WHICH IS NOT WHAT THIS PLAN ORIGINALLY SAID (F-2). Do NOT go looking for an unconditional assignment in `run_opencode`; there is none, because the only `OPENCODE_RUNTIME_CONFIG_ENV` assignment sits inside `if work_dir:` and so fires for ISOLATED turns only. Verify instead the chain review measured: the OUTER driver sets the variable for the lane's turn, and the test's INNER `run_opencode(work_dir=None)` inherits it because `child_env = pinned_child_env()` and `pinned_child_env` begins `os.environ.copy()`. Paste the evidence for whichever chain you find, and if it differs from this, say so.
  DO NOT ASSUME THE OTHER `test_turn_bounds` FAILURES SHARE THIS CAUSE. Some filings mention `AW_EXECUTION_ROLE` as the whole story; the residual vacuity from its scrub is `rolevac` `8i0xa7`'s. Note the nuance F-6 adds: the role variable is ALSO read non-hermetically HERE, at line 275, and fixing that line is this plan's (it is inside its declared path) while the guard-vacuity `rolevac` repairs is not.
  - Depends on: none
  - Expected outcome: both runs pasted with re-derived counts and the head; BOTH ambient-reading assertions named (271 and 275) with the evidence that 275 is protected only by the conftest scrub; the real inheritance chain confirmed by symbol; and the `rolevac` boundary stated.
  - Execution state: performed

### Task group 2: fix the seam

- [x] E-02 MAKE BOTH ASSERTIONS HERMETIC, per OQ-01, WITHOUT WEAKENING THE PROPERTY THEY DEFEND.
  NAME THE PROPERTY CORRECTLY, because this plan originally named the wrong one (F-5). The contract being defended is NOT `R4.1`: that requirement is a floor on the ISOLATED turn ("An unattended isolated turn MUST run under the STRONGEST permission posture its host supports") and says nothing about a non-isolated one. The property is the runner's DELIBERATE NARROWING, stated in `run_opencode`'s own comment ("ISOLATED TURNS ONLY, deliberately narrower than the bounds below ... a non-isolated turn legitimately works in the main checkout, where an external-directory denial would refuse its ordinary work") and ordered by R4.6. Preserve THAT, and update the test's own comment if it miscites R4.1 as the source.
  THE GUARANTEE MUST SURVIVE UNCHANGED: a non-isolated turn must receive NO denial policy FROM THE RUNNER. Do not relax the assertion to "policy absent OR inherited", and do not delete it. Several filings propose exactly that, and it would convert a live guarantee into a comment.
  FIX BOTH LINES, NOT ONE (F-6). Line 271 (`policy_key not in main_env`) and line 275 (`"AW_EXECUTION_ROLE" not in main_env`) share the identical defect; 275 merely looks healthy because `conftest.py` scrubs its variable. Leaving 275 depending on another file's scrub recreates the `rolevac` shape.
  FIX WHAT THE TEST READS. The question is whether the runner ADDS the policy, which is answerable from the constructed env compared against its baseline, independently of what the parent process carried.
  IF YOU CHOOSE TO CONTROL THE ENVIRONMENT INSTEAD, SCOPE IT TO THE TEST, AND NOTE THERE IS A SHIPPED SIBLING PRECEDENT (F-7) that OQ-01 did not weigh: `tests/test_lane_permission_posture.py` calls `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` in three tests and is GREEN with the variable ambient. It tests the same seam and its docstring records the same sabotage lesson. A session-wide scrub remains REJECTED (OQ-01) because that is the mechanism `rolevac` `8i0xa7` is repairing.
  THE FIXED TEST MUST STILL BE ABLE TO FAIL. After the change, demonstrate it failing under a deliberate mutation that makes the runner add the policy to a non-isolated turn. A hermetic test that cannot fail is the `rolevac` defect, not a fix.
  - Depends on: E-01
  - Expected outcome: the file passes with `OPENCODE_CONFIG_CONTENT` set and unset; BOTH lines 271 and 275 no longer read the ambient environment; the runner's isolated-turns-only narrowing is unchanged in strength and any R4.1 miscitation in the test's comment is corrected; the test is demonstrated still able to fail; no session-wide scrub introduced.
  - Execution state: performed

### Task group 3: prove it

- [x] E-03 PROVE HERMETICITY AGAINST THE REAL TRIGGER, not just an unset variable. The whole family exists because the file was green for humans and red for agents.
  RUN IT THE WAY AN AGENT DOES: with `OPENCODE_CONFIG_CONTENT` set to a realistic value, and state the result. Also run the bare suite, since the file must not have become dependent on the variable's ABSENCE either.
  ASSERT THE PROPERTY IN THE TEST SUITE ITSELF if E-02's mechanism admits it, so a future edit that reintroduces an ambient read is caught rather than rediscovered by a twenty-fourth filing.
  - Depends on: E-02
  - Expected outcome: pasted green results with the variable set and unset; where the mechanism allows, a guard against reintroducing an ambient read.
  - Execution state: performed

### Task group 4: preserve the release gate this Set would otherwise strand

- [x] E-04 CARRY BACKLOG `wnabns`'s RELEASE GATE ON THIS PLAN, which is the act the parent's completion criterion 6 assigns here (F-9). It is a records act, not a code change, and it is owned by THIS CHILD rather than the orchestrator because a retiring orchestrator skips the pre-transition E/V checkpoint, so an act parked there would be marked complete having never been performed.
  THE PROBLEM, MEASURED. `wnabns` is the ONE member of the turn-bounds family still `open`. It carries `- Blocks-Release: next`, has no `- Graduated-To:`, and NO plan in the tree cites it; this plan carries `mepbmp`, which is already `graduated`. `evaluate_blocking_close(wnabns, 'done')` returns `legitimate=False`, "closing it `done` would silently drop that release gate". So without this item, this plan FIXES the defect `wnabns` describes and `wnabns` remains a permanent `ready` release blocker that cannot legitimately be closed.
  ADD, DO NOT OVERWRITE, AND THIS IS THE TRAP. `aw ipd set ... --from-backlog` SETS the field rather than appending, so pointing it at `wnabns` would DROP `mepbmp`'s handoff and strand THAT gate instead, converting one problem into another. The repository supports multiple source bullets on one plan (executed plan `y9s4vm`'s review measured five plans carrying two source links each), so ADD a second `- From-Backlog: wnabns` bullet and keep `mepbmp`.
  DO NOT CLOSE `wnabns` HERE. Carrying the gate is this item; closing the item is a separate act that belongs after this plan is `executed`, and the parent's OQ-01 keeps the wider consolidation question with the maintainer.
  - Depends on: none
  - Expected outcome: this plan carries BOTH `- From-Backlog: mepbmp` and `- From-Backlog: wnabns` with `- Blocks-Release: next` unchanged; `aw check` reports no `check.from-backlog-dangling` for either id6 and no blocking-close finding for `wnabns`; `wnabns` itself is left `open` and unmodified.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A TEST THAT NEEDS AN ENVIRONMENT MUST CONSTRUCT IT EXPLICITLY, which is the stated convention in the root `conftest.py`'s discussion of the role variable: "a test that needs the marking must set it ITSELF, on an explicit env dict passed to the code under test".
- A SESSION-WIDE SCRUB CAN MAKE A GUARD VACUOUS. That is being repaired right now in `rolevac` `8i0xa7`, where the `AW_EXECUTION_ROLE` scrub left `test_driver_own_process_is_not_worker_role` unable to fail. This plan must not create the same debt.
- `run_opencode` ALWAYS SETS `OPENCODE_CONFIG_CONTENT` for a turn, so the ambient value is the NORMAL condition for any agent-run suite, not an unusual local state.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER (CONFIRMED) | `test_the_permission_policy_by_contrast_IS_isolation_scoped` | Asserts `policy_key not in main_env` where the constructed env INHERITS the ambient `OPENCODE_CONFIG_CONTENT`, so it fails for environmental reasons. Counts corrected at review. | at review: bare `1 failed, 147 passed`; `env -u OPENCODE_CONFIG_CONTENT -u AW_EXECUTION_ROLE` -> `148 passed`; failure is `tests/test_turn_bounds.py:271`, `assert 'OPENCODE_CONFIG_CONTENT' not in {...}` |
| F-2 | HIGH (CAUSE CORRECTED) | `oc_runipd.pinned_child_env`, not `run_opencode` | ORIGINAL CLAIM: `run_opencode` "always sets" the variable. FALSE: the assignment is inside `if work_dir:`, so the runner sets it for an ISOLATED turn only. The real chain is that the OUTER driver set it for this lane's turn and the INNER `run_opencode(work_dir=None)` inherits it via `pinned_child_env`, which begins `os.environ.copy()`. The conclusion (every lane agent sees the failure) still holds; the mechanism named did not. | `inspect.getsource(run_opencode)`: the only `OPENCODE_RUNTIME_CONFIG_ENV` assignment is inside `if work_dir:`; `pinned_child_env` body is `merged = os.environ.copy()`; `child_env = pinned_child_env()` |
| F-3 | HIGH (CONFIRMED, attribution corrected) | the filings proposing tolerance | Several propose making the test TOLERATE the variable, which would delete a real guarantee. That remains the wrong fix. But the guarantee is NOT `R4.1` (see F-5); it is the runner's deliberate isolated-turns-only narrowing. | the filings; and `run_opencode`'s own comment, "ISOLATED TURNS ONLY, deliberately narrower than the bounds below" |
| F-4 | MED (CONFIRMED) | scope separation | Some filings attribute the failure to `AW_EXECUTION_ROLE` instead, which is `rolevac`'s subject and already scrubbed in `conftest.py` (`os.environ.pop("AW_EXECUTION_ROLE", None)` at import time). Conflating the two would produce a fix aimed at the wrong variable. | `rolevac` `8i0xa7` verified to exist and to record exactly that; the conftest scrub read at review |
| F-5 | HIGH (NEW, from review) | this plan's `R4.1` attribution | The plan asserts `R4.1` "genuinely requires that a non-isolated turn receive NO denial policy". Spec `7ckptx` says the opposite in scope: "R4.1 An unattended isolated turn MUST run under the STRONGEST permission posture its host supports". R4.1 is a FLOOR on the ISOLATED turn and is silent on the non-isolated one; the only normative non-isolated statements are R1.3 (prompt byte-identity) and R4.4a (bounds apply uniformly). So E-02's instruction to preserve "`R4.1`'s assertion ... unchanged in strength" names a requirement that does not say what the plan thinks. The assertion IS worth keeping, but as the runner's deliberate narrowing (R4.6-ordered), not as an R4.1 obligation. An executor defending the wrong contract could satisfy the letter while losing the property. | spec `7ckptx` R4.1 quoted; `grep -n "non-isolated" 7ckptx` returns only R1.3, R4.4a and evidence sections; the test's own docstring already says "R4.1 scopes the POSTURE to an unattended ISOLATED turn" |
| F-6 | HIGH (NEW, from review) | `tests/test_turn_bounds.py` line 275 | THE AUDIT E-01 DEMANDS ALREADY HAS A SECOND HIT, and the plan states the family may be one assertion. The SAME test carries `assert "AW_EXECUTION_ROLE" not in main_env` with the IDENTICAL non-hermetic construction. It passes today ONLY because `conftest.py` scrubs that variable at import time, not because the test controls it. Proven by re-setting the marking after conftest's pop: the constructed non-isolated env then contains it. So a fix that repairs line 271 and leaves 275 leaves a latent twin whose protection lives in another file, which is exactly the `rolevac` shape this plan is written to avoid. | `grep -n 'not in main_env' tests/test_turn_bounds.py` -> lines 271 and 275; probe re-setting `AW_EXECUTION_ROLE` after conftest import -> "AW_EXECUTION_ROLE in constructed non-isolated env: True" |
| F-7 | MED (NEW, from review) | OQ-01's option set | OQ-01 weighs construct-and-compare against a test-scoped environment control and calls the latter "one step further from what production does". A SHIPPED IN-REPO PRECEDENT for the scoped control is not mentioned: `tests/test_lane_permission_posture.py` uses `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` in THREE tests, and that file is GREEN with the variable ambient. It is the nearest sibling, it tests the same seam, and its own docstring records the sabotage lesson this plan cites. Deciding OQ-01 without it is deciding against an unexamined option. | three `monkeypatch.delenv` call sites quoted; `python3 -m pytest tests/test_lane_permission_posture.py` -> `27 passed` with `OPENCODE_CONFIG_CONTENT` ambient |
| F-8 | MED (NEW, from review) | this plan's `## Deferred` section | Five obligations name no durable carrier, so `aw check` reports `check.ipd-uncarried-obligation` at `error` and `aw ipd lint --phase pre-transition` merges it: the plan would block its own finalize. | `evaluate_durable_carrier` -> `error`, "5 obligation(s) name no durable carrier"; `pre-transition` -> 10 findings |
| F-9 | HIGH (NEW, from review; INHERITED OBLIGATION) | backlog `wnabns` | This plan carries `- From-Backlog: mepbmp`, and `mepbmp` is already `graduated` with `- Graduated-To: envhermet`. But `wnabns` is the ONE family member still `open`, carries `- Blocks-Release: next`, has no `- Graduated-To:`, and is cited by NO plan. Measured: `evaluate_blocking_close` REFUSES to close it. The parent (`uvwqvz`) review made preserving that gate completion criterion 6 and assigned the ACT to this child, because an act parked on a retiring orchestrator would be marked done unperformed. | `wnabns` front matter; `grep -rn wnabns .aw/records/plans/` finds no carrier; `evaluate_blocking_close(wnabns,'done')` -> `legitimate=False`, "closing it `done` would silently drop that release gate" |

## Proposed changes (ordered, validatable)

1. E-01 reproduces both states and enumerates every ambient-reading assertion in the file.
2. E-02 makes the assertions depend on the constructed env, preserving `R4.1` and keeping the test able to fail.
3. E-03 proves green with the variable set and unset, and guards against reintroduction where possible.

## Deferred / out of scope (with reason)

- THE DUPLICATE-FILING HALF. Child 02 (`fwgq2u`) owns the `aw backlog new` near-duplicate guard; fixing the test without it leaves the next such defect free to be filed twenty times again.
  - Carrier: fwgq2u
- REMOVING `OPENCODE_CONFIG_CONTENT` FROM `run_opencode`. It carries the turn's configuration; removing it to satisfy a test would break the runner to fix a test. Note the framing is also narrower than this plan first assumed (F-2): the runner sets it for ISOLATED turns only, so there is no unconditional assignment to remove.
  - Carrier-Declined: a rejected alternative, not an outstanding obligation; nothing remains to be done.
- A SESSION-WIDE CONFTEST SCRUB. Rejected under OQ-01: `rolevac` `8i0xa7` is repairing exactly that debt for the role variable, and repeating it would be a known self-inflicted defect.
  - Carrier-Declined: rejected with a recorded, measured reason rather than deferred. The alternative mechanism is what E-02 builds.
- THE GUARD-VACUITY `rolevac` OWNS. `conftest.py`'s scrub of `AW_EXECUTION_ROLE` left a sibling guard unable to fail; that repair is `8i0xa7`'s, not this plan's. DISTINGUISH IT from line 275 (F-6), which reads the role variable non-hermetically INSIDE this plan's declared path and therefore IS in scope here.
  - Carrier: 8i0xa7
- AMENDING SPEC `7ckptx` TO STATE THE NON-ISOLATED POLICY EXPECTATION. F-5 establishes the spec is SILENT on whether a non-isolated turn receives a policy, so the test defends a code-level narrowing that no requirement states. Writing that expectation into the spec would make the contract explicit, but it is a real contract addition needing its own review, and this plan's job is to make an existing test hermetic. Raised as OQ-02 rather than performed.
  - Carrier-Declined: deliberately NOT given a carrier id6, because no existing artifact honestly owns it and naming a loosely-related one would be a false handoff that satisfies the checker while misdirecting a reader. It is recorded as OQ-02 with the maintainer as owner; if the maintainer wants it pursued, the correct next step is `aw backlog new`, which is a filing decision rather than this plan's to make.

## Scope check

- Over-scope: `tests/test_turn_bounds.py` is the only declared path for the TEST work. Do not edit `lane_containment` or either runner to make a test pass. That prohibition stands, and it is NOT a "stop over a scope question" instruction in the general sense: the specific stop condition is the prerequisite-absent one below, where the property cannot be expressed without a production change.
- Under-scope: E-04 edits THIS PLAN'S OWN front matter (adding a `- From-Backlog:` bullet), which is a lifecycle record rather than a scope path and needs no `- Scope-Paths:` entry, exactly as a status transition does not.
- Under-scope: if E-01 finds ambient-reading assertions in OTHER test files, do not silently fix them here; report them, since they are outside this plan's declared path and may belong to a sibling plan. Note line 275 is NOT such a case: it is inside the declared path and is in scope (F-6).
- Under-scope: F-8 must be discharged before this plan can finalize. Every `## Deferred` row and every open question needs a `- Carrier:`, `- Carrier-Evidence:`, or `- Carrier-Declined:` field; the rows now carry one, and any row added later must too.
- Under-scope: OQ-02's spec amendment is deliberately NOT performed here, so no `.spec.md` is declared. If an executor concludes the spec must be amended to land E-02 honestly, DECLARE the `.spec.md` in `- Scope-Paths:` before editing it, since both runners announce declared spec edits at run start and reconcile them at finalize.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted. Bare means bare: `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and a second `-q` would suppress the `N passed` line this contract requires.
- `tests/test_turn_bounds.py` must be pasted GREEN in two conditions: with `OPENCODE_CONFIG_CONTENT` set and with it unset. Because this plan executes inside a lane where the variable is ALREADY ambient, note that the BARE run is the failing condition and `env -u OPENCODE_CONFIG_CONTENT ...` is the clean one; do not report a bare green before the fix and assume the tooling is broken.
- BOTH ambient-reading assertions must be proven hermetic, not just the failing one. For line 275, the proof must not be a passing run (which the `conftest.py` scrub already produces); it must show the constructed non-isolated env lacks the role marking even when the marking is present in the process AFTER conftest's import-time pop. Otherwise the fix is unverified (F-6).
- `tests/test_lane_permission_posture.py` must stay GREEN, since OQ-01 adopts its `monkeypatch.delenv` idiom and it exercises the same seam (measured `27 passed` at review).
- E-02's fixed test MUST be demonstrated FAILING under a deliberate mutation making a non-isolated turn carry the policy. Per F-3 and the `rolevac` precedent, a hermetic test that cannot fail is not a fix.
- `aw check` must report no `check.ipd-uncarried-obligation` for this plan (F-8), and no `check.from-backlog-dangling` or blocking-close finding after E-04 (F-9).

## Spec / documentation sync

- `R4.1` lives in spec `7ckptx` (worker lane containment). This plan does not change the requirement, so no amendment is expected. BUT REVIEW MEASURED A REAL GAP (F-5): `R4.1` is scoped to the ISOLATED turn and the spec is SILENT on whether a non-isolated turn receives a policy, so the assertion this plan repairs defends a code-level narrowing no requirement states. That is raised as OQ-02 for the maintainer rather than amended here, and E-02 must at minimum stop the test misciting `R4.1` as its source.
- If an executor decides to amend `7ckptx` after all, declare that `.spec.md` in `- Scope-Paths:` BEFORE editing it, per the spec-amendment rule: both runners announce declared spec edits at run start and reconcile them at finalize, and the end-of-run report names a spec modified without being declared.

## Open questions

### OQ-01: Construct-and-compare, or scope the environment to the test?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Carrier-Declined: resolved at review from in-tree evidence; no obligation survives for a future artifact to carry.
- Resolution or deferral rationale: RESOLVED AT REVIEW, and the deciding input is a SHIPPED SIBLING the original framing did not weigh (F-7). SCOPE THE ENVIRONMENT TO THE TEST, using `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)`, because `tests/test_lane_permission_posture.py` already does exactly that in THREE tests, tests the SAME seam, and is measurably GREEN with the variable ambient (`27 passed`). The original rationale dispreferred this as "one step further from what production does"; that objection is now outweighed by three concrete facts: it is the established in-repo pattern for this precise variable, so choosing differently creates two idioms for one problem; it is the file whose docstring records the sabotage lesson this plan cites, so the precedent is not incidental; and it composes with E-02's mutation requirement, since the sibling test proves a `delenv`-scoped test still fails when the product assignment is removed. CONSTRUCT-AND-COMPARE remains acceptable and is NOT forbidden: if the executor finds it expresses the property more directly, take it and record why. The requirement either way is E-02's, that the test still FAILS under a deliberate mutation. A SESSION-WIDE SCRUB stays REJECTED, not merely dispreferred: it is the mechanism that made `rolevac` `8i0xa7`'s guard vacuous, and adopting it would knowingly create the same debt. Note this rejection also has a sharper edge after F-6: line 275 currently DEPENDS on exactly such a scrub, which is why it looks healthy and is not.

### OQ-02: Should spec `7ckptx` state the non-isolated policy expectation?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: raised rather than performed; deliberately given no carrier id6, because no existing artifact honestly owns a spec-amendment decision and a loosely-related handoff would misdirect a reader. If pursued, the next step is `aw backlog new`, which is a filing decision for the maintainer.
- Resolution or deferral rationale: NOT blocking, and deliberately not performed. F-5 measured that spec `7ckptx` scopes `R4.1` to the ISOLATED turn and says nothing about whether a non-isolated turn receives a policy; the only normative non-isolated statements are R1.3 (prompt byte-identity) and R4.4a (bounds apply uniformly). So the assertion this plan repairs defends a CODE-LEVEL narrowing (`run_opencode`'s "ISOLATED TURNS ONLY" comment, ordered by R4.6) that no requirement states. That is a real gap: a future change could widen the policy to non-isolated turns, break this test, and no spec would say the test was right. Writing the expectation into the spec would close it, but a spec amendment is a contract change needing its own review and is not what this plan was scoped or approved for. RECOMMENDATION: amend `7ckptx` in a follow-on, and in the meantime E-02 makes the test cite the code-level narrowing rather than miscite `R4.1`, so the record is at least honest about what it defends.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: both runs pasted (bare and with the variable set), the enumerated list of ambient-reading assertions, confirmation that `run_opencode` sets the variable, and any filing reassigned to the role-variable cause.
  - Observed evidence: Runs measured at HEAD `017d03ac` before editing:
    1. Bare (`unset OPENCODE_CONFIG_CONTENT`):
       `148 passed in 6.14s`
    2. With `OPENCODE_CONFIG_CONTENT` set:
       `1 failed, 147 passed in 5.34s`
       `FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
       `AssertionError: a non-isolated turn must get NO denial policy; it works in the main checkout where external-directory denial would refuse its ordinary work (R4.1)`
       `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`
    3. Enumerated ambient-reading assertions in `tests/test_turn_bounds.py`:
       - Line 271: `assert policy_key not in main_env` (reads ambient `OPENCODE_CONFIG_CONTENT`)
       - Line 275: `assert "AW_EXECUTION_ROLE" not in main_env` (reads ambient `AW_EXECUTION_ROLE`, passing only due to `conftest.py` import-time pop).
    4. Inheritance chain confirmed: `oc_runipd.run_opencode` sets `OPENCODE_RUNTIME_CONFIG_ENV` only inside `if work_dir:`; the outer runner exports `OPENCODE_CONFIG_CONTENT` into `os.environ`, and the inner `run_opencode(work_dir=None)` inherits it via `child_env = pinned_child_env()` because `pinned_child_env()` begins `merged = os.environ.copy()`.
    5. Boundary with `rolevac` `8i0xa7`: `rolevac` repairs the guard-vacuity from session-wide `AW_EXECUTION_ROLE` scrub; line 275 is inside `tests/test_turn_bounds.py` and is scoped to this plan.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the file pasted green with the variable SET; a diff or quote showing `R4.1`'s assertion was not weakened; and the test pasted FAILING under a deliberate mutation that adds the policy to a non-isolated turn.
  - Observed evidence: Hermetic execution and mutation test verified:
    1. File passed green with `OPENCODE_CONFIG_CONTENT` set:
       `OPENCODE_CONFIG_CONTENT='{"permission": {"external_directory": "deny", "question": "deny"}}' python3 -m pytest tests/test_turn_bounds.py`
       `148 passed in 8.58s`
    2. Property defended preserved:
       `test_the_permission_policy_by_contrast_IS_isolation_scoped` uses `monkeypatch.delenv(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` and `monkeypatch.delenv("AW_EXECUTION_ROLE", raising=False)`.
       The runner's deliberate narrowing is preserved unchanged:
       `assert policy_key not in main_env`
       `assert "AW_EXECUTION_ROLE" not in main_env`
       Docstring and assertion message updated to cite the runner's deliberate "ISOLATED TURNS ONLY" narrowing (R4.6) rather than misciting R4.1.
    3. Deliberate mutation test:
       Mutating `agent_workflows/oc_runipd.py:3516` (`if work_dir:` -> `if True:`):
       `FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
       `AssertionError: a non-isolated turn must get NO denial policy; it works in the main checkout where external-directory denial would refuse its ordinary work`
       `assert 'OPENCODE_CONFIG_CONTENT' not in {...}`
       `1 failed in 7.82s`
       Mutation reverted and verified clean.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted green results in both environment conditions, plus the bare `python3 -m pytest` summary line; and, if a reintroduction guard was added, the test pasted failing when an ambient read is restored.
  - Observed evidence: Green results in both environment conditions and full suite pass:
    1. `tests/test_turn_bounds.py` in both conditions:
       - Bare: `148 passed in 7.97s`
       - With `OPENCODE_CONFIG_CONTENT` set: `148 passed in 8.58s`
    2. Sibling test suite:
       `python3 -m pytest tests/test_lane_permission_posture.py` -> `27 passed in 8.48s`
    3. Bare repository test suite:
       `python3 -m pytest`
       `8850 passed, 5 skipped, 2 xfailed, 6 warnings in 175.02s (0:02:55)`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: this plan's front matter pasted showing BOTH `- From-Backlog:` bullets present (`mepbmp` AND `wnabns`) and `- Blocks-Release: next` unchanged, which is what proves the existing handoff was not overwritten; `aw check` output pasted showing no `check.from-backlog-dangling` for either id6 and no blocking-close finding for `wnabns`; and `wnabns`'s own front matter pasted showing it is still `open` and was not modified. A statement that the gate "was carried" without the pasted `aw check` result does not satisfy this item.
  - Observed evidence: Front matter state and backlog gate preservation verified:
    1. Front matter of `heglfv`:
       `- Id: heglfv`
       `- From-Backlog: mepbmp`
       `- Blocks-Release: next`
    2. Front matter of `wnabns`:
       `- Id: wnabns`
       `- Status: open`
       `- Blocks-Release: next`
       `- Set: wnabns`
    3. Schema constraint & decision:
       `ipd_schema.py:184` defines `META_FROM_BACKLOG` as single-valued, and `ipd_schema.py:315-316` / `ipd_lint.py` rejects duplicate metadata fields with `IPD-M102: duplicate field`. Plan `y9s4vm` had dual links of different kinds (`From-Spec:` and `From-Backlog:`), not duplicate `From-Backlog:` lines. Per decision recorded in `decisions-and-questions.md`, `heglfv` retains single `- From-Backlog: mepbmp` with `- Blocks-Release: next`, while `wnabns` remains open and unmodified for maintainer consolidation.
    4. `aw check` confirms no `check.from-backlog-dangling` for `mepbmp` or `wnabns`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTIONS: OQ-01 is resolved (scope the environment with `monkeypatch.delenv`, per the shipped sibling precedent; construct-and-compare remains acceptable if recorded). OQ-02 remains `open`, `Blocking: no`, maintainer-owned: whether spec `7ckptx` should state the non-isolated policy expectation at all. Neither gates this plan's correctness.

TWO THINGS AN EXECUTOR MUST NOT GET WRONG, both measured at review. FIRST, the property being defended is the runner's DELIBERATE ISOLATED-TURNS-ONLY NARROWING, not `R4.1`: that requirement is a floor on the ISOLATED turn and says nothing about a non-isolated one (F-5). Defending the wrong contract could satisfy the letter of E-02 while losing the property. SECOND, E-04 must ADD a `- From-Backlog: wnabns` bullet, not replace `mepbmp`: `--from-backlog` SETS rather than appends, so the naive call strands `mepbmp`'s gate instead of preserving `wnabns`'s (F-9).

SCOPE FENCE (a declaration, not a stop instruction). The declared path is `tests/test_turn_bounds.py`. E-04 additionally edits this plan's own front matter, which is a lifecycle record rather than a scope path. An out-of-scope edit is made and then JUSTIFIED at finalize with `--scope-reason`, and a declared-but-unmodified path with `--scope-ack`; `aw ipd finalize` refuses to complete without them.

THE ONE GENUINE STOP CONDITION: if the assertion cannot be made hermetic without changing `lane_containment` or a runner, stop and report rather than widening. That is a prerequisite-absent condition (the property is not expressible within the declared path), not a scope preference.

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste the actual runner output; a claimed pass with no pasted `N passed` line is a failed item. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence. The lifecycle transition to `.aw/records/plans/executed/` is performed by `aw ipd finalize` when an executor runs this plan by hand, and by the runner itself when it is dispatched by `aw oc run`/`aw agy run`; never by a hand-rolled `git mv`.
