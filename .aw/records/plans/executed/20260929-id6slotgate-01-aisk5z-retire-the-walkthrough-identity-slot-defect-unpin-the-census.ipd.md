# IPD: Retire the walkthrough identity-slot defect: unpin the census guard so it survives the next walkthrough and record the shipped remediation

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `mw0s1y` reports three walkthroughs reusing their source plan's id6 in their own filename identity slot. MEASURED IN THIS LANE AT HEAD `9434331c`, THE DATA DEFECT IS ALREADY FIXED and the item is stale: all three files were renamed and given their own `- Id:` by IPD `nrqo90` (commit `e83cb542`, "Mint a walkthrough's own id6 in write_walkthrough, add the walkthrough id6 cutover, and re-id the three D140 walkthroughs"). `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` BOTH return zero findings of every rule, so `e2j5w4`'s liveness-filter half is fixed too (by `t0jyb2`). WHAT IS STILL BROKEN IS THE GUARD nrqo90 left behind. `tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id` opens with `assertEqual(len(all_files), 24, "Census must find exactly 24 walkthroughs")` and a hardcoded 11-name `LEGACY_WALKTHROUGHS` literal it also asserts `len(exempt) == 11` on. Measured: adding ONE fully conformant walkthrough (own `- Id:` equal to its slot, `- Target-Id:` present) reds the suite with `AssertionError: 25 != 24 : Census must find exactly 24 walkthroughs`, BEFORE the loop that checks anything. So the next walkthrough anyone writes breaks CI, and the standing repair is to bump the literal, which mechanically retires the D140 assertion.
- Scope: Close `mw0s1y` honestly and leave the invariant defended. IN: (a) rewrite the census guard's preamble to assert the D140 PROPERTY over whatever walkthroughs exist (every clustered name declares a `- Id:` equal to its slot id6) instead of pinning a population count and a name list, keeping the two real exemptions (no-identity-slot legacy names, and the one deliberately bullet-less `35xfvu` file) as DERIVED predicates rather than as a frozen census; (b) prove the rewritten guard still fails on the original defect shape by mutation, so unpinning the count does not silently unpin the rule; (c) correct the three stale records that still assert the violation is live, namely backlog `mw0s1y`, backlog `e2j5w4`, and DECISIONS D140's `sk7ggr` paragraph, whose parenthetical still says the identity-slot pass deliberately honors the liveness filter "to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions" after `t0jyb2` removed exactly that behavior. OUT: renaming any walkthrough (the renames already happened and re-renaming would rewrite cited history); minting an `- Id:` for the grandfathered `35xfvu` file; renaming the 11 legacy walkthroughs; any change to `check_engine._check_identity_slots` or to the `walkthrough_id6` cutover, both of which measure correct.
- Scope-Paths: tests/test_walkthrough_id6.py, DECISIONS.md, .aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md, .aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mw0s1y
- Blocks-Release: next
- Set: id6slotgate
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: aisk5z

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: aisk5z verified (set id6slotgate, attempt 1).
- 2026-09-30 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 through PR-010, all FIXED in place. Reviewed at HEAD `9bf03bd9` in an isolated lane; typed record at `.aw/records/reviews/20260929-id6slotgate-01-aisk5z-retire-the-walkthrough-identity-slot-defect-unpin-the-census.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after revision, so nothing found was structural.
  ALL SIX AUTHORING FACTS RE-DERIVED AND ALL SIX HOLD, including both mutations: adding one conformant walkthrough still reds `AssertionError: 25 != 24` and deleting the `cceh3w` file's `- Id:` still fires `slot id6='cceh3w', declared in metadata region=None`. So the plan's inversion of backlog `mw0s1y` is correct and its residue diagnosis stands.
  FOUR HIGH FINDINGS, TWO OF THEM RULES ALREADY FIRING ON THIS PLAN. PR-001: both declared backlog paths pointed at `open/` while the runner had moved the items to `graduated/` 35 seconds after the plan commit, which `check.scope-path-target-stale` reports at `error`; retargeted. PR-002: five deferred rows named no durable carrier, which `check.ipd-uncarried-obligation` reports at `error` while the sibling plan `dta75n` carries the fields on every row; typed `Carrier`/`Carrier-Evidence`/`Carrier-Declined` added. PR-003: E-02's instruction to derive the legacy exemption from `_identity_slot_token` was DEAD CODE, measured three ways (literal, pre-filter, and no exemption all return `examined=12, failures=[]`) because the loop's own `if not token: continue` already does it; the instruction now forbids the redundant branch. PR-004: that left the anti-vacuity floor as the only new protection, and BOTH plausible forms of it are vacuous, measured by simulating two normalizer regressions: `examined > 0` passes while examining 1 of 12, and `examined == expected` with both sides from `_identity_slot_token` stayed true at `12/12`, `9/9`, `0/0`; new E-07 computes the expectation from an independent legacy-name-shape rule, which fails those same regressions at `9 != 12` and `0 != 12`.
  SIX FURTHER FINDINGS COMPLETED THE SWEEP. PR-005 applied the plan's own mutation standard to the assertion it ADDED rather than only to the two it kept (new E-09 must paste the floor failing). PR-006 gave the gate the scope fence and the conditional runner/executor finalize ownership it lacked. PR-007 split E-03's three bundled mutation surfaces into E-03/E-08/E-09 via `aw ipd sync` after `IPD-Z602` flagged the density. PR-008 replaced E-05's "if that verb exists" conditional with the verified `aw backlog note` invocation. PR-009 made the `aw check` baseline comparison per-rule, since two of this review's own fixes legitimately lower the total by three. PR-010 corrected `mint_id6` to carry its required `repo_root` positional.
  ONE IRREVERSIBLE DECISION RECORDED AND ESCALATED (D-6): the test must NOT be narrowed toward `aw check`, because a walkthrough with a unique slot id6 and no declared `- Id:` satisfies `_check_identity_slots` rule (b) as sole holder and returns `Counter()` from `check_collisions`, while the test's loop fails it. Measured in a scratch repo; surfaced to the maintainer in the review report rather than as a blocking question, because the decision is to change nothing.

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

- [x] E-01 CAPTURE THE PRE-CHANGE BASELINE AND RE-VERIFY THE SIX AUTHORING FACTS AT THE EXECUTION HEAD, because this plan's entire shape rests on the claim that the remediation already shipped, and executing it against a tree where that is false would be the greenwashing the repository contract forbids. Record, with output: the walkthrough census (slot id6, declared `- Id:`, `- Target-Id:` for every file under `.aw/records/walkthroughs/`, read via `check_engine._identity_slot_token` and `check_engine._read_declared_id`, not by hand-written regex); `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` finding counts broken out by rule; `aw find y5od1h`, `aw find 4fodkt`, `aw find zpbx7o`; a bare `python3 -m pytest` run; and `aw check` output. IF THE THREE OLD FILENAMES STILL EXIST ON DISK, or either collision call returns a `check.id6-identity-slot` finding, STOP and report: the tree is not the one this plan was authored against, and the correct response is a fresh plan rather than proceeding.
  - Depends on: none
  - Expected outcome: the census shows every clustered walkthrough's slot equal to its own declared `- Id:` except the grandfathered `35xfvu` file; both collision calls return zero findings of every rule; the three `aw find` calls return no walkthrough; and a baseline suite summary line plus a baseline `aw check` count are on record for later comparison.
  - Execution state: performed

### Task group 2: unpin the guard without unpinning the rule

- [x] E-02 REWRITE THE CENSUS PREAMBLE OF `test_clustered_walkthroughs_declare_matching_id` SO IT ASSERTS THE PROPERTY, NOT THE POPULATION. Delete the `assertEqual(len(all_files), 24, ...)` assertion and the `assertEqual(len(exempt), 11, ...)` assertion, and delete the `LEGACY_WALKTHROUGHS` literal that the second one exists to police. The legacy exemption becomes the loop's EXISTING `if not token: continue` guard, which is the shipped normalizer's own answer to "does this name have an identity slot" and is already the discriminator the checker uses (fact 6 measured the derived set equals the literal set exactly). DO NOT ADD A SEPARATE DERIVED-EXEMPTION BRANCH: measured at review, `if p.name in LEGACY_WALKTHROUGHS` and a `not _identity_slot_token(p.name)` pre-filter are BOTH redundant with that guard, returning identical `(examined=12, failures=[])` whether the pre-filter is present, absent, or replaced by no exemption at all, so adding one would be dead code a later reader must re-derive the harmlessness of. KEEP `BULLETLESS_GRANDFATHERED` as an explicit one-name frozenset with its `9a1c4206` provenance comment, because that one is a per-file historical concession rather than a derivable class, and a reader must be able to see it is exactly one file. Do NOT change the loop body, which fact 5 measured to work: it must keep reading the declaration through `check_engine._identity_declared_values` so the test and the checker agree on what "declared in the metadata region" means and a quoted example cannot satisfy it.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` reports 4 passed, and the test no longer contains any hardcoded walkthrough count or legacy-name list.
  - Execution state: performed

