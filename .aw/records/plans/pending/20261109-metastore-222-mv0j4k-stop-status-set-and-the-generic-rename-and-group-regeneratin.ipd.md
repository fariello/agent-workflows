# IPD: Stop status set and the generic rename and group regenerating INDEX files

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` 4.5 says the SQLite cache replaces the INDEX files. Today `aw ipd set`, `aw backlog set` and `aw specs set` regenerate INDEX files through `status_set._auto_index_types`, and `aw rename <type>` and `aw group <type>` regenerate them through four `run_index` calls in `artifact_rename`. This is part 3 of the round-3 split of `q6epwc` (Order 41), carrying the `status_set` and `artifact_rename` subset of `q6epwc` E-04.
- Scope: delete `status_set._auto_index_types` and its two calls, delete the four `run_index` calls in `artifact_rename.run_rename_generic` and `artifact_rename.run_group_generic`, and pin the three test modules that assert those commands' INDEX lines or files. EXCLUDES: the finalize refresh (Order 221), the research, plan-rename and adopt callers (Order 223), and the INDEX writers (`snin8q`).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/artifact_rename.py, tests/test_rename_group_machine_output.py, tests/test_research_rename_frontmatter.py, tests/test_group_verb_policy.py, .aw/records/plans/pending/20261109-metastore-222-mv0j4k-stop-status-set-and-the-generic-rename-and-group-regeneratin.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15, executed:tqknnc
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 222
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: mv0j4k

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

After this plan, the status setters and the generic rename and group verbs change records without writing `INDEX.json` or `INDEX.md`; each command's other output is unchanged.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`q6epwc` E-04's site list is split across Orders 221, 222 and 223; this plan takes: `status_set._auto_index_types` (definition, its two inner `run_index` calls, its two callers in `status_set.run_set_command`) and the four `run_index` sites in `artifact_rename` (two in `run_rename_generic`, two in `run_group_generic`), plus the test modules `tests/test_rename_group_machine_output.py`, `tests/test_research_rename_frontmatter.py` and `tests/test_group_verb_policy.py` from E-04's test list. "Each affected command's result loses only its INDEX-refresh line; pin each command's other output in the touched tests first" (carried from `q6epwc` E-04).

PIN RULE (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/mv0j4k/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: pin, delete, retarget

- [ ] E-01 Pin `tests/test_rename_group_machine_output.py`, `tests/test_research_rename_frontmatter.py` and `tests/test_group_verb_policy.py` (PIN RULE, `E-01-before.txt`).
  - Depends on: none
  - Expected outcome: `.aw/state/mv0j4k/E-01-before.txt` exists.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/status_set.py`, delete `status_set._auto_index_types` and its two calls in `status_set.run_set_command`, and rewrite the docstring sentence that says touched types are "refreshed on disk by `_auto_index_types`".
  - Depends on: E-01
  - Expected outcome: `rg -n "_auto_index_types|run_index" agent_workflows/status_set.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/artifact_rename.py`, delete the two `run_index` calls in `artifact_rename.run_rename_generic` and the two in `artifact_rename.run_group_generic`, with the result lines they add.
  - Depends on: E-01
  - Expected outcome: `rg -n "run_index" agent_workflows/artifact_rename.py` prints nothing.
  - Execution state: pending

- [ ] E-04 Retarget the three pinned modules so they assert only on surviving output: `tests/test_rename_group_machine_output.py` (`_NESTED_PLANS_INDEX_LINE`, `_NESTED_RESEARCH_INDEX_LINE` and their uses), `tests/test_research_rename_frontmatter.py` (the "generated INDEX.json points to a path that exists" case becomes "`aw find research` shows the regrouped path"), and `tests/test_group_verb_policy.py` (the `f.name != "INDEX.md"` filters stay valid and need no change unless a case fails). Save `E-04-after.txt`, run the three modules, and commit through `aw commit mv0j4k -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-02, E-03
  - Expected outcome: the three modules pass; the before/after mapping accounts for every case.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `status_set.run_set_command` is the shared engine of the typed setters; `artifact_rename.run_rename_generic` and `artifact_rename.run_group_generic` back `aw rename <type>` and `aw group <type>`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `3d0ddb845`: `rg -n "_auto_index_types|run_index" agent_workflows/status_set.py` prints 1 definition, 2 inner `run_index` calls, 2 call sites and 1 docstring mention; `rg -n "run_index" agent_workflows/artifact_rename.py` prints 4 sites (2 in `run_rename_generic`, 2 in `run_group_generic`). `rg -c "INDEX\.(json|md)"`: `tests/test_rename_group_machine_output.py` 10, `tests/test_research_rename_frontmatter.py` 7, `tests/test_group_verb_policy.py` 6.

## Proposed changes (ordered, validatable)

1. Pin (E-01).
2. Delete the `status_set` (E-02) and `artifact_rename` (E-03) callers.
3. Retarget and commit (E-04).

## Deferred / out of scope (with reason)

- The finalize refresh (Order 221) and the `research_cmd`, `research_refs`, `plans_refs` and `artifact_adopt` callers (Order 223).
  - Carrier: q6epwc

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 5 work Scope-Paths.

## Required tests / validation

Pinned and retargeted: `tests/test_rename_group_machine_output.py`, `tests/test_research_rename_frontmatter.py`, `tests/test_group_verb_policy.py`. Commands: those three modules, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.5.

## Open questions

### OQ-01: Does any caller read the value `_auto_index_types` returned?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Only the agent-mode changes list, which reported the refreshed INDEX paths; after this plan those entries are absent, which is the intended output change pinned by E-04. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `wc -l .aw/state/mv0j4k/E-01-before.txt` and one line from each of the three named modules.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "_auto_index_types|run_index" agent_workflows/status_set.py` printing nothing, and a fixture `aw ipd set to-review <id6>` followed by `ls .aw/records/plans/INDEX.*` showing no such file. Code path: `status_set.run_set_command` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "run_index" agent_workflows/artifact_rename.py` printing nothing, and a fixture `aw group plans` run followed by `ls .aw/records/plans/INDEX.*` showing no such file. Code path: `artifact_rename.run_group_generic` (E-03).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/mv0j4k/E-01-before.txt .aw/state/mv0j4k/E-04-after.txt` with each removed name mapped to its successor, the summary line of `python3 -m pytest -o addopts="" tests/test_rename_group_machine_output.py tests/test_research_rename_frontmatter.py tests/test_group_verb_policy.py` passing, and `git show --stat` of the `aw commit mv0j4k` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit mv0j4k -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
