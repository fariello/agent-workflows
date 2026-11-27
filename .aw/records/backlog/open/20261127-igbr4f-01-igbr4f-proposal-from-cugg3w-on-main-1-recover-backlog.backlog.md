- Id: igbr4f
- Status: open
- Set: igbr4f
- Work-Kind: followup
- Priority: high
- Summary: Proposal from cugg3w: On main: (1) recover backlog item 3pxjya from aw/lane/cugg3w
- Short-Description: Proposal from cugg3w: On main: (1) recover backlog item 3pxjya from aw/lane/cugg3w
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 created (aw backlog): Proposal from cugg3w: On main: (1) recover backlog item 3pxjya from aw/lane/cugg3w

## Agent Proposal from cugg3w

- Run-Id: run-20261127T045218Z-1963184
- Proposing-Item: cugg3w
- Lane-Branch: aw/lane/cugg3w
- Blocked-By: 6 failing batch A tests blocked by Order 317 p109wy (SQLite reviews projection) and backlog 3pxjya (status_set.py and check_engine.py bare-repo resolve_project_context fallbacks). Maintainer selected Option 2 on 2026-11-27.
- Kind: different-approach
- Size: material

### Why
Per maintainer Option 2 decision (cugg3w OQ-02), cugg3w stays strictly test-only and must execute after szykgd -> ... -> 3e0vfy -> 6cltab; sibling plans on main cannot be mutated from this blocked lane.

### Proposed Change
On main: (1) recover backlog item 3pxjya from aw/lane/cugg3w (commit 70c80a9dfd02cd8effc971805e8267cc804c674d); (2) expand Order 322 plan 6cltab with 3pxjya (add in_tree_records -> artifact_meta.legacy_context fallback across status_set.py and check_engine.py) and review/approve 6cltab; (3) re-chain Item-Dependencies to fljn9b -> szykgd -> otin36 -> p109wy -> q6fiws -> j1f454 -> lec341 -> 3e0vfy -> 6cltab -> cugg3w -> psm9ac -> x8id25 -> e0g2gt -> qi0kl6 -> x3mig6 -> x1mmdp (updating szykgd -> executed:fljn9b, 6cltab -> executed:3e0vfy, cugg3w -> executed:6cltab, psm9ac -> executed:cugg3w, and orchestrator 63ib9r child table); (4) re-apply cugg3w's preserved batch A test hunks from aw/lane/cugg3w (commit 42a03c71a7c30bfc5853f166ef3c956fe08b5ee7) once 6cltab executes.

### Affected Paths
- .aw/records/backlog/open/20261127-metastore-01-3pxjya-cutover-status-set-check-engine-bare-repo-context.backlog.md
- .aw/records/plans/pending/20261125-metastore-315-szykgd-make-specs-releases-spec-link-search-and-dep-gate-log-aware.ipd.md
- .aw/records/plans/pending/20261127-metastore-322-6cltab-populate-cli-creator-log-fields-and-align-aw-find-bare-repo.ipd.md
- .aw/records/plans/pending/20261125-metastore-308-cugg3w-convert-test-batch-a-artifact-meta-through-backlog-in-the-cu.ipd.md
- .aw/records/plans/pending/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md
- .aw/records/plans/pending/20261102-metastore-00-63ib9r-build-the-artifact-metadata-store-of-spec-4sd62s-orchestrato.ipd.md
