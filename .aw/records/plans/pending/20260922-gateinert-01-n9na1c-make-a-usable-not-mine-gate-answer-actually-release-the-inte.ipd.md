# IPD: Propagate a usable gate answer to the post-merge gate so an attributed-away failure is not re-blamed after the merge

- Date: 2026-09-22
- Kind: child
- Concern: A lane's suite failure is adjudicated TWICE by two independent gates, and the agent's answer reaches only the first, so a failure the agent correctly attributed away is silently re-litigated after the merge and refuses the lane anyway. MEASURED on item `ld8lb3` in run `run-20260922T024054Z-2245533`. GATE 1 is the per-lane suite signal: the agent was asked, answered `not-mine`, the record shows `answer: not-mine` with `usable: True`, and the release WORKED exactly as documented - `attempts[0]["integration_detail"]` ends "RELEASED by the agent's gate answer (not-mine)", `attempts[0]["finalized"]` is `True`, and the plan genuinely reached `executed/` on the lane branch (commit `78891bde`). GATE 2 is the POST-MERGE revalidation inside `runner_shared.make_integration_validation_runner`, reached later through `runner_shared.integrate_lane_branch`; it re-runs the suite on the merged tree and refuses on its own authority, consulting NEITHER the answer nor the baseline. The item's final status is `merge-refused`.
  THE ANSWER WAS WELL-FOUNDED, which is what makes the second adjudication a defect rather than a safeguard. The agent named `except Exception: pass` in `runner_shared` inside the region `tests/test_defect_report.py` fences, identified the commit that introduced it (`894d7924`, landed after the lane's base), proved it failing at its own base commit `301a1d8fbc15`, re-ran the node id with its own four source changes stashed out to show the failure persisting, and filed it as backlog `p9ag41` rather than opportunistically fixing another agent's code. That is precisely the good-faith attribution the feature exists to honor. It was honored once and then overridden by a gate that never saw it.
  THIS IS DELIBERATELY NARROWER THAN THIS PLAN'S ORIGINAL FILING, which claimed the release was inert. That claim is retracted in the backlog item's own history: the release is NOT inert, it simply governs `integration.earned` (and therefore self-finalize) and has no channel to the post-merge gate. Stating it correctly matters because it changes the fix from "make the release work" to "give the answer a channel to the second gate".
  THE SECOND CLAIM IN THIS PLAN'S ORIGINAL FILING IS FALSE AND IS RETRACTED HERE, because it drove an entire E-item and a `Scope-Paths` widening. The filing said sibling item `65cuw0` "hit the SAME combined-red refusal in the same run with `integration_gate_answer` equal to `null`, meaning it was never asked at all", and inferred that "the ask is not reliably reached". MEASURED at review from the same `state.json`: `65cuw0`'s suite check `passing` is `True` with `exit_code` 0 and an EMPTY failures list (`8118 passed, 3 skipped, 2 xfailed`), and its `integration_signal` is `driver-run-suite` (`INTEGRATION_EARNED_BY_SUITE`), NOT `suite-failed`. Its gate 1 therefore EARNED integration outright, and `gate_answer_is_warranted` returns `(False, 'integration was earned; there is nothing to answer')` for exactly those recorded values, verified by calling the real predicate at review. So `65cuw0` was never asked because there was NOTHING TO ASK: no failure existed at gate 1. A `null` answer record is the CORRECT record for it. The two items did not hit "the SAME refusal" at gate 1 at all; they converged only at GATE 2, which refused them both. There is no ask-reachability defect, and E-02/E-04's ask-reachability work is removed rather than carried on a false premise.
  THE REAL SHAPE `65cuw0` REVEALS IS WORSE FOR THIS PLAN, NOT BETTER, AND IT BOUNDS THE FIX. An item can reach gate 2 having never been asked, because it never failed at gate 1. Such an item has NO answer and NO attributed id set, so this plan's channel carries nothing for it and it still refuses. That is correct and it must stay correct, but it means this plan rescues strictly ONE of the two measured stranded lanes. The other is rescued only by sibling `tgyfs2`'s baseline subtraction, which is why that plan carries `Priority: high` and this one `medium`.
- Scope: Give the recorded gate answer a channel to the post-merge revalidation gate, so failing ids the agent ATTRIBUTED AWAY with a usable `not-mine` answer do not drive a post-merge refusal. EXCLUDES the baseline-subtraction fix (sibling plan `tgyfs2`, backlog `fuk1mr`), which handles ids that were ALREADY red; this plan handles ids no baseline can catch (a failure that landed on main mid-turn, a flake, an order-dependence). EXCLUDES ask-reachability, whose premise was measured FALSE at review (see the Concern). Adds no new refusal kind, no new status, and no new answer token.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_gate_answer_propagation.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:tgyfs2
- Status: approved
- Readiness: go-pending-approval
- Set: gateinert
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n9na1c
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: c74dm7

## Workflow history
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): status set to reviewed

