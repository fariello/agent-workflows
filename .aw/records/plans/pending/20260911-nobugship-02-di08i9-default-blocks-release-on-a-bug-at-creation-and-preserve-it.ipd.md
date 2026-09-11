# IPD: Default Blocks-Release on a bug at creation and preserve it through graduation

- Date: 2026-09-11
- Kind: child
- Concern: A bug item gets a release gate only if its author remembers to pass one, and measurably they do not: 28 of 60 live bug items carry none. The gate is ALSO lost at graduation, measured: all 11 graduated gateless bugs have a plan carrying `- From-Backlog:`, and none of those plans carries `- Blocks-Release:`.
- Scope: Make the correct gate the DEFAULT rather than an act of memory, at both points where it is currently lost: creating a bug item, and graduating one into a plan or spec. Does NOT enforce anything retroactively (child 03 owns the backfill and the checker), does NOT gate other work kinds, and does NOT change what `next` resolves to.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/cli.py, tests/test_bug_gate_default.py
- Item-Dependencies: executed:zqs0px
- Status: to-review
- Set: nobugship
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: di08i9
- Blocks-Release: next

## Workflow history

- 2026-09-11 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored as the second third of the answer to the maintainer's 2026-09-11 question. MEASURED at HEAD `2ff2b1b1`: `backlog.run_new` reads `--blocks-release` from args and validates it resolves to a release record (`backlog.py:388-397`), but applies NOTHING when the flag is absent, so a `--work-kind bug` item is born ungated. `next` resolves to exactly one `planned` release (`f33nrj`, version 2.0.0, verified), so a default has an unambiguous target. THE GRADUATION LEAK IS THE HALF THAT WOULD OTHERWISE BE MISSED and it was found by measurement rather than reasoning: `AGENTS.md:38` already instructs an agent graduating an item to "inherit the item's `- Blocks-Release:` if it has one", yet all 11 graduated gateless bugs have a plan and none of those plans carries a gate. So the obligation exists in prose and is not honored, which is the same failure shape as the rule itself.

## Goal

Make a bug carry its release gate by construction at both points it is currently lost, so the rule holds without anyone remembering it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: default it at creation

- [ ] E-01 DEFAULT THE GATE WHEN A NEW ITEM'S WORK-KIND IS `bug`, in `backlog.run_new`, where the flag is read today (`backlog.py:388-397`). When `--blocks-release` is ABSENT and the work kind is `bug`, apply `next` and SAY SO in the command's output, so the author sees a field they did not type. Reuse the existing `releases.resolve_release` validation rather than assuming `next` resolves: if it does not (no `planned` release exists), REFUSE with a message naming the problem rather than writing an unresolvable gate, since `check.blocks-release-dangling` would otherwise flag the item the tool just created.
  AN EXPLICIT `-` MUST STILL CLEAR IT. The author may deliberately file an ungated bug, and the flag already distinguishes an explicit `-` from an absent value (`br is not None and br != "-"`). Preserve that: a default is not a prohibition, and forcing a gate with no escape would make the tool unusable for the case where a bug genuinely does not gate the release.
  - Depends on: none
  - Expected outcome: `aw backlog new --work-kind bug` with no gate flag produces an item carrying `- Blocks-Release: next` and prints that it did; `--blocks-release -` still produces an ungated item; an unresolvable `next` refuses rather than writing a dangling gate.
  - Execution state: pending

- [ ] E-02 DEFAULT IT ON A WORK-KIND CHANGE TOO, so the gate follows a reclassification. `aw backlog set` gains work-kind and priority setters in plan `b5sfwm`; when an item's work kind BECOMES `bug` and it carries no gate, apply the same default and report it. If `b5sfwm` has not landed, record that this half is deferred to it rather than implementing a second setter surface here.
  DO NOT REMOVE A GATE WHEN A WORK KIND CHANGES AWAY FROM `bug`. A gate may have been set deliberately for another reason, and silently clearing it would lose a decision; leave it and let a human clear it explicitly.
  - Depends on: E-01
  - Expected outcome: reclassifying an item to `bug` applies the gate and reports it; reclassifying away from `bug` leaves any existing gate untouched; or a recorded statement that this half awaits `b5sfwm` with the reason.
  - Execution state: pending

### Task group 2: stop losing it at graduation

- [ ] E-03 MAKE THE GRADUATION INHERITANCE REAL RATHER THAN PROSE. `AGENTS.md:38` already tells an agent to inherit the item's gate, and the measurement shows that instruction is not followed: 11 of 11 graduated gateless bugs have a plan with no gate. Make the tooling carry it: when a plan or spec declares `- From-Backlog: <id6>` and that item carries `- Blocks-Release:`, the artifact must carry the same value, and the setter that writes `From-Backlog` should apply it rather than expecting the author to.
  MEASURE FIRST, THEN CHOOSE THE SURFACE. `aw ipd set --from-backlog` already exists and is the natural place, but a plan may also declare the field at authoring time with no setter involved, in which case the checker in child 03 is the only backstop. State which paths you covered and which you did not, because an inheritance that works on one route and not the other is worse than none: it teaches false confidence.
  - Depends on: E-02
  - Expected outcome: setting `From-Backlog` to a gated item applies that item's gate to the artifact and reports it; the uncovered authoring route is named explicitly for child 03 to catch.
  - Execution state: pending

