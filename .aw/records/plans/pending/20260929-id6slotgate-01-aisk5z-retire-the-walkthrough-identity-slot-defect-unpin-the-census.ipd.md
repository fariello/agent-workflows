# IPD: Retire the walkthrough identity-slot defect: unpin the census guard so it survives the next walkthrough and record the shipped remediation

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `mw0s1y` reports three walkthroughs reusing their source plan's id6 in their own filename identity slot. MEASURED IN THIS LANE AT HEAD `9434331c`, THE DATA DEFECT IS ALREADY FIXED and the item is stale: all three files were renamed and given their own `- Id:` by IPD `nrqo90` (commit `e83cb542`, "Mint a walkthrough's own id6 in write_walkthrough, add the walkthrough id6 cutover, and re-id the three D140 walkthroughs"). `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` BOTH return zero findings of every rule, so `e2j5w4`'s liveness-filter half is fixed too (by `t0jyb2`). WHAT IS STILL BROKEN IS THE GUARD nrqo90 left behind. `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id` opens with `assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")` and a hardcoded 11-name `LEGACY_WALKTHROUGHS` literal it also asserts `len(exempt) == 11` on. Measured: adding ONE fully conformant walkthrough (own `- Id:` equal to its slot, `- Target-Id:` present) reds the suite with `AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`, BEFORE the loop that checks anything. So the next walkthrough anyone writes breaks CI, and the standing repair is to bump the literal, which mechanically retires the D140 assertion.
- Scope: Close `mw0s1y` honestly and leave the invariant defended. IN: (a) rewrite the census guard's preamble to assert the D140 PROPERTY over whatever walkthroughs exist (every clustered name declares a `- Id:` equal to its slot id6) instead of pinning a population count and a name list, keeping the two real exemptions (no-identity-slot legacy names, and the one deliberately bullet-less `35xfvu` file) as DERIVED predicates rather than as a frozen census; (b) prove the rewritten guard still fails on the original defect shape by mutation, so unpinning the count does not silently unpin the rule; (c) correct the three stale records that still assert the violation is live, namely backlog `mw0s1y`, backlog `e2j5w4`, and DECISIONS D140's `sk7ggr` paragraph, whose parenthetical still says the identity-slot pass deliberately honors the liveness filter "to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions" after `t0jyb2` removed exactly that behavior. OUT: renaming any walkthrough (the renames already happened and re-renaming would rewrite cited history); minting an `- Id:` for the grandfathered `35xfvu` file; renaming the 11 legacy walkthroughs; any change to `check_engine._check_identity_slots` or to the `walkthrough_id6` cutover, both of which measure correct.
- Scope-Paths: tests/test_walkthrough_id6.py, DECISIONS.md, .aw/records/backlog/open/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md, .aw/records/backlog/open/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: mw0s1y
- Blocks-Release: next
- Set: id6slotgate
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: aisk5z

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `mw0s1y`, graduating it. Every claim below was measured in this lane at HEAD `9434331c`. THE ITEM'S PREMISE NO LONGER HOLDS AND THAT INVERTS THE WORK. The three named walkthroughs were re-id'd by IPD `nrqo90` after the item was filed, so the remediation the item asks for is DONE and re-performing it would rewrite cited history. What the measurement surfaced instead is a regression guard `nrqo90` shipped that cannot survive its own success: its census assertion reds on the next conformant walkthrough, before the D140 loop executes. The deliverable is therefore an unpinning plus three record corrections, not the rename the item describes. The item's release gate is inherited unchanged because the defect class is live until the guard defends it.

## Goal

Leave the D140 identity-slot invariant DEFENDED BY A PROPERTY rather than by a frozen census, and leave the
repository's records saying what is actually true, so `mw0s1y` can close without either a false claim that
work was performed or a silent handoff of an undefended invariant.

The backlog item asks for a rename that has already happened. Its own text anticipates this possibility and
forbids the obvious wrong move: "DO NOT RENAME THESE RECORDS WITHOUT A MAINTAINER DECISION ... Renaming a
record under `.aw/records/` rewrites tracked history that other artifacts cite by name". That decision was
subsequently taken and executed by `nrqo90`, whose E-05 cites this very item as the authority it was acting
under. So the correct response to the item is to VERIFY the remediation, fix what it left unfinished, and
correct the record; not to re-perform it.

SIX FACTS ESTABLISHED AT AUTHORING, so the executor inherits measurement rather than the item's stale
description.

1. THE THREE NAMED FILES DO NOT EXIST UNDER THE NAMES THE ITEM GIVES. Each was renamed to a freshly minted
   id6 and each now declares that id6 as its own `- Id:`, with the plan it documents demoted to the typed
   `- Target-Id:` field D140 requires. Measured over `.aw/records/walkthroughs/`, reading the slot with
   `check_engine._identity_slot_token` and the declaration with `check_engine._read_declared_id`:

   ```text
   slot=01ad6r id=01ad6r target=zpbx7o  20260901-runstop-00-01ad6r-graceful-quit-whole-set-verification.walkthrough.md
   slot=cceh3w id=cceh3w target=y5od1h  20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md
   slot=v0nmuv id=v0nmuv target=4fodkt  20260917-lanectn-07-v0nmuv-whole-set-verification-of-spec-7ckptx.walkthrough.md
   ```

   Note the third column: `zpbx7o`, `y5od1h` and `4fodkt` are exactly the three plan id6s the item names, now
   held as REFERENCES rather than as identities. The `y5od1h` file also gained the `.walkthrough.md` facet it
   lacked and the `- Target-Id:` bullet the item says it needed. `git log --follow` on the `cceh3w` file names
   commit `e83cb542` as the rename.

2. THE ITEM'S USER-PERCEPTIBLE SYMPTOM IS GONE. The item's stated effect is that "`aw find y5od1h` returns
   two artifacts for one identity". Measured:

   ```text
   $ aw find y5od1h
   ✓  executed      y5od1h  lanectn   .aw/records/plans/executed/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md
   ·  -             -                 .aw/records/reviews/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.review.md
   ```

   The second row is the plan's own REVIEW record, which legitimately shares the plan's stem and is not an
   identity claim; no walkthrough appears. `aw find 4fodkt` behaves identically and `aw find zpbx7o` returns
   one row. So the symptom that justified the `bug` classification no longer reproduces.

3. THE DETECTION HALF IS ALSO FIXED, WHICH RETIRES THE SIBLING ITEM'S PREMISE. `e2j5w4` reports that
   `check_collisions` gates the identity-slot pass on the caller's liveness filter, and predicts 0 findings
   at the default versus 3 under `include_retired=True`. Measured at HEAD:

   ```text
   include_retired= False total= 0 slot= 0
   include_retired= True total= 0 slot= 0
   ```

   Both the divergence and the findings are gone. `check_engine.check_collisions`' docstring now states
   "BOTH IDENTITY PASSES IGNORE THE LIVENESS FILTER; THE SETID PASS DOES NOT (IPD `sk7ggr` E-05, collpop
   `t0jyb2`)", and the enumeration passes `include_retired=True` unconditionally while the setid pass alone
   consults `caller_visible`. `t0jyb2`'s own Scope declares this and explicitly defers the rename to
   `mw0s1y`: "OUT: renaming the three live walkthroughs (backlog `mw0s1y`)".

4. THE GUARD `nrqo90` SHIPPED CANNOT SURVIVE THE NEXT WALKTHROUGH. `test_clustered_walkthroughs_declare_matching_id`
   asserts a population count and an exemption-list length before it checks anything. Measured by adding one
   fully conformant walkthrough (`20260930-newset-01-aaa111-a-new-walkthrough.walkthrough.md`, declaring
   `- Id: aaa111` matching its slot and a `- Target-Id:`):

   ```text
   >       self.assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")
   E       AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs
   tests/test_walkthrough_id6.py:138: AssertionError
   1 failed, 3 passed in 0.22s
   ```

   The failure is a FALSE POSITIVE: the added file satisfies D140 exactly. The cheap repair a future author
   will reach for is bumping `24` to `25`, which keeps the test green while teaching everyone that the census
   number is the thing being defended. That is how this guard stops guarding.

5. THE GUARD'S REAL ASSERTION DOES WORK, SO IT MUST BE PRESERVED, NOT REPLACED. Measured by reproducing the
   original defect shape at an UNCHANGED census size (deleting the `- Id: cceh3w` bullet from the `cceh3w`
   walkthrough, leaving 24 files):

   ```text
   E       "20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md: slot id6='cceh3w', declared in metadata region=None"
   tests/test_walkthrough_id6.py:160: AssertionError
   1 failed, 3 passed in 0.24s
   ```

   That is the D140 rule firing correctly on the exact shape the backlog item describes. The work is to keep
   this failure while removing the one in fact 4, which is why the deliverable is a rewrite of the preamble
   and not a deletion of the test.

6. THE TWO EXEMPTIONS ARE BOTH LEGITIMATE AND BOTH DERIVABLE, so neither needs a frozen literal. The 11
   `LEGACY_WALKTHROUGHS` names are exactly the files for which `check_engine._identity_slot_token` returns
   `None` (measured: 24 total, 13 clustered, 11 with no identity slot, and the 11 match the literal set), so
   the exemption is computable from the shipped normalizer that already decides the question. The single
   `BULLETLESS_GRANDFATHERED` entry is `20260823-35xfvu-01-35xfvu-...` and its grandfathering is recorded in
   commit `9a1c4206`: "The awoptimize walkthrough has bullets, so it gains '- Id: 4533x3'; the other two have
   none and keep their id6 in the filename only". Measured, `35xfvu` appears in no other file's `- Id:` and in
   no other filename, so it is the sole holder of that id6 and satisfies `_check_identity_slots` rule (b),
   which is why `aw check` is silent on it. It stays a NAMED exemption of exactly one file, because unlike
   the legacy set it is a per-file historical concession and not a derivable class.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-establish the baseline before changing anything

- [ ] E-01 CAPTURE THE PRE-CHANGE BASELINE AND RE-VERIFY THE SIX AUTHORING FACTS AT THE EXECUTION HEAD, because this plan's entire shape rests on the claim that the remediation already shipped, and executing it against a tree where that is false would be the greenwashing the repository contract forbids. Record, with output: the walkthrough census (slot id6, declared `- Id:`, `- Target-Id:` for every file under `.aw/records/walkthroughs/`, read via `check_engine._identity_slot_token` and `check_engine._read_declared_id`, not by hand-written regex); `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` finding counts broken out by rule; `aw find y5od1h`, `aw find 4fodkt`, `aw find zpbx7o`; a bare `python3 -m pytest` run; and `aw check` output. IF THE THREE OLD FILENAMES STILL EXIST ON DISK, or either collision call returns a `check.id6-identity-slot` finding, STOP and report: the tree is not the one this plan was authored against, and the correct response is a fresh plan rather than proceeding.
  - Depends on: none
  - Expected outcome: the census shows every clustered walkthrough's slot equal to its own declared `- Id:` except the grandfathered `35xfvu` file; both collision calls return zero findings of every rule; the three `aw find` calls return no walkthrough; and a baseline suite summary line plus a baseline `aw check` count are on record for later comparison.
  - Execution state: pending

### Task group 2: unpin the guard without unpinning the rule

- [ ] E-02 REWRITE THE CENSUS PREAMBLE OF `test_clustered_walkthroughs_declare_matching_id` SO IT ASSERTS THE PROPERTY, NOT THE POPULATION. Delete the `assertEqual(len(all_files), 24, ...)` assertion and the `assertEqual(len(exempt), 11, ...)` assertion, and delete the `LEGACY_WALKTHROUGHS` literal that the second one exists to police. Derive the legacy exemption instead: a file is exempt iff `check_engine._identity_slot_token(p.name)` returns falsey, which is the shipped normalizer's own answer to "does this name have an identity slot" and is already the discriminator the checker uses (fact 6 measured the derived set equals the literal set exactly). KEEP `BULLETLESS_GRANDFATHERED` as an explicit one-name frozenset with its `9a1c4206` provenance comment, because that one is a per-file historical concession rather than a derivable class, and a reader must be able to see it is exactly one file. Assert instead that the directory is non-empty and that at least one clustered walkthrough was actually examined, so the test cannot pass vacuously by examining nothing (the failure mode a derived exemption introduces). Report the examined count in the assertion message. Do NOT change the loop body, which fact 5 measured to work: it must keep reading the declaration through `check_engine._identity_declared_values` so the test and the checker agree on what "declared in the metadata region" means and a quoted example cannot satisfy it.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` reports 4 passed, and the test no longer contains any hardcoded walkthrough count or legacy-name list.
  - Execution state: pending

