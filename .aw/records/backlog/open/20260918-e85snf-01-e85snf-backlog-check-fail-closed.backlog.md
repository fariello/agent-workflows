- Id: e85snf
- Status: open
- Set: e85snf
- Priority: low
- Work-Kind: chore
- Summary: Decide whether aw check backlog should become fail-closed in CI instead of advisory

## Workflow history
- 2026-09-18 created (aw backlog): Decide whether aw check backlog should become fail-closed in CI instead of advisory

Named as explicitly OUT OF SCOPE by durablecapture 01 (`rnkqrc`) and filed here so the open decision has a durable carrier.

CURRENT STATE, measured by that plan: CI enforces `aw check plans` FAIL-CLOSED but `aw check backlog` is ADVISORY. `rnkqrc` E-04 explicitly instructed "do NOT change that as a side effect of this plan, and say so in the report if it seems tempting", and it was tempting: `rnkqrc` now depends on backlog items as the durable carriers its gate resolves, so a malformed backlog item weakens the gate without failing CI.

THIS IS A DECISION, NOT A TASK. Making it fail-closed has its own blast radius over the existing 286-item backlog tree and needs the same before/after finding count `rnkqrc` E-05 required of itself. A reasoned "keep it advisory" closes this item just as legitimately.
