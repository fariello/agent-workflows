# IPD: Clean up .aw/records/ taxonomy: run-artifacts home, dedup prompts, flatten docs (pre-release, legacy->final only)

- Date: 2026-08-17
- Kind: child
- Concern: Spec 20260817-2124-01 (RELEASE BLOCKER): the `.aw/records/` taxonomy has (A) workflow run-artifacts (assess-*/verify/verify-execution/release-review/advise-*) at the records ROOT, (B) two identically-named `prompts` dirs (staging vs library), (C) deeper-than-wanted `docs/` nesting. Backlog lavkg7 gates the release on this.
- Scope: Implement the spec's FINAL `.aw/records/` taxonomy. PRE-RELEASE framing (spec Section 0): the `.aw/` layout has NOT shipped, so this changes the legacy `.agents/` -> FINAL migration DESTINATIONS in place and brings this dev repo onto the final layout by a one-time git mv - it does NOT build an intermediate `.aw/records/docs/` -> final migration hop. Task groups A (run-artifacts home), B (dedup prompts), C (flatten docs). OUT: the four physical roots, records-backend choice, changing what any workflow does.
- Status: executed
- Set: awretrofit
- Order: 7
- Highest E allocated: 08
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: u7xtni

## Workflow history

- 2026-08-17 authored (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): created from spec 20260817-2124-01 (Set awretrofit Order 07); E-items finalized after the maintainer resolved the spec OQs (run-artifacts -> .aw/workflow-artifacts/; flatten -> .aw/records/{research,specs,walkthroughs,roadmaps}; library -> .aw/records/prompt-library/; no misc/). Ready for /plan-review.
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Verified against real code: PR-001 (HIGH, correctness) - `_RECORD_CLASS_SUBPATHS` (record_producers.py:120-129) is used for BOTH the `.aw/records/` primary AND the legacy `.agents/` read path (resolve_record_read_paths:603-609), so E-04 must DECOUPLE the subpaths (final `.aw/records/specs` while legacy stays `.agents/docs/specs`), NOT rewrite one constant; hardened E-04. PR-002 (MEDIUM) - the schema already has contradictory `RecordClass.RUNS -> "runs"` (the rejected `.aw/records/runs` home) AND `WORKFLOW_ARTIFACTS -> "workflow-artifacts"` (record_producers.py:126-127); E-01 hardened to reconcile them to the single `.aw/workflow-artifacts/` home. Both FIXED in plan. No open questions (spec OQs resolved). GO - PENDING HUMAN APPROVAL.
- 2026-08-17 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified against controlling spec 20260817-2124-01 and codebase evidence (record_producers.py, layout_migration.py); structural lint conforming; no open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved (after two independent /plan-review passes). Implemented E-01..E-08 in commits 1308220 (resolvers/migration/gitignore/git mv/tests) + 324ef2e (shipped-doc flatten) + 95d37bf (AGENTS.md regen + evidence). Flattened .aw/records/ (docs types direct; run-artifacts -> .aw/workflow-artifacts/; docs/prompts -> prompt-library); decoupled legacy read subpaths (PR-001); removed contradictory RUNS/WORKFLOW_ARTIFACTS classes (PR-002); legacy->final migration verified DIRECT (no intermediate hop). V-01..V-08 verified with pasted evidence; full serial suite 986 passed/1 skipped; wheel ships flat layout; all checks clean. pre-transition lint conforming; moved pending -> executed/. The spec 20260817-2124-01 -> implemented and backlog lavkg7 -> done are completed immediately after this move (citing this executed IPD as evidence).

## Goal

Land the FINAL `.aw/records/` taxonomy from spec 20260817-2124-01 so the first release carrying the
`.aw/` layout ships a clean, self-consistent record tree: run-artifacts in one obvious home, no
duplicate `prompts` name, and the durable doc types at their agreed final paths - implemented as a
legacy->final destination change plus a one-time dev-repo `git mv`, with NO intermediate migration hop.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FINALIZED TARGETS (spec 20260817-2124-01 OQs resolved by the maintainer 2026-08-17):
- Run-artifacts single home = **`.aw/workflow-artifacts/<workflow>/<RUN_ID>/`** (under `.aw/`, NOT repo-root).
- Durable doc types FLATTENED to **`.aw/records/{research,specs,walkthroughs,roadmaps}`** (no `docs/`).
- Prompt LIBRARY = **`.aw/records/prompt-library/`**; lifecycle STAGING `.aw/records/prompts/` UNCHANGED.
- NO `misc/` catch-all.
- Uniform `.type.md` FILE-naming is a SEPARATE spec (20260817-2147-01, its own Order); this Order is
  DIRECTORIES only and keeps existing filenames.

