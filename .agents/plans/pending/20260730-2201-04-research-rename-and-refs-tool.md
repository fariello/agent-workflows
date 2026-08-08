# IPD: research rename/regroup + reference integrity tool (Set `research-org`, Order 4)

- Date: 2026-07-30
- Kind: child
- Concern: enable after-the-fact regrouping (C4) and prevent citation rot (F5): rename/move research files, update references repo-wide, and flag any `\b<id6>\b` match whose surrounding filename no longer resolves (a dangling citation).
- Scope: the regroup/rename/reference verbs, consuming Orders 01 and 02. No archival policy (05), no migration (06). Requires Orders 01, 02 executed; if their symbols are absent, STOP. Executes BEFORE Order 03 so Order 03's `index --check` can consume this child's dangling-cite detector (the reference/dangling logic resolves against the filesystem + the Order 01 id6 regex, not the generated INDEX, so no dependency on Order 03 exists).
- Status: approved
- Set: research-org
- Order: 4
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-07 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Consider them all approved. Please do them in the recommended order."

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; delivers the C4/F5 capability the timestamp scheme lacked.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-006 (deps narrowed to 01,02 so this runs before 03; dangling detector is a reusable primitive Order 03 consumes), PR-C04-3 (reference rewriter rewrites only the full old-name token, per-file preview+atomic write), PR-C04-4 (atomic tracked moves, `git mv`), PR-C04-5/E-07 (single pinned scan-root constant), PR-C04-8 (bare-id6 not falsely flagged).

## Goal

