# IPD: Delete the last dead census table LANE_INTEGRATION_MOVED and the orphaned paragraph its deleted sibling left behind

- Date: 2026-10-02
- Kind: child
- Concern: `LANE_INTEGRATION_MOVED` in `tests/test_runner_shared.py` is a module-level census tuple of three symbol names with ZERO `Load` references in the repository, so it is data no test reads. It is the LAST survivor of the twelve dead tables that `GUIDING_PRINCIPLES.md` P16 ("No count or census pins") prohibits: plan `b02ohu` E-06(b) deleted nine of them, `ery0ia` deleted two more, and both plans named this one explicitly as out of their subject and left it on purpose, so the residue is a recorded handoff rather than an oversight. THE ITEM'S INSTRUCTION IS NOT SAFE AS WRITTEN AND THIS PLAN CORRECTS IT, which is the single most important thing a reviewer should check. The item says to delete "the dead table and its associated comment block"; doing exactly that leaves TWO DANGLING `LANE_INTEGRATION_MOVED` REFERENCES BEHIND, measured (F-03), because the eleven-line paragraph BELOW the table is not the table's comment block but a separate `87apfx` note that twice explains the table by name. That paragraph is ITSELF already orphaned by `b02ohu`: it was written to introduce `INTEGRATION_CAUSE_SHARED`, which `b02ohu` deleted, so it now sits above the unrelated `HOST_LABELS` assignment introducing a symbol that no longer exists (F-04). A literal reading of the item therefore converts one dead-but-coherent table into two citations pointing at nothing, which is strictly worse than the state it started from and is the exact defect sibling item `pn7rw3` was filed to fix elsewhere in this same file.
- Scope: Delete the contiguous region of `tests/test_runner_shared.py` running from the `# integpath-02 (`6sb3yu`)` comment that introduces `LANE_INTEGRATION_MOVED`, through the tuple itself, and on through the orphaned `# stalemerge-01 (`87apfx`) E-05` paragraph that `b02ohu` stranded, stopping IMMEDIATELY BEFORE the three-line `# The host label each runner MUST bind into `integrate_lane_branch`` comment that documents the LIVE `HOST_LABELS` assignment. Add no replacement table, no replacement test, and no replacement comment. KEEP `HOST_LABELS` and its own three-line comment byte-identical, KEEP `BOTH`, `_MODULES` and `INJECTED` untouched, and KEEP every test in the file. EXCLUDES the three `LaneIntegrationExtractionTests` citations in `agent_workflows/oc_runipd.py` and `agent_workflows/runner_shared.py`, which are the same dead-citation CLASS in production files this plan does not declare; `x3zno3`'s F-08 measures them but excludes them, and review routed them to open backlog `3tov52` (F-07). EXCLUDES `tests/fixtures/runner_shared_premove_fingerprints.json`, the retained historical capture the deleted comment describes, whose own disposition is a separate decision nobody has made (F-08). EXCLUDES any production change, any new test, any mechanical guard against a census table returning (owned by `76ic0k`), and any edit to the module docstring.
- Scope-Paths: tests/test_runner_shared.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 5v4p2l
- Set: structpin
- Order: 6
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: fdmo2v
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved

- 2026-10-02 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Re-measured at HEAD d5b97344f: census (LANE_INTEGRATION_MOVED 0 loads, survivors live), 3 mentions, dead paragraph symbols 0 hits, 135 passed; E-01 cut verified in memory (26 lines, 0 residue, ruff check+format clean). Fixed: Deferred carrier re-routed from x3zno3 (which excludes the family and hands it to done item xvp5vx) to open backlog 3tov52 with the three sites named, false Carrier-Evidence removed; exact removed-line bar; ruff format check; runner/executor finalize ownership.
- 2026-10-02 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `5v4p2l`. Every claim below was MEASURED in this lane at HEAD `dbbd7074b` before being written, and the measurement CORRECTED the item's instruction rather than restating it. THREE THINGS A REVIEWER SHOULD CHECK FIRST. (1) The item's premise VERIFIES exactly: an AST census of all five module-level assignments in the file shows `LANE_INTEGRATION_MOVED` with 0 loads and the other four live (F-01), and it is the last one, since `b02ohu` and `ery0ia` between them removed the other eleven (F-02). (2) THE ITEM'S INSTRUCTION IS UNSAFE AND IS WIDENED HERE ON EVIDENCE: deleting only the table and the comment ABOVE it leaves two surviving `LANE_INTEGRATION_MOVED` mentions in the paragraph BELOW it, which I measured by performing exactly that narrow deletion and counting the residue (F-03). The widening is a CORRECTION of the item, not opportunistic growth, and the region deleted is contiguous and ends at a provable boundary. (3) THE DELETION WAS PERFORMED AND VALIDATED BEFORE BEING WRITTEN UP, then reverted: `135 passed` before and after, `ruff check --select E4,E7,E9,F` clean, and the post-edit AST census showing exactly `BOTH`/`_MODULES`/`HOST_LABELS` live with `INJECTED` unchanged (F-05, F-06). GATE NOTE: item `5v4p2l` carries no `- Blocks-Release:`, so this plan inherits none and invents none; `- Work-Kind: chore` and `- Priority: low` are INHERITED from the item and both remain correct, because deleting unread test data changes nothing a user can perceive. SET CHOICE: `structpin`, which is the Set that owns this work (`b02ohu` is `structpin` Order 01 and deleted this table's nine siblings), rather than a new Set named after the item; Order 06 was the next free Order.
- 2026-10-02 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave `tests/test_runner_shared.py` carrying no module-level census data that no test reads, and leave behind no citation to a symbol that does not exist, so a future reader of the file's header finds only tables that are actually consumed.

The test of success is two-sided, because the one-sided version of this change is what makes it dangerous. The dead table must be gone, AND the file must afterwards contain zero mentions of `LANE_INTEGRATION_MOVED`; a deletion that satisfies only the first half trades a dead table for two dangling citations and must be treated as a failure, not a partial success.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the last dead census table

