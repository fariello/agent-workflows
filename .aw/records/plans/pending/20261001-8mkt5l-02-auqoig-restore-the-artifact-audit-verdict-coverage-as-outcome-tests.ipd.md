# IPD: Restore the artifact_audit verdict coverage as outcome tests after triage

- Date: 2026-10-01
- Kind: child
- Concern: The suite trim `19313eed` deleted the whole `VerdictParityTests` class from `tests/test_artifact_audit.py`, and nothing replaced what it asserted: what an audit CONCLUDES. Measured in this lane at HEAD `d566b7a8`, three distinct behaviors of `agent_workflows.artifact_audit` now have ZERO test reaching them. (1) `read_declared_status` is referenced by NO test in `tests/` at all, so its documented multi-word-status parity with `selectors._STATUS_RE` is unpinned; dropping the regex's trailing `\s*$` anchor makes it return `EXECUTED` where it must return `None`, and no test would go red. (2) `expected_dir_for_status` is exercised for `executed` and for the non-landed statuses that map to `pending` (`tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion`), but NO test anywhere passes `superseded`, `not-executed`, or `reusable`, so three of the four entries in `_TERMINAL_EXPECTED_DIR` are unpinned. (3) `audit_artifact`'s `is_live` passthrough is reached by no `tests/test_artifact_audit*.py` test, and no test asserts that a live pre-terminal step is NOT drift. Separately, the deleted class contained one assertion that is now WRONG rather than merely absent, and a mechanical restore would therefore have failed: `test_four_verdict_shapes` asserted that run-status `superseded` against a file in `executed/` yields `location_mismatch` without `status_mismatch`, and the `allowed_lifecycle_pairs` redesign in `33834c719` makes that case report BOTH mismatches. `test_expected_dir_for_status_maps_every_disposition` is likewise stale: it asserts `complete` and `substantially-complete` map to `executed`, which commit `6b94a4d9d` deliberately reversed.
- Scope: Add outcome-asserting tests for the three uncovered verdict behaviors named in the Concern, written against today's actual semantics rather than restored verbatim. IN: a new `tests/test_artifact_audit_verdicts.py` holding (a) the four verdict SHAPES of `audit_artifact` (clean, location-only, status-only, missing) re-expressed with run statuses that produce those shapes under `allowed_lifecycle_pairs` today, (b) the `is_live` passthrough plus the no-drift property for a live pre-terminal step, (c) `expected_dir_for_status` over the three retirement/standing dispositions no test reaches, and (d) the multi-word-status parity of `read_declared_status`. OUT: any change to `agent_workflows/artifact_audit.py` (this plan is coverage only and must leave production code byte-identical); the cache-invalidation routes already covered by `tests/test_artifact_audit_index_cache.py` (plan `dea7dr`); the three deleted tests this plan judges should STAY deleted or stay re-expressed rather than restored (`OneImplementationTests` as a class, triaged in F-04); `tests/test_terminal_status_vocabulary.py`, which already owns the `complete` coercion question and must not be duplicated; and the pre-existing order-dependent failure in `tests/test_statusline_behavior.py` recorded in F-08.
- Scope-Paths: tests/test_artifact_audit_verdicts.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: 1sn4h0
- Set: 8mkt5l
- Order: 2
- Highest E allocated: 07
- Author: opencode model=its_direct/pt3-claude-opus-5-1m-us
- Id: auqoig

## Workflow history
- 2026-10-02 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (E-06(d) mutation retargeted to the classify_difference return site; constant swap is invisible), PR-002 (E-07/V-07 baseline re-derived at execution, not 4356), PR-003 (test counts/names no longer the bar), PR-004 (F-04 cites git object; scratch under gitignored tmp/), PR-005 (gate requires aw ipd finalize; OQ-01 owner). All F-06 shapes, F-02, F-05, F-07 re-measured at lane HEAD 49844944f.

