# IPD: Make the leak-sanitizer bundle tests hermetic so they do not silently stop testing outside the home tree

- Date: 2026-09-17
- Kind: child
- Concern: `tests/test_run_analytics_spa.py::LeakSanitizerTests` derives BOTH its planted leak and its detector from the same value, so the pair silently agrees whenever the checkout is not under the maintainer's home directory. `setUp` computes `self.repo = Path(__file__).resolve().parent.parent` and builds the ruleset from it; the tests then plant `f"{self.repo}/.aw/worktrees/lane-x"` and assert the sanitizer flags it. Measured 2026-09-17: `build_ruleset(<the repo root, under $HOME>)` scanning that planted string yields 2 `fail` findings, while `build_ruleset(<a temp-directory root>)` scanning the equivalent string yields 0. So in a checkout outside `$HOME` two tests FAIL, including the one named `test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path` whose entire purpose is to prove the detector was looking.
- Scope: Make these tests assert the sanitizer's behavior independently of where the repository happens to sit, so they neither fail in a legitimate checkout location nor pass vacuously. Does NOT change `leak_sanitizer`'s rules, the SPA renderer, or any other test module.
- Scope-Paths: tests/test_run_analytics_spa.py
- Item-Dependencies: none
- Status: to-review
- Set: spahermetic
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: zx9dkq

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from a false alarm this defect caused mid-merge. While resolving the `tx6q0h` lane I created a worktree under a temporary directory, ran the suite to establish a baseline, and got 2 failures that do NOT occur on `main`. I initially had to rule out my own merge as the cause, which is exactly the cost a non-hermetic test imposes: it fires at the moment you are least able to tell a real regression from an environment artifact. ROOT CAUSE MEASURED, not guessed: the planted leak and the ruleset are both derived from `self.repo`, so outside `$HOME` the planted string contains no home-path substring for the rules to match and the assertion `assertTrue(findings)` fails. Verified by calling `leak_sanitizer.build_ruleset` directly for two repo roots: 2 findings under the home tree, 0 under `/tmp`. WORKED AROUND at the time by moving the worktree under `.aw/worktrees/` (which is what the runner itself does), so this was never a blocker; it is a trap for the next person who does the obvious thing.

## Goal

Make these two assertions mean the same thing wherever the repository is checked out: that the sanitizer
detects a real absolute path travelling through a rendered bundle.

The test's own docstring already states the standard it is trying to hold ("The control run is therefore
not optional decoration; it is what makes the clean assertion evidence"). This plan makes that true in
every checkout rather than only in one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: prove the coupling, then break it

