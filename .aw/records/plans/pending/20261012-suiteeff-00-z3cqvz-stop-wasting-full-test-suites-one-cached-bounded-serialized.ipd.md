# IPD: Stop wasting full test suites: one cached, bounded, serialized suite path for runners and agents

- Date: 2026-10-12
- Kind: orchestrator
- Concern: Backlog `58x9mw`. Measured over October's run records: the runner's pre-work suite baseline started 322 times and was collected 0 times (its collection sits inside `if integration_gate_relevant and not validate:` in `runner_shared.execute_item_core`, and validation is ON in the default configuration); agents ran 1,258 full-suite pytest invocations totalling 91.5 hours, each at `-n auto` with no reuse of an identical prior result; and on 2026-10-12, with seven concurrent drivers at load average 75-88 on 12 cores, full suites outran the 900s stall watchdog and three runs lost 9 of 11 turns.
- Scope: Orchestrate four children: (01) stop launching a baseline nothing will collect; (02) one full-suite entry point, `aw suite`, with a tree-keyed result cache and a bounded xdist worker count, adopted by the runner's own suite seams and named in agent prompts; (03) a machine-wide full-suite lock whose wait emits progress the stall watchdog counts; (04) a measurement of coverage-based test selection on real `main` steps, adopted for agent iteration only if it pays. ORCHESTRATION ONLY: every deliverable belongs to a child. The full suite remains the integration authority in every child.
- Scope-Paths: .aw/records/plans/pending/20261012-suiteeff-00-z3cqvz-stop-wasting-full-test-suites-one-cached-bounded-serialized.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 6867099fef6df2b3c6bf0c924a6ece40be7d6e76256927af2e05c34924b5f3ab
- Coverage-Checked: 2026-10-12 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: bug
- Priority: high
- From-Backlog: 58x9mw
- Blocks-Release: next
- Set: suiteeff
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: z3cqvz
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved

- 2026-10-13 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006 (record `.aw/records/reviews/20261012-suiteeff-00-z3cqvz-stop-wasting-full-test-suites-one-cached-bounded-serialized.review.md`)
- 2026-10-13 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006
- 2026-10-12 coverage pass (aw oc run): fingerprint 6867099fef6d, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 coverage pass (aw oc run): fingerprint 81cf22a88361, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog `58x9mw` at the maintainer's instruction, with the measurements in the backlog item re-run from `.aw/records/runs/run-202610*` and the git object store.

## Goal

Make a full test suite something the runners and agents run only when its answer is not already known, never more than the machine can carry at once, and never silently while the stall watchdog decides the turn is dead.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

THIS IS AN ORCHESTRATOR AND ITS ITEMS ARE ORCHESTRATION ONLY. Each item confirms one child reached `executed` and reads that child's own evidence; none produces an artifact.

### Task group 1: sequence and verify the Set

- [ ] E-01 CONFIRM 9ec94f REACHED executed
  - Depends on: none
  - Expected outcome: `9ec94f` is in `executed/`, and its own V-items record that a validation-ON execute attempt starts no baseline while a validation-OFF one still starts and collects it.
  - Execution state: pending

- [ ] E-02 CONFIRM 0o0wt2 REACHED executed
  - Depends on: E-01
  - Expected outcome: `0o0wt2` is in `executed/`, and its own V-items record a cache hit on an unchanged tree, a miss after a one-line edit, the bounded worker count, the runner's three suite seams routed through `run_full_suite`, and the `aw suite` instruction in the rendered execute and verify prompts.
  - Execution state: pending

- [ ] E-03 CONFIRM xvm6no REACHED executed
  - Depends on: E-02
  - Expected outcome: `xvm6no` is in `executed/`, and its own V-items record two concurrent full suites serialized with periodic wait lines, the heartbeat file advancing, and a stalled-looking waiter kept alive by it on both hosts.
  - Execution state: pending

- [ ] E-04 CONFIRM 1qut7y REACHED executed
  - Depends on: E-02
  - Expected outcome: `1qut7y` is in `executed/`, with its measurement recorded as research and its adopt-or-decline decision stated in its own V-items.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `9ec94f` | `20261012-suiteeff-01-9ec94f-stop-launching-the-runner-suite-baseline-when-nothing-will-c.ipd.md` | Starts the pre-work baseline only when the attempt's integration mode will collect it | none |
| 02 | `0o0wt2` | `20261012-suiteeff-02-0o0wt2-add-aw-suite-one-full-suite-entry-point-with-a-tree-keyed-re.ipd.md` | Adds `aw suite` (tree-keyed cache, bounded `-n`), routes the runner's suite seams through it, names it in agent prompts | executed:9ec94f |
| 03 | `xvm6no` | `20261012-suiteeff-03-xvm6no-serialize-full-suites-machine-wide-with-a-lock-whose-wait-th.ipd.md` | Machine-wide full-suite slot lock inside `aw suite`, with wait progress the stall watchdog counts | executed:0o0wt2 |
| 04 | `1qut7y` | `20261012-suiteeff-04-1qut7y-measure-coverage-based-test-selection-on-real-main-steps-and.ipd.md` | Measures pytest-testmon selection on real `main` steps; adopts it behind `aw suite --select` only if it pays | executed:0o0wt2 |

