# IPD: Backlog graduated status plus the graduate-implement-execute contract and spec-as-gate-carrier

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Backlog status is binary in practice (`open` or `done`), which forces a FALSE choice once an item's design work is finished but its code is not: the item still reads `open`, indistinguishable from something nobody has touched, and the only way to change that is `done`, which would be a lie and would drop the release gate. This was hit live on 2026-08-29 with item `kjzlgw`: an approved spec (`c4gd2h`) plus 7 review-ready IPDs existed, yet the item read `open`. Two adjacent defects made it worse: (1) NOTHING in AGENTS.md tells an agent that acting on a backlog item must produce REVIEW-READY IPDs, so the obligation lives only in the maintainer's head; (2) `check_engine.find_from_backlog_plans` scans plan IPDs ONLY, so a spec carrying `From-Backlog` + a matching `Blocks-Release` cannot satisfy the HANDOFF gate, making a spec-first graduation unclosable by construction.
- Scope: Add a `graduated` backlog status between `open` and `done` (enum, directory, attention class, close-legitimacy handling), document the graduate/implement/execute contract in AGENTS.md so agents produce review-ready IPDs without being told, and let a SPEC carrying `From-Backlog` + a matching `Blocks-Release` satisfy the HANDOFF gate. Does NOT change the plan or spec lifecycles, does NOT auto-transition existing items, and does NOT alter what `done` means.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/attention_contract.py, agent_workflows/attention.py, agent_workflows/check_engine.py, AGENTS.md, .aw/records/backlog/README.md, tests/test_backlog_graduated.py, tests/test_check_engine_spec_handoff.py
- Item-Dependencies: none
- Status: to-review
- Set: bklgrad
- Order: 1
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: v58bvy

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready: graduated status + graduate/implement/execute contract + spec-as-gate-carrier.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Make the backlog lifecycle honest for handed-off work by adding a `graduated` status between `open` and `done`, encode the graduate/implement/execute contract in AGENTS.md so agents reliably produce review-ready IPDs, and accept a spec as a legitimate release-gate carrier so a spec-first graduation is closable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the `graduated` status

- [ ] E-01 Add `graduated` to the backlog status vocabulary in `agent_workflows/backlog.py`: extend `STATUS_DIRS` (currently `("open", "blocked", "parked", "done")`, backlog.py:51) and therefore `STATUSES` (:52), and create the `.aw/records/backlog/graduated/` directory so the directory-backed model stays consistent. Ordering in `STATUS_DIRS` must place `graduated` between `open` and `done` to reflect the lifecycle.
  - Depends on: none
  - Expected outcome: `aw backlog new --status graduated` and `aw backlog set graduated <id6>` are accepted; the item file moves into `graduated/`; `aw backlog check` accepts it; an unknown status is still rejected with the full valid list.
  - Execution state: pending
- [ ] E-02 Map `graduated` onto an `aw attention` cross-tree class in `attention_contract.py`/`attention.py`. It is NOT `ready` (no fresh action is needed on the ITEM; the action lives on its plans), NOT `done` (nothing is implemented), and NOT `parked` (it is intentionally ACTIVE work). Map it to `active` per the contract's definition "work is EXPLICITLY in progress (a native state says so); never inferred" (attention_contract.py:24), since a graduated item explicitly asserts in-progress work.
  - Depends on: E-01
  - Expected outcome: `aw attention` shows a graduated item under `active`, not `ready`/`done`/`parked`; `aw attention --check` stays valid; a graduated item carrying `Blocks-Release` still appears in the release-blocker set (it is not yet delivered).
  - Execution state: pending
