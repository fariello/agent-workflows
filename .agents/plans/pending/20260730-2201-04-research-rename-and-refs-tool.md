# IPD: research rename/regroup + reference integrity tool (Set `research-org`, Order 4)

- Date: 2026-07-30
- Kind: child
- Concern: enable after-the-fact regrouping (C4) and prevent citation rot (F5): rename/move research files, update references repo-wide, and flag any `\b<id6>\b` match whose surrounding filename no longer resolves (a dangling citation).
- Scope: the regroup/rename/reference verbs, consuming Orders 01 to 03. No archival policy (05), no migration (06). Requires Orders 01, 02, 03 executed; if their symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 4
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; delivers the C4/F5 capability the timestamp scheme lacked.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.

## Goal

`aw research set-assign` (group N docs into a set: rename to the set's `YYYYMMDD-<set-id>`, assign `NN` in given order) and `aw research mv` (rename/re-slug one doc), both preserving the immutable `<id6>`, updating name-based references across the repo, and REPORTING dangling `\b<id6>\b` citations. Spec Section 5.6, criteria C4/D3/F5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: regroup and rename verbs

- [ ] E-01 confirm Orders 01+02+03 are executed and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the contract + create + index symbols are importable; if absent the tool halts before renaming.
  - Execution state: pending
- [ ] E-02 add `aw research set-assign <id6...> --set <id> [--order ...]`: rename targets into the set (shared date+set-id, assigned NN), keep `<id6>`, dry-run default + `--apply`.
  - Depends on: E-01
  - Expected outcome: 3 docs regrouped get a shared date/set + ordered NN; ids unchanged.
  - Execution state: pending
- [ ] E-03 add `aw research mv <id6> [--slug ... --kind ... --model ...]`: rename one doc within the grammar; `<id6>` unchanged.
  - Depends on: E-01
  - Expected outcome: a re-slug changes the name, not the id.
  - Execution state: pending

### Task group 2: reference integrity + tests

- [ ] E-04 add the reference updater: on any rename, find name-based references repo-wide and rewrite them to the new name (dry-run/`--apply`).
  - Depends on: E-02, E-03
  - Expected outcome: a DECISIONS-style cite to the old name is rewritten on `--apply` and previewed on dry-run.
  - Execution state: pending
- [ ] E-05 add the dangling-cite detector: report `\b<id6>\b` matches whose surrounding filename does not resolve to a current file (a moved/renamed target cited by an old path).
  - Depends on: E-02, E-03
  - Expected outcome: a stale full-path cite to a moved id is reported as dangling.
  - Execution state: pending
- [ ] E-06 add `tests/test_research_refs.py` (set-assign shared-date/ordered-NN/stable-id; mv re-slug stable-id; reference rewrite dry-run vs `--apply`; dangling-cite detection); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Contract: `<id6>` is immutable; only surrounding name parts change (Order 01). Reference regex `\b<id6>\b` from Order 01.
- Reference scan scope: repo-tracked text (DECISIONS.md, `.agents/plans/**`, TODO.md, docs) - the places that cite research (measured: 10 DECISIONS refs, 14 executed plans today).
- Safety precedent: existing tools default to dry-run + explicit `--apply` (e.g. the untrack tool). Mirror that.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C4-1 | HIGH | Low | maintainer | C4 | Sets are discovered after the fact; regrouping must not break cites. | spec 4.3/C4 |
| C4-2 | HIGH | Medium | integrity | F5 | A moved/renamed target leaves dangling cites unless detected; must flag id-matches whose filename no longer resolves. | spec 5.6/F5 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 5.6/C4 | `aw research set-assign <id6...> --set <id> [--order ...]`: rename targets into the set (shared date+set-id, assigned NN), keep `<id6>`, dry-run default + `--apply`. | `agent_workflows/research_cmd.py`, `agent_workflows/research_refs.py` (new) | Medium | E-02 |
| 2 | 5.6 | `aw research mv <id6> [--slug ... --kind ... --model ...]`: rename one doc within the grammar; `<id6>` unchanged. | `agent_workflows/research_cmd.py` | Low | E-03 |
| 3 | F5 | Reference updater: on any rename, find name-based references repo-wide and rewrite them to the new name (dry-run/`--apply`). | `agent_workflows/research_refs.py` | Medium | E-04 |
| 4 | F5 | Dangling-cite detector: report `\b<id6>\b` matches whose surrounding filename does not resolve to a current file (a moved/renamed target cited by an old path). | `agent_workflows/research_refs.py` | Medium | E-05 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Deciding WHICH docs form a set for the existing corpus | n/a | scope | That is the migration's curation. | Order 06 |
| Archival shard moves | n/a | scope | Order 05. | Order 05 |

## Scope check

- Over-scope: none - regroup + rename + reference update + dangling detection.
- Under-scope: MUST keep `<id6>` stable across every operation and never leave a silently-broken cite.

## Required tests / validation

`tests/test_research_refs.py`: set-assign shared-date/ordered-NN/stable-id; mv re-slug stable-id; reference rewrite (dry-run preview vs `--apply`); dangling-cite detection. Run it + full `python -m pytest -q`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: how to regroup after the fact and the dry-run/`--apply` safety.

## Open questions

### OQ-01: reference scan roots

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: scan and rewrite the tracked paths DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, and README/ARCHITECTURE. Confirm the exact set at review; if it changes, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite Orders 01+02+03 in `executed/`; confirm the tool halts when their symbols are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste regrouped names (shared date/set, ordered NN, unchanged ids).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: confirm a re-slug changes the name not the id; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm dry-run previews and `--apply` rewrites a sample cite; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm a stale cite to a moved id is reported dangling; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `pytest tests/test_research_refs.py -q` + the full-suite summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02, 03; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (regroup/rename/refs only; no archival, no corpus curation). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
