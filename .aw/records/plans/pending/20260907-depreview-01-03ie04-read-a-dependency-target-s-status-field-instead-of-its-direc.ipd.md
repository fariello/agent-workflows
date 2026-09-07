# IPD: Read a dependency target's status field instead of its directory so the review relaxation is reachable

- Date: 2026-09-07
- Kind: child
- Concern: `edge_satisfied` is correctly ACTION-AWARE for an `executed:` dependency and deliberately relaxes the requirement for a REVIEW turn (`oc_runipd.py:3312`, `:3339`): `is_exec = item.get("action") != "review"`, then `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")`. That is the right semantics, because a review writes no code and cannot be invalidated by an unexecuted prerequisite. But the relaxation is UNREACHABLE, because the value compared against `allowed` is a DIRECTORY NAME rather than the plan's `- Status:` field: `bucket = plan_bucket(dep_path)` (`:3338`), and `plan_bucket` (`runner_shared.py:1094-1108`) merely scans path components for one of a fixed list. In this repository readiness lives in the `- Status:` FIELD and a plan STAYS in `pending/` until a TERMINAL state moves it, so there are no `reviewed/` or `approved/` directories at all. Every non-terminal plan therefore buckets as `pending`, which is absent from `allowed`, and the review path refuses exactly as the execute path would.
  SO TWO OF THE THREE ALLOWED VALUES ARE DEAD CODE for every plan in this tree. The relaxation is real in intent and inert in practice.
  MEASURED 2026-09-07. `aw oc run --session <sid> ybkmzp`, where `ybkmzp` declares `- Item-Dependencies: executed:tm2cz8` and `tm2cz8` carries `- Status: reviewed` in `.aw/records/plans/pending/`, refused: `ybkmzp: dependency-blocked (executed:tm2cz8: external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved'] (it is not in this run, so it cannot become satisfied here))`. The message names the three states it would accept and reports the one thing it read, which is a directory. `tm2cz8` satisfied the intended condition and was refused anyway.
  THE FIX IS SMALL BECAUSE THE READER ALREADY EXISTS AND IS ALREADY IMPORTED. `selectors.read_front_matter_status` is bound into both runners as `_read_status` (`oc_runipd.py:258`), and THE SAME FUNCTION FILE already uses it for exactly this purpose 2500 lines later: `reconcile_disposition`'s review branch reads `status = _read_status(text)` and compares against `("reviewed", "approved")` (`:5814-5821`). So one code path in this module reads the field and another reads the directory, for the same question.
  WHY IT MATTERS BEYOND ONE COMMAND: a Set authored with `executed:` edges between its children (the normal shape, since a later child consumes an earlier child's work) cannot have its children REVIEWED in one sweep until each prerequisite has actually executed. That serializes review behind execution for no reason, and the review sweep's stated purpose is to review several plans in one shared session.
- Scope: Make the external-target branch of `edge_satisfied` consult the plan's `- Status:` field for the non-terminal states, using the reader both runners already import, so the existing review relaxation becomes reachable. Do NOT relax the EXECUTE path, and do not change the refusal for a target that genuinely has not reached a permitted state.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/runner_shared.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: depreview
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 03ie04
- From-Backlog: yf9fj9

## Workflow history

- 2026-09-07 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yf9fj9`, filed after a live refusal earlier this session. Every claim re-verified at HEAD `3802cb3f` rather than trusted. THE FINDING THAT MOST SHAPES THIS PLAN, and it makes the fix far smaller than the item assumed: the status reader is ALREADY IMPORTED INTO BOTH RUNNERS (`oc_runipd.py:258`, `from agent_workflows.selectors import read_front_matter_status as _read_status`) and THE SAME MODULE ALREADY USES IT FOR THIS EXACT COMPARISON at `:5814-5821`, where `reconcile_disposition`'s review branch reads the field and tests it against `("reviewed", "approved")`. So this is not "teach the runner to read a status"; it is "make one call site agree with the other". The prior work that shared the reader (`rununify` 01, `2r306y`) records why it is shared: "both host runners used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers." ALSO CONFIRMED: `plan_bucket`'s list includes `reviewed` and `approved` as if they were directories, which is where the wrong assumption originates and which OQ-02 addresses. NOT IN SCOPE, and filed separately as the sibling child: the missing persisted REASON that made this defect diagnosable only from a terminal scrollback.

## Goal

Let a plan be reviewed when its prerequisite is reviewed or approved, which the code already intends and cannot currently do.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the relaxation reachable

- [ ] E-01 In `edge_satisfied`'s EXTERNAL-TARGET branch, resolve the target's effective state from BOTH its directory and its `- Status:` field, rather than from the directory alone. Read the field with `_read_status`, which is ALREADY IMPORTED into this module (`oc_runipd.py:258`) and already used for the same comparison at `:5814-5821`; do NOT add a second reader or a second regex.
  PRECEDENCE IS THE DECISION HERE, so make it deliberate: a TERMINAL directory is authoritative (a plan in `executed/` is executed regardless of what a stale field says, which is the anti-fabrication posture the rest of the runner takes), while for a NON-TERMINAL directory the FIELD carries the readiness. State that rule in a comment at the site, because a future reader will otherwise re-derive it wrongly in one direction or the other.
  FAIL CLOSED WHEN THE FIELD IS UNREADABLE. A missing or unparseable `- Status:` must leave the target unsatisfied, exactly as an unrecognized bucket does today. Follow the existing `try`/`except` shape at `:5814-5819`, which already treats an unreadable plan as `status = None`.
  - Depends on: none
  - Expected outcome: an external `executed:` target in `pending/` carrying `- Status: reviewed` SATISFIES a review-action edge; a terminal directory still decides on its own; an unreadable status refuses.
  - Execution state: pending

- [ ] E-02 Do NOT relax the EXECUTE path, and prove it. `is_exec` must keep requiring a genuinely `executed/` prerequisite: an execute turn consumes its prerequisite's WORK, so a merely `reviewed` or `approved` plan has produced nothing to consume, and satisfying that edge would dispatch a dependent against a base lacking its prerequisite's commits.
  THE ASYMMETRY IS THE WHOLE POINT and must be visible in the code, not just in this plan: the review branch gains the field read; the execute branch keeps comparing against the terminal directory. Note that for an execute edge the directory IS the right authority, since `executed/` is exactly where finalize puts a plan, so E-01's precedence rule already yields the correct answer without a special case.
  - Depends on: E-01
  - Expected outcome: an execute-action edge against a `reviewed` or `approved` target still REFUSES; the execute path's behavior is byte-identical to today.
  - Execution state: pending

### Task group 2: remove the source of the wrong assumption

- [ ] E-03 Correct `plan_bucket`'s vocabulary, which is where this defect originates. It scans path components for `executed`, `active`, `pending`, `reviewed`, `approved`, `reusable`, `superseded`, `not-executed` (`runner_shared.py:1096-1105`), but `reviewed/` and `approved/` DO NOT EXIST as directories in this layout, so listing them invites exactly the confusion this plan is fixing: a reader sees `reviewed` in the list and reasonably concludes a bucket can be `reviewed`.
  DO NOT CHANGE THE FUNCTION'S RETURN VALUES FOR ANY REAL PATH. Removing an unreachable member changes nothing observable, but VERIFY that before doing it: search every caller and confirm none tests for `== "reviewed"` or `== "approved"` on a bucket. If any does, that caller is a second instance of this same bug and must be reported (and, if it is in this plan's Scope-Paths, fixed).
  DOCUMENT WHY THE LIST IS WHAT IT IS, so the next reader does not re-add them: buckets are DIRECTORIES, and readiness is a FIELD.
  - Depends on: E-02
  - Expected outcome: `plan_bucket` lists only names that can actually occur, with a comment stating buckets are directories and readiness is a field; no real path's bucket changes; any other caller comparing a bucket to `reviewed`/`approved` is reported.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 Test the MATRIX of action against target state, because the correctness of this change is entirely in which combinations pass. For an external target, assert: review-action against `pending/` + `Status: reviewed` SATISFIES; review against `pending/` + `Status: approved` SATISFIES; review against `pending/` + `Status: to-review` REFUSES; review against `executed/` SATISFIES; execute against `pending/` + `Status: reviewed` REFUSES; execute against `executed/` SATISFIES; and an unreadable or missing status REFUSES for both actions.
  REPRODUCE THE MEASURED CASE as a named fixture: `ybkmzp` with `- Item-Dependencies: executed:tm2cz8` where `tm2cz8` is `pending/` + `Status: reviewed`, action `review`. Assert it now SATISFIES, and assert against the PRE-FIX code that it refused, so the contrast is demonstrated rather than asserted.
  ASSERT THE IN-QUEUE PATH IS UNTOUCHED. The in-queue branch (`:3318-3326`) compares against `EXECUTION_SUCCESS_STATES` or `SUCCESS_STATES` from run state, not from disk, and this plan does not change it; a test should pin that so a later refactor does not merge the two paths carelessly.
  - Depends on: E-03
  - Expected outcome: all seven matrix cases pass, the measured case is pinned with a pre-fix contrast, and the in-queue path is proven unchanged.
  - Execution state: pending

- [ ] E-05 Prove it END TO END through the runner on BOTH hosts, and prove nothing else moved. Drive a real `review` action whose external prerequisite is `pending/` + `Status: reviewed` and show the run proceeds rather than reporting `dependency-blocked`.
  BOTH HOSTS EXPLICITLY. `edge_satisfied` and `plan_bucket` are shared (agy binds them rather than forking), so the fix should reach both by construction, but the CALL PATH is per-driver and the agy suite is materially thinner. If a host cannot be demonstrated, say so plainly rather than inferring from the other.
  Run the suite BARE (`python3 -m pytest`) and state before/after counts. MEASURE YOUR OWN BEFORE-BASELINE: the suite is NOT green at HEAD (`1 failed, 5612 passed` at authoring, the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`), so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
  - Depends on: E-04
  - Expected outcome: a review whose prerequisite is `reviewed` runs on both hosts; the bare-suite delta is empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE GATE IS ALREADY ACTION-AWARE and already intends this relaxation: `is_exec = item.get("action") != "review"` and `allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")` (`oc_runipd.py:3312`, `:3339`). This plan makes an existing intent reachable rather than adding a new behavior.
