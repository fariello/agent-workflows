# IPD: Give row-level test evidence a sound repeatable driver, and fix the accumulate-style tables whose per-row verdicts are currently false

- Date: 2026-09-29
- Kind: child
- Concern: The obvious way to obtain the per-row test verdicts that tabulated-suite evidence needs reports PASS for a FAILING row in four of this repository's table tests, so row-level evidence is not merely unsupported by tooling, it is currently forgeable by accident.
- Scope: Make per-row verdicts truthful in the four affected `subTest` blocks, and ship one sound reusable driver so row-level evidence is a repeatable paste rather than a per-plan ad-hoc script.
- Scope-Paths: tests/test_executed_transition_gate_e2e.py, tests/test_subtest_row_verdicts.py, agent_workflows/subtest_rows.py, docs/row-level-test-evidence.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: nos070
- Set: nos070
- Order: 2
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: t5txjk

## Workflow history

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored in full from backlog `nos070`; ready for `/plan-review`.

## Goal

Make the row-level verdict that backlog `nos070`'s substitution rule asks an executor to paste actually obtainable and actually true. Repair the four `subTest` blocks whose row verdicts are false today, and ship one small driver plus a short doc so the next executor pastes a repeatable command instead of re-inventing a throwaway script whose output may be wrong.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop the four blocks reporting false per-row verdicts

- [ ] E-01 In `tests/test_executed_transition_gate_e2e.py`, make each of the four accumulate-style `subTest` blocks FAIL INSIDE the subtest context when its row is wrong, in addition to (not instead of) appending to the existing `wrong` list. The four enclosing tests are `PreCommitExecutedGateTests.test_each_staged_situation_gets_its_own_verdict_and_reason` (over `SITUATIONS`), `MergeAwareInTreeEvidenceTests.test_the_merge_detector_reports_the_incoming_side_in_every_state` (over `DETECTOR_STATES`, which accumulates a single `problem` rather than a `problems` list), `MergeAwareInTreeEvidenceTests.test_merge_state_never_becomes_a_blanket_exemption` (over `MERGE_DECISIONS`) and `MergeAwareInTreeEvidenceTests.test_git_itself_enforces_the_gate_at_both_merge_stages` (over `INSTALLED_HOOK_RUNS`). PRESERVE BOTH EXISTING PROPERTIES, which is the whole difficulty of this item: every row must still RUN even after an earlier row fails (a bare `assert` inside the loop but outside the subtest context would abort the sweep), and the end-of-test aggregate assertion with its long diagnostic prose must still fire and still list every failing row. `subTest` gives both: a failure raised inside the context is recorded against that row and execution continues to the next row, and the trailing `self.assertEqual(wrong, [], ...)` still runs. Do NOT delete, shorten or reword the existing aggregate assertion messages; they carry the maintainer's diagnostic reasoning (the `MERGE_DECISIONS` message alone explains what each failing row group implies) and they are the channel a normal `pytest` run reports through.
  - Depends on: none
  - Expected outcome: a corrupted row makes an `addSubTest`-observing runner print FAIL for that row and PASS for the others, while a bare `python3 -m pytest` on the file still fails with the same aggregate message naming the same rows, and the row count still executed is unchanged.
  - Execution state: pending

