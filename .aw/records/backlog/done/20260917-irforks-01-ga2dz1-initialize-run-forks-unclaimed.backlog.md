- Id: ga2dz1
- Status: done
- Set: irforks
- Priority: medium
- Work-Kind: chore
- Summary: Two of initialize_run's seven forks are claimed by no rununify child, so the Set cannot reach 100% de-duplication for it

## Workflow history
- 2026-09-25 done (aw set): RETIRED (already fixed): 7a28ed11 unified initialize_run into runner_shared.initialize_run_core; all seven forks are now single definitions or thin label wrappers (runner_fork_scan --closure --symbols initialize_run: BOTH-DELEGATE, 4 lines of host_options residue).
- 2026-09-17 created (aw backlog): Two of initialize_run's seven forks are claimed by no rununify child, so the Set cannot reach 100% de-duplication for it

## What is wrong

The maintainer's 2026-09-16 directive for the `rununify` Set is that "at the end of the SET, there
should be one code base shared by the two runners that contains 100% of the otherwise redundant code
that currently is duplicated between the two runners". `initialize_run` (`rununify` Order 09, plan
`orziju`) cannot reach that with the children the Set currently declares.

Measured at HEAD `87682a3b`, `initialize_run` closes over **SEVEN still-double-defined symbols**, each
of which a shared core would have to receive as an injected parameter. Per-symbol accounting:

| Symbol | Owning sibling | Does that sibling lift it? |
|---|---|---|
| `write_report` | `tx6q0h` (04) E-04 | **YES**, and it repairs a live `run_viewer` defect on the way |
| `enforce_requested_action` | `tx6q0h` (04) E-02 | **YES**, named among its five host-string-only symbols |
| `parse_plan_file` | `sy7uwh` (06) | **PARTLY.** That plan unifies the record type and its two readers, so the fork's CAUSE is addressed; whether the function itself becomes one object is that plan's business, not stated here as settled |
| `build_dynamic_manifest` | none | **NO** |
| `expand_selectors` | none (see below) | **NO** |
| `set_plan_approved` | none | **NO** |
| `enforce_dependency_preflight` | none | **NO** |

So **four are claimed by NO plan in the Set**, and a fifth (`expand_selectors`) is a known dependent:
sibling `i3d6ml`'s own review recorded `discover_plans`/`expand_selectors` as blocked on `sy7uwh`'s
`parse_plan_file`, and `i3d6ml` was re-scoped at review from 48 symbols to 9 which do NOT include it.

## The actionable half

After `tx6q0h` lands, the fork count for this function drops from seven to five WITHOUT
`initialize_run` moving at all. The remaining four unclaimed forks are individually liftable acts, each
small enough for its own behavioral pin, and none requires the 409-line function to relocate. That is
the cheapest real progress available for this function and no plan currently claims it.

## Why this is filed rather than folded into a plan

Two reasons. First, plan `orziju` is a MEASURE-AND-GUARD plan by its 2026-09-16 re-scope and performs
no lift, so it has no authority to claim these symbols. Second, the same shape has now been measured
for THREE of the four split children (`yrqyxb` found nine of eleven forks unclaimed, `ty3cj6` the same,
this plan four to five of seven), which suggests the Set's child decomposition systematically
under-covers the closures rather than missing one symbol in one place. Backlog `5jsjnr` records the
`run_queue` half; this is the `initialize_run` half.

## Where

`agent_workflows/oc_runipd.py:3397` and `agent_workflows/agy_runipd.py:2126` (the two definitions);
the closure classification and the per-symbol table are in
`.aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md`
and asserted mechanically in `tests/test_rununify_initialize_run.py`.
