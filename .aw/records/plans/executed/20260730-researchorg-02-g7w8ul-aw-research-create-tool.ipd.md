# IPD: `aw research new` / `new-comparison` creation tool (Set `research-org`, Order 2)

- Date: 2026-07-30
- Kind: child
- Concern: give agents and humans a deterministic command to create a correctly-named research doc with starter frontmatter, so naming is a tool call (not a fallible convention). Encodes the multi-model comparison pattern as first-class.
- Scope: the create verbs only, consuming the Order-01 contract. No indexing (Order 03), no rename (04), no archival (05). Requires Order 01 executed (imports `research_contract`); if its symbols are absent, STOP.
- Status: executed
- Set: researchorg (research-org)
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: g7w8ul

## Workflow history

- 2026-07-30 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `research-org`; the first behavior on top of the Order-01 contract.
- 2026-08-03 quarantined (opencode its_direct/pt3-claude-opus-4.8-1m-us): deferred by the maintainer's IPD-system-first sequencing; quarantined pending re-authoring to the new E-*/V-* shape.
- 2026-08-03 re-authored (opencode its_direct/pt3-claude-opus-4.8-1m-us): lifted out of quarantine and converted to the new IPD shape (Kind + E-*/V-* bijection + Execution state / Result fields + allocation watermark + OQ-* grammar + Size assessment) per DECISIONS D122; content preserved. Conforms to `aw ipd lint --phase author`.
- 2026-08-07 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (pytest->unittest), PR-C02-2 (writing-command safety: dry-run/`--apply`/atomic/no-clobber), PR-C02-4 (full spec-5.8 frontmatter incl. `outcome`), PR-C02-5 (reconciliation NN=N+1), PR-C02-3 (index-hint worded informational), PR-C02-6 (suggestion via contract API), PR-C02-7 (id collision-checked against on-disk ids), OQ-01 derivation pinned.
- 2026-08-07 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): built `agent_workflows/research_cmd.py` (`aw research new`/`new-comparison`) + wired the `research` subparser in `cli.py` + `tests/test_research_cmd_create.py` (10 tests); product commit 0dd0afe; new tests pass and the full suite is green (Ran 596 tests OK, skipped=1); leak-clean; no em/en dashes. All E-01..E-06 performed and V-01..V-06 pass.

## Goal

`aw research new` and `aw research new-comparison`: generate a unique `<id6>`, resolve/derive the set + next `NN`, validate/normalize `<model>`/`<kind>`, assemble the filename, and write starter frontmatter (status: intake), then print a self-revealing next step (F6). This is spec Sections 5.1 and 5.3.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: create verbs

- [x] E-01 confirm Order 01 is executed and `research_contract` is importable, else STOP.
  - Depends on: none
  - Expected outcome: `research_contract` symbols (id, grammar, vocab, frontmatter) are present; if absent the tool halts before writing.
  - Execution state: performed
- [x] E-02 add `aw research new` (args `--set`, `--kind`, `--model?`, `--slug`, `--summary`, `--topic`, `--date?`): generate an id collision-checked against all existing on-disk `<id6>` tokens (retry on collision), resolve the set (reuse date+next NN, or new set NN=00; omitted set = singleton from slug), validate/normalize vocab, kebab the slug, and write the file plus the FULL spec-5.8 starter frontmatter (`id`, `created`, `set`, `order`, `topic`, `model`, `kind`, `status: intake`, `outcome: none-yet`, `summary`, `consumed-by: []`). Writing-command safety mirrors `aw ipd scaffold`: preview by default, explicit `--apply` to write, atomic write-to-temp-rename, refuse to clobber an existing file without `--overwrite`, nonzero exit on any internal failure (never a false success).
  - Depends on: E-01
  - Expected outcome: a well-formed name plus a frontmatter block that passes `research_contract`'s validator appears in a temp dir under `--apply`; dry-run writes nothing; a second call to the same set increments NN.
  - Execution state: performed
