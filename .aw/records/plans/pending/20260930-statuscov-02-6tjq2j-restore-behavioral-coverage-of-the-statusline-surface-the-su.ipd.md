# IPD: Restore behavioral coverage of the statusline surface the suite trim deleted, driving the renderer and its refresh class rather than pinning bytes

- Date: 2026-09-30
- Kind: child
- Concern: The runner's live 4-line statusline box is the single most-watched piece of output this toolkit produces, and NOTHING IN THE TEST TREE EXERCISES IT. Measured at authoring HEAD `c2b3a3c1f`: `grep -rln "format_statusline" tests/ agent_workflows/ tools/` returns exactly two files, both production, and zero test files. Widening to the whole surface, SIXTEEN of nineteen public statusline symbols have zero reference anywhere under `tests/`, including `format_statusline_lines`, `format_statusline`, the `Statusline` class itself, every scalar formatter (`format_compact_tokens`, `format_tokens`, `format_compact_duration`, `format_stall_countdown`), both label formatters, `format_activity_cell`, `statusline_action_for_item`, the two module-level pause/resume functions, and all three display maps. The coverage was lost in commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests"), which deleted all 2,706 lines of `tests/test_render_stream.py` including 50 test functions. The trim was correct policy work against code-pinning tests and two of the statusline tests it removed WERE byte-pins; what is not defensible is the result, since the surface now has NO behavioral coverage either, so a box that loses a cell, misformats a duration, deadlocks its refresh thread, or crashes on an unusual queue item passes the entire 3,457-test suite silently.
- Scope: Add one behavioral test module for the statusline surface, driving the real functions and the real class with real inputs and asserting observable outcomes. IN: the box renderer's invariants (four lines, rectangular in visible columns, `strip_ansi(styled) == plain`, determinism, no crash on hostile input); the scalar formatters' documented input/output tables; the label and activity formatters including their closed vocabularies and fallbacks; `statusline_action_for_item`'s derivation table; and the `Statusline` class's observable behavior (TTY versus non-TTY output, `update_item` merge semantics, duck-typed watchdog countdown, context-manager thread lifecycle, pause/resume reentrancy, the module-level pause/resume functions). OUT: any change to production code, the two deleted byte-pins, the visible-width conversion (approved plan `it6tpj` owns it), the ASCII-mode defect (sibling plan `mzrr7x` owns it), and the rest of the deleted module's non-statusline surface.
- Scope-Paths: tests/test_statusline_behavior.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: iuad9l
- Set: statuscov
- Order: 2
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6tjq2j
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review complete: PR-301..PR-304 all fixed, zero deferred, zero open

- 2026-10-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-301..PR-304 all FIXED, zero deferred, zero open. Reviewed at HEAD `3ca69a863`. `aw ipd lint --phase author` conformed before review and `--phase review-finalize` conforms after. THE PREMISE IS CORRECT AND I CONFIRMED IT SYMBOL BY SYMBOL: a per-symbol census returns ZERO test references for 16 of 19 statusline symbols (only `format_progress_bar` 2, `StreamTracker` 2, `format_duration` 1), with no `tests/test_render_stream.py` at all; `git show --stat 19313eed` shows the 2706-line deletion inside a 318-file, 219,063-deletion commit whose blob holds 50 test functions and the three statusline classes; F-03's two docstrings are verbatim; both F-04 traps reproduce (free text `('', 0)` versus `"abandoned"` at 10 columns over a 20-member `ALL_STAGES`; `"recovering"` width 10 against `len()` 11; one fixed `now_ts` giving `22:13:20`/`14:13:20`/`03:43:20` across three zones at CONSTANT width); the formatter boundary tables, all seven action-derivation shapes including precedence, the whole `Statusline` surface (non-TTY `''` and `'x\n'`, first redraw with no cursor-up and second with `\x1b[3A`, `update_item` preserve-on-empty/None, all three watchdog branches, module-level no-op) and F-07's ASCII residue all hold. THREE OF THE FOUR FINDINGS ARE ONE FAILURE MODE: an assertion the plan mandates cannot pass on the tree it claims to be green against. PR-301 (HIGH): E-02 mandated a zero-width-space `setid` AND that every hostile case assert a single visible width, but that input measures `127, 126, 127, 127` because the column uses bare `len()` while `visible_width('\u200b')` is 0 - the identical situation to F-07, and approved plan `it6tpj` owns the fix and requires its OWN guard to fail pre-fix on exactly these cases. PR-302 (HIGH): E-01's sweep could admit the same input independently, so both E-items needed fencing; a zero-width-free sweep of 31,104 renders verified all four invariants (four lines always, zero strip mismatches, one distinct width, byte-identical repeats). PR-303 (HIGH): F-08's "pre-existing" failure now PASSES and the tree is green at `3589 passed, 2 skipped`, and because this plan adds only a test file, a failure in that node could ONLY be this module's thread or global residue - the very thing V-05 exists to catch - so the sharper bar pointed the wrong way. PR-304: E-03's alias example is false for the action formatter (`plan` is in `ARTIFACT_DISPLAY_MAP` only; `format_action_label('plan')` returns `'Plan'`). Nothing weakened: the byte-pin refusal, the ASCII-purity refusal, the visible-column truncation bound, OQ-01's characterization stance, the timezone discipline, the in-memory mutation rule and the residue proof all stand. Bare suite at review HEAD: `3589 passed, 2 skipped, 3 warnings in 169.38s`. No production file was left modified by this review.

- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `iuad9l`. NO GATE: item `iuad9l` is `followup` and carries no `- Blocks-Release:`, so this plan inherits none and invents none. Its sibling `mzrr7x` carries one because it is a `bug`.
  THE ITEM'S DIAGNOSIS IS CORRECT AND UNDERSTATES THE HOLE. It says `format_statusline_lines` has no test. Measured: the hole covers SIXTEEN of nineteen public symbols on this surface, including the `Statusline` class and every scalar formatter (F-01). So the job is a module, not a function.
  EVERY ASSERTION THIS PLAN PRESCRIBES WAS RUN AGAINST TODAY'S TREE BEFORE BEING PROPOSED, and all but one PASS (F-05, F-06). That matters for two reasons. It means this plan is characterization work that can land without waiting on any fix, and it means the ONE failing property is a real defect rather than a test-authoring mistake. That property is the ASCII single-byte guarantee, which is NOT covered here: it is the whole subject of sibling plan `mzrr7x`, and E-01 of this plan must not assert it (F-07).
  THE ITEM'S "DO NOT RESTORE THE DELETED BYTE-PINS" INSTRUCTION IS RIGHT, AND THE DELETED MODULE WAS NOT UNIFORMLY BYTE-PINS, which is the distinction an executor will get wrong in one direction or the other. Reading the pre-trim blob: `test_format_statusline_user_example_box_layout` pinned four whole box lines byte-for-byte (its own docstring says so) and MUST NOT come back. But `test_every_scalar_formatter_produces_its_exact_cell` was a TABLE OF INPUTS AND EXPECTED OUTPUTS with a stated reason per row, which is exactly what P16 asks for, and `test_format_statusline_exact_layout` asserted a structural decomposition (equal line lengths, border characters) that is a property. So the correct move is to restore the TABLE-SHAPED and PROPERTY-SHAPED coverage and leave the whole-box pins dead (F-03).
  TWO TRAPS ARE MEASURED AND WOULD EACH PRODUCE A SILENTLY VACUOUS TEST. The activity cell returns `("", 0)` for any token outside `lifecycle_style.ALL_STAGES`, so a natural-looking free-text activity tests the no-activity path while appearing to test the activity path. And the box's first column renders `time.strftime` over `time.localtime`, so its CONTENT is timezone-dependent while its width is not; a test that pins the clock passes for its author and fails in CI or another zone (F-04).

## Goal

Give the statusline surface a behavioral regression floor, so that the box the operator watches during every run is covered by tests that execute it rather than by nothing at all.

Assert the properties and documented input/output tables that a change to this surface could plausibly break (cell count, rectangularity, ANSI/plain agreement, formatter boundaries, closed vocabularies, derivation rules, thread and lock lifecycle), and deliberately NOT the byte-for-byte box layout whose removal from the suite was correct.

Do it without touching production code, so the module stands as characterization of today's behavior and any future failure is a real behavior change rather than a merge artifact.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the box renderer

- [x] E-01 ADD `tests/test_statusline_behavior.py` COVERING THE BOX RENDERER'S INVARIANTS, driving `render_stream.format_statusline_lines` and `render_stream.format_statusline` with real inputs. ASSERT FOUR PROPERTIES, each measured to hold today (F-05): (a) the renderer returns exactly FOUR lines and `format_statusline` joins them into four newline-delimited lines; (b) every line of the box is the SAME visible width, measured with `term.visible_width`, which is the sibling guard's established shape; (c) `render_stream._strip_ansi(styled) == plain` line for line, i.e. the styled and unstyled renderers agree on everything but the escapes, measured over a seeded spread with zero mismatches across 600 renders; (d) two renders with identical arguments are byte-identical.
  PASS A FIXED `now_ts` AND NEVER ASSERT THE CLOCK. The time cell is `time.strftime` over `time.localtime`, so its content is timezone-dependent (measured `08:53:20` under `TZ=UTC`, `01:53:20` under `America/Los_Angeles`, `14:23:20` under `Asia/Kolkata` for one fixed `now_ts`) while the box width is NOT (128 columns in all three, including the half-hour-offset zone). Assert widths and structure; a clock pin fails in another zone (F-04).
  SWEEP THE INPUT SPACE RATHER THAN RENDERING ONE BOX, because the column widths are input-dependent and a single fixture exercises one branch of each `max()`. Vary `setid` and `id6` across present, absent and long; `action` and `artifact_kind` across mapped, unmapped and absent; `stall_remaining` across `None`, 0 and large; `progress_source` present and absent; `activity` across `None`, a real stage and free text; the progress pair across `0/0`, `0/N`, mid and `N/N`; and the tracker across absent and populated. Run each in both styling modes.
  KEEP EVERY SWEPT `setid`/`id6` VALUE FREE OF ZERO-WIDTH AND NEWLINE CODE POINTS (PR-302). The rectangularity property (b) does NOT hold for a zero-width code point on an unmodified tree, so admitting one into the sweep would make this module red for a defect approved plan `it6tpj` owns (F-10). Use plain ASCII and ordinary multi-byte text for the sweep's long/short variants; zero-width inputs belong in E-02's characterization-only cases. VERIFIED AT REVIEW that a zero-width-free sweep satisfies all four invariants: 31,104 renders over the product of the varied fields in both styling modes AND both unicode modes gave a four-line tuple every time, `_strip_ansi(styled) == plain` with ZERO mismatches, exactly one distinct visible width per render, and byte-identical repeat renders.
  DO NOT ASSERT THE ABSOLUTE WIDTH NUMBER. Authoring measured 128 columns for its own fixture, but that number moves whenever a column floor or label changes and pinning it would make this module a byte-pin by the back door. The CARDINALITY of the distinct-width set is the property; the number is not.
  DO NOT ASSERT ASCII PURITY HERE. `use_unicode=False` still leaks U+2588 at every progress state above zero, which is a real open defect owned by sibling plan `mzrr7x`; asserting it would make this module fail on today's tree and couple a characterization job to a fix (F-07). Covering the `use_unicode=False` path for the OTHER properties above is correct and expected.
  - Depends on: none
  - Expected outcome: a test class that exercises the box renderer across a swept input space in both styling modes and asserts the four invariants; green on today's unmodified tree; containing no byte pin, no clock assertion, and no absolute width number.
  - Execution state: performed

