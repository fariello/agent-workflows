# IPD: Attention-visible backlog tier (records/backlog + aw backlog)

- Date: 2026-08-13
- Kind: child
- Concern: `aw attention` (which feeds `/whatnext`) scans only plans/specs/research/actions, so committed work captured in the free-prose `TODO.md` is silently omitted - a false-comprehensiveness risk. Implement a lightweight, tracked, attention-visible backlog tier so committed work surfaces while uncommitted maybes stay quiet.
- Scope: `agent_workflows/attention_contract.py` (`TREE_POLICY` + `CLASS_MAPS`/`_BACKLOG_MAP`), `agent_workflows/artifact_core.py` (`SCAN_ROOTS`), `agent_workflows/attention.py` (scan/`_classify_tree`/`_record_for` + a `_backlog_record` builder), a new `agent_workflows/backlog.py` (the `aw backlog new|set|check` verbs), `agent_workflows/cli.py` (wire `aw backlog` and the `aw att` alias; the parked reveal already exists as `aw attention --all`), the new `records/backlog/` tree scaffold + `README.md`, the `TODO.md` migration, docs (AGENTS.md pointer), and tests. Implements the approved spec `.agents/docs/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md`.
- Status: draft
- Highest E allocated: 08
- Author: opencode Opus 4.8
- Id: crv40v
- Set: backlogtier (attention-visible backlog tier)
- Order: 1
## Workflow history

- 2026-08-13 draft (opencode Opus 4.8): authored from the approved spec 20260813-1833-01 (attention-visible backlog tier). Implements the records-class backlog/ sub-tree, the four attention touch-points, the aw backlog verbs, the aw att alias (parked reveal uses the existing aw attention --all), and the TODO.md migration, per the spec's resolved OQ1-OQ7.

## Goal

Add a `records`-class `backlog/{open,blocked,parked,done}/` tree of lightweight frontmatter+prose items, an `aw backlog new|set|check` verb family to manage them, and the four `aw attention` integration touch-points so committed (`open`) items surface as `ready` and gated (`blocked`) items as `blocked` in `aw attention` + `/whatnext`, while uncommitted `parked` maybes are tracked-but-quiet (auto-hidden from the default board, in `--format json`, revealed by the existing `aw attention --all`). Migrate the existing `TODO.md` committed sections into the tree so nothing committed is invisible.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: The backlog tree + item contract

- [ ] E-02 Define the backlog item contract and scaffold the `records`-class `backlog/` tree. Item = one file per the spec Section 6.1: frontmatter `id` (id6), `created`, `status` (`open|blocked|parked|done`), `set`, `priority` (`high|medium|low`), `kind` (`bug|feature|chore|security|followup`), `summary`, and `gate-kind`/`gate-ref` REQUIRED iff `status: blocked`; prose body. Status encoded BOTH by directory (`open/blocked/parked/done`) and frontmatter, which MUST agree. Clustering filename `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (singleton = set of one). Create `records/backlog/{open,blocked,parked,done}/` + `README.md` at the pre-migration path `.agents/backlog/` (dual-path with `.aw/records/backlog/` handled by the resolver + `_classify_tree` normalization, like plans). Reuse `artifact_core` (id6, atomic write); do NOT fork.
  - Depends on: none
  - Expected outcome: a conformant backlog item file validates; a stray/malformed one is detectable; the tree exists with per-status directories + README.
  - Execution state: pending

### Task group 2: `aw backlog` verbs

- [ ] E-03 Implement `agent_workflows/backlog.py` with `new`, `set`, `check` and wire them at the two `cli.py` edit points (`_build_parser` adds a `backlog` subparser; `_dispatch` routes), mirroring `aw research`/`aw specs`. `new` creates a conformant item (dry-run by default, `--apply` to write), owning the clustering name + frontmatter. `set` moves the file between `open/blocked/parked/done`, updates frontmatter `status`, requires `--gate-kind`/`--gate-ref` when moving to `blocked`, and appends an append-only `## Workflow history` line (D52 style). `check` validates the tree fail-closed (frontmatter present + valid enums; status-mirrors-directory; gate pair present iff blocked; id6 present/unique; nonempty summary) with the `Drift`/`--agent`/exit convention. No `index`/`find` in v1 (spec OQ5).
  - Depends on: E-02
  - Expected outcome: `aw backlog new/set/check` create/transition/validate items; `check` exits nonzero on a malformed tree and 0 clean; blocked-without-gate is rejected.
  - Execution state: pending

