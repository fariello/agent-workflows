# IPD: Announce declared spec edits on both hosts at run start and run end

- Date: 2026-09-07
- Kind: child
- Concern: A plan MAY amend a spec (maintainer ruling 2026-09-07), so the safeguard is VISIBILITY: whenever a run will modify a `.spec.md`, that fact must be raised clearly to the operator, at the START and at the END of the run. `AGENTS.md:82` already states this as doctrine AND asserts as present-tense fact that "`aw oc run` / `aw agy run` announce declared spec edits BEFORE the run starts". That assertion is TRUE OF ONE HOST AND FALSE OF THE OTHER, which is the dangerous direction: an operator who has read AGENTS.md believes the announcement is universal.
  THREE MEASURED GAPS, re-verified at HEAD by symbol rather than by the item's stale line numbers. (1) AGY NEVER ANNOUNCES: `agy_runipd.py:163` re-exports `spec_impacts_for_queue` and that is the ONLY occurrence in the file; `format_spec_impact_announcement` appears ZERO times. The import is dead. The sole caller anywhere is `oc_runipd.py:4146-4148`. (2) NEITHER HOST ANNOUNCES AT THE END: the only call site sits in the run-order announcement path, before dispatch, so the operator's one chance to notice is the top of a scrollback a long run will have buried. (3) THE START ANNOUNCEMENT IS SILENT ON ITS OWN FAILURE: `oc_runipd.py:4149-4151` wraps the call in `except Exception: pass` ("Advisory only: never let a missing announcement stop a run from starting"). Not aborting the run is right; swallowing WITHOUT A TRACE is not, because the failure mode is indistinguishable from "this run amends no spec".
  WHY IT BLOCKS THE RELEASE. Two plans in flight now legitimately carry spec amendments on maintainer rulings: `51vw4y` (amend `25kzda` 2.1, then register the two ladder flags) and `03ie04` (amend 2.9 first, then land). The release should not ship with the announcement covering one host and one end of the run while plans are actively rewriting the contract every other plan is reviewed against.
- Scope: Make the declared-spec-edit announcement real on BOTH hosts and at BOTH ends of a run, from ONE shared implementation, and make a failed computation say so instead of vanishing. Then make `AGENTS.md:82`'s present-tense claim true (or correct it). Add no new policy: this plan changes what the operator is TOLD, never what a run is ALLOWED to do.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, AGENTS.md, tests/test_run_order_announcement.py, tests/test_spec_impact_visibility.py
- Item-Dependencies: none
- Status: to-review
- Set: specvis
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: st5klo
- From-Backlog: dk16dx
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `dk16dx`. Every citation re-located BY SYMBOL rather than trusted: the item's `agy_runipd.py:162` is now `:163`, and `oc_runipd.py:4100-4108` is now `:4146-4151`, because both driver modules moved during the day. The dead-import claim and the zero-occurrence claim for `format_spec_impact_announcement` were re-run and both hold.

## Goal

An operator learns, before a run starts and again when it ends, exactly which spec files that run declared it would change, on whichever host they used, and learns when that computation failed instead of silently seeing nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the start announcement honest and universal

- [ ] E-01 STOP SWALLOWING THE FAILURE. Replace the bare `except Exception: pass` at `oc_runipd.py:4149-4151` with a handler that still cannot abort the run but DOES emit one line saying the spec-impact announcement could not be computed, naming the exception class. Keep the advisory contract exactly as documented: a missing announcement must never stop a run from starting.
  THIS IS THE HIGHEST-VALUE LINE IN THE PLAN AND MUST NOT BE "IMPROVED" INTO A REFUSAL. The reason the swallow is wrong is not that it is lenient, it is that SILENCE IS AMBIGUOUS: today "no spec edits declared" and "the computation crashed" render identically, so an operator cannot tell a clean run from a broken announcer. Emitting the failure resolves the ambiguity without changing what the run is permitted to do.
  - Depends on: none
  - Expected outcome: a computation failure prints a named, one-line advisory and the run still starts; a genuinely empty impact set still prints nothing extra and is distinguishable from a failure.
  - Execution state: pending