- [ ] E-04 TEST ALL THREE DEFAULTS AND THE THREE REFUSALS in a new `tests/test_bug_gate_default.py`, with a falsification pass: every assertion must be shown to FAIL against the pre-change code, since one that passes both before and after proves nothing.
  COVER THE ESCAPE AND THE NON-REGRESSION, not only the happy path: an explicit `-` still yields an ungated bug; a `--work-kind chore` item is NOT gated; and an existing gate is not overwritten by any of these paths.
  - Depends on: E-03
  - Expected outcome: tests for creation default, reclassification default, graduation inheritance, the explicit-`-` escape, the non-bug non-gating case, and the no-overwrite case, each shown failing against pre-change code.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `run_new` already validates `--blocks-release` through `releases.resolve_release` and refuses an unresolvable value (`backlog.py:388-397`), so a default must reuse that validation rather than trusting `next`.
- The flag already distinguishes an ABSENT value from an explicit `-` (`br is not None and br != "-"`), which is exactly the distinction a default needs in order to leave an escape.
- `next` resolves to the single `planned` release record; measured, that is `f33nrj` (2.0.0).
- `AGENTS.md:38` already states the graduation inheritance obligation in prose, and it is measurably not honored, which is why E-03 moves it into tooling.

## Findings

| Id | Severity | Finding |
|---|---|---|
| F-1 | HIGH | Creation applies no gate. `run_new` reads the flag and does nothing when it is absent, so a bug item is born ungated and 28 of 60 live bugs are in that state. |
| F-2 | HIGH | Graduation loses the gate too, and prose does not prevent it: `AGENTS.md:38` instructs inheritance, yet 11 of 11 graduated gateless bugs have a plan and NONE of those plans carries a gate. |
| F-3 | MEDIUM | A default has an unambiguous target: `next` resolves to exactly one `planned` release. But it must be validated rather than assumed, or the tool would write a dangling gate that `check.blocks-release-dangling` immediately flags. |
| F-4 | MEDIUM | An escape is required, not optional. The author may legitimately file an ungated bug, and the existing absent-versus-`-` distinction already supports that, so a default must not become a prohibition. |
| F-5 | LOW | The reclassification half depends on `b5sfwm`, which adds the work-kind setter to `aw backlog set` and is reviewed but unexecuted; E-02 states the deferral rather than building a second setter. |

## Proposed changes (ordered, validatable)

1. Default the gate at creation for `bug`, validated, reported, with an explicit escape (E-01).
2. Default it when a work kind becomes `bug`, or record the deferral to `b5sfwm` (E-02).
3. Move the graduation inheritance from prose into tooling, naming any uncovered route (E-03).
4. Test the defaults, the escape and the non-regressions, with falsification (E-04).

## Deferred / out of scope (with reason)

- ENFORCEMENT AND BACKFILL. Child 03 owns the checker and the 28 existing violations, deliberately after this child so the backfill cannot immediately re-diverge.
- OTHER WORK KINDS. The parent's OQ-01 asks about `security`; not assumed here.
- DETECTING A DEFECT FILED AS `chore`. The gate keys on the author's classification and cannot see a mislabelled defect; the parent's OQ-02 measures that leak and child 01 states it as a limit.

## Scope check

- Over-scope: none. Three paths: the backlog module where the flag is read, the CLI where the setters are wired, and one new test file.
- Under-scope: a plan that declares `From-Backlog` at authoring time with no setter involved is not covered by E-03 and is named for child 03's checker; this child does not claim to close that route.

## Required tests / validation

`tests/test_bug_gate_default.py` with a falsification pass against pre-change code. Establish the suite baseline by running `python3 -m pytest` bare BEFORE the first edit and paste it; no figure is stated here deliberately.

## Spec / documentation sync

N/A with reason: child 01 states the rule in the contributor rules and the decisions log, and this child implements it. If E-01's refusal message or the reported default needs documenting beyond that, add it to child 01's text rather than duplicating policy here.

## Open questions

### OQ-01: Should the creation default be silent or announced?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: ANNOUNCE IT, and E-01 is written that way. A field the tool wrote but the author did not type is exactly the kind of hidden behavior that makes a later reader distrust the record, and the repository's own precedent is to name what a tool did (the maintainer's 2026-09-10 ruling on a malformed config value was to fall back AND warn rather than fall back silently). Non-blocking because the gate is applied either way and only the output differs; recorded so the executor does not quietly drop the notice for tidiness.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `aw backlog new --work-kind bug` with NO gate flag in a scratch repo, showing the created item's `- Blocks-Release: next` line and the printed notice. Paste the same with `--blocks-release -` showing an UNGATED item. Paste the refusal when `next` cannot resolve (a scratch repo with no `planned` release), with its unpiped exit code, proving no dangling gate is written.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a reclassification to `bug` showing the gate applied and reported, and a reclassification AWAY from `bug` showing an existing gate untouched. If deferred to `b5sfwm`, paste that plan's status and the recorded deferral statement instead, and say explicitly that this half is not delivered.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste setting `From-Backlog` to a GATED item and show the artifact gaining the same gate value. Then paste the ROUTE INVENTORY: every path by which an artifact can acquire `From-Backlog`, marked covered or not, with the uncovered ones named for child 03. An inventory claiming full coverage must show the search that establishes it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_bug_gate_default.py -o addopts=""` with per-test names, then the FALSIFICATION showing the new cases FAIL against pre-change code. Confirm the escape, non-bug and no-overwrite cases are among them. Finally paste the bare `python3 -m pytest` summary against the pre-edit baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it has been reviewed and a human sets it `approved`.

It carries `- Item-Dependencies: executed:zqs0px` because the written rule is the authority this tooling implements; defaulting a gate before the policy is recorded would leave the behavior unexplained by any document.

It carries `- Blocks-Release: next` in line with the rule it implements.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped, never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark.

NOTE THE HAZARD: a default that cannot be escaped is worse than no default, because it forces an author to either accept a wrong gate or bypass the tool. The explicit `-` path is not optional polish; it is what keeps the tool honest, and V-01 must prove it works.
