# IPD: Read a prompt's id6 from its metadata comment and filename slot so aw find prompts stops printing a dash

- Date: 2026-09-29
- Kind: child
- Concern: `aw find prompts` renders `-` in the id6 column for ALL 17 tracked prompts, and `aw find prompts --id <id6>` returns ZERO rows for an id6 the tree demonstrably holds. The generic branch of `cli._find_type_records` derives a record's id6 from exactly one reader, `selectors._read_id`, which knows two dialects (a `- Id:` bullet matched by `selectors._ID_RE`, and a case-sensitive YAML `id:` scalar). A prompt has NEITHER BY CONTRACT: `.aw/records/prompts/README.md` states the prompt's `Id:` lives in the single leading HTML comment and is "never a `- Id:` bullet, which would render as visible text above the prompt body", and adds "YAML front-matter is NOT permitted". So the one reader `find` consults is guaranteed to miss, `raw_id` is `None` for every prompt, and the display falls to its `"-"` placeholder while the same branch's `explicit_id` filter compares against that same dead value. The data is fine: `prompts_index.scan_prompts` already resolves all 17 through `meta.get("Id") or fn_id6`, and `attention._prompts_record` already reads `prompts.read_metadata_id6`. `find` is the only prompts-facing reader never taught either source, even though it WAS already taught a prompts special case for the neighboring status column (`cli._find_prompt_lane_status`).
- Scope: Teach `aw find`'s generic branch to resolve a prompt's id6 from the two sources the purity contract DOES sanction, in the precedence `prompts_index.scan_prompts` already ships (metadata comment first, filename identity slot second), so the id6 column is populated and `--id` matches. Fix the `--set` filter in the same reader for the same root cause (a prompt's `Set:` is in the same comment, so `selectors._read_setid` misses it too and `aw find prompts --set plainlang` returns zero rows against a prompt whose filename setid IS `plainlang`). Does NOT widen `selectors._ID_RE`, does NOT route `selectors.resolve`'s id6 rule through a whole-file read, does NOT change which artifacts MATCH for any type, does NOT touch the status column, and does NOT change any non-prompt type's id6 rendering.
- Scope-Paths: agent_workflows/cli.py, tests/test_find_prompts_lane_status.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: y0t9u7
- Blocks-Release: next
- Set: y0t9u7
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3b01h9

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `y0t9u7`, graduating it. Every claim below was MEASURED in this lane at HEAD `94736255`, not restated from the item. Four facts were found that the item does not state and that change the shape of the fix. FIRST, the id6 column is not the only casualty: `--id` and `--set` are BROKEN BY THE SAME READER, measured returning zero rows for `la0gje` and `plainlang` respectively, so a fix that only paints the column leaves two filters silently answering wrong. SECOND, the two sources DISAGREE on 2 of the 17 prompts (`oujnft` and `exnwoz` declare an id6 in their comment that `selectors.filename_slot_id6` REFUSES to read from their filenames, because that helper requires the slot token to contain a digit), so the precedence order is load-bearing and measurable rather than cosmetic. THIRD, the filename slot cannot be read with a bare `parse_clustered(...).group("id6")`: measured, that returns `id6='prompt'` for the legacy name `20260810-1958-01-prompt-purity-lint.prompt.md`, which is a slug word and not an identity. FOURTH, the existing test module for this surface asserts only `tokens[1]` (status) and never `tokens[2]` (id6), which is exactly why 17/17 broken rows shipped green.

## Goal

Make `aw find prompts` report the id6 a prompt actually has, and make its `--id`/`--set` filters find it.
The prompt tree already carries the identity in two places the purity contract sanctions; `find` reads
neither, so it reports absence where the repository has data. This is a DISPLAY-AND-FILTER layer fix
inside `cli._find_type_records`, reusing two existing readers, and it deliberately changes nothing about
which records MATCH a selector.

FIVE FACTS ESTABLISHED AT AUTHORING, so the executor neither re-derives them nor inherits a premise
measurement has already falsified.

1. THE DEFECT IS TOTAL ON THE COLUMN AND SILENT ON TWO FILTERS. Measured at HEAD `94736255`:

   ```text
   $ python3 -m agent_workflows find prompts | head -3
   ✓  executed      -  .aw/records/prompts/executed/20260722-sloz20-01-sloz20-token-efficient-managed-sections-research-prompt.prompt.md
   ✓  executed      -  .aw/records/prompts/executed/20260725-7rddum-01-7rddum-aw-delivery-and-clean-delta.prompt.md
   ✓  executed      -  .aw/records/prompts/executed/20260725-99thcw-01-99thcw-external-delivery-host-probe.prompt.md
   (17 rows, 17 dashes)

   $ python3 -m agent_workflows find prompts --id la0gje
   ✓ CLEAN  no matching prompts          # rc=0, yet that id6's file is row 4 above

   $ python3 -m agent_workflows find prompts --set plainlang
   ✓ CLEAN  no matching prompts          # rc=0, yet 20260920-plainlang-01-ng0ga4-... exists
   ```

   The backlog item names the column. The two filters are the same bug and are WORSE, because a wrong
   empty answer at exit 0 is indistinguishable from a true empty answer.

2. THE DATA IS PRESENT IN BOTH SANCTIONED PLACES, AND TWO OTHER MODULES ALREADY READ IT. Measured over
   all 17 tracked prompts:

   ```text
   comment-Id   filename-slot   selectors._read_id
   17/17        15/17           0/17
   ```

   `prompts_index.scan_prompts` resolves `id6 = meta.get("Id") or fn_id6` and returns all 17;
   `attention._prompts_record` reads `prompts.read_metadata_id6`. Only `find` reads neither.

3. THE PRECEDENCE IS MEASURABLE, NOT COSMETIC. Two prompts (`oujnft`, `exnwoz`) declare an id6 in their
   comment that `selectors.filename_slot_id6` returns `None` for, because that helper requires the slot
   token to CONTAIN A DIGIT (`_HAS_DIGIT_RE`) as its guard against reading a slug word as an identity,
   and both of those id6s are all-letters. Comment-first therefore resolves 17/17 while slot-first
   resolves 15/17. The order `prompts_index` already ships is the correct one and must be matched
   rather than reinvented.

4. THE FILENAME SLOT MUST BE READ THROUGH THE GUARDED HELPER, NEVER THROUGH THE RAW PARSE. Measured:

   ```text
   parse_clustered("20260810-1958-01-prompt-purity-lint.prompt.md").group("id6") -> 'prompt'
   selectors.filename_slot_id6(same)                                             -> None
   ```

   A legacy `YYYYMMDD-HHMM-NN-<slug>` name parses CONFORMANT with a slug word in the identity slot, and
   `artifact_core.ID6_RE` accepts it. `selectors.filename_slot_id6` exists precisely to refuse that, and
   its comment records the live case (`id6='assess'` for a record whose real Id is `wvlk84`). Reading the
   slot any other way MANUFACTURES an identity claim.

5. THE COVERAGE HOLE THAT LET THIS SHIP IS IDENTIFIABLE AND MUST BE CLOSED. `tests/test_find_prompts_lane_status.py`
   is the dedicated test module for this exact surface, its fixture writes prompts WITH `Id:` in the
   metadata comment, and every assertion reads `tokens[1]` (the status cell). Not one reads `tokens[2]`
   (the id6 cell). All 15 tests pass at HEAD against 17 broken rows.

   ```text
   $ python3 -m pytest tests/test_find_prompts_lane_status.py tests/test_find_single_read.py tests/test_cli_find.py
   15 passed in 2.04s
   ```

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect before changing it

- [ ] E-01 EXTEND `tests/test_find_prompts_lane_status.py` WITH FAILING COVERAGE FOR THE id6 CELL, asserting `tokens[2]` for every prompt its fixture already writes, since that fixture writes a comment `Id:` and a conformant clustered filename and therefore already has everything needed. Add the three cases the current fixture does NOT cover, because each one is a distinct source-resolution path: (a) a prompt with a comment `Id:` AND a matching filename slot, (b) a prompt with a comment `Id:` and a LEGACY `YYYYMMDD-HHMM-NN-<slug>` filename that has no identity slot at all, and (c) a prompt with NO metadata comment whose id6 exists only in the filename slot. Also add the two filter cases (`--id`, `--set`). MIND THE EXISTING FIXTURE'S TRAP: its `not-executed` lane id6 is the six-character string `prnot-`, which `artifact_core.ID6_RE` REJECTS (measured: `ID6_RE.match('prnot-')` is None) and which `artifact_naming.parse_clustered` therefore refuses for that row's whole filename; use a valid id6 for any NEW row rather than copying that pattern, and state in the evidence what the pre-existing `prnot-` row resolves to so a reader is not surprised by it later.
  - Depends on: none
  - Expected outcome: a pasted test run showing the new assertions FAILING against HEAD, each failure naming the dash it received, plus the 15 pre-existing tests still passing.
  - Execution state: pending

### Task group 2: the reader, matching the precedence that already ships

- [ ] E-02 ADD A PROMPTS id6 READER to `cli.py` as the exact structural sibling of the existing `cli._find_prompt_lane_status`, which is the precedent for a prompts special case in this branch and returns `None` for every other type. Resolve in the precedence `prompts_index.scan_prompts` ships (`meta.get("Id") or fn_id6`): FIRST `prompts.read_metadata_id6(text)`, which reads the first line only so a body-quoted `Id:` is never taken as a declaration, THEN `selectors.filename_slot_id6(path)`. Do NOT re-implement either reader and do NOT parse the comment inline; `prompts.read_metadata_id6` is documented as the one in-file reader and `filename_slot_id6` carries the slug-word guard E-04 of this plan's findings measures as necessary. Take the ALREADY-READ `text` as a parameter rather than re-opening the file: the generic branch reads each record exactly once and IPD `qfpnrm` removed a measured double read (1240 opens for 620 records) from this very layer, so adding a second open would reintroduce the defect backlog `59t9x5` closed.
  - Depends on: none
  - Expected outcome: a pure function plus pasted output resolving all 17 live prompts, explicitly showing that `oujnft` and `exnwoz` resolve from the COMMENT (their filename slot being `None`) and that a legacy-named prompt resolves to `None` rather than to a slug word.
  - Execution state: pending

- [ ] E-03 WIRE THE READER INTO THE GENERIC BRANCH of `cli._find_type_records` at the single place `raw_id` is computed, so ONE value feeds all three consumers: the `explicit_id` comparison, the `--set` comparison's sibling, and the `id6 = raw_id or "-"` display. Keep `selectors._read_id` as the primary and use the prompts reader as the FALLBACK when it returns `None`, so the ordering states the rule plainly (a declared bullet, if a record ever had one, still wins) and no other type's behavior can shift. DO THE SAME FOR `--set`, whose `selectors._read_setid` misses a prompt's `Set:` for the identical reason (measured `None` for the `plainlang` prompt); resolve it from the metadata comment then the filename setid group. THE FALLBACK MUST BE TYPE-GATED, returning `None` for every non-prompt type exactly as `_find_prompt_lane_status` does, so `walkthroughs` (12 of 24 with no readable `- Id:`), `comms` (7 of 7), `specs` (19 of 38) and `reviews` (416 of 478 with a filename slot holding their SUBJECT's id6) are untouched. That last population is the reason this must not be generalized: a review's slot id6 is its subject's by documented design (`.aw/records/reviews/README.md`), so printing it as the review's own identity would assert an identity claim D140 forbids.
  - Depends on: E-02
  - Expected outcome: pasted `aw find prompts` output showing 17 real id6 values, pasted `--id la0gje` and `--set plainlang` each returning exactly one row, and pasted `aw find reviews`/`aw find walkthroughs`/`aw find comms`/`aw find specs` output proving byte-identical rendering to a pre-change capture.
  - Execution state: pending

