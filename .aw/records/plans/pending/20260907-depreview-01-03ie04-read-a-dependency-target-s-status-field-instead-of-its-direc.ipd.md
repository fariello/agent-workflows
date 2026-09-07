# IPD: Read a dependency target's status field instead of its directory so the review relaxation is reachable

- Date: 2026-09-07
- Kind: child
- Concern: `edge_satisfied` is correctly ACTION-AWARE for an `executed:` dependency and deliberately relaxes the requirement for a REVIEW turn (`oc_runipd.py:3316`, `:3339`): `is_exec = item.get("action") != "review"`, then `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")`. That is the right semantics, because a review writes no code and cannot be invalidated by an unexecuted prerequisite. But the relaxation is UNREACHABLE, because the value compared against `allowed` is a DIRECTORY NAME rather than the plan's `- Status:` field: `bucket = plan_bucket(dep_path)` (`:3338`), and `plan_bucket` (`runner_shared.py:1094-1108`) merely scans path components for one of a fixed list. In this repository readiness lives in the `- Status:` FIELD and a plan STAYS in `pending/` until a TERMINAL state moves it, so there are no `reviewed/` or `approved/` directories at all (verified: `.aw/records/plans/` holds only `executed`, `not-executed`, `pending`, `reusable`, `superseded`). Every non-terminal plan therefore buckets as `pending`, which is absent from `allowed`, and the review path refuses exactly as the execute path would.
  SO TWO OF THE THREE ALLOWED VALUES ARE DEAD CODE for every plan in this tree. The relaxation is real in intent and inert in practice.
  MEASURED 2026-09-07. `aw oc run --session <sid> ybkmzp`, where `ybkmzp` declares `- Item-Dependencies: executed:tm2cz8` and `tm2cz8` carries `- Status: reviewed` in `.aw/records/plans/pending/`, refused: `ybkmzp: dependency-blocked (executed:tm2cz8: external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here))`. The message names the three states it would accept and reports the one thing it read, which is a directory. `tm2cz8` satisfied the intended condition and was refused anyway. RE-REPRODUCED IN ISOLATION at review time in a throwaway repo, so the defect is pinned independently of this repository's state.
  THE FIX IS SMALL BECAUSE THE READER ALREADY EXISTS AND IS ALREADY IMPORTED. `selectors.read_front_matter_status` is bound into both runners as `_read_status` (`oc_runipd.py:258`), and THE SAME FUNCTION FILE already uses it for exactly this purpose 2500 lines later: `reconcile_disposition`'s review branch reads `status = _read_status(text)` and compares against `("reviewed", "approved")` (`:5813-5822`). So one code path in this module reads the field and another reads the directory, for the same question.
  WHY IT MATTERS BEYOND ONE COMMAND: a Set authored with `executed:` edges between its children (the normal shape, since a later child consumes an earlier child's work) cannot have its children REVIEWED in one sweep until each prerequisite has actually executed. That serializes review behind execution for no reason, and the review sweep's stated purpose is to review several plans in one shared session.
  THE FIX DOES NOT REACH AGY BY BINDING ALONE, contrary to this plan's first draft. `agy_runipd.py` defines its OWN `dependency_status_detailed` (`:2251-2306`) with its OWN `plan_bucket` comparison (`:2292-2305`), so ONE of agy's two entry paths never calls `edge_satisfied` at all. See F-9; E-03 is the item that closes it.
- Scope: Make the external-target branch of `edge_satisfied` consult the plan's `- Status:` field for the non-terminal states, using the reader both runners already import, so the existing review relaxation becomes reachable. Then make agy actually reach that fix by removing its divergent local `dependency_status_detailed` copy, and close the sharing-guard hole that let the copy exist. Do NOT relax the EXECUTE path, and do not change the refusal for a target that genuinely has not reached a permitted state.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: depreview
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 03ie04
- From-Backlog: yf9fj9

## Workflow history

- 2026-09-07 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-009 recorded, eight FIXED and one OPEN. Readiness NO-GO for ONE reason, which is not a defect in the plan's craft: the change it makes is FORBIDDEN BY AN APPROVED SPEC and only the maintainer can resolve that. Spec `25kzda` §2.9 (`- Status: approved`) defines an `executed:` edge as satisfied when the target "is in `executed/` with status `executed`", with NO review-action relaxation anywhere in the section, and its §2.10 states "All surfaces call this evaluator; none reimplement the rules". So the `("executed", "reviewed", "approved")` tuple this plan makes REACHABLE is itself unsanctioned: the plan would take a currently-inert deviation from an approved spec and make it live. That is OQ-04 and it carries `- Blocking: yes`. THE PLAN'S THREE CENTRAL CLAIMS ARE ALL TRUE and I verified each rather than trusting it: the relaxation exists at `:3316`/`:3339`, `plan_bucket` reads directories only (`runner_shared.py:1094-1108`), and `_read_status` is already imported (`:258`) and already used for this exact comparison (`:5813-5822`). I also REPRODUCED the defect in an isolated throwaway repo. THE ONE STRUCTURAL ERROR, and it would have shipped a half-fix: the plan asserts `agy_runipd.py` "BINDS these symbols rather than defining them, so the fix reaches it without an edit", and fences agy out. FALSE, and measured: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False`. Agy defines its own copy (`:2251-2306`) which never calls `edge_satisfied`, cannot parse a typed token (measured: it reports `no plan resolves to this id6` for `executed:tttttt` because it uses the raw string as an id6), and compares `plan_bucket` itself. Agy's OTHER path is oc's, because agy re-exports oc's `dependency_status` whose body resolves `dependency_status_detailed` in OC's globals. So agy has TWO dependency paths with DIFFERENT semantics, and the plan's fence would have left one of them broken while claiming host parity. The existing anti-copy guard misses it because `_SHARED_NAMES` (`tests/test_runner_item_dependencies.py:1121-1133`) lists `dependency_status` but NOT `dependency_status_detailed`. SECOND ERROR: E-03 would have deleted `reviewed`/`approved` from `plan_bucket`, which `tests/test_oc_runipd.py:1819-1835` explicitly asserts it recognizes (measured `2 passed`), so the "observably a no-op" claim was wrong and the plan did not declare that test's file in Scope-Paths.
- 2026-09-07 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yf9fj9`, filed after a live refusal earlier this session. Every claim re-verified at HEAD `3802cb3f` rather than trusted. THE FINDING THAT MOST SHAPES THIS PLAN, and it makes the fix far smaller than the item assumed: the status reader is ALREADY IMPORTED INTO BOTH RUNNERS (`oc_runipd.py:258`, `from agent_workflows.selectors import read_front_matter_status as _read_status`) and THE SAME MODULE ALREADY USES IT FOR THIS EXACT COMPARISON at `:5813-5822`, where `reconcile_disposition`'s review branch reads the field and tests it against `("reviewed", "approved")`. So this is not "teach the runner to read a status"; it is "make one call site agree with the other". The prior work that shared the reader (`rununify` 01, `2r306y`) records why it is shared: "both host runners used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers." ALSO CONFIRMED: `plan_bucket`'s list includes `reviewed` and `approved` as if they were directories, which is where the wrong assumption originates and which OQ-02 addresses. NOT IN SCOPE, and filed separately as the sibling child: the missing persisted REASON that made this defect diagnosable only from a terminal scrollback.

## Goal

Let a plan be reviewed when its prerequisite is reviewed or approved, which the code already intends and cannot currently do, on BOTH hosts, and only once the approved spec sanctions it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the relaxation reachable

- [ ] E-01 In `edge_satisfied`'s EXTERNAL-TARGET branch, resolve the target's effective state from BOTH its directory and its `- Status:` field, rather than from the directory alone. Read the field with `_read_status`, which is ALREADY IMPORTED into this module (`oc_runipd.py:258`) and already used for the same comparison at `:5813-5822`; do NOT add a second reader or a second regex.
  DO NOT START UNTIL OQ-04 IS ANSWERED. This item makes live a state tuple that approved spec `25kzda` §2.9 does not sanction. If the maintainer directs the spec-first route, the spec amendment lands before this code changes.
  PRECEDENCE IS THE DECISION HERE, so make it deliberate: a TERMINAL directory is authoritative (a plan in `executed/` is executed regardless of what a stale field says, which is the anti-fabrication posture the rest of the runner takes), while for a NON-TERMINAL directory the FIELD carries the readiness. State that rule in a comment at the site, because a future reader will otherwise re-derive it wrongly in one direction or the other.
  FAIL CLOSED WHEN THE FIELD IS UNREADABLE. A missing or unparseable `- Status:` must leave the target unsatisfied, exactly as an unrecognized bucket does today. Follow the existing `try`/`except` shape at `:5813-5819`, which already treats an unreadable plan as `status = None`. Note `read_front_matter_status` ALSO returns `None` for a MULTI-WORD status (its docstring: "A multi-word status (e.g. `EXECUTED (approved ...)`) yields `None`"), so a legacy plan with a parenthesized status fails closed too; that is correct, and say so rather than treating `None` as one case.
  - Depends on: none
  - Expected outcome: an external `executed:` target in `pending/` carrying `- Status: reviewed` SATISFIES a review-action edge; a terminal directory still decides on its own; an unreadable, absent, or multi-word status refuses.
  - Execution state: pending

- [ ] E-02 Do NOT relax the EXECUTE path, and prove it. `is_exec` must keep requiring a genuinely `executed/` prerequisite: an execute turn consumes its prerequisite's WORK, so a merely `reviewed` or `approved` plan has produced nothing to consume, and satisfying that edge would dispatch a dependent against a base lacking its prerequisite's commits.
  THE ASYMMETRY IS THE WHOLE POINT and must be visible in the code, not just in this plan: the review branch gains the field read; the execute branch keeps comparing against the terminal directory. Note that for an execute edge the directory IS the right authority, since `executed/` is exactly where finalize puts a plan, so E-01's precedence rule already yields the correct answer without a special case.
  PRESERVE THE FINDINGS GATE'S REACH, and know why it does not help here: `dependency_status_detailed` applies `_findings_block_reason` only `if is_exec` (`oc_runipd.py:3483-3487`), and its docstring states a review-action item "is deliberately NOT findings-gated". So a review edge satisfied by this change is NOT additionally screened for unresolved gating findings. That is the existing intended design, not a regression this plan introduces, but it means E-01's field read is the ONLY gate on the review path; do not weaken it further.
  - Depends on: E-01
  - Expected outcome: an execute-action edge against a `reviewed` or `approved` target still REFUSES; the execute path's behavior is byte-identical to today; the findings gate's `is_exec` scoping is unchanged and its consequence is documented.
  - Execution state: pending

### Task group 2: make the fix actually reach the second host

- [ ] E-03 DELETE `agy_runipd.py`'s local `dependency_status_detailed` (`:2251-2306`) so agy consumes the shared implementation, because WITHOUT THIS ITEM THE FIX REACHES ONLY ONE OF AGY'S TWO PATHS. This is the item the plan's first draft omitted while asserting the opposite.
  THE MEASURED FACTS, verified at review rather than reasoned: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False`, while `agy.dependency_status is oc.dependency_status` -> `True`. Agy's dispatch loop calls the RE-EXPORTED `dependency_status` (`:4325`), whose body resolves `dependency_status_detailed` in OC's module globals, so THAT path already gets the fix. Its drain path calls the LOCAL `dependency_status_detailed` (`:4350`), which does not. Two paths, two semantics, in one driver.
  THE LOCAL COPY IS WORSE THAN STALE, IT IS BROKEN: it never calls `edge_satisfied`, uses the RAW dependency string as an id6 with no `parse_dependency_token`, and therefore cannot resolve a typed edge at all. Measured in a throwaway repo: for `executed:tttttt` it reports `executed:tttttt: no plan resolves to this id6 in the repo`, while for a bare `tttttt` it reports the `plan_bucket`-based refusal. Every plan in this tree declares typed edges, so agy's drain path currently misreports EVERY dependency as dangling.
  DELETION IS THE FIX, NOT PATCHING THE COPY. The module's own comment two lines below already states the rule and the history: `dependency_status` "is NOT defined here ... so the runtime satisfaction semantics exist exactly ONCE. The deleted copy was a verbatim duplicate of oc's, which is how both drivers came to be equally unable to read the canonical field: a fix applied to one silently left the other broken" (`:2309-2314`). That is this defect, recurring in the sibling function. Re-export it in the import block exactly as `dependency_status` is.
  VERIFY THE SIGNATURES MATCH BEFORE DELETING. Agy's local copy returns `{dep_id6: reason}` per its own docstring while oc's returns `{dep_token: reason}` keyed by the token AS DECLARED (`oc_runipd.py:3478-3481`). Any agy caller or test asserting on the KEY shape must be checked; if one exists, report it and fix it inside this plan's Scope-Paths.
  - Depends on: E-02
  - Expected outcome: `agy.dependency_status_detailed is oc.dependency_status_detailed` is True; agy's drain path resolves typed edges; no local copy remains; the reason-map key shape is reconciled and any affected caller named.
  - Execution state: pending

- [ ] E-04 CLOSE THE SHARING-GUARD HOLE that let E-03's copy exist, so this class of divergence cannot recur silently. Add `dependency_status_detailed` to `_SHARED_NAMES` in `tests/test_runner_item_dependencies.py:1121-1133`, which today lists `dependency_status` but not its `_detailed` sibling, which is exactly why `test_the_implementation_is_shared_not_copied` passed over a real copy.
  DEMONSTRATE THE GUARD BITES. Add the name, run the test against the PRE-E-03 code and paste the FAILURE, then run it after E-03 and paste the pass. A guard only ever run against fixed code proves nothing.
  CHECK THE SIBLING GUARD TOO: `tests/test_runner_refork_guard.py`'s `Owned(...)` table (`:140-159`) declares ownership per symbol and includes `plan_bucket` but no dependency-predicate entries. Determine whether `dependency_status_detailed` belongs there as well, and either add it or state why the `_SHARED_NAMES` identity assertion is the right home.
  - Depends on: E-03
  - Expected outcome: `_SHARED_NAMES` includes `dependency_status_detailed`; the guard is shown FAILING pre-fix and passing post-fix; the refork-guard table's applicability is decided and stated.
  - Execution state: pending

### Task group 3: remove the source of the wrong assumption

- [ ] E-05 Correct `plan_bucket`'s DOCUMENTATION, and do NOT delete list members without handling the test that pins them. It scans path components for `executed`, `active`, `pending`, `reviewed`, `approved`, `reusable`, `superseded`, `not-executed` (`runner_shared.py:1096-1105`), and `reviewed/`/`approved/` do not exist as directories in this layout, so listing them invites exactly the confusion this plan is fixing.
  THE "OBSERVABLY A NO-OP" CLAIM WAS FALSE, so this item is re-pointed. `tests/test_oc_runipd.py:1819-1835` (`PlanBucketRecognitionTests::test_recognizes_all_lifecycle_buckets`) asserts `plan_bucket` returns each of the eight names INCLUDING `reviewed` and `approved` for a synthetic path; measured `2 passed` at HEAD. Deleting the members BREAKS that test, so the change is not invisible and that test's file must be in Scope-Paths (it now is).
  THE MINIMAL SAFE CHANGE IS DOCUMENTATION, not deletion: state in the docstring that buckets are DIRECTORIES and readiness is a FIELD, that `reviewed`/`approved` (and `active`) are recognized DEFENSIVELY and do not occur in this layout, and that a caller wanting readiness must read `- Status:` (citing `edge_satisfied` as the precedent). That removes the trap for the next reader at zero behavioral risk.
  IF YOU NEVERTHELESS DELETE THEM, you must also update `tests/test_oc_runipd.py` and prove no caller compares a bucket to those values. THE CALLER SEARCH IS ALREADY DONE and its result is recorded here so you verify rather than rediscover: eight non-test call sites (`oc_runipd.py:1171`, `:2236`, `:3338`, `:5835`, `:6744`, `:6771`; `agy_runipd.py:1466`, `:2292`, `:3176`, `:4065`, `:4089`), and the ONLY equality comparisons are against `"executed"`. `agy_runipd.py:2292` compares against the `("executed","reviewed","approved")` tuple and is DELETED by E-03, which is what removes the last such comparison. Re-verify at execution time; do not trust this list blind.
  - Depends on: E-04
  - Expected outcome: `plan_bucket`'s docstring states that buckets are directories, readiness is a field, and which members are defensive; no real path's bucket changes; if members were removed, the pinning test is updated and the caller search re-verified.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 Test the MATRIX of action against target state, prove BOTH hosts, and prove nothing else moved. The correctness of this change is entirely in which combinations pass.
  THE MATRIX, for an external target: review-action against `pending/` + `Status: reviewed` SATISFIES; review against `pending/` + `Status: approved` SATISFIES; review against `pending/` + `Status: to-review` REFUSES; review against `executed/` SATISFIES; execute against `pending/` + `Status: reviewed` REFUSES; execute against `executed/` SATISFIES; a missing, unparseable, or MULTI-WORD status REFUSES for both actions.
  REPRODUCE THE MEASURED CASE as a named fixture: `ybkmzp` with `- Item-Dependencies: executed:tm2cz8` where `tm2cz8` is `pending/` + `Status: reviewed`, action `review`. Assert it now SATISFIES, and assert against the PRE-FIX code that it refused, so the contrast is demonstrated rather than asserted.
  ASSERT BOTH AGY PATHS, which is the test the plan's original fence made impossible: drive the DISPATCH path (re-exported `dependency_status`) AND the DRAIN path (`dependency_status_detailed`) and assert they agree. Pin `agy.dependency_status_detailed is oc.dependency_status_detailed`.
  ASSERT THE IN-QUEUE PATH IS UNTOUCHED. The in-queue branch (`:3319-3330`) compares against `EXECUTION_SUCCESS_STATES` or `SUCCESS_STATES` from run state, not from disk; pin that so a later refactor does not merge the two paths carelessly. Note `SUCCESS_STATES = {"executed","reviewed","approved"}` (`:320`) is the in-run twin of the on-disk tuple, so if OQ-04 changes the sanctioned states BOTH must change together or the same edge will be judged differently depending on queue membership.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. MEASURE YOUR OWN BEFORE-BASELINE: measured at review `1 failed, 5613 passed, 3 skipped, 2 xfailed` (the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`), so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
  - Depends on: E-05
  - Expected outcome: all seven matrix cases pass; the measured case is pinned with a pre-fix contrast; both agy paths are exercised and agree; the in-queue path is proven unchanged; the bare-suite delta is empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE GATE IS ALREADY ACTION-AWARE and already intends this relaxation: `is_exec = item.get("action") != "review"` and `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")` (`oc_runipd.py:3316`, `:3339`). This plan makes an existing intent reachable rather than adding a new behavior. BUT SEE OQ-04: that intent is not sanctioned by the approved spec.
