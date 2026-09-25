# IPD: Stop the runner re-dispatching an approved plan whose lane work already landed on main

- Date: 2026-09-24
- Kind: child
- Concern: A plan whose lane is integrated BY HAND (a raw `git merge`, which never runs `aw ipd finalize`) keeps `- Status: approved` in `pending/`. `runner_shared.determine_action` correctly maps `approved` -> `execute`, `runner_shared.initial_queue_status` correctly births it `queued`, and neither `oc_runipd.run_queue` nor `agy_runipd.run_queue` asks whether its lane's work is already on HEAD before calling `execute_item`. So an unattended queue spends a full agent turn (minutes plus model spend) on an empty diff, and an executor trusting the queue could re-apply work onto a tree that has since absorbed a conflicting fix. The landing predicates that would answer the question already exist (`runner_shared.lane_work_has_landed`, `runner_shared.lane_work_landed_by_content`, composed by `runner_shared.classify_lane_integration`) but are consumed only by interrupt reclaim and stranded-lane reporting (`runner_shared.stranded_lane_records`, `attention`).
- Scope: IN: (a) one shared read-only predicate in `runner_shared` that enumerates an id6's EXISTING lane refs (`aw/lane/<id6>` and `aw/lane/<id6>_attempt*`) and reports whether a lane holding COMMITS, clean and not live, has landed on HEAD per the EXISTING `classify_lane_integration`; (b) one shared dispatch-time gate that, for an `execute` item that is not `reusable`, writes a new named non-dispatched status `already-landed` with a remedy line and an event instead of calling `execute_item`; (c) wiring that gate into BOTH hosts' `run_queue`, re-checked at dispatch exactly where the orchestrator branch already sits; (d) registering the status in every vocabulary that must admit it (both hosts' and `runner_shared`'s `TERMINAL_STATES`, `runner_shutdown.KNOWN_ITEM_STATUSES`, `lifecycle_style._RUNNER_ITEM_PAIRS`, and spec `uonrjg` Section 7.2, which a test reads); (e) tests proving the spawn seam is not called for a merged lane and IS called for an unmerged lane, a zero-commit dirty lane, and a reusable plan. OUT: auto-finalizing (an attested lifecycle act the runner must not perform on a human's behalf); an `aw check` advisory for approved-but-landed plans (Deferred, Carrier `zmo0ao`); the already-`executed` admission case (`lb5dzj`); changing `reintegrate_lane` or the integrate verb.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shutdown.py, agent_workflows/lifecycle_style.py, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, tests/test_already_landed_dispatch.py
- Item-Dependencies: none
- Status: to-review
- Set: mergeskip
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8k0z40
- From-Backlog: zmo0ao
- Blocks-Release: next
- Priority: high
- Work-Kind: bug

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zmo0ao; re-measured at HEAD `877545fc` that no dispatch-time landing check exists in either host, that `classify_lane_integration` reads a ZERO-COMMIT DIRTY lane as LANDED (so the gate must require `commits_ahead > 0` itself), and that `aw oc integrate <id6>` is NOT a usable remedy because `reintegrate_lane` refuses a lane whose plan is not finalized on the lane.

## Goal

Before spending an agent turn on an `execute` item, ask the repository's existing landing predicate whether that plan's lane work is already on HEAD; if it is, park the item under a named, non-dispatched status `already-landed` with a remedy that names the human lifecycle act still owed (`aw ipd finalize`), on both hosts, through one shared definition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the premise

- [ ] E-01 RE-MEASURE THE THREE FACTS THE DESIGN RESTS ON, at the executing HEAD, before writing code. (1) Neither `oc_runipd.run_queue` nor `agy_runipd.run_queue` consults any landing predicate between selecting `runnable` and calling `execute_item(run_dir, state, runnable, ...)`: `grep -n "classify_lane_integration\|lane_work_has_landed\|lane_work_landed_by_content" agent_workflows/*.py` must show callers only in `runner_shared` (reclaim/`stranded_lane_records`), `worktree_lease.lane_merged_into_target` and `attention`. (2) Reproduce the probe in Findings F-3 in a throwaway repo under `/tmp/`: four lanes (zero-commit clean, zero-commit DIRTY, one-commit merged `--no-ff`, one-commit unmerged) classified by `runner_shared.classify_lane_integration`, and confirm the zero-commit dirty lane reads `lane_state == LANDED`. (3) Confirm `runner_shared.reintegrate_lane` step 4 still refuses with `REINTEGRATE_PLAN_NOT_FINALIZED` when `lane_holds_finalized_plan` is False. If ANY of the three no longer holds, STOP and report: (1) moving means the defect is fixed; (2) moving changes E-02's guard; (3) moving changes the remedy line.
  - Depends on: none
  - Expected outcome: the three facts reproduced with pasted command output, or a STOP report naming which moved.
  - Execution state: pending

### Task group 2: one shared predicate and one shared gate

- [ ] E-02 ADD `runner_shared.already_landed_lanes(repo: Path, id6: str) -> list[dict]` (read-only, never raises for an expected condition). It enumerates EXISTING refs with `git for-each-ref --format=%(refname:short) refs/heads/aw/lane/<id6> 'refs/heads/aw/lane/<id6>_attempt*'` (the canonical prefix is `worktree_lease.lane_branch_name`, and the lane id is recovered with `worktree_lease.lane_id_from_branch`), classifies each with the EXISTING `runner_shared.classify_lane_integration(repo, {"id6": id6, "lane_id": <lane id>})`, and returns the records. Add a companion `runner_shared.lane_work_already_landed(records) -> bool` that is True ONLY when (i) at least one record has `lane_state == LANE_LANDED` AND `commits_ahead > 0` AND `dirty is False`, and (ii) NO record is `LANE_STRANDED`, `LANE_UNKNOWN` or `LANE_LIVE`. Rule (i)'s `commits_ahead > 0` is the load-bearing false-positive guard (F-3: a zero-commit dirty lane classifies LANDED because its tip IS its base and is trivially an ancestor of HEAD); it mirrors `reintegrate_lane`'s own `if lane.commits_ahead <= 0` refusal ("HOLDS-WORK alone does NOT prove committed work"). Rule (ii) fails closed: any lane still holding unlanded or unanswerable work means today's dispatch behavior is kept. Enumerating refs that exist is NOT the "reconstruct `aw/lane/<id6>` from the id6" that `worktree_lease.lane_branch_name`'s docstring forbids: that prohibition protects a WRITE (integrating a guessed lane); this is a read whose only consequence is whether a turn is spent, and state it so in the docstring. A `git for-each-ref` failure returns `[]` (no lanes -> dispatch as today).
  - Depends on: E-01
  - Expected outcome: the two functions exist in `runner_shared`, docstrings cite the F-3 measurement and the `reintegrate_lane` precedent, and neither writes anything.
  - Execution state: pending

- [ ] E-03 ADD `runner_shared.ALREADY_LANDED_STATUS = "already-landed"`, `runner_shared.ALREADY_LANDED_RECOVERY_HINT` and `runner_shared.skip_dispatch_if_already_landed(repo, run_dir, state, item, *, save_state, append_jsonl) -> bool`, host bindings INJECTED exactly as `runner_shared.handle_zero_work_retry` takes them (this module may not import a `*runipd` module; `tests/test_runner_shared.py::NoRunnerImportTests`). It returns False (and writes nothing) unless `item.get("action") == "execute"`, `item.get("initial_status") != "reusable"` (a reusable plan is re-executed by design and a merged lane from a previous run must never park it), and `lane_work_already_landed(already_landed_lanes(repo, item["id6"]))` is True. When True it sets `item["status"] = ALREADY_LANDED_STATUS`, `item["already_landed_lanes"]` (branch, head, `landed_by` per lane), `item["already_landed_recovery"] = ALREADY_LANDED_RECOVERY_HINT`, appends an `already-landed` event to `run_dir / "events.jsonl"` carrying the same fields, prints one line to stderr naming the id6 and the hint, and returns True. The hint text, verbatim in substance: "its lane work is already on HEAD but the plan was never finalized (a hand merge does not run `aw ipd finalize`). Run `aw ipd lint --phase pre-transition <id6>` and then `aw ipd finalize <id6> --actor <you> --message <why> --apply`; if the landed lane is stale and the plan genuinely needs new work, delete the merged lane branch (`git branch -d <branch>`, which git only permits for a merged branch) and re-run." It does NOT name `aw oc integrate <id6>` (F-4: that verb refuses an unfinalized lane and would at best re-merge a no-op) and does NOT finalize (an attested lifecycle act).
  - Depends on: E-02
  - Expected outcome: one shared gate function plus its two constants; no host-specific logic in it.
  - Execution state: pending

- [ ] E-04 REGISTER `already-landed` IN EVERY VOCABULARY THAT MUST ADMIT IT, each with a one-line comment citing this plan. It is TERMINAL for the run (a re-check within the same run would give the same answer, and `--retry-incomplete` must NOT list it because re-dispatch would re-park it), so add it to `runner_shared.TERMINAL_STATES`, `oc_runipd.TERMINAL_STATES` and `agy_runipd.TERMINAL_STATES`; to `runner_shutdown.KNOWN_ITEM_STATUSES` (terminal group), or Phase 0's R3 coherence check calls the run "an undefined state" and refuses its own resume (the reason `runner_shared.TERMINAL_QUEUE_STATUSES` documents); and to `lifecycle_style._RUNNER_ITEM_PAIRS` as `("already-landed", BLOCKED)`, because it needs a person, like `merge-needs-human`. Amend spec `uonrjg` Section 7.2 by adding `already-landed` to the `blocked` row, since `tests/test_lifecycle_style.py` parses that spec file and fails on a code mapping absent there. DO NOT add it to `EXECUTION_SUCCESS_STATES` or `SUCCESS_STATES`: the plan is still `approved` in `pending/`, so a dependent correctly waits (cascade marks it `dependency-blocked`, the same outcome `edge_satisfied`'s terminal-directory read would give), and the run exits nonzero (OQ-01).
  - Depends on: E-03
  - Expected outcome: the status admitted by all six surfaces, absent from both success sets; the spec row amended.
  - Execution state: pending

