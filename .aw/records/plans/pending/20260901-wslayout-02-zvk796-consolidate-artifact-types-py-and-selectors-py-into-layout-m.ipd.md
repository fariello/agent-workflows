# IPD: Consolidate artifact_types.py and selectors.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `artifact_types.py` and `selectors.py` maintain separate hardcoded sets of artifact types, aliases, and excluded directories. Sourcing them from `layout.py` removes duplication while maintaining exact backward compatibility.
- Scope: Refactor `agent_workflows/artifact_types.py` and `agent_workflows/selectors.py` to import constants and helper logic from `agent_workflows/layout.py`.
- Scope-Paths: agent_workflows/artifact_types.py, agent_workflows/selectors.py
- Item-Dependencies: executed:wpu5zu
- Status: approved
- Readiness: go-pending-approval
- Set: wslayout
- Order: 2
- Highest E allocated: 02
- Author: antigravity
- Id: zvk796
- Approval: 2026-09-05, recorded via aw ipd set: status set to approved
- From-Spec: kw5y2s

## Workflow history
- 2026-09-05 approved (aw set): status set to approved
- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 6: APPROVE WITH REVISIONS APPLIED; PR-101, PR-102; GO - PENDING HUMAN APPROVAL. Verified at HEAD `16777ccc`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. Lint conforming at `--phase author` before and `--phase review-finalize` after. EVERY CHECKABLE CLAIM RE-MEASURED LIVE rather than trusted: `ARTIFACT_TYPES` is the 10 types claimed and DOES contain `roadmaps`; `normalize_type('roadmap')` -> `roadmaps`; `EXCLUDED_RECORD_DIRS` is exactly the 7 pinned entries; `KNOWN_PRIMARY_TYPES` is 9; `NON_PRIMARY_RECORD_DIRS == {'reviews'}`; and `aw check reviews` does still error with "unknown artifact type", so F-4's net-new-behavior claim is current. `layout.py` correctly does not exist yet (Order 01 creates it). ONE MATERIAL FINDING (PR-101, HIGH, fixed): E-02 instructed sourcing the three INPUT sets from `layout.py` but never named `_OTHER_SWEEP_SKIP_DIRS` (`selectors.py:183`), the UNION of those three that the `other` complement actually consults (`:215`). Re-sourcing the inputs silently redefines the union, and V-02 asserted only the 7 exclusions - so a derivation that dropped `reviews` from the union would have PASSED validation while re-opening a measured outage: with `reviews` in neither set, a bare id6 matched twice and `aw set approved <id6>` refused for ALL 28 reviewed plans until `d802e917` added the third set. E-02 now requires the union stay derived, and V-02 now demands the union, the `other`-resolves-empty check, the single-match check, and `tests/test_selector_resolver_matrix.py`. Also recorded (PR-102, F-8): `reviews` is ALREADY a `RecordClass` member while absent from `ARTIFACT_TYPES`, so the union ruling RECONCILES two live vocabularies rather than adding to one. No blocking question; OQ-01 resolved.
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019, PR-022, PR-023 fixed (added ten-clause execution contract, structured findings evidence table, conventions, bare-suite validation with baseline re-measurement, and readiness).
- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-001 (would delete shipped `roadmaps` noun), PR-005 (silently widens EXCLUDED_RECORD_DIRS), PR-006 (no bare-suite V-item), PR-007 (Item-Dependencies: none contradicts orchestrator).
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

## Goal

Consolidate `artifact_types.py` and `selectors.py` to consume the single source of truth in `layout.py` without breaking any existing imports or tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refactor artifact_types.py

