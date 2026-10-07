- Id: 5v4p2l
- Status: done
- Graduated-To: structpin
- Set: 5v4p2l
- Priority: low
- Work-Kind: chore
- Summary: Delete dead census table LANE_INTEGRATION_MOVED in tests/test_runner_shared.py

## Workflow history
- 2026-10-07 done (aw backlog): closed by aw agy run: IPD fdmo2v executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-structpin-06-fdmo2v-delete-the-last-dead-census-table-lane-integration-moved-and.ipd.md); evidence .aw/records/plans/executed/20261002-structpin-06-fdmo2v-delete-the-last-dead-census-table-lane-integration-moved-and.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: fdmo2v
- 2026-10-01 created (aw backlog): Delete dead census table LANE_INTEGRATION_MOVED in tests/test_runner_shared.py

The census table LANE_INTEGRATION_MOVED in tests/test_runner_shared.py is unread and dead code. Plan b02ohu deleted the other dead census tables (E-06), and plan ery0ia left LANE_INTEGRATION_MOVED out of scope because it is a lane-integration extraction census unconnected to docstring exemptions (F-05). Delete the dead table and its associated comment block.