### Task group 3: the consequences a populated column has elsewhere

- [ ] E-04 MEASURE AND REPORT THE COLLISION-SURFACE CONSEQUENCE, because populating the id6 changes what `cli._detect_id6_collisions` can see and this plan must state whether that is a fix, a risk, or a no-op rather than leaving it to be discovered. THE FACT AT AUTHORING: that function keys on the SELECTOR TOKEN and consults `selectors.id6_ownership`, not on the rendered cell, so this change should be a no-op for it; but `id6_ownership` itself returns `reference` for `oujnft` and `exnwoz` (measured), meaning those two prompts are currently INVISIBLE to claim detection while the other 15 return `slot-only`. Re-measure both facts after the wiring, state whether any NEW warning appears on any query, and if one does, determine whether it is a TRUE collision (a data problem to file) or a false positive (a defect in this change, which must then be fixed before proceeding). Do NOT change `id6_ownership`: it is a whole-file ownership predicate shared with `runner_shared` and widening it is a separate contract decision.
  - Depends on: E-03
  - Expected outcome: a before/after comparison of collision output for a bare-id6 query against a prompt, the re-measured ownership verdicts for all 17, and an explicit verdict of no-op / true-finding-filed / defect-fixed.
  - Execution state: pending

- [ ] E-05 CONFIRM THE `--paths` AND MACHINE SURFACES ARE CONSISTENT WITH THE HUMAN ONE, since `_run_find` has four output paths and this change touches a value two of them carry. The `--paths` stream prints bare paths and must be BYTE-IDENTICAL for an unfiltered query (no id6 appears in it), while `--agent`/`--json` carry `data.matches`, which is the rendered line list and therefore DOES change. Paste all four surfaces before and after for one query, and state plainly that the machine `matches` strings change shape (dash to id6) so a consumer keying on them is warned. Verify the `--agent`/`--json` records still validate against the schema validator rather than judging them by eye.
  - Depends on: E-03
  - Expected outcome: before/after captures of all four surfaces for one prompts query, with the `--paths` stream shown identical and the machine records shown changed AND schema-valid.
  - Execution state: pending