### Task group 3: both hosts consume the one gate

- [ ] E-05 WIRE THE GATE INTO `oc_runipd.run_queue`, immediately AFTER the `if runnable.get("action") == "orchestrate":` block and BEFORE `current_setid = runnable.get("setid")` / `execute_item(...)`: `if runner_shared.skip_dispatch_if_already_landed(Path(state["repo"]), run_dir, state, runnable, save_state=save_state, append_jsonl=append_jsonl): save_state(run_dir, state); continue`. Placement at dispatch (not at queue build) is the same re-check discipline dependencies get: a lane can be merged by hand while an earlier item's turn is running. Pop of `recovery_next` above it is left as is.
  - Depends on: E-04
  - Expected outcome: one call site in oc, no logic beyond the call.
  - Execution state: pending

- [ ] E-06 WIRE THE SAME CALL INTO `agy_runipd.run_queue` at the mirrored position (after its `if runnable.get("action") == "orchestrate":` block, before `execute_item(...)`), byte-identical apart from nothing: both hosts bind `save_state`/`append_jsonl` the same way.
  - Depends on: E-04
  - Expected outcome: one call site in agy, identical to E-05's.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_already_landed_dispatch.py`, looping over `(oc_runipd, agy_runipd)` and reusing the dispatch-harness shape of `tests/test_runner_shared.py` (`_dispatch_repo`/`_dispatch_run`, `mock.patch.object(module, "execute_item", fake)`, `module.run_queue(run_dir)`). Queue item: `action: execute`, `kind: child`, `status: queued`, `initial_status: approved`. Cases: (A) POSITIVE: branch `aw/lane/abc123` cut from main via `git worktree add -b`, one commit, merged into main with `git merge --no-ff`; assert the fake `execute_item` was NEVER called, final status is `already-landed`, `already_landed_recovery` is present and mentions `aw ipd finalize`, an `already-landed` event is in `events.jsonl`, and `run_queue` returns nonzero. (B) NEGATIVE: same but NOT merged; assert `execute_item` called exactly once. (C) FALSE-POSITIVE GUARD: a lane worktree with ZERO commits and an uncommitted file; assert `execute_item` called once. (D) FAIL-CLOSED: `aw/lane/abc123` merged plus `aw/lane/abc123_attempt2` holding an unmerged commit; assert `execute_item` called once. (E) REUSABLE: case A's repo with `initial_status: reusable`; assert `execute_item` called once. Plus direct unit tests of `lane_work_already_landed` on hand-built records covering rules (i) and (ii).
  - Depends on: E-05, E-06
  - Expected outcome: the new module passes; case A fails when the E-05/E-06 call is removed.
  - Execution state: pending