- [ ] E-03 Handle `graduated` in the close-legitimacy predicate (`check_engine.evaluate_blocking_close`): transitioning a release-gated item to `graduated` is LEGITIMATE without evidence (it is not a close and drops no gate), but MUST NOT be treatable as a substitute for `done`. Keep `done`'s existing three fixes (HANDOFF/SATISFIED/DE-GATED) unchanged.
  - Depends on: E-01
  - Expected outcome: `aw backlog set graduated <gated-item>` succeeds with an ok verdict; `aw backlog set done` on that same item still fails closed unless one of the three existing fixes applies; a test asserts `graduated` did not silently become a close.
  - Execution state: pending

### Task group 2: the agent contract in AGENTS.md

- [ ] E-04 Document the graduate/implement/execute contract in AGENTS.md so an agent does not need to be told per-request: acting on a backlog item MUST produce REVIEW-READY artifacts (plans born `to-review`, not `draft`), MUST carry `From-Backlog: <id6>` and inherit any `Blocks-Release`, MUST resolve blocking open questions from repository evidence rather than stopping to ask when the evidence exists, and MUST move the item to `graduated` (never `done`) when design is handed off but code is not written.
  - Depends on: E-01
  - Expected outcome: AGENTS.md states the contract in the backlog/plan section; a fresh reader can determine the required end state (item `graduated`, plans `to-review`, gate inherited) without asking; no em/en dashes are introduced into user-facing prose per the repo rule.
  - Execution state: pending
- [ ] E-05 Update `.aw/records/backlog/README.md`'s status table and three-tier prose to include `graduated`, its directory, and its attention class, so the README and the code agree (single source of truth; the README currently lists only open/blocked/parked/done at :14-17).
  - Depends on: E-01, E-02
  - Expected outcome: the README's status list, directory table, and attention-class mapping include `graduated` and match `STATUS_DIRS` exactly; a test or check comparing the documented list to `STATUSES` passes.
  - Execution state: pending

### Task group 3: spec as a gate carrier

- [ ] E-06 Extend the HANDOFF check so a SPEC can carry a release gate: `check_engine.find_from_backlog_plans` currently iterates plan IPDs only (`_iter_plan_ipds`), so a spec with `From-Backlog: <id6>` and a matching `Blocks-Release` is invisible and cannot satisfy HANDOFF. Add spec scanning (a sibling finder, or generalize to artifact scanning) so a spec-first graduation is closable, keeping the existing plan behavior byte-identical.
  - Depends on: none
  - Expected outcome: given ONLY a spec carrying `From-Backlog: X` + `Blocks-Release: R` and no plan, `evaluate_blocking_close` on item X returns legitimate with route HANDOFF; with a MISMATCHED `Blocks-Release` it still fails closed; existing plan-based HANDOFF results are unchanged.
  - Execution state: pending
- [ ] E-07 Extend the corresponding `aw check` consistency rules to specs so the checker and the setter cannot diverge: `check.from-backlog-dangling` must flag a spec whose `From-Backlog` resolves to no item, and `check.from-backlog-gate-mismatch` must flag a spec whose gate disagrees with its item, mirroring the plan rules (AGENTS.md:80-95 describes the plan-side contract).
  - Depends on: E-06
  - Expected outcome: a spec with a dangling `From-Backlog` is flagged; a spec whose `Blocks-Release` disagrees with its item is flagged; `aw check` on the current repo reports no NEW findings introduced by this change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Backlog status is DIRECTORY-BACKED: `STATUS_DIRS = ("open", "blocked", "parked", "done")` (`backlog.py:51`) with `STATUSES = frozenset(STATUS_DIRS)` (:52), and the parent directory name is how status is read (`:130`, `return parent if parent in STATUSES else None`). Adding a status therefore requires the directory too, not just the enum.
