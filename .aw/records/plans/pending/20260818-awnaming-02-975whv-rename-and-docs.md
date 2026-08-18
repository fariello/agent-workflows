# IPD: awnaming rename + docs (this-repo): rename existing files to .type.md and reconcile AGENTS.md

- Date: 2026-08-18
- Kind: child
- Concern: Spec 20260817-2147-01 (RELEASE BLOCKER, backlog 047ce9), awnaming Order 02. The THIS-REPO, ships-nothing half of the naming-grammar rollout: rename this framework repo's own existing durable records to the `.type.md` grammar (dogfooding), regenerate the INDEX/STATUS manifests, fix internal citations, reconcile AGENTS.md's TWO conflicting documented grammars into the ONE grammar, close vf03z3, and file the optional rename-on-migrate nicety as a follow-up backlog item. Depends on Order 01 (the grammar/validator/generator must exist first so the renamed files match what the tooling expects).
- Scope: This repo's `.aw/records/` files + docs. IN: rename plans (184), specs (16), walkthroughs (11), roadmaps (1), backlog (33), comms (22), prompts (16), prompt-library (4) to `.type.md`; regenerate `aw plans index`/`aw research index`/`aw specs`/`aw backlog check` manifests + STATUS/INDEX; fix internal path citations; reconcile AGENTS.md lines 26 + 51; close vf03z3; file the migration-rename follow-up backlog item. OUT: research files (86, keep `.<model>.<kind>.md`); the grammar/producer/validator CODE (Order 01); the version number (S6-V01); the shipped migration behavior.
- Status: reviewed
- Set: awnaming
- Order: 2
- Highest E allocated: 07
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 975whv

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): built from spec 20260817-2147-01 + inventory (287 non-research files; AGENTS.md has 2 conflicting grammars at lines 26/51).
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; verified backlog is front-matter-driven (dual-read holds) and the test basename literals are synthetic fixtures; PR-001 (prescribe scripted facet-append git mv over aw plans mv, E-01) and PR-002 (scope E-07 to renamed-real-file assertions only) fixed in place.

## Goal

Bring THIS repo's own records onto the `.type.md` grammar (dogfooding the Order-01 tooling): rename
every durable non-research file to `<...>.type.md`, regenerate all manifests, fix internal citations,
collapse AGENTS.md's two documented plan-name grammars into the single canonical one, and close the
vf03z3 tooling-gap backlog item. Because Order 01 made the readers/validators dual-read-tolerant, the
suite stays green before and after the rename.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: rename this repo's durable records to .type.md

- [ ] E-01 Rename the 184 plan files under `.aw/records/plans/**` to `<...>.ipd.md` with a SCRIPTED `git mv` that only APPENDS the `.ipd` facet before `.md` (leaving date/set/order/id6/slug byte-identical), across all lifecycle dirs (pending/approved/executed/reusable/superseded/not-executed), skipping README/INDEX/STATUS and research. Do NOT drive this via `aw plans mv` per file: that verb recomputes the name from front-matter (`_plan_date(text)` at plans_refs.py:374) and is per-id6/slow; the pure facet-append is safer and preserves everything. Reserve `aw plans mv` only for a case that also needs a slug/order change.
  - Depends on: none
  - Expected outcome: every `*.md` under `.aw/records/plans/` (except READMEs/INDEX/STATUS) ends in `.ipd.md`; `git status` shows renames (R), not delete+add; date/set/order/id6/slug are unchanged from the old name.
  - Execution state: pending
- [ ] E-02 Rename the non-plan durable records: specs (16) -> `.spec.md`, walkthroughs (11) -> `.walkthrough.md`, roadmaps (1) -> `.roadmap.md`, backlog (33) -> `.backlog.md`, comms (22) -> `.comms.md`, prompts (16) + prompt-library (4) -> `.prompt.md`, via `git mv`. Leave research (86) as `.<model>.<kind>.md`.
  - Depends on: none
  - Expected outcome: every durable non-research, non-plan record ends in its `.type.md`; research files unchanged; `git status` shows renames.
  - Execution state: pending

### Task group 2: regenerate manifests + fix citations

