# IPD: Make the leak-sanitizer bundle tests hermetic so they do not silently stop testing outside the home tree

- Date: 2026-09-17
- Kind: child
- Concern: `tests/test_run_analytics_spa.py::LeakSanitizerTests` plants its leak by interpolating the LIVE CHECKOUT PATH (`setUp` computes `self.repo = Path(__file__).resolve().parent.parent`; the tests plant `f"{self.repo}/.aw/worktrees/lane-x"` and assert the sanitizer flags it). Outside the maintainer's home directory that planted string contains no home-style path, so there is nothing for the rules to match and the assertion fails. Measured 2026-09-17 and RE-MEASURED at review: with a repo root under `$HOME` the planted string yields 2 `fail` findings (`home-path`, `handle`); with a temp-directory root the equivalent string yields 0. Exactly two of the three tests in the class then FAIL, including `test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path` whose entire purpose is to prove the detector was looking. CORRECTED AT REVIEW: the coupling is NOT that "both the planted leak and the detector are derived from `self.repo`". The RULESET IS EFFECTIVELY IDENTICAL for both roots (measured: same eight fail-rule names, empty difference), because `build_ruleset(repo_root)` uses `repo_root` only to load an optional repo allowlist/config and the leak patterns themselves are HARDCODED regexes (`leak_sanitizer.py:65-84`, e.g. `home-path` = `/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+`). Only the PLANTED VALUE varies with location. That distinction decides the fix, so it is stated here rather than left to be rediscovered.
- Scope: Make these tests assert the sanitizer's behavior independently of where the repository happens to sit, so they neither fail in a legitimate checkout location nor pass vacuously. Does NOT change `leak_sanitizer`'s rules, the SPA renderer, or any other test module.
- Scope-Paths: tests/test_run_analytics_spa.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: spahermetic
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: zx9dkq
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006, all FIXED; no open questions; readiness `go-pending-approval`. Reviewed at HEAD `481465ac`; `aw ipd lint --phase author` conforming before and after; plan byte-identical to the lane input. THE DEFECT REPRODUCES EXACTLY AND I RAN THE PLAN'S OWN MEASUREMENT RATHER THAN TRUSTING IT: a home-tree root yields 2 `fail` findings (`home-path`, `handle`) on the planted string while a temp-directory root yields 0, and with a synthetic outside-home root the per-test outcome is `test_the_produced_bundle_is_clean` PASS, `test_the_CONTROL_proves_...` FAIL, `test_a_leaky_value_travelling_...` FAIL, matching the plan's "two tests FAIL" claim precisely. The code description, the docstring quote, F4's warning against tolerating zero findings, and both deferrals all verify. BUT THE STATED ROOT CAUSE IS WRONG (PR-001, HIGH) AND WOULD MISDIRECT THE FIX: the Concern and F1 say the planted leak and the DETECTOR are both derived from `self.repo`, yet the RULESET IS LOCATION-INDEPENDENT. Measured: `build_ruleset` for a repo root and for a temp root give the SAME eight fail-rule names with an EMPTY difference, and the temp-root ruleset flags a home-style string (1 finding) while the repo-root ruleset finds 0 in a temp-style string; `repo_root` only selects an optional allowlist/config (`leak_sanitizer.py:441-478`) and the patterns are hardcoded regexes (`:65-84`, `home-path` = `/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+`). Only the PLANTED VALUE varies, so E-01 gained a mandatory part (b) proving that localization. THE REMEDY IS CORRECT AND I FOUND ITS TRAP (PR-002, HIGH): a home-style and a macOS-style placeholder path each yield 1 `fail` under BOTH rulesets, but a `Path.home()`-derived plant yields 2 under both only because this machine's home is `/home/<name>`; on a macOS home or with `HOME=/root` it would stop matching and the test would fail again, differently coupled, so E-03 now requires a FIXED LITERAL and V-03 refuses a home-derived one. ALSO: `test_the_produced_bundle_is_clean` references no `self.repo`, already passes outside the home tree, and carries the shipped sanitizer-clean guarantee, so it must NOT be touched (PR-003) though the plan asked E-02 to assign all three tests a remedy; and the non-vacuity pairing was ALREADY split across two test methods, breakable by `-k` or `pytest-randomly` even inside the home tree, so E-04 now requires both halves in ONE method plus an assertion on the rule name (`home-path`) and severity rather than a bare nonzero count (PR-004). Added a deliberate mutation check (PR-005) and the bare-run rule with the `770fkp` 31-failure lane baseline (PR-006). OQ-01 narrowed: no skip applies to any of these three tests, since neither affected test asserts anything about this repository's own root; only the general future case remains the maintainer's.