- [x] E-01 DELETE THE ONE CONTIGUOUS DEAD REGION FROM `tests/test_runner_shared.py`, ADDING NO REPLACEMENT. The region begins at the comment line starting `# integpath-02 (\`6sb3yu\`): the lane->main integration seam, extracted LATER than the 34 above` and runs through the `LANE_INTEGRATION_MOVED = (` tuple and its three string members, then through the blank line, then through the entire paragraph beginning `# stalemerge-01 (\`87apfx\`) E-05: the refusal CAUSE and conflict SHAPE machinery`, ending at and INCLUDING the bare `#` continuation line that immediately precedes the comment line starting `# The host label each runner MUST bind into \`integrate_lane_branch\``. THAT LAST COMMENT IS THE BOUNDARY AND MUST SURVIVE: those three lines document the LIVE `HOST_LABELS` assignment, which has 2 loads inside `LaneIntegrationBehaviorTests` (F-01), so deleting them would strip a live symbol's only documentation. LOCATE THE BOUNDARY BY CONTENT, NEVER BY LINE NUMBER: the file is over 6,000 lines and is declared by two other pending plans (F-09), so any offset recorded here may have moved; find the three anchor strings quoted above and delete between them. DELETE NOTHING ELSE: not `BOTH`, not `_MODULES`, not `INJECTED` and its long preceding comment, not `HOST_LABELS`, not the module docstring, not the `# Replacement behavioral coverage for symbols whose post-move implementations were updated:` block below `HOST_LABELS`, and no test. DO NOT substitute a replacement census, a shortened table, a `# (deleted)` tombstone comment, or a note explaining what used to be here: the file's module docstring already records the harness history, and a tombstone is a fresh citation to a symbol that will not exist. VERIFY THE TABLE IS GENUINELY UNREAD IMMEDIATELY BEFORE DELETING, AND TREAT A NONZERO COUNT AS A STOP CONDITION, exactly as sibling plans `b02ohu` E-06(b) and `9g97e5` E-01 did for their own targets: run an AST census of module-level assignments and their `Load` counts over the file as found, and confirm `LANE_INTEGRATION_MOVED` is 0. If it is nonzero, a concurrent lane has given it a reader; DO NOT DELETE, mark this item `blocked`, and report which test now reads it. ALSO CONFIRM, in the same pass, that no dynamic access reaches it (`getattr`, `globals()`, `vars()`, `__dict__`), since an AST `Load` count cannot see those; measured zero at authoring (F-05).
  - Depends on: none
  - Expected outcome: `rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py` returns NO match, where it returned three before (one definition plus two prose mentions); the file's module-level assignments are exactly `BOTH`, `_MODULES`, `INJECTED` and `HOST_LABELS`, each with a nonzero `Load` count; `HOST_LABELS` and its three-line comment are byte-identical to before; `ruff check --select E4,E7,E9,F tests/test_runner_shared.py` reports `All checks passed!`; and `python3 -m pytest tests/test_runner_shared.py -o addopts=""` reports the same count as the pre-edit baseline (`135 passed` when measured at authoring HEAD `dbbd7074b`, to be re-derived rather than trusted). The diff is deletion-only: zero added lines and exactly 26 removed lines at review HEAD `d5b97344f` (9-line `6sb3yu` comment, 5-line tuple, 1 blank, 11-line `87apfx` paragraph); a different count means the region moved or changed and must be explained. Review verified this cut in memory: 0 surviving `LANE_INTEGRATION_MOVED` and 0 `LaneIntegrationExtractionTests` mentions, survivor census `{BOTH: 20, _MODULES: 25, INJECTED: 1, HOST_LABELS: 2}`, `ruff check --select E4,E7,E9,F -` and `ruff format --check -` both exit 0.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- P16 PROHIBITS THIS SHAPE OUTRIGHT AND IS THE LICENSE FOR THE DELETION. `GUIDING_PRINCIPLES.md` Section 16 states "No count or census pins: Never assert on the number of callers, call-site counts, definition counts, or closure sizes as a proxy for an invariant", and `AGENTS.md` repeats it as clause (2) of "TEST OUTCOMES, NOT CODE STRUCTURE (NO CODE-PINNING TESTS)". A census table that no test even reads is the degenerate case: it carries the prohibited shape and buys nothing at all.
- THE SET'S ESTABLISHED HOUSE STYLE FOR THIS EXACT FILE IS MEASURE-THEN-DELETE-WITH-A-STOP-CONDITION. `b02ohu` E-06(b) deleted nine of this file's census tables and required "Re-measure the reference counts at execution before deleting; do not trust these numbers"; `9g97e5` E-01 made its carrying pin's liveness an explicit STOP rather than an assumption. E-01 follows both deliberately, on the same file.
- THIS FILE'S OWN MODULE DOCSTRING ALREADY RECORDS THE HARNESS HISTORY, WHICH IS WHY NO TOMBSTONE IS NEEDED. It states that the AST fingerprint harness "was deleted in commit `19313eed`" and that `tests/fixtures/runner_shared_premove_fingerprints.json` is "a retained historical capture that no test reads". The deleted comment's whole subject is an exemption from that dead harness, so the context a future reader needs already lives in the docstring and does not need re-stating beside an absent table.
- `b02ohu` AND `ery0ia` EACH NAMED THIS TABLE AND DELIBERATELY LEFT IT, so this plan is the recorded handoff and not a duplicate. `ery0ia`'s Deferred section says of it: "`LANE_INTEGRATION_MOVED`, the twelfth dead table, is NOT deleted here ... it is the one dead name that neither this plan nor `b02ohu` claims (F-05) ... RECORDED HERE rather than filed as a new backlog item". Its Scope check repeats it: "`LANE_INTEGRATION_MOVED` is dead and is not deleted ... that is a deliberate boundary against `b02ohu`, not an oversight."
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This matters more than usual here, because E-01's deletion boundary is defined by content anchors in a 6,000-line file that two other pending plans declare.

## Findings

