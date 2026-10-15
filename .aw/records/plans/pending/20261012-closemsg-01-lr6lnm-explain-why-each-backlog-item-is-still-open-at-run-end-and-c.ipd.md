# IPD: Explain why each backlog item is still open at run end, and close items whose orchestrator retires

- Date: 2026-10-12
- Kind: child
- Concern: The end-of-run "--- Backlog items left open ---" report (`runner_shared.render_unclosed_report`, fed by `runner_shared.unclosed_backlog_items`) prints one line per item reading "IPD <plan> ended <status>, so the close was never evaluated". Measured over October's run records (54 `backlog-items-left-open` events: 26 from review runs, 24 from execute runs, plus 4 others): 289 lines say "ended reviewed" (expected on every review run), 203 "ended queued" (a deliberate stop or a not-yet-reached item), 20 "ended interrupted", 33 `fail-*`, and 13 "ended executed". The wording reads as a fault for the expected cases, buries the cases that need attention, gives no next step, and leads with the PLAN while the heading names BACKLOG items. Separately, the 13 "ended executed" lines are a real defect: every one is an ORCHESTRATOR item (`action: orchestrate`) whose `backlog_close` record is absent, because `runner_shared.dispatch_orchestrator_item` retires it (`item["status"] = "executed"` after `ipd_lifecycle.retire_orchestrator`) without ever calling `process_backlog_close`. Seven of those items (`7yz545`, `s8veyk`, `ariaau`, `mflqqf`, `ildjse`, `oq05nc`, `h0tiaw`) are still not `done` today although every carrier is terminal: `aw backlog set done <id> --dry-run` accepts all seven. (REVIEW 2026-10-15: all seven have since been closed by executed plan `0owirm`; the defect in `dispatch_orchestrator_item` remains, see F-03 and E-05.)
- Scope: IN: (1) classify each unclosed item into a small fixed set of causes from facts the run already records, and render the report grouped by cause, with whether action is needed and one next command per group, item before plan; (2) record the same classification in the `backlog-items-left-open` ledger event (additive fields, existing `reason` kept); (3) call the backlog close for an orchestrator item when the runner retires it, on both hosts through the shared seam; (4) close, through the normal setter and citing this plan, every item re-derived at execution time as complete with an executed orchestrator carrier (the seven measured at authoring were already closed by `0owirm` on 2026-10-13); tests; CHANGELOG. OUT: changing the close predicate itself (`evaluate_backlog_close`, `check_engine.evaluate_blocking_close`); `aw attention`'s cross-tree view; the per-item `reason` strings `process_backlog_close` already writes on a refused close (rendered verbatim under the "close refused" group).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_unclosed_report_grouping.py, tests/test_orchestrator_retire_closes_backlog.py, CHANGELOG.md, .aw/records/backlog/
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: closemsg
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lr6lnm

## Workflow history
- 2026-10-15 reviewed (aw set): plan-review applied revisions

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored at the maintainer's request ("File this as a plan") after the end-of-run report of `run-20261012T233651Z-4004596` listed 24 items as "ended queued, so the close was never evaluated" for a deliberately stopped run.

## Goal

At the end of a run, an operator can tell at a glance which open backlog items are expected (nothing to do), which need attention, and what to run next; and an item whose orchestrator retires is closed exactly as if its plan had been executed by an agent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: classification and rendering

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids. Also render the current report for `run-20261012T233651Z-4004596`'s `state.json` (call `render_unclosed_report` on it) and record the output as the "before" sample. Run records are machine-local and gitignored (resolved through `runner_shared.state_root`), so they do not exist in a lane worktree (none found at review). If the run's `state.json` is not reachable, build the before sample from a synthetic state that reproduces it (24 `queued` items with `from_backlog`, plus a `deliberate-stop` event naming them in `not_started`) and say which source was used.
  - Depends on: none
  - Expected outcome: a recorded summary line, failing-node-id list, and the before sample.
  - Execution state: pending

- [ ] E-02 In `runner_shared.py`, add `classify_unclosed(state, run_dir) -> list[UnclosedItem]` where `UnclosedItem` carries `item_id6`, `plan_id6`, `cause`, `detail`, `needs_action: bool`. Causes, decided in this order from recorded facts only: `close-refused` (a `backlog_close` record exists with `closed: false`; `detail` is its existing `reason`; needs action only when the reason is not the multi-carrier wait below); `waiting-on-carriers` (that refusal's reason begins "IPD carrier(s) not executed"; `detail` lists the unfinished carriers by id6 only, not full paths; no action); `plan-failed` (plan status `interrupted`, `stalled`, or any `fail-*`; needs action); `review-only` (plan status `reviewed`, or the item's action is `review`; no action); `not-started` (plan status `queued`, with `detail` "the run was stopped before this plan ran" when `events.jsonl` holds a `deliberate-stop` event naming it in `not_started`, else "the run ended before reaching this plan"; no action); `unknown` (anything else; needs action, `detail` names the status). Keep `unclosed_backlog_items` returning its `(item_id6, reason)` pairs unchanged for existing callers, derived from the same classification.
  - Depends on: E-01
  - Expected outcome: a pure function mapping the five October status families and the multi-carrier refusal to the expected causes.
  - Execution state: pending

