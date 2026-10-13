# IPD: Refuse to merge a lane that makes a spec line pointer stale

- Date: 2026-10-12
- Kind: child
- Concern: Code comments point into specs by line number ("spec `25kzda` :744"). When a spec is edited the line moves and the pointer goes stale. The detector (`spec_citations.stale_spec_anchors`, rule `check.spec-anchor-stale`) is opt-in and runs only on `aw check --source-anchors`, so stale pointers pile up until a plan sweeps them (`mt54wr`, `atpvao`). Plan `l85xvi` proposed failing CI on them, but CI is not watched (red for 1,623 main commits at review), so the maintainer chose to catch them where the change is made: at the runner's merge check, before a lane reaches main.
- Scope: At the runner's lane-integration step (where `orchestrate_isolation.execute_merge_and_revalidate_gate` already re-validates a lane before it is merged), run `spec_citations.stale_spec_anchors` on the lane tree and on the lane's base commit, and refuse the merge only when the lane has stale pointers that its base did not (new findings, keyed by file, spec id6 and the cited construct, not by line number, so moved lines do not count as new). The refusal goes back to the agent as a fix-it turn through the existing correction path, naming each new stale pointer. Pre-existing stale pointers never block; Order 02's checkup reports them. The detector's accuracy fixes are plan `fz3i3m`'s (Set `sbh1o1`); this plan depends on it.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/orchestrate_isolation.py, agent_workflows/spec_citations.py, tests/test_merge_gate_spec_anchors.py, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:fz3i3m
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 4
- Highest E allocated: 05
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: mnwkqu
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 fixed.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix; replaces plan l85xvi's CI step per the maintainer's 2026-10-12 ruling.
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A lane that makes a spec line pointer stale is not merged until its agent fixes the pointer, so new stale pointers stop reaching main, at the cost of two detector scans (about 2.1s each, measured at review HEAD `bd4c7874e`) only on merges whose lane changed a spec or a scanned `.py` file, and no cost to any other merge.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new-findings comparison

- [ ] E-01 Add `spec_citations.new_stale_anchors(repo, lane_commit, base_commit)` returning a small typed result (`status` one of `new`/`none`/`unknown`, the list of new findings, and a reason). (1) SHORT-CIRCUIT: if `git diff --name-only base_commit lane_commit` names no `.spec.md` file and no `.py` file under the scan roots, return `none` without scanning (findings cannot differ when neither side's inputs changed). (2) Otherwise evaluate BOTH sides at COMMITS, never at a live working tree (a preserved lane's handle can carry `path=Path("")` and a live lane tree can hold uncommitted files): materialize each commit with `git worktree add --detach <tmpdir> <commit>`, outside every tracked path, and remove it in a `finally` with `git worktree remove --force` plus `git worktree prune`. (3) Scan the SAME roots the `aw check --source-anchors` branch in `cli._run_check` scans (`agent_workflows`, `tools`, `tests`, whichever exist); factor that list into one `spec_citations` helper that the CLI also calls, so the two cannot drift. (4) Compare by KEY `(path relative to that side's root, id6, offset, the citing source line with whitespace stripped)`. `StaleSpecAnchor` carries no cited-text field, so the stripped citing line is read from that side's file at `finding.line`. A citing comment that only moves to another source line keeps its key. A spec edit that makes an unchanged citation stale is new, because the base had no finding with that key. (5) Never raises: any exception returns `unknown` with the exception type and message. Measure and paste its wall time on this repository, both short-circuited and with a full two-sided scan.
  - Depends on: none
  - Expected outcome: a function returning only the findings a lane introduced, `none` without scanning when no relevant file changed, and `unknown` (never an exception) on error. A pointer that only moved is not new.
  - Execution state: pending

### Task group 2: the gate

- [ ] E-02 THE REFUSAL. In `runner_shared.integrate_lane_branch`, inside the `if action_kind == INTEGRATION_ACTION_EXECUTE:` branch and BEFORE the `orchestrate_isolation.execute_merge_and_revalidate_gate` call (cheap check first, so a held lane spends no suite run), call `new_stale_anchors(repo, handle.branch, handle.base_commit)`. On `new`: return `(False, tag_integration_cause(INTEGRATION_CAUSE_SPEC_ANCHOR_NEW_STALE, <reason listing each new pointer as file:line, spec id6, offset, cited line>), INTEGRATION_REFUSAL_CONFLICT)`. Add the new cause constant `INTEGRATION_CAUSE_SPEC_ANCHOR_NEW_STALE = "spec-anchor-new-stale"` beside the other `INTEGRATION_CAUSE_*` names, plus its own terminal sentence in the per-cause text table that holds `INTEGRATION_CAUSE_GATE_COMBINED_RED`'s ("the run's fix-it budget was spent ..."), so an exhausted item reads as a spec-pointer refusal rather than the generic fallback. `fail-merge` (`INTEGRATION_REFUSAL_CONFLICT`) is correctly NOT deferrable under `classify_integration_refusal`, because repetition cannot clear it. On `unknown`: proceed to the gate as today, and append a `spec-anchor-check-unknown` event to the run's `events.jsonl` carrying the id6 and reason. The detector must never block on its own failure. On `none`: proceed as today. Review lanes never reach this branch (`action_kind`), so they are unaffected.
  - Depends on: E-01
  - Expected outcome: a lane introducing a stale pointer is refused with the new cause before any suite run; an `unknown` result merges and leaves a warning event; a clean lane merges unchanged.
  - Execution state: pending

