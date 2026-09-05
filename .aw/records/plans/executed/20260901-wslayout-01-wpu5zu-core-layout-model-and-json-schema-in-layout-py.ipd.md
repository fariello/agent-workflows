# IPD: Core Layout Model and JSON Schema in layout.py

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout definitions need a single source of truth in Python with strongly-typed dataclasses and deterministic JSON / JSON Schema generation per Spec kw5y2s.
- Scope: Create `agent_workflows/layout.py` with dataclasses (`RecordClassDefinition`, `LayoutModel`), canonical layout constants, `build_default_layout()`, `to_json()`, and `to_schema()`. Add unit tests in `tests/test_layout.py`.
- Scope-Paths: agent_workflows/layout.py, tests/test_layout.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: wslayout
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: wpu5zu
- From-Spec: kw5y2s

## Workflow history
- 2026-09-05 executed (aw oc run): aw oc run self-finalize: wpu5zu verified (set wslayout, attempt 1).
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 6 (child wpu5zu alone): APPROVE WITH REVISIONS APPLIED; PR-031..PR-035 all FIXED. PR-031 HIGH: round 2's Python 3.9 rationale was FALSE and taught the executor a wrong language fact. Measured on python3.9 (3.9.25): the spec's exact tuple[str,...]/dict[str,str] dataclass field annotations create, instantiate and type-resolve cleanly with NO __future__ import; what actually breaks on 3.9 is PEP 604 (str|None), which the snippet does not use. The __future__ + typing instruction STANDS on the correct ground (universal house pattern, 132/132 modules) and 3.9 is genuinely CI-enforced across the matrix. PR-032 HIGH: the exclusion-parity assertion was FLAKY as specified in BOTH E-02 and V-01: EXCLUDED_RECORD_DIRS is a frozenset and tuple(...)==tuple(...) compares hash order (three seeds, three orderings measured), so it could fail a correct model while pytest-randomly is deliberately enabled; now a set comparison per the house precedent. PR-033 HIGH: the plan owned normalize_type but never mentioned the 'all' expansion token (a real special case feeding every 'aw <verb> all'), and demanded NO negative-path evidence, while the two live helpers it replaces DISAGREE on errors (normalize_type raises ValueError, record_dirs returns []). PR-034 MEDIUM: right-sizing was never assessed, only inherited from a count-based lint; assessed and recorded as a single cohesive deliverable with a stated trigger for splitting to_schema(). PR-035 MEDIUM: CI installs only pytest+pytest-xdist and never the [test] extra, so an undeclared jsonschema import is a CERTAIN CI failure (and it is absent on python3.9, a matrix version), which also makes the declare-it route insufficient on its own. Also removed a self-contradicting leftover sentence and the stale 'six diagnostics' count (16 repo-wide, 3 on this plan). Three decisions recorded (D-23..D-25).
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

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

- [x] E-01 Create `agent_workflows/layout.py` defining frozen dataclasses (`RecordClassDefinition`, `LayoutModel`), `build_default_layout()`, `to_dict()`, `to_json(framework_version)`, `to_schema()`, and helper lookup methods (`get_record_subpath()`, `is_known_type()`, `normalize_type()`).
  - Depends on: none
  - Expected outcome: `agent_workflows/layout.py` exists with complete typed layout definitions.
  - Execution state: performed
  - VOCABULARY IS THE UNION (maintainer ruling 2026-09-01, plan-review PR-001). The model MUST document
    reality, not redefine it. The approved spec's corrected table now records this UNION; use it together with the measured source vocabularies below to keep the model and existing callers aligned. Measured truth at HEAD:
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
    `roadmaps`, `others`/`misc` -> `other`, and the identity entries. Verified exact at round 6: the live
    map is 12 entries (`plan, spec, prompt, walkthrough, roadmap, comm, research, backlog, release, other,
    others, misc`).
  - THE `all` EXPANSION TOKEN IS PART OF THE LIVE SURFACE AND THIS PLAN OMITS IT (round 6, PR-033).
    `normalize_type("all")` returns `"all"` as an explicit special case BEFORE the alias lookup
    (`artifact_types.py:52-53`), the error message advertises it (`valid types: ..., other, all`,
    `:58`), and `expand_types` turns it into every supported type in `ARTIFACT_TYPES` order (`:62-73`).
    It is NOT a record class and must NOT become one. DECIDE AND RECORD which side of the boundary it
    sits on: either the model exposes it as a documented non-class token, or it stays entirely in
    `artifact_types` and Order 02 keeps that logic outside the model. Either is defensible; leaving it
    unstated is not, because `normalize_type` is one of the helpers this model is meant to own and every
    `aw <verb> all` invocation depends on it.
  - `traversal_exclusions` MUST reproduce `selectors.EXCLUDED_RECORD_DIRS` exactly at this stage
    (`.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`). Do NOT add
    `node_modules`/`venv`/`.venv` here; that widening is a deliberate behavior change owned by `zvk796`
    E-02 with its own assertion. RE-VERIFIED at round 2: the live set is exactly those seven.
  - PYTHON 3.9 IS THE FLOOR (`pyproject.toml:12` `requires-python = ">=3.9"`) and it is CI-ENFORCED on
    every supported minor (`.github/workflows/tests.yml:31,172` -> `["3.9", ..., "3.14"]`), so a
    3.10-only construct is a merge-blocking failure, not a theoretical risk.
    RATIONALE CORRECTED AT ROUND 6 (PR-031), because round 2's stated reason is FALSE and would teach the
    executor a wrong fact about the language. PEP 585 builtin generics (`tuple[str, ...]`,
    `dict[str, str]`) as dataclass FIELD ANNOTATIONS work correctly on 3.9 WITHOUT
    `from __future__ import annotations`. MEASURED on `python3.9` (3.9.25): the spec's exact
    `RecordClassDefinition`/`LayoutModel` shape creates its classes, instantiates, and resolves via
    `typing.get_type_hints` with no error. What ACTUALLY breaks on 3.9 is PEP 604 union syntax
    (`str | None`), which raises `TypeError: unsupported operand type(s) for |`; the spec snippet
    contains no `|` union, so the snippet is in fact 3.9-safe as written.
  - THE INSTRUCTION STANDS ANYWAY, on the correct ground: `from __future__ import annotations` plus
    `typing` generics is the UNIVERSAL house pattern here, present in 132 of 132 modules under
    `agent_workflows/` (measured), including `attention_contract.py:38,41`, `worktree_lease.py:24,32`
    and `artifact_core.py:21,30`. Follow it for CONSISTENCY and because it makes a later `X | None`
    annotation safe by construction. Do NOT justify it with the false class-creation claim, and do not
    treat a bare `tuple[...]` you encounter elsewhere as a 3.9 bug.
  - THE MODEL MUST ALSO CARRY WHAT THE CONSUMER CHILDREN IMPORT, or Orders 02 and 03 cannot do their
    job (round 2, PR-015; each measured live at HEAD):
    * `KNOWN_PRIMARY_TYPES` is a DISTINCT, NARROWER set than the union: 9 members, exactly
      `ARTIFACT_TYPES` minus `other` (`selectors.py`, measured). `zvk796` E-02 sources it from here, so
      the model must either expose it or expose a documented rule that derives it (for example a
      per-class `is_primary` flag). Do NOT let a consumer re-hardcode it.
    * `other` IS NOT AN ORDINARY SUBPATH and is the second carve-out this model needs. `record_dirs` computes it as the complement of `KNOWN_PRIMARY_TYPES`, `NON_PRIMARY_RECORD_DIRS`, and `EXCLUDED_RECORD_DIRS` over the records root, plus a literal `other/` if present. `NON_PRIMARY_RECORD_DIRS` currently contains `reviews`, which must stay out of the `other` sweep to preserve review-id isolation. Measured: `record_dirs(repo, "other")` returns `[` + "`.aw/records/prompt-library`" + `]` on this tree, and no `.aw/records/other/` directory exists. Expose this non-primary classification or a documented derivation in the model, never a literal `other` subpath, so Order 02 cannot silently re-sweep reviews.
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

