# IPD: Delete the live-tree walkthrough census literals that turn the default suite red on the next walkthrough any agent writes

- Date: 2026-09-30
- Kind: child
- Concern: `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id` COUNTS the live `.aw/records/walkthroughs/` tree and asserts two literals over it: `self.assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")` and `self.assertEqual(len(exempt), 11, "Must find exactly 11 grandfathered legacy walkthroughs")`. The tree holds EXACTLY 24 non-README walkthroughs, so the census is AT its pin and the next walkthrough turns it red. THIS IS NOT PREDICTED, IT IS MEASURED: at HEAD `e5fc7c69` I added one conformant walkthrough (`- Id:` matching its slot, nothing else wrong) and the test failed with `AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`, then passed again on its removal. The literal therefore FAILS ON A CORRECT CHANGE, and the correct change is one AGENTS.md mandates ("Save narrative walkthroughs to `.aw/records/walkthroughs/`"), so the test taxes the behavior the repository requires. `GUIDING_PRINCIPLES.md` P16 prohibits the shape outright under "No count or census pins" ("Never assert on the number of callers, call-site counts, definition counts, or closure sizes as a proxy for an invariant"). THE BLAST RADIUS IS THE REASON THIS IS A BUG AND NOT A TIDY-UP: the file carries NO `livecorpus` marker, so it runs in the DEFAULT suite that `pyproject.toml` scopes with `-m 'not slow and not livecorpus'`, and a runner lane merges only if the suite passes, so one agent writing a walkthrough blocks integration for every CONCURRENT lane. `pyproject.toml`'s own `livecorpus` marker description records that exact failure costing "2h 10m and $55.02 with nothing integrated" on 2026-09-19.
- Scope: Delete BOTH literal census assertions from that one test, plus the `exempt` binding whose only reader is the second of them (ruff reports `F841` if it is left behind; measured). KEEP the `LEGACY_WALKTHROUGHS` and `BULLETLESS_GRANDFATHERED` sets and every other line, because the real invariant (`assertEqual(missing_or_mismatched, [], ...)`, that every clustered walkthrough declares an `- Id:` equal to its filename identity slot) READS those sets as filters and needs neither literal. THE REMEDY IS SUBTRACTION AND DELIBERATELY NOT THE `livecorpus` MARKER, which is the one judgement in this plan a reviewer should attack first; it is argued from a measurement in F-5 and F-6 rather than from preference, because marking the class would remove the repository's ONLY guard for the `- Id:` half from both the default suite and CI. EXCLUDES re-numbering 24 to 25 (reproduces the defect one walkthrough later, and the item says so). EXCLUDES the two grandfathering sets. EXCLUDES any change to `check_engine` or to the walkthrough producer. EXCLUDES a guard against a census literal RETURNING, which is undecidable syntactically and is recorded in Deferred with the sibling plan that owns the general case.
- Scope-Paths: tests/test_walkthrough_id6.py
- Item-Dependencies: none
- Status: to-review
- Readiness: no-go
- Work-Kind: bug
- Priority: medium
- From-Backlog: zf1m48
- Blocks-Release: next
- Set: structpin
- Order: 4
- Highest E allocated: 02
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: obyhrm

## Workflow history

- 2026-09-30 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 (BLOCKER, OPEN and escalated), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed). Reviewed in an isolated lane at HEAD `a3e4d2c2`; `aw ipd lint` conforming at `--phase author` before revision. THIS PLAN'S OWN REASONING IS EXCELLENT AND EVERY MEASUREMENT REPRODUCES TO THE NUMBER. I re-drove all of it rather than trusting it: F-1's tripwire fired with the exact message (`AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`) on a conformant 25th walkthrough and went green on its removal; F-3's partial-edit lint failure reproduced verbatim (`F841 Local variable 'exempt' is assigned to but never used`, ruff 0.16.3, exit 1); F-2's full fix gave `All checks passed!` plus `4 passed` WITH the 25th probe present; F-7's anti-hollowing held in BOTH directions (a mismatched `- Id:` and an absent one each turned it red, naming the file); F-6's coverage argument reproduced exactly (a modern-named walkthrough declaring no `- Id:` yields `findings:0` and exit 0 from `aw check all`, while a MISMATCH yields `check.id6-identity-slot`), which vindicates the refusal of the `livecorpus` marker; and F-8's set analysis reproduced to the number (all 11 legacy members return `None` from `_identity_slot_token`, the single bulletless member carries slot `35xfvu` and declares nothing, no stale entries, 12 of 24 files reach the per-file comparison). All probes were removed and the tree is clean. THE BLOCKER IS NOT IN THIS PLAN'S REASONING, IT IS AN OWNERSHIP COLLISION THE SURVEY MISSED (PR-001, F-11): plan `aisk5z` is ALREADY `approved` with an `- Approval:` attestation, carries `- Blocks-Release: next`, declares this same file, and its E-02 deletes these same two assertions, so the two plans race. Worse than a race, they DISAGREE on the end state: `aisk5z` DELETES `LEGACY_WALKTHROUGHS` where this plan's OQ-02 deliberately retains it, and `aisk5z` E-07 ADDS an anti-vacuity floor (from an independent discriminator, proven to fire in E-09) where this plan's F-4 accepts the hole. F-9 missed it because the overlap survey was scoped to Set `structpin` and the colliding plan is in Set `id6slotgate`. Escalated as BLOCKING OQ-03 with `- Finding: PR-001`, because resolving it means retiring somebody's approved work and reassigning a release gate, which is the maintainer's call; the reviewer's recommendation (run `aisk5z`, retire this plan superseded) is recorded there but NOT applied. ALSO FIXED: validation item 6's bar was unachievable and one spelling CRASHES (`aw check all --agent` raises `ValueError: Unsanitized absolute home path in field 'next'`; both forms exit 1; the tree carries 51 pre-existing findings), now an unchanged rule breakdown over plain `aw check` plus the narrow `check_collisions` claim that IS achievable (PR-002, F-12); and item 5's suite bar assumed green where the tree carries one pre-existing time-dependent failure (`1 failed, 3457 passed`, the local-versus-UTC clock skew `fnb8pl`), now an unchanged named failure set (PR-003, F-13). Findings recorded in `.aw/records/reviews/20260930-structpin-04-obyhrm-delete-the-live-tree-walkthrough-census-literals-that-turn-t.review.md`.
- 2026-09-30 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `zf1m48`, which plan `b02ohu` deferred to this carrier BY NAME ("EXCLUDES `tests/test_walkthrough_id6.py`, whose literal `24` is a census over the live RECORDS tree rather than over code structure; it is filed separately") and which `b02ohu`'s own review re-confirmed as live in its R-6 row. Every claim below was MEASURED at HEAD `e5fc7c69` before being written, and the measurements went beyond restating the item in three ways a reviewer should check. FIRST, the item's central claim was PROVEN rather than reasoned: the 25th-walkthrough failure and its exact message were reproduced, and the post-fix green was reproduced (F-1, F-7). SECOND, the item's fix is incomplete as stated: deleting the two assertions alone leaves `exempt` unread and ruff fails `F841`, so E-02 deletes the binding too (F-3). THIRD, the item does not mention the `livecorpus` marker, which is the obvious alternative remedy and the one `GUIDING_PRINCIPLES.md` P16 nominates for live-tree tests; I measured what marking would cost and REJECTED it on evidence (F-5, F-6, OQ-01), because `aw check` reports ZERO findings for a modern-named walkthrough declaring no `- Id:`, making this test the sole guard for that half.
- 2026-09-30 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Leave the walkthrough identity test asserting exactly the invariant it exists for, with no assertion that a
legitimate new walkthrough can falsify, and with its sensitivity to a REAL identity defect demonstrated
rather than assumed.

