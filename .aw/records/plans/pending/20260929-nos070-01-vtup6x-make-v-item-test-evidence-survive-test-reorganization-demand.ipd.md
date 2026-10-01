# IPD: Make V-item test evidence survive test reorganization: demand behaviour plus mechanism, and define the row substitution rule

- Date: 2026-09-29
- Kind: child
- Concern: An approved plan's `Required evidence:` can become literally unsatisfiable between review and execution when a suite is tabulated, because the demand names a test FUNCTION or asserts a COLLECTED COUNT rather than the behaviour pinned and the mechanism that pins it.
- Scope: Two workflow bodies (`plan-review` single-file and the long-form `review-rubric`), the `verify-execution` intent audit, and the `ipd-structure-and-linting` spec's evidence section. Prose conventions only; no production Python and no lint rule.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/verify-execution/intent-audit.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_v_item_evidence_durability.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: nos070
- Set: nos070
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vtup6x
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored in full from backlog `nos070`; ready for `/plan-review`.
- 2026-09-29 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED. Every one of F-01 through F-10 was independently re-measured at review HEAD `650f6772` and ALL REPRODUCE, including F-06's empirical falsification (corrupting one `MERGE_DECISIONS` row makes the suite FAIL while an `addSubTest` driver prints PASS for all seven rows including the corrupted one) and F-07's census (exactly 4 such blocks in 1 file, out of 266 subTest blocks measured). The BLOCKER (PR-001) is that E-02 prescribed DUPLICATING the rule into the long-form variant, while the repository's established and TEST-ENFORCED parity mechanism for this exact pair of files is a POINTER plus anchor phrases: `tests/test_plan_review_feasibility_rule.py` asserts the long-form carries `../plan-review/plan-review.md` and `per the parity note in \u0060plan-review-long.md\u0060`, so a duplicated paragraph creates precisely the silent-drift hazard this plan exists to prevent. A second measured correction (PR-002): the calibrated example this plan tells auditors to follow, `i4c0c3` V-03, pastes `[PASS]` lines from exactly the unsound driver shape F-06 falsifies, so E-03 must cite it for its SUBSTITUTION discipline while explicitly warning that its verdict lines are not a model to copy.

## Goal

Close the convention gap at the seam between two good practices: an IPD authored with a named-test or collected-count evidence demand, and a later commit that tabulates that suite. Make the AUTHORING rule state what a V-item must demand (the behaviour pinned plus the mechanism that pins it, re-derived at execution time), and make the SUBSTITUTION rule state what an executor does when the pointer it was given no longer exists, so the honest path is written down instead of improvised per plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the authoring rule that currently blesses the broken demand

- [x] E-01 In `.aw/system/workflows/plan-review/plan-review.md`, amend rubric G's re-derivation convention bullet (the bullet beginning `**Live-artifact success criteria vs. stable code facts (re-derivation convention):**`) so that a COLLECTED TEST COUNT and a TEST FUNCTION NAME are no longer covered by its EXEMPT clause. The bullet today exempts criteria counting `stable code facts (test assertions, schema keys, enum members)`; that exemption is what licensed i4c0c3's V-04 count demand. Replace the `test assertions` element of the exempt list with an explicit statement that a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts, so a V-item must demand the BEHAVIOUR pinned plus the MECHANISM that pins it, and must require re-derivation at execution time. Keep the rest of the bullet (live-artifact counts, the orchestrator-children exemption, the "review is the only enforcement surface" note) intact: schema keys and enum members remain genuinely stable and stay exempt.
  - Depends on: none
  - Expected outcome: the bullet no longer exempts a test count or a test name, states the behaviour-plus-mechanism demand, and permits a test name only as a NON-BINDING pointer. `grep -n 'test assertions' .aw/system/workflows/plan-review/plan-review.md` returns no line inside that bullet.
  - Execution state: performed

- [x] E-02 Close the long-form parity hole F-03 measured, USING THE REPOSITORY'S ESTABLISHED PARITY MECHANISM FOR THIS EXACT PAIR OF FILES, which is a POINTER and not a copy.

  **DO NOT DUPLICATE THE AMENDED BULLET INTO `review-rubric.md`. THE AUTHORED INSTRUCTION TO DO SO WOULD CREATE THE VERY DRIFT THIS PLAN EXISTS TO PREVENT (F-11).** Measured at review: `tests/test_plan_review_feasibility_rule.py` already enforces parity between these two bodies for the feasibility rule, and the shape it enforces is a REFERENCE: it asserts the long-form section contains the literal `../plan-review/plan-review.md` and the literal ``per the parity note in `plan-review-long.md` ``, alongside anchor phrases. `spec-review.md` uses the same shape, and that test's own docstring calls it "references plan-review's rule without copying the five points". Two full copies of a normative paragraph in one repository is a single-source-of-truth violation, and nothing in the toolchain diffs two prose paragraphs for semantic equivalence, so the copies drift silently. That is the identical failure class as the pointer-versus-behaviour confusion this plan is correcting one level up.

  SO WRITE A POINTER BULLET in `## A. Plan completeness`, beside the existing `Right-sizing and conceptual density (per E-item)` and `Maintainer sizing signals` bullets. It must contain: the rule's NAME and its operative one-sentence summary (a V-item demands the behaviour pinned plus the mechanism that pins it; a collected test count is never the bar; a test name is a non-binding pointer only), the literal path `../plan-review/plan-review.md`, and the literal phrase ``per the parity note in `plan-review-long.md` `` so it matches the enforced convention. An agent reading only the long-form must be able to APPLY the rule from the summary and must be able to FIND the full text; it must not be reading a second normative copy that can disagree with the first.
  - Depends on: E-01
  - Expected outcome: `review-rubric.md` carries a pointer bullet whose one-sentence summary answers V-01's three questions the same way E-01's bullet does, whose full text lives in exactly ONE place, and which carries both literals the shipped parity test convention uses. `git show HEAD:.aw/system/workflows/plan-review-long/review-rubric.md | grep -c 'Live-artifact'` returns `0`, confirming F-03's hole was real and this is an addition.
  - Execution state: performed

### Task group 2: write down what an executor does when the pointer has died

- [x] E-03 In `.aw/system/workflows/verify-execution/intent-audit.md`, extend the existing unsatisfiable-demand paragraph (the one beginning `An item whose evidence reports the demand itself as unsatisfiable is classified` `done` `only if the evidence satisfies a three-part bar`) with the TABULATION SUBSTITUTION case as a named instance of that bar. State the three obligations concretely for this case: (a) show the named function is gone and name the commit that removed it, (b) name the SUCCESSOR ROW by its case string and the table constant and class that hold it, and (c) paste that row's individual verdict rather than the enclosing function's. Keep the paragraph's closing rule that an unsatisfiable demand remains a plan DEFECT to report as a finding, and keep the existing `u23gbn` calibrated example. Add `i4c0c3` V-03/V-04 as the calibrated passing example for the tabulation case, since its observed-evidence blocks already record exactly this substitution.

  **CITE `i4c0c3` FOR ITS SUBSTITUTION DISCIPLINE AND EXPLICITLY WARN THAT ITS VERDICT LINES ARE NOT A MODEL TO COPY (F-12).** Measured at review: its V-03 evidence pastes bracketed `[PASS] <case string>` lines per row, which is exactly the driver shape F-06 falsifies for this file's idiom. Its substitution is sound in the three respects the bar cares about (it proves the function is gone and names the removing commit, it names both successor rows by case string and table constant, and it shows the enclosing table passing), and those are what make it the calibrated example. But a reader who copies its per-row `[PASS]` lines inherits a driver that reports PASS for a row that is actually failing. So the text must state BOTH: the substitution obligations it satisfies, and the one thing about it not to imitate, naming child `02` (`t5txjk`) as the owner of a sound driver. Writing the example without that warning would bless, in the very document that teaches the substitution, the unsoundness F-06 exists to flag.

  STATE THE ROW-VERDICT OBLIGATION IN TERMS OF SOUNDNESS, NOT OF A COMMAND. Require that the pasted per-row verdict be produced by a mechanism whose FAILURE is observable for that row, and require the auditor to reject a per-row PASS that co-occurs with an enclosing failure, which is the observable signature of the unsound shape (F-06 measured `FAILED (failures=1)` alongside seven `PASS` rows). Until child `02` ships a sound driver, an honest executor may instead paste the enclosing table's verdict plus the row's inputs and expected value, and SAY that is what they did; that is strictly better than a per-row PASS that cannot fail.
  - Depends on: E-01
  - Expected outcome: the intent audit tells an auditor how to grade a tabulation substitution instead of leaving it to judgement, and cites a real in-repo example of a substitution that met the bar.
  - Execution state: performed

