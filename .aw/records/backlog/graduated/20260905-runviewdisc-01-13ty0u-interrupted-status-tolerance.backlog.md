- Id: 13ty0u
- Status: graduated
- Set: runviewdisc
- Priority: medium
- Work-Kind: bug
- Summary: run_viewer flags an interrupted item as a status discrepancy although an unfinished plan MUST still read approved: add interrupted and substantially-complete to the existing tolerance list

## Workflow history
- 2026-09-08 graduated (aw set): PARTIALLY graduated to plan vdabn5 (runviewdisc-02); see the PARTIAL GRADUATION section appended to this item. GRADUATED: the interrupted half, confirmed live by calling audit_step_artifact against a synthetic repo (interrupted gives status_mismatch=True while queued/running/dependency-blocked/blocked/reviewed all give False, with location_mismatch correctly False throughout). NOT GRADUATED: the substantially-complete half, which is UNSOUND AS WRITTEN. That value normalizes to 'complete' at run_viewer.py:472 and 'complete' selects expected_dir_name='executed' at :474-475, so the audit flags the LOCATION too and a status-list entry fixes half a row; worse, the tolerance branch receives ONE token for two distinct run states, so admitting it would also suppress the genuine regression this item's own test case (c) guards. The surviving work needs a location-side decision plus a way to distinguish the two normalized states, and the normalization is shared by six display sites. This item's own closing warning was the right instinct and understated the problem. Line numbers had drifted ~70 lines. Its 1f9m2j boundary argument re-verified correct.
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

## PARTIAL GRADUATION: THE `substantially-complete` HALF IS UNSOUND AS WRITTEN

Measured 2026-09-08 at HEAD a2e0438a by CALLING `audit_step_artifact` against a synthetic repo, which
is what this item's own closing warning asked for ("verify which spelling actually reaches the
comparison rather than assuming"). The warning was the right instinct and understated the problem.

THE `interrupted` HALF IS CONFIRMED AND IS GRADUATED to plan `vdabn5` (runviewdisc-02). With the file
at `- Status: approved` in `pending/`, the only value an unfinished execute-item's plan can hold:

    run=queued                 loc_mismatch=False  status_mismatch=False
    run=running                loc_mismatch=False  status_mismatch=False
    run=dependency-blocked     loc_mismatch=False  status_mismatch=False
    run=blocked                loc_mismatch=False  status_mismatch=False
    run=reviewed               loc_mismatch=False  status_mismatch=False
    run=interrupted            loc_mismatch=False  status_mismatch=True   <-- the defect

THE `substantially-complete` HALF IS NOT GRADUATED, because the fix this item prescribes cannot work.
Same measurement:

    run=substantially-complete loc_mismatch=True   status_mismatch=True
    run=complete               loc_mismatch=True   status_mismatch=True

TWO REASONS, both mechanical rather than matters of taste.

FIRST, THE LOCATION HALF IS ALSO FLAGGED, so adding the value to the STATUS tolerance list fixes half
a row and leaves the discrepancy standing. `substantially-complete` is normalized to `complete` at
`run_viewer.py:472` (`st = "complete" if step.status == "substantially-complete" else step.status`),
and `complete` is one of the two tokens that select `expected_dir_name = "executed"` at `:474-475`.
A plan the driver deliberately did NOT finalize sits in `pending/`, so the location comparison fails.

SECOND, THE TOLERANCE BRANCH CANNOT EXPRESS THE INTENT, because it receives ONE token for two
distinct run states. After normalization a run-side `substantially-complete` and a run-side
`complete` are indistinguishable to the branch. Admitting the token would therefore ALSO suppress the
genuine regression that this item's own test case (c) exists to guard: a `complete` item beside a
plan still at `approved` in `pending/` SHOULD be flagged, because a completed item should have moved.
That fixture is live in `tests/test_run_viewer.py` and asserts both mismatches plus `actual_dir`,
`expected_dir` and `file_status`.

WHAT THE SURVIVING HALF NEEDS, recorded so it is not lost: a LOCATION-side decision (should a
deliberately-unfinalized item expect `pending/` rather than `executed/`?) plus a way to distinguish
the two normalized states. That is a different change with a different risk profile, and the
normalization at `:472` is shared by six display sites governing every completed item in every run,
so touching it is not a small edit. Plan `vdabn5` fences it out explicitly and its E-04 mutation-check
deliberately proves that admitting `complete` into the tolerance branch BREAKS case (c), which is the
evidence that this half cannot be done the prescribed way.

ALSO CORRECTED: this item's cited line numbers have drifted. It cites `:451-468` and `:457` for the
tolerance branch and `:467-468` for the catch-all; at HEAD they are `:525-534` and `:536-537`. The
`Issue` column it cites at `:1418-1420` is at `:1498` and is one of FIVE textual copies of the same
three-term expression, whose unification is owned by pending plan `r2i1b1` (orchprobe-01), so
`vdabn5` proves the fix reaches every surface WITHOUT editing any copy.

The `1f9m2j` boundary argument in this item RE-VERIFIED correct: `run_viewer` reads only
`actual_file.parent.name` and a `- Status:` regex, with zero references to finalize journals,
receipts, git history or commits, so this item genuinely asserts nothing about legitimacy and is not
gated on `rnl3b7`.
