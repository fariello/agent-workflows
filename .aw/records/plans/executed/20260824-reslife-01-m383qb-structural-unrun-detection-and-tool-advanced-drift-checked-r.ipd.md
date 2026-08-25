# IPD: Structural unrun detection and tool-advanced drift-checked research state

- Date: 2026-08-24
- Kind: child
- Concern: Research `status` is written once at creation (`aw research new` hard-codes `status="intake"`, research_cmd.py ~189/~244) and never advanced or validated, so `intake` conflates "untriaged/to-run" with "run-but-unpromoted" and "adopted-but-unpromoted" (11 docs on 2026-08-24; 10 already run+adopted). Spec 5tapom requires the parent B1/H2: identify unrun research WITHOUT trusting hand-typed status, and keep state genuinely tool-maintained.
- Scope: Add a structural UNRUN/RUN signal derived from manifest set-structure, and a drift rule in `aw research index --check` / `aw check` that flags stale hot state; plus a tool-assisted (human-confirmed) triage classifier reproducing the 2026-08-24 manual pass. Implements spec 5tapom Sections 3.1 and 3.2. Does NOT add a status value or change the vocabulary.
- Scope-Paths: grandfathered
- Status: executed
- Set: reslife
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: m383qb

## Workflow history
- 2026-08-25 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Structural unrun detection (derive_unrun_prompts/run_prompt_set_ids), stale-state-to-promote drift rule (RUN-set OR cited-by-executed reverse traversal) in research index --check / aw check, and the promote --suggest triage classifier; all E performed, all V pass with pasted test evidence
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-104 fixed
- 2026-08-25 to-review (aw set): Authored complete and lint-conforming; ready for plan-review.

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 01 of the reslife Set (spec 5tapom).

## Goal

Make "which research is not yet run?" a reliable, structural fact (not a hand-typed status) and make stale hot state fail-closed-visible in `--check`, so research state stops silently rotting the way it did before the 2026-08-24 triage.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Structural unrun detection

- [x] E-01 Add a pure `unrun`/`run` derivation over the research manifest: a SET is UNRUN when its `NN=00` member is `kind: research-prompt` and it has no `NN>=01` sibling member; RUN otherwise. Implement as a single reusable function (e.g. in `agent_workflows/research_contract.py` or `research_index.py`) consumed by later children; do NOT read the corpus (manifest/frontmatter only).
  - Depends on: none
  - Expected outcome: given the manifest, the function returns the exact set of unrun prompts; unit-tested on a fixture with one run set (excluded) and one bare prompt (included).
  - Execution state: performed
  - Execution note: commit 59fff46; `research_index.derive_unrun_prompts` + `unrun_set_ids` + `run_prompt_set_ids` (pure over `_scan_docs` DocEntry manifest, no corpus read). A prompt-set is UNRUN when its NN=00 research-prompt has no NN>=01 sibling; RUN when it has one; non-prompt sets are outside the taxonomy.

### Task group 2: Drift-checked state

- [x] E-02 Extend `aw research index --check` (and the `aw check` research path / `check_engine`) with a DRIFT rule: an `intake`/`active` doc is flagged as stale-state-to-promote (nonzero exit, in the existing drift-record shape) when EITHER trigger holds: (a) its SET is RUN (E-01's structural signal), OR (b) it is cited by an EXECUTED artifact. "Executed" means the citing plan sits under `executed/` (disposition, per `plans_index`), the citing spec is `implemented`, or the citing backlog item is `done`; a citation from a merely pending/draft artifact does NOT trigger the flag. Reuse the citation PRIMITIVES (the `cite_matcher` id-extractor + id-resolver + `iter_scan_files`), but note this is the REVERSE of `artifact_core.find_dangling_citations` (which finds a doc's OWN unresolved citations): here you scan executed artifacts and match citations that resolve TO the intake doc's id6. Build the reverse traversal on the shared primitives; do NOT bend `find_dangling_citations` and do NOT write a second id-matcher.
  - Depends on: E-01
  - Expected outcome: `--check` flags a stale `intake` doc under trigger (a) AND, independently, under trigger (b) with executed-disposition filtering (a pending-only citer does NOT flag); stays clean once the doc is promoted; regression test asserts each trigger independently and the pending-citer negative case.
  - Execution state: performed
  - Execution note: commit 59fff46; `research_index.cited_by_executed_ids` (reverse traversal reusing `artifact_core.iter_scan_files` + `R.iter_id6_citations`; executed = plan under `executed/` via `_plan_is_executed`, spec `Status: implemented` via `_spec_is_implemented`, backlog `done` via `_backlog_is_done`; does NOT bend `find_dangling_citations`). `check_drift` now appends `STALE_STATE_RULE` ("stale-state-to-promote") for a hot (intake/active) doc whose set is a RUN prompt-set (trigger a) or is in the cited-by-executed set (trigger b). Flows into `aw check research` automatically via `check_engine.check_content` -> `check_drift`.

### Task group 3: Tool-assisted triage classifier

