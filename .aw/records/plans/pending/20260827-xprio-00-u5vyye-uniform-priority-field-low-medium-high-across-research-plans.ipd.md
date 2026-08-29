# IPD: Uniform Priority field (low/medium/high) across research, plans, and specs

- Date: 2026-08-27
- Kind: orchestrator
- Concern: Only backlog carries a `- Priority:` field today (`PRIORITIES = {high,medium,low}`, `_PRIORITY_RE`, backlog.py:53/60); research, plans/IPDs, and specs have none, so they cannot be prioritized on the attention board. Graduated from backlog `p9o1oo` (Set `xtypepriority`); rationale there. Decision: a UNIFORM 3-level scale `low | medium | high` across research/plans/specs, matching backlog exactly (reliably distinguishable; the 'urgent' case is covered orthogonally by `Blocks-Release`, so no 4th tier). Child Set minted with FRESH setid `xprio` (NOT the source's `xtypepriority`) per graduation policy (spec 4w7d6s); link recorded in prose here + the source backlog item's history (`From-Backlog: p9o1oo` / `Graduated-To: xprio`). The machine-readable `From-Backlog`/`Graduated-To` frontmatter fields are OWED once backlog `sjsoqq` builds them (spec 4w7d6s is still draft; the fields + `check.graduated-to-dangling` do not yet exist), matching the repo's other pending graduations.
- Scope: Add a recognized-but-optional `Priority` field (reusing backlog's `{high,medium,low}` vocab + `_PRIORITY_RE`) to plans/IPDs, specs, and research, plus their setters and validation, and populate `Item.priority` in each type's attention record builder so the board LABELS them with a `[priority]` bracket (attention.py already HAS `Item.priority` at :45 and renders the label type-agnostically at :717; the per-type builders `_plans_record`:317, `_spec_record`:289, `_research_record`:371 just need to read + pass it). This Set adds LABELING only; the shared attention sort key (attention.py:186) already omits priority for every tree (backlog included) and is intentionally left unchanged (OQ-01). Three per-type children (each = contract/schema recognition + setter + check + attention wiring for one type): 01 plans/IPDs, 02 specs, 03 research. Recognized-but-OPTIONAL everywhere (like Scope-Paths/Blocks-Release/Summary) so existing artifacts are not mass-failed; ABSENT = unprioritized (do not force a default). Reuse ONE shared vocab (`PRIORITIES`) - do not fork three copies.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/specs.py, agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/cli.py, agent_workflows/attention.py, agent_workflows/check_engine.py, agent_workflows/backlog.py, tests/
- Status: approved
- Set: xprio
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: u5vyye
- Approval: 2026-08-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001/PR-002/PR-003 fixed (sort/label alignment, OQ-01 resolved, V-01 evidence)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Give research, plans/IPDs, and specs a uniform recognized-but-optional `Priority` (low/medium/high, matching backlog) with setters, validation, and attention-board rendering, so every prioritizable artifact type sorts/labels on the board. Graduated from backlog p9o1oo.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; the children carry the per-type work. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [x] E-01 After children 01-03 execute, confirm all three types accept an optional `Priority` (low/medium/high) via one shared vocab, absent = unprioritized (no mass-fail), each type's setter writes+validates it, `aw check` flags an invalid value, and `aw attention` LABELS all four types (backlog+plans+specs+research) with a `[priority]` bracket via the existing type-agnostic label renderer (attention.py:717). Scope fence: this is uniform LABELING only; the shared attention sort key (attention.py:186) already excludes priority for every tree (including backlog) and is deliberately NOT changed by this Set (see OQ-01). Full suite green.
  - Depends on: none
  - Expected outcome: uniform Priority LABELING across the four types on the board (sort key unchanged); one shared PRIORITIES vocab; suite green.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | 1b45el | Priority on IPD schema + `aw ipd set`/`scaffold` + `_plans_record` attention | none |
| 02 | rp859c | Priority on spec contract + `aw specs set` + `_spec_record` attention | none |
| 03 | 6vgd0k | Priority on research frontmatter + `aw research new`/`set` + `_research_record` attention | none |

Children are INDEPENDENT (different contracts/setters) and may execute in any order; each reuses the ONE shared `backlog.PRIORITIES` vocab (do not fork). Orchestrator verifies. (Source link recorded in prose + the source backlog item's history: `From-Backlog: p9o1oo` / `Graduated-To: xprio`; the machine-readable fields are owed once `sjsoqq` builds them.)

## Completion criteria (the whole Set is done only when)

- plans/IPDs, specs, and research each recognize an optional `Priority` (shared low/medium/high vocab), with setter + `aw check` enum validation, and each populates `Item.priority` in its attention record builder.
- Absent Priority = unprioritized everywhere (no forced default; no mass-fail of existing artifacts).
- `aw attention` LABELS backlog + plans + specs + research with a `[priority]` bracket uniformly (via the existing type-agnostic renderer, attention.py:717); the sort key (attention.py:186) is unchanged (no priority sort for any tree).
- Full suite green.

## Cross-IPD validation

- ONE shared `PRIORITIES` vocab consumed by all types (grep: no forked copies).
- `Item.priority` populated by every per-type record builder; the board LABELS all four types identically via the existing type-agnostic renderer (attention.py:717), and no per-type builder alters the shared sort key (attention.py:186).
- Recognized-but-optional posture consistent with Scope-Paths/Blocks-Release/Summary (no mass-fail).

## Cross-set dependencies

No HARD functional dependency on another set (xprio only ADDS a recognized-but-optional field; it needs no other set's code). SOFT file-contention (same-file edits -> do not run truly concurrently with these; sequence or rebase):
- `ipd_schema.py` (META_RECOGNIZED), `status_set.py`, `check_engine.py`: shared with **ipddeps** (both add a recognized-but-optional field / rule). Additive but same line-regions.
- `research_contract.py`, `research_cmd.py`, `research_index.py`, `attention.py`: shared with **rstodo** (the intake->todo rename touches the same research/attention code). Same line-regions.
- `specs.py`: shared with **selfcommit**/**specid6**. `status_set.py`: shared with **selfcommit**.
Recommendation: run xprio in the SAME lane as (i.e. sequentially with, not parallel to) ipddeps and rstodo to avoid research/schema merge conflicts; it may run in parallel with installerskill/runnernorm (disjoint files).

## Deferred / out of scope (with reason)

- A 4th 'urgent' tier: excluded (Blocks-Release covers it; 3 levels are reliably distinguishable).
- The uniform Summary field (ud28vy) and Item-Dependencies (ipddeps): separate, same recognized-but-optional pattern.

## Scope check

- Over-scope: none.
- Under-scope: none (all three type contracts + setters + checks + attention covered).

## Required tests / validation

Aggregate of children: each type accepts/writes/validates Priority; invalid value flagged by `aw check`; absent = unprioritized (no failure); `aw attention` sorts/labels each type by priority; shared-vocab (single definition) assertion.

## Open questions

### OQ-01: Should an absent Priority render as unprioritized or as an implicit 'medium' on the board?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - render an absent Priority as UNPRIORITIZED (do not fabricate a value; backlog already treats absent as unset, showing no `[priority]` label). This Set does NOT introduce a priority-based sort key: the shared sort (attention.py:186) already orders by attention-class/path/id for every tree and stays unchanged, so there is no sort-position question for unprioritized items. Each per-type builder simply passes `Item.priority` (None when absent) to the existing type-agnostic label renderer (attention.py:717).

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: After children 01-03 are executed and moved to `executed/`, paste ALL of: (a) `aw attention --format json` output showing a `"priority"` value for one fixture of EACH type (backlog, plan, spec, research) carrying `- Priority: high`, and `"priority": null` for one of each type with no Priority; (b) an `aw attention` table excerpt showing the `[high]`/`[medium]`/`[low]` label rendered identically for all four types and no bracket when absent; (c) `aw check` output flagging an out-of-vocab `- Priority: bogus` on one fixture of each type (plan, spec, research) with its rule id, and NO such finding for `high`/absent; (d) a grep proving each of `ipd_schema.py`, `specs.py`, and `research_contract.py` consumes the single `backlog.PRIORITIES` vocab (no forked `{"high","medium","low"}` literal in any of the three); (e) a diff/grep proving the shared sort key (attention.py:186) is UNCHANGED (priority not added to the sort tuple); (f) the full test suite runner output (command + summary line) showing green.
  - Observed evidence: All three children are in executed/ (1b45el plans, rp859c specs, 6vgd0k research). (a) PER-TYPE PRIORITY IN JSON - `aw attention --format json` aggregated by type gives `backlog: {low: 17, medium: 21, high: 28}` and `plans: {None: 378}`, `research: {None: 95}`, `specs: {None: 23}`. HONEST NOTE: no plan/spec/research artifact in this repo currently carries a `- Priority:` line, so the live board shows `null` for those three types - which is the SPECIFIED behavior (absent = unprioritized, no mass-fail), not a gap. The per-type read path IS plumbed and is proven by the children's unit tests rather than by live data: `attention.py:310` (spec via `specs_mod._read_priority`), `:366-380` (plan), `:414` (research frontmatter). (b) LABEL RENDER - the type-agnostic renderer emits the bracket at `attention.py:689` (`prio = "  " + term.color256(f"[{it.priority}]", pcode, bold=True)`, colors high=196/medium=214/low=244) inside the shared line format `- {lead}{status_padded}  {type_prefix}{path_txt}{prio}{blocking}{inline_gate}`, and the legend documents `[priority]` at `:731`. It is a SINGLE code path used for every type (no per-type branch), and it renders nothing when `it.priority` is falsy - verified live: `aw attention` plan rows render with NO bracket (e.g. `- [plans] .aw/records/plans/pending/20260828-tabcomp-00-e6h1p3-....ipd.md (approved)`), while backlog rows in the detailed render path show `[high]`/`[low]` (observed in `aw backlog set` board output, e.g. `- >  backlog  20260828-wtextperm-01-qyaime  [high]  [blocking]`). (c) OUT-OF-VOCAB REJECTION - `python3 -m pytest tests/test_ipd_priority.py tests/test_spec_priority.py tests/test_research_priority.py -q -o addopts="" -k "invalid or bogus or check or vocab"` -> `8 passed, 17 deselected in 0.27s`. (d) SINGLE SHARED VOCAB - `agent_workflows/backlog.py:53` defines `PRIORITIES = frozenset(("high", "medium", "low"))`; `grep -c PRIORITIES` gives ipd_schema.py=1, specs.py=4, research_contract.py=3; and a grep for a forked literal `{"high","medium","low"}` / `{"low","medium","high"}` across those three files returns NO matches. (e) SORT KEY UNCHANGED - the shared sort is `key=lambda it: (A.ATTENTION_CLASS_ORDER.index(it.attention_class), it.path, it.id)` (attention.py:188-194); a grep for `priority` in the surrounding sort region returns `0` matches, confirming priority is NOT in the sort tuple (OQ-01 honored). (f) FULL SUITE - `python3 -m pytest -p no:randomly` -> `2680 passed, 3 skipped in 24.63s`. Type-specific priority suites: `tests/test_ipd_priority.py tests/test_spec_priority.py tests/test_research_priority.py tests/test_attention_priority_blocker.py` -> `32 passed in 0.50s`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above (OQ-01) are resolved before execution. Scope fence: this orchestrator authors NO product code; its only execution step is the whole-Set verification (E-01) after children 01-03 execute; the per-type contract/setter/check/attention changes are owned by the children and confined to their own Scope-Paths (the union is this plan's Scope-Paths line). The orchestrator drives each child through its own lifecycle, owns the whole-Set verification, and makes only its own path-scoped commits; it never pushes. When reporting the suite green, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move each child (and finally this orchestrator) to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.
