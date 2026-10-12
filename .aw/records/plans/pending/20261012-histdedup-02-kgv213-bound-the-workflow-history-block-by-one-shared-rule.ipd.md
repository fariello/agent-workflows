# IPD: Bound the Workflow history block by one shared rule

- Date: 2026-10-12
- Kind: child
- Concern: Two readers partition a record's `## Workflow history` by DIFFERENT rules. `backlog._prior_history_records` ends the block at the first non-blank line that is not a column-zero `- ` bullet and so ignores an INDENTED history-shaped line (its docstring cites the measured `tk1gqo` incident that rule fixes). `attention._history_section_lines` bounds only at the next `## ` heading, and every consumer then matches `HISTORY_RECORD_RE` against `line.strip()`, so it DOES count an indented line. `status_set.same_status_message_is_duplicate` reads through the second reader, so on an item whose only history-shaped line is indented the predicate answers "duplicate" while `_prior_history_records` answers "no prior records". Re-measured in this lane at HEAD `5ebf5364d` (after Set `setdisp` reduced `backlog.run_set` to a thin adapter over `status_set.run_set_command`): with the history date pinned to the fixture's date, `aw backlog set <item> --status open --message "metadata only"` over the fixture below printed `unchanged`, wrote NO column-zero record, and left a block whose only content is the indented line, and `backlog.validate_item` returned `[]` on the result. So the disagreement is still live on the shared engine and the `evbx9s` E-04 fail-safe (which lived in the pre-`setdisp` `run_set`) no longer guards this path.
- Scope: IN: (a) ONE shared, pure history-block reader in `agent_workflows/attention_contract.py` (stdlib-only, already owns `HISTORY_RECORD_RE` and `newest_history_record`, imported by both sides with no cycle) that states the bounding rule once and returns the block's RECORDS, the restorable RECORD LINES (records plus their wrapped continuations) and the BODY that follows it; (b) migrate the predicate `status_set.same_status_message_is_duplicate`, the backlog history writer `backlog._prior_history_records` (plus its body twin `backlog._strip_metadata_and_history`) and the `close_on_answer` body reader `set_records._extract_body` onto it, so the dedup answer, the restorable prior records and the body boundary all come from one definition (the writer needs both halves of one partition, F-06); (c) behavioral tests for the rule and for the end-to-end `aw backlog set` outcome on the indented fixture under BOTH spellings; (d) one CHANGELOG entry. OUT, each with a reason under "Deferred": the read-only date/verdict consumers of `attention._history_section_lines` (owned by sibling `6iab2o`, which carries the blast radius the backlog item warns about); the empty-history-block validation backstop (owned by sibling `v5m5y8`); any rewrite of committed records; and plan history writers in `ipd_lifecycle`.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_history_block_bounding.py, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kgv213

## Workflow history
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` with siblings `v5m5y8` and `6iab2o`. The canonical rule (F-04) was chosen by measuring three candidates over all 2489 tracked artifacts carrying a history heading at HEAD `5ebf5364d`; the chosen rule changes zero consumer answers. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

State the `## Workflow history` bounding rule ONCE, as a shared reader, and make the same-status dedup predicate and the backlog writer's prior-record source both call it, so a suppressed same-status write can never be decided on a record the writer cannot restore. The rule is chosen to agree with today's answers on every tracked artifact and to differ only on the malformed shapes that caused the disagreement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the shared reader

- [ ] E-01 `agent_workflows/attention_contract.py`: add a pure function `history_block(text: str) -> HistoryBlock` (a `NamedTuple` with `records: List[str]`, `record_lines: List[str]` and `body: str`) implementing the F-04 rule exactly: locate the heading with `(?m)^## Workflow history[ \t]*$`; scan the following lines; the block ENDS at the next line starting `## `, or at the first non-blank line that starts at COLUMN ZERO and is not a `- ` bullet, or at an INDENTED non-blank line that does not directly continue a bullet (a blank line ends continuation, so a blank-separated indented quotation is NOT part of the block); a RECORD is a column-zero line inside the block matching `HISTORY_RECORD_RE` against `line.rstrip()` (never `strip()`), returned with trailing whitespace stripped, in file order (newest-first, unchanged positional semantics). `record_lines` is the flat, file-order list of every record line FOLLOWED BY its indented continuation lines (each `rstrip()`ed, indentation KEPT, blank lines dropped; a non-record bullet and its continuation are excluded), so `"\n".join(record_lines)` re-emits each record with its wrapped text and the block's lines are partitioned exactly between `record_lines`, dropped non-record bullets, blanks, and `body` (F-06). `body` is the remaining text from the terminating line on with LEADING BLANK LINES removed and trailing whitespace `rstrip()`ed, but the first line's indentation PRESERVED (never `.strip()`/`.lstrip()` the text: de-indenting a blank-separated indented quotation turns it into a column-zero record on the next rewrite, F-07); `""` when there is none. No heading yields `HistoryBlock([], [], "")`. Document the rule in the docstring with the F-01..F-07 measurements and the `tk1gqo` reason, and state that `newest_history_record(history_block(t).records)` is the canonical newest record.
  - Depends on: none
  - Expected outcome: `attention_contract.history_block` exists, is stdlib-only, and returns the records/record_lines/body triple described; `attention_contract` still imports nothing new from the package.
  - Execution state: pending

