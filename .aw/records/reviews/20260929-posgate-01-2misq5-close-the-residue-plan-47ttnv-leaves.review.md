# Review: Close the residue plan 47ttnv leaves when it gates the positional backlog set spelling

- Subject-Id: 2misq5
- Subject-Type: ipd
- Reviewed-At: 2026-09-29
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims re-measured at HEAD `86730317` in an isolated review lane worktree. The target plan was
committed and unchanged, so the pre-review snapshot was correctly skipped per Step 1. Structural
preflight `aw ipd lint --phase author --agent` reported `conforming` (`findings: 0`) before review,
and `--phase review-finalize` reported `conforming` after every revision.

THE PLAN'S THESIS IS CORRECT AND ITS CORE REPRODUCTION SURVIVES INDEPENDENT RE-MEASUREMENT, which
matters because this plan rests almost entirely on a simulation. I re-simulated `47ttnv`'s gate by
inserting the predicate call at the exact position its E-01 specifies (after the
`validate_transition_allowed` loop, before the `_plan_executed` delegation) and reproduced F-03
exactly: the sole failure is
`tests/test_backlog_production.py::TestBacklogProductionE08::test_case5a_agent_sets_done_itself`,
erroring as `subprocess.CalledProcessError ... 'backlog','set','done','bkl201','--no-commit' ...
returned non-zero exit status 1` and printing `FAIL refused: gate 'next' is handed off to
From-Backlog carrier(s) (20260927-demo-01-pln201-test-plan.ipd.md) but the work has not shipped
(carrier is not executed/implemented)`. F-05's claim that the refusal takes the HANDOFF branch rather
than the no-carrier branch is therefore confirmed verbatim from the live output, and F-01's structural
check reproduces (`grep -c evaluate_blocking_close agent_workflows/status_set.py` -> `0`). F-04's
mechanism is real: the exception is raised inside `fake_agent`, so `run_queue` never evaluates the
legitimacy check.

THE DOMINANT FINDING IS ONE NEITHER THIS PLAN NOR `47ttnv` HAS, AND IT INVALIDATES THE PRESCRIBED
FIX. Both plans prescribe the same remedy (drop `check=True`) and both assert it suffices. It does
not. With the gate simulated and `check=True` changed to `check=False`, the test STILL FAILS, on a
DIFFERENT assertion: `AssertionError: 'executed' != 'fail-gate'`. Driving `run_queue` directly
explains the whole chain: post-fix the agent's close is REFUSED (`AGENT-CLOSE-RC 1`), so the item
never leaves `open/`; the run then performs its OWN handoff transition (`backlog set <id6> --status
graduated`, the flag spelling, always gated) which SUCCEEDS because the item is a clean `open` item
with a conforming pending carrier; `production_checks.backlog_graduate_legitimacy` therefore sees
`status_before == "open"` and a properly `graduated` item and returns no findings; and the queue item
ends `executed` with `refusal = None`, item in `graduated/`. A refused misbehavior is
indistinguishable from good behavior, so the case does not merely change its exit code, IT STOPS
BEING THE CASE. `BACKLOG-GRADUATE-LEGITIMACY` ends up untested exactly as `47ttnv`'s own F-11 feared,
but via a GREEN test rather than a red one, which is strictly worse because nothing reports it.

ONE MEASUREMENT TRAP IS WORTH RECORDING BECAUSE IT NEARLY INVERTED THIS FINDING. My first probe ran
outside pytest and reported the post-fix case as still `fail-gate`, i.e. apparently fine. That answer
was wrong: the `python3 -m agent_workflows` subprocess inside `fake_agent` resolves the package from
the environment, and the repo-root `conftest.py` pins `PYTHONPATH` to the worktree for the test
session and its children. Outside pytest the child imported a different copy and never saw the
simulated gate. The pytest run is authoritative and is what the findings rest on; I reproduced the
same result a second time with `PYTHONPATH` set explicitly, which agreed with pytest.

THE REMEDY IS PROVEN, NOT PROPOSED, which is what lets this stay a revision rather than a REPLAN. The
misbehaving agent must still ACHIEVE the illegitimate on-disk state by a route no CLI gate can refuse,
writing `- Status: done` and relocating the file into `done/` directly, which is exactly what a real
misbehaving agent can still do once both spellings are gated. Measured with the gate simulated:
`HAND-WRITTEN done, post-fix: status = fail-gate | refusal = BACKLOG-GRADUATE-LEGITIMACY`, item in
`done/`, every original assertion satisfied and none weakened.