### Task group 4: closeout

- [ ] E-06 RUN THE FULL REGRESSION GATE, capturing a pre-execution baseline BEFORE any edit in this plan lands and a post-change run after E-05, both with bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Additionally run `python3 -m agent_workflows check prompts` and `python3 -m agent_workflows index prompts --check`, because both consume prompt identity and a change to how it is read must leave them conforming. Then `aw ipd lint --phase pre-transition` on this plan and `aw sanitize --agent`. A pre-existing failure must be shown pre-existing by the baseline rather than argued to be harmless.
  - Depends on: E-05
  - Expected outcome: baseline and post-change `N passed` lines pasted side by side, the two prompts checks conforming, a conforming pre-transition lint, and a clean sanitizer report.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE PURITY CONTRACT IS THE REASON A PROMPT HAS NO `- Id:`, so the fix must be a READER change and never a data change. `.aw/records/prompts/README.md` states the metadata "lives in a SINGLE leading HTML comment, which must be the first line of the file, and the prompt's `Id:` is one of its fields (never a `- Id:` bullet, which would render as visible text above the prompt body)", and that "YAML front-matter is NOT permitted (it renders as visible text or a stray table in many chat UIs, so it would become part of the prompt)". The implemented naming spec `20260817-2147-01-uniform-artifact-naming-grammar` repeats it and cites purity spec `prompt-purity-lint` R1/P4 as the authority. `prompts.inject_metadata_id6`'s docstring says the same at the write site: "A `- Id:` BULLET is never produced".
