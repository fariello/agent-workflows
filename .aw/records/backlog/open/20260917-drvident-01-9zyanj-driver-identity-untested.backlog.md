- Id: 9zyanj
- Status: open
- Set: drvident
- Priority: high
- Work-Kind: bug
- Summary: No test covers the runners' driver-identity contract, so run analytics can silently lose host attribution

## Workflow history
- 2026-09-17 created (aw backlog): No test covers the runners' driver-identity contract, so run analytics can silently lose host attribution

## What is wrong

`initialize_run` freezes each run's provenance as `state["driver"] = {"path":
str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__))}` (`oc_runipd.py:3745`,
`agy_runipd.py:2455`). TWO consumers read that value's BASENAME as the host discriminator:

* `run_analytics_sources.driver_generation` (`:183-207`) maps the basename through
  `DRIVER_GENERATIONS`, and its own docstring records that "the basename is the ONLY discriminator
  that works";
* `run_viewer.load_run_summary` (`:865-870`) substring-matches `oc_runipd` / `agy_runipd` to label a
  run `OpenCode` / `Antigravity`.

Until plan `orziju` (rununify Order 09) landed `tests/test_rununify_initialize_run_characterization.py`,
**NO test asserted the runners' end of that contract**: every existing test fed a HAND-WRITTEN
`{"driver": {"path": "agent_workflows/oc_runipd.py"}}` fixture to the consumers, so the consumers were
covered and the producers were not.

## Why it matters, measured rather than argued

`__file__` is evaluated in the module where the code is DEFINED. So any refactor that moves this
statement into a shared module makes BOTH hosts record that shared module's name, and both consumers
return `unknown` for every run created afterwards. Measured by sabotaging `agy_runipd` exactly as such
a relocation would:

    $ python3 -m pytest tests/test_run_analytics_sources.py tests/test_run_viewer.py \
          tests/test_run_analytics.py -o addopts=""
    183 passed in 4.25s

183 green while every agy run had become host-unattributable. `tests/test_oc_runipd.py` produced a
failure set byte-identical to its pre-sabotage baseline, so nothing anywhere noticed. The loss would
be PERMANENT and RETROACTIVELY UNFIXABLE for affected runs, because the wrong basename is written into
each run's durable `state.json`.

## Status: the producer half is now covered, the general gap is not

Plan `orziju` E-02 added `EachHostRecordsItsOwnDriverIdentity`, which asserts for BOTH hosts that the
recorded basename is that host's runner module, that the digest matches that same module, that
`driver_generation`/`generation_host` return the host's labels rather than `unknown`, that the viewer
renders `OpenCode`/`Antigravity`, and that the two hosts record DIFFERENT paths. It also carries a
non-vacuity control constructing the naive-relocation state and showing every consumer assertion fail.

So this item is NOT "add that test": it exists. What remains is the GENERALIZATION, which is why it is
filed rather than closed:

1. The invariant "the driver record names the module that CREATED the run" lives only in a
   `run_analytics_sources` docstring and now in one test file. It is load-bearing enough for a spec
   sentence, and a grep for it across `.aw/records/specs/` returns nothing.
2. The `rununify` Set intends to share this function eventually (maintainer directive 2026-09-16:
   100% de-duplication). When that happens the shared core MUST take the caller's module path as a
   REQUIRED parameter with no default. A default is exactly how this regresses silently.
3. Nothing prevents a THIRD driver generation from being added without a producer-side test, which is
   the same gap in a new place.

## Where

`agent_workflows/oc_runipd.py:3745`, `agent_workflows/agy_runipd.py:2455`,
`agent_workflows/run_analytics_sources.py:183-207`, `agent_workflows/run_viewer.py:865-870`.
Found by plan `orziju` (rununify Order 09); analysis in
`.aw/records/walkthroughs/20260917-irclosure-01-ztmh1b-initialize-run-the-line-count-that-hides-the-divergence.walkthrough.md`.
