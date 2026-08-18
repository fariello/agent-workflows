# IPD: unified check engine core

- Date: 2026-08-18
- Kind: child
- Concern: awcheck Order 01 (spec 20260818-1525-01; TODO item 19). Build ONE check-engine module that, per record TYPE, composes the EXISTING validators into a single result: name-conformity + front-matter/status conformity + reference integrity, all emitted as the shared `artifact_core.Drift` list. This is the engine the `aw check <type>` verb (awcmdsurf Order 02) routes into. Reuse the per-type validators; do NOT reimplement them.
- Scope: ONE new module `agent_workflows/check_engine.py` + ONE test file `tests/test_check_engine.py`. IN: a `check_type(repo_root, record_type, names_only=False, legacy=False) -> List[Drift]` that dispatches to the right existing validators for the type, and a `check_types(repo_root, types, ...)` fan-out; a `SUPPORTED = {...}` map of which check kinds each type supports. OUT: the id6/setid COLLISION check (awcheck Order 02), the `--legacy` flag plumbing + stale-message fix + ipd-lint integration (awcheck Order 03), the CLI verb wiring (awcmdsurf Order 02). This Order builds the composable ENGINE and its tests only; `legacy` is accepted as a passthrough parameter but its behavior is finished in Order 03.
- Status: reviewed
- Set: awcheck
- Order: 1
- Highest E allocated: 05
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: iw1wlx

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): Medium-grade from investigation (Drift artifact_core.py:247; validate_spec specs.py:128; validate_item backlog.py:129; check_drift plans_index.py:235 + research_index.py:231; is_conformant normalize_plan_names.py:205).
- 2026-08-18 /plan-review (Antigravity (Gemini 3.7 Flash High)): APPROVE; verified citations against artifact_core.py:247, specs.py:128, backlog.py:129, plans_index.py:235, and normalize_plan_names.py:205; structural lint conforming; no findings; no open questions; GO - PENDING HUMAN APPROVAL.

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

- [ ] E-01 Create `agent_workflows/check_engine.py` with this header + imports and a `SUPPORTED` map declaring which check kinds each record type supports today:
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
  - Execution state: pending

### Task group 2: name-conformity sub-check

- [ ] E-02 Add `check_names(repo_root: Path, record_type: str, legacy: bool = False) -> List[Drift]` that walks the type's record dirs (reuse `_rp.resolve_record_read_paths(record_type, target_repo=str(repo_root))`, keep existing dirs) and, for every `*.md` file that is NOT README/INDEX/STATUS, checks filename conformity to the grammar. Load the shipped normalizer by path and call its `is_conformant(name, expected_type=<facet>)` where `<facet>` is the type's facet (`plans`->`ipd`, `specs`->`spec`, `backlog`->`backlog`, `prompts`->`prompt`, `walkthroughs`->`walkthrough`, `roadmaps`->`roadmap`, `research` skip - it has its own grammar). For a nonconformant name emit `Drift(str(path), "check.name-nonconformant", "filename does not match the <type> grammar")`. `legacy` is accepted and threaded to `is_conformant` handling in Order 03 (for now, pass it through; do not special-case).
  - Load the normalizer with:
  ```python
  import importlib.util
  def _load_normalizer():
      root = Path(__file__).resolve().parent.parent  # repo root of the installed framework
      script = root / ".aw" / "system" / "workflows" / "setup-repo" / "tools" / "normalize_plan_names.py"
      spec = importlib.util.spec_from_file_location("awcheck_npn", script)
      mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
      return mod
  ```
  (If the script path does not resolve, return `[]` for names rather than raising.)
  - Depends on: E-01
  - Expected outcome: over a fixture with a well-named plan and a badly-named plan (`not-a-grammar.md`), `check_names(root,"plans")` returns exactly one Drift for the bad file with rule `check.name-nonconformant`.
  - Execution state: pending

### Task group 3: content + refs sub-checks (delegate to existing validators)

- [ ] E-03 Add `check_content(repo_root, record_type, legacy=False) -> List[Drift]` that delegates to the EXISTING per-type content validators and returns their Drift:
  - `specs`: for each spec file (reuse `specs._spec_files(repo_root)`), call `specs.validate_spec(path, text)` and extend.
  - `backlog`: for each item (reuse `backlog._iter_items(repo_root)`), call `backlog.validate_item(path, text)` and extend.
  - `plans`: front-matter/name-vs-metadata drift is produced by `plans_index.check_drift(repo_root, plans_dir, limit=None)` - call it and extend (this also covers refs; see E-04 note).
  - `research`: `research_index.check_drift(...)` similarly.
  - types without a content validator (`prompts`/`walkthroughs`/`roadmaps`): return `[]`.
  Import these lazily inside the function to avoid import cycles.
  - Depends on: E-01
  - Expected outcome: `check_content(root,"specs")` over a fixture with one malformed spec returns that spec's validate_spec Drift; a type with no content validator returns `[]`.
  - Execution state: pending