- THE PRECEDENCE ALREADY EXISTS AND MUST BE MIRRORED, NOT INVENTED. `prompts_index.scan_prompts` resolves `id6 = meta.get("Id") or fn_id6` and `set_id = meta.get("Set") or fn_set` on the adjacent line, which is exactly the two-source rule this plan needs for BOTH fields.
- THE PROMPTS SPECIAL CASE IN THIS BRANCH IS ESTABLISHED PRECEDENT. `cli._find_prompt_lane_status` already exists for the STATUS column, returns `None` for `artifact_type != "prompts"`, and delegates to `attention._prompt_disposition_from_rel`. A second sibling for the id6 is the same shape at the same site, which is why this fix needs no new architecture.
- DO NOT WIDEN THE SELECTOR READERS, and this is stated twice in the code as a contract boundary, not a style preference. The comment above `selectors.declares_id6` says raising the byte bounds or routing "`resolve`'s id6 rule through a whole-file read would change which records `aw find` MATCHES for every type and every front-matter kind", and the note on `selectors._STATUS_RE` says editing it "CHANGES WHAT `aw find` MATCHES" and is "a MATCHING-BEHAVIOR decision, not a cleanup". The prompt-aware read therefore belongs in the DISPLAY layer, which is where this plan puts it.
- THE DISPLAY LAYER MUST NOT RE-OPEN THE FILE. `cli._find_type_records`'s docstring records that IPD `qfpnrm` removed a measured double read from this layer (`selectors`' own comment: "1240 opens end to end against 620 here, i.e. every record opened about twice"), and backlog `59t9x5` was filed as a BUG on exactly that. The new reader must consume the `text` the branch already read.
- THE FILENAME SLOT HAS A DOCUMENTED TRAP WITH A DOCUMENTED GUARD. `selectors.filename_slot_id6` and the comment above it record that `parse_clustered` reports CONFORMANT with `id6='assess'` for a legacy name whose real Id is `wvlk84`, and that the discriminator is `_HAS_DIGIT_RE` mirroring `check_engine._is_real_id6`. The cost is a FALSE NEGATIVE on an all-letter real id6, "which is the safe direction for a warning" and is exactly what makes comment-first the right precedence here.
- A REVIEW'S FILENAME SLOT HOLDS ITS SUBJECT'S id6 BY DESIGN, which bounds this fix to prompts. `selectors.id6_ownership`'s docstring quotes `.aw/records/reviews/README.md` ("`<id6>` is the REVIEWED ARTIFACT's id6, not a fresh identifier ... so the join survives a rename") and records that all measured review records declare `- Subject-Id:` and no own `- Id:`. Measured in this lane: 416 of 478 reviews have no declared Id but do have a filename slot id6. Generalizing a slot fallback to all types would print a foreign id6 as 416 reviews' own identity.
- THE id6 CELL AND THE STATUS CELL SHARE ONE RESOLVED COLOR BY SPEC. `cli._find_status_and_id6` produces both from one `Resolved`, and approved spec `uonrjg` criterion A10 requires "glyph, id6, and status use the same resolved color and bold flag". Populating the id6 must not bypass that function.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | 17 of 17 prompts render `-` in the id6 column | `aw find prompts` at HEAD `94736255`, all 17 rows | The defect is total, not a corner case (E-01, E-03) |
| F-2 | `--id <id6>` returns zero rows for an id6 that exists | `aw find prompts --id la0gje` -> `no matching prompts`, rc 0 | The fix must cover the FILTER, not only the column; a wrong empty answer is worse than a dash (E-01, E-03) |
| F-3 | `--set <setid>` is broken by the same root cause | `selectors._read_setid` returns `None` for the `plainlang` prompt; `aw find prompts --set plainlang` -> zero rows | `Set:` lives in the same comment; fixing only `Id:` leaves a second silent wrong answer (E-03) |
| F-4 | The identity is present in both sanctioned places | comment `Id:` 17/17, filename slot 15/17, `selectors._read_id` 0/17 | A reader change suffices; no prompt file needs editing (E-02) |
| F-5 | Two prompts resolve ONLY from the comment | `oujnft`, `exnwoz`: `filename_slot_id6` returns `None` because `_HAS_DIGIT_RE` rejects an all-letter slot token | Comment-first precedence is required and is measurable (E-02) |
| F-6 | A legacy name's parsed slot is a slug word, not an id6 | `parse_clustered("20260810-1958-01-prompt-purity-lint.prompt.md").group("id6")` -> `'prompt'`; `filename_slot_id6` -> `None` | Must use the guarded helper, never the raw parse (E-02) |
| F-7 | Two other modules already resolve this correctly | `prompts_index.scan_prompts` (`meta.get("Id") or fn_id6`) returns all 17; `attention._prompts_record` uses `prompts.read_metadata_id6` | Mirror the shipped precedence rather than inventing one (E-02) |
| F-8 | The status column in this same branch already has a prompts special case | `cli._find_prompt_lane_status`, consumed beside the `raw_status` read | The fix is an established shape at an established site (E-02, E-03) |
| F-9 | A slot fallback generalized to all types would misreport 416 reviews | 416 of 478 reviews have no declared `- Id:` but do have a filename slot holding their SUBJECT's id6 by documented design | The fallback MUST be type-gated to prompts (E-03) |
| F-10 | The dedicated test module never asserts the id6 cell | `tests/test_find_prompts_lane_status.py` asserts `tokens[1]` in every test; 15 passed against 17 broken rows | The coverage hole is the reason this shipped; E-01 closes it |
| F-11 | The existing fixture contains an invalid id6 | `ID6_RE.match('prnot-')` is None, so `parse_clustered` refuses that row's filename | A new test row must not copy that pattern; the existing row's behavior must be stated, not silently inherited (E-01) |
| F-12 | Two prompts are invisible to claim detection today | `selectors.id6_ownership` returns `reference` for `oujnft`/`exnwoz`, `slot-only` for the other 15 | E-04 must measure whether this change alters the collision surface, and report rather than assume |
| F-13 | The display layer previously double-read every record | `cli._find_type_records` docstring and `selectors`' comment (1240 opens for 620 records), closed by IPD `qfpnrm` from backlog `59t9x5` | The new reader must take the already-read `text`, never re-open (E-02) |
| F-14 | The machine surfaces carry the rendered line | `_run_find` puts `all_lines` into `data.matches` for `--agent`/`--json` | Those records change shape; that must be stated, not discovered (E-05) |

