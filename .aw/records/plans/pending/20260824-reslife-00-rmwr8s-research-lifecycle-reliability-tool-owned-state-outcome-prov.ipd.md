# IPD: Research lifecycle reliability: tool-owned state, outcome/provenance, and unrun surfacing

- Date: 2026-08-24
- Kind: orchestrator
- Concern: The research subsystem's reliability half is unimplemented. Per spec 5tapom (follow-on to the implemented research-org spec), `aw research new` writes `status: intake`, `outcome: none-yet`, `consumed-by: []` only at CREATION and nothing ever advances/sets/validates them, so `intake` became a permanent default (11 docs stuck there on 2026-08-24, 10 already run+adopted), `aw attention` maps `intake -> ready` (finished research masquerades as actionable), "which research must I still run?" is unanswerable from the tool, and provenance (`consumed-by`) is populated on ~1 of 85 docs and never validated. This violates the parent spec's B1/B2/H2.
- Scope: Achieve research-lifecycle reliability across three surfaces (state advancement + structural unrun detection; tooled+validated outcome/consumed-by provenance; attention/query surfacing), split into three dependency-ordered child IPDs so each is small and independently verifiable. Implements spec 5tapom. No change to the filename grammar, the four `status` values, the `outcome` vocabulary, or the shard layout.
- Scope-Paths: grandfathered
- Status: approved
- Set: reslife
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rmwr8s
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed
- 2026-08-25 to-review (aw set): Authored complete and lint-conforming; ready for plan-review.

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; orchestrator for spec 5tapom (research lifecycle reliability), split into 3 dependency-ordered children. Release-blocker for 2.0.0 (f33nrj) intent is anchored on spec 5tapom and the f33nrj record: these plans CANNOT carry `- Blocks-Release:` until the vwios6ipd set lands (IPD-M103 rejects the field on plans today). Re-mark via `aw ipd set --blocks-release next` after vwios6ipd ships the setter.

## Goal

Make research `status`, `outcome`, and `consumed-by` genuinely tool-owned and verifiable so the parent research-org spec's reliability requirements (B1 identify unrun research without trusting hand-typed status; B2 compartmentalize by outcome; H2 state is tool-maintained not just tool-created) actually hold, and "what research do I still have to run?" and "what used this research?" become first-class, tool-answered questions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator does not itself edit code; each `E-*` below is the delivery of one child IPD. Execute the children in Order; mark an `E-*` complete only after that child has been fully executed (all its own V items verified and it has moved to `executed/`).

### Task group 1: State advancement and unrun detection (foundation)

- [x] E-01 Deliver child IPD Order 01 (m383qb): structural UNRUN detection (a set whose `NN=00` is a `research-prompt` with no `NN>=01` siblings is unrun, derived from the manifest) and tool-advanced, drift-checked state - `aw research index --check`/`aw check` flag an `intake`/`active` doc whose set is RUN or is cited by an executed artifact, plus a tool-assisted reviewed triage classifier (reproducing the 2026-08-24 manual pass).
  - Depends on: none
  - Expected outcome: all three of child 01's deliverables land and are verified: (a) unrun detection is computed from set structure; (b) `--check` flags stale state; (c) the tool-assisted triage classifier previews the 2026-08-24 cohort classification and applies only on confirmation; a regression test asserts each.
  - Execution state: performed

### Task group 2: Outcome and provenance tooling

- [x] E-02 Deliver child IPD Order 02 (xjrdjp): make `outcome` and `consumed-by` tooled and validated - `aw research set-outcome <id6> --to <...> [--consumed-by <id6,...>]`, carry `consumed-by` in `INDEX.json`, and validate in `aw research index --check`/`aw check` (dangling `consumed-by` flagged; `outcome: adopted` requires a non-empty `consumed-by`).
  - Depends on: E-01
  - Expected outcome: `aw research set-outcome` writes/updates/clears the fields; `INDEX.json` carries `consumed-by`; `--check` flags dangling refs and adopted-without-consumer; regression tests assert each.
  - Execution state: performed