- [ ] E-02 Add `tests/test_subtest_row_verdicts.py` proving the PROPERTY E-01 establishes, generically rather than by pinning the four call sites: build a throwaway `TestCase` in-process whose table has one passing and one failing row in each of the two idioms (fail-inside-context and append-only), run it under a result class that records `addSubTest` outcomes, and assert that the fail-inside-context idiom reports the failing row as FAILED while the append-only idiom does NOT. That second assertion is the one that documents the hazard: it pins the WRONG idiom's observable behaviour so a future reader can see why the convention exists. Then assert the same property holds for the real repaired tests by running one of them with a deliberately corrupted table row injected on the class and checking the recorded per-row outcomes. This test exercises code by running it and asserts on observable outcomes; it reads no production source text, so it is clear of GUIDING_PRINCIPLES P16.
  - Depends on: E-01
  - Expected outcome: a test that goes red if anyone reverts a repaired block to append-only reporting, and which fails for the right reason (a row's recorded verdict, not a string in a file).
  - Execution state: pending

### Task group 2: make the paste repeatable

- [ ] E-03 Add `agent_workflows/subtest_rows.py` exposing a small, importable helper that runs one or more named test methods and returns plus prints the per-row verdicts (the row's `subTest` parameters and PASS/FAIL), built on a `unittest.TextTestResult` subclass overriding `addSubTest`. Model it on the harness executed plan `0i4fkt` pasted as evidence, which is the shape already proven in this repository. TWO HONESTY REQUIREMENTS ARE PART OF THE DELIVERABLE, not decoration. FIRST, the output must report the ENCLOSING test's own pass/fail beside the row verdicts, because a test can fail outside any subtest (in `setUp`, or at a trailing aggregate assertion) and a row listing alone would then read as an all-clear. SECOND, when the enclosing test FAILED but no row was recorded as failing, the helper must say so explicitly rather than printing a clean row list, since that combination is the exact signature of the append-only hazard and of a failure raised outside the loop. Expose it as a module callable from a one-line `python3 -c` invocation an executor can paste into a V-item; do NOT add a CLI verb (see Deferred).
  - Depends on: E-01
  - Expected outcome: one documented import that prints per-row verdicts plus the enclosing verdict, usable in a single pasteable command, and which cannot silently present a failing test as a set of passing rows.
  - Execution state: pending

- [ ] E-04 Add `docs/row-level-test-evidence.md`: a short page stating what row-level evidence is for (satisfying a V-item whose named test has become a table row), the exact pasteable command using E-03's helper, the two-idiom hazard in one paragraph with the reason a passing `subTest` is silent under this repository's runner configuration, and the rule that a row verdict is only trustworthy when the row's failure is raised inside the subtest context. Link it from the convention amended by sibling plan `vtup6x` so the substitution rule has somewhere to point for the mechanism. The page is written for an executing agent, not an end user.
  - Depends on: E-03
  - Expected outcome: an executor needing a row verdict finds one command and one caveat, without reading this plan or reverse-engineering a past plan's evidence block.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE HOUSE TABLE IDIOM IS `(case, <inputs...>, expected, needles, forbidden, why)` with the case string FIRST and a trailing `why` quoted back in the failure message as `this row exists because: <why>`. The `why` column is the convention's real payload: it makes a failing row self-explaining. Nothing in this plan changes the row shape or the `why` convention.
- TESTS MUST ASSERT OUTCOMES, NOT CODE STRUCTURE (GUIDING_PRINCIPLES P16, and the execution contract's `TEST OUTCOMES, NOT CODE STRUCTURE` paragraph). E-02 is therefore written to RUN tests and read recorded verdicts, never to grep `tests/*.py` for an idiom. A census by grep was used at AUTHORING time to bound the work (F-02) and must not become the test.
- A SOUND PER-ROW HARNESS ALREADY EXISTS AS PRECEDENT, in executed plan `0i4fkt`'s V-02 evidence (an `addSubTest`-overriding `TextTestResult` printing `subtest (tree='specs'): PASSED`). Its target asserts INSIDE the subtest context, which is why its verdicts are truthful. E-03 generalizes that precedent rather than inventing a mechanism.
- THE REPOSITORY RUNS THE SUITE BARE. `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; a second `-q` compounds to `-qq` and suppresses the summary line the execution contract requires to be pasted, and `-o addopts=""` is the sanctioned way to clear the defaults for a narrowed run.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE NAIVE ROW-VERDICT DRIVER LIES, and this is the finding that justifies the plan. Measured 2026-09-29 against the real `MERGE_DECISIONS` table: one row's expected exit code was corrupted on the class to an impossible `99`, the test then FAILED (`FAILED (failures=1)` with the aggregate message reporting `check` `decided 1 of 7 merge situations wrongly` and naming the corrupted case), yet an `addSubTest`-observing runner printed `PASS` for ALL SEVEN ROWS, the corrupted one included. So an executor following backlog `nos070`'s substitution rule with the obvious driver would paste seven green rows as evidence for a red test. | measured at authoring against `tests/test_executed_transition_gate_e2e.py` `MergeAwareInTreeEvidenceTests.test_merge_state_never_becomes_a_blanket_exemption` |
| F-02 | THE CAUSE IS THE ASSERT'S LOCATION, AND THE AFFECTED POPULATION IS EXACTLY FOUR BLOCKS IN ONE FILE. These tests append to a `wrong` list INSIDE `with self.subTest(case=case):` and assert ONCE after the loop, so no exception is ever raised inside the subtest context and `addSubTest` records every row as a success. A census over `tests/*.py` for a `subTest` block that appends a failure but contains no `assert`/`fail`/`raise` returns FOUR blocks, all in `tests/test_executed_transition_gate_e2e.py`: the tests over `SITUATIONS`, `DETECTOR_STATES`, `MERGE_DECISIONS` and `INSTALLED_HOOK_RUNS`. The other 242 `subTest` blocks across 46 files assert in context and report truthfully. | measured at authoring over `tests/*.py`; the four enclosing methods named in E-01 |
| F-03 | IT IS THE SAME FILE i4c0c3 DREW ITS EVIDENCE FROM, so this is not a hypothetical hazard. i4c0c3's V-03 pasted `[PASS]` lines for `MERGE_DECISIONS` rows; that evidence happened to be correct because the rows genuinely passed, but the mechanism used could not have revealed a failing row. The substitution rule sibling plan `vtup6x` writes down would institutionalize that mechanism unless this plan lands. | `.aw/records/plans/executed/20260908-gatejrnl-01-i4c0c3-stop-the-executed-transition-gate-firing-on-a-follow-up-edit.ipd.md` V-03 observed evidence; F-01's measurement on the same table |
| F-04 | THE FIX IS SMALL AND PRESERVES BOTH PROPERTIES, verified by construction before authoring. Failing inside the subtest context while also appending to `wrong` yields truthful per-row verdicts (`row-a -> PASS`, `row-b -> FAIL`, `row-c -> FAIL`), still runs every row after the first failure, and still reaches the trailing aggregate assertion which still lists every failing row. The run reports one failure per failing row plus one for the aggregate. | measured at authoring on a two-idiom probe reproducing the house shape |
| F-05 | `pytest-subtests` IS NOT INSTALLED AND ADDING IT WOULD NOT SOLVE THIS. Declared test extras are `pytest>=8`, `pytest-xdist>=3`, `pytest-randomly>=3`, `PyYAML>=6`. Without that plugin pytest does not surface even FAILING subtests as separate ids; with it, a row that never raises inside the context would still not be surfaced, because there is nothing to surface. The defect is in the four tests, not in the runner configuration, so this plan adds no dependency. | `pyproject.toml` `test` and `dev` extras; F-01's measurement, in which the corrupted row raised nothing inside the context |
| F-06 | ROW COUNTS ARE STABLE AND READABLE OFF THE DATA, so the repaired tests need no count assertions and this plan writes none. `SITUATIONS` has 15 rows, `DETECTOR_STATES` 4, `MERGE_DECISIONS` 7, `INSTALLED_HOOK_RUNS` 4, `REGISTRATIONS` 3, totalling 33, matching the census i4c0c3's V-04 recorded, even though the file was renamed and re-collected since. The durable fact is the row's presence and verdict; the collected test count is not, which is the point sibling `vtup6x` makes. | `tests/test_executed_transition_gate_e2e.py` table constants; i4c0c3 V-04's row census |
| F-07 | THE FILE HAS MOVED ONCE ALREADY, so the executor must locate the tables by symbol rather than by the path older records name. The tables now live in `tests/test_executed_transition_gate_e2e.py`; `tests/test_executed_transition_gate.py` still exists and contains NEITHER table. The move was a trim-then-restore pair (`19313eed`, then `cd79ff6e`). | `tests/test_executed_transition_gate_e2e.py`; `tests/test_executed_transition_gate.py`; commits `19313eed`, `cd79ff6e` |

## Proposed changes (ordered, validatable)

1. Make the four accumulate-style `subTest` blocks fail inside the subtest context while keeping the per-row sweep and the aggregate diagnostic intact (E-01).
2. Add a behavioural test pinning truthful per-row reporting for the fixed idiom and the silence of the broken one (E-02).
3. Add a small importable per-row verdict helper that also reports the enclosing test's verdict and flags the failed-but-no-failing-row combination (E-03).
4. Document the one pasteable command and the single caveat (E-04).

## Deferred / out of scope (with reason)

- A `aw` CLI VERB FOR ROW VERDICTS. Deferred on the DEMAND axis. The backlog item rates tooling `Worth considering, not obviously worth building yet`, and an importable helper plus a documented one-line invocation delivers the repeatable paste with no new public CLI surface to keep compatible, no help text, no completion entry and no `--agent` contract. If row-level evidence becomes routine, promoting the helper to a verb is a small follow-up; adding it now would be the larger, less reversible choice.
  - Carrier-Declined: No obligation is left outstanding, because the CAPABILITY ships in this plan and only its packaging is declined. E-03 delivers the repeatable paste as an importable helper with a documented one-line invocation, so nothing a user needs is missing afterwards. A carrier would assert an unmet need that the deliverable itself meets, and promoting a helper to a verb is a new public-surface decision to be taken on evidence of routine use, not a debt.
- SWEEPING EVERY TABLE TEST IN THE SUITE. Out of scope by measurement, not by preference: F-02's census puts the affected population at four blocks in one file, and the other 242 `subTest` blocks already report truthfully. A suite-wide sweep would be 46 files of churn for no behaviour change.
  - Carrier-Declined: No obligation is left outstanding. The census is exhaustive over `tests/*.py` and found four affected blocks, all repaired by E-01, so after this plan the defective population is empty. Filing a carrier would assert remaining work that the measurement says does not exist.
- ADDING `pytest-subtests`. Out of scope per F-05: it would not surface a row that never raises, and the defect is in the four tests.
  - Carrier-Declined: No obligation is left outstanding. This is a rejected remedy rather than postponed work: the plugin cannot surface a row that raises nothing, so adding it would not fix the defect E-01 fixes. Nothing remains for a carrier to own.
- RESTATING THE ROW SHAPE OR THE `why` COLUMN CONVENTION. Out of scope; no table's data is edited by this plan, only the reporting of a wrong row.
  - Carrier: 7fzqop
- THE AUTHORING AND SUBSTITUTION CONVENTIONS THEMSELVES. Owned by sibling plan `vtup6x` (`nos070-01`). This plan supplies the mechanism that plan's rule needs; it states no rule about how a V-item must be worded.
  - Carrier: vtup6x

## Scope check

- Over-scope: none. One existing test file, two new files, one new doc, all declared.
- Under-scope: E-01 repairs the four blocks F-02 measured and adds no guard that would catch a NEW append-only block written later in some other file. E-02 pins the property generically but cannot enforce it at an unwritten call site, and the only mechanism that could is a source-text census, which GUIDING_PRINCIPLES P16 prohibits and which the execution contract names explicitly (`NEVER write or restore tests that read production source code using inspect, ast, regex, or substring search`). E-04 documents the rule for a human and an agent instead. Flagged so the reviewer can judge whether documentation is a sufficient guard here; the author's position is that it is, because the prohibition is categorical and the population is one file.

## Required tests / validation

- `python3 -m pytest tests/test_subtest_row_verdicts.py tests/test_executed_transition_gate_e2e.py -o addopts=""` for the repaired and new surfaces.
- The CORRUPTED-ROW comparison, run twice: once before E-01 and once after, on the same table, showing the per-row verdicts change from all-PASS to one-FAIL while the aggregate assertion's verdict does not change. This is the plan's central claim and must be measured, not argued.
- A bare `python3 -m pytest`, compared against a bare run taken IMMEDIATELY BEFORE the first edit in this same lane. Do NOT compare against any number written in this plan.
- The corruption must be applied and then REMOVED, proven by an empty diff, and it must be applied on the CLASS ATTRIBUTE in the driver process rather than by editing the tracked test file, so no corrupted table can be committed by accident.

## Spec / documentation sync

- No spec is amended by this plan, and none is listed in `- Scope-Paths:`. The evidence CONTRACT lives in `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 5.4 and is amended by sibling plan `vtup6x`; this plan changes only test-harness behaviour and adds tooling, which no spec governs.
- `docs/row-level-test-evidence.md` is new documentation added by E-04. Sibling `vtup6x` amends the workflow bodies that will point at it; if `vtup6x` has not executed when this plan runs, E-04 still lands the page and the pointer is added by that plan, so neither plan blocks the other.

## Open questions

### OQ-01: Is a test-harness that reports a failing row as PASS a `bug` (and therefore a release blocker), or a `followup`?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: No obligation outlives this plan, because the question is about how the work already being done here should be CLASSIFIED, not about work left undone. The defect itself is fixed by E-01 and verified by V-01 under either answer, so nothing needs a later owner. Recorded so review puts the classification question to the maintainer rather than letting it pass unasked; if the maintainer answers `bug`, the consequence is a `- Blocks-Release:` gate set on the artifact at that moment, which is a field change and not a work handoff.
- Resolution or deferral rationale: NOT resolvable from repository evidence, and deliberately left to the maintainer because it is a release-gating and risk-appetite call, which the repository's instructions reserve to the human. The case for `followup`, which is what this plan inherits from backlog `nos070` and therefore carries: no user waits on it, no shipped behaviour is wrong, the four tests correctly FAIL on a wrong row through their aggregate assertion, and the false verdicts appear only in an ad-hoc driver an agent runs by hand. The case for `bug`: the artifact it corrupts is EVIDENCE, and the repository's gating rule would then oblige a `- Blocks-Release:` gate while the item is live. The author did NOT set `- Work-Kind: bug` or invent a gate, because writing a release gate the maintainer has not agreed to is not the author's call; it is recorded here so review can put the question rather than let it pass unasked. Non-blocking: every item in this plan is executable and verifiable under either classification.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the BEFORE and AFTER halves of the corrupted-row comparison for at least two of the four repaired tables, including the one over `MERGE_DECISIONS`. BEFORE (from the pre-change tree) must show the per-row listing reporting every row PASS while the enclosing test FAILS. AFTER must show the corrupted row reporting FAIL, every other row still reporting a verdict (proving the sweep was not aborted), and the enclosing aggregate assertion still failing with its original diagnostic prose naming the same row. Also paste `git diff -- tests/test_executed_transition_gate_e2e.py` and confirm by reading it that no row DATA, no `why` string and no aggregate assertion message was altered, and that no test was deleted or weakened; if the diff removes any line other than the reporting change, report it rather than explaining it. Finally paste the row census read off the tables after the change and confirm it is unchanged at 33.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new module's passing run with its summary line. Then prove it is SENSITIVE, by reverting ONE of the four repaired blocks to append-only reporting in the worktree, pasting the new test FAILING with a message identifying that block's row verdict as the reason, then restoring and pasting an empty `git diff --stat tests/test_executed_transition_gate_e2e.py` against the pre-mutation state. The mutation must be applied to the test file and reverted, not simulated. State explicitly that the new module asserts on RECORDED VERDICTS obtained by running tests, and reads no `tests/*.py` or `agent_workflows/*.py` source text, since a census-by-grep implementation would violate the repository's test contract and must be reported as a defect if found in the delivered code.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the single one-line invocation and its output for one repaired test, showing per-row verdicts AND the enclosing test's own verdict. Then evidence BOTH honesty requirements by measurement. (a) Make the enclosing test fail OUTSIDE any row (for example by corrupting the trailing aggregate assertion's expectation, or by failing in `setUp`) and paste the helper's output showing it reports the enclosing failure rather than presenting a clean row list. (b) Paste the output for the failed-but-no-failing-row combination and show the helper states that combination explicitly. Revert every corruption and paste an empty diff for each touched file. A helper that prints only row lines does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new page. Then verify it by USE rather than by reading: hand the page's pasteable command to a fresh shell, run it verbatim against one repaired test, and paste the result, proving the documented command works as written and needs no undocumented step. Confirm the page states the assert-location caveat and the reason a passing `subTest` is silent here. Paste `aw sanitize --agent` over the new page (or its containing tree) with its exit status, since it is a public tracked artifact that will contain example command output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It must not be executed until `/plan-review` has run and a human has approved it (`aw ipd set approved <id6> --by-human`). The executor must not self-approve, and must not write the `- Readiness:` field, which is an output of review and not of authoring or execution.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. A reporting fix in four `subTest` blocks of one test file, a behavioural test pinning the fixed property, one small helper module, and one short doc page. The reason it is worth doing is a measured defect rather than a tidiness argument: corrupting one row of the real `MERGE_DECISIONS` table makes the test fail, while the obvious per-row driver prints PASS for all seven rows including the corrupted one. Sibling plan `vtup6x` is about to tell executors to paste exactly those per-row verdicts as evidence, so without this plan the convention would institutionalize a mechanism that cannot reveal a failing row. No production behaviour changes, no table data changes, no dependency is added, and no CLI verb is added.

ONE OPEN QUESTION IS FOR THE MAINTAINER, AND IT IS NON-BLOCKING. OQ-01 asks whether a harness that reports a failing row as PASS should be classified `bug`, which under this repository's rules would oblige a `- Blocks-Release:` gate, rather than the `followup` inherited from backlog `nos070`. The author deliberately did NOT set a gate, because inventing one is the maintainer's decision, not the author's. Every item here is executable and verifiable under either answer.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Four paths, all in `- Scope-Paths:`: `tests/test_executed_transition_gate_e2e.py`, the new `tests/test_subtest_row_verdicts.py`, the new `agent_workflows/subtest_rows.py`, and the new `docs/row-level-test-evidence.md`. FIVE NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do NOT change any table ROW, any `why` string, or any aggregate assertion MESSAGE: those messages are the maintainer's diagnostic reasoning and are the channel a normal `pytest` run reports through; this plan changes only WHERE the failure is raised. SECOND, do NOT delete, skip, weaken or `xfail` any existing test; if one goes red, that is a finding to report, not a test to adjust. THIRD, do NOT commit a corrupted table: every corruption in V-01 through V-03 is temporary and each must be proven reverted with an empty diff, and the row corruption must be injected on the CLASS ATTRIBUTE in the driver process rather than by editing the tracked file. FOURTH, do NOT implement E-02 as a grep or AST census over `tests/*.py`: the repository's test contract prohibits reading production or test source text as a correctness proxy, and V-02 requires this to be stated and checked. FIFTH, do NOT add a CLI verb or a new dependency; both are recorded deferrals with reasons.

EXECUTION CONTRACT. Commit only the four declared paths plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and do not push. Paste ACTUAL runner output for every test claim. `tests/test_executed_transition_gate_e2e.py` is a shared-checkout file, so restore each temporary corruption by reverting your own edit and prove it with an empty diff rather than a broad `git checkout` or `git stash` that could discard a co-worker's concurrent work.

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the runner performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/`.

HOW THIS PLAN CAN FAIL SILENTLY, stated for the executor. By making the four tests fail EARLIER instead of fail INSIDE the subtest context. A bare `self.fail(...)` or `assert` placed in the loop body but outside `with self.subTest(...)` aborts the sweep at the first bad row, so the remaining rows never run and the aggregate message reports one failing row where several are wrong. Both a green suite and a red suite can look correct after that mistake, because every row passes on an unmodified tree. The ONLY evidence that distinguishes the two is V-01's after-half showing that EVERY OTHER ROW STILL REPORTED A VERDICT alongside the corrupted one; do not substitute a simpler paste for it.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND all four `V-*` items carry pasted evidence with `Result: pass`, including V-01's before/after corrupted-row comparison on two tables and V-03's two honesty measurements, each with its empty-diff restore. On completion the runner sets backlog `nos070` to `graduated`. The item carries no `- Blocks-Release:` gate, so this plan correctly declares none; see OQ-01 for the classification question that could change that, which is the maintainer's to answer.
