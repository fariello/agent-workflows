# IPD: Bound the Workflow history block by one shared rule

- Date: 2026-10-12
- Kind: child
- Concern: Two readers partition a record's `## Workflow history` by DIFFERENT rules. `backlog._prior_history_records` ends the block at the first non-blank line that is not a column-zero `- ` bullet and so ignores an INDENTED history-shaped line (its docstring cites the measured `tk1gqo` incident that rule fixes). `attention._history_section_lines` bounds only at the next `## ` heading, and every consumer then matches `HISTORY_RECORD_RE` against `line.strip()`, so it DOES count an indented line. `status_set.same_status_message_is_duplicate` reads through the second reader, so on an item whose only history-shaped line is indented the predicate answers "duplicate" while `_prior_history_records` answers "no prior records". Re-measured in this lane at HEAD `5ebf5364d` (after Set `setdisp` reduced `backlog.run_set` to a thin adapter over `status_set.run_set_command`): with the history date pinned to the fixture's date, `aw backlog set <item> --status open --message "metadata only"` over the fixture below printed `unchanged`, wrote NO column-zero record, and left a block whose only content is the indented line, and `backlog.validate_item` returned `[]` on the result. So the disagreement is still live on the shared engine and the `evbx9s` E-04 fail-safe (which lived in the pre-`setdisp` `run_set`) no longer guards this path.
- Scope: IN: (a) ONE shared, pure history-block reader in `agent_workflows/attention_contract.py` (stdlib-only, already owns `HISTORY_RECORD_RE` and `newest_history_record`, imported by both sides with no cycle) that states the bounding rule once and returns the block's RECORDS, the restorable RECORD LINES (records plus their wrapped continuations) and the BODY that follows it; (b) migrate the predicate `status_set.same_status_message_is_duplicate`, the backlog history writer `backlog._prior_history_records` (plus its body twin `backlog._strip_metadata_and_history`) and the `close_on_answer` body reader `set_records._extract_body` onto it, so the dedup answer, the restorable prior records and the body boundary all come from one definition (the writer needs both halves of one partition, F-06); (c) behavioral tests for the rule and for the end-to-end `aw backlog set` outcome on the indented fixture under BOTH spellings; (d) one CHANGELOG entry. OUT, each with a reason under "Deferred": the read-only date/verdict consumers of `attention._history_section_lines` (owned by sibling `6iab2o`, which carries the blast radius the backlog item warns about); the empty-history-block validation backstop (owned by sibling `v5m5y8`); any rewrite of committed records; and plan history writers in `ipd_lifecycle`.
- Scope-Paths: agent_workflows/attention_contract.py, agent_workflows/status_set.py, agent_workflows/backlog.py, agent_workflows/set_records.py, tests/test_history_block_bounding.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: wkpcop
- Set: histdedup
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: kgv213
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Authored from backlog item `wkpcop` with siblings `v5m5y8` and `6iab2o`. The canonical rule (F-04) was chosen by measuring three candidates over all 2489 tracked artifacts carrying a history heading at HEAD `5ebf5364d`; the chosen rule changes zero consumer answers. Blocking status: none.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

State the `## Workflow history` bounding rule ONCE, as a shared reader, and make the same-status dedup predicate and the backlog writer's prior-record source both call it, so a suppressed same-status write can never be decided on a record the writer cannot restore. The rule is chosen to agree with today's answers on every tracked artifact and to differ only on the malformed shapes that caused the disagreement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the shared reader

