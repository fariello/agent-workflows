# IPD: parse the orchestrator child table robustly instead of silently guessing the Set order

- Date: 2026-08-31
- Kind: child
- Concern: `aw ipd execute-set` decides the order it would run a Set's children in by parsing the orchestrator's `## Child IPDs, sequence, and dependencies` table. That parser rejects 28 of the 46 orchestrator tables in this repository (60 percent) and then SILENTLY falls back to guessing a serial chain by Order number. The fallback is signalled only by a `cross_edges_source: legacy-inference` field; nothing warns the operator that their declared dependency table was thrown away. Today the guess usually matches because authors write plans in dependency order, so the defect is invisible until a Set declares an order that differs from its Order numbering, at which point the planner reports a confidently wrong sequence.
- Scope: Make the child-table parser handle the four measured real-world causes of rejection (inline pipes inside cells, a column count other than four, a parenthetical or prose comment in the Depends-on cell, and an `executed:<id6>` typed edge), and make every remaining rejection VISIBLE to the caller instead of silent. Excludes changing the fallback's conservative serial behavior, excludes the scheduler or any execution authority, excludes editing any orchestrator plan file, and excludes a new lint rule (see OQ-02).
- Scope-Paths: agent_workflows/ipd_set_plan.py, tests/test_ipd_set_plan.py
- Item-Dependencies: none
- Status: approved
- Set: setgraph
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 4ot0r6
- Approval: 2026-08-31, human ("approved"): Approved by the maintainer, verbatim: 'I would then have you fix the bug in the tool, even if that means you do the write ipd -> review -> approve -> execute.' Given after I measured and reported that 28 of 46 orchestrator child tables are rejected by the parser, and after the maintainer explicitly rejected the alternative of fixing the table inside the runprofile Set ('Why go back to backlog with this?' -> then, on seeing the blast radius, directing the fix into the tool). Scope authorized: the parser in ipd_set_plan.py only, no plan-file edits, no verb rename.

## Workflow history
- 2026-08-31 approved (aw set, --by-human): Approved by the maintainer, verbatim: 'I would then have you fix the bug in the tool, even if that means you do the write ipd -> review -> approve -> execute.' Given after I measured and reported that 28 of 46 orchestrator child tables are rejected by the parser, and after the maintainer explicitly rejected the alternative of fixing the table inside the runprofile Set ('Why go back to backlog with this?' -> then, on seeing the blast radius, directing the fix into the tool). Scope authorized: the parser in ipd_set_plan.py only, no plan-file edits, no verb rename.
- 2026-08-31 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored after a general (NOT `/plan-review`) read of the `runprofile` Set surfaced its child table being rejected. Measured the blast radius before scoping: 28 of 46 orchestrators are rejected, so the defect is in the TOOL, not in `runprofile`. The maintainer's decision was explicit: fix it in the tool rather than editing one Set's table, and carry it through write -> review -> approve -> execute in one pass.

## Goal

Make the Set planner trust the dependency table authors actually write, and say so out loud when it cannot, so it never reports a confidently wrong order.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: parse what authors actually write

- [x] E-01 Fix the CELL-SPLITTING bug: a cell containing an inline pipe inside backticks (for example `` `--format json|markdown` ``) splits into extra cells, so the fixed index `cells[3]` reads the wrong column and the whole table is rejected. MEASURED as the cause for 4 of the 28 rejections (`attnview`, `awrelease`, `awcmdsurf`, `awselect`), each of which uses the CANONICAL four-column header and is still rejected, which is why this is first. Locate the split at `_parse_orchestrator_child_table` (`agent_workflows/ipd_set_plan.py:163`, the `s.strip("|").split("|")` line). Split so that a pipe inside a backtick-quoted span does not create a column boundary. Do NOT write a general Markdown parser; handle the backtick case, which is the only one present in the corpus, and leave anything else to E-05's visible refusal.
  - Depends on: none
  - Expected outcome: a row whose cell contains `` `a|b` `` yields the same cell count as the header; `attnview`, `awrelease`, `awcmdsurf`, and `awselect` parse; no currently-parsing table changes its result.
  - Execution state: performed

