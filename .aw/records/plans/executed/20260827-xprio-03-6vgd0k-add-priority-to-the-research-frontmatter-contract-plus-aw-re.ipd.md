# IPD: Add Priority to the research frontmatter contract plus aw research new/set and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Research docs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional research FRONTMATTER key reusing the shared `{high,medium,low}` vocab, with `aw research new`/a set-priority path, `aw research index --check`/`aw check` validation, and `_research_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Research contract (`research_contract.py`): add an optional `priority:` frontmatter key. CRITICAL: do NOT add `priority` to `FRONTMATTER_FIELDS` (research_contract.py:365-377) - that tuple is the REQUIRED-presence set (checked at :400-402), so adding it there would mass-fail every existing doc. Optional means: no presence requirement, only a value check when present. Carry `priority` in `INDEX.json` (research_index build path). The enum value check itself is (3)/E-02. (2) Setter: allow `aw research new --priority` to emit it, and add a set path (extend an existing research set verb, e.g. `aw research set-priority` or a `--priority` on an existing mutator) to write/clear it on an existing doc, mirroring the `set-outcome` preview/`--apply` mutator (research_cmd.py:411/448). (3) Validation: add a per-key enum check `if "priority" in data: value in backlog.PRIORITIES` inside `validate_frontmatter` (research_contract.py, mirroring the `status`/`outcome` checks at :442-457); `aw research index --check` (which calls `validate_frontmatter`, research_index.py:93) and `aw check` then flag an out-of-vocab value. (4) Attention: populate `Item.priority` in `attention._research_record` (:371) from the doc's `priority:`. Absent = unprioritized. Research only; plans = child 01, specs = child 02.
- Scope-Paths: agent_workflows/research_contract.py, agent_workflows/research_cmd.py, agent_workflows/research_index.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: executed
- Set: xprio
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 6vgd0k

