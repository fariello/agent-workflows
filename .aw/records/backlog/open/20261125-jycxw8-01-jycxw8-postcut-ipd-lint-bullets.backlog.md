- Id: jycxw8
- Status: open
- Set: jycxw8
- Work-Kind: bug
- Priority: high
- Summary: Post-cutover ipd lint and ipd scaffold still assume the bullet block and Workflow history H2
- Short-Description: Post-cutover ipd lint and ipd scaffold still assume the bullet block and Workflow history H2
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-25 created (aw backlog): Post-cutover ipd lint and ipd scaffold still assume the bullet block and Workflow history H2

Found by 2k5t16 (run run-20261125T162650Z-1337442) while smoke-testing the metastore code patch (.aw/system/cutover/metastore-code.cutover.patch applied over the docs patch) in a throwaway repo.

Observed: after the loader/writer switch, `aw ipd scaffold --apply` writes a log-backed plan (meta/<id6>.jsonl plus the two-key YAML mirror) but ipd_authoring.build_skeleton still emits the legacy bullet block (Date, Kind, Concern, Scope, Scope-Paths, Item-Dependencies, Status, Work-Kind, Priority, Set, Order, Highest E allocated, Author, Id) and a ## Workflow history H2 into the body. With those bullets and the H2 stripped (the post-cutover shape of spec 4sd62s 4.1), `aw ipd lint` reports IPD-M101 for Date, Concern and Scope, IPD-I304 (Highest E allocated), and IPD-H202 (required H2 missing: Workflow history).

Cause: ipd_schema.META_REQUIRED still lists Date/Concern/Scope as bullet fields and CHILD_H2_ORDER/ORCHESTRATOR_H2_ORDER still start with H_WORKFLOW_HISTORY; ipd_lint._overlay_state_into_meta_fields maps State.fields['date'] but the log carries created_day, and has no mapping for highest_e_allocated; ipd_lint reads Concern/Scope only from bullets (m0001_convert moves them to body sections). ipd_authoring._AUTHORING_PLACEHOLDERS and set_records (lines ~179-218) also write or match bullet lines.

Fix: make ipd_schema/ipd_lint log-aware (required fields from the log, Concern/Scope from body sections, no Workflow history H2), drop the bullet block and history H2 from build_skeleton and the placeholders, and add it to the cumulative code patch before cxxmyv applies it. No current metastore child (g45vyv, x1mmdp, 0zylig) owns this.