- [x] E-07 ADD THE ANTI-VACUITY FLOOR AS AN EQUALITY AGAINST AN INDEPENDENT DISCRIMINATOR, because removing the population assertion removes the only thing that made silent under-examination visible, and the two cheaper floors both measurably fail. FIRST, "examined > 0" is too weak: the eligible population measured 12 at review, so that floor passes while examining 1 of 12. SECOND, and this is the trap to avoid, an equality whose EXPECTED side is also computed from `_identity_slot_token` is VACUOUS, measured at review by simulating two normalizer regressions: one recognizing only `202609*` names and one recognizing none, both of which kept `examined == expected` true (`12/12`, then `9/9`, then `0/0`) because the regression moved both sides together. So compute the EXPECTED side from an INDEPENDENT NAME-SHAPE RULE: a file is expected to be examined iff its name does NOT match the legacy `YYYYMMDD-HHMM-NN-` prefix shape and is not in `BULLETLESS_GRANDFATHERED`. Measured at review, that expectation equals the shipped normalizer's answer exactly (12 == 12) while the same two simulated regressions now FAIL it (`9 != 12` and `0 != 12`), which is the whole point. Assert that equality, assert the walkthroughs directory is non-empty, and report both counts in the assertion message so a failure says which side moved. Write the legacy-shape regex as a LOCAL TEST CONSTANT with a comment stating it is deliberately independent of `check_engine` so the test can disagree with the normalizer, and that collapsing it onto `_identity_slot_token` to "remove duplication" would make the assertion vacuous again. This is the ONE place this plan permits a second implementation of a naming question, and the Project-conventions note on single-source naming is amended below to record why. Add no count literal.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` reports 4 passed; the assertion message names both the examined count and the independently computed expectation; and the test file contains no integer literal standing for a walkthrough population.
  - Execution state: performed

Mutation-hygiene rule governing E-03, E-08 and E-09 below (stated once rather than repeated in each): every mutation is TEMPORARY. Revert it by PATH NAME before the next item, never with `git stash`, a bare `git reset`, or `git checkout .`, since this checkout may be shared. Add NO permanent fixture under `.aw/records/` and NO committed test double: the repository tree is a records tree, not a test fixture directory, and a synthetic walkthrough left behind would corrupt the very census this test reads.

- [x] E-03 PROVE THE FIX DIRECTION: THE FALSE POSITIVE IS GONE. Add ONE conformant walkthrough to `.aw/records/walkthroughs/`, with its own `- Id:` equal to its filename slot id6 and a `- Target-Id:` naming some executed plan, minting the id6 with `artifact_core.mint_id6(repo_root)` so it cannot collide (note the REQUIRED positional `repo_root`, measured at review: a bare `mint_id6()` raises `TypeError: mint_id6() missing 1 required positional argument: 'repo_root'`). Run the test and observe PASS, where fact 4 measured `AssertionError: 25 != 24` before E-02. Then REMOVE the file and re-run to confirm the tree is back at rest. This is the defect the plan exists to close, and it is the one direction a green suite alone could never demonstrate.
  - Depends on: E-07
  - Expected outcome: three pasted runs (PASS with the extra walkthrough present, the file removed, PASS again) plus the minted id6 and the `repo_root` argument used, and `git status --short` clean for `.aw/records/walkthroughs/`.
  - Execution state: performed

- [x] E-08 PROVE THE PRESERVATION DIRECTION: THE D140 RULE STILL FIRES. With the tree at rest, delete ONE conformant walkthrough's `- Id:` bullet, run the test, and observe the fact-5 failure naming that file together with its slot id6 (measured at review on the `cceh3w` file: `slot id6='cceh3w', declared in metadata region=None`). Then `git checkout --` that file and re-run to confirm PASS. This is the rule being KEPT, and it is why the deliverable is a preamble rewrite rather than a deletion of the test: E-02 is only correct if this failure survives it.
  - Depends on: E-03
  - Expected outcome: three pasted runs (PASS at rest, FAILURE naming the file and its slot id6, PASS after restore), with the failure output matching fact 5's shape.
  - Execution state: performed

- [x] E-09 PROVE THE FLOOR DIRECTION: SILENT UNDER-EXAMINATION IS CAUGHT. This is what makes E-07 more than an assertion nobody has watched fail. Temporarily narrow the slot discriminator the test consults, inside the test run only, so it recognizes only names beginning `202609`, then run the test and observe the E-07 equality FAIL with BOTH counts named (measured at review: `9 != 12`). Restore and re-run to confirm PASS. Do this as an in-run monkeypatch or a local wrapper, NOT as a committed test double, and do NOT add a permanent test that patches `check_engine`. If this mutation does NOT fail the test, E-07's expected side is still computed from the discriminator under test and E-07 must be reworked before this item can pass.
  - Depends on: E-08
  - Expected outcome: two pasted runs (FAILURE of the E-07 equality under the narrowed discriminator with both counts visible, then PASS after restoring) and `git status --short` clean for `agent_workflows/`.
  - Execution state: performed

