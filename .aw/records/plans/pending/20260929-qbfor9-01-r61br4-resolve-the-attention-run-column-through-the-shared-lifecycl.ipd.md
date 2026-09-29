# IPD: Resolve the attention Run column through the shared lifecycle resolver by emitting the runner's own status vocabulary

- Date: 2026-09-29
- Kind: child
- Concern: `aw attention --runs` paints its Run column from TWO hardcoded lifecycle tables that spec `uonrjg` R10.3 forbids, and five of the six colors CONTRADICT the spec's Section 5 palette. The sites are `attention._render_item_row` (the `run_code = {...}` dict) and `attention._render_table_row` (the `run_raw ==` if/elif ladder), both inside their `runs_mode` branches. Both paint a RUNNER ITEM STATE, which Section 7.2 covers and `lifecycle_style.FAMILY_RUNNER_ITEM` already maps, so criterion A17 ("No second lifecycle color or glyph table remains") is unsatisfiable for this module while they stand. Measured 2026-09-29 by styling each word both ways at HEAD: `running` 51 -> 220, `queued` 220 -> 45, `merging` 201 -> 220, `done` 40 -> 46, `blocked` 214 -> 208 all CHANGE; only `failed` (196) is already correct. The `queued` case is a defect a user can SEE independent of the conversion: 220 is this spec's amber for the five ACTIVE subtypes, so a queued (not yet started) item renders in the color reserved for work in progress, which is precisely the readiness/activity collapse Section 5 exists to prevent.
  THE BLOCKING SUB-PROBLEM THE BACKLOG FILED RATHER THAN FIXED IS THE VOCABULARY, and it is resolved here from code evidence (see Findings F-1 and F-2). `attention.get_active_runs_map` does not pass the runner's status through; it MAPS each one onto its own six-word vocabulary (`running`/`queued`/`merging`/`done`/`failed`/`blocked`), and two of those words are not members of `lifecycle_style`'s runner-item table at all, so a naive substitution resolves them to the `unknown` stage (`?`, gray 244) and REGRESSES the display, printing `?` where an operator reads `merging` today. Verified by resolving both: `resolve(FAMILY_RUNNER_ITEM, "merging")` and `resolve(FAMILY_RUNNER_ITEM, "done")` each return stage `unknown` with a diagnostic.
- Scope: IN: (1) make `get_active_runs_map` emit the runner's OWN canonical status vocabulary instead of its private six-word one, canonicalizing legacy spellings through the two shipped alias tables so a durable pre-rename run still reads; (2) delete both hardcoded Run-column tables and resolve the column through the shared `term` lifecycle helpers, so the Run cell carries its glyph, color and bold from the one resolver; (3) widen the Run column from 7 to 14 visible columns, which is what the longer canonical words require and what removes the measured truncation collisions; (4) re-point the four dependents of the retired six-word vocabulary (`attention_contract.RUN_SORT_ORDER`, `attention._RUN_STATUS_ALIASES`, the `--run-status` filter and its help text, and the `-o runs` sort rank) so a filter token a user types still matches what the column prints; (5) update the affected tests and the `--runs` snapshot assertions.
  OUT: changing WHICH runs are scanned or the liveness test that selects them (`run_viewer.driver_holder_state`, untouched); the `priority_order` collapse that picks ONE state when an id6 appears in several live runs (retained, re-keyed; see Deferred); `runner_shared.format_slated_artifacts_table`'s own queue-to-word mapping (a SEPARATE second mapping, see Deferred); adding any status to `lifecycle_style` or amending spec `uonrjg` (no new mapping is needed once the vocabulary is the runner's own, which is the point of the chosen option); and the artifact Status column, already converted by `f9t5hz`.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/cli.py, tests/test_attention.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: qbfor9
- From-Spec: uonrjg
- Blocks-Release: next
- Set: qbfor9
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: r61br4

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `qbfor9`, spec `uonrjg` Sections 5/7.2/9.1 and R10.3, and criterion A17. Carries the item's `Blocks-Release: next` gate. The vocabulary decision the item deferred is RESOLVED here from code evidence (F-1, F-2) rather than escalated; OQ-01 records the rejected alternative and why.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw attention --runs` the last lifecycle surface in `attention.py` to resolve through the shared module, by retiring the private six-word run vocabulary in favour of the runner's own canonical statuses, so the Run column's color, glyph and weight come from spec `uonrjg` Section 5 and criterion A17 becomes satisfiable for this file.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Retire the private vocabulary at its source

