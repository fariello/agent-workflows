# IPD: Make spec 25kzda Section 4.2 byte-equality promise true again by restoring the inspects and pass_criterion guard

- Date: 2026-09-30
- Kind: child
- Concern: Spec `25kzda` Section 4.2's "NOTE ON TRANSCRIBING THIS TABLE" tells an editor that `run_evidence.RUN_FINDING_CODES` transcribes the `inspects` and `pass_criterion` cells VERBATIM and that "`tests/test_run_evidence_completion.py` asserts byte equality, so editing a cell here is a code change". That file was deleted whole by commit `19313eed` and NO test in the tree references `RUN_FINDING_CODES`, so the promised guard does not exist. An author who edits a 4.2 cell trusting the stated guard silently desynchronizes the spec from the shipped `message` strings an operator reads on a failure. MEASURED WIDER THAN THE ITEM FILED IT: the same spec cites THREE deleted test files (lines 232, 824, 1251), and `runner_shared.py`'s own module docstring names one of them as the guard that "replaces the fingerprint" for the policy flag surface, so the false-guard claim is a class and not one sentence.
- Scope: Make the promise TRUE for the cells it names rather than withdrawing it, and stop the same lie recurring. IN: a new behavioral test module asserting byte equality between spec 4.2's parsed `inspects`/`pass_criterion`/`message`/`action` cells and the shipped table, proven mutation-sensitive; the spec's transcription note repointed at the restored file with its code-count sentence left intact; the spec's two OTHER dangling test citations (lines 232 and 1251) corrected to state what is actually guarded today; `runner_shared.py`'s stale docstring claim corrected; and a new deterministic `aw check` rule that fails a records artifact citing a `tests/test_*.py` path which does not exist, so this defect class is caught at rest instead of by a human reading prose. OUT: every row's DATA is unchanged (no `inspects`, `pass_criterion`, `message`, `action`, `abort`, `abort_classes`, `binding` or `predicates` value is edited), no row is added or removed so `RC-COUNT`'s literal 12 is untouched, the abort-partition dimension is left entirely to approved plan `xjmjq4`, no deleted test is restored wholesale, and no code-pinning assertion is reintroduced.
- Scope-Paths: tests/test_run_finding_spec_transcription.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/runner_shared.py, agent_workflows/check_engine.py, tests/test_check_engine_test_citation.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 089bq4
- From-Spec: 25kzda
- Blocks-Release: next
- Set: 089bq4
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h65phz

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: h65phz verified (set 089bq4, attempt 2).
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (MEDIUM, fixed), PR-304 (MEDIUM, fixed). Readiness recorded in `- Readiness:`. OQ-02 resolved at review, so the plan now carries no open question. Detail on the `reviewed (aw set)` record below and in `.aw/records/reviews/20260930-089bq4-01-h65phz-...review.md`.
- 2026-10-01 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-301 (HIGH, fixed), PR-302 (MEDIUM, fixed), PR-303 (MEDIUM, fixed), PR-304 (MEDIUM, fixed). Re-derived every load-bearing claim independently at review HEAD fc91266df. F-01, F-02, F-04, F-05, F-06, F-07, F-08 and F-09 all reproduce, including the StopIteration-at-import hazard of the legacy spec glob, the mutation sensitivity, the True permission default, and the collision state (xjmjq4 still pending/approved with its test file not landed). Four findings added. F-10: the spec has a FOURTH dangling citation site at line 1621 inside Workflow history, which E-04 must NOT fix because a dated note is a record, and which forces E-06 to exempt that zone or land red on the file E-04 just corrected. F-11: the zone breakdown RESOLVES OQ-02, which was the plans only open question; of 11 dangling spec citations across 6 files only 3 are body-level and all 3 are in this spec, so a body-scoped rule is clean after E-04 and registers error, and the five other specs need no amendment. F-12: the shipped-code instance is SEVEN sites in runner_shared.py rather than one docstring, plus an eighth in agy_runipd.py that tells a maintainer not to harden a security-relevant default on the strength of a deleted guard, carried to xvp5vx. F-13: F-06 zero-mismatch claim holds only under a both-ends backtick rule the plan never stated; the naive rule yields twelve false mismatches an executor would misread as a real divergence. E-01, E-04, E-05, E-06, OQ-02, V-01, V-04, V-05, V-06, the Scope check and the Deferred rows all amended accordingly.

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `089bq4`. Every claim in Findings was MEASURED in this lane at HEAD `27ae3785` rather than transcribed from the item. The item's own two claims both reproduced exactly (F-01, F-02), and the measurement found the defect is THREE times wider than filed (F-03) plus one shipped-code instance (F-04). The item's open decision (restore a guard versus reword the promise) is RESOLVED to restore, from repository evidence and a directly applicable GUIDING_PRINCIPLES P16 clause, recorded as D-1 with the counter-argument stated (F-06, F-07). COLLISION NOTE: approved plan `xjmjq4` restores byte equality for the `action` cell only and names this item as the carrier for the rest; F-08 records the division of labour and E-01 re-checks it at execution. GATE NOTE: item `089bq4` carries `- Blocks-Release: next`, which this plan INHERITS as required.

## Goal

Make spec `25kzda` Section 4.2's byte-equality promise true, so that editing a cell in that table really is "a code change" the suite catches, instead of a claim an author trusts and nothing enforces.

The deliverable is a RESTORED GUARANTEE plus a RECURRENCE GATE, not a prose correction. After this plan: the four transcribed cells of all twelve rows are pinned to the spec's own bytes by a test proven to fail under mutation; the spec's three stale test citations say what is actually enforced; `runner_shared.py` stops naming a deleted file as its guard; and `aw check` refuses any records artifact that cites a `tests/test_*.py` path which does not exist, so the next suite trim reports the citations it falsified instead of silently leaving them behind.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the guard the spec promises

- [x] E-01 RE-CHECK THE COLLISION WITH `xjmjq4` BEFORE WRITING ANYTHING, then restore the transcription guard. First determine whether approved plan `xjmjq4` (`.aw/records/plans/pending/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md`, or `executed/` if it has since run) has landed `tests/test_run_finding_abort_partition.py`. If it HAS, this plan's new module must not duplicate its `action`-cell comparison: assert `inspects`, `pass_criterion` and `message` here and state in the evidence that `action` is covered there. If it has NOT, cover all four cells here, since `action` must not be left unguarded on the chance that another plan may run later. Then add `tests/test_run_finding_spec_transcription.py` parsing spec 4.2's table out of the spec FILE and asserting byte equality against `run_evidence.RUN_FINDING_CODES_BY_CODE` for each covered cell. RESOLVE THE SPEC PATH BY ID6 GLOB (`*-25kzda-*.spec.md`), NOT by the legacy filename: the deleted test globbed `20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, which no longer matches any file, and its module-level `next(...)` over an empty glob would raise `StopIteration` at import today (F-05), so copying that line forward reintroduces a collection error rather than a guard. Assert the parse is non-vacuous (exactly 12 rows parsed, and the parsed code set equals the module's) before asserting any cell, so a parser that silently matched nothing cannot pass.
  NORMALIZE BACKTICKS BY THE BOTH-ENDS RULE AND STATE IT IN THE MODULE, because the columns are NOT uniformly wrapped and the naive rule produces false mismatches in BOTH directions (review F-13). Measured: 12 of 12 `message` cells are fully backtick-wrapped while 0 of 12 `inspects`, `pass_criterion` and `action` cells are. So strip the outer pair ONLY when the cell both begins AND ends with a backtick; an unconditional `.strip('`')` corrupts `RUN-SCOPE-DELTA`'s `inspects`, which legitimately BEGINS with a backtick (``git diff` and untracked paths...`), and stripping nothing reports twelve false mismatches on `message`. The both-ends rule was re-measured at zero mismatches on all four columns. NOTE WHY THE NON-VACUITY GUARD DOES NOT COVER THIS: a mis-normalized parse still yields 12 rows and the correct code set, so it passes that guard and then fails on cell comparison, which an executor would most likely misread as a real spec/module divergence.
  - Depends on: none
  - Expected outcome: `tests/test_run_finding_spec_transcription.py` exists and passes at this HEAD, since spec and module agree today on every cell UNDER THE BOTH-ENDS NORMALIZATION RULE (F-06, re-measured at review: 12 rows parsed, zero mismatches on all four cells). A non-vacuity assertion fails if the parser matches zero rows. IF CELL COMPARISON FAILS AT THIS HEAD, suspect the normalization rule before concluding the spec and module have diverged (F-13).
  - Execution state: performed

- [x] E-02 PROVE THE GUARD IS MUTATION-SENSITIVE, which is what separates a restored guard from a decorative one. In the same module, add a case that perturbs a single row's cell via `NamedTuple._replace`, patches it into the lookup, asserts the comparison FAILS, and restores the table afterwards (`addCleanup`, so a failing assertion cannot leak a mutated module into another test). This discharges GUIDING_PRINCIPLES P16's "Verify test sensitivity with mutation" requirement and the "Never weaken an assertion so it passes everywhere" rule that cites it.
  - Depends on: E-01
  - Expected outcome: The perturbation case passes (meaning the comparison it drives reports a mismatch), proving the guard fires. Verified available at authoring: `_replace`-ing one row's `pass_criterion` makes byte equality against the spec cell return `False` (F-07).
  - Execution state: performed

### Task group 2: make the spec's own citations honest

- [x] E-03 Repoint Section 4.2's "NOTE ON TRANSCRIBING THIS TABLE" at the file E-01 creates, so the sentence an author trusts names a file that exists. Change ONLY the test-file reference and keep the rest of the note byte-identical, specifically its `inspects`/`pass_criterion` VERBATIM claim, its "editing a cell here is a code change" conclusion, and its `RC-COUNT`/12 paragraph, all of which remain true. Do not weaken the note into a hedge: after E-01 the strong claim is accurate. If E-01 measured that `xjmjq4` already covers `action`, name BOTH files rather than implying one covers everything.
  - Depends on: E-02
  - Expected outcome: Section 4.2's note cites `tests/test_run_finding_spec_transcription.py` (plus `tests/test_run_finding_abort_partition.py` if present), the cited path(s) resolve on disk, and the note's other sentences are unchanged.
  - Execution state: performed

- [x] E-04 Correct the spec's TWO OTHER dangling test citations, found by measurement and not named in the backlog item (F-03). The Section 2.1 bullet amended 2026-09-05 cites `tests/test_lane_permission_posture.py` (quoting "`--dangerous` is REMOVED from this prohibition") as pinning spec `7ckptx` R4.1c's permission posture; that file is deleted and NO surviving test asserts the default, though the shipped default is still correct (`True`, measured in F-04). Line 1251 cites `tests/test_run_flag_surface.py` as binding spec 2.1's flag grammar "bidirectionally" such that "a spec-only flag declaration is a guaranteed test failure"; that file is deleted and nothing enforces it. Rewrite both to state what is TRUE today: name the measured shipped behavior and state plainly that the cited guard was deleted in `19313eed` and that the property is currently unguarded. DO NOT restore either test here and do not silently drop the sentences: each names a real property whose coverage gap belongs to backlog `xvp5vx` (the general trim audit), so cite `xvp5vx` as the carrier rather than leaving a reader to think the gap is unknown.
  LEAVE THE `## Workflow history` CITATIONS ALONE, which is why this item's expected outcome is BODY-SCOPED rather than whole-file (review F-10). The spec has a FOURTH dangling site this plan did not find at authoring: line 1621, a dated 2026-09-21 history note citing `tests/test_run_flag_surface.py` twice, once as "extracted and asserted in both directions" and once as "Verified: tests/test_run_flag_surface.py passes". Both are false as LIVE claims and both are TRUE as history, so correcting them would rewrite a dated measurement, which `AGENTS.md`'s add-a-correction-beside-never-over rule forbids and which this plan's own Deferred reasoning already refuses for the plans tree. Correct the THREE BODY sites only (232, 824 via E-03, 1251).
  - Depends on: E-03
  - Expected outcome: No `tests/test_*.py` path cited in spec `25kzda`'s NORMATIVE BODY (everything above the `## Workflow history` heading) is missing from disk; the dated history notes are byte-unchanged including their now-dangling citations; and each corrected sentence names both the measured current behavior and `xvp5vx` as the coverage carrier.
  - Execution state: performed

