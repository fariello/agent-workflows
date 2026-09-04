# IPD: Core Layout Model and JSON Schema in layout.py

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout definitions need a single source of truth in Python with strongly-typed dataclasses and deterministic JSON / JSON Schema generation per Spec kw5y2s.
- Scope: Create `agent_workflows/layout.py` with dataclasses (`RecordClassDefinition`, `LayoutModel`), canonical layout constants, `build_default_layout()`, `to_json()`, and `to_schema()`. Add unit tests in `tests/test_layout.py`.
- Scope-Paths: agent_workflows/layout.py, tests/test_layout.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Set: wslayout
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: wpu5zu
- From-Spec: kw5y2s

## Workflow history

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019..PR-023 fixed across Set (added structured readiness field; consumer interface confirmed against newly-reviewed children 02-05).
- 2026-09-02 reviewed (aw set): plan-review round 2: APPROVE WITH REVISIONS APPLIED; PR-015..PR-018 fixed (incomplete consumer interface, other/3.9, undeclared jsonschema, missing execution contract)

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - Survives nearly intact (PR-001 vocabulary pinning only); the additive layout.py + tests/test_layout.py shape is correct.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all eight findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2 at HEAD `90434d47`, this child alone: APPROVE WITH REVISIONS APPLIED; PR-015..PR-018 all FIXED. The round-1 external gate is CLEARED (spec `kw5y2s` now `approved --by-human`), and round 1's vocabulary pinning was re-verified live (10 + 9 -> 12 = eleven classes plus the `records` carve-out; exclusions exactly seven; aliases intact). PR-015 HIGH: E-01's promised surface was INCOMPLETE FOR ITS OWN CONSUMERS. `zvk796` E-02 imports `KNOWN_PRIMARY_TYPES` (measured a DISTINCT 9-member set, `ARTIFACT_TYPES` minus `other`) and `rodj06` E-01 imports the durable/runtime state vocabularies (5 and 6 members), none of which E-01 named; a gap would have passed here and failed at import time in a later child. PR-016 HIGH: `other` needs a SECOND carve-out, since `record_dirs` computes it as the complement of `KNOWN_PRIMARY_TYPES`/`EXCLUDED_RECORD_DIRS` (measured: returns `reviews` + `prompt-library`, and no `other/` dir exists), so modeling it as `subpath: "other"` would silently change traversal. Also pinned the Python 3.9 floor against the spec's non-3.9-valid `tuple[...]`/`dict[...]` dataclass annotations. PR-017 MEDIUM: E-02 proposed an UNDECLARED `jsonschema` dependency (importable at 4.26.0, declared nowhere, imported by nothing), now either stdlib validation or a declared `[test]` entry with `pyproject.toml` added to scope. PR-018 LOW: added the missing execution contract, converted prose Findings to an evidence table, and filled the empty conventions/scope/tests/spec-sync sections. Three decisions recorded (D-11..D-13). Status to-review -> reviewed.

## Goal

Provide a standalone, pure Python layout model module (`agent_workflows/layout.py`) that encapsulates all workspace logical roots, record classes, state classes, traversal exclusions, and JSON schema emission.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Layout Model Module