- [ ] E-04 Add `check_refs(repo_root, record_type) -> List[Drift]`: for `plans` and `research`, reference integrity is already part of their `check_drift` (dangling citations). To avoid double-counting, implement `check_refs` to return `[]` for now and note in a code comment that plans/research reference drift is delivered via `check_content` (their `check_drift`), while `check_refs` is the seam for FUTURE per-type ref checks (e.g. the Blocks-Release dangling check from the awrelease Set folds in here). This keeps the three-way composition explicit without duplicating drift.
  - Depends on: E-01
  - Expected outcome: `check_refs(root, "plans") == []` (refs are folded into content today); the function exists as the documented seam.
  - Execution state: pending

### Task group 4: the composable public API + fan-out

- [ ] E-05 Add the public `check_type(repo_root, record_type, names_only=False, legacy=False) -> List[Drift]` and `check_types(repo_root, types, names_only=False, legacy=False) -> List[Drift]`, plus create `tests/test_check_engine.py`. `check_type`: if `names_only`, return only `check_names`; else return `check_names + check_content + check_refs` (only the kinds in `SUPPORTED[type]`; an unsupported type returns a single `Drift("<type>", "check.type-unsupported", "no checks for this type")` ... EXCEPT when called from `all` fan-out, where an unsupported type is simply skipped). `check_types`: fan out over the given types (or the `SUPPORTED` keys when the caller passes the sentinel `["all"]`), concatenating Drift; unsupported types skipped. The test `CheckEngineTests` must cover: `check_names` flags a bad name; `check_content` surfaces a malformed spec's drift; `check_type("plans", names_only=True)` returns only name drift; `check_types(["all"])` runs without error over a fixture and returns a list; an unsupported single type returns the `check.type-unsupported` Drift. Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03,E-04
  - Expected outcome: the named tests pass; full serial suite green (new files only).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Shared result type: `artifact_core.Drift(location, rule, detail)` (artifact_core.py:247); `drift_exit_code` (:262) and `render_agent_drift` (:255) are the CLI-layer's job (awcmdsurf), NOT the engine's - the engine returns Drift only.
- Existing validators returning Drift: `specs.validate_spec` (specs.py:128), `backlog.validate_item` (backlog.py:129), `plans_index.check_drift` (plans_index.py:235), `research_index.check_drift` (research_index.py:231). File collectors: `specs._spec_files`, `backlog._iter_items`.
- Name conformity: the shipped `normalize_plan_names.is_conformant(name, expected_type=...)` (normalize_plan_names.py:205); research has its own grammar (skip names for research or use research_index).
- Tree dirs: `record_producers.resolve_record_read_paths(<class>, target_repo=...)` (record_producers.py:597).
- The engine is PURE: returns Drift, never prints, no argparse. The verb layer (awcmdsurf) renders + sets exit codes.

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Every validator already returns Drift. | The engine is a COMPOSITION layer; it invents no checks (except the collision check, which is Order 02). |
| F2 | plans/research fold refs into check_drift. | `check_refs` returns [] today to avoid double-counting; it is the documented seam for future ref checks (awrelease). |
| F3 | Engine must not print. | Rendering + exit codes live in the CLI verb (awcmdsurf); keeps the engine reusable + testable. |

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

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c "import agent_workflows.check_engine as c; print(sorted(c.SUPPORTED))"` output.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `check_names` over a fixture returning exactly one `check.name-nonconformant` Drift for the bad file.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `check_content(root,"specs")` surfacing a malformed spec's Drift; a no-validator type returning [].
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `check_refs(root,"plans") == []` and note the code comment marking it the future seam.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `pytest tests/test_check_engine.py -p no:xdist -q` (passing) + the full serial suite tail (no regressions).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(Gemini 3.7 Flash Medium via `agy`, opencode Opus 4.8 owning verification + path-scoped commits)
performs each E exactly as written, verifies each V with pasted evidence, commits ONLY the two new files
path-scoped (never `git add -A`), never pushes, and the plan moves to `.aw/records/plans/executed/` only
after `aw ipd lint --phase pre-transition` conforms and every V is `pass`. Order 01 of awcheck; Orders
02 (collisions) and 03 (legacy+messages) build on this engine.
