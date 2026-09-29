# IPD: Re-justify run_suite_check's primary-checkout contract on the reason that still holds and pin it with a test

- Date: 2026-09-29
- Kind: child
- Concern: `runner_shared.run_suite_check`'s docstring justifies its PRIMARY-CHECKOUT insistence with a measurement that no longer reproduces: "`tests/test_run_viewer.py` gives `36 passed` in the primary checkout and `15 failed, 20 passed` in a lane", attributed to `.aw/state` resolving relative to cwd (backlog `dh0uno`). `dh0uno` is `- Status: done`, fixed in `6771e590` by keying the control root on `git rev-parse --git-common-dir`, and its own history retracts the claim. RE-MEASURED IN THIS LANE (itself a linked worktree, which is exactly the cited condition): `tests/test_run_viewer.py` gives `38 passed` and the full bare suite gives `3246 passed, 2 skipped`, fully green, so the divergence the docstring describes is absent in the very venue it says is permanently red. Also measured here and WORSE than the backlog item knew: the primary-checkout contract itself is ENTIRELY UNPINNED. Repointing the call at the lane (`run_suite_check(Path(work_dir) if work_dir else repo, ...)`) leaves the whole suite GREEN at `3246 passed, 2 skipped`, so the contract this docstring exists to defend has no regression test, and its only defence is prose an executor is invited to disbelieve because its stated reason is checkably false.
- Scope: Correct the record for `run_suite_check`'s primary-checkout contract and give the contract a test. Rewrite the docstring paragraph to re-justify the contract on the reason that STILL HOLDS (a green PRIMARY tree is what integration endangers, which is already the docstring's own "HONEST LIMIT" sentence and is independent of `dh0uno`), DELETING the stale counts and the "permanently red" conclusion without installing a replacement count, since the item's own eight-day-old figure is already stale by 53 tests (F-3) and a fresh number would re-create this very item. Correct the same stale claim at the three other sites that restate it: the `rerun_suite` comment ("a lane-run suite is permanently red") and the two "`run_suite_check` is defined in `oc_runipd`" statements, which have been wrong since `cnwy8g` re-homed the function into `runner_shared`. Add a behavioral test asserting the suite check receives the PRIMARY checkout and not the lane worktree. EXCLUDES changing which directory `run_suite_check` runs in (the contract is correct and is deliberately preserved), EXCLUDES any change to `dh0uno`'s control-root fix, and EXCLUDES the dangling `NoRunnerImportTests` citations found beside this work (carried by backlog `gia5i7`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: nbu56f
- Set: nbu56f
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: cvs2b7

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog item `nbu56f`, graduating it. Every claim below was re-measured in this lane at HEAD `4bf73373` rather than inherited from the item, and THREE findings change the shape of the work the item described. FIRST, the item's own re-measurement REPRODUCES but with different numbers (`38 passed` here against the item's `91 passed`, because `tests/test_run_viewer.py` has changed again since 2026-09-21 in `cbf17e3e`, `33834c71`, `9e4b7516`), which is itself the argument against writing a fresh count into a docstring: the item's proposed fix, "replace the stale counts with the current measurement", would install a number already stale by 53 tests in eight days. SECOND, and not known to the item, THE CONTRACT IS UNPINNED: mutating the call site to pass the lane leaves the full suite green (`3246 passed, 2 skipped`), so a future executor who reads the falsified justification and "helpfully" repoints the call at the lane breaks nothing and ships it. That makes a test, not a docstring edit, the plan's central deliverable, and it inverts the item's own closing note that this is "a one-line courtesy at most". THIRD, the stale claim is restated at TWO more sites the item did not name, and a separate factual error sits in the same paragraphs: two comments say `run_suite_check` "is defined in `oc_runipd`" when `runner_shared` is where it now lives (`cnwy8g` re-homed it), which matters because the stated reason for INJECTING it rather than importing it rests on that false premise.

## Goal

Make `run_suite_check`'s primary-checkout contract defensible and defended: justified by a reason that is
still true, and pinned by a test that fails if the call is repointed at the lane.