- [ ] E-01 Change `attention.get_active_runs_map` to emit the runner's OWN canonical item status for each queue entry instead of mapping it onto the private six-word vocabulary, canonicalizing each raw status through `runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES` and then `runner_shared.canonical_terminal_status`, and delete the `raw_st ==` / `raw_st in (...)` ladder that produced `running`/`queued`/`merging`/`done`/`failed`/`blocked`.
  - Depends on: none
  - Expected outcome: For every member of `runner_shutdown.KNOWN_ITEM_STATUSES`, the map's value is that status's canonical spelling rather than one of six synthesized words. No `"merging"` literal remains in the function. The `[:7]` truncation in the old `else` branch is gone, so no value is a truncated fragment.
  - Execution state: pending

  THE TRUNCATION IN THE OLD `else` BRANCH IS ITSELF A LIVE DEFECT AND ITS REMOVAL IS NOT MERELY TIDYING, which is why this item must not preserve it. The retired ladder ended `mapped = raw_st[:7] if raw_st else "-"`, so any status the ladder did not name was stored PRE-TRUNCATED, and the truncated fragment then flowed into the filter and the sort as if it were a status word. Measured 2026-09-29 by building a live run directory whose queue holds all 28 members of `KNOWN_ITEM_STATUSES` and reading the resulting map: five statuses came back as fragments (`already-landed` -> `already`, `integration-deferred` -> `integra`, `merge-retry` -> `merge-r`, `not-attempted` -> `not-att`, `retired` -> `retired`), and two of those fragments COLLIDE (`integra` is both `integration-blocked` and `integration-deferred`; `merge-r` is both `merge-refused` and `merge-retry`). Because the fragment is what `matches_run_status` compares against, `--run-status already-landed` matches NOTHING today: verified by calling `parse_run_status_filters(["already-landed"])`, which yields `{already-landed, already_landed}`, and then `matches_run_status` against a map holding `already`, which returns False. Truncation is a DISPLAY concern and belongs at the render site, never in the data.

  CANONICALIZE THROUGH BOTH TABLES, IN THAT ORDER, AND DO NOT INVENT A THIRD. Two shipped tables exist and they compose: `LEGACY_INTEGRATION_STATUS_ALIASES` maps the 2026-09-21 rename (`integration-deferred` -> `merge-retry`, and four spellings onto `fail-merge`), and `canonical_terminal_status` applies `TERMINAL_STATUS_ALIASES` (the 2026-09-25 `statusvocab` vocabulary, e.g. `dependency-blocked` -> `fail-depend`, `partial` -> `fail-verify`). Measured composed over all 28 known statuses: 17 distinct canonical words, longest `already-landed` at 14 characters, and ZERO collisions at every truncation width from 7 to 14. Spec `uonrjg` requires both legacy vocabularies stay READABLE forever because a run directory is a durable record, and composing the two tables is what delivers that without a new mapping.

- [ ] E-02 Update `get_active_runs_map`'s `priority_order` so it ranks the CANONICAL statuses E-01 now emits, preserving the existing behavior that an id6 present in several live runs reports its most-significant state.
  - Depends on: E-01
  - Expected outcome: An id6 appearing in two live runs still resolves to one state by the same most-significant-wins rule. No key in `priority_order` is a word E-01 no longer emits, and every status E-01 can emit has a defined rank (an unranked status must not silently outrank a ranked one).
  - Execution state: pending

  THIS IS A RE-KEYING, NOT A POLICY CHANGE, and the distinction bounds the item. The collapse rule itself (highest rank wins, ties keep the later entry via `>=`) is deliberately OUT of scope and must be carried over unchanged; only the KEYS change, because the six words they name cease to exist. Keep the ordering intent the retired table expressed: in-flight work outranks queued, which outranks settled outcomes. Note the retired table ranked only its own six words, so the `.get(mapped, 0)` default already existed; E-01 widens the key space from 6 to 17, so verify no canonical status falls to the default in a way that makes it beat a genuinely more significant one.

### Task group 2: Convert the two render sites