- [ ] E-01 REPRODUCE THE LOCATION DEPENDENCE DIRECTLY, without needing a second checkout, so the defect is demonstrated rather than described. Call `leak_sanitizer.build_ruleset` for two repo roots (one under the invoking user's home directory, one under a temporary directory) and scan the SAME shape of planted string against each, showing findings for the first and none for the second. This is the measurement that identifies the coupling as `self.repo` feeding both sides.
  - Depends on: none
  - Expected outcome: pasted output showing a nonzero finding count for the home-tree ruleset and zero for the temp-tree ruleset on equivalent planted input, at execution HEAD.
  - Execution state: pending

- [ ] E-02 DECIDE AND RECORD WHAT THESE TESTS ACTUALLY ASSERT, because the fix follows from it and the two candidate readings differ. Reading A: "a real absolute path under this repo's root is detected", which is inherently location-dependent and should be SKIPPED with a stated reason when the checkout is not under a home directory. Reading B: "the sanitizer detects a home-style absolute path travelling through the renderer", which is location-INDEPENDENT and should plant a synthetic home-style path rather than the live repo root. State which reading each of the three tests in the class holds (`test_the_produced_bundle_is_clean`, `test_the_CONTROL_proves_...`, `test_a_leaky_value_travelling_through_a_finding_is_still_detected`) and note that the CONTROL test's purpose (proving the detector was looking) makes a silent skip the wrong answer for it specifically.
  - Depends on: E-01
  - Expected outcome: a written per-test statement of which reading it holds and therefore which remedy applies, with the CONTROL test's special status addressed explicitly.
  - Execution state: pending

- [ ] E-03 MAKE THE ASSERTIONS LOCATION-INDEPENDENT per E-02's decision, preferring a synthetic home-style root for the planted leak over deriving it from the live checkout. The ruleset and the planted value must no longer be able to agree by both being empty of anything detectable. DO NOT weaken any assertion to make it pass: turning `assertTrue(findings)` into a tolerance of zero findings would delete the only thing the CONTROL test proves, which is the same class of error as lowering a threshold to silence a guard. If a test genuinely cannot be made location-independent, SKIP it with an explicit reason naming the condition, never let it pass vacuously.
  - Depends on: E-02
  - Expected outcome: the tests passing in BOTH a home-tree checkout and a temp-directory checkout, with the assertions still demanding real findings; pasted from both locations.
  - Execution state: pending

- [ ] E-04 ADD THE NON-VACUITY GUARD, so this fix cannot itself decay into a test that passes because it checks nothing. Assert that the detector fires on the planted input AND does not fire on a control string that should be clean, in the same test run. That pairing is what makes the clean assertion evidence, per the class's own docstring, and it is the property that must survive relocation.
  - Depends on: E-03
  - Expected outcome: pasted evidence that the planted case yields findings and the clean case yields none, from a checkout OUTSIDE the home tree, proving the guard works where the original failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SUITE IS THE INTEGRATION GATE, which is what makes a non-hermetic test expensive rather than annoying. `tests/test_orchestrator_retirement.py`'s own docstring records that the runner gates lane integration on a bare whole-repo `pytest`, and that one red test refused integration for every lane that finished afterwards, stranding eight plans in one night. A test that fails on checkout LOCATION is a latent version of that.
- THE RUNNER PUTS LANES UNDER `.aw/worktrees/`, so the runner's own lanes are inside the repo tree and never hit this. That is why the defect has stayed hidden: only a hand-made worktree elsewhere triggers it.
- WEAKENING A GUARD TO MAKE IT PASS IS FORBIDDEN, and this repository has the precedent written down: `tests/test_nested_tty_noninteractive.py`'s docstring records that lowering a threshold "would have made this pass while silently accepting a future change that actually removed a `stdin=`". The same reasoning applies to accepting zero findings here.
- A SKIP WITH A STATED REASON IS HONEST; A VACUOUS PASS IS NOT. If a property genuinely depends on the environment, the repository's own standard (record the limit rather than assert past it) says to skip loudly.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | MEDIUM | `tests/test_run_analytics_spa.py` `setUp` | **THE PLANTED LEAK AND THE DETECTOR COME FROM ONE VALUE.** `self.repo = Path(__file__).resolve().parent.parent` feeds both `build_ruleset(self.repo)` and the planted `f"{self.repo}/.aw/worktrees/lane-x"`, so the two agree vacuously wherever the repo root contains nothing the rules recognize. | the `setUp` body; `build_ruleset` returning 2 findings for a home-tree root and 0 for a temp-directory root on equivalent input |
| F2 | MEDIUM | `test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path` | **THE TEST WHOSE JOB IS PROVING THE DETECTOR WAS LOOKING IS THE ONE THAT FAILS.** Its message reads "the CONTROL found nothing, so the detector was not looking and the clean result above is meaningless" -- which is accurate about the environment and misleading about the code. A reader sees an anti-vacuity guard failing and reasonably suspects the sanitizer. | the failure message, observed in a temp-directory worktree |
| F3 | MEDIUM | this session | **IT COST A REAL FALSE ALARM AT THE WORST MOMENT.** It fired while I was establishing a baseline for a conflicted merge, so it had to be ruled out as a merge regression before the merge could proceed. A test that fails for environmental reasons during a risky operation is a tax on exactly the care it should support. | the session transcript: 2 failures in the temp-directory worktree, 0 on `main` at the same commit |
| F4 | LOW | the fix direction | **THE OBVIOUS FIX IS THE WRONG ONE.** Making the assertion tolerate zero findings would turn both tests green everywhere and delete their entire value, since what they assert is that detection HAPPENS. Named here so an executor under time pressure does not reach for it. | the class docstring's own statement that the control is "what makes the clean assertion evidence" |
| F5 | LOW | scope | ONLY THIS TEST MODULE IS IN SCOPE, and that is a claim to re-verify rather than assume: other tests may derive fixtures from `Path(__file__)` in the same shape. E-01 should note any it encounters, as a finding for a follow-up rather than a silent widening. | `- Scope-Paths:` declares one file |

## Proposed changes (ordered, validatable)

1. Reproduce the location dependence by calling `build_ruleset` for two roots (E-01).
2. Decide and record what each of the three tests actually asserts (E-02).
3. Make the assertions location-independent, preferring a synthetic home-style planted path; skip loudly rather than pass vacuously if a property is genuinely environmental (E-03).
4. Add the paired non-vacuity guard and prove it from outside the home tree (E-04).

## Deferred / out of scope (with reason)

- CHANGING `leak_sanitizer`'s RULES. The sanitizer is behaving correctly: there is no home-path leak to find in a `/tmp` string. The defect is in the test's construction, and widening scope to the detector would put a shipped security surface at risk to fix a fixture.
- AUDITING EVERY TEST THAT DERIVES A FIXTURE FROM `Path(__file__)`. Plausibly the same shape exists elsewhere, but a repo-wide sweep is its own plan with its own measurement. E-01 records any encountered as a finding.
- MAKING THE SUITE PASS IN AN ARBITRARY LOCATION GENERALLY. Out of scope and probably not desirable: some tests legitimately depend on being in a git repository with this layout. This plan fixes the tests whose assertion does NOT depend on location but whose implementation did.

## Scope check

- Over-scope: none. One test module, one coupling.
- Under-scope: none for the reported defect. The wider `Path(__file__)` sweep is deferred above with a reason.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted).
2. The three `LeakSanitizerTests` shown passing from a checkout INSIDE the home tree.
3. The same three shown passing from a checkout OUTSIDE it (a temporary directory), which is the condition that currently fails. Both pasted.
4. The non-vacuity pairing demonstrated in the outside-home run: planted input yields findings, clean input yields none.
5. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change expected: this is test construction, not a documented contract, and `- Scope-Paths:`
declares no `.spec.md`. If the executor finds spec text asserting that the SPA bundle is sanitizer-clean
as a shipped guarantee, that guarantee is unaffected by this plan (the assertion is preserved, only its
construction changes); record the citation here rather than editing the spec.

