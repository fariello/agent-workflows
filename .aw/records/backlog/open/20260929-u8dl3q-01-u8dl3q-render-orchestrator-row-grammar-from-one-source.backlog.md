- Id: u8dl3q
- Status: open
- Set: u8dl3q
- Priority: low
- Work-Kind: chore
- Summary: Render the orchestrator row grammar, its refusal message, the scaffold skeleton, and the docs from one source so the instruction and the check cannot drift (spec r07vma OQ-01)

## Workflow history
- 2026-09-29 created (aw backlog): Filed as the durable carrier for the spec r07vma OQ-01 residue that plan zojfn6 deliberately leaves open

Approved spec `r07vma` OQ-01 asks how the AUTHORING INSTRUCTIONS are kept from drifting away from the ENFORCING CODE, and carries a PROPOSED DIRECTION rather than a decision: hold the row GRAMMAR as data in the rule module and render the refusal message, the `aw ipd scaffold` skeleton, and the documentation from that one source. It is explicitly `Blocking: no`.

WHY THIS IS FILED NOW. Plan `zojfn6` (from backlog `htce8t`) makes the scaffolded orchestrator skeleton AGREE with the grammar, which is OQ-01's direction applied to one surface and is what closes the live defect. It does NOT make the two SHARE one generator: after it lands, `ipd_lint._ORCH_ROW_RE` still states the grammar as a regex, `ipd_lint.ORCH_ROW_CANONICAL` states it again as a rendered string, and `ipd_authoring` emits a third hand-written copy in the skeleton. Three hand-maintained statements of one rule is the decay mode OQ-01 names.

SO THE RESIDUAL RISK IS SMALLER BUT REAL: a future change to the grammar must touch all three, and nothing fails if one is missed (the skeleton copy would be caught by the conformance rule once plan `zojfn6` gates `pre-execution`, but the CANONICAL string and the docs would not). The spec itself says the residual surface is 'the GRAMMAR plus the refusal wording'.

EVIDENCE AND SEAM: `ORCH_ROW_CANONICAL` already exists specifically as a single rendered statement of the canonical form, with the comment that it is 'rendered from the same grammar the check enforces, so the instruction an author reads and the rule that refuses them have ONE source (spec OQ-01's proposed direction, partially)'. That word 'partially' is this item. The natural seam is to derive both `_ORCH_ROW_RE` and the skeleton row from one grammar datum.

ALSO NOTE the `ipd-spec` document carries NO statement of this grammar at all (grep for `IPD-S407`, 'typed child-tracking', and 'CONFIRM' in it returns nothing), so whoever takes this up should decide whether the docs surface should exist before deciding how to render it.
