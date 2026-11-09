# IPD: Retarget the value writer tests part 2 to artifact_meta

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata writer (`artifact_meta`). Part 4 of the round-3 split of `k6jd6l` (Order 43, research `nj8zdp` guidance). This part retargets the last five of the ten test modules `k6jd6l` E-08 names. Measured call counts at `f83159217`: `tests/test_from_backlog_cardinality.py` 5, `tests/test_check_engine_from_spec_missing.py` 9, `tests/test_check_engine_spec_criteria.py` 1, `tests/test_backlog_handoff_close.py` 1, `tests/test_research_descriptive_safety.py` 2.
- Scope: The last five of the ten test modules of `k6jd6l` E-08, retargeted to `artifact_meta.append(..., dry_run=True)` or the setter CLI. EXCLUDES the first five (Order 282).
- Scope-Paths: tests/test_from_backlog_cardinality.py, tests/test_check_engine_from_spec_missing.py, tests/test_check_engine_spec_criteria.py, tests/test_backlog_handoff_close.py, tests/test_research_descriptive_safety.py, .aw/records/plans/pending/20261109-metastore-283-6v4uao-retarget-the-value-writer-tests-part-2-to-artifact-meta.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15, executed:tfvby1
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 283
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6v4uao

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from k6jd6l (round 3, research nj8zdp guidance).

## Goal

None of these five test modules calls an original value writer, and each keeps every input case.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Carried from `k6jd6l` E-08 (see Order 282 for the quoted text); this part's subset plus Order 282's equals the original ten modules. Save the before-list of all five modules to `.aw/state/9o83cr/E-08-tests2-before.txt` before E-01.

PIN RULE (carried from `9o83cr`): before an edit that deletes or retargets, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > <before-file>`); after it, run the same command into the matching after-file. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: one test module per item

- [ ] E-01 Retarget `tests/test_from_backlog_cardinality.py` to `artifact_meta.append(..., dry_run=True)` (or the setter CLI), asserting on the rendered text; keep every input case.
  - Depends on: none
  - Expected outcome: `tests/test_from_backlog_cardinality.py` calls no original value writer and passes.
  - Execution state: pending

- [ ] E-02 Retarget `tests/test_check_engine_from_spec_missing.py` to `artifact_meta.append(..., dry_run=True)` (or the setter CLI), asserting on the rendered text; keep every input case.
  - Depends on: E-01
  - Expected outcome: `tests/test_check_engine_from_spec_missing.py` calls no original value writer and passes.
  - Execution state: pending

- [ ] E-03 Retarget `tests/test_check_engine_spec_criteria.py` to `artifact_meta.append(..., dry_run=True)` (or the setter CLI), asserting on the rendered text; keep every input case.
  - Depends on: E-02
  - Expected outcome: `tests/test_check_engine_spec_criteria.py` calls no original value writer and passes.
  - Execution state: pending

- [ ] E-04 Retarget `tests/test_backlog_handoff_close.py` to `artifact_meta.append(..., dry_run=True)` (or the setter CLI), asserting on the rendered text; keep every input case.
  - Depends on: E-03
  - Expected outcome: `tests/test_backlog_handoff_close.py` calls no original value writer and passes.
  - Execution state: pending

- [ ] E-05 Retarget `tests/test_research_descriptive_safety.py` to `artifact_meta.append(..., dry_run=True)` (or the setter CLI), asserting on the rendered text; keep every input case. Then commit through `aw commit 6v4uao -- <paths>`.
  - Depends on: E-04
  - Expected outcome: `tests/test_research_descriptive_safety.py` calls no original value writer and passes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `tests/test_from_backlog_cardinality.py` also calls `ipd_schema.parse_metadata_block` once; Order 287 owns that reference, not this plan.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `history(id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`), and the legacy loader (`load_legacy_artifact`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-09 at `f83159217` with `rg -o "set_[a-z_]+_line|_set_priority_line" <module> | sort | uniq -c`: see the Concern.

## Proposed changes (ordered, validatable)

1. Retarget `test_from_backlog_cardinality` (E-01).
2. Retarget `test_check_engine_from_spec_missing` (E-02).
3. Retarget `test_check_engine_spec_criteria` (E-03).
4. Retarget `test_backlog_handoff_close` (E-04).
5. Retarget `test_research_descriptive_safety` and commit (E-05).

## Deferred / out of scope (with reason)

- Deleting the original writers.
  - Carrier: zs7a45

## Scope check

- Over-scope: none.
- Under-scope: none known. Size: 5 E-items, 5 work Scope-Paths.

## Required tests / validation

The five modules (PIN lists); commit the last item through `aw commit 6v4uao -- <paths>`.

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Open questions

### OQ-01: `tests/test_research_descriptive_safety.py` also calls `research_contract.parse_frontmatter`; is that in scope?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No; Order 289 retargets those calls. This plan changes only the `_set_priority_line` calls. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `rg -n "set_[a-z_]+_line|_set_priority_line" tests/test_from_backlog_cardinality.py` printing no call, and the before/after per-test lines of `tests/test_from_backlog_cardinality.py` from the PIN lists with each renamed test mapped and no FAILED or ERROR line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "set_[a-z_]+_line|_set_priority_line" tests/test_check_engine_from_spec_missing.py` printing no call, and the before/after per-test lines of `tests/test_check_engine_from_spec_missing.py` from the PIN lists with each renamed test mapped and no FAILED or ERROR line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "set_[a-z_]+_line|_set_priority_line" tests/test_check_engine_spec_criteria.py` printing no call, and the before/after per-test lines of `tests/test_check_engine_spec_criteria.py` from the PIN lists with each renamed test mapped and no FAILED or ERROR line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "set_[a-z_]+_line|_set_priority_line" tests/test_backlog_handoff_close.py` printing no call, and the before/after per-test lines of `tests/test_backlog_handoff_close.py` from the PIN lists with each renamed test mapped and no FAILED or ERROR line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "set_[a-z_]+_line|_set_priority_line" tests/test_research_descriptive_safety.py` printing no call, and the before/after per-test lines of `tests/test_research_descriptive_safety.py` from the PIN lists with each renamed test mapped and no FAILED or ERROR line. Also paste `git show --stat` of the `aw commit 6v4uao` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Pin-first where an item deletes or retargets. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit 6v4uao -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
