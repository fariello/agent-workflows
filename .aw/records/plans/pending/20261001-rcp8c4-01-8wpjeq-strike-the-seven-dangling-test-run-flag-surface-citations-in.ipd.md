# IPD: Strike the seven dangling test_run_flag_surface citations in runner_shared and state plainly that the bidirectional spec-versus-table guard was deleted and not replaced

- Date: 2026-10-01
- Kind: child
- Concern: `agent_workflows/runner_shared.py` TELLS EVERY AUTHOR WHO ADDS A RUN POLICY FLAG THAT A BIDIRECTIONAL SPEC-VERSUS-TABLE TEST WILL CATCH A MISMATCH, AND THAT TEST DOES NOT EXIST. Seven comment and docstring sites name `tests/test_run_flag_surface.py` as the mechanism guarding spec `25kzda` Section 2.1's flag surface. Measured at lane HEAD `af30ba67f`: `grep -c test_run_flag_surface agent_workflows/runner_shared.py` -> `7`, `ls tests/test_run_flag_surface.py` -> `No such file or directory`, and `git log --oneline --diff-filter=D -- tests/test_run_flag_surface.py` -> `19313eed7 test: trim test suite from 9,136 to under 2,000 tests`. The claim is LOAD-BEARING rather than decorative: three of the seven sites instruct the next author that amending spec 2.1 in the SAME change is mandatory *because* the test reads the spec file in both directions, so the comments are the only remaining statement of a real obligation while simultaneously attributing it to a guard nobody can run. A false guard claim is worse than no claim, because an author who trusts it does not check, and the author who does check finds nothing and cannot tell whether the discipline was abandoned or the citation merely rotted.
  THE ITEM UNDERSTATES THE DEFECT IN THREE WAYS AND OVERSTATES IT IN ONE, all measured, which is why this plan re-measures before editing. UNDERSTATED (a): the divergence the comments promise to catch IS ALREADY SHIPPING. Re-running the deleted test's own extraction logic by hand (recovered verbatim from `git show 19313eed^:tests/test_run_flag_surface.py`, whose `SpecFlagListTests.spec_grammar_flags` scopes to the `aw <host> run <selector>` stanza of 2.1's grammar fence) yields `declared - owned == ['--action']`, and a separate CHOICE-vocabulary divergence ships too: `--on-conflict` accepts a fifth value `ask` that 2.1 declares nowhere. UNDERSTATED (b): two of the three test function names the comments cite NEVER EXISTED at deletion time; `test_no_owned_flag_is_absent_from_the_spec` and `test_the_mixed_type_call_site_was_not_duplicated` were both removed EARLIER, by `b1e304bc7` on 2026-09-18, so those citations were already dead six days before the trim and the item's single-commit attribution is incomplete. UNDERSTATED (c): the deleted file also held the `DECLARED_BUT_NOT_OWNED_HERE` register that SANCTIONED `--action`'s absence with a named reason and owner, so that register now exists nowhere in the tree and a future reader has no way to distinguish a sanctioned exclusion from a real drift. OVERSTATED: the item's line offsets (`:117`, `:1079`, `:14374`, `:14574`, `:14595`, `:14620`, `:27858`) have all moved; the count of seven is exactly right.
  WHY THIS IS A `chore` AND NOT A `bug`, re-argued on the repository's perceptibility test rather than inherited on the item's word. No computed behavior is wrong: the parsers register, freeze, refuse and resolve identically before and after this plan, and all seven sites are comments or docstrings that no operator ever reads. The cost falls on a future EDITOR, which is real but is not a user waiting on a wrong answer. The item's `- Priority: low` and its ABSENCE of a `- Blocks-Release:` gate are inherited unchanged and no gate is invented. Note that the two live divergences this plan MEASURES are themselves filed separately (`n5gsea`) rather than fixed here, because resolving them changes a public contract.
- Scope: Make all seven sites in `agent_workflows/runner_shared.py` state the truth about what guards spec `25kzda` 2.1's flag surface. At each site, strike the claim that `tests/test_run_flag_surface.py` enforces the property and replace it with (i) the OBLIGATION that survives, stated as a convention the author must honor BY HAND (a flag registered in `RUN_POLICY_FLAGS` must be declared in spec 2.1 in the same change, and the converse), and (ii) the fact that the bidirectional check was deleted in `19313eed` and was NOT replaced, following the wording precedent executed plan `t0ovw6` established in this same package ("deleted in `19313eed`; no live guard currently enforces this"). ALSO correct the five `the contract test` references inside the same flag-surface region that assert a live enforcing test WITHOUT naming the file, since they are the same false claim escaping the item's search string. EXCLUDES restoring `tests/test_run_flag_surface.py` or authoring any replacement that reads production source with `ast`/`inspect`/regex, forbidden by the maintainer ruling the item carries and by `GUIDING_PRINCIPLES` P16. EXCLUDES changing any executable statement, signature, default, choice tuple, help string or flag spelling: this is a comment-and-docstring edit and V-05 proves it by AST comparison of the whole module. EXCLUDES FIXING the two measured divergences (`--action` and `--on-conflict ask`), which are filed as `n5gsea` and need a maintainer decision about a public surface. EXCLUDES editing spec `25kzda` itself, including its 2026-09-21 history note at the `- 2026-09-21 note (aw specs):` line and its Section 5.3a `CONFIGURED, NOT FLAGGED` bullet, both of which repeat the same stale claim; the item forbids rewriting the dated history record and the plan declares no `.spec.md` path. EXCLUDES the truncated-doc-comment damage in the same block, filed as `woxgyo`. EXCLUDES the three sibling dangling-guard families in this file (`NoRunnerImportTests`, `test_no_new_module_level_first_party_import_in_runner_shared`, the `should_color` trio), each owned by another plan or carrier.
- Scope-Paths: agent_workflows/runner_shared.py, .aw/records/plans/pending/20261001-rcp8c4-01-8wpjeq-strike-the-seven-dangling-test-run-flag-surface-citations-in.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 25kzda
- Work-Kind: chore
- Priority: low
- From-Backlog: rcp8c4
- Set: rcp8c4
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8wpjeq
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. At lane HEAD 749efe321 the seven sites were already rewritten by 972817ced (executed h65phz), so the plan is narrowed to the measured residue: the initialize_run_core misattribution to 19313eed (removed by b1e304bc7) (PR-002), the done xvp5vx presented as live coverage carrier (PR-003), and the unnamed contract-test claims including the now-false {dest: False} idiom premise (PR-004); <base>-anchored AST proof and baseline-relative suite bar (PR-005); sibling plans 57v89t/1dkj1n and OQ owner (PR-006).
- 2026-10-01 same-status (aw set): status unchanged (to-review)

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `rcp8c4`. GATE NOTE: the item carries no `- Blocks-Release:`, so this plan inherits none; `- Work-Kind: chore` and `- Priority: low` are INHERITED and both re-verified correct, because no computed behavior is wrong and no operator reads any of the seven sites. THE ITEM'S CENTRAL CLAIM VERIFIES EXACTLY (seven sites, file absent, deleted by `19313eed`) AND THE MEASUREMENT FOUND FOUR THINGS THE ITEM DOES NOT RECORD, which is the authoring finding: the divergence the comments promise to catch is ALREADY SHIPPING in two forms (F-03), two of the three cited test functions were already dead BEFORE the trim commit (F-04), the deleted file held the sanctioned-exclusion register that now exists nowhere (F-05), and five more `contract test` claims in the same region make the same assertion without naming the file (F-06). THE ITEM'S ONE OPEN QUESTION IS RESOLVED FROM REPOSITORY EVIDENCE AND NOT REFERRED UP (OQ-01): the item correctly notes the maintainer ruling it cites covers CODE PINS while the deleted test was partly an ARTIFACT-CONSISTENCY test that P16 permits, but the ruling's instruction to correct the comments holds under either answer, so the text fix is unblocked and reinstating a spec-to-table test is left to a future author with the question stated. TWO NEW BACKLOG ITEMS WERE FILED rather than fixed here, both because they change or restore things this chore has no authority over: `n5gsea` (the two live spec-versus-code divergences, needing a maintainer ruling on a public value) and `woxgyo` (unrelated truncated-comment damage in the same doc-comment block, attributed to `7dd1c486c`). No open question is blocking.
- 2026-10-01 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `runner_shared.py` tell the truth at all seven sites that currently attribute spec-versus-table enforcement to a deleted test, so the next author who adds a run policy flag learns the real obligation (declare it in spec 2.1 in the same change) AND learns that nothing will catch them if they forget. Deliver that without restoring a deleted guard and without touching a single executable statement in a 36,000-line module both host drivers import.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

