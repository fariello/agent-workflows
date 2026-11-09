# IPD: Record the baseline for the INDEX alias and stale-index family

- Date: 2026-11-09
- Kind: child
- Concern: The finishing item of `q6epwc` (E-17) compares the `aw check all` rule multisets after the family's edits against a baseline taken BEFORE any edit. `.aw/state/` is gitignored and does not travel between lane worktrees, so after the round-3 split the baseline must be committed inside a plan file that every later part can read. This is the first part of the round-3 split of `q6epwc` (Order 41), carrying `q6epwc` E-01.
- Scope: run the read-only baseline commands and write their results into this plan's Findings table F-28, then commit this plan file. EXCLUDES every code or test edit (Orders 220 to 227 and 229 of the split).
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-228-sdzcur-record-the-baseline-for-the-index-alias-and-stale-index-fami.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 228
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: sdzcur

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from q6epwc (round 3, research nj8zdp guidance).

## Goal

Commit, inside this plan, the pre-edit outputs that `q6epwc` E-17 compares against, so the comparison survives the lane worktrees of the eight other parts of the family.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The text of `q6epwc` E-01 is split across E-01 and E-02 here; together they equal it. Every other part of the family depends on this plan, so it runs before any edit.

### Task group 1: baseline

- [ ] E-01 Run, on the unedited tree, and save to the gitignored `.aw/state/sdzcur/before/` (never `/tmp`, which a lane integration discards) the stdout and exit code of: `aw index plans --agent`, `aw index research --check --agent`, `aw check plans --all --agent`, `aw check research --all --agent`, `aw check prompts --all --agent`, `aw doctor --agent`, and the rule-id multisets of `aw check all --agent` and `aw check all --all --agent` (`jq -r '.diagnostics[].rule' | sort | uniq -c`; `--all` matters because `check_engine.check_content` reaches the `check_drift` functions only when `include_retired` is set), plus the bare core gate summary line of `python3 -m pytest`.
  - Depends on: none
  - Expected outcome: the saved outputs exist under `.aw/state/sdzcur/before/`.
  - Execution state: pending

- [ ] E-02 Copy into table F-28 of this plan: each command's exit code, the two rule-id multisets in full, the `check.stale-index-*` count in each, and the core gate summary line. Commit this plan file through `aw commit sdzcur -- <this plan's path>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-01
  - Expected outcome: F-28 holds every value; the commit lists only this plan file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift` only when `include_retired` is set (the `--all` path).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-28 | (written by E-02) exit codes, the two rule-id multisets, the `check.stale-index-*` counts and the core gate summary line, measured before any edit of the family | `q6epwc` E-17 compares against this table. |

## Proposed changes (ordered, validatable)

1. Run and save the baseline (E-01).
2. Write F-28 and commit (E-02).

## Deferred / out of scope (with reason)

- Every code, test and document edit of the family: Orders 220 to 227 and 229, and the final comparison in `q6epwc`.
  - Carrier: q6epwc

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 2 E-items, 0 work Scope-Paths (this plan file only).

## Required tests / validation

No test is written. The baseline commands are read-only.

## Spec / documentation sync

N/A: this plan records measurements only.

## Open questions

### OQ-01: Why a separate baseline plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `.aw/state/` does not travel between lane worktrees, and after the round-3 split the edits run in eight separate plans; a baseline committed in a plan file is the only one every later part and `q6epwc` can read. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/sdzcur/before/` showing one saved file per named command (eight commands plus the core gate line), and `git status --porcelain` printing nothing outside `.aw/state/` (no edit was made).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste table F-28 as committed, with an exit code per command, both rule-id multisets and both `check.stale-index-*` counts, and `git show --stat` of the `aw commit sdzcur` commit listing only this plan file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed, and before any other part of the `q6epwc` family. Honesty rule: paste the ACTUAL outputs; never claim a result you did not run. Commits: only through `aw commit sdzcur -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
