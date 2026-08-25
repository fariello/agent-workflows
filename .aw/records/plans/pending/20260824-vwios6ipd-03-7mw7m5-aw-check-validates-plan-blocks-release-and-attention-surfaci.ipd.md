# IPD: aw check validates plan Blocks-Release and attention surfacing

- Date: 2026-08-24
- Kind: child
- Concern: `aw check`'s blocks-release dangling-reference validation (`releases.check_blocks_release`, `releases.py:137-162`) scans only the backlog and specs trees; the plans tree is NOT scanned, so a plan carrying a dangling `- Blocks-Release:` (pointing at a non-existent release) is never flagged. AGENTS.md and the vwios6 acceptance criteria require `aw check` to validate a plan's Blocks-Release the same as backlog/specs. Separately, `aw attention`'s `release_blockers` scan (`attention.py:477-494`) already recognizes any artifact carrying the field, so a plan carrying it should surface once child 02 can persist it; this child confirms that surfacing end to end.
- Scope: Extend `aw check` so a plan's `Blocks-Release` is validated (clean when it resolves via `releases.resolve_release`, flagged `check.blocks-release-dangling` when it does not), reusing the existing shared release-resolution logic; and add coverage confirming `aw attention` lists a plan carrying `Blocks-Release: next` in the release-blocker set. Child 03 of the vwios6ipd Set; depends on schema child 01 and setter child 02.
- Scope-Paths: agent_workflows/releases.py, agent_workflows/check_engine.py, tests/test_blocks_release.py, tests/test_attention_priority_blocker.py
- Status: to-review
- Set: vwios6ipd
- Order: 3
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 7mw7m5

## Workflow history
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 03 of vwios6ipd Set (check validation + attention surfacing).

## Goal

Close the last release-gate-parity gap for plans: make `aw check` validate a plan's `Blocks-Release` reference the same way it validates backlog/specs, and confirm `aw attention` surfaces a release-blocking plan, so all three enforcement surfaces (lint, setter, check/attention) agree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Validate plan Blocks-Release in aw check

- [ ] E-01 Extend the plan tree into the blocks-release dangling check. Choose the lower-drift option at execution time: either (a) add `.aw/records/plans` to the directories scanned by `releases.check_blocks_release` (`releases.py:137-162`, currently backlog+specs only), or (b) add a plan-side check via the `check_engine.check_refs` per-type seam (`check_engine.py:197-205`). Reuse `releases.resolve_release` and emit the existing `Drift(path, "check.blocks-release-dangling", ...)` code for a plan whose value does not resolve.
  - Depends on: none
  - Expected outcome: `aw check` on a repo with a plan carrying a dangling `- Blocks-Release:` reports `check.blocks-release-dangling`; a plan whose value resolves (`next` -> the single planned release, or a live id6) is clean.
  - Execution state: pending

### Task group 2: Confirm attention surfacing for plans

- [ ] E-02 Verify (and, only if a gap is found, fix) that `aw attention`'s `release_blockers` scan (`attention.py:477-494`) surfaces a plan carrying `- Blocks-Release: next` in the release-blocker set for the active planned release. If the plans reader does not populate `Item.blocks_release` for plan artifacts, add that population consistent with the backlog/spec readers so the item is classified and surfaced identically. Do NOT change attention's core scan regex.
  - Depends on: none
  - Expected outcome: a plan carrying `- Blocks-Release: next` appears in `aw attention`'s outstanding release-blocker set for release f33nrj.
  - Execution state: pending

### Task group 3: Tests

- [ ] E-03 Add tests: in `tests/test_blocks_release.py`, a case building a fixture repo with a plan carrying a dangling `Blocks-Release` and asserting `aw check` emits `check.blocks-release-dangling`, plus a resolving case asserting clean. In `tests/test_attention_priority_blocker.py`, a case asserting a plan carrying `Blocks-Release: next` is returned by the release-blocker view.
  - Depends on: E-01, E-02
  - Expected outcome: check dangling/clean and attention-surfacing behavior are covered by passing tests.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `releases.check_blocks_release` (`releases.py:137-162`) is the dangling-reference validator; it uses `resolve_release` (`releases.py:111-131`) and emits `Drift(..., "check.blocks-release-dangling", ...)`. It is invoked from `check_engine.py:597-606` in the full sweep. The `check_refs` seam is at `check_engine.py:197-205`.
- `aw attention`'s `release_blockers` (`attention.py:477-494`) matches `^- Blocks-Release:\s*(\S+)$` on each non-done item's file and collects matching items; `Item.blocks_release` is populated by the per-type readers.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit maintainer | `releases.check_blocks_release` scans only backlog+specs; a plan with a dangling `Blocks-Release` is never flagged, violating the vwios6 acceptance criteria. |
| F-02 | Med | Toolkit user | Attention already scans any artifact for the field, but plan-item population of `Item.blocks_release` must be confirmed so a release-blocking plan is classified and surfaced. |

## Proposed changes (ordered, validatable)

1. Include the plans tree in the blocks-release dangling check (extend `check_blocks_release` scan set or add via the `check_refs` seam), reusing `resolve_release`.
2. Confirm/patch attention plan-item `blocks_release` population so a release-blocking plan surfaces.
3. Add check (dangling + clean) and attention-surfacing tests.

## Deferred / out of scope (with reason)

- Schema recognition (child 01) and the setter (child 02) are prerequisites, not part of this child.
- No changes to the shape or wording of the shared `resolve_release`/`set_blocks_release_line` primitives; this child only extends WHICH artifacts are validated/surfaced.

## Scope check

- Over-scope: none. Confined to the check + attention surfaces and their tests.
- Under-scope: none. Completes the third parity surface required by the orchestrator's completion criteria.

## Required tests / validation

- `python3 -m pytest tests/test_blocks_release.py tests/test_attention_priority_blocker.py` green, including the new plan-check and plan-attention cases.
- Manual: create a scratch plan with `- Blocks-Release: nosuchid`, run `aw check`, confirm `check.blocks-release-dangling`; change to `next`, confirm clean; run `aw attention`, confirm the plan appears in the release-blocker set.
- `pre-commit run --files agent_workflows/releases.py agent_workflows/check_engine.py tests/test_blocks_release.py tests/test_attention_priority_blocker.py`.

## Spec / documentation sync

- No user-facing doc change expected; AGENTS.md already asserts plans may carry the field and that `aw check`/`aw attention` surface it. Confirm the released behavior matches the doc after this child.

## Open questions

### OQ-01: Extend `check_blocks_release` scan set, or add the plan check via the `check_refs` seam?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to execution (E-01 explicitly offers both and picks the lower-drift one). Extending the existing scan set is the smallest change and keeps one validator; the `check_refs` seam is preferable only if per-type wiring is already the established pattern for plans. Either satisfies the acceptance criteria; non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw check` (or test) output showing `check.blocks-release-dangling` for a plan with an unresolvable `Blocks-Release`, and clean for a resolving value.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw attention` (or test) output listing a plan carrying `Blocks-Release: next` in the release-blocker set for release f33nrj.
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