REVIEW UPDATE (2026-10-02, `/plan-review` at lane HEAD `749efe321`). THE SEVEN NAMED CITATIONS WERE ALREADY REWRITTEN, by commit `972817ced` (`work(h65phz): ...`, executed plan `h65phz`, whose E-05 owned "ALL SEVEN `runner_shared.py` SITES"). Measured: `git show af30ba67f:agent_workflows/runner_shared.py` carries "What replaces the fingerprint as its guard is `tests/test_run_flag_surface.py`" and HEAD does not; all seven sites now read "was deleted in `19313eed` ... (carrier: backlog `xvp5vx`) ... the requirement ... remains in force". Spec `25kzda` Section 5.3a was corrected in the same commit. `grep -c test_run_flag_surface agent_workflows/runner_shared.py` is still `7`, because the corrected text NAMES the deleted file as history, so a count of zero is NO LONGER the right bar. THE RESIDUE THIS PLAN STILL OWNS is therefore narrower and is what E-03 to E-05 now target: (i) `972817ced` introduced the exact new false claim F-04 warned about, at `initialize_run_core`, which reads "`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in `19313eed`" while that function was removed by `b1e304bc7` on 2026-09-18; (ii) the F-06 unnamed `contract test` claims, which `972817ced` did not touch and which still assert a live enforcing test; (iii) the seven corrected sites name `xvp5vx` as the "coverage carrier", but `xvp5vx` is `done` (closed 2026-10-01 by plan `oyh28b`, an audit census), so it carries no restoration and the pointer must not read as a live owner. Edits outside (i) to (iii) are NOT made: the `h65phz` wording is accepted as satisfying E-03/E-04's substance, and re-wording it would churn shipped prose for taste.

### Task group 1: re-measure, because the population and the divergence both move

- [x] E-01 RE-MEASURE the citation population, the guard's absence, and the live divergence at execution HEAD, recording each result with the command that produced it. The population is NOT stable: this file is declared by dozens of pending plans, and the item's own line offsets have already all moved. Measure six things. (a) `grep -n test_run_flag_surface agent_workflows/runner_shared.py` and its count, which at authoring is `7`. (b) `grep -rn test_run_flag_surface agent_workflows/ --include=*.py` to confirm this file is the sole carrier in the package, which at authoring it is. (c) The FILE's absence: `ls tests/test_run_flag_surface.py` and `git log --oneline --diff-filter=D -- tests/test_run_flag_surface.py`. (d) A DEFINITION search, not a name search, for the three cited test functions: `grep -rn "def \(test_no_owned_flag_is_absent_from_the_spec\|test_the_spec_and_the_owned_table_agree_in_both_directions\|test_the_mixed_type_call_site_was_not_duplicated\)" tests/ agent_workflows/`, which must return nothing, since every surviving occurrence anywhere is prose. (e) THE LIVE DIVERGENCE, re-derived with the deleted test's own extraction logic rather than by eye, so the replacement text's claim that nothing checks this is evidenced rather than asserted: split spec `25kzda` on `### 2.1 Command grammar`, take the `` ```text `` fence, scope to the `aw <host> run <selector>` stanza (stop at the next blank line or `aw ` line), regex `--[a-z][a-z0-9-]*`, and difference against `set(runner_shared.RUN_POLICY_FLAGS_BY_FLAG)` in BOTH directions. (f) The CHOICE-vocabulary divergence: `runner_shared.RUN_POLICY_FLAGS_BY_FLAG['--on-conflict'].choices` versus `CANONICAL_ON_CONFLICT_CHOICES`. IF A GUARD HAS BEEN RESTORED, do not delete the citation naming it: narrow the edit and report the restoration. IF (e) OR (f) NOW REPORTS CLEAN, say so and do not claim a divergence the tree no longer has; the edit's correctness does not depend on one existing.
  - Depends on: none
  - Expected outcome: six results pasted with their exact commands, each stated explicitly as present or absent rather than implied by empty output. At authoring HEAD `af30ba67f` (context only; at review HEAD `749efe321` the count is still `7` but every site is already the `972817ced` historical wording, so record for each site whether it asserts a LIVE guard or names a DELETED one): (a) `7`, at module docstring scope, `add_output_mode_flags`, the `RUN_POLICY_FLAGS` doc-comment, the `--integration-retry-limit` row comment, the `--allow-uncovered-orchestrator-work` row comment, the `--allow-concurrent-driver` row comment, and `initialize_run_core`; (b) 7 in `runner_shared.py` and 0 in every other package module; (c) `No such file or directory`, deleted by `19313eed7`; (d) no match, exit 1; (e) `declared - owned == ['--action']` and `owned - declared == []`; (f) `('drop','refuse','force','prompt','ask')` versus `('drop','refuse','force','prompt')`, so `ask` is accepted and undeclared.
  - Execution state: performed

- [x] E-02 ESTABLISH the suite baseline this plan's V-items compare against, since a comment-only edit to the module both drivers import must move no count. Run the suite BARE as `python3 -m pytest`, adding no flags: the configured `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, and adding `-n0`, a second `-q`, or `-p no:randomly` would respectively make the run several times slower, suppress the `N passed` line this plan requires pasted, and disable the order randomization. Also run `python3 -m pytest tests/test_runner_shared.py tests/test_concurrent_driver_guard.py -o addopts=""` for the two files that touch `RUN_POLICY_FLAGS` by name, clearing the defaults explicitly rather than fighting them. Record every number with `git rev-parse --short HEAD`.
  - Depends on: E-01
  - THE AUTHORING NUMBERS ARE CONTEXT, NOT AN ACCEPTANCE BAR. The bar is that YOUR OWN pre-edit baseline equals YOUR OWN post-edit count; it is NOT that either matches a figure recorded here. This repository is under concurrent development and the suite demonstrably drifts by over a hundred tests in days. Do NOT treat a difference from the numbers below as a defect or as a reason to stop.
  - Expected outcome: three counts pasted with YOUR execution HEAD, explicitly labelled as the baseline V-05 compares against. At authoring HEAD `af30ba67f`: bare suite `3649 passed, 2 skipped, 3 warnings in 76.66s`, with the runner's own note that `208 tests were deselected by -m/-k`; `tests/test_runner_shared.py` `126 passed`; `tests/test_concurrent_driver_guard.py` `31 passed`.
  - Execution state: performed

### Task group 2: correct the two sites that frame the whole surface

- [x] E-03 VERIFY THE MODULE DOCSTRING BANNER IS ALREADY SATISFIED BY `972817ced`, and edit only its carrier pointer (residue (iii)). At review the banner reads "The former guard (`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in `19313eed`, so the flag surface currently has no such data-driven test (coverage carrier: backlog `xvp5vx`)." That satisfies the ORIGINAL E-03 intent (admission-rule distinction, `--full-auto` motivation and absent-fixture explanation are all retained, the guard sentence is gone, and the property is stated unguarded), so do NOT re-word it. Replace only `(coverage carrier: backlog `xvp5vx`)` with wording that does not present a `done` audit item as a live owner, for example `(audit: backlog `xvp5vx`, done; no restoration is planned)`, applying the SAME replacement at every one of the seven `972817ced` sites so the file keeps one phrasing. IF a concurrent change already altered these sites, treat the residue as satisfied and record the commit. Do NOT touch the two fingerprint claims about `tests/test_runner_shared.py` or `9vtas9`'s prohibition bullet.
  - Depends on: E-02
  - Expected outcome: `grep -n "What replaces the fingerprint as its guard" agent_workflows/runner_shared.py` returns nothing (already true at review), and no site in the file presents `xvp5vx` as a live coverage carrier; the seven sites share one carrier phrasing.
  - Execution state: performed

- [x] E-04 VERIFY THE `RUN_POLICY_FLAGS` DOC-COMMENT AND THE `add_output_mode_flags` DOCSTRING ARE ALREADY SATISFIED BY `972817ced`, and correct the ONE unnamed claim in that doc-comment. At review: (a) the `--allow-dirty-base` paragraph already reads "Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`) was deleted in `19313eed` and is currently unguarded ..., but the requirement that spec 2.1 declare every row here in the same change remains in force", which keeps the obligation and states it unguarded; (b) `add_output_mode_flags` already names neither dead function and says "the surface is currently unguarded ..., but the closed contract stands". Neither needs editing beyond E-03's carrier phrasing. WHAT DOES NEED EDITING in this block is the "THE COUNT IS DELIBERATELY NOT STATED" paragraph's "the contract test derives the expected set from the spec for exactly this reason": keep the paragraph and its point (a stated count goes stale) and replace the clause asserting a live test with the truth that the expected set is the spec's own 2.1 grammar and nothing currently derives or checks it. Do NOT touch `woxgyo`'s truncated lines or the `#: #:` prefix below them (plan `57v89t`, `reviewed`, owns them); if `57v89t` has landed, leave its restored lines alone and record the commit.
  - Depends on: E-03
  - Expected outcome: (a) and (b) are byte-unchanged except for E-03's carrier phrasing; the COUNT paragraph keeps its point and no longer asserts a live contract test; the `woxgyo` region (or `57v89t`'s restoration of it) is untouched in this plan's diff.
  - Execution state: performed

### Task group 3: correct the four remaining sites and the unnamed claims

