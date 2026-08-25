# IPD: Attention and query surfacing for research pending and stale state

- Date: 2026-08-24
- Kind: child
- Concern: `aw attention` maps research `intake -> ready` (attention_contract CLASS_MAPS['research'] = {intake: ready, active: active, reference: done, archive: parked}), so finished-but-unpromoted research shows as actionable work (the "ready" bucket held 11 research rows on 2026-08-24, 10 of them already done), and there is no first-class "what research must I still run?" query. Spec 5tapom Section 3.4 requires separating untriaged from actionable and surfacing pending research.
- Scope: Add `aw research pending` (or `find --unrun`) listing UNRUN prompts (consuming child 01's structural signal), and change `aw attention` so a finished/cited `intake` doc is NOT filed under `ready` (surface it as stale-state-to-promote) while a genuinely-unrun prompt remains actionable. Implements spec 5tapom Section 3.4. Depends on child 01 for BOTH the unrun derivation (E-01) and the RUN/cited-by-executed signal (child 01 E-02). It does NOT consume child 02's `outcome`/`consumed-by` fields (those are provenance, not the surfacing signal), so child 02 is NOT a hard dependency; ordering it after 02 is only for clean sequential Set execution, not a data dependency.
- Scope-Paths: grandfathered
- Status: approved
- Set: reslife
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: h40usm
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-303 fixed
- 2026-08-25 to-review (aw set): Authored complete and lint-conforming; ready for plan-review.

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 03 of the reslife Set (spec 5tapom).

## Goal

Make "what research do I still have to run?" a first-class, tool-answered question and stop `aw attention` from presenting finished research as actionable, so the attention view is trustworthy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Pending query

- [x] E-01 Add `aw research pending` (or `aw research find --unrun`) that lists exactly the UNRUN prompts using child 01's structural derivation (no corpus read), in both human and `--agent` output.
  - Depends on: none
  - Expected outcome: the query lists only unrun prompts on a fixture (run set excluded, bare prompt included); unit-tested in both output modes.
  - Execution note: commit 325874e; `research_index.run_pending` lists exactly `derive_unrun_prompts(entries)` (child 01's structural signal, no corpus read) as `id6<TAB>path<TAB>summary`, in both human and `--agent` output; CLI `pending` parser + dispatch in cli.py.
  - Execution state: performed

### Task group 2: Attention re-classification

- [x] E-02 Change `aw attention` so a research doc at `intake` that is RUN or cited-by-executed is NOT classed `ready` (surface it as a stale-state/drift item, per spec 5tapom OQ-01), while a genuinely-unrun `intake` prompt remains actionable. WIRING (the crux): `attention_contract.class_of(tree, status)` is status-only and MUST stay pure/total over `research_contract.STATUSES` - it cannot see the RUN/cited signal, which is manifest-level + cross-tree and is NOT in the per-file `_research_record(rel, path, text)` scanner signature today. So the derived signal must reach classification by ONE of: (a) thread `repo_root` + a precomputed unrun/cited set (from child 01's derivation) into `_record_for`/`_research_record`, or (b) a post-scan reclassification pass over the collected `items` keyed by research id6. Pick the lower-drift option; do NOT push the signal into `class_of`. `active` is a genuine live state (maps to ACTIVE, not READY) and is OUT of the "masquerades as ready" bug, so it is NOT reclassified here (only `intake` is); state this in the code comment.
  - Depends on: E-01
  - Expected outcome: on a fixture, a finished-but-unpromoted `intake` research doc no longer appears under `ready`; an unrun `intake` prompt does; an `active` doc keeps its ACTIVE class; `class_of` stays status-only and total; `aw attention` regression test asserts the split.
  - Execution note: commit 325874e; chose option (b), the post-scan pass `attention._reclassify_stale_research` keyed by research id6 (OQ-01 resolved to reuse PARKED, no new class, no second fail-closed drift - DECISION 05-h40usm-D1). It moves a RUN-prompt-set or cited-by-executed `intake` item READY -> PARKED (hidden from the default board), leaves a genuinely-unrun `intake` prompt READY, and does NOT touch `active` (code comment states this). `class_of` is unmodified (still status-only/total). Failure-isolated (any derivation error leaves items unchanged).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `attention_contract.class_of(tree, status)` is PURE and TOTAL and raises `UnknownNativeStatus` for an unmapped value; the research fragment currently maps `intake->ready`, `active->active`, `reference->done`, `archive->parked`. Any re-class must remain total over the four statuses. `aw attention` buckets are `active/ready/blocked/done/parked`.
- The attention scan (`attention.py scan(repo_root)`) loops per file and calls `_record_for(tree, rel, path, text)` -> `_research_record(rel, path, text)` WITHOUT `repo_root` or a shared manifest; the per-file record therefore cannot see set-membership (RUN) or cross-tree citations. The RUN/cited signal must be threaded in or applied in a post-pass (E-02). The `Item` NamedTuple carries `id`/`tree`/`native_status`/`path`, so a post-pass keyed by research id6 is viable.

## Findings

- The stale-`intake`-as-`ready` behavior is the visible symptom the maintainer flagged; child 01 provides the RUN/cited signal needed to distinguish "actionable unrun" from "stale finished" so attention can class them differently.

## Proposed changes (ordered, validatable)

1. `aw research pending`/`find --unrun` (E-01).
2. Attention re-classification using the RUN/cited signal (E-02).

## Deferred / out of scope (with reason)

- The RUN/unrun derivation and drift `--check` live in child 01; the provenance fields in child 02. This child consumes them.

## Scope check

- Over-scope: none. Only the pending query and the attention class split.
- Under-scope: none within this surface.

## Required tests / validation

- Unit test `aw research pending` (both output modes) on a fixture; `aw attention` regression test showing finished research is not `ready` and an unrun prompt is actionable. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Section 3.4 and resolves its OQ-01 (attention class choice). Update attention/research docs if the class labels change; otherwise N/A.

## Open questions

### OQ-01: New attention class vs reuse a drift signal for stale-state?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (spec 5tapom OQ-01); pick the lower-drift option (new class vs reuse) at execution, keeping class_of total. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted `aw research pending` (human + `--agent`) on a fixture listing only unrun prompts; unit test passing.
  - Observed evidence: `PendingQueryTests.test_pending_human_lists_only_unrun ... ok` and `test_pending_agent_lists_only_unrun ... ok` (on a fixture with a RUN set and one bare prompt, both modes list only the unrun `prmpt1`; the RUN-set prompt `prmpt2` and its report `rprt01` are excluded; --agent emits exactly one `id6<TAB>path<TAB>summary` line). Real-repo run: `aw research pending` lists the unrun prompts (e.g. `8it88r ... deriving-actor-identity...research-prompt.md`), exit 0, and `--agent` emits the same tab-separated shape. Full output in the run report (V-01, h40usm).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `aw attention` output on a fixture showing a finished-but-unpromoted `intake` doc is NOT under `ready`, an unrun `intake` prompt IS actionable, and an `active` doc keeps its ACTIVE class; a `class_of` test proving it stayed status-only and total over the four statuses (unchanged by this child).
  - Observed evidence: `StaleResearchReclassifyTests.test_run_set_intake_not_ready_unrun_stays_ready_active_untouched ... ok` (a RUN-set intake report `rprt01` -> `parked` (not ready); an unrun intake prompt `prmpt9` -> `ready`; an `active` doc `live01` -> `active`); `test_cited_by_executed_intake_not_ready ... ok` (a standalone intake cited by an executed plan -> `parked`); `test_class_of_unchanged_and_total ... ok` (`class_of('research', ...)` still `intake->ready, active->active, reference->done, archive->parked`). Real-repo `aw attention --format json`: research `ready` count dropped to 1 (the genuinely-unrun `8it88r`), 31 stale docs now `parked`; `aw attention --check` still exits 0 (no new drift emitted). Full output in the run report (V-02, h40usm).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (surface research pending/stale honestly) across the query and the attention class split that consume child 01/02 signals.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the surfacing modules (research_cmd.py / cli.py for the query, attention.py / attention_contract.py for the class split) and tests/. Do NOT re-implement the unrun signal (import child 01's) or the provenance fields (child 02). If more is needed, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
