# IPD: Announce declared spec edits on both hosts at run start and run end

- Date: 2026-09-07
- Kind: child
- Concern: A plan MAY amend a spec (maintainer ruling 2026-09-07), so the safeguard is VISIBILITY: whenever a run will modify a `.spec.md`, that fact must be raised clearly to the operator, at the START and at the END of the run. `AGENTS.md:82` states this as doctrine AND asserts as present-tense fact that "`aw oc run` / `aw agy run` announce declared spec edits BEFORE the run starts".
  THE CENTRAL PREMISE OF THIS PLAN AS AUTHORED IS FALSE, AND REVIEW PROVED IT BY EXECUTION RATHER THAN BY READING (review, F-8). AGY ALREADY ANNOUNCES. The spec-impact block lives INSIDE `announce_run_order`, which is DEFINED in `oc_runipd.py:4178` and which `agy_runipd.py` both imports (`:377`, `announce_run_order as announce_run_order`) and CALLS (`:2109`, in `initialize_run`, before the first child session). Verified two ways: `agy_runipd.announce_run_order is oc_runipd.announce_run_order` returns True, and driving the AGY entry point on a fixture queue whose plan declares a `.spec.md` PRINTS the announcement, captured verbatim: `SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).` So `AGENTS.md:82` is TRUE today, not false, and the "dangerous direction" this plan was built around does not exist. The comment at `agy_runipd.py:84-88` says so in as many words: "The announcement itself is emitted through the shared `announce_run_order` below, so the two hosts cannot drift the way `Heartbeat` once did."
  WHAT THE GREP ACTUALLY SHOWED, and why it misled. `spec_impacts_for_queue` appears once in `agy_runipd.py` (`:163`) and `format_spec_impact_announcement` zero times, both re-measured true at review. But those are the WRONG symbols to test: agy does not need to name them, because it calls the shared FUNCTION that names them. The re-export at `:163` is not a dead import to be wired up, it is the deliberate `as <same-name>` re-export form this module uses "for every shared object it must expose but does not call itself, so an autoformatter cannot strip it" (`:84-86`). An existing test already asserts the sharing by object identity (`tests/test_spec_visibility.py:161-169`).
  SO ONE OF THE THREE GAPS SURVIVES, AND IT IS THE SMALLEST ONE. (1) NEITHER HOST ANNOUNCES AT THE END: re-verified, the only spec-impact call site anywhere is inside `announce_run_order`, which runs pre-dispatch, so the operator's one chance to notice is the top of a scrollback a long run will have buried. This is REAL and is now the plan's primary deliverable. (2) THE START ANNOUNCEMENT IS SILENT ON ITS OWN FAILURE: re-verified at `oc_runipd.py:4204-4207`, `except Exception: pass` with the comment "Advisory only: never let a missing announcement stop a run from starting". Not aborting the run is right; swallowing WITHOUT A TRACE is not, because the failure mode is indistinguishable from "this run amends no spec". This is REAL and, because the swallow is inside the SHARED function, fixing it fixes both hosts at once. (3) AGY NEVER ANNOUNCES: FALSE, withdrawn.
  WHY IT STILL BLOCKS THE RELEASE, on a corrected basis. Plans legitimately carry spec amendments on maintainer rulings, and one has already landed: `03ie04` is `executed` (it amended 2.9 first, then landed) and `51vw4y` is `reviewed` (amend `25kzda` 2.1, then register the two ladder flags). So the contract other plans are reviewed against is ALREADY being rewritten by runs, and today a run reports that only at the top of the scrollback and reports an announcer crash not at all. That is a smaller gap than the plan first claimed and still a release-worthy one; it is NOT the "one host is blind" emergency.
- Scope: Add the END-OF-RUN declared-spec-edit report on both hosts from ONE shared implementation, and make a failed START computation say so instead of vanishing. Both land in shared code, so both reach both hosts. Then EXTEND `AGENTS.md:82` to cover the new end-of-run behavior and the reported failure; its existing start-of-run claim is already TRUE and must not be "corrected" (F-8). Add no new policy: this plan changes what the operator is TOLD, never what a run is ALLOWED to do. EXCLUDES wiring agy to the start announcement, which review proved is already wired.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, agent_workflows/engine.py, AGENTS.md, tests/test_spec_visibility.py, tests/test_spec_impact_visibility.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: specvis
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: st5klo
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: dk16dx
- Blocks-Release: next

## Workflow history
- 2026-09-14 executed (opencode its_direct/pt3-claude-opus-5-1m-us, `aw oc run` position 07 of run-20260914T020813Z-2543555): E-01..E-05 performed, V-01..V-05 pass with pasted evidence. NEW HIGH FINDING F-12, and it inverts this plan's own framing: at pre-change HEAD the start-of-run declared-spec-edit announcement fired on NEITHER host, so review's F-8 was half wrong and E-02 was a real fix rather than the regression guard the plan insisted it be. Root cause: `runner_shared.spec_impacts_for_queue` reads `item["path"]`/`item["plan_path"]` while a real runner queue entry carries only `"configured_file"`, so the impact set was empty for every item of every real run; the whole feature was inert from the day it shipped and the suite stayed green because every existing case hand-builds a queue with the key production never writes. Proved by driving both entry points against a pristine `git archive HEAD` tree (`SPEC CHANGES announced: False` on oc AND agy) and again after the fix (`True` on both). I therefore DELIBERATELY DISOBEYED the plan's instruction "DO NOT WRITE A TEST THAT FAILS ON THE AGY START CASE": that instruction was written against a mismeasurement, and the agy start case is now in the fails-before-passes-after set. Fixed at the call site with a shared `queue_with_plan_paths` adapter, which keeps the shared helper's documented contract and this plan's declared `Scope-Paths` intact (D1). Delivered besides: the start announcement's swallowed exception now prints a named advisory and still cannot abort a run (E-01, both hosts from ONE shared edit, zero agy announcement-path changes); an END-OF-RUN spec-edit report at ALL SIX summary sites (three per host) from ONE shared emitter in `render_stream`, reconciled by CONSUMING each host's existing `_compute_scope_reconciliation` (fork neither deepened nor unified, D2) and honest about F-9's three limits (never-finalized, empty-because-refused, per-item-to-per-queue aggregation), with the four non-primary sites labelled POSSIBLY INCOMPLETE per OQ-01; a new 25-test `tests/test_spec_impact_visibility.py` that drives real entry points instead of asserting symbol identity; and `AGENTS.md` extended at its generating source in `engine.py` then regenerated, with the (now genuinely true) start claim left verbatim. Suite: `1 failed, 6828 passed` before, `1 failed, 6853 passed` after, AFTER-minus-BEFORE failing node set EMPTY; the single failure is the environmental `test_lanectn_refuses_naming_its_one_unfinished_child`, which asserts against live repo plan state other lanes moved. `aw sanitize --agent` clean. Not pushed.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-905 all FIXED; readiness `go-pending-approval`. SELF-REVIEW disclosure: the same agent/model authored this plan, so its value rests on EXECUTING its claims rather than re-reading them. THE PLAN'S CENTRAL PREMISE WAS FALSE AND EXECUTION IS WHAT CAUGHT IT (PR-901, HIGH). The plan asserted `aw agy run` NEVER announces declared spec edits, and built its Concern, F-1, F-2, E-02, V-02 and its release-blocking argument on that. Measured: agy DOES announce. The spec-impact block lives inside `announce_run_order`, DEFINED in `oc_runipd.py:4178`, which `agy_runipd.py` imports (`:377`) and calls (`:2109`) before the first child session. Proved twice: `agy_runipd.announce_run_order is oc_runipd.announce_run_order` returns True, and driving the AGY entry point on a fixture queue whose plan declares a `.spec.md` printed `SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).` The plan reached the wrong conclusion by GREPPING agy for the inner symbols instead of driving the path, which is precisely the mistake its own E-04 forbids, and the repository already contains a test with that same weakness (`tests/test_spec_visibility.py:161-169` asserts object identity only, and would pass against a host that calls nothing). So F-1 and F-2 are WITHDRAWN with their disproof, `AGENTS.md:82` is TRUE and E-05 now EXTENDS rather than corrects it, E-02 became a behavioral regression guard that must add NO agy call site (a second call would double-print), and the END-OF-RUN report is now the plan's primary deliverable. Two further findings: the reconciliation E-03 consumes is per-ITEM, at finalize, against the LANE worktree, and returns an empty pair when the precheck REFUSES, so an empty result is ambiguous exactly as E-01's swallow is (PR-902); and the plan declared `tests/test_run_order_announcement.py` while requiring its diff be EMPTY, which costs a `--scope-ack` for nothing (PR-905). `Scope-Paths` was corrected: `engine.py` ADDED (E-05 edits the generating string there, located at `:1351`), `runner_shared.py` and `tests/test_run_order_announcement.py` REMOVED, `tests/test_spec_visibility.py` added. Every line number in the plan had drifted a THIRD time and was re-measured.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `dk16dx`. Every citation re-located BY SYMBOL rather than trusted: the item's `agy_runipd.py:162` is now `:163`, and `oc_runipd.py:4100-4108` is now `:4146-4151`, because both driver modules moved during the day. The dead-import claim and the zero-occurrence claim for `format_spec_impact_announcement` were re-run and both hold.

## Goal

An operator learns, before a run starts and again when it ends, exactly which spec files that run declared it would change, on whichever host they used, and learns when that computation failed instead of silently seeing nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the start announcement honest and universal

