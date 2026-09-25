# IPD: Five small cleanups: runner parser seam, stale runner comment, tracked-tree reachability test, backlog CI gate, and relocation note

- Date: 2026-09-25
- Kind: child
- Concern: Five small, independent items verified live at HEAD: (1) `runner_shared.discover_plans` still takes an injected `parse_plan_file` though all three drivers share one parser (ykfgpd); (2) `agy_runipd.py` still states the two drivers' PlanRecords differ, which is false (1gw7nl); (3) no test proves each tracked tree's records reach `aw attention`, only that a scan root is declared (2rb85l); (4) CI runs `aw check backlog` advisory although its stated precondition, a clean baseline, is now met (e85snf); (5) the git mv then untrack resolution for relocating tracked content into an ignored tree lives only in a docstring (q0m7qf).
- Scope: IN: exactly those five. OUT: anything else in the files touched.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_attention_contract.py, .github/workflows/tests.yml, .aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- Set: smallfix
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 0i4fkt
- From-Backlog: ykfgpd

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlogs ykfgpd, 1gw7nl, 2rb85l, e85snf, q0m7qf (all verified live at HEAD; each E-group names its item). Measured: `oc_runipd.parse_plan_file is agy_runipd.parse_plan_file is runner_shared.parse_plan_file` -> True; `aw check backlog` -> conforms, exit 0; walkthrough of the git mv/rm --cached mechanism reproduced in a scratch repo.

## Goal

Remove a seam that carries no information and a comment that is false, prove tracked trees are actually visible, gate CI on backlog conformance, and make the relocation technique findable by plan authors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: ykfgpd + 1gw7nl: runner seam

- [ ] E-01 (ykfgpd, 1gw7nl) Drop the `parse_plan_file` keyword from `runner_shared.discover_plans` (it calls its own `parse_plan_file`), update its caller in `initialize_run_core`, reduce the `oc_runipd`/`agy_runipd` `discover_plans` wrappers to plain re-exports of the shared function, delete the false 'DIFFERENT NamedTuples' comment in `agy_runipd.py` and the matching retraction note in `oc_runipd.py`, and remove the `discover_plans` entry from `INJECTED` in `tests/test_runner_shared.py`.
  - Depends on: none
  - Expected outcome: one `discover_plans`, no injection, no false comment; host call sites unchanged.
  - Execution state: pending

### Task group 2: 2rb85l: reachability test

- [ ] E-02 (2rb85l) Add a parametrized test to `tests/test_attention_contract.py`: for each tree in `attention_contract.TRACKED_TREES`, write one minimal valid record under its `.aw/records/<tree>/` root in a temp repo and assert `attention.scan` returns it.
  - Depends on: none
  - Expected outcome: one case per tracked tree passes.
  - Execution state: pending

### Task group 3: e85snf: backlog CI gate

- [ ] E-03 (e85snf) In `.github/workflows/tests.yml`, make the `aw check backlog` step fail-closed: drop the `|| echo ::warning::` fallback and rename the step to say fail closed, keeping a comment that cites this plan and the measured clean baseline.
  - Depends on: none
  - Expected outcome: a backlog conformance finding now fails CI.
  - Execution state: pending

### Task group 4: q0m7qf: relocation note

- [ ] E-04 (q0m7qf) Add a short section to the records-taxonomy spec (`20260817-2124-01-records-taxonomy-cleanup.spec.md`): relocating tracked content into an ignored tree is two commits, `git mv` (keeps `git log --follow` history) then `git rm --cached` (so the ignore rule applies), and a path-scoped `git commit -- <paths>` cannot express the index-only removal while the file is present, which is why `engine._commit_relocation` moves it aside for that commit.
  - Depends on: none
  - Expected outcome: the technique is findable by a plan author.
  - Execution state: pending

### Task group 5: verification

- [ ] E-05 Run the bare suite.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The maintainer prefers fixing small items in one pass over one plan each; these five are independent, each under about 60 lines, and grouped here for that reason.
- Plans may amend a spec and must declare it in `Scope-Paths` (AGENTS.md); E-04 amends the records-taxonomy spec.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `runner_shared.discover_plans` | The injected parser is the same object in every driver. | `o.parse_plan_file is a.parse_plan_file is r.parse_plan_file` -> True |
| F-2 | LOW | `agy_runipd.discover_plans` comment | States the PlanRecords differ; they are one class. | `oc_runipd.PlanRecord is agy_runipd.PlanRecord is runner_shared.PlanRecord` -> True |
| F-3 | LOW | `test_attention_contract` | The guard proves a scan root is declared, not that records arrive; only releases has a reachability test. | read `TrackedTreeScanCoverageTests`, `ReleaseRecordsReachTheViewTests` |
| F-4 | LOW | CI | Backlog check is advisory; its precondition (clean baseline) is met. | `check backlog --agent` -> conforms, exit 0 |
| F-5 | LOW | records-taxonomy spec | The relocation technique is only in `engine._commit_relocation`'s docstring. | grep of specs and DECISIONS.md: no hit |

## Proposed changes (ordered, validatable)

1. E-01: collapse the discover_plans seam and its false comment.
2. E-02: per-tree reachability test.
3. E-03: flip the backlog CI step to fail-closed.
4. E-04: document the relocation technique.
5. E-05: bare suite.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none; each group touches only what its item names.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_runner_shared.py tests/test_attention_contract.py -o addopts="" -q` plus the V-02 mutation.
- Bare `python3 -m pytest`.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md` (E-04), declared in `Scope-Paths`, because that spec documents where run scratch goes and is where a plan author looks before relocating tracked content.

## Open questions

### OQ-01: Should the `discover_plans` host wrappers be deleted outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No, resolved from the tests: `driver.discover_plans(repo)` is called from `test_oc_runipd.py`, `test_orchestrator_retirement.py` and `test_runner_shared.py`, so the names stay as re-exports and no call site changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff stat; paste `grep -n "parse_plan_file=parse_plan_file\|DIFFERENT NamedTuples" agent_workflows/*.py` returning nothing; paste `python3 tools/runner_fork_scan.py` output for `discover_plans`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the run with one passing case per tree; remove `.aw/records/specs` from `artifact_core.SCAN_ROOTS` IN THE WORKTREE, paste the specs case FAILING, restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the workflow diff and `python3 -m agent_workflows check backlog --agent` exiting 0 with no error-severity findings.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec diff and `python3 -m agent_workflows specs check` exit code.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: five independent small cleanups grouped at the maintainer's stated preference for fixing small items together; each group is separately verifiable.

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.
