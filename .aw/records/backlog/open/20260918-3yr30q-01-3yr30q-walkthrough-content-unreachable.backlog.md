- Id: 3yr30q
- Status: open
- Set: 3yr30q
- Priority: low
- Work-Kind: chore
- Summary: Walkthroughs are tracked=False and filename-only checked, so a defect recorded only in a walkthrough is invisible to every gate

## Workflow history
- 2026-09-18 created (aw backlog): Walkthroughs are tracked=False and filename-only checked, so a defect recorded only in a walkthrough is invisible to every gate

Named as explicitly OUT OF SCOPE by durablecapture 01 (`rnkqrc`) F-8, and filed here so the gap has a durable carrier instead of living only in that plan's prose (which is the exact failure mode `rnkqrc` exists to close, so leaving it uncarried would have been self-refuting).

THE GAP: the walkthroughs tree is `tracked=False` in the attention contract and gets FILENAME-ONLY checking, so a walkthrough may describe any number of live defects and no tool reads a word of it. `rnkqrc` closed the IPD route (a `## Deferred / out of scope` row or an `open`/`deferred` question must now name a typed durable carrier) and deliberately did NOT touch this one.

WHY IT WAS DEFERRED RATHER THAN FIXED, quoting that plan: "they are \`tracked=False\` and filename-only checked by design. Changing that is a records-policy change with its own blast radius; this plan makes the IPD route reliable instead."

NOT NECESSARILY A CODE CHANGE. The cheapest resolution may be a documented rule that a walkthrough is never a carrier and defects belong in a backlog item, which is already what `rnkqrc`'s accepted-carrier set enforces. Decide that before building any walkthrough reader.