- [ ] E-03 PROVE THE UNPINNING BY THE TWO MUTATIONS THAT DEFINE IT, since "the count is gone" and "the rule still fires" are independent claims and E-02 is only correct if both hold. FIRST, add a conformant walkthrough to `.aw/records/walkthroughs/` (own `- Id:` equal to its slot id6, a `- Target-Id:` naming some executed plan, minted with `artifact_core.mint_id6` so it cannot collide), run the test, observe PASS where fact 4 measured a census failure, then REMOVE the file and re-run. SECOND, with the tree restored, delete one conformant walkthrough's `- Id:` bullet, run the test, observe the fact-5 failure naming that file and its slot id6, then `git checkout --` the file and re-run. Both temporary files/edits MUST be gone before this plan commits; verify with `git status --short` showing a clean `.aw/records/walkthroughs/`. Add NO permanent fixture under `.aw/records/`: the repository tree is a records tree, not a test fixture directory, and leaving a synthetic walkthrough behind would corrupt the very census this test reads.
  - Depends on: E-02
  - Expected outcome: pasted PASS with the extra conformant walkthrough present (the fact-4 false positive is gone), pasted FAILURE naming the file whose `- Id:` was removed (the fact-5 true positive survives), and `git status --short` clean for the walkthroughs directory afterwards.
  - Execution state: pending