| # | Severity | Subject | Measurement in this lane at HEAD `dbbd7074b` | Consequence for this plan |
|---|---|---|---|---|
| F-01 | HIGH | the target table | **THE ITEM'S PREMISE VERIFIES EXACTLY: THE TABLE IS THE ONLY DEAD MODULE-LEVEL ASSIGNMENT LEFT IN THE FILE.** An AST census of every module-level `Assign`/`AnnAssign` in `tests/test_runner_shared.py`, counting `ast.Name` nodes in `Load` context per name, returns five assignments: `BOTH` (20 loads), `_MODULES` (25), `INJECTED` (1), `LANE_INTEGRATION_MOVED` (**0**), `HOST_LABELS` (2). The single `Name` node bearing the target's id is its own `Store`. `INJECTED`'s one load is in `WrapperTests.test_each_runner_keeps_a_wrapper_at_the_original_name` and `HOST_LABELS`' two are in `LaneIntegrationBehaviorTests`, so both are genuinely live and neither may be touched. | The deletion target is confirmed and unique, and the four survivors are named so E-01 can forbid touching them. `HOST_LABELS` being live is what makes E-01's deletion boundary load-bearing rather than cosmetic. |
| F-02 | MED | closure of the Set's cleanup | **THIS IS THE LAST OF THE TWELVE, SO THE SET CLOSES WITH IT.** `ery0ia`'s F-04 enumerated twelve dead tables in this file. Searching each name repository-wide now: `INTEGRATION_CAUSE_SHARED`, `LANE_INTEGRATION_WRAPPED`, `REHOMED_BACKLOG_CLOSE_CALL_SITES`, `ALL_SHARED_RUN_CHECKED_CALLERS`, `UNMOVABLE`, `HOST_NAMING_ONLY`, `REDOCUMENTED_SINCE_MOVE`, `RELOCATED_RUN_CHECKED_CALLERS`, `NATIVE_SHARED_RUN_CHECKED_CALLERS`, `DOCUMENTED_SINCE_MOVE` and `SUPERSEDED_SINCE_MOVE` return ZERO hits in any `.py` file; only `LANE_INTEGRATION_MOVED` survives. `git show 61eca9ccd -- tests/test_runner_shared.py` confirms `b02ohu` removed nine of them in one commit. | Confirms the item is not stale and that no sibling plan is still mid-flight on the same subject. It also means E-01 needs no coordination with `b02ohu` or `ery0ia`, both of which are `executed`. |
| F-03 | HIGH | the item's instruction | **THE ITEM'S INSTRUCTION, FOLLOWED LITERALLY, LEAVES TWO DANGLING CITATIONS, MEASURED BY DOING IT.** The item says to delete "the dead table and its associated comment block". I deleted exactly the `6sb3yu` comment above the table plus the table and its trailing blank, then counted: TWO `LANE_INTEGRATION_MOVED` mentions survive, both in the paragraph BELOW, reading "pinned as a SEPARATE list rather than appended to `LANE_INTEGRATION_MOVED`" and "`LANE_INTEGRATION_MOVED` drives `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners`". The narrow deletion therefore converts one dead table into two references to a symbol that no longer exists. | THIS IS WHY THE PLAN'S SCOPE IS WIDER THAN THE ITEM'S SENTENCE, and the widening is a correction on evidence rather than scope creep. It is also why the Goal is stated two-sided and why V-01 demands a ZERO-match search rather than merely the table's absence. |
| F-04 | HIGH | the paragraph below the table | **THAT PARAGRAPH IS ITSELF ALREADY ORPHANED BY `b02ohu`, SO DELETING IT REMOVES A SECOND DEFECT RATHER THAN COLLATERAL PROSE.** The `# stalemerge-01 (\`87apfx\`) E-05` paragraph was written to explain why `INTEGRATION_CAUSE_SHARED` was "pinned as a SEPARATE list rather than appended to `LANE_INTEGRATION_MOVED`". `git blame` attributes it to `caf84f1fd` (the `87apfx` work) while the table above is `2129354ad` (`6sb3yu`), so they are separate authorships, and `b02ohu` deleted `INTEGRATION_CAUSE_SHARED` in `61eca9ccd` WITHOUT deleting the paragraph that introduces it. Its every cited symbol is now absent: `INTEGRATION_CAUSE_SHARED` (0 hits in any `.py`), `LANE_INTEGRATION_MOVED` (dead), and `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners` (0 definitions; its one mention is this paragraph). The commit left it sitting directly above the unrelated `HOST_LABELS` assignment, so the file currently reads as though that paragraph documents `HOST_LABELS`, which it does not. | The region E-01 deletes is CONTIGUOUS and wholly dead, which is what makes the single-region deletion clean. It also means the paragraph is not `87apfx`'s live reasoning being discarded: the decision it records is already executed and its subject already gone. |
| F-05 | HIGH | deletion safety | **THE FULL DELETION WAS PERFORMED AND MEASURED IN THIS LANE BEFORE BEING WRITTEN UP, THEN REVERTED.** With the whole region removed and the `HOST_LABELS` comment preserved: `rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py` exits 1 with no output; the post-edit AST census is exactly `BOTH` (20), `_MODULES` (25), `HOST_LABELS` (2) plus `INJECTED` unchanged; `ruff check --no-cache --select E4,E7,E9,F tests/test_runner_shared.py` reports `All checks passed!`; and `python3 -m pytest tests/test_runner_shared.py -o addopts=""` reports `135 passed`, identical to the pre-edit baseline. A search for dynamic access (`getattr(.*LANE`, `globals()`, `vars()[`, `__dict__[`) in the file returns nothing, and `conftest.py`/`tests/support.py` contain no census or module-scanning machinery, so the 0 `Load` count is not hiding a reflective reader. Restored with `git status --short` empty. | The change is proven safe rather than argued safe, and E-01's expected outcome can state real numbers. Crucially the test count does NOT move, which is the signature of deleting data rather than coverage. |
| F-06 | MED | `ruff` under the pinned hook | **THE PINNED HOOK'S RULESET PASSES; A LOCALLY CONFIGURED `ruff` REPORTS 72 PRE-EXISTING ERRORS THAT ARE NOT THIS PLAN'S.** `.pre-commit-config.yaml` pins `ruff-pre-commit` at `rev: v0.4.4` with `args: [--fix]` and no project `[tool.ruff]` table in `pyproject.toml` (and no `ruff.toml`/`.ruff.toml` in the repo), so the enforced ruleset is ruff's default `E4,E7,E9,F`. Under that selection the file is clean BEFORE and AFTER the edit. A bare `ruff check` in this environment resolves a user-level config that enables far more (`UP030` x27, `UP032` x26, `SIM117` x9, `I001` x3, plus `EXE001`, `RUF100`, `B023`, `RUF059`, `PLW1510`), reporting `Found 72 errors` on the UNEDITED file. | V-01 pins `--select E4,E7,E9,F` explicitly, so an executor does not mistake another party's pre-existing style debt for a regression this plan caused, and does not "fix" 72 unrelated findings in a one-region deletion. |
| F-07 | MED | `LaneIntegrationExtractionTests` | **THE DELETED COMMENT CITES A CLASS THAT DOES NOT EXIST, AND THE THREE SURVIVING CITATIONS OF IT ARE IN UNDECLARED PRODUCTION FILES.** `LaneIntegrationExtractionTests` has ZERO definitions repository-wide; its four mentions are `tests/test_runner_shared.py` (inside the region E-01 deletes), `agent_workflows/oc_runipd.py::integrate_lane_branch`'s docstring, and two sites in `agent_workflows/runner_shared.py`. So this deletion removes the TEST-SIDE instance as a side effect, and three production-side instances remain. Plan `x3zno3` (`- Status: approved`, `- Scope-Paths:` including `agent_workflows/runner_shared.py` and `tests/test_runner_shared.py`) MEASURES this family in its F-08 but does NOT own it: CORRECTED AT REVIEW, its Deferred row EXCLUDES the family ("they are not given E-items because neither concerns `should_color`") and hands it to `- Carrier: xvp5vx`, which is now `done` and never carried it (`xvp5vx`'s item text has zero mentions of `LaneIntegrationExtractionTests`). `x3zno3` also does not declare `agent_workflows/oc_runipd.py`. The live owner of this defect class is open backlog `3tov52` ("Retire or update dangling test-symbol citations for code pins in runner_shared and agy_runipd"), which names the class and `runner_shared` but not this family or `oc_runipd`. | EXCLUDED with a route that review corrected to `3tov52`, not stranded. Adding two production modules to `- Scope-Paths:` for three comment lines would widen a one-file deletion into a production edit, and `x3zno3`'s F-08 explicitly reasons that each such family "needs its own decision about what, if anything, now holds the property". Named here so the next reader need not re-measure. |
| F-08 | LOW | the premove fixture | **THE FIXTURE THE DELETED COMMENT DESCRIBES IS STILL ON DISK AND STILL UNREAD, AND ITS DISPOSITION IS NOBODY'S DECISION YET.** `tests/fixtures/runner_shared_premove_fingerprints.json` exists (153,036 bytes). The file's module docstring calls it "a retained historical capture that no test reads". Deleting the comment that describes an exemption from it does not change its status either way. | EXCLUDED with reason. Whether to keep a 150 KB unread historical capture is a judgement about the value of the record, not a dead-code cleanup, and the module docstring (which this plan does not touch) still explains what it is. Deliberately not filed as a carrier: the docstring already documents it accurately as unread, so nothing is broken and no work is owed. |
| F-09 | MED | cross-plan collision | **TWO OTHER PENDING PLANS DECLARE THIS FILE AND NEITHER TOUCHES THIS REGION, CHECKED RATHER THAN ASSUMED.** Enumerating `- Scope-Paths:` across `.aw/records/plans/pending/` for `tests/test_runner_shared.py` returns exactly two: `qkwu1r` (`approved`, Set `p7dtbr`), whose subject is `runner_shared.poll_for_integration_window` and whose target symbols in this file (`merge_in_progress`, `POLL_BOUND_*`) all sit beyond line 1100 and which contains no mention of `LANE_INTEGRATION_MOVED`; and `x3zno3` (`approved`, Set `pn7rw3`), whose test-side item E-03 targets the `SUPERSEDED_SINCE_MOVE` comment block. MEASURED: `rg -n "SUPERSEDED_SINCE_MOVE" tests/test_runner_shared.py` now returns NOTHING, so `ery0ia` already deleted that block and `x3zno3` E-03 is in its own documented "satisfied by deletion" branch; its remaining work is in `agent_workflows/runner_shared.py`. | `- Item-Dependencies: none` is correct across Sets, not merely within `structpin`. Both neighbours edit disjoint regions of the file, so any execution order works. This is also why E-01 anchors its boundary by CONTENT: a neighbour landing first shifts every line number in this plan. |
| F-10 | MED | suite baseline | **THE SUITE IS NOT GREEN AT THIS LANE'S HEAD AND THE THREE FAILURES ARE OTHER PARTIES' FILED BUGS.** Bare `python3 -m pytest` reports `3 failed, 4624 passed, 2 skipped, 3 warnings in 119.95s`. The failures are `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, and `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. This is the IDENTICAL failure set and pass count that sibling plan `9g97e5` F-08 measured independently, where each is recorded as already filed (`bxnhdj`, `6bolin`, `8jeh4x`). None is in a file this plan touches. | The validation bar is an UNCHANGED NAMED FAILURE SET, not green and not a pass count. Named so an executor does not read this red as its own, try to fix another party's release-gated bug, or stall. Re-derive on the tree as found; the pass count will have risen as lanes land. |
| F-11 | LOW | `76ic0k` | **NOTHING MECHANICALLY STOPS A CENSUS TABLE RETURNING TO THIS FILE, AND THAT IS A RECORDED BOUND RATHER THAN AN OVERSIGHT.** Set Order 02 (`76ic0k`, `- Status: approved`, `- Scope-Paths: tests/test_no_code_structure_pins.py, CONTRIBUTING.md`) owns the author-time guard against new code-structure pins. Sibling plans `44c42h` and `9g97e5` both record that the count/census shape is syntactically indistinguishable from a legitimate assertion and is therefore an accepted bound on that guard. | Recorded in Deferred with no new carrier, because the general case is already owned by a live sibling plan in this same Set. It is also the honest answer to "will this recur": possibly, and review plus P16 is the control. |

