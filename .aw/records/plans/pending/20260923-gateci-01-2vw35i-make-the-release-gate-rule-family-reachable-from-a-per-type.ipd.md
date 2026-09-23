# IPD: Make the release-gate rule family reachable from a per-type check and enforced by a named CI step instead of only by a full sweep nothing runs

- Date: 2026-09-23
- Kind: child
- Concern: THE RELEASE-GATE RULE FAMILY IS UNENFORCED IN CI, AND I CONFIRMED BOTH HALVES OF THAT AT HEAD `22cf67d9`. Backlog `wu8qjy` (`high`, `Blocks-Release: next`) says no workflow step runs `aw check all` and the one step that could report it is advisory. MEASURED: `grep -c "agent_workflows check all"` across every file in `.github/workflows/` returns ZERO (`tests.yml`, `local-leaks.yml`, `secret-scan.yml` all 0). So the sweep that hosts the family never runs in CI at all.
  THE RULES ARE ALSO UNREACHABLE FROM THE PER-TYPE CHECK, WHICH IS THE OTHER HALF. `aw check backlog --agent` reports 4 findings on this tree, none of them from the gate family, while `aw check all --agent` reports 49 INCLUDING `check.live-bug-ungated` against a real item (`.aw/records/backlog/open/20260918-7l1ggb-...`). One live, ungated `bug` exists right now and no per-type invocation can see it. That matches `wu8qjy`'s own measurement exactly ("`aw check backlog` CANNOT report any of these rules"), and it means the rule family is wired only into the once-per-full-sweep seam inside `check_types`.
  SO THE GATE IS DOUBLY DEAD: unreachable from the check a developer or hook would plausibly run, and absent from CI even in the form that can report it. `wu8qjy` was filed because the parent Set's completion criterion ("`aw check` reports a live bug with no gate, and CI fails on it") is only half met; the first clause is true under `check all` and the second is false everywhere.
  AND THE CI STEP THAT DOES RUN `check backlog` IS DELIBERATELY ADVISORY, FOR A REASON THAT MUST BE RESPECTED RATHER THAN OVERRIDDEN. `tests.yml` runs it with `|| true` and an explanatory comment: backlog is "ADVISORY (report-only), NOT fail-closed: the tree carries pre-existing backlog name/summary debt ... that a fail-closed gate would red `main` on. It joins the fail-closed set above once that baseline is cleaned by a separate migration (DECISION 18-r2ks4k-D1)". That debt is REAL and still present: `check backlog` reports 4 findings on this tree today (`check.name-nonconformant` x3 plus `check.collisions-not-checked`). So simply deleting the `|| true` would red `main` on unrelated naming debt, which is why this plan must separate the GATE rules from the CONFORMANCE rules rather than flipping one switch.
  THE SHAPE OF THE FIX IS THEREFORE NOT "MAKE `check backlog` FAIL CLOSED". It is to make the release-gate family reachable per-type AND enforced by its own named step, so a live ungated bug blocks a merge while the pre-existing naming debt stays advisory until its own migration lands. That distinction is the whole design and is what OQ-01 asks the reviewer to confirm.
- Scope: Make a live ungated release-blocking bug fail CI, without red-lining `main` on unrelated debt. IN: (a) make the release-gate rule family reachable from a per-type check (today it lives only in the full-sweep seam), per OQ-01; (b) add a NAMED, fail-closed CI step that runs exactly those rules, leaving the existing advisory `check backlog` step as it is; (c) a test proving the family fires on a fixture carrying a live ungated bug and does not fire on a clean one. OUT: flipping the existing `check backlog` step to fail-closed, which `DECISION 18-r2ks4k-D1` defers to a separate baseline-cleaning migration and which the measured 4 findings would immediately red; cleaning that naming debt; and adding `aw check all` wholesale to CI, which would enforce 49 findings' worth of unrelated rules in one step.
- Scope-Paths: agent_workflows/check_engine.py, .github/workflows/tests.yml, tests/test_check_engine_release_gate.py
- Item-Dependencies: none
- Status: to-review
- Set: gateci
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 2vw35i
- From-Backlog: wu8qjy
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `wu8qjy`, whose `- Blocks-Release: next` is INHERITED. Confirmed both halves at HEAD rather than trusting the filing: ZERO occurrences of `agent_workflows check all` in any workflow file, and `check backlog` reporting 4 findings none of which are gate rules while `check all` reports 49 including a real `check.live-bug-ungated`.
  THE FINDING THAT SHAPES THE PLAN is that the obvious fix is wrong. Deleting the `|| true` from the existing advisory step would red `main` immediately, because the pre-existing naming debt `DECISION 18-r2ks4k-D1` defers is still present and measurable (4 findings). So the plan separates the GATE rules from the CONFORMANCE rules and adds a narrow named step, rather than flipping a switch the maintainer deliberately left off.
  I ALSO RECORD THE LIVE VIOLATION the gate would catch today: `7l1ggb` is a live `bug` with no `Blocks-Release`, visible to `check all` and invisible to every per-type invocation. That is the concrete thing this plan makes CI see.