The backlog item asked for a docstring correction. Measurement says that alone is insufficient and
partly counterproductive. The contract is RIGHT and the reason given for it is WRONG, which is the worst
combination available, because a reader who checks the reason finds it false and has nothing stopping them
from acting on that discovery. The durable fix is to move the contract's defence out of prose and into a
test, and to leave prose saying only what remains true.

SIX FACTS ESTABLISHED AT AUTHORING, so the executor inherits measurement rather than the item's diagnosis.

1. THE STALE CLAIM IS STILL IN THE TREE, VERBATIM. `runner_shared.run_suite_check`'s docstring reads
   "MEASURED: `tests/test_run_viewer.py` gives `36 passed` in the primary checkout and `15 failed, 20
   passed` in a lane, every failure being the `run_viewer`/state-resolution family. A lane-run suite is
   therefore permanently red for reasons unrelated to the executing plan". The `dh0uno` citation sits in
   the sentence above it.

2. IT DOES NOT REPRODUCE, MEASURED IN A LINKED WORKTREE. This lane IS a linked worktree
   (`git rev-parse --git-dir` gives `.git/worktrees/nbu56f` against a `--git-common-dir` of `.git`),
   which is the exact condition the docstring says is permanently red:

   ```text
   $ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q
   38 passed in 4.80s

   $ python3 -m pytest
   3246 passed, 2 skipped, 3 warnings in 52.51s
   ```

   Fully green, no `run_viewer`/state-resolution family failure, no environmental failure either. The
   cause is closed at the source: `ipd_lifecycle.checkout_control_root` collapses a lane onto the main
   checkout's `.aw` (measured from this lane: `checkout_control_root(".")` returns the MAIN tree's
   `.aw`, not the lane's).

3. WRITING A FRESH COUNT WOULD RE-ROT IMMEDIATELY, WHICH REFUSES HALF THE ITEM'S PROPOSED FIX. The item
   measured `91 passed` for `tests/test_run_viewer.py` on 2026-09-21; this lane measures `38 passed`
   eight days later, the file having changed in `cbf17e3e`, `33834c71` and `9e4b7516`. A docstring
   number is stale by construction. So the corrected text must cite the PROPERTY (a lane is no longer a
   known-noisy venue, because `dh0uno` is fixed) and the CARRIER (`dh0uno`, plus the test E-03 adds),
   never a fresh count presented as durable.

4. THE CONTRACT IS ENTIRELY UNPINNED, AND THIS IS THE FINDING THAT RESHAPES THE PLAN. Mutating the sole
   call site from `run_suite_check(repo, ...)` to `run_suite_check(Path(work_dir) if work_dir else repo,
   ...)` and running the suite bare:

   ```text
   3246 passed, 2 skipped, 3 warnings in 48.37s
   ```

   Nothing fails. So the primary-checkout contract has no regression test, in either host, and the
   docstring is its only defence. Since fact 2 falsifies that docstring's stated reason, the contract is
   currently defended by an argument a careful reader is entitled to reject.

5. A BEHAVIORAL PIN IS FEASIBLE AND FALSIFIABLE, prototyped at authoring rather than assumed. Driving
   `oc_runipd.execute_item` through the existing `WorktreeIsolationTests` fixture with
   `options["no_audit"] = True` (which is what makes `validate` false and therefore reaches the
   integration-gate suite check) and spying on `run_suite_check`:

   ```text
   HEAD      SUITE_CHECK_CWDS: ['<tmp>/repo', '<tmp>/repo/.aw/records/runs/run-test/revalidation/revalidate-<hash>']
   mutated   SUITE_CHECK_CWDS: ['<tmp>/repo/.aw/worktrees/wir001', '<tmp>/repo/.aw/records/runs/run-test/revalidation/revalidate-<hash>']
   ```

   The FIRST cwd is the assertion target and it flips from the primary checkout to the lane worktree
   under the mutation, so a test asserting it equals the repo root is not vacuous. NOTE THE SECOND
   ENTRY IS NOT A SECOND VIOLATION: it is the merge-and-revalidate gate's own revalidation checkout,
   which is a different mechanism with its own directory, and it is UNCHANGED by the mutation. A test
   must therefore assert on the first call specifically, never on "every call".

6. TWO MORE SITES RESTATE THE STALE CLAIM, AND A SEPARATE FACTUAL ERROR SITS BESIDE THEM. The
   `rerun_suite` comment in the gate-answer construction says "a lane-run suite is permanently red for
   reasons unrelated to the plan", citing the same docstring. And TWO comments say "`run_suite_check`
   is defined in `oc_runipd`, and the shared module may not import it" as the reason it is injected as a
   parameter; measured, `def run_suite_check` occurs exactly once in the package and it is in
   `runner_shared.py`, with both hosts importing it FROM there (`cnwy8g` re-homed it). The injection
   itself is still real and still used, so the code is right and only the premise stated for it is
   wrong, exactly as with the primary-checkout contract.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before editing anything

- [ ] E-01 RE-DERIVE FACTS 2 AND 4 IN YOUR OWN LANE before editing any file, and RECORD THE RESULT EVEN IF IT DIFFERS from this plan's numbers, which fact 3 predicts it will. Run bare `python3 -m pytest` for the baseline and `tests/test_run_viewer.py` for the file the stale claim names. Then apply the fact-4 mutation to the sole call site (the `suite_result = run_suite_check(repo, ...)` assignment in `runner_shared.execute_item`'s integration-gate block) and run the suite bare again, to confirm the contract is STILL unpinned at your HEAD. If the mutated suite FAILS, that changes this plan: a pin already exists, E-03 must be re-scoped to extend it rather than create one, and you must say so instead of adding a duplicate. RESTORE THE FILE and prove it byte-identical with a clean `git status --short` before proceeding; a mutation left in the tree would be committed.
  - Depends on: none
  - Expected outcome: three pasted summary lines (baseline bare, `test_run_viewer.py`, mutated bare), an explicit statement of whether the contract is still unpinned, and a pasted clean `git status --short` proving the mutation was reverted.
  - Execution state: pending

- [ ] E-02 CONFIRM THE CAUSE IS STILL CLOSED rather than inferring it from a green suite, because a green suite is consistent with both "the bug is fixed" and "the tests that would show it were deleted". Call `ipd_lifecycle.checkout_control_root` from inside your lane and show it returns the MAIN checkout's `.aw`, and show `runner_shared.state_root` for the same lane. Read `checkout_control_root`'s docstring and confirm it still documents the `--git-common-dir` collapse as the `dh0uno` fix. NOTE AND RECORD THE ASYMMETRY you will find: the CONTROL root collapses onto the main checkout while `state_root` resolves records relative to the target, so these two answer different questions; do not report the second as a defect, and do not "fix" it, because `run_viewer`'s live-tree dependency is separately owned and guarded (`swps4w`, backlog `rcmbnb`).
  - Depends on: E-01
  - Expected outcome: pasted values for both resolvers as called from the lane, plus a one-line statement of which one `dh0uno` fixed and why the other's behavior is correct and out of scope.
  - Execution state: pending

### Task group 2: pin the contract

- [ ] E-03 ADD THE BEHAVIORAL PIN that the contract has never had, in `tests/test_oc_runipd.py` beside the existing `WorktreeIsolationTests` (that class already builds an isolated-worktree execute turn, so the fixture cost is near zero and the new test sits with the isolation properties it belongs to). Drive `oc_runipd.execute_item` with `options["no_audit"] = True` so `validate` is false and the integration-gate suite check is reached, spy on `run_suite_check`, and assert THE FIRST recorded cwd equals the primary repo root. ASSERT ON THE FIRST CALL ONLY, never on all of them: fact 5 measured a SECOND call from the merge-and-revalidate gate's own revalidation checkout, which is a different mechanism, is unaffected by the mutation, and would make an "every call" assertion fail for the wrong reason. Give the test a docstring stating WHAT it defends (a green PRIMARY tree is what integration endangers) and WHAT IT DOES NOT (it does not re-assert the retracted `dh0uno` divergence), and naming this plan, so the next reader does not restore the stale justification from the test.
  - Depends on: E-02
  - Expected outcome: a passing test, plus the pasted FAILURE of that same test under the fact-4 mutation and a pasted PASS after restoring, proving it is not vacuous.
  - Execution state: pending

### Task group 3: correct the record at the code sites

- [ ] E-04 REWRITE THE `run_suite_check` DOCSTRING'S JUSTIFICATION PARAGRAPH. Delete the two stale counts and the "permanently red" conclusion. Re-justify the contract on the reason that survives independently, which the docstring ALREADY STATES one paragraph later as its "HONEST LIMIT": a green PRIMARY tree is what integration endangers, so the primary checkout is the venue whose greenness the gate is about. Say that the `dh0uno` divergence WAS the original reason, that it is `done` and its acceptance claim retracted, and that the contract survives its removal on the independent ground, so a reader who re-measures and finds no divergence learns they have confirmed this note rather than refuted it. CITE THE TEST FROM E-03 BY NAME as what now enforces the contract. DO NOT WRITE A FRESH TEST COUNT into the docstring (fact 3): cite the property and the carrier, since a number installed today is stale within days and re-creates this item. Keep `Callers MUST pass the primary repo, never work_dir`, which is the operative instruction and is unchanged.
  - Depends on: E-03
  - Expected outcome: the `git diff` of the docstring, showing the counts and the "permanently red" sentence gone, the independent justification present, the E-03 test cited, no new count introduced, and no executable line changed.
  - Execution state: pending

- [ ] E-05 CORRECT THE THREE RESTATEMENTS elsewhere in `runner_shared.py`, which E-04 would otherwise leave as the surviving copies of the claim it just removed. (a) The `rerun_suite` comment in the gate-answer construction, whose "a lane-run suite is permanently red for reasons unrelated to the plan" is the same retracted claim and whose parenthetical points at the docstring E-04 rewrote; restate it on the independent ground (a `fixed` claim is re-verified in the same venue the first check used, which is the primary checkout). (b) and (c) The two comments asserting "`run_suite_check` is defined in `oc_runipd`, and the shared module may not import it": name `runner_shared` as the definition site per fact 6, and preserve the still-true point each comment is making, namely that the call is INJECTED as a parameter. Do not delete the injection rationale and do not change the injection itself; a wrong premise for a correct design is corrected in place, not removed.
  - Depends on: E-04
  - Expected outcome: the `git diff` for all three sites, each showing the corrected premise, with the injection design and the AST-guard reasoning preserved and no executable line changed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan is by symbol or by quoted string, and the one commit citation (`6771e590`) is a durable sha.
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md; GUIDING_PRINCIPLES P16). This constraint is load-bearing here and names the trap directly: the tempting way to "prove the docstring was corrected" is a test that reads the source for the absence of `36 passed`, which is exactly the banned structural pin. E-04 and E-05 are validated by their DIFFS instead, and the single test this plan adds (E-03) calls `execute_item` and asserts on an observed cwd.
- THE MUTATION-DEMONSTRATION CONVENTION IS ESTABLISHED HERE AND IS THE ONLY EVIDENCE AGAINST VACUITY. Sibling pending plan `jw6cm3` requires the same mutate/fail/restore/pass triple for every test it adds, on the same reasoning; V-03 demands it, because a test that passes is not evidence that it tests anything.
- RUN THE SUITE BARE (AGENTS.md). `pyproject.toml` `addopts` already supplies quiet, parallel and the fast subset; a second `-q` would suppress the `N passed` line this plan requires pasted. The targeted runs in this plan pass `-o addopts=""` to get per-file counts, which is the documented way to clear the defaults rather than fighting them flag by flag.
- A DOCSTRING-ONLY CORRECTION IS AN ESTABLISHED ARTIFACT SHAPE IN THIS REPOSITORY, so this plan is not inventing one. Pending `jw6cm3` corrects a docstring's account of two narrowing sites and pins the unpinned half; the same pairing (correct the record, then test the thing the record was wrongly defending) is what this plan follows.
- `run_viewer`'s LIVE-TREE DEPENDENCY IS SEPARATELY OWNED AND ALREADY GUARDED, which is why E-02 forbids touching it. `tests/test_run_viewer.py` carries an autouse audit-hook guard (`_forbid_live_runs_reads`, `_LIVE_RUN_ROOTS`) installed by executed plan `swps4w` from backlog `rcmbnb`, whose own Goal records that it is INERT where no live runs tree exists. That is a second, independent reason the file is green in this lane, and it must not be mistaken for evidence about `dh0uno` either way.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The stale claim is present verbatim in `run_suite_check`'s docstring | "MEASURED: `tests/test_run_viewer.py` gives `36 passed` in the primary checkout and `15 failed, 20 passed` in a lane" plus "permanently red" | E-04 rewrites this paragraph |
| F-2 | It does not reproduce in a linked worktree, the exact cited condition | In this lane: `38 passed` for `tests/test_run_viewer.py`; `3246 passed, 2 skipped` bare, fully green | The justification is false and must be replaced, not merely re-numbered |
| F-3 | A fresh count would re-rot immediately | The item measured `91 passed` on 2026-09-21; this lane measures `38 passed` eight days later, the file having changed in `cbf17e3e`, `33834c71`, `9e4b7516` | E-04 is FORBIDDEN from writing a new count; it cites the property and the carrier instead. Half the item's proposed fix is refused |
| F-4 | The primary-checkout contract is ENTIRELY UNPINNED | With the call site passing the lane, bare suite: `3246 passed, 2 skipped` | A test is the central deliverable (E-03), which inverts the item's "one-line courtesy at most" framing |
| F-5 | A behavioral pin is feasible and falsifiable, and must key on the FIRST call only | HEAD first cwd `<tmp>/repo`; mutated first cwd `<tmp>/repo/.aw/worktrees/wir001`; the second cwd is the revalidation checkout and is unchanged by the mutation | E-03's assertion shape is fixed by this measurement; an "every call" assertion would fail for the wrong reason |
| F-6 | Two further sites restate the retracted claim, and two assert a wrong definition site | The `rerun_suite` comment says "permanently red"; two comments say `run_suite_check` "is defined in `oc_runipd`" while `def run_suite_check` occurs once, in `runner_shared.py` | E-05 exists; without it E-04 leaves surviving copies of the claim it removed |
| F-7 | The cause is closed at the source, not merely unobserved | From this lane, `ipd_lifecycle.checkout_control_root(".")` returns the MAIN checkout's `.aw`; its docstring documents the `--git-common-dir` collapse as the `dh0uno` fix (`6771e590`) | E-02 verifies the mechanism rather than inferring it from a green suite |
| F-8 | `tests/test_run_viewer.py` is green here for a SECOND independent reason | Executed plan `swps4w` (backlog `rcmbnb`) installed an autouse audit-hook guard in that file and records that it is inert where no live runs tree exists; this lane holds zero run directories | E-02 must not read that file's greenness as `dh0uno` evidence, in either direction |
| F-9 | A test class cited nine times as the enforcing guard does not exist, and its removal is already ruled on | `NoRunnerImportTests` cited at eight sites in `runner_shared` plus once in `oc_runipd`; `grep -rn "class NoRunnerImport" tests/` empty; `git log -S "class NoRunnerImportTests"` shows it deleted in `19313eed`, the same suite-trim commit that deleted the files sibling item `pn7rw3` records, whose 2026-09-28 maintainer ruling says such pins "will not be restored" and stale comments should drop the reference. Executed plan `nzznlm` F-7 recorded three further danglers, both files still absent | OUT OF SCOPE, carried by backlog `gia5i7` (Deferred). E-05 edits comments that CONTAIN such a citation: it must not add a new one, and must not delete the still-true design point around it |

## Proposed changes (ordered, validatable)

1. Re-derive the baseline and the unpinned-contract mutation in the executor's own lane, then restore (E-01).
2. Verify the `dh0uno` cause is closed at `checkout_control_root`, and record the `state_root` asymmetry as correct-and-out-of-scope (E-02).
3. Add the behavioral pin asserting the suite check receives the primary checkout, keyed on the first call (E-03).
4. Rewrite the docstring's justification paragraph, citing the new test and no fresh count (E-04).
5. Correct the `rerun_suite` comment and the two "defined in `oc_runipd`" premises (E-05).

## Deferred / out of scope (with reason)

- CHANGING WHICH DIRECTORY `run_suite_check` RUNS IN. The contract is CORRECT and is deliberately preserved; only its stated reason is wrong. This is the whole point of the plan and the most likely way for an executor to go wrong, since E-04 hands them a paragraph saying the original reason is false.
  - Carrier-Declined: A scope fence, not deferred work. No finding measures a fault in where the suite runs; F-2 measures a fault in the REASON GIVEN for it, and F-4 measures the absence of a test. Filing an item would assert the repository intends to move the call, which E-03 is specifically built to prevent.
- THE `state_root`-VERSUS-`checkout_control_root` ASYMMETRY that E-02 will surface: records resolve relative to the target while control state collapses onto the main checkout. Deliberately untouched.
  - Carrier-Declined: Nothing is owed because this is not a defect. The two resolvers answer different questions and `checkout_control_root`'s own docstring states the collapse is the fix and states its limits. `run_viewer`'s live-tree dependency, the one place where the records-relative resolution is actually felt, is already owned and guarded by executed plan `swps4w` from backlog `rcmbnb` (F-8), so an item here would duplicate tracked, completed work.
- THE NONEXISTENT TEST-CLASS CITATIONS (F-9). `runner_shared` cites `NoRunnerImportTests` at eight sites and `oc_runipd` once more, and the class exists nowhere; `nzznlm` F-7 already recorded three sibling danglers in the same neighborhood and both files it named are still absent. Not fixed here: the remedy is to strike nine citations across two modules this plan barely touches, and doing it inside this plan would bury the correction this plan exists to make behind a nine-site sweep with a different subject.
  - Carrier: gia5i7
- WRITING A CURRENT TEST COUNT into the corrected docstring, which is the backlog item's own stated fix shape ("replace the stale counts with the current measurement"). REFUSED ON MEASUREMENT, not deferred: F-3 shows the item's own eight-day-old number is already stale by 53 tests.
  - Carrier-Declined: Nothing is owed because there is no latent work, only a proposal this plan measured and refused. Filing it would assert the repository intends to install a number that F-3 shows re-creates this very item. The refusal and its evidence are recorded here and, after E-04, at the code site, which is where the next author considering the same edit will read it.
- THE AGY HOST. `agy_runipd` imports `run_suite_check` from `runner_shared` rather than defining its own, and the corrected docstring is therefore the same text both hosts read. No agy-side edit is needed and none is made.
  - Carrier-Declined: Nothing is owed because `cnwy8g`'s re-homing already delivered the single definition that makes one correction serve both hosts. An item would imply agy carries a divergent copy; measured, `def run_suite_check` occurs exactly once in the package.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` holds `run_suite_check`, its docstring, the sole integration-gate call site, and all three restatement sites from F-6. `tests/test_oc_runipd.py` holds `WorktreeIsolationTests`, whose isolated-worktree execute-turn fixture is what makes E-03's pin cheap and whose subject (what stays in the lane versus the main tree) is exactly the property being pinned.
