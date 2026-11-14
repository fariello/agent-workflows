# IPD: Delete the stale-index emitters of the plans and prompts check_drift

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 deletes `check.stale-index-*`. Today `plans_index.check_drift` and `prompts_index.check_drift` each emit `check.stale-index-missing` and `check.stale-index-stale` when an INDEX file is absent or out of date, and three `ipd_lifecycle` comments describe those rules. This is part 5 of the round-3 split of `q6epwc` (Order 41), carrying the plans, prompts and `ipd_lifecycle` subset of `q6epwc` E-05.
- Scope: delete the stale-index emitter code in `plans_index.check_drift` and `prompts_index.check_drift`, rewrite the three `stale-index` comments in `ipd_lifecycle`, and update the cases of `tests/test_plans_index.py`, `tests/test_prompts_index.py` and `tests/test_nv_backend_args_climb.py` that name a `check.stale-index-*` id. EXCLUDES: the `research_index` emitter and the two registry entries (Order 229), `doctor` (Order 225), and the INDEX-byte assertions of the same test modules (`snin8q`).
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/prompts_index.py, agent_workflows/ipd_lifecycle.py, tests/test_plans_index.py, tests/test_prompts_index.py, tests/test_nv_backend_args_climb.py, .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15, executed:tqknnc
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 224
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: w819as

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

After this plan, `aw check plans --all` and `aw index prompts --check` report no `check.stale-index-*` finding, and no `ipd_lifecycle` comment names those rules; every other rule of the two `check_drift` functions still fires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`q6epwc` E-05's site list is split across Orders 224, 229 and 225; this plan takes the emitter lines in `plans_index.check_drift` (2) and `prompts_index.check_drift` (2), the 3 `ipd_lifecycle` comment lines, and the test module `tests/test_nv_backend_args_climb.py` from E-05's list, plus the `check.stale-index-*` cases of `tests/test_plans_index.py` and `tests/test_prompts_index.py` ("expected to change only where an assertion names a `check.stale-index-*` id, and each such case is pinned and mapped"). The registry entries stay until Order 229 removes the last emitter, so no rule is ever emitted unregistered (an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC`, severity `error`).

PIN RULE (carried from `9o83cr`): before the edit, ensure the output directory exists (`mkdir -p .aw/state/w819as`) and save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/w819as/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor. A test whose only subject is a deleted rule is deleted, and the mapping says "subject removed".

### Task group 1: pin, delete, retarget

- [ ] E-01 Ensure `.aw/state/w819as` exists (`mkdir -p .aw/state/w819as`) and pin `tests/test_plans_index.py`, `tests/test_prompts_index.py` and `tests/test_nv_backend_args_climb.py` (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/w819as/E-01-before.txt` exists.
  - Execution state: pending

- [ ] E-02 Delete the code in `plans_index.check_drift` and in `prompts_index.check_drift` that emits `check.stale-index-missing` and `check.stale-index-stale`; keep every other rule those functions emit (`name-metadata-mismatch`, `dangling-citation`).
  - Depends on: E-01
  - Expected outcome: `rg -n "stale-index" agent_workflows/plans_index.py agent_workflows/prompts_index.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/ipd_lifecycle.py`, rewrite the three comments that name `check.stale-index-missing` or `check.stale-index-stale` so they no longer describe the deleted rules.
  - Depends on: E-01
  - Expected outcome: `rg -n "stale-index" agent_workflows/ipd_lifecycle.py` prints nothing.
  - Execution state: pending

- [ ] E-04 Retarget the cases that name a stale-index id: `test_stale_index_flagged` and `test_missing_index_is_informational_not_failing` in `tests/test_plans_index.py`; `test_check_drift_missing_index` and `test_check_drift_stale_index` in `tests/test_prompts_index.py` (and its module docstring lines); `test_assertion_d_outside_project_unaltered` in `tests/test_nv_backend_args_climb.py` (it expects two `check.stale-index-missing` diagnostics and now expects none). Save `E-04-after.txt`, run the three modules, and commit through `aw commit w819as -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-02, E-03
  - Expected outcome: the three modules pass; the mapping accounts for every case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Drift findings are `artifact_core.Drift(location, rule, detail)`; severities come from `check_engine.RULE_REGISTRY`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "stale-index" agent_workflows/plans_index.py agent_workflows/prompts_index.py agent_workflows/ipd_lifecycle.py` prints 2, 2 and 3 lines; `rg -c "stale-index"` in `tests/test_plans_index.py` 4, `tests/test_prompts_index.py` 4, `tests/test_nv_backend_args_climb.py` 2.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["E-01: Ensure state dir & pin test baseline (tests/test_plans_index.py, test_prompts_index.py, test_nv_backend_args_climb.py)"]
    E02["E-02: Delete stale-index emitter code in plans_index.check_drift and prompts_index.check_drift"]
    E03["E-03: Rewrite 3 stale-index comment citations in ipd_lifecycle.py"]
    E04["E-04: Retarget test cases naming stale-index rules, verify after-baseline, commit Scope-Paths"]

    E01 --> E02
    E01 --> E03
    E02 --> E04
    E03 --> E04
```

1. Pin (E-01).
2. Delete the emitters (E-02) and comments (E-03).
3. Retarget and commit (E-04).

## Deferred / out of scope (with reason)

- The `research_index` emitter, the registry entries and the `check_engine` comments: Order 229. `doctor`: Order 225.
  - Carrier: q6epwc
- INDEX-byte assertions in `tests/test_plans_index.py` and `tests/test_prompts_index.py`: deleted with the writers.
  - Carrier: snin8q

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 6 work Scope-Paths.

## Required tests / validation

Pinned and retargeted: `tests/test_plans_index.py`, `tests/test_prompts_index.py`, `tests/test_nv_backend_args_climb.py`. Commands: those three modules, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5.

## Open questions

### OQ-01: Is it safe to remove emitters before the registry entries?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. A registered rule with no emitter is inert; the reverse order (registry first) would make a surviving emitter's finding fall to `check_engine._DEFAULT_RULESPEC` at severity `error`. Order 229 removes the last emitter and the entries together. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/w819as/E-01-before.txt` and one line from each of the three named modules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "stale-index" agent_workflows/plans_index.py agent_workflows/prompts_index.py` printing nothing, and `aw check plans --all --agent` on a fixture with a dangling plan citation and no INDEX file, showing `dangling-citation` and no `check.stale-index-*`. Code path: `check_engine.check_content` -> `plans_index.check_drift` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "stale-index" agent_workflows/ipd_lifecycle.py` printing nothing, and the `git diff` hunks of the three comments.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/w819as/E-01-before.txt .aw/state/w819as/E-04-after.txt` with each removed name of the five named cases mapped, the summary line of `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_prompts_index.py tests/test_nv_backend_args_climb.py` passing, and `git show --stat` of the `aw commit w819as` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Safety stop: if prerequisite metastore symbols from `59aiyh`, `sdzcur`, or `tqknnc` are absent upon starting, stop and report rather than creating conflicting implementations. Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit w819as -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through finalize; when `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize w819as` itself after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence; never a hand `git mv` to `executed/`.
