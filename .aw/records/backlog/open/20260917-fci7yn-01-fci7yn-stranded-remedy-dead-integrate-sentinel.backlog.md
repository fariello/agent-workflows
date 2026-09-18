- Id: fci7yn
- Status: open
- Set: fci7yn
- Priority: medium
- Work-Kind: bug
- Summary: Stranded-lane remedy says 'no aw integrate verb exists yet' though it shipped: lane_remedy_hint probes cmd_integrate, a symbol that does not exist

## Workflow history
- 2026-09-17 created (aw backlog): lane_remedy_hint probes hasattr(oc_runipd,'cmd_integrate'), which never existed (real symbol handle_integrate_command), so it prints the stale manual remedy though aw oc integrate shipped in executed plan rl67b0

MEASURED 2026-09-18 at HEAD `d188eaad`:

    hasattr(oc_runipd,"cmd_integrate") = False
    real symbol present                = True     # handle_integrate_command
    remedy printed: Recover it by hand: `git log main..<branch>` to see the work, then merge that
                    branch (no `aw integrate` verb exists yet).

`aw oc integrate` EXISTS and is advertised in `aw oc --help`:

    {runipd,run,review,integrate,update-models,sync-models,profile,profiles}
      integrate   Re-integrate an already verified lane with NO agent turn
                  (thin alias of 'aw oc runipd integrate <id6>').

## Root cause

`attention.lane_remedy_hint` (`attention.py:1297-1320`) gates the remedy on a runtime capability probe:

```python
integrate_exists = hasattr(_oc, "cmd_integrate")
```

There is no `cmd_integrate` in `agent_workflows/oc_runipd.py`. The integrate entry point is
`handle_integrate_command` (the module's integrate-related symbols are `_integrate_stranded_lanes`,
`handle_integrate_command`, `integrate_lane_branch`, `integrate_review_lane_branch`), and the CLI
parser at `cli.py:3929` forwards `aw oc integrate` as REMAINDER args rather than binding a `cmd_*`
function. So the probe can never be True and the stale branch prints unconditionally.

The guard's own docstring states the rule it is trying to enforce, and the rule is right:

    NAMES ONLY A VERB THAT EXISTS AT RUNTIME. Plan `rl67b0` adds `aw <host> integrate <id6>`; it had
    not landed when this shipped, so the honest remedy is the manual one and the verb is printed only
    once it is really there. Do not print a verb that does not exist.

Plan `rl67b0` (`integpath-04`, "add an integrate verb and make resume merge finished lanes") is now in
`.aw/records/plans/executed/` with `- Status: executed`. The verb landed; the sentinel was never
updated to a symbol that exists, so the conditional silently froze in its pre-`rl67b0` state.

## Expected

In a repository where the verb exists, the remedy names it: "Recover it with `aw oc integrate <id6>`."
The manual fallback still fires where it genuinely does not exist.

## Fix sketch

1. Probe a symbol that actually exists (`handle_integrate_command`), or better, probe the CLI surface
   the user would type rather than a module attribute, since that is what the docstring's rule is
   really about.
2. Add a test that FAILS if the probed symbol disappears, so this cannot silently freeze again. A bare
   `hasattr` against a name nothing else references is unobservable when it rots; pin the name.
3. While here, note that the printed remedy is per-lane and the verb takes an `<id6>`; the record
   already carries `id6`, so the hint can name the concrete command (`aw oc integrate 03ie04`) instead
   of a placeholder.

## Why this matters

The docstring states the stake: "An alarm with no route trains its own dismissal." The report tells the
reader to perform a manual `git log` and merge, when a purpose-built verb exists that re-verifies and
routes the merge through the same merge-and-revalidate gate an in-run integration uses. The manual
route is not merely slower, it SKIPS that gate, so the stale hint actively steers an operator toward
the less safe recovery path.

## Class of bug worth noting

A capability probe keyed on a symbol name that nothing else references is a DEAD SENTINEL: it fails
silently and permanently the moment the name drifts, and its failure mode is indistinguishable from the
condition it is testing for. Worth grepping for siblings of this pattern.