### Task group A: run-artifacts get one obvious home (spec G1, OQ-A1 -> `.aw/workflow-artifacts/`)

- [x] E-01 Make `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` the SINGLE run-artifacts home. (a) Point the shipped workflow bodies that write run records (assess.md, verify.md, verify-execution.md, the release-review runbook, advise.md) at `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` instead of repo-root `workflow-artifacts/`. (b) REMOVE the `.aw/records/{assess-*,verify,verify-execution,release-review,advise-*}` home: delete its `.gitignore` lines (currently :68-72) and add a single `.aw/workflow-artifacts/` ignore; remove any migration step that relocates old `workflow-artifacts/` INTO `.aw/records/`. (c) Confirm no code writes run records under `.aw/records/`. **plan-review PR-002:** the schema ALREADY has `RecordClass.RUNS -> "runs"` and `RecordClass.WORKFLOW_ARTIFACTS -> "workflow-artifacts"` (record_producers.py:126-127) - i.e. two competing run-artifact classes, one of which (`runs` = `.aw/records/runs`) is the option-2 home the maintainer REJECTED. Reconcile: make the run-artifacts class resolve to `.aw/workflow-artifacts/` (not `.aw/records/runs`), and retire/redirect the now-unused `RUNS`/`runs` subpath (remove it or point it at the single home) so there are not two contradictory enum values. Check + update every consumer of those two enum values.
  - Depends on: none
  - Expected outcome: exactly ONE documented home (`.aw/workflow-artifacts/`); `.aw/records/` root has no `<RUN_ID>` dirs; no contradictory `RUNS` vs `WORKFLOW_ARTIFACTS` enum resolution; workflow bodies + `.gitignore` + migration + schema enums agree; `.aw/workflow-artifacts/` gitignored.
  - Execution state: performed

- [x] E-02 Bring THIS dev repo onto the decision: move the existing untracked `.aw/records/{assess-*,verify,verify-execution,release-review,advise-*}` run dirs to `.aw/workflow-artifacts/<workflow>/` (one-time; they are untracked so a plain `mv`), or remove any that duplicate content already under the run-artifacts home.
  - Depends on: E-01
  - Expected outcome: this repo's `.aw/records/` root contains only durable record types; the moved run dirs live under `.aw/workflow-artifacts/`.
  - Execution state: performed

### Task group B: dedup the `prompts` name (spec G2, OQ-B1 -> `prompt-library/`)

- [x] E-03 Rename the prompt LIBRARY to `.aw/records/prompt-library/` (was `.aw/records/docs/prompts/`), leaving the lifecycle STAGING `.aw/records/prompts/` UNCHANGED. Update `resolve_record_path`/read-paths + any consumer + the shipped docs that reference the library path.
  - Depends on: E-04
  - Expected outcome: no two record subtrees share the leaf name `prompts`; the library resolves at `.aw/records/prompt-library/`; staging `prompts/` unchanged.
  - Execution state: performed

### Task group C: flatten docs/ (spec G3, OQ-C1 -> flat; OQ-C2 -> no misc)

- [x] E-04 Update the canonical layout + resolvers so the durable doc types resolve at the FINAL flat paths `.aw/records/{research,specs,walkthroughs,roadmaps}` instead of `.aw/records/docs/{...}`. The single source is `_RECORD_CLASS_SUBPATHS` (record_producers.py:120-129: `SPECS: "docs/specs"`, `RESEARCH: "docs/research"`, `WALKTHROUGHS: "docs/walkthroughs"`; add ROADMAPS if not present). **CRITICAL (plan-review PR-001):** that same subpath is used for BOTH the `.aw/records/` primary path AND the LEGACY `.agents/` read path (`resolve_record_read_paths` :603-609 builds `.agents/<subpath>`). Legacy is genuinely `.agents/docs/specs`, so the flatten MUST DECOUPLE the two: introduce a separate legacy-subpath map (or per-class `(final_sub, legacy_sub)`) where the `.aw/records/` sub becomes `specs`/`research`/... while the LEGACY sub stays `docs/specs`/`docs/research`/.... Do NOT just rewrite the one constant (that would make legacy reads resolve `.agents/specs`, breaking migration reads). Also update `research_contract.py` (`RESEARCH_ROOT`=`.agents/docs/research` legacy + `resolve_research_root` :344 `.aw/records/docs/research` -> `.aw/records/research`) and `project_schema`/`project_context` targets. Do NOT add a `misc/` catch-all (OQ-C2: omit).
  - Depends on: none
  - Expected outcome: every resolver + consumer verb (`aw specs`, `aw research`, `aw plans`, `aw attention`, `aw backlog`) resolves the flat final `.aw/records/<type>`; LEGACY `.agents/docs/<type>` reads still resolve (decoupled subpath); no `docs/` level in `.aw/records/`; no `misc/`.
  - Execution state: performed