- Validation reads the same set (`:144-149`), `new` (:307-309) and `set` (:434) both gate on it, so one enum edit propagates to all three surfaces; the error messages already print `sorted(STATUSES)` so they stay correct automatically.
- The attention contract defines exactly five classes with explicit meanings (`attention_contract.py:23-27`, constants at :47-51). `active` is documented as "work is EXPLICITLY in progress (a native state says so); never inferred", which is precisely what a `graduated` item asserts.
- `check_engine.find_from_backlog_plans` iterates `_iter_plan_ipds(repo_root)` and returns `[(path, blocks_release_or_'')]`; `evaluate_blocking_close` compares `plan_br == blocks_release` for the HANDOFF route. Extending to specs means adding a scanner, not changing the comparison.
- `aw check` rules named in AGENTS.md:93-95 (`check.blocking-item-closed-without-gate`, `check.from-backlog-gate-mismatch`, `check.orphaned-live-blocker`) are backed by the SAME predicate as the setter, deliberately so they cannot diverge; any change must preserve that sharing.
- User-facing prose (AGENTS.md, READMEs) must avoid em/en dashes per the repo contract; internal artifacts are exempt.

## Findings

The live failure that motivates this plan (2026-08-29, item `kjzlgw`):

| Fact | Consequence |
|---|---|
| spec `c4gd2h` approved + 7 IPDs authored `to-review` | design work demonstrably finished |
| item still read `Status: open` | indistinguishable from untouched work in `aw attention` |
| only non-`open` option was `done` | would falsely claim implementation |
| `done` requires HANDOFF/SATISFIED/DE-GATED | would have forced dropping the 2.0.0 gate |

Verified predicate behavior before the plans existed:

```
handoff plans found for kjzlgw: []
verdict legitimate: False
severity: error
reason: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate
```

And after the 7 plans landed, the same predicate returned `legitimate: True, route: HANDOFF`, confirming the gate mechanism works for PLANS. The gap is that a spec cannot do the same, which is why a spec-first graduation is unclosable today (E-06 fixes that).

Downstream artifact that must be reconciled (recorded 2026-08-29): research `ig9bai`
(`.aw/records/research/20260829-runverify-00-ig9bai-deterministic-run-and-verify-design.gpt56.reference-research.md`,
an externally-authored deterministic run-and-verify design) specifies in its section 4.9 a
`BACKLOG-DONE-LEGITIMACY` check whose pass criterion is "Backlog changed `open -> done` through the
setter only after the IPD handoff commit", with `aw backlog set open <id6>` as the recovery. That
encodes the BINARY lifecycle this plan replaces. If 4.9 is implemented verbatim it will re-encode the
exact defect described above. E-04's AGENTS.md contract text is therefore the authority, and any
adoption of `ig9bai` must treat `graduated` as the legitimate post-handoff state and reserve `done`
for implemented work. The conflict is recorded as C-1 in that research doc so it cannot be lost.

A trap worth naming: `graduated` must not become a soft `done`. If it were accepted as satisfying a release gate, a maintainer could ship 2.0.0 with every blocker merely `graduated` and nothing implemented. E-03 therefore keeps `done`'s three fixes untouched and a V-item asserts a graduated blocker still counts as outstanding.

## Proposed changes (ordered, validatable)

1. `backlog.py`: `graduated` in `STATUS_DIRS`/`STATUSES` + the `graduated/` directory.
2. `attention_contract.py`/`attention.py`: map `graduated` -> `active`.
3. `check_engine.py`: accept the `graduated` transition without treating it as a close.
4. `AGENTS.md`: the graduate/implement/execute contract (review-ready plans, gate inheritance, resolve-from-evidence, end state `graduated`).
5. `.aw/records/backlog/README.md`: status table + attention mapping updated to match the code.
6. `check_engine.py`: specs count as HANDOFF gate carriers.
7. `aw check` rules extended to specs so checker and setter stay in sync.

## Deferred / out of scope (with reason)

- Auto-migrating existing `open` items that already have From-Backlog plans (e.g. `kjzlgw`) to `graduated`: a data migration with judgment calls per item; do it deliberately after this lands rather than bundling a bulk rewrite into the schema change.
- Renaming `graduated` to a state-shaped word (`handed-off`, `in-plan`): raised with the maintainer, who chose `graduated`; recorded here so the naming question is not silently re-litigated.
- Changing plan or spec lifecycles: out of scope. This plan touches only the backlog status and the gate-carrier check.
- Making `graduated` satisfy a release gate: deliberately REJECTED (see Findings), not deferred.