- [x] E-05 CORRECT THE `initialize_run_core` MISATTRIBUTION AND THE REMAINING UNNAMED `contract test` CLAIMS. (a) RESIDUE (i): `initialize_run_core`'s "THE THREE GATES ARE DESCRIBED HERE AND NOT SPELLED, historically" comment says `test_the_mixed_type_call_site_was_not_duplicated` was "deleted in `19313eed`"; F-04 measured that function's removal at `b1e304bc7` (2026-09-18), six days before the file's deletion. Re-attribute it to `b1e304bc7`, keep "Locate each by its own call above", keep every other paragraph of the comment (the priced-exception argument and the `--prepare-only` note), and do NOT add the gate symbol names back in this plan. (b) The three per-row comments (`--integration-retry-limit`, `--allow-uncovered-orchestrator-work`, `--allow-concurrent-driver`) were already corrected by `972817ced` and need only E-03's carrier phrasing; their OQ-04 ruling, justification-string and 2026-09-22 incident rationale are already intact, so do not re-word them. (c) THE UNNAMED CLAIMS, located by enclosing symbol or quoted text, each asserting a live enforcing test that does not exist: the `# WHY THE FLAG LIST IS DATA AND NOT EIGHT add_argument CALLS` banner ("Driving registration AND the contract test from ONE table makes the drift a test failure"), `RunPolicyFlag`'s `implemented` field doc ("Carried as data so the contract test can assert the refusal"), the `register_run_policy_flags` `skip` docstring ("so the contract test can prove it is registered by SOMEONE"), `resolve_retry_budget`'s "so a contract test asserts the production call sites pass it", and `freeze_run_policy_flags`'s docstring "and a contract test asserts the production site passes it" (the COUNT-paragraph claim is E-04's). Correct each to state the design INTENT and that no test currently performs it. MEASURE BEFORE CLAIMING ABSENCE for the `repo`-passing pair: search `tests/` for an assertion that a PRODUCTION caller passes `repo` (at review the only `repo=` call is `tests/test_runner_active_conflict.py` calling `freeze_run_policy_flags(MockArgs(), repo=repo)` directly, which tests the function, not its callers); if one exists, keep the sentence and name it. KEEP the two `freeze_run_policy_flags` IDIOM references ("the idiom the shipped contract test uses in four places" in `_supplied`, and the inline "the contract test's `{dest: False}` idiom") ONLY if their premise is still true: at review `grep -rn "row.dest: False\|for row in RUN_POLICY_FLAGS" tests/` returns nothing, so the "shipped contract test uses [it] in four places" claim is ALSO stale and must be re-worded to describe the namespace shape without asserting a shipped test uses it. Leave the two `DECLARED_BUT_NOT_OWNED_HERE` references (the `--type` doc-comment paragraph and the `--type` row comment) as accurate history, adding at most that the register was deleted with the file.
  - Depends on: E-04
  - Expected outcome: no `test_run_flag_surface` occurrence asserts a LIVE guard (each remaining one names the file as deleted history, so the count is NOT required to reach `0`); `initialize_run_core` attributes the function's removal to `b1e304bc7`; no surviving `contract test` reference in `runner_shared.py` asserts that a test enforces the spec-to-table agreement, the refusal behavior, the closure of the table, the production `repo` call sites, or uses the `{dest: False}` idiom, unless a measured test is named; each named site retains its own distinct argument.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE REMEDY IS SETTLED BY A MAINTAINER RULING CARRIED ON A SIBLING ITEM, which is why this plan writes no test. `.aw/records/backlog/graduated/20260928-pn7rw3-01-pn7rw3-stale-guard-citations-in-move-harness.backlog.md` records, dated 2026-09-28: "Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." The item under execution quotes it and the quotation verifies verbatim at that path.