- THE READER IS ALREADY SHARED AND ALREADY IMPORTED: `selectors.read_front_matter_status` is bound as `_read_status` in both runners (`oc_runipd.py:258`), and `rununify` 01 (`2r306y`) records why: the runners "used to carry their own private `_read_id`/`_read_status` copies; they now call these, so there is ONE definition per reader and a fix reaches both drivers."
- THE SAME MODULE ALREADY DOES THIS COMPARISON CORRECTLY, 2500 lines away: `reconcile_disposition`'s review branch reads `status = _read_status(text)` inside a `try`/`except` and tests it against `("reviewed", "approved")` (`:5814-5821`). Follow that shape, including its fail-closed `status = None`.
- READINESS IS A FIELD, NOT A DIRECTORY, in this layout: a plan stays in `pending/` through `draft` -> `to-review` -> `reviewed` -> `approved` and only a TERMINAL state moves it. `plan_bucket` listing `reviewed`/`approved` as directory names is the origin of the wrong assumption.
- THE IN-QUEUE BRANCH IS A DIFFERENT QUESTION and reads RUN STATE, not disk (`:3318-3326`): "is this prerequisite verified IN THIS RUN yet". The function's own docstring warns it must not be consolidated with the static evaluator for the same reason. Leave it alone.
- Run the suite BARE: `python3 -m pytest`. The suite is NOT green at HEAD, so judge on the DELTA.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The gate IS action-aware and intends to accept `reviewed`/`approved` for a review turn. | `oc_runipd.py:3312`, `:3339` |
| F-2 | **THE RELAXATION IS UNREACHABLE:** it compares against `plan_bucket`, a DIRECTORY name, and this layout has no `reviewed/` or `approved/` directories, so every non-terminal plan buckets as `pending`. | `oc_runipd.py:3338`; `runner_shared.py:1094-1108` |
| F-3 | **MEASURED REFUSAL:** `ybkmzp` (`Item-Dependencies: executed:tm2cz8`, action `review`) was refused with "external target tm2cz8 is in 'pending', needs one of ['executed', 'reviewed', 'approved']" while `tm2cz8` carried `- Status: reviewed`. | `aw oc run --session <sid> ybkmzp`, 2026-09-07 |
| F-4 | **THE READER IS ALREADY IMPORTED INTO BOTH RUNNERS**, so the fix adds no dependency and no new parsing. | `oc_runipd.py:258` |
| F-5 | **THE SAME MODULE ALREADY READS THE FIELD FOR THE SAME COMPARISON** 2500 lines later, inside a fail-closed `try`/`except`. So one call site reads the field and another reads the directory for the same question. | `oc_runipd.py:5814-5821` |
| F-6 | `plan_bucket` lists `reviewed` and `approved` as if they were directories, which is the origin of the wrong assumption and a trap for the next reader. | `runner_shared.py:1096-1105` |
| F-7 | The consequence is structural, not cosmetic: a Set whose children carry `executed:` edges (the normal shape) cannot have those children reviewed in one sweep until each prerequisite has executed, which serializes review behind execution and defeats the shared-session review sweep. | `aw oc run --help` review-sweep description; the measured refusal |
| F-8 | The in-queue branch answers a DIFFERENT question from run state ("is this prerequisite verified IN THIS RUN yet") and its docstring warns against consolidation, so it is deliberately out of scope. | `oc_runipd.py:3300-3326` |

