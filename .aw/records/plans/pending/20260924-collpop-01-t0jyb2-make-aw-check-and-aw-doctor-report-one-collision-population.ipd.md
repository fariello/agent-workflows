# IPD: Make aw check and aw doctor report one collision population

- Date: 2026-09-24
- Kind: child
- Concern: ONE PREDICATE, TWO POPULATIONS. `check_engine.check_collisions` is reached from `aw check all` via `check_engine.check_types` (`include_retired=include_retired`, which `cli` derives from `--all` and which defaults False) and from `aw doctor` via `doctor.probe_artifacts` (hardcoded `include_retired=True`). The backlog's 38-vs-86 `check.setid-collision` split is STALE: after D153 / spec `2lcqno` N1 and commit `4f1ca199` that rule reports zero on both. RE-MEASURED at HEAD `cfc7f5c1`, the live divergence is now ENTIRELY the identity-slot pass: `check_collisions(root)` returns 0 findings, `check_collisions(root, include_retired=True)` returns 3 `check.id6-identity-slot` (walkthroughs `zpbx7o`, `y5od1h`, `4fodkt`), and `doctor.probe_artifacts` surfaces those same 3. A fixture probe also exposed the SECOND axis spec `2lcqno` Section 6 names: doctor demotes any finding located under `executed/` into `executed_warnings`, so a `check.id6-collision` between two executed plans is an ERROR in `aw check all` and only a WARNING in `aw doctor`. The surfaces therefore disagree in BOTH directions today.
- Scope: Make the two surfaces report the same collision set, with the population chosen per rule and stated. IN: (a) the identity-slot pass in `check_engine.check_collisions` consumes the terminal-inclusive corpus, exactly as its id6 sibling already does, so both identity rules ignore the caller's liveness filter; (b) `doctor.probe_artifacts` passes `include_retired=include_executed` to `check_collisions` instead of a hardcoded `True`, so the setid pass (the only rule still honoring the flag) sees the same corpus as `aw check` at the default and under `-a`/`--all`; (c) doctor stops demoting the two IDENTITY rules into `executed_warnings`, because a collision with a terminal id6 is real (IPD `sk7ggr` F-3) and must not be softer in one surface; (d) a parity test over a fixture tree containing retired plans. OUT: renaming the three live walkthroughs (backlog `mw0s1y`); any change to what counts as retired; the `untracked/` axis; the setid-collision policy for backlog-shares-plan setids (`sjsoqq`).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_collision_population_parity.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: collpop
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: t0jyb2
- From-Backlog: lmjc8h
- Blocks-Release: next

