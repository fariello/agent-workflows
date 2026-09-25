- Id: rtyapw
- Status: done
- Set: rtyapw
- Priority: medium
- Work-Kind: chore
- Summary: Migrate the 745 grandfathered deferred/question rows onto typed durable carriers so check.ipd-uncarried-obligation can reach its error tier

## Workflow history
- 2026-09-25 done (aw set): RETIRED (obsolete as written): 0 grandfathered pending rows remain (measured 8e74dcac; every pending plan postdates the 20260919 cutover). The 745 rows it counted sat in 106 plans that have since executed/been superseded; the rule never reads non-pending plans. The live debt (37 rows in 24 new pending plans, failing CI at error) and the scaffold cause are carried by plan carrierauth (from dtrect).
- 2026-09-18 created (aw backlog): Migrate the 745 grandfathered deferred/question rows onto typed durable carriers so check.ipd-uncarried-obligation can reach its error tier

durablecapture 01 (`rnkqrc`) shipped `check.ipd-uncarried-obligation` with a staged severity: a plan dated before `check_engine.CARRIER_CUTOVER_DATE` (20260919) yields a non-failing `info` finding, and a plan dated at or after it yields a fail-closed `error`.

MEASURED AT SHIP TIME (2026-09-18, HEAD 94345381): 106 pending plans carry 745 obligation rows with no typed carrier field, and ZERO plans anywhere carry one. Those 106 are all reported and none of them fails the gate, which is what kept CI (which enforces `aw check plans` fail-closed) green on day one.

THE OBLIGATION THIS ITEM CARRIES: the maintainer's ruling on that plan's OQ-05 was "All defects require one or more backlogs or plans to address ... This is a MUST, not a should", and the plan records that the advisory tier "exists only so a pre-existing corpus can be migrated, and nothing may leave the rule permanently at \`warning\`". So the grandfathered rows are a migration debt, not a permanent exemption: until they carry `- Carrier:`, `- Carrier-Evidence:` or `- Carrier-Declined:`, the obligations they name are still invisible to `aw attention` the moment their plan reaches `executed`.

WHAT DONE LOOKS LIKE: every remaining pending plan's deferred rows and `open`/`deferred` questions carry a typed carrier field, and `aw check plans` reports zero `check.ipd-uncarried-obligation` findings at any severity. Inspect with `python3 -c "from agent_workflows import check_engine as ce; from pathlib import Path; print(len(ce.check_durable_carrier(Path('.'))))"`.
