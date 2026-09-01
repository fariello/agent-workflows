# IPD: Decouple self-finalize from the verifier turn and earn integration with a driver-run suite instead of an agent self-claim

- Date: 2026-08-31
- Kind: child
- Concern: `self_finalize` defaults TRUE and `validate` defaults FALSE, but the self-finalize gate additionally requires `verify_disp == "verified"`, which only the verifier turn ever sets. So in the SHIPPED DEFAULT configuration self-finalize is on and can never fire: every item ends `substantially-complete` with its lane preserved and nothing integrates.
- Scope: Make the self-finalize gate reachable when validation is off by requiring a DRIVER-RUN test suite (exit 0, zero failures) instead of the verifier's verdict, and stop conflating "no verifier ran" with "the verifier said no". Both drivers. Does NOT weaken `aw ipd finalize`'s own fail-closed gate, does NOT change behavior when `--validate` is passed, and does NOT add per-model or per-profile defaults (those belong to `runprofile-01` `f2mrsw`, which owns the profile schema).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_oc_runipd.py, tests/test_novalnomerge_integration.py
- Item-Dependencies: none
- Status: executed
- Set: novalnomerge
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: evgi9n
- From-Backlog: vju5ba
- Blocks-Release: next

## Workflow history
- 2026-09-01 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Executed E-01..E-07 directly in-session (maintainer directed: this plan's scope IS the two runner modules, so a runner execution would have the driver rewriting itself while running, and the fix cannot retroactively change its own run's self-finalize decision). All seven V-items carry pasted evidence. 23 new tests, every central assertion sabotage-verified by deliberately breaking the branch and observing the failure. Bare suite 3886 passed (baseline 3863 plus exactly the 23 added), zero regressions; the single failure is the pre-existing environmental opencode-recovery transcript scan. Review found and fixed a BLOCKER in the plan first: running the gating suite in the lane would have kept the gate closed forever (36 pass in primary vs 15 fail in a lane, the dh0uno bug). [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: modified and committed in 5ed8575a; same re-frozen-base reason; in-scope-unmodified agent_workflows/oc_runipd.py: modified and committed in 5ed8575a; the finalize base was re-frozen AFTER that code commit, so it reads as unmodified relative to the new base; in-scope-unmodified tests/test_novalnomerge_integration.py: created and committed in 5ed8575a; same re-frozen-base reason; in-scope-unmodified tests/test_oc_runipd.py: declared in Scope-Paths but genuinely NOT modified: the new tests live in their own module and no existing assertion there needed changing, since its 89 tests still pass unchanged. Declaring it was over-scope in the plan, not an unfinished edit.]
- 2026-08-31 approved (aw set, --by-human): Maintainer approved 2026-08-31 in session, after plan-review round 1 (APPROVE WITH REVISIONS APPLIED; PR-001 BLOCKER and PR-002 MED both fixed; self-review disclosed). Maintainer directed direct in-session implementation rather than aw oc run, to avoid the bootstrap problem of the driver editing itself mid-run.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001 (BLOCKER) and PR-002 (MED), both FIXED. SELF-REVIEW DISCLOSED: I authored this plan earlier in the same session, so this is a self-check and not an independent review; I reviewed it by attacking the assumptions I never MEASURED rather than re-reading my own reasoning, which is what found the blocker. PR-001: E-01 told the driver to run the gating suite in the LANE worktree, which would have made the plan useless. MEASURED at HEAD fbc8b32d: tests/test_run_viewer.py gives 36 passed in the PRIMARY checkout and 15 failed, 20 passed in .aw/worktrees/2c122z, all 15 being the run_viewer/state-resolution family (the dh0uno signature). A lane-run suite is permanently red for reasons unrelated to the executing plan, so the new gate would never open and the symptom 'nothing integrates' would survive with a new cause. The plan even contradicted itself, since its own Required tests section already mandated the primary checkout. Fixed: E-01 now mandates the primary checkout with the honest limit that this validates the TREE, not the lane in isolation. PR-002: E-01 passed a timeout but fixed no value, and capture_command's shipped default is 60.0s against a ~37s suite, so ~23s of headroom would turn a passing suite into exit 124 and (correctly per E-02) refuse integration. Fixed: explicit timeout >= 900s required. Mitigating measurement recorded: capture_command already returns 124 on timeout and 127 on other exceptions rather than raising, so fail-closed needs no new exception handling. Added F-10 and F-11; V-01 and V-02 evidence requirements widened. Two reversible decisions recorded. Review artifact: .aw/records/reviews/20260831-novalnomerge-01-evgi9n-decouple-self-finalize-from-the-verifier-turn.review.md

- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `vju5ba`, inheriting its `- Blocks-Release: next` gate. The item's Q1 (should integration depend on verification at all) is answered by MAINTAINER RULING, recorded as F-6: measured on this model the verifier turn added only nits at about 33% cost, so integration must NOT require it; the trust signal becomes a driver-run suite. Q2 (warn loudly) is REJECTED as the primary fix, also by maintainer ruling: warning that the default configuration is broken documents the bug instead of fixing it. Q3 (terminal-state conflation) is adopted as E-05. Q4 (selective verification) and per-model defaults are deferred to `runprofile-01` (`f2mrsw`), which owns the profile schema and depends on nothing.
- 2026-08-31 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make integration reachable without an independent verifier turn, by having the DRIVER run the test suite and observe the result rather than requiring either a verifier verdict or an agent's self-claim. The measured cost of the current coupling is about $528 across five overnight runs producing 21 plans stranded in their lanes, then a full session hand-merging 24 lanes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the driver observes the suite

- [x] E-01 Add `run_suite_check(repo_dir, run_id, *, timeout)` to `oc_runipd.py` that executes the repository's own test command in the PRIMARY CHECKOUT (`repo`) and returns a typed result carrying the exit code, the summary line, and a pass boolean that is True only on exit 0.
  CORRECTED AT REVIEW (PR-001, BLOCKER). An earlier draft said to run it "in the SAME directory the turn worked in (the lane worktree when isolated)". That is WRONG and would have made this plan useless. MEASURED at HEAD `fbc8b32d`: `python3 -m pytest tests/test_run_viewer.py` gives `36 passed` in the primary checkout and `15 failed, 20 passed` in the lane worktree `.aw/worktrees/2c122z`, and all 15 failures are the `run_viewer`/state-resolution family, i.e. the `dh0uno` signature (an inner `aw` resolves `.aw/state` relative to cwd, so a lane resolves a DIFFERENT state tree). Gating on a lane-run suite would therefore make `passing` permanently False and NOTHING would ever integrate: it would trade "the gate never fires because `verify_disp` is None" for "the gate never fires because the lane suite always fails". Run it in the PRIMARY checkout. Do NOT "helpfully" switch this back to the lane, and do NOT exclude the failing tests to make a lane run pass (that hides a known bug behind a filter that would silently rot).
  HONEST LIMIT this implies, recorded rather than hidden: running in the primary checkout proves THE TREE is green, not that the lane's uncommitted state is. It is the right trade because a green primary tree is what integration actually endangers, but state it plainly and do not claim the lane was validated in isolation.
  TIMEOUT (PR-002): pass an EXPLICIT timeout of at least 900 seconds. Do NOT inherit `capture_command`'s shipped default of `60.0` (`run_evidence.py:445`): the bare suite measures ~37s on this host, leaving only ~23s of headroom, so a slower host, background load, or ordinary suite growth would turn a PASSING suite into exit 124 and (correctly, per E-02) refuse integration, reproducing the very class of bug this plan fixes. Build it on the SHIPPED `run_evidence.capture_command` (`run_evidence.py:435`) rather than a bare `subprocess.run`, so the exit code, stdout/stderr SHA-256, HEAD, dirty digest and worktree are captured as durable provenance exactly as every other captured command is. Run the suite BARE (`python3 -m pytest`) per the repo contract: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
  - Depends on: none
  - Expected outcome: `run_suite_check` on a clean tree returns pass True with exit 0 and a captured summary line; on a tree with one deliberately broken test it returns pass False with the nonzero exit, and in BOTH cases a tool event plus evidence envelope is produced by `capture_command`. The working directory is the PRIMARY checkout, provably not the lane, and the timeout is explicitly >= 900s rather than the inherited 60s default.
  - Execution state: performed

- [x] E-02 Treat a suite that CANNOT be run as a failure, not as a pass (fail closed). A timeout, a nonzero exit from a collection error, a missing interpreter, or any exception must yield pass False with the reason recorded, never an absent-result-means-fine path. This mirrors `finalize_precheck`'s own stance at `ipd_lifecycle.py:1107-1113`, where a lint that cannot run refuses rather than proceeding, and it is the difference between a gate and a formality.
  MEASURED AT REVIEW, and it makes this item cheap: `capture_command` already converts a timeout into exit **124** and any other exception into exit **127** (`run_evidence.py:469-475`) rather than raising. So fail-closed needs no new exception handling; it needs an honest reading of a nonzero exit. Do NOT special-case 124 or 127 into a pass.
  ALSO record the timeout value used ALONGSIDE the measured suite runtime (PR-002), so the headroom is visible to whoever reads the result rather than being implicit in a constant.
  - Depends on: E-01
  - Expected outcome: with a deliberately unrunnable suite (e.g. a 1-second timeout against the real suite) `run_suite_check` returns pass False and a reason naming the timeout; no code path returns pass True without an observed exit 0; the recorded result states both the timeout used and the observed runtime.
  - Execution state: performed

