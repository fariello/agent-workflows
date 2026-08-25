# IPD: Tooled and validated research outcome and consumed-by provenance

- Date: 2026-08-24
- Kind: child
- Concern: `outcome` is hard-coded `none-yet` at creation (research_cmd.py ~190/~245) with NO verb to ever set it, and `consumed-by: []` is written at creation but never populated or validated (1 of ~85 docs on 2026-08-24) and is not even carried in `INDEX.json`. So "which research output was authoritative/adopted?" and "what used this research?" are unanswerable, contradicting spec 5tapom Section 3.3 (and the parent's B2/provenance intent).
- Scope: Add a deliberate setter for `outcome` and `consumed-by`, carry `consumed-by` in `INDEX.json`, and validate both in `aw research index --check` / `aw check`. Implements spec 5tapom Section 3.3. Does NOT change the `outcome` vocabulary or the `status` model.
- Scope-Paths: grandfathered
- Status: approved
- Set: reslife
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: xjrdjp
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-203 fixed
- 2026-08-25 to-review (aw set): Authored complete and lint-conforming; ready for plan-review.

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 02 of the reslife Set (spec 5tapom).

## Goal

Make research provenance first-class and honest: a tool sets `outcome`/`consumed-by`, the manifest carries them, and `--check` enforces that an adopted doc names what adopted it and that every `consumed-by` reference resolves.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The setter verb

- [x] E-01 Add `aw research set-outcome <id6> --to <adopted|informational|rejected|none-yet> [--consumed-by <id6[,id6...]>|-]` that sets `outcome` and appends/replaces/clears (`-` clears) `consumed-by` in an EXISTING doc's frontmatter via a new in-place field-updater primitive, dry-run-by-default with `--apply` and the same atomic write-to-temp-rename as the creators. (See conventions: no such updater exists today, so it is introduced here and MUST round-trip - other fields, order, `[a, b]` rendering, and body preserved.)
  - Depends on: none
  - Expected outcome: the verb sets `outcome` and appends/replaces/clears `consumed-by` while leaving every other frontmatter field and the body byte-identical; unit-tested for set, append, replace, clear, AND a round-trip test asserting no other field or the body changed.
  - Execution state: performed
  - Execution note: commit de7e1c1; `research_cmd.update_frontmatter_fields` (rewrites only named fields in the FIRST frontmatter block, preserving all other fields + body byte-for-byte), `plan_set_outcome` (validates outcome vocab; REPLACE list; `-` clears), `run_set_outcome` (preview unless `--apply`, atomic write, refreshes INDEX). CLI `set-outcome` parser + dispatch in cli.py.

### Task group 2: Index carries provenance

- [x] E-02 Carry `consumed-by` in `INDEX.json` (today omitted) so provenance is queryable without reading the corpus; keep `INDEX.md`'s bounded hot-glance unchanged.
  - Depends on: E-01
  - Expected outcome: `INDEX.json` docs include `consumed-by`; `aw research index --check` stays clean; a test asserts the field is present.
  - Execution note: commit de7e1c1; added `consumed_by: List[str]` to `DocEntry` (populated from frontmatter in `_scan_docs`), so `build_index_json` (`_asdict()`) carries it. Regenerated the tracked `.aw/records/research/INDEX.json` via `aw research index` so all 85 docs carry the key and the stale-index finding clears (DECISION 04-xjrdjp-D1); INDEX.md hot-glance unchanged.
  - Execution state: performed

### Task group 3: Validation

- [x] E-03 Extend `aw research index --check` / `aw check`: a `consumed-by` entry that does not resolve to an existing plan/spec/backlog id6 is flagged (in the existing Drift-record shape), and `outcome: adopted` with an empty `consumed-by` is flagged (an adopted doc must name its consumer). NOTE the resolution target: `consumed-by` points at PLAN/SPEC/BACKLOG id6s, so the resolvable-id set must be assembled from those trees (plan ids via `plans_index`, spec ids, backlog ids) - it is NOT `research_refs`'s research-only resolver and NOT `check_blocks_release`'s release-only resolver. Reuse the id-resolution + Drift PATTERN, assembling the cross-tree current-id set; do not reuse a single-tree resolver as if it covered all three.
  - Depends on: E-01
  - Expected outcome: `--check` flags a `consumed-by` id6 that resolves to no plan/spec/backlog artifact, and an `adopted`-with-empty-`consumed-by`; clean when both satisfied; regression tests for each.
  - Execution note: commit de7e1c1; `research_index.resolvable_consumer_ids` assembles the cross-tree id set from `- Id:` metadata across the plan+spec+backlog trees (NOT the research-only or release-only resolver). `check_drift` now appends `DANGLING_CONSUMED_RULE` for a `consumed-by` id6 with no matching plan/spec/backlog artifact and `ADOPTED_NO_CONSUMER_RULE` for `outcome: adopted` with empty `consumed-by`. Flows into `aw check research` via `check_engine.check_content` -> `check_drift`.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `outcome` vocabulary is `adopted|informational|rejected|none-yet` (research_contract). `consumed-by` is a list of plan/spec/backlog id6s the doc informed (spec 20260730 Section 5.4), rendered as an `[a, b]` flow list in frontmatter (`build_frontmatter` line ~84). `releases.check_blocks_release`/citation `--check` show the id-resolution + Drift PATTERN to reuse - but each resolves ONE tree (release records / research ids respectively); the `consumed-by` check needs a resolvable-id set spanning plan+spec+backlog, assembled from those trees, not any single existing resolver.
- There is no in-place research frontmatter field-updater today; creation-only `build_frontmatter` renders all 11 fields. E-01 introduces the updater; it must preserve the other fields + body (round-trip).

## Findings

- No `--outcome`/`set-outcome` exists on `aw research`; `outcome`/`consumed-by` are creation-only. `INDEX.json` doc schema lacks `consumed-by` (verified 2026-08-24). The 2026-08-24 triage hand-set these fields, which this child makes tool-owned.

## Proposed changes (ordered, validatable)

1. `aw research set-outcome` with a shared write primitive (E-01).
2. `consumed-by` in `INDEX.json` (E-02).
3. `--check`/`aw check` validation of dangling refs and adopted-without-consumer (E-03).

## Deferred / out of scope (with reason)

- The structural unrun/RUN signal and stale-state drift are child 01. Attention/pending surfacing is child 03.

## Scope check

- Over-scope: none. Only the provenance fields, their index carriage, and their validation.
- Under-scope: none within this surface.

## Required tests / validation

- Unit test set/append/replace/clear via the verb plus a frontmatter round-trip (other fields + body unchanged); test `INDEX.json` carries `consumed-by`; test `--check` flags a `consumed-by` id6 unresolved across plan+spec+backlog and an adopted-without-consumer, clean otherwise. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Section 3.3. Update the research README's frontmatter example if `consumed-by` guidance changes; otherwise N/A.

## Open questions

### OQ-01: Should `set-outcome` also accept a status change, or stay orthogonal to `promote`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED; keep `set-outcome` orthogonal to `promote` unless execution shows a strong reason to combine. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `aw research set-outcome` setting `outcome` and `--consumed-by`, appending/replacing, and clearing with `-`; a round-trip test showing the other 10 frontmatter fields and the doc body are byte-identical after a set; unit tests passing.
  - Observed evidence: `SetOutcomeTests.test_updater_round_trips_only_named_fields ... ok` (asserts every non-outcome/consumed-by field AND the body are byte-identical after a set, including a decoy `outcome:` body line untouched); `test_set_append_replace_clear ... ok` (set -> [pln001], replace -> [aaaaaa,bbbbbb], clear via '-' -> []); `test_invalid_outcome_rejected ... ok`; `test_run_set_outcome_apply_writes ... ok`. Manual preview on the real repo: `aw research set-outcome 2bodwq --to adopted --consumed-by pln001,spc002` -> `--- would update ...: outcome=adopted, consumed-by=[pln001, spc002] ---`, and `--consumed-by -` -> `consumed-by=[] (cleared)` (preview only, no doc mutated). Full output in the run report (V-01, xjrdjp).
  - Result: pass


- [x] V-02 validates E-02
  - Required evidence: pasted `INDEX.json` fragment showing `consumed-by` on a doc; `aw research index --check` clean; test passing.
  - Observed evidence: `ConsumedByIndexTests.test_docentry_and_json_carry_consumed_by ... ok` (DocEntry.consumed_by populated; `build_index_json` emits `"consumed_by"`). Regenerated `.aw/records/research/INDEX.json` carries `consumed_by` on all 85 docs (`grep -c consumed_by INDEX.json` = 85). `aw research index --check` no longer reports any `stale-index` finding (`grep -c stale-index` = 0); the remaining findings are the intended new provenance/stale-state surfacings (DECISION 04-xjrdjp-D2), not an INDEX drift. INDEX.md hot-glance unchanged. Full output in the run report (V-02, xjrdjp).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `--check` output flagging a dangling `consumed-by` and an `adopted`-without-consumer, and clean once fixed; regression tests passing.
  - Observed evidence: `ConsumedByValidationTests.test_dangling_consumed_by_flagged ... ok` (a `consumed-by: [nofind]` is flagged `dangling-consumed-by`, and clears once a real plan with that id exists); `test_adopted_without_consumer_flagged ... ok` (`outcome: adopted` with empty `consumed-by` flagged, clears once a resolving consumer is added); `test_resolvable_consumer_ids_spans_trees ... ok` (plan+spec+backlog ids all resolve). Real-repo demonstration: `aw research index --check` emits multiple `...: adopted-without-consumer: outcome: adopted requires a non-empty consumed-by` findings (e.g. awdeliv/hostprobe/chkplace sets) - the real provenance gap surfaced (DECISION 04-xjrdjp-D2). Full output in the run report (V-03, xjrdjp).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make research provenance tooled and validated) across the setter, its index carriage, and its checks.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the research provenance surfaces (research_cmd.py / research_index.py / research_contract.py / check_engine.py / cli.py for the verb) and tests/. Do NOT change the unrun/drift logic (child 01) or attention (child 03). If more is needed, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
