# IPD: Delete the redundant len(swept) == 24 count literal from the TERMINAL_STATES sweep in test_artifact_audit

- Date: 2026-10-02
- Kind: child
- Concern: `tests/test_artifact_audit.py::TestArtifactAuditEngine::test_terminal_states_tolerance_and_counterexample_trichotomy` closes with two statements, `self.assertEqual(swept, set(runner_shared.TERMINAL_STATES))` and `self.assertEqual(len(swept), 24)`. The second is a count pin on a vocabulary that is EXPECTED TO GROW, and `GUIDING_PRINCIPLES.md` P16 prohibits the shape outright under "No count or census pins". It is the LAST surviving instance of the shape that Set `structpin` exists to remove: it was created in commit `7ffd3f8a5` AFTER plan `44c42h` was authored, caught by `44c42h`'s own re-run AST scan at validation time, and filed as this plan's backlog item `2je7m3` rather than swept into a plan that had already been reviewed. THE ITEM'S STATED PREMISE IS WRONG IN A WAY THAT MATTERS AND IS CORRECTED HERE, which is the single most important thing a reviewer should check: the item inherits `44c42h`'s framing that such a literal "restates the name-level equality on the line above it", but the line above is a TAUTOLOGY, not a name-level equality. `swept` is built by `for st in sorted(runner_shared.TERMINAL_STATES): swept.add(st)`, so `swept == set(runner_shared.TERMINAL_STATES)` is true by construction for EVERY possible input and can never fail (F-03, proven over random inputs). So the count literal is NOT redundant against its neighbour; it is the only size-bearing claim on those two lines. It is redundant against a CROSS-FILE pin instead (F-02), and deleting it is safe for that reason and not for the reason the item gives.
- Scope: Delete exactly ONE source line, `self.assertEqual(len(swept), 24)`, from that one test, adding no replacement. KEEP the preceding `assertEqual(swept, set(...))` statement, the `swept` binding, and every other line, even though F-03 proves that surviving assertion is vacuous; the reason that tautology is retained rather than cleaned up is argued in OQ-01 and is deliberately a REFUSAL of an adjacent tidy-up, because this plan's file is also declared by the `to-review` plan `8fo926` (F-06) and a minimal one-line diff is what keeps the two from colliding. EXCLUDES the docstring line "22 other members", which is a prose count in the same test; it is measured as CURRENTLY ACCURATE (F-05) and left alone with reasons, since P16 governs assertions and not comments, and editing prose while claiming a pure deletion invites the hollowing-out V-01 exists to detect. EXCLUDES `tests/test_terminal_status_vocabulary.py`, which this plan only READS and whose own `len(TERMINAL_STATES_CANONICAL) == 14` literal is the separately-filed live item `rdtme9` (F-07). EXCLUDES any production change, any new test, and any mechanical guard against a count literal returning (undecidable syntactically; owned by `76ic0k`).
- Scope-Paths: tests/test_artifact_audit.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 2je7m3
- Set: structpin
- Order: 5
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 9g97e5

## Workflow history

- 2026-10-02 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `2je7m3`, which plan `44c42h` filed from its OWN validation evidence (its V-01 records "1 new row in test_artifact_audit.test_terminal_states_tolerance_and_counterexample_trichotomy reconciled and filed as backlog chore 2je7m3"). Every claim below was MEASURED at HEAD `a7367bfbf` before being written, and the measurement CORRECTED the item's central premise rather than restating it. THREE THINGS A REVIEWER SHOULD CHECK FIRST. (1) The item's inherited justification is FALSIFIED: the neighbouring assertion is a tautology over any input (F-03, demonstrated over random sets), so "redundant against the line above" is not why deletion is safe. (2) The real justification was found and VERIFIED LIVE as a stop condition (F-02): `tests/test_terminal_status_vocabulary.py::test_terminal_states_union` pins every member BY NAME against two hand-written tables, and a 25th member was INJECTED into the shipped vocabulary to prove that pin goes red (it did, naming the injected token). (3) THE DELETION LOSES ONE DIRECTION OF COVERAGE AND THAT IS STATED RATHER THAN HIDDEN (F-04): a SHRINK of the vocabulary was injected too, and the edited test stays GREEN after the deletion where the literal would have caught it; the cross-file pin catches that shrink, so no coverage is lost REPOSITORY-WIDE, but the claim "nothing is lost in this file" would have been false and is not made.
- 2026-10-02 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave the `TERMINAL_STATES` sweep asserting only claims that a CORRECT change cannot falsify, with the
coverage its deleted literal carried shown to live elsewhere rather than assumed to.