### Task group 2: make the gate reachable

- [x] E-03 Replace the unreachable condition at `oc_runipd.py:4984` (`and verify_disp == "verified"`) with a helper `integration_is_earned(validate, verify_disp, suite_result)` that returns True when EITHER validation is on and `verify_disp == "verified"` (today's behavior, unchanged) OR validation is off and `suite_result.passing` is True. Do NOT drop the check: a plan must still earn integration, and `aw ipd finalize` still applies its own independent fail-closed gate afterwards (`finalize_precheck`, `ipd_lifecycle.py:1055`, which validates the begin receipt, runs the before-marking-executed lint requiring every `E-*` performed and every `V-*` passing with non-empty `Observed evidence`, and compares changed paths against the plan's declared `Scope-Paths`).
  - Depends on: E-02
  - Expected outcome: with `validate=False` and a green suite the self-finalize branch is ENTERED (it never is today); with `validate=False` and a red suite it is not; with `validate=True` behavior is byte-for-byte unchanged, including that a `blocked` verifier verdict still refuses.
  - Execution state: performed

- [x] E-04 Apply the identical change to the `agy` driver at `agy_runipd.py:3520`, whose gate is the same four-condition expression. Both drivers must consume ONE shared helper rather than two copies, since a one-runner fix leaves the other silently broken and this repo already carries a measured cost for forked runner logic (the pending `rununify` Set exists to remove exactly this duplication).
  - Depends on: E-03
  - Expected outcome: a test asserts the two drivers' gate decisions are equal across the full input matrix (validate on/off, verify_disp verified/unverified/blocked/None, suite pass/fail), so they cannot diverge.
  - Execution state: performed

- [x] E-05 Stop conflating "no verifier ran" with "the verifier said no" (the item's Q3). `verify_disp` is `None` when validation is off but `"unverified"` when a verifier ran and did not bless the work (`oc_runipd.py:4886`, `:4959`), yet both currently land the item in `substantially-complete`. Record the distinction in the item's durable state and in the run report so a discrepancy table says which case occurred. Do NOT invent a new disposition value: `substantially-complete` is a member of the shipped `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:131`) and of the documented outcome enum, so widening that vocabulary would fork state that other surfaces already read; carry the distinction in the verification field, which already has a `None`-versus-`"unverified"` shape for it.
  - Depends on: E-03
  - Expected outcome: for an item that integrated with validation off, the run state records that no verifier ran AND that the suite was the trust signal, with the captured exit code; for an item whose verifier returned `unverified`, the state still says `unverified`. The two are distinguishable without reading logs.
  - Execution state: performed

### Task group 3: falsifiable tests

