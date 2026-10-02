# IPD: Give the dependency disposition a typed in-queue signal instead of matching the word 'external' in prose

- Date: 2026-09-29
- Kind: child
- Concern: A run tells the operator that a dependency sitting in its own queue is "outside this run's queue", inverting the operator's next step, because `run_selection_policy.derive_item_disposition` picks between two disposition codes by substring-matching prose that `edge_satisfied` writes unconditionally.
- Scope: IN: (a) an OPTIONAL, explicit queue-membership signal on `run_selection_policy.derive_item_disposition` plus the three renderers that call it, which OVERRIDES the substring match when supplied and leaves it standing when not; (b) both hosts passing that signal from the queue they already hold, so a real run gets the true code; (c) stopping `runner_shared.edge_satisfied` asserting the word `external` and the clause `it is not in this run` about a target whose queue membership it never checked, replacing them with wording true of every target it can actually resolve; (d) regression tests for the in-queue and genuinely-external cases and for the unparseable-token trap. OUT: changing what `edge_satisfied` DECIDES (the maintainer's 2026-09-19 one-authority ruling stands; `by_id` stays unread by the satisfaction decision), the token-prefix verbosity of the drain path's reason strings (backlog `csjq81`), and the `dependency_not_met` / `dependency_not_met_external` NAMES, which spec `25kzda` 5.4 owns.
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/render_stream.py, tests/test_run_selection_policy.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 8mohre
- Blocks-Release: next
- Set: 8mohre
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: zhqt51
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-29 reviewed (aw set): status set to reviewed

- 2026-09-29 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED. Re-measured every finding independently at HEAD `f628be1d`; the core defect reproduces verbatim and the prescribed fix was re-prototyped from scratch. Corrected three overstated findings (F-05's row census and red-row count, F-07's guard test which no longer exists, F-09's outcome word which does not change), added F-16 (mixed-token entry) and F-17 (five human-facing consumers of the reworded string), and added E-05 case (iv) plus V-01(f). Findings and four `D-*` decisions recorded in `.aw/records/reviews/20260929-8mohre-01-zhqt51-...review.md`. No production file modified.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `8mohre`; every finding measured at HEAD `0547b0c1` and the fix prototyped in memory before being prescribed.

## Goal

Make a run's per-artifact disposition tell the truth about WHERE an unmet dependency lives, so the operator's next step is right: an in-queue prerequisite reports `dependency_not_met` ("this run may yet satisfy it, resume"), and only a genuinely out-of-queue one reports `dependency_not_met_external` ("widen the selector; no resume can help"). Today both report `external`, because the code is chosen by searching the reason PROSE for `not in this run`, a phrase `edge_satisfied` emits for every on-disk resolution failure regardless of queue membership.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the typed signal, in the pure policy module

- [x] E-01 Give `run_selection_policy.derive_item_disposition` an OPTIONAL keyword-only membership signal (an iterable of in-queue id6s, or `None`) and make it OVERRIDE the substring match when supplied. THE DEFAULT MUST BE `None` AND `None` MUST PRESERVE TODAY'S BEHAVIOR EXACTLY, which is measured rather than assumed: F-05 shows that auto-deriving the member set from the `entries` argument turns a shipped table row RED, because each row builds a single entry whose id6 is not its own dependency's target. So membership is an INPUT the caller answers, never a fact this function infers from its existing argument. Resolve each unmet token's target id6 through the shared grammar (`runner_shared.dependency_target_id6` reached by a FUNCTION-LOCAL import, because a module-level one is a genuine import CYCLE per F-07 - note F-07 also records that the test which used to police this is GONE, so nothing will catch a module-level import for you). Treat an UNPARSEABLE token as MEMBERSHIP UNKNOWN rather than as a non-member (F-06 measures such a token yielding `None`, which a naive `in` test would silently read as "external"). For a MULTI-TOKEN entry mixing an in-queue and a genuinely external edge, resolve to the IN-RUN code (fail soft toward the non-committal answer); F-16 measures this case is reachable from all three production write sites and records why the opposite direction is worse. Keep the two code CONSTANTS and their glosses untouched: spec `25kzda` 5.4 owns those names.
  - Depends on: none
  - Expected outcome: called with no membership argument the function returns byte-identical results to HEAD for all five shipped shapes; called with a membership set containing the unmet target's id6 it returns `dependency_not_met`; called with a NON-EMPTY one that excludes it, `dependency_not_met_external`; called with an unparseable token, NOT the external code; called with a mixed in-queue/external token list, the in-run code.
  - Execution state: performed

- [x] E-02 Thread the same optional signal through the three public readers in that module that consume the derivation (`render_queue_dispositions`, `summarize_dispositions`, `render_disposition_summary`), keyword-only and defaulting to `None`, and pass it down unchanged. Do NOT auto-derive it inside any of them, for E-01's measured reason. Each already receives the FULL entry sequence (F-08), so no new plumbing reaches either host beyond one argument at the call site. NOTE `summarize_dispositions` takes `refusal_reader` POSITIONALLY today (F-08's pasted signature shows it is the only one of the three without the `*`), and `render_disposition_summary` calls it positionally (`summarize_dispositions(entries, refusal_reader)`); add the new parameter AFTER a `*` so that existing positional call keeps working rather than silently binding the wrong argument.
  - Depends on: E-01
  - Expected outcome: each of the three accepts the new keyword, forwards it, and is unchanged in behavior when it is omitted.
  - Execution state: performed

### Task group 2: the hosts, so a real run gets the true code

- [x] E-03 At both hosts' single end-of-run call sites (`oc_runipd` and `agy_runipd` each call `render_queue_dispositions` then `render_disposition_summary` with `refusal_reader=refusal_of_item`), pass the membership signal derived from `state["queue"]`, which is the same object already being passed as `entries`. Also pass it at `render_stream.queue_performed_no_work`'s call to `summarize_dispositions`, so the NO-WORK verdict predicate keys on the same judgement the printed lines key on. THE REASON IS THE DOCSTRING'S CLAIM, NOT A CHANGED VERDICT: F-09 measures that this predicate returns the SAME boolean for both codes (both carry a non-`None` remedy), so no run's `Outcome:` word changes; what would become false if this leg were skipped is the docstring's assertion that it reads "the exact same judgement that the closing disposition summary reads". Do not claim in the commit message or the validation evidence that this fixes a wrong outcome word. Change no other behavior at either site and add no new import to either host.
  - Depends on: E-02
  - Expected outcome: a run whose unmet prerequisite IS a queue member prints `dependency_not_met` with the in-run remedy; one whose prerequisite is genuinely absent still prints `dependency_not_met_external`; `queue_performed_no_work` consumes the same membership signal and its boolean is unchanged for both codes.
  - Execution state: performed

### Task group 3: stop the second site asserting a fact it never checked

- [x] E-04 In `runner_shared.edge_satisfied`'s `executed:` branch, reword the refusal so it no longer claims the target is `external` nor that `it is not in this run`. It resolves the target ON DISK and deliberately does not consult queue membership, so both claims are outside what it knows; state instead what it DID establish (the target's effective status, the directory it read, and the states the consuming action requires). CHANGE ONLY THE WORDING: the `(satisfied, reason)` contract, the precedence between directory and `- Status:` field, and the two `allowed` tuples are all untouched, and `by_id` stays unread, because the maintainer's 2026-09-19 one-authority ruling governs the DECISION and this plan does not reopen it. F-10 measures that the one downstream consumer of this text (`classify_drain_block`) decides from queue membership and only PASSES the text through, so rewording cannot move its verdict. Update the two stale comments in this module that quote the old clause as evidence of an external target (in `classify_drain_block`'s section note and its `entry is None` branch) so they no longer cite a phrase the code has stopped writing.
  - Depends on: none
  - Expected outcome: no refusal text in this branch contains `external target` or `not in this run`; the branch's satisfied/unsatisfied verdict is unchanged for every case the existing suite covers.
  - Execution state: performed

### Task group 4: tests that would fail without the fix

- [x] E-05 Add regression tests to `tests/test_run_selection_policy.py` covering the FOUR cases that distinguish this fix from the status quo, each asserting the CODE by EQUALITY and not by substring: (i) the measured defect, an unmet token whose target IS in the supplied membership set, which must be `dependency_not_met` EVEN THOUGH its recorded reason still contains `not in this run` (this is the row that goes red without E-01, and it must forbid the external code rather than only require the in-run one, because `dependency_not_met` is a PREFIX of `dependency_not_met_external`); (ii) the genuinely external case, target absent from a NON-EMPTY membership set, which must stay `dependency_not_met_external`; (iii) the unparseable-token trap from F-06, which must NOT be reported external merely because no id6 could be parsed from it; (iv) F-16's MIXED token list, one in-queue edge and one genuinely external edge in the same entry, pinning the chosen fail-soft direction (the in-run code) so it is a recorded decision rather than an artifact of the `any()` spelling. Extend the shipped table only by adding rows; do not edit, weaken or delete any existing row, and do not change `_queue_entry`.
  - Depends on: E-01
  - Expected outcome: four new tests pass with the fix, and test (i) fails when E-01's override is reverted in memory.
  - Execution state: performed