### Task group 2: migrate the two disagreeing readers

- [ ] E-02 `agent_workflows/backlog.py`: reimplement `_prior_history_records(text)` as `A.history_block(text).record_lines` (NOT `.records`: it is the RESTORABLE source `_reattach_history` re-emits, so it must carry a wrapped record's continuation lines, F-06; its `[0]` is still the newest record line, which `production_checks` BACKLOG-GRADUATE-LEGITIMACY clause 2 reads) and `_strip_metadata_and_history(text)` as `A.history_block(text).body`, keeping both names and signatures (`_prior_history_records` callers: `_reattach_history`, `production_checks` clause 2; `_strip_metadata_and_history` has no production caller today and is kept as the body twin). Update the `_prior_history_records` docstring to say the rule now lives in `attention_contract.history_block`, why it returns `record_lines`, and keep its `tk1gqo` paragraph. Do not change `_reattach_history`'s assembly.
  - Depends on: E-01
  - Expected outcome: both helpers delegate to the shared reader; their output is unchanged on every tracked backlog item (V-02 measures this; 0 differ was measured at review).
  - Execution state: pending

- [ ] E-06 `agent_workflows/set_records.py` (`_extract_body`): reimplement as `_ac.history_block(text).body` (`set_records` already imports `attention_contract as _ac` at module top), keeping the name and signature, and update its docstring to name the shared reader. This is REQUIRED, not cleanup: `close_on_answer` feeds `_extract_body` into `_render_item` and then `_reattach_history`, which re-emits `_prior_history_records`; if the body boundary and the prior-record boundary disagree, a wrapped record's following records are emitted TWICE (once as records, once inside the body), measured at review (F-06).
  - Depends on: E-01
  - Expected outcome: `_extract_body` delegates to the shared reader; on the tracked backlog corpus its output changes ONLY for the two `done/` items F-08 names (a quoted `## Workflow history` line that the old reader dropped is now kept in the body); neither is `blocked`, so `close_on_answer` cannot reach them.
  - Execution state: pending

- [ ] E-03 `agent_workflows/status_set.py` (`same_status_message_is_duplicate`): replace the `_att._history_section_lines(text)` + `strip()` input with `_ac.history_block(text).records`, keeping `_ac.newest_history_record` and the `_readiness._HISTORY_RECORD_PARTS_RE` parse unchanged. Update the docstring to name the shared reader and the reason (the predicate must judge against exactly the records the writer will preserve).
  - Depends on: E-01
  - Expected outcome: on the F-01 indented fixture the predicate returns False (no record to duplicate), so the shared engine writes the record; on every well-formed record its answer is unchanged.
  - Execution state: pending

### Task group 3: behavioral tests and changelog

- [ ] E-04 `tests/test_history_block_bounding.py` (new): behavioral tests calling the real functions and the real CLI, asserting outputs and written file contents only (P16; no source inspection). Cases: (a) well-formed multi-record block returns all records newest-first and the body; (b) the F-01 indented-only fixture returns `records == []`; (c) the `tk1gqo` shape (column-zero records, blank line, prose, indented quoted records) returns only the column-zero records; (d) a WRAPPED record (column-zero record followed directly by indented continuation lines, the plan shape F-03 measures) keeps the following column-zero records inside the block, and `record_lines` carries the continuation lines with their indentation; (e) a blank-separated indented quotation directly under the block is excluded from `records` and `record_lines`, and `body` starts with that line's indentation intact; (e2) writer round-trip, F-06/F-07: for the (d) wrapped fixture and the (e) quoted fixture, written as a `blocked` decision item, call `set_records.close_on_answer` and assert on the written file that every original record occurs EXACTLY ONCE, the wrapped continuation line is still directly under its record, and `history_block(text).records` equals the new `done` record followed by the original records (so the quoted line was NOT promoted to a record); (f) end to end: write the F-01 fixture with the indented line dated with `artifact_core.utc_history_date()` (NEVER a literal date, see F-05), run `cli.main(["backlog","set",<item>,"--status","open","--message","metadata only","--no-commit","--dir",<root>])` AND the positional spelling `["backlog","set","open",<item>,...]`, and assert for each that the file now carries a column-zero `same-status` record and `attention_contract.history_block(text).records` is non-empty; (g) the predicate and `backlog._prior_history_records` agree (predicate True implies prior records non-empty) over every fixture in this module; (h) the specs path: a spec fixture whose only history-shaped line is indented and dated `utc_history_date()`, `cli.main(["specs","note",<spec>,"--message",<m>])` with the same message now appends a column-zero `note` record (the predicate's other callers, `specs.run_note` and the specs migrate path, inherit E-03).
  - Depends on: E-02, E-03, E-06
  - Expected outcome: the new module passes, and cases (f) and (e2, wrapped fixture) FAIL when run against the base sha (proving it exercises the defect).
  - Execution state: pending