- [x] E-03 Add a human-confirmed triage helper (a new verb or `aw research promote --suggest`, per spec 5tapom OQ-02) that CLASSIFIES stale docs (cited/run -> reference; uncited dead-end -> archive) and previews the moves for confirmation, reproducing the 2026-08-24 manual pass behavior. It must NOT mutate without confirmation (H2: distrust blind writes).
  - Depends on: E-01
  - Expected outcome: the helper previews a correct classification on a fixture matching the 2026-08-24 cohort; applying it promotes/archives as previewed; unit-tested.
  - Execution state: performed
  - Execution note: commit 59fff46; `aw research promote --suggest` (OQ-01 resolved to the flag, not a new verb - DECISION 03-m383qb-D1). `research_archive.suggest_triage` classifies stale hot docs: cited (executed or any citation) or in a RUN prompt-set -> reference; a RUN-set-but-uncited dead-end -> archive; genuinely-untriaged docs are left alone. `run_promote` previews unless `--apply` (H2). CLI `id` made optional (`nargs="?"`) so `--suggest` needs no id6.

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Research manifest is `INDEX.json` (all docs, tool-generated from frontmatter); `aw research index --check` is the CI/pre-commit drift gate. Statuses are the four-value `research_contract.STATUSES`. The `NN=00` `research-prompt` convention and set membership come from the filename grammar (spec 20260730 Section 4.5 / 4.2).
- The citation `--check` already resolves `\b<id6>\b` references via the shared `artifact_core` primitives (`cite_matcher`, `iter_scan_files`, id-resolver); reuse those primitives for the cited-by-executed signal rather than a second scanner. NOTE the direction: `artifact_core.find_dangling_citations` scans a doc for its OWN unresolved citations (forward); the drift signal here is the REVERSE (which executed artifacts cite THIS doc), so it is a new traversal over the same primitives, not a call to that function.
- Disposition is derivable without a new parser: a plan's `executed` state is its top-level directory (`plans_index` derives `disposition`), a spec's is `Status: implemented`, a backlog item's is `status: done`.

## Findings

- `research_cmd.py` writes `status="intake"` at creation and nothing advances it; `research_index.py` builds `INDEX.json` from frontmatter; `check_engine`/`releases.check_blocks_release` already demonstrate the "scan trees, resolve ids, emit Drift" pattern to mirror.

## Proposed changes (ordered, validatable)

1. Add the pure unrun/RUN derivation over the manifest (E-01).
2. Add the drift rule to `--check`/`aw check` reusing citation resolution (E-02).
3. Add the human-confirmed triage classifier (E-03).

## Deferred / out of scope (with reason)

- Setting `outcome`/`consumed-by` is child 02's job; this child only READS citations for the drift signal, it does not write provenance.
- The `aw research pending` query and attention re-classification are child 03.

## Scope check

- Over-scope: none. Only the unrun signal, the drift check, and the triage helper.
- Under-scope: none within this surface; provenance and surfacing are separate children by design.

## Required tests / validation

- Unit test the unrun derivation on a fixture manifest; test `--check` flags a stale `intake` doc under BOTH triggers (RUN set; cited-by-executed) independently, does NOT flag a doc cited only by a pending artifact, and is clean after promotion; test the triage classifier's preview/apply on a cohort fixture. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Sections 3.1/3.2; if the research README's "States" section should mention the drift check, update it. Otherwise N/A.

## Open questions

### OQ-01: Is the triage classifier a new verb or `promote --suggest`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (spec 5tapom OQ-02); pick the lower-drift option at execution; non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted unit-test output showing the unrun derivation returns exactly the bare prompt (run set excluded) on the fixture.
  - Observed evidence: `UnrunDerivationTests.test_derive_unrun_excludes_run_set_includes_bare_prompt ... ok` (asserts `derive_unrun_prompts -> ['prmpt1']`, `unrun_set_ids == {'unrunset'}`, `run_prompt_set_ids == {'runset'}` on a fixture with one RUN set and one bare prompt) and `test_prompt_set_taxonomy_ignores_non_prompt_sets ... ok`. Full output in run-20260825T035151Z-1236581/execution-report.md (V-01, m383qb).
  - Result: pass


- [x] V-02 validates E-02
  - Required evidence: pasted `aw research index --check` (or `aw check`) output flagging a stale `intake` doc under trigger (a) RUN-set AND, separately, under trigger (b) cited-by-EXECUTED; a pasted negative case showing a doc cited only by a PENDING artifact is NOT flagged; clean after promotion; regression test(s) named and passing, asserting each trigger and the pending-citer negative independently.
  - Observed evidence: `StaleStateDriftTests.test_trigger_a_run_set_flags_intake_and_clean_after_promote ... ok` (flags the RUN-set intake report, then clean after promoting it out of the hot band); `test_trigger_b_cited_by_executed_plan_flags_but_pending_does_not ... ok` (a pending-only citer does NOT flag; an executed-plan citer does); `test_cited_by_executed_ids_reverse_traversal ... ok` (implemented spec citer counts, draft spec citer does not). Real-repo demonstration: `aw research index --check` now emits `...awnamespace-04-2bodwq-...: stale-state-to-promote: active doc in RUN set 'awnamespace'; promote it` (exit 1) - one genuinely-stale doc surfaced (DECISION 03-m383qb-D3). Full output in the run report (V-02, m383qb).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted preview + apply of the triage classifier on a cohort fixture producing the correct reference/archive classification; test passing.
  - Observed evidence: `SuggestTriageTests.test_suggest_classifies_and_previews_without_mutation ... ok` (a RUN-set report cited by an executed plan -> reference; an uncited non-run intake doc left alone; no file moved during preview); `test_suggest_apply_promotes_as_previewed ... ok` (`--suggest --apply` moves the doc to reference/ and rewrites status); `test_suggest_archives_uncited_run_set_deadend ... ok` (a RUN-set uncited report -> archive). `aw research promote --help` shows `--suggest`. Full output in the run report (V-03, m383qb).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make research state reliable and unrun detectable) across a derivation, a check rule, and the triage helper that consumes it; all read-side/state-side, no provenance or surfacing.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the research-lifecycle modules needed (research_contract.py / research_index.py / research_cmd.py / check_engine.py) and tests/. Do NOT change attention surfacing (child 03) or provenance write paths (child 02). If a fix needs more, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass; never mark a box from narration.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