## Scope check

- Over-scope: none. No item is auto-migrated and no other lifecycle is touched.
- Under-scope: none. The status (enum+dir), its attention class, its close-legitimacy handling, the AGENTS.md contract, the README sync, the spec-as-gate-carrier fix, and the matching `aw check` rules each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_backlog_graduated.py tests/test_check_engine_spec_handoff.py -q` passes.
- `python -m pytest -q` remains green (the status enum is read by `new`, `set`, and validation, so a regression would surface broadly).
- `aw backlog check` and `aw attention --check` both stay valid on the real repo after the change.
- `aw check backlog` and `aw check specs` report no NEW findings attributable to this change (pre-existing findings on other items are recorded, not fixed here).
- A negative test proves `graduated` did NOT become a soft `done` (a graduated blocker still counts as outstanding for the release).

## Spec / documentation sync

- AGENTS.md gains the graduate/implement/execute contract (E-04). This is the authoritative statement; do not duplicate it in prose elsewhere (single source of truth).
- `.aw/records/backlog/README.md` status table updated (E-05) and kept mechanically consistent with `STATUS_DIRS`.
- No new spec record is required: this plan implements a process/schema fix, and its own contract text lands in AGENTS.md rather than a separate spec.

## Open questions

### OQ-01: Which attention class should `graduated` map to?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: `active`. The contract defines `active` as "work is EXPLICITLY in progress (a native state says so); never inferred" (`attention_contract.py:24`), and a graduated item explicitly asserts that implementation work exists in linked plans. `ready` is wrong (no action is needed on the item itself), `done` is false (nothing implemented), and `parked` is wrong (the work is intentionally live). Resolved from the contract's own definitions.

### OQ-02: Should `graduated` be reachable directly from `blocked`?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: yes, allow any status to reach `graduated` rather than enforcing a path. The existing setter does not encode a transition graph (it validates the TARGET against `STATUSES`, `backlog.py:434`), so adding path constraints here would be a new mechanism and a behavior change beyond this plan's scope. A blocked item whose design gets handed off is a real case.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output showing `aw backlog new --status graduated` and `aw backlog set graduated <id6>` succeed, the file lands in `.aw/records/backlog/graduated/`, `aw backlog check` accepts it, and an invalid status is still rejected with the full valid list including `graduated`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `aw attention` output (or its JSON) showing a graduated item classified `active` and absent from `ready`/`done`/`parked`; plus pasted `aw attention --check` exit 0; plus evidence a graduated item carrying `Blocks-Release` STILL appears in the release-blocker set.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output showing (a) `set graduated` on a release-gated item returns an ok verdict, and (b) `set done` on that SAME item still fails closed with the three-fixes message. The negative case is the load-bearing one: without it `graduated` could silently become a close.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the pasted AGENTS.md diff showing the contract text (review-ready plans, `From-Backlog` + gate inheritance, resolve-from-evidence, end state `graduated` not `done`), plus a check that no em or en dash was introduced into that user-facing prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted README diff plus pasted output of a check comparing the README's documented status list against `backlog.STATUSES` and finding them equal (a manual read fails this item).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for three cases: a spec-only HANDOFF returns legitimate with route HANDOFF; a spec with a MISMATCHED `Blocks-Release` still fails closed; an existing plan-based HANDOFF returns exactly as before (regression guard). Plus the live `kjzlgw` check re-run showing the spec `c4gd2h` now counts.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted pytest output showing a spec with a dangling `From-Backlog` is flagged `check.from-backlog-dangling` and a spec with a disagreeing gate is flagged `check.from-backlog-gate-mismatch`; plus pasted `aw check specs`/`aw check backlog` output on the real repo showing no NEW findings introduced.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