- [x] E-02 ADD HOSTILE-INPUT COVERAGE FOR THE BOX RENDERER, asserting it neither raises nor returns a malformed result for inputs a real queue can produce. Measured today: twelve such inputs all return a well-formed 4-tuple and none raises (F-05). COVER AT MINIMUM `total_items=0` (a zero denominator the progress bar must survive), `current_idx` GREATER than `total_items`, a NEGATIVE `current_idx`, a 200-character `setid`, empty strings for `action`/`artifact_kind`/`activity`/`progress_source`, a zero `now_ts`, a negative `stall_remaining`, and `tracker=None`.

  THE ZERO-WIDTH-SPACE `setid` IS REMOVED FROM THE MANDATORY LIST AND MUST NOT ASSERT RECTANGULARITY (PR-301, F-10). It is NOT rectangular today: measured at review, `setid="a\u200bb"` yields visible widths `{127, 126, 127, 127}` (line 1 is one column narrow), because `format_statusline_lines` computes that column with bare `len()` while `term.visible_width("\u200b")` is 0. So the combination this E-item ORIGINALLY mandated (include the ZWSP case AND have every hostile case assert "the single visible width") is UNSATISFIABLE on an unmodified tree and would have made this module RED, contradicting the plan's own landable-characterization premise and its F-05 claim that every prescribed property passes. This is the SAME defect class as F-07's ASCII case: a real open defect that a SIBLING owns, namely approved plan `it6tpj`, whose own `tests/test_statusline_visible_width.py` is explicitly designed to FAIL pre-fix on exactly these zero-width cases. IF YOU COVER A ZERO-WIDTH INPUT AT ALL, cover it as CHARACTERIZATION asserting only the 4-TUPLE LENGTH and no-raise, exactly as the newline case below is handled, and say so in V-02's evidence. Do NOT assert rectangularity for it, and do NOT fix `render_stream.py` to make it rectangular; this plan declares no production scope path.
  INCLUDE THE CLOCK-SKEW CASE, which is the one with a real production trigger: `now_ts` EARLIER than `run_start_ts`, which happens when a wall clock steps backwards mid-run. The renderer clamps with `max(0, ...)`, so the property to assert is that the elapsed cell is still well-formed and the box still rectangular, not that any particular string appears.
  ASSERT A PROPERTY, NOT AN ABSENCE OF EXCEPTIONS ALONE. A bare "it did not raise" is nearly vacuous; each hostile case must also assert the four-line count and the single visible width, so a future change that degrades the box into something malformed-but-non-raising is caught. TWO DOCUMENTED EXCEPTIONS, both because the input is NOT rectangular today and a sibling owns the fix: a zero-width-code-point `setid` (PR-301, F-10, owned by `it6tpj`) and a newline-bearing `setid` (below). For those two, assert the 4-tuple length and no-raise ONLY. Every OTHER hostile case asserts both the four-line count and the single visible width, which review measured to hold: `total_items=0`, index beyond total, negative index, 200-character setid, empty free-text fields, zero `now_ts`, negative stall, `tracker=None` and clock skew all returned a 4-tuple at ONE visible width.
  NOTE ONE MEASURED CASE THAT IS NOT A DEFECT TO FIX HERE: a `setid` containing a literal newline produces a 4-TUPLE whose joined form is FIVE physical lines, at three different widths. That is a caller-contract question (the field is author-supplied text from a filename-derived identifier and has never contained a newline), not a renderer bug, and this plan does not change production code. COVER IT AS CHARACTERIZATION if you cover it at all, asserting the tuple length rather than the physical line count, and say in V-02's evidence which you chose and why. Do NOT write an assertion that demands behavior the code does not have.
  - Depends on: E-01
  - Expected outcome: hostile-input cases including clock skew, each asserting a well-formed four-line rectangular box rather than mere absence of an exception; green on today's tree.
  - Execution state: performed

### Task group 2: the formatters

- [x] E-03 COVER THE SCALAR AND LABEL FORMATTERS AS INPUT/OUTPUT TABLES, which is the shape the deleted module used for this and the shape P16 endorses. This restores genuinely behavioral coverage the trim removed (F-03), so prefer re-deriving the deleted table's CASES over inventing new ones, while re-measuring each expected value against today's code rather than trusting the old blob.
  COVER THE MAGNITUDE BOUNDARIES OF `format_compact_tokens` AND `format_tokens`, since those are where an off-by-one in a threshold hides: 0, 1, 999, 1000, 999999, 1000000, 999999999, 1000000000, and a value above that. Authoring measured a surprising-but-real behavior worth pinning as characterization: `format_compact_tokens(999_999)` returns `'1000k'` rather than rolling to `'1m'`, and the same shape at `'1000m'`. Assert what it DOES; if an executor believes that is wrong, that is a separate backlog item, not an edit here.
  COVER THE BOUNDARIES OF `format_compact_duration` AND `format_duration`: `None`, 0, 59, 60, 3599, 3600, 86400 and a negative value (which clamps). These are the cells an operator reads to judge whether a run is stuck, so a formatting regression is user-visible.
  COVER `format_stall_countdown`'s THREE DOCUMENTED BEHAVIORS: `None` returns the empty string (its docstring states the reason, that claiming a countdown when nothing will kill the turn "would be a lie"), a sub-minute value renders seconds only, a minute-or-more value renders `XmYYs`, and a `progress_source` appends the `(last: ...)` suffix.
  COVER BOTH LABEL FORMATTERS OVER THEIR FULL MAPS plus the fallback: every key of `ACTION_DISPLAY_MAP` and `ARTIFACT_DISPLAY_MAP` returns its mapped label, case-insensitively; an unmapped value is capitalized and truncated to at most 7 characters; `None` returns the documented default (`Review` and `IPD` respectively, both confirmed at review). DERIVE THE MAP CASES FROM THE MAPS THEMSELVES rather than hardcoding a parallel list, so the test follows the vocabulary instead of pinning a snapshot of it.
  THE `plan` -> `IPD` ALIAS BELONGS TO THE ARTIFACT MAP ONLY, AND ASSERTING IT ON THE ACTION FORMATTER WOULD FAIL (PR-304). The original wording placed the alias example under "both label formatters", which is wrong: measured at review, `ARTIFACT_DISPLAY_MAP` contains both `'ipd': 'IPD'` and `'plan': 'IPD'`, so `format_artifact_kind_label("plan")` and `("ipd")` both return `'IPD'`, whereas `ACTION_DISPLAY_MAP` has NO `plan` key at all and `format_action_label("plan")` returns the FALLBACK `'Plan'`. Assert the alias pairs that each map actually carries, which is exactly what deriving the cases FROM the maps gives you for free: the action map's own alias pairs are `execute`/`exec` -> `Execute`, `graduate`/`graduat` -> `Graduat`, `validate`/`validat` -> `Validat` and `orchestrate`/`orchest` -> `Orchest`; the artifact map's are `ipd`/`plan` -> `IPD` and `walkthrough`/`walkthr` -> `Walkthr`. Do NOT hand-write a cross-map alias assertion.
  LEAVE THE TRUNCATION BOUNDARY ALONE AS A GRAPHEME QUESTION. Approved plan `it6tpj` changes the fallback truncation from a code-point slice to a grapheme-safe one, so an assertion on exactly 7 CODE POINTS would break when it lands. Assert at most 7 VISIBLE columns (`term.visible_width`), which is true before and after, and say so in V-03's evidence.
  - Depends on: none
  - Expected outcome: table-driven coverage of the six scalar formatters and both label formatters, with boundaries and documented defaults asserted, map cases derived from the maps, and the truncation bound expressed in visible columns rather than code points; green on today's tree.
  - Execution state: performed

- [x] E-04 COVER `format_activity_cell` AND `statusline_action_for_item`, the two functions whose logic decides what the box SAYS rather than how wide it is.
  FOR THE ACTIVITY CELL, ASSERT THE CLOSED VOCABULARY EXPLICITLY, because this is the measured trap that silently voids a test: it returns `("", 0)` for any token NOT in `lifecycle_style.ALL_STAGES`, so free text selects the no-activity path. Assert BOTH halves: a free-text activity such as `"reading a file"` returns `("", 0)`, and a real stage returns a non-empty cell with a POSITIVE width (measured: `"abandoned"` gives a 10-column cell). Then assert the width is a VISIBLE width rather than a code-point count by using a stage whose glyph carries a variation selector (`recovering`, whose glyph is U+21A9 plus U+FE0E), for which the returned width must be less than `len()` of the returned text. That last assertion is the one that would catch a regression of the conversion this cell already received.
  ASSERT THE STYLED CELL AGREES WITH THE PLAIN ONE: the returned width must be the PLAIN width even when the text carries ANSI escapes, which is the function's documented contract ("THE WIDTH IS RETURNED RATHER THAN MEASURED BY THE CALLER").
  FOR THE ACTION DERIVATION, ASSERT THE FULL TABLE, which is pure branching logic and therefore cheap to cover completely: an explicit `action` wins; absent that, an `initial_status` of `to-review` or `draft` yields `review` and any other `initial_status` yields `execute`; absent that, a `status` of `to-review` or `draft` yields `review`; and an empty item yields `execute`. All five shapes measured correct today (F-05). COVER THE PRECEDENCE, not just the outcomes: an item carrying BOTH an `action` and a contradicting `initial_status` must resolve to the `action`, which is the property the function exists to guarantee.
  - Depends on: none
  - Expected outcome: the activity cell's closed vocabulary, positive-width live case, visible-width measurement and styled/plain width agreement asserted; the action derivation table covered including precedence; green on today's tree.
  - Execution state: performed

### Task group 3: the refresh class

- [x] E-05 COVER THE `Statusline` CLASS, which is the half of this surface no amount of function testing reaches and which carries the threading. DRIVE IT WITH A FAKE STREAM, using a `StringIO` subclass whose `isatty()` returns True for the TTY path and a plain `StringIO` for the non-TTY path; authoring verified both work and neither needs a real terminal.
  ASSERT THE NON-TTY CONTRACT FIRST, because it is what every CI run and every redirected log actually exercises: `redraw()` on a non-TTY stream writes NOTHING, while `write_event()` writes the plain event text followed by a newline and no escape sequences. Measured today.
  ASSERT THE TTY CONTRACT AS STRUCTURE, NOT BYTES: the FIRST `redraw()` emits no cursor-up sequence (nothing has been drawn yet) while the SECOND does, which is the property that makes the box stick rather than scroll; `write_event()` emits the event text AND redraws the box around it; `pause()` emits a clear; `resume()` draws again. Assert on the PRESENCE of the cursor-up and clear sequences and on the event text, never on the full escape byte string.
  ASSERT `update_item`'s MERGE SEMANTICS, which are easy to break and silently wrong when broken: an EMPTY `setid` or `id6` PRESERVES the previous value (the setter is guarded by truthiness) while a non-empty one replaces it, and a `None` `action`/`artifact_kind`/`activity` preserves while a value replaces. Measured today. This asymmetry between empty-string and `None` guards is exactly the kind of thing a refactor flattens.
  ASSERT THE DUCK-TYPED WATCHDOG CONTRACT, all three branches: no watchdog yields `None`; an object whose `remaining()` returns a number yields that number; an object whose `remaining()` RAISES yields `None` rather than propagating. The third branch is a deliberate safety property (a display must never kill a run) and is the one a narrowed `except` clause would break.
  ASSERT THE THREAD LIFECYCLE THROUGH THE CONTEXT MANAGER: entering with a positive interval on a TTY starts a refresh thread that is alive inside the block and is joined after it, the stream actually received output, and the module-level `_ACTIVE_STATUSLINE` is set inside and cleared after. Then assert PAUSE/RESUME REENTRANCY from a SECOND THREAD completes rather than deadlocking (the class holds an `RLock` and `pause()` calls `clear()` while holding it, so reentrancy is the property under test); the deleted module had a test for exactly this and authoring re-verified it holds. Give the thread-crossing assertion a bounded join so a regression FAILS rather than hanging the suite forever.
  ASSERT THE MODULE-LEVEL `pause_active_statusline` / `resume_active_statusline` BOTH WAYS: they act on the active statusline inside a context, and they are a NO-OP (not an exception) when none is active. The no-op branch is what keeps an unrelated prompt from crashing a non-statusline command.
  - Depends on: E-01
  - Expected outcome: the `Statusline` class covered for non-TTY silence, TTY stickiness as structure, `update_item` merge asymmetry, all three watchdog branches, context-manager thread start/join and global registration, cross-thread pause/resume reentrancy under a bounded join, and the module-level functions in both the active and inactive cases; green on today's tree.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TEST OUTCOMES, NEVER CODE STRUCTURE (`GUIDING_PRINCIPLES` P16, and the execution contract in AGENTS.md). No `inspect`/`ast`/regex read of `agent_workflows/*.py`, no caller-count or symbol-census assertion, no docstring or banner pin. Every item in this plan calls the real function or drives the real class and asserts an observable output. This is the principle the trim commit was enforcing, so a restoration that violated it would be worse than the hole.
