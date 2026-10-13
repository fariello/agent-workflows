# IPD: Deny the interactive-question permission on non-isolated unattended opencode turns

- Date: 2026-10-11
- Kind: child
- Concern: `oc_runipd.run_opencode` sets the R4.1 deny posture (`permission.external_directory=deny`, `permission.question=deny` via `OPENCODE_CONFIG_CONTENT`) only inside `if work_dir:`. So a NON-isolated unattended opencode turn gets no host denial at all. It relies on `--auto` and the `StallWatchdog` (backlog `8ctu3u`, research `7so8uz` Finding 5: 24 of the 45 non-isolated driver-turn asks came after the posture landed in commit `8a491d4c1`, while isolated-turn asks fell 1,102 -> 19 -> 0). The narrowing is deliberate for `external_directory`, because a non-isolated turn legitimately works in the main checkout. The same reasoning does NOT cover `question`, since no human can ever answer an interactive question on any `opencode run` child the driver launches.
- Scope: Take backlog option (b). A non-isolated unattended opencode turn gets a QUESTION-ONLY denial (`{"permission": {"question": "deny"}}`), supplied through the same `lane_containment.build_permission_policy_env` merge (R4.3), observed through the same `observe_opencode_policy` probe (R4.2), and recorded through the same `lane_containment.record_host_posture` with an HONEST partial-denial posture record (R4.1a). The isolated turn's policy, prompt, and record stay byte-identical. The non-isolated turn's PROMPT stays byte-identical (R1.3). `external_directory` is NOT denied on a non-isolated turn. Amend spec `7ckptx` so this is a stated requirement and not a code-only narrowing (closing the gap plan `heglfv` OQ-02 named). EXCLUDES antigravity entirely (R4.1c forbids changing its posture), any `PERMISSION_TIMEOUT` change (owned by `e6zeta`), and any new CLI flag or config knob.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/lane_containment.py, tests/test_non_isolated_permission_posture.py, tests/test_oc_runipd.py, .aw/records/specs/implementing/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 8ctu3u
- From-Spec: 7ckptx
- Set: 4xtpvg
- Order: 2
- Highest E allocated: 09
- Author: opencode
- Id: thzrpo
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Reviewed at HEAD 8fc33dcd8. Prototype of E-05 measured a 2s->62s regression in the stall-watchdog fake-host test (new E-09/V-09, tests/test_oc_runipd.py added to Scope-Paths); E-06 harness demonstrated and given an unparseable-operator case; gate challenge answered (F-11, OQ-02); 15db4k ordering and scope fence added. Record: .aw/records/reviews/20261011-4xtpvg-02-thzrpo-deny-the-interactive-question-permission-on-non-isolated-una.review.md.
- 2026-10-12 to-review (aw set): Authored from backlog 8ctu3u: option (b), deny question only on non-isolated opencode turns; spec 7ckptx R4.1d/A8d amendment

- 2026-10-12 draft (opencode): created.

## Goal

Make sure no unattended opencode turn, isolated or not, can stall on an interactive question that has no
answerer, without refusing any ordinary main-checkout work a non-isolated turn does. Write that rule
into spec `7ckptx` so the isolated/non-isolated split stops being a code-only convention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline

- [x] E-01 CAPTURE A BASELINE BEFORE THE FIRST EDIT. Run the bare suite (`python3 -m pytest`) and record its summary line and the node IDs of any failure. Also run `aw check` and keep its violation list for comparison. Also record per-test durations for the 40 launcher-touching test files E-09 names (`python3 -m pytest -o addopts="" -q -n auto -m 'not slow and not livecorpus' --durations=0 <files>`), saved outside the repo, as E-09's comparison baseline. Authoring measured at HEAD `fa5b433ee` that `tests/test_commit_run_trailers_env.py::test_byte_identity_without_env_vars`, `::test_scratch_repo_end_to_end_stamps_trailers` and `::test_malformed_values_dropped_with_warning` ALREADY FAIL in a lane with no change applied, because they spawn `aw commit` subprocesses that are sensitive to the ambient lane environment. Those three are a pre-existing condition and NOT a bar for this plan. Bars are by node ID: nothing that passed in the baseline may fail afterwards.
  - Depends on: none
  - Expected outcome: a recorded baseline summary line, failing node-ID list, `aw check` violation list, and the per-test duration list.
  - Execution state: performed

### Task group 2: the shared policy and its honest record (`lane_containment`)