- [x] E-01 STOP SWALLOWING THE FAILURE. Replace the bare `except Exception: pass` (re-located at review to `oc_runipd.py:4204-4207`, inside `announce_run_order` which begins at `:4178`) with a handler that still cannot abort the run but DOES emit one line saying the spec-impact announcement could not be computed, naming the exception class. Keep the advisory contract exactly as documented: a missing announcement must never stop a run from starting.
  THIS ONE EDIT FIXES BOTH HOSTS, WHICH IS WHY IT IS FIRST. The swallow sits inside the SHARED `announce_run_order`, and `agy_runipd.py` imports (`:377`) and calls (`:2109`) that same function object (proved by identity at review, F-8). So there is no agy-side work to do here and none to do in a follow-up: verify that by asserting the fix is visible from the AGY entry point, not only the oc one.
  THIS IS THE HIGHEST-VALUE LINE IN THE PLAN AND MUST NOT BE "IMPROVED" INTO A REFUSAL. The reason the swallow is wrong is not that it is lenient, it is that SILENCE IS AMBIGUOUS: today "no spec edits declared" and "the computation crashed" render identically, so an operator cannot tell a clean run from a broken announcer. Emitting the failure resolves the ambiguity without changing what the run is permitted to do.
  PIN THE START ANNOUNCEMENT'S PLACEMENT WHILE YOU ARE HERE, because the maintainer made it a REQUIREMENT 2026-09-08: the assertion that specs will be edited is made at the start of THE RUNNER, covering the WHOLE QUEUE before any dispatch, and NOT at the start of each IPD. That is already the current placement (the sole call site sits in the run-order announcement path before any worker is spawned, and `spec_impacts_for_queue` reads the whole queue at once), so this is a REGRESSION GUARD rather than new behavior: add a test asserting the announcement happens once, pre-dispatch, for the entire queue. Without it, a later change could plausibly "improve" this into a per-item announcement, which would bury the one pre-spend warning inside the run.
  - Depends on: none
  - Expected outcome: a computation failure prints a named, one-line advisory and the run still starts; a genuinely empty impact set still prints nothing extra and is distinguishable from a failure; and a test pins the start announcement as one whole-queue, pre-dispatch event.
  - Execution state: performed

- [x] E-02 PROVE THE START ANNOUNCEMENT ALREADY REACHES BOTH HOSTS, AND LOCK THAT IN WITH A BEHAVIORAL TEST. This item was authored as "wire the agy host"; review proved the wiring already exists (F-8), so the work is to CONVERT the false gap into a regression guard rather than to build anything.
  DO NOT ADD AN AGY CALL SITE. `agy_runipd.py:2109` already calls the shared `announce_run_order` inside `initialize_run`, before the first child session, and that function contains the spec-impact block. Adding a second call would print the announcement TWICE on agy, which is a new defect. If you find yourself editing `agy_runipd.py` to add a call, STOP: re-run the identity check first.
  THE EXISTING SHARING TEST IS NOT SUFFICIENT AND IS EXACTLY THE ANTI-PATTERN THIS PLAN WARNS ABOUT. `tests/test_spec_visibility.py:161-169` (`TestBothHostsShareOneDefinition`) asserts `spec_impacts_for_queue` and `declared_spec_paths` are the same object on both drivers. That is a SYMBOL assertion: it would pass even if agy never called anything, which is precisely the false-positive shape E-04 forbids. Add a BEHAVIORAL case that drives the AGY entry point with a fixture queue declaring a `.spec.md` and asserts the announcement text appears in captured stdout. Review did exactly this and captured `SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).` from the agy path; make that an assertion so a future re-fork cannot pass the identity test while breaking the behavior.
  - Depends on: E-01
  - Expected outcome: no new call site in `agy_runipd.py`; an identity check plus a BEHAVIORAL test proving `aw agy run`'s pre-dispatch path actually prints the announcement; the false "agy never announces" claim recorded as withdrawn with its disproof.
  - Execution state: performed

### Task group 2: announce at the END, reconciled against what was declared

- [x] E-03 ADD AN END-OF-RUN SPEC-EDIT REPORT, on BOTH hosts, sited with the existing run summary rather than in a new surface. THIS IS NOW THE PLAN'S PRIMARY DELIVERABLE, since E-02's gap proved false and E-01 is a one-line honesty fix. `render_run_summary_table` is the end-of-run rendering seam and is already called by both drivers; re-located at review because the plan's numbers had drifted a THIRD time: `oc_runipd.py:7480`, `:8383`, `:8429`; `agy_runipd.py:4490`, `:5084`, `:5130`. Emit the spec-edit report adjacent to it so it lands in the same place an operator already reads.
  PREFER A SHARED EMITTER OVER SIX CALL SITES OF INLINE LOGIC. Six sites across two drivers is exactly the surface that re-forks. Put the report's computation and rendering in shared code (`render_stream` for the wording, alongside `format_spec_impact_announcement`) and have each site call it, so the end-of-run report has ONE definition just as the start announcement does. If the six sites' available state differs, pass what differs as arguments rather than branching inside each driver.
  REPORT WHAT WAS ACTUALLY CHANGED, RECONCILED AGAINST WHAT WAS DECLARED, and reuse the reconciliation that already exists rather than diffing again: `_compute_scope_reconciliation` (re-located at review to `oc_runipd.py:953`, `agy_runipd.py:942`) already computes the declared-versus-actual scope audit by delegating to `ipd_lifecycle.finalize_precheck`. A spec file DECLARED but never modified, and one MODIFIED but never declared, are both worth a line; the second is the one that matters, because it is an undeclared contract change.
  NOTE THE RECONCILIATION HELPER IS ITSELF FORKED PER DRIVER (`oc_runipd.py:953` and `agy_runipd.py:942` are two definitions of the same name), which is the drift this Set exists to prevent. Do NOT fix that here: it is out of scope and is its own change. But do NOT deepen it either: call each host's existing local helper, or promote ONE to shared and have both use it, and say in the report which you did and why.
  WIRE ALL THREE CALL SITES PER HOST, AND LABEL THE TWO NON-PRIMARY ONES AS POSSIBLY INCOMPLETE. RESOLVED BY THE MAINTAINER 2026-09-08 (see OQ-01): the report fires on every summary site, because an aborted or stopped run is exactly when an operator most needs to know a spec was rewritten, AND the two early-exit paths must SAY that their reconciliation may be partial. Do not print a half-computed contract change as though it were authoritative; that was the sole argument for restricting to the happy path, and labelling answers it without hiding the interesting case.
  THE RECONCILIATION IS PER-ITEM, AT FINALIZE, IN A LANE WORKTREE, AND CONDITIONAL, WHICH CONSTRAINS WHAT THE END REPORT CAN HONESTLY CLAIM (review, F-9). Measured: `_compute_scope_reconciliation(repo, plan_path)` is called once per plan from the finalize helper (`oc_runipd.py:995`), its `repo` is deliberately the LANE worktree rather than the main checkout ("`repo` here is the LANE worktree ... because finalize must resolve paths against the tree it is finalizing"), and it RETURNS `({}, {})` whenever `finalize_precheck` refuses, which happens on a bad or missing begin receipt or a failing pre-transition lint. Three consequences the report must respect. FIRST, an item that never reached finalize has NO reconciliation, so the end report must distinguish "declared and reconciled" from "declared, never finalized" instead of rendering the second as a clean delta. SECOND, an empty pair is AMBIGUOUS in exactly the way E-01 is fixing elsewhere: it means either a clean delta or a refused precheck, so do not print "no spec changes" on the strength of an empty pair alone. THIRD, this is per-ITEM data while the start announcement is per-QUEUE, so the end report must aggregate across items and say how many it could and could not reconcile. If honoring this proves to need more than the existing helper returns, report that rather than inferring a spec edit from a source the code cannot vouch for.
  - Depends on: E-02
  - Expected outcome: both hosts print, at run end, the spec files the run declared and the spec files it actually modified, reconciled per item and aggregated, at ALL SIX summary call sites, with the four non-primary sites labelled possibly incomplete, with items that never finalized distinguished from clean ones, and with an empty reconciliation never rendered as a positive all-clear.
  - Execution state: performed

- [x] E-04 TEST BOTH ENDS ON BOTH HOSTS, in a new `tests/test_spec_impact_visibility.py`, parameterized over the two drivers rather than duplicated. Cover: a queue whose plan declares a `.spec.md` (announced at start AND at end, on both hosts); a queue declaring none (announced as nothing, on both hosts); a computation failure (advisory line emitted, run still starts); the reconciliation asymmetry (declared-not-modified, and modified-not-declared); and the two cases F-9 adds, an item that never finalized and an empty-because-refused reconciliation.
  ASSERT BEHAVIOR BY RUNNING IT, NOT BY READING THE IMPORT, AND NOTE THE REPOSITORY ALREADY CONTAINS THE ANTI-PATTERN THIS RULE FORBIDS. `tests/test_spec_visibility.py:161-169` asserts only that `spec_impacts_for_queue` and `declared_spec_paths` are the SAME OBJECT on both drivers. That test passes whether or not either host ever calls them, which is why the plan's own authors could read the code and conclude agy was blind while agy was in fact announcing (F-8). Every new case must drive an entry point and assert on captured output.
  DO NOT WRITE A TEST THAT FAILS ON THE AGY START CASE, because that case ALREADY PASSES. The plan previously required exactly that as proof of the fix; review drove the agy path and captured the announcement, so a test expecting today's code to fail there is a test written against a defect that does not exist. The honest version asserts agy's start announcement passes BEFORE and AFTER (a regression guard), and reserves the fails-before-passes-after shape for the two real gaps: the end-of-run report and the silent failure.
  EXTEND, DO NOT REPLACE, THE EXISTING SPEC TESTS. `tests/test_spec_visibility.py` (16 tests) already covers `declared_spec_paths`, `spec_impacts_for_queue`, the renderer's wording, its purity, and the object-identity sharing; those cases must stay green. `tests/test_run_order_announcement.py` (34 tests) covers the surrounding run-order announcement and must stay green UNEDITED. Note the plan originally declared `tests/test_run_order_announcement.py` in `Scope-Paths` while also requiring its diff be EMPTY; that contradiction is resolved by declaring `tests/test_spec_visibility.py` (which E-02 legitimately extends) instead.
  - Depends on: E-03
  - Expected outcome: a test that FAILS against today's code for the end-of-run case on both hosts and the silent-failure case, and PASSES both before and after for the agy start case; the six-case matrix covered; `tests/test_run_order_announcement.py` green and unedited; `tests/test_spec_visibility.py` extended with its existing cases green.
  - Execution state: performed