## Proposed changes (ordered, validatable)

1. Extend `tests/test_find_prompts_lane_status.py` with failing id6-cell and filter coverage, plus the legacy-name and no-comment rows (E-01).
2. Add the type-gated prompts id6 reader in `cli.py`, comment-first then guarded filename slot, consuming the already-read text (E-02).
3. Wire it (and the `Set:` twin) into the single `raw_id`/`raw_set` computation in the generic branch (E-03).
4. Measure the collision-surface consequence and report a verdict (E-04).
5. Confirm all four output surfaces, with the machine `matches` change stated explicitly (E-05).
6. Run the full regression gate plus the two prompts-specific checkers (E-06).

## Deferred / out of scope (with reason)

- POPULATING THE id6 COLUMN FOR THE OTHER GENERIC TYPES THAT RENDER `-`. Measured in this lane: `walkthroughs` 12 of 24, `comms` 7 of 7, `specs` 19 of 38 have no readable `- Id:`. Each is a DIFFERENT question with a different answer (a legacy spec predating the spec id6 cutover legitimately HAS no id6; a comms record has none at all; a walkthrough may simply be unconverted), so answering them together would make one change to several contracts at once on evidence gathered for none of them.
  - Carrier-Declined: No defect is established for those types by this plan, so there is nothing to carry. The prompts case is a defect precisely because the identity DEMONSTRABLY EXISTS in two places and the reader consults neither; for a legacy spec or a comms record the dash may be the TRUTHFUL rendering of a genuine absence, and filing an item asserting otherwise would record a fault this plan has not measured. Determining which of those dashes are truthful requires its own measurement pass per type, and an item filed before that pass could not be closed on evidence. If a maintainer wants that sweep, it is a new backlog item with its own numbers.