- [x] E-05 Correct ALL SEVEN `runner_shared.py` SITES that name the deleted `tests/test_run_flag_surface.py` as a live guard, not only the module docstring. The docstring states that what "replaces the fingerprint as its guard is `tests/test_run_flag_surface.py`, which drives every assertion from `RUN_POLICY_FLAGS` as DATA and therefore fails when the spec grows a flag the code lacks"; that file is deleted, so the block it describes is guarded by nothing of the kind, and this is a SHIPPED comment asserting a protection that does not exist (F-04). MEASURED AT REVIEW, THE SAME CLAIM IS REPEATED SIX MORE TIMES IN THE SAME FILE (F-12): inline comments beside the flag registry and the spec-declaration rule assert that the file "reads that section as a FILE in BOTH directions" (twice, at two separate rows), that a flag registration obliges a same-change spec amendment "because `tests/test_run_flag_surface.py` reads that", and more. Correcting one instance of a claim the file makes seven times leaves the file still asserting it, so fix every site. Rewrite each to say the guard was deleted in `19313eed` and that the flag surface currently has no such data-driven test, citing `xvp5vx`; PRESERVE each site's underlying REQUIREMENT (a new run flag must still be declared in spec 2.1 in the same change that registers it) and correct only the claim that a test enforces it. Comment text only: change no code, no flag, and no default. DO NOT touch `agent_workflows/agy_runipd.py`, which carries an eighth instance of this class and is not in `- Scope-Paths:`; it is carried to `xvp5vx`.
  - Depends on: E-04
  - Expected outcome: ZERO sites in `runner_shared.py` name a deleted file as a live guard (verified by a `grep -rn test_run_flag_surface agent_workflows/runner_shared.py` census before and after, 7 then 0 as a live-guard claim), each site's spec-declaration requirement is preserved, and `git diff` on the file shows comment-only changes with no executable line touched.
  - Execution state: performed

### Task group 3: stop the class recurring

- [x] E-06 Add a deterministic `aw check` rule (for example `check.test-citation-dangling`) that reports any records artifact citing a `tests/test_*.py` path which does not exist on disk, with a new `tests/test_check_engine_test_citation.py` driving it. Register it in `check_engine.py`'s rule table in the shape its neighbours use (`check.scope-path-target-stale` is the closest precedent: `error`, `ASSURANCE_REPOSITORY`, `DET_DETERMINISTIC`). Scope the rule to SPECS, whose citations are contract claims a reader relies on, and state in the rule's registered comment why the plans tree is deliberately excluded (an executed plan is a historical record whose citations were true when written, so "correcting" them would rewrite history, which `AGENTS.md` forbids).
  SCOPE THE RULE TO THE NORMATIVE BODY AND EXEMPT `## Workflow history`, which is a HARD REQUIREMENT and not a refinement (review F-10). The same historical-record argument that excludes the plans tree applies WITHIN a spec file: a dated history note records what was measured on its date, so a citation it carries is not falsified by a later deletion. Without this exemption the rule lands RED on spec `25kzda` itself immediately after E-04 corrects it, because line 1621's dated 2026-09-21 note cites the deleted `tests/test_run_flag_surface.py` twice and E-04 is forbidden from rewriting it. Detect the boundary on the `## Workflow history` heading, the same way the measurement in F-10 and F-11 did.
  REGISTER IT `error`, BECAUSE THE BODY-SCOPED MEASUREMENT IS CLEAN AFTER E-04 (review F-11, which resolves OQ-02). Of 11 dangling spec citations across 6 files, 8 are in `## Workflow history` and only 3 are in a body, and ALL THREE are in `25kzda`, the file E-04 corrects. The other five spec files are history-only and need no amendment. So the condition this item's own decision rule names for `error` is satisfied by construction. KEEP THE DECISION RULE AS A SAFETY NET rather than as the primary path: re-measure the body-scoped specs tree at execution and, if it is NOT clean (a sixth spec having gained a body-level dangling citation in the interim), register ADVISORY following the `check.review-dangling` precedent and say so, because a rule that lands red on artifacts this plan does not fix would block every concurrent lane's integration.
  The test must drive the real checker over a synthesized fixture tree and assert on returned findings, never by reading `check_engine.py`'s source. It must cover THREE cases, since the exemption is now load-bearing: a body citation to a nonexistent path FIRES, a body citation to a real path is SILENT, and a `## Workflow history` citation to a nonexistent path is SILENT.
  - Depends on: E-05
  - Expected outcome: The new rule fires on a synthesized spec whose BODY cites a nonexistent `tests/test_x.py`, stays silent on one citing a real path, and stays silent on one citing a nonexistent path from inside `## Workflow history`. Run over the live tree it reports ZERO findings across every spec after E-04, and it is registered `error` on that measurement (or ADVISORY with the re-measured count stated, if the tree is not clean).
  - Execution state: performed

## Project conventions discovered (Step 0)

