# IPD: Record the lane's own head and status on an isolated attempt so a productive lane turn is distinguishable from a no-op

- Date: 2026-09-26
- Kind: child
- Concern: FOR AN ISOLATED (LANE) EXECUTE TURN, NO ATTEMPT FIELD RECORDS THE LANE'S OWN HEAD, AND ON EVERY SHAPE WHERE THE LANE IS NOT MERGED THE RECORD IS THEREFORE VACUOUS. `runner_shared.execute_item_core` writes `attempt["starting_head"] = git_head(repo)`, `attempt["ending_head"] = git_head(repo)` and `attempt["ending_status"] = git_status(repo)` where `repo = Path(state["repo"])` is the MAIN checkout, while an isolated turn (the default, `options.isolate_worktree` True) works in `work_dir`. A lane agent never moves main's HEAD and never dirties main's tree, so the lane's own facts are recorded NOWHERE. WHICH SHAPES THIS ACTUALLY BREAKS, MEASURED AT REVIEW (2026-09-26, HEAD `863220b8`) RATHER THAN ASSUMED, because the naive reading ("vacuous by construction on every isolated turn") is FALSE and reproducing it would waste the executor's first pass: (i) A VERIFIED, INTEGRATED turn -- the default SUCCESS shape -- ends up with a CORRECT `ending_head`, because the lane-integration success arm re-records `attempt["ending_head"] = git_head(repo)` AFTER `integrate_under_repository_lock` has merged the lane, by which point main's HEAD IS the lane tip. Measured: `starting_head cd0412a4`, `ending_head 11dac09e` (the lane tip), `collect_earned_paths` correctly returning `['.aw/records/plans/executed/...ipd.md', 'src/demo.txt']`. That path is SELF-CORRECTING and is not the defect. (ii) EVERY NON-INTEGRATED shape IS vacuous, and this is the real defect. Measured with a red integration gate: item `fail-merge`, `starting_head == ending_head == 77e21dca`, `ending_status == ''`, while the preserved lane branch tip `28e4e0a8` holds TWO commits beyond its base including `lifecycle(wir001): finalize wir001 -> executed`, and `collect_earned_paths` returns `[]`. A lane holding a finalized plan is recorded as a turn that moved nothing and earned nothing. That shape reaches the `if not integrated:` / `record_integration_refusal` arm, which writes NEITHER field (confirmed by AST walk of `execute_item_core`). Two consumers already work around the missing lane reading rather than rely on the attempt record: `runner_shared.process_backlog_close` adds `collect_lane_earned_paths` because the attempt range is empty on exactly shape (ii); and `runner_shared.turn_attempted_nothing`'s docstring says condition 2 is "TRUE BY CONSTRUCTION" on an isolated turn and reads the lane via `describe_lane` instead. That docstring shares the same over-broad claim corrected here: it is true that a lane agent never moves main's HEAD, but the field is later re-recorded post-merge on the success path, so the claim holds at the SAMPLE and not at the FIELD.
- Scope: IN: (a) when `work_dir` is set, ALSO record `lane_starting_head` (at worktree allocation), `lane_ending_head` and `lane_ending_status` (read with `git_head`/`git_status` against `Path(work_dir)`) at the post-turn site and at the three lane re-record sites reachable while the lane still exists -- INCLUDING the integration-REFUSAL arm, which is where the record is actually vacuous and which writes no head field today; `ending_head`/`ending_status`/`starting_head` are left EXACTLY as they are; (b) add the three keys to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (justified in OQ-02); (c) make `runner_shared.collect_earned_paths` prefer `lane_starting_head..lane_ending_head` when both are present; (d) update `turn_attempted_nothing`'s docstring condition 2 to name the new fields and to state the sample-versus-field distinction above; (e) behavioral tests driving a real isolated turn that commits in a lane on both hosts, covering BOTH the integrated and the refused shape, plus direct tests of `collect_earned_paths` and the prior-attempt projection. OUT: redefining `ending_head` (see OQ-01: `artifact_audit` depends on main-reachability); changing `turn_attempted_nothing`'s LOGIC (it already reads the lane correctly through `describe_lane`); removing the `collect_lane_earned_paths` workaround in `process_backlog_close` (it is keyed on the lane HANDLE, is correct, and stays as a belt for attempts recorded before this change); the agent-facing outcome JSON schema's `starting_head`/`ending_head` in `build_prompt` (agent-authored, a different record); review-sweep turns (`is_review`), which do not run the execute arms.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_attempt_lane_facts.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: jt0mny
- Blocks-Release: next
- Set: attemptfacts
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: s6ne9d

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 all FIXED, none deferred, no open question raised. Reviewed at HEAD `863220b8`; `aw ipd lint --phase author` conformed before revision. Drove real isolated turns on the OC host and MEASURED that the plan's "vacuous BY CONSTRUCTION" premise is FALSE for the integrated shape (the success arm re-records `ending_head` post-merge, so `starting_head != ending_head` and the earned set is correct) and TRUE for the non-integrated shapes, where a preserved lane holding a finalize commit records `start == end`, empty status and an empty earned set. Re-aimed the plan accordingly: Concern and Scope corrected with the measurements, E-01 now reproduces both shapes, E-03 adds the `if not integrated:` integration-refusal arm as the primary site (it writes no head field today and was omitted), E-07 no longer pins the false belief and gains a refused-shape case plus a success-arm-only control, and the dead `test_no_call_site_was_rewritten` census citation in E-05 was replaced with the real justification. F-2/F-3/F-4 corrected in place; F-9/F-10 added. OQ-01, OQ-02 and OQ-03 independently verified correct and left as resolved. Findings recorded in `.aw/records/reviews/20260926-attemptfacts-01-s6ne9d-record-the-lane-s-own-head-and-status-on-an-isolated-attempt.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog jt0mny. Design decision the backlog item left open (redefine the field vs add distinct lane fields) resolved from repository evidence as ADD (OQ-01: artifact_audit's UNKNOWN_HEAD_UNREACHABLE requires ending_head reachable from main). All sites and consumers re-measured at HEAD ea206c49.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an isolated attempt's record say what the LANE did, via three additive fields, so a reader (and `collect_earned_paths`) can tell a productive lane turn from a no-op, without changing the meaning of `ending_head`, which the artifact audit relies on.