- [ ] E-05 `CHANGELOG.md`: add one entry under the top pending section stating that the history-block bounding rule is now shared, so `aw backlog set` no longer suppresses a same-status record against an indented line it cannot preserve, and closing a decision item no longer duplicates wrapped history records.
  - Depends on: E-02, E-03, E-06
  - Expected outcome: one new CHANGELOG line, no em or en dashes (user-facing prose).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `attention_contract` is stdlib-only with ZERO package imports and already owns the history grammar (`HISTORY_RECORD_RE`, `newest_history_record`, `last_history_at`); its module comment near `ACTOR_PARENTHESIS_REMEDY` records that placement there avoids import cycles. `backlog` imports it as `A`, `status_set.same_status_message_is_duplicate` imports it as `_ac`.
- History is NEWEST-FIRST by writer contract and the newest record is POSITIONAL (`attention_contract.newest_history_record` docstring: a date-max rule was measured and rejected because it flips `plan_readiness.history_verdict_approves`). This plan keeps positional semantics.
- Since Set `setdisp` (`vhiqo6`), `backlog.run_set` is a thin adapter over `status_set.run_set_command`; the shared engine decides suppression with `is_dup = same_status_message_is_duplicate(...)` and `should_write_history = not (is_same_status and is_dup)` in `status_set.apply_status_change`. The `evbx9s` E-04 fail-safe (`is_dup and _prior_history_records(text)`) was written into the old `run_set` and is not present on that path.
- History dates come from `artifact_core.utc_history_date()` (spec `2vev8j` Section 4.4); the shared engine only honors `--date` for specs.
- Tests: P16 (no code-pinning); the suite runs bare as `python3 -m pytest`.

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The disagreement is live on the shared engine. | Fixture: metadata bullets, `## Workflow history`, then `    - <D> same-status (aw backlog): metadata only`, blank, `Prose body`. With `D` = the history date in effect, `same_status_message_is_duplicate(..., status="same-status", date=D, message="metadata only")` -> `True`, `backlog._prior_history_records` -> `[]`, `attention._history_section_lines` -> `['    - <D> same-status (aw backlog): metadata only', '', 'Prose body']`. `aw backlog set <item> --status open --message "metadata only"` printed `unchanged`, the file kept only the indented line under the heading, and `backlog.validate_item` returned `[]`. |
| F-02 | Over the live corpus the two readers' record LISTS differ on 163 artifacts (backlog 3, plans 155, research 1, reviews 2, plus none in specs), but the NEWEST record agrees on all 2489. | Probe at `5ebf5364d` comparing `[l.strip() for l in _history_section_lines(t) if HISTORY_RECORD_RE.match(l.strip())]` with `_prior_history_records(t)`. |
| F-03 | Most of that divergence is the strict reader being WRONG for plans, not the loose one: plans WRAP a record onto indented continuation lines (e.g. plan `gwu2pv`), so `_prior_history_records` stops at the first continuation and returns 1 of 5 records. Backlog item `4znh53` has the same shape via a column-zero prose paragraph between records. So "loosen to match the loose reader" and "use the strict reader everywhere" are both wrong. | `gwu2pv`: strict 1, loose 5. `4znh53`: strict 1, column-zero 2. No tracked backlog item has a wrapped record today (probe count 0), which is why the strict rule never bit a backlog write. |
| F-04 | The chosen rule (E-01) differs from the loose reader on only 6 artifacts, each a body QUOTING history lines in indented form (`tk1gqo`, `r74211`, `4znh53`, two reviews `7jqev2`/`1i300e`, and plan `y6gsqw`), and changes NO consumer answer. | Patching the candidate into `attention._history_section_lines` and recomputing `last_history_at`, `_item_close_date`, `_item_graduated_date`, `_spec_implementing_date`, `extract_newest_history_entry`, `newest_verdict`, `history_has_review_record` over all 2489 artifacts: `diffs {}`. It also reproduces `backlog._prior_history_records` and `backlog._strip_metadata_and_history` EXACTLY on all 969 tracked backlog items and all 41 specs (0 differ), so E-02 is a no-op on the live corpus. Rejected candidates: the strict reader (wrong for wrapped plan records, F-03), the loose reader (re-opens `tk1gqo`), and a variant letting a blank-separated indented line continue a bullet (one extra plan, `y6gsqw`, would differ from the strict body boundary for no benefit). |
| F-06 | Moving `_prior_history_records` onto `.records` ALONE breaks the writer for a wrapped record. `_reattach_history` re-emits the prior records and takes its body from `rendered`, whose body came from the caller's own body reader (`set_records._extract_body` on the `close_on_answer` path, a strict `- `/blank skip loop). The new rule continues past a wrapped record, the old body readers stop at the continuation line, so the following records are written twice and the continuation is orphaned. | Review probe on `- 2026-01-03 c (x): third` / `  wrapped tail` / `- 2026-01-02 ...` / `- 2026-01-01 ...` / `Prose body`, simulating E-02 as originally written: the `close_on_answer` assembly emitted `2026-01-02` and `2026-01-01` TWICE with `wrapped tail` between the copies. With `record_lines` + a shared `_extract_body` (E-01/E-02/E-06 as revised) the same fixture round-trips with each record once and the continuation kept under its record. No tracked backlog item has this shape today (F-03), so this is latent, not corpus-visible. |
| F-07 | A `.strip()`ed body forges a record. If the body starts with a blank-separated indented quotation, stripping it de-indents the first line to column zero, and the next `_reattach_history` writes it inside the history block as a record, which is the `tk1gqo` defect by another route. | Review probe: body `    - 2026-01-01 quoted (x): example` / blank / `Prose body` fed `.strip()`ed through `_render_item` + `_reattach_history` produced a block whose `_prior_history_records` read 3 records including the quoted one. With the leading-indentation-preserving body (E-01 as revised) the same fixture kept 2 records. 0 tracked backlog items have a body starting indented today. |
| F-08 | The shared body differs from `set_records._extract_body` on exactly 2 tracked items, both `done/` (`hg2oop`, `r74211`): the old reader drops a body line equal to `## Workflow history` (column-zero in `hg2oop`, indented in `r74211`) that the new one keeps. | Review probe at `211969bb8` over 975 tracked backlog items. Neither is `blocked`, and `close_on_answer` is the only production caller, so no write path reaches them; keeping a quoted line is the correct body. |
| F-05 | The existing `evbx9s` test `test_e_f03_indented_prose_fixture_fails_safe_writes_record` hard-codes `2026-10-02` in the fixture, so on any later day the predicate returns False on date mismatch and the test passes WITHOUT exercising suppression. It no longer fences the hazard. | `same_status_message_is_duplicate(fixture, date="2026-10-02")` -> True; `date="2026-10-12"` -> False. E-04 (f) dates its fixture from `utc_history_date()`. |

