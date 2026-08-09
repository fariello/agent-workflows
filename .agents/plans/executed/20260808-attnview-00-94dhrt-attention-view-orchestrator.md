# IPD (ORCHESTRATOR): attention view + cross-tree status model (Set attnview)

- Date: 2026-08-08
- Kind: orchestrator
- Concern: implement the approved spec `.agents/docs/specs/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`: a read-only `aw attention` command that maps each tree's native status onto a five-value cross-tree attention class and renders an on-demand view (JSON or human board, never committed), per-tree OWNER write verbs (starting `aw specs`) that maintain status + history under a transition/authority table, and a `/whatnext` rewired to consume the view, so a human/agent/CI can answer "what needs attention?" cheaply and deterministically and the specs blind spot is closed.
- Scope: ORCHESTRATOR for the ordered Set `attnview`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It does NOT itself change files (each child does its own edits). v1 covers specs + plans + research (prompts/comms excluded per OQ3; walkthroughs/roadmaps excluded per OQ8); no committed aggregate and no persisted snapshot in v1 (OQ9).
- Status: executed
- Set: attnview
- Order: 0
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 94dhrt

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): authored from the human-approved spec `20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`. Split into a Set because the work spans a contract/fixture-freezing phase, an owner-write verb (`aw specs`), a read-only cross-tree scanner (`aw attention`), a one-time specs migration, and the `/whatnext` + CI + docs wiring, with a clear dependency chain (contracts -> verbs/scanner -> migration -> consumer).
- 2026-08-08 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED (parallel audit lanes). Orchestrator findings L0-01 (note Child 03 owns tree classification + the truthful `local/` non-exclusion) and L0-02/L0-04 (name `implementing` as the executor-set path to spec `active`, and research native `active` as the live source of the `active` class in v1) FIXED. Set-wide: 22 findings across the 6 plans, all Low/Low-Medium remediation risk, all FIXED in place; no deferrals, no REPLAN. Structural lint conforming at author + review-finalize. Status draft -> reviewed.
- 2026-08-08 approved (human maintainer): "Approved all. Go." Status reviewed -> approved; cleared for execution via ipd-lifecycle.
- 2026-08-08 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): all five children executed in dependency order 01->02->03->04->05 via the ipd-lifecycle gate, each with its own V-* verified. Cross-IPD validation passed: contracts single-source in attention_contract.py (imported by specs.py+attention.py, no fork); aw attention is read-only (no write/git call); the class mapping is total over specs/plans/research; no per-tree tool regressed; execution order respected the table (transition commits d569304->6e3f1ed->2ae76aa->419fc97->dc51bee); output byte-deterministic + fail-closed. Final dogfood: full suite Ran 716 tests OK (skipped=1); aw attention --check + aw specs check exit 0 on this repo; aw plans/research index --check unregressed; leak-clean; no em/en dashes. The attention view + owner-written spec status ship (D125). The Set is complete.

## Goal

Deliver the attention view end to end: freeze the class enum + per-tree mappings + JSON/gate/history/approval contracts + fixtures (Order 01); build `aw specs set/note/check` enforcing the transition/authority table and typed gates (Order 02); build the read-only, fail-closed, byte-deterministic `aw attention` scanner + JSON/Markdown renderers (Order 03); migrate the existing specs into contract conformance without moving files (Order 04); rewire `/whatnext` to consume the view and wire the checks into CI + docs/DECISIONS (Order 05). Dogfood in this repo. Do not build prompts/comms adoption or a persisted snapshot (named later phases).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

The orchestrator's execution leaves gate the children and run the whole-Set checks, using the same stable E/V contract as every actionable IPD.

- [x] E-01 verify Child 01 (Phase 0 contracts + fixtures) is executed and its own two checklists are verified.
  - Depends on: none
  - Expected outcome: `attention_contract.py` (five-class enum + tree-policy inventory + exhaustive per-tree mappings), the JSON/serialization/history/gate/approval contracts, and the fixture corpus exist; the totality/coverage test passes.
  - Execution state: performed
