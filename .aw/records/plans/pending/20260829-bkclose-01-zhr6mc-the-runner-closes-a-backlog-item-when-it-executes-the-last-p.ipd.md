# IPD: the runner closes a backlog item when it executes the last plan and reports what it left open

- Date: 2026-08-29
- Kind: child
- Concern: A `graduated` backlog item has no owner for its final close. The runner never reads a plan's `From-Backlog:` link, so it cannot know an item is involved; no automation advances `graduated` to `done`; and the one warning that would nag only inspects `open/`, so a graduated item is invisible to it. No item has ever made the graduated-to-done trip.
- Scope: Teach both runners to read a plan's `From-Backlog:` link, close a backlog item when the run executes the last plan that carries it, report every item left open with the reason before exit on normal exit and on SIGINT and SIGTERM, and end the run output with a pointer to `aw runs <run-id>`. Excludes tightening the release-gate close predicate, excludes fixing the `open/`-only warning, and excludes closing items for hand-run plans.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_backlog_close.py
- Item-Dependencies: executed:af7i6p
- Status: to-review
- Set: bkclose
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zhr6mc
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored at the maintainer's direction after we established that nothing closes a graduated backlog item. The maintainer added the exit-report requirement (E-05), the `aw runs` pointer (E-06), and the requirement that the report also fire on SIGINT and SIGTERM rather than only on `KeyboardInterrupt` (E-04).

## Goal

Close the loop the `graduated` status opened. When a run executes the last plan carrying a backlog item, close that item with the executed plan as evidence. When it cannot, say so before exiting so the human knows work remains.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: see the link, then close on the last plan

- [ ] E-01 Read the plan's `From-Backlog:` value when the runner builds its plan record, and carry it on the frozen queue entry. Use the schema's existing field constant (`ipd_schema.META_FROM_BACKLOG`) rather than a new regex, so the runner and the checkers cannot disagree on the field name. Absent means no linked item. Do this in both runners.
  - Depends on: none
  - Expected outcome: a queue entry for a plan carrying `- From-Backlog: <id6>` records that id6; a plan without the field records nothing; both runners agree.
  - Execution state: pending

- [ ] E-02 After a plan finalizes to `executed`, resolve every plan and spec that carries the same `From-Backlog` id6 by calling the existing shared helper `check_engine.find_from_backlog_artifacts`. Do not write a second lookup. If every carrier is in a terminal executed state, close the item by invoking the lifecycle-owned setter (`aw backlog set done <item> --evidence <path to the executed plan>`), never by editing the item file directly. If any carrier is not executed, do not close; record the reason.
  - Depends on: E-01
  - Expected outcome: an item whose only carrier just executed is closed `done` with the executed plan cited as evidence; an item with an unexecuted carrier is left untouched with a recorded reason.
  - Execution state: pending

- [ ] E-03 Gate the close on this run having executed the last carrier. A run must not close an item whose carriers it merely observed as already executed, because closing is a state change the run did not earn. Also fail closed: if the carrier lookup, the terminal-state read, or the setter invocation fails for any reason, leave the item alone and record the failure as a reason rather than proceeding.
  - Depends on: E-02
  - Expected outcome: a run that executed no carrier for an item closes nothing for it; an induced lookup or setter failure leaves the item untouched and produces a recorded reason.
  - Execution state: pending

### Task group 2: report before exit, on every catchable path

- [ ] E-04 Install explicit handlers for `SIGINT` and `SIGTERM` in the runner process itself. Today `SIGINT` is caught only incidentally as `KeyboardInterrupt` at the `main` boundary (the `except KeyboardInterrupt` in `main`, HEAD line 3084 at review time; anchor on the SYMBOL, not the number, see PR-001) and `SIGTERM` has NO handler, so Python's default terminates immediately and no `except` or `finally` runs. Each handler must write the unclosed-item record to the run ledger first, then print the report, then re-raise the original signal so the exit status remains the conventional one (130 for `SIGINT`, 143 for `SIGTERM`) and any parent still observes a normal signal death. The handler must be idempotent, so a second signal during reporting neither double-prints nor deadlocks, and it must NOT acquire the run lock or call `save_state`; it reads only state already in memory. Do not alter the existing child-process termination path (the escalating `_signal` loop over `(signal.SIGINT, _SIGINT_GRACE_SECONDS)` / `(signal.SIGTERM, _SIGTERM_GRACE_SECONDS)` in the child-kill helper), which is separate and works.
  - Depends on: none
  - Expected outcome: `SIGTERM` to a live run produces the report and exits 143; `SIGINT` produces the report and exits 130; a repeated signal during reporting does not double-report; the child-kill behavior is unchanged.
  - Execution state: pending