- [ ] E-03 Rewrite `render_unclosed_report` to render grouped output: heading `--- Backlog items still open (<n>) ---`; groups that need action first (`plan-failed`, `close-refused`, `unknown`), then the expected ones (`waiting-on-carriers`, `not-started`, `review-only`); per group one plain sentence saying what happened and whether anything needs doing, then `item <- plan` pairs packed several per line (with `detail` per line for `close-refused`, `waiting-on-carriers`, `unknown`), then one next-command line: `not-started` from a stop -> the run's resume command, built as `f"{labels.command} resume {run_id}"` from the run's `HostLabels` (`labels.command` already carries the verb, so never `aw <host> run run resume`; see the `z3si7r` note beside `turn_retry_remedy`), with the host derived from `state["host_capabilities"]` as `dispatch_orchestrator_item` does; `plan-failed` -> `aw runs <run-id>`; `review-only` -> none ("items close when their plans are executed"); `waiting-on-carriers` -> none. Keep the closing pointer to `aw attention`. Wording must not use "never evaluated". Keep the existing `Palette(should_color(sys.stdout))` coloring and keep the function handler-safe (no lock, no state write), because `emit_shutdown_report` calls it from the signal path. Example target for the 2026-10-12 run: "Not started (24): the run was stopped before these plans ran (stop requested 23:59:06). Nothing to fix; each item closes when its plan executes." followed by the pairs and "Continue: aw agy run resume run-20261012T233651Z-4004596".
  - Depends on: E-02
  - Expected outcome: rendering the E-01 state yields one "Not started (24)" group with the resume command and no other group.
  - Execution state: pending

- [ ] E-04 Extend `record_unclosed_backlog_items` so each item in the `backlog-items-left-open` event also carries `cause`, `plan` and `needs_action` (additive; the existing `item` and `reason` keys are unchanged so existing readers keep working).
  - Depends on: E-02
  - Expected outcome: the ledger event carries the new keys alongside the old ones.
  - Execution state: pending

### Task group 2: the orchestrator close

- [ ] E-05 In `runner_shared.dispatch_orchestrator_item`, immediately after a successful retirement sets `item["status"] = "executed"` and appends `orchestrator-finalized`, call the host's backlog close for that item when it carries `from_backlog` (the same `process_backlog_close` binding the execute path receives; thread it through `dispatch_orchestrator_item`'s callers on both hosts, mirroring how `finish_reintegrated_item` takes `process_backlog_close`), guarded exactly as that function guards it (skip when `backlog_close` already records `closed: true`; never raise into the run: a failure records `{closed: false, reason: "close evaluation failed: ..."}` as `process_backlog_close` already does). The close decision is unchanged: it still requires every carrier to be terminal. BEFORE the call, set `item["last_plan_path"]` to the orchestrator plan's post-retirement repo-relative path (re-resolve it with `resolve_plan_path(repo, str(item.get("configured_file") or ""), id6)` after `retire_orchestrator`, inside `contextlib.suppress(DriverError, OSError)`, exactly as `finish_reintegrated_item` does). This is REQUIRED, not optional (PR-001): `evaluate_backlog_close` refuses with "this run executed none of its carriers, so the close was not earned" unless a carrier's path is in `run_earned_paths(state)`, and an orchestrator item has no attempts, so `collect_earned_paths` yields nothing without `last_plan_path`. Measured at review on live `iosmvn` (orchestrator plus four executed children): `evaluate_backlog_close(repo, "iosmvn", [])` refuses with that reason, and the same call with the orchestrator's `executed/` path earned closes. The retirement IS this run's own work on its own plan, so earning that one path is the same "worker asserts a fact about its own item" rule `executed_overrides` already follows; sibling carriers are still read from main. Pass `lane_repo=None` (the retirement already landed on main through `land_worktree_commit`), so the close runs in the non-isolated shape.
  - Depends on: E-01
  - Expected outcome: a run that retires an orchestrator whose item's carriers are all terminal closes the item `done` in the same run; one with a non-terminal sibling carrier records `waiting-on-carriers` instead. Host edits: `oc_runipd.py` and `agy_runipd.py` each pass their own `process_backlog_close` binding at their `dispatch_orchestrator_item(` call (both call sites are in the host modules, measured at review), so both files are in `- Scope-Paths:`.
  - Execution state: pending