- [x] E-02 verify Child 02 (`aw specs` owner verbs) is executed after Child 01 and its checklists are verified.
  - Depends on: E-01
  - Expected outcome: `aw specs set/note/check` enforce the authority table (human token for `approved`, evidence for `implemented`, `approved -> implementing` settable by the executor as the only source of a spec `active`), typed gates, single-file atomic writes, history-append; no git side effects.
  - Execution state: performed
- [x] E-03 verify Child 03 (read-only `aw attention` scanner) is executed after Children 01 and 02 and its checklists are verified.
  - Depends on: E-01, E-02
  - Expected outcome: `aw attention` renders byte-deterministic JSON/Markdown to stdout, `--check`/`--agent` fail closed on every violation class, writes nothing to disk, no `aw status` collision.
  - Execution state: performed
- [x] E-04 verify Child 04 (specs migration) is executed after Children 01 through 03 and its checklists are verified.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: every existing spec normalized to a bare-enum `- Status:` + a `## Workflow history` via the owner verb, paths preserved (zero renames); `aw attention --check` clean on the specs tree.
  - Execution state: performed
- [x] E-05 verify Child 05 (`/whatnext` rewire + CI + docs) is executed after Children 01 through 03 (04 recommended) and its checklists are verified.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `/whatnext` consumes `aw attention --format json` first and stops on an invalid view; CI runs `aw attention --check` + `aw specs check`; AGENTS.md pointer + specs README + DECISIONS + TODO updated.
  - Execution state: performed
- [x] E-06 run the cross-IPD validation (below).
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: single-source contracts (no fork), read-only boundary intact, mapping totality, no per-tree-tool regression, dependency-order correctness.
  - Execution state: performed
- [x] E-07 run the final suite and repository dogfood checks and paste actual output.
  - Depends on: E-06
  - Expected outcome: full suite green; `aw attention --check` + `aw specs check` clean on this repo; `aw plans index --check` + `aw research index --check` unchanged; leak-clean; no em/en dashes.
  - Execution state: performed

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260808-attnview-01-0i8ass-phase0-contracts-and-fixtures.md` | Freeze the five-class enum + tree-policy inventory + exhaustive per-tree mapping tables (specs/plans/research), the `## Workflow history` grammar, the versioned JSON schema + canonical serialization, the gate + output-safety contract, and the approval/authority contract; build fixtures for every status + every violation class. Resolves spec OQ1/OQ2/OQ4/OQ6/OQ10. | none |
| 02 | `20260808-attnview-02-u4q8ml-aw-specs-owner-verbs.md` | `aw specs set/note/check`: validate transitions against the authority table (human token for `approved`, evidence for `implemented`), typed gates, single-file atomic writes, history-append; no git. | 01 |
| 03 | `20260808-attnview-03-h3dadd-aw-attention-scanner.md` | Read-only `aw attention` full-scan over specs/plans/research; `--format json|markdown`, `--check`, `--agent`; byte-deterministic; fail-closed; output-safety; writes nothing. | 01, 02 |
| 04 | `20260808-attnview-04-dxoxgi-specs-migration.md` | One-time normalization of the existing specs to the contract via `aw specs` (bare-enum status + history + gates), paths preserved; a STOP-for-review gate on the status mapping. | 01, 02, 03 |
| 05 | `20260808-attnview-05-9y2fz1-whatnext-and-ci.md` | Rewire `/whatnext` to consume `aw attention --format json` first and stop on invalid; wire `aw attention --check` + `aw specs check` into CI; update AGENTS.md pointer + specs README + DECISIONS + TODO. | 01, 02, 03 (04 recommended) |

Execution order (dependency-correct): 01 -> 02 -> 03 -> 04 -> 05.

## Completion criteria (the whole Set is done only when)

- Each child (01 to 05) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- `aw attention --check` and `aw specs check` pass clean on this repo; `aw plans index --check` and `aw research index --check` are unchanged.
- After the Set completes, the approved spec `20260808-1945-01` is moved toward its terminal `implemented` state via `aw specs set` (a post-Set action, recorded with implementation evidence, NOT an E-*/V-* item here).

## Cross-IPD validation