### Task group 3: correct the records that still assert a live defect

- [ ] E-04 CORRECT DECISIONS D140's `sk7ggr` PARAGRAPH, which is now wrong about shipped behavior in a way that would mislead the next author of this code. Its item (2) states the id6 pass now ignores the liveness filter and adds the parenthetical "(its setid and identity-slot neighbours deliberately do NOT, to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions)". `t0jyb2` changed exactly that: `check_collisions` now enumerates with `include_retired=True` unconditionally and only the setid pass consults `caller_visible`, and its docstring says so. APPEND a new dated `Applied` bullet rather than rewriting the `sk7ggr` bullet in place, matching how that bullet itself was appended beneath the older "Enforcement gap identified" paragraph it superseded and why it says it "is deliberately left intact rather than rewritten": D140's value is partly as a record of what was believed when. The new bullet states that the identity-slot pass now consumes the terminal-inclusive corpus too (naming `t0jyb2`), that the "walkthrough-slot convention" the parenthetical treated as legitimate was ruled a DEFECT by `.aw/records/walkthroughs/README.md` and remediated by `nrqo90`, and that the three files are now conformant, citing the fact-1 census. Write no em or en dashes.
  - Depends on: E-01
  - Expected outcome: the `git diff` of `DECISIONS.md` shows one appended dated bullet under D140 and no modification to any existing bullet.
  - Execution state: pending