The test of success is behavioral and two-sided, because a one-sided fix here is easy and worthless: adding a
conformant 25th walkthrough must leave the suite GREEN (it is RED at HEAD), and a walkthrough whose declared
`- Id:` disagrees with its filename slot, or which declares none at all, must still turn it RED. A change that
achieves only the first has hollowed the test out, which P16 forbids under "Never weaken an assertion so it
passes everywhere".

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the two literals, removed separately because their reasoning differs

- [ ] E-01 DELETE THE LIVE-TREE CENSUS ASSERTION `self.assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")` FROM `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id`, ADDING NO REPLACEMENT. Delete that ONE statement and nothing else in this item. DO NOT substitute a different literal, a range, a floor, or a `>=` bound: the quantity is not the invariant, and any bound over a tree that grows by design is the same defect with a longer fuse. The `all_files` binding itself is RETAINED and is load-bearing (the `for p in all_files:` loop below it is what performs the real check), so this is the removal of an assertion, not of the collection it reads. WHY NO REPLACEMENT IS NEEDED, which is the premise a reviewer should test: the surviving `self.assertEqual(missing_or_mismatched, [], ...)` fixes the property for EVERY file the census counted, individually and by name, so it is strictly stronger than a count over the same set. Measured: with the census gone, 12 of the 24 files reach that per-file comparison, the other 12 being the 11 grandfathered legacy names (no identity slot) plus the 1 bulletless grandfathered name. THE ONE HOLE THE COUNT ARGUABLY COVERED IS NAMED AND MEASURED RATHER THAN WAVED AWAY: if the walkthroughs directory were EMPTIED, `missing_or_mismatched` would be `[]` and the test would pass vacuously, which the census would have caught. That is accepted, with reasons in F-4, and is NOT re-plugged with a count here; V-01 instead demands positive proof that the assertion is reached and is live.
  - Depends on: none
  - Expected outcome: the census assertion and its "Census must find exactly 24 walkthroughs" message are absent from the file; a conformant 25th walkthrough no longer turns the test red; `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` still reports `4 passed`. Authoring baseline to re-derive at execution rather than trust: 4 tests in this file, 24 non-README walkthroughs, and the same file RED with `AssertionError: 25 != 24` once a 25th exists.
  - Execution state: pending
