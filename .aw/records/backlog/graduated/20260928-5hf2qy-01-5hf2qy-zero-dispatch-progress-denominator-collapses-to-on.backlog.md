- Id: 5hf2qy
- Status: graduated
- Graduated-To: 5hf2qy
- Blocks-Release: next
- Set: 5hf2qy
- Priority: low
- Work-Kind: bug
- Summary: The progress denominator reads 0/1 for a zero-dispatch queue of 8 matched items

## Workflow history
- 2026-09-29 set (aw backlog): graduated by run run-20260929T021205Z-3914774: 35mjqc
- 2026-09-28 created (aw backlog): Found while authoring plan 4po0sc from backlog b7oicl; measured at HEAD b26cced3.

Measured 2026-09-28 at HEAD `b26cced3` while authoring plan `4po0sc` (from backlog `b7oicl`).

Rendering the real `render_stream.render_run_summary_table` with EIGHT matched `reviewed`/zero-attempt
items (the shape backlog `em0z50` measured live, where `aw oc run wtiso` matched 8 plans and acted on
none) yields:

    Progress: 0/1  [          ]   0% (8 reviewed)
    Total (0/1 items run)

while EIGHT per-artifact rows are rendered above it. The denominator says ONE and the table shows
EIGHT. An operator reading `0/1` is told this run had one unit of work when it matched eight.

THE CAUSE is deliberate in its own docstring and its consequence is not. `render_stream.dispatchable_work_total`
ends `return sum(1 for item in queue if item_is_dispatchable_work(item)) or 1`, and the `or 1` exists so
"a caller dividing by it cannot raise". That guard is correct; collapsing the DISPLAYED denominator to 1
is the side effect nobody chose. The zero case is already reported honestly by the numerator being 0 and
by the closing disposition summary's `total: 8 matched, 0 acted on, 8 not acted on`.

SCOPE NOTE: this is NOT the `b7oicl` defect and must not be folded into it. `b7oicl` is about the
`Outcome:` WORD (`COMPLETED` for a run that dispatched nothing); plan `4po0sc` fixes that word and
explicitly asserts the progress line is BYTE-IDENTICAL before and after, because `progdenom`
(`a0d6e04b`) already owns the progress arithmetic and a second fix there would double-correct.

FIX: decide what the denominator should show when nothing is dispatchable. Options measured as
available: keep the divide guard but display `len(queue)` (or the matched count) in the rendered
fraction; or render the fraction as `0/8` with an explicit "none dispatchable" note; or suppress the
bar entirely for a zero-dispatch run and let the disposition summary carry the count. The choice is a
judgement about what the fraction MEANS (work this run can do, versus artifacts it matched), which is
why this is filed rather than decided here.
