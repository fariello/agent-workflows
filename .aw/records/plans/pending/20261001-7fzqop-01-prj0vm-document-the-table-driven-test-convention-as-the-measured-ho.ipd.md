# IPD: Document the table-driven test convention as the measured house idiom, and state the accumulate-versus-subTest rule the way pytest actually behaves

- Date: 2026-10-01
- Kind: child
- Concern: The repository has converted at least 16 suites to TABLE-DRIVEN form with a genuinely consistent row shape, and the convention is written down NOWHERE. Measured at HEAD `dfee027e`: `rg -il 'tabulat|table-driven|subtest' GUIDING_PRINCIPLES.md CONTRIBUTING.md AGENTS.md ARCHITECTURE.md README.md DECISIONS.md docs/` exits 1 with no matches, so the only statement of the method is one commit message (`75b90271`, 2026-09-19) plus the idiom itself. A new author must infer the row shape by reading tests, and a reviewer has no cited rule to hold a new table to. The gap is not academic: the backlog item that asked for this doc proposed a subTest rule that this plan MEASURED TO BE BACKWARDS under the runner this repository actually uses, which is exactly the kind of error an undocumented convention invites.
- Scope: Prose only. Add one subsection to `GUIDING_PRINCIPLES.md` P16 stating the row shape, the case-first rule, the mandatory `why` column, when to tabulate and when NOT to, and the per-row-verdict rule stated by MEASURED pytest behaviour; add a one-line pointer from `CONTRIBUTING.md`'s authoring-conventions list; and add one guard test asserting the documented anchors survive, following the shipped `tests/test_plan_review_feasibility_rule.py` precedent. EXCLUDES changing any table, any test idiom, or any production code, and EXCLUDES building the row-verdict driver (that is pending plan `t5txjk`, whose readiness is `no-go` on an open blocking question).
- Scope-Paths: GUIDING_PRINCIPLES.md, CONTRIBUTING.md, tests/test_tabulated_test_convention.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: 7fzqop
- Set: 7fzqop
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: prj0vm
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-101..PR-112, all FIXED, none OPEN or DEFERRED. EVERY MATERIAL CLAIM RE-MEASURED INDEPENDENTLY at review HEAD `3292218f7`, 341 commits ahead of the authored `dfee027e`. THE PLAN'S CENTRAL THESIS IS CORRECT AND ITS HARDEST CLAIM REPRODUCES EXACTLY: F-01's documentation gap still exits 1 with no matches; F-03's inversion holds at 139 accumulate against 30 `subTest` over the same 16 files; and F-04's runner probe, re-run independently, showed pytest reporting ONLY row b with no aggregate marker while the accumulate class printed `AGGREGATE_MARKER: 2 of 3 rows wrong` plus both rows' `why` text, so the plan is right that the backlog item's fourth instruction is backwards for this repository. F-05, F-09's reasoning, F-10 and F-11 all verified verbatim in place. THE CENTRAL FINDING (PR-101, HIGH) IS A COLLISION THE PLAN DID NOT KNOW ABOUT: approved sibling `76ic0k` (`structpin` Order 02, `- Readiness: go-pending-approval`) declares `CONTRIBUTING.md` as a scope path, appends its own bullet to the SAME `## Authoring conventions` list, and carries the instruction "do NOT edit `GUIDING_PRINCIPLES.md`". Read in context that instruction is scoped to ITS subject (restating P16's four EXISTING prohibitions) and does not forbid adding a convention P16 states nowhere, so the plans are compatible in substance; recorded as OQ-02 with both texts quoted. They collide mechanically, and E-04 now carries the coordination instruction with V-04 demanding evidence of a coordinated append rather than a clobber. PR-102 (HIGH) is the same sibling's other half: its E-01 ships an AST guard over `tests/test_*.py` refusing six `inspect`/`ast` call forms with a one-entry self-cleaning allowlist, so E-04's new test had an unstated hard constraint; measured, the precedent `tests/test_plan_review_feasibility_rule.py` calls none of the six and reads with `read_text`, which that plan's E-03 bound (a) deliberately does not flag, so following the precedent exactly is what keeps the new test green, and V-04 now demands that proof. PR-103 (MEDIUM) found E-04's guard unimplementable as specified: P16 is the LAST principle (file is 186 lines, `## 16.` at 167, no `## 17.`), so the precedent's technique of locating a FOLLOWING heading and asserting it was found would fail on arrival; the bounding rule is now end-of-file tolerant. PR-104 (HIGH) widened F-09 tenfold: TEN of the eleven suites `75b90271` names were deleted by `19313eed`, not one, so an executor trusting F-09 could have cited any of nine other dead paths as a live example, and V-02 now requires an `ls` for every path the prose names. FOUR OF THE PLAN'S OWN CENSUSES ARE WRONG OR UNREPRODUCIBLE and are corrected with their re-measurements: F-02's 165 occurrences is 153 at the authored HEAD (PR-108, leaders reproduce exactly); F-07's `99 of 131` is `102 of 149` and its "four loops binding `_why`" is ONE loop binding `_bucket`, the rest being comprehensions that are correct as written (PR-111); F-08's count of 7 is right but its membership named `test_record_producers.py`, which has ZERO `needles`, and omitted `test_installer.py`, which has 4 (PR-105); and F-06's nine alternative first-column names are TWENTY-TWO, omitting `index`, the second most common binding in the corpus (PR-112). Because all four are drifting live populations, the gate now forbids writing any census number into the committed prose, which is the durable fix. Also fixed: PR-106 (the `FAILED (failures=3)` figure is invocation-dependent, `failures=4` under discovery, and V-03 now names the invocation), PR-107 (`t5txjk` E-04's `docs/` page already claims half of E-03's subject while that plan's own Deferred section names `7fzqop` as carrier for the other half, so the division is now stated), PR-109 (Step 0's packaging claim is false of the STRING, which appears in 13 modules including the `engine.py` text installed into every target repo, though its conclusion holds for the FILE), PR-110 (the in-loop bare-`assert` hazard was reasoning and is now demonstrated: `ROWS_EXECUTED=['row a: passes', 'row b: fails']` over a three-row table, so row c never ran). Added: a GREEN baseline the plan lacked entirely (`3822 passed, 2 skipped, 3 warnings in 143.85s`), a scope fence with one concrete stop condition, conditional finalize ownership, and a shared-checkout method rule for V-04's mutation (narrowed run only, since the assertion reads from disk so no in-memory form exists). OQ-01 verified sound with both its measurements re-derived and left resolved; OQ-02 added and resolved from both plans' text. Three decisions recorded in the typed review record, all `Reversible: yes`. Structural preflight `conforming` at `author` and at `review-finalize`.
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored in full from backlog `7fzqop`; every claim re-measured at HEAD `dfee027e`; ready for `/plan-review`.
- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Write down the table-driven test convention that already exists in this repository's suites, so a new author can follow it without reverse-engineering it from 16 files and a reviewer can cite it. State it as it is MEASURED to be, which means correcting one claim the backlog item makes: the house idiom is accumulate-then-assert (139 occurrences), not `subTest` (30), and under this repository's real runner a bare in-context failure DESTROYS the aggregate diagnostic the convention's failure messages exist to deliver.

WHAT THE DELIVERABLE IS AND IS NOT, stated because the distinction decides how a reviewer should judge it. This plan ships a RULE a human and an agent can be held to, plus an anchor guard that the rule remains written down. It ships NO mechanical enforcement that any table obeys the rule, and it deliberately cannot: the arity is variable, the first-column name takes twenty-two measured spellings, and the nearest in-tree precedent for a mechanical test-shape refusal (approved plan `76ic0k`) spends three E-items bounding its own detector and ships a one-entry allowlist to avoid condemning conforming code. So the guard test proves the DOCUMENTATION survives, never that a new table conforms. Judge this plan on whether the rule is correct, cites live files, and declines to state what the toolchain cannot do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: state the convention in its canonical home

- [x] E-01 In `GUIDING_PRINCIPLES.md`, add a new `###` subsection to principle 16 (`## 16. Test outcomes and behavior, never code structure or text`), placed AFTER the existing `### When tests depend on the live checkout or environment:` subsection so it is the last subsection of P16. Title it so it is greppable for the three terms measured absent today (`tabulated`, `table-driven`, `subTest`). It must state, as bullets:

  **THE ROW SHAPE.** A module- or class-level table of tuples, with the CASE STRING FIRST as a human-readable prose id, and a trailing `why` column. Cite the canonical in-repo statement of the shape, which is already written as a comment on `test_ipd_lint.py`'s `RULES` table: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`.   State the middle columns as what they are, VARIABLE per table (inputs, expected value, required `needles`, `forbidden` substrings), and do NOT prescribe a fixed arity: measured, the `needles`/`forbidden` pair appears in 7 files and is a common shape, not a universal one. The seven are `test_check_engine.py`, `test_completion.py`, `test_executed_transition_gate_e2e.py`, `test_installer.py`, `test_ipd_lint.py`, `test_ipd_schema.py` and `test_run_selection_policy.py` (CORRECTED AT REVIEW, PR-105, F-16: F-08's list named `test_record_producers.py`, which carries ZERO `needles`, and omitted `test_installer.py`, which carries 4; the count of 7 was right and the membership was not).

  **THE CASE-FIRST RULE, STATED AS IT IS ACTUALLY FOLLOWED.** The first column is the row's human-readable identity, and `case` is the usual name (72 of 102 measured `why`-terminated loops bind it as `case`). The remaining 30 bind a more specific name and that is CONFORMING, not a deviation: the rule is that the first column IDENTIFIES the row in the failure message, not that it is spelled `case`. Writing the rule as "must be named `case`" would mis-state the repository against itself and condemn 30 existing loops. The alternative names measured at review number TWENTY-TWO distinct bindings in all, led by `index` (13), `name` (7) and `value` (4), then `shell`, `text` and sixteen singletons including `kind`, `lane`, `verb`, `describe`, `record_class` and `checkpoint` (WIDENED AT REVIEW, PR-112: the authored list of nine omitted `index`, which is the second most common first-column name in the whole corpus). Do NOT enumerate all twenty-two in the prose; state the identity rule and give two or three examples, because the list is a drifting live population and the rule is not.

  **THE `why` COLUMN IS NOT OPTIONAL, AND SAY WHAT IT BUYS.** Every row carries the rule it encodes, and the failure message quotes it back as `this row exists because: <why>`. The reason it is mandatory is that tabulating DESTROYS the per-case test NAME that used to carry this information: a class per mode becomes a column, so the row's justification has nowhere else to live, and without it a failing row reports a data mismatch with no statement of which rule just broke. Measured at review: 102 of 149 multi-name table loops terminate in `why` (CORRECTED, PR-111: the authored `99 of 131` reproduces under no counting; see F-07). DO NOT WRITE EITHER RATIO INTO THE PROSE. The count is a live population that drifts with every lane, the rule is what the doc owes a reader, and a stale census in a principles file is exactly the kind of claim that rots unnoticed.

  **THE AGGREGATE FAILURE MESSAGE IS PART OF THE CONVENTION.** The table reports EVERY failing row at once, not just the first, via the accumulate idiom: collect each row's problems into a list and assert that list is empty at the end, with a message that states how many of how many rows were wrong and what their pattern MEANS. Cite `test_runner_profiles.ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`, whose aggregate message tells the reader to read the DIRECTION of the failures because over-reservation and under-reservation are different defects.
  - Depends on: none
  - Expected outcome: `rg -c 'tabulat|table-driven|subTest' GUIDING_PRINCIPLES.md` returns a nonzero count where it returns nothing today, and the subsection states the row shape, the case-first rule as an identity rule, the mandatory `why` column with its justification, and the all-rows-at-once aggregate message.
  - Execution state: performed