## Goal

Make a live release-blocking bug with no gate fail a named CI step, while leaving the deliberately-advisory backlog conformance step untouched.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm the double gap and the constraint

- [ ] E-01 RE-MEASURE ALL THREE FACTS, because the plan's shape depends on the third one as much as the first two.
  CONFIRM CI NEVER RUNS THE SWEEP: grep every file under `.github/workflows/` for `check all` and paste the counts. At authoring: zero in all three workflow files.
  CONFIRM THE PER-TYPE UNREACHABILITY: run `aw check backlog --agent` and `aw check all --agent` on this tree and paste both finding counts and rule sets. At authoring: 4 versus 49, with `check.live-bug-ungated` present only in the second.
  CONFIRM THE ADVISORY STEP'S CONSTRAINT IS STILL LIVE, which is what forbids the one-line fix: show that `check backlog` reports findings TODAY (at authoring: `check.name-nonconformant` x3 and `check.collisions-not-checked`), so removing `|| true` would fail the job on debt unrelated to release gating. If that debt has since been cleaned, SAY SO, because then the simpler fix becomes available and OQ-01's answer changes.
  NAME THE LIVE VIOLATION the new gate must catch, so there is a concrete regression target rather than a synthetic one. At authoring: `7l1ggb`, a live `bug` with no `Blocks-Release`.
  - Depends on: none
  - Expected outcome: the three measurements pasted, the live violating item named, and an explicit statement of whether the naming debt still blocks the simpler fix.
  - Execution state: pending

### Task group 2: make the rules reachable

- [ ] E-02 MAKE THE RELEASE-GATE FAMILY REACHABLE OUTSIDE THE FULL SWEEP, per OQ-01. Today the family (`check.live-bug-ungated`, `check.from-backlog-gate-mismatch`, `check.blocking-item-closed-without-gate`, `check.blocks-release-dangling`, `check.from-backlog-dangling`) is wired only into the once-per-sweep seam in `check_types`, so no per-type invocation can report it.
  DO NOT FORK THE PREDICATES. `AGENTS.md` records that ONE shared predicate (`check_engine.evaluate_blocking_close`) backs the setter, the `aw check` rules and the opt-in hook precisely "so they cannot diverge". Whatever makes the family reachable must call the same rules, not a copy.
  THE RULES ARE CROSS-TREE BY NATURE, WHICH IS WHY THEY LIVE IN THE SWEEP. A gate rule joins a backlog item to a release record and sometimes to a plan, so "check only the backlog tree" cannot answer it in general. Decide deliberately whether the reachable form is a per-type invocation that still reads the other trees, or a distinct named target, and record which.
  DO NOT CHANGE WHAT THE RULES DECIDE. This plan changes REACHABILITY and ENFORCEMENT only. If you find a rule itself is wrong, report it rather than fixing it here; `4le6yz` and `0cqf33` already record specific gate-rule defects and are owned elsewhere.
  - Depends on: E-01
  - Expected outcome: the release-gate family is reportable from an invocation narrower than the full sweep, calling the SAME shared predicates; the rules' verdicts are unchanged; the chosen form (per-type versus distinct target) is recorded with its reason.
  - Execution state: pending

### Task group 3: enforce it in CI