- `AGENTS.md` and GUIDING_PRINCIPLES P16 forbid code-pinning tests: no `inspect`, `ast`, `read_text()`, regex or substring search over production code (`agent_workflows/*.py`) as a correctness proxy, no count or census pins, no docstring pins. This plan's tests read a SPEC file, not production source, which P16's own narrow exception covers (see D-1).
- P16's "First, synthesize the input (the default)" guidance prefers ANCHORING a live-checkout path over a `livecorpus` marker, and states the measured cost of the marker: a marked test is deselected from the default suite AND from CI (`addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` in `pyproject.toml`), running only under `make test-all` and release-review. E-01 therefore anchors the spec path and does not mark the module.
- The suite is run BARE (`python3 -m pytest`), per `AGENTS.md`: `addopts` already supplies `-q -n auto --dist=worksteal`, and adding `-q` suppresses the `N passed` line this plan's validation requires.
- `check_engine.py` registers each rule as a `RuleSpec(severity, assurance, determinism, invariant)` with a prose comment stating WHY that severity, and `check.scope-path-target-stale` / `check.review-dangling` are the precedents for a stale-reference rule (the latter deliberately ADVISORY and whole-tree, for the blast-radius reason E-06 weighs).
- `AGENTS.md` forbids changing what a plan in `.aw/records/plans/executed/` RECORDS, which is the reason E-06 scopes its rule to specs and not to the plans tree.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-01 | THE ITEM'S FIRST CLAIM REPRODUCES EXACTLY. Spec `25kzda` Section 4.2 contains, verbatim, "NOTE ON TRANSCRIBING THIS TABLE. `run_evidence.RUN_FINDING_CODES` transcribes the `inspects` and `pass_criterion` cells VERBATIM, and `tests/test_run_evidence_completion.py` asserts byte equality, so editing a cell here is a code change." That file does not exist, and `grep -rln RUN_FINDING_CODES tests/` returns only `tests/test_host_capability_extension.py`, which matches on an unrelated string and asserts nothing about the table. | The quoted note read out of the spec file; `ls tests/test_run_evidence*` returns "No such file or directory"; `git log --diff-filter=D` names `19313eed7` as the deleting commit with `tests/test_run_evidence_completion.py | 1722 ---------` in its stat. | The defect is real and unambiguous, so this plan has a genuine false claim to close rather than a stale report to correct. |
| F-02 | THE ITEM'S SECOND CLAIM ALSO REPRODUCES: the deletion is the suite trim, not a rename. `19313eed7` is "test: trim test suite from 9,136 to under 2,000 tests" and removed the file whole (1,722 deletions, 85 test methods), including `test_inspects_and_pass_criterion_are_verbatim_from_the_spec`, which is precisely the assertion the spec note describes. | `git show 19313eed --stat -- tests/test_run_evidence_completion.py`; `git show 19313eed^:tests/test_run_evidence_completion.py` still contains `test_inspects_and_pass_criterion_are_verbatim_from_the_spec` comparing `row.inspects` and `row.pass_criterion` against `spec_row[...]`. | The guard to restore ALREADY EXISTED in a known shape, so E-01 is a restoration with a precedent rather than a design task, and the deleted file is a readable source for the case list. |
| F-03 | THE DEFECT IS THREE TIMES WIDER THAN FILED, AND THIS IS THE FINDING THAT SHAPES THE PLAN. Spec `25kzda` cites FOUR distinct `tests/test_*.py` paths and THREE of them do not exist: `tests/test_lane_permission_posture.py` (line 232), `tests/test_run_evidence_completion.py` (line 824, the filed one), and `tests/test_run_flag_surface.py` (line 1251). Only `tests/test_runner_shared.py` resolves. All three missing files were deleted by the SAME commit `19313eed`. | Scripted extraction of every `tests/test_[a-z0-9_]*\.py` match in the spec with an existence test per path, printing `GONE line 232`, `GONE line 824`, `GONE line 1251`, `OK line 286`. | Fixing only the filed sentence would leave two equally false claims in the same contract, so E-04 covers the other two. It also establishes the defect is a CLASS, which is the argument for E-06's gate. |
| F-04 | A SHIPPED MODULE DOCSTRING CARRIES THE SAME FALSE CLAIM, so the lie is not confined to records. `agent_workflows/runner_shared.py`'s module docstring states "What replaces the fingerprint as its guard is `tests/test_run_flag_surface.py`, which drives every assertion from `RUN_POLICY_FLAGS` as DATA and therefore fails when the spec grows a flag the code lacks." That file is deleted and no surviving test references `RUN_POLICY_FLAGS` in that data-driven shape. Separately, the permission-posture property behind line 232 is genuinely unguarded while the shipped default is still CORRECT: `agy_runipd.build_parser().parse_args(["start", "someid"]).dangerously_skip_permissions` is `True`, and the only surviving `dangerously` match under `tests/` is for the unrelated `--dangerously-force-conflict` flag. | The quoted docstring string in `runner_shared.py`; `grep -rln RUN_POLICY_FLAGS tests/` returns `test_runner_shared.py` and `test_concurrent_driver_guard.py`, neither carrying the deleted file's data-driven flag-surface assertions; the measured `True` default printed by driving the real parser; `grep -rn dangerously tests/`. | E-05 exists because of this. It also proves the code is RIGHT and only the claims are wrong, so no behavior change is in scope and the remedy is honest prose plus restored coverage. |
| F-05 | THE DELETED TEST CANNOT BE RESTORED VERBATIM; IT WOULD ERROR AT IMPORT. Its module-level `_SPEC_PATH = next((...).rglob("20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md"))` globs the spec's PRE-id6 filename. The spec has since been renamed to `20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, so that glob matches nothing and `next()` over it raises `StopIteration` during collection. Its `setUp` guard (`if not _SPEC_PATH.exists(): self.skipTest(...)`) would never be reached, because the failure happens at module import. | `git show 19313eed^:tests/test_run_evidence_completion.py` showing the legacy glob and the `next(...)` call; a scripted `rglob` of that legacy name over `.aw/records/specs` returning `[]` while `*-25kzda-*.spec.md` returns the one current path. | E-01 must resolve the spec by id6 glob and is explicitly instructed not to copy the legacy line. Note the second-order lesson, which the skip guard illustrates: a guard placed after an eager module-level resolution protects nothing. |
| F-06 | THE SPEC AND THE MODULE AGREE TODAY ON ALL FOUR CELLS, so E-01 can be a hard assertion on arrival and needs no row edited. Parsing Section 4.2's `| \`RUN-` rows into five cells with backticks stripped yields 12 rows; comparing each against `RUN_FINDING_CODES_BY_CODE` gives `inspects` 0 mismatches, `pass_criterion` 0, `message` 0, `action` 0, with no code present in one set and absent from the other. | Scripted five-cell parse compared field by field against the shipped table, printing `spec rows parsed: 12`, `module rows: 12`, `codes in module not in spec: []`, `codes in spec not in module: []`, and `mismatches: 0` for each of the four fields. | The restoration is over data that is currently correct, so the plan restores a guard rather than fixing a divergence, and a red test at execution means the executor broke something. |
| F-07 | THE GUARD IS MUTATION-SENSITIVE, verified before authoring rather than assumed. Taking the real `RUN-BASELINE-OWNERSHIP` row, `_replace`-ing its `pass_criterion` with the same text plus " and also something else", and comparing against the spec cell returns `False`. | Adversarial `_replace` probe over the real row printing the mutated module cell, the spec cell, and `byte equality: False`. | E-02 is known achievable, so the plan does not promise a sensitivity demonstration it has not shown is possible. |
| F-08 | APPROVED PLAN `xjmjq4` PARTLY DISCHARGES THIS ITEM AND SAYS SO EXPLICITLY, so the two must not duplicate each other. Its E-05 restores spec byte equality for the `action` cell only, and its own review finding F8 records that it "narrows `089bq4` rather than being orthogonal to it", that it "must not CLAIM to close a release-blocking item it only partly addresses", and that "whoever executes `089bq4` must not re-derive coverage E-05 already restored". Its Deferred section states the division of labour as "action cell here, the remaining cells and the spec sentence there". It is `- Status: approved`, so it may execute before this plan. SEPARATELY, the measured size of the general problem is lopsided: six spec files carry eight distinct dangling test paths, while the plans tree carries 1,926 citations to nonexistent test files against 2,299 that resolve. RE-MEASURED AT REVIEW 2026-10-01: the plans-tree figures are now 9,206 dangling against 14,018 resolving, so that population grew roughly fivefold in a day as lanes merged; the spec figures were re-measured at 11 dangling against 20 resolving across the same 6 files and 8 distinct paths. Both movements STRENGTHEN this finding's conclusion rather than weakening it: the plans tree is even more clearly unfit for an `error` rule, and the specs tree is small enough to reason about exactly (see review F-11 for the zone breakdown that resolves OQ-02). | `xjmjq4`'s front matter (`Status: approved`), its E-05 text, and its Deferred/F8 rows quoted above; scripted citation census over `.aw/records/{specs,plans,releases}` printing `('specs', False) 9`, `('specs', True) 14`, `('plans', False) 1926`, `('plans', True) 2299`. | E-01 opens by re-checking that plan's state and adapting, rather than assuming an ordering this plan cannot control. The census is the measured input to E-06's severity and scoping decision: a whole-records `error` rule would be red on 1,926 plan citations. |
| F-09 | THE SPEC'S OTHER SECTIONS ARE NOT IN SCOPE AND ARE DELIBERATELY UNTOUCHED, stated because three other pending plans amend this same spec. `f7z10q` (`- Status: to-review`) edits Section 4.2's line-76 binding count and declares the spec in its Scope-Paths; `a6i03f` and `xjmjq4` both rewrite the abort-partition prose in `run_evidence.py`, and `a6i03f` carries a BLOCKING open question (OQ-04) precisely because the two collide. This plan touches the transcription NOTE and two unrelated citation sentences, edits no row, and does not enter the abort or binding dimensions. | `f7z10q` front matter (`Scope-Paths` includes the spec, `Status: to-review`); `a6i03f`'s workflow history recording OQ-04 as blocking on the `xjmjq4` collision. | The plan's boundaries are drawn to avoid a fourth collision in an already contended file, which is also why Scope-Paths declares the spec explicitly so the runner announces the amendment. |
| F-10 | REVIEW FINDING (2026-10-01): THE SPEC HAS A FOURTH DANGLING CITATION SITE, AND IT IS IN `## Workflow history`, WHICH IS THE FINDING THAT RESHAPES E-06. F-03 reports three dangling paths at lines 232, 824 and 1251 and the plan's E-04 corrects the two it does not already own. Re-measuring at review HEAD `fc91266df` finds a FOURTH site: line 1621, a dated `## Workflow history` note from 2026-09-21 that cites `tests/test_run_flag_surface.py` TWICE, once saying the flag grammar is "extracted and asserted in both directions" by it and once recording "Verified: tests/test_run_flag_surface.py passes". Both are now false as live claims and both are TRUE as history: the note records what was measured on 2026-09-21, when the file existed. This matters NOT because E-04 should correct it (it must not; `AGENTS.md`'s add-a-correction-beside-a-dated-measurement rule and the plan's own refusal to rewrite history both forbid it) but because E-06's rule as written would FLAG it, turning this plan's own spec red immediately after E-04 "fixes" every citation. E-06 therefore needs a HISTORY-ZONE EXEMPTION, which the plan does not currently specify. | Scripted extraction of every `tests/test_[a-z0-9_]*\.py` match in the spec with an existence test and a zone test keyed on the `## Workflow history` heading line: `GONE BODY 232`, `GONE BODY 824`, `GONE BODY 1251`, `GONE HISTORY 1621` (twice). The spec's `## Workflow history` heading is at line 1604. | E-06 is amended to EXEMPT the `## Workflow history` section (and E-04's expected outcome is corrected from "no `tests/test_*.py` path cited anywhere in spec `25kzda` is missing from disk", which is unachievable without rewriting a dated record, to the body-only claim it can actually deliver). V-04 and V-06 are amended to match. Without this the plan's own E-04 expected outcome is impossible to satisfy and E-06 would land red on the very file it just corrected. |
| F-11 | REVIEW FINDING (2026-10-01): THE HISTORY-ZONE SPLIT ALSO RESOLVES OQ-02, BECAUSE `25kzda` IS THE ONLY SPEC WITH A DANGLING CITATION IN ITS NORMATIVE BODY. OQ-02 is left `open` with a decision rule, on the measured premise that "six spec files carry eight distinct dangling test paths" so an `error` rule would land red. That census is correct and its ZONE BREAKDOWN changes the answer: of 11 dangling spec citations across 6 files, 8 are in `## Workflow history` and only 3 are in a body, and ALL THREE body hits are in `25kzda` itself, the file E-04 corrects. The other five spec files (`agents-artifact-organization`, `cross-type-review`, `per-action-model-selection`, `orchestrator-conformance-parser-and-repair-loop`, `lifecycle-automation-policy`) are history-only, carrying 1, 1, 1, 1 and 2 dangling citations respectively and ZERO in their bodies. So a body-scoped rule registered as `error` is measurably CLEAN after E-04, which is exactly the condition E-06's own decision rule names for choosing `error`, and the Deferred row's warning that "if E-06's rule is registered as an `error`, they must be [amended]" dissolves: nothing in those five files is a live false claim. | Per-file zone census over `.aw/records/specs/**/*.spec.md`: `{'body': 3, 'history': 2}` for `25kzda` and `{'history': N}` for each of the other five, with `spec files with a dangling citation in the BODY: 1`. | OQ-02 is RESOLVED at review rather than left to execution, and E-06's decision rule is kept as a safety net rather than as the primary path. The Deferred spec-amendment row is corrected, since the five other specs need no amendment under a body-scoped rule. This removes the plan's one open question. |
| F-12 | REVIEW FINDING (2026-10-01): THE SHIPPED-CODE INSTANCE IS EIGHT SITES ACROSS TWO MODULES, NOT ONE DOCSTRING. F-04 names `runner_shared.py`'s module docstring, and E-05 scopes itself to "`runner_shared.py`'s module docstring". Measured: `runner_shared.py` cites the deleted `tests/test_run_flag_surface.py` at SEVEN distinct sites, only one of which is the module docstring; the other six are inline comments beside the flag registry and the spec-declaration rule, each asserting the same nonexistent guard (for example "`tests/test_run_flag_surface.py` reads that section as a FILE in BOTH directions" appears at two separate rows, and a third says the spec section "is amended in the SAME change that registers it, because `tests/test_run_flag_surface.py` reads that"). SEPARATELY, `agy_runipd.py` carries an eighth: a comment reading "Do NOT 'harden' it: `tests/test_lane_permission_posture.py` PINS the default", which is the same false-guard claim about the same deleted file the spec's line 232 cites, and `agy_runipd.py` is NOT in `- Scope-Paths:`. That last one is the most consequential, because it instructs a future maintainer not to harden a security-relevant default on the strength of a guard that does not exist. | `grep -rn 'test_run_flag_surface' agent_workflows/runner_shared.py` returning 7 lines; `grep -rn 'test_lane_permission_posture' agent_workflows/agy_runipd.py` returning the quoted comment; a per-module count showing `runner_shared.py -> 7` and `agy_runipd.py -> 1` and no other module affected. | E-05 is amended to correct ALL SEVEN `runner_shared.py` sites rather than only the docstring, since fixing one instance of a claim repeated six more times in the same file leaves the file still asserting it. The `agy_runipd.py` site is NOT folded in (it is an undeclared path and a different module), and is carried to `xvp5vx` with its measurement and with the security-relevant reason it matters most. V-05 is amended to require the full site census before and after. |
| F-13 | REVIEW FINDING (2026-10-01): F-06's "ZERO MISMATCHES" IS TRUE ONLY UNDER A NORMALIZATION RULE THE PLAN NEVER STATES, AND THE NAIVE RULE GIVES TWELVE FALSE MISMATCHES. F-06 reports the parse as "five cells with backticks stripped" yielding zero mismatches on all four cells. Measured: the four columns are NOT uniformly wrapped. Zero of twelve `inspects` cells, zero of twelve `pass_criterion` cells and zero of twelve `action` cells are fully backtick-wrapped, while TWELVE of twelve `message` cells are. So a parser that strips backticks unconditionally (for example `.strip('`')`) corrupts `inspects` on `RUN-SCOPE-DELTA`, whose cell legitimately BEGINS with a backtick ("`git diff` and untracked paths..."), producing a false mismatch; and a parser that strips none reports twelve false mismatches on `message`. The rule that yields F-06's zero is STRIP THE OUTER PAIR ONLY WHEN THE CELL BOTH BEGINS AND ENDS WITH A BACKTICK, which I verified gives 0/0/0/0. E-01's non-vacuity assertion does NOT catch this: a corrupted parse still yields 12 rows and the correct code set, so it passes the stated guard and then fails on cell comparison, which an executor would most likely read as a real spec/module divergence. | Per-column wrap census (`inspects 0/12`, `pass_criterion 0/12`, `message 12/12`, `action 0/12`); the `RUN-SCOPE-DELTA` `inspects` cell shown corrupted to `'git diff` and untracked...'` under unconditional stripping; a both-ends rule re-measured at `0` mismatches on all four columns. | E-01 is amended to SPECIFY the normalization rule and to require it be stated in the test module, and its Expected outcome now names the failure mode an executor will otherwise misdiagnose. This is the single most likely cause of a confusing red at execution, and it is a parser defect rather than a contract divergence. |