OWNERSHIP MOVED UNDER THIS PLAN, AND ITS F-03 NOW CARRIES A FALSE SENTENCE. F-03 ends "`47ttnv` does
NOT mention this test anywhere, and `tests/test_backlog_production.py` is NOT in its `- Scope-Paths:`,
so as written it cannot legally fix it." True at authoring, false at review: `47ttnv` is now
`reviewed` / `go-pending-approval`, its `- Scope-Paths:` carries six paths INCLUDING
`tests/test_backlog_production.py`, it mentions that file nine times, and its E-08 plus V-08 perform
the `check=True` removal. Its F-11 names `2misq5` explicitly and states the deadlock it broke (this
plan waited on `47ttnv` while `47ttnv`'s own bare-suite validation could not pass without this plan's
E-01), and its `## Deferred` section carries a `Carrier: 2misq5` entry naming what it left behind.
E-01 is therefore rewritten from "perform the one-line change" to "verify it as found-already-done,
then fix what it leaves broken".

E-02 AS AUTHORED WAS BOTH UNREACHABLE AND REDUNDANT. It asked for a case whose close attempt is
REFUSED yet still yields `fail-gate` plus `BACKLOG-GRADUATE-LEGITIMACY`. That state does not exist
(measured: `executed`, no refusal), so the item could only have been completed by relaxing its own
assertion, which is the failure mode its sibling gate forbids. It was also a duplicate: post-`47ttnv`
the corrected case5a's close IS a refused close, so E-01 and E-02 as written described one scenario
and shipping both would have added a second test over the same path (P8). Re-aimed at the property
the post-gate world genuinely lacks: the DISCRIMINATION between an achieved illegitimate state (must
fail the run) and a blocked attempt (must not), with the second case pinning the measured correct
behavior so a future widening of the check is caught as the regression it would be.

E-03's PREMISES WERE STALE IN TWO WAYS, ONE OF THEM OPERATIONAL. The item says `le31pr` carries
`- Status: open`; it is `graduated` (in `graduated/`, `- Graduated-To: posgate`, graduated to this
plan by run `run-20260929T021205Z-3914774`), and the plan's `- Scope-Paths:` still named the `open/`
directory, i.e. a path that does not exist, which the finalize scope gate would flag. Corrected both.
The duplicate-gate concern is unaffected, since `AGENTS.md` lists `graduated` among the LIVE states a
gating `bug` must carry the field in. The design is stronger than the plan claimed, verified directly
rather than inferred: `evaluate_blocking_close(repo, <le31pr path>, "done")` returns
`legitimate=False severity=error` with reason `gate 'next' is handed off to From-Backlog carrier(s)
(20260929-posgate-01-2misq5-...ipd.md) but the work has not shipped`, so the predicate is ALREADY on
the HANDOFF branch naming this very plan as the carrier it awaits.

