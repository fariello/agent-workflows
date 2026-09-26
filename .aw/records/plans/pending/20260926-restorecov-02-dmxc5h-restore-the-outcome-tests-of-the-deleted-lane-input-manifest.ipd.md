# IPD: Restore the outcome tests of the deleted lane input manifest suite

- Date: 2026-09-26
- Kind: child
- Concern: The suite trim `19313eed` deleted `tests/test_lane_input_manifest.py` (444 lines, 21 test methods), the acceptance coverage for spec `7ckptx` R5.1-R5.3: lane inputs arrive by copy with a digest manifest, copies are link-independent (hard links and symlinks caught), inputs are sealed read-only with changes as new revisions, and every `--file` attachment resolves inside the lane. No remaining test covers `lane_containment.verify_link_independence`, `verify_lane_input_seal` or `attachments_outside_lane`, so a regression in any of them would ship green. Recovered at HEAD `61ef21d8`, the file passes 21/21 in-repo.
- Scope: IN: restore a SUBSET of the recovered file as `tests/test_lane_input_manifest.py`: the outcome tests that each prove a distinct refusal or guarantee; drop the docstring pin, the empty class, and tests redundant with a kept one. OUT: any change to `lane_containment`.
- Scope-Paths: tests/test_lane_input_manifest.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: mvw06u
- Set: restorecov
- Order: 2
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: dmxc5h

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog mvw06u: restore 13 outcome tests of the deleted lane input manifest suite, dropping the docstring pin, an empty class, and seven redundant tests.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A small outcome-only suite fails if lane input materialization stops catching link smuggling, digest tampering, in-place edits, or out-of-lane attachments.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the subset and verify

- [ ] E-01 Write `git show 19313eed^:tests/test_lane_input_manifest.py` to `tests/test_lane_input_manifest.py`, then DELETE: the class `RevisionMechanismHasNoProductCallerTests` (its only test, `test_its_docstring_states_it_has_no_consumer`, asserts docstring wording); the class `DriverArgvTests` (it has a docstring and NO test methods); and these redundant methods: `test_materialized_paths_are_inside_the_lane_and_relative` (subsumed by the attachment-containment tests), `test_an_absent_source_records_no_entry_rather_than_a_fabricated_one`, `test_a_missing_digest_is_caught` and `test_an_unrecognized_mode_is_refused` (same verifier refusal path as the kept wrong-digest test), `test_part_i_the_manifest_file_has_no_write_bit` and `test_part_ii_every_materialized_input_has_no_write_bit` (mode-bit inspection; the kept `test_an_accidental_in_place_write_fails` proves the consequence for both the manifest and an input), and `test_restored_copy_passes_again` (calls another test method; the round trip adds little). Update the module docstring: state that this is a trimmed restoration of the `19313eed` deletion (plan dmxc5h) keeping outcome tests only, and remove its bullet about R5.3 being "asserted over EVERY `--file` value in the constructed argv" only if it no longer describes a kept test (it still describes `test_both_attachments_are_localized`, so keep it).
  - Depends on: none
  - Expected outcome: 13 test methods remain (list in F-2).
  - Execution state: pending

- [ ] E-02 Run the file IN-REPO under both runners: `python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""` (report wall time with `time`) and `python3 -m unittest tests.test_lane_input_manifest`. Do NOT run it under pytest from `/tmp` (triage reported a hang there from rootdir/conftest interplay). If the pytest run takes more than 30s, stop and report rather than marking `slow`.
  - Depends on: E-01
  - Expected outcome: 13 passed under each runner, well under 5s.
  - Execution state: pending

- [ ] E-03 Show the kept tests are not vacuous and run the bare suite: IN THE WORKTREE, make `lane_containment.verify_link_independence` skip its inode/link-count comparison (for example return early after the symlink check), run `test_hard_link_is_caught` and paste it FAILING on the independence assertion; restore. Then run the bare suite.
  - Depends on: E-02
  - Expected outcome: the sabotaged run fails the hard-link test; restored, it passes; bare suite green.
  - Execution state: pending

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

## Proposed changes (ordered, validatable)

1. E-01: restore the 13-test subset.
2. E-02: both runners in-repo, timed.
3. E-03: sabotage check and bare suite.

## Deferred / out of scope (with reason)

- A test of the argv the oc driver actually constructs (the intent of the empty `DriverArgvTests`): it never existed in the deleted file, so it is not a restoration.
  - Carrier-Declined: not lost coverage; nothing to restore.

## Scope check

- Over-scope: none.
- Under-scope: none. Seven redundant outcome tests are dropped deliberately for count (maintainer rule); OQ-01 records the choice.

## Required tests / validation

- The restored file under pytest and unittest, in-repo, timed; one sabotage run; bare suite. Test rule: outcomes only; no docstring or source pins.

## Spec / documentation sync

N/A: test-only restoration of coverage for spec `7ckptx` R5, whose text is unchanged.

## Open questions

### OQ-01: Keep all 20 outcome tests instead of 13?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: 13, per the maintainer's "keep the count small". Every dropped method either shares a verifier path with a kept one or inspects a mechanism (mode bits) whose consequence a kept test proves. A reviewer can restore any dropped method by name from `19313eed^` without re-deriving it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "    def test_" tests/test_lane_input_manifest.py` showing exactly the 13 names in F-2, and `grep -n "__doc__\|DriverArgvTests\|RevisionMechanism" tests/test_lane_input_manifest.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `time python3 -m pytest tests/test_lane_input_manifest.py -o addopts=""` showing `13 passed` and the real time, and `python3 -m unittest tests.test_lane_input_manifest` showing `Ran 13 tests` and `OK`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the sabotage diff, the FAILING `test_hard_link_is_caught` output (the independence assertion, not an import error), the restored passing run, and the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One restored test file with 13 outcome tests (about 2s), dropping one docstring pin, one empty class, and seven redundant outcome tests. No production code changes.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if a kept test fails against today's `lane_containment`, do not edit it to pass; report it as a possible regression since `19313eed`.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push); the sabotage edit is reverted and not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `mvw06u` `done` with `--evidence` citing the executed plan.