The test of success is two-sided, because a one-sided fix here is trivial and worthless. Adding a legitimate
25th terminal status must no longer redden this test on its COUNT (it is reddened at HEAD by the literal), and
a genuinely wrong vocabulary change must still be caught SOMEWHERE in the suite, proven by injecting one in
each direction (growth and shrink) rather than by reasoning about it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the one count literal

- [ ] E-01 DELETE THE SINGLE LINE `self.assertEqual(len(swept), 24)` FROM `tests/test_artifact_audit.py::TestArtifactAuditEngine::test_terminal_states_tolerance_and_counterexample_trichotomy`, ADDING NO REPLACEMENT. Delete that ONE statement and nothing else: not the `assertEqual(swept, set(runner_shared.TERMINAL_STATES))` above it, not the `swept` binding or its `swept.add(st)` accumulation, not the `# Assert closed vocabulary is completely swept and equal to TERMINAL_STATES` comment, and not the docstring. DO NOT substitute a different literal, a range, a floor, or a `>=` bound: the quantity is not the invariant, and any bound over a vocabulary that grows by design is the same defect with a longer fuse (`TERMINAL_STATES` has grown at least twice by name in tracked history, gaining `already-landed` and `retired`, each visible in its own source comment). VERIFY THE CROSS-FILE PIN IS LIVE BEFORE DELETING, AND TREAT ITS ABSENCE AS A STOP CONDITION, exactly as sibling plan `44c42h` E-01 did for the same vocabulary: run `tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union` and confirm it PASSES BY NAME and is not skipped or deselected. That test asserts `runner_shared.TERMINAL_STATES == frozenset(EXPECTED_CANONICAL_STATES | set(EXPECTED_LEGACY_ALIASES.keys()))` where both operands are hand-written module-level tables in that file (measured: 14 canonical + 10 aliases = 24), which fixes every member BY NAME and is therefore strictly stronger than fixing the count. If that test is absent, skipped, or green under a mutated vocabulary, DO NOT DELETE: report instead, because then the premise fails and a redundant literal honestly labelled beats a silent coverage loss. NOTE THE ASYMMETRY E-01 ACCEPTS, measured in F-04 and NOT waved away: after this deletion the edited test no longer notices a SHRINK of the vocabulary (it stays green), so the shrink direction is carried ENTIRELY by the cross-file pin; that is why verifying the pin is a stop condition rather than a courtesy.
  - Depends on: none
  - Expected outcome: the line `self.assertEqual(len(swept), 24)` is absent from the file; `rg` finds no `len(swept)` in it; `ruff check tests/test_artifact_audit.py` reports `All checks passed!` (no binding is orphaned, because `swept` keeps its reader on the line above); `python3 -m pytest tests/test_artifact_audit.py -o addopts=""` reports `24 passed`; and the cross-file pin still turns RED when a member is added to or removed from the shipped vocabulary. Authoring baseline to re-derive at execution rather than trust: 24 tests in this file, `len(runner_shared.TERMINAL_STATES) == 24` (14 canonical + 10 aliases), and `test_terminal_states_union` passing by name.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- P16 PROHIBITS THIS SHAPE OUTRIGHT AND NAMES THE REMEDY AS SUBTRACTION. `GUIDING_PRINCIPLES.md` Section 16
  states "No count or census pins: Never assert on the number of callers, call-site counts, definition counts,
  or closure sizes as a proxy for an invariant", and its "What to do instead" prescribes exercising the code and
  asserting observable outputs. It also warns against the failure this plan must avoid: a test that asserts
  nothing proves nothing, so the deletion must be paired with positive evidence that the real claim survives.
- THE SET'S ESTABLISHED HOUSE STYLE FOR THIS EXACT VOCABULARY IS DELETE-AND-VERIFY-THE-CROSS-FILE-PIN. Sibling
  plan `44c42h` E-01 deleted `len(runner_shared.TERMINAL_STATES) == 24` from
  `tests/test_reaskscore_composed.py` on precisely this reasoning, and made the cross-file pin's liveness a
  STOP condition rather than an assumption. This plan follows that precedent deliberately, including the stop
  condition, because the vocabulary and the carrying pin are the same ones.
