# IPD: Make the scaffolded orchestrator skeleton conform to the typed child-tracking row grammar, then gate begin on it

- Date: 2026-09-29
- Kind: child
- Concern: `aw ipd scaffold` emits an orchestrator skeleton that VIOLATES the rule the same toolkit enforces. Measured at HEAD `10b22ef1` by calling `ipd_authoring.build_skeleton(kind="orchestrator", ...)` in process and passing the result to `ipd_lint.orchestrator_row_conformance`: the result is `conforming=False`, its single row `E-01` is refused for `not-a-typed-child-tracking-row`, and the whole child table is refused with `table_reason` "no readable `## Child IPDs, sequence, and dependencies` table; section present but contains no parseable table row". The scaffold emits the untyped row `- [ ] E-01 TODO one observable action.` and, where the child table belongs, the prose placeholder `TODO: child IPD table (Order | File | What it does | Depends on).`. So the surface an author starts from is the one shape the rule forbids, and spec `r07vma` OQ-01's whole argument for choosing TYPED (that "an author who starts from a conforming skeleton is shown the shape rather than told the rule") does not hold in shipped code.
- Scope: IN: make `ipd_authoring.build_skeleton` emit a CONFORMING orchestrator skeleton (a typed `CONFIRM <child-id6> REACHED <status>` row plus a child table carrying an `Id` column); regenerate the byte-pinned orchestrator template from it; move the coupled scaffold-anchor fixtures in `tests/test_orchestrator_retirement.py` in lockstep; add `pre-execution` back to `ipd_lint._ORCH_ROW_BLOCKING_CHECKPOINTS` so `aw ipd begin` is gated; and update the stale comment block that documents the exclusion. OUT: the `child` skeleton, which has no child table and no orchestrator rows and is deliberately untouched; the rule logic in `orchestrator_row_conformance`, which is correct and is only being satisfied rather than changed; the `/plan-review` repair loop and both runners' pre-queue gate, which already call the shared function and need no edit; spec `r07vma` OQ-01's full "render the instructions from the grammar" direction, which is explicitly non-blocking and larger than this defect; and any migration of the pre-existing orchestrator corpus, which E-01's census shows is already unnecessary.
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/ipd_lint.py, .aw/system/workflows/assess/templates/orchestrator-ipd.md, tests/test_orchestrator_retirement.py, tests/test_ipd_authoring.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: htce8t
- Set: htce8t
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: zojfn6

## Workflow history

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from open backlog item `htce8t`. Every finding below was MEASURED in this lane at HEAD `10b22ef1` by running the code, not inferred from the backlog item's prose, and two of the backlog item's own claims did not survive that check (F-3 and F-4). The remedy was prototyped end to end under a pytest plugin that monkeypatched `build_skeleton` and the constant, so the blast radius in F-5 is an observed suite result rather than an estimate.

## Goal

Make the shipped orchestrator skeleton satisfy `IPD-S407`, so a freshly scaffolded orchestrator conforms to the grammar the toolkit enforces, and then close the gate that could not be closed while it did not: add `pre-execution` back to `_ORCH_ROW_BLOCKING_CHECKPOINTS` so `aw ipd begin` refuses an untyped orchestrator row.

READ THE GOAL PRECISELY. This plan does not widen, weaken, or re-implement the conformance rule. `orchestrator_row_conformance` is correct as shipped and is not edited. The defect is that the AUTHORING SURFACE emits a shape that rule forbids, and the fix is to change the skeleton so the two agree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-derive the corpus facts this plan's safety rests on

- [ ] E-01 RE-DERIVE the live orchestrator conformance census and the `aw check all` baseline, and RECORD both numbers, before changing any code. Walk every `*.ipd.md` under `.aw/records/plans/`, call `ipd_lint.orchestrator_row_conformance` on each, and report per-bucket `conforming/total` over the plans where `applies` is True. This plan's authoring measured `pending: 3/3`, `executed: 11/63`, `superseded: 0/3` (see F-6), and the `pending` number is the one that matters: if it is still all-conforming, adding `pre-execution` strands NO live plan and spec `r07vma` criterion 12 is satisfied with no migration. If a NON-conforming pending orchestrator has appeared since, STOP and report it rather than proceeding, because gating `pre-execution` would then refuse a real plan at `begin` with no migration authored.
  - Depends on: none
  - Expected outcome: a recorded per-bucket census plus an `aw check all --agent` finding count, both pasted. This plan's baseline was 33 findings, none of them `IPD-S407`.
  - Execution state: pending