- [x] E-03 add `aw research new-comparison` (`--set --slug --models a,b,c`): create the prompt at NN=00, one report slot per model at NN=01..N, and reserve a reconciliation-report slot at NN=N+1 (the synthesis is the LAST member, spec 4.2).
  - Depends on: E-01, E-02
  - Expected outcome: a prompt (00) plus N model reports (01..N) plus a reconciliation slot (N+1) in exact NN order with model tags in name and frontmatter.
  - Execution state: performed

### Task group 2: output, safety, tests

- [x] E-04 add self-revealing output: on success print the created path(s) and a next-step hint that names the index refresh (worded as an informational suggestion, since `aw research index` is delivered by Order 03 and may not yet exist), and add `--help` text.
  - Depends on: E-02, E-03
  - Expected outcome: stdout contains the created path and an informational index-refresh hint.
  - Execution state: performed
- [x] E-05 reject invalid input clearly using `research_contract`'s vocab/normalization API for the closest-match suggestion (do NOT implement a second matcher): unknown kind/model returns the contract's suggestion; missing required args are reported; nothing is written.
  - Depends on: E-02
  - Expected outcome: an unknown kind exits nonzero, writes nothing, and suggests the closest valid value via the contract API.
  - Execution state: performed
- [x] E-06 add `tests/test_research_cmd_create.py` (new well-formed output + NN increment + singleton; new-comparison scaffold; self-revealing stdout; invalid-input rejection); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- CLI structure: `agent_workflows/cli.py` uses argparse subcommands (`install`, `setup`, `plan-names`, `check-local-leaks`, ...). Add a `research` subcommand group with a `new`/`new-comparison` action, mirroring the existing subparser style.
- Contract: import id/grammar/vocab/frontmatter (and the vocab-suggestion/normalization API) from Order 01's `research_contract.py`; do NOT restate or reimplement them.
- Writing-command safety precedent: `aw ipd scaffold`/`sync` (`ipd_authoring.py`) - preview/dry-run default, explicit `--apply`, atomic write-to-temp-rename, no-clobber, nonzero-on-failure. Mirror it.
- Test harness precedent: `tests/test_installer.py` etc. use throwaway dirs; mirror for tool tests.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C2-1 | HIGH | Low | weak-agent (G1) | usability | Hand-named research drifts (corpus shows `gpt56`/`gpt-56`, prefix vs suffix). A generator removes the drift. | spec 4.4/5.1, corpus survey |
| C2-2 | MEDIUM | Low | maintainer | ergonomics | The multi-model-then-synthesize pattern is recurring; scaffolding it in one command matches real workflow. | spec 5.3, corpus (aw-delivery/host-probe sets) |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 5.1/5.8 | Add `aw research new`: collision-checked id, resolve set, validate/normalize vocab, kebab slug, write FULL spec-5.8 frontmatter; preview default + `--apply` + atomic write + no-clobber + nonzero-on-failure. | `agent_workflows/cli.py`, `agent_workflows/research_cmd.py` (new) | Low | E-02 |
| 2 | 5.3/4.2 | Add `aw research new-comparison`: prompt NN=00, model reports NN=01..N, reconciliation NN=N+1. | `agent_workflows/research_cmd.py` | Low | E-03 |
| 3 | F6 | Self-revealing output: created path(s) + an informational index-refresh hint (index is Order 03). Add `--help`. | `agent_workflows/research_cmd.py` | Low | E-04 |
| 4 | G1 | Reject invalid input via the contract's suggestion API (no second matcher); write nothing. | `agent_workflows/research_cmd.py` | Low | E-05 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Building/refreshing the index on create | n/a | scope | Index is Order 03; create only prints the hint. | Order 03 |
| Moving/renaming/regrouping existing files | n/a | scope | Order 04. | Order 04 |

## Scope check

- Over-scope: none - two create verbs + validation + help.
- Under-scope: MUST produce contract-conformant names + starter frontmatter and handle the singleton and multi-model cases.

## Required tests / validation

