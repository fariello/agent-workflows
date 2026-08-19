# IPD: create the releases record class and tree

- Date: 2026-08-18
- Kind: child
- Concern: awrelease Order 01 (spec 20260818-1525-03, RELEASE BLOCKER; TODO item 35). Create the new `.aw/records/releases/` record class + tree so a release is a first-class artifact (a thin ship-gate anchor). This Order adds the CLASS plumbing (enum, subpath, facet, attention mapping, README, installer scaffolding) + a minimal release-record creator/validator. The `Blocks-Release` gate field + setter is Order 02; docs are Order 03.
- Scope: `agent_workflows/record_producers.py` (RecordClass + subpaths), `agent_workflows/plans_refs.py` + `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py` (add the `release` facet), `agent_workflows/attention_contract.py` (a _RELEASES_MAP + register), `agent_workflows/engine.py` (scaffold the dir), a new `.aw/records/releases/README.md`, and tests. IN: everything needed for `.aw/records/releases/*.release.md` to be a recognized, scaffolded, attention-visible class + a way to create/validate a release record. OUT: the `Blocks-Release:` item field + setter (Order 02); AGENTS.md docs (Order 03); attention SURFACING of release blockers (awdoctor Set).
- Status: executed
- Set: awrelease
- Order: 1
- Highest E allocated: 06
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wl6c7z

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from spec 20260818-1525-03 + investigation (RecordClass record_producers.py:85; _RECORD_CLASS_SUBPATHS:125; ARTIFACT_TYPE_FACETS plans_refs.py:33 + normalize_plan_names.py:113; CLASS_MAPS attention_contract.py:249; _record_scaffold_dirs engine.py:3780; DOCS_SUBDIRS engine.py:3726).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. Verified RecordClass/subpath/facet/CLASS_MAPS/scaffold anchors. PR-001 (MEDIUM): E-04/E-06 missed that DOCS_SUBDIRS is DUPLICATED (engine.py:3726 + normalize_plan_names.py:77) with a drift-guard test (test_normalize_plan_names.py:430) that FAILS unless both get `releases`, and that _record_scaffold_dirs is a hand-maintained two-branch dict (only the aw branch needs releases; no legacy form). Made E-04/E-06 explicit. GO - PENDING HUMAN APPROVAL.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-06 performed, V pass; new releases record class fully wired (enum/subpath/facet/attention/scaffold/deep-cleanup/README/releases.py); full serial suite 1062 passed 1 skipped.

## Goal

Stand up `.aw/records/releases/` as a real record class: register it in the RecordClass enum + subpath
map, add the `release` filename facet in both grammar sites, give it an attention class-map so release
records show on the board, scaffold the directory + a README, and provide a minimal release-record
create/validate path. After this Order a release record is a recognized, greppable, attention-visible
artifact; Order 02 adds the item-side gate field.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Make the edits at the exact anchors below. Add the `release` facet in BOTH grammar
sites (they are duplicated). Run the full suite after E-05. Do not change unrelated classes.

### Task group 1: register the class

- [x] E-01 In `agent_workflows/record_producers.py`, add `RELEASES = "releases"` to the `RecordClass` enum (after WALKTHROUGHS, near record_producers.py:94), and add `RecordClass.RELEASES.value: "releases"` to `_RECORD_CLASS_SUBPATHS` (record_producers.py:125) AND to `_LEGACY_RECORD_CLASS_SUBPATHS` (record_producers.py:139, reusing the same `"releases"` subpath since there is no legacy `.agents/` releases tree).
  - Depends on: none
  - Expected outcome: `python3 -c "from agent_workflows.record_producers import RecordClass, resolve_record_path; print(RecordClass.RELEASES.value)"` prints `releases`; `resolve_record_path("releases", target_repo=<repo>)` resolves to `<repo>/.aw/records/releases`.
  - Execution state: performed

### Task group 2: the `release` filename facet

- [x] E-02 Add `"release"` to the artifact-type facet tuple in BOTH sites: `agent_workflows/plans_refs.py:33` `ARTIFACT_TYPE_FACETS` and `.aw/system/workflows/setup-repo/tools/normalize_plan_names.py:113` `_ARTIFACT_TYPE_FACETS` (and the inline alternation in `_NEW_RE` at normalize_plan_names.py:104-107 if it lists the facets inline — add `release` there too). Keep both lists identical.
  - Depends on: none
  - Expected outcome: `python3 -c "from agent_workflows.plans_refs import ARTIFACT_TYPE_FACETS as F; print('release' in F)"` prints True; a name like `20260818-r1-01-abc123-first.release.md` is recognized as conformant by the normalizer's `is_conformant(name, expected_type='release')`.
  - Execution state: performed