- Under-scope: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are deliberately NOT declared. Both merely re-export `run_suite_check` from `runner_shared`, so neither carries the text being corrected; if the executor concludes an edit there is required, that is a scope change to stop and re-declare rather than absorb. The `.aw/records/backlog/` item text is likewise undeclared: this plan does not modify the item's requirements, and the runner owns its status transition. No spec is declared, for the reason in Spec / documentation sync.

## Required tests / validation

- Bare `python3 -m pytest` with the `N passed` summary line pasted, against a pre-execution baseline captured the same way BEFORE any edit in this plan lands (measured at authoring: `3246 passed, 2 skipped`). A pre-existing failure must be shown pre-existing by the baseline rather than argued harmless.
- A targeted `tests/test_oc_runipd.py` run with `-o addopts=""` for the per-test count, since E-03's test lands there.
- A MUTATION DEMONSTRATION FOR THE NEW TEST: apply the fact-4 mutation, paste the new test FAILING, restore, paste it PASSING. A new test with no mutation evidence is exactly the vacuous pin F-4 shows this contract has lived without, so this is a hard requirement.
- A `git status --short` after E-01 and again after the mutation demonstration, proving every exploratory mutation was reverted before any real edit landed and before commit.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean.
- NO TEST MAY ASSERT ON THE PRESENCE OR ABSENCE OF DOCSTRING TEXT. E-04 and E-05 are validated by their diffs (V-04, V-05). A structural pin would violate GUIDING_PRINCIPLES P16 and would itself become the next stale-text defect.

