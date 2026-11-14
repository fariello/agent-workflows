# IPD: Move setter-byte assertions of batches S08 to S10 onto the format-aware field helper

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` C10a requires `main` to read and write exactly one metadata format at every commit, so the cutover commit (Order 13, `cxxmyv`) must switch the format and every test that asserts on it at once. `cxxmyv` E-07 carried, as one item, "convert the setter-byte assertions to `artifact_meta.read` plus the in-file mirror" (`59aiyh` Deferred row). Measured 2026-11-07 at `ac76110f4`: `rg -n "assert.*['\"]- (Status|Priority|Blocks-Release|Work-Kind|From-Backlog|From-Spec|Readiness|Approval|Set|Order|Kind|Id|Gate-Kind|Gate-Ref|Item-Dependencies|Graduated-To|Close-Evidence|Release-Exempt-(Kind|Ref)):" tests`, minus lines over command output and minus the legacy-grammar test modules, prints 518 candidate lines in 81 test modules; the 7 modules that `k6jd6l` E-08 already retargets hold 51 of them, leaving 467 in 74 modules. Converting them inside the attended cutover would hide several hundred steps in one item of a plan that cannot be retried cheaply. This work CAN move earlier without changing `main`'s on-disk format: the helper asserts through the ACTIVE format, which is the legacy format until the cutover, so every converted test still checks the same bytes today and needs no edit when the cutover flips the builder. Part of the split of `iog3cw` (Order 44); the helper is `j5fqax` E-01 (formerly `iog3cw` E-01).
- Scope: `cxxmyv` E-07 (setter-byte half), batches S09 and S10 moved verbatim from `iog3cw` (module and class lists unchanged; 6 module entries, 47 candidate lines at the split; batch S08, E-01, moved to `wdz2l9` on 2026-11-09, round-3 split); E-04 finishes. The helper is `j5fqax` E-01 (formerly `iog3cw` E-01). EXCLUDES: switching `RECORD_FORMAT` to `log` and the log-format branch of the helper (`cxxmyv` E-07, the cutover commit); displayed-output assertions; legacy-format subject tests; the `review-pilot` corpus; production code; every other batch.
- Scope-Paths: tests/test_plan_priority_required.py, tests/test_plans_archive.py, tests/test_plans_group_order_preservation.py, tests/test_plans_order_grammar.py, tests/test_plans_rename_selectors.py, tests/test_plan_transition_gate.py, .aw/records/plans/pending/20261108-metastore-60-rdg0qv-move-setter-byte-assertions-of-batches-s08-to-s10-onto-the-f.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:ya4ee4, executed:wdz2l9
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: standard
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 60
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: rdg0qv

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01 (S08) moved to wdz2l9.
- 2026-11-08 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from iog3cw (batches S08, S09, S10) per maintainer step-complexity rule (no single E/V item hides hundreds of steps; at most 4 batch items per plan).

## Goal

Every setter-byte assertion in batches S09 and S10 goes through the format-aware field helper of `j5fqax` E-01, with identical per-test outcomes before and after, so the cutover commit changes the helper and the builder and not these modules.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan:
1. Record the unmodified per-test outcome list of the batch's modules: ensure directory `.aw/state/rdg0qv/` exists (`mkdir -p .aw/state/rdg0qv/`), then run `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/rdg0qv/<batch>-before.txt`. For a batch restricted to named test classes, pass the `<module>::<Class>` node ids.
2. In each named module (or class), replace every SETTER-BYTE assertion with a call to the helper of `tests/record_builder.py` added by `j5fqax` E-01, formerly `iog3cw` E-01 (`assert_field(path, field, value)` and `assert_no_field(path, field)`). A setter-byte assertion is an `assertIn`/`assertNotIn`/`assert ... in` over the text of a RECORD FILE that names a front-matter bullet (`- Status:`, `- Priority:`, `- Blocks-Release:` and the other F-28 fields). An assertion over command OUTPUT (stdout, stderr, a rendered message) is a `displayed-output assertion` and is NOT converted; an assertion whose subject is the legacy grammar itself (a legacy-loader, migration or quoted-example test) is `legacy-format subject` and is NOT converted.
3. Re-run the same command into `<batch>-after.txt` and require `diff` to print nothing. A conversion that would change what a test checks (for example a test that asserts the exact bullet spelling, such as whitespace after the colon) stops and is reported with its node id; it is listed as `setter-byte, exact spelling` in F-28 for `cxxmyv`, not weakened.
4. Count the remaining matches of the F-28 pattern in the batch's modules and give each remaining line one class: `converted` (none should remain), `displayed-output assertion`, `legacy-format subject` or `setter-byte, exact spelling`.
5. The helper never reads production source, and no test gains a source-reading assertion.

### Task group 1: batches

- [ ] E-02 Batch S09: ensure directory `.aw/state/rdg0qv/` exists (`mkdir -p .aw/state/rdg0qv/`) and convert the setter-byte assertions of `tests/test_plan_priority_required.py`, `tests/test_plans_archive.py` (19 candidate assertion lines at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S09`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S09 outcome lists; the remaining F-28 matches in the batch's modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

