- Id: 8l1hgw
- Status: done
- Graduated-To: runledger
- Set: runledger
- Priority: low
- Work-Kind: chore
- Summary: No CLI writer of requirement_set or verifier_decision records exists, so aw run finalize can never reach complete on an operator-created ledger

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD um0twl executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-runledger-05-um0twl-write-requirement-set-on-aw-run-init-and-add-aw-run-verify-f.ipd.md); evidence .aw/records/plans/executed/20261014-runledger-05-um0twl-write-requirement-set-on-aw-run-init-and-add-aw-run-verify-f.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: um0twl
- 2026-10-12 created (aw backlog): Filed while authoring plan v47z9u from backlog hegwri: measured that after a header exists, start and record work end to end but the completion predicate is unreachable.

MEASURED 2026-10-12 at HEAD a3084a234 in lane worktree hegwri: with a hand-appended kind=run header at <runs-root>/run-abcdef1234/ledger.jsonl, 'aw run start ... --step S-01 --workflow wf.json' exits 0 and 'aw run record ... --state performed' exits 0, but 'aw runs verify-ledger' reports Completion Predicates UNSATISFIED with 'no frozen requirements defined', and 'runs status' exits 1. run_evidence.evaluate_completion needs a requirement_set record and a verifier_decision per requirement; RunEngine.record_verifier_decision exists but run_cli has no leaf that calls it, and nothing in run_cli writes a requirement_set (run_freeze.requirement_set_record builds one but mints M-NN ids that do not match a workflow's R-NN ids). Plan v47z9u deliberately stops at the header record (the item's stated minimum). Depends on v47z9u being executed. Not filed as bug: no operator path reaches this today, so there is no user-perceptible failure until v47z9u ships.
