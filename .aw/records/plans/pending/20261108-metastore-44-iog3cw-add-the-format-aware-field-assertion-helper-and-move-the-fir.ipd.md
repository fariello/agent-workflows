# IPD: Add the format-aware field assertion helper and move the first setter-byte test assertions onto it

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` C10a requires `main` to read and write exactly one metadata format at every commit, so the cutover commit (Order 13, `cxxmyv`) must switch the format and every test that asserts on it at once. `cxxmyv` E-07 carried, as one item, "convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror" (`59aiyh` Deferred row). Measured 2026-11-07 at `ac76110f4`: `rg -n "assert.*['\"]- (Status|Priority|Blocks-Release|Work-Kind|From-Backlog|From-Spec|Readiness|Approval|Set|Order|Kind|Id|Gate-Kind|Gate-Ref|Item-Dependencies|Graduated-To|Close-Evidence|Release-Exempt-(Kind|Ref)):" tests`, minus lines over command output and minus the legacy-grammar test modules, prints 518 candidate lines in 81 test modules; the 7 modules that `k6jd6l` E-08 already retargets hold 51 of them, leaving 467 in 74 modules. Converting them inside the attended cutover would hide several hundred steps in one item of a plan that cannot be retried cheaply. This work CAN move earlier without changing `main`'s on-disk format: the helper asserts through the ACTIVE format, which is the legacy format until the cutover, so every converted test still checks the same bytes today and needs no edit when the cutover flips the builder. Part 1 of 2 of the preparation split from `cxxmyv`.
- Scope: `cxxmyv` E-07 (setter-byte half), split: batches S02 and S03 convert named module subsets (4 modules, 34 candidate lines at the split); E-12 finishes and assembles this part's F-28 table. The helper (E-01) and batch S04 (E-05) moved to `j5fqax`, and batch S01 (E-02) to `545ag7`, on 2026-11-09 (round-3 split). Batches S05 to S10 moved to `87rvs2` (Order 59) and `rdg0qv` (Order 60) on 2026-11-08; S11 to S20 are in `w13bkp` (Order 47), `aqc3m6` (Order 61) and `zgyna1` (Order 62). EXCLUDES: switching `RECORD_FORMAT` to `log` and the log-format branch of the helper (`cxxmyv` E-07, the cutover commit); displayed-output assertions; legacy-format subject tests; the `review-pilot` corpus; production code.
- Scope-Paths: tests/test_backlog_gate_follows_status.py, tests/test_backlog_new_gate_vocabulary.py, tests/test_backlog_positional_close_gate.py, tests/test_backlog_production.py, .aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:ya4ee4, executed:j5fqax, executed:545ag7
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 44
- Highest E allocated: 12
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: iog3cw
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): plan-review verified E/V bijection, Scope-Paths, batch rules, execution gate, and PIN rule; findings PR-001..PR-004 fixed; marked reviewed and go-pending-approval.
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-05 moved to j5fqax; E-02 moved to 545ag7 (as S01a and S01b).
- 2026-11-08 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): split per maintainer step-complexity rule (at most 4 batch items per plan); items E-06, E-07, E-08 (S05 to S07) moved to 87rvs2; E-09, E-10, E-11 (S08 to S10) moved to rdg0qv.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from cxxmyv per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every setter-byte assertion in the S02 and S03 modules goes through the format-aware field helper, with identical per-test outcomes before and after, so the cutover commit changes the helper and the builder and not these modules.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan:
1. Before any edits, create directory `mkdir -p .aw/state/iog3cw/` and record the unmodified per-test outcome list of the batch's modules: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/iog3cw/<batch>-before.txt`. For a batch restricted to named test classes, pass the `<module>::<Class>` node ids.
2. In each named module (or class), replace every SETTER-BYTE assertion with a call to the helper of `tests/record_builder.py` added by `j5fqax` E-01, formerly `iog3cw` E-01 (`assert_field(path, field, value)` and `assert_no_field(path, field)`). A setter-byte assertion is an `assertIn`/`assertNotIn`/`assert ... in` over the text of a RECORD FILE that names a front-matter bullet (`- Status:`, `- Priority:`, `- Blocks-Release:` and the other F-28 fields). An assertion over command OUTPUT (stdout, stderr, a rendered message) is a `displayed-output assertion` and is NOT converted; an assertion whose subject is the legacy grammar itself (a legacy-loader, migration or quoted-example test) is `legacy-format subject` and is NOT converted.
3. Re-run the same command into `<batch>-after.txt` and require `diff` to print nothing. A conversion that would change what a test checks (for example a test that asserts the exact bullet spelling, such as whitespace after the colon) stops and is reported with its node id; it is listed as `setter-byte, exact spelling` in F-28 for `cxxmyv`, not weakened.
4. Count the remaining matches of the F-28 pattern in the batch's modules and give each remaining line one class: `converted` (none should remain), `displayed-output assertion`, `legacy-format subject` or `setter-byte, exact spelling`.
5. The helper never reads production source, and no test gains a source-reading assertion.