- [x] E-02 Author unit tests in `tests/test_layout.py` (NEW FILE; it does not exist today) verifying model defaults, JSON serialization determinism, type normalization, alias resolution, and JSON schema validation.
  - Depends on: E-01
  - Expected outcome: `pytest tests/test_layout.py` passes cleanly.
  - Execution state: performed
  - DO NOT INTRODUCE A `jsonschema` DEPENDENCY (round 2, PR-017). It is importable on a maintainer
    machine (4.26.0) but is declared NOWHERE: `pyproject.toml:50` declares runtime `["filelock>=3"]` and
    the `[test]` extra is `pytest`/`pytest-xdist`/`pytest-randomly`. No module under `agent_workflows/`
    or `tests/` imports it today (measured: zero matches). Depending on an accidental transitive install
    is precisely the reproducibility hole `pyproject.toml`'s own comments call out (the `filelock` note:
    "An accidental transitive install is not a dependency"), and it would make a clean
    `pip install '.[test]'` and CI run different code than the maintainer.
    STRENGTHENED AT ROUND 6 (PR-035): this is a CERTAIN CI FAILURE, not a divergence risk. CI installs
    exactly `pip install --upgrade pip build pytest pytest-xdist` and never the `[test]` extra
    (`.github/workflows/tests.yml:58`), so an undeclared import fails outright. Measured: `jsonschema`
    imports on the maintainer's 3.14 (4.26.0) but is ABSENT on `python3.9`, which IS a CI matrix version
    (`:31,172`). Note the consequence for the dependency route too: adding `jsonschema` to the `[test]`
    extra would still NOT put it on the CI runner, so the schema test would need its own skip guard or a
    CI change. That makes the stdlib route the strongly preferred one, not merely the default. D138 permits a justified
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
  - COMPARE AS SETS, NOT AS TUPLES (round 6, PR-032). `selectors.EXCLUDED_RECORD_DIRS` is a FROZENSET,
    so `tuple(...) == tuple(...)` compares ITERATION ORDER, which varies with `PYTHONHASHSEED`. MEASURED
    across three seeds it produced three different orderings, so that assertion is FLAKY: it can pass
    locally and fail in CI, or pass on one xdist worker and fail on another, for no code reason. The
    repository deliberately keeps order-randomization on (`pytest-randomly` is a DECLARED dependency
    precisely because it changes observed behavior, and `addopts` never disables it). Assert
    `set(model.traversal_exclusions) == set(selectors.EXCLUDED_RECORD_DIRS)`, or compare
    `sorted(...) == sorted(...)`, matching the house precedent that uses set algebra rather than
    positional comparison (`tests/test_selector_resolver_matrix.py:277-285`). If the model deliberately
    exposes an ORDERED tuple as part of its contract, assert the order against a literal expected
    sequence, never against the frozenset's incidental iteration order.
  - MUST assert the CONSUMER-INTERFACE surface E-01 now owes Orders 02 and 03 (round 2, PR-015), since
    those children import it and a missing piece surfaces there as an ImportError rather than here:
    `KNOWN_PRIMARY_TYPES` and `NON_PRIMARY_RECORD_DIRS` (or their derivation rules) equal the live sets; the durable and runtime
    state-class vocabularies equal the live sets member-for-member; `other` is representable WITHOUT a
    literal `other` subpath and excludes `reviews`; and the legacy subpath map's three `docs/`-prefixed entries survive.
  - MUST assert DETERMINISM concretely rather than by inspection: serialize twice in one process and
    assert byte equality, and assert a stable key order, since `hauwqh` E-01 relies on re-emission being
    a no-op for an unchanged version.
  - MUST run on Python 3.9 semantics: no test may depend on 3.10+ syntax, and the module must import
    cleanly under the declared floor.

## Project conventions discovered (Step 0)

