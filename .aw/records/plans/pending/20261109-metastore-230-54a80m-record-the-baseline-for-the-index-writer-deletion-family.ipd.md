# IPD: Record the baseline for the INDEX writer deletion family

- Date: 2026-11-09
- Kind: child
- Concern: The finishing item of `snin8q` (E-17) compares the `aw check <type> --all` rule multisets and the `aw ipd board` output after the family's deletions against a baseline taken BEFORE any of them. `.aw/state/` is gitignored and does not travel between lane worktrees, so after the round-3 split the baseline must be committed in a plan file. This is the first part of the round-3 split of `snin8q` (Order 42), carrying `snin8q` E-01.
- Scope: run the read-only baseline commands, write their results into this plan's table F-29, and commit this plan file. EXCLUDES every code or test edit (Orders 231 to 237 of the split, and `snin8q`).
- Scope-Paths: .aw/records/plans/pending/20261109-metastore-230-54a80m-record-the-baseline-for-the-index-writer-deletion-family.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:q6epwc, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 230
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 54a80m

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from snin8q (round 3, research nj8zdp guidance).

## Goal

Commit, inside this plan, the pre-deletion outputs that `snin8q` E-17 and Order 236 compare against, so the comparison survives the lane worktrees of the other parts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The text of `snin8q` E-01 is split across E-01 and E-02 here; together they equal it. Every other part of the family depends on this plan.

### Task group 1: baseline

- [ ] E-01 On the unedited tree, save under the gitignored `.aw/state/54a80m/before/` (never `/tmp`) the stdout and exit code of `aw check plans --all --agent`, `aw check research --all --agent`, `aw check prompts --all --agent` (rule-id multisets, `jq -r '.diagnostics[].rule' | sort | uniq -c`), `aw find plans --agent`, `aw ipd board` (as `board.txt`), and the bare core gate summary line of `python3 -m pytest`.
  - Depends on: none
  - Expected outcome: the saved outputs exist under `.aw/state/54a80m/before/`.
  - Execution state: pending

- [ ] E-02 Copy into table F-29 of this plan each command's exit code, the three rule-id multisets in full, the line count of `aw find plans --agent`, the full `aw ipd board` output inside a fenced block, and the core gate summary line. Commit this plan file through `aw commit 54a80m -- <this plan's path>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-01
  - Expected outcome: F-29 holds every value; the commit lists only this plan file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `check_engine.check_content` reaches each `check_drift` function on the `--all` path.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-29 | (written by E-02) exit codes, three rule-id multisets, `aw find plans` line count, the `aw ipd board` output and the core gate summary line, before any deletion of the family | `snin8q` E-17 and Order 236 compare against this table. |

## Proposed changes (ordered, validatable)

1. Run and save the baseline (E-01).
2. Write F-29 and commit (E-02).

## Deferred / out of scope (with reason)

- Every code and test edit of the family: Orders 231 to 237 and `snin8q`.
  - Carrier: snin8q

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 2 E-items, 0 work Scope-Paths (this plan file only).

## Required tests / validation

No test is written. The commands are read-only.

## Spec / documentation sync

N/A: this plan records measurements only.

## Open questions

### OQ-01: Why a separate baseline plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `.aw/state/` does not travel between lane worktrees, and the deletions now run in seven separate plans; a committed table is the only baseline all of them can read. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/54a80m/before/` showing one saved file per named command (five commands plus the core gate line, with `board.txt`), and `git status --porcelain` showing no edit outside `.aw/state/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste table F-29 as committed, with an exit code per command, the three multisets and the board block, and `git show --stat` of the `aw commit 54a80m` commit listing only this plan file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed, and before any other part of the `snin8q` family. Honesty rule: paste the ACTUAL outputs. Commits: only through `aw commit 54a80m -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