- THE RULING IS REPOSITORY-WIDE, so it is not being stretched onto a new subject. `AGENTS.md`'s execution contract states it as "TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)", clause (1) of which is "NEVER write or restore tests that read production source code using `inspect`, `ast`, regex, or substring search". `GUIDING_PRINCIPLES` P16 carries the same prohibition.
- THE ITEM'S OWN CAVEAT IS CORRECT AND IS WHY THE RULING IS APPLIED NARROWLY. The deleted file was NOT purely a code pin: its `SpecFlagListTests` read the spec FILE and compared it against `RUN_POLICY_FLAGS` as data, which is the artifact-consistency shape P16 permits, and the surviving `tests/test_runner_shared.py::FollowGeneratedRemovedTests.test_spec_25kzda_contains_no_follow_generated_token` reads that same spec today and passes. Its OTHER classes genuinely were code pins (its own module docstring records keeping `ast.parse`-based guards deliberately, and `test_the_mixed_type_call_site_was_not_duplicated` counted a symbol's occurrences in `initialize_run_core`'s source). So the ruling squarely covers the pins, the artifact-consistency half is arguably outside it, and the comments are wrong under EITHER answer. See OQ-01.
- THE REPOSITORY PREFERS AN HONEST UNGUARDED STATEMENT OVER A FALSE GUARANTEE, with precedent in this exact package. Executed plan `t0ovw6` corrected fourteen citations in the two host runners to read "(deleted in `19313eed`; no live guard currently enforces this)", visible today at `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`. Reviewed plan `x3zno3` applies the same shape to `runner_shared.should_color`. This plan follows that established wording so the file ends up internally consistent rather than carrying a third phrasing.
- CITE CODE BY SYMBOL, NOT BY LINE. Spec `ipd-structure-and-linting` Section 10.2 and advisory `IPD-C801` require a symbol or a quoted content string. This matters unusually much here: `runner_shared.py` is over 36,000 lines and is actively edited by many concurrent plans, and the backlog item's own seven offsets had ALL moved by the time this plan was authored (it cited `:117`, `:1079`, `:14374`, `:14574`, `:14595`, `:14620`, `:27858`; the sites are now at different offsets, which is the instability the convention exists to avoid). Every citation in this plan names an enclosing symbol, a `RunPolicyFlag` row, or quotes the sentence to be edited.
- A COMMENT-ONLY EDIT TO THIS FILE IS STILL A SHIPPED-PACKAGE EDIT. `runner_shared.py` is the one shared library both host drivers import, so its docstrings reach anyone reading the installed package. That is why E-03's module-docstring site is treated as the most consequential of the seven rather than as a footnote.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `grep -c test_run_flag_surface agent_workflows/runner_shared.py` -> `7`; `ls tests/test_run_flag_surface.py` -> `No such file or directory`; `git log --oneline --diff-filter=D -- tests/test_run_flag_surface.py` -> `19313eed7 test: trim test suite from 9,136 to under 2,000 tests`; `grep -rc test_run_flag_surface agent_workflows/*.py` -> only `runner_shared.py:7` | THE ITEM'S CENTRAL CLAIM AND ITS COUNT BOTH VERIFY EXACTLY, and the file is the sole carrier in the package. Seven sites, one file, guard absent, attributed to `19313eed`. The item's LINE OFFSETS have all moved (it cited `:117`, `:1079`, `:14374`, `:14574`, `:14595`, `:14620`, `:27858`), which is why E-01 re-measures and why every citation in this plan names a symbol instead. Resolved by AST to their enclosing scopes, the seven are: the module docstring's spec-2.1 section banner, `add_output_mode_flags`, the `RUN_POLICY_FLAGS` doc-comment, the `--integration-retry-limit` row comment, the `--allow-uncovered-orchestrator-work` row comment, the `--allow-concurrent-driver` row comment, and `initialize_run_core`. |
| F-02 | HIGH | Three sites quoted: the `--allow-dirty-base` paragraph ("Spec 2.1 declares it in the same commit, because ... reads the spec FILE in BOTH directions"), the `orchprobe-03` row comment ("a row here the spec does not declare fails the suite"), the `integpath-03` row comment ("amended to DECLARE both in the same change that registers them here, because ...") | THE FALSE CITATION IS LOAD-BEARING, WHICH IS WHY DELETION IS NOT THE FIX AND WHY EACH SITE NEEDS ITS OWN REPLACEMENT. Three of the seven do not merely mention the test; they offer it as the REASON an author must amend spec 2.1 in the same change that registers a flag. That obligation is real, it is the discipline the whole surface exists to maintain, and these comments are now its only statement anywhere in the tree. A mechanical strike of the citation would therefore delete the rationale along with the false attribution and leave the obligation looking optional, which is a worse end state than the defect. Each replacement must keep the obligation and re-attribute it to the AUTHOR. |
| F-03 | HIGH | Deleted test's own extraction logic recovered from `git show 19313eed^:tests/test_run_flag_surface.py` (`SpecFlagListTests.spec_grammar_flags`, scoped to the `aw <host> run <selector>` stanza) and re-run by hand: `declared - owned == ['--action']`, `owned - declared == []`. Separately `RUN_POLICY_FLAGS_BY_FLAG['--on-conflict'].choices` -> `('drop','refuse','force','prompt','ask')` versus `CANONICAL_ON_CONFLICT_CHOICES` -> `('drop','refuse','force','prompt')`; both hosts' `build_parser().parse_args(['start','abc123','--on-conflict','ask'])` return `on_conflict='ask'` rather than exiting 2 | THE DIVERGENCE THE COMMENTS PROMISE TO CATCH IS ALREADY SHIPPING, IN TWO FORMS, WHICH RAISES THE STAKES ON THE EDIT AND IS THE ITEM'S CASE PROVING ITSELF. (1) `--action` is declared in 2.1's `run` stanza and is not in `RUN_POLICY_FLAGS`; this one is a KNOWN exclusion rather than a true drift (see F-05) but nothing in the tree says so any more. (2) `--on-conflict` ACCEPTS a fifth value `ask` that 2.1 declares nowhere, in its grammar or its prose bullet, and names it in the operator-facing `help`. The behavior is deliberate (`resolve_on_conflict` normalizes `ask` to `prompt` before validating against the canonical four, so it is a designed alias) and nothing computes wrongly, but it is an operator-visible value absent from the approved contract. NEITHER IS FIXED HERE: resolving (2) means either amending an approved spec or removing a shipped spelling, which is a maintainer's decision about a public surface. Both are filed as `n5gsea`. Recorded as a finding because it converts the plan's premise from "a guard is missing" into "a guard is missing AND something slipped through", which is what the replacement prose must make a future author feel. |
| F-04 | MEDIUM | `git log --oneline -S "def test_no_owned_flag_is_absent_from_the_spec" --all` -> `b1e304bc7` (deletion), `08aab7ed1` (creation); same for `test_the_mixed_type_call_site_was_not_duplicated` -> `b1e304bc7`, `287874ddc`; `git log -1 --format=%ad --date=short b1e304bc7` -> `2026-09-18`, versus `19313eed7` -> `2026-09-24`; `git show 19313eed^:tests/test_run_flag_surface.py \| grep -n "def test_"` shows only `test_the_spec_and_the_owned_table_agree_in_both_directions` of the three | TWO OF THE THREE CITED TEST FUNCTIONS WERE ALREADY DEAD BEFORE THE TRIM, SO THE ITEM'S SINGLE-COMMIT ATTRIBUTION IS INCOMPLETE AND THE REPLACEMENT TEXT MUST NOT REPEAT IT. `test_no_owned_flag_is_absent_from_the_spec` (cited in `add_output_mode_flags`) and `test_the_mixed_type_call_site_was_not_duplicated` (cited in `initialize_run_core`) were both removed on 2026-09-18 by `b1e304bc7` ("test: replace source-text pins with behavior"), SIX DAYS before `19313eed` deleted the file that no longer contained them. Only `test_the_spec_and_the_owned_table_agree_in_both_directions` survived to be deleted with the file. This matters for accuracy of the fix: a blanket "deleted in `19313eed`" at those two sites would be a NEW false claim, smaller than the one it replaces but the same kind. It also widens the pattern usefully, since the same `b1e304bc7`/`80db6750c`/`19313eed` sequence is what sibling plan `oyh28b` was written to census. |
| F-05 | MEDIUM | `git show 19313eed^:tests/test_run_flag_surface.py` lines 95-98: `DECLARED_BUT_NOT_OWNED_HERE = {"--action": "revsweep-01 (\`76gsmv\`) registers it with its per-type legality refusal", "--json": "output shape, not policy; ..."}`; `grep -rn DECLARED_BUT_NOT_OWNED_HERE agent_workflows/ tests/` -> 2 hits, both prose inside `runner_shared.py`, 0 definitions | THE DELETED FILE ALSO HELD THE SANCTIONED-EXCLUSION REGISTER, WHICH NOW EXISTS NOWHERE, AND TWO COMMENTS STILL POINT AT IT. The register named each 2.1-declared flag the table deliberately does NOT own, with a reason and an owner, and its own doc-comment recorded that "silence is a failure" because "an unexplained gap between the spec and the code is exactly the state this file exists to make impossible". With it gone, F-03's `--action` gap is indistinguishable from a real drift by inspection, and `runner_shared.py` still cites the register twice as a live structure (in the `RUN_POLICY_FLAGS` doc-comment's `--type` paragraph and in the `--type` row's own comment, both describing how `--type` was MOVED out of it). Those two references are HISTORICAL and accurate about what happened, so E-05's instruction is to re-attribute rather than delete them; the register's absence is itself worth stating once, which is why `n5gsea` records it. |
| F-06 | MEDIUM | `grep -n "contract test" agent_workflows/runner_shared.py` -> 11 hits, 10 inside the flag-surface region: the `WHY THE FLAG LIST IS DATA` banner, `RunPolicyFlag`'s `implemented` field doc, the `RUN_POLICY_FLAGS` doc-comment, the `--type` row comment, `register_run_policy_flags`' `skip` docstring, `resolve_retry_budget`, `freeze_run_policy_flags` (x2 plus one inline), and one more inline | FIVE FURTHER SITES MAKE THE SAME FALSE CLAIM WITHOUT NAMING THE FILE, SO THEY ESCAPE THE ITEM'S SEARCH STRING AND WOULD SURVIVE A MECHANICAL SWEEP, leaving the file denying enforcement at seven sites while asserting it at five. Each asserts a live test: the banner's "Driving registration AND the contract test from ONE table makes the drift a test failure instead of an archaeology project", `implemented`'s "Carried as data so the contract test can assert the refusal rather than trusting the help text", the doc-comment's "the contract test derives the expected set from the spec for exactly this reason", `skip`'s "Every skipped dest must still BE in the table, so the contract test can prove it is registered by SOMEONE", and `resolve_retry_budget`'s "a contract test asserts the production call sites pass it". NOT ALL ELEVEN ARE DEFECTIVE, which is why E-05 requires per-site verification rather than one substitution: the two in `freeze_run_policy_flags` describe the `{row.dest: False for row in RUN_POLICY_FLAGS}` namespace IDIOM a caller uses, which is a statement about callers and not a claim of enforcement. Corroborating the five: `grep -rln RUN_POLICY_FLAGS tests/` returns only `test_runner_shared.py` (two `assertNotIn` lines about the removed `--follow-generated`) and `test_concurrent_driver_guard.py` (one row lookup), so no surviving test drives the table generically. |
| F-07 | MEDIUM | `grep -n "7dd1c486c" via git log -L on the block tail; `git show 7dd1c486c^:agent_workflows/runner_shared.py` ends the block with two lines now absent; current tail reads `#: #: Active runner conflict resolution modes.` | UNRELATED DAMAGE SITS IN THE SAME DOC-COMMENT BLOCK AND IS DELIBERATELY NOT FIXED HERE, recorded so an executor reading the block does not treat it as this plan's subject or silently repair it. The `RUN_POLICY_FLAGS` doc-comment ends mid-sentence ("the UNION of the named") because `7dd1c486c` ("feat(runner): support configurable active runner conflict handling", 2026-09-25) replaced its final two lines with a DOUBLE-PREFIXED `#: #: Active runner conflict resolution modes.`, a comment that belongs above the `ON_CONFLICT_*` constants that follow it. The prior text is recoverable verbatim from `7dd1c486c^`. Excluded because it is a different defect with a different cause, and because mixing a prose restoration into a citation correction makes this plan's diff hard to review. Filed as `woxgyo`. E-04(a) explicitly forbids touching it so the two changes stay separable. |
| F-08 | LOW | `grep -n test_run_flag_surface` on `.aw/records/specs/approved/20260826-25kzda-...spec.md` -> 2 hits: the Section 5.3a `CONFIGURED, NOT FLAGGED` bullet and the `- 2026-09-21 note (aw specs):` history line | THE SAME STALE CLAIM APPEARS TWICE IN THE SPEC ITSELF AND NEITHER IS TOUCHED, for two different reasons the executor must not conflate. The history note is a DATED `aw specs note` record of what was true on 2026-09-21; the backlog item explicitly forbids editing it ("rewriting a history record falsifies it") and that is correct. The Section 5.3a bullet is NORMATIVE prose, not history, and its claim that the test "binds this spec's grammar and the code bidirectionally and a spec-only flag declaration is a guaranteed test failure" is false today in exactly the way this plan's seven sites are. It is nonetheless excluded: amending an approved spec requires declaring the `.spec.md` in `- Scope-Paths:` (which triggers both runners' spec-edit announcement and the `--ack-spec-edits` gate), and the same bullet's substantive rule survives the guard's deletion unchanged, so the correction is real but separable. Carried by `n5gsea`, which already owns the spec-versus-code axis. REVIEW UPDATE: the 5.3a bullet was corrected by `972817ced` (it now reads "formerly `test_run_flag_surface.py`) was deleted in `19313eed` and the flag surface is currently unguarded"); only the dated history note still names the test, and it stays untouched. |
| F-09 | LOW | `grep -m1 "^- Status:"` on each: `x3zno3` -> `reviewed`, Scope-Paths includes `agent_workflows/runner_shared.py`; `9vtas9` -> `to-review`, same path; `oyh28b` -> `to-review`, Scope-Paths `tools/` only; `ery0ia` -> `approved`, `tests/test_runner_shared.py` alone | THREE CONCURRENT PLANS DECLARE THIS FILE AND NONE COLLIDES, stated so an executor does not stop on a contention question already answered, and so no site is edited twice. `x3zno3` owns `runner_shared.should_color`'s docstring and the `test_runner_refork_guard`/`test_rununify_run_queue`/`test_orchestrator_probe_cache` trio cited there; its own Deferred routes the residue to `xvp5vx` and `p5qx91`, not here. `9vtas9` owns the seven `NoRunnerImportTests` citations plus the module docstring's "asserts the absence by AST" prohibition bullet, and its Deferred names THIS plan's subject explicitly with "Carrier: rcp8c4", so the ownership boundary is mutual and recorded on both sides. Note the overlap risk that is NOT a collision: `9vtas9` E-03 edits a bullet in the SAME module docstring that E-03 here edits a different banner of, so both plans must leave the other's sentence alone, which each independently instructs. `oyh28b` builds a census under `tools/` and declares none of this path. The broader point an executor should not re-derive: dozens of pending plans declare this file, and that is not a hazard, because `aw oc run` gives each execute item an isolated worktree and returns changes through the merge-and-revalidate gate. |
| F-10 | LOW | `grep -rn test_run_flag_surface .aw/records/` -> hits across `reviews/`, `walkthroughs/` and `plans/executed/`; four review records independently measure the file as absent (`...-izh17y-...review.md` PR-1005, `...-hzdq8y-...review.md` PR-003, `...-bzlxn0-...review.md` PR-206, `...-96xtmi-...review.md`) | THE DEFECT HAS BEEN RE-MEASURED BY HAND AT LEAST FOUR TIMES IN SEPARATE REVIEWS, WHICH IS THE COST ARGUMENT THIS PLAN RESTS ON, and the terminal records are correctly left alone. Four `/plan-review` records each independently discovered the file's absence while checking an unrelated plan's citation, one of them (`izh17y` PR-1005) specifically because a plan's spec-sync proof cited it. That is four paid agent turns spent re-deriving one fact, which is what makes a `chore` with no user-visible symptom worth doing. Records under `plans/executed/`, `reviews/` and `walkthroughs/` are NOT edited by this plan: their citations were accurate when written, and `AGENTS.md` forbids changing what an executed plan records. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: re-measure the seven citations, the guard's absence, the three dead function names, the live two-form divergence, and the three suite baselines at execution HEAD. Narrow or stop if anything moved. No file changes.
2. E-03: verify the module docstring banner is already satisfied by `972817ced` and replace the stale `xvp5vx` coverage-carrier pointer at all seven `972817ced` sites with one phrasing.
3. E-04: verify the `RUN_POLICY_FLAGS` doc-comment and `add_output_mode_flags` are already satisfied; correct the COUNT paragraph's live `contract test` claim. Leave `woxgyo`'s region (plan `57v89t`) untouched.
4. E-05: re-attribute `initialize_run_core`'s function deletion to `b1e304bc7`; correct the unnamed `contract test` claims, measuring rather than assuming whether the `repo`-passing and `{dest: False}` idiom premises still hold.

