# IPD: Stop inferring workflow-history order from line position in the lifecycle-transition check

- Date: 2026-09-24
- Kind: child
- Concern: `ipd_lifecycle._plan_status_events` ends with `# Inline history is stored newest-first; reverse to oldest-first for derivation.` / `events.reverse()`. Writers disagree on direction (`status_set.apply_status_change` PREPENDS; authors APPEND; a tool-touched plan carries BOTH, separated by a blank line), so the reversal inverts every oldest-first block and `check_engine.check_lifecycle_transitions` reports `check.lifecycle-transition-invalid` on conformant plans. RE-MEASURED 2026-09-24 at `cfc7f5c1`: `aw check plans --agent` reports ZERO findings of that rule, but only because the 14 current `pending/` plans are all tool-written newest-first; the reader defect is unchanged (probe below inverts a two-line oldest-first history to `['to-review', 'draft']`), and over the whole plans tree the same predicate flags 435 edges, of which 59 plans are strictly oldest-first in file order and 16 are mixed. The zero is an artifact of today's corpus, and the next hand-authored pending plan reintroduces it.
- Scope: IN: replace the fixed reversal with a per-block direction detection keyed on the record DATE plus the in-block ordinal, with an explicit UNORDERED outcome for a same-date tie the file cannot resolve; make the checker skip (never guess) edges touching an unordered tie; enumerate `approved -> reviewed` as the one legal backward edge (spec `2vev8j` 4.8) and fail closed on every other; record the ordering rule and the backward-edge table in the IPD spec; tests for newest-first, oldest-first and mixed files. OUT: the `seq` journal (spec `2vev8j` 4.3, owned by `ms06pi`), the UTC/local writer defect (spec 4.4), and any rewrite of plan histories.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/check_engine.py, tests/test_history_order.py, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- Set: historder
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 63h054
- From-Backlog: tk1gqo
- Blocks-Release: next
- From-Spec: 2vev8j

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tk1gqo; re-measured 0 pending findings (corpus artifact) versus a still-live inverting reader, 435 whole-tree edges today, and 22 flagged plans (0 pending) under the proposed direction-detecting reader.

## Goal

Make the lifecycle-transition check read a plan's inline history in the order the file actually records it, detected from the dates rather than assumed from position, and refuse to validate any edge whose order the file cannot establish. This is migration step 1 of approved spec `2vev8j` Section 6 ("stop the fixed-direction interpretation of unsequenced legacy history"), which needs no data migration.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: tests first (they must fail on the current reader)

- [ ] E-01 Add `tests/test_history_order.py` with three fixture plans written under `pending/` in a `tempfile` repo and asserted through BOTH `ipd_lifecycle._plan_status_events` (or its successor) and `check_engine.check_lifecycle_transitions`: (a) NEWEST-FIRST `2026-09-03 approved`, `2026-09-02 reviewed`, `2026-09-01 draft` -> oldest-first `draft, reviewed, approved`, zero findings; (b) OLDEST-FIRST, the same three lines reversed -> the same order, zero findings; (c) MIXED (the `kw5y2s` shape): a tool block `2026-09-03 approved`, `2026-09-02 reviewed`, blank line, author block `2026-08-30 draft`, `2026-09-01 to-review` -> `draft, to-review, reviewed, approved`, zero findings. Add two negative tests so the check is not weakened: (d) an oldest-first file with a real cross-day `approved` then `draft` still yields exactly one finding naming `'approved' -> 'draft'`; (e) a one-block file whose lines all share one date (`to-review` above `draft`, both `2026-09-01`) yields ZERO findings and the group is reported unordered.
  - Depends on: none
  - Expected outcome: the new file exists; on the unmodified reader (b) and (c) fail with `backwards transition`, (e) fails with a finding, and (a) and (d) pass.
  - Execution state: pending

### Task group 2: the reader

