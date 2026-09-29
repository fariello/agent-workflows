# IPD: Make V-item test evidence survive test reorganization: demand behaviour plus mechanism, and define the row substitution rule

- Date: 2026-09-29
- Kind: child
- Concern: An approved plan's `Required evidence:` can become literally unsatisfiable between review and execution when a suite is tabulated, because the demand names a test FUNCTION or asserts a COLLECTED COUNT rather than the behaviour pinned and the mechanism that pins it.
- Scope: Two workflow bodies (`plan-review` single-file and the long-form `review-rubric`), the `verify-execution` intent audit, and the `ipd-structure-and-linting` spec's evidence section. Prose conventions only; no production Python and no lint rule.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/review-rubric.md, .aw/system/workflows/verify-execution/intent-audit.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_v_item_evidence_durability.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: nos070
- Set: nos070
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vtup6x

## Workflow history

- 2026-09-29 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored in full from backlog `nos070`; ready for `/plan-review`.

## Goal

Close the convention gap at the seam between two good practices: an IPD authored with a named-test or collected-count evidence demand, and a later commit that tabulates that suite. Make the AUTHORING rule state what a V-item must demand (the behaviour pinned plus the mechanism that pins it, re-derived at execution time), and make the SUBSTITUTION rule state what an executor does when the pointer it was given no longer exists, so the honest path is written down instead of improvised per plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: correct the authoring rule that currently blesses the broken demand

- [ ] E-01 In `.aw/system/workflows/plan-review/plan-review.md`, amend rubric G's re-derivation convention bullet (the bullet beginning `**Live-artifact success criteria vs. stable code facts (re-derivation convention):**`) so that a COLLECTED TEST COUNT and a TEST FUNCTION NAME are no longer covered by its EXEMPT clause. The bullet today exempts criteria counting `stable code facts (test assertions, schema keys, enum members)`; that exemption is what licensed i4c0c3's V-04 count demand. Replace the `test assertions` element of the exempt list with an explicit statement that a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts, so a V-item must demand the BEHAVIOUR pinned plus the MECHANISM that pins it, and must require re-derivation at execution time. Keep the rest of the bullet (live-artifact counts, the orchestrator-children exemption, the "review is the only enforcement surface" note) intact: schema keys and enum members remain genuinely stable and stay exempt.
  - Depends on: none
  - Expected outcome: the bullet no longer exempts a test count or a test name, states the behaviour-plus-mechanism demand, and permits a test name only as a NON-BINDING pointer. `grep -n 'test assertions' .aw/system/workflows/plan-review/plan-review.md` returns no line inside that bullet.
  - Execution state: pending