## Proposed changes (ordered, validatable)

1. Re-measure the AST `Load` census on the file as found and confirm `LANE_INTEGRATION_MOVED` is still 0 and that no dynamic access reaches it; STOP if it has gained a reader (E-01, V-01 (a)).
2. Delete the one contiguous dead region, anchored by content at both ends, adding nothing (E-01).
3. Prove the deletion is complete rather than partial, by showing ZERO surviving mentions of the name, and prove it is confined, by showing `HOST_LABELS` and its comment intact and the per-file test count unmoved (V-01 (b) through (f)).

## Deferred / out of scope (with reason)

- THE THREE `LaneIntegrationExtractionTests` CITATIONS IN `agent_workflows/oc_runipd.py` AND `agent_workflows/runner_shared.py`. F-07: the class has zero definitions, so these are the same dead-citation class as the comment this plan deletes, but they sit in production files this plan does not declare, Widening a single-file deletion into two production modules for three comment lines would convert a clean non-collision (F-09) into a real one. ROUTE CORRECTED AT REVIEW: the authored row named `x3zno3` as `- Carrier:` with that plan as `- Carrier-Evidence:`, but `x3zno3` explicitly EXCLUDES this family (its Deferred row routes it to `xvp5vx`, which is `done` and never mentions it), so neither field was true. The defect CLASS is carried by open backlog `3tov52` (dangling test-symbol citations in `runner_shared` and `agy_runipd`); its text does not yet name `LaneIntegrationExtractionTests` or `oc_runipd.py`, so whoever executes or graduates `3tov52` must include the three sites (`oc_runipd.integrate_lane_branch`'s docstring, `runner_shared.integrate_lane_branch`'s docstring, and the `runner_shared` `INTEGRATION_CAUSE_TOKEN_PREFIX` decision comment). This plan does NOT edit `3tov52`, because that path is not in `- Scope-Paths:`; the note here is the handoff.
  - Carrier: 3tov52