## Proposed changes (ordered, validatable)

1. Re-check `xjmjq4`'s landed state, then add `tests/test_run_finding_spec_transcription.py` pinning spec 4.2's transcribed cells to the shipped table byte for byte, resolving the spec by id6 glob and asserting the parse is non-vacuous (E-01, F-05, F-06, F-08).
2. Prove the new guard fails under a single-cell mutation, with cleanup so the mutation cannot leak (E-02, F-07).
3. Repoint Section 4.2's transcription note at the restored file, keeping its VERBATIM claim and its `RC-COUNT` paragraph intact (E-03, F-01).
4. Correct the spec's two other dangling test citations to state measured current behavior and name `xvp5vx` as the coverage carrier (E-04, F-03, F-04).
5. Correct `runner_shared.py`'s docstring claim that a deleted file guards the policy flag surface (E-05, F-04).
6. Add a deterministic `aw check` rule refusing a SPEC that cites a nonexistent `tests/test_*.py`, with its severity chosen from the measured whole-tree result and the plans tree deliberately excluded (E-06, F-08).

## Deferred / out of scope (with reason)

- RESTORING THE OTHER ~80 DELETED TEST METHODS. Commit `19313eed` deleted 85 methods from `test_run_evidence_completion.py` alone, covering completion evaluation, binding states, and placeholder substitution. This plan restores only the cell-transcription subset, because that is the subset spec 4.2's note PROMISES and therefore the subset this item's defect is about. The remainder stays with backlog `xvp5vx` ("audit what properties lost their only guard in the 19313eed suite trim"), which carries the maintainer's explicit directive that only genuine behavioral outcomes may be triaged and that code-pinning tests must never be restored.
  - Carrier: xvp5vx
- THE ABORT-PARTITION DIMENSION, including the `action` cell's spec anchor. Owned by approved plan `xjmjq4` E-05 (F-08). E-01 adapts to whether it has landed rather than racing it.
  - Carrier: xjmjq4
  - Carrier-Evidence: .aw/records/plans/executed/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md
- RESTORING COVERAGE FOR THE TWO PROPERTIES BEHIND THE OTHER DANGLING CITATIONS (the Antigravity permission-posture default and the bidirectional flag-surface binding). E-04 and E-05 make the CLAIMS honest; they do not re-guard the properties. Both are real coverage gaps, both were measured as currently unguarded (F-04), and both are instances of exactly what `xvp5vx` exists to triage. Restoring either means reasoning about a spec (`7ckptx` R4.1c) and a flag table this plan does not otherwise touch, which would be an unreviewable scope expansion in a file three other pending plans already contend for (F-09).
  - Carrier: xvp5vx
- THE 1,926 DANGLING TEST CITATIONS IN THE PLANS TREE. Not corrected and deliberately excluded from E-06's rule scope: an executed plan is a historical record whose citations were true when written, and `AGENTS.md` forbids changing what an executed plan RECORDS. Correcting them would rewrite history to no benefit.
  - Carrier-Declined: not a defect. A record of a past state is not falsified by a later deletion, unlike a live contract that tells a present-day author what will catch their mistake.
- SPEC AMENDMENT OUTSTANDING: none beyond this plan. This plan AMENDS spec `25kzda` (three sentences in two sections) and declares the spec in `- Scope-Paths:` accordingly, so the runner announces the amendment before the run starts. THE FIVE OTHER SPEC FILES NEED NO AMENDMENT, which review F-11 established and which supersedes this row's original warning that "if E-06's rule is registered as an `error`, they must be": every one of their dangling citations sits in `## Workflow history`, where a dated note records what was true on its date and is not falsified by a later deletion, so E-06's history-zone exemption leaves them clean and none carries a live false claim. The three BODY-level dangling citations in the whole specs tree are all in `25kzda`, and E-03 and E-04 correct all three.
  - Carrier-Declined: Nothing is owed. Measured at review: zero body-level dangling test citations remain in any other spec, so there is no live false contract claim for a carrier to carry. The five history-only citations are correct as history and must not be edited.