- [ ] E-02 Carry the SAME rule into the long-form variant at `.aw/system/workflows/plan-review-long/review-rubric.md`, whose section `## A. Plan completeness` holds the long-form twin of rubric G (it already carries the verbatim `Right-sizing and conceptual density (per E-item)` bullet and the `Maintainer sizing signals` bullet, and the file's own `SCOPE-FENCE WORDING` note declares these two variants are `kept in deliberate parity`). The re-derivation bullet is PRESENTLY ABSENT from the long-form copy (`grep -rln 'Live-artifact' .aw/system/workflows/` matches only the single-file `plan-review/plan-review.md`), so this item adds the amended bullet there rather than editing one in place, closing a pre-existing parity hole in the same pass.
  - Depends on: E-01
  - Expected outcome: `.aw/system/workflows/plan-review-long/review-rubric.md` carries a re-derivation bullet whose test-evidence rule is substantively the same as E-01's, placed beside the existing right-sizing bullets in `## A. Plan completeness`. Both files then answer "may a V-item demand a collected count?" the same way.
  - Execution state: pending

### Task group 2: write down what an executor does when the pointer has died

- [ ] E-03 In `.aw/system/workflows/verify-execution/intent-audit.md`, extend the existing unsatisfiable-demand paragraph (the one beginning `An item whose evidence reports the demand itself as unsatisfiable is classified` `done` `only if the evidence satisfies a three-part bar`) with the TABULATION SUBSTITUTION case as a named instance of that bar. State the three obligations concretely for this case: (a) show the named function is gone and name the commit that removed it, (b) name the SUCCESSOR ROW by its case string and the table constant and class that hold it, and (c) paste that row's individual verdict rather than the enclosing function's. Keep the paragraph's closing rule that an unsatisfiable demand remains a plan DEFECT to report as a finding, and keep the existing `u23gbn` calibrated example. Add `i4c0c3` V-03/V-04 as the calibrated passing example for the tabulation case, since its observed-evidence blocks already record exactly this substitution.
  - Depends on: E-01
  - Expected outcome: the intent audit tells an auditor how to grade a tabulation substitution instead of leaving it to judgement, and cites a real in-repo example of a substitution that met the bar.
  - Execution state: pending

- [ ] E-04 Amend Section 5.4 (`### 5.4 Evidence requirements`) of the spec `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` to record the DURABILITY property of an authored evidence demand: `Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour. Add the test-organization case explicitly (a collected count and a test function name are not durable; the behaviour plus the mechanism that pins it is), and add one sentence stating that when the named mechanism has been reorganized the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. State plainly, in the same place, that this is a CONVENTION the linter does not and will not check, consistent with the section's existing closing sentence that the linter `checks presence and state consistency` and `MUST NOT claim that evidence is authentic, relevant, or sufficient`.
  - Depends on: E-01
  - Expected outcome: the spec section that defines what `Required evidence:` must be now also says it must be durable, with the test-count and test-name cases named, and with the linter boundary restated so no reader expects mechanical enforcement.
  - Execution state: pending

### Task group 3: pin the convention so it cannot silently revert

- [ ] E-05 Add `tests/test_v_item_evidence_durability.py` asserting the BEHAVIOUR of the shipped workflow and spec ARTIFACTS this plan changes: that the single-file and long-form plan-review bodies agree on the test-evidence rule (parity, the property E-02 establishes), and that the rule is present and not exempting a collected test count. This test reads WORKFLOW BODIES and a SPEC, never `agent_workflows/*.py`, so it sits inside GUIDING_PRINCIPLES P16's stated narrow exception (`Content verification is permissible only where the text or file itself is the artifact under test`) and outside its `No production source inspection` prohibition. Follow the precedent and the justification shape of `tests/test_plan_review_feasibility_rule.py`, which pins anchor phrases in these same two workflow bodies and carries an explicit module docstring recording why it is exempt; write the equivalent docstring here. Assert on a SMALL number of distinctive semantic anchors, not on whole paragraphs, so wording may be improved without breaking the test.
  - Depends on: E-01, E-02, E-04
  - Expected outcome: a new test module that fails if either plan-review variant loses the rule or if the two variants drift apart, and passes on the amended tree.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. Amend rubric G's re-derivation bullet in the single-file `plan-review` so a collected test count and a test function name are no longer exempt, and state the behaviour-plus-mechanism demand (E-01).
2. Add the amended rule to the long-form `review-rubric`, closing the parity hole F-03 records (E-02).
3. Extend the existing unsatisfiable-demand bar in `verify-execution/intent-audit.md` with the tabulation substitution case and the `i4c0c3` calibrated example (E-03).
4. Record the durability property of `Required evidence:` in spec Section 5.4, restating the linter boundary (E-04).
5. Add `tests/test_v_item_evidence_durability.py` pinning the rule's presence and the two variants' parity (E-05).

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

- `python3 -m pytest tests/test_v_item_evidence_durability.py` for the new pin, plus its MUTATION proof (remove the rule from one variant, see the test go red, restore, see it green).
- `python3 -m pytest tests/test_plan_review_feasibility_rule.py tests/test_installer.py` because those exercise the two workflow bodies this plan edits and the installer that ships them.
- A bare `python3 -m pytest` for the whole suite, compared against a bare run taken IMMEDIATELY BEFORE the change in this same lane. Do NOT compare against any number written in this plan: per the repository's own measured guidance, a plan-recorded figure cannot distinguish an added test from a merge landing on main.
- A DOGFOOD CHECK, which is the real acceptance test of this plan: read this plan's own V-items against the amended rubric G and confirm none of them demands a collected test count or binds to a test function name. A plan that fixes this rule while violating it is not executed correctly.

## Spec / documentation sync

- `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Section 5.4 is AMENDED by E-04, and is declared in `- Scope-Paths:` so both runners announce the spec edit before the run and reconcile it afterwards. WHY the amendment belongs in this change: Section 5.4 is the single definition of what `Required evidence:` must be, and the durability property is a property OF that definition. Leaving it out would put the operative rule in a workflow body while the spec that governs the field stayed silent, which is the drift this repository's single-source-of-truth principle exists to prevent, and would leave the next author reading the spec with no reason not to write the demand that broke.
- The spec's `- Status:` is `implemented`. E-04 changes the contract it states, not the record of whether it was built, so the status is left alone; the amendment is additive and no implemented behaviour is retracted. The spec carries no `- Id:` bullet (it is a legacy pre-cutover name), so it is cited here by path and section.
- `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/review-rubric.md` and `.aw/system/workflows/verify-execution/intent-audit.md` are workflow bodies shipped by the installer; no generated or managed block in `agent_workflows/engine.py` restates rubric G, so no managed-block regeneration is required. The executor MUST confirm this rather than assume it (V-05).

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

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review/plan-review.md` showing the amended bullet in full. Then demonstrate the BEHAVIOUR CHANGE rather than asserting it, by answering three questions against the amended text and pasting the answering sentence for each: (a) may a V-item's bar be a collected test count? (b) may it be the presence of a named test function? (c) what must it be instead? The amended bullet must answer no, no, and behaviour-plus-mechanism-re-derived-at-execution. Also paste the result of re-reading the bullet's SURVIVING exemptions and confirm `schema keys` and `enum members` and the orchestrator-children clause are still exempt and the live-artifact requirement is unchanged, since narrowing an exemption must not silently delete the rest of the rule.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md`. Then prove PARITY by extracting the test-evidence rule from BOTH files and pasting them adjacently for comparison, so a reader can see the two variants now answer V-01's three questions identically. Confirm by measurement that the bullet was ABSENT before this change (paste `git show HEAD:.aw/system/workflows/plan-review-long/review-rubric.md | grep -c 'Live-artifact'` or the equivalent for the amended anchor, expecting `0`), which is what makes this an added bullet rather than an edited one and confirms F-03 was a real hole rather than a misread.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff -- .aw/system/workflows/verify-execution/intent-audit.md`. Prove the extension is an EXTENSION and not a replacement: paste the surviving three-part bar, the surviving `u23gbn` example, and the surviving rule that an unsatisfiable demand is still a reportable plan defect. Then APPLY the new text to the real historical case as a calibration check: walk i4c0c3's V-03 evidence against the three obligations E-03 states and paste, for each, the sentence in that evidence which satisfies it. If any of the three is NOT satisfied by i4c0c3's evidence, say so plainly rather than stretching the reading: that would mean the rule as written is stricter than the precedent it cites, which is a finding to report, not a result to round off.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` showing the amended Section 5.4. Confirm the section's five existing acceptable-evidence forms and its closing linter-boundary sentence are intact (paste them), since an amendment that quietly drops the boundary would license the lint rule this plan deferred. Paste the run-end spec-edit reconciliation (or, if executed by hand, `git status --short` plus the `- Scope-Paths:` line) showing this spec edit was DECLARED and not an undeclared spec change.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test module's passing run (`python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`) with its summary line. Then PROVE IT CAN FAIL, by mutation applied to the SOURCE FILE and not to a module attribute: delete the amended rule from `.aw/system/workflows/plan-review-long/review-rubric.md`, paste the test FAILING with the message naming that file, restore it, and paste `git diff --stat .aw/system/workflows/plan-review-long/review-rubric.md` against the pre-mutation state showing an EMPTY diff so the temporary deletion was not left behind. Separately paste a bare `python3 -m pytest` summary line together with a bare run taken immediately before this plan's first edit in this same lane, and account for the difference; do not compare against any count written in this plan. Finally, evidence the managed-block claim in Spec sync by a search rather than by assertion: paste a grep for the amended anchor over `agent_workflows/engine.py` showing rubric G is not restated in a managed block, or, if it IS, report that as a finding and update the plan's scope instead of editing one surface and leaving the other stale.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It must not be executed until `/plan-review` has run and a human has approved it (`aw ipd set approved <id6> --by-human`). The executor must not self-approve, and must not write the `- Readiness:` field, which is an output of review and not of authoring or execution.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. Four prose amendments and one new test. The operative change is one clause: rubric G today declares criteria counting `test assertions` EXEMPT from its re-derivation requirement, and that exemption is what licensed the evidence demand which later became unsatisfiable. After this plan, a V-item must demand the behaviour pinned plus the mechanism that pins it, a test NAME is allowed only as a non-binding pointer, and a collected COUNT is not allowed as the bar at all. The second change tells an executor what to do when the pointer has died, hung on the unsatisfiable-demand bar that already exists in `verify-execution`. No production Python changes, no lint rule is added, and no existing plan is edited.

WHY THIS IS CONVENTION AND NOT CODE, since that is the obvious objection. The repository has already decided this class of judgement is the reviewer's: spec Section 5.4 forbids the linter from judging evidence sufficiency, Section 10.1 repeats it, and rubric G's own text refuses the mechanical route for the neighbouring case because it `requires semantic reading`. A lint rule here would contradict an implemented spec. That is recorded as a deferral with its axis, not omitted.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Five paths, all in `- Scope-Paths:`: the two plan-review variants, `verify-execution/intent-audit.md`, the `ipd-structure-and-linting` spec, and the new `tests/test_v_item_evidence_durability.py`. THREE NEGATIVE CONSTRAINTS CARRY WEIGHT. FIRST, do NOT add a lint rule and do NOT touch `agent_workflows/ipd_lint.py` or `agent_workflows/ipd_schema.py`; the deferral above is a decision, not an oversight, and `IPD-S402`/`IPD-S404` deliberately test only that evidence is non-empty. SECOND, do NOT edit `.aw/system/workflows/assess/templates/ipd.md` or `agent_workflows/ipd_authoring.py`: the `Required evidence: TODO falsifiable evidence.` string is a tracked placeholder marker (`I-12`) and changing it can break placeholder detection; OQ-01 settled this. THIRD, do NOT edit any plan under `.aw/records/plans/executed/`, i4c0c3 included: it is cited as evidence and its record must not be rewritten.

A SPEC EDIT IS DECLARED. `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` is amended by E-04 and is declared in `- Scope-Paths:`, so both runners announce it before the run and reconcile it at run end. The reason is in Spec sync: Section 5.4 is the single definition of what `Required evidence:` must be, so the durability property belongs there and nowhere else.

EXECUTION CONTRACT. Commit only the five declared paths plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and do not push. Paste ACTUAL runner output for every test claim. The mutation proof in V-05 edits a SHARED-CHECKOUT file, so restore it by reverting your own edit and prove the restore with an empty diff rather than a broad `git checkout` that could discard a co-worker's concurrent work.

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the runner performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/`.

HOW THIS PLAN CAN FAIL SILENTLY, stated for the executor. By amending the single-file `plan-review` and forgetting the long-form variant, or by amending them inconsistently. Nothing in the toolchain catches workflow-body drift today, which is exactly the hole F-03 measured and why E-05 exists and why V-05 demands a mutation proof rather than a green run. A green new test that only reads the file you just edited proves nothing about parity; V-02's side-by-side extraction is the evidence that matters.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND all five `V-*` items carry pasted evidence with `Result: pass`, including V-05's source-file mutation proof and empty-diff restore. On completion the runner sets backlog `nos070` to `graduated`. The item carries no `- Blocks-Release:` gate, so this plan correctly declares none.
