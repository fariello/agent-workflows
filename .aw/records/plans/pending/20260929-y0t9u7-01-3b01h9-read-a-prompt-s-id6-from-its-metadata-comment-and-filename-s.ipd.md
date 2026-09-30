# IPD: Read a prompt's id6 from its metadata comment and filename slot so aw find prompts stops printing a dash

- Date: 2026-09-29
- Kind: child
- Concern: `aw find prompts` renders `-` in the id6 column for ALL 17 tracked prompts, and `aw find prompts --id <id6>` returns ZERO rows for an id6 the tree demonstrably holds. The generic branch of `cli._find_type_records` derives a record's id6 from exactly one reader, `selectors._read_id`, which knows two dialects (a `- Id:` bullet matched by `selectors._ID_RE`, and a case-sensitive YAML `id:` scalar). A prompt has NEITHER BY CONTRACT: `.aw/records/prompts/README.md` states the prompt's `Id:` lives in the single leading HTML comment and is "never a `- Id:` bullet, which would render as visible text above the prompt body", and adds "YAML front-matter is NOT permitted". So the one reader `find` consults is guaranteed to miss, `raw_id` is `None` for every prompt, and the display falls to its `"-"` placeholder while the same branch's `explicit_id` filter compares against that same dead value. The data is fine: `prompts_index.scan_prompts` already resolves all 17 through `meta.get("Id") or fn_id6`, and `attention._prompts_record` already reads `prompts.read_metadata_id6`. `find` is the only prompts-facing reader never taught either source, even though it WAS already taught a prompts special case for the neighboring status column (`cli._find_prompt_lane_status`).
- Scope: Teach `aw find`'s generic branch to resolve a prompt's id6 from the two sources the purity contract DOES sanction, in the precedence `prompts_index.scan_prompts` ships for its FIRST source (metadata comment) and with a GUARDED second source (`selectors.filename_slot_id6`, which refuses a legacy name's slug word where `prompts_index`'s raw `parse_clustered(...).group("id6")` would accept it), so the id6 column is populated and `--id` matches. Fix the `--set` filter in the same reader for the same root cause (a prompt's `Set:` is in the same comment, so `selectors._read_setid` misses it and `aw find prompts --set plainlang` returns zero rows against a prompt whose filename setid IS `plainlang`), using the comment then `check_engine._filename_setid`, whose HHMM guard is the setid twin of the slot guard. THE PROMPT-AWARE READER MUST BE CONSULTED BEFORE `selectors._read_id`/`_read_setid`, NOT AFTER, because for a prompt those readers are not merely silent but WRONG-CAPABLE: a prompt body legitimately quoting a `- Id:`/`- Set:` bullet before its first `##` heading is read as a declaration (measured), and a prompt has no sanctioned bullet at all. Does NOT widen `selectors._ID_RE`, does NOT route `selectors.resolve`'s id6 rule through a whole-file read, does NOT change which artifacts MATCH for any type, does NOT touch the status column, and does NOT change any non-prompt type's id6 or setid rendering.
- Scope-Paths: agent_workflows/cli.py, tests/test_find_prompts_lane_status.py
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: y0t9u7
- Blocks-Release: next
- Set: y0t9u7
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3b01h9

## Workflow history

- 2026-09-30 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-801 (HIGH, fixed), PR-802 (HIGH, fixed), PR-803 (MEDIUM, fixed), PR-804 (MEDIUM, fixed), PR-805 (MEDIUM, fixed), PR-806 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-y0t9u7-01-3b01h9-read-a-prompt-s-id6-from-its-metadata-comment-and-filename-s.review.md`. The plan's direction and its purity-contract reasoning both survive scrutiny, and every one of its 14 findings reproduced. Review found two errors of MECHANISM, both in E-02/E-03. FIRST, the prescribed FALLBACK ordering (`selectors._read_id` primary, prompt reader second) is unsafe for prompts specifically: measured, a prompt body quoting a `- Id: aaa111` bullet before its first `##` heading is read by `_read_id` as a DECLARATION, so a fallback would print a quoted example as the prompt's identity in exactly the corpus (prompts about the metadata convention) where it is most likely to appear. Prompt-first is now mandated and the reason recorded. SECOND, the `Set:` half named no reader, and the obvious symmetric choice is a trap `prompts_index` itself falls into: its `fn_set` is the RAW `parse_clustered(...).group("set")`, which returns `'1958'` for a legacy `YYYYMMDD-HHMM-NN-<slug>` name (measured); `check_engine._filename_setid` exists with exactly that HHMM guard and is now named. The same measurement corrected the plan's "mirror `prompts_index`'s precedence" premise for the id6 half too: `prompts_index`'s `fn_id6` is also the RAW group, which returns `'prompt'` for that legacy name, so the plan's own F-6 contradicts its own E-02 instruction to mirror that module. Two coverage gaps were also closed: no fixture id6 in the existing test module can reach the filename-slot branch at all (all seven are all-letters, which `_HAS_DIGIT_RE` rejects), and V-05's demand that `--json` be "accepted by the schema validator" is unsatisfiable as written because that surface is a different shape (`command`/`exit_code`, not `cmd`/`kind`) and `agent_schema.validate_agent_record` rejects it by construction.
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

- [ ] E-01 EXTEND `tests/test_find_prompts_lane_status.py` WITH FAILING COVERAGE FOR THE id6 CELL, asserting `tokens[2]` for every prompt its fixture already writes (the row format is `glyph  status  id6  path`, verified by splitting a rendered line, so `tokens[2]` is the id6 cell), since that fixture writes a comment `Id:` and a conformant clustered filename and therefore already has everything needed for the COMMENT path. Add the four cases the current fixture does NOT cover, because each is a distinct source-resolution path: (a) a prompt with a comment `Id:` AND a matching filename slot, (b) a prompt with a comment `Id:` and a LEGACY `YYYYMMDD-HHMM-NN-<slug>` filename that has no identity slot at all, (c) a prompt with NO metadata comment whose id6 exists only in the filename slot, and (d) a prompt with a comment `Id:` whose BODY ALSO QUOTES a `- Id:`/`- Set:` bullet above its first `##` heading, which is the case E-03's ordering exists for and the one an unguarded fallback gets wrong. Also add the two filter cases (`--id`, `--set`). MIND TWO TRAPS IN THE EXISTING FIXTURE, both measured at review. FIRST, its `not-executed` lane id6 is the six-character string `prnot-`, which `artifact_core.ID6_RE` REJECTS (`ID6_RE.match('prnot-')` is None) and which `artifact_naming.parse_clustered` therefore refuses for that row's whole filename; use a valid id6 for any NEW row rather than copying that pattern, and state in the evidence what the pre-existing `prnot-` row resolves to so a reader is not surprised later. SECOND, AND THIS IS WHY CASE (c) NEEDS A NEW FIXTURE ROW RATHER THAN AN ASSERTION ON AN EXISTING ONE: not one of the seven fixture id6s (`prpend`, `prexec`, `prreus`, `prsupe`, `prnot-`, `prmdiv`, `prmnol`) can reach the filename-slot branch at all, because `selectors.filename_slot_id6` requires the slot token to CONTAIN A DIGIT and all seven are all-letters (measured: `filename_slot_id6` returns `None` for every one). A case-(c) row whose id6 is all-letters would therefore assert `-` and pass both before and after the fix, proving nothing; the new row MUST use a digit-bearing id6 (the module's own walkthrough fixture uses `wt0001`, which does resolve). State this in the evidence, because it is the same class of silent-green hole F-10 records.
  - Depends on: none
  - Expected outcome: a pasted test run showing the new assertions FAILING against HEAD, each failure naming the dash it received, plus the 15 pre-existing tests still passing, and an explicit statement that the case-(c) row's id6 is digit-bearing with the measured `filename_slot_id6` verdict for it.
  - Execution state: pending

### Task group 2: the reader, matching the precedence that already ships

- [ ] E-02 ADD A PROMPTS id6 READER to `cli.py` as the exact structural sibling of the existing `cli._find_prompt_lane_status`, which is the precedent for a prompts special case in this branch and returns `None` for every other type. Resolve comment-first, slot-second: FIRST `prompts.read_metadata_id6(text)`, which reads the first line only so a body-quoted `Id:` is never taken as a declaration, THEN `selectors.filename_slot_id6(path)`. Do NOT re-implement either reader and do NOT parse the comment inline; `prompts.read_metadata_id6` is documented as the one in-file reader and `filename_slot_id6` carries the slug-word guard F-6 measures as necessary. DO NOT "MIRROR `prompts_index.scan_prompts`" LITERALLY FOR THE SECOND SOURCE, and this is a correction to an earlier draft of this plan rather than a nicety: that module's `fn_id6` is the RAW `parse_clustered(...).group("id6")` with no guard, which F-6 measures returning the slug word `'prompt'` for a legacy `YYYYMMDD-HHMM-NN-<slug>` name. Copying it would manufacture an identity claim, which is precisely what `filename_slot_id6` exists to refuse, so this plan mirrors only its FIRST source (the comment) and its ORDER, never its second reader. Take the ALREADY-READ `text` as a parameter rather than re-opening the file: the generic branch reads each record exactly once and IPD `qfpnrm` removed a measured double read (1240 opens for 620 records) from this very layer, so adding a second open would reintroduce the defect backlog `59t9x5` closed. The `path` is already in hand at the call site (the loop variable `p`), so passing it costs no I/O.
  - Depends on: none
  - Expected outcome: a pure function plus pasted output resolving all 17 live prompts naming which source supplied each, explicitly showing that `oujnft` and `exnwoz` resolve from the COMMENT (their filename slot being `None`) and that a legacy-named prompt with no comment resolves to `None` rather than to a slug word, contrasted against `prompts_index.scan_prompts`'s `'prompt'` for the same name so the divergence is deliberate and recorded.
  - Execution state: pending

- [ ] E-07 ADD THE PROMPTS `Set:` READER AS A SEPARATE SIBLING, not as a clause of E-02, because it resolves a DIFFERENT field from a DIFFERENT pair of sources and needs its own guard evidence. FIRST the metadata comment's `Set:` (read through `prompts_index._parse_metadata_comment`, which is the established reader for comment fields other than `Id:` and is already imported this way by `check_engine.check_prompt_content`), THEN the filename setid group read through `check_engine._filename_setid`, NOT through a bare `parse_clustered(...).group("set")`. THE RAW GROUP IS A MEASURED TRAP EXACTLY AS ITS id6 TWIN IS: it returns `'1958'` for `20260810-1958-01-prompt-purity-lint.prompt.md`, because a legacy name's HHMM occupies the setid position without being one, and `_filename_setid`'s docstring records that reading `2147` as a setid "would invent findings on legacy names". `prompts_index.scan_prompts` uses the raw group here too (`fn_set`), so it is again a precedent for the ORDER and not for the reader. Measured on today's corpus, only 1 of 17 prompts declares a comment `Set:` while 17 of 17 have a readable filename setid, so unlike the id6 case the SLOT is the load-bearing source here and the comment is the rare one; that asymmetry is why the two fields get two items.
  - Depends on: none
  - Expected outcome: a pure function plus pasted per-prompt output over all 17 live prompts showing the source of each setid, the 1/17 versus 17/17 split, and `None` (not `'1958'`) for a legacy-named prompt, contrasted against the raw group's `'1958'` for the same name.
  - Execution state: pending

- [ ] E-03 WIRE BOTH READERS INTO THE GENERIC BRANCH of `cli._find_type_records` at the single place `raw_id` is computed, so ONE value feeds all three consumers: the `explicit_id` comparison, the `id6 = raw_id or "-"` display, and (for the setid twin) the `explicit_set` comparison. THE PROMPT READER IS CONSULTED FIRST AND `selectors._read_id` SECOND, which REVERSES what an earlier draft of this plan prescribed, and the reversal is load-bearing rather than stylistic. Measured at review: `selectors._read_id` applied to a prompt whose BODY quotes a `- Id: aaa111` bullet ANYWHERE BEFORE its first `##` heading returns `aaa111`, because `selectors.metadata_region`'s bullet dialect bounds the region at the first `##` and a prompt legitimately has prose above that point (5 of 17 live prompts contain no `##` heading at all, so for them the region is the WHOLE FILE). A prompt has no sanctioned `- Id:` bullet BY CONTRACT, so for this type that reader cannot be right and can be WRONG, and a fallback ordering would print a quoted example as the prompt's own identity in exactly the corpus most likely to contain one: a prompt about the metadata convention. Prompt-first makes the sanctioned source win and leaves the unsanctioned reader as a harmless last resort that no tracked prompt reaches (measured: 0 of 17 contain a `- Id:` or `- Set:` bullet today, so this reordering is a NO-OP on the live corpus and a correctness guard against the next prompt authored). DO THE SAME FOR `--set` with E-07's reader, on the same ordering and for the same reason (the identical measurement holds: a body-quoted `- Set: bogusset` is read as a declaration). THE PROMPT READERS MUST BE TYPE-GATED, returning `None` for every non-prompt type exactly as `_find_prompt_lane_status` does, so `walkthroughs` (12 of 24 with no readable `- Id:`), `comms` (7 of 7), `specs` (19 of 38) and `reviews` (519 of 519, of which 452 carry a filename slot holding their SUBJECT's id6) are untouched. That last population is the reason this must not be generalized: a review's slot id6 is its subject's by documented design (`.aw/records/reviews/README.md`), so printing it as the review's own identity would assert an identity claim D140 forbids.
  - Depends on: E-02, E-07
  - Expected outcome: pasted `aw find prompts` output showing 17 real id6 values, pasted `--id la0gje` and `--set plainlang` each returning exactly one row, pasted proof that a prompt whose body quotes a `- Id:` bullet renders its COMMENT id6 and not the quoted one, and pasted `aw find reviews`/`aw find walkthroughs`/`aw find comms`/`aw find specs` output proving byte-identical rendering to a pre-change capture.
  - Execution state: pending

### Task group 3: the consequences a populated column has elsewhere

- [ ] E-04 MEASURE AND REPORT THE COLLISION-SURFACE CONSEQUENCE, because populating the id6 changes what `cli._detect_id6_collisions` can see and this plan must state whether that is a fix, a risk, or a no-op rather than leaving it to be discovered. THE FACT AT AUTHORING: that function keys on the SELECTOR TOKEN and consults `selectors.id6_ownership`, not on the rendered cell, so this change should be a no-op for it; but `id6_ownership` itself returns `reference` for `oujnft` and `exnwoz` (measured), meaning those two prompts are currently INVISIBLE to claim detection while the other 15 return `slot-only`. Re-measure both facts after the wiring, state whether any NEW warning appears on any query, and if one does, determine whether it is a TRUE collision (a data problem to file) or a false positive (a defect in this change, which must then be fixed before proceeding). Do NOT change `id6_ownership`: it is a whole-file ownership predicate shared with `runner_shared` and widening it is a separate contract decision.
  - Depends on: E-03
  - Expected outcome: a before/after comparison of collision output for a bare-id6 query against a prompt, the re-measured ownership verdicts for all 17, and an explicit verdict of no-op / true-finding-filed / defect-fixed.
  - Execution state: pending

- [ ] E-05 CONFIRM THE `--paths` AND MACHINE SURFACES ARE CONSISTENT WITH THE HUMAN ONE, since `_run_find` has four output paths and this change touches a value only SOME of them carry. MEASURED AT REVIEW, because the plan's original premise about which surfaces change was wrong in a way that would have sent the executor hunting for a diff that does not exist: for a query WITH matches, `--agent` takes the early `all_paths` branch in `_run_find` and emits BARE PATHS ONLY (no envelope, no `data.matches`; `python3 -m agent_workflows find prompts --agent | grep -c schema` is `0`), so it is BYTE-IDENTICAL exactly as `--paths` is. Only `--json` carries `data.matches` on a matching query. The `--agent` envelope appears only when the query matches NOTHING, and that record has no `data` key at all (measured keys: `cmd`, `complete`, `evidence`, `exit`, `findings`, `kind`, `next`, `outcome`, `schema`, `verified`), which is itself worth capturing because `--id la0gje` goes from that empty-record shape to the bare-path shape. Paste all four surfaces before and after for one query, and state plainly that `--json`'s `data.matches` strings change shape (dash to id6) so a consumer keying on them is warned. DO NOT ASSERT THE `--json` RECORD AGAINST `agent_schema.validate_agent_record`: that validator checks the `aw.agent/v1` JSONL shape (`kind`, `cmd`, `exit`) and `--json` is a DIFFERENT surface rendered by `renderers.JsonRenderer` from `CommandResult.to_dict()` (keys `command`, `exit_code`, no `kind`), so the validator rejects it by construction and always has (measured: two errors, `Invalid kind: 'None'` and `Field 'cmd' must be a non-empty string`). Validate the `--agent` empty-match record with `agent_schema.validate_agent_record` (which is its real contract) and check `--json` by asserting the ENVELOPE KEYS are unchanged before and after, which is the property that actually matters here.
  - Depends on: E-03
  - Expected outcome: before/after captures of all four surfaces for one prompts query, with `--paths` AND `--agent` both shown byte-identical on a matching query, `--json`'s `data.matches` shown changed with its envelope keys shown unchanged, the `--agent` empty-match record shown validating under `validate_agent_record`, and the `--id la0gje` shape transition from empty-record to bare-paths stated.
  - Execution state: pending

### Task group 4: closeout

- [ ] E-06 RUN THE FULL REGRESSION GATE, capturing a pre-execution baseline BEFORE any edit in this plan lands and a post-change run after E-05, both with bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Additionally run `python3 -m agent_workflows check prompts` and `python3 -m agent_workflows index prompts --check`, because both consume prompt identity and a change to how it is read must leave them NO WORSE. STATE THE BASELINE FOR BOTH RATHER THAN ASSERTING A CLEAN RUN, because neither is clean at HEAD and an executor expecting "conforming" would misread a pre-existing condition as a regression it caused. Measured at review: `check prompts` prints `✓ CONFORMS  2 prompts checked` yet reports `errors 1` for `<collisions>` ("cross-tree collisions NOT checked by a per-type run"), a per-type-run artifact unrelated to this change; `index prompts --check` reports two `check.stale-index-missing` findings for `INDEX.json` and `INDEX.md`. Both exit `0`. The bar is therefore BYTE-IDENTICAL output before and after, not absence of findings. Then `aw ipd lint --phase pre-transition` on this plan and `aw sanitize --agent`. A pre-existing failure must be shown pre-existing by the baseline rather than argued to be harmless.
  - Depends on: E-05
  - Expected outcome: baseline and post-change `N passed` lines pasted side by side, the two prompts checks shown byte-identical before and after with their pre-existing findings named rather than hidden, a conforming pre-transition lint, and a clean sanitizer report.
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
- A REVIEW'S FILENAME SLOT HOLDS ITS SUBJECT'S id6 BY DESIGN, which bounds this fix to prompts. `selectors.id6_ownership`'s docstring quotes `.aw/records/reviews/README.md` ("`<id6>` is the REVIEWED ARTIFACT's id6, not a fresh identifier ... so the join survives a rename") and records that all measured review records declare `- Subject-Id:` and no own `- Id:`. Measured at authoring: 416 of 478 reviews had no declared Id but did have a filename slot id6; re-measured at review, 452 of 519. That population GROWS every time a review runs, which is why the bar E-03/V-03 set is a byte-identical before/after capture rather than either count. Generalizing a slot fallback to all types would print a foreign id6 as hundreds of reviews' own identity.
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
| F-7 | Two other modules already resolve this, and one of them is only PARTLY safe to copy | `prompts_index.scan_prompts` (`meta.get("Id") or fn_id6`) returns all 17; `attention._prompts_record` uses `prompts.read_metadata_id6`. BUT `scan_prompts`'s `fn_id6` is the RAW `parse_clustered(...).group("id6")` with no digit guard, and driving it over a legacy-named prompt with no comment returns `id6='prompt'`, `set_id='1958'` | Mirror its ORDER and its FIRST source only; use the GUARDED readers for the second. Corrected at review: this row previously said "mirror the shipped precedence", which F-6 already contradicted (E-02, E-07) |
| F-8 | The status column in this same branch already has a prompts special case | `cli._find_prompt_lane_status`, consumed beside the `raw_status` read | The fix is an established shape at an established site (E-02, E-03) |
| F-9 | A slot fallback generalized to all types would misreport 452 reviews | Re-measured at review: 519 of 519 reviews have no declared `- Id:`, and 452 of them carry a filename slot id6 holding their SUBJECT's id6 by documented design (the authoring figure 416 of 478 has drifted with the corpus, as a live-artifact count does) | The fallback MUST be type-gated to prompts (E-03). The BAR is the byte-identical before/after capture, not either number |
| F-10 | The dedicated test module never asserts the id6 cell | `tests/test_find_prompts_lane_status.py` asserts `tokens[1]` in every test; 15 passed against 17 broken rows | The coverage hole is the reason this shipped; E-01 closes it |
| F-11 | The existing fixture contains an invalid id6 | `ID6_RE.match('prnot-')` is None, so `parse_clustered` refuses that row's filename | A new test row must not copy that pattern; the existing row's behavior must be stated, not silently inherited (E-01) |
| F-12 | Two prompts are invisible to claim detection today | `selectors.id6_ownership` returns `reference` for `oujnft`/`exnwoz`, `slot-only` for the other 15 | E-04 must measure whether this change alters the collision surface, and report rather than assume |
| F-13 | The display layer previously double-read every record | `cli._find_type_records` docstring and `selectors`' comment (1240 opens for 620 records), closed by IPD `qfpnrm` from backlog `59t9x5` | The new reader must take the already-read `text`, never re-open (E-02) |
| F-14 | ONLY `--json` carries the rendered line on a matching query | Corrected at review. `_run_find`'s `all_paths` branch fires for `--agent` too and returns BEFORE any `CommandResult` is built (its own comment says so: "this branch returns before any `CommandResult` is built"); measured, `find prompts --agent` emits 17 bare paths and zero `schema` tokens. `--agent` shows an envelope only on an EMPTY match, and that record has no `data` key at all | Only `--json`'s `data.matches` changes. `--agent` is byte-identical on a matching query exactly as `--paths` is (E-05) |
| F-15 | For a prompt, `selectors._read_id`/`_read_setid` are not merely silent but WRONG-CAPABLE | Measured: on a prompt whose comment declares `ng0ga4` and whose body quotes `- Id: aaa111` / `- Set: bogusset` above the first `##` heading, `_read_id` returns `aaa111` and `_read_setid` returns `bogusset`. `selectors.metadata_region`'s bullet dialect ends at the first `##`, and 5 of 17 live prompts contain NO `##` heading, so for them the region is the whole file. A prompt has no sanctioned bullet by contract | The prompt reader must be consulted FIRST, not as a fallback. Reverses E-03's original instruction; a no-op on today's corpus (0 of 17 carry such a bullet) and a correctness guard for the next prompt authored (E-03, V-03) |
| F-16 | No fixture id6 in the dedicated test module can reach the slot branch | Measured `selectors.filename_slot_id6` -> `None` for all seven (`prpend`, `prexec`, `prreus`, `prsupe`, `prnot-`, `prmdiv`, `prmnol`), because `_HAS_DIGIT_RE` rejects an all-letter token; the module's walkthrough fixture `wt0001` DOES resolve | A comment-less fixture row written with an all-letter id6 would assert `-` and pass before AND after, proving nothing. The new row's id6 must be digit-bearing (E-01, V-01) |
| F-17 | `--json` cannot validate under `agent_schema.validate_agent_record`, by construction | `--json` is rendered by `renderers.JsonRenderer` from `CommandResult.to_dict()` (keys `command`, `exit_code`); the validator requires the `aw.agent/v1` JSONL shape (`kind`, `cmd`, `exit`). Measured on today's output: two errors, `Invalid kind: 'None'` and `Field 'cmd' must be a non-empty string` | V-05's original demand was unsatisfiable. Validate the `--agent` record against it and check `--json` by envelope-key stability instead (E-05, V-05) |
| F-18 | Neither prompts checker is clean at HEAD | `check prompts` prints `✓ CONFORMS  2 prompts checked` yet `errors 1` for `<collisions>` ("cross-tree collisions NOT checked by a per-type run"); `index prompts --check` reports two `check.stale-index-missing` rows. Both exit `0` | The bar is byte-identical before/after, not absence of findings; an executor expecting clean would misattribute a pre-existing condition to this change (E-06, V-06) |

## Proposed changes (ordered, validatable)

1. Extend `tests/test_find_prompts_lane_status.py` with failing id6-cell and filter coverage, plus the legacy-name, no-comment (digit-bearing id6) and body-quoted-bullet rows (E-01).
2. Add the type-gated prompts id6 reader in `cli.py`, comment-first then GUARDED filename slot, consuming the already-read text (E-02).
3. Add the type-gated prompts setid reader, comment-first then `check_engine._filename_setid` (E-07).
4. Wire both into the single `raw_id`/`raw_set` computation in the generic branch, PROMPT READER FIRST (E-03).
5. Measure the collision-surface consequence and report a verdict (E-04).
6. Confirm all four output surfaces, with the `--json`-only `matches` change stated explicitly (E-05).
7. Run the full regression gate plus the two prompts-specific checkers against their measured baselines (E-06).

## Deferred / out of scope (with reason)

- POPULATING THE id6 COLUMN FOR THE OTHER GENERIC TYPES THAT RENDER `-`. Measured at authoring and re-confirmed at review: `walkthroughs` 12 of 24, `comms` 7 of 7, `specs` 19 of 38 have no readable `- Id:`. Each is a DIFFERENT question with a different answer (a legacy spec predating the spec id6 cutover legitimately HAS no id6; a comms record has none at all; a walkthrough may simply be unconverted), so answering them together would make one change to several contracts at once on evidence gathered for none of them.
  - Carrier-Declined: No defect is established for those types by this plan, so there is nothing to carry. The prompts case is a defect precisely because the identity DEMONSTRABLY EXISTS in two places and the reader consults neither; for a legacy spec or a comms record the dash may be the TRUTHFUL rendering of a genuine absence, and filing an item asserting otherwise would record a fault this plan has not measured. Determining which of those dashes are truthful requires its own measurement pass per type, and an item filed before that pass could not be closed on evidence. If a maintainer wants that sweep, it is a new backlog item with its own numbers.
- CHANGING `selectors._ID_RE`, `selectors._read_id`, or `selectors.resolve`'s id6 rule so prompts resolve by identity rather than by filename substring. Today `aw find <prompt-id6>` succeeds only via `MATCH_SUBSTRING`, the documented last resort, so a bare-token prompt query works by accident of the filename rather than by identity.
  - Carrier-Declined: This is a PROHIBITION on this plan rather than deferred work, and the code states the prohibition itself: the comment above `selectors.declares_id6` records that routing the id6 rule through a whole-file read "would change which records `aw find` MATCHES for every type and every front-matter kind", and the `_STATUS_RE` note calls such an edit "a MATCHING-BEHAVIOR decision, not a cleanup". The current behavior is also NOT WRONG, merely indirect: the query returns the correct single file. Filing an item would assert the repository intends to change selector matching semantics for every type, which no evidence here supports and which is a maintainer's call about a public contract.
- MAKING `selectors.id6_ownership` see a prompt's comment-declared id6, which would move `oujnft` and `exnwoz` from `reference` to a claiming verdict.
  - Carrier-Declined: Nothing is owed because this plan measures the question rather than leaving it open: E-04 REQUIRES a before/after measurement of the collision surface and an explicit verdict, and V-04 refuses it without one. If that measurement finds a TRUE collision the item is filed BY E-04 with the evidence attached, which is a better record than a guessed item filed now. `id6_ownership` is additionally a whole-file ownership predicate shared with `runner_shared`, so widening it is a contract change for every consumer and must not ride along inside a display fix.
- GIVING `--check` MEANING ON `find`. A comment at the `CommandResult` site in `_run_find` records that `find`'s parser accepts `--check` and "deliberately leaves that flag INERT rather than quietly giving it meaning (paw8so F-14)".
  - Carrier-Declined: A standing decision this plan declines to overturn, not deferred work. No finding here measures a fault on that flag, so there is no defect to carry, and repurposing it would smuggle a second public-contract change into a display fix.

## Scope check

- Over-scope: none. `agent_workflows/cli.py` carries `_find_type_records`, `_find_prompt_lane_status` and `_run_find`, which are the reader site, the precedent, and the four output surfaces respectively. `tests/test_find_prompts_lane_status.py` is the dedicated test module for this exact surface and is where F-10's coverage hole lives.
- Under-scope: `agent_workflows/prompts.py`, `agent_workflows/selectors.py`, `agent_workflows/prompts_index.py` and `agent_workflows/check_engine.py` are deliberately NOT declared. This plan CONSUMES four existing readers unchanged (`prompts.read_metadata_id6`, `selectors.filename_slot_id6`, `prompts_index._parse_metadata_comment`, `check_engine._filename_setid`) and mirrors only `prompts_index`'s ORDER; it edits none of them. IMPORTING A LEADING-UNDERSCORE HELPER FROM `check_engine` AND `prompts_index` IS DELIBERATE AND HAS IN-TREE PRECEDENT: `check_engine.check_prompt_content` itself does `from agent_workflows.prompts_index import _parse_metadata_comment`, so a cross-module private import for exactly this purpose is the established pattern rather than a new liberty. The alternative, re-implementing either guard locally, is what F-6 and F-7 measure as the actual hazard. If the executor concludes a reader must CHANGE, that is a scope change: record it and re-declare rather than editing an undeclared file, because these readers are shared with `attention`, `artifact_rename`, `check_engine` and `runner_shared`. A same-file edit that is genuinely required is made and then JUSTIFIED at finalize with a `--scope-reason`, not silently.

## Required tests / validation

- `python3 -m pytest` run BARE, with the pasted `N passed` summary line, against a pre-execution baseline captured the same way, so a pre-existing failure is not mistaken for a regression.
- Targeted runs of `tests/test_find_prompts_lane_status.py`, `tests/test_find_filters.py`, `tests/test_find_single_read.py` and `tests/test_cli_find.py`: the second covers the `--id`/`--set` filter surface this plan changes, and the third asserts the single-read property F-13 requires be preserved.
- `python3 -m agent_workflows check prompts` and `python3 -m agent_workflows index prompts --check`, both BYTE-IDENTICAL to their pre-change output, because both consume prompt identity and NEITHER is clean at HEAD (F-18). "Conforming" is the wrong bar here and asserting it would be a false report.
- Real end-to-end `aw find` invocations on all four surfaces, with actual output pasted rather than described, including a non-prompt type capture proving no other type's rendering moved, and the body-quoted-bullet ordering proof V-03(iii) requires.
- `aw ipd lint --phase pre-transition` conforming and `aw sanitize --agent` clean before any terminal transition.

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and that is a deliberate finding rather than an omission. Approved spec `uonrjg` A10 governs how the id6 cell is STYLED and this plan keeps producing it through `cli._find_status_and_id6`, so the styling contract is satisfied unchanged. The implemented naming spec `20260817-2147-01-uniform-artifact-naming-grammar` already states that a prompt's id6 is declared in its metadata comment "rather than as a `- Id:` bullet"; this plan makes `find` conform to that existing statement rather than changing it. No `.spec.md` path appears in `- Scope-Paths:`, consistent with that.
- NO DOCUMENTATION CHANGE IS REQUIRED. `.aw/records/prompts/README.md` already asserts the behavior this plan delivers ("it is how `aw find` resolves it"), so the document is currently ahead of the code and becomes accurate when this lands. `docs/cli-human-guide.md` and `docs/cli-output-contract.md` describe `find`'s output modes and empty states, neither of which this plan changes. If the executor finds a doc statement that becomes false, that is a scope change to declare, not a silent edit.

## Open questions

### OQ-01: Should `aw find prompts --id <id6>` match a filename-slot-only id6, or only a declared one?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW (2026-09-30, reviewer's own authority; recorded as decision D-3 in the typed review record): MATCH BOTH SOURCES, comment first then the GUARDED slot, as E-02 proposes. Three pieces of evidence settle it without a maintainer turn. FIRST, the strictness the alternative would buy is already bought by the GUARD: `selectors.filename_slot_id6` refuses any slot token that is not a real id6, so the permissiveness at issue is not "accept a slug word" (F-6's hazard, which is closed) but only "accept a real id6 that a prompt failed to declare in its comment". SECOND, that residual case is EMPTY on today's corpus (measured: comment `Id:` present 17 of 17), so declaration-only and both-sources return byte-identical answers for every tracked prompt and the choice is about the NEXT prompt, not this one. THIRD, for that next prompt the tree already has a policy and it is not strictness: `prompts.inject_metadata_id6`'s docstring states that a file with no leading comment is returned UNCHANGED and that "the id6 then lives in the FILENAME only, which is stated plainly rather than silently repaired". A filter that refused such a prompt would make `find` disagree with the writer that deliberately created it. Rejected alternative: declaration-only, which would answer "no such prompt" for a file whose name visibly contains the typed id6 and whose id6 the repository's own writer put there on purpose.
- Carrier-Declined: RESOLVED, so nothing is owed. The chosen branch is implemented in E-02 and its evidence is demanded by V-02, which requires the per-source resolution to be pasted rather than asserted. No residual work outlives this plan.

### OQ-02: Is the `--json` `data.matches` string change acceptable without a version bump?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW (2026-09-30, reviewer's own authority; recorded as decision D-4 in the typed review record): YES, no version bump and no CHANGELOG entry. The question's own premise NARROWED at review, which is most of the answer: F-14 measures that `--agent` does NOT carry `data.matches` on a matching query at all (it takes `_run_find`'s bare-path branch and returns before any `CommandResult` is built), so the blast radius is ONE surface, `--json`, not two. On that surface the record's SHAPE is untouched (measured envelope keys before the change: `changes`, `command`, `complete`, `data`, `diagnostics`, `evidence`, `exit_code`, `next_actions`, `schema`, `status`, `summary`, `verified`; `data` keys: `matches`, `paths`, `type`, `selectors`, `count`, `filters`), and `matches` is DOCUMENTED as the rendered human line rather than as a parsed field: `docs/cli-output-contract.md` describes `find`'s output modes and empty states and specifies no per-column contract on that string. A consumer wanting the id6 as a field has `paths` and can resolve it; one scraping the rendered line reads a placeholder today and a correct value after. Rejected alternatives: a CHANGELOG entry, which would require declaring `CHANGELOG.md` and announces a fix to a value that was simply wrong; and a version bump, which is unwarranted for correcting a placeholder inside a human-rendered string. Reversible: yes, and cheaply, since announcing it later costs one CHANGELOG line.
- Carrier-Declined: RESOLVED, so nothing is owed. E-05 requires the before/after `--json` capture and the envelope-key stability check, so the change is recorded as measured rather than assumed, and V-05 refuses it without that evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted test run showing the NEW id6-cell and filter assertions FAILING against unmodified HEAD, with each failure naming the `-` it received, and the 15 pre-existing tests still passing in the same run. A test written after the fix proves nothing, so the failing run must be shown FIRST. Plus two fixture facts stated explicitly rather than skipped: the recorded behavior of the pre-existing `prnot-` row under the new assertion, and the `selectors.filename_slot_id6` verdict for the case-(c) row's id6, proving it is digit-bearing and therefore actually exercises the slot branch rather than passing vacuously on a `-` both before and after.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted per-prompt resolution output over all 17 live prompts naming WHICH SOURCE supplied each id6, showing (i) `oujnft` and `exnwoz` resolved from the COMMENT with their filename slot `None`, (ii) a legacy `YYYYMMDD-HHMM-NN-<slug>` name resolving to `None` shown BESIDE `prompts_index.scan_prompts`'s `'prompt'` for the same name, so the DELIBERATE divergence from that module's second reader is recorded as measured rather than as an assumption this plan inherited and then had to correct, and (iii) which branch of OQ-01 shipped. Plus a shown-by-reading confirmation that the function takes the already-read text and opens no file, since F-13 makes that a correctness property and not a preference.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: four separate proofs, each pasted. (i) `aw find prompts` showing 17 real id6 values and zero dashes. (ii) `aw find prompts --id la0gje` and `aw find prompts --set plainlang` each returning exactly one correct row, where both return zero at HEAD. (iii) THE ORDERING PROOF: a prompt fixture whose comment declares one id6 and whose body quotes a DIFFERENT `- Id:` bullet above its first `##` heading, shown rendering the COMMENT value, plus the measured `selectors._read_id` return for that same text showing it would have returned the quoted value. Without this, the reordering E-03 mandates is asserted rather than demonstrated, and the reordering is the substantive correction review made. (iv) NON-REGRESSION for other types: `aw find reviews`, `aw find walkthroughs`, `aw find comms` and `aw find specs` captured before and after and shown byte-identical, which is what proves the type gate holds and that the 452 slot-carrying reviews of F-9 did not start claiming their subjects' id6s. A pass on (i) alone is insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted per-prompt setid resolution over all 17 live prompts naming WHICH SOURCE supplied each, showing (i) the measured 1-of-17 comment-`Set:` versus 17-of-17 filename-setid split, so the reader's precedence is recorded against real data rather than assumed symmetric with the id6 case, (ii) `None` and NOT `'1958'` for a legacy `YYYYMMDD-HHMM-NN-<slug>` name, shown BESIDE the raw `parse_clustered(...).group("set")` return for the same name so the guard is demonstrated to be doing work, and (iii) a shown-by-reading confirmation that the function takes the already-read text and opens no file, since F-13 makes that a correctness property.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: before/after collision-surface output for a bare-id6 query resolving to a prompt, the re-measured `selectors.id6_ownership` verdict for all 17 prompts, and an EXPLICIT verdict of one of: no-op (with the reason the token-keyed logic is unaffected), true finding (with the id6 of the backlog item filed), or defect in this change (with the fix). A silent "no new warnings appeared" is not sufficient evidence; the measurement must be shown.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: before/after captures of all four `find` surfaces for one prompts query: the human table changed, `--paths` AND `--agent` both shown BYTE-IDENTICAL on a matching query (because `--agent` takes the bare-path branch there and carries no `data.matches` at all), and `--json` shown changed in `data.matches` with its envelope key set shown unchanged. Plus the `--agent` EMPTY-match record for `--id la0gje` shown validating under `agent_schema.validate_agent_record`. Do NOT accept a claim that the `--json` record validates under that function: it cannot, by construction, and a `V-*` demanding an impossible proof is unsatisfiable rather than strict. Plus the explicit written statement that `--json`'s `matches` strings change from dash to id6, so a consumer is warned.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted, alongside the pre-execution baseline captured the same way, so any failure is shown pre-existing rather than introduced. Plus BYTE-IDENTICAL before/after output from `check prompts` and `index prompts --check`, with their pre-existing findings (the `<collisions>` per-type-run artifact and the two `check.stale-index-missing` rows) named in the evidence rather than omitted; a claim that either is "conforming" with no findings is a FALSE report against the measured baseline and must not be accepted. Plus a conforming `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` reporting zero findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A display-and-filter fix in ONE function of `cli.py` plus its dedicated test
module, adding two small type-gated readers so `aw find prompts` stops printing `-` for all 17 prompts and
so `--id`/`--set` stop answering "no matching prompts" for prompts that exist. No selector matching
semantics change, no prompt file is edited, and no shared reader is modified. REVIEW CHANGED TWO
MECHANISMS, both of which would have shipped a defect. FIRST, the reader ORDER is reversed: the prompt
reader now runs BEFORE `selectors._read_id`, because that reader does not merely miss a prompt's identity
but can return a WRONG one, reading a body-quoted `- Id:` bullet as a declaration (F-15, measured). SECOND,
the `Set:` half named no reader and the symmetric-looking choice was a trap: the raw filename group returns
`'1958'` for a legacy name, so `check_engine._filename_setid` and its HHMM guard are now named (F-7, E-07).
Review also corrected three premises the executor would otherwise have worked from: `--agent` does NOT
change on a matching query (F-14), `--json` cannot validate under the agent-record validator (F-17), and
neither prompts checker is clean at HEAD so the bar is byte-identical output rather than zero findings
(F-18).

SCOPE FENCE, A DECLARATION RATHER THAN A STOP. The intended surface is exactly the two paths in
`- Scope-Paths:` (`agent_workflows/cli.py`, `tests/test_find_prompts_lane_status.py`). An edit outside them
is to be MADE and then JUSTIFIED: `aw ipd finalize` refuses to complete without a `--scope-reason` for each
out-of-scope path and a `--scope-ack` for each declared-but-unmodified path, which is the reconciliation
this declaration exists to feed. Do not stop the run over a scope question. DO stop and report for a
genuinely unsafe condition: if any of the four consumed readers (`prompts.read_metadata_id6`,
`selectors.filename_slot_id6`, `prompts_index._parse_metadata_comment`, `check_engine._filename_setid`) is
ABSENT or has a changed signature at execution HEAD, this plan's whole mechanism is gone and improvising a
replacement would re-create the exact unguarded reads F-6 and F-7 measure as the hazard.

TWO SILENT-FAILURE MODES THIS PLAN IS BUILT TO CATCH, both measured. (a) A test that passes before AND
after: a comment-less fixture row with an all-letter id6 asserts `-` either way (F-16), which is why V-01
requires the `filename_slot_id6` verdict for that row. (b) A checker claimed "conforming" when it reports
findings and merely exits 0 (F-18), which is why V-06 requires the baselines side by side.

THE EXECUTOR MUST: perform E-01, E-02, E-07, E-03, E-04, E-05, E-06, respecting the declared `Depends on`
edges (E-03 now depends on BOTH E-02 and E-07); commit only the declared paths via
`aw commit <plan> -- <paths>`, never `git add -A` and never push; paste ACTUAL runner output for every
claim of a passing test, and never write a `V-*` `Observed evidence` block for something not observed;
and verify each `V-*` in a separate pass from the `E-*` that produced it.

LIFECYCLE TRANSITION (a post-gate step, not a checklist item). The terminal transition is obligatory but
its OWNER is conditional (`AW-LIFECYCLE-ROLE-001`): under a managed runner (`aw oc run` / `aw agy run`) the
RUNNER owns finalize and the executor must NOT call it, while for a hand-run execution the executor calls
`aw ipd finalize` after every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms. Do NOT hand-roll a `git mv` into
`.aw/records/plans/executed/`; that bypasses the scope reconciliation and the transition checks.

Backlog item `y0t9u7` is this plan's origin (`- From-Backlog: y0t9u7`) and its `- Blocks-Release: next`
gate is inherited above, so the release gate travels with the work and is not re-decided here.
