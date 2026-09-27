# IPD: Restore the outcome tests of the deleted lane input manifest suite

- Date: 2026-09-26
- Kind: child
- Concern: The suite trim `19313eed` deleted `tests/test_lane_input_manifest.py` (444 lines, 21 test methods), the acceptance coverage for spec `7ckptx` R5.1-R5.3: lane inputs arrive by copy with a digest manifest, copies are link-independent (hard links and symlinks caught), inputs are sealed read-only with changes as new revisions, and every `--file` attachment resolves inside the lane. No remaining test covers `lane_containment.verify_link_independence`, `verify_lane_input_seal` or `attachments_outside_lane`, so a regression in any of them would ship green. Recovered at HEAD `61ef21d8`, the file passes 21/21 in-repo.
- Scope: IN: restore a SUBSET of the recovered file as `tests/test_lane_input_manifest.py`: the outcome tests that each prove a distinct refusal or guarantee; drop the empty class, the write-bit mode-bit pair whose consequence a kept test proves, and the round-trip test that calls another test method; REPLACE the R3.4 docstring pin with an outcome-form test rather than dropping the requirement it guards (review PR-802); and PROVE collection by the bare-suite test count (review PR-804). Review reinstated four tests the plan had classed as redundant, having measured each to be the only test that catches its defect (review PR-801/F-5). OUT: any PERMANENT change to `lane_containment` (E-05's sabotages are temporary, reverted, and never committed).
- Scope-Paths: tests/test_lane_input_manifest.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: mvw06u
- Set: restorecov
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: dmxc5h
- Approval: 2026-09-26, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-26 approved (aw set): status set to approved
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-806 all FIXED. The plan's premise and all four of its findings hold (the coverage gap is real; the recovered file passes 21/21 under both runners; `DriverArgvTests` is genuinely empty). THE FINDING THAT MATTERS INVERTS THE USUAL DIRECTION: the plan deletes too MUCH. Sabotaging `lane_containment` one branch at a time showed FOUR of its eight proposed drops are each the ONLY test in the file that catches their defect (`test_an_unrecognized_mode_is_refused`, `test_a_missing_digest_is_caught`, `test_an_absent_source_records_no_entry...`, `test_materialized_paths_are_inside_the_lane_and_relative`), each giving `1 failed, 20 passed` while every kept test passed; the "same verifier refusal path" justification is false, since that verifier has three independent branches with three distinct violation strings. Kept count is now 17, not 13, and E-05 requires each reinstatement be proven load-bearing. Also: the R3.4 docstring pin is REPLACED by an outcome test rather than dropped, because approved spec `7ckptx` R3.4 still requires the statement and this was its only guard (E-02); collection is now proven by test COUNT, not a green summary (E-04, the same defect found in sibling plan `6vozur`). The drops the plan got RIGHT were verified too: sabotaging `SEALED_FILE_MODE` to `0o644` failed the kept `test_an_accidental_in_place_write_fails`, so the write-bit pair is safely droppable. 3 items -> 6 with a 6:6 E/V bijection. `agent_workflows/lane_containment.py` left byte-unchanged. Baseline for the executor: `2436 passed, 1 skipped in 41.39s`; with the full 21-test file, `2457 passed`. Review record: `.aw/records/reviews/20260926-restorecov-02-dmxc5h-restore-the-outcome-tests-of-the-deleted-lane-input-manifest.review.md`.
- 2026-09-26 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-801..PR-806 all FIXED. Sabotage measurement found 4 of the 8 proposed drops are each the ONLY test catching their defect, so the kept count is 17 not 13; the R3.4 docstring pin is replaced rather than dropped. 3 items -> 6.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mvw06u: restore 13 outcome tests of the deleted lane input manifest suite, dropping the docstring pin, an empty class, and seven redundant tests.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A small outcome-only suite fails if lane input materialization stops catching link smuggling, digest tampering, in-place edits, or out-of-lane attachments.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the subset and verify

- [x] E-01 Write `git show 19313eed^:tests/test_lane_input_manifest.py` to `tests/test_lane_input_manifest.py`, then DELETE ONLY the four the review PROVED are not load-bearing (PR-801): the class `RevisionMechanismHasNoProductCallerTests` (see E-02, which reinstates its coverage in a non-pinning form rather than simply dropping it); the class `DriverArgvTests` (it has a docstring and NO test methods); `test_part_i_the_manifest_file_has_no_write_bit` and `test_part_ii_every_materialized_input_has_no_write_bit` (mode-bit inspection whose consequence the kept `test_an_accidental_in_place_write_fails` proves - review sabotaged `SEALED_FILE_MODE` to `0o644` and the kept test failed alongside them, so the coverage genuinely survives); and `test_restored_copy_passes_again` (it calls another test method as its first statement, which is the real defect; the round trip adds little). KEEP the four the plan originally dropped as "redundant": review measured each to be the ONLY test in the file that catches its defect, so dropping them silently loses coverage this plan exists to restore (F-5, per-test sabotage evidence in the table). Update the module docstring: state that this is a trimmed restoration of the `19313eed` deletion (plan dmxc5h) keeping outcome tests only, and record WHY each of the four deletions is safe, citing the sabotage result for the write-bit pair. Keep its bullet about R5.3 being "asserted over EVERY `--file` value in the constructed argv" (it still describes `test_both_attachments_are_localized`).
  - Depends on: none
  - Expected outcome: 17 test methods remain (the 13 in F-2 plus the four reinstated by F-5), plus whatever E-02 adds; `DriverArgvTests` and `RevisionMechanismHasNoProductCallerTests` gone.
  - Execution state: performed

- [x] E-02 REPLACE THE R3.4 DOCSTRING PIN RATHER THAN DROPPING ITS COVERAGE (PR-802). The deleted test asserted `"no product caller" in lane_containment.revise_lane_inputs.__doc__`, which IS a wording pin and correctly fails the maintainer's outcomes-only rule. But it is the ONLY check of a live spec obligation: approved spec `7ckptx` R3.4 states "a plan that implements it MUST state that it has no consumer rather than implying one", and `revise_lane_inputs`'s docstring currently satisfies it ("NO PRODUCT CALLER, AND THAT IS STATED RATHER THAN IMPLIED, because spec R3.4 requires it"). Dropping the test with no replacement leaves that requirement unchecked. Write instead the OUTCOME the requirement is really about: assert that `revise_lane_inputs` has NO production caller, by grepping the `agent_workflows/` package for call sites and asserting the set is empty (excluding its own definition and comments). That is a fact about the code, not about wording, so it survives any rewording of the docstring while still failing the moment someone wires up a caller - which is the condition R3.4 cares about. If that proves infeasible in one focused pass, STOP and report rather than silently dropping the requirement: say so, and leave the original pinning test in place with a comment naming it as a known wording pin, because an ugly test of a live spec obligation beats no test.
  - Depends on: E-01
  - Expected outcome: one test asserting `revise_lane_inputs` has zero production call sites, passing today (review confirmed the only matches in `agent_workflows/` are its own definition and prose); or an explicit report that it was infeasible, with the pin retained.
  - Execution state: performed

- [x] E-03 Run the file IN-REPO under both runners: `python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""` (report wall time with `time`) and `python3 -m unittest tests.test_lane_input_manifest`. Do NOT run it under pytest from a directory outside this checkout: the root `conftest.py` runs `_ensure_xdist_then_reexec()` at import, which can `pip install pytest-xdist` and then `os.execv` the interpreter, so an out-of-tree rootdir has a plausible mechanism for the hang triage reported, and the in-repo run is the one that matters anyway. If the pytest run takes more than 30s, stop and report rather than marking `slow`.
  - Depends on: E-02
  - Expected outcome: the same count under each runner (17 plus whatever E-02 added), well under 5s (review measured the FULL 21-test file at 0.84-0.89s under pytest and 1.99s under unittest).
  - Execution state: performed

- [x] E-04 PROVE THE FILE IS COLLECTED BY THE BARE SUITE, by test COUNT and not by a green summary (PR-804, the same defect found in sibling plan `6vozur`). Paste the bare `python3 -m pytest` total BEFORE the file exists and AFTER, and show the delta equals the number of tests kept. This matters because pytest's default `python_files` is `test_*.py` with no override in `pyproject.toml`, so a mistyped filename contributes ZERO tests while the suite still reports fully green - and this plan's entire deliverable is regained coverage. Review measured the baseline at `2436 passed, 1 skipped in 41.39s` and, with the full 21-test file restored, `2457 passed, 1 skipped in 45.75s` (+21 exactly); re-derive both at the executing HEAD rather than reusing those numbers.
  - Depends on: E-03
  - Expected outcome: the bare-suite delta equals the kept test count exactly; a green summary with an unchanged total is a FAILED restoration.
  - Execution state: performed

- [x] E-05 Show the kept tests are not vacuous, ONE SABOTAGE PER DISTINCT GUARANTEE rather than one for the whole file (PR-803). For each, sabotage in the worktree, paste the named test FAILING on its own assertion (not an import error), and restore before the next: (a) LINK INDEPENDENCE - disable the `st_nlink != 1` branch AND the `(st_dev, st_ino)` comparison in `lane_containment.verify_link_independence`, leaving the symlink check intact, and show `test_hard_link_is_caught` failing on `assertFalse(result.independent)` while `test_symlink_is_caught` still passes (review measured exactly this: `1 failed, 1 passed`); (b) DIGEST MISMATCH - for `test_a_wrong_recorded_digest_is_caught`; (c) MISSING DIGEST - disable the `records no source digest` branch, for `test_a_missing_digest_is_caught`; (d) MODE - disable the `is not 'copy'` branch, for `test_an_unrecognized_mode_is_refused`; (e) FABRICATED ENTRY - make the absent-source `except OSError: continue` fabricate an empty payload, for `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one`; (f) RECORDED PATH SHAPE - record `str(destination)` instead of `destination.relative_to(lane_root).as_posix()`, for `test_materialized_paths_are_inside_the_lane_and_relative`. Each of (c) to (f) must show `1 failed` with THAT test named, which is what proves the four reinstated tests are load-bearing. Revert every sabotage; commit none of them.
  - Depends on: E-04
  - Expected outcome: six sabotages, each failing exactly the named test on its own assertion; the file fully passing after every revert; `git status` showing no change to `agent_workflows/lane_containment.py`.
  - Execution state: performed

- [x] E-06 Run the bare suite and confirm a clean tree.
  - Depends on: E-05
  - Expected outcome: bare suite green with the E-04 count; `git diff --stat agent_workflows/` empty.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Maintainer decision 2026-09-26: restore IFF the restored tests check OUTCOMES only; drop any test pinning source text, docstrings, or "code has not changed"; keep the count small.
- The file is plain `unittest.TestCase` with `TemporaryDirectory`, no subprocess, no lifecycle wrapper, so it needs no execution-role declaration and no `slow` marker.
- Private helper `lane_containment._sha256_file` is used by two kept tests to compute an expected digest; that computes an outcome value, it does not pin source.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8` on the file recovered from `19313eed^`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | coverage | The recovered file passes in-repo under both runners. | copied into `tests/`: pytest `21 passed in 1.80s` (2.88s wall); `python3 -m unittest` -> `OK` |
| F-2 | INFO | kept (13) | `test_every_entry_is_a_copy_with_a_matching_digest`, `test_a_wrong_recorded_digest_is_caught`, `test_no_manifest_is_not_silently_conforming`, `test_a_fresh_copy_is_link_independent`, `test_hard_link_is_caught`, `test_symlink_is_caught`, `test_an_accidental_in_place_write_fails`, `test_part_iii_a_change_is_a_new_revision_not_an_edit`, `test_a_restored_write_bit_is_detected`, `test_both_attachments_are_localized`, `test_an_out_of_lane_attachment_is_detected`, `test_a_non_isolated_turn_is_untouched`, `test_traversal_cannot_masquerade_as_contained`. Each asserts a verifier verdict, a raised error, or returned paths. | method bodies |
| F-3 | INFO | dropped (8 methods + 1 empty class) | Docstring pin (1); redundant with a kept test (7, reasons in E-01); `DriverArgvTests` is empty. | method bodies |
| F-4 | LOW | brief correction | The brief listed "driver argv" among tests to keep, but `DriverArgvTests` in the recovered file contains NO test methods (only a docstring), so there is nothing to keep; argv localization is covered by `test_both_attachments_are_localized` on a constructed argv. | `sed -n '/class DriverArgvTests/,$p'` of the recovered file |
| F-5 | HIGH | four of the eight proposed drops (review PR-801) | FOUR "REDUNDANT" TESTS ARE EACH THE ONLY TEST THAT CATCHES THEIR DEFECT, so dropping them loses exactly the coverage this plan exists to restore. The claim that three of them share "the same verifier refusal path as the kept wrong-digest test" is false on inspection: `verify_lane_input_manifest` contains three SEPARATE `if` branches appending three DIFFERENT violation strings (`is not 'copy'`, `records no source digest`, `does not match on-disk`), and the fourth drop is the only assertion anywhere that a recorded manifest path is RELATIVE and lane-contained. Review proved each by sabotage, one branch at a time. | Per-test sabotage of `lane_containment`, each run over the full recovered file: disable the mode branch -> `1 failed, 20 passed` naming `test_an_unrecognized_mode_is_refused`; disable the `records no source digest` branch -> `1 failed, 20 passed` naming `test_a_missing_digest_is_caught`; make the absent-source `except OSError` fabricate an empty payload -> `1 failed, 20 passed` naming `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one`; record `str(destination)` instead of the lane-relative posix path -> `1 failed, 20 passed` naming `test_materialized_paths_are_inside_the_lane_and_relative`. In every case the kept tests all passed. |
| F-6 | MED | the R3.4 docstring pin (review PR-802) | THE DROPPED DOCSTRING PIN IS THE ONLY CHECK OF A LIVE SPEC OBLIGATION, so dropping it with no replacement removes coverage rather than noise. It IS a wording pin and correctly fails the outcomes-only rule, but approved spec `7ckptx` R3.4 says in terms: "a plan that implements it MUST state that it has no consumer rather than implying one", and the docstring currently satisfies it. The right move is to replace the pin with the OUTCOME (no production caller exists), not to delete the requirement's only guard. Hence E-02. | Spec `7ckptx`, R3.4 paragraph ("R3.4 WITHDRAWN by R3.3a ... MUST state that it has no consumer rather than implying one"); `lane_containment.revise_lane_inputs.__doc__` contains "NO PRODUCT CALLER, AND THAT IS STATED RATHER THAN IMPLIED, because spec R3.4 requires it"; `rg` over `agent_workflows/` finds no call site for `revise_lane_inputs` outside its own definition and prose, so the outcome form is satisfiable today. |
| F-7 | MED | collection, not correctness (review PR-804) | A GREEN SUITE IS NOT EVIDENCE THE RESTORED TESTS RUN. pytest's default `python_files` is `test_*.py` and `pyproject.toml` sets no override, so a mistyped filename contributes ZERO tests while the bare suite still reports fully green. The same defect was measured in sibling plan `6vozur`, where a non-conforming probe name left 6 restored tests silently uncollected with the suite unchanged and green. Hence E-04's count-based criterion. | Review measured the bare suite at `2436 passed, 1 skipped in 41.39s` without the file and `2457 passed, 1 skipped in 45.75s` with the full 21-test file (+21 exactly). |
| F-8 | LOW | E-02's `/tmp` prohibition, mechanism identified (review PR-805) | The plan forbade running the file under pytest from `/tmp` citing a triage-reported hang but named no cause, which makes the instruction unfalsifiable and easy for an executor to disregard. A plausible mechanism exists in-repo and is worth naming: the root `conftest.py` calls `_ensure_xdist_then_reexec()` AT IMPORT, which on a missing `xdist` runs `pip install pytest-xdist>=3` as a subprocess and then `os.execv`s the interpreter. An out-of-tree rootdir changes which conftest is loaded and whether that bootstrap fires. | `conftest.py`: `_ensure_xdist_then_reexec()` invoked at module level; its body runs `subprocess.run([sys.executable, "-m", "pip", "install", "pytest-xdist>=3"])` then `os.execv(...)`, guarded only by `AW_XDIST_BOOTSTRAP`. |

## Proposed changes (ordered, validatable)

1. E-01: restore, deleting only the four drops proven safe (17 tests kept, not 13).
2. E-02: replace the R3.4 docstring pin with an outcome test rather than dropping the requirement.
3. E-03: both runners in-repo, timed, counts agreeing.
4. E-04: prove collection by test COUNT.
5. E-05: six per-guarantee sabotages, four of which prove the reinstated tests load-bearing.
6. E-06: bare suite and a clean tree.

## Deferred / out of scope (with reason)

- A test of the argv the oc driver actually constructs (the intent of the empty `DriverArgvTests`): it never existed in the deleted file, so it is not a restoration.
  - Carrier-Declined: not lost coverage; nothing to restore.

## Scope check

- Over-scope: none.
- Under-scope: closed by review, and the correction went the OTHER way from the usual. The plan was UNDER-scoped by dropping too much: four of its eight proposed deletions were each the only test catching their defect (F-5, proven by per-test sabotage), so the trim would have removed live coverage in a plan whose purpose is restoring coverage. The count is therefore 17 kept, not 13. Two further gaps are now items: the R3.4 docstring pin is replaced with an outcome test rather than deleted (F-6), and collection is proven by test count rather than by a green summary (F-7). The maintainer's "keep the count small" rule is still honored - four deletions stand, and the pin is removed as a pin - but it is applied where it costs nothing rather than where it costs a guard.

## Required tests / validation

- The restored file under pytest AND unittest, in-repo, timed, with the two counts agreeing.
- The bare suite judged by COUNT: the total must move by exactly the kept test count. A green summary with an unchanged total is a FAILED restoration (F-7).
- Six per-guarantee sabotage runs (E-05), of which four exist specifically to prove the reinstated tests are load-bearing; every sabotage reverted and none committed.
- Test rule: outcomes only. The one wording pin is REPLACED by an outcome test (E-02), not silently dropped, because it guards a live spec requirement (F-6).

## Spec / documentation sync

N/A: test-only restoration of coverage for spec `7ckptx` R5, whose text is unchanged.

## Open questions

### OQ-01: Keep all 20 outcome tests instead of 13?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REVISED BY REVIEW to 17, not 13, and the original rationale is recorded as wrong on its facts. It claimed "every dropped method either shares a verifier path with a kept one or inspects a mechanism (mode bits) whose consequence a kept test proves". The second half is true and holds (the write-bit pair). The first half is false: `verify_lane_input_manifest` has three SEPARATE branches emitting three DIFFERENT violations, and review sabotaged each in turn, with only the dropped test failing each time. The same applies to the absent-source and recorded-path-shape drops. So the four are reinstated on measurement (F-5). The maintainer's "keep the count small" is still honored - four deletions stand and the wording pin is removed as a pin - but a count target may not be met by deleting the only guard of a behavior, since that converts a coverage restoration into a coverage reduction. The closing sentence of the original rationale ("a reviewer can restore any dropped method by name") is also recorded as a weak defense: it makes the loss recoverable, not harmless, and nothing would signal that a restore was needed.

### OQ-02: Is the outcome-form replacement for the R3.4 pin actually achievable?

- Blocking: no
- Status: resolved
- Owner: review (see review record `dmxc5h` D-2)
- Resolution or deferral rationale: Yes, from repository evidence. Spec `7ckptx` R3.4 requires the revision mechanism to STATE it has no consumer; the behavioral fact underneath is that no production caller exists, and review confirmed by search that `revise_lane_inputs` has no call site anywhere in `agent_workflows/` outside its own definition and explanatory prose. A test asserting that emptiness is an outcome test, survives any rewording, and fails precisely when someone wires up a caller - which is the condition the requirement protects. E-02 carries an explicit fallback (retain the pin, comment it, and report) so the requirement is never left unguarded if the replacement proves harder than it looks; that fallback is deliberate, because an ugly test of a live obligation beats no test.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `grep -n "    def test_" tests/test_lane_input_manifest.py` showing the kept names, and confirm the list CONTAINS all four reinstated by F-5 (`test_materialized_paths_are_inside_the_lane_and_relative`, `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one`, `test_a_missing_digest_is_caught`, `test_an_unrecognized_mode_is_refused`). Paste `grep -n "DriverArgvTests\|RevisionMechanism" tests/test_lane_input_manifest.py` returning nothing, and the module-docstring lines recording why each of the four deletions is safe.
  - Observed evidence: Verified. Kept names listed, all 4 reinstated tests present, DriverArgvTests and RevisionMechanism absent, docstring safe-deletion rationale present:
    ```
    $ grep -n "    def test_" tests/test_lane_input_manifest.py
    81:    def test_every_entry_is_a_copy_with_a_matching_digest(self):
    121:    def test_materialized_paths_are_inside_the_lane_and_relative(self):
    129:    def test_an_absent_source_records_no_entry_rather_than_a_fabricated_one(self):
    140:    def test_a_wrong_recorded_digest_is_caught(self):
    159:    def test_a_missing_digest_is_caught(self):
    172:    def test_an_unrecognized_mode_is_refused(self):
    184:    def test_no_manifest_is_not_silently_conforming(self):
    207:    def test_a_fresh_copy_is_link_independent(self):
    225:    def test_hard_link_is_caught(self):
    258:    def test_symlink_is_caught(self):
    287:    def test_an_accidental_in_place_write_fails(self):
    295:    def test_part_iii_a_change_is_a_new_revision_not_an_edit(self):
    329:    def test_a_restored_write_bit_is_detected(self):
    342:    def test_revise_lane_inputs_has_no_production_caller(self):
    379:    def test_both_attachments_are_localized(self):
    408:    def test_an_out_of_lane_attachment_is_detected(self):
    423:    def test_a_non_isolated_turn_is_untouched(self):
    434:    def test_traversal_cannot_masquerade_as_contained(self):
    ```
    Confirmed: contains all four reinstated tests:
    - `test_materialized_paths_are_inside_the_lane_and_relative` (line 121)
    - `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one` (line 129)
    - `test_a_missing_digest_is_caught` (line 159)
    - `test_an_unrecognized_mode_is_refused` (line 172)

    `grep -n "DriverArgvTests\|RevisionMechanism" tests/test_lane_input_manifest.py` returns nothing (exit 1).

    Module-docstring lines recording why each of the four deletions is safe:
    ```
    Four deletions from the original 21-test file were verified safe:
      1. The revision-mechanism docstring-pin test class - replaced per PR-802 with an
         outcome test (`test_revise_lane_inputs_has_no_production_caller`) verifying zero
         production call sites exist in `agent_workflows/`, rather than pinning docstring wording.
      2. The driver argv test class - empty class with docstring and no test methods.
      3. `test_part_i_the_manifest_file_has_no_write_bit` and
         `test_part_ii_every_materialized_input_has_no_write_bit` - mode-bit inspection tests whose
         consequence is proven by the kept `test_an_accidental_in_place_write_fails` (sabotaging
         `SEALED_FILE_MODE` from `0o444` to `0o644` fails the kept test, confirming coverage survives).
      4. `test_restored_copy_passes_again` - defective round-trip test that called another test method
         (`test_hard_link_is_caught`) as its first statement.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new R3.4 test's source and a run showing it PASSES; paste the derivation showing `revise_lane_inputs` has no production call site (the command and its output); and paste `grep -n "__doc__" tests/test_lane_input_manifest.py` returning nothing, so the wording pin is genuinely gone rather than relocated. If E-02 reported the replacement infeasible, paste that report and the retained pin with its explanatory comment instead, and say so plainly here.
  - Observed evidence: Verified. New R3.4 test passes, git grep shows zero production callers in agent_workflows, __doc__ absent:
    Source of new R3.4 test:
    ```python
    class ProductionCallerTests(unittest.TestCase):
        """Spec `7ckptx` R3.4: the revision mechanism has no production consumer."""

        def test_revise_lane_inputs_has_no_production_caller(self):
            package_dir = Path(lane_containment.__file__).parent
            call_sites: list[str] = []
            for path in package_dir.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func = node.func
                        is_target = False
                        if isinstance(func, ast.Name) and func.id == "revise_lane_inputs":
                            is_target = True
                        elif (
                            isinstance(func, ast.Attribute)
                            and func.attr == "revise_lane_inputs"
                        ):
                            is_target = True
                        if is_target:
                            call_sites.append(f"{path.name}:{node.lineno}")
            self.assertEqual(call_sites, [])
    ```

    Run showing it passes:
    ```
    $ python3 -m unittest tests.test_lane_input_manifest.ProductionCallerTests.test_revise_lane_inputs_has_no_production_caller
    .
    ----------------------------------------------------------------------
    Ran 1 test in 2.026s

    OK
    ```

    Derivation showing revise_lane_inputs has no production call site:
    ```
    $ git grep -n "revise_lane_inputs" agent_workflows/
    agent_workflows/lane_containment.py:2449:    the old one stays exactly as it was written. See `revise_lane_inputs`.
    agent_workflows/lane_containment.py:2622:def revise_lane_inputs(
    agent_workflows/lane_containment.py:2764:    `revise_lane_inputs` writing a new `rev-<N>` directory and by `latest_lane_input_revision`
    ```

    Grep for `__doc__`:
    ```
    $ grep -n "__doc__" tests/test_lane_input_manifest.py
    (returns nothing, exit code 1)
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `time python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""` showing the kept count and the real time, and `python3 -m unittest tests.test_lane_input_manifest` showing `Ran <n> tests` and `OK`, with the two counts AGREEING.
  - Observed evidence: Verified. 18 tests under pytest in 3.18s, 18 tests under unittest in 4.36s, counts agreeing:
    ```
    $ time python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=498181859
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 18 items

    tests/test_lane_input_manifest.py ..................                     [100%]

    ============================== 18 passed in 3.18s ==============================

    real	0m3.668s
    user	0m3.355s
    sys	0m0.127s
    ```

    ```
    $ python3 -m unittest tests.test_lane_input_manifest
    ..................
    ----------------------------------------------------------------------
    Ran 18 tests in 4.360s

    OK
    ```
    Both runners report 18 tests passed, agreeing on 18 items.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` summary line from before the file exists and from after, with the arithmetic shown and the delta stated explicitly; it must equal the kept test count. Also paste `python3 -m pytest --collect-only -q tests/test_lane_input_manifest.py | tail -1`. A green summary alone does NOT satisfy this item.
  - Observed evidence: Verified. Bare suite moved from 2525 to 2543 (+18 tests), matching kept count exactly, collect-only reports 18:
    Summary line from before file exists:
    ```
    2525 passed, 2 skipped, 3 warnings in 84.43s (0:01:24)
    ```

    Summary line from after file exists:
    ```
    2543 passed, 2 skipped, 3 warnings in 39.84s
    ```

    Arithmetic:
      After:  2543 passed
      Before: 2525 passed
      Delta:  2543 - 2525 = +18 tests
    The delta equals the kept test count (18) exactly.

    ```
    $ python3 -m pytest --collect-only -q tests/test_lane_input_manifest.py
    tests/test_lane_input_manifest.py: 18
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: for EACH of the six sabotages (a) to (f), paste the sabotage diff, the failing output with the test name and the assertion it failed on, and the passing run after the revert. Cases (c) to (f) must each show `1 failed` naming the reinstated test, which is the evidence that reinstating it was correct. Finally paste `git diff --stat agent_workflows/` showing empty.
  - Observed evidence: Verified. Six distinct sabotages, each failing on its own assertion with (c)-(f) naming the reinstated tests, all reverted cleanly:
    (a) Link Independence:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2716,7 +2716,7 @@ def verify_link_independence(
             except OSError as exc:
                 violations.append(f"{rel}: cannot stat ({exc})")
                 continue
    -        if stat_result.st_nlink != 1:
    +        if False and stat_result.st_nlink != 1:
                 violations.append(
                     f"{rel}: st_nlink={stat_result.st_nlink} (expected 1); another name shares this "
                     "inode, so it is a hard link and not an independent copy"
    @@ -2728,7 +2728,7 @@ def verify_link_independence(
                     source_stat = os.stat(source, follow_symlinks=False)
                 except OSError:
                     source_stat = None
    -            if source_stat is not None and (
    +            if False and source_stat is not None and (
                     (stat_result.st_dev, stat_result.st_ino)
                     == (source_stat.st_dev, source_stat.st_ino)
                 ):
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -k "test_hard_link_is_caught or test_symlink_is_caught" -o addopts=""
    tests/test_lane_input_manifest.py .F                                     [100%]
    =================================== FAILURES ===================================
    ________________ LinkIndependenceTests.test_hard_link_is_caught ________________
    >       self.assertFalse(result.independent)
    E       AssertionError: True is not false
    FAILED tests/test_lane_input_manifest.py::LinkIndependenceTests::test_hard_link_is_caught
    ================== 1 failed, 1 passed, 16 deselected in 0.72s ==================
    ```
    Post-revert: 18 passed in 6.49s.

    (b) Digest Mismatch:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2860,7 +2860,7 @@ def verify_lane_input_manifest(
             except OSError as exc:
                 violations.append(f"{rel}: cannot read to digest ({exc})")
                 continue
    -        if actual != digest:
    +        if False and actual != digest:
                 violations.append(
                     f"{rel}: recorded digest {digest[:12]} does not match on-disk {actual[:12]}"
                 )
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    =================================== FAILURES ===================================
    _________ MaterializationTests.test_a_wrong_recorded_digest_is_caught __________
    >       self.assertFalse(verdict.conforming)
    E       AssertionError: True is not false
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_a_wrong_recorded_digest_is_caught
    ========================= 1 failed, 17 passed in 5.25s =========================
    ```
    Post-revert: 18 passed in 3.17s.

    (c) Missing Digest:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2851,7 +2851,7 @@ def verify_lane_input_manifest(
             if entry.get("input_class") not in _INPUT_CLASSES:
                 violations.append(f"{rel}: unrecognized class {entry.get('input_class')!r}")
             digest = entry.get("source_sha256") or ""
    -        if not digest:
    +        if False and not digest:
                 violations.append(f"{rel}: records no source digest")
                 continue
             target = lane_root / rel
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    =================================== FAILURES ===================================
    _____________ MaterializationTests.test_a_missing_digest_is_caught _____________
    >       self.assertTrue(
                any("records no source digest" in v for v in verdict.violations), verdict
            )
    E       AssertionError: False is not true : ManifestVerification(conforming=False, violations=('.aw/state/lane-inputs/rev-1/plan-plan.ipd.md: recorded digest  does not match on-disk 1c653131076f', 'manifest.json: mode 0644 carries a write bit'))
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_a_missing_digest_is_caught
    ========================= 1 failed, 17 passed in 2.91s =========================
    ```
    Post-revert: 18 passed in 6.52s.

    (d) Mode:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2844,7 +2844,7 @@ def verify_lane_input_manifest(
             violations.append("manifest lists no inputs")
         for entry in entries:
             rel = entry.get("path") or "<unnamed>"
    -        if entry.get("mode") != MATERIALIZATION_MODE_COPY:
    +        if False and entry.get("mode") != MATERIALIZATION_MODE_COPY:
                 violations.append(
                     f"{rel}: mode {entry.get('mode')!r} is not {MATERIALIZATION_MODE_COPY!r}"
                 )
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    =================================== FAILURES ===================================
    __________ MaterializationTests.test_an_unrecognized_mode_is_refused ___________
    >       self.assertTrue(any("is not 'copy'" in v for v in verdict.violations), verdict)
    E       AssertionError: False is not true : ManifestVerification(conforming=False, violations=('manifest.json: mode 0644 carries a write bit',))
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_an_unrecognized_mode_is_refused
    ========================= 1 failed, 17 passed in 3.09s =========================
    ```
    Post-revert: 18 passed in 4.74s.

    (e) Fabricated Entry:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2540,10 +2540,7 @@ def materialize_lane_inputs(
             try:
                 payload = source.read_bytes()
             except OSError:
    -            # Absent or unreadable: record NOTHING. The missing-input cycle (spec R3, child `y5od1h`)
    -            # owns reporting a genuinely required input that is not there; inventing a manifest entry
    -            # here would hide it behind a record that looks satisfied.
    -            continue
    +            payload = b""
             destination = root / f"{input_class}-{source.name}"
             if destination.exists():
                 _unseal_for_write(destination)
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    =================================== FAILURES ===================================
    _ MaterializationTests.test_an_absent_source_records_no_entry_rather_than_a_fabricated_one _
    >       self.assertIsNone(manifest.entry(lane_containment.INPUT_CLASS_RUNBOOK))
    E       AssertionError: MaterializedInput(...) is not None
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_an_absent_source_records_no_entry_rather_than_a_fabricated_one
    ========================= 1 failed, 17 passed in 2.95s =========================
    ```
    Post-revert: 18 passed in 2.89s.

    (f) Recorded Path Shape:
    Diff:
    ```diff
    --- a/agent_workflows/lane_containment.py
    +++ b/agent_workflows/lane_containment.py
    @@ -2559,7 +2559,7 @@ def materialize_lane_inputs(
                     )
             entries.append(
                 MaterializedInput(
    -                path=destination.relative_to(lane_root).as_posix(),
    +                path=str(destination),
                     input_class=input_class,
                     source_sha256=written_digest,
                     mode=MATERIALIZATION_MODE_COPY,
    ```
    Failing output:
    ```
    $ python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""
    =================================== FAILURES ===================================
    _ MaterializationTests.test_materialized_paths_are_inside_the_lane_and_relative _
    >               self.assertFalse(Path(entry.path).is_absolute())
    E               AssertionError: True is not false
    FAILED tests/test_lane_input_manifest.py::MaterializationTests::test_materialized_paths_are_inside_the_lane_and_relative
    ========================= 1 failed, 17 passed in 2.87s =========================
    ```
    Post-revert: 18 passed in 3.83s.

    All six sabotages reverted; confirmed clean:
    ```
    $ git diff --stat agent_workflows/
    (returns empty)
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary line of a BARE `python3 -m pytest` showing 0 failed with the expected total, and `git status --short` showing only `tests/test_lane_input_manifest.py`.
  - Observed evidence: Verified. Bare pytest passed with 2543 passed, 0 failed, git status clean with only tests/test_lane_input_manifest.py:
    Final summary line of BARE `python3 -m pytest`:
    ```
    2543 passed, 2 skipped, 3 warnings in 72.36s (0:01:12)
    ```

    Git status:
    ```
    $ git status --short
    ?? tests/test_lane_input_manifest.py
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: six items, one concern (restore one deleted test file so `lane_containment`'s three uncovered guarantees regain coverage). E-02 is separate because replacing a wording pin with an outcome test is a different deliverable from trimming; E-04 and E-05 are separate because one proves the file RUNS and the other proves its tests BITE, which are independent failure modes with independent evidence.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One restored test file with 17 outcome tests (about 1s under pytest, 2s under unittest), plus one replacement test for a spec requirement. No permanent production code change; E-05's sabotages are temporary and reverted. Deleted: one empty class, two mode-bit inspection tests whose consequence a kept test provably still catches, and one test that called another test method. The R3.4 docstring pin is REPLACED by an outcome test rather than dropped.

WHAT REVIEW CHANGED, because it moved the count the human was asked to approve. The plan proposed keeping 13 and dropping 8 as redundant. Review sabotaged `lane_containment` one branch at a time and found that FOUR of those 8 are each the ONLY test in the file that catches their defect (a manifest mode that is not `copy`; a manifest recording no digest at all; a fabricated entry for an absent source; a recorded path that is absolute rather than lane-relative). Dropping them would have reduced coverage in a plan whose purpose is restoring it, so they are reinstated and E-05 now requires each to be shown load-bearing by sabotage. The maintainer's "keep the count small" rule still governs; it is applied to the four deletions that cost nothing. A human who wants the count at 13 anyway should say so at approval, knowing those four guarantees then have no test.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. ONE CLAIM IS SPECIFICALLY NOT ACCEPTED AS GREEN-MEANS-DONE: a bare-suite summary with an UNCHANGED total does not demonstrate the restoration, because a mistyped filename is never collected and the suite stays green (F-7). E-04's delta is the evidence, not the word "green".

GENUINE STOP CONDITIONS, each needing a human rather than a local workaround:
- A kept test fails against today's `lane_containment`: do NOT edit it to pass; report it as a possible regression since `19313eed`.
- An E-05 sabotage does NOT make its named test fail: stop and report. That means the test is vacuous against the guarantee it claims to cover, which is worth knowing and must not be silently accepted just because the file is green.
- The bare-suite delta does not equal the kept test count: stop. Something is not being collected and a green summary will hide it.
- E-02's outcome-form replacement proves infeasible: do NOT simply delete the R3.4 test. Retain the pin with an explanatory comment and report, per E-02's stated fallback.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); the sabotage edit is reverted and not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `mvw06u` `done` with `--evidence` citing the executed plan.
