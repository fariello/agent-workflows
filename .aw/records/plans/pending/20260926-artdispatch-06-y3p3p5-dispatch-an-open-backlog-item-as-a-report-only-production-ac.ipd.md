# IPD: Dispatch an open backlog item as a report-only production action verified by the BACKLOG codes

- Date: 2026-09-26
- Kind: child
- Concern: THE BACKLOG HALF OF PRODUCTION IS UNBUILT (spec `z7nbn1` section 3, OQ-05, acceptance 5.5c). `run_selection_policy._BACKLOG_ACTIONS` maps `open -> plan`, and after plans `8l8dgb` and `aeq7f8` a queue can carry a backlog item and the runner can run a production turn, but no dispatcher exists for `backlog`/`plan`, and the five verification codes of approved spec `25kzda` 4.9 (`BACKLOG-GRADUATE-COUNT`, `BACKLOG-GRADUATE-IPD`, `BACKLOG-GATE-HANDOFF`, `BACKLOG-GRADUATE-LEGITIMACY`, `BACKLOG-CROSS-TREE`) re-measured at HEAD `310ea53e` grep to ZERO under `agent_workflows/`. `25kzda` 3.4's `open` row defines the action: author the artifacts the item needs (one or more conformant IPDs, each carrying `From-Backlog` and inheriting `Blocks-Release`), set the item `graduated` using the handoff receipt, verify, and report the IPDs as next actions; setting it `graduated` before a conformant handoff exists, or setting it `done`, is forbidden. The shared gate predicate `check_engine.evaluate_blocking_close` already treats `graduated` as legitimate for a release-gated item ("graduated preserves gate ... `done` still requires handoff, evidence, or explicit de-gating"). THE CROSS-TREE CHECKERS EXIST BUT ARE NOT ALL IN ONE FUNCTION, and that is a load-bearing correction to this plan's first draft: `check_engine.check_release_gates` composes exactly the five ids in `check_engine.RELEASE_GATE_RULES` (`check.live-bug-ungated`, `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`), so two of the four classes `25kzda` 4.9's `BACKLOG-CROSS-TREE` row names are NOT reachable through it: `check.orphaned-live-blocker` lives in `check_engine.release_gate_warnings`, returned separately and DELIBERATELY so it never sets an exit code, and the "dangling source link" class is `check_engine.check_from_spec_dangling`, its own function. `BACKLOG-CROSS-TREE` must consult all three entry points (F-5).
- Scope: IN: (a) the backlog production dispatcher, reusing plan `aeq7f8`'s production turn, commit, report-only `generated_next_actions` and quarantine machinery, with a backlog-specific prompt (house "Acting on a backlog item" rules: review-ready `to-review` plans, `aw ipd scaffold --from-backlog <id6>` which inherits Priority/Work-Kind/Blocks-Release, `aw ipd lint` conforming; "do NOT change the item's `- Status:`; the runner sets `graduated`"); (b) the five `BACKLOG-*` verifiers in `agent_workflows/production_checks.py` beside the `SPEC-PLAN-*` ones, implementing `25kzda` 4.9's pass criteria, message templates and Action columns; (c) on success, the runner sets the item `open -> graduated` through the GATED setter spelling `aw backlog set <selector> --status graduated --message ... --no-commit` AFTER the handoff commit, citing the produced plans (`--graduated-to` when the produced plans share a Set), then re-runs `BACKLOG-CROSS-TREE`; on any failure, the item is left `open` (restored through the setter when the failure is found after the transition); the item is never set `done`; (d) spec 5.5c's refusal matrix tested; (e) A STATUS PRECONDITION ON THE RUNNER'S OWN TRANSITION, because `aw backlog set --status graduated` is a legal transition from EVERY status including `done` and therefore cannot itself detect the `done` case `BACKLOG-GRADUATE-LEGITIMACY` exists to catch (F-6); (f) the item SELECTOR discipline for both the transition and the rollback, because a path captured at dispatch is STALE the moment the setter moves the file, so a rollback issued against it exits 2 having changed nothing (F-7). OUT: authoring a SPEC from a backlog item (25kzda 3.4 permits "any spec it requires"; spec `z7nbn1` 5.5c tests plans only, and a spec-producing graduation needs the human-approval attestation a runner cannot supply; recorded as OQ-01); the existing post-execution `process_backlog_close` (`done` on executed carriers), which is unchanged.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_backlog_production.py
- Item-Dependencies: executed:aeq7f8
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 6
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: y3p3p5
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-06-y3p3p5-dispatch-an-open-backlog-item-as-a-report-only-production-ac.review.md`. Every authored claim re-derived at lane HEAD 8ef40273 by driving the real setter and the real checkers on a scratch repo, not by reading source. ADDED two HIGH findings that the plan as written would have shipped as silent failures. First, `aw backlog set --status graduated` is LEGAL FROM `done`, so the runner's own transition moves the item out of `done/` and the authored LEGITIMACY clause "its status is not `done`" then PASSES on exactly the input it was written to catch (driven: agent closes `done` exit 0, runner graduates exit 0, item ends `- Status: graduated`); the verifier now takes a `status_before` the runner captures and E-05 refuses to transition from any status but `open`. Second, the authored rollback reused the path captured at dispatch, which names nothing after the setter has moved the file, so a post-transition failure would have stranded the item in `graduated/` while the run reported containment (driven: exit 2, `no such item`); the transition and the rollback now select by id6 and E-06 verifies the item landed back under `open/`. Also CORRECTED the plan's own F-3: `BACKLOG-CROSS-TREE`'s four finding classes are NOT all in `check_release_gates`, whose composition is exactly `RELEASE_GATE_RULES`; `check.orphaned-live-blocker` lives in `release_gate_warnings` (deliberately non-exit-coding, needing its own disposition) and the dangling-source-link class in `check_from_spec_dangling`, both measured returning findings where `check_release_gates` returned `[]`. Further fixes: the setter's `--no-commit` and exit-code contract (PR-005), the corpus counts re-derived (620->634, PR-006), and the gating measured to be a function of the `--status` flag rather than the selector shape (PR-007). Split the six items into eleven (E-01..E-11) and rebuilt the V checklist to an 11-item bijection. `aw ipd lint --phase review-finalize` conforming, 0 findings.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 06 of Set artdispatch). The five BACKLOG-* codes re-measured at HEAD 310ea53e (zero enforcement); evaluate_blocking_close's graduated branch and check_release_gates' cross-tree rules confirmed as the authorities to consume; backlog corpus measured (166 open, 620 total).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running an open backlog item produces review-ready plans that link back to it and carry its release gate, moves the item to `graduated` (never `done`) through the gated setter only after a verified handoff, and leaves the item `open` whenever any of the five backlog handoff checks fails.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 RE-MEASURE at the executing HEAD: `grep -rn "BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` (expect only plan `aeq7f8`'s module scaffolding, no enforcement); paste `25kzda` 4.9's five rows' pass criteria and Action cells verbatim into Findings; read plan `aeq7f8`'s executed production turn and name the extension points this plan uses (its production arm, its baseline capture, its `generated_next_actions` field and its `record_lane_preserved` wiring).

  THEN RE-DERIVE THE FOUR SETTER FACTS THIS PLAN'S DESIGN RESTS ON, on a scratch repo carrying one release record and one `open` item with `- Blocks-Release: next`, pasting each command and its exit code. These are stated as the review measured them so a divergence is visible rather than silently absorbed; every one is a LIVE code fact, so re-derive rather than trust: (i) `aw backlog set <selector> --status graduated` on that item SUCCEEDS with exit 0 and the predicate's `graduated preserves gate` verdict; (ii) the same spelling with `--status done` REFUSES with exit 1, naming the three fixes, and this holds for BOTH an id6 selector and a path selector, so the gating is a function of the `--status` FLAG and not of the selector shape (the review measured the id6 spelling refusing identically, which matters because `close_backlog_item` passes an id6); (iii) the POSITIONAL `aw backlog set done <id6>` spelling closes the SAME gated item with exit 0, which is the bypass `close_backlog_item`'s docstring records; (iv) `--status graduated` is legal FROM `done/`, exiting 0 and moving the file back, which is F-6's defect and the reason E-05 needs its own precondition.

  THEN RE-DERIVE WHAT EACH CROSS-TREE ENTRY POINT ACTUALLY RETURNS, because the plan's first draft named one function for four finding classes and two of them are not in it (F-5). Print `check_engine.RELEASE_GATE_RULES`, then drive all three entry points (`check_release_gates`, `release_gate_warnings`, `check_from_spec_dangling`) on scratch trees built to trigger each class in turn: a mismatched gate on the produced plan, a dangling `From-Backlog`, an `open` gated item whose `From-Backlog` plan is still pending (the orphaned-live-blocker class), and a produced plan with a dangling `From-Spec`. Record which entry point reports which id. The review measured the last two returning NOTHING from `check_release_gates`.
  - Depends on: none
  - Expected outcome: the five rows pasted; the four setter facts pasted with exit codes, including that `--status graduated` succeeds from `done/`; each of the four cross-tree classes attributed to the entry point that actually reports it; extension points named.
  - Execution state: pending