- [ ] E-02 In `agent_workflows/ipd_lifecycle.py`, delete the `events.reverse()` line and its "stored newest-first" comment. Add `_plan_status_event_groups(text)` returning oldest-first date groups `(date, [(status, actor), ...], ordered: bool)`. Algorithm: split the `## Workflow history` section into CONTIGUOUS BLOCKS of record lines (a blank or non-record line ends a block; `record_history._inline_history_records` flattens these, so read the section with the same `_HISTORY_RECORD_RE`/heading rules rather than a new grammar). Per block, classify DIRECTION from adjacent record dates over ALL records in the block (status and note lines alike): only ascending steps -> oldest-first; only descending -> newest-first; both -> mixed; none (single date) -> unknown. Sort all status events by DATE (ISO strings sort correctly). Within one date, the group is `ordered=True` and sorted by in-block ordinal (ascending for oldest-first, descending for newest-first) only when every member sits in ONE block of known direction or the group has one distinct status; otherwise `ordered=False` and members keep file order for display only. Keep `_plan_status_events` as the flattened oldest-first list of those groups, so `derive_plan_status` keeps its signature.
  - Depends on: E-01
  - Expected outcome: fixtures (a), (b), (c) produce the oldest-first sequence; (e) produces one group with `ordered=False`.
  - Execution state: pending

### Task group 3: the checker and the backward-edge table

