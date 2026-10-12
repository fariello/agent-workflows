# IPD: Delete the redundant len(TERMINAL_STATES_CANONICAL) == 14 count literal from test_canonical_terminal_states_set

- Date: 2026-10-11
- Kind: child
- Concern: `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_canonical_terminal_states_set` asserts `self.assertEqual(runner_shared.TERMINAL_STATES_CANONICAL, EXPECTED_CANONICAL_STATES)` and then, on the next statement, `self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)`. The first assertion fixes every member BY NAME against a hand-written module-level table, so the count is strictly implied by it and can never fail on its own; it only adds a second number to update when the canonical vocabulary legitimately grows, which is the count-pin shape `GUIDING_PRINCIPLES.md` P16 prohibits and the shape Set `structpin` exists to remove. This is the third instance found by plan `44c42h`'s scan and filed at its review as backlog `rdtme9`.
- Scope: Delete exactly ONE source line, `self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)`, from that one test, adding no replacement. KEEP the preceding name-level equality and every other line of the file, including the `EXPECTED_CANONICAL_STATES` table and the test's docstring. EXCLUDES the three bare count literals in `tests/test_runwire_verifier_authority.py::test_set_level_checks` part (c), which are a DIFFERENT shape (no name-level equality beside them) filed separately as backlog `2n9y3f`; EXCLUDES the module docstring's stale "12 canonical terminal states" prose count; EXCLUDES any production change and any new test.
- Scope-Paths: tests/test_terminal_status_vocabulary.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: rdtme9
- Set: structpin
- Order: 7
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5.5-1m-us
- Id: aoy1uk

## Workflow history

- 2026-10-12 to-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): Authored from backlog `rdtme9`, filed at plan `44c42h`'s review (PR-404) from its Deferred row. Every claim MEASURED at HEAD `9e94438c7`. Unlike sibling `9g97e5`, whose item inherited a false "name-level equality on the line above" premise, the premise here is TRUE and was proven by in-process mutation in both directions (F-02): the name-level equality fails first on growth and on shrink, so the literal is unreachable as a failure. Filed backlog `2n9y3f` for the adjacent but differently-shaped literals in `tests/test_runwire_verifier_authority.py` rather than widening scope.
- 2026-10-12 draft (opencode/its_direct-pt3-claude-opus-5.5-1m-us): created.

## Goal

Leave `test_canonical_terminal_states_set` asserting only the name-level membership of the canonical terminal
vocabulary, so a legitimate addition costs one table edit instead of two, while losing no coverage, because
the count it deletes is implied by the equality that precedes it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the one count literal

- [ ] E-01 DELETE THE SINGLE STATEMENT `self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)` FROM `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_canonical_terminal_states_set`, ADDING NO REPLACEMENT. Keep the preceding `self.assertEqual(runner_shared.TERMINAL_STATES_CANONICAL, EXPECTED_CANONICAL_STATES)` verbatim, keep the docstring ("TERMINAL_STATES_CANONICAL contains exactly the 14 canonical states."), and touch no other line. DO NOT substitute a range, a floor, a `>=` bound, or `len(EXPECTED_CANONICAL_STATES)`: the quantity is not the invariant, and comparing two lengths of sets already proven equal is the same tautology in a different spelling. STOP CONDITION BEFORE DELETING: run the test by name and confirm it PASSES (not skipped, not deselected), and confirm the preceding assertion still compares the module attribute against the hand-written `EXPECTED_CANONICAL_STATES` table; if that equality has been removed, weakened to a subset check, or rebased onto a value derived from `runner_shared` itself, DO NOT DELETE and report, because then the count would no longer be redundant.
  - Depends on: none
  - Expected outcome: `rg -n "len\(runner_shared.TERMINAL_STATES_CANONICAL\)" tests/test_terminal_status_vocabulary.py` returns no match; `git diff -- tests/test_terminal_status_vocabulary.py` shows exactly one removed line and no added line; the file's collected test count is unchanged (16 at authoring) and all pass; the name-level equality still turns RED under an in-memory growth and shrink of the canonical set.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `GUIDING_PRINCIPLES.md` P16 "No count or census pins" is the clause this literal violates, and its "Verify test sensitivity with mutation" bullet is why V-01 demands the surviving assertion be shown RED under mutation rather than only green.