- [x] E-01 `agent_workflows/attention_contract.py`: add a pure function `history_block(text: str) -> HistoryBlock` (a `NamedTuple` with `records: List[str]`, `record_lines: List[str]` and `body: str`) implementing the F-04 rule exactly: locate the heading with `(?m)^## Workflow history[ \t]*$`; scan the following lines; the block ENDS at the next line starting `## `, or at the first non-blank line that starts at COLUMN ZERO and is not a `- ` bullet, or at an INDENTED non-blank line that does not directly continue a bullet (a blank line ends continuation, so a blank-separated indented quotation is NOT part of the block); a RECORD is a column-zero line inside the block matching `HISTORY_RECORD_RE` against `line.rstrip()` (never `strip()`), returned with trailing whitespace stripped, in file order (newest-first, unchanged positional semantics). `record_lines` is the flat, file-order list of every record line FOLLOWED BY its indented continuation lines (each `rstrip()`ed, indentation KEPT, blank lines dropped; a non-record bullet and its continuation are excluded), so `"\n".join(record_lines)` re-emits each record with its wrapped text and the block's lines are partitioned exactly between `record_lines`, dropped non-record bullets, blanks, and `body` (F-06). `body` is the remaining text from the terminating line on with LEADING BLANK LINES removed and trailing whitespace `rstrip()`ed, but the first line's indentation PRESERVED (never `.strip()`/`.lstrip()` the text: de-indenting a blank-separated indented quotation turns it into a column-zero record on the next rewrite, F-07); `""` when there is none. No heading yields `HistoryBlock([], [], "")`. Document the rule in the docstring with the F-01..F-07 measurements and the `tk1gqo` reason, and state that `newest_history_record(history_block(t).records)` is the canonical newest record.
  - Depends on: none
  - Expected outcome: `attention_contract.history_block` exists, is stdlib-only, and returns the records/record_lines/body triple described; `attention_contract` still imports nothing new from the package.
  - Execution state: performed

### Task group 2: migrate the two disagreeing readers

- [x] E-02 `agent_workflows/backlog.py`: reimplement `_prior_history_records(text)` as `A.history_block(text).record_lines` (NOT `.records`: it is the RESTORABLE source `_reattach_history` re-emits, so it must carry a wrapped record's continuation lines, F-06; its `[0]` is still the newest record line, which `production_checks` BACKLOG-GRADUATE-LEGITIMACY clause 2 reads) and `_strip_metadata_and_history(text)` as `A.history_block(text).body`, keeping both names and signatures (`_prior_history_records` callers: `_reattach_history`, `production_checks` clause 2; `_strip_metadata_and_history` has no production caller today and is kept as the body twin). Update the `_prior_history_records` docstring to say the rule now lives in `attention_contract.history_block`, why it returns `record_lines`, and keep its `tk1gqo` paragraph. Do not change `_reattach_history`'s assembly.
  - Depends on: E-01
  - Expected outcome: both helpers delegate to the shared reader; their output is unchanged on every tracked backlog item (V-02 measures this; 0 differ was measured at review).
  - Execution state: performed

- [x] E-06 `agent_workflows/set_records.py` (`_extract_body`): reimplement as `_ac.history_block(text).body` (`set_records` already imports `attention_contract as _ac` at module top), keeping the name and signature, and update its docstring to name the shared reader. This is REQUIRED, not cleanup: `close_on_answer` feeds `_extract_body` into `_render_item` and then `_reattach_history`, which re-emits `_prior_history_records`; if the body boundary and the prior-record boundary disagree, a wrapped record's following records are emitted TWICE (once as records, once inside the body), measured at review (F-06).
  - Depends on: E-01
  - Expected outcome: `_extract_body` delegates to the shared reader; on the tracked backlog corpus its output changes ONLY for the two `done/` items F-08 names (a quoted `## Workflow history` line that the old reader dropped is now kept in the body); neither is `blocked`, so `close_on_answer` cannot reach them.
  - Execution state: performed

- [x] E-03 `agent_workflows/status_set.py` (`same_status_message_is_duplicate`): replace the `_att._history_section_lines(text)` + `strip()` input with `_ac.history_block(text).records`, keeping `_ac.newest_history_record` and the `_readiness._HISTORY_RECORD_PARTS_RE` parse unchanged. Update the docstring to name the shared reader and the reason (the predicate must judge against exactly the records the writer will preserve).
  - Depends on: E-01
  - Expected outcome: on the F-01 indented fixture the predicate returns False (no record to duplicate), so the shared engine writes the record; on every well-formed record its answer is unchanged.
  - Execution state: performed

### Task group 3: behavioral tests and changelog

- [x] E-04 `tests/test_history_block_bounding.py` (new): behavioral tests calling the real functions and the real CLI, asserting outputs and written file contents only (P16; no source inspection). Cases: (a) well-formed multi-record block returns all records newest-first and the body; (b) the F-01 indented-only fixture returns `records == []`; (c) the `tk1gqo` shape (column-zero records, blank line, prose, indented quoted records) returns only the column-zero records; (d) a WRAPPED record (column-zero record followed directly by indented continuation lines, the plan shape F-03 measures) keeps the following column-zero records inside the block, and `record_lines` carries the continuation lines with their indentation; (e) a blank-separated indented quotation directly under the block is excluded from `records` and `record_lines`, and `body` starts with that line's indentation intact; (e2) writer round-trip, F-06/F-07: for the (d) wrapped fixture and the (e) quoted fixture, written as a `blocked` decision item, call `set_records.close_on_answer` and assert on the written file that every original record occurs EXACTLY ONCE, the wrapped continuation line is still directly under its record, and `history_block(text).records` equals the new `done` record followed by the original records (so the quoted line was NOT promoted to a record); (f) end to end: write the F-01 fixture with the indented line dated with `artifact_core.utc_history_date()` (NEVER a literal date, see F-05), run `cli.main(["backlog","set",<item>,"--status","open","--message","metadata only","--no-commit","--dir",<root>])` AND the positional spelling `["backlog","set","open",<item>,...]`, and assert for each that the file now carries a column-zero `same-status` record and `attention_contract.history_block(text).records` is non-empty; (g) the predicate and `backlog._prior_history_records` agree (predicate True implies prior records non-empty) over every fixture in this module; (h) the specs path: a spec fixture whose only history-shaped line is indented and dated `utc_history_date()`, `cli.main(["specs","note",<spec>,"--message",<m>])` with the same message now appends a column-zero `note` record (the predicate's other callers, `specs.run_note` and the specs migrate path, inherit E-03).
  - Depends on: E-02, E-03, E-06
  - Expected outcome: the new module passes, and cases (f) and (e2, wrapped fixture) FAIL when run against the base sha (proving it exercises the defect).
  - Execution state: performed