- [ ] E-02 DELETE THE GRANDFATHER-SET CENSUS `self.assertEqual(len(exempt), 11, "Must find exactly 11 grandfathered legacy walkthroughs")` AND THE NOW-DEAD `exempt = [p for p in all_files if p.name in LEGACY_WALKTHROUGHS]` BINDING THAT ONLY IT READS. BOTH LINES GO TOGETHER AND THAT IS NOT TIDINESS, IT IS A GATE: `exempt` has exactly one reader in the file (that assertion), so deleting the assertion alone leaves an unused local and `ruff check tests/test_walkthrough_id6.py` FAILS with `F841 Local variable 'exempt' is assigned to but never used` (measured by doing it; ruff 0.16.3 exits 1). This literal is a SEPARATE defect from E-01's with separate reasoning, which is why it is a separate item: E-01's literal counts a tree that GROWS by design, whereas this one counts a hand-written module-level constant in the same file, so it is redundant in a second way (it restates `len(LEGACY_WALKTHROUGHS)` against a set the reader can see) on top of being stale the moment the grandfathered population is ever corrected. `LEGACY_WALKTHROUGHS` ITSELF IS RETAINED, deliberately, and DO NOT DELETE IT while noticing it is a redundant FILTER: measured, all 11 of its members have NO identity slot, so the loop's own `if not token: continue` already skips every one of them and removing the set would change no outcome today. It stays because the plan that introduced it (`nrqo90` E-06) required the grandfathering be STATED rather than silently relied upon ("Exempt the 11 legacy names (no identity slot) explicitly, so the test states the grandfathering rather than silently skipping"), and because that redundancy is exactly what would stop a future legacy rename from being silently swept into the exempt population. `BULLETLESS_GRANDFATHERED` is NOT redundant and is equally retained: measured, its single member carries a real slot (`35xfvu`) and declares no `- Id:`, so it WOULD be reported if the filter were dropped.
  - Depends on: E-01
  - Expected outcome: both lines absent; `ruff check tests/test_walkthrough_id6.py` reports `All checks passed!`; both module-level grandfathering sets still present and still read by the loop; the retained assertion still turns RED on a genuine identity defect.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- P16 GOVERNS THIS FILE TWICE OVER, and the second half is the part that decides the remedy. `GUIDING_PRINCIPLES.md` Section 16 prohibits count pins ("No count or census pins"), and its "When tests depend on the live checkout or environment" subsection gives an ORDERED procedure: synthesize the input FIRST, reach for a collection-time marker such as `livecorpus` SECOND, and a runtime skip only THIRD. It also warns against the failure this plan must avoid: "Never weaken an assertion so it passes everywhere ... A test that asserts nothing proves nothing."