- THE MODULE UNDER TEST DOCUMENTS "DERIVE, NEVER ENUMERATE" AS ITS CONVENTION, which is the positive form of the
  same rule. `artifact_audit.run_status_is_nonterminal`'s docstring argues the enumerated form "fails" and
  derives forwardness from `expected_dir_for_status` instead, and `artifact_audit.allowed_lifecycle_pairs`
  derives its pairs from `record_placement.target_subdir`. The sweep itself already follows this by iterating
  `sorted(runner_shared.TERMINAL_STATES)` at test time; the count literal is the one line that does not.
- THE SWEEP IS WRITTEN AS AN ANTI-DRIFT CROSS-CHECK AND THAT PART IS LOAD-BEARING. Inside the loop,
  `self.assertIn(st, runner_shutdown.KNOWN_ITEM_STATUSES)` asserts one-directional containment of the audit
  vocabulary in the runner's, carrying the comment "Anti-drift: in the style of
  runner_shutdown.KNOWN_ITEM_STATUSES". Measured (F-04): that assertion, not the count, is what actually fires
  when a new member is added to the shipped set. It is retained untouched.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Subject | Measurement at HEAD `a7367bfbf` | Consequence for this plan |
|---|---|---|---|---|
| F-01 | HIGH | the target literal | **THE TARGET EXISTS, IS UNIQUE IN THE REPOSITORY, AND IS THE LAST OF ITS SHAPE ON THIS VOCABULARY.** `rg -n "len\(.*TERMINAL_STATES.*\)\|len\(swept\)" tests/ agent_workflows/` returns exactly two rows repository-wide: `tests/test_artifact_audit.py:515 self.assertEqual(len(swept), 24)` (this plan's target) and `tests/test_terminal_status_vocabulary.py:74 self.assertEqual(len(runner_shared.TERMINAL_STATES_CANONICAL), 14)` (the separately-filed `rdtme9`). The two literals `44c42h` deleted are confirmed gone. | The scope is a single line and the item is not stale. E-01 deletes one of these two rows and explicitly excludes the other (F-07). |
| F-02 | HIGH | `tests/test_terminal_status_vocabulary.py::test_terminal_states_union` | **THE COVERAGE IS CARRIED BY A LIVE CROSS-FILE NAME PIN, VERIFIED BY INJECTION RATHER THAN BY READING.** That test passes by name at HEAD (`1 passed in 0.35s`, not skipped, not deselected) and asserts `runner_shared.TERMINAL_STATES` equals `frozenset(EXPECTED_CANONICAL_STATES \| set(EXPECTED_LEGACY_ALIASES.keys()))` over two hand-written module-level tables (measured: 14 canonical, 10 aliases, union 24). I then INJECTED a 25th member (`"probe-25th-state"`) into `runner_shared.TERMINAL_STATES_CANONICAL` in the shipped module and re-ran it: `2 failed, 14 passed`, with `test_terminal_states_union` and `test_canonical_terminal_states_set` both naming `'probe-25th-state'` in their diff. Mutation reverted. | THIS IS THE REAL JUSTIFICATION FOR THE DELETION, replacing the item's falsified one. A name-level equality is strictly stronger than a count over the same set, so the literal is redundant against THIS, in another file. E-01's stop condition is exactly this test. |
| F-03 | HIGH | the neighbouring assertion | **THE ITEM'S PREMISE IS FALSE: THE LINE ABOVE THE LITERAL IS A TAUTOLOGY, NOT A NAME-LEVEL EQUALITY.** Backlog `2je7m3` inherits `44c42h`'s framing of a count that "restates the name-level equality on the line above it". Here the line above is `self.assertEqual(swept, set(runner_shared.TERMINAL_STATES))`, and `swept` is constructed by `swept = set()` then `for st in sorted(runner_shared.TERMINAL_STATES): swept.add(st)`. That assertion is therefore true BY CONSTRUCTION for every possible value of `TERMINAL_STATES` and can never fail. Proven over 6 random sets of random size (including the empty set): `swept == set(fake)` held every time, no counterexample reachable. | The plan must NOT justify the deletion as "redundant against its neighbour", which is what the item says and what a reviewer would otherwise check. It is redundant against F-02's cross-file pin. This also means the surviving assertion is vacuous, which raises OQ-01 (and is refused there, deliberately). |
| F-04 | MED | coverage directionality | **THE DELETION LOSES THE SHRINK DIRECTION IN THIS FILE, AND THE SURVIVING GUARD IS THE `assertIn`, NOT THE COUNT.** Two injections into the shipped vocabulary, each with the literal already deleted. GROWTH (added a 25th canonical member): the edited test FAILS anyway, at `self.assertIn(st, runner_shutdown.KNOWN_ITEM_STATUSES)` with `AssertionError: 'probe-25th-state' not found in frozenset(...)`, so the count was never what caught growth. SHRINK (removed the alias `"not-attempted"`, leaving 23): the edited test reports `24 passed`, i.e. GREEN, where the count literal would have failed; the cross-file pin reports `3 failed`. Both mutations reverted. | Stated in E-01 rather than hidden. Repository-wide no coverage is lost (F-02 catches both directions by name), but the honest claim is narrower than "nothing changes", and this is WHY the cross-file pin's liveness is a stop condition instead of a remark. |
| F-05 | LOW | the docstring count | **A SECOND COUNT LIVES IN THE SAME TEST AS PROSE, AND IT IS CURRENTLY ACCURATE.** The docstring reads "22 other members: derived from expected_dir_for_status ('pending') -> tolerated unmoved, flagged moved". Measured: excluding `executed` and `retired` leaves exactly 22 members, and `artifact_audit.expected_dir_for_status` returns `pending` for all 22 (the result set is the single value `{'pending'}`). | EXCLUDED from scope with reason. P16 governs assertions, not comments ("Comments and docstrings are for humans and models reading the code"); the number is right today; and no test fails when it rots. Recorded in Deferred so a reader does not mistake the omission for an oversight. |
| F-06 | MED | `8fo926` | **ONE OTHER PENDING PLAN DECLARES THIS FILE, AND IT DOES NOT COLLIDE, WHICH WAS CHECKED RATHER THAN ASSUMED.** Enumerating every plan declaring `tests/test_artifact_audit.py` in `- Scope-Paths:` returns exactly one besides this plan: `8fo926` (`- Status: to-review`, Set `runviewdisc`, Order 4), which also declares `agent_workflows/artifact_audit.py`. Its E-02 and E-03 ADD two new tests (a `substantially-complete`/`complete` symmetry test and a `fail-gate` family test) and its E-04 edits a production comment; none of its items touches the sweep test, and it cites that test only as a STYLE precedent in its conventions ("E-02 and E-03 are written in that house style"). | No `- Item-Dependencies:` edge is required and `none` is correct. The two plans touch disjoint regions of one file, so either order works. This is ALSO the reason E-01 is deliberately minimal: a wider tidy-up of the sweep (OQ-01) would rewrite lines `8fo926`'s prose cites, turning a non-collision into one. |
| F-07 | LOW | `rdtme9` | **THE SIBLING LITERAL IS ALREADY FILED AND LIVE, SO EXCLUDING IT STRANDS NOTHING.** `len(runner_shared.TERMINAL_STATES_CANONICAL) == 14` in `tests/test_terminal_status_vocabulary.py::test_canonical_terminal_states_set` is backlog `rdtme9` (`- Status: open`, Set `structpin`, `Work-Kind: chore`), filed at `44c42h`'s review as PR-404. Unlike this plan's target it DOES sit beside a genuine name-level equality (`TERMINAL_STATES_CANONICAL == EXPECTED_CANONICAL_STATES` on the preceding lines), so the item's inherited framing is accurate THERE and false HERE (F-03). | Excluded with a live carrier. Editing that file would also entangle E-01's premise with its own edit, since the stop condition READS it; `44c42h` E-01 refused the same widening for the same reason. |
| F-08 | MED | suite baseline | **THE SUITE IS NOT GREEN AT HEAD AND THE THREE FAILURES ARE OTHER PARTIES' FILED BUGS.** Bare `python3 -m pytest` reports `3 failed, 4624 passed, 2 skipped` in 117s. The failures are `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. All three reproduce individually on a CLEAN tree with no edit of mine, and all three are already filed as open backlog items (`6bolin`, `8jeh4x`, `bxnhdj` respectively). | The validation bar is an UNCHANGED NAMED FAILURE SET, not a pass count and not green. Named here so an executor does not read this red as its own, try to fix another party's release-gated bug, or stall. Re-derive on the tree as found; the pass count will have risen as lanes land. |
| F-09 | LOW | `76ic0k` | **NO MECHANICAL GUARD STOPS THIS LITERAL BEING RE-ADDED, AND THAT IS A RECORDED BOUND RATHER THAN AN OVERSIGHT.** This very literal was introduced in `7ffd3f8a5`, AFTER `44c42h` was authored to remove the shape, and was caught only by that plan's re-run scan at validation time. Set Order 02 (`76ic0k`, pending) owns the author-time guard and deliberately EXCLUDES the count shape as syntactically indistinguishable from a legitimate output-count assertion; `44c42h`'s Under-scope records the same bound. | Recorded in Deferred with no new carrier, because the general case is already owned. It is also the honest answer to "will this recur": possibly, and review plus P16 is the control. |

## Proposed changes (ordered, validatable)

1. Verify the cross-file name pin (`test_terminal_states_union`) is live and sensitive, by mutation in BOTH
   directions, BEFORE deleting anything; stop if it is not (E-01, V-01 (a)).
2. Delete the single count literal, adding nothing (E-01).
3. Prove by injection that the vocabulary's membership is still fenced after the deletion, and record which
   direction each fence catches, including the one this file stops catching (V-01 (d), (e)).

## Deferred / out of scope (with reason)

- THE DOCSTRING'S "22 other members" PROSE COUNT, in the same test. F-05: measured accurate today (exactly 22
  members once `executed` and `retired` are excluded, all 22 resolving to `pending` through
  `expected_dir_for_status`). It is out of scope because P16's prohibition is on ASSERTIONS and its sibling
  bullet explicitly frames docstrings as "for humans and models reading the code, not test assertions"; no test
  fails when this number rots; and editing the docstring while claiming a single-line deletion is exactly the
  scope creep that would make V-01's "only this line changed" evidence unprovable. Deliberately not filed as a
  carrier: an accurate comment is not a defect, and filing one would assert outstanding work that does not exist.
  - Carrier-Declined: an accurate comment, not a defect; P16 governs assertions and expressly treats docstrings as human-facing rather than test-asserted, so nothing is owed and no test can rot from it
