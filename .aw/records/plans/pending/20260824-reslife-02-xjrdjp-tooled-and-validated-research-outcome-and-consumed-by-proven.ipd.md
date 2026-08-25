# IPD: Tooled and validated research outcome and consumed-by provenance

- Date: 2026-08-24
- Kind: child
- Concern: `outcome` is hard-coded `none-yet` at creation (research_cmd.py ~190/~245) with NO verb to ever set it, and `consumed-by: []` is written at creation but never populated or validated (1 of ~85 docs on 2026-08-24) and is not even carried in `INDEX.json`. So "which research output was authoritative/adopted?" and "what used this research?" are unanswerable, contradicting spec 5tapom Section 3.3 (and the parent's B2/provenance intent).
- Scope: Add a deliberate setter for `outcome` and `consumed-by`, carry `consumed-by` in `INDEX.json`, and validate both in `aw research index --check` / `aw check`. Implements spec 5tapom Section 3.3. Does NOT change the `outcome` vocabulary or the `status` model.
- Scope-Paths: grandfathered
- Status: to-review
- Set: reslife
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: xjrdjp

## Workflow history
- 2026-08-25 to-review (aw set): Authored complete and lint-conforming; ready for plan-review.

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 02 of the reslife Set (spec 5tapom).

## Goal

Make research provenance first-class and honest: a tool sets `outcome`/`consumed-by`, the manifest carries them, and `--check` enforces that an adopted doc names what adopted it and that every `consumed-by` reference resolves.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: The setter verb

- [ ] E-01 Add `aw research set-outcome <id6> --to <adopted|informational|rejected|none-yet> [--consumed-by <id6[,id6...]>|-]` that writes/updates/clears `outcome` and `consumed-by` in frontmatter through a single shared write primitive, records the disposition, and is dry-run-by-default with `--apply` (consistent with other `aw research` mutators).
  - Depends on: none
  - Expected outcome: the verb sets `outcome` and appends/replaces/clears `consumed-by`; unit-tested for set/append/clear.
  - Execution state: pending

### Task group 2: Index carries provenance

- [ ] E-02 Carry `consumed-by` in `INDEX.json` (today omitted) so provenance is queryable without reading the corpus; keep `INDEX.md`'s bounded hot-glance unchanged.
  - Depends on: E-01
  - Expected outcome: `INDEX.json` docs include `consumed-by`; `aw research index --check` stays clean; a test asserts the field is present.
  - Execution state: pending

### Task group 3: Validation

- [ ] E-03 Extend `aw research index --check` / `aw check`: a `consumed-by` entry that does not resolve to an existing plan/spec/backlog id6 is flagged (mirroring the dangling-citation check), and `outcome: adopted` with an empty `consumed-by` is flagged (an adopted doc must name its consumer).
  - Depends on: E-01
  - Expected outcome: `--check` flags a dangling `consumed-by` and an adopted-without-consumer; clean when satisfied; regression tests for both.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `outcome` vocabulary is `adopted|informational|rejected|none-yet` (research_contract). `consumed-by` is a list of plan/spec/backlog id6s the doc informed (spec 20260730 Section 5.4). `releases.check_blocks_release`/citation `--check` show the id-resolution + Drift pattern to reuse.

## Findings

- No `--outcome`/`set-outcome` exists on `aw research`; `outcome`/`consumed-by` are creation-only. `INDEX.json` doc schema lacks `consumed-by` (verified 2026-08-24). The 2026-08-24 triage hand-set these fields, which this child makes tool-owned.

## Proposed changes (ordered, validatable)

1. `aw research set-outcome` with a shared write primitive (E-01).
2. `consumed-by` in `INDEX.json` (E-02).
3. `--check`/`aw check` validation of dangling refs and adopted-without-consumer (E-03).

## Deferred / out of scope (with reason)

- The structural unrun/RUN signal and stale-state drift are child 01. Attention/pending surfacing is child 03.

## Scope check

- Over-scope: none. Only the provenance fields, their index carriage, and their validation.
- Under-scope: none within this surface.

## Required tests / validation

- Unit test set/append/clear via the verb; test `INDEX.json` carries `consumed-by`; test `--check` flags dangling `consumed-by` and adopted-without-consumer, clean otherwise. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Section 3.3. Update the research README's frontmatter example if `consumed-by` guidance changes; otherwise N/A.

## Open questions

### OQ-01: Should `set-outcome` also accept a status change, or stay orthogonal to `promote`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED; keep `set-outcome` orthogonal to `promote` unless execution shows a strong reason to combine. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `aw research set-outcome` setting `outcome` and `--consumed-by`, and clearing with `-`; unit test passing.
  - Observed evidence:
  - Result: pending


- [ ] V-02 validates E-02
  - Required evidence: pasted `INDEX.json` fragment showing `consumed-by` on a doc; `aw research index --check` clean; test passing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `--check` output flagging a dangling `consumed-by` and an `adopted`-without-consumer, and clean once fixed; regression tests passing.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make research provenance tooled and validated) across the setter, its index carriage, and its checks.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the research provenance surfaces (research_cmd.py / research_index.py / research_contract.py / check_engine.py / cli.py for the verb) and tests/. Do NOT change the unrun/drift logic (child 01) or attention (child 03). If more is needed, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
