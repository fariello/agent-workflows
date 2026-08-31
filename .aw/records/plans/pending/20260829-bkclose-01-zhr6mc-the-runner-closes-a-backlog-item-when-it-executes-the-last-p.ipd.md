# IPD: the runner closes a backlog item when it executes the last plan and reports what it left open

- Date: 2026-08-29
- Kind: child
- Concern: A `graduated` backlog item has no owner for its final close. The runner never reads a plan's `From-Backlog:` link, so it cannot know an item is involved; no automation advances `graduated` to `done`; and the one warning that would nag only inspects `open/`, so a graduated item is invisible to it. No item has ever made the graduated-to-done trip.
- Scope: Teach both runners to read a plan's `From-Backlog:` link, close a backlog item when the run executes the last plan that carries it, report every item left open with the reason before exit on normal exit and on SIGINT and SIGTERM, and end the run output with a pointer to `aw runs <run-id>`. Excludes tightening the release-gate close predicate, excludes fixing the `open/`-only warning, and excludes closing items for hand-run plans.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_backlog_close.py
- Item-Dependencies: executed:af7i6p
- Status: approved
- Set: bkclose
- Order: 1
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: zhr6mc
- Approval: 2026-08-30, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): RECOVERY ATTEMPT 2, completing the plan. Attempt 1 was interrupted; its work survived as commit `42b38ac` on lane `aw/lane/zhr6mc`, which never reached `main`, and `main` then advanced 15 commits including FOUR that touch these same two runner modules (`bds6nd` exit-summary table, `ng2blv`, `9trlc3`, `rhszxj`). This attempt cherry-picked that work onto current `main` and resolved three conflicts per module, all in the exit path. Two were purely additive and both sides were kept. The third mattered: attempt 1 had REPLACED the whole `except KeyboardInterrupt` funnel with a SIGINT-only report, which would have deleted `bds6nd`'s landed summary table and its SIGTERM/143 handling; resolved by KEEPING `bds6nd`'s funnel and inserting the shared report call into it. THE SUBSTANTIVE CHANGE FROM ATTEMPT 1: E-05 is now COMPLETE and OQ-03 is RESOLVED rather than deferred. Attempt 1 could not deliver the SIGTERM half because four executed plans forbid `signal.signal(` in these two files (reserved for `71vjbn`). That boundary still stands and is still asserted, but `bds6nd` has since registered the SIGTERM handler in `render_stream` -- a module the guards do not cover -- so SIGTERM now raises `KeyboardInterrupt("Terminated by SIGTERM")` into the very funnel SIGINT already used. Verified with real signalled subprocesses: exit 143 on SIGTERM and 130 on SIGINT in BOTH drivers, each with the unclosed-item report, the `aw runs` pointer, and the ledger record, and a doubled signal reporting exactly once. Added `test_sigterm_produces_the_report_and_exits_143` and `test_the_sigterm_funnel_is_wired_in_both_drivers_main` (47 tests now, up from 45). ALL evidence was re-measured on the rebased tree rather than reused: fast suite 3686 passed / 15 failed vs a pre-fix baseline of 25 failed with `comm -13` EMPTY (zero newly broken); full marker set 4070 passed / 20 failed vs 36 pre-fix, also EMPTY; the 267-test guard sweep over all four `signal.signal` ownership suites plus `bds6nd`'s own suite passes, so the rebase broke none of them; falsifiability 43/47 fail pre-fix and a one-runner-only build fails 9. `aw ipd lint --phase pre-transition` now reports conforming, which is why this plan can legitimately move to `executed/` where attempt 1 correctly could not.
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): executed by `aw oc runipd` (run-20260830T202016Z-3474491). E-01/02/03/04/06/07/08 performed and validated with pasted evidence; E-05 PARTIAL. The runner now reads `From-Backlog`, closes an item when it executes the last carrier (IPD rule) or creates the artifact (non-IPD rule), gates the close on having EARNED it, fails closed on any lookup/read/setter failure, and reports every item left open with its reason before exit. Implemented ONCE in `oc_runipd` and IMPORTED by `agy_runipd` (object identity asserted) so the two cannot diverge. DECISIONS: (D1) the close uses the `--status done --evidence` form, NOT the positional `set done <sel>`, because the positional spelling routes to `status_set` and bypasses the shared release-gate close predicate entirely - verified live that it closed a release-blocking item with no evidence at exit 0; (D2) the item move is committed through the shared `git_commit_helper.offer_commit`, path-scoped and filtered by the item's id6, so the next turn does not inherit a dirty tree and a co-worker's other backlog item cannot be swept in; (D4) the earned-close set is derived from `git diff --name-only <start>..<end>` plus the finalized plan path, not from a model claim. DEFERRED (OQ-03): the `signal.signal` registration and with it the SIGTERM half belong to `runstop` Phase 5 (`71vjbn`) - four executed plans guard it and its handler semantics are the opposite of E-05's - so this plan supplies the handler-safe callable plus the SIGINT half through the existing `KeyboardInterrupt` funnel. THREE REAL BUGS were found by actually running the end-to-end close, each silently producing no commit (nonexistent-pathspec suppression, untracked-directory collapse, and a fixed-width porcelain slice eating the path's leading dot); all three are fixed and pinned. Fast suite 3620 passed with 15 failures, ALL pre-existing `test_run_viewer.py` (identical at HEAD); full suite shows ZERO newly-broken tests against a pre-fix baseline.
- 2026-08-30 approved (aw set): status set to approved
- 2026-08-30 approval-note (opencode its_direct/pt3-claude-opus-5-1m-us): approved by the maintainer's explicit instruction ("Approved. Go." then "Approve both"). NOT yet runnable: the declared edge `executed:af7i6p` is unsatisfied (af7i6p is approved in pending/), so `aw ipd lint --phase pre-execution` will refuse until af7i6p executes or the edge is deliberately cleared. Approval here records authority to run, not readiness to start.
- 2026-08-30 reviewed (aw set): status set to reviewed
- 2026-08-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003. PR-001 (HIGH, fixed): every absolute line citation was a snapshot, not an address. `oc_runipd.py` moved twice while this plan was being written (`62810c3`, then `c2e6ca3`), so `oc_runipd.py:3084-3086` was correct at HEAD when read but is already wrong against the working tree; replaced all brittle line anchors with SYMBOL anchors (`except KeyboardInterrupt` in `main`, `execute_item`, `find_from_backlog_artifacts`) and added a CITATION DISCIPLINE clause to the gate. PR-002 (HIGH, fixed): added finding F6 recording a LIVE concurrent edit: another session holds uncommitted changes inside `execute_item` (adding `verify_log`/`verify_cost`/`verify_tokens`), which is the SAME function E-02/E-04 must modify, so an executor working from a remembered view would clobber it. The gate now requires re-locating by symbol and re-running `git status`/`git diff` on both runner modules, and stopping rather than overwriting. PR-003 (HIGH, fixed): OQ-01 resolved by the maintainer, and my framing of it was wrong. The discriminator is not the carrier's TYPE but whether the item's output INCLUDES AN IPD: an item whose carriers include one or more IPDs is `graduated` and closes only when those IPDs execute; an item with NO IPD carrier is `done` as soon as the artifact EXISTS, even unreviewed and unapproved, because the item asked for creation and approval is the artifact's own lifecycle. Split the closing rule into E-02 (IPD rule) and a new E-03 (non-IPD rule), extended E-04's earned-close gate to both, added V-03 demanding a spec-only close while the spec is still `draft`/`to-review` plus a mixed spec+IPD case that must NOT close, renumbered to 8/8 E/V, and removed the now-stale deferral and the BLOCKING gate note. VERIFIED ACCURATE (no finding): `find_from_backlog_artifacts` exists and returns plans and specs; `ipd_schema.META_FROM_BACKLOG` is `From-Backlog`; both runners reference `From-Backlog` ZERO times; `release_gate_warnings` really does skip anything not in `open/`; the multi-carrier counts still hold (`xmqv5l` 1, `dh0uno` 2, `qyaime` 2); ZERO items in `done/` carry a graduation, so the transition has never occurred; and no item currently has spec-only carriers, so E-03 sets a rule before the case arises. Also verified the E-05 signal design is safe: `run_lock` uses `fcntl.flock`, which the OS releases on process death, so re-raising the signal cannot orphan the lock. Structural gate: `aw ipd lint --phase author` clean before review, `--phase review-finalize` conforming after revisions.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored at the maintainer's direction after we established that nothing closes a graduated backlog item. The maintainer added the exit-report requirement (E-06), the `aw runs` pointer (E-07), and the requirement that the report also fire on SIGINT and SIGTERM rather than only on `KeyboardInterrupt` (E-05).

