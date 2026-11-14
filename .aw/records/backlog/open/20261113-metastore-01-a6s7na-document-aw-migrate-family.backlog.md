- Id: a6s7na
- Status: open
- Set: metastore
- Priority: medium
- Work-Kind: followup
- Summary: Document the aw migrate command family for users (carrier for 1vfqdu OQ-08 and ya4ee4 OQ-05)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Scope

User documentation (README and reference docs) for `aw migrate`, `aw migrate layout`, bare `aw migrate`, `aw install --migrate`, and `aw migrate metadata` with its `--describe-host`, `--describe-model`, `--describe-limit` and `--no-describe` options. No metastore plan carries it today; `90iqr1` and its split parts `qhay6a`, `a49djh`, `y1zihp` and `ngc2a2` do not mention these commands.

Decision for the maintainer: which plan carries it. Both reviews recommend adding it to the `y1zihp` cutover docs patch, because documenting `aw migrate metadata` before the Order 13 cutover would invite users to convert repositories into a format phase-A readers cannot load.

## Workflow history
- 2026-11-14 note (aw backlog): maintainer decided 2026-11-14 via /askme: carrier is y1zihp (cutover docs patch); y1zihp to be widened, gain executed:1vfqdu and executed:ya4ee4 dependencies, and return to review
- 2026-11-14 created (aw backlog): Document the aw migrate family (aw migrate, aw migrate layout, bare aw migrate, aw install --migrate) for users; decide which metastore plan carries it (1vfqdu OQ-08, recommended: y1zihp cutover docs patch)
- 2026-11-14 widened: also carries ya4ee4 OQ-05 (aw migrate metadata user docs), the same gap 1vfqdu OQ-08 names
