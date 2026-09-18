# IPD: Attention view correctness and drift audit fixes

- Date: 2026-09-17
- Kind: child
- Concern: bugs
- Scope: agent_workflows/attention.py and attention regression tests
- Scope-Paths: agent_workflows/attention.py,tests/test_attention.py,tests/test_releases.py
- Item-Dependencies: none
- Status: to-review
- Set: attcor (attention-correctness)
- Order: 1
- Highest E allocated: 13
- Author: Antigravity
- Id: rkn8ya

## Workflow history

- 2026-09-17 to-review (Antigravity): /assess bugs: assessed; proposed 14 changes.

## Goal

Remediate 14 bugs and contract violations discovered during the /assess-bugs audit of `agent_workflows/attention.py`, ensuring fail-closed drift filtering under CLI flags, precise release blocker matching, modern .aw disposition checking, elimination of absolute path leaks, and robust set name grammar parsing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fail-closed drift filtering and path sanitization

- [ ] E-01 Fix drift filtering in `run()` to retain drift records from selected trees when files fail to parse into items.
  - Depends on: none
  - Expected outcome: `aw attention -t plans --check` fails closed when an invalid plan exists.
  - Execution state: pending
- [ ] E-02 Pass `Path(rel)` to `specs_mod.validate_spec` in `_spec_record` to eliminate absolute path leaks.
  - Depends on: none
  - Expected outcome: Drift locations for specs are repo-relative POSIX paths.
  - Execution state: pending
- [ ] E-03 Extend unclassified tree checks in `scan()` to detect unclassified files under `.aw/records/`.
  - Depends on: none
  - Expected outcome: Rogue files under `.aw/records/` emit `attention.unclassified-tree`.
  - Execution state: pending

### Task group 2: Filter matching and disposition logic

- [ ] E-04 Fix `matches_blocking` to validate `tok == "next"` against planned release metadata instead of unconditionally returning True.
  - Depends on: none
  - Expected outcome: `aw att --blocking next` excludes items blocking past or different releases.
  - Execution state: pending
- [ ] E-05 Update disposition mismatch detection to support `.aw/records/plans/` paths and non-terminal plan statuses in terminal directories.
  - Depends on: none
  - Expected outcome: Plans in wrong disposition directories emit `attention.disposition-mismatch`.
  - Execution state: pending
- [ ] E-06 Normalize `med` alias to `medium` in `parse_priority_filters` and `_PRIORITY_SORT_RANK`.
  - Depends on: none
  - Expected outcome: `aw att --priority med` matches medium-priority items.
  - Execution state: pending
- [ ] E-07 Refactor `--open-questions` filtering in `run()` to filter visible items instead of mutating `items` in-place.
  - Depends on: none
  - Expected outcome: JSON and diagnostic outputs preserve all items when `--open-questions` is passed.
  - Execution state: pending

### Task group 3: Grammar parsing, ordering, and rendering

- [ ] E-08 Update `_NAME_GRAMMAR_RE` to allow hyphens in set IDs and optional trailing slugs.
  - Depends on: none
  - Expected outcome: Plans with hyphenated set IDs sort correctly under `-o set,order`.
  - Execution state: pending
- [ ] E-09 Update `-o blocking` sort helper to treat `blocks_release == "-"` as absent rather than top priority.
  - Depends on: none
  - Expected outcome: Non-blocking items sort below active release blockers.
  - Execution state: pending
- [ ] E-10 Update `_extract_detail` to recognize unbulleted YAML keys in research frontmatter.
  - Depends on: none
  - Expected outcome: Research summaries and questions display properly under `--details`.
  - Execution state: pending
- [ ] E-11 Refine status column truncation and readiness color checks to avoid collision between `implementing` and `implemented`.
  - Depends on: none
  - Expected outcome: Visual distinction between active and completed work in table view.
  - Execution state: pending
- [ ] E-12 Clean up duplicate `return 3` statement and fix `arcive_state` typo in `attention.py`.
  - Depends on: none
  - Expected outcome: Clean code without dead statements or misnamed attributes.
  - Execution state: pending

### Task group 4: Regression test suite

- [ ] E-13 Add regression tests for all 14 audit findings across `tests/test_attention.py` and `tests/test_releases.py`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-12
  - Expected outcome: All new regression tests pass cleanly.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Clustered plan naming `YYYYMMDD-<setid>-NN-<id6>-<slug>.ipd.md` in `.aw/records/plans/pending/`.
