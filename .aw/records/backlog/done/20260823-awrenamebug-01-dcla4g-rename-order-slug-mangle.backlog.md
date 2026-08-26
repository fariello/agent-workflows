- Id: dcla4g
- Status: done
- Set: awrenamebug
- Priority: high
- Kind: bug
- Summary: aw rename --order mangles the slug when --slug is omitted (injects the old cluster segment into the new slug)
- Blocks-Release: next

## Workflow history
- 2026-08-25 done (aw set): Verified fixed: aw rename plans <id6> --order NN preserves the slug (live repro on demo plan; no cluster-prefix injection). Executed IPD 5rzupk, commit 40ab3b2; regression test_rename_order_preserves_slug_end_to_end.
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 blocks-release-set (opencode its_direct/pt3-claude-opus-4.8-1m-us): added `Blocks-Release: next` (gates 2.0.0 / f33nrj) by HAND-EDIT, as a justified exception to the use-the-tool rule: `aw backlog set --blocks-release` cannot set it here because of bug 61qk4a (no-op-transition non-persist) - the tool that would do this is itself broken. Fix 61qk4a, then this can be re-set via the tool.
- 2026-08-23 created (aw backlog): aw rename --order mangles the slug when --slug is omitted (injects the old cluster segment into the new slug)

BUG: 'aw rename plans <id6> --order <NN>' without an explicit --slug corrupts the slug. Observed 2026-08-23 renumbering the ipdgates Set: 'aw rename plans wezhxg --order 07' proposed '20260823-ipdgates-07-wezhxg-ipdgates-06-remove-raw-...ipd.md' - it injected the OLD cluster segment ('ipdgates-06-') into the new slug instead of changing only the NN facet. REPRO: aw rename plans <id6> --order <newNN>  (no --slug) on a clustered plan name; the dry-run shows the mangled target. WORKAROUND: always pass --slug <existing-slug> explicitly, which produces the correct name. IMPACT: silent filename corruption on a common regroup/renumber operation; high false-name risk for agents/humans who omit --slug. LIKELY ROOT CAUSE: the rename name-builder re-derives the slug from the current filename without stripping the existing YYYYMMDD-<setid>-NN- cluster prefix when only --order changes. RELATION: this is exactly the class of naming-tool defect the unifyfileio Set (canonical naming authority, Order 01 o6b8l3; unified rename engine) is meant to eliminate - fix here or fold into that Set's naming authority. Add a regression test: rename --order alone preserves the slug.