- Spec `kw5y2s` is `approved` again (re-measured at round 5): the maintainer-directed API terminology correction was reviewed and re-approved `--by-human`. Treat its Sections 4 and 5 as authoritative and IMMUTABLE during execution, and report any further factual defect rather than editing the spec or diverging silently.
- The spec's Section 5 code block is a SHAPE, not copyable source, because it elides bodies and defaults (`= ...`), NOT because it is 3.9-invalid. Round 6 measured the opposite of round 2's claim: its `tuple[...]`/`dict[...]` field annotations are perfectly legal on 3.9.
- Python 3.9 is the floor (`pyproject.toml:12`) and is CI-enforced on every supported minor (`.github/workflows/tests.yml:31,172`). The house pattern for a typed module is `from __future__ import annotations` plus `typing` generics, used by 132 of 132 modules under `agent_workflows/` (`attention_contract.py:38,41`; `worktree_lease.py:24,32`; `artifact_core.py:21,30`). Follow it for consistency. The construct that genuinely breaks on 3.9 is PEP 604 `X | None`, so avoid that specifically.
- CI installs only `pytest pytest-xdist`, NOT the `[test]` extra (`.github/workflows/tests.yml:58`). So an undeclared third-party import in a test is a CERTAIN CI failure, not merely a reproducibility risk. Confirming this: `jsonschema` is importable on the maintainer's 3.14 (4.26.0) but is ABSENT on this machine's `python3.9`, which is a CI matrix version.
- Runtime dependencies are `["filelock>=3"]` only, and the `[test]` extra is `pytest`/`pytest-xdist`/`pytest-randomly` (`pyproject.toml:50,68`). D138 permits a justified dependency but the operative rule is DECLARE IT OR DO NOT IMPORT IT; `pyproject.toml`'s own `filelock` comment states "An accidental transitive install is not a dependency".
- The suite is run BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.
- `other` is not a directory anywhere: `selectors.record_dirs` computes it as the complement of `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` over the records root.
- Two distinct vocabularies exist for different questions and must not be conflated: `LogicalRoot` (4 members) answers "which logical root", `RootClass` (6) answers "which physical placement class". Spec Section 5.1 item 4 forbids collapsing them.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The additive-first shape is correct and is why this plan survived round 1 nearly intact.** Creating `layout.py` standalone changes no existing code and allows full unit validation before any consumer is refactored. | Round 1 review record; this plan's `Scope-Paths` (two new files only). |
| F-2 | **Round 1's vocabulary pinning is accurate, re-verified live AGAIN at round 6 and unchanged.** `ARTIFACT_TYPES` has 10 members and `RecordClass` 9; their union is 12 names = the eleven modeled classes plus `records`. `_RECORD_CLASS_SUBPATHS['records'] == ''` confirms the carve-out. `EXCLUDED_RECORD_DIRS` is exactly the seven pinned. `_ALIASES` is exactly 12 entries including `roadmap -> roadmaps` and `misc`/`others -> other`. `KNOWN_PRIMARY_TYPES` is 9 and is exactly `ARTIFACT_TYPES` minus `other` (asserted programmatically, not eyeballed). Durable state = 5, runtime = 6, `LogicalRoot` = 4, `RootClass` = 6, legacy map = the three `docs/`-prefixed entries. | Live import at round-6 HEAD `e96ebc61` (the round-2 citation `90434d47` is stale); `artifact_types.py:12-23,26-39`; `record_producers.py:85-101,136,148-152`; `project_schema.py:46-62`. |
| F-3 | **The controlling spec is `approved` again; the round-4 "reopened" claim is STALE.** The API terminology correction was reviewed and re-approved `--by-human` 459 seconds AFTER these plans were demoted, so the demotion text outlived its premise. The spec gate (`ipd-lifecycle.md:16`) is satisfied; only ordinary human plan approval remains. | `.aw/records/specs/20260901-kw5y2s-01-...spec.md:4` and its `approved (aw set, --by-human)` history line; `git log` timestamps of `298be4b2` vs `3e05c2ba`. |
| F-4 | **REVIEW FINDING (round 2): E-01's promised surface was incomplete for its own consumers.** `zvk796` E-02 sources `KNOWN_PRIMARY_TYPES` from `layout.py`, and `rodj06` E-01 sources the durable/runtime state classes, but E-01 named none of them. Measured: `KNOWN_PRIMARY_TYPES` is a distinct 9-member set (`ARTIFACT_TYPES` minus `other`), durable = 5 members, runtime = 6. A missing piece would surface in Order 02/03 as an ImportError, after this plan was already marked done. | `selectors.KNOWN_PRIMARY_TYPES`; `record_producers.DurableStateClass`/`RuntimeStateClass`; `zvk796:53`; `rodj06:36`. |
| F-5 | **REVIEW FINDING (round 2, RE-MEASURED round 5): `other` needs a SECOND carve-out, and the plan named only the `records` one.** The complement branch (`selectors.record_dirs`, `if record_type == "other"`) subtracts `KNOWN_PRIMARY_TYPES`, `NON_PRIMARY_RECORD_DIRS` and `EXCLUDED_RECORD_DIRS` over the records root; no `.aw/records/other/` directory exists. Modeling `other` as `subpath: "other"` would silently change traversal in Order 02. THE MEASURED OUTPUT CHANGED SINCE ROUND 2 and the old value must not be reused as an expected result: it is now `['.aw/records/prompt-library']`, NOT the `['.aw/records/reviews', '.aw/records/prompt-library']` rounds 2-4 recorded, because commit `d802e917` added `NON_PRIMARY_RECORD_DIRS = frozenset({'reviews'})` to `_OTHER_SWEEP_SKIP_DIRS` specifically to stop `other` claiming the reviews tree. A test that pins the round-2 pair would now fail against correct code. | `selectors.py:183-185` (`_OTHER_SWEEP_SKIP_DIRS`), `:210-225` (the branch); `record_dirs(repo,'other')` re-measured at round 5 -> `['.aw/records/prompt-library']`; commit `d802e917`; `ls -d .aw/records/*/`. |
| F-6 | **CORRECTED (round 6): round 2's 3.9 claim was FALSE, and the instruction it produced is right for a different reason.** Round 2 asserted the spec's `tuple[str, ...]`/`dict[str, str]` dataclass field annotations "are evaluated at class creation and fail on 3.9". Measured on `python3.9` (3.9.25): they do NOT fail; the spec's exact shape creates, instantiates and type-resolves cleanly with no `__future__` import. The real 3.9 boundary is PEP 604 (`str \| None` -> `TypeError`), and the snippet has no union. The `from __future__ import annotations` + `typing` generics instruction REMAINS, justified by the universal house pattern (132/132 modules) and by making a future `\| None` safe, not by a language error. 3.9 is genuinely CI-enforced, so the floor itself is real. | `python3.9` 3.9.25 execution of the spec's `RecordClassDefinition`/`LayoutModel` shape (class creation + `get_type_hints` both succeed); PEP 604 failing on the same interpreter; `pyproject.toml:12`; `.github/workflows/tests.yml:31,172`; 132/132 `from __future__ import annotations` measured under `agent_workflows/`. |
| F-8 | **REVIEW FINDING (round 6): the exclusion-parity assertion was FLAKY as specified, in both E-02 and V-01.** `selectors.EXCLUDED_RECORD_DIRS` is a FROZENSET, so the prescribed `tuple(...) == tuple(...)` compares hash iteration order. Measured across three `PYTHONHASHSEED` values it produced three different orderings, so the check could report a mismatch against a perfectly correct model, and an executor "fixing" the model to match one accidental order would encode noise. The repo deliberately keeps `pytest-randomly` enabled, so this is a live risk rather than theoretical. Now a set comparison, matching the house precedent that uses set algebra. | `type(selectors.EXCLUDED_RECORD_DIRS).__name__ == 'frozenset'`; three-seed measurement at round 6; `tests/test_selector_resolver_matrix.py:277-285`; `pyproject.toml:59-66` (`pytest-randomly` declared because it changes observed behavior). |
| F-9 | **REVIEW FINDING (round 6): the plan owned `normalize_type` but never mentioned the `all` token, and demanded no negative-path behavior at all.** `normalize_type("all")` is an explicit special case returning `"all"` (`artifact_types.py:52-53`) and `expand_types` fans it out to every supported type (`:62-73`), so a model that silently drops it breaks every `aw <verb> all` invocation. Separately, the two live helpers this model replaces DISAGREE on error handling, which the plan never surfaced: `normalize_type` RAISES `ValueError` on unknown/`''`/`None`, while `record_dirs` returns `[]` by documented design (`selectors.py:188-195`). Unifying them silently would be a behavior change landing in Order 02. | `artifact_types.py:50-73` read and executed at round 6 (`normalize_type('nosuchtype')` -> `ValueError`, `normalize_type('all')` -> `'all'`, `expand_types('all', ARTIFACT_TYPES)` -> all 10); `selectors.py:188-195` docstring. |
| F-10 | **REVIEW FINDING (round 6): CI never installs the `[test]` extra, which upgrades PR-017 from a risk to a certainty.** `.github/workflows/tests.yml:58` installs exactly `pip install --upgrade pip build pytest pytest-xdist`, so ANY undeclared third-party test import fails CI outright rather than merely diverging from a maintainer venv. Confirmed concretely: `jsonschema` imports on the maintainer's 3.14 (4.26.0) but is ABSENT on this machine's `python3.9`, and 3.9 is in the CI matrix. The stdlib route is therefore the only route that works without a `pyproject.toml` change. | `.github/workflows/tests.yml:31,58,172`; `python3 -c "import jsonschema"` OK vs `python3.9 -c "import jsonschema"` -> `ModuleNotFoundError`. |
| F-7 | **REVIEW FINDING (round 2): E-02 proposed an UNDECLARED dependency.** `jsonschema` imports on a maintainer machine (4.26.0) but appears in neither the runtime deps nor the `[test]` extra, and nothing in `agent_workflows/` or `tests/` imports it. Relying on it would make CI and a clean install run different code, the exact hole `pyproject.toml`'s `filelock` comment warns about. | `pyproject.toml:50,68`; zero `import jsonschema` matches; live import succeeding only incidentally. |