- Single-source contracts: the class enum, tree-policy inventory, per-tree mappings, JSON schema, gate/history/approval grammars are defined ONCE (Child 01) and consumed by `aw specs` (02), `aw attention` (03), the migration (04), and `/whatnext` (05); no child forks them. Read them together and confirm no contradiction.
- Read-only boundary: `aw attention` performs NO writes (grep the module for any write/`atomic_write`/git call returns none); all writes go through `aw specs` (specs) or the existing `aw plans`/`aw research` verbs; no generic write router exists (OQ7). Confirm Child 03 owns the path->tree classification (tracked/excluded/unclassified) and does not rely on `iter_scan_files` to exclude gitignored `local/` lanes (`iter_scan_files` does NOT; the exclusion is Child 03's responsibility if such a tree enters scope).
- Mapping totality: the coverage test proves `class_of` is total over specs/plans/research native enums; an unmapped status is a violation, not a default.
- No per-tree regression: `aw plans index --check` and `aw research index --check` behave identically after the Set (their tests pass unchanged).
- Dependency correctness: execution order 01 -> 02 -> 03 -> 04 -> 05; no child uses a later child's symbols; the migration (04) runs only after the verbs (02) and checker (03) exist.
- Determinism + safety: `aw attention` output is byte-identical across varied `cwd`/`TZ`/`LANG` and rejects hostile descriptive fields (control chars, newlines, over-length, non-http gate URLs).
- Size check: each child stays within the IPD size guidance; if any grows past it during execution, split it further.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| prompts/comms adoption | scope | v1 covers the trees with settled contracts; prompts/comms deferred unless finalized in Phase 0 (OQ3). | Phase 3 / a later Set |
| walkthroughs/roadmaps status | scope | No real lifecycle semantics yet; excluded in the tree-policy inventory (OQ8). | Phase 3 |
| A committed aggregate / persisted `aw attention snapshot` | complexity | The view is ephemeral by design; a snapshot waits for a demonstrated non-CLI consumer (OQ9). | Phase 2 |
| A generic cross-tree `aw attention set` write router | complexity | Writes are owner-local; a router waits until every owner has a stable mutation API (OQ7). | not planned |
| plans native `executing` state (for `active`) | functionality | Owner-local plans decision; until added, plans map to `ready` (OQ5). Note: research's native `active` (research_contract.py:133) IS the live source of the `active` class in v1, and specs reach `active` via `implementing`; only plans lack `active` until an `executing` state is added. | plans owner, later |

## Scope check

- Over-scope: none - this orchestrator only coordinates; the children make the bounded edits. The determinism/safety rigor is scoped to observable output, with the exact serialization profile a Phase-0 (Child 01) deliverable.
- Under-scope: the Set MUST deliver, for specs+plans+research: the frozen contracts + fixtures, the `aw specs` owner verbs, the read-only `aw attention` scanner, the specs migration, and the `/whatnext` + CI + docs wiring. Anything less ships a tool nothing consumes or a half-standardized specs tree.

## Required tests / validation

Per-child validation (each child names its literal commands) plus the cross-IPD checks above. Run `python3 -m unittest discover -s tests -t .` after each child and at the end; paste ACTUAL output (`Ran N tests ... OK`); `aw attention --check` + `aw specs check` clean on this repo; `aw plans index --check` + `aw research index --check` unchanged; `aw sanitize --agent` clean; no em/en dashes.

## Open questions

### OQ-01: spec open questions OQ1 to OQ10 ownership

- Blocking: no
- Status: resolved
- Owner: the individual children
- Resolution or deferral rationale: the spec's OQ3/OQ7/OQ8/OQ9 were RESOLVED with the human at /plan-review (v1 scope = specs+plans+research; read-only attention + `aw specs` writes, no router; walkthroughs/roadmaps excluded v1; no persisted snapshot v1). OQ1/OQ2/OQ4/OQ6/OQ10 are Phase-0 design deliverables OWNED by Child 01, which freezes them into tested contracts. OQ5 (plans native `executing`) is an owner-local plans decision deferred without blocking (plans map to `ready` until then). The orchestrator does not re-open these.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: cite Child 01 in `.agents/plans/executed/` with `Status: executed` and its Validation checklist verified; confirm the totality/coverage test passes and the fixtures cover every status + violation class.
  - Observed evidence: `.agents/plans/executed/20260808-attnview-01-0i8ass-phase0-contracts-and-fixtures.md` is `Status: executed`, V-01..V-08 pass (product commit d569304). `tests.test_attention_contract.MappingTotalityTests` (5 tests) pass; fixtures under `tests/fixtures/attnview/` cover every spec status + every violation class.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: cite Child 02 executed after Child 01 with its checklists verified; confirm `aw specs set` refuses agent-set `approved` and evidence-less `implemented`.
  - Observed evidence: `.agents/plans/executed/20260808-attnview-02-u4q8ml-aw-specs-owner-verbs.md` executed after 01 (product 53c35c8, transition 6e3f1ed), V-01..V-06 pass. `test_specs_verbs.SetTests` confirms a no-TTY `set --status approved` is refused byte-identical and `--status implemented` without a resolvable evidence citation is refused.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: cite Child 03 executed after Children 01 and 02 with its checklists verified; confirm `aw attention` writes nothing, is byte-deterministic, and fails closed.
  - Observed evidence: `.agents/plans/executed/20260808-attnview-03-h3dadd-aw-attention-scanner.md` executed after 01/02 (product 39de8e5, transition 2ae76aa), V-01..V-07 pass. `attention.py` has no write/git call (grep confirmed); `test_attention` proves byte-identical output under varied TZ/LANG/cwd, fail-closed `--check`, exit 2 on could-not-run, and writes-nothing.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: cite Child 04 executed after Children 01 through 03 with its checklists verified; confirm the specs tree is `--check` clean and `git` shows zero spec renames.
  - Observed evidence: `.agents/plans/executed/20260808-attnview-04-dxoxgi-specs-migration.md` executed after 01-03 (verb 7135e9f, fix 6bb2a42, migrated specs ebae031, transition 419fc97), V-01..V-05 pass. All 10 specs migrated via `aw specs migrate`; `aw specs check` -> all conform; `aw attention --check` shows no specs-tree violation; `git` showed 10 `M`, 0 `R` (zero renames).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: cite Child 05 executed with its checklists verified; confirm `/whatnext` consumes the view first and CI gates the checks.
  - Observed evidence: `.agents/plans/executed/20260808-attnview-05-9y2fz1-whatnext-and-ci.md` executed (c7a2f86, 56f6a70, 0beb7f6, f8e150c, transition dc51bee), V-01..V-06 pass. `whatnext.md` Step 1 runs `aw attention --format json` first and stops on invalid; the CI `attention-check` job runs `aw specs check` + `aw attention --check`; AGENTS pointer + DECISIONS D125 + TODO + specs README updated.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: confirm the contracts are single-source (no fork), the read-only boundary holds (no writes in `aw attention`), the mapping is total, no per-tree tool regressed, and execution order respected the table.
  - Observed evidence: the contracts live ONCE in `attention_contract.py`, imported by `specs.py` and `attention.py` (no fork). `attention.py` performs no writes (read-only boundary). `class_of` is total over specs/plans/research (coverage test). `aw plans index --check` clean but for the 2 known strays; `aw research index --check` shows only the pre-existing k7m2xq example dangler (no regression). Execution order 01->02->03->04->05 respected (transition commits d569304 -> 6e3f1ed -> 2ae76aa -> 419fc97 -> dc51bee in order). Determinism + fail-closed safety tests pass.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste the actual final `python3 -m unittest` summary; confirm `aw attention --check` + `aw specs check` clean; `aw plans index --check` + `aw research index --check` unchanged; leak-clean; no em/en dashes.
  - Observed evidence: final full suite `python3 -m unittest discover -s tests -t .` -> `Ran 716 tests in 155.892s / OK (skipped=1)`. `aw attention --check --agent` exit 0; `aw specs check` exit 0; `aw plans index --check` clean but for the 2 known stray other-agent plans; `aw research index --check` unregressed; `aw sanitize --agent` exit 0; no em/en dashes in authored files.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
