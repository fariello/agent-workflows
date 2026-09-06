- Id: 6kq1lj
- Status: open
- Blocks-Release: next
- Set: runsverify
- Priority: high
- Work-Kind: bug
- Summary: aw runs with an unrecognized leaf name silently degrades into a run-id search and exits 0: a mistyped or not-yet-built subcommand reports success having done nothing

## Workflow history
- 2026-09-06 created (aw backlog): aw runs with an unrecognized leaf name silently degrades into a run-id search and exits 0: a mistyped or not-yet-built subcommand reports success having done nothing

THE DEFECT. `aw runs` supports two shapes at once: `aw runs <leaf> <target>` (nine read-only
leaves) and `aw runs [<target> ...]` (the bare viewer). Plain argparse cannot express that, so
`_ViewerOrLeafSubParsersAction` (`cli.py:623-653`) disambiguates by hand with ONE rule: if the
first token exactly matches a registered leaf name, route to that leaf; OTHERWISE hand the whole list
to the viewer, which treats every token as a run-id/setid/substring TARGET.

The consequence is that a first token which is NOT a known leaf is not an error. It becomes a search
term, matches nothing, is silently dropped, and the remaining tokens still resolve. The command then
prints an ordinary report and EXITS 0.

MEASURED 2026-09-05:

    $ aw runs verify run-20260905T211011Z-3780617
    run-20260905T211011Z-3780617  [lanectn, revsweep, ...]  2026-09-05 21:10:12
      pid: 3780617 [exited], runtime: 13h 42m 40s
      24 steps: 1 blocked, 4 dependency-blocked, 15 executed, 3 reviewed, 1 complete
    EXIT CODE: 0

Nothing was verified. `verify` is not a registered leaf (the real one is `verify-ledger`), so it
was consumed as a target. The operator asked for an integrity check and received a status report plus
a success exit.

WHY THIS IS A SAFETY DEFECT AND NOT A TYPO NUISANCE. Until 2026-09-05 the spec itself documented
`aw runs verify <run-id>`, and SEVEN shipped recovery messages in `run_evidence.py` told operators
to run it (fixed in the same pass that filed this item). So the fail-open path was not hypothetical:
the repository's own error messages routed operators into it, at exactly the moment they were being
told something might be wrong with a run's ledger. A checker that reports success when it did not run
is worse than one that is missing.

SECOND, SMALLER DEFECT ON THE SAME SURFACE: `verify-ledger` itself exits 0 when the ledger is
absent (`error: ledger file not found for target '<id>'` then exit 0). An error printed on a
success exit is invisible to any script or CI step that checks the exit code.

THE FIX (direction, not prescription). A first positional that is not a registered leaf and does not
resolve to any run should FAIL LOUDLY: nonzero exit, and a message naming the registered leaves plus
the closest match (`verify` -> `verify-ledger` is a one-edit suggestion). Be careful of the
documented AMBIGUITY RULE at `cli.py:652`: a Set or run id that legitimately collides with a leaf
name currently routes to the LEAF, and that precedence must not silently invert. Note also that a
bare `aw runs` with no arguments is a legitimate call meaning 'all runs', so the refusal must key on
'unresolvable first token', not on 'token present'.

The maintainer's stated minimum (2026-09-05) is that an unimplemented or unrecognized spelling must
exit NONZERO and say so plainly, even before the underlying gap is closed. That is strictly better
than today's silent success and is a reasonable first step on its own.

WHILE FIXING, ALSO AUDIT the other leaves for the same shape: any command whose failure path prints a
message and returns 0 has this defect. `verify-ledger`'s missing-ledger path is one confirmed
instance.
