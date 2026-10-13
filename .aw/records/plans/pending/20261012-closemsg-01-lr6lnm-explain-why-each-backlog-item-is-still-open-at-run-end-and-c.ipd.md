# IPD: Explain why each backlog item is still open at run end, and close items whose orchestrator retires

- Date: 2026-10-12
- Kind: child
- Concern: The end-of-run "--- Backlog items left open ---" report (`runner_shared.render_unclosed_report`, fed by `runner_shared.unclosed_backlog_items`) prints one line per item reading "IPD <plan> ended <status>, so the close was never evaluated". Measured over October's run records (54 `backlog-items-left-open` events: 26 from review runs, 24 from execute runs, plus 4 others): 289 lines say "ended reviewed" (expected on every review run), 203 "ended queued" (a deliberate stop or a not-yet-reached item), 20 "ended interrupted", 33 `fail-*`, and 13 "ended executed". The wording reads as a fault for the expected cases, buries the cases that need attention, gives no next step, and leads with the PLAN while the heading names BACKLOG items. Separately, the 13 "ended executed" lines are a real defect: every one is an ORCHESTRATOR item (`action: orchestrate`) whose `backlog_close` record is absent, because `runner_shared.dispatch_orchestrator_item` retires it (`item["status"] = "executed"` after `ipd_lifecycle.retire_orchestrator`) without ever calling `process_backlog_close`. Seven of those items (`7yz545`, `s8veyk`, `ariaau`, `mflqqf`, `ildjse`, `oq05nc`, `h0tiaw`) are still not `done` today although every carrier is terminal: `aw backlog set done <id> --dry-run` accepts all seven.
- Scope: IN: (1) classify each unclosed item into a small fixed set of causes from facts the run already records, and render the report grouped by cause, with whether action is needed and one next command per group, item before plan; (2) record the same classification in the `backlog-items-left-open` ledger event (additive fields, existing `reason` kept); (3) call the backlog close for an orchestrator item when the runner retires it, on both hosts through the shared seam; (4) close the seven currently-stranded items through the normal setter, citing this plan; tests; CHANGELOG. OUT: changing the close predicate itself (`evaluate_backlog_close`, `check_engine.evaluate_blocking_close`); `aw attention`'s cross-tree view; the per-item `reason` strings `process_backlog_close` already writes on a refused close (rendered verbatim under the "close refused" group).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_unclosed_report_grouping.py, tests/test_orchestrator_retire_closes_backlog.py, CHANGELOG.md, .aw/records/backlog/
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- Set: closemsg
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: lr6lnm

## Workflow history

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored at the maintainer's request ("File this as a plan") after the end-of-run report of `run-20261012T233651Z-4004596` listed 24 items as "ended queued, so the close was never evaluated" for a deliberately stopped run.

## Goal

