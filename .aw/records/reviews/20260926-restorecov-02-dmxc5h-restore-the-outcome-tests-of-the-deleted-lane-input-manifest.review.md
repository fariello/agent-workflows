# Review: Restore the outcome tests of the deleted lane input manifest suite

- Subject-Id: dmxc5h
- Subject-Type: ipd
- Reviewed-At: 2026-09-26
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `d66ec740`. The target plan was committed and unchanged, so the pre-review
snapshot was correctly skipped per Step 1. Structural preflight `aw ipd lint --phase author` reported
`conforming` before review and `--phase review-finalize` reported `clean` with ZERO findings after the
revisions.

THE PLAN'S PREMISE AND ITS FOUR FINDINGS ALL HOLD. `19313eed` deleted
`tests/test_lane_input_manifest.py` at exactly 444 lines with exactly 21 test methods; the file does not
exist today; `lane_containment.verify_link_independence`, `verify_lane_input_seal` and
`attachments_outside_lane` all still exist and NO remaining test in the suite references any of them, so
the coverage gap is real and a regression in any of the three would indeed ship green. I recovered the
file, and it passes 21/21 in-repo under pytest (`21 passed in 0.89s`, 2.63s wall) and under unittest
(`Ran 21 tests ... OK`), confirming F-1 including the dual-runner claim. F-4 is correct and worth the
credit: `DriverArgvTests` really does contain only a docstring and no test methods, so the brief's
instruction to keep it named nothing. The 13/8 arithmetic is exact and every name in F-2 exists in the
file.

THE REVIEW TURNED ON TESTING THE ONE CLAIM THAT DECIDES THE DELIVERABLE: is each dropped test actually
redundant? The plan asserts three of them share "the same verifier refusal path as the kept wrong-digest
test". Reading `verify_lane_input_manifest` shows that is false on its face - it contains three SEPARATE
`if` branches appending three DIFFERENT violation strings (`mode ... is not 'copy'`, `records no source
digest`, `recorded digest ... does not match on-disk`) - so I did not stop at reading. I sabotaged
`lane_containment` one branch at a time, running the full 21-test file after each, and reverting between:

- disable the mode branch -> `1 failed, 20 passed`, failing only `test_an_unrecognized_mode_is_refused`;
- disable the `records no source digest` branch -> `1 failed, 20 passed`, failing only
  `test_a_missing_digest_is_caught`;
- make the absent-source `except OSError: continue` fabricate an empty payload -> `1 failed, 20 passed`,
  failing only `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one`;
- record `str(destination)` instead of `destination.relative_to(lane_root).as_posix()` -> `1 failed,
  20 passed`, failing only `test_materialized_paths_are_inside_the_lane_and_relative`.

FOUR OF THE EIGHT PROPOSED DROPS ARE THEREFORE THE ONLY TEST IN THE FILE THAT CATCHES THEIR DEFECT, and
in every case the 13 kept tests all passed while the defect was live. That is PR-801, and it inverts the
usual review finding: the plan is under-scoped by deleting too much, and executing it as written would
have turned a coverage restoration into a coverage reduction. The fourth is the sharpest case, because it
is not a verifier branch at all: no kept test anywhere asserts that a recorded manifest path is RELATIVE
and lane-contained, and the plan's stated justification for dropping it (that the attachment-containment
tests subsume it) confuses two different functions - those tests exercise `attachments_outside_lane` on a
constructed argv, which never looks at manifest entries.

I ALSO CHECKED THE DROPS THE PLAN GOT RIGHT, because a finding that only reports errors is not a review.
The write-bit pair IS safely droppable: I sabotaged `SEALED_FILE_MODE` from `0o444` to `0o644` and the
kept `test_an_accidental_in_place_write_fails` failed alongside them, so the consequence genuinely
survives, exactly as the plan argued. `test_restored_copy_passes_again` calls `self.test_hard_link_is_caught()`
as its first statement, which is a real defect and a fair deletion. And `DriverArgvTests` is empty. So
four of the eight deletions stand on the plan's own reasoning, which is why the revision keeps 17 rather
than restoring all 21.

