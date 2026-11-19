# IPD: Preserve prompt_kind and created_day in artifact_meta.load_legacy_artifact

- Date: 2026-11-19
- Kind: child
- Concern: Preserve `prompt_kind` and `created_day` when `agent_workflows/artifact_meta.py::load_legacy_artifact` reads staged prompt files, and invalidate stale SQLite caches via `LEGACY_LOADER_VERSION`.
- Scope: Update `agent_workflows/artifact_meta.py::load_legacy_artifact` to map `Kind` and `kind` to `prompt_kind` and `Created` and `created` to `created_day` when `art_type == "prompt"`, set `artifact_row["created_day"]` from `mapped_fields.get("created_day")` for prompts, bump `agent_workflows/artifact_meta.py::LEGACY_LOADER_VERSION` from `"legacy_v7"` to `"legacy_v8"`, and add behavioral outcome tests in `tests/test_artifact_meta_legacy.py` and `tests/test_artifact_meta_legacy_writer.py`. EXCLUDES changing non-prompt record mappings (`ipd`, `spec`, `backlog`, `research`, `release`, `walkthrough`, `roadmap`), changing `agent_workflows/artifact_meta.py::read_text`, or modifying `agent_workflows/prompts.py`.
- Scope-Paths: agent_workflows/artifact_meta.py, tests/test_artifact_meta_legacy.py, tests/test_artifact_meta_legacy_writer.py, .aw/records/plans/pending/20261119-xxdzcq-01-acqenf-preserve-prompt-kind-and-created-day-in-artifact-meta-load-l.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Review-Depth: standard
- Short-Description: Map prompt Kind to prompt_kind and Created to created_day in artifact_meta.load_legacy_artifact
- Work-Kind: bug
- Priority: medium
- From-Backlog: xxdzcq
- Blocks-Release: next
- Set: xxdzcq
- Order: 1
- Highest E allocated: 03
- Author: antigravity/gemini
- Id: acqenf

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-19 reviewed (aw set): reviewed via plan-review (PR-001, PR-002, PR-003)
- 2026-11-19 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-11-19 to-review (aw set): ready for review: authored for backlog xxdzcq
- 2026-11-19 draft (antigravity/gemini): created.

## Goal

Ensure `agent_workflows/artifact_meta.py::read` returns the declared `prompt_kind` and `created_day` values for legacy prompt files created through `artifact_meta.create` or `aw prompts new`. Today `agent_workflows/artifact_meta.py::load_legacy_artifact` maps `Kind` to `plan_role` and `Created` to `created`, both of which are absent from `REGISTRY["prompt"]` and are dropped before cache insertion.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Map prompt Kind and Created in load_legacy_artifact and bump loader version

- [ ] E-01 Update `agent_workflows/artifact_meta.py::load_legacy_artifact` and `agent_workflows/artifact_meta.py::LEGACY_LOADER_VERSION`:
  - When `art_type == "prompt"`, map bullet or comment key `bk in ("Kind", "kind")` to `target_k = "prompt_kind"`, and map `bk in ("Created", "created")` to `target_k = "created_day"`.
  - Keep existing key-mapping behavior unchanged for all other values of `art_type` (`backlog` `Kind` fallback to `work_kind` when `Work-Kind` is absent, `ipd` `Kind` to `plan_role`, `research` `kind` to `research_kind`, and `field_map` defaults).
  - Set `artifact_row["created_day"]` to `mapped_fields.get("created_day") if art_type == "prompt" else None` so `State.created_day` and `State.fields["created_day"]` agree on legacy prompts without altering non-prompt records.
  - Increment `LEGACY_LOADER_VERSION` from `"legacy_v7"` to `"legacy_v8"` and document the `xxdzcq` prompt field fix in the adjacent version comment so `compute_schema_hash` triggers cache rebuilds for pre-existing `.aw/state/index.db` files.
  - Depends on: none
  - Expected outcome: `load_legacy_artifact` populates `prompt_kind` and `created_day` in `artifact_row["fields"]`, populates `artifact_row["created_day"]` for prompts, preserves non-prompt behavior, and bumps `LEGACY_LOADER_VERSION` to `"legacy_v8"`.
  - Execution state: pending