Order is forced: 01 removes the largest pure waste and is independent; 02 creates the single entry point that 03's lock and 04's selection both live inside; 03 and 04 are independent of each other but both need 02.

## Completion criteria (the whole Set is done only when)

- A validation-ON execute attempt starts no suite baseline, and a validation-OFF attempt still starts and collects one. OWNER: `9ec94f`.
- An unchanged code tree served twice runs the suite once; the cache key covers tracked and untracked non-ignored files, the argv, the interpreter and the installed distributions; failures are never cached without one confirming re-run. OWNER: `0o0wt2`.
- The runner's own suite seams (`run_suite_check`, the baseline, post-merge revalidation) and the agent prompt's validation instruction use `aw suite`. OWNER: `0o0wt2`.
- No more full suites than the configured slot count run at once on one machine, a waiter prints a progress line at least every 60 seconds, and the stall watchdog counts those lines. OWNER: `xvm6no`.
- A measured adopt-or-decline decision on coverage-based selection is recorded as research, and the full suite stays the integration authority either way. OWNER: `1qut7y`.

## Cross-IPD validation

- THE FULL SUITE STAYS THE AUTHORITY. No child may let a cached, selected or skipped result stand in for the integration gate's verdict except an exact-key cache hit on a PASS (0o0wt2 E-03); selection (1qut7y) is for agent iteration only. Each child's own V-items carry this check: 0o0wt2 V-03 (an unconfirmed failure is never stored) and V-06 (a FAILURE at a seam is still a failure), and 1qut7y V-04 (`--select` never touches the full-suite cache).
- ONE ENTRY POINT. 03 and 04 add behavior inside `aw suite`, never a second wrapper; checked by xvm6no V-02 (the slot is exercised through `aw suite`, code path `run_full_suite` -> `suite_slot`) and 1qut7y V-03/V-04 (`aw suite --select`) against 0o0wt2's command.
- NO SILENT WAIT. Any wait 03 adds emits progress the watchdog counts (xvm6no V-04 and V-05), because a silent wait is exactly the stall this Set exists to stop.

## Deferred / out of scope (with reason)

- The stall watchdog treating a long-running shell tool as idle in general (beyond suite-lock waits and suite runs, which `xvm6no` E-04 covers): a separate defect with its own blast radius. NOT YET TRACKED: no backlog item exists for it at review (2026-10-12); the maintainer should file it with `aw backlog new` (prose here is not a tracked work surface). Filing it is not this Set's deliverable and no child owns it.
- Limiting how many DRIVERS run at once or warning on host load: a separate defect; this Set bounds suites, not drivers. NOT YET TRACKED: no backlog item exists for it at review (2026-10-12); the maintainer should file it with `aw backlog new`.
- Sharing a cache across machines: the cache is local to the git common dir; a remote cache needs a trust model.

## Scope check

- Over-scope: none. This plan's only declared path is itself.
- Under-scope: none; each completion criterion names an owning child.

## Required tests / validation

None owed by this plan. Each child validates itself with its own bare-suite run and pasted output; this plan's V-items quote those records.

## Open questions

### OQ-01: One slot or a small pool for concurrent full suites?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED (by the plan author, not the maintainer) to a configurable pool defaulting to `max(1, cpu_count // 6)` slots (2 on the 12-core host), carried by `xvm6no`. One slot serializes seven drivers behind a 216s-median, 622s-p90 suite and would starve them; an unbounded count is today's failure. Each slot's suite gets `-n` = `max(2, cpu_count // slots)` from `0o0wt2` E-04, so the machine's cores are divided rather than multiplied.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted `- Status: executed` line of `9ec94f` from `executed/` and its V-02 (events from the validation-ON and validation-OFF cells) and V-03 (the cell failing with the condition reverted) evidence quoted from its record.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted `- Status: executed` line of `0o0wt2` and its V-02 (key sensitivity), V-04 (bounded `-n` and the cached second run), V-06 (seam records with `cached: true|false`) and V-07 (rendered prompts) evidence quoted from its record.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted `- Status: executed` line of `xvm6no` and its V-02 (serialized runs with the waiting line), V-04 (heartbeat mtime advancing) and V-05 (end-to-end not-stalled cell on both hosts, failing with the wiring reverted) evidence quoted from its record.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the pasted `- Status: executed` line of `1qut7y`, the path of its research record, and its adopt-or-decline line quoted from its record.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. Its open questions are resolved (OQ-01). It performs no work itself and its only declared path is itself, so any non-record edit made while executing it is out of scope and must be justified at finalize. Execute children in Order; `1qut7y`'s adoption half needs its own measurement to pass its stated threshold and otherwise records a decline, which still completes it. Under `aw oc run` / `aw agy run` the runner retires this plan once every child is `executed`; run by hand, the executor confirms each child in Order and stops at the first that has not reached `executed`, reporting which. The terminal transition is owned by the runner under a runner and by `aw ipd finalize` when run by hand; never hand-edit `- Status: executed` and never `git mv` the file. Every `V-*` MUST carry the actual pasted text quoted from the child's record, never a paraphrase or a claim. Commit only declared paths through `aw commit z3cqvz -- <paths>`; never push. Inherits `- Blocks-Release: next` from backlog `58x9mw`.
