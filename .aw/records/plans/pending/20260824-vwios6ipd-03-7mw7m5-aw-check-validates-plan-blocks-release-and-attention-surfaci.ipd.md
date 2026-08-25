# IPD: aw check validates plan Blocks-Release and attention surfacing

- Date: 2026-08-24
- Kind: child
- Concern: `aw check`'s blocks-release dangling-reference validation (`releases.check_blocks_release`, `releases.py:137-162`) scans only the backlog and specs trees; the plans tree is NOT scanned, so a plan carrying a dangling `- Blocks-Release:` (pointing at a non-existent release) is never flagged. AGENTS.md and the vwios6 acceptance criteria require `aw check` to validate a plan's Blocks-Release the same as backlog/specs. Separately, `aw attention`'s `release_blockers` scan (`attention.py:477-494`) already recognizes any artifact carrying the field, so a plan carrying it should surface once child 02 can persist it; this child confirms that surfacing end to end.
- Scope: Extend `aw check` so a plan's `Blocks-Release` is validated (clean when it resolves via `releases.resolve_release`, flagged `check.blocks-release-dangling` when it does not), reusing the existing shared release-resolution logic; and add coverage confirming `aw attention` lists a plan carrying `Blocks-Release: next` in the release-blocker set. Child 03 of the vwios6ipd Set; depends on schema child 01 and setter child 02.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/check_engine.py, tests/test_blocks_release.py, tests/test_attention_priority_blocker.py
- Status: approved
- Set: vwios6ipd
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 7mw7m5
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (plans reader blocks_release population + corrected convention), PR-002 (check-all sweep gating in E-01/V-01)
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 03 of vwios6ipd Set (check validation + attention surfacing).

## Goal

Close the last release-gate-parity gap for plans: make `aw check` validate a plan's `Blocks-Release` reference the same way it validates backlog/specs, and confirm `aw attention` surfaces a release-blocking plan, so all three enforcement surfaces (lint, setter, check/attention) agree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Validate plan Blocks-Release in aw check

- [ ] E-01 Extend the plan tree into the blocks-release dangling check. Choose the lower-drift option at execution time: either (a) add `.aw/records/plans` to the directories scanned by `releases.check_blocks_release` (`releases.py:137-162`, currently backlog+specs only), or (b) add a plan-side check via the `check_engine.check_refs` per-type seam (`check_engine.py:197-205`). Reuse `releases.resolve_release` and emit the existing `Drift(path, "check.blocks-release-dangling", ...)` code for a plan whose value does not resolve. Note the invocation gating: `check_blocks_release` is invoked only in the full cross-tree sweep (`check_engine.py:601-604`, run when `collisions` is set, which the `["all"]` sentinel forces at `check_engine.py:585-587`); it does NOT run for a single type-scoped `aw check plans`. Option (a) inherits that same gating (fires on `aw check all`); if option (b) is chosen, it rides the per-type `check_refs` path and may run under type-scoped checks too - either is acceptable, but the executor MUST validate with the command that actually triggers the check (see V-01).
  - Depends on: none
  - Expected outcome: `aw check all` (the full sweep) on a repo with a plan carrying a dangling `- Blocks-Release:` reports `check.blocks-release-dangling`; a plan whose value resolves (`next` -> the single planned release, or a live id6) is clean.
  - Execution state: pending

### Task group 2: Confirm attention surfacing for plans

- [ ] E-02 Populate `Item.blocks_release` in the plans reader for display parity, and confirm end-to-end surfacing. Verified during review: `release_blockers` (`attention.py:477-494`) re-reads each item's FILE with a regex, so a release-blocking plan already appears in the release-blocker SET without any reader change; BUT the plans reader `_plans_record` (`attention.py:262-301`) constructs its `Item` WITHOUT `blocks_release` (it defaults to `None`), UNLIKE the specs reader (`attention.py:249,258`) and backlog reader (`attention.py:369`) which both populate it. Because the display glyph (`rb_glyph = ">" if it.blocks_release`, `attention.py:622`) and the `[blocking]` label (`attention.py:649-650`) key off `Item.blocks_release`, a release-blocking plan would surface WITHOUT the `>` glyph / `[blocking]` label, inconsistent with backlog/specs. Fix: populate `blocks_release` in `_plans_record` consistent with the specs/backlog readers (read the `- Blocks-Release:` line from the plan text and pass it as the `blocks_release=` kwarg). Do NOT change attention's core scan regex.
  - Depends on: none
  - Expected outcome: a plan carrying `- Blocks-Release: next` appears in `aw attention`'s outstanding release-blocker set for release f33nrj AND renders with the `>` glyph and `[blocking]` label, identical to a backlog/spec release blocker.
  - Execution state: pending

### Task group 3: Tests

- [ ] E-03 Add tests: in `tests/test_blocks_release.py`, a case building a fixture repo with a plan carrying a dangling `Blocks-Release` and asserting the full-sweep check (`aw check all`, or a direct `releases.check_blocks_release(repo_root)` call - matching whichever wiring E-01 chose) emits `check.blocks-release-dangling`, plus a resolving case asserting clean. In `tests/test_attention_priority_blocker.py`, a case asserting a plan carrying `Blocks-Release: next` is returned by the release-blocker view AND that its rendered `Item.blocks_release` is populated (so the `>` glyph / `[blocking]` label parity from E-02 holds).
  - Depends on: E-01, E-02
  - Expected outcome: check dangling/clean and attention-surfacing (set membership + populated `blocks_release` for display parity) behavior are covered by passing tests.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `releases.check_blocks_release` (`releases.py:137-162`) is the dangling-reference validator; it uses `resolve_release` (`releases.py:111-131`) and emits `Drift(..., "check.blocks-release-dangling", ...)`. It is invoked from `check_engine.py:597-606` in the full sweep. The `check_refs` seam is at `check_engine.py:197-205`.