- [ ] E-06 RE-DERIVE the stranded set at execution time instead of closing a fixed list (PR-002). The seven ids measured at authoring (`7yz545`, `s8veyk`, `ariaau`, `mflqqf`, `ildjse`, `oq05nc`, `h0tiaw`) were ALREADY CLOSED on 2026-10-13 by executed plan `0owirm`'s dispatch-time check (each item's newest history line reads "closed by 0owirm: every carrier executed"), so they are not re-closed. Instead: for every item under `.aw/records/backlog/graduated/` and `open/`, call `runner_shared.backlog_item_already_complete(repo, id6)`; for each `COMPLETE` result whose carriers include a `- Kind: orchestrator` plan (the population F-03 strands), run `aw backlog set done <id> --dry-run`, and only if it accepts run the real transition with `--message "closed by plan lr6lnm: every carrier is executed; the runner retired its orchestrator without evaluating the close (orchestrator close gap)"`. Never hand-edit an item file. Measured at review (context, not a bar): `iosmvn`, `coivul`, `5st6e5`, `58x9mw` were COMPLETE with an executed orchestrator carrier, and `aw backlog set done iosmvn --dry-run` accepted. A COMPLETE item with no orchestrator carrier (for example `rolswj`, `23p80m`) is outside F-03's cause and is left to `0owirm`'s dispatch-time close.
  - Depends on: E-05
  - Expected outcome: each re-derived, dry-run-accepted item is in `backlog/done/` with a workflow-history line citing `lr6lnm`; an empty re-derived set is a valid outcome and is recorded as such.
  - Execution state: pending

### Task group 3: tests and changelog

- [ ] E-07 Tests (behavioral, P16). `tests/test_unclosed_report_grouping.py`: build `state` dicts and an `events.jsonl` in a temp run dir covering each cause (queued plus a deliberate-stop event naming it; queued without one; reviewed; interrupted; fail-gate; a `backlog_close` refusal with the carrier reason; one with another reason; an unknown status) and assert on `render_unclosed_report` output: group headings and counts, needs-action groups ordered first, `item <- plan` pairs, the resume command only for the stopped-run group, no "never evaluated" anywhere; assert the ledger event's new keys. `tests/test_orchestrator_retire_closes_backlog.py`: in a `git init` fixture repo with a backlog item, an orchestrator carrying `- From-Backlog:` and one executed child, drive `dispatch_orchestrator_item` (with the real `process_backlog_close` binding, so `retire_orchestrator` and `evaluate_backlog_close` both run for real) and assert the item moved to `backlog/done/`; with a second, unexecuted carrier assert it stays open with cause `waiting-on-carriers`. Add a `- Fixed:` CHANGELOG bullet (clearer end-of-run open-item report; items whose orchestrator retires now close); no em or en dashes.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: both files pass; the orchestrator test fails with E-05 reverted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The unclosed report is this run's own items only; `aw attention` owns the cross-tree view (`unclosed_backlog_items` docstring, zhr6mc OQ-02).
- Ledger first: the event is appended before printing (`record_unclosed_backlog_items` docstring); the shutdown path must never raise.
- A deliberate stop is recorded only as a `deliberate-stop` event in `events.jsonl` with `not_started` (`runner_shared._record_deliberate_stop`); un-run items stay `queued` in state.
- The close decision is taken against main and requires every carrier terminal (`process_backlog_close` docstring); this plan does not change it.
- Behavioral tests only (P16); run the suite bare.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | One reason template covers every non-close. | `unclosed_backlog_items`: `f"IPD {item.get('id6')} ended {item.get('status', 'unknown')}, so the close was never evaluated"`. |
| F-02 | Most lines are expected noise. | October `backlog-items-left-open` events: 289 "ended reviewed", 203 "ended queued", 20 "interrupted", 33 `fail-*`, 13 "executed"; 26 of 54 events from review runs. |
| F-03 | Orchestrator retirement skips the close. | All 13 "ended executed" lines are `action: orchestrate` items with no `backlog_close` record; `dispatch_orchestrator_item` sets `executed` after `retire_orchestrator` and returns without calling `process_backlog_close`. |
| F-04 | Real items are stranded by F-03. (REVIEW 2026-10-15: these seven were closed on 2026-10-13 by `0owirm`; the population is re-derived in E-06.) | `7yz545` (4 of 4 carriers terminal), `s8veyk` (3/3), `ariaau` (4/4), `mflqqf` (3/3), `ildjse` (3/3), `oq05nc` (4/4), `h0tiaw` (3/3) not `done`; `aw backlog set done <id> --dry-run` accepted all seven. |
| F-05 | The confusing report that prompted this. | `run-20261012T233651Z-4004596`: deliberate stop at 23:59:06Z, 26 items `not_started`, 24 listed as "ended queued, so the close was never evaluated". |

