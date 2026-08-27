# IPD: Add Priority to the research frontmatter contract plus aw research new/set and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Research docs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional research FRONTMATTER key reusing the shared `{high,medium,low}` vocab, with `aw research new`/a set-priority path, `aw research index --check`/`aw check` validation, and `_research_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Research contract (`research_contract.py`): recognize an optional `priority:` frontmatter key validated against shared `backlog.PRIORITIES` (import, do not fork); optional so existing docs are not mass-failed; carry it in `INDEX.json`. (2) Setter: allow `aw research new --priority` to emit it, and add a set path (extend an existing research set verb, e.g. `aw research set-priority` or a `--priority` on an existing mutator) to write/clear it on an existing doc. (3) Validation: `aw research index --check`/`aw check` flag an out-of-vocab value. (4) Attention: populate `Item.priority` in `attention._research_record` (:371) from the doc's `priority:`. Absent = unprioritized. Research only; plans = child 01, specs = child 02.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: draft
- Set: xprio
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 6vgd0k

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `priority` (shared low/medium/high vocab) to research frontmatter: contract recognition + INDEX carry, `aw research new --priority` + a set path, validation, and `_research_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract + INDEX + writers

- [ ] E-01 In `research_contract.py`, recognize an optional `priority:` frontmatter key (`validate_frontmatter` ignores unknown keys today, so add explicit per-key acceptance) validated against shared `backlog.PRIORITIES` (import, do not fork); optional (existing docs stay valid). Carry it as an INDEX.json field in `research_index` (build path).
  - Depends on: none
  - Expected outcome: a research doc may carry `priority: high`, `aw research index --check` conforms with or without it, and a rebuilt INDEX.json carries the `priority` field for a doc that has it.
  - Execution state: pending
- [ ] E-03 Add the writer surface: `--priority <low|medium|high>` on `aw research new` (research_cmd.py `plan_new`/`run_new` + cli.py), and a set/clear path that MIRRORS the existing in-place frontmatter mutator `aw research set-outcome` (research_cmd.py:373/449, IPD xjrdjp) - either a `--priority` on that mutator or a sibling `aw research set-priority <id6> --to <low|medium|high|->` - to write/clear `priority` on an existing doc.
  - Depends on: E-01
  - Expected outcome: `aw research new --priority high` emits `priority: high`; the set path writes `priority: medium` on an existing doc and `-`/clear removes it; both mirror `set-outcome`'s preview/`--apply` shape.
  - Execution state: pending

### Task group 2: check + attention

- [ ] E-02 Flag an out-of-vocab `priority` value in `aw research index --check`/`aw check` (validated against shared `backlog.PRIORITIES`).
  - Depends on: E-01
  - Expected outcome: `aw research index --check`/`aw check` reports a finding for a doc carrying `priority: bogus` and reports none for `priority: high` or an absent priority.
  - Execution state: pending
- [ ] E-04 Populate `Item.priority` in `attention._research_record` (attention.py:371) from the doc's `priority:` key so the board labels a research doc's priority (absent = unset). Scope note: reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a research doc carrying `priority:`, matching backlog's label rendering; no label for an absent priority.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab `backlog.PRIORITIES` (backlog.py:53) - reuse.
- Research frontmatter contract + STATUSES live in `research_contract.py`; `research_index` builds INDEX.json/md; `aw research new`/mutators are the tool-owned writers.
- `attention._research_record` (:371) builds the research Item; populate `priority` (Item.priority exists, :45).

## Findings

Same recognized-but-optional-field + setter + attention pattern; research-specific bits are the frontmatter contract, the INDEX carry, and `_research_record`. (Independent of the intake->todo rename set rstodo, though both touch research_contract - executor should rebase if both land.)

## Proposed changes (ordered, validatable)

1. `research_contract.py`: recognize optional `priority` (shared vocab).
2. `research_index.py`: carry `priority` in INDEX.
3. `research_cmd.py`+`cli.py`: `aw research new --priority` + set path.
4. `check_engine.py`/index --check: enum validation.
5. `attention.py`: populate `Item.priority` in `_research_record`.
6. `tests/`: index-check-clean with/without priority; create/set; invalid flagged; board shows research priority.

## Deferred / out of scope (with reason)

- Plans Priority: child 01. Specs Priority: child 02.

## Scope check

- Over-scope: none.
- Under-scope: none (research field+INDEX+setter+check+attention complete).

## Required tests / validation

- A research doc with `priority: high` passes `aw research index --check`; without it also passes (optional).
- Creation `--priority` and the set path write/clear it.
- `aw check`/`index --check` flag an out-of-vocab value.
- `aw attention` sorts/labels a research doc by priority.

## Spec / documentation sync

- Document `priority` in the research frontmatter docs + `aw research --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Handled at the orchestrator (OQ-01).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Pasted `aw research index --check` on a fixture doc carrying `priority: high` showing conformance, and on a doc with NO priority also conforming (optional). Pasted rebuilt `INDEX.json` excerpt showing the `priority` field present for the doc that has it (and absent/null for one that does not). A grep proving `research_contract` imports `backlog.PRIORITIES` (no forked vocab literal).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Pasted `aw research index --check` (and `aw check`) over a fixture doc carrying `priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `priority: high` and no priority showing NO such finding. Pasted new/updated test in tests/ asserting all three cases.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Pasted `aw research new --priority high ... --apply` run and the created doc's `priority: high` frontmatter line. Pasted set-path run (preview then `--apply`) writing `priority: medium` on an existing doc, and the clear (`-`) run removing the key; confirm the surface mirrors `set-outcome`'s preview/`--apply` shape.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture research doc carrying `priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a doc with no priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`research_contract.py`, `research_cmd.py`, `research_index.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch the plans/specs contracts (children 01/02) or the shared attention sort key. If the intake->todo rename Set `rstodo` (which also touches `research_contract.py`) has landed, rebase onto it before executing. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.
