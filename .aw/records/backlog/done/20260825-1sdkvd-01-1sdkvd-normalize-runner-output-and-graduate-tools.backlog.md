- Id: 1sdkvd
- Status: done
- Set: 1sdkvd
- Priority: medium
- Work-Kind: followup
- Summary: Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw

## Workflow history
- 2026-09-08 done (aw set): OBSOLETE, FULLY: all three parts shipped in the runnernorm Set on 2026-08-27, whose Order 0 (ryvoi5) is titled with this item's summary and cites this item by id twice. (a) render_stream.py owns render_event/Palette/Heartbeat and oc_runipd.py defines ZERO of them (275324a2, runnernorm dg28i9); the normalization went further than asked, since tests/test_runner_refork_guard.py now asserts symmetrically that neither driver re-defines any of 28 (runner, symbol) pairs. (b) all four verbs resolve live: aw agy run, aw agy sessions, aw agy view, aw pwatch, implemented at agent_workflows/{agy_run,agy_sessions,agy_view,pwatch}.py (48cf10af, runnernorm puot79). (c) the packaged-core + host-subcommand + compat-shim pattern was honored: tools/agy_run.py, tools/agy_sessions.py, tools/pwatch.py and tools/view-antigravity-jsonl.py are 35-41 line delegating shims whose docstrings each state they contain NO tool logic. One naming detail recorded: the canonical verb for the single-target runner is aw agy exec, not aw agy run, because aw agy run is aliased to the multi-IPD queue driver; the shim documents the deliberate split. No Blocks-Release on this item, so no gate is dropped.
- 2026-08-25 created (aw backlog): Normalize runner interactive output into a shared renderer and graduate remaining tools (runagy, pwatch, agy sessions/view) under aw

OBSOLETE 2026-09-08, FULLY, VERIFIED IN-REPO. DO NOT GRADUATE THIS ITEM: all three parts shipped in the
`runnernorm` Set on 2026-08-27, and that Set's Order 0 (`ryvoi5`) is literally titled "normalize runner
interactive output and graduate remaining tools" and CITES this item by id twice.

PART (a) IS DONE. `agent_workflows/render_stream.py` exists and owns `render_event`, `Palette` and
`Heartbeat`; `oc_runipd.py` defines ZERO of them (measured: 3 definitions in `render_stream.py`, 0 inline
in the driver). Landed in `275324a2`, "runnernorm dg28i9: extract runipd render layer into shared
render_stream". The normalization went FURTHER than this item asked: both host drivers now import the
shared objects and `tests/test_runner_refork_guard.py` is a symmetric AST-based guard asserting neither
driver re-defines any of 28 (runner, symbol) pairs, so the duplication this item wanted prevented is now
prevented BY TEST rather than by convention.

PART (b) IS DONE, all four verbs. Measured live: `aw agy run`, `aw agy sessions`, `aw agy view` and
`aw pwatch` all resolve (`--help` exits 0). The implementations are packaged at
`agent_workflows/agy_run.py`, `agent_workflows/agy_sessions.py`, `agent_workflows/agy_view.py` and
`agent_workflows/pwatch.py`. Landed in `48cf10af`, "runnernorm puot79: graduate agy sessions/view and
pwatch under aw".

PART (c) IS DONE AND IS THE PART MOST WORTH RECORDING, because it is the requirement a future reader
would most doubt: this item asked that the graduation follow "the packaged-core + host-subcommand +
compat-shim pattern". It did. `tools/agy_run.py` (41 lines), `tools/agy_sessions.py` (35),
`tools/pwatch.py` (35) and `tools/view-antigravity-jsonl.py` (35) are all THIN DELEGATING SHIMS whose
docstrings each state they contain "NO tool logic", name the packaged module they delegate to, and point
at the canonical `aw` verb. So the compat half of the pattern is honored, not skipped.

ONE NAMING DETAIL, recorded so nobody reads it as a gap: this item says `agy_run.py -> aw agy run
(renamed runagy)`. The canonical verb for that single-target multi-mode runner is actually
`aw agy exec`; `aw agy run` is aliased to the separate multi-IPD queue driver `agy_runipd`. The shim's
own docstring explains the distinction and states the two "genuinely distinct" tools do not collide. So
both verbs exist and the split is deliberate, which satisfies the item's intent under a better name.

WHY THIS IS `done` AND NOT `parked`: nothing here awaits a decision or an opportunity. Every deliverable
exists in the tree with a named commit, and the item's own splitting suggestion (renderer versus
tool-graduation) is exactly how the `runnernorm` Set was decomposed (`dg28i9` for the renderer, `puot79`
for the tools). Evidence citation for the close is the executed orchestrator
`.aw/records/plans/executed/20260825-runnernorm-00-ryvoi5-normalize-runner-interactive-output-and-graduate-remaining-t.ipd.md`.

This item carries no `Blocks-Release`, so no gate is dropped by closing it.

ORIGINAL ITEM TEXT BELOW, PRESERVED. Its analysis was correct and its plan was adopted essentially
verbatim; only its status is stale.

Follow-on work deferred by the awocrunner Set (which graduated runipd to `aw oc runipd`). Non-blocking.

(a) Extract runipd's render_event / Palette / Heartbeat streaming layer (currently inline in agent_workflows/oc_runipd.py) into a shared agent_workflows rendering utility so interactive/progress output is normalized across consumers rather than duplicated per tool.

(b) Graduate the remaining source-checkout tools under the packaged host-subcommand pattern: agy_run.py -> `aw agy run` (renamed runagy), agy_sessions.py -> `aw agy sessions`, view-antigravity-jsonl.py -> `aw agy view`, pwatch.py -> `aw pwatch`.

(c) This follows the packaged-core + host-subcommand + compat-shim pattern established by the awocrunner Set (agent_workflows/oc_runipd.py + `aw oc` group + tools/ipdrunner/runipd.py shim). Non-blocking; can be split (renderer vs tool-graduation) when picked up.