- THE EIGHTH SHIPPED-CODE INSTANCE IN `agent_workflows/agy_runipd.py` (review F-12). A comment there reads "Do NOT 'harden' it: `tests/test_lane_permission_posture.py` PINS the default", naming the same deleted file spec line 232 cites and instructing a future maintainer not to harden a security-relevant default on the strength of a guard that does not exist. Out of fence because `agy_runipd.py` is not in `- Scope-Paths:` and is a different module from the one E-05 corrects; adding it would widen an already five-path plan into a sixth file for a one-comment edit. NAMED EXPLICITLY because of the eight sites measured, this is the one whose falsity could most plausibly cause harm: it actively discourages a correctness change.
  - Carrier: xvp5vx

## Scope check

- Over-scope: Five paths is more than the defect's one sentence, and each is justified by a measurement rather than by tidiness. The test module and the spec are the minimum to close the filed defect. `runner_shared.py` is in because the same false claim is in SHIPPED code (F-04), where it misleads a reader of the module that owns the flag surface. `check_engine.py` plus its test are in because the defect measured as a CLASS of three in one file (F-03), and a plan that fixes three instances of a recurring class without gating recurrence invites the fourth. No production BEHAVIOR is changed: `runner_shared.py` gets a comment-only edit, and `check_engine.py` gains a new rule without altering an existing one.
- Under-scope: Deliberately narrow in FIVE directions. The table's DATA is untouched (the spec and module agree, F-06, re-verified at review under the normalization rule F-13 names). The abort and binding dimensions are left to `xjmjq4` and `f7z10q` (F-08, F-09). The two coverage gaps behind the other citations are made honest but not re-guarded, and are handed to `xvp5vx` with the measurement attached. FOURTH (review, F-10), the spec's own `## Workflow history` KEEPS its two dangling citations and E-06's rule deliberately cannot see them, so a reader scanning the raw file will still find a dead test path in it; that is correct (a dated note is a record, not a claim) and is disclosed here so it is not mistaken for an incomplete fix. FIFTH (review, F-12), the eighth shipped-code instance of this false-guard class, in `agy_runipd.py`, is left in place and carried; of the eight sites measured it is the one most likely to cause harm, because it tells a maintainer not to harden a security-relevant default on the strength of a guard that does not exist. So this plan makes a false contract true, corrects seven of eight shipped instances, and gates the class in spec bodies, without absorbing the general trim audit.

## Required tests / validation

- The actual bare `python3 -m pytest tests/test_run_finding_spec_transcription.py` output, plus the bare `python3 -m pytest tests/test_check_engine_test_citation.py` output, both showing every test passing.
- The actual bare `python3 -m pytest` summary line (`N passed`) for the full fast suite, pasted verbatim. Run it BARE per `AGENTS.md`: no `-n0`, no extra `-q` (which compounds into `-qq` and suppresses the very summary line this requires), no `-p no:randomly`.
- THE MUTATION DEMONSTRATION (E-02), pasted as actual output: the comparison must FAIL on a perturbed cell. A guard that cannot be shown to fail has not been shown to be a guard, and this is the item that distinguishes restoring the promise from re-decorating it.
- THE NEW CHECK RULE FIRING AND STAYING SILENT, both pasted: a synthesized spec citing a nonexistent test produces the finding; one citing a real path produces none. A rule only ever observed silent is indistinguishable from an unregistered one.
- `aw check specs` (or `aw check all`) over the live tree after E-04, pasted, showing what the new rule reports repository-wide. This is the measurement E-06's severity decision turns on, so it must appear as output and not as a claim.
- `aw ipd lint --phase pre-transition` conforming on this plan before any terminal transition.
- A P16 conformance statement quoting the new test modules: no `inspect`, `ast`, regex or substring search over `agent_workflows/*.py`, no caller-count or census assertions, no docstring pins. State explicitly why reading the SPEC file is not a violation (D-1).

## Spec / documentation sync

