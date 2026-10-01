# IPD: Document the table-driven test convention as the measured house idiom, and state the accumulate-versus-subTest rule the way pytest actually behaves

- Date: 2026-10-01
- Kind: child
- Concern: The repository has converted at least 16 suites to TABLE-DRIVEN form with a genuinely consistent row shape, and the convention is written down NOWHERE. Measured at HEAD `dfee027e`: `rg -il 'tabulat|table-driven|subtest' GUIDING_PRINCIPLES.md CONTRIBUTING.md AGENTS.md ARCHITECTURE.md README.md DECISIONS.md docs/` exits 1 with no matches, so the only statement of the method is one commit message (`75b90271`, 2026-09-19) plus the idiom itself. A new author must infer the row shape by reading tests, and a reviewer has no cited rule to hold a new table to. The gap is not academic: the backlog item that asked for this doc proposed a subTest rule that this plan MEASURED TO BE BACKWARDS under the runner this repository actually uses, which is exactly the kind of error an undocumented convention invites.
- Scope: Prose only. Add one subsection to `GUIDING_PRINCIPLES.md` P16 stating the row shape, the case-first rule, the mandatory `why` column, when to tabulate and when NOT to, and the per-row-verdict rule stated by MEASURED pytest behaviour; add a one-line pointer from `CONTRIBUTING.md`'s authoring-conventions list; and add one guard test asserting the documented anchors survive, following the shipped `tests/test_plan_review_feasibility_rule.py` precedent. EXCLUDES changing any table, any test idiom, or any production code, and EXCLUDES building the row-verdict driver (that is pending plan `t5txjk`, whose readiness is `no-go` on an open blocking question).
- Scope-Paths: GUIDING_PRINCIPLES.md, CONTRIBUTING.md, tests/test_tabulated_test_convention.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: 7fzqop
- Set: 7fzqop
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: prj0vm

## Workflow history

- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored in full from backlog `7fzqop`; every claim re-measured at HEAD `dfee027e`; ready for `/plan-review`.

## Goal

Write down the table-driven test convention that already exists in this repository's suites, so a new author can follow it without reverse-engineering it from 16 files and a reviewer can cite it. State it as it is MEASURED to be, which means correcting one claim the backlog item makes: the house idiom is accumulate-then-assert (139 occurrences), not `subTest` (30), and under this repository's real runner a bare in-context failure DESTROYS the aggregate diagnostic the convention's failure messages exist to deliver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the convention in its canonical home

- [ ] E-01 In `GUIDING_PRINCIPLES.md`, add a new `###` subsection to principle 16 (`## 16. Test outcomes and behavior, never code structure or text`), placed AFTER the existing `### When tests depend on the live checkout or environment:` subsection so it is the last subsection of P16. Title it so it is greppable for the three terms measured absent today (`tabulated`, `table-driven`, `subTest`). It must state, as bullets:

  **THE ROW SHAPE.** A module- or class-level table of tuples, with the CASE STRING FIRST as a human-readable prose id, and a trailing `why` column. Cite the canonical in-repo statement of the shape, which is already written as a comment on `test_ipd_lint.py`'s `RULES` table: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`. State the middle columns as what they are, VARIABLE per table (inputs, expected value, required `needles`, `forbidden` substrings), and do NOT prescribe a fixed arity: measured, the `needles`/`forbidden` pair appears in 7 files and is a common shape, not a universal one.

  **THE CASE-FIRST RULE, STATED AS IT IS ACTUALLY FOLLOWED.** The first column is the row's human-readable identity, and `case` is the usual name (72 of 102 measured `why`-terminated loops bind it as `case`). The remaining 30 bind a more specific name (`kind`, `name`, `text`, `lane`, `record_class`, `shell`, `verb`, `describe`) and that is CONFORMING, not a deviation: the rule is that the first column IDENTIFIES the row in the failure message, not that it is spelled `case`. Writing the rule as "must be named `case`" would mis-state the repository against itself and condemn 30 existing loops.

  **THE `why` COLUMN IS NOT OPTIONAL, AND SAY WHAT IT BUYS.** Every row carries the rule it encodes, and the failure message quotes it back as `this row exists because: <why>`. The reason it is mandatory is that tabulating DESTROYS the per-case test NAME that used to carry this information: a class per mode becomes a column, so the row's justification has nowhere else to live, and without it a failing row reports a data mismatch with no statement of which rule just broke. Measured: 99 of 131 table loops in these files terminate in `why`.

  **THE AGGREGATE FAILURE MESSAGE IS PART OF THE CONVENTION.** The table reports EVERY failing row at once, not just the first, via the accumulate idiom: collect each row's problems into a list and assert that list is empty at the end, with a message that states how many of how many rows were wrong and what their pattern MEANS. Cite `test_runner_profiles.ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`, whose aggregate message tells the reader to read the DIRECTION of the failures because over-reservation and under-reservation are different defects.
  - Depends on: none
  - Expected outcome: `rg -c 'tabulat|table-driven|subTest' GUIDING_PRINCIPLES.md` returns a nonzero count where it returns nothing today, and the subsection states the row shape, the case-first rule as an identity rule, the mandatory `why` column with its justification, and the all-rows-at-once aggregate message.
  - Execution state: pending

