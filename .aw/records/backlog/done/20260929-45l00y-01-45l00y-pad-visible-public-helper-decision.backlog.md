- Id: 45l00y
- Status: done
- Graduated-To: padvisible
- Set: 45l00y
- Priority: low
- Work-Kind: followup
- Summary: Decide whether term._pad_visible should become a public alignment-aware padding helper

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD n7yaa6 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-padvisible-01-n7yaa6-promote-the-private-visible-width-padding-helper-to-one-shar.ipd.md); evidence .aw/records/plans/executed/20260930-padvisible-01-n7yaa6-promote-the-private-visible-width-padding-helper-to-one-shar.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: n7yaa6
- 2026-09-29 created (aw backlog): Filed at review of plan it6tpj (/plan-review), discharging OQ-01's carrier obligation.

An API DECISION for the maintainer, surfaced by two concurrent renderer conversions. No defect exists;
the question is whether a private helper should be promoted rather than duplicated.

THE SITUATION, measured at review HEAD `2aaf45e2`. `term._pad_visible(text, width)` already performs
visible-width padding and its docstring says it is "the one padding path lifecycle rendering uses, which
is what Section 9.4's fourth contract bullet asks for". Two properties make it unusable by the
statusline box:

  1. it is PRIVATE to `term` (leading underscore);
  2. it LEFT-ALIGNS ONLY (`return text + (" " * pad) if pad > 0 else text`), and most of the statusline
     box's pads are RIGHT-aligned.

So plan `it6tpj` writes twenty-two inline `" " * max(0, w - visible_width(text))` expressions instead.
Its authoring tried `_pad_visible` for three sites and abandoned it for reason (2); review re-confirmed
both properties.

THE QUESTION. Should `term` expose an alignment-aware public padding helper (for example
`pad_visible(text, width, align="left"|"right")`) that every renderer shares, instead of each renderer
spelling the arithmetic inline?

WHY IT IS NOT A BUG AND WAS RIGHT TO DEFER. Both forms produce identical output; `it6tpj` measured the
inline form sufficient for all twenty-two sites, and its bare-suite run is clean with the fix staged.
Promoting a private helper and adding an alignment parameter creates a NEW PUBLIC SURFACE in `term`,
which spec `uonrjg` Section 9.4 designates as the shared home for width handling, so the shape of that
surface is a design decision with spec reach rather than a bug fix. Bundling it into a release-gated
defect fix would also make the evidence for both halves harder to read.

WHY THE MOMENT MAY BE NEAR, which is the reason to record it rather than drop it. Section 9.4 forbids
"per-renderer width guesses" and permits "a shared display-width helper", and inline arithmetic
repeated across renderers drifts toward the former. TWO renderers in `render_stream.py` are being
converted concurrently: `it6tpj` converts `format_statusline_lines` (22 pads) and `4taj2e` converts
`render_run_summary_table` (13 measurements). The plans' own reasoning is that a THIRD renderer needing
it is the moment to extract; after those two land, `term`'s own table plus two renderers will be
spelling the same expression.

WHAT TO DECIDE. Whether to extract, and if so the signature (an `align` parameter versus a
right-aligning sibling), whether the truncating counterpart `truncate_visible` should gain a matching
pad-or-truncate form, and whether existing inline sites should be migrated in the same change or left
alone.

PROVENANCE: plan `it6tpj` OQ-01 (`Blocking: no`, `Status: deferred`, `Owner: maintainer`,
`Finding: F-05`), whose `Carrier-Declined` instructed the executor to file this. Filed at review so the
question does not depend on an executor remembering. See also `it6tpj` F-05 for the abandoned
three-site attempt.