### Task group 2: Add behavioral tests and run validation

- [ ] E-02 Add behavioral outcome tests in `tests/test_artifact_meta_legacy.py` and `tests/test_artifact_meta_legacy_writer.py`:
  - In `tests/test_artifact_meta_legacy.py`, assert `art_row["fields"]["prompt_kind"]` in `test_legacy_load_staged_prompt_with_comment_artifact`, add a test verifying `load_legacy_artifact` maps `Kind:` to `prompt_kind` and `Created:` to `created_day` (both `art_row["fields"]["created_day"]` and `art_row["created_day"]`) on `<!-- aw-prompt: ... -->` prompts, and add assertions verifying `ipd` (`Kind` -> `plan_role`), `backlog` (`Kind` -> `work_kind`), and `research` (`kind` -> `research_kind`) mappings remain intact.
  - In `tests/test_artifact_meta_legacy_writer.py`, assert via `agent_workflows/artifact_meta.py::read` (after `agent_workflows/artifact_meta.py::create` on a legacy root and via `agent_workflows/cli.py::main` / `aw prompts new` in an isolated repo) that `state.fields["prompt_kind"]`, `state.fields["created_day"]`, and `state.created_day` match the written `Kind:` and `Created:` header values, and verify that a stale `.aw/state/index.db` cache with `NULL` `prompt_kind` and `created_day` values under an older `schema_hash` is rebuilt under `LEGACY_LOADER_VERSION`.
  - Depends on: E-01
  - Expected outcome: All new and existing behavioral tests pass and fail against the unpatched `load_legacy_artifact` implementation.
  - Execution state: pending

- [ ] E-03 Run targeted tests, full test suite, static type check, and repository hygiene checks after the final edit:
  - Run `python3 -m pytest -v tests/test_artifact_meta_legacy.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_loader_parity.py tests/test_prompts_new.py`.
  - Run `python3 -m pytest`.
  - Run `python3 -m mypy agent_workflows`.
  - Run `aw check all --agent` and `aw sanitize --agent`.
  - Depends on: E-02
  - Expected outcome: Every test run, `mypy`, `aw check all --agent`, and `aw sanitize --agent` exits 0 with zero errors.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Prompt comment metadata keys are defined in `agent_workflows/artifact_meta.py::_PROMPT_COMMENT_KEY`, which writes `prompt_kind` as `Kind` and `created_day` as `Created`.
- `agent_workflows/prompts.py::run_new` passes `"prompt_kind"` and `"created_day"` into `artifact_meta.create(..., legacy_render=...)`, which renders `<!-- aw-prompt: Kind: ... | Id: ... | Set: ... | Status: ... | Created: ... -->`.
- `agent_workflows/artifact_meta.py::REGISTRY["prompt"]` defines `"prompt_kind"` and inherits `"created_day"` from `_COMMON_FIELDS`, whereas `"plan_role"` exists only in `REGISTRY["ipd"]` and `"created"` exists only in `REGISTRY["research"]`.
- `agent_workflows/artifact_meta.py::compute_schema_hash` includes `LEGACY_LOADER_VERSION` so any change to `load_legacy_artifact` output for an unchanged file requires bumping `LEGACY_LOADER_VERSION` (from `"legacy_v7"` to `"legacy_v8"`).
- `agent_workflows/artifact_meta.py::replay` sets `state.created_day = current_fields.get("created_day")`, so `State.created_day` and `State.fields["created_day"]` agree in the log-backed path.
- `agent_workflows/migrations/m0001_convert.py` already maps prompt `Kind` to `prompt_kind` and `Created` to `created_day` during migration conversion.