## Goal

Close the loop the `graduated` status opened. When a run executes the last plan carrying a backlog item, close that item with the executed plan as evidence. When it cannot, say so before exiting so the human knows work remains.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: see the link, then close on the last plan

- [x] E-01 Read the plan's `From-Backlog:` value when the runner builds its plan record, and carry it on the frozen queue entry. Use the schema's existing field constant (`ipd_schema.META_FROM_BACKLOG`) rather than a new regex, so the runner and the checkers cannot disagree on the field name. Absent means no linked item. Do this in both runners.
  - Depends on: none
  - Expected outcome: a queue entry for a plan carrying `- From-Backlog: <id6>` records that id6; a plan without the field records nothing; both runners agree.
  - Execution state: performed

- [x] E-02 After a plan finalizes to `executed`, resolve every plan and spec that carries the same `From-Backlog` id6 by calling the existing shared helper `check_engine.find_from_backlog_artifacts`. Do not write a second lookup. PARTITION the carriers by kind, because the closing rule differs (OQ-01): if the carrier set includes ONE OR MORE IPDs, the item may close only when EVERY IPD carrier is in a terminal executed state; close it by invoking the lifecycle-owned setter (`aw backlog set done <item> --evidence <path to the executed plan>`), never by editing the item file directly. If any IPD carrier is not executed, do not close; record the reason.
  - Depends on: E-01
  - Expected outcome: an item whose only IPD carrier just executed is closed `done` with the executed plan cited as evidence; an item with an unexecuted IPD carrier is left untouched with a recorded reason.
  - Execution state: performed

- [x] E-03 Implement the NON-IPD closing rule (OQ-01, resolved): when an item's carrier set contains NO IPD, the item's requested output is the artifact itself, so it is `done` as soon as that artifact EXISTS. Close it without waiting for review or approval, citing the created artifact as evidence. A spec-only item therefore closes even while its specs are `draft` or `to-review`, because the item asked for the spec to be created and the spec's own approval is tracked by `aw specs`, not by the backlog item. Do not consult spec status; existence is the whole test. An item with NO carriers at all is not closed and is reported by E-06.
  - Depends on: E-02
  - Expected outcome: a spec-only item closes `done` with the spec cited as evidence even when the spec is unapproved; a mixed item carrying both a spec and an IPD does NOT close until the IPD is executed; an item with no carriers is not closed and appears in the report.
  - Execution state: performed

- [x] E-04 Gate the close on this run having executed the last carrier. A run must not close an item whose carriers it merely observed as already executed, because closing is a state change the run did not earn. This gate applies to BOTH closing rules (E-02 and E-03): a spec-only item closes only when THIS run created or executed that final artifact. Also fail closed: if the carrier lookup, the terminal-state read, or the setter invocation fails for any reason, leave the item alone and record the failure as a reason rather than proceeding.
  - Depends on: E-02, E-03
  - Expected outcome: a run that executed no carrier for an item closes nothing for it; an induced lookup or setter failure leaves the item untouched and produces a recorded reason.
  - Execution state: performed

### Task group 2: report before exit, on every catchable path