PRECISELY WHAT IMPROVES, stated so the deliverable is not overclaimed (review PR-001/PR-006). On the SUCCESSFUL, integrated shape the existing record is ALREADY correct, because the success arm re-records `ending_head` after the merge; there the three new fields add a direct lane reading that no longer depends on that post-merge coincidence, which is a clarity and robustness gain rather than a bug fix. On every NON-INTEGRATED shape (`fail-merge`, integration-blocked, deferred, finalize-refused) the record is genuinely vacuous today and the new fields are the ONLY reading of what the lane did; that is the bug being fixed. Both are worth doing in one pass because they are the same three fields written at the same sites.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE BOTH ISOLATED SHAPES at the executing HEAD, and establish which one is vacuous. Using the `tests/test_oc_runipd.py::WorktreeIsolationTests` harness shape (`_init_repo_with_conforming_plan`, `_state_and_item`, `_fake_agent_commits_in_worktree` patched over `driver.run_opencode`, then `driver.execute_item(run_dir, state, item, recovery=False)`), drive TWO isolated execute turns whose fake agent COMMITS `src/demo.txt` in the lane, and for EACH paste `item["attempts"][0]` keys `starting_head`, `ending_head`, `ending_status`, `worktree_base`, `worktree_branch`, plus `item["status"]`, the lane branch tip (`git rev-parse aw/lane/<id6>`, or the integrated commit when the lane is gone), and `collect_earned_paths`'s result. (a) THE INTEGRATED SHAPE: the harness as-is. EXPECT `starting_head != ending_head`, with `ending_head` equal to the lane tip, because the success arm re-records after the merge; this shape is NOT the defect and the point is to confirm it is self-correcting so no later step tries to "fix" it. (b) THE REFUSED SHAPE, WHICH IS THE DEFECT: additionally patch `driver.make_integration_validation_runner` to `lambda *a, **k: (lambda _d, _f: False)` (the shape `tests/test_oc_runipd.py::WorktreeIsolationTests::test_non_passing_gate_defers_not_faked_executed` already uses) so the gate goes combined-red. EXPECT item `fail-merge`, `starting_head == ending_head`, `ending_status == ''`, `collect_earned_paths() == []`, while the preserved lane holds TWO commits beyond base including the `lifecycle(<id6>): finalize <id6> -> executed` commit. Also enumerate every `attempt["ending_head"]` / `attempt["ending_status"]` assignment in `execute_item_core` by AST (not grep, so a commented or quoted occurrence cannot inflate the count) and paste the list with line numbers; expected THREE assignment sites (integration-success arm, lane finalize-refusal arm, no-lane self-finalize arm) plus the post-turn `attempt.update({...})`, and confirm that the `if not integrated:` / `record_integration_refusal` arm that shape (b) traverses assigns NEITHER.
  - Depends on: none
  - Expected outcome: shape (a) reproduces a CORRECT `ending_head`; shape (b) reproduces the vacuous record with a lane holding real commits; the write-site inventory confirms the refusal arm records no head at all.
  - Execution state: pending

