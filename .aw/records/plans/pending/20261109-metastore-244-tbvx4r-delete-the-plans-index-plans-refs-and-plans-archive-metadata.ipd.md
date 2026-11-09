# IPD: Delete the plans_index plans_refs and plans_archive metadata regex literals

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 and 4.3 require deleting every `^-` metadata regex outside `artifact_meta`. `plans_index`, `plans_refs` and `plans_archive` hold 16 such literals, including `plans_index._META_RE` and its reader `plans_index._meta`, which `9o83cr` E-12 names. This is part 1 of the round-3 split of `0xsx2n` (Order 46), carrying the plans-module subset of `0xsx2n` E-21.
- Scope: delete the 16 literals in three modules, each use reading through `artifact_meta.read`, `read_text` or `read_at`; update `tests/test_plans_archive.py` where a test names a deleted pattern. EXCLUDES the artifact-family modules of E-21 (Order 245).
- Scope-Paths: agent_workflows/plans_index.py, agent_workflows/plans_refs.py, agent_workflows/plans_archive.py, tests/test_plans_archive.py, tests/test_plans_index.py, .aw/records/plans/pending/20261109-metastore-244-tbvx4r-delete-the-plans-index-plans-refs-and-plans-archive-metadata.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 244
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tbvx4r

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 0xsx2n (round 3, research nj8zdp guidance).

## Goal

After this plan, the `LIT` search over `plans_index`, `plans_refs` and `plans_archive` prints nothing, and `aw find plans --agent` matches the `786w7r` F-30 baseline.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

`0xsx2n` E-21's site list ("`plans_index` (6 module-level, including `_META_RE` and the `_meta` reader), `plans_refs` (5: `_ID_RE`, `_DATE_RE`, `_SET_LINE_RE`, `_ORDER_LINE_RE`, and the `order_lines` literal in `_set_metadata` if Order 43 left it), `plans_archive` (5: `_ID_RE`, and the inline literals in `_plan_date`, `_resolve_plan_date`, `_plan_status`, `sweep_candidates`), `artifact_rename` (5 ...), `artifact_refs` (1 ...), `artifact_adopt` (1 ...), `artifact_audit` (1 ...). Update `tests/test_artifact_audit.py` and `tests/test_plans_archive.py` where a test names a deleted pattern.") is split across Orders 244 and 245; this plan takes the `plans_index`, `plans_refs` and `plans_archive` sites and `tests/test_plans_archive.py`.

PIN RULE (carried from `9o83cr`): before E-01, save the per-test outcome list of the named test modules (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/tbvx4r/before.txt`); after the last edit, the same into `after.txt`. A retargeted test keeps every input case; a test edited because it names a deleted pattern is justified at finalize (`--scope-reason`) if it is outside Scope-Paths.

### Task group 1: one module per item, then verify

- [ ] E-01 In `agent_workflows/plans_index.py`, delete its 6 module-level `^-` literals, including `plans_index._META_RE` and the reader `plans_index._meta`; each caller reads through `artifact_meta.read_text`.
  - Depends on: none
  - Expected outcome: the `LIT` search over `agent_workflows/plans_index.py` prints nothing; `rg -n "_META_RE|def _meta\b" agent_workflows/plans_index.py` prints nothing.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/plans_refs.py`, delete `plans_refs._ID_RE`, `_DATE_RE`, `_SET_LINE_RE`, `_ORDER_LINE_RE` and, if `k6jd6l` left it, the `order_lines` literal.
  - Depends on: E-01
  - Expected outcome: the `LIT` search over `agent_workflows/plans_refs.py` prints nothing.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/plans_archive.py`, delete `plans_archive._ID_RE` and the inline literals in `plans_archive._plan_date`, `_resolve_plan_date`, `_plan_status` and `sweep_candidates`.
  - Depends on: E-02
  - Expected outcome: the `LIT` search over `agent_workflows/plans_archive.py` prints nothing.
  - Execution state: pending

- [ ] E-04 Update `tests/test_plans_archive.py` and `tests/test_plans_index.py` only where a case names a deleted pattern; save `after.txt`; run both modules; compare `aw find plans --agent` with `786w7r` F-30; commit through `aw commit tbvx4r -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-03
  - Expected outcome: both modules pass; the `aw find plans` hash equals F-30.
  - Execution state: pending

## Project conventions discovered (Step 0)

- N3 keeps Markdown body bullets (open-question rows, E/V checklist fields, review rounds and findings) outside `artifact_meta`; their patterns are `body prose` and stay, and `9o83cr` E-14 lists them in its exclusion file.
- A literal inside a function that REWRITES a bullet is a writer; its replacement is an `artifact_meta.append` event, not a read (carried from `0xsx2n`).
- The search `LIT` is defined in `786w7r`; table F-27 there classes every site of this plan.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured at `ac76110f4` (`0xsx2n` F-27): `plans_index` 6, `plans_refs` 5, `plans_archive` 5 literals. `786w7r` F-27 re-derives them.

## Proposed changes (ordered, validatable)

1. Delete the `plans_index` literals and `_meta` (E-01).
2. Delete the `plans_refs` literals (E-02).
3. Delete the `plans_archive` literals (E-03).
4. Update tests, verify and commit (E-04).

## Deferred / out of scope (with reason)

- Every other module of `9o83cr` E-12, and the family-wide comparison.
  - Carrier: 0xsx2n

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 4 E-items, 5 work Scope-Paths.

## Required tests / validation

`tests/test_plans_archive.py`, `tests/test_plans_index.py` (PIN lists), then the bare core gate `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3.

## Open questions

### OQ-01: What if F-27 classes a listed site `already gone`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Record it in the V-item evidence and move on; a site an earlier reader plan removed needs no edit. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `LIT` search over `agent_workflows/plans_index.py` and `rg -n "_META_RE|def _meta\b" agent_workflows/plans_index.py`, both printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `LIT` search over `agent_workflows/plans_refs.py` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `LIT` search over `agent_workflows/plans_archive.py` printing nothing, and a fixture `aw archive plans` dry run whose candidate list equals the pre-edit run's.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/tbvx4r/before.txt .aw/state/tbvx4r/after.txt` (empty, or each change mapped), the summary line of `python3 -m pytest -o addopts="" tests/test_plans_archive.py tests/test_plans_index.py` passing, the `aw find plans --agent | sha256sum` beside the `786w7r` F-30 hash, and `git show --stat` of the `aw commit tbvx4r` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first. Scope fence: a needed file outside `- Scope-Paths:` is edited and then justified at finalize (`--scope-reason`). Honesty rule: paste the ACTUAL summary lines. Commits: only through `aw commit tbvx4r -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
