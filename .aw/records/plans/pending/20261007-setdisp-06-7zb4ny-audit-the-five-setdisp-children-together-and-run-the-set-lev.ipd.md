# IPD: Audit the five setdisp children together and run the Set-level checks

- Date: 2026-10-07
- Kind: child
- Concern: Orchestrator `63zo2f` (Set `setdisp`) lists Set-level checks that no single child can make: that each expected-difference assertion child 02 (`afdmn6`) records is flipped by exactly one later child; that no backlog carrier closed by children 03 and 05 was closed on a partial fix; that child 04's spec amendment landed in the same commit as its behavior; that the three retrospective parity files passed after every child; that no added test reads production source; the bare-suite failure set compared by name with the pre-Set baseline; and `aw check release-gates`. On 2026-10-06 the coverage probe refused `63zo2f` (sent back to `draft` by `gradcover` `52opph`) because those checks sat on the orchestrator, where a runner retirement marks them complete without anyone performing them. This plan performs them, after the last child.
- Scope: Measurement and reporting only. IN: run and record each Set-level check named in `63zo2f`'s Completion criteria and Cross-IPD validation, against the tree after children 01 to 05 have executed; report any failure plainly and stop the Set from being reported complete. OUT: fixing anything a check finds (a failure is reported, and the fix is a new plan); closing or editing any backlog item; editing any child plan.
- Scope-Paths: .aw/records/plans/pending/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.ipd.md
- Item-Dependencies: executed:afdmn6, executed:m1jlwm, executed:m94eht, executed:vhiqo6
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: chore
- Priority: medium
- From-Backlog: fcnz1r
- Set: setdisp
- Order: 6
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7zb4ny

## Workflow history
- 2026-10-07 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed
- 2026-10-07 /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005 (all fixed; E-07 added; record `.aw/records/reviews/20261007-setdisp-06-7zb4ny-audit-the-five-setdisp-children-together-and-run-the-set-lev.review.md`).
- 2026-10-07 to-review (aw set): returned to review: Set-level checks now owned by new Order 06 7zb4ny; coverage pass recorded; open questions are non-blocking executor measurements

- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored so the Set-level checks orchestrator `63zo2f` carried have an owner; the coverage probe quoted each of them as work no child covers.
- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Perform, after the last `setdisp` child executes, every Set-level check the orchestrator `63zo2f` lists, so the Set is declared complete only when each has been run and its evidence pasted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the child evidence