### Task group 2: make the scaffolded orchestrator conform

- [ ] E-02 TEACH `ipd_authoring.build_skeleton` to emit a CONFORMING orchestrator skeleton, changing the `orchestrator` kind ONLY. Two edits, and both are required because the rule refuses on both counts independently (F-1): (a) the execution placeholder must become a typed row of the exact shape `_ORCH_ROW_RE` accepts, `- [ ] E-01 CONFIRM <child-id6> REACHED executed`, carrying its `- Depends on: none` edge; and (b) the `S.H_CHILD_IPDS` body must become a real markdown table whose header includes an `Id` column, with one placeholder row whose `Id` cell holds that same `<child-id6>`. The two must name the SAME placeholder id6, because `orchestrator_row_conformance` resolves the row's child against `_child_id6_index`, which reads the table's `Id` column. Keep the `child` kind's placeholder EXACTLY as it is: a child plan has no child table and the rule reports `applies=False` for it, so touching it is out of scope and would churn the byte-pinned child template for nothing.
  - Depends on: E-01
  - Expected outcome: `orchestrator_row_conformance(build_skeleton(kind="orchestrator", ...))` returns `conforming=True` with an empty `table_reason` and one row whose three typed fields resolve; the same call for `kind="child"` still returns `applies=False`; and the child skeleton's bytes are unchanged.
  - Execution state: pending

- [ ] E-03 KEEP the authoring-placeholder predicate honest in the same change. `_AUTHORING_PLACEHOLDERS` currently lists the literal string `- [ ] E-01 TODO one observable action.`, which E-02 deletes from the orchestrator skeleton, and that tuple is what makes `authoring_placeholders_resolved` report a fresh scaffold as an unfinished stub (it gates the `check.ipd-draft-ready-to-review` nudge). Verify the predicate still returns False for a FRESH orchestrator skeleton after E-02 and, if it does not, add an anchored marker for whichever placeholder text the new skeleton introduces. THE ANCHOR MUST BE A PLACEHOLDER AN AUTHOR IS EXPECTED TO REPLACE, not the typed row's permanent structure: the file's own comment beside `_SECTION_BODY[S.H_PROJECT_CONVENTIONS]` records why permanent guidance must NOT be listed there ("this is PERMANENT guidance an author is not expected to delete, so listing it would make every plan look forever-unfinished and silence the `check.ipd-draft-ready-to-review` nudge"). Measured under the prototype: the predicate already returns False for both kinds, because the new table row retains `TODO child plan filename` and the skeleton retains six other listed markers, so this item is expected to CONFIRM rather than to edit.
  - Depends on: E-02
  - Expected outcome: `authoring_placeholders_resolved` returns False for a freshly scaffolded orchestrator AND for a freshly scaffolded child, with the result pasted for each.
  - Execution state: pending

- [ ] E-04 REGENERATE the byte-pinned orchestrator template `.aw/system/workflows/assess/templates/orchestrator-ipd.md` from the changed generator, and leave `templates/ipd.md` untouched. `tests/test_ipd_templates.py::TemplateParityTests::test_orchestrator_template_matches_generator` asserts byte equality against `build_skeleton(kind="orchestrator", title="<short title of the coordinated change>", author="<agent/model>", when="<YYYY-MM-DD>", set_name="<set-id>", order=0, plan_id="tmp1d6")`, so this is the mechanical consequence of E-02 and not a judgement call. Regenerate with exactly those pinned argument values rather than hand-editing the markdown, which is what the parity test exists to force. Measured under the prototype: this was the LAST remaining suite failure once the fixtures moved, and regenerating closes it while the regenerated template still lints `conforming` at the `author` checkpoint.
  - Depends on: E-02
  - Expected outcome: the orchestrator template matches the generator byte for byte, `templates/ipd.md` is unchanged, and both template lint tests still pass.
  - Execution state: pending

