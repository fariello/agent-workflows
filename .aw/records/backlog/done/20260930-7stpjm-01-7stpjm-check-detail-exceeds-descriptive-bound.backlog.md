- Id: 7stpjm
- Status: done
- Graduated-To: 7stpjm
- Set: 7stpjm
- Priority: low
- Work-Kind: chore
- Summary: Twelve aw check findings carry a detail over the Section 8.8 descriptive bound, the longest at 942 characters

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD lxcexr executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-7stpjm-01-lxcexr-bring-every-carrier-obligation-check-detail-inside-the-secti.ipd.md); evidence .aw/records/plans/executed/20261001-7stpjm-01-lxcexr-bring-every-carrier-obligation-check-detail-inside-the-secti.ipd.md
- 2026-10-03 note (aw backlog): lxcexr: resolved via combination of route (b) and budget-driven variant of (a) rather than (b) alone; route (a) as framed (smaller fixed cap) was refused because a fixed cap unconditionally loses locators whereas the budget-driven cap keeps every obligation named or counted (naming more on single-body findings and fewer on findings with distinct long evidence paths); fixed a second unstated violation (embedded newlines in all finished-carrier details); corrected premise that shortening removes operator information since evwmm2 closed and aw check prints pasteable path in Fix: field
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221834Z-1991716: lxcexr
- 2026-09-30 created (aw backlog): Twelve aw check findings carry a detail over the Section 8.8 descriptive bound, the longest at 942 characters

FILED AS THE CARRIER for the deferred row in plan `mc6r92` (hv8zlg-01), which measured this while bounding the STRANDED-LANE detail and declined to fix it in scope.

MEASURED 2026-09-30 in a lane at HEAD `c5a13052`: `python3 -m agent_workflows check all --json` returns 60 diagnostics, of which 12 carry a `detail` longer than `attention_contract.MAX_DESCRIPTIVE_LEN` (300). Ten are `check.ipd-uncarried-obligation` and two are `check.ipd-carrier-finished-unverified`; the longest is 942 characters. No lane rule is among them, so this is disjoint from the lane defect `hv8zlg` covers.

WHY IT IS NOT CAUGHT: the same gap as `hv8zlg`. `attention_contract.is_safe_descriptive` is never applied to a composed drift `detail`; its callers are in `specs`, `backlog` and `check_engine`, and `core.Drift` does not validate its own field.

THE FIX IS A DECISION ABOUT AN AGGREGATING FINDING, NOT A WORDING TRIM, which is why it was deferred. `check_engine.evaluate_durable_carrier` DELIBERATELY enumerates up to five offending locators plus a total in one detail (its docstring cites DECISION 07-rnkqrc-D4, plan `cnzrxb` E-01), so the length is by design and shortening it removes information an operator uses to find the offending rows. Routes: (a) reduce the enumeration cap, which loses locators; (b) summarize repeated per-row clauses, since the measured 942-character string repeats one clause seven times with only the row number varying, and this looks like the cheapest real win; (c) bound at the producer and accept elision. Note the surface is shared: this evaluator backs both `aw check` and `aw ipd lint --phase pre-transition`, so a change alters what a plan transition gate prints.
