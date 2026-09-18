- Id: 2rb85l
- Status: open
- Set: attnreach
- Priority: low
- Work-Kind: followup
- Summary: The tracked-tree scan-root guard proves DECLARATION not REACHABILITY, so a tracked tree can still be scan-rooted and never surfaced

## Workflow history
- 2026-09-18 created (aw backlog): Deferred by plan m867ox with a reason; filed so the gap has a durable carrier rather than living only in that plan's prose.

MEASURED at HEAD cdace6a5 while executing plan m867ox, which ADDED the guard in question.

tests/test_attention_contract.py::TrackedTreeScanCoverageTests::test_every_tracked_tree_has_a_scan_root asserts every TRACKED_TREES entry has at least one artifact_core.SCAN_ROOTS entry. That closes the specific drift that hid every release record from aw attention. It does NOT prove the tree's records actually ARRIVE in the view.

PROVEN, not asserted (plan m867ox E-05 mutation 3): with only '.agents/releases' in SCAN_ROOTS the guard PASSES (exit 0) while attention.scan still yields ZERO releases items, because releases._releases_dir resolves '.aw/records/releases' and this repository materializes no '.agents/releases' directory. So the guard is satisfiable by a configuration that fixes nothing.

MITIGATION ALREADY IN PLACE, which is why this is low priority and a followup rather than a bug: the guard's own docstring states the limit and cites that measurement, plan m867ox added a releases-specific reachability test (ReleaseRecordsReachTheViewTests, which scans synthesized records in both the flat and subdirectory layouts), and E-05 mutation 3 is recorded so a reader cannot over-trust the green.

THE REMAINING WORK, and why plan m867ox deliberately did not do it: a guard that asserted each tracked tree's records actually reach the view would need a fixture record per tree and would couple one contract test to five trees' record shapes (a spec's front matter, a plan's, a research doc's, a backlog item's, a release's). That is a real design decision about where such a test belongs and how it stays cheap, not a line to add. Note the reachability test m867ox did add covers releases ONLY; the other four tracked trees have no equivalent, they are simply known-good today by observation.