### Task group 3: aw attention integration (the four touch-points)

- [ ] E-04 Register the backlog tree in the attention contract: add `_BACKLOG_MAP = {"open": READY, "blocked": BLOCKED, "parked": PARKED, "done": DONE}` to `CLASS_MAPS["backlog"]` in `attention_contract.py` (a PURE, TOTAL mapping; unknown status -> `attention.unknown-status`, never a default), and add a `TreePolicy("backlog", ".agents/backlog", ...)` to `TREE_POLICY` so `_classify_tree` recognizes the root (its `.aw/records/` -> `.agents/` normalization makes one root cover both layouts).
  - Depends on: E-02
  - Expected outcome: `class_of("backlog", s)` is defined for every backlog status and raises on unknown; `_classify_tree` maps a backlog file (either layout) to the backlog policy.
  - Execution state: pending

- [ ] E-05 Make `aw attention` discover + record backlog items: add the backlog root(s) (`.agents/backlog` and `.aw/records/backlog`) to `SCAN_ROOTS` in `artifact_core.py`, and add a `backlog` branch in `attention.py` `_record_for` + a `_backlog_record` builder (reading frontmatter `status`/`priority`/`summary`/`id`, mirroring `_plans_record`/`_research_record`) with `scan()` routing backlog files to it. NOTE (verified during authoring): the hot-glance vs JSON split needs NO new code - `attention.render_board` (attention.py:354) ALREADY hides `DONE`/`PARKED` class groups unless `show_all`, and `render_json` always includes them. So once a backlog item maps to its class (E-04), `open`->`ready` and `blocked`->`blocked` show in the default board while `parked`->`parked` is auto-hidden (shown under `--all`, always in `--format json`). Do NOT build a separate exclusion filter. `priority` is carried into the record and used to order the `ready` group (high first) - confirm whether `render_board` currently sorts within a class; if not, add priority ordering for backlog `ready` items only, minimally.
  - Depends on: E-02
  - Expected outcome: `aw attention` includes backlog items with correct classes; `open`/`blocked` show in the default board + `/whatnext`; `parked` is auto-hidden from the default board (visible under `--all`) and always in `--format json`; `aw attention --check` stays clean with backlog items present.
  - Execution state: pending

- [ ] E-06 Add the `aw att` alias for `aw attention` (a small `cli.py` edit). NOTE (verified during authoring): the "reveal parked" capability the spec's OQ2 asked for ALREADY EXISTS as `aw attention --all` (cli.py `--all` "Show done/parked groups in the board"; `attention.render_board` hides DONE/PARKED groups unless `show_all`, printing `## parked (N) [hidden; use --all]`). So do NOT add a new `aw attention all` subcommand (it would be redundant); the only new surface here is the `aw att` alias. The spec's `aw attention all` phrasing is superseded by the existing `--all` flag.
  - Depends on: E-02
  - Expected outcome: `aw att` behaves identically to `aw attention` (incl. `--all`, `--format json`, `--check`); `aw attention --all` reveals `parked` backlog items that the default board hides (existing behavior, confirmed post-implementation).
  - Execution state: pending

### Task group 4: Migrate TODO.md + docs