- [ ] E-05 Print, immediately before exit, every backlog item this run touched but did not close, each with its reason (which carriers remain unexecuted, or that this run did not execute the last carrier, or the recorded failure from E-03). Emit on normal exit and from the E-04 handlers. Write the record to the ledger BEFORE printing, so an uncatchable kill still leaves the answer on disk. Print nothing when there is nothing outstanding.
  - Depends on: E-03, E-04
  - Expected outcome: a run leaving items open lists each with a reason on normal exit and under both signals; a run with nothing outstanding prints no such section; the ledger record exists even when the print is truncated.
  - Execution state: pending

- [ ] E-06 End the run output with the single line ``Run `aw runs <run-id>` for more info.`` using the run's actual id. The verb is `aw runs <run-id>`; `aw oc runs` does not exist and must not be emitted. Suppress the line in `--json` and `--agent` output so machine-readable output stays parseable.
  - Depends on: E-05
  - Expected outcome: the pointer is the last line of human output on normal exit and under both signals, naming the real run id; it is absent from `--json` and `--agent` output.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-07 Add `tests/test_runner_backlog_close.py` covering: a single-carrier item closes when its plan executes; a two-carrier item does NOT close when only one executed; it DOES close when both have; the evidence argument names the real executed plan path; a run that executed no carrier closes nothing; an induced lookup or setter failure leaves the item untouched with a reason; the unclosed report lists each item with its reason on normal exit; the same report appears under `SIGINT` and under `SIGTERM` with exit codes 130 and 143; the ledger record precedes the print; a repeated signal does not double-report; the pointer line is last and names the real run id; the pointer is absent under `--json`. Include a symmetry assertion so a one-runner-only implementation fails. Each assertion must be shown to fail without the fix.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: the module passes; the close, no-close, signal-report, and pointer assertions each fail against pre-fix code; the symmetry assertion fails when only one runner is changed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner cannot see the link today: `grep -n "From-Backlog" agent_workflows/oc_runipd.py` returns nothing. It reads a plan's id, set, order, status, and scope, never the provenance field. This is an omission, not a decision, and it mirrors the `Item-Dependencies` gap where the field exists and four surfaces consume it while the runner does not.
- The lookup already exists and is shared: `check_engine.find_from_backlog_artifacts(repo_root, item_id6)` (locate by symbol; HEAD line 1336 at review time) returns every plan AND spec carrying the link, plans first. E-02 must reuse it; a second implementation would be the same divergence defect this repository keeps hitting.
- Closing must go through the setter. `aw backlog set done` runs the shared release-gate close predicate, which demands a preserved gate, a resolvable evidence citation, or explicit de-gating. Passing `--evidence <executed plan>` supplies the stronger SATISFIED proof rather than relying on the weaker "a carrier exists" route.
- Multi-carrier items are the normal case, not an edge case. Measured: `dh0uno` has carriers `58ha43` and `7p9n2v`; `qyaime` has `bl9q3d` and `qcqhj7`; `xmqv5l` has `rchpms`. Closing on "my plan executed" would falsely close `dh0uno` when only one of two finished.
- Carriers currently cluster inside one Set (`wtiso`, `lanetruth`), so a whole-Set run would see them all, but nothing guarantees that. The predicate must therefore be "all carriers executed in the REPOSITORY", not "all carriers executed in this run".
- There is exactly one exit funnel to extend: `main` catches `KeyboardInterrupt` and prints "Interrupted; durable run state was preserved." (locate by that string; HEAD lines 3084-3086 at review time). `SIGTERM` never reaches it because no handler is installed; the only `signal.SIGTERM` reference is in the escalating kill sequence for CHILD processes and is unrelated.
- `aw runs <run-id>` is the real inspection verb (`aw runs show|evidence|verify` all resolve). `aw oc runs` is not a command.
- Precedent for the test shape: `tests/test_lane_session_isolation.py` demonstrates the required AST guard plus cross-runner symmetry assertion, and the practice of proving a test fails without the fix.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `oc_runipd.py` | The runner never reads `From-Backlog`, so it cannot know a plan carries a backlog item and cannot close one. | `grep -n "From-Backlog"` returns nothing |
| F2 | HIGH | repository-wide | Nothing advances `graduated` to `done`: no automation, no workflow instruction, no `aw check` rule. Zero items in `done/` have a graduation in their history, so the transition has never once occurred. | searched every file in `backlog/done/` |
| F3 | HIGH | `check_engine.release_gate_warnings` | The one warning that would nag about a stale handed-off item skips anything not in `open/`, so a `graduated` item is invisible to it. Measured: it fires for `l6rh0z`, `tfx39h`, `y9lcem` and not for `xmqv5l`, `dh0uno`, `qyaime`. | `if f.parent.name != "open": continue` |
| F4 | HIGH | `oc_runipd.py` `main`, `except KeyboardInterrupt` | `SIGTERM` is not handled at all, so a `kill` of the runner runs no `except` and no `finally` and prints nothing. `SIGINT` is caught only as `KeyboardInterrupt`. | no `signal.signal` registration for the runner's own signals |
| F5 | MED | `oc_runipd.py` child-kill `_signal` escalation loop | The only `SIGINT`/`SIGTERM` constants in the runner are part of the escalating kill sequence for CHILD processes. Reusing that path for self-signal handling would be a category error; E-04 must add a separate handler. | source |
| F6 | HIGH | `oc_runipd.py` `execute_item` | LIVE CONCURRENT EDIT at review time: another session holds 9 uncommitted lines inside `execute_item`, adding `verify_log`/`verify_cost`/`verify_tokens` to the attempt record, and that is the SAME function E-02/E-03 must modify. Absolute line numbers in this plan are therefore already stale against the working tree, and an executor who edits from a remembered view will clobber that work. | `git diff -- agent_workflows/oc_runipd.py` shows the hunk; `git status` reports `M` |

