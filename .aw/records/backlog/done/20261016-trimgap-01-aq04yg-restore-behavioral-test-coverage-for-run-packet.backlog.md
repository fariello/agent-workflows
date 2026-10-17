- Id: aq04yg
- Status: done
- Graduated-To: trimgap
- Set: trimgap
- Priority: low
- Work-Kind: chore
- Summary: Restore behavioral test coverage for run_packet

## Workflow history
- 2026-10-17 done (aw backlog): closed by aw agy run: IPD 5jevb2 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261017-trimgap-05-5jevb2-restore-behavioral-test-coverage-for-run-packet-step-packets.ipd.md); evidence .aw/records/plans/executed/20261017-trimgap-05-5jevb2-restore-behavioral-test-coverage-for-run-packet-step-packets.ipd.md
- 2026-10-17 graduated (aw backlog): graduated by run run-20261017T053813Z-512749: 5jevb2
- 2026-10-17 created (aw backlog): Restore behavioral test coverage for run_packet

Carries 10 candidate production keys for agent_workflows/run_packet.py (396 exclusive lines): StepPacket.to_dict, StepOutcomeEnvelope.to_dict, _compute_packet_digest, BoundRequirement.to_dict, StepPacket.to_json, ... (10 keys).

Details in Set findings doc b1mx2w ## Rollup mutation results and ## Rollup mutation totals.
Reach class and verdict: all 10 keys are unreached at baseline HEAD (reach class unreached, final verdict unguarded-unreached).
Deleted test files to mine: test_host_runner.py, test_run_packet_gates.py at 19313eed^ (see hpjj44 ## Derived properties).
Remedy: restore behavioral test coverage for run_packet.
