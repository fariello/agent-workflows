- Id: w6mqc0
- Status: open
- Set: w6mqc0
- Priority: high
- Kind: bug
- Summary: aw ipd set approved must write the required Approval field (approved IPDs currently fail aw ipd lint IPD-M104)
- Blocks-Release: next

## Workflow history
- 2026-08-24 created (aw backlog): aw ipd set approved must write the required Approval field (approved IPDs currently fail aw ipd lint IPD-M104)

The IPD schema requires a '- Approval:' front-matter field when Status is approved (ipd_schema META_APPROVAL; aw ipd lint enforces it as IPD-M104 'Approval: Approval is required when Status is approved', disposition: error). But 'aw ipd set approved' transitions Status to approved and appends a workflow-history line WITHOUT writing the '- Approval:' field. Result: every plan approved via the tool fails 'aw ipd lint' and therefore CANNOT pass the pre-execution/pre-transition checkpoints (lint gates execution). CANNOT-PASS-CHECKS-TODAY (verified): all 22 currently-approved pending IPDs (sets execset, ipdgates, proclint, unifyfileio) fail 'aw ipd lint' with IPD-M104 because none carry an '- Approval:' field. The setter and the linter disagree: the setter produces an approved state the linter rejects. FIX: (1) 'aw ipd set approved' (and any path that sets Status=approved, including --by-human) MUST also write a conformant '- Approval:' field (date + human attestation + optional message), so the resulting plan lints CONFORMING; (2) provide a remediation for the 22 already-broken approved plans (a repair pass or 'aw doctor' fix that back-fills the Approval field from the existing 'approved (aw set, --by-human)' history line); (3) regression test: after 'aw ipd set approved --by-human', 'aw ipd lint' on the plan is conforming (no IPD-M104). Note the single earlier plan a4j0ly was fixed by hand-adding the Approval field during its execution; this item generalizes that fix into the setter so no approved plan is born failing lint. Origin: discovered while attempting to mark approved IPDs as release blockers - the plans were already failing lint (IPD-M104) before any Blocks-Release change.
