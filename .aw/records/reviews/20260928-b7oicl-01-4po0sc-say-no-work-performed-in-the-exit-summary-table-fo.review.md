# Review findings: plan 4po0sc

- Subject-Id: 4po0sc
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `50777ca3` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `"outcome":"clean"`, `findings: 0`) and `--phase
review-finalize --agent` conforms after revision with `findings: 0`.
`check_engine.evaluate_durable_carrier` returned ZERO drifts and `aw check` reports 2 repository
errors, neither naming this plan or its Set. No pre-review snapshot was owed: `git status --short`
reported the tree clean with the plan committed and unmodified.

ALL TWELVE AUTHORED FINDINGS REPRODUCED INDEPENDENTLY, several to the digit, and this is the
highest-evidence plan of this sweep. F-01: the item's `1/1 100%` is stale and the same shape renders
`Progress: 0/1  [          ]   0% (1 reviewed)`; commit `a0d6e04b` exists and is the `progdenom` fix.
F-02: one `reviewed`/zero-attempt item renders `Outcome: COMPLETED` while
`render_disposition_summary` on the SAME queue prints `NO WORK WAS PERFORMED: this run matched 1
artifact(s) and acted on NONE of them` and `total: 1 matched, 0 acted on, 1 not acted on`. F-03: the
success tuple is `("executed", "reviewed", "approved", "substantially-complete")` and
`EXECUTE_REPORTING_SUCCESS_STATES` is `{'approved', 'executed'}` with `reviewed` absent, so the
renderer is indeed the last surface treating `reviewed` as run-level success. F-04: exit codes are 1,
1, 0 on the three shapes, exactly as claimed. F-06: `summarize_dispositions` on the all-already-executed
shape returns `(('ipd_already_executed', 1, None),)`, `remedy_for_disposition` returns `None` for it,
and `DISPOSITIONS_NEEDING_NO_REMEDY` is `['acted_on', 'ipd_already_executed']`. F-07: SGR codes
`COMPLETED`->32, `STRANDED`->31, `PARTIAL`->33, `NO WORK PERFORMED`->36, `NOTHING TO DO`->36, all five
matching. F-08: `run_selection_policy`'s module-level first-party imports are exactly `{selectors,
status_set}`, `render_stream` has ZERO function-local imports, the combined closure reaches none of
`render_stream`/`runner_shared`/`oc_runipd`/`agy_runipd`, and the guard file was indeed deleted by
`19313eed`. F-09: zero `COMPLETED` occurrences in `.aw/records/specs/` (the two `STRANDED` hits are
unrelated prose). F-10: both prior `and`-chain conditions and their comments are present verbatim.
F-11 and F-12: all cited symbols and all three cited plans (`bsc457`, `r2i1b1`, `ys1dor`) confirmed
`executed`.

I ALSO RAN THE PLAN'S OWN PROPOSED PREDICATE AGAINST THE REAL RENDERER over every shape, and it
behaves as designed: exactly three change, all `COMPLETED` -> `NO WORK PERFORMED`. THE DESIGN IS RIGHT
AND ONE CHOICE DESERVES SPECIFIC PRAISE: F-06's second condition (require at least one disposition to
carry a REMEDY, asked of `remedy_for_disposition` rather than by re-listing a set) was not asked for by
the backlog item, and without it a Set whose members already executed on disk - which correctly acts on
nothing - would have been relabeled. The plan found that itself, measured it, and recorded the
correction to the item in OQ-01. Its refusal to touch progress arithmetic (because `progdenom` already
fixed it) and its refusal to remove `reviewed` from the success tuple (because review-action runs
legitimately succeed at `reviewed`) are both correct and both evidenced.

WHAT REVIEW FOUND IS IN THE FIXTURES, NOT THE DESIGN, AND TWO OF THE THREE WOULD HAVE COST AN EXECUTOR
A CYCLE.

**TWO REGRESSION SHAPES WERE SPECIFIED BY REFUSAL RECORD WHERE THE CODE KEYS ON `status` (PR-601).**
E-05 listed "a recorded `Refusal` with zero attempts -> `BLOCKED`" and "a recorded `merge-refused`
refusal that ran -> `FAILED`". Neither word comes from the refusal: the `FAILED` and `BLOCKED` arms are
`it.get("status") in (...)` over literal status tuples and never call `refusal_of_item`. Measured: a
zero-attempt item carrying a real `awaiting-human-decision` refusal renders `QUEUED` at `status:
reviewed`, and `BLOCKED` only at `status: blocked` or `fail-gate`; a `merge-refused` refusal WITH
attempts renders `PARTIAL` at `status: executed`, and `FAILED` only at `status: merge-refused`. So an
executor building those two fixtures exactly as written gets two failures in a plan whose whole risk
story is "did I relabel something I should not have", and the most likely reaction is to believe the
change broke something. The words are right for the right statuses; the attribution was wrong.

**E-02'S CENTRAL SAFETY ARGUMENT WAS ARGUED BUT NOT TESTABLE (PR-602).** The plan says at length, and
correctly, that placing the new condition last is load-bearing because earlier placement would relabel
existing outcomes. Nothing in E-04 or E-05 could catch that. Measured, there ARE such shapes: the
predicate returns TRUE for `status: not-attempted` (renders `QUEUED`) and `status: not-run` (renders
`BLOCKED`), because both derive `type_or_status_not_runnable`, which carries a remedy. Both are
correctly left alone, and the ONLY reason is that neither reaches the `COMPLETED` branch. That makes
the placement claim falsifiable: pin both as predicate-True-word-unchanged, then move the condition
earlier and watch them go red. Without it, the one argument the plan repeats most has no guard.

**THREE FIXTURE FACTS SILENTLY PRODUCE A GREEN TEST FOR THE WRONG REASON (PR-603).** All three were hit
while building fixtures at review. `needs_input` is read as an ENTRY KEY (`if bool(get("needs_input"))`),
not as `final_outcome: needs_input`; an entry carrying only the latter derives
`type_or_status_not_runnable`, which is E-04's case (c), so case (a) still passes but stops
distinguishing the needs-approval disposition from the not-runnable one. Case (d)'s false-positive
fixture must set `status: executed`, not only `initial_status: executed`, because the
`SKIP_ALREADY_EXECUTED` arm tests `status == "executed"`; set only `initial_status` and the entry
derives a disposition that HAS a remedy, so the fixture asserts the opposite of its intent and the
F-06 protection is untested. And `attempts` must be a LIST: the renderer iterates it and an int raises
`TypeError: 'int' object is not iterable`. Separately, `Palette` is defined in `render_stream`, not
`term`; `from agent_workflows.term import Palette` raises `ImportError`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-601 | MEDIUM | IN-SCOPE | E. Testing (a fixture that cannot produce the asserted result) | E-05 as authored: "a recorded `Refusal` with zero attempts -> `BLOCKED`; a recorded `merge-refused` refusal that ran -> `FAILED`"; the outcome chain's `FAILED` arm tests `it.get("status") in ("failed", "failed-safely", "fail-lane", "fail-verify", "fail-merge", "integration-blocked", "merge-conflict", "merge-needs-human", "merge-refused")` and its `BLOCKED` arm `("blocked", "dependency-blocked", "fail-gate", "fail-begin", "fail-depend", "not-run")`, neither calling `refusal_of_item`; measured: refusal + `status: reviewed` -> `QUEUED`, refusal + `status: blocked` -> `BLOCKED`, refusal + `status: fail-gate` -> `BLOCKED`; `merge-refused` refusal + attempts + `status: executed` -> `PARTIAL`, + `status: merge-refused` -> `FAILED` | **TWO OF EIGHT REGRESSION FIXTURES ARE SPECIFIED BY A FIELD THAT DOES NOT PRODUCE THE ASSERTED WORD.** The refusal record is orthogonal to `FAILED`/`BLOCKED`; only `status` selects them. An executor building these as written sees two red assertions in the exact area this plan's risk story is about (did the change relabel an existing outcome), and the natural conclusion is that the change regressed something it did not touch. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now pins both as STATUS shapes (`status: blocked`/`fail-gate` -> `BLOCKED`; `status: merge-refused` with attempts -> `FAILED`), states that the refusal may be present or absent without changing the word, and offers the with/without pair as the way to assert the refusal's independence if wanted. New F-13 records the mechanism with all five measurements. F-05's finding text carries the correction rather than silently dropping the two shapes. V-05's fixture list is rewritten status-first and warns explicitly that a refusal-built fixture fails and looks like a regression in this plan when it is not. |
| PR-602 | MEDIUM | UNDER-SCOPE | D. Anti-regression (the plan's main safety argument had no test) | E-02's own prose ("PLACEMENT LAST IS LOAD-BEARING ... testing this predicate any earlier would RELABEL those existing outcomes, which is a regression dressed as the feature") with no corresponding assertion in E-04 or E-05; measured: predicate True for `status: not-attempted` (word `QUEUED`) and `status: not-run` (word `BLOCKED`), both correctly unrelabeled | **THE CLAIM THE PLAN REPEATS MOST IS THE ONE NOTHING GUARDS.** Two real shapes make the predicate fire while correctly keeping their existing word, and the sole protection is branch placement. Nothing in the authored test plan detects a future edit that moves the condition earlier, so the regression the plan most fears is exactly the one its suite would miss. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | New F-14 records both shapes with their measured predicate answers and words. E-05 gains them as explicit predicate-True-word-unchanged pins with the reason stated. V-05 requires printing predicate-and-word side by side for both AND showing them RED under the move-it-earlier mutation, then restored - which converts the argument into a falsifiable guard in the same shape as the plan's two existing deliberate-failure demonstrations. |
| PR-603 | LOW | IN-SCOPE | E. Testing (fixtures that pass for the wrong reason) / F. Honest documentation | `derive_item_disposition`'s second arm is `if bool(get("needs_input"))`; its `SKIP_ALREADY_EXECUTED` arm is `if status == "executed" and not get("attempts")`; `render_run_summary_table` contains `for att in attempts:`; measured: `final_outcome`-only entry -> `type_or_status_not_runnable`; `initial_status`-only entry -> `type_or_status_not_runnable` (has a remedy); int `attempts` -> `TypeError: 'int' object is not iterable`; `grep -rn "class Palette"` -> `render_stream.py` only, and `from agent_workflows.term import Palette` -> `ImportError` | Four fixture-construction facts the plan does not state, two of which produce a GREEN test that proves nothing: case (a) built on `final_outcome` silently collapses into case (c), and case (d) built on `initial_status` alone asserts the opposite of the F-06 protection it exists to prove. The other two fail loudly (a `TypeError` and an `ImportError`) and merely cost time. The plan cites `Palette(False)` five times without naming its module. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now names all three fixture rules with the measurement and the consequence of getting each wrong, and specifies `render_stream.Palette(False)` with F-15 recording the `ImportError`. Case (d)'s wording changed from `initial_status: executed` to `status: executed`. New F-15 records the `Palette` location. V-02 also updated to `render_stream.Palette(False)` and to require fixtures built per those rules. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-601: two regression fixtures cannot produce their asserted word. Drop those two shapes, or respecify them by `status`? | RESPECIFY BY `status`, keeping both words in the fence and recording the mechanism in a new finding. | (a) Drop the two shapes: rejected, `BLOCKED` and `FAILED` are two of the seven outcome words this plan must prove it did not disturb, and dropping them would leave the two largest pre-existing branches unfenced. (b) Leave them and let the executor work it out: rejected, the failure mode is an executor concluding the plan's own change caused a red assertion, which is the most expensive possible misreading in a plan about not relabeling outcomes. | Read both outcome arms at the symbol and confirmed neither calls `refusal_of_item`; measured five status/refusal combinations and recorded which word each produces. | yes |
| D-2 | PR-602: E-02's placement argument has no guard. Add one, or accept the argument as reviewed-and-sound? | ADD THE GUARD, using the two shapes that already exist in the corpus of possible queues. | Accept the argument: rejected. The plan itself names relabeling an existing outcome as "a regression dressed as the feature" and separately names a false `NO WORK PERFORMED` as the worse direction of error, so leaving the mechanism that prevents it untested contradicts the plan's own risk analysis. It is also cheap: the shapes exist, the predicate already answers True on them, and the mutation is a two-line move. | Measured the predicate and the rendered word for `not-attempted` and `not-run`; both fire the predicate and both keep their word solely by branch placement. | yes |
| D-3 | OQ-01 resolved that `acted == 0` alone is insufficient and a remedy condition is required. Accept? | ACCEPT, independently confirmed, and it is the best judgement in the plan. | Key on `acted == 0` alone as the backlog item literally proposed: rejected on measurement. The all-already-executed shape has `acted == 0` and is legitimately `COMPLETED`; relabeling it would train an operator to ignore the new word, which destroys the value of adding it. | Re-measured: `summarize_dispositions` -> `(('ipd_already_executed', 1, None),)`; `remedy_for_disposition('ipd_already_executed')` -> `None`; the predicate correctly returns False; the shape's rendered word stays `COMPLETED`. | yes |
| D-4 | OQ-02 resolved that the new `run_selection_policy` import is safe despite the module's near-purity note. Accept? | ACCEPT, independently confirmed, with the plan's honest caveat about the deleted guard preserved. | Duplicate the acted-on/remedy judgement inside `render_stream` to avoid the import: rejected, that recreates the two-vocabularies-for-one-fact drift `bsc457` extracted `derive_item_disposition` to prevent, which is the same defect class this plan exists to close. | AST-measured `run_selection_policy`'s module-level first-party imports as exactly `{selectors, status_set}`; combined transitive closure contains none of `render_stream`, `runner_shared`, `oc_runipd`, `agy_runipd`; `render_stream` has zero function-local imports today; `tests/test_refusal_surfacing.py` confirmed deleted by `19313eed`, so the plan's caveat that nothing guards this is true and V-01's in-tree measurement requirement is the right response. | yes |
| D-5 | OQ-03 chose the phrase `NO WORK PERFORMED`. Accept, or escalate the wording to the maintainer? | ACCEPT without escalation. | Escalate as a `- Blocking: yes` question: rejected. It is a one-word human banner, the plan pins it through a CONSTANT so changing it is one edit, and the choice is evidenced (it matches `SUMMARY_NO_ACTION_VERDICT`'s opening words three lines below it, and `PARTIAL`/`QUEUED` already mean other things). A reversible cosmetic choice with a stated reversal cost does not need a human gate. | Verified `SUMMARY_NO_ACTION_VERDICT` begins `NO WORK WAS PERFORMED`; verified `STRANDED_OUTCOME`'s docstring states the one-vocabulary principle the plan cites; E-04 asserts through `NO_WORK_OUTCOME` rather than repeating the literal. | yes |
| D-6 | F-09 claims no spec amendment is owed. Accept, or require a spec edit for a new banner word? | ACCEPT. No `.spec.md` in `- Scope-Paths:` is correct. | Declare and amend `25kzda` 5.6: rejected, that section enumerates per-ITEM outcomes and EXIT CODES, neither of which changes, and it does not enumerate the run-level banner at all. Adding a banner vocabulary to a spec because one word was added would invent a contract nobody agreed to. | Read Section 5.6's two enumerations; `grep` found ZERO `COMPLETED` occurrences across `.aw/records/specs/` and the only `STRANDED` hits are unrelated prose in `r07vma` and the attention spec; `ys1dor` added `STRANDED` to this same banner with no spec in its `- Scope-Paths:`. | yes |

No `Reversible: no` decision was taken in this round, so no escalation under Step 3.1 is owed. Every
finding is `FIXED`; none was deferred or left open, so no `- Blocking: yes` escalation under Step 4 is
owed either. All three of the plan's open questions were already `resolved` at authoring and all three
were independently re-measured and upheld (D-3, D-4, D-5), so the plan carries no open question.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0` BEFORE any
  edit; `--phase review-finalize --agent` -> exit 0, `"findings":0` after all edits.