- `tests/fixtures/runner_shared_premove_fingerprints.json`, THE 150 KB UNREAD HISTORICAL CAPTURE the deleted comment describes an exemption from. F-08: whether to retain a deliberately-kept historical record is a judgement about the record's value, not a dead-code cleanup, and it is orthogonal to whether a comment about it is accurate. Deliberately not filed as a carrier: the file's module docstring already describes it correctly as "a retained historical capture that no test reads", so there is no false claim to fix and no outstanding obligation; filing one would assert work that nobody has decided is wanted.
  - Carrier-Declined: the module docstring already documents the fixture accurately as unread, so no defect exists; retaining or removing a deliberate historical capture is a maintainer's judgement about the record, not cleanup work this Set owns
- A MECHANICAL GUARD AGAINST A CENSUS TABLE RETURNING TO THIS FILE. F-11: the general case is owned by Set Order 02 (`76ic0k`, `approved`), and the count/census shape is a recorded accepted bound on that guard in both `44c42h` and `9g97e5`. A bespoke per-file detector here would be a new content pin over a test module, on a concern this plan does not own.
  - Carrier-Declined: an accepted, recorded bound on live sibling plan `76ic0k` (Set `structpin`, Order 02), which owns the author-time guard and whose siblings record count-shape detection as syntactically undecidable; nothing is left unowned
- THE THREE PRE-EXISTING SUITE FAILURES. F-10: each belongs to another party, none is in a file this plan touches, and each is already an open backlog item (`bxnhdj`, `6bolin`, `8jeh4x`). Touching them is what the shared-checkout rule forbids. They are named only so the validation bar can be stated as an unchanged failure set.
  - Carrier-Declined: each is already carried by its own open backlog item (`bxnhdj`, `6bolin`, `8jeh4x`) and belongs to another party; re-filing would duplicate a live item
- THE 72 PRE-EXISTING `ruff` FINDINGS a locally-configured `ruff` reports on this file (F-06). They are not enforced by the pinned `v0.4.4` hook's default `E4,E7,E9,F` selection, they exist identically before this plan's edit, and auto-fixing modernization rules (`UP030`, `UP032`) across a 6,000-line file declared by two other pending plans would create exactly the collision F-09 shows does not currently exist.
  - Carrier-Declined: not a defect under the repository's own enforced configuration (no `[tool.ruff]` table, hook pinned to default `E4,E7,E9,F`, which passes); a different local config reporting more is that config's opinion, not an obligation on this repo

## Scope check

- Over-scope: none. One file, one contiguous deletion, zero added lines, no production change, no new or removed test, no `.spec.md` touched, and no `.aw/` record other than this plan changed.
- THE SCOPE IS WIDER THAN THE BACKLOG ITEM'S SENTENCE, DELIBERATELY AND ON MEASURED EVIDENCE. The item names "the dead table and its associated comment block"; E-01 also deletes the orphaned `87apfx` paragraph below it. This is a CORRECTION of the item, not opportunistic growth: F-03 measured that the narrow reading leaves two dangling `LANE_INTEGRATION_MOVED` citations, and F-04 measured that the paragraph is itself already dead in every symbol it names. The item's own requirements are unchanged; only the extent of the region needed to satisfy them without creating a new defect is corrected.
- NO CROSS-PLAN COLLISION, CHECKED RATHER THAN ASSUMED (F-09): exactly two other pending plans declare this file, and both edit regions that provably do not overlap this one. `- Item-Dependencies: none` is therefore correct across Sets.
- Under-scope: this plan leaves the three production-file `LaneIntegrationExtractionTests` citations to open backlog `3tov52` (F-07; corrected at review from `x3zno3`, which excludes them), leaves the unread premove fixture in place (F-08), does not prevent a census table being written again (F-11, an accepted bound owned by `76ic0k`), and does not touch the module docstring whose harness history this deletion relies on remaining accurate (it is, and it needs no amendment because it describes the harness and the fixture, never the deleted table).

## Required tests / validation

Outcome tests only. No production source is read by any test, nothing is asserted about source text, and no replacement pin of any kind is written: this plan removes data and adds nothing, which is exactly what P16 prescribes. All evidence must be PASTED, per the execution contract.

