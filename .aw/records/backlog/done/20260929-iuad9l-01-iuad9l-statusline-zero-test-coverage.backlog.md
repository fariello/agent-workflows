- Id: iuad9l
- Status: done
- Graduated-To: statuscov
- Set: iuad9l
- Priority: medium
- Work-Kind: followup
- Summary: The statusline box renderer has zero test coverage of any kind

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD mzrr7x executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-statuscov-01-mzrr7x-honor-the-ascii-single-byte-guarantee-in-the-runner-statusli.ipd.md); evidence .aw/records/plans/executed/20260930-statuscov-01-mzrr7x-honor-the-ascii-single-byte-guarantee-in-the-runner-statusli.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 6tjq2j, mzrr7x
- 2026-09-29 created (aw backlog): Filed at review of plan it6tpj (/plan-review), discharging a Deferred row that instructed the executor to file it.

`render_stream.format_statusline_lines` renders the runner's live 4-line statusline box and NO TEST IN
THE TREE EXERCISES IT.

MEASURED at review HEAD `2aaf45e2`:

  grep -rln "format_statusline" tests/ agent_workflows/ tools/
  -> agent_workflows/render_stream.py, agent_workflows/oc_runipd.py       (production only)
  -> zero test files

  ls tests/test_render_stream.py  ->  No such file or directory

HOW THE COVERAGE WAS LOST. `tests/test_render_stream.py` held 2,706 lines including
`test_format_statusline_user_example_box_layout` and `test_format_statusline_exact_layout`. Commit
`19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") deleted the entire file. The trim
was deliberate policy work against code-pinning tests, and the two statusline tests it removed WERE
byte-pins, so their removal was defensible on its own terms. What is not defensible is the result: the
surface now has no behavioral coverage either, so a box that misaligns by a column, loses a cell, or
crashes on an unusual input passes the whole suite silently.

WHAT THIS IS NOT. Plan `it6tpj` (from backlog `l76ir6`) adds `tests/test_statusline_visible_width.py`,
which closes the WIDTH-and-GRAPHEME part only: it asserts the box is rectangular in visible columns and
that a truncated label keeps its variation selector. That is one property of one function. It does not
cover which columns appear, the progress bar, the token and spend formatters, the countdown, the
tracker, the elapsed-time formatting, the `use_unicode=False` path as a whole, or the `Statusline`
class that drives the refresh loop.

WHY IT IS WORTH ITS OWN ITEM RATHER THAN A CLAUSE IN THAT PLAN. Restoring outcome-based coverage for a
deleted 2,706-line module is a scoped job with its own design question (which properties are worth
asserting, given the repository now forbids the byte-pins the deleted tests used). Smuggling it into a
width fix would either bloat that fix or, more likely, produce a token gesture. Plan `it6tpj`'s
Deferred section says exactly this and instructed the executor to file this item; it is filed here
instead so the obligation does not depend on an executor remembering.

SUGGESTED SHAPE. Behavioral only, per GUIDING_PRINCIPLES P16: drive `format_statusline_lines` and the
`Statusline` class with real inputs and assert observable properties (line count, column presence,
rectangularity, monotonic elapsed formatting, the ASCII mode's single-byte guarantee, no crash on
empty/absent/oversized fields). Do NOT restore the deleted byte-pins; they are what the trim correctly
removed. Reuse the case matrix `it6tpj` establishes rather than inventing a second one.

EVIDENCE TRAIL: plan `it6tpj` findings F-03 (the deletion) and F-08 (the total coverage hole), and its
Deferred row "RESTORING THE BROADER tests/test_render_stream.py COVERAGE".
