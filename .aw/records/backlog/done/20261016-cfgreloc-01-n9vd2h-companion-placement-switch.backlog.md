- Id: n9vd2h
- Status: done
- Graduated-To: cmpreloc
- Set: cfgreloc
- Priority: low
- Work-Kind: feature
- Summary: Support aw install placement switches that involve the public-target-private-companion preset (companion-tracked config and records)

## Workflow history
- 2026-10-17 done (aw backlog): closed by aw agy run: IPD aqun5z executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261016-cmpreloc-00-aqun5z-support-placement-switches-into-and-out-of-the-public-target.ipd.md, .aw/records/plans/executed/20261016-cmpreloc-02-fo08zx-execute-companion-placement-switches-with-companion-staging.ipd.md, .aw/records/plans/executed/20261016-cmpreloc-03-y1e2m9-make-companion-placement-switches-reachable-from-aw-install.ipd.md); evidence .aw/records/plans/executed/20261016-cmpreloc-00-aqun5z-support-placement-switches-into-and-out-of-the-public-target.ipd.md
- 2026-10-16 graduated (aw backlog): graduated by run run-20261016T212837Z-3381978: aqun5z, fo08zx, xc8nae, y1e2m9
- 2026-10-16 created (aw backlog): Support aw install placement switches that involve the public-target-private-companion preset (companion-tracked config and records)

Deferred from the cfgreloc Set (graduating ui1aln, 2026-10-16). The cfgreloc placement switch relocates config, durable state and records between the target (private-target) and AW_HOME (completely-clean-target, local-only). A switch into or out of public-target-private-companion also has to stage into or out of a second git repository (the companion) and attach or detach a companion identity (storage.attach_companion), which the cfgreloc executor does not do. Those switches keep refusing with InvalidPolicyError (they are safe, nothing is changed). This item owns adding them.