1. STOP CONDITION FIRST, BEFORE THE EDIT: an AST census over `tests/test_runner_shared.py` as found, printing every module-level assignment with its `Load` count, showing `LANE_INTEGRATION_MOVED` at **0**. Plus `rg -n "getattr\(.*LANE|globals\(\)|vars\(\)\[|__dict__\[" tests/test_runner_shared.py` returning nothing. If the count is nonzero or a dynamic access appears, DO NOT DELETE; report.
2. `rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py` -> NO match after the edit, where it returned THREE lines before. Paste the empty result or the nonzero exit. A result showing one or two surviving lines is the F-03 failure mode and must be treated as a failed deletion, not a partial one.
3. `rg -c "LANE_INTEGRATION_MOVED" -g '!*.md' .` -> no match repository-wide in any non-markdown file (the `.md` exclusion is required: plan and review records legitimately discuss the name in prose and must not be edited).
4. The post-edit AST census again, showing exactly `BOTH`, `_MODULES`, `INJECTED` and `HOST_LABELS`, each with a nonzero `Load` count.
5. `git diff -- tests/test_runner_shared.py` pasted in full, showing a deletion-only hunk with ZERO added lines, and showing the three-line `# The host label each runner MUST bind into \`integrate_lane_branch\`` comment and the `HOST_LABELS` assignment as unchanged context.
6. `ruff check --no-cache --select E4,E7,E9,F tests/test_runner_shared.py` -> `All checks passed!`, AND `ruff format --check tests/test_runner_shared.py` -> already formatted, because the pinned hook also runs `ruff-format` (review verified both on the cut in memory). The explicit `--select` is REQUIRED and matches the pinned `v0.4.4` hook's default ruleset; a bare `ruff check` may resolve an unrelated local config and report dozens of pre-existing findings (F-06).
7. `python3 -m pytest tests/test_runner_shared.py -o addopts=""` -> the same count as the pre-edit baseline re-derived on the tree as found (`135 passed` at authoring). The cleared `addopts` is required to see the per-test count, per AGENTS.md. AN UNCHANGED COUNT IS THE POSITIVE SIGNAL HERE: it is what distinguishes deleting unread data from deleting coverage.
8. Bare whole suite `python3 -m pytest`, pasted with its summary line. THE BAR IS AN UNCHANGED NAMED FAILURE SET, NOT A PASS COUNT AND NOT GREEN (F-10). Re-derive before any edit, record WHICH tests fail, and require the after-set identical by name.
9. `git status --short` -> `tests/test_runner_shared.py` as the ONLY modified path, with no scratch file left behind.

## Spec / documentation sync

N/A with reason. This plan deletes unread test data and dead comment prose from one test file. It changes no behavior, no CLI surface, no record grammar, and no public contract, so no `.spec.md` is amended and `- Scope-Paths:` declares no spec file. Specifically NOT edited: `GUIDING_PRINCIPLES.md` P16, which already prohibits census pins and needs no amendment to license this removal; the module docstring of `tests/test_runner_shared.py`, which already records the deleted comment's context (the `19313eed` harness deletion and the retained premove fixture) accurately and so neither needs correcting nor may be relied on less after this change; and no user-facing documentation, since nothing here reaches a reader of the installed package.

## Open questions

