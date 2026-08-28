# IPD: Add Priority to the spec contract plus aw specs set and attention rendering

- Date: 2026-08-27
- Kind: child
- Concern: Specs have no `Priority`, so they cannot be prioritized on the attention board. Add it as a recognized-but-optional spec metadata field reusing the shared `{high,medium,low}` vocab, with the `aw specs set` setter, `aw check`/`aw specs check` validation, and `_spec_record` attention rendering. Part of Set xprio (graduated from backlog p9o1oo).
- Scope: (1) Spec contract (`specs.py`): add a reader for an optional `- Priority:` bullet (mirroring `_read_blocks_release`, specs.py:149); the value is enum-validated in `validate_spec` (see (3)) - note `validate_spec` has no unknown-field rejection, so a Priority bullet needs no "recognition" step, only the reader + the explicit enum check. Optional so existing specs are not mass-failed (none carry Priority today). (2) Setter: add `--priority <low|medium|high|->` to `aw specs set` (cli.py + specs.py), writing/clearing the bullet as a side-effect of a status transition (the same shape as `--blocks-release`, specs.py:510-514). NOTE: `aw specs set` REQUIRES a target status (positional `<status>` or `--status`) and always appends a history record and re-runs `validate_spec` (specs.py:499-524); so setting priority re-asserts the current status (a no-op transition still records history), and once (3)'s enum check lives in `validate_spec` the setter itself REFUSES an out-of-vocab `--priority bogus` (byte-identical refuse path, specs.py:516-523). (3) Validation: enum-validate the value in `validate_spec` (specs.py) so `aw specs check`/`aw check` (and the setter's refuse path) flag an out-of-vocab value; reuse shared `backlog.PRIORITIES`. (4) Attention: populate `Item.priority` in `attention._spec_record` (:289) from the spec's `- Priority:`. Absent = unprioritized. Specs only; plans = child 01, research = child 03.
- Scope-Paths: agent_workflows/specs.py, agent_workflows/cli.py, agent_workflows/check_engine.py, agent_workflows/attention.py, agent_workflows/backlog.py, tests/
- Status: executed
- Set: xprio
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: rp859c

## Workflow history
- 2026-08-28 executed (aw oc run model=its_direct/pt3-claude-opus-4.8-1m-us): xprio-02 rp859c: Priority on spec contract (reader + validate_spec enum + aw specs set --priority + attention render), committed 3eaf7c0 [Scope reconciliation - in-scope-unmodified agent_workflows/attention.py: committed pre-begin (E-03 in 3eaf7c0); in-scope-unmodified agent_workflows/backlog.py: import-only, not modified; in-scope-unmodified agent_workflows/check_engine.py: not needed; spec enum lives in validate_spec (specs.py); in-scope-unmodified agent_workflows/cli.py: committed pre-begin (E-01 in 3eaf7c0); in-scope-unmodified agent_workflows/specs.py: committed pre-begin (E-01/E-02 in 3eaf7c0); in-scope-unmodified tests/: test committed pre-begin (3eaf7c0)]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-201..PR-204 fixed (specs-set status-coupling + setter-refuse consequence, reader-not-recognition, label-not-sort, OQ-01 resolved, V-01/V-02 evidence)

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add a recognized-but-optional `Priority` (shared low/medium/high vocab) to specs: contract recognition, `aw specs set --priority`, validation, and `_spec_record` attention rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: contract + setter

- [x] E-01 In `specs.py`, add a reader for an optional `- Priority:` bullet (mirror `_read_blocks_release`, specs.py:149); the enum validation itself is E-02 (`validate_spec` has no unknown-field rejection, so no separate "recognition" step is needed). Optional (existing specs without it stay conforming). Add `--priority <low|medium|high|->` to `aw specs set` (cli.py + specs.py), writing/clearing the bullet as a side-effect of the required status transition (same shape as `--blocks-release`, specs.py:510-514); a priority-only change is expressed as a no-op status transition (which still appends a history record).
  - Depends on: none
  - Expected outcome: a spec may carry `- Priority: high` and `aw specs check` conforms; `aw specs set <status> <spec> --priority medium` writes it (re-asserting the current status if unchanged, appending history), `--priority -` clears; absent stays conforming.
  - Done note: Added `_PRIORITY_RE` + `_read_priority(lines)` to specs.py (mirroring `_BLOCKS_RELEASE_RE`/`_read_blocks_release`). Added `--priority <low|medium|high|->` to `aw specs set` in cli.py (choices-guarded) and the writer in specs.run_set, which funnels through the shared idempotent `releases.set_priority_line` (no forked write path) right after the `--blocks-release` write and before the `validate_spec` refuse gate; `-`/None clears. Verified live: a `- Priority: high` spec conforms (explicit-path `aw specs check` exit 0); `aw specs set draft <spec> --priority medium` writes `- Priority: medium`; `--priority -` clears; absent conforms.
  - Execution state: performed

### Task group 2: check + attention