- [ ] E-05 THE FIX-IT TURN. In `runner_shared.execute_item_core`, add a send-back loop for the new cause modeled on the combined-red send-back loop (fixfirst Order 05 `w9nvq4` E-03, the `while` guarded by `read_integration_cause(integ_reason)[0] == INTEGRATION_CAUSE_GATE_COMBINED_RED`). Same guards: a lane handle, a `session_id`, and a per-item counter below `frozen_retry_budget(state)`. Give it its own counter key (`SPEC_ANCHOR_RETRY_COUNT_KEY`) and its own `spec-anchor-sent-back` event. The prompt is built with `build_fix_it_notice("spec-anchor-new-stale", ...)` and lists each new pointer plus the remedy: cite by section heading or quoted string (spec `ipd-structure-and-linting` Section 10.2), never by a new bare line number. After the resumed turn, re-integrate through `integrate_under_repository_lock` exactly as the combined-red loop does. Budget exhausted: the item ends `fail-merge` with the new cause's terminal sentence, as combined-red does.
  - Depends on: E-02
  - Expected outcome: a held lane gets a bounded fix-it turn in its own session, and a fixed lane merges on re-integration. Both hosts reach the loop because it sits in shared `execute_item_core`.
  - Execution state: pending

### Task group 3: prove and document

- [ ] E-03 Add `tests/test_merge_gate_spec_anchors.py`, driving the real integration path with a scripted host (follow `tests/test_hook_and_suite_fix_it.py`, whose combined-red send-back case drives the same loop shape) in a fixture repo holding a small spec and a source file citing it, asserting on queue status, events, refusal codes and whether main advanced, never on source text. Cases: (a) the lane edits the spec so an existing pointer goes stale: held, correction turn issued with the pointer named; (b) the scripted agent then fixes the pointer: merged; (c) the lane adds a new stale pointer: held; (d) a stale pointer already on the base: merged, not held; (e) a lane that only moves lines in a non-spec file: merged; (f) the detector raises: merged with a `spec-anchor-check-unknown` event; (g) the budget is exhausted (budget 0, or the scripted agent never fixes it): item ends `fail-merge` with cause `spec-anchor-new-stale`, and main did not advance; (h) a direct call of `new_stale_anchors` on a lane that changed no spec and no scanned `.py` returns `none` without scanning, observed by the detector not being called (patch it to raise; the result is still `none`). (a), (c) must FAIL on the base commit; show it.
  - Depends on: E-05
  - Expected outcome: the new module passes; (a) and (c) shown failing before the change.
  - Execution state: pending

- [ ] E-04 Amend spec `25kzda` Section "5.5 Retry policy". Name this refusal as an instance of the existing group (a) member "missing expected artifact or failed deterministic check", with no new group member, so the stated "12 members" count and `TURN_RETRY_CLASSIFICATION` stay unchanged. Add one sentence to that row's Notes in the retry-class mapping table naming the merge-time spec-anchor check, its cause `spec-anchor-new-stale`, and its fail-open `unknown` behavior. Cite nothing in the spec by bare line number. Add a CHANGELOG line (no em or en dashes). Run the bare suite and paste its summary line.
  - Depends on: E-03
  - Expected outcome: the spec diff, the CHANGELOG line, and a green bare suite.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite BARE as `python3 -m pytest`; narrowed runs `-o addopts=""`. Tests drive surfaces, never read source (P16).
- Cite code by SYMBOL or quoted string; a line number only beside one of those (spec `ipd-structure-and-linting` 10.2, advisory `IPD-C801`).
- Commit through `aw commit <plan> -- <paths>`; never push.

## Findings