## Workflow history
- 2026-09-25 reviewed (aw set): plan-review complete: PR-801..PR-806 all fixed. Reproduced every author claim independently (0-vs-3 slot findings on the three named walkthroughs; doctor's executed/ demotion verbatim on a fixture). HIGH PR-801: E-04 before E-03 is a silent mirror regression (doctor would drop to zero slot findings) - now an explicit precondition with ordering evidence in V-04. Added E-05 proving the 3 new errors cannot red CI. Corrected the docstring's stale +47/39-to-86 deterrent. 7 items, 7:7 bijection; OQ-01 resolved from evidence. Findings and 3 decisions in .aw/records/reviews/20260924-collpop-01-t0jyb2-...review.md

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801..PR-806, all FIXED. INDEPENDENTLY REPRODUCED EVERY CLAIM: `check_collisions(root)` returns `Counter()` and `include_retired=True` returns `Counter({'check.id6-identity-slot': 3})` on exactly the three named walkthroughs; the fixture probe reproduced doctor's `executed/` demotion verbatim (check reports the `ccc333` `check.id6-collision` in `all_drift`, doctor files the identical `(path, rule)` under `executed_warnings` and reports `all_drift` empty); and simulating E-03 produced exactly 3 findings and no more. Added E-03's ordering hazard as an explicit item precondition (measured: E-04 landing BEFORE E-03 would take doctor from 3 slot findings to ZERO, a regression the dependency chain prevents but the plan never named); added E-05 to prove the 3 new errors cannot red CI (measured: the fail-closed CI steps are `aw check plans`/`aw check releases`, whose per-type runs emit only the `info`-severity `check.collisions-not-checked` marker, so the new `error`s reach only `aw check all`/`aw doctor`); recorded that the docstring's "+47-finding regression" warning is itself STALE (it described the pre-D153 cross-type emission, and the setid pass measures zero even at the wide corpus today); and noted D140's own 2026-09-20 note calls the walkthrough slot shape a "legitimate convention", contradicting the README, which is the real reason F-4's docstring text exists. Resolved OQ-01 from evidence with a carrier, clearing an error-severity `check.ipd-uncarried-obligation`.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog lmjc8h; re-measured check_collisions at both include_retired values on the live tree (0 vs 3, all check.id6-identity-slot) and on a fixture tree, which also exposed doctor's executed/ demotion as a second divergence axis.

## Goal

`aw check all` and `aw doctor` report the SAME set of `check.id6-collision`, `check.id6-identity-slot` and `check.setid-collision` findings for the same tree, at the default scope and at the widened scope, with each rule's population chosen deliberately and written down where the next reader will look.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the divergence

- [ ] E-01 Re-measure the baseline before touching code. On the live tree run `check_engine.check_collisions(root)` and `check_engine.check_collisions(root, include_retired=True)` and print the rule counter and the (location, rule) difference; then build the fixture tree from E-02 by hand in a scratch dir and print the collision findings from `check_engine.check_types(root, ["all"])` versus `doctor.probe_artifacts(root).all_drift` and `.executed_warnings`.
  - Depends on: none
  - Expected outcome: live tree shows 0 vs 3 (`check.id6-identity-slot` on `zpbx7o`, `y5od1h`, `4fodkt`); the fixture shows doctor reporting a slot finding check does not, and check reporting an executed/ `check.id6-collision` as error that doctor files under `executed_warnings`. If either no longer holds, stop and report: the defect has moved.
  - Execution state: pending

- [ ] E-02 Add `tests/test_collision_population_parity.py`. One fixture tree (via `tempfile`, conformant plan bodies built the way `tests/test_check_engine._plan_text` builds them; import it from `tests.test_check_engine` rather than copying) holding: a live pending plan; an executed plan `aaa111`; a walkthrough whose identity slot reuses `aaa111` while declaring no `- Id:`; two executed plans that both declare `- Id: ccc333`; two executed plans sharing setid `other` with different descriptives. Assert, on repo-relative `(path, rule)` sets restricted to the three collision rules: (1) default `aw check` (`check_types(root, ["all"])`) equals default doctor (`probe_artifacts(root).all_drift`); (2) widened `aw check` (`include_retired=True`) equals widened doctor (`include_executed=True`); (3) the identity findings (the slot finding and the `ccc333` id6-collision) are present in BOTH default sets, and the retired setid conflict is absent from both default sets and present in both widened sets; (4) no identity finding appears in `executed_warnings`. Each assertion message names which surface diverged and the differing members.
  - Depends on: E-01
  - Expected outcome: the new file exists and FAILS at HEAD on assertions (1) and (4).
  - Execution state: pending

### Task group 2: settle each rule's population

- [ ] E-03 In `check_engine.check_collisions`, feed `_check_identity_slots` the terminal-inclusive record list (every enumerated file), keeping `caller_visible` gating ONLY the setid pass. LAND THIS BEFORE E-04, and treat the order as a correctness precondition rather than mere sequencing: measured at review, if doctor's call were changed to `include_retired=include_executed` (E-04) while the slot pass still honored the flag, `check_collisions(root, include_retired=False)` returns `Counter()`, so doctor would report ZERO slot findings where it reports 3 today. That is a REGRESSION on the exact rule this plan exists to align, and it is silent. If you are executing items out of order, stop.
  Rewrite the docstring paragraph "THE WIDENING IS DELIBERATELY NARROW" so it states the new split (both identity rules terminal-inclusive; setid pass on the caller's corpus). Three things in that paragraph must change, not one. (a) REMOVE the claim that the `zpbx7o`/`y5od1h` slot findings are "FALSE POSITIVES ... the documented walkthrough convention": `.aw/records/walkthroughs/README.md` says a walkthrough "MUST NOT reuse the id6 of the plan it documents", and backlog `mw0s1y` (open, `Blocks-Release: next`) measures all three as real violations, so they are true positives. (b) The paragraph's "+47-finding regression" warning and its `check.setid-collision` 39 -> 86 measurement are BOTH STALE and must be corrected rather than carried forward: they described the PRE-D153 cross-type emission, since removed, and measured at review the setid pass returns ZERO even at the wide corpus (`include_retired=True` yields `Counter({'check.id6-identity-slot': 3})` and nothing else). Leaving a stale scare-number in a docstring that warns a future reader off the exact change this plan makes is how the next person re-opens a settled question. (c) Note that D140's own 2026-09-20 "Applied" note calls the walkthrough-slot shape a "legitimate ... convention" while the walkthroughs README forbids it; cite the README and `mw0s1y` as controlling and say plainly that the D140 note's parenthetical is the source of the false-positive claim being removed, so the contradiction is recorded once instead of rediscovered.
  - Depends on: E-02
  - Expected outcome: `check_collisions(root)` on the live tree returns the same 3 `check.id6-identity-slot` findings as `include_retired=True` (verified at review: feeding the slot pass the terminal-inclusive list yields exactly those 3 and nothing more); the setid pass is unchanged and still zero.
  - Execution state: pending

- [ ] E-04 In `doctor.probe_artifacts`, replace the hardcoded `include_retired=True` in the `check_engine.check_collisions(` call with `include_retired=include_executed`, and exempt `check.id6-collision` and `check.id6-identity-slot` from the `executed/` demotion in the collision loop (the per-type loop above it is untouched). Replace the comment block beginning "`include_retired=True` IS DELIBERATE AND ASYMMETRIC WITH `aw check`" with one stating the settled contract: identity rules are terminal-inclusive and never demoted on either surface; the setid rule follows `aw check`'s default and widens under `-a`/`--include-executed` exactly as `aw check --all` does; the parity test named by path pins it. State in that comment that E-03 is a PRECONDITION and why (without it this very change zeroes doctor's slot findings), so a future partial revert cannot silently reintroduce the divergence in the opposite direction.
  - Depends on: E-03
  - Expected outcome: the parity test passes; doctor's per-type findings and their `executed/` demotion are unchanged (verified at review that `tests/test_doctor.test_executed_dir_warns_by_default` keys on `check.name-nonconformant`, a per-type rule this item does not touch, so it must keep passing unmodified).
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Prove the newly-reported errors cannot red `main`, and record the reasoning where a reader will find it. E-03 adds 3 `error`-severity findings to `aw check all`, and this plan deliberately does NOT fix the underlying data (that is `mw0s1y`), so the blast radius must be established rather than assumed. Measured at review and to be RE-DERIVED at execution time because the tree is live: the fail-closed CI steps in `.github/workflows/tests.yml` are `aw check plans` and `aw check releases` (plus advisory `aw check backlog` and `aw check release-gates`), and a per-TYPE run does not execute the collision scan at all - it emits only `check.collisions-not-checked`, whose `RuleSpec` severity is `info`. `.pre-commit-config.yaml` declares no `aw check all` hook. So the 3 new errors reach `aw check all` and `aw doctor` only. Paste the re-derived evidence; if a fail-closed CI step has since been widened to `check all` or `check walkthroughs`, STOP and report, because then this plan reds `main` until `mw0s1y` lands and the two must be sequenced.
  - Depends on: E-04
  - Expected outcome: the fail-closed CI steps are shown not to run the collision scan, and no local hook does either; the 3 new errors are confined to `aw check all` and `aw doctor`.
  - Execution state: pending

- [ ] E-06 Run the directly affected modules: `python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_doctor.py tests/test_artifact_adopt.py`. Baseline measured at review: the three existing modules report `86 passed` together, so a drop is a real regression and not a pre-existing failure. Two rows to watch, both checked at review and expected to SURVIVE unchanged: `RetiredAndIgnoredScopeTests`'s "the full sweep, retired excluded" row asserts ZERO findings and its fixture trips no widened slot finding (verified by running the terminal-inclusive slot pass against that class's own tree); and `tests/test_doctor.test_executed_dir_warns_by_default` keys on a per-type rule. If either flips, that is new information about the change and not a fixture to adjust.
  - Depends on: E-05
  - Expected outcome: all pass, at or above the measured 86-passed baseline for the three pre-existing modules; if a `CollisionTests` or `RetiredAndIgnoredScopeTests` row changes, the fixture is fixed only if the new finding is a true identity violation, never by loosening the rule.
  - Execution state: pending