- [ ] E-02 WIRE THE AGY HOST TO THE SAME START ANNOUNCEMENT, which is the gap that makes `AGENTS.md:82` false today. `agy_runipd.py` re-exports `spec_impacts_for_queue` (`:163`) and never calls it, and never references `format_spec_impact_announcement` at all. Call the SHARED pair from agy's equivalent pre-dispatch point, and do NOT copy the oc call site's body into agy.
  ONE IMPLEMENTATION, NOT TWO. Both the impact computation (`runner_shared.spec_impacts_for_queue`, `:251-253`) and the rendering (`render_stream.format_spec_impact_announcement`) already live in shared modules; only the CALL is missing. If wiring reveals that the two hosts' pre-dispatch points differ enough to need a helper, put the helper in `runner_shared.py` and have both hosts call it, per `cnwy8g` on the 40-symbol driver coupling. A second copy in agy is the drift this Set exists to prevent.
  - Depends on: E-01
  - Expected outcome: `aw agy run` prints the same declared-spec-edit announcement `aw oc run` prints, from the same shared functions, with no logic duplicated into `agy_runipd.py`.
  - Execution state: pending

### Task group 2: announce at the END, reconciled against what was declared

- [ ] E-03 ADD AN END-OF-RUN SPEC-EDIT REPORT, on BOTH hosts, sited with the existing run summary rather than in a new surface. `render_run_summary_table` is the end-of-run rendering seam and is already called by both drivers (`oc_runipd.py:7267`, `:8124`, `:8170`; `agy_runipd.py:4489`, `:5078`, `:5124`). Emit the spec-edit report adjacent to it so it lands in the same place an operator already reads.
  REPORT WHAT WAS ACTUALLY CHANGED, RECONCILED AGAINST WHAT WAS DECLARED, and reuse the reconciliation that already exists rather than diffing again: `_compute_scope_reconciliation` (`oc_runipd.py:944`, `agy_runipd.py:876`) already computes the declared-versus-actual scope audit by delegating to `ipd_lifecycle.finalize_precheck`. A spec file DECLARED but never modified, and one MODIFIED but never declared, are both worth a line; the second is the one that matters, because it is an undeclared contract change.
  NOTE THE MULTIPLE CALL SITES ARE NOT ACCIDENTAL. Each driver calls the summary renderer three times (normal completion, and two other paths). Determine which of them are genuine run-END paths and cover those; state explicitly which sites you wired and which you deliberately did not, because a report that only fires on the happy path misses exactly the aborted runs an operator most needs to inspect.
  - Depends on: E-02
  - Expected outcome: both hosts print, at run end, the spec files the run declared and the spec files it actually modified, reconciled; every summary call site is either wired or explicitly excluded with a reason.
  - Execution state: pending

- [ ] E-04 TEST BOTH ENDS ON BOTH HOSTS, in a new `tests/test_spec_impact_visibility.py`, parameterized over the two drivers rather than duplicated. Cover: a queue whose plan declares a `.spec.md` (announced at start AND at end, on both hosts); a queue declaring none (announced as nothing, on both hosts); a computation failure (advisory line emitted, run still starts); and the reconciliation asymmetry (declared-not-modified, and modified-not-declared).
  ASSERT THE AGY PATH BY RUNNING IT, NOT BY READING THE IMPORT. The defect this plan fixes is precisely that agy's import exists and is never called, so a test that only checks the symbol is importable would have PASSED against the broken code. Drive agy's actual announcement path and assert on its output.
  EXTEND, DO NOT REPLACE, `tests/test_run_order_announcement.py`, which already covers the surrounding run-order announcement; the spec-impact assertions belong beside it or in the new file, and the existing cases must stay green unedited.
  - Depends on: E-03
  - Expected outcome: a test that FAILS against today's code for the agy start case, the end-of-run case on both hosts, and the silent-failure case; passes after; existing run-order announcement tests unchanged and green.
  - Execution state: pending

### Task group 3: make the documented claim true

- [ ] E-05 RECONCILE `AGENTS.md:82` WITH REALITY. Its managed block asserts that both runners announce declared spec edits before a run starts. After E-02 that becomes true for the start; extend the sentence to state the END announcement too, and to state that a failed computation is reported rather than silent.
  IT IS A MANAGED BLOCK, SO EDIT THE SOURCE, NOT THE RENDERED COPY. `AGENTS.md`'s `<!-- aw:block -->` content is installed from `engine.py`; a hand-edit to the rendered file will be overwritten on the next install. Find the generating string and change it there, then regenerate, and state in the report which file actually holds the text. If the source and the rendered copy disagree before you start, say so rather than silently normalizing.
  - Depends on: E-04
  - Expected outcome: the doctrine text matches shipped behavior for both hosts and both ends, edited at its generating source with the rendered copy regenerated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The impact computation and its renderer ALREADY live in shared modules (`runner_shared.spec_impacts_for_queue`, `render_stream.format_spec_impact_announcement`); only the agy call is missing. This is a wiring plan, not a design plan.