- [x] E-04 Amend Section 5.4 (`### 5.4 Evidence requirements`) of the spec `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` to record the DURABILITY property of an authored evidence demand: `Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour. Add the test-organization case explicitly (a collected count and a test function name are not durable; the behaviour plus the mechanism that pins it is), and add one sentence stating that when the named mechanism has been reorganized the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. State plainly, in the same place, that this is a CONVENTION the linter does not and will not check, consistent with the section's existing closing sentence that the linter `checks presence and state consistency` and `MUST NOT claim that evidence is authentic, relevant, or sufficient`.
  - Depends on: E-01
  - Expected outcome: the spec section that defines what `Required evidence:` must be now also says it must be durable, with the test-count and test-name cases named, and with the linter boundary restated so no reader expects mechanical enforcement.
  - Execution state: performed

### Task group 3: pin the convention so it cannot silently revert

- [x] E-05 Add `tests/test_v_item_evidence_durability.py` with the PRESENCE-AND-NARROWING test over the single-file `plan-review` body: that the amended rule is present, and that a collected test count and a test function name are NO LONGER inside the exempt clause, while `schema keys`, `enum members` and the orchestrator-children clause remain exempt and the live-artifact requirement is unchanged.

  THE P16 POSITION, which must be recorded in the module docstring rather than assumed. This test reads WORKFLOW BODIES and a SPEC, never `agent_workflows/*.py`, so it sits inside GUIDING_PRINCIPLES P16's stated narrow exception (verified verbatim at review: "Content verification is permissible only where the text or file itself is the artifact under test") and outside its "No production source inspection" prohibition (whose enumerated targets are all `agent_workflows/*.py`). Follow the precedent and the justification shape of `tests/test_plan_review_feasibility_rule.py`, whose docstring records the same exemption and names the deletion plan (`96xtmi`, now executed) it was written against; write the equivalent docstring here. Assert on a SMALL number of distinctive semantic anchors, not on whole paragraphs, so wording may be improved without breaking the test.
  - Depends on: E-01, E-04
  - Expected outcome: a test module that fails if the single-file variant loses the amended rule or re-widens the exemption, and that carries an explicit P16 justification docstring.
  - Execution state: performed

- [x] E-06 In the SAME new test module, add the PARITY test over the long-form variant, which is the assertion this plan most needs because nothing in the toolchain diffs two workflow bodies today (F-03's hole).

  PIN THE POINTER SHAPE E-02 ESTABLISHES, not a duplicated paragraph: assert `review-rubric.md` carries the rule's one-sentence summary anchor, the literal `../plan-review/plan-review.md`, and the literal ``per the parity note in `plan-review-long.md` ``, which is exactly the trio `tests/test_plan_review_feasibility_rule.py` already asserts for the feasibility rule (measured at review). DO NOT assert that the two files contain the same paragraph text: after E-02 they deliberately do not, and such an assertion would either fail immediately or push a future maintainer back into duplication.
  - Depends on: E-02, E-05
  - Expected outcome: a test that fails if the long-form loses its pointer bullet or its reference literals, and that does NOT require the two bodies to hold identical prose.
  - Execution state: performed

- [x] E-07 VALIDATE THE WHOLE CHANGE AND DOGFOOD THE RULE ON THIS PLAN ITSELF, which is this plan's real acceptance test and was previously buried in a V-item with no owning E-item.

  Run a bare `python3 -m pytest` and compare against a bare run taken immediately before the first edit IN THIS SAME LANE, judged on the delta of failing node ids (do NOT compare against any number written in this plan). Run `python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_installer.py`, which exercise the two workflow bodies this plan edits and the installer that ships them. CONFIRM the Spec-sync managed-block claim by SEARCH rather than assertion (grep the amended anchor over `agent_workflows/engine.py`); measured at review it returns nothing, but re-derive it. THEN DOGFOOD: read this plan's own V-items against the amended rubric G and confirm none demands a collected test count or the presence of a named test function AS ITS BAR. Note the distinction the rule itself draws, so this check is applied honestly: naming `tests/test_plan_review_feasibility_rule.py` as a file to RUN is a mechanism, not a count and not a name-as-contract, and remains legitimate.
  - Depends on: E-03, E-05, E-06
  - Expected outcome: no new failing node id against a same-lane baseline; both named test files pass; the managed-block claim is re-derived by search; and every V-item in this plan is confirmed to comply with the rule this plan adds.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE TWO PLAN-REVIEW VARIANTS ARE KEPT IN DELIBERATE PARITY. `review-rubric.md`'s own `SCOPE-FENCE WORDING` note says so in those words (`kept in deliberate parity with the single-file variant`), and `agent_workflows/migration_inventory.py` records `plan-review-long` as an ALIAS of `plan-review` (`_PLAN_REVIEW_ALIAS`, `PLAN_REVIEW_ALIAS`). A rule added to one belongs in both; E-02 exists because of this.
- A PRECEDENT EXISTS FOR EDITING BOTH VARIANTS IN ONE COMMIT. Commit `e6566341` (`workflows: add sweep obligation to plan-review and unsatisfiable V-* rule to verify-execution`) added one paragraph to `plan-review/plan-review.md`, the parallel paragraph to `plan-review-long/02-review-and-revise.md`, and the unsatisfiable-demand bar to `verify-execution/intent-audit.md`: the same three-surface shape this plan uses.
- A PRECEDENT EXISTS FOR A TEST THAT READS A WORKFLOW BODY. `tests/test_plan_review_feasibility_rule.py` pins anchor phrases in `plan-review/plan-review.md`, `plan-review-long/03-resolve-and-finalize.md` and `spec-review/spec-review.md`, and its module docstring records the P16 exemption explicitly (`A workflow body is a WORKFLOW BODY, the artifact under change, and this test reads no agent_workflows/* source`). E-05 follows it deliberately rather than inventing a shape.
- THE LINTER WILL NOT ENFORCE THIS AND MUST NOT BE ASKED TO. Spec Section 5.4 ends `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.`, and Section 10.1 lists `truth, relevance, independence, or sufficiency of observed evidence` among the things a passing lint does not establish. `agent_workflows/ipd_lint.py` bears this out: `IPD-S402` (via `ipd_schema.validation_row_error`) and the `pre-transition` arm of `IPD-S404` test only that `Observed evidence:` is non-whitespace. Any non-empty string passes. This plan therefore changes CONVENTIONS and REVIEW, which is where the repository already puts semantic judgement (rubric G's own parenthetical: `Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading`).
- THE TABULATION CONVENTION IS UNDOCUMENTED. The canonical row shape (`(case, <inputs...>, expected, needles, forbidden, why)`, case first and a trailing `why` quoted back in the failure message) exists purely as a code idiom plus commit `75b90271`'s message; `tabulat`/`table-driven`/`subtest` appear nowhere in `GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md`, `AGENTS.md`, `ARCHITECTURE.md` or `docs/`. This plan does not document it (that is not the seam the backlog item names); it only makes the evidence rule independent of it.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The repository's ONLY rule about count-based success criteria currently EXEMPTS the exact case that broke. Rubric G's re-derivation bullet in `plan-review/plan-review.md` requires re-derivation for `live artifacts` but declares criteria counting `stable code facts (test assertions, schema keys, enum members)` EXEMPT `because these are fixed authored facts rather than drifting live populations`. A collected test count is NOT a fixed authored fact: commit `75b90271` changed it from 27 to 6 while removing no behaviour. E-01 corrects precisely this clause. | `.aw/system/workflows/plan-review/plan-review.md`, rubric G section `### G. Plan executability`, the bullet beginning `**Live-artifact success criteria vs. stable code facts` |
| F-02 | Nothing in the spec forbids the broken demand, so the author who wrote i4c0c3's V-03/V-04 violated no rule. Spec Section 5.4 lists five acceptable evidence forms including `a test report or structured result file` and says `Required evidence:` `MUST describe evidence capable of revealing failure`; it never mentions test names or counts, and never mentions durability across a refactor. E-04 adds that property. | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`, `### 5.4 Evidence requirements` |
| F-03 | The re-derivation bullet is MISSING from the long-form variant, a pre-existing parity hole. `grep -rln 'Live-artifact' .aw/system/workflows/` matches `plan-review/plan-review.md` alone, while the neighbouring right-sizing and maintainer-sizing bullets DO appear in both. So an agent running the long-form flow never sees the rule at all. E-02 closes this. | `grep -rln 'Live-artifact' .aw/system/workflows/` -> one path; `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness` carries the sibling bullets but not this one |
| F-04 | An unsatisfiable-demand bar ALREADY EXISTS and is the right place to hang the substitution rule, so this plan extends rather than invents. `verify-execution/intent-audit.md` already grades such an item `done` only on a three-part bar (state why it cannot be met, prove impossibility by MEASUREMENT not prose, evidence the satisfiable counterpart) and still requires reporting the contradiction as a finding. i4c0c3's substitution already satisfies that bar in substance. E-03 names the tabulation case as an instance. | `.aw/system/workflows/verify-execution/intent-audit.md`, the paragraph beginning `An item whose evidence reports the demand itself as unsatisfiable` |
| F-05 | The i4c0c3 substitution is a sound worked precedent and should be cited rather than re-derived. Its V-03 observed evidence records `THE TWO NAMED TESTS NO LONGER EXIST AS FUNCTIONS, and the substance they pinned does`, names commit `75b90271`, names both successor rows by case string and table (`PreCommitExecutedGateTests.SITUATIONS`, `MergeAwareInTreeEvidenceTests.MERGE_DECISIONS`), and pastes per-row verdicts; its V-04 records `THE EXPECTED COUNT OF 31 IS UNREACHABLE AND ITS PURPOSE IS SERVED A DIFFERENT WAY` and counts ROWS off the tables instead. | `.aw/records/plans/executed/20260908-gatejrnl-01-i4c0c3-stop-the-executed-transition-gate-firing-on-a-follow-up-edit.ipd.md`, V-03 and V-04 observed-evidence blocks |
| F-06 | The substitution rule must NOT be written as "paste the subTest verdicts", because the obvious driver that produces them is UNSOUND for this repository's dominant table idiom. Measured on 2026-09-29 against the real `MERGE_DECISIONS` table: corrupting one row's expected exit code to an impossible `99` makes the suite FAIL (`FAILED (failures=1)`, the assertion naming `check` `decided 1 of 7 merge situations wrongly`) while an `addSubTest` driver prints `PASS` for ALL SEVEN ROWS INCLUDING THE CORRUPTED ONE. The cause is structural: these tests append to a `wrong` list INSIDE the `subTest` block and assert ONCE after the loop, so no exception is ever raised inside the subtest context and `addSubTest` records every row as a success. E-03 therefore requires the row's individual verdict WITHOUT prescribing that mechanism, and child `02` owns making a sound one exist. | measured at authoring; `tests/test_executed_transition_gate_e2e.py`, `MergeAwareInTreeEvidenceTests.test_merge_state_never_becomes_a_blanket_exemption` (`wrong.append(` inside `with self.subTest(case=case):`, single `self.assertEqual(wrong, [], ...)` after the loop) |
| F-07 | The population affected by F-06 is exactly FOUR subTest blocks in ONE file, and it is the same file that produced i4c0c3's evidence. A census over `tests/*.py` for a `subTest` block that appends a failure but contains no `assert`/`fail`/`raise` returns 4 blocks, all in `tests/test_executed_transition_gate_e2e.py` (`test_each_staged_situation_gets_its_own_verdict_and_reason`, `test_the_merge_detector_reports_the_incoming_side_in_every_state`, `test_merge_state_never_becomes_a_blanket_exemption`, `test_git_itself_enforces_the_gate_at_both_merge_stages`). The other 242 subTest blocks across 46 files assert in context and DO report per-row verdicts truthfully. This bounds child `02` and is why it is a small plan, not a suite-wide sweep. | measured at authoring over `tests/*.py`; the four enclosing test methods in `tests/test_executed_transition_gate_e2e.py` |
| F-08 | A sound per-row driver DOES exist in the repository as a worked precedent, for the assert-in-context idiom. Executed plan `0i4fkt` pastes an `addSubTest`-subclass harness printing `subtest (tree='specs'): PASSED` per row, and its target (`tests/test_attention_contract.py`, `test_every_tracked_tree_records_reach_the_view`) asserts INSIDE the `subTest` block, so its verdicts are truthful. The distinction between that case and F-06's is the assert's LOCATION, which is why the rule must be stated in terms of the verdict required rather than the command that prints it. | `.aw/records/plans/executed/20260925-smallfix-01-0i4fkt-five-small-cleanups-runner-parser-seam-stale-runner-comment.ipd.md` V-02 evidence; `tests/test_attention_contract.py` `test_every_tracked_tree_records_reach_the_view` |
| F-09 | A passing subTest is silent under the repository's actual runner configuration, so the backlog item's premise holds and no config change would surface row verdicts. `pyproject.toml` `[tool.pytest.ini_options]` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, and the `test`/`dev` extras declare `pytest>=8`, `pytest-xdist>=3`, `pytest-randomly>=3`, `PyYAML>=6`. `pytest-subtests` is NOT declared and NOT installed, so pytest does not surface even FAILING subtests as separate ids. The 33 rows of `tests/test_executed_transition_gate_e2e.py` collect as 7 tests. | `pyproject.toml` `[tool.pytest.ini_options]` `addopts`, and the `test`/`dev` extras; `python3 -m pytest tests/test_executed_transition_gate_e2e.py -o addopts="" -v` -> `7 passed` |
| F-10 | The file i4c0c3 named no longer holds the tables, so an executor re-checking that evidence today must follow one more hop. `tests/test_executed_transition_gate.py` still exists but contains neither table; `SITUATIONS` (15 rows) and `MERGE_DECISIONS` (7 rows) now live in `tests/test_executed_transition_gate_e2e.py`, moved by the trim-and-restore pair `19313eed` then `cd79ff6e`. This is a SECOND independent instance of the same class of drift (the pointer moved, the behaviour did not), which strengthens the case for a durability rule over a naming rule. | `tests/test_executed_transition_gate_e2e.py` (`PreCommitExecutedGateTests.SITUATIONS`, `MergeAwareInTreeEvidenceTests.MERGE_DECISIONS`); commits `19313eed`, `cd79ff6e` |
| F-11 | **REVIEW FINDING, BLOCKING: E-02 AS AUTHORED PRESCRIBED DUPLICATING A NORMATIVE PARAGRAPH, which creates the very silent drift this plan exists to prevent.** The repository's established parity mechanism for THIS EXACT PAIR of files is a POINTER, and it is TEST-ENFORCED: `tests/test_plan_review_feasibility_rule.py` asserts the long-form section contains the literal `../plan-review/plan-review.md` and the literal ``per the parity note in `plan-review-long.md` ``, and its own docstring for the sibling surface says "references plan-review's rule without copying the five points". Nothing in the toolchain diffs two prose paragraphs for semantic equivalence, so two normative copies drift unobserved. FIXED: E-02 now writes a POINTER bullet (summary + both literals) and forbids duplication; E-06 pins the pointer trio rather than paragraph equality. | Measured at review HEAD `650f6772`: `tests/test_plan_review_feasibility_rule.py` `test_spec_review_feasibility_rule_reference` docstring and the three `assertIn` calls for `../plan-review/plan-review.md`, the parity-note literal, and the subsection heading; `spec-review.md` uses the same reference shape. |
| F-12 | **REVIEW FINDING: the calibrated example this plan tells auditors to follow pastes verdict lines from exactly the driver shape F-06 falsifies.** `i4c0c3` V-03's observed evidence contains bracketed `[PASS] <case string>` lines per row for `MergeAwareInTreeEvidenceTests`, whose table is one of F-07's four unsound blocks. Its SUBSTITUTION is sound (function-gone proof with the removing commit, both successor rows named by case string and table constant, enclosing table verdict pasted), which is what makes it the right calibrated example; its per-row verdict MECHANISM is not. Citing it without that caveat would bless the unsoundness in the very document that teaches the substitution. | Measured at review: `i4c0c3` V-03 evidence lines `[PASS] a hand-edited status flip OUTSIDE any merge` and `[PASS] a \`git mv\` into executed/ OUTSIDE any merge`, against F-06's own measurement that such a driver prints PASS for a row that is failing. | FIXED: E-03 now requires the text to cite `i4c0c3` for its substitution discipline AND to warn that its verdict lines are not a model to copy, naming `t5txjk` as the owner of a sound driver; and to state the row-verdict obligation in terms of SOUNDNESS (the mechanism's failure must be observable for that row; reject a per-row PASS co-occurring with an enclosing failure) with an honest fallback until child `02` ships. |
| F-13 | **REVIEW FINDING: the plan's real acceptance test had no owning E-item.** The DOGFOOD CHECK and the whole-suite validation lived only in `## Required tests / validation` prose and inside the old V-05's evidence demand, so no execution checklist item owned them and the E/V mapping did not reach them. An obligation with no E-item is one an executor can complete the plan without performing. | Read at review: the authored checklist ended at E-05, while `## Required tests / validation` carried four obligations including the dogfood check described as "the real acceptance test of this plan". | FIXED: added E-07 owning the suite comparison, the two named test files, the managed-block re-derivation and the dogfood check, with V-07 demanding each. It also records the distinction that keeps the dogfood check honest: naming a test FILE TO RUN is a mechanism, not a name-as-contract. |
| F-14 | **REVIEW FINDING: E-05 as authored bundled two independent test surfaces,** which the deterministic density check flagged (`IPD-Z602`, "3 clauses"). The presence-and-narrowing assertion over the single-file body and the PARITY assertion over the long-form body are different surfaces with different failure meanings, and after F-11 they assert structurally different things (rule text versus pointer literals), so one V-item could not check either properly. | `aw ipd lint --phase author` at review HEAD reported `IPD-Z602` on E-05; after the split `--phase review-finalize` reports clean with zero findings. | FIXED: split into E-05 (presence and narrowing) and E-06 (parity pointer), with V-05/V-06 each demanding one surface's mutation proof. `- Highest E allocated:` raised to `07`. |

## Proposed changes (ordered, validatable)

1. Amend rubric G's re-derivation bullet in the single-file `plan-review` so a collected test count and a test function name are no longer exempt, and state the behaviour-plus-mechanism demand (E-01).
2. Close the parity hole F-03 records by adding a POINTER bullet to the long-form `review-rubric`, using the test-enforced reference shape rather than a duplicated paragraph (E-02, F-11).
3. Extend the existing unsatisfiable-demand bar in `verify-execution/intent-audit.md` with the tabulation substitution case, the `i4c0c3` calibrated example, and the warning that its per-row verdict lines are not a model to copy (E-03, F-12).
4. Record the durability property of `Required evidence:` in spec Section 5.4, restating the linter boundary (E-04).
5. Add `tests/test_v_item_evidence_durability.py` pinning the amended rule's presence and its narrowed exemption (E-05).
6. Add the parity test over the long-form pointer trio in the same module (E-06).
7. Validate the whole change against a same-lane baseline and DOGFOOD the new rule on this plan's own V-items (E-07, F-13).
## Deferred / out of scope (with reason)

- A LINT RULE THAT REJECTS A COUNT-BASED OR NAME-BASED V-ITEM. Deferred on the AUTHORITY axis, not the effort axis: spec Section 5.4 ends `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.` and Section 10.1 excludes evidence `truth, relevance, independence, or sufficiency` from what a passing lint establishes. Rubric G's own parenthetical already refuses the mechanical route for the sibling case (`no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading`). Building one here would contradict an implemented spec this plan is otherwise amending consistently. If it is ever wanted, it needs its own spec amendment first.
  - Carrier-Declined: No obligation is left outstanding, because this is a refusal on authority rather than a postponement. The implemented spec forbids the linter from judging evidence sufficiency, so the work is not deferred until later, it is declined until a maintainer chooses to amend that boundary. Filing a carrier would assert a gap the repository's own contract says must not be closed mechanically.
- THE ROW-VERDICT TOOLING, AND REPAIRING THE FOUR UNSOUND SUBTEST BLOCKS. Split out to child `nos070-02` (`t5txjk`) because it is CODE with its own test surface, while this plan is conventions; and because the backlog item itself rates the tooling `Worth considering, not obviously worth building yet`, a weaker mandate than the convention it rates as the thing to solve for. This plan is deliberately usable with no tooling at all: E-03 demands the row's individual verdict and does not prescribe how it is obtained.
  - Carrier: t5txjk
- DOCUMENTING THE TABLE-DRIVEN TEST CONVENTION ITSELF (row shape, the `why` column, when to tabulate). Out of scope: the backlog item is explicit that tabulation is `NOT a defect`, and the missing convention is `at the seam between them`, not inside either. This one IS real outstanding work rather than a declined idea, so it was FILED rather than parked in this plan's prose: backlog `7fzqop` owns it.
  - Carrier: 7fzqop
- RETROACTIVELY AUDITING EXECUTED PLANS FOR COUNT-BASED V-ITEMS. Out of scope and partly forbidden: the execution contract bars changing what an executed plan RECORDS. i4c0c3 is already correctly substituted and already reports its own contradiction.
  - Carrier-Declined: No obligation is left outstanding. An executed plan's record is immutable by contract, so there is no permitted remediation to carry; the sole known instance is already correctly substituted and self-reporting. A carrier here would name work nobody is allowed to do.

## Scope check

- Over-scope: none. Four prose surfaces plus one new test file, all in `- Scope-Paths:`.
- Under-scope: an author using the `assess` workflow to write an IPD reads `assess/assess.md` and the template `assess/templates/ipd.md`, neither of which is amended here, so the corrected rule reaches an author through REVIEW rather than at first draft. Accepted deliberately: the template's `Required evidence: TODO falsifiable evidence.` placeholder is a tracked authoring-incomplete marker (catalog invariant `I-12`, `agent_workflows/ipd_authoring.py`), so editing it risks the placeholder-detection contract for a gain review already delivers. A reviewer applying the amended rubric G is the enforcement surface either way, and `/plan-review` runs on every plan before approval. Flagged for the reviewer to overrule if they prefer the earlier touchpoint.

## Required tests / validation

- `python3 -m pytest tests/test_v_item_evidence_durability.py` for the new pins, plus a SOURCE-FILE mutation proof for EACH of the two surfaces (re-widen the single-file exemption; delete the long-form pointer bullet), each restored with an empty `git diff --stat` so no temporary edit is left in this shared checkout.
- `python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_installer.py` because those exercise the two workflow bodies this plan edits and the installer that ships them.
- A bare `python3 -m pytest` for the whole suite, compared against a bare run taken IMMEDIATELY BEFORE the change in this same lane. Do NOT compare against any number written in this plan: per the repository's own measured guidance, a plan-recorded figure cannot distinguish an added test from a merge landing on main.
- A DOGFOOD CHECK, which is the real acceptance test of this plan and is OWNED BY E-07 (not left as prose): read this plan's own V-items against the amended rubric G and confirm none of them demands a collected test count or binds to a test function name AS ITS BAR. Naming a test file to RUN is a mechanism and stays legitimate. A plan that fixes this rule while violating it is not executed correctly.

## Spec / documentation sync

- `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 5.4 is AMENDED by E-04, and is declared in `- Scope-Paths:` so both runners announce the spec edit before the run and reconcile it afterwards. WHY the amendment belongs in this change: Section 5.4 is the single definition of what `Required evidence:` must be, and the durability property is a property OF that definition. Leaving it out would put the operative rule in a workflow body while the spec that governs the field stayed silent, which is the drift this repository's single-source-of-truth principle exists to prevent, and would leave the next author reading the spec with no reason not to write the demand that broke.
- The spec's `- Status:` is `implemented`. E-04 changes the contract it states, not the record of whether it was built, so the status is left alone; the amendment is additive and no implemented behaviour is retracted. The spec carries no `- Id:` bullet (it is a legacy pre-cutover name), so it is cited here by path and section.
- `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/review-rubric.md` and `.aw/system/workflows/verify-execution/intent-audit.md` are workflow bodies shipped by the installer; no generated or managed block in `agent_workflows/engine.py` restates rubric G, so no managed-block regeneration is required. Re-measured at review HEAD `650f6772`: a grep for `rubric G`, `Live-artifact` and `re-derivation` over `agent_workflows/engine.py` returns nothing. The executor MUST re-derive this by search rather than assume it (E-07, V-07).

## Open questions

### OQ-01: Should the corrected rule reach an author at DRAFT time by amending the `assess` template, or only at REVIEW time through rubric G?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: review time only, for this plan. The template's validation placeholder (`Required evidence: TODO falsifiable evidence.`) is load-bearing for placeholder detection as catalog invariant `I-12` in `agent_workflows/ipd_authoring.py`, and `aw ipd sync` emits the identical string per newly assigned E-item, so the template is a poor place for narrative guidance and a risky one to edit. Rubric G is applied to every plan before approval, so the rule is enforced on the whole population either way. Recorded in Scope check under-scope so a reviewer who prefers the earlier touchpoint can add it as a finding.

### OQ-02: Does amending an `implemented` spec require its status to change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from the repository's own instructions: `A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT`, and specs are `living contracts, not immutable history`. The obligation is to list the `.spec.md` in `- Scope-Paths:` (done) and to say why in the spec-sync section (done). Nothing requires a status change, and `implemented` continues to describe truthfully what was built; the amendment adds a property to a definition and retracts no shipped behaviour.

### OQ-03: Should the long-form variant carry a COPY of the amended rule or a POINTER to it?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us (reviewer)
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM THE SHIPPED, TEST-ENFORCED PRECEDENT: a POINTER, carrying the rule's one-sentence operative summary plus the two reference literals. The authored plan said to copy the bullet, and that is the one change in this plan that would have reproduced its own target defect at a different layer. THE EVIDENCE: `tests/test_plan_review_feasibility_rule.py` already enforces parity for these two bodies and the shape it enforces is a REFERENCE, asserting the long-form section contains the literal `../plan-review/plan-review.md` and the literal ``per the parity note in `plan-review-long.md` ``; its sibling case for `spec-review.md` is named "references plan-review's rule without copying the five points". WHY IT MATTERS ON THE MERITS AND NOT ONLY BY PRECEDENT: nothing in the toolchain compares two prose paragraphs for semantic equivalence, so two normative copies of one rule drift silently and a reader cannot tell which is authoritative. This plan's entire thesis is that a POINTER is legitimate while treating the pointer's text as the contract is what breaks; duplicating the paragraph would treat two texts as one contract. ALTERNATIVES REJECTED: (a) a verbatim copy in both files, rejected above; (b) a bare cross-reference with no summary, rejected because an agent running only the long-form flow must be able to APPLY the rule without opening a second file, which is the purpose the long-form's own summary bullets already serve; (c) moving the rule wholly into the long-form and pointing the single-file at it, rejected because the single-file variant is explicitly the portable one that must stand alone. REVERSIBLE: yes, either shape can be converted later, and E-06's test pins whichever is chosen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review/plan-review.md` showing the amended bullet in full. Then demonstrate the BEHAVIOUR CHANGE rather than asserting it, by answering three questions against the amended text and pasting the answering sentence for each: (a) may a V-item's bar be a collected test count? (b) may it be the presence of a named test function? (c) what must it be instead? The amended bullet must answer no, no, and behaviour-plus-mechanism-re-derived-at-execution. Also paste the result of re-reading the bullet's SURVIVING exemptions and confirm `schema keys` and `enum members` and the orchestrator-children clause are still exempt and the live-artifact requirement is unchanged, since narrowing an exemption must not silently delete the rest of the rule.
  - Observed evidence: `git diff -- .aw/system/workflows/plan-review/plan-review.md`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review/plan-review.md b/.aw/system/workflows/plan-review/plan-review.md
    index 495a5c49d..5c7857c62 100644
    --- a/.aw/system/workflows/plan-review/plan-review.md
    +++ b/.aw/system/workflows/plan-review/plan-review.md
    @@ -551,7 +551,7 @@ Verify the plan states:
     - For an agent-executable plan: BOTH a top execution checklist AND an end verification/cross-check
       checklist that maps 1:1 with concrete per-item evidence. A weak or absent verification checklist
       (one that could let an agent claim completion without doing every step) is an UNDER-SCOPE finding.
    -- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (test assertions, schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
    +- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
     - **Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):** When a plan demands proof that an advisory rule adds no error, the author must demand evidence that can actually be produced. The canonical proof requires two limbs:
       (a) a **registry severity assertion**, showing the rule id resolves through `check_engine.rule_spec` to the intended severity; and
       (b) a **gate-consequence measurement**, driving `artifact_core.drift_exit_code` with the finding list and pasting its return value as a contrastive pair--asserting the real finding list exits 1 (e.g. `drift_exit_code(drift) == 1` for `warning` or `error`) AND that the same finding list with its severity swapped to `info` exits 0 (e.g. `drift_exit_code([d._replace(severity="info") for d in drift]) == 0`). The pair is what localizes the exit code to the severity under test.
    ```

    Demonstration of behaviour change by answering the three questions:
    (a) May a V-item's bar be a collected test count?
    No. Answering sentence: "In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer)."
    (b) May it be the presence of a named test function?
    No. Answering sentence: "neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer)."
    (c) What must it be instead?
    Behaviour-plus-mechanism-re-derived-at-execution. Answering sentence: "A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time."

    Surviving exemptions re-read and confirmed:
    `schema keys`, `enum members`, and `orchestrator counting its own declared children` remain exempt:
    "Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations."
    Live-artifact requirement is unchanged:
    "An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar."
    `grep -n 'test assertions' .aw/system/workflows/plan-review/plan-review.md` returns no match (exit code 1).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md`. Then prove PARITY by extracting the test-evidence rule from BOTH files and pasting them adjacently for comparison, so a reader can see the two variants now answer V-01's three questions identically. Confirm by measurement that the bullet was ABSENT before this change (paste `git show HEAD:.aw/system/workflows/plan-review-long/review-rubric.md | grep -c 'Live-artifact'` or the equivalent for the amended anchor, expecting `0`), which is what makes this an added bullet rather than an edited one and confirms F-03 was a real hole rather than a misread.
  - Observed evidence: `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review-long/review-rubric.md b/.aw/system/workflows/plan-review-long/review-rubric.md
    index fa78fe8d3..88908d833 100755
    --- a/.aw/system/workflows/plan-review-long/review-rubric.md
    +++ b/.aw/system/workflows/plan-review-long/review-rubric.md
    @@ -35,6 +35,7 @@ For an agent-executable plan (an IPD or similar with actionable steps), it must
     verification/cross-check checklist that maps 1:1 with concrete per-item evidence; a weak or
     absent verification checklist (one that could let an agent claim completion without doing every
     step) is an UNDER-SCOPE finding.
    +- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** A V-item demands the behaviour pinned plus the mechanism that pins it (re-derived at execution time); a collected test count is never the bar; a test name is a non-binding pointer only (see `../plan-review/plan-review.md` per the parity note in `plan-review-long.md`).
     - **Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):** When a plan demands proof that an advisory rule adds no error, the author must demand evidence that can actually be produced. The canonical proof requires two limbs:
       (a) a **registry severity assertion**, showing the rule id resolves through `check_engine.rule_spec` to the intended severity; and
       (b) a **gate-consequence measurement**, driving `artifact_core.drift_exit_code` with the finding list and pasting its return value as a contrastive pair--asserting the real finding list exits 1 (e.g. `drift_exit_code(drift) == 1` for `warning` or `error`) AND that the same finding list with its severity swapped to `info` exits 0 (e.g. `drift_exit_code([d._replace(severity="info") for d in drift]) == 0`). The pair is what localizes the exit code to the severity under test.
    ```

    Parity comparison between the two files:
    Single-file (`plan-review.md`):
    "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)"

    Long-form (`review-rubric.md`):
    "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** A V-item demands the behaviour pinned plus the mechanism that pins it (re-derived at execution time); a collected test count is never the bar; a test name is a non-binding pointer only (see `../plan-review/plan-review.md` per the parity note in `plan-review-long.md`)."

    Comparison against V-01's three questions:
    (a) may a V-item's bar be a collected test count?
    - Single-file: No ("neither may serve as a V-item's bar").
    - Long-form: No ("a collected test count is never the bar").
    (b) may it be the presence of a named test function?
    - Single-file: No ("neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer)").
    - Long-form: No ("a test name is a non-binding pointer only").
    (c) what must it be instead?
    - Single-file: Behaviour-plus-mechanism-re-derived-at-execution ("A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time").
    - Long-form: Behaviour-plus-mechanism-re-derived-at-execution ("A V-item demands the behaviour pinned plus the mechanism that pins it (re-derived at execution time)").
    Both variants answer all three questions identically.

    Measurement confirming pre-edit absence:
    `git show HEAD:.aw/system/workflows/plan-review-long/review-rubric.md | grep -c 'Live-artifact'` returned `0` (exit code 1), confirming the bullet was absent and F-03 was a real hole.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff -- .aw/system/workflows/verify-execution/intent-audit.md`. Prove the extension is an EXTENSION and not a replacement: paste the surviving three-part bar, the surviving `u23gbn` example, and the surviving rule that an unsatisfiable demand is still a reportable plan defect. Then APPLY the new text to the real historical case as a calibration check: walk i4c0c3's V-03 evidence against the three obligations E-03 states and paste, for each, the sentence in that evidence which satisfies it. If any of the three is NOT satisfied by i4c0c3's evidence, say so plainly rather than stretching the reading: that would mean the rule as written is stricter than the precedent it cites, which is a finding to report, not a result to round off.
  - Observed evidence: `git diff -- .aw/system/workflows/verify-execution/intent-audit.md`:
    ```diff
    diff --git a/.aw/system/workflows/verify-execution/intent-audit.md b/.aw/system/workflows/verify-execution/intent-audit.md
    index bda17d5e4..d582c57f6 100644
    --- a/.aw/system/workflows/verify-execution/intent-audit.md
    +++ b/.aw/system/workflows/verify-execution/intent-audit.md
    @@ -36,9 +36,30 @@ passing example: `u23gbn` V-02, which reported the demand for `PHASE_COMMITTED_I
     unsatisfiable under the plan's ordering, pasted the ancestry result showing the commit is not
     reachable from the branch (`is the abandoned commit an ancestor of HEAD: False`, beside
     `classification: refused-would-overwrite`, `git rc: 1`, and `HEAD unmoved: True`), and evidenced the
    -real post-commit incomplete case from E-07. Even when the requirement is rated `done` under this bar,
    -an unsatisfiable demand is a plan defect: the auditor must still report the contradiction as a
    -finding (requiring the corrective IPD route rather than an in-place edit to an executed plan).
    +real post-commit incomplete case from E-07.
    +
    +The **tabulation substitution** is a named instance of this three-part bar. When an approved plan's
    +demand named a test function or asserted a collected count that has since been tabulated into a
    +table-driven suite, the evidence satisfies the bar by meeting three concrete obligations:
    +(a) show the named function is gone and name the commit that removed it;
    +(b) name the successor row by its case string and the table constant and class that hold it; and
    +(c) paste that row's individual verdict rather than the enclosing function's.
    +The row-verdict obligation is stated in terms of soundness, not of a specific command: the pasted
    +per-row verdict MUST be produced by a mechanism whose failure is observable for that row, and the
    +auditor MUST reject a per-row PASS that co-occurs with an enclosing failure (the observable signature
    +of an unsound driver that appends failures after a loop rather than failing in context). Until child
    +plan `t5txjk` (`nos070-02`) ships a sound driver, an honest executor may instead paste the enclosing
    +table's verdict plus the row's inputs and expected value and state that is what was done.
    +Calibrated passing example for the tabulation case: `i4c0c3` V-03/V-04, which records this exact
    +substitution discipline (proving the functions were removed by commit `75b90271`, naming successor
    +rows across `PreCommitExecutedGateTests.SITUATIONS` and `MergeAwareInTreeEvidenceTests.MERGE_DECISIONS`,
    +and verifying row counts). Note: `i4c0c3` is cited for its substitution discipline; its per-row
    +`[PASS]` verdict lines are explicitly NOT a model to copy because its driver shape cannot report a
    +per-row failure in that table's idiom (`t5txjk` owns shipping a sound driver).
    +
    +Even when the requirement is rated `done` under this bar, an unsatisfiable demand is a plan defect:
    +the auditor must still report the contradiction as a finding (requiring the corrective IPD route
    +rather than an in-place edit to an executed plan).

     ## Dimension 2: Implicit Intent & Spirit Audit
    ```

    Proof the extension is an extension and not a replacement:
    - Surviving three-part bar:
      "An item whose evidence reports the demand itself as unsatisfiable is classified `done` only if the evidence satisfies a three-part bar: it states why the demand cannot be met, proves the impossibility with an empirical measurement rather than an argument from prose, and evidences the satisfiable counterpart that does exist. Absent any of the three, the requirement is not satisfied; a bare assertion of impossibility without a measurement is rejected as an unsupported excuse."
    - Surviving `u23gbn` example:
      "Calibrated passing example: `u23gbn` V-02, which reported the demand for `PHASE_COMMITTED_INCOMPLETE` as unsatisfiable under the plan's ordering, pasted the ancestry result showing the commit is not reachable from the branch (`is the abandoned commit an ancestor of HEAD: False`, beside `classification: refused-would-overwrite`, `git rc: 1`, and `HEAD unmoved: True`), and evidenced the real post-commit incomplete case from E-07."
    - Surviving plan defect rule:
      "Even when the requirement is rated `done` under this bar, an unsatisfiable demand is a plan defect: the auditor must still report the contradiction as a finding (requiring the corrective IPD route rather than an in-place edit to an executed plan)."

    Calibration walk of `i4c0c3` V-03 evidence against the three obligations:
    (a) Show the named function is gone and name the commit that removed it:
    Satisfied by: "THE TWO NAMED TESTS NO LONGER EXIST AS FUNCTIONS, and the substance they pinned does. Commit `75b90271` ("test: tabulate eleven more suites (385 -> 160 tests)") landed AFTER this plan's review and converted both into ROWS of the two decision tables; see DECISION 03-i4c0c3-D2."
    (b) Name the successor row by its case string and the table constant and class that hold it:
    Satisfied by: "Their successors are the row `"a hand-edited `- Status: executed` in place, no journal"` (`PreCommitExecutedGateTests.SITUATIONS`, asserting `REASON_STATUS_FLIP` and forbidding the merge wording) and the row `"a hand-edited status flip OUTSIDE any merge"` (`MergeAwareInTreeEvidenceTests.MERGE_DECISIONS`)."
    (c) Paste that row's individual verdict rather than the enclosing function's:
    Satisfied by:
    ```text
    === MergeAwareInTreeEvidenceTests.MERGE_DECISIONS (`check` given merge state)
      [PASS] a hand-edited status flip OUTSIDE any merge
               want_rc=1 got_rc=1 missing=[] leaked=[]
      [PASS] a `git mv` into executed/ OUTSIDE any merge
               want_rc=1 got_rc=1 missing=[] leaked=[]
    ```
    All three obligations are satisfied by `i4c0c3` V-03 evidence.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` showing the amended Section 5.4. Confirm the section's five existing acceptable-evidence forms and its closing linter-boundary sentence are intact (paste them), since an amendment that quietly drops the boundary would license the lint rule this plan deferred. Paste the run-end spec-edit reconciliation (or, if executed by hand, `git status --short` plus the `- Scope-Paths:` line) showing this spec edit was DECLARED and not an undeclared spec change.
  - Observed evidence: `git diff -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    index f84a7bd08..31b9a46b8 100644
    --- a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    +++ b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    @@ -286,6 +286,8 @@ The execution and validation states MUST also agree:
     - a generated artifact with an independently inspectable path or identifier;
     - a documented human observation when tool capture is impossible.

    +`Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour (evidence durability). In particular, a collected test count and a test function name are not durable, because both are artifacts of test organization rather than stable authored facts; the demand must instead specify the behaviour pinned plus the mechanism that pins it. When the named mechanism has been reorganized (such as into a table-driven suite), the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. This durability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence durability.
    +
     `Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator.

     The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.
    ```

    Five existing acceptable-evidence forms intact:
    "- a diff or repository location showing the intended change;
    - a tool-captured command, arguments, exit status, and retained output artifact;
    - a test report or structured result file;
    - a generated artifact with an independently inspectable path or identifier;
    - a documented human observation when tool capture is impossible."

    Closing linter-boundary sentence intact:
    "The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient."

    Spec edit declaration check:
    `git status --short`:
    `M .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`
    Plan `- Scope-Paths:` line:
    `- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/verify-execution/intent-audit.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_v_item_evidence_durability.py`
    The spec path is explicitly declared in `- Scope-Paths:`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test module's passing run (`python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`) with its summary line, and paste the module DOCSTRING showing the P16 justification is recorded rather than implied. Then PROVE THE PRESENCE-AND-NARROWING TEST CAN FAIL, by mutation applied to the SOURCE FILE and not to a module attribute: re-widen the exemption in `.aw/system/workflows/plan-review/plan-review.md` (restore the words a collected test count is exempt), paste the test FAILING with a message naming that file, restore it, and paste `git diff --stat .aw/system/workflows/plan-review/plan-review.md` showing an EMPTY diff against the pre-mutation state so the temporary edit was not left behind. A green run with no mutation proof FAILS this item: it would only show that the test reads the file just edited.
  - Observed evidence: Passing test module run:
    ```text
    $ python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=3366314743
    rootdir: <repo>/.aw/worktrees/vtup6x
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability PASSED [ 50%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity PASSED [100%]

    ============================== 2 passed in 0.08s ===============================
    ```

    Module docstring with P16 justification:
    ```python
    """Tests for V-item evidence durability and parity rules (IPD vtup6x, set nos070).

    Exemption from source-text-pin prohibition:
    This test is explicitly outside the source-text-pin prohibition, verified at review
    (PR-004) rather than assumed, because plan 96xtmi (srcguard-01) deleted text-pinning
    tests under the maintainer's 2026-09-26 ruling and that plan's scope excluded "tests that
    read NON-production files (specs, workflow bodies, READMEs, the test module's own file)
    unless the census flags them as reading agent_workflows/*". A workflow body is a WORKFLOW
    BODY, the artifact under change, and this test reads no agent_workflows/* source, so it
    sits inside GUIDING_PRINCIPLES P16's stated narrow exception ("Content verification is
    permissible only where the text or file itself is the artifact under test") and outside its
    "No production source inspection" prohibition (whose enumerated targets are all
    agent_workflows/*.py). Follows the precedent of tests/test_plan_review_feasibility_rule.py.
    """
    ```

    Mutation proof (restoring "a collected test count is exempt" to `.aw/system/workflows/plan-review/plan-review.md`):
    ```text
    $ python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2241777768
    rootdir: <repo>/.aw/worktrees/vtup6x
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity PASSED [ 50%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability FAILED [100%]

    =================================== FAILURES ===================================
    _ TestVItemEvidenceDurability.test_single_file_plan_review_evidence_durability _
    ...
    >       self.assertNotIn(
                "collected test count is exempt",
                bullet_text.lower(),
                f"Exemption re-widened in {PLAN_REVIEW_REL}: a collected test count must not be exempt",
            )
    E       AssertionError: 'collected test count is exempt' unexpectedly found in "...": Exemption re-widened in .aw/system/workflows/plan-review/plan-review.md: a collected test count must not be exempt
    =========================== short test summary info ============================
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability
    ========================= 1 failed, 1 passed in 0.11s ==========================
    ```

    Restored pre-mutation state verified:
    `git diff --stat .aw/system/workflows/plan-review/plan-review.md` against pre-mutation state shows an empty diff (reverted cleanly).
    Tests passing again after restore:
    `2 passed in 0.09s`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the parity test's passing run. Then PROVE IT PINS PARITY by mutating the LONG-FORM source file: delete the pointer bullet from `.aw/system/workflows/plan-review-long/review-rubric.md`, paste the test FAILING with the message naming that file, restore it, and paste `git diff --stat` for that path showing an EMPTY diff. ALSO paste the test source for this case and confirm by quoting that it asserts the POINTER trio (summary anchor, `../plan-review/plan-review.md`, ``per the parity note in `plan-review-long.md` ``) and does NOT assert the two bodies hold identical paragraph text, since after E-02 they deliberately do not (F-11).
  - Observed evidence: Parity test passing run:
    ```text
    $ python3 -m pytest tests/test_v_item_evidence_durability.py -k test_long_form_plan_review_evidence_durability_parity -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=1400290639
    rootdir: <repo>/.aw/worktrees/vtup6x
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items / 1 deselected / 1 selected

    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity PASSED [100%]

    ======================= 1 passed, 1 deselected in 0.15s ========================
    ```

    Mutation proof (deleting pointer bullet from `.aw/system/workflows/plan-review-long/review-rubric.md`):
    ```text
    $ python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts="" -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2944993007
    rootdir: <repo>/.aw/worktrees/vtup6x
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity FAILED [ 50%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability PASSED [100%]

    =================================== FAILURES ===================================
    _ TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity _
    ...
    >       self.assertNotEqual(
                bullet_idx,
                -1,
                f"Missing pointer bullet '{bullet_prefix}' in {REVIEW_RUBRIC_REL}",
            )
    E       AssertionError: -1 == -1 : Missing pointer bullet '- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**' in .aw/system/workflows/plan-review-long/review-rubric.md
    =========================== short test summary info ============================
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity
    ========================= 1 failed, 1 passed in 0.19s ==========================
    ```

    Restored pre-mutation state verified:
    `git diff --stat` for `.aw/system/workflows/plan-review-long/review-rubric.md` against pre-mutation state shows an empty diff (reverted cleanly).
    Tests passing again after restore:
    `2 passed in 0.15s`

    Test source asserting the POINTER trio without paragraph equality:
    ```python
    # Pointer anchors for the long-form parity rule:
    LONG_FORM_POINTER_ANCHORS = [
        "Live-artifact success criteria vs. stable code facts (re-derivation convention):",
        "behaviour pinned plus the mechanism that pins it",
        "collected test count is never the bar",
        "../plan-review/plan-review.md",
        "per the parity note in `plan-review-long.md`",
    ]
    ...
        # Assert pointer trio and summary anchors are present in the long-form bullet
        for anchor in LONG_FORM_POINTER_ANCHORS:
            self.assertIn(
                anchor,
                bullet_text,
                f"Anchor '{anchor}' not found in pointer bullet of {REVIEW_RUBRIC_REL}",
            )

        # Confirm the long-form does NOT duplicate the full paragraph (remains a pointer)
        self.assertNotIn(
            "Criteria counting **stable code facts**",
            bullet_text,
            f"{REVIEW_RUBRIC_REL} must not duplicate the full normative paragraph from plan-review.md",
        )
    ```
    The test source asserts the pointer trio (`../plan-review/plan-review.md`, ``per the parity note in `plan-review-long.md` ``, summary anchor) and explicitly confirms non-duplication (`self.assertNotIn("Criteria counting **stable code facts**", bullet_text)`).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a bare `python3 -m pytest` summary line together with a bare run taken immediately before this plan's first edit IN THIS SAME LANE, and account for any difference as a delta of failing node ids rather than as two totals; do not compare against any count written in this plan (the review-measured `3246 passed, 2 skipped` at HEAD `650f6772` is DATED CONTEXT, not the bar). Paste `python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_installer.py` passing, since those exercise the two workflow bodies this plan edits and the installer that ships them. Evidence the managed-block claim in Spec sync by a SEARCH rather than by assertion: paste a grep for the amended anchor over `agent_workflows/engine.py` showing rubric G is not restated in a managed block, or, if it IS, report that as a finding and update the plan's scope instead of editing one surface and leaving the other stale. FINALLY paste the DOGFOOD CHECK: read this plan's own V-01 through V-07 against the amended rubric G and state, per item, that it demands neither a collected test count nor the presence of a named test function as its bar. A plan that fixes this rule while violating it is not executed correctly.
  - Observed evidence: Bare pytest suite comparison:
    - Pre-edit baseline run in this same lane:
      `4201 passed, 2 skipped, 3 warnings in 245.24s (0:04:05)`
    - Post-change bare run in this same lane:
      `4203 passed, 2 skipped, 3 warnings in 289.02s (0:04:49)`
    - Delta of failing node ids: 0 (empty delta; zero failures before and zero failures after; exactly +2 tests passed from `tests/test_v_item_evidence_durability.py`).

    Named test files passing:
    ```text
    $ python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_installer.py
    4 passed in 3.99s
    ```

    Managed-block claim verified by search:
    ```sh
    $ grep -E 'rubric G|Live-artifact|re-derivation' agent_workflows/engine.py
    # (exit code 1, 0 matches)
    ```
    Rubric G is not restated in any managed block in `agent_workflows/engine.py`.

    Dogfood check on this plan's own V-items (V-01 through V-07) against amended rubric G:
    - V-01: Demands diff showing amended bullet, answers to three questions, and surviving exemptions verified. Bar is semantic demonstration; demands no collected test count and no named test function as bar.
    - V-02: Demands diff showing pointer bullet, parity text comparison, and measurement of pre-edit absence. Bar is diff and comparison; demands no collected test count and no named test function as bar.
    - V-03: Demands diff showing extension, proof of 3 surviving elements, and calibration walk of i4c0c3 against 3 obligations. Bar is diff and precedent walk; demands no collected test count and no named test function as bar.
    - V-04: Demands diff of spec Section 5.4, verification of 5 forms and linter boundary, and scope path declaration check. Bar is diff and contract verification; demands no collected test count and no named test function as bar.
    - V-05: Demands running test module `tests/test_v_item_evidence_durability.py`, module docstring verification, and source-file mutation proof with empty-diff restore. Running test file is a mechanism; bar is falsifiable mutation failure and passing restore, not a collected count or function name as contract.
    - V-06: Demands running parity test, source-file mutation proof with empty-diff restore, and quoting pointer trio assertions. Running test is a mechanism; bar is falsifiable mutation failure, not a count or function name as contract.
    - V-07: Demands bare pytest comparison against baseline, running two named test files, grep search over `agent_workflows/engine.py`, and dogfood check. Running test suite is a mechanism; bar is zero delta of failing node ids and clean grep search, not a count or function name as contract.
    Every V-item complies with the amended rule.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It must not be executed until `/plan-review` has run and a human has approved it (`aw ipd set approved <id6> --by-human`). The executor must not self-approve, and must not write the `- Readiness:` field, which is an output of review and not of authoring or execution.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. Four prose amendments and one new test module (two test cases). The operative change is one clause: rubric G today declares criteria counting `test assertions` EXEMPT from its re-derivation requirement, and that exemption is what licensed the evidence demand which later became unsatisfiable. After this plan, a V-item must demand the behaviour pinned plus the mechanism that pins it, a test NAME is allowed only as a non-binding pointer, and a collected COUNT is not allowed as the bar at all. The second change tells an executor what to do when the pointer has died, hung on the unsatisfiable-demand bar that already exists in `verify-execution`. No production Python changes, no lint rule is added, and no existing plan is edited.

WHAT REVIEW CHANGED, because it alters what an executor builds. All ten authored findings were independently re-measured and ALL REPRODUCE, including F-06's empirical falsification (corrupting one `MERGE_DECISIONS` row makes the suite report `FAILED (failures=1)` while an `addSubTest` driver prints PASS for all seven rows including the corrupted one) and F-07's census (exactly 4 such blocks, all in one file, out of 266 subTest blocks measured across `tests/`). Two things were wrong. FIRST, E-02 told the executor to DUPLICATE the amended paragraph into the long-form variant, while the repository's parity mechanism for these two files is a test-enforced POINTER; duplication would leave two normative copies that nothing diffs, which is this plan's own target defect one layer up (F-11, OQ-03). SECOND, the calibrated example the plan tells auditors to follow pastes per-row `[PASS]` lines from exactly the driver shape F-06 falsifies, so E-03 must now cite it for its substitution discipline while warning that its verdict lines are not a model to copy (F-12). Also added: an E-item owning the dogfood check that previously existed only as prose (F-13), and a split of E-05's two independent test surfaces (F-14).

WHY THIS IS CONVENTION AND NOT CODE, since that is the obvious objection. The repository has already decided this class of judgement is the reviewer's: spec Section 5.4 forbids the linter from judging evidence sufficiency, Section 10.1 repeats it, and rubric G's own text refuses the mechanical route for the neighbouring case because it `requires semantic reading`. A lint rule here would contradict an implemented spec. That is recorded as a deferral with its axis, not omitted.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Five paths, all in `- Scope-Paths:`: the two plan-review variants, `verify-execution/intent-audit.md`, the `ipd-structure-and-linting` spec, and the new `tests/test_v_item_evidence_durability.py`. FOUR NEGATIVE CONSTRAINTS CARRY WEIGHT. ZEROTH AND MOST IMPORTANT AFTER REVIEW: do NOT duplicate the amended rule's full text into `review-rubric.md` (F-11); write the pointer bullet E-02 specifies. THEN: FIRST, do NOT add a lint rule and do NOT touch `agent_workflows/ipd_lint.py` or `agent_workflows/ipd_schema.py`; the deferral above is a decision, not an oversight, and `IPD-S402`/`IPD-S404` deliberately test only that evidence is non-empty. SECOND, do NOT edit `.aw/system/workflows/assess/templates/ipd.md` or `agent_workflows/ipd_authoring.py`: the `Required evidence: TODO falsifiable evidence.` string is a tracked placeholder marker (`I-12`) and changing it can break placeholder detection; OQ-01 settled this. THIRD, do NOT edit any plan under `.aw/records/plans/executed/`, i4c0c3 included: it is cited as evidence and its record must not be rewritten.

A SPEC EDIT IS DECLARED. `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` is amended by E-04 and is declared in `- Scope-Paths:`, so both runners announce it before the run and reconcile it at run end. The reason is in Spec sync: Section 5.4 is the single definition of what `Required evidence:` must be, so the durability property belongs there and nowhere else.

EXECUTION CONTRACT. Commit only the five declared paths plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and do not push. Paste ACTUAL runner output for every test claim. The mutation proof in V-05 edits a SHARED-CHECKOUT file, so restore it by reverting your own edit and prove the restore with an empty diff rather than a broad `git checkout` that could discard a co-worker's concurrent work.

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the runner performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/`.

HOW THIS PLAN CAN FAIL SILENTLY, stated for the executor, and REVISED AT REVIEW because the authored answer named the wrong hazard. The obvious risk is amending the single-file body and forgetting the long-form one, which E-06's parity test now catches. THE SUBTLER AND MORE LIKELY FAILURE IS DUPLICATING THE RULE INTO BOTH FILES (F-11): that passes a naive parity check, looks complete, and leaves two normative copies that nothing in the toolchain will ever diff for semantic equivalence. That is this plan's own target defect reproduced one layer up, so E-02 forbids it, OQ-03 records why, and V-06 requires confirming the test does NOT assert paragraph equality. A green new test that only reads the file you just edited proves nothing; the two SOURCE-FILE mutation proofs in V-05 and V-06 are the evidence that matters.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND all SEVEN `V-*` items carry pasted evidence with `Result: pass`, including V-05's and V-06's source-file mutation proofs each with an empty-diff restore, and V-07's dogfood check. On completion the runner sets backlog `nos070` to `graduated`. The item carries no `- Blocks-Release:` gate, so this plan correctly declares none.