### Task group 1: helper and batches

- [ ] E-03 Batch S02: ensure `.aw/state/iog3cw/` exists (`mkdir -p .aw/state/iog3cw/`) and convert the setter-byte assertions of `tests/test_backlog_gate_follows_status.py`, `tests/test_backlog_new_gate_vocabulary.py` (18 candidate assertion lines at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S02`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S02 outcome lists; the remaining F-28 matches in the batch's modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

- [ ] E-04 Batch S03: convert the setter-byte assertions of `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_production.py` (16 candidate assertion lines at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S03`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S03 outcome lists; the remaining F-28 matches in the batch's modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

### Task group 2: finish

- [ ] E-12 Finish this part: run the batch rule's command over the four modules of S02 and S03 once more and confirm the outcome multiset equals the union of their `-before.txt` lists; write F-28's remaining-match table for S01 to S04 (this plan's S02 and S03 rows plus the F-28 rows of `545ag7` for S01 and `j5fqax` for S04, copied with their source named) so the cutover (`x1mmdp`, carrying `cxxmyv` E-07) has the exact list of `setter-byte, exact spelling` rows it must still change; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit iog3cw -- <each changed path>`, one commit per batch allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-03, E-04
  - Expected outcome: the union comparison is empty; F-28 for this part is written; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Test data comes from ONE builder, `tests/record_builder.py` (`9rgn2w`/`59aiyh`), which writes through `artifact_meta`; `cxxmyv` E-07 switches it to `RECORD_FORMAT = "log"` in the cutover commit.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, so a complete comparison passes `-m ""`, and `pytest-randomly` is installed, so a deterministic order needs `-p no:randomly`.
- `artifact_meta.read_text(text, *, record_type=None) -> State` parses a record's text in either format (phase-B legacy loader), so the helper's legacy branch needs no new parser.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-28 | Candidate setter-byte lines at `ac76110f4` with the pattern in the Concern, minus lines whose subject is command output (`stdout`, `stderr`, `output`, `result.`, `proc.`, `captured`, `msg`, `message`) and minus legacy-grammar modules (`*legacy*`, `*m0001*`, `*migrat*`, `test_front_matter_loose*`, `test_selector_two_dialect*`, `test_history_block_bounding*`): 518 in 81 modules; minus the 7 modules `k6jd6l` E-08 retargets (51 lines): 467 in 74 modules, split into 20 batches S01 to S20 of at most about 30 lines (`tests/test_status_set.py`, 79 lines, is split by test class into S18 to S20). This part: S01, S02, S03, S04, 92 lines (S05 to S10, 128 lines, moved to `87rvs2` and `rdg0qv`). | Each batch is at most about 30 one-line conversions in at most 10 modules. The final table (written by E-12) lists every remaining match with its class. |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E03["1. Convert batch S02 assertions (E-03)<br/>tests/test_backlog_gate_follows_status.py, tests/test_backlog_new_gate_vocabulary.py"]
    E04["2. Convert batch S03 assertions (E-04)<br/>tests/test_backlog_positional_close_gate.py, tests/test_backlog_production.py"]
    E12["3. Finish, assemble F-28 & commit (E-12)<br/>PIN diffs, core gate, aw sanitize, aw commit"]

    E03 --> E04
    E04 --> E12
```

1. (Moved) the helper and S04: `j5fqax`; S01: `545ag7`. Convert S02 and S03 (E-03, E-04); the batches are independent.
2. Re-run the union, write F-28, run the core gate, commit (E-12).

## Deferred / out of scope (with reason)

- The helper (E-01) and batch S04 (E-05). Moved to j5fqax (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: j5fqax
- Batch S01 (E-02), as S01a and S01b. Moved to 545ag7 (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: 545ag7
- Batches S05, S06, S07: Moved to 87rvs2 (split 2026-11-08 per maintainer step-complexity rule; at most 4 batch items per plan).
  - Carrier: 87rvs2
- Batches S08, S09, S10: Moved to rdg0qv (split 2026-11-08 per maintainer step-complexity rule; at most 4 batch items per plan).
  - Carrier: rdg0qv
- Switching the builder to `RECORD_FORMAT = "log"`, adding the helper's log-format branch, and changing the `setter-byte, exact spelling` rows F-28 lists: they change the on-disk format and so belong to the cutover commit (C10a).
  - Carrier: cxxmyv
- Batches S11 to S14.
  - Carrier: w13bkp
- Batches S15 to S20.
  - Carrier: aqc3m6
- The value-writer test modules (`tests/test_releases_line_writers.py`, `tests/test_releases_sibling_line_writers_bounding.py`, `tests/test_blocks_release_reader_bounding.py`, `tests/test_backlog_metadata_duplicate_and_gate_summary.py`, `tests/test_from_backlog_cardinality.py`, `tests/test_check_engine_from_spec_missing.py`, `tests/test_backlog_handoff_close.py`): retargeted by `k6jd6l` E-08.
  - Carrier: k6jd6l

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none known. Size: 3 E-items (2 batches and the finish), 4 work Scope-Paths entries.

## Required tests / validation

Each batch is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, the same inputs, the same outcomes, with each assertion at least as strict as before. The helper's own test module is `j5fqax`'s. Commands: the batch rule's command per batch, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; prepares part of `4sd62s` section 6 and section 7 step 9 (the test-data half of the cutover) without changing the on-disk format.

## Open questions

### OQ-02: Why does this part run so late?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: It carries `cxxmyv`'s own dependencies (rule of the 2026-11-07 split), including `90iqr1`, which depends on `9o83cr` and so on every phase-B deletion part. Running after them means the deletion parts' test retargets (for example `k6jd6l` E-08 and E-09, which already move several of these modules onto `artifact_meta.read`) land first, so no assertion is converted twice. Recommendation strength: strong.

### OQ-01: Can this run before the cutover without breaking C10a?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. The helper reads through the ACTIVE format and, in the legacy format, also asserts the exact bullet line, so each converted test checks at least what it checked before on the same legacy bytes; `main` keeps one on-disk format. Only the format switch, the log branch of the helper and the exact-spelling rows wait for the cutover commit. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-03 validates E-03
  - Required evidence: paste the empty `diff .aw/state/iog3cw/S02-before.txt .aw/state/iog3cw/S02-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_backlog_gate_follows_status.py`, `tests/test_backlog_new_gate_vocabulary.py` (one line per module or test class), and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the empty `diff .aw/state/iog3cw/S03-before.txt .aw/state/iog3cw/S03-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_production.py` (one line per module or test class), and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the `diff` of the concatenated, sorted `-before.txt` lists of S02 and S03 against the combined after-run list (empty), F-28 for S01 to S04 as written with one row per remaining match and its class, the per-module F-28 `rg -c` count for each of the four S02 and S03 modules, the bare `python3 -m pytest` summary line and wall time beside them, the `aw sanitize --agent` result with zero `fail`, and every `aw commit iog3cw` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or the format-aware field assertion helper from `j5fqax` is absent, stop and report rather than proceeding. Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit iog3cw -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize iog3cw` itself.