- 2026-09-18 reviewed (aw set): plan-review complete: APPROVE WITH REVISIONS APPLIED; 6 findings, all 6 FIXED, no open questions. The defect reproduces exactly (measured: 2 fail findings under a home-tree root vs 0 under a temp root; per-test PASS/FAIL/FAIL outside home, matching the plan's claim). But PR-001 HIGH: the stated root cause is wrong and would misdirect the fix. The ruleset is location-INDEPENDENT (measured: identical eight fail-rule names for both roots, empty difference; the temp-root ruleset flags a home-style string), because build_ruleset uses repo_root only for an optional allowlist and the leak patterns are hardcoded regexes; only the PLANTED VALUE varies. PR-002 HIGH: 'synthetic home-style root' did not exclude a Path.home()-derived plant, which passes here only because this machine's home is /home/<name> and would fail on macOS or with HOME=/root; E-03 now requires a fixed literal. PR-003: one of the three tests is unaffected and carries the shipped clean-bundle guarantee, so it must not be touched. PR-004: the non-vacuity pairing was already split across two methods and breakable by -k or random ordering; E-04 now requires one method plus a rule-name assertion. Also added a mutation check and the 770fkp bare-run baseline; readiness go-pending-approval

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

- [x] E-01 REPRODUCE THE LOCATION DEPENDENCE AND LOCALIZE IT TO THE PLANTED VALUE, without needing a second checkout, so the defect is demonstrated rather than described. Two measurements, and the SECOND is the one that identifies the fix. (a) Scan the planted string shape against a ruleset built for a home-tree root and for a temp-directory root, showing findings for the first and none for the second. (b) PROVE THE RULESET IS NOT THE VARIABLE: compare the two rulesets' fail-rule names (expect an empty difference) and show the TEMP-root ruleset flagging a home-style string, so the only thing that changed is the planted value. Without (b) an executor may "fix" the ruleset construction, which measurement shows would fix nothing (F6).
  - Depends on: none
  - Expected outcome: pasted output at execution HEAD showing (a) nonzero findings for the home-tree case and zero for the temp-tree case on equivalent planted input, and (b) the two rulesets' fail-rule names identical with an empty difference, plus the temp-root ruleset flagging a home-style string. Review's baseline for (a) was 2 findings (`home-path`, `handle`) vs 0, and for (b) eight identical rule names.
  - Execution state: performed

- [x] E-02 DECIDE AND RECORD WHAT EACH TEST ACTUALLY ASSERTS, because the remedy follows from it and the readings differ per test. Reading A: "a real absolute path under THIS repo's root is detected", which is inherently location-dependent and would warrant a loud SKIP outside a home directory. Reading B: "the sanitizer detects a home-style absolute path travelling through the renderer", which is location-INDEPENDENT and warrants planting a synthetic home-style path. State which reading each of the three tests holds, and note two things review already established so they are not re-litigated: `test_the_produced_bundle_is_clean` does NOT reference `self.repo`, already passes outside the home tree, and is therefore NOT part of this defect (F7); and the CONTROL test's purpose (proving the detector was looking) makes a silent skip the wrong answer for it specifically.
  - Depends on: E-01
  - Expected outcome: a written per-test statement of which reading it holds and therefore which remedy applies, explicitly recording that the clean-bundle test needs NO change, and addressing the CONTROL test's special status.
  - Execution state: performed

- [x] E-03 MAKE THE TWO AFFECTED ASSERTIONS LOCATION-INDEPENDENT by planting a SYNTHETIC home-style path instead of the live checkout root. Use a path that is home-style by CONSTRUCTION and independent of the invoking user, e.g. `/home/user/checkouts/agent-workflows/.aw/worktrees/lane-x` (the `user` placeholder is one the sanitizer's own rules deliberately allow, so this plan's text stays self-clean); do NOT build it from `Path.home()`, because that reintroduces an environment dependency (on a machine whose home is not under `/home`, such as macOS, the `home-path` rule would not match it). REVIEW MEASURED BOTH FORMS: the user-independent home-style and macOS-style placeholder strings each yield 1 `fail` finding when spelled with a REAL-looking account name under a home-tree ruleset AND under a temp-directory ruleset, while a `Path.home()`-derived string yields 2 under both only because this machine's home happens to be `/home/<name>`. So the fixed literal is the portable choice and it is what makes the assertion mean the same thing everywhere. DO NOT weaken any assertion to make it pass: turning `assertTrue(findings)` into a tolerance of zero findings would delete the only thing the CONTROL test proves, the same class of error as lowering a threshold to silence a guard. If a test genuinely cannot be made location-independent, SKIP it with an explicit reason naming the condition, never let it pass vacuously. LEAVE `test_the_produced_bundle_is_clean` ALONE (F7).
  - Depends on: E-02
  - Expected outcome: the three tests passing in BOTH a home-tree checkout and a temp-directory checkout, with the two fixed assertions still demanding real findings and the planted value shown to be a fixed literal rather than derived from the environment; pasted from both locations.
  - Execution state: performed

- [x] E-04 ADD THE NON-VACUITY GUARD IN ONE TEST, so the pairing cannot be broken by test selection or ordering. Assert that the detector fires on the planted input AND does not fire on a clean control string WITHIN A SINGLE TEST METHOD. WHY IN ONE METHOD, measured at review: the clean assertion and the CONTROL currently live in SEPARATE methods, so the class docstring's "the control run is what makes the clean assertion evidence" holds only if both happen to run; `pytest-randomly` is active and `-k` can select either alone (F8). A guard whose two halves can be separated is not a guard. ALSO ASSERT THE RULE NAMES, not merely a nonzero count, so a future change that starts matching for an unrelated reason cannot keep this green: the planted home-style path must be flagged by `home-path` specifically, at `fail` severity.
  - Depends on: E-03
  - Expected outcome: pasted evidence from a checkout OUTSIDE the home tree that a single test asserts both halves (planted yields `home-path`/`fail`, clean yields none) and passes, proving the guard works where the original failed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SUITE IS THE INTEGRATION GATE, which is what makes a non-hermetic test expensive rather than annoying. `tests/test_orchestrator_retirement.py`'s own docstring records that the runner gates lane integration on a bare whole-repo `pytest`, and that one red test refused integration for every lane that finished afterwards, stranding eight plans in one night. A test that fails on checkout LOCATION is a latent version of that.
- THE RUNNER PUTS LANES UNDER `.aw/worktrees/`, so the runner's own lanes are inside the repo tree and never hit this. That is why the defect has stayed hidden: only a hand-made worktree elsewhere triggers it.
- WEAKENING A GUARD TO MAKE IT PASS IS FORBIDDEN, and this repository has the precedent written down: `tests/test_nested_tty_noninteractive.py`'s docstring records that lowering a threshold "would have made this pass while silently accepting a future change that actually removed a `stdin=`". The same reasoning applies to accepting zero findings here.
- A SKIP WITH A STATED REASON IS HONEST; A VACUOUS PASS IS NOT. If a property genuinely depends on the environment, the repository's own standard (record the limit rather than assert past it) says to skip loudly.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | MEDIUM | `tests/test_run_analytics_spa.py` `setUp` | **THE PLANTED LEAK IS THE LIVE CHECKOUT PATH, so the test asserts a property of its own location.** `self.repo = Path(__file__).resolve().parent.parent` is interpolated into the planted string, which is therefore a home-style path in one checkout and a `/tmp` path in another. RESTATED AT REVIEW: the original wording ("the planted leak and the detector come from ONE value ... so the two agree vacuously") is WRONG about the mechanism and would misdirect the fix. See F6. | the `setUp` body; measured 2 findings (`home-path`, `handle`) for a home-tree root vs 0 for a temp-directory root |
| F6 | MEDIUM | `agent_workflows/leak_sanitizer.py:65-84`, `:441-455` | **THE RULESET IS NOT LOCATION-DEPENDENT AT ALL, so `build_ruleset(self.repo)` is not half of the coupling.** The fail patterns are HARDCODED (`home-path` = `/home/(?!u/|alice/|user/|USER/|<)[A-Za-z0-9._-]+`, `handle` = an escaped literal username fragment); `repo_root` only selects an optional repo allowlist/config. MEASURED: `build_ruleset(<repo>)` and `build_ruleset(<temp dir>)` yield the SAME eight fail-rule names with an EMPTY difference, and the temp-root ruleset flags a home-style string (1 finding) exactly as the repo-root ruleset does. So the remedy is to fix the PLANTED VALUE only; changing how the ruleset is built would fix nothing. | the two `build_ruleset` calls compared by rule name; a cross-check scanning a home-style string with the temp-root ruleset |
| F7 | LOW | `test_the_produced_bundle_is_clean` | THAT TEST DOES NOT USE `self.repo` AND ALREADY PASSES EVERYWHERE, so it is not part of this defect and must not be "fixed". Measured with a synthetic outside-home root: `findings=0 -> PASS`, while the other two FAIL. It reads only `self.ruleset`, which F6 shows is location-independent. E-02's per-test statement should record it as ALREADY location-independent rather than assigning it a remedy. | its body (no `self.repo` reference); the three-test simulation showing PASS/FAIL/FAIL |
| F8 | LOW | the class's pairing claim | THE CONTROL AND THE CLEAN ASSERTION ARE IN SEPARATE TEST METHODS, so the docstring's "the control run is what makes the clean assertion evidence" is true only across the whole class, not within any single test. `pytest-randomly` is active (per `addopts`), and either test can run alone under `-k`. E-04's "in the same test run" requirement is therefore the right instinct, and it should be satisfied by pairing them IN ONE TEST rather than by relying on both methods happening to run. | the two separate method bodies; the configured random ordering |
| F2 | MEDIUM | `test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path` | **THE TEST WHOSE JOB IS PROVING THE DETECTOR WAS LOOKING IS THE ONE THAT FAILS.** Its message reads "the CONTROL found nothing, so the detector was not looking and the clean result above is meaningless" -- which is accurate about the environment and misleading about the code. A reader sees an anti-vacuity guard failing and reasonably suspects the sanitizer. | the failure message, observed in a temp-directory worktree |
| F3 | MEDIUM | this session | **IT COST A REAL FALSE ALARM AT THE WORST MOMENT.** It fired while I was establishing a baseline for a conflicted merge, so it had to be ruled out as a merge regression before the merge could proceed. A test that fails for environmental reasons during a risky operation is a tax on exactly the care it should support. | the session transcript: 2 failures in the temp-directory worktree, 0 on `main` at the same commit |
| F4 | LOW | the fix direction | **THE OBVIOUS FIX IS THE WRONG ONE.** Making the assertion tolerate zero findings would turn both tests green everywhere and delete their entire value, since what they assert is that detection HAPPENS. Named here so an executor under time pressure does not reach for it. | the class docstring's own statement that the control is "what makes the clean assertion evidence" |
| F5 | LOW | scope | ONLY THIS TEST MODULE IS IN SCOPE, and that is a claim to re-verify rather than assume: other tests may derive fixtures from `Path(__file__)` in the same shape. E-01 should note any it encounters, as a finding for a follow-up rather than a silent widening. | `- Scope-Paths:` declares one file |

## Proposed changes (ordered, validatable)

1. Reproduce the location dependence AND localize it to the planted value, proving the ruleset is not the variable (E-01).
2. Decide and record what each of the three tests actually asserts, including that the clean-bundle test needs no change (E-02).
3. Plant a FIXED synthetic home-style literal (not a `Path.home()`-derived one) so the two affected assertions mean the same thing everywhere; skip loudly rather than pass vacuously if a property is genuinely environmental (E-03).
4. Put the non-vacuity pairing inside ONE test, assert the rule name and severity, and prove it from outside the home tree (E-04).

REVIEW NOTE: this plan changes only two of the three tests. `test_the_produced_bundle_is_clean` is not
affected by the defect (F7) and touching it would be over-scope.

## Deferred / out of scope (with reason)

- CHANGING `leak_sanitizer`'s RULES. The sanitizer is behaving correctly: there is no home-path leak to find in a `/tmp` string. The defect is in the test's construction, and widening scope to the detector would put a shipped security surface at risk to fix a fixture.
  - Carrier-Declined: this row defers NOTHING, so there is no obligation to carry. It records a decision NOT to act: the sanitizer is behaving correctly and needs no change. Execution confirmed it rather than assuming it, and the confirmation is the point: the rules were not touched (`- Scope-Paths:` names one test file and the diff is confined to `tests/test_run_analytics_spa.py`), and `aw sanitize --agent` reports `"outcome":"clean","findings":0` with the change in place. Filing a carrier here would assert future work this plan argues against.
- AUDITING EVERY TEST THAT DERIVES A FIXTURE FROM `Path(__file__)`. Plausibly the same shape exists elsewhere, but a repo-wide sweep is its own plan with its own measurement. E-01 records any encountered as a finding.
  - Carrier: rd2yh7
- MAKING THE SUITE PASS IN AN ARBITRARY LOCATION GENERALLY. Out of scope and probably not desirable: some tests legitimately depend on being in a git repository with this layout. This plan fixes the tests whose assertion does NOT depend on location but whose implementation did.
  - Carrier-Declined: this row is a SCOPE FENCE, not a deferred obligation. The plan's stated position is that the general property is not even desirable, because some tests legitimately require being in a git repository with this layout, so there is nothing outstanding for a carrier to track. A carrier here would manufacture an obligation the plan deliberately declines, and would misrepresent a boundary as a backlog.

CARRIER NOTE, added at execution. `aw ipd lint --phase pre-transition --detail` raised the advisory
`check.ipd-uncarried-obligation` against all three rows above plus `OQ-01`, on the correct general
ground that an obligation recorded only inside an `executed` plan classes as `done` in `aw attention`
and disappears. Each row is now answered explicitly: two are genuine obligations and one carrier was
filed for each (`rd2yh7` for the audit, `5mc38x` for `OQ-01`), and two are decisions NOT to act, where
filing a carrier would manufacture work the plan deliberately declines. Stating which is which is the
point, so a later reader does not have to re-derive it from the advisory count.

## Scope check

- Over-scope: none as scoped, but ONE RISK NAMED at review: the plan spoke of "these tests" and "both
  tests" interchangeably across three tests, and `test_the_produced_bundle_is_clean` is NOT affected (F7).
  An executor who "fixed" all three would be editing a passing test for no reason. E-02 and E-03 now say so.
- Under-scope: none for the reported defect. The wider `Path(__file__)` sweep is deferred below with a
  reason. NOTE the non-vacuity gap E-04 closes is slightly wider than the location defect: the pairing was
  ALREADY split across two test methods before this plan, so it was already breakable by `-k` or by random
  ordering even inside the home tree (F8). That is in scope because E-04 is where the pairing is asserted.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted). RUN IT BARE: `pyproject.toml` `addopts` already supplies the quiet/parallel/fast-subset flags, and a second `-q` suppresses the summary line this item requires. A managed worker lane also fails a set of lifecycle tests BY DESIGN (backlog `770fkp`, measured at 31 in this session), so take the baseline in the SAME tree and gate on NO NEW failures rather than an absolute count.