- CHANGING `selectors._ID_RE`, `selectors._read_id`, or `selectors.resolve`'s id6 rule so prompts resolve by identity rather than by filename substring. Today `aw find <prompt-id6>` succeeds only via `MATCH_SUBSTRING`, the documented last resort, so a bare-token prompt query works by accident of the filename rather than by identity.
  - Carrier-Declined: This is a PROHIBITION on this plan rather than deferred work, and the code states the prohibition itself: the comment above `selectors.declares_id6` records that routing the id6 rule through a whole-file read "would change which records `aw find` MATCHES for every type and every front-matter kind", and the `_STATUS_RE` note calls such an edit "a MATCHING-BEHAVIOR decision, not a cleanup". The current behavior is also NOT WRONG, merely indirect: the query returns the correct single file. Filing an item would assert the repository intends to change selector matching semantics for every type, which no evidence here supports and which is a maintainer's call about a public contract.
- MAKING `selectors.id6_ownership` see a prompt's comment-declared id6, which would move `oujnft` and `exnwoz` from `reference` to a claiming verdict.
  - Carrier-Declined: Nothing is owed because this plan measures the question rather than leaving it open: E-04 REQUIRES a before/after measurement of the collision surface and an explicit verdict, and V-04 refuses it without one. If that measurement finds a TRUE collision the item is filed BY E-04 with the evidence attached, which is a better record than a guessed item filed now. `id6_ownership` is additionally a whole-file ownership predicate shared with `runner_shared`, so widening it is a contract change for every consumer and must not ride along inside a display fix.