- [ ] E-03 ADD A NAMED FAIL-CLOSED CI STEP FOR THE GATE FAMILY, AND LEAVE THE ADVISORY STEP ALONE.
  THE NEW STEP MUST BE NARROW. It enforces the release-gate family only. A step that enforces everything `check all` reports would fail on 49 findings' worth of unrelated rules and would be reverted within a day, which is the same "gate that stays red stops being read" failure `4y7nzh` measured over two days and 143 commits.
  DO NOT TOUCH THE EXISTING ADVISORY `check backlog` STEP. Its `|| true` is a recorded maintainer decision (`DECISION 18-r2ks4k-D1`) with a stated precondition (the naming baseline is cleaned by a separate migration). Removing it is out of scope and E-01 re-proves why.
  FOLLOW THE EXISTING FAIL-CLOSED PRECEDENT in the same job: `check plans` and `check releases` already run fail-closed as named steps beside the advisory one, so the pattern, naming style and placement are established and should be matched rather than invented.
  THE STEP MUST BE PROVEN TO FAIL, not merely added. A CI step nobody has seen fail is an assumption; demonstrate it failing on a fixture carrying a live ungated bug.
  - Depends on: E-02
  - Expected outcome: a named, fail-closed CI step enforcing the release-gate family, matching the existing fail-closed steps' shape; the advisory backlog step unchanged; the step demonstrated failing on a violating fixture and passing on a clean one.
  - Execution state: pending

- [ ] E-04 TEST THE FAMILY'S REACHABILITY AND ITS POLARITY, from fixtures.
  ASSERT BOTH DIRECTIONS: a fixture with a live `bug` carrying no `Blocks-Release` must produce `check.live-bug-ungated` from the new reachable invocation, and a clean fixture must produce nothing. A one-sided test would pass against a rule that fires always.
  DO NOT PIN THE LIVE CORPUS. `7l1ggb` is the live violation today and this plan's own siblings may gate or close it, so an assertion keyed on it would rot; `jb0sc1`, `caf5ed` and `agrlvw` all record that hazard in this repository.
  COVER THE `done`-WITH-GATE CASE TOO if it is cheap, since `check.blocking-item-closed-without-gate` shares the family's seam and `AGENTS.md` documents its three legitimate fixes (handoff, evidence, de-gate); a test that only covers the ungated-bug rule leaves the rest of the family unproven as reachable.
  - Depends on: E-02
  - Expected outcome: tests proving the family is reachable and fires only on genuine violations, using synthetic fixtures with no reference to live records.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE SHARED PREDICATE BACKS THE SETTER, THE CHECK RULES AND THE HOOK (`check_engine.evaluate_blocking_close`), explicitly "so they cannot diverge" (`AGENTS.md`). Any reachability change must call it rather than copy it.
- THE ADVISORY BACKLOG STEP IS A DELIBERATE DECISION with a stated precondition (`DECISION 18-r2ks4k-D1`): it becomes fail-closed only once the naming baseline is cleaned. The debt is still measurable, so the decision still holds.
- CI ALREADY HAS FAIL-CLOSED PER-TYPE STEPS (`check plans`, `check releases`) in the same job as the advisory one, which is the pattern for E-03 to match.
- A GATE THAT STAYS RED STOPS BEING READ: `4y7nzh` measured a correct fail-closed gate red for two days while 143 commits landed past it. That is the argument for a NARROW new step rather than enforcing everything.
- `aw check` EXITS 0 CLEAN / 1 FINDINGS / 2 CANNOT-RUN, so a CI step's fail-closed behavior follows from not swallowing exit 1.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `.github/workflows/` | No workflow runs `aw check all`, so the sweep hosting the release-gate family never executes in CI. | `grep -c "agent_workflows check all"` returns 0 in `tests.yml`, `local-leaks.yml`, `secret-scan.yml` |
| F-2 | BLOCKER | `check_engine.check_types` seam | The gate family is unreachable from a per-type check: `check backlog` reports 4 findings with no gate rules; `check all` reports 49 including `check.live-bug-ungated`. | both invocations' pasted counts and rule sets |
| F-3 | HIGH | live tree | A real violation exists right now and CI cannot see it: `7l1ggb` is a live `bug` with no `Blocks-Release`. | `check all` diagnostic naming that file |
| F-4 | HIGH (constraint) | `tests.yml` advisory step | The one-line fix is WRONG: removing `|| true` would red `main` on pre-existing naming debt that is still present (4 findings), which `DECISION 18-r2ks4k-D1` defers to a separate migration. | the step's `|| true` and comment; `check backlog` reporting `check.name-nonconformant` x3 + `check.collisions-not-checked` |
| F-5 | MED | rule ownership | Specific gate-rule DEFECTS are owned elsewhere (`4le6yz`, `0cqf33` both concern `check.from-backlog-gate-mismatch` spelling comparisons), so this plan must change reachability and enforcement only, not verdicts. | those items' summaries |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the CI absence, the per-type unreachability, and the still-live naming debt that forbids the simpler fix.
2. E-02 makes the release-gate family reachable outside the full sweep, calling the shared predicates unchanged.
3. E-03 adds a narrow named fail-closed CI step and leaves the advisory step untouched.
4. E-04 proves reachability and polarity from synthetic fixtures.