- THE VACUOUS SURVIVING ASSERTION AND ITS `swept` SCAFFOLDING. F-03 proves `assertEqual(swept, set(TERMINAL_STATES))`
  cannot fail. Removing it (and the now-unread binding) was MEASURED as mechanically clean: `ruff` reports
  `All checks passed!` and the file reports `24 passed`. It is nonetheless REFUSED here, with the reasoning in
  OQ-01: the backlog item scopes this carrier to the count literal, and a wider edit would rewrite the exact
  lines the `to-review` plan `8fo926` cites as its house-style precedent (F-06), converting a clean
  non-collision into a real one for no behavioral gain. Not filed as a carrier because the tautology is inert:
  it asserts nothing, so it can neither fail on a correct change (the defect this Set removes) nor hide a real
  one, which makes it a cosmetic residue rather than deferred work.
  - Carrier-Declined: an inert tautology that asserts nothing, so it neither taxes a correct change nor masks a defect; there is no outstanding obligation to carry, and the measured alternative is recorded in OQ-01 for whoever next edits this test
- THE SIBLING LITERAL `len(TERMINAL_STATES_CANONICAL) == 14` in `tests/test_terminal_status_vocabulary.py`.
  F-07: already filed and live as backlog `rdtme9`, and additionally excluded because E-01's stop condition
  READS that file, so editing it in the same change would entangle the premise with the edit (the same reason
  `44c42h` E-01 gave for refusing the identical widening).
  - Carrier: rdtme9
  - Carrier-Evidence: .aw/records/backlog/open/20260930-structpin-01-rdtme9-redundant-canonical-count-literal.backlog.md