- [x] E-05 Update the legacy->FINAL migration DESTINATIONS in `layout_migration.py` (and its mapping tables) so legacy `.agents/docs/{research,specs,walkthroughs,roadmaps}` and `.agents/docs/prompts` map DIRECTLY to the final flat paths + the renamed library - NO intermediate `.aw/records/docs/` hop (spec Section 0). Update the awphysical migration tests' expected destinations.
  - Depends on: E-04, E-03
  - Expected outcome: `aw migrate-layout` maps legacy `.agents/*` directly to the final layout; migration tests assert the final destinations.
  - Execution state: performed

### Task group D: reconcile shipped docs + bring this dev repo onto the final tree

- [x] E-06 Update every SHIPPED doc/AGENTS.md-generator/index.md/template path that Order 02 set to the INTERMEDIATE `.aw/records/docs/{...}` so it now names the FINAL flat paths (e.g. the engine.py AGENTS.md generator aw-branch `.aw/records/docs/research` -> `.aw/records/research`), and regenerate AGENTS.md. Extend the Order-02 drift-guard test accordingly.
  - Depends on: E-04
  - Expected outcome: shipped bundle + AGENTS.md reference the final flat paths; drift guard updated.
  - Execution state: performed

- [x] E-07 One-time `git mv` of THIS dev repo's tracked doc trees `.aw/records/docs/{research,specs,walkthroughs,roadmaps}` -> `.aw/records/{...}` and the library rename, plus the run-artifacts move (E-02), updating any tracked references + regenerating INDEX/STATUS manifests.
  - Depends on: E-04, E-05, E-06, E-02, E-03
  - Expected outcome: this repo is physically on the final layout.
  - Execution state: performed

### Task group E: verification + unblock the release gate

- [x] E-08 Full validation: serial suite green (>= current baseline), `aw attention --check` / `aw plans index --check` / `aw research index --check` / `aw specs check` / `aw backlog check` / `aw sanitize --agent` clean, wheel rebuild ships the final-layout bundle, and a legacy-`.agents/` fixture migrates DIRECTLY to the final layout (no docs/ hop). Then advance spec 20260817-2124-01 to implemented and move blocked backlog lavkg7 to done (unblocking the release gate).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: all checks green; spec implemented; lavkg7 done; the release blocker is cleared.
  - Execution state: performed

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

### OQ-01: run-artifacts home - top-level `workflow-artifacts/` or `.aw/records/runs/`? (mirrors spec OQ-A1) [RESOLVED]

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-17)
- Resolution or deferral rationale: SINGLE home = `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` (the
  maintainer chose top-level-single-home AND under `.aw/` rather than repo-root). The `.aw/records/<run>`
  home is removed. E-01/E-02 finalized to this.

