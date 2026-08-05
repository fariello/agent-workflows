# IPD: `aw research new` / `new-comparison` creation tool (Set `research-org`, Order 2)

- Date: 2026-07-30
- Kind: child
- Concern: give agents and humans a deterministic command to create a correctly-named research doc with starter frontmatter, so naming is a tool call (not a fallible convention). Encodes the multi-model comparison pattern as first-class.
- Scope: the create verbs only, consuming the Order-01 contract. No indexing (Order 03), no rename (04), no archival (05). Requires Order 01 executed (imports `research_contract`); if its symbols are absent, STOP.
- Status: to-review
- Set: research-org
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the first behavior on top of the Order-01 contract.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.

## Goal

`aw research new` and `aw research new-comparison`: generate a unique `<id6>`, resolve/derive the set + next `NN`, validate/normalize `<model>`/`<kind>`, assemble the filename, and write starter frontmatter (status: intake), then print a self-revealing next step (F6). This is spec Sections 5.1 and 5.3.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: create verbs

- [ ] E-01 confirm Order 01 is executed and `research_contract` is importable, else STOP.
  - Depends on: none
  - Expected outcome: `research_contract` symbols (id, grammar, vocab, frontmatter) are present; if absent the tool halts before writing.
  - Execution state: pending
- [ ] E-02 add `aw research new` (args `--set`, `--kind`, `--model?`, `--slug`, `--summary`, `--topic`, `--date?`): generate a collision-checked id, resolve the set (reuse date+next NN, or new set NN=00; omitted set = singleton from slug), validate/normalize vocab, kebab the slug, and write the file plus starter frontmatter (status: intake, consumed-by []).
  - Depends on: E-01
  - Expected outcome: a well-formed name plus frontmatter appears in a temp dir; a second call to the same set increments NN.
  - Execution state: pending
- [ ] E-03 add `aw research new-comparison` (`--set --slug --models a,b,c`): create the prompt at NN=00, one report slot per model at NN=01..N, and reserve a reconciliation-report slot.
  - Depends on: E-01, E-02
  - Expected outcome: a prompt plus N model reports plus a reconciliation slot in correct NN order with model tags in name and frontmatter.
  - Execution state: pending

### Task group 2: output, safety, tests

- [ ] E-04 add self-revealing output: on success print the created path(s) and the next step ("run `aw research index`"), and add `--help` text.
  - Depends on: E-02, E-03
  - Expected outcome: stdout contains the created path and the index hint.
  - Execution state: pending
- [ ] E-05 reject invalid input clearly (unknown kind/model with a closest-match suggestion; missing required args) without writing a file.
  - Depends on: E-02
  - Expected outcome: an unknown kind exits nonzero, writes nothing, and suggests the closest valid value.
  - Execution state: pending
- [ ] E-06 add `tests/test_research_cmd_create.py` (new well-formed output + NN increment + singleton; new-comparison scaffold; self-revealing stdout; invalid-input rejection); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- CLI structure: `agent_workflows/cli.py` uses argparse subcommands (`install`, `setup`, `plan-names`, `check-local-leaks`, ...). Add a `research` subcommand group with a `new`/`new-comparison` action, mirroring the existing subparser style.
- Contract: import id/grammar/vocab/frontmatter from Order 01's `research_contract.py`; do NOT restate them.
- Test harness precedent: `tests/test_installer.py` etc. use throwaway dirs; mirror for tool tests.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C2-1 | HIGH | Low | weak-agent (G1) | usability | Hand-named research drifts (corpus shows `gpt56`/`gpt-56`, prefix vs suffix). A generator removes the drift. | spec 4.4/5.1, corpus survey |
| C2-2 | MEDIUM | Low | maintainer | ergonomics | The multi-model-then-synthesize pattern is recurring; scaffolding it in one command matches real workflow. | spec 5.3, corpus (aw-delivery/host-probe sets) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 5.1 | Add `aw research new` (args: `--set`, `--kind`, `--model?`, `--slug`, `--summary`, `--topic`, `--date?`): generate collision-checked id, resolve set (reuse date+next NN, or new set NN=00; omitted set = singleton from slug), validate/normalize vocab, kebab slug, write file + starter frontmatter (status: intake, consumed-by []). | `agent_workflows/cli.py`, `agent_workflows/research_cmd.py` (new) | Low | E-02 |
| 2 | 5.3 | Add `aw research new-comparison` (`--set --slug --models a,b,c`): create prompt at NN=00, one report slot per model NN=01..N, reserve a reconciliation-report slot. | `agent_workflows/research_cmd.py` | Low | E-03 |
| 3 | F6 | Self-revealing output: on success print the created path(s) and the next step ("run `aw research index`"). Add `--help` text. | `agent_workflows/research_cmd.py` | Low | E-04 |
| 4 | G1 | Reject invalid input clearly (unknown kind/model with a suggestion; missing required args) without writing a file. | `agent_workflows/research_cmd.py` | Low | E-05 |

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

### OQ-01: default derivation of `<set-id>`/`<slug>` when omitted

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: derive the omitted `<set-id>`/`<slug>` from `--summary`/`--slug` (a slug-derived singleton when no set is given). Confirm the exact derivation rule at review; if it changes, only this child changes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite that `research_contract` symbols exist (Order 01 in `executed/`) and that the tool halts when they are absent.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a created name + frontmatter from the test and confirm NN increments on a second same-set call.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the `new-comparison` output; confirm the 00 prompt + N model reports + reconciliation with correct order and model tags.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: confirm stdout shows the created path + the `aw research index` hint; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm an unknown kind exits nonzero and writes no file; cite.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `pytest tests/test_research_cmd_create.py -q` + the full-suite summary (new tests pass, suite green); leak-clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Order 01 (`research_contract`); if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (create verbs only; no index/rename/archival). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