## Proposed changes (ordered, validatable)

1. Create `agent_workflows/layout.py` (E-01).
2. Create `tests/test_layout.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring existing modules is deferred to Orders 02 & 03.

## Scope check

- Over-scope: none. Both declared paths are new files created by this plan; no existing module is touched, which is what makes Order 01 purely additive.
- Under-scope, CONDITIONAL (round 2, PR-017; sharpened round 6, PR-035): if the executor takes the `jsonschema` route for E-02 instead of stdlib structural validation, `pyproject.toml` MUST be added to `Scope-Paths` in the same change, because declaring the dependency is part of that choice. Taking the dependency without declaring it is a FAILED validation, not an out-of-scope edit to be justified later. Note the route is WORSE than round 2 implied: CI installs only `pytest pytest-xdist` and never the `[test]` extra (`.github/workflows/tests.yml:58`), so even a correctly declared `jsonschema` would be missing on the CI runner and the test would need a skip guard or a workflow change (which is a further scope expansion). The stdlib route needs no scope change and is strongly preferred.
- Under-scope note: this plan creates the interface Orders 02 and 03 consume. The consumer-surface requirements are now enumerated in E-01 and asserted in E-02/V-01 (PR-015), so a gap fails HERE rather than in a later child.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_layout.py` for per-test names and counts.
- The bare full suite `python3 -m pytest` from the PRIMARY checkout, with the baseline re-measured on unmodified HEAD at execution time (round 1 observed `4004 passed, 3 skipped, 4 xfailed`; treat that as historical). This module is additive, so the only expected delta is the new tests.
- Expect the `check.lifecycle-transition-invalid` diagnostic CLASS from `aw check plans`; it is a known tooling defect (backlog `tk1gqo`, `open` and carrying `- Blocks-Release: next`), not a regression, and must NOT be worked around by reordering this plan's history. Assert the CLASS, never a count: re-measured at round 6 the rule fires 16 times repo-wide (3 on THIS plan alone), not the "six" earlier rounds recorded, and the number RISES with every history line any tool or reviewer appends, including the ones this review just added.