- [x] E-02 Flag an out-of-vocab `- Priority:` value on a spec in `aw specs check`/`aw check` (validated against shared `backlog.PRIORITIES`), added to `validate_spec` (specs.py) alongside the existing status/gate checks. Note: `validate_spec` today ignores unrecognized bullets, so this explicit enum check is what catches a bad value. Consequence to verify: because `aw specs set` re-runs `validate_spec` and refuses a nonconforming result (specs.py:516-523), placing the enum check here also makes the SETTER refuse an out-of-vocab `--priority bogus` (not merely a later `aw check` report).
  - Depends on: E-01
  - Expected outcome: `aw specs check`/`aw check` reports a finding for a spec carrying `- Priority: bogus` and reports none for `- Priority: high` or an absent Priority.
  - Done note: Added a `spec.priority-invalid` enum check to `validate_spec` (specs.py, right before `return drift`): when `_read_priority` is non-None and the value is not in the SHARED `_backlog.PRIORITIES` (imported, 0 forked literals), it flags `spec.priority-invalid`; absent = silent. Verified live: `aw check specs` and explicit-path `aw specs check` both report `spec.priority-invalid: priority not in ['high','low','medium']: 'bogus'` (exit 1); `- Priority: high`/absent -> no finding. Setter refuse: `aw specs set draft <spec> --priority bogus` is refused (the CLI `choices=[low,medium,high,-]` guard rejects it at parse; a hand-passed bogus value is additionally refused by the `validate_spec` re-run in run_set, proven by unit test `test_setter_refuses_out_of_vocab_via_validate_spec` -> rc 1, file unchanged).
  - Execution state: performed
- [x] E-03 Populate `Item.priority` in `attention._spec_record` (attention.py:289) from the spec's `- Priority:` line so the board labels a spec's priority (absent = unset). Scope note: reuses the EXISTING label renderer (attention.py:717) only; it does NOT change the shared attention sort key (attention.py:186), which excludes priority for all trees today.
  - Depends on: E-01
  - Expected outcome: `aw attention` renders a `[high]`/`[medium]`/`[low]` label for a spec carrying `- Priority:`, matching backlog's label rendering; no label for an absent Priority.
  - Done note: In `attention._spec_record`, read `specs_mod._read_priority(lines)` and pass `priority=pr` (None when absent) to the existing `Item(...)` constructor, mirroring the `blocks_release=` populate. My attention.py diff is ONLY the `pr` read + `priority=pr` kwarg; the shared sort key is untouched. Verified live: `_spec_record` yields `Item.priority == "high"` for a `- Priority: high` spec and `None` for an absent one; the board renders `[medium]` after a set.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Shared vocab `backlog.PRIORITIES` (backlog.py:53) - reuse.
- Spec contract lives in `specs.py` (status enum, required sections, typed gates, history); add Priority as an optional recognized bullet there; `aw specs set` is the tool-owned writer.
- `attention._spec_record` (:289) builds the spec Item; populate its `priority` (Item.priority exists, :45).

## Findings

Same recognized-but-optional-field + setter + attention pattern as the plans child; spec-specific bits are the specs.py contract + `aw specs set` + `_spec_record`.

## Proposed changes (ordered, validatable)

1. `specs.py`: add an optional `Priority` reader (mirror `_read_blocks_release`); enum validation is E-02 in `validate_spec` (shared vocab).
2. `cli.py`+`specs.py`: `aw specs set --priority` (write/clear + history).
3. `check_engine.py`/specs check: enum validation.
4. `attention.py`: populate `Item.priority` in `_spec_record`.
5. `tests/`: specs-check-clean with/without Priority; set/clear; invalid flagged; board shows spec priority.

## Deferred / out of scope (with reason)

- Plans Priority: child 01. Research Priority: child 03.

## Scope check

- Over-scope: none.
- Under-scope: none (specs field+setter+check+attention complete).

## Required tests / validation

- A spec with `- Priority: high` passes `aw specs check`; a spec without it also passes (optional).
- `aw specs set <spec> --priority medium` writes it; `--priority -` clears.
- `aw check`/`aw specs check` flag an out-of-vocab value.
- `aw attention` LABELS a spec by its priority (`[high]`/`[medium]`/`[low]` bracket via the existing renderer, attention.py:717); the shared sort key (attention.py:186) is unchanged (E-03 scope note).

## Spec / documentation sync

- Document `Priority` in the spec contract docs + `aw specs set --help`.

## Open questions

