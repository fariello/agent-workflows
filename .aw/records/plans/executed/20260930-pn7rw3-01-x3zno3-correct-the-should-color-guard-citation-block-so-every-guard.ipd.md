# IPD: Correct the should_color guard citation block so every guard it names exists, and state what actually holds the single-definition property

- Date: 2026-09-30
- Kind: child
- Concern: A COMMENT AND A SHIPPED DOCSTRING BOTH TELL A FUTURE AUTHOR THAT THREE TESTS WILL FAIL IF THEY TOUCH A DELEGATING `def`, AND ALL THREE ARE ABSENT, SO THE ONLY THING PROTECTING THE SYMBOL IS THE FALSE SENTENCE ITSELF. Backlog `pn7rw3` records the test-side instance: the `should_color` note inside `tests/test_runner_shared.py`'s `SUPERSEDED_SINCE_MOVE` comment justifies keeping a delegating `def` rather than an import by naming "three shipped guards" that assert `runner_shared` DEFINES the symbol. Measured at lane HEAD `6992d396`, ZERO of the three exist. THE ITEM UNDERSTATES THE DEFECT IN TWO WAYS, WHICH IS WHY THIS PLAN IS LARGER THAN A COMMENT EDIT. FIRST, THE SAME FALSE JUSTIFICATION IS SHIPPED IN PRODUCTION: `runner_shared.should_color`'s own docstring repeats all three citations nearly verbatim ("three shipped guards assert that `runner_shared` DEFINES this symbol ... and an import fails all three"), so the claim reaches anyone reading the installed package, not only a reader of the test file, and the item does not mention it. SECOND, THAT SAME DOCSTRING CARRIES A FOURTH DEAD CITATION the item does not name: it says a module-level import is "REFUSED by a shipped guard", `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`, and that file was deleted in the same commit `19313eed`. So the docstring's two independent structural claims - keep the `def`, keep the import function-local - are each backed by a guard that does not exist, and a reader who checks either one finds nothing. The maintainer ruling on this very item settles the direction and forecloses the obvious repair: "Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins."
- Scope: Replace the dead guard citations with what is TRUE at execution HEAD, in the two places the false claim lives. In `agent_workflows/runner_shared.should_color`'s docstring: delete the "three shipped guards ... an import fails all three" justification and the `test_orchestrator_probe_cache.py` module-level-import claim, and state in their place the reasons that survive without a guard (the symbol is re-exported by name from both hosts and is in `oc_runipd.__all__`, so the name must resolve on this module; the function-local import is the module's established convention, now stated as a convention rather than as an enforced rule), keeping the still-true `tests/test_runner_shared.py::SharedColorDecisionTests` pointer and the behavior-change paragraph intact. In `tests/test_runner_shared.py`: correct the same three citations inside the `should_color` note, and delete the unresolvable `OneOriginatingDefinitionTests` pointer while keeping the `tests/test_term.py` `ShouldColorGridTests` pointer that does resolve. EXCLUDES restoring any deleted guard, and EXCLUDES writing any new test that reads production source with `ast`/`inspect`/regex (forbidden by `GUIDING_PRINCIPLES` P16 and by this item's own maintainer ruling). EXCLUDES changing `should_color`'s body, signature or the `def`-versus-import decision itself: this plan corrects the JUSTIFICATION and deliberately leaves the code as shipped. EXCLUDES the other 24 `test_runner_refork_guard`/`anti-re-fork` citations measured across seven files, and EXCLUDES the three `LaneIntegrationExtractionTests` and two `test_rununify_host_descriptor.py` citations, all of which are the same class in different subjects and are carried onward by name in Deferred.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_shared.py, .aw/records/plans/pending/20260930-pn7rw3-01-x3zno3-correct-the-should-color-guard-citation-block-so-every-guard.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: pn7rw3
- Set: pn7rw3
- Order: 1
- Highest E allocated: 04
- Author: aw oc run
- Id: x3zno3

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: x3zno3 verified (set pn7rw3, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_runner_shared.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (aw set): /plan-review verdict APPROVE WITH REVISIONS APPLIED; PR-001 through PR-005 all fixed; no BLOCKER, no unfixed HIGH; readiness go-pending-approval
- 2026-09-30 to-review (aw oc run): authored from backlog `pn7rw3`. GATE NOTE: the item carries no `- Blocks-Release:`, so this plan inherits none; `- Work-Kind: chore` and `- Priority: low` are INHERITED and both remain correct, because nothing a user can perceive changes. THE ITEM'S CLAIM VERIFIES AND IS AN UNDERSTATEMENT IN TWO RESPECTS, which is the authoring finding: the same false three-guard justification is SHIPPED in `runner_shared.should_color`'s docstring (the item mentions only the test comment), and that docstring carries a FOURTH dead citation the item does not name (`test_orchestrator_probe_cache.py`, deleted in the same commit). The item's open question - what now guards the single-definition property - is RESOLVED from repository evidence rather than referred to the maintainer, because the ruling already recorded on the item forecloses the only answer that would have needed one: no code pin is to be restored, so the honest fix is to state the surviving non-guard reasons and stop claiming an enforcement that does not exist. Pending plan `ery0ia` (`Status: reviewed`) deletes the comment block this item's subject sits in and names `pn7rw3` as the carrier for exactly the production-file residue this plan fixes; E-03 is written to be idempotent against either landing order. [CORRECTED AT REVIEW 2026-10-01: `ery0ia` is now `- Status: approved`, so its deletion is cleared to run and E-03's deletion branch is the LIKELY path rather than the exception; see F-10. The idempotency conclusion is unchanged, which is why nothing else in this plan needed rewriting.]
- 2026-09-30 draft (aw oc run): created.

## Goal

Make both statements of the `should_color` exemption rationale true, so a future author who checks a cited guard finds it or is told plainly that none exists. Deliver that WITHOUT restoring a code-pinning test, which this item's maintainer ruling forbids, and WITHOUT changing the shipped delegation, whose `def`-versus-import shape this plan deliberately leaves as-is while replacing the false reason for it with the reasons that actually hold.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before editing

- [x] E-01 RE-MEASURE the five citation claims this plan rests on, at execution HEAD, and record each result, because the population provably moves: every guard named here was deleted by one commit (`19313eed`) and a concurrent lane may restore one, and pending plan `ery0ia` may have deleted this plan's test-side subject outright. For each of `tests/test_runner_refork_guard.py`, `tests/test_rununify_run_queue.py`, `tests/test_orchestrator_probe_cache.py`: test file existence. For each of `test_exactly_one_definition_package_wide`, `OneOriginatingDefinitionTests`: search for a `def`/`class` definition across `tests/` and `agent_workflows/`, NOT merely for the name, since at authoring every occurrence of both was a comment mention. Also record whether `tests/test_runner_shared.py` still contains the `SUPERSEDED_SINCE_MOVE` assignment, which decides whether E-03 has a subject at all. IF ANY GUARD NOW EXISTS, do not delete the citation that names it: report the restoration and narrow the edit to the citations that still dangle.
  - Depends on: none
  - Expected outcome: five existence/definition results pasted with the exact commands that produced them. At authoring: all three files absent (`ls` -> No such file or directory); `test_exactly_one_definition_package_wide` has 0 definitions and exactly 2 occurrences, both comments (`tests/test_runner_shared.py` and `agent_workflows/runner_shared.py`); `OneOriginatingDefinitionTests` has 0 definitions and 3 occurrences, all comments or docstrings (`agent_workflows/term.py` twice, `tests/test_runner_shared.py` once); `SUPERSEDED_SINCE_MOVE` still present.
  - Execution state: performed

- [x] E-02 ESTABLISH the suite baselines this plan's V-items compare against, since both edited files are covered and a comment-only change must move neither number. Run the suite bare (`python3 -m pytest`) plus the two per-file runs that matter (`tests/test_runner_shared.py` and `tests/test_term.py`), with `-o addopts=""` for the per-file runs so the configured `-q` does not suppress the count line. Record the exact numbers and the HEAD they were measured at.
  - Depends on: E-01
  - THE AUTHORING NUMBERS BELOW ARE CONTEXT, NOT AN ACCEPTANCE BAR, AND TWO OF THE THREE HAVE ALREADY DRIFTED. The bar is that YOUR OWN pre-edit baseline equals YOUR OWN post-edit count; it is NOT that either matches a number recorded here. Re-measured at review HEAD `3b39f14ef`: the bare suite is `3523 passed, 2 skipped` (authoring recorded `3387 passed, 2 skipped`, so +136), `tests/test_runner_shared.py` is `126 passed` (authoring recorded `119`, so +7), and `tests/test_term.py` is `28 passed` (unchanged). The suite is under concurrent development, so expect further drift and do NOT treat a difference from these figures as a defect or as a reason to stop. Record your own numbers with your own HEAD and compare only against those.
  - Expected outcome: three counts pasted with YOUR execution HEAD, explicitly labelled as the baseline V-03/V-04 will compare against. At authoring, HEAD `6992d396`: bare suite `3387 passed, 2 skipped, 3 warnings in 64.19s`; `tests/test_runner_shared.py` `119 passed`; `tests/test_term.py` `28 passed`. At review HEAD `3b39f14ef`: bare suite `3523 passed, 2 skipped`; `tests/test_runner_shared.py` `126 passed`; `tests/test_term.py` `28 passed`. Both sets are historical context; neither is the bar.
  - Execution state: performed

### Task group 2: correct the two statements of the false claim

- [x] E-03 CORRECT THE THREE DEAD CITATIONS IN THE TEST-SIDE `should_color` NOTE, inside the `SUPERSEDED_SINCE_MOVE` comment block in `tests/test_runner_shared.py`. The sentence to fix is the one beginning "THE `def` DELIBERATELY REMAINS, as a single delegating statement, because three shipped guards assert `runner_shared` DEFINES this symbol", which then names `test_runner_refork_guard.py`'s `Owned("should_color", "runner_shared", BOTH)` row, `test_rununify_run_queue.py`'s `RESOLVES_IN_RUNNER_SHARED`, and `test_exactly_one_definition_package_wide` "below", and concludes "an import fails all three". REPLACE the enforcement claim with the reasons that survive, which E-04 states in full for the production copy: say that the three guards were deleted in `19313eed` and that NO test now asserts the symbol is defined here, and keep the `def` justified by the two facts that remain true (both hosts re-export the name, and a delegation cannot fingerprint as the body it replaced, which is why the exemption entry exists at all). ALSO DELETE the `OneOriginatingDefinitionTests` pointer in the same block's coverage sentence, because that class has zero definitions; KEEP the `tests/test_term.py` `ShouldColorGridTests` pointer and the `SharedColorDecisionTests` pointer, both of which resolve. BE IDEMPOTENT AGAINST PENDING PLAN `ery0ia`, which is `Status: reviewed` and whose E-02 DELETES this whole comment block: if the block is already gone at execution, treat this item as SATISFIED BY DELETION, say so in the evidence with the commit that removed it, and do not re-add any of the text. Do not touch `INJECTED`, `HOST_LABELS`, `_MODULES` or any live test.
  - Depends on: E-02
  - Expected outcome: no surviving sentence in `tests/test_runner_shared.py` asserts that a deleted guard enforces the `should_color` definition, and the block names zero symbols that have no definition. Verified by searching the file for all five names from E-01 and finding either no hit or a hit that describes the guard as DELETED rather than as live. If `ery0ia` landed first, the file contains none of them and the evidence records that instead.
  - Execution state: performed

- [x] E-04 CORRECT THE SHIPPED DOCSTRING OF `runner_shared.should_color`, which carries the SAME false three-guard justification plus a FOURTH dead citation, and is the instance the backlog item does not mention. Two independent claims must change. (a) THE `def`-VERSUS-IMPORT CLAIM: "The `def` stays at this name DELIBERATELY rather than becoming an import: three shipped guards assert that `runner_shared` DEFINES this symbol (`test_runner_refork_guard.py`'s `Owned(...)` row, `test_rununify_run_queue.py`'s `RESOLVES_IN_RUNNER_SHARED`, and `test_runner_shared.py::test_exactly_one_definition_package_wide`), and an import fails all three." Delete the enforcement claim and state the reasons that hold WITHOUT a guard: the name must resolve as an attribute of this module because BOTH hosts re-export it by name (`from agent_workflows.runner_shared import should_color as should_color` in each of `oc_runipd` and `agy_runipd`) and `oc_runipd.__all__` lists `"should_color"`, so the module is a published binding site regardless of whether a test says so; and record that the three cited guards were deleted in `19313eed` and that the shape is now a CONVENTION rather than an enforced property. (b) THE IMPORT-PLACEMENT CLAIM: "THE IMPORT IS FUNCTION-LOCAL DELIBERATELY, and a module-level one is REFUSED by a shipped guard: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`". That file is absent, so nothing refuses it. Keep the REASON (a module-level first-party import here changes the import graph for both host drivers, and `ipd_lint`/`ipd_schema`/`ipd_lifecycle`/`worktree_lease` all arrive function-locally) and drop the claim that a test enforces it. KEEP UNCHANGED the behavior-change paragraph and its `tests/test_runner_shared.py::SharedColorDecisionTests` pointer, which resolves and passes. DO NOT change the function body, the signature, or the `def`-versus-import decision: this is a docstring edit, and the code is deliberately left as shipped.
  - Depends on: E-03
  - Expected outcome: the docstring names no absent test as a live guard, both structural decisions carry a reason that survives without one, and an AST comparison shows the function's executable statements are byte-identical to before the edit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE ITEM'S OWN MAINTAINER RULING FORECLOSES THE REPAIR A READER WOULD REACH FOR FIRST, and it is the reason this plan writes no test. The `## Workflow history` of `.aw/records/backlog/graduated/20260928-pn7rw3-01-pn7rw3-stale-guard-citations-in-move-harness.backlog.md` (the item moved from `open/` to `graduated/` when this plan was authored; the authoring text cited the pre-move `open/` path, corrected at review) records: "Code-pinning guards (refork tables/module ownership pins) were deleted in the suite trim and will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." So the item's own open question ("deciding what (if anything) now guards the single-definition property of `should_color` is a real question") has its answer already recorded on the item: nothing will, by ruling. See OQ-01.
- THE SAME RULING IS REPOSITORY-WIDE AND IS NOT SPECIFIC TO THIS ITEM. `GUIDING_PRINCIPLES.md` Section 16 forbids "No production source inspection", naming `inspect.getsource`, `ast.parse`, `read_text()` and substring/regex searches against `agent_workflows/*.py`; `AGENTS.md`'s execution contract repeats it as clause (1) of "TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)". Sibling item `p5qx91` carries the identically worded ruling for the color axis specifically: "Do NOT restore single-originating-definition AST/source pins."
- A CONCURRENT PENDING PLAN OWNS THE TEST-SIDE SUBJECT AND NAMES THIS ITEM AS THE CARRIER FOR THE REST, which decides this plan's shape rather than merely overlapping it. `ery0ia` (`Scope-Paths: tests/test_runner_shared.py`) deletes `SUPERSEDED_SINCE_MOVE` with its comment block, and its F-06 states the deletion "DISSOLVES a second open item rather than colliding with it", explicitly declining to close `pn7rw3`. Its own Deferred section routes the production-file citations here by name: "Carrier: pn7rw3". So the production docstring is unambiguously this plan's, and the test-side edit is written idempotently (E-03) rather than contested.
- `ery0ia` HAS ADVANCED TO `approved` SINCE THIS PLAN WAS AUTHORED, which raises the probability of E-03's deletion branch from "possible" to "likely" and is recorded at review so the executor is not surprised. Measured at review HEAD `3b39f14ef`: `ery0ia` carries `- Status: approved` (the plan text above said `reviewed`), so it is cleared to execute and `aw oc run` may dispatch it before or alongside this plan. Two consequences, both already handled rather than newly required: E-03's V-03 route (b) is the EXPECTED path rather than the exception, and the two plans still cannot collide on the production file, because `ery0ia` declares `tests/test_runner_shared.py` ALONE and E-04's subject is `agent_workflows/runner_shared.py`. Verified that the block boundary is real: the false `should_color` claim sits at `tests/test_runner_shared.py` line 313 inside the comment block whose `SUPERSEDED_SINCE_MOVE = (` assignment is at line 353, and `ery0ia` E-02 instructs deleting "EACH ASSIGNMENT WITH ITS OWN PRECEDING BLOCK".
- `ery0ia` ALSO ALREADY DELETES THE UNRESOLVABLE `OneOriginatingDefinitionTests` POINTER THAT E-03 TARGETS, which is worth knowing so the two edits are not read as contradictory. Its review-added F-09 resolves each of the block's six coverage pointers BY SYMBOL and deletes the ones that do not resolve, naming `OneOriginatingDefinitionTests` and `test_exactly_one_definition_package_wide` as "`pn7rw3`'s own subject ... dissolved by the deletion". So under the deletion branch E-03's intent is satisfied in full by another plan, which is exactly what "satisfied by deletion" means and why E-03 must re-add nothing.
- CITE CODE BY SYMBOL, NOT BY LINE. Spec `ipd-structure-and-linting` Section 10.2 and advisory `IPD-C801` require a symbol or a quoted content string; an offset expires before the plan executes. Both target files are large and actively edited (`runner_shared.py` is over 36,000 lines), so every citation in this plan names a function, class, or quoted sentence.
- THE FINGERPRINT HARNESS THIS COMMENT BLOCK SERVES IS ITSELF ALREADY DEAD, which bounds how much the comment can honestly claim. `tests/test_runner_shared.py`'s module docstring already says of assertion 1: "`tests/fixtures/runner_shared_premove_fingerprints.json` is a RETAINED HISTORICAL CAPTURE that no test reads, rather than a live pin (the test harness was deleted in `19313eed`)." So an "exemption" from that harness exempts a symbol from nothing that runs. This plan does not act on that (it is `ery0ia`'s subject); it matters here because it is why E-03 must not replace the false claim with a different enforcement claim about the exemption mechanism.

## Findings

| Id | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `ls tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py` -> both `No such file or directory`; `rg -n "test_exactly_one_definition_package_wide" tests/` -> ONE hit, the comment line itself | THE ITEM'S CENTRAL CLAIM VERIFIES, AND IS STRONGER THAN FILED: THE ITEM SAYS TWO OF THREE GUARDS ARE GONE AND HEDGES ON THE THIRD ("might survive"), BUT ALL THREE ARE ABSENT. The two files were deleted in `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), confirmed by `git log --diff-filter=D --name-only -1 19313eed`. The third, `test_exactly_one_definition_package_wide`, is cited as living "below" in that very file and has ZERO definitions anywhere: its only two occurrences in the repository are the `tests/test_runner_shared.py` comment and the `runner_shared.py` docstring, i.e. the two false claims themselves. So the comment's stated consequence, "an import fails all three", would in fact fail none. |
| F-02 | HIGH | `rg -n "test_runner_refork_guard" agent_workflows/runner_shared.py` -> first hit is inside `should_color`'s docstring, reading "three shipped guards assert that `runner_shared` DEFINES this symbol" with the same three names | THE FALSE JUSTIFICATION IS SHIPPED IN PRODUCTION, NOT ONLY IN A TEST COMMENT, AND THE ITEM DOES NOT MENTION IT. `runner_shared.should_color`'s docstring repeats the entire three-guard argument nearly verbatim, including "an import fails all three". This is the more consequential instance for two reasons: it ships in the installed package, so it reaches any reader of the library rather than only a reader of the test suite; and it is the docstring attached to the very `def` the claim is protecting, which is exactly where a future author deciding whether to collapse the `def` into an import will look. Fixing the test comment alone would leave the defect in the place it does the most damage. |
| F-03 | MEDIUM | `rg -n "test_orchestrator_probe_cache" agent_workflows/runner_shared.py`; `ls tests/test_orchestrator_probe_cache.py` -> `No such file or directory`; `ls tests/ \| grep -i probe` -> only `test_orchestrator_probe_payload.py` | A FOURTH DEAD CITATION SITS IN THE SAME DOCSTRING, BACKING A SECOND AND INDEPENDENT STRUCTURAL CLAIM, AND THE ITEM NAMES NEITHER. The docstring's final paragraph says the function-local import placement is "REFUSED by a shipped guard: `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`", which "allows exactly `render_stream` and `runner_profiles` at module level". That file was deleted in `19313eed` too, and `rg "no_new_module_level\|module_level_first_party" tests/` returns nothing, so no test refuses a module-level import here. This matters beyond arithmetic: the docstring makes TWO structural claims (keep the `def`, keep the import local) and BOTH are backed by guards that do not exist, so an author who verifies either one finds nothing and may reasonably conclude both shapes are free to change. `runner_shared.py` carries eight further citations of the same deleted probe-cache file in other subjects, which are NOT in scope (see Deferred). |
| F-04 | MEDIUM | `rg -n "OneOriginatingDefinitionTests" agent_workflows/ tests/` -> 3 hits: `agent_workflows/term.py` twice, `tests/test_runner_shared.py` once; `rg -n "^class " tests/test_term.py` -> 22 classes, none named `OneOriginatingDefinitionTests` | THE REPLACEMENT-COVERAGE POINTER IN THE SAME BLOCK IS HALF DEAD, so E-03 cannot simply preserve the coverage sentence wholesale. The block says the unified decision "has its OWN dedicated coverage in `tests/test_term.py` (`ShouldColorGridTests` pins all 16 `NO_COLOR` x `FORCE_COLOR` cells ...; `OneOriginatingDefinitionTests` forbids a fourth implementation)". `ShouldColorGridTests` RESOLVES (`tests/test_term.py`, and the file passes `28 passed`). `OneOriginatingDefinitionTests` has ZERO definitions; it is cited twice more in `agent_workflows/term.py` docstrings, which is the same defect in a file this plan does not declare (see Deferred). Preserving the sentence intact would carry a fifth stale citation forward inside the very edit meant to remove stale citations. |
| F-05 | MEDIUM | `rg -n "should_color" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py`; `rg -n '"should_color"' agent_workflows/oc_runipd.py` | THE `def` HAS A REAL SURVIVING JUSTIFICATION, WHICH IS WHAT MAKES THE FIX A REWRITE RATHER THAN A DELETION. Independently of any test, the name must resolve as an attribute of `runner_shared`: `agy_runipd` carries `from agent_workflows.runner_shared import should_color as should_color`, `oc_runipd` carries the same re-export, and `oc_runipd.__all__` includes the string `"should_color"`. An `import` at the top of `runner_shared` would in fact ALSO satisfy those (an imported name is still a module attribute), so the honest statement is narrower than the one being replaced: the module is a published binding site, the current single-statement `def` form is a convention, and nothing mechanically enforces it. E-04 must state that narrower truth rather than substitute a new overclaim. |
| F-06 | MEDIUM | `python3 -c` AST walk over `agent_workflows/runner_shared.py`: `should_color` has 1 top-level definition, body = 2 non-docstring statements, `[ImportFrom, Return]`; `python3 -m pytest tests/test_runner_shared.py -o addopts="" -k SharedColorDecision` -> `1 passed` | THE BEHAVIORAL SUBSTANCE OF THE EXEMPTION IS INTACT AND MUST BE PRESERVED, so this plan's edit is provably confined to prose. The shape the comment describes is real (exactly one definition, exactly one delegating statement after the docstring), and the behavior it was exempted for is covered by a LIVE passing test, `SharedColorDecisionTests`, which asserts the delegation agrees with `term.should_color` and pins both behavior changes (`TERM=dumb` honored, `FORCE_COLOR=0` no longer forces). So the fix is to correct WHY the shape is kept, not to change the shape: there is no behavioral gap to close and no test to add. |
| F-07 | LOW | `rg -c "test_runner_refork_guard\|anti-re-fork" agent_workflows/ tests/` -> 26 hits across 7 files: `oc_runipd.py` 8, `agy_runipd.py` 6, `runner_shared.py` 8, `run_viewer.py` 1, `artifact_audit.py` 1, `tests/test_runner_shared.py` 1, `tests/fixtures/verifier_evidence_corpus.json` 1 | THE BROADER RESIDUE IS LARGE, PARTLY ALREADY FIXED, AND DELIBERATELY NOT THIS PLAN'S SUBJECT, stated so the scope boundary is a decision rather than an omission. Executed plan `t0ovw6` (Scope-Paths `tests/test_runner_shared.py`, `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`) already corrected the FOURTEEN citations in the two host runners: each now reads "(deleted in `19313eed`; no live guard currently enforces this)", which is the exact shape this plan applies to the two it owns. Its own Deferred section names the residue and its carrier: "the residue is carried by `pn7rw3`". This plan fixes ONE of `runner_shared.py`'s eight (the one inside `should_color`) plus the one in `tests/test_runner_shared.py`; the other seven in `runner_shared.py` and the three in `run_viewer.py`/`artifact_audit.py`/the fixture are different subjects requiring their own judgement, and are listed in Deferred. |
| F-08 | LOW | `rg -n "LaneIntegrationExtractionTests" agent_workflows/ tests/` -> 4 hits, 0 definitions; `ls tests/test_rununify_host_descriptor.py` -> absent, 2 citations survive | TWO FURTHER DEAD-CITATION FAMILIES IN THE SAME FILES ARE OUT OF SCOPE AND ARE NAMED SO THE NEXT READER NEED NOT RE-MEASURE. `LaneIntegrationExtractionTests` has zero definitions and is cited as live coverage by `oc_runipd.integrate_lane_branch`'s docstring, `runner_shared.integrate_lane_branch`'s docstring, the `INTEGRATION_CAUSE_TOKEN_PREFIX` decision comment, and `tests/test_runner_shared.py`'s `LANE_INTEGRATION_MOVED` comment. `tests/test_rununify_host_descriptor.py` is absent yet is cited by the LIVE `CrossHostSuccessBarEqualityTests` docstring (for `RELOCATED_CONSTANTS`) and twice inside `runner_shared.py`. `ery0ia`'s F-06 and Deferred name both families and route them here; they are excluded because each needs its own decision about what, if anything, now holds the property, and bundling them would make this chore a multi-subject sweep. |
| F-10 | MEDIUM | ADDED AT REVIEW. `grep -n "^- Status:"` on `.aw/records/plans/pending/20260929-qdro85-01-ery0ia-...ipd.md` -> `approved`; its history shows `- 2026-09-30 approved` above `- 2026-09-30 reviewed`; block boundary measured at `tests/test_runner_shared.py` lines 313 (the false claim) and 353 (the `SUPERSEDED_SINCE_MOVE = (` assignment) | `ery0ia` HAS ADVANCED FROM `reviewed` TO `approved` SINCE AUTHORING, SO E-03'S DELETION BRANCH IS NOW THE LIKELY PATH RATHER THAN THE EXCEPTION. The plan's Step 0 describes it as `Status: reviewed`, which is stale; it is now cleared to execute and a runner may dispatch it first. This does NOT invalidate anything: E-03 was deliberately written idempotent, V-03 already carries route (b), and the two plans still cannot collide on the production file because `ery0ia` declares `tests/test_runner_shared.py` ALONE while E-04's subject is `agent_workflows/runner_shared.py`. ALSO VERIFIED, and reassuring rather than alarming: `ery0ia`'s review-added F-09 resolves the block's six coverage pointers by SYMBOL and deletes the unresolvable ones, naming `OneOriginatingDefinitionTests` and `test_exactly_one_definition_package_wide` as "`pn7rw3`'s own subject ... dissolved by the deletion", so under the deletion branch E-03's full intent is satisfied by that plan. Recorded so the executor reads a likely no-op as success rather than as a missing subject. |
| F-11 | MEDIUM | ADDED AT REVIEW at HEAD `3b39f14ef`: bare `python3 -m pytest` -> `3523 passed, 2 skipped`; `tests/test_runner_shared.py -o addopts=""` -> `126 passed`; `tests/test_term.py -o addopts=""` -> `28 passed` | TWO OF E-02'S THREE RECORDED BASELINES HAVE ALREADY DRIFTED, WHICH MATTERS BECAUSE V-03 AND V-04 TREAT A MOVED COUNT AS A FAILURE. The bare suite moved from the recorded `3387 passed` to `3523 passed` (+136) and `tests/test_runner_shared.py` from `119` to `126` (+7) in the days between authoring HEAD `6992d396` and review HEAD `3b39f14ef`; only `tests/test_term.py` (28) is unchanged. The plan's DESIGN is already correct here (E-02 re-derives at execution rather than asserting the authoring figures), so this is not a structural defect, but the V-items said "equals V-02's baseline" while the prose presented specific numbers, which invites an executor to compare against the printed figures and stop on a legitimate difference. E-02 and both V-items now state explicitly that the authoring and review numbers are CONTEXT and that the bar is the executor's own pre-edit measurement, plus how to attribute a difference if `ery0ia` lands mid-execution. |
| F-12 | LOW | ADDED AT REVIEW. `grep -rln "^- Id: pn7rw3" .aw/records/backlog/` -> `.aw/records/backlog/graduated/...`, whose `- Status:` is `graduated` | THE PLAN CITES ITS OWN BACKLOG ITEM AT A PATH THAT NO LONGER EXISTS, which is the same class of defect the plan exists to fix. Step 0 quotes the maintainer ruling from `.aw/records/backlog/open/20260928-pn7rw3-...`; the item is now under `graduated/` (moved when this plan graduated it). The RULING ITSELF verifies verbatim at the new path, so no reasoning changes. Corrected at review, and worth recording precisely because a plan about dangling citations should not carry one. |
| F-09 | LOW | `python3` scan extracting every `tests/test_*.py` citation from every `.py` under `agent_workflows/` and `tests/` and testing existence: 145 distinct cited paths, 94 ABSENT | THE CLASS IS REPOSITORY-WIDE AND A SWEEP IS A DIFFERENT, MUCH LARGER JOB, which is the argument for fixing the two instances this item names rather than generalizing. The 94 absent paths are not all defects: the scan's own noise includes deliberate fixture and example names (`tests/test_foo.py` in 7 files, `tests/test_x.py`, `tests/test_demo.py`, `tests/test_1.py`) that are illustrative strings inside test bodies and MUST NOT resolve. Separating the real dangling citations from the illustrative ones needs per-site judgement across dozens of files. NOTE ALSO that pending plan `1jg2m2` (backlog `ikxtkj`) adds a citation-existence test, but its declared scope is `docs/` plus `CONTRIBUTING.md`, NOT `agent_workflows/`, so it will not catch either instance this plan fixes and there is no guard to inherit. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: re-measure the five citation facts and the three test baselines at execution HEAD, and abort or narrow if anything has moved. No file changes.
2. E-03: correct the three dead citations in the `should_color` note inside `tests/test_runner_shared.py`'s `SUPERSEDED_SINCE_MOVE` comment, drop the unresolvable `OneOriginatingDefinitionTests` pointer, keep the two that resolve. Idempotent if `ery0ia` deleted the block first.
3. E-04: correct the shipped `runner_shared.should_color` docstring, replacing both the three-guard `def` justification and the `test_orchestrator_probe_cache` import-placement claim with reasons that hold without a guard, and leaving the behavior-change paragraph and the function body untouched.

## Deferred / out of scope (with reason)

- THE OTHER SEVEN `test_runner_refork_guard`/`anti-re-fork` CITATIONS IN `agent_workflows/runner_shared.py` are not fixed here. They are in a declared path, so an executor is not blocked from touching them, but each has a DIFFERENT subject and needs its own judgement about what now holds the property it claims (named by symbol so no re-measurement is needed): the `FrontMatterReaderBehaviorTests` pointer inside the front-matter reader, the "WHY BOTH LIVE HERE RATHER THAN IN `oc_runipd`" decision comment, the "second copy the anti-re-fork discipline forbids" branch comment, the "pins that no runner REDEFINES an extracted symbol" comment, the "fails if one grows back" comment, the "fails if a driver grows a copy" comment, and the "tables it as `selectors`-owned" comment. Fixing them in this chore would make it a multi-subject sweep of a 36,000-line file.
  - Carrier: xvp5vx
- THE SINGLE CITATIONS IN `agent_workflows/run_viewer.py` AND `agent_workflows/artifact_audit.py` are excluded because those files are not declared, and adding two production modules to `- Scope-Paths:` for a one-line comment each would widen the plan's blast radius past its subject. Both cite the deleted refork guard as a live pattern.
  - Carrier: xvp5vx
- `tests/fixtures/verifier_evidence_corpus.json` names `python3 -m pytest tests/test_runner_refork_guard.py` as a COMMAND inside a shape-regression corpus read by `tests/test_verifier_evidence.py`. This is NOT the same defect and must not be "fixed": the corpus pins the SHAPE of historical verification-evidence dicts, so the command string is data whose only requirement is that it once appeared in a real outcome record. Editing it would weaken a regression fence to satisfy a cosmetic search.
  - Carrier-Declined: this row records that the citation MUST NOT be changed, so there is no work to hand off. The string is corpus DATA asserting a historical shape, not a pointer a reader is meant to follow, and filing a carrier for it would invite a future agent to "fix" a regression fence.
- THE `LaneIntegrationExtractionTests` AND `tests/test_rununify_host_descriptor.py` FAMILIES (F-08) are excluded for the same reason as the seven above: same class, different subjects, each needing its own decision. Two of the five sites sit in `tests/test_runner_shared.py`, which IS declared, so an executor may correct them while there; they are not given E-items because neither concerns `should_color`.
  - Carrier: xvp5vx
- THE TWO `OneOriginatingDefinitionTests` CITATIONS IN `agent_workflows/term.py` are excluded because that file is not declared. They are the upstream instance of F-04: `term.should_color`'s own docstring tells a reader that `tests/test_term.py::OneOriginatingDefinitionTests` "fails if a" second implementation appears, and the class has zero definitions. This plan removes the pointer from the two files it owns; correcting `term.py` needs the same decision about what now holds the single-originating-definition property that sibling item `p5qx91` was filed for and already carries a maintainer ruling on.
  - Carrier: p5qx91
- RESTORING ANY DELETED GUARD IS OUT OF SCOPE BY MAINTAINER RULING, recorded on this item and repeated on `p5qx91`. No `ast`/`inspect`/regex test over production source is written, and no census or symbol-ownership table is restored.
  - Carrier-Declined: a maintainer ruling recorded on this item and on `p5qx91` DECIDED against the work, so no carrier should exist; filing one would re-open a settled decision and hand a future agent an instruction that `GUIDING_PRINCIPLES` P16 forbids executing.
- CHANGING THE `def` TO AN IMPORT is out of scope. F-05 shows the change would probably be safe, and that is precisely why it must not ride along in a citation-correction chore: it is a shipped-surface change to a symbol both hosts re-export, it belongs in a plan that can validate it, and this plan's Expected outcomes all assert the executable body is unchanged.
  - Carrier-Declined: nothing is broken, so there is no defect to carry. After this plan the `def` is documented by reasons that are TRUE (both hosts re-export the name; `oc_runipd.__all__` publishes it), which is a sufficient terminal state; collapsing it into an import is an optional refactor with no defect behind it, and filing a carrier would assert one exists.
- A REPOSITORY-WIDE DANGLING-CITATION GUARD OVER `agent_workflows/` is out of scope (F-09). 94 of 145 cited test paths are absent, and an unknown fraction are deliberate illustrative names that must not resolve; building a gate needs an allowlist design and a cleanup tranche far larger than this item.
  - Carrier: xvp5vx

## Scope check

- Over-scope: none. Both declared paths receive COMMENT-AND-DOCSTRING-ONLY edits. No signature, no executable statement, no flag, no help string and no test assertion changes; no test is added, weakened or deleted; no `.spec.md` is touched and no `.aw/` record other than this plan changes. `V-04` proves the production edit is prose-only by AST comparison of the function's executable statements.
- Under-scope: DELIBERATE AND ENUMERATED. This plan corrects TWO of the 26 measured `refork`-family citations plus one coverage pointer, and leaves the residue named by carrier in Deferred rather than sweeping it. It also leaves the `should_color` single-definition property with NO mechanical guard, which is the maintainer's recorded decision and not an oversight: after this plan the repository states honestly that nothing enforces the shape, where before it stated falsely that three tests did.

## Required tests / validation

No new test is authored, by ruling. Validation is therefore (a) the two edited surfaces contain no citation to an absent guard, proved by re-running E-01's existence and definition searches against the post-edit files; (b) the shipped function is behaviorally and structurally unchanged, proved by an AST comparison of its executable statements plus the live `SharedColorDecisionTests`; and (c) no suite count moves, proved against E-02's baselines with the bare runner (`python3 -m pytest`) and the two per-file runs.

## Spec / documentation sync

N/A with reason. No spec governs these comments. Spec `uonrjg` R9.3a.2 is CITED by the text this plan edits ("requires the depth resolver above this decision have EXACTLY ONE definition"), and that requirement is NOT changed here: the plan corrects false claims about which TESTS enforce it, not the requirement itself. That spec's own stale color-axis pins are separately filed as `p5qx91` with a maintainer ruling already recorded, so amending the spec from here would pre-empt that item's decision. `- Scope-Paths:` therefore declares no `.spec.md` file. No user-facing documentation changes: the edited docstring is an internal implementation note on a module that is not in the package's public re-export set.

## Open questions

### OQ-01: What, if anything, should guard that `should_color` has exactly one definition in `runner_shared`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE RULING ALREADY RECORDED ON THE ITEM, so it needs no maintainer round trip. The backlog item raises this as "a real question rather than a text fix", and the maintainer note on that same item answers it: "Code-pinning guards ... will not be restored. Stale comments should simply remove references to them without seeking to restore code pins." Sibling item `p5qx91` carries the same ruling for this exact symbol's axis ("Do NOT restore single-originating-definition AST/source pins"), and `GUIDING_PRINCIPLES` P16 forbids the instrument repository-wide. So the answer is NOTHING guards it mechanically, and the correct action is to say so. What replaces the guard is a statement of the facts that survive without one (F-05: both hosts re-export the name and `oc_runipd.__all__` publishes it) plus the live behavioral coverage that already exists (F-06: `SharedColorDecisionTests` and `tests/test_term.py`'s `ShouldColorGridTests`). One narrower question is NOT resolved here and is correctly someone else's: whether the `def` should become an import at all, which is a shipped-surface change excluded in Deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the five commands and their pasted output: `ls tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py tests/test_orchestrator_probe_cache.py`; a definition search for `test_exactly_one_definition_package_wide` and for `OneOriginatingDefinitionTests` of the form `rg -n "^\s*(def|class) (test_exactly_one_definition_package_wide|OneOriginatingDefinitionTests)\b" agent_workflows/ tests/` showing zero matches, TOGETHER WITH the plain-name occurrence counts so the difference between "mentioned" and "defined" is visible; and `rg -n "SUPERSEDED_SINCE_MOVE" tests/test_runner_shared.py`. Each result must be stated as absent-or-present explicitly, not implied by empty output. If any guard is present, the evidence must state which citation is consequently NOT being deleted.
  - Observed evidence:
    1. File existence check:
    ```
    $ ls tests/test_runner_refork_guard.py tests/test_rununify_run_queue.py tests/test_orchestrator_probe_cache.py
    ls: cannot access 'tests/test_runner_refork_guard.py': No such file or directory
    ls: cannot access 'tests/test_rununify_run_queue.py': No such file or directory
    ls: cannot access 'tests/test_orchestrator_probe_cache.py': No such file or directory
    ```
    Result: All three files are absent.

    2. Definition search across `agent_workflows/` and `tests/`:
    ```
    $ rg -n "^\s*(def|class) (test_exactly_one_definition_package_wide|OneOriginatingDefinitionTests)\b" agent_workflows/ tests/
    [exit code 1, 0 matches]
    ```
    Result: 0 definitions found for both symbols.

    3. Plain-name occurrence counts:
    ```
    $ rg -c "test_exactly_one_definition_package_wide" agent_workflows/ tests/
    agent_workflows/runner_shared.py:1

    $ rg -c "OneOriginatingDefinitionTests" agent_workflows/ tests/
    [exit code 1, 0 matches]
    ```
    Result: `test_exactly_one_definition_package_wide` had 0 definitions and 1 mention (in `agent_workflows/runner_shared.py` pre-edit docstring, 0 in tests); `OneOriginatingDefinitionTests` had 0 definitions and 0 mentions across the repository.

    4. Presence of `SUPERSEDED_SINCE_MOVE` in `tests/test_runner_shared.py`:
    ```
    $ rg -n "SUPERSEDED_SINCE_MOVE" tests/test_runner_shared.py
    [exit code 1, 0 matches]
    ```
    Result: `SUPERSEDED_SINCE_MOVE` is absent from `tests/test_runner_shared.py` (deleted by commit `a93adc424` from plan `ery0ia`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted tail of `python3 -m pytest` showing the `N passed` summary line, plus pasted tails of `python3 -m pytest tests/test_runner_shared.py -o addopts=""` and `python3 -m pytest tests/test_term.py -o addopts=""` showing their counts, plus `git rev-parse --short HEAD`. The bare run must NOT be given `-n0`, an extra `-q`, or `-p no:randomly`. These three numbers ARE the baseline V-03 and V-04 compare against; a difference from the authoring or review figures recorded in E-02 is EXPECTED (the suite moved +136 between them) and is not a finding. State explicitly that the recorded numbers are your own measurement at your own HEAD.
  - Observed evidence:
    Execution HEAD:
    ```
    $ git rev-parse --short HEAD
    a2789c49a
    ```
    Per-file run for `tests/test_runner_shared.py`:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts=""
    ======================== 136 passed in 64.70s (0:01:04) ========================
    ```
    Per-file run for `tests/test_term.py`:
    ```
    $ python3 -m pytest tests/test_term.py -o addopts=""
    ============================= 32 passed in 56.39s ==============================
    ```
    Bare suite baseline:
    ```
    $ python3 -m pytest
    6648 passed, 2 skipped, 3 warnings in 373.54s (0:06:13)
    ```
    These recorded numbers are our own baseline measurements at our own execution HEAD `a2789c49a`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: EITHER (a) the post-edit `should_color` note quoted in full, showing that it names no guard as live, plus `rg -n "test_runner_refork_guard|test_rununify_run_queue|test_exactly_one_definition_package_wide|OneOriginatingDefinitionTests" tests/test_runner_shared.py` whose every surviving hit (if any) is visibly a "deleted in `19313eed`" statement rather than a live-guard claim; OR (b), if `ery0ia` landed first, `rg -n "SUPERSEDED_SINCE_MOVE" tests/test_runner_shared.py` returning nothing plus the commit hash that deleted it, and an explicit statement that this item was satisfied by deletion and re-added nothing. In BOTH cases: `rg -n "ShouldColorGridTests" tests/test_runner_shared.py tests/test_term.py` must still show the pointer resolving to a real class (or, under (b), show the pointer gone with the block), and `python3 -m pytest tests/test_runner_shared.py -o addopts=""` must equal V-02's OWN recorded per-file count (not the authoring `119` nor the review `126`, both of which are historical context). UNDER ROUTE (b) ONLY, the per-file count MAY legitimately differ from V-02's baseline if `ery0ia` landed BETWEEN V-02 and this item, since that plan deletes module-level assignments from the same file; if so, state the landing commit and that the difference is attributable to it rather than to this plan, and re-baseline before V-04.
  - Observed evidence:
    Route (b) applies: plan `ery0ia` landed prior to this turn in commit `a93adc424` ("work(ery0ia): Delete the dead AST-freeze exemption tables so the two docstring exemptions cannot mislead a future author").
    Verification that `SUPERSEDED_SINCE_MOVE` is absent:
    ```
    $ rg -n "SUPERSEDED_SINCE_MOVE" tests/test_runner_shared.py
    [exit code 1, 0 matches]
    ```
    Verification that none of the dead guards remain in `tests/test_runner_shared.py`:
    ```
    $ rg -n "test_runner_refork_guard|test_rununify_run_queue|test_exactly_one_definition_package_wide|OneOriginatingDefinitionTests" tests/test_runner_shared.py
    [exit code 1, 0 matches]
    ```
    This item was satisfied by deletion in commit `a93adc424` and re-added nothing.

    Resolution of `ShouldColorGridTests`:
    ```
    $ rg -n "ShouldColorGridTests" tests/test_runner_shared.py tests/test_term.py
    tests/test_term.py:125:class ShouldColorGridTests(unittest.TestCase):
    tests/test_runner_shared.py:89:# - `should_color`: dedicated coverage in `tests/test_term.py` (`ShouldColorGridTests`)
    ```
    The pointer resolves to the real class in `tests/test_term.py`.

    Per-file test count:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts=""
    ======================== 136 passed in 60.69s (0:01:00) ========================
    ```
    Matches V-02's baseline (136 passed).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: THREE artifacts. (1) The post-edit docstring of `runner_shared.should_color` quoted in full, showing no absent test named as a live guard, both structural decisions carrying a surviving reason, and the `SharedColorDecisionTests` pointer intact. (2) PROOF THE EDIT IS PROSE-ONLY: output of a script that parses the file before and after (`git show HEAD:agent_workflows/runner_shared.py` versus the working copy), extracts the `should_color` function, strips the leading docstring expression, and compares `ast.dump` of the remaining statements, printing an explicit equality verdict; it must report EQUAL, and must also report the body is `[ImportFrom, Return]` so a reader sees the delegation survived. (3) `python3 -m pytest tests/test_runner_shared.py -o addopts="" -k SharedColorDecision` showing `1 passed`, and a bare `python3 -m pytest` whose `N passed` equals V-02's OWN recorded baseline exactly. A count that moved in either direction is a FAILURE of this V-item, not a note, because a comment-only change cannot move it. ONE EXCEPTION, which must be evidenced rather than assumed: if `ery0ia` (or another plan) landed in this checkout BETWEEN V-02 and here, name the commit and re-run the baseline at that commit before comparing, so a neighbour's change is not attributed to this plan and does not mask a real regression. Note for calibration that `-k SharedColorDecision` also prints a deselected count (`125 deselected` at review HEAD); only the `1 passed` matters.
  - Observed evidence:
    (1) Post-edit docstring of `runner_shared.should_color` quoted in full:
    ```python
    """Decide whether to emit ANSI color for ``stream`` (default stdout).

    A SANCTIONED ONE-LINE DELEGATION to :func:`agent_workflows.term.should_color`, which is the
    single ORIGINATING definition of this decision package-wide (plan `z8ddk0`, spec `uonrjg`
    R9.3a.2). The `def` stays at this name DELIBERATELY rather than becoming an import: the name
    must resolve as an attribute of this module because BOTH hosts re-export it by name
    (`from agent_workflows.runner_shared import should_color as should_color` in each of `oc_runipd`
    and `agy_runipd`) and `oc_runipd.__all__` lists `"should_color"`, so the module is a published
    binding site regardless of whether a test says so. The historical guards that previously asserted
    `runner_shared` defines this symbol (`test_runner_refork_guard.py`'s `Owned` row,
    `test_rununify_run_queue.py`'s `RESOLVES_IN_RUNNER_SHARED`, and
    `test_runner_shared.py::test_exactly_one_definition_package_wide`) were deleted in `19313eed`,
    so no live guard currently enforces this; the single-statement shape is now an established
    convention making this a BINDING rather than a second body.

    THIS CHANGED BEHAVIOR, and the change is the point. The previous body was an independent
    implementation that DISAGREED with `term`'s: it ignored `TERM` entirely, so `TERM=dumb aw oc run`
    emitted color while `TERM=dumb aw attention` did not, and it read both variables by TRUTHINESS,
    so `FORCE_COLOR=0` forced color on even into a pipe. Both are now `term`'s answers: `TERM=dumb`
    is honored, and a falsey `FORCE_COLOR` falls through instead of forcing. Measured 2026-09-19;
    pinned by `tests/test_runner_shared.py::SharedColorDecisionTests`.

    THE IMPORT IS FUNCTION-LOCAL DELIBERATELY, because an import added at module level changes the
    import graph for BOTH host drivers. A function-local import is this module's established
    convention for a first-party dependency (`ipd_lint`/`ipd_schema`/`ipd_lifecycle`/`worktree_lease`
    all arrive that way), kept here as a convention (the historical guard
    `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`
    was deleted in `19313eed`, so no live guard currently enforces this).
    """
    ```

    (2) Prose-only AST check output:
    ```
    $ python3 -c '
    import ast, subprocess
    cmd = ["git", "show", "HEAD:agent_workflows/runner_shared.py"]
    orig_code = subprocess.check_output(cmd, text=True)
    with open("agent_workflows/runner_shared.py") as f:
        new_code = f.read()
    tree_orig = ast.parse(orig_code)
    tree_new = ast.parse(new_code)
    fn_orig = next(node for node in tree_orig.body if isinstance(node, ast.FunctionDef) and node.name == "should_color")
    fn_new = next(node for node in tree_new.body if isinstance(node, ast.FunctionDef) and node.name == "should_color")
    body_orig = [s for s in fn_orig.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
    body_new = [s for s in fn_new.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str))]
    dump_orig = [ast.dump(s) for s in body_orig]
    dump_new = [ast.dump(s) for s in body_new]
    print("Body types:", [type(s).__name__ for s in body_new])
    if dump_orig == dump_new:
        print("Verdict: EQUAL")
    else:
        print("Verdict: NOT EQUAL")
    '
    Body types: ['ImportFrom', 'Return']
    Verdict: EQUAL
    ```

    (3) Suite verification:
    ```
    $ python3 -m pytest tests/test_runner_shared.py -o addopts="" -k SharedColorDecision
    ====================== 1 passed, 135 deselected in 1.84s =======================

    $ python3 -m pytest
    6648 passed, 2 skipped, 3 warnings in 582.75s (0:09:42)
    ```
    Matches V-02 baseline (`6648 passed, 2 skipped`) exactly.
  - Result: pass

## Approval and execution gate

This plan is `to-review` and carries no `- Readiness:` field: that field is an output of `/plan-review` and writing one here would forge an attestation. It must not execute before explicit human approval recorded through `aw ipd set approved`.

EXECUTION CONTRACT. Commit only the two declared paths plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit, because this is a shared checkout and both declared files are high-contention. PASTE THE ACTUAL COMMAND OUTPUT for every measurement and every suite claim in the `V-*` items; a count or an existence result you did not run is a fabrication, and this plan's whole subject is prose that asserted something nobody checked. The declared scope is a DECLARATION the runner reconciles afterwards, not a stop condition: if an out-of-scope edit proves necessary, MAKE it and then JUSTIFY it at `aw ipd finalize` with `--scope-reason <path>=<why>`, and `--scope-ack` any declared path you did not modify (which is the likely case for `tests/test_runner_shared.py` under E-03's deletion branch). The one genuine STOP remains: if either declared file is being changed concurrently in a way that cannot be safely combined with this edit, stop and report rather than overwriting.

TWO EXECUTION-TIME CONDITIONS THAT ARE NOT FAILURES. FIRST, if pending plan `ery0ia` has landed, E-03's subject is already deleted; record it as satisfied by deletion (V-03 route (b)) and proceed to E-04, which is unaffected because `ery0ia` declares only `tests/test_runner_shared.py`. SECOND, if E-01 finds that any cited guard has been RESTORED, do not delete the citation that names it: narrow the edit, say which citation survived and why, and report the divergence.

POST-GATE LIFECYCLE MOVE. After every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, the terminal transition happens through the TOOLED path, and whose job it is depends on how this plan was dispatched: when `aw oc run`/`aw agy run` dispatched it the runner performs `aw ipd begin` and `aw ipd finalize` itself (an in-lane invocation is refused by design), and in an unmanaged or manual run the executor finalizes with `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan and never hand-edit `- Status:` or the terminal state. Backlog item `pn7rw3` is NOT closed by this plan's execution: the item carries no release gate, and the residue this plan defers is carried by `xvp5vx` and `p5qx91` as named above.