- [x] E-02 ADD THE NON-ISOLATED POLICY CONSTANT next to `lane_containment.LANE_PERMISSION_POLICY`: `NON_ISOLATED_PERMISSION_POLICY: dict[str, str] = {"question": "deny"}`. Give it a `#:` block (the module's convention for constants) that says three things. FIRST, why `question` is denied: every driver child is `opencode run` with stdout piped and no TTY, so an interactive question has no answerer in ANY mode, and the driver prompt already tells the agent "do not invoke an interactive question tool or wait for human input" (`runner_shared.build_prompt`). SECOND, why `external_directory` is NOT denied: a non-isolated turn legitimately works in the main checkout and outside it, so denying it would refuse ordinary work. THIRD, cite research `7so8uz` Finding 5 and backlog `8ctu3u` as the measurement behind it. Do NOT change `LANE_PERMISSION_POLICY`.
  - Depends on: E-01
  - Expected outcome: the new constant exists with its rationale block, and `LANE_PERMISSION_POLICY` is byte-identical.
  - Execution state: performed

- [x] E-03 ADD AN HONEST PARTIAL-DENIAL POSTURE RECORD. The existing `lane_containment.opencode_posture_record` hard-codes a reason stating that BOTH classes are refused, and a layer string saying "external-directory and interactive-question asks are denied". Using it for a question-only request would be exactly the false parity claim R4.1a forbids. So add `HOST_POSTURE_PARTIAL = "partial-denial"` beside `HOST_POSTURE_DENIED`/`HOST_POSTURE_NONE`. That comment already says "three capability tiers" while defining two, and this addition makes the comment true. Then add `opencode_non_isolated_posture_record(request: PermissionPolicyRequest) -> HostPostureRecord` returning `host="opencode"`, `posture=HOST_POSTURE_PARTIAL`, a `reason` that names the classes `request.policy` denies and states that `external_directory` is NOT denied on a non-isolated turn and is left to `--auto`, and `layers` that name the question denial followed by `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL`, plus `requested`/`policy_source`/`policy_note` from the request just as the isolated constructor does. Leave `opencode_posture_record` byte-identical so the isolated record cannot move.
  - Depends on: E-02
  - Expected outcome: a third posture tier and a constructor whose record never uses the word `denied` as its posture and names what is and is not denied.
  - Execution state: performed

- [x] E-04 UPDATE THE MODULE'S OWN DOCUMENTATION OF THE GAP so it does not contradict the code. (a) The R4 section header (the `# WHAT IS NOT UNIFORM` block whose `OPENCODE` row reads "a real denial. `permission.external_directory` and `permission.question` are set to `deny`") gets a sentence saying this applies to ISOLATED turns, and that a non-isolated turn gets the question-only denial. (b) The `RESIDUAL LIMITS:` paragraph in `PERMISSION_TIMEOUT`'s `#:` block currently says "a non-isolated unattended turn can still ask (carrier `8ctu3u`)". Replace it with the narrowed truth: a non-isolated turn can still be asked an `external_directory` permission, which `--auto` approves, but it can no longer be asked an interactive question (plan `thzrpo`). Keep the antigravity half of that paragraph and keep `PERMISSION_TIMEOUT` at `0.0`.
  - Depends on: E-03
  - Expected outcome: both comment blocks describe the post-change behavior, and no constant value changes.
  - Execution state: performed

### Task group 3: the driver (`oc_runipd`)

- [x] E-05 APPLY THE POSTURE TO BOTH TURN CLASSES IN `oc_runipd.run_opencode`, in the block that begins "lanectn Order 03 (`lhmrhx`) E-01/E-02/E-03". Replace the `if work_dir:` gate with a selection: an isolated turn (`work_dir` truthy) requests `lane_containment.LANE_PERMISSION_POLICY` and records `opencode_posture_record`, exactly as today. A non-isolated turn requests `lane_containment.NON_ISOLATED_PERMISSION_POLICY` and records `opencode_non_isolated_posture_record`. Both go through the SAME `build_permission_policy_env(child_env.get(OPENCODE_RUNTIME_CONFIG_ENV), policy)` merge (R4.3), the SAME `observe_opencode_policy(opencode, child_env, policy_request.policy)` probe (R4.2), and the SAME `record_host_posture` call. Do not fork a second env construction. Rewrite the "ISOLATED TURNS ONLY, deliberately narrower than the bounds below" paragraph so it states the new split and its reason, and cite the amended spec requirement from E-07. Do NOT touch the prompt builders: R1.3 requires the non-isolated prompt to stay byte-identical, and this change is env-only. KNOWN COST, accepted and recorded: a non-isolated turn now pays the R4.2 probe (`opencode --version` plus `opencode debug config`). Authoring measured about 2.05s wall time for both on this machine. The probe never raises and never aborts a turn, but it runs the CONFIGURED `--opencode` executable under `_POLICY_PROBE_TIMEOUT_SECONDS` (30s) per call. That is why E-09 exists: a fake host that ignores its argv now costs up to 60s per non-isolated turn in tests (measured at review, F-10).
  - Depends on: E-03
  - Expected outcome: a non-isolated child env carries `{"permission": {"question": "deny"}}` (merged with any operator value), an isolated child env is unchanged, and both attempts carry a `host_posture` record.
  - Execution state: performed

### Task group 4: behavioral coverage

- [x] E-06 ADD `tests/test_non_isolated_permission_posture.py`. Every test drives `oc_runipd.run_opencode` with `oc_runipd.observe_opencode_policy` patched to return a fixed `lane_containment.PolicyObservation` (built with `lane_containment.evaluate_policy_observation`) and `subprocess.Popen` patched with a fake. The fake records the `env` keyword and raises a sentinel exception for the agent launch, but delegates any `git` argv to the real `Popen`, because `run_opencode` runs git before the launch. The test catches the sentinel. So no real host is spawned. This harness shape (a temp `git init` repo, `state["options"]["opencode"] = "/bin/false"`, and an isolated case passing a temp `work_dir`) was demonstrated at review against a prototype of E-05: it decoded `{"permission": {"question": "deny"}}` for non-isolated and both denials for isolated, and read the record from `item["host_posture"]`, since the bare item has no `attempts`. Each test clears ambient `OPENCODE_CONFIG_CONTENT` with `mock.patch.dict(os.environ, ...)` and a pop, because a driver-launched test run inherits the parent turn's value (the `cfgj8s` lesson). Asserted behaviors: (a) NON-ISOLATED, no operator value: the decoded `OPENCODE_CONFIG_CONTENT` is exactly `{"permission": {"question": "deny"}}` and has no `external_directory` key. (b) ISOLATED: the decoded value denies both `external_directory` and `question`, i.e. unchanged. (c) NON-ISOLATED with operator value `{"permission": {"external_directory": "allow", "question": "allow"}, "x": 1}`: `x` survives, `external_directory` stays `allow`, `question` becomes `deny`, and the recorded `policy_source` is `merged-with-operator`. (d) NON-ISOLATED posture record (`item["host_posture"]` when the item has no attempt list, per `lane_containment.record_host_posture`'s fallback): `posture == "partial-denial"`, `requested_policy == {"question": "deny"}`, the `policy_observation` is present, and the record's `reason` text mentions `external_directory` as not denied (an assertion on a produced OUTPUT, not on source). (e) The isolated posture record still has `posture == "denied"`. (f) NON-ISOLATED with an UNPARSEABLE operator value (`"not json"`): the decoded value is exactly `{"permission": {"question": "deny"}}` and the recorded `policy_source` is `override-unparseable-operator`, so the loud-override path R4.3 requires is covered for the new turn class too. Write no `inspect`, `ast`, or source-text reads (GUIDING_PRINCIPLES P16).
  - Depends on: E-05
  - Expected outcome: six passing behavioral tests that fail if the non-isolated policy is removed or the isolated one is weakened.
  - Execution state: performed