### OQ-01: none beyond the orchestrator's absent-renders-as question.

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the orchestrator's OQ-01 (absent = unprioritized, no `[priority]` label, no priority sort introduced). This child follows: `_spec_record` passes `Item.priority` (None when absent) to the existing renderer and does not alter the sort key.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Pasted `aw specs check` on a fixture spec carrying `- Priority: high` showing conformance, and on a spec with NO Priority also conforming (optional). Pasted `aw specs set <current-status> <fixture> --priority medium` run (status re-asserted as a no-op transition) then the resulting `- Priority: medium` bullet AND the appended `## Workflow history` record, and `aw specs set <current-status> <fixture> --priority -` showing the bullet removed. A grep proving the enum check in `specs.py`/`validate_spec` consumes the shared `backlog.PRIORITIES` (no forked `{"high","medium","low"}` literal).
  - Observed evidence: SPECS CHECK (live, explicit-path form) - a `- Priority: high` spec -> `aw specs check <spec>` -> `aw specs check: all specs conform.` (exit 0); with NO Priority -> also `all specs conform.` (exit 0). SETTER (live) - `aw specs set draft <spec> --priority medium --message set` -> file gains `- Priority: medium` (board shows the spec `unchanged` status, priority written); `aw specs set draft <spec> --priority -` -> 0 `- Priority:` lines (cleared, board shows `[medium]` pre-clear). GREP - `grep -n _backlog.PRIORITIES agent_workflows/specs.py` -> the enum check at specs.py:281/286 uses `_backlog.PRIORITIES`; `sed -n '/priority = _read_priority/,/return drift/p' | grep -c '"high"'` = `0` (no forked literal). TESTS - `python3 -m pytest tests/test_spec_priority.py -o addopts=""` -> `7 passed`: `SpecPriorityContractTests::test_valid_priority_conforms` (every backlog.PRIORITIES member clean), `::test_absent_priority_conforms`, `::test_reader_returns_value_or_none`; `SpecPrioritySetterTests::test_set_writes_and_clears` (via real `specs.run_set`). NOTE: the sidecar/inline history model keeps the latest inline record; the transition is recorded to the global history sidecar (a same-status re-assert), consistent with the specs history convention.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Pasted `aw specs check` (and `aw check`) over a fixture spec carrying `- Priority: bogus` showing a `priority`-invalid finding (with its rule id), and over fixtures carrying `- Priority: high` and no Priority showing NO such finding. PLUS pasted `aw specs set <status> <fixture> --priority bogus` showing the setter REFUSES (byte-identical, nonzero exit) because `validate_spec` now rejects the value. Pasted new/updated test in tests/ asserting the check (all three cases) and the setter-refuse behavior.
  - Observed evidence: CHECK (live) - `aw check specs` over a `- Priority: bogus` spec -> `Issue: priority not in ['high', 'low', 'medium']: 'bogus'` (rule `spec.priority-invalid`); explicit-path `aw specs check <spec>` -> `spec.priority-invalid: priority not in ['high','low','medium']: 'bogus'` (exit 1); `- Priority: high` and absent -> no `spec.priority-invalid`. SETTER REFUSE (live) - `aw specs set draft <spec> --priority bogus` -> `argument --priority: invalid choice: 'bogus' (choose from 'low','medium','high','-')` (CLI choices guard). The DEEPER validate_spec refuse (hand-passed bogus, byte-identical, file unchanged, rc 1) is proven by the unit test `SpecPrioritySetterTests::test_setter_refuses_out_of_vocab_via_validate_spec`. TESTS - part of the `7 passed` run: `SpecPriorityContractTests::test_out_of_vocab_priority_flagged` (exactly 1 `spec.priority-invalid`), `test_valid_priority_conforms`/`test_absent_priority_conforms` (none), and the setter-refuse test. Regression: `python3 -m pytest tests/test_specs_verbs.py tests/test_check_engine.py -o addopts=""` green (part of `55 passed`).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Pasted `aw attention --format json` (or the table) for a fixture spec carrying `- Priority: high` showing `"priority": "high"` (JSON) / a `[high]` label (table), and for a spec with no Priority showing `"priority": null` / no label. A diff/grep proving `attention.py:186` sort key is UNCHANGED (priority not added to the sort tuple).
  - Observed evidence: ATTENTION (live) - `attention._spec_record` for a `- Priority: high` spec yields `Item.priority == "high"`; for a spec with no Priority yields `None` (the JSON serializer renders these as `"priority": "high"` / `"priority": null`, identical to the plans path proven in 1b45el V-03). DIFF - `git diff HEAD -- agent_workflows/attention.py` shows ONLY the `_spec_record` change (the `pr = specs_mod._read_priority(lines)` read + the `priority=pr` kwarg on the existing `Item(...)`); the shared sort key is NOT in the diff (unchanged). TESTS - part of the `7 passed` run: `SpecPriorityAttentionTests::test_spec_record_populates_priority` asserts `_spec_record` -> `Item.priority == "high"` for a Priority spec and `None` for an absent one. Regression: `tests/test_attention.py tests/test_attention_priority_blocker.py` green.
  - Result: pass



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line. All open questions above are resolved (OQ-01 defers only to the orchestrator's absent-rendering decision). Scope fence: changes are confined to this plan's Scope-Paths (`specs.py`, `cli.py`, `check_engine.py`, `attention.py`, `backlog.py` import-only, `tests/`); do NOT fork the shared `backlog.PRIORITIES` vocab and do NOT touch the plans/research contracts (children 01/03) or the shared attention sort key. The executor owns all path-scoped commits and never pushes. When reporting tests, PASTE THE ACTUAL RUNNER OUTPUT (never claim a pass not run). Move this plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item is verified with pasted evidence; if any validation fails, STOP and report rather than marking done.