- [ ] E-01 Create `agent_workflows/layout.py` defining frozen dataclasses (`RecordClassDefinition`, `LayoutModel`), `build_default_layout()`, `to_dict()`, `to_json(framework_version)`, `to_schema()`, and helper lookup methods (`get_record_subpath()`, `is_known_type()`, `normalize_type()`).
  - Depends on: none
  - Expected outcome: `agent_workflows/layout.py` exists with complete typed layout definitions.
  - Execution state: pending
  - VOCABULARY IS THE UNION (maintainer ruling 2026-09-01, plan-review PR-001). The model MUST document
    reality, not redefine it. The draft spec's table is WRONG and MUST NOT be copied verbatim: it omits
    `roadmaps` and `records` and adds `reviews`/`backlog`/`other`. Measured truth at HEAD:
    `ARTIFACT_TYPES` = plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms,
    releases, other (`agent_workflows/artifact_types.py:12-23`); `RecordClass` = plans, specs, research,
    records, prompts, comms, walkthroughs, releases, reviews
    (`agent_workflows/record_producers.py:85-101`).
  - Therefore `record_classes` MUST contain the union of ELEVEN names: plans, specs, research, backlog,
    reviews, releases, prompts, walkthroughs, roadmaps, comms, other. `roadmaps` is NOT optional: it has
    5 artifacts on disk (incl. `.aw/records/roadmaps/`) and working verbs `run_rename_roadmaps` /
    `run_group_roadmaps` (`agent_workflows/artifact_rename.py:827-828,855-856`).
  - `records` CARVE-OUT: `RecordClass.RECORDS` maps to the EMPTY subpath (`record_producers.py:136`),
    i.e. the records root itself, not a child directory. It MUST NOT be modeled as an ordinary record
    class with `subpath: "records"`. Represent it explicitly (a separate constant or an
    `is_root_alias`-style flag) so nothing derives a `records/records/` path.
  - Aliases MUST reproduce `_ALIASES` (`artifact_types.py:26-39`) exactly, including `roadmap` ->
    `roadmaps`, `others`/`misc` -> `other`, and the identity entries.
  - `traversal_exclusions` MUST reproduce `selectors.EXCLUDED_RECORD_DIRS` exactly at this stage
    (`.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`). Do NOT add
    `node_modules`/`venv`/`.venv` here; that widening is a deliberate behavior change owned by `zvk796`
    E-02 with its own assertion. RE-VERIFIED at round 2: the live set is exactly those seven.
  - PYTHON 3.9 IS THE FLOOR (`pyproject.toml:12` `requires-python = ">=3.9"`), so the spec's Section 5
    snippet CANNOT be transcribed literally: its `tuple[str, ...]` and `dict[str, ...]` annotations on
    dataclass fields are evaluated at class-creation time and fail on 3.9. Follow the house pattern used
    by every comparable module: `from __future__ import annotations` plus `typing.Tuple`/`Dict`
    (`attention_contract.py:38,41`; `worktree_lease.py:24,32`; `artifact_core.py:21,30`). Treat the
    spec snippet as a shape, not as copyable source. (Round 2, PR-016.)
  - THE MODEL MUST ALSO CARRY WHAT THE CONSUMER CHILDREN IMPORT, or Orders 02 and 03 cannot do their
    job (round 2, PR-015; each measured live at HEAD):
    * `KNOWN_PRIMARY_TYPES` is a DISTINCT, NARROWER set than the union: 9 members, exactly
      `ARTIFACT_TYPES` minus `other` (`selectors.py`, measured). `zvk796` E-02 sources it from here, so
      the model must either expose it or expose a documented rule that derives it (for example a
      per-class `is_primary` flag). Do NOT let a consumer re-hardcode it.
    * `other` IS NOT AN ORDINARY SUBPATH and is the second carve-out this model needs. `record_dirs`
      computes it as the COMPLEMENT of `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` over the records
      root, plus a literal `other/` if present (`selectors.record_dirs`, the `if record_type == "other"`
      branch). Measured: `record_dirs(repo, "other")` returns `['.aw/records/reviews',
      '.aw/records/prompt-library']` on this tree, and NO `.aw/records/other/` directory exists. Model it
      as a computed/complement class, never as `subpath: "other"`, or Order 02 will silently change
      traversal.
    * `durable_state_classes` and `runtime_state_classes` are named by the spec's `LayoutModel` and are
      consumed by `rodj06` E-01. Live values, to be reproduced exactly: durable = `install`, `history`,
      `actions`, `migrations`, `routing_receipts`; runtime = `transactions`, `locks`, `staging`,
      `backups`, `cache`, `tmp` (`record_producers.DurableStateClass`/`RuntimeStateClass`).
    * `RootClass` has SIX members (`system`, `config_project`, `config_local`, `state_durable`,
      `state_runtime`, `records`) against `LogicalRoot`'s FOUR (`system`, `config`, `state`, `records`).
      The spec's Section 5.1 item 4 explicitly forbids collapsing the six to four; the model must not
      encode a shape that invites it.
    * The three NEW record classes need real subpaths, and only two are determined by disk: `backlog` ->
      `backlog` and `roadmaps` -> `roadmaps` both exist under `.aw/records/`, while `other` is the
      computed class above. `reviews` -> `reviews` already exists in `_RECORD_CLASS_SUBPATHS`.
    * PRESERVE the bounded legacy map: `_LEGACY_RECORD_CLASS_SUBPATHS` maps `specs` -> `docs/specs`,
      `research` -> `docs/research`, `walkthroughs` -> `docs/walkthroughs` (others identical). `rodj06`
      E-01 must keep it, so the model must not assume one subpath per class.