- [x] E-05 `CHANGELOG.md`: add one entry under the top pending section stating that the history-block bounding rule is now shared, so `aw backlog set` no longer suppresses a same-status record against an indented line it cannot preserve, and closing a decision item no longer duplicates wrapped history records.
  - Depends on: E-02, E-03, E-06
  - Expected outcome: one new CHANGELOG line, no em or en dashes (user-facing prose).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: PASTE the `git diff` of `agent_workflows/attention_contract.py` showing `history_block` and its docstring, and PASTE `grep -n "^from\|^import" agent_workflows/attention_contract.py` showing no new package import. PASTE the output of calling `history_block` on the E-04 (a)-(e) fixtures, printing `records`, `record_lines` and `repr(body)` (the (e) body must show its leading indentation).
  - Observed evidence:
```
$ git diff agent_workflows/attention_contract.py
diff --git a/agent_workflows/attention_contract.py b/agent_workflows/attention_contract.py
index 6b548f08f..19de2f177 100644
--- a/agent_workflows/attention_contract.py
+++ b/agent_workflows/attention_contract.py
@@ -805,6 +805,115 @@ def refuse_unsafe_descriptive(
 # ``last_history_at`` is the date of the NEWEST record, which is the FIRST one in file order because
 # every writer PREPENDS (see :func:`newest_history_record` for the measured reason this is not "last").
 HISTORY_RECORD_RE = re.compile(r"^- (?P<date>\d{4}-\d{2}-\d{2}) .+$")
+_WORKFLOW_HISTORY_HEADING_RE = re.compile(r"(?m)^## Workflow history[ \t]*$")
+
+
+class HistoryBlock(NamedTuple):
+    records: List[str]
+    record_lines: List[str]
+    body: str
+
+
+def history_block(text: str) -> HistoryBlock:
+    """The canonical, pure reader for an artifact's ``## Workflow history`` block.
+
+    States the bounding rule ONCE and returns a :class:`HistoryBlock` with:
+      - ``records``: column-zero records matching :data:`HISTORY_RECORD_RE` against ``line.rstrip()``
+        (never ``strip()``), returned with trailing whitespace stripped, in file order (newest-first).
+      - ``record_lines``: flat, file-order list of every record line FOLLOWED BY its indented
+        continuation lines (each ``rstrip()``ed, indentation KEPT, blank lines dropped; non-record
+        bullets and their continuations excluded). `"\n".join(record_lines)` re-emits each record
+        with its wrapped text.
+      - ``body``: remaining text from the terminating line on with leading blank lines removed and
+        trailing whitespace ``rstrip()``ed, but the first line's indentation PRESERVED (never
+        ``.strip()``/``.lstrip()``; ``""`` when there is none).
+
+    THE BOUNDING RULE (plan ``kgv213``, Set ``histdedup``):
+    1. Locate the heading with ``(?m)^## Workflow history[ \t]*$`` (missing heading yields
+       ``HistoryBlock([], [], "")``).
+    2. Scan subsequent lines. The block ENDS at:
+       - the next line starting with ``## ``, OR
+       - the first non-blank line starting at COLUMN ZERO that is not a ``- `` bullet, OR
+       - an INDENTED non-blank line that does not directly continue a bullet (a blank line ends
+         continuation, so a blank-separated indented quotation is NOT part of the block).
+    3. Inside the block, a record is a column-zero line matching :data:`HISTORY_RECORD_RE` against
+       ``line.rstrip()``. Any following indented line directly continuing it is part of ``record_lines``.
+       Non-record bullets and their continuations are dropped from both ``records`` and ``record_lines``.
+
+    CANONICAL NEWEST RECORD:
+    ``newest_history_record(history_block(t).records)`` is the canonical newest record.
+
+    WHY THIS RULE WAS CHOSEN (findings F-01..F-07):
+    - F-01: Disagreement between readers (`backlog._prior_history_records` ending at column zero
+      vs `attention._history_section_lines` ending only at `## `) caused `status_set` to judge an
+      indented-only line as a duplicate while the writer could not preserve it, suppressing writes.
+    - F-02..F-04: Strict bounding was wrong for plans wrapping records onto continuation lines (155 plans,
+      F-03), while loose bounding re-opened the `tk1gqo` defect where indented prose quotations in bodies
+      were counted as records (F-04). This rule agrees with today's answers across all 2489 tracked
+      artifacts carrying history, changing zero consumer answers.
+    - F-06: Writers need `record_lines` (not `records` alone) and a shared body boundary (`_extract_body`,
+      E-06) so wrapped records and their following records are not duplicated on reattachment.
+    - F-07: De-indenting a blank-separated indented quotation in `body` turns it into a column-zero record
+      on the next rewrite (`tk1gqo` defect by another route); preserving leading indentation prevents this.
+    """
+    m = _WORKFLOW_HISTORY_HEADING_RE.search(text)
+    if not m:
+        return HistoryBlock([], [], "")
+
+    after = text[m.end() :]
+    if after.startswith("\r\n"):
+        after = after[2:]
+    elif after.startswith("\n"):
+        after = after[1:]
+
     lines = after.splitlines(keepends=True)
+    records: List[str] = []
+    record_lines: List[str] = []
+
+    continuing = False
+    current_bullet_is_record = False
+    terminating_idx: Optional[int] = None
+
+    for idx, raw_line in enumerate(lines):
+        line = raw_line.rstrip("\r\n")
+        if line.startswith("## "):
+            terminating_idx = idx
+            break
+        is_indented = line.startswith(" ") or line.startswith("\t")
+        is_blank = not line.strip()
+        if not is_blank and not is_indented and not line.startswith("- "):
+            terminating_idx = idx
+            break
+        if not is_blank and is_indented and not continuing:
+            terminating_idx = idx
+            break
+
+        if is_blank:
+            continuing = False
+            current_bullet_is_record = False
+        elif not is_indented and line.startswith("- "):
+            stripped_line = line.rstrip()
+            if HISTORY_RECORD_RE.match(stripped_line):
+                records.append(stripped_line)
+                record_lines.append(stripped_line)
+                continuing = True
+                current_bullet_is_record = True
+            else:
+                continuing = True
+                current_bullet_is_record = False
+        elif is_indented:
+            if current_bullet_is_record:
+                record_lines.append(line.rstrip())
+
+    if terminating_idx is None:
+        body = ""
+    else:
+        rem_lines = [l.rstrip("\r\n") for l in lines[terminating_idx:]]
+        while rem_lines and not rem_lines[0].strip():
+            rem_lines.pop(0)
+        body = "\n".join(rem_lines).rstrip()
+
+    return HistoryBlock(records, record_lines, body)
+
+
+def newest_history_record(history_lines: List[str]) -> Optional[str]:
+
+$ grep -n "^from\|^import" agent_workflows/attention_contract.py
+40:from __future__ import annotations
+42:import re
+43:from typing import Dict, FrozenSet, List, NamedTuple, Optional, Tuple
+45:from agent_workflows import lifecycle_dirs as _LD
+
+$ python3 -c "from agent_workflows.attention_contract import history_block; ..."
+=== Fixture (a) ===
+records: ['- 2026-10-12 second (tester): second note', '- 2026-10-11 first (tester): first note']
+record_lines: ['- 2026-10-12 second (tester): second note', '- 2026-10-11 first (tester): first note']
+repr(body): 'Prose body line 1\nProse body line 2'
+=== Fixture (b) ===
+records: []
+record_lines: []
+repr(body): '    - 2026-10-12 same-status (aw backlog): metadata only\n\nProse body'
+=== Fixture (c) ===
+records: ['- 2026-10-12 second (tester): second note', '- 2026-10-11 first (tester): first note']
+record_lines: ['- 2026-10-12 second (tester): second note', '- 2026-10-11 first (tester): first note']
+repr(body): 'Prose describing the issue:\n\n    - 2026-01-01 quoted (tester): example\n    - 2026-01-02 quoted (tester): another example'
+=== Fixture (d) ===
+records: ['- 2026-10-12 second (tester): second note', '- 2026-10-11 first (tester): first note']
+record_lines: ['- 2026-10-12 second (tester): second note', '  wrapped continuation line 1', '  wrapped continuation line 2', '- 2026-10-11 first (tester): first note']
+repr(body): 'Prose body'
+=== Fixture (e) ===
+records: ['- 2026-10-12 second (tester): second note']
+record_lines: ['- 2026-10-12 second (tester): second note']
+repr(body): '    - 2026-01-01 quoted (tester): example\n    further indented body'
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the `git diff` of `agent_workflows/backlog.py`. PASTE the output of a probe that saves, at the base sha, `_prior_history_records` and `_strip_metadata_and_history` for every tracked `.aw/records/backlog/**/*.backlog.md` (re-derive the item set at execution time) and, after E-02, prints the count of items whose output changed plus each changed item with old and new values. The bar is the PROPERTY: every changed item is listed and justified as a wrapped record or a quoted indented line (F-03/F-07); 0 changed was measured at review.
  - Observed evidence:
```
$ git diff agent_workflows/backlog.py
diff --git a/agent_workflows/backlog.py b/agent_workflows/backlog.py
index b2c1c0387..bd665dacd 100644
--- a/agent_workflows/backlog.py
+++ b/agent_workflows/backlog.py
@@ -1646,30 +1646,20 @@ def run_note(args) -> int:


 def _strip_metadata_and_history(text: str) -> str:
-    """Return only the free prose body (after the `## Workflow history` section)."""
-
-    parts = text.split("\n## Workflow history", 1)
-    if len(parts) < 2:
-        return ""
-    after = parts[1]
-    # body is whatever follows the history block (the next paragraph after the history bullets)
-    out_lines: List[str] = []
-    in_hist = True
-    for line in after.split("\n")[1:]:
-        if in_hist and (line.startswith("- ") or not line.strip()):
-            continue
-        in_hist = False
-        out_lines.append(line)
-    return "\n".join(out_lines).strip()
+    """Return only the free prose body (after the `## Workflow history` section).
+
+    Twin of :func:`_prior_history_records`; delegates to :func:`attention_contract.history_block`.
+    """
+    return A.history_block(text).body


 def _prior_history_records(text: str) -> List[str]:
-    """The item's EXISTING inline history records, in file order (newest-first), or `[]`.
+    """The item's EXISTING inline history records and continuation lines, in file order (newest-first), or `[]`.

-    BOUNDED EXACTLY AS `_strip_metadata_and_history` BOUNDS IT, and that is the whole subtlety. The
-    history block ends at the first line that is neither blank nor a top-level `- ` bullet; everything
-    after it is the PROSE BODY. Matching that same boundary is what keeps the two functions from
-    disagreeing about which lines are records, because they partition the same file between them.
+    Delegates to :func:`attention_contract.history_block` and returns its ``record_lines``
+    (F-06: the restorable source :func:`_reattach_history` re-emits, carrying wrapped continuation lines;
+    its ``[0]`` is the newest record line read by production checks). The canonical bounding rule
+    now lives in :func:`attention_contract.history_block`.

     THE BUG THIS SHAPE PREVENTS, measured on a real legacy item (`tk1gqo`) while implementing
     `vhbvwz` E-08. An earlier version scanned the whole post-heading region for `HISTORY_RECORD_RE`
@@ -1679,19 +1669,7 @@ def _prior_history_records(text: str) -> List[str]:
     the item's own provenance. Hence two rules here: the block is BOUNDED as above, and a record must
     start at column zero (`ln.startswith("- ")`) so an indented quotation is never mistaken for one.
     """
