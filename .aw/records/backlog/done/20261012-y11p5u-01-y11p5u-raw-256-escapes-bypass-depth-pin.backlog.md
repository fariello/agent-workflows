- Id: y11p5u
- Status: done
- Graduated-To: y11p5u
- Work-Kind: bug
- Blocks-Release: next
- Set: y11p5u
- Priority: low
- Summary: Raw 38;5 escapes in pwatch, runners_monitor and render_stream headers bypass the color_depth pin

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 32fso3 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-y11p5u-01-32fso3-raw-sgr-escapes-in-pwatch-runners-monitor-and-render-stream.ipd.md); evidence .aw/records/plans/executed/20261014-y11p5u-01-32fso3-raw-sgr-escapes-in-pwatch-runners-monitor-and-render-stream.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 32fso3
- 2026-10-12 same-status (aw set): Maintainer ruling 2026-10-12: color_depth=none must turn off ALL color; reclassified bug
- 2026-10-12 created (aw backlog): filed while graduating cvtg9u (plan lv0dvv), which fixes the Term generic axis only

## Context

Plan lv0dvv (graduating backlog cvtg9u) makes the generic Term styling axis (`Term.colorize`, `Term.color256` and everything built on them) honor the `color_depth` pin. It deliberately does NOT touch modules that emit hard-coded SGR 38;5;N literals without going through `Term`. Measured at HEAD 3ecef6088 with `grep -c 38;5;` over `agent_workflows/*.py` (excluding docstrings): `pwatch.py` 19 (the `C_*` module constants), `runners_monitor.py` 7 (`c_step`, `c_set`, `c_id6`, ... gated only on `color_enabled`), `render_stream.py` 14 (the runner header and statusline literals such as `c_runner`, `b_blue`, `bdr_color`). `render_stream.Palette.__call__` (the event/severity axis built on `_ANSI_CODES`) likewise honors only `enabled`, so it emits 16-color escapes at pin `none`. Each is gated on a boolean color decision only, so at `color_depth` pin `none` or `16` on a capable TTY these surfaces still emit 256-color escapes.

## Ask

Route these literals through the resolved tier (`term.resolve_color_depth`) so pin `none` emits no escapes and pin `16` emits no `38;5;` sequences, reusing the generic 256->16 reduction lv0dvv adds to `term`.

Also, once lv0dvv lands, drop the now-stale residual-exposure caveat ("generic axis ... ignores the depth pin entirely per finding F-08, tracked in carrier backlog item cvtg9u") from the `LifecycleColorDepthSeamSweepTests` and `LifecycleColorDepthCrossSurfaceCliTests` docstrings in `tests/test_term.py`, rewording it to name only the raw-literal surfaces this item covers.

## Provenance
- From-Plan: lv0dvv
- Related: cvtg9u