- [ ] E-07 Run the bare suite `python3 -m pytest`.
  - Depends on: E-06
  - Expected outcome: summary line shows zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Identity is terminal-inclusive by precedent: `check_collisions`'s id6 pass already enumerates retired files with the reason "A terminal id6 is permanently cited, so a collision with one is real" (IPD `sk7ggr` E-05).
- Spec `2lcqno` Section 6 does NOT pick a winner; it requires "only that the two surfaces AGREE and that the choice be stated", and names doctor's executed/ demotion as a second axis that reconciling `include_retired` alone cannot fix.
- `aw doctor -a` sets `include_executed`; `aw check --all` sets `include_retired` (`cli` `include_retired = bool(getattr(args, "all", False))`). Mapping one onto the other is what makes "widened" mean the same on both.
- `tests/test_check_engine.py` builds fixtures with `_tree` and conformant `_plan_text` bodies; `tests/__init__.py` exists, so `from tests.test_check_engine import _plan_text` is the established cross-module import shape.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `check_engine.check_collisions` (`caller_visible`) | The identity-slot pass honors the caller's liveness filter while its id6 sibling does not, so `aw check all` reports 0 slot findings where doctor reports 3. Same defect as backlog `e2j5w4`. | Live probe: `False Counter()` vs `True Counter({'check.id6-identity-slot': 3})` |
| F-2 | HIGH | `doctor.probe_artifacts` collision loop | Findings located under `executed/` are demoted to `executed_warnings`, so an executed-vs-executed id6 collision is an error in `aw check all` and a warning in doctor. | Fixture probe: check `{(...ccc333-one.ipd.md, 'check.id6-collision')}`; doctor `warn {(...ccc333-one.ipd.md, 'check.id6-collision')}` |
| F-3 | INFO | backlog `lmjc8h` body | The 38/86 setid-collision split it quotes is obsolete; that rule is zero on both surfaces since `4f1ca199`. The disagreement it names is still real, but on other rules. | Live probe; `doctor.probe_artifacts` comment "both report ZERO on the real tree" |
| F-4 | MED | `check_collisions` docstring | Calls the `zpbx7o`/`y5od1h` slot findings "FALSE POSITIVES", contradicting the walkthroughs README and D140. | README quote in E-03 |
| F-5 | HIGH | E-03/E-04 ordering | ADDED AT REVIEW. E-04 landing BEFORE E-03 is a silent REGRESSION, not merely out of order: with doctor passing `include_retired=include_executed` while the slot pass still honors the flag, doctor reports ZERO slot findings where it reports 3 today. The plan's `Depends on` chain prevents it; nothing in the plan SAID so, and a partial revert would reintroduce the divergence in the opposite direction. | Measured at review: `check_collisions(root, include_retired=False)` returns `Counter()`; `include_retired=True` returns `Counter({'check.id6-identity-slot': 3})` |
| F-6 | MED | `check_collisions` docstring, same paragraph as F-4 | ADDED AT REVIEW. The paragraph's deterrent "+47-finding regression" and its `check.setid-collision` 39 -> 86 figure are STALE: both described the pre-D153 cross-type emission, since removed. Measured at review the setid pass yields ZERO even at the wide corpus, so the number that warns a reader off this change no longer describes anything. Correcting it is part of E-03, not a separate cleanup. | `check_collisions(root, include_retired=True)` -> `Counter({'check.id6-identity-slot': 3})`, no setid findings at any scope |
| F-7 | INFO | DECISIONS.md D140 "Applied (2026-09-20, IPD `sk7ggr`)" | ADDED AT REVIEW. That note says the identity-slot pass deliberately excludes retired files "to avoid mass-flagging the legitimate shared-setid and walkthrough-slot conventions" - calling the walkthrough slot shape LEGITIMATE, which the walkthroughs README forbids and `mw0s1y` treats as a live `Blocks-Release: next` bug. This is the ORIGIN of the docstring's false-positive claim, so E-03 records the contradiction once with the README and `mw0s1y` as controlling. | D140 note quote; `.aw/records/walkthroughs/README.md` "MUST NOT reuse the id6 of the plan it documents"; `mw0s1y` status `open` |
| F-8 | INFO | CI and hook surfaces | ADDED AT REVIEW. The 3 new `error` findings cannot red `main`: the fail-closed CI steps are `aw check plans` and `aw check releases`, and a per-TYPE run does not execute the collision scan (it emits only `check.collisions-not-checked`, `RuleSpec` severity `info`); `.pre-commit-config.yaml` declares no `aw check all` hook. E-05 re-derives this at execution time. | `.github/workflows/tests.yml` fail-closed steps; `ce.RULE_REGISTRY` severities (`check.id6-identity-slot` = `error`, `check.collisions-not-checked` = `info`); per-type runs measured to emit only the marker |