- [x] E-02 In the SAME subsection added by E-01, state WHEN TO TABULATE and WHEN NOT TO, taking both halves from the recorded reasoning rather than inventing a rule.

  **WHEN IT IS RIGHT:** clusters of tests differing only in DATA. Quote the method from commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN". Name the columns that commit reports as carrying the value (host, lint phase, entry point, cutover marker, queue shape, git state, resolver), and cite the fuller in-repo statement in the `test_runner_profiles.py` module docstring, which names HOST, TIER and ROUTE as the three mode-columns and explains that a chain tested level by level cannot exhibit an INVERSION.

  CITE THE COMMIT MESSAGE FOR ITS REASONING AND CITE NO FILE IT NAMES AS A LIVE EXAMPLE (ADDED AT REVIEW, PR-104, F-15, which corrects F-09's scope). `75b90271` lists eleven converted suites, and measured at review TEN of the eleven no longer exist: `test_orchestrator_probe.py`, `test_migration_complex.py`, `test_run_analytics_findings.py`, `test_ipd_dependency_check.py`, `test_research_contract.py`, `test_host_adapters_skills.py`, `test_backlog_graduated.py`, `test_release_gate_close.py`, `test_nested_tty_noninteractive.py` and `test_spec_visibility.py` were all deleted by `19313eed`. Only `test_executed_transition_gate.py` survives. F-09 named only `test_migration_complex.py`, which understated the hazard tenfold. So the doc may quote the commit's REASONING freely (it is a durable record of why) and must cite a LIVE file for every worked example; the live examples this plan already verified are `test_ipd_lint.py`'s `RULES` comment, `test_runner_profiles.py`'s module docstring and its `ProfileNameGrammarTests` aggregate message. Before writing any other file path into the prose, `ls` it.

  **WHEN IT IS WRONG, which is the half a new author will get wrong.** State these as the recorded reasons a test was deliberately left un-merged: the property IS the sequence (`75b90271` records rollback ORDER, where recoverability is the reverse order and no single row can state it); idempotence PAIRS; multi-step consent transcripts; an ordering constraint between two phases; every `assertRaises`; a claim that is STRUCTURAL rather than behavioural; a subject that is TWO RESULTS COMPARED TO EACH OTHER rather than to an expectation; and a CONTRAST between outcomes, where the point is that two cases differ. The last four are lifted from the `test_runner_profiles.py` module docstring's own "TESTS THAT ARE NOT ROWS CARRY A ONE-LINE DOCSTRING SAYING WHY" list, so cite it and adopt its rule: a test that is not a row says why in one line.

  **TWO TRAPS MEASURED IN PRACTICE, both recorded in `75b90271` and worth one bullet each.** FIRST, a safety gate must keep every refusal INDIVIDUALLY detectable: pin the refusal CODE, not merely that it refused, or two distinct refusals collapse into "it refused". SECOND, do not reference a production CONSTANT in the expected column when the constant is the published interface under test: `test_ipd_lint.py`'s `RULES` comment records that constant-referencing rows stayed GREEN when two code definitions were swapped, because constant and reported value move together, and it forbids "tidying" the literals back. State that a three-valued column is sometimes required and must not be collapsed to a bool, citing the same commit's measured `None`-means-absent versus `False`-means-decided distinction.
  - Depends on: E-01
  - Expected outcome: the subsection answers "should I tabulate this?" in both directions with in-repo citations, and carries the individually-detectable-refusal rule and the literal-strings rule as named traps.
  - Execution state: performed

### Task group 2: state the per-row-verdict rule as pytest actually behaves

- [x] E-03 In the same subsection, state the per-row-verdict rule. **THE BACKLOG ITEM'S FOURTH INSTRUCTION IS BACKWARDS FOR THIS REPOSITORY AND MUST NOT BE COPIED IN.** The item asks for "the rule that a row's failure must be raised INSIDE the subTest context or the row's per-row verdict is unobtainable". That is true of `unittest` and FALSE of the runner this repository runs, and writing it as an unconditional rule would instruct authors to delete the aggregate diagnostic E-01 just made mandatory. Re-measured for this plan at HEAD `dfee027e` with a two-class probe (an in-context `self.subTest` + `assertEqual` class and an accumulate class, each over a 3-row table with rows b and c failing):

  - under `python3 -m pytest` with `pytest-subtests` ABSENT (confirmed absent: `python3 -m pip show pytest-subtests` reports `Package(s) not found`, and `pytest-subtests` appears nowhere in `pyproject.toml`, so no extra installs it), the in-context class reported ONLY row b, never reached the trailing aggregate assertion, and printed no aggregate marker; the accumulate class reported BOTH wrong rows with the full `this row exists because:` text for each.
  - under `python3 -m unittest` the in-context class reported row b AND row c as separate subtest failures and still ran the aggregate. RE-MEASURED AND THE TOTAL CORRECTED AT REVIEW (PR-106, F-17): running the in-context class ALONE finishes `FAILED (failures=3)` (two rows plus the aggregate), while discovering BOTH probe classes finishes `FAILED (failures=4)` (those three plus the accumulate class's one aggregate failure). The authored plan reported `failures=3` without saying which invocation produced it; V-03 now names the invocation so the number is reproducible rather than ambiguous.

  So state the rule CONDITIONALLY and name the runner: in the default suite run, which is pytest, the ACCUMULATE idiom is what delivers every failing row plus its `why`, and a bare in-context failure costs you every row after the first plus the aggregate message. Say plainly that the per-row verdict an IPD's `V-*` evidence may ask for is therefore NOT obtainable from a default pytest run of an accumulate table, and that the honest paste is the enclosing test's verdict plus the row's inputs and expected value, SAID to be that. Point at pending plan `t5txjk` as the owner of a sound opt-in driver and `vtup6x` as the owner of the evidence-substitution rule, and state that until one ships, a per-row `PASS` list is not evidence. Do NOT document `t5txjk`'s opt-in strict mode as though it exists: its `Readiness:` is `no-go` with OQ-01 open and blocking, so describing it would be an aspirational claim (P2).

  **ALSO RECORD THE NON-OBVIOUS HAZARD THIS SAME MEASUREMENT EXPOSES**, because it is the one an author trying to be helpful will hit: a bare `assert` in the loop body but OUTSIDE any subtest context aborts the sweep at the first bad row, so later rows never execute at all. Every row must still run after an earlier row fails. That is why the accumulate idiom collects rather than asserts in the loop. DEMONSTRATED AT REVIEW rather than reasoned, which matters because the claim is about which rows RUN and not merely which are reported: a probe appending each visited case to a module list before a bare `assert` printed `ROWS_EXECUTED=['row a: passes', 'row b: fails']` over a three-row table, so row c never executed at all.

  DO NOT DUPLICATE `t5txjk`'s PAGE, AND SAY WHICH HALF IS WHOSE (ADDED AT REVIEW, PR-107, F-18). `t5txjk` E-04 adds `docs/row-level-test-evidence.md` carrying, in its own words, "the two-idiom hazard in one paragraph with the reason a passing `subTest` is silent under this repository's runner configuration, and the rule that a row verdict is only trustworthy when the row's failure is raised inside the subtest context". That overlaps this E-item's subject. The division that keeps both honest, and which `t5txjk` itself already asserts by naming `7fzqop` as the Carrier for "RESTATING THE ROW SHAPE OR THE `why` COLUMN CONVENTION": THIS plan states the AUTHORING rule (which idiom to write, and why accumulate is the default), and `t5txjk` states the EVIDENCE PROCEDURE (how to obtain a row verdict with its helper, and the one pasteable command). So keep this subsection's row-verdict bullets to the authoring consequence plus the honest statement that a per-row `PASS` list is not evidence today, and point at `t5txjk` for the procedure rather than describing it. If `t5txjk` has shipped by execution time, link its page; if not, cite it as pending. Either way do not restate its command.
  - Depends on: E-01
  - Expected outcome: the subsection states which idiom to use under which runner with the measured consequence of each, declines to promise a per-row verdict the toolchain cannot yet produce, and warns that an in-loop bare `assert` truncates the sweep.
  - Execution state: performed

- [x] E-04 Add the pointer and the guard. In `CONTRIBUTING.md`, append ONE bullet to the `## Authoring conventions` list (beside the existing `Tests depending on the live checkout or environment:` bullet, which is the established shape for pointing at P16) naming the convention and pointing at the P16 subsection by its title. Keep it a POINTER, not a second copy, per that file's own "Keep each policy or rule in exactly one canonical place and link to it, rather than duplicating it (P8)" bullet.

  COORDINATE WITH APPROVED PLAN `76ic0k`, WHICH EDITS THE SAME LIST AND FORBIDS ONE OF THIS PLAN'S EDITS (ADDED AT REVIEW, PR-101, F-12). `76ic0k` (Set `structpin` Order 02) is `- Status: approved` with `- Readiness: go-pending-approval` and declares `- Scope-Paths: tests/test_no_code_structure_pins.py, CONTRIBUTING.md`. Its E-04 appends its OWN pointer bullet to this same `## Authoring conventions` list and instructs, verbatim, "do NOT edit `GUIDING_PRINCIPLES.md`: P16 already says everything this Set needs, and duplicating it is the P8 violation the same section warns against." That instruction is scoped to ITS subject (restating P16's four prohibitions), not to this plan's subject (a convention P16 does not yet state at all), so the two are compatible in substance. They are NOT automatically compatible in execution:
  - BOTH plans append a bullet to the same list in the same file, so whichever runs second must REREAD the list and place its bullet beside the other rather than assuming the authored line numbers. Do not resolve this by text search for a line offset; locate the `## Authoring conventions` heading and append at the end of its bullet list.
  - If `76ic0k`'s bullet is already present, this bullet must not duplicate its P16 reference; name the TABLE-DRIVEN subsection specifically so the two bullets point at different P16 content.
  - Report at finalize which order actually happened and whether the other plan's bullet was present, so a reviewer can tell a coordinated append from a clobber.

  Then add `tests/test_tabulated_test_convention.py` asserting the documented anchors are present, modelled on the shipped `tests/test_plan_review_feasibility_rule.py`, which is the repository's precedent for pinning a prose convention. Carry the same explicit exemption note that file carries: this reads `GUIDING_PRINCIPLES.md` and `CONTRIBUTING.md`, which are the artifacts under change and are NOT `agent_workflows/*` production source, so it falls inside P16's own "one narrow exception" ("Content verification is permissible only where the text or file itself is the artifact under test").

  THE NEW TEST MUST READ WITH `read_text` AND MUST CALL NO `ast` OR `inspect` FORM, WHICH IS A HARD CONSTRAINT AND NOT A STYLE NOTE (ADDED AT REVIEW, PR-102, F-13). `76ic0k` E-01 ships `tests/test_no_code_structure_pins.py`, an AST guard that walks `tests/test_*.py` and REFUSES six attribute-call forms (`inspect.getsource`, `inspect.getsourcelines`, `inspect.getsourcefile`, `ast.parse`, `ast.walk`, `ast.unparse`), with an allowlist its E-02 pins at EXACTLY ONE justified entry and makes self-cleaning. So a new test under `tests/` that called any of those six would turn that approved guard RED with no allowlist slot available. Measured at review: the precedent `tests/test_plan_review_feasibility_rule.py` calls NONE of the six and reads its three subjects with `read_text` only, and `76ic0k` E-03 bound (a) records deliberately that `read_text` is NOT flagged. So following the precedent exactly is what keeps this test compatible; deviating toward an AST parse of the Markdown would not be. State this constraint in the new test's docstring so a later editor does not "improve" it into a violation.

  Assert: that the P16 subsection exists and is inside P16; that it carries a short list of distinctive anchor phrases, one per load-bearing rule (the row shape, the `why` column's `this row exists because:` rendering, the when-NOT-to-tabulate list, and the pytest-versus-unittest row-verdict statement); and that `CONTRIBUTING.md` carries the pointer. Use anchor phrases distinctive enough to fail if the rule is deleted and loose enough to survive a copy-edit, exactly as the precedent's `ANCHOR_PHRASES` list does.

  BOUND THE "INSIDE P16" ASSERTION ON THE FILE'S REAL STRUCTURE, BECAUSE P16 IS THE LAST PRINCIPLE AND HAS NO CLOSING BOUNDARY (ADDED AT REVIEW, PR-103, F-14). Measured: `GUIDING_PRINCIPLES.md` is 186 lines, `## 16.` begins at line 167, and NO `## 17.` or any later `##` exists, so P16 runs to end of file. The precedent test bounds its section by finding a NEXT heading (`### 3.1 ` then `### 3.2 `) and asserts both are found; copying that shape literally here would fail, because there is no heading after the new subsection. Bound the slice as "from the `## 16.` heading to the next `## ` heading OR end of file", and assert the subsection's offset is greater than the `## 16.` offset. Do not assert a trailing `## ` exists.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `CONTRIBUTING.md` points at the new subsection without restating it and without clobbering `76ic0k`'s bullet if present; the new test calls none of the six forms `76ic0k` flags; it bounds P16 to end-of-file rather than requiring a following heading; and it goes red if any of the four load-bearing rules is removed from P16.
  - Execution state: performed

## Project conventions discovered (Step 0)

- **P16 is the canonical home for test-authoring policy, and it is a repo-local file, not an installed asset.** `GUIDING_PRINCIPLES.md` principle 16 already carries the prohibitions, the what-to-do-instead list, and the live-checkout decision rule, and `CONTRIBUTING.md` points INTO it rather than restating it. Measured, with the claim NARROWED AT REVIEW to what is actually true (F-19): only `run_analytics_statistics.py` references the FILE (two size entries), the file is not declared as package data in `pyproject.toml`, and nothing copies it into a managed target repo, so this edit ships nowhere and the project-agnostic constraint (P7) does not bind it. The authored wording claimed the file "appears in `agent_workflows/` only as a size entry", which is false of the STRING (13 modules mention it, and `engine.py` writes a `GUIDING_PRINCIPLES P16` citation into the managed `AGENTS.md` block every target repo receives). The citation travels; the file does not.
- **P16 IS THE LAST PRINCIPLE IN THE FILE AND ENDS AT EOF**, which constrains both E-01's placement and E-04's guard (ADDED AT REVIEW, F-14). There is no `## 17.`, so "after the live-checkout subsection" and "last subsection of P16" and "end of file" are the same position, and a section-bounding assertion must tolerate the absence of a following heading.
- **A prose convention IS pinnable here, with a stated exemption.** `tests/test_plan_review_feasibility_rule.py` reads two workflow bodies and asserts five `ANCHOR_PHRASES`, and its module docstring records the exemption explicitly ("This test is explicitly outside the source-text-pin prohibition, verified at review (PR-004)") on the grounds that a workflow body is the artifact under change and it reads no `agent_workflows/*`. That is the shape E-04 follows. CRITICALLY, it reads with `read_text` and calls no `ast` or `inspect` form, which is what keeps it clear of the AST guard approved plan `76ic0k` ships (F-13); that is a constraint on E-04, not merely a stylistic resemblance.
- **THREE SIBLING PLANS TOUCH THIS NEIGHBOURHOOD AND ONE EDITS A DECLARED PATH OF THIS PLAN.** `vtup6x` (`approved`) owns the V-item evidence rule, `t5txjk` (`reviewed`, `no-go`) owns the row-verdict driver and a `docs/` page overlapping E-03's subject (F-18), and `76ic0k` (`approved`) edits the same `CONTRIBUTING.md` list and ships the AST guard (F-12, F-13). Coordination instructions are in E-04; none of the three declares `GUIDING_PRINCIPLES.md`, so that half of this plan's scope is uncontested.
- **Cite by symbol or quoted string, not by bare offset.** Per spec `ipd-structure-and-linting` Section 10.2 (advisory `IPD-C801`), this plan cites `test_ipd_lint.py`'s `RULES` table comment, `test_runner_profiles.ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`, and commit `75b90271` by content rather than by line number.
- **The run-suite contract is a bare `python3 -m pytest`.** `pyproject.toml` sets `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`, which is why the runner-dependence in E-03 is decided by pytest's behaviour and not `unittest`'s.

## Findings

| Id | Finding (all re-measured at HEAD `dfee027e`) | Evidence |
|---|---|---|
| F-01 | The convention is undocumented, exactly as the backlog item claims. | `rg -il 'tabulat|table-driven|subtest' GUIDING_PRINCIPLES.md CONTRIBUTING.md AGENTS.md ARCHITECTURE.md README.md DECISIONS.md docs/` printed nothing and exited 1. |
| F-02 | The convention is real and widespread: 16 test modules render `this row exists because:`, led by `test_completion.py` (20), `test_record_producers.py` (18), `test_installer.py` (18), `test_ipd_schema.py` (16), `test_ipd_lint.py` (15). THE TOTAL IS CORRECTED AT REVIEW (PR-108): the occurrence count at authoring HEAD `dfee027e` is **153**, not 165, measured by `git grep -o` over `tests/`; the authored 165 reproduces under no counting I could find (the nearest figures are 162 over the whole tree at that HEAD and 164 over `tests/` at review HEAD, where a 17th file has since appeared). The five leaders reproduce EXACTLY, so the shape of the finding holds and only its total was wrong. Since this population drifts with every lane, the doc must not quote a count at all. | `git grep -o 'this row exists because' dfee027e -- tests/ \| wc -l` -> 153; `git grep -c ... dfee027e -- tests/` for the per-file leaders; `rg -o ... tests/ \| wc -l` -> 164 at review HEAD. |
| F-03 | **THE BACKLOG ITEM'S subTest PREMISE IS INVERTED.** Across those 16 files the accumulate idiom (`wrong = []`) appears 139 times against 30 `with self.subTest`, and 10 of the 16 files contain NO `subTest` at all. The house idiom is accumulate-then-assert. VERIFIED EXACTLY AT REVIEW against the same 16 files at `dfee027e`: `wrong = []` 139, `with self.subTest` 30. At review HEAD the same census over 17 files reads 148 and 34, so the ratio is stable and the finding is robust to drift. | Per-file census: `test_installer.py` 18/3, `test_completion.py` 16/0, `test_ipd_schema.py` 16/0, `test_ipd_lint.py` 14/2, `test_runner_profiles.py` 12/10, `test_aw_upgrade_test.py` 12/0; review re-ran the aggregate at both HEADs. |
| F-04 | **AND THE RULE IT ASKS FOR WOULD BE HARMFUL UNDER THIS RUNNER.** With `pytest-subtests` absent, an in-context failure made pytest report only the FIRST failing row and never reach the trailing aggregate assertion; the accumulate class reported BOTH failing rows with each row's `why`. RE-MEASURED INDEPENDENTLY AT REVIEW and it reproduces exactly: pytest reported `row b` only, with no `AGGREGATE_MARKER_REACHED`, while the accumulate class printed `AGGREGATE_MARKER: 2 of 3 rows wrong` followed by both rows' `this row exists because:` text. Under `python3 -m unittest` the in-context class ALONE finishes `FAILED (failures=3)`; discovering both probe classes finishes `failures=4` (see F-17 for why the plan must name the invocation). | Two-class probe run both ways at review inside the lane's gitignored `tmp/`, removed afterwards; `python3 -m pip show pytest-subtests` -> `WARNING: Package(s) not found`; `rg -n subtests pyproject.toml` -> no match. Independently corroborates `t5txjk`'s F-08. |
| F-05 | The row shape is already stated canonically in one place, which is the right thing to cite rather than paraphrase. | `test_ipd_lint.py`'s `RULES` comment: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`. |
| F-06 | Case-first holds as an IDENTITY rule, not as a naming rule: of 102 `why`-terminated loops, 72 bind `case` and 30 bind a specific name. A "must be named `case`" rule would condemn 30 conforming loops. VERIFIED EXACTLY AT REVIEW (102 loops, 72 `case`, 30 other) and the alternative-name set is WIDER than the plan lists, which strengthens the finding: beyond the nine named (`kind`, `name`, `text`, `lane`, `record_class`, `shell`, `verb`, `describe`, `checkpoint`) the census also finds `index` (13, the second most common binding of all), `value` (4), `words`, `state`, `which`, `groups`, `args`, `i`, `attr`, `sub_name`, `left`, `target`. Twenty-two distinct bindings in total, so prescribing a name would be even more wrong than the plan says. | Regex census over the 16 files at `dfee027e`, printing every first-column binding with its frequency. |
| F-07 | The `why` column is near-universal but not absolute, so stating it as mandatory for a NEW table is honest while stating it as universal today would not be. THE DENOMINATOR AND THE EXCEPTION SHAPE ARE BOTH CORRECTED AT REVIEW (PR-111): re-measured over the 16 files at `dfee027e`, of **149** multi-name table loops **102** terminate in `why`, and exactly **ONE** binds an underscore-prefixed last name (`_bucket`, in `test_orchestrator_retirement.py`), not four. The authored `99 of 131` reproduces under no counting I tried. The `_w`/`_why` bindings the plan had in mind are COMPREHENSIONS over the same tables (`test_check_engine.py`, `test_ipd_schema.py`, `test_record_producers.py`), which discard columns they do not read and are correct as written, so they are not exceptions to the rule at all. The finding's CONCLUSION is unchanged and is what the doc needs. | Review census counting multi-name `for ... in ...:` loops and their last bound name; `git grep -n "_w\b\|_why\b" dfee027e -- tests/` with each hit read in context to separate loops from comprehensions. |
| F-08 | The `needles`/`forbidden` pair is a common shape, not a universal arity: it appears in 7 files (`test_ipd_lint.py`, `test_executed_transition_gate_e2e.py`, `test_completion.py`, `test_record_producers.py`, `test_ipd_schema.py`, `test_check_engine.py`, `test_run_selection_policy.py`). So the doc must present middle columns as variable. | `rg -n 'for case, ' tests/` plus per-loop inspection. |
| F-09 | `75b90271`'s message is a rich and currently-unique source for the when-NOT-to-tabulate half (rollback order, idempotence pairs, consent transcripts, phase ordering, every `assertRaises`) and for two traps (keep every refusal individually detectable; do not reference constants that move with the reported value). VERIFIED AT REVIEW: every reason and both traps are present in that commit body verbatim, including the mutation anecdote ("Referencing `rs.PROBE_*_CODE` constants left all 40 probe tests green when the two code definitions were swapped"). THE DELETION CAVEAT IS UNDERSTATED TENFOLD AND IS CORRECTED BY F-15: the plan named only `test_migration_complex.py`, but TEN of the eleven suites that commit lists are gone. | `git log -1 75b90271 --format=%b` read in full; per-file existence check over all eleven named suites (see F-15). |
| F-10 | `test_runner_profiles.py`'s module docstring is the fullest in-repo statement of the convention (mode-as-column for HOST/TIER/ROUTE, three-valued tri-states, and a list of reasons a test is not a row). It is a docstring in one test file, so it is invisible to anyone not already reading that file, which is the gap F-01 names. | Module docstring. |
| F-11 | Two pending sibling plans own the adjacent mechanism and must not be duplicated or pre-announced: `vtup6x` (evidence demand plus substitution rule, `approved`) and `t5txjk` (sound row-verdict driver, `reviewed` with `Readiness: no-go`, OQ-01 open and blocking). This plan is prose-only and cites them. VERIFIED EXACTLY AT REVIEW: `vtup6x` is `- Status: approved` / `- Readiness: go-pending-approval`, and `t5txjk` is `- Status: reviewed` / `- Readiness: no-go` with one `- Status: open` question carrying `- Blocking: yes` and `- Finding: PR-002`. Neither declares `GUIDING_PRINCIPLES.md`, so no scope-path collision exists with either. | Both files read in place; `- Status:`/`- Readiness:`/`- Scope-Paths:` lines quoted. |
| F-12 | **ADDED AT REVIEW (PR-101). A THIRD SIBLING IS APPROVED, EDITS THE SAME `CONTRIBUTING.md` LIST, AND CARRIES AN INSTRUCTION THAT READS AS FORBIDDING THIS PLAN'S MAIN EDIT.** `76ic0k` (Set `structpin` Order 02) is `- Status: approved`, `- Readiness: go-pending-approval`, `- Scope-Paths: tests/test_no_code_structure_pins.py, CONTRIBUTING.md`. Its E-04 appends a pointer bullet to the SAME `## Authoring conventions` list and says verbatim "do NOT edit `GUIDING_PRINCIPLES.md`: P16 already says everything this Set needs, and duplicating it is the P8 violation the same section warns against." Read in context that instruction is scoped to ITS subject (restating P16's four existing prohibitions), not to adding a convention P16 does not state, so the plans are compatible in SUBSTANCE. They collide in EXECUTION, because both append to one list and the plan had no coordination instruction at all. | Both plans' front matter and E-04 bodies read in place. |
| F-13 | **ADDED AT REVIEW (PR-102). `76ic0k` SHIPS AN AST GUARD OVER `tests/test_*.py` WITH A ONE-ENTRY SELF-CLEANING ALLOWLIST, SO E-04's NEW TEST HAS A HARD CONSTRAINT ON HOW IT MAY READ FILES.** That guard refuses six attribute-call forms (`inspect.getsource`, `inspect.getsourcelines`, `inspect.getsourcefile`, `ast.parse`, `ast.walk`, `ast.unparse`), its E-02 pins the allowlist at exactly one justified entry and asserts a stale entry FAILS, and its E-03 bound (a) records deliberately that `read_text` is NOT flagged. Measured: the precedent `tests/test_plan_review_feasibility_rule.py` calls none of the six and reads all three subjects with `read_text`. So following the precedent keeps the new test green against the approved guard, and an AST parse of the Markdown would turn it red with no allowlist slot available. | `rg` for all six forms in the precedent -> none; `rg -n read_text` -> three call sites; `76ic0k` E-01/E-02/E-03 read in place. |
| F-14 | **ADDED AT REVIEW (PR-103). P16 IS THE LAST PRINCIPLE IN THE FILE, SO THE PRECEDENT'S SECTION-BOUNDING TECHNIQUE CANNOT BE COPIED LITERALLY.** `GUIDING_PRINCIPLES.md` is 186 lines; `## 16.` starts at line 167; no `## 17.` or any later `##` exists, and P16's three existing subsections (`### What is prohibited:`, `### What to do instead:`, `### When tests depend on the live checkout or environment:`) run to EOF. The precedent test bounds its target by locating a NEXT heading and asserting it was found (`### 3.1 ` then `### 3.2 `); the analogous assertion here would fail on arrival, because E-01 places the new subsection last. | `rg -n "^## 1[678]" GUIDING_PRINCIPLES.md` -> only line 167; `wc -l` -> 186; the precedent's two `assertNotEqual(..., -1)` heading checks read in place. |
| F-15 | **ADDED AT REVIEW (PR-104). TEN OF THE ELEVEN SUITES `75b90271` NAMES NO LONGER EXIST, NOT ONE.** Per-file check: `test_orchestrator_probe.py`, `test_migration_complex.py`, `test_run_analytics_findings.py`, `test_ipd_dependency_check.py`, `test_research_contract.py`, `test_host_adapters_skills.py`, `test_backlog_graduated.py`, `test_release_gate_close.py`, `test_nested_tty_noninteractive.py`, `test_spec_visibility.py` all GONE, every one deleted by `19313eed`; only `test_executed_transition_gate.py` survives. F-09 named a single deletion, so an executor trusting it could have cited any of nine other dead paths as a live example. | `ls tests/<name>.py` plus `git log --diff-filter=D --format=%h` for each of the eleven. |
| F-16 | **ADDED AT REVIEW (PR-105). F-08's COUNT IS RIGHT AND ITS MEMBERSHIP IS WRONG.** The `needles`/`forbidden` pair appears in 7 files, but they are `test_check_engine.py`, `test_completion.py`, `test_executed_transition_gate_e2e.py`, `test_installer.py`, `test_ipd_lint.py`, `test_ipd_schema.py`, `test_run_selection_policy.py`. F-08 listed `test_record_producers.py`, which has ZERO `needles` (6 `forbidden`), and omitted `test_installer.py`, which has 4 `needles` and 3 `forbidden`. | Per-file `grep -c needles` / `grep -c forbidden` over all 16 tabulated files at `dfee027e`. |
| F-17 | **ADDED AT REVIEW (PR-106). THE `FAILED (failures=3)` FIGURE IS INVOCATION-DEPENDENT AND THE PLAN DID NOT SAY WHICH.** Running the in-context probe class alone gives `failures=3` (row b, row c, aggregate), matching the plan; `unittest discover` over BOTH probe classes gives `failures=4`, adding the accumulate class's aggregate. A V-item demanding "`FAILED (failures=3)`" without naming the invocation is therefore satisfiable or not depending on how the executor runs it. | `python3 -m unittest test_rowprobe.InContextSubTestTests -v` -> `failures=3`; `python3 -m unittest discover -s tmp/rowprobe -p test_rowprobe.py -v` -> `failures=4`. |
| F-18 | **ADDED AT REVIEW (PR-107). `t5txjk` E-04's PAGE ALREADY CLAIMS PART OF E-03's SUBJECT, AND `t5txjk` ITSELF NAMES THIS ITEM AS THE CARRIER FOR THE OTHER PART.** Its E-04 writes `docs/row-level-test-evidence.md` carrying "the two-idiom hazard in one paragraph with the reason a passing `subTest` is silent under this repository's runner configuration, and the rule that a row verdict is only trustworthy when the row's failure is raised inside the subtest context". Separately its own `## Deferred` section lists "RESTATING THE ROW SHAPE OR THE `why` COLUMN CONVENTION" with `- Carrier: 7fzqop`. So the division is already agreed in-tree and needs stating here: this plan owns the AUTHORING rule, `t5txjk` owns the EVIDENCE PROCEDURE. | `t5txjk` E-04 body and its `## Deferred / out of scope` carrier rows read in place. |
| F-19 | **ADDED AT REVIEW (PR-109). STEP 0's PACKAGING CLAIM IS FALSE AS WRITTEN, THOUGH ITS CONCLUSION HOLDS.** Step 0 says `GUIDING_PRINCIPLES.md` "appears in `agent_workflows/` only as a size entry in `run_analytics_statistics.py`". Measured: the STRING appears in 13 modules, including `engine.py`, which writes `GUIDING_PRINCIPLES P16` into the managed `AGENTS.md` block installed into every target repo. What is true is the narrower claim the conclusion needs: only `run_analytics_statistics.py` references the FILE (two size entries), the file is not declared as package data in `pyproject.toml`, and nothing copies it into a target repo, so the edit ships nowhere and P7 does not bind it. The citation is what travels, not the file. | `rg -ln GUIDING_PRINCIPLES agent_workflows/ \| wc -l` -> 13; `rg -n "GUIDING_PRINCIPLES\.md" agent_workflows/` -> two lines, both in `run_analytics_statistics.py`; `agent_workflows/engine.py` P16 citation read in context; `rg -n GUIDING_PRINCIPLES pyproject.toml` -> no match. |
| F-20 | **ADDED AT REVIEW (PR-110). THE IN-LOOP BARE-`assert` HAZARD E-03 ASSERTS IS REAL AND NOW DEMONSTRATED.** The plan stated the hazard as reasoning; review proved it. A probe appending each visited case to a module-level list before a bare `assert` over a three-row table printed `ROWS_EXECUTED=['row a: passes', 'row b: fails']`, so row c never executed. This matters because the claim is about which rows RUN, which is stronger than which rows are REPORTED, and it is the half an author will not predict. | `python3 -m pytest tmp/rowprobe/test_bareassert.py -o addopts="" -p no:randomly -s` printing the `ROWS_EXECUTED` line beside `1 failed, 1 passed`. |
| F-21 | **ADDED AT REVIEW. THE SUITE IS GREEN AT REVIEW HEAD, AND THE PLAN STATED NO BASELINE AT ALL.** Bare `python3 -m pytest` gives `3822 passed, 2 skipped, 3 warnings in 143.85s` at HEAD `3292218f7`, which is 341 commits ahead of the authored `dfee027e`. The plan's Required tests asked for "no new failures" without recording a before-count, so an executor had nothing to compare against. | `python3 -m pytest` summary line at review; `git log --oneline dfee027e..HEAD \| wc -l` -> 341. |

## Proposed changes (ordered, validatable)

1. E-01: add the P16 subsection stating the row shape, case-first-as-identity, the mandatory `why` column, and the all-rows-at-once aggregate message.
2. E-02: extend it with when-to-tabulate and when-NOT-to, plus the individually-detectable-refusal and literal-strings traps.
3. E-03: state the per-row-verdict rule conditionally on the runner, with the measured pytest and unittest consequences, and the in-loop-bare-`assert` warning.
4. E-04: add the `CONTRIBUTING.md` pointer and the anchor-phrase guard test.

## Deferred / out of scope (with reason)

- **Changing any existing table or test idiom.** This item is documentation of an existing good practice (the backlog item says so explicitly). Converting the 30 `subTest` call sites, or the 4 blocks `t5txjk` targets, is that plan's work.
  - Carrier: t5txjk
- **THE PER-ROW EVIDENCE PROCEDURE (the pasteable command and its helper).** Out of scope, ADDED AT REVIEW (F-18). `t5txjk` E-04 already writes `docs/row-level-test-evidence.md` carrying the hazard paragraph and the trustworthy-verdict rule, and that plan's own Deferred section names `7fzqop` as the Carrier for the row-shape half, so the division is agreed in-tree: this plan states the AUTHORING rule, `t5txjk` states the PROCEDURE. E-03 points rather than restating.
  - Carrier: t5txjk
- **Building the row-verdict driver or any `aw` verb for it.** Owned by `t5txjk`, which is `no-go` pending OQ-01. E-03 cites it as pending and deliberately does not describe its mechanism as shipped (P2).
  - Carrier: t5txjk
- **The IPD evidence-demand and substitution rules.** Owned by `vtup6x`, which amends the plan-review and intent-audit bodies. This plan touches no workflow body.
  - Carrier: vtup6x
  - Carrier-Evidence: .aw/records/plans/executed/20260929-nos070-01-vtup6x-make-v-item-test-evidence-survive-test-reorganization-demand.ipd.md
- **A mechanical lint rule for table shape.** The row shape is variable by design (F-06, F-07, F-08), so an author-time refusal would need a judgement call this plan has no evidence to calibrate. Deliberately prose plus an anchor guard, matching the feasibility-rule precedent.
  - Carrier-Declined: A genuine won't-fix rather than postponed work, and review strengthened the reason rather than accepting it: the arity is variable (F-08/F-16 measured the `needles`/`forbidden` pair in 7 of 16 files), the first-column NAME is variable by design across 22 distinct bindings (F-06), and the nearest in-tree precedent for a mechanical test-shape refusal, approved plan `76ic0k`, spends three E-items documenting why its own detector must stay narrow and ships a one-entry allowlist to avoid false positives. A shape lint here would be strictly harder to calibrate than that one and would start by condemning conforming loops. Nothing remains for a carrier to own.
- **Reconciling the `why`-column exceptions.** CORRECTED AT REVIEW: the authored row said "four loops bind a throwaway `_why`", and the measurement does not support that shape. Re-measured over the 16 tabulated files at `dfee027e`: of 149 multi-name table loops, 102 terminate in `why` and exactly ONE binds an underscore-prefixed last name (`_bucket`, in `test_orchestrator_retirement.py`). The `_w`/`_why` bindings the plan had in mind are not loops at all but set/dict COMPREHENSIONS over the same tables (in `test_check_engine.py`, `test_ipd_schema.py`, `test_record_producers.py`), which discard columns they do not need and are correct as written. So there is nothing to reconcile: documenting the rule for NEW tables requires no edit to any of them.
  - Carrier-Declined: No obligation outlives this plan, because the measurement shows no defective population: a comprehension that discards a column it does not read is not a table loop missing its `why`. Filing a carrier would assert cleanup work that the re-measurement says does not exist.

## Scope check

- Over-scope: none. All three declared paths are touched by E-01 through E-04, and nothing outside them is modified. ONE DECLARED PATH IS SHARED WITH AN APPROVED SIBLING: `CONTRIBUTING.md` is also declared by `76ic0k` (F-12), which appends its own bullet to the same list. That is a coordination obligation (E-04 carries it) and not an over-scope edit, since each plan writes only its own bullet.
- Under-scope: the backlog item asks for four things (row shape and case-first rule, the `why` column and why it is not optional, when to tabulate and when not, and the per-row-verdict rule). E-01 covers the first two, E-02 the third, E-03 the fourth. E-03 deliberately CORRECTS the item's framing of the fourth rather than transcribing it, on the measurement in F-04; this is a correction of the stated mechanism, not a reduction of the requirement, and the requirement (tell an author how a row's verdict can and cannot be obtained) is met. TWO BOUNDS ADDED AT REVIEW, both recorded rather than closed here: the evidence PROCEDURE for a row verdict stays with `t5txjk` (F-18), so E-03 states the authoring consequence and points rather than describing a command; and no mechanical check enforces the row shape, which is deliberate (see the Deferred row) with E-04's anchor guard covering only that the RULE remains written down, never that any table obeys it.