- GIVING `--check` MEANING ON `find`. A comment at the `CommandResult` site in `_run_find` records that `find`'s parser accepts `--check` and "deliberately leaves that flag INERT rather than quietly giving it meaning (paw8so F-14)".
  - Carrier-Declined: A standing decision this plan declines to overturn, not deferred work. No finding here measures a fault on that flag, so there is no defect to carry, and repurposing it would smuggle a second public-contract change into a display fix.

## Scope check

- Over-scope: none. `agent_workflows/cli.py` carries `_find_type_records`, `_find_prompt_lane_status` and `_run_find`, which are the reader site, the precedent, and the four output surfaces respectively. `tests/test_find_prompts_lane_status.py` is the dedicated test module for this exact surface and is where F-10's coverage hole lives.
- Under-scope: `agent_workflows/prompts.py`, `agent_workflows/selectors.py` and `agent_workflows/prompts_index.py` are deliberately NOT declared. This plan CONSUMES `prompts.read_metadata_id6` and `selectors.filename_slot_id6` unchanged and mirrors `prompts_index`'s precedence; it edits none of them. If the executor concludes a reader must change, that is a scope change: stop, record it, and re-declare rather than editing an undeclared file, because both readers are shared with `attention`, `artifact_rename` and `runner_shared`.

## Required tests / validation

- `python3 -m pytest` run BARE, with the pasted `N passed` summary line, against a pre-execution baseline captured the same way, so a pre-existing failure is not mistaken for a regression.
- Targeted runs of `tests/test_find_prompts_lane_status.py`, `tests/test_find_filters.py`, `tests/test_find_single_read.py` and `tests/test_cli_find.py`: the second covers the `--id`/`--set` filter surface this plan changes, and the third asserts the single-read property F-13 requires be preserved.
- `python3 -m agent_workflows check prompts` and `python3 -m agent_workflows index prompts --check`, both conforming, because both consume prompt identity.
- Real end-to-end `aw find` invocations on all four surfaces, with actual output pasted rather than described, including a non-prompt type capture proving no other type's rendering moved.
- `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` clean before any terminal transition.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is a deliberate finding rather than an omission. Approved spec `uonrjg` A10 governs how the id6 cell is STYLED and this plan keeps producing it through `cli._find_status_and_id6`, so the styling contract is satisfied unchanged. The implemented naming spec `20260817-2147-01-uniform-artifact-naming-grammar` already states that a prompt's id6 is declared in its metadata comment "rather than as a `- Id:` bullet"; this plan makes `find` conform to that existing statement rather than changing it. No `.spec.md` path appears in `- Scope-Paths:`, consistent with that.
- NO DOCUMENTATION CHANGE IS REQUIRED. `.aw/records/prompts/README.md` already asserts the behavior this plan delivers ("it is how `aw find` resolves it"), so the document is currently ahead of the code and becomes accurate when this lands. `docs/cli-human-guide.md` and `docs/cli-output-contract.md` describe `find`'s output modes and empty states, neither of which this plan changes. If the executor finds a doc statement that becomes false, that is a scope change to declare, not a silent edit.

## Open questions

### OQ-01: Should `aw find prompts --id <id6>` match a filename-slot-only id6, or only a declared one?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-02 PROPOSES matching both sources, because that is the precedence `prompts_index.scan_prompts` already ships and because the alternative would answer "no such prompt" for a file whose name visibly contains the id6 the caller typed. The cost is stated rather than hidden: a filename slot is a WEAKER identity claim than a declaration (which is exactly why `selectors.id6_ownership` separates `declared` from `slot-only`), so a filter accepting it is slightly more permissive than one that does not. Measured, the distinction is nearly moot for `--id` on today's corpus: all 17 prompts carry a comment `Id:`, so the slot only ever supplies a value for a prompt whose comment is missing, which no tracked prompt currently is. The reviewer may prefer declaration-only for strictness; that changes one clause in E-02 and V-02's evidence, not the design.
- Carrier-Declined: NOT BLOCKING and owed to no future item, because both branches are implemented inside this plan's own E-02 and neither leaves residual work. V-02 demands pasted per-source resolution evidence, so whichever branch ships is recorded as measured behavior rather than as an intention. Filing an item would imply work outlives this plan, and it does not.