### Task group 2: the verifiers

- [ ] E-02 ADD THE FOUR PRE-TRANSITION VERIFIERS to `agent_workflows/production_checks.py`, each returning templated findings from `25kzda` 4.9: `backlog_graduate_count(repo, item_id6, baseline_plan_ids)` (at least one new ACTIVE plan and every new plan claiming this item links `From-Backlog: <id6>`); `backlog_graduate_ipd(repo, item_id6, produced_paths)` (every produced plan canonical, `to-review`, in `pending/`, resolved `Item-Dependencies`, `review-finalize` lint conforming; share `aeq7f8`'s conformance helper rather than copying it); `backlog_gate_handoff(repo, item_id6, produced_paths)` (if the item carries `Blocks-Release: R`, every produced plan carries a gate `check_engine._same_release` equates with R, checked BEFORE the transition; all references resolve).

  `backlog_cross_tree(repo, item_id6, produced_paths)` MUST CONSULT THREE ENTRY POINTS, NOT ONE (F-5). `25kzda` 4.9's row requires "no dangling gate, mismatched gate, orphaned live blocker, or dangling source link", and `check_release_gates` composes only `RELEASE_GATE_RULES` (measured: `check.live-bug-ungated`, `check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.blocks-release-dangling`, `check.from-backlog-dangling`). So also call `check_engine.release_gate_warnings` (the only source of `check.orphaned-live-blocker`) and `check_engine.check_from_spec_dangling` (the "dangling source link" class); driven on a scratch tree, a produced plan with a dangling `From-Spec` and an `open` gated item with a pending carrier BOTH return `[]` from `check_release_gates` alone. Call the three, do not reimplement any of them, and filter to findings located at the item or a produced path.

  ONE WARN-SEVERITY CLASS NEEDS AN EXPLICIT DISPOSITION rather than being swept in silently: `release_gate_warnings` is documented as returning findings that "must not set the exit code", so treating `check.orphaned-live-blocker` as a hard `BACKLOG-CROSS-TREE` failure promotes a deliberate warning into a run-failing error. Decide and record whether it fails the item or is reported as a warning beside the success, and state the reason. The review's own measurement is the argument for care here: an `open` gated item with a pending `From-Backlog` carrier produces this warning, which is the EXPECTED mid-graduation state, so a naive promotion would fail a legitimate handoff at exactly the moment it is correct.
  - Depends on: E-01
  - Expected outcome: the four functions return `[]` for a legitimate handoff and the templated finding for each violation; `backlog_cross_tree` is shown reporting a dangling `From-Spec` and an orphaned live blocker that `check_release_gates` alone misses; the warn-class disposition is recorded with its reason.
  - Execution state: pending

- [ ] E-03 ADD `backlog_graduate_legitimacy(repo, item_id6, handoff_commit, *, status_before)`, THE VERIFIER WHOSE INPUTS THE FIRST DRAFT COULD NOT SUPPLY. `25kzda` 4.9's pass criterion is that the item "changed `open -> graduated` through the setter only after the handoff commit; history cites the generated artifacts; the item was NOT set `done`", so it asserts a TRANSITION, not a final state, and three of its four clauses are unobservable from the post-transition tree alone:

  (1) "was NOT set `done`" CANNOT be read off the item's status after the runner's own setter call, because `--status graduated` is a legal transition from `done` and the review measured it succeeding (exit 0) and moving the file from `done/` to `graduated/`. An agent that closed the item `done` therefore leaves an item reading `- Status: graduated` and the naive clause PASSES. Hence `status_before`: the runner records the item's status immediately before its own transition, and this clause compares THAT against `open`. Anything else (`done`, `graduated`, `parked`) is a `BACKLOG-GRADUATE-LEGITIMACY` finding, which also catches the second half of the criterion, an agent that set `graduated` itself before any handoff commit existed.

  (2) "through the setter" is evidenced by the item's own `## Workflow history` carrying the setter's record with the runner's message, which `_reattach_history` appends on every `aw backlog set`. Note what this can and cannot prove: an agent that ran the setter ITSELF also produces a setter record, so this clause proves TOOLED transition, not RUNNER authorship; (1) is what distinguishes them, which is why both clauses are required.

  (3) "only after the handoff commit" is a commit-ancestry question: the commit that moved the item file must have the handoff commit in its parent chain. State the honest limit rather than over-claiming: on the isolated-lane path the item move and the produced plans may ride ONE lane commit, in which case ancestry is not strictly-after and the check must accept same-commit; verify which shape the executing code produces and encode that, do not assume.

  (4) "history cites the generated artifacts" is satisfied by the runner's own `--message`, so it is a check on the message the runner composed, not on the agent.
  - Depends on: E-02
  - Expected outcome: the verifier takes `status_before` and refuses a non-`open` prior status; the four clauses are implemented with the same-commit ancestry question resolved against the executing code; the `done`-then-graduated case is shown FAILING where a post-state-only check passes.
  - Execution state: pending

### Task group 3: the dispatcher

- [ ] E-04 ADD THE BACKLOG PRODUCTION TURN AND THE PRE-TRANSITION GATE. Route a `backlog`/`plan` entry to the production turn plan `aeq7f8` built, with the backlog prompt (Scope bullet (a)); capture the baseline plan inventory AND the item's status (which is `status_before` for E-03); after the turn, commit the new plans path-scoped (the handoff commit); run COUNT, IPD and GATE-HANDOFF. Any finding: item `fail-gate` with every finding recorded via `render_stream.record_refusal`, item left `open`, produced files quarantined on the lane through the `record_lane_preserved` wiring `aeq7f8` established and not integrated. NO TRANSITION IS ATTEMPTED in that path, which is what makes "the item is left `open`" true by construction rather than by rollback.
  - Depends on: E-03
  - Expected outcome: a fake agent writing one conformant plan reaches the transition step; each pre-transition finding leaves the item untouched at `open` with the lane recorded as preserved.
  - Execution state: pending

- [ ] E-05 PERFORM THE GATED TRANSITION, WITH THE PRECONDITION AND THE SELECTOR DISCIPLINE THE SETTER DOES NOT SUPPLY. With no pre-transition finding, run `aw backlog set <item id6> --status graduated --message "graduated by run <run-id>: <plan id6s>"` through `pinned_module_argv` in the tree holding the handoff commit, then commit that transition path-scoped. Four corrections the first draft needed, each measured:

  REFUSE UNLESS THE ITEM IS STILL `open` (F-6). Read the item's status immediately before the call and refuse the transition if it is not `open`, recording a `BACKLOG-GRADUATE-LEGITIMACY` finding instead. The setter will NOT do this for you: `--status graduated` is legal from every status, so an agent that closed the item `done` in its turn is silently "fixed" by the runner's own call, which then reports a successful graduation. Measured on a scratch gated item: agent sets `done` (positional spelling, exit 0), runner then runs `--status graduated` (exit 0), and the item ends `graduated` with `- Status: graduated` on disk, so every post-state clause passes while the criterion was violated.

  SELECT THE ITEM BY ID6, NOT BY A PATH CAPTURED AT DISPATCH (F-7). The setter MOVES the file between status directories, so a path captured when the item was in `open/` names nothing once it is in `graduated/`. Measured: `aw backlog set <open/ path> --status open` after the item was graduated printed `aw backlog set: no such item: <path>` and exited 2, having changed nothing. An id6 selector resolves regardless of the item's current directory (measured: `aw backlog set wmnm6b --status graduated` succeeded), and it is the spelling `close_backlog_item` already passes. This applies to the ROLLBACK especially, because that is the call issued when the item has already moved.

  PASS `--no-commit` AND COMMIT THROUGH THE TOOLED PATH. `aw backlog set` without it attempts its own self-commit, which on a lane both duplicates the runner's path-scoped commit and (measured on a scratch repo with no HEAD) emits `warning: self-commit skipped: git commit failed` into the runner's output. `close_backlog_item` already passes `--no-commit` for exactly this reason and `commit_backlog_close` owns the commit; follow that split rather than inventing a second one.

  CHECK THE SETTER'S EXIT CODE AND FAIL THE ITEM ON NONZERO. The setter has three distinct refusal exits reachable here (2 for an unresolvable or ambiguous selector, 2 for a malformed `--graduated-to`, 1 for a predicate refusal), and a transition believed to have happened but refused would make every later check read a stale tree. Only pass `--graduated-to` when every produced plan shares ONE Set; it is validated at the setter and a malformed value exits 2 (measured: a non-kebab value refused with "takes lowercase-kebab setids of at most 40 characters"), so an agent-chosen Set id must be canonicalized or omitted rather than forwarded blindly.
  - Depends on: E-04
  - Expected outcome: the transition runs only from `open`, selects by id6, passes `--no-commit`, and fails the item on any nonzero setter exit with the code and stderr recorded.
  - Execution state: pending

- [ ] E-06 RUN THE POST-TRANSITION CHECKS AND THE ROLLBACK. After the committed transition, run LEGITIMACY (with `status_before`) and CROSS-TREE (all three entry points). A finding THERE: restore the item through the setter BY ID6 (`aw backlog set <id6> --status open --message "handoff incomplete: <code>" --no-commit`, the recovery `25kzda` 4.9 names), commit that restore path-scoped, verify the item is back under `open/` before reporting the rollback as done, and fail the item. A rollback that itself exits nonzero is reported as a CONTAINMENT FAILURE naming the item, its current status and the manual command, never swallowed: an item stranded in `graduated/` with no handoff is the one state this plan must not leave silently, because `aw attention` maps `graduated` to `active` and the item disappears from the `ready` set a human works from. Success: record `generated_next_actions` on the item, end it `executed`.

  THE RUNNER NEVER SETS `done`, and `process_backlog_close` must not fire for a production item (it keys on a plan's `from_backlog` after execution); confirm by test that a `backlog`-typed entry never reaches it.
  - Depends on: E-05
  - Expected outcome: a legitimate handoff ends `executed` with the item under `graduated/`; a post-transition finding leaves the item verified back under `open/`; a failed rollback is reported as a containment failure with the manual command.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_backlog_production.py` WITH SPEC 5.5c's MATRIX (behavioral only; temp git repos; fake agent via patched host spawn; `AW_HOME` needs no per-test handling, the root `conftest.py` already re-points it via an autouse fixture, so do not add a second mechanism). On BOTH hosts: (1) success: one conformant plan carrying `From-Backlog` and the item's `Blocks-Release: next`; item `graduated` via the setter (its history shows the record), never `done`; plan listed in `generated_next_actions`; queue id set before equals after, and resume spawns nothing (spawn patched to fail if called); (2) `BACKLOG-GRADUATE-COUNT`: no plan written; (3) `BACKLOG-GRADUATE-IPD`: a plan with `- Status: draft` or unresolved `Item-Dependencies`; (4) `BACKLOG-GATE-HANDOFF`: a release-gated item whose plan omits the gate. In EACH of (2)-(4) the item ends `open` having never been transitioned, and the item fails naming the code.
  - Depends on: E-06
  - Expected outcome: (1) through (4) pass on both hosts; every case FAILS against the pre-change code.
  - Execution state: pending

- [ ] E-08 ADD THE THREE `BACKLOG-GRADUATE-LEGITIMACY` RUN-LEVEL CASES, the ones that pin F-6 and F-7. (5a) the fake agent writes a conformant plan AND sets the item `done` itself: the item must NOT end `graduated`, the item fails naming the code, and the item is restored to `open`. THIS CASE MUST FAIL against a build whose precondition is missing, because the runner's own `--status graduated` call succeeds from `done/` and yields a `graduated` item that a post-state check accepts, so paste that failure as the specific harm E-05's precondition prevents. (5b) the agent sets the item `graduated` itself before writing any plan, so the transition precedes the handoff commit. (5c) the ROLLBACK actually lands: after a post-transition failure the item file is under `open/` ON DISK, not merely reported as rolled back; this case must FAIL against a build that rolls back using the dispatch-time path, whose setter exits 2 and strands the item in `graduated/`.
  - Depends on: E-07
  - Expected outcome: (5a), (5b) and (5c) pass on both hosts; (5a) and (5c) FAIL against a build lacking respectively the status precondition and the id6 rollback selector, with the (5a) failure pasted.
  - Execution state: pending

- [ ] E-09 ADD THE TWO `BACKLOG-CROSS-TREE` RUN-LEVEL CASES, each chosen because it is invisible to `check_release_gates` alone (F-5). (6a) a produced plan carrying a dangling `From-Spec`, reported only by `check_from_spec_dangling`. (6b) the orphaned-live-blocker shape, asserted against whichever disposition E-02 recorded: a failure naming the code if that class fails the item, or a warning reported beside a successful graduation if it does not. Both must fail against a build whose `backlog_cross_tree` calls only `check_release_gates`.
  - Depends on: E-08
  - Expected outcome: (6a) and (6b) pass on both hosts and both FAIL against a single-entry-point `backlog_cross_tree`.
  - Execution state: pending

- [ ] E-10 UNIT-TEST THE FIVE VERIFIERS DIRECTLY against hand-built trees, one pass and one fail fixture per pass-criterion clause. For `backlog_graduate_legitimacy` that means a fixture per clause of E-03, INCLUDING `status_before='done'` with a post-transition status of `graduated`, the case a post-state-only check cannot see. For `backlog_cross_tree` that means one fixture per entry point, so a regression that drops an entry point is visible without a run.
  - Depends on: E-09
  - Expected outcome: each clause has a passing and a failing fixture; the `status_before='done'` fixture fails and the three cross-tree entry points each have their own.
  - Execution state: pending

- [ ] E-11 RUN the bare suite before and after, then drive all three cross-tree entry points on a scratch repo after a successful graduation. `aw check release-gates` alone is NOT sufficient evidence: it composes `RELEASE_GATE_RULES` only, so a clean result covers neither the orphaned-live-blocker nor the dangling-source-link class; paste `release_gate_warnings` and `check_from_spec_dangling` on the same tree beside it.
  - Depends on: E-10
  - Expected outcome: the after-minus-before failing node set is empty; all three cross-tree entry points are clean on the scratch tree after a successful graduation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `graduated` means the design is handed off; `done` means the code is written and validated (AGENTS.md "Acting on a backlog item"; `backlog.py` bklgrad comment). A release-gated item may be `graduated` freely and may reach `done` only by handoff, evidence, or de-gating (`evaluate_blocking_close`).
- The GATED backlog setter spelling is `aw backlog set <selector> --status <s>`, which dispatches to `backlog.run_set` and runs the shared predicate; the positional `aw backlog set <status> <selector>` spelling dispatches to `status_set.run_set_command` and does not (`close_backlog_item` docstring, verified live there and re-verified at review). WHAT GATES IS THE `--status` FLAG, NOT THE SELECTOR SHAPE: `cli.py` forks on `getattr(args, "status", None) is None`, so an id6 selector with `--status` is equally gated (measured: `aw backlog set <id6> --status done` on a gated item refused with exit 1). That matters because the runner passes an id6.
- THE SETTER GATES THE DESTINATION, NOT THE SOURCE. `evaluate_blocking_close` branches on `target_status`, so `--status graduated` returns its `ok` verdict regardless of where the item is coming from, including `done/`. The setter is therefore not a precondition check and a runner needing one must carry it (F-6).
- A SELECTOR IS RESOLVED FRESH ON EVERY CALL and the setter MOVES the file, so a path captured before a transition names nothing after it (`selectors.resolve`; measured exit 2, `no such item`). An id6 selector resolves across status directories (F-7).
- `aw backlog set` self-commits unless `--no-commit` is passed; `close_backlog_item` passes it and `commit_backlog_close` owns the commit through `git_commit_helper.offer_commit`.
- `aw ipd scaffold --from-backlog <id6>` inherits Priority, Work-Kind and Blocks-Release (its `--help`), so a well-behaved turn carries the gate by construction; `BACKLOG-GATE-HANDOFF` verifies rather than assumes it.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-4 are the author's, measured at HEAD `310ea53e` (2026-09-26); F-3 and F-4 were CORRECTED by `/plan-review` on 2026-09-26 and F-5 through F-7 were ADDED by it, each driven live on a scratch repo rather than read off the source.

THE TWO ADDED DEFECTS ARE BOTH CASES OF THE PLAN TRUSTING THE SETTER TO ENFORCE SOMETHING IT DOES NOT. `evaluate_blocking_close` branches on the DESTINATION status, so `--status graduated` is legitimate from anywhere; the plan's `BACKLOG-GRADUATE-LEGITIMACY` clause "its status is not `done`" is read after the runner's own transition has already moved the item out of `done/`, so the clause passes on exactly the input it was written to catch. Driven end to end: the agent closes a gated item `done` (positional spelling, exit 0), the runner then runs `--status graduated` (exit 0), and the item ends `- Status: graduated` under `graduated/`. Separately, the setter MOVES the file, so the dispatch-time path E-03 passed to the rollback resolves to nothing once the item has been graduated: the rollback exits 2 printing `no such item` and the item stays stranded in `graduated/` with no handoff, which is the one containment failure this plan exists to prevent.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | verification | The five `BACKLOG-*` codes have zero enforcement. | `grep -rn "BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` -> no hits |
| F-2 | INFO | `check_engine.evaluate_blocking_close` | `graduated` is explicitly legitimate for a gated item and drops nothing. | branch `if target_status == "graduated" and blocks_release: return CloseVerdict(True, "ok", ...)`; driven on a scratch gated item: exit 0 |
| F-3 | INFO (CORRECTED) | `check_engine.check_release_gates` | Cross-tree gate rules exist but this function is NOT all of them; see F-5. | `check_engine.RELEASE_GATE_RULES == ('check.live-bug-ungated', 'check.blocking-item-closed-without-gate', 'check.from-backlog-gate-mismatch', 'check.blocks-release-dangling', 'check.from-backlog-dangling')` |
| F-4 | INFO (CORRECTED) | corpus | 634 backlog items: 177 open, 110 graduated, 330 done, 16 parked, 1 blocked. Re-derived by directory count at lane HEAD; the authored figures (620/166/122/315/15/2) no longer hold, which is expected for a live population and is why E-01 re-derives rather than trusting any of them. | `ls .aw/records/backlog/<status> | wc -l` per status |
| F-5 | MEDIUM | `check_engine.check_release_gates` | `BACKLOG-CROSS-TREE` NEEDS THREE ENTRY POINTS, NOT ONE. `25kzda` 4.9 requires no "dangling gate, mismatched gate, orphaned live blocker, or dangling source link", and two of those four are unreachable through `check_release_gates`: `check.orphaned-live-blocker` is returned only by `release_gate_warnings` (deliberately separate so it never sets an exit code) and the dangling-source-link class is `check_from_spec_dangling`. | On a scratch tree, an `open` gated item with a pending `From-Backlog` plan: `check_release_gates` -> `[]`, `release_gate_warnings` -> `['check.orphaned-live-blocker']`. With a produced plan carrying `From-Spec: nosuch` and a spec corpus present: `check_release_gates` -> `[]`, `check_from_spec_dangling` -> `['check.from-spec-dangling']` |
| F-6 | HIGH | the LEGITIMACY clause "its status is not `done`" | THE `done` CASE IS UNOBSERVABLE AFTER THE RUNNER'S OWN TRANSITION. `--status graduated` is legal from `done`, so the runner's call moves the item out of `done/` and the post-state clause then passes on the violating input. Without a status precondition and a `status_before` input, spec 5.5c's "never `done`" criterion is asserted by a check that cannot fail for it. | Driven in order on a scratch gated item: agent `aw backlog set done <id6>` -> exit 0, item in `done/`; runner `aw backlog set <id6> --status graduated` -> exit 0, item in `graduated/`, file reads `- Status: graduated` |
| F-7 | HIGH | E-03's rollback (`aw backlog set <path> --status open`) | THE ROLLBACK CANNOT WORK, because it reuses the dispatch-time path after the setter has moved the file. A post-transition finding therefore leaves the item in `graduated/` with no valid handoff, while the run believes it contained the failure. `graduated` maps to `active` in the attention view, so the item also vanishes from the `ready` set a human works from. | `aw backlog set <open/ path> --status open` after the item was graduated: `aw backlog set: no such item: <path>`, exit 2, item still in `graduated/`. The id6 spelling on the same item: exit 0, item moved |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the setter's four facts and attributes each cross-tree class to its entry point.
2. E-02 adds the four pre-transition verifiers, including the three-entry-point `backlog_cross_tree`.
3. E-03 adds the LEGITIMACY verifier, which needs `status_before` because the post-state cannot carry it.
4. E-04 adds the production turn and the pre-transition gate (no transition attempted on failure).
5. E-05 performs the gated transition with the `open` precondition and the id6 selector.
6. E-06 runs the post-transition checks and the verified rollback.
7. E-07 adds the run-level success and the three pre-transition refusals.
8. E-08 adds the three LEGITIMACY cases, which pin F-6 and F-7.
9. E-09 adds the two CROSS-TREE cases.
10. E-10 adds verifier unit tests.
11. E-11 runs the suite and all three cross-tree entry points on a scratch tree.

## Deferred / out of scope (with reason)

- Producing a SPEC (rather than plans) from a backlog item.
  - Carrier-Declined: spec `z7nbn1` 5.5c specifies plan production only, and a spec that graduates work must be human-approved (`aw specs set approved --by-human`), which an unattended production turn cannot attest; OQ-01 records it.
- Changing `process_backlog_close` (closing `done` after carriers execute).
  - Carrier-Declined: unchanged by spec `z7nbn1`; E-06 only proves a production item never reaches it.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/backlog.py`, `check_engine.py` are called, not changed. THE `open` PRECONDITION IS DELIBERATELY THE RUNNER'S, NOT THE SETTER'S (E-05, F-6): making `aw backlog set --status graduated` refuse a `done` source would change a shipped, legal transition every human and every other caller depends on, which is a public-contract change far outside this plan's concern. The precondition belongs where the criterion does, in the runner performing the graduation.
- Scope-Paths justification: `production_checks.py` gains the five verifiers beside `aeq7f8`'s; `runner_shared.py` holds the backlog dispatch, transition and rollback; host modules hold any host-specific prompt spelling; the new test file holds E-07 through E-10.

## Required tests / validation

- `tests/test_backlog_production.py` (new): the success path and all five refusal codes of spec 5.5c on both hosts, each leaving the item `open`; report-only and resume checks; verifier unit cases; shown failing before the change.
- THREE CASES MUST FAIL AGAINST A BUILD THAT HAS THIS PLAN'S TURN BUT NOT ITS CORRECTIONS, and they are the tests that carry this review's findings: the `done`-then-graduated case against a build with no status precondition (F-6), the rollback case against a build using the dispatch-time path (F-7), and the dangling-`From-Spec` case against a `backlog_cross_tree` calling only `check_release_gates` (F-5). A suite that passes without these three has not tested the defects.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` section 3 (backlog half), OQ-05 and acceptance 5.5c as written, and `25kzda` 3.4's `open` row and 4.9's five rows with their existing text.
- No user-facing docs.

## Open questions

### OQ-01: May the backlog production turn author a spec instead of plans?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NOT in this plan, from repository evidence. `25kzda` 3.4 allows "any spec it requires (created and approved under the authority of this request)", but spec `z7nbn1` 5.5c's acceptance criterion names plans only, and approval of a spec is a human-only transition (`attention_contract.TRANSITION_AUTHORITY["->approved"]` requires `by_human`); an unattended turn asserting it would forge the attestation the AGENTS.md "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD" rule forbids. The prompt tells the agent to write plans; a turn that writes a spec instead fails `BACKLOG-GRADUATE-COUNT`.

### OQ-02: Scope of the backlog production ruling

- Blocking: no
- Status: resolved
- Owner: maintainer (ruled 2026-09-26)
- Resolution or deferral rationale: RULED by the maintainer 2026-09-26 at spec review (spec `z7nbn1` OQ-05): the backlog production action and ALL FIVE `BACKLOG-*` verification codes of `25kzda` 4.9 are in scope, covered by acceptance criterion 5.5c. This plan implements exactly that set.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the grep; the five `25kzda` 4.9 rows verbatim; the four setter facts each as the command plus its exit code, INCLUDING the `--status graduated`-from-`done/` call showing exit 0 and the item's resulting directory; `RELEASE_GATE_RULES` as printed; and the per-class attribution table naming which of `check_release_gates` / `release_gate_warnings` / `check_from_spec_dangling` reported each of the four `BACKLOG-CROSS-TREE` classes, with the two that `check_release_gates` returns nothing for called out. Also the named `aeq7f8` extension points.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the four signatures and one `python3 -c` run per verifier on a hand-built tree showing `[]` and a templated finding. For `backlog_cross_tree` specifically, paste a run on a tree whose only defect is a dangling `From-Spec` showing the finding, beside a `check_release_gates`-only call on the SAME tree returning `[]`, which is what proves the three entry points are consulted. Paste the recorded warn-class disposition and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `backlog_graduate_legitimacy` signature showing `status_before`, and its output on a tree where the item reads `- Status: graduated` on disk but `status_before='done'`, showing the finding. Paste the resolved same-commit-versus-strictly-after ancestry decision with the code shape it was resolved against.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a failing pre-transition run's item record showing `fail-gate` with the code, the item's on-disk path still under `open/`, and the preserved-lane record with its path. Paste evidence that no setter invocation occurred on that path (for example the item's unchanged `## Workflow history`).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the transition call as issued (showing the id6 selector and `--no-commit`) with its exit code; a run where the item's status is `done` at transition time showing the REFUSAL and the recorded code rather than a successful graduation; and a run where the setter exits nonzero showing the item failed with that code and stderr recorded.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a success run's item record with the item's new location and its history line; a post-transition-failure run showing the rollback call, the item verified back under `open/` on disk, and `git log --oneline` for the item path; and a simulated rollback failure showing the containment-failure report naming the item, its status and the manual command.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_backlog_production.py -q` for cases (1) through (4) passing with the count, and the same cases FAILING against the pre-change code.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste (5a), (5b) and (5c) passing; then paste (5a) FAILING against a build with the status precondition removed (this is the pasted failure E-08 requires) and (5c) FAILING against a build whose rollback uses the dispatch-time path.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste (6a) and (6b) passing, and both FAILING against a build whose `backlog_cross_tree` calls only `check_release_gates`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the verifier unit case names and pass output, one pass and one fail fixture per clause, including the `status_before='done'` fixture and one fixture per cross-tree entry point.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty), and all three cross-tree entry points' output on the scratch tree after a successful graduation.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Running an open backlog item now GRADUATES it: one agent turn writes review-ready plans linked to the item and carrying its release gate, the runner verifies the handoff with the five `25kzda` 4.9 checks, then moves the item to `graduated` (never `done`) through the gated setter and lists the plans as next actions without running them. A failure found BEFORE the transition leaves the item untouched at `open` because no transition is attempted; a failure found AFTER it restores the item through the setter and VERIFIES it landed back under `open/`, reporting a containment failure with the manual command if that restore itself fails. Produced files are quarantined on the lane and not integrated. Order 06 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `aeq7f8`, whose production machinery it reuses.

WHAT THE RUNNER MUST ENFORCE ITSELF, because the setter does not. `aw backlog set --status graduated` is a legal transition from EVERY status, including `done`, so it cannot detect an agent that closed the item itself; the runner therefore refuses to transition unless the item is still `open` and passes that prior status to the LEGITIMACY verifier. The runner also addresses the item by id6 rather than by a path captured at dispatch, because the setter moves the file and a stale path makes the rollback a silent no-op. Both were measured failing on a scratch repo at review; both have tests that fail without the fix.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