## Spec / documentation sync

- NO SPEC IS AMENDED, and the search is recorded so the absence is a finding rather than an omission: no file under `.aw/records/specs/` mentions `run_suite_check`, and none carries the `36 passed` / `15 failed, 20 passed` claim. The stale text lives only in source comments and in `.aw/records/` history, so there is no normative contract to correct.
- HISTORICAL RECORDS ARE LEFT ALONE, DELIBERATELY. Superseded plan `32ij2j` and review `evgi9n` both quote the `36 passed` figure. Those are RECORDS of what was believed and measured at the time; rewriting them would falsify history, and the plan contract forbids changing what an executed or superseded record records. The banner comment above `SUITE_BASELINE_SUBDIR` in `runner_shared` already handles this the correct way, by naming the docstring's claim HISTORICAL and citing the re-measurement beside it, and it needs no edit.
- NO CHANGELOG ENTRY. This is an internal comment and test change with no user-visible behavior difference; `run_suite_check` runs in the same directory before and after.

## Open questions

### OQ-01: Should the corrected docstring keep the `dh0uno` citation at all, or drop it as settled history?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-04 KEEPS it, marked as the original-and-retracted reason. The argument for keeping: a reader who re-measures and finds no divergence needs to learn that they have CONFIRMED the note rather than refuted it, and that requires the note to name what was once true and is now fixed. That is precisely the failure mode this item records, where a reviewer re-measured and had to go read `dh0uno`'s history to discover the retraction. The argument for dropping: a citation to a closed bug invites the next reader to re-litigate it. NOT BLOCKING because E-04's other requirements (no fresh count, the independent justification, the E-03 citation) are identical under either answer, and the difference is one clause.
- Carrier-Declined: No carrier is owed under either answer, because both are fully implemented inside E-04 and neither leaves anything unbuilt: the docstring either keeps the marked-historical `dh0uno` citation or omits it, and V-04's required evidence (counts removed, independent justification present, E-03 cited, no new count) is identical in both cases. Filing an item would imply an outstanding edit remains after this plan executes, and none does. The reasoning for the choice this plan made is recorded above and, after E-04, at the code site.