- [ ] E-02 In the SAME subsection added by E-01, state WHEN TO TABULATE and WHEN NOT TO, taking both halves from the recorded reasoning rather than inventing a rule.

  **WHEN IT IS RIGHT:** clusters of tests differing only in DATA. Quote the method from commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN". Name the columns that commit reports as carrying the value (host, lint phase, entry point, cutover marker, queue shape, git state, resolver), and cite the fuller in-repo statement in the `test_runner_profiles.py` module docstring, which names HOST, TIER and ROUTE as the three mode-columns and explains that a chain tested level by level cannot exhibit an INVERSION.

  **WHEN IT IS WRONG, which is the half a new author will get wrong.** State these as the recorded reasons a test was deliberately left un-merged: the property IS the sequence (`75b90271` records rollback ORDER, where recoverability is the reverse order and no single row can state it); idempotence PAIRS; multi-step consent transcripts; an ordering constraint between two phases; every `assertRaises`; a claim that is STRUCTURAL rather than behavioural; a subject that is TWO RESULTS COMPARED TO EACH OTHER rather than to an expectation; and a CONTRAST between outcomes, where the point is that two cases differ. The last four are lifted from the `test_runner_profiles.py` module docstring's own "TESTS THAT ARE NOT ROWS CARRY A ONE-LINE DOCSTRING SAYING WHY" list, so cite it and adopt its rule: a test that is not a row says why in one line.

  **TWO TRAPS MEASURED IN PRACTICE, both recorded in `75b90271` and worth one bullet each.** FIRST, a safety gate must keep every refusal INDIVIDUALLY detectable: pin the refusal CODE, not merely that it refused, or two distinct refusals collapse into "it refused". SECOND, do not reference a production CONSTANT in the expected column when the constant is the published interface under test: `test_ipd_lint.py`'s `RULES` comment records that constant-referencing rows stayed GREEN when two code definitions were swapped, because constant and reported value move together, and it forbids "tidying" the literals back. State that a three-valued column is sometimes required and must not be collapsed to a bool, citing the same commit's measured `None`-means-absent versus `False`-means-decided distinction.
  - Depends on: E-01
  - Expected outcome: the subsection answers "should I tabulate this?" in both directions with in-repo citations, and carries the individually-detectable-refusal rule and the literal-strings rule as named traps.
  - Execution state: pending

### Task group 2: state the per-row-verdict rule as pytest actually behaves