### Task group 3: correct the records that still assert a live defect

- [x] E-04 CORRECT DECISIONS D140's `sk7ggr` PARAGRAPH, which is now wrong about shipped behavior in a way that would mislead the next author of this code. Its item (2) states the id6 pass now ignores the liveness filter and adds the parenthetical "(its setid and identity-slot neighbours deliberately do NOT, to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions)". `t0jyb2` changed exactly that: `check_collisions` now enumerates with `include_retired=True` unconditionally and only the setid pass consults `caller_visible`, and its docstring says so. APPEND a new dated `Applied` bullet rather than rewriting the `sk7ggr` bullet in place, matching how that bullet itself was appended beneath the older "Enforcement gap identified" paragraph it superseded and why it says it "is deliberately left intact rather than rewritten": D140's value is partly as a record of what was believed when. The new bullet states that the identity-slot pass now consumes the terminal-inclusive corpus too (naming `t0jyb2`), that the "walkthrough-slot convention" the parenthetical treated as legitimate was ruled a DEFECT by `.aw/records/walkthroughs/README.md` and remediated by `nrqo90`, and that the three files are now conformant, citing the fact-1 census. Write no em or en dashes.
  - Depends on: E-01
  - Expected outcome: the `git diff` of `DECISIONS.md` shows one appended dated bullet under D140 and no modification to any existing bullet.
  - Execution state: performed

- [x] E-05 CORRECT BOTH BACKLOG ITEMS' MEASUREMENTS WITHOUT TOUCHING THEIR REQUIREMENTS, since each still presents a remediated defect as live and each is `Blocks-Release: next`, so a release reviewer reading them would believe two blockers are outstanding. Append to `mw0s1y` a dated paragraph recording that the three renames shipped in `nrqo90` (commit `e83cb542`), that the `aw find` symptom no longer reproduces, and that the residual work is the census guard this plan fixes. Append to `e2j5w4` a dated paragraph recording that `t0jyb2` gave the identity-slot pass the terminal-inclusive corpus its "SUGGESTED FIX" asked for, and that both collision calls now return zero. DO NOT edit either item's existing measurement text: its whole value is as the record of what was true on 2026-09-21, and `nrqo90`'s E-07 deliberately preserved these two items byte-identical for that reason ("KEEP unchanged: ... (iii) the measurement text in backlog items `mw0s1y` and `e2j5w4`, which describe the defect as it was"). DO NOT change either item's `- Status:`, which this plan's authoring contract reserves to the runner, and DO NOT change `- Blocks-Release:`. USE `aw backlog note <id6> --message '<text>'`, WHICH EXISTS: verified at review from `aw backlog note --help`, which documents it as appending "a workflow-history record to a backlog item WITHOUT changing its status or moving its file" and takes an id6, filename, stem, or path selector. The earlier conditional wording is removed because it invited a hand append the tooled path already covers. Note the mechanical consequence, so the evidence is read correctly: the verb writes into the `## Workflow history` block near the TOP of the item, not at the end of the file, so the `git diff` will show the addition high in the file while the measurement prose below stays untouched; that is the correct shape, not a sign the wrong thing moved. BOTH ITEMS ARE NOW UNDER `graduated/`, so select them by id6 rather than by a path built from `open/`. If the verb refuses, STOP and report rather than hand-editing around it.
  - Depends on: E-04
  - Expected outcome: the `git diff` of both backlog files shows only appended text, with every pre-existing line including the three old walkthrough filenames unchanged, and with `- Status:` and `- Blocks-Release:` untouched. The addition appears inside each item's `## Workflow history` block (the verb's documented placement), not appended at end of file.
  - Execution state: performed

### Task group 4: regression gate