## Proposed changes (ordered, validatable)

1. Read the link (E-01), so the runner knows an item exists.
2. Close only when every carrier is executed, through the setter, with evidence (E-02).
3. Gate on having earned the close, and fail closed (E-03).
4. Handle the runner's own `SIGINT` and `SIGTERM` (E-04).
5. Report what was left open, ledger first, on every catchable exit (E-05).
6. End with the `aw runs` pointer, suppressed for machine output (E-06).
7. Prove all of it, in both runners (E-07).

## Deferred / out of scope (with reason)

- Tightening the release-gate close predicate to require carriers be EXECUTED. Measured today: all three graduated items would be permitted to close `done` right now purely because a carrier exists, with no code written. That is a real defect but it is the predicate's problem, it is shared by the setter and the hook and `aw check`, and changing it would alter behavior for every caller. Separate plan.
- Fixing the `open/`-only warning (F3) so a graduated item is still nagged about. Complementary to this plan: this one closes items automatically, that one catches the ones automation misses. Separate, and in `check_engine.py`, which this plan does not touch.
- Closing an item when a human finalizes a plan by hand outside a run. The runner is the only actor that knows the moment the last carrier lands, and hand-finalizes have no run to report in.
- Closing items whose carriers are SPECS rather than plans. See OQ-01; deferred pending the maintainer's answer because a spec is design, not code, and closing on a spec would restate the false-completion problem `graduated` was created to fix.
- `SIGKILL`. Uncatchable by definition. The ledger write ordered before the print (E-05) is the mitigation, and `aw runs <run-id>` is the recovery path.

## Scope check

- Over-scope: none. Both runner modules carry F1 and F4; the test module is new and required by E-07.
- Under-scope: the close predicate, the `open/`-only warning, hand-run closes, spec carriers, and `SIGKILL` are each named under Deferred with a reason.

## Required tests / validation

- `tests/test_runner_backlog_close.py` must pass, with the close, no-close, signal-report, and pointer assertions each shown to FAIL against pre-fix code, and the symmetry assertion shown to fail when only one runner is changed.
- `tests/test_lane_session_isolation.py` must pass unchanged; it covers the same two runner modules.
- `python3 -m pytest -n auto` and `python3 -m pytest -m "" -n auto`. Baseline recorded at authoring: fast subset `2871 passed, 3 skipped, 4 xfailed`; full `4 failed, 3198 passed, 3 skipped, 4 xfailed`. Known-unrelated failures that must NOT be claimed as caused or fixed: `test_command_surface_declarations`, `test_cli_conformance_matrix` (x2), `test_cli` subparser descriptions, and `tests/test_run_viewer.py::test_run_viewer_cli_issues_flag` (reads the live run tree, so it is state-dependent while runners are active).
- A real end-to-end check: run a Set containing a plan that carries `From-Backlog`, confirm the item closes with the executed plan as evidence, and confirm `aw backlog check` and `aw attention` stay clean afterward.
- A signal check on a real run, not only a unit test: send `SIGTERM` to a live runner and paste the report, the pointer line, and the exit status.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- Spec `25kzda` section 3.4 covers the backlog dispatch and section 5.6 covers reporting; this plan implements the missing close-and-report behavior rather than changing specified behavior. The executor should record which of those sections are now genuinely satisfied.
- The installed agent contract states that `graduated` means design handed off and `done` means the code is written and validated. This plan makes the tooling enforce that boundary instead of leaving it to memory. If the contract text needs a sentence about automatic closure, that is a separate change to `engine.py`, which this plan does not touch.