- [ ] E-03 In the same subsection, state the per-row-verdict rule. **THE BACKLOG ITEM'S FOURTH INSTRUCTION IS BACKWARDS FOR THIS REPOSITORY AND MUST NOT BE COPIED IN.** The item asks for "the rule that a row's failure must be raised INSIDE the subTest context or the row's per-row verdict is unobtainable". That is true of `unittest` and FALSE of the runner this repository runs, and writing it as an unconditional rule would instruct authors to delete the aggregate diagnostic E-01 just made mandatory. Re-measured for this plan at HEAD `dfee027e` with a two-class probe (an in-context `self.subTest` + `assertEqual` class and an accumulate class, each over a 3-row table with rows b and c failing):

  - under `python3 -m pytest` with `pytest-subtests` ABSENT (confirmed absent: `python3 -m pip show pytest-subtests` reports `Package(s) not found`), the in-context class reported ONLY row b, never reached the trailing aggregate assertion, and printed no aggregate marker; the accumulate class reported BOTH wrong rows with the full `this row exists because:` text for each.
  - under `python3 -m unittest` the in-context class reported row b AND row c as separate subtest failures and still ran the aggregate, finishing `FAILED (failures=3)`.

  So state the rule CONDITIONALLY and name the runner: in the default suite run, which is pytest, the ACCUMULATE idiom is what delivers every failing row plus its `why`, and a bare in-context failure costs you every row after the first plus the aggregate message. Say plainly that the per-row verdict an IPD's `V-*` evidence may ask for is therefore NOT obtainable from a default pytest run of an accumulate table, and that the honest paste is the enclosing test's verdict plus the row's inputs and expected value, SAID to be that. Point at pending plan `t5txjk` as the owner of a sound opt-in driver and `vtup6x` as the owner of the evidence-substitution rule, and state that until one ships, a per-row `PASS` list is not evidence. Do NOT document `t5txjk`'s opt-in strict mode as though it exists: its `Readiness:` is `no-go` with OQ-01 open and blocking, so describing it would be an aspirational claim (P2).

  **ALSO RECORD THE NON-OBVIOUS HAZARD THIS SAME MEASUREMENT EXPOSES**, because it is the one an author trying to be helpful will hit: a bare `assert` in the loop body but OUTSIDE any subtest context aborts the sweep at the first bad row, so later rows never execute at all. Every row must still run after an earlier row fails. That is why the accumulate idiom collects rather than asserts in the loop.
  - Depends on: E-01
  - Expected outcome: the subsection states which idiom to use under which runner with the measured consequence of each, declines to promise a per-row verdict the toolchain cannot yet produce, and warns that an in-loop bare `assert` truncates the sweep.
  - Execution state: pending