- `spec_impacts_for_queue` reads each item's plan file FROM DISK at dispatch rather than trusting run state, deliberately, "so the announcement reflects the plan as it stands at dispatch" (`runner_shared.py:256-259`). Preserve that.
- Its docstring also records that an unreadable plan is SKIPPED rather than failing the run, for the same advisory reason. E-01 must keep that posture while making the failure visible.
- `AGENTS.md` carries managed blocks installed from `engine.py`; hand-edits inside them do not survive.
- The suite is run BARE (`python3 -m pytest`). Shared checkout: run `aw runs` first.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | agy host | agy re-exports the impact helper and NEVER calls it; it never mentions the renderer at all. The announcement simply does not exist on that host. | `agy_runipd.py:163` is the only occurrence of `spec_impacts_for_queue` in the file; `grep -c format_spec_impact_announcement agent_workflows/agy_runipd.py` = 0 |
| F-2 | HIGH | doc vs reality | `AGENTS.md:82` asserts both runners announce, in the present tense. False for agy, so the doctrine over-promises in the fail-open direction. | `AGENTS.md:82` versus F-1 |
| F-3 | HIGH | run end | Neither host announces at the end. The sole call site is pre-dispatch. | `oc_runipd.py:4146-4148` is the only caller anywhere in `agent_workflows/` |
| F-4 | MEDIUM | silent failure | The start announcement swallows any exception with no trace, making "no spec edits" and "announcer crashed" indistinguishable. | `oc_runipd.py:4149-4151` (`except Exception: pass`) |
| F-5 | MEDIUM | reconciliation exists | The declared-versus-actual scope audit is already computed and must be reused, not re-derived. | `_compute_scope_reconciliation` at `oc_runipd.py:944`, `agy_runipd.py:876`, delegating to `ipd_lifecycle.finalize_precheck` |
| F-6 | MEDIUM | summary seam | The end-of-run renderer is called THREE times per driver, so "wire the end" is ambiguous until the sites are enumerated. | `oc_runipd.py:7267`, `:8124`, `:8170`; `agy_runipd.py:4489`, `:5078`, `:5124` |
| F-7 | LOW | stale citations | The item's line numbers had already drifted (`agy:162`->`:163`, `oc:4100-4108`->`:4146-4151`), which is why this plan re-locates by symbol. | both re-measured at HEAD 2026-09-08 |

## Proposed changes (ordered, validatable)

1. Make the start announcement's failure visible without letting it abort a run (E-01).
2. Wire agy to the same shared start announcement, adding no second copy (E-02).
3. Add the end-of-run report on both hosts, reconciled via the existing scope audit (E-03).
4. Test both ends on both hosts, driving agy's real path (E-04).
5. Make `AGENTS.md:82` true, edited at its generating source (E-05).

## Deferred / out of scope (with reason)

- REFUSING a run that declares a spec edit, or requiring extra consent for one: explicitly not this plan. The maintainer ruled a plan MAY amend a spec; this plan changes what the operator is TOLD, never what a run may do. Adding a gate would reverse that ruling.
- VALIDATING that a declared spec amendment is CORRECT, or that it matches the plan's spec-sync prose: a review-quality question, not a visibility one.
- PER-REQUIREMENT spec coverage tracking (the "which half of this spec is unbuilt" gap): named in backlog `f1sw71`, unrelated mechanism.
- The `--full-auto` interaction: whether an unattended run should announce differently is a policy question this plan deliberately does not open.

## Scope check

- Over-scope: none. Two shared modules, two drivers, one doc source, two test files.
- Under-scope: this plan does NOT gate spec edits, does not verify amendment correctness, and does not touch the finalize scope gate itself (it only CONSUMES the reconciliation the gate already computes).

## Required tests / validation

New `tests/test_spec_impact_visibility.py` parameterized over both drivers, covering start and end, the empty case, the failure case, and both reconciliation asymmetries. Existing `tests/test_run_order_announcement.py` must stay green UNEDITED. Plus the bare suite judged on a self-measured delta.

## Spec / documentation sync

No `.spec.md` is amended by this plan, so no spec file is declared in `- Scope-Paths:`. That is deliberate and worth stating plainly, because this plan is ABOUT spec-edit visibility and it would be confusing for it to also amend a spec.

`AGENTS.md` IS edited (E-05), and it is a MANAGED BLOCK whose text is installed from `engine.py`. The report must name which file actually holds the generating string, since editing the rendered copy alone would be silently reverted by the next `aw install`.

