- Id: 4mdi4v
- Status: open
- Set: 4mdi4v
- Priority: medium
- Work-Kind: chore
- Summary: Six execute_item_core getattr(driver_module, ...) fallbacks default to a shared definition that cannot satisfy the call site, so a host without its own copy gets TypeError instead of working behavior

## Workflow history
- 2026-09-29 created (aw backlog): Filed while authoring plan vbhat9 (from backlog 2yjc5l) as the durable carrier for that plan's deferred fallback-chain row (its F-09 and F-10).

MEASURED 2026-09-29 at HEAD f7f9e7de while authoring plan `vbhat9` from backlog `2yjc5l`. That item
warned that `execute_item_core` binds `route_recovery_turn` with
`getattr(driver_module, ..., globals().get(...))`, so "a future host with no copy of its own would
silently get the divergent logic". The DIVERGENCE half of that warning is now moot (plan `cdxcbh`
made the shared body the only real body). What survives is the FALLBACK SHAPE, and it is broader than
the one symbol the item named.

## What is wrong

`runner_shared.execute_item_core` rebinds a set of names off `driver_module`, defaulting to the shared
module-level definition. For six of them the shared definition CANNOT satisfy the call site, because it
declares a required keyword-only argument that only a host wrapper can supply and the call site does
not pass:

    route_recovery_turn        required kwonly: save_state        call site passes 4 positional args
    integrate_lane_branch      required kwonly: host_label, run_checked, action_kind
    build_lane_outcome         required kwonly: run_checked
    git_head                   required kwonly: run_checked
    git_status                 required kwonly: run_checked
    acquire_review_sweep_lane  required kwonly: save_state        (its call site DOES pass it, so this
                                                                  one is currently safe)

So the default is not a working fallback, it is a deferred `TypeError`. Demonstrated by simulating a
host that lacks its own copy:

    >>> f = getattr(fake_host, "route_recovery_turn", runner_shared.route_recovery_turn)
    >>> f is runner_shared.route_recovery_turn
    True
    >>> f(run_dir, state, item, True)      # the call shape execute_item_core uses
    TypeError: route_recovery_turn() missing 1 required keyword-only argument: 'save_state'

This is NOT a live defect on the two real hosts: both `oc_runipd` and `agy_runipd` define every one of
these, so the `getattr` always finds the host copy and the default is never taken. The exposure is a
THIRD HOST. The repository already treats a runnerless third host as a supported shape
(`tests/test_hostdedup_third_host.py` builds a `HostLabels` descriptor with no `*_runipd.py` module at
all), so the fallback is exactly the seam such a host would land on.

## Why this is a chore and not a bug

No user is affected today and no output is wrong, because the default is never reached on either
shipped host. Filing it `bug` would gate a release on a path no user can currently execute. What makes
it worth tracking is that the same class has shipped SILENT defects twice, by the repository's own
written measurements:

  * `execute_item_core` carries a comment recording that a pre-existing
    `build_lane_outcome(repo, wt_handle, item["id6"])` call resolved the shared definition, raised
    `TypeError` for the missing `run_checked`, and was "swallowed whole by the
    `contextlib.suppress(Exception)` around it" on EVERY integration refusal (measured 2026-09-20), so
    `integration_changed_files` was never written and a human reading a refused item saw no file list.
  * `_record_checkpoint_stop`'s docstring records that its shared body called the module-level
    `git_status(repo)` and would have written
    `"<unobserved: git_status() missing 1 required keyword-only argument: 'run_checked'"` into every
    level-3 stop record, replacing the observed working-tree state with an error string. It states:
    "That was invisible precisely BECAUSE the definition was dead; pointing the hosts at it is what
    would have shipped the defect."

Both are fixed. The pattern that produced them is not.

## Fix direction (not decided; this is the design question)

The repository already ships THREE different answers to this, and picking among them is the work:

1. PRE-BIND A LAMBDA as the default, which is what `write_report` and `save_state` do two rebindings
   above in the same function (`lambda r, s: globals()["save_state"](r, s, write_report=write_report)`).
   This makes the fallback actually work.
2. DROP THE DEFAULT so a missing host attribute raises at BIND time rather than at call time, turning a
   late mystery `TypeError` into an early explicit one.
3. REQUIRE THE INJECTION with no default at all, which is what `_record_checkpoint_stop` chose for its
   `git_status_fn` precisely so "the mistake cannot recur silently".

Option 1 is the only one that lets a runnerless third host work; options 2 and 3 only make the failure
honest. A decision that differs per symbol is legitimate and should be recorded per symbol.

## Provenance

- Plan `vbhat9` F-09 (the six bindings and the `TypeError` demonstration) and F-10 (the two
  already-shipped silent instances). That plan deliberately kept `agent_workflows/runner_shared.py` out
  of its `- Scope-Paths:` so a release-blocking verification plan could not quietly become a change to
  the shared execution loop.
- Backlog `2yjc5l`, whose closing note should point here for the fallback half of its concern.
