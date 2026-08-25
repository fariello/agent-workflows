# IPD: Attention and query surfacing for research pending and stale state

- Date: 2026-08-24
- Kind: child
- Concern: `aw attention` maps research `intake -> ready` (attention_contract CLASS_MAPS['research'] = {intake: ready, active: active, reference: done, archive: parked}), so finished-but-unpromoted research shows as actionable work (the "ready" bucket held 11 research rows on 2026-08-24, 10 of them already done), and there is no first-class "what research must I still run?" query. Spec 5tapom Section 3.4 requires separating untriaged from actionable and surfacing pending research.
- Scope: Add `aw research pending` (or `find --unrun`) listing UNRUN prompts (consuming child 01's structural signal), and change `aw attention` so a finished/cited `intake` doc is NOT filed under `ready` (surface it as stale-state-to-promote) while a genuinely-unrun prompt remains actionable. Implements spec 5tapom Section 3.4. Depends on child 01 (unrun signal) and child 02 (provenance fields).
- Scope-Paths: grandfathered
- Status: draft
- Set: reslife
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: h40usm

## Workflow history

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 03 of the reslife Set (spec 5tapom).

## Goal

Make "what research do I still have to run?" a first-class, tool-answered question and stop `aw attention` from presenting finished research as actionable, so the attention view is trustworthy.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Pending query

- [ ] E-01 Add `aw research pending` (or `aw research find --unrun`) that lists exactly the UNRUN prompts using child 01's structural derivation (no corpus read), in both human and `--agent` output.
  - Depends on: none
  - Expected outcome: the query lists only unrun prompts on a fixture (run set excluded, bare prompt included); unit-tested in both output modes.
  - Execution state: pending

### Task group 2: Attention re-classification

- [ ] E-02 Change `aw attention`/`attention_contract` so a research doc at `intake`/`active` that is RUN or cited-by-executed is NOT classed `ready` (surface it as a stale-state/drift item, per spec 5tapom OQ-01), while a genuinely-unrun `intake` prompt remains actionable. Keep the mapping PURE/TOTAL over `research_contract.STATUSES` (class_of must not raise).
  - Depends on: E-01
  - Expected outcome: on a fixture, a finished-but-unpromoted research doc no longer appears under `ready`; an unrun prompt does; `aw attention` regression test asserts the split.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `attention_contract.class_of(tree, status)` is PURE and TOTAL and raises `UnknownNativeStatus` for an unmapped value; the research fragment currently maps `intake->ready`. Any re-class must remain total over the four statuses. `aw attention` buckets are `active/ready/blocked/done/parked`.

## Findings

- The stale-`intake`-as-`ready` behavior is the visible symptom the maintainer flagged; child 01 provides the RUN/cited signal needed to distinguish "actionable unrun" from "stale finished" so attention can class them differently.

## Proposed changes (ordered, validatable)

1. `aw research pending`/`find --unrun` (E-01).
2. Attention re-classification using the RUN/cited signal (E-02).

## Deferred / out of scope (with reason)

- The RUN/unrun derivation and drift `--check` live in child 01; the provenance fields in child 02. This child consumes them.

## Scope check

- Over-scope: none. Only the pending query and the attention class split.
- Under-scope: none within this surface.

## Required tests / validation

- Unit test `aw research pending` (both output modes) on a fixture; `aw attention` regression test showing finished research is not `ready` and an unrun prompt is actionable. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Section 3.4 and resolves its OQ-01 (attention class choice). Update attention/research docs if the class labels change; otherwise N/A.

## Open questions

### OQ-01: New attention class vs reuse a drift signal for stale-state?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (spec 5tapom OQ-01); pick the lower-drift option (new class vs reuse) at execution, keeping class_of total. Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw research pending` (human + `--agent`) on a fixture listing only unrun prompts; unit test passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw attention` output on a fixture showing a finished-but-unpromoted research doc is NOT under `ready` and an unrun prompt is actionable; class_of totality test passing.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (surface research pending/stale honestly) across the query and the attention class split that consume child 01/02 signals.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the surfacing modules (research_cmd.py / cli.py for the query, attention.py / attention_contract.py for the class split) and tests/. Do NOT re-implement the unrun signal (import child 01's) or the provenance fields (child 02). If more is needed, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