- [ ] E-03 Regenerate every manifest so it points at the new names: `aw plans index`, `aw research index` (unchanged names but re-verify), `aw specs check`, `aw backlog check`, plus any STATUS/INDEX boards. Confirm each `--check` passes.
  - Depends on: E-01,E-02
  - Expected outcome: `aw plans index --check`, `aw research index --check`, `aw specs check`, `aw backlog check`, `aw attention --check` all pass against the renamed tree.
  - Execution state: pending
- [ ] E-04 Fix internal path citations that reference the old bare-`.md` names (grep the repo for `.aw/records/**/*-*.md` string references in docs/specs/plans/READMEs and update to the `.type.md` names where the citation is to a renamed file). Skip research citations.
  - Depends on: E-01,E-02
  - Expected outcome: `rg` for a sample of renamed basenames without the facet finds no stale citation in tracked non-research text (or each remaining hit is justified, e.g. historical prose).
  - Execution state: pending

### Task group 3: reconcile docs + close backlog

- [ ] E-05 Reconcile AGENTS.md's two documented grammars into ONE: update line 26 (`YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md`) and line 51 (the stale `YYYYMMDD-HHMM-NN-<slug>.md`) to the single canonical `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`, listing the type facets. Regenerate any shipped AGENTS.md via the engine generator if the block is managed. No em/en dashes in this user-facing prose.
  - Depends on: E-01,E-02
  - Expected outcome: AGENTS.md documents exactly one filename grammar (the `.type.md` form); `rg "YYYYMMDD-HHMM-NN"` finds no remaining stale grammar in AGENTS.md.
  - Execution state: pending
- [ ] E-06 Close the vf03z3 backlog item (`.aw/records/backlog/open/20260817-awretrofit-01-vf03z3-plan-name-grammar-tooling.md`): its gaps (scaffold-derives-name, mv-preserves-Order, plan-names-validates, AGENTS.md-single-grammar) are all satisfied by Order 01 (scaffold/mv/plan-names) + this Order (AGENTS.md). Move it to `.aw/records/backlog/done/` via `aw backlog set` (or `git mv` if it cannot resolve a moved item, per known behavior), and file the optional rename-on-migrate nicety as a NEW open backlog item.
  - Depends on: E-05
  - Expected outcome: vf03z3 is under `backlog/done/`; a new `open` backlog item exists for the optional `aw migrate-layout --rename-to-grammar` nicety; `aw backlog check` passes.
  - Execution state: pending

### Task group 4: verify the whole repo

- [ ] E-07 Run the FULL serial suite (`python3 -m pytest -p no:xdist`) + `aw sanitize --agent` + all `--check`s after the rename, and paste the tails. Note: the known basename literals in tests (`test_layout_migration.py:452/611` `p.md`, `test_awphysical_routing.py:123/155` `test.md`, `test_installer.py:1286` `my.md`, `test_dir_readmes.py:57` `README.md`, `fixtures/awphysical/order08/e05-external-records.json` `20260810-home-plan.md`) are SYNTHETIC fixtures the tests create themselves, NOT references to this repo's real records, so the rename does not touch them. The specific obligation here is to grep the test tree for any assertion that names one of THIS repo's ACTUALLY-RENAMED real record basenames and fix only those.
  - Depends on: E-01,E-02,E-03,E-04,E-05,E-06
  - Expected outcome: full serial suite green; sanitize clean; all manifest `--check`s pass against the renamed tree; no test references a renamed real record by its old bare-`.md` basename.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Inventory (non-research durable files): plans 184, specs 16, walkthroughs 11, roadmaps 1, backlog 33, comms 22, prompts 16, prompt-library 4 = ~287 renames. Research (86) is excepted.
- AGENTS.md documents TWO conflicting plan-name grammars: line 26 (current clustered) and line 51 (stale `YYYYMMDD-HHMM-NN-<slug>.md`); both must collapse to the one `.type.md` grammar.
- `aw backlog set` cannot resolve a moved/`blocked` item in some cases (known behavior); fall back to `git mv` + manifest regen.
- The filename id6 must equal the front-matter `- Id:`; renaming only appends `.type` before `.md`, so id6/date/set/order/slug are unchanged and manifests stay consistent.
- User-facing prose (AGENTS.md, READMEs) must contain no em or en dashes (agent execution contract).