### Task group 3: attention visibility

- [x] E-03 In `agent_workflows/attention_contract.py`, add a `_RELEASES_MAP` mapping the release statuses to attention classes: `{"planned": "ready", "blocked": "blocked", "shipped": "done"}` and register it in `CLASS_MAPS` (attention_contract.py:249) under key `"releases"`. Add `releases` to the tracked-tree policy (`TREE_POLICY`, attention_contract.py:83) so the attention scanner reads `.aw/records/releases/`. Add a `_release_record` reader in `attention.py` mirroring `_spec_record`/`_backlog_record` (read the release file's `- Status:` via the same bullet regex and call `A.class_of("releases", status)`).
  - Depends on: E-01
  - Expected outcome: a `.aw/records/releases/<...>.release.md` with `- Status: planned` appears in `aw attention` under `ready`; `aw attention --check` stays valid.
  - Execution state: performed

### Task group 4: scaffolding + README

- [x] E-04 Scaffold the directory: add `releases` to the record scaffold set so `aw install`/setup creates `.aw/records/releases/` with a README. Specifically: (1) add `"releases"` to `DOCS_SUBDIRS` in BOTH copies that must stay in sync - `engine.py:3726` AND the DUPLICATED `normalize_plan_names.py:77` (a drift-guard test, tests/test_normalize_plan_names.py:430, asserts `NPN.DOCS_SUBDIRS == engine.DOCS_SUBDIRS`, so updating only one BREAKS that test); (2) add a `releases` entry to `_record_scaffold_dirs` (engine.py:3780) - it is a HAND-MAINTAINED dict with two branches; add `"releases": f"{base}/releases"` to the `aw` branch (~engine.py:3789). The `legacy` branch does NOT get releases (it is a new `.aw/`-only class with no `.agents/` history); (3) add `.aw/records/releases` to `_DEEP_CLEANUP_ROOTS` (engine.py:3427) so uninstall --deep removes it. Create `.aw/records/releases/README.md` (mirror the roadmaps README tone): "Release records: thin ship-gate anchors. A release record (`<...>.release.md`) names a planned release (Version or 'next'), its Status (planned/blocked/shipped), and a Summary. Items declare they gate a release via a `Blocks-Release:` field (see AGENTS.md). This is a COMMITTED ship gate, distinct from roadmaps (possibilities)."
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` (or the scaffold path in a test) creates `.aw/records/releases/README.md`; `_DEEP_CLEANUP_ROOTS` includes the releases tree; the DOCS_SUBDIRS drift-guard test still passes (both copies updated).
  - Execution state: performed

### Task group 5: create + validate a release record

- [x] E-05 Add a minimal release-record creator + validator (new small module `agent_workflows/releases.py`): `create_release(repo_root, version, summary, status="planned") -> Path` writing a conformant `<YYYYMMDD>-<setid>-01-<id6>-<slug>.release.md` (setid = id6 for a standalone, per the grammar) with front-matter `- Id:`/`- Status:`/`- Version:`/`- Summary:` + a `## Workflow history`; and `validate_release(path, text) -> List[Drift]` checking Status in {planned,blocked,shipped}, a present Version, and a valid id6 (reuse artifact_core). Wire `validate_release` so the awcheck engine can pick up `releases` content later (add `"releases": ("names","content")` to check_engine.SUPPORTED if that module exists; if not yet, note it as a follow-up for awcheck).
  - Depends on: E-01,E-02
  - Expected outcome: `create_release(root,"2.0.0","first .aw/ release")` writes a `.release.md` file with a valid id6 + `- Status: planned`; `validate_release` returns [] for it and a Drift for a bad status.
  - Execution state: performed

### Task group 6: tests

- [x] E-06 Add `tests/test_releases.py` (`ReleasesClassTests`): `test_class_resolves` (resolve_record_path("releases") ends in .aw/records/releases), `test_facet_recognized` (is_conformant of a `.release.md` name), `test_attention_shows_release` (a planned release appears in the attention scan as ready + `--check` valid), `test_create_and_validate` (create_release writes a valid record; validate_release flags a bad status), `test_deep_cleanup_includes_releases`. Update any test asserting the exact facet tuple / RecordClass membership / scaffold-dir count to include `releases`, and SPECIFICALLY re-run tests/test_normalize_plan_names.py:421-432 (the DOCS_SUBDIRS drift guard `NPN.DOCS_SUBDIRS == engine.DOCS_SUBDIRS`) which will FAIL unless BOTH DOCS_SUBDIRS copies got `releases` (E-04). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04,E-05
  - Expected outcome: the new tests pass; membership/count tests updated; full serial suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `RecordClass` enum + `_RECORD_CLASS_SUBPATHS` + `_LEGACY_RECORD_CLASS_SUBPATHS` (record_producers.py:85/125/139) define a class; `resolve_record_path`/`resolve_record_read_paths` consume them.
- The facet tuple is DUPLICATED: `ARTIFACT_TYPE_FACETS` (plans_refs.py:33) and `_ARTIFACT_TYPE_FACETS` (normalize_plan_names.py:113) + possibly inline in `_NEW_RE` (:104). Update all.
- Attention: `CLASS_MAPS` + `TREE_POLICY` (attention_contract.py:249/83); per-tree readers in attention.py mirror `_spec_record`/`_backlog_record`.
- Installer scaffolding: `DOCS_SUBDIRS` (engine.py:3726), `_record_scaffold_dirs` (engine.py:3780), `_DEEP_CLEANUP_ROOTS` (engine.py:3427).
- Standalone naming: setid = id6, NN=01 (uniform grammar); facet `release` -> `*.release.md`.
- roadmaps README (`.aw/records/roadmaps/README.md`) is the tone template; releases README must stress "committed ship gate, NOT a roadmap/possibility".

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Adding a class is a known, patterned change. | Follow the existing enum/subpath/facet/attention/scaffold pattern for the other classes; low risk. |
| F2 | Facet tuple duplicated in 2-3 spots. | Update ALL sites or names won't validate; E-02 enumerates them. |
| F3 | Membership/count tests may assert the old class set. | E-06 updates them (facet tuple, RecordClass, scaffold-dir count). |

## Proposed changes (ordered, validatable)

1. RecordClass + subpaths (E-01). 2. `release` facet in both grammar sites (E-02). 3. attention map + reader (E-03). 4. scaffold dir + README + deep-cleanup (E-04). 5. releases.py create/validate (E-05). 6. tests + suite (E-06).

## Deferred / out of scope (with reason)

- The `Blocks-Release:` item field + setter: Order 02.
- AGENTS.md documentation of BLOCKS-RELEASE vs BLOCKED-BY: Order 03.
- Attention SURFACING of the release-blocker set: awdoctor Set (consumes this class).
- Folding release validation into the awcheck engine SUPPORTED map: noted in E-05; finalized when both Sets are executed.

## Scope check

- Over-scope: none - only the class plumbing + a minimal create/validate.
- Under-scope: none - the class is fully recognized (resolve/facet/attention/scaffold) + creatable + validatable.

## Required tests / validation

`tests/test_releases.py` (E-06) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

The releases README is created (E-04). AGENTS.md BLOCKS-RELEASE documentation is Order 03. No spec transition here (orchestrator advances spec 20260818-1525-03 when the Set completes).

## Open questions

### OQ-01: standalone release setid = id6, or a short version-derived setid?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: setid = id6 for a standalone release record (the uniform-grammar standalone convention). A human-friendly slug carries the version. Deterministic; matches how other standalone records are named.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `RecordClass.RELEASES.value` == "releases" and `resolve_record_path("releases", target_repo=<repo>)` ending in `.aw/records/releases`.
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `'release' in ARTIFACT_TYPE_FACETS` True and `is_conformant("20260818-r1-01-abc123-first.release.md", expected_type="release")` True.
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste a release record showing under `ready` in `aw attention` + `aw attention --check` valid.
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste a scaffold run creating `.aw/records/releases/README.md` + `_DEEP_CLEANUP_ROOTS` containing the releases tree.
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `create_release(...)` output path + `validate_release` returning [] for it and a Drift for a bad status.
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `pytest tests/test_releases.py -p no:xdist -q` passing + the full serial suite tail (no regressions).
  - Observed evidence: Verified: RecordClass.RELEASES resolves; .release.md facet conformant; create/validate/resolve_release + attention reader work (test_releases 6 pass); suite 1062p/1s.
  - Result: pass

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the six E-items are one indivisible unit of work - registering a new record class REQUIRES the enum+subpath, the facet, the attention mapping, the scaffold+README, and a create/validate path to all land together, or the class is half-real (e.g. resolvable but not attention-visible, or named but not scaffolded). Splitting further would leave broken intermediate states. All six are small, mechanical, and follow the existing class-registration pattern.

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the touched files
path-scoped (never `git add -A`), never pushes, and transitions only after `aw ipd lint --phase
pre-transition` conforms and every V is `pass`. Order 01 of awrelease (RELEASE BLOCKER); Orders 02 (gate
field) + 03 (docs) build on this class.