- [ ] E-05 CORRECT BOTH BACKLOG ITEMS' MEASUREMENTS WITHOUT TOUCHING THEIR REQUIREMENTS, since each still presents a remediated defect as live and each is `Blocks-Release: next`, so a release reviewer reading them would believe two blockers are outstanding. Append to `mw0s1y` a dated paragraph recording that the three renames shipped in `nrqo90` (commit `e83cb542`), that the `aw find` symptom no longer reproduces, and that the residual work is the census guard this plan fixes. Append to `e2j5w4` a dated paragraph recording that `t0jyb2` gave the identity-slot pass the terminal-inclusive corpus its "SUGGESTED FIX" asked for, and that both collision calls now return zero. DO NOT edit either item's existing measurement text: its whole value is as the record of what was true on 2026-09-21, and `nrqo90`'s E-07 deliberately preserved these two items byte-identical for that reason ("KEEP unchanged: ... (iii) the measurement text in backlog items `mw0s1y` and `e2j5w4`, which describe the defect as it was"). DO NOT change either item's `- Status:`, which this plan's authoring contract reserves to the runner, and DO NOT change `- Blocks-Release:`. Use `aw backlog note` if that verb exists for appending history; otherwise append the paragraph directly and say which you did and why.
  - Depends on: E-04
  - Expected outcome: the `git diff` of both backlog files shows only appended text, with every pre-existing line including the three old walkthrough filenames unchanged, and with `- Status:` and `- Blocks-Release:` untouched.
  - Execution state: pending

