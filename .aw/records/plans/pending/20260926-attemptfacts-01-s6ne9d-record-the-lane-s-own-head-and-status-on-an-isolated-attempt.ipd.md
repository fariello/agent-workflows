# IPD: Record the lane's own head and status on an isolated attempt so a productive lane turn is distinguishable from a no-op

- Date: 2026-09-26
- Kind: child
- Concern: FOR AN ISOLATED (LANE) EXECUTE TURN, EVERY HEAD/STATUS FACT ON THE ATTEMPT RECORD DESCRIBES A TREE THE TURN NEVER TOUCHED. `runner_shared.execute_item_core` writes `attempt["starting_head"] = git_head(repo)`, `attempt["ending_head"] = git_head(repo)` and `attempt["ending_status"] = git_status(repo)` where `repo = Path(state["repo"])` is the MAIN checkout, while an isolated turn (the default, `options.isolate_worktree` True) works in `work_dir`. It does so at the post-turn `attempt.update({...})` and at three post-finalize re-record sites (the lane integration success `else:` arm, the lane finalize-refusal `else:` arm, and the no-lane self-finalize arm). A lane agent never moves main's HEAD and never dirties main's tree, so for the default execution shape `starting_head == ending_head` and `ending_status == ""` BY CONSTRUCTION, even for a lane that committed substantial work: a productive lane turn is indistinguishable from a no-op in the record. Two consumers already work around it rather than rely on it: `runner_shared.process_backlog_close` adds `collect_lane_earned_paths` because `collect_earned_paths`'s `starting_head..ending_head` range is `X..X` and empty for a lane; and `runner_shared.turn_attempted_nothing`'s docstring says condition 2 is "TRUE BY CONSTRUCTION" on an isolated turn and reads the lane via `describe_lane` instead.
- Scope: IN: (a) when `work_dir` is set, ALSO record `lane_starting_head` (at worktree allocation), `lane_ending_head` and `lane_ending_status` (read with `git_head`/`git_status` against `Path(work_dir)`) at the post-turn site and at the two lane re-record sites that write `ending_head` while the lane still exists; `ending_head`/`ending_status`/`starting_head` are left EXACTLY as they are; (b) add the three keys to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` (justified in OQ-02); (c) make `runner_shared.collect_earned_paths` prefer `lane_starting_head..lane_ending_head` when both are present; (d) update `turn_attempted_nothing`'s docstring condition 2 to name the new fields; (e) behavioral tests driving a real isolated turn that commits in a lane on both hosts, plus direct tests of `collect_earned_paths` and the prior-attempt projection. OUT: redefining `ending_head` (see OQ-01: `artifact_audit` depends on main-reachability); changing `turn_attempted_nothing`'s LOGIC (it already reads the lane correctly through `describe_lane`); removing the `collect_lane_earned_paths` workaround in `process_backlog_close` (it is keyed on the lane HANDLE, is correct, and stays as a belt for attempts recorded before this change); the agent-facing outcome JSON schema's `starting_head`/`ending_head` in `build_prompt` (agent-authored, a different record); review-sweep turns (`is_review`), which do not run the execute arms.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_attempt_lane_facts.py
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog jt0mny. Design decision the backlog item left open (redefine the field vs add distinct lane fields) resolved from repository evidence as ADD (OQ-01: artifact_audit's UNKNOWN_HEAD_UNREACHABLE requires ending_head reachable from main). All sites and consumers re-measured at HEAD ea206c49.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make an isolated attempt's record say what the LANE did, via three additive fields, so a reader (and `collect_earned_paths`) can tell a productive lane turn from a no-op, without changing the meaning of `ending_head`, which the artifact audit relies on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE THE VACUOUS RECORD at the executing HEAD. Using the `tests/test_oc_runipd.py::WorktreeIsolationTests` harness shape (`_init_repo_with_conforming_plan`, `_state_and_item`, `_fake_agent_commits_in_worktree` patched over `driver.run_opencode`, then `driver.execute_item(run_dir, state, item, recovery=False)`), run one isolated execute turn whose fake agent COMMITS `src/demo.txt` in the lane, and paste the resulting `item["attempts"][0]` keys `starting_head`, `ending_head`, `ending_status`, `worktree_base`, `worktree_branch`. Also re-grep `runner_shared.execute_item_core` for every `ending_head` write and paste the list (expected: the post-turn `attempt.update`, the lane integration success arm, the lane finalize-refusal arm, the no-lane self-finalize arm). If `ending_head != starting_head` for the lane turn (main moved because integration ran), record which site wrote it; the point to prove is that NO attempt key names the lane's own post-turn head.
  - Depends on: none
  - Expected outcome: no attempt key records the lane branch's post-turn commit; the four `ending_head` write sites are confirmed.
  - Execution state: pending

### Task group 2: record the lane facts

- [ ] E-02 RECORD `lane_starting_head` AT ALLOCATION. In `execute_item_core`'s execute-isolation arm (the `if isolate:` block that sets `attempt["worktree_base"] = wt_handle.base_commit` after `allocate_isolation_worktree`), set `attempt["lane_starting_head"] = git_head(Path(work_dir))`. Read it from the lane rather than copying `worktree_base`, because a REUSED lane (`worktree_disposition` other than `created`) may already hold commits beyond its base, and "where did THIS attempt start" is the lane's HEAD now, not its creation base. Do not add it to the review-sweep arm. Wrap the read so a failure records nothing rather than raising (the field is informational; an absent field means "unknown", and E-05's consumer falls back).
  - Depends on: E-01
  - Expected outcome: an isolated attempt carries `lane_starting_head` equal to the lane's HEAD at dispatch; a non-isolated attempt carries no such key.
  - Execution state: pending

- [ ] E-03 RECORD `lane_ending_head` / `lane_ending_status` AT THE POST-TURN SITE AND THE TWO LANE RE-RECORD SITES. (1) In the post-turn `attempt.update({... "ending_head": git_head(repo), ...})`, when `work_dir` is set and the turn is not a review, add `lane_ending_head = git_head(Path(work_dir))` and `lane_ending_status = git_status(Path(work_dir))`. (2) In the lane integration SUCCESS `else:` arm and (3) the lane finalize-REFUSAL `else:` arm (both inside the `self_finalize and work_dir and wt_handle is not None and integration.earned` branch, each currently writing `attempt["ending_head"] = git_head(repo)`), refresh the two lane keys from `Path(work_dir)` BEFORE any teardown in that arm, since the lane-side finalize adds a lifecycle commit to the lane after the post-turn sample. Guard each read so a lane already removed leaves the previously recorded value in place (catch `DriverError`/`OSError`, do not overwrite). The no-lane self-finalize arm (`elif self_finalize and not work_dir ...`) is NOT touched: there is no lane. Leave every existing `ending_head`/`ending_status`/`starting_head` write byte-unchanged. Add a comment at the post-turn site stating that `ending_head` is deliberately main's HEAD (OQ-01) and the `lane_*` keys are the lane's.
  - Depends on: E-02
  - Expected outcome: after an isolated turn that commits in the lane, `lane_ending_head` is the lane branch's tip (including the finalize commit when finalize ran) and differs from `lane_starting_head`; `ending_head` is unchanged in meaning.
  - Execution state: pending

- [ ] E-04 ALLOWLIST THE THREE KEYS for an isolated recovery prompt: append `lane_starting_head`, `lane_ending_head`, `lane_ending_status` to `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS`, with a comment giving OQ-02's justification (they describe the worker's OWN lane: two commit hashes it can `git show` from inside the lane, and a `git status --short` listing whose paths are lane-relative, so none carries a driver-side absolute path, which is the property the allowlist exists to enforce).
  - Depends on: E-03
  - Expected outcome: `prior_attempt_summary(prior, lane_root)` keeps the three keys for an isolated turn and still drops `prompt`, `log`, `worktree`.
  - Execution state: pending

### Task group 3: consumers

- [ ] E-05 MAKE `collect_earned_paths` PREFER THE LANE RANGE. In `runner_shared.collect_earned_paths`, per attempt: when both `lane_starting_head` and `lane_ending_head` are present and differ, diff that range; otherwise fall back to today's `starting_head..ending_head`. Keep the function best-effort and non-raising, keep ONE `run_checked` call per attempt (the census `RELOCATED_RUN_CHECKED_CALLERS["collect_earned_paths"] == 1` in `tests/test_runner_shared.py` counts call SITES; choose the range first, then make the single call, so the count is unchanged). Update its docstring to say the lane range is preferred and why. Do NOT remove the `collect_lane_earned_paths` addition in `process_backlog_close`; update the comment there ("THE EARNED SET, AND THE TRAP IN IT") to say the attempt range now covers a lane attempt recorded after this change and the handle-based range remains for older records.
  - Depends on: E-03
  - Expected outcome: for an isolated attempt with lane fields, `collect_earned_paths` returns the lane's changed paths without the handle; for an attempt without them the result is byte-identical to today.
  - Execution state: pending

- [ ] E-06 UPDATE THE ZERO-WORK DOCSTRING. In `runner_shared.turn_attempted_nothing`, rewrite condition 2's text: it stays "load-bearing ONLY for a SHARED-TREE turn" (the logic is unchanged), but state that `starting_head`/`ending_head` are main's HEAD by design and that an isolated attempt's own head facts now live in `lane_starting_head`/`lane_ending_head`/`lane_ending_status`, while the predicate continues to read the lane through `describe_lane` (condition 3/4) because that reading is also available on attempts recorded before this change. No executable change.
  - Depends on: E-03
  - Expected outcome: the docstring names the new fields; `git diff` of the function shows docstring lines only.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_attempt_lane_facts.py` (behavioral only; no source-text or AST assertions). Cases: (1) OC host, isolated turn whose fake agent commits `src/demo.txt` in the lane (reuse `tests.test_oc_runipd._init_repo_with_conforming_plan` and the `WorktreeIsolationTests` fake-turn shape, patched over `oc_runipd.run_opencode`, with `support.declare_execution_role(self)` in `setUp`): assert `lane_starting_head` equals the lane base, `lane_ending_head != lane_starting_head`, `git diff --name-only lane_starting_head..lane_ending_head` includes `src/demo.txt`, and `ending_head`/`starting_head` are still main-checkout values (`starting_head` equals main's HEAD before the turn); (2) the same on the AGY host (reuse `tests.test_agy_runipd_cli._init_repo_with_conforming_plan` and patch `agy_runipd.run_agy_turn`); (3) a NON-isolated turn (`isolate_worktree: False`) carries none of the three keys; (4) `collect_earned_paths` on a synthetic item whose attempt has `starting_head == ending_head` but a real lane range returns the lane paths, and on an attempt without lane keys returns exactly today's result; (5) `lane_containment.prior_attempt_summary` with a lane root keeps the three keys and drops `worktree`/`log`/`prompt`; (6) a lane whose worktree path no longer exists at a re-record site leaves the post-turn value in place (drive the guard by calling the site's helper if E-03 factors one out, otherwise by removing the worktree inside a patched `integrate_lane_branch` stub before the re-record).
  - Depends on: E-04, E-05, E-06
  - Expected outcome: all cases pass; (1), (2), (4)-lane-branch and (5) fail against the pre-change code.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `execute_item_core` is the ONE execution loop for both hosts (`oc_runipd.execute_item` and `agy_runipd.execute_item` both call `runner_shared.execute_item_core`), so recording the fields once covers both; `git_head`/`git_status` are bound from `driver_module` inside it (the injected-`run_checked` wrappers), and must be used rather than the shared unwrapped symbols.
- `turn_ran_in_a_lane(attempt)` keys isolation on `attempt["worktree"]`/`worktree_lane_id`; the new keys are written only under the same condition (`work_dir` set).
- Isolated-turn prompt hygiene: `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` is an ALLOWLIST whose stated invariant is "none of them can carry a filesystem path"; `starting_head`/`ending_head`/`worktree_base` are already on it.
- The shared-module harness `tests/test_runner_shared.py` counts `run_checked` call sites per shared function (`RELOCATED_RUN_CHECKED_CALLERS`); E-05 keeps `collect_earned_paths` at one.
- Test policy (maintainer ruling 2026-09-26): behavior tests only, no `inspect.getsource`/AST pins. Suites run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `ea206c49` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.execute_item_core`, attempt creation | `starting_head` is `git_head(repo)` (main) for every turn, isolated or not. | `"starting_head": git_head(repo),` in the `attempt: dict[str, Any] = {` literal; `repo = Path(state["repo"])` |
| F-2 | HIGH | `execute_item_core`, post-turn `attempt.update` | `ending_head`/`ending_status` read main even when `work_dir` is set. | `"ending_head": git_head(repo),` / `"ending_status": git_status(repo),` |
| F-3 | MEDIUM | `execute_item_core`, three re-record sites | `attempt["ending_head"] = git_head(repo)` / `attempt["ending_status"] = git_status(repo)` in the lane integration-success `else:` arm, the lane finalize-refusal `else:` arm, and the no-lane self-finalize arm. | `grep -n 'attempt\["ending_head"\]' agent_workflows/runner_shared.py` -> 3 hits |
| F-4 | MEDIUM | `runner_shared.collect_earned_paths` | Diffs `starting_head..ending_head`, which is `X..X` for a lane attempt; `process_backlog_close` compensates with `collect_lane_earned_paths` (comment "THE EARNED SET, AND THE TRAP IN IT"). | the `if not start or not end or start == end: continue` guard |
| F-5 | INFO | `runner_shared.turn_attempted_nothing` docstring | Condition 2 documented "TRUE BY CONSTRUCTION" on isolated turns; logic reads `describe_lane` instead. | docstring text "so on an isolated turn a lane agent never moves the main checkout's HEAD and this is TRUE BY CONSTRUCTION" |
| F-6 | HIGH (design constraint) | `artifact_audit.FinalizeEvidence.finalize_after` | Requires `ending_head` reachable from main HEAD; an unmerged lane head is not, so redefining the field would turn audit rows into `UNKNOWN_HEAD_UNREACHABLE`. | `if ending_head not in self.head_reachable:` and `UNKNOWN_HEAD_UNREACHABLE = "the run record's ending_head is not in this repository's history, ..."`; `run_viewer` passes `att["ending_head"]` as the time bound |
| F-7 | INFO | `lane_containment._PRIOR_ATTEMPT_SAFE_KEYS` | Allowlist already includes `starting_head`, `ending_head`, `worktree_base`, `worktree_branch`; excludes `ending_status`. | tuple literal |
| F-8 | INFO | spec `25kzda` | Does NOT enumerate the attempt record shape: the only `starting_status` hit is the Section 5.6 final-report JSON's `item.starting_status`, and "ending HEAD" appears once in 4.6 prose about run-owned commits. No attempt-field list exists to amend. | `grep -n "ending_head\|ending_status\|starting_head" <25kzda>` -> no hits |

## Proposed changes (ordered, validatable)

1. E-01 reproduces the vacuous record and confirms the write sites.
2. E-02 records `lane_starting_head` at allocation.
3. E-03 records `lane_ending_head`/`lane_ending_status` post-turn and at the two lane re-record sites.
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
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` are NOT declared: both call the shared `execute_item_core`, so no host edit is expected. `tests/test_runner_shared.py` is NOT declared because E-05 keeps its census count unchanged; if the census still moves, justify at finalize.
- Adjacent plans: `184tn9` (approved, pending) also edits `runner_shared.py` (lane reclaim prompt and deferred integration shells), and `zrvtm2` (executed at `ea206c49`) edited the interrupt path. File overlap only; no ordering dependency, and the runner isolates each item in its own lane.
- Scope-Paths justification: `runner_shared.py` holds the recording sites and both consumers; `lane_containment.py` holds the allowlist; the new test file holds E-07.

## Required tests / validation

- `tests/test_attempt_lane_facts.py` (new): both hosts' isolated commit-in-lane turn, the non-isolated negative, `collect_earned_paths` lane preference and fallback, the allowlist projection, and the removed-lane guard. Shown failing before the change.
- Bare `python3 -m pytest` before and after; compare failing node IDs.

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
  - Required evidence: paste the attempt's `starting_head`, `ending_head`, `ending_status`, `worktree_base`, `worktree_branch` from the reproduction, the lane branch tip (`git rev-parse aw/lane/<id6>` or the integrated commit), and the grep listing the `ending_head` write sites.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the allocation arm, and from a reproduction run the attempt's `lane_starting_head` next to `git rev-parse` of the lane at dispatch.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff of the post-turn site and both lane re-record arms showing every pre-existing `ending_head`/`ending_status` line unchanged; paste an attempt record where `lane_ending_head != lane_starting_head` and `ending_head` is still a main-checkout commit.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the allowlist diff and the output of `prior_attempt_summary` for a sample attempt with a lane root, showing the three keys kept and `worktree`/`log`/`prompt` dropped.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `collect_earned_paths` diff; paste `python3 -m pytest -o addopts="" tests/test_runner_shared.py -q` passing (census unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff` of `turn_attempted_nothing` showing docstring-only lines.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_attempt_lane_facts.py -q` passing with the count; then with the E-02..E-05 hunks temporarily reverted, the same command showing cases (1), (2), (4)-lane and (5) FAILING; then passing again after restoring. Paste the bare `python3 -m pytest` summary line BEFORE and AFTER the change and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Three additive, lane-sourced fields on an isolated attempt record (`lane_starting_head`, `lane_ending_head`, `lane_ending_status`), their inclusion in the isolated recovery-prompt allowlist, `collect_earned_paths` preferring the lane range, and a docstring correction. `ending_head`, `ending_status`, and `starting_head` keep their exact current meaning (main's), because the artifact audit depends on it. This graduates backlog `jt0mny` and inherits its `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `agent_workflows/runner_shared.py` (`execute_item_core`, `collect_earned_paths`, `turn_attempted_nothing`'s docstring, and the `process_backlog_close` comment), `agent_workflows/lane_containment.py` (`_PRIOR_ATTEMPT_SAFE_KEYS`), and the new `tests/test_attempt_lane_facts.py`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `jt0mny` `done` with `--evidence` citing the executed plan; its release gate is preserved by the `From-Backlog` handoff.