`tests/test_research_cmd_create.py`: `new` well-formed output + full-frontmatter-passes-validator + NN increment + singleton + dry-run-writes-nothing + `--apply`-writes-atomically + no-clobber; `new-comparison` full scaffold with correct order (00 prompt, 01..N models, N+1 reconciliation) + model tags; self-revealing stdout; invalid-input rejection writes nothing (suggestion via contract API). Run that file then full `python3 -m unittest discover -s tests -t .`; PASTE both (the `Ran N tests ... OK` summary). Leak-clean; no em/en dashes.

## Spec / documentation sync

Update `.agents/docs/research/README.md` usage section (created in Order 01) to show `aw research new`/`new-comparison`. Add the thin AGENTS.md pointer only in Order 07 (one place).

## Open questions

### OQ-01: default derivation of `<set-id>`/`<slug>` when omitted

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: RESOLVED at review (2026-08-07). When `--set` is omitted, the doc is a singleton whose `<set-id>` is derived by kebab-normalizing the `--slug` (falling back to a kebab of `--summary` if `--slug` is also omitted); `<id6>` remains the stable citation handle regardless.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: cite that `research_contract` symbols exist (Order 01 in `executed/`) and that the tool halts when they are absent.
  - Observed evidence: Order 01 is executed at `.agents/plans/executed/20260730-researchorg-01-3x7po2-research-naming-and-frontmatter-contract.md`; `agent_workflows/research_contract.py` is present and imported at the top of `research_cmd.py` (`from agent_workflows import research_contract as R`), so an absent contract raises ImportError before any write. `research new`/`new-comparison` consume the contract's id/grammar/vocab/frontmatter without restating them.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste a created name + full frontmatter and confirm it passes `research_contract`'s validator; confirm NN increments on a second same-set call; confirm dry-run wrote nothing and `--apply` wrote atomically and refused to clobber.
  - Observed evidence: `NewPlanTests`/`WriteSafetyTests` pass. Example created name `20260726-aw-delivery-00-<id6>-delivery-notes.gpt56.research-report.md` with a full 11-field frontmatter block (`status: intake`, `outcome: none-yet`) that `R.validate_frontmatter` accepts (returns `[]`). Second same-set call increments NN 00 -> 01 sharing the set date. `test_dry_run_writes_nothing` (file absent after preview), `test_apply_writes_atomically` (file present, no `.research-tmp-*` leftover), `test_no_clobber_without_overwrite` (exit 1, original bytes preserved). CLI smoke run confirmed end to end.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste the `new-comparison` output; confirm the 00 prompt + 01..N model reports + N+1 reconciliation in exact order with model tags.
  - Observed evidence: `ComparisonTests::test_scaffold_order_and_tags` passes: `--models gpt56,sonnet5,gemini31pro` yields 5 files with orders `["00","01","02","03","04"]`; order 00 kind `research-prompt` (no model); 01 model `gpt56`; order 04 kind `reconciliation-report` model `reconciliation`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: confirm stdout shows the created path + the informational index-refresh hint; cite.
  - Observed evidence: `_emit_and_write` prints `wrote <path>` (or `--- would write <path> ---` on dry-run) then `next step (informational): ... run \`aw research index\` to refresh the manifest`. Confirmed in the CLI smoke run and in the test stdout.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: confirm an unknown kind exits nonzero, writes no file, and returns the contract API's closest-match suggestion; cite.
  - Observed evidence: `NewPlanTests::test_unknown_kind_rejected_with_suggestion` and `ComparisonTests::test_unknown_model_rejected` pass: `plan_new(kind="reserch-reprt")` returns `(None, "unknown kind ...; did you mean ...?")` via `R.normalize_kind` (the contract API, not a second matcher) and writes nothing; the CLI handler prints `error: ...` and returns exit 2.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_research_cmd_create -v` + the full-suite `Ran N tests ... OK` summary (new tests pass, suite green); leak-clean.
  - Observed evidence: `python3 -m unittest tests.test_research_cmd_create` -> `Ran 10 tests in 0.006s / OK`. Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 596 tests in 145.536s / OK (skipped=1)`. `aw sanitize --agent` exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Order 01 (`research_contract`); if absent, STOP. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (create verbs only; no index/rename/archival). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