- THE MARKER IS NOT A FREE ACTION. `pyproject.toml`'s `markers` entry documents `livecorpus` as "asserts a property over EVERY artifact in this repository's own .aw/records/ tree, so ANY agent writing a plan can turn it red", and `addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"` deselects it by default. P16's own text names the cost: a marked test runs "only under `make test-all` and at release-review", since `.github/workflows/tests.yml` runs `python -m pytest tests/ -n auto -rfEs` with no `-m ''`.
- THE RETAINED ASSERTION AGREES WITH THE SHIPPED CHECKER BY CONSTRUCTION, and that constrains how it may be rewritten. It reads declarations through `check_engine._identity_declared_values` and slots through `check_engine._identity_slot_token`, which `nrqo90` E-06 chose deliberately "so the test and the checker agree on what 'declared in the metadata region' means and a quoted example cannot satisfy it". Any reformulation must keep using those helpers rather than a hand-written regex.
- THE INVARIANT IS A DOCUMENTED DECISION, NOT A TEST-LOCAL PREFERENCE. `.aw/records/walkthroughs/README.md` states it: "The `<id6>` in the filename identity slot is the walkthrough's OWN unique identity (DECISIONS.md D140): a walkthrough MUST mint its own id6 there and MUST NOT reuse the id6 of the plan it documents", linking a walkthrough to its plan via `Target-Id:` instead.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Measurement at HEAD `e5fc7c69` | Consequence for this plan |
|---|---|---|
| F-1 | THE TRIPWIRE IS REAL AND WAS FIRED, NOT INFERRED. With the tree at 24 the file reports `4 passed`. Adding ONE conformant walkthrough (`20260930-probe-99-pr0be1-growth-probe.walkthrough.md`, declaring `- Id: pr0be1` matching its slot, nothing else wrong) turns it `1 failed, 3 passed` with `AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`. Removing the probe restores `4 passed`. | The item's central claim is confirmed by demonstration. The failure is triggered by a CORRECT change, which is what makes this a bug rather than a latent smell. |
| F-2 | THE FIX WAS APPLIED AND MEASURED, NOT JUST SPECIFIED. With both literals and the `exempt` binding removed: `ruff check` reports `All checks passed!`, the file reports `4 passed`, and re-adding the same conformant 25th walkthrough leaves it `4 passed`. | E-01 and E-02 are known-good as written. The executor is reproducing a measured result, not attempting an unproven edit. |
| F-3 | THE ITEM'S FIX IS INCOMPLETE AS STATED. Deleting only the two `assertEqual` statements and leaving `exempt` bound makes `ruff check tests/test_walkthrough_id6.py` exit 1 with `F841 Local variable 'exempt' is assigned to but never used`. Confirmed by performing exactly that partial edit. | E-02 removes the binding WITH its assertion, and V-02 requires ruff as evidence. An executor who follows the item's wording literally would leave the tree failing lint. |
| F-4 | THE VACUITY HOLE IS REAL BUT NARROW, AND THE COUNT IS THE WRONG PLUG. With zero files examined, `missing_or_mismatched == []` passes, so an EMPTIED walkthroughs tree would go unnoticed. Measured today, 12 of 24 files reach the per-file comparison (24 minus 11 legacy minus 1 bulletless). | Accepted rather than plugged with a literal, for two reasons. (a) The scenario is a records-tree deletion, which `aw check`'s inventory rules and review of the commit would surface, and which no plausible authoring mistake produces. (b) A count that fires on deletion ALSO fires on addition, which is the defect being removed; trading a live tripwire for a hypothetical one is a bad exchange. V-01 instead requires POSITIVE proof (a nonzero examined population and a real red on mutation), which is the falsifiable form of the same concern. |
| F-5 | MARKING THE CLASS `livecorpus` WORKS MECHANICALLY. Adding `@pytest.mark.livecorpus` to `TestWalkthroughDeclaredIdMatchesSlot` deselects exactly 1 test under the default `addopts`, leaving the 3 synthetic tests running, and `tests/deselect_notice.py` announces it. | The alternative remedy is genuinely available, so rejecting it needs a REASON rather than an omission. F-6 is that reason. |
| F-6 | THE MARKER WOULD OPEN A REAL COVERAGE HOLE, MEASURED AGAINST THE SHIPPED CHECKER. In a synthetic repo containing one modern-named walkthrough that declares NO `- Id:` (`20260930-probe-01-aaa111-no-declared-id.walkthrough.md`), `aw check all --agent` reports `"findings":0` and exits 0, and `check_engine.check_name_identity` and `check_engine.check_names` both return `[]`. Only a MISMATCH is caught (`check.id6-identity-slot`, reproduced on a probe declaring `- Id: zzz999` in a `bbb222` slot). `check_engine._check_identity_slots`' rule (b) explains why: a file declaring no Id passes whenever nobody else owns its slot id6. This is the same hole `nrqo90`'s review recorded ("`check.id6-identity-slot` clears on a RENAME ALONE") and is precisely why E-06 created this test. | DECISION: DO NOT MARK. This test is the repository's only guard for the missing-`- Id:` case, so marking it would remove that guard from the default suite AND from CI (which passes no `-m ''`) in exchange for nothing, since subtraction already removes the tripwire. The marker exists for tests a CORRECT change can redden; after E-01 and E-02 the only thing that reddens this one is an actual D140 violation. |
| F-7 | MUTATION SENSITIVITY SURVIVES THE SUBTRACTION, DEMONSTRATED IN BOTH DIRECTIONS. After the fix, a probe walkthrough with slot `pr0be1` declaring `- Id: wr0ng1` gives `1 failed, 3 passed` with both tokens named in the message; a probe declaring NO `- Id:` also gives `1 failed, 3 passed`; a conformant probe gives `4 passed`. | The retained assertion is not hollow, which is the P16 "never weaken" requirement. V-01 and V-02 demand these exact three probes because a green suite alone cannot distinguish a working assertion from a vacuous one. |
| F-8 | THE GRANDFATHERING SETS ARE NOT INTERCHANGEABLE. All 11 `LEGACY_WALKTHROUGHS` members return `None` from `_identity_slot_token`, so the loop's `if not token: continue` already skips them and the set is a redundant filter today. The single `BULLETLESS_GRANDFATHERED` member returns slot `35xfvu` and declares no `- Id:`, so dropping THAT set would produce a real failure. Neither set contains a name absent from the tree (no stale entries). | E-02 retains both and says why, so a later reader does not "simplify" `LEGACY_WALKTHROUGHS` away and lose the stated grandfathering, nor delete `BULLETLESS_GRANDFATHERED` and turn the suite red. |
| F-9 | NO FILE OVERLAP **WITHIN SET `structpin`**, WHICH IS WHAT WAS CHECKED AND IS NOT THE QUESTION THAT MATTERS. `b02ohu` declares five other test files, `76ic0k` declares `tests/test_no_code_structure_pins.py` (which does not yet exist) and `CONTRIBUTING.md`, `44c42h` declares `tests/test_reaskscore_composed.py` and `tests/test_term.py`. None names `tests/test_walkthrough_id6.py`. | CORRECTED AT REVIEW (PR-001): the survey was scoped to this plan's own Set and therefore MISSED an APPROVED plan in a DIFFERENT Set that declares this exact file and rewrites these exact two assertions. `Item-Dependencies: none` is correct as a statement about `structpin` and is NOT sufficient. See F-11, which is BLOCKING. |
| F-11 | BLOCKER (ADDED AT REVIEW, PR-001). **AN ALREADY-APPROVED PLAN IN ANOTHER SET OWNS THIS FILE AND THESE TWO ASSERTIONS, AND ITS INTENDED END STATE CONTRADICTS THIS PLAN'S ON TWO POINTS.** `aisk5z` (`.aw/records/plans/pending/20260929-id6slotgate-01-aisk5z-retire-the-walkthrough-identity-slot-defect-unpin-the-census.ipd.md`) carries `- Status: approved` with an `- Approval:` attestation dated 2026-09-30, declares `tests/test_walkthrough_id6.py` in its `- Scope-Paths:`, and carries `- Blocks-Release: next`. Its E-02 deletes the SAME two `assertEqual` statements this plan's E-01 and E-02 delete, so the two plans race on one file. THE CONFLICT IS NOT MERELY AN EDIT COLLISION, IT IS A DISAGREEMENT ABOUT THE END STATE: (a) `aisk5z` E-02 DELETES `LEGACY_WALKTHROUGHS` ("delete the `LEGACY_WALKTHROUGHS` literal that the second one exists to police", replacing it with the loop's existing `if not token: continue`), while this plan's E-02 and OQ-02 RETAIN it as a deliberate authored artifact; (b) `aisk5z` E-07 ADDS an anti-vacuity floor (an equality against an independently computed name-shape expectation, with E-09 proving it fires), while this plan's F-4 and its third Deferred row ACCEPT the vacuity hole and add no floor. Whichever runs second either reverts the other's decision or lands on a file that no longer matches its own prose. The two carriers are genuinely distinct (`zf1m48` here, `mw0s1y` there), so this is two real items converging on one guard, not a duplicate filing. | Read from both plan files at HEAD `a3e4d2c2`: `aisk5z`'s front matter (`- Status: approved`, `- Approval: 2026-09-30, recorded via aw ipd set: status set to approved`, `- Scope-Paths: tests/test_walkthrough_id6.py, DECISIONS.md, ...`, `- Blocks-Release: next`) and its E-02, E-07, E-09 text. Enumerated every pending plan declaring this path in `- Scope-Paths:`: exactly two, `aisk5z` and this plan. |
| F-12 | MEDIUM (ADDED AT REVIEW, PR-002). **VALIDATION ITEM 6'S BAR IS UNACHIEVABLE IN THIS CHECKOUT, AND ONE SPELLING OF THE COMMAND CRASHES.** The plan requires `python3 -m agent_workflows check all --agent` to show unchanged findings with "the expected after-state is 0". Measured: `aw check all --agent` RAISES `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'` from `agent_schema.assert_valid_agent_record` (the `next` hint embeds the worktree's absolute path), and both `aw check all --agent` and plain `aw check all` exit 1. The whole-tree `aw check` reports 51 findings across 8 rules, none of which this plan can affect. So an executor holding item 6 would either chase a crash it did not cause or try to drive a pre-existing finding set to zero. | `AW_NO_REEXEC=1 python3 -m agent_workflows check all --agent` -> traceback ending `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'`, exit 1. `check all` (no `--agent`) -> exit 1. `aw check` rule breakdown: 33 `check.plan-spec-link-missing`, 6 `check.ipd-lint-diagnostic`, 5 `check.ipd-carrier-finished-unverified`, 2 `check.scope-path-target-stale`, and 1 each of `check.system-layout-missing`, `check.scope-drift`, `check.lifecycle-transition-invalid`, `check.ipd-uncarried-obligation`. |
| F-13 | MEDIUM (ADDED AT REVIEW, PR-003). **THE SUITE BASELINE IS NOT GREEN AND VALIDATION ITEM 5 WOULD READ THE RED AS THIS PLAN'S.** The bare suite reports `1 failed, 3457 passed, 2 skipped`, failing `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`. That failure is TIME-DEPENDENT and unrelated to walkthroughs: `agent_workflows/backlog.py` stamps history dates from the LOCAL clock while `agent_workflows/status_set.py` uses UTC, so the test is red for the part of every day when the two dates differ (`TZ=UTC` passes). It is filed three times as a release-blocking `bug` (`fnb8pl`, `lq2w86`, `2wae2x`) and belongs to another party. The plan's item 5 cites `b02ohu`'s `3246 passed, 2 skipped` and says to re-derive, which is right in spirit, but it frames the bar as a pass count with "no new failure" rather than as an unchanged FAILURE SET. | Bare `python3 -m pytest` at HEAD `a3e4d2c2`: `1 failed, 3457 passed, 2 skipped, 3 warnings in 69.37s`. `TZ=UTC python3 -m pytest tests/test_backlog.py -o addopts="" -k release_exempt` -> `3 passed`. Local date `2026-09-30`, UTC `2026-10-01`. |
| F-10 | `76ic0k`'S GUARD WOULD NOT HAVE CAUGHT THIS AND WILL NOT CATCH ITS RETURN. That plan detects production-source READS (`ast.parse`, `inspect.getsource`) in test modules; this test reads RECORD files, not production source, and its own plan states the count shape "is undecidable syntactically" and is an accepted bound. | Recorded in Deferred rather than fixed here. No mechanical guard stops a census literal being re-added, so the protection is P16's text plus review. |