### OQ-02: Is the `--agent`/`--json` `data.matches` string change acceptable without a version bump?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: E-05 proposes yes. Those strings currently contain a dash where an id6 belongs, so a consumer parsing the id6 out of them reads a placeholder today and a real value after; the change makes the field correct rather than incompatible, and the record's SHAPE (keys, types, envelope) is untouched. The plan judges a bump unwarranted for a field whose current value is wrong. If the reviewer disagrees, the alternative is to state the change in a CHANGELOG entry, which is a one-line addition to E-05 and would require declaring `CHANGELOG.md` in `- Scope-Paths:`.
- Carrier-Declined: NOT BLOCKING and carrying no residual work under either answer. E-05 already REQUIRES the before/after machine captures and schema validation that make the change visible and reviewable; if the reviewer wants it announced, that is one edit to this plan before execution plus a declared path, not a follow-up item. A pre-filed carrier would assert debt the reviewer may decide does not exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted test run showing the NEW id6-cell and filter assertions FAILING against unmodified HEAD, with each failure naming the `-` it received, and the 15 pre-existing tests still passing in the same run. A test written after the fix proves nothing, so the failing run must be shown FIRST. Plus the recorded behavior of the pre-existing `prnot-` fixture row under the new assertion, stated explicitly rather than skipped.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted per-prompt resolution output over all 17 live prompts naming WHICH SOURCE supplied each id6, showing (i) `oujnft` and `exnwoz` resolved from the COMMENT with their filename slot `None`, (ii) a legacy `YYYYMMDD-HHMM-NN-<slug>` name resolving to `None` rather than to the slug word `parse_clustered` would hand back, and (iii) which branch of OQ-01 shipped. Plus a shown-by-reading confirmation that the function takes the already-read text and opens no file, since F-13 makes that a correctness property and not a preference.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: three separate proofs, each pasted. (i) `aw find prompts` showing 17 real id6 values and zero dashes. (ii) `aw find prompts --id la0gje` and `aw find prompts --set plainlang` each returning exactly one correct row, where both return zero at HEAD. (iii) NON-REGRESSION for other types: `aw find reviews`, `aw find walkthroughs`, `aw find comms` and `aw find specs` captured before and after and shown byte-identical, which is what proves the type gate holds and that the 416 slot-carrying reviews of F-9 did not start claiming their subjects' id6s. A pass on (i) alone is insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: before/after collision-surface output for a bare-id6 query resolving to a prompt, the re-measured `selectors.id6_ownership` verdict for all 17 prompts, and an EXPLICIT verdict of one of: no-op (with the reason the token-keyed logic is unaffected), true finding (with the id6 of the backlog item filed), or defect in this change (with the fix). A silent "no new warnings appeared" is not sufficient evidence; the measurement must be shown.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: before/after captures of all four `find` surfaces for one prompts query: the human table, `--paths` shown BYTE-IDENTICAL, and `--agent`/`--json` shown changed in `data.matches` AND accepted by the schema validator. Plus the explicit written statement that the machine `matches` strings change from dash to id6, so a consumer is warned.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted, alongside the pre-execution baseline captured the same way, so any failure is shown pre-existing rather than introduced. Plus conforming output from `check prompts` and `index prompts --check`, a conforming `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` reporting zero findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-06 in order, respecting the declared `Depends on` edges; commit
only the two paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner
output for every claim of a passing test; and verify each `V-*` in a separate pass from the `E-*` that
produced it. Do NOT mark this plan executed or move it to `.aw/records/plans/executed/` until every
`V-*` carries concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms.

Backlog item `y0t9u7` is this plan's origin (`- From-Backlog: y0t9u7`) and its `- Blocks-Release: next`
gate is inherited above, so the release gate travels with the work and is not re-decided here.