- 2026-10-01 to-review (opencode model=its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `1sn4h0`. Every claim below was MEASURED in this lane at HEAD `d566b7a8` by running the deleted tests against today's code, not transcribed from the item. THE ITEM'S CENTRAL PREMISE HELD AND ITS FRAMING DID NOT. Confirmed: `19313eed` deleted `VerdictParityTests` entire (four tests), and the item is right that this needs triage rather than a mechanical restore. But the triage reason the item gives (P16 code-pinning) is NOT the reason that applies to these four: all four assert on real function return values, so none is a code-pinning test. The reason a mechanical restore fails is DIFFERENT and larger: two of the four now FAIL against today's code because the behavior they pinned was deliberately changed by later commits (`6b94a4d9d` removed the `complete` coercion; `33834c719` replaced the mismatch logic with `allowed_lifecycle_pairs`). Restoring them verbatim would re-assert a contract the repository intentionally abandoned. Measured: of the four, `test_liveness_is_carried_through_and_never_derived` and `test_multi_word_status_is_unreadable_by_design` pass unchanged, and `test_four_verdict_shapes` and `test_expected_dir_for_status_maps_every_disposition` fail. ALSO FOUND, and it is why this plan is worth executing beyond bookkeeping: the genuine coverage hole is wider than the four deleted tests, because `read_declared_status` has NO test in the entire suite and `expected_dir_for_status` has none for three of its four terminal entries. NOTE ON THE ITEM'S HEADLINE: the item's stale-index motivation is already addressed by `dea7dr`, which is executed and shipped `tests/test_artifact_audit_index_cache.py`; this plan deliberately does NOT re-cover that, and the item itself says so. GATE NOTE: item `1sn4h0` carries no `- Blocks-Release:`, so this plan inherits none.

## Goal

Make the three verdict behaviors that `19313eed` left unpinned able to go red again, by adding outcome tests that assert what `agent_workflows.artifact_audit` actually concludes today. Concretely: pin `read_declared_status`'s multi-word refusal (currently untested anywhere in the suite), pin `expected_dir_for_status` over the three retirement/standing dispositions no test reaches, pin the `is_live` passthrough and the live-step no-drift property, and re-express the four verdict shapes against the `allowed_lifecycle_pairs` semantics that replaced the ones the deleted test asserted.

Secondarily, and stated plainly because it decides how this plan should be reviewed: this is NOT a restore. Two of the four deleted tests encode a contract the repository deliberately reversed, so re-adding them would be a regression dressed as coverage. The deliverable is new tests that assert today's truth, plus a recorded triage verdict per deleted test so the next reader does not re-litigate it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: prove the premise before writing any test

- [ ] E-01 RE-DEMONSTRATE THE DELETION AND THE TWO STALE ASSERTIONS AT THE EXECUTION HEAD, before creating the new test file. Extract the historical file with `git show 19313eed^:tests/test_artifact_audit.py` into a scratch path INSIDE this worktree under the gitignored `tmp/` directory (not `/tmp`, and never a tracked path), confirm `class VerdictParityTests` and all four test names are present there and absent from `tests/test_artifact_audit.py` at HEAD, then copy the four deleted bodies verbatim into a scratch runner (NOT a committed test) and run them against today's `agent_workflows.artifact_audit`.

  IF THE FAILURE SET HAS CHANGED, STOP AND REPORT. This plan is built on exactly two of four failing (`test_four_verdict_shapes` on the `superseded` case, `test_expected_dir_for_status_maps_every_disposition` on the `complete` row) and two passing. If all four now pass, the re-expression in E-02 and E-04 is wrong and a verbatim restore may be correct instead; if a third fails, there is a behavior change this plan has not accounted for. Either way the triage must be redone rather than worked around.
  - Depends on: none
  - Expected outcome: the deletion shown both ways (present at `19313eed^`, absent at HEAD), plus a scratch run reporting `FAILED (failures=2)` naming those two tests, with both failure messages captured. Authoring measurements: `expected_dir_for_status("complete")` returned `'pending'` against an asserted `'executed'`; the `superseded`-in-`executed/` case returned `status_mismatch=True` against an asserted `False`.
  - Execution state: pending

### Task group 2: re-express the verdict shapes against today's semantics

- [ ] E-02 CREATE `tests/test_artifact_audit_verdicts.py` AND ADD THE FOUR VERDICT SHAPES, each built in its own `tempfile.TemporaryDirectory()` repo root with the plan directories created, asserting on `artifact_audit.audit_artifact`'s return value. Use the shapes F-06 measured, which are reachable today: CLEAN, an `- Status: executed` plan in `executed/` audited with `status="executed"`, asserting `location_mismatch is False`, `status_mismatch is False`, `has_discrepancy is False`, `difference_class == artifact_audit.CLASS_UNCHANGED`. LOCATION-ONLY, an `- Status: executed` plan left in `pending/` audited with `status="executed"`, asserting `location_mismatch is True`, `status_mismatch is False`, `difference_class == artifact_audit.CLASS_REGRESSED`. STATUS-ONLY, an `- Status: approved` plan in `executed/` audited with `status="executed"`, asserting `location_mismatch is False`, `status_mismatch is True`, `difference_class == artifact_audit.CLASS_UNKNOWN`. MISSING, an id6 written nowhere, asserting `missing_entirely is True` and `difference_class == artifact_audit.CLASS_MISSING`.

  DO NOT reuse the deleted test's `status="superseded"` route to reach the location-only shape: F-02 measured that it now reports BOTH mismatches, and F-03 shows that is the intended consequence of `allowed_lifecycle_pairs`. Reference the class CONSTANTS (`artifact_audit.CLASS_UNCHANGED` and siblings) rather than the bare strings, so a constant rename is a visible break rather than a silent mismatch. Per OQ-01 assert both the booleans and the class.
  - Depends on: E-01
  - Expected outcome: a new file whose tests pin all four shapes (how they are split into test functions is the executor's choice), all passing, asserting the boolean triple and the `difference_class` for each shape, with no production code touched.
  - Execution state: pending

### Task group 3: restore the two behaviors that still hold

- [ ] E-03 ADD THE `is_live` PASSTHROUGH AND LIVE-STEP NO-DRIFT TEST, restored in substance from the deleted `test_liveness_is_carried_through_and_never_derived` (which F-02 measured as still passing, so this is a true restore and not a re-expression). Build a plan with `- Status: approved` in `pending/`, audit it twice with `status="running"` and `is_live=True` then `is_live=False`, and assert that `audit.is_live` mirrors the input in both directions AND that `has_discrepancy is False` in both, because a running step's plan sitting in `pending/` is correct and must not be reported as drift either way. Keep the deleted test's docstring point that `is_live` is an INPUT this module only records and never derives.
  - Depends on: E-02
  - Expected outcome: one test asserting both `is_live` directions and both no-drift outcomes, passing.
  - Execution state: pending

- [ ] E-04 ADD THE `expected_dir_for_status` TEST FOR THE DISPOSITIONS NO TEST REACHES. Assert `superseded`, `not-executed`, and `reusable` each map to their own directory name (the three `_TERMINAL_EXPECTED_DIR` entries F-05 proved unpinned), assert `executed` maps to `executed`, and sweep the pre-terminal statuses `draft`, `to-review`, `reviewed`, `approved`, `queued`, `running` to `pending`.

  DELIBERATELY OMIT the `complete` and `substantially-complete` rows the deleted test carried. F-03 shows `6b94a4d9d` reversed both answers on purpose, and `tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion` already owns that contract; re-adding them here would either re-assert an abandoned contract or create a second owner of a live one. If execution believes those rows belong in this file, it must say so in the evidence rather than adding them silently.
  - Depends on: E-02
  - Expected outcome: one test covering four terminal/standing dispositions plus a six-status pre-terminal sweep, passing, with no `complete`/`substantially-complete` row.
  - Execution state: pending

- [ ] E-05 ADD THE `read_declared_status` MULTI-WORD PARITY TEST, restored in substance from the deleted `test_multi_word_status_is_unreadable_by_design`. Write a file whose body contains `- Status: EXECUTED (approved by maintainer)` and assert `artifact_audit.read_declared_status(f) is None`, because the anchored pattern must refuse a multi-word value rather than return a partial read. ALSO assert the positive control in the same test: a file carrying a single-token `- Status: executed` returns `"executed"`. The positive control is what stops the test passing vacuously if the reader were ever broken into always returning `None`.
  - Depends on: E-02
  - Expected outcome: one test asserting both the multi-word refusal and the single-token read, passing. F-05's `grep` for `read_declared_status` in `tests/` must now match this file where it previously matched nothing.
  - Execution state: pending

### Task group 4: prove the new tests can fail, and that nothing else moved

- [ ] E-06 PROVE MUTATION SENSITIVITY FOR EACH NEW BEHAVIOR, by breaking the production behavior in the working tree one mutation at a time, confirming the intended test goes RED, and REVERTING before the next. Four mutations, one per task-group-2/3 deliverable. (a) For E-05: delete the trailing `\s*$` from `artifact_audit._STATUS_LINE_RE`; F-07 measured that this makes the multi-word input read `EXECUTED` instead of `None`, so the multi-word test must fail. (b) For E-04: remove the `"reusable"` entry from `_TERMINAL_EXPECTED_DIR`; the new disposition test must fail on that row. (c) For E-03: hard-code `is_live=False` where `audit_artifact` records it; the passthrough test must fail on the `True` direction. (d) For E-02: in `artifact_audit.classify_difference`, change the plans-branch return quoted as `# BACKWARDS: the run recorded a SUCCESS and the artifact is in neither` from `CLASS_REGRESSED` to `CLASS_UNKNOWN`, so the location-only shape classifies `unknown` with its booleans unchanged; this is the mutation OQ-01 exists to catch, and it must turn the location-only shape test red (a test asserting only the booleans would survive it). MUTATE THE RETURN SITE, NOT THE CONSTANTS: swapping the VALUES of `CLASS_REGRESSED` and `CLASS_UNKNOWN` at their definitions is invisible to tests that reference the constants (as E-02 requires), so it would prove nothing.

  REVERT AFTER EACH, and finish with `git diff --stat agent_workflows/` empty. Do NOT commit any mutation. If any mutation leaves every test green, the corresponding test is vacuous: fix the test, re-run the mutation, and record both attempts.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: four recorded red runs, one per mutation, each naming the test that failed and why, and a clean `agent_workflows/` afterwards.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE AND RECONCILE AGAINST THE BASELINE. Run `python3 -m pytest` with no added flags (the configured `addopts` already supply `-q -n auto --dist=worksteal` and the fast-subset markers; adding `-n0` or a second `-q` is forbidden by `AGENTS.md`). Reconcile the counts against a baseline YOU re-derive with a bare `python3 -m pytest` on the clean tree at the execution head BEFORE creating the new file (F-08's `1 failed, 4356 passed, 2 skipped` at `d566b7a8` is authoring context, not the bar; the suite has since grown): the passed count must rise by exactly the number of tests this plan added, and the failing set must contain nothing that was not in your baseline's failing set. For EVERY failure in the post-change run, show it is in your baseline failing set, and for any that is not, run it alone at the pre-change head to show it is pre-existing and order-dependent (F-08's statusline test is the authoring-time instance); a new failure in `tests/test_artifact_audit_verdicts.py` is never pre-existing. Finally confirm `git status --short agent_workflows/` is empty, proving this coverage plan changed no production code.
  - Depends on: E-06
  - Expected outcome: a bare suite run whose final line reconciles with your re-derived baseline plus the new tests, every failure accounted for as pre-existing, and an empty `git status` for `agent_workflows/`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- OUTCOME TESTS ONLY, and this plan's subject matter sits right next to the line. `GUIDING_PRINCIPLES.md` forbids verifying implementation details by reading production source: "Never use `inspect.getsource`, `inspect.getsourcelines`, `ast.parse`, `read_text()`, or substring/regex searches against production code (`agent_workflows/*.py`)" ("No production source inspection"), and separately forbids asserting which module holds a `def` ("No architectural placement pins"). `AGENTS.md` repeats this as a hard prohibition. Consequence for this plan: the deleted `OneImplementationTests.test_docstring_records_the_aw_check_decision` read `artifact_audit.__doc__` and asserted substrings in it, which is exactly the banned shape and must NOT be restored (F-04).
- NEVER WEAKEN AN ASSERTION TO MAKE IT PASS. `GUIDING_PRINCIPLES.md`: "Under no circumstances should an assertion be relaxed, made conditional, or hollowed out so that a test passes vacuously", and a test is valid only if "breaking the underlying behavior makes the test fail". Consequence: where a deleted assertion no longer holds, this plan re-derives the CURRENT behavior from running code and asserts that, rather than deleting the assertion or loosening it to accept both answers (E-02, E-03).
- THE STATUS READER'S PARITY CONSTRAINT IS DELIBERATE AND DOCUMENTED AT THE CODE. `artifact_audit.read_declared_status`'s docstring states "A multi-word status yields None, matching the pattern that shipped inside `run_viewer` and `selectors._STATUS_RE`'s documented parity constraint", and both readers are the same pattern (`artifact_audit._STATUS_LINE_RE` and `selectors._STATUS_RE` are each `(?m)^- Status:\s*(\S+)\s*$`). `selectors`' own commentary says the two readers "provably disagree on 24 records" with `plans_index`, so the strictness is load-bearing and not an accident.
- THE TERMINAL VOCABULARY WAS RENAMED ON PURPOSE. `agent_workflows/runner_shared.canonical_terminal_status` maps legacy tokens via `TERMINAL_STATUS_ALIASES`, in which `substantially-complete` maps to `fail-gate` and NOT to `complete`; `artifact_audit._TERMINAL_EXPECTED_DIR` no longer contains a `complete` key and `_RUN_SUCCESS_STATUSES` is `frozenset({"executed"})`. `tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion` already owns this question, so this plan must not duplicate it.
- MISMATCH CLASSIFICATION IS NOW PAIR-DRIVEN. `artifact_audit.audit_artifact` computes `location_mismatch`/`status_mismatch` by searching `allowed_lifecycle_pairs(record_type, action, run_status)` for a `(declared_status, directory)` pair matching the file, and falls back to per-axis membership checks when none matches. `allowed_lifecycle_pairs` keys off the RUN status, so run-status `superseded` returns only pre-terminal `pending` pairs; that is why the deleted test's `superseded` case changed answer.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE DELETION IS REAL AND COMPLETE, as the item states. `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") removed `class VerdictParityTests` and all four of its tests; the file at HEAD contains neither the class nor any of the four names. The file went from 1312 lines to 529. | `git show 19313eed^:tests/test_artifact_audit.py` contains `class VerdictParityTests` at line 277 with `test_four_verdict_shapes`, `test_liveness_is_carried_through_and_never_derived`, `test_expected_dir_for_status_maps_every_disposition`, `test_multi_word_status_is_unreadable_by_design`. `grep -n "class \|def test_" tests/test_artifact_audit.py` at HEAD lists none of them. `wc -l`: 1312 then 529. |
| F-02 | A MECHANICAL RESTORE WOULD FAIL, which is the finding that most changes the item's framing. Two of the four deleted tests FAIL against today's code, because the behavior they pinned was deliberately changed after the deletion. Run verbatim in this lane: `test_liveness` and `test_multi_word` pass; `test_four_verdict_shapes` and `test_expected_dir` fail. | Deleted bodies copied verbatim into a scratch runner: `Ran 4 tests ... FAILED (failures=2)`, with `test_expected_dir ... FAIL`, `test_four_verdict_shapes ... FAIL`, `test_liveness ... ok`, `test_multi_word ... ok`. Failure 1: `expected_dir_for_status("complete")` returned `'pending'`, asserted `'executed'`. Failure 2: the `superseded`-in-`executed/` case returned `status_mismatch=True`, asserted `False`. |
| F-03 | BOTH BEHAVIOR CHANGES WERE INTENTIONAL, so the correct action is to assert the NEW answer and never to "fix" the code back. (a) `6b94a4d9d` ("statusvocab: rename the terminal status vocabulary so a label names its refusing authority") deleted the `"complete": "executed"` entry from `_TERMINAL_EXPECTED_DIR`, narrowed `_RUN_SUCCESS_STATUSES` from `{"executed","complete"}` to `{"executed"}`, and replaced the inline `substantially-complete` coercion with `canonical_terminal_status`, which maps it to `fail-gate`. (b) `33834c719` ("work(mlhryi): Audit runner queue artifacts by type and action") introduced `allowed_lifecycle_pairs`, which is what makes the `superseded` case report both mismatches. | `git show 6b94a4d9d -- agent_workflows/artifact_audit.py` shows `- "complete": "executed",` and `-_RUN_SUCCESS_STATUSES = frozenset({"executed", "complete"})` / `+_RUN_SUCCESS_STATUSES = frozenset({"executed"})`. `git log -S"allowed_lifecycle_pairs" -- agent_workflows/artifact_audit.py` names `33834c719`. `TERMINAL_STATUS_ALIASES` maps `"substantially-complete": "fail-gate"`. |
| F-04 | THE TRIAGE THE ITEM ASKS FOR, PER TEST, and its answer is not the one the item anticipated. The item expects P16 code-pinning to be the disqualifier; it disqualifies NONE of the four, because all four assert on real return values. VERDICT: restore-as-outcome-test all four, two verbatim-equivalent and two re-expressed. `test_multi_word` RESTORE AS IS (asserts `read_declared_status` returns `None`; passes today). `test_liveness` RESTORE AS IS (asserts `is_live` in/out and `has_discrepancy`; passes today). `test_expected_dir` RE-EXPRESS, dropping the two stale legacy rows (`complete`, `substantially-complete`) which `test_terminal_status_vocabulary.py` now owns, and KEEPING the three retirement/standing rows plus the pre-terminal sweep. `test_four_verdict_shapes` RE-EXPRESS against `allowed_lifecycle_pairs` semantics. SEPARATELY, one test in the same deleted region must STAY DELETED: `OneImplementationTests.test_docstring_records_the_aw_check_decision` asserts substrings (`"aw check"`, `"GITIGNORED"`, `"IPD-M105"`) in `artifact_audit.__doc__`, which is precisely the production-source-inspection shape `GUIDING_PRINCIPLES.md` bans; `test_run_viewer_audit_type_is_the_shared_module_object` asserts `run_viewer.StepArtifactAudit is artifact_audit.ArtifactAudit`, an architectural placement pin, and also stays deleted. Both are out of scope here and recorded so the next reader does not restore them. | Deleted bodies read via `git show 19313eed^:tests/test_artifact_audit.py` lines 19-57 (`OneImplementationTests`) and 277-353 (`VerdictParityTests`) (the authoring lane's gitignored scratch copy is not durable; the git object is). `GUIDING_PRINCIPLES.md` "No production source inspection" and "No architectural placement pins". |
| F-05 | THE REAL HOLE IS WIDER THAN THE FOUR DELETED TESTS, which is the strongest justification for executing this plan. `read_declared_status` appears in NO test file in `tests/`. `expected_dir_for_status` is asserted for `executed` and for non-landed statuses mapping to `pending`, but for NONE of `superseded`, `not-executed`, `reusable`, so three of four `_TERMINAL_EXPECTED_DIR` entries are unpinned. `is_live` is passed to `audit_artifact` by no test in `tests/test_artifact_audit*.py`. | `grep -rn "read_declared_status" tests/` returns nothing. `grep -rn 'expected_dir_for_status("superseded")\|...("not-executed")\|...("reusable")' tests/` exits 1 (no match). `grep -rn "is_live" tests/` matches only `test_statusline_visible_width.py` and `test_run_viewer.py`, never an `artifact_audit` verdict test. |
| F-06 | THE FOUR VERDICT SHAPES ARE STILL ALL REACHABLE TODAY, so re-expression is possible and the shapes need not be abandoned. Probed on today's code: CLEAN = `executed` file in `executed/` under run status `executed` gives `loc=False st=False disc=False cls=unchanged`. LOCATION-ONLY = `executed` file in `pending/` under run status `executed` gives `loc=True st=False cls=regressed`. STATUS-ONLY = `approved` file in `executed/` under run status `executed` gives `loc=False st=True cls=unknown`. MISSING = absent id6 gives `missing_entirely=True cls=missing`. The deleted test reached the location-only shape via run status `superseded`, which no longer produces it; run status `executed` with the file left in `pending/` does. | Scratch probe output: `1 clean executed/executed loc=False st=False miss=False disc=False cls=unchanged`; `2 loc-only executed in pending loc=True st=False miss=False disc=True cls=regressed`; `3 st-only approved in executed loc=False st=True miss=False disc=True cls=unknown`; `4 missing loc=False st=False miss=True disc=True cls=missing`. |
| F-07 | THE MULTI-WORD ASSERTION IS MUTATION-SENSITIVE, so it is a real test and not a tautology. Removing the trailing `\s*$` anchor from the pattern changes the answer on exactly the deleted test's input. | Probe on the two patterns against `- Status: EXECUTED (approved by maintainer)`: anchored (`(?m)^- Status:\s*(\S+)\s*$`) yields `None`; unanchored (`(?m)^- Status:\s*(\S+)`) yields `EXECUTED`. `artifact_audit._STATUS_LINE_RE` and `selectors._STATUS_RE` are both the anchored form. |
| F-08 | A PRE-EXISTING, UNRELATED SUITE FAILURE EXISTS AT THIS HEAD and must not be attributed to this plan. The bare suite reports one failure, `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`, which PASSES when run alone, so it is order-dependent (the suite randomizes order) and outside this plan's scope. Baseline to carry forward: `1 failed, 4356 passed, 2 skipped`. | `python3 -m pytest` at HEAD `d566b7a8`: `1 failed, 4356 passed, 2 skipped, 3 warnings in 423.28s`. The same nodeid alone: `1 passed in 41.67s`. |
| F-09 | `dea7dr` IS EXECUTED, so the item's cache motivation is already closed and must not be re-covered here. Its `tests/test_artifact_audit_index_cache.py` ships six tests over the invalidation routes. | `find .aw/records/plans -name "*dea7dr*"` resolves under `.aw/records/plans/executed/`. `grep -n "def test_" tests/test_artifact_audit_index_cache.py` lists six tests (routes 1-3, memoization, two compounds). |

## Proposed changes (ordered, validatable)

1. Re-reproduce the deletion and the two stale assertions at the execution head before writing anything, so the plan's premises are demonstrated rather than trusted (E-01).
2. Create `tests/test_artifact_audit_verdicts.py` holding the four verdict shapes, re-expressed against today's `allowed_lifecycle_pairs` semantics (E-02).
3. Add the `is_live` passthrough and live-step no-drift test, restored in substance from the deleted body (E-03).
4. Add the `expected_dir_for_status` test covering the three retirement/standing dispositions and the pre-terminal sweep, deliberately omitting the legacy rows owned elsewhere (E-04).
5. Add the `read_declared_status` multi-word parity test (E-05).
6. Prove every new test is mutation-sensitive by breaking the behavior and pasting the failure (E-06).
7. Run the bare suite and reconcile against the F-08 baseline, confirming production code is byte-identical (E-07).

## Deferred / out of scope (with reason)

- `OneImplementationTests.test_docstring_records_the_aw_check_decision` and `test_run_viewer_audit_type_is_the_shared_module_object` stay deleted, triaged in F-04 as a production-source-inspection test and an architectural placement pin respectively, both banned by `GUIDING_PRINCIPLES.md`.
  - Carrier-Declined: The correct disposition is PERMANENT deletion, not deferred restoration, so there is no future work for a carrier to hold. Filing one would schedule the re-introduction of two tests `GUIDING_PRINCIPLES.md` forbids ("No production source inspection", "No architectural placement pins"). The triage verdict itself is the deliverable and it is recorded in F-04.
- The `complete` / `substantially-complete` rows of the deleted `expected_dir_for_status` test are not re-added here, because `tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion` already asserts the post-`6b94a4d9d` answer for exactly those tokens, and duplicating it would create two owners of one contract.
  - Carrier-Declined: The coverage already EXISTS and is owned elsewhere, so there is no outstanding work to carry: `tests/test_terminal_status_vocabulary.py::TestArtifactAuditNoCompleteCoercion::test_expected_directory_mapping_for_canonical_and_legacy_statuses` asserts today's answer for `complete` and every `TERMINAL_STATUS_ALIASES` legacy token. Filing a carrier would schedule a duplicate owner of one contract, which is the outcome this row exists to prevent. (No `Carrier-Evidence:` is used because that field resolves only in-tree RECORDS artifacts, not test files.)
- The index-cache staleness routes are out of scope: `dea7dr` is executed and owns `tests/test_artifact_audit_index_cache.py` (F-09). The backlog item itself draws this line.
  - Carrier-Evidence: .aw/records/plans/executed/20260929-8mkt5l-01-dea7dr-make-the-artifact-audit-index-cache-see-a-change-its-directo.ipd.md
- The pre-existing order-dependent failure in `tests/test_statusline_behavior.py` (F-08) is not fixed here; it is unrelated to `artifact_audit` and recorded only so the suite baseline reconciles.
  - Carrier: 8sr0or
- No change is made to `agent_workflows/artifact_audit.py`. If execution finds a behavior it believes is WRONG rather than merely changed, it must stop and report rather than editing production code under a coverage plan.
  - Carrier-Declined: This is a SCOPE CONSTRAINT on this plan, not deferred work: there is no known defect in `artifact_audit` being parked. F-03 establishes that both behavior changes this plan encounters were intentional, so nothing here needs a future fix. Should execution discover a real defect, the gate instructs it to stop and report, which files a new item at that point rather than pre-committing a carrier to work nobody has shown is needed.

## Scope check

- Over-scope: none. `- Scope-Paths:` names exactly one new test file, and the plan forbids production edits.
- Under-scope: the plan does not restore every test `19313eed` deleted repository-wide (that trim touched many files); it closes only the `artifact_audit` VERDICT coverage the item names, plus the two adjacent holes F-05 measured in the same functions. A general audit of the trim is a separate, larger question and is not claimed here.

## Required tests / validation

Every validation item below demands PASTED runner output, not a claim. The new file is `tests/test_artifact_audit_verdicts.py`; run it with `python3 -m pytest tests/test_artifact_audit_verdicts.py` and the whole suite bare with `python3 -m pytest` (the configured `addopts` already supply `-q -n auto`, so do not add flags). Mutation sensitivity (E-06/V-06) is proved by editing production code in the working tree, capturing the failure, and REVERTING, leaving `git status` clean for `agent_workflows/`.

## Spec / documentation sync

N/A with reason: this plan adds test coverage for behavior that already shipped and changes no contract, no CLI surface, and no production module. No `.spec.md` file is touched, so `- Scope-Paths:` declares none and the runners' spec-edit announcement will correctly report nothing. The triage verdicts that a future reader needs are recorded in F-04 of this plan, which becomes the durable record once it is executed.

## Open questions

### OQ-01: Should the two re-expressed tests also assert the `difference_class`, or only the three booleans?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE, so no human decision is needed. Assert both. The booleans alone cannot distinguish the location-only shape from the status-only shape's operator-visible consequence: F-06 measured that location-only classifies `regressed` (the alarming class, which `CLASS_REGRESSED`'s own comment says "is what the red styling is FOR") while status-only classifies `unknown`. A test asserting only `loc`/`st` would pass if those two classes were ever swapped, which is the highest-consequence mutation in this module. The deleted test asserted only the booleans because it predated the class; there is no reason to inherit that limitation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste (a) the two `git show`/`grep` outputs proving `VerdictParityTests` and all four test names are present at `19313eed^` and absent at the execution head, and (b) the scratch runner output showing exactly two of the four deleted bodies failing, including both failure messages. If all four PASS, or if a third fails, the plan's premise has moved: stop and report rather than proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_artifact_audit_verdicts.py -o addopts="" -v` showing the shape tests passing, with a mapping from each test to the shape(s) it pins (test names and counts are pointers, not the bar), and paste the asserted values for each shape so a reviewer can check them against F-06 (clean `loc=False st=False disc=False cls=unchanged`; location-only `loc=True st=False cls=regressed`; status-only `loc=False st=True cls=unknown`; missing `missing_entirely=True cls=missing`). A test that asserts a shape F-06 did not measure must be justified in the evidence block.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `is_live` test passing, and show that it asserts BOTH directions (`is_live=True` yields `audit.is_live is True`, `is_live=False` yields `False`) AND that neither is a discrepancy (`has_discrepancy is False` both ways). Paste the assertion lines from the committed file alongside the passing run.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `expected_dir_for_status` test passing, and confirm by `grep` on the committed file that it asserts `superseded`, `not-executed`, and `reusable` (the three F-05 proved uncovered) and that it does NOT assert `complete` or `substantially-complete` (owned by `tests/test_terminal_status_vocabulary.py`). Both the presence and the absence must be shown.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `read_declared_status` test passing, and paste `grep -rn "read_declared_status" tests/` showing it now matches the new file (F-05 measured zero matches before).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: for EACH of the four mutations named in E-06, paste the mutation diff and the failing pytest output with the mutation applied, naming the test that went red, then paste `git diff --stat agent_workflows/` showing empty after reverting. A mutation that does NOT turn a new test red is a vacuous test and must be fixed, not recorded as an exception.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the full final line of a bare `python3 -m pytest` run, AND the final line of your own pre-change baseline run, and reconcile: the passed count must rise by exactly the number of tests added, and every post-change failure must appear in the baseline failing set (paste the isolated run for any that is order-dependent). Also paste `git status --short agent_workflows/` showing no production change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

`- Readiness:` was written by `/plan-review` (2026-10-02), its legitimate producer. The plan still requires explicit human approval before execution.

EXECUTION CONTRACT. Commit only the single path `- Scope-Paths:` declares, through `aw commit <plan> -- tests/test_artifact_audit_verdicts.py`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit, because this is a shared checkout and other parties' work must not be swept in. The scratch files this plan's E-01 and E-06 create (the extracted historical test file, the scratch runner, any probe script) are working aids and must NOT be committed.

HARD CONSTRAINT, and the one most likely to be violated under time pressure: this plan may not modify `agent_workflows/artifact_audit.py` or any other production module. E-06 edits production code TRANSIENTLY to prove mutation sensitivity and must revert each time; E-07 proves the tree is clean afterwards. If execution concludes that a behavior F-02 measured is a DEFECT rather than an intended change, the correct action is to stop, report, and let a separate plan carry the fix; silently "restoring" the old behavior would re-break what `6b94a4d9d` and `33834c719` deliberately changed.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries pasted evidence with `Result: pass`. The move is ALWAYS made by `aw ipd finalize`, never a hand edit plus `git mv` and never `aw ipd set executed`: under `aw oc run` / `aw agy run` follow the runner's lifecycle notice (self-finalize when it tells you to, otherwise the driver finalizes); when executing by hand, run `aw ipd finalize` yourself. Backlog item `1sn4h0` is set to `graduated` by the authoring runner, not by this plan's execution, and must not be set `done` here: `done` would claim the code is written, which only this plan's execution establishes.

- Size assessment: standard
- Cohesion rationale: not required
