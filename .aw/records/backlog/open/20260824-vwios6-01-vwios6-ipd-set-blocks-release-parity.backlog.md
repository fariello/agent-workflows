- Id: vwios6
- Status: open
- Set: vwios6
- Priority: high
- Kind: feature
- Summary: aw ipd set must support --blocks-release (release-gate parity with backlog and specs setters)
- Blocks-Release: next

## Workflow history
- 2026-08-24 open (aw set): status set to open
- 2026-08-24 created (aw backlog): aw ipd set must support --blocks-release (release-gate parity with backlog and specs setters)

AGENTS.md (Release gates) states any backlog item, spec, OR plan may carry a '- Blocks-Release: <release-id6|next>' front-matter field, and documents setters for backlog (aw backlog set --blocks-release) and specs (aw specs set --blocks-release). Two gaps make this UNTRUE for plans today:

1. SCHEMA REJECTION (root cause, must fix first): the IPD linter's recognized-field set does NOT include Blocks-Release. agent_workflows/ipd_schema.py META_RECOGNIZED (line ~147) omits it, and ipd_schema parse records any unknown field as an error, surfaced by aw ipd lint as IPD-M103 'Blocks-Release: unknown field' (verified by hand-adding the field to an approved IPD and running 'aw ipd lint'). Because aw ipd lint gates execution (pre-execution/pre-transition checkpoints), a plan that carries the field currently FAILS lint and cannot be executed. So the documented 'a plan may carry Blocks-Release' is contradicted by the linter. Meanwhile agent_workflows/attention.py DOES scan any artifact (line ~482) for '- Blocks-Release:', so the attention view would recognize it - the toolkit is internally inconsistent. FIX: add Blocks-Release to META_RECOGNIZED (optional, single-valued: a release id6 or 'next'), validated the same way backlog/specs validate it (dangling-reference check via aw check), so an IPD may legally carry it and still lint clean.

2. NO SETTER: 'aw ipd set' has no --blocks-release flag, so even once the schema allows it, a plan release blocker can only be set by hand-editing front matter. FIX: add '--blocks-release <release-id6|next|->' to 'aw ipd set' with the SAME semantics as the backlog/specs setters: resolve 'next' to the single planned release record, write/update the '- Blocks-Release:' front-matter field (not prose), clear it with '-', append a workflow-history line, validate via aw check, and surface via aw attention.

Constraints: field is independent of the plan's lifecycle Status (an approved or pending IPD can be a release blocker). Add tests covering: schema accepts the field and lint stays conforming; set/clear/resolve-next; the no-release-record (dangling) error; and that a plan carrying it appears in aw attention's release-blocker set. Related: known bug 61qk4a (backlog set --blocks-release silently no-ops) - fix the shared blocks-release setter path so the backlog AND the new ipd setter actually persist the field and its removal, rather than duplicating a broken code path.

ACCEPTANCE / CANNOT-PASS-CHECKS-TODAY (explicit): the hard blocker right now is that a plan carrying '- Blocks-Release:' CANNOT PASS 'aw ipd lint' (IPD-M103 'unknown field', disposition: error) nor the execution checkpoints that call it, and 'aw check' has no path to validate the field on a plan. Definition of done MUST include: (1) an IPD that legally carries '- Blocks-Release: next' (or a real release id6) lints CONFORMING at every phase (author/pre-execution/pre-transition/post-transition); (2) 'aw check' validates the plan's Blocks-Release the same as backlog/specs (clean when it resolves, flagged when dangling); (3) a regression test asserts an IPD with the field passes lint (guards against re-introducing IPD-M103). Only after this lands may the execset/ipdgates/proclint/unifyfileio IPDs be marked with the field; until then their release-blocker intent is tracked on the 2.0.0 release record (interim note) and here. Origin: user asked whether IPDs can be release-blocking (docs say yes) and to mark the approved IPDs blocking; attempting it revealed the field is schema-rejected by aw ipd lint (IPD-M103) AND there is no ipd setter, so the marking was reverted pending this fix.