### Task group 3: Attention and query surfacing

- [x] E-03 Deliver child IPD Order 03 (h40usm): add `aw research pending` (or `find --unrun`) listing unrun prompts, and change `aw attention` so plain `intake` that is finished/cited no longer files under `ready` (surface it as stale-state-to-promote), while genuinely-unrun research remains actionable.
  - Depends on: E-01, E-02
  - Expected outcome: `aw research pending` lists exactly the unrun prompts; `aw attention` no longer shows finished-but-unpromoted research as `ready`; regression tests assert both.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260824-reslife-01-m383qb-structural-unrun-detection-and-tool-advanced-drift-checked-r.ipd.md | Structural unrun detection + drift-checked state + triage classifier | none |
| 02 | 20260824-reslife-02-xjrdjp-tooled-and-validated-research-outcome-and-consumed-by-proven.ipd.md | `aw research set-outcome`/`consumed-by`; index + `--check`/`aw check` validation | 01 |
| 03 | 20260824-reslife-03-h40usm-attention-and-query-surfacing-for-research-pending-and-stale.ipd.md | `aw research pending`; attention stops treating stale `intake` as `ready` | 01, 02 |

Dependency rationale: 01 establishes the structural unrun/RUN signal and the drift rule the others build on. 02 needs 01 so validation can reason about state and the RUN signal. 03 needs 01 (unrun signal) and 02 (the outcome/consumed-by fields it surfaces).

## Completion criteria (the whole Set is done only when)

- `aw research pending`/`find --unrun` lists exactly the UNRUN prompts (structural), proven on a fixture where a set with outputs is excluded and a bare `NN=00` prompt is included.
- `aw research index --check`/`aw check` flag: an `intake`/`active` doc whose set is RUN or cited by an executed artifact; a dangling `consumed-by`; and `outcome: adopted` with empty `consumed-by`.
- `aw research set-outcome` writes/updates/clears `outcome` and `consumed-by`; `INDEX.json` carries `consumed-by`.
- The tool-assisted, human-confirmed triage classifier (spec 5tapom Section 3.2 / child 01 E-03) reproduces the 2026-08-24 manual pass: it PREVIEWS a cited/run -> reference, uncited-dead-end -> archive classification and mutates only on confirmation.
- `aw attention` no longer files finished-but-unpromoted research under `ready`.
- Spec 5tapom's acceptance criteria (Section 5) are met by tests, not prose; whole suite green.
- Each child IPD's own validation passed with pasted evidence and each child moved to `executed/`.

## Cross-IPD validation

- After all three children execute, hand-verify end-to-end against the 2026-08-24 reference triage: a fixture research set that is run+cited must be flagged stale by `--check`, promotable, and NOT appear in `aw research pending`; a bare unrun prompt must appear in `aw research pending` and as actionable in `aw attention`.
- Confirm no duplicated logic: unrun/RUN detection has ONE implementation consumed by `pending`, `--check`, and attention; the outcome/consumed-by write goes through one shared setter primitive.

## Deferred / out of scope (with reason)