- [x] E-06 RUN THE FULL REGRESSION GATE and compare it against the E-01 baseline, so any failure is shown pre-existing rather than argued harmless. Run bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Then `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its E-01 baseline count, and `aw sanitize --agent`, which is not a formality here because E-03's probe output may contain temp-directory paths. ALSO re-run the fact-1 census one final time, because E-03 temporarily added and removed a file under `.aw/records/walkthroughs/` and E-09 temporarily narrowed a discriminator, and the cheapest way this plan could do damage is to leave residue in either place. FINALLY confirm with `git status --short` that the modified set is EXACTLY the four declared Scope-Paths, with nothing under `.aw/records/walkthroughs/` and no change to `agent_workflows/`. Restore any residue by path name, never with `git stash`, a bare `git reset`, or `git checkout .`, since this checkout may be shared. WHEN COMPARING `aw check`, compare the RULE BREAKDOWN and not only the total: two of this plan's own review fixes (`check.scope-path-target-stale` on the two backlog paths, and `check.ipd-uncarried-obligation` on the deferred rows) were findings against THIS plan at review, so the baseline should already be lower by three findings than it was before review; a total that merely fails to grow can hide a new finding offsetting a resolved one.
  - Depends on: E-09, E-05
  - Expected outcome: suite summary line pasted beside the E-01 baseline with no new failure; a conforming pre-transition lint; `aw check` no worse than baseline with both counts AND both rule breakdowns pasted; a clean sanitizer report; a final census identical to E-01's; and a `git status --short` showing exactly the four declared paths.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE. AGENTS.md forbids tests that read production source with `inspect`/`ast`/regex or that assert symbol censuses and line counts as proxies for correctness (GUIDING_PRINCIPLES P16). The guard this plan repairs is a borderline case worth naming: it reads the RECORDS TREE rather than source code, which is legitimate (the records are the subject), but its census assertion is the same anti-pattern one level out, pinning a POPULATION SIZE as a proxy for a property. E-02 moves it onto the property.
- THE NAMING AUTHORITY IS A SINGLE SOURCE AND MUST BE CONSULTED, NOT REIMPLEMENTED, WITH ONE NAMED EXCEPTION. `check_engine._identity_slot_token` documents itself as using "the naming authority's clustered parse (single source, IPD o6b8l3)" and carries the `_HHMM_RE` exclusion that keeps a legacy `YYYYMMDD-HHMM-NN-<slug>` name from being misread as clustered. E-02 therefore leans on it for the exemption itself (via the loop's existing `if not token: continue`) and adds no second parse there. THE EXCEPTION IS E-07'S EXPECTED SIDE, and the reason is that a test whose expectation is computed by the very function under scrutiny cannot detect that function regressing: measured at review, an equality with both sides derived from `_identity_slot_token` stayed true (`12/12`, `9/9`, `0/0`) across two simulated normalizer regressions. So E-07's legacy-shape regex is a DELIBERATE second implementation, confined to the expectation side, whose whole value is that it can disagree with the normalizer. It is not a violation of the single-source convention but the standard reason a test asserts an outcome independently of the code producing it; the convention governs PRODUCTION parsing, which this plan does not touch.
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
| F-7 | ADDED AT REVIEW. The legacy exemption needs no new derived predicate at all, because the loop's pre-existing `if not token: continue` already performs it. Measured over the live tree, the loop returns identical `(examined=12, failures=[])` with the `LEGACY_WALKTHROUGHS` literal, with a `_identity_slot_token` pre-filter, and with NO exemption whatsoever. So E-02's original instruction to add a derived pre-filter would have produced dead code. | Review probe over `.aw/records/walkthroughs/` comparing the three exemption shapes; E-02 as revised. |
| F-8 | ADDED AT REVIEW. An anti-vacuity floor is only meaningful if its expected side is INDEPENDENT of the discriminator under test. A `examined > 0` floor passes while examining 1 of 12, and an `examined == expected` floor with both sides from `_identity_slot_token` survived two simulated normalizer regressions (`12/12`, `9/9`, `0/0`). Recomputing the expectation from an independent legacy-name-shape rule keeps `12 == 12` at rest and fails both regressions (`9 != 12`, `0 != 12`). | Review probe simulating a narrowed and an empty normalizer; E-07 and V-07. |
| F-9 | ADDED AT REVIEW. The plan's two declared backlog paths pointed at `open/` while the runner had already moved both items to `graduated/` (commits `0f777712`, `4eec8292`), so `check.scope-path-target-stale` reported both at severity `error`, and its five deferred rows named no durable carrier, so `check.ipd-uncarried-obligation` reported at `error` too. Both are fixed in place; the rule is silent on this plan afterwards. | `ce.stale_record_scope_paths` and `ce.check_durable_carrier` before and after the fix, both returning empty for this plan. |

## Proposed changes (ordered, validatable)

1. Re-verify the six facts at the execution HEAD and capture the suite and `aw check` baselines, refusing to
   proceed if the tree still holds the old filenames or any identity-slot finding (E-01 / V-01).
2. Replace the guard's census preamble with a property assertion: drop the hardcoded 24 and the 11-name
   literal, let the loop's existing slot guard carry the legacy exemption rather than adding a redundant
   pre-filter, and keep the one-file bullet-less concession named (E-02 / V-02).
2b. Add the anti-vacuity floor as an equality between the examined count and an INDEPENDENTLY computed
   expectation (a local legacy-name-shape rule), because an equality derived from the same normalizer the
   test scrutinizes was measured vacuous across two simulated regressions (E-07 / V-07).
3. Demonstrate the unpinning by three mutations: the false positive is gone, the true positive survives, and
   the new floor fails under a narrowed discriminator, leaving no residue in the records tree (E-03 / V-03,
   E-08 / V-08, E-09 / V-09).
4. Append a dated `Applied` bullet to DECISIONS D140 correcting the parenthetical that still calls the
   walkthrough-slot shape a legitimate convention the checker deliberately tolerates (E-04 / V-04).
5. Append dated measurement corrections to both backlog items, leaving their requirements, statuses, gates
   and original measurement text untouched (E-05 / V-05).
6. Run the full regression gate against the baseline and re-check the records tree for residue (E-06 / V-06).

## Deferred / out of scope (with reason)

- RENAMING ANY WALKTHROUGH. Already done by `nrqo90`; re-renaming would rewrite names other artifacts cite
  and would be the history damage `mw0s1y` itself warns against.
  - Carrier-Evidence: .aw/records/plans/executed/20260926-wkthid6-01-nrqo90-mint-a-walkthrough-s-own-id6-in-write-walkthrough-add-the-wa.ipd.md
- MINTING AN `- Id:` FOR THE GRANDFATHERED `35xfvu` WALKTHROUGH. Its bullet-less state is a recorded
  concession (commit `9a1c4206`) and it satisfies `_check_identity_slots` rule (b) as the sole holder of its
  id6, so there is no defect to fix. Adding bullets to a historical record is a separate decision with its
  own cost and belongs to a maintainer, not to this plan.
  - Carrier-Declined: nobody's task, because there is no defect to carry. Measured at review: `35xfvu` appears in no other file's `- Id:` and in no other filename, so it satisfies `_check_identity_slots` rule (b) as the sole holder of its id6 and `aw check` is correctly silent on it. Naming a carrier would schedule an edit to tracked history that no rule asks for. OQ-01 records the maintainer-facing question if anyone later wants it reopened.
- RENAMING THE 11 LEGACY WALKTHROUGHS. Explicitly out of scope in `nrqo90` ("OUT: renaming the 11
  grandfathered legacy walkthroughs") and grandfathered by the `walkthrough_id6` cutover, which measured at
  `20260927` and returns `False` from `_walkthrough_requires_id6` for every one of them.
  - Carrier-Declined: grandfathered by shipped contract, not postponed. `_walkthrough_requires_id6` returns `False` for all 11 (re-measured at review over the whole directory), and `.aw/records/walkthroughs/README.md` states "the 11 pre-cutover legacy names stay valid". A carrier here would own work the repository's own cutover exempts permanently.
- ANY CHANGE TO `check_engine._check_identity_slots`, its corpus, or the `walkthrough_id6` cutover. All
  measure correct at HEAD; changing a passing gate to close a stale ticket is how a real rule gets narrowed.
  - Carrier-Declined: there is no outstanding work to carry. Both collision calls return zero findings of every rule at HEAD and the corpus is terminal-inclusive by contract, so this row records a NON-task; naming a carrier would assert someone still owes a behavior fix that nobody owes.
- CLOSING `e2j5w4`. It is a separate item with its own id6 and its own gate. This plan corrects its
  measurement so a reviewer is not misled, and deliberately does not touch its `- Status:`: a second item's
  closure is not this plan's authority, and `aw check`'s close-legitimacy predicate is the right gate for it.
  - Carrier: dta75n

## Scope check

- Over-scope: none. Each of the four declared paths is touched by exactly one task group: the test by E-02,
  E-07, E-03, E-08 and E-09, `DECISIONS.md` by E-04, and the two backlog items by E-05. No product code under
  `agent_workflows/` is changed, which is deliberate: every code path this plan investigated measured
  correct, and the defect is in a test and in three records. NOTE THE DECLARED BACKLOG PATHS ARE
  `graduated/`, not `open/`: the runner moved both items when this plan was authored (commits `0f777712` and
  `4eec8292`), and the original `open/` declarations were corrected at review after `check.scope-path-target-stale`
  reported both as `moved`. If either item has moved again by execution time, re-derive the path rather than
  assuming this one.
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
- The anti-vacuity direction: the test must report how many clustered walkthroughs it examined AND an
  independently computed expectation, and assert they are EQUAL. A bare "greater than zero" floor is
  explicitly insufficient (it passes while examining 1 of 12), and so is an equality whose expected side is
  computed from `_identity_slot_token`, which was measured vacuous across two simulated normalizer
  regressions. This direction is itself demonstrated by mutation in E-09, because an assertion
  nobody has watched fail is not yet known to work.
- Residue: `git status --short` must show `.aw/records/walkthroughs/` AND `agent_workflows/` clean after the
  mutations, and E-06 re-runs the fact-1 census to confirm it.
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
- Resolution or deferral rationale: RESOLVED FROM THE REPOSITORY'S OWN CLOSE-LEGITIMACY CONTRACT. AGENTS.md's handoff fix requires "an EXECUTED plan (or an implemented spec) carrying `- From-Backlog: <this id6>` and the same `- Blocks-Release: <R>`", which this plan is and does. The gate is therefore preserved rather than dropped, and the item reaches `graduated` on authoring and `done` only when this plan executes. The substantive question underneath is whether a plan that does NOT perform the item's stated action may carry it, and the answer here is yes for a specific reason: facts 1 through 3 measure that the action was already performed by `nrqo90`, so performing it again is impossible, and the item's residual obligation (an invariant left defended only by a guard that breaks on the next walkthrough) IS carried by this plan's E-02 and E-07, demonstrated by E-03, E-08 and E-09. What this plan must NOT do is claim to have performed the renames, which is why E-05 appends a correction naming `nrqo90` as the actor rather than rewriting the item to look satisfied.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted walkthrough census (one line per file with slot id6, declared `- Id:`, and `- Target-Id:`), showing the three `nrqo90` names present and the three item-named names ABSENT; pasted `check_collisions` counts for both `include_retired` values broken out by rule, both zero for `check.id6-identity-slot`; pasted `aw find` output for `y5od1h`, `4fodkt` and `zpbx7o` with no walkthrough row; and the baseline bare `python3 -m pytest` summary line plus baseline `aw check` count recorded for E-06 to compare against. State explicitly that the refusal condition (old filenames present, or any identity-slot finding) did NOT trigger.
  - Observed evidence: PASS. Six authoring facts re-verified at execution HEAD; details below.
    Walkthrough census gathered via check_engine._identity_slot_token and check_engine._read_declared_id:
    ```text
    Total walkthrough files: 24
    slot=None   id=None   target=None   20260712-1023-01-installer-shim-detection-ctrlc-and-diff-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1033-01-assess-bugs-and-tests-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1038-01-fix-installer-shim-tests-left-red-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1041-01-agents-docs-research-and-walkthroughs-convention-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1049-01-scope-review-gemini-bugs-tests-execution-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1100-01-1028-falsely-marked-executed-tests-still-red-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1200-01-ux-and-data-modeling-principles-import-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1230-01-mirror-workflow-pointer-into-native-agent-files-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260810-2052-01-awphysical-01-rejected-greenwashed-execution-corrective-review.walkthrough.md
    slot=None   id=None   target=None   20260812-0300-01-awphysical-overnight-autonomous-execution-01-to-10-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260812-1200-01-order11-self-migration-decision-record-walkthrough.walkthrough.md
    slot=4533x3 id=4533x3 target=None   20260821-4533x3-01-4533x3-awoptimize-rescope.walkthrough.md
    slot=35xfvu id=None   target=None   20260823-35xfvu-01-35xfvu-highpbacklog0822-execution-decisions.walkthrough.md
    slot=hey7r7 id=hey7r7 target=p7dqwz 20260823-artifactenginefix-01-hey7r7-execution.walkthrough.md
    slot=5gdzyz id=5gdzyz target=y6mfgo 20260831-locksafe-01-5gdzyz-one-cross-platform-file-lock-walkthrough.walkthrough.md
    slot=01ad6r id=01ad6r target=zpbx7o 20260901-runstop-00-01ad6r-graceful-quit-whole-set-verification.walkthrough.md
    slot=cceh3w id=cceh3w target=y5od1h 20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md
    slot=ryn48z id=ryn48z target=s16omw 20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md
    slot=pi4wof id=pi4wof target=yrqyxb 20260917-eiclosure-01-pi4wof-execute-item-closure-measured-not-split.walkthrough.md
    slot=ztmh1b id=ztmh1b target=orziju 20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md
    slot=v0nmuv id=v0nmuv target=4fodkt 20260917-lanectn-07-v0nmuv-whole-set-verification-of-spec-7ckptx.walkthrough.md
    slot=zogmmg id=zogmmg target=3dki3o 20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md
    slot=k2vn8p id=k2vn8p target=ty3cj6 20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md
    slot=u8tiox id=u8tiox target=3v7wo6 20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    ```
    The three nrqo90 names (01ad6r, cceh3w, v0nmuv) are present with matching declared id6 and typed Target-Id, and the three item-named names are ABSENT.
    Pasted check_collisions finding counts:
    ```text
    include_retired=False total: 0
    include_retired=True total: 0
    ```
    Zero findings for check.id6-identity-slot and all rules.
    Pasted aw find outputs:
    ```text
    $ aw find y5od1h
    ✓  executed      y5od1h  lanectn         .aw/records/plans/executed/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.ipd.md
    ·  -             -  .aw/records/reviews/20260901-lanectn-04-y5od1h-bounded-missing-input-repair-without-original-checkout-acces.review.md

    $ aw find 4fodkt
    ✓  executed      4fodkt  lanectn         .aw/records/plans/executed/20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.ipd.md
    ·  -             -  .aw/records/reviews/20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.review.md

    $ aw find zpbx7o
    ✓  executed      zpbx7o  runstop         .aw/records/plans/executed/20260829-runstop-00-zpbx7o-runner-graceful-quit-protocol-adopt-spec-c4gd2h.ipd.md
    ```
    No walkthrough row returned.
    Baseline bare python3 -m pytest summary:
    `3525 passed, 2 skipped, 3 warnings in 70.84s (0:01:10)`
    Baseline aw check count:
    `errors  68   warnings  0`
    The refusal condition (old filenames present, or any identity-slot finding) did NOT trigger.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the `git diff` of `tests/test_walkthrough_id6.py` showing the `assertEqual(len(all_files), 24, ...)` and `assertEqual(len(exempt), 11, ...)` assertions and the `LEGACY_WALKTHROUGHS` literal all removed, `BULLETLESS_GRANDFATHERED` retained with its provenance comment, and the loop body unchanged. Plus pasted `python3 -m pytest tests/test_walkthrough_id6.py -o addopts=""` output showing 4 passed, and a confirmation read off the diff that no hardcoded walkthrough count and no legacy filename remains in the test. STATE EXPLICITLY that no redundant derived-exemption pre-filter was added and that the loop's pre-existing `if not token: continue` carries the exemption, since adding one is the specific dead code E-02 forbids.
  - Observed evidence: PASS. Census preamble rewritten to assert property; details below.
    `git diff tests/test_walkthrough_id6.py` confirms that `LEGACY_WALKTHROUGHS`, `assertEqual(len(all_files), 24, ...)`, and `assertEqual(len(exempt), 11, ...)` were deleted, while `BULLETLESS_GRANDFATHERED` was retained with its commit 9a1c4206 provenance comment as a frozenset. The loop body is unchanged, reading metadata declarations through `check_engine._identity_declared_values`.
    Explicitly confirmed: no redundant derived-exemption pre-filter was added; the loop's pre-existing `if not token: continue` carries the exemption.
    Confirmation from diff: no hardcoded walkthrough count and no legacy filename remains in the test.
    Pasted test output:
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.23s ===============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THREE pasted runs (PASS with the extra conformant walkthrough present, the file removed, PASS again), the minted id6, and a statement of how it was minted naming the `repo_root` argument passed to `artifact_core.mint_id6` so it could not collide. Plus `git status --short` pasted showing no modified or untracked file under `.aw/records/walkthroughs/`. A green run at rest does NOT satisfy this item: the PASS that matters is the one taken WITH the extra walkthrough present, because that is the input fact 4 measured as failing.
  - Observed evidence: PASS. Fix direction proven: extra conformant walkthrough passes; details below.
    Minted id6: `6ei4wj` minted via `artifact_core.mint_id6(repo_root)` with `repo_root=pathlib.Path('.')`.
    Created temporary walkthrough `.aw/records/walkthroughs/20260930-id6slotgate-02-6ei4wj-extra-conformant-test-walkthrough.walkthrough.md`.
    Run 1 (with extra walkthrough present):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.25s ===============================
    ```
    File removed:
    `rm .aw/records/walkthroughs/20260930-id6slotgate-02-6ei4wj-extra-conformant-test-walkthrough.walkthrough.md`
    Run 2 (file removed, at rest):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.22s ===============================
    ```
    Run 3 (re-confirmed at rest):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.23s ===============================
    ```
    `git status --short .aw/records/walkthroughs/`: clean (no output).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the `git diff` of `DECISIONS.md`, shown to contain ONLY an added bullet under D140 with no `-` line removing or altering any existing bullet (state how that was confirmed from the diff). The added text must name `t0jyb2` as the change that gave the identity-slot pass the terminal-inclusive corpus, must state that the "walkthrough-slot convention" the earlier parenthetical tolerated was ruled a defect by the walkthroughs README and remediated by `nrqo90`, and must cite the census. Confirm the added prose contains no em or en dashes.
  - Observed evidence: PASS. DECISIONS D140 updated with appended dated Applied bullet; details below.
    `git diff DECISIONS.md` shows only one added bullet under D140:
    ```diff
    +- **Applied (2026-09-30, IPD `aisk5z`):** the parenthetical in item (2) of the 2026-09-20 bullet above is superseded. The identity-slot pass now consumes the terminal-inclusive corpus too (IPD `t0jyb2`), with `check_collisions` enumerating with `include_retired=True` unconditionally and only the setid pass consulting `caller_visible`. The "walkthrough-slot convention" that the parenthetical tolerated as legitimate was ruled a defect by `.aw/records/walkthroughs/README.md` and remediated by IPD `nrqo90`, giving each walkthrough its own minted id6 and demoting the plan id6 to a typed `- Target-Id:` field. As confirmed by the fact-1 census, all three files are now conformant and both collision checks return zero findings.
    ```
    Confirmed from the diff: zero `-` lines (no lines removed or altered).
    The text names `t0jyb2`, states the walkthrough-slot convention was ruled a defect and remediated by `nrqo90`, and cites the fact-1 census.
    Verified with Python regex search: zero em dashes (`\u2014`) and zero en dashes (`\u2013`) in the added prose.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the `git diff` of both backlog files, shown to be append-only, with the three old walkthrough filenames still present verbatim in each item's original measurement text and with `- Status:` and `- Blocks-Release:` unchanged on both (paste those two lines from each file after the edit). Plus the pasted `aw backlog note` invocation and its output for each item; a hand append fails this item unless the verb itself refused, in which case paste the refusal. Any `-` line in either diff other than a trailing-newline artifact fails this item.
  - Observed evidence: PASS. Both backlog items updated via aw backlog note with status and gates preserved; details below.
    Tool invocation for mw0s1y:
    `aw backlog note mw0s1y --message "Remediation confirmed shipped in IPD nrqo90 (commit e83cb542): the three walkthroughs were renamed with their own minted id6 and typed - Target-Id: pointers, and aw find y5od1h no longer returns a duplicate walkthrough record. The residual defect is the frozen census guard in test_walkthrough_id6.py, fixed by IPD aisk5z."`
    Output:
    `aw backlog note: appended a history record to .aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md`

    Tool invocation for e2j5w4:
    `aw backlog note e2j5w4 --message "Remediation confirmed shipped in IPD t0jyb2: check_collisions now enumerates the terminal-inclusive corpus unconditionally for the identity-slot pass (matching the suggested fix), and both collision checks (with include_retired True and False) return zero findings."`
    Output:
    `aw backlog note: appended a history record to .aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md`

    `git diff .aw/records/backlog/graduated/` shows append-only additions to `## Workflow history` with zero `-` lines:
    ```diff
    diff --git a/.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md b/.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
    --- a/.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
    +++ b/.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
    @@ -8,6 +8,7 @@
     - Summary: aw check misses check.id6-identity-slot on a live D140 violation because check_collisions gates the slot pass on the caller's liveness filter

     ## Workflow history
    +- 2026-10-01 note (aw backlog): Remediation confirmed shipped in IPD t0jyb2: check_collisions now enumerates the terminal-inclusive corpus unconditionally for the identity-slot pass (matching the suggested fix), and both collision checks (with include_retired True and False) return zero findings.
     - 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: dta75n
     - 2026-09-21 created (aw backlog): aw check misses check.id6-identity-slot on a live D140 violation because check_collisions gates the slot pass on the caller's liveness filter

    diff --git a/.aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md b/.aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md
    --- a/.aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md
    +++ b/.aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md
    @@ -8,6 +8,7 @@
     - Summary: Three walkthroughs reuse their source plan's id6 in their own filename identity slot, violating D140 and the walkthroughs README

     ## Workflow history
    +- 2026-10-01 note (aw backlog): Remediation confirmed shipped in IPD nrqo90 (commit e83cb542): the three walkthroughs were renamed with their own minted id6 and typed - Target-Id: pointers, and aw find y5od1h no longer returns a duplicate walkthrough record. The residual defect is the frozen census guard in test_walkthrough_id6.py, fixed by IPD aisk5z.
     - 2026-09-29 set (aw backlog): graduated by run run-20260928T235632Z-1358353: aisk5z
     - 2026-09-21 created (aw backlog): Three walkthroughs reuse their source plan's id6 in their own filename identity slot, violating D140 and the walkthroughs README
    ```

    Pasted lines from mw0s1y:
    `- Status: graduated`
    `- Blocks-Release: next`

    Pasted lines from e2j5w4:
    `- Status: graduated`
    `- Blocks-Release: next`

    Original measurement text with all three old filenames remains verbatim and untouched.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted beside the E-01 baseline line, so any failure is shown pre-existing rather than introduced, AND a statement of whether the test COUNT moved (it should be unchanged: E-02 and E-07 edit assertions inside one existing test, so a changed count means something else moved and must be explained). `aw ipd lint --phase pre-transition` on this plan reporting conforming. `aw check` counts before and after pasted WITH the per-rule breakdown on both sides, the after no worse on every rule. `aw sanitize --agent` reporting zero findings. The final walkthrough census pasted and stated to be identical to E-01's. And `git status --short` pasted showing exactly the four declared Scope-Paths modified, with nothing under `.aw/records/walkthroughs/` and no change to `agent_workflows/`, proving E-03 left no residue in either place.
  - Observed evidence: PASS. Full regression gate clean and compared to baseline; details below.
    Full test suite summary comparison:
    Baseline:   `3525 passed, 2 skipped, 3 warnings in 70.84s (0:01:10)`
    Regression: `3525 passed, 2 skipped, 3 warnings in 80.37s (0:01:20)`
    Test count: exactly unchanged at 3525 passed.
    aw check counts and rule breakdown:
    Before (Baseline): 68 errors, 0 warnings
      check.ipd-carrier-finished-unverified: 5
      check.ipd-lint-diagnostic: 7
      check.ipd-uncarried-obligation: 13
      check.lifecycle-transition-invalid: 5
      check.name-nonconformant: 2
      check.plan-spec-link-missing: 31
      check.scope-drift: 1
      check.scope-path-target-stale: 2
      check.spec-criteria-uncovered: 1
      check.system-layout-missing: 1
    After: 68 errors, 0 warnings
      check.ipd-carrier-finished-unverified: 5
      check.ipd-lint-diagnostic: 7
      check.ipd-uncarried-obligation: 13
      check.lifecycle-transition-invalid: 5
      check.name-nonconformant: 2
      check.plan-spec-link-missing: 31
      check.scope-drift: 1
      check.scope-path-target-stale: 2
      check.spec-criteria-uncovered: 1
      check.system-layout-missing: 1
    After is no worse on every single rule.
    aw sanitize --agent output:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    Final walkthrough census:
    ```text
    Total walkthrough files: 24
    slot=None   id=None   target=None   20260712-1023-01-installer-shim-detection-ctrlc-and-diff-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1033-01-assess-bugs-and-tests-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1038-01-fix-installer-shim-tests-left-red-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1041-01-agents-docs-research-and-walkthroughs-convention-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1049-01-scope-review-gemini-bugs-tests-execution-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1100-01-1028-falsely-marked-executed-tests-still-red-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1200-01-ux-and-data-modeling-principles-import-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260712-1230-01-mirror-workflow-pointer-into-native-agent-files-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260810-2052-01-awphysical-01-rejected-greenwashed-execution-corrective-review.walkthrough.md
    slot=None   id=None   target=None   20260812-0300-01-awphysical-overnight-autonomous-execution-01-to-10-walkthrough.walkthrough.md
    slot=None   id=None   target=None   20260812-1200-01-order11-self-migration-decision-record-walkthrough.walkthrough.md
    slot=4533x3 id=4533x3 target=None   20260821-4533x3-01-4533x3-awoptimize-rescope.walkthrough.md
    slot=35xfvu id=None   target=None   20260823-35xfvu-01-35xfvu-highpbacklog0822-execution-decisions.walkthrough.md
    slot=hey7r7 id=hey7r7 target=p7dqwz 20260823-artifactenginefix-01-hey7r7-execution.walkthrough.md
    slot=5gdzyz id=5gdzyz target=y6mfgo 20260831-locksafe-01-5gdzyz-one-cross-platform-file-lock-walkthrough.walkthrough.md
    slot=01ad6r id=01ad6r target=zpbx7o 20260901-runstop-00-01ad6r-graceful-quit-whole-set-verification.walkthrough.md
    slot=cceh3w id=cceh3w target=y5od1h 20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md
    slot=ryn48z id=ryn48z target=s16omw 20260917-bpclosure-01-ryn48z-build-parser-two-cli-contracts-not-one-with-drift.walkthrough.md
    slot=pi4wof id=pi4wof target=yrqyxb 20260917-eiclosure-01-pi4wof-execute-item-closure-measured-not-split.walkthrough.md
    slot=ztmh1b id=ztmh1b target=orziju 20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md
    slot=v0nmuv id=v0nmuv target=4fodkt 20260917-lanectn-07-v0nmuv-whole-set-verification-of-spec-7ckptx.walkthrough.md
    slot=zogmmg id=zogmmg target=3dki3o 20260917-mnclosure-01-zogmmg-main-is-an-entry-point-and-the-set-shared-nothing.walkthrough.md
    slot=k2vn8p id=k2vn8p target=ty3cj6 20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md
    slot=u8tiox id=u8tiox target=3v7wo6 20260918-integpath-05-u8tiox-lane-to-main-integration-whole-set-verification-and-residuals.walkthrough.md
    ```
    Identical to E-01 census.
    `git status --short`:
    ```text
     M .aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
     M .aw/records/backlog/graduated/20260921-id6slotgate-01-mw0s1y-walkthrough-identity-slot-reuse.backlog.md
     M DECISIONS.md
     M tests/test_walkthrough_id6.py
    ```
    Exactly the 4 declared Scope-Paths modified, zero residue under `.aw/records/walkthroughs/` or `agent_workflows/`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the `git diff` hunk containing the new floor, showing (i) the examined count compared for EQUALITY against an expectation computed from the local legacy-name-shape rule and NOT from `check_engine._identity_slot_token`, (ii) the local regex defined as a test constant carrying the comment that its independence is deliberate, (iii) the non-empty directory assertion, and (iv) an assertion message naming BOTH counts. Plus the two counts the assertion reports on this tree, stated as numbers. If the expectation side is computed from `_identity_slot_token` in any form, this item FAILS regardless of a green run, because the review measured that shape vacuous.
  - Observed evidence: PASS. Anti-vacuity floor equality against independent legacy name-shape rule verified; details below.
    `git diff tests/test_walkthrough_id6.py` shows the floor definition and assertions:
    ```diff
    +# Deliberately independent of check_engine so the test can disagree with
    +# the normalizer: collapsing this onto _identity_slot_token would make
    +# the anti-vacuity floor vacuous again (IPD aisk5z E-07).
    +_LEGACY_NAME_PREFIX_RE = re.compile(r"^\d{8}-\d{4}-\d{2}-")
    ...
    +        self.assertTrue(all_files, f"{wdir} must not be empty")
    +
    +        expected = sum(
    +            1
    +            for p in all_files
    +            if not _LEGACY_NAME_PREFIX_RE.match(p.name)
    +            and p.name not in BULLETLESS_GRANDFATHERED
    +        )
    ...
    +        self.assertEqual(
    +            examined,
    +            expected,
    +            f"Examined count ({examined}) must match independently computed expectation ({expected})",
    +        )
    ```
    (i) `examined` is compared for EQUALITY against `expected`, computed from `_LEGACY_NAME_PREFIX_RE` and not `check_engine._identity_slot_token`.
    (ii) `_LEGACY_NAME_PREFIX_RE` is defined as a module-level constant with the required independence comment.
    (iii) `self.assertTrue(all_files, f"{wdir} must not be empty")` asserts directory non-emptiness.
    (iv) `f"Examined count ({examined}) must match independently computed expectation ({expected})"` names both counts.
    On this tree: examined = 12, expected = 12.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: THREE pasted runs (PASS at rest, FAILURE, PASS after `git checkout --`). The FAILURE output must name the file whose `- Id:` bullet was deleted AND its slot id6, matching fact 5's shape (`slot id6=<token>, declared in metadata region=None`); a failure that reports only a count, or that names no file, does NOT satisfy this item because it would not distinguish the D140 rule firing from the census assertion firing. Name which walkthrough was mutated and confirm `git status --short` shows it restored.
  - Observed evidence: PASS. Preservation direction proven: D140 rule fires on deleted Id bullet; details below.
    Mutated walkthrough: `.aw/records/walkthroughs/20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md`.
    Run 1 (at rest):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.23s ===============================
    ```
    Deleted line `- Id: cceh3w\n`.
    Run 2 (mutated):
    ```text
    =================================== FAILURES ===================================
    _ TestWalkthroughDeclaredIdMatchesSlot.test_clustered_walkthroughs_declare_matching_id _
    ...
    E       AssertionError: Lists differ: ["20260906-lanectn-04-cceh3w-missing-input[83 chars]one"] != []
    E
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       "20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md: slot id6='cceh3w', declared in metadata region=None"
    E
    E       + []
    E       - ['20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md: '
    E       -  "slot id6='cceh3w', declared in metadata region=None"] : Walkthroughs missing declared - Id: matching identity slot:
    E       20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md: slot id6='cceh3w', declared in metadata region=None
    ...
    ========================= 1 failed, 3 passed in 0.41s ==========================
    ```
    Failure output names `20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md` and slot id6='cceh3w' matching fact 5's shape.
    Restored file via `git checkout -- .aw/records/walkthroughs/20260906-lanectn-04-cceh3w-missing-input-report-and-refuse.walkthrough.md`.
    Run 3 (restored):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.48s ===============================
    ```
    `git status --short .aw/records/walkthroughs/`: clean (no output).
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: TWO pasted runs (FAILURE under the slot discriminator narrowed to `202609*` names, then PASS after restoring). The FAILURE message must show BOTH counts, so the two sides of the E-07 equality are visible and the reviewer can see they diverged (measured at review: `9 != 12`). State the mechanism used to narrow the discriminator and confirm it was an in-run patch, with `git status --short` pasted showing `agent_workflows/` unmodified. IF THIS MUTATION PASSES rather than fails, record that as a FAILED validation and do not proceed: it proves E-07's expected side is still derived from the discriminator under test, which is the vacuous shape the review measured and rejected.
  - Observed evidence: PASS. Floor direction proven: silent under-examination caught under narrowed discriminator; details below.
    Mechanism: In-process monkeypatch passed via Python one-liner wrapper:
    `python3 -c "import pytest, sys, agent_workflows.check_engine as ce; orig = ce._identity_slot_token; ce._identity_slot_token = lambda f: orig(f) if f.startswith('202609') else None; sys.exit(pytest.main(['tests/test_walkthrough_id6.py', '-o', 'addopts=']))"`
    Run 1 (narrowed to `202609*`):
    ```text
    =================================== FAILURES ===================================
    _ TestWalkthroughDeclaredIdMatchesSlot.test_clustered_walkthroughs_declare_matching_id _
    ...
    >       self.assertEqual(
                examined,
                expected,
                f"Examined count ({examined}) must match independently computed expectation ({expected})",
            )
    E       AssertionError: 9 != 12 : Examined count (9) must match independently computed expectation (12)

    tests/test_walkthrough_id6.py:157: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_walkthrough_id6.py::TestWalkthroughDeclaredIdMatchesSlot::test_clustered_walkthroughs_declare_matching_id
    ========================= 1 failed, 3 passed in 0.34s ==========================
    ```
    Both counts visible (`9 != 12 : Examined count (9) must match independently computed expectation (12)`).
    Run 2 (normal unpatched run):
    ```text
    tests/test_walkthrough_id6.py ....                                       [100%]
    ============================== 4 passed in 0.39s ===============================
    ```
    `git status --short agent_workflows/`: clean (no output).
  - Result: pass



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