## Spec / documentation sync

- Implements spec `kw5y2s` Sections 4 and 5. The spec is `approved`; do NOT edit it. Its Section 5 snippet is a shape, not copyable source (F-6), and where the snippet and the 3.9 floor conflict, the floor wins.
- No user-facing documentation is owned here. The user-visible surface belongs to `30jug9`.

## Open questions

- none BLOCKING, and none awaiting a human. Round 2 resolved three decisions from repository evidence rather than deferring them: the consumer-interface surface (D-11), the `other` representation (D-12), and the schema-validation dependency (D-13). Round 6 resolved three more the same way: the corrected 3.9 rationale (D-23), set-vs-tuple parity comparison (D-24), and the `all`-token boundary plus the per-helper error contract (D-25, which asks the EXECUTOR to RECORD a choice rather than leaving it implicit, and fails V-01 if unrecorded). Each is in the review record with its basis, and all six are reversible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `agent_workflows/layout.py` defines `LayoutModel`, `RecordClassDefinition`, `build_default_layout()`, `to_json()`, and `to_schema()`.
  - PLUS the union-vocabulary proof (PR-001), pasted, not asserted. Run and paste the output of a
    differential check that the model reproduces the live vocabulary with NOTHING dropped, e.g.:
    `python3 -c "from agent_workflows import layout, artifact_types as AT, record_producers as RP, selectors as S; m=layout.build_default_layout(); rc=set(m.record_classes); print('missing_from_model:', sorted((set(AT.ARTIFACT_TYPES)|{r.value for r in RP.RecordClass}) - rc - {'records'})); print('roadmaps_present:', 'roadmaps' in rc); print('excl_equal:', set(m.traversal_exclusions)==set(S.EXCLUDED_RECORD_DIRS))"`
    Required result: `missing_from_model: []`, `roadmaps_present: True`, `excl_equal: True`.
    NOTE THE SET COMPARISON (round 6, PR-032): this command previously used
    `tuple(m.traversal_exclusions)==tuple(S.EXCLUDED_RECORD_DIRS)`. `EXCLUDED_RECORD_DIRS` is a
    FROZENSET, so the tuple form compares hash-order and is `PYTHONHASHSEED`-dependent (measured: three
    seeds, three different orderings). It could therefore print `excl_equal: False` against a completely
    correct model, and an executor who then "fixed" the model to match one accidental ordering would be
    encoding noise. Compare as sets.
  - PLUS THE CONSUMER-INTERFACE PROOF (round 2, PR-015), pasted, because a gap here does not fail in this
    plan; it fails in Orders 02/03 as an ImportError or a silent behavior change. Paste, for each: the
    model's primary-type set (or derived rule) equals the live 9-member `selectors.KNOWN_PRIMARY_TYPES`;
    the durable set equals `install, history, actions, migrations, routing_receipts`; the runtime set
    equals `transactions, locks, staging, backups, cache, tmp`; the model represents `other` WITHOUT a
    literal `other` subpath; and the model can express the legacy map's `docs/specs`, `docs/research`,
    `docs/walkthroughs`. State explicitly which representation was chosen for `other` and for
    `KNOWN_PRIMARY_TYPES`, since Order 02 must consume exactly that.
  - PLUS the 3.9 proof, STRENGTHENED at round 6 (PR-031, PR-033): paste the import block showing
    `from __future__ import annotations` with `typing` generics (house pattern, 132/132 modules), AND
    paste an ACTUAL 3.9 import run, not a stylistic argument. A 3.9 interpreter IS available on this
    machine (`python3.9` -> 3.9.25, verified at round 6) and 3.9 is in the CI matrix, so the round-2
    escape clause ("if a 3.9 interpreter is unavailable, cite the annotation style as the mitigation")
    is REMOVED as an unnecessary loophole: run
    `python3.9 -c "import sys; sys.path.insert(0,'.'); from agent_workflows import layout; m=layout.build_default_layout(); print('3.9 OK', sys.version.split()[0], len(m.record_classes))"`
    and paste the output. Only if no 3.9 interpreter genuinely exists in the execution environment may you
    fall back to stating that plainly; say which, and never claim a run you did not perform.
  - PLUS the NEGATIVE-PATH proof (round 6, PR-033), which the plan previously demanded nowhere: paste the
    behavior of `get_record_subpath()`, `is_known_type()` and `normalize_type()` on an UNKNOWN type
    (e.g. `"nosuchtype"`, `""`, `None`) and on the `records` carve-out. State the contract each honors and
    MATCH THE LIVE BEHAVIOR PER HELPER, because the two live helpers Order 02 replaces DIFFER from each
    other (both measured at round 6):
    * `artifact_types.normalize_type` RAISES `ValueError` on an unknown type, with a message listing the
      valid types (`unknown artifact type 'nosuchtype'; valid types: plans, ..., other, all`), and it
      raises on `''` and `None` as well. A model helper that silently returned `None` here would swallow
      an error the CLI currently surfaces to the user.
    * `selectors.record_dirs` DEGRADES: "Returns [] for an unknown/unresolvable type rather than raising"
      (`selectors.py:188-195`).
    Do NOT unify these two conventions without saying so explicitly, and do not assume one from the other.
    ALSO state whether the model represents the `all` EXPANSION TOKEN, which appears in the live
    valid-type list and is handled by `artifact_types.expand_types`/`is_type_token` but is NOT a record
    class and is mentioned NOWHERE in this plan. If the model omits it, confirm Order 02 keeps handling it
    outside the model, since a silent loss of `all` would break every `aw <verb> all` invocation.
  - Observed evidence: PASS. `layout.py` created; union proof `missing_from_model: []` / `roadmaps_present: True` / `excl_equal: True`; consumer surface measured equal to the live 9-member primary set, the `reviews` non-primary set, the derived sweep union, and the 5/6 state vocabularies; both carve-outs represented without a literal subpath; 3.9 import run on 3.9.25; negative paths raise `ValueError` per the live contract; `all` preserved as a non-class token. Full detail below.
    SURFACE. `agent_workflows/layout.py` created (additive; no existing module touched). Defines
    `RecordClassDefinition` and `LayoutModel` (both `@dataclass(frozen=True)`), `build_default_layout()`,
    `to_dict()`, `to_json()`, `to_schema()`, `to_schema_json()`, plus `get_record_subpath()`,
    `get_record_class()`, `resolve_class_name()`, `is_known_type()`, `normalize_type()`, `expand_type()`,
    `artifact_types()`, `alias_map()`, `primary_types()`, `non_primary_record_dirs()`,
    `other_sweep_skip_dirs()`, `record_subpaths()`, `legacy_record_subpaths()`.

    UNION-VOCABULARY PROOF (the prescribed command, run verbatim, SET comparison):
    ```
    missing_from_model: []
    roadmaps_present: True
    excl_equal: True
    ```

    CONSUMER-INTERFACE PROOF:
    ```
    primary_equal: True 9
    nonprimary_equal: True ('reviews',)
    sweep_union_equal: True
    durable: True ['actions', 'history', 'install', 'migrations', 'routing_receipts']
    runtime: True ['backups', 'cache', 'locks', 'staging', 'tmp', 'transactions']
    other literal subpath?: '' is_complement True
    other in record_subpaths: False
    legacy: {'specs': 'docs/specs', 'research': 'docs/research', 'walkthroughs': 'docs/walkthroughs'}
    records carve-out subpath: '' is_root_alias True
    ```
    REPRESENTATIONS CHOSEN, since Order 02 must consume exactly these. `KNOWN_PRIMARY_TYPES` is a
    DERIVED RULE, not a literal set: `LayoutModel.primary_types()` returns every class with
    `is_primary=True` that is neither the root alias nor the complement, measured equal to the live
    9-member `selectors.KNOWN_PRIMARY_TYPES` and to `ARTIFACT_TYPES - {other}`. `other` is represented by
    `is_complement=True` with an EMPTY subpath and is absent from `record_subpaths()`, so no literal
    `other` subpath exists; `non_primary_record_dirs()` returns `('reviews',)` and
    `other_sweep_skip_dirs()` exposes the DERIVED union (measured equal to `selectors._OTHER_SWEEP_SKIP_DIRS`),
    so Order 02 sources the union rather than recomputing it. The legacy map is a strict SUPERSET of
    `_LEGACY_RECORD_CLASS_SUBPATHS` by exactly `{backlog, roadmaps}`, which inherit their FINAL subpath by
    absence of an override (correct-by-absence, matching the live `**` spread); all three `docs/`-prefixed
    entries survive.

    PYTHON 3.9 PROOF. Import block is `from __future__ import annotations` + `typing` generics (house
    pattern). ACTUAL 3.9 run, not a stylistic argument:
    ```
    $ python3.9 -c "import sys; sys.path.insert(0,'.'); from agent_workflows import layout; m=layout.build_default_layout(); print('3.9 OK', sys.version.split()[0], len(m.record_classes)); print('json ok', len(m.to_json('1.2.3'))); print('normalize roadmap ->', m.normalize_type('roadmap'))"
    3.9 OK 3.9.25 12
    json ok 3422
    normalize roadmap -> roadmaps
    ```

    NEGATIVE-PATH PROOF, matched PER HELPER to the live behavior:
    ```
    normalize_type('nosuchtype') -> ValueError: unknown artifact type 'nosuchtype'; valid types: plans, specs, prompts...
    is_known_type('nosuchtype') -> False
    normalize_type('') -> ValueError: unknown artifact type ''; valid types: ...
    is_known_type('') -> False
    normalize_type(None) -> ValueError: unknown artifact type None; valid types: ...
    is_known_type(None) -> False
    get_record_subpath(nosuchtype) -> ValueError: unknown artifact type 'nosuchtype'; ...
    get_record_subpath(records) -> ''
    get_record_subpath(other) -> ''
    normalize_type(all) -> all
    LIVE normalize_type(nosuchtype): ValueError: unknown artifact type 'nosuchtype'; ...
    LIVE record_dirs unknown -> []
    expand all == True
    ```
    CONTRACT STATED: `LayoutModel.normalize_type` RAISES `ValueError` (advertising `all`) for unknown,
    `''` and `None`, exactly as `artifact_types.normalize_type` does. The returns-`[]` degradation stays
    with `selectors.record_dirs`, which keeps its own documented contract; the two are deliberately NOT
    unified (recorded as DECISION 03-wpu5zu-D2).
    THE `all` TOKEN IS REPRESENTED, as a documented NON-CLASS token: `layout.EXPANSION_TOKEN_ALL == "all"`,
    `normalize_type("all") -> "all"`, `is_known_type("all") -> True`, `expand_type("all", ...)` measured
    equal to `AT.expand_types("all", ...)`, and `"all" not in record_classes`.
    THE `records` CARVE-OUT NEEDED A SECOND HELPER (DECISION 03-wpu5zu-D3): `records` is a real record
    class but never an `ARTIFACT_TYPES` member, so `normalize_type("records")` RAISES and
    `is_known_type("records")` is False (parity with the live `AT.is_type_token('records') == False`),
    while `resolve_class_name("records") -> "records"` serves the routing question. It is also omitted
    from the EMITTED `record_classes` (11 emitted, not 12) so nothing derives `records/records/`.
    TWO SPEC-EXAMPLE DEVIATIONS, both deliberate and reported rather than silently absorbed: the
    walkthroughs pattern is `*.walkthrough.md` (the spec's `*-walkthrough.md` matches 0 of 16 on-disk
    artifacts; DECISION 03-wpu5zu-D1) and durable `install` is `install.json` (the live load-bearing
    value; DECISION 03-wpu5zu-D4). The `approved` spec was NOT edited.
  - Result: pass