- A MECHANICAL GUARD AGAINST A COUNT LITERAL RETURNING TO THIS FILE. F-09: the general case is owned by Set
  Order 02 (`76ic0k`), whose scope is production-source-read detection and which records count-shape detection
  as syntactically undecidable and therefore an accepted bound; `44c42h`'s Under-scope records the same. A
  bespoke per-file detector here would be a new content pin over a test module, on a concern this plan does not
  own. No carrier is filed because the bound is already recorded on a live sibling plan.
  - Carrier-Declined: an accepted, recorded bound on live sibling plan `76ic0k` (Set `structpin`, Order 02), which owns the author-time guard and states count-shape detection as syntactically undecidable; nothing is left unowned
- THE THREE PRE-EXISTING SUITE FAILURES. F-08: each reproduces on a clean tree, each is another party's work,
  and each is already an open backlog item (`6bolin`, `8jeh4x`, `bxnhdj`). Touching them is what the
  shared-checkout rule forbids. They are named only so the validation bar can be stated as an unchanged failure
  set.
  - Carrier-Declined: each is already carried by its own open backlog item (`6bolin`, `8jeh4x`, `bxnhdj`) and belongs to another party; re-filing would duplicate a live item

## Scope check

- Over-scope: none. One file, one deleted assertion line, nothing added and nothing else edited.
- NO CROSS-PLAN COLLISION, CHECKED RATHER THAN ASSUMED (F-06): exactly one other plan declares
  `tests/test_artifact_audit.py` (`8fo926`, `to-review`), and its items add two new tests and edit a production
  comment, touching no line this plan touches. `- Item-Dependencies: none` is therefore correct across Sets and
  not merely within `structpin`. The minimality of E-01 is partly what preserves this.