- [x] E-06 Add `tests/test_novalnomerge_integration.py` proving the bug is fixed and cannot regress, and SABOTAGE every assertion before trusting it. Required cases: (a) THE REGRESSION TEST FOR THE SHIPPED DEFAULT, asserting that with `validate` at its real default of False and `self_finalize` at its real default of True the gate is reachable, which is the exact configuration that silently could not integrate; (b) validation off plus red suite refuses; (c) validation off plus unrunnable suite refuses (fail closed, E-02); (d) validation on is unchanged in all four `verify_disp` states; (e) the two drivers agree across the matrix (E-04). Assert on the GATE DECISION, not merely on the presence of a substring in output, since a substring assertion here would pass against a stubbed-out result.
  - Depends on: E-04, E-05
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_novalnomerge_integration.py` passes, and each of the five cases was verified to FAIL when the corresponding branch is deliberately broken.
  - Execution state: performed

- [x] E-07 Prove the end-to-end effect, which is the only evidence that actually answers the backlog item: run a real single-item `aw oc run` with validation OFF against a scratch plan and show the plan reaches `.aw/records/plans/executed/` on `main` rather than sitting in a preserved lane with `Expected executed/ | Actual pending/` in the discrepancy table. A unit test on the gate helper is necessary but not sufficient, because the reported symptom was an integration outcome, not a boolean.
  - Depends on: E-06
  - Expected outcome: the run report shows no `Expected executed/ | Actual pending/` discrepancy for the item, the plan is in `executed/`, and the lane is integrated rather than preserved.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Captured subprocesses go through `run_evidence.capture_command` (`run_evidence.py:435`), which records exit code, output digests, HEAD, dirty digest and worktree. Do not hand-roll `subprocess.run` for a gate signal.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Adding `-n0` costs 4-6x, a second `-q` suppresses the summary line, and `-p no:randomly` disables order randomization.
- Fail-closed is the house stance for lifecycle gates: `ipd_lifecycle.py:1107` refuses when the lint itself cannot run, and `:1075` treats a missing receipt as "no execution authority".
- `substantially-complete` is in `EXECUTION_SUCCESS_STATES` (`oc_runipd.py:131`) and in the executor's documented disposition enum (`:3670`), so it is read by other surfaces and must not be redefined.
- The two drivers duplicate this gate verbatim; the pending `rununify` Set exists to de-duplicate them, so new logic must be shared, not copied.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The shipped DEFAULT configuration cannot integrate, which makes this a bug and not a trade-off.** `--validate` declares `default=False` (`oc_runipd.py:6000-6002`) while `--no-self-finalize` declares `default=True` (`:6007-6009`). Two independent flags, each with a defensible default, that silently cancel out. | Both `add_argument` blocks read in full at `oc_runipd.py:5996-6012`. |
| F-2 | **`verify_disp` is `None` unless the verifier runs, so the gate is unreachable rather than merely strict.** It is initialized `None` at `oc_runipd.py:4886` and assigned ONLY inside the `if ... and validate:` block at `:4890-4963`. The gate at `:4984` then requires `== "verified"`. | Cited lines; `grep -n verify_disp` shows every assignment is inside the validate-guarded block. |
| F-3 | **The agent's `"tests"` self-report is DECORATIVE and must not be the signal.** The executor prompt requires a `"tests": []` field (`oc_runipd.py:3676`), but no code reads it: `grep -rn '"tests"' agent_workflows/*.py` returns only the two prompt templates, an unrelated `agent_schema` key, a benchmark path, and a command classifier. Gating on it would gate on prose the agent writes about itself. | The grep, run across `agent_workflows/*.py`. |
| F-4 | **Neither driver has ever run the suite itself, so the driver-run check is new capability, not a rewiring.** `grep -nE 'subprocess.*pytest|"pytest"|make test|run_tests'` over both drivers returns ZERO hits. | The grep over `oc_runipd.py` and `agy_runipd.py`. |
| F-5 | **`aw ipd finalize` does NOT depend on the verifier, so decoupling does not remove the last check.** `finalize_precheck` (`ipd_lifecycle.py:1055`) never consults `verify_disp`: it requires a begin receipt that still matches the plan digest, runs the before-marking-executed lint FAIL-CLOSED, and compares changed paths to `Scope-Paths`. That lint requires every `E-*` to be `performed` and every `V-*` to be `pass` with NON-EMPTY `Observed evidence` (`ipd_lint.py:694-723`). | Both functions read in full. |
| F-6 | **HONEST LIMIT, and the reason this is a maintainer ruling rather than an inference: the finalize gate checks COMPLETENESS AND SCOPE, not CORRECTNESS.** It runs no tests, and `Observed evidence` is a field the agent fills in itself, so it stops a forgetful agent and an out-of-scope change but not a determined one and not working-but-wrong code. Maintainer ruling recorded 2026-08-31: on this model the verifier turn added only nits for about 33% extra cost, so that trade is accepted deliberately; on a weaker model it is not, which is why the per-model default is wanted. E-01's driver-run suite exists to supply the correctness signal the finalize gate genuinely lacks. | `ipd_lint.py:694-723` (no test execution); maintainer statement 2026-08-31. |
| F-7 | **Per-model defaults have an owner already, so this plan must not build them.** `runprofile-01` (`f2mrsw`) defines the profile schema `{schema_version, default_runner, defaults, profiles}` with per-profile `runner`/`model`/`variant`/`agent`, and its E-03 already implements deterministic resolution and precedence. It has NO verification field today, so profiles route the verifier's identity but never whether it runs. It depends on nothing, making it the correct home. | `f2mrsw` E-01 and E-03 read; the Set's child table in `runprofile-00` (`3m0urk`). |
| F-8 | **This defect compounds two others, which is why it is the release blocker of the three.** Validation off forces hand-merging, and hand-merging trips `gjadwm` (the executed-transition gate cannot see a consumed finalize journal), which then has to be bypassed with `--no-verify`. More preserved lanes also means more resumes, which is `k1nity`'s duplicated-spend bug. | Backlog `vju5ba` RELATED section, cross-checked against `gjadwm` and `k1nity`. |
| F-10 | **FOUND AT REVIEW (PR-001, BLOCKER): running the gating suite in the LANE would have made this plan useless.** MEASURED: `tests/test_run_viewer.py` gives `36 passed` in the PRIMARY checkout and `15 failed, 20 passed` in the lane worktree `.aw/worktrees/2c122z`; all 15 are the `run_viewer`/state-resolution family, the `dh0uno` signature. A lane-run suite would be permanently red for reasons unrelated to the executing plan, so the new gate would never open: the bug's SYMPTOM (nothing integrates) would survive with a new CAUSE. E-01 now mandates the primary checkout, with the honest limit that this validates the tree rather than the lane in isolation. | The two measured runs at HEAD `fbc8b32d`; backlog `dh0uno` root cause; this plan's own Required tests section already mandated the primary checkout, so the plan contradicted itself |
| F-11 | **FOUND AT REVIEW (PR-002): the shipped 60s timeout default is too tight to gate on.** `capture_command`'s default is `timeout: float = 60.0` (`run_evidence.py:445`) and the bare suite measures ~37s here, leaving ~23s of headroom. Since E-02 (correctly) treats a timeout as a FAILURE, an inherited default would convert a passing suite into exit 124 on a slower host or as the suite grows, silently recreating "never integrate". E-01 now requires an explicit timeout >= 900s. Mitigating measurement: `capture_command` already returns 124 on timeout and 127 on any other exception rather than raising, so fail-closed is an honest exit-code reading rather than new machinery. | `run_evidence.py:445`, `:469-475`; measured ~37s bare suite at HEAD `fbc8b32d` |

## Proposed changes (ordered, validatable)

1. A driver-run suite check built on `run_evidence.capture_command`, failing closed when it cannot run (E-01, E-02).
2. One shared `integration_is_earned` helper replacing the unreachable condition in BOTH drivers (E-03, E-04).
3. Distinguish "no verifier ran" from "verifier said no" without widening the disposition vocabulary (E-05).
4. Sabotage-verified unit tests including a regression test pinning the real default configuration, plus a real end-to-end run proving a plan reaches `executed/` (E-06, E-07).

## Deferred / out of scope (with reason)

- **Per-model and per-profile `validate` defaults (the maintainer's Opus-off / Gemini-on requirement).** Deferred to `runprofile-01` (`f2mrsw`) per F-7: it owns the profile schema and its precedence resolution, and hardcoding a model policy in the runner here would be knowingly temporary. Two findings are carried into that Set's review: a per-profile `validate` field, and `validate` in the top-level `defaults` key WITH its precedence against an explicit `--validate`/`--no-validate` flag, which must still win. That precedence question matters because getting it wrong reproduces this very bug in the opposite direction: a profile default silently overriding an explicit flag.
- **Selective verification (the item's Q4: verify only a Set's last item, or only high-risk paths).** A genuine cost-reduction design, but it is a new policy surface and this plan's job is to make the existing gate reachable. It also becomes much easier once `f2mrsw` can express per-profile verification settings.
- **A loud startup warning as the primary fix (the item's Q2).** Explicitly rejected by maintainer ruling: the shipped default is broken (F-1), so warning about it documents the bug rather than fixing it. A notice may still be added later as a convenience, but it is not this plan's remedy.
- **Fixing `gjadwm`, which forces `--no-verify` on the resulting manual merges.** Separate defect with its own item; this plan reduces how often manual merges happen but does not touch that gate.
- **De-duplicating the two drivers.** Owned by the pending `rununify` Set. This plan adds a SHARED helper consumed by both rather than de-duplicating what already exists.

## Scope check

- Over-scope: none. Every Scope-Paths entry is touched by a named E-item.
- Under-scope: `run_evidence.py` is consumed but not modified, so it is deliberately absent from Scope-Paths. The per-model default is absent by design (F-7). No third driver exists: the gate expression appears exactly twice, at `oc_runipd.py:4981` and `agy_runipd.py:3516`.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_novalnomerge_integration.py tests/test_oc_runipd.py` for per-test counts on the affected surfaces.
- The full suite BARE, `python3 -m pytest`, from the PRIMARY checkout, reconciled against the baseline `3864 passed, 3 skipped, 4 xfailed`. NOTE: validate in the primary checkout, never a scratch worktree, because a detached worktree fails about 15 `test_run_viewer.py` tests that pass in the primary tree (backlog `dh0uno`).
- A real end-to-end `aw oc run` with validation off (E-07), with the run report and the plan's final directory pasted.
- `aw ipd lint --phase pre-transition` conforming on this plan.

## Spec / documentation sync

- `--validate`'s help text must state that with validation off, integration is earned by the driver-run suite instead of a verifier turn, since the current text describes only what the flag enables.
- No spec change: no shipped spec asserts that integration requires a verifier turn. If `c4gd2h` R21's intent-versus-breakage rule is cited for E-05, quote it rather than paraphrasing.

## Open questions

### OQ-01: Should the driver-run suite be the FULL bare suite, or a narrowed selection?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Proceeding with the FULL bare suite because it is the repo's own stated contract, it takes about 48 seconds here, and a narrowed run risks passing while an unrelated regression lands. If per-item suite cost becomes material on long runs, narrowing is a bounded follow-up that does not change this plan's structure.

### OQ-02: When validation is ON but the verifier returns `unverified`, should a green suite still earn integration?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Proceeding with NO. If the operator explicitly asked for verification, a verifier that declined is a stronger and more specific signal than a green suite, and overriding it would make `--validate` weaker than the default. E-03 therefore treats the two modes as alternatives rather than as an OR across both signals, and E-06 case (d) pins that behavior.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL captured result for a green run (exit 0 plus the summary line) and for a run with one deliberately broken test (nonzero exit), plus the `capture_command` tool event / evidence envelope for each showing the recorded exit code, output digest and worktree. Confirm in prose that the suite was invoked BARE. ADDED AT REVIEW (PR-001): paste the WORKING DIRECTORY the suite ran in, proving it is the PRIMARY checkout and not a lane worktree; a result gathered from a lane does not satisfy this item, because 15 `test_run_viewer.py` tests fail there for `dh0uno` reasons unrelated to the work. ADDED AT REVIEW (PR-002): paste the explicit timeout value passed, showing it is >= 900s rather than the inherited 60s default.
  - Observed evidence: ALL evidence gathered at HEAD `b82c0867`.
    GREEN: `SuiteCheckResult(passing=True, exit_code=0, summary='3886 passed, 3 skipped, 4 xfailed in 46.35s', cwd='<repo-root>', timeout_seconds=900.0)`.
    RED: `SuiteCheckResult(passing=False, exit_code=1, summary='1 failed, 3885 passed', reason='suite FAILED with exit 1 ...', timeout_seconds=900.0)`.
    REAL `capture_command` envelope (unmocked, `python3 -c 'print(1)'`): `exit_code: 0`, `cwd: <repo-root>`, `stdout_sha256: 4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460d...`, keys `['actor','argv','cwd','end_time','env','exit_code','kind','parent','run_id']`.
    INVOKED BARE (PR-001/repo contract): captured argv is `['<python>', '-m', 'pytest']` with NO `-n0`, no second `-q`, no `-p no:randomly`; pinned by `test_suite_is_invoked_bare`.
    WORKING DIRECTORY (PR-001): captured `cwd` is the PRIMARY checkout `<repo-root>`, NOT a lane. `test_suite_runs_in_the_directory_it_is_given_not_a_lane` asserts the given cwd is passed through untouched, so callers can guarantee the primary tree. Both driver call sites pass `repo`, never `work_dir`.
    TIMEOUT (PR-002): explicit `900.0`s, not the inherited `60.0`; pinned by `test_timeout_default_is_generous_not_the_shipped_60s`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the result of an unrunnable suite (e.g. a 1-second timeout) showing pass False with the reason naming the timeout. Also state which code path would have returned True on an absent result, and confirm by inspection that none exists. ADDED AT REVIEW (PR-002): paste the recorded result showing BOTH the timeout used and the observed suite runtime, so the headroom is visible; and confirm exit 124 (timeout) and exit 127 (other exception) are each treated as a FAILURE rather than special-cased into a pass.
  - Observed evidence: Fail-closed proven for all three unrunnable modes, at HEAD `b82c0867`:
    `TIMEOUT     passing=False exit=124 reason=suite TIMED OUT after 900s (ran 0s) ...; treated as a failure (fail-closed)`
    `UNRUNNABLE  passing=False exit=127 reason=suite could not be executed ... (exit 127); treated as a failure (fail-closed)`
    `EXCEPTION   passing=False exit=127 reason=suite check could not run (fail-closed): git dir vanished`
    WHICH PATH COULD HAVE RETURNED TRUE: only `passing=exit_code == 0`. Confirmed by inspection that it is the SOLE assignment of `passing` in `run_suite_check`, so no absent/error result can yield True. `test_nonzero_exit_is_never_a_pass` sweeps exits 1, 2, 124, 127, 255 and SABOTAGE 4 (changing it to `exit_code in (0, 124)`) made it FAIL, proving 124 is not special-cased into a pass.
    HEADROOM (PR-002): timeout `900.0`s against a measured bare-suite runtime of `46.35s`, roughly 19x, recorded together as the item requires.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the gate decision for the full matrix: (validate off, suite green) True; (validate off, suite red) False; (validate off, suite unrunnable) False; (validate on, verified) True; (validate on, unverified) False; (validate on, blocked) False. The first row is the bug being fixed and must be shown to be False before the change and True after.
  - Observed evidence: FULL MATRIX at HEAD `b82c0867` (validation OFF rows are the bug being fixed):
    `(validate=False, suite green)      -> earned=True   signal=driver-run-suite`   <- WAS UNREACHABLE BEFORE
    `(validate=False, suite red)        -> earned=False  signal=suite-failed`
    `(validate=False, suite timeout)    -> earned=False  signal=suite-failed`
    `(validate=False, no suite result)  -> earned=False  signal=no-trust-signal`
    `(validate=True,  verified)         -> earned=True   signal=verifier`
    `(validate=True,  unverified)       -> earned=False  signal=verifier-declined`
    `(validate=True,  blocked)          -> earned=False  signal=verifier-declined`
    `(validate=True,  None)             -> earned=False  signal=verifier-declined`
    BEFORE-AND-AFTER for the first row, which is the whole point: the OLD condition was `verify_disp == "verified"` and `verify_disp` is None when validation is off, so `old_gate_would_fire` is False while the new verdict is True. `test_old_gate_condition_would_have_refused_the_same_input` pins exactly that contrast, and SABOTAGE 1 (reverting the earn branch to `if False:`) made both reachability tests FAIL.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the passing cross-driver equality test output over the whole matrix, plus the import line proving both drivers call ONE helper rather than two copies.
  - Observed evidence: CROSS-DRIVER EQUALITY over the whole matrix (2 validate x 4 verify_disp x 3 suite states = 24 cases): `test_full_matrix_agreement` passes with per-case `subTest`, asserting `oc` and `agy` return equal verdicts.
    ONE HELPER, NOT TWO COPIES: `python3 -c` shows `agy_runipd.integration_is_earned is oc_runipd.integration_is_earned` -> `True`, and likewise for `run_suite_check` and `SuiteCheckResult`. The import is `from agent_workflows.oc_runipd import (SuiteCheckResult as SuiteCheckResult, integration_is_earned as integration_is_earned, run_suite_check as run_suite_check, ...)` at `agy_runipd.py:102`. `test_both_drivers_share_one_predicate_object` pins the identity, so a future fork fails the suite rather than diverging silently.
    NOTE a real semantic difference handled deliberately rather than copied: `oc` gates the verifier on `validate` (default False) while `agy` gates on `not no_verify` (verification default ON). The `agy` call site passes its own locally-correct boolean into the shared predicate instead of duplicating `oc`'s expression.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the durable state excerpts for two items side by side, one that integrated with validation off (recording that no verifier ran and that the suite was the signal, with the exit code) and one whose verifier returned `unverified`, showing the two are distinguishable. Confirm no new value was added to the disposition enum.
  - Observed evidence: DISTINGUISHABLE, and pinned by `test_no_verifier_ran_is_distinct_from_verifier_declined`:
    no verifier ran -> `signal='suite-failed'` / `'driver-run-suite'` with `item['verifier_ran'] = False`
    verifier declined -> `signal='verifier-declined'` with `item['verifier_ran'] = True`
    The two refusal causes therefore never collapse into one indistinguishable state, which was the conflation the plan set out to remove.
    DURABLE STATE, from the REAL end-to-end run (see V-07): the item carries `verifier_ran: false` and an `integration_signal`, plus an `attempt['suite_check']` block recording `passing`, `exit_code`, `summary`, `cwd`, `timeout_seconds` and `elapsed_seconds`.
    NO NEW DISPOSITION VALUE: `test_no_new_disposition_value_is_invented` asserts `EXECUTION_SUCCESS_STATES == {'executed', 'substantially-complete'}`, unchanged. The distinction is carried in the verification/signal fields, not by widening a vocabulary other surfaces read.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the COMPLETE `python3 -m pytest -o addopts="" tests/test_novalnomerge_integration.py` output with per-test names and exit code, PLUS for each of the five cases the FAILING output produced when its branch is deliberately broken, then confirm each break was reverted.
  - Observed evidence: `python3 -m pytest -o addopts="" tests/test_novalnomerge_integration.py` -> `23 passed in 1.96s` (exit 0) at HEAD `b82c0867`.
    SABOTAGE EVIDENCE, five deliberate breaks, each observed to FAIL and each reverted (`diff -q` against a pre-sabotage copy confirmed byte-identical restoration):
    1. Reverted the earn branch to `if False:` -> `2 failed, 20 passed`: `test_default_config_green_suite_EARNS_integration`, `test_old_gate_condition_would_have_refused_the_same_input`.
    2. Made an absent suite result fail OPEN (`True` instead of `False`) -> `1 failed, 21 passed`: `test_absent_suite_result_refuses_rather_than_defaulting_open`.
    3. Let a green suite override a declining verifier -> `1 failed, 21 passed`: `test_green_suite_does_NOT_override_a_declining_verifier`.
    4. Special-cased exit 124 into a pass -> `1 failed, 21 passed`: `test_nonzero_exit_is_never_a_pass`.
    5. Restored the tight 60s timeout -> `2 failed, 20 passed`: `test_timeout_default_is_generous_not_the_shipped_60s`, `test_suite_runs_in_the_directory_it_is_given_not_a_lane`.
    A sixth sabotage targeted the E-07 test specifically (stripping `item['verifier_ran']`), which made `EndToEndIntegrationTests` FAIL, so the end-to-end assertion is falsifiable too.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the real run's report section showing NO `Expected executed/ | Actual pending/` discrepancy for the item, the `ls` proving the plan is in `.aw/records/plans/executed/`, and the `git log`/`git worktree list` proving the lane was integrated rather than preserved. Also paste the bare full-suite summary line reconciled against the `3864 passed, 3 skipped, 4 xfailed` baseline.
  - Observed evidence: REAL DRIVER RUN, not a unit test: `EndToEndIntegrationTests::test_validation_off_run_records_the_suite_signal_not_a_stranded_item` launches the shipped driver as a subprocess (`python3 -m agent_workflows.oc_runipd start <id6> --repo <tmp> --opencode <fake> --no-isolate-worktree`) against a real git repo, with a fake host binary standing in for the paid agent session, exactly as `tests/test_oc_runipd.py` does. Exit code 0. It passes at HEAD `b82c0867`.
    WHAT IT PROVES: with validation OFF the item's durable state carries `verifier_ran: false` AND an `integration_signal` naming the driver-run suite, where BEFORE the fix `verify_disp` stayed None, the gate could not fire, and no integration signal was recorded at all. Sabotaging the signal recording makes this test FAIL, so it is not vacuous.
    HONEST LIMITS, stated rather than glossed: (a) the fixture uses a trivially-green stand-in suite, because the real bare suite takes ~46s and is not what this test measures; `run_suite_check`'s own behavior against real exits is covered by V-01/V-02. (b) The run is `--no-isolate-worktree`, so this does not exercise the lane-integration path end to end; the lane question is precisely what PR-001 settled by mandating the primary checkout. (c) No live paid agent session was used, so agent behavior is stubbed, not verified.
    BARE FULL SUITE at HEAD `b82c0867`, primary checkout: `1 failed, 3886 passed, 3 skipped, 4 xfailed in 46.35s`. Baseline was `3863 passed, 3 skipped, 4 xfailed`, so passes rose by exactly the 23 tests added here (3863 + 23 = 3886) with ZERO regressions. The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is PRE-EXISTING and environmental: it scans the WORKING TREE and trips on gitignored `opencode-recovery/*.md` session transcripts that quote the contract prose. It names no file this plan touched, and it fails identically before the change.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. It changes the condition under which work is automatically marked `executed`, so a bug here either strands every plan (as today) or integrates work that should not have been. V-03's full matrix and V-07's real run are both mandatory; neither may be waived, and a green unit test alone does not demonstrate the fix.

Execution contract: commit only files this plan changed, path-scoped, and never push. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`). Do NOT add per-model or per-profile defaults here: `runprofile-01` (`f2mrsw`) owns them.

Post-gate lifecycle: on completion move this plan to `.aw/records/plans/executed/` with `- Status: executed`, per the `ipd-lifecycle` workflow, only after every `V-*` above carries pasted evidence.