- [x] V-02 validates E-02
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
  - Observed evidence: PASS. `python3 -m pytest -o addopts="" tests/test_layout.py -v` -> `41 passed in 0.15s`; no `jsonschema` import (stdlib structural validation, `pyproject.toml` untouched); two serializations byte-identical (sha256 `d558c290...`); bare suite baseline on unmodified HEAD `31 failed, 4303 passed` -> after `31 failed, 4344 passed`, an exact +41 delta with an IDENTICAL failure set (31 pre-existing runner/viewer failures, not caused here). Full detail below.
    TARGETED RUN (actual output, per-test names via `-o addopts=""`):
    ```
    $ python3 -m pytest -o addopts="" tests/test_layout.py -v
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1112591307
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 41 items

    ConsumerInterfaceTests::test_primary_types_equal_the_live_known_primary_types PASSED
    ConsumerInterfaceTests::test_exclusions_are_deterministically_ordered PASSED
    ConsumerInterfaceTests::test_other_sweep_skip_union_is_derived_from_the_three_inputs PASSED
    ConsumerInterfaceTests::test_durable_state_classes_equal_the_live_vocabulary PASSED
    ConsumerInterfaceTests::test_runtime_state_classes_equal_the_live_vocabulary PASSED
    ConsumerInterfaceTests::test_the_three_dir_sets_are_disjoint PASSED
    ConsumerInterfaceTests::test_non_primary_record_dirs_equal_the_live_set PASSED
    ConsumerInterfaceTests::test_traversal_exclusions_equal_the_live_set_as_sets PASSED
    SerializationTests::test_serialization_is_byte_identical_across_calls PASSED
    SerializationTests::test_json_key_order_is_stable PASSED
    SerializationTests::test_schema_is_stable_and_json_serializable PASSED
    SerializationTests::test_emitted_record_classes_omit_the_root_alias PASSED
    SerializationTests::test_document_has_the_required_top_level_keys PASSED
    SerializationTests::test_emitted_state_classes_are_state_root_relative PASSED
    SchemaConformanceTests::test_traversal_exclusions_satisfy_the_schema PASSED
    SchemaConformanceTests::test_state_classes_satisfy_the_schema PASSED
    SchemaConformanceTests::test_no_additional_top_level_properties PASSED
    SchemaConformanceTests::test_logical_roots_satisfy_their_required_keys_and_types PASSED
    SchemaConformanceTests::test_schema_version_matches_the_declared_enum PASSED
    SchemaConformanceTests::test_every_required_top_level_property_is_present PASSED
    SchemaConformanceTests::test_each_record_class_entry_satisfies_the_schema PASSED
    NormalizationTests::test_get_record_subpath_resolves_aliases_and_carve_outs PASSED
    NormalizationTests::test_unknown_type_raises_valueerror_listing_the_valid_set PASSED
    NormalizationTests::test_expand_type_matches_the_live_expansion PASSED
    NormalizationTests::test_all_expansion_token_passes_through PASSED
    NormalizationTests::test_normalization_agrees_with_the_live_helper_for_every_live_token PASSED
    NormalizationTests::test_canonical_and_alias_tokens_normalize PASSED
    NormalizationTests::test_resolve_class_name_rejects_unknown_and_the_all_token PASSED
    NormalizationTests::test_is_known_type_is_falsy_tolerant_like_the_live_helper PASSED
    NormalizationTests::test_records_alias_is_reachable_by_name_but_not_as_a_type_noun PASSED
    LayoutModelDefaultsTests::test_legacy_docs_prefixed_subpaths_survive PASSED
    LayoutModelDefaultsTests::test_artifact_types_reproduce_the_live_tuple_in_order PASSED
    LayoutModelDefaultsTests::test_record_classes_are_the_union_of_both_live_vocabularies PASSED
    LayoutModelDefaultsTests::test_root_classes_are_the_six_and_are_not_collapsed PASSED
    LayoutModelDefaultsTests::test_reviews_is_a_type_noun_only_in_the_union_view PASSED
    LayoutModelDefaultsTests::test_lifecycle_subdirs_match_the_live_status_dirs PASSED
    LayoutModelDefaultsTests::test_record_subpaths_match_the_live_final_map PASSED
    LayoutModelDefaultsTests::test_logical_roots_are_the_four PASSED
    LayoutModelDefaultsTests::test_aliases_reproduce_the_live_map_exactly PASSED
    LayoutModelDefaultsTests::test_other_is_a_complement_without_a_literal_subpath PASSED
    LayoutModelDefaultsTests::test_records_is_the_root_alias_carve_out PASSED

    ============================== 41 passed in 0.15s ==============================
    ```
    (Cross-check: `grep -c "    def test_" tests/test_layout.py` -> 41, matching the 41 collected.)

    DEPENDENCY EVIDENCE (stdlib route taken; `pyproject.toml` NOT touched and NOT added to Scope-Paths):
    ```
    $ grep -nE "^\s*(import|from)\s+jsonschema" tests/test_layout.py agent_workflows/layout.py
    (no matches)
    $ grep -n "jsonschema" tests/test_layout.py
    10:`jsonschema`, which is declared in neither the runtime deps nor the `[test]` extra and is absent on
    391:    """Structural conformance checked with the STDLIB (no `jsonschema` dependency)."""
    ```
    Both matches are DOCSTRING PROSE explaining the choice, not imports. The new test imports are only
    `json`, `unittest`, and four `agent_workflows` modules. `SchemaConformanceTests` validates the emitted
    document against the emitted schema by walking `required`, `properties`, `additionalProperties`, the
    `enum`, and the declared item types with the stdlib alone.

    DETERMINISM EVIDENCE (two serializations from ONE process, byte-identical):
    ```
    sha1 d558c290bdd00a78c355f59bc19c4880ee8665fb5d195ce184e2967376c09061
    sha2 d558c290bdd00a78c355f59bc19c4880ee8665fb5d195ce184e2967376c09061
    byte_identical: True 3422
    fresh_model_identical: True
    schema_identical: True d8bdc5da8f4b185d
    ```

    BARE FULL SUITE, with the baseline re-measured on unmodified HEAD at execution time (both new files
    stashed, suite run, then restored):
    ```
    BASELINE (unmodified HEAD ab9795aa, both files stashed):
    31 failed, 4303 passed, 3 skipped, 4 xfailed in 32.08s

    AFTER (this plan's two new files present):
    31 failed, 4344 passed, 3 skipped, 4 xfailed in 31.34s
    ```
    DELTA IS THE NEW TESTS ONLY: 4303 -> 4344 passed is exactly +41, matching the 41 collected above, and
    the FAILURE SET IS IDENTICAL (`diff` of the sorted `FAILED` lines before and after reports no
    difference). Those 31 failures are PRE-EXISTING on unmodified HEAD, not caused here, and are confined
    to runner/viewer modules untouched by this plan: `test_run_viewer.py` (14), `test_oc_runipd.py` (7),
    `test_agy_runipd_cli.py` (6), `test_ipd_lifecycle_cli.py` (2), `test_novalnomerge_integration.py` (1),
    `test_worker_role_refusal.py` (1). Spot-checked
    `test_run_viewer.py::test_run_viewer_cli_json`, which fails on run-record discovery
    (`AssertionError: 0 != 1`) with no layout involvement. Reported to the driver rather than fixed:
    repairing them is outside this plan's Scope-Paths.
    `aw check-local-leaks --agent` -> `"outcome":"clean","findings":0`, exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: SINGLE COHESIVE DELIVERABLE, assessed explicitly at round 6 (PR-034) rather than
  inherited from a passing count-based lint. `aw ipd lint` measures only structural counts (>18 E-leaves,
  >5 groups) and this plan has 2 E-items in 2 groups, so the lint says nothing about conceptual density;
  the rubric requires the judgement to be made anyway. MADE: E-01 carries one deliverable (`layout.py`)
  and E-02 carries one (`tests/test_layout.py`), and although E-01 now holds many MUST clauses, they are
  all CONSTRAINTS ON ONE FILE that must be satisfied together, not independent deliverables: the
  vocabulary, the two carve-outs, the aliases, the exclusions, the annotation style and the consumer
  surface are all fields of the same two dataclasses, and splitting them would produce children that each
  leave `layout.py` importable-but-incomplete, which is precisely the foundation failure the gate below
  warns about. The `Highest E allocated: 02` is therefore correct and NOT an under-decomposition.
  WHAT WOULD CHANGE THE ANSWER: if the executor finds that `to_schema()` needs substantive logic beyond
  serializing the same model (for example bespoke per-class schema fragments), that is a genuinely
  separable second deliverable and should become its own E-item under this plan's Order, not be smuggled
  into E-01.