- [x] E-06 Add a test pinning the property E-04 establishes: that `edge_satisfied`'s refusal for an unresolvable-on-disk `executed:` edge does NOT assert queue absence. Drive the REAL function against a temporary repository containing a `pending/` plan (as the measurement in F-01 does) and assert on the returned reason string that `external target` and `not in this run` are both absent while the target's status is still named. Assert on the returned VALUE, never by reading the function's source: a test that greps production text would pin code structure rather than behavior.
  - Depends on: E-04
  - Expected outcome: the test passes after E-04 and fails against HEAD's wording.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_selection_policy` is the PURE renderer/policy home and its module docstring plus several function docstrings record a deliberate TWO-IMPORT purity property (module-level first-party imports are exactly `selectors` and `status_set`; verified by an import-graph walk, F-07). `reason_from_refusal` and `derive_item_disposition` both document duck-typing rather than importing `render_stream` for this reason. E-01 therefore reaches `runner_shared.dependency_target_id6` through a FUNCTION-LOCAL import, which is the same route `runner_shared.edge_satisfied` itself uses for `run_selection_policy`.
- `runner_shared`'s in-code comment says a module-level first-party import is refused by a named guard (`tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`) and that a function-local import is "this module's documented route for a first-party dependency" (see the reader-import comment inside `edge_satisfied`). **THAT GUARD NO LONGER EXISTS**: F-07 measures the file absent at review HEAD, removed by the suite-trim commits. The CONVENTION still holds and this plan still follows it, on the cycle argument rather than on a test; the comment is simply stale, and this plan does not repair it because `runner_shared`'s import comments are outside the wording E-04 touches. E-04 adds no import at all.
- The disposition reason vocabulary is CLOSED and its names are transcribed from spec `25kzda` (Sections 5.4, 5.7 and 6), stated in `SKIP_REASONS`' own comment: "NOTHING IS MINTED HERE". This plan therefore changes WHICH of the two existing codes is chosen and mints no third.
- `skip_reason_text` FAILS CLOSED on an unknown code by design, so a code chosen outside `SKIP_REASONS` raises rather than rendering; this bounds E-01's blast radius to a choice between two existing members.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| id | finding | evidence |
|---|---|---|
| F-01 | **THE DEFECT REPRODUCES EXACTLY AS THE BACKLOG ITEM RECORDS IT, INDEPENDENTLY RE-MEASURED AT REVIEW HEAD `f628be1d` on a clean tree.** With BOTH the dependent and its prerequisite present in `state["queue"]`, the real `dependency_status_detailed` returns the reason `executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)`, and the real `derive_item_disposition` returns `dependency_not_met_external`, whose gloss asserts the dependency "is outside this run's queue". It is not; it is in the queue. **THE ONE REPRODUCTION TRAP, named so the executor does not lose an hour to it:** the dependent's edges must be written under the item key `dependencies`, which is the key `dependency_status_detailed` iterates (`for dep in item.get("dependencies", [])`); an entry carrying them under `item_dependencies` yields `satisfied: True, unmet: []` and the defect does NOT appear. **AND THE STRONGEST FORM OF THE EVIDENCE:** the reason string is BYTE-IDENTICAL whether the prerequisite is in the queue or absent from it, which is the decoupling proof - the producer text carries NO information about queue membership, so no substring of it can decide the code. | `tmp/pr8mohre/probe_f01b.py` on a temporary repo writing one `pending/` plan with `- Status: to-review`, building a two-entry queue, calling the real `dependency_status_detailed` then `derive_item_disposition`: prints `target IS in the queue: True`, the reason verbatim, `derive_item_disposition code: dependency_not_met_external`, `MISLABELLED: True`, then re-runs with the prerequisite ABSENT and prints `IDENTICAL REASON TEXT IN BOTH CASES? True`. |
| F-02 | **THE MISLABEL IS USER-PERCEPTIBLE BECAUSE THE TWO CODES CARRY OPPOSITE REMEDIES, not merely different words.** `remedy_for_disposition` returns, for the external code, "the dependency is outside this run's queue, so widen the selector to include it (or run it first); this run cannot satisfy the edge no matter how often it is resumed", against the in-run code's "run the dependency to its declared state first, or include it in the same selector so this run can satisfy the edge". So a reader of the mislabelled line is told resuming can never help, about an item a resume may well satisfy. That is the actionable inversion `derive_item_disposition`'s own comment predicts ("an operator's next step differs"). | Direct calls to `remedy_for_disposition` for both codes, printed side by side; both are non-`None` and neither is in `DISPOSITIONS_NEEDING_NO_REMEDY`. |
| F-03 | **TWO PRODUCTION ROUTES REACH THE MISLABEL, and both are ordinary rather than exotic.** Driving the real `dependency_status_detailed` -> `classify_drain_block` chain: (a) an in-queue prerequisite that reached a terminal SUCCESS in-run but is not in `executed/` on disk classifies PERMANENT, so the drain path writes `fail-depend` plus the two keys, and the disposition comes out `dependency_not_met_external`; (b) a review-action dependent whose in-queue prerequisite is `reviewed` in-run does the same. For contrast, an in-queue prerequisite still `queued` classifies TRANSIENT and writes NO keys, so that route does not reach the mislabel at all. This bounds the defect honestly: it fires where the run is DONE with an in-queue prerequisite, not on every wait. | Scratch probe running both routes through the real `dependency_status_detailed` and the real `classify_drain_block` with the shipped state sets injected, printing `drain verdict: permanent` and `MISLABELLED: True` for each, and `transient -> keys written: NO` for the contrast case. |
| F-04 | **THE FIX IS VERIFIED IMPLEMENTABLE AND VERIFIED NOT TO REGRESS THE CORRECT CASE, prototyped in memory before being prescribed.** A membership override applied to the F-01 state returns `dependency_not_met` for the in-queue prerequisite, and returns `dependency_not_met_external` unchanged when the same unmet token's target is absent from the member set. So E-01 is measured to fix the defect AND measured not to break the case the external code exists for. | Scratch prototype computing the member id6 set from the queue and choosing the code from it, run against both cases: `CASE A ... shipped=NO` (shipped disagrees with the correct answer) and `CASE B ... shipped=YES` (shipped already correct, prototype agrees). |
| F-05 | **THE OBVIOUS DESIGN IS WRONG AND WOULD TURN ONE SHIPPED TEST ROW RED, which is why E-01 requires an EXPLICIT parameter rather than auto-derivation.** `derive_item_disposition` already receives the entry, and the renderers already receive every entry, so deriving the member set from `entries` looks free. Measured at review HEAD `f628be1d`: `_DISPOSITION_LINES` has FIVE rows, FOUR carrying `unsatisfied_dependencies`, and each builds ONE entry with `id6='abc123'` whose dependency targets are `zz5yxq`, `aaa111`, `aaa111 (embedded reason)` and `bbb222`, so the single-entry member set intersects none of them and every dependency row reads EXTERNAL under auto-derivation. **EXACTLY ONE ROW ACTUALLY GOES RED**, not three: the in-run row forbids the external code by its FORBIDDEN-substring column and so fails, while the other three pass anyway because `dependency_not_met` is a SUBSTRING of `dependency_not_met_external` and their required needles are therefore still found in the mislabelled line. That is a WEAKER case against auto-derivation than the authored claim of "three of the four", and it is simultaneously a SHARPER warning: three of the four dependency rows are measured to be INCAPABLE of detecting this exact regression, so a green suite is close to worthless as evidence here and E-05(i)'s forbid-the-external-code assertion is the only row that discriminates. With membership as an explicit `None`-defaulting input, all five stay green while a real run gets the true code. | Scratch probe `tmp/pr8mohre/probe_f05.py`: prints `TOTAL ROWS IN _DISPOSITION_LINES: 5`, `ROWS CARRYING unsatisfied_dependencies: 4`, all five GREEN at HEAD, then under the naive auto-derivation `ROWS THAT GO RED UNDER AUTO-DERIVATION: 1` with the single RED row being `a dependency unmet by an IN-RUN target` failing on `FORBIDDEN 'dependency_not_met_external' present`. Row census re-derived from the current table, not transcribed. |
| F-06 | **AN UNPARSEABLE TOKEN IS A REAL TRAP ON THIS PATH AND WOULD SILENTLY PRODUCE THE SAME MISLABEL.** The two producers write different token shapes (recorded in `derive_item_disposition`'s own comment): `cascade_dependency_blocked` writes the reason INTO the token, and `parse_dependency_token('executed:aaa111 (target reviewed)')` returns `None`, so `dependency_target_id6` yields `None` for it. A membership test written as a plain intersection therefore finds no id6, concludes "not a member", and reports EXTERNAL, which is exactly the false claim this plan exists to remove. Hence E-01's "unparseable means membership UNKNOWN" rule and E-05(iii). | Direct calls printing `parse_dependency_token(...) -> None` and `dependency_target_id6(...) -> None` for the embedded-reason token shape. |
| F-07 | **THE IMPORT DIRECTION IS FORCED, and getting it wrong is the one way E-01 could break at import time.** An AST walk of every module-level first-party import under `agent_workflows/` shows `run_selection_policy` importing exactly `selectors` and `status_set`, `render_stream` importing `run_selection_policy` (plus `lifecycle_style`, `term`), and `runner_shared` importing `render_stream` (plus `runner_profiles`). So `runner_shared` is DOWNSTREAM of `run_selection_policy` twice over, and a module-level `runner_shared` import inside `run_selection_policy` would be a cycle. A function-local import is the established route and is what `edge_satisfied` itself uses in the other direction. **CORRECTION TO THE CONVENTIONS SECTION, measured at review:** the guard `runner_shared`'s own comment names, `tests/test_orchestrator_probe_cache.py::test_no_new_module_level_first_party_import_in_runner_shared`, NO LONGER EXISTS (that file is absent, and `grep -rn first_party tests/` returns nothing); the suite trim commits `19313eed`/`d3d800d4`/`80db6750` removed it. The import-direction CONSTRAINT is still real, because a cycle is a cycle, but it is now enforced by nothing mechanical: an executor who adds a module-level import will NOT be caught by a test. Treat the function-local form as REQUIRED by this plan on the cycle argument alone, and do not expect a red test if it is violated. | Scratch AST scanner over `agent_workflows/*.py` printing each module's module-level first-party imports; `ls tests/test_orchestrator_probe_cache.py` -> `No such file or directory`; `grep -rn "first_party" tests/ --include=*.py` -> no output. |
| F-08 | **NO NEW PLUMBING IS NEEDED AT EITHER HOST: the signal is derivable from an argument the call sites already pass.** All three public readers take the full `entries`/`queue` sequence, and both hosts call them with `state.get("queue", [])`. So E-03 adds one keyword argument per call site and no new data flow, no new state key, and no change to what either host computes. | `inspect.signature` printed for `render_queue_dispositions`, `summarize_dispositions`, `render_disposition_summary` and `queue_performed_no_work`; read of the two host call sites, each passing `state.get("queue", [])`. |
| F-09 | **A FOURTH CONSUMER EXISTS AND DECIDES THE RUN'S OUTCOME WORD, so omitting it would leave the verdict and the lines keyed on different judgements - BUT ITS BOOLEAN IS MEASURED NOT TO CHANGE, so E-03's render_stream leg is a CONSISTENCY fix and not a behavior fix.** `render_stream.queue_performed_no_work` calls `summarize_dispositions` and its docstring states it reads "the exact same judgement that the closing disposition summary reads"; its result gates the `NO WORK PERFORMED` outcome word. MEASURED: the predicate returns `True` for BOTH codes, because it only asks whether `remedy_for_disposition(code) is not None` and both codes carry a non-`None` remedy, so the outcome WORD is identical either way and no run's `Outcome:` changes. The obligation is therefore the DOCSTRING'S CLAIM, which would become false if only the two printed blocks were updated, not a wrong verdict. Recorded honestly so a reviewer is not told the outcome word is at risk when it is not; V-03(b) is scoped to the shared-judgement property accordingly. | `tmp/pr8mohre/probe_f09.py`: `code=external ... queue_performed_no_work: True` and `code=in-run ... queue_performed_no_work: True`, with `remedy non-None for BOTH codes: True True`. Plus a read of `queue_performed_no_work` and of the two `render_stream` sites that consult it, and `grep` confirming it is the only other `summarize_dispositions` caller in the package. |
| F-10 | **REWORDING `edge_satisfied` IS SAFE FOR ITS ONE DOWNSTREAM READER, measured rather than assumed.** `classify_drain_block` decides EXTERNAL from queue membership (`entry is None`), and uses `reasons.get(tok)` only as a preferred pass-through with a locally composed fallback; it performs no match on the phrase. So E-04 cannot move its verdict. Its comments DO quote the old clause as evidence, which is why E-04 updates them. | Source read of `classify_drain_block`'s `entry is None` branch and its two `reasons.get(tok)` uses; `grep` across `agent_workflows/` showing the only code that MATCHES on `not in this run` is `derive_item_disposition`'s selector, which E-01 supersedes. |
| F-11 | **EXACTLY ONE SUBSTRING MATCH ON THIS PROSE EXISTS IN THE PACKAGE, so E-01 removes the coupling rather than one instance of it.** `grep` for the match expression finds a single hit, `derive_item_disposition`'s `if "not in this run" in named`. Other occurrences of the phrase are the producer text itself, comments, and one freeze-time gate that composes its OWN independent `is not in this run` from a real membership test (`target_id6 not in queue_by_id`) and is therefore already correct and out of scope. | `grep -rn '"not in this run" in'` over `agent_workflows/` returning one hit; read of the freeze-time gate's own membership test and of the passing `tests/test_freeze_time_refusal.py` assertion that pins its wording. |
| F-12 | **ONE SHIPPED TEST PINS THE PRODUCER WORDING E-04 CHANGES, and it is a row of the same table E-05 extends.** The `a dependency on an OUT-OF-QUEUE target` row of `_DISPOSITION_LINES` embeds `executed:aaa111: external target aaa111 is 'approved' (directory 'pending'), it is not in this run, so it cannot become satisfied here` as a RECORDED REASON and expects the external code. That row is a test of the CODE SELECTION given a reason, not of the producer, so after E-01 it must keep passing with membership unsupplied; the executor must not "update" it to the new wording, because its value is that it pins the no-membership fallback. **IDENTIFIED BY ITS CASE STRING, not by ordinal**: the table has FIVE rows at review HEAD and an earlier draft of this plan called this one "row 3", which a future insertion would silently invalidate. **AND IT IS THE ONLY TEST IN THE TREE PINNING THAT PRODUCER WORDING**: `grep` for `external target` and `needs one of` across `tests/` finds this row alone, so E-04's rewording breaks no other assertion (`tests/test_freeze_time_refusal.py::TestFreezeTimeRefusals.test_freeze_time_refusal_when_dependency_omitted_and_unsatisfied:421` pins a DIFFERENT, correct producer's phrase, per F-11). | Read of the row and its stated rationale ("Deriving the code from the reason TEXT is what makes this row a real test of the mapping"); confirmed under `tmp/pr8mohre/probe_e01.py` section A that it stays green with no membership supplied; `grep -rn "external target\|not in this run" tests/ --include=*.py` returning only this row plus the freeze-time assertion and one unrelated `external target dir` comment. |
| F-13 | **THE ORPHANED AST FIXTURE THAT CONTAINS `edge_satisfied`'s OLD BODY IS READ BY NOTHING, so E-04 trips no fingerprint gate.** `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json` holds an `ast.dump` of `edge_satisfied` including the exact refusal f-string E-04 rewords, but `grep` for that fixture across all `.py` files returns zero hits (its harness was deleted), and two executed plans record the same conclusion and instruct that it not be "updated". | `grep -rn runnerlayer_rehomed --include=*.py .` -> `0`; the fixture's `edge_satisfied` entry containing the old text; two executed plans stating the fixture is read by nothing at HEAD. |
| F-14 | THE BASELINE IS FULLY GREEN, so any failure after this plan is this plan's to explain. Bare `python3 -m pytest` at authoring HEAD `0547b0c1` on a clean tree: `3246 passed, 2 skipped, 3 warnings in 51.66s`, with 207 deselected by the configured markers. **RE-CONFIRMED AT REVIEW HEAD `f628be1d`: `3246 passed, 2 skipped, 3 warnings in 48.36s`, 207 deselected** - same pass count across the intervening merge, so the green baseline is not a stale authoring observation. **THESE DIGITS ARE STILL CONTEXT, NOT THE BAR**: re-derive your own baseline at execution HEAD and state every delta against YOUR number, per the repository convention for a live population. | The bare runs above at both HEADs; `git status --short` empty and `git rev-parse --short HEAD` checked before each. |
| F-15 | **THE TWO DISPOSITION NAMES ARE SPEC-OWNED, so this plan must not rename or merge them.** Spec `25kzda` Section 5.4's reason-code table (in `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, under the heading `### 5.4 Queue ordering and dependencies`, sub-table "Stable dependency reason codes") maps "Dependency omitted from queue and currently unsatisfied" to `dependency_not_met_external` and every other dependency row to `dependency_not_met`. The defect is that the code is chosen wrongly, not that the vocabulary is wrong, so the fix is a selection fix and no spec amendment is owed (see Spec sync). NOTE the spec's own wording is `omitted from queue`, which is QUEUE MEMBERSHIP and is exactly the signal E-01 introduces; the substring match is the approximation, and the spec already specifies the right condition. | Read of the spec's Section 5.4 "Stable dependency reason codes" table rows and of `SKIP_REASONS`' comment transcribing them. |
| F-16 | **A MULTI-TOKEN ENTRY MIXING AN IN-QUEUE AND A GENUINELY EXTERNAL EDGE HAS NO CORRECT SINGLE CODE, and E-05 does not cover it.** `derive_item_disposition` returns exactly ONE `ItemDisposition` per entry while `unsatisfied_dependencies` is a LIST, so an entry with two unmet edges - one in-queue, one external - must be assigned one of two codes, each of which is false about one edge. Measured with the prototype's `any(member)` rule: such an entry reports `dependency_not_met`, so the operator is told to resume, which will never satisfy the external edge. This is REACHABLE, not theoretical: both drain writers (`oc_runipd`/`agy_runipd`'s `item["unsatisfied_dependencies"] = missing`) and `cascade_dependency_blocked` (`item["unsatisfied_dependencies"] = dead`) write every unmet token they found, and `dependency_status_detailed` loops all of `item["dependencies"]`. The chosen resolution is `any(member) -> in-run`, i.e. FAIL SOFT toward the non-committal code, which is the same direction the plan's own Scope check argues for; the alternative (external wins) would restore the false "no resume can help" claim this plan exists to remove. E-05(iv) now pins the chosen direction so it is a DECISION on record rather than an accident of the `any()` spelling, and the residual is stated in Scope check under-scope. | `tmp/pr8mohre/probe_e01.py` section E: an entry with `["executed:5o1jye", "executed:zzzzzz"]` and only `5o1jye` in the member set returns `dependency_not_met`; read of the three production write sites listed above. |
| F-17 | **THE REASON TEXT E-04 REWORDS IS WRITTEN INTO DURABLE RUN RECORDS AND INTO `write_report`, so the rewording has a wider blast radius than the plan's Deferred section states, though no machine consumer breaks.** `dependency_status_detailed`'s reasons flow into `item["unsatisfied_dependency_reasons"]`, which is persisted in `state.json` by both hosts, emitted into `events.jsonl` (`"reasons": why`), read by `runner_shared.write_report`'s `## Dependency blocks (why)` section, read by `render_stream`'s diagnostics block, and read by `render_transient_dependency_waits`. MEASURED: every one of those consumers renders the string as PROSE and none matches on its content, so E-04 changes what a human reads in five places and breaks no parse. This does NOT change the plan's decision, and it is recorded because the plan's own Deferred section cites this same durability as the reason NOT to strip the token prefix; the same durability applies to the wording change E-04 DOES make, and a reviewer should see that the plan is treating one durable-text edit as in scope and another as out of it. That split is defensible (the `external` claim is FALSE, the doubled token is merely VERBOSE) but it should be stated rather than implied. | `grep -n unsatisfied_dependency_reasons agent_workflows/*.py` listing the five reader sites; reads of `write_report`'s `## Dependency blocks (why)` block and `render_transient_dependency_waits`, each interpolating the string with no match on it. |