- [ ] E-05 MOVE the coupled fixture anchors in `tests/test_orchestrator_retirement.py` in LOCKSTEP with E-02. `_structurally_conforming_plan` builds its fixture from the REAL scaffold and then substitutes into it by matching literal scaffold text, so E-02 breaks three of its anchors at once: the child-table replacement keys on the prose placeholder string, the checklist replacement keys on a regex containing `### Task group 1: TODO\n\n- \[ \] E-01 TODO one observable action\.`, and the `untyped_checklist=True` path RELIES on the scaffold supplying an untyped row that will no longer be there. Re-point the first two at the new skeleton text, and make the untyped path INJECT its untyped row explicitly rather than inheriting one. THE UNTYPED PATH MUST KEEP TESTING WHAT IT TESTS: `OrchestratorRetirementRowAuditAndHonestRecord::test_an_orchestrator_with_untyped_checklist_rows_is_refused_at_retirement` and the `untypedrows` row of `TheGateDoesNotOpenForOrdinaryPlans` both depend on a genuinely non-conforming orchestrator existing, so this must remain a real untyped fixture; do NOT satisfy the anchors by making that fixture conforming, which would silently delete the coverage that the rollup refuses a non-conforming parent. Note the table anchor spans the section HEADING as well as the table body, because the fixture's `_table` helper emits its own `## Child IPDs...` heading (a prototype that replaced the body alone produced a DUPLICATED heading and an unparseable table, which is how this was found).
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_orchestrator_retirement.py` is fully green, with the untyped-row refusal test still asserting a refusal rather than passing vacuously.
  - Execution state: pending

### Task group 3: close the gate the defect held open

- [ ] E-06 ADD `pre-execution` to `ipd_lint._ORCH_ROW_BLOCKING_CHECKPOINTS` and REWRITE the stale comment that justifies its exclusion. The constant currently reads `frozenset(("review-finalize", "pre-transition"))`, and the long comment above it explains the exclusion by naming a specific blocker: that including `pre-execution` broke `tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_an_orchestrator` because that test's fixture comes from the real scaffold. THAT COMMENT IS NOW STALE ON TWO COUNTS AND MUST NOT BE LEFT IN PLACE (F-3, F-4): the test it names no longer exists under that name, and the named blocker no longer reproduces at all, because plan `kjqqzf` gave the fixture typed rows. Replace the `pre-execution` paragraph with what is true after this plan: it blocks at `begin` because the scaffold now conforms, so the gate can no longer refuse a freshly scaffolded orchestrator. Leave the `author` and `post-transition` exclusions and their reasoning ALONE; `author` is where `aw check plans` sweeps and this plan makes no claim about that phase.
  - Depends on: E-01, E-02, E-04, E-05
  - Expected outcome: `aw ipd begin` on an orchestrator carrying an untyped row is refused naming `IPD-S407`, the same command on a freshly scaffolded orchestrator is NOT refused for that reason, and the comment block beside the constant contains no reference to the removed test or to the scaffold being non-conforming.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every anchor in this plan is a symbol or a quoted string for that reason.
- THE SUITE IS RUN BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, so `python3 -m pytest` is already quiet, parallel and fast-scoped. Adding `-q` compounds into `-qq` and suppresses the `N passed` summary this plan's validation requires pasted.
- ONE IMPLEMENTATION OF THE RULE (spec `r07vma` R3). `/plan-review` and both runners already call `ipd_lint.orchestrator_row_conformance`; `ipd_lint.check_orchestrator_rows` delegates to it entirely and its docstring says so. This plan therefore edits the SKELETON and the CHECKPOINT SET, and adds no second regex anywhere.
- A DELETED CHECKLIST IS NOT AN ACCEPTABLE FIX (spec `r07vma` R2, and the refusal text's own `ORCH_ROW_NO_DELETION` clause). Measured while prototyping: a skeleton with the `E-01` row removed entirely is refused by `IPD-I303` at every checkpoint including `author`, so "emit no rows" is not even mechanically available as a shortcut. It is named here because it is the tempting wrong answer the spec predicts.
- THE TEMPLATES ARE GENERATED, NOT HAND-MAINTAINED. `tests/test_ipd_templates.py` asserts byte parity between each template and `build_skeleton` with pinned arguments, so any skeleton change is a two-file change by construction.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-1 | THE SHIPPED ORCHESTRATOR SKELETON IS REFUSED ON TWO INDEPENDENT COUNTS, not one. Calling `orchestrator_row_conformance` on `build_skeleton(kind="orchestrator", ...)` yields `conforming=False` with row `E-01` refused as `not-a-typed-child-tracking-row` AND `table_reason` "no readable `## Child IPDs, sequence, and dependencies` table; section present but contains no parseable table row". Fixing only the row would leave every row refused with `child-table-cannot-resolve-a-child-id6` instead, because `orchestrator_row_conformance` resolves each row's child through `_child_id6_index`. This is why E-02 is one item with two mandatory edits. | Measured in process at HEAD `10b22ef1`. `ipd_authoring._exec_placeholder_leaf` returns `- [ ] E-01 TODO one observable action.`; `_SECTION_BODY[S.H_CHILD_IPDS]` is `TODO: child IPD table (Order | File | What it does | Depends on).`; `ipd_lint._ORCH_ROW_RE` requires `^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$`. |
| F-2 | THE GATE IS GENUINELY OPEN AT `begin` TODAY, so this is not a cosmetic tidy. `lint_text` on the scaffolded orchestrator reports `IPD-S407` at `review-finalize` and `pre-transition` but ZERO `IPD-S407` findings at `pre-execution`, and `ipd_lifecycle.begin` gates on the `pre-execution` lint. So an orchestrator carrying an untyped row can be begun. | Measured per checkpoint: `author` 0, `review-finalize` 1, `pre-execution` 0, `pre-transition` 1, `post-transition` 0. `ipd_lint._ORCH_ROW_BLOCKING_CHECKPOINTS` is `frozenset(("review-finalize", "pre-transition"))`. |
| F-3 | THE BACKLOG ITEM'S NAMED PIN DOES NOT EXIST. The item says `tests/test_orchestrator_row_grammar.py::TheRuleActuallyFires::test_the_SHIPPED_SCAFFOLD_is_not_conforming_which_is_why_begin_is_not_gated` "pins the current state and FAILS LOUDLY when the scaffold is fixed, pointing the reader here". There is no such FILE in the tree, and a repository-wide grep for the test name returns nothing. So the executor must NOT go looking for a test to delete, and the "fails loudly and points here" safety net the item promises is NOT present. | `tests/test_orchestrator_row_grammar.py` is absent from `tests/`; `grep -rn "SHIPPED_SCAFFOLD" tests/` returns no match. |
| F-4 | THE BLOCKER THAT FORCED THE EXCLUSION NO LONGER REPRODUCES, which materially shrinks this plan. The comment beside `_ORCH_ROW_BLOCKING_CHECKPOINTS` says including `pre-execution` broke `TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_an_orchestrator`. That test is now named `..._still_refuses_orchestrator_and_child_without_evidence`, and with `pre-execution` added it PASSES. The reason is that plan `kjqqzf` later gave `RollupTransitionCase.make_set` typed checklist rows (a `checklist_rows` parameter emitting `- [ ] E-{order} CONFIRM {id6} REACHED executed`) plus an `untyped_checklist` opt-out, so the fixture no longer inherits the scaffold's untyped row. | Ran that single test with the constant monkeypatched to include `pre-execution`: `Ran 1 test ... OK`. `git log -S "untyped_checklist" -- tests/test_orchestrator_retirement.py` attributes the fixture change to commit `97cb2f49` "ipd(kjqqzf): stop retired orchestrator asserting work its commit denies and close row conformance hole". |
| F-5 | THE WHOLE BLAST RADIUS IS SIX TESTS, ALL FIXTURE/TEMPLATE COUPLING, AND ALL CLOSABLE. Under a prototype that monkeypatched `build_skeleton` to emit a conforming orchestrator and added `pre-execution` to the constant, the bare suite reported `6 failed, 3240 passed`. Repairing the three `_structurally_conforming_plan` anchors dropped that to `1 failed, 3245 passed`, the single remaining failure being the orchestrator template parity test, which regenerating the template closes. No production code outside `ipd_authoring` and `ipd_lint` needed to move. | Prototype run under a pytest plugin. Failures were: `test_ipd_templates.py::TemplateParityTests::test_orchestrator_template_matches_generator`; and in `test_orchestrator_retirement.py`, `RollupRetiresAnEligibleSet::test_an_eligible_set_retires_and_lands_in_executed`, `TheHonestTerminalRecord::test_honest_terminal_record_history_entry_and_actor`, `TheGateDoesNotOpenForOrdinaryPlans::test_every_gate_refuses_its_own_target_for_its_own_typed_reason`, and both `OrchestratorRetirementRowAuditAndHonestRecord` tests. |
| F-6 | NO MIGRATION IS NEEDED AND NO SET IS STRANDED, which is what makes E-06 safe. Spec `r07vma` criterion 12 demands that after any route "every one of the pre-existing orchestrators either conforms or is explicitly grandfathered ... and NONE is left in a state where a run refuses it with no available remedy". Census at HEAD `10b22ef1`: ALL 3 live `pending` orchestrators already conform. The non-conforming ones are in TERMINAL buckets (`executed` 11/63, `superseded` 0/3), which `pre-execution` never gates because a terminal plan is not begun. The spec's dated "ZERO of 32 conform" snapshot is stale: child `68uhp0` already ran that migration. | Walked `.aw/records/plans/**/*.ipd.md` calling `orchestrator_row_conformance`; counted `applies=True` plans per bucket. |
| F-7 | AN EMPTY CHECKLIST IS NOT AN ESCAPE HATCH, so the spec's feared failure mode is mechanically blocked here. Removing the `E-01` row from the skeleton instead of typing it yields `IPD-I303` at `author`, `review-finalize`, `pre-execution` and `pre-transition`. | Measured on a modified skeleton with the exec leaf deleted. |
| F-8 | A PLACEHOLDER CHILD ID6 IN THE SKELETON'S TABLE RAISES NO NEW `aw check` FINDING, so the conforming skeleton does not trade one red surface for another. Writing a freshly scaffolded orchestrator (whose table names a placeholder child that does not exist) into `pending/` and running `aw check plans --agent` produced no finding naming that plan or that placeholder id6. | Ran the probe against a temporary scaffolded plan, then removed it. Baseline `aw check all --agent`: 33 findings, none `IPD-S407`. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/ipd_authoring.py`: make the orchestrator skeleton conforming (E-02), and keep `_AUTHORING_PLACEHOLDERS` / `authoring_placeholders_resolved` honest about it (E-03). The `child` skeleton is untouched.
2. `.aw/system/workflows/assess/templates/orchestrator-ipd.md`: regenerate from the changed generator with the parity test's pinned arguments (E-04).
3. `tests/test_orchestrator_retirement.py`: re-point the three `_structurally_conforming_plan` substitution anchors, and make the `untyped_checklist` path inject its own untyped row (E-05).
4. `agent_workflows/ipd_lint.py`: add `pre-execution` to `_ORCH_ROW_BLOCKING_CHECKPOINTS` and rewrite the now-stale justification comment (E-06).
5. `tests/test_ipd_authoring.py`: add coverage that a freshly scaffolded orchestrator CONFORMS and that `aw ipd begin` is gated, so the fix cannot silently regress. This is the test surface the backlog item expected to find in a file that does not exist (F-3), authored here in the file that actually covers scaffolding.