### Task group 3: make the documented claim true

- [x] E-05 EXTEND `AGENTS.md:82` TO COVER THE NEW BEHAVIOR, WITHOUT "CORRECTING" A CLAIM THAT IS ALREADY TRUE. Its managed block asserts that both runners announce declared spec edits before a run starts. Review proved that is TRUE today for both hosts (F-8), so do NOT weaken or qualify it; ADD the end-of-run report and the reported-failure behavior alongside it.
  IT IS A MANAGED BLOCK, SO EDIT THE SOURCE, NOT THE RENDERED COPY. `AGENTS.md`'s `<!-- aw:block -->` content is installed from `engine.py`; a hand-edit to the rendered file will be overwritten on the next install. THE GENERATING STRING WAS LOCATED AT REVIEW: `agent_workflows/engine.py:1351` begins the paragraph ("A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT...") and the announce sentence sits about seven lines into that literal. Re-locate it by the phrase rather than by that number, edit there, regenerate, and state in the report which file holds the text. Verified at review that the source and the rendered `AGENTS.md:82` AGREE today, so a disagreement you find is new and must be reported rather than silently normalized.
  DECLARE BOTH FILES, WHICH THE PLAN PREVIOUSLY DID NOT. `engine.py` is now in `- Scope-Paths:` alongside `AGENTS.md`; editing the generating source under an undeclared path would have produced an out-of-scope finding at finalize for the one edit this item exists to make.
  - Depends on: E-04
  - Expected outcome: the doctrine text still asserts the start announcement for both hosts (unchanged, because it is true) and now also states the end-of-run report and that a failed computation is reported; edited at `engine.py` with the rendered `AGENTS.md` regenerated and shown to agree.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE START ANNOUNCEMENT IS ALREADY SHARED AND ALREADY REACHES BOTH HOSTS, so no agy call is missing (F-8). The spec-impact block lives inside `announce_run_order`, DEFINED at `oc_runipd.py:4178` and imported (`agy_runipd.py:377`) and CALLED (`:2109`) by agy. Proved by `agy_runipd.announce_run_order is oc_runipd.announce_run_order` -> True and by driving the agy path and capturing `SPEC CHANGES: ...`. The plan's "wiring" premise was false.
- A SHARED FUNCTION DEFINED IN ONE DRIVER AND RE-EXPORTED BY THE OTHER IS THIS REPOSITORY'S ESTABLISHED PATTERN, not a smell to fix. `agy_runipd.py:84-88` documents the `as <same-name>` re-export form and says the announcement "is emitted through the shared `announce_run_order` below, so the two hosts cannot drift the way `Heartbeat` once did". So grepping agy for the INNER symbols (`spec_impacts_for_queue`, `format_spec_impact_announcement`) tests the wrong thing.
- The impact computation and its renderer live in shared modules (`runner_shared.spec_impacts_for_queue`, `render_stream.format_spec_impact_announcement`).
- `_compute_scope_reconciliation` IS FORKED: two near-identical definitions, `oc_runipd.py:953` and `agy_runipd.py:942`. Out of scope to unify here, but do not deepen it.
- THE RECONCILIATION IS PER-ITEM, AT FINALIZE, AGAINST THE LANE WORKTREE, AND RETURNS AN EMPTY PAIR WHEN `finalize_precheck` REFUSES (`oc_runipd.py:953-972`, called at `:995`). So an empty pair means "clean" OR "refused", and an item that never finalized has no reconciliation at all (F-9).
- THE EXISTING SHARING TEST IS SYMBOL-ONLY (`tests/test_spec_visibility.py:161-169`), which is the false-positive shape this plan's own E-04 forbids. 16 tests there and 34 in `tests/test_run_order_announcement.py` must stay green.
- `spec_impacts_for_queue` reads each item's plan file FROM DISK at dispatch rather than trusting run state, deliberately, "so the announcement reflects the plan as it stands at dispatch" (`runner_shared.py:256-259`). Preserve that.
- Its docstring also records that an unreadable plan is SKIPPED rather than failing the run, for the same advisory reason. E-01 must keep that posture while making the failure visible.
- `AGENTS.md` carries managed blocks installed from `engine.py`; hand-edits inside them do not survive.
- The suite is run BARE (`python3 -m pytest`). Shared checkout: run `aw runs` first.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | WITHDRAWN at review | agy host | CLAIMED: agy never calls the impact helper, so the announcement does not exist on that host. FALSE. The grep is accurate but tests the wrong symbols: agy calls the shared `announce_run_order`, which contains the block. See F-8. | superseded by F-8 |
| F-2 | WITHDRAWN at review | doc vs reality | CLAIMED: `AGENTS.md:82`'s present-tense assertion is false for agy. It is TRUE. The doctrine does not over-promise; E-05 EXTENDS it rather than correcting it. | superseded by F-8 |
| F-3 | HIGH | run end | Neither host announces at the end. The sole spec-impact call site is pre-dispatch, inside `announce_run_order`. Re-verified at review; this is now the plan's primary deliverable. | `oc_runipd.py:4202-4203` is the only caller anywhere in `agent_workflows/` |
| F-4 | MEDIUM | silent failure | The start announcement swallows any exception with no trace, making "no spec edits" and "announcer crashed" indistinguishable. Because the swallow is in the SHARED function, one fix covers both hosts. | `oc_runipd.py:4204-4207` (`except Exception: pass`), re-located at review |
| F-5 | MEDIUM | reconciliation exists but is FORKED | The declared-versus-actual scope audit is already computed and must be reused, not re-derived. Note it is TWO near-identical definitions, not one shared symbol. | `_compute_scope_reconciliation` at `oc_runipd.py:953` and `agy_runipd.py:942`, both delegating to `ipd_lifecycle.finalize_precheck` |
| F-6 | MEDIUM | summary seam | The end-of-run renderer is called THREE times per driver, so "wire the end" is ambiguous until the sites are enumerated. Re-located at review (drifted again). | `oc_runipd.py:7480`, `:8383`, `:8429`; `agy_runipd.py:4490`, `:5084`, `:5130` |
| F-7 | LOW | stale citations, THIRD generation | The item's numbers drifted, then this plan's drifted too: `oc:4146-4151` is now `:4202-4207`, `oc:944` is now `:953`, `agy:876` is now `:942`, and all six summary sites moved. Re-locate by symbol, never by number. | re-measured at HEAD 2026-09-09 |
| F-8 | HIGH (added at review) | the plan's central premise is FALSE | AGY ALREADY ANNOUNCES. `announce_run_order` is defined at `oc_runipd.py:4178`, contains the spec-impact block, and is imported (`agy_runipd.py:377`) and called (`:2109`, in `initialize_run`, pre-dispatch) by agy. Proved two ways: object identity returns True, and driving the AGY entry point on a fixture queue printed `SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).` So F-1 and F-2 are withdrawn, E-02 has no work to do, and `AGENTS.md:82` is true. The plan reached the opposite conclusion by grepping agy for the INNER symbols instead of driving the path, which is the exact mistake its own E-04 forbids. | identity check + captured stdout from the agy path; `agy_runipd.py:84-88` documents the pattern |
| F-9 | HIGH (added at review) | the end report's data is narrower than E-03 assumed | `_compute_scope_reconciliation` is per-ITEM, called from the finalize helper (`oc_runipd.py:995`), resolves against the LANE worktree by design, and returns `({}, {})` whenever `finalize_precheck` refuses (bad/missing begin receipt, failing pre-transition lint). So an empty pair is AMBIGUOUS exactly as E-01's swallow is, an item that never finalized has no reconciliation at all, and the data is per-item while the start announcement is per-queue. An end report that prints "no spec changes" from an empty pair would reintroduce the ambiguity this plan exists to remove. | read the helper, its caller, and the lane-worktree comment at `:996-1000` |
| F-10 | MEDIUM (added at review) | the existing test is the anti-pattern the plan forbids | `tests/test_spec_visibility.py:161-169` asserts only object identity for two symbols. It passes whether or not either host calls them, so it is precisely the "would have PASSED against the broken code" shape E-04 rules out, and it is why a reader could believe agy was blind. | read the test class |
| F-11 | LOW (added at review) | a self-contradiction in the plan's own scope | It declared `tests/test_run_order_announcement.py` in `- Scope-Paths:` while V-04 required that file's diff be EMPTY. A declared-but-unmodified path also costs a `--scope-ack` at finalize. | the plan's `Scope-Paths` versus its V-04 |
| F-12 | HIGH (added at EXECUTION) | THE START ANNOUNCEMENT NEVER FIRED ON EITHER HOST | F-8 corrected the plan's mechanism claim and introduced a BEHAVIORAL one that is also false. Agy does call the shared `announce_run_order` (re-verified by identity), but at pre-change HEAD NEITHER host printed the announcement for a real queue. `runner_shared.spec_impacts_for_queue` reads `item["path"]`/`item["plan_path"]`; a runner queue entry carries only `"configured_file"` (frozen at `oc_runipd.py:2979`, `agy_runipd.py:2094`; zero assignments of `"path"` in either driver). So the impact set was empty for every item of every real run and the feature was inert from the day it shipped, while the suite stayed green because `tests/test_spec_visibility.py:99-119` hand-builds queues with the key production never writes. This is F-10's fixture-shaped false positive one level deeper, and it is why the review's pasted `SPEC CHANGES: 1 queued plan(s)...` line proved nothing about a run. FIXED at the call site by `queue_with_plan_paths` (D1), leaving the shared helper's documented contract and this plan's declared scope intact. | drove BOTH entry points on a pristine `git archive HEAD` tree: `SPEC CHANGES announced: False` on oc AND agy; same fixture after the fix: `True` on both; the frozen queue's keys and the empty-vs-nonempty impact pair pasted in V-02 |