## Proposed changes (ordered, validatable)

1. Resolve an external target's state from the terminal directory OR the `- Status:` field, using the already-imported reader, failing closed when unreadable (E-01).
2. Keep the execute path requiring a genuinely `executed/` prerequisite, and make the asymmetry visible in the code (E-02).
3. Correct `plan_bucket`'s vocabulary to list only names that can occur, and report any other caller comparing a bucket to `reviewed`/`approved` (E-03).
4. Pin the seven-case action-against-state matrix plus the measured case with a pre-fix contrast (E-04).
5. Prove it end to end on both hosts and show the bare-suite delta is empty (E-05).

## Deferred / out of scope (with reason)

- THE MISSING PERSISTED REASON. Sibling child `2p8p71` (depreview-02) owns persisting WHY an item was dependency-blocked. That defect is what made THIS one diagnosable only from a terminal scrollback, so the two are related but separately verifiable: this one changes a decision, that one records it.
- THE IN-QUEUE DEPENDENCY BRANCH. It reads run state to answer "verified in this run yet", a different question, and its own docstring warns it must not be consolidated with the static evaluator. Untouched.
- THE STATIC EVALUATOR (`check_engine.evaluate_ipd_dependencies`). The function's docstring is explicit that the shared rules live there and "NOTHING of them is re-implemented here", and that consolidating the runtime wait/release semantics into it "would break both". This plan changes only the runtime branch.
- WHETHER `reviewed`/`approved` SHOULD BECOME REAL DIRECTORIES. That is a layout decision with wide consequences (every selector, every index, every existing plan's path) and is not needed to fix this: the field already carries the state. Backlog `qzhfk2` covers whether specs should get lifecycle subdirs, which is the same question one tree over.
- RELAXING WHAT AN EXECUTE EDGE REQUIRES. Explicitly counter to the goal; E-02 pins it.

## Scope check

- Over-scope: none. One branch of one predicate, one vocabulary list, and two driver test modules.
- Scope-Paths justification: `oc_runipd.py` holds `edge_satisfied` and the already-imported reader (E-01, E-02); `runner_shared.py` holds `plan_bucket` (E-03); `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` cover the matrix and the per-host end-to-end path. `agy_runipd.py` is deliberately NOT in Scope-Paths: it BINDS these symbols rather than defining them, so the fix reaches it without an edit, and declaring a path this plan should not modify would invite an unnecessary change to a high-contention file.
- Under-scope, stated rather than left as `none`: this child does not persist the block reason, does not touch the in-queue branch or the static evaluator, does not create `reviewed/`/`approved/` directories, and does not relax the execute path. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE; the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
- Targeted: `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, plus whatever module covers `plan_bucket`.
- A LIVE END-TO-END DEMONSTRATION on BOTH hosts: a `review` action whose external prerequisite is `pending/` + `Status: reviewed`, proceeding rather than reporting `dependency-blocked`.
- THE PRE-FIX CONTRAST for the measured case, pasted, so the fix is shown to change the outcome.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`); a pipe through `head` reports the pipe's status, which has already produced one false finding in this repository.
- `aw sanitize --agent` clean.