### Task group 4: regression gate

- [ ] E-06 RUN THE FULL REGRESSION GATE and compare it against the E-01 baseline, so any failure is shown pre-existing rather than argued harmless. Run bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Then `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its E-01 baseline count, and `aw sanitize --agent`. ALSO re-run the fact-1 census one final time, because E-03 temporarily added and removed a file under `.aw/records/walkthroughs/` and the cheapest way this plan could do damage is to leave residue there.
  - Depends on: E-03, E-05
  - Expected outcome: suite summary line pasted beside the E-01 baseline with no new failure; a conforming pre-transition lint; `aw check` no worse than baseline with both counts pasted; a clean sanitizer report; and a final census identical to E-01's.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE. AGENTS.md forbids tests that read production source with `inspect`/`ast`/regex or that assert symbol censuses and line counts as proxies for correctness (GUIDING_PRINCIPLES P16). The guard this plan repairs is a borderline case worth naming: it reads the RECORDS TREE rather than source code, which is legitimate (the records are the subject), but its census assertion is the same anti-pattern one level out, pinning a POPULATION SIZE as a proxy for a property. E-02 moves it onto the property.
- THE NAMING AUTHORITY IS A SINGLE SOURCE AND MUST BE CONSULTED, NOT REIMPLEMENTED. `check_engine._identity_slot_token` documents itself as using "the naming authority's clustered parse (single source, IPD o6b8l3)" and carries the `_HHMM_RE` exclusion that keeps a legacy `YYYYMMDD-HHMM-NN-<slug>` name from being misread as clustered. E-02 derives the legacy exemption from it for exactly that reason; a hand-written regex would re-introduce the bug that exclusion exists to prevent.
- A RECORD UNDER `.aw/records/` IS APPENDED TO, NOT REWRITTEN. D140's `sk7ggr` bullet states the convention explicitly for itself ("deliberately left intact rather than rewritten"), and `nrqo90`'s E-07 applied the same rule to these two backlog items and to fenced command transcripts in `t0jyb2`. E-04 and E-05 both append.
- `aw check` IS SILENT ON THE `35xfvu` FILE FOR A STATED REASON, not by oversight: `_check_identity_slots` rule (b) requires only that a file declaring no `- Id:` be the SOLE holder of its slot id6, and measurement confirms `35xfvu` appears in no other file's identity or filename. So the test's exemption and the checker's silence agree, and neither is a hole this plan should close.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-1 | The three walkthroughs `mw0s1y` names were renamed and given their own `- Id:`, with the plan id6 demoted to `- Target-Id:`. The item's remediation is DONE. | Goal fact 1 census; `git log --follow` on the `cceh3w` file naming commit `e83cb542`; `nrqo90` E-05 execution state `performed`. |
| F-2 | The item's user-perceptible symptom (`aw find y5od1h` returning two artifacts for one identity) no longer reproduces; the second row is the plan's own review record, not an identity claim. | Goal fact 2 `aw find` output for all three id6s. |
| F-3 | Sibling item `e2j5w4`'s liveness-filter defect is also fixed, by `t0jyb2`. Both collision calls return zero findings of every rule, so its predicted 0-versus-3 divergence is gone. | Goal fact 3; `check_collisions` docstring "BOTH IDENTITY PASSES IGNORE THE LIVENESS FILTER"; the unconditional `include_retired=True` in its enumeration. |
| F-4 | The regression guard `nrqo90` shipped reds on the NEXT conformant walkthrough, before its D140 loop runs, and the cheap repair (bump the literal) mechanically retires the assertion. This is the live residue. | Goal fact 4 pasted `AssertionError: 25 != 24`. |
| F-5 | The guard's actual D140 assertion works and fires on the exact defect shape the item describes, so it must be preserved rather than replaced. | Goal fact 5 pasted failure naming `slot id6='cceh3w', declared in metadata region=None`. |
| F-6 | Both exemptions are legitimate; the 11-name legacy list is exactly the derivable no-identity-slot class, while the one bullet-less file is a per-file concession recorded in commit `9a1c4206`. | Goal fact 6 counts (24 total, 13 clustered, 11 slotless) and the quoted commit message. |

## Proposed changes (ordered, validatable)

1. Re-verify the six facts at the execution HEAD and capture the suite and `aw check` baselines, refusing to
   proceed if the tree still holds the old filenames or any identity-slot finding (E-01 / V-01).
2. Replace the guard's census preamble with a property assertion: drop the hardcoded 24 and the 11-name
   literal, derive the legacy exemption from `check_engine._identity_slot_token`, keep the one-file
   bullet-less concession named, and add an anti-vacuity floor that reports the examined count (E-02 / V-02).
3. Demonstrate the unpinning by two mutations, one proving the false positive is gone and one proving the
   true positive survives, leaving no residue in the records tree (E-03 / V-03).
4. Append a dated `Applied` bullet to DECISIONS D140 correcting the parenthetical that still calls the
   walkthrough-slot shape a legitimate convention the checker deliberately tolerates (E-04 / V-04).
5. Append dated measurement corrections to both backlog items, leaving their requirements, statuses, gates
   and original measurement text untouched (E-05 / V-05).
6. Run the full regression gate against the baseline and re-check the records tree for residue (E-06 / V-06).

## Deferred / out of scope (with reason)

- RENAMING ANY WALKTHROUGH. Already done by `nrqo90`; re-renaming would rewrite names other artifacts cite
  and would be the history damage `mw0s1y` itself warns against.
- MINTING AN `- Id:` FOR THE GRANDFATHERED `35xfvu` WALKTHROUGH. Its bullet-less state is a recorded
  concession (commit `9a1c4206`) and it satisfies `_check_identity_slots` rule (b) as the sole holder of its
  id6, so there is no defect to fix. Adding bullets to a historical record is a separate decision with its
  own cost and belongs to a maintainer, not to this plan.
- RENAMING THE 11 LEGACY WALKTHROUGHS. Explicitly out of scope in `nrqo90` ("OUT: renaming the 11
  grandfathered legacy walkthroughs") and grandfathered by the `walkthrough_id6` cutover, which measured at
  `20260927` and returns `False` from `_walkthrough_requires_id6` for every one of them.
- ANY CHANGE TO `check_engine._check_identity_slots`, its corpus, or the `walkthrough_id6` cutover. All
  measure correct at HEAD; changing a passing gate to close a stale ticket is how a real rule gets narrowed.
- CLOSING `e2j5w4`. It is a separate item with its own id6 and its own gate. This plan corrects its
  measurement so a reviewer is not misled, and deliberately does not touch its `- Status:`: a second item's
  closure is not this plan's authority, and `aw check`'s close-legitimacy predicate is the right gate for it.

## Scope check

- Over-scope: none. Each of the four declared paths is touched by exactly one task group: the test by E-02
  and E-03, `DECISIONS.md` by E-04, and the two backlog items by E-05. No product code under
  `agent_workflows/` is changed, which is deliberate: every code path this plan investigated measured
  correct, and the defect is in a test and in three records.
- Under-scope: the plan changes NO product behavior, so no user-visible surface, CLI output, or check rule
  moves. A reader expecting `mw0s1y` to produce a rename or a checker change will find neither, and facts 1
  and 3 are the evidence that neither is needed. The `.aw/records/walkthroughs/` tree appears in no declared
  path even though E-03 temporarily writes there, because that write is transient and E-03 and E-06 both
  verify it is gone; if any walkthrough file is still modified at finalize time, the scope gate SHOULD refuse
  and that refusal is the intended signal, not an obstacle to work around by widening this list.

## Required tests / validation

The subject of this plan IS a test, so the validation standard is higher than usual: a green run proves
nothing on its own, because the failure mode being fixed is a test that passes while asserting the wrong
thing. Every claim about the guard is therefore demonstrated by MUTATION, in both directions.

- The fix direction: with one extra CONFORMANT walkthrough present, the test must PASS where fact 4 measured
  `AssertionError: 25 != 24`. This is the defect being closed.
- The preservation direction: with a conformant walkthrough's `- Id:` bullet deleted, the test must FAIL
  naming that file and its slot id6, reproducing fact 5. This is the rule being kept.
- The anti-vacuity direction: the test must report how many clustered walkthroughs it examined, and that
  count must be greater than zero, so a future change to the derived exemption cannot make the test pass by
  examining nothing.
- Residue: `git status --short` must show `.aw/records/walkthroughs/` clean after the mutations, and E-06
  re-runs the fact-1 census to confirm it.
- The gate: bare `python3 -m pytest` compared against the E-01 baseline, `aw ipd lint --phase pre-transition`
  conforming, `aw check` no worse than baseline, `aw sanitize --agent` clean.

No test may read production source text to satisfy any item here. The DECISIONS and backlog edits are
verified by `git diff` inspection, not by a test asserting a document contains a string.

## Spec / documentation sync

No spec amendment, and the reason is that the two governing documents already say what this plan implements.
`.aw/records/walkthroughs/README.md` states the D140 rule, names the enforcing rule id, and already documents
the `walkthrough_id6` cutover and the grandfathered legacy names, all of which `nrqo90` E-08 landed. Spec
`20260817-2147-01-uniform-artifact-naming-grammar`'s walkthrough row was amended by the same plan. This plan
changes a test and corrects three records; it changes no contract, so no `.spec.md` file is declared in
`- Scope-Paths:` and the runners' spec-edit announcement will correctly report none.

The DOCUMENTATION correction this plan does make is D140's own `sk7ggr` paragraph (E-04). That is a decision
record rather than a spec, and it is corrected by APPENDING a dated bullet, which is the convention that
paragraph states for itself.

## Open questions

### OQ-01: Should the grandfathered bullet-less `35xfvu` walkthrough eventually receive an `- Id:` bullet, or is its exemption permanent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as out of scope, permanently for this plan and open as a maintainer question. The exemption is a recorded concession, not an oversight: commit `9a1c4206` states "the other two have none and keep their id6 in the filename only", and one of that pair was later re-id'd by `nrqo90` leaving this single file. It is also not a live defect by the checker's own rule: `_check_identity_slots` rule (b) requires a file declaring no `- Id:` to be the sole holder of its slot id6, and measurement confirms `35xfvu` appears in no other file's `- Id:` and in no other filename, so `aw check` is correctly silent. Adding metadata bullets to a historical narrative record is a change to tracked history with no defect driving it, which this plan's own scope forbids. E-02 therefore keeps it as a NAMED one-file exemption with its provenance comment, which is the shape that makes the concession visible to the next reader rather than hiding it inside a derived predicate.

### OQ-02: Does correcting `mw0s1y`'s measurement rather than performing its stated remediation legitimately close it?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM THE REPOSITORY'S OWN CLOSE-LEGITIMACY CONTRACT. AGENTS.md's handoff fix requires "an EXECUTED plan (or an implemented spec) carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>`", which this plan is and does. The gate is therefore preserved rather than dropped, and the item reaches `graduated` on authoring and `done` only when this plan executes. The substantive question underneath is whether a plan that does NOT perform the item's stated action may carry it, and the answer here is yes for a specific reason: facts 1 through 3 measure that the action was already performed by `nrqo90`, so performing it again is impossible, and the item's residual obligation (an invariant left defended only by a guard that breaks on the next walkthrough) IS carried by this plan's E-02 and E-03. What this plan must NOT do is claim to have performed the renames, which is why E-05 appends a correction naming `nrqo90` as the actor rather than rewriting the item to look satisfied.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted walkthrough census (one line per file with slot id6, declared `- Id:`, and `- Target-Id:`), showing the three `nrqo90` names present and the three item-named names ABSENT; pasted `check_collisions` counts for both `include_retired` values broken out by rule, both zero for `check.id6-identity-slot`; pasted `aw find` output for `y5od1h`, `4fodkt` and `zpbx7o` with no walkthrough row; and the baseline bare `python3 -m pytest` summary line plus baseline `aw check` count recorded for E-06 to compare against. State explicitly that the refusal condition (old filenames present, or any identity-slot finding) did NOT trigger.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `git diff` of `tests/test_walkthrough_id6.py` showing the `assertEqual(len(all_files), 24, ...)` and `assertEqual(len(exempt), 11, ...)` assertions and the `LEGACY_WALKTHROUGHS` literal all removed, the legacy exemption derived from `check_engine._identity_slot_token`, `BULLETLESS_GRANDFATHERED` retained with its provenance comment, and an anti-vacuity assertion that reports the examined count. Plus pasted `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` output showing 4 passed, and a grep-free confirmation from the diff that no hardcoded walkthrough count or legacy filename remains in the test. State the examined count the new assertion reports.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: THREE pasted runs for the fix direction (PASS with the extra conformant walkthrough present, the file removed, PASS again) and THREE for the preservation direction (PASS at rest, FAILURE naming the file whose `- Id:` was deleted together with its slot id6, PASS after `git checkout --`). The failure output must name the file, matching fact 5's shape. Plus `git status --short` pasted showing no modified or untracked file under `.aw/records/walkthroughs/`, and a statement of how the synthetic walkthrough's id6 was minted so it could not collide. A green run with no paired failure does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of `DECISIONS.md`, shown to contain ONLY an added bullet under D140 with no `-` line removing or altering any existing bullet (state how that was confirmed from the diff). The added text must name `t0jyb2` as the change that gave the identity-slot pass the terminal-inclusive corpus, must state that the "walkthrough-slot convention" the earlier parenthetical tolerated was ruled a defect by the walkthroughs README and remediated by `nrqo90`, and must cite the census. Confirm the added prose contains no em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` of both backlog files, shown to be append-only, with the three old walkthrough filenames still present verbatim in each item's original measurement text and with `- Status:` and `- Blocks-Release:` unchanged on both (paste those two lines from each file after the edit). Plus a statement of whether `aw backlog note` was used or the paragraph was appended directly, and why. Any `-` line in either diff other than a trailing-newline artifact fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted beside the E-01 baseline line, so any failure is shown pre-existing rather than introduced; `aw ipd lint --phase pre-transition` on this plan reporting conforming; `aw check` counts before and after pasted with the after no worse; `aw sanitize --agent` reporting zero findings; and the final walkthrough census pasted and stated to be identical to E-01's, proving E-03 left no residue.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is an
output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