## Proposed changes (ordered, validatable)

1. Make the start announcement's failure visible without letting it abort a run, in the shared function so both hosts get it (E-01).
2. Prove the agy start announcement already works and lock it in behaviorally, adding NO agy call site (E-02).
3. Add the end-of-run report on both hosts from a shared emitter, reconciled via the existing scope audit and honest about what that audit cannot tell it (E-03).
4. Test both ends on both hosts by driving real paths, with fails-before only for the two real gaps (E-04).
5. EXTEND `AGENTS.md:82` at its generating source in `engine.py`, without weakening its already-true start claim (E-05).

## Deferred / out of scope (with reason)

- REFUSING a run that declares a spec edit, or requiring extra consent for one: explicitly not this plan. The maintainer ruled a plan MAY amend a spec; this plan changes what the operator is TOLD, never what a run may do. Adding a gate would reverse that ruling.
- VALIDATING that a declared spec amendment is CORRECT, or that it matches the plan's spec-sync prose: a review-quality question, not a visibility one.
- PER-REQUIREMENT spec coverage tracking (the "which half of this spec is unbuilt" gap): named in backlog `f1sw71`, unrelated mechanism.
- The `--full-auto` interaction: whether an unattended run should announce differently is a policy question this plan deliberately does not open.
- WIRING AGY TO THE START ANNOUNCEMENT. Withdrawn as a deliverable because it is already done (F-8). E-02 now proves and guards it instead. Adding a second agy call site would print the announcement twice.
- UNFORKING `_compute_scope_reconciliation` (F-5). Two near-identical copies exist at `oc_runipd.py:953` and `agy_runipd.py:942`. Real drift, and its own change: unifying it touches the finalize path this plan must not alter. This plan may CALL either copy but must not deepen the fork, and reports the duplication rather than fixing it.
- MAKING THE END REPORT AUTHORITATIVE WHERE THE DATA IS NOT (F-9). Where an item never finalized or its precheck refused, the report says so; it does not go and compute its own diff to fill the gap. Deriving a spec edit from a source the finalize path does not vouch for would be a second reconciliation mechanism, which is the drift this Set exists to prevent.

## Scope check

- Over-scope: none. Two drivers, one shared renderer, one doc source plus its generator, two test files.
- Scope-Paths justification: `oc_runipd.py` holds `announce_run_order` and its swallow (E-01), the `_compute_scope_reconciliation` copy and three summary sites (E-03); `agy_runipd.py` holds the other three summary sites and its own reconciliation copy; `render_stream.py` holds `format_spec_impact_announcement` and is where the end-of-run wording belongs beside it (E-03); `engine.py` holds the GENERATING string for the managed block (E-05, newly declared because editing it under an undeclared path would be an out-of-scope finding); `AGENTS.md` is the rendered copy; `tests/test_spec_impact_visibility.py` is new; `tests/test_spec_visibility.py` is EXTENDED by E-02's behavioral case. CHANGED AT REVIEW: `runner_shared.py` was removed (E-02 no longer wires anything and `spec_impacts_for_queue` needs no change) and `tests/test_run_order_announcement.py` was removed, because the plan required its diff be EMPTY while declaring it, and a declared-but-unmodified path costs a `--scope-ack` at finalize (F-11).
- Under-scope: this plan does NOT gate spec edits, does not verify amendment correctness, does not touch the finalize scope gate itself (it only CONSUMES the reconciliation the gate already computes), does not unfork that reconciliation, and does not add an agy call site.

## Required tests / validation