### Task group 2: Unit Testing & Schema Conformance

- [ ] E-02 Author unit tests in `tests/test_layout.py` (NEW FILE; it does not exist today) verifying model defaults, JSON serialization determinism, type normalization, alias resolution, and JSON schema validation.
  - Depends on: E-01
  - Expected outcome: `pytest tests/test_layout.py` passes cleanly.
  - Execution state: pending
  - DO NOT INTRODUCE A `jsonschema` DEPENDENCY (round 2, PR-017). It is importable on a maintainer
    machine (4.26.0) but is declared NOWHERE: `pyproject.toml:50` declares runtime `["filelock>=3"]` and
    the `[test]` extra is `pytest`/`pytest-xdist`/`pytest-randomly`. No module under `agent_workflows/`
    or `tests/` imports it today (measured: zero matches). Depending on an accidental transitive install
    is precisely the reproducibility hole `pyproject.toml`'s own comments call out (the `filelock` note:
    "An accidental transitive install is not a dependency"), and it would make a clean
    `pip install '.[test]'` and CI run different code than the maintainer. D138 permits a justified
    dependency, so this is not a prohibition, but it is a DECLARED-OR-NOT-USED rule: either validate
    structurally with the stdlib (assert the emitted document's required keys, types, and enum values
    against the emitted schema by hand, which is what the schema is for at this scale), or, if genuine
    schema validation is judged necessary, ADD `jsonschema` to the `[test]` extra in the same change and
    say so in the V-item. `wpu5zu`'s `Scope-Paths` does not include `pyproject.toml`, so the stdlib route
    is the in-scope one; taking the dependency route requires declaring that path too.
  - MUST include a vocabulary-parity test asserting the model's `record_classes` is a SUPERSET of both
    `artifact_types.ARTIFACT_TYPES` and `{r.value for r in record_producers.RecordClass}` (excluding the
    `records` root carve-out), so a future edit that silently drops `roadmaps` (or any other live type)
    fails the suite. This is the regression fence for PR-001.
  - MUST assert the model's `traversal_exclusions` equals `selectors.EXCLUDED_RECORD_DIRS` exactly, so
    `zvk796`'s later widening is a visible, deliberate test change rather than a silent drift.
  - MUST assert the CONSUMER-INTERFACE surface E-01 now owes Orders 02 and 03 (round 2, PR-015), since
    those children import it and a missing piece surfaces there as an ImportError rather than here:
    `KNOWN_PRIMARY_TYPES` (or its derivation rule) equals the live 9-member set; the durable and runtime
    state-class vocabularies equal the live sets member-for-member; `other` is representable WITHOUT a
    literal `other` subpath; and the legacy subpath map's three `docs/`-prefixed entries survive.
  - MUST assert DETERMINISM concretely rather than by inspection: serialize twice in one process and
    assert byte equality, and assert a stable key order, since `hauwqh` E-01 relies on re-emission being
    a no-op for an unchanged version.
  - MUST run on Python 3.9 semantics: no test may depend on 3.10+ syntax, and the module must import
    cleanly under the declared floor.