- [ ] E-03 Replace the `run_code = {...}` hardcoded color dict in `attention._render_item_row` with the shared lifecycle helpers, resolving the run state through `term.resolve_lifecycle(lifecycle_style.FAMILY_RUNNER_ITEM, ...)` and styling the cell with `term.style_lifecycle_text`.
  - Depends on: E-01
  - Expected outcome: No color literal remains in `_render_item_row`'s run branch. The `[run:<state>]` cell takes its color and bold flag from the shared resolver. The uncolored branch still prints `[run: <state>]` with the canonical word.
  - Execution state: pending

  LOCATE BOTH SITES BY GREP, NOT BY THE LINE NUMBERS IN THIS PROSE. Sibling `f9t5hz` recorded that all four line numbers in its own text had drifted by +32 before it executed, and this file is under concurrent change. `grep -n "run_code\|run_raw" agent_workflows/attention.py` is the durable locator; the two render sites are the only matches.

  PASS THE ACTIVITY FOR `merging`, WHICH IS THE ONE NON-MECHANICAL PART OF THE CONVERSION. The runner's canonical vocabulary has no `merging` member (see F-2), so if E-01's output ever carries a merge-in-progress word it must reach the resolver as an ACTIVITY rather than as a native status: `resolve(FAMILY_RUNNER_ITEM, "merging")` resolves `unknown` (gray 244, `?`), while `resolve(FAMILY_RUNNER_ITEM, "merging", activity="merging")` resolves `integrating` (amber 220, `⇄`), which is the spec's own word and glyph for merge or integration work (Section 7.1). Measured both 2026-09-29. Follow the precedent already shipped in `run_viewer._resolve_item_status` and `render_stream.resolve_item_lifecycle`: apply an activity only to an IN-FLIGHT item, and DROP an activity the table does not map rather than passing it through, because an unrecognized activity resolves `unknown` and prints `?` for an item whose own status already earns a stage.

- [ ] E-04 Replace the `run_raw ==` if/elif color ladder in `attention._render_table_row` with the same shared-helper resolution, and emit the Run cell so that it carries the lifecycle glyph immediately preceding the status word.
  - Depends on: E-01, E-03
  - Expected outcome: No color literal remains in `_render_table_row`'s `runs_mode` branch. Both render sites resolve through ONE code path, so the board row and the table row cannot disagree about a run state's color. `grep -n "38;5;" agent_workflows/attention.py` reports no lifecycle color literal in either run branch.
  - Execution state: pending

  PAD BY VISIBLE COLUMNS, NEVER BY `len()`, AND THIS SITE CURRENTLY GETS IT WRONG. The existing code computes `run_pad = " " * (7 - len(run_raw))`, which is safe only while every value is pure ASCII. After E-04 the cell carries a glyph, and two of Section 5's graphemes (`⚠︎`, `↩︎`) are TWO code points and ONE column, so a `len()`-based pad leaves their column one short of every other row's. Use `term.format_lifecycle_marker(resolved, width=2)` for the glyph and `T.visible_width` for the word's pad, exactly as the already-converted Status column in this same function does (`st_col`). Spec Section 9.4 bullets 2 and 4 require this, and `f9t5hz` measured the failure it prevents.

- [ ] E-05 Widen the Run column from 7 to 14 visible columns at the header, the row, and the sizing constants, so the canonical statuses print in full rather than truncated.
  - Depends on: E-04
  - Expected outcome: The `--runs` header reads `Run` padded to the new width and every row's Run cell aligns with it. `already-landed` (14 characters, the longest canonical word) prints in full. The colored table remains a character-for-character match of the uncolored one once ANSI is stripped, and the columns to the right of Run stay in their existing order.
  - Execution state: pending

  14 IS MEASURED, NOT CHOSEN FOR ROUNDNESS: it is `max(len(w))` over the 17 canonical words the composed alias tables produce, and it is the smallest width at which no canonical word is truncated. Truncation is no longer needed for DISAMBIGUATION at any width (zero collisions from 7 to 14, measured), so the width is purely about printing the word the spec makes authoritative. WIDENING IS THE CORRECT DIRECTION HERE AND ABBREVIATING IS NOT, which is the opposite of the ruling the Status column took: that column's width is pinned at 8 by an exact-line snapshot test and by every column to its right, so `attcor rkn8ya` abbreviated the one colliding pair instead (`_STATUS_ABBREV`). The Run column has no such pin: it exists ONLY in `runs_mode`, which is off by default, so widening it shifts nothing in the default view. STILL VERIFY THE SNAPSHOT: `tests/test_attention.py` asserts `lines_on[0].startswith("  Status   Run     Type")` and three exact cell strings (`"approved running plan"`, `"to-revie queued  plan"`, `"draft    done    plan"`), every one of which this item changes, so update them deliberately and say in V-05 what each became.

### Task group 3: Keep the filter and the sort agreeing with the column