| ID | Finding | Evidence |
|----|---------|----------|
| F-01 | The detector exists and is opt-in. | `cli.py` `--source-anchors` handler calls `spec_citations.stale_spec_anchors(repo_root, scan_paths)` and reports rule `check.spec-anchor-stale`. |
| F-02 | Lane integration already re-validates before merging. | `runner_shared.integrate_lane_branch` calls `orchestrate_isolation.execute_merge_and_revalidate_gate(... full_validation_runner=validation_runner)` for execute items. |
| F-03 | Its cost is small against a merge's suite run. | Review at `bd4c7874e`: one `stale_spec_anchors` call over `agent_workflows`, `tools`, `tests` took 2.16s real (2.11s user); two sides cost about 4.3s plus two `git worktree add`, and the E-01 short-circuit removes it from merges touching no spec and no scanned `.py`. The merge gate already runs the full suite. |
| F-06 | The detector's findings do not carry the cited text and do carry absolute paths. | `spec_citations.StaleSpecAnchor` fields: `file` (absolute `Path`), `line`, `id6`, `offset`, `enclosing_heading`, `validity`; hence E-01's key definition and relativization. |
| F-07 | The only integration fix-it loop is keyed on one cause. | `runner_shared.execute_item_core` combined-red loop: `while ... integ_kind == INTEGRATION_REFUSAL_CONFLICT and read_integration_cause(integ_reason)[0] == INTEGRATION_CAUSE_GATE_COMBINED_RED ...`; so a new cause gets no correction turn unless E-05 adds one. |
| F-08 | A preserved lane may have no worktree. | `runner_shared` nested `_handle_for` (beside `_integrate`) builds `WorktreeHandle(path=Path(worktree) if worktree else Path(""), ...)`; hence E-01 evaluates commits, not trees. |
| F-04 | The detector has known false positives and a crash, fixed elsewhere. | Plan `fz3i3m` (Set `sbh1o1`, approved): table-row acceptance and the `--agent` crash `g3ropl`; hence the dependency. |
| F-05 | CI is not a viable venue today. | CI red since 2026-09-27 (Order 01 F-01). |

## Proposed changes (ordered, validatable)

1. New-findings comparison (E-01). 2. Refusal at integration (E-02). 3. Fix-it send-back loop (E-05). 4. Tests (E-03). 5. Spec and docs (E-04).

## Deferred / out of scope (with reason)

- Gating hand commits: Order 02's checkup reports stale pointers made outside runs.
  - Carrier: n7xlhm
- A pointer made stale only by COMBINING the lane with commits main gained after the lane's base (the lane is compared against its own base, not the merge result). Comparing against the merge result would block a lane for a peer's change; Order 02's checkup reports any such residue.
  - Carrier: n7xlhm
- Making the rule `error` in `aw check` or adding a CI step (plan `l85xvi`'s approach): superseded by this gate by maintainer decision.
  - Carrier-Declined: maintainer ruling 2026-10-12; `l85xvi` retired as superseded by this Set.

## Scope check

- Over-scope: none.
- Under-scope: the fix-it turn was missing (no integration send-back exists for any cause but combined-red, F-07); added as E-05.

## Required tests / validation

- `tests/test_merge_gate_spec_anchors.py` (new), cases (a) to (h), with (a) and (c) failing on the base commit.
- `tests/test_hook_and_suite_fix_it.py` and `tests/test_retry_class_mapping.py` unchanged and passing.
- Existing integration-gate tests unchanged and passing.
- Bare suite `python3 -m pytest`.

## Spec / documentation sync

Spec `25kzda` amended (E-04), listed in Scope-Paths. WHY: it describes what lane integration checks; a new refusal there changes what a reviewer expects a run to do. CHANGELOG line.

## Open questions

### OQ-01: Block on stale pointers that already exist?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Only pointers a lane makes stale block it, so a lane is never held for someone else's debt. Existing ones are reported by the checkup (Order 02). Reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the function's pasted output on a fixture with one moved pointer and one newly stale pointer (only the second returned); its `none` result on a lane with no relevant change; its `unknown` result when scanning raises; `git worktree list` after each call, showing no leftover temporary worktree; and both measured wall times on this repository.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: E-03 (a), (c), (f) passing, produced through `runner_shared.integrate_lane_branch` (E-02): the pasted refusal reason carrying cause `spec-anchor-new-stale` and naming the pointer, the `spec-anchor-check-unknown` event line for (f), and confirmation that `validation_runner` was not called for the refused lane.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new module's pasted pass output (all of (a) to (h)) and the pasted failing output of (a) and (c) on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the spec diff, the CHANGELOG line, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: E-03 (a), (b), (g) passing through the `runner_shared.execute_item_core` send-back loop (E-05): the pasted correction prompt text naming the pointer and the section-heading remedy, the `spec-anchor-sent-back` event line, main advanced after (b), and the `fail-merge` record with cause `spec-anchor-new-stale` and an unmoved main after (g).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after `fz3i3m` is executed. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit mnwkqu -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual runner output for every test and timing claim; a claim without pasted output is not evidence. Never `git mv` the plan or hand-edit `- Status:`. This plan inherits `- Blocks-Release: next` from backlog `5st6e5`. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize mnwkqu` only after `aw ipd lint --phase pre-transition` conforms.