- 2026-09-22 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. THE DEFECT IS REAL AND REPRODUCES: `ld8lb3`'s answer record carries `answer: not-mine`, `usable: True`, `asked: True`, and a one-id `failing_tests` set, its `integration_released_by_answer` is `not-mine`, and gate 2 then refused it with `measured: True` on a post-merge failing set IDENTICAL to that one id. PR-001 (BLOCKER): THE PROPOSED SUBTRACTION IS THE COMPARISON THAT ALREADY INVERTED THIS GATE ONCE (`32ij2j`, pinned by `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`). Measured at review: a genuinely red post-merge run whose text yields no parseable ids gives an EMPTY merged set, so "a red consisting ONLY of attributed ids" is vacuously true and a tree that broke everything INTEGRATES. E-04 now requires an empty merged set on a non-passing suite to REFUSE. PR-002 (BLOCKER): THE 40-LINE CAP MAKES THIS PLAN FAIL OPEN, which is worse than the over-refusal it causes in sibling `tgyfs2`. Measured: 45 attributed pre-existing failures plus one genuine lane regression both cap at 40, the regression is TRUNCATED OUT of the merged list, the subtraction finds nothing new, and the gate passes a lane that introduced a failure. E-04 now refuses whenever either list is at the cap. PR-003 (BLOCKER): a `fixed` answer carries a NON-EMPTY pre-repair `failing_tests` set AND `release: True`; an answer-agnostic read would clear exactly the ids whose repair did not survive the merge. E-03/E-04 now gate strictly on the `not-mine` token. PR-004 (HIGH): E-02's ask-reachability premise is FALSE - `65cuw0` earned integration at gate 1 (`exit 0`, `8118 passed`, signal `driver-run-suite`) and the real `gate_answer_is_warranted` returns "integration was earned; there is nothing to answer" for its recorded values, so the ask was correctly never reached; E-02 and E-04's reachability clause are REMOVED and the Concern retracts the claim. PR-005 (HIGH): this plan releases a red suite on an agent's assertion at a gate spec `25kzda` Section 5.1 names as NOT relaxed by the attribution exception, so it REQUIRES a declared spec amendment; the spec path is now in `Scope-Paths` and new E-06 owns the amendment. PR-006 (HIGH): E-03 proposed a channel that ALREADY EXISTS (`item[GATE_ANSWER_RECORD_KEY]` is written by `execute_item_core` before `val_runner` is built, and `failing_tests` already holds the id set), so E-03 is rewritten as a pure reader plus a normalizer rather than a new write. PR-007 (MEDIUM): the deferral re-attempt path passes `dict(item)`, a SHALLOW copy, so a read works but any record write is LOST; E-04 now states which it depends on. PR-008 (MEDIUM): the tree-keyed revalidation cache would serve an answer-relative verdict across items, the same trap sibling `tgyfs2` raised as its OQ-03. PR-009 (MEDIUM): this plan and `tgyfs2` edit the SAME six-return-path function with no declared edge; `Item-Dependencies` is now `executed:tgyfs2` and new E-07 owns the composition proof. PR-010 (LOW): `resolve_lane_endpoints` was verified to resolve `ld8lb3`'s real endpoints and the merge result was verified IDENTICAL to the lane head tree, so V-04's replay is achievable as written. `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after.
- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `c74dm7`, inheriting its `Blocks-Release: next` gate. THE ITEM'S ORIGINAL DIAGNOSIS WAS WRONG AND THIS PLAN CORRECTS IT rather than inheriting it: the filing said a `not-mine` release "has no effect", and the attempt record disproves that (`finalized: True`, plan reached `executed/` on the lane, detail records the release). The true shape is two independent gates where the answer reaches only the first. The correction is recorded in the backlog item's own history and the item's priority was lowered high -> medium accordingly, because the primary cause of the stranded lanes is `fuk1mr` and this is the second line of defense rather than the trigger.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one adjudication final. When an agent supplies a usable, recorded answer attributing a suite failure away from its own work, that answer must survive the merge rather than being re-decided by a later gate that cannot see it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the true mechanism before changing it

- [x] E-01 Document the TWO-GATE path in one place in `runner_shared`, by symbol, stating which gate each of the four answers governs today and which it does not. This is a prerequisite rather than bookkeeping: the backlog item's original diagnosis was wrong precisely because this path was not written down anywhere, and the in-code comment at the answer-consequence block currently describes only gate 1 while reading as though it describes integration as a whole.
  ALSO RECORD THE THIRD CASE, which review measured and which the original filing mistook for a defect: an item can reach gate 2 having NEVER BEEN ASKED, because it never failed at gate 1. `65cuw0` is that case (`exit 0`, `8118 passed`, signal `driver-run-suite`). Such an item has no answer, carries no attributed set, and must keep refusing on gate 2's own verdict. Writing this down is what stops the next reader re-deriving the false "the ask is unreliable" conclusion from a `null` answer record.
  - Depends on: none
  - Expected outcome: a comment block naming `integration_is_earned`/`integration.earned` as gate 1 and `make_integration_validation_runner` (via `integrate_lane_branch`) as gate 2, stating that an answer reaches only the former today, and naming the never-asked-because-green case explicitly.
  - Execution state: performed
- [x] E-02 State, in the same block, the THREE measured ways this plan's subtraction can lie, each with the guard that closes it, BEFORE writing the consumer. This replaces the removed ask-reachability investigation, whose premise review measured false; it is not bookkeeping, because every one of the three was reachable in the authored design and two of them fail OPEN.
  (a) AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS NOT "NOTHING NEW". This is the `32ij2j` inversion, pinned by `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`, whose own docstring records that plan comparing failing sets as a subset over an always-empty string so that "every lane passed including one that broke everything". The always-empty read was SHIPPED in `run_suite_check` until `h5pyqa`. Measured at review: with the merged list `()` and one attributed id, "a red consisting only of attributed ids" is vacuously TRUE and the tree integrates.
  (b) EITHER LIST AT THE TRUNCATION CAP MAKES THE SUBTRACTION UNSOUND, and here it fails OPEN. `oc_runipd.extract_suite_failures` stops at `SUITE_FAILURE_LINE_LIMIT` (40) in first-seen order. Measured at review: 45 attributed pre-existing failures plus ONE genuine lane regression both cap at 40, the regression is truncated OUT of the merged list, the subtraction finds nothing new, and a lane that introduced a failure passes. Note this is the OPPOSITE sign from sibling `tgyfs2`, where the cap causes over-refusal; the same cap is a safety hole here and merely unreliable there, because this plan's comparison licenses a PASS.
  (c) ONLY THE `not-mine` TOKEN MAY LICENSE A RELEASE. Measured at review: a `fixed` answer that earned a passing re-run carries `release: True` AND a NON-EMPTY `failing_tests` set holding its PRE-REPAIR failures. An answer-agnostic read of `failing_tests` would therefore clear exactly the ids whose repair did not survive the merge.
  - Depends on: E-01
  - Expected outcome: the three rules are stated in-code beside the consumer, each citing the measurement or the test that establishes it, so a later refactor cannot re-derive any of them away.
  - Execution state: performed

### Task group 2: the channel

- [x] E-03 Read the ATTRIBUTED-AWAY failing id set from the answer record ALREADY on the item, and normalize it for comparison. THE CHANNEL ALREADY EXISTS AND MUST NOT BE REBUILT: `execute_item_core` writes `item[GATE_ANSWER_RECORD_KEY] = gate_outcome.record` strictly BEFORE the integration block builds `val_runner`, and `gate_answer_record` already persists the id set as `failing_tests` (verified at review by driving `perform_gate_answer` and reading the record back). So this item adds a READER and a NORMALIZER, not a write, and adds no new key, no new injection, and no second vocabulary for the ids.
  GATE THE READ ON THE ANSWER TOKEN, NOT ON THE PRESENCE OF THE SET. The set is populated for EVERY answer including `fixed`, `mine` and `needs-human` (it is what the agent was shown), so a reader keyed on "is `failing_tests` non-empty" releases on answers that must never release. Require `answer == not-mine` AND `usable` true; treat every other token, an absent record, and an unusable verdict as carrying NO attributed set.
  NORMALIZE BY NODE ID, and toward REFUSING. Both sides flow through `extract_suite_failures`, whose lines are `^(?:FAILED|ERROR)\s+\S.*$`, so a line carries the node id plus whatever trailing message pytest appended: strip the trailing message, keep the `path::Class::test` node id, keep the `FAILED` versus `ERROR` distinction rather than collapsing it, and do NOT normalize away a parametrization suffix (`test_x[a]` and `test_x[b]` are different failures). A line that cannot be parsed into a node id is an UNMATCHABLE id that is always treated as NOT attributed, so an unparseable post-merge line refuses rather than vanishing from the difference.
  - Depends on: E-02
  - Expected outcome: a pure helper that, given an item, returns the attributed node-id set for a usable `not-mine` and an EMPTY set for `fixed`/`mine`/`needs-human`/absent/unusable; with every existing key on the record unchanged and nothing new written to the item.
  - Execution state: performed
- [x] E-04 Consume that set in the post-merge revalidation verdict so a merged-tree red consisting ONLY of attributed-away ids passes, while any unattributed id still refuses. Apply it at EXACTLY ONE POINT and enforce E-02's three guards there.
  THE ONE APPLICATION POINT is the measured-red verdict after `suite_check`, i.e. the `passed = bool(getattr(result, "passing", False))` path. `_runner` has SIX return paths and only that one is a measured red. The other five must be untouched, each for its own reason: the `validate` branch returns True with `skipped=True` before any suite runs, because `integration_is_earned`'s two modes are ALTERNATIVES and the factory's docstring records 14 tests going red when that distinction was missed; the no-`suite_check`, unresolvable-base/head, unmaterializable-merge and exception paths all carry `measured=False`, and clearing a failure against a measurement that never happened is meaningless. The `pytest` exit-5 path already forces `passed=True` and clears `failures`, so it must short-circuit BEFORE the comparison rather than be fed an emptied list that guard (a) would then have to catch.
  REFUSE, NOT RELEASE, ON EVERY UNKNOWN. An empty merged failing list on a non-passing suite REFUSES (guard a). Either list at the 40-line cap REFUSES (guard b), detected by length and never by parsing prose. A non-`not-mine` or unusable answer carries no attributed set and therefore REFUSES exactly as today (guard c). An absent answer record leaves today's verdict byte-identical.
  READ-ONLY ON THE ITEM, and say so because one call path makes it matter. The deferral re-attempt path passes `dict(item)`, a SHALLOW copy (verified at review in both hosts' `validation_runner_for` lambdas), so a READ of the answer record works there while any WRITE lands on the copy and is LOST. This item must depend only on the read. If it also needs to record WHY it released, that record must go through the existing `_record_revalidation` reason string, which is written to the item the factory was handed and is already best-effort.
  THE CACHE IS KEYED ON THE MERGED TREE, NOT ON THE ANSWER. `cache[tree_id]` stores `{passed, reason, measured}` and serves it wholesale to any item reaching the same merge result, so once the verdict depends on a PER-ITEM answer a cached verdict can be served to an item that answered differently or not at all. Either include the attributed-set identity in the key or cache the raw failing-id set and re-derive the judgement per item. State which you chose and why. This is the same trap sibling `tgyfs2` raised as its OQ-03 and resolved to the second option; choosing differently here would make the two fixes disagree about what the cache means.
  - Depends on: E-03
  - Expected outcome: replaying `ld8lb3`'s recorded answer and merged failing set yields a PASS rather than `merge-refused`; adding one unattributed id yields a refusal naming ONLY that id; an empty merged list on a red suite refuses; either list at the cap refuses; a `fixed`/`mine`/`needs-human`/absent answer leaves today's verdict unchanged.
  - Execution state: performed

### Task group 3: the guard

- [x] E-05 Add a regression file pinning the propagation and its limits, including SEVEN anti-fail-open controls: `mine` releases nothing, `needs-human` releases nothing, `fixed` releases nothing THROUGH THIS PATH (even though it carries a non-empty set and `release: True` at gate 1), an unusable answer releases nothing, an absent answer preserves today's verdict, an EMPTY merged failing list on a non-passing suite releases nothing, and either list at the 40-line cap releases nothing. Drive the real functions rather than reimplementing the predicate.
  THE LAST THREE ARE THE MOST IMPORTANT CASES IN THE FILE and each was measured reachable at review, so each needs a constructed fixture rather than an assertion about intent: an empty-list red run, a 45-attributed-plus-1-regression pair that both truncate at 40, and a `fixed` answer with a passing re-run. State that ranking in the file's docstring, naming `32ij2j` for the first.
  - Depends on: E-04
  - Expected outcome: the file is RED against pre-fix source and GREEN after; each of the seven controls FAILS if the corresponding case is ever made to release.
  - Execution state: performed

### Task group 4: the contract and the composition

- [x] E-06 Amend spec `25kzda` Section 5.1 to admit the post-merge gate as a second place the attribution exception applies, and say why. THIS IS REQUIRED, NOT OPTIONAL: Section 5.1 currently states "the merge-and-revalidate gate ... likewise untouched" and "This exception adds an ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate", and this plan makes the exception govern a SECOND decision at a gate the spec names as untouched. Shipping the code without the amendment would leave the approved contract contradicting the runner, which is the drift a declared spec edit exists to prevent.
  KEEP THE EXCEPTION'S CONJUNCTIVE CONDITIONS AND ITS HONEST LIMIT VERBATIM. The amendment widens WHERE an already-admissible answer applies; it must not widen WHICH answers release, must not touch the `fixed`-needs-an-observed-re-run rule, and must not weaken the captured-evidence requirement. State the three guards from E-02 in the spec too, since they are now part of what makes the exception admissible at this gate.
  DO NOT TOUCH THE BASELINE RULING. The maintainer's 2026-09-08/2026-09-20 ruling that nothing may refuse on the strength of a BASELINE is a different rule about a different artifact, and `runner_shared`'s own comment block plus `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` pin it. This plan consults the ANSWER, never the baseline.
  - Depends on: E-04
  - Expected outcome: Section 5.1 names both gates, the three guards are recorded as conditions of admissibility, a `## Workflow history` note records the amendment and its reason, and the exception's conditions and honest limit are unchanged.
  - Execution state: performed