## Proposed changes (ordered, validatable)

1. Remove the live-tree census assertion (E-01), which is the assertion that actually fires.
2. Remove the grandfather-set census together with the binding it orphans (E-02), keeping lint green.
3. Prove both directions on the real tree with throwaway probes that are removed again (V-01, V-02): a conformant
   25th walkthrough must be GREEN where HEAD is RED, and a mismatched or absent `- Id:` must still be RED.

## Deferred / out of scope (with reason)

- A MECHANICAL GUARD AGAINST A CENSUS LITERAL RETURNING. F-10: the general case is owned by `76ic0k`, whose
  scope is source-read detection and whose own text records count-shape detection as syntactically undecidable
  and therefore an accepted bound. Writing a bespoke detector for this one file here would be a new
  content pin over a test module, which is the mechanism that plan exists to argue about, on a file it does
  not claim. No carrier is filed, because the bound is already recorded in `76ic0k`.
  - Carrier-Declined: the general case is an accepted, recorded bound in live sibling plan `76ic0k` (Set `structpin`, Order 02), which owns the author-time guard and states count-shape detection as syntactically undecidable; nothing is left unowned here and a bespoke per-file detector would be a new content pin this plan does not claim
- IMPROVING THE RETAINED FAILURE MESSAGE TO NAME THE ONE-BULLET REMEDY. When the assertion does fire, its
  message reports `slot id6=... , declared in metadata region=None` but does not tell the author to add
  `- Id: <slot>`. That is a genuine usability gap and the population most likely to hit it is a HAND-WRITTEN
  walkthrough (the programmatic producer `set_records.write_walkthrough` always writes the bullet, asserted by
  `test_write_walkthrough_mints_own_id6`). It is nonetheless NOT swept in: the item scopes this carrier to the
  two literals, the message is not part of the defect, and touching the assertion's text while claiming to
  preserve it invites exactly the hollowing-out V-01 is written to detect. No carrier is filed; this is a
  cosmetic improvement, not an obligation.
  - Carrier-Declined: a cosmetic message improvement on an assertion that is correct and correctly sensitive (F-7), not a defect; the invariant it reports is fully enforced today, so there is no outstanding work to carry, and editing the assertion's text while claiming to preserve it is the exact hollowing-out V-01 exists to detect