## Findings

1. In `agent_workflows/artifact_meta.py::load_legacy_artifact`, `field_map` maps `"Kind"` to `"plan_role"` and `"kind"` to `"research_kind"`, and contains no mapping for `"Created"`.
2. In the bullet/comment mapping loop of `load_legacy_artifact`, only `bk == "Kind" and art_type == "backlog"` has a type-specific branch; for `art_type == "prompt"`, `"Kind"` falls through to `field_map["Kind"]` (`"plan_role"`) and `"Created"` falls through to `bk.lower().replace("-", "_")` (`"created"`).
3. Neither `"plan_role"` nor `"created"` is present in `REGISTRY["prompt"]`, so the `fields` filter at the end of `load_legacy_artifact` drops both keys before `_store_legacy_artifact_projection` writes the `"prompt"` SQLite table.
4. `artifact_row["created_day"]` in `load_legacy_artifact` is hardcoded to `None`, so `State.created_day` is also `None` when `artifact_meta.read` loads a legacy prompt.
5. In `tests/test_artifact_meta_legacy.py::test_legacy_load_staged_prompt_with_comment_artifact`, the docstring states `"Staged prompt comment maps Kind to prompt_kind."`, but the test body never inspects `art_row["fields"]`, leaving the bug undetected.

## Proposed changes (ordered, validatable)

1. In `agent_workflows/artifact_meta.py::load_legacy_artifact`, branch on `art_type == "prompt"` inside the `bullets.items()` loop before consulting `field_map`:
   - Map `bk in ("Kind", "kind")` to `target_k = "prompt_kind"`.
   - Map `bk in ("Created", "created")` to `target_k = "created_day"`.
2. In `agent_workflows/artifact_meta.py::load_legacy_artifact`, set `"created_day": mapped_fields.get("created_day") if art_type == "prompt" else None` in `artifact_row` so `State.created_day` matches `State.fields["created_day"]` on prompts while keeping non-prompt behavior unchanged.
3. In `agent_workflows/artifact_meta.py`, bump `LEGACY_LOADER_VERSION` from `"legacy_v7"` to `"legacy_v8"` and add the `"legacy_v8"` note above the constant so existing SQLite caches rebuild on next open.
4. Add behavioral tests in `tests/test_artifact_meta_legacy.py` and `tests/test_artifact_meta_legacy_writer.py` covering `load_legacy_artifact`, `artifact_meta.create` -> `artifact_meta.read`, `aw prompts new` -> `artifact_meta.read`, stale cache rebuild on version bump, and non-prompt `Kind`/`kind` regression preservation.

```mermaid
flowchart TD
    A["bullets key bk in load_legacy_artifact"] --> B{"bk in (Kind, kind) or (Created, created)?"}
    B -->|No| C["target_k = field_map.get(bk, lowercase)"]
    B -->|Yes| D{"art_type?"}
    D -->|backlog and Kind| E["If Work-Kind set, skip Kind; else target_k = work_kind"]
    D -->|prompt and Kind or kind| F["target_k = prompt_kind"]
    D -->|prompt and Created or created| G["target_k = created_day"]
    D -->|other art_type| C
    E -->|when Work-Kind absent| H["Filter mapped_fields by REGISTRY[art_type]"]
    F --> H
    G --> H
    C --> H
    H --> I["Set artifact_row created_day for prompt"]
    I --> J["LEGACY_LOADER_VERSION legacy_v8 triggers cache rebuild"]
```

## Deferred / out of scope (with reason)

- Updating `agent_workflows/artifact_meta.py::read_text` to parse `<!-- aw-prompt: ... -->` HTML comments: `read_text` only parses YAML front matter and markdown bullets, and backlog item `xxdzcq` targets `load_legacy_artifact` and `artifact_meta.read`.
  - Carrier-Declined: Separate in-memory parser outside `load_legacy_artifact`.