### OQ-02: flatten `docs/` + library name + `misc/`? (mirrors spec OQ-B1/OQ-C1/OQ-C2) [RESOLVED]

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-17)
- Resolution or deferral rationale: FLATTEN to `.aw/records/{research,specs,walkthroughs,roadmaps}`;
  library = `.aw/records/prompt-library/`; NO `misc/`. E-03/E-04/E-05/E-06/E-07 finalized to these.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: exactly one documented run-artifacts home; `.aw/records/` root has no `<RUN_ID>` dirs; grep shows no code writes run records under `.aw/records/`; the `.gitignore` + workflow bodies + migration agree. Paste.
  - Observed evidence: Removed `RecordClass.RUNS`/`WORKFLOW_ARTIFACTS` + subpath entries (zero remaining consumers, grep-verified). `.gitignore` now a single `.aw/workflow-artifacts/` ignore. `git check-ignore .aw/workflow-artifacts/verify` -> IGNORED; `.aw/records/research` -> not ignored. `ls .aw/records/` -> backlog comms plans prompt-library prompts README.md research roadmaps specs walkthroughs (no `<RUN_ID>` dirs).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: this repo's `.aw/records/` root lists only durable record types (no assess-*/verify/release-review/advise-* dirs). Paste `ls .aw/records/`.
  - Observed evidence: moved 9 untracked run dirs (assess-bugs/documentation/secrets/self-documentation/testing, advise-spec-editor, release-review, verify, verify-execution) to `.aw/workflow-artifacts/`. `ls .aw/records/` afterward: only durable types (see V-01). No run dirs at the records root.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the prompt library resolves at its new distinct name; staging `.aw/records/prompts/` unchanged; no duplicate `prompts` leaf. Paste resolver output + `ls`.
  - Observed evidence: `git mv .aw/records/docs/prompts -> .aw/records/prompt-library` (6 files, history preserved). `ls .aw/records/prompts/` still shows the lifecycle staging (pending/executed/reusable/superseded/not-executed/README). Two distinct leaves: `prompts/` (staging) and `prompt-library/` (library) - no collision. artifact_core SCAN_ROOTS + attention `_DOCS_FAMILY` map `prompt-library` to the legacy docs/prompts policy.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `resolve_record_path("specs"/"research"/...)` returns the flat `.aw/records/<type>` (not `.aw/records/docs/<type>`); a consumer verb resolves them. Paste.
  - Observed evidence: `resolve_record_path('specs')` -> `.aw/records/specs`; `('research')` -> `.aw/records/research`; `('walkthroughs')` -> `.aw/records/walkthroughs` (all flat). Decoupled legacy map keeps `.agents/docs/specs` for legacy reads (PR-001). `aw specs check` -> all specs conform; `aw research index --check` -> clean (83 docs at `.aw/records/research`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: a legacy `.agents/docs/{...}` fixture migrates DIRECTLY to the final flat `.aw/records/{...}` (no intermediate); migration tests assert final destinations. Paste.
  - Observed evidence: `aw migrate-layout plan` on a legacy `.agents/docs/*` fixture -> destination_relpath `records/specs/s.spec.md`, `records/research/r.md`, `records/walkthroughs/w.md`, `records/prompt-library/lib.md`, `records/plans/pending/p.md` - DIRECT to final flat, no `records/docs/` hop. awphysical tool + migration test suites: 68 passed. (Bare `docs` dir entry maps to `records/docs` but directory entries are never materialized - layout_migration.py:724 moves only files/symlinks - so no empty `.aw/records/docs/` is created.)
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: shipped bundle + regenerated AGENTS.md reference the final flat paths; the Order-02 drift guard (extended) passes. Paste grep + test.
  - Observed evidence: `git grep records/docs -- .aw/system/** agent_workflows/**` -> empty (0). AGENTS.md regenerated via the real code path: `grep -c "records/docs\|.agents/" AGENTS.md` -> 0; references `.aw/records/research/`, `.aw/records/walkthroughs/`, `.aw/records/specs/`. `tests/test_awretrofit_shipped_docs.py` (updated to assert flat + assertNotIn `.aw/records/docs/`) -> 4 passed.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: this repo's tracked doc trees are physically at the final flat paths (git mv done); INDEX/STATUS regenerated; `aw plans index --check` clean. Paste.
  - Observed evidence: `git mv` relocated research(103)/specs(18)/walkthroughs(13)/roadmaps(2) + prompt-library(6) to flat `.aw/records/*` (renames tracked at 100% similarity); obsolete `.aw/records/docs/README.md` removed; `.aw/records/docs/` gone. INDEX (plans 178, research 83) + STATUS (194) regenerated; `aw plans index --check` clean; backlog Gate-Refs repointed to `.aw/records/specs/`.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: full serial suite green (>= baseline); all `aw ... --check`/`sanitize` clean; wheel ships the final-layout bundle; spec advanced to `implemented`; backlog lavkg7 moved to `done`. Paste.
  - Observed evidence: full serial suite `986 passed, 1 skipped` (== baseline; fixed 5 pre-flatten-path tests + SOURCE_DOCS helper). `aw specs/research index/backlog/attention --check` + `aw sanitize --agent` all clean. Wheel rebuild: no `records/docs`, no legacy `.agents/workflows`, flat layout shipped. Spec 20260817-2124-01 walked draft->...->implementing; final `implemented` + backlog lavkg7 done are performed in the terminal transition step (cites the executed IPD as evidence) after this IPD moves to executed/.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

SPEC OQs RESOLVED (2026-08-17): the E-item target names are finalized (`.aw/workflow-artifacts/`,
flat `.aw/records/{research,specs,walkthroughs,roadmaps}`, `.aw/records/prompt-library/`, no `misc/`),
so this IPD is ready for `/plan-review` -> human `approved` -> execution. Execution requires human approval
(`Status: approved` + attributed `- Approval:` line). The executor implements E-01..E-08, pastes actual
evidence (resolver outputs, the legacy->final migration test, the drift guard, the full serial suite,
the spec/backlog transitions), commits only the scoped paths (`agent_workflows/record_producers.py`,
`project_schema.py`, `project_context.py`, `layout_migration.py`, `engine.py`, the shipped
`.aw/system/**` docs, `AGENTS.md`, `.gitignore`, the workflow bodies for the run-artifacts home, tests,
and the one-time `.aw/records/**` `git mv` + INDEX/STATUS), never pushes, runs `aw ipd lint
--phase pre-transition` + the full suite, and the orchestrator owns the move to `executed/`. RELEASE
BLOCKER: clears backlog lavkg7 + spec 20260817-2124-01, which the Section 8 Go/No-Go gates on.