- [x] E-07 Prove the COMPOSITION with sibling `tgyfs2` on the merged result, since both plans modify the same `_runner` verdict and this plan declares `Item-Dependencies: executed:tgyfs2`. Run both fixes together and show the four-way matrix: a failing id that is in the baseline only, in the attributed set only, in both, and in neither.
  THE ONLY ACCEPTABLE COMPOSITION IS A UNION OF TWO EXCUSES OVER ONE REFUSAL. An id excused by either the baseline or the answer is not new; an id excused by neither still refuses. Verify specifically that composing them does not produce a THIRD unknown-handling rule: both plans make an unknown REFUSE, and a composition that turns two refusing unknowns into a pass would be the `32ij2j` inversion arriving by a new route.
  - Depends on: E-05, E-06
  - Expected outcome: the four-way matrix pasted from a real run of the composed code, with the in-neither case refusing and the unknown cases still refusing.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The four answers and their consequences are already defined in ONE comment block in `runner_shared` above `GATE_ANSWER_RECORD_KEY`, which states `not-mine -> RELEASE this attempt's integration.earned`. Read precisely, that line is TRUE and scoped to gate 1; it is the absence of any statement about gate 2 that misleads. E-01 must extend that block rather than write a competing description elsewhere.
- Only `not-mine` releases on the answer alone; `fixed` earns a suite RE-RUN and the re-run decides. This plan must preserve that asymmetry exactly, since collapsing `fixed` into an answer-only release would let a claim substitute for a measurement.
- `record_refusal` is the ONE refusal writer and `needs-human` already routes through it so the existing diagnostics block renders it. No new renderer or refusal code is needed here.
- THE CHANNEL THIS PLAN NEEDS ALREADY EXISTS. `execute_item_core` writes BOTH `attempt[GATE_ANSWER_RECORD_KEY]` and `item[GATE_ANSWER_RECORD_KEY]`, and it does so strictly BEFORE the integration block that builds `val_runner`; `gate_answer_record` already persists the id set as `failing_tests`. So the executor must ADD A READER, not a write, and must resist inventing a second key (that is the `render_stream` F-4 producer/reader drift this module's comments cite twice).
- `_runner` HAS SIX RETURN PATHS and only ONE is a measured red. The five others are the `validate` short-circuit (True, `skipped=True`), no `suite_check` (False, `measured=False`), unresolvable base/head (False, `measured=False`), the cache hit, and the unmaterializable-merge path (False, `measured=False`), plus the `pytest` exit-5 override that forces `passed=True` and clears `failures`. The `measured` flag is the `l2mzxn` honesty distinction between "the tree is red" and "the harness could not ask", and a comparison applied to the latter is meaningless.
- BOTH HOSTS' DEFERRAL RE-ATTEMPT PATHS PASS `dict(item)`, a SHALLOW COPY, into `validation_runner_for`. A read of the answer record works through it; a write is lost. Verified at review in both `oc_runipd` and `agy_runipd`.
- `extract_suite_failures` CAPS AT `SUITE_FAILURE_LINE_LIMIT` (40) in first-seen order, while `pyproject.toml` `addopts` carry `-n auto --dist=worksteal` plus random ordering. Any comparison treating its output as a COMPLETE set is unsound past 40 failures, and in THIS plan the unsoundness fails OPEN.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The release is NOT inert; the original filing was wrong | `attempts[0]["finalized"] == True`, detail ends "RELEASED by the agent's gate answer (not-mine)", plan reached `executed/` on lane commit `78891bde` |
| F-2 | Two independent gates adjudicate the same failure | gate 1 `integration_is_earned`/`integration.earned`; gate 2 `make_integration_validation_runner` via `integrate_lane_branch` |
| F-3 | The answer has no channel to gate 2 | the post-merge factory reads neither the answer record nor the baseline; its verdict comes solely from the merged-tree run |
| F-4 | The answer was well-founded | agent cited the introducing commit `894d7924`, proved the failure at base `301a1d8fbc15`, reproduced it with its own changes stashed out, and filed `p9ag41` |
| F-5 | RETRACTED AT REVIEW: there is NO ask-reachability defect. `65cuw0` was not asked because it never failed at gate 1 | `65cuw0` suite check `passing: True`, `exit_code: 0`, `failures: []` (`8118 passed`), `integration_signal: driver-run-suite`; the real `gate_answer_is_warranted` returns `(False, 'integration was earned; there is nothing to answer')` for those values |
| F-6 | The final status contradicts the honored answer | `integration_released_by_answer: not-mine` on an item whose `status` is `merge-refused` |
| F-7 | The `32ij2j` inversion is reachable in the authored design and FAILS OPEN | with a merged failing list of `()` and one attributed id, "a red consisting only of attributed ids" is vacuously true; `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` exists for this exact incident |
| F-8 | The 40-line cap FAILS OPEN here, hiding a genuine regression | measured: 45 attributed pre-existing failures plus 1 lane regression both cap at 40, the regression is truncated OUT of the merged list, the subtraction finds nothing new, and the lane passes |
| F-9 | A `fixed` answer carries a non-empty attributed set AND `release: True`, so an answer-agnostic read fails open | measured by driving `perform_gate_answer` with `fixed` and a passing re-run: `release: True`, `failing_tests` holds the PRE-REPAIR ids |
| F-10 | This plan releases a red suite at a gate spec `25kzda` names as untouched, so it REQUIRES a spec amendment | Section 5.1: "The merge-and-revalidate gate ... likewise untouched" and "it removes no gate" |
| F-11 | This plan rescues ONE of the two measured stranded lanes, not both | `65cuw0` reaches gate 2 with no answer at all, so this plan's channel carries nothing for it; only `tgyfs2`'s baseline subtraction rescues it |
| F-12 | The replay V-04 demands is achievable: the endpoints resolve and the merge result is the lane head tree | `resolve_lane_endpoints` returns base `301a1d8fbc15` / branch `aw/lane/ld8lb3`; `git merge-tree --write-tree` gives tree `9ec0a5be8e52`, IDENTICAL to the lane head tree, and matching the `tree` recorded in `post_merge_revalidation` |

## Proposed changes (ordered, validatable)

1. Write down the two-gate path by symbol, extending the existing answer-consequence block, including the never-asked-because-green case (E-01).
2. State the three measured ways the subtraction can lie, each with its guard (E-02).
3. Read and normalize the attributed id set from the answer record that already carries it, gated on the `not-mine` token (E-03).
4. Consume it at the single measured-red return path, refusing on every unknown (E-04).
5. Pin propagation plus seven anti-fail-open controls (E-05).
6. Amend spec `25kzda` Section 5.1 to admit the second gate (E-06).
7. Prove the composition with sibling `tgyfs2` on the merged result (E-07).

## Deferred / out of scope (with reason)

- Baseline subtraction in the post-merge gate: sibling plan `tgyfs2` (backlog `fuk1mr`) owns it. The two are complementary and must not be merged into one change: a baseline covers ids that were already red, an answer covers ids attributed away for reasons no baseline records.
  - Carrier-Evidence: .aw/records/plans/executed/20260922-revalbase-01-tgyfs2-subtract-the-measured-suite-baseline-before-declaring-combin.ipd.md
  - Carrier-Note: CHANGED AT EXECUTION from `- Carrier: fuk1mr` to cited evidence, because the obligation was DISCHARGED between authoring and execution and the carrier field then became a false claim rather than a handoff. At authoring, `fuk1mr` was live and naming it was correct. It is now `done` and `tgyfs2` is `executed` (this plan's own `- Item-Dependencies: executed:tgyfs2` is what required that before this plan could start), so `aw ipd lint --phase pre-transition` correctly refused the row: "carrier fuk1mr resolves only to a terminal/hidden artifact (done); nothing revisits it". Pointing a reader at a closed item would imply work is still pending when it has shipped. The cited executed plan IS the deferral's resolution and is resolvable in-tree, which is the SATISFIED escape rather than a weakening of the rule; the deferral itself was never in this plan's scope and E-07 proves the two arms compose.
- `reattempt_deferred_integrations`' accepted-and-ignored `validation_runner_for` (backlog `iv4n2c`): a different inert-injection defect in the same area, latent today.
  - Carrier: iv4n2c
- Any change to the answer VOCABULARY, the question text, or `fixed`'s re-run semantics: this plan adds a channel for an existing answer and deliberately changes no adjudication rule.
  - Carrier-Declined: DELIBERATELY NOT WANTED, not postponed. The four-token vocabulary and `fixed`'s observed-re-run rule are the maintainer's 2026-09-20 rulings, and spec `25kzda` Section 5.1 states them as the conditions that make the attribution exception admissible at all. Filing a carrier would assert that changing them is pending work, when the correct future action is to keep NOT changing them; E-06's amendment is explicitly required to preserve them verbatim.
- Making `mine` or `needs-human` releasable: explicitly forbidden, and pinned as controls in E-05. Those answers refuse by design.
  - Carrier-Declined: A PROHIBITION, NOT A DEFERRAL. There is no outstanding work to carry: the desired end state is that these never release, E-05 pins it as two of its seven controls, and an item asserting it as pending work would invite a future agent to implement the thing the controls exist to prevent.
- ASK-REACHABILITY: removed rather than deferred, because review measured its premise FALSE. `65cuw0` earned integration at gate 1 and so had nothing to be asked about; the ask fired exactly when it should. There is no defect here to defer, and leaving it as a deferral would imply an open question that the evidence closes.
  - Carrier-Declined: NO DEFECT EXISTS, so nothing can carry it. Measured at review: `65cuw0`'s suite check is `passing: True` with `exit_code: 0` and an empty failures list, its signal is `driver-run-suite`, and the real `gate_answer_is_warranted` returns `(False, 'integration was earned; there is nothing to answer')` for those values. Filing a carrier would create an item whose only sound resolution is to observe that the predicate is already correct.
- ANY REFUSAL KEYED ON THE BASELINE: that is sibling `tgyfs2`'s subject and is separately governed by the maintainer's 2026-09-08/2026-09-20 ruling that nothing may refuse on the strength of a baseline. This plan consults the ANSWER and never the baseline, which is why it needs a spec amendment and `tgyfs2` needs none.
  - Carrier-Declined: A STANDING RULING, not outstanding work. The constraint is already pinned in code (`runner_shared`'s baseline comment block) and in a test (`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`), so there is nothing to hand off; the obligation on this plan is to not violate it, which E-03's answer-only read discharges.

## Scope check

- Over-scope: none. Three paths, one a new test file and one a REQUIRED spec amendment (E-06, F-10).
- Under-scope: the spec path was ADDED at review. Section 5.1 of `25kzda` states the merge-and-revalidate gate is untouched by the attribution exception, and this plan makes the exception govern it, so shipping the code without the amendment would leave an approved contract contradicting the runner. Declared in `Scope-Paths` so both runners announce the spec edit before the run starts and the finalize scope gate can reconcile it.
- SEQUENCING: this plan and sibling `tgyfs2` modify the SAME `_runner` verdict in the SAME function. `Item-Dependencies: executed:tgyfs2` was added at review so the runner orders them; without it the queue could dispatch them in either order and the second to land would rebase onto a function its author never read. E-07 owns the composition proof.

## Required tests / validation

- `python3 -m pytest tests/test_gate_answer_propagation.py` GREEN after, and RED before, the before-run produced by reverting only `agent_workflows/runner_shared.py` while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- A REPLAY of `ld8lb3`'s recorded answer plus merged failing set through the real post-merge factory, showing it passes; and the same with one unattributed id added, showing it refuses and names ONLY that id.
- The SEVEN anti-fail-open controls each demonstrated FAILING when the corresponding case is forced to release, with the empty-list, at-the-cap and `fixed` cases called out as the three that were measured reachable.
- The composed four-way matrix with sibling `tgyfs2` (E-07), pasted from a real run.
- `aw specs check` (or the repository's spec lint) clean after the E-06 amendment, and the amendment's `## Workflow history` note pasted.

## Spec / documentation sync

A `.spec.md` AMENDMENT IS REQUIRED, and the authored plan's claim that none was expected is corrected here. Spec `25kzda` Section 5.1 ("The attributed suite-attribution exception") defines the one narrow exception under which an agent's answer may release a lane, and it states in terms that "The merge-and-revalidate gate, the scope fence, the commit-content and hook checks, and the dependency checks are likewise untouched" and that "This exception adds an ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate". This plan makes that answer govern a SECOND decision, at the merge-and-revalidate gate the spec names as untouched. Shipping the code without amending the spec would leave an `approved` contract asserting the opposite of what the runner does, which is exactly the drift a declared spec edit prevents. E-06 owns the amendment, `Scope-Paths` declares the file so both runners announce it before the run starts, and the amendment must preserve the exception's conjunctive conditions, its captured-evidence requirement, `fixed`'s observed-re-run rule, and its stated honest limit verbatim.

Separately and deliberately NOT amended: the maintainer's ruling that nothing may refuse or release on the strength of a BASELINE (recorded in `runner_shared`'s baseline comment block and pinned by `tests/test_suite_baseline.py::NothingRefusesOnTheBaseline`). That rule governs a different artifact, and this plan consults the answer record rather than the baseline.

## Open questions

### OQ-01: Should the attributed-away set be the agent's named ids, or every id in the gate-1 failure set the answer covered?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to the ids the ANSWER WAS ASKED ABOUT, i.e. the `failures` set carried into the question, and NOT a free-text set parsed from the agent's prose. The question already carries that set (`failures=getattr(suite_result, "failures", ()) or ()`), so the scope of the answer is exactly what the agent was shown, which is both auditable and impossible to widen by wording. Parsing ids out of prose would let an agent release a failure it was never asked about.

### OQ-02: If the post-merge run surfaces a failure that is attributed-away AND a new one, what happens?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: REFUSE, naming only the unattributed id(s). The presence of one legitimately attributed failure never licenses ignoring a genuine regression beside it, and the refusal message must not list the attributed ids as reasons, since that is what made the original refusals so hard to diagnose.

### OQ-03: Should the tree-keyed revalidation cache carry the attributed-set identity, or should it cache the measurement and re-derive the judgement per item?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to CACHE THE MEASUREMENT AND RE-DERIVE THE JUDGEMENT, matching what sibling `tgyfs2` resolved for the identical trap at its own OQ-03. Raised at review: `cache[tree_id]` stores `{passed, reason, measured}` and serves it wholesale to any item reaching the same merge result, so once the verdict depends on a PER-ITEM answer, a cached verdict can be served to an item that answered differently or not at all. Caching the raw failing-id set preserves the cache's actual purpose (one suite RUN per distinct merge result, which is the expensive part at ~107s) while making the cheap judgement per-item, and it keeps the two sibling plans agreeing about what the cache means. Widening the key instead is permitted only if the executor records why, since it would re-run the suite for two items sharing a tree and disagreeing on their answer.

### OQ-04: Does this plan need to record WHY it released, and can it, on the deferral re-attempt path?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to record through the EXISTING `_record_revalidation` reason string and to depend on NO new write. Measured at review: both hosts' `validation_runner_for` lambdas pass `dict(item)`, a shallow copy, so a READ of the answer record works on that path while any WRITE lands on the copy and is lost. `_record_revalidation` already writes to the item the factory was handed and is already best-effort with a suppressed exception, so an answer-released pass is explicable on the first-attempt path and silently correct on the re-attempt path. A design that REQUIRED the write to be durable would be broken on one of its two call paths, which is why this is settled before execution rather than discovered during it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the new comment block pasted, plus a grep showing it names both `integration_is_earned` and `make_integration_validation_runner`, plus confirmation by quotation that the pre-existing `not-mine -> RELEASE ... integration.earned` line is preserved rather than rewritten, plus the sentence naming the never-asked-because-green case.
  - Observed evidence: VERIFIED. The block was ADDED to the EXISTING answer-consequence comment above `GATE_ANSWER_RECORD_KEY` rather than written elsewhere, as the plan's Step-0 note requires. Pasted from the source as written:

```
# THE SEAM IS `execute_item_core`'s integration verdict, and the four answers map onto it like this:
#   not-mine     -> RELEASE this attempt's `integration.earned`, so self-finalize and integration run.
#   fixed        -> RE-RUN the suite and believe the RE-RUN. Bounded by the run's existing budget.
#   mine         -> refuse, preserve the lane. No override, deliberately.
#   needs-human  -> refuse, preserve the lane, and say in the run summary that a DECISION is awaited.
#   anything else-> refuse. Silence and malformed answers are the fail-closed direction.
#
# ---- gateinert 01 (`n9na1c`) E-01: THERE ARE TWO GATES, AND THE FIVE LINES ABOVE DESCRIBE ONE ------
#
# READ THE `not-mine` LINE ABOVE PRECISELY: it says `integration.earned`, and that is TRUE and COMPLETE
# for the gate it names. What misled a reader (and a backlog filing) was the ABSENCE of any statement
# about the SECOND gate, which made the block read as though it described integration as a whole. It
# does not. A lane's suite failure is adjudicated TWICE, by two independent gates:
#
#   GATE 1, THE PER-LANE SUITE SIGNAL: `integration_is_earned` -> `integration.earned`, resolved inside
#     `execute_item_core`. This is the gate the four answers govern. It decides SELF-FINALIZE and
#     whether an integration is attempted at all.
#   GATE 2, THE POST-MERGE REVALIDATION: `make_integration_validation_runner`, reached LATER through
#     `integrate_lane_branch`. It materializes the MERGE RESULT and re-runs the suite THERE.
#
# BEFORE THIS ITEM, GATE 2 CONSULTED NEITHER THE ANSWER NOR THE BASELINE and refused on its own
# authority. MEASURED on item `ld8lb3` in run `run-20260922T024054Z-2245533`: the agent was asked,
# answered `not-mine`, the record shows `answer: not-mine` with `usable: True`, gate 1 released exactly
# as documented (`attempts[0]["integration_detail"]` ends "RELEASED by the agent's gate answer
# (not-mine)", `finalized` is True, and the plan genuinely reached `executed/` on lane commit
# `78891bde`) - and then gate 2 re-ran the suite on the merged tree, saw the SAME one failing id the
# agent had attributed away, and refused it. The item's final status is `merge-refused`. So the answer
# was honored once and then silently re-litigated by a gate that never saw it.
#
# AND THERE IS A THIRD CASE, recorded here because its ABSENCE from this block is what let a reader
# derive a false conclusion from it. AN ITEM CAN REACH GATE 2 HAVING NEVER BEEN ASKED, because it never
# failed at gate 1. Sibling item `65cuw0` in the SAME run is that case: its suite check is
# `passing: True` with `exit_code: 0` and an EMPTY failures list (`8118 passed, 3 skipped, 2 xfailed`),
# its signal is `driver-run-suite` (`INTEGRATION_EARNED_BY_SUITE`), and `gate_answer_is_warranted`
# returns `(False, 'integration was earned; there is nothing to answer')` for exactly those recorded
# values. Its `integration_gate_answer` is `null` because there was NOTHING TO ASK, which is the
# CORRECT record; the original filing read that `null` as "the ask is not reliably reached" and
# inferred an ask-reachability defect that does not exist. Such an item carries NO answer and NO
# attributed id set, so the channel below carries nothing for it and gate 2 keeps refusing on its own
# verdict. THAT IS CORRECT AND MUST STAY CORRECT.
```

GREP over the block (counted programmatically against `inspect.getsource(runner_shared)` truncated at `GATE_ANSWER_RECORD_KEY: str`):

```
  integration_is_earned                    5 occurrence(s)
  integration.earned                       3 occurrence(s)
  make_integration_validation_runner       4 occurrence(s)
  integrate_lane_branch                    30 occurrence(s)
  65cuw0                                   9 occurrence(s)
  NEVER BEEN ASKED                         1 occurrence(s)
```

THE PRE-EXISTING LINE IS PRESERVED VERBATIM, not rewritten: `tests/test_gate_answer_propagation.py::TheTwoGatePathIsDocumentedAtTheAnswerConsequenceBlock::test_the_PRE_EXISTING_not_mine_line_is_PRESERVED_and_not_rewritten` asserts the exact string ``not-mine     -> RELEASE this attempt's `integration.earned`, so self-finalize and integration run.`` is still present, and it passes (see the 8-test class run below). That line is visible unchanged at the top of the paste above.

THE NEVER-ASKED-BECAUSE-GREEN SENTENCE IS NOT ONLY PROSE, it is checked against the shipped predicate so the retraction cannot rot: `test_the_REAL_predicate_CONFIRMS_65cuw0_was_correctly_never_asked` drives the real `gate_answer_is_warranted` with `65cuw0`'s recorded values and asserts it returns False with "integration was earned".

```
$ python3 -m pytest tests/test_gate_answer_propagation.py::TheTwoGatePathIsDocumentedAtTheAnswerConsequenceBlock tests/test_gate_answer_propagation.py::TheThreeGuardsAreStatedWithTheReasonThatEstablishesThem -o addopts="" -q
........                                                                 [100%]
8 passed in 0.56s
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the three guard rules pasted from the code as written, each showing its citation (`32ij2j` / the test name for (a), `SUITE_FAILURE_LINE_LIMIT` for (b), the `not-mine` token requirement for (c)). A guard stated without its reason FAILS this item, because the reason is what stops the next refactor removing it.
  - Observed evidence: VERIFIED. All three guards are stated in the SAME block as E-01 (immediately below it, still above `GATE_ANSWER_RECORD_KEY`), each WITH the measurement or test that establishes it. Pasted from the source as written:

```
# ---- gateinert 01 (`n9na1c`) E-02: THE THREE MEASURED WAYS THIS SUBTRACTION CAN LIE ----------------
#
# Every rule here is stated WITH THE MEASUREMENT OR TEST THAT ESTABLISHES IT, because the reason is
# what stops a later refactor deriving the rule away. This channel WIDENS when an integration is
# ALLOWED, which is the fail-open direction, and all three of these were reachable in the authored
# design; two of them fail OPEN. Sibling `tgyfs2` makes the SAME comparison fail toward OVER-refusal,
# which is recoverable. Here the same mistake merges unverified work into main.
#
#   (a) AN EMPTY MERGED FAILING LIST ON A NON-PASSING SUITE IS NOT "NOTHING NEW". This is the `32ij2j`
#       inversion, pinned by `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList`,
#       whose own docstring records that plan comparing failing sets as a subset over an ALWAYS-EMPTY
#       string so that "every lane passed including one that broke everything" (the always-empty read
#       was SHIPPED in `run_suite_check` until `h5pyqa`). Measured while authoring this: with a merged
#       list of `()` and one attributed id, "a red consisting only of attributed ids" is VACUOUSLY TRUE
#       and a tree that broke everything integrates. So an empty merged list on a non-passing suite
#       REFUSES, forever. `new_failures_since_baseline` already encodes the same rule for the baseline
#       arm and this arm inherits it rather than restating a second copy.
#   (b) EITHER LIST AT THE TRUNCATION CAP MAKES THE SUBTRACTION UNSOUND, AND HERE IT FAILS OPEN.
#       `oc_runipd.extract_suite_failures` stops at `SUITE_FAILURE_LIST_CAP` (40) in FIRST-SEEN order.
#       Measured while authoring this: 45 attributed pre-existing failures plus ONE genuine lane
#       regression both truncate at 40, the regression is truncated OUT of the merged list, the
#       subtraction finds nothing new, and a lane that INTRODUCED a failure passes. Detected by LENGTH,
#       never by parsing prose. Note the sign is OPPOSITE to `tgyfs2`'s, where the same cap causes
#       over-refusal: there it is unreliable, here it is a safety hole, because this arm licenses a PASS.
#   (c) ONLY THE `not-mine` TOKEN MAY LICENSE A RELEASE THROUGH THIS CHANNEL. Measured while authoring
#       this by driving `perform_gate_answer` with `fixed` and a passing re-run: the record carries
#       `release: True` AND a NON-EMPTY `failing_tests` set holding its PRE-REPAIR failures, because
#       `failing_tests` records what the agent was SHOWN for EVERY answer including `mine` and
#       `needs-human`. So a reader keyed on "is `failing_tests` non-empty" would clear exactly the ids
#       whose repair did not survive the merge, and would release on two answers designed to refuse.
#       `fixed` is released at gate 1 by an OBSERVED RE-RUN and never by its id set; that asymmetry is
#       the maintainer's 2026-09-20 ruling and this channel preserves it by gating on the TOKEN.
```

EACH CITATION IS PRESENT AND IS ASSERTED, not merely written: guard (a) cites both `32ij2j` and `TheExitCodeIsTheAuthorityAndNotTheList`; guard (b) cites the constant `SUITE_FAILURE_LIST_CAP` (which `test_the_cap_CONSTANT_still_equals_the_DRIVERS_extractor_limit` pins equal to `oc_runipd.SUITE_FAILURE_LINE_LIMIT`, so the plan's `SUITE_FAILURE_LINE_LIMIT` reference is satisfied through the asserted-equal shared-module name that `NoRunnerImportTests` forces this module to use) plus the measured 45-plus-1 shape; guard (c) names the `not-mine` token and the PRE-REPAIR reason. `TheThreeGuardsAreStatedWithTheReasonThatEstablishesThem` has one test per citation and all four pass (8-test run pasted under V-01).

ALSO NOTE THE REASONS ARE NOT ONLY IN THE COMMENT: each guard is restated with its reason in the docstring of `unattributed_merged_failures`, beside the code that implements it, so a reader of the function alone still sees why. The plan's own hazard statement is what this item exists for, and all three guards are demonstrated FAILING when forced under V-05.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the helper driven with FIVE recorded answer shapes (`not-mine` usable, `fixed`, `mine`, `needs-human`, absent) and its returned set pasted for each, showing NON-EMPTY for only the first; plus proof that the answer record on the item is unchanged key-for-key and that no new key was written to the item.
  - Observed evidence: VERIFIED. `attributed_away_failure_ids` driven with FIVE recorded answer shapes. The four real answers were produced by driving the SHIPPED `perform_gate_answer` (not hand-rolled records), each with the measured `ld8lb3` failing id as the set the agent was shown:

```
$ python3 (driving the real perform_gate_answer, then attributed_away_failure_ids)
not-mine     -> ('FAILED tests/test_defect_report.py::ValidatorTests::test_no_bare_except_was_introduced_around_the_new_code',)
fixed        -> ()
mine         -> ()
needs-human  -> ()
absent       -> ()
unusable     -> ()
```

NON-EMPTY FOR ONLY THE FIRST, as required. The sixth line is the unusable-verdict shape, added because `usable` is a second independent gate beside the token.

THE SET IS NORMALIZED, so the two sides compare: the record carried `... - assert x` trailing text and the returned id is the bare `FAILED <node id>`, which `test_the_SAME_node_id_with_DIFFERENT_trailing_text_MATCHES` asserts against a DIFFERENT trailing text on the merged side.

THE GATE IS THE TOKEN AND NOT THE PRESENCE OF THE SET, measured rather than assumed: `test_the_gate_is_the_TOKEN_and_NOT_the_presence_of_the_SET` drives all four answers and asserts EVERY record's `failing_tests` is non-empty, which is exactly why a presence check would release on `mine` and `needs-human`.

READ-ONLY, PROVEN BOTH WAYS. `test_the_record_is_UNCHANGED_key_for_key_and_NO_key_is_added_to_the_item` snapshots the record through `json.dumps` and the item's key set before the call and asserts both are identical afterwards. `test_the_reader_is_PURE` AST-walks the function and asserts it calls none of `_run_git`, `subprocess.run`, `open`, `Path`. Both pass:

```
$ python3 -m pytest tests/test_gate_answer_propagation.py::TheAttributedSetIsReadFromTheRecordThatAlreadyCarriesIt -o addopts="" -q
........                                                                 [100%]
8 passed in 0.94s
```

NO NEW KEY AND NO NEW WRITE ANYWHERE: the channel `execute_item_core` already writes (`item[GATE_ANSWER_RECORD_KEY] = gate_outcome.record`, strictly before the integration block builds `val_runner`) is READ, not rebuilt. `git diff` touches no line of `execute_item_core`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: the real post-merge factory driven with `ld8lb3`'s recorded inputs (base `301a1d8fbc15`, the one attributed id), pasting `passed=True` and the reason naming the attributed id; the same with one unattributed id added, pasting `passed=False` and a reason naming ONLY that new id; a non-passing suite with an EMPTY merged failing list pasting `passed=False`; either list at the 40-line cap pasting `passed=False`; and the five non-measured-red return paths shown UNCHANGED with their `measured`/`skipped` flags intact. Also state which cache strategy was chosen (OQ-03) and paste the two-items-one-tree case showing each gets its own judgement.
  - Observed evidence: VERIFIED, at EXACTLY ONE application point: the measured-red path of `_relative_revalidation_verdict`, which is the single consumer `tgyfs2` already funnels both the fresh measurement and the cache hit through.

REPLAY WITH `ld8lb3`'S REAL RECORDED INPUTS, driven through the REAL `make_integration_validation_runner` against THIS repository (base `301a1d8fbc15`, branch `aw/lane/ld8lb3`, the one attributed id, no baseline record):

```
resolve_lane_endpoints: ('301a1d8fbc15', 'aw/lane/ld8lb3', '')

REPLAY with ld8lb3's REAL endpoints:
  merged tree id : 9ec0a5be8e528c2f92d2a0d1a722997be97a9840
  gate verdict   : PASS
  measured       : True
  reason         : the merged suite is RED but every failing id in the merged tree is excused by the pre-work baseline or by the agent's usable `not-mine` answer, so this work introduced no failure (answer: every failing id in the merged tree was ATTRIBUTED AWAY by the agent's u

--- and with ONE unattributed id added ---
  gate verdict   : REFUSE
  reason         : the driver-run suite did not pass; and the merged tree is refused because 1 failure(s) are excused by NEITHER the pre-work baseline NOR the agent's `not-mine` answer: FAILED tests/test_new.py::T::test_introduced_here
  names ONLY the new id: True
```

The tree id `9ec0a5be8e52` is IDENTICAL to the one F-12 recorded at review, so this is a replay of the real merge result and not a synthetic one. `passed=True` with the reason naming the attributed id; with one unattributed id added, `passed=False` and the reason names ONLY that new id (OQ-02), asserted programmatically on the last line.

THE TWO UNKNOWN SHAPES REFUSE (from the four-way matrix run pasted under V-07, same composed code):

```
UNKNOWN: empty list, red       | REFUSE        | ... the merged suite did NOT pass yet reported NO failing ids, so the failing se
UNKNOWN: at-the-cap            | REFUSE        | ... a failing-id list is at the 40-line truncation cap (baseline 40, merged 40),
```

THE FIVE NON-MEASURED-RED RETURN PATHS ARE UNCHANGED WITH THEIR FLAGS INTACT. Each was driven with an item CARRYING a usable `not-mine`, which is the point: the answer must not leak into a path that measured nothing.

```
exit5 passed: True | baseline_comparison present: False | reason: the merge result collected NO tests (pytest exit 5), so the merge cannot have broken anyth
validate-on passed: True skipped: True suite runs: 0
green passed: True | baseline_comparison present: False
exception passed: False measured: False unmeasured(): True
no-suite_check passed: False measured: False
```

plus the unresolvable-base/head and unmaterializable-merge paths, both `measured: False`, pinned by `TheFiveNonMeasuredRedPathsAreUNCHANGED` (7 tests, all passing in the file run under V-05). The `pytest` exit-5 reading SHORT-CIRCUITS before the comparison as the plan requires, proven by the absent `baseline_comparison` block rather than by inspection.

CACHE STRATEGY (OQ-03): CACHE THE MEASUREMENT AND RE-DERIVE THE JUDGEMENT PER ITEM, i.e. option (b), matching what sibling `tgyfs2` resolved for the identical trap. NO CODE CHANGE WAS NEEDED to achieve it, which is the strongest form of "the two fixes agree about what the cache means": `tgyfs2` already converted `cache[tree_id]` to hold a MEASUREMENT (`passed`/`reason`/`measured`/`suite_passed`/`failures`/`collected_nothing`) and routes every cache hit back through `_relative_revalidation_verdict`, so adding this arm to that one function made the answer judgement per-item automatically. The key was NOT widened, so the ~107s suite still runs once per distinct merge result. Two-items-one-tree case, one answered and one never asked:

```
suite calls: 1
item WITH not-mine answer: True | cached: False
item with NO answer      : False | cached: True
```

ONE suite run, TWO different verdicts, and the second is recorded as a genuine cache HIT. Pinned by `TheCacheServesAMeasurementAndNotAPerItemJudgement::test_TWO_items_ONE_tree_get_their_OWN_judgements_from_ONE_suite_run`.

READ-ONLY ON THE ITEM, as E-04 requires for the shallow-copy deferral path: the arm depends only on `attributed_away_failure_ids` (proven pure and non-writing under V-03), and the only write is the pre-existing best-effort `_record_revalidation` reason string, which already carried this gate's explanation.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the new test file's output pasted GREEN after and RED before, the bare suite count line, and each of the SEVEN controls (`mine`, `needs-human`, `fixed`, unusable, absent, empty-merged-list-on-a-red-suite, either-list-at-the-cap) shown FAILING when forced to release. The last three are the measured-reachable ones and each needs a constructed fixture, not an assertion about intent.
  - Observed evidence: VERIFIED. New file `tests/test_gate_answer_propagation.py`, 49 tests. GREEN AFTER:

```
$ python3 -m pytest tests/test_gate_answer_propagation.py -o addopts="" -q
.................................................                        [100%]
49 passed in 1.76s
```

RED BEFORE, produced exactly as the plan's "Required tests" section specifies - the new tests copied onto PRE-FIX `agent_workflows/runner_shared.py`, obtained by adding a detached worktree at this lane's base commit `fc69807e` (so nothing in the lane was stashed or reverted):

```
$ (in a detached worktree at fc69807e, with only tests/test_gate_answer_propagation.py copied in)
$ python3 -m pytest tests/test_gate_answer_propagation.py -o addopts="" -q
30 failed, 19 passed in 2.05s
```

The 30 include `test_the_MEASURED_ld8lb3_REPLAY_now_PASSES`, every `ANTI_FAIL_OPEN` control, the whole E-03 reader class, the composition class, and the E-01/E-02 documentation assertions. The 19 that pass pre-fix are the ones pinning UNCHANGED behavior (the five fail-closed paths, the exit-5 reading, the vocabulary), which is correct: they must pass on both sides.

ALL SEVEN CONTROLS SHOWN FAILING WHEN THE CORRESPONDING CASE IS FORCED TO RELEASE. Each forcing deletes the specific guard from a COPY of the fixed source in the throwaway worktree, runs the file, and restores it.

Controls 1-5 (`mine`, `needs-human`, `fixed`, unusable, absent) share one guard - the TOKEN-and-usable check in `attributed_away_failure_ids` - so removing it is the single forcing that must break all of them, and does:

```
### FORCED: the answer-agnostic read (guard c removed): every token control must FAIL
    FAILED ...::TheAnswerReachesThePostMergeVerdict::test_ANTI_FAIL_OPEN_2_NEEDS_HUMAN_releases_NOTHING
    FAILED ...::TheAnswerReachesThePostMergeVerdict::test_a_FIXED_answer_whose_RERUN_FAILED_also_releases_NOTHING
    FAILED ...::TheAnswerReachesThePostMergeVerdict::test_ANTI_FAIL_OPEN_1_MINE_releases_NOTHING
    FAILED ...::TheAnswerReachesThePostMergeVerdict::test_ANTI_FAIL_OPEN_3_FIXED_releases_NOTHING_THROUGH_THIS_PATH
    FAILED ...::TheAnswerReachesThePostMergeVerdict::test_ANTI_FAIL_OPEN_4_an_UNUSABLE_answer_releases_NOTHING
    FAILED ...::TheAttributedSetIsReadFromTheRecordThatAlreadyCarriesIt::test_the_FIVE_answer_shapes_and_only_the_FIRST_carries_anything
    FAILED ...::TheAttributedSetIsReadFromTheRecordThatAlreadyCarriesIt::test_an_UNUSABLE_verdict_carries_NOTHING_even_saying_not_mine
    7 failed, 42 passed in 1.99s
```

Note control 5 (ABSENT) is the one case that does NOT break under that forcing, and correctly so: an absent record returns early before the token check, which is why it is asserted as EQUALITY-to-today rather than as a guard, and it is RED pre-fix in the 30-failure run above.

Controls 6 and 7, the two measured-reachable fail-open cases, each with its own forcing:

```
### FORCED: control 6 (32ij2j: empty merged list on a RED suite): drop guard (a)
    FAILED ...::test_ANTI_FAIL_OPEN_6_THE_32ij2j_INVERSION_an_EMPTY_list_on_a_RED_suite
    1 failed, 2 passed, 41 deselected in 0.62s

### FORCED: control 7 (either list at the 40-line cap): drop guard (b)
    FAILED ...::test_ANTI_FAIL_OPEN_7_EITHER_list_at_the_CAP_releases_NOTHING
    1 failed, 1 passed, 41 deselected in 0.52s
```

and the source restored, re-verified green:

```
restored. verify GREEN again:
    49 passed in 1.81s
```

THE THREE MEASURED-REACHABLE CASES EACH HAVE A CONSTRUCTED FIXTURE RATHER THAN AN ASSERTION ABOUT INTENT, as required: control 6 builds an exit-1 result with an EMPTY failures tuple and drives both the predicate and the real gate; control 7 builds 45 pre-existing failures plus one real regression, truncates both sides at 40, and ASSERTS THE FIXTURE REPRODUCES THE HAZARD before asserting the refusal (`assertNotIn(regression, merged_kept)` and `assertEqual(naive_unexcused, [])`, so a fixture that stopped reproducing the hazard fails loudly instead of passing vacuously); control 3 drives the real `perform_gate_answer` with `fixed` and a passing re-run and asserts the SURPRISING shape (a gate-1 release beside a non-empty PRE-REPAIR id set) before asserting this channel refuses it. The ranking is stated in the file's module docstring, which names `32ij2j` for the first.

BARE SUITE COUNT LINE:

```
$ python3 -m pytest
1 failed, 8940 passed, 3 skipped, 2 xfailed, 6 warnings in 137.96s (0:02:17)
```

ATTRIBUTION STATEMENT for the one failure, which is required because this change makes a safety gate more permissive. There is exactly ONE failing node id: `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. It is NOT MINE and it is NOT NEW. It asserts `OPENCODE_CONFIG_CONTENT` is ABSENT from a non-isolated turn's environment, and this turn runs with that variable SET in its own process environment, so the test observes the ambient value rather than anything this plan wrote. Proven pre-existing at this lane's base commit rather than argued:

```
$ (in a detached worktree at fc69807e, PRISTINE source, no changes of mine)
$ python3 -m pytest tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped -o addopts="" -q
E       assert 'OPENCODE_CONFIG_CONTENT' not in {'AGENT': '1', ...}
tests/test_turn_bounds.py:310: AssertionError
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
1 failed in 1.33s
```

It touches nothing this plan changes, and sibling `tgyfs2`'s own execution record names the same node id as pre-existing for the same reason. NO EXISTING TEST TURNED RED: the five suites closest to this change run clean together, which is a RUN and not an inspection:

```
$ python3 -m pytest tests/test_integration_revalidation_baseline.py tests/test_suite_baseline.py tests/test_suite_adjudication.py tests/test_gate_answer_wiring.py tests/test_runner_shared.py
421 passed in 24.45s
```

`tests/test_suite_baseline.py::NothingRefusesOnTheBaseline` is inside that 421 and still passes, so the maintainer's standing baseline ruling is intact.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: the spec diff pasted showing Section 5.1 naming BOTH gates and the three guards; quotation proving the exception's conjunctive conditions, its captured-evidence requirement, `fixed`'s observed-re-run rule and its honest-limit paragraph are unchanged; the `## Workflow history` note; and the repository's spec check reported clean.
  - Observed evidence: VERIFIED. `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` Section 5.1 amended, declared in `Scope-Paths`, and `aw specs check` clean.

THE SENTENCE THAT CONTRADICTED THE RUNNER IS GONE, and it was AMENDED rather than annotated because it was wrong as a DESIGN and not only as a description. Diff of the changed sentence:

```
-non-empty observed evidence, and the scope comparison. The merge-and-revalidate gate, the scope fence,
-the commit-content and hook checks, and the dependency checks are likewise untouched. This exception adds
-an ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate.
+non-empty observed evidence, and the scope comparison. The scope fence, the commit-content and hook
+checks, and the dependency checks are likewise untouched. This exception adds an ATTRIBUTED, REVIEWABLE
+input to the integration decision; it removes no gate.
+
+WHERE IT APPLIES: BOTH GATES THAT ADJUDICATE THE SAME SUITE FAILURE, AND THIS PARAGRAPH IS AN AMENDMENT
+(2026-09-23, plan `n9na1c`). ...
+- GATE 1, THE PER-LANE SUITE SIGNAL, decides whether an integration is attempted at all, ...
+- GATE 2, THE POST-MERGE REVALIDATION, re-runs the full suite on the MERGE RESULT and refuses on its own
+  authority. It exists because per-lane green never implies integrated green, and that remains true.
+...
+THE EXCEPTION THEREFORE GOVERNS GATE 2 AS WELL, ON EXACTLY THE SAME TERMS AND NO OTHERS. ...
+THREE FURTHER CONDITIONS ARE REQUIRED FOR ADMISSIBILITY AT GATE 2, ...
+1. A NON-PASSING SUITE THAT REPORTS NO FAILING IDENTIFIERS IS UNKNOWN, NEVER "NOTHING UNCOVERED". ...
+2. A TRUNCATED IDENTIFIER LIST MAY NOT BE SUBTRACTED. ...
+3. ONLY THE ANSWER ASSERTING THE FAILURES ARE NOT THE AGENT'S MAY RELEASE HERE. ...
+BOTH GATES REMAIN GATES. ...
```

The amendment names BOTH gates and records ALL THREE GUARDS as conditions of admissibility at gate 2, checked programmatically:

```
OK       both gates named
OK       guard a
OK       guard b
OK       guard c
```

THE EXCEPTION'S CONDITIONS AND ITS HONEST LIMIT ARE UNCHANGED, verified by presence-checking the exact strings rather than by reading:

```
OK       conjunctive conditions      "WHEN IT APPLIES, and the conditions are conjunctive."
OK       fixed observed-re-run       "An answer asserting the agent REPAIRED them / releases only on an OBSERVED PASSING RE-RUN of the full suite, never on the claim."
OK       captured evidence           "WHAT MAKES IT ADMISSIBLE IS CAPTURED EVIDENCE, NOT PROSE."
OK       honest limit                "THE HONEST LIMIT, stated so the exception is not trusted further than it holds."
OK       baseline ruling             "no programmatic gate may refuse the verdict on that basis"

stale 'merge-and-revalidate gate ... likewise untouched' removed: True
```

WHICH ANSWERS MAY RELEASE IS NOT WIDENED: the amendment says so in terms ("the closed vocabulary is unchanged, the two answers that may release are unchanged, an answer asserting a REPAIR still releases only on an OBSERVED PASSING RE-RUN and never on the claim"), and its third admissibility condition NARROWS the second gate further than the first by admitting only the not-mine answer there. The BASELINE RULING is untouched: the honest-limit paragraph is byte-identical and this plan's arm never reads the baseline, asserted by `test_NOTHING_REFUSES_OR_RELEASES_ON_THE_BASELINE_IN_THE_ANSWER_ARM`, which AST-walks both new functions and fails if either names `revalidation_baseline_for`.

`## Workflow history` NOTE, appended through the tool (`aw specs note`) and not by hand:

```
$ aw specs note .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md --message "AMENDED 2026-09-23 (plan n9na1c, backlog c74dm7): Section 5.1's attributed suite-attribution exception now governs BOTH gates ... WHAT IS UNCHANGED, deliberately and verbatim: the conjunctive conditions, the closed vocabulary, the two answers that may release, the rule that an answer asserting a REPAIR releases only on an OBSERVED PASSING RE-RUN and never on the claim, the captured-evidence requirement, and the HONEST LIMIT paragraph including the maintainer's 2026-09-08/2026-09-20 ruling that no gate may refuse on the strength of a pre-work baseline. Only WHERE an already-admissible answer applies changed. WHAT IS ADDED: three conditions required for admissibility at the second gate ..."
aw specs note: appended a history record to .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
```

SPEC CHECK CLEAN after the amendment:

```
$ aw specs check .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
aw specs check: all specs conform.
```

The spec's `- Status:` is left at `approved` and no status transition was performed: this is an amendment to an approved contract made in the same change as the behavior, which is what the declared spec edit exists for.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: the four-way matrix pasted from a real run of the composed code (id in baseline only, in attributed set only, in both, in neither), showing the in-neither case REFUSING; plus the two unknown shapes (empty merged list, at-the-cap) shown still refusing under composition.
  - Observed evidence: VERIFIED against the COMPOSED code. `tgyfs2` is `executed` and its baseline arm is present in this lane's `runner_shared.py` (`new_failures_since_baseline`, `revalidation_baseline_for`, `normalize_failure_id`, `SUITE_FAILURE_LIST_CAP`), so this matrix is a real run of BOTH fixes together through `make_integration_validation_runner`, not a simulation:

```
================================================================================================
E-07 COMPOSED FOUR-WAY MATRIX -- real run of runner_shared with BOTH fixes (tgyfs2 + n9na1c)
================================================================================================
case                           | gate verdict  | why
------------------------------------------------------------------------------------------------
id in BASELINE only            | PASS (merge)  | the merged suite is RED but this work INTRODUCED NO FAILURE, so revalidation passes: every failing id in the merged tree was ALREADY failing at the ba
id in ATTRIBUTED set only      | PASS (merge)  | the merged suite is RED but every failing id in the merged tree is excused by the pre-work baseline or by the agent's usable `not-mine` answer, so thi
id in BOTH                     | PASS (merge)  | the merged suite is RED but this work INTRODUCED NO FAILURE, so revalidation passes: every failing id in the merged tree was ALREADY failing at the ba
id in NEITHER                  | REFUSE        | the driver-run suite did not pass; and the merged tree is refused because 1 failure(s) are excused by NEITHER the pre-work baseline NOR the agent's `n
MIXED (one per arm)            | PASS (merge)  | the merged suite is RED but every failing id in the merged tree is excused by the pre-work baseline or by the agent's usable `not-mine` answer, so thi
MIXED + one in NEITHER         | REFUSE        | the driver-run suite did not pass; and the merged tree is refused because 1 failure(s) are excused by NEITHER the pre-work baseline NOR the agent's `n
UNKNOWN: empty list, red       | REFUSE        | the driver-run suite did not pass; and the merged tree is refused because the merged suite did NOT pass yet reported NO failing ids, so the failing se
UNKNOWN: at-the-cap            | REFUSE        | the driver-run suite did not pass; and the merged tree is refused because a failing-id list is at the 40-line truncation cap (baseline 40, merged 40),
```

THE FOUR REQUIRED CASES: in-baseline-only PASSES, in-attributed-set-only PASSES, in-both PASSES, IN-NEITHER REFUSES. THE TWO UNKNOWN SHAPES STILL REFUSE UNDER COMPOSITION, so two refusing unknowns do NOT become a pass and the `32ij2j` inversion does not arrive by this new route.

A FINDING THE MATRIX FORCED, worth recording because it changed the implementation. The MIXED row (rows 5-6) is not decoration: with merged `{A, B}` where `A` is in the baseline and `B` is attributed away, EACH ARM INDIVIDUALLY SAYS `regressed` (each holds the other's id as its own leftover), so composing the two BOOLEANS would REFUSE a lane that introduced nothing - reintroducing the exact defect both plans exist to remove, for the one shape that needs both of them. My first implementation did exactly that and the matrix caught it. The union is therefore PER-ID (`_compose_revalidation_excuses`), which is what rows 5 and 6 verify: mixed PASSES, and mixed-plus-one-unexcused REFUSES naming only the unexcused id.

NO THIRD UNKNOWN-HANDLING RULE WAS CREATED, asserted at the composer itself rather than inferred from the rows: an arm whose judgement is `unknown` contributes NO excuses, because its `new_ids` is meaningless by its own contract (for the absent cases it is the whole merged set, and for the vacuous-truth case it is EMPTY, which read as a leftover set would excuse EVERYTHING). `test_the_COMPOSER_reads_an_UNKNOWN_arm_as_EXCUSING_NOTHING` drives `_compose_revalidation_excuses` with two unknown arms and asserts it returns `None`, i.e. refuse.

BOTH ARMS REMAIN INDEPENDENT AND NEITHER REPLACED THE OTHER: `test_BOTH_sibling_predicates_are_STILL_PRESENT_and_INDEPENDENT` drives each predicate alone and asserts each reaches `no-regression` on its own evidence.

The whole composition class passes:

```
$ python3 -m pytest tests/test_gate_answer_propagation.py::TheCompositionWithTheBaselineArmIsAUnionOfTwoExcuses -o addopts="" -q
.......                                                                  [100%]
7 passed in 0.57s
```

And the sibling's own file is untouched and still green (inside the 421-test run pasted under V-05), so the composition did not achieve its result by weakening the baseline arm.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

THE SPECIFIC HAZARD OF THIS PLAN is that it widens when an integration is ALLOWED, which is the fail-open direction, and review measured THREE distinct routes by which the authored design reached that direction: an empty merged failing list read as "nothing new" (the `32ij2j` inversion, F-7), a genuine regression truncated out of the merged list by the 40-line cap (F-8), and a `fixed` answer's pre-repair id set read as attributed (F-9). The seven anti-fail-open controls in E-05 are therefore not optional, and an executor who cannot make all seven fail against a forced release must report that rather than proceed. Sibling `tgyfs2` makes the SAME comparison fail toward over-refusal, which is recoverable; here the same mistakes merge unverified work into main, so where the two plans disagree about how careful to be, this one is the stricter.

THE SPEC AMENDMENT IS PART OF THE WORK, NOT A FOLLOW-UP (E-06, F-10). `Scope-Paths` declares `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` so both runners announce the spec edit before the run starts and the finalize scope gate reconciles it. An executor who ships the code without the amendment leaves an `approved` spec asserting the opposite of what the runner does.

SEQUENCING IS DECLARED, NOT ASSUMED. `Item-Dependencies: executed:tgyfs2` was added at review because both plans modify the same `_runner` verdict in the same function; the runner sorts by dependency depth and re-checks the edge at dispatch, so this plan will not start before its sibling has landed. If that edge is ever removed, E-07's composition proof becomes unperformable and this plan must not execute.
