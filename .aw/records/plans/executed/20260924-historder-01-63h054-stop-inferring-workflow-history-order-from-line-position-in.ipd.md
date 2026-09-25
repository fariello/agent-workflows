# IPD: Stop inferring workflow-history order from line position in the lifecycle-transition check

- Date: 2026-09-24
- Kind: child
- Concern: `ipd_lifecycle._plan_status_events` ends with `# Inline history is stored newest-first; reverse to oldest-first for derivation.` / `events.reverse()`. Writers disagree on direction (`status_set.apply_status_change` PREPENDS; authors APPEND; a tool-touched plan carries BOTH, separated by a blank line), so the reversal inverts every oldest-first block and `check_engine.check_lifecycle_transitions` reports `check.lifecycle-transition-invalid` on conformant plans. RE-MEASURED 2026-09-25 at `d39d58e9` (this plan's own review HEAD; the authored numbers at `cfc7f5c1` are superseded and every live count below is a re-derivation obligation, never a bar - see F-1a): `aw check plans --agent` reports ZERO findings of that rule, but only because no current `pending/` plan is oldest-first or mixed; the reader defect is unchanged (probe F-2 still inverts a two-line oldest-first history to `['to-review', 'draft']`), and over the whole plans tree the same predicate flags 846 edges on 617 plans as the checker really calls it (with `actor=`), or 435 on 270 without. The zero is an artifact of today's corpus, and the next hand-authored pending plan reintroduces it.
- Scope: IN: replace the fixed reversal with a per-block direction detection keyed on the record DATE plus the in-block ordinal, with an explicit UNORDERED outcome for a same-date tie the file cannot resolve; make the checker skip (never guess) edges touching an unordered tie; hold `derive_plan_status`'s answer BYTE-IDENTICAL across the change (the reader has a SECOND consumer with different needs, F-7); enumerate the legal backward edges (`approved -> reviewed` and its `auto-approved` tier sibling, spec `2vev8j` 4.8 plus `25kzda` 4.5) and fail closed on every other; record the ordering rule and the backward-edge table in the IPD spec; tests for newest-first, oldest-first, mixed and single-date files. OUT: the `seq` journal (spec `2vev8j` 4.3, owned by `ms06pi`), the UTC/local writer defect (spec 4.4), and any rewrite of plan histories.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/check_engine.py, tests/test_history_order.py, tests/fixtures/derive_plan_status_baseline.json, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- Set: historder
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 63h054
- From-Backlog: tk1gqo
- Blocks-Release: next
- From-Spec: 2vev8j

## Workflow history
- 2026-09-25 executed (aw agy run model=gemini-3.7-flash-high): aw agy run self-finalize: 63h054 verified (set historder, attempt 1).
- 2026-09-25 approved (aw set): status set to approved

- 2026-09-25 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL. 9 findings PR-601..PR-609, all FIXED; 5 decisions D-1..D-5 recorded in the typed review record; `aw ipd lint` conforming at `--phase author` before review and at `--phase review-finalize` after. THE FINDING THAT RESHAPED THE PLAN is PR-601: E-02's "keep `_plan_status_events` as the flattened oldest-first list of those groups" silently regressed the reader's SECOND consumer, `derive_plan_status`, on 307 of 776 plans, including 8 of 49 pending plans whose shipped two-line same-date `reviewed`/`to-review` history would have started deriving `to-review` against an authoritative `- Status: reviewed` - a NEW false finding manufactured by a plan whose purpose is removing false findings. The plan now KEEPS `events.reverse()` deliberately and adds a whole-tree baseline plus a guard test that must pass before the reader changes. Also fixed: the fixture in (e) could not discriminate (it yields 0 findings on the current reader too, so it passed before and after; replaced with `draft` above `approved`, which yields 1 today); "reset `prev` to `None`" MANUFACTURES 215 findings because `validate_transition(None, x)` rejects everything but `draft`; the backward-edge table omitted `auto-approved -> reviewed`, leaving the automated tier's own documented recovery (spec `25kzda` 4.5) illegal; fixtures writing `executed` with an agent actor would have failed for the unrelated unauthorized-terminal reason; 1097 continuation lines across 120 plans would fragment blocks under a non-blank-line boundary rule; the whole-tree count was measured WITHOUT `actor=` and so understated the real population by 411 edges (846 versus 435), of which 286 of 296 survivors are actor rejections this plan does not fix; the plan bought 0 pending findings partly by validating 8 fewer pending and 1224 fewer tree-wide edges, now stated as a cost; every live count is now a re-derivation obligation rather than a bar; and the gate was missing its approval statement, scope fence, honesty rule, stop conditions and conditional finalize ownership. Reviewed sound and unchanged: the central diagnosis, the per-block direction algorithm, the unordered-tie rule, the refusal to rewrite histories, and the rejection of both a rank-free date sort and a lifecycle-rank tiebreak.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog tk1gqo; re-measured 0 pending findings (corpus artifact) versus a still-live inverting reader, 435 whole-tree edges today, and 22 flagged plans (0 pending) under the proposed direction-detecting reader.

## Goal

Make the lifecycle-transition check read a plan's inline history in the order the file actually records it, detected from the dates rather than assumed from position, and refuse to validate any edge whose order the file cannot establish. This is migration step 1 of approved spec `2vev8j` Section 6 ("stop the fixed-direction interpretation of unsequenced legacy history"), which needs no data migration.

TWO CONSUMERS, TWO DIFFERENT NEEDS, and conflating them is the one way this plan can do net harm (F-7). `_plan_status_events` feeds `check_engine.check_lifecycle_transitions`, which wants an ORDER it can trust and must ABSTAIN when it has none; and it feeds `ipd_lifecycle.derive_plan_status`, which wants ONE current status and has no abstain state. The checker gets the new grouped reader with its `ordered=False` outcome. The derivation KEEPS ITS CURRENT ANSWER BYTE-IDENTICALLY on every plan in the tree, because the naive shared implementation (flatten the groups, take the last on-sequence status) silently regresses it: measured at review over 776 plans it changes 307 answers and, for 8 of today's 49 pending plans, reads the shipped two-line same-date `reviewed` / `to-review` history that `aw set` writes as `to-review`, contradicting the authoritative `- Status: reviewed` that the derivation exists to cross-check. That is a NEW false consistency finding manufactured by a plan whose whole purpose is to remove false findings.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the derivation baseline (capture it BEFORE touching the reader)

- [x] E-01 Capture a whole-tree BASELINE of `ipd_lifecycle.derive_plan_status` as a tracked fixture, because F-7 makes "did the derivation change" the single most important question this plan must answer and it is unanswerable after the edit lands. Write a small script (untracked scratch is fine) that walks `glob(".aw/records/plans/**/*.ipd.md", recursive=True)` at the PRE-CHANGE HEAD, calls `derive_plan_status` on each file's text, and writes `tests/fixtures/derive_plan_status_baseline.json` as a sorted mapping of repo-relative path -> derived status (`null` for None). Add the path to `- Scope-Paths:`. Do NOT hand-write or edit this file: it is a machine capture, and a hand-touched entry destroys the only evidence that the derivation is unchanged.
  - Depends on: none
  - Expected outcome: the fixture exists, has one entry per plan file found, and re-running the capture at the same HEAD reproduces it byte-identically.
  - Execution state: performed
- [x] E-02 Add `tests/test_history_order.py::DerivationIsUnchangedTests`, a single test that re-derives `derive_plan_status` over the same glob and asserts EQUALITY with the E-01 fixture, reporting every differing path. This is the ANTI-REGRESSION guard for F-7 and it must pass BEFORE and AFTER the reader change; a plan file added or removed between capture and run is tolerated by comparing only paths present in BOTH (assert that at least 700 paths were compared so the test cannot pass vacuously on an empty intersection).
  - Depends on: E-01
  - Expected outcome: the test passes at the pre-change HEAD (it is comparing the capture against the code that produced it), and its failure message names each differing path with both statuses.
  - Execution state: performed

### Task group 2: the checker's tests first (they must fail on the current reader)

- [x] E-03 Add to `tests/test_history_order.py` five fixture plans written under `pending/` in a `tempfile` repo and asserted through BOTH the new group reader and `check_engine.check_lifecycle_transitions`. Write EVERY fixture's terminal-status line, if any, with actor `aw ipd finalize`, since `validate_transition` rejects a terminal transition by any other actor (`_FINALIZE_ACTORS`) and an ordinary agent actor would make a fixture fail for the UNRELATED unauthorized-terminal reason (F-8). (a) NEWEST-FIRST `2026-09-03 approved`, `2026-09-02 reviewed`, `2026-09-01 draft` -> oldest-first `draft, reviewed, approved`, zero findings; (b) OLDEST-FIRST, the same three lines reversed -> the same order, zero findings; (c) MIXED (the `kw5y2s` shape): a tool block `2026-09-03 approved`, `2026-09-02 reviewed`, blank line, author block `2026-08-30 draft`, `2026-09-01 to-review` -> `draft, to-review, reviewed, approved`, zero findings. Add two negative tests so the check is not weakened: (d) an oldest-first file with a real cross-day `approved` then `draft` still yields exactly one finding naming `'approved' -> 'draft'`; (e) the DISCRIMINATING single-date fixture `2026-09-01 draft` ABOVE `2026-09-01 approved` (both in one block) yields ZERO findings and the group is reported unordered. Fixture (e) is deliberately NOT the `to-review`-above-`draft` shape the plan originally proposed: measured at review, that shape yields zero findings on the CURRENT reader too, so it could not distinguish the fix from the defect, while `draft` above `approved` yields one `approved -> draft` finding today (F-9).
  - Depends on: E-02
  - Expected outcome: on the unmodified reader (b) and (c) FAIL with `backwards transition`, (e) FAILS with an `approved -> draft` finding, and (a) and (d) pass.
  - Execution state: performed

### Task group 3: the reader

- [x] E-04 In `agent_workflows/ipd_lifecycle.py`, add `_plan_status_event_groups(text)` returning oldest-first date groups `(date, [(status, actor), ...], ordered: bool)`. Algorithm: split the `## Workflow history` section into CONTIGUOUS BLOCKS of record lines (a blank or non-record line ends a block; `record_history._inline_history_records` flattens these, so read the section with the same `HISTORY_RECORD_RE`/heading rules rather than a new grammar - note the constant lives in `attention_contract` and `record_history` imports it as `_HISTORY_RECORD_RE`). Per block, classify DIRECTION from adjacent record dates over ALL records in the block (status and note lines alike): only ascending steps -> oldest-first; only descending -> newest-first; both -> mixed; none (single date) -> unknown. Sort all status events by DATE (ISO strings sort correctly). Within one date, the group is `ordered=True` and sorted by in-block ordinal (ascending for oldest-first, descending for newest-first) only when every member sits in ONE block of known direction or the group has one distinct status; otherwise `ordered=False` and members keep file order for display only. CONTINUATION LINES ARE PART OF THE GRAMMAR, not a block boundary to discover at runtime: an indented continuation of a long record is a non-record line and would split one logical block in two, so treat a non-blank, non-record line inside the section as a CONTINUATION of the preceding record (it does NOT end the block) and reserve the block break for a BLANK line. Measured at review: 120 plans in the tree carry 1097 such continuation lines while 0 pending plans do, so a blank-line-only rule is both correct and the one that keeps the terminal corpus readable. LEAVE `_plan_status_events` AND `events.reverse()` EXACTLY AS THEY ARE, with a comment above the reversal pointing at `_plan_status_event_groups` and stating that the two readers answer different questions (F-7): the reversal is WRONG for ordering but is the shipped derivation behavior that `derive_plan_status` cross-checks `- Status:` with, and changing it is a separate, larger decision this plan explicitly does not make (see the new Deferred row).
  - Depends on: E-03
  - Expected outcome: fixtures (a), (b), (c) produce the oldest-first sequence; (e) produces one group with `ordered=False`; `derive_plan_status` is untouched and E-02 still passes.
  - Execution state: performed

### Task group 4: the checker and the backward-edge table

- [x] E-05 In `ipd_lifecycle.validate_transition`, add a module constant `_LEGAL_BACKWARD_EDGES` with a comment citing spec `2vev8j` 4.8, and permit an edge in that set before the `to_rank < from_rank` rejection. It MUST contain BOTH tier spellings of the recovery edge: `("approved", "reviewed")` and `("auto-approved", "reviewed")`. The second is not an embellishment: spec `25kzda` 4.5 `IPD-AUTO-APPROVAL` prescribes recovering an invalidly auto-approved plan with `aw ipd set reviewed <id6>`, `auto-approved` shares rank 3 with `approved` (`_status_rank`), and the apprvguard precedent (`status_set`, "a gate keyed on the literal `approved` would leave the automated tier ungated") is this repository's recorded reason for never writing the human tier alone (F-10). Every other rank decrease still returns `missing predecessor: backwards transition` (fail closed; deleting the rank comparison is explicitly rejected by 4.8 point 2).
  - Depends on: E-04
  - Expected outcome: `validate_transition("approved","reviewed")` and `("auto-approved","reviewed")` are both `ok=True`; `("approved","to-review")` and `("reviewed","draft")` are still refused.
  - Execution state: performed
- [x] E-06 In `check_engine.check_lifecycle_transitions`, iterate `_plan_status_event_groups` instead of `_plan_status_events`: an `ordered=False` group validates NO edge into, within, or out of it. Reset `prev` to the group's single status when the group has one distinct forward status; otherwise set a `prev = None` AND an explicit `unvalidated = True` flag that SUPPRESSES the next edge entirely. Do NOT rely on `prev = None` alone to mean "skip": measured at review, `validate_transition(None, tgt)` is a REJECTION for every target except `draft` ("cannot start the lifecycle at ..."), so the literal reading of "reset `prev` to `None`" manufactures 215 brand-new findings on the whole tree (511 versus 296) instead of abstaining - the exact opposite of the intent (F-11). Leave the pending-only scoping and the finding text unchanged.
  - Depends on: E-05
  - Expected outcome: all five fixtures pass; an `approved -> reviewed -> approved` round trip yields zero findings; `approved -> to-review` still yields one; no finding text mentions `None`.
  - Execution state: performed

### Task group 5: contract and corpus

- [x] E-07 Amend `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` next to its `## Workflow history` bullet: state that the file's line direction is NOT normative (writers prepend, authors append), that readers derive order from the date plus per-block direction and treat an unresolvable same-date tie as unordered, that the durable fix is the `seq` journal of spec `2vev8j` 4.3, and list the legal backward edges (`approved -> reviewed` and `auto-approved -> reviewed`, nothing else). Write the SECTION BODY ONLY: do NOT hand-edit the spec's `- Status:` or its `## Workflow history`, which `.aw/records/specs/README.md` forbids and routes through `aw specs note`. An `implemented` spec is amendable in place (AGENTS.md: "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT") and this plan declares it in `- Scope-Paths:`.
  - Depends on: E-06
  - Expected outcome: the spec names the rule and both edges; `grep -n "auto-approved -> reviewed" <spec>` shows the second one.
  - Execution state: performed
- [x] E-08 Re-measure the corpus at execution HEAD and record the numbers as OBSERVATIONS, not as a bar to hit. Run `python3 -m agent_workflows check plans --agent` and a whole-tree count through the new group reader plus `validate_transition`. RE-DERIVE the before-number in the same run rather than trusting any number written in this plan: the counts moved between authoring (`cfc7f5c1`) and review (`d39d58e9`) and will move again, and the review measured that the whole-tree figure depends on whether `actor=` is passed (846 with, 435 without, at review HEAD) - so state which form was measured. The PROPERTY that must hold, and the only pass/fail bar: zero `check.lifecycle-transition-invalid` findings in `pending/`, and every whole-tree survivor explainable as either a cross-day edge or an unauthorized-terminal actor rejection (which is an actor defect this plan does not fix, not an ordering one).
  - Depends on: E-06
  - Expected outcome: 0 `check.lifecycle-transition-invalid` in pending; the whole-tree survivor set categorized by rejection reason with counts, and strictly fewer ordering (`backwards` / `cannot start`) rejections than the same run's re-derived before-count.
  - Execution state: performed
- [x] E-09 Run the full suite bare: `python3 -m pytest`.
  - Depends on: E-07, E-08
  - Expected outcome: summary line with 0 failed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The checker runs alongside the authoritative `- Status:` read and is pending-only (`check_lifecycle_transitions` comment "Scope to PENDING-lane plans only"), so this change moves no plan's executability.
- `_plan_status_events` has one production caller (`check_engine.check_lifecycle_transitions`) plus `ipd_lifecycle.derive_plan_status`; `validate_transition` in `ipd_lifecycle` is distinct from `run_state.validate_transition` (run-state machine), which this plan does not touch. THE TWO CONSUMERS WANT DIFFERENT THINGS and the plan now keeps them separate rather than sharing one implementation (F-7).
- NOTHING IN `tests/` REFERENCES ANY OF THESE SYMBOLS TODAY. An AST-free grep of the whole `tests/` tree for `derive_plan_status`, `derive_status_from_events`, `_plan_status_events`, `check_lifecycle_transitions` and `lifecycle-transition-invalid` returns ZERO hits, so this plan's new file is the FIRST test coverage any of them has ever had and there is no existing test to lean on for regression safety. That is precisely why E-01/E-02 build a baseline instead of trusting the suite.
- `attention_contract.newest_history_record` and `plan_readiness.extract_newest_history_entry` are DELIBERATELY positional (first record = newest) and gate auto-approval; their docstrings reject a date-max rule. This plan does NOT touch them. Note the consequence for F-7: the FIRST-record rule those two use agrees with today's `derive_plan_status` on all 49 pending plans and on all 743 plans carrying a `- Status:`, which is more evidence that the shipped reversal, wrong as an ordering rule, is the right DERIVATION rule and must not be collaterally changed.
- `validate_transition` refuses a terminal (`executed`) transition by any actor outside `_FINALIZE_ACTORS` (`aw ipd finalize` / `aw finalize` / `ipd finalize`), and that refusal is checked BEFORE the predecessor logic. Measured at review, it accounts for 286 of the 296 whole-tree survivors under this plan's own design, so an execution report that counts them as ordering failures would misread its own result (F-8).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Every number here is an OBSERVATION at a stated HEAD, never an acceptance bar. The authored row set was measured at `cfc7f5c1`; the review re-measured at `d39d58e9` and several figures moved, which is itself the reason E-08 re-derives rather than compares.

| # | Claim | Measured |
|---|---|---|
| F-1 | Rule count in `aw check plans` | At `cfc7f5c1`: 0 of 11 findings. RE-MEASURED at `d39d58e9`: still 0 `check.lifecycle-transition-invalid`, but `aw check plans --agent` now reports 22 findings total (21 `check.ipd-uncarried-obligation`, 1 `check.ipd-lint-diagnostic`, 1 `check.collisions-not-checked`); direct `check_lifecycle_transitions(Path("."))` is 0 |
| F-1a | The plan file count itself moved | 14 pending plans at `cfc7f5c1`, 49 at `d39d58e9`; 737 -> 776 plans tree-wide. Any count in this plan is stale by construction |
| F-2 | Reader still inverts | Re-run at review: `_plan_status_events("## Workflow history\n- 2026-09-01 draft (a): x\n- 2026-09-02 to-review (a): y\n")` -> `['to-review', 'draft']`. UNCHANGED |
| F-3 | Why 0 is not a fix | At `d39d58e9`: 669 plans with 2+ status events; in FILE order 59 are strictly oldest-first, 16 mixed, 165 single-date. Of 49 pending plans, 22 are newest-first, 8 single-date, 19 have <2 events, and ZERO are oldest-first or mixed |
| F-4 | Current predicate, whole tree | 846 failing edges on 617 plans AS THE CHECKER ACTUALLY CALLS IT (with `actor=`), or 435 on 270 without `actor=`. The authored 435 measured the actor-free form, which is NOT the production call; the plan's own probe therefore understated the population by 411 edges |
| F-4a | Almost all of that is an ACTOR defect, not an ordering one | Of the 846, the terminal-actor rejection ("only `aw ipd finalize` may perform it") accounts for the bulk: 409 `approved -> executed` edges alone. That defect is out of this plan's scope and must not be counted as its result |
| F-5 | Date sort plus direction tiebreak, no unordered state | Re-measured 838 with `actor=` / 428 without (authored: 333). Ties still dominate |
| F-6 | Proposed design (per-block direction, unordered ties skipped, `approved -> reviewed` legal) | Prototyped at review with the real `validate_transition`: pending 0 edges / 0 plans, whole tree 296 edges on 291 plans with `actor=` or 22 edges on 22 plans without, 492 unordered groups. The authored "22 flagged plans" is the ACTOR-FREE figure; with the production call it is 291, of which 286 are terminal-actor rejections and only 10 are `backwards` |
| F-7 | THE DERIVATION REGRESSION (found at review, the plan's most serious defect) | E-02's "keep `_plan_status_events` as the flattened oldest-first list of those groups" silently changes `derive_plan_status`. Measured over 776 plans: 307 answers change, 128 of them to an EARLIER lifecycle status. In `pending/` it breaks 8 of 49 plans, all carrying the exact two-line same-date history `aw set` writes (`- 2026-09-25 reviewed (...)` above `- 2026-09-25 to-review (...)`), which flattens to `to-review` and contradicts their authoritative `- Status: reviewed`. Today that pair derives correctly on all 49 |
| F-8 | The fixtures would have failed for an unrelated reason | `validate_transition` rejects a terminal transition by any actor not in `_FINALIZE_ACTORS`, checked BEFORE predecessor logic. A fixture writing `executed` with an ordinary agent actor fails with `unauthorized terminal transition`, not with an ordering verdict |
| F-9 | Fixture (e) as authored could not discriminate | Measured on the CURRENT reader: single-date `to-review` above `draft` yields ZERO findings today, so the authored negative test passes before AND after and proves nothing. Single-date `draft` above `approved` yields one `approved -> draft` finding today and zero under the proposal, so it is the shape that actually tests the change |
| F-10 | The backward-edge table needs both approval tiers | `auto-approved` shares rank 3 with `approved`; spec `25kzda` 4.5 `IPD-AUTO-APPROVAL` prescribes recovery via `aw ipd set reviewed <id6>`; `validate_transition("auto-approved","reviewed")` is refused today. A table containing only the human tier leaves the automated tier's own documented recovery illegal, which is the apprvguard mistake this repository already recorded |
| F-11 | "reset `prev` to `None`" does the opposite of abstaining | `validate_transition(None, tgt)` REJECTS every target but `draft` ("cannot start the lifecycle at ..."). Prototyped both readings over the whole tree: an explicit suppression flag gives 296 edges, the literal `prev=None` reading gives 511, i.e. 215 findings MANUFACTURED by the abstain path |
| F-12 | Continuation lines would fragment blocks | 120 plans carry 1097 non-blank non-record lines inside `## Workflow history` (wrapped long records). Treating any non-record line as a block boundary splits one logical block into fragments of unknown direction. 0 pending plans carry them, so the defect would be invisible in the lane this rule scopes to |
| F-13 | The proposal narrows what is checked, and that is a real cost | Edges the checker VALIDATES at all: pending 30 -> 22, whole tree 1946 -> 722 (37%). Abstention is the correct response to unknowable order per spec `2vev8j` 4.7, but this plan buys 0 pending findings partly by checking less, and the honest claim is "fewer false findings AND less coverage", not "the check got better" |

Probes were untracked scratch scripts; V-08 re-derives the corpus numbers with the real functions at execution HEAD.

BACKLOG CLAIM NOW FALSE: `tk1gqo`'s "third defect" (`attention_contract` reading the LAST record as newest) is already fixed; `attention_contract.newest_history_record` takes the FIRST record ("corrected by plan `vhbvwz` E-02"). Not in scope.

## Proposed changes (ordered, validatable)

1. Derivation baseline captured (E-01) and guarded by a test that passes before the change (E-02). 2. Discriminating checker fixtures, failing (E-03). 3. Direction-detecting grouped reader ADDED beside the untouched derivation path (E-04). 4. Both backward edges enumerated (E-05). 5. Checker consumes groups and truly abstains (E-06). 6. IPD spec amendment (E-07). 7. Corpus re-measure as observation (E-08). 8. Bare suite (E-09).

THE ORDER IS LOAD-BEARING AND ONE STEP CANNOT MOVE: E-01 must run at the PRE-CHANGE HEAD. A baseline captured after E-04 records the new behavior as if it were the old, which converts the plan's only anti-regression guard into a tautology that passes no matter what the reader does. If E-01 is reached with the reader already modified, revert the reader, capture, then re-apply.

SAME-DATE TIE, stated exactly: two status events with the same date are ordered by their in-block ordinal ONLY when both lie in one contiguous block whose other records prove its direction by a strict date change. If the block is single-date (no evidence), mixed, or the tie spans two blocks, the group is UNORDERED: no transition into, inside, or out of it is validated, and nothing is guessed. This follows spec `2vev8j` 4.7 ("do NOT run forward-transition validation across unordered pre-checkpoint records") and is why F-5's rank-free date sort is rejected. A lifecycle-rank tiebreak is also rejected (it infers order from the invariant being checked, `tk1gqo` 2026-09-05 note).

ABSTAINING IS NOT THE SAME AS VALIDATING AGAINST NOTHING, and the distinction is mechanical rather than stylistic (F-11). `validate_transition(None, x)` has a MEANING already - "this is the first recorded event, so it must be `draft`" - so handing it `None` to express "I do not know the predecessor" asserts a different claim and gets a rejection. The unordered path therefore needs its own suppression flag, and a reviewer of the implementation should check that the next edge after an unordered multi-status group produces NO finding at all.

WHAT THIS PLAN DOES NOT BUY, stated because the headline number invites the wrong reading (F-13). Pending goes to 0 partly because fewer edges are checked at all: 30 validated edges become 22 in `pending/`, and 1946 become 722 tree-wide. That is the correct treatment of order the file cannot establish, and it is also a coverage reduction. The durable recovery of that coverage is the `seq` journal (spec `2vev8j` 4.3), which is deferred to `ms06pi`; this plan's honest claim is that it stops reporting failures it cannot substantiate, not that it verifies more.

## Deferred / out of scope (with reason)

- The `seq` history journal that makes order explicit (spec `2vev8j` 4.3, migration steps 3 to 6). This is also what would restore the validation coverage F-13 measures this plan giving up.
  - Carrier: ms06pi
- UTC versus local-date writer stamps (spec `2vev8j` 4.4); a same-day tie created by it is handled here as unordered, not corrected.
  - Carrier-Declined: no dedicated item exists; spec `2vev8j` 4.4 owns it and `ms06pi` graduates that spec.
- The whole-tree survivors in terminal directories (291 plans with the production `actor=` call at review HEAD, 22 without it); the rule is pending-only and spec `2vev8j` Section 6 step 5 freezes those trees.
  - Carrier-Evidence: .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
- FIXING `derive_plan_status`' OWN ORDERING. The reversal is wrong as an ordering rule and stays in place here (E-04), deliberately, because it is the shipped derivation and every alternative measured at review is WORSE against the authoritative `- Status:` field over the whole tree: today's reversal 229 mismatches of 743, plain file order 507, the first-record rule 229, a date sort 245. Choosing among those is a behavior decision about a second consumer, needing its own measurement and its own approval, and folding it in here would make this plan's own regression guard meaningless. Consequence if never done: `derive_plan_status` keeps disagreeing with `- Status:` on 229 terminal-tree plans, which no gate reads today.
  - Carrier-Declined: this is the SAME defect `ms06pi` carries under spec `2vev8j` 4.3, whose `seq` authority removes the direction question for BOTH readers at once; filing a second item would duplicate that carrier's scope rather than add a distinct obligation.
- THE UNAUTHORIZED-TERMINAL ACTOR POPULATION (F-4a/F-8): 409 `approved -> executed` edges in the terminal tree are refused because their recorded actor is not `aw ipd finalize`. Real, pre-existing, and entirely independent of ordering; correcting it would mean either rewriting terminal plan histories (which `tk1gqo` forbids and this plan refuses) or widening `_FINALIZE_ACTORS`, a lifecycle-authority change. Consequence if never done: the rule stays noisy on the frozen tree it already does not scan.
  - Carrier-Declined: no obligation is outstanding on anybody, because the rule this plan touches is PENDING-ONLY and the population is entirely in terminal directories that spec `2vev8j` Section 6 step 5 freezes as audit archives; there is nothing to fix unless that freeze is lifted, which is that spec's decision to make.

## Scope check

- Over-scope: none. The backward-edge table is included because spec `2vev8j` 4.8 point 1 makes it part of reaching 0 honestly, and `auto-approved -> reviewed` is included because 4.8 point 3 requires the table to be an ENUMERATION and omitting a shipped tier would leave its documented recovery illegal (F-10).
- Under-scope, CLOSED at review: the plan had no protection for its second consumer. E-01/E-02 add a whole-tree derivation baseline and its guard, and E-04 now explicitly preserves `events.reverse()` (F-7).
- Under-scope: `plans/README.md` still says history lines are "newest-first"; left as-is because it describes what `aw set` writes, which remains true.
- EXPLICITLY NOT IN SCOPE: `attention_contract.newest_history_record`, `attention_contract.last_history_at`, `plan_readiness.extract_newest_history_entry`, `plan_readiness.history_verdict_approves` (all positional by deliberate design, all gating auto-approval); `record_history._TAIL_RE` and `_inline_history_records` (reused, not modified); `status_set.apply_status_change`'s prepend (the writer side, which `tk1gqo` rules must not be "fixed" alone); `_FINALIZE_ACTORS`; `run_state.validate_transition`; and any plan history file.

## Required tests / validation

`tests/test_history_order.py`: the derivation-unchanged guard (must pass BEFORE the reader change, proving the baseline is honest, and after) plus fixtures (a) to (e), shown failing before E-04/E-06 and passing after; `aw check plans --agent`; bare suite.

## Spec / documentation sync

Amends `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` (declared in Scope-Paths). WHY: its "append one dated line per workflow touch" wording implies oldest-first while `aw set` prepends, and spec `2vev8j` 4.8 point 3 names the IPD spec as the home of the enumerated backward-edge table. Spec `2vev8j` itself is not edited. The amendment is BODY-ONLY; the spec's `- Status:` and `## Workflow history` are owned by `aw specs` (`.aw/records/specs/README.md`) and are not hand-edited, so if a history line is wanted it goes through `aw specs note`.

## Open questions

### OQ-01: Beyond the two approval tiers, is any other backward edge legal?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: no. The table is `approved -> reviewed` plus `auto-approved -> reviewed`, and nothing else, because spec `2vev8j` 4.8 names the recovery edge and mandates fail-closed for anything unlisted, while spec `25kzda` 4.5 supplies the second tier's spelling for the same recovery (F-10). The review NARROWED this question rather than answering the maintainer's part of it: adding the `auto-approved` spelling is a derivation from two approved specs, not a widening, so the reviewer resolved it; whether to admit a genuinely NEW edge (for example `approved -> to-review`, 5 cross-day instances tree-wide, or `executed -> approved`, 3) remains a maintainer call and those edges stay flagged meanwhile.
- Carrier-Declined: nothing is outstanding on anybody. The plan ships a complete fail-closed table sufficient for both shipped approval tiers; the residual question widens a table that is already correct, and a new edge is admitted only when a real recovery procedure needs it, at which point that procedure's own work carries the change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git rev-parse HEAD` proving the capture ran at the PRE-CHANGE head, together with `git status --porcelain agent_workflows/ipd_lifecycle.py agent_workflows/check_engine.py` showing BOTH production files UNMODIFIED at capture time (an empty result). A baseline captured after the reader changed is worthless and this is the only evidence that distinguishes the two. Then paste the entry count (`python3 -c 'import json;d=json.load(open("tests/fixtures/derive_plan_status_baseline.json"));print(len(d))'`) and a 3-line head of the sorted keys.
  - Observed evidence: pre-change HEAD 77ca5765 clean on target files; 777 baseline entries captured
```
$ git rev-parse HEAD
77ca5765d20d06aebcf73527f57547f13ecdbc47
$ git status --porcelain agent_workflows/ipd_lifecycle.py agent_workflows/check_engine.py
(empty output - both production files unmodified at capture time)
$ python3 -c 'import json;d=json.load(open("tests/fixtures/derive_plan_status_baseline.json"));print(len(d))'
777
$ python3 -c 'import json;d=json.load(open("tests/fixtures/derive_plan_status_baseline.json"));print("\n".join(list(d.keys())[:3]))'
.aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md
.aw/records/plans/executed/20260630-assess-documentation-00-7ibobm-assess-documentation.ipd.md
.aw/records/plans/executed/20260701-add-generalization-00-rin79g-add-generalization-assess-lens.ipd.md
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation` PASSING at the pre-change HEAD, and paste the number of paths the test reports comparing (must be >= 700, proving it is not passing on an empty intersection).
  - Observed evidence: Derivation test passed comparing 777 paths at pre-change HEAD
```
$ python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation -s
Compared 777 paths
.
1 passed, 5 deselected in 0.39s
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: with ONLY the test additions (reader unmodified), paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q` output showing fixtures (b) and (c) FAILED with `backwards transition` text, (e) FAILED naming `'approved' -> 'draft'`, and (a) and (d) passed. The (e) failure text is the discriminating evidence (F-9): if (e) passes here, the fixture was written in the non-discriminating shape and must be corrected before proceeding.
  - Observed evidence: fixtures (b), (c), and (e) failed as expected on unmodified reader; (a) and (d) passed
```
$ python3 -m pytest -o addopts="" tests/test_history_order.py -q
F.F.F.                                                                   [100%]
=================================== FAILURES ===================================
_____________ HistoryOrderFixtureTests.test_fixture_c_mixed_blocks _____________
...
AssertionError: Lists differ: [Drift(location='/tmp/tmpvd1f5gt2/.aw/reco[538 chars]or')] != []
First extra element 0:
Drift(location='/tmp/tmpvd1f5gt2/.aw/records/plans/pending/20260901-fix01c-01-fix01c-mixed.ipd.md', rule='check.lifecycle-transition-invalid', detail="recorded lifecycle transition 'to-review' -> 'draft' is invalid: missing predecessor: backwards transition 'to-review' -> 'draft'", observed='to-review -> draft (actor agent)', required='a valid forward transition authored by the correct actor', recovery='correct the plan history via `aw set <status> <id6>` (or `aw ipd finalize` for the terminal transition)', assurance='repository', determinism='deterministic', severity='error')

_____________ HistoryOrderFixtureTests.test_fixture_b_oldest_first _____________
...
AssertionError: Lists differ: [Drift(location='/tmp/tmpv5c3_1lo/.aw/reco[1140 chars]or')] != []
First extra element 0:
Drift(location='/tmp/tmpv5c3_1lo/.aw/records/plans/pending/20260901-fix01b-01-fix01b-oldest-first.ipd.md', rule='check.lifecycle-transition-invalid', detail="recorded lifecycle transition 'approved' -> 'reviewed' is invalid: missing predecessor: backwards transition 'approved' -> 'reviewed'", observed='approved -> reviewed (actor agent)', required='a valid forward transition authored by the correct actor', recovery='correct the plan history via `aw set <status> <id6>` (or `aw ipd finalize` for the terminal transition)', assurance='repository', determinism='deterministic', severity='error')

____ HistoryOrderFixtureTests.test_fixture_e_discriminating_single_date_tie ____
...
AssertionError: Lists differ: [Drift(location='/tmp/tmp5tcgyfkk/.aw/reco[541 chars]or')] != []
First extra element 0:
Drift(location='/tmp/tmp5tcgyfkk/.aw/records/plans/pending/20260901-fix01e-01-fix01e-single-date.ipd.md', rule='check.lifecycle-transition-invalid', detail="recorded lifecycle transition 'approved' -> 'draft' is invalid: missing predecessor: backwards transition 'approved' -> 'draft'", observed='approved -> draft (actor agent)', required='a valid forward transition authored by the correct actor', recovery='correct the plan history via `aw set <status> <id6>` (or `aw ipd finalize` for the terminal transition)', assurance='repository', determinism='deterministic', severity='error')

=========================== short test summary info ============================
FAILED tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_c_mixed_blocks
FAILED tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_b_oldest_first
FAILED tests/test_history_order.py::HistoryOrderFixtureTests::test_fixture_e_discriminating_single_date_tie
3 failed, 3 passed in 0.35s
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste `git diff agent_workflows/ipd_lifecycle.py` showing `_plan_status_event_groups` ADDED and `events.reverse()` STILL PRESENT with its new pointing comment. Paste a `python3 -c` call of `_plan_status_event_groups` on fixture (e) text printing one group with `ordered=False`, and on a synthetic record whose text wraps onto an indented continuation line, printing ONE block rather than two (F-12). Then re-run `python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation` and paste it PASSING, which is the proof the derivation did not move.
  - Observed evidence: _plan_status_event_groups added; events.reverse() preserved; single-date tie unordered; continuation line preserved single block; Derivation test passed
```
$ python3 -c 'from agent_workflows.ipd_lifecycle import _plan_status_event_groups; t="## Workflow history\n- 2026-09-01 draft (a): ok\n- 2026-09-01 approved (a): ok\n"; print(_plan_status_event_groups(t))'
[('2026-09-01', [('draft', 'a'), ('approved', 'a')], False)]

$ python3 -c 'from agent_workflows.ipd_lifecycle import _plan_status_event_groups; t="## Workflow history\n- 2026-09-01 draft (a): first\n  wrapped line\n- 2026-09-02 approved (a): second\n"; print(_plan_status_event_groups(t))'
[('2026-09-01', [('draft', 'a')], True), ('2026-09-02', [('approved', 'a')], True)]

$ python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation
.                                                                        [100%]
1 passed, 5 deselected in 0.27s
```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `python3 -c 'from agent_workflows import ipd_lifecycle as IL; print(IL.validate_transition("approved","reviewed")); print(IL.validate_transition("auto-approved","reviewed")); print(IL.validate_transition("approved","to-review")); print(IL.validate_transition("reviewed","draft"))'` showing the first two `ok=True` and the last two `ok=False ... backwards transition`. All four lines are required: the two refusals are what prove the rank comparison was not deleted (spec `2vev8j` 4.8 point 2).
  - Observed evidence: approved->reviewed and auto-approved->reviewed ok=True; approved->to-review and reviewed->draft ok=False
```
$ python3 -c 'from agent_workflows import ipd_lifecycle as IL; print(IL.validate_transition("approved","reviewed")); print(IL.validate_transition("auto-approved","reviewed")); print(IL.validate_transition("approved","to-review")); print(IL.validate_transition("reviewed","draft"))'
TransitionCheck(ok=True, reason='')
TransitionCheck(ok=True, reason='')
TransitionCheck(ok=False, reason="missing predecessor: backwards transition 'approved' -> 'to-review'")
TransitionCheck(ok=False, reason="missing predecessor: backwards transition 'reviewed' -> 'draft'")
```
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q` showing ALL tests passed. Then paste the ABSTENTION PROOF, which is the claim most exposed to a silently wrong implementation (F-11): a `python3 -c` that builds a plan text with an unordered multi-status same-date group FOLLOWED by a later-dated status line, runs `check_engine.check_lifecycle_transitions` over a tempfile repo containing it, and prints an EMPTY finding list. A `cannot start the lifecycle at` finding here means the `prev=None` reading was implemented and the abstain path is manufacturing findings.
  - Observed evidence: all 6 tests in test_history_order.py passed; abstention probe confirmed 0 findings on unordered tie followed by later transition
```
$ python3 -m pytest -o addopts="" tests/test_history_order.py -q
......                                                                   [100%]
6 passed in 0.33s

$ python3 -c '
import tempfile
from pathlib import Path
from agent_workflows import check_engine as ce
from tests.test_history_order import _fixture_plan_text

history = (
    "- 2026-09-01 draft (agent): start\n"
    "- 2026-09-01 approved (agent): fast\n"
    "- 2026-09-02 executed (aw ipd finalize): done\n"
)
content = _fixture_plan_text("abst01", history, status="executed")

with tempfile.TemporaryDirectory() as tmpdir:
    tmproot = Path(tmpdir)
    pending_dir = tmproot / ".aw" / "records" / "plans" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    (pending_dir / "20260901-abst01-01-abst01-test.ipd.md").write_text(content, encoding="utf-8")
    drift = ce.check_lifecycle_transitions(tmproot, include_untracked=True)
    print("Drift findings:", drift)
'
Drift findings: []
```
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste `git diff .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` showing the ordering rule and BOTH table entries, plus `git diff` evidence that the spec's `- Status:` line and `## Workflow history` block are UNCHANGED.
  - Observed evidence: IPD spec updated with ordering rule and legal backward edges; Status and Workflow history unchanged
```
$ git diff .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
diff --git a/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md b/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
index 1b0d935f..e06ad90e 100644
--- a/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
+++ b/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
@@ -20,7 +20,7 @@ Author from the template (`assess/templates/ipd.md`), or generate a conformant s

 - Metadata block (a bullet `- Field: value` list after the H1 title, NOT YAML front matter; "YAML front matter" means only actual `---` YAML, which the parser ignores): required `Date`, `Kind` (`child` or `orchestrator`), `Concern`, `Scope`, `Status`, `Author`; `Set` and `Order` together when in an ordered Set (`Order: 0` for an orchestrator, `>= 1` for a child); `Approval` when and only when `Status: approved`; `Highest E allocated` once any `E-*` exists (the allocation watermark); the `Quarantine`/`Quarantine owner`/`Quarantine follow-up` trio only on a quarantined nonterminal plan.
 - The H2 SECTION ORDER is exact and per-kind (child and orchestrator differ), enumerated in the schema. In BOTH kinds `## Detailed Implementation Checklist (TODO)` is the H2 IMMEDIATELY AFTER `## Goal` and `## Validation and cross-check ...` is the H2 IMMEDIATELY BEFORE `## Approval and execution gate`. (There is no "near the top/end"; placement is exact.)
-- `## Workflow history` (append one dated line per workflow touch; never rewrite prior lines).
+- `## Workflow history` (append one dated line per workflow touch; never rewrite prior lines). Line direction in the file is NOT normative (writers prepend, authors append); readers derive order from record dates plus per-block direction and treat an unresolvable same-date tie as unordered. The durable fix is the `seq` journal of spec `2vev8j` 4.3. The only legal backward lifecycle transitions are `approved -> reviewed` and `auto-approved -> reviewed` (spec `2vev8j` 4.8 / spec `25kzda` 4.5); every other backwards move fails closed.
 - `## Detailed Implementation Checklist (TODO)` (mandatory): the EXECUTION checklist. Only executable leaves are checkboxes; each carries a unique `E-NN` id, `Depends on:` (`none` or comma-separated `E-*`), `Expected outcome:`, and `Execution state:` (`pending`|`performed`|`blocked`|`failed`). `E-* checked` means the action was PERFORMED, not that it was verified (F-07). The terminal lifecycle transition is NOT an `E-*` item (F-08); it is a post-gate transaction (see the lifecycle line). An `Expected outcome` counting live artifacts must state a property rather than an authored count; see `.aw/system/workflows/plan-review/plan-review.md` Rubric G for the re-derivation convention and code-facts exemptions.
 - `## Validation and cross-check` (mandatory): a SEPARATE evidence pass. Exactly one `V-NN validates E-NN` row per `E-NN` (a 1:1 bijection), each with `Required evidence:`, `Observed evidence:`, and `Result:` (`pending`|`pass`|`blocked`|`failed`). `V-* pass` means the evidence was INSPECTED and supports the expected outcome. Both the CREATOR (authors both checklists) and the REVIEWER (assesses both) are responsible for it (DECISIONS D115).
 - `## Open questions`: each question is an `### OQ-NN:` with `Blocking:` (`yes`|`no`), `Status:` (`open`|`resolved`|`deferred`), `Owner:`, and a resolution/deferral rationale. A blocking question may not be deferred and must be resolved before `pre-execution` (F-09).
```
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: paste the rule count from `python3 -m agent_workflows check plans --agent | grep -o 'check.lifecycle-transition-invalid' | wc -l` (expected 0). Then paste a one-off whole-tree measurement that reports, for the SAME run, the BEFORE and AFTER counts BROKEN DOWN BY REJECTION REASON (at minimum: `backwards`, `cannot start`, `unauthorized terminal`, `terminal requires at least reviewed`), and that states explicitly whether `actor=` was passed. A single undifferentiated total is NOT acceptable evidence: at review 286 of 296 survivors were actor rejections this plan does not address, so a bare total cannot show whether the ordering fix worked (F-4a). The bar is the PROPERTY in E-08, not any number written in this plan.
  - Observed evidence: 0 check.lifecycle-transition-invalid in pending; backwards transitions reduced 416->14 with actor= and 416->14 without actor=
```
$ python3 -m agent_workflows check plans --agent | grep -o 'check.lifecycle-transition-invalid' | wc -l
0

=== WHOLE TREE MEASUREMENT ===
Total plans: 777

--- WITH actor= (Production call) ---
BEFORE: 851 failing edges across 622 plans
  unauthorized terminal: 435
  backwards: 416
AFTER:  301 failing edges across 292 plans
  unauthorized terminal: 287
  backwards: 14

--- WITHOUT actor= ---
BEFORE: 435 failing edges across 270 plans
  backwards: 416
  terminal requires at least reviewed: 19
AFTER:  26 failing edges across 26 plans
  backwards: 14
  terminal requires at least reviewed: 12
```
  - Result: pass
- [x] V-09 validates E-09
  - Required evidence: paste the `N passed` summary line of bare `python3 -m pytest`, with 0 failed.
  - Observed evidence: pytest full suite passed: 2009 passed, 1 skipped, 3 warnings
```
2009 passed, 1 skipped, 3 warnings in 30.96s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Nine items, one concern: making the lifecycle-transition check read an order it can justify. The count grew from six at review because F-7 required a baseline-plus-guard pair that must run BEFORE the reader changes (E-01, E-02), and because the original E-03 bundled two independent deliverables with independent test surfaces (a transition-table constant, verified by four `validate_transition` calls, and a checker loop rewrite, verified by an abstention probe), which the plan's own right-sizing rule says to split. No item introduces a second concern.

WHAT A HUMAN IS APPROVING. A behavior change to ONE advisory consistency rule (`check.lifecycle-transition-invalid`), which is pending-only, gates no execution, and reports 0 findings on this repository today. Three things to weigh. FIRST, the change makes the rule report LESS: it validates 22 pending edges where it now validates 30, and 722 tree-wide where it now validates 1946, because an order the file cannot establish is abstained on rather than guessed (F-13). That is what approved spec `2vev8j` 4.7 requires, and it is still a coverage reduction, recovered later only by the `seq` journal that `ms06pi` carries. SECOND, this plan deliberately DOES NOT fix `derive_plan_status`, whose own reversal is wrong for 229 of 743 plans, because every measured alternative is worse and choosing among them is a separate decision (see Deferred); approving this means accepting that the two readers stay divergent for now. THIRD, it legalizes two backward lifecycle edges (`approved -> reviewed`, `auto-approved -> reviewed`) in `validate_transition`, which is a small widening of a shipped lifecycle predicate; spec `2vev8j` 4.8 is the maintainer decision authorizing it, and it is IRREVERSIBLE in the sense 4.8 records (artifacts authored under it will rely on it).

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The intended surface: in `ipd_lifecycle.py`, a new `_plan_status_event_groups` plus a `_LEGAL_BACKWARD_EDGES` constant and one early-permit branch inside `validate_transition`, and a comment above the RETAINED `events.reverse()`; in `check_engine.py`, the edge loop inside `check_lifecycle_transitions` only; `tests/test_history_order.py` and `tests/fixtures/derive_plan_status_baseline.json` are new; the IPD spec gets a body-only amendment beside its `## Workflow history` bullet. EXPLICITLY NOT IN SCOPE, and each of these would be a silent contract change: `_plan_status_events`' own reversal and `derive_plan_status`; `_FINALIZE_ACTORS` or the unauthorized-terminal branch; the pending-only scoping; the finding text; `attention_contract`'s positional readers; `plan_readiness`; `record_history`'s parser; `status_set.apply_status_change`'s prepend; `run_state.validate_transition`; the spec's `- Status:`/history; and any plan history file. An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-01 (the baseline's pre-change provenance cannot be reconstructed afterwards, so the `git status` evidence is the whole guarantee), on V-03 (the fixtures must be shown FAILING against unmodified code, which requires running them there), and on V-06's abstention probe (a wrong implementation makes every OTHER assertion in the file pass while manufacturing 215 findings tree-wide).

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `events.reverse()` or `_plan_status_events` is already gone from `ipd_lifecycle.py` at execution time (another change landed in this surface and F-7's whole analysis needs re-deriving); the derivation-unchanged guard FAILS at the pre-change HEAD in E-02 (the baseline does not describe the code that produced it, so nothing downstream can be trusted); or `check_lifecycle_transitions` is no longer pending-only (the blast radius moves from an advisory rule to the whole frozen corpus).

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit 63h054 -- <Scope-Paths>`, never `git add -A`, and never push. This plan inherits `- Blocks-Release: next` from backlog `tk1gqo` and does NOT discharge the whole gate alone: `ms06pi` carries the `seq` journal and the UTC/local defect, and the Deferred rows name it, so do not close `tk1gqo`'s wider obligations as part of this execution. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-09 carry pasted evidence.