### Task group 5: contract and user-facing record

- [x] E-07 AMEND SPEC `7ckptx` (declared in `- Scope-Paths:`). After R4.1c, add `R4.1d` stating: an unattended NON-isolated opencode turn MUST run with the interactive-question class denied, supplied through the same runner-owned runtime config, merged per R4.3, observed per R4.2, and recorded per R4.1a as a PARTIAL denial. It MUST NOT have `external_directory` denied, because its ordinary work is in the main checkout. Its prompt stays byte-identical per R1.3. Add acceptance criterion `A8d` after `A8c`: decode the child env for a non-isolated opencode turn and show `question` denied and `external_directory` absent from the request, and show its attempt record says `partial-denial` and never `denied`. Cite research `7so8uz` and backlog `8ctu3u`. Log the amendment with `aw specs note <spec> --message "AMENDED <date> (4xtpvg-02 thzrpo): R4.1d and A8d added ..."`. Do NOT change the spec's `- Status:`.
  - Depends on: E-05
  - Expected outcome: spec carries R4.1d and A8d plus a workflow-history note, and `aw specs check` conforms.
  - Execution state: performed

- [x] E-08 ADD ONE `CHANGELOG.md` LINE under the pending 2.0.0 entry, in the file's existing `- Changed:` style and with no em or en dashes (user-facing prose): `aw oc run` now denies the interactive-question permission on non-isolated (`--no-isolate-worktree`) turns too, so an unattended turn cannot wait on a question nobody can answer. Out-of-checkout file access on those turns is unchanged.
  - Depends on: E-05
  - Expected outcome: one new CHANGELOG line, dash-free.
  - Execution state: performed

- [x] E-09 KEEP THE EXISTING FAKE-HOST TEST FAST. Review found that one existing test, `tests/test_oc_runipd.py` `StallWatchdogTests.test_stall_watchdog_terminates_silent_child_and_marks_interrupted`, goes from about 2s to about 62s once E-05 lands (F-10). It drives a NON-isolated `start` with a fake `--opencode` script that runs `time.sleep(60)` whatever its argv, so the new R4.2 probe now waits out the 30s probe timeout twice (`--version`, `debug config`). Fix the FAKE, not the probe: make the script exit non-zero immediately unless `sys.argv[1:2] == ["run"]`, then sleep as before. The test still proves what it proves (stall watchdog on the agent turn). The probe then records `unverified` with its reason, which this test does not assert on. Demonstrated at review: with that edit and an E-05 prototype applied, the test gave `1 passed in 2.98s`. Afterwards, re-run the 40 test files that contain `run_opencode`, `_capture_turn_argv`, `host_sandbox_profile`, `host_posture`, `OPENCODE_CONFIG_CONTENT`, `_DRIVER_CMD` or `make_fake_executable` with `--durations=0`, and compare per-test durations with the same run on the E-01 baseline. Any OTHER test slowed by more than 10s for the same reason gets the same fix. Each such fix is an out-of-scope path, justified at finalize with `--scope-reason`. At review no other test was affected (the next-largest delta was 1.5s).
  - Depends on: E-05
  - Expected outcome: no test's duration rises by more than 10s against the E-01 baseline because of the new probe, and the stall-watchdog test still passes with its assertions unchanged.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Tests assert behavior and never pin source structure or text (GUIDING_PRINCIPLES P16; `AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
