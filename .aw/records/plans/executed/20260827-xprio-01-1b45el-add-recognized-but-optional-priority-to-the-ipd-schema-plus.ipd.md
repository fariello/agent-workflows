# IPD: Add recognized-but-optional Priority to the IPD schema plus aw ipd set/scaffold and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Plans/IPDs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional IPD metadata field reusing the shared `{high,medium,low}` vocab, with the `aw ipd set` setter, scaffold emission (optional), `aw check` validation, and `_plans_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Schema: add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (NOT `META_REQUIRED`; recognized-but-optional like Scope-Paths/Blocks-Release). Schema-layer recognition ONLY suppresses the IPD-M103 "unknown field" lint error; per the documented convention (ipd_schema.py:161-162,168-170), value/enum validation does NOT live in `validate_metadata` but in the `aw check` surface (see (3)). Define `META_PRIORITY` referencing the shared `backlog.PRIORITIES = {high,medium,low}` in prose only; do not fork the vocab. (2) Setter: add `--priority <low|medium|high>` to `aw ipd set` in cli.py + status_set.py using the hoisted status-branch-independent write (mirrors `--blocks-release`/`--from-backlog`, status_set.py:544-562) so it persists on a no-op transition; `-`/empty clears. (3) `aw check`: validate the enum here (flag an out-of-vocab Priority on a plan against the shared `backlog.PRIORITIES`; import the one vocab, do not fork). (4) Attention: populate `Item.priority` in `attention._plans_record` (:317) from the plan's `- Priority:` (attention.py already renders `Item.priority`, :45/:435/:717). Absent = unprioritized. This child covers PLANS only; specs = child 02, research = child 03.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: executed
- Set: xprio
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 1b45el

