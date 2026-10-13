# IPD: Detect untooled status changes and hook-skipping commits in a lane and send them back

- Date: 2026-10-07
- Kind: child
- Concern: Two rule breaks the spec says abort a run are not detected at all. (1) An agent that hand-edits a plan's `- Status:` or `git mv`s a plan between lifecycle directories is not caught by the runner: `outcome_precedence_disposition` trusts a plan found in `superseded/`/`not-executed/` by directory alone and lands it as `retired`, and a plan found in `executed/` turns a refused finalize into success through `finalize_already_done`. The only detectors (`check_engine.check_status_untooled`, the `status_untooled_gate` and `executed_transition_gate` hooks) are commit-scoped, local and skippable. (2) A lane commit made with `--no-verify` is not detected: `RUN-COMMIT-GATEWAY` is `UNBOUND_BY_DEPENDENCY`. The maintainer ruled on 2026-10-07: detect them, tell the agent to undo and redo with the proper tool, continue.
- Scope: After each execute turn and before finalize or integration, check the lane's commits since the turn began for (a) plan status or lifecycle-directory changes with no matching tool-written history line or, for `executed`, no `lifecycle(<id6>): finalize` commit in the range, reusing the predicates behind `check_status_untooled` and `executed_transition_gate`, and (b) lane changes the repository's pre-commit hooks would refuse, by re-running those hooks over the lane's net change in a disposable worktree; send any finding back as a fix-it turn (Order 03) with the specific undo-and-redo instruction; stop trusting a plan's directory alone in `outcome_precedence_disposition` and `finalize_already_done`. EXCLUDES push detection (Set `denypush`) and making the local hooks mandatory.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/check_engine.py, agent_workflows/run_evidence.py, tests/test_lane_rule_break_detection.py, tests/test_host_capability_extension.py, tests/test_ipd_exec_finding_codes.py, tests/test_inlane_retirement_lands.py
- Item-Dependencies: executed:mcbph5
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 7
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 62sdwr