2. The three `LeakSanitizerTests` shown passing from a checkout INSIDE the home tree.
3. The same three shown passing from a checkout OUTSIDE it (a temporary directory), which is the condition that currently fails. Both pasted. STATE THE MEASURED BASELINE THIS FIX MUST FLIP, so the after-state is comparable: at review, an outside-home root gives `test_the_produced_bundle_is_clean` PASS, `test_the_CONTROL_proves_...` FAIL, `test_a_leaky_value_travelling_...` FAIL.
4. The non-vacuity pairing demonstrated in the outside-home run, WITHIN ONE TEST METHOD: planted input flagged by `home-path` at `fail` severity, clean input yielding none. Two separate green methods do not satisfy this (F8).
5. THE PLANTED VALUE SHOWN TO BE ENVIRONMENT-FREE: quote it and show it contains no `Path.home()`, `$HOME`, or checkout-derived component. This is the assertion that the fix is actually hermetic rather than differently coupled.
6. A DELIBERATE MUTATION CHECK, cheap and decisive: temporarily break the planted literal (e.g. change it to a `/tmp/...` path) and show the fixed test FAILS. A test that passes both before and after such a mutation is not testing detection.
7. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec change expected: this is test construction, not a documented contract, and `- Scope-Paths:`
declares no `.spec.md`. If the executor finds spec text asserting that the SPA bundle is sanitizer-clean
as a shipped guarantee, that guarantee is unaffected by this plan (the assertion is preserved, only its
construction changes); record the citation here rather than editing the spec.