- Under-scope: this plan does not remove the vacuous neighbouring assertion (OQ-01, refused on collision and
  scope grounds), does not correct or delete the docstring's prose count (F-05, accurate today), does not fix
  the sibling literal in the vocabulary file (F-07, carried by `rdtme9`), and does not prevent a count literal
  being written again (F-09, an accepted bound owned by `76ic0k`). AND IT ACCEPTS ONE MEASURED RESIDUE: after
  the deletion this file no longer reddens on a SHRINK of the terminal vocabulary (F-04), so that direction is
  carried solely by the cross-file name pin. That is deliberate and is why E-01 makes the pin's liveness a stop
  condition, but it is a real narrowing of what this one file detects and is not claimed otherwise.

## Required tests / validation

Outcome tests only; no production source is read and no source text is asserted about production. The evidence
is behavioral and must be PASTED, per the execution contract.

1. STOP CONDITION FIRST, BEFORE THE EDIT:
   `python3 -m pytest "tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union" -o addopts="" -v`
   -> `1 passed`, PASSED by name and not skipped. If this is absent, skipped, or deselected, do not delete; report.
2. `rg -n "len\(swept\)" tests/test_artifact_audit.py` -> NO match after the edit (paste the empty result or
   the nonzero exit).
3. `ruff check tests/test_artifact_audit.py` -> `All checks passed!`. This is cheap but not a formality: it is
   what proves no binding was orphaned by the deletion.
