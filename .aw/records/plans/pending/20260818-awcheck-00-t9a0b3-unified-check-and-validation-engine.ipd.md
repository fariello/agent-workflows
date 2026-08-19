# IPD: unified check and validation engine

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Build the ENGINE behind the `aw check` verb from spec 20260818-1525-01 and satisfy the maintainer's validation TODO items (6, 11, 19, 20, 23). Today validation is scattered across per-type tools with inconsistent scope, messages, and flags: specs.run_check (specs.py:296), backlog.run_check (backlog.py:442, which alone does an id6 dup check at backlog.py:447-463), plans_index.check_drift (plans_index.py:235), research_index.check_drift (research_index.py:231), and the shipped normalize_plan_names.is_conformant/parse_name. Cross-tree id6 uniqueness is checked ONLY inside attention.scan (attention.py:153-163), there is NO setid collision check anywhere, `aw ipd lint` does not verify filename conformity, and normalize_plan_names still prints a stale grammar message (normalize_plan_names.py:677) with no --allow-legacy escape. This Set unifies those into one engine, per type, emitting the shared Drift convention (artifact_core.py:247, drift_exit_code:262, render_agent_drift:255; exit 0 clean / 1 findings / 2 cannot-run).
- Scope: The check/validation engine and its integration points. IN: a unified engine module that, per artifact TYPE, composes name-conformity + front-matter/status conformity + reference-integrity by reusing the existing per-type validators as sub-checks and emitting Drift; a cross-tree id6 AND setid uniqueness verifier generalized from attention's id6 dedup; a --legacy/--allow-legacy flag on every check path; the stale-message fix (normalize_plan_names.py:677); and making `aw ipd lint` call name-conformity. OUT: the `aw check <type>` VERB GRAMMAR + argv routing (Set A / awcmdsurf owns the parser and dispatch; this Set is the engine it dispatches INTO); the selector grammar internals (Set E / awselect); color/pretty output (Set C); help-text quality (Set B). This Set is referenced by Set A (awcmdsurf), whose Order 02 routes `aw check` into this engine.
- Status: reviewed
- Set: awcheck
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: t9a0b3

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level orchestrator skeleton from spec 20260818-1525-01 + validation TODO items 6,11,19,20,23; children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; PR-001 (all cited anchors + negative claims verified against source). Fixed a false/unsatisfiable evidence requirement: completion criteria + V-01 demanded `aw check` verb output, but this Set builds the ENGINE only (the verb is Set A's, and does not exist when this Set completes) - rewrote both to require engine-API + real-verb (`aw ipd lint`, normalize_plan_names) evidence; aligned the Order-01 child-table row to the pure-engine reality. Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Provide ONE coherent validation engine behind `aw check <type>` so that, per artifact type, the toolkit
uniformly verifies filename-grammar conformity, front-matter/status conformity, reference integrity, and
global id6/setid uniqueness, all through the shared Drift convention with consistent exit codes and a
uniform --legacy escape hatch, replacing today's scattered and inconsistent per-type checks and stale
messages.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..03 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits and never pushing. Sequence so the engine core (01) lands first, then the collision verifier (02) plugs in as a sub-check, then the legacy flag + message fix + ipd-lint integration (03) wire across all paths. On completion, confirm `aw check <type>`, `aw check <type> names`, and `aw check all` route through the unified engine, that id6/setid collisions and name nonconformity are caught, that --legacy behaves, and that the stale message is gone.
  - Depends on: none
  - Expected outcome: Orders 01..03 executed; the unified engine backs Set A's `aw check` verb; name + front-matter + reference + collision checks all emit Drift with correct exit codes; --legacy works everywhere; stale message fixed; full suite + all --check green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split so the engine core lands first, the collision verifier plugs in as a sub-check, then the
cross-cutting flag/message/integration work wires across all paths. Each child is marked "(to scaffold)"
and will be fleshed out to line-level detail later.

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260818-awcheck-01-iw1wlx (fleshed) | A unified check engine module (`check_engine.py`) that, per TYPE, composes name-conformity + front-matter/status conformity + reference-integrity as sub-checks and RETURNS the shared Drift list (artifact_core.py:247). Reuses existing per-type validators (specs.validate_spec specs.py:128, backlog.validate_item backlog.py:129, plans_index.check_drift plans_index.py:235, research_index.check_drift research_index.py:231, normalize_plan_names.is_conformant/parse_name) rather than reimplementing them; `check_types(["all"])` fans out over every applicable type. The engine is PURE (returns Drift, never prints); `drift_exit_code` (artifact_core.py:262) / `render_agent_drift` (:255) rendering + exit-code mapping live in the CLI verb layer (Set A / awcmdsurf), not the engine. + tests. | none |
| 02 | (to scaffold) awcheck-collisions | A cross-tree id6 AND setid uniqueness verifier. Generalize attention's id6 dedup (attention.py:153-163) into a reusable collision sub-check the engine can run for a type or for `all`; ADD setid collision detection (none exists today) with a clear duplicate report. Reuse backlog's existing id6 dup logic (backlog.py:447-463) as a pattern. + tests. | 01 |
| 03 | (to scaffold) awcheck-legacy-and-messages | Add a --legacy/--allow-legacy flag to ALL check paths (item 20) so legacy-named files (YYYYMMDD-HHMM-NN-<slug>.md) pass without findings; fix the stale message at normalize_plan_names.py:677 ("All scanned plan/prompt filenames conform to YYYYMMDD-HHMM-NN-<slug>.md.") to reflect the current grammar and honor the legacy flag (item 11); make `aw ipd lint` call the engine's name-conformity sub-check (item 6). + tests. | 01, 02 |

## Completion criteria (the whole Set is done only when)

- Orders 01..03 executed.
- The unified engine's PUBLIC API (`check_engine.check_type(repo_root, type, names_only=..., legacy=...)` and `check_types(..., ["all"])`) runs name + front-matter/status + reference sub-checks per type, `names_only=True` runs ONLY name-conformity, and `["all"]` fans out over every applicable type, all RETURNING the shared Drift list (item 19). Exit-code mapping (0 clean / 1 findings / 2 cannot-run via `drift_exit_code`) is asserted at the engine boundary; the `aw check` VERB that renders it belongs to Set A (awcmdsurf) and is verified there, NOT here (this Set is a dependency of that verb, so `aw check` does not yet exist when this Set completes).
- A duplicate id6 OR a duplicate setid anywhere in the tracked trees is reported as a Drift finding by the collision verifier (item 23); the generalized verifier subsumes attention's id6 check.
- The engine's name-conformity sub-check honors `legacy=True`, letting legacy-named files pass cleanly (item 20).
- The stale normalize_plan_names message is corrected and grammar-accurate (item 11, verified via the shipped tool directly); `aw ipd lint` verifies filename conformity (item 6, verified via the real `aw ipd lint` verb this Set touches).
- Full serial suite green; the engine's public API + Drift shape are stable for Set A's `aw check` verb routing to consume.

## Cross-IPD validation

- Order 01 (engine core) MUST land before Order 02 plugs the collision verifier in as a sub-check, and before Order 03 wires the legacy flag / message fix / ipd-lint integration across all paths. Re-run the full suite after each Order.
- Cross-Set: Set A (awcmdsurf) Order 02 routes `aw check <type>` into THIS engine; the engine's public entry points and Drift shape must be stable for that routing. The verb GRAMMAR and argv dispatch belong to Set A, not here; this Set must not add or rename verbs.
- Reuse discipline: the engine composes the existing per-type validators as sub-checks rather than forking them, so a fix in specs/backlog/plans_index/research_index flows through automatically.

## Deferred / out of scope (with reason)

- The `aw check` verb grammar + argv routing: Set A (awcmdsurf), which dispatches into this engine.
- The selector grammar internals (id6/setid/filename/status + multiple targets): Set E (awselect).
- Help-text quality: Set B (awhelp). Color/pretty output: Set C (awcolor).
- The deep-inspection `aw doctor` (TODO item 33): a separate concern; this Set is the per-type check engine `doctor` may later consume, not doctor itself.

## Scope check

- Over-scope: none. Every Order maps to spec 20260818-1525-01's `check` verb engine and to TODO items 6, 11, 19, 20, 23; the verb grammar, selectors, help, color, and doctor are explicitly delegated elsewhere.
- Under-scope: none. The three Orders cover the unified engine core (name + front-matter + reference), the cross-tree id6/setid collision verifier, and the cross-cutting legacy flag + stale-message fix + ipd-lint name-conformity integration, which together satisfy all five referenced TODO items.

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria. E-01's verification runs the full serial suite
and demonstrates the engine end to end: `aw check <type>`, `aw check <type> names`, and `aw check all`
emitting Drift with correct exit codes; a seeded duplicate id6 and a seeded duplicate setid both reported;
--legacy passing a legacy-named fixture; the corrected normalize_plan_names message; and `aw ipd lint`
flagging a nonconformant filename.

## Open questions

### OQ-01: Does `aw check <type>` (no `names`) include the cross-tree collision check by default, or only under `all`?

- Blocking: no
- Status: open
- Owner: maintainer (resolve at Order 02)
- Resolution or deferral rationale: Recommendation: run the id6/setid collision sub-check on every `aw check <type>` scoped to that type's tree, and the full cross-tree collision scan under `aw check all`, since collisions across types can only be proven globally. Non-blocking; the engine surfaces collisions either way and the exact default is a small policy choice settled during Order 02.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three child Orders show `Status: executed` under `.aw/records/plans/executed/`; paste ENGINE-API smoke output (a Python call, not the `aw check` verb, which is Set A's): `check_engine.check_type(root,"plans")`, `check_type(root,"plans",names_only=True)`, and `check_types(root,["all"])` each returning a Drift list, plus `drift_exit_code(...)` mapping to 0/1/2; paste a `check_collisions(root)` run over a seeded duplicate id6 AND a seeded duplicate setid, each reported as a Drift finding; paste an engine name-check with `legacy=True` passing a legacy-named fixture that is flagged without the flag; paste the corrected `normalize_plan_names` message from the shipped tool (no stale "YYYYMMDD-HHMM-NN-<slug>.md" claim); paste `aw ipd lint <nonconformant-filename>` flagging it (real verb this Set touches); and paste the full serial suite tail green. Do NOT require `aw check` verb output here (that verb is created + verified in Set A / awcmdsurf).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: three Orders for one coherent objective (the unified check/validation engine), split so intermediate states stay runnable and each is independently reviewable: the engine core composes existing per-type validators, the collision verifier plugs in as a sub-check, and the cross-cutting legacy flag + message fix + ipd-lint integration wire the engine across all paths. They share one engine module and one Drift contract, so splitting into separate Sets would fragment a single objective.

Execution requires human approval (`Status: approved` + an attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, OWNS all verification + path-scoped
commits, and NEVER pushes, moving each Order (and finally this orchestrator) to `executed/` only after
`aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted evidence. Large
mechanical Orders may be handed to Gemini via `agy` (blocking), but opencode OWNS verification and commits
and never trusts a report on faith. RELEASE-relevant: this engine backs Set A (awcmdsurf)'s `aw check`
verb, which is a release blocker, so this Set must land (or be explicitly waived) before that Set's
cutover can complete.