- [ ] E-06 Re-point the four dependents of the retired six-word vocabulary onto the canonical statuses: `attention_contract.RUN_SORT_ORDER`, `attention._RUN_STATUS_ALIASES`, the `--run-status` help text in `cli.py`, and `attention._RUN_SORT_RANK`'s fallback tuple.
  - Depends on: E-01
  - Expected outcome: A token a user passes to `--run-status` matches the state the column prints, for every member of `KNOWN_ITEM_STATUSES` INCLUDING the legacy spellings (a user who types a pre-rename name still matches the canonical state it maps to). `-o runs` still sorts in-flight before queued before settled. The help text no longer advertises `merging` as an example value it can never match. `attention.selector_vocabulary` (which sources run words from `_RUN_STATUS_ALIASES`) offers the words the column can actually show.
  - Execution state: pending

  THE FILTER IS THE PART MOST LIKELY TO BREAK SILENTLY, because it fails by MATCHING NOTHING rather than by raising, so a wrong mapping here looks like an empty board. `matches_run_status` compares the map's value against the parsed filter set, so the two must be re-pointed TOGETHER with E-01: leaving `_RUN_STATUS_ALIASES` mapping `executed -> done` while the map now holds `executed` makes `--run-status done` match nothing and `--run-status executed` match everything, inverting the user's intent without an error. Note the retired table deliberately OMITTED `merge-retry` and `merge-unchecked` ("those are non-terminal and retry themselves, so classifying them as `blocked` would report an item needing no attention as needing attention") - PRESERVE that judgement's EFFECT under the new vocabulary rather than mechanically adding them to a blocked bucket.

  `RUN_SORT_ORDER` LIVES IN `attention_contract.py`, WHICH IS A FROZEN-CONTRACT MODULE, so state in V-06 that this constant is NOT spec-governed before changing it. Checked 2026-09-29: `grep -rn "RUN_SORT_ORDER" .aw/records/specs/*/*.md` returns no match, and the module's docstring enumerates the spec sections it freezes (Sections 6, 7, 8.x of the attention spec) without naming run-status sort order, which arrived later with `--order-by runs`. So it is an ordinary internal constant that happens to live beside frozen ones. `attention._RUN_SORT_RANK` reads it via `getattr(A, "RUN_SORT_ORDER", (...))` with a hardcoded six-word fallback tuple, so BOTH copies must change or the fallback silently reinstates the retired vocabulary.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Sibling `f9t5hz` had all four of its line numbers drift +32 before execution, so this plan cites by symbol and grep string throughout.