## Findings

| # | Finding | Consequence |
|---|---|---|
| F1 | Dual-read (Order 01) is already in force. | The suite is green before AND after the rename; rename is safe to do in one Order. |
| F2 | AGENTS.md has two grammars. | E-05 must edit both line 26 and line 51 to a single grammar. |
| F3 | Renames preserve id6/date/order/slug (only append facet). | Manifests need only a regen, not re-keying; citations change only in the basename tail. |
| F4 | `aw backlog set` may not resolve a moved item. | E-06 falls back to `git mv` + regen. |

## Proposed changes (ordered, validatable)

1. `git mv` rename plans (E-01) then non-plan durable records (E-02) to `.type.md`.
2. Regenerate all manifests + fix internal citations (E-03, E-04).
3. Reconcile AGENTS.md to one grammar (E-05).
4. Close vf03z3 + file the migration-rename follow-up (E-06).
5. Full serial suite + sanitize + all `--check`s (E-07).

## Deferred / out of scope (with reason)

- The grammar/producer/validator CODE: Order 01 (this Order depends on it).
- Research files: keep `.<model>.<kind>.md` (the documented exception).
- The shipped `aw migrate-layout` rename behavior: filed as a follow-up backlog item in E-06, not implemented here (OQ-02 resolved: optional nicety, not a release blocker).
- The version number (S6-V01): maintainer, Section 9.

## Scope check

- Over-scope: none - this Order is exactly the this-repo dogfood rename + docs.
- Under-scope: none - together with Order 01 (shipped grammar) it satisfies the spec: producers emit the grammar, validators accept it, this repo conforms, AGENTS.md documents one grammar, vf03z3 closed.

## Required tests / validation

The full serial suite + `aw sanitize --agent` + `aw plans index --check`/`aw research index --check`/
`aw specs check`/`aw backlog check`/`aw attention --check` (E-07), plus per-E evidence below.

## Spec / documentation sync

AGENTS.md reconciled (E-05). On completion the orchestrator advances spec 20260817-2147-01 to
`implemented` and moves backlog 047ce9 to `done` (release Blocker 2 cleared). This Order closes vf03z3.

## Open questions

### OQ-01: Do comms files adopt `.comms.md` given their envelope/inbox naming? (mirrors spec + orchestrator OQ)

- Blocking: no
- Status: open
- Owner: opencode (resolve at E-02 when renaming comms)
- Resolution or deferral rationale: comms messages carry an inbox/envelope/ack convention that may name files by routing. At E-02, decide whether appending `.comms.md` is compatible with that convention or whether comms is a second documented exception like research. If comms is excepted, drop the 22 comms files from E-02 and note it in AGENTS.md; not blocking the rest of the rename.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a count showing every `*.md` under `.aw/records/plans/` (excluding README/INDEX/STATUS) ends in `.ipd.md`, and a `git status` excerpt showing renames (R) not delete+add.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste per-type counts proving specs/walkthroughs/roadmaps/backlog/comms/prompts/prompt-library all end in their `.type.md`, and that research files are unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste passing output of `aw plans index --check`, `aw research index --check`, `aw specs check`, `aw backlog check`, `aw attention --check`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste an `rg` over tracked non-research text for a sample of renamed basenames-without-facet showing no stale citation (or each hit justified).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the reconciled AGENTS.md grammar line(s) + `rg "YYYYMMDD-HHMM-NN" AGENTS.md` returning nothing.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `ls .aw/records/backlog/done/` showing vf03z3, the new open migration-rename backlog item, and `aw backlog check` passing.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the tail of the full serial suite (`python3 -m pytest -p no:xdist`) + `aw sanitize --agent` result, all green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
(opencode Opus 4.8) performs each E, verifies each V with pasted evidence, commits ONLY the files it
changed path-scoped (never `git add -A`), never pushes, and moves this plan to
`.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every
V-item is `pass`. Final Order of the awnaming Set (orchestrator 6gy9rf); on its completion the
orchestrator advances spec 20260817-2147-01 to implemented and backlog 047ce9 to done.