## Project conventions discovered (Step 0)

- Spec `kw5y2s` Section 4 (`:171-352`) defines the JSON schema and the concrete emitted document; Section 5 (`:353-392`) defines the Python dataclass shapes. The spec is now `approved`, so do not edit it; if a further factual defect is found, report it rather than diverging silently.
- The spec's Section 5 code block is a SHAPE, not copyable source: its `tuple[...]`/`dict[...]` field annotations are invalid at class-creation time on the declared 3.9 floor.
- Python 3.9 is the floor (`pyproject.toml:12`). The house pattern for a 3.9-compatible typed module is `from __future__ import annotations` plus `typing` generics (`attention_contract.py:38,41`; `worktree_lease.py:24,32`; `artifact_core.py:21,30`).
- Runtime dependencies are `["filelock>=3"]` only, and the `[test]` extra is `pytest`/`pytest-xdist`/`pytest-randomly` (`pyproject.toml:50,68`). D138 permits a justified dependency but the operative rule is DECLARE IT OR DO NOT IMPORT IT; `pyproject.toml`'s own `filelock` comment states "An accidental transitive install is not a dependency".
- The suite is run BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- `other` is not a directory anywhere: `selectors.record_dirs` computes it as the complement of `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` over the records root.
- Two distinct vocabularies exist for different questions and must not be conflated: `LogicalRoot` (4 members) answers "which logical root", `RootClass` (6) answers "which physical placement class". Spec Section 5.1 item 4 forbids collapsing them.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The additive-first shape is correct and is why this plan survived round 1 nearly intact.** Creating `layout.py` standalone changes no existing code and allows full unit validation before any consumer is refactored. | Round 1 review record; this plan's `Scope-Paths` (two new files only). |
| F-2 | **Round 1's vocabulary pinning is accurate, re-verified live at round 2.** `ARTIFACT_TYPES` has 10 members and `RecordClass` 9; their union is 12 names = the eleven modeled classes plus `records`. `_RECORD_CLASS_SUBPATHS['records'] == ''` confirms the carve-out. `EXCLUDED_RECORD_DIRS` is exactly the seven pinned. `_ALIASES` includes `roadmap -> roadmaps` and `misc`/`others -> other`. | Live import at HEAD `90434d47`. |
| F-3 | **The controlling spec is now `approved`, so the round-1 execution gate is cleared** and readiness turns on ordinary plan approval. | `.aw/records/specs/20260901-kw5y2s-01-...spec.md:4`; commit `6db54f8b`. |
| F-4 | **REVIEW FINDING (round 2): E-01's promised surface was incomplete for its own consumers.** `zvk796` E-02 sources `KNOWN_PRIMARY_TYPES` from `layout.py`, and `rodj06` E-01 sources the durable/runtime state classes, but E-01 named none of them. Measured: `KNOWN_PRIMARY_TYPES` is a distinct 9-member set (`ARTIFACT_TYPES` minus `other`), durable = 5 members, runtime = 6. A missing piece would surface in Order 02/03 as an ImportError, after this plan was already marked done. | `selectors.KNOWN_PRIMARY_TYPES`; `record_producers.DurableStateClass`/`RuntimeStateClass`; `zvk796:53`; `rodj06:36`. |
| F-5 | **REVIEW FINDING (round 2): `other` needs a SECOND carve-out, and the plan named only the `records` one.** `record_dirs(repo, "other")` returns `['.aw/records/reviews', '.aw/records/prompt-library']` on this tree and no `.aw/records/other/` exists, because the branch computes the complement of `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS`. Modeling `other` as `subpath: "other"` would silently change traversal in Order 02. | `selectors.record_dirs` `if record_type == "other"` branch; measured output; `ls -d .aw/records/*/`. |
| F-6 | **REVIEW FINDING (round 2): the spec snippet the plan implements is not 3.9-valid.** `requires-python = ">=3.9"` while the snippet annotates dataclass fields as `tuple[str, ...]`/`dict[str, str]`, which are evaluated at class creation and fail on 3.9 without `from __future__ import annotations`. | `pyproject.toml:12`; spec `:358-372`; house pattern in three comparable modules. |
| F-7 | **REVIEW FINDING (round 2): E-02 proposed an UNDECLARED dependency.** `jsonschema` imports on a maintainer machine (4.26.0) but appears in neither the runtime deps nor the `[test]` extra, and nothing in `agent_workflows/` or `tests/` imports it. Relying on it would make CI and a clean install run different code, the exact hole `pyproject.toml`'s `filelock` comment warns about. | `pyproject.toml:50,68`; zero `import jsonschema` matches; live import succeeding only incidentally. |

