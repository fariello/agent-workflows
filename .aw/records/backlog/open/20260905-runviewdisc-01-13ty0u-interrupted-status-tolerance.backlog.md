- Id: 13ty0u
- Status: open
- Set: runviewdisc
- Priority: medium
- Work-Kind: bug
- Summary: run_viewer flags an interrupted item as a status discrepancy although an unfinished plan MUST still read approved: add interrupted and substantially-complete to the existing tolerance list

## Workflow history
- 2026-09-05 created (aw backlog): run_viewer flags an interrupted item as a status discrepancy although an unfinished plan MUST still read approved: add interrupted and substantially-complete to the existing tolerance list

THE DEFECT. `audit_step_artifact` tolerates several run-status/file-status pairs that are legitimately
different (`run_viewer.py:451-468`). The list at `:457` covers `queued`, `running`,
`dependency-blocked`, and `blocked`, each of which may coexist with a file status of `approved`,
`to-review`, `draft`, `reviewed`, `queued`, or `running`.

`interrupted` is MISSING from that list. So it falls through to the catch-all at `:467-468`
(`if f_norm != st: status_mismatch = True`) and an interrupted item is reported as a discrepancy.

WHY THAT IS WRONG, and it is a tautology rather than a judgement call: an item whose turn was
INTERRUPTED by definition did not finish. Its plan therefore MUST still carry the status it had when
the turn began, which for an execute-action item is `approved`. There is no other legal value it
could hold. Flagging it asks the operator to investigate a state that could not have been otherwise.

`substantially-complete` has the same property and should be added in the same pass: the plan stays
in `pending/` at `approved` because the driver deliberately did NOT finalize it, so the difference
is the DESIGNED outcome, not a mismatch.

MEASURED. Run `run-20260905T201722Z-3652350` (2026-09-05), a single-item run of `i6015i` that was
interrupted twice:

    Item                             Expected  Actual    Expected     Actual
                                     Location  Location  Status       Status
    20260831-worksequence-01-i6015i  pending/  pending/  interrupted  approved

Note the LOCATION COLUMNS MATCH (`pending/` == `pending/`), so `location_mismatch` is correctly
False. The row appears purely because of the status comparison. The per-step table's `Issue` column
also reads `YES` for the same reason (`run_viewer.py:1418-1420`).

WHY THIS IS SOUND TO FIX, AND WHY IT IS NOT THE CASE BLOCKED IN `1f9m2j`. This distinction is the
whole point of filing a separate item, so do not merge the two.

  * `1f9m2j` (BLOCKED on `rnl3b7`) concerns run `integration-blocked` + file `executed` in
    `executed/`. Classifying that pair benign REQUIRES asserting the move was LEGITIMATE, i.e. that
    `aw ipd finalize` really ran rather than someone hand-editing `- Status:` and `git mv`-ing the
    file. `run_viewer` reads exactly two things, `actual_file.parent.name`
    (`run_viewer.py:438`) and a `- Status:` regex (`:444-445`), with ZERO references to finalize
    journals, receipts, git history, or commits anywhere in the module. The two situations are
    byte-identical to it, so any verdict there is a fabrication.
  * THIS item requires NO such assertion. "An unfinished item still sits where it started" is
    ENTAILED by the run record alone: the run status itself says `interrupted`, and the location
    already matches. Nothing external is consulted and nothing is inferred about legitimacy.

So this is grounded in the data the viewer already has, and is NOT gated on `rnl3b7`.

THE FIX. Add `interrupted` and `substantially-complete` to the existing tolerance branch at
`run_viewer.py:457`. Prefer extending the EXISTING mechanism over introducing a new classification
vocabulary: the ad-hoc tolerance list is admittedly not a general solution (a direction-aware
classifier would be, and that is what `1f9m2j` wanted before it proved unsound without evidence), but
adding two values to a list that already encodes exactly this idea is a minimal, honest change.

Be careful about the normalization already in play: `st` is computed as
`"complete" if step.status == "substantially-complete" else step.status`
(`run_viewer.py:404`), and `f_norm` applies the same mapping to the FILE status (`:447-449`). So
the run-side value to match is `complete`, not `substantially-complete`; verify which spelling
actually reaches the comparison rather than assuming.

TESTS. Add cases pinning: (a) run `interrupted` + file `approved` in `pending/` -> NOT a
discrepancy; (b) the same pair must ALSO clear the `Issue` column in `render_steps_table`; (c) the
existing true-positive fixture at `tests/test_run_viewer.py:1139-1174` (run `complete`, file
`approved` in `pending/` -- a genuine regression, since a completed item should have moved) MUST keep
being flagged. That last case is the guard against over-suppression and is the reason (a) and (c) look
superficially similar but must diverge.

Note `tests/test_run_viewer.py` reads run directories from `.aw/records/runs/`, which is gitignored:
the module fails 14/42 in a bare worktree and passes 42/42 in the real checkout (measured both ways
2026-09-05). Validate in the real checkout.