- [ ] E-08 RUN THE BARE SUITE `python3 -m pytest` (no extra flags) and paste the summary line.
  - Depends on: E-07
  - Expected outcome: green bare suite with the summary line pasted.
  - Execution state: pending

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
| F-5 | INFO | backlog item's example | The measured example `li44r9` is NOW `executed` (`.aw/records/plans/executed/20260917-hostdedup-01-li44r9-...`, history "aw oc run self-finalize: li44r9 verified"), so it no longer reproduces at HEAD. The defect class still holds (F-1); the regression test must build its own merged lane rather than rely on a live one. A scan of every `approved` plan in `pending/` at HEAD found lanes only for `lkexaw` (four lanes, all `STRANDED`), so the gate would change nothing in today's queue, which is the fail-closed direction. | scan over `pending/*.ipd.md` with `Status: approved` + `git for-each-ref refs/heads/aw/lane/<id6>*`: `lkexaw aw/lane/lkexaw STRANDED 1`, `..._attempt2 STRANDED 2`, `..._attempt3 STRANDED 1`, `..._attempt4 STRANDED 2`. |
| F-6 | MED | vocabulary surfaces | Six places must admit a new item status: `runner_shared.TERMINAL_STATES`, both hosts' `TERMINAL_STATES`, `runner_shutdown.KNOWN_ITEM_STATUSES` ("an unknown value means the ledger was left in an undefined state"), `lifecycle_style._RUNNER_ITEM_PAIRS`, and spec `uonrjg` Section 7.2 (read by `tests/test_lifecycle_style.py`). | quoted comments in each; `tests/test_lifecycle_style.py` locates "20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md". |

