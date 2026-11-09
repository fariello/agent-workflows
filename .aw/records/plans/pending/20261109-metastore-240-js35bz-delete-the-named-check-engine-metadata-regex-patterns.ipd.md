# IPD: Delete the named check_engine metadata regex patterns

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 and 4.3 require deleting every `^-` metadata regex literal outside `artifact_meta`. `agent_workflows/check_engine.py` defines 19 named module-level patterns that each parse one front-matter bullet. This is part 2 of the round-3 split of `e8420v` (Order 45), carrying the named-pattern subset of `e8420v` E-12.
- Scope: delete the 19 named patterns in four groups, each use reading the value through `artifact_meta.read`, `read_text` or `read_at` at its caller, and update comments in `check_engine` that cite a deleted pattern. EXCLUDES the three parsers (Order 239), the inline literals (Order 241), and the two `body prose` patterns `_TARGET_BULLET_RE` and the `parse_spec_acceptance_criteria` table-rule literal (kept, N3).
- Scope-Paths: agent_workflows/check_engine.py, .aw/records/plans/pending/20261109-metastore-240-js35bz-delete-the-named-check-engine-metadata-regex-patterns.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:7uq6xg, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 240
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: js35bz

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from e8420v (round 3, research nj8zdp guidance).

## Goal

After this plan, none of the 19 named patterns is defined in `check_engine`, and `aw check all --agent` and `aw check all --all --agent` report the same rule multisets as the `786w7r` F-30 baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`e8420v` E-12's list is split across Orders 239, 240 and 241; this plan takes "the named patterns `_ID_LINE_RE`, `_SET_LINE_RE`, `_IDENT_ID_BULLET_RE`, `_IDENT_SET_BULLET_RE`, `_STATUS_META_RE`, `_ITEM_ID_RE`, `_ITEM_PRIORITY_RE`, `_ITEM_WORK_KIND_RE`, `_META_BLOCKS_RELEASE_RE`, `_META_CLOSE_EVIDENCE_RE`, `_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE` (defined twice), `_PLAN_STATUS_RE`, `_ITEM_DEPENDENCIES_RE`, `_DATE_LINE_RE`, `_REVIEW_SUBJECT_TYPE_RE`, `_FROM_SPEC_LINE_RE`, `_SCOPE_PATHS_LINE_RE`, `_CARRIER_DATE_RE`". Each group below is one edit pass in `agent_workflows/check_engine.py`: delete the pattern, change each use to the `artifact_meta` field of the same name, fix a comment that cites it. If F-26 classes a pattern `already gone`, record that and move on.

PIN RULE (carried from `9o83cr`): before E-01, save the per-test outcome list of every `tests/test_check_engine*.py` module (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA tests/test_check_engine*.py | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/js35bz/before.txt`); after E-04, the same into `after.txt`. A test edited because it names a deleted pattern keeps every input case and is justified at finalize (`--scope-reason`).

### Task group 1: four pattern groups, then verify

- [ ] E-01 Group A (identity and status): delete `_ID_LINE_RE`, `_SET_LINE_RE`, `_IDENT_ID_BULLET_RE`, `_IDENT_SET_BULLET_RE`, `_STATUS_META_RE`, `_PLAN_STATUS_RE`.
  - Depends on: none
  - Expected outcome: `rg -n "\b(_ID_LINE_RE|_SET_LINE_RE|_IDENT_ID_BULLET_RE|_IDENT_SET_BULLET_RE|_STATUS_META_RE|_PLAN_STATUS_RE)\b" agent_workflows/check_engine.py` prints nothing.
  - Execution state: pending

- [ ] E-02 Group B (item fields): delete `_ITEM_ID_RE`, `_ITEM_PRIORITY_RE`, `_ITEM_WORK_KIND_RE`, `_ITEM_DEPENDENCIES_RE`, `_DATE_LINE_RE`.
  - Depends on: E-01
  - Expected outcome: `rg -n "\b(_ITEM_ID_RE|_ITEM_PRIORITY_RE|_ITEM_WORK_KIND_RE|_ITEM_DEPENDENCIES_RE|_DATE_LINE_RE)\b" agent_workflows/check_engine.py` prints nothing.
  - Execution state: pending

- [ ] E-03 Group C (gate and provenance fields): delete `_META_BLOCKS_RELEASE_RE`, `_META_CLOSE_EVIDENCE_RE`, `_META_FROM_BACKLOG_RE`, both definitions of `_ITEM_FROM_SPEC_RE`, and `_FROM_SPEC_LINE_RE`.
  - Depends on: E-02
  - Expected outcome: `rg -n "\b(_META_BLOCKS_RELEASE_RE|_META_CLOSE_EVIDENCE_RE|_META_FROM_BACKLOG_RE|_ITEM_FROM_SPEC_RE|_FROM_SPEC_LINE_RE)\b" agent_workflows/check_engine.py` prints nothing.
  - Execution state: pending

- [ ] E-04 Group D (review and scope fields): delete `_REVIEW_SUBJECT_TYPE_RE`, `_SCOPE_PATHS_LINE_RE`, `_CARRIER_DATE_RE`.
  - Depends on: E-03
  - Expected outcome: `rg -n "\b(_REVIEW_SUBJECT_TYPE_RE|_SCOPE_PATHS_LINE_RE|_CARRIER_DATE_RE)\b" agent_workflows/check_engine.py` prints nothing.
  - Execution state: pending

- [ ] E-05 Save `after.txt`, run every `tests/test_check_engine*.py` module, compare `aw check all --agent` and `aw check all --all --agent` rule-id multisets with `786w7r` F-30, and commit through `aw commit js35bz -- <paths>` with only Scope-Paths files (or justified test paths); never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-04
  - Expected outcome: the modules pass; both multisets equal F-30.
  - Execution state: pending

## Project conventions discovered (Step 0)

- N3 keeps Markdown body bullets (open-question rows, E/V checklist fields, prose targets) out of `artifact_meta`; their patterns are `body prose` and stay.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured at `ac76110f4` (`e8420v` F-26): `check_engine` has 30 `^-` literals, of which these 19 named patterns (20 definitions), 8 inline literals (Order 241) and 2 `body prose` rows. `786w7r` F-26 re-derives the list before this plan runs.

## Proposed changes (ordered, validatable)

1. Delete groups A to D (E-01 to E-04).
2. Verify and commit (E-05).

## Deferred / out of scope (with reason)

- The inline literals of `check_engine`: Order 241.
  - Carrier: e8420v

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 1 work Scope-Path.

## Required tests / validation

Every `tests/test_check_engine*.py` module (PIN lists), the two `aw check all` multisets, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3.

## Open questions

### OQ-01: What if a group's use is in a function Orders 29 to 33 already moved?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Then the pattern has no use left; delete the definition only, and F-26 shows it. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the E-01 `rg` command printing nothing (group A, six names).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the E-02 `rg` command printing nothing (group B, five names).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the E-03 `rg` command printing nothing (group C, five names, both `_ITEM_FROM_SPEC_RE` definitions).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the E-04 `rg` command printing nothing (group D, three names).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `diff .aw/state/js35bz/before.txt .aw/state/js35bz/after.txt` (empty, or each change mapped), the per-module summary of `python3 -m pytest -o addopts="" tests/test_check_engine*.py`, the two rule-id multiset diffs against `786w7r` F-30 (empty), and `git show --stat` of the `aw commit js35bz` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first. Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit js35bz -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
