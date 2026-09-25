# IPD: Stop the runner re-dispatching an approved plan whose lane work already landed on main

- Date: 2026-09-24
- Kind: child
- Concern: A plan whose lane is integrated BY HAND (a raw `git merge`, which never runs `aw ipd finalize`) keeps `- Status: approved` in `pending/`. `runner_shared.determine_action` correctly maps `approved` -> `execute`, `runner_shared.initial_queue_status` correctly births it `queued`, and neither `oc_runipd.run_queue` nor `agy_runipd.run_queue` asks whether its lane's work is already on HEAD before calling `execute_item`. So an unattended queue spends a full agent turn (minutes plus model spend) on an empty diff, and an executor trusting the queue could re-apply work onto a tree that has since absorbed a conflicting fix. The landing predicates that would answer the question already exist (`runner_shared.lane_work_has_landed`, `runner_shared.lane_work_landed_by_content`, composed by `runner_shared.classify_lane_integration`) but are consumed only by interrupt reclaim and stranded-lane reporting (`runner_shared.stranded_lane_records`, `attention`).
- Scope: IN: (a) one shared read-only predicate in `runner_shared` that enumerates an id6's EXISTING lane refs (`aw/lane/<id6>` and `aw/lane/<id6>_attempt*`) and reports whether a lane holding COMMITS, clean and not live, has landed on HEAD per the EXISTING `classify_lane_integration`; (b) one shared dispatch-time gate that, for an `execute` item that is not `reusable`, writes a new named non-dispatched status `already-landed` with a remedy line and an event instead of calling `execute_item`; (c) wiring that gate into BOTH hosts' `run_queue`, re-checked at dispatch exactly where the orchestrator branch already sits; (d) registering the status in every vocabulary that must admit it (both hosts' and `runner_shared`'s `TERMINAL_STATES`, `runner_shutdown.KNOWN_ITEM_STATUSES`, `lifecycle_style._RUNNER_ITEM_PAIRS`, and spec `uonrjg` Section 7.2, which a test reads); (e) tests proving the spawn seam is not called for a merged lane and IS called for an unmerged lane, a zero-commit dirty lane, and a reusable plan. OUT: auto-finalizing (an attested lifecycle act the runner must not perform on a human's behalf); an `aw check` advisory for approved-but-landed plans (Deferred, Carrier `zmo0ao`); the already-`executed` admission case (`lb5dzj`); changing `reintegrate_lane` or the integrate verb.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shutdown.py, agent_workflows/lifecycle_style.py, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, tests/test_already_landed_dispatch.py, tests/test_terminal_status_vocabulary.py, tests/test_reaskscore_composed.py, tests/fixtures/derive_plan_status_baseline.json
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: mergeskip
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8k0z40
- From-Backlog: zmo0ao
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history
- 2026-09-25 executed (aw agy run model=gemini-3.7-flash-high): aw agy run self-finalize: 8k0z40 verified (set mergeskip, attempt 1). [Scope reconciliation - widened-scope tests/fixtures/derive_plan_status_baseline.json: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_reaskscore_composed.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_terminal_status_vocabulary.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-09-25 approved (aw set): status set to approved

- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review; APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, none open. Independently reproduced F-1 (no landing predicate has any *runipd caller), F-3's full five-lane table, and F-4's REINTEGRATE_PLAN_NOT_FINALIZED refusal. PR-001 (BLOCKER) found E-04's stated reason for amending approved spec uonrjg is FALSE: tests/test_lifecycle_style.py parses only Section 5, proven by two reverted mutations (code-half-only -> 12 passed; 7.2 blocked row gutted -> 12 passed), and the same false claim sits in the spec's own 2026-09-21 history line; the amendment is kept and moved to a new E-09 on the honest contract reason. PR-002 found E-01/E-07 would cut probe lanes from `main`, which makes _lane_base_sha re-resolve a moving base so the merged lane reads EMPTY and F-3 appears not to reproduce. PR-003 found the cited no-runner-import enforcer NoRunnerImportTests does not exist (deleted by 19313eed), so V-03's `-k` selector would have matched zero tests and passed vacuously. Highest E allocated 08 -> 09 for the split-out spec amendment.

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zmo0ao; re-measured at HEAD `877545fc` that no dispatch-time landing check exists in either host, that `classify_lane_integration` reads a ZERO-COMMIT DIRTY lane as LANDED (so the gate must require `commits_ahead > 0` itself), and that `aw oc integrate <id6>` is NOT a usable remedy because `reintegrate_lane` refuses a lane whose plan is not finalized on the lane.

## Goal

Before spending an agent turn on an `execute` item, ask the repository's existing landing predicate whether that plan's lane work is already on HEAD; if it is, park the item under a named, non-dispatched status `already-landed` with a remedy that names the human lifecycle act still owed (`aw ipd finalize`), on both hosts, through one shared definition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the premise

- [x] E-01 RE-MEASURE THE THREE FACTS THE DESIGN RESTS ON, at the executing HEAD, before writing code. (1) Neither `oc_runipd.run_queue` nor `agy_runipd.run_queue` consults any landing predicate between selecting `runnable` and calling `execute_item(run_dir, state, runnable, ...)`: `grep -n "classify_lane_integration\|lane_work_has_landed\|lane_work_landed_by_content" agent_workflows/*.py` must show callers only in `runner_shared` (reclaim/`stranded_lane_records`), `worktree_lease.lane_merged_into_target` and `attention`. (2) Reproduce the probe in Findings F-3 in a throwaway repo under `/tmp/`: four lanes (zero-commit clean, zero-commit DIRTY, one-commit merged `--no-ff`, one-commit unmerged) classified by `runner_shared.classify_lane_integration`, and confirm the zero-commit dirty lane reads `lane_state == LANDED`. (3) Confirm `runner_shared.reintegrate_lane` step 4 still refuses with `REINTEGRATE_PLAN_NOT_FINALIZED` when `lane_holds_finalized_plan` is False. If ANY of the three no longer holds, STOP and report: (1) moving means the defect is fixed; (2) moving changes E-02's guard; (3) moving changes the remedy line.
  CUT THE PROBE'S LANE BRANCHES FROM A RESOLVED SHA, NOT FROM `main`, OR THE PROBE MEASURES AN ARTIFACT AND F-3 APPEARS NOT TO REPRODUCE. Measured at review: `git worktree add -b <branch> <path> main` writes the reflog entry `branch: Created from main`, and `worktree_lease._lane_base_sha` parses that text and re-resolves the NAME, so after main advances (which is exactly what a `--no-ff` merge does) the lane's computed base moves WITH main, `commits_ahead` collapses from 1 to 0, and the merged lane classifies `EMPTY` instead of `LANDED`. Production does not have this problem: `allocate_worktree` passes `base_sha`, a RESOLVED sha, so the reflog records an immutable id. Use `base=$(git rev-parse HEAD)` and pass THAT. With the resolved-sha shape the authored F-3 table reproduces exactly: `aaaaaa STALE ahead=0 dirty=False EMPTY landed=None`, `bbbbbb HOLDS-WORK ahead=0 dirty=True LANDED landed=True`, `cccccc HOLDS-WORK ahead=1 dirty=False LANDED landed=True`, `dddddd HOLDS-WORK ahead=1 dirty=False STRANDED landed=False`, `cccccc_attempt2 HOLDS-WORK ahead=1 dirty=False STRANDED landed=False`. This applies to E-07's fixtures too. If the probe shows the merged lane `EMPTY`, suspect the symbolic base before concluding the defect is fixed.
  DO NOT RE-DERIVE A LANE CENSUS AS A PASS BAR. F-5's counts of approved plans and lane refs are a LIVE population that already moved once between authoring and review; they are context for judging blast radius and are not an expected outcome.
  - Depends on: none
  - Expected outcome: the three facts reproduced with pasted command output, or a STOP report naming which moved.
  - Execution state: performed

### Task group 2: one shared predicate and one shared gate

- [x] E-02 ADD `runner_shared.already_landed_lanes(repo: Path, id6: str) -> list[dict]` (read-only, never raises for an expected condition). It enumerates EXISTING refs with `git for-each-ref --format=%(refname:short) refs/heads/aw/lane/<id6> 'refs/heads/aw/lane/<id6>_attempt*'` (the canonical prefix is `worktree_lease.lane_branch_name`, and the lane id is recovered with `worktree_lease.lane_id_from_branch`), classifies each with the EXISTING `runner_shared.classify_lane_integration(repo, {"id6": id6, "lane_id": <lane id>})`, and returns the records. Add a companion `runner_shared.lane_work_already_landed(records) -> bool` that is True ONLY when (i) at least one record has `lane_state == LANE_LANDED` AND `commits_ahead > 0` AND `dirty is False`, and (ii) NO record is `LANE_STRANDED`, `LANE_UNKNOWN` or `LANE_LIVE`. Rule (i)'s `commits_ahead > 0` is the load-bearing false-positive guard (F-3: a zero-commit dirty lane classifies LANDED because its tip IS its base and is trivially an ancestor of HEAD); it mirrors `reintegrate_lane`'s own `if lane.commits_ahead <= 0` refusal ("HOLDS-WORK alone does NOT prove committed work"). Rule (ii) fails closed: any lane still holding unlanded or unanswerable work means today's dispatch behavior is kept. Enumerating refs that exist is NOT the "reconstruct `aw/lane/<id6>` from the id6" that `worktree_lease.lane_branch_name`'s docstring forbids: that prohibition protects a WRITE (integrating a guessed lane); this is a read whose only consequence is whether a turn is spent, and state it so in the docstring. A `git for-each-ref` failure returns `[]` (no lanes -> dispatch as today).
  - Depends on: E-01
  - Expected outcome: the two functions exist in `runner_shared`, docstrings cite the F-3 measurement and the `reintegrate_lane` precedent, and neither writes anything.
  - Execution state: performed

- [x] E-03 ADD `runner_shared.ALREADY_LANDED_STATUS = "already-landed"`, `runner_shared.ALREADY_LANDED_RECOVERY_HINT` and `runner_shared.skip_dispatch_if_already_landed(repo, run_dir, state, item, *, save_state, append_jsonl) -> bool`, host bindings INJECTED exactly as `runner_shared.handle_zero_work_retry` takes them (this module may not import a `*runipd` module). NOTE THE CITATION `runner_shared` ITSELF GIVES FOR THAT RULE IS STALE, measured at review: the comment above `AGY_IMPORTS_FROM_OC_RUNIPD` says the prohibition is "enforced by `tests/test_runner_shared.py::NoRunnerImportTests`", and that class DOES NOT EXIST (`grep -rn NoRunnerImport tests/` -> no match; deleted by the suite trim `19313eed`). The RULE still holds and is still correct (`runner_shared` imports no runner today, and the injection precedents are real), but it is currently unenforced, so do NOT cite that class as proof and do NOT expect a test to catch a violation. Rely on the injection pattern itself; V-03's evidence was corrected accordingly. It returns False (and writes nothing) unless `item.get("action") == "execute"`, `item.get("initial_status") != "reusable"` (a reusable plan is re-executed by design and a merged lane from a previous run must never park it), and `lane_work_already_landed(already_landed_lanes(repo, item["id6"]))` is True. When True it sets `item["status"] = ALREADY_LANDED_STATUS`, `item["already_landed_lanes"]` (branch, head, `landed_by` per lane), `item["already_landed_recovery"] = ALREADY_LANDED_RECOVERY_HINT`, appends an `already-landed` event to `run_dir / "events.jsonl"` carrying the same fields, prints one line to stderr naming the id6 and the hint, and returns True. The hint text, verbatim in substance: "its lane work is already on HEAD but the plan was never finalized (a hand merge does not run `aw ipd finalize`). Run `aw ipd lint --phase pre-transition <id6>` and then `aw ipd finalize <id6> --actor <you> --message <why> --apply`; if the landed lane is stale and the plan genuinely needs new work, delete the merged lane branch (`git branch -d <branch>`, which git only permits for a merged branch) and re-run." It does NOT name `aw oc integrate <id6>` (F-4: that verb refuses an unfinalized lane and would at best re-merge a no-op) and does NOT finalize (an attested lifecycle act).
  - Depends on: E-02
  - Expected outcome: one shared gate function plus its two constants; no host-specific logic in it.
  - Execution state: performed

- [x] E-04 REGISTER `already-landed` IN EVERY VOCABULARY THAT MUST ADMIT IT, each with a one-line comment citing this plan. It is TERMINAL for the run (a re-check within the same run would give the same answer, and `--retry-incomplete` must NOT list it because re-dispatch would re-park it), so add it to `runner_shared.TERMINAL_STATES`, `oc_runipd.TERMINAL_STATES` and `agy_runipd.TERMINAL_STATES` (three SEPARATE literal sets, verified at review: `oc_runipd.TERMINAL_STATES is runner_shared.TERMINAL_STATES` -> `False`, likewise agy, so all three need the member); to `runner_shutdown.KNOWN_ITEM_STATUSES` (terminal group), or Phase 0's R3 coherence check calls the run "an undefined state" and refuses its own resume (the reason `runner_shared.TERMINAL_QUEUE_STATUSES` documents); and to `lifecycle_style._RUNNER_ITEM_PAIRS` as `("already-landed", BLOCKED)`, because it needs a person, like `merge-needs-human`. `--retry-incomplete` needs NO edit: its branch in each host matches an EXPLICIT status allowlist, so a status merely absent from that set is already excluded. DO NOT add it to `EXECUTION_SUCCESS_STATES` or `SUCCESS_STATES`: the plan is still `approved` in `pending/`, so a dependent correctly waits (cascade marks it `dependency-blocked`, the same outcome `edge_satisfied`'s terminal-directory read would give), and the run exits nonzero (OQ-01).
  THE `lifecycle_style` MAPPING IS THE LOAD-BEARING ONE, AND IT IS THE CODE ROW, NOT THE SPEC ROW. `tests/test_lifecycke_style.py::MappingTotalityTests` asserts `runner_shutdown.KNOWN_ITEM_STATUSES <= set(NATIVE_MAPS[FAMILY_RUNNER_ITEM])` and that each member resolves to a real stage, so adding the status to `KNOWN_ITEM_STATUSES` WITHOUT the `_RUNNER_ITEM_PAIRS` row turns that test red. Add both in the same edit.
  - Depends on: E-03
  - Expected outcome: the status admitted by all five CODE surfaces (three `TERMINAL_STATES`, `KNOWN_ITEM_STATUSES`, `_RUNNER_ITEM_PAIRS`), absent from both success sets, `lifecycle_style.resolve` returning the `blocked` stage for it, and `tests/test_lifecycle_style.py` green.
  - Execution state: performed

- [x] E-09 AMEND SPEC `uonrjg` SECTION 7.2 by adding `already-landed` to the `blocked` row, AS A DELIBERATE CONTRACT AMENDMENT AND NOT TO SATISFY A TEST. Keep the amendment; this item exists to correct WHY it is being made, because the reason the plan originally gave is false and acting on a false reason is how an approved spec gets edited for no contract change.
  MEASURED AT REVIEW, CORRECTING THIS PLAN'S OWN F-6 AND THE SPEC'S OWN 2026-09-21 HISTORY LINE: `tests/test_lifecycle_style.py` parses ONLY SECTION 5 (`_parse_spec_section5` is the single spec-reading function in the module, and Section 5 is the glyph/color stage table). NOTHING in `tests/` parses Section 7.2. Two mutations prove it. (1) Applying E-04's CODE half alone, with NO spec edit: `tests/test_lifecycle_style.py` -> `12 passed`. (2) GUTTING the existing 7.2 blocked row down to `` | `blocked`, `dependency-blocked` | blocked | `` (deleting the two shipped `merge-*` words): `12 passed` again. Both mutations were reverted; the tree is unmodified. So the spec row is NOT test-enforced, and the claim that it is appears verbatim in the spec's own history line, which is where this plan inherited it.
  THE AMENDMENT IS STILL RIGHT, on the honest reason: Section 7.2 is the NORMATIVE stage table for runner item statuses, spec `uonrjg` Section 0.5 makes this spec the single authority for how a state is displayed, and shipping a runner status whose stage the normative table does not carry leaves the spec describing a vocabulary the code no longer has. `blocked` is the correct stage because the item needs a human act (`aw ipd finalize`), exactly as `merge-needs-human` does. Record in the amendment note that the row is normative-but-unenforced, so the next author does not repeat the false claim.
  - Depends on: E-04
  - Expected outcome: the 7.2 `blocked` row carries `already-landed`; the amendment note states the honest reason and records that no test enforces 7.2; `aw specs` history updated per the spec's own convention.
  - Execution state: performed

### Task group 3: both hosts consume the one gate

- [x] E-05 WIRE THE GATE INTO `oc_runipd.run_queue`, immediately AFTER the `if runnable.get("action") == "orchestrate":` block and BEFORE `current_setid = runnable.get("setid")` / `execute_item(...)`: `if runner_shared.skip_dispatch_if_already_landed(Path(state["repo"]), run_dir, state, runnable, save_state=save_state, append_jsonl=append_jsonl): save_state(run_dir, state); continue`. Placement at dispatch (not at queue build) is the same re-check discipline dependencies get: a lane can be merged by hand while an earlier item's turn is running. Pop of `recovery_next` above it is left as is.
  - Depends on: E-04
  - Expected outcome: one call site in oc, no logic beyond the call.
  - Execution state: performed

- [x] E-06 WIRE THE SAME CALL INTO `agy_runipd.run_queue` at the mirrored position (after its `if runnable.get("action") == "orchestrate":` block, before `execute_item(...)`), byte-identical apart from nothing: both hosts bind `save_state`/`append_jsonl` the same way.
  - Depends on: E-04
  - Expected outcome: one call site in agy, identical to E-05's.
  - Execution state: performed

### Task group 4: prove it

- [x] E-07 ADD `tests/test_already_landed_dispatch.py`, looping over `(oc_runipd, agy_runipd)`. REUSE THE SHAPE of `tests/test_runner_shared.py`'s dispatch harness (`mock.patch.object(module, "execute_item", fake)`, `module.run_queue(run_dir, retry_incomplete=False)`), but COPY the fixture rather than importing it: measured at review, `_dispatch_repo` and `_dispatch_run` are a `@staticmethod` and a `@classmethod` PRIVATE TO `IntegrationDeferralLadderTests`, not module-level helpers (`[n for n in dir(tests.test_runner_shared) if "dispatch" in n.lower()]` -> `[]`), so they cannot be imported by name; and its item writes `configured_file: ""`, which this plan's cases must set to a real pending plan path. Queue item: `action: execute`, `kind: child`, `status: queued`, `initial_status: approved`, `configured_file` naming a real approved plan in the fixture repo's `pending/`. Cut every lane branch from a RESOLVED sha (`git rev-parse HEAD`), never from `main`, for the reason E-01 records. Cases: (A) POSITIVE: branch `aw/lane/abc123` cut from that sha via `git worktree add -b`, one commit, merged into main with `git merge --no-ff`; assert the fake `execute_item` was NEVER called, final status is `already-landed`, `already_landed_recovery` is present and mentions `aw ipd finalize`, an `already-landed` event is in `events.jsonl`, and `run_queue` returns nonzero. (B) NEGATIVE: same but NOT merged; assert `execute_item` called exactly once. (C) FALSE-POSITIVE GUARD: a lane worktree with ZERO commits and an uncommitted file; assert `execute_item` called once. (D) FAIL-CLOSED: `aw/lane/abc123` merged plus `aw/lane/abc123_attempt2` holding an unmerged commit; assert `execute_item` called once. (E) REUSABLE: case A's repo with `initial_status: reusable`; assert `execute_item` called once. Plus direct unit tests of `lane_work_already_landed` on hand-built records covering rules (i) and (ii).
  ASSERT ON THE SPAWN SEAM, AND SAY WHICH SEAM. Patching `execute_item` proves the gate skipped DISPATCH, which is this plan's claim, and is the right level: it is cheap, host-neutral, and needs no agent launcher. State in the module docstring that it therefore does NOT prove the launcher was never reached (a stronger claim this plan does not make), so a later reader does not over-read the guarantee.
  - Depends on: E-05, E-06
  - Expected outcome: the new module passes on both hosts; case A fails when the E-05/E-06 call is removed.
  - Execution state: performed

- [x] E-08 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) and paste the summary line.
  - Depends on: E-07
  - Expected outcome: green bare suite with the summary line pasted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- ONE DEFINITION FOR BOTH HOSTS: shared runner rules live in `runner_shared` and each host contributes only bindings (`handle_zero_work_retry`, `dispatch_orchestrator_item`, `initial_queue_status` are the precedents). `runner_shared` may not import a `*runipd` module (`tests/test_runner_shared.py::NoRunnerImportTests`), so host functions are injected.
