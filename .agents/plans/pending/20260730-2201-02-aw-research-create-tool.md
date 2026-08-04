# IPD: `aw research new` / `new-comparison` creation tool (Set `research-org`, Order 2)

- Date: 2026-07-30
- Concern: give agents and humans a deterministic command to create a correctly-named research doc with starter frontmatter, so naming is a tool call (not a fallible convention). Encodes the multi-model comparison pattern as first-class.
- Scope: the create verbs only, consuming the Order-01 contract. No indexing (Order 03), no rename (04), no archival (05). Requires Order 01 executed (imports `research_contract`); if its symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 2
- Quarantine: old-shape draft; superseded by the ipd-structure convention, to be re-authored to the E-*/V-* shape
- Quarantine owner: maintainer (IPD-system-first sequencing decision, 2026-08-03)
- Quarantine follow-up: re-author the research-org Set to the new schema after the ipd-structure Set lands
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the first behavior on top of the Order-01 contract.

- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): the maintainer's IPD-system-first sequencing decision defers this old-shape research-org plan; quarantined under spec Section 13.3 (metadata trio added) pending re-authoring to the new E-*/V-* shape after the ipd-structure Set. Not conforming, not an error; an informational disposition.

## Goal

`aw research new` and `aw research new-comparison`: generate a unique `<id6>`, resolve/derive the set + next `NN`, validate/normalize `<model>`/`<kind>`, assemble the filename, and write starter frontmatter (status: intake), then print a self-revealing next step (F6). This is spec Sections 5.1 and 5.3.

## Detailed Implementation Checklist (TODO)

- [ ] **Precheck**: Order 01 executed; `research_contract` importable, else STOP.
- [ ] **Task 1: `aw research new`** (id, set/NN resolution, vocab validate, write + starter frontmatter).
- [ ] **Task 2: `aw research new-comparison`** (prompt 00 + model reports + reconciliation).
- [ ] **Task 3: self-revealing output + `--help`**.
- [ ] **Task 4: invalid-input rejection** (no file written).
- [ ] **Tests** `tests/test_research_cmd_create.py`; run it + full suite and PASTE output.
- [ ] **Lifecycle/commit** path-scoped; `git add` new files; never push.

## Project conventions discovered (Step 0)

- CLI structure: `agent_workflows/cli.py` uses argparse subcommands (`install`, `setup`, `plan-names`, `check-local-leaks`, ...). Add a `research` subcommand group with a `new`/`new-comparison` action, mirroring the existing subparser style.
- Contract: import id/grammar/vocab/frontmatter from Order 01's `research_contract.py`; do NOT restate them.
- Test harness precedent: `tests/test_installer.py` etc. use throwaway dirs; mirror for tool tests.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C2-1 | HIGH | Low | weak-agent (G1) | usability | Hand-named research drifts (corpus shows `gpt56`/`gpt-56`, prefix vs suffix). A generator removes the drift. | spec 4.4/5.1, corpus survey |
| C2-2 | MEDIUM | Low | maintainer | ergonomics | The multi-model-then-synthesize pattern is recurring; scaffolding it in one command matches real workflow. | spec 5.3, corpus (aw-delivery/host-probe sets) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 5.1 | Add `aw research new` (args: `--set`, `--kind`, `--model?`, `--slug`, `--summary`, `--topic`, `--date?`): generate collision-checked id, resolve set (reuse date+next NN, or new set NN=00; omitted set = singleton from slug), validate/normalize vocab, kebab slug, write file + starter frontmatter (status: intake, consumed-by []). | `agent_workflows/cli.py`, `agent_workflows/research_cmd.py` (new) | Low | test: creates a well-formed name+frontmatter in a temp dir; second call to same set increments NN |
| 2 | 5.3 | Add `aw research new-comparison` (`--set --slug --models a,b,c`): create prompt at NN=00, one report slot per model NN=01..N, reserve a reconciliation-report slot. | `agent_workflows/research_cmd.py` | Low | test: yields prompt + N model reports + reconciliation, correct NN order, model tags in name+frontmatter |
| 3 | F6 | Self-revealing output: on success print the created path(s) and the next step ("run `aw research index`"). Add `--help` text. | `agent_workflows/research_cmd.py` | Low | test: stdout contains the created path and the index hint |
| 4 | G1 | Reject invalid input clearly (unknown kind/model with a suggestion; missing required args) without writing a file. | `agent_workflows/research_cmd.py` | Low | test: unknown kind exits nonzero, writes nothing, suggests closest |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Building/refreshing the index on create | n/a | scope | Index is Order 03; create only prints the hint. | Order 03 |
| Moving/renaming/regrouping existing files | n/a | scope | Order 04. | Order 04 |

## Scope check

- Over-scope: none - two create verbs + validation + help.
- Under-scope: MUST produce contract-conformant names + starter frontmatter and handle the singleton and multi-model cases.

## Required tests / validation

`tests/test_research_cmd_create.py`: `new` well-formed output + NN increment + singleton; `new-comparison` full scaffold with correct order/model tags; self-revealing stdout; invalid-input rejection writes nothing. Run that file then full `python -m pytest -q`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

Update `.agents/docs/research/README.md` usage section (created in Order 01) to show `aw research new`/`new-comparison`. Add the thin AGENTS.md pointer only in Order 07 (one place).

## Open questions

- Default derivation of `<set-id>`/`<slug>` when omitted: derive from `--summary`/`--slug`. Confirm the derivation rule at review.

## Validation and cross-check (verify before reporting done)

- [ ] Precheck: cite that `research_contract` symbols exist (Order 01 in executed/).
- [ ] Task 1: PASTE a created name + frontmatter from the test; confirm NN increments on a second same-set call.
- [ ] Task 2: PASTE the `new-comparison` output; confirm 00 prompt + N model reports + reconciliation with correct order and model tags.
- [ ] Task 3: confirm stdout shows the created path + the `aw research index` hint; cite.
- [ ] Task 4: confirm unknown kind exits nonzero and writes no file; cite.
- [ ] PASTE `pytest tests/test_research_cmd_create.py -q` + full-suite summary; leak-clean.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; else do not transition.

## Approval and execution gate

Proposal; human review + approval; not auto-executed. Requires Order 01 (`research_contract`); if absent, STOP. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation item is verified with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (create verbs only; no index/rename/archival). Never create or push a tag / Release / PyPI upload.
