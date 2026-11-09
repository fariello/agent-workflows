# IPD: Move setter-byte assertions of batch S01 onto the format-aware helper

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C10a requires `main` to read and write exactly one metadata format at every commit, so the cutover commit (Order 13, `cxxmyv`) must switch the format and every test that asserts on it at once. `cxxmyv` E-07 carried, as one item, "convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror" (`59aiyh` Deferred row). Measured 2026-11-07 at `ac76110f4`: `rg -n "assert.*['\"]- (Status|Priority|Blocks-Release|Work-Kind|From-Backlog|From-Spec|Readiness|Approval|Set|Order|Kind|Id|Gate-Kind|Gate-Ref|Item-Dependencies|Graduated-To|Close-Evidence|Release-Exempt-(Kind|Ref)):" tests`, minus lines over command output and minus the legacy-grammar test modules, prints 518 candidate lines in 81 test modules; the 7 modules that `k6jd6l` E-08 already retargets hold 51 of them, leaving 467 in 74 modules. Converting them inside the attended cutover would hide several hundred steps in one item of a plan that cannot be retried cheaply. This work CAN move earlier without changing `main`'s on-disk format: the helper asserts through the ACTIVE format, which is the legacy format until the cutover, so every converted test still checks the same bytes today and needs no edit when the cutover flips the builder. Round-3 split of `iog3cw` (research `nj8zdp`): this part converts batch S01 (`iog3cw` E-02), split in two items of four modules each; the helper is `j5fqax` E-01.
- Scope: `iog3cw` E-02 (batch S01: 8 modules, 28 candidate lines at `ac76110f4`), as S01a and S01b. EXCLUDES the `iog3cw` exclusions: switching `RECORD_FORMAT` to `log`, the log branch of the helper, displayed-output assertions, legacy-format subject tests, the `review-pilot` corpus, production code.
- Scope-Paths: tests/test_agy_runipd_cli.py, tests/test_artifact_group.py, tests/test_artifact_rename.py, tests/test_attention_priority_blocker.py, tests/test_attention.py, tests/test_awcmdsurf_mutation_verbs.py, tests/test_backlog_already_complete.py, tests/test_backlog_close_evidence_plan_disposition.py, .aw/records/plans/pending/20261109-metastore-262-545ag7-move-setter-byte-assertions-of-batch-s01-onto-the-format-awa.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:ya4ee4, executed:j5fqax
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 262
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 545ag7

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from iog3cw (round 3, research nj8zdp guidance).

## Goal

Every setter-byte assertion in the eight S01 modules goes through the format-aware field helper, with identical per-test outcomes before and after.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan:
1. Record the unmodified per-test outcome list of the batch's modules: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/545ag7/<batch>-before.txt`. For a batch restricted to named test classes, pass the `<module>::<Class>` node ids.
2. In each named module (or class), replace every SETTER-BYTE assertion with a call to the helper of `tests/record_builder.py` added by `j5fqax` E-01, formerly `iog3cw` E-01 (`assert_field(path, field, value)` and `assert_no_field(path, field)`). A setter-byte assertion is an `assertIn`/`assertNotIn`/`assert ... in` over the text of a RECORD FILE that names a front-matter bullet (`- Status:`, `- Priority:`, `- Blocks-Release:` and the other F-28 fields). An assertion over command OUTPUT (stdout, stderr, a rendered message) is a `displayed-output assertion` and is NOT converted; an assertion whose subject is the legacy grammar itself (a legacy-loader, migration or quoted-example test) is `legacy-format subject` and is NOT converted.
3. Re-run the same command into `<batch>-after.txt` and require `diff` to print nothing. A conversion that would change what a test checks (for example a test that asserts the exact bullet spelling, such as whitespace after the colon) stops and is reported with its node id; it is listed as `setter-byte, exact spelling` in F-28 for `cxxmyv`, not weakened.
4. Count the remaining matches of the F-28 pattern in the batch's modules and give each remaining line one class: `converted` (none should remain), `displayed-output assertion`, `legacy-format subject` or `setter-byte, exact spelling`.
5. The helper never reads production source, and no test gains a source-reading assertion.

### Task group 1: work