### OQ-02: Should E-03's pin live in `tests/test_oc_runipd.py` or in a host-neutral test module?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-03 puts it in `tests/test_oc_runipd.py` beside `WorktreeIsolationTests`, because that class already builds the isolated execute turn the pin needs and the property is an isolation property. Against that: the call site now lives in `runner_shared` and is shared by both hosts, so a host-named test file understates the reach, and a future agy-side regression would not be caught by a test driven through `oc_runipd.execute_item`. The counter-argument, and the reason the plan chose as it did: there is ONE call site and ONE definition, so a host-neutral duplicate would pin the same line twice. NOT BLOCKING because the assertion, the mutation demonstration and the docstring V-03 demands are identical wherever the test lives; only the file changes.
- Carrier-Declined: No carrier is owed under either answer. Both branches are implemented inside E-03 and neither leaves anything unbuilt: the executor records which it chose and why, and V-03's mutation evidence proves the pin works regardless of location. Filing an item would imply test placement remains outstanding work after this plan executes, and it does not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: three PASTED summary lines from the executor's own lane, labelled: bare-suite baseline, `tests/test_run_viewer.py`, and bare suite UNDER the fact-4 mutation. Plus an explicit sentence stating whether the primary-checkout contract is still unpinned at that HEAD, and if the mutated suite FAILED, naming the failing test and stating how E-03 was re-scoped. Plus a pasted `git status --short` showing `agent_workflows/runner_shared.py` unmodified after restoration. Numbers differing from this plan's are EXPECTED and satisfy this item; silently reusing this plan's numbers does NOT.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted return values of `ipd_lifecycle.checkout_control_root` and `runner_shared.state_root` as called from inside the lane, showing the first resolving to the MAIN checkout's `.aw`. Plus a quoted sentence from `checkout_control_root`'s docstring naming the `--git-common-dir` collapse as the `dh0uno` fix. Plus one line stating which resolver `dh0uno` fixed and why the other's target-relative behavior is correct and out of scope. A green suite alone does NOT satisfy this item, because a green suite is equally consistent with the relevant tests having been deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted PASS of the new test, AND pasted FAILURE of that same test under the fact-4 mutation, AND pasted PASS after restoring. The failure output must show the assertion comparing the primary repo root against the lane worktree path, which is what proves the test observes the contract and not something incidental. Plus confirmation, shown by reading the test, that it asserts on the FIRST recorded cwd only and not on every call (F-5), and that its docstring states both what it defends and that it does not re-assert the retracted divergence. A pass with no paired failure does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the `git diff` of the docstring, shown to contain ONLY docstring text changes with no executable line altered, and state how that was confirmed from the diff. The diff must show: both stale counts REMOVED; the "permanently red" conclusion REMOVED; an independent justification present that does not depend on `dh0uno`; the E-03 test cited by name; and `Callers MUST pass the primary repo, never work_dir` still present. Confirm NO new test count was introduced anywhere in the paragraph (F-3). Do NOT satisfy this item with a test that inspects source text; the diff is the evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` for all three sites from F-6, pasted, each showing the corrected premise: the `rerun_suite` comment no longer claiming a lane suite is permanently red, and both comments naming `runner_shared` rather than `oc_runipd` as the definition site. Confirm for each that the still-true point was PRESERVED (the injection design, and the reason it is a parameter) rather than deleted, and that no executable line changed. Confirm no NEW citation to a nonexistent test class was added (F-9).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-05 in order, respecting the declared `Depends on` edges; treat
E-01 as a hard gate, since E-03's whole justification is the measured absence of a pin and a plan that adds
a duplicate pin would be doing different work than this one describes; commit only the two paths in
`- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner output for every claim
of a passing test, INCLUDING the paired mutation failure E-03 requires; and verify each `V-*` in a separate
pass from the `E-*` that produced it. Do NOT mark this plan executed or move it to
`.aw/records/plans/executed/` until every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms.

THE ONE WAY TO GET THIS PLAN WRONG, stated because E-04 hands the executor a paragraph explaining that the
contract's stated reason is false: the contract itself is CORRECT and must not move. `run_suite_check` runs
in the primary checkout before this plan and after it. If you find yourself editing the call site for any
purpose other than the temporary, reverted mutation E-01 and V-03 require, stop.

Backlog item `nbu56f` is this plan's origin (`- From-Backlog: nbu56f`). That item carries NO
`- Blocks-Release:` gate and none is invented here, consistent with its `chore` work kind: measurement
confirms the classification, since `run_suite_check` gives no wrong answer and no user waits on the
difference. What the item under-measured was not severity but SHAPE, since it recorded the fix as "a
one-line courtesy at most" without knowing the contract had no test (F-4).
