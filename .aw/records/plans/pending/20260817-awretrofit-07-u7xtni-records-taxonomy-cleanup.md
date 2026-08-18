# IPD: Clean up .aw/records/ taxonomy: run-artifacts home, dedup prompts, flatten docs (pre-release, legacy->final only)

- Date: 2026-08-17
- Kind: child
- Concern: Spec 20260817-2124-01 (RELEASE BLOCKER): the `.aw/records/` taxonomy has (A) workflow run-artifacts (assess-*/verify/verify-execution/release-review/advise-*) at the records ROOT, (B) two identically-named `prompts` dirs (staging vs library), (C) deeper-than-wanted `docs/` nesting. Backlog lavkg7 gates the release on this.
- Scope: Implement the spec's FINAL `.aw/records/` taxonomy. PRE-RELEASE framing (spec Section 0): the `.aw/` layout has NOT shipped, so this changes the legacy `.agents/` -> FINAL migration DESTINATIONS in place and brings this dev repo onto the final layout by a one-time git mv - it does NOT build an intermediate `.aw/records/docs/` -> final migration hop. Task groups A (run-artifacts home), B (dedup prompts), C (flatten docs). OUT: the four physical roots, records-backend choice, changing what any workflow does.
- Status: draft
- Set: awretrofit
- Order: 7
- Highest E allocated: 08
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: u7xtni

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created from spec 20260817-2124-01 (Set awretrofit Order 07). DRAFT: blocked on the spec's OQ-A1/OQ-C1 being resolved (approved) before the E-items are final.

## Goal

Land the FINAL `.aw/records/` taxonomy from spec 20260817-2124-01 so the first release carrying the
`.aw/` layout ships a clean, self-consistent record tree: run-artifacts in one obvious home, no
duplicate `prompts` name, and the durable doc types at their agreed final paths - implemented as a
legacy->final destination change plus a one-time dev-repo `git mv`, with NO intermediate migration hop.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

DRAFT NOTE: The exact target names depend on spec OQ-A1 (run-artifacts home), OQ-B1 (library name),
OQ-C1/C2 (flatten + misc). The E-items below assume the spec's RECOMMENDED defaults and MUST be
finalized when the spec is approved (see this IPD's Open questions, which mirror the spec's). `aw ipd
sync` will assign V-* items after the E-set is finalized in review.

### Task group A: run-artifacts get one obvious home (spec G1, OQ-A1)

- [ ] E-01 Resolve the run-artifacts double-home. Per OQ-A1 recommended default (option 1): the SINGLE home is the top-level `workflow-artifacts/<workflow>/<RUN_ID>/` (what the shipped workflow bodies already write). REMOVE the `.aw/records/{assess-*,verify,verify-execution,release-review,advise-*}` home: delete its `.gitignore` lines (:68-72), remove any migration step that relocates old `workflow-artifacts/` INTO `.aw/records/`, and confirm no code writes run records under `.aw/records/`. If OQ-A1 resolves to option 2 instead (`.aw/records/runs/`), invert: point the workflow bodies + gitignore + migration there. (Finalize on OQ-A1.)
  - Depends on: none
  - Expected outcome: exactly ONE documented home for run-artifacts; `.aw/records/` root has no `<RUN_ID>` dirs; workflow bodies, `.gitignore`, and migration agree.
  - Execution state: pending

- [ ] E-02 Bring THIS dev repo onto the decision: move the existing untracked `.aw/records/{assess-*,verify,verify-execution,release-review,advise-*}` run dirs to the chosen home (one-time; they are untracked so a plain `mv`), or remove them if they duplicate `workflow-artifacts/` content.
  - Depends on: E-01
  - Expected outcome: this repo's `.aw/records/` root contains only durable record types.
  - Execution state: pending

### Task group B: dedup the `prompts` name (spec G2, OQ-B1)

- [ ] E-03 Rename the prompt LIBRARY `.aw/records/docs/prompts/` to its agreed distinct name (OQ-B1 default `prompt-library/`, final path per Task group C), leaving the lifecycle STAGING `.aw/records/prompts/` unchanged. Update `resolve_record_path`/read-paths + any consumer + the shipped docs that reference the library path.
  - Depends on: E-04
  - Expected outcome: no two record subtrees share the leaf name `prompts`; the library resolves at its new path; staging `prompts/` unchanged.
  - Execution state: pending

### Task group C: flatten docs/ (spec G3, OQ-C1/C2)

