# IPD: attention board priority + labeled blocker columns with legend (awdoctor-01 corrective)

- Date: 2026-08-19
- Concern: The executed awdoctor-01 IPD was titled "compact attention board with urgency and blocking columns" but its E-items only delivered a folded dir prefix + an age marker (!/?) + a gate glyph (#). No priority column, no labeled blocker column, and no legend for the cryptic glyphs. The human reading `aw att` cannot see an item's priority or whether it blocks a release.
- Scope: The `agent_workflows/attention.py` Item model + its readers + `render_board`/`render_json`; a legend line on the human board; tests. No change to the attention contract classes, the scan, or any other verb.
- Kind: child
- Status: approved
- Set: awdoctorfix
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: hblwtx
- Approval: maintainer (chose option (a): author + execute the awdoctor-01 corrective), 2026-08-19

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created as a corrective for the awdoctor-01 title/scope gap (priority + labeled blocker columns + legend were promised by the title but not delivered by the E-items).
- 2026-08-19 reviewed (opencode): self-review - verified anchors (Item:34, 6 construction sites, _backlog_record:358 has item.priority/blocks_release, _spec_record:269, render_board:539, render_json:395 SCHEMA_VERSION:30), E/V bijection, additive JSON + schema bump, plain-branch-unchanged invariant, and the contract-correct 'new corrective IPD not in-place edit' posture.
- 2026-08-19 approved (opencode, on maintainer instruction): maintainer chose option (a) - author the corrective IPD and execute it.

## Goal

Close the awdoctor-01 gap: surface each item's PRIORITY and whether it is a RELEASE BLOCKER on the attention board, and add a LEGEND so the compact markers are self-explanatory. The underlying data already exists (backlog files carry `- Priority:`; items may carry `- Blocks-Release:`) but the attention `Item` drops it before rendering.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: carry the data on the Item model

- [ ] E-01 In `agent_workflows/attention.py`, add two OPTIONAL trailing fields to the `Item` NamedTuple (attention.py:34): `priority: Optional[str] = None` and `blocks_release: Optional[str] = None`. Trailing + defaulted so the SIX existing `Item(...)` constructions (actions/releases/specs/plans/research/backlog) keep working unchanged. Bump `SCHEMA_VERSION` (attention.py:30) from 1 to 2 and add both new keys to each item dict in `render_json` (attention.py:395) so the JSON stays in sync (additive).
  - Depends on: none
  - Expected outcome: `Item(...)` still constructs from every existing site; `attention.SCHEMA_VERSION == 2`; a JSON item dict now has `priority` and `blocks_release` keys.
  - Execution state: pending

- [ ] E-02 Populate the new fields in the readers that have the data. In `_backlog_record` (attention.py:358) set `priority=item.priority` and `blocks_release=item.blocks_release` (both already parsed by `backlog.parse_item`). In `_spec_record` (attention.py:269) read `- Blocks-Release:` via `specs._read_blocks_release(lines)` and set `blocks_release=`. Other readers (plans/research/releases/actions) pass the fields as `None` (no priority/blocks-release concept there today) - update their `Item(...)` calls only if switching to keyword args; positional calls inherit the defaults.
  - Depends on: E-01
  - Expected outcome: a backlog item with `- Priority: high` yields an Item with `priority=="high"`; a backlog/spec item with `- Blocks-Release: next` yields `blocks_release=="next"`.
  - Execution state: pending

### Task group 2: render the columns + a legend

- [ ] E-03 In `render_board` (attention.py:539), (a) render PRIORITY on the colored per-item line as a compact bracket after the status (e.g. `[P:high]`), colored by level (high=red 196, medium=amber 214, low=grey 244), only when `it.priority` is set; (b) mark a RELEASE BLOCKER with a distinct labeled marker on the line (e.g. a `>` glyph before the name AND the item still appearing in the existing `## release-blockers` section from awdoctor-02); (c) add a one-line LEGEND immediately under the (optional) `VIEW INVALID` block / before the first `##` section, printed in the colored HUMAN view only, e.g. `legend: ! stale(>30d)  ? unknown-age  # blocked-by-gate  > release-blocker  [P:_] priority`. The plain/machine (`- [tree] path (status){gate}`) branch stays byte-for-byte unchanged; JSON is unaffected by the legend.
  - Depends on: E-01,E-02
  - Expected outcome: with `FORCE_COLOR`, a high-priority backlog item's line shows `[P:high]`; a `Blocks-Release: next` item shows the `>` marker and appears in `## release-blockers`; the board starts with a `legend:` line; `NO_COLOR`/piped output shows neither the legend nor the markers (stable machine shape preserved).
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_attention_priority_blocker.py` (`AttentionPriorityBlockerTests`) building `List[attention.Item]` in code (render_board is pure over items): assert (a) a `priority="high"` item renders `[P:high]` colored; (b) a `blocks_release="next"` item renders the `>` marker; (c) the colored board contains a `legend:` line; (d) the plain board is unchanged (no legend, no `[P:` , stable `- [tree] path (status)` shape); (e) `SCHEMA_VERSION==2` and a JSON item carries `priority`+`blocks_release`. Update any test that pins `SCHEMA_VERSION==1` or the exact JSON item key set (`tests/test_attention.py`, `tests/test_attention_contract.py`). Run the FULL serial suite and paste the tail.
  - Depends on: E-01,E-02,E-03
  - Expected outcome: the new module passes; any schema-pinning test updated to 2; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The attention `Item` is a `NamedTuple` (attention.py:34) built at six sites; trailing defaulted fields are the safe way to extend it.
- `backlog.parse_item` already exposes `.priority` and `.blocks_release`; `specs._read_blocks_release` reads the spec field. The data is present; only the Item + renderers drop it.
- `render_json` carries a `SCHEMA_VERSION`; changing the item shape requires a version bump (and updating any pinning test).
- The colored HUMAN board is the only surface that should gain the legend/markers; the plain branch is the stable machine contract (`- [tree] path (status){gate}`) and must not change.

## Findings

The awdoctor-01 title ("urgency and blocking columns") over-promised its three E-items (folded prefix + age marker + gate glyph). Root cause: priority is not a field on the attention `Item`, and there was no legend. This IPD adds the two fields + renders them with a legend. It does NOT edit the executed awdoctor-01 (a new corrective IPD is the contract-correct fix for a post-execution gap).

## Proposed changes (ordered, validatable)

1. Extend `Item` with `priority`/`blocks_release` (+ SCHEMA_VERSION bump + JSON keys).
2. Populate them in `_backlog_record` and `_spec_record`.
3. Render a priority bracket + release-blocker marker + a legend on the colored human board.
4. Tests + schema-pin updates.

## Deferred / out of scope (with reason)

- Priority for non-backlog trees (plans/specs/research): those trees have no priority concept today; the field stays `None` there. Deferred, not needed.
- Sorting the board by priority: this IPD SHOWS priority; re-ordering is a separate UX decision (OQ-01).

## Scope check

- Over-scope: none (touches only attention.py + its tests).
- Under-scope: does not re-order the board by priority (OQ-01).

## Required tests / validation

`tests/test_attention_priority_blocker.py` + updates to schema-pinning tests; the full serial suite must stay green.

## Spec / documentation sync

N/A: no spec governs the attention board's cosmetic columns; the legend is self-documenting.

## Open questions

### OQ-01: Should the board sort items by priority within a class group?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: Deferred. This IPD surfaces priority; whether high-priority items sort to the top of their class group is a follow-on UX decision, not required to close the awdoctor-01 gap.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -c "from agent_workflows import attention as a; print(a.SCHEMA_VERSION); i=a.Item('x','p','backlog','open','ready',None,None); print(i.priority, i.blocks_release)"` shows SCHEMA_VERSION 2 and both new fields default None; a `render_json` item dict contains `priority` + `blocks_release` keys.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a fixture backlog item with `- Priority: high` + `- Blocks-Release: next` scanned via `_backlog_record` yields `priority=="high"`, `blocks_release=="next"`; a spec with `- Blocks-Release: next` via `_spec_record` yields `blocks_release=="next"`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: with FORCE_COLOR a high-priority item's colored line shows `[P:high]`; a `blocks_release` item shows the `>` marker + appears in `## release-blockers`; the colored board starts with a `legend:` line; NO_COLOR/piped output has no legend/markers and keeps the `- [tree] path (status)` shape.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest tests/test_attention_priority_blocker.py -p no:xdist -q` and the tail of the full serial suite `python3 -m pytest -p no:xdist`; all green, schema-pin tests updated to 2.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.
