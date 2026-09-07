# IPD: Earn integration from a suite-failure delta against the frozen base instead of absolute green

- Date: 2026-09-06
- Kind: child
- Concern: ONE pre-existing red test anywhere in the repository silently disables automatic lane integration for EVERY plan. With `--validate` defaulting FALSE, `integration_is_earned` falls back to the driver-run suite as the trust signal (`oc_runipd.py:3635-3660`), and `run_suite_check` reports a BINARY pass/fail on the whole suite (`passing` is True only on an observed exit 0, `:3517`). So the gate cannot distinguish "this lane broke something" from "this repository was already red before the lane existed", and any unrelated failure closes it for every item in every run.
  MEASURED COST, ONE INCIDENT. Run `run-20260907T010730Z-3199043` executed `mm6wuz` for 1h35m at $39.42, committed 2164 insertions across 10 files on its lane, verified all 12 E-items and all 12 V-items, and reported `aw ipd lint --phase pre-transition` conforming. Its `suite_check` recorded `{'passing': False, 'exit_code': 1, 'elapsed_seconds': 78.0}`, so `integration.earned` was False, so the branch at `oc_runipd.py:6435` never ran, and that branch is the ONLY caller of both `driver_finalize` and `integrate_lane_branch` (`:6468`). No finalize meant the plan stayed in `pending/`, which made `reconcile_disposition` downgrade the agent's own `disposition: executed` to `substantially-complete`. Zero integration events were emitted. The work was recovered by hand (`0f8abfab`, `b2bda903`).
  THE AGENT HAD ALREADY PROVEN NO REGRESSION AND THE GATE COULD NOT SEE IT. Its outcome record states the bare suite ended `31 failed, 5563 passed`, that a clean clone of the frozen base `6091014c` was built and run bare giving `31 failed, 5505 passed`, and that the sorted FAILED sets were BYTE-IDENTICAL, so zero regressions and +58 passing tests. That is exactly the delta comparison this plan makes the gate perform. The information existed; only the gate's question was wrong.
  THIS IS THE SAME CLASS AS THE BUG `evgi9n` ALREADY FIXED, which is why it is a release blocker rather than tuning. `integration_is_earned`'s own docstring records that the gate used to require `verify_disp == "verified"`, unreachable in the default configuration, and that the measured cost was "~$528 across five overnight runs, 21 plans stranded in lanes, then a full session hand-merging 24 lanes". That fix made an unreachable condition reachable. This is the next layer: reachable, but gated on a signal that is red for reasons unrelated to the lane. Today's baseline is ONE failure (`test_orchestrator_retirement::RealRepositorySets`, which asserts against a sibling plan's live status), so the trigger threshold is a single unrelated red test.
- Scope: Teach the driver's suite check to answer a DELTA question instead of an absolute one: capture the failing-test set at the frozen base HEAD, compare the lane-time failing set against it, and earn integration when the lane's failures are a SUBSET of the base's. Keep every existing refusal that is genuinely about this lane, keep the fail-closed posture for a suite that cannot run, and change no default the operator must remember.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_novalnomerge_integration.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: integearn
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 32ij2j
- From-Backlog: ciesaj
- Blocks-Release: next

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ciesaj`, which was itself filed from a measured incident earlier in this session: a $39.42 lane left unintegrated with zero integration events. Every claim was re-verified against code at HEAD `15445857` rather than trusted. CONFIRMED: `SuiteCheckResult.passing` is True only on exit 0 (`oc_runipd.py:3517`); `run_suite_check` is called from exactly two sites, one per driver (`oc_runipd.py:6397`, `agy_runipd.py:3711`), and agy BINDS the shared definition rather than forking it (`agy_runipd.py:306`), so a fix in the shared function reaches both hosts by construction; the earned-integration branch at `:6435` is the sole caller of `driver_finalize` and `integrate_lane_branch`. FEASIBILITY MEASURED BEFORE AUTHORING, so the design is not speculative: `capture_command` is invoked with `max_output_bytes=512_000` (`:3563`) while a real run's `FAILED` lines total 125 bytes, so the substrate for parsing a failing-test set is already captured and no new plumbing is needed; and the begin receipt already persists `base_head` (verified in `.aw/state/ipd-lifecycle/mm6wuz.receipt.json`) with `ipd_lifecycle.read_receipt` (`:816`) as the reader, so the baseline commit is already knowable at gate time. TWO THINGS DELIBERATELY LEFT TO SIBLINGS: reporting the verdict honestly is `7m0aro` (integearn-02), and the stale-base scope misattribution the same recovery exposed is `hyx1dg`.

## Goal

Make the integration gate ask "did this lane make the suite worse", which is the question that actually protects main, instead of "is the whole repository green", which no busy repository ever is.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make a failing-test SET observable

- [ ] E-01 Extend `SuiteCheckResult` (`oc_runipd.py:3509-3524`) with the FAILING TEST SET, and populate it in `run_suite_check` by parsing the `FAILED <nodeid>` lines out of the captured stdout. Store it as a SORTED TUPLE so two results are comparable by equality and a subset test is cheap and order-independent.
  THE SUBSTRATE IS ALREADY CAPTURED, so this adds parsing rather than plumbing: `capture_command` is called with `max_output_bytes=512_000` (`:3563`) and a real run's `FAILED` lines total 125 bytes. Follow the existing `_SUITE_SUMMARY_RE` precedent (`:3504`, searched against stdout then stderr at `:3586`) rather than inventing a second output-reading style.
  KEEP `passing` EXACTLY AS IT IS. It is documented as "an OBSERVED FACT, not a claim ... True only on an observed exit 0" and other readers depend on that meaning. This item ADDS a field; it must not redefine one.
  RECORD WHEN THE SET IS UNKNOWABLE, and distinguish that from an empty set. A truncated capture, an unparseable summary, or exit 124/127 means "I could not determine the failing set", which is NOT the same as "nothing failed". Use `None` for unknown and an empty tuple for genuinely no failures, because E-03 must fail closed on the former and pass on the latter.
  - Depends on: none
  - Expected outcome: `SuiteCheckResult` carries a sorted failing-test tuple (or `None` when undeterminable); `passing` is unchanged in meaning and value; parsing follows the existing regex precedent.
  - Execution state: pending

- [ ] E-02 Capture the BASE-HEAD baseline failing set, and cache it per commit so the cost is paid once per run rather than once per item. The comparison target is the frozen base, which the begin receipt already records: `base_head` is persisted in the receipt (verified present in `.aw/state/ipd-lifecycle/<id6>.receipt.json`) and `ipd_lifecycle.read_receipt` (`:816`) reads it.
  RUN THE BASELINE IN A DETACHED CLONE OR SCRATCH WORKTREE OF `base_head`, NEVER BY MUTATING THE PRIMARY CHECKOUT. This is not optional: the primary tree is what other agents are working in, and this repository's policy for un-owned state is to leave it strictly alone. A `git stash` or `git checkout` to reach the base would be exactly the co-worker-clobbering `AGENTS.md` forbids. The agent whose incident motivated this plan did it correctly by hand, building "a clean clone of HEAD `6091014c` in a gitignored scratch dir".
  CACHE UNDER `.aw/state/`, keyed by the base commit sha. That tree is gitignored and box-local, which is the correct home for an ephemeral measurement, and a sha key makes the cache self-invalidating: a different base is a different key, so a stale baseline cannot be reused.
  DO NOT RUN THE BASELINE IN A LANE WORKTREE. `run_suite_check`'s docstring records the measured reason: a linked worktree resolves `.aw/state` relative to cwd (`dh0uno`), giving `36 passed` in the primary checkout versus `15 failed, 20 passed` in a lane, "every failure being the `run_viewer`/state-resolution family". A baseline measured in a lane would be permanently and wrongly red, reproducing this plan's own bug with a new cause.
  - Depends on: E-01
  - Expected outcome: the base-head failing set is measured in an isolated checkout of that commit, cached under `.aw/state/` keyed by sha, reused within a run, and never obtained by mutating the primary tree.
  - Execution state: pending

### Task group 2: change the question the gate asks

- [ ] E-03 Change `integration_is_earned`'s validation-OFF branch from "the suite passed" to "the lane's failing set is a SUBSET of the base's". Earn integration when every failing test also failed at the base; refuse when the lane introduces a failure the base did not have.
  FAIL CLOSED ON UNKNOWN, which is the case E-01 made distinguishable. If either failing set is `None` (undeterminable), REFUSE. The existing posture is explicit that "a suite that cannot be run is a FAILURE, never a pass" and that "a gate that crashes is a gate that is OFF"; an unknown delta must inherit that, or this change becomes an escape hatch rather than a better question.
  DO NOT TOUCH THE VALIDATION-ON BRANCH. The docstring states the two modes are ALTERNATIVES and that "a verifier that DECLINED is a stronger and more specific signal than a green suite, so a passing suite must NOT override it; otherwise `--validate` would be weaker than the default, which is absurd". That reasoning is unaffected by this change and must survive it verbatim.
  CARRY THE REASON. `IntegrationVerdict` already exists to explain the decision; populate it with the delta ("3 failures, all present at base `<sha>`" or "1 NEW failure not at base: `<nodeid>`"). Sibling child `7m0aro` (integearn-02) owns PERSISTING and REPORTING that reason; this item's obligation is to produce it rather than discard it.
  - Depends on: E-02
  - Expected outcome: a lane whose failures are all pre-existing earns integration; a lane introducing any new failure does not; an undeterminable set refuses; the validation-ON branch is byte-unchanged.
  - Execution state: pending

- [ ] E-04 Bound the cost and state the honest limits, because a baseline suite run is not free and a plan that pretends otherwise will be switched off.
  BOUND THE BASELINE RUN with the same timeout discipline `run_suite_check` already uses (`SUITE_CHECK_TIMEOUT_SECONDS = 900.0`, `:3496`), and treat a baseline timeout as UNKNOWN (refuse per E-03), never as an empty failing set. Reuse the constant; do not introduce a second timeout.
  RECORD THE HONEST LIMITS in the function's docstring, extending the existing "HONEST LIMIT" paragraph rather than replacing it. Three are known and each should be stated: (a) the comparison proves the lane added no failure THE SUITE CAN SEE, not that the lane is correct; (b) a FLAKY test can appear in one set and not the other, so a single new failure may be noise rather than a regression, which is an argument for reporting it rather than for ignoring it; (c) the baseline is measured at `base_head`, so a failure introduced on main by another agent AFTER that commit will look like this lane's fault. Limit (c) is a real residual and must be written down; narrowing it is `hyx1dg`'s territory, not this plan's.
  - Depends on: E-03
  - Expected outcome: the baseline run is timeout-bounded with the existing constant; a timeout refuses rather than passes; all three honest limits are documented at the decision site.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Test the DELTA LOGIC deterministically, without running a real suite. Drive `integration_is_earned` directly with synthesized `SuiteCheckResult` pairs and assert: identical failing sets earn; a lane set that is a strict subset earns (a lane that FIXED something must not be punished); a lane set containing one node absent from the base REFUSES and names that node; both-empty earns; `None` on either side refuses; and validation-ON still defers entirely to `verify_disp`.
  ASSERT THE REGRESSION CASE NAMES THE OFFENDER. A refusal that says only "suite not green" reproduces the diagnostic gap that made the original incident hard to read. The verdict must identify which test is new.
  ADD THE INCIDENT AS A REGRESSION FIXTURE, using its real measured numbers so the test documents the bug it prevents: base `31 failed, 5505 passed` and lane `31 failed, 5563 passed` with byte-identical FAILED sets must EARN integration. That is the exact case that stranded $39.42.
  - Depends on: E-04
  - Expected outcome: seven delta cases pinned including the incident fixture; the new-failure refusal names the offending node; the validation-ON path is proven untouched.
  - Execution state: pending

- [ ] E-06 Prove the END-TO-END path on BOTH hosts, which is where a shared-predicate fix can still be wired wrong. The predicate is shared by construction (`agy_runipd.py:306` binds it, and its docstring says "ONE predicate, consumed by BOTH drivers, so a one-runner fix cannot leave the other silently broken"), but the CALL SITES are per-driver (`oc_runipd.py:6397`, `agy_runipd.py:3711`) and each must pass the baseline through.
  DEMONSTRATE INTEGRATION ACTUALLY HAPPENING with a red pre-existing test present. Build a throwaway repository whose suite has one permanently failing test, run a lane that changes something unrelated, and show the lane INTEGRATES to main. Under today's code it would strand; that contrast is the proof.
  DEMONSTRATE THE REFUSAL TOO: a lane that breaks a test which passed at base must NOT integrate, and its lane branch must be preserved.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. Note `tests/test_run_viewer.py` reads the gitignored `.aw/records/runs/`, so validate in the REAL checkout; green in a bare worktree proves nothing.
  - Depends on: E-05
  - Expected outcome: on both hosts, a lane integrates despite an unrelated red test and refuses on a genuine new failure; bare suite green with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE PREDICATE IS ALREADY SHARED AND SAYS WHY: `integration_is_earned` is "ONE predicate, consumed by BOTH drivers, so a one-runner fix cannot leave the other silently broken", and `agy_runipd.py:306` binds it with the `as <same-name>` re-export form. Fix it there and both hosts inherit the fix.
- `run_suite_check` MUST RUN IN THE PRIMARY CHECKOUT, never a lane. Its docstring records the measured reason (`dh0uno`): a lane resolves a different `.aw/state`, giving `15 failed, 20 passed` where the primary checkout gives `36 passed`. A lane-measured baseline would be permanently red.
- FAIL-CLOSED IS THE ESTABLISHED POSTURE, stated twice at the site: "a suite that cannot be run is a FAILURE, never a pass", and "a gate that crashes is a gate that is OFF, so an unexpected exception here must still be a REFUSAL". The unknown-delta case must inherit it.
- `passing` IS DOCUMENTED AS AN OBSERVED FACT, not a claim, and is True only on exit 0. Add fields; do not redefine it.
- THE OUTPUT SUBSTRATE IS ALREADY CAPTURED: `max_output_bytes=512_000` versus 125 bytes of `FAILED` lines in a real run, so parsing needs no new capture.
- `base_head` IS ALREADY FROZEN AND READABLE: the begin receipt persists it and `ipd_lifecycle.read_receipt` reads it, so the comparison target requires no new state.
- `.aw/state/` IS GITIGNORED AND BOX-LOCAL, the correct home for a cached measurement, and a sha-keyed cache is self-invalidating.
- THE TWO VALIDATION MODES ARE ALTERNATIVES, NOT AN OR. A verifier that declined must not be overridden by a green suite.
- Run the suite BARE: `python3 -m pytest`. The configured `addopts` already supply quiet, parallel, and the fast subset; do not add `-n0` or a second `-q`.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The gate is BINARY on the whole suite: `passing` is True only on an observed exit 0, so any unrelated red test closes it for every item. | `oc_runipd.py:3509-3524`, `:3517` |
| F-2 | **THE MEASURED INCIDENT.** `mm6wuz` ran 1h35m at $39.42, committed 2164 insertions across 10 files, verified 12 E and 12 V items, and stranded everything: `suite_check` recorded `{'passing': False, 'exit_code': 1}`, `attempt['integration']` was `None`, and `grep -c integrat events.jsonl` returned 0. | `run-20260907T010730Z-3199043` state.json and events.jsonl |
| F-3 | The earned branch is the SOLE caller of both finalize and integration, so a False verdict skips both silently. | `oc_runipd.py:6435` (the `if integration_gate_relevant and integration.earned:` guard), `:6468` |
| F-4 | **THE AGENT HAD ALREADY DONE THE DELTA COMPARISON BY HAND** and the gate could not consume it: base clone of `6091014c` gave `31 failed, 5505 passed`, the lane gave `31 failed, 5563 passed`, and the sorted FAILED sets were byte-identical, so zero regressions and +58 passing tests. | `mm6wuz` outcome record, `regression_analysis` field |
| F-5 | The downgrade to `substantially-complete` is a CONSEQUENCE, not the cause: with no finalize the plan stayed in `pending/`, so `reconcile_disposition` read `plan_bucket() != "executed"` and overrode the agent's `disposition: executed`. | `oc_runipd.py:5814-5822` |
| F-6 | **SAME CLASS AS A BUG ALREADY FIXED AT MEASURED COST.** `integration_is_earned`'s docstring records the prior version required `verify_disp == "verified"`, unreachable with `--validate` defaulting False, costing "~$528 across five overnight runs, 21 plans stranded in lanes, then a full session hand-merging 24 lanes". | `oc_runipd.py:3646-3651` |
| F-7 | TODAY'S THRESHOLD IS ONE TEST. The current bare baseline is `1 failed, 5612 passed`, the failure being `test_orchestrator_retirement::RealRepositorySets`, which asserts against a sibling plan's live status and will recur whenever a plan's status changes. So the gate is closed right now. | measured 2026-09-06 at HEAD `15445857` |
| F-8 | **THE PARSING SUBSTRATE ALREADY EXISTS**, measured before authoring: `capture_command` keeps 512,000 bytes while a real run's `FAILED` lines total 125 bytes. | `oc_runipd.py:3563`; `python3 -m pytest \| grep '^FAILED' \| wc -c` |
| F-9 | **THE COMPARISON TARGET ALREADY EXISTS**: the begin receipt persists `base_head` (confirmed `6091014ce127...` in `mm6wuz`'s receipt) and `read_receipt` is its reader. | `.aw/state/ipd-lifecycle/mm6wuz.receipt.json`; `ipd_lifecycle.py:816`, `:1084` |
| F-10 | The fix reaches both hosts by construction: `run_suite_check` is called once per driver and agy BINDS the shared definition rather than forking it. | `oc_runipd.py:6397`; `agy_runipd.py:3711`, `:306` |
| F-11 | A LANE-MEASURED BASELINE WOULD REPRODUCE THIS BUG with a new cause: `dh0uno` makes a lane resolve a different `.aw/state`, giving `15 failed, 20 passed` where the primary checkout gives `36 passed`. Hence E-02's isolated-clone requirement. | `run_suite_check` docstring, `oc_runipd.py:3536-3542` |

## Proposed changes (ordered, validatable)

1. Add a sorted failing-test set to `SuiteCheckResult`, parsed from already-captured stdout, with `None` for undeterminable (E-01).
2. Measure the `base_head` baseline in an isolated checkout, cached under `.aw/state/` by sha, never by mutating the primary tree (E-02).
3. Change the validation-OFF branch to a subset test, failing closed on unknown, leaving validation-ON untouched (E-03).
4. Bound the baseline with the existing timeout and document the three honest limits (E-04).
5. Pin seven delta cases including the real incident as a fixture (E-05).
6. Prove end to end on both hosts that an unrelated red test no longer strands a lane (E-06).

## Deferred / out of scope (with reason)

- REPORTING THE VERDICT HONESTLY. Sibling child `7m0aro` (integearn-02) owns persisting the integration verdict, recording the disposition downgrade, and fixing `Outcome: COMPLETED` for a stranded run. This child PRODUCES the reason; that one PERSISTS and DISPLAYS it. Split deliberately: the gate's logic and the report's honesty have different test surfaces and can be verified independently.
- THE STALE-BASE SCOPE MISATTRIBUTION (`hyx1dg`). Same incident, different mechanism: finalize's scope audit attributing other agents' commits to the finalizing plan. It shares the `base_head` value but nothing else, and mixing them would put two unrelated fixes behind one verdict.
- NARROWING HONEST LIMIT (c), that a failure introduced on main by another agent after `base_head` looks like this lane's fault. Real residual, documented in E-04, and its fix needs commit-level attribution which is `a8eufb`/`hyx1dg` territory.
- FIXING THE PRE-EXISTING FAILURES THEMSELVES. `test_orchestrator_retirement::RealRepositorySets` asserts against a sibling plan's live status and is out of scope; this plan makes such a failure stop blocking integration, which is the durable answer rather than chasing each one.
- MAKING THE DELTA CHECK OPTIONAL VIA A FLAG. Rejected: `vju5ba` measured that a default which silently disables the mechanism is exactly how five overnight runs were lost. The correct behavior must be the default.
- THE DEFERRAL LADDER AND THE `integrate` VERB. `5wdoze` / `yocdq4` in the `integpath` Set handle a lane whose integration was ATTEMPTED and refused. This plan is the case where it was never attempted, so those do not cover it and this does not cover them.

## Scope check

- Over-scope: none. The shared suite-check and predicate, both drivers' call sites, and three test modules.
- Scope-Paths justification: `oc_runipd.py` holds `SuiteCheckResult`, `run_suite_check`, `integration_is_earned` and the oc call site (E-01..E-04); `agy_runipd.py` holds the agy call site that must pass the baseline through (E-06); `tests/test_novalnomerge_integration.py` is the suite that pins THIS gate's bug class and is where the incident fixture belongs; each driver's suite covers its own end-to-end path.
- BOTH DRIVER MODULES ARE THE HIGHEST-CONTENTION FILES IN THE REPOSITORY. Expect drift, re-locate by symbol, expect to rebase and re-run the full suite after any merge.
- Under-scope, stated rather than left as `none`: this child does not persist or display the verdict (`7m0aro`), does not fix the scope misattribution (`hyx1dg`), does not narrow honest limit (c), does not repair the pre-existing failures, and does not add the ladder or the `integrate` verb. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE: at authoring it is `1 failed, 5612 passed, 3 skipped, 2 xfailed` at HEAD `15445857`, and the failure is pre-existing. The criterion is that the AFTER failure set minus the BEFORE failure set is EMPTY, not that the suite is green.
- Targeted: `tests/test_novalnomerge_integration.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`.
- A REAL END-TO-END DEMONSTRATION on BOTH hosts in a throwaway repository: a permanently red unrelated test present, a lane that changes something else, and the lane INTEGRATING. Plus the refusal case: a lane that breaks a previously-passing test does not integrate and its branch is preserved.
- VALIDATE IN THE REAL CHECKOUT for `tests/test_run_viewer.py` (reads the gitignored `.aw/records/runs/`).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`); a pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda` governs the run's verification and integration semantics. This plan changes WHICH OBSERVATION earns integration, not whether verification is required, so no requirement changes. If the executor finds spec text asserting that integration requires a GREEN suite (rather than no-new-failures), NOTE IT for a spec amendment and do NOT edit the spec here: its §4.2 finding-code table is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

`integration_is_earned`'s docstring is the authoritative prose statement of the gate and MUST be updated: it currently says the driver-run suite decides when validation is off, which becomes "the driver-run suite's DELTA against the frozen base decides". Extend its existing "THE TWO MODES ARE ALTERNATIVES" and "HONEST LIMIT" paragraphs rather than replacing them, and add E-04's three limits.

Any `--help` or CHANGELOG text describing the integration gate must state the new behavior plainly, including that a pre-existing failure no longer blocks integration. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should the baseline be measured at `base_head` or at main's CURRENT head at integration time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: AT `base_head`, the frozen begin-time commit. Three reasons. It is ALREADY RECORDED in the begin receipt, so it needs no new state and cannot drift. It is the commit the lane was actually built on, so it is the honest counterfactual for "what did this lane change". And it is STABLE: main's current head moves under a long run as other agents commit, so a moving target would make the same lane earn or refuse depending on when it happened to finish, which is precisely the timing-dependent unfairness this plan exists to remove. The cost is honest limit (c) in E-04: a failure another agent introduces on main after `base_head` will look like this lane's fault. That is a real residual, is documented, and is narrower than the bug being fixed.

### OQ-02: Should a lane that FIXES a pre-existing failure be treated specially?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO SPECIAL CASE; the subset test already handles it correctly. A lane whose failing set is a strict subset of the base's earns integration, which is the right outcome for a lane that repaired something incidentally. E-05 pins this explicitly because the naive implementation (requiring set EQUALITY) would REFUSE such a lane, punishing an improvement, and that error is easy to make and invisible without a test. No credit, no reward, no separate reporting: it simply must not be blocked.

### OQ-03: What if the baseline suite run is itself flaky, so the same base yields different failing sets?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ACCEPT IT AND REPORT, do not retry or vote. A flaky test can appear in the lane's set and not the base's, producing a spurious refusal; the correct response is that the refusal NAMES the test (E-03, E-05), so an operator sees "1 NEW failure: <nodeid>" and can recognize a known flake immediately. Retrying or best-of-N would hide genuine regressions behind noise and would multiply the already-real cost of a baseline run. The sha-keyed cache also reduces exposure by measuring a given base once. This is stated as honest limit (b) in E-04 rather than engineered around, because the alternative trades a visible false refusal for an invisible false pass.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the extended `SuiteCheckResult` and the parsing code. Paste a real `run_suite_check` result showing the failing set populated and SORTED. Paste a case where the set is `None` (undeterminable) and state which condition produced it, confirming it is distinguishable from an empty tuple. Confirm by quoting the field that `passing` still means "observed exit 0" and its value is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the baseline capture code and the cache path, showing the key is the base commit sha. PROVE THE PRIMARY TREE WAS NOT MUTATED: paste `git status --short` and `git rev-parse HEAD` in the primary checkout immediately before and after a baseline measurement, both unchanged. State where the baseline ran (an isolated clone or scratch worktree of `base_head`) and confirm it was NOT a lane worktree, naming the `dh0uno` reason. Paste evidence the cache is reused within a run rather than re-measured per item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the changed branch of `integration_is_earned`. Show FOUR verdicts with their reasons: identical sets (earn), strict subset (earn), one new node (REFUSE, and the reason NAMES that node), and `None` on either side (refuse). Paste the validation-ON branch and confirm by diff that it is byte-unchanged, plus one probe showing a declined verifier still refuses even with a green suite.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the baseline timeout wiring showing it reuses `SUITE_CHECK_TIMEOUT_SECONDS` rather than a new constant. Paste a simulated baseline timeout showing the verdict REFUSES (not passes) and the reason says so. Quote all three honest limits from the updated docstring and confirm the pre-existing "HONEST LIMIT" text was extended rather than replaced.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL output of the seven delta cases. Quote the assertion for the strict-subset case and state in one sentence why requiring set EQUALITY would have been wrong (OQ-02). Paste the incident fixture using the real numbers (base `31 failed, 5505 passed`, lane `31 failed, 5563 passed`, identical FAILED sets) and show it EARNS. Paste the refusal message for the new-failure case showing it names the offending node.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THE PROOF THAT MATTERS. For BOTH hosts, in a throwaway repository with one permanently failing unrelated test: paste the lane INTEGRATING to main (show the merge commit on main). Then paste the same scenario against the PRE-FIX code showing it strands, so the contrast is demonstrated rather than asserted. Then paste the refusal case: a lane that breaks a previously-passing test does not integrate and `git branch --list` shows its lane preserved. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is empty. If the agy host could not be demonstrated, SAY SO PLAINLY rather than inferring from the oc result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the five paths in `Scope-Paths`. Do NOT change the meaning of `passing`. Do NOT touch the validation-ON branch of `integration_is_earned`. Do NOT weaken the fail-closed posture for a suite that cannot run. Do NOT reach the base by `git stash`, `git checkout`, or any mutation of the primary checkout. Do NOT measure the baseline in a lane worktree. Do NOT add a flag that lets an operator disable the delta check. Do NOT repair the pre-existing failing tests. Do NOT edit spec `25kzda`. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and both driver modules are the highest-contention files in it: run `aw runs` before starting, and if a driver file is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. The pass criterion is a DELTA (after-minus-before failure set is empty), not an absolute count. Do not report the pre-existing `test_orchestrator_retirement` failure as caused by this change, and do not fix it here.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `SuiteCheckResult`, `run_suite_check`, `integration_is_earned`, `IntegrationVerdict`, both `run_suite_check` call sites, and `ipd_lifecycle.read_receipt` by name.

THE ITEM THAT MATTERS MOST IS V-06's PRE-FIX CONTRAST. This plan's whole claim is that a lane no longer strands because of an unrelated red test. A test suite that only ever runs against the FIXED code cannot demonstrate that; it would pass identically if the delta logic were subtly inverted. Show the same scenario failing before and succeeding after.

THE SECOND-MOST IMPORTANT IS THE FAIL-CLOSED PATH IN V-03. This change makes a previously-refusing gate pass in more cases, which is exactly the direction in which a mistake becomes dangerous: a bug that makes the delta LOOK empty would auto-integrate unverified work into main. An undeterminable set MUST refuse. If you find yourself defaulting an unknown to "no failures", stop.

On completion, close backlog `ciesaj`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits.