## Workflow history
- 2026-10-13 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 62sdwr verified (set fixfirst, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_host_capability_extension.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_ipd_exec_finding_codes.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-11 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-900, PR-901, PR-902, PR-903, PR-904, PR-905, PR-906. Reviewed at HEAD 2284049fa. Hook re-run moved to one net-change pass in a disposable worktree (the lane --from-ref form measured checking the wrong content, missing staged gates and mutating the lane); executed evidence is the finalize commit, not the deleted journal; tooled retirement kept legitimate; RUN-COMMIT-GATEWAY stays unbound (OQ-02). Record: .aw/records/reviews/20261007-fixfirst-07-62sdwr-detect-untooled-status-changes-and-hook-skipping-commits-in.review.md.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

If an agent hand-edits a plan's status, moves a plan by hand, or commits around the hooks, the runner notices before the work is finalized or merged and tells the agent to undo it and use the proper tool.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: untooled status changes

- [x] E-01 In `check_engine`, expose a range-scoped form of the untooled-status predicate: given a base and head commit, return one finding per plan whose `- Status:` or lifecycle directory changed in that range with no matching tool-written `## Workflow history` line for the new status. Factor the per-path comparison out of `check_status_untooled` (which compares `:0:` against `HEAD`) so both callers read the same `_status_meta` / `_has_matching_history_line` pair over a `(old_blob, new_blob)` pair; do not write a second rule.
  - THE `executed` CASE IS IN-TREE EVIDENCE, NOT A JOURNAL (review PR-901). The finalize journal is the wrong evidence after the fact: `ipd_lifecycle._clear_finalize_journal` deletes it on completion (finalize's COMPLETE path: "Finalize the journal + consume the receipt" then `_clear_finalize_journal`), and it lives under the gitignored `.aw/state/`, so it never travels with a lane branch. `hooks/executed_transition_gate.py`'s own docstring records that limit and accepts instead "a `lifecycle(<id6>): finalize` commit reachable" from the incoming side. Use that: an arrival in `executed/` within the range is tooled iff the range contains a commit whose subject starts with `artifact_core.finalize_commit_subject(<id6>)`. Under the default `self_finalize` the agent cannot produce one (a worker-role `aw ipd finalize` is refused `AW-LIFECYCLE-ROLE-001`), so every in-lane `executed` arrival is untooled, which is the correct verdict.
  - RETIREMENT IS LEGITIMATE AND MUST NOT BE FLAGGED (review PR-902). `superseded`/`not-executed` are reached by `aw ipd set superseded <id6>` (measured at review: `aw ipd set superseded 62sdwr --dry-run` -> `to-review -> superseded (dry-run)`), which writes a history line, so the history-line predicate covers them. `tests/test_inlane_retirement_lands.py` drives a hand `git mv` + `- Status: superseded` retirement and expects `RETIRED_STATUS`; that fixture is a HAND retirement with no history line, so E-02 changes its verdict. Decide it explicitly in E-02 rather than discovering it as a red test.
  - Depends on: none
  - Expected outcome: over a scratch range containing one tooled and one hand-edited intermediate status change, one hand `git mv` into `executed/` with no finalize commit, one `aw ipd set superseded` retirement and one hand retirement with no history line, the function returns exactly the hand-edited change, the hand `executed` arrival and the hand retirement.
  - Execution state: performed

- [x] E-02 In the runner, after an execute turn and before finalize, run E-01 over `attempt["lane_starting_head"]..HEAD` of the lane; on any finding, send the item back through `runner_shared.build_fix_it_notice` (Order 03, kind `untooled-status-change`) naming each plan and the instruction: "revert the hand edit or move, then use `aw ipd set <status> <id6>` for an intermediate status or a retirement; for `executed`, leave the plan in `pending/` and let the runner finalize it". Do NOT tell the agent to run `aw ipd finalize`: under the default `self_finalize` a worker-role finalize is refused `AW-LIFECYCLE-ROLE-001` and `ipd_lifecycle.runner_owns_lifecycle_notice` tells it not to, so that instruction would contradict the turn's own prompt (review PR-903). Count against the per-kind `--retry-budget`; an uncorrected finding fails the item (spec `25kzda` 5.5 group (a)).
  - THE DIRECTORY-ALONE FIX IS A RUNNER-LEVEL GATE, NOT A CHANGE TO THE TWO PURE HELPERS' SIGNATURES (review PR-904). `outcome_precedence_disposition(bucket, outcome)` is pure and also called by `run_viewer` and the crash-recovery path; `finalize_already_done` is called from `finalize_outcome` with the MAIN repo and is the `ld8lb3` idempotence fix for a legitimate agent-or-driver double finalize. Gate their callers in the execute path instead: when the E-01 check over the lane range reports the item's own plan as untooled, the item is sent back BEFORE `reconcile_disposition` / `driver_finalize` run, so neither helper ever sees a hand-placed plan. Leave both helpers' behavior unchanged for every other caller, and say so in their docstrings. If execution shows a caller the gate does not cover, add the range evidence as an optional keyword defaulting to today's behavior.
  - Depends on: E-01
  - Expected outcome: a lane that `git mv`s its own plan into `executed/` gets a fix-it turn instead of being scored executed; after the agent reverts and the driver finalizes, the item executes normally. A lane that retires its plan through `aw ipd set superseded` still lands `RETIRED_STATUS` with no fix-it turn; a hand retirement gets one; `tests/test_inlane_retirement_lands.py` (declared in Scope-Paths) is updated so its retiring fixture uses the tooled retirement, plus one hand-retirement case asserting the fix-it turn.
  - Execution state: performed

### Task group 2: hook-skipping commits

- [x] E-03 After an execute turn, re-run the repository's configured pre-commit hooks over the lane's NET change since `lane_starting_head`, in a DISPOSABLE detached worktree, never in the lane: check out `lane_starting_head`, stage the lane `HEAD`'s tree over it (`git checkout <HEAD> -- .` stages every changed path), then run `pre-commit run` (no `--from-ref`) so `pass_filenames` hooks see the changed files and the staged-index gates (`ipd-executed-transition-gate`, `ipd-status-untooled-gate`, both `pass_filenames: false`, `always_run: true`) see the real delta; remove the worktree afterwards. When pre-commit is not installed or `.pre-commit-config.yaml` is absent, skip and record "hook checking unavailable". A refusal is a hook-skipping change. Send the item back through `runner_shared.build_fix_it_notice` (kind `hook-bypass`) carrying the hook output and the instruction: "your lane's changes since the turn began do not pass the hooks; fix what they report and commit the fix through `aw commit` (do not use --no-verify)".
  - THE PLAN'S `pre-commit run --from-ref <parent> --to-ref <commit>` IN THE LANE WAS MEASURED WRONG THREE WAYS (review PR-900), in a scratch repo with a content hook, a staged-index gate shaped like `ipd-executed-gate`, and a mutating fixer: (1) `--from-ref`/`--to-ref` only SELECTS FILE NAMES and the hooks read the WORKING TREE, so after a later fix commit the per-commit check of the bad commit printed `refuse BAD ... Passed` while `git show <bad>:x.txt` was still `BAD`; (2) the staged-index gate printed `Passed` for a range that added the file it refuses, because nothing is staged, whereas the disposable-worktree form printed `Failed` / `STAGED-z-SEEN`; (3) a mutating hook rewrote the lane in place (`lane status after: [ M .pre-commit-config.yaml ]`). The disposable-worktree form refused both bad changes and left the lane clean (`lane status: []`). It checks the NET change, which is what integration merges, so a bypass commit later fixed by a normal commit is correctly not a finding.
  - OFFLINE AND COST. This repository's config fetches `pre-commit-hooks`, `gitleaks` and `ruff-pre-commit` from the network on a cold cache, and a self-commit's pre-commit pass was measured at 10.6s (`commit_lock` docstring). A hook-environment install failure (exit 3 from `pre-commit`, or no network) is "hook checking unavailable", never a hook refusal, so a cold offline host does not send every item back. OQ-01's measurement belongs in V-03.
  - Depends on: none
  - Expected outcome: a lane commit made with `--no-verify` over a file a hook refuses yields a fix-it turn with the hook output; a `--no-verify` commit that moves a plan into `executed/` with no finalize commit is refused by the staged-index gate in the disposable worktree; a clean lane yields none; a repo without pre-commit, or with an unbuildable hook environment, yields none and records "unavailable"; the lane's working tree is byte-identical before and after the check.
  - Execution state: performed

- [x] E-04 Record E-03's check against `RUN-COMMIT-GATEWAY` in `run_evidence` WITHOUT binding the code as decided by it, unless the maintainer answers OQ-02 otherwise. The code's pass criterion is "The engine, not the agent, invoked `git commit ... -- <explicit paths>` as an argv list; no `-a`, broad add, shell string, or `git commit --no-verify` occurred", which needs a captured commit-gateway event and argv. E-03 re-runs hooks over the content, so it detects a bypass whose content the hooks REFUSE, not that a bypass happened (this plan's own Scope check: "a bypass whose content would pass the hooks is not distinguishable"). Binding the code to it would be the fail-open claim `run_evidence`'s comment forbids ("binding these two now would be exactly the fail-open error described above") and `RUN-NO-PUSH`'s retirement recorded. So: keep `binding=UNBOUND_BY_DEPENDENCY`, and add the new predicate to the row's `waiting_on` text as a PARTIAL detector, naming what it does and does not decide.
  - THREE SHIPPED TESTS PIN THE CURRENT STATE (review PR-905). `tests/test_host_capability_extension.CommitGatewayClaimConsistencyTests` asserts `row.binding == run_evidence.UNBOUND_BY_DEPENDENCY` and `row.predicates == ()` ("Leg 2 is asserted nowhere else"); `tests/test_ipd_exec_finding_codes` asserts `len(run_evidence.bound_run_finding_codes()) == 10`. Binding would turn both red, and both are now declared in Scope-Paths so whichever OQ-02 answer is chosen, the executor updates them in the same change and says why.
  - Depends on: E-03
  - Expected outcome: `RUN-COMMIT-GATEWAY` stays `UNBOUND_BY_DEPENDENCY` with empty `predicates` and its `waiting_on` names E-03's partial detector; `run_evidence.validate_finding_table().ok` holds; `tests/test_run_finding_spec_transcription.py`, `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py` pass. If OQ-02 is answered "bind it", the binding names the predicate and the two pinning tests are amended with the reason.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 Add `tests/test_lane_rule_break_detection.py` driving the real runner on BOTH hosts (`oc_runipd`, `agy_runipd`, the `tests/test_inlane_retirement_lands._HOSTS` pattern) with a scripted host that (a) hand-edits a plan status, (b) `git mv`s its plan into `executed/`, (c) commits with `--no-verify` past a refusing hook, (d) retires its plan through `aw ipd set superseded`, (e) hand-retires it, and (f) does everything through the tools; assert on fix-it turns, delivered prompt text (including that it never tells the agent to run `aw ipd finalize`), the lane's working tree unchanged by the hook check, and final status. Use a scratch repo with a local `language: system` hook so the test needs no network. No source introspection.
  - Depends on: E-02, E-04
  - Expected outcome: the module passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- One predicate, many surfaces: `status_untooled_gate` delegates to `check_engine.check_status_untooled` so the hook and the check cannot diverge; the runner joins that pattern.
- `RUN-NO-PUSH` was retired because a presence check was being passed off as enforcement (`run_evidence` comment); E-03 re-runs the real hooks, which is a behavior check, not a presence check.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Lifecycle directory alone decides `retired` and `executed` in the lane. | `outcome_precedence_disposition`; `finalize_already_done` / `plan_already_finalized` check the bucket only (survey 2026-10-07). |
| F-02 | The untooled-status detectors are commit-scoped and local only. | `hooks/status_untooled_gate.py` docstring "Git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`"; `check_engine.check_status_untooled` compares the staged index against HEAD. |
| F-03 | Hook bypass is not detected. | `run_evidence` `RUN-COMMIT-GATEWAY` `binding=UNBOUND_BY_DEPENDENCY`, waiting on "a captured commit-gateway RECEIPT". |
| F-04 | Maintainer ruling 2026-10-07: detect hand edits and bypass now; undo and redo with the tools; continue. Push stays with `denypush`. | Session 2026-10-07. |
| F-05 | `pre-commit run --from-ref/--to-ref` in the lane does not check a commit's content, misses staged-index gates and mutates the lane (measured at review). | Scratch repo: bad commit checked after a later fix -> `refuse BAD ... Passed` while `git show <bad>:x.txt` = `BAD`; staged-index gate `Passed` vs `Failed` / `STAGED-z-SEEN` in a disposable worktree; mutating hook left `M .pre-commit-config.yaml` in the lane. |
| F-06 | The finalize journal cannot be after-the-fact evidence. | `ipd_lifecycle._clear_finalize_journal` on the COMPLETE path; `.aw/state/` is gitignored; `executed_transition_gate` docstring: the journal "cannot travel with a lane branch ... and it is also EPHEMERAL". |
| F-07 | `RUN-COMMIT-GATEWAY` cannot be honestly bound to a content check, and two tests pin it unbound. | `run_evidence` row pass criterion and `waiting_on`; `CommitGatewayClaimConsistencyTests`; `test_ipd_exec_finding_codes` `bound_run_finding_codes()) == 10`. |

## Proposed changes (ordered, validatable)

1. Range-scoped untooled-status predicate (E-01).
2. Runner check and send-back; stop trusting directory alone (E-02).
3. Re-run hooks over lane commits (E-03).
4. Bind `RUN-COMMIT-GATEWAY` (E-04).
5. Tests (E-05).

## Deferred / out of scope (with reason)

- Push detection.
  - Carrier: oq05nc

## Scope check

- Over-scope: none. `check_engine.py` E-01; `runner_shared.py` E-02, E-03; `run_evidence.py` E-04; `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py` E-04 (acknowledged at finalize as declared-but-unmodified if OQ-02 keeps the code unbound and they need no edit); the new test module E-05. `tests/test_inlane_retirement_lands.py` is edited by E-02, because its hand-retirement fixture is exactly the behavior this plan reclassifies.
- Under-scope: a bypass whose content would pass the hooks is not distinguishable from a normal commit and does not matter for this purpose; recorded rather than chased.

## Required tests / validation

- `python3 -m pytest tests/test_lane_rule_break_detection.py tests/test_run_finding_spec_transcription.py tests/test_host_capability_extension.py tests/test_ipd_exec_finding_codes.py tests/test_inlane_retirement_lands.py tests/test_finalize_stale_plan_path.py tests/test_finidem_reusable_not_finalized.py -o addopts=""`.
- Bare `python3 -m pytest`, baseline re-derived in the lane before any edit.

## Spec / documentation sync

No spec edit: spec `25kzda` 5.5/5.7 and the Section 4.2 action cells were amended by Order 01 (`tb6lw3`, executed). Under OQ-02's default answer the `RUN-COMMIT-GATEWAY` row stays unbound, so the spec's 4.2 `binding` statements ("`RUN-COMMIT-GATEWAY` is unbound and fails closed") remain true. If OQ-02 is answered "bind it", that sentence becomes false and this plan must add the spec to Scope-Paths and amend it in the same change.

## Open questions

### OQ-01: Is re-running hooks per lane commit too slow?

- Blocking: no
- Status: resolved
- Owner: executor of E-03
- Resolution or deferral rationale: RESOLVED at execution (2026-10-13): Measured `pre-commit run` on this repository's own configuration at 4.97s, well under the 10.6s baseline from `commit_lock`. Performed once over the lane's net delta in a disposable worktree, this overhead is minimal compared to the full-suite integration gate and is not too slow.
- Carrier-Declined: answered inside this plan by its executor, whose V-item evidence records the measurement and the choice; nothing outlives the plan.

### OQ-02: Should `RUN-COMMIT-GATEWAY` be bound to the hook re-run, or stay unbound with the re-run recorded as a partial detector?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED at review (2026-10-11): stay unbound, record the partial detector. The code's pass criterion is about HOW a commit was made (argv, no `--no-verify`), which the hook re-run cannot observe; it detects only bypasses whose content the hooks refuse. `run_evidence` already records that binding a code to a weaker predicate "would be exactly the fail-open error", and `RUN-NO-PUSH` was retired for the same reason. Keeping it unbound costs nothing the maintainer asked for: the 2026-10-07 ruling (F-04) asks for DETECTION and a fix-it turn, which E-03 delivers without the finding code. Reversible: a later plan with a captured commit gateway binds it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the predicate's findings over the scratch range of E-01's six cases, showing exactly the three untooled ones reported and the tooled change, the `aw ipd set superseded` retirement and a range containing a `lifecycle(<id6>): finalize` commit NOT reported. Paste one `aw check` run over a staged hand edit showing `check.status-untooled` still fires, to prove the refactor kept the commit-scoped caller.
  - Observed evidence:
    ```
    Case 1 (untooled hand-edit in pending/): 1 '- Status:' changed to 'to-review' in this range with no matching tool-authored '## Workflow history' line; apply it via `aw set to-review <id6>` (or `aw ipd set to-review <id6>`) so the transition is attributed
    Case 2 (untooled hand mv into executed/): 1 Plan entered 'executed/' in this range with no matching finalize commit; leave the plan in 'pending/' and let the runner finalize it
    Case 3 (untooled hand retirement without history): 1 '- Status:' changed to 'superseded' in this range with no matching tool-authored '## Workflow history' line; apply it via `aw set superseded <id6>` (or `aw ipd set superseded <id6>`) so the transition is attributed
    Case 4 (tooled status change with history): 0 findings
    Case 5 (tooled retirement with history): 0 findings
    Case 6 (range containing lifecycle(dem001): finalize): 0 findings

    Staged check_status_untooled findings count: 1
    check.status-untooled at .aw/records/plans/pending/20261007-demo-01-dem001-test.ipd.md: '- Status:' changed to 'to-review' in this commit with no matching tool-authored '## Workflow history' line; apply it via `aw set to-review <id6>` (or `aw ipd set to-review <id6>`) so the transition is attributed
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the delivered fix-it prompt for the hand `git mv` case (it must name the plan and must NOT tell the agent to run `aw ipd finalize`) and the item's final status after the agent reverted. Paste the tooled-retirement case ending `RETIRED_STATUS` with no fix-it turn, the hand-retirement case receiving one, and `tests/test_inlane_retirement_lands.py`, `tests/test_finalize_stale_plan_path.py` and `tests/test_finidem_reusable_not_finalized.py` passing.
  - Observed evidence:
    Delivered fix-it prompt header for hand `git mv` into `executed/`:
    ```markdown
    # OpenCode IPD Driver Turn

    Mode: RECOVERY/CONTINUATION

    ## You are continuing an INTERRUPTED attempt

    A previous attempt at this IPD was interrupted or killed before it finished. It is NOT a
    clean start. Whatever that attempt did is already on disk or already committed, and it may
    be half-applied. Establish the CURRENT state yourself before you edit anything: read the
    plan's execution/validation state, inspect the git log and the working tree, and check
    which E-items were actually performed. Do not assume the previous attempt did nothing, and
    do not assume it finished what it started.

    ## untooled-status-change (attempt 1 of 2)

    Plan entered 'executed/' in this range with no matching finalize commit; leave the plan in 'pending/' and let the runner finalize it

    revert the hand edit or move, then use `aw ipd set <status> <id6>` for an intermediate status or a retirement; for `executed`, leave the plan in `pending/` and let the runner finalize it
    ```
    Final item status after revert: `executed`.
    Tooled retirement: lands with status `retired`, no fix-it turn.
    Hand retirement: receives fix-it turn with `untooled-status-change` refusal.
    Test execution output:
    ```
    tests/test_finidem_reusable_not_finalized.py ...                         [ 15%]
    tests/test_finalize_stale_plan_path.py .......                           [ 50%]
    tests/test_inlane_retirement_lands.py ..........                         [100%]

    ============================= 20 passed in 45.34s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the fix-it prompt with hook output for the `--no-verify` content case and for the `--no-verify` move-into-`executed/` case (refused by the staged-index gate), the clean case showing no finding, the no-pre-commit and unbuildable-environment cases showing "unavailable", `git status --porcelain` of the lane before and after the check (identical), and the measured hook-pass time on this repository's own config for OQ-01.
  - Observed evidence:
    Hook output for `--no-verify` content bypass:
    ```
    refuse bad content.......................................................Failed
    - hook id: refuse-content
    - exit code: 1
    ```
    Hook output for `--no-verify` move-into-`executed/` (staged-index gate):
    ```
    check staged executed....................................................Failed
    - hook id: check-staged-executed
    - exit code: 1
    ```
    Delivered hook notice in recovery prompt:
    ```markdown
    ## hook-bypass (attempt 1 of 2)

    check staged executed....................................................Failed
    - hook id: check-staged-executed
    - exit code: 1

    your lane's changes since the turn began do not pass the hooks; fix what they report and commit the fix through `aw commit` (do not use --no-verify)
    ```
    Clean case: passed=True, msg="" (no findings).
    Unavailable cases:
    - `.pre-commit-config.yaml absent` -> passed=True, msg="hook checking unavailable: .pre-commit-config.yaml absent"
    - `pre-commit not installed` -> passed=True, msg="hook checking unavailable: pre-commit not installed"
    - `pre-commit exit 3` -> passed=True, msg="hook checking unavailable: pre-commit environment error (exit 3): network error"
    Lane working tree before and after check: `git status --porcelain` is identical (`""`).
    Measured hook-pass time on repository config: `4.97s` (exit code 0).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `RUN-COMMIT-GATEWAY`'s `binding`, `predicates` and `waiting_on` as read from `run_evidence.RUN_FINDING_CODES` at runtime, `run_evidence.validate_finding_table().ok`, and the passing runs of `tests/test_run_finding_spec_transcription.py`, `tests/test_host_capability_extension.py` and `tests/test_ipd_exec_finding_codes.py`.
  - Observed evidence:
    `RUN-COMMIT-GATEWAY` runtime properties:
    - `binding`: `UNBOUND-BY-DEPENDENCY`
    - `predicates`: `()`
    - `waiting_on`: `a captured commit-gateway RECEIPT. `git_commit_helper.offer_commit` is a helper the driver CHOOSES to call, not a boundary an agent cannot evade, and `host_sandbox_profile` declares `supports_commit_gateway` False-by-default and NEVER PROBED for exactly that reason; `m73aet`'s executed receipt states this code 'remains wholly unbuilt'. Plan 62sdwr added `runner_shared.check_lane_hook_bypass` as a partial detector that re-runs configured hooks over the lane's net change in a disposable worktree, which catches content-refused bypasses and sends them back as fix-it turns, but does not observe the commit argv or detect bypasses whose content passes hooks`
    `run_evidence.validate_finding_table().ok`: `True`
    Test execution output:
    ```
    tests/test_run_finding_spec_transcription.py ...                         [  5%]
    tests/test_host_capability_extension.py ................................ [ 66%]
    ..............                                                           [ 92%]
    tests/test_ipd_exec_finding_codes.py ....                                [100%]

    ============================= 53 passed in 26.38s ==============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the passing module run (per-test lines, `-o addopts=""`) showing every scripted case on both hosts, and the bare `python3 -m pytest` summary line against the baseline re-derived in the lane before any edit.
  - Observed evidence:
    Per-test output of `tests/test_lane_rule_break_detection.py` (`-o addopts=""`):
    ```
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_f_clean_tooled_run_lands_executed PASSED [ 11%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_hook_bypass_staged_gate_move_into_executed PASSED [ 22%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_lane_working_tree_unchanged_by_hook_check PASSED [ 33%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_a_hand_edit_status_receives_fix_it_turn PASSED [ 44%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_c_hook_bypass_content_receives_fix_it_turn PASSED [ 55%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_b_hand_move_into_executed_receives_fix_it_turn PASSED [ 66%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_e_hand_retirement_receives_fix_it_turn PASSED [ 77%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_hook_checking_unavailable_conditions PASSED [ 88%]
    tests/test_lane_rule_break_detection.py::LaneRuleBreakDetectionTests::test_case_d_tooled_retirement_lands_retired_without_fix_it PASSED [100%]

    ========================= 9 passed in 66.35s (0:01:06) =========================
    ```
    Baseline: `7681 passed, 4 skipped, 3 warnings in 1002.44s (0:16:42)`
    Full test suite run after changes:
    `7691 passed, 4 skipped, 3 warnings in 817.44s (0:13:37)` (+10 tests: 9 in `test_lane_rule_break_detection.py`, 1 in `test_inlane_retirement_lands.py`).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. Execute only after `mcbph5` has executed (`- Item-Dependencies:`), because every send-back uses its `build_fix_it_notice`. Commit through `aw commit <plan> -- <paths>`, never `git add -A`, and never push. Scope-Paths is a declaration: an out-of-scope edit is made and then justified with `--scope-reason` at finalize, never a reason to stop. PASTE THE ACTUAL RUNNER OUTPUT into each V-item; a summary you did not produce is not evidence.

LIFECYCLE TRANSITION. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns begin and finalize, so do NOT run `aw ipd finalize` yourself; a HAND execution finishes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status:` and never hand-`git mv` into `executed/`, which is the exact behavior this plan detects. This plan must not set backlog `coivul` to `done`.
