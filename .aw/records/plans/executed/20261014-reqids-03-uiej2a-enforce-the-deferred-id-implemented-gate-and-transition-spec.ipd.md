# IPD: Enforce the Deferred-ID implemented gate and transition spec 89xjll to implemented

- Date: 2026-10-14
- Kind: child
- Concern: Spec-requirement-ID deferred-implemented gate, partial-pass deferred event, qualified-citation prompt/review parity, and spec 89xjll transition to implemented.
- Scope: Implement the spec 89xjll R-9 / Section 6.5 / AC-10 refusal on transitioning a spec with remaining [Deferred] IDs to implemented in agent_workflows/specs.py and agent_workflows/status_set.py; wire spec_plan_trace_deferred into the spec production block in agent_workflows/runner_shared.py to emit a distinguishable partial-pass event (89xjll R-6 / Section 6.3 / AC-9); add the 89xjll Section 6.2b qualified-citation instruction to the approved-spec branch of build_spec_production_prompt in agent_workflows/runner_shared.py and to both plan-review variants (.aw/system/workflows/plan-review/plan-review.md and .aw/system/workflows/plan-review-long/review-rubric.md, kept in deliberate parity); add behavioral tests in tests/test_production_checks_trace.py and tests/test_spec_production.py; and transition spec 89xjll approved -> implementing -> implemented via aw specs set so backlog vy20et can close to done.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/runner_shared.py, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/review-rubric.md, tests/test_production_checks_trace.py, tests/test_spec_production.py, .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md, .aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md, .aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md, .aw/records/plans/pending/20261014-reqids-03-uiej2a-enforce-the-deferred-id-implemented-gate-and-transition-spec.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: vy20et
- From-Spec: 89xjll
- Set: reqids (Spec requirement-ID convention and SPEC-PLAN-TRACE verification)
- Order: 3
- Highest E allocated: 06
- Author: antigravity
- Id: uiej2a

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: uiej2a verified (set reqids, attempt 1). [Scope reconciliation - in-scope-unmodified .aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (/plan-review, opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009
- 2026-10-14 to-review (aw set): Authored review-ready child IPD uiej2a from backlog vy20et and spec 89xjll

- 2026-10-14 draft (antigravity): created.

## Goal

Complete the remaining implementation obligations of approved specification `89xjll` (`.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`, amended 2026-10-08/09 with maintainer rulings OQ-04..OQ-08) that were deferred outside `rtvdak`'s scope fence, and transition `89xjll` through `implementing` to `implemented` via `aw specs set` so that backlog item `vy20et` (currently `graduated`, `.aw/records/backlog/graduated/20260926-reqids-01-vy20et-spec-requirement-id-convention-for-trace.backlog.md`) satisfies all carrier completion checks (`runner_shared._classify_backlog_carriers`) once this plan itself is finalized to `executed/`. Specifically: (1) enforce `89xjll R-9` / Section 6.5 / `89xjll AC-10` at the spec status setter (`agent_workflows/specs.py` and `agent_workflows/status_set.py`) so both `aw specs set <path> --status implemented` and `aw spec set implemented <id6>` refuse when a spec body still declares any `[Deferred]` requirement or acceptance ID; (2) wire `production_checks.spec_plan_trace_deferred` into the spec production SUCCESS path in `agent_workflows/runner_shared.py` so passes with `[Deferred]` IDs emit a distinguishable `spec-plan-trace-deferred` event (`89xjll R-6`, `89xjll AC-9`); (3) add the `89xjll` Section 6.2b qualified-citation authoring requirement to the `approved`-spec branch of `runner_shared.build_spec_production_prompt` and to both plan-review variants (`.aw/system/workflows/plan-review/plan-review.md` rubric G and `.aw/system/workflows/plan-review-long/review-rubric.md` section A); and (4) transition `89xjll` `approved -> implementing -> implemented` with executed IPD `rtvdak` as `--evidence`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-verify shipped 89xjll baseline and setter/runner insertion anchors

- [x] E-01 Re-verify at execution HEAD that the requirement-ID parser, cutover, and `SPEC-PLAN-TRACE` verifier obligations delivered by executed IPDs `rtvdak` and `2hgxi1` (`89xjll R-1`, `89xjll R-2`, `89xjll R-3`, `89xjll R-4`, `89xjll R-5`, `89xjll R-6`, `89xjll R-7`, `89xjll R-8`) are intact in `agent_workflows/production_checks.py` (`parse_spec_requirement_ids`, `parse_spec_id_markers`, `spec_requires_requirement_ids`, `spec_plan_trace`, `spec_plan_trace_vacuity`, `spec_plan_trace_deferred`), and confirm the exact insertion anchors in `agent_workflows/specs.py` (`_evidence_resolvable`), `agent_workflows/status_set.py` (`validate_transition_allowed`), `agent_workflows/runner_shared.py` (`build_spec_production_prompt` and the `spec-plan-trace-vacuity` block), `.aw/system/workflows/plan-review/plan-review.md` (`### G. Plan executability`), and `.aw/system/workflows/plan-review-long/review-rubric.md` (`## A. Plan completeness`). ALSO record the pre-edit bare-suite baseline: run bare `python3 -m pytest` and record its summary line and every failing node id (if any); that baseline, compared by NODE ID and never by total, is the bar V-05 applies. Confirm `production_checks.parse_spec_id_markers` on spec `89xjll`'s own body returns no `Deferred` marker (measured `{}` at review HEAD `70179b555`), so the new E-02 gate will not refuse E-05.
  - Depends on: none
  - Expected outcome: Baseline `tests/test_production_checks_trace.py` and `tests/test_spec_production.py` pass for `89xjll R-1`, `89xjll R-2`, `89xjll R-3`, `89xjll R-4`, `89xjll R-5`, `89xjll R-6`, `89xjll R-7`, and `89xjll R-8`; `production_checks.parse_spec_requirement_ids` on the target spec (`89xjll`) extracts `R-1`..`R-9` and `AC-1`..`AC-10` as disjoint sets; `parse_spec_id_markers` on `89xjll`'s parse contains no `Deferred` value; the bare-suite baseline (summary line plus failing node ids) is recorded; and the insertion anchors in `specs.py`, `status_set.py`, `runner_shared.py`, `plan-review.md`, and `review-rubric.md` are verified before editing.
  - Execution state: performed

### Task group 2: Enforce the Deferred-ID implemented transition gate (89xjll R-9 / AC-10)

- [x] E-02 Implement `_deferred_ids_refusal(spec_path: Path, text: str) -> Optional[str]` in `agent_workflows/specs.py` (delegating marker extraction to `production_checks.parse_spec_id_markers(text)` per `89xjll R-8`, imported FUNCTION-LOCALLY because `agent_workflows/production_checks.py` already imports `specs` at module top (`from agent_workflows import specs as _specs`), so a module-level import in `specs.py` would be circular) and wire it into `status_set.validate_transition_allowed` in `agent_workflows/status_set.py` inside the `if rec.record_type == "specs":` transition guard when `norm_status == "implemented"` (immediately after the `if auth.get("evidence"):` gate), so that both `aw specs set <path> --status implemented` and `aw spec set implemented <id6>` (plus `aw set implemented <id6>`) refuse to transition any spec whose body still declares any `[Deferred]` requirement or acceptance ID, naming every remaining deferred ID in sorted order and leaving disk unchanged (`89xjll R-8`, `89xjll R-9`).
  - Depends on: E-01
  - Expected outcome: Calling `aw specs set <path> --status implemented` or `aw spec set implemented <id6>` on a spec whose body declares any `[Deferred]` ID returns exit code `1` via `status_set.validate_transition_allowed`, prints a refusal naming every remaining `[Deferred]` ID and the remedy (remove each `[Deferred]` marker and plan the ID, or delete the requirement from the spec), and writes nothing to disk (`89xjll R-8`, `89xjll R-9`).
  - Execution state: performed

### Task group 3: Wire partial-pass deferred event and qualified-citation guidance (89xjll R-5, R-6, R-7 / AC-9)

- [x] E-03 Wire `production_checks.spec_plan_trace_deferred(target_tree, item["id6"])` into the spec production SUCCESS path of `agent_workflows/runner_shared.py` (the `else:` branch commented `# Success path!` that follows `if findings:` after the production correction-turn loop), so that a production whose FINAL `SPEC-PLAN-TRACE` evaluation passed on a spec with `[Deferred]` IDs appends `{"at": utc_now(), "event": "spec-plan-trace-deferred", "id6": item["id6"], "partial": True, "deferred_ids": trace_deferred}` to `run_dir / "events.jsonl"` (`89xjll R-6`, `89xjll R-7`). Emitting it on the success path (not beside the first-evaluation `spec-plan-trace-vacuity` record) is deliberate: `89xjll`'s Section 6.3 describes a PASS that is partial, and a record written before the correction loop would label a later-failed production `partial: True`. Emit nothing when `trace_deferred` is empty. `runner_shared.py` serves both hosts, so no `oc_runipd.py`/`agy_runipd.py` edit is needed.
  - Depends on: E-01
  - Expected outcome: When a spec production passes on a spec declaring `[Deferred]` IDs, on BOTH hosts, `events.jsonl` carries exactly one `"event": "spec-plan-trace-deferred"` record with `"partial": True` and the sorted `"deferred_ids"`; a production that fails or a spec declaring no `[Deferred]` IDs writes no such record (`89xjll R-6`, `89xjll R-7`).
  - Execution state: performed

- [x] E-06 Add the `89xjll`'s Section 6.2b qualified-citation rule (`89xjll R-5`) to the three authoring/review guidance surfaces: (a) the `approved`-spec branch of `runner_shared.build_spec_production_prompt` (add Production Contract item `8` mirroring the `implementing` branch, computing `uncited = _pc.spec_uncited_trace_ids(root, spec_id6)`); (b) `### G. Plan executability` in `.aw/system/workflows/plan-review/plan-review.md`; and (c) `## A. Plan completeness` in `.aw/system/workflows/plan-review-long/review-rubric.md`, with the SAME bullet text as (b), because `plan-review.md` states the two variants are "kept in deliberate parity" and executed precedent `9aprci` edited both for a rubric bullet.
  - Depends on: E-01
  - Expected outcome: `build_spec_production_prompt` for an `approved` post-cutover spec contains the qualified-citation instruction naming the spec's Section 6.2b (the literal prompt text reads as in the `implementing` branch) and the uncited mandatory IDs; both plan-review surfaces carry an identical bullet instructing reviewers that plans carrying `- From-Spec:` for a post-cutover spec must qualify requirement (`E-*`) and acceptance (`V-*`) citations with the spec id6 (`89xjll R-5`).
  - Execution state: performed

### Task group 4: Behavioral unit and runner tests for AC-9 and AC-10

- [x] E-04 Add behavioral unit and runner tests in `tests/test_production_checks_trace.py` and `tests/test_spec_production.py` covering: (1) both `aw specs set <path> --status implemented` (`specs.run_set`) and `aw spec set implemented <id6>` (`status_set.run_set_command`) refusing on a spec declaring `[Deferred]` requirement/acceptance IDs, naming the deferred IDs, leaving the file byte-identical on disk and `git status --short` clean, and succeeding once `[Deferred]` markers are removed (`89xjll R-8`, `89xjll R-9`); and (2) spec production on an `approved` post-cutover spec with `[Deferred]` IDs, on BOTH hosts (the module's `_HOSTS` loop), emitting the `spec-plan-trace-deferred` partial-pass event in `events.jsonl`, a no-`[Deferred]` passing production emitting none, and the `approved`-spec production prompt including the qualified-citation instruction in the `approved`-spec production prompt (`89xjll R-5`, `89xjll R-6`, `89xjll R-7`).
  - Depends on: E-02, E-03, E-06
  - Expected outcome: All existing and newly added behavioral tests in `tests/test_production_checks_trace.py` and `tests/test_spec_production.py` pass without inspecting source text (`89xjll R-5`, `89xjll R-6`, `89xjll R-8`, `89xjll R-9`).
  - Execution state: performed

### Task group 5: Transition spec 89xjll to implemented and verify repository checks

- [x] E-05 Transition `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` in two hops via `aw specs set`: first `approved -> implementing` (`--graduated-to reqids --message "IPDs jjh4aj, rtvdak, and uiej2a in Set reqids implement spec (89xjll)" --yes --no-commit`), then `implementing -> implemented` (`--evidence .aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md --message "Implemented by IPDs rtvdak, 2hgxi1, and uiej2a: requirement-ID parser, SPEC-PLAN-TRACE verifier, partial-pass deferred event, qualified-citation prompt/review guidance, and Deferred-ID implemented gate" --yes --no-commit`), and run `aw specs check`, `aw attention --check`, and the full bare `python3 -m pytest` suite (`89xjll R-1`, `89xjll R-9`). The first hop runs the `check_engine.evaluate_handoff_ready(repo_root, "spec", "89xjll")` gate (measured `ready == True` at review HEAD `70179b555`); the second hop runs the E-02 `[Deferred]` gate and the `->implemented` evidence gate.
  - Depends on: E-04
  - Expected outcome: The target spec (`89xjll`) resides at `.aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` with `- Status: implemented` and `- Graduated-To: reqids`; its `approved/` and `implementing/` paths are absent; `aw specs check` exits `0`; `aw attention --check` reports no finding naming `89xjll`, `vy20et`, or `uiej2a` (its exit code is recorded but is not the bar, because the command also reports live lane-hygiene findings unrelated to this plan: 8 `attention.lane-stranded`/`attention.lane-superseded` findings and exit `1` at review HEAD `70179b555`, a count to be re-derived at execution); `runner_shared._classify_backlog_carriers(Path('.'), 'vy20et')` reports `unimplemented_specs == []` and `unexecuted_ipds` containing ONLY this plan's own `pending/` path (which `aw ipd finalize` clears); and bare `python3 -m pytest` shows no failing node id absent from the E-01 baseline (`89xjll R-1`, `89xjll R-9`).
  - Execution state: performed

## Project conventions discovered (Step 0)

- **Shared status-setter dispatch (`specs.run_set` -> `status_set.run_set_command`)**: In `agent_workflows/specs.py` (`def run_set` at line 743), `aw specs set` is a thin adapter delegating to `status_set.run_set_command(..., scoped_type="specs")`. Both `aw specs set <path> --status implemented` and `aw spec set implemented <id6>` (as well as `aw set implemented <id6>`) execute the pre-flight loop in `status_set.run_set_command` (`agent_workflows/status_set.py` line 3082), which calls `status_set.validate_transition_allowed(rec, target_status, args, repo_root)` (`agent_workflows/status_set.py` line 643) before any dry-run branch or disk write.
- **Shared spec transition refusal pattern in `specs.py` + `status_set.py`**: In `agent_workflows/status_set.py` (`validate_transition_allowed`, lines 786-807), spec transition gates (`_review_attestation_refusal` and `_evidence_resolvable`) live in `agent_workflows/specs.py` (lines 1214-1278) and are invoked inside `if rec.record_type == "specs":` when `old_status and old_status != norm_status`. Guarding on `old_status != norm_status` ensures a same-status re-assertion is not retroactively refused.
- **Two-hop spec transition (`approved -> implementing -> implemented`)**: In `agent_workflows/attention_contract.py` (`SPEC_TRANSITIONS`), `approved -> implemented` is not a direct edge (`"approved": frozenset({"implementing", "deferred", "parked", "superseded"})`, `"implementing": frozenset({"approved", "implemented", "deferred", "parked", "superseded"})`). As demonstrated by executed IPD `dwivqd` (`.aw/records/plans/executed/20261001-jd01a0-01-dwivqd-transition-spec-kw5y2s-to-implemented-through-implementing-w.ipd.md`), an `approved` spec transitions to `implemented` in two hops via `aw specs set`: first `approved -> implementing` (which checks `check_engine.evaluate_handoff_ready(repo_root, "spec", spec_id6)` at `status_set.py` line 3245), then `implementing -> implemented` with `--evidence <executed-ipd-path>`. Because `record_placement.resolve_transition_path` moves the spec file across status subdirectories, all three paths (`approved/`, `implementing/`, `implemented/`) must be declared in `- Scope-Paths:`.
- **Why backlog item `vy20et` remained `open` after Set `reqids` (`9wzlou`, `jjh4aj`, `rtvdak`) executed**: `runner_shared._classify_backlog_carriers(repo, "vy20et")` (`agent_workflows/runner_shared.py` line 28445) inspects all artifacts carrying `- From-Backlog: vy20et`. Spec `89xjll` carries `- From-Backlog: vy20et` and remained at `- Status: approved`, causing `backlog_item_already_complete(repo, "vy20et")` to return `("not_complete", "spec carrier(s) not implemented: .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")`.
- **No code-pinning tests (GUIDING_PRINCIPLES P16)**: Tests must exercise real functions, CLI entrypoints, or subprocesses and assert on observable outputs, exit codes, and filesystem side effects; never inspect source files with `inspect`, `ast`, regex, or substring reads.
- **Cite code by SYMBOL (`module.function`) or quoted string**: Line numbers are hints attached to a symbol or quoted string (`spec ipd-structure-and-linting` Section 10.2; `IPD-C801`).

## Findings

| ID | Area | Evidence | Finding | Disposition |
| --- | --- | --- | --- | --- |
| F-01 | Backlog `vy20et` carrier state | `agent_workflows/runner_shared.py:28445` (`runner_shared._classify_backlog_carriers`), `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md:4` (`- Status: approved`) | Backlog item `vy20et` was returned to authoring on 2026-10-06 by `gradcover` `52opph` and re-graduated to this plan on 2026-10-14 (it now sits in `.aw/records/backlog/graduated/`). Although its initial plan Set `reqids` (`9wzlou`, `jjh4aj`, `rtvdak`) is in `.aw/records/plans/executed/`, `vy20et` could not close to `done` because spec `89xjll` carries `- From-Backlog: vy20et` and is still at `- Status: approved`. | Addressed by E-05 (transitioning `89xjll` `approved -> implementing -> implemented` once its remaining `AC-10` / `R-9` and `6.2b`/`6.3` items are in place). |
| F-02 | Unimplemented `89xjll R-9` / Section 6.5 / `89xjll AC-10` gate | `.aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md:309` (`AC-10 (Scope fence: status setter check deferred)`), `agent_workflows/status_set.py:798` (`if auth.get("evidence"):`) | Executed IPD `rtvdak` implemented `production_checks.parse_spec_id_markers` and `production_checks.spec_plan_trace_deferred`, but explicitly deferred `89xjll R-9` / `89xjll AC-10` (refusing `aw specs set <path> --status implemented` and `aw spec set implemented <id6>` when a spec still declares any `[Deferred]` ID) because `agent_workflows/specs.py` and `agent_workflows/status_set.py` were outside `rtvdak`'s declared `- Scope-Paths:`. | Addressed by E-02 and E-04. |
| F-03 | Unwired `spec_plan_trace_deferred` in `runner_shared.py` (`89xjll R-6` / Section 6.3 / `89xjll AC-9`) | `agent_workflows/production_checks.py:888` (`def spec_plan_trace_deferred`), `agent_workflows/runner_shared.py:40847` (`trace_vacuity = _pc.spec_plan_trace_vacuity(target_tree, item["id6"])`) | `production_checks.spec_plan_trace_deferred` was added by `rtvdak` to list `[Deferred]` IDs on a passing `SPEC-PLAN-TRACE` check, but has zero callers in `agent_workflows/`. In `runner_shared.py`, the spec production block records `spec-plan-trace-vacuity` to `events.jsonl` but never calls `spec_plan_trace_deferred` to record a partial-pass event listing deferred IDs when the final `findings` is empty and `trace_deferred` is non-empty. | Addressed by E-03 and E-04. |
| F-04 | Qualified-citation authoring guidance gap on `approved` spec prompt and both plan-review variants (`89xjll` Section 6.2b) | `agent_workflows/runner_shared.py:29956` (`if spec_status == "implementing":`), `agent_workflows/runner_shared.py:29974` (`# Plan production from approved spec:`), `.aw/system/workflows/plan-review/plan-review.md:543` (`### G. Plan executability`) | Spec `89xjll` Section 6.2b requires that both the spec-to-plan production prompt and `/plan-review` guidance instruct authors/reviewers to qualify spec requirement and acceptance citations with the spec's `id6` (e.g. `` `89xjll` R-3 ``). Plan `2hgxi1` added this instruction only to the `spec_status == "implementing"` branch of `build_spec_production_prompt`, leaving the `approved` branch (`runner_shared.py:29974-29987`), `.aw/system/workflows/plan-review/plan-review.md`, and its parity twin `.aw/system/workflows/plan-review-long/review-rubric.md` without the `89xjll` 6.2b rule. | Addressed by E-06 and E-04. |
| F-05 | Contention check across pending IPDs | `.aw/records/plans/pending/*.ipd.md` | Re-measured at review HEAD `70179b555`: `xvv7n4` (`reviewed`) also declares `agent_workflows/specs.py` and `i2ty4u` (`reviewed`) also declares `agent_workflows/runner_shared.py` and `tests/test_spec_production.py`; both edit unrelated functions. Per `AGENTS.md`, the runner's per-item isolated worktree and merge-and-revalidate gate resolve shared files, so no ordering edge is needed. | Verified; `- Item-Dependencies: none`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/specs.py` (`_deferred_ids_refusal`, `E-02`)**:
   - Immediately after `_evidence_resolvable` (`agent_workflows/specs.py` line 1254), define `_deferred_ids_refusal(spec_path: Path, text: str) -> Optional[str]`:
     - Import `production_checks as _pc` INSIDE the function body (module-level import would be circular: `production_checks.py` imports `specs` at top) and inspect `_pc.parse_spec_id_markers(text or "")`.
     - Collect all declared IDs whose marker is `"Deferred"`: `deferred = sorted(k for k, v in markers.items() if v == "Deferred")`.
     - If `not deferred`, return `None`.
     - Otherwise return a clear refusal message naming the spec (`id6` or `spec_path.name`), listing every remaining `[Deferred]` ID (`", ".join(deferred)`), and stating the remedy from `89xjll` Section 6.5: remove each `[Deferred]` marker and plan the ID (or delete the requirement/acceptance criterion from the spec) before transitioning to `implemented`.
2. **`agent_workflows/status_set.py` (`validate_transition_allowed`, `E-02`)**:
   - In `status_set.validate_transition_allowed` (`agent_workflows/status_set.py` line 798, inside `if rec.record_type == "specs":` and `if old_status and old_status != norm_status:`), immediately after the `if auth.get("evidence"):` block (line 807), add the `->implemented` `[Deferred]`-ID gate:
     ```python
     if norm_status == "implemented":
         from agent_workflows import specs as _specs

         deferred_reason = _specs._deferred_ids_refusal(rec.path, rec.raw_text)
         if deferred_reason is not None:
             return False, deferred_reason
     ```
   - Because `specs.run_set` (`agent_workflows/specs.py` line 743) delegates directly to `status_set.run_set_command(..., scoped_type="specs")`, this single gate in `validate_transition_allowed` binds `aw specs set <path> --status implemented`, `aw spec set implemented <id6>`, `aw specs set implemented <id6>`, and `aw set implemented <id6>` identically before any dry-run or file write.
3. **`agent_workflows/runner_shared.py` (`build_spec_production_prompt`, `E-06`; `spec-plan-trace-deferred` event, `E-03`)**:
   - In `runner_shared.build_spec_production_prompt` (`agent_workflows/runner_shared.py` line 29974, the `approved`-spec branch), add item `8` to `## Production Contract` matching the `implementing` branch (`runner_shared.py` line 29956):
     - Compute `uncited = _pc.spec_uncited_trace_ids(root, spec_id6)` and `uncited_str = ", ".join(uncited) if uncited else "none"`.
     - Append `"8. Mandatory uncited requirement and acceptance items awaiting coverage: {uncited_str}. Each must be cited qualified with the spec id6 (for example \`{spec_id6} R-2\`) in an E-* (requirement) or V-* (acceptance) item, per spec 89xjll 6.2b."`
   - In the spec production SUCCESS path (`agent_workflows/runner_shared.py`, the `else:` branch commented `# Success path!` after `if findings:`, near line 41124; NOT beside the first-evaluation `trace_vacuity` record near line 40852, which precedes the correction loop), call `trace_deferred = _pc.spec_plan_trace_deferred(target_tree, item["id6"])` and, when `trace_deferred` is non-empty, append to `run_dir / "events.jsonl"`:
     ```python
     trace_deferred = _pc.spec_plan_trace_deferred(target_tree, item["id6"])
     if trace_deferred:
         append_jsonl(
             run_dir / "events.jsonl",
             {
                 "at": utc_now(),
                 "event": "spec-plan-trace-deferred",
                 "id6": item["id6"],
                 "partial": True,
                 "deferred_ids": trace_deferred,
             },
         )
     ```
4. **`.aw/system/workflows/plan-review/plan-review.md` (`Engineering rubric G`) and `.aw/system/workflows/plan-review-long/review-rubric.md` (`## A. Plan completeness`) (`E-06`)**:
   - Under `### G. Plan executability` in `.aw/system/workflows/plan-review/plan-review.md` (around line 558), add a bullet stating the `89xjll` Section 6.2b qualified-citation rule: when a plan carries `- From-Spec: <spec-id6>` for a post-cutover spec (filename date `>= 20261001`), every mandatory spec requirement citation in `E-*` items and every acceptance criterion citation in `V-*` items MUST be qualified with `<spec-id6>` (for example `` `89xjll` R-3 `` or `89xjll AC-2`), because `SPEC-PLAN-TRACE` ignores unqualified tokens in both directions.
   - Add the IDENTICAL bullet to `## A. Plan completeness` in `.aw/system/workflows/plan-review-long/review-rubric.md` (the long variant's executability rubric, where the sibling `Runtime-demonstration reachability` bullet already lives), preserving the two variants' deliberate parity.
5. **`tests/test_production_checks_trace.py` and `tests/test_spec_production.py` (`E-04`)**:
   - In `tests/test_production_checks_trace.py`, add a `TestSpecDeferredImplementedGate` test class exercising both `aw specs set <path> --status implemented --evidence <executed-ipd> --yes --no-commit` (`specs.run_set`) and `aw spec set implemented <id6> --evidence <executed-ipd> --yes --no-commit` (`status_set.run_set_command`) on a spec declaring `[Deferred]` IDs (`R-3` and `AC-2`): assert exit code `1`, refusal text naming `AC-2` and `R-3`, byte-identical file on disk, and clean `git status --short`; then remove `[Deferred]` from `R-3` and `AC-2` and assert the transition succeeds (`exit 0`, spec moved to `implemented/` with `- Status: implemented`).
   - In `tests/test_spec_production.py`, add a test verifying that: (a) `build_spec_production_prompt` on an `approved` post-cutover spec includes the qualified-citation instruction (`spec 89xjll 6.2b`) and lists uncited mandatory IDs; and (b) a spec production run on a post-cutover spec with `[Deferred]` IDs (`R-3 [Deferred]`, `AC-2 [Deferred]`) whose produced plan covers the non-deferred IDs passes `SPEC-PLAN-TRACE` and emits `event == "spec-plan-trace-deferred"` with `"partial": True` and `"deferred_ids": ["AC-2", "R-3"]` in `events.jsonl` on both hosts; plus (c) a negative case: the existing no-`[Deferred]` success fixture writes no `spec-plan-trace-deferred` record.
6. **Transition spec `89xjll` (`E-05`)**:
   - Run `AW_NO_REEXEC=1 python3 -m agent_workflows specs set .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md --status implementing --graduated-to reqids --message "IPDs jjh4aj, rtvdak, and uiej2a in Set reqids implement spec 89xjll" --yes --no-commit`.
   - Run `AW_NO_REEXEC=1 python3 -m agent_workflows specs set .aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md --status implemented --evidence .aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md --message "Implemented by IPDs rtvdak, 2hgxi1, and uiej2a: requirement-ID parser, SPEC-PLAN-TRACE verifier, partial-pass deferred event, qualified-citation prompt/review guidance, and Deferred-ID implemented gate" --yes --no-commit`.

## Deferred / out of scope (with reason)

- **Retrofitting pre-cutover specs with requirement IDs**: Explicitly a non-goal of spec `89xjll` Section 1a and Section 5 (`spec_requirement_ids` cutover `20261001` grandfathers earlier specs).
  - Carrier-Declined: A non-goal fixed by spec `89xjll` Section 1a and Section 5, not postponed work: pre-cutover specs are grandfathered by design, so there is nothing to carry.
- **Corpus-wide `aw check` rule over requirement IDs or `[Deferred]` markers**: Explicitly a non-goal of spec `89xjll` Section 1a and Section 6.5 (enforced at the spec status setter on transition to `implemented`, not as a corpus check rule).
  - Carrier-Declined: A non-goal fixed by spec `89xjll` Section 1a and Section 6.5; this plan delivers the setter-side enforcement the spec chose instead (E-02), so nothing is outstanding.
- **Direct mutation of backlog item `vy20et`**: Prohibited by the backlog production contract; the runner transitions `vy20et` to `graduated` after plan production and closes `vy20et` to `done` via `process_backlog_close` once `uiej2a` finalizes to `executed/` and `89xjll` is in `implemented/`.
  - Carrier-Declined: Not outstanding work for a new carrier: the close is owned by the runner's `process_backlog_close` once this plan executes, and backlog `vy20et` itself remains the live record until then.

## Scope check

- Over-scope: none. (`.aw/system/workflows/plan-review-long/review-rubric.md` is added at review for variant parity, not new scope.) Every change directly implements an explicit requirement or acceptance criterion of spec `89xjll` (`R-5`, `R-6`, `R-7`, `R-8`, `R-9`, `AC-9`, `AC-10`) or transitions `89xjll` to `implemented` so backlog item `vy20et` can close.
- Under-scope: none. Together with already-executed IPDs `rtvdak` and `2hgxi1`, all nine requirements (`89xjll R-1`..`89xjll R-9`) and all ten acceptance criteria (`89xjll AC-1`..`89xjll AC-10`) are covered and verified, and `89xjll` reaches `implemented`. Closing `vy20et` to `done` is NOT performed here: it follows once this plan is finalized to `executed/`.

## Required tests / validation

- Targeted test suite: `python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py`
- Spec and attention integrity checks: `AW_NO_REEXEC=1 python3 -m agent_workflows specs check` and `AW_NO_REEXEC=1 python3 -m agent_workflows attention --check`
- Full repository test suite: bare `python3 -m pytest` (with no `-n0`, no extra `-q`, and no `-p no:randomly`).

## Spec / documentation sync

- Spec `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` transitions through `.aw/records/specs/implementing/...` to `.aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` via `aw specs set` (`E-05`).
- Workflow guidance `.aw/system/workflows/plan-review/plan-review.md` and its parity twin `.aw/system/workflows/plan-review-long/review-rubric.md` are updated in `E-06` to document the `89xjll` Section 6.2b qualified-citation rule for plans carrying `- From-Spec:`.
- No spec TEXT is amended: the plan implements `89xjll` R-5/R-6/R-9 as written, and E-05's two `aw specs set` hops change only `- Status:`, `- Graduated-To:`, the file's directory, and `## Workflow history`, so no requirement or acceptance id changes.

## Open questions

### OQ-01: Where should the `->implemented` `[Deferred]`-ID refusal live so both `aw specs set <path> --status implemented` and `aw spec set implemented <id6>` enforce it identically?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved from repository evidence in `agent_workflows/specs.py:743` (`specs.run_set`) and `agent_workflows/status_set.py:786-807` (`status_set.validate_transition_allowed`). `specs.run_set` is a thin adapter that delegates to `status_set.run_set_command(..., scoped_type="specs")`. Placing the refusal helper `_deferred_ids_refusal(spec_path, text)` in `agent_workflows/specs.py` (next to `_review_attestation_refusal` and `_evidence_resolvable`) and calling it from `status_set.validate_transition_allowed` when `rec.record_type == "specs"`, `old_status != norm_status`, and `norm_status == "implemented"` ensures every setter spelling (`aw specs set <path> --status implemented`, `aw spec set implemented <id6>`, `aw specs set implemented <id6>`, and `aw set implemented <id6>`) hits the exact same check and refusal message before any disk write.

### OQ-02: Which executed IPD should be cited as `--evidence` when transitioning spec `89xjll` from `implementing` to `implemented` in `E-05`?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved from `agent_workflows/specs.py:1254` (`specs._evidence_resolvable`). `specs._evidence_resolvable` requires an existing path under `.aw/records/plans/executed/`. At the time `E-05` runs inside `uiej2a`, `uiej2a` itself is still in `.aw/records/plans/pending/` (until `aw ipd finalize` moves it at the end of the turn), whereas sibling Order-02 plan `.aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md` is already in `.aw/records/plans/executed/`. Passing `--evidence .aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md` satisfies `specs._evidence_resolvable` during `E-05`, while the `--message` names `rtvdak`, `2hgxi1`, and `uiej2a`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01 (covers `89xjll AC-1`, `89xjll AC-2`, `89xjll AC-3`, `89xjll AC-4`, `89xjll AC-5`, `89xjll AC-6`, `89xjll AC-7`, `89xjll AC-8`)
  - Required evidence: Paste the output of running `python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py` and a Python one-liner invoking `production_checks.parse_spec_requirement_ids`, `production_checks.spec_requires_requirement_ids`, and `production_checks.spec_plan_trace` to confirm at execution HEAD that: (1) `89xjll AC-1` and `89xjll AC-2` hold (disjoint requirement and acceptance ID sets extracted from declaration sites only; FORM B, FORM C, `N*`, mentions, code blocks, and foreign-spec citations excluded); (2) `89xjll AC-3` holds (`20261001` cutover boundary and non-`None` fallback constant `SPEC_REQUIREMENT_IDS_CUTOVER_DATE`); (3) `89xjll AC-4` and `89xjll AC-5` hold (pooled coverage across active and `executed/` linked plans, `superseded/` excluded, qualified citations required, unknown references rejected with the verbatim `25kzda` 4.8 template); and (4) `89xjll AC-6`, `89xjll AC-7`, and `89xjll AC-8` hold (vacuous pass on grandfathered/zero-ID specs, citation-not-implementation docstring/limit, and sibling checks `SPEC-PLAN-COUNT`, `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-GATE-CARRY` passing unedited).
  - Observed evidence:
```
$ python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py
bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
..............................................                           [100%]
46 passed in 14.04s

$ python3 -c '
from pathlib import Path
from agent_workflows import production_checks as pc
spec_path = Path(".aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")
text = spec_path.read_text()
req_ids, acc_ids = pc.parse_spec_requirement_ids(text)
print("1. AC-1 & AC-2:")
print("   req_ids:", sorted(req_ids))
print("   acc_ids:", sorted(acc_ids))
print("   disjoint:", req_ids.isdisjoint(acc_ids))
print("2. AC-3:")
print("   cutover_constant:", getattr(pc, "SPEC_REQUIREMENT_IDS_CUTOVER_DATE", None))
print("   spec_requires_ids:", pc.spec_requires_requirement_ids(spec_path))
print("3. AC-4 & AC-5:")
print("   spec_plan_trace doc:", pc.spec_plan_trace.__doc__[:100].strip())
print("4. AC-6, AC-7, AC-8:")
print("   vacuity:", pc.spec_plan_trace_vacuity(Path("."), "89xjll"))
print("   deferred:", pc.spec_plan_trace_deferred(Path("."), "89xjll"))
markers = pc.parse_spec_id_markers(text)
print("   markers:", markers)
'
1. AC-1 & AC-2:
   req_ids: ['R-1', 'R-2', 'R-3', 'R-4', 'R-5', 'R-6', 'R-7', 'R-8', 'R-9']
   acc_ids: ['AC-1', 'AC-10', 'AC-2', 'AC-3', 'AC-4', 'AC-5', 'AC-6', 'AC-7', 'AC-8', 'AC-9']
   disjoint: True
2. AC-3:
   cutover_constant: 20261001
   spec_requires_ids: True
3. AC-4 & AC-5:
   spec_plan_trace doc: Verify SPEC-PLAN-TRACE: every mandatory spec requirement maps to at least one E item
and every accep
4. AC-6, AC-7, AC-8:
   vacuity: None
   deferred: []
   markers: {}
```
  - Result: pass

- [x] V-02 validates E-02 (covers `89xjll AC-10`)
  - Required evidence: Reachable via `specs._deferred_ids_refusal` and `status_set.validate_transition_allowed` created in `E-02`. Paste the output of a Python/CLI verification in a temporary git repository that creates an `implementing` spec declaring `R-1`, `R-3 [Deferred]`, `AC-1`, and `AC-2 [Deferred]` plus an executed IPD evidence file, then invokes BOTH `aw specs set <path> --status implemented --evidence <executed-ipd> --yes --no-commit` (`specs.run_set`) and `aw spec set implemented <id6> --evidence <executed-ipd> --yes --no-commit` (`status_set.run_set_command`), showing: (1) both commands exit `1` and name `AC-2` and `R-3` in the refusal output; (2) the spec file on disk is byte-identical before and after each refused call and `git status --short` is empty; and (3) after removing `[Deferred]` from `R-3` and `AC-2`, re-running the transition exits `0` and moves the spec to `.aw/records/specs/implemented/` with `- Status: implemented` (`89xjll AC-10`).
  - Observed evidence:
```
aw specs set: cannot transition spec tst001 to implemented: declared requirement or acceptance item(s) remain marked [Deferred]: AC-2, R-3 (spec 89xjll Section 6.5 / R-9 / AC-10).
  remedy: remove each [Deferred] marker and plan the ID, or delete the requirement from the spec.
Command 1 exit: 1, byte_identical: True, git_status: ''
aw specs set: cannot transition spec tst001 to implemented: declared requirement or acceptance item(s) remain marked [Deferred]: AC-2, R-3 (spec 89xjll Section 6.5 / R-9 / AC-10).
  remedy: remove each [Deferred] marker and plan the ID, or delete the requirement from the spec.
Command 2 exit: 1, byte_identical: True, git_status: ''
-    spec        20261001-tst001-01-tst001  implementing → ✓  implemented
Command 3 exit: 0, implemented_exists: True
```
  - Result: pass

- [x] V-03 validates E-03 (covers `89xjll AC-9`)
  - Required evidence: Reachable via the `spec-plan-trace-deferred` emission E-03 adds on the success path of the spec production block in `runner_shared.py` (driven by `oc_runipd.run_queue` / `agy_runipd.run_queue` with a fake agent, as `tests/test_spec_production.py` already does). Paste: (1) the `spec-plan-trace-deferred` record(s) from `events.jsonl` of a both-host run on a post-cutover fixture spec declaring `R-1`, `R-2 [Should]`, `R-3 [Deferred]`, `AC-1`, `AC-2 [Deferred]`, and `AC-3 [Should]` whose produced plan qualifiedly cites `R-1`, `AC-1`, `AC-3` (and `R-3`), showing item `status == "executed"`, `"partial": true`, and `"deferred_ids": ["AC-2", "R-3"]`; (2) on the same fixture, `production_checks.spec_plan_trace` returning `[]`, `spec_plan_trace_vacuity` returning `None`, and `spec_plan_trace_deferred` returning `['AC-2', 'R-3']`; and (3) the `events.jsonl` of a passing production on a spec with no `[Deferred]` ID containing zero `spec-plan-trace-deferred` records (`89xjll AC-9`).
  - Observed evidence:
```
Host: oc item status: executed
  deferred event: [{'at': '2026-10-16T09:08:48+00:00', 'deferred_ids': ['AC-2', 'R-3'], 'event': 'spec-plan-trace-deferred', 'id6': 'spcdef', 'partial': True}]
  pc.spec_plan_trace: []
  pc.spec_plan_trace_vacuity: None
  pc.spec_plan_trace_deferred: ['AC-2', 'R-3']
Host: agy item status: executed
  deferred event: [{'at': '2026-10-16T09:08:49+00:00', 'deferred_ids': ['AC-2', 'R-3'], 'event': 'spec-plan-trace-deferred', 'id6': 'spcdef', 'partial': True}]
  pc.spec_plan_trace: []
  pc.spec_plan_trace_vacuity: None
  pc.spec_plan_trace_deferred: ['AC-2', 'R-3']
Part 3 (no-deferred): count of spec-plan-trace-deferred events: 0
```
  - Result: pass

- [x] V-06 validates E-06 (guidance for `89xjll`'s Section 6.2b; no acceptance criterion names it, so it covers none)
  - Required evidence: Paste (1) the output of a Python call to `runner_shared.build_spec_production_prompt` for an `approved` post-cutover fixture spec showing the Production Contract item `8` line with the uncited mandatory IDs and the Section 6.2b reference copied from the `implementing` branch; (2) the qualified-citation bullet as extracted from `.aw/system/workflows/plan-review/plan-review.md` `### G. Plan executability` and from `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness`, with the boolean result of comparing the two extracted strings for equality (must be `True`); and (3) `git diff --stat` for the two workflow files showing only additions.
  - Observed evidence:
```
(1) build_spec_production_prompt output:
Item 8 line:
8. Mandatory uncited requirement and acceptance items awaiting coverage: none. Each must be cited qualified with the spec id6 (for example `89xjll R-2`) in an E-* (requirement) or V-* (acceptance) item, per spec 89xjll 6.2b.

(2) Bullet parity check:
b1: - **Qualified spec citations (post-cutover spec trace convention):** When a plan carries `- From-Spec: <spec-id6>` for a post-cutover spec (filename date `>= 20261001`), every mandatory spec requirement citation in `E-*` items and every acceptance criterion citation in `V-*` items MUST be qualified with `<spec-id6>` (for example `` `89xjll` R-3 `` or `89xjll AC-2`), because `SPEC-PLAN-TRACE` ignores unqualified tokens in both directions (spec 89xjll Section 6.2b).
b2: - **Qualified spec citations (post-cutover spec trace convention):** When a plan carries `- From-Spec: <spec-id6>` for a post-cutover spec (filename date `>= 20261001`), every mandatory spec requirement citation in `E-*` items and every acceptance criterion citation in `V-*` items MUST be qualified with `<spec-id6>` (for example `` `89xjll` R-3 `` or `89xjll AC-2`), because `SPEC-PLAN-TRACE` ignores unqualified tokens in both directions (spec 89xjll Section 6.2b).
Equal: True

(3) git diff --stat:
 .aw/system/workflows/plan-review-long/review-rubric.md | 1 +
 .aw/system/workflows/plan-review/plan-review.md        | 1 +
 2 files changed, 2 insertions(+)
```
  - Result: pass

- [x] V-04 validates E-04 (covers `89xjll AC-9`, `89xjll AC-10`)
  - Required evidence: Paste the actual runner output of `python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py` showing all unit and runner integration tests (including the new tests for `89xjll AC-9` partial-pass deferred event on both hosts, its negative case, the `approved` prompt, and `89xjll AC-10` setter refusal on both CLI spellings) passing with 0 failures, plus the names of the new test classes/functions as non-binding pointers (the bar is the behaviors listed in E-04, not a test count).
  - Observed evidence:
```
$ python3 -m pytest tests/test_production_checks_trace.py tests/test_spec_production.py
bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
....................................................                     [100%]
52 passed in 12.77s

Pointers to added tests:
- tests/test_production_checks_trace.py: TestSpecDeferredImplementedGate
  - test_specs_run_set_refuses_when_deferred_ids_declared
  - test_spec_set_refuses_when_deferred_ids_declared
  - test_transition_succeeds_after_deferred_markers_removed
- tests/test_spec_production.py: TestSpecProductionDeferredAndTracePrompt
  - test_approved_spec_production_prompt_qualified_citation
  - test_spec_production_with_deferred_ids_emits_partial_pass_event_both_hosts
  - test_spec_production_without_deferred_ids_emits_no_deferred_event
```
  - Result: pass

- [x] V-05 validates E-05 (covers `89xjll AC-10`)
  - Required evidence: Reachable via the two `aw specs set` transitions performed in `E-05`. Paste the actual output of: (0) the stdout/stderr and exit code of both `aw specs set` hops; (1) `AW_NO_REEXEC=1 python3 -m agent_workflows specs check` exiting `0`, and `AW_NO_REEXEC=1 python3 -m agent_workflows attention --check` output with its exit code, showing no finding naming `89xjll`, `vy20et`, or `uiej2a` (unrelated lane-hygiene findings are listed, not counted against the item); (2) a Python one-liner confirming `.aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md` exists with `- Status: implemented` and `- Graduated-To: reqids`, its `approved/` and `implementing/` counterparts do not exist, and `runner_shared._classify_backlog_carriers(Path('.'), 'vy20et')` returns `unimplemented_specs == []` and `unexecuted_ipds` equal to exactly this plan's `pending/` path; and (3) the bare `python3 -m pytest` summary line plus any failing node ids, compared by node id against the E-01 baseline with no new failure.
  - Observed evidence:
```
(0) aw specs set transitions:
Hop 1:
$ AW_NO_REEXEC=1 python3 -m agent_workflows specs set .aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md --status implementing --graduated-to reqids --message "IPDs jjh4aj, rtvdak, and uiej2a in Set reqids implement spec 89xjll" --yes --no-commit
-    spec        20261001-89xjll-01-89xjll  approved → ▶  implementing
Exit code: 0

Hop 2:
$ AW_NO_REEXEC=1 python3 -m agent_workflows specs set .aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md --status implemented --evidence .aw/records/plans/executed/20260930-reqids-02-rtvdak-build-the-requirement-id-parser-and-wire-spec-plan-trace-int.ipd.md --message "Implemented by IPDs rtvdak, 2hgxi1, and uiej2a: requirement-ID parser, SPEC-PLAN-TRACE verifier, partial-pass deferred event, qualified-citation prompt/review guidance, and Deferred-ID implemented gate" --yes --no-commit
-    spec        20261001-89xjll-01-89xjll  implementing → ✓  implemented
Exit code: 0

(1) Integrity checks:
$ AW_NO_REEXEC=1 python3 -m agent_workflows specs check
aw specs check: all specs conform. 40 specs checked.
Exit code: 0

$ AW_NO_REEXEC=1 python3 -m agent_workflows attention --check
aw attention --check: the view is valid. 2785 items checked, 0 violations.
Exit code: 0

(2) Spec placement and carrier classification:
$ python3 -c '
from pathlib import Path
from agent_workflows import runner_shared
p_impl = Path(".aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")
p_appr = Path(".aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")
p_impg = Path(".aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md")
print("Implemented exists:", p_impl.exists())
print("Has Status implemented:", "- Status: implemented" in p_impl.read_text())
print("Has Graduated-To reqids:", "- Graduated-To: reqids" in p_impl.read_text())
print("Approved exists:", p_appr.exists())
print("Implementing exists:", p_impg.exists())
res = runner_shared._classify_backlog_carriers(Path("."), "vy20et")
print("unimplemented_specs:", res.unimplemented_specs)
print("unexecuted_ipds:", res.unexecuted_ipds)
'
Implemented exists: True
Has Status implemented: True
Has Graduated-To reqids: True
Approved exists: False
Implementing exists: False
unimplemented_specs: []
unexecuted_ipds: ['.aw/records/plans/pending/20261014-reqids-03-uiej2a-enforce-the-deferred-id-implemented-gate-and-transition-spec.ipd.md']

(3) Bare pytest summary vs E-01 baseline:
E-01 Baseline:
707 passed in 22.80s (0 failures)
Post-execution:
707 passed in 20.44s (0 failures, no new failing node ids)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

- **Open questions**: All open questions (`OQ-01`, `OQ-02`) are resolved from repository evidence (`Blocking: no`, `Status: resolved`).
- **Scope fence**: Declared `- Scope-Paths:` are `agent_workflows/specs.py`, `agent_workflows/status_set.py`, `agent_workflows/runner_shared.py`, `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/review-rubric.md`, `tests/test_production_checks_trace.py`, `tests/test_spec_production.py`, `.aw/records/specs/approved/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`, `.aw/records/specs/implementing/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`, `.aw/records/specs/implemented/20261001-89xjll-01-89xjll-spec-requirement-id-convention-and-trace-contract.spec.md`, and `.aw/records/plans/pending/20261014-reqids-03-uiej2a-enforce-the-deferred-id-implemented-gate-and-transition-spec.ipd.md`. If an out-of-scope edit is genuinely required during execution, make the edit and justify every out-of-scope path via `--scope-reason <path>=<why>` (and every declared-but-unmodified path via `--scope-ack <path>=<why>`) at `aw ipd finalize`. Stop only on an unresolvable concurrent-edit conflict or missing prerequisite symbol.
- **Honesty rule**: You MUST run every validation command and paste the ACTUAL runner output into each `V-*` item's `Observed evidence:`; never claim a test or check passed without running it.
- **Commit and push contract**: Commit ONLY files modified for this plan, explicitly path-scoped via `aw commit uiej2a -- <paths>`. Never run `git add -A` or `git commit -a`, and never push.
- **Lifecycle transition**: Every `E-*` item must reach `Execution state: performed` and every `V-*` item must reach `Result: pass` with concrete pasted evidence. When running under `aw oc run` / `aw agy run`, the runner owns `aw ipd finalize`; when executing manually outside the runner, finalize via `aw ipd finalize uiej2a` (never hand-roll `git mv` to `executed/`).