### Task group 2: record the lane facts

- [ ] E-02 RECORD `lane_starting_head` AT ALLOCATION. In `execute_item_core`'s execute-isolation arm (the `if isolate:` block that sets `attempt["worktree_base"] = wt_handle.base_commit` after `allocate_isolation_worktree`), set `attempt["lane_starting_head"] = git_head(Path(work_dir))`. Read it from the lane rather than copying `worktree_base`, because a REUSED lane (`worktree_disposition` other than `created`) may already hold commits beyond its base, and "where did THIS attempt start" is the lane's HEAD now, not its creation base. Do not add it to the review-sweep arm. Wrap the read so a failure records nothing rather than raising (the field is informational; an absent field means "unknown", and E-05's consumer falls back).
  - Depends on: E-01
  - Expected outcome: an isolated attempt carries `lane_starting_head` equal to the lane's HEAD at dispatch; a non-isolated attempt carries no such key.
  - Execution state: pending

- [ ] E-03 RECORD `lane_ending_head` / `lane_ending_status` AT THE POST-TURN SITE AND AT ALL THREE LANE ARMS, THE REFUSAL ARM FIRST. (0) In the post-turn `attempt.update({... "ending_head": git_head(repo), ...})`, when `work_dir` is set and the turn is not a review, add `lane_ending_head = git_head(Path(work_dir))` and `lane_ending_status = git_status(Path(work_dir))`. THEN refresh the two lane keys from `Path(work_dir)` at each arm below, BEFORE any teardown in that arm. THE REFRESH IS NOT OPTIONAL POLISH: the lane-side finalize adds a `lifecycle(<id6>): finalize <id6> -> executed` commit to the lane AFTER the post-turn sample (measured at review: exactly one such commit), so an arm left un-refreshed strands a `lane_ending_head` that is one commit short of the lane tip -- silently incomplete rather than wrong, which is the harder kind to notice. (1) THE INTEGRATION-REFUSAL ARM, `if not integrated:` (the branch reaching `record_integration_refusal`), inside the `self_finalize and work_dir and wt_handle is not None and integration.earned` branch. THIS IS THE PRIMARY SITE AND IT IS THE ONE THE ORIGINAL PLAN OMITTED (review PR-002): it writes NEITHER `ending_head` nor `ending_status` today, and it is the arm the measured vacuous `fail-merge` shape traverses, with the lane preserved and holding the work. Record both lane keys here; the lane still exists on this path by construction (it is preserved precisely so the work is not lost). (2) The lane integration SUCCESS `else:` arm, which already writes `attempt["ending_head"] = git_head(repo)`. (3) The lane finalize-REFUSAL `else:` arm, likewise. Guard each read so a lane already removed leaves the previously recorded value in place (catch `DriverError`/`OSError`, do not overwrite). The no-lane self-finalize arm (`elif self_finalize and not work_dir ...`) is NOT touched: there is no lane. Leave every existing `ending_head`/`ending_status`/`starting_head` write byte-unchanged. Add a comment at the post-turn site stating that `ending_head` is deliberately main's HEAD (OQ-01), that on the SUCCESS path it is re-recorded post-merge and therefore coincides with the lane tip, and that the `lane_*` keys are the lane's own reading on every path including the refused ones.
  - Depends on: E-02
  - Expected outcome: after an isolated turn that commits in the lane, `lane_ending_head` is the lane branch's tip INCLUDING the finalize commit, on the integrated shape AND on the refused shape; on the refused shape it is the only field naming the lane's work, and `ending_head` is unchanged in meaning everywhere.
  - Execution state: pending

- [ ] E-04 ALLOWLIST THE THREE KEYS for an isolated recovery prompt: append `lane_starting_head`, `lane_ending_head`, `lane_ending_status` to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`, with a comment giving OQ-02's justification (they describe the worker's OWN lane: two commit hashes it can `git show` from inside the lane, and a `git status --short` listing whose paths are lane-relative, so none carries a driver-side absolute path, which is the property the allowlist exists to enforce).
  - Depends on: E-03
  - Expected outcome: `prior_attempt_summary(prior, lane_root)` keeps the three keys for an isolated turn and still drops `prompt`, `log`, `worktree`.
  - Execution state: pending

### Task group 3: consumers

- [ ] E-05 MAKE `collect_earned_paths` PREFER THE LANE RANGE. In `runner_shared.collect_earned_paths`, per attempt: when both `lane_starting_head` and `lane_ending_head` are present and differ, diff that range; otherwise fall back to today's `starting_head..ending_head`. Keep the function best-effort and non-raising. KEEP IT AT ONE `run_checked` CALL PER ATTEMPT -- choose the range first, then make the single call -- but note the reason has been CORRECTED at review (PR-004): the justification is NOT a census test. `RELOCATED_RUN_CHECKED_CALLERS["collect_earned_paths"] == 1` still sits in `tests/test_runner_shared.py`, but its only reader, `test_no_call_site_was_rewritten`, was DELETED in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"); `grep -rn 'def test_no_call_site_was_rewritten' tests/` finds nothing and a whole-suite collect matches the name nowhere, so that table is inert data and protects nothing. The constraint stands on its own merit: this runs per attempt on a path an operator waits on, and a second `git diff` per attempt is user-perceptible waste this repository classifies as a defect. Do NOT add a second call in order to keep the two ranges "symmetrical". Update its docstring to say the lane range is preferred and why. Do NOT remove the `collect_lane_earned_paths` addition in `process_backlog_close`; update the comment there ("THE EARNED SET, AND THE TRAP IN IT") to say the attempt range now covers a lane attempt recorded after this change, that the trap it describes was real and is measured on the NON-INTEGRATED shapes specifically, and that the handle-based range remains for older records.
  - Depends on: E-03
  - Expected outcome: for an isolated attempt with lane fields, `collect_earned_paths` returns the lane's changed paths without the handle -- including on the refused shape, where it returns `[]` today; for an attempt without them the result is byte-identical to today; exactly one `run_checked` call site remains in the body.
  - Execution state: pending

- [ ] E-06 UPDATE THE ZERO-WORK DOCSTRING. In `runner_shared.turn_attempted_nothing`, rewrite condition 2's text: it stays "load-bearing ONLY for a SHARED-TREE turn" (the logic is unchanged), but state that `starting_head`/`ending_head` are main's HEAD by design and that an isolated attempt's own head facts now live in `lane_starting_head`/`lane_ending_head`/`lane_ending_status`, while the predicate continues to read the lane through `describe_lane` (condition 3/4) because that reading is also available on attempts recorded before this change. ALSO CORRECT THE OVER-BROAD CLAIM IN THE EXISTING TEXT (review PR-001): the sentence "so on an isolated turn a lane agent never moves the main checkout's HEAD and this is TRUE BY CONSTRUCTION" is true of the SAMPLE but not of the FIELD, because the integration-success arm re-records `ending_head` AFTER the merge, at which point it equals the lane tip and `starting_head != ending_head` on a productive integrated turn (measured at review). State that the equality holds by construction only on the shapes where the lane is NOT merged, which is also where the lane fields are the only true reading. This correction matters for the predicate's honesty even though its logic is unchanged: a reader who trusts the unqualified claim would wrongly conclude condition 2 can never refuse on an isolated turn. No executable change.
  - Depends on: E-03
  - Expected outcome: the docstring names the new fields; `git diff` of the function shows docstring lines only.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_attempt_lane_facts.py` (behavioral only; no source-text or AST assertions). Cases: (1) OC host, INTEGRATED isolated turn whose fake agent commits `src/demo.txt` in the lane (reuse `tests.test_oc_runipd._init_repo_with_conforming_plan` and the `WorktreeIsolationTests` fake-turn shape, patched over `oc_runipd.run_opencode`, with `support.declare_execution_role(self)` in `setUp`): assert `lane_starting_head` equals the lane base, `lane_ending_head != lane_starting_head`, `git diff --name-only lane_starting_head..lane_ending_head` includes `src/demo.txt`, and `starting_head` equals main's HEAD BEFORE the turn. DO NOT assert that `ending_head` is unchanged on this shape (review PR-003): it is re-recorded post-merge and therefore EQUALS the lane tip, so assert exactly that (`ending_head == lane_ending_head` here) and comment that the two coincide on this path only because integration succeeded, which is what case (2) separates. (2) THE REFUSED SHAPE, OC host, which is the defect's home: same turn plus `make_integration_validation_runner` patched to `lambda *a, **k: (lambda _d, _f: False)`, and assert item `fail-merge`, `starting_head == ending_head` (main never moved, unchanged behavior), `ending_status == ''`, AND `lane_ending_head != lane_starting_head` with the lane range including BOTH `src/demo.txt` and the `lifecycle(<id6>)` finalize commit -- so the lane fields carry the reading the main fields cannot. This is the case that fails hardest against pre-change code, where no lane key exists at all. (3) the integrated shape on the AGY host (reuse `tests.test_agy_runipd_cli._init_repo_with_conforming_plan` and patch `agy_runipd.run_agy_turn`); (4) a NON-isolated turn (`isolate_worktree: False`) carries none of the three keys; (5) `collect_earned_paths` on a synthetic item whose attempt has `starting_head == ending_head` but a real lane range returns the lane paths, and on an attempt without lane keys returns exactly today's result; (6) `lane_containment.prior_attempt_summary` with a lane root keeps the three keys and drops `worktree`/`log`/`prompt`, AND `lane_containment.absolute_paths_outside_lane` finds no out-of-lane path in a rendered recovery prompt carrying a realistic `lane_ending_status` (the property check that backs OQ-02's claim rather than restating it); (7) a lane whose worktree path no longer exists at a re-record site leaves the post-turn value in place (drive the guard by calling the site's helper if E-03 factors one out, otherwise by removing the worktree inside a patched `integrate_lane_branch` stub before the re-record).
  - Depends on: E-04, E-05, E-06
  - Expected outcome: all cases pass; (1), (2), (3), (5)-lane-branch and (6) fail against the pre-change code, and (2) additionally fails against a change that instruments only the integration-SUCCESS arm.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `execute_item_core` is the ONE execution loop for both hosts (`oc_runipd.execute_item` and `agy_runipd.execute_item` both call `runner_shared.execute_item_core`), so recording the fields once covers both; `git_head`/`git_status` are bound from `driver_module` inside it (the injected-`run_checked` wrappers), and must be used rather than the shared unwrapped symbols.
- `turn_ran_in_a_lane(attempt)` keys isolation on `attempt["worktree"]`/`worktree_lane_id`; the new keys are written only under the same condition (`work_dir` set).
- Isolated-turn prompt hygiene: `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` is an ALLOWLIST whose stated invariant is "none of them can carry a filesystem path"; `starting_head`/`ending_head`/`worktree_base` are already on it.
- `tests/test_runner_shared.py` still DEFINES `RELOCATED_RUN_CHECKED_CALLERS`, but the census test that read it (`test_no_call_site_was_rewritten`) was DELETED in `19313eed`, so the table is INERT and enforces nothing (corrected at review, PR-004). E-05 keeps `collect_earned_paths` at one `run_checked` call for its own merit (one git invocation per attempt on a path an operator waits on), not to satisfy a census. The suite itself is real and green (92 tests) and is still worth running as a regression check.
- Test policy (maintainer ruling 2026-09-26): behavior tests only, no `inspect.getsource`/AST pins. Suites run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `ea206c49` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.execute_item_core`, attempt creation | `starting_head` is `git_head(repo)` (main) for every turn, isolated or not. | `"starting_head": git_head(repo),` in the `attempt: dict[str, Any] = {` literal; `repo = Path(state["repo"])` |
| F-2 | HIGH (CORRECTED at review) | `execute_item_core`, post-turn `attempt.update` | `ending_head`/`ending_status` read main even when `work_dir` is set. CORRECTION: this is true of the SAMPLE but does not by itself leave the FIELD wrong. On the integration-SUCCESS path the field is re-recorded after the merge (F-10) and ends up correct; the sample is only load-bearing on the non-integrated shapes (F-9). Retained rather than deleted so the original premise stays visible. | `"ending_head": git_head(repo),` / `"ending_status": git_status(repo),`; corrected by measurement, see F-9/F-10 |
| F-3 | MEDIUM (CORRECTED at review) | `execute_item_core`, three re-record sites | `attempt["ending_head"] = git_head(repo)` / `attempt["ending_status"] = git_status(repo)` in the lane integration-success `else:` arm, the lane finalize-refusal `else:` arm, and the no-lane self-finalize arm. CORRECTION: three ASSIGNMENT sites is right, but the enumeration is incomplete as a list of arms an isolated turn can END in -- it omits the `if not integrated:` arm, which assigns neither and is where the vacuous record actually occurs (F-9). | AST walk of `execute_item_core` -> assignments at the three named arms only; the `if not integrated:` arm assigns neither |
| F-4 | MEDIUM (CORRECTED at review) | `runner_shared.collect_earned_paths` | Diffs `starting_head..ending_head`, which is `X..X` for a lane attempt; `process_backlog_close` compensates with `collect_lane_earned_paths` (comment "THE EARNED SET, AND THE TRAP IN IT"). CORRECTION: `X..X` holds on the NON-INTEGRATED shapes (measured `[]`), not on the integrated one, where the range spans the lane's work correctly (measured: both the executed plan path and `src/demo.txt`). The compensation is therefore load-bearing for a narrower but real population. | the `if not start or not end or start == end: continue` guard; measured both shapes at review |
| F-5 | INFO | `runner_shared.turn_attempted_nothing` docstring | Condition 2 documented "TRUE BY CONSTRUCTION" on isolated turns; logic reads `describe_lane` instead. | docstring text "so on an isolated turn a lane agent never moves the main checkout's HEAD and this is TRUE BY CONSTRUCTION" |
| F-6 | HIGH (design constraint) | `artifact_audit.FinalizeEvidence.finalize_after` | Requires `ending_head` reachable from main HEAD; an unmerged lane head is not, so redefining the field would turn audit rows into `UNKNOWN_HEAD_UNREACHABLE`. | `if ending_head not in self.head_reachable:` and `UNKNOWN_HEAD_UNREACHABLE = "the run record's ending_head is not in this repository's history, ..."`; `run_viewer` passes `att["ending_head"]` as the time bound |
| F-7 | INFO | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` | Allowlist already includes `starting_head`, `ending_head`, `worktree_base`, `worktree_branch`; excludes `ending_status`. | tuple literal |
| F-8 | INFO | spec `25kzda` | Does NOT enumerate the attempt record shape: the only `starting_status` hit is the Section 5.6 final-report JSON's `item.starting_status`, and "ending HEAD" appears once in 4.6 prose about run-owned commits. No attempt-field list exists to amend. | `grep -n "ending_head\|ending_status\|starting_head" <25kzda>` -> no hits |
| F-9 | HIGH (ADDED at review) | `execute_item_core`, the `if not integrated:` arm reaching `record_integration_refusal` | **THE ARM WHERE THE RECORD IS ACTUALLY VACUOUS, AND IT WRITES NO HEAD FIELD AT ALL.** With a combined-red integration gate: item `fail-merge`, `starting_head == ending_head == 77e21dca`, `ending_status == ''`, `collect_earned_paths() == []`, while the PRESERVED lane tip `28e4e0a8` holds two commits beyond base including `lifecycle(wir001): finalize wir001 -> executed`. A finalized plan on a preserved lane, recorded as a turn that did nothing. This arm is not in the plan's original site list, which is why E-03 now names it first. | measured at review by patching `make_integration_validation_runner` to return a false-returning runner, the shape `test_non_passing_gate_defers_not_faked_executed` uses; AST walk confirms the arm assigns neither field |
| F-10 | MEDIUM (ADDED at review) | `execute_item_core`, the lane integration-SUCCESS `else:` arm | **THE SUCCESS PATH IS SELF-CORRECTING, WHICH IS WHY THE "VACUOUS BY CONSTRUCTION" PREMISE IS FALSE.** The arm re-records `attempt["ending_head"] = git_head(repo)` AFTER `integrate_under_repository_lock` merged the lane, so main's HEAD already IS the lane tip. Measured: `starting_head cd0412a4` -> `ending_head 11dac09e` (the lane tip), `collect_earned_paths` returning both the executed plan path and `src/demo.txt`. Recorded so no step "fixes" a path that is already right, and so E-07 does not pin the false belief. | captured timeline across `integrate_lane_branch`: main HEAD `96c09f6e` before and during the turn, `c4c5ee0c` after integration, with `attempt["ending_head"]` moving with it |

## Proposed changes (ordered, validatable)

1. E-01 reproduces BOTH isolated shapes, establishes which one is vacuous, and confirms the write sites by AST.
2. E-02 records `lane_starting_head` at allocation.
3. E-03 records `lane_ending_head`/`lane_ending_status` post-turn and at all three lane arms, the integration-refusal arm first.
4. E-04 allowlists the three keys.
5. E-05 makes `collect_earned_paths` prefer the lane range.
6. E-06 corrects the zero-work docstring.
7. E-07 adds behavioral tests on both hosts.

## Deferred / out of scope (with reason)

- Redefining `ending_head` to the lane head.
  - Carrier-Declined: breaks `artifact_audit`'s main-reachability bound (F-6); ADD is strictly safer and was the backlog item's second option.
- Removing `collect_lane_earned_paths` from `process_backlog_close`.
  - Carrier-Declined: it keys on the lane handle and still covers attempts recorded before this change; removing it would regress resumed old runs for no gain.
- Surfacing the lane facts in `aw runs` / `run_viewer`.
  - Carrier-Declined: no consumer asked for it; the record is the deliverable, a view can follow if needed.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` are NOT declared: both call the shared `execute_item_core` (verified at review by reading both `execute_item` bodies), so no host edit is expected. `tests/test_runner_shared.py` is NOT declared and E-05 adds no `run_checked` call site, so nothing in it should move; note the census it was cited for is inert (see E-05), so the real risk there is a behavioral regression rather than a count change. `tests/test_finalize_sendback.py` is NOT declared either, and it is the file E-04 is most likely to disturb (it asserts `_PRIOR_ATTEMPT_SAFE_KEYS` membership and inspects a rendered recovery prompt); an ALLOWLIST ADDITION should not break either assertion, but if it does, that is a signal to re-examine E-04 rather than to edit the test, so justify at finalize.
- Adjacent plans: `184tn9` (approved, pending) also edits `runner_shared.py` (lane reclaim prompt and deferred integration shells), and `zrvtm2` (executed at `ea206c49`) edited the interrupt path. File overlap only; no ordering dependency, and the runner isolates each item in its own lane.
- Scope-Paths justification: `runner_shared.py` holds the recording sites and both consumers; `lane_containment.py` holds the allowlist; the new test file holds E-07.

## Required tests / validation

- `tests/test_attempt_lane_facts.py` (new): the INTEGRATED and the REFUSED isolated shape on OC, the integrated shape on AGY, the non-isolated negative, `collect_earned_paths` lane preference and fallback, the allowlist projection plus the `absolute_paths_outside_lane` property check, and the removed-lane guard. Shown failing before the change, and the refused-shape case additionally shown failing against a success-arm-only change.
- Bare `python3 -m pytest` before and after; compare failing node IDs.
- `python3 -m pytest -o addopts="" tests/test_runner_shared.py` and `tests/test_finalize_sendback.py` (the latter asserts on `_PRIOR_ATTEMPT_SAFE_KEYS` membership and on the rendered recovery prompt, so E-04 is the change most likely to move it).

## Spec / documentation sync

- N/A for specs: spec `25kzda` does not enumerate the per-attempt record fields (F-8), so there is nothing to amend; no `.spec.md` is in `- Scope-Paths:`.
- No user-facing docs: the attempt record is an internal run-state shape.

## Open questions

### OQ-01: Redefine `ending_head` for an isolated turn, or add distinct lane fields?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: ADD, from repository evidence. `artifact_audit.FinalizeEvidence.finalize_after` forms the range `<ending_head>..HEAD` and returns `UNKNOWN_HEAD_UNREACHABLE` when `ending_head` is not in main's history; `run_viewer` feeds it each attempt's `ending_head`. An unmerged (or refused, or torn-down) lane head is not reachable from main, so redefining the field would silently degrade every isolated row of the audit. Adding `lane_*` keys changes no existing reader.

### OQ-02: Are the three new keys safe to show a worker in an isolated recovery prompt?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES. `_PRIOR_ATTEMPT_SAFE_KEYS`' invariant is "none of them can carry a filesystem path". Two keys are commit hashes of the worker's own lane (the list already admits `starting_head`, `ending_head`, `worktree_base`), and `lane_ending_status` is `git status --short` run INSIDE the lane, whose paths are lane-relative. They are also the facts a resuming worker most needs (what it had committed and left uncommitted). `ending_status` (main's) stays excluded, unchanged.

### OQ-03: Does spec `25kzda` enumerate the attempt record so it must be amended?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO (F-8). Its only attempt-adjacent JSON is the Section 5.6 final-report item shape (`starting_status` is the artifact's lifecycle status, not a git status), and "ending HEAD" appears only in Section 4.6 prose. Nothing to declare.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste, FOR BOTH SHAPES SEPARATELY and labelled, the attempt's `starting_head`, `ending_head`, `ending_status`, `worktree_base`, `worktree_branch`, `item["status"]`, the lane branch tip (`git rev-parse aw/lane/<id6>` or the integrated commit), and `collect_earned_paths`'s result. The INTEGRATED shape must show `starting_head != ending_head` with `ending_head` equal to the lane tip and a NON-empty earned set; the REFUSED shape must show `starting_head == ending_head`, empty `ending_status`, an empty earned set, and a lane holding two commits beyond base including the finalize commit (paste `git log --format='%s' <base>..<tip>`). Also paste the AST write-site inventory with line numbers and the explicit confirmation that the `if not integrated:` arm assigns neither field. A reproduction that pastes only one shape does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the allocation arm, and from a reproduction run the attempt's `lane_starting_head` next to `git rev-parse` of the lane at dispatch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the post-turn site and ALL THREE lane arms, INCLUDING the `if not integrated:` integration-refusal arm, showing every pre-existing `ending_head`/`ending_status` line unchanged. Paste a REFUSED-shape attempt record showing `starting_head == ending_head` (main untouched) alongside `lane_ending_head != lane_starting_head`, and show the recorded lane range CONTAINS the `lifecycle(<id6>)` finalize commit (`git log --format='%s' lane_starting_head..lane_ending_head`), which is what proves the refresh happened after the lane-side finalize rather than at the post-turn sample. Paste an INTEGRATED-shape record too, showing `ending_head` unchanged in meaning. A diff that does not touch the refusal arm does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the allowlist diff and the output of `prior_attempt_summary` for a sample attempt with a lane root, showing the three keys kept and `worktree`/`log`/`prompt` dropped.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `collect_earned_paths` diff and state the number of `run_checked` call sites in the body (must be one). Paste `python3 -m pytest -o addopts="" tests/test_runner_shared.py -q` passing with its count (a regression check on a real suite; NOT a census check, see E-05). Paste the earned set for a REFUSED-shape attempt before and after the change (expected `[]` before, the lane's paths after), which is the consumer-visible proof the fix reaches the defect.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff` of `turn_attempted_nothing` showing docstring-only lines, and confirm the corrected condition-2 text no longer states the unqualified "TRUE BY CONSTRUCTION" claim for every isolated turn.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_attempt_lane_facts.py -q` passing with the count; then with the E-02..E-05 hunks temporarily reverted, the same command showing cases (1), (2), (3), (5)-lane and (6) FAILING; then passing again after restoring. ADDITIONALLY, to prove case (2) is not decoration, temporarily restore ONLY the integration-SUCCESS arm's refresh (leaving the refusal arm un-instrumented) and paste case (2) still FAILING; that is the control which distinguishes this change from one that instruments the already-correct path. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER the change and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Three additive, lane-sourced fields on an isolated attempt record (`lane_starting_head`, `lane_ending_head`, `lane_ending_status`), written at the post-turn sample and refreshed at all three lane arms INCLUDING the integration-refusal arm; their inclusion in the isolated recovery-prompt allowlist; `collect_earned_paths` preferring the lane range; and two docstring corrections. `ending_head`, `ending_status`, and `starting_head` keep their exact current meaning (main's), because the artifact audit depends on it. This graduates backlog `jt0mny` and inherits its `- Blocks-Release: next`.

WHAT THE REVIEW CHANGED, because it alters what is being claimed. The plan as authored asserted that an isolated attempt's record is vacuous BY CONSTRUCTION on every isolated turn. That was measured FALSE for the default successful shape, where the integration-success arm re-records `ending_head` after the merge and the record ends up correct. The defect is real on every NON-INTEGRATED shape (`fail-merge` and its siblings), where a preserved lane holding a finalized plan is recorded as a turn that moved nothing and earned nothing -- and that shape traverses an arm the original plan did not list. So the SOLUTION is unchanged and the DIAGNOSIS is narrowed and re-aimed: one more site, a two-shape reproduction, and tests that cannot pass by instrumenting only the already-correct path. A human approving this is approving a fix whose benefit is concentrated on refused and deferred turns, plus a robustness gain on successful ones.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (`execute_item_core`, `collect_earned_paths`, `turn_attempted_nothing`'s docstring, and the `process_backlog_close` comment), `agent_workflows/lane_containment.py` (`_PRIOR_ATTEMPT_SAFE_KEYS`), and the new `tests/test_attempt_lane_facts.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `jt0mny` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