## Open questions

### OQ-01: Should the runner close an item whose carriers are specs rather than plans?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: The shared helper returns specs as well as plans, so the runner will see them. My lean is NO: a spec is design, and closing an item because its design exists is exactly the false-completion the `graduated` status was introduced to prevent. But a spec-first graduation is explicitly legitimate elsewhere in the toolkit, and the close predicate accepts a spec as a gate carrier, so refusing here creates an item that automation can never close. This is the maintainer's call and the executor must not choose silently: it decides whether a spec-only item closes automatically, never closes, or is reported as permanently outstanding by E-05.

### OQ-02: Should the unclosed report also list items this run never touched?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. The report covers items this run touched, because a run reporting on the whole repository would duplicate `aw attention`, which already owns the cross-tree view. The E-06 pointer plus `aw attention` is the path to the wider picture; a run should be accountable for its own work only.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a frozen queue entry for a plan carrying `From-Backlog` showing the id6 recorded, and one for a plan without the field showing nothing recorded. Show both runners. Paste the reference to `ipd_schema.META_FROM_BACKLOG` proving no new regex was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the call into `check_engine.find_from_backlog_artifacts` proving reuse and the absence of a second lookup. Paste a closed item showing `Status: done` with the executed plan cited as evidence, and the setter invocation used. Paste an item left untouched because a carrier was unexecuted, with its recorded reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a run that executed no carrier for an item, showing the item unchanged. Paste an induced lookup failure and an induced setter failure, each showing the item untouched and a reason recorded rather than an exception escaping.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a real `SIGTERM` to a live run showing the report and exit status 143, and a real `SIGINT` showing the report and exit status 130. Paste a repeated-signal case showing no double-report and no hang. Paste evidence the child-kill path is unchanged (the existing escalation still runs).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the unclosed section from a normal exit and from both signal paths, each item with its reason. Paste the ledger record and show it was written before the print (for example by truncating output and showing the record still present). Paste a run with nothing outstanding showing no such section.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the final line of human output on normal exit and under both signals, showing ``Run `aw runs <run-id>` for more info.`` with the real id. Paste `--json` and `--agent` output showing the line absent and the output still parsing. Paste a grep proving the string `aw oc runs` appears nowhere.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the new module passing. Then paste falsifiability for the close, no-close, signal-report, and pointer assertions against pre-fix code, and the symmetry assertion failing with only one runner changed. Paste `tests/test_lane_session_isolation.py` unchanged, the fast and full suite results against the recorded baseline with the known-unrelated failures named and not claimed, and the real end-to-end run described under Required tests.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-01 is BLOCKING and must be answered before execution: it determines whether a spec-only carrier can close an item automatically.

Execution contract: commit ONLY the files in Scope-Paths, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`/bare/`-a`, and never push. Before every commit AND every retry, run `git diff --cached --name-only` and unstage anything not in Scope-Paths. The git index is SHARED mutable state in this checkout: a co-worker's `git add` can land between your check and your commit, which was observed this session, so a verification older than the commit attempt is worthless.

SEQUENCING: this plan declares `oc_runipd.py` and `agy_runipd.py`, which are also declared by in-flight plans `af7i6p`, `z2isfg`, and `8guhs0`. It declares `executed:af7i6p` so the tool-identity pin lands first; do not begin until those plans have cleared, and re-read both runner modules before editing rather than reusing a stale view. Keep the two runners symmetric: a one-runner fix is a defect and E-07 asserts against it.

CITATION DISCIPLINE (PR-001, and finding F6): every line number in this plan is a snapshot, not an address. `oc_runipd.py` moved twice during the hour this plan was written (`62810c3` then `c2e6ca3`), and at review time another session held UNCOMMITTED changes inside `execute_item`, the very function E-02/E-03 edit. Before editing, re-locate every target by SYMBOL (`except KeyboardInterrupt` in `main`, `execute_item`, `find_from_backlog_artifacts`) and re-run `git status`/`git diff` on both runner modules. If a co-worker's uncommitted work occupies the region you must change and the two edits cannot be safely combined, STOP and report rather than overwriting; that is the shared-checkout rule and this plan is unusually exposed to it.

Signal-handler discipline: handlers run at arbitrary points. Do not acquire the run lock, do not call `save_state`, and do not perform blocking I/O beyond the single ledger append and the print. Re-raise the original signal so the exit status stays conventional.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