## Workflow history
- 2026-08-28 executed (aw oc run model=its_direct/pt3-claude-opus-4.8-1m-us): xprio-01 1b45el: recognized-but-optional Priority on IPDs (schema recognize + aw ipd set --priority + aw check enum + attention render); E-01 from salvage bfe4bf1, E-02/E-03 added a7bfe03 [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: committed pre-begin (E-03 in a7bfe03); in-scope-unmodified agent_workflows/backlog.py: import-only, not modified; in-scope-unmodified agent_workflows/check_engine.py: committed pre-begin (E-02 in a7bfe03); in-scope-unmodified agent_workflows/cli.py: committed pre-begin (E-01 in salvage bfe4bf1); in-scope-unmodified agent_workflows/ipd_schema.py: committed pre-begin (E-01 in salvage bfe4bf1); in-scope-unmodified agent_workflows/status_set.py: committed pre-begin (E-01 in salvage bfe4bf1); in-scope-unmodified tests/: test committed pre-begin (a7bfe03)]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-104 fixed (schema recognizes-not-validates, enum-check precedent corrected, label-not-sort, OQ-01 resolved, V-01/V-02 evidence realigned)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `Priority` (shared low/medium/high vocab) to IPDs: schema recognition, `aw ipd set --priority`, `aw check` enum validation, and `_plans_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: schema + setter

- [x] E-01 Add `META_PRIORITY = "Priority"` to `ipd_schema.META_RECOGNIZED` (not META_REQUIRED) so it RECOGNIZES the field (suppresses IPD-M103 unknown-field); do NOT add value/enum validation to `validate_metadata` (per convention that lives in `aw check`, E-02). Add `--priority <low|medium|high|->` to `aw ipd set` (cli.py + status_set.py) via the hoisted status-branch-independent write (mirroring the `--blocks-release`/`--from-backlog` primitives at status_set.py:544-562); optionally emit it from scaffold.
  - Depends on: none
  - Expected outcome: an IPD may carry `- Priority: high` and lints clean (schema recognizes it); `aw ipd set <plan> --priority medium` writes it (persists on no-op), `--priority -` clears.
  - Done note (already committed in the interrupted-run salvage commit bfe4bf1, verified this turn): `ipd_schema.META_PRIORITY = "Priority"` is in `META_RECOGNIZED` (NOT `META_REQUIRED`) with no `validate_metadata` enum check (ipd_schema.py:196,209). `aw ipd set --priority <low|medium|high|->` exists (cli.py:1003 with `choices=["low","medium","high","-"]`) and writes via the hoisted status-branch-independent primitive `releases.set_priority_line` (status_set.py:647-658), so it persists on a same-status no-op and `-` clears. Verified live: set medium -> persists on a no-op re-run -> `--priority -` clears; a `- Priority: high` plan lints `conforming`. Scaffold emission left as the optional (not required) part; not added. NO further code change was needed for E-01 this turn (reconciled real state).
  - Execution state: performed

### Task group 2: check + attention

- [x] E-02 Validate the Priority enum in `aw check` (flag an out-of-vocab `- Priority:` value on a plan against the shared `backlog.PRIORITIES`). This is an ENUM check on a plan's own metadata (the true precedent is backlog's own priority enum guard, backlog.py:162, `item.priority not in PRIORITIES`), NOT a dangling/reference-resolution check like `check_blocks_release`/`check_from_backlog` (which resolve a target across trees, check_engine.py:604-607). Wire the new check into the plan-metadata pass of `aw check` (check_engine.py) reusing the shared `backlog.PRIORITIES` vocab.
  - Depends on: E-01
  - Expected outcome: `aw check` reports a finding for a plan carrying `- Priority: bogus` and reports none for `- Priority: high` or an absent Priority.
  - Done note: Added `check_plan_priority(repo_root, include_untracked)` to check_engine.py (near check_ipd_dependencies) that reads each plan's `- Priority:` via `_ITEM_PRIORITY_RE`, skips when absent (optional), and flags `check.priority-invalid` when the value is not in the SHARED `backlog.PRIORITIES` (imported, no forked literal - 0 `"high"` literals in the function). Registered `check.priority-invalid` in `RULE_REGISTRY` (error/repository/deterministic). Wired into the plans-type content path (check_content, right after check_ipd_dependencies) so BOTH `aw check plans` and `aw check all` surface it exactly once. Verified live: `- Priority: bogus` -> `Issue: priority not in ['high','low','medium']: 'bogus'` (exit 1); `- Priority: high` and absent -> 0 priority findings.
  - Execution state: performed
- [x] E-03 Populate `Item.priority` in `attention._plans_record` (attention.py:317) from the plan's `- Priority:` line so the board labels a plan's priority (absent = unset). Scope note: this reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a plan carrying `- Priority:`, matching backlog's label rendering; no label for an absent Priority.
  - Done note: In `attention._plans_record`, parse `- Priority:` (`re.search(r"(?m)^- Priority:[ \t]*(\S+)[ \t]*$", text)`) and pass `priority=pr` (None when absent) to the existing `Item(...)` constructor, exactly mirroring the `blocks_release=` populate already there. The shared sort key is UNTOUCHED (my attention.py diff is only the parse + the `priority=pr` kwarg). Verified live: `aw attention --format json` shows `"priority": "high"` for a `- Priority: high` plan and `"priority": null` for a plan with no Priority; `aw ipd lint`'s board renders the `[high]` label.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab: `backlog.PRIORITIES = frozenset(high,medium,low)` + `_PRIORITY_RE` (backlog.py:53/60) - reuse.
- Recognized-but-optional pattern: `META_RECOGNIZED` not `META_REQUIRED` (Scope-Paths/Blocks-Release/From-Backlog precedent); hoisted setter write is the `--blocks-release`/`--from-backlog` pattern (status_set.py) so it persists on a no-op transition.
- `Item.priority` already exists (attention.py:45) and is rendered (:435); `_plans_record` (:317) just needs to read + pass it.

## Findings

Pure clone of the recognized-but-optional-field + hoisted-setter + attention-populate pattern used repeatedly this program; the only plan-specific bit is `_plans_record`.

## Proposed changes (ordered, validatable)

1. `ipd_schema.py`: RECOGNIZE `Priority` (add to `META_RECOGNIZED`) only; enum validation is `aw check`'s job (item 3), not the schema layer.
2. `cli.py`+`status_set.py`: `aw ipd set --priority` (hoisted write).
3. `check_engine.py`: enum validation.
4. `attention.py`: populate `Item.priority` in `_plans_record`.
5. `tests/`: lint-clean with Priority; set/clear/no-op-persist; invalid flagged; board shows plan priority.

## Deferred / out of scope (with reason)

- Specs Priority: child 02. Research Priority: child 03. (Same pattern, different contracts.)

## Scope check

- Over-scope: none.
- Under-scope: none (plans field+setter+check+attention complete).

## Required tests / validation

- An IPD with `- Priority: high` lints clean at all phases; absent Priority also clean (optional).
- `aw ipd set <plan> --priority medium` writes it and persists on a same-status no-op; `--priority -` clears.
- `aw check` flags an out-of-vocab Priority on a plan.
- `aw attention` LABELS a plan by its priority (`[high]`/`[medium]`/`[low]` bracket via the existing renderer, attention.py:717); the shared sort key (attention.py:186) is unchanged (E-03 scope note).

## Spec / documentation sync

- Document `Priority` in the IPD metadata docs + `aw ipd --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the orchestrator's OQ-01 (absent = unprioritized, no `[priority]` label, no priority sort introduced). This child follows that: `_plans_record` passes `Item.priority` (None when absent) to the existing type-agnostic label renderer and does not alter the sort key.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `aw ipd lint --phase author` on a fixture IPD carrying `- Priority: high` showing exit 0 (clean, schema RECOGNIZES the field), and on one with NO Priority also exit 0 (optional). Pasted `aw ipd set <fixture> --priority medium` run then the resulting `- Priority: medium` line, a same-status no-op re-run showing the line PERSISTS, and `--priority -` showing the line removed. A grep proving `ipd_schema` adds `META_PRIORITY` to `META_RECOGNIZED` (recognition only) and does NOT add value validation to `validate_metadata`.
  - Observed evidence: LINT (live) - `aw ipd lint --phase author <fixture with Priority: high>` -> `-    approved     plan        20260828-demo-01-pri001  [high]  conforming`; with NO Priority -> `-    approved     plan        20260828-demo-01-pri001  conforming` (both clean). SETTER (live) - `aw ipd set approved pri001 --priority medium` -> file gains `- Priority: medium`; a same-status no-op re-run (`aw ipd set approved pri001` with NO --priority) -> board shows `[medium]` and the line PERSISTS; `aw ipd set approved pri001 --priority -` -> 0 `- Priority:` lines (cleared). GREP - `grep -n META_PRIORITY agent_workflows/ipd_schema.py` -> `196:META_PRIORITY = "Priority"` and `209:        META_PRIORITY,` (inside META_RECOGNIZED); `validate_metadata` has no Priority enum check. TESTS - `python3 -m pytest tests/test_ipd_priority.py -o addopts=""` -> `7 passed`: `PrioritySchemaTests::test_priority_is_recognized_not_required` (in META_RECOGNIZED, not META_REQUIRED), `::test_schema_does_not_enum_validate_priority` (no IPD-M103 for a recognized bogus value), `PrioritySetterTests::test_set_writes_persists_on_noop_and_clears` (set medium -> no-op persists -> `-` clears, via real `cli.main(["ipd","set",...])`).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted `aw check` run over a fixture plan carrying `- Priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `- Priority: high` and no Priority showing NO such finding. A grep proving the enum check in `check_engine.py` consumes the shared `backlog.PRIORITIES` (no forked `{"high","medium","low"}` literal). Pasted new/updated test in tests/ asserting all three cases.
  - Observed evidence: CHECK (live) - `aw check plans` over a `- Priority: bogus` fixture -> `Issue: priority not in ['high', 'low', 'medium']: 'bogus'` (rule `check.priority-invalid`, exit 1); over `- Priority: high` and an absent-Priority fixture -> 0 priority findings. GREP - the new `check_plan_priority` in check_engine.py uses `_backlog.PRIORITIES` (lines 1877/1886/1889) with `sed -n '/def check_plan_priority/,/return drift/p' | grep -c '"high"'` = `0` (no forked literal); `check.priority-invalid` is registered in `RULE_REGISTRY`. TESTS - part of the `7 passed` run: `PriorityCheckTests::test_check_flags_out_of_vocab_only` (exactly 1 finding, on the bogus fixture; none for high/absent), `::test_check_uses_shared_backlog_vocab_not_forked` (every member of `backlog.PRIORITIES` passes silently), `::test_check_content_plans_surfaces_priority_invalid` (wired into the plans content path). Regression: `python3 -m pytest tests/test_check_engine.py -o addopts=""` green (part of `40 passed`).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture plan carrying `- Priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a plan with no Priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence: ATTENTION (live) - `aw attention --format json` for a `- Priority: high` plan -> the item JSON includes `"priority": "high"` (full record: `{"id":"pri001", ..., "priority":"high", "blocks_release":null}`); `aw ipd lint`'s board renders the `[high]` label; a plan with NO Priority -> `"priority": null`. DIFF - `git diff HEAD -- agent_workflows/attention.py` shows ONLY the `_plans_record` change (the `pr_m`/`pr` parse + `priority=pr` kwarg on the existing `Item(...)`); the shared sort key is NOT in the diff (unchanged). TESTS - part of the `7 passed` run: `PriorityAttentionTests::test_plans_record_populates_priority` asserts `_plans_record` yields `Item.priority == "high"` for a Priority plan and `None` for an absent one. Regression: `python3 -m pytest tests/test_attention.py tests/test_attention_priority_blocker.py -o addopts=""` green.
  - Result: pass



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`ipd_schema.py`, `status_set.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch specs/research contracts (children 02/03) or the shared attention sort key. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.