## Open questions

### OQ-01: For a property that genuinely depends on the checkout location, skip with a reason or synthesize the input?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because E-02 decides it per test from the code and E-03 implements the stronger option by default (synthesize a home-style path, so the assertion runs everywhere). FOR SYNTHESIZING: the property under test is "the sanitizer detects a home-style absolute path travelling through the renderer", which does not actually depend on where this repo sits, so a synthetic path tests the real thing in every checkout. FOR SKIPPING: if a test genuinely asserts something about THIS repository's own root, a loud skip is more honest than a synthetic substitute that quietly tests something adjacent. Recorded because the choice is a judgement about what the test is FOR, and getting it wrong produces a green test that proves less than it claims.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output at execution HEAD showing `build_ruleset` for a home-tree root yielding a nonzero finding count on the planted string and for a temp-directory root yielding zero on the equivalent string. The two calls and their results must both be visible, so the coupling is demonstrated rather than asserted. PLUS any other test noted that derives a fixture from `Path(__file__)` in the same shape, or an explicit "none encountered".
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the written per-test statement quoted, covering all three tests in the class by name and saying which reading each holds and which remedy applies. The CONTROL test must be addressed explicitly, including why a silent skip is the wrong remedy for it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the three tests pasted PASSING from two different checkout locations, one inside the home tree and one outside it, with the location stated for each run. PLUS the assertions quoted to show none was weakened: `assertTrue(findings)` (or its replacement) must still demand real findings, and any `skip` must carry an explicit reason naming its condition.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: from the OUTSIDE-home run specifically, pasted evidence that the planted input yields findings AND the clean control yields none. Evidence from the home-tree run alone does NOT satisfy this item, since that is the location where the original tests already passed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (4 E-items in 1 task group, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with the SYNTHESIZE form and do
not guess a relaxation. SCOPE FENCE: this plan declares `tests/test_run_analytics_spa.py` only; an
out-of-scope edit must be made only if genuinely required and then JUSTIFIED to `aw ipd finalize` with a
`--scope-reason` per path. THE ONE THING THIS PLAN MUST NOT DO, stated because it is the shortest path to
green: do NOT weaken an assertion to tolerate zero findings. That would make both tests pass everywhere
while deleting the only property they assert, and it is the same error as lowering a guard's threshold to
silence it. A loud skip is acceptable; a vacuous pass is not. THE HARD-MUST HONESTY RULE: paste the ACTUAL
test output for every `V-*`, and for V-03 and V-04 paste it from BOTH checkout locations with the location
named, since a single-location run cannot demonstrate the fix. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
