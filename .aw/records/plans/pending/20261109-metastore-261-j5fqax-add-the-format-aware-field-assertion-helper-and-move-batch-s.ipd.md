# IPD: Add the format-aware field assertion helper and move batch S04 onto it

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` C10a requires `main` to read and write exactly one metadata format at every commit, so the cutover commit (Order 13, `cxxmyv`) must switch the format and every test that asserts on it at once. `cxxmyv` E-07 carried, as one item, "convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror" (`59aiyh` Deferred row). Measured 2026-11-07 at `ac76110f4`: `rg -n "assert.*['\"]- (Status|Priority|Blocks-Release|Work-Kind|From-Backlog|From-Spec|Readiness|Approval|Set|Order|Kind|Id|Gate-Kind|Gate-Ref|Item-Dependencies|Graduated-To|Close-Evidence|Release-Exempt-(Kind|Ref)):" tests`, minus lines over command output and minus the legacy-grammar test modules, prints 518 candidate lines in 81 test modules; the 7 modules that `k6jd6l` E-08 already retargets hold 51 of them, leaving 467 in 74 modules. Converting them inside the attended cutover would hide several hundred steps in one item of a plan that cannot be retried cheaply. This work CAN move earlier without changing `main`'s on-disk format: the helper asserts through the ACTIVE format, which is the legacy format until the cutover, so every converted test still checks the same bytes today and needs no edit when the cutover flips the builder. Round-3 split of `iog3cw` (research `nj8zdp`): this part adds the helper (`iog3cw` E-01) and converts batch S04 (`iog3cw` E-05); every later batch plan depends on it.
- Scope: `iog3cw` E-01 (the helper and its test module) and E-05 (batch S04: `tests/test_backlog.py`, 30 candidate lines at `ac76110f4`). EXCLUDES the `iog3cw` exclusions: switching `RECORD_FORMAT` to `log`, the log branch of the helper, displayed-output assertions, legacy-format subject tests, the `review-pilot` corpus, production code.
- Scope-Paths: tests/record_builder.py, tests/test_record_builder_assert_field.py, tests/test_backlog.py, .aw/records/plans/pending/20261109-metastore-261-j5fqax-add-the-format-aware-field-assertion-helper-and-move-batch-s.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:ya4ee4
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 261
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: j5fqax

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from iog3cw (round 3, research nj8zdp guidance).

## Goal

Add the format-aware field helper and move `tests/test_backlog.py` onto it with identical per-test outcomes, so later batches have the helper and the cutover commit changes the helper and the builder and not this module.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan:
1. Record the unmodified per-test outcome list of the batch's modules: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/j5fqax/<batch>-before.txt`. For a batch restricted to named test classes, pass the `<module>::<Class>` node ids.
2. In each named module (or class), replace every SETTER-BYTE assertion with a call to the helper of `tests/record_builder.py` added by `j5fqax` E-01, formerly `iog3cw` E-01 (`assert_field(path, field, value)` and `assert_no_field(path, field)`). A setter-byte assertion is an `assertIn`/`assertNotIn`/`assert ... in` over the text of a RECORD FILE that names a front-matter bullet (`- Status:`, `- Priority:`, `- Blocks-Release:` and the other F-28 fields). An assertion over command OUTPUT (stdout, stderr, a rendered message) is a `displayed-output assertion` and is NOT converted; an assertion whose subject is the legacy grammar itself (a legacy-loader, migration or quoted-example test) is `legacy-format subject` and is NOT converted.
3. Re-run the same command into `<batch>-after.txt` and require `diff` to print nothing. A conversion that would change what a test checks (for example a test that asserts the exact bullet spelling, such as whitespace after the colon) stops and is reported with its node id; it is listed as `setter-byte, exact spelling` in F-28 for `cxxmyv`, not weakened.
4. Count the remaining matches of the F-28 pattern in the batch's modules and give each remaining line one class: `converted` (none should remain), `displayed-output assertion`, `legacy-format subject` or `setter-byte, exact spelling`.
5. The helper never reads production source, and no test gains a source-reading assertion.