REVIEW CONFIRMED THE PRESERVATION CLAIM IS SAFE TO MAKE: the shipped guarantee lives in
`test_the_produced_bundle_is_clean`, which this plan does NOT touch (F7), so the clean-bundle assertion is
preserved byte-for-byte rather than merely re-expressed. The two tests that DO change are the control and
the leak-through-a-finding case, neither of which is a shipped guarantee about the bundle.

## Open questions

### OQ-01: For a property that genuinely depends on the checkout location, skip with a reason or synthesize the input?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: 5mc38x
- Resolution or deferral rationale: NOT blocking, because E-02 decides it per test from the code and E-03 implements the stronger option by default (synthesize a home-style path, so the assertion runs everywhere). FOR SYNTHESIZING: the property under test is "the sanitizer detects a home-style absolute path travelling through the renderer", which does not actually depend on where this repo sits, so a synthetic path tests the real thing in every checkout. FOR SKIPPING: if a test genuinely asserts something about THIS repository's own root, a loud skip is more honest than a synthetic substitute that quietly tests something adjacent. Recorded because the choice is a judgement about what the test is FOR, and getting it wrong produces a green test that proves less than it claims.
  NARROWED AT REVIEW, and the narrowing removes most of the judgement: measurement shows NEITHER of the two
  affected tests asserts anything about THIS repository's root. Both assert that a home-style absolute path
  travelling through the renderer is detected, and the live root was merely a convenient source of such a
  path. Since the detector's `home-path` rule is a hardcoded regex that is identical in every checkout
  (F6), a synthetic literal tests the SAME property rather than an adjacent one, so the "FOR SKIPPING"
  branch has no applicable case here and no skip should be introduced. What remains genuinely open, and is
  the maintainer's, is only whether a future test that DOES want to assert something about the live root
  should skip or synthesize; that question is not raised by this plan's three tests.
  EXECUTED AS THE SYNTHESIZE FORM, per the execution contract, and the review narrowing HELD under
  execution measurement: `build_ruleset` for a home-tree root and for a temp-directory root give the same
  eight fail-rule names with an empty difference, and the temp-root ruleset flags a home-style string at
  `fail`, so a fixed synthetic literal tests the same property in every checkout (V-01(b)). No `skip` was
  introduced anywhere in the class and no assertion was relaxed; both were tightened to demand the
  `home-path` rule at `fail` severity specifically (V-03).
  CARRIER FILED: backlog `5mc38x` (`open`, followup, low) carries the residual maintainer question about a
  FUTURE test that genuinely wants to assert something about the live checkout root. Filed because this
  plan is reaching `executed` and an open question recorded only inside an executed plan classes as `done`
  in `aw attention` and vanishes; the question itself is unchanged and remains the maintainer's.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted output at execution HEAD for BOTH measurements. (a) `build_ruleset` for a home-tree root yielding a nonzero finding count on the planted string and for a temp-directory root yielding zero on the equivalent string, with both calls and both results visible. (b) THE LOCALIZATION: the two rulesets' fail-rule names compared with an empty difference, AND the temp-root ruleset shown flagging a home-style string. Part (b) is not optional: without it the plan's original (wrong) reading that the ruleset is half the coupling would stand, and the fix could be aimed at the wrong side (F6). PLUS any other test noted that derives a fixture from `Path(__file__)` in the same shape, or an explicit "none encountered".
  - Observed evidence: run at execution HEAD `e87eaca4` in this lane, calling `leak_sanitizer.build_ruleset` directly for two roots. Both the plan's numbers reproduce EXACTLY.

    ```text
    repo root      = <lane worktree root, under the home tree>
    temp root      = /tmp/aw-e01-oqql0hwq

    === E-01(a): the PLANTED STRING SHAPE, scanned with the ruleset built for each root ===
    home-tree root   planted=<p>partial work at <lane worktree root>/.aw/worktrees/lane-x</p>
    home-tree root   findings=2 -> [('home-path', 'fail'), ('handle', 'fail')]
    temp-dir root    planted=<p>partial work at /tmp/aw-e01-oqql0hwq/.aw/worktrees/lane-x</p>
    temp-dir root    findings=0 -> []

    === E-01(b): PROVE THE RULESET IS NOT THE VARIABLE ===
    fail-rule names (repo root) = ['handle', 'home-path', 'other-account', 'private-repo', 'session-id', 'users-path', 'vc-home', 'windows-home']
    fail-rule names (temp root) = ['handle', 'home-path', 'other-account', 'private-repo', 'session-id', 'users-path', 'vc-home', 'windows-home']
    identical                   = True
    symmetric difference        = []
    home-style string           = /ho + me/dev_user/checkouts/agent-workflows/.aw/worktrees/lane-x
    TEMP-root ruleset flags it  = 1 [('home-path', 'fail')]
    REPO-root ruleset flags it  = 1 [('home-path', 'fail')]
    ```

    (a) 2 findings for the home-tree root vs 0 for the temp root on equivalent planted input, matching review's baseline of `home-path` + `handle` vs none. (b) EIGHT identical fail-rule names, empty symmetric difference, and the TEMP-root ruleset flags a home-style string at `fail` exactly as the repo-root ruleset does. So the ruleset is NOT half the coupling and the remedy belongs on the planted value alone (F6 confirmed, the plan's original F1 wording refuted).

    OTHER TESTS DERIVING A FIXTURE FROM `Path(__file__)` IN THE SAME SHAPE: none encountered that plant the result as leak-detector INPUT. `Path(__file__)` is used widely in this module and elsewhere, but for reading source text or locating `pyproject.toml` (e.g. `NoNewTestDependencyTests` at `tests/test_run_analytics_spa.py:2723` and `:2745`), never as a value asserted to match a leak rule. The deferred repo-wide sweep therefore has no new lead from this execution.

    ONE MATERIAL DISCREPANCY WITH THE PLAN'S BASELINE, recorded because it changes what V-03 flips (DECISION 02-zx9dkq-D1): at execution HEAD the three tests ALREADY PASS outside the home tree, so the plan's "two tests FAIL" baseline no longer reproduces. Commit `74858380` (2026-09-17 22:17:42 -0400), which is NOT an ancestor of the plan's review HEAD `481465ac` (2026-09-17 22:01:11 -0400), added a `_leaky_repo_path` property that falls back to a synthetic string when the live root matches no rule. That masks the SYMPTOM while leaving the plan's requirements unmet: the plant was still an environment BRANCH (2 findings inside the home tree, 1 outside, i.e. a different input asserted in each location), the pairing was still split across methods, and no rule name was asserted.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the written per-test statement quoted, covering all three tests in the class by name and saying which reading each holds and which remedy applies. It MUST record that `test_the_produced_bundle_is_clean` needs no change, with the evidence that it references no `self.repo` and already passes outside the home tree (F7); a statement that assigns it a remedy is wrong and does not satisfy this item. The CONTROL test must be addressed explicitly, including why a silent skip is the wrong remedy for it.
  - Observed evidence: THE PER-TEST STATEMENT, one row per test in `LeakSanitizerTests`, each naming the reading it holds and the remedy that follows.

    1. `test_the_produced_bundle_is_clean` holds NEITHER reading, because it plants nothing: it renders the fixture bundle and asserts the finding list is empty. It is LOCATION-INDEPENDENT ALREADY and gets NO REMEDY. Evidence, both checked at execution HEAD: its body references no `self.repo` (it reads only `self.ruleset` and `render_document(_model())`), and it PASSED in the outside-home checkout before any edit of mine (`test_the_produced_bundle_is_clean PASSED`, in the run where the class was measured). It also carries the shipped sanitizer-clean guarantee, so editing it would put a real contract at risk to fix a fixture. NOT TOUCHED: confirmed by diff, the method body is byte-identical to HEAD.

    2. `test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path` holds READING B: "the sanitizer detects a home-style absolute path travelling through the renderer". It does not assert anything about THIS repository's root; the live root was merely a convenient source of a home-style path, and since `home-path` is a hardcoded regex identical in every checkout (V-01(b)), a synthetic literal tests the SAME property rather than an adjacent one. REMEDY: plant a fixed home-style literal (E-03), and additionally host both halves of the non-vacuity guard (E-04). A SILENT SKIP IS THE WRONG REMEDY FOR THIS TEST SPECIFICALLY: its entire purpose is to prove the detector was looking, so a skip would remove the evidence that makes the clean assertion in row 1 meaningful, and would do so exactly in the environments where nobody is watching. A skip here converts "the detector is proven awake" into "nobody checked", which is the same end state as the vacuous pass the plan forbids.

    3. `test_a_leaky_value_travelling_through_a_finding_is_still_detected` holds READING B as well: the property is that a real absolute path riding inside an `AnalysisResult` name survives rendering and is still detected, which is a claim about the renderer-plus-sanitizer boundary and not about where the repo sits. REMEDY: the same fixed literal (E-03) plus a rule-name assertion, so it cannot stay green on an unrelated match.

    NEITHER remedy is a skip and no `skip` was introduced anywhere in the class, which is the conclusion OQ-01 was narrowed to at review: with the property established as location-independent for both affected tests, the "FOR SKIPPING" branch has no applicable case here.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the three tests pasted PASSING from two different checkout locations, one inside the home tree and one outside it, with the location stated for each run. PLUS the assertions quoted to show none was weakened: `assertTrue(findings)` (or its replacement) must still demand real findings, and any `skip` must carry an explicit reason naming its condition. PLUS the planted value quoted, shown to be a FIXED LITERAL and not derived from `Path.home()`, `$HOME`, or the checkout path; a `Path.home()`-derived plant does not satisfy this item because it would still depend on the machine's home layout.
  - Observed evidence: both runs taken AFTER the final `ruff format` pass, so they reflect the committed code.

    RUN 1, LOCATION: INSIDE THE HOME TREE (this lane worktree, under the maintainer's home directory).

    ```text
    rootdir: <lane worktree root, under the home tree>
    collected 49 items / 46 deselected / 3 selected

    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_a_leaky_value_travelling_through_a_finding_is_still_detected PASSED [ 33%]
    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path PASSED [ 66%]
    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_the_produced_bundle_is_clean PASSED [100%]

    ======================= 3 passed, 46 deselected in 0.19s =======================
    ```

    RUN 2, LOCATION: OUTSIDE THE HOME TREE (`/tmp/opencode/aw-outside/agent-workflows`, a temp-directory copy of the tracked files). This is the condition that the plan recorded as failing.

    ```text
    rootdir: /tmp/opencode/aw-outside/agent-workflows
    collected 49 items / 46 deselected / 3 selected

    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_the_produced_bundle_is_clean PASSED [ 33%]
    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_a_leaky_value_travelling_through_a_finding_is_still_detected PASSED [ 66%]
    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path PASSED [100%]

    ======================= 3 passed, 46 deselected in 0.19s =======================
    ```

    THE PLANTED VALUE, QUOTED, AND WHY IT IS ENVIRONMENT-FREE. Two class constants replace the old property:

    ```python
    PLANTED_HOME_PATH = "/ho" + "me/dev_user/checkouts/agent-workflows"
    CLEAN_CONTROL_PATH = "/tmp/build-area/checkouts/agent-workflows"
    ```

    Both are fixed literals. Inspected over the whole class body: NO `$HOME`, NO `os.environ`, and NO interpolation of `self.repo` into any planted value (`"{self.repo"` and `"self.repo}"` both absent). `Path.home()` appears twice in the class, BOTH times inside the docstring prose explaining why it must NOT be used (lines 2801 and 2806), never in code. `self.repo` survives in exactly two places and neither is a plant: `self.repo = Path(__file__)...` and `build_ruleset(self.repo)`, the latter being correct because V-01(b) proved the ruleset is location-independent. The old `_leaky_repo_path` property, which BRANCHED on the environment, is deleted.

    NO ASSERTION WAS WEAKENED; both were STRENGTHENED, and no `skip` was introduced anywhere in the class. The replacements demand MORE than the originals did:

    ```python
    # was: self.assertTrue(findings, ...) then assertIn("fail", {f.severity for f in findings})
    self.assertIn(
        ("home-path", "fail"),
        {(f.rule, f.severity) for f in flagged},
        "the CONTROL found no home-path leak, so the detector was not looking and the clean "
        "result above is meaningless",
    )

    # was: self.assertTrue(findings, "a real absolute path passed through undetected")
    self.assertIn(
        ("home-path", "fail"),
        {(f.rule, f.severity) for f in findings},
        "a real absolute path passed through undetected",
    )
    ```

    A nonzero count no longer satisfies either one: the specific `home-path` rule at `fail` severity must be present, so tolerating zero findings is impossible by construction rather than by convention.

    THE MUTATION CHECK CONFIRMS DETECTION IS REAL (validation item 6), run in the OUTSIDE-home checkout with `-p no:randomly` for deterministic ordering. Mutating the planted literal to a non-home-style `/tmp` path makes BOTH fixed tests fail, and mutating the clean control to be home-style makes the negative half object:

    ```text
    --- MUTATION 1: planted literal -> non-home-style /tmp path (rc=1) ---
    ...test_a_leaky_value_travelling_through_a_finding_is_still_detected FAILED [ 33%]
    ...test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path FAILED [ 66%]
    ...test_the_produced_bundle_is_clean PASSED [100%]
    ================== 2 failed, 1 passed, 46 deselected in 0.22s ==================
    --- MUTATION 2: clean control -> ALSO home-style (rc=1) ---
    ...test_a_leaky_value_travelling_through_a_finding_is_still_detected PASSED [ 33%]
    ...test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path FAILED [ 66%]
    ...test_the_produced_bundle_is_clean PASSED [100%]
    ================== 1 failed, 2 passed, 46 deselected in 0.19s ==================
    --- RESTORED (rc=0) ---
    ======================= 3 passed, 46 deselected in 0.16s =======================
    ```

    `test_the_produced_bundle_is_clean` PASSES under both mutations, which is the expected signature of a test that plants nothing and was correctly left alone.

    ONE IMPLEMENTATION CONSTRAINT WORTH RECORDING, because it explains why the literal is spelled as a concatenation rather than whole. The plan suggested `/home/user/...`, but `user` is a placeholder the `home-path` rule DELIBERATELY ALLOWS, so a plant spelled that way yields ZERO findings and would have produced exactly the vacuous pass the plan forbids. The account name must therefore be real-looking (`dev_user`). Spelled whole, that string would then trip the repository's OWN leak gate on this source file; measured: a source line containing it whole yields 1 `fail` (`home-path`), the same line split as `"/ho" + "me/..."` yields 0. The concatenation is the existing idiom in this file and in `leak_sanitizer.py` itself, and `aw sanitize --agent` reports `"outcome":"clean","findings":0` with the change in place.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: from the OUTSIDE-home run specifically, the SINGLE test method quoted showing both halves in it, and its pasted pass: the planted input flagged by `home-path` at `fail` severity, and the clean control yielding none. Evidence from the home-tree run alone does NOT satisfy this item (that is where the originals already passed), and two separate passing test methods do NOT satisfy it either, since the whole point is that the pairing survives `-k` selection and random ordering (F8).
  - Observed evidence: THE SINGLE METHOD, quoted in full from `tests/test_run_analytics_spa.py:2844-2884`, with both halves inside it.

    ```python
    def test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path(self):
        """BOTH HALVES OF THE NON-VACUITY GUARD LIVE IN THIS ONE METHOD, deliberately.
        ...
        """

        planted = f"<p>partial work at {self.PLANTED_HOME_PATH}/.aw/worktrees/lane-x</p>"
        flagged = self.sanitizer.scan_text(planted, "control/planted.html", self.ruleset)
        self.assertIn(
            ("home-path", "fail"),
            {(f.rule, f.severity) for f in flagged},
            "the CONTROL found no home-path leak, so the detector was not looking and the clean "
            "result above is meaningless",
        )

        # THE NEGATIVE HALF: an equivalent non-home-style path must yield NOTHING. Without it, a rule
        # that matched every string would satisfy the assertion above.
        control = f"<p>partial work at {self.CLEAN_CONTROL_PATH}/.aw/worktrees/lane-x</p>"
        self.assertEqual(
            [
                f"{f.rule}\t{f.severity}"
                for f in self.sanitizer.scan_text(
                    control, "control/clean.html", self.ruleset
                )
            ],
            [],
            "a non-home-style path was flagged, so the detector is matching indiscriminately and "
            "the planted assertion above proves nothing",
        )
    ```

    The POSITIVE half asserts `("home-path", "fail")` is in the planted scan's `{(rule, severity)}` set; the NEGATIVE half asserts the clean control's finding list is exactly `[]`. Both are in ONE method, so no selection or ordering can separate them.

    THE PROOF IT SURVIVES `-k` SELECTION, taken in the OUTSIDE-home checkout with that ONE method selected ALONE, which is the case F8 identified as breaking the old split pairing:

    ```text
    rootdir: /tmp/opencode/aw-outside/agent-workflows
    collected 49 items / 48 deselected / 1 selected

    tests/test_run_analytics_spa.py::LeakSanitizerTests::test_the_CONTROL_proves_the_same_ruleset_flags_a_raw_absolute_path PASSED [100%]

    ======================= 1 passed, 48 deselected in 0.14s =======================
    ```

    One selected test, both halves asserted, green OUTSIDE the home tree, which is where the original CONTROL failed. Random ordering is likewise immaterial now: there is no second method the guard depends on. The per-rule finding sets behind the two halves were independently measured against the live ruleset: planted -> `1 [('home-path', 'fail')]`, clean control -> `0 []`.

    WHY THE PAIRING WENT INTO THE CONTROL TEST AND NOT INTO THE CLEAN-BUNDLE TEST (DECISION 02-zx9dkq-D4): merging into `test_the_produced_bundle_is_clean` would have satisfied F8 too, but the plan's execution contract forbids editing that test absolutely, and F7 measured why (it references no `self.repo` and already passed outside the home tree). Hosting both halves in the CONTROL method satisfies F8 without touching the fenced test, and it strengthens the module docstring's "adjacent" requirement rather than weakening it: the control can no longer run without its own negative case.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (4 E-items in 1 task group, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute with the SYNTHESIZE form and do
not guess a relaxation. SCOPE FENCE: this plan declares `tests/test_run_analytics_spa.py` only; an
out-of-scope edit must be made only if genuinely required and then JUSTIFIED to `aw ipd finalize` with a
`--scope-reason` per path. THE THREE THINGS THIS PLAN MUST NOT DO, each a short path to a green test that
proves less than it claims. FIRST, do NOT weaken an assertion to tolerate zero findings. That would make
both tests pass everywhere while deleting the only property they assert, and it is the same error as
lowering a guard's threshold to silence it. A loud skip is acceptable; a vacuous pass is not. SECOND, do NOT
derive the planted path from `Path.home()` or `$HOME`. It would pass on this machine and reintroduce the same
class of coupling, since the `home-path` rule matches `/home/<name>` specifically and a machine whose home is
elsewhere (a macOS `/Users/<name>` home, or a container with `HOME=/root`) would not match it. Plant a FIXED literal.
THIRD, do NOT edit `test_the_produced_bundle_is_clean`: measurement shows it references no `self.repo` and
already passes outside the home tree, so it is not part of this defect and it carries the shipped
sanitizer-clean guarantee. THE HARD-MUST HONESTY RULE: paste the ACTUAL
test output for every `V-*`, and for V-03 and V-04 paste it from BOTH checkout locations with the location
named, since a single-location run cannot demonstrate the fix. Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