- [ ] E-04 Update the canonical layout + resolvers: `resolve_record_path`/`resolve_record_read_paths` (record_producers.py) + `project_schema`/`project_context` targets so the durable doc types resolve at the FINAL flat paths `.aw/records/{specs,research,walkthroughs,roadmaps}` (per OQ-C1) instead of `.aw/records/docs/{...}`. Add `misc/` only if OQ-C2 says so.
  - Depends on: none
  - Expected outcome: every resolver + consumer verb (`aw specs`, `aw research`, `aw plans`, `aw attention`, `aw backlog`) resolves the flat final paths.
  - Execution state: pending

- [ ] E-05 Update the legacy->FINAL migration DESTINATIONS in `layout_migration.py` (and its mapping tables) so legacy `.agents/docs/{research,specs,walkthroughs,roadmaps}` and `.agents/docs/prompts` map DIRECTLY to the final flat paths + the renamed library - NO intermediate `.aw/records/docs/` hop (spec Section 0). Update the awphysical migration tests' expected destinations.
  - Depends on: E-04, E-03
  - Expected outcome: `aw migrate-layout` maps legacy `.agents/*` directly to the final layout; migration tests assert the final destinations.
  - Execution state: pending

### Task group D: reconcile shipped docs + bring this dev repo onto the final tree

- [ ] E-06 Update every SHIPPED doc/AGENTS.md-generator/index.md/template path that Order 02 set to the INTERMEDIATE `.aw/records/docs/{...}` so it now names the FINAL flat paths (e.g. the engine.py AGENTS.md generator aw-branch `.aw/records/docs/research` -> `.aw/records/research`), and regenerate AGENTS.md. Extend the Order-02 drift-guard test accordingly.
  - Depends on: E-04
  - Expected outcome: shipped bundle + AGENTS.md reference the final flat paths; drift guard updated.
  - Execution state: pending

- [ ] E-07 One-time `git mv` of THIS dev repo's tracked doc trees `.aw/records/docs/{research,specs,walkthroughs,roadmaps}` -> `.aw/records/{...}` and the library rename, plus the run-artifacts move (E-02), updating any tracked references + regenerating INDEX/STATUS manifests.
  - Depends on: E-04, E-05, E-06, E-02, E-03
  - Expected outcome: this repo is physically on the final layout.
  - Execution state: pending

### Task group E: verification + unblock the release gate

- [ ] E-08 Full validation: serial suite green (>= current baseline), `aw attention --check` / `aw plans index --check` / `aw research index --check` / `aw specs check` / `aw backlog check` / `aw sanitize --agent` clean, wheel rebuild ships the final-layout bundle, and a legacy-`.agents/` fixture migrates DIRECTLY to the final layout (no docs/ hop). Then advance spec 20260817-2124-01 to implemented and move blocked backlog lavkg7 to done (unblocking the release gate).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: all checks green; spec implemented; lavkg7 done; the release blocker is cleared.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Spec Section 0 is load-bearing: the `.aw/` layout has NOT shipped, so only legacy->final migration is
  needed; the intermediate `.aw/records/docs/` shape is dev-only and fixed by a one-time `git mv`.
- The canonical resolver is `record_producers.resolve_record_path`; consumers already route through it
  (post-Order-01). Order 02 set the shipped docs to the INTERMEDIATE `.aw/records/docs/{...}` - E-06
  updates those to the final flat paths.
- Run-artifacts are gitignored (`.gitignore:63-72`); the shipped workflow bodies write `workflow-artifacts/`.
- `aw plans mv` clobbers `- Order:` to 0 and `aw ipd scaffold` omits the id6 (backlog vf03z3); this IPD
  was renamed + Order-restored by hand as a result.

## Findings

Per spec 20260817-2124-01 problems A/B/C (facts observed on disk in release-review run 20260817-153418).
Summarized in that spec's Sections 2-3; not duplicated here.

## Proposed changes (ordered, validatable)

A (E-01/E-02) run-artifacts single home; B (E-03) dedup prompts; C (E-04/E-05) flatten docs + migration
destinations; D (E-06/E-07) shipped-docs reconcile + dev-repo git mv; E (E-08) verify + unblock.

## Deferred / out of scope (with reason)

- Intermediate `.aw/records/docs/` -> final migration hop: NOT built (spec Section 0; pre-release).
- The four physical roots, records-backend choice, workflow behavior: unchanged.

## Scope check

- Over-scope: none - each E-item maps to a spec goal; `misc/` added only if OQ-C2 warrants (else omitted, KISS).
- Under-scope: none - A+B+C plus the shipped-docs reconcile (so nothing regresses to the intermediate shape)
  and the migration-destination update are all covered.

