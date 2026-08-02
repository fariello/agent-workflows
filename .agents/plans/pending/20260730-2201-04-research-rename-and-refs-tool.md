# IPD: research rename/regroup + reference integrity tool (Set `research-org`, Order 4)

- Date: 2026-07-30
- Concern: enable after-the-fact regrouping (C4) and prevent citation rot (F5): rename/move research files, update references repo-wide, and flag any `\b<id6>\b` match whose surrounding filename no longer resolves (a dangling citation).
- Scope: the regroup/rename/reference verbs, consuming Orders 01 to 03. No archival policy (05), no migration (06). Requires Orders 01, 02, 03 executed; if their symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 4
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; delivers the C4/F5 capability the timestamp scheme lacked.

## Goal

`aw research set-assign` (group N docs into a set: rename to the set's `YYYYMMDD-<set-id>`, assign `NN` in given order) and `aw research mv` (rename/re-slug one doc), both preserving the immutable `<id6>`, updating name-based references across the repo, and REPORTING dangling `\b<id6>\b` citations. Spec Section 5.6, criteria C4/D3/F5.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Orders 01+02+03 executed; symbols present, else STOP.
- [ ] **Task 1: `set-assign`** (regroup; stable id; dry-run/apply).
- [ ] **Task 2: `mv`** (rename one; stable id).
- [ ] **Task 3: reference updater** (rewrite name-based cites; dry-run/apply).
- [ ] **Task 4: dangling-cite detector** (id matched, filename unresolved).
- [ ] **Tests** `tests/test_research_refs.py`; run it + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- Contract: `<id6>` is immutable; only surrounding name parts change (Order 01). Reference regex `\b<id6>\b` from Order 01.
- Reference scan scope: repo-tracked text (DECISIONS.md, `.agents/plans/**`, TODO.md, docs) - the places that cite research (measured: 10 DECISIONS refs, 14 executed plans today).
- Safety precedent: existing tools default to dry-run + explicit `--apply` (e.g. the untrack tool). Mirror that.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C4-1 | HIGH | Low | maintainer | C4 | Sets are discovered after the fact; regrouping must not break cites. | spec 4.3/C4 |
| C4-2 | HIGH | Medium | integrity | F5 | A moved/renamed target leaves dangling cites unless detected; must flag id-matches whose filename no longer resolves. | spec 5.6/F5 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 5.6/C4 | `aw research set-assign <id6...> --set <id> [--order ...]`: rename targets into the set (shared date+set-id, assigned NN), keep `<id6>`, dry-run default + `--apply`. | `agent_workflows/research_cmd.py`, `agent_workflows/research_refs.py` (new) | Medium | test: 3 docs regrouped get shared date/set + ordered NN; ids unchanged |
| 2 | 5.6 | `aw research mv <id6> [--slug ... --kind ... --model ...]`: rename one doc within the grammar; `<id6>` unchanged. | `agent_workflows/research_cmd.py` | Low | test: re-slug changes name, not id |
| 3 | F5 | Reference updater: on any rename, find name-based references repo-wide and rewrite them to the new name (dry-run/`--apply`). | `agent_workflows/research_refs.py` | Medium | test: a DECISIONS-style cite to the old name is rewritten on `--apply`, previewed on dry-run |
| 4 | F5 | Dangling-cite detector: report `\b<id6>\b` matches whose surrounding filename does not resolve to a current file (a moved/renamed target cited by an old path). | `agent_workflows/research_refs.py` | Medium | test: a stale full-path cite to a moved id is reported as dangling |

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

- Reference scan roots (which tracked paths to scan/rewrite). Lean: DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, README/ARCHITECTURE. Confirm at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite Orders 01+02+03 in executed/.
- [ ] Task 1: PASTE regrouped names (shared date/set, ordered NN, unchanged ids).
- [ ] Task 2: confirm re-slug changes name not id; cite.
- [ ] Task 3: confirm dry-run previews and `--apply` rewrites a sample cite; cite.
- [ ] Task 4: confirm a stale cite to a moved id is reported dangling; cite.
- [ ] PASTE `pytest tests/test_research_refs.py -q` + full-suite summary; leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02, 03; if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (regroup/rename/refs only; no archival, no corpus curation). Never create or push a tag / Release / PyPI upload.