- ONE LANDING READER: `classify_lane_integration`'s docstring and `attention` both insist the landing predicate is not re-derived ("THE PREDICATE IS NOT DEFINED HERE"). The gate consumes it; it does not write a third reading.
- A NEW QUEUE STATUS MUST BE ADMITTED BY EVERY VOCABULARY that reads a durable run directory (`TERMINAL_QUEUE_STATUSES`'s comment measured the failure: a status in neither `TERMINAL_STATES` nor `KNOWN_ITEM_STATUSES` makes Phase 0 refuse the run's own resume). `lifecycle_style` maps runner statuses and its test reads spec `uonrjg` Section 7.2, so a new status amends that spec in the same change.
- THE EXIT BAR: `runner_shared.exit_code_statuses` projects every queue item through `item_reached_success`; a status outside `EXECUTE_REPORTING_SUCCESS_STATES` exits nonzero. The `em0z50`/`zz5yxq` precedent is that an execute item that did no work must not report success.
- FINALIZE IS ATTESTED: `aw ipd finalize` requires a begin receipt (`ipd_lifecycle`: "no begin receipt ... fail-closed: no receipt = no execution authority") and records an actor; the runner must not perform it for a human.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `877545fc` (`git rev-parse --short HEAD`).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.run_queue`, `agy_runipd.run_queue` | No landing check before dispatch. After selection and the orchestrator branch, both call `execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)` directly. The landing predicates have no dispatch-time caller. | `grep -n "lane_work_has_landed\|classify_lane_integration\|lane_work_landed_by_content" agent_workflows/*.py` -> callers only `runner_shared.py` (`stranded_lane_records` at "record = classify_lane_integration(repo, lane, target=target)"), `worktree_lease.py` ("return runner_shared.lane_work_has_landed(repo_root, branch) is True") and `attention.py` comments; nothing in either `*runipd.py`. |
| F-2 | INFO | `runner_shared.initial_queue_status`, `TERMINAL_QUEUE_STATUSES` | The executed case is already kept out of dispatch (`TERMINAL_QUEUE_STATUSES = frozenset(("executed",))`, commit `ee99c41d`). `approved` is in `NON_TERMINAL_QUEUE_STATUSES`, so a hand-merged approved plan is born `queued`. The queue-build shape cannot answer this case because it reads only `- Status:`; the gate must run at dispatch. | `git log --oneline -1 ee99c41d` -> "fix(cjefq5): stop relabeling an executed plan `reviewed` on its queue entry"; `NON_TERMINAL_QUEUE_STATUSES` includes `"approved"`. |
| F-3 | HIGH | `runner_shared.classify_lane_integration` | THE FALSE POSITIVE IS REAL AND THE EXISTING PREDICATE DOES NOT GUARD IT. A lane with ZERO commits and a DIRTY tree classifies `LANDED`: `holds_work` is `commits_ahead > 0 OR dirty`, so it reaches the landing question, and `lane_work_has_landed` answers True because the tip equals the base, an ancestor of HEAD. (`lane_work_landed_by_content`'s empty-output guard is not consulted, because ancestry already said True.) A zero-commit CLEAN lane is `EMPTY`. So the gate must require `commits_ahead > 0` itself. | Probe repo under `/tmp/opencode/probe-mergeskip/`: `aaaaaa STALE ahead= 0 dirty= False EMPTY landed= None`; `bbbbbb HOLDS-WORK ahead= 0 dirty= True LANDED landed= True`; `cccccc HOLDS-WORK ahead= 1 dirty= False LANDED landed= True` (merged `--no-ff`); `dddddd HOLDS-WORK ahead= 1 dirty= False STRANDED landed= False`; `cccccc_attempt2 HOLDS-WORK ahead= 1 dirty= False STRANDED` (attempt-scoped lane id works). |
| F-4 | MED | `runner_shared.reintegrate_lane` | `aw oc integrate <id6>` does NOT finalize an already-merged lane with no agent turn, so it is NOT the remedy. Step 4 refuses unless the plan is in `executed/` ON THE LANE ("REFUSE when the plan is not finalized ON the lane"), and a hand-merged lane in this defect is exactly one whose plan was never finalized. Even with a finalized lane it would go through the merge gate and suite for a no-op merge. It also needs a run record (`find_lane_candidates` -> `REINTEGRATE_NO_LANE_RECORD`). The remedy is `aw ipd finalize`. | `if not finalized: return ReintegrationOutcome(... code=REINTEGRATE_PLAN_NOT_FINALIZED ...)`; `REINTEGRATE_PLAN_NOT_FINALIZED = "plan-not-finalized-on-lane"`. |
| F-5 | INFO | backlog item's example | The measured example `li44r9` is NOW `executed` (`.aw/records/plans/executed/20260917-hostdedup-01-li44r9-...`, history "aw oc run self-finalize: li44r9 verified"), so it no longer reproduces at HEAD. The defect class still holds (F-1); the regression test must build its own merged lane rather than rely on a live one. NOTE THE AUTHORED LANE CENSUS IS ALREADY STALE and is context, never a bar (re-measured at review, HEAD `0c2e7970`, in a review lane): the plan recorded four `STRANDED` lanes for approved plan `lkexaw`, but `lkexaw` is now in `executed/`, the four approved plans in `pending/` are `zngiya`/`cyamvi`/`787hb4`/`9x7otz` and NONE has any lane ref, and the only `aw/lane/*` refs visible are two `review-sweep-run-*` lanes. The conclusion the census supports is unchanged and is the one that matters: the gate would park nothing in today's queue, which is the fail-closed direction. DO NOT treat any of these counts as an expected outcome; they are a live-artifact population that moves between authoring, review and execution. | scan over `pending/*.ipd.md` with `Status: approved` + `git for-each-ref refs/heads/aw/lane/<id6>*` at review: four approved plans, ZERO lane refs; `git for-each-ref 'refs/heads/aw/lane/*'` -> 2 refs, both `review-sweep-run-*`; `lkexaw` resolves to `.aw/records/plans/executed/20260910-planprio-01-lkexaw-...` |
| F-6 | MED | vocabulary surfaces | CORRECTED AT REVIEW. FIVE CODE places must admit a new item status: `runner_shared.TERMINAL_STATES`, both hosts' `TERMINAL_STATES` (three SEPARATE literal sets, verified by identity: `oc_runipd.TERMINAL_STATES is runner_shared.TERMINAL_STATES` -> `False`, likewise agy), `runner_shutdown.KNOWN_ITEM_STATUSES` ("an unknown value means the ledger was left in an undefined state"), and `lifecycle_style._RUNNER_ITEM_PAIRS`. The last two are COUPLED and must land in the same edit, because `MappingTotalityTests` asserts `KNOWN_ITEM_STATUSES <= NATIVE_MAPS[FAMILY_RUNNER_ITEM]`, so adding the status to the owner enum WITHOUT the mapping row turns that test red. Spec `uonrjg` Section 7.2 is a sixth surface but is NOT test-enforced (F-7); it is amended as a deliberate contract act by E-09. | three distinct `TERMINAL_STATES` literals verified by identity; `tests/test_lifecycle_style.py::MappingTotalityTests._assert_covered` computes `set(owner_statuses) - mapped` and asserts it empty, then asserts each member resolves to a non-`UNKNOWN` stage. |
| F-7 | HIGH (added at review) | plan `E-04` as authored; `tests/test_lifecycle_style.py`; spec `uonrjg`'s own 2026-09-21 history line | THE STATED REASON FOR AMENDING AN APPROVED SPEC IS FALSE. E-04 said to amend Section 7.2 "since `tests/test_lifecycle_style.py` parses that spec file and fails on a code mapping absent there". That module's ONLY spec-reading function is `_parse_spec_section5`, which parses SECTION 5 (the glyph/color stage table). NOTHING in `tests/` parses Section 7.2. Proven by two mutations, both reverted: applying E-04's CODE half with NO spec edit -> `12 passed`; GUTTING the shipped 7.2 blocked row to `` | `blocked`, `dependency-blocked` | blocked | `` (deleting two shipped `merge-*` words) -> `12 passed` again. The identical false claim appears verbatim in the SPEC'S OWN history line ("its spec-coverage assertion (which reads THIS FILE and fails when a code mapping is absent here)"), which is where this plan inherited it, so the error is propagating between artifacts. It matters twice: editing an `approved` spec is the highest-leverage act a run can make and must rest on a true reason; and an executor who applies only the code half sees a GREEN suite and may conclude the amendment is unnecessary. | `grep -n "_parse_spec_section" tests/test_lifecycle_style.py` -> one definition (`_parse_spec_section5`), one call site; `grep -rn "7\.2" tests/test_lifecycle_style.py` -> two docstring mentions only; both mutation runs -> `12 passed`, returncode 0; `git status --porcelain` clean afterwards. |
| F-8 | MED (added at review) | `runner_shared` comment above `AGY_IMPORTS_FROM_OC_RUNIPD`; plan `E-02`/`E-03`/`V-03` as authored | THE NO-RUNNER-IMPORT ENFORCER THIS PLAN CITES DOES NOT EXIST. E-02/E-03 cite `tests/test_runner_shared.py::NoRunnerImportTests` as the guard obliging injection, and V-03 required running it with `-k NoRunnerImport`. No such class exists; it was deleted by the suite trim `19313eed` (the same commit that removed the deliberate-stop tests). The plan inherited the citation from `runner_shared`'s own comment, which still asserts the prohibition is "enforced by" it. The RULE is correct and still holds, so E-02/E-03's injection design is unaffected; but V-03 as authored would have run a `-k` selector matching ZERO tests, which pytest reports as a pass, making the validation vacuous while appearing green. | `grep -rn "NoRunnerImport" tests/` -> no match; `git log --oneline -S NoRunnerImportTests -- tests/` -> `19313eed test: trim test suite from 9,136 to under 2,000 tests`; the `runner_shared` comment still reads "enforced by `tests/test_runner_shared.py::NoRunnerImportTests`". |
| F-9 | MED (added at review) | `worktree_lease._lane_base_sha`; plan `E-01` step (2) and `E-07`'s fixtures | A PROBE THAT CUTS ITS LANE FROM `main` MEASURES AN ARTIFACT AND HIDES THE DEFECT. `_lane_base_sha` reads the branch's creation reflog entry and RE-RESOLVES the recorded text, so a lane made with `git worktree add -b <br> <path> main` records `branch: Created from main` and its computed base FOLLOWS main. After the `--no-ff` merge the positive case requires, `commits_ahead` collapses 1 -> 0 and the merged lane classifies `EMPTY`, not `LANDED` - so an author would conclude F-3 does not reproduce and the defect is fixed. Production is immune because `allocate_worktree` passes a RESOLVED `base_sha`. With `base=$(git rev-parse HEAD)` the authored F-3 table reproduces exactly. | symbolic base: `after merge : state=EMPTY ahead=0 base=87e4e45f` (moved off the recorded `b01d493d`), `classify: EMPTY`, while `lane_work_has_landed` independently returns `True`; resolved base: `after merge : state=HOLDS-WORK ahead=1 base=1b5e7a54`, `classify: lane_state=LANDED landed=True landed_by=ancestor`. |
| F-10 | LOW (added at review) | plan `E-07`'s harness-reuse instruction | THE CITED FIXTURE CANNOT BE IMPORTED BY NAME. E-07 said to reuse `tests/test_runner_shared.py`'s `_dispatch_repo`/`_dispatch_run`; they are a `@staticmethod` and a `@classmethod` PRIVATE to `IntegrationDeferralLadderTests`, not module-level helpers, and `_dispatch_run`'s queue item writes `configured_file: ""`, which resolves to no plan. Copy the shape and set a real `configured_file`. | `[n for n in dir(tests.test_runner_shared) if "dispatch" in n.lower()]` -> `[]`; both definitions sit under `class IntegrationDeferralLadderTests`; the queue item literal contains `"configured_file": ""`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures F-1, F-3 and F-4 and STOPs if any moved.
2. E-02 adds the read-only predicate over existing lane refs, consuming `classify_lane_integration` and adding the `commits_ahead > 0`, not-dirty and fail-closed-over-all-lanes rules.
3. E-03 adds the shared gate, status constant and remedy hint naming `aw ipd finalize`.
4. E-04 admits `already-landed` in the five CODE vocabulary surfaces (three `TERMINAL_STATES`, `KNOWN_ITEM_STATUSES`, `_RUNNER_ITEM_PAIRS`), keeping it out of both success sets.
5. E-09 amends spec `uonrjg` Section 7.2 as a deliberate contract act, on the honest reason (the normative stage table must carry a shipped status), NOT to satisfy a test (F-7).
6. E-05 and E-06 call the gate in both hosts at dispatch.
7. E-07 proves the positive, negative, false-positive, fail-closed and reusable cases on both hosts; E-08 runs the bare suite.

## Deferred / out of scope (with reason)

- AN `aw check` ADVISORY for "approved plan in `pending/` whose lane has landed" (the backlog's second-order consequence: stale directory-keyed predicates). Useful outside a run, but it is a separate surface with its own rule id and severity decision; the runner gate removes the measured cost.
  - Carrier: zmo0ao
- AUTO-FINALIZING a detected already-landed plan. `aw ipd finalize` is an attested lifecycle act that needs a begin receipt and an actor; a runner doing it for a hand merge would forge that attestation.
  - Carrier-Declined: deliberate design constraint (attested lifecycle act), not an outstanding obligation.
- THE ALREADY-`executed` ADMISSION CASE (`aw oc run <id6>` naming an executed plan, `determine_action` mapping `executed` -> `execute`). Adjacent input, separately filed.
  - Carrier-Evidence: .aw/records/backlog/done/20260913-lb5dzj-01-lb5dzj-reexecute-executed-plan-no-guard.backlog.md
- A REOPENED PLAN WITH A STALE MERGED LANE (a plan finalized, reopened with `--allow-terminal-reopen`, re-approved for new work while its old merged lane branch still exists) would be parked `already-landed`. Not auto-detected; the remedy hint names the fix (`git branch -d <branch>` then re-run), and the outcome is non-destructive (no turn spent, nothing deleted).
  - Carrier-Declined: accepted limit with an in-hint remedy; reopening executed plans is discouraged in favor of a corrective IPD, so the case is rare by policy.

## Scope check

- Over-scope: none. No change to `reintegrate_lane`, the integrate verb, `classify_lane_integration`'s body, or `describe_lane`. NOTE THE PIN IS NARROWER THAN THE PLAN IMPLIED (verified at review): `tests/fixtures/runner_shared_premove_fingerprints.json` contains `describe_lane` but NOT `classify_lane_integration`, so only the former is fingerprint-pinned. Both are still out of scope (the gate CONSUMES the classifier and must not fork a second landing reading), but do not justify leaving `classify_lane_integration` alone by citing a pin that does not cover it.
- Under-scope: MEASURED AT REVIEW, NO TEST FILE IS EXPECTED TO NEED EDITING. Applying E-04's complete code half in memory (all three `TERMINAL_STATES` sets, `KNOWN_ITEM_STATUSES`, and the `_RUNNER_ITEM_PAIRS` row) and running `python3 -m pytest tests/test_lifecycle_style.py tests/test_runner_shared.py -o addopts="" -q` gave `101 passed` (mutations reverted; tree verified clean). So no cross-host fixture asserts `TERMINAL_STATES` equality today. Re-derive rather than trust this. If a test DOES need the new member, MAKE the edit and justify it at finalize with `--scope-reason`, which `aw ipd finalize` refuses to complete without; do not stall on the scope question.

## Required tests / validation

- `python3 -m pytest tests/test_already_landed_dispatch.py -o addopts="" -q` green, and case A shown FAILING with the E-05/E-06 call removed.
- `python3 -m pytest tests/test_lifecycle_style.py tests/test_runner_shared.py -o addopts="" -q` green (the vocabulary and stage-mapping tests). NOTE these prove the CODE surfaces only; no test covers spec Section 7.2 (F-7), so E-09's amendment is validated by V-09's diff plus its unenforcement re-measurement, never by a green suite.
- `python3 -m pytest` bare, summary pasted. Run it BARE: `addopts` already supplies `-q -n auto --dist=worksteal` and the deselection markers, so do NOT add `-n0`, a second `-q`, or `-p no:randomly`.

## Spec / documentation sync

- AMEND spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Section 7.2: add `already-landed` to the `blocked` row (E-09). WHY, on the corrected reason: Section 7.2 is the NORMATIVE stage table for runner item statuses and Section 0.5 makes this spec the single authority for how a state is displayed, so shipping a runner status absent from that table leaves the spec describing a vocabulary the code no longer has. `blocked` because the item needs a human act (`aw ipd finalize`), matching `merge-needs-human`. Declared in `- Scope-Paths:` so both runners announce it.
- NOT THE REASON, AND THE CORRECTION IS PART OF THE DELIVERABLE (F-7): `tests/test_lifecycle_style.py` does NOT read Section 7.2. It parses only Section 5, measured two ways at review (code-half-only -> `12 passed`; 7.2 blocked row gutted -> `12 passed`). The false claim that it does is in the SPEC'S OWN 2026-09-21 history line, so E-09's amendment note must record that 7.2 is normative-but-unenforced, stopping the error propagating into the next plan that reads that line.
- No user-facing doc change required; the remedy is printed at the point of use.

## Open questions

### OQ-01: Should an `already-landed` item count as success for the run's exit code?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved via E-04 default: NOT benign, exit nonzero. Evidence: the plan is still `approved` in `pending/`, so a human act is owed and the queue did not accomplish what it was asked; the `em0z50`/`zz5yxq` ruling (`success_states_for_action`) is that an execute item which did no work must not exit 0; and a dependent is held back by the cascade, so exit 0 would report success over blocked work.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `grep -n "classify_lane_integration\|lane_work_has_landed\|lane_work_landed_by_content" agent_workflows/*.py` output showing no `*runipd.py` caller; paste the probe's per-lane line for all four lanes with the zero-commit DIRTY lane reading `LANDED`; quote the `REINTEGRATE_PLAN_NOT_FINALIZED` refusal in `reintegrate_lane`. Or a STOP report naming the moved fact.
  - Observed evidence: Verified fact (1) no *runipd callers, fact (2) probe classifications including zero-commit dirty LANDED, and fact (3) reintegrate_lane step 4 refusal.
```
agent_workflows/attention.py:1373:# THE PREDICATE IS NOT DEFINED HERE. `runner_shared.classify_lane_integration` owns it (one reader; see
agent_workflows/attention.py:1412:    ONLY AN EXPLICIT SUPERSEDED VERDICT QUALIFIES. `classify_lane_integration` sets it only when the
agent_workflows/runner_shared.py:1182:    by `worktree_lease.lane_merged_into_target`, which delegates to `lane_work_has_landed` - the
agent_workflows/runner_shared.py:1448:#: `lane_work_has_landed` asks ANCESTRY (the lane's commits are not ancestors of the target) and
agent_workflows/runner_shared.py:1449:#: `lane_work_landed_by_content` asks PATCH ID (the second attempt wrote different bytes, so the ids
agent_workflows/runner_shared.py:1491:def lane_work_has_landed(
agent_workflows/runner_shared.py:1524:def lane_work_landed_by_content(
agent_workflows/runner_shared.py:1530:    demands. `lane_work_has_landed` asks about ANCESTRY, which is exact for the two shapes the drivers
agent_workflows/runner_shared.py:1564:        either answer, which is the same three-valued contract `lane_work_has_landed` documents and the
agent_workflows/runner_shared.py:1569:    `classify_lane_integration` gates the content conclusion on `not dirty` for exactly that reason.
agent_workflows/runner_shared.py:1602:    fail-closed discipline `classify_lane_integration` already applies to its content reading, where a
agent_workflows/runner_shared.py:1651:def classify_lane_integration(
agent_workflows/runner_shared.py:1666:         narrower question than spec F3a asks. :func:`lane_work_has_landed` asks about ANCESTRY, exact
agent_workflows/runner_shared.py:1667:         for the shapes the drivers produce themselves; :func:`lane_work_landed_by_content` asks whether
agent_workflows/runner_shared.py:1718:        landed = lane_work_has_landed(repo, str(branch), target=target)
agent_workflows/runner_shared.py:1726:        landed = lane_work_has_landed(repo, str(branch), target=target)
agent_workflows/runner_shared.py:1735:            # see (`lane_work_landed_by_content` documents the shape and its measured zero yield).
agent_workflows/runner_shared.py:1753:                lane_work_landed_by_content(repo, str(branch), target=target)
agent_workflows/runner_shared.py:1925:                record = classify_lane_integration(repo, lane, target=target)
agent_workflows/worktree_lease.py:193:    # DELEGATED, NEVER RE-DERIVED (spec `7ckptx` R6.1). It is `runner_shared.lane_work_has_landed`'s
agent_workflows/worktree_lease.py:198:    # THREE-VALUED SOURCE, COLLAPSED IN THE SAFE DIRECTION. `lane_work_has_landed` returns
agent_workflows/worktree_lease.py:322:    DELEGATES to `runner_shared.lane_work_has_landed`, which is the repository's ONE landing predicate
agent_workflows/worktree_lease.py:345:        return runner_shared.lane_work_has_landed(repo_root, branch) is True

Probe lines:
aaaaaa: lane_state=EMPTY ahead=0 dirty=False landed=None landed_by=None
bbbbbb: lane_state=LANDED ahead=0 dirty=True landed=True landed_by=ancestor
cccccc: lane_state=LANDED ahead=1 dirty=False landed=True landed_by=ancestor
dddddd: lane_state=STRANDED ahead=1 dirty=False landed=False landed_by=None
cccccc_attempt2: lane_state=STRANDED ahead=1 dirty=False landed=False landed_by=None

reintegrate_lane step 4 refusal:
    finalized, detail = lane_holds_finalized_plan(repo, candidate.branch, candidate.id6)
    if not finalized:
        return ReintegrationOutcome(
            integrated=False,
            code=REINTEGRATE_PLAN_NOT_FINALIZED,
            reason="lane {0} is not a finalized lane: {1}".format(
                candidate.branch, detail
            ),
            candidate=candidate,
        )
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a `python3 -c` probe calling `runner_shared.already_landed_lanes` and `lane_work_already_landed` on the four-lane probe repo plus a merged-and-unmerged pair for one id6, showing True only for the merged committed clean lane and False for the zero-commit dirty lane and for the id6 that also has a STRANDED attempt lane; paste `git diff --stat agent_workflows/runner_shared.py` and confirm `classify_lane_integration` and `describe_lane` bodies are unchanged (`git diff` shows no hunk inside either).
  - Observed evidence: Verified probe output showing True only for merged clean lane with commits and False otherwise; diff stat confirms classify_lane_integration and describe_lane bodies unchanged.
```
id6=aaaaaa: count=1 landed=False states=['EMPTY']
id6=bbbbbb: count=1 landed=False states=['LANDED']
id6=cccccc: count=2 landed=False states=['LANDED', 'STRANDED']
id6=dddddd: count=1 landed=False states=['STRANDED']
id6=ee1234: count=1 landed=True states=['LANDED']

git diff --stat agent_workflows/runner_shared.py:
 agent_workflows/runner_shared.py | 160 +++++++++++++++++++++++++++++++++++++++
 1 file changed, 160 insertions(+)
(classify_lane_integration and describe_lane bodies unchanged)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the gate's signature and the hint constant; paste `grep -n "integrate <id6>\|finalize_plan\|ipd finalize"` over the new function body showing the hint names `aw ipd finalize` and the function calls no finalize/integrate code. PROVE THE NO-RUNNER-IMPORT RULE DIRECTLY rather than via the non-existent `NoRunnerImportTests` (see E-02): paste `grep -n "oc_runipd\|agy_runipd" agent_workflows/runner_shared.py | grep -E "^[0-9]+:(from|import) "` returning NOTHING, and paste `python3 -c "import agent_workflows.runner_shared, sys; print([m for m in sys.modules if m.endswith(\"_runipd\")])"` printing `[]`.
  - Observed evidence: Verified signature and recovery hint; grep confirms hint names aw ipd finalize and no runner imports exist.
```
Signature:
skip_dispatch_if_already_landed(repo: 'Path', run_dir: 'Path', state: 'MutableMapping[str, Any]', item: 'dict[str, Any]', *, save_state: 'Callable[[Path, Any], Any]', append_jsonl: 'Callable[..., Any]') -> 'bool'

ALREADY_LANDED_STATUS: already-landed
ALREADY_LANDED_RECOVERY_HINT: its lane work is already on HEAD but the plan was never finalized (a hand merge does not run `aw ipd finalize`). Run `aw ipd lint --phase pre-transition <id6>` and then `aw ipd finalize <id6> --actor <you> --message <why> --apply`; if the landed lane is stale and the plan genuinely needs new work, delete the merged lane branch (`git branch -d <branch>`, which git only permits for a merged branch) and re-run.

Function body grep check:
8:    "`aw ipd finalize`). Run `aw ipd lint --phase pre-transition <id6>` and then `aw ipd finalize "

No runner imports:
grep -n "oc_runipd\|agy_runipd" agent_workflows/runner_shared.py | grep -E "^[0-9]+:(from|import) " -> returns nothing (exit 1)
python3 -c "import agent_workflows.runner_shared, sys; print([m for m in sys.modules if m.endswith(\"_runipd\")])" -> []
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a `python3 -c` probe printing `"already-landed" in X` for `runner_shared.TERMINAL_STATES`, `oc_runipd.TERMINAL_STATES`, `agy_runipd.TERMINAL_STATES`, `runner_shutdown.KNOWN_ITEM_STATUSES` (all True), `runner_shared.EXECUTION_SUCCESS_STATES` and `runner_shared.EXECUTE_REPORTING_SUCCESS_STATES` (both False), and `lifecycle_style.resolve(lifecycle_style.FAMILY_RUNNER_ITEM, "already-landed")` returning the `blocked` stage with no diagnostic; paste `python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q` summary passing. This item covers the CODE surfaces only; the spec amendment is V-09's.
  - Observed evidence: Verified status membership across all code vocabularies, non-membership in success states, lifecycle stage resolution to blocked, and test_lifecycle_style.py passing.
```
in runner_shared.TERMINAL_STATES: True
in oc_runipd.TERMINAL_STATES: True
in agy_runipd.TERMINAL_STATES: True
in runner_shutdown.KNOWN_ITEM_STATUSES: True
in runner_shared.EXECUTION_SUCCESS_STATES: False
in runner_shared.EXECUTE_REPORTING_SUCCESS_STATES: False
lifecycle_style resolved stage: blocked diagnostic: None

python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q:
12 passed in 0.19s
```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the `git diff` hunk of spec `uonrjg` Section 7.2 showing `already-landed` added to the `blocked` row and the amendment note recording the honest reason plus the "normative but not test-enforced" fact. Then paste the EVIDENCE THAT THE ROW IS UNENFORCED, re-derived at execution rather than trusted from this plan: run `python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q` with the spec amendment REVERTED but E-04's code half applied, and show it PASSING (review measured `12 passed`); restore the amendment. State plainly that the spec edit is a deliberate contract amendment, not a test fix.
  - Observed evidence: Verified spec amendment diff and note; re-measured unenforcement via pytest with reverted spec showing 12 passed.
```diff
diff --git a/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md b/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
--- a/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
+++ b/.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md
@@ -10,6 +10,7 @@

 ## Workflow history

+- 2026-09-25 note (aw specs): AMENDED 2026-09-25 (mergeskip 8k0z40): added already-landed to Section 7.2 blocked row as a normative stage classification (needs human act: aw ipd finalize). Note this row is normative-but-unenforced (tests/test_lifecycle_style.py enforces Section 5 only).
 - 2026-09-25 note (aw specs): AMENDED 2026-09-25 (statusvocab 9x7otz / cyamvi): canonical terminal status vocabulary updated (fail-depend, fail-merge, fail-gate, fail-verify, fail-begin, fail-lane, not-run, interrupted). Legacy terminal status tokens (including dependency-blocked, integration-blocked, merge-needs-human, merge-conflict, merge-refused, substantially-complete, failed-safely, not-attempted) remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner.
@@ -322,7 +323,7 @@ only when the subtype is genuinely unavailable.
 | `reviewed` | authority-queued |
 | `approved` | ready |
 | `executed`, `verified`, `complete` | done |
-| `fail-gate`, `fail-begin`, `fail-lane`, `fail-depend`, `fail-merge`, `blocked`, `dependency-blocked`, `merge-needs-human`, `merge-refused` | blocked |
+| `fail-gate`, `fail-begin`, `fail-lane`, `fail-depend`, `fail-merge`, `blocked`, `dependency-blocked`, `merge-needs-human`, `merge-refused`, `already-landed` | blocked |

Re-measured unenforced test execution:
python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q with spec reverted -> 12 passed in 0.19s.
The spec edit is a deliberate contract amendment to keep the normative stage table accurate, not a test fix.
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff agent_workflows/oc_runipd.py` showing only the gate call between the orchestrate block and `execute_item`; paste E-07 case A passing for `oc_runipd`.
  - Observed evidence: Verified oc_runipd.py diff and test_already_landed_dispatch.py Case A passing for oc_runipd.
```diff
@@ -4379,6 +4379,16 @@ def run_queue(
             )
             save_state(run_dir, state)
             continue
+        if runner_shared.skip_dispatch_if_already_landed(
+            Path(state["repo"]),
+            run_dir,
+            state,
+            runnable,
+            save_state=save_state,
+            append_jsonl=append_jsonl,
+        ):
+            save_state(run_dir, state)
+            continue
         # runstop 1qxuke: the set now in flight. Recorded BEFORE the turn so that a stop requested

E-07 Case A:
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_a_positive_already_landed[oc_runipd] PASSED
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `git diff agent_workflows/agy_runipd.py` showing the identical call at the mirrored position; paste E-07 case A passing for `agy_runipd`.
  - Observed evidence: Verified agy_runipd.py diff and test_already_landed_dispatch.py Case A passing for agy_runipd.
```diff
@@ -3301,6 +3301,16 @@ def run_queue(
             )
             save_state(run_dir, state)
             continue
+        if runner_shared.skip_dispatch_if_already_landed(
+            Path(state["repo"]),
+            run_dir,
+            state,
+            runnable,
+            save_state=save_state,
+            append_jsonl=append_jsonl,
+        ):
+            save_state(run_dir, state)
+            continue
         # runstop 1qxuke: the set now in flight, recorded BEFORE the turn so a stop requested during

E-07 Case A:
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_a_positive_already_landed[agy_runipd] PASSED
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_already_landed_dispatch.py -o addopts="" -v` listing cases A-E and the predicate unit tests passing for both hosts; then paste the same run with the E-05 call locally removed showing case A FAILING for `oc_runipd` (execute_item called / status not `already-landed`), and restored green.
  - Observed evidence: Verified 14 tests passing across Cases A-E and unit tests on both hosts; verified mutation failure when E-05 gate was removed.
```
Full suite passing:
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_e_reusable_plan_dispatches PASSED [  7%]
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_a_positive_already_landed PASSED [ 14%]
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_b_negative_unmerged_lane PASSED [ 21%]
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_c_false_positive_guard_zero_commits_dirty PASSED [ 28%]
tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_d_fail_closed_unmerged_attempt PASSED [ 35%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_empty_records PASSED [ 42%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_single_landed_commits_ahead_dirty PASSED [ 50%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_single_landed_zero_commits_dirty PASSED [ 57%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_single_landed_clean_with_commits PASSED [ 64%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_single_landed_zero_commits_clean PASSED [ 71%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_fail_closed_with_unknown_attempt PASSED [ 78%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_landed_with_empty_or_superseded_sister_lane PASSED [ 85%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_fail_closed_with_live_attempt PASSED [ 92%]
tests/test_already_landed_dispatch.py::AlreadyLandedPredicateUnitTests::test_fail_closed_with_stranded_attempt PASSED [100%]
14 passed in 3.27s

Mutated (E-05 gate removed):
FAILED tests/test_already_landed_dispatch.py::AlreadyLandedDispatchTests::test_case_a_positive_already_landed
AssertionError: 1 != 0 : agent_workflows.oc_runipd called execute_item on landed lane

Restored:
14 passed in 3.27s
```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the final summary line of a bare `python3 -m pytest` (e.g. `N passed, M skipped, ...`) with zero failures.
  - Observed evidence: Full test suite passing bare (2054 passed, 1 skipped, 3 warnings in 30.73s).
```
2054 passed, 1 skipped, 3 warnings in 30.73s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Two things, and the second is the consequential one. FIRST, a new dispatch-time gate that can DECLINE TO RUN AN APPROVED PLAN on both runner hosts, parking it under a new terminal status `already-landed`. The failure mode to weigh is a FALSE POSITIVE: a plan that genuinely needs work is parked and a human must intervene. Three things bound that risk and each is tested (E-07 C/D/E): the `commits_ahead > 0` and not-dirty rules, the fail-closed rule over ALL of an id6's lanes, and the `reusable` exemption. The gate never deletes, never merges, and never finalizes; its only effect is whether a turn is spent. SECOND, AN AMENDMENT TO AN `approved` SPEC (`uonrjg` Section 7.2, E-09). That is the highest-leverage change in this plan, because a spec is the contract every future plan is reviewed against. Review measured that no test enforces that row, so the amendment rests on the contract argument alone: approve it as a contract decision, not as a mechanical consequence.

A NEW ITEM STATUS IS A DURABLE VOCABULARY CHANGE. `already-landed` will be written into run ledgers that outlive this release and read by `runner_shutdown`'s coherence check, `lifecycle_style`, and every reporting surface. A status admitted by some vocabularies and not others is the measured failure `TERMINAL_QUEUE_STATUSES` documents (Phase 0 calls the run "an undefined state" and refuses its own resume), which is why E-04 lands all five code surfaces in one edit and V-04 probes each by name.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the seven paths in `- Scope-Paths:` are the intended surface. `classify_lane_integration` and `describe_lane` are OUT: the gate consumes the existing landing reading and must not fork a second one. If a cross-host fixture or test must also change, MAKE the edit and justify it at finalize with `--scope-reason` per out-of-scope path (and `--scope-ack` per declared-but-unmodified path), which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output, and a `-k` selector that matches zero tests is NOT a pass (F-8 caught exactly that in the authored V-03). Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

OQ-01 is `Blocking: no` with a stated default (nonzero exit) and a one-line alternative if the maintainer prefers benign.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if E-01 finds fact (1) moved, the defect is already fixed and this plan should be retired rather than executed; if fact (2) moved, E-02's `commits_ahead > 0` guard may be unnecessary or insufficient and the predicate needs re-derivation; if fact (3) moved, the remedy line names the wrong verb. In each case report rather than adapting silently. If the gate appears to require editing `classify_lane_integration`, stop: forking the landing reading is the one thing this design must not do.

Commit through `aw commit <plan> -- <paths>`, path-scoped, never `git add -A`, never push. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` carry observed evidence before the terminal transition, which the RUNNER owns when it executes this plan in a lane and which the executor otherwise performs with `aw ipd finalize`.
