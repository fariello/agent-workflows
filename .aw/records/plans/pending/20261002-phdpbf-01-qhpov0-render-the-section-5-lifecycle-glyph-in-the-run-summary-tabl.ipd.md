# IPD: Render the Section 5 lifecycle glyph in the run summary table Status cell

- Date: 2026-10-02
- Kind: child
- Concern: Align `render_run_summary_table`'s `Status` cell with its five sibling lifecycle surfaces by rendering the spec `uonrjg` Section 5 glyph ahead of the native status word, resolving backlog `phdpbf` / plan `4taj2e` OQ-01 in the affirmative.
- Scope: `render_stream.render_run_summary_table`'s `Status` cell and the column-width computation feeding it, the `use_unicode` wiring at the six driver call sites that reach it, and the tests pinning both.
- Scope-Paths: agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_run_summary_lifecycle_glyph.py, tests/test_run_summary_malformed_entry.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: phdpbf
- From-Spec: uonrjg
- Set: phdpbf
- Order: 1
- Highest E allocated: 05
- Author: agent
- Id: qhpov0

## Workflow history

- 2026-10-02 draft (agent): created.
- 2026-10-02 to-review (agent): authored from backlog item `phdpbf`; decision question resolved from repository evidence (see Findings F-01 and OQ-01).

## Goal

Render the Section 5 lifecycle glyph immediately before the native status word in
`render_run_summary_table`'s `Status` cell, matching the form the five sibling surfaces already
emit, and fix the two mechanical defects that make the naive version of that change wrong: the
column width is measured from the GLYPHLESS raw row, and the glyph's Unicode-vs-ASCII choice would
come from a different source than the table's own box-drawing choice.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: make the glyph's capability choice single-sourced