## Proposed changes (ordered, validatable)

1. E-01 re-measures F-1, F-3 and F-4 and STOPs if any moved.
2. E-02 adds the read-only predicate over existing lane refs, consuming `classify_lane_integration` and adding the `commits_ahead > 0`, not-dirty and fail-closed-over-all-lanes rules.
3. E-03 adds the shared gate, status constant and remedy hint naming `aw ipd finalize`.
4. E-04 admits `already-landed` in all six vocabulary surfaces, including the spec `uonrjg` 7.2 row.
5. E-05 and E-06 call the gate in both hosts at dispatch.
6. E-07 proves the positive, negative, false-positive, fail-closed and reusable cases on both hosts; E-08 runs the bare suite.

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

- Over-scope: none. No change to `reintegrate_lane`, the integrate verb, `classify_lane_integration`'s body, or `describe_lane` (pinned by `tests/fixtures/runner_shared_premove_fingerprints.json`).
- Under-scope: if an existing cross-host test asserts `TERMINAL_STATES` equality or coverage and needs the new member listed in a fixture, that test file becomes in scope; declare it in `- Scope-Paths:` before editing rather than editing silently.

## Required tests / validation

- `python3 -m pytest tests/test_already_landed_dispatch.py -o addopts="" -q` green, and case A shown FAILING with the E-05/E-06 call removed.
- `python3 -m pytest tests/test_lifecycle_style.py tests/test_runner_shared.py -o addopts="" -q` green (vocabulary and spec-coverage tests).
- `python3 -m pytest` bare, summary pasted.

## Spec / documentation sync