At the end of a run, an operator can tell at a glance which open backlog items are expected (nothing to do), which need attention, and what to run next; and an item whose orchestrator retires is closed exactly as if its plan had been executed by an agent.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: classification and rendering

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` before the first edit; record its summary line and failing node ids. Also render the current report for `run-20261012T233651Z-4004596`'s `state.json` (call `render_unclosed_report` on it) and record the output as the "before" sample.
  - Depends on: none
  - Expected outcome: a recorded summary line, failing-node-id list, and the before sample.
  - Execution state: pending

- [ ] E-02 In `runner_shared.py`, add `classify_unclosed(state, run_dir) -> list[UnclosedItem]` where `UnclosedItem` carries `item_id6`, `plan_id6`, `cause`, `detail`, `needs_action: bool`. Causes, decided in this order from recorded facts only: `close-refused` (a `backlog_close` record exists with `closed: false`; `detail` is its existing `reason`; needs action only when the reason is not the multi-carrier wait below); `waiting-on-carriers` (that refusal's reason begins "IPD carrier(s) not executed"; `detail` lists the unfinished carriers by id6 only, not full paths; no action); `plan-failed` (plan status `interrupted`, `stalled`, or any `fail-*`; needs action); `review-only` (plan status `reviewed`, or the item's action is `review`; no action); `not-started` (plan status `queued`, with `detail` "the run was stopped before this plan ran" when `events.jsonl` holds a `deliberate-stop` event naming it in `not_started`, else "the run ended before reaching this plan"; no action); `unknown` (anything else; needs action, `detail` names the status). Keep `unclosed_backlog_items` returning its `(item_id6, reason)` pairs unchanged for existing callers, derived from the same classification.
  - Depends on: E-01
  - Expected outcome: a pure function mapping the five October status families and the multi-carrier refusal to the expected causes.
  - Execution state: pending

- [ ] E-03 Rewrite `render_unclosed_report` to render grouped output: heading `--- Backlog items still open (<n>) ---`; groups that need action first (`plan-failed`, `close-refused`, `unknown`), then the expected ones (`waiting-on-carriers`, `not-started`, `review-only`); per group one plain sentence saying what happened and whether anything needs doing, then `item <- plan` pairs packed several per line (with `detail` per line for `close-refused`, `waiting-on-carriers`, `unknown`), then one next-command line: `not-started` from a stop -> the run's resume command (`aw <host> run resume <run-id>` using the host label the run recorded); `plan-failed` -> `aw runs <run-id>`; `review-only` -> none ("items close when their plans are executed"); `waiting-on-carriers` -> none. Keep the closing pointer to `aw attention`. Wording must not use "never evaluated". Example target for the 2026-10-12 run: "Not started (24): the run was stopped before these plans ran (stop requested 23:59:06). Nothing to fix; each item closes when its plan executes." followed by the pairs and "Continue: aw agy run resume run-20261012T233651Z-4004596".
  - Depends on: E-02
  - Expected outcome: rendering the E-01 state yields one "Not started (24)" group with the resume command and no other group.
  - Execution state: pending

- [ ] E-04 Extend `record_unclosed_backlog_items` so each item in the `backlog-items-left-open` event also carries `cause`, `plan` and `needs_action` (additive; the existing `item` and `reason` keys are unchanged so existing readers keep working).
  - Depends on: E-02
  - Expected outcome: the ledger event carries the new keys alongside the old ones.
  - Execution state: pending

### Task group 2: the orchestrator close

- [ ] E-05 In `runner_shared.dispatch_orchestrator_item`, immediately after a successful retirement sets `item["status"] = "executed"` and appends `orchestrator-finalized`, call the host's backlog close for that item when it carries `from_backlog` (the same `process_backlog_close` binding the execute path receives; thread it through `dispatch_orchestrator_item`'s callers on both hosts, mirroring how `finish_reintegrated_item` takes `process_backlog_close`), guarded exactly as that function guards it (skip when `backlog_close` already records `closed: true`; never raise into the run: a failure records `{closed: false, reason: "close evaluation failed: ..."}` as `process_backlog_close` already does). The close decision is unchanged: it still requires every carrier to be terminal.
  - Depends on: E-01
  - Expected outcome: a run that retires an orchestrator whose item's carriers are all terminal closes the item `done` in the same run; one with a non-terminal sibling carrier records `waiting-on-carriers` instead.
  - Execution state: pending

- [ ] E-06 Close the seven stranded items found at authoring through the normal setter, one at a time, only if `aw backlog set done <id> --dry-run` still accepts it at execution time: `7yz545`, `s8veyk`, `ariaau`, `mflqqf`, `ildjse`, `oq05nc`, `h0tiaw`, each with `--message "closed by plan lr6lnm: every carrier is executed; the runner retired its orchestrator without evaluating the close (orchestrator close gap)"`. An item whose dry run refuses is left as is, with the refusal recorded in V-06. Never hand-edit an item file.
  - Depends on: E-05
  - Expected outcome: each accepted item is in `backlog/done/` with a workflow-history line citing `lr6lnm`.
  - Execution state: pending

### Task group 3: tests and changelog

- [ ] E-07 Tests (behavioral, P16). `tests/test_unclosed_report_grouping.py`: build `state` dicts and an `events.jsonl` in a temp run dir covering each cause (queued plus a deliberate-stop event naming it; queued without one; reviewed; interrupted; fail-gate; a `backlog_close` refusal with the carrier reason; one with another reason; an unknown status) and assert on `render_unclosed_report` output: group headings and counts, needs-action groups ordered first, `item <- plan` pairs, the resume command only for the stopped-run group, no "never evaluated" anywhere; assert the ledger event's new keys. `tests/test_orchestrator_retire_closes_backlog.py`: in a `git init` fixture repo with a backlog item, an orchestrator carrying `- From-Backlog:` and one executed child, drive `dispatch_orchestrator_item` (with the real `process_backlog_close` binding) and assert the item moved to `backlog/done/`; with a second, unexecuted carrier assert it stays open with cause `waiting-on-carriers`. Add a `- Fixed:` CHANGELOG bullet (clearer end-of-run open-item report; items whose orchestrator retires now close); no em or en dashes.
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
| F-04 | Real items are stranded by F-03. | `7yz545` (4 of 4 carriers terminal), `s8veyk` (3/3), `ariaau` (4/4), `mflqqf` (3/3), `ildjse` (3/3), `oq05nc` (4/4), `h0tiaw` (3/3) not `done`; `aw backlog set done <id> --dry-run` accepted all seven. |
| F-05 | The confusing report that prompted this. | `run-20261012T233651Z-4004596`: deliberate stop at 23:59:06Z, 26 items `not_started`, 24 listed as "ended queued, so the close was never evaluated". |

## Proposed changes (ordered, validatable)

1. Classify (E-02), render grouped (E-03), ledger fields (E-04).
2. Orchestrator close (E-05), close the stranded items (E-06).
3. Tests and CHANGELOG (E-07).

## Deferred / out of scope (with reason)

- Showing the classification in `aw runs`: the ledger fields from E-04 make it possible; the viewer change is separate.
- Items stranded before October: E-06 closes only the measured set; an `aw check` rule for "all carriers terminal but item not done" would find the rest and is a separate item.

## Scope check

- Over-scope: none.
- Under-scope: none known. Host modules need no edit if `dispatch_orchestrator_item`'s callers already live in `runner_shared`; if a host call site must pass the new binding, add that host file to Scope-Paths in the same commit and say so in V-05.

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
  - Required evidence: pasted output of `classify_unclosed` over the state of `run-20261012T233651Z-4004596` (24 `not-started` with the stop detail) and over one October review run's state (all `review-only`).
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
  - Required evidence: the `git diff` of `dispatch_orchestrator_item` (and any host call site), plus the passing E-07 orchestrator test and its failure with E-05 reverted (code path: `dispatch_orchestrator_item` -> `retire_orchestrator` -> `process_backlog_close`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: for each of the seven ids, the pasted dry-run line and either the applied transition line plus `ls .aw/records/backlog/done/ | grep <id>`, or the refusal text.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted passing `python3 -m pytest tests/test_unclosed_report_grouping.py tests/test_orchestrator_retire_closes_backlog.py`; pasted post-change bare suite summary with no new failing node id versus V-01; `git diff CHANGELOG.md` with no em/en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review` then human approval. Commit only Scope-Paths via `aw commit lr6lnm -- <paths>`; never push; paste real output into each `V-*`. Carries `- Blocks-Release: next` because it fixes a live defect (F-03) under the repository's bug-gating rule.