The executor must further: perform E-01 through E-09 respecting the declared `Depends on` edges (note the
execution order is E-01, E-02, E-07, E-03, E-08, E-09, E-04, E-05, E-06; E-07, E-08 and E-09 were allocated at review by `aw ipd sync` and
so carries a number out of sequence with its position, which is expected and is not a defect to "tidy");
commit only the four paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL
runner output for every claim of a passing test, INCLUDING the paired mutation failures E-08 and E-09 require;
leave `.aw/records/walkthroughs/` and `agent_workflows/` byte-identical to their pre-execution state; and
verify each `V-*` in a pass separate from the `E-*` that produced it.

SCOPE FENCE (a declaration, not a stop directive). The four declared paths are the whole intended surface.
E-03 temporarily writes under `.aw/records/walkthroughs/` and E-09 temporarily narrows a discriminator, and both
must be fully reverted, so NEITHER path is declared. If the work genuinely requires a path outside the fence,
MAKE the edit and JUSTIFY it: `aw ipd finalize` refuses to complete until every out-of-scope path carries a
`--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`. Do not make a cosmetic edit
to satisfy the gate, and do not widen `- Scope-Paths:` to pre-empt it.

POST-GATE LIFECYCLE. Do not claim done and do not move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence. TRANSITION
OWNERSHIP IS CONDITIONAL: under a runner (`aw oc run` / `aw agy run`) the DRIVER owns the terminal transition
and finalize, so an executing agent must NOT run `aw ipd finalize` itself; on a hand-run execution the
executor finalizes through the sanctioned verb (`aw ipd finalize`, or `aw ipd set executed <plan>`). Either
way, NEVER hand-edit `- Status:` and NEVER `git mv` this file into `executed/` yourself: a hand-rolled move
skips the pre-transition checkpoint that is the only thing standing between an unvalidated plan and a
terminal record.

THE EXECUTOR MUST NOT change the `- Status:` of either backlog item, nor either item's `- Blocks-Release:`.
`mw0s1y` reaches `graduated` by the runner's own transition on this plan's authoring and `done` only once
this plan is `executed`, which is what preserves its release gate through the handoff. `e2j5w4` is a separate
item that this plan corrects but does not close.

Backlog item `mw0s1y` is this plan's origin (`- From-Backlog: mw0s1y`) and its `- Blocks-Release: next` gate
is inherited here unchanged. The gate is kept even though the item's original symptom no longer reproduces,
because the defect CLASS is still undefended: the only regression test standing between the repository and a
recurrence is the one that fact 4 measures as breaking on the next walkthrough anyone writes. When E-02 and
E-07 land and E-03, E-08 and E-09 demonstrate them by mutation, that is no longer true, and the gate is
legitimately satisfied rather than merely cleared.