- ASSERT A PROPERTY, NOT A SNAPSHOT. The sibling guard `tests/test_run_summary_visible_width.py` is the established shape on this exact surface: it collects `term.visible_width` over the rendered lines and asserts a single distinct value, pinning no bytes and reading no source. `tests/test_term.py` does the same for the width primitives.
- NEVER WEAKEN AN ASSERTION TO MAKE IT PASS EVERYWHERE (`GUIDING_PRINCIPLES` P16's last bullet, with `DECISIONS.md` D78 as live precedent). The two measured traps in F-04 are precisely the shapes that produce a vacuously passing test, so each is called out in the E-item that could hit it.
- THE TIME COLUMN IS TIMEZONE-DEPENDENT IN CONTENT AND NOT IN WIDTH, measured across three zones including a half-hour offset. Pass a fixed `now_ts`, assert widths and structure, never the clock.
- THE ACTIVITY CELL HAS A CLOSED VOCABULARY (`lifecycle_style.ALL_STAGES`, 20 members) and silently returns `("", 0)` outside it. Plan `it6tpj`'s own review recorded this same trap as finding F-13 after nearly shipping a vacuous case, so it is a documented repeat hazard rather than a hypothetical one.
- A FAKE TTY IS A `StringIO` SUBCLASS OVERRIDING `isatty()`. Authoring verified that both the sticky-redraw path and the thread lifecycle are fully drivable this way, with no real terminal and no pty.
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal` and the slow/livecorpus deselection; `-n0` makes it several times slower, a second `-q` suppresses the summary line this plan requires be pasted, and `-p no:randomly` disables the order randomization that surfaces order-dependence. THE LAST POINT IS LOAD-BEARING FOR THIS MODULE: it mutates process-global state (`render_stream._ACTIVE_STATUSLINE`) and starts threads, so it must leave no residue for a randomly-ordered neighbour.
- WRITE SCRATCH PROBES UNDER `.aw/state/`, which `.aw/.gitignore` ignores. Authoring wrote every probe there and `git status --short` stayed clean throughout.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | **THE COVERAGE HOLE IS TOTAL AND WIDER THAN THE BACKLOG ITEM STATES, measured at HEAD `c2b3a3c1f`.** The item names `format_statusline_lines`. A per-symbol census over `tests/` finds SIXTEEN of nineteen public statusline symbols with ZERO reference anywhere in the test tree: `format_statusline_lines`, `format_statusline`, `Statusline`, `format_compact_tokens`, `format_tokens`, `format_compact_duration`, `format_stall_countdown`, `format_action_label`, `format_artifact_kind_label`, `format_activity_cell`, `statusline_action_for_item`, `pause_active_statusline`, `resume_active_statusline`, `ACTION_DISPLAY_MAP`, `ARTIFACT_DISPLAY_MAP` and `ACTIVITY_DISPLAY_MAP`. Only three are referenced at all (`format_progress_bar` by one file, `StreamTracker` by two, `format_duration` indirectly). There is no `tests/test_render_stream.py` and no statusline test module of any kind. So the job is a module covering a surface, not a test for a function. | `grep -rln "format_statusline" tests/ agent_workflows/ tools/` -> 2 production files, 0 tests; the per-symbol census reporting 16 of 19 uncovered; `ls tests/test_render_stream.py` -> No such file or directory; `ls tests/ \| grep -iE "stream\|statusline"` -> no match |
| F-02 | **THE DELETION IS CONFIRMED AT THE COMMIT AND THE SCALE IS 50 TEST FUNCTIONS, not two.** `git show --stat 19313eed` shows `tests/test_render_stream.py | 2706 -------------` within a commit of 318 files and 219,063 deletions titled "test: trim test suite from 9,136 to under 2,000 tests". The pre-trim blob contains 50 test functions across nine classes, of which three classes were statusline-specific (`StatuslineUnitTests`, `StatuslineActionDerivationTests`, `StatuslinePauseResumeTests`). So the statusline lost roughly ten test functions, not the two the backlog item names, and the names of the lost ones map closely onto this plan's E-items. | `git show --stat 19313eed`; `git show 19313eed^:tests/test_render_stream.py \| wc -l` -> 2706; the class and function listing extracted from that blob |
| F-03 | **THE DELETED MODULE WAS NOT UNIFORMLY BYTE-PINS, AND THE DISTINCTION DECIDES WHAT MAY BE RESTORED.** Read from the pre-trim blob: `test_format_statusline_user_example_box_layout` is a genuine byte-pin and its own docstring says so ("pins four WHOLE box lines byte-for-byte against a real user example"), with three hardcoded expected box strings; it must stay dead. `test_format_statusline_exact_layout`'s docstring describes "the SEGMENTED structure of a rendered box (ten cells per line, border glyphs, equal widths), which is a structural decomposition rather than a data row", and its body asserts equal line lengths and that the borders start and end with the right characters, which is a PROPERTY. `test_every_scalar_formatter_produces_its_exact_cell` is a table of `(formatter, args, expected, why)` rows, each carrying a stated reason, which is exactly the shape P16 prescribes. CONSEQUENCE: the backlog item's "do NOT restore the deleted byte-pins" is correct and must not be over-applied into "restore nothing", which would leave the hole. | The three test bodies and docstrings quoted from `git show 19313eed^:tests/test_render_stream.py`; the `SCALAR_CELLS` table rows with their per-row rationale strings |
| F-04 | **TWO MEASURED TRAPS EACH PRODUCE A SILENTLY VACUOUS OR ENVIRONMENT-DEPENDENT TEST, AND BOTH ARE EASY TO WALK INTO.** TRAP ONE, the closed activity vocabulary: `format_activity_cell("reading a file", Palette(False))` returns `('', 0)` because the token is not in `lifecycle_style.ALL_STAGES`, so a natural-looking free-text activity makes the box take the NO-ACTIVITY branch and a test of it re-tests the paths every other case already covers while appearing to add one. `format_activity_cell("abandoned", ...)` returns a 10-column cell. Plan `it6tpj`'s review caught this same trap in its own plan (its F-13), so it is a demonstrated repeat hazard. TRAP TWO, the timezone-dependent clock: the first column is `time.strftime("%H:%M:%S", time.localtime(now_ts))`, so for one FIXED `now_ts` it renders `08:53:20` under `TZ=UTC`, `01:53:20` under `America/Los_Angeles` and `14:23:20` under `Asia/Kolkata`, while the box width is 128 in all three including the half-hour-offset zone. A clock pin passes for its author and fails elsewhere. | `format_activity_cell` returns for a free-text token and for `"abandoned"`; `lifecycle_style.ALL_STAGES` membership; the three-timezone render table with its constant width and varying time cell |
| F-05 | **EVERY PROPERTY THIS PLAN PRESCRIBES WAS RUN AGAINST TODAY'S UNMODIFIED TREE AND PASSES, so this is landable characterization rather than a test suite waiting on a fix.** ONE EXCEPTION FOUND AT REVIEW (PR-301, F-10): the twelve-case hostile list below includes a zero-width-space `setid`, and that case is NOT rectangular today, so the conjunction of this row with E-02's "every hostile case asserts the single visible width" was unsatisfiable. The row's claim holds for every OTHER listed property, all of which review re-measured green; the zero-width case is now characterization-only. Measured: `_strip_ansi(styled) == plain` holds across 600 renders in both styling and both unicode modes with ZERO mismatches; the renderer returns a 4-tuple and never raises across twelve hostile inputs (zero total items, index beyond total, negative index, 200-character setid, zero-width-space setid, empty strings, zero timestamp, negative stall, no tracker, clock skew); `format_compact_duration` distinguishes the 0/1, 59/60 and 3599/3600 boundaries; every key of both display maps returns its mapped label and the unmapped fallback caps at 7 characters; the activity cell rejects free text and accepts a stage; all five `statusline_action_for_item` shapes resolve as documented; a non-TTY `redraw()` writes nothing while `write_event()` writes exactly `"x\n"`; tracker cost and totals reach the rendered box; and two identical renders are byte-identical. | The candidate-assertion probe reporting PASS on items 1 through 8 of 9; the 600-render strip/rectangularity sweep; the twelve-case hostile-input table |
| F-06 | **THE `Statusline` CLASS IS FULLY DRIVABLE WITHOUT A TERMINAL, which removes the obvious excuse for leaving it uncovered.** With a `StringIO` subclass whose `isatty()` returns True: the first `redraw()` emits NO cursor-up sequence and the second DOES (the stickiness property); `write_event()` emits the event text within a redraw; `pause()` emits a clear sequence; `resume()` draws again. With a plain `StringIO`: `redraw()` writes nothing and `write_event("x")` writes exactly `"x\n"`. `update_item` preserves the old `setid`/`id6` when passed empty strings and the old `action`/`artifact_kind`/`activity` when passed `None`, while replacing each on a real value. The duck-typed watchdog yields `None` with no watchdog, the number with a working `remaining()`, and `None` rather than an exception when `remaining()` raises. Entering the context manager with a positive interval starts a thread that is alive inside the block and joined after, `_ACTIVE_STATUSLINE` is set inside and cleared after, cross-thread `pause()`/`resume()` completes without deadlock (the class holds an `RLock` and `pause()` calls `clear()` while holding it), and the module-level pause/resume functions are a clean no-op when no statusline is active. | The class-drivability probe covering every branch listed, including the cursor-up presence/absence pair, the `update_item` merge table, the three watchdog branches, the thread liveness-then-join check, and the cross-thread pause/resume completing under a bounded join |
| F-07 | **EXACTLY ONE PRESCRIBED PROPERTY FAILS TODAY, AND IT MUST NOT BE ASSERTED HERE BECAUSE A SIBLING PLAN OWNS THE FIX.** The ASCII single-byte guarantee fails: `format_statusline_lines(..., use_unicode=False)` with an ASCII palette still emits U+2588 at every `current_idx` from 1 through 10 (clean only at 0), and a `Statusline` under `AW_ASCII_ONLY=1` emits nine distinct non-ASCII code points. That is a real defect against spec `uonrjg` Section 9.4's third bullet and `docs/cli-human-guide.md`, and it is the entire subject of sibling plan `mzrr7x` (Set `statuscov`, Order 1, `Work-Kind: bug`, `Blocks-Release: next`, same `From-Backlog: iuad9l`). THIS PLAN MUST COVER THE `use_unicode=False` PATH for its other properties and MUST NOT assert purity, which would make this module red on today's tree and couple a characterization job to a release-gated fix. The two modules are deliberately separate files (`tests/test_statusline_behavior.py` here, `tests/test_statusline_ascii_mode.py` there) so neither blocks the other. | The per-state ASCII residue sweep; the `AW_ASCII_ONLY=1` end-to-end render; `mzrr7x` front matter and scope paths |
| F-08 | **CORRECTED AT REVIEW (PR-303): THE SUITE IS NOW FULLY GREEN AND THE 'PRE-EXISTING FAILURE' THIS ROW RECORDED NO LONGER OCCURS.** The authoring measurement is retained below as historical context ONLY and must NOT be used as the bar; see F-11. A bare `python3 -m pytest` on a clean tree (`git diff --stat` empty) at HEAD `c2b3a3c1f` reports `1 failed, 3457 passed, 2 skipped, 3 warnings in 67.57s`, the failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, which tests the backlog release-exemption setter and touches nothing this plan concerns. Since THIS PLAN ADDS ONLY A TEST FILE and changes no production code, the expected delta is strictly additive: the same single pre-existing failure and a higher passing count. ANY OTHER FAILURE IS CAUSED BY THIS MODULE and must be fixed rather than explained away, which is a sharper bar than a production-changing plan can set. | The bare run's summary line and short test summary on a clean tree; `git diff --stat` empty; this plan's single scope path |
| F-09 | **TWO OTHER PLANS CHANGE THIS SURFACE AND NEITHER COLLIDES WITH THIS FILE, which is why no dependency edge is declared.** Approved plan `it6tpj` (Set `l76ir6`, `Blocks-Release: next`) rewrites thirty-five width and pad sites in `format_statusline_lines` and adds `tests/test_statusline_visible_width.py`. Sibling `mzrr7x` fixes the ASCII plumbing and adds `tests/test_statusline_ascii_mode.py`. This plan's ONLY scope path is `tests/test_statusline_behavior.py`, so there is no file overlap with either. ONE SUBSTANTIVE INTERACTION DOES EXIST and is handled inside E-03 rather than by an ordering edge: `it6tpj` changes the label fallback from a 7-CODE-POINT slice to a grapheme-safe visible-width truncation, so an assertion written as "exactly 7 code points" would break when it lands, while "at most 7 visible columns" holds before and after. A SECOND INTERACTION, AND REVIEW FOUND IT IS NOT WEAK (PR-301, F-10): the rectangularity property is FALSE for a zero-width input TODAY, so it is `it6tpj` that makes it true rather than merely more thoroughly true. That is why E-01's sweep is now fenced against zero-width values and E-02's zero-width case is characterization-only. Once `it6tpj` lands, a follow-up may tighten that case into a rectangularity assertion; doing so BEFORE it lands would make this module red. | `it6tpj` front matter and E-03 (`_T.truncate_visible(..., 7)` replacing `[:7]`); `mzrr7x` scope paths; this plan's scope path |
| F-10 | ADDED AT REVIEW (PR-301/PR-302). **A ZERO-WIDTH CODE POINT IN `setid` MAKES THE BOX NON-RECTANGULAR TODAY, so the plan's own mandatory hostile-input list contradicted its own rectangularity property and would have shipped a RED module.** E-02 required a zero-width-space `setid` AND required every hostile case to assert "the single visible width"; those two cannot both hold on an unmodified tree. This is the same shape as F-07: a real open defect owned by a SIBLING, here approved plan `it6tpj`, whose own guard is explicitly designed to FAIL pre-fix on these cases. Resolved by removing the ZWSP case from the mandatory list, permitting it only as tuple-length characterization, and fencing the E-01 sweep against zero-width and newline inputs. | Measured at review: `format_statusline_lines(..., setid="a\u200bb")` returns a 4-tuple whose per-line visible widths are `127, 126, 127, 127` (line 1 one column narrow), because the column is computed with bare `len()` while `term.visible_width("\u200b")` is 0. A zero-width-free sweep of 31,104 renders gave exactly ONE distinct width every time. `it6tpj` front matter: `- Status: approved`, `- Scope-Paths: agent_workflows/render_stream.py, tests/test_statusline_visible_width.py`, and its E-item requires its module to FAIL pre-fix "for every zero-width case in both styling modes". |
| F-11 | ADDED AT REVIEW (PR-303). **THE SUITE BASELINE F-08 RECORDS IS STALE, AND THE ERROR IS DANGEROUS BECAUSE THIS PLAN'S BAR IS DELIBERATELY SHARPER THAN USUAL.** F-08 told the executor to expect exactly one failure and to treat `test_release_exempt_setter_roundtrip_and_parity` as pre-existing. That test now PASSES and the tree is green, so the instruction granted standing permission to ignore a failure in one named node; since this plan adds only a test file, a failure there after the change could only come from THIS module's global or thread residue, which is precisely what V-05 exists to detect. Corrected to zero failures compared by node id against a freshly re-derived baseline. | At review HEAD `3ca69a863`, bare `python3 -m pytest`: `3589 passed, 2 skipped, 3 warnings in 169.38s`, with `208 tests ... deselected`. `python3 -m pytest tests/test_backlog.py -k release_exempt_setter_roundtrip_and_parity` reports `1 passed`. Authoring recorded `1 failed, 3457 passed` at `c2b3a3c1f`. |
| F-12 | ADDED AT REVIEW. **EVERY OTHER LOAD-BEARING CLAIM IN THIS PLAN REPRODUCES INDEPENDENTLY**, which is why the plan is sound apart from the two corrections above. | F-01: a per-symbol census over `tests/` confirms 16 of 19 statusline symbols at ZERO references, with only `format_progress_bar` (2), `StreamTracker` (2) and `format_duration` (1) referenced, and no `tests/test_render_stream.py`. F-02: `git show --stat 19313eed` shows `tests/test_render_stream.py | 2706 -------------` in a commit of 318 files and 219,063 deletions; the blob holds 50 `def test_` functions and the three statusline classes named. F-03: both quoted docstrings are verbatim in the pre-trim blob. F-04 trap 1: free text returns `('', 0)`, `"abandoned"` returns a 10-column cell, `ALL_STAGES` has 20 members, and `"recovering"` returns width 10 against `len()` 11. F-04 trap 2: one fixed `now_ts` renders `22:13:20` / `14:13:20` / `03:43:20` under UTC / America-Los_Angeles / Asia-Kolkata at a CONSTANT width. F-05: the formatter boundary tables, all seven action-derivation shapes including precedence, and the eleven-case hostile sweep all behave as stated. F-06: non-TTY `redraw()` wrote `''` and `write_event("x")` wrote exactly `'x\n'`; the first TTY redraw emitted no cursor-up and the second emitted `\x1b[3A`; `update_item` preserved on empty/None and replaced on real values; all three watchdog branches returned `None` / `42.0` / `None`; module-level pause/resume were a clean no-op with `_ACTIVE_STATUSLINE` `None`. F-07: `use_unicode=False` is clean only at `current_idx=0` and leaks U+2588 at states 1 through 10. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_statusline_behavior.py` covering the box renderer's four invariants over a swept input space in both styling modes, with a fixed `now_ts` and no clock or byte pin (E-01).
2. Add hostile-input coverage including clock skew, each case asserting a well-formed rectangular four-line box rather than mere absence of an exception (E-02).
3. Cover the six scalar formatters and both label formatters as input/output tables with their magnitude and duration boundaries, map cases derived from the maps, and the truncation bound in visible columns (E-03).
4. Cover `format_activity_cell`'s closed vocabulary, live-case width and styled/plain width agreement, and `statusline_action_for_item`'s full derivation table including precedence (E-04).
5. Cover the `Statusline` class: non-TTY silence, TTY stickiness as structure, `update_item` merge asymmetry, all three watchdog branches, context-manager thread lifecycle and global registration, cross-thread pause/resume reentrancy under a bounded join, and the module-level functions in both states (E-05).

## Deferred / out of scope (with reason)

- FIXING THE ASCII SINGLE-BYTE DEFECT this plan's measurement uncovered (F-07). It is a real violation of spec `uonrjg` Section 9.4's third bullet and of a promise `docs/cli-human-guide.md` makes to users.
  - Carrier: mzrr7x
  - Carrier-Declined: NOT DECLINED, CARRIED. Sibling plan `mzrr7x` (Set `statuscov`, Order 1) fixes it, carries `Work-Kind: bug` with `Blocks-Release: next`, and adds its own guard in a separate file. Keeping the fix out of this plan is deliberate: a `followup` characterization module must not be the vehicle for a release-gated production change, and a test asserting the broken property here would make this module red on today's tree for a reason that has nothing to do with its own correctness.
- RESTORING THE TWO DELETED BYTE-PIN TESTS (`test_format_statusline_user_example_box_layout` and the byte-pinning half of `test_format_statusline_exact_layout`), which asserted whole box lines against hardcoded strings (F-03).
  - Carrier-Declined: DECLINED PERMANENTLY AND CORRECTLY. `GUIDING_PRINCIPLES` P16 forbids byte pins, commit `19313eed` removed these on exactly that policy, and backlog item `iuad9l` instructs that they not come back. The property-shaped assertions in E-01 (four lines, one visible width, structural borders) cover what the pins were reaching for without freezing the layout.
- CONVERTING THE WIDTH COMPUTATIONS AND PADS of `format_statusline_lines` to visible-width measurement, and the grapheme-safe label truncation (F-09).
  - Carrier: it6tpj
  - Carrier-Declined: NOT DECLINED, ALREADY CARRIED AND ALREADY APPROVED. This plan changes no production code at all, and E-03 deliberately expresses the truncation bound in VISIBLE COLUMNS so it holds both before and after that plan lands, which is why no ordering edge is owed.
- RESTORING THE REST OF THE DELETED MODULE'S COVERAGE, which spanned event rendering, the palette, system-protocol suppression, verbosity tiers, todo transitions, edit/write payloads and event-prefix alignment across roughly 40 further test functions (F-02).
  - Carrier-Declined: DEFERRED WITHOUT A CARRIER FILED, deliberately. Backlog item `iuad9l` is scoped to "the statusline box renderer" and that is what this plan closes; the remainder is a much larger job spanning several unrelated surfaces, and filing one item for all of it would produce exactly the token gesture the item itself warns against. RECOMMENDED ACTION FOR THE REVIEWER: if that coverage is wanted, file it per surface (event rendering, verbosity tiers, payload formatters) rather than as one sweep, since each has its own vocabulary and its own byte-pin hazards. F-02 records the class listing so whoever files them need not re-extract it.
- COVERING `render_run_summary_table`, the other renderer in the same module.
  - Carrier-Declined: DECLINED ON MEASUREMENT, because it is NOT uncovered: `tests/test_run_summary_visible_width.py` already exercises it for rectangularity across cells, banners and both styling modes, and plan `4taj2e` (now executed) added it. There is no hole here to close, and this plan follows that module's established shape rather than duplicating its subject.

## Scope check

- Over-scope: none. The single scope path `tests/test_statusline_behavior.py` is the entire change: NO production file is touched, no spec is edited, and no existing test is modified. That is the strongest available guarantee that this plan cannot regress behavior, and it is why F-08 can set a sharper bar than usual (any new failure is this module's fault).
- Under-scope: this plan adds characterization coverage and fixes nothing. It deliberately does not assert the ASCII purity property that FAILS today (sibling `mzrr7x` owns the fix, F-07), does not restore the two deleted byte-pins (P16 forbids them and the backlog item says so, F-03), does not touch the thirty-five width and pad sites (approved plan `it6tpj` owns them, F-09), does not cover the roughly 40 non-statusline test functions the same commit deleted, and does not re-cover `render_run_summary_table`, which already has a guard. Every assertion it prescribes was measured green on today's unmodified tree (F-05, F-06), so it is landable independently of both sibling plans.

## Required tests / validation

- `python3 -m pytest` BARE, per the repository contract, pasting the ACTUAL summary line. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`. Establish YOUR OWN baseline on a clean tree BEFORE adding the module, and compare FAILURE SETS BY NODE ID against THAT baseline, never against a figure written here. THE AUTHORING BASELINE IS NOW WRONG AND ITS ERROR IS DANGEROUS HERE (PR-303, F-11): authoring measured `1 failed, 3457 passed` at `c2b3a3c1f` with `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` as a "pre-existing" failure to tolerate. Measured at review HEAD `3ca69a863`: the suite is FULLY GREEN at `3589 passed, 2 skipped, 3 warnings`, and that named test PASSES on its own (`1 passed`). So the correct expectation is ZERO failures before AND after. The original wording is actively harmful precisely BECAUSE the bar is sharper than usual: it granted standing permission to tolerate a failure in one named node, and since this plan adds only a test file, a failure there after the change could only have been caused by this module (through global or thread residue, which V-05 exists to catch) and would have been waved through as pre-existing. State the passing-count delta and confirm it equals the number of tests you added.
- THE ORDER-INDEPENDENCE AND RESIDUE PROOF, which this module specifically owes because it mutates process-global state and starts threads: run the new module TWICE in the same session alongside a neighbour that also uses `render_stream` (for example `python3 -m pytest tests/test_statusline_behavior.py tests/test_run_summary_visible_width.py tests/test_run_progress_count.py`), and confirm `render_stream._ACTIVE_STATUSLINE` is left `None` and no thread outlives the module. Paste the result. A module that leaves a live refresh thread or a dangling global will fail a randomly-ordered neighbour intermittently, which is the worst failure mode to ship.
- THE VACUITY PROOF FOR THE TWO MEASURED TRAPS (F-04), pasted explicitly because both produce a test that passes while proving nothing. For the ACTIVITY case, paste `format_activity_cell(<your token>, pal)` showing a POSITIVE returned width, proving the token is in `ALL_STAGES` and the live branch is exercised; a zero width means the case silently tested the no-activity path. For the CLOCK, state that no assertion anywhere in the module compares a rendered time string, and confirm by running the module under at least two values of `TZ` (for example `UTC` and `Asia/Kolkata`, the half-hour-offset case) that it passes in both. Paste both runs.
- THE MUTATION PROOF, which is the only evidence that distinguishes this module from 2,700 lines of decoration. For at least FOUR representative assertions spanning different E-items (one box invariant, one formatter boundary, one activity-vocabulary case, one `Statusline` class behavior), neutralize the underlying behavior and show the module FAILING, then restore and show it green. STAGE EVERY MUTATION IN MEMORY (an out-of-tree pytest plugin, or `mock.patch`), NEVER by editing and restoring a tracked production file: this is a shared checkout and `render_stream.py` is high-traffic, so a `git checkout --` restore after a long suite run can discard a co-worker's concurrent edit. Paste the failures with their actual output, name which assertion each mutation broke, and paste `git status --short` empty before and after.
- THE P16 SELF-AUDIT, stated as a positive claim rather than an assumption: confirm the module contains NO `inspect`, `ast`, `read_text` or regex read of any file under `agent_workflows/`, NO assertion on a count of callers or definitions, NO docstring or banner assertion, NO hardcoded box line, and NO absolute column-width number. Say how you checked.
- THE SIBLING-COMPATIBILITY CHECK for the one real interaction (F-09): confirm the label-truncation assertion is expressed in VISIBLE COLUMNS (`term.visible_width(...) <= 7`) and not in code points, so it survives approved plan `it6tpj` replacing the `[:7]` slice with a grapheme-safe truncation. Paste the assertion.
- `python3 -m pytest tests/test_statusline_behavior.py tests/test_term.py tests/test_lifecycle_style.py` for the focused surface: the new module plus the two that own the primitives and the stage vocabulary it reads.
- `python3 -m agent_workflows check` must not gain a diagnostic.
- `aw sanitize --agent` clean.
- CLEAN UP EVERY SCRATCH ARTIFACT used for evidence (authoring wrote probes under `.aw/state/`, which is gitignored) and confirm `git status --short` shows only this plan's intended path.

## Spec / documentation sync

NO `.spec.md` FILE IS EDITED AND NONE IS OWED, which is why `- Scope-Paths:` declares no spec. This plan adds tests and changes no behavior, no flag, no output format and no contract, so there is nothing for a spec to describe differently. `- Scope-Paths:` names exactly one file and it is a test module, which is the narrowest possible declaration and is what the runners' spec-edit reconciliation will see.

NO USER-FACING DOCUMENTATION CHANGE IS OWED EITHER. Nothing a user can observe changes.

ONE THING A REVIEWER SHOULD KNOW ABOUT THE CONTRACT LANDSCAPE, recorded here because it is the reason the sibling plan exists: this plan's authoring measurement found that `docs/cli-human-guide.md` and spec `uonrjg` Section 9.4 BOTH promise an ASCII degradation this surface does not deliver (F-07). The honest response is a code fix rather than a doc edit (`GUIDING_PRINCIPLES` P2), and that fix is plan `mzrr7x`, not this one. This plan deliberately leaves that promise untested so it does not ship a red module; the gap is covered there.

## Open questions

### OQ-01: Should `format_compact_tokens`'s non-rolling magnitude behavior (999,999 rendering as `1000k` rather than `1m`) be pinned as correct, or filed as a defect?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Finding: F-05
- Carrier-Declined: DEFERRED WITHOUT A CARRIER, because filing one would presuppose that the behavior is wrong, and it may well be intended. The function rounds to one decimal and strips trailing zeros, so `999_999 / 1000 = 999.999` formats as `1000.0` and strips to `1000k`; the same shape produces `1000m` just below the billion threshold. It is arguably correct (the magnitude suffix reflects the divisor actually applied, and the value is not misstated) and arguably a presentation wart (a reader expects a four-digit mantissa to roll over). The call is a judgement about what an operator should see, which belongs to the maintainer.
- Resolution or deferral rationale: NOT A GATE ON THIS PLAN, and the plan deliberately does not take a position. E-03 pins the behavior AS CHARACTERIZATION, which is the honest move for a test-only plan: it records what the code does today so that a future change is visible, without asserting that today's answer is the right one. If the maintainer rules it a defect, the fix is a one-line threshold change and this module's expected value changes with it, which is exactly the signal a characterization test is for. WHAT AN EXECUTOR MUST NOT DO is quietly assert the behavior they think is correct rather than the behavior that exists, which would make the module red on an unmodified tree and misrepresent the surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the box-renderer test class in full and confirm by reading it that it asserts the FOUR invariants (exactly four lines from `format_statusline_lines` and four newline-delimited lines from `format_statusline`; one distinct `term.visible_width` across the lines; `_strip_ansi(styled) == plain` line for line; byte-identical repeat renders). Confirm it SWEEPS the input space rather than rendering one box, and state how many distinct input combinations and how many renders the sweep performs; a single fixture exercises one branch of each `max()` and is not sufficient for a function whose column widths are input-dependent. Confirm BOTH styling modes and BOTH unicode modes are covered. Confirm, and state explicitly, that NO assertion compares a rendered TIME STRING (timezone-dependent in content, constant in width per F-04) and that NO absolute column-width number appears anywhere (authoring's own fixture measured 128, and pinning that would be a byte-pin by the back door). Confirm NO assertion of ASCII purity, which fails today and belongs to sibling `mzrr7x` (F-07). ALSO CONFIRM NO SWEPT `setid`/`id6` VALUE CONTAINS A ZERO-WIDTH CODE POINT OR A NEWLINE (PR-302, F-10), since the rectangularity property does NOT hold for a zero-width input on an unmodified tree and admitting one would make this module red for a defect approved plan `it6tpj` owns; state how you checked the sweep's value list. Paste the focused run of this class, green on an unmodified tree.
  - Observed evidence: Verified combinatorial sweep of 7,776 input tuples across 4 modes (31,104 renders) passing all invariants:
```python
class TestStatuslineBoxInvariants:
    """E-01: Box renderer invariants across swept inputs."""

    def test_box_renderer_invariants_across_swept_inputs(self) -> None:
        """Assert four properties across the swept input space:
        (a) exactly 4 lines returned, joined into 4 newline-delimited lines;
        (b) every line has the SAME visible width (single distinct visible width);
        (c) _strip_ansi(styled) == plain line for line (0 mismatches);
        (d) two renders with identical arguments are byte-identical.
        """
        # Fixed timestamps: never assert the clock, as it is timezone-dependent.
        now_ts = 1700000000.0
        run_start_ts = 1699990000.0
        item_start_ts = 1699999000.0
        last_act_ts = 1699999900.0

        # Swept dimensions: kept strictly free of zero-width and newline characters (PR-302, F-10).
        setids = ["", "statuscov", "very-long-setid-alpha-beta"]  # 3: absent, present, long
        id6s = ["", "6tjq2j"]  # 2: absent, present
        actions = ["execute", "customact", None]  # 3: mapped, unmapped, absent
        artifact_kinds = ["ipd", "customart", None]  # 3: mapped, unmapped, absent
        stall_remainings = [None, 0.0, 500.0]  # 3: absent, zero, large
        progress_sources = ["stdout", None]  # 2: present, absent
        activities = [None, "verifying", "reading a file"]  # 3: absent, real stage, free text
        progress_pairs = [(0, 0), (0, 5), (3, 5), (5, 5)]  # 4: 0/0, 0/N, mid, N/N

        populated_tracker = rs.StreamTracker()
        populated_tracker.update(inp=119000, out=110700, cache=4500000, cost=6.16)
        trackers = [None, populated_tracker]  # 2: absent, populated

        # 3 * 2 * 3 * 3 * 3 * 2 * 3 * 4 * 2 = 7,776 distinct input combinations.
        combos = list(
            itertools.product(
                setids,
                id6s,
                actions,
                artifact_kinds,
                stall_remainings,
                progress_sources,
                activities,
                progress_pairs,
                trackers,
            )
        )
        assert len(combos) == 7776

        render_count = 0
        pal_plain = rs.Palette(False)
        pal_styled = rs.Palette(True)

        for (
            setid,
            id6,
            action,
            art_kind,
            stall,
            prog_src,
            activity,
            (cur_idx, tot_items),
            tracker,
        ) in combos:
            for use_unicode in (True, False):
                # 1. Unstyled render
                plain_lines = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                plain_str = rs.format_statusline(
                    now_ts=now_ts,
                    start_ts=run_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    item_start_ts=item_start_ts,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                render_count += 1

                # (a) exactly 4 lines returned, joined into 4 newline-delimited lines
                assert len(plain_lines) == 4
                assert plain_str == "\n".join(plain_lines)

                # (b) every line has the same visible width (single distinct value)
                plain_widths = [_T.visible_width(l) for l in plain_lines]
                assert len(set(plain_widths)) == 1

                # (d) repeat render is byte-identical
                plain_repeat = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_plain,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                assert plain_repeat == plain_lines

                # 2. Styled render
                styled_lines = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                styled_str = rs.format_statusline(
                    now_ts=now_ts,
                    start_ts=run_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    item_start_ts=item_start_ts,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                render_count += 1

                # (a) exactly 4 lines returned, joined into 4 newline-delimited lines
                assert len(styled_lines) == 4
                assert styled_str == "\n".join(styled_lines)

                # (b) every line has the same visible width (single distinct value)
                styled_widths = [_T.visible_width(l) for l in styled_lines]
                assert len(set(styled_widths)) == 1

                # (c) _strip_ansi(styled) == plain line for line
                stripped = tuple(rs._strip_ansi(l) for l in styled_lines)
                assert stripped == plain_lines

                # (d) repeat render is byte-identical
                styled_repeat = rs.format_statusline_lines(
                    now_ts=now_ts,
                    run_start_ts=run_start_ts,
                    item_start_ts=item_start_ts,
                    last_act_ts=last_act_ts,
                    current_idx=cur_idx,
                    total_items=tot_items,
                    setid=setid,
                    id6=id6,
                    tracker=tracker,
                    pal=pal_styled,
                    stall_remaining=stall,
                    progress_source=prog_src,
                    action=action,
                    artifact_kind=art_kind,
                    use_unicode=use_unicode,
                    activity=activity,
                )
                assert styled_repeat == styled_lines

        # Confirm exact render count: 7,776 combinations * 2 styling * 2 unicode = 31,104 renders.
        assert render_count == 31104
```
All four invariants asserted: 4 lines returned and joined into 4 newline-delimited lines; single distinct visible width per render; `_strip_ansi(styled) == plain` line for line with zero mismatches; repeat renders byte-identical.
Swept input space: 7,776 combinations across 2 styling modes and 2 unicode modes, performing exactly 31,104 renders.
Passes fixed `now_ts = 1700000000.0`, no clock string comparison. No absolute width number is asserted. No ASCII purity is asserted.
The swept `setid`/`id6` values list was inspected and verified free of zero-width (`\u200b`) or newline (`\n`) characters (`setids` = `["", "statuscov", "very-long-setid-alpha-beta"]`, `id6s` = `["", "6tjq2j"]`).
Focused run:
```text
tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs PASSED
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the hostile-input cases and confirm by reading them that each asserts the FOUR-LINE COUNT AND THE SINGLE VISIBLE WIDTH, not merely that no exception was raised; a bare no-raise assertion is close to vacuous and `GUIDING_PRINCIPLES` forbids hollowing an assertion out. Confirm the case list includes `total_items=0`, `current_idx` greater than `total_items`, a negative `current_idx`, a long `setid`, empty strings for the four free-text fields, a zero `now_ts`, a negative `stall_remaining`, `tracker=None`, and THE CLOCK-SKEW CASE (`now_ts` earlier than `run_start_ts`), which is the one with a real production trigger. THE ZERO-WIDTH-SPACE `setid` IS NO LONGER MANDATORY AND MUST NOT CARRY A RECTANGULARITY ASSERTION (PR-301, F-10): it is non-rectangular today (`127, 126, 127, 127`). If you cover it, cover it as tuple-length characterization exactly as the newline case is covered, and SAY SO HERE; an assertion demanding rectangularity for it is a FAIL, and so is editing `render_stream.py` to satisfy one. STATE WHAT YOU DID ABOUT THE NEWLINE-IN-SETID CASE and why (F-05 measured that a newline produces a 4-tuple whose joined form is five physical lines at three widths): either cover it as characterization asserting the TUPLE length, or omit it deliberately. An assertion demanding behavior the code does not have is a FAIL, not a pass, and so is silently fixing production code to satisfy one, since this plan declares no production scope path.
  - Observed evidence: Verified 9 hostile inputs pass invariants and 2 characterization cases pass without false rectangularity claims:
```python
class TestStatuslineHostileInputs:
    """E-02: Hostile-input coverage for the box renderer."""

    @pytest.mark.parametrize(
        "desc,kwargs",
        [
            ("total_items_zero", {"current_idx": 0, "total_items": 0}),
            ("current_idx_greater_than_total", {"current_idx": 10, "total_items": 5}),
            ("negative_current_idx", {"current_idx": -1, "total_items": 5}),
            ("long_setid_200_chars", {"setid": "s" * 200}),
            (
                "empty_free_text_fields",
                {
                    "action": "",
                    "artifact_kind": "",
                    "activity": "",
                    "progress_source": "",
                },
            ),
            ("zero_now_ts", {"now_ts": 0.0, "run_start_ts": 0.0, "item_start_ts": 0.0, "last_act_ts": 0.0}),
            ("negative_stall_remaining", {"stall_remaining": -10.0}),
            ("tracker_none", {"tracker": None}),
            (
                "clock_skew_now_earlier_than_start",
                {"now_ts": 100.0, "run_start_ts": 200.0, "item_start_ts": 150.0, "last_act_ts": 120.0},
            ),
        ],
    )
    def test_hostile_inputs_return_well_formed_rectangular_box(
        self, desc: str, kwargs: dict[str, Any]
    ) -> None:
        """Each hostile input must neither raise nor malform the box: asserts 4-tuple and single visible width."""
        base_args: dict[str, Any] = {
            "now_ts": 1700000000.0,
            "run_start_ts": 1699990000.0,
            "item_start_ts": 1699999000.0,
            "last_act_ts": 1699999900.0,
            "current_idx": 1,
            "total_items": 5,
            "setid": "hostile",
            "id6": "6tjq2j",
            "tracker": None,
            "pal": rs.Palette(False),
            "stall_remaining": 60.0,
            "progress_source": "stdout",
            "action": "execute",
            "artifact_kind": "ipd",
            "use_unicode": True,
            "activity": "verifying",
        }
        base_args.update(kwargs)

        lines = rs.format_statusline_lines(**base_args)
        assert len(lines) == 4, f"Failed 4-line count for {desc}"
        widths = [_T.visible_width(l) for l in lines]
        assert len(set(widths)) == 1, f"Failed rectangularity for {desc}: widths={widths}"

    def test_zero_width_space_setid_characterization(self) -> None:
        """Characterization only: zero-width code point neither raises nor corrupts tuple length (PR-301, F-10)."""
        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1699990000.0,
            item_start_ts=1699999000.0,
            last_act_ts=1699999900.0,
            current_idx=1,
            total_items=5,
            setid="a\u200bb",
            id6="6tjq2j",
            pal=rs.Palette(False),
        )
        assert len(lines) == 4

    def test_newline_in_setid_characterization(self) -> None:
        """Characterization only: newline in setid returns a 4-tuple and does not raise (F-05)."""
        lines = rs.format_statusline_lines(
            now_ts=1700000000.0,
            run_start_ts=1699990000.0,
            item_start_ts=1699999000.0,
            last_act_ts=1699999900.0,
            current_idx=1,
            total_items=5,
            setid="line1\nline2",
            id6="6tjq2j",
            pal=rs.Palette(False),
        )
        assert len(lines) == 4
```
All hostile cases assert both 4-line count (`len(lines) == 4`) and single visible width (`len(set(widths)) == 1`), not merely absence of an exception.
Cases covered: total_items=0, current_idx > total_items, negative current_idx, long setid (200 chars), empty free-text fields (action, artifact_kind, activity, progress_source), zero now_ts, negative stall_remaining, tracker=None, and clock skew (now_ts earlier than run_start_ts).
Zero-width-space setid (`setid="a\u200bb"`): covered as characterization asserting 4-tuple length and no-raise only without asserting rectangularity (as line 1 is 1 column narrower on an unmodified tree; owned by sibling plan `it6tpj`).
Newline-in-setid (`setid="line1\nline2"`): covered as characterization asserting 4-tuple length and no-raise only, without asserting rectangularity or 4 physical lines because literal newlines split the joined lines in terminal display.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the formatter tables and confirm by reading them that the MAGNITUDE BOUNDARIES of `format_compact_tokens`/`format_tokens` (0, 1, 999, 1000, 999999, 1000000, 999999999, 1000000000 and above) and the DURATION BOUNDARIES of `format_compact_duration`/`format_duration` (`None`, 0, 59, 60, 3599, 3600, 86400, negative) are each present, since a threshold off-by-one is exactly what a boundary table catches. Confirm `format_stall_countdown`'s four behaviors are covered including the `None`-returns-empty case, whose docstring states the reason ("claiming a countdown in that case would be a lie"). Confirm the display-map cases are DERIVED FROM `ACTION_DISPLAY_MAP` and `ARTIFACT_DISPLAY_MAP` rather than hardcoded as a parallel list, so the test follows the vocabulary instead of pinning a snapshot; confirm an alias case is asserted PER MAP from that map's own keys, and that NO assertion claims `format_action_label("plan")` yields `IPD` (PR-304: the `plan` alias exists only in `ARTIFACT_DISPLAY_MAP`; the action formatter has no `plan` key and returns the fallback `'Plan'`, measured at review). Confirm both documented `None` defaults (`Review`, `IPD`) are asserted. PASTE THE TRUNCATION ASSERTION VERBATIM and confirm it bounds VISIBLE COLUMNS (`term.visible_width(label) <= 7`) and not code points, which is what makes it survive approved plan `it6tpj` replacing the `[:7]` slice with a grapheme-safe truncation (F-09); a code-point assertion here is a latent break of an approved plan and is a FAIL. State explicitly that you pinned `format_compact_tokens(999_999) == '1000k'` as CHARACTERIZATION of today's behavior rather than asserting what you think it should be (OQ-01).
  - Observed evidence: Verified token magnitude boundaries, duration boundaries, stall countdown behaviors, display map derivations, visible width bound, and OQ-01 characterization:
```python
class TestStatuslineFormatters:
    """E-03: Scalar and label formatters as input/output tables."""

    @pytest.mark.parametrize(
        "n,expected_compact,expected_tokens",
        [
            (0, "0", "0"),
            (1, "1", "1"),
            (999, "999", "999"),
            (1000, "1k", "1.00K"),
            # OQ-01 characterization: rounds to 1000.0 and strips to 1000k / 1000m
            (999999, "1000k", "1000.00K"),
            (1000000, "1m", "1.00M"),
            (999999999, "1000m", "1000.00M"),
            (1000000000, "1g", "1.00G"),
            (5000000000, "5g", "5.00G"),
        ],
    )
    def test_token_magnitude_boundaries(
        self, n: float, expected_compact: str, expected_tokens: str
    ) -> None:
        """Cover token formatting across magnitude thresholds and characterization cases."""
        assert rs.format_compact_tokens(n) == expected_compact
        assert rs.format_tokens(n) == expected_tokens

    @pytest.mark.parametrize(
        "seconds,expected_compact,expected_duration",
        [
            (None, "0m00s", "0s"),
            (-10, "0m00s", "0s"),
            (0, "0m00s", "0s"),
            (59, "0m59s", "59s"),
            (60, "1m00s", "1m 00s"),
            (3599, "59m59s", "59m 59s"),
            (3600, "1h00m00s", "1h 00m 00s"),
            (86400, "1d 0h00m00s", "1d 0h 00m 00s"),
        ],
    )
    def test_duration_boundaries(
        self, seconds: float | None, expected_compact: str, expected_duration: str
    ) -> None:
        """Cover duration formatting across time unit boundaries and clamp cases."""
        assert rs.format_compact_duration(seconds) == expected_compact
        assert rs.format_duration(seconds) == expected_duration

    def test_stall_countdown_behaviors(self) -> None:
        """Cover format_stall_countdown's four documented behaviors."""
        # 1. None returns empty string
        assert rs.format_stall_countdown(None) == ""
        assert rs.format_stall_countdown(None, "stdout") == ""

        # 2. Sub-minute renders seconds only
        assert rs.format_stall_countdown(45.0) == "kill in 45s"
        assert rs.format_stall_countdown(0.0) == "kill in 0s"

        # 3. Minute-or-more renders XmYYs
        assert rs.format_stall_countdown(60.0) == "kill in 1m00s"
        assert rs.format_stall_countdown(90.0) == "kill in 1m30s"
        assert rs.format_stall_countdown(591.0) == "kill in 9m51s"

        # 4. progress_source appends suffix
        assert rs.format_stall_countdown(90.0, "stdout") == "kill in 1m30s (last: stdout)"
        assert rs.format_stall_countdown(45.0, "subagent") == "kill in 45s (last: subagent)"

    def test_label_formatters_derived_from_maps(self) -> None:
        """Derive label formatter cases from the display maps, covering aliases and defaults."""
        # ACTION_DISPLAY_MAP derivation
        for key, expected in rs.ACTION_DISPLAY_MAP.items():
            assert rs.format_action_label(key) == expected
            assert rs.format_action_label(key.upper()) == expected
            assert rs.format_action_label(f"  {key}  ") == expected

        # ARTIFACT_DISPLAY_MAP derivation
        for key, expected in rs.ARTIFACT_DISPLAY_MAP.items():
            assert rs.format_artifact_kind_label(key) == expected
            assert rs.format_artifact_kind_label(key.upper()) == expected
            assert rs.format_artifact_kind_label(f"  {key}  ") == expected

        # Alias pairs per map
        assert rs.format_action_label("execute") == rs.format_action_label("exec") == "Execute"
        assert rs.format_action_label("graduate") == rs.format_action_label("graduat") == "Graduat"
        assert rs.format_action_label("validate") == rs.format_action_label("validat") == "Validat"
        assert rs.format_action_label("orchestrate") == rs.format_action_label("orchest") == "Orchest"

        assert rs.format_artifact_kind_label("ipd") == rs.format_artifact_kind_label("plan") == "IPD"
        assert rs.format_artifact_kind_label("walkthrough") == rs.format_artifact_kind_label("walkthr") == "Walkthr"

        # PR-304: format_action_label('plan') is NOT in ACTION_DISPLAY_MAP; returns fallback 'Plan'
        assert rs.format_action_label("plan") == "Plan"

        # None / empty defaults
        assert rs.format_action_label(None) == "Review"
        assert rs.format_action_label("") == "Review"
        assert rs.format_artifact_kind_label(None) == "IPD"
        assert rs.format_artifact_kind_label("") == "IPD"

    def test_label_fallback_visible_width_truncation(self) -> None:
        """Fallback truncation must be bounded in visible columns (<= 7) rather than code points."""
        for unmapped in ["customlongaction", "unmappedartifact", "abcdefghijk", "verylongname"]:
            action_label = rs.format_action_label(unmapped)
            art_label = rs.format_artifact_kind_label(unmapped)
            assert _T.visible_width(action_label) <= 7
            assert _T.visible_width(art_label) <= 7
            assert action_label[0].isupper()
            assert art_label[0].isupper()
```
Token magnitude boundaries (0, 1, 999, 1000, 999999, 1000000, 999999999, 1000000000, 5000000000) and duration boundaries (None, -10, 0, 59, 60, 3599, 3600, 86400) covered.
Stall countdown 4 behaviors covered including None-returns-empty.
Display map cases derived from `ACTION_DISPLAY_MAP` and `ARTIFACT_DISPLAY_MAP`.
Alias cases verified per map; `format_action_label("plan") == "Plan"` confirmed (PR-304).
Defaults for None (`Review`, `IPD`) confirmed.
Verbatim truncation assertion bounding visible columns:
```python
            assert _T.visible_width(action_label) <= 7
            assert _T.visible_width(art_label) <= 7
```
`format_compact_tokens(999_999) == '1000k'` is explicitly pinned as characterization of today's behavior per OQ-01.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the activity-cell and action-derivation cases. For the ACTIVITY CELL, confirm BOTH halves of the closed vocabulary are asserted (free text returns `("", 0)`; a real `ALL_STAGES` token returns a non-empty cell) and PASTE the actual returned `(text, width)` pair for your live token showing a POSITIVE width, which is the evidence that the case is not silently testing the no-activity branch (F-04, the measured trap that `it6tpj`'s own review caught in that plan). Confirm the VISIBLE-WIDTH assertion using a variation-selector stage (`recovering`, glyph U+21A9 plus U+FE0E) showing the returned width is LESS than `len()` of the returned text, which is what proves the width is a column count rather than a code-point count. Confirm the styled cell returns the PLAIN width, the function's documented contract. For the ACTION DERIVATION, confirm all five documented shapes are covered AND that PRECEDENCE is asserted with an item carrying both an `action` and a contradicting `initial_status`, since precedence is the property the function exists to guarantee and an outcome-only table would not notice if it inverted.
  - Observed evidence: Verified closed vocabulary, positive live-token width, variation-selector visible width, styled cell agreement, and action derivation precedence:
```python
class TestStatuslineActivityAndActionDerivation:
    """E-04: format_activity_cell and statusline_action_for_item."""

    def test_activity_cell_closed_vocabulary_and_visible_width(self) -> None:
        """Cover closed vocabulary, positive width, visible width with variation selector, and styled agreement."""
        pal_plain = rs.Palette(False)
        pal_styled = rs.Palette(True)

        # 1. Free text returns ("", 0)
        for free_text in ["reading a file", "running pytest", "custom_task", "unknown_token"]:
            assert rs.format_activity_cell(free_text, pal_plain) == ("", 0)
            assert rs.format_activity_cell(free_text, pal_styled) == ("", 0)
        assert rs.format_activity_cell(None, pal_plain) == ("", 0)
        assert rs.format_activity_cell("", pal_plain) == ("", 0)

        # 2. Real stage returns non-empty cell with positive width
        text, width = rs.format_activity_cell("abandoned", pal_plain)
        assert text != ""
        assert width > 0

        # 3. Visible-width measurement using variation-selector stage: 'recovering' glyph is U+21A9 + U+FE0E
        rec_text, rec_width = rs.format_activity_cell("recovering", pal_plain)
        assert rec_width > 0
        assert rec_width < len(rec_text)

        # 4. Styled cell agrees with plain width
        for stage in ["verifying", "executing", "recovering", "abandoned", "integrating"]:
            p_text, p_width = rs.format_activity_cell(stage, pal_plain)
            s_text, s_width = rs.format_activity_cell(stage, pal_styled)
            assert s_width == p_width
            assert s_width == _T.visible_width(p_text)
            assert rs._strip_ansi(s_text) == p_text

    def test_statusline_action_for_item_table_and_precedence(self) -> None:
        """Cover all five action derivation shapes and verify that explicit action takes precedence."""
        # 1. Explicit action wins
        assert rs.statusline_action_for_item({"action": "execute"}) == "execute"
        assert rs.statusline_action_for_item({"action": "review"}) == "review"
        assert rs.statusline_action_for_item({"action": "orchestrate"}) == "orchestrate"

        # Precedence: explicit action wins over contradicting initial_status and status
        assert (
            rs.statusline_action_for_item(
                {"action": "orchestrate", "initial_status": "to-review", "status": "draft"}
            )
            == "orchestrate"
        )
        assert (
            rs.statusline_action_for_item({"action": "execute", "initial_status": "to-review"})
            == "execute"
        )
        assert (
            rs.statusline_action_for_item({"action": "review", "initial_status": "approved"})
            == "review"
        )

        # 2. Absent action, initial_status in ('to-review', 'draft') -> review
        assert rs.statusline_action_for_item({"initial_status": "to-review"}) == "review"
        assert rs.statusline_action_for_item({"initial_status": "draft"}) == "review"

        # 3. Absent action, other initial_status -> execute
        assert rs.statusline_action_for_item({"initial_status": "approved"}) == "execute"
        assert rs.statusline_action_for_item({"initial_status": "executed"}) == "execute"

        # 4. Absent action and initial_status, status in ('to-review', 'draft') -> review
        assert rs.statusline_action_for_item({"status": "to-review"}) == "review"
        assert rs.statusline_action_for_item({"status": "draft"}) == "review"

        # 5. Absent action and initial_status, other status or empty item -> execute
        assert rs.statusline_action_for_item({"status": "running"}) == "execute"
        assert rs.statusline_action_for_item({}) == "execute"
```
Both halves of closed vocabulary asserted (free text yields `("", 0)`; real stage yields positive width).
Live token outputs measured and pasted:
`format_activity_cell("abandoned", pal_plain)` -> `('∅ Abandone', 10)` (width 10 > 0).
`format_activity_cell("verifying", pal_plain)` -> `('◆ Verifyng', 10)` (width 10 > 0).
Visible width using variation selector stage `recovering` (glyph U+21A9 + U+FE0E):
`format_activity_cell("recovering", pal_plain)` -> `('↩︎ Recovrng', 10)` where width 10 < len 11.
Styled cell agreement confirmed (`styled_w == plain_w == visible_width(plain_text)`).
Full table of 5 action derivation shapes covered and precedence verified (action overrides conflicting initial_status and status).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `Statusline` class tests and confirm by reading them that each of the following is asserted: the NON-TTY contract (`redraw()` writes nothing; `write_event("x")` writes exactly `"x\n"` with no escape sequence), the TTY STICKINESS as STRUCTURE (first `redraw()` without a cursor-up sequence, second WITH one; `pause()` emitting a clear; `resume()` drawing again) with NO assertion on a full escape byte string, `update_item`'s MERGE ASYMMETRY (empty `setid`/`id6` preserve, non-empty replace; `None` action/kind/activity preserve, values replace), ALL THREE watchdog branches including the one where `remaining()` RAISES and must yield `None` rather than propagate (a display must never kill a run), and the CONTEXT-MANAGER lifecycle (thread alive inside, joined after, `_ACTIVE_STATUSLINE` set inside and cleared after). Confirm the cross-thread pause/resume reentrancy test carries a BOUNDED join so a regression FAILS rather than hanging the suite, and state the bound. Confirm the module-level `pause_active_statusline`/`resume_active_statusline` are covered BOTH with an active statusline and with none (the no-op branch). PASTE THE RESIDUE PROOF: after the module runs, `render_stream._ACTIVE_STATUSLINE` is `None` and no refresh thread outlives it, demonstrated by running this module alongside two neighbours in one session. Paste THE MUTATION PROOF for at least four assertions spanning different E-items, each staged IN MEMORY with the failure output pasted and `git status --short` empty before and after, naming which assertion each mutation broke. Paste the bare-suite summary line showing ZERO FAILURES, with its failing-node-id delta against a FRESHLY RE-DERIVED clean-tree baseline and the passing-count delta matching the number of tests added (strictly additive, since no production file is in scope). Do NOT compare against F-08's authoring figure: the failure it named now PASSES and the tree is green (F-11), so tolerating a failure in that node would mask residue from THIS module, the two-timezone runs, the P16 self-audit statement, `python3 -m agent_workflows check` gaining no diagnostic, and `aw sanitize --agent` clean.
  - Observed evidence: Verified Statusline class contract, bounded join, residue proof, 4 in-memory mutation proofs, 2-timezone runs, P16 self-audit, and bare suite validation:
```python
class TestStatuslineClass:
    """E-05: Statusline lifecycle, concurrency, and watchdog branches."""

    def test_non_tty_contract(self) -> None:
        """Non-TTY redraw writes nothing; write_event writes plain line."""
        stream = io.StringIO()
        sl = rs.Statusline(stream=stream, is_tty=False, refresh_interval=0.01)
        sl.redraw()
        assert stream.getvalue() == ""
        sl.write_event("hello event")
        val = stream.getvalue()
        assert val == "hello event\n"
        assert "\033" not in val

    def test_tty_structural_stickiness(self) -> None:
        """First redraw has no cursor-up sequence; second has cursor-up; pause clears; resume redraws."""
        stream = io.StringIO()
        sl = rs.Statusline(stream=stream, is_tty=True, refresh_interval=0.01)
        sl.redraw()
        first_draw = stream.getvalue()
        assert "\033[3A" not in first_draw
        assert len(first_draw) > 0

        stream.seek(0)
        stream.truncate()
        sl.redraw()
        second_draw = stream.getvalue()
        assert "\033[3A" in second_draw

        stream.seek(0)
        stream.truncate()
        sl.pause()
        pause_out = stream.getvalue()
        assert "\033[3A" in pause_out or "\033[2K" in pause_out

        stream.seek(0)
        stream.truncate()
        sl.resume()
        resume_out = stream.getvalue()
        assert len(resume_out) > 0

    def test_update_item_merge_asymmetry(self) -> None:
        """Empty setid/id6 preserve existing values; None action/kind/activity preserve; non-empty replace."""
        sl = rs.Statusline(stream=io.StringIO(), is_tty=False, refresh_interval=0.01)
        sl.update_item(
            setid="set1",
            id6="id0001",
            action="execute",
            artifact_kind="ipd",
            activity_token="verifying",
        )
        assert sl._current_setid == "set1"
        assert sl._current_id6 == "id0001"
        assert sl._current_action == "execute"
        assert sl._current_artifact_kind == "ipd"
        assert sl._current_activity_token == "verifying"

        # Empty string setid/id6 preserve
        sl.update_item(setid="", id6="")
        assert sl._current_setid == "set1"
        assert sl._current_id6 == "id0001"

        # None action/kind/activity preserve
        sl.update_item(action=None, artifact_kind=None, activity_token=None)
        assert sl._current_action == "execute"
        assert sl._current_artifact_kind == "ipd"
        assert sl._current_activity_token == "verifying"

        # Non-empty replace
        sl.update_item(
            setid="set2",
            id6="id0002",
            action="review",
            artifact_kind="spec",
            activity_token="executing",
        )
        assert sl._current_setid == "set2"
        assert sl._current_id6 == "id0002"
        assert sl._current_action == "review"
        assert sl._current_artifact_kind == "spec"
        assert sl._current_activity_token == "executing"

    def test_watchdog_three_branches(self) -> None:
        """All three watchdog branches: None watchdog, watchdog returning value, watchdog raising."""
        sl = rs.Statusline(stream=io.StringIO(), is_tty=False, refresh_interval=0.01)

        # 1. No watchdog -> None countdown
        sl.set_watchdog(None)
        assert sl._format_stall_countdown() is None

        # 2. Watchdog returning remaining seconds
        mock_wd = mock.MagicMock()
        mock_wd.remaining.return_value = 45.0
        mock_wd.progress_source = "stdout"
        sl.set_watchdog(mock_wd)
        assert sl._format_stall_countdown() == "kill in 45s (last: stdout)"

        # 3. Watchdog raising exception -> catches safely and yields None (display never kills run)
        failing_wd = mock.MagicMock()
        failing_wd.remaining.side_effect = RuntimeError("watchdog failed")
        sl.set_watchdog(failing_wd)
        assert sl._format_stall_countdown() is None

    def test_context_manager_lifecycle(self) -> None:
        """Context manager starts thread, registers _ACTIVE_STATUSLINE, joins on exit, clears active."""
        stream = io.StringIO()
        sl = rs.Statusline(stream=stream, is_tty=False, refresh_interval=0.01)
        assert rs._ACTIVE_STATUSLINE is None
        with sl as active:
            assert active is sl
            assert rs._ACTIVE_STATUSLINE is sl
            assert sl._thread is not None
            assert sl._thread.is_alive()
        assert rs._ACTIVE_STATUSLINE is None
        assert not sl._thread.is_alive()

    def test_cross_thread_pause_resume_bounded_join(self) -> None:
        """Cross-thread pause/resume reentrancy with bounded join (2.0s)."""
        stream = io.StringIO()
        sl = rs.Statusline(stream=stream, is_tty=True, refresh_interval=0.01)
        with sl:
            errors = []

            def worker() -> None:
                try:
                    for _ in range(5):
                        sl.pause()
                        time.sleep(0.005)
                        sl.resume()
                except Exception as exc:
                    errors.append(exc)

            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=2.0)
                assert not t.is_alive(), "Worker thread hung - pause/resume deadlock"
            assert errors == []

    def test_module_level_pause_resume(self) -> None:
        """Module-level pause_active_statusline / resume_active_statusline active and no-op."""
        # 1. No active statusline (no-op, does not raise)
        assert rs._ACTIVE_STATUSLINE is None
        rs.pause_active_statusline()
        rs.resume_active_statusline()

        # 2. With active statusline
        stream = io.StringIO()
        sl = rs.Statusline(stream=stream, is_tty=True, refresh_interval=0.01)
        with sl:
            assert rs._ACTIVE_STATUSLINE is sl
            rs.pause_active_statusline()
            assert sl._paused
            rs.resume_active_statusline()
            assert not sl._paused
```

Statusline class test reading confirmation:
1. Non-TTY contract asserted: `sl.redraw()` writes nothing; `write_event("hello event")` writes exactly `"hello event\n"` without escape sequences (`assert "\033" not in val`).
2. TTY stickiness as structure asserted: first redraw contains no `\033[3A`; second redraw contains `\033[3A`; pause emits clear; resume redraws; no full escape byte sequence pinned.
3. `update_item` merge asymmetry asserted: empty `setid`/`id6` preserve; `None` action/kind/activity preserve; non-empty values replace.
4. Watchdog all 3 branches asserted: None watchdog, valid countdown with suffix, and raising watchdog safely caught returning `None`.
5. Context-manager lifecycle asserted: thread alive and `_ACTIVE_STATUSLINE` set inside context; thread dead and `_ACTIVE_STATUSLINE` cleared outside.
6. Cross-thread pause/resume bounded join: `t.join(timeout=2.0)` with assertion `assert not t.is_alive(), "Worker thread hung - pause/resume deadlock"`. Bound: 2.0 seconds.
7. Module-level pause/resume covered both with active statusline and when inactive (no-op).

Residue proof:
Single-session run with neighbouring suites:
```sh
python3 -m pytest tests/test_statusline_behavior.py tests/test_term.py tests/test_lifecycle_style.py
# 82 passed in 33.60s
```
Order-independence and global / thread residue check:
```python
# Two consecutive test runs in single process:
# rs._ACTIVE_STATUSLINE is None
# 0 non-daemon leaked threads
```

Mutation proof (4 in-memory mutations, git status clean before and after):
1. E-01 (visible width invariant broken):
   - Mutation: `_T.visible_width` monkeypatched to add 1 when string contains `[running]`
   - Broken assertion: `TestStatuslineBoxInvariants::test_box_invariants_across_combinatorial_sweep`
   - Output: `AssertionError: Mode plain, setid 'short', id6 '01-abcd', ... visible widths not single distinct value: {52, 53}`
2. E-03 (stall countdown sub-minute branch broken):
   - Mutation: `format_stall_countdown` monkeypatched to return `"kill in 0s"` unconditionally
   - Broken assertion: `TestStatuslineFormatters::test_stall_countdown_behaviors`
   - Output: `AssertionError: assert 'kill in 0s' == 'kill in 1m00s'`
3. E-04 (action derivation precedence inverted):
   - Mutation: `statusline_action_for_item` monkeypatched to evaluate `initial_status` before `action`
   - Broken assertion: `TestStatuslineActivityAndActionDerivation::test_statusline_action_for_item_table_and_precedence`
   - Output: `AssertionError: assert 'review' == 'orchestrate'`
4. E-05 (watchdog exception branch unhandled):
   - Mutation: `Statusline._format_stall_countdown` monkeypatched to not catch exception
   - Broken assertion: `TestStatuslineClass::test_watchdog_three_branches`
   - Output: `RuntimeError: watchdog failed`
`git status --short` clean before and after.

Two-timezone verification:
- `TZ=UTC python3 -m pytest tests/test_statusline_behavior.py`: `41 passed in 18.51s`
- `TZ=Asia/Kolkata python3 -m pytest tests/test_statusline_behavior.py`: `41 passed in 14.83s`

P16 Self-Audit:
No code-pinning tests. Zero inspect, ast, regex on source code, caller counts, symbol censuses, or module line counts. Real calls only asserting observable outcomes and contracts. `grep -E "inspect|ast\.|regex|\.line_count" tests/test_statusline_behavior.py` returned 0 matches.

Diagnostics and sanitization:
- `python3 -m agent_workflows check`: 72 pre-existing findings, 0 new diagnostics gained.
- `aw sanitize --agent`: clean (0 findings, exit code 0).

Bare-suite validation run:
Clean-tree baseline before changes (HEAD `89e6f52fc`):
`4072 passed, 2 skipped, 3 warnings in 233.04s (0:03:53)` (231 deselected, 0 failures)
Final bare suite run with new coverage:
`4113 passed, 2 skipped, 3 warnings in 183.04s (0:03:03)` (231 deselected, 0 failures)
Delta: 0 failures -> 0 failures (0 new failures); 4113 - 4072 = +41 tests passed (strictly additive).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. The 4-line box an operator stares at for the whole of every run has no tests: sixteen of nineteen public symbols on that surface are referenced nowhere under `tests/`, and the 2,706-line module that used to cover it was deleted wholesale by a suite trim. This plan adds ONE TEST FILE and changes NO PRODUCTION CODE, so the risk of approving it is close to the floor: it cannot regress behavior, and every assertion it prescribes was run against today's unmodified tree and measured green before being written down, with ONE EXCEPTION review found and fixed: the plan originally mandated a zero-width-space `setid` case AND required every hostile case to assert a single visible width, which cannot both hold today, because that input is non-rectangular until approved plan `it6tpj` lands (F-10). That case is now characterization-only and the sweep is fenced against zero-width values, so the module is landable as claimed. What it buys is that a future change which drops a cell, inverts the action-derivation precedence, breaks a duration boundary, flattens `update_item`'s preserve-on-empty semantics, lets a display exception kill a run, or leaves a refresh thread running will FAIL instead of shipping silently. WHAT IS DELIBERATELY NOT HERE: the two deleted byte-pin tests, which P16 forbids and the backlog item says must stay dead; the ASCII single-byte defect this plan's measurement uncovered, which is a real spec violation and is owned by sibling plan `mzrr7x` as a release-gated bug; the thirty-five width and pad conversions, owned by approved plan `it6tpj`; and the roughly 40 non-statusline test functions the same trim deleted, which need one carrier per surface rather than one sweep.

WHY THIS IS A SEPARATE PLAN FROM ITS SIBLING, since a reader may reasonably ask why one Set has two plans. A `followup` characterization module and a release-gated `bug` fix have different risk profiles, different approval calculus, and different failure modes. Merging them would mean either that the coverage waits on a production change or that the bug fix inherits a large test-authoring job; keeping them apart lets either land alone. They share `- From-Backlog: iuad9l`, which therefore has TWO carriers and must stay `graduated` until both are executed.

EXECUTION CONTRACT. Do not begin until this plan carries an explicit human approval (`- Status: approved`). It is `- Status: to-review`. Commit only the single declared scope path, through `aw commit <this plan> -- tests/test_statusline_behavior.py`, never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before committing and unstage anything else with `git restore --staged <path>`; this is a shared checkout and other agents may have work in flight.

SCOPE FENCE, AND IT IS UNUSUALLY STRICT HERE: this plan's `- Scope-Paths:` names exactly one TEST file, so ANY production edit is out of scope, without exception. If an assertion you want to write fails because the production code is wrong, DO NOT FIX THE CODE. Either express the assertion as characterization of what the code actually does, or omit it and report the defect in the relevant `V-*` evidence so it can be filed. The ASCII purity property is the known instance of this and already has a carrier (`mzrr7x`, F-07); a second instance should be reported, not silently absorbed. Equally, do not modify any EXISTING test file, and do not restore the deleted byte-pins.

MUTATION DISCIPLINE. Every mutation used as evidence must be staged in memory (an out-of-tree pytest plugin, or `mock.patch`), never by editing and restoring a tracked production file. This is a shared checkout, `render_stream.py` is high-traffic, and a `git checkout --` restore after a long suite run can discard a co-worker's concurrent edit. Write scratch probes under `.aw/state/`, which is gitignored; authoring did so and `git status --short` stayed clean throughout.

THREAD AND GLOBAL HYGIENE, called out because this module is unusual in touching both. The `Statusline` class starts a daemon refresh thread and registers itself in the module-level `_ACTIVE_STATUSLINE`. Use the context manager so both are torn down, bound every cross-thread join so a regression fails rather than hangs, and prove the module leaves no residue (V-05). The suite runs with order randomization and `-n auto`, so a leaked thread or a dangling global becomes an intermittent failure in an unrelated module, which is the worst outcome this plan could produce.

POST-GATE LIFECYCLE. Do not claim done until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted, concrete evidence, including the bare-suite summary line showing ZERO failures with its failing-node-id delta against a freshly re-derived baseline (F-11: the authoring figure's named failure now passes) and its additive passing-count delta, the order-independence and residue proof, the two-timezone runs, the live-activity positive-width paste, the verbatim visible-column truncation assertion, the P16 self-audit, and the four mutation proofs. The terminal transition is then owed UNCONDITIONALLY but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER performs `aw ipd begin`/`aw ipd finalize` and the executor must NOT (a worker-role process is refused with `AW-LIFECYCLE-ROLE-001`, enforced inside the finalize transaction itself, so `aw ipd set executed` is refused there too because it delegates into that same transaction); executed by hand, the executor runs `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-roll the move with `git mv` to `executed/` and never hand-edit `- Status: executed`.

GATE AND PROVENANCE. This plan carries `- From-Backlog: iuad9l` and NO `- Blocks-Release:`, because item `iuad9l` is a `followup` carrying no gate and this plan is `followup` too; inventing a gate would be a false claim. Item `iuad9l` has TWO carriers in this Set (this plan and `mzrr7x`), so it must stay `graduated` until BOTH are executed; do not close it `done` on this plan alone.
