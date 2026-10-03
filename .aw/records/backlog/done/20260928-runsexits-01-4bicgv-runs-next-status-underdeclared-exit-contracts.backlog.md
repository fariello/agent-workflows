- Id: 4bicgv
- Status: done
- Graduated-To: runsexits
- Set: runsexits
- Priority: low
- Work-Kind: chore
- Summary: runs next and runs status under-declare their exit contracts: reachable codes 2, 5 and 7 are missing

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw oc run: IPD 69rdv6 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-runsexits-01-69rdv6-declare-runs-next-and-runs-status-by-their-measured-exit-cod.ipd.md); evidence .aw/records/plans/executed/20260930-runsexits-01-69rdv6-declare-runs-next-and-runs-status-by-their-measured-exit-cod.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 69rdv6
- 2026-09-28 created (aw backlog): runs next and runs status under-declare their exit contracts: reachable codes 2, 5 and 7 are missing

Measured at plan review of ck0vya (2026-09-28) by driving all three sibling verbs over identical fixtures.

THE MATRIX, observed through the real CLI:

  next     {clean: 3, absent: 2, notaledger: 7, seqgap: 5}
  resume   {clean: 0, absent: 2, notaledger: 7, seqgap: 5}
  status   {clean: 1, absent: 2, notaledger: 7, seqgap: 5}

Declared today: `runs next` = (0, 3); `runs status` = (0, 1, 3, 5).

So `runs next` omits reachable 2, 5 and 7, and `runs status` omits reachable 2 and 7. Both under-declare; NEITHER is misclassified (both are already `command_class="read"`), which is why plan ck0vya fenced them out: it corrects the one leaf backlog item cldbus reported.

WHY THIS IS A SEPARATE ITEM RATHER THAN A WIDENING OF ck0vya. The reachability evidence is per-leaf and ASYMMETRIC: exit 3 IS reachable on `runs next` (a step-less run exits 3, measured) while it is UNREACHABLE on `runs resume` (see item tzqvjn), so a single diff would both remove and retain the same code, which a reviewer cannot check quickly. And `runs status` declares 1 while `resume` does not, so its `required_scenarios` already includes `domain_failure` and widening its contract has a different coverage consequence.

SUGGESTED FIX: measure each leaf's own reachability matrix, then widen `next` to include 2, 5, 7 and `status` to include 2, 7. Retain 3 on `next` (reachable) and re-measure whether 3 is genuinely reachable on `status`. Add a per-leaf test in the shape of `tests/test_run_cli_declarations.py` (created by ck0vya) rather than reviving the deleted conformance harness.

NOTE THE NEIGHBOUR: pending plan fuuw94 (set z63xoh) moves `runs show|evidence|verify-ledger` from exit 2 to exit 5 on a corrupt ledger. It does not touch next/status/resume, but whoever executes THIS item should re-measure rather than trust this matrix if fuuw94 has landed.

CARRIER FOR: plan ck0vya's OQ-02 and its second Deferred row.