- [ ] E-01 In `render_stream.render_run_summary_table`, derive the lifecycle glyph's Unicode/ASCII
      choice from the function's OWN `use_unicode` parameter rather than from the `Palette`'s
      independent `use_unicode` attribute, so the glyph and the box-drawing characters cannot
      disagree. Do this by building the glyph through a `Term` whose `unicode` is the function's
      `use_unicode` (reusing `pal.lifecycle_term()`'s resolved color depth so the color decision is
      still the caller's), NOT by mutating `pal`.
  - Depends on: none
  - Expected outcome: `render_run_summary_table(..., pal=Palette(False), use_unicode=False)` emits
    the Section 5 ASCII fallback (`!` for `blocked`) in the `Status` cell, while
    `render_run_summary_table(..., pal=Palette(False, use_unicode=False), use_unicode=True)` emits
    the Unicode grapheme. The glyph tracks the function argument in both directions.
  - Execution state: pending

### Task group 2: render the glyph and keep the box rectangular

- [ ] E-02 Render the glyph into the `Status` cell ahead of the native word, padded to 2 visible
      columns by `Term.format_lifecycle_marker(resolved, width=2, style=<color>)`, following the
      `attention.py` / `ipd_lint.py` form (glyph, then the status word) so the column COUNT and
      ORDER are unchanged and only the `Status` column widens. Pass `style=False` when `color` is
      false so no escape is emitted on a `NO_COLOR` / piped stream.
  - Depends on: E-01
  - Expected outcome: a `blocked` row's `Status` cell reads `⚠︎ blocked` (ASCII: `! blocked`); the
    header stays `Status`; `headers` and `aligns` are unmodified.
  - Execution state: pending

- [ ] E-03 Make the `Status` column's width account for the glyph. The width loop measures
      `raw_rows`, and the glyph is added only to the styled cell, so the `Status` width would be
      computed 2 columns short and the pad would go negative, breaking the box. Fix it by carrying
      the glyph in the RAW `Status` cell too (so `col_widths` measures the same text that is
      printed), keeping raw and styled cells width-identical by construction rather than by adding
      a compensating constant.
  - Depends on: E-02
  - Expected outcome: every rendered line has one identical visible width; no `+ 2` fudge constant
    exists anywhere in the width computation.
  - Execution state: pending

### Task group 3: thread the capability decision from the drivers

- [ ] E-04 At the six `render_run_summary_table` call sites that do not pass the stream's Unicode
      capability (`oc_runipd` lines near the three `driver_label="opencode"` calls, `agy_runipd`
      near the three `driver_label="antigravity"` calls, and `runner_shared.print_status`), pass
      `use_unicode=should_unicode(sys.stdout)` and construct the `Palette` with the same value, as
      `oc_runipd`'s `Palette(should_color(sys.stdout), use_unicode=should_unicode(sys.stdout))`
      site already does. Do not change any other argument.
  - Depends on: E-01
  - Expected outcome: a run whose stdout cannot encode the glyph prints the ASCII fallback instead
    of a replacement character or a `UnicodeEncodeError`; `should_unicode` is imported/visible at
    each site (it is already re-exported in both runners).
  - Execution state: pending

### Task group 4: tests

- [ ] E-05 Add `tests/test_run_summary_lifecycle_glyph.py` driving `render_run_summary_table` and
      asserting on its real returned string: (a) the `Status` cell carries the Section 5 glyph for
      `blocked` (`⚠︎`, the U+FE0E-bearing grapheme) and for a settled `executed` row; (b) the ASCII
      mode emits the exact Section 5 fallback and NO Unicode grapheme; (c) the table is rectangular
      (one distinct visible width) in unstyled, styled, and ASCII-box modes with a VS-bearing glyph
      present, reusing the box-width helper style of `tests/test_run_summary_visible_width.py`;
      (d) `Palette(False)` output contains no ANSI escape; (e) the malformed-entry row renders the
      `unknown` glyph (`?`) rather than crashing. Then update
      `tests/test_run_summary_malformed_entry.py`, whose `row[5] == MALFORMED_ENTRY_TOKEN` assertion
      becomes false once the glyph precedes the word, to assert the cell CONTAINS the token and
      carries the `unknown` glyph.
  - Depends on: E-03, E-04
  - Expected outcome: the new module fails against the pre-E-02 code and passes after; the full
    suite is green with no other test edited.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- THE GLYPH-INSIDE-THE-STATUS-COLUMN FORM IS ALREADY SETTLED by two surfaces, and this plan copies
  it rather than inventing a shape. `attention.py` states it in a comment: "THE GLYPH LIVES INSIDE
  THE STATUS COLUMN, immediately preceding the status word (Section 9.1 ...)" and "Folded into the
  existing column rather than added as a new one so Section 12's 'existing column order MUST be
  preserved' holds literally: the column COUNT and their order are unchanged, and only the Status
  column's width grows from 8 to 10", implemented as
  `term.format_lifecycle_marker(resolved, width=2, style=colored)` followed by
  `T.pad_visible(st_styled, 8)`. `ipd_lint.py` repeats it, noting "only this column widens 12 -> 15".
- WIDTH IS MEASURED BY VISIBLE COLUMNS, NEVER `len()`, throughout this renderer. That rule is
  stated in `render_run_summary_table`'s own leading comment ("Every cell and banner pad in this
  function is computed with `_T.visible_width`, never `len()`") and is required by spec `uonrjg`
  Section 9.4 bullet 4 ("no use of `len(styled_text)` to compute a visible column"). It was
  implemented by plan `4taj2e`, the plan that filed this item.
- `Palette` ALREADY EXPOSES THE GLYPH HELPER this plan needs: `render_stream.Palette.lifecycle_glyph`
  ("The Section 5 lifecycle GLYPH for ``resolved``, styled and padded by VISIBLE columns"),
  delegating to `Term.format_lifecycle_marker`. `runner_shared` already calls it as
  `pal.lifecycle_glyph(finish_resolved, width=2)` for the per-item finish line, so the glyph is
  already a routine part of runner output; the summary table is the straggler.
- THE ASCII FALLBACK IS THE RENDERER'S DECISION, NOT THE SEMANTIC MODULE'S:
  `lifecycle_style.glyph_for` documents that "``unicode=False`` selects the exact Section 5 ASCII
  fallback. The CHOICE between the two is the RENDERER's (it owns stream capability,
  ``AW_ASCII_ONLY`` and ``FORCE_ASCII``)". This is why E-01 routes the choice through the function's
  `use_unicode` argument.