- [ ] E-03 Batch S10: convert the setter-byte assertions of `tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py`, `tests/test_plans_rename_selectors.py`, `tests/test_plan_transition_gate.py` (28 candidate assertion lines at `ac76110f4`, F-28). Apply the batch rule with `<batch>` = `S10`.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the S10 outcome lists; the remaining F-28 matches in the batch's modules pasted with a class on each and no `setter-byte` row left unconverted except `setter-byte, exact spelling` rows with their node ids.
  - Execution state: pending

### Task group 2: finish

- [ ] E-04 Finish this part: run the batch rule's command over every module of S09 and S10 once more and confirm the outcome multiset equals the union of the batches' `-before.txt` lists; write F-28's remaining-match table for S08 to S10 (one row per remaining match with its class; the S08 rows copied from `wdz2l9` F-28 with the source named) so `cxxmyv` E-07 has the exact list of `setter-byte, exact spelling` rows it must still change; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit rdg0qv -- <each changed path>`, one commit per batch allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-02, E-03
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
| F-28 | Copied from `iog3cw` F-28 (measured at `ac76110f4`): 467 candidate setter-byte lines in 74 modules, split into 20 batches S01 to S20 of at most about 30 lines. This part: S08, S09, S10, 71 lines. | Each batch is at most about 30 one-line conversions in at most 10 modules. The final table (written by E-04) lists every remaining match with its class. |

## Proposed changes (ordered, validatable)

1. (Moved) S08: `wdz2l9`. Create baseline directory and convert batch S09 (E-02).
2. Convert batch S10 (E-03); batches S09 and S10 are independent.
3. Re-run union comparison over all modules, write table F-28, run bare core gate, and commit path-scoped (E-04).

```mermaid
flowchart TD
    A["E-02: mkdir -p .aw/state/rdg0qv/, capture S09-before.txt, convert batch S09 tests"] --> B["E-03: Capture S10-before.txt, convert batch S10 tests"]
    B --> C["E-04: Re-run union comparison against concatenated baselines, compile table F-28"]
    C --> D["E-04: Verify bare core gate python3 -m pytest, aw sanitize, and commit path-scoped"]
```

## Deferred / out of scope (with reason)

- Batch S08 (E-01). Moved to wdz2l9 (round-3 split 2026-11-09 per research nj8zdp guidance).
  - Carrier: wdz2l9
- Switching the builder to `RECORD_FORMAT = "log"`, adding the helper's log-format branch, and changing the `setter-byte, exact spelling` rows F-28 lists: they change the on-disk format and so belong to the cutover commit (C10a).
  - Carrier: cxxmyv
- The helper and batches S01 to S04.
  - Carrier: iog3cw
- The value-writer test modules retargeted by `k6jd6l` E-08.
  - Carrier: k6jd6l

## Scope check

- Over-scope: none. No production module changes.
- Under-scope: none known. Size: 3 E-items, 6 work Scope-Paths entries; every batch item is at most about 30 one-line conversions.

## Required tests / validation

Each batch is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, the same inputs, the same outcomes, with each assertion at least as strict as before. Commands: the batch rule's command per batch, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

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

- [ ] V-02 validates E-02
  - Required evidence: paste the empty `diff .aw/state/rdg0qv/S09-before.txt .aw/state/rdg0qv/S09-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_plan_priority_required.py`, `tests/test_plans_archive.py` (one line per module or test class), and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the empty `diff .aw/state/rdg0qv/S10-before.txt .aw/state/rdg0qv/S10-after.txt`, the before and after F-28 `rg -c` count for each of `tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py`, `tests/test_plans_rename_selectors.py`, `tests/test_plan_transition_gate.py` (one line per module or test class), and the class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `diff` of the concatenated, sorted `-before.txt` lists of S09 and S10 against the combined after-run list (empty), F-28 for this part as written with one row per remaining match and its class, the per-module F-28 `rg -c` count for each of `tests/test_plan_priority_required.py`, `tests/test_plans_archive.py`, `tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py`, `tests/test_plans_rename_selectors.py`, `tests/test_plan_transition_gate.py`, the bare `python3 -m pytest` summary line beside them and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit rdg0qv` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. OQ-01 and OQ-02 are resolved and not blocking. Pin-first.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code is not modified; only declared test files and this plan are edited.

Safety: if the format-aware field helper from `j5fqax` or prerequisite record builder from `59aiyh` is absent, stop and report immediately: that is an unsafe condition, not a scope question.

Honesty rule: run the named modules and `python3 -m pytest` (core gate), and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit rdg0qv -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize rdg0qv` itself.
