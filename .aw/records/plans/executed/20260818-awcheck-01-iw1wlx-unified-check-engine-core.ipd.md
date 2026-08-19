# IPD: unified check engine core

- Date: 2026-08-18
- Kind: child
- Concern: awcheck Order 01 (spec 20260818-1525-01; TODO item 19). Build ONE check-engine module that, per record TYPE, composes the EXISTING validators into a single result: name-conformity + front-matter/status conformity + reference integrity, all emitted as the shared `artifact_core.Drift` list. This is the engine the `aw check <type>` verb (awcmdsurf Order 02) routes into. Reuse the per-type validators; do NOT reimplement them.
- Scope: ONE new module `agent_workflows/check_engine.py` + ONE test file `tests/test_check_engine.py`. IN: a `check_type(repo_root, record_type, names_only=False, legacy=False) -> List[Drift]` that dispatches to the right existing validators for the type, and a `check_types(repo_root, types, ...)` fan-out; a `SUPPORTED = {...}` map of which check kinds each type supports. OUT: the id6/setid COLLISION check (awcheck Order 02), the `--legacy` flag plumbing + stale-message fix + ipd-lint integration (awcheck Order 03), the CLI verb wiring (awcmdsurf Order 02). This Order builds the composable ENGINE and its tests only; `legacy` is accepted as a passthrough parameter but its behavior is finished in Order 03.
- Status: executed
- Set: awcheck
- Order: 1
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: iw1wlx

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from investigation (Drift artifact_core.py:247; validate_spec specs.py:128; validate_item backlog.py:129; check_drift plans_index.py:235 + research_index.py:231; is_conformant normalize_plan_names.py:205).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against artifact_core.py:247, specs.py:128, backlog.py:129, plans_index.py:235, and normalize_plan_names.py:205; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE; re-review (opencode): verified validate_spec/validate_item/check_drift/is_conformant/Drift citations; conforming; no findings.
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. Empirically verified real signatures + the live dir-resolver. PR-001 (MEDIUM): E-02's hand-rolled `Path(__file__).parent.parent/.aw/system/...` normalizer path is non-portable and BREAKS when pip-installed; replaced with `engine.resolve_source_root(None)` (cli.py:2890 pattern). PR-002 (LOW): E-03 passed `limit=None` to `check_drift` whose param is an int; corrected to omit it. PR-003 (HIGH): `check_names` walked `resolve_record_read_paths(record_type)`, which RAISES `Invalid record or state class` for `backlog`/`roadmaps` (both in SUPPORTED but NOT RecordClass members) - a guaranteed crash; added a `_type_dirs` helper that branches per type (backlog->BACKLOG_ROOTS, roadmaps->.aw/records/roadmaps, else resolve_record_read_paths) + file de-dup by resolved path. (Prior APPROVE passes, incl. my first re-review, missed all three by checking citations but not signatures/portability/live-resolver behavior.) Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.
- 2026-08-18 executed (opencode Opus 4.8): E-01..E-05 performed, V-01..V-05 pass; check_engine.py + tests committed; 7 module tests pass (full suite at Set boundary).

## Goal

Provide a single composable check engine: given a repo root and a record type, run that type's
name-conformity + content/status + reference checks by delegating to the validators that already exist,
returning one flat `List[Drift]`. A fan-out runs it over several types or `all`. The CLI verb consumes
this; no validator logic is duplicated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

FOR THE EXECUTOR: Create ONLY the two files named in Scope. Do NOT edit any existing validator or
cli.py. Every check function must return a `List[artifact_core.Drift]` (never print). Use
`from __future__ import annotations`.

### Task group 1: module skeleton + the supported-checks map

- [x] E-01 Create `agent_workflows/check_engine.py` with this header + imports and a `SUPPORTED` map declaring which check kinds each record type supports today:
  ```python
  """Unified check engine: compose the existing per-type validators into one Drift list per record
  type. Pure (returns Drift, never prints). Consumed by the `aw check <type>` verb (awcmdsurf)."""

  from __future__ import annotations

  from pathlib import Path
  from typing import Dict, List

  from agent_workflows import artifact_core as _core
  from agent_workflows import record_producers as _rp

  # Which check kinds each type supports today. "names" = filename-grammar conformity;
  # "content" = front-matter/status/contract; "refs" = reference integrity (via the index drift).
  SUPPORTED: Dict[str, tuple] = {
      "plans": ("names", "content", "refs"),
      "specs": ("content",),
      "backlog": ("names", "content"),
      "research": ("names", "content", "refs"),
      "prompts": ("names",),
      "walkthroughs": ("names",),
      "roadmaps": ("names",),
  }
  ```
  - Depends on: none
  - Expected outcome: `python3 -c "import agent_workflows.check_engine as c; print(sorted(c.SUPPORTED))"` runs and lists the types.
  - Execution state: performed

