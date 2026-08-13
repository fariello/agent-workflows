# IPD: Attention-visible backlog tier (records/backlog + aw backlog)

- Date: 2026-08-13
- Kind: child
- Concern: `aw attention` (which feeds `/whatnext`) scans only plans/specs/research/actions, so committed work captured in the free-prose `TODO.md` is silently omitted - a false-comprehensiveness risk. Implement a lightweight, tracked, attention-visible backlog tier so committed work surfaces while uncommitted maybes stay quiet.
- Scope: `agent_workflows/attention_contract.py` (`TREE_POLICY` + `CLASS_MAPS`/`_BACKLOG_MAP`), `agent_workflows/artifact_core.py` (`SCAN_ROOTS`), `agent_workflows/attention.py` (scan/`_classify_tree`/`_record_for` + a `_backlog_record` builder + the `all` reveal), a new `agent_workflows/backlog.py` (the `aw backlog new|set|check` verbs), `agent_workflows/cli.py` (wire `aw backlog`, `aw attention all`, and the `aw att` alias), the new `records/backlog/` tree scaffold + `README.md`, the `TODO.md` migration, docs (AGENTS.md pointer), and tests. Implements the approved spec `.agents/docs/specs/20260813-1833-01-attention-visible-backlog-tier.spec.md`.
- Status: draft
- Highest E allocated: 08
- Author: opencode Opus 4.8
- Id: crv40v
- Set: backlogtier (attention-visible backlog tier)
- Order: 1
## Workflow history

- 2026-08-13 draft (opencode Opus 4.8): authored from the approved spec 20260813-1833-01 (attention-visible backlog tier). Implements the records-class backlog/ sub-tree, the four attention touch-points, the aw backlog verbs, aw attention all + aw att alias, and the TODO.md migration, per the spec's resolved OQ1-OQ7.

## Goal

Add a `records`-class `backlog/{open,blocked,parked,done}/` tree of lightweight frontmatter+prose items, an `aw backlog new|set|check` verb family to manage them, and the four `aw attention` integration touch-points so committed (`open`) items surface as `ready` and gated (`blocked`) items as `blocked` in `aw attention` + `/whatnext`, while uncommitted `parked` maybes are tracked-but-quiet (JSON-only, revealed by `aw attention all`). Migrate the existing `TODO.md` committed sections into the tree so nothing committed is invisible.

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

- [ ] E-05 Make `aw attention` discover + record backlog items: add the backlog root(s) (`.agents/backlog` and `.aw/records/backlog`) to `SCAN_ROOTS` in `artifact_core.py`, and add a `backlog` branch in `attention.py` `_record_for` + a `_backlog_record` builder (reading frontmatter `status`/`priority`/`summary`/`id`, mirroring `_plans_record`/`_research_record`) with `scan()` routing backlog files to it. `open`/`blocked` items appear in the human hot glance (as `ready`/`blocked`) and in `--format json`; `parked` items are in JSON but EXCLUDED from the hot glance (like `archive` research); `priority` orders the `ready` list (high first).
  - Depends on: E-02
  - Expected outcome: `aw attention` includes backlog items with correct classes; `open` shows in the board + `/whatnext`; `parked` is JSON-only, out of the default board; `aw attention --check` stays clean with backlog items present.
  - Execution state: pending

- [ ] E-06 Add the attention CLI conveniences (spec OQ2): `aw attention all` (reveals `parked`/archived-tier items the default board hides) and an `aw att` alias for `aw attention`, both small `cli.py` edits.
  - Depends on: E-02
  - Expected outcome: `aw attention all` lists parked backlog items that `aw attention` hides; `aw att` behaves identically to `aw attention`.
  - Execution state: pending

### Task group 4: Migrate TODO.md + docs

- [ ] E-07 Migrate `TODO.md` into the backlog tree per spec OQ1: "Known bugs to fix" + "Security follow-ups" + "Planned next (designed, deferred)" -> `open/` (or `blocked/` for an item that names a gate); "Consider and possibly implement (may be declined)" -> `parked/`; "Notes" stays prose. Reduce `TODO.md` to a pointer at the backlog tree + the retained Notes section (do not silently drop any committed item). Add the AGENTS.md pointer that committed backlog lives in the records backlog tree (surfaced by `aw attention`) and `TODO.md` holds only uncommitted notes; add the `records/backlog/README.md`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: every previously-committed TODO item is a backlog file at the right status; `aw attention` shows the committed ones; `TODO.md` no longer holds committed work; docs point at the tree.
  - Execution state: pending

### Task group 5: Tests

- [ ] E-08 Add tests: (a) `_BACKLOG_MAP` purity/totality + `class_of("backlog", ...)` incl. unknown-status raising; (b) attention inclusion - `open`/`blocked` in the board, `parked` JSON-only/out-of-glance, `aw attention all` reveals parked, `aw att` alias; (c) `aw backlog new/set/check` incl. blocked-requires-gate, status-mirrors-directory, and fail-closed `check` cases; (d) a post-migration assertion that a representative migrated item surfaces in `aw attention`. Full suite green (`pytest -n auto` / `unittest discover`).
  - Depends on: E-02, E-03, E-04, E-05, E-07
  - Expected outcome: new tests pass; full suite green; `aw attention --check` + `aw backlog check` clean on the repo after migration.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `aw attention` discovery is NOT generic (spec PR-001): a new tree needs a `TreePolicy` (`attention_contract.TREE_POLICY`), a `SCAN_ROOTS` entry (`artifact_core.py`), and a `_record_for` branch (`attention.py`) - not just a `CLASS_MAPS` line.
- `records`-class trees are dual-path: `.agents/<x>` pre-migration, `.aw/records/<x>` post-migration; `attention._classify_tree` normalizes `.aw/records/` -> `.agents/`, and `SCAN_ROOTS` lists BOTH (as plans does).
- The `actions` tree uses a bespoke scan path; backlog should instead use the standard `iter_scan_files` + `_classify_tree` + `_record_for` path (it is a `records` tree like plans, not `state`).
- Status-mirrors-directory + append-only workflow history + machine-readable bare-enum status are the shipped conventions (D52, D125) to reuse; the leak sanitizer + zero-runtime-deps + Python 3.9 constraints apply.

## Findings

- The gap and design are fully specified and reviewed in `20260813-1833-01-attention-visible-backlog-tier.spec.md` (approved). This IPD implements it; OQ1-OQ7 are all resolved there (records location; open|blocked|parked|done + typed gate; priority high|medium|low + Set from v1; no v1 manifest; promotion = done+plan-cite; parked JSON-only + `aw attention all` + `aw att`).

## Proposed changes (ordered, validatable)

1. Backlog item contract + `records/backlog/` tree scaffold.
2. `agent_workflows/backlog.py` + `aw backlog new|set|check` CLI.
3. Attention contract: `_BACKLOG_MAP` + `TreePolicy`.
4. Attention discovery/record: `SCAN_ROOTS` + `_backlog_record` + `scan` routing; parked hot-glance exclusion.
5. `aw attention all` + `aw att` alias.
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
  - Required evidence: `aw attention all` lists a parked item that `aw attention` hides; `aw att` output equals `aw attention` output.
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

Execution requires the controlling spec `20260813-1833-01` at `Status: approved` (human), a GO `/plan-review` on this IPD, and human approval of this IPD. Scope fence: the files in Scope only - the backlog tree/contract, `backlog.py` + `aw backlog`, the attention contract/discovery touch-points, `aw attention all` + `aw att`, the TODO.md migration + docs, and tests. Do not add a manifest, do not build the `/aw` redesign, do not change the physical model or other attention trees. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