- Actually re-marking the reslife IPDs with `- Blocks-Release: next` is out of scope until the vwios6ipd set lands (a plan carrying the field fails `aw ipd lint` IPD-M103 "unknown field" today, since `Blocks-Release` is not in the IPD schema's recognized-fields set). Interim release-blocker intent lives on spec 5tapom and the f33nrj release record. Re-mark via the tooled setter that vwios6ipd ships (child efnn74; `aw ipd set-blocks-release` per its title) once that set is `executed`; use whatever verb/flag vwios6 actually delivers, do not assume the exact spelling here.
- No change to the filename grammar, the four `status` values, the `outcome` vocabulary, `INDEX.md`'s bounded hot-glance, or the shard layout (all shipped and working).
- The one genuinely-unrun prompt today (`actorenv/8it88r`) is real pending research to run, not a lifecycle bug; running it is out of scope for this tooling Set.

## Scope check

- Over-scope: none. Confined to research-lifecycle reliability surfaces (state/unrun, outcome/provenance, surfacing) named in spec 5tapom.
- Under-scope: none. Covers all three DoD surfaces plus the drift check that keeps state honest going forward.

## Required tests / validation

- Each child ships its own tests (unrun detection + drift `--check`; set-outcome/consumed-by persist + validation; `pending` + attention surfacing). This orchestrator is validated by the children passing and by the cross-IPD reference-triage check above.
- Whole-suite `python3 -m pytest tests/` green after the last child.

## Open questions

### OQ-01: Does `aw attention` gain a distinct "stale-state-to-promote" class, or reuse an existing drift signal?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to child 03 (mirrors spec 5tapom OQ-01); child 03 owns the attention_contract change and picks the lower-drift option at execution time. Non-blocking for this orchestrator.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: child 01 moved to `executed/` with ALL of its own V-items (its V-01/V-02/V-03) verified; pasted test output showing (a) structural unrun detection (run set excluded, bare prompt included), (b) `--check` flagging a stale `intake` doc and clean after promotion, and (c) the triage classifier previewing then applying the 2026-08-24 cohort classification; the regression tests named and shown passing.
  - Observed evidence: child `20260824-reslife-01-m383qb-structural-unrun-detection-and-tool-advanced-drift-checked-r.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01/V-02/V-03 all `Result: pass`; product commit 59fff46 (`feat(research): structural unrun detection + stale-state drift check + triage classifier (m383qb)`), evidence 124feba, finalize 8f0c5da. (a) `UnrunDerivationTests.test_derive_unrun_excludes_run_set_includes_bare_prompt ... ok` (asserts `derive_unrun_prompts -> ['prmpt1']`, `unrun_set_ids == {'unrunset'}`, `run_prompt_set_ids == {'runset'}`); (b) `StaleStateDriftTests.test_trigger_a_run_set_flags_intake_and_clean_after_promote ... ok` and `test_trigger_b_cited_by_executed_plan_flags_but_pending_does_not ... ok`; (c) `SuggestTriageTests.test_suggest_classifies_and_previews_without_mutation ... ok`, `test_suggest_apply_promotes_as_previewed ... ok`, `test_suggest_archives_uncited_run_set_deadend ... ok`. Re-verified live at HEAD 106aef4: `aw research index --check` emits `20260813-awnamespace-04-2bodwq-...: stale-state-to-promote: active doc in RUN set 'awnamespace'; promote it` (the one genuinely-stale doc). Single-source confirmed: `derive_unrun_prompts`/`unrun_set_ids`/`run_prompt_set_ids` defined once in `agent_workflows/research_index.py:238-275`, consumed by `attention.py`, `research_archive.py`, and the `--check` path.
  - Result: pass


- [x] V-02 validates E-02
  - Required evidence: child 02 moved to `executed/` with ALL of its own V-items verified; pasted output of `aw research set-outcome` writing `outcome`+`consumed-by`; `INDEX.json` showing `consumed-by`; `--check` flagging a dangling `consumed-by` and an `adopted`-without-consumer; regression tests passing.
  - Observed evidence: child `20260824-reslife-02-xjrdjp-tooled-and-validated-research-outcome-and-consumed-by-proven.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01/V-02/V-03 all `Result: pass`; product commit de7e1c1 (`feat(research): tooled+validated outcome/consumed-by provenance (xjrdjp)`), evidence e20cd62, finalize 0970c8f. Re-verified live at HEAD 106aef4: `aw research set-outcome 2bodwq --to adopted --consumed-by pln001,spc002` -> `--- would update 20260813-awnamespace-04-2bodwq-...: outcome=adopted, consumed-by=[pln001, spc002] ---`, and `--consumed-by -` -> `consumed-by=[] (cleared)` (dry-run default, no doc mutated). `.aw/records/research/INDEX.json` carries `consumed_by` on all 85 docs (`grep -c consumed_by INDEX.json` = 85). `aw research index --check` emits `adopted-without-consumer` findings (e.g. awdeliv/hostprobe/chkplace sets) - the real provenance gap surfaced (child DECISION 04-xjrdjp-D2). Tests: `SetOutcomeTests.test_updater_round_trips_only_named_fields ... ok`, `test_set_append_replace_clear ... ok`, `test_invalid_outcome_rejected ... ok`; `ConsumedByIndexTests.test_docentry_and_json_carry_consumed_by ... ok`; `ConsumedByValidationTests.test_dangling_consumed_by_flagged ... ok`, `test_adopted_without_consumer_flagged ... ok`, `test_resolvable_consumer_ids_spans_trees ... ok`. Single shared setter primitive: `update_frontmatter_fields` in `agent_workflows/research_cmd.py:383`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: child 03 moved to `executed/` with ALL of its own V-items verified; pasted `aw research pending` listing only unrun prompts; pasted `aw attention` output showing a finished-but-unpromoted research doc is NOT under `ready`; regression tests passing.
  - Observed evidence: child `20260824-reslife-03-h40usm-attention-and-query-surfacing-for-research-pending-and-stale.ipd.md` is `Status: executed` under `.aw/records/plans/executed/` with its own V-01/V-02 all `Result: pass`; product commit 325874e (`feat(research): aw research pending + attention stale-intake reclassification (h40usm)`), evidence ba74be4, finalize 66a822b. Re-verified live at HEAD 106aef4: `aw research pending` lists only structurally-unrun bare prompts (`8it88r` actorenv, plus migrated bare prompts `jd8qhs`, `g5vhpz`, `2838rp`); the `--agent` form emits the same `id6<TAB>path<TAB>summary` shape. `aw attention --format json` research breakdown: `attention_class` = {active:1, ready:1, done:52, parked:31}; the single `ready` research item is `8it88r` (native_status `intake`, the genuinely-unrun actorenv prompt), and 31 finished-but-unpromoted docs are `parked` (NOT `ready`); `aw attention` overall `valid: true, violations: 0`. Tests: `PendingQueryTests.test_pending_human_lists_only_unrun ... ok`, `test_pending_agent_lists_only_unrun ... ok`; `StaleResearchReclassifyTests.test_run_set_intake_not_ready_unrun_stays_ready_active_untouched ... ok`, `test_cited_by_executed_intake_not_ready ... ok`, `test_class_of_unchanged_and_total ... ok`.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (research-lifecycle reliability) delivered as three dependency-ordered children, each a small single-surface change; splitting maximizes clean, independently-verifiable execution.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred to child 03. No blocking open question remains.
2. Scope fence: this orchestrator authors no code; execute children in Order (01, then 02, then 03), each under its own scope fence. Do NOT begin a child before its declared dependencies are `executed`.
2a. Per-child approval gate: the three children are authored `Status: draft`. Each child MUST independently reach `Status: approved` (its own `/plan-review` completed and human sign-off recorded) BEFORE it is executed. Executing this orchestrator does NOT confer approval on the children; an executor MUST NOT run a child still `draft`/`to-review`/`reviewed`.
3. Honesty rule (hard MUST): when reporting a child complete, rely on that child's pasted validation evidence (real runner output); never mark an `E-*`/`V-*` here from narration.
4. Commit ONLY each child's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Release-blocker follow-through: once the vwios6ipd set is `executed`, mark this orchestrator and its children with `- Blocks-Release: next` via the tooled setter vwios6ipd ships (child efnn74; use whatever verb/flag it actually delivers, do NOT hand-edit the field, which fails IPD-M103 until the schema recognizes it), retiring the interim intent held on spec 5tapom / the f33nrj record.
6. Lifecycle move: this orchestrator moves to `executed/` only after all three children are `executed`, every V item here is verified with pasted evidence, the `## Workflow history` line is appended, and `Status: executed` is set, via the gated `aw ipd begin`/`aw ipd finalize` lifecycle.