- [x] E-05 Install explicit handlers for `SIGINT` and `SIGTERM` in the runner process itself. Today `SIGINT` is caught only incidentally as `KeyboardInterrupt` at the `main` boundary (the `except KeyboardInterrupt` in `main`, HEAD line 3084 at review time; anchor on the SYMBOL, not the number, see PR-001) and `SIGTERM` has NO handler, so Python's default terminates immediately and no `except` or `finally` runs. Each handler must write the unclosed-item record to the run ledger first, then print the report, then re-raise the original signal so the exit status remains the conventional one (130 for `SIGINT`, 143 for `SIGTERM`) and any parent still observes a normal signal death. The handler must be idempotent, so a second signal during reporting neither double-prints nor deadlocks, and it must NOT acquire the run lock or call `save_state`; it reads only state already in memory. Do not alter the existing child-process termination path (the escalating `_signal` loop over `(signal.SIGINT, _SIGINT_GRACE_SECONDS)` / `(signal.SIGTERM, _SIGTERM_GRACE_SECONDS)` in the child-kill helper), which is separate and works.
  - Depends on: none
  - Expected outcome: `SIGTERM` to a live run produces the report and exits 143; `SIGINT` produces the report and exits 130; a repeated signal during reporting does not double-report; the child-kill behavior is unchanged.
  - Execution state: performed
  - Execution note: COMPLETE, and completed WITHOUT this plan calling `signal.signal` in either runner module (which four executed plans still forbid; see OQ-03, now closed). The required OUTCOME is what E-05 specified and it is met on both signals: ledger first, then the report, then the conventional exit status. HOW: executed plan `bds6nd` landed `render_stream.install_exit_signal_handler`, which registers the SIGTERM handler OUTSIDE the two guarded modules and raises `KeyboardInterrupt("Terminated by SIGTERM")`; both drivers' `main` already call it, and CPython already routes SIGINT to `KeyboardInterrupt`. So BOTH signals converge on the single `except KeyboardInterrupt` funnel, which emits the shared idempotent `emit_shutdown_report()` before returning 143 for SIGTERM and 130 for SIGINT. When this plan's first attempt ran, `bds6nd` had not landed and the SIGTERM half was genuinely unreachable, which is why the earlier attempt recorded it blocked; the deferral was correct THEN and is obsolete NOW. Idempotence uses a `threading.Event`, not a lock, so a repeated signal mid-report returns instead of deadlocking. The child-process kill escalation is untouched and pinned by `test_the_child_kill_escalation_path_is_unchanged`.

- [x] E-06 Print, immediately before exit, every backlog item this run touched but did not close, each with its reason (which carriers remain unexecuted, or that this run did not execute the last carrier, or the recorded failure from E-04). Emit on normal exit and from the E-05 handlers. Write the record to the ledger BEFORE printing, so an uncatchable kill still leaves the answer on disk. Print nothing when there is nothing outstanding.
  - Depends on: E-04, E-05
  - Expected outcome: a run leaving items open lists each with a reason on normal exit and under both signals; a run with nothing outstanding prints no such section; the ledger record exists even when the print is truncated.
  - Execution state: performed
  - Execution note: performed on every exit path that EXISTS today (normal exit in both drivers, and SIGINT via the existing funnel), with the ledger written before the print and the emitter idempotent. The SIGTERM path is not reachable until `71vjbn` registers the handler (OQ-03); the report content, ordering, and idempotence are complete and SHARED, so it gains SIGTERM coverage for free.

- [x] E-07 End the run output with the single line ``Run `aw runs <run-id>` for more info.`` using the run's actual id. The verb is `aw runs <run-id>`; `aw oc runs` does not exist and must not be emitted. Suppress the line in `--json` and `--agent` output so machine-readable output stays parseable.
  - Depends on: E-06
  - Expected outcome: the pointer is the last line of human output on normal exit and under both signals, naming the real run id; it is absent from `--json` and `--agent` output.
  - Execution state: performed

### Task group 3: prove it

- [x] E-08 Add `tests/test_runner_backlog_close.py` covering: a single-IPD-carrier item closes when its plan executes; a spec-only item closes on existence even while its spec is unapproved; a mixed spec-plus-IPD item does not close until the IPD executes; an item with no carriers is not closed and is reported; a two-carrier item does NOT close when only one executed; it DOES close when both have; the evidence argument names the real executed plan path; a run that executed no carrier closes nothing; an induced lookup or setter failure leaves the item untouched with a reason; the unclosed report lists each item with its reason on normal exit; the same report appears under `SIGINT` and under `SIGTERM` with exit codes 130 and 143; the ledger record precedes the print; a repeated signal does not double-report; the pointer line is last and names the real run id; the pointer is absent under `--json`. Include a symmetry assertion so a one-runner-only implementation fails. Each assertion must be shown to fail without the fix.
  - Depends on: E-01, E-02, E-04, E-05, E-06, E-07
  - Expected outcome: the module passes; the close, no-close, signal-report, and pointer assertions each fail against pre-fix code; the symmetry assertion fails when only one runner is changed.
  - Execution state: performed

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
| F5 | MED | `oc_runipd.py` child-kill `_signal` escalation loop | The only `SIGINT`/`SIGTERM` constants in the runner are part of the escalating kill sequence for CHILD processes. Reusing that path for self-signal handling would be a category error; E-05 must add a separate handler. | source |
| F6 | HIGH | `oc_runipd.py` `execute_item` | LIVE CONCURRENT EDIT at review time: another session holds 9 uncommitted lines inside `execute_item`, adding `verify_log`/`verify_cost`/`verify_tokens` to the attempt record, and that is the SAME function E-02/E-04 must modify. Absolute line numbers in this plan are therefore already stale against the working tree, and an executor who edits from a remembered view will clobber that work. | `git diff -- agent_workflows/oc_runipd.py` shows the hunk; `git status` reports `M` |

## Proposed changes (ordered, validatable)

1. Read the link (E-01), so the runner knows an item exists.
2. Close only when every carrier is executed, through the setter, with evidence (E-02).
3. Gate on having earned the close, and fail closed (E-04).
4. Handle the runner's own `SIGINT` and `SIGTERM` (E-05).
5. Report what was left open, ledger first, on every catchable exit (E-06).
6. End with the `aw runs` pointer, suppressed for machine output (E-07).
7. Prove all of it, in both runners (E-08).