- [ ] E-03 In `ipd_lifecycle.validate_transition`, add a module constant `_LEGAL_BACKWARD_EDGES = frozenset({("approved", "reviewed")})` with a comment citing spec `2vev8j` 4.8, and permit an edge in that set before the `to_rank < from_rank` rejection. Every other rank decrease still returns `missing predecessor: backwards transition` (fail closed; deleting the rank comparison is explicitly rejected by 4.8 point 2). In `check_engine.check_lifecycle_transitions`, iterate `_plan_status_event_groups`: an `ordered=False` group validates NO edge into, within, or out of it (reset `prev` to the group's single status when it has one distinct forward status, else to `None`, meaning the next edge is unvalidated). Leave the pending-only scoping and the finding text unchanged.
  - Depends on: E-02
  - Expected outcome: all five fixtures pass; an `approved -> reviewed -> approved` round trip yields zero findings; `approved -> to-review` still yields one.
  - Execution state: pending

### Task group 4: contract and corpus

- [ ] E-04 Amend `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` next to its `## Workflow history` bullet: state that the file's line direction is NOT normative (writers prepend, authors append), that readers derive order from the date plus per-block direction and treat an unresolvable same-date tie as unordered, that the durable fix is the `seq` journal of spec `2vev8j` 4.3, and list the legal backward edges (`approved -> reviewed` only).
  - Depends on: E-03
  - Expected outcome: the spec names the rule and the edge table; `grep -n "approved -> reviewed" <spec>` shows it.
  - Execution state: pending
- [ ] E-05 Re-measure the corpus: `python3 -m agent_workflows check plans --agent` and a whole-tree count through the new reader (the one-liner in V for this item).
  - Depends on: E-03
  - Expected outcome: 0 `check.lifecycle-transition-invalid` in pending; whole-tree edges at or below the 22 flagged plans the prototype measured, and every survivor is a cross-day edge.
  - Execution state: pending
- [ ] E-06 Run the full suite bare: `python3 -m pytest`.
  - Depends on: E-04, E-05
  - Expected outcome: summary line with 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The checker runs alongside the authoritative `- Status:` read and is pending-only (`check_lifecycle_transitions` comment "Scope to PENDING-lane plans only"), so this change moves no plan's executability.
- `_plan_status_events` has one production caller (`check_engine.check_lifecycle_transitions`) plus `ipd_lifecycle.derive_plan_status`; `validate_transition` in `ipd_lifecycle` is distinct from `run_state.validate_transition` (run-state machine), which this plan does not touch.
- `attention_contract.newest_history_record` and `plan_readiness.extract_newest_history_entry` are DELIBERATELY positional (first record = newest) and gate auto-approval; their docstrings reject a date-max rule. This plan does NOT touch them.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Claim | Measured 2026-09-24 at `cfc7f5c1` |
|---|---|---|
| F-1 | Rule count in `aw check plans` | 0 of 11 findings (all `check.ipd-uncarried-obligation`/collisions); direct `check_lifecycle_transitions(Path("."))` also 0 |
| F-2 | Reader still inverts | `_plan_status_events("## Workflow history\n- 2026-09-01 draft (a): x\n- 2026-09-02 to-review (a): y\n")` -> `['to-review', 'draft']` |
| F-3 | Why 0 is not a fix | 14 pending plans, none strictly oldest-first; over all 639 plans with 2+ status events, 59 are oldest-first, 16 mixed, 161 single-date |
| F-4 | Current predicate, whole tree | 435 failing edges |
| F-5 | Date sort plus direction tiebreak, no unordered state | 333 (ties dominate: `to-review -> draft` same-day 63, `executed -> approved` same-day 50) |
| F-6 | Proposed design (per-block direction, unordered ties skipped, `approved -> reviewed` legal) | pending 0, whole tree 22 plans, 510 unordered tie groups, top survivors cross-day `to-review -> executed` 10, `approved -> to-review` 5 |

Probes were untracked scratch scripts; V-05 re-derives F-6 with the real functions.

BACKLOG CLAIM NOW FALSE: `tk1gqo`'s "third defect" (`attention_contract` reading the LAST record as newest) is already fixed; `attention_contract.newest_history_record` takes the FIRST record ("corrected by plan `vhbvwz` E-02"). Not in scope.

## Proposed changes (ordered, validatable)

1. Failing tests (E-01). 2. Direction-detecting grouped reader (E-02). 3. Checker consumes groups; one enumerated backward edge (E-03). 4. IPD spec amendment (E-04). 5. Corpus re-measure (E-05). 6. Bare suite (E-06).

SAME-DATE TIE, stated exactly: two status events with the same date are ordered by their in-block ordinal ONLY when both lie in one contiguous block whose other records prove its direction by a strict date change. If the block is single-date (no evidence), mixed, or the tie spans two blocks, the group is UNORDERED: no transition into, inside, or out of it is validated, and nothing is guessed. This follows spec `2vev8j` 4.7 ("do NOT run forward-transition validation across unordered pre-checkpoint records") and is why F-5's rank-free date sort is rejected. A lifecycle-rank tiebreak is also rejected (it infers order from the invariant being checked, `tk1gqo` 2026-09-05 note).

## Deferred / out of scope (with reason)

- The `seq` history journal that makes order explicit (spec `2vev8j` 4.3, migration steps 3 to 6).
  - Carrier: ms06pi
- UTC versus local-date writer stamps (spec `2vev8j` 4.4); a same-day tie created by it is handled here as unordered, not corrected.
  - Carrier-Declined: no dedicated item exists; spec `2vev8j` 4.4 owns it and `ms06pi` graduates that spec.
- The 22 whole-tree survivors in terminal directories; the rule is pending-only and spec `2vev8j` Section 6 step 5 freezes those trees.
  - Carrier-Evidence: .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md

## Scope check

- Over-scope: none. The backward-edge table is included because spec `2vev8j` 4.8 point 1 makes it part of reaching 0 honestly.
- Under-scope: `plans/README.md` still says history lines are "newest-first"; left as-is because it describes what `aw set` writes, which remains true.

## Required tests / validation

`tests/test_history_order.py` fixtures (a) to (e), shown failing before E-02/E-03 and passing after; `aw check plans --agent`; bare suite.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` (declared in Scope-Paths). WHY: its "append one dated line per workflow touch" wording implies oldest-first while `aw set` prepends, and spec `2vev8j` 4.8 point 3 names the IPD spec as the home of the enumerated backward-edge table. Spec `2vev8j` itself is not edited.

## Open questions

### OQ-01: Is `approved -> reviewed` the only legal backward edge?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: yes, only that edge, because spec `2vev8j` 4.8 names only it and mandates fail-closed for anything unlisted. Whole-tree `approved -> to-review` (5 cross-day edges) would stay flagged; widening the table is a maintainer call.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: with ONLY the test file added (reader unmodified), paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q` output showing fixtures (b), (c) and (e) FAILED with `backwards transition` text and (a), (d) passed.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/ipd_lifecycle.py` showing `events.reverse()` removed, and a `python3 -c` call of `_plan_status_event_groups` on fixture (e) text printing one group with `ordered=False`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q` showing all tests passed, plus `python3 -c 'from agent_workflows import ipd_lifecycle as IL; print(IL.validate_transition("approved","reviewed"), IL.validate_transition("approved","to-review"))'` showing `ok=True` then `ok=False ... backwards transition`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git diff .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` showing the ordering rule and the `approved -> reviewed` table.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the rule count from `python3 -m agent_workflows check plans --agent | grep -o 'check.lifecycle-transition-invalid' | wc -l` (expected 0) and the whole-tree flagged-plan count from a one-off `python3 -c` that monkeypatches the pending-only guard away, e.g. by calling the new group reader plus `validate_transition` over `glob(".aw/records/plans/**/*.ipd.md", recursive=True)` with the checker's edge loop (expected at or below 22 plans, every survivor a cross-day edge).
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the `N passed` summary line of bare `python3 -m pytest`, with 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <plan> -- <Scope-Paths>`; never push. Move to `executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every V item carries pasted evidence.