Verified TRUE and unchanged: F-02's account of `47ttnv`'s E-01..E-07 coverage and its `Carrier:
le31pr` declination; F-06's four other positional-spelling test files (all four exist and all pass
under the simulation) and `tests/test_backlog_gate_follows_status.py` as the established paired-
spelling template; F-08's specs-parity evidence, quoted verbatim from the comment above
`_gated_approval` in `validate_transition_allowed` ("the POSITIONAL `aw specs set approved
<selector>` spelling routes to THIS function while the `--status` spelling routes to the forked
`specs.run_set`"); the plan's reading of what case5a actually pins (three assertions on the queue item
and the `graduated/` glob, nothing about the setter's exit code); `backlog_graduate_legitimacy`'s
keying on on-disk state rather than a setter outcome, which is what makes E-02's re-aimed pin
meaningful; and that `aw backlog set --status done` is the FLAG spelling, already gated today, so
E-03's legitimacy does not depend on the fix under review.

Two smaller corrections. F-06 says the paired-spelling file pins "nineteen properties"; it declares 18
test functions, so the number is off by one and I left the claim's substance alone rather than
re-deriving what a "property" counts as, noting it here instead. And the baseline paragraph asked the
executor to hit `1 failed, 3245 passed, 2 skipped` "with zero failures", a figure taken on a simulated
tree at a different HEAD; replaced with the parity rule against the executor's own pre-change
measurement, since other lanes move the whole-suite total continuously.

Every probe was reverted. Two gate simulations and two edits to `tests/test_backlog_production.py`
were made and undone; the restored tree reports `git status --porcelain` empty, `grep -c
evaluate_blocking_close agent_workflows/status_set.py` -> `0`, and `python3 -m pytest -o addopts=""
-q tests/test_backlog_production.py` -> `14 passed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | BLOCKER | IN-SCOPE | A. Correctness / E. Testing (prescribed fix does not work) | Measured under pytest (authoritative: repo-root `conftest.py` pins `PYTHONPATH` for the session and its children) with `47ttnv`'s gate simulated and `check=True` -> `check=False`: `AssertionError: 'executed' != 'fail-gate'` at `tests/test_backlog_production.py:832`. Driving `run_queue` directly: `POST-FIX(pinned): run status = executed \| refusal = None`, item in `graduated/`, `AGENT-CLOSE-RC 1`. Chain: refused close leaves item in `open/` -> run's own `--status graduated` handoff succeeds -> `production_checks.backlog_graduate_legitimacy` sees `status_before == "open"` and a `graduated` item -> no findings. | REMOVING `check=True` DOES NOT FIX THE TEST, IT HIDES THE BREAKAGE. Both this plan's E-01 and `47ttnv`'s E-08 prescribe exactly that one-line change and both assert it suffices. Post-fix the agent's misbehavior is REFUSED, so from the run's point of view the agent behaved correctly and the scenario dissolves: the case passes while no longer exercising `BACKLOG-GRADUATE-LEGITIMACY` at all. That is the same loss of coverage `47ttnv`'s F-11 identified, arriving via a GREEN test instead of a red one, which is worse because nothing reports it. An executor following either plan would mark the work validated on a test that proves nothing. | C:Low; U:Low; S:Low; F:High -> Low once the scenario is restored (the remedy is a change to the fake agent only, demonstrated at review); Overall:Low | FIXED | E-01 rewritten: verify `47ttnv` E-08's one-liner as found-already-done, then RESTORE the scenario by having the fake agent achieve `done` through a setter-bypassing route (hand-written status plus relocation), which no CLI gate can refuse. Remedy verified at review, not proposed: `HAND-WRITTEN done, post-fix: status = fail-gate \| refusal = BACKLOG-GRADUATE-LEGITIMACY`, item in `done/`, all three original assertions intact. Recorded as F-09; V-01 now requires the item's final location in `done/` as evidence and requires BOTH before-states pasted. |
| PR-602 | HIGH | IN-SCOPE | E. Testing (unreachable assertion + duplicate coverage) | E-02 as authored asks for a `fake_agent` "whose close attempt is REFUSED" asserting `fail-gate` and `BACKLOG-GRADUATE-LEGITIMACY`. Measured: that state is `executed` with `refusal = None`. Separately, post-`47ttnv` the corrected case5a's close IS a refused close, so both items describe one scenario. | E-02 WAS BOTH IMPOSSIBLE AND A DUPLICATE. Written as specified it asserts a state the code never reaches, so the only way to make it green is to relax the assertion, which is precisely the defeat-the-test failure mode this Set exists to prevent. And had it been written to match reality it would have duplicated E-01's corrected case over the same code path (P8). The plan's stated lesson ("a production check must still fire when the mutation was refused") is itself false: the check correctly does NOT fire, because nothing illegitimate happened. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-02 re-aimed at the coverage the post-gate world actually lacks: the DISCRIMINATION between an achieved illegitimate state (setter-bypassing `done` must reach `fail-gate` with the legitimacy code) and a blocked attempt (must end `executed` with no refusal, the measured correct behavior). The contrast is what makes it a pin rather than a restatement of E-01. The refuted framing is recorded as F-10 and V-02 explicitly forbids building it. |
| PR-603 | HIGH | IN-SCOPE | G. Plan executability (ownership moved; a claim is now false) | `47ttnv` at review: `- Status: reviewed`, `- Readiness: go-pending-approval`, `- Scope-Paths:` = six paths including `tests/test_backlog_production.py`, `grep -c test_backlog_production` -> 9, E-08 + V-08 perform the `check=True` removal, F-11 names `2misq5` and the deadlock, `## Deferred` carries `Carrier: 2misq5`. | F-03 ENDS IN A SENTENCE THAT IS NOW FALSE, AND E-01 WOULD RE-PERFORM ANOTHER PLAN'S WORK. F-03 asserts `47ttnv` neither mentions this test nor declares its path "so as written it cannot legally fix it". Both halves are now untrue. Since this plan cannot execute until `47ttnv` is `executed`, its E-01 would arrive to find the one-line change already on disk and, following the plan literally, would either re-apply it or report performing work it did not do. The reproduction evidence in F-03 is independently confirmed and stands; only the ownership claim changed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | F-03's stale sentence corrected in place with the new measurement and the reason `47ttnv` absorbed the line (deadlock-breaking, its F-11). E-01 re-scoped from perform to VERIFY-then-complete, and its Expected outcome requires reporting the one-liner as found-already-done. The Scope and Task-group-1 prose carry a dated review note so the change of ownership is visible to a reader who only reads the top. |
| PR-604 | MEDIUM | IN-SCOPE | A. Correctness (stale artifact state with an operational cost) | `le31pr` is at `.aw/records/backlog/graduated/20260926-posgate-01-le31pr-...backlog.md` with `- Status: graduated`, `- Graduated-To: posgate`, graduated by run `run-20260929T021205Z-3914774`; the plan's E-03 says `- Status: open` and `- Scope-Paths:` named `.aw/records/backlog/open/...`. | THE DECLARED SCOPE PATH POINTS AT A FILE THAT DOES NOT EXIST. E-03 describes the item as `open` and the plan declares the `open/` path, but the item was graduated to this very plan. This is not only prose drift: `aw ipd finalize` reconciles declared paths, so a declared path that cannot be modified because it does not exist is a finalize-time problem, and the transition under test is `graduated -> done`, not `open -> done`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `- Scope-Paths:` re-pointed to the `graduated/` path; E-03 and F-07 both corrected with the measured state and with the note that `graduated` is still a LIVE gating state per `AGENTS.md`, so the duplicate-gate concern is untouched. V-03 now states the transition is `graduated -> done`. |
| PR-605 | MEDIUM | UNDER-SCOPE | G. Plan executability (gate) | Workflow Step 4 requires the gate to carry the lifecycle transition with conditional runner/executor ownership and a declaration-shaped scope fence; the authored gate had neither, and `47ttnv`'s gate carries both. E-03 must run AFTER this plan's own `executed` transition while the `le31pr` path is declared in `- Scope-Paths:`. | THE GATE OMITTED THE LIFECYCLE CLAUSE AND THE FINALIZE/E-03 ORDERING TRAP. Nothing said who owns `aw ipd finalize`, so a runner-driven execution could invoke it and collide with the runner's own transition. Worse, E-03's required ordering (close only once this plan IS the executed carrier) means the declared `le31pr` path is still UNMODIFIED at finalize time, which the scope reconciliation will flag; the plan gave the executor no warning and no remedy. Nothing said to revert the probes V-02 and V-01 require either, so a left-behind probe could make the final green run meaningless. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten: conditional finalize ownership added; the fence restated as a DECLARATION reconciled by `--scope-reason`/`--scope-ack` (no STOP directive for the out-of-scope-edit case, per the 2026-09-01 ruling); an explicit REVERT-EVERY-PROBE clause with a clean-`git status` requirement; and a named ordering-trap paragraph telling the executor to expect to `--scope-ack` the `le31pr` path at finalize and commit E-03's close separately afterwards. |
| PR-606 | LOW | IN-SCOPE | E. Testing (stale baseline) + A. Correctness (count) | Authored target `1 failed, 3245 passed, 2 skipped` was measured on a simulated tree at a different HEAD; at review HEAD `86730317` `tests/test_backlog_production.py` alone reports `14 passed`. `tests/test_backlog_gate_follows_status.py` declares 18 test functions against F-06's "nineteen properties". | A STALE WHOLE-SUITE TARGET AND ONE OFF-BY-ONE COUNT. Asking the executor to reproduce a specific total taken on a different HEAD invites either explaining other lanes' test additions or abandoning the check; this repository has been bitten by exactly that before. The "nineteen properties" figure is a minor over-count against 18 declared tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The baseline paragraph now states the parity rule (compare against your own pre-change measurement on the post-`47ttnv` tree, never a number written in the plan), names the only acceptable delta (the cases E-02 adds), and makes a dropped collected count in that file a FAILED validation even when the summary is green. The count discrepancy is recorded here rather than edited into F-06, since what counts as a "property" versus a test function is the author's framing and its substance (that file is the established paired-spelling template) is verified and unaffected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Given PR-601 (the prescribed fix leaves the test proving nothing), is this REJECT - NEEDS REPLAN or a bounded revision? | BOUNDED REVISION. Rewrite E-01 to restore the scenario; keep the plan and all three items. | (a) REPLAN on the grounds that both plans' shared premise is wrong. Rejected because a working remedy was DEMONSTRATED at review, not merely imagined: having the fake agent achieve `done` by writing the status and relocating the file yields `fail-gate` + `BACKLOG-GRADUATE-LEGITIMACY` with every original assertion intact, and it is a change to one fake agent inside one test. Nothing about the plan's structure, its dependency, or E-03 is affected. (b) Escalate as a blocking question and stop. Rejected: the repository answered it (the remedy is measured), and the workflow forbids asking the human what evidence settles. | Measured at review with the gate simulated: `HAND-WRITTEN done, post-fix: status = fail-gate \| refusal = BACKLOG-GRADUATE-LEGITIMACY`, item in `done/`; `production_checks.backlog_graduate_legitimacy` clause order (status_before, then on-disk status and `/graduated/` path) | yes |
| D-2 | PR-601 also invalidates `47ttnv`'s E-08, an already-`reviewed` sibling plan. Edit that plan, or confine the fix here? | CONFINE IT HERE, and make this plan's E-01 own the completion. | (a) Edit `47ttnv`'s E-08 to carry the full remedy. Rejected on two grounds: the review scope ledger contains only `2misq5`, and the workflow states a file referenced as evidence is not in scope unless explicitly added; and `47ttnv` is already `reviewed` with `- Readiness: go-pending-approval`, so silently widening it would invalidate a recorded readiness another review attested. (b) Leave the gap unowned and merely note it. Rejected: `47ttnv` would then execute, pass its own V-08 on a green-but-hollow test, and the coverage loss would ship unreported, which is the exact outcome its F-11 exists to prevent. Confining it here is safe BECAUSE of the dependency: this plan cannot execute until `47ttnv` is `executed`, so E-01 necessarily runs after E-08 and completes it. | `47ttnv` front matter (`- Status: reviewed`, `- Readiness: go-pending-approval`) and its E-08/V-08; this plan's `- Item-Dependencies: executed:47ttnv`; plan-review Step 0.1 ledger rule and the cross-plan rule to fix in the owning plan and cross-reference from dependents | yes |
| D-3 | OQ-01 asks the maintainer whether to fold this residue into `47ttnv`. Ask it, or resolve it? | RESOLVE IT as settled by events, and record the reasoning in the question. | (a) Ask the maintainer as authored. Rejected: the apportionment has already been DECIDED by the plan that owned it. `47ttnv`'s review folded the one-line change in (its F-11) and explicitly declined the rest with a `Carrier: 2misq5` entry, so asking now would ask a human to re-decide something already recorded in another plan's front matter. (b) Resolve it as "keep separate" on the authored reasoning alone. Rejected as under-stated: the authored rationale claimed the work is "identical either way", which PR-601 refutes, so the honest resolution has to say the remaining work is strictly larger than the absorbed line and that folding it now would widen a release-blocking plan on evidence its own review never saw. | `47ttnv`'s `- Scope-Paths:`, E-08, F-11 and `## Deferred` `Carrier: 2misq5` entry; PR-601's measurement | yes |
| D-4 | My first probe (outside pytest) reported the post-fix case as still `fail-gate`, contradicting the pytest result. Which is authoritative? | THE PYTEST RESULT, and record the trap. | (a) Trust the bare probe and drop PR-601. Rejected on mechanism: the `python3 -m agent_workflows` subprocess inside `fake_agent` resolves the package from the environment, and the repo-root `conftest.py` inserts the repo root into `sys.path` AND into `PYTHONPATH` for children, so only under pytest does the child see the simulated gate. The bare probe measured an unpatched package. (b) Report both without deciding. Rejected: that would leave a reader unable to act, and the question has a determinate answer confirmed by re-running the probe with `PYTHONPATH` set explicitly, which then agreed with pytest. | `conftest.py`'s `_REPO_ROOT` `sys.path` insert and `PYTHONPATH` composition; agreement of the pinned probe with the pytest failure (`executed`, no refusal) | yes |