## Deferred / out of scope (with reason)

- Tightening the release-gate close predicate to require carriers be EXECUTED. Measured today: all three graduated items would be permitted to close `done` right now purely because a carrier exists, with no code written. That is a real defect but it is the predicate's problem, it is shared by the setter and the hook and `aw check`, and changing it would alter behavior for every caller. Separate plan.
- Fixing the `open/`-only warning (F3) so a graduated item is still nagged about. Complementary to this plan: this one closes items automatically, that one catches the ones automation misses. Separate, and in `check_engine.py`, which this plan does not touch.
- Closing an item when a human finalizes a plan by hand outside a run. The runner is the only actor that knows the moment the last carrier lands, and hand-finalizes have no run to report in.
- `SIGKILL`. Uncatchable by definition. The ledger write ordered before the print (E-06) is the mitigation, and `aw runs <run-id>` is the recovery path.

## Scope check

- Over-scope: none. Both runner modules carry F1 and F4; the test module is new and required by E-08.
- Under-scope: the close predicate, the `open/`-only warning, hand-run closes, and `SIGKILL` are each named under Deferred with a reason. Spec carriers are NOT deferred: OQ-01 is resolved and E-03 implements the rule.

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

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the maintainer, and the rule is simpler than the question implied: the discriminator is NOT the carrier's type but WHETHER THE ITEM'S OUTPUT INCLUDES AN IPD. If an item's carriers include one or more IPDs, the item is `graduated` and closes only when those IPDs are executed, because an IPD is a promise of code that has not yet been written. If an item's carriers include NO IPD (specs only, or any other non-IPD artifact), the item's requested output is the artifact itself, so the item is `done` as soon as that artifact EXISTS. Explicitly: a spec-only item closes even if its specs are unreviewed and unapproved, because the item asked for a spec to be created, not for it to be approved; approval is the spec's own lifecycle and is tracked by `aw specs`, not by the backlog item. E-02 therefore partitions on carrier KIND, and this resolution is what E-03 implements. Measured while resolving: no backlog item in the repository currently has spec-only carriers, so this sets the rule before the case arises rather than changing behavior for existing items.

### OQ-02: Should the unclosed report also list items this run never touched?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. The report covers items this run touched, because a run reporting on the whole repository would duplicate `aw attention`, which already owns the cross-tree view. The E-07 pointer plus `aw attention` is the path to the wider picture; a run should be accountable for its own work only.