## Open questions

### OQ-01: Should the end-of-run report appear on ALL THREE summary call sites per driver, or only on normal completion?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED AT AUTHORING from a MEASUREMENT (F-6), and left OPEN because it is a judgement about operator attention rather than a fact the repository settles. Each driver calls `render_run_summary_table` three times, and the two non-primary sites correspond to paths where a run did not complete normally. THE ARGUMENT FOR ALL THREE: an aborted or stopped run is exactly when an operator most needs to know a spec was rewritten, and a report that only fires on success hides the interesting case. THE ARGUMENT FOR ONE: on an aborted path the reconciliation may be incomplete or unreliable, and printing a half-computed contract change could mislead worse than printing nothing. E-03 currently requires the executor to wire what it can and STATE which sites it excluded and why, so the plan is executable either way and the decision is recorded rather than assumed. NOT BLOCKING because the plan's value does not depend on the answer: the normal-completion path alone closes F-3.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new handler's source and paste THREE runs distinguishable from each other: a run declaring a spec edit (announcement printed), a run declaring none (no spurious line), and a run where the computation RAISES (advisory line naming the exception class, and the run still starts). Force the failure by patching `spec_impacts_for_queue` to raise, and paste the exit code proving the run was not aborted.
    The load-bearing assertion is DISTINGUISHABILITY: paste the empty-case output and the failure-case output side by side and show they differ. If they are identical, this item has not been done.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw agy run ... --prepare-only` (or the equivalent that reaches the pre-dispatch announcement) showing the declared-spec-edit announcement on the AGY host, for a queue whose plan declares a `.spec.md`. A symbol-import assertion is a FAILED validation: the pre-fix code already imports the helper successfully, so only driving the real path proves anything.
    Paste `git diff agent_workflows/agy_runipd.py` and show it contains NO copy of the impact or rendering logic, only a call. State which shared function each host calls and confirm by object identity that both hosts reach the same implementation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the end-of-run output on BOTH hosts for a run that modified a declared `.spec.md`, and for a run that modified a spec it did NOT declare (the undeclared contract change, which is the case that matters). Show the reconciliation names both asymmetries.
    ENUMERATE THE SUMMARY CALL SITES (F-6): list all six (`oc_runipd.py:7267`, `:8124`, `:8170`; `agy_runipd.py:4489`, `:5078`, `:5124`), and for EACH state whether you wired it and why. An unenumerated site is an unanswered question, and OQ-01 exists precisely because this choice is not obvious.
    Confirm you consumed `_compute_scope_reconciliation` rather than writing a second diff, and paste the call.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test FAILING against pre-change HEAD for at least the agy start case, the end-of-run case, and the silent-failure case, then passing after. Paste `python3 -m pytest tests/test_run_order_announcement.py` green and `git diff --stat -- tests/test_run_order_announcement.py` EMPTY, proving the existing coverage was extended-beside rather than edited.
    Paste the bare `python3 -m pytest` summary line with a BEFORE baseline you measured yourself and the AFTER-minus-BEFORE failure set shown EMPTY. Note the ~14 `test_run_viewer.py` failures that appear inside a lane worktree are the pre-existing `agrlvw` defect (plan `utwr6y`), not this plan's.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of the GENERATING source (name the file; if it is `engine.py`, paste that hunk) AND the regenerated `AGENTS.md` hunk, showing they agree. Quote the new sentence and confirm it claims only what now ships: both hosts, both ends, failure reported. State explicitly whether the source and rendered copy disagreed BEFORE your edit, since a pre-existing drift there is a separate finding worth reporting rather than silently fixing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 is open but `Blocking: no`, so it does not gate approval; E-03 requires the executor to record which summary sites it wired either way.

THIS PLAN ADDS NO POLICY. It changes what the operator is told, never what a run may do. If executing it appears to require refusing a run, gating a spec edit, or adding a consent flag, STOP and report: that would reverse the maintainer ruling this item exists to serve.

ONE IMPLEMENTATION, BOTH HOSTS. Every change lands in shared code with both drivers calling it. A second copy in `agy_runipd.py` is the specific failure this Set is guarding against, and `render_stream` was already extracted once and re-forked in the other driver with nothing noticing.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: both driver modules are being edited by concurrent runs, so RE-LOCATE EVERY CITED SYMBOL before editing; this plan's own line numbers are already the second generation.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `dk16dx` (this plan carries `- From-Backlog: dk16dx` and inherits its `Blocks-Release: next`).
