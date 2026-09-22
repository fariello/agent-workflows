- Id: baskrx
- Status: open
- Set: baskrx
- Priority: medium
- Work-Kind: chore
- Summary: Two runner symbols became byte-identical after hostdedup Order 01 was reviewed and are unlifted

## Workflow history
- 2026-09-22 created (aw backlog): Two runner symbols became byte-identical after hostdedup Order 01 was reviewed and are unlifted

Found while executing plan li44r9 (hostdedup Order 01), by its own committed scanner.

`tools/runner_fork_scan.py` at execution HEAD measured NINETEEN byte-identical real forks between
`oc_runipd` and `agy_runipd`, not the SEVENTEEN plan li44r9 was authored and reviewed against. The two
extra symbols are:

  * `_integrate_stranded_lanes`
  * `handle_integrate_command`

Both became identical AFTER li44r9 was authored, so neither was reviewed under it, and neither appears
in any of the pin tables that plan declared in `Scope-Paths`.

WHY THEY WERE NOT LIFTED OPPORTUNISTICALLY. li44r9's E-01 does instruct that 'a newly identical symbol
is added here', and that instruction was honored for the MEASUREMENT (both are named in its records and
its scanner reports them). Lifting them is a different act: it would touch guard tables outside the
declared fence and would carry two symbols through no review, in a plan whose entire premise is a
reviewable, decision-free tranche.

WHAT THE RIGHT HOME IS. hostdedup Order 02 (`nmlx47`) already owns the remaining divergent symbols and
already declares all four `test_rununify_*` pin files, so it is the natural place to absorb these two.
Note `handle_integrate_command` is currently classified `still-defined-twice` in
`tests/test_rununify_main.py` with a recorded reason (each host binds its own `integrate_lane_branch`
wrapper and its own `run_suite_check`), so whoever lifts it must re-derive whether that reason still
holds or has been overtaken.

Re-measure with `python3 tools/runner_fork_scan.py` before acting; do not trust these counts.