- `check_engine.evaluate_durable_carrier` -> `drifts: 0`. `aw check` -> 2 repository errors, neither
  naming this plan or its Set. All cited artifacts resolve: `b7oicl` (graduated, `Work-Kind: bug`,
  `Blocks-Release: next`, `Graduated-To: b7oicl`), `5hf2qy` (open), `bsc457` / `r2i1b1` / `ys1dor` (all
  executed).
- Suite baseline BARE: `2935 passed, 2 skipped, 3 warnings in 42.72s`. Targeted regression set (all
  seven files confirmed present): `163 passed in 23.44s`. No code, test, configuration, spec or doc
  file was modified by this review.
- **F-01 reproduced.** The item's own text quotes `Progress: 1/1  [##########] 100% (1 reviewed)`; the
  same shape renders `Progress: 0/1  [          ]   0% (1 reviewed)` today. `git log -S` confirms
  `a0d6e04b` "fix(runner): count DISPATCHABLE WORK in progress, not queue length (progdenom)".
  `dispatchable_work_total`'s body ends `... or 1`, confirming the deferred `5hf2qy` defect, and the
  eight-plan shape does render `Progress: 0/1` and `Total (0/1 items run)` above eight rows.
- **F-02 reproduced side by side** on one queue entry, output quoted in the amended F-02.
- **F-03 confirmed at the symbol.** Success tuple read verbatim;
  `EXECUTE_REPORTING_SUCCESS_STATES` -> `['approved', 'executed']`; `'reviewed' in
  success_states_for_action("execute")` -> `False`.