4. `python3 -m pytest tests/test_artifact_audit.py -o addopts=""` -> `24 passed`. The cleared `addopts` is
   required to see the per-test count, per AGENTS.md ("clear the defaults explicitly with
   `python3 -m pytest -o addopts=""`").
5. MUTATION PROBES ON THE SHIPPED VOCABULARY, BOTH DIRECTIONS, EACH A SEPARATE PASTED RUN, AND EACH REVERTED
   IMMEDIATELY. This is the anti-hollowing gate and it is the only evidence that distinguishes a safe deletion
   from a silent coverage loss. With the literal deleted: (a) GROWTH, add one member to
   `runner_shared.TERMINAL_STATES_CANONICAL` and show `tests/test_terminal_status_vocabulary.py` RED naming the
   injected token; (b) SHRINK, remove one entry from `runner_shared.TERMINAL_STATUS_ALIASES` and show the same
   file RED. Record what the EDITED test does under each (authoring measurement: red on growth via the
   `assertIn`, GREEN on shrink, which is the accepted residue F-04 names). `agent_workflows/runner_shared.py` is
   a production file NOT in `- Scope-Paths:`: each mutation is a throwaway probe that MUST be reverted before
   the next step, and `git status --short` must show it unmodified at the end.
6. Bare whole suite `python3 -m pytest`, pasted with its summary line. THE BAR IS AN UNCHANGED NAMED FAILURE
   SET, NOT A PASS COUNT AND NOT GREEN (F-08). Re-derive the baseline on the tree as found BEFORE any edit,
   record WHICH tests fail, and require the after-set identical by name. Measured at authoring:
   `3 failed, 4624 passed, 2 skipped`, the failures being
   `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`,
   `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`,
   and `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, all three filed to other parties
   (`6bolin`, `8jeh4x`, `bxnhdj`). Do NOT report them as this plan's, do NOT fix them, and do NOT skip or
   deselect them to get a clean line. A risen pass count is expected as other lanes land.
7. `git status --short` -> `tests/test_artifact_audit.py` as the ONLY modified path, with
   `agent_workflows/runner_shared.py` unmodified and no probe or scratch file left behind.

## Spec / documentation sync

N/A with reason. This plan deletes one test assertion. It changes no behavior, no CLI surface, no record
grammar, and no public contract, so no `.spec.md` is amended and `- Scope-Paths:` declares no spec file.
Specifically NOT edited: `GUIDING_PRINCIPLES.md` P16, which already prohibits count pins and needs no amendment
to license this removal; and `agent_workflows/runner_shared.py`, which is touched only by the throwaway
mutation probes of Required-tests item 5 and must be reverted.

## Open questions

### OQ-01: F-03 shows the surviving `assertEqual(swept, set(TERMINAL_STATES))` is a tautology. Should it and its `swept` scaffolding be deleted too, in this plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED ON MEASUREMENT AND ON COLLISION RISK: NO, not in this plan, and the
  refusal is recorded rather than left implicit because a reviewer will reasonably ask.

  THE TIDY-UP IS MECHANICALLY CLEAN, which is why it needs a real reason to refuse rather than a hand-wave. I
  applied it (deleting both assertions plus the `swept = set()` binding and its `swept.add(st)` accumulation,
  leaving the loop and its `assertIn` intact) and measured: `ruff check` reports `All checks passed!` and
  `python3 -m pytest tests/test_artifact_audit.py -o addopts=""` reports `24 passed`. Reverted.

  THREE REASONS IT IS STILL REFUSED HERE. (1) SCOPE: backlog `2je7m3` names the count literal and nothing else;
  widening to a second assertion the item does not mention is the opportunistic growth the execution contract
  forbids, and the Set already has a precedent for refusing exactly this (`44c42h` declined its own third
  instance and filed `rdtme9` instead). (2) COLLISION: F-06 measures that `8fo926` (`to-review`) declares this
  same file and cites these very lines as its house-style precedent ("closes with
  `assertEqual(swept, set(runner_shared.TERMINAL_STATES))`. E-02 and E-03 are written in that house style").
  Deleting the lines it cites would strand that plan's prose and turn a clean non-collision into a real one, for
  no behavioral gain. A one-line diff is what keeps the two plans independent. (3) THE RESIDUE IS INERT: a
  tautology asserts nothing, so unlike the count literal it can neither fail on a correct change nor mask a
  real defect. It costs a reader a moment's confusion, not a red suite.

  WHY NO CARRIER IS FILED, stated so the decision is not mistaken for an omission: filing one would assert
  outstanding work, and there is none to do; the measurement above is recorded here so that whoever next edits
  this test (plausibly `8fo926`'s executor, who will be adding tests beside it) can remove it in a change that
  owns those lines.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: (a) THE STOP CONDITION, CHECKED BEFORE THE EDIT AND PASTED:
    `python3 -m pytest "tests/test_terminal_status_vocabulary.py::TestTerminalStatusVocabularyDefinitions::test_terminal_states_union" -o addopts="" -v`
    showing `PASSED` by name and `1 passed`. A skipped, deselected, or missing result is a STOP: do not delete,
    mark this item `blocked`, and report. (b) THE LITERAL IS GONE: `rg -n "len\(swept\)" tests/test_artifact_audit.py`
    pasted showing NO match (include the empty output or the nonzero exit code). (c) NOTHING ELSE CHANGED IN THE
    FILE: `git diff -- tests/test_artifact_audit.py` pasted in full, showing exactly ONE deleted line and zero
    added lines, with the preceding `assertEqual(swept, set(...))`, the `swept` binding, the comment above it,
    and the docstring all intact. (d) THE FENCE IS LIVE ON GROWTH: inject one new member into
    `runner_shared.TERMINAL_STATES_CANONICAL`, paste `python3 -m pytest tests/test_terminal_status_vocabulary.py -o addopts=""`
    showing RED with the injected token NAMED in the failure, paste what the edited
    `tests/test_artifact_audit.py` does under the same injection, then REVERT and paste `git status --short`
    showing `agent_workflows/runner_shared.py` unmodified. (e) THE FENCE IS LIVE ON SHRINK: repeat (d) removing
    one entry from `runner_shared.TERMINAL_STATUS_ALIASES` instead, showing the vocabulary file RED; state
    explicitly what the edited test does (authoring measurement: GREEN, the accepted residue of F-04), then
    REVERT and re-paste `git status --short`. (f) `ruff check tests/test_artifact_audit.py` pasted showing
    `All checks passed!`, and `python3 -m pytest tests/test_artifact_audit.py -o addopts=""` pasted showing
    `24 passed`. (g) THE SUITE'S FAILURE SET IS UNCHANGED: bare `python3 -m pytest` pasted with its summary line
    BESIDE a baseline re-derived before any edit, with the FAILING TEST NAMES listed on both sides and shown
    IDENTICAL (not green; name the three pre-existing failures of F-08 explicitly if they appear). (h)
    `git status --short` pasted showing `tests/test_artifact_audit.py` as the ONLY modified path and no probe
    or scratch file left behind.
    A run that shows only (b), (f) and (h) is INSUFFICIENT and does not satisfy this item: a green suite after
    deleting an assertion is equally consistent with having deleted the only thing that was checking anything,
    which is precisely what (a), (d) and (e) exist to rule out. If (d) shows the vocabulary file GREEN under an
    injected member, STOP: the carrying pin is not sensitive, the premise of this plan has failed, and the
    literal must be restored rather than the evidence written up.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

Execution is gated on explicit human approval (`- Status: approved`), per AGENTS.md. This plan is `to-review`
and MUST NOT be executed until it has been reviewed and approval is recorded. `- Readiness:` is deliberately
ABSENT: it is an output of `/plan-review`, and writing one at authoring time would forge a review that has not
happened.

THE ONE JUDGEMENT A REVIEWER SHOULD ATTACK FIRST is not the deletion, which is a single line licensed outright
by P16 and precedented twice in this Set. It is the HONESTY OF F-04: this plan claims the deletion is safe
because a cross-file NAME pin carries the coverage, while conceding that the edited file itself stops noticing a
SHRINK of the vocabulary. If a reviewer judges that the shrink direction must remain detectable inside
`tests/test_artifact_audit.py`, the remedy is NOT to keep the count literal (which reddens on legitimate growth,
the defect being removed) but to say so, and the plan should be revised rather than executed as written. The
second judgement worth attacking is OQ-01's refusal to delete the neighbouring tautology F-03 proves is vacuous.

Execution contract for whoever runs it: commit ONLY `tests/test_artifact_audit.py`, through
`aw commit <plan> -- tests/test_artifact_audit.py`, never `git add -A`, never `-a`, never `--no-verify`, and
never push. Verify the staged set with `git diff --cached --name-only` before committing and re-verify after any
failed raw commit, because this is a SHARED CHECKOUT and another party's restored path must not be swept in.
THE MUTATION PROBES OF V-01 (d) AND (e) MODIFY A PRODUCTION FILE THAT IS NOT IN SCOPE
(`agent_workflows/runner_shared.py`): each must be reverted immediately after its measurement, must never be
staged, and V-01 (h) exists to prove the tree is clean of them. Keep any scratch script under the gitignored
`tmp/`. Execute through `aw ipd begin` before any edit and `aw ipd finalize` for the terminal transition; never
hand-roll the lifecycle move and never `git mv` this plan into `executed/`. Paste real runner output for every
item; a claimed pass with no output does not satisfy V-01.

On success, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition, only after
`aw ipd lint --phase pre-transition` conforms and V-01 carries pasted evidence. Backlog `2je7m3` carries NO
`- Blocks-Release:` gate, so none is inherited above and none may be invented; the item reaches `done` through
the handoff route (this plan executed while carrying `- From-Backlog: 2je7m3`), so do not close it by hand.

- Size assessment: standard
- Cohesion rationale: not required