- `0owirm` (executed, `gradfix`) added a dispatch-time close for an `open` backlog item whose carriers are all executed (`runner_shared.backlog_item_already_complete`, `_close_already_complete_backlog_item`) and explicitly DECLINED a retirement close site ("Carrier-Declined: Covered by this plan's dispatch-time check (E-03), so a retirement close site is unneeded"). REVIEW (PR-003): that check fires only when the item is itself QUEUED for production, so an item whose orchestrator retires in an execute run stays open until some later run queues the item, which is why E-05 is still needed. E-05 and the dispatch-time check both route through `aw backlog set done` and the shared gate, so they cannot disagree about eligibility.

## Proposed changes (ordered, validatable)

1. Classify (E-02), render grouped (E-03), ledger fields (E-04).
2. Orchestrator close (E-05), close the stranded items (E-06).
3. Tests and CHANGELOG (E-07).

## Deferred / out of scope (with reason)

- Showing the classification in `aw runs`: the ledger fields from E-04 make it possible; the viewer change is separate.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Items stranded before October: E-06 closes only the measured set; an `aw check` rule for "all carriers terminal but item not done" would find the rest and is a separate item.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

## Scope check

- Over-scope: none.
- Under-scope: none after review. Both `dispatch_orchestrator_item(` callers live in the host modules (`oc_runipd.py`, `agy_runipd.py`), so both are now in Scope-Paths (PR-005).

## Required tests / validation

Two new test files (E-07); existing runner tests covering `dispatch_orchestrator_item`, `process_backlog_close` and the shutdown report must still pass; bare suite against E-01.

## Spec / documentation sync

`CHANGELOG.md`. No spec amendment: spec `25kzda` requires the run to report items it left open with a reason; this changes the wording and grouping, not the obligation.

## Open questions

### OQ-01: Should expected groups (review-only, not-started) be hidden by default?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to show them, condensed: the report exists so a linked item is never silently absent (`unclosed_backlog_items` docstring), and a one-line group with a count and a next command costs little. Needs-action groups come first so they cannot be buried.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change bare-suite summary line, failing node ids, and the before sample.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of `classify_unclosed` over the E-01 state (24 `not-started` with the stop detail) and over a review-run state (real if reachable, else synthetic with `reviewed` items; all `review-only`), naming which source was used.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted after-render for the E-01 state, side by side with the before sample, showing the single grouped "Not started (24)" block and the resume command.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: a pasted `backlog-items-left-open` event line written by the changed function, showing `item`, `reason`, `cause`, `plan`, `needs_action`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` of `dispatch_orchestrator_item` (including the `last_plan_path` re-resolution) and of both host call sites, plus the passing E-07 orchestrator test and its failure with E-05 reverted, and its failure with ONLY the `last_plan_path` line removed (showing the "close was not earned" refusal), proving the earned-path half is load-bearing (code path: `dispatch_orchestrator_item` -> `retire_orchestrator` -> `process_backlog_close` -> `evaluate_backlog_close`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted re-derivation output (each graduated/open item that `backlog_item_already_complete` reports `COMPLETE`, with whether an orchestrator carrier is among its carriers); then for each selected id the pasted dry-run line and either the applied transition line plus `ls .aw/records/backlog/done/ | grep <id>`, or the refusal text. An empty selection is pasted as such.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted passing `python3 -m pytest tests/test_unclosed_report_grouping.py tests/test_orchestrator_retire_closes_backlog.py`; pasted post-change bare suite summary with no new failing node id versus V-01; `git diff CHANGELOG.md` with no em/en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Execute only after explicit human approval (`aw ipd set approved lr6lnm`); start with `aw ipd begin lr6lnm`. Commit ONLY the `- Scope-Paths:`, through `aw commit lr6lnm -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`; verify the staged set with `git diff --cached --name-only` first. Backlog transitions in E-06 go through `aw backlog set`, never a hand edit. Test fixtures are temp git repos, never the live tree.

SCOPE FENCE. The declared `- Scope-Paths:` are the expected edit set; an out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`. Do not change `evaluate_backlog_close`, `check_engine.evaluate_blocking_close`, or `backlog_item_already_complete`.

POST-GATE LIFECYCLE. On completion every `V-*` carries pasted evidence and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize lr6lnm`. Never hand-roll the move or `git mv` the plan. Carries `- Blocks-Release: next` because it fixes a live defect (F-03) under the repository's bug-gating rule.