- [ ] E-04 Add the pointer and the guard. In `CONTRIBUTING.md`, append ONE bullet to the `## Authoring conventions` list (beside the existing `Tests depending on the live checkout or environment:` bullet, which is the established shape for pointing at P16) naming the convention and pointing at the P16 subsection by its title. Keep it a POINTER, not a second copy, per that file's own "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)" bullet.

  Then add `tests/test_tabulated_test_convention.py` asserting the documented anchors are present, modelled on the shipped `tests/test_plan_review_feasibility_rule.py`, which is the repository's precedent for pinning a prose convention. Carry the same explicit exemption note that file carries: this reads `GUIDING_PRINCIPLES.md` and `CONTRIBUTING.md`, which are the artifacts under change and are NOT `agent_workflows/*` production source, so it falls inside P16's own "one narrow exception" ("Content verification is permissible only where the text or file itself is the artifact under test") and is out of scope for the structure-pin deletion sweep that plan `76ic0k` guards. Assert: that the P16 subsection exists and is inside P16 (not merely somewhere in the file); that it carries a short list of distinctive anchor phrases, one per load-bearing rule (the row shape, the `why` column's `this row exists because:` rendering, the when-NOT-to-tabulate list, and the pytest-versus-unittest row-verdict statement); and that `CONTRIBUTING.md` carries the pointer. Use anchor phrases distinctive enough to fail if the rule is deleted and loose enough to survive a copy-edit, exactly as the precedent's `ANCHOR_PHRASES` list does.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `CONTRIBUTING.md` points at the new subsection without restating it, and a new test goes red if any of the four load-bearing rules is removed from P16.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **P16 is the canonical home for test-authoring policy, and it is a repo-local file, not an installed asset.** `GUIDING_PRINCIPLES.md` principle 16 already carries the prohibitions, the what-to-do-instead list, and the live-checkout decision rule, and `CONTRIBUTING.md` points INTO it rather than restating it. Measured: `GUIDING_PRINCIPLES.md` appears in `agent_workflows/` only as a size entry in `run_analytics_statistics.py` and is not declared as package data in `pyproject.toml`, so this edit ships to no managed target repo and the project-agnostic constraint (P7) does not bind it.
- **A prose convention IS pinnable here, with a stated exemption.** `tests/test_plan_review_feasibility_rule.py` reads two workflow bodies and asserts five `ANCHOR_PHRASES`, and its module docstring records the exemption explicitly ("This test is explicitly outside the source-text-pin prohibition, verified at review (PR-004)") on the grounds that a workflow body is the artifact under change and it reads no `agent_workflows/*`. That is the shape E-04 follows.
- **Cite by symbol or quoted string, not by bare offset.** Per spec `ipd-structure-and-linting` Section 10.2 (advisory `IPD-C801`), this plan cites `test_ipd_lint.py`'s `RULES` table comment, `test_runner_profiles.ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`, and commit `75b90271` by content rather than by line number.
- **The run-suite contract is a bare `python3 -m pytest`.** `pyproject.toml` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, which is why the runner-dependence in E-03 is decided by pytest's behaviour and not `unittest`'s.

## Findings

| Id | Finding (all re-measured at HEAD `dfee027e`) | Evidence |
|---|---|---|
| F-01 | The convention is undocumented, exactly as the backlog item claims. | `rg -il 'tabulat|table-driven|subtest' GUIDING_PRINCIPLES.md CONTRIBUTING.md AGENTS.md ARCHITECTURE.md README.md DECISIONS.md docs/` printed nothing and exited 1. |
| F-02 | The convention is real and widespread: 16 test modules render `this row exists because:`, 165 occurrences in total, led by `test_completion.py` (20), `test_record_producers.py` (18), `test_installer.py` (18), `test_ipd_schema.py` (16), `test_ipd_lint.py` (15). | `rg -c 'this row exists because' tests/` |
| F-03 | **THE BACKLOG ITEM'S subTest PREMISE IS INVERTED.** Across those 16 files the accumulate idiom (`wrong = []`) appears 139 times against 30 `with self.subTest`, and 10 of the 16 files contain NO `subTest` at all. The house idiom is accumulate-then-assert. | Per-file census: `test_installer.py` 18/3, `test_completion.py` 16/0, `test_ipd_schema.py` 16/0, `test_ipd_lint.py` 14/2, `test_runner_profiles.py` 12/10, `test_aw_upgrade_test.py` 12/0. |
| F-04 | **AND THE RULE IT ASKS FOR WOULD BE HARMFUL UNDER THIS RUNNER.** With `pytest-subtests` absent, an in-context failure made pytest report only the FIRST failing row and never reach the trailing aggregate assertion; the accumulate class reported BOTH failing rows with each row's `why`. Under `python3 -m unittest` the same in-context class reported both rows and still ran the aggregate (`FAILED (failures=3)`). | Two-class probe run both ways; `python3 -m pip show pytest-subtests` -> `Package(s) not found`. Independently corroborates `t5txjk`'s F-08. |
| F-05 | The row shape is already stated canonically in one place, which is the right thing to cite rather than paraphrase. | `test_ipd_lint.py`'s `RULES` comment: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`. |
| F-06 | Case-first holds as an IDENTITY rule, not as a naming rule: of 102 `why`-terminated loops, 72 bind `case` and 30 bind a specific name (`kind`, `name`, `text`, `lane`, `record_class`, `shell`, `verb`, `describe`, `checkpoint`). A "must be named `case`" rule would condemn 30 conforming loops. | Regex census over the 16 files. |
| F-07 | The `why` column is near-universal but not absolute: 99 of 131 table loops terminate in `why`; the exceptions are loops over a table binding an underscore-prefixed throwaway (`_w`, `_why`) or iterating one column only (`for w in INS`). Stating it as mandatory for a NEW table is therefore honest; stating it as universal today would not be. | Same census; exceptions in `test_installer.py`, `test_ipd_schema.py`, `test_check_engine.py`, `test_ipd_lint.py`. |
| F-08 | The `needles`/`forbidden` pair is a common shape, not a universal arity: it appears in 7 files (`test_ipd_lint.py`, `test_executed_transition_gate_e2e.py`, `test_completion.py`, `test_record_producers.py`, `test_ipd_schema.py`, `test_check_engine.py`, `test_run_selection_policy.py`). So the doc must present middle columns as variable. | `rg -n 'for case, ' tests/` plus per-loop inspection. |
| F-09 | `75b90271`'s message is a rich and currently-unique source for the when-NOT-to-tabulate half (rollback order, idempotence pairs, consent transcripts, phase ordering, every `assertRaises`) and for two traps (keep every refusal individually detectable; do not reference constants that move with the reported value). One file it names, `test_migration_complex.py`, no longer exists (deleted in `19313eed`, "trim test suite from 9,136 to under 2,000 tests"), so the doc must take the REASONING from the message and not cite that path as a live example. | `git log -1 75b90271`; `git log --diff-filter=D -- tests/test_migration_complex.py`. |
| F-10 | `test_runner_profiles.py`'s module docstring is the fullest in-repo statement of the convention (mode-as-column for HOST/TIER/ROUTE, three-valued tri-states, and a list of reasons a test is not a row). It is a docstring in one test file, so it is invisible to anyone not already reading that file, which is the gap F-01 names. | Module docstring. |
| F-11 | Two pending sibling plans own the adjacent mechanism and must not be duplicated or pre-announced: `vtup6x` (evidence demand plus substitution rule, `approved`) and `t5txjk` (sound row-verdict driver, `reviewed` with `Readiness: no-go`, OQ-01 open and blocking). This plan is prose-only and cites them. | Both files in `.aw/records/plans/pending/`. |

## Proposed changes (ordered, validatable)

1. E-01: add the P16 subsection stating the row shape, case-first-as-identity, the mandatory `why` column, and the all-rows-at-once aggregate message.
2. E-02: extend it with when-to-tabulate and when-NOT-to, plus the individually-detectable-refusal and literal-strings traps.
3. E-03: state the per-row-verdict rule conditionally on the runner, with the measured pytest and unittest consequences, and the in-loop-bare-`assert` warning.
4. E-04: add the `CONTRIBUTING.md` pointer and the anchor-phrase guard test.

## Deferred / out of scope (with reason)

- **Changing any existing table or test idiom.** This item is documentation of an existing good practice (the backlog item says so explicitly). Converting the 30 `subTest` call sites, or the 4 blocks `t5txjk` targets, is that plan's work.
- **Building the row-verdict driver or any `aw` verb for it.** Owned by `t5txjk`, which is `no-go` pending OQ-01. E-03 cites it as pending and deliberately does not describe its mechanism as shipped (P2).
- **The IPD evidence-demand and substitution rules.** Owned by `vtup6x`, which amends the plan-review and intent-audit bodies. This plan touches no workflow body.
- **A mechanical lint rule for table shape.** The row shape is variable by design (F-06, F-07, F-08), so an author-time refusal would need a judgement call this plan has no evidence to calibrate. Deliberately prose plus an anchor guard, matching the feasibility-rule precedent.
- **Reconciling the `why`-column exceptions in F-07.** Four loops bind a throwaway `_why`. Documenting the rule for NEW tables does not require editing them, and editing them is not this plan's scope.

## Scope check

- Over-scope: none. All three declared paths are touched by E-01 through E-04, and nothing outside them is modified.
- Under-scope: the backlog item asks for four things (row shape and case-first rule, the `why` column and why it is not optional, when to tabulate and when not, and the per-row-verdict rule). E-01 covers the first two, E-02 the third, E-03 the fourth. E-03 deliberately CORRECTS the item's framing of the fourth rather than transcribing it, on the measurement in F-04; this is a correction of the stated mechanism, not a reduction of the requirement, and the requirement (tell an author how a row's verdict can and cannot be obtained) is met.