### OQ-03: Who owns the `signal.signal` registration E-05 asked this plan to install?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, and E-05 is complete without this plan registering anything. The question was recorded as DEFERRED by this plan's first attempt, on correct evidence at the time: FOUR EXECUTED plans install guards that forbid `signal.signal(` in exactly these two runner modules and assign that registration to `runstop` Phase 5 (`71vjbn`) (`tests/test_lane_allocation_idempotent.py`, `tests/test_runner_stop.py`, `tests/test_runner_stop_level3.py`, `tests/test_runner_stop_level4.py`), one of them stating the split verbatim: "`runstop` Phase 5 (`71vjbn`, approved) OWNS SIGINT/SIGTERM registration in these same two files ... whichever plan registered last would silently win. This plan supplies the callable those handlers will invoke, and installs none itself." Those designs are genuinely incompatible with E-05's: `71vjbn` requires SIGINT to ESCALATE level 1 -> 3 -> 4 and SIGTERM to REQUEST LEVEL 3, whereas E-05 wanted report-then-die. Measured then: installing the handlers broke exactly those 5 guards (21 -> 26 failures).
WHAT CHANGED IS THE FACTS, NOT THE OWNERSHIP. Between that attempt and this one, plan `bds6nd` was executed and landed `render_stream.install_exit_signal_handler`, which registers the SIGTERM handler in `render_stream` -- a module the guards do NOT cover -- and raises `KeyboardInterrupt("Terminated by SIGTERM")`. Both drivers' `main` already call it. CPython already routes SIGINT to `KeyboardInterrupt`. So both signals now converge on the ONE `except KeyboardInterrupt` funnel, and emitting the shared idempotent report there satisfies E-05's required outcome (report on both signals, ledger first, conventional 130/143) with no registration in the guarded files at all.
The boundary the guards protect therefore still holds and is still asserted: `test_the_registration_is_left_to_its_owner` continues to require that `signal.signal(` appear in NEITHER runner module, so `71vjbn` remains free to design its escalation ladder. The difference is that this plan no longer has an incomplete requirement waiting on it. Verified with real signalled subprocesses in both drivers: exit 143 on SIGTERM and 130 on SIGINT, each with the report, the pointer, and the ledger record (pasted under V-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a frozen queue entry for a plan carrying `From-Backlog` showing the id6 recorded, and one for a plan without the field showing nothing recorded. Show both runners. Paste the reference to `ipd_schema.META_FROM_BACKLOG` proving no new regex was introduced.
  - Observed evidence: FROZEN QUEUE ENTRIES, both drivers (real `initialize_run` on a temp repo with two plans, one carrying the field):
```
  oc_runipd: id6=aaaaaa from_backlog='bbbbbb'
  oc_runipd: id6=cccccc from_backlog=None
  agy_runipd: id6=aaaaaa from_backlog='bbbbbb'
  agy_runipd: id6=cccccc from_backlog=None
```
NO NEW REGEX: `_read_from_backlog` (oc_runipd.py, symbol anchor) resolves the field name through `ipd_schema.META_FROM_BACKLOG` via `ipd_lint.parse(text).meta_fields`, the same structural reader `_read_item_dependencies` uses. `agy_runipd` IMPORTS the function (object identity asserted). `grep -n 're.compile([^)]*From-Backlog'` over both drivers returns nothing; `test_no_new_regex_the_field_name_comes_from_the_schema` pins this.
Pre-fix contrast: `grep -c "From-Backlog" agent_workflows/oc_runipd.py` == 0 at HEAD, and both `test_both_drivers_read_the_link_into_the_plan_record` and `test_the_link_is_frozen_on_the_queue_entry` FAIL there.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the call into `check_engine.find_from_backlog_artifacts` proving reuse and the absence of a second lookup. Paste the carrier partition by kind. Paste a closed item showing `Status: done` with the executed plan cited as evidence, and the setter invocation used. Paste an item left untouched because an IPD carrier was unexecuted, with its recorded reason.
  - Observed evidence: SHARED LOOKUP REUSED, no second implementation: `evaluate_backlog_close` calls `check_engine.find_from_backlog_artifacts(repo, item_id6)`; `grep -c "def find_from_backlog"` over both drivers == 0 (`test_the_shared_lookup_is_reused_not_reimplemented`).
CARRIER PARTITION BY KIND: `ipds = [p for p in carriers if _carrier_kind(p) == CARRIER_KIND_IPD]` / `others = [...CARRIER_KIND_OTHER]`.
REAL CLOSE, end to end (scratch repo, real setter, item carried `Blocks-Release: next`):
```
{"item": "aaa111", "closed": true,
 "reason": "every IPD carrier is executed and this run executed .aw/records/plans/executed/20260830-demo-01-bbb222-a-plan.ipd.md",
 "rule": "ipd", "evidence": ".aw/records/plans/executed/20260830-demo-01-bbb222-a-plan.ipd.md",
 "commit": "75cc05e0d0daab15ba0e168b2ee0917ac797d600"}
```
The item MOVED graduated/ -> done/, kept `- Status: done` AND `- Blocks-Release: next` (gate preserved, not dropped), and the move was committed path-scoped with both sides and nothing else; `git status --porcelain -uall -- .aw/records/backlog` afterwards is EMPTY.
SETTER FORM (decision D1, recorded): the argv is `backlog set <id6> --status done --evidence <carrier> --message ... --no-commit`, NOT the positional `set done <id6>`. Measured live: the positional form routes to `status_set.run_set_command`, which does NOT run `check_engine.evaluate_blocking_close` and cannot accept `--evidence` (it closed a release-blocking item with no evidence, exit 0), while the `--status` form was REFUSED with the three fixes. `test_the_close_uses_the_status_form_which_runs_the_release_gate_predicate` pins the gated form and rejects the ungated one.
ITEM LEFT UNTOUCHED when a carrier is unexecuted, with the reason naming it. Against the LIVE repo's three real graduated items:
```
qyaime -> False | IPD carrier(s) not executed: .aw/records/plans/pending/20260828-wtiso-00-bl9q3d-...
dh0uno -> False | IPD carrier(s) not executed: .aw/records/plans/pending/20260828-wtiso-04-7p9n2v-...
xmqv5l -> False | IPD carrier(s) not executed: .aw/records/plans/pending/20260828-wtiso-03-rchpms-...
```
No item file is ever written by this path: `test_the_item_file_is_never_edited_directly` bans `write_text`/`atomic_write`/`unlink`/`replace(` in the close code.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a spec-only item closing `done` with the spec cited as evidence WHILE that spec is still `draft` or `to-review`, proving approval is not required and that spec status was not consulted. Paste a MIXED item (one spec plus one IPD) NOT closing while the IPD is unexecuted, proving the IPD rule dominates. Paste an item with no carriers showing it was not closed and does appear in the E-06 report.
  - Observed evidence: SPEC-ONLY CLOSE WHILE UNAPPROVED: `test_spec_only_item_closes_on_existence_even_while_unapproved` closes an item whose only carrier is a `- Status: draft` spec, with that spec cited as evidence and `rule == "other"`; the reason ends "(no IPD carrier, so approval is not required)".
SPEC STATUS IS NEVER CONSULTED: `test_spec_status_is_never_consulted` runs the same fixture at `draft`, `to-review`, AND `approved` and asserts an IDENTICAL close verdict, plus a code-only guard that `evaluate_backlog_close` contains no `spec_status`. Existence is the whole test (`existing = [p for p in others if p.is_file()]`).
MIXED spec+IPD does NOT close: `test_mixed_spec_plus_ipd_does_not_close_until_the_ipd_executes` asserts `close is False` with "not executed" in the reason, proving the IPD rule dominates (the `if ipds:` branch returns before the non-IPD rule is reached).
NO CARRIERS: `test_item_with_no_carriers_is_not_closed` -> reason "no plan or spec carries From-Backlog: bbbbbb, so no carrier proves the work", and `unclosed_backlog_items` surfaces it in the E-06 report.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste a run that executed no carrier for an item, showing the item unchanged. Paste an induced lookup failure and an induced setter failure, each showing the item untouched and a reason recorded rather than an exception escaping.
  - Observed evidence: NOT EARNED: `test_a_run_that_executed_no_carrier_closes_nothing` -> "this run executed none of its carriers, so the close was not earned (all carriers were already executed before this run)" even though every carrier IS executed. `test_the_gate_applies_to_the_non_ipd_rule_too` proves the same gate applies to the spec-only rule.
INDUCED LOOKUP FAILURE: `test_an_induced_lookup_failure_leaves_the_item_untouched` monkeypatches `check_engine.find_from_backlog_artifacts` to raise; verdict is `close=False`, reason "carrier lookup failed: induced carrier lookup failure", no exception escapes, and the item is still in `graduated/`.
INDUCED TERMINAL-STATE READ FAILURE: `test_an_induced_terminal_state_read_failure_fails_closed` -> "terminal-state read failed for <path>: ...".
INDUCED SETTER FAILURE: `test_an_induced_setter_failure_leaves_the_item_untouched_with_a_reason` -> record `closed=False`, reason "setter refused the close: aw backlog set: refused: induced setter failure", item still `graduated`, and a `backlog-close-refused` ledger event.
EARNED SET DERIVED FROM GIT, not from a model claim: `collect_earned_paths` uses `git diff --name-only <starting_head>..<ending_head>` per attempt plus the finalized plan path (decision D4).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a real `SIGTERM` to a live run showing the report and exit status 143, and a real `SIGINT` showing the report and exit status 130. Paste a repeated-signal case showing no double-report and no hang. Paste evidence the child-kill path is unchanged (the existing escalation still runs).
  - Observed evidence: COMPLETE on both signals. The earlier attempt recorded the SIGTERM half BLOCKED, and that was correct at the time; executed plan `bds6nd` has since landed `render_stream.install_exit_signal_handler`, which registers SIGTERM OUTSIDE the two guarded runner modules and raises `KeyboardInterrupt("Terminated by SIGTERM")`. Both drivers' `main` already call it, so SIGTERM now reaches the same funnel SIGINT always did and E-05's required outcome is met without this plan registering anything.
REAL SIGNALS TO REAL SUBPROCESSES, both drivers, using the EXACT two lines real `main` uses (`install_exit_signal_handler()` then the `except KeyboardInterrupt` funnel):
```
========================= oc_runipd SIGTERM =========================
EXIT CODE: 143 (expected 143 )
--- stderr ---

--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
Run `aw runs run-sigterm-test` for more info.
Terminated by SIGTERM; durable run state was preserved.

--- ledger ---
{"at": "2026-08-31T00:11:46+00:00", "event": "backlog-items-left-open", "items": [{"item": "bbbbbb", "reason": "IPD carrier(s) not executed: x.ipd.md"}]}

========================= oc_runipd SIGINT =========================
EXIT CODE: 130 (expected 130 )
--- stderr ---

--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
Run `aw runs run-sigterm-test` for more info.
Interrupted; durable run state was preserved.

--- ledger ---
{"at": "2026-08-31T00:11:46+00:00", "event": "backlog-items-left-open", "items": [{"item": "bbbbbb", "reason": "IPD carrier(s) not executed: x.ipd.md"}]}

========================= agy_runipd SIGTERM =========================
EXIT CODE: 143 (expected 143 )
--- stderr ---

--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
Run `aw runs run-sigterm-test` for more info.
Terminated by SIGTERM; durable run state was preserved.

--- ledger ---
{"at": "2026-08-31T00:11:46+00:00", "event": "backlog-items-left-open", "items": [{"item": "bbbbbb", "reason": "IPD carrier(s) not executed: x.ipd.md"}]}

========================= agy_runipd SIGINT =========================
EXIT CODE: 130 (expected 130 )
--- stderr ---

--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
Run `aw runs run-sigterm-test` for more info.
Interrupted; durable run state was preserved.

--- ledger ---
{"at": "2026-08-31T00:11:46+00:00", "event": "backlog-items-left-open", "items": [{"item": "bbbbbb", "reason": "IPD carrier(s) not executed: x.ipd.md"}]}

========================= REPEATED SIGINT (idempotence) =========================
EXIT CODE: 130
pointer occurrences: 1
report-header occurrences: 1
--- stderr ---

--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
Run `aw runs run-sigterm-test` for more info.
Interrupted; durable run state was preserved.

```
Exit status is the conventional one in all four cases: **143** for SIGTERM and **130** for SIGINT, in BOTH drivers, each with the unclosed-item section, the `aw runs` pointer, and the ledger record on disk.
PINNED BY TESTS, so this cannot silently regress: `test_sigterm_produces_the_report_and_exits_143` and `test_sigint_produces_the_report_and_exits_130` drive real signalled subprocesses across both drivers; `test_the_sigterm_funnel_is_wired_in_both_drivers_main` asserts each `main` still calls `install_exit_signal_handler()` and still returns 143; `test_both_drivers_report_from_their_keyboardinterrupt_funnel` is AST-structural, so a one-driver fix fails.
IDEMPOTENT under repeat, measured on a real doubled signal (`pointer occurrences: 1`, `report-header occurrences: 1` in the log above) and unit-pinned by `test_the_report_is_idempotent_under_a_repeated_signal`, which calls the emitter 3x and asserts the ledger is byte-identical after the first. A `threading.Event` is used rather than a lock precisely so a handler can never block.
HANDLER-SAFE, verified by a code-only guard: `test_the_callable_is_handler_safe` bans `run_lock`/`locked_run`/`save_state`/`flock` in the report path, so `71vjbn` can call `signal_report_callback()` from a real handler unchanged.
CHILD-KILL PATH UNCHANGED: `test_the_child_kill_escalation_path_is_unchanged` asserts `terminate_process` still carries `_SIGINT_GRACE_SECONDS`/`_SIGTERM_GRACE_SECONDS` and never references the report; the diff touches neither `terminate_process` nor `runner_shutdown.py`.
REGISTRATION BOUNDARY STILL HELD: `test_the_registration_is_left_to_its_owner` still asserts `signal.signal(` appears in NEITHER runner module, so `71vjbn`'s escalation ladder is not pre-empted.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the unclosed section from a normal exit and from both signal paths, each item with its reason. Paste the ledger record and show it was written before the print (for example by truncating output and showing the record still present). Paste a run with nothing outstanding showing no such section.
  - Observed evidence: EACH ITEM WITH ITS REASON, normal exit: `render_unclosed_report` emits
```
--- Backlog items left open ---
  - bbbbbb: IPD carrier(s) not executed: x.ipd.md
  (this run's own items only; `aw attention` owns the cross-tree view)
```
and is wired into BOTH drivers' `run_queue` before the exit-code return (`test_both_drivers_emit_the_shutdown_report_on_normal_exit`, which also fails if only one driver is changed).
UNDER BOTH SIGNALS: the same section, from real signalled subprocesses in both drivers, at exit 130 (SIGINT) and 143 (SIGTERM) (pasted in full under V-05).
NOTHING OUTSTANDING -> NO SECTION: `test_a_run_with_nothing_outstanding_prints_no_section` asserts `render_unclosed_report(...) == ""` once the item closed.
LEDGER BEFORE PRINT, asserted STRUCTURALLY not by comment: `test_the_ledger_record_is_written_before_the_print` walks the AST of `emit_shutdown_report` and requires the `record_unclosed_backlog_items` call to precede the first `print`. `test_the_ledger_record_survives_when_the_print_is_discarded` shows the record on disk with no output captured at all:
```
{"at": "...", "event": "backlog-items-left-open", "items": [{"item": "bbbbbb", "reason": "IPD carrier(s) not executed: x.ipd.md"}]}
```
NEVER SILENTLY ABSENT: an item whose plan never reached the close evaluation is still reported, with the plan's fate as the reason (`test_an_item_whose_plan_never_reached_the_close_is_still_reported`, reason contains "partial"). A plan with no linked item contributes nothing.
ALL THREE EXIT PATHS are now covered: normal exit, SIGINT, and SIGTERM. The SIGTERM emission was deferred with E-05 by this plan's first attempt and is now delivered, because executed plan `bds6nd` funnels SIGTERM into the same `except KeyboardInterrupt` path (see OQ-03); the content, ordering, and idempotence are shared by all three paths, so they cannot drift.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the final line of human output on normal exit and under both signals, showing ``Run `aw runs <run-id>` for more info.`` with the real id. Paste `--json` and `--agent` output showing the line absent and the output still parsing. Paste a grep proving the string `aw oc runs` appears nowhere.
  - Observed evidence: FINAL LINE, human output, real run id (live run of THIS execution):
```
02 71vjbn runstop      execute  queued               attempts=0
Run `aw runs run-20260830T202016Z-3474491` for more info.
```
UNDER BOTH SIGNALS: pasted under V-05, `Run \`aw runs run-signal-test\` for more info.` as the last report line, in both drivers, on SIGINT (130) and SIGTERM (143).
`--json` SUPPRESSED AND STILL PARSES:
```
JSON PARSES OK, run_id = run-20260830T202016Z-3474491
pointer absent from json: True
```
`test_json_output_suppresses_the_pointer` asserts this structurally (AST) for BOTH drivers' `main`, so the suppression cannot regress. `--agent` is not a flag either runner exposes (it forwards `--agent <name>` to the child agent, a different meaning), so there is no separate agent-mode emission to suppress; the JSON branch is the machine-readable surface.
`aw oc runs` APPEARS NOWHERE: `grep -n "aw oc runs " agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returns nothing, pinned by `test_the_string_aw_oc_runs_appears_nowhere_in_either_driver`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the new module passing. Then paste falsifiability for the close, no-close, signal-report, and pointer assertions against pre-fix code, and the symmetry assertion failing with only one runner changed. Paste `tests/test_lane_session_isolation.py` unchanged, the fast and full suite results against the recorded baseline with the known-unrelated failures named and not claimed, and the real end-to-end run described under Required tests.
  - Observed evidence: RE-MEASURED IN FULL on the current tree. This plan's first attempt was interrupted, and `main` advanced by 15 commits underneath it (including `bds6nd`, `ng2blv`, `9trlc3`, `rhszxj`, which all touch these two runner modules), so every number below was taken again after rebasing the work onto current `main` and resolving three real conflicts per module. The stale first-attempt figures are deliberately NOT reused.
NEW MODULE PASSES (47 tests; 45 from the first attempt plus the two new SIGTERM assertions), together with the untouched lane suite and, importantly, all four `signal.signal` OWNERSHIP-GUARD suites and `bds6nd`'s own summary-table suite, which is the regression risk this rebase actually carries:
```
$ python3 -m pytest tests/test_runner_backlog_close.py tests/test_lane_session_isolation.py \
    tests/test_runner_stop.py tests/test_runner_stop_level3.py tests/test_runner_stop_level4.py \
    tests/test_lane_allocation_idempotent.py tests/test_lane_tool_identity.py \
    tests/test_run_summary_table.py -o addopts="" -q
267 passed in 68.88s (0:01:08)
```
FALSIFIABILITY, against pre-fix code (a clean `git archive HEAD` tree plus ONLY this test file):
```
$ cd /tmp/opencode/prefix2 && python3 -m pytest tests/test_runner_backlog_close.py -o addopts="" -q
43 failed, 4 passed in 1.40s
```
The close, no-close, earned-gate, gated-setter, pointer, AND BOTH signal-report assertions fail without the fix, confirmed by name:
```
test_sigterm_produces_the_report_and_exits_143     FAILED (pre-fix)
test_sigint_produces_the_report_and_exits_130      FAILED (pre-fix)
test_the_pointer_names_the_real_run_id_and_the_real_verb  FAILED (pre-fix)
test_json_output_suppresses_the_pointer            FAILED (pre-fix)
```
The 4 that pass pre-fix are the deliberate NEGATIVE/BOUNDARY guards, each true pre-fix by construction: `test_the_registration_is_left_to_its_owner` (no `signal.signal` in either runner), `test_the_child_kill_escalation_path_is_unchanged`, `test_the_sigterm_funnel_is_wired_in_both_drivers_main` (satisfied by `bds6nd` alone), and `test_agy_does_not_redefine_any_of_the_shared_functions`.
SYMMETRY, a one-runner-only fix must fail (HEAD tree + ONLY `oc_runipd.py` from this change):
```
$ cd /tmp/opencode/sym2 && python3 -m pytest tests/test_runner_backlog_close.py -o addopts="" -q
9 failed, 38 passed in 2.54s
FAILED ...::SharedNotCopied::test_the_implementation_is_shared_not_copied
FAILED ...::SharedNotCopied::test_both_drivers_expose_the_backlog_close_api
FAILED ...::SharedNotCopied::test_both_drivers_call_the_close_from_their_finalize_success_branch
FAILED ...::SharedNotCopied::test_both_drivers_emit_the_shutdown_report_on_normal_exit
FAILED ...::ReadsTheFromBacklogLink::test_both_drivers_read_the_link_into_the_plan_record
FAILED ...::ReadsTheFromBacklogLink::test_the_link_is_frozen_on_the_queue_entry
FAILED ...::ShutdownReportOnInterrupt::test_sigterm_produces_the_report_and_exits_143
FAILED ...::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
FAILED ...::ShutdownReportOnInterrupt::test_both_drivers_report_from_their_keyboardinterrupt_funnel
```
`tests/test_lane_session_isolation.py` is UNCHANGED (it does not appear in `git status`) and passes, as part of the 267 above.
FAST SUITE, bare per the execution contract, differenced against the SAME bare command on a pre-fix `git archive HEAD` tree:
```
$ python3 -m pytest                          -> 15 failed, 3686 passed, 3 skipped, 4 xfailed in 30.95s
pre-fix baseline (same bare command)         -> 25 failed, 3629 passed, 3 skipped, 4 xfailed in 30.73s
$ comm -13 base_ids.txt now_ids.txt          -> (empty)
```
ZERO newly-broken tests. All 15 remaining failures are `tests/test_run_viewer.py`, the KNOWN-UNRELATED state-dependent suite this plan named in advance (it reads the LIVE run tree, and a runner is active right now). Proven not mine by running that file alone on the pre-fix tree: `15 failed, 21 passed`, the same 15. I claim neither to have caused nor fixed them. The 10 that the baseline fails and this tree does not are artifacts of the baseline being an extracted archive rather than a git repository (`test_doctor`, `test_local_leaks` working-tree-clean, `test_untracked_lane_migration`, `test_git_commit_helper`), NOT fixes by this change, and I do not claim them.
FULL MARKER SET (`-m ""`), same differencing:
```
$ python3 -m pytest -m ""                    -> 20 failed, 4070 passed, 3 skipped, 4 xfailed in 100.26s
pre-fix baseline (same command)              -> 36 failed, 4007 passed, 3 skipped, 4 xfailed in 78.03s
$ comm -13 basef.txt nowf.txt                -> (empty)
```
ZERO newly-broken tests here either. The remaining set is the pre-existing `run_viewer`, `command_surface`/`cli_conformance`, and `runner_stop` slow/fixture failures the plan named as known-unrelated.
REAL END-TO-END CLOSE (real setter, real git, real move), pinned as executable tests rather than a one-off transcript, all passing on this tree: `test_a_real_close_moves_the_item_to_done_with_evidence` (graduated -> done, `- Status: done` written, `- Blocks-Release: next` PRESERVED, evidence = the executed plan path), `test_the_move_is_committed_path_scoped_and_leaves_the_tree_clean`, `test_a_coworkers_other_backlog_item_is_never_swept_in`, `test_the_close_is_recorded_in_the_run_ledger`, `test_the_close_uses_the_status_form_which_runs_the_release_gate_predicate`:
```
$ python3 -m pytest tests/test_runner_backlog_close.py -o addopts="" -q -k "real_close or committed_path_scoped or coworkers or recorded_in_the_run_ledger or status_form"
5 passed, 42 deselected in 1.13s
```
REAL SIGNALS: pasted in full under V-05 (exit 143 on SIGTERM and 130 on SIGINT, both drivers, with report + pointer + ledger).
THREE REAL BUGS FOUND BY RUNNING THE END-TO-END CHECK, each of which silently produced no commit, now fixed and pinned by `test_the_move_is_committed_path_scoped_and_leaves_the_tree_clean`: (1) naming a nonexistent backlog root made `git status` exit nonzero, which this path suppresses; (2) default `--porcelain` collapsed the untracked side to the DIRECTORY, whose basename carries no id6; (3) `run_checked` strips output, so `" D <path>"` arrived as `"D <path>"` and a fixed `line[3:]` slice ate the path's leading `.`.
REPOSITORY CHECKERS, each differenced against the pre-fix tree so a pre-existing violation is not mis-attributed:
```
$ python3 -m agent_workflows attention --check      -> aw attention --check: the view is valid.
$ python3 -m agent_workflows backlog check          -> aw backlog check: 3 violation(s).
   pre-fix baseline (same command)                  -> aw backlog check: 3 violation(s).   [the SAME 3]
```
The 3 are pre-existing `backlog.summary-unsafe` findings on unrelated items (`uhbdt1`, `f7w55w`, `av9hni`); not caused by this change and not claimed as fixed.
LEAK SANITIZER CLEAN:
```
$ python3 -m agent_workflows check-local-leaks . --agent
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files in Scope-Paths, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`/bare/`-a`, and never push. Before every commit AND every retry, run `git diff --cached --name-only` and unstage anything not in Scope-Paths. The git index is SHARED mutable state in this checkout: a co-worker's `git add` can land between your check and your commit, which was observed this session, so a verification older than the commit attempt is worthless.

SEQUENCING: this plan declares `oc_runipd.py` and `agy_runipd.py`, which are also declared by in-flight plans `af7i6p`, `z2isfg`, and `8guhs0`. It declares `executed:af7i6p` so the tool-identity pin lands first; do not begin until those plans have cleared, and re-read both runner modules before editing rather than reusing a stale view. Keep the two runners symmetric: a one-runner fix is a defect and E-08 asserts against it.

CITATION DISCIPLINE (PR-001, and finding F6): every line number in this plan is a snapshot, not an address. `oc_runipd.py` moved twice during the hour this plan was written (`62810c3` then `c2e6ca3`), and at review time another session held UNCOMMITTED changes inside `execute_item`, the very function E-02/E-04 edit. Before editing, re-locate every target by SYMBOL (`except KeyboardInterrupt` in `main`, `execute_item`, `find_from_backlog_artifacts`) and re-run `git status`/`git diff` on both runner modules. If a co-worker's uncommitted work occupies the region you must change and the two edits cannot be safely combined, STOP and report rather than overwriting; that is the shared-checkout rule and this plan is unusually exposed to it.

Signal-handler discipline: handlers run at arbitrary points. Do not acquire the run lock, do not call `save_state`, and do not perform blocking I/O beyond the single ledger append and the print. Re-raise the original signal so the exit status stays conventional.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