PR-802 is the subtlest finding. `test_its_docstring_states_it_has_no_consumer` asserts `"no product
caller" in revise_lane_inputs.__doc__`, which IS a wording pin and correctly fails the maintainer's
outcomes-only rule, so the plan's instinct to remove it is right. But it is the only check of a LIVE spec
obligation: approved spec `7ckptx` R3.4 states "a plan that implements it MUST state that it has no
consumer rather than implying one", and the docstring currently satisfies it verbatim. Deleting the test
with no replacement silently retires the requirement's only guard. The fix is neither to keep the pin nor
to drop the requirement but to assert the OUTCOME underneath it - that no production caller exists - which
I confirmed is true today and therefore testable. E-02 now does that, with an explicit fallback to retain
the pin and report if the replacement proves harder than it looks, because an ugly test of a live
obligation beats no test.

PR-804 is the same defect I found in sibling plan `6vozur`, and I checked for it here deliberately. A
green bare suite does not prove a restored file is collected: pytest's default `python_files` is
`test_*.py` with no override in `pyproject.toml`, so a mistyped name contributes zero tests while the
summary stays green. Measured here: baseline `2436 passed, 1 skipped in 41.39s`; with the full 21-test
file, `2457 passed, 1 skipped in 45.75s`, i.e. exactly +21. E-04 now requires that delta.

PR-803 and PR-805 are smaller. The plan's single sabotage covered link independence only, leaving the
other five guarantees unproven against vacuity, so E-05 is now one sabotage per distinct guarantee - and
four of those six exist precisely to demonstrate that the reinstated tests bite. I verified the plan's
own proposed sabotage works as specified: disabling both inode checks while leaving the symlink check
intact gives `1 failed, 1 passed`, with `test_hard_link_is_caught` failing on
`assertFalse(result.independent)` and `test_symlink_is_caught` still passing, which is exactly what E-05(a)
predicts. And the plan's `/tmp` prohibition was unfalsifiable as written ("triage reported a hang") with
no mechanism, which invites an executor to ignore it; I found a plausible in-repo cause worth naming -
the root `conftest.py` calls `_ensure_xdist_then_reexec()` at import, which can `pip install
pytest-xdist` and then `os.execv` the interpreter.

Two things I confirmed correct and recorded so they are not re-derived. The file needs no execution-role
declaration and no `slow` marker: it is plain `unittest.TestCase` with `TemporaryDirectory`, spawns no
subprocess, and touches no lifecycle wrapper - which is the substantive difference from sibling plan
`6vozur`, where the same marker question went the other way. And `lane_containment._sha256_file` is
indeed used to compute an expected digest, which is an outcome value rather than a source pin. The plan
carries `- Work-Kind: followup` with no `- Blocks-Release:`, correct since the gating set is `bug` alone.