ORDERING MATTERS FOR ONE REASON ONLY: E-06 must land with or after E-02/E-04/E-05, because gating `pre-execution` while the scaffold is still non-conforming is precisely the state the stale comment describes as refusing every freshly scaffolded orchestrator at `begin`.

## Deferred / out of scope (with reason)

- SPEC `r07vma` OQ-01 IN FULL ("hold the row grammar as data and render the refusal message, the scaffold skeleton, and the documentation from that one source") is NOT done here. This plan makes the scaffold AGREE with the grammar; it does not make the two share one generator, so the drift risk OQ-01 names is reduced but not eliminated. That question is explicitly `Blocking: no` and is a larger refactor spanning the message renderer and the docs. Note `ORCH_ROW_CANONICAL` already exists as a single rendered statement of the canonical form and is the natural seam for whoever takes OQ-01 up.
  - Carrier: u8dl3q
- THE TERMINAL-BUCKET NON-CONFORMANCE (F-6: `executed` 11/63, `superseded` 0/3) is left alone. Those plans are historical records, `pre-execution` never gates them, and editing what an executed plan RECORDS is forbidden by the execution contract.
  - Carrier-Declined: Nothing is owed, and filing an item would misrepresent a correct state as a defect. A terminal plan is never BEGUN, so `pre-execution` cannot gate it and no run can be refused by it; the non-conformance is therefore inert rather than outstanding. The only edit that would change the number is rewriting what an executed plan RECORDS, which the execution contract forbids outright ("Never change what a plan already in `.aw/records/plans/executed/` RECORDS"). Recorded here so a reviewer does not read the 11/63 figure as unfinished migration work.