- `lane_containment` constants document themselves with `#:` comment blocks, not docstrings (recorded by plan `0b7fic`'s conventions).
- Rules both drivers consume live in `lane_containment`, and each driver keeps a thin adapter (spec R2.6; the module's R4 header "WHY THIS LIVES HERE AND NOT IN A DRIVER").
- Tests that build a child env must neutralize ambient `OPENCODE_CONFIG_CONTENT`, because a test run launched by the driver inherits the parent turn's value (backlog `cfgj8s`, plan `heglfv`).
- A plan amending a spec declares the `.spec.md` in `- Scope-Paths:` and logs the change with `aw specs note` (`AGENTS.md` "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT").
- Run the suite bare as `python3 -m pytest`; clear defaults with `-o addopts=""` only for a narrowed per-test view (`AGENTS.md` repository development contract).

## Findings

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| F-1 | The deny posture is gated on isolation | `oc_runipd.run_opencode`: `if work_dir:` wraps `build_permission_policy_env`, `observe_opencode_policy`, `record_host_posture`. Authoring probe (`tmp/pr/probe.py`, gitignored): non-isolated child env `OPENCODE_CONFIG_CONTENT` = `None`, posture `None`; isolated = `{"permission": {"external_directory": "deny", "question": "deny"}}`, posture `denied`. | The gap the backlog names is real at HEAD `fa5b433ee`. |
| F-2 | The narrowing's stated reason covers `external_directory` only | Comment in `run_opencode`: "a non-isolated turn legitimately works in the main checkout, where an external-directory denial would refuse its ordinary work." | Nothing in code or spec justifies leaving `question` undenied. |
| F-3 | No driver child can ever answer an interactive question | `run_opencode` launches `opencode run ... --format json` with `stdout=subprocess.PIPE` and no TTY. `runner_shared.build_prompt` says "This run is non-interactive: do not invoke an interactive question tool or wait for human input". | Denying `question` refuses nothing legitimate. This answers the backlog's "nobody has checked whether a non-isolated turn ever legitimately needs `question`". |
| F-4 | Isolated turns already run with `question` denied, including review turns | Isolation is the default (`isolate_worktree`), and review sweeps run in a lane (`runner_shared.turn_runs_in_review_sweep_lane`). Research `7so8uz` Finding 5: 676 isolated turns after 2026-09-05 under this posture. | Workflows that tell the agent to prompt (e.g. `/plan-review`'s "Ask and wait") already run under the denial in the common case, so this is not a new constraint on them. |
| F-5 | The merge helper already supports a custom policy | `build_permission_policy_env(operator_value, policy=None)`. Authoring call with `{"question": "deny"}` and an operator value `{"permission":{"external_directory":"allow","question":"allow"},"x":1}` returned `{"permission": {"external_directory": "allow", "question": "deny"}, "x": 1}`, source `merged-with-operator`. | No new merge logic is needed. R4.3 holds unchanged. |
| F-6 | The real host honors a question-only runtime config | `OPENCODE_CONFIG_CONTENT='{"permission":{"question":"deny"}}' opencode debug config` on opencode 1.18.35 reported `"question": "deny"` in the resolved `permission` object. | The R4.2 probe will observe `conforms_to_request: true` for the new policy. |
| F-7 | The existing posture constructor would misreport a question-only request | `opencode_posture_record` reason: "the runner supplied `permission.external_directory=deny` and `permission.question=deny` ... so the host itself refuses both request classes". | E-03 needs a separate constructor, or the record would violate R4.1a. |
| F-8 | Spec `7ckptx` is silent on the non-isolated posture | R4.1 opens "An unattended isolated turn MUST ..."; plan `heglfv` OQ-02 recommended amending the spec so the split is a stated requirement. | E-07 closes that gap. |
| F-10 | Probing non-isolated turns slows one existing fake-host test by about 60s | Review prototype (E-05's selection, applied in a throwaway worktree): the 40 launcher-touching test files gave `3 failed, 635 passed` (the same 3 pre-existing failures), but `--durations=0` showed `test_stall_watchdog_terminates_silent_child_and_marks_interrupted` at `61.89s` against `2.15s` at baseline. Its fake `--opencode` sleeps 60s for every argv, so both R4.2 probe calls hit the 30s `_POLICY_PROBE_TIMEOUT_SECONDS`. With the fake made to exit for non-`run` argv it gave `1 passed in 2.98s`. No other test moved by more than 1.5s. | E-09. |
| F-11 | No driver launch path gives the child an answerer (the gate's challenge) | `run_opencode` argv: `opencode run ... --format json`, never `-i/--interactive` or `--attach` (opencode 1.18.35 `run --help` lists both as opt-in; neither string occurs in `oc_runipd.py`); `popen_kwargs` pipe stdout, pass no stdin, and set `start_new_session`; `--auto` (default True, `start` parser) appends `--auto`. The other `run_opencode` caller, `host_sandbox_profile._capture_turn_argv`, is an argv capture whose fake `Popen` raises before launch. Research `7so8uz` Finding 2: the 333 asks NOT attributable to an `aw-*` session are human TUI sessions, which are not driver children. | F-3 holds: no driver child can answer. |
| F-9 | Prototype regression scan | With E-05's selection applied as a throwaway edit (since reverted), the nine `run_opencode`-calling test files gave `3 failed, 247 passed`, and the 3 failures (`test_commit_run_trailers_env.py`) also fail with the change reverted. | The change does not break existing launcher tests. E-01 re-baselines at execution time. |

## Proposed changes (ordered, validatable)

1. Baseline (E-01).
2. `lane_containment`: new policy constant, partial-denial tier and constructor, corrected comments (E-02..E-04).
3. `oc_runipd.run_opencode`: choose the policy by isolation and apply it to both turn classes through the one existing path (E-05).
4. New behavioral test file (E-06).
5. Spec R4.1d/A8d plus history note (E-07). CHANGELOG line (E-08).
6. Keep the existing fake-host stall test fast under the new probe (E-09).

## Deferred / out of scope (with reason)

- Denying `external_directory` on a non-isolated turn. Out of scope by design: backlog `8ctu3u` and F-2 establish that it would refuse the turn's ordinary work, which is the worse failure.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Antigravity. Spec R4.1c forbids changing its posture, and it has no denial mechanism (R4.1b).
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Arming or deleting `PERMISSION_TIMEOUT`. Owned by backlog `e6zeta`.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Re-measuring the host-log ask corpus after this change. The corpus is machine-local and unreachable from a lane (plan `0b7fic` E-01). Any future non-isolated deadlock is a `bug` to be filed with this plan as context, as the backlog item says.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: one temptation named. An executor may want to unify the two posture constructors or make the policy configurable. Do neither: the isolated record must stay byte-identical, and spec R4.4c's KISS ruling rejects new knobs for this surface.
- Under-scope: the non-isolated `external_directory` ask stays possible, approved by `--auto`. That is the deliberate residual, and E-04/E-07 document it. Non-isolated turns now pay roughly 2s for the R4.2 probe (F-6 timing). That is accepted, because R4.2 forbids requesting a policy without observing it. In tests, a fake host that ignores argv pays up to 60s; E-09 covers this (F-10).

## Required tests / validation

1. Bare suite `python3 -m pytest`, actual summary line pasted, compared by node ID with the E-01 baseline (E-06, E-05). Then the E-09 duration comparison over the 40 launcher-touching files (E-09).
2. `python3 -m pytest -o addopts="" tests/test_non_isolated_permission_posture.py -v`, with every test named and its result shown (E-06).
2a. `python3 -m pytest -o addopts="" -q --durations=1 "tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_terminates_silent_child_and_marks_interrupted"` passes in under 10s (E-09).
3. Mutation check in a throwaway process via `mock.patch.object(lane_containment, "NON_ISOLATED_PERMISSION_POLICY", {})` or an equivalent monkeypatch, never by editing source: test (a) or (d) must FAIL while (b) and (e) still PASS. Patch the name where `oc_runipd` reads it (`lane_containment.NON_ISOLATED_PERMISSION_POLICY` attribute access at call time); if E-05 binds it at import, patch that binding instead. Paste `git status --porcelain` afterwards (E-06).
4. A search of the new test file showing zero `inspect.`, `ast.`, and zero `read_text()` on an `agent_workflows/` path (E-06).
5. Real-host observation of the non-isolated policy: run `opencode debug config` with `OPENCODE_CONFIG_CONTENT` set to `build_permission_policy_env(None, NON_ISOLATED_PERMISSION_POLICY).env_value`, and paste the resolved `permission` object's `question` value. If the binary is unavailable in the workspace, say so and paste F-6 as the dated measurement instead (E-05).
6. `aw specs check` conforming (E-07); `aw check` showing no new `check.spec-criteria-uncovered` for `7ckptx` (A8d must be traced). `aw ipd lint --phase pre-transition` conforming. `aw check` showing no new violations against E-01's baseline. `aw sanitize --agent` exit 0 (E-01..E-09).

## Spec / documentation sync

- Spec `7ckptx` IS AMENDED (declared in `- Scope-Paths:`). WHY: today the isolated/non-isolated split exists only in a code comment. Plan `heglfv` found that this leaves a test defending a property that no requirement states. Since this plan changes that property, writing it into the spec as R4.1d with acceptance criterion A8d is what keeps code and contract aligned. The amendment adds an obligation for non-isolated turns and leaves every existing requirement as it is. The spec's `- Status:` is not changed.
- `lane_containment` and `oc_runipd` comments are updated in E-04/E-05 so they do not keep describing the old gap.
- `CHANGELOG.md` gets one user-facing line (E-08).

## Open questions

### OQ-01: Which of backlog `8ctu3u`'s three options to take?

- Blocking: no
- Status: resolved
- Owner: maintainer (by approving or rejecting this plan)
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE IN FAVOR OF (b), with the maintainer's approval of this plan as the confirming decision the backlog item asks for. The item called (b) "most promising and UNMEASURED: nobody has checked whether a non-isolated turn ever legitimately needs `question`". F-3 settles that: every driver child is a piped, TTY-less `opencode run`, and the driver's own prompt forbids interactive questions, so a non-isolated turn never legitimately needs `question`. F-4 shows the denial already runs on the default isolated path, including review turns, without breaking them. (a) leaves a known-unanswerable class open for no benefit. (c) gives up a host denial that F-6 shows works. Neither weakens anything (b) keeps. If the maintainer prefers (a) or (c), the right move is to reject this plan and record that choice on backlog `8ctu3u`, not to edit this plan down.

### OQ-02: Does any driver launch path give a child an answerer for `question` (the gate's challenge)?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: No. See F-11: the only agent-launch `Popen` in `run_opencode` uses `opencode run --format json` with no `-i`/`--attach`, piped stdout, no stdin and a new session. The only other caller captures argv and never launches. So the plan does not need to narrow to unattended runs. Recorded as D-2 in the review record.

### OQ-03: Should an existing test's fake host be edited to absorb the new probe cost?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Yes, the fake is edited (E-09). The alternatives were rejected. Skipping the R4.2 probe on non-isolated turns violates R4.2 ("MUST OBSERVE"), which this plan extends to them via R4.1d. Lowering `_POLICY_PROBE_TIMEOUT_SECONDS` changes a production bound to suit a test. Accepting a 60s test regression costs every bare-suite run. Demonstrated at review (F-10). Recorded as D-3.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted baseline `python3 -m pytest` summary line, the list of failing node IDs (or "none"), and the baseline `aw check` violation summary, all captured before any edit, together with the HEAD commit they were taken at.
  - Observed evidence: Taken at HEAD `94702ee34173c520b94dd4bfb4317cda4e10504d`.
    Bare pytest suite baseline summary:
    `1 failed, 8125 passed, 4 skipped, 18 xfailed, 3 warnings in 842.74s`
    Failing node IDs:
    `tests/test_verbs_write_nothing_to_repo.py::test_the_verbs_write_nothing_to_the_repository` (passed in 0.79s when run in isolation; failure caused by concurrent workspace activity during baseline run).
    Baseline `aw check` violation summary:
    `178 findings across 2656 all (errors 5, warnings 4, info 169)`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/lane_containment.py` excerpt showing the new `NON_ISOLATED_PERMISSION_POLICY = {"question": "deny"}` with its `#:` block, plus pasted output of `python3 -c "from agent_workflows import lane_containment as l; print(l.LANE_PERMISSION_POLICY, l.NON_ISOLATED_PERMISSION_POLICY)"` showing the isolated policy still `{'external_directory': 'deny', 'question': 'deny'}`.
  - Observed evidence: `git diff agent_workflows/lane_containment.py`:
    ```python
    +#: The permission policy requested for non-isolated unattended opencode turns (spec R4.1d).
    +#:
    +#: `question` is denied: every driver child is `opencode run` with stdout piped and no TTY, so an
    +#: interactive question has no answerer in ANY mode, and the driver prompt already tells the agent
    +#: "do not invoke an interactive question tool or wait for human input" (`runner_shared.build_prompt`).
    +#:
    +#: `external_directory` is NOT denied: a non-isolated turn legitimately works in the main checkout
    +#: and outside it, so denying it would refuse ordinary work.
    +#:
    +#: Measured by research `7so8uz` Finding 5 and backlog `8ctu3u`.
    +NON_ISOLATED_PERMISSION_POLICY: dict[str, str] = {
    +    "question": "deny",
    +}
    ```
    Output of `python3 -c "from agent_workflows import lane_containment as l; print(l.LANE_PERMISSION_POLICY, l.NON_ISOLATED_PERMISSION_POLICY)"`:
    `{'external_directory': 'deny', 'question': 'deny'} {'question': 'deny'}`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of a one-off `python3 -c` call that builds `opencode_non_isolated_posture_record(build_permission_policy_env(None, NON_ISOLATED_PERMISSION_POLICY)).as_dict()` and prints it, showing `posture: partial-denial`, `requested_policy: {'question': 'deny'}`, and a reason naming `external_directory` as not denied. Also the same call for `opencode_posture_record(build_permission_policy_env(None)).as_dict()`, showing `posture: denied` and the reason text unchanged against `git show HEAD:agent_workflows/lane_containment.py`. Also the pasted output showing that the non-isolated record's `posture` is not `"denied"` and that its `containment_layers` list ends with every entry of `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL`.
  - Observed evidence: Output of `python3 -c`:
    ```
    NON-ISOLATED RECORD:
    {'containment_layers': ['R4.1 host denial: interactive-question asks are '
                            'denied',
                            'R1 prompt purity: the emitted prompt names no path '
                            'outside the lane',
                            'R4.4 driver-side bound: MAX_TURN_TIMEOUT terminates '
                            "the turn regardless of the host's permission "
                            'decision'],
     'host': 'opencode',
     'policy_note': 'no operator value present; runner policy supplied alone',
     'policy_source': 'runner',
     'posture': 'partial-denial',
     'reason': "the runner supplied `permission.question=deny` through the host's "
               'runtime config; `external_directory` is not denied on a '
               'non-isolated turn and is left to `--auto`',
     'requested_policy': {'question': 'deny'}}
    ISOLATED RECORD:
    {'containment_layers': ['R4.1 host denial: external-directory and '
                            'interactive-question asks are denied',
                            'R1 prompt purity: the emitted prompt names no path '
                            'outside the lane',
                            'R4.4 driver-side bound: MAX_TURN_TIMEOUT terminates '
                            "the turn regardless of the host's permission "
                            'decision'],
     'host': 'opencode',
     'policy_note': 'no operator value present; runner policy supplied alone',
     'policy_source': 'runner',
     'posture': 'denied',
     'reason': 'the runner supplied `permission.external_directory=deny` and '
               "`permission.question=deny` through the host's runtime config, so "
               'the host itself refuses both request classes',
     'requested_policy': {'external_directory': 'deny', 'question': 'deny'}}
    POSTURE NOT DENIED: True
    CONTAINMENT LAYERS ENDSWITH WITHOUT_HOST_DENIAL: True
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff` excerpts of the R4 header `OPENCODE` row and of the `RESIDUAL LIMITS:` paragraph showing the post-change wording, plus pasted `python3 -c "from agent_workflows import lane_containment as l; print(l.PERMISSION_TIMEOUT)"` printing `0.0`.
  - Observed evidence: Excerpt of R4 header `OPENCODE` row:
    ```diff
    -#   OPENCODE     a real denial. `permission.external_directory` and `permission.question` are set to
    -#                `deny` through the runner-supplied runtime config, so the host itself refuses.
    +#   OPENCODE     a real denial. For isolated turns, `permission.external_directory` and
    +#                `permission.question` are set to `deny` through the runner-supplied runtime
    +#                config, so the host itself refuses. A non-isolated turn gets the question-only
    +#                denial, leaving external-directory access open for ordinary main-checkout work.
    ```
    Excerpt of `RESIDUAL LIMITS:` paragraph (on `MAX_TURN_TIMEOUT`'s docblock following prior sibling `15db4k` execution, as documented in ORDERING WITH SIBLING `15db4k`):
    ```diff
    -#: RESIDUAL LIMITS: the R4.1 deny posture applies to ISOLATED opencode turns only (`oc_runipd.run_opencode`
    -#: applies `build_permission_policy_env` inside `if work_dir:`), so a non-isolated unattended turn can
    -#: still ask (carrier `8ctu3u`); and antigravity has NO denial posture at all, permanently and by design
    -#: (R4.1, R4.1c), so there `MAX_TURN_TIMEOUT` is the whole of the bound half.
    +#: RESIDUAL LIMITS: a non-isolated opencode turn can still be asked an `external_directory`
    +#: permission, which `--auto` approves, but it can no longer be asked an interactive question
    +#: (plan `thzrpo`, carrier `8ctu3u`); and antigravity has NO denial posture at all, permanently
    +#: and by design (R4.1, R4.1c), so there `MAX_TURN_TIMEOUT` is the whole of the bound half.
    ```
    `PERMISSION_TIMEOUT`: deleted by executed sibling plan `15db4k` prior to this turn; `RESIDUAL LIMITS:` paragraph was updated at its current home on `MAX_TURN_TIMEOUT` exactly as directed by the plan's ORDERING note.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `git diff agent_workflows/oc_runipd.py` showing the `if work_dir:` gate replaced by the policy selection, with one `build_permission_policy_env`/`observe_opencode_policy`/`record_host_posture` sequence serving both classes. The pasted real-host observation from Required tests item 5 (the `question` value in the resolved `permission` object, produced by `observe_opencode_policy`'s own probe command `opencode debug config`), or an explicit unavailability statement citing F-6. Also the pasted result of the existing `tests/test_turn_bounds.py::test_non_isolated_prompt_byte_identical_and_names_neither_bound` passing, as evidence that R1.3 prompt byte-identity survived.
  - Observed evidence: `git diff agent_workflows/oc_runipd.py`:
    ```diff
    -        if work_dir:
    -            policy_request = lane_containment.build_permission_policy_env(
    -                child_env.get(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV)
    -            )
    -            child_env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV] = (
    -                policy_request.env_value
    -            )
    -            observation = lane_containment.observe_opencode_policy(
    -                opencode, child_env, policy_request.policy
    -            )
    -            lane_containment.record_host_posture(
    -                state,
    -                lane_containment.opencode_posture_record(policy_request),
    -                observation=observation,
    -            )
    +        policy_request = lane_containment.build_permission_policy_env(
    +            child_env.get(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV),
    +            policy=(
    +                lane_containment.LANE_PERMISSION_POLICY
    +                if work_dir
    +                else lane_containment.NON_ISOLATED_PERMISSION_POLICY
    +            ),
    +        )
    +        child_env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV] = (
    +            policy_request.env_value
    +        )
    +        observation = lane_containment.observe_opencode_policy(
    +            opencode, child_env, policy_request.policy
    +        )
    +        lane_containment.record_host_posture(
    +            state,
    +            (
    +                lane_containment.opencode_posture_record(policy_request)
    +                if work_dir
    +                else lane_containment.opencode_non_isolated_posture_record(
    +                    policy_request
    +                )
    +            ),
    +            observation=observation,
    +        )
    ```
    Real-host observation (`OPENCODE_CONFIG_CONTENT='{"permission":{"question":"deny"}}' opencode debug config`):
    ```json
      "permission": {
        "websearch": "deny",
        "webfetch": "deny",
        "question": "deny"
      }
    ```
    Prompt byte-identity test:
    ```
    tests/test_turn_bounds.py::test_non_isolated_prompt_byte_identical_and_names_neither_bound PASSED [100%]
    ============================== 1 passed in 0.58s ===============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the pasted `python3 -m pytest -o addopts="" tests/test_non_isolated_permission_posture.py -v` output with each of the six tests named and PASSED. The pasted mutation run (Required tests item 3) showing the split: non-isolated tests FAIL and isolated tests PASS. `git status --porcelain` after the mutation showing no production file modified. The pasted search output showing zero `inspect.`/`ast.`/source `read_text()` uses. The pasted bare `python3 -m pytest` summary line, with any failing node IDs shown as a subset of V-01's baseline list.
  - Observed evidence:
    Six behavioral tests:
    ```
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_isolated_no_operator_value_denies_both_classes PASSED [ 16%]
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_with_unparseable_operator_value_loudly_overrides PASSED [ 33%]
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_isolated_posture_record_reports_denied PASSED [ 50%]
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_posture_record_reports_partial_denial PASSED [ 66%]
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_with_operator_value_merges_and_preserves_keys PASSED [ 83%]
    tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_no_operator_value_denies_question_only PASSED [100%]
    ============================== 6 passed in 1.59s ===============================
    ```
    Mutation check (`mock.patch.object(lane_containment, 'NON_ISOLATED_PERMISSION_POLICY', {})`):
    ```
    FAILED tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_with_operator_value_merges_and_preserves_keys
    FAILED tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_posture_record_reports_partial_denial
    FAILED tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_with_unparseable_operator_value_loudly_overrides
    FAILED tests/test_non_isolated_permission_posture.py::NonIsolatedPermissionPostureTests::test_non_isolated_no_operator_value_denies_question_only
    ========================= 4 failed, 2 passed in 1.94s ==========================
    ```
    Status after mutation: no production files modified.
    AST/inspect check: zero matches found via `grep -E "inspect\.|ast\.|read_text\(" tests/test_non_isolated_permission_posture.py`.
    Bare pytest suite summary:
    `8175 passed, 4 skipped, 18 xfailed, 3 warnings in 763.15s (0:12:43)` (0 failures, 0 regressions).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: `git diff` of the spec showing R4.1d and A8d, the spec's `## Workflow history` line added by `aw specs note`, an unchanged `- Status: implementing`, and pasted `aw specs check` output conforming. Also the pasted `aw check` output, filtered to `7ckptx`, showing no new `check.spec-criteria-uncovered` versus V-01's baseline.
  - Observed evidence: Spec diff adds R4.1d and A8d.
    Workflow history note: `- 2026-10-13 amended (4xtpvg-02 thzrpo): R4.1d and A8d added (deny question on non-isolated opencode turns, spec 7ckptx)`.
    Status remains `- Status: implementing`.
    `aw specs check`: `aw specs check: all specs conform. 40 specs checked.`
    `aw check | grep -C 2 "7ckptx"`: `No findings for 7ckptx`
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: `git diff CHANGELOG.md` showing exactly one added line, plus pasted output of a search of that added line for the characters U+2013 and U+2014 returning no match. Also the pasted `aw sanitize --agent` result exiting 0 and `aw check` showing no new violations against V-01's baseline.
  - Observed evidence: `git diff CHANGELOG.md`:
    `+- Changed: \`aw oc run\` now denies the interactive-question permission on non-isolated (\`--no-isolate-worktree\`) turns too, so an unattended turn cannot wait on a question nobody can answer. Out-of-checkout file access on those turns is unchanged.`
    Dash check (U+2013 / U+2014): `Contains U+2013: False, Contains U+2014: False`.
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":4946,"findings":0,"evidence":["leak-scan"],"next":null}`
    `aw check`: 178 findings across 2656 all (no new violations against baseline).
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: `git diff tests/test_oc_runipd.py` showing only the fake script's argv guard added and no assertion changed. The pasted Required-tests item 2a run, passing in under 10s. The pasted `--durations=0` comparison: the largest per-test increases against the E-01 duration baseline, with no test up by more than 10s, re-derived at execution (the review measurement in F-10 is context, not the bar). Any further test fixed under E-09 is listed with its `--scope-reason`.
  - Observed evidence: `git diff tests/test_oc_runipd.py`:
    ```diff
    @@ -1711,7 +1711,10 @@ class StallWatchdogTests(unittest.TestCase):
                     textwrap.dedent(
                         """\
                         #!/usr/bin/env python3
    +                    import sys
                         import time
    +                    if sys.argv[1:2] != ["run"]:
    +                        sys.exit(1)
                         time.sleep(60)
                         """
                     ),
    ```
    Required-tests item 2a:
    ```
    2.74s call     tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_terminates_silent_child_and_marks_interrupted
    1 passed in 3.51s
    ```
    Durations comparison across 44 launcher files (702 passed in baseline vs 708 passed post-change): largest delta was `tests/test_code_pinning_prohibition.py::test_source_files_contain_no_prohibited_inspect_or_ast_patterns` (+9.21s, below 10s ceiling). Stall watchdog test ran in 2.22s / 2.74s call duration (baseline: 2.93s). No test slowed by >10s.
    Further test fixed under E-09:
    `tests/test_agent_user_config_containment.py` with `--scope-reason`: "Filter events.jsonl for agent-user-config-discarded to tolerate host-permission-posture events emitted on non-isolated turns".
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A REVIEWER SHOULD CHALLENGE HARDEST: F-3's claim that no driver child can ever legitimately use `question`. If any supported launch path gives the `opencode run` child an answerer (a TTY, an attached client, a server mode a human watches), that claim is false and the plan must narrow to unattended runs only. The authoring check covered `run_opencode`'s `popen_kwargs` (stdout piped, `start_new_session`) and the shared prompt's non-interactive instruction.

REVIEW ANSWER (2026-10-12): the challenge above was checked and F-3 holds (F-11, OQ-02).

ORDERING WITH SIBLING `15db4k` (same Set, Order 2, shares `lane_containment.py`, `oc_runipd.py` and the spec). `15db4k` is held by a blocking maintainer question and may never run. If it HAS executed before this plan, `PERMISSION_TIMEOUT` and its `RESIDUAL LIMITS:` paragraph will have MOVED onto `MAX_TURN_TIMEOUT`'s `#:` block, so E-04(b) edits the paragraph at its new home, and `CONTAINMENT_LAYERS_WITHOUT_HOST_DENIAL` will no longer say "(and PERMISSION_TIMEOUT when armed)". Re-read both at execution rather than trusting the quotes here. Neither order changes this plan's behavior.

SCOPE FENCE (a declaration, not a stop rule): the change is expected to touch only `- Scope-Paths:`. If an out-of-scope edit proves necessary (for example a further fake-host test under E-09), make it and justify it at finalize with `--scope-reason`; acknowledge any declared path left unmodified with `--scope-ack`.

Execution contract: commit ONLY the paths named in `- Scope-Paths:` (plus any justified out-of-scope path), through `aw commit <plan> -- <paths>`, never `git add -A` and never push. This is a SHARED CHECKOUT: verify the staged set with `git diff --cached --name-only` before committing, unstage anything that is not yours with `git restore --staged <path>`, and re-verify after any failed raw commit attempt. Run the suite BARE as `python3 -m pytest` and PASTE ITS ACTUAL SUMMARY LINE. Every `V-*` demands pasted, observed evidence; do not write evidence you did not observe.

LIFECYCLE TRANSITION. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns the terminal transition and finalize, so do NOT invoke `aw ipd finalize` yourself in a runner-driven execution. A HAND execution invokes it (`aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`). Never hand-edit `- Status:` and never hand-roll a `git mv` into `executed/`. Do NOT set backlog `8ctu3u` to `done`: the runner manages its state.