- Populating `artifact_row["created_day"]` from `- Date:` or YAML `created:` for non-prompt record types (`ipd`, `spec`, `backlog`, `release`, `research`): backlog item `xxdzcq` requires preserving existing behavior for other record types.
  - Carrier-Declined: Explicit non-regression constraint in backlog item `xxdzcq`.

## Scope check

- Over-scope: none. Only `agent_workflows/artifact_meta.py`, `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_legacy_writer.py`, and this IPD are modified.
- Under-scope: none. Fixing `load_legacy_artifact` and bumping `LEGACY_LOADER_VERSION` fixes every `artifact_meta.read`, `artifact_meta.query`, and `aw prompts new` cache-read path for legacy prompts.

## Required tests / validation

- Targeted tests: `python3 -m pytest -v tests/test_artifact_meta_legacy.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_loader_parity.py tests/test_prompts_new.py`
- Full suite: `python3 -m pytest`
- Static type check: `python3 -m mypy agent_workflows`
- Self-check and leak scan: `aw check all --agent` and `aw sanitize --agent`

## Spec / documentation sync

N/A: this bugfix restores already-specified prompt field mapping (`prompt_kind` and `created_day` in `REGISTRY["prompt"]`) inside `agent_workflows/artifact_meta.py::load_legacy_artifact` without changing CLI interfaces, record formats, or specification contracts.

## Open questions

### OQ-01: Should `load_legacy_artifact` also set top-level `artifact_row["created_day"]` for prompts, in addition to `artifact_row["fields"]["created_day"]`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, for `art_type == "prompt"` only (`mapped_fields.get("created_day") if art_type == "prompt" else None`). In `agent_workflows/artifact_meta.py::replay`, `State.created_day` is populated from `current_fields.get("created_day")`, so setting `artifact_row["created_day"]` for prompts keeps `State.created_day` and `State.fields["created_day"]` consistent across legacy and log-backed reads while leaving non-prompt legacy rows unchanged.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the unified `git diff agent_workflows/artifact_meta.py` showing `art_type == "prompt"` mapping `Kind`/`kind` to `prompt_kind` and `Created`/`created` to `created_day`, setting `artifact_row["created_day"]` for prompts, preserving non-prompt mappings, and bumping `LEGACY_LOADER_VERSION` to `"legacy_v8"`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `python3 -m pytest -v tests/test_artifact_meta_legacy.py tests/test_artifact_meta_legacy_writer.py` output showing all PASSED test node IDs covering `load_legacy_artifact` prompt `Kind`/`Created` mapping, non-prompt `Kind`/`kind` preservation, `artifact_meta.create` and `aw prompts new` round-trip via `artifact_meta.read`, and stale cache rebuild on `LEGACY_LOADER_VERSION` bump.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the pass summaries and exit codes from `python3 -m pytest -v tests/test_artifact_meta_legacy.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_loader_parity.py tests/test_prompts_new.py`, `python3 -m pytest`, `python3 -m mypy agent_workflows`, `aw check all --agent`, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution proceeds only after `OQ-01` remains resolved and `aw ipd set approved acqenf --by-human` (or runner dispatch on an approved plan). `- Scope-Paths:` declares the expected modified files; if execution requires editing an additional file or leaves a declared path untouched, complete the work and justify the variance via `--scope-reason` or `--scope-ack` at finalize rather than stopping over scope. When reporting tests or checks passed, you MUST paste the actual runner output and never claim success you did not run. Commit only the paths you modified using `aw commit acqenf -- <paths>`, never `git add -A`, bare `git add`, or `git commit -a`, and never push without explicit human instruction. Never perform a hand-rolled `git mv` to `executed/`. After `V-01` through `V-03` reach `pass`, finalize the plan lifecycle to `executed/` unconditionally: when `aw oc run` or `aw agy run` executes the plan, the runner owns `aw ipd finalize`; when executed directly outside a runner, run `aw ipd finalize acqenf --actor ...`.