I left `agent_workflows/lane_containment.py` byte-unchanged: every sabotage was reverted with
`git checkout` and the final `git status` shows no modification to it.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-801 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing | `verify_lane_input_manifest` holds three separate branches emitting `mode ... is not 'copy'`, `records no source digest`, and `recorded digest ... does not match on-disk`. Per-branch sabotage over the full recovered file: mode branch -> `1 failed, 20 passed` (`test_an_unrecognized_mode_is_refused`); missing-digest branch -> `1 failed, 20 passed` (`test_a_missing_digest_is_caught`); absent-source `except OSError` fabricating a payload -> `1 failed, 20 passed` (`test_an_absent_source_records_no_entry...`); recorded path made absolute -> `1 failed, 20 passed` (`test_materialized_paths_are_inside_the_lane_and_relative`). The 13 kept tests passed in every case | FOUR OF THE EIGHT PROPOSED DROPS ARE EACH THE ONLY TEST THAT CATCHES THEIR DEFECT, so executing the trim as written would REDUCE coverage in a plan whose stated purpose is restoring it. The justification "same verifier refusal path as the kept wrong-digest test" is false: those are three independent branches with three distinct violations. The path-shape drop is worse than redundant-by-mistake - it is the only assertion anywhere that a recorded manifest path is relative and lane-contained, and the tests said to subsume it exercise a DIFFERENT function (`attachments_outside_lane` on a constructed argv, which never reads manifest entries). | C:Low; U:Low; S:Low; F:High if unfixed (four guarantees silently unguarded); Overall:Low (the fix is to delete less) | FIXED | E-01 now deletes only the four proven-safe drops and explicitly KEEPS the four reinstated ones; count is 17 not 13. Added F-5 with the per-test sabotage evidence. E-05 requires each of the four to be shown load-bearing by its own sabotage, so the reinstatement is verified rather than asserted. OQ-01 revised, recording the original rationale as wrong on its facts and why a count target may not be met by deleting a behavior's only guard. Scope, Scope check, and the gate all updated to 17 with the change flagged for the approving human. |
| PR-802 | MEDIUM | UNDER-SCOPE | D. Anti-regression / F. Honest documentation | Spec `7ckptx` R3.4: "a plan that implements it MUST state that it has no consumer rather than implying one"; `revise_lane_inputs.__doc__` contains "NO PRODUCT CALLER, AND THAT IS STATED RATHER THAN IMPLIED, because spec R3.4 requires it" (1031 chars, verified via `__doc__` at runtime); `rg` over `agent_workflows/` finds no call site for `revise_lane_inputs` outside its own definition and prose | DROPPING THE DOCSTRING PIN RETIRES THE ONLY GUARD OF A LIVE SPEC OBLIGATION. The plan is right that it is a wording pin failing the outcomes-only rule, and wrong that the answer is deletion: R3.4 is a current requirement of an APPROVED spec, and after the drop nothing would notice if the statement vanished or a caller appeared. The correct move is to convert the pin to the outcome it stands for (no production caller exists), which is both testable today and robust to any rewording. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-02 replacing the pin with an outcome test asserting zero production call sites, carrying an explicit fallback (retain the pin with a comment and report) so the requirement is never left unguarded. Added V-02 requiring the new test's source, a passing run, the call-site derivation, and `grep __doc__` returning nothing. Added F-6 and OQ-02 recording feasibility from evidence. E-01 now points at E-02 rather than simply deleting the class. |
| PR-803 | MEDIUM | UNDER-SCOPE | E. Testing and verification | Plan E-03 as authored: one sabotage, of `verify_link_independence` only. Review verified that sabotage behaves as specified (both inode checks disabled, symlink check intact -> `1 failed, 1 passed`, `test_hard_link_is_caught` failing on `assertFalse(result.independent)`), and additionally sabotaged five other guarantees, each failing a different single test | ONE SABOTAGE PROVED ONE GUARANTEE AND LEFT FIVE UNTESTED FOR VACUITY. The plan's own framing is that the restored tests must "fail if lane input materialization stops catching link smuggling, digest tampering, in-place edits, or out-of-lane attachments" - four guarantees, of which the single sabotage covers one. Without per-guarantee sabotage, a test that passes for the wrong reason is indistinguishable from one that bites, and this file's whole value is that it bites. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 replaces the single sabotage with six, one per distinct guarantee, each requiring the named test to fail on its OWN assertion (not an import error) and to be reverted before the next. Four of the six double as the PR-801 reinstatement proof. V-05 requires the diff, failing output and post-revert pass for each, plus `git diff --stat agent_workflows/` empty. A stop condition covers a sabotage that fails to make its test fail. |
| PR-804 | MEDIUM | UNDER-SCOPE | E. Testing and verification | Baseline bare suite `2436 passed, 1 skipped, 3 warnings in 41.39s`; with the full 21-test file restored `2457 passed, 1 skipped, 3 warnings in 45.75s` (+21). pytest default `python_files = test_*.py`; `pyproject.toml` sets no override. Same defect measured in sibling plan `6vozur`, where a non-conforming filename left 6 tests uncollected with the suite green and unchanged | THE PLAN'S SUCCESS CRITERIA CANNOT DISTINGUISH A COLLECTED FILE FROM AN UNCOLLECTED ONE. E-02's "13 passed" comes from a directly-named run, which collects the file regardless of the default pattern, and E-03's "bare suite green" is true when the count never moved. For a plan whose deliverable is regained coverage, the criterion must be a test COUNT. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added E-04 requiring the bare-suite total before and after with the arithmetic shown and a delta equal to the kept count, plus a `--collect-only` check; added V-04 stating a green summary does not satisfy it; added F-7; the honesty rule and a stop condition both name the false pass. |
| PR-805 | LOW | IN-SCOPE | G. Plan executability | Plan E-02: "Do NOT run it under pytest from `/tmp` (triage reported a hang there from rootdir/conftest interplay)". `conftest.py` calls `_ensure_xdist_then_reexec()` at module level; its body runs `subprocess.run([sys.executable, "-m", "pip", "install", "pytest-xdist>=3"])` and then `os.execv(sys.executable, ...)`, guarded only by an `AW_XDIST_BOOTSTRAP` env flag | A PROHIBITION WITH NO NAMED MECHANISM IS UNFALSIFIABLE AND EASY TO DISREGARD. An executor told only that "triage reported a hang" cannot tell whether the constraint still applies, and the natural response to an unexplained ban is to test it. A plausible in-repo cause exists and naming it makes the instruction checkable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names the `_ensure_xdist_then_reexec` pip-install-and-`os.execv` mechanism as the plausible cause and states that the in-repo run is the one that matters regardless, so the constraint is justified rather than asserted. Added F-8. |
| PR-806 | LOW | UNDER-SCOPE | G. Plan executability (execution contract) | Plan gate as authored: `- Cohesion rationale: not required`; one stop condition; "13 outcome tests" in the what-a-human-is-approving paragraph; Scope said OUT "any change to `lane_containment`" while E-03 requires a temporary sabotage of it | THE GATE MISSTATED WHAT IS BEING APPROVED AND CONTRADICTED ITSELF ON SCOPE. After PR-801 the count is 17, not 13, and the approving human needs to see that review changed it and why. The Scope line also flatly forbade changing `lane_containment` while an execution item requires sabotaging it, which an executor could read as a conflict; the distinction is PERMANENT versus temporary-and-reverted. No cohesion rationale despite the item count growing, and no stop conditions for the new failure modes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate gained a cohesion rationale, a corrected count (17), and a WHAT REVIEW CHANGED paragraph naming the four reinstated guarantees and inviting the human to overrule at approval; Scope OUT now reads "any PERMANENT change to `lane_containment`" with the sabotage carve-out stated; the honesty rule names the collection false pass; four stop conditions replace the one. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan classifies 8 tests as droppable, 3 of them as sharing a verifier path. Accept the classification, or test it? | Test it, by sabotaging each verifier branch and behavior in turn and observing which test fails. | (a) Accept the plan's audit - rejected: the "same verifier refusal path" claim is contradicted by reading the verifier, which has three separate branches with three distinct violation strings, so the audit's central justification was already suspect. (b) Read the method bodies and reason, as the plan's F-3 did ("method bodies" is its whole evidence column) - rejected: reading tells you what a test asserts, not whether anything else asserts it too, and the question here is uniqueness of coverage. (c) Keep all 21 to be safe - rejected: it ignores the maintainer's explicit "keep the count small" rule and would retain a docstring pin, an empty class, and a test that calls another test. | Six sabotage runs over the full recovered file, each reverted: four produced `1 failed, 20 passed` naming a DROPPED test; the `SEALED_FILE_MODE` sabotage produced a failure in the KEPT `test_an_accidental_in_place_write_fails` alongside the write-bit pair, confirming that drop safe | yes |
| D-2 | The R3.4 docstring pin fails the outcomes-only rule but guards a live spec requirement. Drop it, keep it, or replace it? | Replace it with an outcome test asserting `revise_lane_inputs` has no production caller, with a fallback to retain the pin and report if that proves infeasible. | (a) Drop it as the plan says - rejected: spec `7ckptx` R3.4 is a current requirement of an APPROVED spec and this is its only guard, so dropping it retires the requirement silently. (b) Keep the pin as-is - rejected: it is a wording assertion and the maintainer's rule against those is explicit, and it would break on any harmless rewording. (c) Amend the spec to drop R3.4's statement obligation - rejected outright: this is a test-only restoration with no spec-edit mandate, and weakening an approved contract to avoid writing a test is backwards. | Spec `7ckptx` R3.4 text; `revise_lane_inputs.__doc__` verified at runtime to contain the required statement; no call site for `revise_lane_inputs` anywhere in `agent_workflows/` outside its definition and prose, so the outcome form passes today | yes |
| D-3 | Should review re-decide the final kept count itself, or hand the 13-versus-17 question to the human? | Set it to 17 in the plan on the measured evidence, and flag the change prominently in the gate for the human to overrule. | (a) Leave it at 13 and raise a finding - rejected: that leaves an approved plan whose execution provably loses coverage, and the fix (delete less) is Low risk and fully determined by the measurement. (b) Ask the maintainer before revising - rejected: the repository answered it. The maintainer's rule is "keep the count small", not "reach 13", and four deletions still satisfy it; the measurement decides which four. (c) Restore all 21 - rejected as above. | The four sabotage results; the maintainer's rule as recorded in the plan's own conventions section; the plan's stated goal that the suite "fails if lane input materialization stops catching" each named defect | yes |