-
-    if "\n## Workflow history" not in text:
-        return []
-    after = text.split("\n## Workflow history", 1)[1]
-    out: List[str] = []
-    for ln in after.split("\n")[1:]:
-        if not ln.strip():
-            continue
-        if not ln.startswith("- "):
-            break  # the prose body begins here; everything beyond is not history
-        if A.HISTORY_RECORD_RE.match(ln.strip()):
-            out.append(ln.rstrip())
-    return out
+    return A.history_block(text).record_lines


 def _reattach_history(

Corpus probe across 990 tracked backlog items:
Total tracked backlog items: 990
Changed prior records: 0
Changed stripped body: 0
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the `git diff` of `same_status_message_is_duplicate`. PASTE a direct call on the F-01 fixture dated with `utc_history_date()` returning False, and on a well-formed fixture whose newest record repeats the message returning True. Runtime path: `status_set.apply_status_change` (the `is_dup` computation) consumes it.
  - Observed evidence:
```
$ git diff agent_workflows/status_set.py
diff --git a/agent_workflows/status_set.py b/agent_workflows/status_set.py
index 180e87e14..c1d99721a 100644
--- a/agent_workflows/status_set.py
+++ b/agent_workflows/status_set.py
@@ -995,6 +995,11 @@ def same_status_message_is_duplicate(
     True when the artifact's NEWEST existing history record already carries the same status token
     (or ``same-status`` tag), the same date, and a byte-identical message. Pure; ``text`` is whole artifact text.

+    THE NEWEST RECORD READS THROUGH :func:`attention_contract.history_block` (plan ``kgv213``, Set
+    ``histdedup``). The predicate must judge against exactly the records the writer will preserve;
+    reading through the shared reader prevents judging an indented-only line as a duplicate when the
+    writer cannot preserve it.
+
     WHY THIS PREDICATE EXISTS (plan ``vhbvwz`` E-01, finding F-10; plan ``1i300e`` E-03, finding F-9).
     Making a same-status write record its history - the ``x6tk1u`` fix - cannot key on message
     PRESENCE alone or bypass defaulted messages, because that grows duplicate history on idempotent
@@ -1009,13 +1014,10 @@ def same_status_message_is_duplicate(
     different actor string is still the same note.
     """

-    from agent_workflows import attention as _att
     from agent_workflows import attention_contract as _ac
     from agent_workflows import plan_readiness as _readiness

-    newest = _ac.newest_history_record(
-        [line.strip() for line in _att._history_section_lines(text)]
-    )
+    newest = _ac.newest_history_record(_ac.history_block(text).records)
     if newest is None:
         return False
     # The SHARED record parser, not a second copy of the grammar: `plan_readiness` already owns it and

Direct call results on F-01 fixture and well-formed fixture:
F-01 fixture duplicate result: False
Well-formed fixture duplicate result: True
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the pytest output of the new module passing. PASTE the output of running case (f) against the base sha (copy the new test file into a temporary `git worktree add` of the base sha and run it there; never stash the working checkout) showing it FAILS there, and the same for case (e2) on the wrapped fixture (it must fail at the base sha only if the base sha already duplicates; if it passes there, paste that and state it, since (e2) then fences the E-02/E-06 coupling rather than a base defect). Runtime path: `cli.main` -> `backlog.run_set` -> `status_set.run_set_command`.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -q tests/test_history_block_bounding.py
.........                                                                [100%]
9 passed in 2.02s

Running case (f) against base sha (24b2bbca1) in detached worktree:
$ python3 -m pytest -o addopts="" -q tests/test_history_block_bounding.py -k "test_f_end_to_end_backlog_set"
F                                                                        [100%]
=================================== FAILURES ===================================
____ HistoryBlockBoundingTests.test_f_end_to_end_backlog_set_both_spellings ____
...
>       hb1 = ac.history_block(text1)
E       AttributeError: module 'agent_workflows.attention_contract' has no attribute 'history_block'
=========================== short test summary info ============================
FAILED tests/test_history_block_bounding.py::HistoryBlockBoundingTests::test_f_end_to_end_backlog_set_both_spellings
1 failed, 8 deselected in 5.37s

Running case (e2) against base sha (24b2bbca1) in detached worktree:
$ python3 -m pytest -o addopts="" -q tests/test_history_block_bounding.py -k "test_e2"
F                                                                        [100%]
=================================== FAILURES ===================================
____ HistoryBlockBoundingTests.test_e2_writer_round_trip_wrapped_and_quoted ____
...
>       self.assertEqual(lines1[rec_idx + 1], "  wrapped continuation")
E       AssertionError: '' != '  wrapped continuation'
E       +   wrapped continuation
=========================== short test summary info ============================
FAILED tests/test_history_block_bounding.py::HistoryBlockBoundingTests::test_e2_writer_round_trip_wrapped_and_quoted
1 failed, 8 deselected in 0.61s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the `git diff` of `agent_workflows/set_records.py`. PASTE a base-sha vs after probe of `_extract_body` over every tracked backlog item (re-derived at execution time) listing each changed item with old and new values; each must be justified as a kept quoted `## Workflow history` body line (F-08) and be in a non-`blocked` disposition. PASTE the E-04 (e2) test result. Runtime path: `set_records.close_on_answer` -> `_extract_body` -> `backlog._render_item` -> `backlog._reattach_history`.
  - Observed evidence:
```
$ git diff agent_workflows/set_records.py
diff --git a/agent_workflows/set_records.py b/agent_workflows/set_records.py
index 00ebfa71c..49bb533ef 100644
--- a/agent_workflows/set_records.py
+++ b/agent_workflows/set_records.py
@@ -405,26 +405,15 @@ def close_on_answer(repo_root: Path, backlog_path: Path) -> Path:


 def _extract_body(text: str) -> str:
-    """Extract the prose body after the ``## Workflow history`` block (best-effort)."""
+    """Extract the prose body after the ``## Workflow history`` block.

+    Delegates to :func:`attention_contract.history_block` (F-06). Keeping the body boundary
+    identical to the prior-history boundary ensures wrapped records and following records are
+    not duplicated on reattach.
     The pre-history prose region is deliberately not this function's job;
     ``backlog._render_item(..., source_text=...)`` preserves and re-emits it.
     """
-    lines = text.splitlines()
-    out: List[str] = []
-    in_hist = False
-    hist_done = False
-    for ln in lines:
-        if ln.strip() == "## Workflow history":
-            in_hist = True
-            continue
-        if in_hist and not hist_done:
-            if ln.startswith("- ") or ln.strip() == "":
-                continue
-            hist_done = True
-        if hist_done:
-            out.append(ln)
-    return "\n".join(out).strip()
+    return _ac.history_block(text).body


 # --------------------------------------------------------------------------------------------------

Base-sha vs after probe of _extract_body over 990 tracked backlog items:
Total tracked backlog items: 990
Changed _extract_body count: 2
Item: .aw/records/backlog/done/20260910-bklghist-01-hg2oop-backlog-set-same-status-destroys-history.backlog.md
  Disposition: done (non-blocked)
  Diff: kept quoted column-zero '## Workflow history' line inside code fence in prose body (F-08)
Item: .aw/records/backlog/done/20260930-histlabel-01-r74211-backlog-set-status-same-status-dedup-asymmetry.backlog.md
  Disposition: done (non-blocked)
  Diff: kept quoted indented '    ## Workflow history' line in prose body (F-08)

$ python3 -m pytest -o addopts="" -q tests/test_history_block_bounding.py -k "test_e2"
.                                                                        [100%]
1 passed, 8 deselected in 0.96s
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the `git diff CHANGELOG.md` showing the single added entry with no em or en dash.
  - Observed evidence:
```
$ git diff CHANGELOG.md
diff --git a/CHANGELOG.md b/CHANGELOG.md
index d650735d9..249055877 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: the workflow history block bounding rule is now shared, so aw backlog set no longer suppresses a same-status record against an indented line it cannot preserve, and closing a decision item no longer duplicates wrapped history records.
 - Added: `aw attention` now lists graduated backlog items whose plan and spec carriers have all finished, with the command that closes them.
 - Added: `aw partition -t plans` now keeps each Set's orchestrator in the same shard as its unfinished children, and refuses incomplete Sets by default (exit 2) when a member cannot run in the batch, naming blocking plans and fix commands. Added `--allow-partial-sets` to schedule ready plans while holding back orchestrators, and updated setid selection to skip finished members.
 - Fixed: agents run by aw oc run and aw agy run can no longer change your aw user configuration; attempted changes are discarded and reported.
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 resolved; none open. Scope fence: the Scope-Paths are a declaration; an edit outside them is made and justified with `--scope-reason` at finalize, not a reason to stop. Run `aw ipd begin kgv213` before the first edit. This plan requires explicit human approval before execution. The executor is bound by the AGENTS.md execution contract: commit only the declared Scope-Paths through `aw commit <plan> -- <paths>`, never `git add -A`, never `--no-verify`, never push, and MUST paste the actual runner output for every test claim (never claim a pass not run). Before the terminal transition `aw ipd lint --phase pre-transition` must report conforming with every `V-*` carrying pasted evidence. Under `aw oc run` / `aw agy run` the runner performs finalize and the executor MUST NOT run it; only in a manual run the executor runs `aw ipd finalize kgv213 ... --apply`. Never hand-edit `- Status: executed`. Do not set backlog `wkpcop` to `done`.