### OQ-01: Should the deletion also remove the three surviving `LaneIntegrationExtractionTests` citations in the two production files, given that this plan removes the test-side one as a side effect?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED ON OWNERSHIP AND ON COLLISION RISK: NO, and the refusal is recorded because a reviewer will reasonably ask, since this deletion does remove the fourth instance of the same dead citation.

  THE DEFECT IS REAL, WHICH IS WHY IT NEEDS A REASON RATHER THAN A HAND-WAVE. `LaneIntegrationExtractionTests` has zero definitions repository-wide (F-07), and after this plan three citations of it survive: one in `agent_workflows/oc_runipd.py::integrate_lane_branch`'s docstring and two in `agent_workflows/runner_shared.py`. Two of those ship in the installed package, which by `x3zno3`'s own F-02 reasoning is the more consequential location.

  THREE REASONS IT IS STILL REFUSED HERE. (1) IT HAS AN OWNER, THOUGH NOT THE ONE AUTHORING NAMED: CORRECTED AT REVIEW, `x3zno3`'s F-08 measures this family but its Deferred row EXCLUDES it and routes it to `xvp5vx`, which is `done` and never carried it; the open item that owns the dead-test-citation CLASS is backlog `3tov52`, and the Deferred row now names it as the carrier and lists the three sites it must cover. (2) COLLISION: F-09 measures that this plan currently has no overlap with either neighbour; adding `agent_workflows/runner_shared.py` would put it in direct contention with both `x3zno3` and `qkwu1r`, in a 36,000-line file, for three comment lines. (3) SCOPE: backlog `5v4p2l` names a dead census table in one test file. Widening into two production modules is the opportunistic growth the execution contract forbids, and it is a different judgement anyway, because each production citation must be replaced with a statement of what now holds the property rather than simply deleted (the shape `x3zno3` and `9vtas9` both apply).

  WHY THE SIDE-EFFECT REMOVAL IS NONETHELESS CORRECT: the test-side citation is INSIDE the dead region, so leaving it would mean keeping dead census data to preserve a dead citation. Deleting it reduces the family from four to three and strands nothing, because the remaining three are routed to `3tov52` with their sites named in the Deferred row.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: EIGHT artifacts, each a pasted command and its real output. (a) THE STOP CONDITION, CHECKED BEFORE THE EDIT: an AST census script over `tests/test_runner_shared.py` printing each module-level assignment name with its `ast.Name`-in-`Load` count, pasted, showing `LANE_INTEGRATION_MOVED` at `0` and the other four nonzero; PLUS `rg -n "getattr\(.*LANE|globals\(\)|vars\(\)\[|__dict__\["  tests/test_runner_shared.py` pasted showing no match. A nonzero load count or any dynamic access is a STOP: do not delete, mark this item `blocked`, and report which reader appeared. (b) THE DELETION IS COMPLETE, NOT PARTIAL: `rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py` pasted showing NO match (include the empty output or the nonzero exit). STATE EXPLICITLY that the pre-edit count was three (one `Store` plus two prose mentions) and the post-edit count is zero; a surviving one or two is the F-03 failure mode and FAILS this item. (c) NO RESIDUE REPOSITORY-WIDE IN CODE: `rg -c "LANE_INTEGRATION_MOVED" -g '!*.md' .` pasted showing no match, with an explicit note that `.md` records are excluded deliberately because plan and review prose legitimately discusses the name and must not be edited. (d) THE SURVIVORS ARE INTACT AND LIVE: the post-edit AST census pasted, showing exactly `BOTH`, `_MODULES`, `INJECTED`, `HOST_LABELS`, each with a nonzero count. (e) THE EDIT IS DELETION-ONLY AND BOUNDED: `git diff -- tests/test_runner_shared.py` pasted IN FULL plus `git diff --numstat -- tests/test_runner_shared.py` showing `0	26` (or a different removed count with an explanation of what moved), showing zero added lines and showing as unchanged context both the `# The host label each runner MUST bind into \`integrate_lane_branch\`` comment and the `HOST_LABELS = {...}` assignment. An added line of any kind (including a tombstone comment) FAILS this item. (f) LINT AND PER-FILE TESTS: `ruff check --no-cache --select E4,E7,E9,F tests/test_runner_shared.py` pasted showing `All checks passed!` (the explicit `--select` is required; see F-06) and `ruff format --check tests/test_runner_shared.py` pasted showing the file already formatted, and `python3 -m pytest tests/test_runner_shared.py -o addopts=""` pasted showing the SAME count as a pre-edit baseline you measured yourself on the tree as found (`135 passed` at authoring HEAD `dbbd7074b`, which is historical context and NOT the bar). A count that FELL is a failure: it would mean a test was removed, not data. (g) THE SUITE'S FAILURE SET IS UNCHANGED: bare `python3 -m pytest` pasted with its summary line BESIDE a baseline re-derived before any edit, with the FAILING TEST NAMES listed on both sides and shown IDENTICAL (not green; name the three pre-existing failures of F-10 explicitly if they appear). The bare run must NOT be given `-n0`, an extra `-q`, or `-p no:randomly`. (h) `git status --short` pasted showing `tests/test_runner_shared.py` as the ONLY modified path and no scratch file left behind.
    A run that shows only (b), (f) and (h) is INSUFFICIENT and does not satisfy this item. The specific risk this evidence set exists to rule out is NOT that a test broke, because deleting unread data cannot break one; it is that the deletion was either INCOMPLETE (leaving the F-03 dangling citations, caught only by (b) and (c)) or OVERSHOT (taking `HOST_LABELS`' live documentation with it, caught only by (d) and (e)). A green suite is consistent with both of those failures, which is why neither (b) nor (e) may be skipped.
  - Observed evidence:
    (a) STOP CONDITION CHECKED BEFORE EDIT:
    ```sh
    python3 -c '
    import ast
    with open("tests/test_runner_shared.py") as f:
        tree = ast.parse(f.read())
    assignments = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                assignments.append(node.target.id)
    load_counts = {name: 0 for name in assignments}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in load_counts:
                load_counts[node.id] += 1
    for name in assignments:
        print(f"{name}: {load_counts[name]}")
    '
    ```
    Output:
    ```
    BOTH: 20
    _MODULES: 25
    INJECTED: 1
    LANE_INTEGRATION_MOVED: 0
    HOST_LABELS: 2
    ```
    Dynamic access check:
    ```sh
    rg -n "getattr\(.*LANE|globals\(\)|vars\(\)\[|__dict__\[" tests/test_runner_shared.py
    ```
    Output: exit code 1 (no match).

    (b) DELETION IS COMPLETE, NOT PARTIAL:
    Pre-edit count was three (one definition/Store at line 91 plus two prose mentions at lines 98 and 101):
    ```sh
    rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py
    # 91:LANE_INTEGRATION_MOVED = (
    # 98:# list rather than appended to `LANE_INTEGRATION_MOVED`, and the reason is a scope decision worth stating
    # 101:# `LANE_INTEGRATION_MOVED` drives `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners`, which
    ```
    Post-edit:
    ```sh
    rg -n "LANE_INTEGRATION_MOVED" tests/test_runner_shared.py
    ```
    Output: exit code 1 (no match). Post-edit count is zero.

    (c) NO RESIDUE REPOSITORY-WIDE IN CODE:
    ```sh
    rg -c "LANE_INTEGRATION_MOVED" -g '!*.md' .
    ```
    Output: exit code 1 (no match). Note: `.md` records are excluded deliberately because plan and review prose legitimately discusses the name and must not be edited.

    (d) SURVIVORS INTACT AND LIVE:
    Post-edit AST census:
    ```sh
    python3 -c '
    import ast
    with open("tests/test_runner_shared.py") as f:
        tree = ast.parse(f.read())
    assignments = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                assignments.append(node.target.id)
    load_counts = {name: 0 for name in assignments}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in load_counts:
                load_counts[node.id] += 1
    for name in assignments:
        print(f"{name}: {load_counts[name]}")
    '
    ```
    Output:
    ```
    BOTH: 20
    _MODULES: 25
    INJECTED: 1
    HOST_LABELS: 2
    ```
    All four survivor assignments live with nonzero Load counts.

    (e) EDIT IS DELETION-ONLY AND BOUNDED:
    ```sh
    git diff -- tests/test_runner_shared.py
    ```
    Output:
    ```diff
    diff --git a/tests/test_runner_shared.py b/tests/test_runner_shared.py
    index ed7f467d8..be9358e57 100644
    --- a/tests/test_runner_shared.py
    +++ b/tests/test_runner_shared.py
    @@ -79,32 +79,6 @@ INJECTED: dict[str, str] = {
         "git_common_dir": "run_checked",
     }

    -# integpath-02 (`6sb3yu`): the lane->main integration seam, extracted LATER than the 34 above and
    -# therefore held to a DIFFERENT standard, stated here so the split is deliberate rather than an
    -# exemption. `runner_shared_premove_fingerprints.json` is a retained historical capture that no test
    -# reads; these three symbols do not appear in that fixture
    -# because they did not exist in it, so they have no pre-move fingerprint to match and adding them to
    -# `INJECTED` would make the fixture-backed tests raise `KeyError` rather than prove anything.
    -# `LaneIntegrationExtractionTests` is what replaces the fingerprint for them: it asserts the same
    -# three properties (no re-definition, object identity or a delegating wrapper, and no runner import)
    -# plus the host-label binding that a fingerprint could not express.
    -LANE_INTEGRATION_MOVED = (
    -    "dirty_tree_overlap",
    -    "build_lane_outcome",
    -    "integrate_lane_branch",
    -)
    -
    -# stalemerge-01 (`87apfx`) E-05: the refusal CAUSE and conflict SHAPE machinery, pinned as a SEPARATE
    -# list rather than appended to `LANE_INTEGRATION_MOVED`, and the reason is a scope decision worth stating
    -# because appending was TRIED FIRST AND REVERTED.
    -#
    -# `LANE_INTEGRATION_MOVED` drives `test_an_unwrapped_symbol_is_the_SAME_OBJECT_in_both_runners`, which
    -# demands that each host module carry the ATTRIBUTE. Satisfying it therefore requires adding ten
    -# `as <same-name>` re-exports to BOTH `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`,
    -# neither of which `87apfx` declares in its `Scope-Paths`, and the plan's Scope check explicitly forbids
    -# widening into undeclared host files without reporting first. Measured: the append made all nine tests
    -# in that class pass, at the cost of 36 added lines in each undeclared host module.
    -#
     # The host label each runner MUST bind into `integrate_lane_branch`. This value lands in a merge
     # commit subject on MAIN, so it records WHICH driver integrated a lane; the shared function gives it
     # no default precisely so a mis-binding cannot be silent.
    ```
    ```sh
    git diff --numstat -- tests/test_runner_shared.py
    ```
    Output:
    ```
    0	26	tests/test_runner_shared.py
    ```
    Zero lines added, exactly 26 lines removed. Unchanged context includes both the 3-line `# The host label each runner MUST bind into \`integrate_lane_branch\`` comment and the `HOST_LABELS` assignment.

    (f) LINT AND PER-FILE TESTS:
    ```sh
    ruff check --no-cache --select E4,E7,E9,F tests/test_runner_shared.py && ruff format --check tests/test_runner_shared.py
    ```
    Output:
    ```
    All checks passed!
    1 file already formatted
    ```
    Per-file test pre-edit baseline:
    ```sh
    python3 -m pytest tests/test_runner_shared.py -o addopts=""
    ```
    Output: `135 passed in 73.41s (0:01:13)`
    Per-file test post-edit:
    ```sh
    python3 -m pytest tests/test_runner_shared.py -o addopts=""
    ```
    Output: `135 passed in 40.76s`
    Test count is identical (135 passed).

    (g) SUITE FAILURE SET UNCHANGED:
    Pre-edit bare suite run:
    ```sh
    python3 -m pytest
    ```
    Output summary:
    `6261 passed, 2 skipped, 3 warnings in 424.79s (0:07:04)`
    Failing tests: None (0 failures).

    Post-edit bare suite run:
    ```sh
    python3 -m pytest
    ```
    Output summary:
    `6261 passed, 2 skipped, 3 warnings in 572.05s (0:09:32)`
    Failing tests: None (0 failures).
    Failure sets are identical (empty set).

    (h) GIT STATUS:
    ```sh
    git status --short
    ```
    Output:
    ```
     M tests/test_runner_shared.py
    ```
    Only declared scope file modified, zero scratch files left behind.
  - Result: pass

## Approval and execution gate

Execution is gated on explicit human approval (`- Status: approved`), per AGENTS.md. This plan is `to-review` and MUST NOT be executed until it has been reviewed and approval is recorded. `- Readiness:` is deliberately ABSENT: it is an output of `/plan-review`, and writing one at authoring time would forge a review that has not happened.

THE ONE JUDGEMENT A REVIEWER SHOULD ATTACK FIRST is not whether the table is dead, which is measured at zero loads and licensed outright by P16 with two precedents in this very Set and this very file. It is THE WIDENING IN F-03 AND F-04: this plan deletes eleven lines of comment prose the backlog item does not mention, on the argument that the item's literal instruction would leave two citations pointing at a deleted symbol and that the paragraph is independently dead in every symbol it names. If a reviewer judges that the `87apfx` paragraph carries reasoning worth keeping (it records a scope decision that was tried and reverted), the correct remedy is NOT to delete the table alone, which is the measured defect; it is to say so and have the plan revised to rewrite the paragraph without the dead names. The second judgement worth attacking is OQ-01's refusal to clean the three production-file citations of a class that does not exist, when this deletion removes the fourth.

Execution contract for whoever runs it: commit ONLY `tests/test_runner_shared.py`, through `aw commit <plan> -- tests/test_runner_shared.py`, never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and re-verify after any failed raw commit, because this is a SHARED CHECKOUT and `tests/test_runner_shared.py` is declared by two other pending plans (F-09); another party's restored path must not be swept in. THE DELETION BOUNDARY MUST BE FOUND BY CONTENT, NEVER BY THE LINE NUMBERS implied anywhere in this plan: a neighbour landing first shifts every offset in a 6,000-line file, and the three anchor strings in E-01 are what make the edit reproducible. Keep any scratch census script under the gitignored `tmp/`. Execute through `aw ipd begin` before any edit. The terminal transition is `aw ipd finalize`: under `aw oc run` / `aw agy run` the RUNNER performs it and the executor must not pre-empt it, while a human-driven execution runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` itself; never hand-roll the lifecycle move and never `git mv` this plan into `executed/`. Paste real runner output for every item; a claimed pass with no output does not satisfy V-01.

On success, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition, only after `aw ipd lint --phase pre-transition` conforms and V-01 carries pasted evidence. Backlog `5v4p2l` carries NO `- Blocks-Release:` gate, so none is inherited above and none may be invented; the item reaches `done` through the handoff route (this plan executed while carrying `- From-Backlog: 5v4p2l`), so do not close it by hand.

- Size assessment: standard
- Cohesion rationale: not required