- THE `author` CHECKPOINT stays excluded. This plan makes no claim about the `aw check plans` sweep phase, and widening it is a separate decision with its own corpus measurement.
  - Carrier-Declined: Nothing is owed. This row records a DELIBERATE SCOPE FENCE, not a deferred defect: the existing exclusion is justified in `ipd_lint` by a corpus measurement about `check_engine._IPD_LINT_SWEEP_CHECKPOINT` sweeping at `author`, and E-06 leaves both that behavior and its reasoning untouched. Widening it would need its own re-measurement of the sweep's blast radius on every tracked plan, which is a different question from this defect; asserting now that it SHOULD be widened would file work no measurement here supports.
- NO CHANGE TO THE SEMANTIC PROBE. Spec `25kzda` 2.5b forbids substituting a syntactic rule for it and `r07vma` criterion 9 pins it as still running; this plan touches neither.
  - Carrier-Declined: Nothing is owed, and an item here would propose work an approved spec PROHIBITS. `25kzda` 2.5b states that the coverage check is semantic and that "A syntactic rule MUST NOT be added in its place", and `r07vma` criterion 9 pins the probe as still running with its seven functions intact. This row exists to state a prohibition this plan obeys, so there is no future task to carry.

## Scope check

- Over-scope: none. Every declared path carries an item: `ipd_authoring.py` (E-02, E-03), `ipd_lint.py` (E-06), the orchestrator template (E-04), `test_orchestrator_retirement.py` (E-05), `test_ipd_authoring.py` (proposed change 5, validated by V-02/V-06).
- Under-scope: the executor MUST confirm no further consumer of the two changed scaffold strings exists beyond those measured in F-5. Known couplings deliberately NOT changed, with the reason each is safe: `tests/fixtures/conforming-orchestrator.md` is a HAND-WRITTEN fixture, not generated, and the suite passed with it untouched under the prototype; `tests/test_ipd_lifecycle_cli.py` uses `- [ ] E-01 TODO one observable action.` in hand-built plan text of its own and also passed untouched. If a NEW coupling appears, it must be fixed in this same change rather than left red, since a half-moved anchor is exactly the mid-flight breakage this item's lockstep framing exists to prevent.