- SET PRECEDENT: siblings `44c42h` (E-01, `len(runner_shared.TERMINAL_STATES) == 24` in `tests/test_reaskscore_composed.py`) and `9g97e5` (`len(swept) == 24` in `tests/test_artifact_audit.py`) deleted the same shape on the same vocabulary family, each with a stop condition on the pin that carries the coverage. This plan follows that house style. Here the carrying pin is in the SAME test, one statement earlier, which makes this the simplest case of the three.
- `9g97e5` REVIEW-DEMONSTRATED MUTATION MECHANISM: rebind module attributes in-process from a scratch script under the gitignored `tmp/` and call `pytest.main(["-o", "addopts=", ...])`, so no production file is edited. Reused for F-02 and V-01.
- The suite is run BARE (`python3 -m pytest`); use `-o addopts=""` only where a per-test count is needed (AGENTS.md repo-local contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements at HEAD `9e94438c7`.

| Id | Finding | Evidence |
| --- | --- | --- |
| F-01 | **THE TARGET EXISTS AND IS EXACTLY AS THE ITEM DESCRIBES.** The test body is two statements: the name-level equality against `EXPECTED_CANONICAL_STATES`, then the count literal. `EXPECTED_CANONICAL_STATES` is a hand-written module-level `frozenset` of 14 string literals in the same file, not derived from `runner_shared`. Both literals are correct today, so this is a maintenance-cost change (`Work-Kind: chore`), not a bug fix. | Test body read in full; `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q` -> `16 passed in 0.46s` |
| F-02 | **THE COUNT CAN NEVER FAIL ON ITS OWN, PROVEN BY MUTATION IN BOTH DIRECTIONS.** In-process rebinding of `runner_shared.TERMINAL_STATES_CANONICAL` (scratch script under `tmp/`, deleted afterwards, no production file edited), running only this test with the literal still present: GROWTH (added `probe-15th-state`, len 15) -> `1 failed`, `AssertionError: Items in the first set but not the second: 'probe-15th-state'`; SHRINK (removed `retired`, len 13) -> `1 failed`, `AssertionError: Items in the second set but not the first: 'retired'`. In both cases the failure is raised by the name-level equality, which precedes the count, so the count is never reached when membership is wrong and always passes when membership is right. | Probe output: `== growth 15` / `E  'probe-15th-state'` / `1 failed in 0.19s`; `== shrink 13` / `E  'retired'` / `1 failed in 0.07s` |
| F-03 | **NO OTHER ASSERTION IN THE FILE READS THE LITERAL.** The literal is a standalone statement; no later statement depends on it. Other tests in the file reference `TERMINAL_STATES_CANONICAL` by membership (`assertIn`) or identity (`assertIs`), never by length. | `rg -n "TERMINAL_STATES_CANONICAL" tests/test_terminal_status_vocabulary.py` read: the only `len(` site is the target |
| F-04 | **AN ADJACENT, DIFFERENTLY-SHAPED INSTANCE EXISTS ELSEWHERE AND IS NOT THIS ITEM.** `tests/test_runwire_verifier_authority.py::test_set_level_checks` part (c) "VOCABULARY UNCHANGED" asserts `len(rs.TERMINAL_STATES_CANONICAL) == 14`, `len(rs.TERMINAL_STATUS_ALIASES) == 10` and `len(runner_shutdown.KNOWN_ITEM_STATUSES) == 28` with NO name-level equality beside them. Those are bare count pins, not redundant restatements, so deleting them needs a different argument (which cross-file pin carries each vocabulary) and is out of this item's scope. Filed as backlog `2n9y3f`. | `rg -n "len(rs.TERMINAL_STATES_CANONICAL)" tests/` returns that one site; no pending plan or open backlog item named it before this authoring |
| F-05 | **THE MODULE DOCSTRING CARRIES A STALE PROSE COUNT.** It reads "V-01 (E-01): 12 canonical terminal states" while the vocabulary has 14. P16 governs assertions, not comments; no test fails on it, and editing prose while claiming a one-line deletion would muddy V-01's diff evidence. | Module docstring read |
| F-06 | **NO OTHER PENDING PLAN DECLARES THIS FILE.** `rg -n "Scope-Paths:.*test_terminal_status_vocabulary" .aw/records/plans/pending/` returns nothing, so `- Item-Dependencies: none` is correct. Siblings `44c42h` and `9g97e5` (both executed) only READ this file for their stop conditions. | Search returned no output |

## Proposed changes (ordered, validatable)

1. Verify the preceding name-level equality is live and sensitive (stop condition), then delete the single count statement (E-01).
2. Prove by in-memory mutation, after the deletion, that the surviving equality still reddens on growth and shrink, and that the file's collected count is unchanged (V-01).

## Deferred / out of scope (with reason)

- THE THREE BARE COUNT LITERALS IN `tests/test_runwire_verifier_authority.py::test_set_level_checks` part (c) (F-04). A different shape in a different file, outside `rdtme9`'s single named test; widening would be the opportunistic scope growth the execution contract forbids.
  - Carrier: 2n9y3f
  - Carrier-Evidence: .aw/records/backlog/open/20261011-structpin-01-2n9y3f-runwire-vocab-count-literals.backlog.md
- THE MODULE DOCSTRING'S STALE "12 canonical terminal states" (F-05) and the test docstring's "exactly the 14 canonical states".
  - Carrier-Declined: prose, not an assertion; P16 governs assertions and treats docstrings as human-facing, no test can rot from it, and the test docstring is accurate today; editing it here would break the one-line-deletion evidence V-01 relies on
- A MECHANICAL GUARD AGAINST THE SHAPE RETURNING. Set Order 02 (`76ic0k`) owns the author-time guard and records count-shape detection as syntactically undecidable.
  - Carrier-Declined: an accepted, recorded bound on sibling plan `76ic0k`; nothing is left unowned

## Scope check

- Over-scope: none. One file, one deleted statement, nothing added.
- Under-scope: does not touch the bare count pins in `tests/test_runwire_verifier_authority.py` (carried by `2n9y3f`), does not correct the stale module-docstring count (declined, F-05), and does not prevent the shape recurring (bound owned by `76ic0k`). No coverage residue: unlike `9g97e5` F-04, the carrying pin here is in the same test, so this file detects every growth and shrink after the deletion exactly as before (F-02).

## Required tests / validation

Outcome tests only; no production source is read or asserted about. All evidence is pasted actual output.

1. Stop condition BEFORE the edit: `python3 -m pytest "tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_canonical_terminal_states_set" -o addopts="" -v` -> PASSED by name.
2. `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q` BEFORE and AFTER, same collected count (16 at authoring; re-derive), all passing.
3. `rg -n "len\(runner_shared.TERMINAL_STATES_CANONICAL\)" tests/test_terminal_status_vocabulary.py` -> no match; `git diff -- tests/test_terminal_status_vocabulary.py` -> exactly one `-` line, no `+` line.
4. Mutation probe AFTER the edit, in-process from a gitignored `tmp/` scratch script rebinding `runner_shared.TERMINAL_STATES_CANONICAL` (growth by one invented member, shrink by one real member), each run showing the edited test RED naming the injected or removed token; scratch file deleted afterwards.
5. Bare `python3 -m pytest` before and after: the set of FAILING tests must be identical by name (re-derive the baseline on the tree as found; do not fix, skip, or deselect other parties' failures) and the passed count must not fall.
6. `git status --short` shows `tests/test_terminal_status_vocabulary.py` as the only modified tracked path, no scratch file left.

## Spec / documentation sync

N/A with reason: deleting one redundant test assertion changes no behavior, CLI surface, record grammar, or contract. No `.spec.md` is amended and none is in `- Scope-Paths:`. `GUIDING_PRINCIPLES.md` P16 already licenses the removal.

## Open questions

### OQ-01: Should the stale "12 canonical terminal states" module docstring be corrected in the same change?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED NO from repository precedent. Sibling `9g97e5` (OQ-01 and F-05) refused the equivalent prose edit beside its literal on the same grounds: P16 governs assertions, not docstrings, and a prose edit would turn a provable one-line deletion into a mixed diff. Recorded in Deferred with Carrier-Declined.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: (a) STOP CONDITION, pasted BEFORE the edit: the by-name run of `test_canonical_terminal_states_set` showing `PASSED` and `1 passed`, plus a quoted excerpt of the test body showing the equality against `EXPECTED_CANONICAL_STATES`; a skipped, missing, or weakened equality is a STOP (mark `blocked`, do not delete). (b) `rg` for `len(runner_shared.TERMINAL_STATES_CANONICAL)` in the file returning no match, pasted. (c) `git diff -- tests/test_terminal_status_vocabulary.py` pasted, showing exactly one removed line and no added line. (d) `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts="" -q` pasted before and after with the same collected count, all passing. (e) MUTATION after the edit, pasted: the in-process growth probe and shrink probe (the code path is `pytest.main` driving the edited test with `runner_shared.TERMINAL_STATES_CANONICAL` rebound, as in F-02) each showing `1 failed` with the injected or removed token named. (f) Bare `python3 -m pytest` summary lines before and after, with the failing-test set identical by name and the passed count not lower. (g) `git status --short` showing only the one test file modified and no scratch file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (1 E-leaf in 1 group).

EXECUTE ONLY WHAT THIS PLAN DECLARES: one deleted statement in `tests/test_terminal_status_vocabulary.py`. If execution appears to need any other edit, STOP and report. The only sanctioned perturbation of production state is the IN-MEMORY rebinding in V-01 (e); no production file is written. DO NOT WEAKEN AN ASSERTION TO MAKE IT PASS: if the stop condition fails, leave the literal in place, mark E-01 `blocked`, and report. Commit through `aw commit aoy1uk -- tests/test_terminal_status_vocabulary.py <this plan path>`; never push. Move the plan to `executed/` only through the tooled lifecycle after `aw ipd lint --phase pre-transition` conforms and V-01 records pasted evidence.