- Fail-closed invariant on `aw attention --check`.
- Absolute path sanitization in all agent/human outputs.

## Findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| F-01 | Blocker | Low (functionality) | QA engineer | Filter matching purges contract violations breaking fail-closed invariant |
| F-02 | High | Low (functionality) | Software engineer | `--blocking next` short-circuits and matches all gated items across all releases |
| F-03 | High | Low (functionality) | QA engineer | Disposition-mismatch check is silently dead under `.aw` layout |
| F-04 | Medium | Low (functionality) | Data integrity | `attention.unclassified-tree` drift suppressed for `.aw/records/` files |
| F-05 | Medium | Low (security) | Security engineer | Machine-local absolute path leaked in spec contract violations |
| F-06 | Medium | Low (functionality) | Software engineer | Set and order sorting regex rejects hyphenated set IDs |
| F-07 | Medium | Low (usability) | Novice user | Column truncation collides `implementing` with `implemented` |
| F-08 | Medium | Low (functionality) | Software engineer | Non-blocking marker `"-"` sorted ahead of real blockers in `-o blocking` |
| F-09 | Medium | Low (functionality) | Software engineer | `last_history_at` reads oldest entry instead of latest on prepended history |
| F-10 | Low | Low (complexity) | Performance engineer | Multiple redundant file reads and uncached scans in plans and releases |
| F-11 | Low | Low (usability) | Operator | Priority filter and sort rejects `med` alias |
| F-12 | Low | Low (functionality) | Software engineer | In-place mutation of `items` by `--open-questions` filter |
| F-13 | Low | Low (functionality) | Software engineer | `_extract_detail` fails on YAML frontmatter in research documents |
| F-14 | Low | Low (complexity) | Software engineer | Duplicate return statement and typo in `active_state` attribute lookup |

## Proposed changes (ordered, validatable)

1. Retain drift records from selected scan trees even when parsing fails (Low Remediation Risk).
2. Pass `Path(rel)` to `specs_mod.validate_spec` (Low Remediation Risk).
3. Extend unclassified tree checks to `.aw/records/` (Low Remediation Risk).
4. Validate `tok == "next"` against planned release ID/version (Low Remediation Risk).
5. Support `.aw/records/plans/` paths in disposition mismatch check (Low Remediation Risk).
6. Normalize `med` priority alias (Low Remediation Risk).
7. Preserve items list during `--open-questions` filtering (Low Remediation Risk).
8. Update `_NAME_GRAMMAR_RE` for hyphenated sets (Low Remediation Risk).
9. Fix `-o blocking` sort ranking for non-blocking marker (Low Remediation Risk).
10. Support unbulleted YAML keys in `_extract_detail` (Low Remediation Risk).
11. Fix column truncation and readiness color checks (Low Remediation Risk).
12. Remove dead code and attribute typos (Low Remediation Risk).
13. Add regression tests for each finding (Low Remediation Risk).

## Deferred / out of scope (with reason)

- None. All 14 findings have Low Remediation Risk and are proposed for remediation.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Bare test suite: `python3 -m pytest`
- Targeted tests: `python3 -m pytest tests/test_attention.py tests/test_releases.py`

## Spec / documentation sync

- N/A. Preserves existing attention view contracts and specifications.

## Open questions

### OQ-01: Historical prepended history parsing

- Blocking: no
- Status: open
- Owner: Antigravity
- Resolution or deferral rationale: Existing parser in `attention_contract.py` can parse all timestamps and select the maximum date rather than relying on line order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Test confirms `aw att -t plans --check` fails when an unparseable plan is present.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Drift output from spec validation contains repo-relative path, zero absolute paths.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Test confirms unclassified file under `.aw/records/` triggers `attention.unclassified-tree`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Test confirms `--blocking next` excludes items blocking non-planned releases.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Test confirms plan in `.aw/records/plans/executed/` with draft status triggers `attention.disposition-mismatch`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Test confirms `aw att --priority med` matches medium priority items.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Test confirms `--open-questions --format json` retains complete item inventory.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: Test confirms plan with set `prompt-lib` sorts under `prompt-lib` in `-o set`.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: Test confirms `-o blocking` places `"-"` items after actual blocking items.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: Test confirms research YAML frontmatter `summary:` appears in `--details`.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: Test confirms `implementing` displays distinct text from `implemented`.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: Static check confirms absence of duplicate return statements and typos.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: Suite `python3 -m pytest tests/test_attention.py tests/test_releases.py` passes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must be human-approved before execution and is not auto-run.