## Spec / documentation sync

Spec `25kzda` §2.9 owns the dependency wait/release semantics that `edge_satisfied` implements. This plan does NOT change which states satisfy an edge; it makes the runner read the state correctly. If the spec's text describes the check in terms of a plan's DIRECTORY rather than its status, NOTE IT for an amendment and do not edit the spec here: its §4.2 finding-code table is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

`edge_satisfied`'s comment at the external-target branch must state the precedence rule E-01 establishes (terminal directory authoritative; otherwise the field), since that is exactly the reasoning a future reader would otherwise get wrong. `plan_bucket`'s docstring must state that buckets are DIRECTORIES and readiness is a FIELD (E-03).

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
- Resolution or deferral rationale: NO, remove them, but VERIFY FIRST. They cannot occur in this layout, and their presence is what makes a reader believe a bucket can be `reviewed`, which is precisely the assumption that produced this defect. Removing an unreachable member is observably a no-op, which is why E-03 requires searching every caller before the removal: if some caller tests a bucket for `== "reviewed"`, that caller is a second instance of this same bug and the removal would silently change its behavior. Verify, then remove, then document why the list contains only directories. Keeping them "just in case" preserves a trap for no benefit, since a future layout change that introduces such directories would touch this list anyway.

### OQ-03: Should the fix live in `edge_satisfied` or in `plan_bucket`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IN `edge_satisfied`. `plan_bucket` answers a narrow and honest question, "which lifecycle directory is this path in", and it answers it correctly; teaching it to read file contents would make a path-inspection helper do IO and would change the meaning of every existing caller's result. The defect is that `edge_satisfied` asked `plan_bucket` a question it cannot answer (what is this plan's readiness) rather than that `plan_bucket` answered wrongly. Fixing it at the call site keeps each function honest and confines the change to the one caller whose question was wrong; E-03's vocabulary correction is documentation hygiene at the helper, not the fix.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the changed external-target branch. Show THREE probes: `pending/` + `Status: reviewed` under a review action SATISFIES; `pending/` + `Status: to-review` REFUSES; an unreadable or absent status REFUSES. Quote the comment stating the precedence rule. Confirm by inspection that `_read_status` is the already-imported reader and that no second reader or regex was added.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste an execute-action edge against a `pending/` + `Status: reviewed` target REFUSING, and against an `executed/` target SATISFYING. Paste a diff or a statement confirming the execute path's behavior is unchanged from today, and state in one sentence why an execute edge legitimately needs the terminal directory (it consumes the prerequisite's work).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `plan_bucket`'s corrected list and its updated docstring. PASTE THE CALLER SEARCH: every caller of `plan_bucket`, with a statement for each about whether it compares against `reviewed` or `approved`. If any does, name it and state what you did. Paste a probe showing a real path's bucket is UNCHANGED for each remaining member.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL output of all seven matrix cases. Paste the measured-case fixture (`ybkmzp` / `tm2cz8`) SATISFYING, AND the same fixture against the PRE-FIX code REFUSING with the original message, so the contrast is demonstrated rather than asserted. Paste the in-queue-path test proving that branch is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste a real review run on BOTH hosts whose external prerequisite is `pending/` + `Status: reviewed`, proceeding rather than reporting `dependency-blocked`. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is EMPTY. If the agy host could not be demonstrated, SAY SO PLAINLY rather than inferring from the oc result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the four paths in `Scope-Paths`. Do NOT relax what an EXECUTE edge requires. Do NOT modify the in-queue dependency branch or `check_engine.evaluate_ipd_dependencies`. Do NOT make `plan_bucket` read file contents (OQ-03). Do NOT create `reviewed/` or `approved/` directories. Do NOT edit `agy_runipd.py`: it binds these symbols rather than defining them, so the fix reaches it without an edit. Do NOT edit spec `25kzda`, and never its finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT and `oc_runipd.py` is the highest-contention file in it: run `aw runs` before starting, and if it is being changed under you and the two sets of changes cannot be safely combined, STOP and report rather than overwriting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. Judge on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.

THE ITEM THAT MATTERS MOST IS V-02. This change makes a gate accept MORE, which is the direction where a mistake lets real work proceed against an unmet prerequisite. The relaxation must apply to a REVIEW action ONLY: an execute turn consumes its prerequisite's commits, so satisfying its edge on a merely `reviewed` plan would dispatch it against a base that lacks the work it depends on. If you find the execute path accepting a non-terminal target, stop.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find `edge_satisfied`, its external-target branch, `plan_bucket`, `_read_status`'s import, and `reconcile_disposition`'s review branch by name.

On completion, close backlog `yf9fj9`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited.