## Required tests / validation

- The bare full suite (`python3 -m pytest`) must pass, with the `N passed` line pasted. Baseline in this lane at HEAD `10b22ef1`: `3246 passed, 2 skipped`.
- `aw check all --agent` must be no worse than its 33-finding baseline, with the count pasted.
- THREE PRE-EXISTING SLOW FAILURES ARE NOT THIS PLAN'S. Under `-m "slow or livecorpus"`, `tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw`, `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, and `tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory` fail identically WITH and WITHOUT the prototype patch. They are recorded here so the executor neither claims them nor tries to fix them, and they are covered by other pending plans (`4vfkl1`, `57dwkc`). The executor must re-confirm they fail on an unmodified tree before attributing them elsewhere.
- New coverage in `tests/test_ipd_authoring.py` must EXERCISE the code rather than inspect it: call `build_skeleton`, pass the result to `orchestrator_row_conformance`, and drive `ipd_lifecycle.begin` on real files. Per the execution contract, no test may read production source with `inspect`/`ast`/regex or assert on symbol censuses.

## Spec / documentation sync

- SPEC `r07vma` NEEDS NO AMENDMENT, and no `.spec.md` file is in `- Scope-Paths:`. This plan IMPLEMENTS what the spec already says: R1a defines the typed row, and OQ-01 names a conforming scaffold as its own proposed direction ("an author who starts from a conforming skeleton is shown the shape rather than told the rule"). Nothing in the spec's normative section changes, and OQ-01 stays open because its full render-from-one-source direction is out of scope (see Deferred).
- THE STALE COMMENT IN `ipd_lint.py` IS THE DOCUMENTATION THIS PLAN MUST FIX, and E-06 owns it. It currently tells a reader that the scaffold is non-conforming, that `pre-execution` is excluded because of a named test, and that "if a later plan makes the scaffold conforming, adding `pre-execution` back becomes a one-line change with this test as its proof". This plan IS that later plan; leaving the comment would leave the codebase asserting a state that no longer holds, and F-3/F-4 show the reader would be sent to a test that does not exist.
- The `ipd-spec` document carries no statement of the orchestrator row grammar (grep for `IPD-S407`, `typed child-tracking`, and `CONFIRM` in it returns nothing), so there is no prose copy of the grammar to keep in step. Recorded because it is the obvious place a reader would expect one, and its absence is what OQ-01 is about.

