- Id: krwj2o
- Status: done
- Graduated-To: krwj2o
- Set: krwj2o
- Priority: medium
- Work-Kind: chore
- Summary: Restore deleted CLI conformance test gates and refresh stale goldens

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD cqxq2a executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261011-krwj2o-01-cqxq2a-verify-the-h0tiaw-restoration-discharged-krwj2o-and-pin-that.ipd.md); evidence .aw/records/plans/executed/20261011-krwj2o-01-cqxq2a-verify-the-h0tiaw-restoration-discharged-krwj2o-and-pin-that.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005606Z-2321569: cqxq2a
- 2026-10-01 created (aw backlog): Restore deleted CLI conformance test gates and refresh stale goldens

Restore deleted CLI quality and conformance gates (tests/test_cli_quality_gates.py and tests/test_cli_conformance_matrix.py, removed by 19313eed; see audit xvp5vx) so tests/conformance_matrix.py and twelve goldens under tests/fixtures/conformance_goldens/ are exercised again (F-04). Refresh unrelated stale remediation strings in check_findings.human.golden (F-05).