- `aw ipd scaffold` derives the filename and mints the id6; plans are not hand-named (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE DECISION IS YES, AND THE SPEC DECIDES IT RATHER THAN TASTE.** Spec `uonrjg` Section 9.1 requires that "glyph MUST immediately precede either id6 or status so its referent is obvious", and Section 11 item 2 makes "Glyph and color are redundant cues. Either can be removed without losing the state." The table today renders the styled WORD ONLY, so on a `NO_COLOR` or piped stream it carries NEITHER cue: color is suppressed and there is no glyph to fall back to. That is the exact failure Section 11 item 2 exists to prevent, so this is a conformance gap and not merely a cosmetic inconsistency. | `st_styled = pal.lifecycle(st_resolved, st_val) if color else st_val` in `render_run_summary_table`; measured with `Palette(False)`, the rendered `blocked` cell is the bare word `blocked`; Section 9.1 and Section 11 item 2 as quoted |
| F-02 | **FIVE SIBLING SURFACES ALREADY RENDER THE MARKER INTO A STATUS COLUMN, so the form is established and this table is the odd one out.** This is the measurement the backlog item asserts, re-verified. | `term.format_lifecycle_marker` call sites: `attention.py` (two, incl. the row builder), `run_viewer.py`, `ipd_lint.py` (two), `status_set.py`, `cli.py` (two), plus `term.format_lifecycle_row` itself; `runner_shared` reaches the same glyph via `pal.lifecycle_glyph(finish_resolved, width=2)` |
| F-03 | **THE NAIVE CHANGE BREAKS THE BOX, and this is the finding that makes the plan more than a one-liner.** `col_widths` is computed from `raw_rows` (`for row in raw_rows: ... max(col_widths[idx], _T.visible_width(str(cell)))`), while the row printer pads the STYLED cell (`raw_len = _T.visible_width(str(cell)); pad = w - raw_len`). Adding the glyph to the styled cell only leaves the `Status` width 2 columns short and the pad NEGATIVE. Measured: raw `blocked` is 7 visible columns, `⚠︎ blocked` is 9, and a column width of 7 yields a pad of -2. E-03 fixes it by putting the glyph in the raw cell too, so the measured text IS the printed text. | the two quoted loops in `render_run_summary_table`; measured `visible_width` values 7 and 9 |
| F-04 | **THE GLYPH'S UNICODE CHOICE AND THE BOX'S UNICODE CHOICE COME FROM DIFFERENT SOURCES TODAY, so sourcing the glyph from `pal` would produce a mixed table.** `render_run_summary_table` takes its own `use_unicode` parameter for the box characters, while `Palette` carries an INDEPENDENT `use_unicode` defaulting to `True`. The repository's own ASCII-box test passes `pal=Palette(False)` (so `pal.use_unicode` is `True`) together with `use_unicode=False`, which would render a UNICODE lifecycle glyph inside an ASCII `+`/`-` box. Verified: `Palette(False).lifecycle_glyph(...)` returns `'⚠︎ '` while `Palette(False, use_unicode=False)` returns `'! '`. | `test_run_summary_visible_width.test_cell_variation_selector_is_rectangular_ascii_box` passing `Palette(False)` with `use_unicode=False`; `Palette.__init__(self, enabled, *, use_unicode: bool = True)`; the two measured glyph values |
| F-05 | **SIX OF THE SEVEN PRODUCTION CALL SITES NEVER PASS THE STREAM'S UNICODE CAPABILITY,** so after this change they would emit a Unicode glyph onto a stream the repository already has a helper for declining. Both runners already import `should_unicode` and one site in each already pairs it with `Palette`, so E-04 is applying an existing local pattern, not inventing one. | `oc_runipd` 3 sites and `agy_runipd` 3 sites calling `render_run_summary_table(state, run_dir, ... pal=pal, ...)` with no `use_unicode`; `runner_shared.print_status` likewise; contrast `oc_runipd`'s `Palette(should_color(sys.stdout), use_unicode=should_unicode(sys.stdout))` and `agy_runipd`'s identical line; `should_unicode as should_unicode` re-exported in both runners |
| F-06 | **ONE EXISTING TEST WILL FAIL AND MUST BE UPDATED DELIBERATELY, not discovered during execution.** `test_run_summary_malformed_entry` asserts `row[5] == MALFORMED_ENTRY_TOKEN` on the exact cell this plan changes. The malformed token resolves to the `unknown` stage, whose glyph is `?` in BOTH modes, so that row gains `? ` and the equality breaks while the containment holds. | the quoted assertion and its `# Row layout:` comment; measured `resolve_item_lifecycle('malformed-entry').stage == 'unknown'` and `glyph_for('unknown')` = `?` for both `unicode=True` and `False` |
| F-07 | **NO MACHINE SURFACE IS AFFECTED, so Section 9.5 is not engaged.** `render_run_summary_table` is reached only from the two runners' human summary prints and `runner_shared.print_status`; there is no `--agent` or `--json` caller, and the function has no JSON output path. | `render_run_summary_table(` call sites are exactly `oc_runipd` (3), `agy_runipd` (3), `runner_shared.print_status` (1), plus tests; no occurrence in `cli.py` or `run_viewer.py` |
| F-08 | **THE AMBIGUOUS-WIDTH CAVEAT IS UNCHANGED AND MUST NOT BE OVERSTATED.** Two Section 5 glyphs this change can place in the cell are East Asian Width `A` (`▶` U+25B6 for `executing`, `◇` U+25C7 for `parked`), and the box-drawing characters are themselves Ambiguous, so a CJK-configured terminal already scales the box. This plan closes no part of that; it must not add a comment implying the table is now width-perfect. | spec `uonrjg` Section 9.4's prior-art note naming `▶` and `◇`; the existing `WHAT IS NOT FIXED` comment in `render_run_summary_table` |

## Proposed changes (ordered, validatable)

1. E-01: single-source the glyph's Unicode choice onto the function's `use_unicode` argument (F-04).
2. E-02: render the marker ahead of the native word in the `Status` cell, unstyled when color is off (F-01, F-02).
3. E-03: carry the glyph in the raw cell so `col_widths` measures the printed text (F-03).
4. E-04: thread `should_unicode(sys.stdout)` at the six call sites that omit it (F-05).
5. E-05: add the new behavioral test module and update the one assertion F-06 identifies.

## Deferred / out of scope (with reason)

- AMBIGUOUS-WIDTH HANDLING for `▶` and `◇` (F-08). Spec `uonrjg` Section 9.4 explicitly admits that
  "perfect alignment cannot be guaranteed across every terminal's ambiguous-width policy", and the
  box characters are Ambiguous too, so no fix confined to this cell could deliver it.
  - Carrier-Declined: DECLINED ON THE SPEC'S OWN TERMS, and this is the same declination plan
    `4taj2e` recorded for the identical concern on this identical function. Section 9.4 states the
    ambiguous-width guarantee is unreachable and requires only its four contract bullets; this plan
    satisfies the fourth and `use_unicode=False` remains the existing guarantee for width-constrained
    terminals. There is no defect to carry because the spec declines the guarantee.
- CONVERTING `format_statusline_lines` to the lifecycle resolver. It is a different surface with its
  own evidence burden, and spec R10.3 permits `render_stream.py` to retain non-lifecycle event
  glyphs.
  - Carrier-Declined: NOT DECLINED ON MERIT, ALREADY CARRIED ELSEWHERE. Plan `4taj2e` deferred this
    same surface with an explicit instruction that it be filed as its own backlog item, recording
    that review measured it as having ZERO test coverage (no test mentions `format_statusline_lines`),
    so the work is "author coverage, then convert". Filing a second item for the same surface from
    this plan would duplicate that obligation rather than carry it. This plan's filed scope is the
    `Status` cell of `render_run_summary_table` and nothing else.
- CONVERTING `format_event_prefix`. Its glyph table is an EVENT/severity table, not a lifecycle one,
  and `EVENT_PREFIXES_ASCII` is the bounded fix that already shipped for its ambiguous glyphs.
  - Carrier-Declined: DECLINED ON MEASUREMENT, matching `4taj2e`'s declination of the same item. No
    glyph in `EVENT_PREFIXES`/`STATUS_GLYPHS` is a Section 5 lifecycle glyph, so spec R10.3's
    consumer obligation does not reach it ("`render_stream.py` MAY retain event glyphs and severity
    colors that are not lifecycle semantics"). There is no conformance gap to carry.
- ADDING A LEGEND to the summary table. Section 9.2 asks for a legend in a view with three or more
  semantic stages "unless the words already appear beside every glyph".
  - Carrier-Declined: DECLINED BECAUSE THE SPEC'S OWN EXEMPTION APPLIES. After E-02 this table
    prints the native status word beside every glyph, which is the precise condition Section 9.2
    names for not owing a legend, so no obligation is created and nothing needs carrying.
- CHANGING THE `Verify` CELL's hand-rolled green/red, or the banner's `c_green`/`c_red` outcome
  colors.
  - Carrier-Declined: DECLINED AS OUTSIDE THE SPEC. These are generic command-level outcomes, which
    R10.3's final paragraph explicitly places outside the lifecycle spec ("Generic `Term` outcomes
    such as command-level OK, WARN, and FAIL remain valid and are outside this spec. Do not
    mechanically replace every checkmark in the repository"), so there is no defect or conformance
    gap to carry.

## Scope check

- Over-scope: none. The three production modules named in `Scope-Paths` are exactly the renderer and
  the two runners holding the call sites F-05 measures; `runner_shared.py` is in scope solely for
  `print_status`'s one call.
- Under-scope: `tests/test_run_summary_malformed_entry.py` is listed because F-06 proves one of its
  assertions must change; no other existing test asserts on the `Status` cell's exact text
  (`test_run_summary_visible_width` asserts only rectangularity, which E-03 preserves).

## Required tests / validation

- `python3 -m pytest tests/test_run_summary_lifecycle_glyph.py tests/test_run_summary_malformed_entry.py tests/test_run_summary_visible_width.py` green.
- Full `python3 -m pytest` green (bare, per AGENTS.md: the configured `addopts` already supply `-q -n auto`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

No spec amendment. This plan brings an existing surface INTO conformance with approved spec
`uonrjg` (Sections 9.1, 9.3, 9.4 and Section 11 item 2) without changing what the spec requires, so
no `.spec.md` file is in `Scope-Paths`. The spec's acceptance criteria already cover the behavior
being added; nothing in Section 5's table, the rendering contract, or R10.3's consumer list needs
new wording for this cell.

## Open questions

### OQ-01: Should this table's `Status` cell render the Section 5 lifecycle glyph?

- Blocking: no
- Status: resolved
- Owner: agent
- Resolution or deferral rationale: RESOLVED YES FROM REPOSITORY EVIDENCE, which is why this plan
  exists rather than asking the maintainer again. Plan `4taj2e` deferred this as "a presentation
  decision that is not mine to make" and filed it as backlog `phdpbf`. Re-examined against the
  approved spec, it is not purely a presentation preference: F-01 shows the current cell carries
  NEITHER of the two redundant cues Section 11 item 2 requires once color is disabled, because the
  word alone is all it prints. Section 9.1's "glyph MUST immediately precede either id6 or status"
  is normative, five sibling surfaces already implement it (F-02), and `Palette.lifecycle_glyph`
  already exists for it. The residual judgement a human might still want is whether to accept the
  `Status` column widening by 2 columns, which is the same trade `attention.py` and `ipd_lint.py`
  already took and recorded in their comments.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python snippet and its ACTUAL output rendering the same `blocked`
    queue four ways and showing the glyph tracks the FUNCTION argument, not the palette's: (a)
    `pal=Palette(False), use_unicode=True` -> `⚠︎`; (b) `pal=Palette(False), use_unicode=False` ->
    `!` and NO `\u26a0` anywhere in the output; (c) `pal=Palette(False, use_unicode=False),
    use_unicode=True` -> `⚠︎`; (d) `pal=Palette(True), use_unicode=False` -> `!`. Cases (c) and (d)
    are the ones that fail if the glyph is sourced from `pal`. Also paste the committed diff hunk
    and confirm by reading it that `pal` is NOT mutated.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rendered `Status` column (strip ANSI) for a queue containing one
    `blocked` and one `executed` row, showing `⚠︎ blocked` and `✓ executed` with the glyph BEFORE
    the word and the header still reading `Status`. Paste the committed diff and confirm by reading
    it that `headers` and `aligns` are untouched (same entries, same order, same length). Separately
    paste a `Palette(False)` render piped through a check that the output contains NO `\x1b`, proving
    `style=False` is honored on a no-color stream.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the FULL rendered table for a queue whose statuses include `blocked`
    (the VS-bearing `⚠︎`) alongside at least two other stages, together with the computed set of
    distinct `visible_width` values over its lines, and show that set has exactly ONE element.
    Repeat for styled (`Palette(True)`) and ASCII-box (`use_unicode=False`) modes and paste all
    three results. Paste the committed width-computation hunk and confirm by reading it that the
    raw and styled `Status` cells are built from the same glyph-bearing text and that NO constant
    offset (`+ 2` or similar) was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n -A8 "render_run_summary_table\(" agent_workflows/oc_runipd.py
    agent_workflows/agy_runipd.py agent_workflows/runner_shared.py` output and confirm by reading it
    that ALL SEVEN production call sites now pass `use_unicode=`, naming each by its enclosing
    function. Paste the `Palette(...)` construction line at each changed site showing it carries the
    same `should_unicode(sys.stdout)` value. Then paste an actual run of
    `aw oc run --help`-adjacent status path or a direct `runner_shared.print_status` invocation
    against a real run directory under an `AW_ASCII_ONLY=1` environment, showing ASCII glyphs and no
    `UnicodeEncodeError` and no replacement character.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new test module's full `python3 -m pytest
    tests/test_run_summary_lifecycle_glyph.py` output with its `N passed` line, and paste the output
    of running that module against the PRE-CHANGE renderer (e.g. via `git stash` of the production
    hunks) showing it FAILS, which is what proves it tests behavior rather than restating the
    implementation. Confirm by reading the committed test file that it drives
    `render_run_summary_table` and asserts on the returned STRING, and that it uses no `inspect`,
    `ast`, or source-reading of production code (AGENTS.md: no code-pinning tests). Paste the
    updated `test_run_summary_malformed_entry` assertion and the full bare `python3 -m pytest`
    summary line showing the whole suite green. Paste `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> --
<paths>`, never `git add -A` and never pushing. Paste ACTUAL runner output for every test claim.
Run the suite BARE as `python3 -m pytest`.

This plan is authoring-complete and carries NO `Readiness:` field: that field is an output of
`/plan-review` and writing it here would forge an attestation. Execution requires human approval
(`aw ipd set approved <plan>`) first. After every `V-*` reports `pass` with pasted evidence and
`aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/`
through the tooled transition; backlog item `phdpbf` is set `graduated`, not `done`, by the runner.