- [ ] E-07 Migrate `TODO.md` into the backlog tree per spec OQ1, following an EXPLICIT procedure (the migration is human-in-the-loop for judgment calls, NOT a mechanical sweep - the current TODO.md is NOT flat; see the per-item rules). Procedure:
  1. INVENTORY first: enumerate every committed-tier item (each `- **...**` lead bullet under "Known bugs to fix", "Security follow-ups", "Planned next (designed, deferred)") and every "Consider and possibly implement (may be declined)" item; record the count. This count is the reconciliation baseline (step 6).
  2. ONE lead bullet -> ONE backlog item (via `aw backlog new`), body = that bullet's full prose (sub-bullets included). Preserve any embedded Set grouping: items already clustered in TODO.md (e.g. the "IPD 2/3/4" broker group, and the two distinct "Order 1/2/3/4" pipeline Sets) become backlog items sharing a `set` id; unrelated singletons get their own set.
  3. STATUS derivation: default committed items -> `open`; an item whose prose is explicitly marked DONE (e.g. "Order 1 - DONE (D88)", "Order 2 - DONE (D91)") -> `done/` with a history line citing the referenced decision/commit (do NOT create an `open` item for already-done work); an item that names a concrete GATE it waits on (e.g. the split-brain-install bug is gated on the awphysical migration; a "Consider" item explicitly deferred pending another decision) -> `blocked/` with `gate-kind`/`gate-ref` (e.g. `plan`/the awphysical order, or `spec`/id); "Consider and possibly implement (may be declined)" items -> `parked/`. Ambiguous status/gate assignments are surfaced to the maintainer, not guessed.
  4. FIELD derivation per item: `kind` from content (`bug`/`security`/`feature`/`chore`/`followup`); `priority` high/medium/low (bugs+security default high, planned-next medium, unless the prose implies otherwise - confirm with the maintainer where unclear); `summary` = a one-line distillation of the bullet's lead sentence.
  5. "Notes" section stays PROSE in `TODO.md` (Tier-3). Reduce `TODO.md` to a short pointer at the backlog tree + the retained Notes.
  6. RECONCILE: assert the number of migrated backlog items (open+blocked+parked+done) EQUALS the step-1 inventory count (minus any the maintainer explicitly drops); list the before -> after mapping so no committed item is silently lost. Add the AGENTS.md pointer (committed backlog lives in the records backlog tree, surfaced by `aw attention`; `TODO.md` holds only uncommitted notes) and the `records/backlog/README.md`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: every committed TODO item maps to exactly one backlog file at the correct status (open/blocked/parked/done, DONE-marked items NOT resurrected as open), embedded Sets preserved, the before->after reconciliation shows zero loss, `aw attention` shows the open/blocked ones, `TODO.md` retains only Notes + a pointer, docs updated.
  - Execution state: pending

### Task group 5: Tests