- [ ] E-01 Update `agent_workflows/artifact_types.py` to derive `ARTIFACT_TYPES`, `_ALIASES`, `is_type_token()`, and `normalize_type()` directly from `agent_workflows/layout.py`, preserving all function signatures and exception types.
  - Depends on: none
  - Expected outcome: `artifact_types.py` re-exports the layout model definitions seamlessly.
  - Execution state: pending
  - Set-level prerequisite: `wpu5zu` must be executed first; see `- Item-Dependencies:` in the metadata.
  - NON-NEGOTIABLE (plan-review PR-001, maintainer ruling 2026-09-01): `roadmaps` MUST survive in
    `ARTIFACT_TYPES`, and `roadmap` MUST survive in `_ALIASES`. The draft spec's table omits them; the
    ruling is UNION, so derivation MUST NOT narrow this tuple. Deleting `roadmaps` would break
    `run_rename_roadmaps` / `run_group_roadmaps`
    (`agent_workflows/artifact_rename.py:827-828,855-856`) and orphan 5 on-disk artifacts.
  - `reviews` becomes an ACCEPTED type token by this derivation (it is in the layout model but not in
    today's `ARTIFACT_TYPES`), which is net-new behavior: `aw check reviews` currently fails with
    "unknown artifact type 'reviews'". That is intended per the union ruling and MUST be covered by
    V-01, not left as an accident.

### Task group 2: Refactor selectors.py

- [ ] E-02 Update `agent_workflows/selectors.py` to source `KNOWN_PRIMARY_TYPES`, `NON_PRIMARY_RECORD_DIRS`, and `EXCLUDED_RECORD_DIRS` from `agent_workflows/layout.py`.
  - Depends on: E-01
  - Expected outcome: `selectors.py` uses the canonical layout exclusions and types.
  - Execution state: pending
  - TRAVERSAL EXCLUSIONS ARE A BEHAVIOR DECISION, NOT A PURE MOVE (plan-review PR-005). Today
    `EXCLUDED_RECORD_DIRS` = `.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`
    (7 entries). The draft spec additionally lists `node_modules`, `venv`, `.venv` (`kw5y2s:88-90`).
    `wpu5zu` deliberately pins the model to the CURRENT 7 so this consolidation is behavior-preserving.
  - Therefore: EITHER keep the 7 exactly (default; V-02 asserts equality), OR widen to 10 as an
    EXPLICIT, stated change and update the `wpu5zu` parity test in the same commit. Do NOT let the set
    change as a side effect of "sourcing from the model". Whichever is chosen, V-02 must paste the
    resulting set.
  - THE DERIVED SET IS THE ONE THAT ACTUALLY GATES THE SWEEP, and this item names only its three
    INPUTS (found at plan-review 2026-09-04, PR-101). `selectors.py` computes
    `_OTHER_SWEEP_SKIP_DIRS = KNOWN_PRIMARY_TYPES | NON_PRIMARY_RECORD_DIRS | EXCLUDED_RECORD_DIRS`
    (`selectors.py:183`) and the `other` catch-all consults THAT union, not the three sets
    individually (`:215`). So re-sourcing the inputs from `layout.py` silently redefines the derived
    set too. Keep `_OTHER_SWEEP_SKIP_DIRS` computed from whatever the three sets become, never
    hardcoded, and never bypassed by a fourth direct membership test.
  - WHY THIS IS LOAD-BEARING RATHER THAN TIDINESS: that union is what stops the `other` complement
    from swallowing `.aw/records/reviews/`. When `reviews` was in NEITHER the primary types nor the
    exclusions, a bare id6 matched TWICE (the plan as `plans`/id6 and its own review record as
    `other`/substring) and `aw set approved <id6>` refused with "id6 collision ... a data bug to fix,
    not overridable by --force", for ALL 28 reviewed plans. Fixed 2026-09-04 in `d802e917` by adding
    the third set. A derivation that drops `reviews` from the union re-opens exactly that outage, and
    it would NOT be caught by V-02's exclusion-set assertion, which never looks at the union.
  - V-02 therefore asserts the union AND the collision, not just the 7 exclusions.

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_types.py`: closed TYPE-noun vocabulary and verb routing.
- `agent_workflows/selectors.py`: shared selector resolver.
- Controlling spec `kw5y2s` is `approved` again (re-measured at round 5; the round-4 `to-review` claim is stale, the correction having been re-approved `--by-human` after these plans were demoted). Its UNION vocabulary and GITIGNORED rulings are unchanged, and the spec is immutable during execution.
- `KNOWN_PRIMARY_TYPES` is 9 members (`ARTIFACT_TYPES` minus `other`), sourced from `layout.py` (PR-015).
- `NON_PRIMARY_RECORD_DIRS = frozenset({"reviews"})` exists in `selectors.py` to prevent `other` from capturing review records and colliding with plan id6 resolution; sourcing from `layout.py` must preserve this isolation.
- `EXCLUDED_RECORD_DIRS` is pinned to the current 7 entries (`runs`, `scratch`, `tmp`, `temp`, `.git`, `.system_generated`, `__pycache__`) per maintainer ruling OQ-01.
- Python 3.9 is the floor (`pyproject.toml:12`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **Consolidating `artifact_types.py` and `selectors.py` onto `layout.py` removes duplication without breaking existing imports or tests.** Re-exporting preserves backward compatibility across the entire repository. | `agent_workflows/artifact_types.py:12-40`; `agent_workflows/selectors.py:120-185`. |
| F-2 | **The union vocabulary preserves `roadmaps` and `roadmap` alias.** Deleting `roadmaps` would break `run_rename_roadmaps` / `run_group_roadmaps` and orphan 5 on-disk artifacts. | `artifact_rename.py:827-828,855-856`; `.aw/records/roadmaps/`. |
| F-3 | **Traversal exclusions stay at seven per maintainer ruling OQ-01.** Sourcing exclusions from `layout.py` must not silently widen to include `node_modules`, `venv`, or `.venv`. | `selectors.py:168-178`; maintainer resolution on OQ-01. |
| F-4 | **`reviews` becomes an accepted type token by derivation**, allowing `aw check reviews` to succeed (net-new behavior enabled by the union vocabulary). | `artifact_types.py:42-60`; `aw check reviews`. |
| F-5 | **Resolver isolation for `NON_PRIMARY_RECORD_DIRS` (`reviews`) must be preserved** so that `_OTHER_SWEEP_SKIP_DIRS` continues to prevent `other` from capturing `.review.md` files. | `selectors.py:140-185`. |
| F-6 | **Concurrent scope must be measured at execution time.** The prior `e32j35` example is superseded; inspect current pending declarations for `selectors.py` immediately before editing. | Current pending-plan board. |
| F-7 | **FOUND AT PLAN-REVIEW 2026-09-04 (PR-101). E-02 named the three INPUT sets but not the DERIVED set that actually gates the sweep.** `selectors.py:183` computes `_OTHER_SWEEP_SKIP_DIRS = KNOWN_PRIMARY_TYPES \| NON_PRIMARY_RECORD_DIRS \| EXCLUDED_RECORD_DIRS`, and the `other` complement consults THAT union (`:215`), not the three sets individually. Re-sourcing the inputs silently redefines the union, and V-02 as written asserted only the 7 exclusions, so a derivation that dropped `reviews` from the union would PASS validation while re-opening a measured outage: with `reviews` in neither set, a bare id6 matched twice and `aw set approved <id6>` refused for ALL 28 reviewed plans until `d802e917` added the third set. E-02 and V-02 now cover the union and the collision. | `selectors.py:183`, `:215`; `d802e917`; `tests/test_selector_resolver_matrix.py` (`OtherCatchAllDoesNotClaimTypedTreesTests`) |
| F-8 | **`reviews` is ALREADY a `RecordClass` member, so `record_producers` and `artifact_types` disagree TODAY.** Measured: `RecordClass` has 9 members including `REVIEWS`, while `artifact_types.ARTIFACT_TYPES` has 10 and does NOT include `reviews` (`aw check reviews` errors with "unknown artifact type"). So the union ruling does not merely ADD a token to one vocabulary; it RECONCILES two live vocabularies that already differ. Recorded so an executor does not read F-4's "net-new behavior" as meaning nothing consumes `reviews` yet. | `record_producers.RecordClass` (9 members, `REVIEWS` present with its own comment); `artifact_types.ARTIFACT_TYPES` (10, no `reviews`); `aw check reviews` -> error |

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/artifact_types.py` (E-01).
2. Refactor `agent_workflows/selectors.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring `record_producers.py` and `project_schema.py` is in Order 03 (rodj06).

## Scope check

- Over-scope: none. Both files are strictly internal refactors re-exporting canonical constants from `layout.py`.
- Under-scope: none.
- Concurrent-scope collision: the prior `e32j35` example is superseded. Re-measure current pending declarations immediately before execution.

## Required tests / validation

- `python3 -m pytest tests/test_awcmdsurf_vocab_and_parsers.py tests/test_selector_resolver_matrix.py` passing, with actual output pasted.
- Bare full repository suite `python3 -m pytest` from the PRIMARY checkout, with baseline re-measured on unmodified HEAD at execution time.
- `aw check --agent` showing no new diagnostic class (expecting the six `tk1gqo` reports).
- `aw sanitize --agent` passing clean.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1. Spec is `approved`; do NOT edit it.
- No user-facing documentation changes owned by this internal refactor.

## Open questions

### OQ-01: Keep the seven current traversal exclusions, or widen to ten?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-005
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: keep the seven exclusions exactly. This consolidation preserves current selector behavior; adding `node_modules`, `venv`, and `.venv` would be a separate policy change that needs its own evidence and regression coverage. `selectors.EXCLUDED_RECORD_DIRS` therefore remains the source behavior that E-02 reproduces.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_awcmdsurf_vocab_and_parsers.py` passes cleanly, with the ACTUAL runner output pasted (file verified to exist at review time).
  - PLUS the no-narrowing proof (PR-001), pasted:
    `python3 -c "from agent_workflows import artifact_types as AT; print(sorted(AT.ARTIFACT_TYPES)); print('roadmaps:', 'roadmaps' in AT.ARTIFACT_TYPES, '| roadmap alias:', AT.normalize_type('roadmap'))"`
    Required result: the printed tuple still contains all 10 pre-existing types INCLUDING `roadmaps`,
    and `normalize_type('roadmap')` returns `roadmaps`.
  - PLUS the intended net-new surface: `aw check reviews` no longer errors with "unknown artifact type",
    output pasted.
  - PLUS the BARE FULL SUITE (PR-006), because "100% backward compatibility" cannot be proven by two
    narrow files: run `python3 -m pytest` (bare; addopts already supply `-q -n auto --dist=worksteal -m 'not slow'`)
    and paste the `N passed` summary line, with zero regressions against the pre-change baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest tests/test_selector_resolver_matrix.py` passes cleanly, with the ACTUAL runner output pasted (file verified to exist at review time).
  - PLUS the exact exclusion set (PR-005), pasted:
    `python3 -c "from agent_workflows import selectors as S; print(tuple(S.EXCLUDED_RECORD_DIRS))"`
    Required result: either the unchanged 7-entry set, or the deliberately widened 10-entry set WITH the
    `wpu5zu` parity test updated in the same commit. A set that changed without a stated decision is a
    FAILED validation, not a pass.
  - PLUS THE DERIVED UNION AND THE COLLISION IT PREVENTS (PR-101). The exclusion set alone does not
    prove the sweep is still correct, because the sweep reads the UNION. Paste all three:
    `python3 -c "from agent_workflows import selectors as S; print(sorted(S._OTHER_SWEEP_SKIP_DIRS))"`
    showing `reviews` is present and the union equals
    `KNOWN_PRIMARY_TYPES | NON_PRIMARY_RECORD_DIRS | EXCLUDED_RECORD_DIRS`;
    `python3 -c "from pathlib import Path; from agent_workflows import selectors as S; print(S.resolve(Path('.'),'other','2r306y').paths)"`
    returning an EMPTY list (a review record must not resolve as `other`);
    and `python3 -c "from pathlib import Path; from agent_workflows import status_set as SS; r=SS.inventory_all_artifacts(Path('.')); print([m.record_type for m in SS.match_selector('2r306y',r,Path('.'))])"`
    returning exactly `['plans']`. A second match here is the 28-plan `aw set` outage regressing
    (`d802e917`), and `tests/test_selector_resolver_matrix.py` already pins it - so run that file too
    and paste its result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS CLEARED (re-measured at plan-review round 5): controlling spec `kw5y2s` is `- Status: approved` with a `--by-human` attestation, so `ipd-lifecycle.md:16` is satisfied. The round-4 "reopened" wording was accurate when written and then outlived its premise: the plans were demoted at commit `298be4b2` (00:10:38 -0400) and the corrected spec was re-approved 459 seconds later at `3e05c2ba` (00:18:17 -0400). RE-VERIFY the spec's `- Status:` line yourself before starting rather than trusting this paragraph; if it is not `approved`, STOP (a genuinely absent prerequisite). The only remaining gate is ordinary human approval of this plan.

Execution contract:

1. Human approval of this plan is required before execution. There are no unresolved blocking questions: OQ-01 is `Status: resolved` by the maintainer.
2. Serial prerequisite: `wpu5zu` (Order 01) MUST reach `executed` before starting this plan, as this plan imports `agent_workflows/layout.py`.
3. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EXECUTION: the prior `e32j35` example is superseded, so inspect current pending declarations for `agent_workflows/selectors.py`. If concurrent edits are in flight, verify mergeability before editing.
4. Non-narrowing invariant: `roadmaps` MUST survive in `ARTIFACT_TYPES` and `roadmap` in `_ALIASES` (PR-001).
5. Exclusions invariant: Keep exactly the 7 current exclusions per maintainer ruling OQ-01.
6. Validation requires ACTUAL pasted runner output; never claim a pass without running the commands.
7. Shared checkout discipline: commit only files this plan changed, path-scoped. Verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged`. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
8. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
9. Scope fence: declared paths are `agent_workflows/artifact_types.py` and `agent_workflows/selectors.py`. An out-of-scope edit requires `--scope-reason`, and an unmodified declared path requires `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a concurrent-edit conflict cannot be safely combined.
10. Expect the `check.lifecycle-transition-invalid` diagnostic; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
11. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