- [x] E-02 Stop hard-coding the column INDEX. The parser reads Order from `cells[0]` and Depends-on from `cells[3]`, so any table with a column count other than four is rejected even when it is perfectly well formed. MEASURED as the cause for 12 rejections, at 3, 5, and 6 columns; the corpus contains 17 distinct header shapes, and the canonical four-column form is a minority at 18 of 46. Resolve the columns BY HEADER NAME instead: find the Order column and the Depends-on column from the header row. Accept the header spellings present in the corpus (`Depends on`, `Set dependencies`, `Item-Dependencies`) as the dependency column, matched case-insensitively; treat the first column named `Order` as the order column. If the header does not yield both columns, that is a visible refusal (E-05), not a silent fallback.
  - Depends on: E-01
  - Expected outcome: tables at 3, 5, and 6 columns parse when their header names the two required columns; the four-column canonical form still parses; a table whose header names neither column refuses visibly rather than silently.
  - Execution state: performed

- [x] E-03 Tolerate a PROSE COMMENT in the Depends-on cell. MEASURED as the cause for 12 rejections: authors write `none (parallelizable)`, `01 (consumes the rewritten strings)`, `09; D113 evidence`, `03 (04 precedes in Set order but is not a functional dep...)`, and `01 executed`. Every one of these states a machine-readable dependency and then explains it, which is good authoring, and the parser discards the whole table for it. Extract the leading dependency tokens and IGNORE a trailing parenthetical or a trailing clause after `;`. Be conservative in one specific way: only ignore trailing commentary, never a token that could itself be a dependency. If a cell mixes tokens and prose such that the dependency set is genuinely ambiguous, refuse visibly (E-05) rather than guessing, because a wrong edge is worse than a reported failure.
  - Depends on: E-02
  - Expected outcome: `none (parallelizable)` reads as no dependencies; `01 (consumes ...)` reads as Order 01; `09; D113 evidence` reads as Order 09; `01 executed` reads as Order 01; a genuinely ambiguous cell refuses visibly rather than producing a partial edge set.
  - Execution state: performed

- [x] E-04 Accept a TYPED `executed:<id6>` edge in the Depends-on cell. MEASURED in 2 rejections (`driverfin` uses `executed:p7peqf`, `tabcomp` uses `executed:bja8og`). This is the repository's own canonical `Item-Dependencies` grammar, so the planner rejecting it is the tool disagreeing with its own convention. CONSUME the shipped grammar rather than re-parsing it: `ipd_schema.parse_item_dependencies` and the runner's `parse_dependency_token` already handle these tokens (the runner resolves them at `oc_runipd.py:3343`). Map an `executed:<id6>` edge to the child with that `Id` when the target is a child of this Set; when it names a plan OUTSIDE the Set, it is not a Set-ordering edge and must be ignored for ordering purposes rather than treated as a parse failure, which is exactly how the runner treats an out-of-queue target.
  - Depends on: E-02
  - Expected outcome: `executed:<id6>` naming a sibling child produces the correct edge; naming a plan outside the Set is ignored for ordering without rejecting the table; the shipped grammar helper is called rather than a second tokenizer being written.
  - Execution state: performed

### Task group 2: never guess silently again

