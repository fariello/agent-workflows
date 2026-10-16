- Id: a4tjxc
- Status: done
- Graduated-To: runledger
- Set: runledger
- Priority: low
- Work-Kind: chore
- Summary: Make the eight ledger-reading runs leaves live conformance rows once aw run init (plan v47z9u) can create a ledger fixture

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD g5s94t executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-runledger-05-g5s94t-add-ledger-leaves-to-live-safe-leaves-once-aw-run-init-lands.ipd.md); evidence .aw/records/plans/executed/20261014-runledger-05-g5s94t-add-ledger-leaves-to-live-safe-leaves-once-aw-run-init-lands.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: g5s94t
- 2026-10-12 created (aw backlog): Filed while authoring plan v47z9u from backlog hegwri: the conformance_matrix not_runnable exemptions cite the absence of any ledger, which v47z9u removes.

tests/conformance_matrix.py EXEMPTION_REGISTRY carries eight runs leaves (decisions, evidence, next, questions, resume, show, status, verify-ledger) as reason_kind not_runnable with the reason 'Requires an on-disk hash-chained ledger.jsonl file which is not present in the workspace.' and MUTATION_EXEMPTION_REGISTRY carries run start/record/cancel/finalize as arg_fixture_needed. Once plan v47z9u ships aw run init, a harness fixture can create a real ledger, so those exemptions stop being true for the ledger readers and could become live scenario rows. Out of v47z9u's scope because it is a test-harness redesign (fixture lifecycle in the conformance harness and its session template), not ledger creation. Depends on v47z9u being executed.