## Workflow history
- 2026-08-28 executed (aw oc run model=its_direct/pt3-claude-opus-4.8-1m-us): xprio-03 6vgd0k: Priority on research frontmatter (optional key + INDEX carry + enum + aw research new/set-priority + attention), committed 6b88087 [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: committed pre-begin (6b88087); in-scope-unmodified agent_workflows/backlog.py: import-only, not modified; in-scope-unmodified agent_workflows/check_engine.py: not needed; research enum lives in validate_frontmatter; in-scope-unmodified agent_workflows/cli.py: committed pre-begin (6b88087); in-scope-unmodified agent_workflows/research_cmd.py: committed pre-begin (6b88087); in-scope-unmodified agent_workflows/research_contract.py: committed pre-begin (6b88087); in-scope-unmodified agent_workflows/research_index.py: committed pre-begin (6b88087); in-scope-unmodified tests/: test committed pre-begin (6b88087)]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-304 fixed (do-not-add-to-FRONTMATTER_FIELDS mass-fail guard, E-01/E-02 validation ownership split, label-not-sort, OQ-01 resolved, V-01/V-02 evidence)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `priority` (shared low/medium/high vocab) to research frontmatter: contract recognition + INDEX carry, `aw research new --priority` + a set path, validation, and `_research_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract + INDEX + writers

- [x] E-01 In `research_contract.py`, support an optional `priority:` frontmatter key and carry it in the INDEX. Do NOT add `priority` to `FRONTMATTER_FIELDS` (that is the REQUIRED-presence tuple, :365-377/:400-402; adding it there mass-fails every existing doc) - "optional" means no presence check. Add reading/carrying of the key so `research_index` (build path) emits it as an `INDEX.json` field for a doc that has it. The enum VALUE validation is E-02 (a `validate_frontmatter` check), not this item.
  - Depends on: none
  - Expected outcome: a research doc may carry `priority: high`, `aw research index --check` conforms with or without it (optional), and a rebuilt INDEX.json carries the `priority` field for a doc that has it (absent/null otherwise).
  - Done note: `priority` is NOT added to `FRONTMATTER_FIELDS` (grep of the tuple -> 0 `priority`), so absence is clean. Added `priority: str = ""` to `research_index.DocEntry` (defaulted, carried into INDEX.json via `_asdict()`) and populated it in `_scan_docs` from `fm.get("priority","")`. Verified live: a doc with `priority: high` -> `aw research index --check: clean` (exit 0); INDEX.json carries `"priority": "high"`; a doc without it -> DocEntry.priority == "" and still conforms.
  - Execution state: performed
- [x] E-03 Add the writer surface: `--priority <low|medium|high>` on `aw research new` (research_cmd.py `plan_new`/`run_new` + cli.py), and a set/clear path that MIRRORS the existing in-place frontmatter mutator `aw research set-outcome` (research_cmd.py:373/449, IPD xjrdjp) - either a `--priority` on that mutator or a sibling `aw research set-priority <id6> --to <low|medium|high|->` - to write/clear `priority` on an existing doc.
  - Depends on: E-01
  - Expected outcome: `aw research new --priority high` emits `priority: high`; the set path writes `priority: medium` on an existing doc and `-`/clear removes it; both mirror `set-outcome`'s preview/`--apply` shape.
  - Done note: `build_frontmatter` gained an optional `priority` param that emits a `priority:` line ONLY when non-empty (so a doc created without it stays contract-clean); threaded through `plan_new`/`run_new` with a shared-vocab guard. Added a sibling `aw research set-priority <id6> --to <low|medium|high|->` (cli.py subparser + dispatch) backed by `plan_set_priority`/`run_set_priority`, mirroring `set-outcome`'s preview/`--apply` shape; the new `_set_priority_line` helper INSERTS the line when absent, REPLACES when present, and REMOVES on `-` (since priority is optional, unlike `update_frontmatter_fields` which only rewrites existing lines). Verified live: `aw research new . --kind findings --slug demo --priority high --apply` -> `priority: high` in the created doc; `aw research set-priority <id6> --to medium --apply` -> `priority: medium` (preview shows `would update`); `--to -` -> line removed.
  - Execution state: performed

### Task group 2: check + attention

- [x] E-02 Add the enum value check to `validate_frontmatter` (research_contract.py): `if "priority" in data` and the value not in shared `backlog.PRIORITIES` (import, do not fork), emit a structured error - mirroring the `status`/`outcome` value checks (:442-457). Because `aw research index --check` (research_index.py:93) and `aw check` call `validate_frontmatter`, both then flag an out-of-vocab value.
  - Depends on: E-01
  - Expected outcome: `aw research index --check`/`aw check` reports a finding for a doc carrying `priority: bogus` and reports none for `priority: high` or an absent priority.
  - Done note: Added `if "priority" in data:` -> value must be in the SHARED `_backlog.PRIORITIES` (imported, 0 forked literals) to `validate_frontmatter`, emitting `FrontmatterError("priority", "priority must be one of [...]")`; absent = no error (optional). Verified live: `aw research index --check` and `aw check research` both report `frontmatter-invalid: priority: priority must be one of ['high','low','medium']` for a bogus value; `priority: high`/absent -> no priority finding.
  - Execution state: performed
- [x] E-04 Populate `Item.priority` in `attention._research_record` (attention.py:371) from the doc's `priority:` key so the board labels a research doc's priority (absent = unset). Scope note: reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a research doc carrying `priority:`, matching backlog's label rendering; no label for an absent priority.
  - Done note: In `attention._research_record`, read `data.get("priority")` and pass `priority=pr` (None when absent/empty) to the existing `Item(...)`. My attention.py diff is ONLY this read + the `priority=pr` kwarg; the shared sort key is untouched. Verified live: `_research_record` yields `Item.priority == "high"` for a `priority: high` doc and `None` for an absent one.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab `backlog.PRIORITIES` (backlog.py:53) - reuse.
- Research frontmatter contract + STATUSES live in `research_contract.py`; `research_index` builds INDEX.json/md; `aw research new`/mutators are the tool-owned writers.
- `attention._research_record` (:371) builds the research Item; populate `priority` (Item.priority exists, :45).

## Findings

Same recognized-but-optional-field + setter + attention pattern; research-specific bits are the frontmatter contract, the INDEX carry, and `_research_record`. (Independent of the intake->todo rename set rstodo, though both touch research_contract - executor should rebase if both land.)

## Proposed changes (ordered, validatable)

1. `research_contract.py`: support optional `priority` key (NOT added to the required `FRONTMATTER_FIELDS`); enum value check is item 4 in `validate_frontmatter`.
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
- `aw attention` LABELS a research doc by its priority (`[high]`/`[medium]`/`[low]` bracket via the existing renderer, attention.py:717); the shared sort key (attention.py:186) is unchanged (E-04 scope note).

## Spec / documentation sync

- Document `priority` in the research frontmatter docs + `aw research --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the orchestrator's OQ-01 (absent = unprioritized, no `[priority]` label, no priority sort introduced). This child follows: `_research_record` passes `Item.priority` (None when absent) to the existing renderer and does not alter the sort key.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted `aw research index --check` on a fixture doc carrying `priority: high` showing conformance, and on a doc with NO priority also conforming (optional). Pasted rebuilt `INDEX.json` excerpt showing the `priority` field present for the doc that has it (and absent/null for one that does not). A grep proving `priority` is NOT added to `FRONTMATTER_FIELDS` (research_contract.py) - i.e. an existing doc with no `priority` still validates clean.
  - Observed evidence: INDEX CHECK (live) - a doc with `priority: high` -> `aw research index --check` -> `index --check: clean` (exit 0); a doc with no priority also conforms. INDEX.json - `python3 -c 'json.load(INDEX.json)[0]["priority"]'` -> `high` for the doc that has it; a doc without priority carries `DocEntry.priority == ""`. GREP - `sed -n '/^FRONTMATTER_FIELDS/,/)/p' research_contract.py | grep -c priority` = `0` (priority NOT in the required tuple). TESTS - `python3 -m pytest tests/test_research_priority.py -o addopts=""` -> `11 passed`: `ResearchPriorityContractTests::test_priority_not_in_required_fields`, `::test_absent_priority_conforms`; `ResearchPriorityIndexTests::test_index_carries_priority` (INDEX.json contains `"priority": "high"`), `::test_index_priority_empty_when_absent`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted `aw research index --check` (and `aw check`) over a fixture doc carrying `priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `priority: high` and no priority showing NO such finding. A grep proving the `validate_frontmatter` enum check consumes the shared `backlog.PRIORITIES` (no forked `{"high","medium","low"}` literal). Pasted new/updated test in tests/ asserting all three cases.
  - Observed evidence: CHECK (live) - a `priority: bogus` doc -> `aw research index --check` -> `frontmatter-invalid: priority: priority must be one of ['high', 'low', 'medium']`; `aw check research` -> `Issue: priority: priority must be one of ['high','low','medium']`; `priority: high` and absent -> 0 priority findings. GREP - `grep -n _backlog.PRIORITIES research_contract.py` -> the check at :499/:503 uses `_backlog.PRIORITIES` (imported; no forked literal). TESTS - part of the `11 passed` run: `ResearchPriorityContractTests::test_out_of_vocab_priority_flagged` (exactly 1 priority error), `test_valid_priority_conforms` (every backlog.PRIORITIES member clean), `test_absent_priority_conforms`. Regression: `tests/test_research_contract.py tests/test_research_index.py tests/test_check_engine.py` green (part of `105 passed`).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted `aw research new --priority high ... --apply` run and the created doc's `priority: high` frontmatter line. Pasted set-path run (preview then `--apply`) writing `priority: medium` on an existing doc, and the clear (`-`) run removing the key; confirm the surface mirrors `set-outcome`'s preview/`--apply` shape.
  - Observed evidence: NEW (live) - `aw research new . --kind findings --slug demo --summary s --priority high --apply` -> `wrote .../20260828-demo-00-4sh13t-demo.findings.md`; the created doc carries `priority: high`. SET (live) - `aw research set-priority 4sh13t --to medium` (preview) -> `--- would update ...: priority=medium ---`; with `--apply` -> `updated ...` and the doc shows `priority: medium`; `aw research set-priority 4sh13t --to - --apply` -> `updated ...` and 0 `priority:` lines (cleared). Both mirror `set-outcome`'s preview/`--apply` shape. TESTS - part of the `11 passed` run: `ResearchPriorityNewAndSetTests::test_new_emits_priority_line_only_when_given` (line present only with --priority), `::test_new_rejects_out_of_vocab_priority`, `::test_set_priority_writes_inserts_and_clears` (insert/replace/remove, body preserved), `::test_plan_set_priority_rejects_out_of_vocab`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture research doc carrying `priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a doc with no priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence: ATTENTION (live) - `attention._research_record` for a `priority: high` doc yields `Item.priority == "high"`; for a doc with no priority yields `None` (the serializer renders `"priority": "high"` / `"priority": null`, identical to the plans/specs paths proven in 1b45el/rp859c). DIFF - `git diff HEAD -- agent_workflows/attention.py` shows ONLY the `_research_record` change (the `pr_val`/`pr` read + the `priority=pr` kwarg on the existing `Item(...)`); the shared sort key is NOT in the diff (unchanged). TESTS - part of the `11 passed` run: `ResearchPriorityAttentionTests::test_research_record_populates_priority` (`Item.priority == "high"` for a priority doc, `None` when absent). Regression: `tests/test_attention.py` green.
  - Result: pass



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`research_contract.py`, `research_cmd.py`, `research_index.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch the plans/specs contracts (children 01/02) or the shared attention sort key. If the intake->todo rename Set `rstodo` (which also touches `research_contract.py`) has landed, rebase onto it before executing. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.