THE EXTERNAL SPEC GATE IS CLEARED (re-measured at plan-review round 5): controlling spec `kw5y2s` is `- Status: approved` with a `--by-human` attestation, so `ipd-lifecycle.md:16` is satisfied. The round-4 "reopened" wording was accurate when written and then outlived its premise: the plans were demoted at commit `298be4b2` (00:10:38 -0400) and the corrected spec was re-approved 459 seconds later at `3e05c2ba` (00:18:17 -0400). RE-VERIFY the spec's `- Status:` line yourself before starting rather than trusting this paragraph; if it is not `approved`, STOP (a genuinely absent prerequisite). The only remaining gate is ordinary human approval of this plan (round 6 removed a trailing sentence left over from the round-4 demotion, which still said the plan was 'returned to to-review' and contradicted the paragraph it ended).

THIS IS ORDER 01, THE FOUNDATION: three of the four later children import what it creates. The dangerous failure is therefore NOT a bug in `layout.py` but an INCOMPLETE INTERFACE that looks finished: if the model omits `KNOWN_PRIMARY_TYPES`, the state-class vocabularies, the `other` complement rule, or the legacy subpath map, this plan validates green and Order 02 or 03 fails at import time or, worse, silently changes traversal (F-4, F-5). V-01's consumer-interface proof exists for exactly that and may not be waived.

