# IPD: Make aw check and aw doctor report one collision population

- Date: 2026-09-24
- Kind: child
- Concern: ONE PREDICATE, TWO POPULATIONS. `check_engine.check_collisions` is reached from `aw check all` via `check_engine.check_types` (`include_retired=include_retired`, which `cli` derives from `--all` and which defaults False) and from `aw doctor` via `doctor.probe_artifacts` (hardcoded `include_retired=True`). The backlog's 38-vs-86 `check.setid-collision` split is STALE: after D153 / spec `2lcqno` N1 and commit `4f1ca199` that rule reports zero on both. RE-MEASURED at HEAD `cfc7f5c1`, the live divergence is now ENTIRELY the identity-slot pass: `check_collisions(root)` returns 0 findings, `check_collisions(root, include_retired=True)` returns 3 `check.id6-identity-slot` (walkthroughs `zpbx7o`, `y5od1h`, `4fodkt`), and `doctor.probe_artifacts` surfaces those same 3. A fixture probe also exposed the SECOND axis spec `2lcqno` Section 6 names: doctor demotes any finding located under `executed/` into `executed_warnings`, so a `check.id6-collision` between two executed plans is an ERROR in `aw check all` and only a WARNING in `aw doctor`. The surfaces therefore disagree in BOTH directions today.
- Scope: Make the two surfaces report the same collision set, with the population chosen per rule and stated. IN: (a) the identity-slot pass in `check_engine.check_collisions` consumes the terminal-inclusive corpus, exactly as its id6 sibling already does, so both identity rules ignore the caller's liveness filter; (b) `doctor.probe_artifacts` passes `include_retired=include_executed` to `check_collisions` instead of a hardcoded `True`, so the setid pass (the only rule still honoring the flag) sees the same corpus as `aw check` at the default and under `-a`/`--all`; (c) doctor stops demoting the two IDENTITY rules into `executed_warnings`, because a collision with a terminal id6 is real (IPD `sk7ggr` F-3) and must not be softer in one surface; (d) a parity test over a fixture tree containing retired plans. OUT: renaming the three live walkthroughs (backlog `mw0s1y`); any change to what counts as retired; the `untracked/` axis; the setid-collision policy for backlog-shares-plan setids (`sjsoqq`).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/doctor.py, tests/test_collision_population_parity.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: collpop
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: t0jyb2
- From-Backlog: lmjc8h
- Blocks-Release: next

## Workflow history

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

- [ ] E-03 In `check_engine.check_collisions`, feed `_check_identity_slots` the terminal-inclusive record list (every enumerated file), keeping `caller_visible` gating ONLY the setid pass. Rewrite the docstring paragraph "THE WIDENING IS DELIBERATELY NARROW" so it states the new split (both identity rules terminal-inclusive; setid pass on the caller's corpus) and REMOVE its claim that the `zpbx7o`/`y5od1h` slot findings are "FALSE POSITIVES ... the documented walkthrough convention": `.aw/records/walkthroughs/README.md` says a walkthrough "MUST NOT reuse the id6 of the plan it documents" and D140 agrees, so they are true positives owned by backlog `mw0s1y`.
  - Depends on: E-02
  - Expected outcome: `check_collisions(root)` on the live tree returns the same 3 `check.id6-identity-slot` findings as `include_retired=True`; the setid pass is unchanged.
  - Execution state: pending

- [ ] E-04 In `doctor.probe_artifacts`, replace the hardcoded `include_retired=True` in the `check_engine.check_collisions(` call with `include_retired=include_executed`, and exempt `check.id6-collision` and `check.id6-identity-slot` from the `executed/` demotion in the collision loop (the per-type loop above it is untouched). Replace the comment block beginning "`include_retired=True` IS DELIBERATE AND ASYMMETRIC WITH `aw check`" with one stating the settled contract: identity rules are terminal-inclusive and never demoted on either surface; the setid rule follows `aw check`'s default and widens under `-a`/`--include-executed` exactly as `aw check --all` does; the parity test named by path pins it.
  - Depends on: E-03
  - Expected outcome: the parity test passes; doctor's per-type findings and their executed/ demotion are unchanged.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-05 Run the directly affected modules: `python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_doctor.py tests/test_artifact_adopt.py`.
  - Depends on: E-04
  - Expected outcome: all pass; if a `CollisionTests` or `RetiredAndIgnoredScopeTests` row changes, the fixture is fixed only if the new finding is a true identity violation, never by loosening the rule.
  - Execution state: pending

- [ ] E-06 Run the bare suite `python3 -m pytest`.
  - Depends on: E-05
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

## Proposed changes (ordered, validatable)

1. E-01 re-measures both axes on the live tree and a fixture.
2. E-02 adds the parity test and shows it failing.
3. E-03 makes the identity-slot pass terminal-inclusive.
4. E-04 aligns doctor's flag and stops demoting identity findings.
5. E-05 and E-06 run the affected modules, then the bare suite.

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
- Under-scope: `aw check all` exit status on the live tree does not change (it already exits 1 with 24 errors), but it gains 3 errors. That is the intended effect of E-03, not a regression.

## Required tests / validation

The new `tests/test_collision_population_parity.py` must be shown failing before E-03/E-04 and passing after. The affected modules and then the bare suite are run with pasted summary lines.

## Spec / documentation sync

N/A for specs: spec `2lcqno` Section 6 explicitly leaves the choice to the implementer and asks only that it be stated. It is stated in the `check_collisions` docstring and the `doctor.probe_artifacts` comment (E-03, E-04), both inside Scope-Paths. No user-facing docs describe the populations.

## Open questions

### OQ-01: Should doctor keep a softer, historical view of identity collisions on retired records?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default is NO, per IPD `sk7ggr` F-3 and D140: an executed plan's id6 is permanently cited, so a collision with one is real, and showing it as a warning in one surface and an error in the other is the defect being fixed. If the maintainer wants doctor softer, both surfaces must soften together and the parity test's assertion (4) inverts.

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
  - Required evidence: pasted live-tree probe showing `check_collisions(root)` and `check_collisions(root, include_retired=True)` now both return the 3 `check.id6-identity-slot` findings; `git diff -- agent_workflows/check_engine.py` showing the docstring no longer says "FALSE POSITIVES".
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_collision_population_parity.py` pasted and passing; `grep -n "include_retired" agent_workflows/doctor.py` showing no hardcoded `include_retired=True` on the `check_collisions` call.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted summary line of `python3 -m pytest tests/test_collision_population_parity.py tests/test_check_engine.py tests/test_doctor.py tests/test_artifact_adopt.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the pasted final summary line of the bare `python3 -m pytest`, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution. The executor commits only the Scope-Paths via `aw commit t0jyb2 -- <paths>`, never `git add -A`, never pushes, pastes actual runner output for every V item, and moves the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms.