## Proposed changes (ordered, validatable)

1. Create `agent_workflows/layout.py` (E-01).
2. Create `tests/test_layout.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring existing modules is deferred to Orders 02 & 03.

## Scope check

- Over-scope: none. Both declared paths are new files created by this plan; no existing module is touched, which is what makes Order 01 purely additive.
- Under-scope, CONDITIONAL (round 2, PR-017): if the executor takes the `jsonschema` route for E-02 instead of stdlib structural validation, `pyproject.toml` MUST be added to `Scope-Paths` in the same change, because declaring the dependency is part of that choice. Taking the dependency without declaring it is a FAILED validation, not an out-of-scope edit to be justified later. The stdlib route needs no scope change and is the default.
- Under-scope note: this plan creates the interface Orders 02 and 03 consume. The consumer-surface requirements are now enumerated in E-01 and asserted in E-02/V-01 (PR-015), so a gap fails HERE rather than in a later child.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_layout.py` for per-test names and counts.
- The bare full suite `python3 -m pytest` from the PRIMARY checkout, with the baseline re-measured on unmodified HEAD at execution time (round 1 observed `4004 passed, 3 skipped, 4 xfailed`; treat that as historical). This module is additive, so the only expected delta is the new tests.
- Expect the six pre-existing `check.lifecycle-transition-invalid` diagnostics from `aw check plans`; they are a known tooling defect (backlog `tk1gqo`), not a regression, and must NOT be worked around by reordering this plan's history.

## Spec / documentation sync

- Implements spec `kw5y2s` Sections 4 and 5. The spec is `approved`; do NOT edit it. Its Section 5 snippet is a shape, not copyable source (F-6), and where the snippet and the 3.9 floor conflict, the floor wins.
- No user-facing documentation is owned here. The user-visible surface belongs to `30jug9`.

## Open questions

