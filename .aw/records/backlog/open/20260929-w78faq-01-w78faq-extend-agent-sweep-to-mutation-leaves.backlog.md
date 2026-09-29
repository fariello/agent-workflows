- Id: w78faq
- Status: open
- Set: w78faq
- Priority: medium
- Work-Kind: followup
- Summary: The agent-surface conformance sweep covers no mutation-class leaf, so 79 declared machine surfaces stay unexecuted and a dropped emit there still passes CI

## Workflow history
- 2026-09-29 created (aw backlog): Deferred by plan f36de0 (graduating kjr5ol) as the named durable carrier for its mutation-class gap.

DEFERRED BY IPD `f36de0` (Set `agentemitswp`), which graduates backlog `kjr5ol` and is the plan that builds the sweep this item extends.

WHAT f36de0 COVERS AND WHAT IT LEAVES: that plan drives every `read`/`check`/`bare` parser leaf declaring `agent_record_kind="result"` with `--agent` in a subprocess and asserts a schema-valid terminal record with exit parity. Measured at HEAD 58dc1c70 while authoring it: 151 parser leaves, 161 declarations, of which 79 are `command_class="mutation"`. NONE of those 79 are executed by the sweep.

WHY IT WAS NOT DONE THERE: driving a mutating verb live needs a write-isolation design that plan deliberately did not attempt, namely a temp repo (or a per-leaf fixture) for every leaf, or a proven universal `--dry-run`/preview guarantee that no mutation escapes it. Either is a real design question rather than an increment of the read-side harness, and folding it in would have made a focused plan unreviewable.

WHY IT STILL MATTERS: the defect class f36de0 exists to close is 'a declared machine surface that emits nothing, and no test notices'. That class is not specific to read verbs. The original instance (commit 4cfa2283 deleting `return get_renderer(ctx).emit(res, ctx)` from `attention.run`'s no-project branch) happened to be a read path, and the six live instances f36de0 fixes are the hook-gate leaves, but a `mutation` leaf can drop its emit exactly the same way and nothing would go red.

WHAT MAKES THIS TRACTABLE: f36de0 computes its universe from `command_surface.discover_parser_leaves` crossed with a declaration predicate rather than from a hand-written list, so widening coverage to mutation leaves is a PREDICATE CHANGE plus an isolation strategy, not a rewrite of the harness. Its `tests/conformance_matrix.py` additions (a runnable-argv table and a `cwd` parameter on `run_cli`) are the pieces to build on.

NOT IN SCOPE HERE: the `aw config` family's eight `format_agent_json` ImportError crash sites, which are owned by backlog `dtq6jr`.
