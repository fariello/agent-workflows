# IPD: Delete the inline check_engine metadata regex literals

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 and 4.3 require deleting every `^-` metadata regex literal outside `artifact_meta`. Besides its named patterns, `agent_workflows/check_engine.py` has eight inline `^-` literals inside six rule functions. This is part 3 of the round-3 split of `e8420v` (Order 45), carrying the inline subset of `e8420v` E-12.
- Scope: delete the eight inline literals, each use reading the value through `artifact_meta.read`, `read_text` or `read_at`; confirm the two `body prose` rows stay; update comments in `check_engine` that cite a deleted literal. EXCLUDES the parsers (Order 239) and named patterns (Order 240).
- Scope-Paths: agent_workflows/check_engine.py, .aw/records/plans/pending/20261109-metastore-241-bcrko1-delete-the-inline-check-engine-metadata-regex-literals.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:js35bz, executed:k6jd6l, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 241
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: bcrko1

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from e8420v (round 3, research nj8zdp guidance).

## Goal

After this plan, the `^-` literal search over `agent_workflows/check_engine.py` prints only the two `body prose` rows, and both `aw check all` rule multisets equal the `786w7r` F-30 baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`e8420v` E-12's list is split across Orders 239, 240 and 241; this plan takes "the inline literals in `_artifact_compact_date`, `evaluate_handoff_ready`, `check_spec_review_attestation`, `find_obligations_carried_by`, `check_ipd_lint_reach` and `check_orchestrator_not_review_ready` (three). Classed `body prose` (kept, N3) unless E-01 shows otherwise: `_TARGET_BULLET_RE` (Concern/Scope/Scope-Paths prose targets), the `parse_spec_acceptance_criteria` table-rule literal (`^-+$`, a Markdown table divider)." The search is `LIT` from `786w7r`.

PIN RULE (carried from `9o83cr`): before E-01, save the per-test outcome list of every `tests/test_check_engine*.py` module to `.aw/state/bcrko1/before.txt` (command as in `js35bz`); after E-03, the same into `after.txt`.

### Task group 1: inline literals, then verify

- [ ] E-01 Delete the inline literals in the three date and handoff rules: `check_engine._artifact_compact_date`, `check_engine.evaluate_handoff_ready`, `check_engine.check_spec_review_attestation`.
  - Depends on: none
  - Expected outcome: the `LIT` search over those three functions prints nothing.
  - Execution state: pending

- [ ] E-02 Delete the inline literals in `check_engine.find_obligations_carried_by` and `check_engine.check_ipd_lint_reach`.
  - Depends on: E-01
  - Expected outcome: the `LIT` search over those two functions prints nothing.
  - Execution state: pending

- [ ] E-03 Delete the three inline literals in `check_engine.check_orchestrator_not_review_ready`.
  - Depends on: E-02
  - Expected outcome: the `LIT` search over that function prints nothing.
  - Execution state: pending

- [ ] E-04 Re-run the `LIT` search over `agent_workflows/check_engine.py` (only `_TARGET_BULLET_RE` and the `parse_spec_acceptance_criteria` table-rule literal may remain), save `after.txt`, run every `tests/test_check_engine*.py` module, compare both `aw check all` multisets with `786w7r` F-30, and commit through `aw commit bcrko1 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-03
  - Expected outcome: only the two `body prose` rows remain; tests pass; multisets equal F-30.
  - Execution state: pending

## Project conventions discovered (Step 0)

- N3 keeps Markdown body bullets and prose targets out of `artifact_meta`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured at `ac76110f4` (`e8420v` F-26): 8 inline literals in 6 functions, 2 `body prose` rows. `786w7r` F-26 re-derives them.

## Proposed changes (ordered, validatable)

1. Delete the inline literals in three passes (E-01 to E-03).
2. Verify and commit (E-04).

## Deferred / out of scope (with reason)

- The `runner_shared`, `status_set` and `releases` literals: Orders 242 and 243.
  - Carrier: e8420v

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 1 work Scope-Path.

## Required tests / validation

Every `tests/test_check_engine*.py` module (PIN lists), the two `aw check all` multisets, then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3.

## Open questions

### OQ-01: May `_TARGET_BULLET_RE` be deleted too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. It matches Concern/Scope/Scope-Paths prose targets inside the body, which N3 keeps outside `artifact_meta`; `9o83cr` E-14 lists it in the exclusion file. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` hunks of `check_engine._artifact_compact_date`, `check_engine.evaluate_handoff_ready` and `check_engine.check_spec_review_attestation`, each removing a `^-` literal.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` hunks of `check_engine.find_obligations_carried_by` and `check_engine.check_ipd_lint_reach`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk of `check_engine.check_orchestrator_not_review_ready` removing three literals.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `LIT` search over `agent_workflows/check_engine.py` showing only the two `body prose` rows, `diff .aw/state/bcrko1/before.txt .aw/state/bcrko1/after.txt` (empty, or each change mapped), the two rule-id multiset diffs against `786w7r` F-30 (empty), and `git show --stat` of the `aw commit bcrko1` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first. Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit bcrko1 -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