## Required tests / validation

- Full serial suite green; all `aw ... --check`/`sanitize` clean; wheel ships the final-layout bundle.
- A legacy `.agents/` fixture migrates DIRECTLY to the final flat layout (migration tests assert final
  destinations, no `.aw/records/docs/` intermediate).
- `.aw/records/` root has no `<RUN_ID>` run dirs and no duplicate `prompts` leaf; drift-guard extended.

## Spec / documentation sync

- Implements spec 20260817-2124-01; E-08 advances it to `implemented` and moves blocked backlog lavkg7
  to done (release gate). Updates the Order-02-corrected shipped docs to the final flat paths.

## Open questions

### OQ-01: run-artifacts home - top-level `workflow-artifacts/` or `.aw/records/runs/`? (mirrors spec OQ-A1)

- Blocking: yes
- Status: open
- Owner: maintainer (resolve at spec approval)
- Resolution or deferral rationale: Determines E-01/E-02. Spec recommendation: option 1 (keep top-level
  `workflow-artifacts/` as the single home, drop the `.aw/records/<run>` home) - less shipped-body churn
  and keeps `.aw/records/` purely durable. Finalize the E-items when the spec resolves this.

### OQ-02: flatten `docs/` fully + library name + `misc/`? (mirrors spec OQ-B1/OQ-C1/OQ-C2)

- Blocking: yes
- Status: open
- Owner: maintainer (resolve at spec approval)
- Resolution or deferral rationale: Determines E-03/E-04/E-05/E-06/E-07 target names. Spec defaults:
  flat `.aw/records/{specs,research,walkthroughs,roadmaps}`, library `prompt-library/`, `misc/` only if
  a real need. Finalize on spec approval.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: exactly one documented run-artifacts home; `.aw/records/` root has no `<RUN_ID>` dirs; grep shows no code writes run records under `.aw/records/`; the `.gitignore` + workflow bodies + migration agree. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: this repo's `.aw/records/` root lists only durable record types (no assess-*/verify/release-review/advise-* dirs). Paste `ls .aw/records/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the prompt library resolves at its new distinct name; staging `.aw/records/prompts/` unchanged; no duplicate `prompts` leaf. Paste resolver output + `ls`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `resolve_record_path("specs"/"research"/...)` returns the flat `.aw/records/<type>` (not `.aw/records/docs/<type>`); a consumer verb (e.g. `aw specs check`, `aw research index --check`) resolves them. Paste.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: a legacy `.agents/docs/{research,specs,...}` fixture migrates DIRECTLY to the final flat `.aw/records/{...}` (no `.aw/records/docs/` intermediate); migration tests assert the final destinations. Paste test output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: shipped bundle + regenerated AGENTS.md reference the final flat paths (e.g. `.aw/records/research`, not `.aw/records/docs/research`); the Order-02 drift guard (extended) passes. Paste grep + test.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: this repo's tracked doc trees are physically at the final flat paths (git mv done); INDEX/STATUS regenerated; `aw plans index --check` clean. Paste `git status`/`ls`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: full serial suite green (>= baseline); all `aw ... --check`/`sanitize` clean; wheel ships the final-layout bundle; spec 20260817-2124-01 advanced to `implemented`; backlog lavkg7 moved to `done` (release gate cleared). Paste suite summary + spec/backlog status.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

BLOCKED ON SPEC APPROVAL: this IPD is a draft whose E-item target names depend on spec 20260817-2124-01
OQ-A1/OQ-B1/OQ-C1/OQ-C2. It must reach `to-review` -> `/plan-review` -> human `approved` only AFTER the
spec's blocking OQs are resolved (finalizing the E-items). Execution requires human approval
(`Status: approved` + attributed `- Approval:` line). The executor implements E-01..E-08, pastes actual
evidence (resolver outputs, the legacy->final migration test, the drift guard, the full serial suite,
the spec/backlog transitions), commits only the scoped paths (`agent_workflows/record_producers.py`,
`project_schema.py`, `project_context.py`, `layout_migration.py`, `engine.py`, the shipped
`.aw/system/**` docs, `AGENTS.md`, `.gitignore`, the workflow bodies for the run-artifacts home, tests,
and the one-time `.aw/records/**` `git mv` + INDEX/STATUS), never pushes, runs `aw ipd lint
--phase pre-transition` + the full suite, and the orchestrator owns the move to `executed/`. RELEASE
BLOCKER: clears backlog lavkg7 + spec 20260817-2124-01, which the Section 8 Go/No-Go gates on.