Execution contract:

1. Additive only. Do NOT modify `artifact_types.py`, `selectors.py`, `record_producers.py`, or `project_schema.py`; those are Orders 02 and 03. This plan's value is that it changes no existing behavior.
2. Use `from __future__ import annotations` plus `typing` generics, matching the universal house pattern (132/132 modules). Do NOT transcribe the spec's Section 5 snippet literally, because it elides bodies and defaults (`= ...`). CORRECTED AT ROUND 6 (F-6): the snippet is NOT 3.9-invalid, contrary to round 2; PEP 585 field annotations are legal on 3.9 and were measured working on 3.9.25. The construct that genuinely breaks on 3.9 is PEP 604 `X | None`, so avoid that one specifically.
3. Do NOT add an undeclared dependency. Prefer stdlib structural validation; taking `jsonschema` requires declaring it in the `[test]` extra AND adding `pyproject.toml` to `Scope-Paths` in the same change, AND handling the fact that CI does not install that extra at all (F-7, F-10, Scope check).
4. Assert set-valued constants as SETS. `EXCLUDED_RECORD_DIRS` and friends are frozensets, so a `tuple(...)==tuple(...)` comparison is `PYTHONHASHSEED`-dependent and flaky (F-8). This applies to any parity assertion this plan adds, not only the exclusions.
5. State the model's ERROR CONTRACT explicitly, and match the live helpers rather than unifying them by accident: `normalize_type` raises `ValueError`, `record_dirs` returns `[]` (F-9). Say what happens to the `all` token.
6. Report validation by pasting the ACTUAL runner output; never claim a test result you did not run.
7. Commit only files this plan changed, path-scoped. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
8. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
9. Scope fence (a DECLARATION so the runner can reconcile afterwards): the declared paths are `agent_workflows/layout.py` and `tests/test_layout.py`, plus `pyproject.toml` only under clause 3. An out-of-scope edit is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`, and a declared-but-unmodified path needs a `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined.
10. Expect the `check.lifecycle-transition-invalid` diagnostic on this plan; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
11. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