- THE VACUOUS-PASS-ON-EMPTY-TREE CASE. F-4, accepted with reasons, replaced by positive-reach evidence in V-01
  rather than by a count. NOTED AT REVIEW (F-11): the approved sibling `aisk5z` reaches the OPPOSITE disposition,
  adding a floor in its E-07 computed from an INDEPENDENT name-shape rule and proving it fires in E-09. It also
  measured, and recorded, the trap this plan does not discuss: a floor whose expected side is computed from the
  same discriminator under test stays true under a normalizer regression and is therefore vacuous. If the
  maintainer resolves OQ-03 in favour of this plan, that measurement should be carried across rather than lost.
  - Carrier-Declined: an accepted bound argued on measurement in F-4, not deferred work: the scenario is a
    records-tree deletion no authoring mistake produces, and the only mechanism that would catch it is the
    census literal this plan removes, so filing a carrier would be filing the defect back as its own remedy.
    The alternative disposition is not unowned either: it is authored and approved in `aisk5z` E-07/E-09, which
    OQ-03 surfaces for decision
- ANY CHANGE TO `check_engine` TO CLOSE THE MISSING-`- Id:` HOLE F-6 MEASURES. That hole is a property of
  `_check_identity_slots` rule (b), whose docstring explicitly warns against widening it ("DO NOT 'fix' this by
  adding a declared-duplicate case here"), and `nrqo90` already decided to work WITH it by adding this test
  rather than changing the rule. Re-litigating that decision is out of scope for a subtraction. The hole is
  why the marker is refused (F-6), which is the only bearing it has here.
  - Carrier-Declined: a decided design property, not outstanding work: `_check_identity_slots`' own docstring
    forbids widening it and `nrqo90` already resolved to work with it by adding this very test, so the
    coverage is in place and re-litigating that decision is out of scope for a subtraction

## Scope check

- Over-scope: none. One file, two deleted assertions, one deleted dead binding, nothing added.
- CROSS-PLAN COLLISION (added at review, F-11): the declared path `tests/test_walkthrough_id6.py` is ALSO
  declared by the APPROVED plan `aisk5z` in Set `id6slotgate`, which deletes the same two assertions and wants a
  different end state. This is not a scope error in either plan taken alone; it is an ownership question only a
  maintainer can settle, and it is escalated as BLOCKING open question OQ-03. Until it is answered, this plan's
  `Scope-Paths` overlaps a plan that may legitimately run first.
- Under-scope: this plan does not prevent a census literal from being written again (F-10), does not close the
  `aw check` blindness to a missing `- Id:` (F-6, deliberately left to its owning rule), and does not make the
  retained assertion non-vacuous on an emptied tree (F-4, which `aisk5z` E-07 DOES address, and which is one of
  the two substantive differences OQ-03 asks the maintainer to weigh). Each is named above with its reason.

## Required tests / validation

Outcome tests only; no production source is read and no source text is asserted. The evidence is behavioral and
must be PASTED, per the execution contract:

1. `ruff check tests/test_walkthrough_id6.py` -> `All checks passed!` (this is the F-3 gate, not a formality).
2. `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` -> `4 passed`. The cleared `addopts` is
   required to see the per-test count, per AGENTS.md ("clear the defaults explicitly with
   `python3 -m pytest -o addopts=""`").
3. GROWTH PROBE (the fix): create one conformant walkthrough under `.aw/records/walkthroughs/` whose declared
   `- Id:` equals its filename identity slot, re-run the file, observe `4 passed`, then DELETE the probe and
   confirm the tree is back to 24 files with `4 passed` again. The probe is a throwaway and MUST NOT be
   committed.
4. MUTATION PROBES (the anti-hollowing gate): with a probe whose declared `- Id:` disagrees with its slot,
   the file must FAIL; with a probe declaring no `- Id:` at all, it must FAIL. Both probes deleted afterwards.
5. Bare whole suite `python3 -m pytest`, pasted with its summary line. THE BAR IS AN UNCHANGED NAMED FAILURE
   SET, NOT A PASS COUNT AND NOT GREEN (F-13, corrected at review). Re-derive the baseline on the tree as you
   find it BEFORE any edit and record WHICH tests fail, then require the after-set identical. Measured at
   review: `1 failed, 3457 passed, 2 skipped`, the failure being
   `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, which is
   the pre-existing local-versus-UTC history-date skew (`fnb8pl`, `lq2w86`, `2wae2x`; `TZ=UTC` passes) and is
   unrelated to walkthroughs. Do NOT report it as this plan's failure, do NOT fix it, and do NOT set `TZ` to
   hide it: it is another party's release-gated bug and touching it is what the shared-checkout rule forbids.
   The authored numbers (`b02ohu`'s `3246`, and any count written here) are context only; a risen pass count is
   expected as lanes land.
6. `python3 -m agent_workflows check` -> UNCHANGED named finding set, re-derived on the tree as found.
   CORRECTED AT REVIEW (F-12): the authored bar ("`check all --agent` -> unchanged findings ... expected
   after-state is 0") is UNACHIEVABLE here and one spelling CRASHES. Measured: `aw check all --agent` raises
   `ValueError: Invalid aw.agent/v1 record: Unsanitized absolute home path in field 'next'` from
   `agent_schema.assert_valid_agent_record`, and both `check all --agent` and plain `check all` exit 1. The
   whole-tree `aw check` exits 1 with 51 findings across 8 rules, none of which this plan can affect. So: run
   plain `aw check`, capture the RULE BREAKDOWN before and after, and require them IDENTICAL; do not require
   exit 0 and do not require zero findings. The narrow claim the authored item was reaching for IS worth
   keeping and is achievable: `check_engine.check_collisions(REPO_ROOT, include_retired=True)` returns 0
   findings of every rule, so assert THAT separately. No probe may remain when any of this runs.

## Spec / documentation sync

N/A with reason. This plan deletes two test assertions and changes no behavior, no CLI surface, and no record
grammar, so no `.spec.md` is amended and `Scope-Paths` declares no spec file. Specifically NOT edited:
`.aw/records/walkthroughs/README.md`, whose "the 11 pre-cutover legacy names stay valid" sentence remains
accurate because `LEGACY_WALKTHROUGHS` is retained (F-8); and `GUIDING_PRINCIPLES.md` P16, which already
prohibits census pins and needs no amendment to justify this removal.

## Open questions

### OQ-01: Should the class be marked `livecorpus` instead of, or in addition to, deleting the literals?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED ON MEASUREMENT: NO, neither instead nor in addition. "Instead" is
  refused because it treats the symptom: the census would still be wrong (P16 prohibits the shape outright) and
  would still fire at `make test-all` and at release-review, merely later and at a worse moment. "In addition"
  is refused because after E-01 and E-02 nothing a CORRECT change does can redden this test (F-7), so the
  marker's blast-radius rationale no longer applies, while its cost is concrete and measured: marking removes
  the test from the default suite AND from CI (`.github/workflows/tests.yml` passes no `-m ''`), and F-6 shows
  this test is the repository's ONLY guard for a walkthrough that declares no `- Id:`, since `aw check all`
  reports 0 findings on exactly that case. Paying a real coverage hole to fix a tripwire subtraction already
  removes is a bad trade. This follows P16's own ordering, which puts the marker SECOND and warns it is "the
  wrong trade for a test that should simply be made location-independent"; removing the count is what makes
  this test count-independent.

### OQ-03: An APPROVED plan in another Set (`aisk5z`) already owns this file and these two assertions, and wants a different end state. Which plan should do this work, and what happens to the other?

- Blocking: yes
- Finding: PR-001
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: UNRESOLVED AND BLOCKING. This is a SCOPE AND PRIORITY decision that belongs to the maintainer, not to a reviewer, because either answer retires somebody's approved or reviewed work and the two plans disagree on the deliverable rather than merely racing on a file.

  THE FACTS (F-11, measured at review, HEAD `a3e4d2c2`). `aisk5z` carries `- Status: approved` with an `- Approval:` attestation dated 2026-09-30, declares `tests/test_walkthrough_id6.py` in `- Scope-Paths:`, carries `- Blocks-Release: next`, and its E-02 deletes the SAME two `assertEqual` statements this plan deletes. Exactly two pending plans declare this path; those are the two. The carriers are genuinely distinct (`zf1m48` here, `mw0s1y` there), so this is two real items converging on one guard rather than a duplicate filing.

  WHERE THE TWO PLANS DISAGREE, which is why ordering alone does not fix it:
  - `LEGACY_WALKTHROUGHS`. `aisk5z` E-02 DELETES it, arguing the loop's existing `if not token: continue` is the shipped discriminator and the literal is redundant (review independently confirmed all 11 members return `None` from `_identity_slot_token`, so it changes no outcome today). This plan's E-02 and OQ-02 RETAIN it, arguing `nrqo90` E-06 required the grandfathering be STATED rather than silently relied upon. Both arguments are sound; they weigh a recorded decision against redundancy differently.
  - THE VACUITY FLOOR. `aisk5z` E-07 ADDS one (an equality against an INDEPENDENTLY computed name-shape expectation, with E-09 proving it fires under a simulated normalizer regression). This plan's F-4 and its third Deferred row ACCEPT the hole and deliberately add no floor. `aisk5z` also measured, and recorded, that a floor whose expected side comes from the same discriminator is vacuous, which is a real trap this plan does not address.

  WHY A REVIEWER MUST NOT DECIDE IT. Resolving this means either (a) retiring an APPROVED, release-gated plan to `superseded/`, or (b) retiring this one, or (c) narrowing one of them. Each disposes of attested work and reassigns a release gate, which is the maintainer's call under the repository's approval contract. A reviewer may not set `superseded` on an approved plan, and picking a winner silently would strand one carrier's gate.

  THE OPTIONS, with the reviewer's recommendation stated and labelled. (1) RUN `aisk5z` ALONE and retire this plan `superseded` citing it: `aisk5z` is already approved, is strictly a superset (it fixes the same tripwire AND adds the anti-vacuity floor AND corrects three stale records), and its E-07/E-09 address the one hole this plan accepts. This plan's distinct carrier `zf1m48` can close via a handoff to `aisk5z` or be noted as satisfied by it. RECOMMENDED. (2) RUN THIS PLAN ALONE and narrow `aisk5z` to its records-correction items (E-04, E-05) plus the floor, which requires re-approving a modified approved plan. (3) RUN BOTH in a declared order with the loser's test-file items removed, which costs an `- Item-Dependencies:` edge and a re-review of whichever is amended. Option 1 is recommended because it is the only one that spends no further authoring effort and loses no measured work: everything this plan measured (F-1 through F-8) is either already recorded in `aisk5z` or is preserved in this plan's record for a reader.

  UNTIL THIS IS ANSWERED THIS PLAN MUST NOT EXECUTE. `aw ipd lint` reports `IPD-Q501` at every checkpoint while this question is `open` with `- Blocking: yes`, which is the intended fail-closed behavior and not a defect to work around.

### OQ-02: Is `LEGACY_WALKTHROUGHS` now dead code that should also be deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED: NO, retain it. Measured (F-8), all 11 members lack an identity
  slot, so the loop's `if not token: continue` already skips them and the filter changes no outcome today. It is
  kept for two reasons. (a) It is a DELIBERATE authored artifact: `nrqo90` E-06 required the grandfathering be
  stated "rather than silently skipping", so deleting it would quietly undo a recorded decision. (b) It is
  defensive against a legitimate future change: if a legacy walkthrough were ever renamed into the clustered
  grammar, the named filter keeps the exemption explicit and reviewable instead of depending on the slot
  parser's behavior. Note this is the opposite disposition to the `exempt` BINDING, which E-02 does delete,
  because that binding has no reader at all once its assertion is gone (F-3) and is a lint error rather than a
  redundant-but-documenting constant.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) `rg -n "Census must find exactly" tests/test_walkthrough_id6.py` returns NO match
    (pasted, including the empty result or nonzero exit). (b) THE TRIPWIRE IS GONE, PROVEN BY THE SAME PROBE
    THAT FIRES IT AT HEAD: paste a `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` run taken
    WHILE one extra conformant walkthrough exists in `.aw/records/walkthroughs/` (declared `- Id:` equal to its
    filename identity slot), showing `4 passed`; state the probe's filename and the file count observed (25).
    For contrast, paste or cite the HEAD behavior from F-1 (`AssertionError: 25 != 24`). (c) THE ASSERTION IS
    REACHED, NOT VACUOUS (the F-4 concern in falsifiable form): paste the count of files that reach the per-file
    comparison, computed by the same filters the test uses, and show it is NONZERO (authoring measurement: 12 of
    24). (d) THE PROBE IS GONE: paste the walkthrough file count back at its pre-probe value and a final
    `4 passed`. A run that shows only (d) is INSUFFICIENT and does not satisfy this item, because a green suite
    is equally consistent with the literal still being present.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: (a) `rg -n "exempt|Must find exactly 11" tests/test_walkthrough_id6.py` returns NO match
    for either the binding or the message (pasted). (b) `ruff check tests/test_walkthrough_id6.py` pasted showing
    `All checks passed!`, which is the F-3 gate proving the dead binding went with its assertion. (c) BOTH
    GRANDFATHERING SETS SURVIVE AND ARE STILL READ: paste `rg -n "LEGACY_WALKTHROUGHS|BULLETLESS_GRANDFATHERED"`
    showing each set is both defined and referenced inside the loop. (d) MUTATION SENSITIVITY, BOTH CASES, EACH
    A SEPARATE PASTED RUN: with one probe walkthrough whose declared `- Id:` DISAGREES with its slot, the file
    FAILS and the failure message names the offending file; with one probe declaring NO `- Id:`, the file FAILS.
    (e) ALL PROBES REMOVED, then the bare whole suite `python3 -m pytest` pasted with its summary line BESIDE a
    baseline re-derived before any edit, with the FAILING TEST NAMES listed on both sides and shown IDENTICAL
    (not green; see F-13 and Required-tests item 5, and name the pre-existing clock-skew failure explicitly if
    it appears), plus plain `python3 -m agent_workflows check` pasted with its rule breakdown before and after
    shown identical (NOT `check all --agent`, which crashes here; F-12), plus
    `check_engine.check_collisions(REPO_ROOT, include_retired=True)` pasted showing 0 findings of every rule.
    (f) `git status --short`
    pasted showing `tests/test_walkthrough_id6.py` as the ONLY modified path and NO untracked walkthrough
    probe left behind. If (d) produces a PASS in either case, STOP: the retained assertion has been hollowed
    out and the plan has failed its Goal even though the suite is green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

EXECUTION IS BLOCKED ON OQ-03, WHICH IS A HUMAN DECISION AND NOT A FORMALITY. An already-APPROVED,
release-gated plan in another Set (`aisk5z`) declares this same file and deletes these same two assertions, and
it wants a DIFFERENT end state on two points (it deletes `LEGACY_WALKTHROUGHS`, which this plan retains; it adds
an anti-vacuity floor, which this plan declines). See F-11 and OQ-03. While OQ-03 is `open` with
`- Blocking: yes`, `aw ipd lint` reports `IPD-Q501` at every checkpoint and this plan cannot reach `approved`
or be dispatched. That is the intended fail-closed behavior. The reviewer's recommendation, recorded in OQ-03,
is to run `aisk5z` (already approved, a strict superset) and retire this plan `superseded` citing it; a reviewer
may not make that call, because it disposes of attested work and reassigns a release gate.

Execution is otherwise gated on explicit human approval (`- Status: approved`), per AGENTS.md. This plan is
`reviewed` and MUST NOT be executed until OQ-03 is answered AND approval is recorded. `- Readiness: no-go` is
written by this review and reflects the unresolved BLOCKING question, not a defect in the plan's own reasoning,
which review found sound and reproduced in full.

Execution contract for whoever runs it: commit ONLY `tests/test_walkthrough_id6.py`, through
`aw commit <plan> -- tests/test_walkthrough_id6.py`, never `git add -A`, and never push. THE PROBES ARE
THROWAWAY AND MUST NOT BE COMMITTED: every walkthrough file created for V-01 or V-02 is deleted before the
final suite run, and V-02 (f) exists to prove the working tree is clean of them. Creating a probe under
`.aw/records/walkthroughs/` is a records-tree write, so it must be removed even if the plan fails midway;
leaving one behind would commit a fabricated walkthrough with no plan behind it. Paste real runner output for
every item; a claimed pass with no output does not satisfy any `V-*` item here.

On success, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition (not a raw
`git mv`), only after `aw ipd lint --phase pre-transition` conforms and both `V-*` items carry pasted evidence.
Backlog `zf1m48` carries `- Blocks-Release: next`, which this plan inherits above; the item reaches `done`
through the handoff route (this plan executed while carrying `- From-Backlog: zf1m48` and the same gate), so do
not clear the gate and do not close the item by hand.

- Size assessment: standard
- Cohesion rationale: not required
