# IPD: Structural unrun detection and tool-advanced drift-checked research state

- Date: 2026-08-24
- Kind: child
- Concern: Research `status` is written once at creation (`aw research new` hard-codes `status="intake"`, research_cmd.py ~189/~244) and never advanced or validated, so `intake` conflates "untriaged/to-run" with "run-but-unpromoted" and "adopted-but-unpromoted" (11 docs on 2026-08-24; 10 already run+adopted). Spec 5tapom requires the parent B1/H2: identify unrun research WITHOUT trusting hand-typed status, and keep state genuinely tool-maintained.
- Scope: Add a structural UNRUN/RUN signal derived from manifest set-structure, and a drift rule in `aw research index --check` / `aw check` that flags stale hot state; plus a tool-assisted (human-confirmed) triage classifier reproducing the 2026-08-24 manual pass. Implements spec 5tapom Sections 3.1 and 3.2. Does NOT add a status value or change the vocabulary.
- Scope-Paths: grandfathered
- Status: draft
- Set: reslife
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: m383qb

## Workflow history

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; child 01 of the reslife Set (spec 5tapom).

## Goal

Make "which research is not yet run?" a reliable, structural fact (not a hand-typed status) and make stale hot state fail-closed-visible in `--check`, so research state stops silently rotting the way it did before the 2026-08-24 triage.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Structural unrun detection

- [ ] E-01 Add a pure `unrun`/`run` derivation over the research manifest: a SET is UNRUN when its `NN=00` member is `kind: research-prompt` and it has no `NN>=01` sibling member; RUN otherwise. Implement as a single reusable function (e.g. in `agent_workflows/research_contract.py` or `research_index.py`) consumed by later children; do NOT read the corpus (manifest/frontmatter only).
  - Depends on: none
  - Expected outcome: given the manifest, the function returns the exact set of unrun prompts; unit-tested on a fixture with one run set (excluded) and one bare prompt (included).
  - Execution state: pending

### Task group 2: Drift-checked state

- [ ] E-02 Extend `aw research index --check` (and the `aw check` research path / `check_engine`) with a DRIFT rule: an `intake`/`active` doc whose set is RUN, or which is cited by an executed plan/spec/backlog artifact, is flagged as stale-state-to-promote (nonzero exit, like the existing dangling-citation check). Reuse the existing citation-resolution machinery; do not duplicate it.
  - Depends on: E-01
  - Expected outcome: `--check` flags a stale `intake` doc (RUN set or cited-by-executed) and stays clean once promoted; regression test asserts both directions.
  - Execution state: pending

### Task group 3: Tool-assisted triage classifier

- [ ] E-03 Add a human-confirmed triage helper (a new verb or `aw research promote --suggest`, per spec 5tapom OQ-02) that CLASSIFIES stale docs (cited/run -> reference; uncited dead-end -> archive) and previews the moves for confirmation, reproducing the 2026-08-24 manual pass behavior. It must NOT mutate without confirmation (H2: distrust blind writes).
  - Depends on: E-01
  - Expected outcome: the helper previews a correct classification on a fixture matching the 2026-08-24 cohort; applying it promotes/archives as previewed; unit-tested.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Research manifest is `INDEX.json` (all docs, tool-generated from frontmatter); `aw research index --check` is the CI/pre-commit drift gate. Statuses are the four-value `research_contract.STATUSES`. The `NN=00` `research-prompt` convention and set membership come from the filename grammar (spec 20260730 Section 4.5 / 4.2).
- The citation `--check` already resolves `\b<id6>\b` references; reuse it for the cited-by-executed signal rather than a second scanner.

## Findings

- `research_cmd.py` writes `status="intake"` at creation and nothing advances it; `research_index.py` builds `INDEX.json` from frontmatter; `check_engine`/`releases.check_blocks_release` already demonstrate the "scan trees, resolve ids, emit Drift" pattern to mirror.

## Proposed changes (ordered, validatable)

1. Add the pure unrun/RUN derivation over the manifest (E-01).
2. Add the drift rule to `--check`/`aw check` reusing citation resolution (E-02).
3. Add the human-confirmed triage classifier (E-03).

## Deferred / out of scope (with reason)

- Setting `outcome`/`consumed-by` is child 02's job; this child only READS citations for the drift signal, it does not write provenance.
- The `aw research pending` query and attention re-classification are child 03.

## Scope check

- Over-scope: none. Only the unrun signal, the drift check, and the triage helper.
- Under-scope: none within this surface; provenance and surfacing are separate children by design.

## Required tests / validation

- Unit test the unrun derivation on a fixture manifest; test `--check` flags a stale `intake` doc and is clean after promotion; test the triage classifier's preview/apply on a cohort fixture. `python3 -m pytest tests/` green.

## Spec / documentation sync

- Implements spec 5tapom Sections 3.1/3.2; if the research README's "States" section should mention the drift check, update it. Otherwise N/A.

## Open questions

### OQ-01: Is the triage classifier a new verb or `promote --suggest`?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED (spec 5tapom OQ-02); pick the lower-drift option at execution; non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted unit-test output showing the unrun derivation returns exactly the bare prompt (run set excluded) on the fixture.
  - Observed evidence:
  - Result: pending


- [ ] V-02 validates E-02
  - Required evidence: pasted `aw research index --check` (or `aw check`) output flagging a stale `intake` doc, and clean after promotion; regression test named and passing.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted preview + apply of the triage classifier on a cohort fixture producing the correct reference/archive classification; test passing.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern (make research state reliable and unrun detectable) across a derivation, a check rule, and the triage helper that consumes it; all read-side/state-side, no provenance or surfacing.

### Execution contract

1. Open questions RESOLVED: OQ-01 non-blocking (deferred). No blocking open question remains.
2. Scope fence: touch ONLY the research-lifecycle modules needed (research_contract.py / research_index.py / research_cmd.py / check_engine.py) and tests/. Do NOT change attention surfacing (child 03) or provenance write paths (child 02). If a fix needs more, STOP and report.
3. Honesty rule (hard MUST): paste ACTUAL runner output for every claimed pass; never mark a box from narration.
4. Commit ONLY this child's changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: after every E is performed and every V verified with pasted evidence, transition to `executed/` via the gated `aw ipd begin`/`aw ipd finalize`.