THE EXECUTOR MUST TREAT E-01 AS A HARD GATE. This plan asserts that the defect `mw0s1y` describes was already
remediated, and every later item rests on that. If the E-01 census finds the three old filenames, or either
collision call returns a `check.id6-identity-slot` finding, the tree is not the one this plan was authored
against: STOP, report, and do not proceed into E-02. Proceeding would produce a plan that claims to have
verified a remediation it did not observe.

The executor must further: perform E-01 through E-06 respecting the declared `Depends on` edges; commit only
the four paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner output
for every claim of a passing test, INCLUDING the paired mutation failure E-03 requires; leave
`.aw/records/walkthroughs/` byte-identical to its pre-execution state; and verify each `V-*` in a pass
separate from the `E-*` that produced it. Do NOT mark this plan executed or move it to
`.aw/records/plans/executed/` until every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms.

THE EXECUTOR MUST NOT change the `- Status:` of either backlog item, nor either item's `- Blocks-Release:`.
`mw0s1y` reaches `graduated` by the runner's own transition on this plan's authoring and `done` only once
this plan is `executed`, which is what preserves its release gate through the handoff. `e2j5w4` is a separate
item that this plan corrects but does not close.

Backlog item `mw0s1y` is this plan's origin (`- From-Backlog: mw0s1y`) and its `- Blocks-Release: next` gate
is inherited here unchanged. The gate is kept even though the item's original symptom no longer reproduces,
because the defect CLASS is still undefended: the only regression test standing between the repository and a
recurrence is the one that fact 4 measures as breaking on the next walkthrough anyone writes. When E-02 and
E-03 land, that is no longer true, and the gate is legitimately satisfied rather than merely cleared.