- [ ] E-01 For each of children `c6f6sj`, `afdmn6`, `m1jlwm`, `m94eht` and `vhiqo6`, confirm the plan is under `.aw/records/plans/executed/`, `aw ipd lint --phase post-transition --detail <path>` (run with `AW_NO_REEXEC=1`) reports conforming, and every `V-*` has non-empty `Observed evidence` and `Result: pass`. A `V-*` whose evidence is empty or only says it passed fails this check. Also record, for each child, its EXECUTION COMMIT and its INTEGRATION MERGE, found by trailer (`git log --format='%h %s' --grep 'AW-Item: <id6>'`; for `c6f6sj` at review these were `4d4966695` and merges `ce551c597`/`5041ef8bc`). E-04 and E-05 use these commits. If `m1jlwm` was instead retired to `superseded/` (orchestrator `63zo2f` OQ-02's alternative), its row records the superseded path and RETIRED header, and the plans that carried its fixes (`wdyz5n`, `ju3rhs`) are audited in its place.
  - Depends on: none
  - Expected outcome: a five-row table (child, executed path, lint result, count of `V-*` with pasted evidence out of total, execution commit, integration merge), every row complete.
  - Execution state: pending

### Task group 2: the cross-child checks

- [ ] E-02 NO AXIS FIXED TWICE OR BY NOBODY. Take the axis classification `afdmn6` RECORDED in its own V-04 evidence (eight candidates (a) to (h); at `afdmn6`'s review six were DIFFER and two reclassified to agreement, so the DIFFER count is read from its evidence, never assumed to be eight). For each DIFFER axis, name the plan whose evidence shows it flipped: a Set child (03 `m1jlwm`, 04 `m94eht`, 05 `vhiqo6`) or a named plan outside the Set (for example `wdyz5n` for the evidence gate, which may land before `m1jlwm`; `m1jlwm`'s own E-01 then only confirms). Each must be flipped by exactly one plan; any still unflipped must correspond to a spec `wy9aru` Section 7 axis with a live carrier (name it). Confirm the final `tests/test_set_dispatch_parity.py` agrees by running it.
  - Depends on: E-01
  - Expected outcome: one row per candidate axis (a) to (h), giving its classification at `afdmn6`, and for each DIFFER row exactly one flipping plan or a named live carrier; plus a passing run of `tests/test_set_dispatch_parity.py`.
  - Execution state: pending

- [ ] E-03 NO CARRIER CLOSED ON A PARTIAL FIX. Find every backlog item whose `- Status:` became `done` during the Set window (from the parent of `c6f6sj`'s execution commit to the tip; `git log -p <base>..HEAD -- .aw/records/backlog/` and the items' own `## Workflow history`), restricted to items a Set plan or a plan named in `63zo2f` touched. CORRECTED AT REVIEW: after their own reviews, `m1jlwm` closes nothing itself and `vhiqo6` closes nothing, so the expected set may be just `h4fiwa` and `fv4b6s`. For each closed item, quote its own stated scope and confirm the cited evidence covers all of it. For `h4fiwa` and `fv4b6s` (both `graduated` at review, to `wdyz5n` and `ju3rhs`, both `Blocks-Release: next`): report each as `done` via the HANDOFF route (its `From-Backlog` carrier executed) or the SATISFIED route (a resolvable `Close-Evidence`), with the `- Blocks-Release:` line intact, OR still `graduated` with its carrier plan's status named. A `graduated` item whose carrier is `executed` is reported, not fixed. Also confirm the Set closed none of `2wae2x`, `fnb8pl`, `lq2w86`.
  - Depends on: E-02
  - Expected outcome: per closed item, its scope quoted beside the evidence covering it and its close route; `h4fiwa` and `fv4b6s` each with status, route and gate line; `2wae2x`/`fnb8pl`/`lq2w86` status unchanged by any Set commit. Any partial close is reported as a failure.
  - Execution state: pending

- [ ] E-04 THE SPEC AMENDMENT TRAVELLED WITH ITS BEHAVIOR, AND NO TEST READS SOURCE. Show that child 04's amendment to spec `1525-02` R2 and its sidecar behavior change are in the same commit (`git show --stat <commit>` listing both `.aw/records/specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md` and `agent_workflows/status_set.py`), using the execution commit E-01 recorded; and that child 05's commits touch no `.spec.md`. List the test files the five children ADDED (`git diff --name-only --diff-filter=A <base>..HEAD -- tests/`, filtered to the children's commits), then search each for `import inspect`, `inspect.`, `ast.parse`, `read_text` or `open(` on a path under `agent_workflows/`, and caller-count or symbol-census assertions. Each hit is read and judged (a fixture file read is fine; a production-source read is a failure), not counted.
  - Depends on: E-03
  - Expected outcome: one commit listing both the spec and the behavior file; no `.spec.md` in child 05's commits; the added-test list, the search output, and a judgement per hit, with no production-source read.
  - Execution state: pending

### Task group 3: the whole tree

- [ ] E-05 THE THREE RETROSPECTIVE PARITY FILES PASSED AFTER EVERY CHILD. The three are `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_gate_follows_status.py` and `tests/test_status_set.py::TestGateFieldClearingOnStatusChange` (all three exist at the pre-Set commit, measured at review). CORRECTED AT REVIEW: the children do NOT all paste these files (executed `c6f6sj` contains none of the three names), so the per-child record must be MEASURED, not quoted. For each child, check out its execution commit (E-01) in a throwaway scratch worktree (`git worktree add --detach <scratch> <commit>`, removed afterwards) and run the three with `PYTHONPATH=<scratch> AW_NO_REEXEC=1 python3 -m pytest -o addopts="" -p no:cacheprovider <three ids>`; where a child DID paste them, quote that as well. Then run them once more at the current tree under two zones chosen so local and UTC dates differ at run time (`TZ=Pacific/Kiritimati` and `TZ=Etc/GMT+12`), and paste both.
  - Depends on: E-04
  - Expected outcome: five per-child pass records, each with the commit it was measured at, plus two current passing runs under the two skewed zones; the scratch worktrees removed (`git worktree list` pasted).
  - Execution state: pending

- [ ] E-06 THE BARE SUITE FAILURE SET. Run `python3 -m pytest` bare, paste the `N passed` line, and compare its failure SET by test id with the pre-Set baseline; any new id not named in advance by a child is a failure. CORRECTED AT REVIEW: executed `c6f6sj` records only a count (`3512 passed, 2 skipped` at `ec857565a`) and no failure set, so the baseline must be RE-DERIVED: run the bare suite at the parent of `c6f6sj`'s execution commit (`4d4966695~1` at review) in a throwaway scratch worktree with `PYTHONPATH=<scratch> AW_NO_REEXEC=1`, with `-rf` added so failing ids are listed (`python3 -m pytest -rf`), and run the current suite the same way. Because a test can be red only for part of a day (`63zo2f` and `c6f6sj` F-03), run both under the same `TZ` in one sitting.
  - Depends on: E-05
  - Expected outcome: both summary lines, both failure-id sets and their difference, with no unexplained new id; the scratch worktree removed.
  - Execution state: pending

- [ ] E-07 THE RELEASE GATES. Run `AW_NO_REEXEC=1 python3 -m agent_workflows check release-gates --agent` and paste it (at review it reported `conforms`, 0 findings). Any finding naming an item a Set plan touched is a failure; a finding on an unrelated item is reported and attributed.
  - Depends on: E-03
  - Expected outcome: `check release-gates` output pasted with no finding attributable to the Set.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR CARRIES NO WORK OF ITS OWN (`AGENTS.md`); a whole-Set check needs a child that runs after the others, which is this plan.
- RUN THE SUITE BARE (`AGENTS.md` execution contract).
- `AW_NO_REEXEC=1` keeps the measured package the one in the tree under test.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The checks were on the orchestrator, with no owner. | `63zo2f`'s Completion criteria and Cross-IPD validation; its 2026-10-06 coverage record quoting them as uncovered |
| F-02 | Only a plan that runs after all five children can make them. | each check compares or audits two or more children's results |
| F-03 | Three demands were not reachable from the children's evidence (found at review). | executed `c6f6sj` names none of the three parity files and records no failure set; `afdmn6`'s own review counts six DIFFER axes, not eight; `h4fiwa`/`fv4b6s` are `graduated` to `wdyz5n`/`ju3rhs` and close by HANDOFF, not the evidence route; `vhiqo6` closes no carrier after its review. E-02, E-03, E-05 and E-06 now measure what the evidence cannot supply. |

## Proposed changes (ordered, validatable)

1. Audit each child's evidence (E-01).
2. The three cross-child checks (E-02 to E-04).
3. Parity files, the whole suite and the release gates (E-05, E-06, E-07).

## Deferred / out of scope (with reason)

- FIXING WHAT A CHECK FINDS. This plan reports; a failure needs its own plan.
  - Carrier-Declined: measurement-only by design; a fix inside an audit would audit its own work

## Scope check

- Over-scope: none. Only this plan's own file is edited (its evidence). Scratch worktrees used by E-05 and E-06 are created outside the tracked tree and removed; they are not edits.
- Under-scope: none.

## Required tests / validation

Each E-item's commands, run and pasted as its V-item requires. No new test is written.

## Spec / documentation sync

None. This plan edits no spec or document.

## Open questions

### OQ-01: Should this be a child rather than the orchestrator's own checklist?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: a child. When the runner retires an orchestrator it skips the orchestrator's own checks, so they would be marked done without being run (`AGENTS.md`, spec `77tr3o` R-12). A child is executed and verified like any other plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the five-row table and, for each child, the lint command and its output, and the `git log --grep 'AW-Item: <id6>'` output that identified its commits.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the per-axis table (a) to (h) with, per row, `afdmn6`'s recorded classification quoted from its V-04, and for each DIFFER row the quoted evidence line from the flipping plan (or the live carrier's id6 and status); plus the pasted passing run of `tests/test_set_dispatch_parity.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git log` command and output that found the items closed in the Set window; per closed item, its quoted scope, the covering evidence and the close route; `grep -n '^- Status:\|^- Blocks-Release:\|^- Close-Evidence:'` for `h4fiwa`, `fv4b6s`, `2wae2x`, `fnb8pl` and `lq2w86`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git show --stat` for child 04's amendment commit, the list of child 05's commits with their changed paths, the added-test list, and the search output with a one-line judgement per hit.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste, per child, the commit, the scratch-worktree command and the three files' pytest summary; the two current runs with their `TZ` and pass counts; and `git worktree list` after cleanup.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the baseline commit, both `python3 -m pytest -rf` summary lines with their `TZ`, the baseline and current failure sets by id with their difference, and `git worktree list` after cleanup. Paste `aw ipd lint` on this plan conforming and `git diff --cached --name-only` before committing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted `check release-gates --agent` output, and for any finding the item id6 and whether a Set plan touched it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Measurement only: commit only this plan's own file (its evidence) through `aw commit <plan> -- <path>`; never push. Paste actual output for every `V-*`. A failed check is reported and the plan is NOT finalized as passing: record the `V-*` `Result: failed` and leave the plan in `pending/`, so orchestrator `63zo2f`'s E-06 cannot report the Set complete. The scope fence is a declaration, not a stop condition; an out-of-scope edit is justified with `--scope-reason` at finalize. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`; never hand-`git mv` the file.