## Required tests / validation

The deliverable is prose plus one guard test, so validation is the guard test plus a full-suite regression check that the two edited Markdown files break nothing that reads them.

BASELINE, MEASURED AT REVIEW HEAD `3292218f7` (ADDED AT REVIEW, F-21): bare `python3 -m pytest` gives `3822 passed, 2 skipped, 3 warnings in 143.85s`. THE TREE IS FULLY GREEN, so the bar is a green before-baseline and a green after-baseline, with the passed count increased by exactly the number of tests E-04 adds. The authored plan recorded no baseline at all, leaving "no new failures" with nothing to compare against; the tree is 341 commits ahead of the authored `dfee027e`, so take your own before-baseline rather than trusting this number, and if any node is red at your baseline identify it as pre-existing with evidence.

- `python3 -m pytest tests/test_tabulated_test_convention.py` must pass, and must be shown to be SENSITIVE: deleting one documented anchor from `GUIDING_PRINCIPLES.md` must make it fail, and restoring it must make it pass again (P16's own mutation requirement). THE MUTATION IS A REAL EDIT TO A TRACKED FILE IN A SHARED CHECKOUT, so keep the window to seconds: run only the narrowed node while the edit is live (`-o addopts=""` on the single file, never the full suite), restore with `git checkout -- GUIDING_PRINCIPLES.md`, and paste `git status --short` empty before and after. The reason is measured rather than stylistic and is recorded in `t0ovw6`'s review: a `git checkout` restore after a multi-minute suite run discards whatever a co-worker wrote to that file in the interval. An in-memory mutation is not available here because the assertion reads the file from disk, which is exactly why the window must be minimized instead.
- A bare `python3 -m pytest` must pass GREEN, pasted with its summary line, with the count increased by exactly the number of tests E-04 adds.
- RE-RUN THE F-04 PROBE AT EXECUTION HEAD and paste it, naming the invocation (see V-03). If `pytest-subtests` has since been installed, the measurement differs and the committed prose must state what was OBSERVED, not what this plan predicted.
- `aw ipd lint` on this plan must report conforming at `--phase pre-transition`.
- `aw sanitize --agent` must report no new finding, since the new prose quotes commit messages and test identifiers.
- CONFIRM THE `76ic0k` COMPATIBILITY CLAIMS EMPIRICALLY, not by reading this plan: the new test must call none of the six forms that plan's guard flags, and if `tests/test_no_code_structure_pins.py` exists at execution time it must be RUN and shown green with the new test present (see V-04).

## Spec / documentation sync

No `.spec.md` file is touched, so no spec amendment is declared and `Scope-Paths` lists none. The convention being documented is a repository test-authoring practice, not a toolkit contract: it governs how THIS repository's own suite is written, and `GUIDING_PRINCIPLES.md` P16 is already the canonical home for exactly that (`CONTRIBUTING.md` points into it for the live-checkout rule rather than restating it). `CONTRIBUTING.md` gets a pointer, not a copy, per its own P8 bullet. No `docs/` page is added: `docs/` is the user-facing product documentation set indexed by `docs/README.md`, and a rule about writing this repository's unit tests is contributor-facing. Note that `t5txjk` separately declares `docs/row-level-test-evidence.md`; that page is its deliverable, not this one's.

## Open questions

### OQ-01: Should the P16 subsection state the accumulate idiom as the DEFAULT, or merely as one of two permitted shapes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence, which is why this is non-blocking. Two independent measurements point the same way. By PREVALENCE, accumulate leads 139 to 30 and 10 of 16 tabulated files use no `subTest` at all (F-03). By CONSEQUENCE, accumulate is the only one of the two that delivers the convention's own promise under the runner the repository actually uses: with `pytest-subtests` absent, in-context failure reported one row of two and never reached the aggregate message (F-04). A convention whose stated purpose is "reports every failing row at once" must therefore name accumulate as the default. `subTest` stays permitted and useful (it is what makes a per-row verdict recordable at all, which is why `t5txjk` builds on it), so the subsection presents it as the opt-in shape for row-level verdicts rather than as prohibited. No maintainer decision is required: this is a measurement, and if either measurement is disputed the fix is to re-run it. VERIFIED INDEPENDENTLY AT REVIEW: both measurements reproduce exactly (139/30 at `dfee027e`, and the two-class probe behaving as F-04 records), so the resolution rests on re-derived evidence rather than on the author's word.

### OQ-02: Does approved sibling `76ic0k`'s instruction "do NOT edit `GUIDING_PRINCIPLES.md`" forbid this plan's central edit?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: ADDED AT REVIEW (F-12). RESOLVED FROM BOTH PLANS' TEXT: NO, it does not, and the reason is that the instruction is scoped to its own subject. `76ic0k` E-04's full sentence reads "DO NOT restate P16's four prohibitions here, and do NOT edit `GUIDING_PRINCIPLES.md`: P16 already says everything this Set needs, and duplicating it is the P8 violation the same section warns against." The operative clause is "everything THIS SET needs": that Set's subject is the four prohibitions P16 ALREADY states, so editing P16 would have been pure duplication and a P8 violation. This plan's subject is a convention P16 states NOWHERE (F-01 measured `tabulat`, `table-driven` and `subTest` absent from the entire file), so adding it is the OPPOSITE of duplication; it is what gives the convention a canonical home to point at, which is what P8 asks for. The two plans are therefore compatible in substance, and the real risk is mechanical rather than normative: both append a bullet to the same `## Authoring conventions` list, so whichever runs second must reread the list and append beside the other. E-04 now carries that coordination instruction and V-04 part (1) demands evidence of a coordinated append. Not blocking: nothing in either plan's content needs changing, and the ordering hazard is handled by an instruction rather than a decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the full new P16 subsection as committed, plus the output of `rg -n 'tabulat|table-driven|subTest' GUIDING_PRINCIPLES.md` showing the terms now present where F-01 measured none. Then, reading the pasted prose only, answer these four questions and quote the sentence that answers each: (a) what is the first column of a row and what is it FOR; (b) what is the last column and why is it not optional; (c) what does the failure message render for a failing row; (d) does the rule require the first column to be NAMED `case`? Answer (d) must be NO. A paste that does not answer all four is a failed item.
  - Observed evidence: Full new P16 subsection committed in GUIDING_PRINCIPLES.md with all anchor terms present and four questions answered:
    ```markdown
    ### Tabulated and table-driven tests (accumulate versus subTest):

    Table-driven tests group related test cases differing primarily in data into a single table. When authoring or reviewing table-driven tests in this repository, follow these conventions:

    - **The row shape**: A module- or class-level table of tuples, with the human-readable case identifier first and a trailing `why` column. The canonical in-repository shape is stated in `tests/test_ipd_lint.py`'s `RULES` table comment: `(case, the plan text, codes that MUST all be reported, message substrings that must appear on those codes' diagnostics, codes that must NOT be reported, why this row exists)`. The middle columns vary by table (such as inputs, expected value, required `needles`, and `forbidden` substrings; seen across `test_check_engine.py`, `test_completion.py`, `test_executed_transition_gate_e2e.py`, `test_installer.py`, `test_ipd_lint.py`, `test_ipd_schema.py`, and `test_run_selection_policy.py`). Do not prescribe a rigid arity for middle columns.
    - **The case-first rule**: The first column serves as the row's human-readable identity in diagnostics and failure messages. While `case` is the most common variable name in loop bindings, the rule requires identity rather than a specific parameter name. Clear contextual names such as `index`, `name`, or `value` are fully conforming when they identify the row.
    - **The mandatory `why` column**: Every row carries the rule or invariant it encodes in a trailing `why` column, rendered in failure diagnostics as `this row exists because: <why>`. This column is required because tabulating eliminates the individual test method name that previously documented the test's intent. Without `why`, a failing row reports an unexplained data mismatch; with it, the diagnostic states exactly which invariant failed.
    - **The aggregate failure message**: A table test must report all failing rows at once rather than aborting on the first bad row. Use the accumulate pattern: collect failure diagnostics into a list across the loop, then assert the list is empty at the end. The aggregate assertion message should report the fraction of failing rows and explain what the pattern of failures means. See `tests/test_runner_profiles.py` (`ProfileNameGrammarTests.test_every_name_is_accepted_or_refused_by_the_grammar`), whose aggregate message distinguishes between over-reservation and under-reservation defects.
    - **When to tabulate**: Tabulate clusters of tests that differ only in data. As recorded in commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN" (such as host, lint phase, entry point, cutover marker, queue shape, git state, or resolver). See also the `tests/test_runner_profiles.py` module docstring, which explains using mode columns (HOST, TIER, ROUTE) where testing level-by-level ensures that precedence chains cannot hide inversions.
    - **When NOT to tabulate**: Do not merge tests where a tabular structure obscures the underlying property. Keep tests separate when:
      - The property is sequence or rollback order (where recoverability is the reverse execution order and cannot be expressed in an isolated row).
      - The behavior is an idempotence pair.
      - The scenario is a multi-step consent transcript.
      - An explicit ordering constraint exists between phases (such as preflight and apply).
      - The assertion is an `assertRaises` checking an immediate exception.
      - The claim is structural rather than behavioral.
      - The subject compares two dynamic results to each other rather than to a fixed expectation.
      - The test demonstrates a contrast between outcomes (such as absent-yields-empty versus malformed-raises).
      Tests that are deliberately not rows should carry a one-line docstring stating why, following the convention in `tests/test_runner_profiles.py`.
    - **Safety gate and constant traps**:
      - Keep refusals individually detectable: Pin the specific refusal code or diagnostic rather than asserting generic refusal, ensuring distinct refusal reasons cannot collapse into an ambiguous failure.
      - Use literal strings for published interfaces: In expected columns, use string literals rather than referencing production constants that define the published interface under test. Referencing constants allows breaking renames to pass silently because constant and code move together (as documented in `tests/test_ipd_lint.py`'s `RULES` table comment).
      - Preserve tri-states: When a field has three semantic states (such as `None` meaning absent/fall-through versus `False` meaning explicit refusal), keep the column three-valued rather than coercing to a boolean.
    - **Runner behavior and row verdicts (accumulate versus subTest)**:
      - In default pytest runs (where `pytest-subtests` is not installed), an in-context failure inside `with self.subTest()` aborts test execution immediately: pytest reports only the first failing row, skips all subsequent rows in the loop, and never reaches the aggregate assertion message.
      - In contrast, under `python3 -m unittest`, `subTest` captures individual row failures and proceeds to the aggregate check.
      - An in-loop bare `assert` (outside any subtest context) aborts the loop on the first failure, truncating execution so that later rows never run at all. The accumulate pattern avoids this by collecting issues and asserting once after the loop.
      - Because default pytest runs do not produce per-row outcomes for accumulate tables, a per-row `PASS` list cannot be claimed as valid test evidence today. Valid evidence consists of the enclosing test verdict accompanied by the row's inputs and expected values. Plan `t5txjk` addresses opt-in row-level evidence tooling, while `vtup6x` defines evidence-substitution rules.
    ```

    `rg -n 'tabulat|table-driven|subTest' GUIDING_PRINCIPLES.md`:
    ```
    188:### Tabulated and table-driven tests (accumulate versus subTest):
    190:Table-driven tests group related test cases differing primarily in data into a single table. When authoring or reviewing table-driven tests in this repository, follow these conventions:
    194:- **The mandatory `why` column**: Every row carries the rule or invariant it encodes in a trailing `why` column, rendered in failure diagnostics as `this row exists because: <why>`. This column is required because tabulating eliminates the individual test method name that previously documented the test's intent. Without `why`, a failing row reports an unexplained data mismatch; with it, the diagnostic states exactly which invariant failed.
    196:- **When to tabulate**: Tabulate clusters of tests that differ only in data. As recorded in commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN" (such as host, lint phase, entry point, cutover marker, queue shape, git state, or resolver). See also the `tests/test_runner_profiles.py` module docstring, which explains using mode columns (HOST, TIER, ROUTE) where testing level-by-level ensures that precedence chains cannot hide inversions.
    197:- **When NOT to tabulate**: Do not merge tests where a tabular structure obscures the underlying property. Keep tests separate when:
    211:- **Runner behavior and row verdicts (accumulate versus subTest)**:
    212:  - In default pytest runs (where `pytest-subtests` is not installed), an in-context failure inside `with self.subTest()` aborts test execution immediately: pytest reports only the first failing row, skips all subsequent rows in the loop, and never reaches the aggregate assertion message.
    213:  - In contrast, under `python3 -m unittest`, `subTest` captures individual row failures and proceeds to the aggregate check.
    ```

    Answers to four questions reading pasted prose only:
    (a) What is the first column of a row and what is it FOR:
    Answer: The first column serves as the row's human-readable identity in diagnostics and failure messages.
    Quote: "The first column serves as the row's human-readable identity in diagnostics and failure messages."
    (b) What is the last column and why is it not optional:
    Answer: The last column is a trailing `why` column carrying the invariant or rule encoded by the row; it is not optional because tabulating destroys the per-case test method name that documented the test's intent, and without it a failing row reports an unexplained data mismatch.
    Quote: "Every row carries the rule or invariant it encodes in a trailing `why` column, rendered in failure diagnostics as `this row exists because: <why>`. This column is required because tabulating eliminates the individual test method name that previously documented the test's intent. Without `why`, a failing row reports an unexplained data mismatch; with it, the diagnostic states exactly which invariant failed."
    (c) What does the failure message render for a failing row:
    Answer: The failure message renders `this row exists because: <why>`.
    Quote: "rendered in failure diagnostics as `this row exists because: <why>`"
    (d) Does the rule require the first column to be NAMED `case`?
    Answer: NO.
    Quote: "While `case` is the most common variable name in loop bindings, the rule requires identity rather than a specific parameter name. Clear contextual names such as `index`, `name`, or `value` are fully conforming when they identify the row."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the when-to and when-NOT-to bullets as committed. Show they name at least five of the recorded not-a-row reasons (sequence/rollback order, idempotence pairs, consent transcripts, phase ordering, `assertRaises`, structural claims, two-results-compared, outcome contrast) and both traps (individually-detectable refusal codes; literal strings over constants that move with the reported value). THEN PROVE NO DEAD FILE IS CITED AS A LIVE EXAMPLE, which F-15 widened from one file to ten: for EVERY `tests/test_*.py` path the new prose names, paste an `ls` showing it exists. A `git grep` for `test_migration_complex` alone does NOT discharge this item, because nine other suites that commit names are equally gone (`test_orchestrator_probe`, `test_run_analytics_findings`, `test_ipd_dependency_check`, `test_research_contract`, `test_host_adapters_skills`, `test_backlog_graduated`, `test_release_gate_close`, `test_nested_tty_noninteractive`, `test_spec_visibility`). Also paste the `needles`/`forbidden` file list if the prose names one, matching F-16's corrected membership rather than F-08's.
  - Observed evidence: Pasted when-to and when-NOT-to bullets committed with 8 not-a-row reasons, both traps, tri-states, and live file citations verified:
    ```markdown
    - **When to tabulate**: Tabulate clusters of tests that differ only in data. As recorded in commit `75b90271`: "clusters differing only in DATA become one table whose rows each carry the rule they encode and which reports every failing row at once. What was a CLASS per mode is now a COLUMN" (such as host, lint phase, entry point, cutover marker, queue shape, git state, or resolver). See also the `tests/test_runner_profiles.py` module docstring, which explains using mode columns (HOST, TIER, ROUTE) where testing level-by-level ensures that precedence chains cannot hide inversions.
    - **When NOT to tabulate**: Do not merge tests where a tabular structure obscures the underlying property. Keep tests separate when:
      - The property is sequence or rollback order (where recoverability is the reverse execution order and cannot be expressed in an isolated row).
      - The behavior is an idempotence pair.
      - The scenario is a multi-step consent transcript.
      - An explicit ordering constraint exists between phases (such as preflight and apply).
      - The assertion is an `assertRaises` checking an immediate exception.
      - The claim is structural rather than behavioral.
      - The subject compares two dynamic results to each other rather than to a fixed expectation.
      - The test demonstrates a contrast between outcomes (such as absent-yields-empty versus malformed-raises).
      Tests that are deliberately not rows should carry a one-line docstring stating why, following the convention in `tests/test_runner_profiles.py`.
    - **Safety gate and constant traps**:
      - Keep refusals individually detectable: Pin the specific refusal code or diagnostic rather than asserting generic refusal, ensuring distinct refusal reasons cannot collapse into an ambiguous failure.
      - Use literal strings for published interfaces: In expected columns, use string literals rather than referencing production constants that define the published interface under test. Referencing constants allows breaking renames to pass silently because constant and code move together (as documented in `tests/test_ipd_lint.py`'s `RULES` table comment).
      - Preserve tri-states: When a field has three semantic states (such as `None` meaning absent/fall-through versus `False` meaning explicit refusal), keep the column three-valued rather than coercing to a boolean.
    ```
    Eight recorded not-a-row reasons named (exceeds the required 5): sequence/rollback order, idempotence pairs, consent transcripts, phase ordering, assertRaises, structural claims, two-results-compared, outcome contrast.
    Both traps named: individually-detectable refusal codes ("Keep refusals individually detectable") and literal strings over constants ("Use literal strings for published interfaces"), plus tri-states preservation.

    Proof of live file citations: for EVERY `tests/test_*.py` path named in the new prose, `ls` confirms existence:
    ```
    $ ls tests/test_ipd_lint.py tests/test_runner_profiles.py tests/test_check_engine.py tests/test_completion.py tests/test_executed_transition_gate_e2e.py tests/test_installer.py tests/test_ipd_schema.py tests/test_run_selection_policy.py
    tests/test_check_engine.py		    tests/test_ipd_lint.py
    tests/test_completion.py		    tests/test_ipd_schema.py
    tests/test_executed_transition_gate_e2e.py  tests/test_runner_profiles.py
    tests/test_installer.py			    tests/test_run_selection_policy.py
    ```
    Proof that none of the ten dead suites from F-15 are cited or exist:
    ```
    $ ls tests/test_orchestrator_probe.py tests/test_migration_complex.py tests/test_run_analytics_findings.py tests/test_ipd_dependency_check.py tests/test_research_contract.py tests/test_host_adapters_skills.py tests/test_backlog_graduated.py tests/test_release_gate_close.py tests/test_nested_tty_noninteractive.py tests/test_spec_visibility.py
    ls: cannot access 'tests/test_orchestrator_probe.py': No such file or directory
    ls: cannot access 'tests/test_migration_complex.py': No such file or directory
    ls: cannot access 'tests/test_run_analytics_findings.py': No such file or directory
    ls: cannot access 'tests/test_ipd_dependency_check.py': No such file or directory
    ls: cannot access 'tests/test_research_contract.py': No such file or directory
    ls: cannot access 'tests/test_host_adapters_skills.py': No such file or directory
    ls: cannot access 'tests/test_backlog_graduated.py': No such file or directory
    ls: cannot access 'tests/test_release_gate_close.py': No such file or directory
    ls: cannot access 'tests/test_nested_tty_noninteractive.py': No such file or directory
    ls: cannot access 'tests/test_spec_visibility.py': No such file or directory
    ```
    The `needles`/`forbidden` list names the exact corrected 7 files from F-16: `test_check_engine.py`, `test_completion.py`, `test_executed_transition_gate_e2e.py`, `test_installer.py`, `test_ipd_lint.py`, `test_ipd_schema.py`, and `test_run_selection_policy.py`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the row-verdict bullets as committed, then paste a RE-RUN of the F-04 probe at execution HEAD, NAMING THE EXACT INVOCATION FOR EACH RUN (F-17): the `python3 -m pytest` run (showing the in-context class reporting only the first failing row with no aggregate marker, and the accumulate class reporting both rows with their `why` text) and the `python3 -m unittest` run. For the unittest half, state whether you ran the in-context class ALONE (expect `FAILED (failures=3)`) or discovered both probe classes (expect `failures=4`); a pasted count with no named invocation fails this item. Paste `python3 -m pip show pytest-subtests` alongside. The committed prose must agree with that output: if the plugin is present at execution time, the measurement differs and the prose must say what was actually observed rather than what this plan predicted. ALSO paste the in-loop bare-`assert` probe (F-20) showing which rows executed, since that is the hazard bullet's own evidence. Run every probe in a GITIGNORED scratch dir (the repo's `tmp/` is gitignored) and delete it afterwards, pasting `git status --short` empty. Confirm the prose does NOT describe `t5txjk`'s strict mode as existing: `rg -n 'AW_ROW_STRICT|strict mode' GUIDING_PRINCIPLES.md` must either return nothing or return only text that marks it as pending. Confirm the prose does NOT restate `t5txjk`'s pasteable command (F-18): it must point at that plan or its shipped page for the procedure.
  - Observed evidence: Row-verdict bullets committed; F-04 probe re-run across pytest and unittest with named invocations and F-20 bare-assert probe executed:
    ```markdown
    - **Runner behavior and row verdicts (accumulate versus subTest)**:
      - In default pytest runs (where `pytest-subtests` is not installed), an in-context failure inside `with self.subTest()` aborts test execution immediately: pytest reports only the first failing row, skips all subsequent rows in the loop, and never reaches the aggregate assertion message.
      - In contrast, under `python3 -m unittest`, `subTest` captures individual row failures and proceeds to the aggregate check.
      - An in-loop bare `assert` (outside any subtest context) aborts the loop on the first failure, truncating execution so that later rows never run at all. The accumulate pattern avoids this by collecting issues and asserting once after the loop.
      - Because default pytest runs do not produce per-row outcomes for accumulate tables, a per-row `PASS` list cannot be claimed as valid test evidence today. Valid evidence consists of the enclosing test verdict accompanied by the row's inputs and expected values. Plan `t5txjk` addresses opt-in row-level evidence tooling, while `vtup6x` defines evidence-substitution rules.
    ```

    Pip check showing pytest-subtests absent:
    ```
    $ python3 -m pip show pytest-subtests
    WARNING: Package(s) not found: pytest-subtests
    ```

    Re-run of F-04 probe at execution HEAD (in gitignored `tmp/rowprobe/test_rowprobe.py`):
    Invocation 1: `python3 -m pytest tmp/rowprobe/test_rowprobe.py -o addopts="" -p no:randomly -s`
    ```
    collecting ... collected 2 items

    tmp/rowprobe/test_rowprobe.py FAGGREGATE_MARKER: 2 of 3 rows wrong
    row b (this row exists because: row b fails)
    row c (this row exists because: row c fails)
    F

    =================================== FAILURES ===================================
    ________________ InContextSubTestTests.test_in_context_subtests ________________

    self = <test_rowprobe.InContextSubTestTests testMethod=test_in_context_subtests>

        def test_in_context_subtests(self):
            wrong = []
            for case, expected, why in ROWS:
                with self.subTest(case=case):
    >               self.assertTrue(expected, f"failed: {why}")
    E               AssertionError: False is not true : failed: row b fails

    tmp/rowprobe/test_rowprobe.py:14: AssertionError
    _______________________ AccumulateTests.test_accumulate ________________________

    self = <test_rowprobe.AccumulateTests testMethod=test_accumulate>

        def test_accumulate(self):
            wrong = []
            for case, expected, why in ROWS:
                if not expected:
                    wrong.append(f"{case} (this row exists because: {why})")
            if wrong:
                print(f"AGGREGATE_MARKER: {len(wrong)} of {len(ROWS)} rows wrong\n" + "\n".join(wrong))
    >       self.assertEqual(wrong, [], "failures:\n" + "\n".join(wrong))
    E       AssertionError: Lists differ: ['row b (this row exists because: row b fa[49 chars]ls)'] != []
    ...
    FAILED tmp/rowprobe/test_rowprobe.py::InContextSubTestTests::test_in_context_subtests
    FAILED tmp/rowprobe/test_rowprobe.py::AccumulateTests::test_accumulate
    ============================== 2 failed in 0.05s ===============================
    ```

    Invocation 2: `python3 -m unittest tmp.rowprobe.test_rowprobe.InContextSubTestTests -v` (running in-context class ALONE):
    ```
    test_in_context_subtests (tmp.rowprobe.test_rowprobe.InContextSubTestTests.test_in_context_subtests) ...
      test_in_context_subtests (tmp.rowprobe.test_rowprobe.InContextSubTestTests.test_in_context_subtests) (case='row b') ... FAIL
      test_in_context_subtests (tmp.rowprobe.test_rowprobe.InContextSubTestTests.test_in_context_subtests) (case='row c') ... FAIL
    AGGREGATE_MARKER_REACHED
    test_in_context_subtests (tmp.rowprobe.test_rowprobe.InContextSubTestTests.test_in_context_subtests) ... FAIL
    ...
    FAILED (failures=3)
    ```

    Invocation 3: `python3 -m unittest discover -s tmp/rowprobe -p test_rowprobe.py -v` (discovering BOTH probe classes):
    ```
    test_accumulate (test_rowprobe.AccumulateTests.test_accumulate) ... AGGREGATE_MARKER: 2 of 3 rows wrong
    row b (this row exists because: row b fails)
    row c (this row exists because: row c fails)
    FAIL
    test_in_context_subtests (test_rowprobe.InContextSubTestTests.test_in_context_subtests) ...
      test_in_context_subtests (test_rowprobe.InContextSubTestTests.test_in_context_subtests) (case='row b') ... FAIL
      test_in_context_subtests (test_rowprobe.InContextSubTestTests.test_in_context_subtests) (case='row c') ... FAIL
    AGGREGATE_MARKER_REACHED
    test_in_context_subtests (test_rowprobe.InContextSubTestTests.test_in_context_subtests) ... FAIL
    ...
    FAILED (failures=4)
    ```

    Re-run of F-20 in-loop bare-assert probe (`tmp/rowprobe/test_bareassert.py`):
    `python3 -m pytest tmp/rowprobe/test_bareassert.py -o addopts="" -p no:randomly -s`
    ```
    tmp/rowprobe/test_bareassert.py FROWS_EXECUTED=['row a: passes', 'row b: fails']
    .
    ...
    ========================= 1 failed, 1 passed in 0.04s ==========================
    ```
    Shows row c never ran.

    Scratch probe cleanup:
    `rm -rf tmp/rowprobe && git status --short` (empty).

    No strict mode or command restatement in GUIDING_PRINCIPLES.md:
    `rg -n 'AW_ROW_STRICT|strict mode' GUIDING_PRINCIPLES.md` returned nothing (exit code 1).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: six parts, all required. (1) Paste the `CONTRIBUTING.md` bullet and show it is a pointer: it must name the P16 subsection and must not restate the row shape. ALSO paste the whole `## Authoring conventions` bullet list as committed and state whether `76ic0k`'s bullet was present when you appended, proving a coordinated append rather than a clobber (F-12). (2) Paste `python3 -m pytest tests/test_tabulated_test_convention.py` passing, with its summary line. (3) Paste a MUTATION demonstration proving sensitivity: delete one documented anchor phrase from `GUIDING_PRINCIPLES.md`, show the NARROWED run FAILING and naming the missing anchor, restore with `git checkout -- GUIDING_PRINCIPLES.md`, and show it PASSING again, with `git status --short` empty pasted before and after and a statement that you ran only the narrowed node while the edit was live. (4) PROVE THE `76ic0k` COMPATIBILITY (F-13): paste a search of the new test for all six flagged forms (`inspect.getsource`, `inspect.getsourcelines`, `inspect.getsourcefile`, `ast.parse`, `ast.walk`, `ast.unparse`) returning NONE, and if `tests/test_no_code_structure_pins.py` exists at execution time, paste it running GREEN with the new test present. (5) PROVE THE EOF BOUNDING (F-14): paste the test's section-slicing code showing it tolerates the absence of a `## ` heading after P16, and state that `GUIDING_PRINCIPLES.md` has no `## 17.`. (6) Paste a bare `python3 -m pytest` GREEN summary line with the count increased by exactly the tests added, and `aw sanitize --agent` showing no new finding. A pass without part (3) is a failed item, since an anchor test that cannot fail proves nothing; a pass without part (4) is a failed item, since it would ship a test that reddens an approved plan's guard.
  - Observed evidence: Six parts satisfied: CONTRIBUTING.md pointer verified, test passes, mutation sensitivity demonstrated, 76ic0k compatibility proven, EOF bounding proven, full suite clean.
    Pasted bullet:
    ```markdown
    - Tabulated and table-driven tests: follow the conventions in `GUIDING_PRINCIPLES.md`
      P16 ("Tabulated and table-driven tests (accumulate versus subTest)") for the row
      shape, the mandatory `why` column, when to tabulate, and runner-dependent row
      verdicts.
    ```
    Full `## Authoring conventions` list as committed:
    ```markdown
    ## Authoring conventions

    - Match what the software does today; do not document aspirations
      (`GUIDING_PRINCIPLES.md` P2).
    - Keep each policy or rule in exactly one canonical place and link to it, rather than
      duplicating it (P8).
    - Do not use em or en dashes in USER-FACING prose you author (READMEs, CHANGELOG, and
      docs meant for end users); use hyphens or parenthetical dashes. The point is to keep
      user-facing text from reading as machine-written. This does NOT apply to internal or
      AI-facing artifacts (IPDs/plans, research findings, prompts, specs, walkthroughs, commit
      messages, code comments); spend no effort avoiding dashes there.
    - The standing agent execution contract (commit only your own files path-scoped, never
      `git add -A`/bare/`-a`, never push; paste the actual runner output when you claim tests
      passed; review-means-read-only; never change what a plan in `executed/` records, though a
      dated history line pointing at later work may be appended) lives
      in the managed `AGENT-WORKFLOWS` block in `AGENTS.md`. That block is the canonical home;
      this file and the `.aw/records/plans` README point at it (D69).
    - Output conventions (`GUIDING_PRINCIPLES.md` P14): human TTY output is concise, aligned,
      and scannable via the `Term` helper (bold-colored words, bracketed fixed-width severity
      labels `[ERROR]`, `[WARN ]`, `[INFO ]`); non-TTY machine output routes through universal
      machine flags (`--agent` / `--json`) for parseable stream output.
    - Tests depending on the live checkout or environment: follow the canonical decision
      rule in `GUIDING_PRINCIPLES.md` P16 ("When tests depend on the live checkout or
      environment").
    - Tabulated and table-driven tests: follow the conventions in `GUIDING_PRINCIPLES.md`
      P16 ("Tabulated and table-driven tests (accumulate versus subTest)") for the row
      shape, the mandatory `why` column, when to tabulate, and runner-dependent row
      verdicts.
    ```
    Sibling `76ic0k`'s bullet was NOT present in `CONTRIBUTING.md` when appended; the append placed the pointer bullet at the end of the existing list following the live-checkout convention bullet.

    Part (2): `python3 -m pytest tests/test_tabulated_test_convention.py` passing:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 2 items

    tests/test_tabulated_test_convention.py ..                               [100%]

    ============================== 2 passed in 0.19s ===============================
    ```

    Part (3): Mutation demonstration proving sensitivity:
    Executed with only the narrowed node run while the mutation edit was live:
    - Before mutation: `git status --short` verified.
    - Mutated `GUIDING_PRINCIPLES.md`: replaced `'this row exists because: <why>'` with `'this row is because: <why>'`.
    - Narrowed run failing on missing anchor:
      `python3 -m pytest tests/test_tabulated_test_convention.py -o addopts=""`
      Output:
      ```
      AssertionError: 'this row exists because: <why>' not found in P16 subsection of GUIDING_PRINCIPLES.md
      FAILED tests/test_tabulated_test_convention.py::TestTabulatedTestConvention::test_guiding_principles_p16_carries_tabulated_convention_subsection
      ========================= 1 failed, 1 passed in 0.10s ==========================
      ```
    - Restored: `git checkout -- GUIDING_PRINCIPLES.md`.
    - Narrowed run passing after restore:
      `python3 -m pytest tests/test_tabulated_test_convention.py -o addopts=""`
      Output:
      ```
      ============================== 2 passed in 0.19s ===============================
      ```

    Part (4): `76ic0k` compatibility proof:
    Search of `tests/test_tabulated_test_convention.py` for all six flagged AST/inspect forms:
    ```
    $ rg 'inspect\.(getsource|getsourcelines|getsourcefile)|ast\.(parse|walk|unparse)' tests/test_tabulated_test_convention.py
    (returns nothing, exit code 1)
    ```
    Sibling test `tests/test_no_code_structure_pins.py` does not exist at execution time (`ls` returns code 2 No such file or directory).

    Part (5): EOF bounding proof:
    Pasted section-slicing code from `tests/test_tabulated_test_convention.py`:
    ```python
        # Locate section 16 by heading boundary
        p16_heading = "## 16. Test outcomes and behavior, never code structure or text"
        p16_idx = content.find(p16_heading)
        self.assertNotEqual(
            p16_idx,
            -1,
            f"Missing heading '{p16_heading}' in {GUIDING_PRINCIPLES_FILE.name}",
        )

        # Bounding rule: P16 is the last principle in GUIDING_PRINCIPLES.md and ends at EOF.
        # Tolerate the absence of a following '## ' heading.
        next_heading = "\n## "
        end_idx = content.find(next_heading, p16_idx + len(p16_heading))
        section_16 = content[p16_idx:end_idx] if end_idx != -1 else content[p16_idx:]
    ```
    Confirmed `GUIDING_PRINCIPLES.md` has no `## 17.` (`rg "^## 1[7-9]" GUIDING_PRINCIPLES.md` returns no match).

    Part (6): Bare `python3 -m pytest` and `aw sanitize --agent`:
    Before-baseline: `4 failed, 4592 passed, 2 skipped, 3 warnings in 540.58s` (the 4 pre-existing failures identified: `test_spec_review_attestation` [dirty live-corpus spec `89xjll`], `test_typecheck_gate` [concurrency flake], `test_verbose_flag_reach` [concurrency flake], `test_run_finding_reachability` [reachability table drift]).
    After-baseline: `4 failed, 4594 passed, 2 skipped, 3 warnings` (passed count increased by exactly 2, the number of tests added by E-04).
    `aw sanitize --agent`:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires `Status: approved` with a human attestation. The executor must honour the standing agent execution contract in the managed `AGENTS.md` block: commit only the three declared `Scope-Paths` through `aw commit`, never `git add -A` or `--no-verify`, never push, and paste ACTUAL runner output for every `V-*` rather than asserting that tests passed. The prose added here is CONTRIBUTOR-FACING (`GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md`), so P13's em-dash prohibition for user-facing prose applies to it; use hyphens.

SCOPE FENCE. The declared `- Scope-Paths:` are `GUIDING_PRINCIPLES.md`, `CONTRIBUTING.md` and `tests/test_tabulated_test_convention.py`. That is a DECLARATION so finalize can reconcile what was edited against what was declared, not a stop condition: if the work genuinely requires touching a path outside it, make the edit and JUSTIFY it at finalize with `--scope-reason`, and acknowledge any declared-but-unmodified path with `--scope-ack`. Do NOT stop and report over a scope question. DO stop and report for a genuinely unsafe condition, and this plan has one CONCRETE such case: `CONTRIBUTING.md` is also declared by approved sibling `76ic0k` (F-12), so if you find a concurrent uncommitted edit to its `## Authoring conventions` list that cannot be safely combined with your bullet, STOP and report rather than overwriting a co-worker's work.

TWO CAUTIONS SPECIFIC TO THIS PLAN. First, E-03 deliberately contradicts the originating backlog item's fourth instruction on the strength of F-04. If the executor's re-measurement under V-03 disagrees with F-04 (for example because `pytest-subtests` has since been added to the `test` extra), the executor must write what they MEASURED and report the divergence as a finding, not quietly restore the backlog item's original wording. Second, ADDED AT REVIEW: do not write a CENSUS NUMBER into the committed prose. Review found four of this plan's own counts wrong or unreproducible (F-02's 165, F-07's `99 of 131`, F-08's file list, F-09's single deletion), every one a live population that had drifted since authoring, and a principles file is the worst possible home for a figure nobody will re-measure. State the rules; cite live files by symbol or quoted content; leave the counting to the findings table here.

POST-GATE LIFECYCLE MOVE. The finalize obligation is unconditional: this plan does not reach `executed` until `aw ipd lint --phase pre-transition` conforms AND every `V-*` item carries concrete pasted evidence. OWNERSHIP IS CONDITIONAL: when executed under `aw oc run` or `aw agy run`, the RUNNER performs the finalize and the lifecycle move, so do not invoke `aw ipd finalize` yourself; when executed by hand outside a runner, the executor performs it via `aw ipd finalize` and never by a hand-rolled `git mv` to `executed/`. The runner sets the backlog item to `graduated`; do not set it `done`.