- [x] E-05 Make every remaining rejection VISIBLE. This is the item that matters most, and it is deliberately separate from the parsing fixes because it must hold even for a table no future parser understands. Today the caller cannot tell a parsed table from a guess except by reading `cross_edges_source`, and the human output prints that string with no explanation. Change the contract so that when the table is rejected the planner reports WHICH row and WHY, in both the human and `--agent` output. Keep the conservative serial fallback exactly as it is (it is correctly fail-safe; see `_parse_orchestrator_child_table`'s own docstring), and keep `cross_edges_source` byte-stable for existing consumers. The human snapshot must say plainly that the declared table was not used and name the reason; the JSON must carry a structured reason a checker can consume.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a Set whose table cannot be parsed prints an explicit warning naming the offending row and cause; `--agent` carries the same as structured data; the fallback ordering is unchanged; `cross_edges_source` keeps its existing values so nothing downstream breaks.
  - Execution state: performed

- [x] E-06 Add tests to `tests/test_ipd_set_plan.py` covering each measured cause with a REAL fixture shape drawn from the corpus, plus a corpus-wide regression assertion. Cases: inline-pipe cell (E-01); 3, 5, and 6 column tables (E-02); each of the four prose forms in E-03; `executed:<id6>` both in-Set and out-of-Set (E-04); and an unparseable table producing a VISIBLE reason plus an unchanged serial fallback (E-05). Add one test that parses every orchestrator in `.aw/records/plans/**` and asserts the parse-success count does not REGRESS below the post-fix number, so a future change cannot silently reintroduce mass rejection. Do NOT assert a specific total that will drift as plans are added; assert no-worsening against a computed baseline.
  - Depends on: E-05
  - Expected outcome: every measured cause has a failing-before/passing-after test; the corpus test guards against regression without being brittle to new plans; the suite passes bare.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE FALLBACK IS FAIL-SAFE AND MUST STAY. `_parse_orchestrator_child_table` returns `None` on an ambiguous table so the caller "conservatively serializes rather than guessing" (its own docstring). Serializing is the safe direction: it never invents parallelism. The defect is not the fallback, it is that the fallback is SILENT and that it triggers on 60 percent of well-formed tables.
- THE PLANNER CANNOT EXECUTE. `aw ipd execute-set` supports only `--plan-only` in this build: it "never launches a model or worktree, never mutates an authoritative record, and never grants execution authority (scheduling is a later Order)". So this bug currently produces a WRONG PREVIEW, not wrong execution. That bounds the severity and is why this plan is small and carries no release gate.
- THE HEADING IS SCHEMA-FIXED, THE COLUMNS ARE NOT. `ipd_schema.H_CHILD_IPDS` pins the section heading, and `aw ipd scaffold` emits the hint `(Order | File | What it does | Depends on)`. But no schema, linter, or check enforces the column layout, so 17 distinct header shapes exist and the parser silently requires exactly one of them. An unenforced convention that a parser depends on is the root cause.
- THE DEPENDENCY GRAMMAR IS ALREADY SINGLE-SOURCED. `ipd_schema.parse_item_dependencies` plus `check_engine.evaluate_ipd_dependencies` own the `executed:<id6>` grammar, and the runner consumes it (`oc_runipd.py:3343`). E-04 must call it, not re-tokenize.
- THE RUNNER ALREADY DOES THIS CORRECTLY, which is the strongest argument that the planner should. `oc_runipd.queue_sort_key` (`:3352`) orders by declared dependency DEPTH first and treats Set/Order as a mere tiebreaker, explicitly so that "Set/Order can no longer act as evidence that a dependency is satisfied". `aw oc run` reads the machine-readable field; `aw ipd execute-set` reads a hand-written table. Two sources of truth for one question is what GUIDING_PRINCIPLES P8 forbids.
- THE TWO SURFACES ARE SEPARATE. `ipd_set_plan` is reached only via `cli.py:9232` and `ipd_set_executor.py`; it does not feed the runner queue. So changing it cannot affect a live `aw oc run`, which keeps this plan's risk low.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `ipd_set_plan._parse_orchestrator_child_table:163` | 28 of 46 orchestrator child tables (60 percent) are rejected, and the planner then silently guesses. The guess currently matches often enough to hide the bug, because authors write plans in dependency order. | ran the shipped parser over every `.aw/records/plans/**/*.ipd.md` with a child table: 18 parse, 28 rejected |
| F2 | HIGH | same, the `split("|")` line | FOUR rejections use the CANONICAL four-column header and still fail, because an inline pipe inside backticks (`` `--format json\|markdown` ``) creates a phantom column and shifts `cells[3]`. This is the finding that proves authors are not at fault. | `attnview-00` row 03 splits into 5 cells; `cells[3]` becomes `markdown\`, ...` and fails `isdigit()`; same in `awrelease`, `awcmdsurf`, `awselect` |
| F3 | HIGH | same, `cells[0]`/`cells[3]` | The parser hard-codes column INDICES while the corpus contains 17 distinct header shapes at 3, 5, and 6 columns. Any author who adds a useful column (`Id`, `Layer`, `Phase`, `From-Backlog`) silently breaks their own Set's ordering. `runprofile-00` added `Id` and was rejected for exactly this. | 12 rejections attributable to column count; header-shape census across 46 files |
| F4 | MED | same, the dep-token loop | 12 rejections are authors writing a valid dependency AND explaining it: `none (parallelizable)`, `01 (consumes the rewritten strings)`, `09; D113 evidence`, `01 executed`. Punishing good authoring is a parser flaw, not an author error. | measured per-file offending token for each canonical-shape rejection |
| F5 | MED | same vs `ipd_schema` | 2 rejections use the repository's OWN `executed:<id6>` grammar (`driverfin`, `tabcomp`). The planner rejects the canonical dependency syntax that `aw check`, `aw ipd lint`, and the runner all accept. | `driverfin-00` dep cell `executed:p7peqf`; `tabcomp-00` `executed:bja8og`; grammar owned by `ipd_schema.parse_item_dependencies` |
| F6 | HIGH | `ipd_set_plan.run_execute_set` output | The failure is SILENT. The only signal is `cross_edges_source: legacy-inference`, printed without explanation in the human snapshot. An operator reviewing a Set has no way to know the sequence shown was inferred rather than read. This is the part that makes a wrong preview dangerous rather than merely wrong. | `aw ipd execute-set runprofile --plan-only` prints `Cross-IPD edges: legacy-inference` and a confident `Serial fallback order:` line with no warning |
| F7 | LOW | `aw ipd execute-set` naming | Separately from the parsing bug: the verb promises execution, cannot execute, and requires a `--plan-only` flag that reads as optional but is mandatory. The maintainer had never used it. Recorded as a finding only; a rename belongs to the command-surface owners (`0soncw` holds `command_surface.py`), NOT to this plan. | `--help` text ("required in this build"); `aw execute-set` is not a valid command, the verb is nested under `aw ipd` |
| F8 | LOW | `runprofile-00` (`3m0urk`) | The Set under review is a normal instance of F3, not a special case: it added an `Id` column. Its declared chain (01 -> 02 -> 03 -> 04 -> 05) happens to equal the inferred chain, so nothing is currently mis-ordered. No edit to that plan is needed once the parser is fixed, which is why this plan touches no plan file. | its header is `Order \| Id \| Child \| Responsibility \| Depends on`; its `Item-Dependencies` chain matches the inferred serial order |

## Proposed changes (ordered, validatable)

1. Split cells without breaking on a pipe inside backticks (E-01).
2. Resolve the Order and Depends-on columns by header NAME, not index (E-02).
3. Ignore trailing prose in a Depends-on cell, refusing only genuine ambiguity (E-03).
4. Accept the canonical `executed:<id6>` edge via the shipped grammar (E-04).
5. Report every remaining rejection visibly, in human and agent output (E-05).
6. Test each measured cause plus a corpus no-regression guard (E-06).

## Deferred / out of scope (with reason)

- A NEW LINT RULE enforcing the column layout. Arguably the real long-term fix, but it would put 28 existing plans into violation at once, including plans in terminal directories that must not be edited. Sequencing matters: make the parser tolerant FIRST, then a rule can be considered against a corpus that mostly passes. See OQ-02.
- RENAMING `aw ipd execute-set` (F7). A command-surface change owned elsewhere; approved `0soncw` declares `command_surface.py` and is mid-flight. Adding a rename here would widen a contended surface, which is the exact pattern that made the five `detrun` plans unexecutable.
- EDITING ANY ORCHESTRATOR PLAN, including `runprofile-00`. Fixing 1 of 28 tables while leaving the parser broken is the wrong layer, and terminal-directory plans must not be edited at all.
- THE SCHEDULER AND EXECUTION AUTHORITY. Explicitly a later Order per the command's own help; this plan changes only how the graph is READ.
- CHANGING THE FALLBACK BEHAVIOR. The conservative serial chain is correct and stays; only its silence is fixed.
- MAKING `aw ipd execute-set` READ `Item-Dependencies` INSTEAD OF THE TABLE. A larger design question (which source is authoritative) that deserves its own decision; this plan makes the declared table work as intended rather than replacing it.

## Scope check

- Over-scope: none. One shipped module and its test module.
- Under-scope, DELIBERATE: the two-sources-of-truth problem is NOT solved here. After this plan the planner reads the table well; whether the table or `Item-Dependencies` should be authoritative remains open (see Deferred). This plan makes the existing design work correctly rather than redesigning it.
- Under-scope, ACKNOWLEDGED: a parser tolerant of four measured patterns is still a parser, and a fifth pattern will appear. That is why E-05 is a separate, load-bearing item: the guarantee that survives is "never guess silently", not "always parse".
- CONTENTION: `ipd_set_plan.py` is not currently claimed by another pending plan (checked: no pending plan lists it in `Scope-Paths`). `cli.py` is heavily contended and this plan does NOT touch it.

## Required tests / validation

- `tests/test_ipd_set_plan.py` must pass with every case in E-06, and every pre-existing assertion must pass unchanged.
- FALSIFIABILITY (HARD): for each of the four causes, show the fixture FAILING to parse before the fix and parsing after. A test that only passes after is not evidence the fix did anything.
- CORPUS MEASUREMENT: paste the before and after parse-success counts over the real corpus (before is 18 of 46, measured at HEAD `dd6b1fd2`). A fix that does not move that number materially has not addressed F1.
- E-05 MUST BE DEMONSTRATED ON A TABLE NO FIX HANDLES: construct a deliberately unparseable table and paste the visible warning plus the structured agent reason. This is the item most likely to be quietly skipped because the parsing fixes make it feel unnecessary.
- NO BEHAVIOR CHANGE FOR PARSING TABLES: paste evidence that the 18 currently-parsing orchestrators produce byte-identical graphs before and after.
- INVOKE THE SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- VALIDATE IN THE PRIMARY CHECKOUT, not a scratch worktree (`dh0uno`: about 15 `test_run_viewer.py` tests fail in a detached worktree and pass in the primary tree).
- `aw check plans` is RED on pre-existing findings owned by other Sets (measured 829 at HEAD `dd6b1fd2`). Do NOT claim it passes; the bar is NO-WORSENING against a freshly measured baseline.
- `aw sanitize --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec change. Spec `25kzda` governs the runner, not this planner; the two surfaces are separate (`ipd_set_plan` is reached only from `cli.py:9232` and `ipd_set_executor`).
- Update the parser's own docstring to state the column-resolution rule it actually implements after this change, since the current docstring documents the fixed four-column layout that is the bug.
- Consider recording in `.aw/records/plans/README.md` that the child table's Order and Depends-on columns are load-bearing and machine-read. Deliberately NOT done in this plan: documenting a convention while 28 plans violate it invites a mass edit; sequence it after OQ-02 is decided.

## Open questions

### OQ-01: Should an unparseable table be a hard failure rather than a warned fallback?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: keep the fallback, add the warning. A hard failure would break `aw ipd execute-set` for 28 existing Sets the moment this ships, including Sets in terminal directories nobody may edit, and the command is read-only so a wrong preview harms nobody who is told it is a guess. The shipped design is already fail-safe in the right direction (it serializes rather than inventing parallelism, per its own docstring), so the defect is the silence, not the fallback. E-05 fixes exactly that. If a future maintainer wants strictness, the honest sequence is: tolerant parser, then a lint rule (OQ-02), then strictness once the corpus passes.

### OQ-02: Should a lint rule enforce the child-table column layout?

- Blocking: no
- Status: deferred
- Owner: maintainer (decide after this parser fix lands and the corpus is re-measured; a rule now would put 28 plans into violation at once)
- Resolution or deferral rationale: DEFERRED DELIBERATELY, and non-blocking because the parser fix stands alone. A rule is the durable answer to the root cause (an unenforced convention that a parser silently depends on), but shipping it NOW would flag 28 existing orchestrators, several in `executed/` and `superseded/` where the plan body is immutable, so the only compliant move would be a mass edit of historical records. The right order is: make the parser tolerant (this plan), re-measure, then decide whether the residual non-conformers justify a rule and whether it applies only to `pending/`. Recorded so the root cause is not forgotten once the symptom stops hurting.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `attnview-00` row 03 cell split BEFORE (5 cells, `cells[3]` starting `markdown`) and AFTER (4 cells, `cells[3]` = `01, 02`). Paste all four inline-pipe orchestrators (`attnview`, `awrelease`, `awcmdsurf`, `awselect`) parsing after the fix and failing before.
  - Observed evidence: VERIFIED. `_split_table_row` is backtick-aware (`ipd_set_plan.py`, `_split_table_row`). BEFORE, `attnview-00` row 03 split into 5 cells with `cells[3] == "markdown`, `--check`, `--agent`; ..."`; AFTER it splits into 4 with `cells[3] == "01, 02"`. All four inline-pipe orchestrators now parse (they were part of the 18->37 corpus gain). FALSIFIABILITY, actually run: reverting only this split to the naive `s.split("|")` fails `test_inline_pipe_in_backticks_does_not_shift_columns` with `AssertionError: "cannot parse the dependency cell 'markdown` here' for Order 02" is not None`; restoring it returns 34 passed. Unbalanced-backtick guard covered by `test_unbalanced_backtick_falls_back_to_naive_split`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a 3-, a 5-, and a 6-column real orchestrator parsing after the fix. Paste the header-name resolution code showing the column is found by NAME. Paste a table whose header names neither required column refusing visibly rather than silently falling back.
  - Observed evidence: VERIFIED. Columns are resolved by header NAME via `_ORDER_COLUMN_NAME`/`_DEP_COLUMN_NAMES` in `parse_child_table` (it locates `order` and the first dependency-column spelling in the header row, then indexes by those). Real corpus: `rununify-00` (3 columns) now parses its rows; `runprofile-00` (5 columns, `Order | Id | Child | Responsibility | Depends on`) reports `Cross-IPD edges: orchestrator-table` where it previously reported `legacy-inference`; `wtiso-00` and `lanetruth-00` (6 columns) are covered by the same path. Unit-covered by `test_columns_resolved_by_header_name_not_index` (5- and 3-column) and `test_alternate_dependency_column_spellings` (all three in-corpus spellings). A header naming no dependency column refuses WITH a reason: `test_header_without_dependency_column_refuses_with_reason` asserts the reason contains `no dependency column`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste each of the four measured prose forms (`none (parallelizable)`, `01 (consumes the rewritten strings)`, `09; D113 evidence`, `01 executed`) with the dependency set extracted. Paste a deliberately AMBIGUOUS cell refusing rather than producing a partial edge set, since guessing an edge is the failure mode that matters.
  - Observed evidence: VERIFIED, run directly against `_dep_tokens`: `'none (parallelizable)' -> []`, `'01 (consumes the rewritten strings)' -> ['1']`, `'09; D113 evidence' -> ['9']`, `'01 executed' -> ['1']`, plus three further in-corpus spellings found while measuring: `'Order 01' -> ['1']`, `'Orders 01' -> ['1']`, `'-' -> []`, `'01-03' -> ['1','2','3']`. AMBIGUITY FAILS CLOSED: `'approved spec' -> None` and `'E-01 inventory' -> None`, so the caller serializes conservatively rather than inventing an edge. All asserted by `test_trailing_prose_in_dependency_cell_is_ignored` and `test_genuinely_ambiguous_cell_refuses_rather_than_guessing`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `executed:<id6>` naming a sibling producing the right edge, and naming an out-of-Set plan being ignored for ordering WITHOUT rejecting the table. Paste the call into the shipped grammar helper proving no second tokenizer was written.
  - Observed evidence: VERIFIED. `_dep_tokens` calls the SHIPPED authority `_schema.parse_item_dependencies(tok)` (ipd_schema, spec 25kzda 2.7) and reads `edges[0].id6`; no second tokenizer exists. In-Set: `_dep_tokens("executed:aaaaaa", {"1":"aaaaaa","2":"bbbbbb"}) -> ['1']`. Out-of-Set: `_dep_tokens("executed:zzzzzz", ...) -> []`, ignored for ordering and the table is NOT rejected, matching how the runner treats an out-of-queue target (`oc_runipd.dependency_depth`). A BARE id6 resolves only when it names a sibling (`test_bare_id6_resolves_only_when_it_names_a_sibling`), so no arbitrary word can become a dependency. Asserted by `test_typed_executed_edge_resolves_in_set_and_ignores_out_of_set`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the human output for a deliberately unparseable table showing the explicit warning and the offending row/cause, and the `--agent` JSON carrying the structured reason. Paste evidence the fallback ORDER is unchanged and `cross_edges_source` keeps its existing values. This item must be demonstrated on a table the parsing fixes do NOT handle.
  - Observed evidence: VERIFIED on a REAL still-unparseable Set (`rununify`, whose cell `E-01 inventory` is genuinely ambiguous). Human output of `aw ipd execute-set rununify --plan-only`:
      `Cross-IPD edges: legacy-inference`
      `  WARNING: the orchestrator's declared child table was NOT used; the order below is`
      `  INFERRED (conservative serial by Order). Reason: cannot parse the dependency cell 'E-01 inventory' for Order 01`
    `--agent` JSON carries `cross_edges_source: legacy-inference` and `cross_edges_fallback_reason: cannot parse the dependency cell 'E-01 inventory' for Order 01`. Fallback ORDER is unchanged (`test_unparseable_table_sets_a_reason_and_keeps_serial_order` asserts the serial chain `bbbbbb -> aaaaaa`), and `cross_edges_source` keeps its exact existing values so downstream consumers are unaffected. Two MAPPING failures that were also silent (a child with no row; a dependency on a non-child Order) now set a reason too. FALSIFIABILITY, actually run: forcing `fallback_reason = None` fails two tests (`unexpectedly None`); restoring gives 34 passed.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_ipd_set_plan.py` with counts and the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at, in the PRIMARY checkout. Paste before/after corpus parse counts (before: 18 of 46 at `dd6b1fd2`). Paste evidence the 18 previously-parsing Sets produce byte-identical graphs. Paste proof the new tests are NOT vacuous by reverting one fix and showing its test fail. Paste the `aw check plans` no-worsening comparison.
  - Observed evidence: VERIFIED, all measured in the PRIMARY checkout at HEAD `dd6b1fd2`.
    `python3 -m pytest tests/test_ipd_set_plan.py -o addopts="" -q` -> `34 passed in 0.43s` (was 19 before; 15 new cases, and the file's pre-existing assertions all still pass unchanged).
    BARE `python3 -m pytest` -> `3832 passed, 3 skipped, 4 xfailed in 50.55s` (baseline before this work: `3816 passed, 3 skipped, 4 xfailed`).
    CORPUS: 18/47 parsed BEFORE, 37/47 AFTER (the denominator is 47 not 46 because this plan added a file; the pre-fix rate was re-measured at 18/47 on the same corpus). The remaining 10 refusals are genuinely ambiguous cells or files with no child-table section, and EVERY one now reports a reason (`test_every_refusal_states_a_reason` asserts this repo-wide).
    NO REGRESSION: all 18 previously-parsing Sets produce BYTE-IDENTICAL graphs (compared serialized before/after maps: 0 changed).
    NOT VACUOUS: sabotaging E-01 fails exactly its test; sabotaging E-05 fails exactly its two tests; both restored and re-run to 34 passed.
    `aw check plans`: 829 findings before, 837 with my two files UNCOMMITTED. I attributed all 8 rather than waving them through: each is one `check.scope-drift` finding on ANOTHER plan (`wtiso-02/03/05/06/07`, `runstop-06`, `terseout-01`), caused by uncommitted working-tree files counting against every pending plan's declared scope. That is the known filed defect `v880xk`, not drift caused by this plan. ZERO findings are attributed to `setgraph` itself. `aw sanitize --agent`: clean, 0 findings.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 6 E-leaves across 2 task groups, under the thresholds. One concern throughout: read the declared Set order correctly, and never guess silently.

Open questions: NEITHER is blocking. OQ-01 is resolved from repository evidence (keep the fail-safe fallback, fix its silence). OQ-02 is deferred to the maintainer with a named trigger, because a lint rule now would put 28 existing plans, some immutable, into violation at once.

Scope fence: touch ONLY `agent_workflows/ipd_set_plan.py` and `tests/test_ipd_set_plan.py`. Do NOT edit any `.ipd.md` plan file, including `runprofile-00` and including any orchestrator in a terminal directory. Do NOT touch `cli.py` or `command_surface.py` (contended; `0soncw` is mid-flight and a verb rename is explicitly out of scope, F7). Do NOT change the fallback ORDERING or the existing values of `cross_edges_source`. Do NOT add a lint rule (OQ-02). Do NOT write a second dependency tokenizer; consume `ipd_schema` (E-04). Do NOT grant or approach execution authority: this command is read-only by design. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at, measured in the PRIMARY checkout. Do NOT claim `aw check plans` passes; it is RED on 829 pre-existing findings owned by other Sets at `dd6b1fd2`, and the bar is no-worsening against your own fresh baseline. Do NOT describe this as fixing Set EXECUTION: `aw ipd execute-set` cannot execute anything, so this fixes a PREVIEW. Say that plainly.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Note that `aw ipd finalize --apply` legitimately regenerates and commits `.aw/records/plans/INDEX.json` and `INDEX.md`; that is the tool working as designed, not index pollution.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