- APPROVED SPEC `25kzda` §2.9 DEFINES THE EDGE MORE NARROWLY THAN THE CODE: an `executed:` edge requires the target be "in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence", with no review-action relaxation stated. §2.10 adds "All surfaces call this evaluator; none reimplement the rules." The spec carries `- Status: approved`.
- THE READER IS ALREADY SHARED AND ALREADY IMPORTED: `selectors.read_front_matter_status` is bound as `_read_status` in both runners (`oc_runipd.py:258`), and `rununify` 01 (`2r306y`) records why: the runners "used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers."
- THE SAME MODULE ALREADY DOES THIS COMPARISON CORRECTLY, 2500 lines away: `reconcile_disposition`'s review branch reads `status = _read_status(text)` inside a `try`/`except` and tests it against `("reviewed", "approved")` (`:5813-5822`). Follow that shape, including its fail-closed `status = None`.
- `read_front_matter_status` RETURNS `None` FOR A MULTI-WORD STATUS, by documented contract (`selectors.py:294-301`), so a parenthesized legacy status is indistinguishable from an absent one. Both must fail closed.
- READINESS IS A FIELD, NOT A DIRECTORY, in this layout: a plan stays in `pending/` through `draft` -> `to-review` -> `reviewed` -> `approved` and only a TERMINAL state moves it. Verified: `.aw/records/plans/` contains only `executed`, `not-executed`, `pending`, `reusable`, `superseded`; no `reviewed/`, `approved/`, or `active/` directory exists anywhere under `.aw/records`.
- **AGY IS NOT A PURE BINDER OF THIS PREDICATE.** `agy_runipd.py` re-exports `dependency_status` (`:339`) and `edge_satisfied` (`:341`) from oc, but DEFINES its own `dependency_status_detailed` (`:2251-2306`). Measured: `agy.dependency_status is oc.dependency_status` -> True; `agy.dependency_status_detailed is oc.dependency_status_detailed` -> False. So agy's dispatch path (`:4325`) inherits an oc fix and its drain path (`:4350`) does not.
- THE ANTI-COPY GUARD HAS A HOLE: `_SHARED_NAMES` (`tests/test_runner_item_dependencies.py:1121-1133`) lists `dependency_status` but not `dependency_status_detailed`, which is why `test_the_implementation_is_shared_not_copied` passes over a live copy.
- `plan_bucket`'s MEMBERS ARE PINNED BY A TEST: `tests/test_oc_runipd.py:1819-1835` asserts all eight names resolve, including `reviewed` and `approved` (measured `2 passed`). Removing a member is NOT invisible.
- THE FINDINGS GATE IS EXECUTE-ONLY, by design: `_findings_block_reason` is applied only `if is_exec` (`oc_runipd.py:3483-3487`) and the docstring says a review item "is deliberately NOT findings-gated". A review edge made satisfiable by this change gets no findings screening.
- THE IN-QUEUE BRANCH IS A DIFFERENT QUESTION and reads RUN STATE, not disk (`:3319-3330`): "is this prerequisite verified IN THIS RUN yet". The function's own docstring warns it must not be consolidated with the static evaluator. Leave it alone, but keep `SUCCESS_STATES` (`:320`) consistent with whatever OQ-04 sanctions.
- Run the suite BARE: `python3 -m pytest`. The suite is NOT green at HEAD, so judge on the DELTA.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The gate IS action-aware and intends to accept `reviewed`/`approved` for a review turn. | `oc_runipd.py:3316`, `:3339` |
| F-2 | **THE RELAXATION IS UNREACHABLE:** it compares against `plan_bucket`, a DIRECTORY name, and this layout has no `reviewed/` or `approved/` directories, so every non-terminal plan buckets as `pending`. | `oc_runipd.py:3338`; `runner_shared.py:1094-1108`; `ls .aw/records/plans/` |
| F-3 | **MEASURED REFUSAL, AND RE-REPRODUCED IN ISOLATION:** `ybkmzp` (`Item-Dependencies: executed:tm2cz8`, action `review`) was refused with "external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved']" while `tm2cz8` carried `- Status: reviewed`. Re-created at review in a throwaway repo: a `review` item against a `pending/` + `Status: reviewed` target returns `satisfied=False` with the identical message. | `aw oc run --session <sid> ybkmzp`, 2026-09-07; isolated probe at review |
| F-4 | **THE READER IS ALREADY IMPORTED INTO BOTH RUNNERS**, so the fix adds no dependency and no new parsing. | `oc_runipd.py:258` |
| F-5 | **THE SAME MODULE ALREADY READS THE FIELD FOR THE SAME COMPARISON** 2500 lines later, inside a fail-closed `try`/`except`. So one call site reads the field and another reads the directory for the same question. | `oc_runipd.py:5813-5822` |
| F-6 | `plan_bucket` lists `reviewed` and `approved` as if they were directories, which is the origin of the wrong assumption and a trap for the next reader. | `runner_shared.py:1096-1105` |
| F-7 | The consequence is structural, not cosmetic: a Set whose children carry `executed:` edges (the normal shape) cannot have those children reviewed in one sweep until each prerequisite has executed, which serializes review behind execution and defeats the shared-session review sweep. Nine pending plans currently declare such edges. | `aw oc run --help` review-sweep description; the measured refusal; `grep 'Item-Dependencies: executed:' .aw/records/plans/pending/` |
| F-8 | The in-queue branch answers a DIFFERENT question from run state ("is this prerequisite verified IN THIS RUN yet") and its docstring warns against consolidation, so it is deliberately out of scope. Its `SUCCESS_STATES` twin nonetheless encodes the same three states and must stay consistent with the on-disk tuple. | `oc_runipd.py:3300-3330`, `:320` |
| F-9 | **AGY DEFINES ITS OWN `dependency_status_detailed`, SO THE FIX DOES NOT REACH ONE OF ITS TWO PATHS.** Measured: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> `False` (while `dependency_status`, `edge_satisfied` and `plan_bucket` all -> `True`). The local copy never calls `edge_satisfied`, does not parse typed tokens, and compares `plan_bucket` itself; measured, it reports `executed:tttttt: no plan resolves to this id6 in the repo` for a valid typed edge. Agy's dispatch path uses oc's function, its drain path uses the copy. The plan's original claim that agy "binds these symbols rather than defining them" is false, and its fence would have shipped a half-fix. | `agy_runipd.py:2251-2306`, `:4325`, `:4350`; interpreter identity probe; isolated repo probe |
| F-10 | **THE ANTI-COPY GUARD MISSES IT:** `_SHARED_NAMES` lists `dependency_status` but not `dependency_status_detailed`, so `test_the_implementation_is_shared_not_copied` passes over the copy in F-9. The module's own comment at `:2309-2314` already describes this exact failure mode for the sibling function ("a fix applied to one silently left the other broken"), so the class of defect is known and recurring. | `tests/test_runner_item_dependencies.py:1121-1149`; `agy_runipd.py:2309-2314` |
| F-11 | **DELETING `plan_bucket`'s DEAD MEMBERS IS NOT A NO-OP:** `PlanBucketRecognitionTests::test_recognizes_all_lifecycle_buckets` explicitly asserts `reviewed` and `approved` resolve (measured `2 passed`). The plan's "observably a no-op" premise was wrong and it did not declare that test file in Scope-Paths. | `tests/test_oc_runipd.py:1819-1835` |
| F-12 | **THE APPROVED SPEC DOES NOT SANCTION THE RELAXATION.** `25kzda` §2.9 defines an `executed:` edge as requiring the target be "in `executed/` with status `executed`", says nothing about a review action accepting `reviewed`/`approved`, and §2.10 says no surface may reimplement the rules. The spec is `- Status: approved`. So the tuple this plan makes live is an undocumented deviation, and making it reachable converts a dormant deviation into an active one. | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:4`, `:363-373` |
| F-13 | A REVIEW EDGE IS NOT FINDINGS-GATED: `_findings_block_reason` runs only `if is_exec`. So once E-01 makes review edges satisfiable, nothing additionally screens the prerequisite's unresolved gating findings. Pre-existing intent, but newly consequential. | `oc_runipd.py:3483-3487` and the `dependency_status_detailed` docstring |

## Proposed changes (ordered, validatable)

1. Resolve an external target's state from the terminal directory OR the `- Status:` field, using the already-imported reader, failing closed when unreadable, absent, or multi-word (E-01).
2. Keep the execute path requiring a genuinely `executed/` prerequisite, and document that the review path is not findings-gated (E-02).
3. Delete agy's divergent local `dependency_status_detailed` so both of its paths consume the shared predicate (E-03).
4. Close the `_SHARED_NAMES` hole and demonstrate the guard bites (E-04).
5. Document `plan_bucket`'s vocabulary rather than silently breaking the test that pins it (E-05).
6. Pin the seven-case matrix, the measured case with a pre-fix contrast, both agy paths, and the unchanged in-queue path (E-06).

## Deferred / out of scope (with reason)

- THE MISSING PERSISTED REASON. Sibling child `2p8p71` (depreview-02) owns persisting WHY an item was dependency-blocked. That defect is what made THIS one diagnosable only from a terminal scrollback, so the two are related but separately verifiable: this one changes a decision, that one records it.
- THE IN-QUEUE DEPENDENCY BRANCH. It reads run state to answer "verified in this run yet", a different question, and its own docstring warns it must not be consolidated with the static evaluator. Untouched, except that `SUCCESS_STATES` must stay consistent with whatever OQ-04 sanctions.
- THE STATIC EVALUATOR (`check_engine.evaluate_ipd_dependencies`). The function's docstring is explicit that the shared rules live there and "NOTHING of them is re-implemented here", and that consolidating the runtime wait/release semantics into it "would break both". This plan changes only the runtime branch.
- EXTENDING THE FINDINGS GATE TO REVIEW EDGES (F-13). A deliberate existing design decision with its own rationale; changing it is a separate judgement about what a review turn should be blocked on, and bundling it here would conflate "make the intended behavior reachable" with "change the intended behavior".
- WHETHER `reviewed`/`approved` SHOULD BECOME REAL DIRECTORIES. That is a layout decision with wide consequences (every selector, every index, every existing plan's path) and is not needed to fix this: the field already carries the state. Backlog `qzhfk2` covers whether specs should get lifecycle subdirs, which is the same question one tree over.
- RELAXING WHAT AN EXECUTE EDGE REQUIRES. Explicitly counter to the goal; E-02 pins it.
- THE BROADER `rununify` CONSOLIDATION. E-03 removes ONE divergent copy because it blocks this fix; it does not attempt the Set's wider extraction of shared runner logic.

## Scope check

- Over-scope: none. One branch of one predicate, one duplicated function removed, one docstring, one guard list, and three test modules.
- Scope-Paths justification: `oc_runipd.py` holds `edge_satisfied` and the already-imported reader (E-01, E-02); `agy_runipd.py` holds the divergent local `dependency_status_detailed` that must be DELETED for the fix to reach that host's drain path (E-03, F-9); `runner_shared.py` holds `plan_bucket` (E-05); `tests/test_runner_item_dependencies.py` holds the `_SHARED_NAMES` guard (E-04); `tests/test_oc_runipd.py` holds the `plan_bucket` pinning test (E-05, F-11) and the oc matrix; `tests/test_agy_runipd_cli.py` covers the per-host paths (E-06). NOTE the earlier revision deliberately EXCLUDED `agy_runipd.py` on the false premise that it only binds these symbols; F-9 measured otherwise, so it is now in scope by necessity.
- Under-scope, stated rather than left as `none`: this child does not persist the block reason, does not touch the in-queue branch or the static evaluator, does not extend the findings gate to review edges, does not create `reviewed/`/`approved/` directories, does not relax the execute path, and does not attempt the wider `rununify` consolidation. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the summary line pasted and counts stated. Measured BEFORE at review: `1 failed, 5613 passed, 3 skipped, 2 xfailed`. The criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
- Targeted: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_runner_item_dependencies.py`, `tests/test_runner_refork_guard.py`.
- THE IDENTITY ASSERTION, pasted: `agy.dependency_status_detailed is oc.dependency_status_detailed` -> True after E-03 (it is False at HEAD).
- THE GUARD-BITES DEMONSTRATION: `test_the_implementation_is_shared_not_copied` FAILING against pre-E-03 code with the new name added, then passing.
- BOTH AGY PATHS exercised (dispatch via the re-exported `dependency_status`, drain via `dependency_status_detailed`) and shown to agree.
- A LIVE END-TO-END DEMONSTRATION on BOTH hosts: a `review` action whose external prerequisite is `pending/` + `Status: reviewed`, proceeding rather than reporting `dependency-blocked`. If a host cannot be demonstrated, SAY SO PLAINLY rather than inferring from the other.
- THE PRE-FIX CONTRAST for the measured case, pasted, so the fix is shown to change the outcome.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`); a pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

**THIS PLAN AMENDS SPEC `25kzda` §2.9, AND THE AMENDMENT LANDS FIRST (OQ-04 RESOLVED 2026-09-07, OPTION (a)).** §2.9 owns the dependency wait/release semantics that `edge_satisfied` implements, it is `approved`, and it defines an `executed:` edge as satisfied only when the target "is in `executed/` with status `executed`", describing no review-action relaxation. So the change here is not "make the runner read the state correctly" in a spec-neutral sense: the three-state tuple the code carries is itself unsanctioned, and this plan makes it LIVE. The maintainer ruled the relaxation IS the intended contract and that §2.9 is amended to say so BEFORE this code path is made live, so shipped behavior never contradicts an approved spec. The spec file is declared in `- Scope-Paths:` so the edit is announced at run start and reconciled by the finalize scope gate.

THE AMENDMENT IS A PRECONDITION, NOT A SIDE EFFECT. If it has not landed when this plan is dispatched, refuse and report rather than making the path live against an unamended spec. The amendment must state the review-action relaxation (a REVIEW action accepts `executed`, `reviewed`, or `approved`), that an EXECUTE action still requires the full `executed/` plus evidence condition, and that readiness is read from the `- Status:` field rather than the directory.

DO NOT EDIT the spec's §4.2 finding-code table: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change. The amendment belongs in §2.9's prose and its edge table row.

`edge_satisfied`'s comment at the external-target branch must state the precedence rule E-01 establishes (terminal directory authoritative; otherwise the field), since that is exactly the reasoning a future reader would otherwise get wrong. `plan_bucket`'s docstring must state that buckets are DIRECTORIES, readiness is a FIELD, and which members are recognized only defensively (E-05).

The refusal message is operator-facing and should name what it actually read. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: When a plan's directory and its `- Status:` field disagree, which wins?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A TERMINAL DIRECTORY WINS; otherwise the FIELD wins. A plan in `executed/` is executed whatever a stale field claims, because `aw ipd finalize` is what moves it there and the move is the harder-to-forge signal; that matches the anti-fabrication posture `reconcile_disposition` already takes when it trusts the directory over an agent's outcome file. For a NON-TERMINAL directory there is no competing signal at all: `pending/` is where every plan sits from `draft` through `approved`, so the field is the only thing that distinguishes them and reading the directory tells you nothing. The rule is therefore not a compromise between two authorities but a recognition that only one of them carries information in each case.

### OQ-02: Should `plan_bucket` keep listing `reviewed` and `approved`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP THEM AND DOCUMENT THEM; do not delete. This REVERSES the earlier resolution, on measured evidence. The earlier answer ("remove them, it is observably a no-op") rested on a false premise: `tests/test_oc_runipd.py:1819-1835` explicitly asserts `plan_bucket` recognizes all eight names including these two (measured `2 passed`), so deletion breaks a passing test and is not invisible. The trap the earlier answer wanted to remove is real, but the cheap fix for a misleading list is a docstring that says WHY the members exist (defensive recognition of names that do not occur in this layout) and where readiness actually lives, at zero behavioral risk. Deletion would buy nothing beyond that and would spend a test edit plus a caller re-verification to remove a defensive branch. The caller search that the earlier answer demanded was performed at review and found the only `== "executed"` comparisons plus the tuple comparison at `agy_runipd.py:2292`, which E-03 deletes for an independent reason.

### OQ-03: Should the fix live in `edge_satisfied` or in `plan_bucket`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IN `edge_satisfied`. `plan_bucket` answers a narrow and honest question, "which lifecycle directory is this path in", and it answers it correctly; teaching it to read file contents would make a path-inspection helper do IO and would change the meaning of every existing caller's result across eleven call sites. The defect is that `edge_satisfied` asked `plan_bucket` a question it cannot answer (what is this plan's readiness) rather than that `plan_bucket` answered wrongly. Fixing it at the call site keeps each function honest and confines the change to the one caller whose question was wrong; E-05's docstring correction is documentation hygiene at the helper, not the fix.

### OQ-04: Approved spec `25kzda` §2.9 does not sanction the review-action relaxation this plan makes live. Amend the spec first, or proceed and amend after?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-07 BY MAINTAINER RULING: OPTION (a), AMEND SPEC §2.9 FIRST, THEN LAND. The `("executed", "reviewed", "approved")` acceptance for a review-action edge IS the intended contract, so option (c) (deleting the two states) is rejected: the relaxation's reasoning holds (a review writes no code and cannot be invalidated by an unexecuted prerequisite) and F-7's serialization is a real cost that would fall on nine currently-pending plans. The spec is amended in a maintainer-approved change that lands BEFORE the code path is made live, so the contract is never in a state where shipped behavior contradicts it, which is what distinguishes (a) from (b).
  A PLAN MAY AMEND A SPEC, AND THIS ONE DOES. The maintainer's ruling settles the framing question this OQ raised: specs are living contracts meant to EVOLVE as we learn, so amending §2.9 is legitimate rather than a violation, and the obligation is to make the amendment IMPOSSIBLE TO MISS (`AGENTS.md:82`). Accordingly the spec file is now declared in `- Scope-Paths:`, which is what makes the runner announce the edit before the run starts and what the finalize scope gate reconciles afterwards; the visibility mechanism itself is tracked by backlog `dk16dx` (`Blocks-Release: next`), which records that agy never calls the announcement helper and that neither host announces at run END.
  WHAT THE AMENDMENT MUST SAY: §2.9 gains the review-action relaxation explicitly, stating that an edge whose consuming action is a REVIEW is satisfied by a target in `executed`, `reviewed`, or `approved`, and that an EXECUTE action still requires the full `executed/` plus evidence condition. §2.10's "All surfaces call this evaluator; none reimplement the rules" stays intact and is the reason the relaxation belongs in the shared evaluator rather than in either host. Do NOT weaken the execute-action condition while editing, and do NOT touch the finding-code table (byte-equality test).
  ORDERING CONSEQUENCE, stated because it changes this plan's queue position: the spec amendment is a PRECONDITION, not a side effect. If the amendment has not landed when this plan is dispatched, the correct action is to refuse and report, not to make the path live against an unamended spec.
  ALSO NOTE E-06's IN-RUN TWIN. `SUCCESS_STATES = {"executed","reviewed","approved"}` (`oc_runipd.py:320`) is the in-run twin of the on-disk tuple; the amendment sanctions BOTH readings, so E-06's requirement to state whether the twin needed a matching change stands unchanged (PR-005).
  ORIGINAL ESCALATION RATIONALE, retained for the record: the decision needed was whether the three-state acceptance is the intended contract, and if so whether spec `25kzda` is amended BEFORE this code ships or in the same change.
  WHY IT BLOCKS. Spec `25kzda` carries `- Status: approved` and its §2.9 defines an `executed:` edge as satisfied when the target "is in `executed/` with status `executed`, passes terminal lint, and has valid deterministic execution/finalization evidence"; there is no review-action exception anywhere in the section, and §2.10 states "All surfaces call this evaluator; none reimplement the rules." Today the deviation is INERT, because the relaxation is unreachable (F-2), so nothing has ever behaved contrary to the spec. This plan's entire purpose is to make it reachable, which converts a dormant deviation from an approved spec into a live one. An agent must not do that on its own authority: approving a contract change is a human act, and this is a contract change dressed as a bug fix.
  WHY I DID NOT RESOLVE IT FROM EVIDENCE. The repository genuinely does not answer it. The code says one thing (three states for a review turn, since before the current shared-predicate refactor), the approved spec says another (one state, unconditionally), and no review record, plan, or history line reconciles them. Choosing either reading would be inventing the maintainer's intent about a public contract.
  WHAT EACH OPTION COSTS. (a) AMEND THE SPEC FIRST, then execute: correct by the book, and the spec then documents both the relaxation and that readiness is read from the field; costs one extra round trip. (b) PROCEED AND AMEND IN THE SAME CHANGE: one pass, and the spec and code land consistent; but a spec edit inside an execution turn is a wider act than this plan's fence contemplates. (c) DECIDE THE RELAXATION IS WRONG and instead DELETE the two dead states so the code matches the spec: that also fixes the false-advertising refusal message, is a smaller change, and would close backlog `yf9fj9` with the opposite outcome; it costs the review-sweep serialization F-7 describes.
  RECOMMENDATION: (a) or (b), because F-7's serialization is a real cost paid on nine currently-pending plans and the relaxation's reasoning (a review writes no code and cannot be invalidated by an unexecuted prerequisite) is sound. But (c) is a legitimate answer and the choice is the maintainer's.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the changed external-target branch. Show FOUR probes: `pending/` + `Status: reviewed` under a review action SATISFIES; `pending/` + `Status: to-review` REFUSES; an absent status REFUSES; a MULTI-WORD status REFUSES. Quote the comment stating the precedence rule. Confirm by inspection that `_read_status` is the already-imported reader and that no second reader or regex was added. State that OQ-04 was answered and how.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste an execute-action edge against a `pending/` + `Status: reviewed` target REFUSING, and against an `executed/` target SATISFYING. Paste a diff or a statement confirming the execute path's behavior is unchanged from today, and state in one sentence why an execute edge legitimately needs the terminal directory (it consumes the prerequisite's work). Paste the `if is_exec` findings-gate line unchanged and state in one sentence that a review edge is therefore not findings-gated.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `agy.dependency_status_detailed is oc.dependency_status_detailed` -> True (and the pre-fix `False` for contrast). Paste the deletion diff and the re-export line. Paste a probe showing agy's DRAIN path now resolves a TYPED edge (`executed:<id6>`) instead of reporting `no plan resolves to this id6`. State what you found about the reason-map KEY shape (`dep_id6` vs `dep_token`) and name any caller or test affected.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `_SHARED_NAMES` containing `dependency_status_detailed`. Paste the guard FAILING against pre-E-03 code and then PASSING after it, so it is shown to bite rather than merely be green. State the decision about `tests/test_runner_refork_guard.py`'s `Owned` table with its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `plan_bucket`'s updated docstring. Paste `PlanBucketRecognitionTests` PASSING (or, if members were removed, the updated test plus the re-verified caller search naming every call site and its comparison). Paste a probe showing a real path's bucket is UNCHANGED for each member.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the ACTUAL output of all seven matrix cases. Paste the measured-case fixture (`ybkmzp` / `tm2cz8`) SATISFYING, AND the same fixture against the PRE-FIX code REFUSING with the original message. Paste BOTH agy paths agreeing. Paste the in-queue-path test proving that branch is unchanged, and state whether `SUCCESS_STATES` needed a matching change. Paste a real review run on BOTH hosts, or say plainly which host could not be demonstrated. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is EMPTY.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**EXECUTION IS BLOCKED ON OQ-04**, which carries `- Blocking: yes` and is OPEN. The pre-execution lint will refuse while it stands, and that is correct: this plan makes live a behavior an approved spec does not sanction, and only the maintainer may decide that. Answer OQ-04 first; approval alone is not enough.

Execution otherwise requires explicit human approval (`- Status: approved`).

Scope fence: touch ONLY the six paths in `Scope-Paths`. Do NOT relax what an EXECUTE edge requires. Do NOT modify the in-queue dependency branch or `check_engine.evaluate_ipd_dependencies`. Do NOT make `plan_bucket` read file contents (OQ-03). Do NOT create `reviewed/` or `approved/` directories. Do NOT extend the findings gate to review edges. Do NOT edit spec `25kzda` except as OQ-04 directs, and NEVER its §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and `oc_runipd.py` is the highest-contention file in it: run `aw runs` before starting, and if it is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD (`1 failed, 5613 passed`) and this plan does not make it green. Judge on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.

THE ITEM THAT MATTERS MOST IS V-02. This change makes a gate accept MORE, which is the direction where a mistake lets real work proceed against an unmet prerequisite. The relaxation must apply to a REVIEW action ONLY: an execute turn consumes its prerequisite's commits, so satisfying its edge on a merely `reviewed` plan would dispatch it against a base that lacks the work it depends on. If you find the execute path accepting a non-terminal target, stop.

THE SECOND-MOST IMPORTANT IS V-03, and it exists because this plan's first draft got it wrong. Do NOT assume agy inherits an oc fix: it defines its own `dependency_status_detailed` and one of its two dependency paths does not call `edge_satisfied` at all. Prove the identity, do not reason about it.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `edge_satisfied`, its external-target branch, `plan_bucket`, `_read_status`'s import, `reconcile_disposition`'s review branch, agy's local `dependency_status_detailed`, and `_SHARED_NAMES` by name.

On completion, close backlog `yf9fj9`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited. NOTE that if OQ-04 is answered with option (c), the correct closure is the OPPOSITE outcome (delete the dead states so the code matches the spec), and this plan must be superseded rather than executed as written.