- **F-04 reproduced exactly.** `deliberate_stop_exit_code` -> 1 (needs-approval), 1 (not-runnable), 0
  (all-already-executed).
- **F-05 re-derived against the REAL renderer** (not a prototype) over twelve shapes plus four refusal
  and signal variants: exactly three change, all `COMPLETED` -> `NO WORK PERFORMED`.
- **F-06 reproduced exactly**, figures quoted in the findings table.
- **F-07 reproduced exactly**: 32 / 31 / 33 / 36 / 36 for the five cited words, plus `INTERRUPTED`->33
  and `FAILED`->31 as controls.
- **F-08 re-measured by AST.** `run_selection_policy` -> `{selectors, status_set}`; `render_stream` ->
  `{lifecycle_style, term}`; combined closure 18 modules (the plan says 21, a methodology difference in
  edge collection, not a safety difference) containing NONE of the four forbidden modules;
  `render_stream` function-local imports -> `0`; `tests/test_refusal_surfacing.py` absent, deleted by
  `19313eed`.
- **F-09 confirmed.** Zero `COMPLETED` in `.aw/records/specs/`; the two `STRANDED` hits are unrelated
  prose ("THE MIGRATION LEAVES NO SET STRANDED" in `r07vma`, and an `aw attention` context).
- **F-10 confirmed verbatim**: both prior `and` conditions present with their comments, including
  `zzcrlo`'s "do NOT 'fix' this by removing `substantially-complete` from the tuple above" and
  `ys1dor`'s "PLACED LAST IN THE SUCCESS BRANCH, WHICH IS LOAD-BEARING rather than stylistic".
- **F-11 confirmed.** `tests/test_run_selection_policy.py::test_the_line_and_the_summary_cannot_disagree_about_one_artifact`
  exists; `tests/test_finalize_sendback.py::TheRunOutcomeReflectsARefusedFinalize` exists;
  `tests/test_zero_dispatch_outcome.py` correctly does not.
- **PR-601 measured**, five status/refusal combinations, results in the findings table.
- **PR-602 measured**: `not-attempted` -> pred `True`, word `QUEUED`; `not-run` -> pred `True`, word
  `BLOCKED`.
- **PR-603 measured**: all four facts hit directly while building fixtures, including the live
  `TypeError` and `ImportError`.
- **Machine-surface claim confirmed.** No parser of this banner: the only `Outcome:` strings in
  `run_cli.py` are its own unrelated `COMPLETE (all predicates satisfied)` / `INCOMPLETE` lines, and
  `run_viewer.py` has none.
- All probes ran in-process against in-memory queue dicts; no run directory was created or read, no
  repository file was written by a probe, and `git status --short` reports only the plan and this
  record.