## Proposed changes (ordered, validatable)

1. E-01 re-measures both axes on the live tree and a fixture.
2. E-02 adds the parity test and shows it failing.
3. E-03 makes the identity-slot pass terminal-inclusive and corrects the stale docstring (F-4, F-6, F-7). MUST precede E-04 (F-5).
4. E-04 aligns doctor's flag and stops demoting identity findings.
5. E-05 proves the new errors cannot red CI (F-8).
6. E-06 and E-07 run the affected modules, then the bare suite.

## Deferred / out of scope (with reason)

- Renaming the three walkthroughs whose identity slot reuses their plan's id6. After E-03 `aw check all` reports them as errors; fixing the data is a separate, record-editing change.
  - Carrier: mw0s1y
- Closing backlog `e2j5w4`, whose defect E-03 fixes. Closing it is a backlog state change this plan's author may not make; the executor or maintainer closes it citing this plan.
  - Carrier: e2j5w4
- Whether a backlog item sharing its plan's setid should count as a setid collision under the widened scope.
  - Carrier: sjsoqq
- Aligning the `untracked/` axis between the surfaces. Both already exclude it by default, and nothing measured shows a divergence.
  - Carrier-Declined: no measured divergence; not an outstanding obligation.

## Scope check

- Over-scope: none. Doctor's per-type loop and its executed/ demotion stay as they are; only the collision loop changes.
- Under-scope: `aw check all` exit status on the live tree does not change (it already exits 1), but it gains 3 errors. That is the intended effect of E-03, not a regression. RE-DERIVE THE COUNT AT EXECUTION TIME rather than trusting a number here: the plan originally read "24 errors" and review measured 23 on the same command a day later, which is exactly the live-artifact drift that makes an authored count unusable as a bar. The property that matters and does not drift: the exit status is already 1 before this change, so the 3 added errors change no gate's verdict. E-05 establishes the CI half of that claim (F-8).
- Not a gap, recorded so it is not mistaken for one: this plan deliberately leaves the three offending walkthroughs unfixed (`mw0s1y`, open, `Blocks-Release: next`), so after execution `aw check all` reports 3 errors that no in-scope change can clear. That is the correct division - detection here, data repair there - and it is the reason E-05 exists: an honest detection fix must prove it does not red the build for the window before the data fix lands.