- [ ] E-08 Add tests: (a) `_BACKLOG_MAP` purity/totality + `class_of("backlog", ...)` incl. unknown-status raising; (b) attention inclusion - `open`/`blocked` in the board, `parked` auto-hidden from the default board but present in `--format json` and revealed by the existing `aw attention --all`, plus the `aw att` alias equivalence; (c) `aw backlog new/set/check` incl. blocked-requires-gate, status-mirrors-directory, and fail-closed `check` cases; (d) a post-migration assertion that a representative migrated item surfaces in `aw attention`. Full suite green (`pytest -n auto` / `unittest discover`).
  - Depends on: E-02, E-03, E-04, E-05, E-07
  - Expected outcome: new tests pass; full suite green; `aw attention --check` + `aw backlog check` clean on the repo after migration.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw attention` discovery is NOT generic (spec PR-001): a new tree needs a `TreePolicy` (`attention_contract.TREE_POLICY`), a `SCAN_ROOTS` entry (`artifact_core.py`), and a `_record_for` branch (`attention.py`) - not just a `CLASS_MAPS` line.
- `records`-class trees are dual-path: `.agents/<x>` pre-migration, `.aw/records/<x>` post-migration; `attention._classify_tree` normalizes `.aw/records/` -> `.agents/`, and `SCAN_ROOTS` lists BOTH (as plans does).
- The `actions` tree uses a bespoke scan path; backlog should instead use the standard `iter_scan_files` + `_classify_tree` + `_record_for` path (it is a `records` tree like plans, not `state`).
- Status-mirrors-directory + append-only workflow history + machine-readable bare-enum status are the shipped conventions (D52, D125) to reuse; the leak sanitizer + zero-runtime-deps + Python 3.9 constraints apply.

## Findings

- The gap and design are fully specified and reviewed in `20260813-1833-01-attention-visible-backlog-tier.spec.md` (approved). This IPD implements it; OQ1-OQ7 are all resolved there (records location; open|blocked|parked|done + typed gate; priority high|medium|low + Set from v1; no v1 manifest; promotion = done+plan-cite; parked JSON-only, revealed by the existing `aw attention --all`; add `aw att` alias).

## Proposed changes (ordered, validatable)

1. Backlog item contract + `records/backlog/` tree scaffold.
2. `agent_workflows/backlog.py` + `aw backlog new|set|check` CLI.
3. Attention contract: `_BACKLOG_MAP` + `TreePolicy`.
4. Attention discovery/record: `SCAN_ROOTS` + `_backlog_record` + `scan` routing; parked hot-glance exclusion.
5. `aw att` alias (parked reveal already provided by the existing `aw attention --all`).
6. `TODO.md` migration + AGENTS.md/README docs.
7. Tests + full-suite green.

## Deferred / out of scope (with reason)

- A backlog manifest (`INDEX.json` + `aw backlog index/find`): deferred to a later phase (spec OQ5); directory + `aw attention` suffices at v1 scale.
- The `/aw` command-family redesign: separate follow-up (TODO/backlog), not this plan.
- Importing in-code `TODO`/`FIXME` comments: stays a `release-review` concern (D39).

## Scope check

- Over-scope: none - implements exactly the approved spec; no new attention class, no physical-model change, no manifest.
- Under-scope: the four attention touch-points, the verb family, the tree + contract, the `all`/`att` conveniences, the TODO migration, and tests are all included.

## Required tests / validation

- New unit tests per E-NEW Task group 5.
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- `aw attention --check` and `aw backlog check` clean on this repo after the migration.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- Implements `20260813-1833-01-attention-visible-backlog-tier.spec.md` (approved); on completion, advance that spec to `implemented` (with evidence) via `aw specs set`.
- Add a DECISIONS entry recording the three-tier model + backlog-as-attention-adopter (extends D125), per the spec Section 7.
- AGENTS.md pointer + `records/backlog/README.md` as in E-NEW Task group 4.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: All design questions (OQ1-OQ7) were resolved during the spec's /plan-review and human approval; this IPD carries no new open questions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: create a conformant item via `aw backlog new --apply`; show it validates; show the tree dirs + README exist; show a malformed item (missing frontmatter / bad enum / blocked-without-gate) is rejected by `aw backlog check` (RED), and a clean tree passes (GREEN).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: run `aw backlog new/set/check`; paste output showing create, a status transition with an appended history line, blocked-requires-gate rejection, status-mirrors-directory enforcement, and `check` exit 0 clean / nonzero on a planted malformed item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: unit test that `class_of("backlog", s)` maps open->ready, blocked->blocked, parked->parked, done->done and RAISES on an unknown status (falsifiable); `_classify_tree` maps a backlog file (both `.agents/backlog` and `.aw/records/backlog`) to the backlog policy.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: with fixture backlog items, `aw attention` shows open/blocked in the board and `/whatnext`; `parked` is absent from the board but present in `--format json`; `aw attention --check` clean. Mutation-probe: an item with an invalid status yields `attention.unknown-status` (fail closed), not a silent default.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: `aw att` (the new alias) produces byte-identical output to `aw attention` for the same args (incl. `--all`, `--format json`, `--check`); and confirm the EXISTING `aw attention --all` reveals a `parked` backlog item that the default `aw attention` board hides (no new `aw attention all` subcommand was added, since `--all` already exists). Paste both invocations.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: show each former committed TODO section is now backlog files at the correct status; `aw attention` surfaces the committed ones; `TODO.md` retains only Notes + a pointer; AGENTS.md + README updated. No committed item lost (diff/enumeration).
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste `pytest -n auto` (or `unittest discover`) summary green; `aw attention --check` and `aw backlog check` clean on the repo.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one coherent deliverable - a new records-class tree + its verbs + its attention integration + the migration that makes it useful - all implementing a single approved spec.

Execution requires the controlling spec `20260813-1833-01` at `Status: approved` (human), a GO `/plan-review` on this IPD, and human approval of this IPD. Scope fence: the files in Scope only - the backlog tree/contract, `backlog.py` + `aw backlog`, the attention contract/discovery touch-points, the `aw att` alias, the TODO.md migration + docs, and tests. Do not add a manifest, do not build the `/aw` redesign, do not change the physical model or other attention trees. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