- none. Round 2 resolved the three decisions this plan needed from repository evidence rather than deferring them: the consumer-interface surface (D-11), the `other` representation (D-12), and the schema-validation dependency (D-13). Each is recorded in the review record with its basis, and each is reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `agent_workflows/layout.py` defines `LayoutModel`, `RecordClassDefinition`, `build_default_layout()`, `to_json()`, and `to_schema()`.
  - PLUS the union-vocabulary proof (PR-001), pasted, not asserted. Run and paste the output of a
    differential check that the model reproduces the live vocabulary with NOTHING dropped, e.g.:
    `python3 -c "from agent_workflows import layout, artifact_types as AT, record_producers as RP, selectors as S; m=layout.build_default_layout(); rc=set(m.record_classes); print('missing_from_model:', sorted((set(AT.ARTIFACT_TYPES)|{r.value for r in RP.RecordClass}) - rc - {'records'})); print('roadmaps_present:', 'roadmaps' in rc); print('excl_equal:', tuple(m.traversal_exclusions)==tuple(S.EXCLUDED_RECORD_DIRS))"`
    Required result: `missing_from_model: []`, `roadmaps_present: True`, `excl_equal: True`.
  - PLUS THE CONSUMER-INTERFACE PROOF (round 2, PR-015), pasted, because a gap here does not fail in this
    plan; it fails in Orders 02/03 as an ImportError or a silent behavior change. Paste, for each: the
    model's primary-type set (or derived rule) equals the live 9-member `selectors.KNOWN_PRIMARY_TYPES`;
    the durable set equals `install, history, actions, migrations, routing_receipts`; the runtime set
    equals `transactions, locks, staging, backups, cache, tmp`; the model represents `other` WITHOUT a
    literal `other` subpath; and the model can express the legacy map's `docs/specs`, `docs/research`,
    `docs/walkthroughs`. State explicitly which representation was chosen for `other` and for
    `KNOWN_PRIMARY_TYPES`, since Order 02 must consume exactly that.
  - PLUS the 3.9 proof (round 2, PR-016): paste the import block showing `from __future__ import
    annotations` with `typing.Tuple`/`Dict` rather than the spec's bare `tuple[...]`/`dict[...]`, and
    confirm the module imports cleanly. If a 3.9 interpreter is unavailable, say so plainly and cite the
    annotation style as the mitigation rather than claiming a run that did not happen.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_layout.py` passes cleanly, with the
    ACTUAL runner output and per-test names pasted (never a claimed pass).
  - PLUS the dependency evidence (round 2, PR-017): paste a grep of the new test file proving it does NOT
    `import jsonschema`, OR, if the dependency route was deliberately taken, paste the `pyproject.toml`
    `[test]` diff that DECLARES it and note that `pyproject.toml` was added to `Scope-Paths`. An
    undeclared import that happens to work on this machine is a FAILED validation, not a pass.
  - PLUS the determinism evidence: paste two serializations from one process shown byte-identical.
  - PLUS the bare full suite `python3 -m pytest` summary line, with the baseline re-measured on unmodified
    HEAD at execution time. This module is additive, so the expected delta is the new tests only; anything
    else must be explained change-by-change.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS CLEARED (round 2): controlling spec `kw5y2s` is now `- Status: approved`, approved `--by-human`, so `ipd-lifecycle.md:16` is satisfied and this plan needs only ordinary human approval. This plan is `reviewed` and has no unresolved blocking questions.

THIS IS ORDER 01, THE FOUNDATION: three of the four later children import what it creates. The dangerous failure is therefore NOT a bug in `layout.py` but an INCOMPLETE INTERFACE that looks finished: if the model omits `KNOWN_PRIMARY_TYPES`, the state-class vocabularies, the `other` complement rule, or the legacy subpath map, this plan validates green and Order 02 or 03 fails at import time or, worse, silently changes traversal (F-4, F-5). V-01's consumer-interface proof exists for exactly that and may not be waived.

Execution contract:

1. Additive only. Do NOT modify `artifact_types.py`, `selectors.py`, `record_producers.py`, or `project_schema.py`; those are Orders 02 and 03. This plan's value is that it changes no existing behavior.
2. Do NOT transcribe the spec's Section 5 snippet literally; it is not valid on the 3.9 floor (F-6). Use `from __future__ import annotations` plus `typing` generics.
3. Do NOT add an undeclared dependency. Either validate structurally with the stdlib, or declare `jsonschema` in the `[test]` extra and add `pyproject.toml` to `Scope-Paths` in the same change (F-7, Scope check).
4. Report validation by pasting the ACTUAL runner output; never claim a test result you did not run.
5. Commit only files this plan changed, path-scoped. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
6. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
7. Scope fence (a DECLARATION so the runner can reconcile afterwards): the declared paths are `agent_workflows/layout.py` and `tests/test_layout.py`, plus `pyproject.toml` only under clause 3. An out-of-scope edit is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`, and a declared-but-unmodified path needs a `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined.
8. Expect the `check.lifecycle-transition-invalid` diagnostic on this plan; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
9. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