- [ ] E-01 (first half of `iog3cw` E-02.) Batch S01a: convert the setter-byte assertions of `tests/test_agy_runipd_cli.py`, `tests/test_artifact_group.py`, `tests/test_artifact_rename.py`, `tests/test_attention_priority_blocker.py` (part of the 28 candidate assertion lines of S01 at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S01a`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S01a outcome lists; the remaining F-28 matches in the four modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

- [ ] E-02 (second half of `iog3cw` E-02.) Batch S01b: convert the setter-byte assertions of `tests/test_attention.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_backlog_already_complete.py`, `tests/test_backlog_close_evidence_plan_disposition.py` (the rest of S01's 28 candidate lines, F-28). Apply the batch rule with `<batch>` = `S01b`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S01b outcome lists; the remaining F-28 matches in the four modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

- [ ] E-03 Finish this part: run the batch rule's command over the eight S01 modules once more and confirm the outcome multiset equals the union of `S01a-before.txt` and `S01b-before.txt`; write this plan's F-28 rows (one row per remaining match with its class) and F-29 (per-module PASSED, FAILED, SKIPPED and XFAIL counts of the after run) so `iog3cw` E-12 can assemble the part table; run `aw sanitize --agent`; commit through `aw commit 545ag7 -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-01, E-02
  - Expected outcome: the union comparison is empty; F-28 and F-29 for this part are written; every commit is path-scoped to Scope-Paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Test data comes from ONE builder, `tests/record_builder.py` (`9rgn2w`/`59aiyh`), which writes through `artifact_meta`; `cxxmyv` E-07 switches it to `RECORD_FORMAT = "log"` in the cutover commit.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, so a complete comparison passes `-m ""`, and `pytest-randomly` is installed, so a deterministic order needs `-p no:randomly`.
- `artifact_meta.read_text(text, *, record_type=None) -> State` parses a record's text in either format (phase-B legacy loader), so the helper's legacy branch needs no new parser.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-28 | `iog3cw` F-28 (measurement at `ac76110f4`) | This part: S01, 28 lines in 8 modules, as S01a (first four) and S01b (last four). Rows for remaining matches are written by E-03. |
| F-29 | (written by E-03) | Per-module after-run outcome counts. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: the two halves of S01 (independent).
2. E-03: union check, F-28 rows, commit.

## Deferred / out of scope (with reason)

- The helper and batch S04.
  - Carrier: j5fqax
- Batches S02, S03 and the assembly of the part F-28 table.
  - Carrier: iog3cw
- Switching the builder to `RECORD_FORMAT = "log"`, the helper's log-format branch, and the `setter-byte, exact spelling` rows: cutover commit (C10a).
  - Carrier: x1mmdp

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none. `iog3cw` E-02's module list equals the union of E-01's and E-02's lists here; this part's share of `iog3cw` E-12 maps to E-03.

## Required tests / validation

Each batch is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction. Commands: the batch rule's command per batch, the per-module F-28 `rg -c` counts, the bare core gate `python3 -m pytest` beside them, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; prepares part of `4sd62s` section 6 and section 7 step 9 (the test-data half of the cutover) without changing the on-disk format.

## Open questions

### OQ-01: Can this run before the cutover without breaking C10a?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. The helper reads through the ACTIVE format and, in the legacy format, also asserts the exact bullet line, so each converted test checks at least what it checked before on the same legacy bytes; `main` keeps one on-disk format. Only the format switch, the log branch of the helper and the exact-spelling rows wait for the cutover commit. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the empty `diff .aw/state/545ag7/S01a-before.txt .aw/state/545ag7/S01a-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_agy_runipd_cli.py`, `tests/test_artifact_group.py`, `tests/test_artifact_rename.py`, `tests/test_attention_priority_blocker.py`, and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the empty `diff .aw/state/545ag7/S01b-before.txt .aw/state/545ag7/S01b-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_attention.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_backlog_already_complete.py`, `tests/test_backlog_close_evidence_plan_disposition.py`, and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the empty union `diff`, this plan's F-28 rows, the F-29 table with one row per S01 module, the `aw sanitize --agent` result with zero `fail`, and every `aw commit 545ag7` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit 545ag7 -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