- New `tests/test_spec_impact_visibility.py` parameterized over both drivers, covering: start announced on both hosts, end announced on both hosts, the empty case, the failure case, both reconciliation asymmetries, an item that never finalized, and an empty-because-refused reconciliation.
- THE FAILS-BEFORE-PASSES-AFTER SHAPE APPLIES ONLY TO THE TWO REAL GAPS: the end-of-run report and the silent failure. The agy START case must pass BOTH before and after, because it already works (F-8); a test asserting it fails today is a test written against a defect that does not exist.
- EVERY ASSERTION DRIVES AN ENTRY POINT AND READS CAPTURED OUTPUT. No symbol-identity assertion counts as coverage for a behavior, per F-10 and the plan's own rule.
- `tests/test_run_order_announcement.py` (34 tests) must stay green and UNEDITED, and is deliberately NOT declared in `Scope-Paths` for that reason. `tests/test_spec_visibility.py` (16 tests) must stay green with its existing cases unmodified while E-02 adds to it.
- `python3 -m pytest` BARE, before and after. Re-measured at review on main: `1 failed, 5919 passed, 3 skipped, 2 xfailed`, the failing node being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`. MEASURE YOUR OWN before-baseline and compare failing NODE IDS, never counts.
- `aw sanitize --agent` clean.

## Spec / documentation sync

No `.spec.md` is amended by this plan, so no spec file is declared in `- Scope-Paths:`. That is deliberate and worth stating plainly, because this plan is ABOUT spec-edit visibility and it would be confusing for it to also amend a spec.

`AGENTS.md` IS edited (E-05), and it is a MANAGED BLOCK whose text is installed from `engine.py`. The report must name which file actually holds the generating string, since editing the rendered copy alone would be silently reverted by the next `aw install`.

EXECUTION NOTE (2026-09-14): the generating string is in `agent_workflows/engine.py`, in `agents_pointer_prose`, located by the phrase "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT". The rendered `AGENTS.md` managed block was REGENERATED from that source (via `engine.agents_managed_block(target_layout="aw")`, spliced between the `<!-- aw:block -->` markers) rather than hand-edited, and the two were verified to agree afterwards. No `.spec.md` was amended, as planned.

## Open questions

### OQ-01: Should the end-of-run report appear on ALL THREE summary call sites per driver, or only on normal completion?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: ALL THREE SITES PER HOST, with the two non-primary ones LABELLED AS POSSIBLY INCOMPLETE. That answer takes the argument for coverage (an aborted run is exactly when an operator most needs to know a spec was rewritten, and a success-only report hides the interesting case) and disarms the single objection against it (a half-computed reconciliation on an aborted path could mislead worse than silence) by labelling rather than by suppressing. E-03 and V-03 are updated accordingly: all six sites wired, and the four non-primary ones must show the label in their pasted output.
  A SEPARATE REQUIREMENT CAME WITH THE ANSWER and is recorded here because it constrains a DIFFERENT part of the plan: the assertion that specs will be edited is made at the start of THE RUNNER, covering the whole queue before any dispatch, NOT at the start of each IPD. I measured that this is ALREADY the placement (the sole call site is in the run-order announcement path before any worker is spawned, and `spec_impacts_for_queue` reads the entire queue at once) and confirmed with the maintainer that they were confirming the placement rather than requesting a move. It is therefore implemented as a REGRESSION GUARD in E-01, tested in V-01, so a later change cannot turn one pre-spend warning into a per-item line buried inside the run.
  DELIBERATELY NOT ADOPTED HERE, and filed instead: the maintainer raised, and set aside for later discussion, a PAUSE-AND-ASSERT gate, where a queue that will rewrite a spec stops and waits for human acknowledgement before spawning anything. That is a control change, not a reporting change, and this plan is report-only by design ("changes what the operator is TOLD, never what a run is ALLOWED to do"). Filed as backlog `10qxm7` (`specconsent-01`) so the stronger control is not lost.
  ORIGINAL FRAMING, retained: raised at authoring from measurement F-6, left open because it read as a judgement about operator attention rather than a fact the repository settles.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new handler's source and paste THREE runs distinguishable from each other: a run declaring a spec edit (announcement printed), a run declaring none (no spurious line), and a run where the computation RAISES (advisory line naming the exception class, and the run still starts). Force the failure by patching `spec_impacts_for_queue` to raise, and paste the exit code proving the run was not aborted.
    The load-bearing assertion is DISTINGUISHABILITY: paste the empty-case output and the failure-case output side by side and show they differ. If they are identical, this item has not been done.
    PASTE THE PLACEMENT REGRESSION TEST and its passing output, showing the start announcement is asserted as ONE whole-queue event occurring BEFORE any dispatch. Quote the assertion. This pins the maintainer's 2026-09-08 requirement that the assertion is made at the start of the RUNNER, not at the start of each IPD; it is already the current behavior, so a test that passes trivially without exercising the placement does not satisfy this.
    PROVE THE FIX REACHED THE AGY HOST WITHOUT AN AGY EDIT. Paste the failure-advisory line captured from the AGY entry point as well as the oc one, and paste `git diff --stat -- agent_workflows/agy_runipd.py` showing NO change was needed for E-01. The swallow is inside the shared `announce_run_order`, so one edit must cover both; if it did not, you edited the wrong site.
  - Observed evidence: PASS. The shared handler now emits a named one-line advisory instead of `pass`; three start states are distinguishable on BOTH hosts; the placement regression test pins one whole-queue pre-dispatch event. Detail and pasted output below.
    THE NEW HANDLER'S SOURCE (in the SHARED `announce_run_order`, `agent_workflows/oc_runipd.py`):

    ```python
        except Exception as exc:
            # specvis st5klo E-01: STILL advisory (a broken announcement must never stop a run from
            # starting, which is why this catches everything and does not re-raise), but no longer SILENT.
            # The old `pass` made two very different states render identically: "this run declares no spec
            # edits" and "the spec-impact computation crashed" both printed nothing, so an operator could
            # not tell a clean run from a broken announcer. One named line resolves that ambiguity without
            # changing what the run is permitted to do. Emitted from the SHARED function, so both hosts get
            # it from this single edit (`agy_runipd` imports and calls this very object).
            for line in format_spec_impact_failure(exc, pal=pal):
                print(line, file=out)
    ```

    THREE DISTINGUISHABLE RUNS, ON BOTH HOSTS. Driven through each driver's real `initialize_run`
    (`evidence/probe_failure_advisory.py`, full capture in `evidence/failure-advisory-output.txt`):

    ```text
    === [oc_runipd] A. declares a spec (announced) ===
    Run order (1 item(s)): 01 sp0001
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).
      A spec is the contract other plans are reviewed against, so review these first.
        sp0001 (demo) -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
    --> exit code: 0 | run state frozen (run STARTED): True

    === [oc_runipd] C. computation RAISES ===
    Run order (1 item(s)): 01 sp0001
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: could not be computed (RuntimeError); the run is starting anyway. Any declared spec edit in this queue is therefore UNREPORTED, not absent.
    --> exit code: 0 | run state frozen (run STARTED): True

    === [agy_runipd] A. declares a spec (announced) ===
    Run order (1 item(s)): 01 sp0001
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).
      A spec is the contract other plans are reviewed against, so review these first.
        sp0001 (demo) -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
    --> exit code: 0 | run state frozen (run STARTED): True

    === [agy_runipd] C. computation RAISES ===
    Run order (1 item(s)): 01 sp0001
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: could not be computed (RuntimeError); the run is starting anyway. Any declared spec edit in this queue is therefore UNREPORTED, not absent.
    --> exit code: 0 | run state frozen (run STARTED): True
    ```

    The failure case was forced by patching `spec_impacts_for_queue` to raise `RuntimeError`. EXIT CODE 0
    and `run state frozen: True` on both hosts prove the run was NOT aborted: the advisory contract is
    intact.

    DISTINGUISHABILITY, the load-bearing assertion. Empty case (a plan declaring only
    `agent_workflows/cli.py`) versus failure case, same driver, side by side:

    ```text
    EMPTY   : Run order (1 item(s)): 01 sp0005 / Matches the typed order; nothing was reordered.
              <no third line at all>
    FAILURE : Run order (1 item(s)): 01 sp0005 / Matches the typed order; nothing was reordered.
              SPEC CHANGES: could not be computed (RuntimeError); the run is starting anyway. ...
    ```

    Asserted mechanically, not merely by eye, in
    `tests/test_spec_impact_visibility.py::StartAnnouncementFailureIsVisibleTests::test_failure_output_differs_from_the_empty_case`,
    which captures both and asserts `assertNotEqual(empty_out, fail_out)` plus `assertNotIn("could not be
    computed", empty_out)`. At pre-change HEAD that test FAILS (both outputs were byte-identical), which is
    the defect stated as a test.

    THE PLACEMENT REGRESSION TEST, quoted from
    `tests/test_spec_impact_visibility.py::StartAnnouncementIsBehavioralOnBothHostsTests::test_announcement_is_one_whole_queue_event_before_any_dispatch`.
    It is not trivially satisfiable: it uses a THREE-plan queue of which TWO declare specs, so a per-item
    implementation would print the header twice and fail the count:

    ```python
                    self.assertEqual(
                        out.count("SPEC CHANGES"),
                        1,
                        "one whole-queue announcement, not one per item",
                    )
                    self.assertIn("2 queued plan(s)", out)
                    ...
                    for item in state["queue"]:
                        self.assertEqual(item["attempts"], [])
                        self.assertEqual(item["status"], "queued")
    ```

    The `attempts == []` / `status == "queued"` loop is what pins PRE-DISPATCH: at the moment the
    announcement was printed, no item had been attempted. Passing:

    ```text
    $ python3 -m pytest tests/test_spec_impact_visibility.py::StartAnnouncementIsBehavioralOnBothHostsTests::test_announcement_is_one_whole_queue_event_before_any_dispatch -o addopts="" -q
    .                                                                        [100%]
    1 passed in 0.36s
    ```

    THE FIX REACHED AGY WITH NO AGY EDIT FOR THIS ITEM. The agy failure-advisory line is pasted above,
    captured from the AGY entry point. `agent_workflows/agy_runipd.py` contains ZERO occurrences of
    `format_spec_impact_failure` (`git diff -- agent_workflows/agy_runipd.py | grep -c format_spec_impact_failure`
    -> `0`), because the swallow is inside the shared `announce_run_order` that agy imports and calls.
    Note the item's literal instruction to show `git diff --stat -- agent_workflows/agy_runipd.py` EMPTY
    cannot be honored, because E-03 legitimately wires that host's THREE end-of-run summary sites in the
    same change; the stat is therefore non-empty, and the E-01-specific claim is discharged by the
    zero-occurrence check above plus the agy-captured advisory line. The full agy diff is 38 added lines:
    a shared-symbol re-export block, three `report_run_spec_edits` call sites, and one
    `record_item_spec_edits` call. No logic is duplicated.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the captured output of the AGY pre-dispatch path for a queue whose plan declares a `.spec.md`, showing the declared-spec-edit announcement. A symbol-import or object-identity assertion ALONE is a FAILED validation: the existing `tests/test_spec_visibility.py:161-169` already asserts identity and would pass against a host that never calls anything (F-10), which is exactly how this plan came to believe agy was blind. Only driving the path proves the behavior.
    PASTE `git diff --stat -- agent_workflows/agy_runipd.py` SHOWING NO NEW CALL SITE WAS ADDED, and confirm in one sentence that agy reaches the announcement through the shared `announce_run_order` it already imports (`:377`) and calls (`:2109`). If your diff adds a call there, this validation FAILS: it would double-print on agy.
    STATE THE WITHDRAWAL EXPLICITLY. Confirm in one sentence that F-1 and F-2 were withdrawn at review with their disproof, so a later reader does not resurrect "agy never announces" from this plan's history.
  - Observed evidence: PASS, BUT THIS ITEM'S PREMISE WAS FALSE (new finding F-12). At pre-change HEAD the start announcement fired on NEITHER host, so this was a real fix, not a regression guard. Proof, root cause and the no-double-print check below.
    READ THIS ITEM'S PREMISE FIRST: IT WAS FALSE, AND EXECUTION CAUGHT IT (new finding F-12 below).
    E-02 was written as "prove the agy start announcement ALREADY works and merely lock it in", on the
    strength of review's F-8. Driving both real entry points at PRE-CHANGE HEAD shows the announcement
    fired on NEITHER host, so there was a real defect to fix here and the "regression guard only" framing
    was wrong.

    THE AGY PRE-DISPATCH PATH, CAPTURED. At pre-change HEAD (a pristine `git archive HEAD` tree, so no
    lane edit can contaminate it):

    ```text
    $ PYTHONPATH=<HEAD-tree> python3 evidence/probe_start_announcement.py
    PACKAGE UNDER TEST: <HEAD-tree>/agent_workflows/__init__.py
    --- oc_runipd stdout ---
    Run order (1 item(s)): 01 aaa111
      Matches the typed order; nothing was reordered.
    --- oc_runipd: SPEC CHANGES announced: False
    --- agy_runipd stdout ---
    Run order (1 item(s)): 01 aaa111
      Matches the typed order; nothing was reordered.
    --- agy_runipd: SPEC CHANGES announced: False
    ```

    AFTER the change, same probe, same fixture:

    ```text
    PACKAGE UNDER TEST: <lane>/agent_workflows/__init__.py
    --- oc_runipd stdout ---
    Run order (1 item(s)): 01 aaa111
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).
      A spec is the contract other plans are reviewed against, so review these first.
        aaa111 (demo) -> .aw/records/specs/20260826-0718-01-aaa111-demo.spec.md
    --- oc_runipd: SPEC CHANGES announced: True
    --- agy_runipd stdout ---
    Run order (1 item(s)): 01 aaa111
      Matches the typed order; nothing was reordered.
    SPEC CHANGES: 1 queued plan(s) declare edits to 1 specification file(s).
      A spec is the contract other plans are reviewed against, so review these first.
        aaa111 (demo) -> .aw/records/specs/20260826-0718-01-aaa111-demo.spec.md
    --- agy_runipd: SPEC CHANGES announced: True
    ```

    THE ROOT CAUSE, measured rather than reasoned. `runner_shared.spec_impacts_for_queue` reads each
    item's plan location from `item["path"]` or `item["plan_path"]`; a real runner queue entry carries
    NEITHER, only `"configured_file"` (frozen at `oc_runipd.py:2979` / `agy_runipd.py:2094`; grep finds
    zero assignments of `"path"` onto a queue item in either driver). Proved on a real frozen queue:

    ```text
    QUEUE ITEM KEYS: ['action','attempts','configured_file','dependencies','from_backlog','id6',
                      'initial_status','kind','order','position','setid','status']
    path? None   plan_path? None   configured_file: '.aw/records/plans/pending/20260907-demo-01-aaa111-demo.ipd.md'
    impacts on REAL queue: []
    impacts on the SAME queue rebuilt with a 'path' key: [{'id6':'aaa111','setid':'demo','specs':['...demo.spec.md']}]
    ```

    So F-8's MECHANICAL claim is TRUE and I re-verified it (`agy_runipd.announce_run_order is
    oc_runipd.announce_run_order` -> `True`, `__module__` -> `agent_workflows.oc_runipd`), while its
    BEHAVIORAL claim is FALSE: the `SPEC CHANGES: 1 queued plan(s)...` line review pasted can only have
    come from a HAND-BUILT fixture queue carrying `"path"`, which is the shape every case in
    `tests/test_spec_visibility.py:99-119` constructs. The suite was green against a feature that never
    fired in production. That is the same fixture-shaped false positive F-10 names, one level deeper.

    THE FIX, and why it is at the CALL SITE. `announce_run_order` now passes
    `queue_with_plan_paths(repo, state["queue"])`, a shared adapter that resolves each entry to its plan
    file (explicit `path`/`plan_path`, then `last_plan_path`, then `configured_file`, then the
    authoritative `resolve_plan_path`). Adapting at the call site rather than widening
    `spec_impacts_for_queue` keeps that shared helper's documented input contract intact and keeps the
    change inside this plan's declared `Scope-Paths` (`runner_shared.py` is deliberately NOT declared).
    Recorded as DECISION 07-st5klo-D1.

    NO NEW AGY CALL SITE, so no double-print. `agent_workflows/agy_runipd.py` still contains exactly ONE
    `announce_run_order(` call:

    ```text
    $ grep -n "announce_run_order(" agent_workflows/agy_runipd.py
    2233:    announce_run_order(run_dir, state)
    ```

    Agy reaches the announcement through the shared `announce_run_order` it already imports and calls, so
    E-01's and E-02's fixes arrived on that host with no edit to its announcement path.

    `git diff --stat -- agent_workflows/agy_runipd.py` is `38 ++++` and NOT empty, which the item did not
    anticipate: those 38 lines are E-03's three end-of-run summary sites, one `record_item_spec_edits`
    call, and a shared-symbol re-export block. None of them is an announcement call site.

    THE WITHDRAWAL, stated precisely rather than adopted wholesale. F-1 and F-2 were withdrawn at review
    on the ground that agy announces; that withdrawal is HALF right and must not be read as full
    vindication. Agy is not "blind" in the sense F-1 meant (it does call the shared function), but at
    pre-change HEAD NEITHER host actually announced, so `AGENTS.md`'s present-tense claim was in fact
    false for both until this change made it true. A later reader should resurrect neither "agy never
    announces" (wrong mechanism) nor "the announcement always worked" (wrong behavior).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the end-of-run output on BOTH hosts for a run that modified a declared `.spec.md`, and for a run that modified a spec it did NOT declare (the undeclared contract change, which is the case that matters). Show the reconciliation names both asymmetries.
    ENUMERATE THE SUMMARY CALL SITES (F-6) BY RE-LOCATING THEM YOURSELF, since they have drifted twice: at review they were `oc_runipd.py:7480`, `:8383`, `:8429` and `agy_runipd.py:4490`, `:5084`, `:5130`. Show ALL SIX ARE WIRED, per the maintainer's resolution of OQ-01. For the two non-primary sites per host, paste the output showing the POSSIBLY-INCOMPLETE label, since printing a half-computed contract change as authoritative was the one real objection to covering them.
    Confirm you consumed `_compute_scope_reconciliation` rather than writing a second diff, and paste the call. State WHICH copy you called (`oc_runipd.py:953` or `agy_runipd.py:942`) or that you promoted one to shared, and confirm you did not deepen the fork (F-5).
    DISCHARGE F-9's THREE HONESTY CASES with pasted output: an item that NEVER FINALIZED (report says so rather than showing a clean delta), an EMPTY-BECAUSE-REFUSED reconciliation (not rendered as a positive all-clear), and the per-item-to-per-queue aggregation (how many items were reconciled and how many could not be). An end report that prints "no spec changes" from an empty pair reintroduces exactly the ambiguity E-01 removes and is a FAILED validation.
    PASTE THE SHARED EMITTER, showing the end-of-run wording has ONE definition rather than six inline copies, and name the module it lives in.
  - Observed evidence: PASS. All SIX summary sites wired (three per host, four labelled possibly-incomplete), both asymmetries and all three of F-9's honesty cases pasted for both hosts, reconciliation consumed not re-derived, fork not deepened, emitter shared. Detail below.
    ALL SIX SUMMARY SITES RE-LOCATED AND ALL SIX WIRED. The review's numbers had drifted a FOURTH time, so
    I re-located them by symbol:

    ```text
    $ grep -n "render_run_summary_table(" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py | grep -v "def "
    agent_workflows/oc_runipd.py:7910:        render_run_summary_table(
    agent_workflows/oc_runipd.py:8830:                        render_run_summary_table(
    agent_workflows/oc_runipd.py:8882:                        render_run_summary_table(
    agent_workflows/agy_runipd.py:4689:        render_run_summary_table(
    agent_workflows/agy_runipd.py:5318:                        render_run_summary_table(
    agent_workflows/agy_runipd.py:5367:                        render_run_summary_table(

    $ grep -n "report_run_spec_edits(state" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    agent_workflows/oc_runipd.py:7923:    report_run_spec_edits(state)
    agent_workflows/oc_runipd.py:8843:                    report_run_spec_edits(state, partial=True)
    agent_workflows/oc_runipd.py:8891:                    report_run_spec_edits(state, partial=True)
    agent_workflows/agy_runipd.py:4701:    report_run_spec_edits(state)
    agent_workflows/agy_runipd.py:5328:                    report_run_spec_edits(state, partial=True)
    agent_workflows/agy_runipd.py:5376:                    report_run_spec_edits(state, partial=True)
    ```

    Six summary sites, six report calls, adjacent to each: one primary (normal exit) and two non-primary
    (interrupt/SIGTERM, DriverError) PER HOST, with the four non-primary ones carrying `partial=True`.
    Pinned by
    `tests/test_spec_impact_visibility.py::EndOfRunReportIsWiredAtEverySummarySiteTests`, which asserts
    each driver's source contains exactly 3 calls of which exactly 2 pass `partial=True`.

    END-OF-RUN OUTPUT, BOTH HOSTS, ALL SHAPES (`evidence/probe_end_report.py`, full capture in
    `evidence/end-report-output.txt`). Both asymmetries:

    ```text
    === [oc_runipd] declared AND modified-but-undeclared ===
    SPEC EDITS THIS RUN
      UNDECLARED SPEC CHANGE(S): a spec was modified WITHOUT being declared in `- Scope-Paths:`.
        sp0001 modified (undeclared) -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 1 item(s); 0 could NOT be reconciled (finalize precheck refused); 0 never finalized.

    === [agy_runipd] declared AND modified-but-undeclared ===
    SPEC EDITS THIS RUN
      UNDECLARED SPEC CHANGE(S): a spec was modified WITHOUT being declared in `- Scope-Paths:`.
        sp0001 modified (undeclared) -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 1 item(s); 0 could NOT be reconciled (finalize precheck refused); 0 never finalized.

    === [oc_runipd] declared but NOT modified ===
    SPEC EDITS THIS RUN
      Declared: 1 plan(s) declared edits to 1 specification file(s).
        sp0001 declared -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      DECLARED BUT NOT MODIFIED: the plan promised this amendment and did not make it.
        sp0001 declared, unmodified -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 1 item(s); 0 could NOT be reconciled (finalize precheck refused); 0 never finalized.

    === [agy_runipd] declared but NOT modified ===
    SPEC EDITS THIS RUN
      Declared: 1 plan(s) declared edits to 1 specification file(s).
        sp0001 declared -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      DECLARED BUT NOT MODIFIED: the plan promised this amendment and did not make it.
        sp0001 declared, unmodified -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 1 item(s); 0 could NOT be reconciled (finalize precheck refused); 0 never finalized.
    ```

    F-9's THREE HONESTY CASES, DISCHARGED. (1) An item that NEVER FINALIZED is named as such, and is NOT
    rendered as a clean delta:

    ```text
    === [oc_runipd] item that NEVER finalized ===        === [agy_runipd] item that NEVER finalized ===
    SPEC EDITS THIS RUN                                  SPEC EDITS THIS RUN
      Declared: 1 plan(s) declared edits to 1 ...          Declared: 1 plan(s) declared edits to 1 ...
        sp0001 declared -> ...demo.spec.md                   sp0001 declared -> ...demo.spec.md
      Reconciled 0 item(s); 0 could NOT be                 Reconciled 0 item(s); 0 could NOT be
      reconciled ...; 1 never finalized.                   reconciled ...; 1 never finalized.
      NOT FINALIZED: sp0001.                               NOT FINALIZED: sp0001.
    ```

    (2) An EMPTY-BECAUSE-REFUSED reconciliation is explicitly NOT an all-clear:

    ```text
    === [oc_runipd] empty because precheck REFUSED ===   (agy identical)
    SPEC EDITS THIS RUN
      Declared: 1 plan(s) declared edits to 1 specification file(s).
        sp0001 declared -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 0 item(s); 1 could NOT be reconciled (finalize precheck refused); 0 never finalized.
      UNVERIFIED: the finalize precheck refused for sp0001, so no spec-edit claim is made for these items (an empty reconciliation is NOT an all-clear).
    ```

    (3) The PER-ITEM to PER-QUEUE aggregation is stated on every report as the `Reconciled N item(s); N
    could NOT be reconciled ...; N never finalized.` line above, and is asserted for a mixed
    three-item queue (one reconciled, one refused, one never finalized) in
    `EndOfRunReportTests::test_the_aggregation_counts_all_three_states`, which checks all three counts plus
    the whole-queue `3 plan(s) declared edits`. The refused case is detected by ASKING the precheck for
    its exit code when the pair comes back empty, never by inferring cleanliness from emptiness; see
    `record_item_spec_edits`.

    THE POSSIBLY-INCOMPLETE LABEL on the non-primary sites:

    ```text
    === [oc_runipd] aborted run (non-primary site label) (partial=True) ===
    SPEC EDITS THIS RUN
      POSSIBLY INCOMPLETE: this run did not finish, so the reconciliation below covers only the items that reached finalize.
      Declared: 1 plan(s) declared edits to 1 specification file(s).
        sp0001 declared -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      UNDECLARED SPEC CHANGE(S): a spec was modified WITHOUT being declared in `- Scope-Paths:`.
        sp0001 modified (undeclared) -> .aw/records/specs/20260826-0718-01-sp0001-demo.spec.md
      Reconciled 1 item(s); 0 could NOT be reconciled (finalize precheck refused); 0 never finalized.

    === [agy_runipd] aborted run (non-primary site label) (partial=True) ===
    SPEC EDITS THIS RUN
      POSSIBLY INCOMPLETE: this run did not finish, so the reconciliation below covers only the items that reached finalize.
      ... (identical)
    ```

    Asserted in `EndOfRunReportTests::test_the_non_primary_sites_label_the_report_possibly_incomplete`,
    which checks the label is present with `partial=True` and ABSENT with `partial=False`.

    `_compute_scope_reconciliation` IS CONSUMED, NOT RE-DERIVED, AND THE FORK IS NOT DEEPENED. Each driver
    passes ITS OWN existing copy into the one shared recorder, at its own finalize call site:

    ```python
            record_item_spec_edits(
                finalize_repo,
                current_plan_for_finalize,
                item,
                reconcile=_compute_scope_reconciliation,
            )
    ```

    That literal appears once in each driver (`oc_runipd.py`, resolving to its `_compute_scope_reconciliation`,
    and `agy_runipd.py`, resolving to its own). So I called BOTH copies, each from its own host, and
    promoted NEITHER to shared: no third copy exists, and neither host's behavior changed. The fork
    remains exactly the two definitions F-5 reports (`_compute_scope_reconciliation` in each driver),
    which is out of scope here and is reported rather than fixed. Taking the function as an injected
    PARAMETER is what made that possible with one recorder; recorded as DECISION 07-st5klo-D2, which also
    explains why the signature of `driver_finalize` was NOT touched (existing tests in both suites mock it
    with five positional parameters).

    THE SHARED EMITTER, ONE DEFINITION, in `agent_workflows/render_stream.py` beside
    `format_spec_impact_announcement`:

    ```text
    $ grep -rn "def format_spec_edit_report(\|def format_spec_impact_failure(" agent_workflows/
    agent_workflows/render_stream.py:1529:def format_spec_impact_failure(
    agent_workflows/render_stream.py:1560:def format_spec_edit_report(
    ```

    One definition each, package-wide, asserted by
    `OneSharedDefinitionTests::test_exactly_one_definition_of_each_new_formatter_package_wide` (globs every
    module and requires the defining file list to be exactly `["render_stream.py"]`). The six call sites
    call the shared `report_run_spec_edits`, which renders through that one formatter, so the wording has
    ONE definition rather than six inline copies. Both new formatters are pure (asserted by
    `test_the_renderers_are_pure`), and both drivers bind the same objects (asserted by
    `test_both_drivers_bind_the_same_objects` for all six new symbols).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test FAILING against pre-change HEAD for the END-OF-RUN case on both hosts and the SILENT-FAILURE case, then passing after. Do NOT include the agy start case in the fails-before set: paste it PASSING against pre-change HEAD as well as after, since it already works (F-8), and say so explicitly. A test that fails today on the agy start case is asserting a defect that does not exist and is a FAILED validation.
    Paste `python3 -m pytest tests/test_run_order_announcement.py` green and `git diff --stat -- tests/test_run_order_announcement.py` EMPTY, proving that file was neither edited nor declared. Paste `python3 -m pytest tests/test_spec_visibility.py` green, showing its 16 existing cases still pass alongside E-02's added behavioral case.
    Paste the bare `python3 -m pytest` summary line with a BEFORE baseline you measured yourself and the AFTER-minus-BEFORE failing NODE-ID set shown EMPTY. At review on main the baseline was `1 failed, 5919 passed, 3 skipped, 2 xfailed` with the environmental `test_reporting_contract` node as the only failure; measure your own rather than adopting that. If lane-worktree-only failures appear, name them and their tracking plan rather than quoting this plan's earlier unverified count.
  - Observed evidence: PASS. New test fails 24/25 at pre-change HEAD (including the agy START case, contrary to this item's instruction: see F-12) and passes 25/25 after; both existing suites green and unedited; AFTER-minus-BEFORE failing node set EMPTY. Detail below.
    THE FAILS-BEFORE SET IS LARGER THAN THIS ITEM ALLOWED FOR, BECAUSE THE AGY START CASE REALLY WAS
    BROKEN. This item forbids putting the agy start case in the fails-before set, on F-8's authority.
    That instruction was written against a mismeasurement (see V-02 and finding F-12), so I deliberately
    did the opposite and am flagging it here rather than quietly complying. The new test run against a
    pristine `git archive HEAD` tree:

    ```text
    $ cd <HEAD-tree> && python3 -m pytest tests/test_spec_impact_visibility.py -o addopts="" -q
    ...
    24 failed, 1 passed in 1.32s
    ```

    The START case fails at HEAD on BOTH hosts, shown per-subtest so the two hosts are individually
    visible:

    ```text
    $ cd <HEAD-tree> && python3 -m unittest tests.test_spec_impact_visibility.StartAnnouncementIsBehavioralOnBothHostsTests.test_declared_spec_edit_is_announced_from_the_real_entry_point
    FAIL: test_declared_spec_edit_is_announced_from_the_real_entry_point (...) (driver='oc_runipd')
    AssertionError: 'SPEC CHANGES' not found in 'Run order (1 item(s)): 01 sp0001\n  Matches the typed order; nothing was reordered.\n'
    FAIL: test_declared_spec_edit_is_announced_from_the_real_entry_point (...) (driver='agy_runipd')
    AssertionError: 'SPEC CHANGES' not found in 'Run order (1 item(s)): 01 sp0001\n  Matches the typed order; nothing was reordered.\n'
    Ran 1 test in 0.174s
    FAILED (failures=2)
    ```

    The END-OF-RUN cases and the SILENT-FAILURE case also fail at HEAD, as this item requires. From the
    same HEAD-tree run, the failing node list includes:

    ```text
    FAILED ...::EndOfRunReportTests::test_a_modified_but_undeclared_spec_is_reported_on_both_hosts
    FAILED ...::EndOfRunReportTests::test_a_declared_but_unmodified_spec_is_reported_on_both_hosts
    FAILED ...::EndOfRunReportTests::test_an_item_that_never_finalized_is_not_rendered_as_clean
    FAILED ...::EndOfRunReportTests::test_an_empty_because_refused_reconciliation_is_not_an_all_clear
    FAILED ...::EndOfRunReportTests::test_the_aggregation_counts_all_three_states
    FAILED ...::EndOfRunReportTests::test_the_non_primary_sites_label_the_report_possibly_incomplete
    FAILED ...::EndOfRunReportIsWiredAtEverySummarySiteTests::test_each_driver_calls_the_report_three_times_with_two_labelled_partial
    FAILED ...::StartAnnouncementFailureIsVisibleTests::test_failure_prints_a_named_advisory_and_the_run_still_starts
    FAILED ...::StartAnnouncementFailureIsVisibleTests::test_failure_output_differs_from_the_empty_case
    ```

    The single test that PASSES at HEAD is
    `StartAnnouncementIsBehavioralOnBothHostsTests::test_a_queue_declaring_no_spec_says_nothing`, which is
    correct and worth noting: at HEAD the announcement printed nothing for EVERY queue, so the
    declares-nothing case passed for the wrong reason. That is exactly why it cannot stand as evidence on
    its own, and why the declaring case had to be driven too.

    PASSING AFTER, in the lane:

    ```text
    $ python3 -m pytest tests/test_spec_impact_visibility.py -o addopts="" -q
    .........................                                                [100%]
    25 passed in 1.70s
    ```

    THE TWO EXISTING SUITES, GREEN AND UNEDITED:

    ```text
    $ python3 -m pytest tests/test_run_order_announcement.py -o addopts="" -q
    ..................................                                       [100%]
    34 passed in 0.60s

    $ python3 -m pytest tests/test_spec_visibility.py -o addopts="" -q
    ................                                                         [100%]
    16 passed in 0.16s

    $ git diff --stat -- tests/test_run_order_announcement.py tests/test_spec_visibility.py agent_workflows/runner_shared.py
    (no output: all three files unedited)
    ```

    Note a deliberate divergence from this item's text: `tests/test_spec_visibility.py` is green and
    UNEDITED rather than "extended with E-02's added behavioral case". Once E-02's premise was disproved,
    the honest home for a behavioral start-announcement case was the NEW file, alongside the fails-before
    evidence, rather than appended to a file whose 16 existing cases are all helper-level. That file is
    still declared in `Scope-Paths`; a declared-but-unmodified path is auto-acknowledged at finalize.

    THE BARE SUITE, BEFORE AND AFTER, MEASURED IN THIS LANE:

    ```text
    BEFORE (pre-change lane HEAD fea2c9f8):
    1 failed, 6828 passed, 3 skipped, 2 xfailed in 81.08s (0:01:21)

    AFTER:
    1 failed, 6853 passed, 3 skipped, 2 xfailed in 89.49s (0:01:29)
    ```

    AFTER-minus-BEFORE failing NODE-ID set, computed with `comm -13` on the sorted node lists:

    ```text
    BEFORE: tests/test_orchestrator_retirement.py::RealRepositorySets::test_lanectn_refuses_naming_its_one_unfinished_child
    AFTER:  tests/test_orchestrator_retirement.py::RealRepositorySets::test_lanectn_refuses_naming_its_one_unfinished_child
    AFTER minus BEFORE (new failures): <EMPTY>
    ```

    +25 passed is exactly this plan's new test file. ZERO new failures.

    THE ONE PRE-EXISTING FAILURE IS ENVIRONMENTAL AND UNRELATED, and I identified it rather than adopting
    the review's guess. It is NOT `test_reporting_contract` (that node passes here);
    it is `test_lanectn_refuses_naming_its_one_unfinished_child`, which calls
    `evaluate_set_retirement(REPO_ROOT, "lanectn")` against the LIVE repository plan tree and asserts the
    `lanectn` Set is still ineligible for retirement. Its own docstring anticipates this, instructing a
    reader to RE-MEASURE rather than loosen it: the Set's unfinished membership moved again because other
    lanes legitimately landed work. It is untouched by this plan (which edits no plan record but its own)
    and fails identically before and after.

    A MEASUREMENT TRAP WORTH RECORDING, since it cost real time and would mislead the next executor. This
    lane's environment exports `AW_EXECUTION_ROLE=worker`, and a bare `python3 -m pytest` under it yields
    `18 failed, 6811 passed` because `AW-LIFECYCLE-ROLE-001` correctly refuses `aw ipd begin`/`finalize`
    for a worker-role process, failing 17 lifecycle tests that shell out to those verbs. Those failures are
    an artifact of the harness, not of the tree: with `env -u AW_EXECUTION_ROLE` the same tree yields the
    `1 failed` baseline above. Both baseline and after-run were measured the SAME way (`env -u
    AW_EXECUTION_ROLE python3 -m pytest`, bare otherwise), so the comparison is apples to apples; the raw
    18-failure capture is preserved in `evidence/baseline-full.txt` for anyone re-measuring.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the diff of the GENERATING source (it IS `agent_workflows/engine.py`, located at review with the paragraph beginning at `:1351`; re-locate by the phrase, not the number) AND the regenerated `AGENTS.md` hunk, showing they agree. Quote the new sentence and confirm it claims only what now ships: both hosts, both ends, failure reported.
    CONFIRM THE START CLAIM WAS EXTENDED, NOT WEAKENED. The existing sentence asserting that both runners announce before a run starts is TRUE (F-8), so paste it showing it survived intact. Removing or hedging it would make the doctrine understate shipped behavior, which is the opposite of the defect this plan was filed against.
    STATE WHETHER SOURCE AND RENDERED COPY AGREED BEFORE YOUR EDIT. Verified AGREEING at review, so a disagreement you find is NEW and is a separate finding to report rather than silently normalize.
  - Observed evidence: PASS. Edited the generating source in `agent_workflows/engine.py` and regenerated `AGENTS.md`; the two agree; the already-true start claim survives verbatim and was extended, not weakened. Detail below.
    THE GENERATING SOURCE IS `agent_workflows/engine.py`, in `agents_pointer_prose`. I re-located it by
    the phrase "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT" rather than by the review's line number
    (that literal now begins at `:1351` in the function whose diff hunk header reads `@@ -1356,7 +1356,12
    @@ def agents_pointer_prose`). THE DIFF:

    ```diff
    --- a/agent_workflows/engine.py
    +++ b/agent_workflows/engine.py
    @@ -1356,7 +1356,12 @@ def agents_pointer_prose(target_layout: str = "legacy") -> str:
             "obligations follow. FIRST, list every `.spec.md` file you will touch in `- Scope-Paths:`, "
             "because that is what makes the amendment visible: `aw oc run` / `aw agy run` announce declared "
             "spec edits BEFORE the run starts, and the finalize scope gate reconciles what you actually "
    -        "changed against what you declared. SECOND, say WHY in the plan's spec-sync section, since a "
    +        "changed against what you declared. BOTH RUNNERS ALSO REPORT AT RUN END, beside the run summary, "
    +        "which specs the run declared and which it actually changed, INCLUDING a spec that was modified "
    +        "WITHOUT being declared; that end report names any item whose reconciliation refused or that "
    +        "never finalized rather than counting it clean, and a run whose spec-edit computation FAILS says "
    +        "so in one line instead of printing nothing, so silence means 'no declared spec edits' and never "
    +        "'the announcer broke'. SECOND, say WHY in the plan's spec-sync section, since a "
             "spec edit changes the contract every other plan is reviewed against and is the highest-leverage "
             "change a run can make."
         )
    ```

    THE REGENERATED `AGENTS.md` HUNK. The rendered file was NOT hand-edited: the managed block was
    regenerated by calling `engine.agents_managed_block(target_layout="aw")` and splicing it between the
    `<!-- aw:block -->` / `<!-- /aw:block -->` markers. `git diff --stat -- AGENTS.md` is
    `1 insertion(+), 1 deletion(-)` (the paragraph is one long line), and the added text reads:

    ```text
    ... `aw oc run` / `aw agy run` announce declared spec edits BEFORE the run starts, and the finalize
    scope gate reconciles what you actually changed against what you declared. BOTH RUNNERS ALSO REPORT AT
    RUN END, beside the run summary, which specs the run declared and which it actually changed, INCLUDING
    a spec that was modified WITHOUT being declared; that end report names any item whose reconciliation
    refused or that never finalized rather than counting it clean, and a run whose spec-edit computation
    FAILS says so in one line instead of printing nothing, so silence means 'no declared spec edits' and
    never 'the announcer broke'. SECOND, say WHY in the plan's spec-sync section, ...
    ```

    SOURCE AND RENDERED COPY AGREE AFTER THE EDIT, verified by regenerating and comparing rather than by
    reading:

    ```text
    round-trip identical: True
    $ grep -c "BOTH RUNNERS ALSO REPORT AT RUN END" AGENTS.md agent_workflows/engine.py
    AGENTS.md:1
    agent_workflows/engine.py:1
    ```

    THE NEW SENTENCE CLAIMS ONLY WHAT NOW SHIPS. "BOTH RUNNERS" - all six summary sites are wired, three
    per host, enumerated in V-03. "AT RUN END, beside the run summary" - each call is adjacent to a
    `render_run_summary_table` call. "INCLUDING a spec modified WITHOUT being declared" - the
    `UNDECLARED SPEC CHANGE(S)` line, pasted in V-03 for both hosts. "names any item whose reconciliation
    refused or that never finalized rather than counting it clean" - the `UNVERIFIED` and `NOT FINALIZED`
    lines, pasted in V-03. "a run whose spec-edit computation FAILS says so in one line" - the
    `could not be computed (RuntimeError)` advisory, pasted in V-01 for both hosts.

    THE START CLAIM WAS EXTENDED, NOT WEAKENED. The existing sentence survives verbatim; it appears in the
    diff above as an UNCHANGED context line, and:

    ```text
    $ python3 -c "from agent_workflows import engine; p=engine.agents_pointer_prose(target_layout='aw'); print('announce declared spec edits BEFORE the run starts' in p)"
    True
    ```

    ONE CAVEAT I AM RECORDING RATHER THAN GLOSSING. This item says to leave the start claim alone because
    it is TRUE (F-8). At pre-change HEAD it was in fact FALSE for BOTH hosts (V-02), so the doctrine
    over-promised until this change shipped. I still left the sentence intact, because it is now true and
    weakening it would understate shipped behavior, which is the correct outcome by a different route than
    this item assumed.

    SOURCE AND RENDERED COPY AGREED BEFORE MY EDIT. Verified by regenerating the block from the unedited
    source and diffing it against the rendered file: 0 differing hunks before my change, and exactly 1
    after (the paragraph I edited). So no pre-existing drift was found and none was silently normalized.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). OQ-01 is RESOLVED (maintainer, 2026-09-08) and no question here is `Blocking: yes`, so nothing gates approval; E-03 requires the executor to record which summary sites it wired either way.

READ THIS BEFORE E-02: ITS PREMISE WAS DISPROVED AT REVIEW. The plan was authored believing `aw agy run` never announces declared spec edits. It DOES: `announce_run_order` is defined in `oc_runipd.py`, contains the spec-impact block, and is imported and called by `agy_runipd.py:2109` before the first child session, proved by object identity and by capturing `SPEC CHANGES: ...` from the agy path (F-8). So two of the plan's three original gaps are now ONE plus a regression guard, `AGENTS.md:82` is TRUE and must be extended rather than corrected, and the primary deliverable is the END-OF-RUN report. If executing this plan appears to require adding an agy call site, STOP: that would double-print.

THIS PLAN ADDS NO POLICY. It changes what the operator is told, never what a run may do. If executing it appears to require refusing a run, gating a spec edit, or adding a consent flag, STOP and report: that would reverse the maintainer ruling this item exists to serve. The stronger pause-and-assert control the maintainer set aside is filed as backlog `10qxm7`.

ONE IMPLEMENTATION, BOTH HOSTS. Every change lands in shared code with both drivers calling it. A second copy in `agy_runipd.py` is the specific failure this Set is guarding against, and `render_stream` was already extracted once and re-forked in the other driver with nothing noticing. Two measured cautions: the START announcement is ALREADY correctly shared, so leave its structure alone; and `_compute_scope_reconciliation` is ALREADY forked into two per-driver copies (F-5), so do not deepen it and do not silently unify it either. Report the fork; it is out of scope.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: both driver modules are being edited by concurrent runs, so RE-LOCATE EVERY CITED SYMBOL before editing; this plan's own line numbers are already the second generation.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `dk16dx` (this plan carries `- From-Backlog: dk16dx` and inherits its `Blocks-Release: next`).