### Task group 1: work

- [ ] E-01 (was `iog3cw` E-01, verbatim.) Add to `tests/record_builder.py` (the shared builder of `9rgn2w`/`59aiyh`) two helpers that assert a record's field through the active record format, so a test written against them passes unchanged when the cutover switches the builder to `RECORD_FORMAT = "log"`: `assert_field(path, field, value)` passes when the record at `path` has `field` equal to `value`, and `assert_no_field(path, field)` passes when the field is absent or unset. In the legacy format (`RECORD_FORMAT = "legacy"`, today's only format) each helper reads the value through `artifact_meta.read_text(path.read_text(), record_type=...)` and ALSO asserts the exact bullet line is present (or absent) in the file, so it is never weaker than the `assertIn("- Status: x", text)` it replaces; in the log format it reads `artifact_meta.read` and the in-file mirror (the cutover, `cxxmyv` E-07, adds that branch). Field names use the registry names (`status`, `priority`, `blocks_release`, ...) and the helper maps them to bullet labels with `artifact_meta`'s own label table (no second table). Add `tests/test_record_builder_assert_field.py` (core): for each record type, a builder-made record with and without a field, asserting pass and fail (a failing helper raises `AssertionError` naming the field, the expected and the observed value), including a record whose bullet uses a loose spelling (`-  Status:`), which must fail the exact-line half so the helper is not weaker than the old assertion.
  - Depends on: none
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_record_builder_assert_field.py` passes; the helpers read no production source.
  - Execution state: pending

- [ ] E-02 (was `iog3cw` E-05.) Batch S04: convert the setter-byte assertions of `tests/test_backlog.py` (30 candidate assertion lines at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S04`.
  - Depends on: E-01
  - Expected outcome: an empty before/after `diff` for the S04 outcome lists; the remaining F-28 matches in the batch's module pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

- [ ] E-03 Finish this part: run the batch rule's command over `tests/test_backlog.py` once more and confirm the outcome multiset equals the union of this part's `-before.txt` lists (S04); write this plan's F-28 rows (one row per remaining match in those modules with its class) so `iog3cw` E-12 can assemble the part table; record per module the PASSED, FAILED, SKIPPED and XFAIL counts of the after run in F-29; run `aw sanitize --agent`; commit through `aw commit j5fqax -- <each changed path>`, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
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
| F-28 | `iog3cw` F-28 (measurement at `ac76110f4`) | This part: S04, 30 lines in `tests/test_backlog.py`. Rows for remaining matches are written by E-03. |
| F-29 | (written by E-03) | Per-module after-run outcome counts; `iog3cw` E-12 compares against them. |

## Proposed changes (ordered, validatable)

1. E-01: the helper and its test.
2. E-02: batch S04.
3. E-03: union check, F-28 rows, commit.

## Deferred / out of scope (with reason)

- Batch S01.
  - Carrier: 545ag7
- Batches S02, S03 and the assembly of the part F-28 table.
  - Carrier: iog3cw
- Switching the builder to `RECORD_FORMAT = "log"`, the helper's log-format branch, and the `setter-byte, exact spelling` rows: cutover commit (C10a).
  - Carrier: x1mmdp

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none. `iog3cw` E-01 maps to E-01; `iog3cw` E-05 maps to E-02; this part's share of `iog3cw` E-12 maps to E-03.

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
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_record_builder_assert_field.py` with every case PASSED (pass and fail per record type, the loose-spelling failure, the `AssertionError` message), and `rg -n "inspect\.|import ast|getsource" tests/record_builder.py tests/test_record_builder_assert_field.py` empty.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the empty `diff .aw/state/j5fqax/S04-before.txt .aw/state/j5fqax/S04-after.txt`, the before and after F-28 `rg -c` count for `tests/test_backlog.py`, and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the empty union `diff` for S04, this plan's F-28 rows, the F-29 per-module counts for `tests/test_backlog.py`, the `aw sanitize --agent` result with zero `fail`, and every `aw commit j5fqax` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL output; never claim a result you did not run. Commits: only through `aw commit j5fqax -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