`aw research set-assign` (group N docs into a set: rename to the set's `YYYYMMDD-<set-id>`, assign `NN` in given order) and `aw research mv` (rename/re-slug one doc), both preserving the immutable `<id6>`, updating name-based references across the repo, and REPORTING dangling `\b<id6>\b` citations. Spec Section 5.6, criteria C4/D3/F5.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: regroup and rename verbs

- [ ] E-01 confirm Orders 01+02 are executed and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the contract + create symbols are importable; if absent the tool halts before renaming.
  - Execution state: pending
- [ ] E-02 add `aw research set-assign <id6...> --set <id> [--order ...]`: rename targets into the set (shared date+set-id, assigned NN), keep `<id6>`, dry-run default + `--apply`; apply the moves as atomic tracked renames (prefer `git mv`, staged not committed).
  - Depends on: E-01
  - Expected outcome: 3 docs regrouped get a shared date/set + ordered NN; ids unchanged; moves are tracked renames.
  - Execution state: pending
- [ ] E-03 add `aw research mv <id6> [--slug ... --kind ... --model ...]`: rename one doc within the grammar; `<id6>` unchanged; atomic tracked rename.
  - Depends on: E-01
  - Expected outcome: a re-slug changes the name, not the id.
  - Execution state: pending

### Task group 2: reference integrity + tests

- [ ] E-04 add the reference updater: on any rename, find name-based references across the pinned tracked-text scan root (E-07) and rewrite ONLY the full old-filename token to the new name (never the bare `<id6>`), per-file preview then atomic write; dry-run default + `--apply`.
  - Depends on: E-02, E-03
  - Expected outcome: a DECISIONS-style cite to the old name is rewritten on `--apply` and previewed on dry-run; a bare `<id6>` cite is untouched; a cite OUTSIDE the scan root is untouched.
  - Execution state: pending
- [ ] E-05 add the dangling-cite detector AS A REUSABLE PRIMITIVE in `research_refs.py` (a pure function + a CLI reporter): report `\b<id6>\b` matches whose surrounding filename does not resolve to a current file (a moved/renamed target cited by an old path). Order 03's `index --check` imports and invokes this primitive so the gate fails on danglers (spec 5.2).
  - Depends on: E-02, E-03
  - Expected outcome: a stale full-path cite to a moved id is reported as dangling; a bare `<id6>` cite to a moved (but still-present) doc is NOT falsely flagged; the primitive is importable by Order 03.
  - Execution state: pending
- [ ] E-07 pin the authoritative reference scan-root list as a single constant (DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, README.md, ARCHITECTURE.md) consumed by E-04 and E-05; do not scatter differing enumerations in prose.
  - Depends on: E-01
  - Expected outcome: one enforced scan-root constant; the reference tools and their tests reference it, not a prose list.
  - Execution state: pending
- [ ] E-06 add `tests/test_research_refs.py` (set-assign shared-date/ordered-NN/stable-id; mv re-slug stable-id; reference rewrite dry-run vs `--apply`, bare-id6-untouched, outside-root-untouched; dangling-cite detection incl. bare-id6-not-falsely-flagged); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05, E-07
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Contract: `<id6>` is immutable; only surrounding name parts change (Order 01). Reference regex `\b<id6>\b` from Order 01. The reference REWRITER rewrites only the full old-filename token, never the bare `<id6>`.
- Reference scan scope: ONE pinned constant (E-07) over repo-tracked text (DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, README.md, ARCHITECTURE.md) - the places that cite research (per-source counts re-counted at execution, not hardcoded).
- Safety precedent: existing tools default to dry-run + explicit `--apply` and use per-file scan/rebuild/re-scan/atomic-write (see `leak_sanitizer.py` and `ipd_authoring.py`). Mirror that: preview by default, `--apply` to write, atomic write-to-temp-rename, and prefer `git mv` (staged) for moves.
- Dangling-cite detection is a REUSABLE primitive here (E-05) that Order 03's `index --check` imports, so the CI/pre-commit gate catches citation rot (spec 5.2).

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
| 3 | F5 | Reference updater over the pinned scan root: rewrite only the full old-filename token (never bare `<id6>`), per-file preview + atomic write, dry-run default/`--apply`. | `agent_workflows/research_refs.py` | Medium | E-04 |
| 4 | F5/5.2 | Dangling-cite detector as a reusable primitive (consumed by Order 03 `index --check`): report `\b<id6>\b` matches whose surrounding filename does not resolve; do not falsely flag stable bare-id6 cites. | `agent_workflows/research_refs.py` | Medium | E-05 |
| 5 | F5 | Pin the reference scan-root as one constant consumed by E-04/E-05. | `agent_workflows/research_refs.py` | Low | E-07 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Deciding WHICH docs form a set for the existing corpus | n/a | scope | That is the migration's curation. | Order 06 |
| Archival shard moves | n/a | scope | Order 05. | Order 05 |

## Scope check

- Over-scope: none - regroup + rename + reference update + dangling detection.
- Under-scope: MUST keep `<id6>` stable across every operation and never leave a silently-broken cite.

## Required tests / validation

`tests/test_research_refs.py`: set-assign shared-date/ordered-NN/stable-id; mv re-slug stable-id; reference rewrite (dry-run preview vs `--apply`, bare-`<id6>`-untouched, outside-scan-root-untouched); dangling-cite detection (incl. bare-`<id6>`-not-falsely-flagged). Run it + full `python3 -m unittest discover -s tests -t .`; PASTE both (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/docs/research/README.md`: how to regroup after the fact and the dry-run/`--apply` safety.

## Open questions

### OQ-01: reference scan roots

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: RESOLVED at review (2026-08-07). The authoritative scan root is pinned as ONE constant (E-07): DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, README.md, ARCHITECTURE.md. The reference tools and tests consume that constant, never a prose list.

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
  - Required evidence: confirm dry-run previews and `--apply` rewrites a full-old-filename sample cite; confirm a bare `<id6>` token and a cite OUTSIDE the pinned scan root are both left untouched; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm a stale full-path cite to a moved id is reported dangling AND a bare `<id6>` cite to a moved-but-present doc is NOT flagged; confirm the primitive is importable by Order 03's `index --check`; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: cite the single scan-root constant and show E-04/E-05 and their tests consume it (no divergent prose enumeration remains).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_research_refs -v` + the full-suite `Ran N tests ... OK` summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02, 03; if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (regroup/rename/refs only; no archival, no corpus curation). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