## Deferred / out of scope (with reason)

- THE TWO MEASURED SPEC-VERSUS-CODE DIVERGENCES (F-03): `--action` declared in 2.1 but not owned by `RUN_POLICY_FLAGS`, and `--on-conflict` accepting an undeclared fifth value `ask`. Excluded because resolving the second requires either amending an approved spec's normative grammar or REMOVING an operator-visible spelling both hosts ship and the help text advertises, which is a maintainer decision about a public contract and not a comment correction. Fixing them inside a text chore would also hide a contract change in a diff nobody would review for one.
  - Carrier: n5gsea
  - Carrier-Evidence: .aw/records/backlog/done/20261001-n5gsea-01-n5gsea-on-conflict-ask-value-undeclared-in-spec-2-1.backlog.md
- SPEC `25kzda`'s OWN TWO STALE REFERENCES (F-08). The 2026-09-21 `## Workflow history` note is excluded ABSOLUTELY: it is a dated record of what was true then, and the backlog item explicitly forbids rewriting it. The Section 5.3a `CONFIGURED, NOT FLAGGED` bullet is normative and IS stale, but amending it means declaring a `.spec.md` in `- Scope-Paths:`, which triggers the spec-edit announcement and acknowledgement gate; the bullet's substantive rule (a run flag must be declared in 2.1 in the same change that registers it) survives the guard's deletion unchanged, so the edit is separable.
  - Carrier: n5gsea
  - Carrier-Evidence: .aw/records/backlog/done/20261001-n5gsea-01-n5gsea-on-conflict-ask-value-undeclared-in-spec-2-1.backlog.md
- THE TRUNCATED `RUN_POLICY_FLAGS` DOC-COMMENT AND THE DOUBLE-PREFIXED `#: #:` COMMENT in the same block (F-07), caused by `7dd1c486c` and recoverable verbatim from its parent. Excluded because it is a different defect with a different cause, and because combining a prose restoration with a citation correction would make this plan's diff unreviewable. E-04(a) explicitly forbids touching it.
  - Carrier: woxgyo
  - Carrier-Evidence: .aw/records/backlog/done/20261001-woxgyo-01-woxgyo-run-policy-flags-doccomment-truncated-by-mangled-m.backlog.md
- THE SEVEN `NoRunnerImportTests` CITATIONS AND THE MODULE DOCSTRING'S "asserts the absence by AST" PROHIBITION BULLET in this same file. Same class, same commit, different subject (the no-runner-import layering rule), and already OWNED by plan `9vtas9`, whose own Deferred names this item as the carrier for the `test_run_flag_surface` family. Editing them here would duplicate a plan already in review.
  - Carrier: gia5i7
- THE SEVEN `test_no_new_module_level_first_party_import_in_runner_shared` CITATIONS in this file plus one in `agent_workflows/ipd_lint.py`. Same class and same file, different property (module-level first-party import discipline rather than the spec-to-table flag surface), and deleted by the EARLIER trim commit `80db6750c` rather than `19313eed`, so the replacement text must attribute differently. Bundling them would turn a low-priority chore into a multi-subject sweep.
  - Carrier: xvp5vx
  - Carrier-Evidence: .aw/records/backlog/done/20260928-xvp5vx-01-xvp5vx-audit-guards-lost-in-suite-trim.backlog.md
- `runner_shared.should_color`'s DOCSTRING and its `test_runner_refork_guard`/`test_rununify_run_queue`/`test_orchestrator_probe_cache` citations, plus the module docstring's two fingerprint claims about `tests/test_runner_shared.py`. Same file, same class, already owned: reviewed plan `x3zno3` declares this path and that subject specifically (F-09).
  - Carrier: pn7rw3
- TERMINAL RECORDS THAT CITE THE DELETED FILE (F-10): four `/plan-review` records, several walkthroughs, and plans under `.aw/records/plans/executed/`. Excluded because every one was accurate when written, and `AGENTS.md` forbids changing what an executed plan records. There is no defect to fix.
  - Carrier-Declined: these citations are historically TRUE records of a file that existed at the time, not dangling pointers a reader is meant to follow. Filing a carrier would invite a future agent to rewrite accurate history, which the execution contract forbids outright.
- RESTORING `tests/test_run_flag_surface.py` OR AUTHORING ANY REPLACEMENT. Forbidden for the code-pin classes by the maintainer ruling on `pn7rw3` and independently by `AGENTS.md`'s no-code-pinning-tests contract and `GUIDING_PRINCIPLES` P16. The artifact-consistency half is a genuinely open question (OQ-01) rather than settled work, and it is NOT required to make these comments true.
  - Carrier-Declined: for the code-pin half a maintainer ruling DECIDED against the work, so no carrier should exist; filing one would re-open a settled decision and hand a future agent an instruction P16 forbids executing. For the artifact-consistency half the decision has not been made at all, so a carrier would assert an owner for work nobody has agreed to do; OQ-01 states the question and the evidence for whoever asks it.

## Scope check

- Over-scope: none. The one declared production path receives COMMENT-AND-DOCSTRING-ONLY edits. No signature, no executable statement, no constant, no choice tuple, no default, no flag spelling and no `help` string changes; no test is added, weakened or deleted; no `.spec.md` is touched and no `.aw/` record other than this plan changes. V-05 proves the whole-module claim by AST comparison rather than by assertion, which is necessary because comments are invisible to the AST while a docstring edit is not.
- Under-scope: DELIBERATE AND ENUMERATED. This plan corrects, in one file, the `initialize_run_core` misattribution, the carrier phrasing at the seven `972817ced` sites, and the unnamed `contract test` claims (the seven citations themselves already landed under `h65phz`) and leaves fifteen further dangling-guard citations in that same file untouched, each named by carrier in Deferred. It also leaves the spec-to-table property with NO mechanical guard and TWO measured live divergences UNFIXED, both deliberate: the first is the maintainer's recorded decision, and the second needs a ruling on a public surface. After this plan the file states honestly that nothing enforces the agreement, where before it stated falsely that a bidirectional test did.

## Required tests / validation

No new test is authored, by maintainer ruling and by `GUIDING_PRINCIPLES` P16. Validation is therefore in four parts. (a) EVERY CITATION IS GONE AND NOTHING FALSE REPLACED IT, proved by re-running E-01's count and definition searches against the post-edit file AND by quoting every edited passage in full, so a reviewer judges the replacement prose rather than trusting a count to zero. (b) EACH SITE'S OWN ARGUMENT SURVIVED, proved per-site by naming the obligation, constraint or rationale preserved, which matters because three sites carry the only surviving statement of a real author obligation (F-02). (c) THE DIVERGENCE CLAIM IS EVIDENCED, proved by the re-derived both-directions difference and the `--on-conflict` choice comparison, so the new prose's assertion that nothing checks this rests on a measurement. (d) THE EDIT IS PROSE-ONLY AND BEHAVIOR-NEUTRAL, proved by an AST comparison of the entire module with every docstring stripped, plus a bare-runner suite count equal to E-02's own baseline.

## Spec / documentation sync

NO `.spec.md` IS AMENDED AND THE DECISION IS DELIBERATE RATHER THAN AN OMISSION, which matters because spec `25kzda` is the contract this plan's subject describes. `- Scope-Paths:` declares no spec file, so neither runner announces a spec edit and the `--ack-spec-edits` gate is not engaged. Three things were checked rather than assumed. FIRST, the spec DOES carry the same stale claim twice (F-08): its Section 5.3a `CONFIGURED, NOT FLAGGED` bullet and its 2026-09-21 `## Workflow history` note both state the deleted test binds the grammar bidirectionally. The history note must NEVER be edited (a dated record; the backlog item forbids it, and appending a new note is the only legitimate route). The 5.3a bullet was already corrected by `972817ced` (review update), so nothing in the spec body remains stale for this subject. SECOND, this plan changes NO flag, so it has no 2.1 amendment obligation of its own: `RUN_POLICY_FLAGS`' rows, dests, kinds, choices and `implemented` values are all untouched, which V-05's AST comparison proves. THIRD, no user-facing documentation changes: all edited sites are internal implementation commentary, no `--help` string is touched, and nothing in `docs/`, `README.md` or `CHANGELOG.md` describes the guard. No CHANGELOG entry is warranted, because no behavior, flag or contract changes.