- AMEND spec `uonrjg` (`.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`) Section 7.2: add `already-landed` to the `blocked` row. WHY: the spec is the normative stage table for runner item statuses and `tests/test_lifecycle_style.py` fails on a mapped status the spec does not carry; `blocked` because the item needs a human act (finalize), matching `merge-needs-human`. Declared in `- Scope-Paths:` so both runners announce it.
- No user-facing doc change required; the remedy is printed at the point of use.

## Open questions

### OQ-01: Should an `already-landed` item count as success for the run's exit code?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFAULT, applied by E-04: NOT benign, exit nonzero. Evidence: the plan is still `approved` in `pending/`, so a human act is owed and the queue did not accomplish what it was asked; the `em0z50`/`zz5yxq` ruling (`success_states_for_action`) is that an execute item which did no work must not exit 0; and a dependent is held back by the cascade, so exit 0 would report success over blocked work. The alternative (benign, exit 0) is defensible for an unattended overnight queue where the gate saved a turn; it is a one-line change (add to `EXECUTE_REPORTING_SUCCESS_STATES` only, never `EXECUTION_SUCCESS_STATES`) if the maintainer prefers it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `grep -n "classify_lane_integration\|lane_work_has_landed\|lane_work_landed_by_content" agent_workflows/*.py` output showing no `*runipd.py` caller; paste the probe's per-lane line for all four lanes with the zero-commit DIRTY lane reading `LANDED`; quote the `REINTEGRATE_PLAN_NOT_FINALIZED` refusal in `reintegrate_lane`. Or a STOP report naming the moved fact.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a `python3 -c` probe calling `runner_shared.already_landed_lanes` and `lane_work_already_landed` on the four-lane probe repo plus a merged-and-unmerged pair for one id6, showing True only for the merged committed clean lane and False for the zero-commit dirty lane and for the id6 that also has a STRANDED attempt lane; paste `git diff --stat agent_workflows/runner_shared.py` and confirm `classify_lane_integration` and `describe_lane` bodies are unchanged (`git diff` shows no hunk inside either).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the gate's signature and the hint constant; paste `grep -n "integrate <id6>\|finalize_plan\|ipd finalize" ` over the new function body showing the hint names `aw ipd finalize` and the function calls no finalize/integrate code; paste `python3 -m pytest tests/test_runner_shared.py -o addopts="" -q -k NoRunnerImport` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a `python3 -c` probe printing `"already-landed" in X` for `runner_shared.TERMINAL_STATES`, `oc_runipd.TERMINAL_STATES`, `agy_runipd.TERMINAL_STATES`, `runner_shutdown.KNOWN_ITEM_STATUSES` (all True), `runner_shared.EXECUTION_SUCCESS_STATES` and `runner_shared.EXECUTE_REPORTING_SUCCESS_STATES` (both False), and `lifecycle_style` resolving it to `blocked`; paste the spec 7.2 diff hunk; paste `python3 -m pytest tests/test_lifecycle_style.py -o addopts="" -q` summary passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff agent_workflows/oc_runipd.py` showing only the gate call between the orchestrate block and `execute_item`; paste E-07 case A passing for `oc_runipd`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff agent_workflows/agy_runipd.py` showing the identical call at the mirrored position; paste E-07 case A passing for `agy_runipd`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest tests/test_already_landed_dispatch.py -o addopts="" -v` listing cases A-E and the predicate unit tests passing for both hosts; then paste the same run with the E-05 call locally removed showing case A FAILING for `oc_runipd` (execute_item called / status not `already-landed`), and restored green.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the final summary line of a bare `python3 -m pytest` (e.g. `N passed, M skipped, ...`) with zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. OQ-01 is `Blocking: no` with a stated default (nonzero exit). The executor commits only the paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes; test claims paste actual runner output. STOP conditions: if E-01 finds any of its three facts moved, or if the gate appears to require editing `classify_lane_integration` or `describe_lane` (pinned bodies), stop and report. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` carry observed evidence before the terminal transition, which the runner owns when it executes this plan in a lane and which is otherwise performed with `aw ipd finalize`.
