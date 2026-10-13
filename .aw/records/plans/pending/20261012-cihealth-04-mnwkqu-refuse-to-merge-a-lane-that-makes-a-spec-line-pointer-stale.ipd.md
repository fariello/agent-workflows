# IPD: Refuse to merge a lane that makes a spec line pointer stale

- Date: 2026-10-12
- Kind: child
- Concern: Code comments point into specs by line number ("spec `25kzda` :744"). When a spec is edited the line moves and the pointer goes stale. The detector (`spec_citations.stale_spec_anchors`, rule `check.spec-anchor-stale`) is opt-in and runs only on `aw check --source-anchors`, so stale pointers pile up until a plan sweeps them (`mt54wr`, `atpvao`). Plan `l85xvi` proposed failing CI on them, but CI is not watched (red for 1,623 main commits at review), so the maintainer chose to catch them where the change is made: at the runner's merge check, before a lane reaches main.
- Scope: At the runner's lane-integration step (where `orchestrate_isolation.execute_merge_and_revalidate_gate` already re-validates a lane before it is merged), run `spec_citations.stale_spec_anchors` on the lane tree and on the lane's base commit, and refuse the merge only when the lane has stale pointers that its base did not (new findings, keyed by file, spec id6 and the cited construct, not by line number, so moved lines do not count as new). The refusal goes back to the agent as a fix-it turn through the existing correction path, naming each new stale pointer. Pre-existing stale pointers never block; Order 02's checkup reports them. The detector's accuracy fixes are plan `fz3i3m`'s (Set `sbh1o1`); this plan depends on it.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/orchestrate_isolation.py, agent_workflows/spec_citations.py, tests/test_merge_gate_spec_anchors.py, CHANGELOG.md, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:fz3i3m
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 5st6e5
- Blocks-Release: next
- Set: cihealth
- Order: 4
- Highest E allocated: 04
- Author: opencode model=its_direct/pt3-claude-opus-5.5-1m-us
- Id: mnwkqu

## Workflow history
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored during /plan-review of Set gradfix; replaces plan l85xvi's CI step per the maintainer's 2026-10-12 ruling.
- 2026-10-12 draft (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A lane that makes a spec line pointer stale is not merged until its agent fixes the pointer, so new stale pointers stop reaching main, at about 5 seconds per merge and no cost to anything else.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: new-findings comparison

- [ ] E-01 Add `spec_citations.new_stale_anchors(lane_root, base_commit)`: run `stale_spec_anchors` on the lane tree, run it on the base commit (a temporary `git worktree add --detach` at `base_commit`, removed afterwards, or a cached result keyed by base commit under `.aw/state/`), and return the lane findings whose key (repo-relative file, spec id6, and the cited text or section, not the line number) is absent from the base findings. Never raises; an error yields a typed UNKNOWN with the reason. Measure and paste its wall time on this repository.
  - Depends on: none
  - Expected outcome: a function returning only the findings a lane introduced; moved but unchanged pointers are not new.
  - Execution state: pending

### Task group 2: the gate

- [ ] E-02 Call it at lane integration for execute items, beside the existing revalidation in `runner_shared` (the path that calls `orchestrate_isolation.execute_merge_and_revalidate_gate`). New findings: do not merge; send the item to the existing fix-it correction turn with a message listing each new stale pointer (file, line, spec id6, cited text) and the remedy (cite by section heading or quoted string, spec `ipd-structure-and-linting` 10.2); if the correction budget is exhausted, end the item with a typed refusal `SPEC-ANCHOR-NEW-STALE`. UNKNOWN: merge, and record a warning event (the detector must never block on its own failure). No new findings: merge as today. Review and production lanes are unaffected.
  - Depends on: E-01
  - Expected outcome: a lane adding a stale pointer is held and its agent is asked to fix it; a clean lane merges unchanged.
  - Execution state: pending

### Task group 3: prove and document

- [ ] E-03 Add `tests/test_merge_gate_spec_anchors.py`, driving the real integration path with a scripted host in a fixture repo holding a small spec and a source file citing it, asserting on queue status, events, refusal codes and whether main advanced, never on source text. Cases: (a) the lane edits the spec so an existing pointer goes stale: held, correction turn issued with the pointer named; (b) the scripted agent then fixes the pointer: merged; (c) the lane adds a new stale pointer: held; (d) a stale pointer already on the base: merged, not held; (e) a lane that only moves lines in a non-spec file: merged; (f) the detector raises: merged with a warning event. (a), (c) must FAIL on the base commit; show it.
  - Depends on: E-02
  - Expected outcome: the new module passes; (a) and (c) shown failing before the change.
  - Execution state: pending

- [ ] E-04 Amend spec `25kzda` where it lists what lane integration checks, adding this gate and its fix-it path; add a CHANGELOG line (no em or en dashes). Run the bare suite and paste its summary line.
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
| F-03 | Its cost is small against a merge's suite run. | `aw check specs --source-anchors` about 4.2s user (plan `l85xvi` F-03); the merge gate already runs the full suite. |
| F-04 | The detector has known false positives and a crash, fixed elsewhere. | Plan `fz3i3m` (Set `sbh1o1`, approved): table-row acceptance and the `--agent` crash `g3ropl`; hence the dependency. |
| F-05 | CI is not a viable venue today. | CI red since 2026-09-27 (Order 01 F-01). |

## Proposed changes (ordered, validatable)

1. New-findings comparison (E-01). 2. Gate at integration (E-02). 3. Tests (E-03). 4. Spec and docs (E-04).

## Deferred / out of scope (with reason)

- Gating hand commits: Order 02's checkup reports stale pointers made outside runs.
  - Carrier: n7xlhm
- Making the rule `error` in `aw check` or adding a CI step (plan `l85xvi`'s approach): superseded by this gate by maintainer decision.
  - Carrier-Declined: maintainer ruling 2026-10-12; `l85xvi` retired as superseded by this Set.

## Scope check

- Over-scope: none.
- Under-scope: none known.

## Required tests / validation

- `tests/test_merge_gate_spec_anchors.py` (new), (a) and (c) failing on the base commit.
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
  - Required evidence: the function's output on a fixture with one moved and one newly stale pointer (only the second returned), and its measured wall time on this repository.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: E-03 (a), (b), (f) passing, showing the correction prompt text and the warning event, produced by the integration path E-02 changes.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the new module passing and (a), (c) failing on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the spec diff, the CHANGELOG line, and the bare-suite summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and after `fz3i3m` is executed. Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit mnwkqu -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize mnwkqu` only after `aw ipd lint --phase pre-transition` conforms.