## Required tests / validation

The deliverable is prose plus one guard test, so validation is the guard test plus a full-suite regression check that the two edited Markdown files break nothing that reads them.

- `python3 -m pytest tests/test_tabulated_test_convention.py` must pass, and must be shown to be SENSITIVE: deleting one documented anchor from `GUIDING_PRINCIPLES.md` must make it fail, and restoring it must make it pass again (P16's own mutation requirement).
- A bare `python3 -m pytest` must pass with no new failures, pasted with its summary line.
- `aw ipd lint` on this plan must report conforming at `--phase pre-transition`.
- `aw sanitize --agent` must report no new finding, since the new prose quotes commit messages and test identifiers.

## Spec / documentation sync

No `.spec.md` file is touched, so no spec amendment is declared and `Scope-Paths` lists none. The convention being documented is a repository test-authoring practice, not a toolkit contract: it governs how THIS repository's own suite is written, and `GUIDING_PRINCIPLES.md` P16 is already the canonical home for exactly that (`CONTRIBUTING.md` points into it for the live-checkout rule rather than restating it). `CONTRIBUTING.md` gets a pointer, not a copy, per its own P8 bullet. No `docs/` page is added: `docs/` is the user-facing product documentation set indexed by `docs/README.md`, and a rule about writing this repository's unit tests is contributor-facing. Note that `t5txjk` separately declares `docs/row-level-test-evidence.md`; that page is its deliverable, not this one's.

## Open questions

### OQ-01: Should the P16 subsection state the accumulate idiom as the DEFAULT, or merely as one of two permitted shapes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence, which is why this is non-blocking. Two independent measurements point the same way. By PREVALENCE, accumulate leads 139 to 30 and 10 of 16 tabulated files use no `subTest` at all (F-03). By CONSEQUENCE, accumulate is the only one of the two that delivers the convention's own promise under the runner the repository actually uses: with `pytest-subtests` absent, in-context failure reported one row of two and never reached the aggregate message (F-04). A convention whose stated purpose is "reports every failing row at once" must therefore name accumulate as the default. `subTest` stays permitted and useful (it is what makes a per-row verdict recordable at all, which is why `t5txjk` builds on it), so the subsection presents it as the opt-in shape for row-level verdicts rather than as prohibited. No maintainer decision is required: this is a measurement, and if either measurement is disputed the fix is to re-run it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the full new P16 subsection as committed, plus the output of `rg -n 'tabulat|table-driven|subTest' GUIDING_PRINCIPLES.md` showing the terms now present where F-01 measured none. Then, reading the pasted prose only, answer these four questions and quote the sentence that answers each: (a) what is the first column of a row and what is it FOR; (b) what is the last column and why is it not optional; (c) what does the failure message render for a failing row; (d) does the rule require the first column to be NAMED `case`? Answer (d) must be NO. A paste that does not answer all four is a failed item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the when-to and when-NOT-to bullets as committed. Show they name at least five of the recorded not-a-row reasons (sequence/rollback order, idempotence pairs, consent transcripts, phase ordering, `assertRaises`, structural claims, two-results-compared, outcome contrast) and both traps (individually-detectable refusal codes; literal strings over constants that move with the reported value). Confirm by `git grep -n 'test_migration_complex' GUIDING_PRINCIPLES.md` returning NOTHING, since F-09 measured that file deleted and citing it as a live example would be a false citation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the row-verdict bullets as committed, then paste a RE-RUN of the F-04 probe at execution HEAD: both the `python3 -m pytest` run (showing the in-context class reporting only the first failing row with no aggregate marker, and the accumulate class reporting both rows) and the `python3 -m unittest` run (showing both rows plus `FAILED (failures=3)`), alongside `python3 -m pip show pytest-subtests`. The committed prose must agree with that output: if the plugin is present at execution time, the measurement differs and the prose must say what was actually observed rather than what this plan predicted. Also confirm the prose does NOT describe `t5txjk`'s strict mode as existing: `rg -n 'AW_ROW_STRICT|strict mode' GUIDING_PRINCIPLES.md` must either return nothing or return only text that marks it as pending/not yet shipped.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: three parts, all required. (1) Paste the `CONTRIBUTING.md` bullet and show it is a pointer: it must name the P16 subsection and must not restate the row shape. (2) Paste `python3 -m pytest tests/test_tabulated_test_convention.py` passing, with its summary line. (3) Paste a MUTATION demonstration proving sensitivity: delete one documented anchor phrase from `GUIDING_PRINCIPLES.md`, show the test FAILING and naming the missing anchor, restore the file (`git checkout -- GUIDING_PRINCIPLES.md` or equivalent), and show it PASSING again. Then paste a bare `python3 -m pytest` summary line showing no new failures, and `aw sanitize --agent` showing no new finding. A pass without the mutation half is a failed item, since an anchor test that cannot fail proves nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires `Status: approved` with a human attestation; this plan is `to-review` and carries no `Readiness:` field, because readiness is an output of `/plan-review` and not of authoring. The executor must honour the standing agent execution contract in the managed `AGENTS.md` block: commit only the three declared `Scope-Paths` through `aw commit`, never `git add -A` or `--no-verify`, never push, and paste ACTUAL runner output for every `V-*` rather than asserting that tests passed. The prose added here is CONTRIBUTOR-FACING (`GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md`), so P13's em-dash prohibition for user-facing prose applies to it; use hyphens.

One caution specific to this plan: E-03 deliberately contradicts the originating backlog item's fourth instruction on the strength of F-04. If the executor's re-measurement under V-03 disagrees with F-04 (for example because `pytest-subtests` has since been added to the `test` extra), the executor must write what they MEASURED and report the divergence as a finding, not quietly restore the backlog item's original wording. After all validation items are verified with pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `.aw/records/plans/executed/` through the tooled lifecycle transition.