- Lifecycle presentation resolves through `lifecycle_style` (the semantic table, which EMITS NO ESCAPES) and is rendered by `term` (`resolve_lifecycle`, `style_lifecycle_text`, `format_lifecycle_marker`). Spec `uonrjg` R10.2 assigns every capability decision to `term`, which is why the semantic module takes the unicode choice as an argument rather than sniffing the stream.
- The ALREADY-CONVERTED sites in this same file are the pattern to copy, not to re-derive: `attention._resolve_item_lifecycle` is the module's one resolution entry point and translates a non-lifecycle tree to the `unknown` stage rather than letting `UnknownFamily` propagate, because a read-only view must not crash on an unclassifiable row.
- A run directory is a DURABLE RECORD, so a status spelling that was ever written must stay readable forever. Two alias tables exist for exactly this (`LEGACY_INTEGRATION_STATUS_ALIASES`, `TERMINAL_STATUS_ALIASES` via `canonical_terminal_status`); nothing writes a legacy spelling any more.
- The suite runs BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0` or a second `-q`.

## Findings

| Id | Severity | Finding | Evidence |
|---|---|---|---|
| F-1 | HIGH | `get_active_runs_map` is a SECOND vocabulary, not a pass-through, and that is why the conversion is not mechanical. It maps the runner's statuses onto six private words, so the Run column's values are not the runner's states at all. Both hardcoded tables downstream key on those six words. | `attention.get_active_runs_map`'s own docstring: "States are mapped to: 'running', 'queued', 'merging', 'done', 'failed', 'blocked'". The `raw_st ==` ladder performs the mapping. |
| F-2 | HIGH | Two of the six words are NOT in `lifecycle_style`'s runner-item table, so a naive substitution REGRESSES the display to `?`. This is the sub-problem the backlog filed rather than fixed. | Measured 2026-09-29: `resolve(FAMILY_RUNNER_ITEM, "merging")` and `resolve(FAMILY_RUNNER_ITEM, "done")` both return stage `unknown`, color 244, glyph `?`, with a diagnostic. The other four resolve cleanly (`running` -> active, `queued` -> ready, `failed` -> failed, `blocked` -> blocked). |
| F-3 | HIGH | Five of the six colors contradict spec Section 5; only `failed` agrees. `queued` is visible today as the readiness/activity collapse Section 5 exists to prevent. | Measured 2026-09-29 by styling each word both ways: `running` `\x1b[1;38;5;51m` -> `\x1b[1;38;5;220m`; `queued` `\x1b[38;5;220m` -> `\x1b[1;38;5;45m`; `merging` `201` -> `220`; `done` `40` -> `46`; `blocked` `\x1b[38;5;214m` -> `\x1b[1;38;5;208m`; `failed` `196` -> `196` unchanged. |
| F-4 | HIGH | NEW, not in the backlog item: the retired ladder's `else` branch stored a `[:7]`-TRUNCATED status, so five statuses became fragments in the DATA, and `--run-status already-landed` matches nothing as a result. Truncation belongs at the render site. | Measured 2026-09-29 against a live run dir holding all 28 `KNOWN_ITEM_STATUSES`: `already-landed` -> `already`, `integration-deferred` -> `integra`, `merge-retry` -> `merge-r`, `not-attempted` -> `not-att`. `parse_run_status_filters(["already-landed"])` yields `{already-landed, already_landed}`; `matches_run_status` against a map holding `already` returns False. |
| F-5 | MEDIUM | Two of those fragments COLLIDE, so the filter and sort cannot distinguish an obstruction from a self-retrying state. Resolving the vocabulary at the source (E-01) removes the collision class entirely rather than patching it. | `integra` <- {`integration-blocked`, `integration-deferred`}; `merge-r` <- {`merge-refused`, `merge-retry`}. Measured at width 7. After canonicalization through both alias tables: 17 words, ZERO collisions at every width 7 to 14. |
| F-6 | MEDIUM | `"merging"` HAS NO WRITER ANYWHERE IN THE PACKAGE, so the word the column shows for merge work is synthesized by this module alone and no runner ever records it. | `grep -rn 'merging' --include=*.py agent_workflows/` matches only `attention.py` (the two render sites plus the map and sort order), `attention_contract.RUN_SORT_ORDER`, `lifecycle_style`'s `ACTIVITY_FROM_ACTION`, and prose. `git log --all -S'= "merging"'` shows no commit introducing a writer. `'merging' in runner_shutdown.KNOWN_ITEM_STATUSES` is False. |
| F-7 | MEDIUM | The existing Run cell pads by `len()`, which is safe only while the value is pure ASCII and becomes a misalignment bug the moment E-04 adds a glyph. | `run_pad = " " * (7 - len(run_raw))` in `_render_table_row`. Spec Section 9.4; `f9t5hz` measured `status_256('⚠︎', width=4)` producing 3 rendered columns against `◕`'s 4. |
| F-8 | MEDIUM | The retired vocabulary has FOUR dependents, not one, and two of them hold their own copy, so converting only the render sites leaves the filter matching words the column no longer prints. | `attention_contract.RUN_SORT_ORDER`; `attention._RUN_STATUS_ALIASES` (also feeding `selector_vocabulary`); `attention._RUN_SORT_RANK`'s `getattr` fallback tuple, which hardcodes the same six words a second time; `cli.py`'s `--run-status` help, which advertises "running, queued, merging, done, blocked, failed". |
| F-9 | LOW | `runner_shared.format_slated_artifacts_table` contains a THIRD copy of the queue-to-word mapping and calls `attention.render_table(runs_mode=True)`, so it feeds the converted column. It is deliberately out of scope; see Deferred. | `format_slated_artifacts_table` builds its own `run_map` with an independent `q_st in (...)` ladder producing `done`/`running`/`failed`/`blocked`/`queued`, then calls `attention.render_table`. |
| F-10 | MEDIUM | A TRAP FOR THE EXECUTOR: two of the six retired escapes are ALSO used in this same file for NON-lifecycle purposes, so a table-wide "retired escape is absent" assertion is unsatisfiable and would look like a failed conversion. The assertion must be scoped to the Run CELL. This is the same trap `f9t5hz`'s review caught as PR-506. | `tests/test_attention.py` asserts `"\033[1;38;5;214m1/2\033[0m"` and `"\033[1;38;5;40m2/2\033[0m"` against the colored table: those are the OQ-COUNT column's colors (214 amber for partially-resolved, 40 green for fully-resolved), not lifecycle colors, and they must NOT change. `214` additionally appears as the `medium` PRIORITY color in both `_render_item_row` and `_render_table_row`. Outside this file, `tests/test_run_summary_table.py` asserts `38;5;214munknown` and `tests/test_ipd_lint.py` asserts `1;38;5;214mquarantined`; neither file is in scope and neither may change. |

## Proposed changes (ordered, validatable)

1. E-01: `get_active_runs_map` emits canonical runner statuses, composing `LEGACY_INTEGRATION_STATUS_ALIASES` then `canonical_terminal_status`. The private six-word ladder and its `[:7]` truncation are deleted.
2. E-02: `priority_order` is re-keyed onto those canonical statuses, preserving the most-significant-wins collapse unchanged.
3. E-03: `_render_item_row`'s `run_code` dict is replaced by shared-resolver styling, passing an activity only for an in-flight item and dropping an unmapped one.
4. E-04: `_render_table_row`'s `run_raw ==` ladder is replaced by the same one path, adding the glyph and padding by visible width.
5. E-05: the Run column widens 7 -> 14 so the canonical words print in full; the header and the three exact-cell test assertions are updated.
6. E-06: `RUN_SORT_ORDER`, `_RUN_STATUS_ALIASES`, `_RUN_SORT_RANK`'s fallback tuple and the `--run-status` help are re-pointed so filter, sort and column agree.

## Deferred / out of scope (with reason)

- `runner_shared.format_slated_artifacts_table`'s independent queue-to-word mapping (F-9). It is a THIRD mapping of the same shape and it feeds this very column, so it is a real follow-up, but it is a runner-side surface in a different module and converting it means deciding whether the runner should build a `run_map` at all or hand `render_table` its queue directly. Folding that in would widen this plan's blast radius from one view to the runner's pre-flight report. NOT INVISIBLE AFTER THIS PLAN: because E-01 re-points the column onto canonical statuses, this function's synthesized words become inconsistent with the rest of the column, so it must be filed as a follow-up backlog item at execution time rather than left unrecorded.
- The `priority_order` COLLAPSE POLICY itself (which state wins when one id6 is in several live runs). E-02 re-keys it and deliberately does not re-litigate it: whether "most significant wins" is the right answer for a multi-run id6 is a product question this plan has no evidence to settle, and changing it would alter which state a user sees for reasons unrelated to color.
- Which runs are scanned, and the liveness test that selects them (`run_viewer.driver_holder_state`, `HOLDER_LIVE`). Untouched. This plan changes how a state is NAMED and PAINTED, never which runs contribute one.
- Adding any status to `lifecycle_style`, and amending spec `uonrjg`. Neither is needed: once the vocabulary is the runner's own, every value already has a Section 7.2 mapping, which is the decisive advantage of the chosen option (OQ-01).
- The artifact Status column and `_STATUS_COLOR_256`. Already converted by `f9t5hz`; this plan touches only the Run column that conversion could not reach.

## Scope check

- Over-scope: none. Every E-item is required either to remove a hardcoded lifecycle table (E-03, E-04), to make that removal non-regressing (E-01, E-02, E-05), or to keep an existing user-facing feature working across it (E-06).
- Under-scope: `runner_shared.format_slated_artifacts_table` (F-9) is a third copy of the same mapping that feeds this column and is NOT fixed here; it is recorded in Deferred with an instruction to file it as a follow-up backlog item at execution time. Criterion A17 speaks of "both runners" as well as attention, so A17 is not globally satisfied by this plan alone; what this plan makes true is that no second lifecycle color or glyph table remains in `attention.py`, which is the part `qbfor9` filed and the part `f9t5hz` could not reach.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`) and paste the actual summary line. Targeted runs during development: `python3 -m pytest tests/test_attention.py tests/test_lifecycle_style.py tests/test_runner_active_conflict.py`.

- A totality test over the OWNER ENUM, not over a hand-typed list: for every member of `runner_shutdown.KNOWN_ITEM_STATUSES`, build a live run directory holding it and assert `get_active_runs_map` returns a value that (a) is not truncated, (b) equals that status's canonical spelling, and (c) resolves through `lifecycle_style.resolve(FAMILY_RUNNER_ITEM, ...)` to a stage OTHER than `unknown` with no diagnostic. This is the assertion that would have caught F-2, F-4 and F-5, and sourcing it from the enum is what makes a newly added runner status fail here rather than silently render gray.
- A round-trip test that the FILTER agrees with the COLUMN: for each canonical status, and for each LEGACY spelling in both alias tables, assert an item whose run state is that status is matched by `--run-status <token>` and is absent from the complement. This is the F-8 regression, and it must cover the legacy spellings because a user reading an old run report will type the old word.
- Behavioral assertions on the two render sites: the colored `--runs` table contains the SHARED resolver's escape on each Run cell. Assert the retired escapes are absent FROM THE RUN CELL, scoping the assertion to that cell rather than to the whole table (see F-10: two of those escapes are legitimately present elsewhere in the same output and a table-wide `assertNotIn` is UNSATISFIABLE). Extract the Run cell by column position or by splitting the row, then assert on it.
- A visible-width assertion (F-7): render a Run cell whose stage glyph is one of the two VS-bearing graphemes (`⚠︎` for `blocked`, `↩︎` for a recovering state) and one whose glyph is single-codepoint, and assert the Run column occupies the SAME number of rendered columns in both rows. Assert via `T.visible_width` on the ANSI-stripped cell, never via `len()`.
- The plain/colored equivalence property this file already asserts: stripping ANSI from the colored `--runs` table yields the uncolored table character for character.
- `--no-color`, `NO_COLOR=1` and `AW_ASCII_ONLY=1` over the same fixture: no ANSI in the first two, the exact Section 5 ASCII fallbacks in the third, and the canonical WORD present in all three (spec criteria A11, A12, A12d).
- `python3 -m pytest tests/test_lifecycle_style.py` must stay green WITHOUT any edit to `lifecycle_style.py`. A change there would mean the vocabulary decision was wrong; the chosen option's whole claim is that the runner's own statuses are already fully mapped.

## Spec / documentation sync

NO SPEC AMENDMENT IS REQUIRED, and that is a load-bearing property of the chosen option rather than an omission. Spec `uonrjg` Section 7.2 already maps every member of `runner_shutdown.KNOWN_ITEM_STATUSES` (verified 2026-09-29: all 28 resolve to a non-`unknown` stage with no diagnostic), so emitting the runner's own vocabulary needs no new row. The REJECTED option would have required one: adding `merging` and `done` to the runner-item family means amending an approved, release-gating spec to admit two words no runner writes (F-6). Consequently no `.spec.md` path appears in `- Scope-Paths:`.

`cli.py`'s `--run-status` help text IS user-facing documentation and IS changed by E-06, because it currently advertises `merging` as an example value. No file under `docs/` mentions `--runs` or `--run-status` (checked: `grep -rn "run_status\|--runs\|run-status" docs/*.md` returns nothing), so there is no published contract document to re-point.

## Open questions

### OQ-01: Should the fix change `get_active_runs_map`'s vocabulary, or add a translation table at the render boundary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED IN FAVOUR OF CHANGING THE VOCABULARY (E-01), from code evidence, which is why this plan does not escalate the decision the backlog item deferred. THREE FACTS DECIDE IT. (1) The six private words are not states anything records: `"merging"` has no writer anywhere in the package and is not a member of `KNOWN_ITEM_STATUSES` (F-6), so a translation table would permanently maintain a word the system never produces. (2) The private vocabulary is LOSSY IN A WAY USERS FEEL, independent of color: it collapses 28 statuses onto 6, so `fail-gate`, `fail-depend`, `not-run` and `partial` all print `blocked`, and an operator cannot tell a dependency block from a gate refusal in this view. Spec Section 0 makes the native word authoritative and Section 4.4a is explicit that many words sharing one STAGE is the design while the word itself must still print, so collapsing the words is the part that contradicts the spec most deeply. A translation table preserves that collapse. (3) The private vocabulary is also where F-4's truncation and F-5's collisions live, and both are removed by construction once the value is a canonical status rather than a synthesized fragment. THE REJECTED OPTION'S COST, stated so a reviewer can weigh it: a boundary translation table is a smaller diff and touches neither the filter nor the column width, but it requires amending an approved release-gating spec to admit `merging` and `done` (F-2), keeps the 28-to-6 collapse, and leaves the truncation defect in place. THE CHOSEN OPTION'S COST, stated honestly: it is a wider change (it re-points a filter, a sort order, a help string and a column width, hence E-06 and E-05), and it CHANGES WHAT THE COLUMN PRINTS, so a user who has learned to read `blocked` will now see `fail-gate` or `fail-depend`. That is an improvement in precision rather than a regression, and it is consistent with the rest of the run surfaces, which already print canonical statuses (`run_viewer` styles `canonical_terminal_status(step.status)`).

### OQ-02: Should `get_active_runs_map` return the canonical status only, or both the raw and the canonical value?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: CANONICAL ONLY, returning the existing `Dict[str, str]` shape unchanged. The map has THREE consumers beyond this view (`runner_shared.enforce_no_active_runner_conflict`, which only tests whether a value is non-empty; the `-o runs` sort; and the `--run-status` filter), and none needs the pre-canonical spelling: the alias tables are one-way by design and nothing writes a legacy spelling any more. Widening the value to a tuple or a dataclass would change a shape those consumers and their tests depend on (`tests/test_runner_active_conflict.py` patches this function with plain `{"aaaaaa": "running"}` dicts) for no consumer's benefit. If a future view wants to show the raw spelling from a durable old run, that is a separate change with its own caller.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the OUTPUT of a script that builds a live run directory whose queue holds every member of `runner_shutdown.KNOWN_ITEM_STATUSES` and prints, one line per status, the value `get_active_runs_map` returns plus the stage `lifecycle_style.resolve(FAMILY_RUNNER_ITEM, value)` gives it. Every line must show a value equal to that status's canonical spelling, no value may be a truncated fragment, and no line may show stage `unknown` or a non-empty diagnostic. Separately paste the output of `grep -n 'merging\|\[:7\]' agent_workflows/attention.py` showing no match inside `get_active_runs_map`. Paste the pytest summary line for the new totality test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the output of a test that places ONE id6 in TWO live run directories with different statuses and asserts the map reports the more significant one, run for at least three pairs (an in-flight status against a settled one, a queued status against an in-flight one, and two settled statuses). Paste the new `priority_order` table and show that every value `get_active_runs_map` can emit appears in it, computed from `KNOWN_ITEM_STATUSES` rather than read by eye.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the rendered `--runs` BOARD row (from `_render_item_row`, colored) for at least five distinct run states, showing the shared resolver's escape on each `[run:...]` cell. Paste `grep -n 'run_code' agent_workflows/attention.py` returning no match. Paste the assertion output proving the retired escapes are absent from the `[run:...]` CELL specifically, extracted from the row rather than matched against the whole line; state explicitly that a table-wide assertion was NOT used and name the two non-lifecycle uses (F-10) that make it unsatisfiable. If any state reaches the resolver as an activity, paste the resolved stage for it and show it is not `unknown`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the colored `--runs` TABLE (at least six rows spanning distinct stages) and the uncolored table for the same fixture, plus the output of the equivalence check that stripping ANSI from the first yields the second character for character. Paste `grep -n '38;5;' agent_workflows/attention.py` and state that no remaining match is a lifecycle color in a run branch, naming what each surviving match IS (F-10 names the expected survivors: the OQ-count column and the priority column both legitimately use 214). Paste the visible-width comparison from the F-7 assertion: the rendered column count of a VS-bearing Run cell and a single-codepoint one, measured with `T.visible_width`, shown EQUAL. Paste a run of `tests/test_run_summary_table.py` and `tests/test_ipd_lint.py` showing both still green and UNMODIFIED, since each pins a 214 escape this plan must not disturb.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the new `--runs` header line and a row containing `already-landed` (the 14-character longest canonical word) showing it UNTRUNCATED and aligned under the header. Paste the BEFORE and AFTER of each of the four changed assertions in `tests/test_attention.py` (the `startswith("  Status   Run     Type")` header check and the three exact cell strings), and state for each what it became and why. Paste a default (non-`runs_mode`) table for the same fixture showing it is BYTE-IDENTICAL to the pre-change output, proving the widening did not leak into the default view.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the output of the filter round-trip test: for every canonical status AND every legacy spelling in both alias tables, the item is matched by `--run-status <token>` and absent from the complement. Paste the `-o runs` sort output over a fixture holding one item per stage class, showing in-flight before queued before settled. Paste the new `--run-status` help text showing no unreachable example value. Paste `grep -rn 'RUN_SORT_ORDER\|_RUN_STATUS_ALIASES\|_RUN_SORT_RANK' agent_workflows/` and confirm no site still holds a copy of the retired six words, INCLUDING `_RUN_SORT_RANK`'s `getattr` fallback tuple. State explicitly, with the grep that shows it, that `RUN_SORT_ORDER` is not spec-governed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is authored for review and is NOT approved for execution. It requires explicit human sign-off (`aw ipd set approved <plan> --by-human --message ...`) before any code change.

Execution contract: commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never push. Report tests by pasting the ACTUAL runner output; run the suite BARE. Do not mark a `V-*` item complete from the matching execution checkmark; inspect the evidence in a separate pass.

Post-gate lifecycle move: once every `E-*` is performed and every `V-*` is verified with the concrete evidence demanded above, `aw ipd lint --phase pre-transition` must report conforming before the plan moves to `.aw/records/plans/executed/`. If any validation fails, leave the plan in `pending/` and record what failed rather than moving it.

- Size assessment: standard
- Cohesion rationale: not required