## Open questions

### OQ-01: Which placeholder child id6 should the conforming skeleton name?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE as "any valid id6 that collides with no tracked artifact, chosen to READ as a placeholder". `artifact_core.is_valid_id6` accepts any 6-char base36 token, so the constraint is weak and the real risk is a placeholder that looks like a real reference. Measured: across 1801 tracked `- Id:` values, none of `c0ch01`, `tmp1d6`, `000001` or `chi1d6` collides. The existing precedent is the template's own `tmp1d6` plan id, whose comment in `tests/test_ipd_templates.py` calls it "A fixed, valid id6 placeholder so the templates are deterministic AND lint conforming", so a fixed placeholder is established practice rather than a new idea. The prototype used `c0ch01`; the executor may pick another, and the only hard requirements are that the row and the table's `Id` cell name the SAME token (F-1) and that F-8's no-new-`aw check`-finding result be re-confirmed for whatever token is chosen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-bucket census (`conforming/total` over `applies=True` plans in `pending`, `executed`, `superseded`) and the pasted `aw check all --agent` finding count, both taken BEFORE any code change. The `pending` bucket must be all-conforming; if it is not, paste the offending plan's name and the recorded STOP decision instead.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted in-process output showing, for a freshly built orchestrator skeleton, `conforming=True`, an empty `table_reason`, and one row whose `(child_id6, status, depends_on)` all resolve; PLUS the same call on a `kind="child"` skeleton showing `applies=False`; PLUS evidence the child skeleton's bytes did not move (the `templates/ipd.md` parity test passing, and `git diff --stat` showing that file unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of `authoring_placeholders_resolved` returning False for a freshly scaffolded ORCHESTRATOR and False for a freshly scaffolded CHILD. If a marker was added to `_AUTHORING_PLACEHOLDERS`, paste it and state why it is an author-replaceable placeholder and not permanent structure.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted passing output for `tests/test_ipd_templates.py` (both parity tests and both `author`-checkpoint lint tests), plus `git diff --name-only` showing `orchestrator-ipd.md` changed and `ipd.md` NOT changed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted passing output for `python3 -m pytest tests/test_orchestrator_retirement.py`. PLUS a positive demonstration that the untyped fixture is still genuinely untyped: paste the refusal message from `test_an_orchestrator_with_untyped_checklist_rows_is_refused_at_retirement` (it must contain `not a typed child-tracking row`), so a green run cannot be a vacuous pass on a fixture that quietly became conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: THREE pasted artifacts. (1) `ipd_lifecycle.begin` on an orchestrator carrying an untyped row REFUSED with `IPD-S407` in the message. (2) The same call on a freshly scaffolded orchestrator NOT refused for `IPD-S407` (other unrelated readiness findings are acceptable and should be shown as such). (3) The rewritten comment block, showing it no longer references the removed test name or claims the scaffold is non-conforming. PLUS the bare full-suite `N passed` line and the post-change `aw check all --agent` count, compared against V-01's baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change with a hard internal ordering: the skeleton, its generated template, its coupled fixtures, and the checkpoint set must move together. Splitting it would leave the suite red between steps, because the byte-pinned template parity test and the retirement fixtures fail the instant the skeleton changes (F-5). It requires explicit human approval before execution; on approval the executor follows the repository execution contract, committing only the declared `- Scope-Paths:` through `aw commit`, and moves this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence.