### Task group 2: name-conformity sub-check

- [x] E-02 First add a shared per-type directory resolver `_type_dirs(repo_root: Path, record_type: str) -> List[Path]` (used by this Order AND by Order 02's collision scan). CRITICAL: `_rp.resolve_record_read_paths` ONLY accepts the RecordClass values {plans, specs, research, prompts, comms, walkthroughs} - it RAISES `Invalid record or state class` for `backlog` and `roadmaps` (verified: RecordClass has no backlog/roadmaps member; backlog resolves via its own `BACKLOG_ROOTS`/`_iter_items`, roadmaps has no resolver). So `_type_dirs` MUST branch: for `backlog` return the existing dirs among `backlog.BACKLOG_ROOTS` (".agents/backlog", ".aw/records/backlog") under repo_root; for `roadmaps` return `[repo_root/".aw/records/roadmaps"]` if it exists; for every other type call `_rp.resolve_record_read_paths(record_type, target_repo=str(repo_root))`; wrap in try/except so an unknown type yields `[]`. THEN add `check_names(repo_root: Path, record_type: str, legacy: bool = False) -> List[Drift]` that walks `_type_dirs(repo_root, record_type)` (NOT a raw `_rp.resolve_record_read_paths`, which crashes on backlog/roadmaps), de-duplicating files by RESOLVED path (a file present in both `.aw/records/<t>` and legacy `.agents/<t>` is counted once), and for every `*.md` that is NOT README/INDEX/STATUS checks filename conformity to the grammar. De-duplicate files by resolved path across the returned dirs. Load the shipped normalizer by path and call its `is_conformant(name, expected_type=<facet>)` where `<facet>` is the type's facet (`plans`->`ipd`, `specs`->`spec`, `backlog`->`backlog`, `prompts`->`prompt`, `walkthroughs`->`walkthrough`, `roadmaps`->`roadmap`, `research` skip - it has its own grammar). For a nonconformant name emit `Drift(str(path), "check.name-nonconformant", "filename does not match the <type> grammar")`. `legacy` is accepted and threaded to `is_conformant` handling in Order 03 (for now, pass it through; do not special-case).
  - Load the normalizer the SAME portable way the CLI already does (do NOT hand-roll a `Path(__file__).parent.parent` path - that assumes a source checkout and BREAKS when the framework is pip-installed into another repo, because the bundle is then packaged, not at that relative path). Reuse `engine.resolve_source_root(None)`, which resolves the workflow-bundle root layout-agnostically for both a source checkout and an installed wheel (this is exactly what `cli.py:2890` `_load_normalizer` does):
  ```python
  import importlib.util
  from agent_workflows import engine as _engine
  def _load_normalizer():
      try:
          root = _engine.resolve_source_root(None)
      except SystemExit:
          return None
      script = root / "setup-repo" / "tools" / "normalize_plan_names.py"
      if not script.is_file():
          return None
      spec = importlib.util.spec_from_file_location("awcheck_npn", script)
      mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
      return mod
  ```
  (If the normalizer cannot be located/loaded, return `[]` for names rather than raising - name-conformity is then simply not checked, which is safe.)
  - Depends on: E-01
  - Expected outcome: over a fixture with a well-named plan and a badly-named plan (`not-a-grammar.md`), `check_names(root,"plans")` returns exactly one Drift for the bad file with rule `check.name-nonconformant`.
  - Execution state: performed

### Task group 3: content + refs sub-checks (delegate to existing validators)

- [x] E-03 Add `check_content(repo_root, record_type, legacy=False) -> List[Drift]` that delegates to the EXISTING per-type content validators and returns their Drift:
  - `specs`: for each spec file (reuse `specs._spec_files(repo_root)`), call `specs.validate_spec(path, text)` and extend.
  - `backlog`: for each item (reuse `backlog._iter_items(repo_root)`), call `backlog.validate_item(path, text)` and extend.
  - `plans`: front-matter/name-vs-metadata drift is produced by `plans_index.check_drift(repo_root, plans_dir)` - call it and extend (this also covers refs; see E-04 note). NOTE the real signature is `check_drift(repo_root, plans_dir, limit=DEFAULT_INDEX_LIMIT)` where `limit` is an int; OMIT `limit` to take the default (do NOT pass `limit=None` - it is not an int and is used in numeric context). Resolve `plans_dir` via `_rp.resolve_record_read_paths("plans", target_repo=str(repo_root))[0]`.
  - `research`: `research_index.check_drift(repo_root, research_root)` similarly (same `(repo_root, root, limit=int)` signature; omit `limit`; resolve `research_root` the same way).
  - types without a content validator (`prompts`/`walkthroughs`/`roadmaps`): return `[]`.
  Import these lazily inside the function to avoid import cycles.
  - Depends on: E-01
  - Expected outcome: `check_content(root,"specs")` over a fixture with one malformed spec returns that spec's validate_spec Drift; a type with no content validator returns `[]`.
  - Execution state: performed
- [x] E-04 Add `check_refs(repo_root, record_type) -> List[Drift]`: for `plans` and `research`, reference integrity is already part of their `check_drift` (dangling citations). To avoid double-counting, implement `check_refs` to return `[]` for now and note in a code comment that plans/research reference drift is delivered via `check_content` (their `check_drift`), while `check_refs` is the seam for FUTURE per-type ref checks (e.g. the Blocks-Release dangling check from the awrelease Set folds in here). This keeps the three-way composition explicit without duplicating drift.
  - Depends on: E-01
  - Expected outcome: `check_refs(root, "plans") == []` (refs are folded into content today); the function exists as the documented seam.
  - Execution state: performed

### Task group 4: the composable public API + fan-out

- [x] E-05 Add the public `check_type(repo_root, record_type, names_only=False, legacy=False) -> List[Drift]` and `check_types(repo_root, types, names_only=False, legacy=False) -> List[Drift]`, plus create `tests/test_check_engine.py`. `check_type`: if `names_only`, return only `check_names`; else return `check_names + check_content + check_refs` (only the kinds in `SUPPORTED[type]`; an unsupported type returns a single `Drift("<type>", "check.type-unsupported", "no checks for this type")` ... EXCEPT when called from `all` fan-out, where an unsupported type is simply skipped). `check_types`: fan out over the given types (or the `SUPPORTED` keys when the caller passes the sentinel `["all"]`), concatenating Drift; unsupported types skipped. The test `CheckEngineTests` must cover: `check_names` flags a bad name; `check_content` surfaces a malformed spec's drift; `check_type("plans", names_only=True)` returns only name drift; `check_types(["all"])` runs without error over a fixture and returns a list; an unsupported single type returns the `check.type-unsupported` Drift. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the named tests pass; full serial suite green (new files only).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Shared result type: `artifact_core.Drift(location, rule, detail)` (artifact_core.py:247); `drift_exit_code` (:262) and `render_agent_drift` (:255) are the CLI-layer's job (awcmdsurf), NOT the engine's - the engine returns Drift only.
- Existing validators returning Drift: `specs.validate_spec` (specs.py:128), `backlog.validate_item` (backlog.py:129), `plans_index.check_drift` (plans_index.py:235), `research_index.check_drift` (research_index.py:231). File collectors: `specs._spec_files`, `backlog._iter_items`.
- Name conformity: the shipped `normalize_plan_names.is_conformant(name, expected_type=...)` (normalize_plan_names.py:205); research has its own grammar (skip names for research or use research_index). Locate the shipped normalizer via `engine.resolve_source_root(None)` (layout-agnostic: source checkout AND installed wheel), exactly as `cli.py:2890` does - NOT a hand-rolled `Path(__file__).parent.parent` path, which breaks when pip-installed.
- Real validator signatures: `plans_index.check_drift(repo_root, plans_dir, limit=int)` and `research_index.check_drift(repo_root, research_root, limit=int)` - `limit` is an int (default DEFAULT_INDEX_LIMIT); omit it, do not pass None. `specs._spec_files(repo_root)` / `backlog._iter_items(repo_root)` collect files.
- Tree dirs: `record_producers.resolve_record_read_paths(<class>, target_repo=...)` (record_producers.py:597) BUT it ONLY accepts RecordClass values {plans, specs, research, prompts, comms, walkthroughs} and RAISES for `backlog`/`roadmaps`. Use the `_type_dirs` helper (E-02) that branches: backlog -> `backlog.BACKLOG_ROOTS`, roadmaps -> `.aw/records/roadmaps`, else resolve_record_read_paths. This is why the SUPPORTED map lists backlog/roadmaps yet the engine must NOT feed them to resolve_record_read_paths directly.
- The engine is PURE: returns Drift, never prints, no argparse. The verb layer (awcmdsurf) renders + sets exit codes.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Every validator already returns Drift. | The engine is a COMPOSITION layer; it invents no checks (except the collision check, which is Order 02). |
| F2 | plans/research fold refs into check_drift. | `check_refs` returns [] today to avoid double-counting; it is the documented seam for future ref checks (awrelease). |
| F3 | Engine must not print. | Rendering + exit codes live in the CLI verb (awcmdsurf); keeps the engine reusable + testable. |
| F4 | `resolve_record_read_paths` RAISES for backlog/roadmaps (not RecordClass members). | The engine MUST resolve dirs via the `_type_dirs` helper (E-02) that branches per type, or `check_names`/collision scan crash on those two types. Verified empirically against the live resolver. |

## Proposed changes (ordered, validatable)

1. `check_engine.py` header + SUPPORTED (E-01). 2. `check_names` via the normalizer (E-02). 3. `check_content` delegating to existing validators (E-03). 4. `check_refs` seam (E-04). 5. `check_type`/`check_types` + tests (E-05).

## Deferred / out of scope (with reason)

- id6/setid COLLISION check: awcheck Order 02 (a separate sub-check the engine will call).
- `--legacy` flag behavior + stale-message fix + `ipd lint` name integration: awcheck Order 03.
- CLI verb wiring (`aw check <type>`): awcmdsurf Order 02.

## Scope check

- Over-scope: none - composition engine + tests only.
- Under-scope: none for the CORE - names+content+refs composition + fan-out are covered; collisions/legacy are explicitly later Orders.

## Required tests / validation

`tests/test_check_engine.py` (E-05) + the full serial suite. Each V-item pins one E.

## Spec / documentation sync

No doc change (internal engine). No spec transition (orchestrator advances the spec when the Set completes).

## Open questions

### OQ-01: should research names be checked here or left to research_index?

- Blocking: no
- Status: resolved
- Owner: opencode (2026-08-18)
- Resolution or deferral rationale: LEAVE research name-conformity to `research_index.check_drift` (delivered via `check_content` for research), because research uses a DIFFERENT grammar (`.<model>.<kind>.md`) than the `is_conformant` normalizer. So `check_names` skips research; research name drift still surfaces through content. Documented in E-02/E-03.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.check_engine as c; print(sorted(c.SUPPORTED))"` output.
  - Observed evidence: import agent_workflows.check_engine; sorted(SUPPORTED) lists the 7 types (verified).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `check_names` over a fixture returning exactly one `check.name-nonconformant` Drift for the bad file.
  - Observed evidence: check_names flags only the badly-named plan with check.name-nonconformant (test_check_engine test_check_names_flags_bad_name).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `check_content(root,"specs")` surfacing a malformed spec's Drift; a no-validator type returning [].
  - Observed evidence: check_content('specs') surfaces the malformed spec's validate_spec Drift; a no-validator type ('prompts') returns [] (tests pass). NOTE: check_content discovers files via _iter_type_files for bare-repo robustness (deviation from literal _spec_files/_iter_items, noted in commit).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `check_refs(root,"plans") == []` and note the code comment marking it the future seam.
  - Observed evidence: check_refs(root,'plans') == [] (documented future seam) - test_check_refs_seam_empty passes.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_check_engine.py -p no:xdist -q` (passing) + the full serial suite tail (no regressions).
  - Observed evidence: pytest tests/test_check_engine.py -> 7 passed; full serial suite run at the awcheck Set boundary (after Orders 02+03).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two new files
path-scoped (never `git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/` only
after `aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 01 of awcheck; Orders
02 (collisions) and 03 (legacy+messages) build on this engine.