## Required tests / validation

The new `tests/test_collision_population_parity.py` must be shown failing before E-03/E-04 and passing after. The affected modules and then the bare suite are run with pasted summary lines.

## Spec / documentation sync

N/A for specs: spec `2lcqno` Section 6 explicitly leaves the choice to the implementer and asks only that it be stated. It is stated in the `check_collisions` docstring and the `doctor.probe_artifacts` comment (E-03, E-04), both inside Scope-Paths. No user-facing docs describe the populations.

## Open questions

### OQ-01: Should doctor keep a softer, historical view of identity collisions on retired records?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO, resolved at review from the repository rather than left to the maintainer. Three pieces of in-tree evidence settle it. (1) IPD `sk7ggr` E-05's own reasoning, still in the code: the id6 pass enumerates retired files because "A terminal id6 is permanently cited, so a collision with one is real" - the identity-slot rule asks the same question about the same permanently-cited handle, so a different answer for it is not a policy choice but an inconsistency. (2) `check.id6-identity-slot` and `check.id6-collision` are both `error` severity in `RULE_REGISTRY` (verified at review), so demoting them in one surface contradicts the declared severity rather than expressing a softer view. (3) The user-visible harm is concrete and measured on the live tree by `mw0s1y`: `aw find y5od1h` returns two artifacts for one identity, which breaks the cross-tree handle every typed link depends on, and that is equally broken whichever surface is asked. A softer doctor would mean the audit surface reports a broken handle as a warning while the gate calls it an error, which is the divergence this plan exists to remove. If the maintainer nonetheless wants both surfaces softer, that is a rule-severity change to `RULE_REGISTRY` affecting `aw check` too, not a doctor-local demotion, and the parity test's assertion (4) inverts.
- Carrier-Declined: Resolved from in-tree evidence (the shipped `sk7ggr` reasoning, the rule severities, and `mw0s1y`'s measurement), so nothing is outstanding; a future decision to soften both surfaces would be a new severity decision, not a deferred obligation from this plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted probe output showing the live-tree rule counters for both `include_retired` values (expected `Counter()` vs `Counter({'check.id6-identity-slot': 3})`) and the fixture's check-vs-doctor-vs-executed_warnings sets.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_collision_population_parity.py` run BEFORE E-03/E-04, pasted, showing failures on the default-parity and no-demotion assertions, with the message naming the slot finding and the `ccc333` collision.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted live-tree probe showing `check_collisions(root)` and `check_collisions(root, include_retired=True)` now both return the 3 `check.id6-identity-slot` findings AND that neither returns any additional rule (the counter, not just the slot count, so a widened setid pass cannot hide inside a passing item). Paste `git diff -- agent_workflows/check_engine.py` showing the docstring no longer says "FALSE POSITIVES" AND no longer carries the stale "+47-finding regression" / "39 -> 86" figures (F-6), AND that it records the D140-versus-README contradiction with the README and `mw0s1y` as controlling (F-7). A diff that removes only the "FALSE POSITIVES" phrase does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_collision_population_parity.py` pasted and passing; `grep -n "include_retired" agent_workflows/doctor.py` showing no hardcoded `include_retired=True` on the `check_collisions` call. ALSO paste the ORDERING evidence for F-5: with E-04 applied, show `doctor.probe_artifacts(root).all_drift` still containing the 3 slot findings, which is the assertion that proves E-03 landed first and doctor did not silently drop to zero. Paste the new comment block's sentence naming E-03 as a precondition.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the RE-DERIVED CI evidence, not the plan's prose: the fail-closed step names from `.github/workflows/tests.yml`, a run of one of them (for example `python3 -m agent_workflows check plans --agent`) showing the collision rules absent and only `check.collisions-not-checked` present, that marker's `info` severity read out of `RULE_REGISTRY`, and a grep of `.pre-commit-config.yaml` showing no `aw check all` hook. State explicitly whether any fail-closed step now runs `check all` or `check walkthroughs`; if one does, this item's outcome is STOP-and-report, not a pass.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted summary line of `python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_doctor.py tests/test_artifact_adopt.py` with 0 failed, and the pass count stated against the 86-passed baseline review measured for the three pre-existing modules. If `RetiredAndIgnoredScopeTests`' zero-findings row or `tests/test_doctor.test_executed_dir_warns_by_default` changed, say so explicitly and justify it as a true identity violation rather than adjusting the fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted final summary line of the bare `python3 -m pytest`, showing 0 failed. Bare per AGENTS.md: no `-n0`, no extra `-q`, no `-p no:randomly`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Seven items, one concern: making two surfaces report one collision population. The count grew from six at review because the ordering hazard between E-03 and E-04 needed stating as a precondition (F-5, a silent regression if inverted) and because the blast radius of newly-reported errors needed its own proof item (E-05, F-8) rather than a sentence in the scope check. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A behavior change to two reporting surfaces that makes `aw check all` and `aw doctor` newly report 3 `error`-severity findings on this repository's own records, WITHOUT fixing the underlying data (that is backlog `mw0s1y`, open, `Blocks-Release: next`). Three things to weigh. FIRST, the findings are real: the walkthroughs README says a walkthrough "MUST NOT reuse the id6 of the plan it documents", and the user-visible harm is that `aw find y5od1h` returns two artifacts for one identity. SECOND, this plan REMOVES a docstring claim that those findings are false positives, and that claim traces to D140's own 2026-09-20 note calling the shape a "legitimate convention" - so approving this also endorses the README over that parenthetical (recorded as F-7, and as OQ-01's resolution). THIRD, review measured that the new errors cannot red `main`, because the fail-closed CI steps do not run the collision scan; E-05 re-derives that at execution time and STOPS if it has changed.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `agent_workflows/check_engine.py`, the `records` construction and the `_check_identity_slots` call inside `check_collisions`, plus that function's docstring paragraph; in `agent_workflows/doctor.py`, the `include_retired=` argument on the `check_collisions` call, the demotion condition in the COLLISION loop only, and the comment block above it; `tests/test_collision_population_parity.py` is new. EXPLICITLY NOT IN SCOPE: `_check_identity_slots`' own rule logic; the setid pass; `RULE_REGISTRY` severities; doctor's PER-TYPE loop and its `executed/` demotion; `_iter_type_files`; `is_retired`; the three offending walkthrough files (`mw0s1y`); backlog state changes for `e2j5w4` or `lmjc8h`; `.github/workflows/tests.yml`; and DECISIONS.md D140 (the contradiction is RECORDED in the docstring, not resolved by editing a decision record). An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-02 (the parity test must be shown FAILING at HEAD before the fix, which requires running it against unfixed code) and on V-04's ordering evidence (doctor still reporting 3 slot findings is the only observable distinguishing a correct sequence from the F-5 regression, and both a correct and an inverted implementation make the parity test's other assertions pass).

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: E-01's baseline no longer shows 0-vs-3 with those three id6s, or the fixture no longer shows doctor demoting an executed id6 collision (the defect has moved and the plan needs re-deriving, as E-01 already says); a fail-closed CI step has been widened to run `check all` or `check walkthroughs`, in which case this plan reds `main` until `mw0s1y` lands and the two must be sequenced (E-05); or `mw0s1y` has already been executed, in which case the 3 findings are gone and E-01's, E-03's and V-03's expected counts must be re-derived rather than asserted.

This plan is `to-review` and needs explicit human approval before execution. The executor commits only the Scope-Paths via `aw commit t0jyb2 -- <paths>`, never `git add -A`, never pushes, and pastes actual runner output for every V item. This plan inherits `- Blocks-Release: next` from backlog `lmjc8h` and does NOT discharge it alone: `mw0s1y` and `e2j5w4` carry their own gates, and the Deferred rows name them as carriers, so do not close either item as part of this execution. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-07 carry pasted evidence.
