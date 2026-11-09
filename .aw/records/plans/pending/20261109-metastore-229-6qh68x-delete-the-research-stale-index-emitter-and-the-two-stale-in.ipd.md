# IPD: Delete the research stale-index emitter and the two stale-index registry entries

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 deletes `check.stale-index-*`. After Order 224 the only emitter left is `research_index.check_drift`, and `check_engine.RULE_REGISTRY` still registers `check.stale-index-missing` and `check.stale-index-stale`, with 16 `check_engine` comment lines that describe or cite them. This is part 6 of the round-3 split of `q6epwc` (Order 41), carrying the `research_index` and `check_engine` subset of `q6epwc` E-05.
- Scope: delete the last emitter and the two registry entries together, rewrite the `check_engine` comments that cite them, and update `tests/test_drift_rule_registration.py` plus the stale-index cases of `tests/test_research_index.py` and `tests/test_index_check_agent_records.py`. EXCLUDES: `doctor` (Order 225), the plans and prompts emitters (Order 224), and INDEX-byte assertions (`snin8q`).
- Scope-Paths: agent_workflows/research_index.py, agent_workflows/check_engine.py, tests/test_drift_rule_registration.py, tests/test_research_index.py, tests/test_index_check_agent_records.py, .aw/records/plans/pending/20261109-metastore-229-6qh68x-delete-the-research-stale-index-emitter-and-the-two-stale-in.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15, executed:tqknnc, executed:w819as
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 229
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6qh68x

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

After this plan, no `check_drift` emits a `check.stale-index-*` rule and `check_engine.RULE_REGISTRY` no longer registers one; every other research drift rule still fires.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`q6epwc` E-05's site list is split across Orders 224, 229 and 225; this plan takes: the 2 `check_engine.RULE_REGISTRY` entries, the 2 emitter lines of `research_index.check_drift`, the 16 `check_engine` comment lines, the test module `tests/test_drift_rule_registration.py` from E-05's list, and the stale-index cases of `tests/test_research_index.py` and `tests/test_index_check_agent_records.py`. "Deleting the registry entry and the emitters together matters: an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`)" (carried from `q6epwc` E-05): E-02 and E-03 land in ONE commit.

PIN RULE (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/6qh68x/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor. A test whose only subject is a deleted rule is deleted, and the mapping says "subject removed".

### Task group 1: pin, delete, retarget

- [ ] E-01 Pin `tests/test_drift_rule_registration.py`, `tests/test_research_index.py` and `tests/test_index_check_agent_records.py` (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/6qh68x/E-01-before.txt` exists.
  - Execution state: pending

- [ ] E-02 Delete the code in `research_index.check_drift` that emits `check.stale-index-missing` and `check.stale-index-stale`; keep its other rules (`stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`, `research.frontmatter-key-repeated`, `status-tier-mismatch`, `check.research-companion-orphaned`).
  - Depends on: E-01
  - Expected outcome: `rg -n "stale-index" agent_workflows/research_index.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/check_engine.py`, delete the `check.stale-index-missing` and `check.stale-index-stale` entries of `check_engine.RULE_REGISTRY`, and rewrite the comment lines that describe them or cite them as a severity precedent so each keeps its reasoning without naming a deleted rule.
  - Depends on: E-02
  - Expected outcome: `rg -n "stale-index" agent_workflows/check_engine.py` prints nothing.
  - Execution state: pending

- [ ] E-04 Retarget `tests/test_drift_rule_registration.py` to the new rule set, and the stale-index cases `test_stale_index_detected` and `test_missing_index_is_informational_not_failing` in `tests/test_research_index.py`, and `test_human_drifting_output_per_verb`, `test_human_stale_output_per_verb` and `test_all_partial_stale_fixture` in `tests/test_index_check_agent_records.py` (each assertion that names a `check.stale-index-*` id). Save `E-04-after.txt`.
  - Depends on: E-03
  - Expected outcome: the three modules pass.
  - Execution state: pending

- [ ] E-05 Run the three modules and `rg -n "stale-index" agent_workflows`, then commit E-02 to E-04 together through `aw commit 6qh68x -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-04
  - Expected outcome: `rg` lists only `doctor` lines (Order 225) and the `engine.py` `.aw/.gitignore` template comment (cutover); one commit holds the registry and emitter deletion.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Severities come from `check_engine.RULE_REGISTRY` (`RuleSpec`); an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "stale-index" agent_workflows/check_engine.py` prints 18 lines (2 registry keys, 16 comments); `agent_workflows/research_index.py` 2 lines in `check_drift`. `rg -c "stale-index"`: `tests/test_research_index.py` 4, `tests/test_index_check_agent_records.py` 6.

## Proposed changes (ordered, validatable)

1. Pin (E-01).
2. Delete the research emitter (E-02) and the registry entries with their comments (E-03).
3. Retarget (E-04), verify and commit in one commit (E-05).

## Deferred / out of scope (with reason)

- `doctor`'s stale-index remediation: Order 225.
  - Carrier: q6epwc
- The `engine.py` `.aw/.gitignore` template comment: removed with the ignore lines at the cutover.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 5 work Scope-Paths.

## Required tests / validation

Pinned and retargeted: `tests/test_drift_rule_registration.py`, `tests/test_research_index.py`, `tests/test_index_check_agent_records.py`. Commands: those three modules, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5.

## Open questions

### OQ-01: Can `doctor` still match a deleted rule after this plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Its substring branches stay dead but harmless until Order 225 deletes them; no emitter produces the rule. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/6qh68x/E-01-before.txt` and one line from each of the three named modules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "stale-index" agent_workflows/research_index.py` printing nothing, and `aw check research --all --agent` on a fixture with one `dangling-consumed-by` research doc and no INDEX file, showing that rule and no `check.stale-index-*`. Code path: `check_engine.check_content` -> `research_index.check_drift` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "stale-index" agent_workflows/check_engine.py` printing nothing, and `python3 -c "from agent_workflows import check_engine as c;print([k for k in c.RULE_REGISTRY if 'stale-index' in k])"` printing `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/6qh68x/E-01-before.txt .aw/state/6qh68x/E-04-after.txt` with each removed name of the five named cases mapped, and the summary line of `python3 -m pytest -o addopts="" tests/test_drift_rule_registration.py tests/test_research_index.py tests/test_index_check_agent_records.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "stale-index" agent_workflows` listing only `doctor.py` and `engine.py` lines, and `git show --stat` of the single `aw commit 6qh68x` commit listing `agent_workflows/research_index.py` and `agent_workflows/check_engine.py` together and only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed (Order 224 first, so this plan removes the LAST emitter with the registry entries). Every deletion is pin-first (PIN RULE above). Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit 6qh68x -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
