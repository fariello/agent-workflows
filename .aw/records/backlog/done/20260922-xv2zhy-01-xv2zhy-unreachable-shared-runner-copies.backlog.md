- Id: xv2zhy
- Status: done
- Set: xv2zhy
- Priority: medium
- Work-Kind: chore
- Summary: Five runner_shared definitions are unreachable dead copies, and unreachable shared code rots undetected

## Workflow history
- 2026-09-26 done (aw set): Retired MOOT (verified 2026-09-26 at 2f77995d): 4 of the 5 dead copies are gone (classify_recovery_disposition/build_verify_and_continue_notice via cdxcbh adef0e6a, reconcile_disposition 6b94a4d9, route_recovery_turn now delegated). The remaining _record_forced_stop host copies are owned by approved plan 184tn9, and the general --triples guard by open backlog yo0ooe.
- 2026-09-22 created (aw backlog): Five runner_shared definitions are unreachable dead copies, and unreachable shared code rots undetected

Found while executing plan li44r9 (hostdedup Order 01). REPORTED AS A CLASS, because one instance of it
was a real latent defect that li44r9 had to fix mid-execution.

THE MEASURED INSTANCE, which is what makes this worth filing rather than a tidiness note.
`runner_shared._record_checkpoint_stop` existed while BOTH hosts kept their own real bodies, so nothing
called it. Its body read `git_status(repo)`, but `runner_shared.git_status` takes a REQUIRED keyword-only
`run_checked` (each host's wrapper binds its own). So the call raised `TypeError`, the surrounding
`except Exception` swallowed it, and the recorded `git_state` would have read
`<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'>` for EVERY level-3
stop -- silently replacing the observed working-tree state, which is the entire evidentiary point of a
stop record, with an error string. It had never been noticed precisely BECAUSE it was unreachable.
li44r9 found it only because pointing the hosts at that definition activated it, and
`tests/test_runner_stop.py::test_stop_isolated_git_status` then failed. It is fixed there (the host's
bound `git_status` is now injected with no default).

THE REMAINING POPULATION, measured with the committed scanner at that plan's execution HEAD via
`python3 tools/runner_fork_scan.py --triples`. Five symbols are still defined in `runner_shared` while
BOTH hosts keep a real body, so three bodies must be kept in step and the shared one is dead:

  * `_record_forced_stop`
  * `build_verify_and_continue_notice`
  * `classify_recovery_disposition`
  * `reconcile_disposition`
  * `route_recovery_turn`  (this one IS currently identical to the hosts' bodies)

Each of the first four ALREADY DIFFERS from the hosts' bodies, which is the same starting condition the
measured defect had. None has been executed, so none is known-broken; equally, none is known-good.

WHAT TO DO, and the ordering matters. All five belong to hostdedup Order 02 (`nmlx47`)'s divergent
tranche, so the fix is to point the hosts at the shared definition as part of that work -- NOT to delete
the shared copies, which would discard work, and NOT to point the hosts at them blindly, which is what
would have shipped the measured defect. Before activating any of them, RUN the tests that cover the
host behavior and expect failures: an unreachable body has never been exercised, so its first real call
is its first test.

GENERALIZABLE GUARD WORTH CONSIDERING: a shared definition that no host reaches is invisible to every
test, so a cheap check for 'defined in runner_shared and also defined in every host' would surface this
class automatically. `tools/runner_fork_scan.py --triples` reports it today but nothing gates on it.