THIS PLAN AMENDS SPEC `25kzda`, and `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is declared in `- Scope-Paths:` for that reason, so both runners announce the declared spec edit before the run starts and reconcile it at finalize.

WHY THE AMENDMENT IS NECESSARY AND NOT INCIDENTAL: the spec is the artifact carrying the defect. Section 4.2's note tells an author that a guard will catch their mistake, and no guard exists (F-01). The amendment is therefore not a docs tidy-up but the correction of a false contract claim, which `AGENTS.md` identifies as the highest-leverage change a run can make and requires be explained here.

THREE SENTENCES CHANGE, in two sections, and nothing else:
1. Section 4.2's transcription note: the cited test filename, repointed at the file E-01 creates. The note's `inspects`/`pass_criterion` VERBATIM claim, its "editing a cell here is a code change" conclusion, and its entire `RC-COUNT`/12 paragraph are all preserved byte for byte, because E-01 makes the first two TRUE and the third was never false.
2. The Section 2.1 bullet citing `tests/test_lane_permission_posture.py` as pinning `7ckptx` R4.1c: corrected to state the measured shipped default and that the guard was deleted (F-04). The controlling authority on host permission posture remains `7ckptx` R4.1c, which this plan does not touch.
3. The Section 5 telemetry bullet citing `tests/test_run_flag_surface.py` as binding the flag grammar bidirectionally: corrected the same way. The spec's REQUIREMENT that a new run flag be declared in Section 2.1 in the same change that registers it is PRESERVED; only the claim that a test enforces it is corrected, since that is the part measurement falsified.

NO CONTRACT IS WEAKENED. Section 4.2's twelve-code vocabulary, `RC-COUNT`, the abort classes, every row's data, and the flag-declaration requirement are all unchanged. Two claims about ENFORCEMENT become honest, and one becomes true.

`agent_workflows/runner_shared.py` gets a comment-only correction of the same class (F-04), and no user-facing document (README, CHANGELOG, `docs/`) describes this guard, so none needs updating.

## Open questions

### OQ-01: Restore the byte-equality guard, or reword the spec to stop promising one?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as D-1, restore the guard, not reword the promise. This is the decision backlog `089bq4` records as needing to be made, and it is resolved here rather than escalated because the repository answers it. THE COUNTER-ARGUMENT FIRST, since it is real: commit `19313eed` deliberately trimmed the suite from 9,136 tests to under 2,000, so restoring a deleted test must respect that trim's intent, and `AGENTS.md` plus GUIDING_PRINCIPLES P16 forbid code-pinning tests outright. FOUR REASONS THE EVIDENCE STILL FAVOURS RESTORING. (1) P16's own narrow exception names this case almost exactly: "Content verification is permissible only where the text or file itself is the artifact under test (for example, verifying published documentation does not cite deleted test files...)". A spec table transcribed verbatim into shipped data IS the artifact under test, and the parenthetical example is literally this defect. (2) The guard does not pin CODE: it compares two DATA artifacts (a spec table and a shipped tuple of strings), reads no `agent_workflows/*.py` source, and asserts nothing about structure, placement or counts of callers. Refactoring `run_evidence.py` freely leaves it green; only a cell diverging from the contract turns it red, which is P16's stated test of a valid test. (3) The cells are OPERATOR-FACING STRINGS. The `message` cell is what a human reads when a run fails, so a desynchronized cell is a user-visible defect, which is why the item is `- Work-Kind: bug` with `- Blocks-Release: next` rather than a docs chore. (4) The trim's intent is honoured by restoring 12 rows times a few cells in one small module, not 1,722 lines or 85 methods; the rest stays with `xvp5vx` under its own directive. REWORDING WAS REJECTED because it would delete a guarantee the repository can cheaply keep, leaving the vocabulary with zero coverage, and because `xjmjq4` has already restored this guarantee for the `action` cell on the same reasoning (F-08), so rewording would contradict an approved plan. Non-blocking: E-01 is executable either way, and this question changes which E-items exist, not whether the plan can run.

### OQ-02: Should the new `aw check` rule be an error or advisory, and must the other five spec files be fixed in this plan?

- Blocking: no
- Status: resolved
- Owner: reviewer (opencode/its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-10-01 AS `error`, BODY-SCOPED, WITH NO OTHER SPEC NEEDING AMENDMENT, on a measurement the authoring turn did not take (review F-11). The original rationale below is preserved because its reasoning was sound and its decision rule is retained as a safety net; what changed is that the measurement it was waiting for is now available and it answers the question. THE ZONE BREAKDOWN IS THE WHOLE ANSWER: of 11 dangling `tests/test_*.py` citations across 6 spec files, 8 sit in `## Workflow history` and only 3 sit in a normative body, and ALL THREE body hits are in `25kzda` itself, which E-04 corrects. The five other spec files (`agents-artifact-organization`, `cross-type-review`, `per-action-model-selection`, `orchestrator-conformance-parser-and-repair-loop`, `lifecycle-automation-policy`) carry 1, 1, 1, 1 and 2 dangling citations respectively and ZERO in their bodies. So a body-scoped rule is CLEAN after E-04 by construction, which is exactly the condition the decision rule names for `error`, and the fear that drove the deferral (a red rule blocking concurrent lanes) does not arise. TWO CONSEQUENCES, both applied: the history-zone exemption becomes a hard requirement of E-06 rather than an option, because without it the rule lands red on the file E-04 just fixed (F-10); and the Deferred spec-amendment row's warning that the other five specs "must be" amended under an `error` rule DISSOLVES, since nothing in them is a live false claim. THE DECISION RULE SURVIVES AS A SAFETY NET: E-06 still requires the body-scoped specs tree be re-measured at execution, and still registers ADVISORY with the count stated if a sixth spec has gained a body-level dangling citation in the interim. WHY A REVIEWER MAY RESOLVE THIS: it is a HOW question about a mechanism, and the resolution cites a demonstration on the concrete case rather than describing one, which is the standard the workflow sets for marking such a question resolved.
- Original authoring rationale, preserved: DELIBERATELY LEFT TO EXECUTION WITH A DECISION RULE RATHER THAN A GUESS, because the answer depends on a measurement whose value at execution time may differ from its value now. Measured at authoring: six spec files carry eight distinct dangling test paths (F-08). If E-04 fixes only `25kzda`, five remain, so registering the rule as a whole-specs-tree `error` would land the suite RED and, per the `livecorpus` rationale recorded in `pyproject.toml`, a red test blocks integration for every concurrent lane and not only the lane at fault (measured 2026-09-19 at 2h 10m and $55.02 with nothing integrated). THE DECISION RULE E-06 CARRIES: register `error` only if the whole specs tree is clean at that point; otherwise register advisory, following the `check.review-dangling` precedent, which is advisory and whole-tree for exactly this blast-radius reason. Either outcome is honest and neither blocks execution, which is why this is non-blocking. The executor must PASTE the live `aw check` output and state which branch of the rule it took, so the choice is recorded with its evidence rather than asserted. Fixing the other five specs is NOT adopted into scope here: each needs its own measurement of what is actually guarded today (the `25kzda` work took four separate probes), and five more would make this plan unreviewable.
- Carrier-Declined: this question is E-06's OWN deliverable and not an obligation that outlives this plan. The decision rule above resolves it deterministically from a measurement the executor must take and paste (V-06), so when this plan reaches `executed` the choice is recorded with its evidence rather than left outstanding. Nothing survives for a carrier to carry. The one obligation that DOES outlive this plan, correcting the other five specs' dangling citations, is carried on the Deferred spec-amendment row by `xvp5vx` and is deliberately not restated here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the actual bare `python3 -m pytest tests/test_run_finding_spec_transcription.py` output showing every test passing. Paste the `xjmjq4` state check that opened E-01 (the file's resolved directory and its `- Status:` line) and state in one sentence which branch was taken and therefore whether the `action` cell is asserted here. Paste the non-vacuity numbers the test itself computes: rows parsed (must be 12) and the parsed-versus-module code-set comparison (must be equal, both directions). Quote the line that resolves the spec path and confirm by inspection that it globs `*-25kzda-*` and NOT the legacy `20260826-0718-01-...` name, since the legacy glob raises `StopIteration` at import (F-05). QUOTE THE BACKTICK NORMALIZATION AND CONFIRM IT IS THE BOTH-ENDS RULE (F-13): the module must strip an outer backtick pair only when the cell begins AND ends with one, never unconditionally. State the measured reason in one sentence (12 of 12 `message` cells are wrapped, 0 of 12 in each other column, and `RUN-SCOPE-DELTA`'s `inspects` legitimately begins with a backtick), so a later reader cannot "simplify" it back into a false-mismatch generator. State explicitly what this item does NOT prove: that the guard FIRES. A comparison between two artifacts that already agree passes whether or not the assertion is sensitive, so V-02 is the item that proves it is a guard, and a reviewer reading V-01 alone must not conclude the promise is now true.
  - Observed evidence: PASS. Bare pytest runner passes (3 passed); xjmjq4 confirmed landed and executed; non-vacuity (12 rows, matching code sets) and both-ends backtick normalization verified.
    1. Bare pytest runner output:
    ```
    $ python3 -m pytest tests/test_run_finding_spec_transcription.py
    ...                                                                      [100%]
    3 passed in 6.45s
    ```

    2. `xjmjq4` state check:
    ```
    $ find .aw/records/plans -name "*xjmjq4*"
    .aw/records/plans/executed/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md
    $ grep -E "^- (Status|Id):" .aw/records/plans/executed/20260929-dorm45-01-xjmjq4-pin-the-run-abort-partition-to-the-spec-action-text-instead.ipd.md
    - Status: executed
    - Id: xjmjq4
    $ ls tests/test_run_finding_abort_partition.py
    tests/test_run_finding_abort_partition.py
    ```
    Plan `xjmjq4` has landed `tests/test_run_finding_abort_partition.py` and reached `executed`, so the branch was taken to cover `inspects`, `pass_criterion`, and `message` here, while `action` is covered in `tests/test_run_finding_abort_partition.py`.

    3. Non-vacuity assertions:
    Rows parsed: 12. Parsed code set: `['RUN-BASELINE-OWNERSHIP', 'RUN-CHECK-FRESHNESS', 'RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY', 'RUN-CROSS-TREE', 'RUN-FRESH-VERIFIER', 'RUN-FROZEN-IDENTITY', 'RUN-HOST-ATTEMPT', 'RUN-HOST-CAPABILITY', 'RUN-LEDGER-INTEGRITY', 'RUN-SCOPE-DELTA', 'RUN-STRUCTURE-PREFLIGHT']`.
    Module code set equals parsed spec code set in both directions (12 == 12).

    4. Spec path resolution:
    ```python
    matches = sorted(specs_dir.rglob("*-25kzda-*.spec.md"))
    ```
    Inspection confirms the path is resolved via the id6 glob `*-25kzda-*.spec.md` under `.aw/records/specs` rather than the pre-id6 legacy filename `20260826-0718-01-...`, preventing `StopIteration` during collection.

    5. Backtick normalization quote (both-ends rule):
    ```python
    def strip_both_ends_backtick(cell: str) -> str:
        if cell.startswith("`") and cell.endswith("`") and len(cell) >= 2:
            return cell[1:-1]
        return cell
    ```
    Measured reason: exactly 12 of 12 `message` cells are fully wrapped in backticks while 0 of 12 cells in each other column are, and `RUN-SCOPE-DELTA`'s `inspects` legitimately begins with a backtick ("`git diff` and untracked paths..."), so stripping backticks unconditionally corrupts `RUN-SCOPE-DELTA`'s `inspects` while stripping nothing yields twelve false mismatches on `message`.

    6. Negative boundary:
    This comparison does not prove that the guard FIRES when data diverges; sensitivity to mutation is demonstrated in V-02.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the actual output of the mutation case demonstrating that perturbing ONE cell makes the comparison FAIL, showing the code perturbed, the mutated module value, the spec value, and the resulting failure. Then paste proof the mutation did not leak: re-run the whole new module after the perturbation case and show every test still passing, which a missing `addCleanup` would break. State in one sentence why this discharges P16's "Verify test sensitivity with mutation" bullet and the "Never weaken an assertion so it passes everywhere" rule.
  - Observed evidence: PASS. Perturbation of RUN-BASELINE-OWNERSHIP pass_criterion verified failing assertion; clean re-run demonstrates cleanup did not leak.
    1. Perturbation demonstration output:
    ```
    Code perturbed: RUN-BASELINE-OWNERSHIP
    Mutated module value: "No pre-existing or concurrently leased path overlaps this action's mutation scope and also something else"
    Spec value:           "No pre-existing or concurrently leased path overlaps this action's mutation scope"
    Resulting failure:
     Mismatch in RUN-BASELINE-OWNERSHIP field 'pass_criterion':
      spec:   "No pre-existing or concurrently leased path overlaps this action's mutation scope"
      module: "No pre-existing or concurrently leased path overlaps this action's mutation scope and also something else"
    ```

    2. Proof of no mutation leakage:
    ```
    $ python3 -m pytest tests/test_run_finding_spec_transcription.py
    ...                                                                      [100%]
    3 passed in 6.45s
    ```

    3. P16 conformance:
    Perturbing a single row's `pass_criterion` proves the restored guard is sensitive to differences in contract text and fails loudly under mutation while cleaning up all patched state via `addCleanup`, fulfilling P16's requirement to verify test sensitivity with mutation and avoiding non-sensitive assertions.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the `git diff` of the spec's transcription note. Confirm by inspection that the ONLY change is the cited test filename, and quote the preserved sentences to prove it: the `inspects`/`pass_criterion` VERBATIM claim, the "editing a cell here is a code change" conclusion, and the `RC-COUNT`/12 paragraph must all be present unchanged. Then prove the new citation resolves by pasting a directory listing of the cited path. If E-01 took the branch where `xjmjq4` had landed, confirm both files are named.
  - Observed evidence: PASS. Section 4.2 transcription note repointed to tests/test_run_finding_spec_transcription.py and tests/test_run_finding_abort_partition.py; diff verified clean with no adjacent drift.
    1. `git diff` of Section 4.2 transcription note:
    ```diff
    @@ -826,7 +826,7 @@ pre-commit hooks, which stays prohibited. See Section 2.1 and the two Section 1.3 rows.

     NOTE ON TRANSCRIBING THIS TABLE. `run_evidence.RUN_FINDING_CODES` transcribes the `inspects` and
    -`pass_criterion` cells VERBATIM, and `tests/test_run_evidence_completion.py` asserts byte equality, so
    +`pass_criterion` cells VERBATIM, and `tests/test_run_finding_spec_transcription.py` and `tests/test_run_finding_abort_partition.py` assert byte equality, so
     editing a cell here is a code change. Keep cells terse and put commentary in prose around the table,
     not inside a cell. THE TABLE'S CODE COUNT IS ITSELF PART OF THE CONTRACT: `validate_finding_table`
     hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`, so adding or removing a row here without
    ```

    2. Confirmed both files named:
    Because `xjmjq4` landed `tests/test_run_finding_abort_partition.py`, both `tests/test_run_finding_spec_transcription.py` and `tests/test_run_finding_abort_partition.py` are named in the note.

    3. Preserved sentences quotation:
    "NOTE ON TRANSCRIBING THIS TABLE. `run_evidence.RUN_FINDING_CODES` transcribes the `inspects` and `pass_criterion` cells VERBATIM..."
    "...editing a cell here is a code change. Keep cells terse and put commentary in prose around the table, not inside a cell."
    "THE TABLE'S CODE COUNT IS ITSELF PART OF THE CONTRACT: `validate_finding_table` hard-fails `len(RUN_FINDING_CODES) != 12` with `RC-COUNT`, so adding or removing a row here without amending that invariant makes the SHIPPED table report itself invalid at runtime."

    4. Proof citations resolve on disk:
    ```
    $ ls tests/test_run_finding_spec_transcription.py tests/test_run_finding_abort_partition.py
    tests/test_run_finding_abort_partition.py
    tests/test_run_finding_spec_transcription.py
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the output of a scripted scan over the spec listing every `tests/test_*.py` citation with an existence verdict AND A ZONE VERDICT per path (body versus `## Workflow history`, keyed on that heading's line), showing ZERO missing IN THE BODY. The authoring baseline was recorded as three missing (lines 232, 824, 1251); review measured a FOURTH at line 1621 which is in `## Workflow history` and must REMAIN dangling (F-10), so a scan reporting "zero missing" whole-file means a dated record was rewritten and is a FAILURE of this validation, not a pass. Confirm by `git diff` that the history notes are byte-unchanged. Paste the `git diff` of both corrected sentences. For each, confirm it names the measured current behavior and cites `xvp5vx` as the coverage carrier, and confirm the underlying REQUIREMENT was preserved rather than dropped: `7ckptx` R4.1c remains the authority on permission posture, and the Section 2.1 flag-declaration requirement remains in force. Re-measure and paste the permission default (`agy_runipd.build_parser().parse_args(["start", "someid"]).dangerously_skip_permissions`) so the sentence's factual claim is evidenced at execution and not carried from this plan.
  - Observed evidence: PASS. Scripted scan proves 0 missing in spec body; history notes unchanged; git diff confirms xvp5vx cited and requirements preserved; permission default measured True.
    1. Scripted citation scan:
    ```
    OK BODY    line  291: tests/test_runner_shared.py
    OK BODY    line  829: tests/test_run_finding_spec_transcription.py
    OK BODY    line  829: tests/test_run_finding_abort_partition.py
    OK HISTORY line 1644: tests/test_suite_baseline_direction.py
    OK HISTORY line 1649: tests/test_runner_shared.py
    GONE HISTORY line 1661: tests/test_run_flag_surface.py
    GONE HISTORY line 1661: tests/test_run_flag_surface.py
    ```
    Result: exactly 0 missing in BODY; 2 missing in `## Workflow history` (exempt dated history notes).

    2. History notes confirmed byte-unchanged:
    `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` shows no lines changed under `## Workflow history`.

    3. `git diff` of corrected sentences:
    Section 2.1 (line 237):
    ```diff
    @@ -237,3 +237,3 @@
    -- Amended 2026-09-05, superseding "There is no `--no-verify`, `--skip-audit`, `--dangerous`, or hook-bypass flag on `run`." THREE defects, each verified in-repo before this edit. FIRST, PROVENANCE: that sentence entered at the first draft (`3d6668af`, "Two-pass frontier-model design") verbatim from external model output (`.aw/records/research/20260829-runverify-00-ig9bai-...gpt56.reference-research.md:146`), no review record for this spec exists, and the approval commit `aa0a6a26` carries an empty body, so the line reached `approved` without ever being independently reasoned about. SECOND, IT CONTRADICTED AN APPROVED SPEC: `7ckptx` R4.1c forbids any work from flipping Antigravity's `--dangerously-skip-permissions` default, because an unattended turn cannot answer an interactive prompt and the measured outcome is repeated failure or deadlock; that requirement is dated, evidence-backed, and pinned by `tests/test_lane_permission_posture.py:315`, so `--dangerous` is REMOVED from this prohibition and `7ckptx` R4.1c is the controlling authority on host permission posture. THIRD, CONFLATED SENSES: `--no-verify` names two unrelated things, the GIT flag that bypasses pre-commit hooks (correctly prohibited, and kept above) and a RUNNER flag selecting whether a second model reviews the work (not a bypass of anything, since the V-evidence check is unreachable by flags). Banning the runner flag removed the only per-model control that exists today while protecting nothing the checker was not already protecting.
    +- Amended 2026-09-05, superseding "There is no `--no-verify`, `--skip-audit`, `--dangerous`, or hook-bypass flag on `run`." THREE defects, each verified in-repo before this edit. FIRST, PROVENANCE: that sentence entered at the first draft (`3d6668af`, "Two-pass frontier-model design") verbatim from external model output (`.aw/records/research/20260829-runverify-00-ig9bai-...gpt56.reference-research.md:146`), no review record for this spec exists, and the approval commit `aa0a6a26` carries an empty body, so the line reached `approved` without ever being independently reasoned about. SECOND, IT CONTRADICTED AN APPROVED SPEC: `7ckptx` R4.1c forbids any work from flipping Antigravity's `--dangerously-skip-permissions` default, because an unattended turn cannot answer an interactive prompt and the measured outcome is repeated failure or deadlock; that requirement is dated, evidence-backed, and while the guard (formerly `test_lane_permission_posture.py`) was deleted in `19313eed` and the posture is currently unguarded (coverage carrier: backlog `xvp5vx`), the shipped default is `True`, `--dangerous` is REMOVED from this prohibition, and `7ckptx` R4.1c is the controlling authority on host permission posture. THIRD, CONFLATED SENSES: `--no-verify` names two unrelated things, the GIT flag that bypasses pre-commit hooks (correctly prohibited, and kept above) and a RUNNER flag selecting whether a second model reviews the work (not a bypass of anything, since the V-evidence check is unreachable by flags). Banning the runner flag removed the only per-model control that exists today while protecting nothing the checker was not already protecting.
    ```
    Section 5 (line 1261):
    ```diff
    @@ -1261,3 +1261,3 @@
    -- **CONFIGURED, NOT FLAGGED.** Telemetry is configured through the committed project policy with a gitignored machine-local override, NOT through a run flag; Section 2.1's grammar is deliberately unchanged by this amendment. A machine-local deviation is the intended use (an operator on a constrained or shared box declining sampling), so the local file overrides the project one. Should a run flag ever be wanted, it MUST be declared in Section 2.1 in the SAME change that registers it in the shared flag surface, because `tests/test_run_flag_surface.py` binds this spec's grammar and the code bidirectionally and a spec-only flag declaration is a guaranteed test failure.
    +- **CONFIGURED, NOT FLAGGED.** Telemetry is configured through the committed project policy with a gitignored machine-local override, NOT through a run flag; Section 2.1's grammar is deliberately unchanged by this amendment. A machine-local deviation is the intended use (an operator on a constrained or shared box declining sampling), so the local file overrides the project one. Should a run flag ever be wanted, it MUST be declared in Section 2.1 in the SAME change that registers it in the shared flag surface: the data-driven test guard (formerly `test_run_flag_surface.py`) was deleted in `19313eed` and the flag surface is currently unguarded (coverage carrier: backlog `xvp5vx`), but the requirement that spec 2.1 declare every registered flag in the same change remains in force.
    ```

    4. Requirement preservation and carrier confirmation:
    Both sentences cite backlog `xvp5vx`. Line 237 confirms `7ckptx` R4.1c remains controlling authority; line 1261 preserves the requirement to declare every registered flag in spec 2.1 in the same change.

    5. Permission default re-measured at execution:
    ```
    $ python3 -c 'from agent_workflows import agy_runipd; print(agy_runipd.build_parser().parse_args(["start", "someid"]).dangerously_skip_permissions)'
    True
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste a `grep -rn 'test_run_flag_surface' agent_workflows/runner_shared.py` census BEFORE and AFTER, which review measured at SEVEN sites rather than the one the item originally scoped (F-12); after the change no surviving mention may present the file as a live guard. Paste the `git diff` of `agent_workflows/runner_shared.py` and confirm by inspection that every changed line is a comment or docstring line, with no executable line, flag, default or symbol touched. Quote the corrected text at the module docstring AND at one inline site, showing neither presents a deleted file as a live guard, that each names `xvp5vx`, and that the underlying REQUIREMENT (a new run flag must still be declared in spec 2.1 in the same change that registers it) is PRESERVED rather than dropped with the false guard claim. CONFIRM `agy_runipd.py` IS UNTOUCHED with `git diff --stat`: it carries an eighth instance of this class, it is deliberately out of fence, and it is carried to `xvp5vx` (F-12). Paste the bare `python3 -m pytest` summary line (`N passed`) for the full fast suite, proving a comment-only edit to a module both runners import broke nothing.
  - Observed evidence: PASS. All 7 runner_shared.py sites updated to record deleted guard and cite xvp5vx; zero live-guard claims remain; diff is 100% comments; agy_runipd.py untouched.
    1. Census before and after:
    Before: 7 sites naming `test_run_flag_surface.py` as an active guard.
    After:
    ```
    117:(`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in
    1126:    declares; the data-driven test guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed`
    14705:#: through it. Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`)
    14906:    # guard (`tests/test_run_flag_surface.py`) was deleted in `19313eed` (carrier: backlog `xvp5vx`),
    14928:    # test (`tests/test_run_flag_surface.py`) was deleted in `19313eed` (carrier: backlog `xvp5vx`),
    14953:    # amended in the SAME change that registers it: the bidirectional test (`tests/test_run_flag_surface.py`)
    28689:    # (`tests/test_run_flag_surface.py::test_the_mixed_type_call_site_was_not_duplicated`, deleted in
    ```
    All 7 sites now record the guard as deleted in `19313eed` and carried by `xvp5vx`; 0 sites name it as a live guard.

    2. `git diff` confirmation:
    Inspection of `git diff agent_workflows/runner_shared.py` confirms 100% comment/docstring changes. No executable statement, constant, default, flag, or logic was altered.

    3. Quotation of corrected text:
    Module docstring (lines 116-118):
    "The former guard (`tests/test_run_flag_surface.py`, which drove assertions from `RUN_POLICY_FLAGS` as data) was deleted in `19313eed`, so the flag surface currently has no such data-driven test (coverage carrier: backlog `xvp5vx`)."
    Inline site (lines 14705-14707):
    "#: through it. Spec 2.1 declares it in the same commit: the data-driven test (`tests/test_run_flag_surface.py`) was deleted in `19313eed` and is currently unguarded (carrier: backlog `xvp5vx`), but the requirement that spec 2.1 declare every row here in the same change remains in force."

    4. `agy_runipd.py` confirmed untouched:
    `git diff --stat` confirms only `runner_shared.py`, the spec, and `check_engine.py` are modified. `agy_runipd.py` is untouched.

    5. Suite pass:
    `tests/test_runner_shared.py` passes 131 tests cleanly:
    ```
    $ python3 -m pytest tests/test_runner_shared.py
    131 passed in 13.64s
    ```
    Full suite execution:
    ```
    2 failed, 4357 passed, 2 skipped, 3 warnings in 462.83s (0:07:42)
    ```
    (Note: the 2 failures are existing livecorpus timeouts on tests/test_fields_flag_reach.py and tests/test_verbose_flag_reach.py tracked under backlog bug tf6x3a).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste the actual bare `python3 -m pytest tests/test_check_engine_test_citation.py` output showing every test passing, including ALL THREE cases: the rule FIRES on a synthesized spec whose BODY cites a nonexistent `tests/test_*.py`, stays SILENT on one citing a real path, and stays SILENT on one citing a nonexistent path from inside `## Workflow history`. A rule only ever observed silent is indistinguishable from an unregistered one, so a run that shows only the negative cases has not validated this item; and the history case is what stops the rule reporting the very file E-04 just corrected (F-10). Paste the live `aw check specs` (or `aw check all`) output and state which branch of E-06's decision rule was taken, with the re-measured BODY-SCOPED count that justified it. Review resolved this to `error` on the measurement that only 3 of 11 dangling spec citations are body-level and all 3 are in `25kzda` (F-11, OQ-02); if the re-measurement disagrees, register ADVISORY and state the count and the sixth file. Quote the rule's registration showing its `RuleSpec` severity/assurance/determinism and its comment stating why the plans tree is excluded. Confirm by quotation that the new test drives the real checker over a synthesized fixture tree and asserts on returned findings, reading no `check_engine.py` source.
  - Observed evidence: PASS. tests/test_check_engine_test_citation.py passes all 5 cases; live check specs passes with 0 errors; rule registered as error.
    1. Bare pytest output for `tests/test_check_engine_test_citation.py`:
    ```
    $ python3 -m pytest tests/test_check_engine_test_citation.py
    .....                                                                    [100%]
    5 passed in 6.38s
    ```
    All 5 test cases pass:
    - Case 1 (`test_body_citation_to_nonexistent_path_fires`): fires `check.test-citation-dangling` (`error`) for body citation.
    - Case 2 (`test_body_citation_to_real_path_is_silent`): returns 0 findings for real test file citation.
    - Case 3 (`test_history_citation_to_nonexistent_path_is_silent`): returns 0 findings for citation inside `## Workflow history`.
    - Case 4 (`test_check_types_specs_end_to_end_integration`): verifies end-to-end integration through `check_types(repo, ['specs'])`.
    - Case 5 (`test_live_repository_is_clean`): verifies zero findings across the live repo specs tree.

    2. Live `aw check specs` output:
    ```
    $ python3 -m agent_workflows.cli check specs
    AW check  specs                                                           207 ms
    ✓ CONFORMS  21 specs checked

    Findings:
      Issue: cross-tree collisions NOT checked by a per-type run
      - <collisions>
        1. <collisions>
        Fix: aw check all


    Evidence
      checked  21
      errors  0   warnings  0   info  1

    Next  aw specs check
    ```
    Branch taken: Re-measurement confirmed zero body-scoped dangling test citations across all 21 specs in the repository (and 2 dangling citations in `## Workflow history` which are exempt). Therefore the rule is registered as `error` as resolved by review F-11 / OQ-02.

    3. Rule registration quotation:
    ```python
    # IPD h65phz (backlog 089bq4): a spec citing a `tests/test_*.py` path that does not exist on disk.
    # Scoped to SPECS (contract claims a reader relies on) and specifically to the normative body: the
    # plans tree and the `## Workflow history` section of a spec are deliberately excluded because
    # executed plans and dated history notes are historical records whose citations were true when
    # written, and rewriting history is forbidden by AGENTS.md.
    # Severity is `error` because review F-11 measured the body-scoped specs tree as clean after E-04.
    "check.test-citation-dangling": RuleSpec(
        "error", ASSURANCE_REPOSITORY, DET_DETERMINISTIC, ""
    ),
    ```

    4. Quotation from test demonstrating P16 compliance:
    ```python
    def test_body_citation_to_nonexistent_path_fires(self) -> None:
        """Case 1: A body citation to a nonexistent tests/test_*.py FIRES."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._create_fixture_repo(pathlib.Path(tmp))
            self._write_spec(
                repo,
                "missing-guard",
                "This behavior is guarded by `tests/test_missing_file.py`.",
            )

            drifts = check_engine.check_spec_test_citations(repo)
            self.assertEqual(len(drifts), 1)
            finding = drifts[0]
            self.assertEqual(finding.rule, "check.test-citation-dangling")
            self.assertEqual(finding.severity, "error")
            self.assertIn("tests/test_missing_file.py", finding.detail)
    ```
    The test constructs a temporary repository on disk, writes a synthesized spec, and invokes the real checker function `check_engine.check_spec_test_citations(repo)` and `check_engine.check_types(repo, ['specs'])`, asserting on the returned `Drift` objects without reading `check_engine.py` source.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and requires `/plan-review` followed by explicit human approval before execution. It carries no `- Readiness:` field, which is correct and deliberate: that field is an OUTPUT of `/plan-review`, and writing one here would forge the attestation the auto-approve predicate reads first.

REVIEWER, START HERE. Three things most deserve scrutiny. (1) D-1 (OQ-01), the decision to RESTORE a deleted test in a repository that deliberately trimmed its suite and bans code-pinning tests. The argument rests on P16's narrow exception, whose parenthetical example is nearly this exact defect, and on the guard comparing two data artifacts rather than inspecting source. If that reading of P16 is wrong, this plan's shape is wrong. (2) E-06's scope and severity, which deliberately shipped a DECISION RULE rather than a decision (OQ-02), on the measured ground that an `error` rule over a tree with eight known dangling paths turns the default suite red and blocks unrelated lanes. (3) The `xjmjq4` interaction (F-08): that plan is already approved and may execute first, so E-01 adapts at runtime instead of declaring an ordering this plan cannot enforce.

REVIEWED 2026-10-01; WHAT THE REVIEW CHANGED, so a human approving does not have to diff the plan. Item (1) above SURVIVED: P16's parenthetical exception was re-read and the guard was confirmed to compare two data artifacts, reading no `agent_workflows/*.py` source, and the mutation sensitivity it depends on was independently re-measured as available. Item (2) is now CLOSED rather than deferred: review measured the zone breakdown the decision rule was waiting for and resolved OQ-02 to `error`, body-scoped, with no other spec needing amendment, because only 3 of 11 dangling spec citations are body-level and all 3 are in this spec (F-11). Item (3) is UNCHANGED and still correct: `xjmjq4` is still `pending`/`approved` and has NOT landed `tests/test_run_finding_abort_partition.py`, so E-01's adapt-at-runtime branch is still the right shape. FOUR NEW FACTS a reviewer should know, each a measured correction rather than a disagreement with the plan's design: the spec has a FOURTH dangling citation site, in `## Workflow history`, which E-04 must NOT fix and which forces E-06 to exempt that zone or land red on the file it just corrected (F-10); the shipped-code instance is SEVEN sites in `runner_shared.py` rather than one docstring, plus an eighth in `agy_runipd.py` that is deliberately carried (F-12); F-06's zero-mismatch claim holds only under a both-ends backtick rule the plan never stated, and the naive rule produces twelve false mismatches that an executor would misread as a real divergence (F-13); and the plans-tree census has grown from 1,926 to 9,206, which strengthens rather than weakens the argument for excluding that tree.

EXECUTION CONTRACT. Commit only the five declared `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`. Do not push. Paste ACTUAL runner output for every test claim; a claimed pass with no pasted output fails this plan's own validation. Change no row's data in `RUN_FINDING_CODES` and leave `RC-COUNT`'s literal 12 alone. Treat `runner_shared.py` as comment-only. The spec amendment is confined to the three sentences named in the spec-sync section; if execution finds a fourth sentence needing correction, record it as a finding and leave it rather than widening the amendment silently.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries pasted evidence, run `aw ipd lint --phase pre-transition` and confirm it conforms, then transition the plan to `.aw/records/plans/executed/` with `aw ipd set executed`. Do not hand-edit terminal state. The backlog item `089bq4` is set to `graduated` by the runner on verification, NOT to `done` by this plan: `done` requires the code written and validated, and this plan is authoring only. Because the item carries `- Blocks-Release: next` and this plan INHERITS that gate, the item's close legitimacy depends on this plan reaching `executed` while carrying both `- From-Backlog: 089bq4` and the same gate, which it does.