- `aw attention`'s `release_blockers` (`attention.py:477-494`) matches `^- Blocks-Release:\s*(\S+)$` on each non-done item's file and collects matching items (so it does not depend on `Item.blocks_release` being set). `Item.blocks_release` IS populated by the specs reader (`attention.py:249,258`) and backlog reader (`attention.py:369`), but is NOT populated by the plans reader `_plans_record` (`attention.py:299-300`) - which is the display-parity gap E-02 fixes. The `>` glyph (`attention.py:622`) and `[blocking]` label (`attention.py:649-650`) key off `Item.blocks_release`.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit maintainer | `releases.check_blocks_release` scans only backlog+specs; a plan with a dangling `Blocks-Release` is never flagged, violating the vwios6 acceptance criteria. |
| F-02 | Med | Toolkit user | The plans reader `_plans_record` (`attention.py:299-300`) does NOT populate `Item.blocks_release` (unlike specs/backlog readers), so a release-blocking plan surfaces in the set but renders WITHOUT the `>` glyph / `[blocking]` label - a display inconsistency E-02 fixes. |

## Proposed changes (ordered, validatable)

1. Include the plans tree in the blocks-release dangling check (extend `check_blocks_release` scan set or add via the `check_refs` seam), reusing `resolve_release`.
2. Populate `Item.blocks_release` in the plans reader (`_plans_record`) so a release-blocking plan surfaces AND renders with the `>`/`[blocking]` markers, matching backlog/specs.
3. Add check (dangling + clean) and attention-surfacing tests.

## Deferred / out of scope (with reason)

- Schema recognition (child 01) and the setter (child 02) are prerequisites, not part of this child.
- No changes to the shape or wording of the shared `resolve_release`/`set_blocks_release_line` primitives; this child only extends WHICH artifacts are validated/surfaced.

## Scope check

- Over-scope: none. Confined to the check + attention surfaces and their tests.
- Under-scope: none. Completes the third parity surface required by the orchestrator's completion criteria.

## Required tests / validation

- `python3 -m pytest tests/test_blocks_release.py tests/test_attention_priority_blocker.py` green, including the new plan-check and plan-attention cases.
- Manual: create a scratch plan with `- Blocks-Release: nosuchid`, run `aw check all` (the full sweep, which triggers the cross-tree blocks-release check - a type-scoped `aw check plans` will not), confirm `check.blocks-release-dangling`; change to `next`, confirm clean; run `aw attention`, confirm the plan appears in the release-blocker set with the `>`/`[blocking]` markers.
- `pre-commit run --files agent_workflows/releases.py agent_workflows/check_engine.py tests/test_blocks_release.py tests/test_attention_priority_blocker.py`.

## Spec / documentation sync

- No user-facing doc change expected; AGENTS.md already asserts plans may carry the field and that `aw check`/`aw attention` surface it. Confirm the released behavior matches the doc after this child.

## Open questions

### OQ-01: Extend `check_blocks_release` scan set, or add the plan check via the `check_refs` seam?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to execution (E-01 explicitly offers both and picks the lower-drift one). Extending the existing scan set (option a) is the smallest change and keeps one validator, but it inherits the full-sweep-only gating (fires on `aw check all`, not `aw check plans`). The `check_refs` seam (option b) is currently a STUB returning `[]` whose docstring explicitly names this exact use ("the awrelease Blocks-Release dangling check folds in here", `check_engine.py:197-205`), and it would run under type-scoped checks too - so it is the documented future home but a slightly larger change. Either satisfies the acceptance criteria; non-blocking. Evidence trade-off recorded so the executor can decide with the gating consequence (V-01) in mind.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output from the command that ACTUALLY triggers the check (`aw check all` for the full-sweep wiring, or a direct `releases.check_blocks_release` call in a test - NOT a type-scoped `aw check plans`, which does not run the sweep-gated check) showing `check.blocks-release-dangling` for a plan with an unresolvable `Blocks-Release`, and clean for a resolving value.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw attention` (or test) output listing a plan carrying `Blocks-Release: next` in the release-blocker set for release f33nrj, AND evidence that the plan `Item.blocks_release` is populated (the `>` glyph / `[blocking]` label renders for the plan the same as for a backlog/spec blocker), confirming the `_plans_record` population fix.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_blocks_release.py tests/test_attention_priority_blocker.py` output with the new cases passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (plan-side blocks-release validation and surfacing), reusing existing shared release-resolution logic across the check and attention surfaces.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and deferred to execution (E-01 chooses the lower-drift wiring). No blocking open question remains.
2. Scope fence: touch ONLY the files in Scope-Paths. Reuse `resolve_release`/existing Drift code; do NOT invent a new validation code or new release-resolution logic. Do NOT change the schema (child 01) or setter (child 02). If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest ...`, `aw check`, `aw attention`); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