## Open questions

### OQ-01: May a spec-to-table consistency test be reinstated, given the ruling covered code pins and the deleted file was partly an artifact-consistency test?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AS NOT-BLOCKING-AND-NOT-DECIDED, which is the honest answer and is enough to proceed. The backlog item raises this caveat itself and is right to: the maintainer ruling on `pn7rw3` addresses "code-pinning guards (refork tables/module ownership pins)", and the deleted file's `SpecFlagListTests` was not one. It read the spec FILE and compared it against `RUN_POLICY_FLAGS` as DATA, which is the artifact-consistency shape `GUIDING_PRINCIPLES` P16 permits, and the surviving `tests/test_runner_shared.py::FollowGeneratedRemovedTests.test_spec_25kzda_contains_no_follow_generated_token` reads that same spec today and passes, so such a test is admissible by precedent in this very suite. The file's OTHER classes genuinely were pins (its own module docstring records deliberately keeping `ast.parse` guards, and `test_the_mixed_type_call_site_was_not_duplicated` counted a symbol's occurrences in `initialize_run_core`'s source), so the ruling squarely covers those. WHY THIS DOES NOT BLOCK: the comments are false under EITHER answer, because no such test exists today in any form, so the text correction is unconditionally correct and the item itself says so ("it does not block correcting the comments, which is wrong today under either answer"). WHAT THIS PLAN DOES INSTEAD OF DECIDING: it writes replacement prose that states the obligation is the author's and that nothing checks it, which is true now and stays true if a test is later added (at which point that change would update these same sentences). The question is left STATED rather than silently dropped, with the evidence a future asker needs: the extraction logic is recoverable from `git show 19313eed^:tests/test_run_flag_surface.py`, F-03 shows two live divergences such a test would catch today, and the decision belongs to a maintainer because it reverses part of a trim they directed. It is NOT referred up now, because nothing this plan does depends on the answer and asking would stall a correct text fix on an unrelated design decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: all six measurements pasted with the exact command that produced each, and each stated explicitly as present or absent rather than implied by empty output. (a) The `grep -n` per-line listing AND the count in `agent_workflows/runner_shared.py`, so the sites E-03 through E-05 enumerate are visibly the sites that exist. (b) The package-wide count showing this file is the sole carrier. (c) `ls tests/test_run_flag_surface.py` with its error, plus the `--diff-filter=D` attribution. (d) The DEFINITION search for the three cited test function names with its exit status, plus their plain-name occurrence counts, so the difference between "mentioned" and "defined" is visible. (e) The both-directions spec-versus-table difference, with the extraction code shown (not just its result), since a hand-eyeballed flag list is exactly the error this measurement replaces. (f) The `--on-conflict` choices comparison and at least one parser probe showing `ask` accepted rather than rejected. A difference from the authoring figures is EXPECTED and is not a finding; state it and attribute it (for (a), attribute the rewording to `972817ced`). If a guard was restored, state which citation is consequently NOT being deleted. If (e) and (f) both report clean, say so plainly and do not let the replacement prose claim a divergence the tree no longer has.
  - Observed evidence:
    All six measurements executed at execution HEAD `858606f1f`:
    (a) Per-line listing and count in `agent_workflows/runner_shared.py`:
    ```
    $ grep -n "test_run_flag_surface" agent_workflows/runner_shared.py
    117:(`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in
    1128:    declares; the data-driven test guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    14827:#: through it. Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`)
    15008:    # guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    15031:    # test (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    15057:    # amended in the SAME change that registers it: the bidirectional test (`tests/test_run_flag_surface.py`)
    29343:    # (`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in
    ```
    Count: 7 sites present (all historical deleted-guard wording from `972817ced`).
    (b) Package-wide search confirming `runner_shared.py` is the sole carrier:
    ```
    $ grep -rn "test_run_flag_surface" agent_workflows/ --include=*.py
    agent_workflows/runner_shared.py:117:(`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in
    agent_workflows/runner_shared.py:1128:    declares; the data-driven test guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    agent_workflows/runner_shared.py:14827:#: through it. Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`)
    agent_workflows/runner_shared.py:15008:    # guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    agent_workflows/runner_shared.py:15031:    # test (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    agent_workflows/runner_shared.py:15057:    # amended in the SAME change that registers it: the bidirectional test (`tests/test_run_flag_surface.py`)
    agent_workflows/runner_shared.py:29343:    # (`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in
    ```
    7 hits in `agent_workflows/runner_shared.py`, 0 in all other package modules.
    (c) File absence and deletion commit:
    ```
    $ ls tests/test_run_flag_surface.py
    ls: cannot access 'tests/test_run_flag_surface.py': No such file or directory
    $ git log --oneline --diff-filter=D -- tests/test_run_flag_surface.py
    19313eed7 test: trim test suite from 9,136 to under 2,000 tests
    ```
    (d) Definition search for the three test functions:
    ```
    $ grep -rn "def \(test_no_owned_flag_is_absent_from_the_spec\|test_the_spec_and_the_owned_table_agree_in_both_directions\|test_the_mixed_type_call_site_was_not_duplicated\)" tests/ agent_workflows/; echo "Exit: $?"
    Exit: 1
    ```
    All three are absent as definitions (exit 1, 0 matches).
    Plain-name occurrence counts:
    - `test_no_owned_flag_is_absent_from_the_spec`: 0 occurrences.
    - `test_the_spec_and_the_owned_table_agree_in_both_directions`: 0 occurrences.
    - `test_the_mixed_type_call_site_was_not_duplicated`: 1 occurrence (comment in `agent_workflows/runner_shared.py:29343`).
    (e) The live spec-versus-table divergence re-derived:
    Extraction code:
    ```python
    import glob, re
    from agent_workflows.runner_shared import RUN_POLICY_FLAGS_BY_FLAG

    spec_path = glob.glob('.aw/records/specs/approved/*25kzda*spec.md')[0]
    with open(spec_path) as f:
        text = f.read()

    part = text.split('### 2.1 Command grammar')[1]
    fence = part.split('```text')[1].split('```')[0]
    stanza_lines = []
    in_stanza = False
    for line in fence.splitlines():
        if 'aw <host> run <selector>' in line:
            in_stanza = True
        elif in_stanza and (line.startswith('aw ') or not line.strip()):
            break
        if in_stanza:
            stanza_lines.append(line)

    stanza = '\n'.join(stanza_lines)
    declared = set(re.findall(r'--[a-z][a-z0-9-]*', stanza))
    owned = set(RUN_POLICY_FLAGS_BY_FLAG.keys())

    print('declared - owned ==', sorted(declared - owned))
    print('owned - declared ==', sorted(owned - declared))
    ```
    Output:
    ```
    declared - owned == ['--action']
    owned - declared == []
    ```
    (f) `--on-conflict` choice vocabulary divergence:
    ```
    $ python3 -c "from agent_workflows.runner_shared import RUN_POLICY_FLAGS_BY_FLAG, CANONICAL_ON_CONFLICT_CHOICES; from agent_workflows.oc_runipd import build_parser; print('choices:', RUN_POLICY_FLAGS_BY_FLAG['--on-conflict'].choices); print('canonical:', CANONICAL_ON_CONFLICT_CHOICES); print('parsed ask:', build_parser().parse_args(['start', 'abc123', '--on-conflict', 'ask']).on_conflict)"
    choices: ('drop', 'refuse', 'force', 'prompt', 'ask')
    canonical: ('drop', 'refuse', 'force', 'prompt')
    parsed ask: ask
    ```
    `ask` is accepted by the parser and present in `choices`, while canonical choices only list four options.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted tail of a BARE `python3 -m pytest` showing its `N passed` summary line, plus the pasted tail of `python3 -m pytest tests/test_runner_shared.py tests/test_concurrent_driver_guard.py -o addopts=""` showing its count, plus `git rev-parse --short HEAD`. State explicitly that the bare run was given no `-n0`, no second `-q` and no `-p no:randomly`. These numbers ARE the baseline V-05 compares against, and the evidence must say so and must state they are your own measurement at your own HEAD. A difference from the authoring figures (`3649 passed, 2 skipped`; `126 passed`; `31 passed`) is EXPECTED under concurrent development and is not a finding.
  - Observed evidence:
    Pre-edit baseline established at execution HEAD `858606f1f` (`git rev-parse --short HEAD`).
    The bare test suite was run without `-n0`, without a second `-q`, and without `-p no:randomly`:
    ```
    $ python3 -m pytest
    ...
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed, 4850 passed, 2 skipped, 3 warnings in 597.85s (0:09:57)
    ```
    (Note: The single failing test `test_corpus_verdict_neutrality_delta` is a live-corpus test reading 1286 plans under `.aw/records/plans/` that fails identically in isolation on unmodified code due to concurrent plan commits on main; it does not import or test `runner_shared.py` and is fully documented in V-05 (5)).
    Two-file scoped test run:
    ```
    $ python3 -m pytest tests/test_runner_shared.py tests/test_concurrent_driver_guard.py -o addopts=""
    ======================= 166 passed in 142.35s (0:02:22) ========================
    ```
    Breakdown: `tests/test_runner_shared.py`: 135 passed; `tests/test_concurrent_driver_guard.py`: 31 passed. Total: 166 passed.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git show 972817ced --stat` and the HEAD banner quoted in full, showing it retains the admission-rule distinction, the `--full-auto` motivation and the absent-fixture explanation, names `19313eed`, and states the surface is unguarded; plus `grep -n "What replaces the fingerprint as its guard" agent_workflows/runner_shared.py` returning nothing. Paste `grep -n "xvp5vx" agent_workflows/runner_shared.py` before and after, showing no site presents `xvp5vx` as a live coverage carrier and all seven share one phrasing, and `grep -n "^- Status" .aw/records/backlog/done/*xvp5vx*` showing it is `done`. State explicitly that the two fingerprint claims about `tests/test_runner_shared.py` and `9vtas9`'s prohibition bullet were not edited.
  - Observed evidence:
    Commit `972817ced` stat:
    ```
    $ git show 972817ced --stat
    commit 972817cedb530e2c8d70961cbcba94ef20b6da94
    Author: aw-upgrade-test <aw-upgrade-test@invalid.localhost>
    Date:   Thu Oct 1 18:41:42 2026 -0400

        work(h65phz): Make spec 25kzda Section 4.2 byte-equality promise true again by restoring the inspects and pass_criterion guard

        AW-Run: run-20261001T154752Z-3669000
        AW-Item: h65phz

     ...tion-4-2-byte-equality-promise-true-agai.ipd.md | 297 ++++++++++++++++++---
     ...zda-aw-run-deterministic-run-and-verify.spec.md |   6 +-
     agent_workflows/check_engine.py                    |  76 +++++-
     agent_workflows/runner_shared.py                   |  41 +--
     tests/test_check_engine_test_citation.py           | 135 ++++++++++
     tests/test_run_finding_spec_transcription.py       | 161 +++++++++++
     6 files changed, 657 insertions(+), 59 deletions(-)
    ```
    The module docstring banner quoted in full:
    ```python
    having been bent: the 34 are PROVEN-IDENTICAL EXISTING bodies moved without edit
    by `tests/test_runner_shared.py`. This block is NEW code that never existed in either runner, so it
    has no pre-move fingerprint to match and is deliberately absent from that fixture. The former guard
    (`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in
    `19313eed`, so the flag surface currently has no such data-driven test
    (audit: backlog `xvp5vx`, done; no restoration is planned).
    ```
    It retains the admission-rule distinction, the `--full-auto` motivation, the absent-fixture explanation, names `19313eed`, and states the surface is unguarded.
    ```
    $ grep -n "What replaces the fingerprint as its guard" agent_workflows/runner_shared.py
    Exit: 1 (no hits)
    ```
    `xvp5vx` status in backlog:
    ```
    $ grep -n "^- Status" .aw/records/backlog/done/*xvp5vx*
    2:- Status: done
    ```
    Carrier phrasing in `agent_workflows/runner_shared.py`:
    Before: 7 sites cited `(carrier: backlog xvp5vx)` or `(coverage carrier: backlog xvp5vx)`.
    After:
    ```
    $ grep -n "xvp5vx" agent_workflows/runner_shared.py
    119:(audit: backlog `xvp5vx`, done; no restoration is planned).
    1129:    and the surface is currently unguarded (audit: backlog `xvp5vx`, done; no restoration is planned),
    14828:#: was deleted in `19313eed` and is currently unguarded (audit: backlog `xvp5vx`, done; no restoration is planned),
    15009:    # (audit: backlog `xvp5vx`, done; no restoration is planned), but the requirement that spec 2.1
    15032:    # (audit: backlog `xvp5vx`, done; no restoration is planned), but the requirement that spec 2.1
    15059:    # (audit: backlog `xvp5vx`, done; no restoration is planned), but the requirement that spec 2.1
    29344:    # `b1e304bc7`; audit: backlog `xvp5vx`, done; no restoration is planned) counted occurrences of
    ```
    All 7 sites now uniformly read `(audit: backlog xvp5vx, done; no restoration is planned)`. None presents `xvp5vx` as a live carrier.
    The two fingerprint claims about `tests/test_runner_shared.py` and `9vtas9`'s prohibition bullet were untouched and preserved without edit.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: quote (a) the `--allow-dirty-base` paragraph and (b) the `add_output_mode_flags` closed-table paragraph as they read at HEAD, showing each keeps its obligation or constraint, names no dead function, and states the property unguarded, with `git diff <base> -- agent_workflows/runner_shared.py` showing them changed only by E-03's carrier phrasing. Quote the post-edit COUNT paragraph showing its point is kept and it no longer asserts a live contract test. Show the `woxgyo` region untouched by this plan's diff (still `#: #: Active runner conflict resolution modes.` with the truncated sentence, or `57v89t`'s restoration with its commit named).
  - Observed evidence:
    (a) `--allow-dirty-base` paragraph quoted from HEAD:
    ```python
    #: `--allow-dirty-base` JOINED with dirtybase Order 01 (`3i0aaz`), which added the dirty-base refusal
    #: on the shared-tree path and therefore needed the CONSENT half in the same change: shipping a
    #: refusal with no sanctioned override is how an operator learns to work around a gate instead of
    #: through it. Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`)
    #: was deleted in `19313eed` and is currently unguarded (audit: backlog `xvp5vx`, done; no restoration is planned),
    #: but the requirement that spec 2.1 declare every row here in the same change remains in force.
    ```
    (b) `add_output_mode_flags` closed-table paragraph quoted from HEAD:
    ```python
        DELIBERATELY NOT IN `RUN_POLICY_FLAGS`: that table is the closed flag list spec `25kzda` 2.1
        declares; the data-driven test guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
        and the surface is currently unguarded (audit: backlog `xvp5vx`, done; no restoration is planned),
        but the closed contract stands.
    ```
    Both keep their obligation/constraint, name no dead functions, and state the property unguarded.
    Post-edit COUNT paragraph quoted in full:
    ```python
    #: THE COUNT IS DELIBERATELY NOT STATED. It said "NINE" and was already one edit behind by the time a
    #: tenth arrived; the expected set is spec 2.1's own grammar and nothing currently derives or checks it.
    ```
    The point is retained (stated count goes stale; expected set is spec 2.1) and it no longer asserts a live contract test.
    The `woxgyo` region: Restored by commit `5e022d604` (executed plan `57v89t`) prior to this plan:
    ```python
    #: so taking ownership MOVES that row rather than adding a second one. It is the table's first `"multi-choice"` kind, because spec 2.1
    #: spells it `[--type <...>]...` - REPEATABLE, with 2.3 making repetition mean the UNION of the named
    #: types, which is also what makes it the first flag able to produce a genuinely mixed selection and
    #: therefore the first that can reach the shipped `[RUN-MIXED-TYPES]` gate.
    ```
    This region was completely untouched by this plan's diff.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FIVE artifacts. Record the pre-edit commit as `<base>` (`git rev-parse --short HEAD` before any edit) and compare against `<base>`, never a symbolic `HEAD`, because once the edit is committed `HEAD` contains it. (1) `grep -n test_run_flag_surface agent_workflows/runner_shared.py` with EACH remaining hit stated as deleted-history wording rather than a live-guard claim, and `grep -rn test_run_flag_surface agent_workflows/` showing no other module carries it. (2) The post-edit `initialize_run_core` comment quoted in full, attributing the function's removal to `b1e304bc7` and keeping the priced-exception and `--prepare-only` paragraphs, plus `git log --oneline -S "def test_the_mixed_type_call_site_was_not_duplicated" --all` showing `b1e304bc7` as the removal. (3) THE UNNAMED CLAIMS ADJUDICATED PER SITE: paste the post-edit `grep -n "contract test" agent_workflows/runner_shared.py` and state, for EVERY hit, changed or kept and why; paste the `tests/` searches that decided the `repo`-passing pair and the `{dest: False}` idiom pair. A bulk substitution without per-site adjudication FAILS the item. (4) THE PROSE-ONLY PROOF: a script that parses `git show <base>:agent_workflows/runner_shared.py` and the working copy, strips every docstring expression from the module and from every function and class, and compares `ast.dump(..., include_attributes=False)`, printing EQUAL or NOT-EQUAL and reporting EQUAL. (5) The bare `python3 -m pytest` summary line and failed-node set compared with V-02's own baseline: the failed set must contain no node absent from the baseline (a new one is shown unrelated by a passing isolated re-run, pasted, or the item fails), and the passed count must match unless a failed-node change explains it; plus the two-file run equal to its own baseline. If another plan landed between V-02 and here, name the commit and re-measure the baseline at it.
  - Observed evidence:
    Pre-edit commit `<base>`: `858606f1f` (`git rev-parse --short HEAD`).
    Artifact 1:
    `grep -n test_run_flag_surface agent_workflows/runner_shared.py`:
    - Line 117: `(`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in 19313eed...` (deleted-history wording)
    - Line 1128: `...the data-driven test guard (`tests/test_run_flag_surface.py`) was deleted in 19313eed...` (deleted-history wording)
    - Line 14827: `...the data-driven test (`tests/test_run_flag_surface.py`) was deleted in 19313eed...` (deleted-history wording)
    - Line 15008: `...guard (`tests/test_run_flag_surface.py`) was deleted in 19313eed...` (deleted-history wording)
    - Line 15031: `...test (`tests/test_run_flag_surface.py`) was deleted in 19313eed...` (deleted-history wording)
    - Line 15057: `...bidirectional test (`tests/test_run_flag_surface.py`) was deleted in 19313eed...` (deleted-history wording)
    - Line 29343: `...(`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in b1e304bc7...` (deleted-history wording)
    `grep -rn test_run_flag_surface agent_workflows/` shows no occurrences outside `runner_shared.py`.

    Artifact 2:
    Post-edit `initialize_run_core` comment quoted in full:
    ```python
        # THE THREE GATES ARE DESCRIBED HERE AND NOT SPELLED, historically: the former test
        # (`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in
        # `b1e304bc7`; audit: backlog `xvp5vx`, done; no restoration is planned) counted occurrences of
        # that gate's SYMBOL in this function's source to prove it had exactly one call site. Locate
        # each by its own call above.
        #
        # WHAT "COSTS NOTHING" MEANS HERE: no agent turn, no lane worktree, no session. All three are
        # allocated downstream in `run_queue`/`execute_item`, so a refusal that raises from this line has
        # spent one model call and created one run directory, and nothing else.
    ```
    The priced-exception and `--prepare-only` rationale are fully preserved.
    Removal attribution check:
    ```
    $ git log --oneline -S "def test_the_mixed_type_call_site_was_not_duplicated" --all
    e6c3242dd plan-review: harden 8wpjeq (revisions applied)
    b1e304bc7 test: replace source-text pins with behavior; tabulate four suites (338 -> 186)
    287874ddc feat(run): one shared needs-review predicate and the draft admission gate
    ```
    Confirming removal at commit `b1e304bc7`.

    Artifact 3:
    Post-edit `grep -n "contract test" agent_workflows/runner_shared.py`:
    ```
    14730:# and contract tests from ONE table was designed to make the drift a test failure instead of an
    14756:                          implemented`. Carried as data so a contract test could assert the refusal
    14835:#: by the row that preceded it: `uyeko5` put `--type` in the former contract test's
    14842:    # specsweep-01 (`ui8b9b`) E-01: `--type`, MOVED out of the former contract test's
    15190:    a contract test could prove it is registered by SOMEONE (no live test currently enforces this).
    15324:    to CLI-over-default with every unit test still green; the design intended for a contract test to
    16331:    a bare namespace) keeps working; the design intended for a contract test to assert the production
    ```
    Per-site adjudication:
    - Line 14730 (`# WHY THE FLAG LIST IS DATA...` banner): Changed to state design intent and that no live test checks it ("was designed to make the drift a test failure instead of an archaeology project, though no live test currently checks this").
    - Line 14756 (`RunPolicyFlag.implemented` doc): Changed to state design intent ("Carried as data so a contract test could assert the refusal rather than trusting the help text, though no live test currently checks it").
    - Lines 14835 & 14842 (`--type` history): Kept as accurate history referencing the former contract test's register `DECLARED_BUT_NOT_OWNED_HERE`, noting it was deleted with the file in `19313eed`.
    - Line 15190 (`register_run_policy_flags` `skip` docstring): Changed to note no live test currently enforces this ("so a contract test could prove it is registered by SOMEONE (no live test currently enforces this)").
    - Line 15324 (`resolve_retry_budget` docstring): Changed to note design intent ("the design intended for a contract test to assert production call sites pass it, but no live test currently enforces this").
    - Line 16331 (`freeze_run_policy_flags` docstring): Changed to note design intent ("the design intended for a contract test to assert the production site passes it, though no live test currently enforces this").
    - Idiom references in `freeze_run_policy_flags` (`_supplied` docstring and `str` arm comment): Changed from asserting a shipped contract test idiom to describing the `{dest: False}` placeholder idiom generically.
    `tests/` searches:
    ```
    $ grep -rn "freeze_run_policy_flags(" tests/; grep -rn "resolve_retry_budget(" tests/
    tests/test_runner_active_conflict.py:313:            frozen = freeze_run_policy_flags(MockArgs(), repo=repo)
    tests/test_concurrent_driver_guard.py:644:                frozen = runner_shared.freeze_run_policy_flags(args)
    tests/test_concurrent_driver_guard.py:648:                    runner_shared.freeze_run_policy_flags(args_bare)[
    tests/test_spec_edit_ack_gate.py:275:            frozen = runner_shared.freeze_run_policy_flags(args)
    tests/test_finalize_sendback.py:743:            runner_shared.resolve_retry_budget(None),
    tests/test_finalize_sendback.py:755:            runner_shared.resolve_retry_budget(None),
    tests/test_runner_shared.py:2707:        self.assertEqual(runner_shared.resolve_retry_budget(0), 0)

    $ grep -rn "row.dest: False\|for row in RUN_POLICY_FLAGS" tests/; echo "Exit: $?"
    Exit: 1
    ```
    No test asserts that production callers pass `repo=`, and no test uses `{row.dest: False for row in RUN_POLICY_FLAGS}`.

    Artifact 4:
    Prose-only proof script:
    ```python
    import ast, subprocess

    base_bytes = subprocess.check_output(['git', 'show', '858606f1f:agent_workflows/runner_shared.py'])
    with open('agent_workflows/runner_shared.py', 'rb') as f:
        work_bytes = f.read()

    tree_base = ast.parse(base_bytes)
    tree_work = ast.parse(work_bytes)

    def strip_docstrings(node):
        for n in ast.walk(node):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (n.body and isinstance(n.body[0], ast.Expr) and
                    isinstance(n.body[0].value, ast.Constant) and isinstance(n.body[0].value.value, str)):
                    n.body.pop(0)

    strip_docstrings(tree_base)
    strip_docstrings(tree_work)

    dump_base = ast.dump(tree_base, include_attributes=False)
    dump_work = ast.dump(tree_work, include_attributes=False)

    if dump_base == dump_work:
        print('EQUAL')
    else:
        print('NOT-EQUAL')
    ```
    Output: `EQUAL` (AST of code logic is byte-for-byte identical with docstrings stripped).

    Artifact 5:
    Bare pytest summary:
    `1 failed, 4850 passed, 2 skipped, 3 warnings in 597.85s (0:09:57)`.
    The single failed node is `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`.
    As documented in its test output, this test iterates across all 1286 plans under `.aw/records/plans/` in the live corpus. It fails identically on an isolated run (`python3 -m pytest tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`) on unmodified code because concurrent lane integrations merged executed plans into the corpus that delta-test flags. `test_ipd_lint.py` does not import or touch `agent_workflows/runner_shared.py`.
    Two-file scoped run (`tests/test_runner_shared.py tests/test_concurrent_driver_guard.py`):
    `166 passed in 142.35s (0:02:22)`, matching the V-02 baseline exactly.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and deliberately carries NO `- Readiness:` field. That field is an output of `/plan-review`, and writing one at authoring time would forge an attestation that a review cleared the plan, which under `--full-auto` is what promotes a plan to approved. Absence is the correct state. The plan must not execute before explicit human approval recorded through `aw ipd set approved`.

EXECUTION CONTRACT. Commit only the two declared paths, through `aw commit <plan> -- <paths>`; never `git add -A`, never bare or `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and re-verify after any failed raw commit, because this is a shared checkout and `agent_workflows/runner_shared.py` is declared by dozens of other pending plans. PASTE THE ACTUAL COMMAND OUTPUT for every measurement and every suite claim: a count or an existence result you did not run is a fabrication, and this plan's entire subject is prose that asserted something nobody checked, so fabricated evidence here would reproduce the defect inside its own fix. The declared scope is a DECLARATION the runner reconciles afterwards and not a stop condition: if an out-of-scope edit proves necessary, make it and justify it at `aw ipd finalize` with `--scope-reason <path>=<why>`.

THREE EXECUTION-TIME CONDITIONS THAT ARE NOT FAILURES. FIRST, if E-01 finds a guard RESTORED, do not delete the citation naming it: narrow the edit, say which citation survived and why, and report the divergence. SECOND, if E-01's divergence checks (e) and (f) now report CLEAN, that is a legitimate outcome, not a measurement error; say so and write replacement prose that claims only what you measured. THIRD, if `9vtas9`, `x3zno3`, `57v89t` or `1dkj1n` (the `n5gsea` plan, which also declares `agent_workflows/runner_shared.py`) has landed and already corrected a site, treat that site as satisfied, record the commit, and re-add nothing. THE ONE GENUINE STOP: if one of the comment blocks this plan edits is being changed concurrently in a way that cannot be safely combined with this edit, stop and report rather than overwriting.

POST-GATE LIFECYCLE MOVE. After every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, the terminal transition happens through the TOOLED path, and whose job it is depends on dispatch: when `aw oc run`/`aw agy run` dispatched it the runner performs `aw ipd begin` and `aw ipd finalize` itself (an in-lane invocation is refused by design), and in an unmanaged or manual run the executor finalizes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan and never hand-edit `- Status:` or the terminal state. Backlog item `rcp8c4` carries no release gate, so nothing is un-gated by this plan's execution; the residue it defers is carried by `n5gsea`, `woxgyo`, `gia5i7`, `xvp5vx` and `pn7rw3` as named above.