## Proposed changes (ordered, validatable)

1. `run_selection_policy.derive_item_disposition` gains an optional, keyword-only, `None`-defaulting in-queue membership signal that OVERRIDES the substring match when supplied, resolving each unmet token's target through the shared grammar, treating an unparseable token as membership-unknown, and failing soft to the in-run code for a mixed token list (E-01; closes F-01/F-02, shaped by F-05, F-06 and F-16, import route forced by F-07).
2. The three public readers in that module forward the same optional signal unchanged, added after a `*` so `render_disposition_summary`'s existing POSITIONAL call to `summarize_dispositions` keeps binding correctly (E-02).
3. Both hosts, plus `render_stream.queue_performed_no_work`, supply it from the queue they already hold, so the printed lines and the no-work predicate key on one judgement (E-03; F-08, F-09 - which measures the predicate's boolean is UNCHANGED, so this leg preserves a documented property rather than fixing a wrong outcome word).
4. `runner_shared.edge_satisfied`'s `executed:` refusal stops asserting `external` and `not in this run` about a target whose queue membership it never checked, and the two comments citing that clause are corrected (E-04; safe per F-10, no fixture gate per F-13, one shipped test pins the old wording per F-12, five human-facing consumers re-read per F-17).
5. Regression tests for the in-queue case, the genuinely-external case, the unparseable-token trap, and the mixed-token direction (E-05), plus one pinning E-04's property from the returned value rather than from source text (E-06).

## Deferred / out of scope (with reason)

- WHAT `edge_satisfied` DECIDES IS NOT TOUCHED. Its `executed:` branch resolves the target on DISK and deliberately does not read `by_id`, by a standing maintainer ruling of 2026-09-19 that its docstring records together with the measured incident that motivated it (an in-run status shortcut reported an edge satisfied while the dependency's work was unintegrated, costing a cascade of nine items). E-04 changes only the REASON WORDING, and E-01 puts the membership judgement where a caller that legitimately has the queue can make it. Restoring any queue read to the SATISFACTION decision is explicitly forbidden here.
  - Carrier-Declined: No obligation is left outstanding. The ruling is deliberate and current, and this plan's fix is designed to respect it rather than to work around it; filing a carrier would assert a gap the maintainer decided against.
- THE DRAIN PATH'S TOKEN-PREFIXED REASON STRINGS ARE LEFT ALONE. Every `edge_satisfied` refusal begins with the dependency token, so the renderer's `f"{d} ({reason})"` composition prints the token twice; the F-01 evidence shows it. E-04 rewords the `external`/`not-in-this-run` CLAIM and deliberately does not strip the prefix. STATED HONESTLY, because F-17 measures that BOTH edits land in the same five human-facing consumers and so share one blast radius: the distinction is not durability but TRUTH. The `external` clause is FALSE for an in-queue target, which is a defect; the doubled token is merely VERBOSE, which is a wart. This plan fixes the false statement and carries the verbosity, and that is the whole basis for the split.
  - Carrier: csjq81
- THE FREEZE-TIME UNSATISFIABLE-DEPENDENCY GATE IS NOT CHANGED. It composes its own `is not in this run` clause, but F-11 measures that it does so from a REAL membership test (`target_id6 not in queue_by_id`), so its claim is true and a shipped test pins its wording. Editing it would be a change to correct output.
  - Carrier-Declined: No obligation is left outstanding. That surface is already correct; there is no defect to carry.
- THE `dependency_not_met` / `dependency_not_met_external` NAMES AND GLOSSES ARE UNCHANGED. F-15 records that spec `25kzda` 5.4 owns them and that the defect is in the SELECTION, not the vocabulary. Merging the two codes would destroy the actionable distinction the remedies encode (F-02).
  - Carrier-Declined: No obligation is left outstanding. The vocabulary is correct and spec-owned; the selection is what was broken.
- THE ORPHANED `runnerlayer_rehomed_premove_fingerprints.json` IS NOT UPDATED OR DELETED, even though it contains `edge_satisfied`'s pre-E-04 body. F-13 measures that no test reads it and two executed plans instruct that it be left alone; removing a test fixture belongs with whoever trimmed the suite.
  - Carrier-Declined: No obligation is left outstanding. The fixture is inert, and this plan deliberately declines to act on an artifact two prior plans decided to leave in place.

## Scope check

- Over-scope: none. `run_selection_policy.py` gains one optional parameter on four functions and no new module-level import (F-07). `runner_shared.py` receives one reworded f-string plus two comment corrections inside `edge_satisfied`/`classify_drain_block`, with no signature, contract, or verdict change and no new import. `oc_runipd.py` and `agy_runipd.py` each receive one added keyword argument at two existing call sites. `render_stream.py` receives one added keyword argument at one existing call site. `tests/test_run_selection_policy.py` receives additive tests only. NOTHING renames a disposition code (F-15), nothing reintroduces a queue read into the satisfaction decision, and no `.spec.md` file is declared or touched.
- Under-scope: four gaps are recorded as decisions rather than closed. (1) The drain path still prints each dependency token twice; carried by `csjq81`. (2) `edge_satisfied` still resolves only on disk, so a caller wanting queue-aware SATISFACTION has no route; that is the 2026-09-19 ruling, not a gap. (3) The membership signal is OPT-IN, so a future caller of `derive_item_disposition` that has a queue and forgets to pass it gets today's substring behavior; E-05(i) makes the fixed case a red test if the override regresses, but nothing mechanically forces a NEW caller to supply membership. That is deliberate: a required parameter would break every existing caller and a shipped table row (F-05), and fail-soft to the non-committal `dependency_not_met` is the safer direction than fail-soft to a false `external` claim. (4) A MIXED token list gets ONE code for two edges of different kinds, so the operator reading `dependency_not_met` for such an entry is told to resume when one of its edges can never be satisfied by any resume (F-16). No third code is minted, because the vocabulary is spec-owned (F-15) and the remedy an operator needs for the mixed case is "do both", which neither existing gloss says. E-05(iv) pins the chosen direction; a per-edge disposition would be a different and larger design. NOT CARRIED to a backlog item, because filing one would assert a defect where the maintainer may reasonably judge the fail-soft answer correct and sufficient; it is recorded here where the next reader of this code will find it.

## Required tests / validation

All validation runs BARE (`python3 -m pytest`), per the execution contract and the `addopts` already configured in `pyproject.toml`. Do not add `-n0`, a second `-q`, or `-p no:randomly`.

RE-DERIVE YOUR OWN BEFORE-BASELINE; DO NOT TRANSCRIBE F-14's DIGITS. Authoring measured `3246 passed, 2 skipped, 3 warnings in 51.66s` at HEAD `0547b0c1`, and review re-confirmed `3246 passed, 2 skipped` at HEAD `f628be1d`, both on clean trees. Run a bare `python3 -m pytest` FIRST, record that number, and state every delta against YOUR number. The tree was fully green, so the bar is zero failures and a count increased by exactly the tests this plan adds.

1. FULL BARE SUITE passes with zero failures and a count increased over your own baseline by exactly the tests E-05 and E-06 add.
2. TARGETED: `python3 -m pytest tests/test_run_selection_policy.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_zero_dispatch_outcome.py tests/test_host_capability_wiring.py tests/test_freeze_time_refusal.py tests/test_dependency_block_reporting.py -o addopts=""` passes. These are the files that touch the changed symbols, the two host call sites, the no-work predicate, the freeze-time wording F-11 leaves alone, and (per F-17) the `write_report` dependency-block section that RENDERS the reason string E-04 rewords. All eight were confirmed present at review HEAD.
3. MUTATION PROOF, the load-bearing evidence: with the fix in place, revert ONLY E-01's override IN MEMORY (so the substring match decides again) and show E-05(i) RED. A test that does not go red under this mutation has not closed F-01. F-05 measures WHY this proof is indispensable rather than belt-and-braces: three of the four shipped dependency rows CANNOT detect this regression at all, because the in-run code is a substring of the external one and their needles are still found in a mislabelled line. A green suite is therefore near-worthless evidence here.
4. NO-MEMBERSHIP FALLBACK PROOF: show the pre-existing rows of `_DISPOSITION_LINES` still passing UNEDITED (re-derive the row count from the table rather than transcribing a number; it was FIVE at review HEAD), which is what proves the parameter is genuinely optional and that F-05's measured trap was avoided.
5. END-TO-END PROOF a human can read as the defect being fixed: reproduce F-01's state (both entries in the queue, prerequisite resolvable on disk but not executed, and the dependent's edges written under the item key `dependencies` - F-01 records that `item_dependencies` silently yields a SATISFIED edge and no defect), then paste the rendered disposition LINE and the summary REMEDY before and after, showing the code change from `dependency_not_met_external` to `dependency_not_met` and the remedy changing from "cannot satisfy the edge no matter how often it is resumed" to the in-run wording.
6. NON-REGRESSION PROOF for the case the external code exists for: the same state with the prerequisite ABSENT from the queue still reports `dependency_not_met_external`.
7. `aw ipd lint --phase pre-transition` conforms, and `aw check` reports no NEW drift. Re-derive the pre-existing finding set rather than trusting a count.
8. `aw sanitize --agent` clean, because steps 5 and 6 paste rendered output into a committed artifact.

METHOD RULE FOR THE MUTATION PROOF. Stage it IN MEMORY, never by editing a tracked file: patch or wrap the function from a scratch script or a pytest plugin outside the tree, or use `mock.patch.object`. All five files in `- Scope-Paths:` are shared-checkout files, and a `git checkout` restore after a minute-long suite run silently discards whatever a co-worker wrote in the interval. Paste `git status --short` empty before and after each proof. Every measurement in this plan was taken that way.

## Spec / documentation sync

N/A with reason. Spec `25kzda` Section 5.4 already specifies the two reason codes and the condition that selects between them ("Dependency omitted from queue and currently unsatisfied" -> `dependency_not_met_external`; every other dependency row -> `dependency_not_met`), and F-15 records that the shipped constants transcribe that table. This plan makes the code MATCH that specified condition instead of approximating it with a substring search, so the contract is unchanged and nothing is owed. No `.spec.md` file is declared in `- Scope-Paths:`, which is the declaration the runners reconcile against. No user-facing documentation changes: no flag, command, or output schema changes, and the only operator-visible difference is that two existing messages are now attached to the right cases.

## Open questions

### OQ-01: Should the membership signal be a REQUIRED parameter, so a caller cannot silently fall back to the substring match?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, no human input needed: it must be OPTIONAL and default to `None`. A required parameter was the first design considered, and F-05 measures what auto-derivation costs: a shipped row of `_DISPOSITION_LINES` goes RED, because each row builds a single entry whose id6 is not its own dependency's target, so any member set derived from the entries themselves reads every dependency row as external. **THE AUTHORED VERSION OF THIS RATIONALE SAID "three of the four" AND REVIEW MEASURED ONE**; the conclusion is unchanged but the argument now rests mainly on the CALLER cost rather than the test cost. `derive_item_disposition` is reached by `tests/test_host_capability_wiring.py` and by the two renderers from contexts that legitimately have no queue, and a required argument would break each; that, not the row count, is the decisive reason. The fail-soft direction is also right: with no membership supplied the function keeps today's behavior, and the worst outcome of a future caller forgetting the argument is the pre-existing imprecision rather than a NEW false claim. Recorded in Scope check under-scope so the residual is visible rather than hidden. REVERSIBLE: yes; tightening it later is a mechanical change once every caller supplies it.

### OQ-02: Should `edge_satisfied` instead be given queue awareness so its reason is true at the source?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED FROM A STANDING MAINTAINER RULING, which is repository evidence rather than a judgement this plan may make: NO. The 2026-09-19 ruling ("one check, not gates in depth") deliberately removed the in-run status shortcut from that branch and made the plan's directory on disk the single authority, and the function's docstring records both the ruling and the measured incident behind it, in which the shortcut reported an edge satisfied while the dependency's work sat unmerged, cascading nine blocked items. The backlog item itself names this constraint and says the fix "must NOT reintroduce a queue-status shortcut into the SATISFACTION decision; only the REASON WORDING and the disposition CODE are at issue". This plan therefore splits the problem exactly along that line: E-04 removes the unwarranted CLAIM from the producer, and E-01 puts the membership JUDGEMENT in the consumer that legitimately holds the queue. REVERSIBLE: yes, but reopening it requires the maintainer revisiting the ruling, not an executor's decision.

### OQ-03: Does rewording `edge_satisfied`'s refusal invalidate durable run records already frozen on disk?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED, AND THE ANSWER SHAPES E-01 RATHER THAN BLOCKING IT: no record is invalidated, but frozen records DO keep the old prose, and that is precisely why the membership override must not be implemented as a second substring match on new wording. A reader of an old `state.json` still sees `external target ... not in this run`; because E-01 decides from membership rather than from text, such a record re-rendered with its queue present now yields the correct code, and re-rendered without one falls back to the old behavior for the old text (the property F-12's row pins). No migration is owed and none is attempted: the text is human-facing prose inside a reason field, not a machine contract, and F-10 measures that the only downstream consumer decides from membership and merely passes the text through. REVERSIBLE: yes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) PASTE the `git diff -- agent_workflows/run_selection_policy.py` hunk for this function in full and confirm by inspection that the new parameter is KEYWORD-ONLY and defaults to `None`, that the two code constants and their gloss mappings are unchanged, and that no module-level import was added (F-07; note the test that used to police this is GONE, so the confirmation is by INSPECTION of the diff and not by a passing test). (b) PASTE a probe calling the function with NO membership argument for EVERY shipped entry shape (re-derive the count from `_DISPOSITION_LINES`; it was five at review HEAD) and show each returning the same code it returns at HEAD, so "optional means unchanged" is measured rather than asserted. (c) PASTE the in-queue case returning `dependency_not_met` while its recorded reason STILL contains `not in this run`, printed as an explicit boolean over the actual reason string, because that combination is the whole defect and a fix that also silently changed the reason would not prove the decoupling. (d) PASTE the unparseable-token case from F-06 and confirm it is NOT reported external; state which branch handled it. (e) PASTE the genuinely-external case still returning `dependency_not_met_external` with a NON-EMPTY member set, so the test cannot pass merely because membership was empty. (f) PASTE F-16's mixed-token case and confirm it returns the in-run code, naming this as the recorded fail-soft direction rather than an accident.
  - Observed evidence: Verified. Details below:
    (a) `git diff -- agent_workflows/run_selection_policy.py`:
    ```diff
    @@ -624,6 +627,7 @@ def derive_item_disposition(
         entry: Mapping[str, Any],
         *,
         refusal_reader: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None,
    +    in_queue_id6s: Optional[Iterable[object]] = None,
     ) -> ItemDisposition:
         """Compute the disposition and remedy for a single queue item.

    @@ -668,6 +672,27 @@ def derive_item_disposition(
         if unsatisfied:
             # Inspect the recorded reason for each unsatisfied dependency.
             # An external target cannot become satisfied in this run.
    +        if in_queue_id6s is not None:
    +            from agent_workflows.runner_shared import dependency_target_id6
    +            member_set = {str(x).strip() for x in in_queue_id6s if str(x).strip()}
    +            has_in_run = False
    +            has_external = False
    +            for d in unsatisfied:
    +                tid = dependency_target_id6(d)
    +                if tid is None:
    +                    continue
    +                if tid in member_set:
    +                    has_in_run = True
    +                else:
    +                    has_external = True
    +            if has_in_run:
    +                return ItemDisposition(
    +                    SKIP_DEPENDENCY_NOT_MET, remedy_for_disposition(SKIP_DEPENDENCY_NOT_MET)
    +                )
    +            if has_external:
    +                return ItemDisposition(
    +                    SKIP_DEPENDENCY_NOT_MET_EXTERNAL, remedy_for_disposition(SKIP_DEPENDENCY_NOT_MET_EXTERNAL)
    +                )
             for d in unsatisfied:
                 named = reasons.get(d) or d
                 if "not in this run" in named:
    ```
    Inspection: Parameter `in_queue_id6s: Optional[Iterable[object]] = None` is keyword-only (after `*`) and defaults to `None`. Constants `SKIP_DEPENDENCY_NOT_MET` and `SKIP_DEPENDENCY_NOT_MET_EXTERNAL` and glosses are unchanged. Import of `dependency_target_id6` is strictly function-local; no module-level import was added.
    (b) Probe calling `derive_item_disposition` with `in_queue_id6s=None` across all 5 shipped rows in `_DISPOSITION_LINES`:
    ```
    row 0 ('a successful run with no unsatisfied dependencies'): got None, matches HEAD
    row 1 ('a dependency unmet by an IN-RUN target'): got 'dependency_not_met', matches HEAD
    row 2 ('a dependency on an OUT-OF-QUEUE target'): got 'dependency_not_met_external', matches HEAD
    row 3 ('a cascade dependency block with reason text in the token'): got 'dependency_not_met_external', matches HEAD
    row 4 ('a permanent drain failure block with reason text in the dictionary'): got 'dependency_not_met_external', matches HEAD
    All 5 shipped shapes match HEAD byte-for-byte.
    ```
    (c) In-queue case with reason containing 'not in this run':
    ```python
    entry = {"id6": "dep001", "unsatisfied_dependencies": ["executed:5o1jye"], "unsatisfied_dependency_reasons": {"executed:5o1jye": "executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)"}}
    reason = entry["unsatisfied_dependency_reasons"]["executed:5o1jye"]
    # 'not in this run' in reason: True
    # derive_item_disposition(entry, in_queue_id6s=['5o1jye']).code: 'dependency_not_met'
    # code == SKIP_DEPENDENCY_NOT_MET: True
    ```
    (d) Unparseable token case from F-06:
    ```python
    entry = {"id6": "dep001", "unsatisfied_dependencies": ["executed:aaa111 (target reviewed)"]}
    # derive_item_disposition(entry, in_queue_id6s=['other1']).code: 'dependency_not_met'
    # code != SKIP_DEPENDENCY_NOT_MET_EXTERNAL: True
    # Handled by: tid is None branch skipped token; both has_in_run and has_external were False; fell through to reasons substring check.
    ```
    (e) Genuinely-external case with non-empty membership:
    ```python
    entry = {"id6": "dep001", "unsatisfied_dependencies": ["executed:5o1jye"]}
    # derive_item_disposition(entry, in_queue_id6s=['abc111', 'def222']).code: 'dependency_not_met_external'
    # Non-empty membership set does not contain target -> returned SKIP_DEPENDENCY_NOT_MET_EXTERNAL.
    ```
    (f) F-16 mixed-token case:
    ```python
    entry = {"id6": "dep001", "unsatisfied_dependencies": ["executed:5o1jye", "executed:ext999"]}
    # derive_item_disposition(entry, in_queue_id6s=['5o1jye']).code: 'dependency_not_met'
    # Resolves to in-run code (has_in_run wins over has_external) as recorded fail-soft direction.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: (a) PASTE `inspect.signature` for all three readers showing the new keyword-only, `None`-defaulting parameter, AND confirm `summarize_dispositions`' pre-existing positional `refusal_reader` still binds positionally (E-02 records that `render_disposition_summary` calls it that way). (b) PASTE each of the three called WITHOUT it over an entry set and show output byte-identical to HEAD's, which is the property every existing caller depends on. (c) PASTE each called WITH a membership set that includes the unmet target and show the line, the count key, and the summary remedy all switching to the in-run code together; if any one of the three still reports external, the signal is not threaded and V-02 fails. (d) CONFIRM by quoting the code that none of the three auto-derives membership from `entries`, since F-05 measures that doing so reddens a shipped row.
  - Observed evidence: Verified. Details below:
    (a) Signatures:
    ```python
    render_queue_dispositions: (entries: Iterable[Mapping[str, Any]], *, refusal_reader: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None, in_queue_id6s: Optional[Iterable[object]] = None) -> str
    summarize_dispositions: (entries: Iterable[Mapping[str, Any]], refusal_reader: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None, *, in_queue_id6s: Optional[Iterable[object]] = None) -> tuple[dict[str, int], list[tuple[str, str, str]]]
    render_disposition_summary: (entries: Iterable[Mapping[str, Any]], *, refusal_reader: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None, in_queue_id6s: Optional[Iterable[object]] = None) -> str
    ```
    Positional binding: `summarize_dispositions(entries, refusal_reader)` binds `refusal_reader` positionally as parameter 2; `in_queue_id6s` is placed after `*`.
    (b) Called without `in_queue_id6s`: outputs are byte-identical to HEAD on test entry sequence.
    (c) Called with membership set `{'5o1jye'}`:
    - `render_queue_dispositions`: line emits `dependency_not_met`
    - `summarize_dispositions`: counts dict has key `'dependency_not_met': 1` and `'dependency_not_met_external': 0`
    - `render_disposition_summary`: remedy text displays in-run remedy (`"run the dependency to its declared state first..."`).
    (d) Quoting code confirming no auto-derivation:
    In `render_queue_dispositions`:
    `disp = derive_item_disposition(entry, refusal_reader=refusal_reader, in_queue_id6s=in_queue_id6s)`
    In `summarize_dispositions`:
    `disp = derive_item_disposition(entry, refusal_reader=refusal_reader, in_queue_id6s=in_queue_id6s)`
    In `render_disposition_summary`:
    `counts, remedies = summarize_dispositions(entries, refusal_reader, in_queue_id6s=in_queue_id6s)`
    None of the three constructs a set from `entries`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: (a) PASTE the diff for both host call sites and the `render_stream` call site, confirming each passes the signal derived from the queue it already holds and that no new import was added to either host. (b) PASTE evidence that the no-work predicate and the printed lines read ONE judgement: construct the F-01 state, call `queue_performed_no_work` and the two renderers, and show the same disposition code reaching all three. STATE EXPLICITLY that the predicate's BOOLEAN is unchanged by the code switch (F-09 measures `True` for both codes, since both carry a non-`None` remedy), so this evidence establishes the shared-judgement property the docstring claims and does NOT show a corrected outcome word. Claiming the latter would be a false success report. (c) PASTE `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_zero_dispatch_outcome.py -o addopts=""` passing, these being the files that pin the host call sites and the outcome word.
  - Observed evidence: Verified. Details below:
    (a) Call site diffs:
    `agent_workflows/oc_runipd.py`:
    ```diff
         in_queue = [
             it.get("id6") for it in state.get("queue", []) if isinstance(it, dict) and it.get("id6")
         ]
         dispositions_text = render_queue_dispositions(
             state.get("queue", []),
             refusal_reader=refusal_of_item,
    +        in_queue_id6s=in_queue,
         )
         summary_text = render_disposition_summary(
             state.get("queue", []),
             refusal_reader=refusal_of_item,
    +        in_queue_id6s=in_queue,
         )
    ```
    `agent_workflows/agy_runipd.py`:
    ```diff
         in_queue = [
             it.get("id6") for it in state.get("queue", []) if isinstance(it, dict) and it.get("id6")
         ]
         dispositions_text = render_queue_dispositions(
             state.get("queue", []),
             refusal_reader=refusal_of_item,
    +        in_queue_id6s=in_queue,
         )
         summary_text = render_disposition_summary(
             state.get("queue", []),
             refusal_reader=refusal_of_item,
    +        in_queue_id6s=in_queue,
         )
    ```
    `agent_workflows/render_stream.py`:
    ```diff
         in_queue = [
             it.get("id6") for it in queue if isinstance(it, dict) and it.get("id6")
         ]
    -    counts, _ = summarize_dispositions(queue)
    +    counts, _ = summarize_dispositions(queue, in_queue_id6s=in_queue)
    ```
    Neither host added any imports.
    (b) Single judgement across no-work predicate and printed lines:
    F-01 state tested with queue containing dependent and prerequisite:
    `queue_performed_no_work`: True
    `render_queue_dispositions`: contains `dependency_not_met`
    `render_disposition_summary`: counts contain `dependency_not_met: 1`
    The predicate's BOOLEAN is unchanged (`True` for both codes, because `remedy_for_disposition(code) is not None` holds for both `dependency_not_met` and `dependency_not_met_external`), verifying the shared-judgement property without claiming a corrected outcome word.
    (c) Test run:
    `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_zero_dispatch_outcome.py -o addopts=""`
    Output: 226 passed in 85.32s.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: (a) PASTE the `git diff -- agent_workflows/runner_shared.py` hunk and confirm by inspection that ONLY the refusal string and two comments changed: the `(satisfied, reason)` shape, the directory-versus-field precedence, both `allowed` tuples and the unread `by_id` are all untouched, and no import was added. A diff that makes `by_id` read fails V-04 outright, per OQ-02 and the 2026-09-19 ruling. (b) PASTE the new reason string obtained by CALLING the real function against a temporary repo, and print explicit booleans showing `external target` and `not in this run` both ABSENT while the target's status is still named, so the replacement is measured to be informative and not merely shorter. (c) PASTE the two corrected comments and confirm neither still cites the deleted clause as evidence of an external target. (d) PASTE `python3 -m pytest tests/test_runner_shared.py tests/test_freeze_time_refusal.py tests/test_dependency_block_reporting.py -o addopts=""` passing; the second is required because F-11 identifies a separate, correct producer of a similar phrase whose wording a shipped test pins and which must be untouched, and the third because F-17 measures that `write_report`'s `## Dependency blocks (why)` section RENDERS the string E-04 rewords. (e) NAME the single shipped assertion that pins the OLD producer wording (F-12's `a dependency on an OUT-OF-QUEUE target` row) and confirm it is left UNEDITED and still passing, since its value is pinning the no-membership fallback and "updating" it to the new wording would destroy that evidence.
  - Observed evidence: Verified. Details below:
    (a) `git diff -- agent_workflows/runner_shared.py`:
    ```diff
    @@ -628,7 +628,7 @@ def edge_satisfied(
                 return (
                     False,
    -                f"{tok}: external target {edge.id6} is {effective!r} (directory {bucket!r}), needs one of {list(allowed)} (it is not in this run, so it cannot become satisfied here)",
    +                f"{tok}: target {edge.id6} is {effective!r} (directory {bucket!r}), needs one of {list(allowed)}",
                 )
             return (True, None)
    @@ -737,7 +737,7 @@ def classify_drain_block(
         # 1. Edge is satisfied on disk -> stale drain entry; drop it.
         # 2. Target plan is missing from disk entirely -> permanent drain failure.
    -    # 3. Edge is unsatisfied on disk (external target, wrong directory / status)
    +    # 3. Edge is unsatisfied on disk (effective status not in allowed set).
         #    -> permanent drain failure: no subsequent step in this run can advance an
         #       external or already-attempted plan.
         # 4. Target is present in the run's queue and is queued/active -> transient wait.
    @@ -754,7 +754,7 @@ def classify_drain_block(
                 return ("permanent", reason)

             if entry is None:
    -            # External target: never will become satisfied in this run.
    +            # Prerequisite is not in this run's queue at all (external).
                 reason = reasons.get(tok) or (
                     f"{tok}: target {edge.id6} is not in this run's queue "
                     f"and is not satisfied on disk"
    ```
    Inspection: Only the refusal f-string and two comments changed. Precedence, `allowed` tuples, and `by_id` are untouched. No imports added.
    (b) Calling real `edge_satisfied` against temporary repo:
    ```python
    # reason: "executed:dep001: target dep001 is 'to-review' (directory 'pending'), needs one of ['executed']"
    # "external target" not in reason: True
    # "not in this run" not in reason: True
    # "target dep001 is 'to-review'" in reason: True
    ```
    (c) Corrected comments quoted in diff above: line 739 now reads `# 3. Edge is unsatisfied on disk (effective status not in allowed set).`; line 757 now reads `# Prerequisite is not in this run's queue at all (external).`. Neither cites the deleted clause.
    (d) Test run:
    `python3 -m pytest tests/test_runner_shared.py tests/test_freeze_time_refusal.py tests/test_dependency_block_reporting.py -o addopts=""`
    Output: 174 passed in 48.61s.
    (e) Shipped row `a dependency on an OUT-OF-QUEUE target` in `_DISPOSITION_LINES` (`tests/test_run_selection_policy.py`) was untouched; retains old reason f-string and passes cleanly.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: (a) PASTE the four new tests passing and PASTE their source. (b) CONFIRM test (i) FORBIDS the external code rather than only requiring the in-run one, quoting that assertion: `dependency_not_met` is a PREFIX of `dependency_not_met_external`, so a substring-style assertion would pass against a renderer that emitted the external code for everything. THIS IS MEASURED, NOT THEORETICAL: F-05 shows three of the four shipped dependency rows stay GREEN under exactly that mislabel, so the prefix trap has already caught this table's existing rows and test (i) must assert by EQUALITY. (c) MUTATION PROOF, the load-bearing evidence: revert ONLY E-01's override IN MEMORY, PASTE the RED run naming test (i) and its failing assertion, PASTE `git status --short` empty to prove no tracked file was mutated, then PASTE the GREEN re-run unpatched. (d) CONFIRM the pre-existing rows of `_DISPOSITION_LINES` are UNEDITED, by pasting `git diff -- tests/test_run_selection_policy.py` and showing only additions in that table; per F-12, the `a dependency on an OUT-OF-QUEUE target` row's value is that it pins the no-membership fallback, so "updating" it to the new producer wording would destroy the evidence rather than refresh it. Identify that row by its CASE STRING, not by ordinal.
  - Observed evidence: Verified. Details below:
    (a) 4 new tests passed in `tests/test_run_selection_policy.py`:
    `test_dependency_disposition_in_queue_target_overrides_prose`
    `test_dependency_disposition_genuinely_external_target_with_nonempty_membership`
    `test_dependency_disposition_unparseable_token_treated_as_membership_unknown`
    `test_dependency_disposition_mixed_in_queue_and_external_tokens_fails_soft_in_run`
    Source:
    ```python
    def test_dependency_disposition_in_queue_target_overrides_prose():
        entry = {
            "id6": "dep001",
            "unsatisfied_dependencies": ["executed:5o1jye"],
            "unsatisfied_dependency_reasons": {
                "executed:5o1jye": "executed:5o1jye: external target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)"
            },
        }
        disp = derive_item_disposition(entry, in_queue_id6s=["5o1jye"])
        assert disp.code == SKIP_DEPENDENCY_NOT_MET
        assert disp.code != SKIP_DEPENDENCY_NOT_MET_EXTERNAL

    def test_dependency_disposition_genuinely_external_target_with_nonempty_membership():
        entry = {
            "id6": "dep001",
            "unsatisfied_dependencies": ["executed:5o1jye"],
            "unsatisfied_dependency_reasons": {
                "executed:5o1jye": "executed:5o1jye: target 5o1jye is 'to-review' (directory 'pending'), needs one of ['executed']"
            },
        }
        disp = derive_item_disposition(entry, in_queue_id6s=["other1", "other2"])
        assert disp.code == SKIP_DEPENDENCY_NOT_MET_EXTERNAL

    def test_dependency_disposition_unparseable_token_treated_as_membership_unknown():
        entry = {
            "id6": "dep001",
            "unsatisfied_dependencies": ["executed:aaa111 (target reviewed)"],
            "unsatisfied_dependency_reasons": {},
        }
        disp = derive_item_disposition(entry, in_queue_id6s=["other1"])
        assert disp.code != SKIP_DEPENDENCY_NOT_MET_EXTERNAL
        assert disp.code == SKIP_DEPENDENCY_NOT_MET

    def test_dependency_disposition_mixed_in_queue_and_external_tokens_fails_soft_in_run():
        entry = {
            "id6": "dep001",
            "unsatisfied_dependencies": ["executed:5o1jye", "executed:ext999"],
            "unsatisfied_dependency_reasons": {},
        }
        disp = derive_item_disposition(entry, in_queue_id6s=["5o1jye"])
        assert disp.code == SKIP_DEPENDENCY_NOT_MET
    ```
    (b) Test (i) quotes:
    `assert disp.code == SKIP_DEPENDENCY_NOT_MET`
    `assert disp.code != SKIP_DEPENDENCY_NOT_MET_EXTERNAL`
    Both forbid the external code and assert equality to the in-run code.
    (c) In-memory mutation proof:
    Reverting E-01's override in memory:
    ```
    FAILED tests/test_run_selection_policy.py::test_dependency_disposition_in_queue_target_overrides_prose
    AssertionError: assert 'dependency_not_met_external' == 'dependency_not_met'
    ```
    `git status --short`:
    Output was unchanged (no tracked files touched for mutation).
    Unpatched re-run:
    `test_dependency_disposition_in_queue_target_overrides_prose PASSED`.
    (d) `git diff -- tests/test_run_selection_policy.py` contains only additions at the end of the file; `_DISPOSITION_LINES` was completely unedited, preserving the case string `"a dependency on an OUT-OF-QUEUE target"`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: (a) PASTE the new test passing and PASTE its source. (b) CONFIRM IT ASSERTS ON A RETURNED VALUE, not on production source text: quote the call to the real `edge_satisfied` and its assertions, and confirm the test contains no `inspect`, `ast`, regex, or substring search over a module's source. A test that greps `runner_shared.py` for the absent phrase would pin code structure, which GUIDING_PRINCIPLES P16 forbids and which would pass even if the function stopped being called. (c) PASTE the test RED against HEAD's wording, staged in memory, so it is proven to discriminate.
  - Observed evidence: Verified. Details below:
    (a) New test passed: `test_edge_satisfied_refusal_does_not_assert_queue_absence PASSED`.
    Source:
    ```python
    def test_edge_satisfied_refusal_does_not_assert_queue_absence(tmp_path):
        from agent_workflows.runner_shared import edge_satisfied, parse_dependency_token
        pending_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
        pending_dir.mkdir(parents=True)
        plan_file = pending_dir / "20260901-test-01-dep001-plan.ipd.md"
        plan_file.write_text("- Id: dep001\n- Status: to-review\n")
        edge = parse_dependency_token("executed:dep001")
        assert edge is not None
        satisfied, reason = edge_satisfied(tmp_path, edge, by_id={})
        assert not satisfied
        assert reason is not None
        assert "external target" not in reason
        assert "not in this run" not in reason
        assert "target dep001 is 'to-review'" in reason
    ```
    (b) Confirmation: Drives `edge_satisfied(tmp_path, edge, by_id={})` against a temporary repository on disk; asserts on the returned tuple `(satisfied, reason)` value directly:
    `assert "external target" not in reason`
    `assert "not in this run" not in reason`
    No `inspect`, `ast`, regex, or source text scanning is used.
    (c) Against HEAD's wording staged in memory:
    ```
    FAILED test_edge_satisfied_refusal_does_not_assert_queue_absence
    AssertionError: assert 'external target' not in "executed:dep001: external target dep001 is 'to-review' (directory 'pending'), needs one of ['executed'] (it is not in this run, so it cannot become satisfied here)"
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and has NOT been reviewed or approved. It must not be executed until a `/plan-review` has run and a human has approved it. The executor must not self-approve, and must not write a `- Readiness:` field, which is an output of the review and not of authoring.

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. One imprecise decision is replaced by a precise one: the choice between two existing dependency disposition codes stops being made by searching a reason string for the words `not in this run` and starts being made from the queue membership the caller already knows. Four functions in the pure policy module gain one optional keyword argument, four call sites supply it, one refusal message in `runner_shared` stops claiming a target is `external` when the code that wrote it never checked, and seven tests are added. No disposition is renamed (spec `25kzda` owns those names), no satisfaction verdict changes, and the maintainer's 2026-09-19 one-authority ruling on `edge_satisfied` is respected rather than reopened. The operator-visible effect is that a run whose prerequisite is sitting in its own queue is told to resume instead of being told, falsely, that resuming can never help. The fix was prototyped in memory against the real functions before being written down, and re-measured independently at review, which both confirmed the defect and corrected three of the plan's own findings (F-05's row count, F-07's vanished guard test, F-09's unchanged outcome word). THE ONE REAL RISK IS NAMED IN F-05 AND IS NOT HYPOTHETICAL, though its shape is the opposite of comforting: the obvious implementation (deriving membership from the entries already passed in) reddens only ONE shipped row, because `dependency_not_met` is a SUBSTRING of `dependency_not_met_external` and three of the four dependency rows therefore pass even when mislabelled. So the suite is a WEAK detector for this specific regression, and V-05(c)'s in-memory mutation proof is the evidence that actually discriminates. An executor who "simplifies" the optional parameter away will make every no-queue caller report `external` while the suite stays almost entirely green.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Six files, listed in `- Scope-Paths:`. FOUR NEGATIVE CONSTRAINTS CARRY REAL WEIGHT. FIRST, do NOT make `edge_satisfied` read `by_id` or otherwise consult queue status in its SATISFACTION decision; that is a standing maintainer ruling with a measured nine-item cascade behind it, and OQ-02 refuses it explicitly. SECOND, do NOT rename, merge, or re-gloss `dependency_not_met` or `dependency_not_met_external`; spec `25kzda` 5.4 owns both, and the remedies they carry are the operator-actionable difference this plan exists to attach correctly. THIRD, do NOT edit, weaken, or delete any of the four existing rows of `_DISPOSITION_LINES`, and do not change `_queue_entry`; row 3 in particular pins the no-membership fallback and its old wording is the point. FOURTH, do NOT strip the token prefix from the drain path's reason strings (backlog `csjq81`) and do NOT touch the freeze-time gate's own `is not in this run` clause, which F-11 measures to be true and which a shipped test pins. An out-of-scope edit that turns out to be necessary is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, and a declared path you end up not modifying needs a `--scope-ack`; neither is a reason to stop.

EXECUTION CONTRACT. Commit only the six files in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`. Do not push. THE MUTATION PROOFS ARE STAGED IN MEMORY, NOT BY EDITING A FILE: every file here is a shared-checkout file, and a `git checkout` restore after a minute-long suite run silently discards a co-worker's concurrent edit. The execution contract's "verify what you are actually about to commit" step is not optional here. Do NOT update or delete `tests/fixtures/runnerlayer_rehomed_premove_fingerprints.json`, which contains `edge_satisfied`'s old body but is read by nothing (F-13) and which two executed plans instruct be left in place.

LIFECYCLE TRANSITION. The terminal transition is owed unconditionally but its OWNER is conditional: under `aw oc run` / `aw agy run` the runner performs finalize and the executor must NOT also run it; executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll a `git mv` to `executed/`.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY, stated for the executor: by adding tests that would also pass without the fix. Three shapes do that and all three are measured. A test asserting the in-run code by SUBSTRING passes against a renderer emitting the external code for everything, since one name is a prefix of the other (V-05(b) forbids it) - and F-05 measures that THREE OF THE FOUR ALREADY-SHIPPED dependency rows have exactly this weakness, so this is a demonstrated property of this very table and not a cautionary hypothetical. A test supplying an EMPTY member set proves nothing about the external branch, because everything is a non-member of an empty set (V-01(e) forbids it). And a test that greps `runner_shared.py` for the absent phrase pins code structure rather than behavior and would pass even if the function were never called (V-06(b) forbids it). So a green suite is NOT sufficient evidence for this plan; V-05(c)'s RED mutation run is, and it must be performed and pasted rather than reasoned about.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms AND all six `V-*` items carry pasted evidence with `Result: verified`, including the V-05(c) mutation proof and the V-01(c) end-to-end reason/code decoupling proof. On completion the runner sets backlog `8mohre` to `graduated`; this plan inherits its `- Blocks-Release: next` gate, so that gate is preserved rather than dropped.
