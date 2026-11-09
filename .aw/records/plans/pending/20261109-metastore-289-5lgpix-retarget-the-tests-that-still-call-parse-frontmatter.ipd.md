# IPD: Retarget the tests that still call parse_frontmatter

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader (`artifact_meta`). Part 10 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance). Before Order 290 deletes `research_contract.parse_frontmatter`, eight test modules that call it must read through `artifact_meta.read_text` instead. Measured references at `f83159217`: `tests/test_research_cmd_create.py` 15, `tests/test_research_rename_frontmatter.py` 12, `tests/test_research_archive.py` 7, `tests/test_research_descriptive_safety.py` 5, `tests/test_artifact_adopt.py` 1, `tests/test_date_reader_clock_parity.py` 2, `tests/test_research_unsafe_field.py` 3, `tests/test_selector_two_dialect_readers.py` 2.
- Scope: Test retargets for the `parse_frontmatter` move of `k6jd6l` E-10 (`k6jd6l` named only the loader test modules; these eight were found on 2026-11-09 by running the E-10 search over `tests`). Items E-01 to E-04 take one large module each; E-05 takes the four small ones.
- Scope-Paths: tests/test_research_cmd_create.py, tests/test_research_rename_frontmatter.py, tests/test_research_archive.py, tests/test_research_descriptive_safety.py, tests/test_artifact_adopt.py, tests/test_date_reader_clock_parity.py, tests/test_research_unsafe_field.py, tests/test_selector_two_dialect_readers.py, .aw/records/plans/pending/20261109-metastore-289-5lgpix-retarget-the-tests-that-still-call-parse-frontmatter.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sq6v7i, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 289
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 5lgpix

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

No test module calls `research_contract.parse_frontmatter`; each keeps every input case.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Save the before-list of the eight modules to `.aw/state/9o83cr/E-10c-before.txt` before E-01. Each assertion that read a parsed dict now reads the matching `artifact_meta.State` field (or `State.fields`) from `artifact_meta.read_text(text, record_type="research")`.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: one test module per item, the four small ones together

- [ ] E-01 Retarget `tests/test_research_cmd_create.py` (15 references) from `parse_frontmatter` to `artifact_meta.read_text`, keeping every case.
  - Depends on: none
  - Expected outcome: `tests/test_research_cmd_create.py` calls no `parse_frontmatter` and passes.
  - Execution state: pending

- [ ] E-02 Retarget `tests/test_research_rename_frontmatter.py` (12 references) from `parse_frontmatter` to `artifact_meta.read_text`, keeping every case.
  - Depends on: E-01
  - Expected outcome: `tests/test_research_rename_frontmatter.py` calls no `parse_frontmatter` and passes.
  - Execution state: pending

- [ ] E-03 Retarget `tests/test_research_archive.py` (7 references) from `parse_frontmatter` to `artifact_meta.read_text`, keeping every case.
  - Depends on: E-02
  - Expected outcome: `tests/test_research_archive.py` calls no `parse_frontmatter` and passes.
  - Execution state: pending

- [ ] E-04 Retarget `tests/test_research_descriptive_safety.py` (5 references) from `parse_frontmatter` to `artifact_meta.read_text`, keeping every case.
  - Depends on: E-03
  - Expected outcome: `tests/test_research_descriptive_safety.py` calls no `parse_frontmatter` and passes.
  - Execution state: pending

- [ ] E-05 Retarget the four small modules, `tests/test_artifact_adopt.py`, `tests/test_date_reader_clock_parity.py`, `tests/test_research_unsafe_field.py`, `tests/test_selector_two_dialect_readers.py`, the same way; save the after-list; commit through `aw commit 5lgpix -- <paths>`.
  - Depends on: E-04
  - Expected outcome: no test calls `parse_frontmatter`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -c "parse_frontmatter" tests`: see the Concern.

## Proposed changes (ordered, validatable)

1. Retarget `test_research_cmd_create` (E-01).
2. Retarget `test_research_rename_frontmatter` (E-02).
3. Retarget `test_research_archive` (E-03).
4. Retarget `test_research_descriptive_safety` (E-04).
5. Retarget the four small modules and commit (E-05).

## Deferred / out of scope (with reason)

- Deleting `parse_frontmatter`.
  - Carrier: bxupy8

## Scope check

- Over-scope: none.
- Under-scope: These eight modules were not named in `k6jd6l` E-10; they are added because deleting the original would break them. Size: 5 E-items, 8 work Scope-Paths.

## Required tests / validation

The eight modules (PIN lists).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: Some tests assert on `parse_frontmatter` returning None for a malformed block; how is that kept?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Assert on the matching `artifact_meta.read_text` outcome (a defect or empty fields) and keep the case; if the observable differs, stop and report it in this plan rather than weakening the test. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "parse_frontmatter" tests/test_research_cmd_create.py` printing nothing and its before/after per-test lines with each rename mapped.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "parse_frontmatter" tests/test_research_rename_frontmatter.py` printing nothing and its before/after per-test lines with each rename mapped.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "parse_frontmatter" tests/test_research_archive.py` printing nothing and its before/after per-test lines with each rename mapped.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "parse_frontmatter" tests/test_research_descriptive_safety.py` printing nothing and its before/after per-test lines with each rename mapped.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "parse_frontmatter" tests` printing nothing, the before/after per-test lines of each of the four modules, and `git show --stat` of the `aw commit 5lgpix` commit.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit 5lgpix -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