## Deferred / out of scope (with reason)

- FLIPPING `check backlog` TO FAIL-CLOSED. `DECISION 18-r2ks4k-D1` conditions it on a separate baseline-cleaning migration, and F-4 shows the debt is still live, so flipping it now would red `main` on unrelated findings.
- CLEANING THE BACKLOG NAMING DEBT. That is the deferred migration's job; doing it here would bundle an unrelated records sweep into a CI fix.
- ADDING `aw check all` TO CI WHOLESALE. It reports 49 findings on this tree; enforcing all of them in one step is the red-gate failure `4y7nzh` measured.
- FIXING INDIVIDUAL GATE RULES. `4le6yz` and `0cqf33` own specific verdict defects; E-02 explicitly changes no verdict.
- GATING `7l1ggb` ITSELF. It is the live violation this plan makes visible, and deciding its gate is a maintainer judgement about that bug, not a side effect of wiring a check.

## Scope check

- Over-scope: `check_engine.py` is in scope ONLY for reachability of the existing family. Do not alter any rule's verdict, severity, or the shared `evaluate_blocking_close` predicate's logic.
- Under-scope: if E-02's reachable form needs a new CLI target, `agent_workflows/cli.py` is undeclared and must be added deliberately before editing, with the reason recorded.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: the new release-gate check test module.
- E-03's CI step MUST be demonstrated FAILING on a fixture carrying a live ungated bug; a step never seen to fail is an assumption, which is exactly what `wu8qjy` reports about the current state.
- E-04 MUST use synthetic fixtures, never the live corpus (`jb0sc1`, `caf5ed`, `agrlvw`).
- Confirm `aw check plans` and `aw check releases` still behave as before, since E-02 touches the shared engine they run through.

## Spec / documentation sync

- `AGENTS.md`'s release-gate section states the `aw check` rule plus CI is "the portable authority", which is currently only half true; if E-03 lands, that sentence becomes accurate and the section should name the enforcing step.
- If the gate family's reachability is specified in a spec governing `aw check`, declare that `.spec.md` in `- Scope-Paths:` before amending it, per the spec-amendment rule. No spec edit is anticipated otherwise.

## Open questions

### OQ-01: Per-type reachability, or a distinct named check target?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer if it changes a documented CLI surface
- Resolution or deferral rationale: NOT blocking, because E-02 must deliver one and either makes the family enforceable, so the plan terminates correctly either way. PER-TYPE (teach `check backlog` to also report the gate family) matches where a developer would look and needs no new surface, but it muddies the type boundary, since these rules are cross-tree by nature and a backlog-scoped check would have to read releases and plans too; it also collides with F-4, because the natural CI step for it is the advisory one that must stay advisory. A DISTINCT NAMED TARGET (for example a release-gate check) keeps the cross-tree nature honest, gives CI an obviously narrow step to enforce, and leaves the advisory step untouched, at the cost of one more surface to document. Recommend the DISTINCT TARGET, chiefly because it makes E-03's step narrow by construction rather than by careful filtering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `check all` grep counts for every workflow file; pasted finding counts and rule sets for `check backlog` versus `check all`; the named live violation; and an explicit statement of whether the naming debt still blocks the simpler fix.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of the new reachable invocation reporting `check.live-bug-ungated` on a fixture, plus evidence by inspection that it calls the shared predicate rather than a copy, plus the recorded choice of form and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the CI step's definition quoted; a pasted local run of that exact command FAILING (nonzero exit) on a violating fixture and PASSING on a clean one; and a diff or quote proving the advisory `check backlog` step is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: tests pasted showing the family fires on a violating fixture and NOT on a clean one; confirmation by inspection that no assertion reads live records; `aw check plans`/`check releases` shown unchanged; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