## Proposed changes (ordered, validatable)

1. E-01 adds `attention_contract.history_block`.
2. E-02, E-06 and E-03 move the writer's prior-record source, its body boundary and the dedup predicate onto it.
3. E-04 fences the rule and the end-to-end outcome; E-05 records it.

## Deferred / out of scope (with reason)

- The read-only consumers of `attention._history_section_lines` (`attention` `last_history_at` call sites, `check_engine` close/graduated/implementing date readers, `plan_readiness` newest-entry and verdict readers): owned by sibling `6iab2o`. F-04 shows migrating them changes no answer today, but they gate approval surfaces, so the move is its own reviewable change.
  - Carrier: 6iab2o
- A validation rule refusing an item whose history block holds no record: owned by sibling `v5m5y8` (the item's "cheap independent backstop").
  - Carrier: v5m5y8
- Editing the `evbx9s` test module: it is an executed plan's deliverable; F-05 is recorded and the new module covers the hazard instead. Any cleanup is a separate corrective change.
  - Carrier-Declined: the hazard that test was meant to fence is covered by E-04 (f) here; editing an executed plan's deliverable is a separate optional cleanup
- Rewriting committed history: committed records are history.
  - Carrier-Declined: committed records are history and must not be rewritten

## Scope check

- Over-scope: none. Every Scope-Path is edited by an E-item.
- Under-scope: none. The predicate, the writer's prior-record source and the writer's body boundary (`_extract_body`, F-06) are all migrated, so the disagreement this item names is closed on the shared engine without opening a duplication route.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_history_block_bounding.py tests/test_backlog_history_dedup_parity.py tests/test_history_label_parity.py tests/test_backlog.py tests/test_history_provenance.py tests/test_status_set.py tests/test_specs_date_containment.py`, actual output pasted.
- The WHOLE BARE SUITE, `python3 -m pytest`, actual summary line pasted; record the base-sha failure set first and require no new failure.
- `aw backlog check` and `aw check` on the live corpus, output pasted.
- A corpus equivalence probe (V-02) run before and after.

## Spec / documentation sync

N/A. No spec states the history bounding rule; spec `20260818-1525-02` R2/AC1 require prior records be preserved newest-first, which this plan keeps. The rule's documentation lives in the `history_block` docstring.

## Open questions

### OQ-01: Which bounding rule is canonical?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The item asks for this decision. Resolved from repository evidence (F-02..F-04): neither existing reader is right for every tree, so the canonical rule is the one in E-01, which preserves the `tk1gqo` protection (indented quotations are never records), handles wrapped records, and changes zero consumer answers over all 2489 tracked artifacts.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: PASTE the `git diff` of `agent_workflows/attention_contract.py` showing `history_block` and its docstring, and PASTE `grep -n "^from\|^import" agent_workflows/attention_contract.py` showing no new package import. PASTE the output of calling `history_block` on the E-04 (a)-(e) fixtures, printing `records`, `record_lines` and `repr(body)` (the (e) body must show its leading indentation).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the `git diff` of `agent_workflows/backlog.py`. PASTE the output of a probe that saves, at the base sha, `_prior_history_records` and `_strip_metadata_and_history` for every tracked `.aw/records/backlog/**/*.backlog.md` (re-derive the item set at execution time) and, after E-02, prints the count of items whose output changed plus each changed item with old and new values. The bar is the PROPERTY: every changed item is listed and justified as a wrapped record or a quoted indented line (F-03/F-07); 0 changed was measured at review.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `git diff` of `same_status_message_is_duplicate`. PASTE a direct call on the F-01 fixture dated with `utc_history_date()` returning False, and on a well-formed fixture whose newest record repeats the message returning True. Runtime path: `status_set.apply_status_change` (the `is_dup` computation) consumes it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the pytest output of the new module passing. PASTE the output of running case (f) against the base sha (copy the new test file into a temporary `git worktree add` of the base sha and run it there; never stash the working checkout) showing it FAILS there, and the same for case (e2) on the wrapped fixture (it must fail at the base sha only if the base sha already duplicates; if it passes there, paste that and state it, since (e2) then fences the E-02/E-06 coupling rather than a base defect). Runtime path: `cli.main` -> `backlog.run_set` -> `status_set.run_set_command`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the `git diff` of `agent_workflows/set_records.py`. PASTE a base-sha vs after probe of `_extract_body` over every tracked backlog item (re-derived at execution time) listing each changed item with old and new values; each must be justified as a kept quoted `## Workflow history` body line (F-08) and be in a non-`blocked` disposition. PASTE the E-04 (e2) test result. Runtime path: `set_records.close_on_answer` -> `_extract_body` -> `backlog._render_item` -> `backlog._reattach_history`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the `git diff CHANGELOG.md` showing the single added entry with no em or en dash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 resolved; none open. Scope fence: the Scope-Paths are a declaration; an edit outside them is made and justified with `--scope-reason` at finalize, not a reason to stop. Run `aw ipd begin kgv213` before the first edit. This plan requires explicit human approval before execution. The executor is bound by the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, never `--no-verify`, never push, and MUST paste the actual runner output for every test claim (never claim a pass not run). Before the terminal transition `aw ipd lint --phase pre-transition` must report conforming with every `V-*` carrying pasted evidence. Under `aw oc run` / `aw agy run` the runner performs finalize and the executor MUST NOT run it; only in a manual run the executor runs `aw ipd finalize kgv213 ... --apply`. Never hand-edit `- Status: executed`. Do not set backlog `wkpcop` to `done`.
